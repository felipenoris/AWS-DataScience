# Outputs - what other slices and by-hand steps read, never paste.

output "vpc_id" {
  description = "The lake account's VPC, the Tooling configuration's VpcId (Stage 6f step 11)."
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "The private subnets by zone id, the Tooling configuration's Subnets."
  value       = module.vpc.private_subnet_ids
}

output "provisioning_role_arn" {
  description = "The blueprint provisioning role in the lake account - one of the two Lake Formation administrator seats data/ declares behind LAKE_PUBLISHERS."
  value       = module.sagemaker_prereqs.provisioning_role_arn
}

output "manage_access_role_arn" {
  description = "The manage-access role in the lake account - the other seat."
  value       = module.sagemaker_prereqs.manage_access_role_arn
}

output "project_boundary_arn" {
  description = "The D13 boundary (US-8), imposed on the publishing project's role through the blueprint configuration; data/'s publisher grant refuses a role without it."
  value       = module.sagemaker_prereqs.project_boundary_arn
}

output "project_key_arn" {
  description = "The lake account's project CMK - not its data CMK."
  value       = module.sagemaker_prereqs.project_key_arn
}

output "regional_parameters" {
  description = "What the Tooling configuration is pointed at."
  value       = module.sagemaker_prereqs.regional_parameters
}
