# Outputs. Null until release.tf names a release.

output "glue_job_name" {
  description = "awsds-<env>-app-etl - the name the rendered workflow's transform task starts."
  value       = one(aws_glue_job.this[*].name)
}

output "release_prefix" {
  description = "The release's tree in the outputs bucket, where the release job copies the bundle (Stage 10 step 2.4)."
  value       = local.release_prefix
}

output "image_uri" {
  description = "The release's image by digest, for a by-hand render (Stage 8 step 3.8); the pipeline takes build-image's."
  value       = var.release == null ? null : "${data.terraform_remote_state.registry.outputs.ecr_app_etl_repository_url}@${var.release.digest}"
}
