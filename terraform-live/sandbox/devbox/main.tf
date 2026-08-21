# sandbox/devbox/ - THE BUILD HOST (Stage 6 step 5.0), layer [E].
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
#   IN   nothing reaches this host except from the WireGuard client range. It has no public
#        address, it is in a tier with no internet gateway, and its security group admits
#        var.peer_cidr and nothing else. A shell arrives over Session Manager, which needs no
#        inbound rule at all - so the ingress rule is for the direct paths (docker daemon,
#        a served port during a test) rather than for the shell.
#
#   OUT  through the WireGuard host, which is the single public egress of this design. THREE
#        THINGS IN THREE SLICES, AND ALL THREE ARE NEEDED - reach is an intersection (Lesson
#        28), and the first apply of this slice had two of them: the route below sends this
#        tier's default at that instance's ENI; sandbox/vpn/ gives the host the masquerade
#        rules that make it a NAT instance for these ranges; and sandbox/foundation/'s
#        WireGuard security group ADMITS those ranges inbound, or the packet is dropped on
#        arrival - which is what happened, and it read as a broken package mirror.
#        NO NAT GATEWAY IS INVOLVED - egress/ is not a prerequisite of this slice and does not
#        have to be up, which is 0.170 USD/h not spent to run a build.
#
# THE TIER IS THE ISOLATED ONE, AND THAT IS A CHOICE WITH A CO-TENANT. The private tier's
# default route belongs to egress/ under egress_mode=A, and two slices writing 0.0.0.0/0 into
# one route table is a collision rather than a design. The isolated tier has no default route
# by construction - which is the property that leaves room for one, AND the premise
# sandbox/probes/'s perimeter probe measures ("this subnet has no default route, so a host
# that is neither S3 nor DynamoDB must fail to connect"). While this slice is up, that premise
# is false. The two are never up together: ./scripts/devbox.py refuses to apply while the
# perimeter probe exists, because a comment is not a control (Lesson 5).
# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------ the way out, and back
#
# ONE ROUTE, AND IT IS THE ONLY THING THIS SLICE WRITES OUTSIDE ITSELF. It is created and
# destroyed with the session, so the isolated tier returns to having no default route the
# moment the build host is gone - which is what lets the perimeter probe's premise be true
# again without anyone remembering to restore anything.
#
# IT POINTS AT AN ENI, NOT AN INSTANCE ID, because that is what aws_route takes - and the ENI
# is READ from vpn/'s state rather than pasted, because the WireGuard host is [D] and
# replaceable: a shape change or a user-data change mints a new interface, and a pasted id
# would leave a route that blackholes silently instead of a plan that moves (Lesson 4).
#
# IF THE WIREGUARD HOST IS STOPPED, THIS ROUTE IS A BLACKHOLE. Not an error, not a warning -
# packets leave and nothing comes back, and every symptom looks like a broken package mirror.
# That is why the helper script starts the [D] host before it applies this slice and says so.
resource "aws_route" "default_via_wireguard" {
  route_table_id         = data.terraform_remote_state.foundation.outputs.isolated_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  network_interface_id   = data.terraform_remote_state.vpn.outputs.primary_network_interface_id
}

# ---------------------------------------------------------------------- the security group
resource "aws_security_group" "devbox" {
  name        = "awsds-${var.env}-devbox"
  description = "Stage 6 build host - ingress from the WireGuard client range only; egress through the VPN host"
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

  # THE CLIENT RANGE, AND IT IS THE ONLY INGRESS THERE IS. It is also a range that never
  # appears anywhere else inside AWS: the WireGuard host SNATs the tunnel, so no other
  # security group in this design has ever had reason to name it. Here it is named because
  # this rule is the answer to "reachable only over the VPN" - with the tunnel down there is
  # no source address that satisfies it, and with the host stopped there is no path at all.
  ingress {
    # NO APOSTROPHE, and it is not a style rule: AWS validates a rule description against
    # ^[0-9A-Za-z_ .:/()#,@\[\]+=&;{}!$*-]*$, and an apostrophe fails it at PLAN time.
    description = "the WireGuard client range - the whole of the inbound surface"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.peer_cidr]
  }

  # UNRESTRICTED ON PURPOSE, and the argument is the one sandbox/probes/ makes for its own
  # egress: what bounds this host's reach is the ROUTE - a single default at a NAT instance
  # this design owns - and a port list here would add a second, weaker copy of a control that
  # already exists, in the file where somebody would later "fix" it. The build pulls from
  # public.ecr.aws, PyPI, conda-forge, julialang and static.rust-lang.org over 443; naming
  # them would be an allow-list maintained by hand in the wrong layer (egress design A owns
  # that question, and answers it with a DNS firewall).
  egress {
    # checkov:skip=CKV_AWS_382:deliberate - the control is the route (a NAT instance this design owns), not this rule; see the note above
    description = "out through the VPN host - the route is the control, not this rule"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "awsds-${var.env}-devbox"
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
# not push them. The Production registry grants the two Interactive accounts a PULL and
# nothing more (terraform-live/production/registry/ecr.tf: "nothing outside this account
# publishes"), so a push from Sandbox is refused at the far end anyway - and adding the near
# half of a permission the far half denies would produce a role that reads as if it could
# publish. The push is Stage 6 step 5.0's own act, from an identity that may, and Stage 8's
# pipeline after that. Revision trigger: a decision that the Sandbox may publish, which is a
# change to the supply chain rather than to this slice.
module "role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-devbox"
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

resource "aws_iam_instance_profile" "devbox" {
  name = "awsds-${var.env}-devbox"
  role = module.role.role_name
}

# -------------------------------------------------------------------------- the host itself
resource "aws_instance" "devbox" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same session buys nothing - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t3 is not EBS-optimized-capable at these sizes and the build's bottleneck is the network, not the volume
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the isolated tier, which has no internet gateway behind it at all
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id                   = data.terraform_remote_state.foundation.outputs.isolated_subnet_ids[local.zone]
  vpc_security_group_ids      = [aws_security_group.devbox.id]
  iam_instance_profile        = aws_iam_instance_profile.devbox.name
  associate_public_ip_address = false

  user_data = local.user_data
  # THE USER DATA IS A BUILD, and it runs at first boot only. A change to it must produce a
  # NEW host rather than an attribute nobody applied - the same reasoning the WireGuard module
  # states, and the same failure it avoids: a running host whose configuration silently
  # disagrees with the code describing it.
  user_data_replace_on_change = true

  # THE ROUTE BEFORE THE HOST, AND IT IS NOT COSMETIC ORDERING. Neither resource references
  # the other, so Terraform would happily create them in parallel - and this host's first boot
  # NEEDS the internet: the SSM agent has to reach ssm.<region>.amazonaws.com to register, and
  # docker comes from the AL2023 repository. Without this line the race is silent and
  # intermittent: sometimes the agent registers, sometimes `start-session` says the instance
  # is not connected and the host has to be replaced to try again.
  depends_on = [aws_route.default_via_wireguard]

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
    # nobody is looking for and `./scripts/devbox.py status` would not see it.
    delete_on_termination = true
  }

  # THE NAME TAG IS A CONTRACT: ./scripts/devbox.py finds this host by `awsds-<env>-devbox`
  # to open a session and to report status. A rename here is a rename there.
  tags = {
    Name = "awsds-${var.env}-devbox"
  }
}
