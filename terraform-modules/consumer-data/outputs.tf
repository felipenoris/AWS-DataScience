# Outputs - what the slice republishes, and what other slices read through
# terraform_remote_state rather than paste.
#
# No derived-zone outputs: D19 as revised (2026-08-26) makes the derived zone the SMUS project
# path, owned by terraform-modules/sagemaker-prereqs/, and identity/sso/ no longer reads this
# state.

output "data_key_arn" {
  description = "The account's data CMK - today the sandbox lake's key in Sandbox (Stage 16); the copy in Staging stands empty under its original `awsds-dev-data` alias."
  value       = module.data_key.key_arn
}

output "data_key_alias" {
  description = "alias/awsds-<env>-data - one data CMK per account, same pattern as the lake's."
  value       = module.data_key.alias_name
}

output "resource_link_names" {
  description = "The local databases that resolve to the lake's shared ones - what an Athena query addresses."
  value       = { for k, db in aws_glue_catalog_database.link : k => db.name }
}
