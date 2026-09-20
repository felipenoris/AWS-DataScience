# Two alarms, on the two things that are irreversible or unbounded. Both notify nobody, which is the
# same state every other alarm in this repository is in: D12's budget has no subscriber and this
# account's first automatic notification is Stage 15 step 4's GuardDuty topic, in Audit. What they
# buy today is a state ./aws/warehouse.py and Stage 12's dashboard can read, not a page anybody
# receives (Lesson 5 - said here rather than implied).

# ---------------------------------------------------------------------------- the ratchet (5b 6.2)
#
# AWS: "Once you scale your data warehouse beyond 4 RPUs, your data warehouse will continue to use
# more RPUs, and Amazon Redshift won't scale your data warehouse back down to 4 RPUs." So this is
# not an alarm that says "this will pass": it says A MANUAL UpdateWorkgroup IS NOW OWED, and the
# remedy itself "might cancel some of the queries running on your workgroup".
#
# The metric is "Average number of compute units allocated during the past 30 minutes, rounded up to
# the nearest integer" (AWS, read 2026-09-20), so one period is 30 minutes of history and a single
# expensive query is visible for that long. `notBreaching` on missing data is load-bearing for an
# [E] workgroup: a destroyed workgroup publishes nothing, and the default (`missing`) would put this
# alarm into INSUFFICIENT_DATA after every `make down` - a state change per session, produced by the
# machinery working exactly as designed.
resource "aws_cloudwatch_metric_alarm" "compute_capacity" {
  alarm_name          = "${local.name}-compute-capacity"
  alarm_description   = "Redshift Serverless allocated RPUs above the ${var.base_capacity}-RPU floor (Stage 5b step 6.2). The ratchet is irreversible: the warehouse does not return to ${var.base_capacity} on its own, so this alarm reports that a manual UpdateWorkgroup is owed. No action: no SNS topic exists in this account yet - see Stage 12."
  namespace           = "AWS/Redshift-Serverless"
  metric_name         = "ComputeCapacity"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = var.base_capacity
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Workgroup = local.name
  }
}

# --------------------------------------------------------- the storage nothing bounds (6h decision 7)
#
# THE QUOTA IS A RUNAWAY GUARD AND NOT A COST GUARD. One schema filled to its 1 TB quota is 24.58
# USD/month - half the D12 ceiling - and NOTHING BOUNDS THE NUMBER OF SCHEMAS: 6h creates them by
# SQL, one per theme, and a schema is free to create. So the compensating control is a namespace-wide
# alarm on the bytes actually stored, and its threshold is argued in dollars (data.tf does the
# conversion) because dollars are what is being defended.
#
# The metric is in MEGABYTES with dimension {Namespace} (AWS, read 2026-09-20) - a different
# dimension set from ComputeCapacity's {Workgroup}, which is why this alarm survives `make down`
# while the other one goes quiet: the namespace is [P] and keeps publishing.
resource "aws_cloudwatch_metric_alarm" "data_storage" {
  alarm_name          = "${local.name}-data-storage"
  alarm_description   = "Redshift Managed Storage above ${var.storage_alarm_usd} USD/month for namespace ${local.name} (Stage 6h decision 7). ${local.storage_alarm_mb} MB at 0.024 USD/GB-month. This is the only bound on total storage: a schema QUOTA bounds one schema and nothing bounds the number of schemas. No action - see Stage 12."
  namespace           = "AWS/Redshift-Serverless"
  metric_name         = "DataStorage"
  statistic           = "Maximum"
  period              = 21600
  evaluation_periods  = 1
  threshold           = local.storage_alarm_mb
  comparison_operator = "GreaterThanThreshold"
  # A namespace holding nothing publishes nothing, and "no data stored" must not read as a breach.
  treat_missing_data = "notBreaching"

  dimensions = {
    Namespace = local.name
  }
}
