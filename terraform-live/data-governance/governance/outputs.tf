# Outputs - what other slices read through terraform_remote_state (never pasted).

output "domain_id" {
  description = "The value every member account's sagemaker/ slice reads on its second apply - the blueprint configurations name it."
  value       = aws_datazone_domain.this.id
}

output "domain_arn" {
  description = "The domain ARN."
  value       = aws_datazone_domain.this.arn
}

output "portal_url" {
  description = "The AWS-issued portal URL, reached from any network with an Identity Center session (D39). D15 phase 1 needs no domain name of ours because of it."
  value       = aws_datazone_domain.this.portal_url
}

output "root_domain_unit_id" {
  description = "The root domain unit - where the authorization policies live. Since 2026-08-22 that is not hypothetical: grants.tf attaches a CREATE_PROJECT_FROM_PROJECT_PROFILE grant per profile here. The domain is still not subdivided, so this is the only unit there is."
  value       = aws_datazone_domain.this.root_domain_unit_id
}

output "domain_execution_role_arn" {
  description = "The domain execution role - what the portal and the SageMaker Catalog act as in this account."
  value       = module.domain_execution_role.role_arn
}

output "domain_service_role_arn" {
  description = "The domain service role."
  value       = module.domain_service_role.role_arn
}

output "project_profile_ids" {
  description = "The profiles, by name - empty until pass 2c."
  value       = { for k, p in awscc_datazone_project_profile.this : k => p.project_profile_id }
}

output "project_profile_creators" {
  description = "Who may create a project from which profile - the applied form of local.project_profiles' group column, by group name rather than group id (aws/INDEX.md rule 1), or the InfrastructureAccess role of the profile's account where the group is null (Stage 18 decision 3). Empty until pass 2c."
  value       = { for k, p in local.project_profiles : k => coalesce(p.group, "InfrastructureAccess (${p.account})") if var.profiles_enabled }
}

output "model_governance_project_id" {
  description = "The project that owns the Bedrock model listings (Stage 17 decision 13). An associated account's console selects it by name."
  value       = var.profiles_enabled ? awscc_datazone_project.model_governance[0].project_id : null
}
