# production/networking/hub-anchors.tf - Stage 6c step 4.1 (2026-09-06). The [P] half of the
# cut-over, applied BEFORE anything moves, so the blackout of pass 4 contains only the two
# irreversible-looking acts (the address transfer and the host builds) and none of the
# preparation.
#
# THIS FILE IS sandbox/foundation/vpn-anchors.tf's ARGUMENT, RE-MADE IN A NEW ACCOUNT, PLUS A
# SECOND HOST. That argument in one sentence: a reference is only worth writing if what it
# names outlives the thing that uses it - so the addresses, the security groups and the key's
# custody are [P] and created here, while the instances that consume them are [D] in
# production/vpn/ and production/proxy/ and may be replaced whenever the SSM-resolved AMI moves.
#
# WHAT IS NOT HERE, AND THE ABSENCE IS THE STEP AFTER THIS ONE: the WireGuard Elastic IP. It is
# not allocated - it is TRANSFERRED from Sandbox (4.5) and imported (4.6), which is what keeps
# every client's `Endpoint =` line unchanged. Allocating one here would produce a second address
# and a re-issue of every .conf, which is the fallback in the stage's risk table and not the plan.
#
# WHY TWO HOSTS AND NOT ONE (D38): the WireGuard host receives untrusted UDP from the internet
# and the Squid host parses untrusted internet responses. Separating them keeps a compromise of
# either off the other, and it costs one more t3.nano.

# The CostCenter override, per resource and for sandbox/foundation/vpn-anchors.tf's reason: the
# slice's provider default_tags say `stage-03`, which is true of the VPC this file sits beside
# and false of everything below it. The convention is CostCenter = the stage that CREATED the
# resource, and a slice-level default cannot tell two stages apart inside one slice. The other
# four mandatory tags still arrive from default_tags, unrepeated (Lesson 14).
locals {
  hub_anchor_tags = {
    CostCenter = "stage-06c"
  }
}

# ------------------------------------------------------- the WireGuard security group
#
# THE ESTATE'S ONE WORLD-OPEN RULE, MOVING ACCOUNTS. Exactly one port, open to the world, and
# nothing else - from 4.13 on, ./aws/networking.py section 9 and ./aws/vpn.py VP-3 must show
# this as the only world-open rule in the whole measured estate.
#
# BETWEEN THIS APPLY AND 4.13 THERE ARE TWO, AND THAT IS EXPECTED RATHER THAN A FINDING
# (Lesson 50 - a check written to a stage's FINAL expectation is red for every pass until the
# stage ends). Sandbox's `awsds-sandbox-vpn` group stands until its slice is destroyed at 4.13,
# because destroying it earlier would strand the host that still holds the address. The
# discriminator is the group NAME: two groups named `awsds-<env>-vpn` in two different accounts
# is the cut-over; any OTHER world-open rule, in either account, is the finding.
#
# NO PORT 22, EVER - the host's preinstalled SSM agent reaches the SSM endpoints outbound and
# Session Manager is the shell. NO `vpc_nat_cidrs` RULE EITHER: the isolated-tier NAT job that
# Sandbox's copy of this group carries dies with the buildbox's move (5.8), so it is not
# reproduced here. A rule description carries no apostrophe - AuthorizeSecurityGroupIngress
# rejects the whole call with InvalidParameterValue, measured in Stage 3.
resource "aws_security_group" "wireguard" {
  # checkov:skip=CKV2_AWS_5:attached by production/vpn/ - A DIFFERENT SLICE BY DESIGN (the [P]/[D] split this file opens with). The check cannot see across two state files
  # checkov:skip=CKV_AWS_382:egress is unrestricted BY DESIGN - this instance forwards every tunnel client's traffic at the proxy, so an egress allow-list here would duplicate Squid's and diverge from it. The perimeter is the proxy's allow-list and the SCP/RCP pair
  name        = "awsds-${var.env}-vpn"
  description = "WireGuard tunnel endpoint - the only human path into the private network (D4, D38, Stage 6c step 4.1)"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "WireGuard - the one world-open rule in this estate, and the tunnel itself"
    from_port   = 51820
    to_port     = 51820
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "unrestricted - this instance forwards tunnel traffic to the proxy and to RFC1918 only"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-vpn"
  })
}

# ----------------------------------------------------------- the proxy security group
#
# THE CLIENT LIST IS THE PEERING MATRIX, AND THAT SHARING IS DELIBERATE RATHER THAN LAZY
# (Lesson 51 - two intents sharing one list stay identical until they must differ). Under D38 a
# peering to this hub EXISTS IN ORDER TO REACH THE PROXY: three of the four rows in PEERINGS say
# so in their own comment. So "which ranges may open a TCP connection to Squid" and "which
# ranges are peered to this VPC" are one question at the reachability layer, and deriving the
# second from the first is what stops a spoke being peered and then silently left off the group.
#
# WHERE THE TWO INTENTS DO DIVERGE IS THE LAYER ABOVE, and it is the allow-list, not this group
# (4.9): the Workloads range is admitted here and reaches NOTHING, because its allow-list is
# empty by default. Reachability and policy are two spellings on purpose - a source that cannot
# open a socket produces a timeout nobody can debug, while a source that opens one and is
# refused by name produces a 403 with the name in it.
#
# 3128 AND NOT 80/443: an explicit proxy is a distinct listener, which is the whole of D38's
# "peering shares an address, never a path" (Lesson 44). Nothing here is a transparent intercept.
resource "aws_security_group" "proxy" {
  # checkov:skip=CKV2_AWS_5:attached by production/proxy/ - A DIFFERENT SLICE BY DESIGN, the same [P]/[D] split as the group above
  # checkov:skip=CKV_AWS_382:this host IS the estate's egress point - restricting its egress would be restricting the internet itself, and the control that does that is the allow-list rendered from the SSM parameter below
  name        = "awsds-${var.env}-proxy"
  description = "Squid explicit forward proxy - the single internet exit of this estate (D38, Stage 6c step 4.8)"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "explicit proxy - the peered spokes and the tunnel, and no other source"
    from_port   = 3128
    to_port     = 3128
    protocol    = "tcp"
    cidr_blocks = sort(concat([for p in var.peerings : p.peer_cidr], [var.wireguard_peer_cidr]))
  }

  egress {
    description = "unrestricted - the allow-list belongs to Squid, not to this group"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy"
  })
}

# ------------------------------------------------------------------ the proxy address
#
# ~USD 3.65/month, measured (docs/PRICING.md 3), billed from THIS apply rather than from the
# host's first boot - an Elastic IP is charged whether or not it is associated. That is the
# price of [P], and it buys the thing 4.12 depends on: the address the control-plane deny
# re-keys onto has to be knowable and stable BEFORE the host that wears it exists, because the
# union-then-trim of that step is written against it.
#
# It is also why ./aws/vpn.py VP-2's "orphan allocation" reading is a NOTE and not a FAIL
# between here and 4.8: an unassociated allocation is the expected state of this stretch.
resource "aws_eip" "proxy" {
  # checkov:skip=CKV2_AWS_19:the association is DELIBERATELY in another slice - this address is [P] so that a [D] instance rebuild cannot change it, and aws_eip_association lives in production/proxy/ where the instance does. The check cannot see across two state files
  domain = "vpc"

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy"
  })
}

# ------------------------------------------------------------- the WireGuard host key
#
# THE CONTAINER IS TERRAFORM'S, THE VALUE NEVER IS (decision 4, third design review): no
# aws_secretsmanager_secret_version exists anywhere in this repository. The user copies the
# value in by hand at 4.3 - get-secret-value in Sandbox, put-secret-value here - and the [D]
# host reads it at first boot with its own role, so the key crosses neither state nor plan.
#
# AND THE VALUE IS THE OLD ONE, COPIED, NEVER A NEW ONE GENERATED. The host's private key is
# what makes every client's `PublicKey =` line still valid; minting a fresh key here would be
# a silent re-issue of every peer's configuration on top of an account move. That is why 4.3
# is a [user] step in a stage whose applies are Claude's: the one act in pass 4 that cannot be
# undone by re-running anything.
resource "aws_secretsmanager_secret" "wireguard_host_key" {
  # checkov:skip=CKV2_AWS_57:automatic rotation is FORBIDDEN here by design, not missing - a rotation Lambda would replace the key without touching a single client config, which is the keys runbook's one rule violated by machine. Rotation is procedure C. ./aws/vpn.py VP-9 fails if RotationEnabled ever reads true
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - it delegates to IAM exactly as the Sandbox container it replaces does, and the containment here is the resource policy's explicit deny below, which a CMK would not sharpen
  name        = "awsds-${var.env}-vpn-host-key"
  description = "WireGuard host private key - value copied in by the user at Stage 6c step 4.3, never written by Terraform; read once per first boot by the [D] host's role. Rotation is manual and coordinated: docs/plan/runbooks/vpn.md, part K."

  # The undelete path, and the reason a routine destroy of this resource is never routine: the
  # NAME is unavailable until the window closes, so a slice rebuild that recreated the container
  # would fail on the name it just released.
  recovery_window_in_days = 30

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-vpn-host-key"
  })
}

# The containment rides on the OBJECT, not on six permission sets (Lesson 14's good direction):
# one deny here reaches every principal this account will ever hold. Scoped to the VALUE read
# alone, deliberately - denying secretsmanager:* would put the container's own management behind
# a deny only its author could lift, an availability trap with no confidentiality gain, since
# GetSecretValue IS the secret. Lesson 18 stands: this policy cannot constrain
# InfrastructureAccess, which authors it, and does not try to - Infrastructure is the enrollment
# writer of 4.3 and the recovery reader, carved out by name.
#
# The instance-role ARN is a NAME CONTRACT with the wireguard module (its iam.tf names the role
# awsds-<env>-vpn): the foundation cannot read a [D] slice's outputs, so the name is the seam.
# The SSO pattern is 1c decision 7's - the suffix is minted per account, an exact ARN breaks on
# re-provision.
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

# ------------------------------------------------------------- the proxy's allow-lists
#
# THE CONFIGURATION IS [P] DATA, NOT [D] DISK STATE (Lesson 4 - state living only inside an [E]
# or [D] resource is the recurring failure mode). Squid's allow-lists are the estate's egress
# policy; a copy of them that exists only in /etc/squid on an instance dies with the instance.
# So they live in this parameter, are rendered at boot, and reach a RUNNING host through 4.10's
# State Manager association - which is what lets a list change be an apply rather than a host
# replacement or a 30-second estate-wide outage.
#
# ONE PLANE PER SOURCE, AND THE PLANES ARE DERIVED FROM THE PEERING MATRIX rather than listed
# (Lesson 14): a spoke that gets peered gets a plane, so no spoke can be admitted by the
# security group above and then forgotten here. The step 4.9 prose enumerates four planes -
# tunnel, Sandbox, SharedServices, Workloads - and OMITS STAGING, which is a peered spoke with
# a runtime of its own; deriving rather than transcribing is what surfaces that.
#
# EMPTY IS THE SAFE DEFAULT AND THE HONEST ONE. Squid's last line is `http_access deny all`, so
# an empty allow-list denies everything by name rather than by timeout. 4.9 fills these; until
# it does, this parameter says exactly what the estate has decided so far, which is nothing.
locals {
  proxy_allowlist = merge(
    {
      # The institutional web filter - what a person on a company laptop may reach. Its source
      # is the tunnel range, which reaches Squid UN-MASQUERADED (4.7) so the access log carries
      # a per-device address.
      tunnel = {
        sources = [var.wireguard_peer_cidr]
        allow   = []
      }
    },
    {
      for p in var.peerings : "${p.peer_account}-${p.peer_slice}" => {
        sources = [p.peer_cidr]
        allow   = []
      }
    },
  )
}

resource "aws_ssm_parameter" "proxy_allowlist" {
  # checkov:skip=CKV_AWS_337:a String parameter, not a SecureString, so there is no KMS key to name - an egress ALLOW-LIST is a published control, not a credential, and its whole value is that ./aws/proxy.py (7.3) can diff running against committed without a decrypt permission
  # checkov:skip=CKV2_AWS_34:same reading - SecureString would encrypt a document whose contents are in this repository in plain text
  # `/datascience/` AND NOT `/awsds/`, AND THE RULE IS OLDER THAN THIS FILE (conventions "One
  # service refuses this prefix outright", measured at Stage 2's Validation 2026-08-16).
  # Parameter Store reserves every name beginning with `aws` or `ssm`, case-insensitive, and
  # `awsds` begins with `aws` - so `/awsds/...` fails PutParameter with
  # `AccessDeniedException: No access to reserved parameter name`, a message that reads like a
  # policy problem and is a naming one. This apply hit it anyway, because step 4.10 named the
  # parameter without naming the constraint: the note is repeated HERE, at the only site in the
  # repository that writes an SSM parameter, so the next one does not have to rediscover it.
  name        = "/datascience/${var.env}/proxy/allowlist"
  description = "Squid source-scoped allow-lists, one plane per peered spoke plus the tunnel (Stage 6c steps 4.9/4.10). Rendered at boot and by a State Manager association; never edited on the host."
  type        = "String"

  # Standard tier: free, and capped at 4 KB. An allow-list that outgrows that is the signal to
  # split per plane rather than to pay for Advanced (USD 0.05/parameter-month) - a per-plane
  # parameter is also what a per-plane review would want. ./aws/proxy.py reports the margin.
  tier = "Standard"

  value = jsonencode(local.proxy_allowlist)

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy-allowlist"
  })
}
