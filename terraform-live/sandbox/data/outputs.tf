# Outputs - what other slices read through terraform_remote_state (never pasted).
#
# The derived zone's outputs (derived bucket and workgroup, name and ARN each) went with the zone on
# 2026-08-26 - D19 revised: the zone is the SMUS project path, and identity/sso/ stopped reading this
# state in the same revision.

output "data_key_arn" {
  description = "This account's data CMK - the key of the sandbox lake (Stage 16) and the warehouse namespace (Stage 5b)."
  value       = module.consumer_data.data_key_arn
}

output "resource_link_names" {
  description = "The local databases resolving to the lake's shared ones."
  value       = module.consumer_data.resource_link_names
}

output "lake_catalog_id" {
  description = "The lake account's catalog id, the account Lake Formation shares from: sandbox/warehouse/ names it in the access roles' read of a governed share (Stage 9 9.7)."
  value       = data.aws_caller_identity.lake.account_id
}
