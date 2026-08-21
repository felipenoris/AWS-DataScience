# Outputs - what other slices and by-hand steps read, never paste.

output "provisioning_role_arn" {
  description = "The blueprint provisioning role in this account."
  value       = module.sagemaker_prereqs.provisioning_role_arn
}

output "manage_access_role_arn" {
  description = "The manage-access role - verification (xiv) asks whether it needs a Lake Formation data lake administrator seat, and if so it is added to the ONE aws_lakeformation_data_lake_settings this account already has (in terraform-modules/consumer-data/), never a second one."
  value       = module.sagemaker_prereqs.manage_access_role_arn
}

output "project_boundary_arn" {
  description = "The D13 boundary (US-8) - imposed on blueprint-authored roles through the blueprint configuration."
  value       = module.sagemaker_prereqs.project_boundary_arn
}

output "project_key_arn" {
  description = "This account's project CMK - NOT its data CMK."
  value       = module.sagemaker_prereqs.project_key_arn
}

output "regional_parameters" {
  description = "What the blueprint configuration is pointed at - verification (iii)'s subject."
  value       = module.sagemaker_prereqs.regional_parameters
}
