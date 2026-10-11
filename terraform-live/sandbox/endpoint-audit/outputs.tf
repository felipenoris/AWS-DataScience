# What this slice publishes. A query names the store by its id, the last segment of the ARN:
# SELECT ... FROM <id>.

output "event_data_store_arn" {
  description = "The store of S3 requests a VPC endpoint policy refused."
  value       = aws_cloudtrail_event_data_store.endpoint_refusals.arn
}

output "event_data_store_id" {
  description = "The id a CloudTrail Lake query names in its FROM clause."
  value       = element(split("/", aws_cloudtrail_event_data_store.endpoint_refusals.arn), 1)
}
