# Outputs - what other slices read through terraform_remote_state (never pasted). Stage 6 is the
# first consumer: the blueprint-provisioned project roles need the derived prefixes and the key.

output "derived_bucket_name" {
  description = "The derived zone in this account - Stage 11's Macie and CloudTrail data-event scope."
  value       = module.consumer_data.derived_bucket_name
}

output "derived_bucket_arn" {
  description = "The derived zone's ARN."
  value       = module.consumer_data.derived_bucket_arn
}

output "zone_key_arn" {
  description = "This account's zn-lab CMK - D31's read control, and Stage 6's extension point for the project execution roles."
  value       = module.consumer_data.zone_key_arn
}

output "athena_workgroup_name" {
  description = "The enforced workgroup (D19 practice i)."
  value       = module.consumer_data.athena_workgroup_name
}

output "athena_workgroup_arn" {
  description = "The workgroup ARN - identity/sso/ scopes athena:StartQueryExecution to it."
  value       = module.consumer_data.athena_workgroup_arn
}

output "resource_link_names" {
  description = "The local databases resolving to the lake's shared ones."
  value       = module.consumer_data.resource_link_names
}
