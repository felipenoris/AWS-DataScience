# Outputs - what runners/ reads through terraform_remote_state, and what a person needs to reach
# or diagnose the host. Nothing a policy pins: the address is read from the records.

output "instance_id" {
  description = "The GitLab host. A shell is `aws ssm start-session --target <this>` (Session Manager, no port 22); the first boot's log is /var/log/awsds-gitlab-boot.log there, and `aws ec2 get-console-output --instance-id <this> --latest` needs no endpoint when SSM itself failed."
  value       = aws_instance.gitlab.id
}

output "private_ip" {
  description = "The address both records carry - survives stop/start (verification i)."
  value       = aws_instance.gitlab.private_ip
}

output "gitlab_url" {
  description = "https://gitlab.awsds.internal - resolvable in all five VPCs and from the tunnel, reachable from the three sources 1.2 admits."
  value       = "https://${local.gitlab_host}"
}

output "pages_url_pattern" {
  description = "https://<project>.awsds-pages.internal - resolvable from VPC-SharedServices and the tunnel only (4.2)."
  value       = "https://<project>.${local.pages_host}"
}

output "role_arn" {
  description = "The host's role - Session Manager, the two buckets and their key, the three secrets, the published certificates, and nothing else."
  value       = module.role.role_arn
}

output "gitlab_security_group_id" {
  description = "GitLab's group - HTTPS from the tunnel host, the Interactive private tiers and the runners."
  value       = aws_security_group.gitlab.id
}

output "runner_security_group_id" {
  description = "The runners' group, declared here so GitLab's rule never names an [E] object; production/runners/ attaches it (6.1)."
  value       = aws_security_group.runner.id
}

output "gitlab_rb_object" {
  description = "The rendered gitlab.rb's S3 location - what the bootstrap and `awsds-gitlab-refresh` fetch (decision 8)."
  value       = "s3://${local.objects_bucket}/${aws_s3_object.gitlab_rb.key}"
}

output "data_volume_id" {
  description = "The 50 GiB data volume at /var/opt/gitlab - the object the DLM policy snapshots and a replacement re-attaches."
  value       = aws_ebs_volume.data.id
}

output "dlm_policy_id" {
  description = "The daily snapshot policy over the data volume."
  value       = aws_dlm_lifecycle_policy.data.id
}

output "alarm_name" {
  description = "The status-check alarm, red only while the host runs and fails."
  value       = aws_cloudwatch_metric_alarm.health.alarm_name
}

output "saml_enabled" {
  description = "Whether the rendered gitlab.rb carries the SAML block (step 3.2) - false until saml.auto.tfvars exists."
  value       = local.saml_enabled
}
