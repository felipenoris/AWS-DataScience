# Two alarms, on the two things that are irreversible or unbounded. Both publish to awsds-prod-alerts,
# the topic production/foundation/ owns (Stage 8 decision 5; Stage 12 adopts it), whose policy admits
# CloudWatch since PR #179. The topic reaches a person only through a confirmed subscription, which
# ./aws/observability.py OB-3 reads.

# ---------------------------------------------------------------------------- the ratchet (5b 6.2)
#
# AWS: once the warehouse scales beyond 4 RPUs it never scales back down to 4 on its own. So this
# alarm does not say "this will pass": it says a manual UpdateWorkgroup is owed, and the remedy itself
# "might cancel some of the queries running on your workgroup".
#
# The metric is the average number of compute units allocated during the past 30 minutes, rounded up
# (AWS, read 2026-09-20), so one period is 30 minutes of history. `notBreaching` on missing data is
# load-bearing for an [E] workgroup: a destroyed workgroup publishes nothing, and the default
# (`missing`) would put this alarm into INSUFFICIENT_DATA after every `make down`.
resource "aws_cloudwatch_metric_alarm" "compute_capacity" {
  alarm_name          = "${local.name}-compute-capacity"
  alarm_description   = "Redshift Serverless allocated RPUs above the ${var.base_capacity}-RPU floor (Stage 5b step 6.2, Stage 9 step 9.1). The ratchet is irreversible: the warehouse does not return to ${var.base_capacity} on its own, so this alarm reports that a manual UpdateWorkgroup is owed."
  namespace           = "AWS/Redshift-Serverless"
  metric_name         = "ComputeCapacity"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = var.base_capacity
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [local.alerts_topic_arn]

  dimensions = {
    Workgroup = local.name
  }
}

# --------------------------------------------------------- the storage nothing bounds (6h decision 7)
#
# The schema quota is a runaway guard and not a cost guard. One schema filled to its 1 TB quota is
# 24.58 USD/month, half the D12 ceiling, and nothing bounds the number of schemas: step 9.3 creates
# them by SQL, and a schema is free to create. The compensating control is a namespace-wide alarm on
# the bytes stored, its threshold argued in dollars (data.tf does the conversion). WH-4b fails without
# it.
#
# The metric is in megabytes with dimension {Namespace}, a different dimension set from
# ComputeCapacity's {Workgroup}, which is why this alarm keeps working while the compute is down: the
# namespace is [P] and keeps publishing.
resource "aws_cloudwatch_metric_alarm" "data_storage" {
  alarm_name          = "${local.name}-data-storage"
  alarm_description   = "Redshift Managed Storage above ${var.storage_alarm_usd} USD/month for namespace ${local.name} (Stage 6h decision 7, Stage 9 step 9.1). ${local.storage_alarm_mb} MB at 0.024 USD/GB-month. This is the only bound on total storage: a schema QUOTA bounds one schema and nothing bounds the number of schemas."
  namespace           = "AWS/Redshift-Serverless"
  metric_name         = "DataStorage"
  statistic           = "Maximum"
  period              = 21600
  evaluation_periods  = 1
  threshold           = local.storage_alarm_mb
  comparison_operator = "GreaterThanThreshold"
  # A namespace holding nothing publishes nothing, and "no data stored" must not read as a breach.
  treat_missing_data = "notBreaching"
  alarm_actions      = [local.alerts_topic_arn]

  dimensions = {
    Namespace = local.name
  }
}
