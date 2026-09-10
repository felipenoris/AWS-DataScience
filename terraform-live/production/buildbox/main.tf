# production/buildbox/ - the build host (Stage 6 step 5.0), layer [E].
#
# The host lives here rather than in `sandbox/buildbox/` since 6c step 5.8 (2026-09-06). Its only
# egress was a default route at the WireGuard host's ENI in the Sandbox isolated tier; D38 removed
# every default route in the estate and moved the WireGuard host to `VPC-Networking`, and a route
# target cannot live in another VPC. The move is a destroy-and-create (Recipe E), not a state
# migration: the host is [E], its volume dies with the session, and it holds nothing that survives
# one.
#
# It exists because the images this project runs on are linux/amd64 - SageMaker instance types are
# x86 and the sagemaker-distribution base publishes no arm64 tag - and the laptop this repository
# is driven from is arm64 and has no docker. The build runs on a machine of the right architecture,
# inside the perimeter, that exists only while a build is running.
#
# It is not a workstation. It holds no data, it is destroyed at the end of the session, and its
# state carries no secret. Anything worth keeping leaves it as an image in ECR.
#
# ------------------------------------------------------------------------------------------
# The network shape
#
#   IN   Nothing. There is no ingress rule at all (decided by the user 2026-08-21). This host has
#        no public address and sits in a tier with no internet gateway; the only way to a shell is
#        Session Manager, which needs no inbound rule because the agent holds the channel open
#        outbound.
#
#        The rule that stood here admitted the WireGuard client range on every port, to deliver
#        "reachable only with the tunnel up". It did not gate the shell - `ssm start-session` goes
#        laptop -> the SSM API -> the agent's outbound channel, which this group never sees - and
#        AL2023 runs sshd, so it left port 22 reachable from the tunnel on a host with zero
#        authorized keys, one `key_name` away from a second way in (Lesson 5).
#
#        "Reachable only over the VPN" is therefore not delivered for this host. The access path is
#        IAM, and for InfrastructureAccess it does not require the tunnel (open question 17, the
#        user's option (a)). A port served during a build is reached with SSM port forwarding -
#        AWS-StartPortForwardingSession - which is still Session Manager and still needs no ingress
#        rule.
#
#   OUT  As a client of the proxy. There is no default route in this tier and none is created here.
#        Three paths leave this host, and reading them apart is what makes a failure diagnosable:
#
#          the internet         -> `http_proxy` at `proxy.awsds.internal:3128`, over the
#                                  SharedServices <-> Networking peering. The
#                                  `production-foundation` plane is `open` since 2026-09-08
#                                  (D38 section 6 amended): any public name, every request logged
#                                  by requested hostname (4.11). A build host's control is the
#                                  reviewed Dockerfile, not a list of hostnames.
#          AWS APIs             -> this VPC's interface endpoints, which is why `no_proxy` is
#                                  generated rather than written (5.6). Session Manager is one of
#                                  these, and it must not be proxied.
#          S3 and DynamoDB      -> the [P] gateway endpoints, by route. Free, and the reason an ECR
#                                  pull is cheap: the manifest comes over `ecr.dkr` and the layers
#                                  come from S3 through that gateway.
#
#        No NAT gateway is involved, and none exists anywhere. `egress/` is a prerequisite: the SSM
#        path is an interface endpoint (5.5) rather than an internet route, so a build session pays
#        that slice's 0.130 USD/h.
#
# The subnet is the private tier. Measured 2026-09-06: the peering routes to `VPC-Networking` are
# in the private route tables and not in the isolated one, so an isolated-tier build host could not
# reach the proxy at all.
#
# `./scripts/buildbox.py` no longer refuses to apply while `sandbox/probes/` exists. That refusal
# guarded the Sandbox isolated tier's no-default-route premise; this slice creates no route
# anywhere and is not in that account.
# ------------------------------------------------------------------------------------------

# ------------------------------------------------- the security group: egress only
#
# No `ingress` block. An aws_security_group with none admits nothing: Session Manager needs no
# inbound rule, and nothing else connects.
resource "aws_security_group" "buildbox" {
  name        = "awsds-${var.env}-buildbox"
  description = "Stage 6 build host - NO ingress at all (Session Manager needs none); the internet is the explicit proxy"
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

  # Unrestricted on purpose. This tier has no default route, so the only way to the internet is a
  # proxy the host must be configured to use, and what that proxy will fetch for this source is the
  # `production-foundation` plane - `open` since 2026-09-08 (D38 section 6 amended). The bound is
  # the absent route, the proxy's 3128-only security group and the three global denies, not a list
  # of names. A port list here would be a second, weaker copy of a control that already exists.
  egress {
    # checkov:skip=CKV_AWS_382:the control is the absent default route plus the proxy, not this rule
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
# AmazonSSMManagedInstanceCore is what makes `aws ssm start-session` work, and it is the whole
# reason this host needs a role.
#
# No `ecr:` permission is granted. This host builds the images; it does not push them. The push is
# Stage 6 step 5.0's own act, from an identity that may, and Stage 8's pipeline after that (D26/D28:
# the pipeline is the deployer).
#
# Since the move (6c step 5.8, 2026-09-06) this host is in the registry's own account, so
# `production/registry/`'s pull-only grant to the Interactive accounts no longer refuses a push at
# the far end. The absence below is now the whole control, and an `ecr:` action added here would
# simply work. The token dance in runbooks/buildbox.md §P is what stands between a build host and
# the registry: the identity arrives as a short-lived ECR token vended by the operator, never as a
# permission on this role. Revisit only on a decision that a build host may publish, which is a
# change to the supply chain rather than to this slice.
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
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the private tier, which has no default route
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id                   = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids      = [aws_security_group.buildbox.id]
  iam_instance_profile        = aws_iam_instance_profile.buildbox.name
  associate_public_ip_address = false

  user_data = local.user_data
  # The user data is a build and runs at first boot only, so a change to it must produce a new host
  # rather than an attribute nobody applied.
  user_data_replace_on_change = true

  # No `depends_on` expresses this host's first-boot prerequisite. The SSM agent must register or
  # `start-session` reports the instance as not connected and the host has to be replaced to try
  # again; the path it registers over is `egress/`'s three SSM endpoints and the proxy - one a
  # different slice, the other a different account. The order is recorded by the rank in
  # scripts/tfhygiene/layers.py and enforced by ./scripts/buildbox.py, which refuses to apply while
  # either is down.

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = var.root_volume_size
    volume_type = "gp3"
    # The default, stated because this slice is [E] and the D11 claim rests on it: a volume that
    # outlived its instance would be a bill `./scripts/buildbox.py status` does not see.
    delete_on_termination = true
  }

  # The Name tag is a contract: ./scripts/buildbox.py finds this host by `awsds-<env>-buildbox` to
  # open a session and to report status. A rename here is a rename there.
  tags = {
    Name = "awsds-${var.env}-buildbox"
  }
}
