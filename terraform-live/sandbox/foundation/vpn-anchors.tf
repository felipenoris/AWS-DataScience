# sandbox/foundation/vpn-anchors.tf - Stage 4 step 2, and the whole file is an argument about
# WHERE these three live rather than about what they are.
#
# All three are named FROM OUTSIDE this stage: step 8's control-plane deny pins every persona
# permission set to the Elastic IP, Stage 5 step 1.3's bucket policy carries it as a branch
# (INT-05), Stage 5's EFS mount rule and Stage 7's GitLab rule both admit this security
# group by id across the peering, and the host-key secret is written by the user at
# enrollment (step 4.3) and read by every instance the [D] slice will ever boot. A reference
# is only worth writing if what it names outlives the thing that uses it - so the address,
# the group and the key's custody are [P], created here, while the instance that consumes
# them is [D] in sandbox/vpn/ and may be replaced whenever the SSM-resolved AMI moves
# (conventions 5.1 rule 5).
#
# THE CONSEQUENCE THAT MAKES IT LOAD-BEARING RATHER THAN TIDY: after step 8.3, an Elastic IP
# that changed would deny every persona every AWS API call until each client config and the
# permission-set fragment were edited together. [P] is what makes that impossible rather than
# unlikely.

# ------------------------------------------------------------------------ the address
#
# ~USD 3.65/month, measured (docs/PRICING.md 3) - billed whether or not it is associated and
# whether or not the host is running, which is why an orphan allocation is pure cost and
# ./aws/vpn.py VP-2 fails on one.
resource "aws_eip" "wireguard" {
  # checkov:skip=CKV2_AWS_19:the association is DELIBERATELY in another slice - this address is [P] so that a [D] instance rebuild cannot change it (step 2.1), and aws_eip_association lives in sandbox/vpn/ where the instance does. The check cannot see across two state files
  domain = "vpc"

  tags = {
    Name = "awsds-${var.env}-vpn"
  }
}

# ------------------------------------------------------------------ the security group
#
# Free, and referenced cross-slice AND cross-account (Stages 5 and 7): a security group that
# survives every lifecycle is the only kind worth referencing by id. Its CONTENTS are step 3
# and they are here rather than in vpn/ for the same reason the group is - a rule that lives
# in the [D] slice would be a rule that a rebuild can lose.
#
# WHY THE PEERS ADMIT THIS GROUP AND NEVER THE CLIENT RANGE (step 1.2): the instance is the
# NAT for every tunnel client, so a packet arriving in Production carries the instance's own
# private address. A rule written against 10.90.0.0/24 matches nothing, and the symptom is a
# mount or a clone that hangs rather than an error anybody can read.
resource "aws_security_group" "wireguard" {
  # checkov:skip=CKV2_AWS_5:attached by sandbox/vpn/ - A DIFFERENT SLICE BY DESIGN, and that separation is step 2.2 itself: the group outlives every instance that wears it, which is what makes it worth referencing by id from two other accounts. The check cannot see across two state files (the same reading the vpc module's endpoint SG carries)
  # checkov:skip=CKV_AWS_382:egress is unrestricted BY DESIGN - this instance is the NAT for every tunnel client, and a full tunnel (step 5.1) carries all of their traffic, so an egress allow-list here would be an allow-list on the operator's own browsing rather than a data-perimeter control. The perimeter that applies to it is the endpoint policies of foundation/ and the SCP/RCP pair, neither of which this group can substitute for
  name        = "awsds-${var.env}-vpn"
  description = "WireGuard tunnel endpoint - the only human path into the private network (D4, Stage 4)"
  vpc_id      = module.vpc.vpc_id

  # STEP 3.1 - EXACTLY ONE PORT, OPEN TO THE WORLD, AND NOTHING ELSE. From this stage on
  # ./aws/networking.py section 9 must show this as the only world-open rule in the whole
  # measured estate, and ./aws/vpn.py VP-3 fails on any second one.
  #
  # NO PORT 22, EVER. The host sits on a public subnet with a public address; its preinstalled
  # SSM agent reaches the SSM endpoints outbound with no interface endpoint anywhere in the
  # account, and Session Manager is the shell (verification (iii) measures exactly that).
  #
  # A RULE DESCRIPTION CARRIES NO APOSTROPHE: AuthorizeSecurityGroupIngress rejects the whole
  # call with InvalidParameterValue, measured in Stage 3.
  ingress {
    description = "WireGuard - the one world-open rule in this estate, and the tunnel itself"
    from_port   = 51820
    to_port     = 51820
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "unrestricted - this instance NATs every tunnel client, so this is not a perimeter"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "awsds-${var.env}-vpn"
  }
}

# ------------------------------------------------------------------------ the host key
#
# THE CONTAINER IS TERRAFORM'S, THE VALUE NEVER IS (decision 4, third design review
# 2026-08-16 - Stage 7's awsds-prod-gitlab-secrets idiom, arriving one stage early): no
# aws_secretsmanager_secret_version exists anywhere in this repository. The user writes the
# value once at enrollment (`put-secret-value --secret-string file://...`, step 4.3) and the
# [D] host reads it at first boot with its own role - so the key crosses neither state nor
# plan, the user data carries only this ARN, and every read of the value is a CloudTrail
# management event.
#
# WHY [P] AND NOT IN sandbox/vpn/: the value must outlive every instance replacement and
# every `make down` - the exact anchor argument of the address above - and a deleted secret
# blocks its own NAME for the length of the recovery window, so a slice rebuild that
# recreated the container would fail on the name it just released. The window is also the
# undelete path: deletion is scheduled, never immediate (runbook, procedure A).
resource "aws_secretsmanager_secret" "wireguard_host_key" {
  # checkov:skip=CKV2_AWS_57:automatic rotation is FORBIDDEN here by design, not missing - a rotation Lambda would replace the key without touching a single client config, which is the keys runbook's one rule violated by machine. Rotation is procedure C: put-secret-value, a deliberate -replace, every client config in the same minute. ./aws/vpn.py VP-9 fails if RotationEnabled ever reads true
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - it delegates to IAM exactly as the bootstrap CMK's one-statement policy does, and the containment here is the resource policy's explicit deny below, which a CMK would not sharpen. A dedicated CMK would cost more than the secret it wraps (USD 1.00 vs 0.40/month, docs/PRICING.md) and add a second key policy saying the same thing
  name        = "awsds-${var.env}-vpn-host-key"
  description = "WireGuard host private key - value written by the user at enrollment (Stage 4 step 4.3), never by Terraform; read once per first boot by the [D] host's role. Rotation is manual and coordinated: docs/plan/runbooks/vpn-keys.md, procedure C."

  # The undelete path (procedure A), and the reason a routine destroy of this resource is
  # never routine: the name is unavailable until the window closes.
  recovery_window_in_days = 30

  tags = {
    Name = "awsds-${var.env}-vpn-host-key"
  }
}

# THE CONTAINMENT RIDES ON THE OBJECT, not in six permission sets (Lesson 14's good
# direction): one deny here reaches every principal this account will ever hold - today's
# personas and Stage 6's notebook execution roles alike - without any per-set fragment to
# forget. Scoped to the VALUE read alone, deliberately: denying secretsmanager:* would put
# the container's own management (Delete, Restore, PutSecretValue, this policy itself)
# behind a deny only its author could lift - an availability trap with no confidentiality
# gain, since GetSecretValue IS the secret. Lesson 18 stands either way: this policy cannot
# constrain InfrastructureAccess, which authors it - and does not try to; Infrastructure is
# the enrollment writer and the recovery reader, carved out by name.
#
# The instance-role ARN is a NAME CONTRACT with the wireguard module (iam.tf names the role
# awsds-<env>-vpn), the same way the Name tag is a contract with scripts/slices.py: the
# foundation cannot read a [D] slice's outputs, so the name is the seam. The SSO pattern is
# 1c decision 7's - the suffix is minted per account, an exact ARN breaks on re-provision.
resource "aws_secretsmanager_secret_policy" "wireguard_host_key" {
  secret_arn = aws_secretsmanager_secret.wireguard_host_key.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyValueReadExceptHostAndInfrastructure"
        Effect    = "Deny"
        Principal = "*"
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
        Condition = {
          StringNotLike = {
            "aws:PrincipalArn" = [
              "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-vpn",
              "arn:${data.aws_partition.current.partition}:iam::*:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*",
            ]
          }
        }
      }
    ]
  })
}
