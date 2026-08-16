# production/probes/ - the TARGET half of Stage 3's reachability Deliverables, and nothing
# else. [E] and deliberately short-lived: applied, read from the serial console, destroyed in
# the same sitting through `make down ENV=production` (D11). It exists to answer three
# questions no describe call can answer, and then to stop costing money.
#
# WHY A SLICE AND NOT A SCRIPT. aws/probes/ is the one folder under aws/ allowed to write,
# but its declared safety class is that NOTHING IS CREATED - and this creates instances. The
# expensive failure for a probe is not a wrong reading, it is an instance nobody turned off;
# a slice puts it under `make down` and under `make status`'s burn meter, where the machinery
# already refuses to skip what it has never heard of (Stage 2 step 8).
#
# WHAT IT IS FOR, one line per Deliverable:
#   "the Sandbox probe reaches the Production probe on the GitLab port"   -> the listener
#   "the same probe reaches NOTHING in a Production subnet outside the
#    permitted one"                                                       -> the SECOND ENI
#   "a temporary probe.prod.internal A record resolves from a Sandbox
#    host"                                                                -> the two records
#
# THE SECOND ENI IS THE WHOLE DESIGN, and it is what turns the negative reading into
# evidence rather than an absence (Lesson 13; Lesson 26's negative control). One host, ONE
# process bound to 0.0.0.0, ONE security group attached to BOTH interfaces - so the permitted
# address and the forbidden one differ in exactly one thing: whether Sandbox holds a route to
# the range. Two separate hosts would have left "nothing answered" indistinguishable from
# "nothing was listening there", which is the reading this pair exists to rule out.
#
# NO IAM PRINCIPAL IS CREATED HERE, and that is a design choice rather than an omission: the
# probes need no credentials (see sandbox/probes/main.tf on why the perimeter readings are
# anonymous), so an instance profile would be blast radius bought for nothing.

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# Resolved at plan time from the region's own catalog rather than pinned: a probe destroyed
# the same day has no reproducibility claim to protect, and a stale AMI literal in a tracked
# file is the kind of thing that outlives its reason.
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

locals {
  zone = var.zone_ids[0]

  # Both interfaces land in the same AZ because a secondary ENI cannot cross one.
  private_subnet_id  = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  isolated_subnet_id = data.terraform_remote_state.foundation.outputs.isolated_subnet_ids[local.zone]

  # The listener binds 0.0.0.0 so ONE process answers on BOTH addresses - see the header.
  # rp_filter is switched off because the reply to a packet arriving on the secondary
  # interface would leave by the primary one's default route; leaving it on would add a
  # second possible cause to a reading that is supposed to have exactly one.
  user_data = <<-EOT
    #!/bin/bash
    exec > /dev/console 2>&1
    sysctl -w net.ipv4.conf.all.rp_filter=0
    sysctl -w net.ipv4.conf.default.rp_filter=0
    mkdir -p /tmp/probe-root
    echo "awsds-stage03-probe-target" > /tmp/probe-root/index.html
    nohup python3 -m http.server ${var.listener_port} --bind 0.0.0.0 \
      --directory /tmp/probe-root > /tmp/listener.log 2>&1 &
    sleep 8
    echo "=== AWSDS-PROBE-TARGET-BEGIN ==="
    ip -4 -o addr show scope global | awk '{print "addr", $2, $4}'
    echo "listening:"
    ss -ltn | grep -E ":${var.listener_port}\b" || echo "  NOTHING ON ${var.listener_port} - every peering reading below is void"
    echo "=== AWSDS-PROBE-TARGET-END ==="
  EOT
}

# Ingress on the listener port from the whole source VPC, and NO egress rule at all: a
# security group is stateful, so replies to an accepted inbound connection leave without one,
# and the target has nothing of its own to reach. var.blocked_port is absent on purpose -
# that absence is the REJECT half of the flow-log Deliverable.
resource "aws_security_group" "probe" {
  name        = "awsds-${var.env}-probe"
  description = "Stage 3 reachability target - listener port from the peer VPC only, no egress"
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

  tags = {
    Name = "awsds-${var.env}-probe"
  }
}

# One rule per source account - Sandbox for the Deliverables, Development for INT-09.
resource "aws_vpc_security_group_ingress_rule" "listener" {
  for_each = toset(var.peer_cidrs)

  security_group_id = aws_security_group.probe.id
  # No apostrophe anywhere in this string, and that is a constraint rather than a style:
  # AuthorizeSecurityGroupIngress accepts descriptions from a fixed character set that does
  # not include one, and rejects the call with InvalidParameterValue.
  description = "the GitLab port, from a source VPC range of a peer account (Stage 3 Deliverables, INT-09)"

  cidr_ipv4   = each.value
  ip_protocol = "tcp"
  from_port   = var.listener_port
  to_port     = var.listener_port
}

# The forbidden address. It carries the SAME security group as the primary interface, which
# is what keeps the security group out of the comparison.
resource "aws_network_interface" "isolated" {
  subnet_id       = local.isolated_subnet_id
  security_groups = [aws_security_group.probe.id]
  description     = "Stage 3 probe - an address in a tier the source account has no route to"

  tags = {
    Name = "awsds-${var.env}-probe-isolated"
  }
}

resource "aws_instance" "target" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same day buys nothing - the reading is the serial console, and CloudWatch is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t4g.nano is not EBS-optimized-capable and the probe moves no volume traffic - the instance type is chosen by price (docs/PRICING.md 3), not by throughput
  # checkov:skip=CKV2_AWS_41:NO instance profile, deliberately - the probe makes no AWS API call, and a role would be blast radius bought for nothing. The header says why the SOURCE probes must stay anonymous; this host is kept credential-free for the same reason
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = "t4g.nano"
  subnet_id     = local.private_subnet_id

  vpc_security_group_ids = [aws_security_group.probe.id]
  user_data              = local.user_data
  # THE USER DATA IS THE INSTRUMENT, so a changed instrument must produce a NEW RUN:
  # user-data executes at first boot only, and the provider's default is to update the
  # attribute in place - which would leave the old reading running and look like a
  # re-measurement that agreed with itself.
  user_data_replace_on_change = true

  # No public address, and none is reachable anyway - the private tier has no IGW route.
  associate_public_ip_address = false

  # IMDSv2 only. The probe reads no credentials, but a host that is deliberately exposed to
  # a peered network is exactly where the weaker service would be worth someone's time.
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
    Name = "awsds-${var.env}-probe-target"
  }
}

resource "aws_network_interface_attachment" "isolated" {
  instance_id          = aws_instance.target.id
  network_interface_id = aws_network_interface.isolated.id
  device_index         = 1
}

# The two names, in the private zone foundation/ created and pass 2 associated with the
# source account's VPC. THE NAMES ARE THE INTERFACE: the source slice never learns an
# address, so nothing is pasted and nothing is read across the account boundary - and a name
# that resolves in Sandbox is itself the cross-account private-DNS Deliverable, answered on
# the way past rather than as a step of its own.
resource "aws_route53_record" "probe" {
  zone_id = data.terraform_remote_state.foundation.outputs.prod_internal_zone_id
  name    = "probe.prod.internal"
  type    = "A"
  ttl     = 60
  records = [aws_instance.target.private_ip]
}

resource "aws_route53_record" "probe_isolated" {
  # checkov:skip=CKV2_AWS_23:the record DOES have an attached resource - a secondary ENI, whose private_ip the check cannot trace the way it traces an aws_instance attribute. That the address belongs to an interface rather than to an instance is the design, not an oversight
  zone_id = data.terraform_remote_state.foundation.outputs.prod_internal_zone_id
  name    = "probe-isolated.prod.internal"
  type    = "A"
  ttl     = 60

  # Deliberately the SECONDARY interface: same host, same listener, unroutable from Sandbox.
  records = [aws_network_interface.isolated.private_ip]
}
