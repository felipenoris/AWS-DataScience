# Read by staging/data/ (the key and bucket policies name the job role, step 4.1), by Stage 10's
# render table and staging/orchestration/ (iam:PassRole to the job role) and by
# ./aws/deploytargets.py by name.

output "job_role_arn" {
  description = "awsds-<env>-job-exec, the role every pipeline-submitted Glue and SageMaker job in this account runs as (step 4.3, Stage 8 step 2.5)."
  value       = module.job_role.role_arn
}

output "job_role_name" {
  description = "The job role's name, the contract DT-4 reads and Stage 10 decision 6's render table maps."
  value       = module.job_role.role_name
}

output "job_log_group_names" {
  description = "The job log groups this slice declares with a retention (step 4.3, EXC-10)."
  value       = sort([for group in aws_cloudwatch_log_group.job : group.name])
}

output "job_security_group_id" {
  description = "awsds-<env>-jobs, the group a Glue job's connection and a processing job's VpcConfig name (decision 12)."
  value       = aws_security_group.jobs.id
}

output "glue_connection_name" {
  description = "awsds-<env>-jobs, the Glue network connection the application slice declares its Glue job on (decision 12)."
  value       = aws_glue_connection.jobs.name
}
