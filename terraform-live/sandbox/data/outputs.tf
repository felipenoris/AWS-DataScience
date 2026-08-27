# Outputs - what other slices read through terraform_remote_state (never pasted).
#
# FOUR OUTPUTS LEFT 2026-08-26 with the derived zone (derived bucket + workgroup, name and
# ARN each) - D19 revised: the zone is the SMUS project path, and identity/sso/ stopped
# reading this state in the same revision.

output "data_key_arn" {
  description = "This account's data CMK - the sandbox lake's key in Sandbox (Stage 16), held empty in Development (D19 as revised 2026-08-26)."
  value       = module.consumer_data.data_key_arn
}

output "resource_link_names" {
  description = "The local databases resolving to the lake's shared ones."
  value       = module.consumer_data.resource_link_names
}
