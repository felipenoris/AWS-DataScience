# Stage 12 step 9.2: an alarm at quota_alarm_percent of each quota in var.quotas. The metric is the
# quota's own usage metric as Service Quotas reports it (data.tf), and SERVICE_QUOTA() reads the
# applied value at evaluation, so an increase needs no apply. A per-VPC quota adds the VPC's id, the
# one dimension Service Quotas leaves to the caller.
#
# What an 80 % alarm cannot see: a quota of zero refuses the first use before any datapoint exists,
# which is how Stage 17 met its training, endpoint and transform quotas. Reading the quota before a
# stage's first use is the control for that case.

resource "aws_cloudwatch_metric_alarm" "quota" {
  for_each = var.quotas

  alarm_name          = "awsds-${var.env}-quota-${each.key}"
  alarm_description   = "${data.aws_servicequotas_service_quota.alarmed[each.key].quota_name} (${each.value.quota_code}) is at ${var.quota_alarm_percent}% of its quota or more (Stage 12 step 9.2). The next one is refused: request an increase in Service Quotas, or stop what is running."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = var.quota_alarm_percent
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  metric_query {
    id          = "usage"
    return_data = false

    metric {
      namespace   = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_namespace
      metric_name = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_name
      period      = 3600
      stat        = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_statistic_recommendation

      dimensions = merge(
        {
          Class    = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_dimensions[0].class
          Resource = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_dimensions[0].resource
          Service  = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_dimensions[0].service
          Type     = data.aws_servicequotas_service_quota.alarmed[each.key].usage_metric[0].metric_dimensions[0].type
        },
        each.value.per_vpc ? { ResourceId = local.vpc_id } : {},
      )
    }
  }

  metric_query {
    id          = "share"
    expression  = "usage / SERVICE_QUOTA(usage) * 100"
    label       = "${each.key}, % of the quota"
    return_data = true
  }

  # The topic must admit CloudWatch before an alarm can publish to it.
  depends_on = [aws_sns_topic_policy.alerts]
}
