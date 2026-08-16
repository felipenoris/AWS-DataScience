# sandbox/probes/ - the SOURCE half of Stage 3's Deliverables: two throwaway hosts that
# measure what a describe call cannot, write their findings to the serial console, and are
# destroyed in the same sitting through `make down ENV=sandbox` (D11).
#
# WHY TWO HOSTS AND NOT ONE, which is the plan's own estimate revised by the route tables:
# the perimeter reading is only worth taking from a subnet WITH NO DEFAULT ROUTE - that
# absence is what makes a dnf success attributable to the S3 gateway policy rather than to
# the NAT - and the isolated tier, which is the only such tier, carries no peering route
# either. One host cannot be in both places, and moving a peering route into the [P] isolated
# route table to save an instance would edit the thing being measured.
#
# NEITHER PROBE CARRIES CREDENTIALS, and no IAM principal is created by this slice. The two
# endpoint-policy statements the perimeter reading exercises carry NO principal condition -
# one keys on aws:ResourceOrgID, the other enumerates AWS-owned buckets - so an anonymous
# request is judged by exactly the statement under test. An instance profile would have added
# a second possible explanation for every denial.

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

  # THE PERIMETER READING, and it is four readings rather than one because each of the first
  # three is worthless without the others (the Deliverable says so in its own words: "either
  # result alone proves nothing").
  #
  #   (1) THE PREMISE, measured rather than assumed. This subnet has no default route, so a
  #       host that is neither S3 nor DynamoDB must fail to connect. If this one SUCCEEDS,
  #       every reading under it is void - a dnf that worked would prove nothing about the
  #       allow-list.
  #   (2) WHERE THE MIRROR LIST COMES FROM. The stage's second log entry withdrew a caveat by
  #       claiming AL2023 serves its mirror list from the repository bucket itself. That claim
  #       is load-bearing here, so it is read rather than trusted: the repo file is printed,
  #       and cdn.amazonlinux.com is reached for on its own. If dnf fails AND the cdn is
  #       unreachable, the withdrawn caveat was right and the finding is the plan's, not the
  #       policy's - which is a different repair from an incomplete allow-list.
  #   (3) THE ALLOW-LISTED PATH, end to end and for real.
  #   (4) THE PAIR THAT MAKES (3) EVIDENCE. Two anonymous GETs of REAL, PUBLIC OBJECTS in
  #       REAL buckets - both Amazon Linux repository buckets in this region, both readable
  #       without credentials - differing in exactly one thing: the endpoint policy names
  #       al2023-repos-<region>-* and does not name amazonlinux-2-repos-<region>.
  #         200 / 403  -> the allow-list is what decides. The reading holds.
  #         200 / 200  -> the perimeter is open.
  #         403 / 403  -> something else is denying; nothing was measured.
  #         404 on the first -> al2023_repo_suffix is stale; reading (2) prints the current
  #                             value, and a 404 is deliberately NOT a 403 so the two cannot
  #                             be confused.
  #
  #       THE FIRST VERSION OF THIS READING USED BUCKETS THAT DO NOT EXIST, and it was wrong
  #       in the way Lesson 21 names: S3 answers NoSuchBucket BEFORE it evaluates
  #       authorization, so a nonexistent bucket returns 404 whatever the endpoint policy
  #       says. It returned 404/404 - which by the criterion above would have read as "the
  #       perimeter is open" - and the nonexistence chosen to keep the bucket's OWN policy
  #       out of the comparison had removed the policy under test along with it. Public
  #       objects in real buckets are what put the endpoint back in the decision.
  perimeter_user_data = <<-EOT
    #!/bin/bash
    exec > /dev/console 2>&1
    echo "=== AWSDS-PROBE-PERIMETER-BEGIN ==="

    echo "--- (1) the premise: no default route in this tier"
    if curl -s -o /dev/null --max-time 10 https://checkip.amazonaws.com/ ; then
      echo "premise BROKEN - reached the internet; every reading below is void"
    else
      echo "premise holds - no route to the internet (curl exit $?)"
    fi

    echo "--- (2) where the mirror list is served from"
    grep -h -E "^(mirrorlist|baseurl)" /etc/yum.repos.d/*.repo | sort -u
    if curl -s -o /dev/null --max-time 10 https://cdn.amazonlinux.com/ ; then
      echo "cdn.amazonlinux.com REACHED"
    else
      echo "cdn.amazonlinux.com unreachable (curl exit $?)"
    fi

    echo "--- (3) the allow-listed path, end to end"
    if dnf -q makecache --refresh > /tmp/dnf.log 2>&1 ; then
      echo "dnf makecache SUCCEEDED"
    else
      echo "dnf makecache FAILED"
      tail -12 /tmp/dnf.log
    fi

    echo "--- (4) the pair: two REAL public objects, one bucket on the allow-list"
    pair () {
      code=$(curl -s -o /tmp/body.xml -w '%%{http_code}' --max-time 20 "$2")
      err=$(grep -o '<Code>[^<]*' /tmp/body.xml | head -1 | cut -d'>' -f2)
      echo "s3-anon $1 -> HTTP $code $err"
    }
    pair "ON the allow-list      [expect 200]" \
      "https://al2023-repos-${var.region}-${var.al2023_repo_suffix}.s3.${var.region}.amazonaws.com/core/mirrors/latest/aarch64/mirror.list"
    pair "NOT on the allow-list  [expect 403]" \
      "https://amazonlinux-2-repos-${var.region}.s3.${var.region}.amazonaws.com/2/core/latest/aarch64/mirror.list"
    echo "=== AWSDS-PROBE-PERIMETER-END ==="
  EOT

  # THE PEERING READING - three attempts against ONE host, differing one variable at a time.
  #   permitted address + admitted port -> connects        (route and security group agree)
  #   FORBIDDEN address, same port      -> no answer       (only the route differs)
  #   permitted address, blocked port   -> no answer       (only the security group differs)
  # The two failures are not the same failure, and telling them apart is the point: the
  # blocked port produces a REJECT record in the target's flow log because the packet reaches
  # the ENI, while the forbidden address produces no record at all because the packet never
  # leaves this account. That pair is also the flow-log Deliverable, answered here.
  #
  # Both names are resolved FIRST and printed: a name that resolves proves the private zone
  # is associated with this VPC across the account boundary (the DNS Deliverable) and proves
  # the host is known - so silence afterwards has only one remaining explanation.
  peering_user_data = <<-EOT
    #!/bin/bash
    exec > /dev/console 2>&1
    echo "=== AWSDS-PROBE-PEERING-BEGIN ==="

    echo "--- names, in a private zone owned by the peer account"
    for n in ${var.target_name} ${var.target_forbidden_name} ; do
      ip=$(getent hosts "$n" | awk '{print $1}' | head -1)
      echo "dns $n -> $${ip:-NXDOMAIN}"
    done

    echo "--- reachability, one variable at a time"
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
    echo "=== AWSDS-PROBE-PEERING-END ==="
  EOT
}

# ------------------------------------------------------------------ the perimeter probe
#
# Egress is 0.0.0.0/0 ON PURPOSE, and the suppression below is the argument rather than an
# excuse: this probe's first reading asserts that it CANNOT reach the internet, and that
# assertion is only about ROUTING if nothing else is in the way. A tightened security group
# would produce the same silence and prove nothing - it would move the control being measured
# into the instrument measuring it (Lesson 13).
resource "aws_security_group" "perimeter" {
  # checkov:skip=CKV_AWS_382:deliberate - see the note above; the absent default route is the control under test, and an egress rule here would substitute for it
  name        = "awsds-${var.env}-probe-perimeter"
  description = "Stage 3 perimeter probe - egress deliberately unrestricted so the ROUTE is what is measured"
  vpc_id      = local.vpc_id

  egress {
    description = "unrestricted BY DESIGN - the isolated tier has no default route, and that absence is the reading"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "awsds-${var.env}-probe-perimeter"
  }
}

resource "aws_instance" "perimeter" {
  # checkov:skip=CKV2_AWS_41:NO instance profile, deliberately - and for this probe it is load-bearing rather than merely unnecessary: the endpoint-policy statements under test carry no principal condition, so an anonymous request is judged by exactly the statement being measured. Credentials would have added a second possible explanation for every denial (see the header)
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same day buys nothing - the reading is the serial console, and CloudWatch is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t4g.nano is not EBS-optimized-capable and the probe moves no volume traffic - the instance type is chosen by price (docs/PRICING.md 3)
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = "t4g.nano"

  # THE ISOLATED TIER, and the whole reading depends on it: no default route by design, the
  # S3 and DynamoDB gateway endpoints only.
  subnet_id              = data.terraform_remote_state.foundation.outputs.isolated_subnet_ids[local.zone]
  vpc_security_group_ids = [aws_security_group.perimeter.id]
  user_data              = local.perimeter_user_data
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
    Name = "awsds-${var.env}-probe-perimeter"
  }
}

# -------------------------------------------------------------------- the peering probe
#
# Egress is scoped to two ranges and both are needed: the peer VPC (the targets) and this
# VPC (the resolver at base+2, without which the names never resolve). The peer range is kept
# WHOLE so that the permitted address and the forbidden one are equally allowed here - the
# security group must not be part of what distinguishes them.
resource "aws_security_group" "peering" {
  name        = "awsds-${var.env}-probe-peering"
  description = "Stage 3 peering probe - egress to the peer VPC and to the resolver of this VPC"
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
    Name = "awsds-${var.env}-probe-peering"
  }
}

resource "aws_instance" "peering" {
  # checkov:skip=CKV2_AWS_41:NO instance profile, deliberately - and for this probe it is load-bearing rather than merely unnecessary: the endpoint-policy statements under test carry no principal condition, so an anonymous request is judged by exactly the statement being measured. Credentials would have added a second possible explanation for every denial (see the header)
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same day buys nothing - the reading is the serial console, and CloudWatch is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t4g.nano is not EBS-optimized-capable and the probe moves no volume traffic - the instance type is chosen by price (docs/PRICING.md 3)
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = "t4g.nano"

  # The PRIVATE tier, which is the one this account routes to the peer from. The plan named
  # the public subnet; private carries the same peering routes and needs no public address,
  # and the peer routes back to both - so the choice costs the reading nothing.
  subnet_id              = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids = [aws_security_group.peering.id]
  user_data              = local.peering_user_data
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
    Name = "awsds-${var.env}-probe-peering"
  }
}
