# Read by production/data/ (the key and bucket policies name the job and debug roles, step 1.1), by
# Stage 10's application slices (iam:PassRole to the job role) and by ./aws/deploytargets.py by name.

output "job_role_arn" {
  description = "awsds-<env>-job-exec, the role every pipeline-submitted Glue and SageMaker job in this account runs as (step 3.1)."
  value       = module.job_role.role_arn
}

output "job_role_name" {
  description = "The job role's name, the contract DT-4 and Stage 5a step 1.4's drop-box statements name."
  value       = module.job_role.role_name
}

output "job_log_group_names" {
  description = "The job log groups this slice declares with a retention (step 3.1, EXC-10)."
  value       = sort([for group in aws_cloudwatch_log_group.job : group.name])
}

output "model_package_group_arns" {
  description = "The Model Registry's package groups, keyed by application or model family (step 3.2)."
  value       = { for family, group in aws_sagemaker_model_package_group.this : family => group.arn }
}

output "debug_role_arn" {
  description = "awsds-<env>-debug, the escape hatch (step 6.1): assumable only while var.debug_window_end is in the future."
  value       = module.debug_role.role_arn
}

output "job_security_group_id" {
  description = "awsds-<env>-jobs, the group a Glue job's connection and a processing job's VpcConfig name (decision 12); the warehouse's 5439 rule names it (step 9.1)."
  value       = aws_security_group.jobs.id
}

output "glue_connection_name" {
  description = "awsds-<env>-jobs, the Glue network connection the application slice declares its Glue job on (decision 12)."
  value       = aws_glue_connection.jobs.name
}

output "producer_proof_job_name" {
  description = "awsds-<env>-producer-proof, step 2.4's proof job: one run per --MODE, producer then pickup."
  value       = aws_glue_job.producer_proof.name
}

output "producer_proof_script" {
  description = "Where the infrastructure user uploads proofs/producer_proof.py before a run (step 2.4)."
  value       = local.producer_proof_script
}
