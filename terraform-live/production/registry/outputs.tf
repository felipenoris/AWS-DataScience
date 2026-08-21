# Outputs - what other slices and by-hand steps read, never paste.

output "registry_key_arn" {
  description = "The slice's own CMK - ECR layers and CodeArtifact assets (D14 option preservation)."
  value       = module.registry_key.key_arn
}

output "ecr_base_repository_url" {
  description = "The push/pull target for the base image (Stage 6 step 5.0, Stage 8 step 1)."
  value       = module.ecr_base.repository_url
}

output "ecr_dev_env_repository_url" {
  description = "The push/pull target for the SMUS custom image - what */dev-env/ registers (Stage 6 step 5.1, INT-01/INT-17)."
  value       = module.ecr_dev_env.repository_url
}

output "ecr_repository_arns" {
  description = "Both ARNs - what a consumer-side IAM statement names."
  value = {
    base    = module.ecr_base.repository_arn
    dev-env = module.ecr_dev_env.repository_arn
  }
}

output "codeartifact_domain_name" {
  description = "The CodeArtifact domain (INT-02) - `aws codeartifact login --domain` reads it."
  value       = aws_codeartifact_domain.packages.domain
}

output "codeartifact_repository_names" {
  description = "The two repositories a consumer logs in to."
  value       = [aws_codeartifact_repository.pypi.repository, aws_codeartifact_repository.crates.repository]
}
