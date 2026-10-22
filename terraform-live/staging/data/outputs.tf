# Read by Stage 8's application slices and Stage 10's render through the deploy role's
# state_read_keys, and by ./aws/deploytargets.py by name: production/data/'s names.

output "data_key_arn" {
  description = "The account data CMK, alias/awsds-<env>-data: both buckets, the workgroup's results and the job log groups."
  value       = module.consumer_data.data_key_arn
}

output "data_key_alias" {
  description = "alias/awsds-<env>-data - one data CMK per account."
  value       = module.consumer_data.data_key_alias
}

output "resource_link_names" {
  description = "The local databases that resolve to the lake's shared ones - what a query or a job addresses."
  value       = module.consumer_data.resource_link_names
}

output "outputs_bucket_name" {
  description = "awsds-<env>-outputs, the applications' outputs: the release's tree under applications/, the inbox, each application's work/ and outbox/ (Stage 10 decision 17)."
  value       = module.outputs_bucket.bucket_name
}

output "outputs_bucket_arn" {
  description = "The outputs bucket's ARN."
  value       = module.outputs_bucket.bucket_arn
}

output "derived_bucket_name" {
  description = "awsds-<env>-derived, the workgroup's results under results/ (decision 11)."
  value       = module.derived_bucket.bucket_name
}

output "derived_bucket_arn" {
  description = "The derived bucket's ARN."
  value       = module.derived_bucket.bucket_arn
}

output "workgroup_name" {
  description = "awsds-<env>-athena, the enforced workgroup (decision 11)."
  value       = aws_athena_workgroup.this.name
}

output "app_outputs_database" {
  description = "The local Glue database applications write their tables to (step 4.1)."
  value       = aws_glue_catalog_database.app_outputs.name
}
