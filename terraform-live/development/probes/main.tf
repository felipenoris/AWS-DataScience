# development/probes/ - ONE host, and it is here because two things this stage claims had no
# reading anywhere else.
#
#   INT-09. The stage's Proves row is the Development-to-Production peering, and the
#   Deliverables measure Sandbox-to-Production. Those are different peering connections with
#   different routes on both sides; exercising one says nothing about the other, and INT-09
#   is the one a promotion will actually run over.
#
#   THE OTHER HALF OF THE DNS DELIVERABLE. It asks that probe.prod.internal resolve from a
#   Sandbox host AND from a Development host. The zone association reaching this VPC can be
#   READ from Route 53, but reading an association is not resolving a name (Lesson 5), and
#   the harness can produce this principal - so it is attempted rather than inferred. The
#   third clause, NXDOMAIN from Staging, waits on the vend: with no Staging VPC there is no
#   host to be refused, and an absent negative control is recorded rather than substituted.
#
# THERE IS NO PERIMETER PROBE HERE, and that is a decision rather than an omission: the S3
# gateway policy is byte-identical across the three accounts, `./aws/egress.py` EG-4 reads it
# in each of them, and the same allow-list measured a second time from a second account is a
# second copy of one reading. What differs per account is the ROUTE, which is what this host
# measures.
#
# NO IAM PRINCIPAL, no credentials, and the reading leaves by the serial console - same as
# the other two slices, for the same reasons.

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

locals {
  zone     = var.zone_ids[var.zone_index]
  vpc_id   = data.terraform_remote_state.foundation.outputs.vpc_id
  vpc_cidr = data.terraform_remote_state.foundation.outputs.vpc_cidr

  # THE SAME THREE ATTEMPTS the Sandbox peering probe makes, against the same target host,
  # over a DIFFERENT peering connection - which is the whole point of running them twice.
  #   permitted address + admitted port -> connects   (INT-09 route and security group agree)
  #   FORBIDDEN address, same port      -> no answer  (only the route differs)
  #   permitted address, blocked port   -> no answer  (only the security group differs)
  user_data = <<-EOT
    #!/bin/bash
    exec > /dev/console 2>&1
    echo "=== AWSDS-PROBE-INT09-BEGIN ==="

    echo "--- names, in a private zone owned by the peer account"
    for n in ${var.target_name} ${var.target_forbidden_name} ; do
      ip=$(getent hosts "$n" | awk '{print $1}' | head -1)
      echo "dns $n -> $${ip:-NXDOMAIN}"
    done

    echo "--- reachability over INT-09, one variable at a time"
    probe () {
      printf '%-58s ' "$1"
      code=$(curl -s -o /dev/null --max-time 10 -w '%%{http_code}' "$2" 2>/dev/null)
      rc=$?
      if [ "$rc" = "0" ] ; then echo "HTTP $code" ; else echo "no answer (curl exit $rc)" ; fi
    }
    probe "permitted address, admitted port  [expect HTTP]" \
      "http://${var.target_name}:${var.listener_port}/"
    probe "FORBIDDEN address, admitted port  [expect silence]" \
      "http://${var.target_forbidden_name}:${var.listener_port}/"
    probe "permitted address, blocked port   [expect silence]" \
      "http://${var.target_name}:${var.blocked_port}/"
    echo "=== AWSDS-PROBE-INT09-END ==="
  EOT
}

# Egress to the peer VPCs and to this VPC - the second is the Route 53 resolver at base+2,
# without which no name resolves. The peer range is kept WHOLE so the permitted address and
# the forbidden one are equally allowed here: the security group must not be part of what
# distinguishes them.
resource "aws_security_group" "int09" {
  # checkov:skip=CKV_AWS_382:the egress is scoped to two PRIVATE ranges and never to 0.0.0.0/0 - the rule fires on cidr_blocks it CANNOT RESOLVE, not on an open one (measured 2026-08-22 by contrast: the same block with a resolvable default PASSES, and only the default was removed). peer_cidrs is built by scripts/tfhygiene/backend.py from the closed CIDRS table - four RFC1918 /16s, and an account outside PROBE_PEERS raises rather than defaults - while local.vpc_cidr is foundation/ remote state; neither is literal in a .tf file, which is exactly why the scanner sees nothing
  name        = "awsds-${var.env}-probe-int09"
  description = "Stage 3 INT-09 probe - egress to the peer VPC and to the resolver of this VPC"
  vpc_id      = local.vpc_id

  egress {
    description = "the peer VPCs, WHOLE - both the permitted address and the forbidden one, so the route is the only difference"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = var.peer_cidrs
  }

  egress {
    description = "this VPC - the Route 53 resolver at base+2, without which no name resolves"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [local.vpc_cidr]
  }

  tags = {
    Name = "awsds-${var.env}-probe-int09"
  }
}

resource "aws_instance" "int09" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same day buys nothing - the reading is the serial console, and CloudWatch is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t4g.nano is not EBS-optimized-capable and the probe moves no volume traffic - the instance type is chosen by price (docs/PRICING.md 3)
  # checkov:skip=CKV2_AWS_41:NO instance profile, deliberately - the probe makes no AWS API call, and a role would be blast radius bought for nothing
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = "t4g.nano"

  # The PRIVATE tier: it is the only one carrying INT-09's routes. The public tier has an IGW
  # default and no peering route at all, and the isolated tier has neither.
  subnet_id              = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids = [aws_security_group.int09.id]
  user_data              = local.user_data
  # THE USER DATA IS THE INSTRUMENT, so a changed instrument must produce a NEW RUN:
  # user-data executes at first boot only, and the provider's default is to update the
  # attribute in place - which would leave the old reading running and look like a
  # re-measurement that agreed with itself.
  user_data_replace_on_change = true

  associate_public_ip_address = false

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = 8
    volume_type = "gp3"
  }

  tags = {
    Name = "awsds-${var.env}-probe-int09"
  }
}
