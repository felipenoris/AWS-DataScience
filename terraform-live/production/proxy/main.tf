# production/proxy/ - THE ESTATE'S SINGLE INTERNET EXIT (Stage 6c step 4.8, D38).
#
# WHAT THIS REPLACES: three NAT gateways, one per account, each 0.045/h plus per-GB processing
# plus its own Elastic IP - and, more to the point, three exits nobody could enumerate. This is
# one exit, on one host, with one allow-list and one access log.
#
# WHY AN EXPLICIT PROXY AND NOT A SHARED NAT, which is the design everyone draws first: peering
# shares an ADDRESS, never a PATH (Lesson 44). A spoke cannot route its default through a peered
# VPC's gateway - AWS does not forward peered traffic to an internet gateway, a NAT gateway or a
# VPC endpoint, and it says so four times in its own guide. So the hop has to be at the
# APPLICATION layer: the client opens a TCP connection to this host and asks it, by name, to
# fetch something. That constraint is also what enforces the isolation for free - a spoke with no
# default route cannot accidentally reach anything.
#
# WHY IT IS A SECOND HOST AND NOT A SECOND SERVICE ON THE WIREGUARD ONE: that host receives
# untrusted UDP from the open internet and this one parses untrusted internet RESPONSES.
# Separating them keeps a compromise of either off the other, and the price is one t3.nano.
#
# WHAT IT IS NOT: a TLS-terminating inspector. It relays CONNECT, so it sees the host NAME and
# the byte counts and never the content. That is deliberate - an interception proxy needs a CA
# that every client trusts, which is a far larger commitment than this stage is making.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_ssm_parameter" "al2023" {
  # The same image the tunnel endpoint runs, and for the same reason: `squid` and `jq` are both
  # in the AL2023 repositories, so nothing here downloads a binary of its own. x86_64 is what
  # var.instance_type's closed list follows - the image decides the family, never the reverse.
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/networking/terraform.tfstate"
    region = var.region
  }
}

locals {
  zone = var.zone_ids[var.zone_index]

  squid_conf = templatefile("${path.module}/squid.conf.tftpl", {
    rfc1918_cidrs        = var.rfc1918_cidrs
    reconfigure_schedule = var.reconfigure_schedule
  })

  render_script = templatefile("${path.module}/render-squid.sh.tftpl", {
    parameter_name       = data.terraform_remote_state.networking.outputs.proxy_allowlist_parameter_name
    region               = var.region
    reconfigure_schedule = var.reconfigure_schedule
  })

  agent_config = jsonencode({
    agent = { run_as_user = "root" }
    logs = {
      logs_collected = {
        files = {
          collect_list = [
            {
              file_path       = "/var/log/squid/access.log"
              log_group_name  = data.terraform_remote_state.networking.outputs.proxy_access_log_group_name
              log_stream_name = "{instance_id}/access"
              timezone        = "UTC"
            }
          ]
        }
      }
    }
  })

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    squid_conf    = local.squid_conf
    render_script = local.render_script
    agent_config  = local.agent_config
  })
}

# ------------------------------------------------------------------------------- the role
#
# THREE PERMISSIONS AND NOT ONE MORE. Session Manager (the shell - there is no port 22 here
# either), ONE SSM parameter by name, and ONE log group with no delete.
#
# THE BOUNDARY IS null AND IT IS A DECISION, not an omission - the iam-role module makes it
# unforgettable by requiring the argument. This is an EC2 service role authored by the identity
# that authors boundaries (Lesson 18).
module "role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-proxy"
  description = "Squid proxy host - Session Manager, its allow-list parameter, and its access log (Stage 6c step 4.8)"

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

  # AmazonSSMManagedInstanceCore is Session Manager AND State Manager: the association of step
  # 4.10 reaches this host over the agent's OUTBOUND channel, so a scheduled re-render needs no
  # inbound rule and no write API from anybody's laptop.
  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ]

  inline_policies = {
    # ONE PARAMETER, BY NAME. `ssm:GetParameter` on a PREFIX would let this host read every
    # parameter the account will ever hold - and the managed policy above already carries a
    # prefix grant for the agent's own parameters, which is exactly why this one is narrow.
    "read-allowlist" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "ReadTheAllowList"
          Effect   = "Allow"
          Action   = "ssm:GetParameter"
          Resource = "arn:${data.aws_partition.current.partition}:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter${data.terraform_remote_state.networking.outputs.proxy_allowlist_parameter_name}"
        }
      ]
    })

    # THE ACCESS LOG, WRITE-ONLY AND SCOPED TO ONE GROUP (step 4.11, Lesson 18: the author of
    # the allow-list must not own its record). No logs:CreateLogGroup - networking/ owns that
    # group because networking/ owns its retention and its key, and an agent allowed to create
    # it would recreate it WITHOUT either after a manual delete. No delete of any kind: this
    # principal appends to the record of its own behaviour and can never edit it.
    "ship-access-log" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "AppendToTheAccessLog"
          Effect = "Allow"
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogStreams",
          ]
          Resource = "${data.terraform_remote_state.networking.outputs.proxy_access_log_group_arn}:*"
        }
      ]
    })
  }
}

resource "aws_iam_instance_profile" "this" {
  name = "awsds-${var.env}-proxy"
  role = module.role.role_name
}

# ------------------------------------------------------------------------------- the host
resource "aws_instance" "this" {
  # checkov:skip=CKV_AWS_126:detailed monitoring is 5x the metric volume for a one-host proxy whose alarm is on the free basic status checks - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_135:t3.nano is not EBS-optimized-capable; the shape is the measured baseline of docs/PRICING.md 3
  # checkov:skip=CKV_AWS_88:A PUBLIC ADDRESS IS WHAT THIS HOST IS FOR - it is the estate's internet exit, and the [P] Elastic IP below is the address every VPN-only condition re-keys onto at 4.12. What bounds it is the security group: TCP/3128 from the peered spokes and the tunnel, and nothing else
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id              = data.terraform_remote_state.networking.outputs.public_subnet_ids[local.zone]
  vpc_security_group_ids = [data.terraform_remote_state.networking.outputs.proxy_security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.this.name

  # No auto-assigned address: the [P] Elastic IP below is THE address, and a second one would be
  # a second thing to reason about in every condition that names it.
  associate_public_ip_address = false

  user_data = local.user_data
  # THE USER DATA CARRIES THE WHOLE SQUID CONFIGURATION, so a change to it must produce a NEW
  # HOST: user data runs at first boot only, and the provider's default edits the attribute in
  # place, which would leave a proxy whose running configuration silently disagrees with the code
  # that describes it. WHAT THIS DOES NOT COVER, and it is the point of step 4.10: the ALLOW-LISTS
  # are not in here. They live in SSM and reach the running host through the association below,
  # so editing one is an apply of networking/ and never a replacement of this instance.
  user_data_replace_on_change = true

  # SOURCE/DESTINATION CHECKING STAYS ON, and the contrast with the WireGuard host next door is
  # worth one line: that host FORWARDS for somebody else, so both legs carry foreign addresses.
  # This one TERMINATES the client's connection and opens its own - every packet it sends wears
  # its own address, which is the whole difference between a proxy and a router.

  metadata_options {
    http_endpoint = "enabled"
    # IMDSv2 REQUIRED. This host is internet-facing, holds a role credential, and - uniquely in
    # this estate - FETCHES URLS ON BEHALF OF OTHERS. That last part is why the metadata service
    # is also denied as a DESTINATION in squid.conf's `to_private` line: a client must not be
    # able to ask the proxy to fetch 169.254.169.254 and hand back this role's credentials.
    # Two independent guards on one hole, deliberately (Lesson 20's good direction).
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = 8
    volume_type = "gp3"
  }

  # THE NAME TAG IS A CONTRACT: scripts/slices.py stops and starts this host by
  # `awsds-<env>-proxy`, the State Manager association below TARGETS it by this tag, and
  # ./aws/proxy.py measures it by the same string.
  tags = {
    Name = "awsds-${var.env}-proxy"
  }

  # The same read-back trap the WireGuard host hit on its first apply (2026-08-17): with the [P]
  # address associated below, the refresh reports this attribute from the instance's CURRENT
  # public address and the next plan wants to replace the instance on
  # `associate_public_ip_address = true -> false # forces replacement`. The argument stays as
  # false because it is load-bearing at LAUNCH; only the read-back is ignored.
  lifecycle {
    ignore_changes = [associate_public_ip_address]
  }
}

resource "aws_eip_association" "this" {
  instance_id   = aws_instance.this.id
  allocation_id = data.terraform_remote_state.networking.outputs.proxy_eip_allocation_id
}

# ------------------------------------------------------- the reload path (step 4.10)
#
# THE ALLOW-LISTS ARE [P] DATA AND THIS IS HOW THEY REACH A RUNNING HOST. Without it, editing one
# domain would mean replacing the instance - a 30-second outage of the whole estate's internet -
# or a person with a write API and a shell, which is the thing this design does not want to need.
#
# AWS-RunShellScript RATHER THAN A DOCUMENT OF OUR OWN: the command is one absolute path, the
# script it runs is version-controlled in the user data, and an SSM document would be a second
# place for the same instruction to live (Lesson 14). The association reaches the host over the
# agent's OUTBOUND channel, so no security-group rule and no inbound path exists for it.
#
# WHAT MAKES ITS SILENCE READABLE - and an association that runs every half hour forever is
# otherwise the definition of an unread signal: the script exits 0 without touching anything when
# the rendered file is byte-identical, non-zero when the list does not parse, and ./aws/proxy.py
# (step 7.3) diffs what is RUNNING against what is committed. The association reports its own
# failures; the instrument is what catches a success that changed nothing it should have.
resource "aws_ssm_association" "reconfigure" {
  name             = "AWS-RunShellScript"
  association_name = "awsds-${var.env}-proxy-reconfigure"

  targets {
    key    = "tag:Name"
    values = [aws_instance.this.tags["Name"]]
  }

  parameters = {
    commands = "/usr/local/sbin/awsds-render-squid"
  }

  schedule_expression = var.reconfigure_schedule

  # Run it on the instance the moment the association is created, rather than waiting up to a
  # full interval: the first boot already rendered the list, so this is a no-op by design - and a
  # no-op that FAILS is the reading that says the association itself is misconfigured, which is
  # worth learning at apply time rather than half an hour later.
  apply_only_at_cron_interval = false
}

# ------------------------------------------------------------------------------ the alarm
#
# THE ONLY EXIT THE ESTATE HAS MUST NOT FAIL SILENTLY, and step 4.8 did not name an alarm - this
# is added rather than assumed, on the WireGuard host's precedent and for a stronger reason: when
# the tunnel dies one person notices immediately, and when this host dies every automated thing
# in four accounts loses the internet at once with no single obvious symptom.
#
# ON THE STATUS CHECKS AND NOT ON TRAFFIC, the same judgement the tunnel's alarm records: an
# alarm on "no requests for N minutes" is red every night and every weekend, and an alarm that is
# red when nothing is wrong teaches its reader to ignore it.
resource "aws_cloudwatch_metric_alarm" "health" {
  alarm_name          = "awsds-${var.env}-proxy-status-check"
  alarm_description   = "The estate's single internet exit is failing its EC2 status checks (Stage 6c step 4.8)."
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  # A stopped host produces NO datapoints, and `missing` must not read as healthy - `breaching`
  # is what makes "somebody stopped the proxy and forgot" visible. It is also why this alarm has
  # no action wired: D12 left the budget notifying nobody, and an alarm with no destination is
  # honest about that rather than pretending.
  treat_missing_data = "breaching"

  dimensions = {
    InstanceId = aws_instance.this.id
  }
}
