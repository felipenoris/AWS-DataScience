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

output "ecr_app_etl_repository_url" {
  description = "The push/pull target for the first application image (Stage 7 step 5.1, Stage 8 step 2)."
  value       = module.ecr_app_etl.repository_url
}

output "ecr_deploy_repository_url" {
  description = "The push/pull target for the deploy image, the deploy runner's job image (Stage 8 steps 3.1 and 4.3)."
  value       = module.ecr_deploy.repository_url
}

output "ecr_repository_arns" {
  description = "The image repositories' ARNs, keyed by image - what a consumer-side IAM statement names by key, and what the build runner's push statement names whole (Stage 7 step 6.1)."
  value = {
    base    = module.ecr_base.repository_arn
    dev-env = module.ecr_dev_env.repository_arn
    app-etl = module.ecr_app_etl.repository_arn
    deploy  = module.ecr_deploy.repository_arn
  }
}

output "releases_bucket_arn" {
  description = "The release store (Stage 8 decision 20) - what the build runner's put statement names."
  value       = module.releases_bucket.bucket_arn
}

output "releases_bucket_name" {
  description = "The release store's name, awsds-<env>-releases - what a pipeline's `aws s3 cp` names."
  value       = module.releases_bucket.bucket_name
}

output "pull_through_cache_prefixes" {
  description = "The cache rules' repository prefixes (Stage 7 step 5.2) - the repository families the runner may import into."
  value       = keys(aws_ecr_pull_through_cache_rule.this)
}

output "codeartifact_domain_name" {
  description = "The CodeArtifact domain (INT-02) - `aws codeartifact login --domain` reads it."
  value       = aws_codeartifact_domain.packages.domain
}

output "codeartifact_repository_names" {
  description = "The two repositories a consumer logs in to."
  value       = [aws_codeartifact_repository.pypi.repository, aws_codeartifact_repository.crates.repository]
}
