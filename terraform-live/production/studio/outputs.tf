# Outputs - what other slices and by-hand steps read, never paste.

output "provisioning_role_arn" {
  description = "The blueprint provisioning role in this account."
  value       = module.sagemaker_prereqs.provisioning_role_arn
}

output "manage_access_role_arn" {
  description = "The manage-access role, which fulfils a subscription to a table of this account's project."
  value       = module.sagemaker_prereqs.manage_access_role_arn
}

output "project_boundary_arn" {
  description = "The D13 boundary, imposed on blueprint-authored roles through the blueprint configuration."
  value       = module.sagemaker_prereqs.project_boundary_arn
}

output "project_key_arn" {
  description = "This account's project CMK - not its data CMK. A stage of an application's manifest names it as PROJECT_KEY_ARN."
  value       = module.sagemaker_prereqs.project_key_arn
}

output "regional_parameters" {
  description = "What the blueprint configurations are pointed at: the VPC and the private subnets."
  value       = module.sagemaker_prereqs.regional_parameters
}

output "project_roles" {
  description = "The deployment project's roles this slice attaches the workflows grant and the person-session deny to, by name."
  value       = var.project_roles
}

output "app_genai_inference_profile_arn" {
  description = "app-genai's model in this account, the application inference profile genai.tf declares (Stage 17 decision 23 (a)). scripts/deploy-application.py reads it as the deploy role and fills the application's MODEL_ID with it."
  value       = aws_bedrock_inference_profile.app_genai.arn
}
