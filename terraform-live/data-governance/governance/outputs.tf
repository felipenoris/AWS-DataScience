# Outputs - what other slices read through terraform_remote_state (never pasted).

output "domain_id" {
  description = "THE VALUE EVERY MEMBER ACCOUNT'S sagemaker/ SLICE READS on its second apply - the blueprint configurations name it."
  value       = aws_datazone_domain.this.id
}

output "domain_arn" {
  description = "The domain ARN."
  value       = aws_datazone_domain.this.arn
}

output "portal_url" {
  description = "The AWS-issued portal URL - INT-16's portal half is read against it (step 1.7), and D15 phase 1 needs no domain name of ours because of it."
  value       = aws_datazone_domain.this.portal_url
}

output "root_domain_unit_id" {
  description = "The root domain unit - where authorization policies (who may create projects, who may join) would be granted if this design ever subdivided the domain. Nothing creates one today."
  value       = aws_datazone_domain.this.root_domain_unit_id
}

output "domain_execution_role_arn" {
  description = "The domain execution role - the principal AWS's own network-isolation deny (DenyUserAccessFromUnauthorizedVPCs) would be written against if INT-16's fallback (i) is ever adopted (step 1.7)."
  value       = module.domain_execution_role.role_arn
}

output "domain_service_role_arn" {
  description = "The domain service role."
  value       = module.domain_service_role.role_arn
}

output "project_profile_ids" {
  description = "The two profiles, by name - empty until pass 2c."
  value       = { for k, p in awscc_datazone_project_profile.this : k => p.project_profile_id }
}
