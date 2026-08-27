# Outputs - what the slice republishes, and what other slices read through
# terraform_remote_state rather than paste.
#
# FOUR OUTPUTS LEFT ON 2026-08-26 with the derived zone (derived_bucket_name/arn,
# athena_workgroup_name/arn) - D19 as revised: the zone is the SMUS project path now, owned by
# terraform-modules/sagemaker-prereqs/, and identity/sso/ stopped reading this state in the
# same revision (its consumer_data lookup left with the statements that consumed it).

output "data_key_arn" {
  description = "The account's data CMK - today the sandbox lake's key in Sandbox (Stage 16), held empty in Development."
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
