# Outputs - what the slice republishes, and what Stage 6 will read through
# terraform_remote_state rather than paste.

output "derived_bucket_name" {
  description = "The derived zone. Stage 11 scopes Macie and CloudTrail data events on it; Stage 6 grants the project execution roles into its prefixes."
  value       = module.derived.bucket_name
}

output "derived_bucket_arn" {
  description = "The derived zone's ARN - the prefix scoping in identity/sso/ is written against this shape."
  value       = module.derived.bucket_arn
}

output "data_key_arn" {
  description = "The account's data CMK. D31's read control: Stage 6 adds the project execution roles to its policy as a second Principal, which is the extension point step 9.3 asks for."
  value       = module.data_key.key_arn
}

output "data_key_alias" {
  description = "alias/awsds-<env>-data - one data CMK per account, same pattern as the lake's."
  value       = module.data_key.alias_name
}

output "athena_workgroup_name" {
  description = "The enforced workgroup - identity/sso/ scopes athena:StartQueryExecution to it by ARN."
  value       = aws_athena_workgroup.this.name
}

output "athena_workgroup_arn" {
  description = "The workgroup ARN, so the persona grant names a resource instead of a wildcard."
  value       = aws_athena_workgroup.this.arn
}

output "resource_link_names" {
  description = "The local databases that resolve to the lake's shared ones - what an Athena query addresses."
  value       = { for k, db in aws_glue_catalog_database.link : k => db.name }
}
