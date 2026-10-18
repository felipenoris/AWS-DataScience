# Stage 12 steps 1.1 and 1.3: the account dashboard. Every panel survives `make down` (step 1.3): an
# AWS/Usage metric, a [P] VPC id, a SEARCH over dimension names, the warehouse's name, which the [E]
# workgroup keeps across every rebuild, or an alarm by name. No panel names an app, a job, an
# endpoint or a workgroup id.

locals {
  sandbox_widgets = [
    {
      type   = "text"
      x      = 0
      y      = 0
      width  = 24
      height = 4
      properties = {
        markdown = <<-EOT
          ## Sandbox

          What a session runs and what it leaves behind. The interface endpoints are the largest line on the bill, and the spaces' volumes bill while every app is stopped ([cost-model.md](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/cost-model.md)). Athena bytes against a workgroup limit has no panel: the project workgroups publish no metric and set no cutoff.

          Runbooks: [dev-env.md](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/dev-env.md), [redshift-connection.md](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/redshift-connection.md). Instruments: `./aws/studio.py`, `./aws/egress.py`, `./aws/warehouse.py`, `./aws/observability.py`; `make status` for the hourly burn.
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
          [for a in aws_cloudwatch_metric_alarm.quota : a.arn],
          [for name in local.warehouse_alarms : "${local.alarm_arn_prefix}${name}"],
        )
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 7
      width  = 8
      height = 6
      properties = {
        title  = "Studio apps running, by type"
        region = var.region
        metrics = [
          [{ expression = "SEARCH('{AWS/Usage,Class,Resource,Service,Type} MetricName=\"ResourceCount\" Service=\"SageMaker\" (JupyterLab OR CodeEditor OR KernelGateway)', 'Maximum', 300)", id = "apps" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 8
      y      = 7
      width  = 8
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
      x      = 16
      y      = 7
      width  = 8
      height = 6
      properties = {
        title  = "Studio space volumes, GB"
        region = var.region
        stat   = "Maximum"
        period = 3600
        metrics = [
          ["AWS/Usage", "ResourceCount", "Class", "None", "Resource", "studio/total_volume_size_in_gb", "Service", "SageMaker", "Type", "Resource", { label = "GB across every space" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 13
      width  = 8
      height = 6
      properties = {
        title  = "Interface endpoints in the VPC, and the quota"
        region = var.region
        stat   = "Maximum"
        period = 3600
        metrics = [
          ["AWS/Usage", "ResourceCount", "Class", "None", "Resource", "InterfaceVPCEndpointsPerVPC", "Service", "EC2", "Type", "Resource", "ResourceId", local.vpc_id, { id = "endpoints", label = "endpoints" }],
          [{ expression = "SERVICE_QUOTA(endpoints)", id = "quota", label = "quota" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 8
      y      = 13
      width  = 8
      height = 6
      properties = {
        title  = "DNS Firewall queries"
        region = var.region
        stat   = "Sum"
        period = 3600
        metrics = [
          ["AWS/Route53Resolver", "VpcFirewallQueryVolume", "VpcId", local.vpc_id, { label = "queries" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 16
      y      = 13
      width  = 8
      height = 6
      properties = {
        title  = "Bedrock, every model"
        region = var.region
        stat   = "Sum"
        period = 3600
        metrics = [
          ["AWS/Bedrock", "InputTokenCount", { label = "input tokens" }],
          ["AWS/Bedrock", "OutputTokenCount", { label = "output tokens" }],
          ["AWS/Bedrock", "Invocations", { label = "invocations", yAxis = "right" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 0
      y      = 19
      width  = 12
      height = 6
      properties = {
        title  = "Warehouse compute, RPU-seconds"
        region = var.region
        stat   = "Sum"
        period = 3600
        metrics = [
          ["AWS/Redshift-Serverless", "ComputeSeconds", "Workgroup", local.warehouse, { label = "compute" }],
          ["AWS/Redshift-Serverless", "ChargedSeconds", "Workgroup", local.warehouse, { label = "charged" }],
          ["AWS/Redshift-Serverless", "ComputeCapacity", "Workgroup", local.warehouse, { label = "RPUs allocated", stat = "Maximum", yAxis = "right" }],
        ]
      }
    },
    {
      type   = "metric"
      x      = 12
      y      = 19
      width  = 12
      height = 6
      properties = {
        title  = "Warehouse storage, MB"
        region = var.region
        stat   = "Maximum"
        period = 3600
        metrics = [
          ["AWS/Redshift-Serverless", "DataStorage", "Namespace", local.warehouse, { label = "stored" }],
        ]
      }
    },
  ]
}

resource "aws_cloudwatch_dashboard" "sandbox" {
  dashboard_name = "awsds-${var.env}-environment"
  dashboard_body = jsonencode({ widgets = local.sandbox_widgets })
}
