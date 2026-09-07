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

# ---------------------------------------------------------- the WireGuard address, IMPORTED
#
# NOT ALLOCATED - TRANSFERRED, and that is the whole reason this stage can move the tunnel
# between two AWS accounts without a single client editing a `.conf` file. `52.89.212.1` is the
# address every device pins as `Endpoint =`, and it is the same address it was in Sandbox.
#
# THE ALLOCATION ID DID **NOT** SURVIVE THE TRANSFER - measured 2026-09-06, and this closes the
# stage's verification 1, which AWS does not document either way:
#
#   in Sandbox     eipalloc-04397bfae0295333d
#   in Production  eipalloc-07edec7a52dc0820a
#
# So an id is a per-account fact about an address, not a property of it. Anything that had
# pinned the OLD id would now be pointing at nothing - which is why `[P]` outputs in this
# repository are read through remote state and never pasted, and why the import block below had
# to be written from a READING rather than from the plan's prose (Lesson 38).
#
# THE TAGS ARRIVED EMPTY. A transfer resets them, so the first apply after the import re-applies
# the whole project tag set - a `~ tags` on a resource nobody edited is the expected reading
# here exactly once.
resource "aws_eip" "wireguard" {
  # checkov:skip=CKV2_AWS_19:the association is DELIBERATELY in another slice - this address is [P] so that a [D] instance rebuild cannot change it, and aws_eip_association lives in production/vpn/ where the instance does. The check cannot see across two state files
  domain = "vpc"

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-vpn"
  })
}

# THE IMPORT BLOCK IS ONE-SHOT AND IS DELETED ONCE IT HAS RUN - that is the lifecycle of an
# `import {}`, not an oversight when it disappears from a later diff. It is a block rather than
# a `terraform import` command line so that the act is in the DIFF, reviewable, and so that the
# plan can be read before anything touches state.
import {
  to = aws_eip.wireguard
  id = "eipalloc-07edec7a52dc0820a"
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
# ---------------------------------------------------------------- 4.9, THE TWO FILTERS
#
# THE OBJECTIVES ASK FOR TWO DIFFERENT FILTERS AND THIS IS WHERE BOTH NOW LIVE. Until D38 they
# sat in two places and one of them has stopped working: a per-VPC DNS firewall inspects the
# names a client RESOLVES, and an explicit-proxy client resolves nothing - it hands Squid a name
# and Squid resolves it. So the DNS firewall can no longer see a laptop's browsing at all, and
# both filters move here, as SOURCE-SCOPED lists.
#
# THE TRANSLATION IS NOT A COPY, and this is the part that would be wrong if it had been treated
# as one. Route 53 DNS Firewall and Squid `dstdomain` spell subdomains DIFFERENTLY:
#
#   DNS Firewall   `example.com` is the APEX ONLY; `*.example.com` is subdomains and NOT the apex
#   Squid          `example.com` is that EXACT host; `.example.com` is the domain AND every
#                  subdomain of it
#
# So a DNS-firewall pair (`amazonaws.com`, `*.amazonaws.com`) collapses to ONE Squid entry
# (`.amazonaws.com`), and a lone DNS-firewall apex stays a lone Squid host. Transcribing the
# asterisks would have produced entries matching nothing, and the symptom would have been a
# refusal that looks exactly like a missing entry.
#
# THE WILDCARD IS GONE. The DNS firewall's list opens with a literal `"*"` - it was the
# permissive baseline of an earlier stage, and every entry after it is decoration while it
# stands. It is not carried across: this list is the first time the estate's egress is actually
# enumerated.
locals {
  # (i) THE CLIENT PLANE'S DENY LIST, AND IT REPLACED AN ALLOW-LIST THAT WAS THE WRONG SHAPE
  # (2026-09-07). What stood here was twenty-three AWS console, portal and sign-in families, seeded
  # from the SMUS network-isolation guide exactly as step 4.9 said to - and the result was a client
  # that could open the AWS console and nothing else on the internet. `objectives.md` asks for the
  # opposite: the client's internet is **monitored**, not restricted, and the restriction belongs to
  # the SageMaker compute. The full argument is on `proxy_allowlist` below, where the mode is set.
  #
  # EMPTY, BY DECISION (the user, 2026-09-07): everything permitted, everything logged, and this
  # list filled when a written policy exists to fill it from. **Empty is not "no control"** - the
  # control for this plane is the access log, which is what the objectives' word *monitored* names,
  # and it is already carrying a per-device address (`10.90.0.2`, measured at step 6.1).
  #
  # WHAT AN ENTRY HERE WILL MEAN when the list is filled: a name this estate's people may not
  # reach. It obeys the same `dstdomain` rules as the allow-lists - `.x` covers `x` and every
  # subdomain, and `x` beside `.x` in one acl is **FATAL** - so the plan-time collision check below
  # reads this list too.
  #
  # THE THREE GLOBAL DENIES STILL APPLY and are not repeated here: private destinations (the L7
  # bridge control), unsafe ports, and CONNECT to anything but 443. "Open" means open to the
  # internet, never open to the estate.
  proxy_deny_tunnel = []

  # (ii) SAGEMAKER'S STRICTER LIST - what a NOTEBOOK may reach. Today's DNS Firewall allow-list
  # moved across, minus the wildcard and minus every portal family above: a notebook does not
  # open the console, and a name it cannot reach is a name a job cannot post data to.
  proxy_allow_sandbox = [
    ".amazonaws.com",
    "public.ecr.aws",
    # OS packages.
    "archive.ubuntu.com",
    "security.ubuntu.com",
    # Python.
    "astral.sh",
    "releases.astral.sh",
    "pypi.org",
    "files.pythonhosted.org",
    # DuckDB.
    "blobs.duckdb.org",
    "extensions.duckdb.org",
    # Julia.
    "install.julialang.org",
    "julialang-s3.julialang.org",
    "pkg.julialang.org",
    "storage.julialang.net",
    "us-west.pkg.julialang.org",
    # Rust.
    "sh.rustup.rs",
    "index.crates.io",
    "static.crates.io",
    "static.rust-lang.org",
    # Source.
    "github.com",
  ]

  # (iii) THE BUILD HOSTS' PACKAGE SOURCES. SharedServices is where the buildbox lands when 5.8
  # moves it, and a build host needs what an image needs - which is the notebook list minus the
  # AWS control plane it does not call. Derived rather than retyped: the day somebody adds a
  # package source for notebooks, a build of that image needs it too, and two hand-kept copies
  # would part company on exactly that day (Lesson 33).
  # AND ONE NAME THIS PLANE NEEDS THAT NO OTHER DOES, ADDED 2026-09-06 AFTER A BUILD HOST FAILED
  # A REAL PULL. `public.ecr.aws` serves the token and the manifest and then **redirects the blob
  # download to a CloudFront distribution** - and Squid matches the hostname the client REQUESTED,
  # so a redirect is a NEW request with a NEW name that must itself be allowed. The old DNS
  # Firewall never met this: it evaluated a CNAME chain (and `TRUST_REDIRECTION_DOMAIN` handled
  # it), while an HTTP redirect is not a chain at all. Two systems, one intent, different
  # mechanisms - Lesson 53 from the other side.
  #
  # THE NAME WAS READ OUT OF THE ACCESS LOG, WHICH IS WHY 4.11 EXISTS. `docker pull` reported
  # `download failed after attempts=6: Forbidden` and named nothing; `/awsds/prod/proxy` carried
  # `CONNECT d5l0dvt14r5h8.cloudfront.net:443 403 TCP_DENIED`. That is the difference between a
  # proxy and a route, in one line of evidence.
  #
  # ONE DISTRIBUTION, NOT `.cloudfront.net`, AND THE ASYMMETRY IS DELIBERATE. The tunnel plane
  # carries `.cloudfront.net` - every distribution in the world - because the console's asset
  # delivery needs it and a person's browser is a different threat model. Granting that to a BUILD
  # host would hand it a namespace anyone can publish into, which is the exact widening splitting
  # the filters was meant to avoid.
  # REVISION TRIGGER, and it is a WHEN rather than an IF: this is a third party's name and AWS may
  # change it without notice. The symptom is a pull that fails with `Forbidden`, and the remedy is
  # to read the new name out of the same log. Do not "fix" it by widening to the namespace.
  proxy_allow_shared = concat(
    [for d in local.proxy_allow_sandbox : d if d != ".amazonaws.com"],
    ["d5l0dvt14r5h8.cloudfront.net"],
  )

  # THE PLANES, BY THE KEY THE MATRIX GENERATES. A key here that is not a plane below is a typo
  # that would otherwise be silently dropped by the merge - the precondition on the resource is
  # what turns it into a plan-time failure.
  # THE TUNNEL IS ABSENT FROM THIS MAP SINCE 2026-09-07, and its absence is the correction: this
  # map holds ALLOW-lists, and the client plane no longer has one. Its deny list is
  # `proxy_deny_tunnel` above, and `proxy_allowlist` is where the two are given their modes.
  proxy_allow_by_plane = {
    "sandbox-foundation"    = local.proxy_allow_sandbox
    "production-foundation" = local.proxy_allow_shared
    # EMPTY, AND EMPTY IS A DECISION RATHER THAN AN OMISSION. `production-workloads` is the
    # production runtime: everything it needs is an AWS API reached through an endpoint or the
    # proxy's own AWS entry, and nothing has yet named a public dependency for it. Staging is the
    # plane step 4.9 forgot entirely (it enumerated four sources and Staging is a fifth) - it is
    # here, empty, so that adding to it is an edit rather than a discovery.
    "production-workloads" = []
    "staging-foundation"   = []
  }

  # EVERY PLANE CARRIES A `mode`, AND THE TUNNEL'S IS THE ONE THAT IS NOT `allowlist`
  # (restructured 2026-09-07, correcting a requirements defect - see the block above the tunnel
  # entry). Two values, and the render script branches on exactly this field:
  #
  #   allowlist   the plane may reach the names in `allow` and nothing else. `deny` is unused.
  #               This is a RESTRICTION, and it is what the objectives ask for on the compute.
  #   open        the plane may reach anything EXCEPT the names in `deny`. `allow` is unused.
  #               This is MONITORING - the control is the access log, not the list - and it is
  #               what the objectives ask for on the client.
  #
  # BOTH KEYS ARE ALWAYS PRESENT, one of them empty, so no parser downstream has to handle a
  # missing field: `./aws/proxy.py` PX-3 and `./aws/dns-allowlist.py` both read this document, and
  # a shape that is sometimes one thing and sometimes another is how those two drift apart.
  # THE UNION THE COLLISION GATE READS - both kinds, keyed by plane, because a `deny` entry is
  # rendered into the same `dstdomain` syntax and carries the same fatal pair.
  proxy_collision_lists = {
    for plane, cfg in local.proxy_allowlist : plane => concat(cfg.allow, cfg.deny)
  }

  proxy_allowlist = merge(
    {
      # THE CLIENT PLANE IS `open`, AND THE ALLOW-LIST IT USED TO CARRY WAS A REQUIREMENTS DEFECT
      # (found by the user 2026-09-07, on the first browser that tried to use the proxy).
      # `objectives.md` is explicit in two places, and they agree:
      #
      #   "all internet access will be MONITORED - there will be an HTTP/HTTPS proxy between the
      #    VPN-connected client and the cloud's internet egress. Once on the VPN, the user can
      #    therefore use the browser to reach the internet"
      #   "the restriction is on the SageMaker-MANAGED COMPUTE, never on the user's (client's)
      #    machine"
      #
      # What stood here was a 23-name allow-list of AWS console and portal families, which made the
      # CLIENT's internet stricter than the COMPUTE's - the exact inversion of the requirement.
      # It came from step 4.9's paraphrase, *"the institutional web filter - what a person on a
      # company laptop may reach"*, plus a `squid.conf` that is default-deny: "filter" was
      # implemented as an allow-list. **An institutional web filter is a DENY-list over an open
      # default** - it blocks categories, it does not enumerate the web - and `CLAUDE.md` says the
      # objectives are "the specification a stage is measured against, so it is summarised
      # nowhere". The paraphrase became the specification, which is what that rule exists to stop.
      #
      # THE DENY LIST IS EMPTY BY DECISION (the user, 2026-09-07): everything permitted, everything
      # logged, and the list filled when there is a written policy to fill it from. Empty here does
      # NOT mean "no control" - it means the control is the access log in `/awsds/prod/proxy`,
      # which is what "monitored" names. The three global denies above every plane still apply to
      # this one: private destinations, unsafe ports, and CONNECT to anything but 443.
      tunnel = {
        sources = [var.wireguard_peer_cidr]
        mode    = "open"
        allow   = []
        deny    = local.proxy_deny_tunnel
      }
    },
    {
      # EVERY SPOKE STAYS `allowlist`, and that is the objectives' other half: the restriction
      # belongs to the compute. `sandbox-foundation` is SageMaker's list - D5 as amended by D38
      # calls it "the length of that compute's source-scoped allow-list on the proxy", which is
      # design A's short one rather than design B's empty one.
      for p in var.peerings : "${p.peer_account}-${p.peer_slice}" => {
        sources = [p.peer_cidr]
        mode    = "allowlist"
        allow   = lookup(local.proxy_allow_by_plane, "${p.peer_account}-${p.peer_slice}", [])
        deny    = []
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

  lifecycle {
    # A PLANE AUTHORED FOR A SPOKE THAT IS NOT PEERED IS A TYPO THE MERGE WOULD SWALLOW. The
    # planes come from `var.peerings`; the LISTS are authored by hand and keyed by the same
    # string. Misspell one - `staging` for `staging-foundation` - and the merge simply never
    # looks it up: the parameter applies clean, the spoke gets an empty list, and the symptom is
    # a refusal that reads exactly like a name nobody added. This turns it into a plan failure.
    precondition {
      condition     = length(setsubtract(keys(local.proxy_allow_by_plane), keys(local.proxy_allowlist))) == 0
      error_message = "proxy_allow_by_plane names a plane that no peering generates: ${join(", ", setsubtract(keys(local.proxy_allow_by_plane), keys(local.proxy_allowlist)))}. The plane keys are `tunnel` plus one `<peer_account>-<peer_slice>` per row of PEERINGS."
    }

    # THE 4 KB STANDARD-TIER CEILING, CHECKED AT PLAN TIME RATHER THAN MET AT APPLY TIME. Past it
    # the answer is a parameter per plane (which a per-plane review would want anyway), never
    # Advanced tier at USD 0.05/parameter-month for a list of domain names. 3800 leaves room for
    # the entries added between one reading of this line and the next.
    # THE APEX-PLUS-WILDCARD COLLISION, CAUGHT AT PLAN TIME (added 2026-09-06, after it took the
    # proxy's first boot down to an empty allow-list). Squid's `dstdomain` treats `x` beside `.x`
    # in ONE acl as **FATAL** - and the trap is that the list this was translated from, a Route 53
    # DNS Firewall allow-list, REQUIRED both forms to mean what `.x` means here. So every future
    # entry copied from that side carries the defect in, and the failure is invisible from this
    # repository: the render script reverts, the proxy keeps an EMPTY list, and every source is
    # refused by name.
    #
    # A DEEPER name under a wildcard (`a.b.example.com` under `.example.com`) is only a WARNING and
    # is deliberately NOT failed here - it is redundant rather than wrong, and a gate that refuses
    # both would refuse a list that works.
    #
    # IT READS BOTH LIST KINDS SINCE 2026-09-07. `deny` renders into a `dstdomain` acl exactly as
    # `allow` does, so an apex beside its own wildcard is just as fatal there - and a deny list is
    # the one somebody will paste names into in a hurry, from a blocklist written for a different
    # syntax. `local.proxy_collision_lists` is the union, so neither kind can be added later
    # without this gate seeing it.
    precondition {
      condition = length(flatten([
        for plane, names in local.proxy_collision_lists : [
          for d in names : "${plane}:${d}"
          if !startswith(d, ".") && contains(names, ".${d}")
        ]
      ])) == 0
      error_message = "a plane lists a domain AND its own wildcard, which Squid refuses with `FATAL: Bungled`: ${join(", ", flatten([for plane, names in local.proxy_collision_lists : [for d in names : "${plane}:${d} beside .${d}" if !startswith(d, ".") && contains(names, ".${d}")]]))}. Keep the dotted form only - `.x` matches the apex as well."
    }

    # EVERY PLANE'S MODE IS ONE OF TWO WORDS, AND AN UNKNOWN ONE MUST NOT REACH THE HOST. The
    # render script branches on this string; a typo would match neither branch, emit no block at
    # all for that plane, and the symptom would be a source that is admitted by the security group
    # and refused by name - reachable and mute, which is the failure this estate keeps meeting.
    precondition {
      condition     = alltrue([for cfg in values(local.proxy_allowlist) : contains(["allowlist", "open"], cfg.mode)])
      error_message = "every plane's `mode` must be `allowlist` (may reach only `allow`) or `open` (may reach anything but `deny`)."
    }

    precondition {
      condition     = length(jsonencode(local.proxy_allowlist)) < 3800
      error_message = "the rendered allow-list is ${length(jsonencode(local.proxy_allowlist))} bytes, against Parameter Store's 4 KB Standard-tier ceiling. Split it per plane rather than paying for Advanced."
    }
  }

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy-allowlist"
  })
}

# --------------------------------------------------------- the proxy's access log, and its key
#
# [P] AND NOT IN THE PROXY SLICE, WHICH IS THE WHOLE POINT (Stage 6c step 4.11). This log is the
# estate's record of what left it - Stage 11's egress evidence - and evidence that dies with the
# host it describes is not evidence. The [D] slice writes into this group; it does not own it,
# and `make down` does not take it.
#
# A CMK HERE, WHERE THE FLOW LOGS AND THE HANDSHAKE LOG BOTH DECLINED ONE, and the difference is
# the one their own comments draw: those are DEBUGGING logs, and this is an audit trail. The
# rate is measured, not estimated (docs/PRICING.md; Lesson 6) - ~USD 1.00/key-month, which the
# stage's cost table now carries as its one line that is neither an address nor a gateway.
module "proxy_log_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-proxy-log"
  description = "Squid access log - the estate's egress evidence (Stage 6c step 4.11, read by Stage 11)"

  # CloudWatch Logs encrypts and decrypts on this account's behalf, so the service principal
  # needs the key - scoped by `kms:EncryptionContext:aws:logs:arn` to THIS log group and no
  # other, which is the condition AWS's own documentation specifies and the reason the grant is
  # not "logs may use this key for anything in the account".
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowAccountIAM"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudWatchLogsForThisGroupOnly"
        Effect    = "Allow"
        Principal = { Service = "logs.${data.aws_region.current.region}.amazonaws.com" }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*",
        ]
        Resource = "*"
        Condition = {
          ArnEquals = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:/awsds/${var.env}/proxy"
          }
        }
      },
    ]
  })
}

# RETENTION IS 365 DAYS AND STEP 4.11 DID NOT NAME ONE - said here rather than left implicit.
# Every other log group in this repository is 30 days by decision, because every other one is a
# DIAGNOSTIC. This is the answer to "what left the estate, from which device, and when", which is
# a question asked after the fact and rarely within a month. Storage is USD 0.03/GB-month and a
# handful of people browsing produce megabytes, so the retention is chosen against the question
# rather than against the bill - but Stage 11 is where it is reviewed against a real volume.
resource "aws_cloudwatch_log_group" "proxy_access" {
  # checkov:skip=CKV_AWS_338:365 days IS the deliberate value - see the paragraph above; the one-year default this check wants is what is written
  name              = "/awsds/${var.env}/proxy"
  retention_in_days = 365
  kms_key_id        = module.proxy_log_key.key_arn

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy-access-log"
  })
}
