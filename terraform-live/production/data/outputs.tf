# Read by Stage 8's application slices and Stage 10's render through the deploy role's
# state_read_keys, by production/warehouse/ for the key (step 9.1), and by ./aws/deploytargets.py by
# name. staging/data/ gives the same names.

output "data_key_arn" {
  description = "The account data CMK, alias/awsds-<env>-data (decision 1): both buckets, the workgroup's results, the job log groups and the warehouse namespace."
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
  description = "awsds-<env>-outputs, the applications' outputs: the release's tree under applications/, the inbox, each application's work/ and outbox/, model archives under models/."
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
  description = "The local Glue database applications write their tables to (step 1.3)."
  value       = aws_glue_catalog_database.app_outputs.name
}

# The governed source an application's Glue job reads through Lake Formation's full-table-access mode,
# on an Iceberg catalog over the lake account's Glue catalog (Stage 9 2.4's recipe): the catalog's id,
# the curated database and table, and the curated bucket its warehouse setting names. The application
# slice reads them here, since the deploy role reads no other account's state.
output "lake_catalog_id" {
  description = "The lake account's Glue catalog id, the Iceberg catalog's glue.id."
  value       = data.aws_caller_identity.lake.account_id
}

output "curated_database" {
  description = "The lake's curated database, as the lake account's catalog names it."
  value       = data.terraform_remote_state.lake.outputs.database_names["curated"]
}

output "curated_table" {
  description = "The governed table an application reads, curated.trades (Stage 9 step 2.1)."
  value       = data.terraform_remote_state.lake.outputs.producer_table_name
}

output "curated_bucket_name" {
  description = "The curated bucket, whose warehouse/ prefix is the Iceberg catalog's root."
  value       = data.terraform_remote_state.lake.outputs.bucket_names["curated"]
}
