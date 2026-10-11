# What this slice publishes. The trail delivers gzipped JSON files under
# s3://<bucket>/AWSLogs/<account>/CloudTrail/<region>/<yyyy>/<mm>/<dd>/.

output "trail_arn" {
  description = "The trail of S3 requests a VPC endpoint policy refused."
  value       = aws_cloudtrail.refusals.arn
}

output "bucket" {
  description = "The bucket the trail delivers to."
  value       = aws_s3_bucket.refusals.id
}
