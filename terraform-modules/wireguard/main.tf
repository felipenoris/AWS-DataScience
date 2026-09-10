# wireguard - the tunnel endpoint of D4, and the repository's first [D] resource.
#
# Here: the instance, its user data, its role, the handshake log and the alarm - everything a
# rebuild may legitimately replace. Not here: the Elastic IP and the security group, which are
# [P] in the caller's foundation/ because things outside this stage name them (step 8's
# control-plane deny names the address; Stage 7's GitLab rule names the group, across an account
# boundary).
#
# A rebuild is made invisible rather than prevented, and it will happen: `ami` resolves through
# an SSM public parameter that moves with every AL2023 release, and a changed `ami` forces
# replacement. Everything a client config pins survives it - the address because it is [P], the
# server's public key because its private half lives in the caller's [P] Secrets Manager secret,
# fetched at first boot rather than generated on the host (step 4.3; decision 4, third review).
#
# The architecture is one of those rebuilds, taken deliberately on 2026-08-20: this module was
# arm64 (Graviton, the `-arm64` spelling of the parameter below) from D4 until the user moved it
# to x86_64. The AMI is where that decision lives, and the only place it can live: an AMI is
# specific to its processor architecture, so the image below is what makes `instance_type` a t3
# family rather than a t4g one, and not the other way round. The caller's closed-list validation
# follows this line; it does not constrain it.
#
# What such a move costs is a replaced instance - x86_64 and arm64 are not a stop, modify and
# start the way two sizes in one family are, and EC2 refuses the in-place change - so the user
# data re-runs and /etc/wireguard/ is rebuilt from the [P] secret and the roster. It costs no
# client edit: the address is the [P] Elastic IP and the server's public key is the [P] secret's,
# so every .conf on every device stays valid across it.
#
# What is architecture-neutral, and why the move is this one line: the user data installs every
# package by name from the AL2023 repository (wireguard-tools, iptables-nft,
# amazon-cloudwatch-agent - all three built for both architectures), derives the uplink
# interface rather than assuming a generation's name, and downloads no binary of its own.

data "aws_partition" "current" {}

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  zone = var.zone_ids[var.zone_index]

  # The tunnel addressing, derived in one place from the allocation table's range: the server
  # takes .1, every device takes the host number authored beside its public key. Deriving the
  # device numbers from map order instead fails the way Lesson 4 fails - deleting one revoked
  # device would renumber every device after it, invalidating client configs nobody edited.
  server_address = "${cidrhost(var.peer_cidr, 1)}/${split("/", var.peer_cidr)[1]}"

  # The same host number in both families: `fd90::2` is the device that is `10.90.0.2`. The
  # access log, the handshake log and the roster all key on that number, so a reader meeting
  # `fd90::3` should not have to look anything up. The server keeps `.1` in both.
  server_address_v6 = var.peer_cidr_v6 == "" ? "" : "${cidrhost(var.peer_cidr_v6, 1)}/${split("/", var.peer_cidr_v6)[1]}"
  server_addresses  = join(", ", compact([local.server_address, local.server_address_v6]))

  peers = {
    for name, p in var.peers : name => {
      public_key = p.public_key
      address    = cidrhost(var.peer_cidr, p.host)
      # `/128` for the same reason the v4 half is `/32`: a peer does not reach another peer. An
      # empty string when the tunnel is IPv4-only, and `compact()` at the render site drops it.
      address_v6 = var.peer_cidr_v6 == "" ? "" : "${cidrhost(var.peer_cidr_v6, p.host)}/128"
    }
  }

  # Logs only - see the user data. The file name is the one the sampler timer appends to.
  agent_config = jsonencode({
    agent = {
      run_as_user = "root"
    }
    logs = {
      logs_collected = {
        files = {
          collect_list = [
            {
              file_path       = "/var/log/wireguard-handshakes.log"
              log_group_name  = aws_cloudwatch_log_group.handshakes.name
              log_stream_name = "{instance_id}/handshakes"
              timezone        = "UTC"
            }
          ]
        }
      }
    }
  })

  # The iptables rules are built here rather than in the template, because a `%{ for }` directive
  # inside a single wg0.conf line has to trim its own newlines on both sides and is then
  # unreadable in the one place it must not be. `$UPLINK` survives verbatim: Terraform
  # interpolates `${`, not `$U`, and the heredoc that writes wg0.conf is unquoted, so the shell
  # substitutes the real interface name at write time.
  #
  # The two rules below are the halves of D38's client model (6c step 4.7) - a tunnel that reaches
  # only the private network, and a proxy that can see which device is talking to it. They replace
  # the VPC-NAT pair, whose job was a private tier with no other way out.

  # (a) The masquerade, with its exemptions first. Order is the whole of it: iptables walks
  # POSTROUTING top to bottom, so each `-j RETURN` has to be appended before the MASQUERADE it
  # exempts from. RETURN in a built-in chain means "stop here and take the chain policy", which
  # in `nat`/POSTROUTING is ACCEPT - so the packet leaves with its original client source. An
  # empty list makes the prefix empty and renders no exemption at all.
  #
  # The prefixes are their own locals because `+` in HCL is arithmetic, not concatenation
  # (measured: `join(...) + "..."` answered `Unsuitable value for left operand: a number is
  # required`). Strings join by interpolation, and a local per prefix keeps the interpolated line
  # short enough to read.
  masquerade_exempt_up = join("", [
    for c in var.no_masquerade_cidrs :
    "iptables -t nat -A POSTROUTING -s ${var.peer_cidr} -d ${c} -j RETURN; "
  ])
  masquerade_exempt_down = join("", [
    for c in var.no_masquerade_cidrs :
    "iptables -t nat -D POSTROUTING -s ${var.peer_cidr} -d ${c} -j RETURN; "
  ])

  # `%i` survives every layer verbatim as well - it is wg-quick's own placeholder for the
  # interface, and templatefile's directive marker is `%{`, not `%i`.
  #
  # (c) The IPv6 half of the FORWARD chain, one rule because there is one answer. This estate is
  # IPv4-only in every VPC, so there is no IPv6 destination a forwarded packet could reach and no
  # allow-list to write. `net.ipv6.conf.all.forwarding` is 0 on this host (measured 2026-09-07),
  # so the packets would be dropped by routing anyway; the rule is here so the refusal is explicit
  # and, more usefully, counted. A dropped packet leaves no evidence; a rejected one increments a
  # counter, and that counter is the only place a refusal the sender cannot see is legible
  # (Lesson 55, learned on this host's IPv4 half two days earlier).
  #
  # Empty when the tunnel is IPv4-only, so a caller that has not opted in renders no IPv6 rule.
  forward_v6_up   = var.peer_cidr_v6 == "" ? "" : "; ip6tables -A FORWARD -i %i -j REJECT --reject-with icmp6-adm-prohibited"
  forward_v6_down = var.peer_cidr_v6 == "" ? "" : "; ip6tables -D FORWARD -i %i -j REJECT --reject-with icmp6-adm-prohibited"

  masquerade_post_up   = "${local.masquerade_exempt_up}iptables -t nat -A POSTROUTING -s ${var.peer_cidr} -o $UPLINK -j MASQUERADE"
  masquerade_post_down = "${local.masquerade_exempt_down}iptables -t nat -D POSTROUTING -s ${var.peer_cidr} -o $UPLINK -j MASQUERADE"

  # (b) The FORWARD chain. An empty `forward_destinations` renders one blanket accept each way. A
  # non-empty list accepts `-i wg0` only toward the named ranges and rejects the rest; the return
  # leg (`-o wg0`) keeps its blanket accept, because tightening it to ESTABLISHED,RELATED is a
  # change nobody asked for whose failure mode would be indistinguishable from this one.
  #
  # The REJECT sits after the accepts and matches `-i wg0` only, so it can never catch the return
  # leg: a reply arrives on the uplink, and `-i wg0` does not match it.
  forward_allow_up = join("", [
    for c in var.forward_destinations :
    "iptables -A FORWARD -i %i -d ${c} -j ACCEPT; "
  ])
  forward_allow_down = join("", [
    for c in var.forward_destinations :
    "iptables -D FORWARD -i %i -d ${c} -j ACCEPT; "
  ])

  forward_post_up   = length(var.forward_destinations) == 0 ? "iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT" : "${local.forward_allow_up}iptables -A FORWARD -i %i -j REJECT --reject-with icmp-admin-prohibited; iptables -A FORWARD -o %i -j ACCEPT"
  forward_post_down = length(var.forward_destinations) == 0 ? "iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT" : "${local.forward_allow_down}iptables -D FORWARD -i %i -j REJECT --reject-with icmp-admin-prohibited; iptables -D FORWARD -o %i -j ACCEPT"

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    masquerade_post_up   = local.masquerade_post_up
    masquerade_post_down = local.masquerade_post_down
    forward_post_up      = "${local.forward_post_up}${local.forward_v6_up}"
    forward_post_down    = "${local.forward_post_down}${local.forward_v6_down}"
    peer_cidr            = var.peer_cidr
    peer_cidr_v6         = var.peer_cidr_v6
    server_addresses     = local.server_addresses
    listen_port          = var.listen_port
    mtu                  = var.mtu
    host_key_secret_arn  = var.host_key_secret_arn
    peers                = local.peers
    peer_count           = length(local.peers)
    log_group            = aws_cloudwatch_log_group.handshakes.name
    agent_config         = local.agent_config
  })
}

resource "aws_instance" "this" {
  # checkov:skip=CKV_AWS_126:detailed monitoring is 5x the metric volume for a one-host tunnel whose alarm is on the free basic status checks (step 7.3) - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t3.nano is not EBS-optimized-capable; the instance type is D4's shape on the x86_64 image of 2026-08-20, chosen by measured price (docs/PRICING.md 3)
  # checkov:skip=CKV_AWS_88:A PUBLIC ADDRESS IS THE WHOLE POINT - this is the tunnel endpoint, the one internet-facing resource in the design, and it is what GuardDuty is enabled for at Stage 15. What bounds it is the security group (one UDP port, step 3.1) and the absence of port 22
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id              = var.public_subnet_ids[local.zone]
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.this.name

  # No public IP at launch, by the subnet's default - the [P] Elastic IP below is the address,
  # and a second auto-assigned one would be a second thing to reason about. The consequence is
  # an ordering note rather than a problem: for the seconds between RunInstances and the
  # association the host has no route out, and the first thing the user data does needs none -
  # the packages come from S3 through foundation's gateway endpoint. The SSM agent and the
  # CloudWatch agent retry until the address lands.
  associate_public_ip_address = false

  user_data = local.user_data
  # The user data is an instrument as well as a build: it carries the peer list and the key's
  # pointer, so a change to either must produce a new host. User data runs at first boot only
  # and the provider's default edits the attribute in place, which would leave a host whose
  # running configuration silently disagrees with the code that describes it (Stage 3's
  # finding). The key's value sits outside the user data, so a rotation alone changes nothing
  # here - procedure C's -replace is what rebuilds the host on the new key.
  user_data_replace_on_change = true

  # Kept on wherever it can be, and the exception is named rather than assumed: the check is off
  # only where no_masquerade_cidrs asks for it (6c step 4.7).
  #
  # For the tunnel this is why the value is not simply `false`: every packet wg0 forwards is
  # masqueraded to this instance's own address (step 1.2), so nothing legitimate is asymmetric,
  # and the check stays as anti-spoofing that fails in the useful direction - a wrong masquerade
  # rule drops traffic visibly instead of letting it leave with a ${var.peer_cidr} source that a
  # peering discards three hops later.
  #
  # An un-masqueraded destination breaks both legs at once, because source/destination checking
  # is applied by the ENI on the way in as well as out: the request leaves this host carrying a
  # `10.90.0.x` source that is not its own address, and the reply arrives carrying a `10.90.0.x`
  # destination that is not its own either. EC2 drops each before the kernel could route it, and
  # no iptables rule recovers from that - which is why every recipe that makes an instance
  # forward for somebody else disables the check.
  #
  # So the posture is unchanged while no_masquerade_cidrs is empty, which is the default and what
  # every reading before 2026-09-06 was taken under. A caller that fills the list trades this
  # host's anti-spoofing for a proxy access log that can tell two devices apart, and the trade is
  # bounded by that list plus the caller's route, not by this line.
  source_dest_check = length(var.no_masquerade_cidrs) == 0

  metadata_options {
    http_endpoint = "enabled"
    # IMDSv2 required - VP-4 fails otherwise, and it is not a formality here: this host is
    # world-reachable and holds a role credential, which is the textbook IMDSv1 target.
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = var.root_volume_size
    volume_type = "gp3"
  }

  # The Name tag is a contract: scripts/slices.py stops and starts this host by
  # `awsds-<env>-vpn` and ./aws/vpn.py measures it by the same string. A rename here is a
  # rename in both, and `make down` silently finding nothing is what it costs.
  tags = {
    Name = "awsds-${var.env}-vpn"
  }

  # The one attribute this resource must not read back, measured rather than foreseen (first
  # apply, 2026-08-17): with the host built and the [P] address associated below, the very next
  # `terraform plan` wanted to destroy and recreate the instance, on
  # `associate_public_ip_address = true -> false # forces replacement`. Nothing had changed.
  # The refresh reports the attribute from the instance's current public address, and the
  # aws_eip_association below is what gave it one - so the two resources disagree by
  # construction, for as long as they both exist, and the disagreement is ForceNew. Left
  # alone this is a permanent replacement loop: every apply rebuilds the tunnel endpoint,
  # and `plan` stops being able to say "nothing drifted" about anything else in the slice.
  #
  # The argument stays as false rather than being deleted - it is load-bearing at launch, the
  # only moment it means anything: no second, auto-assigned public IPv4 to reason about or to
  # pay for. What is ignored is only the read-back.
  lifecycle {
    ignore_changes = [associate_public_ip_address]
  }
}

# The address is allocated in the caller's [P] slice and associated here, with the instance
# that may be replaced. Verification (ii) is already answered by the documentation - an
# Elastic IP belongs to the network interface, which persists across stop/start, so the
# address stays associated (and bills) while the host is stopped and no re-association code
# is needed. The residual is the make down / make up diff of ./aws/vpn.py (VP-2).
resource "aws_eip_association" "this" {
  instance_id   = aws_instance.this.id
  allocation_id = var.eip_allocation_id
}
