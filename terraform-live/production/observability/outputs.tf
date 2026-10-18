# What a later slice or an instrument reads from this one.

output "dashboard_name" {
  description = "The hub dashboard (Stage 12 steps 1.1 and 1.2)."
  value       = aws_cloudwatch_dashboard.hub.dashboard_name
}

output "alarm_names" {
  description = "The alarms this slice owns, each notifying awsds-<env>-alerts."
  value = [
    aws_cloudwatch_metric_alarm.proxy_refusals.alarm_name,
    aws_cloudwatch_metric_alarm.vpcs_per_region.alarm_name,
  ]
}

output "proxy_metric_namespace" {
  description = "The namespace of the proxy log's two metrics, Requests and Refused."
  value       = local.proxy_metric_namespace
}
