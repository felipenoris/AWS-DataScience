# production/buildbox/ - THE BUILD HOST (Stage 6 step 5.0), layer [E].
#
# IT MOVED HERE FROM `sandbox/buildbox/` AT 6c STEP 5.8 (2026-09-06), AND THE MOVE IS FORCED
# RATHER THAN TIDY. Its only egress was a default route pointing at the WireGuard host's ENI, in
# the Sandbox isolated tier. D38 removed every default route in the estate and moved the WireGuard
# host to `VPC-Networking` - and a route target cannot live in another VPC, so the old shape was
# not merely deprecated, it was unbuildable. This is a destroy-and-create rather than a state
# migration (Recipe E): the host is [E], its volume dies with the session, and it holds nothing
# that survives one.
#
# WHY IT EXISTS, and it is one measurement rather than a preference: the images this project
# runs on are linux/amd64 - SageMaker instance types are x86 and the sagemaker-distribution
# base publishes no arm64 tag at all - and the laptop this repository is driven from is
# arm64. Building there means qemu for every layer; more to the point, the laptop has no
# docker at all. So the build moves to a machine of the right architecture, inside the
# perimeter, that exists only while a build is running.
#
# WHAT IT IS NOT: a workstation, and nothing here should make it one. It holds no data, it is
# destroyed at the end of the session, and its state carries no secret. Anything worth
# keeping leaves it as an image in ECR or does not leave it at all.
#
# ------------------------------------------------------------------------------------------
# THE NETWORK SHAPE, WHICH IS THE WHOLE DESIGN, AND IT IS TWO SENTENCES:
#
#   IN   NOTHING. There is no ingress rule at all, and that is the design rather than an
#        omission - decided by the user 2026-08-21, after a measurement made the earlier shape
#        dishonest. This host has no public address and sits in a tier with no internet
#        gateway; the only way to a shell is Session Manager, which needs NO inbound rule
#        because the agent holds the channel open OUTBOUND.
#
#        WHAT THE RULE THAT USED TO BE HERE WAS FOR, AND WHY IT WENT. It admitted the
#        WireGuard client range on every port, to deliver "reachable only with the tunnel up".
#        Two things were wrong with it. It did not gate the SHELL - `ssm start-session` goes
#        laptop -> the SSM API -> the agent's outbound channel, and this group never sees it,
#        so the claim was false for the one path anybody actually uses. And it was a grant with
#        no consumer: AL2023 runs sshd, so the rule left port 22 REACHABLE from the tunnel on a
#        host with zero authorized keys - one `key_name` away from a second way in that nothing
#        in this design asked for. A rule nobody uses is not neutral; it is the shape a later
#        convenience grows out of (Lesson 5).
#
#        SO THE REQUIREMENT WAS WITHDRAWN RATHER THAN FAKED. "Reachable only over the VPN" is
#        not delivered for this host, and saying so is the point - the access path is IAM, and
#        for InfrastructureAccess it does not require the tunnel (open question 17, the user's
#        option (a): the administrative credential is also the fire escape). If a port served
#        during a build ever has to be reached from the laptop, the answer is SSM PORT
#        FORWARDING - AWS-StartPortForwardingSession - which is still Session Manager and
#        still needs no ingress rule.
#
#   OUT  AS A CLIENT OF THE PROXY, AND THAT IS THE WHOLE CHANGE. There is no default route in
#        this tier and there will not be one. Three different paths leave this host, and reading
#        them apart is what makes a failure diagnosable:
#
#          the internet         -> `http_proxy` at `proxy.awsds.internal:3128`, over the
#                                  SharedServices <-> Networking peering. The
#                                  `production-foundation` plane, `open` since 2026-09-08
#                                  (D38 section 6 amended): any public name, all of it logged.
#                                  It was an allow-list until then; a build host's control is
#                                  the reviewed Dockerfile, not a list of hostnames.
#          AWS APIs             -> this VPC's interface endpoints, which is why `no_proxy` is
#                                  generated rather than written (5.6). Session Manager is one
#                                  of these, and it must NOT be proxied.
#          S3 and DynamoDB      -> the [P] GATEWAY endpoints, by route. Free, and the reason an
#                                  ECR pull is cheap: the manifest comes over `ecr.dkr` and the
#                                  LAYERS come from S3 through that gateway.
#
#        NO NAT GATEWAY IS INVOLVED, AND NONE EXISTS ANYWHERE. `egress/` IS now a prerequisite,
#        which is the one cost the move adds: the SSM path is an interface endpoint (5.5) rather
#        than an internet route, so a build session pays that slice's 0.130 USD/h.
#
# THE TIER IS THE PRIVATE ONE, AND THE OLD CO-TENANCY PROBLEM IS GONE WITH IT. In Sandbox this
# host sat in the ISOLATED tier for one reason: under design A the private tier's default route
# belonged to `egress/`, and two slices writing 0.0.0.0/0 into one table is a collision rather
# than a design. Nothing writes a default route now, so the reason evaporated - and the private
# tier is where it has to be anyway, because MEASURED 2026-09-06 the peering routes to
# `VPC-Networking` are in the private route tables and NOT in the isolated one. An isolated-tier
# build host could not reach the proxy at all.
#
# AND THE `sandbox/probes/` EXCLUSION DIES HERE. `./scripts/buildbox.py` refused to apply while
# the perimeter probe existed, because that probe's premise is that the Sandbox ISOLATED tier has
# no default route, and this slice used to create one there. It creates no route anywhere now,
# and it is not even in that account. The refusal is removed rather than left as a superstition -
# a guard that no longer guards anything is the thing a later reader trusts by mistake.
# ------------------------------------------------------------------------------------------

# ---------------------------------------- THE ROUTE THAT USED TO BE HERE, AND IS NOT REPLACED
#
# `aws_route.default_via_wireguard` stood here until 6c step 5.8: `0.0.0.0/0` in the Sandbox
# isolated tier, pointed at the WireGuard host's ENI, created and destroyed with the session. It
# is DELETED, not moved, and nothing takes its place - that is what "design B" means for this
# host. Reach is now three separate paths (see the header), none of them a default route, and the
# one that carries the internet is a PROXY the host is CONFIGURED to use rather than a route it
# is unaware of.
#
# WHY THAT IS AN IMPROVEMENT AND NOT JUST A CHANGE: a route is invisible to the process using it,
# so a build that reached something unexpected left no trace anyone would look at. A proxy logs
# the requested hostname of every connection (4.11), and refuses an unlisted one with a NAMED
# 403 instead of a timeout. The old note here said a stopped WireGuard host made this route a
# blackhole rather than an error; the equivalent failure now is a stopped PROXY, and it announces
# itself as a connection refused to a name that resolves.

# ------------------------------------------------- the security group: EGRESS ONLY
#
# NO ingress BLOCK. An aws_security_group with none is a group that admits nothing, which is
# exactly the posture this host wants: Session Manager needs no inbound rule, and nothing else
# connects. The header above carries why the rule that used to be here was withdrawn.
resource "aws_security_group" "buildbox" {
  name        = "awsds-${var.env}-buildbox"
  description = "Stage 6 build host - NO ingress at all (Session Manager needs none); the internet is the explicit proxy"
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

  # UNRESTRICTED ON PURPOSE, AND THE ARGUMENT CHANGED WITH THE MOVE (6c step 5.8). It used to
  # be "what bounds this host's reach is the ROUTE - a single default at a NAT instance this
  # design owns". There is no route now. What bounds it is stronger and named: this tier has NO
  # default route at all, so the only way to the internet is a proxy the host must be CONFIGURED
  # to use. What that proxy will fetch for this source is the `production-foundation` plane,
  # which since 2026-09-08 is `open` rather than an allow-list (D38 section 6 amended) - so the
  # bound is the absent route, the security group's single destination port, and the three
  # global denies, not a list of names. A port list in this group would be a second, weaker copy
  # of a control that already exists, in the file where somebody would later "fix" it.
  #
  # AND THE PARAGRAPH THAT USED TO FOLLOW IS RETIRED WITH THE DESIGN. It said that
  # `sandbox/egress/`'s DNS Firewall associated to the VPC ID rather than to a route table, so it
  # filtered this host too whenever that slice was up - and that `public.ecr.aws` and
  # `static.rust-lang.org` were CDN-fronted and therefore unreachable, so a build had to run with
  # `egress/` DOWN. Three things ended that: `vpc-egress-v0.4.0` made chain evaluation an input,
  # 6c step 5.7 cut the firewall lists to AWS's own namespaces and this estate's private zones,
  # and those package names moved to the PROXY - where matching is on the hostname the client
  # REQUESTED and no chain is evaluated at all. The build no longer has an argument with the
  # firewall, and `egress/` is now a PREREQUISITE rather than an obstacle.
  egress {
    # checkov:skip=CKV_AWS_382:deliberate - the control is the ABSENCE of a default route plus the proxy's allow-list, not this rule; see the note above
    description = "no default route in this tier - the internet is the proxy, and its allow-list is the control"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "awsds-${var.env}-buildbox"
  }
}

# ------------------------------------------------------------------------------- the role
#
# ONE MANAGED POLICY AND NOTHING ELSE, and the absence is the part worth reading.
#
# AmazonSSMManagedInstanceCore is what makes `aws ssm start-session` work; it is the whole
# reason this host needs a role at all.
#
# WHAT IS DELIBERATELY NOT HERE: any ecr: permission. This host BUILDS the images; it does
# not push them. The push is Stage 6 step 5.0's own act, from an identity that may, and Stage 8's
# pipeline after that (D26/D28: the pipeline is the deployer).
#
# AND THE MOVE TOOK HALF OF THAT CONTROL AWAY, WHICH IS WORTH SAYING RATHER THAN DISCOVERING
# (6c step 5.8, 2026-09-06). The old reasoning had two legs: this role names no `ecr:` action,
# AND `production/registry/` grants the Interactive accounts a PULL and nothing more, so a push
# from Sandbox was refused AT THE FAR END regardless of what the near end said. This host is now
# IN the registry's own account. The far-end refusal does not apply to it, so the absence below
# is no longer a belt beside a brace - IT IS THE WHOLE CONTROL, and an `ecr:` action added here
# in a hurry would simply work. The token dance in runbooks/buildbox.md SS P is unchanged and is
# now the only thing between a build host and the registry: the identity arrives as a
# short-lived ECR token vended by the operator, never as a permission on this role.
# Revision trigger: a decision that a build host may publish, which is a change to the supply
# chain rather than to this slice.
module "role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-buildbox"
  description = "Stage 6 build host - Session Manager only; it builds images and pushes none"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowEc2Service"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ]
}

resource "aws_iam_instance_profile" "buildbox" {
  name = "awsds-${var.env}-buildbox"
  role = module.role.role_name
}

# -------------------------------------------------------------------------- the host itself
resource "aws_instance" "buildbox" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same session buys nothing - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t3 is not EBS-optimized-capable at these sizes and the build's bottleneck is the network, not the volume
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the private tier, which has no default route at all under design B
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id                   = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids      = [aws_security_group.buildbox.id]
  iam_instance_profile        = aws_iam_instance_profile.buildbox.name
  associate_public_ip_address = false

  user_data = local.user_data
  # THE USER DATA IS A BUILD, and it runs at first boot only. A change to it must produce a
  # NEW host rather than an attribute nobody applied - the same reasoning the WireGuard module
  # states, and the same failure it avoids: a running host whose configuration silently
  # disagrees with the code describing it.
  user_data_replace_on_change = true

  # THE ORDERING PROBLEM DID NOT GO AWAY WITH THE ROUTE, IT MOVED ACCOUNTS. The old
  # `depends_on` existed because this host's first boot NEEDS a path before it has one: the SSM
  # agent must register or `start-session` reports the instance as not connected, and the host
  # has to be replaced to try again. The path is now `egress/`'s three SSM endpoints and the
  # proxy, and NEITHER is expressible as a `depends_on` - one is a different slice, the other a
  # different account. What records the order is the rank in scripts/tfhygiene/layers.py and
  # what enforces it is ./scripts/buildbox.py, which refuses to apply while either is down.
  # The race that made a literal `depends_on` necessary is gone with the same-slice route.

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = var.root_volume_size
    volume_type = "gp3"
    # DELETED WITH THE HOST, which is the default and is stated because this slice is [E] and
    # the whole D11 claim rests on it: a volume that outlived its instance would be a bill
    # nobody is looking for and `./scripts/buildbox.py status` would not see it.
    delete_on_termination = true
  }

  # THE NAME TAG IS A CONTRACT: ./scripts/buildbox.py finds this host by `awsds-<env>-buildbox`
  # to open a session and to report status. A rename here is a rename there.
  tags = {
    Name = "awsds-${var.env}-buildbox"
  }
}
