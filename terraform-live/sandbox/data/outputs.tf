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

output "outputs_bucket_name" {
  description = "awsds-<env>-outputs - where an application run by hand in this account writes, one prefix per application (Stage 8 step 2.4)."
  value       = module.outputs_bucket.bucket_name
}

output "outputs_bucket_arn" {
  description = "The outputs bucket's ARN - what an application job role's statement names."
  value       = module.outputs_bucket.bucket_arn
}
