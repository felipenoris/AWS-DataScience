# Outputs for a person diagnosing a job, and for ./aws/supplychain.py's reader.

output "instance_id" {
  description = "The runner. `aws ssm start-session --target <this>` for a shell; /var/log/awsds-runner-boot.log holds the first boot, including the registration's result."
  value       = aws_instance.runner.id
}

output "private_ip" {
  description = "The runner's address - what GitLab's access log shows for a job's clone, and what the proxy's access log shows for a build's fetches."
  value       = aws_instance.runner.private_ip
}

output "role_arn" {
  description = "The runner's role - push to the image repositories, pull through the cache, its token, the CA root, Session Manager. No deploy permission, by design (6.1)."
  value       = module.role.role_arn
}
