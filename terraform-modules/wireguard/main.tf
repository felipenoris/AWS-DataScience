# wireguard - the tunnel endpoint of D4, and the repository's first [D] resource.
#
# WHAT IS IN THIS MODULE AND WHAT IS DELIBERATELY NOT. Here: the instance, its user data, its
# role, the handshake log and the alarm - everything a rebuild may legitimately replace. NOT
# here: the Elastic IP and the security group, which are [P] in the caller's foundation/
# because things OUTSIDE this stage name them (step 8's control-plane deny names the address;
# Stage 5's EFS rule and Stage 7's GitLab rule name the group, across an account boundary).
#
# SO A REBUILD IS MADE INVISIBLE RATHER THAN PREVENTED, and it will happen: `ami` resolves
# through an SSM public parameter that moves with every AL2023 release, and a changed `ami`
# forces replacement. Everything a client config pins survives it - the address because it is
# [P], the server's public key because its private half lives in the caller's [P] Secrets
# Manager secret, fetched at first boot, rather than being generated on the host (step 4.3;
# decision 4, third review).

data "aws_partition" "current" {}

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

locals {
  zone = var.zone_ids[var.zone_index]

  # The tunnel addressing, derived in ONE place from the allocation table's range: the server
  # takes .1, every device takes the host number authored beside its public key. Deriving the
  # device numbers from map ORDER instead was the alternative, and it fails the way Lesson 4
  # fails - deleting one revoked device would renumber every device after it, invalidating
  # client configs nobody edited.
  server_address = "${cidrhost(var.peer_cidr, 1)}/${split("/", var.peer_cidr)[1]}"

  peers = {
    for name, p in var.peers : name => {
      public_key = p.public_key
      address    = cidrhost(var.peer_cidr, p.host)
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

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    peer_cidr           = var.peer_cidr
    server_address      = local.server_address
    listen_port         = var.listen_port
    host_key_secret_arn = var.host_key_secret_arn
    peers               = local.peers
    peer_count          = length(local.peers)
    log_group           = aws_cloudwatch_log_group.handshakes.name
    agent_config        = local.agent_config
  })
}

resource "aws_instance" "this" {
  # checkov:skip=CKV_AWS_126:detailed monitoring is 5x the metric volume for a one-host tunnel whose alarm is on the free basic status checks (step 7.3) - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t4g.nano is not EBS-optimized-capable; the instance type is D4's, chosen by measured price (docs/PRICING.md 3)
  # checkov:skip=CKV_AWS_88:A PUBLIC ADDRESS IS THE WHOLE POINT - this is the tunnel endpoint, the one internet-facing resource in the design, and it is what GuardDuty is enabled for in step 10. What bounds it is the security group (one UDP port, step 3.1) and the absence of port 22
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id              = var.public_subnet_ids[local.zone]
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.this.name

  # NO PUBLIC IP AT LAUNCH, BY THE SUBNET'S DEFAULT - the [P] Elastic IP below is the address,
  # and a second auto-assigned one would be a second thing to reason about. The consequence is
  # an ordering note rather than a problem: for the seconds between RunInstances and the
  # association the host has no route out, and the first thing the user data does needs none -
  # the packages come from S3 through foundation's GATEWAY endpoint. The SSM agent and the
  # CloudWatch agent retry until the address lands.
  associate_public_ip_address = false

  user_data = local.user_data
  # THE USER DATA IS AN INSTRUMENT AS WELL AS A BUILD: it carries the peer list and the key's
  # POINTER, so a change to either must produce a NEW HOST. User data runs at first boot only
  # and the provider's default edits the attribute in place, which would leave a host whose
  # running configuration silently disagrees with the code that describes it (Stage 3's
  # finding). The flip side, since the third review: the key's VALUE sits outside the user
  # data, so a rotation alone changes nothing here - procedure C's -replace is what rebuilds
  # the host on the new key.
  user_data_replace_on_change = true

  # KEPT ON, DELIBERATELY, ON A HOST THAT FORWARDS PACKETS. The usual NAT-instance recipe
  # disables it; here every forwarded packet is masqueraded to this instance's own address
  # (step 1.2), so nothing legitimate is asymmetric and the check stays as anti-spoofing. It
  # also fails in the useful direction: if the masquerade rule is ever wrong, traffic is
  # dropped visibly instead of leaving with a ${var.peer_cidr} source that the peering would
  # discard three hops later, where nobody would connect the two.
  source_dest_check = true

  metadata_options {
    http_endpoint = "enabled"
    # IMDSv2 REQUIRED - VP-4 fails otherwise, and it is not a formality here: this host is
    # world-reachable and holds a role credential, which is the textbook IMDSv1 target.
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = var.root_volume_size
    volume_type = "gp3"
  }

  # THE NAME TAG IS A CONTRACT, not a label: scripts/slices.py stops and starts this host by
  # `awsds-<env>-vpn` and ./aws/vpn.py measures it by the same string. A rename here is a
  # rename in both, and `make down` silently finding nothing is what it costs.
  tags = {
    Name = "awsds-${var.env}-vpn"
  }
}

# The address is allocated in the caller's [P] slice and ASSOCIATED here, with the instance
# that may be replaced. Verification (ii) is already answered by the documentation - an
# Elastic IP belongs to the network interface, which persists across stop/start, so the
# address stays associated (and bills) while the host is stopped and no re-association code
# is needed. The residual is the make down / make up diff of ./aws/vpn.py (VP-2).
resource "aws_eip_association" "this" {
  instance_id   = aws_instance.this.id
  allocation_id = var.eip_allocation_id
}
