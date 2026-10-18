# Stage 12 steps 1.2 and 1.3: the hub dashboard, which also carries Production's own panels (step
# 1.1) - one dashboard where the stage drew two, since CloudWatch's free tier holds three, counted
# once per bill (docs/PRICING.md 6), and Sandbox takes the second.
#
# Every panel survives `make down` and `make hub-down` (step 1.3): a [P] log group or metric, a [P]
# VPC id, a SEARCH over dimension names, or one of the [D] hosts' alarms by name. No panel names an
# instance, a volume or an endpoint id.

locals {
  # The proxy's request line split into its eight fields, and the destination read off the target:
  # `host:443` for a CONNECT, `http://host/path` for a plain request.
  proxy_fields = chomp(<<-EOT
    | parse @message "* * * * * * * *" as ts, client, method, target, status, reply_size, request_size, result
    | parse target /^(?:[a-z]+:\/\/)?(?<destination>[^\/:]+)/
  EOT
  )

  hub_widgets = [
    {
      type   = "text"
      x      = 0
      y      = 0
      width  = 24
      height = 4
      properties = {
        markdown = <<-EOT
          ## The hub and Production

          The WireGuard host and the Squid proxy are the two `[D]` hosts every other account's session depends on (D38). A **stopped** host shows a gap in its status-check graph; a **failing** one shows 1. The proxy's alarm reads `ALARM` whenever the proxy is stopped, by design (`treat_missing_data = breaching`); the tunnel's and GitLab's read `OK` while stopped. A full disk has no panel: no host publishes a disk metric.

          Runbooks: [vpn.md](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/vpn.md) (section C5a for the planes and their lists), [gitlab.md](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/gitlab.md). Instruments: `./aws/proxy.py`, `./aws/vpn.py`, `./aws/dns-allowlist.py`, `./aws/observability.py`.
        EOT
      }
    },
    {
      type   = "alarm"
      x      = 0
      y      = 4
      width  = 24
      height = 3
      properties = {
        title  = "Alarms"
        sortBy = "stateUpdatedTimestamp"
        alarms = concat(
          [for name in values(local.host_alarms) : "${local.alarm_arn_prefix}${name}"],
          [
            aws_cloudwatch_metric_alarm.proxy_refusals.arn,
            aws_cloudwatch_metric_alarm.vpcs_per_region.arn,
          ],
        )
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 7
      width  = 8
      height = 5
      properties = {
        title       = "WireGuard host status checks"
        region      = var.region
        annotations = { alarms = ["${local.alarm_arn_prefix}${local.host_alarms.vpn}"] }
      }
    },
    {
      type   = "metric"
      x      = 8
      y      = 7
      width  = 8
      height = 5
      properties = {
        title       = "Proxy status checks"
        region      = var.region
        annotations = { alarms = ["${local.alarm_arn_prefix}${local.host_alarms.proxy}"] }
      }
    },
    {
      type   = "metric"
      x      = 16
      y      = 7
      width  = 8
      height = 5
      properties = {
        title       = "GitLab status checks"
        region      = var.region
        annotations = { alarms = ["${local.alarm_arn_prefix}${local.host_alarms.gitlab}"] }
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 12
      width  = 12
      height = 6
      properties = {
        title  = "Proxy requests and refusals"
        region = var.region
        stat   = "Sum"
        period = 300
        metrics = [
          [local.proxy_metric_namespace, "Requests", { id = "requests", label = "requests" }],
          [local.proxy_metric_namespace, "Refused", { id = "refused", label = "refused (403)" }],
          [{ expression = "100 * refused / requests", id = "rate", label = "refused, % of requests", yAxis = "right" }],
        ]
        yAxis = { right = { min = 0, max = 100 } }
      }
    },
    {
      type   = "log"
      x      = 12
      y      = 12
      width  = 12
      height = 6
      properties = {
        title  = "Proxy destinations - requests, refusals and bytes each way"
        region = var.region
        view   = "table"
        query  = <<-EOT
          SOURCE '${local.proxy_log_group}'
          ${local.proxy_fields}
          | stats count(*) as requests, sum(status = 403) as refused, sum(request_size) as bytes_from_client, sum(reply_size) as bytes_to_client by destination
          | sort requests desc
          | limit 20
        EOT
      }
    },
    {
      type   = "log"
      x      = 0
      y      = 18
      width  = 12
      height = 6
      properties = {
        title  = "Proxy refusals by destination and client"
        region = var.region
        view   = "table"
        query  = <<-EOT
          SOURCE '${local.proxy_log_group}'
          ${local.proxy_fields}
          | filter status = 403
          | stats count(*) as refused by destination, client
          | sort refused desc
          | limit 20
        EOT
      }
    },
    {
      type   = "log"
      x      = 12
      y      = 18
      width  = 12
      height = 6
      properties = {
        title  = "WireGuard latest handshake per peer"
        region = var.region
        view   = "table"
        query  = <<-EOT
          SOURCE '${local.vpn_log_group}'
          | parse @message /peer=(?<peer>\S+) (?<handshake>handshake\S*)/
          | filter ispresent(peer)
          | stats latest(handshake) as latest, latest(@timestamp) as read_at by peer
          | sort peer
        EOT
      }
    },
    {
      type   = "text"
      x      = 0
      y      = 24
      width  = 24
      height = 2
      properties = {
        markdown = "### Production: endpoints, VPC-Workloads' resolver, SageMaker jobs, the VPC quota\nPeering bytes have no metric; they are a flow-log query (Stage 12 step 1.2)."
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 26
      width  = 6
      height = 6
      properties = {
        title  = "Interface endpoints per VPC"
        region = var.region
        stat   = "Maximum"
        period = 3600
        metrics = [
          ["AWS/Usage", "ResourceCount", "Class", "None", "Resource", "InterfaceVPCEndpointsPerVPC", "Service", "EC2", "Type", "Resource", "ResourceId", local.shared_vpc_id, { label = "VPC-SharedServices" }],
          ["AWS/Usage", "ResourceCount", "Class", "None", "Resource", "InterfaceVPCEndpointsPerVPC", "Service", "EC2", "Type", "Resource", "ResourceId", local.workloads_vpc_id, { label = "VPC-Workloads" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 6
      y      = 26
      width  = 6
      height = 6
      properties = {
        title  = "DNS Firewall queries, VPC-Workloads"
        region = var.region
        stat   = "Sum"
        period = 3600
        metrics = [
          ["AWS/Route53Resolver", "VpcFirewallQueryVolume", "VpcId", local.workloads_vpc_id, { label = "queries" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 12
      y      = 26
      width  = 6
      height = 6
      properties = {
        title  = "SageMaker jobs and endpoints running, by type"
        region = var.region
        metrics = [
          [{ expression = "SEARCH('{AWS/Usage,Class,Resource,Service,Type} MetricName=\"ResourceCount\" Service=\"SageMaker\" (job OR endpoint)', 'Maximum', 300)", id = "jobs" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 18
      y      = 26
      width  = 6
      height = 6
      properties = {
        title       = "VPCs per Region, % of the quota"
        region      = var.region
        annotations = { alarms = [aws_cloudwatch_metric_alarm.vpcs_per_region.arn] }
      }
    },
  ]
}

resource "aws_cloudwatch_dashboard" "hub" {
  dashboard_name = "awsds-${var.env}-hub"
  dashboard_body = jsonencode({ widgets = local.hub_widgets })
}
