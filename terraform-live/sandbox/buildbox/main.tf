# sandbox/buildbox/ - THE BUILD HOST (Stage 6 step 5.0), layer [E].
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
#        laptop -> the PUBLIC SSM API -> the agent's outbound channel, and this group never
#        sees it, so the claim was false for the one path anybody actually uses. And it was a
#        grant with no consumer: AL2023 runs sshd, so the rule left port 22 REACHABLE from the
#        tunnel on a host with zero authorized keys - one `key_name` away from a second way in
#        that nothing in this design asked for. A rule nobody uses is not neutral; it is the
#        shape a later convenience grows out of (Lesson 5).
#
#        SO THE REQUIREMENT WAS WITHDRAWN RATHER THAN FAKED. "Reachable only over the VPN" is
#        not delivered for this host, and saying so is the point - the access path is IAM, and
#        for InfrastructureAccess it does not require the tunnel (open question 17, the user's
#        option (a): the administrative credential is also the fire escape). If a port served
#        during a build ever has to be reached from the laptop, the answer is SSM PORT
#        FORWARDING - AWS-StartPortForwardingSession - which is still Session Manager and
#        still needs no ingress rule.
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
# is false. The two are never up together: ./scripts/buildbox.py refuses to apply while the
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

# ------------------------------------------------- the security group: EGRESS ONLY
#
# NO ingress BLOCK. An aws_security_group with none is a group that admits nothing, which is
# exactly the posture this host wants: Session Manager needs no inbound rule, and nothing else
# connects. The header above carries why the rule that used to be here was withdrawn.
resource "aws_security_group" "buildbox" {
  name        = "awsds-${var.env}-buildbox"
  description = "Stage 6 build host - NO ingress at all (Session Manager needs none); egress through the VPN host"
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

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
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the isolated tier, which has no internet gateway behind it at all
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id                   = data.terraform_remote_state.foundation.outputs.isolated_subnet_ids[local.zone]
  vpc_security_group_ids      = [aws_security_group.buildbox.id]
  iam_instance_profile        = aws_iam_instance_profile.buildbox.name
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
    # nobody is looking for and `./scripts/buildbox.py status` would not see it.
    delete_on_termination = true
  }

  # THE NAME TAG IS A CONTRACT: ./scripts/buildbox.py finds this host by `awsds-<env>-buildbox`
  # to open a session and to report status. A rename here is a rename there.
  tags = {
    Name = "awsds-${var.env}-buildbox"
  }
}
