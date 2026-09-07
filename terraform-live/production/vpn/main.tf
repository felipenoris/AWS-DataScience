# production/vpn/ - the tunnel endpoint, in the hub (Stage 6c step 4.7). The Sandbox slice of
# Stage 4, moved one account and one design across, and the two differences are the whole file.
#
# DIFFERENCE ONE - IT READS networking/ AND NOT foundation/. Production holds three VPCs since
# 6c, so "the account's VPC" stopped naming anything: the anchors this slice consumes are in
# VPC-Networking, which is the only VPC in the estate whose public tier routes to an internet
# gateway. A tunnel endpoint has to sit where the internet is.
#
# DIFFERENCE TWO - THE HOST IS NO LONGER A NAT AND IS NOT AN INTERNET DOOR EITHER. Under D38 a
# VPN client is a PRIVATE-NETWORK client: its whole internet crosses the Squid proxy next door,
# by name, over an explicit CONNECT. So this host forwards to the private address space and
# rejects the rest, and it stops masquerading the one destination whose LOG has to tell two
# devices apart. Both are module inputs (wireguard-v0.5.0), both are argued at their site below.
#
# WHAT DID NOT CHANGE, and it is the point of the whole transfer: the Elastic IP. It is the same
# address the Sandbox slice held - transferred at 4.5, imported at 4.6 - so no client `.conf`
# moved, and neither did `DenyControlPlaneOffVpn`'s WireGuard branch until 4.12 re-keyed it onto
# the PROXY deliberately rather than by accident.
#
# THE MODULE ARRIVES BY GIT TAG, NEVER BY BRANCH (conventions 6; Stage 3 step 1.1a), and the tag
# is cut BETWEEN two commits - the validate hook inits from origin, so a module and its first
# caller cannot share one.

data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/networking/terraform.tfstate"
    region = var.region
  }
}

# THE PUBLIC TIER'S ADDRESS RANGES, READ FROM THE SUBNETS THEMSELVES - the idiom sandbox/vpn/
# uses for the isolated tier, applied to the tier the proxy lives in. networking/ exports subnet
# IDs and not their CIDRs, and the right repair is this data source rather than a new output: a
# CIDR is a property of the subnet, `aws_subnet` already reports it, and an output would be a
# second place for the same fact to live (Lesson 14). A literal here would be a third.
data "aws_subnet" "public" {
  for_each = data.terraform_remote_state.networking.outputs.public_subnet_ids

  id = each.value
}

module "wireguard" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/wireguard?ref=wireguard-v0.5.0"

  env        = var.env
  zone_ids   = var.zone_ids
  zone_index = var.zone_index
  peer_cidr  = var.peer_cidr

  instance_type    = var.instance_type
  root_volume_size = var.root_volume_size

  public_subnet_ids = data.terraform_remote_state.networking.outputs.public_subnet_ids
  security_group_id = data.terraform_remote_state.networking.outputs.wireguard_security_group_id
  eip_allocation_id = data.terraform_remote_state.networking.outputs.wireguard_eip_allocation_id

  # The POINTER, never the key (decision 4, third review): the module grants its instance role
  # GetSecretValue on exactly this ARN and the host fetches the value at first boot. The value
  # was copied in by hand at 4.3 - the one act of pass 4 that is nobody's but the user's, because
  # a NEW key would silently invalidate every client's `PublicKey =` line.
  host_key_secret_arn = data.terraform_remote_state.networking.outputs.wireguard_host_key_secret_arn

  # A PRIVATE-NETWORK CLIENT, ENFORCED ON THE HOST (D38). The tunnel reaches the private address
  # space and nothing else; a packet addressed straight at a public IP is rejected here, with an
  # ICMP that says so rather than a timeout nobody diagnoses. What that leaves a person is the
  # proxy - which is the design, not a side effect: ONE egress, with an access log, for the whole
  # estate.
  #
  # THE LIST IS GENERATED (backend.py RFC1918_CIDRS) rather than written here, because the SAME
  # ranges appear in the proxy's `to_private` ACL with the OPPOSITE polarity - the tunnel admits
  # them, Squid denies them as destinations - and a range added to one and missed in the other is
  # a spoke reachable through the proxy that the topology says is unreachable.
  forward_destinations = var.rfc1918_cidrs

  # THE PROXY MUST SEE WHICH DEVICE IS TALKING TO IT (Stage 11's egress evidence, 4.11). Squid's
  # access log is the estate's record of what left; a log in which every line reads "the VPN
  # host" identifies nothing. So packets bound for the PUBLIC TIER - where the proxy is - keep
  # their `10.90.0.x` source, and every other destination is masqueraded exactly as before.
  #
  # WHY THE PUBLIC SUBNETS AND NOT THE VPC CIDR, which is the tidy-looking version and is WRONG:
  # the VPC resolver at `.2` sits inside the VPC range too, and the Amazon DNS server answers
  # requests from within the VPC's own addresses - a packet arriving with a `10.90.0.x` source is
  # not that. Exempting the whole VPC would take the tunnel's DNS down, and the symptom would
  # look like anything but a masquerade rule.
  #
  # IT COSTS THE ENI's SOURCE/DESTINATION CHECK (the module keys that off this list) and it needs
  # the ROUTE below. Neither is optional: without the check off, EC2 drops both legs before any
  # kernel rule sees them; without the route, the proxy's reply has nowhere to go.
  no_masquerade_cidrs = [for s in data.aws_subnet.public : s.cidr_block]

  peers = var.peers
}

# THE RETURN PATH FOR AN UN-MASQUERADED CLIENT, and the single exception to step 3.6's rule that
# no route table in this estate carries the tunnel range (6c step 4.7).
#
# It is safe here and nowhere else because it stays INSIDE one VPC: the proxy and the tunnel
# endpoint share VPC-Networking, so this is a route between two ENIs, not a path across a
# peering. Peering shares an address, never a path (Lesson 44) - which is exactly why the spokes
# have no such route and why `./aws/networking.py` NT-4 admits this one and only this one.
#
# THE TARGET IS AN ENI THAT MAY BE REPLACED. It is read from the module's output rather than
# looked up, so an instance rebuild re-plans onto the new interface instead of leaving a route
# pointing at a deleted one - which blackholes silently instead of erroring (the module's own
# output description carries the argument).
#
# IT LIVES IN THIS [D] SLICE AND NOT IN networking/ FOR THE SAME REASON: a route whose target is
# a [D] instance cannot outlive it. `make down` takes the route with the host, which is correct -
# a route to nothing is worse than no route.
resource "aws_route" "tunnel_return" {
  route_table_id         = data.terraform_remote_state.networking.outputs.public_route_table_id
  destination_cidr_block = var.peer_cidr
  network_interface_id   = module.wireguard.primary_network_interface_id
}

# ------------------------------------------------- the name (6c step 2.1, written here at 4.7)
#
# `vpn.awsds.internal`. STEP 2.1 SAYS THIS RECORD AND THE PROXY'S ARE *"written by pass 4 from
# the two hosts' private addresses"*, AND PASS 4 DID NOT WRITE THEM (found 2026-09-06, while 5.7
# was re-cutting the firewall lists to include `.awsds.internal` - a family whose only content
# was, at that moment, nothing). The apex zone was created at 2.1 with the comment *"shared names
# only: gitlab, proxy, vpn"* and then no record was ever declared, so both names have been
# NXDOMAIN since the zone existed. Pass 6's step 6.1 asks a client to reach
# `proxy.awsds.internal:3128` by NAME; that reading was unrunnable and nothing said so, which is
# a deferred obligation recorded only at the deferring end (Lesson 34).
#
# THE RECORD IS [D] AND LIVES WITH THE HOST, WHICH IS THE POINT. The zone is [P] in
# production/foundation/; the ADDRESS is a property of an instance this slice may replace, so the
# record is declared beside the thing that owns the value. `make down` STOPS this host rather
# than destroying it, so both the ENI and its private address survive a down/up cycle and the
# record does not churn.
#
# PRIVATE, NOT THE ELASTIC IP. Everything that resolves this name is inside the estate and reaches
# the host over the VPC or a peering; the public address is the tunnel ENDPOINT, which clients
# carry in their `.conf` and never look up.
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
