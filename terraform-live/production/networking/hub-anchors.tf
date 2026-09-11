# hub-anchors.tf - the [P] half of the 6c step 4.1 cut-over, applied before anything moves, so
# pass 4's blackout contains only the address transfer and the host builds.
#
# It re-makes sandbox/foundation/vpn-anchors.tf's argument in a new account, plus a second host: a
# reference is worth writing only if what it names outlives the thing that uses it. The addresses,
# the security groups and the key's custody are [P] and created here; the instances that consume
# them are [D] in production/vpn/ and production/proxy/ and may be replaced whenever the
# SSM-resolved AMI moves.
#
# The WireGuard Elastic IP is not allocated here. It is transferred from Sandbox (4.5) and imported
# (4.6), which keeps every client's `Endpoint =` line unchanged; allocating one would produce a
# second address and a re-issue of every .conf, the fallback in the stage's risk table.
#
# Two hosts and not one (D38): the WireGuard host receives untrusted UDP from the internet and the
# Squid host parses untrusted internet responses. Separating them keeps a compromise of either off
# the other, for one more t3.nano.

# CostCenter is overridden per resource, for sandbox/foundation/vpn-anchors.tf's reason: the slice's
# provider default_tags say `stage-03`, true of the VPC this file sits beside and false of everything
# below it, and a slice-level default cannot tell two stages apart inside one slice. The other four
# mandatory tags arrive from default_tags, unrepeated (Lesson 14).
locals {
  hub_anchor_tags = {
    CostCenter = "stage-06c"
  }
}

# ------------------------------------------------------- the WireGuard security group
#
# The estate's one world-open rule: exactly one port, open to the world, and nothing else. From 4.13
# on, ./aws/networking.py section 9 and ./aws/vpn.py VP-3 must show it as the only world-open rule in
# the measured estate. Until then Sandbox's `awsds-sandbox-vpn` group stands beside it, because
# destroying that slice earlier would strand the host still holding the address; the discriminator is
# the group name, so two groups named `awsds-<env>-vpn` in two accounts is the cut-over and any other
# world-open rule is the finding.
#
# No port 22: the host's preinstalled SSM agent reaches the SSM endpoints outbound and Session
# Manager is the shell. No `vpc_nat_cidrs` rule either, since the isolated-tier NAT job Sandbox's copy
# carries dies with the buildbox's move (5.8). A rule description carries no apostrophe:
# AuthorizeSecurityGroupIngress rejects the whole call with InvalidParameterValue (measured, Stage 3).
resource "aws_security_group" "wireguard" {
  # checkov:skip=CKV2_AWS_5:attached by production/vpn/, a different slice - the [P]/[D] split this file opens with. The check cannot see across two state files
  # checkov:skip=CKV_AWS_382:egress is unrestricted by design - this instance forwards every tunnel client's traffic at the proxy, so an egress allow-list here would duplicate Squid's and diverge from it. The perimeter is the proxy's allow-list and the SCP/RCP pair
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
# The client list is derived from the peering matrix (Lesson 51). Under D38 a peering to this hub
# exists in order to reach the proxy, so "which ranges may open a TCP connection to Squid" and
# "which ranges are peered to this VPC" are one question at the reachability layer; deriving the
# second from the first is what stops a spoke being peered and then left off the group.
#
# The two intents diverge one layer above, in the allow-list rather than in this group (4.9): the
# Workloads range is admitted here and reaches nothing, because its allow-list is empty by
# default. A source that cannot open a socket produces a timeout nobody can debug; a source that
# opens one and is refused by name produces a 403 carrying that name.
#
# Port 3128 and not 80/443: an explicit proxy is a distinct listener, so nothing here is a
# transparent intercept (D38, Lesson 44).
resource "aws_security_group" "proxy" {
  # checkov:skip=CKV2_AWS_5:attached by production/proxy/, a different slice - the same [P]/[D] split as the group above
  # checkov:skip=CKV_AWS_382:this host is the estate's egress point - restricting its egress would be restricting the internet itself, and the control that does that is the allow-list rendered from the SSM parameter below
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
# ~USD 3.65/month, measured (docs/PRICING.md 3), billed from this apply rather than from the host's
# first boot: an Elastic IP is charged whether or not it is associated. That is the price of [P],
# and it buys what 4.12 depends on - the address the control-plane deny re-keys onto has to be
# knowable and stable before the host that wears it exists, because the union-then-trim of that
# step is written against it.
#
# Between this apply and 4.8 the allocation is unassociated, which is why ./aws/vpn.py VP-2 reads
# "orphan allocation" as a NOTE and not a FAIL.
resource "aws_eip" "proxy" {
  # checkov:skip=CKV2_AWS_19:the association is deliberately in another slice - this address is [P] so that a [D] instance rebuild cannot change it, and aws_eip_association lives in production/proxy/ where the instance does. The check cannot see across two state files
  domain = "vpc"

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy"
  })
}

# -------------------------------------------------------- the WireGuard address, imported
#
# The address is transferred from Sandbox, not allocated, which is what lets the tunnel move
# between two AWS accounts without a single client editing a `.conf` file. `52.89.212.1` is the
# address every device pins as `Endpoint =`, and it is the same address it was in Sandbox.
#
# The allocation id did not survive the transfer (measured 2026-09-06, the stage's verification 1;
# AWS documents it neither way):
#
#   in Sandbox     eipalloc-04397bfae0295333d
#   in Production  eipalloc-07edec7a52dc0820a
#
# An id is a per-account fact about an address, not a property of it. Anything pinning the old id
# would now point at nothing, so `[P]` outputs in this repository are read through remote state and
# never pasted, and the import block below was written from a reading rather than from the plan's
# prose (Lesson 38).
#
# A transfer resets the tags, so the first apply after the import re-applies the whole project tag
# set: a `~ tags` on a resource nobody edited is the expected reading here exactly once.
resource "aws_eip" "wireguard" {
  # checkov:skip=CKV2_AWS_19:the association is deliberately in another slice - this address is [P] so that a [D] instance rebuild cannot change it, and aws_eip_association lives in production/vpn/ where the instance does. The check cannot see across two state files
  domain = "vpc"

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-vpn"
  })
}

# The import block is one-shot and is deleted once it has run; its disappearance from a later diff
# is the lifecycle of an `import {}`, not an oversight. It is a block rather than a `terraform
# import` command line so the act sits in the diff and the plan can be read before anything touches
# state.
import {
  to = aws_eip.wireguard
  id = "eipalloc-07edec7a52dc0820a"
}

# ------------------------------------------------------------- the WireGuard host key
#
# The container is Terraform's, the value never is (decision 4, third design review): no
# aws_secretsmanager_secret_version exists anywhere in this repository. The user copies the value
# in by hand at 4.3 - get-secret-value in Sandbox, put-secret-value here - and the [D] host reads
# it at first boot with its own role, so the key crosses neither state nor plan.
#
# The value copied in is the old key, never a freshly generated one. The host's private key is what
# keeps every client's `PublicKey =` line valid, so minting a new one here would silently re-issue
# every peer's configuration on top of an account move. 4.3 is therefore a [user] step in a stage
# whose applies are Claude's: the one act in pass 4 that re-running nothing can undo.
resource "aws_secretsmanager_secret" "wireguard_host_key" {
  # checkov:skip=CKV2_AWS_57:automatic rotation is forbidden here, not missing - a rotation Lambda would replace the key without touching a single client config, the one rule in the keys runbook that a machine must not violate. Rotation is procedure C. ./aws/vpn.py VP-9 fails if RotationEnabled ever reads true
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - it delegates to IAM exactly as the Sandbox container it replaces does, and the containment here is the resource policy's explicit deny below, which a CMK would not sharpen
  name        = "awsds-${var.env}-vpn-host-key"
  description = "WireGuard host private key - value copied in by the user at Stage 6c step 4.3, never written by Terraform; read once per first boot by the [D] host's role. Rotation is manual and coordinated: docs/plan/runbooks/vpn.md, part K."

  # The undelete path, and the reason destroying this resource is never routine: the name is
  # unavailable until the window closes, so a slice rebuild that recreated the container would fail
  # on the name it just released.
  recovery_window_in_days = 30

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-vpn-host-key"
  })
}

# The containment rides on the object rather than on six permission sets (Lesson 14): one deny here
# reaches every principal this account will ever hold. It is scoped to the value read alone, since
# denying secretsmanager:* would put the container's own management behind a deny only its author
# could lift, an availability trap with no confidentiality gain - GetSecretValue is the secret. This
# policy cannot constrain InfrastructureAccess, which authors it (Lesson 18), and does not try to:
# Infrastructure is the enrollment writer of 4.3 and the recovery reader, carved out by name.
#
# The instance-role ARN is a name contract with the wireguard module, whose iam.tf names the role
# awsds-<env>-vpn: the foundation cannot read a [D] slice's outputs, so the name is the seam. The
# SSO pattern is 1c decision 7's - the suffix is minted per account, and an exact ARN breaks on
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
# The configuration is [P] data, not [D] disk state (Lesson 4). Squid's allow-lists are the
# estate's egress policy, and a copy of them that exists only in /etc/squid on an instance dies
# with the instance. They live in this parameter, are rendered at boot, and reach a running host
# through 4.10's State Manager association, so a list change is an apply rather than a host
# replacement or a 30-second estate-wide outage.
#
# One plane per source, and the planes are derived from the peering matrix rather than listed
# (Lesson 14): a spoke that gets peered gets a plane, so no spoke can be admitted by the security
# group above and then forgotten here. The step 4.9 prose enumerates the tunnel, Sandbox,
# SharedServices and Workloads planes and omits Staging, a peered spoke with a runtime of its own;
# deriving rather than transcribing is what surfaces that.
#
# Squid's last line is `http_access deny all`, so an empty allow-list denies everything by name
# rather than by timeout.
# ---------------------------------------------------------------- 4.9, the two filters
#
# The objectives ask for two different filters and both live here. Until D38 they sat in two
# places and one of them stopped working: a per-VPC DNS firewall inspects the names a client
# resolves, and an explicit-proxy client resolves nothing - it hands Squid a name and Squid
# resolves it. The DNS firewall can no longer see a laptop's browsing at all, so both filters are
# here, as source-scoped lists.
#
# The translation is not a copy. Route 53 DNS Firewall and Squid `dstdomain` spell subdomains
# differently:
#
#   DNS Firewall   `example.com` is the apex only; `*.example.com` is subdomains and not the apex
#   Squid          `example.com` is that exact host; `.example.com` is the domain and every
#                  subdomain of it
#
# So a DNS-firewall pair (`amazonaws.com`, `*.amazonaws.com`) collapses to one Squid entry
# (`.amazonaws.com`), and a lone DNS-firewall apex stays a lone Squid host. Transcribing the
# asterisks would produce entries matching nothing, and the symptom would be a refusal that looks
# exactly like a missing entry.
#
# The DNS firewall's list opens with a literal `"*"`, the permissive baseline of an earlier stage,
# and every entry after it is decoration while it stands. It is not carried across.
locals {
  # (i) The client plane's deny list. `objectives.md` asks for the client's internet to be
  # **monitored**, not restricted; the restriction belongs to the SageMaker compute. The argument
  # is on `proxy_allowlist` below, where the mode is set.
  #
  # Empty by decision (the user, 2026-09-07): everything permitted, everything logged, and this
  # list filled when a written policy exists to fill it from. The control for this plane is the
  # access log, which is what the objectives' word *monitored* names, and it already carries a
  # per-device address (`10.90.0.2`, measured at step 6.1).
  #
  # An entry here names a destination this estate's people may not reach. It obeys the same
  # `dstdomain` rules as the allow-lists - `.x` covers `x` and every subdomain, and `x` beside `.x`
  # in one acl is fatal - so the plan-time collision check below reads this list too.
  #
  # The global denies still apply and are not repeated here: private destinations (the L7 bridge
  # control), unsafe ports, and CONNECT to anything but 443. "Open" means open to the internet,
  # never open to the estate.
  proxy_deny_tunnel = []

  # (ii) SageMaker's stricter list - what a notebook or Code Editor may reach. The DNS Firewall
  # allow-list moved across, minus the wildcard and minus every portal family: a notebook does not
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
    # R. Allowed 2026-09-11 (the user, 6d decision 6) on the reasoning that put `pypi.org` and
    # `index.crates.io` here: this plane already carries code download for three of the four
    # languages the environment supports, and R was the one arbitrarily without it. Measured before
    # the decision, from a space on `default-v0.2.0`: `install.packages` is `403 TCP_DENIED` on this
    # name, three times in one second, because R tries more than one index candidate - and it
    # reports none of them, saying `package 'R6' is not available for this version of R`, which
    # points a reader at the R version instead of at the perimeter.
    #
    # What it does not buy: CRAN serves SOURCE packages, so anything with C or Fortran compiles in
    # the space, and `images/dev-env/r/conda-packages.txt` stays the delivery path for the binary
    # half. The pure-R half now installs from a notebook.
    "cloud.r-project.org",
    # conda stays OFF, by the same decision. `repo.anaconda.com` and `conda.anaconda.org` are the
    # image build's channel and `production-foundation` is `open`, so a build reaches them; a solver
    # run inside a space would move the SageMaker Distribution's own pins, which is a mechanism
    # argument rather than a perimeter one. `repo.anaconda.com` was read as `403 TCP_DENIED` from a
    # space the same day, the negative control for the entry above.
    # Source control is deliberately absent: `github.com` was removed by the user 2026-09-09 (6d
    # 8.6), and it worked while it stood - 3.1 measured a clone from a JupyterLab space 2026-09-08.
    # A name is judged by whether an interactive compute plane should reach it, and source control
    # is the path by which code, and whatever a notebook has put beside it, leaves a governed
    # environment; `objectives.md` names data-leakage protection as a requirement of its own.
    # `api.github.com` and `raw.githubusercontent.com` came off for the same reason, though they
    # are the IDE's own startup traffic rather than anyone's clone - measured 2026-09-09, both
    # firing in bursts where the gallery is not touched at all.
    #
    # What this costs, so nobody re-adds it as a bug fix: `git clone`, `fetch` and `push` from a
    # Sandbox space fail. The build plane is unaffected - `production-foundation` is `open`, so the
    # buildbox and the future pipeline still reach GitHub, which is where a build belongs.
    #
    # The IDE's own hosts, allowed as one block 2026-09-09 (6d 8.6). Each was read as a `403` in
    # `/awsds/prod/proxy` after 8.4 put the proxy in the process, each fires at startup without
    # anyone asking for anything, and none has a VPC endpoint - the test that separates an
    # allow-list entry from a bypass-list one, since an endpoint-backed name allow-listed here would
    # work while arriving without `aws:SourceVpce`. Each sits in a different domain family, and none
    # of them is `.amazonaws.com`.
    "idetoolkits.amazonwebservices.com",
    "ide-toolkits.app-composer.aws.dev",
    # Regional, so it is interpolated, and the form is `${var.region}` rather than
    # `${data.aws_region.current.region}` because two readers parse this list and only one of them
    # is Terraform. `check-tf-conventions` catches the literal, a portability defect that reads as
    # data; `aws/dns-allowlist.py` catches the wrong interpolation, because it resolves
    # `${var.region}` and reports anything else as unresolved rather than guessing. Terraform
    # accepts both and says `No changes` either way, so only the instrument tells them apart. It is
    # the only regional entry on this plane.
    "sagemaker-unified-studio-mcp.${var.region}.api.aws",
    # The VS Code extension gallery needs both names (measured 2026-09-09, 6d 8.6). `open-vsx.org`
    # serves the API and the manifest; `openvsx.eclipsecontent.org` serves the `.vsix` bytes. The
    # install goes to the first, is redirected to the second, and Squid matches the hostname the
    # client requested, so a redirect is a new request with a new name and the first entry alone
    # authorised the question while refusing the answer. Read from `/awsds/prod/proxy`:
    # `open-vsx.org:443 200 TCP_TUNNEL` followed by `openvsx.eclipsecontent.org:443 403
    # TCP_DENIED`, the same shape as `public.ecr.aws`'s CloudFront distribution at 6c 5.8. The
    # tunnel plane, which is `open`, reached the second host with a 200 in the same minutes - the
    # negative control that says the name is refused by this list and by nothing else.
    #
    # Both are bare names. `dstdomain` matches a bare entry exactly, so neither covers a subdomain:
    # `eclipsecontent.org` is a namespace, and a namespace entry would authorise every host anyone
    # puts under it.
    "open-vsx.org",
    "openvsx.eclipsecontent.org",
  ]

  # (iii) The build plane's deny list (2026-09-08, the user, amending D38 section 6; 6d step 9).
  # `production-foundation` is `open`: a build host runs a Dockerfile that is in git and reviewed,
  # so its control is that review rather than a list of hostnames, and the restriction
  # `objectives.md` places on the SageMaker-managed compute does not reach it.
  #
  # `open` is not "no control". Three things bound this plane and none of them are in this list:
  # the global denies above every plane (private destinations, so the proxy cannot become an L7
  # bridge into the estate; unsafe ports; CONNECT to anything but 443); the security group, which
  # admits this source to 3128 and nothing else; and the absence of a default route in
  # SharedServices, which leaves the proxy the only way out. What changes is which public names are
  # reachable through that one door, and every one of them is still written to the access log.
  #
  # `sandbox-foundation` stays an allow-list: a name a build host may fetch is not thereby
  # reachable from a notebook.
  #
  # The plane is a CIDR, not a host (Lesson 29), which is the sentence to re-read before adding
  # anything to `VPC-SharedServices`. `10.30.0.0/16` is the whole VPC - the buildbox today, the
  # GitLab runners when Stage 7 puts them there - and anything else that lands in it inherits
  # `open` too. A host that should not have the open internet belongs in a VPC with its own plane.
  #
  # Empty, like the tunnel's: everything permitted, everything logged, and this list filled when
  # there is a written policy to fill it from. An entry here would be a name a build may not fetch,
  # a compromised package host say, and it obeys the same `dstdomain` rules as the allow-lists, so
  # the collision gate below reads it too.
  proxy_deny_shared = []

  # The allow-list planes, keyed as the peering matrix generates them. A key here that is not a
  # plane below is a typo the merge would silently drop; the precondition on the resource turns it
  # into a plan-time failure. The tunnel is absent because this map holds allow-lists and the client
  # plane has none - its deny list is `proxy_deny_tunnel` above, and `proxy_allowlist` is where
  # every plane is given its mode.
  proxy_allow_by_plane = {
    "sandbox-foundation" = local.proxy_allow_sandbox
    # Empty by decision. `production-workloads` is the production runtime: everything it needs is
    # an AWS API reached through an endpoint or the proxy's own AWS entry, and nothing has yet
    # named a public dependency for it. Staging is the plane step 4.9 omitted; it is here, empty,
    # so that adding to it is an edit rather than a discovery.
    "production-workloads" = []
    "staging-foundation"   = []
  }

  # The planes that are `open`. Membership of this map decides the mode: a peering plane appears in
  # exactly one of the two maps, an allow-list in `proxy_allow_by_plane` and a deny list here. Two
  # maps rather than one map of objects, so the mode cannot be set independently of the kind of
  # list the plane carries - otherwise a plane could say `open` and carry an allow-list, and the
  # render script would emit a block meaning the opposite of what it reads like. The preconditions
  # below fail a plane that is in both maps; a plane in neither is an allow-list with nothing on
  # it, which refuses everything.
  # `tunnel` is not here for the same reason it is not in the allow map: it is authored inline
  # below, because its source is a variable rather than a peering row.
  proxy_deny_by_plane = {
    "production-foundation" = local.proxy_deny_shared
  }

  # Every plane carries a `mode`, and the render script branches on exactly this field:
  #
  #   allowlist   the plane may reach the names in `allow` and nothing else. `deny` is unused.
  #               A restriction, which is what the objectives ask for on the compute.
  #   open        the plane may reach anything except the names in `deny`. `allow` is unused.
  #               Monitoring - the control is the access log, not the list - which is what the
  #               objectives ask for on the client.
  #
  # Both keys are always present, one of them empty, so no parser downstream has to handle a
  # missing field: `./aws/proxy.py` PX-3 and `./aws/dns-allowlist.py` both read this document, and
  # a shape that is sometimes one thing and sometimes another is how those two drift apart.
  # The collision gate reads the union of both kinds, keyed by plane, because a `deny` entry is
  # rendered into the same `dstdomain` syntax and carries the same fatal pair.
  proxy_collision_lists = {
    for plane, cfg in local.proxy_allowlist : plane => concat(cfg.allow, cfg.deny)
  }

  proxy_allowlist = merge(
    {
      # The client plane is `open`. `objectives.md` is explicit in two places, and they agree:
      #
      #   "all internet access will be monitored - there will be an HTTP/HTTPS proxy between the
      #    VPN-connected client and the cloud's internet egress. Once on the VPN, the user can
      #    therefore use the browser to reach the internet"
      #   "the restriction is on the SageMaker-managed compute, never on the user's (client's)
      #    machine"
      #
      # An institutional web filter is a **deny-list over an open default**: it blocks categories,
      # it does not enumerate the web (the user, 2026-09-07).
      #
      # The deny list is empty by decision (the user, 2026-09-07): everything permitted, everything
      # logged, and the list filled when there is a written policy to fill it from. The control for
      # this plane is the access log in `/awsds/prod/proxy`, which is what "monitored" names. The
      # global denies above every plane still apply here: private destinations, unsafe ports, and
      # CONNECT to anything but 443.
      tunnel = {
        sources = [var.wireguard_peer_cidr]
        mode    = "open"
        allow   = []
        deny    = local.proxy_deny_tunnel
      }
    },
    {
      # A spoke carrying compute stays `allowlist`, the objectives' other half: the restriction
      # belongs to the compute. `sandbox-foundation` is SageMaker's list - D5 as amended by D38
      # calls it "the length of that compute's source-scoped allow-list on the proxy", design A's
      # short list rather than design B's empty one. `production-foundation` is the exception, a
      # build plane rather than a compute one, `open` by the user's decision (see
      # `proxy_deny_shared` above and D38 section 6). The mode is not hard-coded here: it comes
      # from which of the two maps the plane is in, so this branch cannot contradict them.
      for p in var.peerings : "${p.peer_account}-${p.peer_slice}" => {
        sources = [p.peer_cidr]
        mode    = contains(keys(local.proxy_deny_by_plane), "${p.peer_account}-${p.peer_slice}") ? "open" : "allowlist"
        allow   = lookup(local.proxy_allow_by_plane, "${p.peer_account}-${p.peer_slice}", [])
        deny    = lookup(local.proxy_deny_by_plane, "${p.peer_account}-${p.peer_slice}", [])
      }
    },
  )
}

resource "aws_ssm_parameter" "proxy_allowlist" {
  # checkov:skip=CKV_AWS_337:a String parameter, not a SecureString, so there is no KMS key to name - an egress allow-list is a published control, not a credential, and its whole value is that ./aws/proxy.py (7.3) can diff running against committed without a decrypt permission
  # checkov:skip=CKV2_AWS_34:same reading - SecureString would encrypt a document whose contents are in this repository in plain text
  # `/datascience/` and not `/awsds/` (conventions, "One service refuses this prefix outright",
  # measured at Stage 2's Validation 2026-08-16). Parameter Store reserves every name beginning
  # with `aws` or `ssm`, case-insensitive, and `awsds` begins with `aws`, so `/awsds/...` fails
  # PutParameter with `AccessDeniedException: No access to reserved parameter name` - a message
  # that reads like a policy problem and is a naming one. The note is repeated here, at the only
  # site in the repository that writes an SSM parameter.
  name        = "/datascience/${var.env}/proxy/allowlist"
  description = "Squid source-scoped allow-lists, one plane per peered spoke plus the tunnel (Stage 6c steps 4.9/4.10). Rendered at boot and by a State Manager association; never edited on the host."
  type        = "String"

  # Standard tier: free, and capped at 4 KB. An allow-list that outgrows that is split per plane
  # rather than moved to Advanced (USD 0.05/parameter-month). ./aws/proxy.py reports the margin.
  tier = "Standard"

  value = jsonencode(local.proxy_allowlist)

  lifecycle {
    # A plane authored for a spoke that is not peered is a typo the merge would swallow. The planes
    # come from `var.peerings`; the lists are authored by hand and keyed by the same string.
    # Misspell one - `staging` for `staging-foundation` - and the merge never looks it up: the
    # parameter applies clean, the spoke gets an empty list, and the symptom is a refusal that reads
    # exactly like a name nobody added. This turns it into a plan failure.
    precondition {
      condition     = length(setsubtract(setunion(keys(local.proxy_allow_by_plane), keys(local.proxy_deny_by_plane)), keys(local.proxy_allowlist))) == 0
      error_message = "a plane map names a plane that no peering generates: ${join(", ", setsubtract(setunion(keys(local.proxy_allow_by_plane), keys(local.proxy_deny_by_plane)), keys(local.proxy_allowlist)))}. The plane keys are `tunnel` plus one `<peer_account>-<peer_slice>` per row of PEERINGS."
    }

    # A plane in both maps is a mode nobody chose. `mode` is decided by membership of
    # `proxy_deny_by_plane`, so a plane listed in both would be `open` and carry an allow-list: the
    # render script would emit the deny block and drop the allow list in silence, the permissive
    # half of the pair. It fails here rather than being resolved by precedence.
    precondition {
      condition     = length(setintersection(keys(local.proxy_allow_by_plane), keys(local.proxy_deny_by_plane))) == 0
      error_message = "a plane is in BOTH proxy_allow_by_plane and proxy_deny_by_plane: ${join(", ", setintersection(keys(local.proxy_allow_by_plane), keys(local.proxy_deny_by_plane)))}. A plane is an allow-list or it is `open`; membership of the deny map is what decides."
    }

    # The apex-plus-wildcard collision, caught at plan time (2026-09-06, after it took the proxy's
    # first boot down to an empty allow-list). Squid's `dstdomain` treats `x` beside `.x` in one acl
    # as **FATAL**, and the list this was translated from - a Route 53 DNS Firewall allow-list -
    # required both forms to mean what `.x` means here. Every entry copied from that side carries
    # the defect in, and the failure is invisible from this repository: the render script reverts,
    # the proxy keeps an empty list, and every source is refused by name.
    #
    # A deeper name under a wildcard (`a.b.example.com` under `.example.com`) is only a warning and
    # is not failed here: it is redundant rather than wrong, and a gate that refused both would
    # refuse a list that works.
    #
    # It reads both list kinds. `deny` renders into a `dstdomain` acl exactly as `allow` does, so an
    # apex beside its own wildcard is just as fatal there, and a deny list is the one somebody will
    # paste names into in a hurry from a blocklist written for a different syntax.
    # `local.proxy_collision_lists` is the union, so neither kind can be added later without this
    # gate seeing it.
    precondition {
      condition = length(flatten([
        for plane, names in local.proxy_collision_lists : [
          for d in names : "${plane}:${d}"
          if !startswith(d, ".") && contains(names, ".${d}")
        ]
      ])) == 0
      error_message = "a plane lists a domain AND its own wildcard, which Squid refuses with `FATAL: Bungled`: ${join(", ", flatten([for plane, names in local.proxy_collision_lists : [for d in names : "${plane}:${d} beside .${d}" if !startswith(d, ".") && contains(names, ".${d}")]]))}. Keep the dotted form only - `.x` matches the apex as well."
    }

    # An unknown `mode` must not reach the host. The render script branches on this string; a typo
    # would match neither branch and emit no block at all for that plane, leaving a source that is
    # admitted by the security group and refused by name - reachable and mute.
    precondition {
      condition     = alltrue([for cfg in values(local.proxy_allowlist) : contains(["allowlist", "open"], cfg.mode)])
      error_message = "every plane's `mode` must be `allowlist` (may reach only `allow`) or `open` (may reach anything but `deny`)."
    }

    # The 4 KB Standard-tier ceiling, checked at plan time rather than met at apply time. Past it
    # the answer is a parameter per plane, which a per-plane review would want anyway, never
    # Advanced tier at USD 0.05/parameter-month for a list of domain names. 3800 leaves room for
    # the entries added between one reading of this line and the next.
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
# [P] and not in the proxy slice (Stage 6c step 4.11). This log is the estate's record of what left
# it, Stage 11's egress evidence, and evidence that dies with the host it describes is not
# evidence. The [D] slice writes into this group, does not own it, and `make down` does not take
# it.
#
# A CMK here, where the flow logs and the handshake log both declined one: those are debugging
# logs, and this is an audit trail. The rate is measured, not estimated (docs/PRICING.md; Lesson
# 6) - ~USD 1.00/key-month.
module "proxy_log_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-proxy-log"
  description = "Squid access log - the estate's egress evidence (Stage 6c step 4.11, read by Stage 11)"

  # CloudWatch Logs encrypts and decrypts on this account's behalf, so the service principal needs
  # the key, scoped by `kms:EncryptionContext:aws:logs:arn` to this log group and no other. That is
  # the condition AWS's documentation specifies, and it is what keeps the grant from reading "logs
  # may use this key for anything in the account".
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

# Retention is 365 days, where every other log group in this repository is 30 days: the others are
# diagnostics, and this one answers "what left the estate, from which device, and when", a question
# asked after the fact and rarely within a month. Storage is USD 0.03/GB-month and a handful of
# people browsing produce megabytes, so the retention is chosen against the question rather than
# against the bill. Stage 11 reviews it against a real volume.
resource "aws_cloudwatch_log_group" "proxy_access" {
  # checkov:skip=CKV_AWS_338:365 days is the deliberate value - see the paragraph above; the one-year default this check wants is what is written
  name              = "/awsds/${var.env}/proxy"
  retention_in_days = 365
  kms_key_id        = module.proxy_log_key.key_arn

  tags = merge(local.hub_anchor_tags, {
    Name = "awsds-${var.env}-proxy-access-log"
  })
}
