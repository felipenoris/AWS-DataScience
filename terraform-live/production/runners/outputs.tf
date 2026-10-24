# Outputs for a person diagnosing a job, and for ./aws/supplychain.py's reader.

output "instance_id" {
  description = "The build runner, or null when the apply left var.build_runner false. `aws ssm start-session --target <this>` for a shell; /var/log/awsds-runner-boot.log holds the first boot, including the registration's result."
  value       = one(aws_instance.runner[*].id)
}

output "private_ip" {
  description = "The build runner's address, or null without it - what GitLab's access log shows for a job's clone, and what the proxy's access log shows for a build's fetches."
  value       = one(aws_instance.runner[*].private_ip)
}

output "role_arn" {
  description = "The build runner's role, or null without it - push to the image repositories, pull through the cache, its token, the CA root, Session Manager. No deploy permission, by design (6.1)."
  value       = one(module.role[*].role_arn)
}

output "deploy_runner_instance_id" {
  description = "The deploy runner, or null while no deploy image is pinned. Its first boot assumes each deploy role once and logs the result to /var/log/awsds-runner-boot.log."
  value       = one(aws_instance.deploy_runner[*].id)
}

output "test_runner_instance_id" {
  description = "The test runner (Stage 8 decision 11). Its first boot reads, from a container, that the metadata service gives a job no token, and logs the result to /var/log/awsds-runner-boot.log."
  value       = aws_instance.test_runner.id
}
