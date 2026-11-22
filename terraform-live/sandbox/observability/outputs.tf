# What a later slice or an instrument reads from this one.

output "alerts_topic_arn" {
  description = "awsds-<env>-alerts - this account's alarm target (Stage 12 step 2.2). sandbox/warehouse/'s two alarms take it as their action."
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "The account dashboard (Stage 12 step 1.1)."
  value       = aws_cloudwatch_dashboard.sandbox.dashboard_name
}

output "quota_alarm_names" {
  description = "The quota alarms, keyed as var.quotas is (Stage 12 step 9.2)."
  value       = { for k, a in aws_cloudwatch_metric_alarm.quota : k => a.alarm_name }
}
