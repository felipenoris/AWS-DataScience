# production/proxy/ - the estate's single internet exit (Stage 6c step 4.8, D38).
#
# It replaces three NAT gateways, one per account, each 0.045/h plus per-GB processing plus its own
# Elastic IP, and three exits nobody could enumerate. This is one exit, on one host, with one
# allow-list and one access log.
#
# An explicit proxy rather than a shared NAT, because peering shares an address, never a path
# (Lesson 44): a spoke cannot route its default through a peered VPC's gateway, since AWS does not
# forward peered traffic to an internet gateway, a NAT gateway or a VPC endpoint. The hop is
# therefore at the application layer - the client opens a TCP connection to this host and asks it,
# by name, to fetch something - and a spoke with no default route reaches nothing by accident.
#
# A second host rather than a second service on the WireGuard one: that host receives untrusted UDP
# from the open internet and this one parses untrusted internet responses. Separating them keeps a
# compromise of either off the other, for one more t3.nano.
#
# It is not a TLS-terminating inspector. It relays CONNECT, so it sees the host name and the byte
# counts and never the content; an interception proxy would need a CA that every client trusts,
# a far larger commitment than this stage is making.

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
# Three permissions and no more: Session Manager (the shell - there is no port 22 here either),
# one SSM parameter by name, and one log group with no delete.
#
# permissions_boundary is null by decision, not by omission; the iam-role module makes it
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

  # AmazonSSMManagedInstanceCore covers Session Manager and State Manager: step 4.10's association
  # reaches this host over the agent's outbound channel, so a scheduled re-render needs no inbound
  # rule and no write API from anybody's laptop.
  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ]

  inline_policies = {
    # One parameter, by name. `ssm:GetParameter` on a prefix would let this host read every
    # parameter the account will ever hold, and the managed policy above already carries a prefix
    # grant for the agent's own parameters.
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

    # The access log, write-only and scoped to one group (step 4.11, Lesson 18: the author of the
    # allow-list must not own its record). No logs:CreateLogGroup - networking/ owns that group,
    # its retention and its key, and an agent allowed to create it would recreate it without either
    # after a manual delete. No delete of any kind: this principal appends to the record of its own
    # behaviour and can never edit it.
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
  # checkov:skip=CKV_AWS_88:a public address is what this host is for - it is the estate's internet exit, and the [P] Elastic IP below is the address every VPN-only condition re-keys onto at 4.12. What bounds it is the security group: TCP/3128 from the peered spokes and the tunnel, and nothing else
  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.instance_type

  subnet_id              = data.terraform_remote_state.networking.outputs.public_subnet_ids[local.zone]
  vpc_security_group_ids = [data.terraform_remote_state.networking.outputs.proxy_security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.this.name

  # No auto-assigned address: the [P] Elastic IP below is the address, and a second one would be a
  # second thing to reason about in every condition that names it.
  associate_public_ip_address = false

  user_data = local.user_data
  # The user data carries the whole Squid configuration, so a change to it must produce a new host:
  # user data runs at first boot only, and the provider's default edits the attribute in place,
  # leaving a proxy whose running configuration disagrees with the code that describes it. The
  # allow-lists are not in here (step 4.10): they live in SSM and reach the running host through
  # the association below, so editing one is an apply of networking/ and not a replacement of this
  # instance.
  user_data_replace_on_change = true

  # Source/destination checking stays on. The WireGuard host next door forwards for somebody else,
  # so both its legs carry foreign addresses; this one terminates the client's connection and opens
  # its own, and every packet it sends wears its own address.

  metadata_options {
    http_endpoint = "enabled"
    # IMDSv2 required. This host is internet-facing, holds a role credential, and fetches URLs on
    # behalf of others, which is why the metadata service is also denied as a destination in
    # squid.conf's `to_private` line: a client must not be able to ask the proxy to fetch
    # 169.254.169.254 and hand back this role's credentials. Two independent guards on one hole.
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    volume_size = 8
    volume_type = "gp3"
  }

  # The Name tag is a contract: scripts/slices.py stops and starts this host by
  # `awsds-<env>-proxy`, the State Manager association below targets it by this tag, and
  # ./aws/proxy.py measures it by the same string.
  tags = {
    Name = "awsds-${var.env}-proxy"
  }

  # The same read-back trap the WireGuard host hit on its first apply (2026-08-17): with the [P]
  # address associated below, the refresh reports this attribute from the instance's current public
  # address and the next plan wants to replace the instance on
  # `associate_public_ip_address = true -> false # forces replacement`. The argument stays false
  # because it is load-bearing at launch; only the read-back is ignored.
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
# The allow-lists are [P] data, and this is how they reach a running host. Without it, editing one
# domain would mean replacing the instance - a 30-second outage of the whole estate's internet - or
# a person with a write API and a shell.
#
# AWS-RunShellScript rather than a document of our own: the command is one absolute path, the
# script it runs is version-controlled in the user data, and an SSM document would be a second
# place for the same instruction to live (Lesson 14). The association reaches the host over the
# agent's outbound channel, so it needs no security-group rule and no inbound path.
#
# What makes its silence readable, since it runs every half hour forever: the script exits 0
# without touching anything when the rendered file is byte-identical, non-zero when the list does
# not parse, and ./aws/proxy.py (step 7.3) diffs what is running against what is committed. The
# association reports its own failures; the instrument catches a success that changed nothing it
# should have.
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

  # Do not run at creation (measured 2026-09-06). The association is created seconds after
  # `RunInstances`, and the user data spends its first ~50 seconds in `dnf install`, so an
  # immediate run lands on a host that has not written `/usr/local/sbin/awsds-render-squid` yet and
  # dies with **exit 127, no such file**. That is guaranteed on a fresh host rather than
  # diagnostic, and it leaves a `Failed` association in the console as a working proxy's permanent
  # first impression.
  #
  # The first render belongs to the user data, which owns the boot; this association owns the
  # ongoing reconciliation, and its first scheduled run is then a real test rather than a race.
  apply_only_at_cron_interval = true
}

# ------------------------------------------------------------------------------ the alarm
#
# The estate's only exit must not fail silently. When the tunnel dies one person notices
# immediately; when this host dies every automated thing in four accounts loses the internet at
# once, with no single obvious symptom.
#
# On the status checks and not on traffic, the same judgement the tunnel's alarm records: an alarm
# on "no requests for N minutes" is red every night and every weekend, and an alarm that is red
# when nothing is wrong teaches its reader to ignore it.
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
  # A stopped host produces no datapoints, and `missing` must not read as healthy: `breaching` is
  # what makes "somebody stopped the proxy and forgot" visible. This alarm has no action wired,
  # since D12 left the budget notifying nobody.
  treat_missing_data = "breaching"

  dimensions = {
    InstanceId = aws_instance.this.id
  }
}

# ------------------------------------------------- the name (6c step 2.1, written here at 4.8)
#
# `proxy.awsds.internal` is the name the whole design is configured against. Every client in every
# spoke is told `http_proxy=http://proxy.awsds.internal:3128`, NO_PROXY carries `.awsds.internal`
# so that name is never sent to the proxy itself, and step 6.1's closing check is `curl -x
# proxy.awsds.internal:3128 https://checkip.amazonaws.com`.
#
# It is here and not in networking/ because the zone is [P] and belongs to production/foundation/,
# while the address is a property of an instance this [D] slice may replace on a configuration
# change, and a [P] slice must not take a dependency on a [D] value (Lesson 4). `make down` stops
# this host rather than destroying it, so the ENI and its private address survive a down/up cycle
# and the record does not churn.
#
# The record carries the private address, not the Elastic IP: a spoke reaches 3128 over a peering,
# and a peering carries the private address only. Pointing this name at the Elastic IP would send
# every spoke's proxy traffic at a public address it has no route to - a timeout with no message,
# from a name that resolves perfectly.
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

resource "aws_route53_record" "proxy" {
  zone_id = data.terraform_remote_state.foundation.outputs.awsds_internal_zone_id
  name    = "proxy.awsds.internal"
  type    = "A"
  ttl     = 60
  records = [aws_instance.this.private_ip]
}
