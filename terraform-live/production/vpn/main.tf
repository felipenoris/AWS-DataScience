# production/vpn/ - the tunnel endpoint, in the hub (Stage 6c step 4.7). It is Stage 4's Sandbox
# slice moved one account and one design across.
#
# It reads networking/ and not foundation/. Production holds three VPCs since 6c, so "the account's
# VPC" names nothing: the anchors this slice consumes are in VPC-Networking, the only VPC in the
# estate whose public tier routes to an internet gateway, and a tunnel endpoint has to sit where
# the internet is.
#
# The host is no longer a NAT and is not an internet door either. Under D38 a VPN client is a
# private-network client, and its whole internet crosses the Squid proxy next door, by name, over
# an explicit CONNECT. This host forwards to the private address space, rejects the rest, and stops
# masquerading the one destination whose log has to tell two devices apart. Both are module inputs,
# argued at their site below.
#
# The Elastic IP did not change. It is the same address the Sandbox slice held, transferred at 4.5
# and imported at 4.6, so no client `.conf` moved, and neither did `DenyControlPlaneOffVpn`'s
# WireGuard branch until 4.12 re-keyed it onto the proxy.
#
# The module arrives by git tag, never by branch (conventions 6; Stage 3 step 1.1a), and the tag is
# cut between two commits: the validate hook inits from origin, so a module and its first caller
# cannot share one.

data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/networking/terraform.tfstate"
    region = var.region
  }
}

# The public tier's address ranges, read from the subnets themselves - the idiom sandbox/vpn/ uses
# for the isolated tier, applied to the tier the proxy lives in. networking/ exports subnet ids and
# not their CIDRs, and this data source is the repair rather than a new output: a CIDR is a
# property of the subnet, `aws_subnet` already reports it, and an output would be a second place
# for the same fact to live (Lesson 14). A literal here would be a third.
data "aws_subnet" "public" {
  for_each = data.terraform_remote_state.networking.outputs.public_subnet_ids

  id = each.value
}

module "wireguard" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/wireguard?ref=wireguard-v0.6.0"

  env          = var.env
  zone_ids     = var.zone_ids
  zone_index   = var.zone_index
  peer_cidr    = var.peer_cidr
  peer_cidr_v6 = var.peer_cidr_v6

  instance_type    = var.instance_type
  root_volume_size = var.root_volume_size

  public_subnet_ids = data.terraform_remote_state.networking.outputs.public_subnet_ids
  security_group_id = data.terraform_remote_state.networking.outputs.wireguard_security_group_id
  eip_allocation_id = data.terraform_remote_state.networking.outputs.wireguard_eip_allocation_id

  # The pointer, never the key (decision 4, third review): the module grants its instance role
  # GetSecretValue on exactly this ARN and the host fetches the value at first boot. The value was
  # copied in by hand at 4.3, the one act of pass 4 that is the user's alone, because a new key
  # would silently invalidate every client's `PublicKey =` line.
  host_key_secret_arn = data.terraform_remote_state.networking.outputs.wireguard_host_key_secret_arn

  # A private-network client, enforced on the host (D38). The tunnel reaches the private address
  # space and nothing else; a packet addressed straight at a public IP is rejected here, with an
  # ICMP that says so rather than a timeout nobody diagnoses. What that leaves a person is the
  # proxy: one egress, with an access log, for the whole estate.
  #
  # The list is generated (backend.py RFC1918_CIDRS) rather than written here, because the same
  # ranges appear in the proxy's `to_private` ACL with the opposite polarity - the tunnel admits
  # them, Squid denies them as destinations - and a range added to one and missed in the other is a
  # spoke reachable through the proxy that the topology says is unreachable.
  forward_destinations = var.rfc1918_cidrs

  # The proxy must see which device is talking to it (Stage 11's egress evidence, 4.11). Squid's
  # access log is the estate's record of what left, and a log in which every line reads "the VPN
  # host" identifies nothing. Packets bound for the public tier, where the proxy is, keep their
  # `10.90.0.x` source; every other destination is masqueraded as before.
  #
  # The public subnets and not the VPC CIDR: the VPC resolver at `.2` sits inside the VPC range
  # too, and the Amazon DNS server answers requests from within the VPC's own addresses, which a
  # packet arriving with a `10.90.0.x` source is not. Exempting the whole VPC would take the
  # tunnel's DNS down, and the symptom would look like anything but a masquerade rule.
  #
  # It costs the ENI's source/destination check (the module keys that off this list) and it needs
  # the route below. Without the check off, EC2 drops both legs before any kernel rule sees them;
  # without the route, the proxy's reply has nowhere to go.
  no_masquerade_cidrs = [for s in data.aws_subnet.public : s.cidr_block]

  peers = var.peers
}

# The return path for an un-masqueraded client, and the single exception to step 3.6's rule that no
# route table in this estate carries the tunnel range (6c step 4.7).
#
# It is safe here and nowhere else because it stays inside one VPC: the proxy and the tunnel
# endpoint share VPC-Networking, so this is a route between two ENIs, not a path across a peering.
# Peering shares an address, never a path (Lesson 44), which is why the spokes have no such route
# and why `./aws/networking.py` NT-4 admits this one and only this one.
#
# The target is an ENI that may be replaced, read from the module's output rather than looked up,
# so an instance rebuild re-plans onto the new interface instead of leaving a route pointing at a
# deleted one, which blackholes silently instead of erroring.
#
# It lives in this [D] slice and not in networking/ for the same reason: a route whose target is a
# [D] instance cannot outlive it. `make down` takes the route with the host, and a route to nothing
# is worse than no route.
resource "aws_route" "tunnel_return" {
  route_table_id         = data.terraform_remote_state.networking.outputs.public_route_table_id
  destination_cidr_block = var.peer_cidr
  network_interface_id   = module.wireguard.primary_network_interface_id
}

# ------------------------------------------------- the name (6c step 2.1, written here at 4.7)
#
# `vpn.awsds.internal`. The apex zone is production/foundation/'s and carries the shared names only
# - gitlab, proxy, vpn - so this record and the proxy's are the tunnel's half of that set.
#
# The record is [D] and lives with the host: the zone is [P], while the address is a property of an
# instance this slice may replace, so the record is declared beside the thing that owns the value.
# `make down` stops this host rather than destroying it, so both the ENI and its private address
# survive a down/up cycle and the record does not churn.
#
# It carries the private address, not the Elastic IP. Everything that resolves this name is inside
# the estate and reaches the host over the VPC or a peering; the public address is the tunnel
# endpoint, which clients carry in their `.conf` and never look up.
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

resource "aws_route53_record" "vpn" {
  # checkov:skip=CKV2_AWS_23:the value IS an attached resource - `module.wireguard.private_ip`, the host built two blocks up. Checkov traces a reference into a resource in the same file (the proxy slice's identical record passes) and cannot follow one through a module output. The dangling-record risk this check exists for is absent: the address is the module's, so the record cannot outlive the instance
  zone_id = data.terraform_remote_state.foundation.outputs.awsds_internal_zone_id
  name    = "vpn.awsds.internal"
  type    = "A"
  ttl     = 60
  records = [module.wireguard.private_ip]
}
