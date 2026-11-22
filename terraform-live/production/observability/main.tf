# Stage 12 steps 1.2, 2.2 and 9.2 in Production: the proxy access log turned into two metrics, the
# alarm on the refusals, and the alarm on the one quota here that a usage metric measures and this
# account has approached. Every alarm notifies awsds-prod-alerts (Stage 8 decision 5), whose policy
# admits CloudWatch since production/foundation/'s statement for it.

# -------------------------------------------------------------- the proxy log's metrics (step 1.2)
#
# One line per request, `logformat awsds` in production/proxy/squid.conf.tftpl: time, client, method,
# target, HTTP status, reply size (%<st), request size (%>st), Squid's result. No default value: a
# filter without one publishes nothing while the proxy is stopped, and a custom metric bills only for
# the hours it receives data (docs/PRICING.md 6).

resource "aws_cloudwatch_log_metric_filter" "proxy_requests" {
  name           = "awsds-${var.env}-proxy-requests"
  log_group_name = local.proxy_log_group
  pattern        = "[time, client, method, target, status, reply_size, request_size, result]"

  metric_transformation {
    name      = "Requests"
    namespace = local.proxy_metric_namespace
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "proxy_refusals" {
  name           = "awsds-${var.env}-proxy-refusals"
  log_group_name = local.proxy_log_group
  pattern        = "[time, client, method, target, status = 403, reply_size, request_size, result]"

  metric_transformation {
    name      = "Refused"
    namespace = local.proxy_metric_namespace
    value     = "1"
    unit      = "Count"
  }
}

# -------------------------------------------------------------------- the refusal alarm (step 2.2)
#
# A design signal rather than a fault: a run of refusals means a plane's allow-list is behind the
# work. Missing data is not breaching, since a stopped proxy writes nothing.
resource "aws_cloudwatch_metric_alarm" "proxy_refusals" {
  alarm_name          = "awsds-${var.env}-proxy-refusals"
  alarm_description   = "The proxy refused ${var.refusal_threshold} or more requests in one hour (Stage 12 step 2.2): a plane's allow-list is behind the work. The refused names are on the awsds-${var.env}-hub dashboard; the planes and their lists are docs/plan/runbooks/vpn.md section C5a, read with ./aws/dns-allowlist.py and ./aws/proxy.py."
  namespace           = local.proxy_metric_namespace
  metric_name         = aws_cloudwatch_log_metric_filter.proxy_refusals.metric_transformation[0].name
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = var.refusal_threshold
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [local.alerts_topic_arn]
}

# ----------------------------------------------------------------------- the quota alarm (step 9.2)
#
# Read 2026-10-18: of step 9.1's quotas, VPCs per Region is the one with a usage metric that this
# account has approached, 3 of 5 every hour since 6c. The Elastic IP and gateway-endpoint quotas
# publish no usage metric, and the interface endpoints per VPC peak at 12 of 50. The alarm's metric
# is the quota's own usage metric, read back from Service Quotas with the quota's name (Lesson 38),
# and SERVICE_QUOTA() follows an increase without an apply.
data "aws_servicequotas_service_quota" "vpcs_per_region" {
  service_code = "vpc"
  quota_code   = "L-F678F1CE"

  lifecycle {
    postcondition {
      condition     = strcontains(lower(self.quota_name), "vpcs per region") && length(self.usage_metric) == 1
      error_message = "L-F678F1CE no longer answers as VPCs per Region with a usage metric: read the quota in Service Quotas before trusting this alarm (Lesson 38)."
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "vpcs_per_region" {
  alarm_name          = "awsds-${var.env}-quota-vpcs-per-region"
  alarm_description   = "VPCs per Region (${data.aws_servicequotas_service_quota.vpcs_per_region.quota_code}) is at ${var.quota_alarm_percent}% of its quota or more (Stage 12 step 9.2). The next VPC this account needs is refused at apply: request an increase in Service Quotas before it."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = var.quota_alarm_percent
  treat_missing_data  = "notBreaching"
  alarm_actions       = [local.alerts_topic_arn]

  metric_query {
    id          = "usage"
    return_data = false

    metric {
      namespace   = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_namespace
      metric_name = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_name
      period      = 3600
      stat        = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_statistic_recommendation

      dimensions = {
        Class    = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_dimensions[0].class
        Resource = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_dimensions[0].resource
        Service  = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_dimensions[0].service
        Type     = data.aws_servicequotas_service_quota.vpcs_per_region.usage_metric[0].metric_dimensions[0].type
      }
    }
  }

  metric_query {
    id          = "share"
    expression  = "usage / SERVICE_QUOTA(usage) * 100"
    label       = "VPCs per Region, % of the quota"
    return_data = true
  }
}
