# Outputs - what other slices read through terraform_remote_state (never pasted).

output "vpc_id" {
  description = "This unit's VPC - the aws:SourceVpc anchor (step 3.3)."
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "The VPC CIDR."
  value       = module.vpc.vpc_cidr
}

output "s3_gateway_endpoint_id" {
  description = "The INT-05 anchor (step 3.2) - what Stage 5a's bucket policies condition on."
  value       = module.vpc.s3_gateway_endpoint_id
}

output "dynamodb_gateway_endpoint_id" {
  description = "The DynamoDB gateway endpoint id."
  value       = module.vpc.dynamodb_gateway_endpoint_id
}

output "public_subnet_ids" {
  description = "Public subnets by zone id - design A's NAT lands here (step 7); GitLab does not (it is private, Stage 7)."
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnets by zone id - GitLab, runners, jobs (Stage 7-9)."
  value       = module.vpc.private_subnet_ids
}

output "isolated_subnet_ids" {
  description = "Isolated subnets by zone id - empty on purpose (step 1.4)."
  value       = module.vpc.isolated_subnet_ids
}

output "public_route_table_id" {
  description = "The public tier's route table."
  value       = module.vpc.public_route_table_id
}

output "private_route_table_ids" {
  description = "Where egress/ inserts design A's default route, and where step 6.3's return routes land (pass 2)."
  value       = module.vpc.private_route_table_ids
}

output "isolated_route_table_id" {
  description = "The isolated tier's route table."
  value       = module.vpc.isolated_route_table_id
}

output "endpoints_security_group_id" {
  description = "The endpoint SG (step 2.4) - egress/ attaches it to every interface endpoint."
  value       = module.vpc.endpoints_security_group_id
}

output "tier_security_group_ids" {
  description = "Baseline tier SGs."
  value       = module.vpc.tier_security_group_ids
}

# Stage 6c pass 2 - read by every slice that associates a VPC into these zones, and by 2.5's
# authorizations. `production/probes/`'s two `[E]` records live in the apex, and the apex is what a
# spoke associates with, so this is the only zone id that crosses an account boundary from here.
output "awsds_internal_zone_id" {
  description = "The awsds.internal apex - the shared names, associated into all five VPCs (INT-22)."
  value       = aws_route53_zone.awsds_internal.zone_id
}

output "awsds_pages_internal_zone_id" {
  description = "The awsds-pages.internal apex - a separate registrable parent, by decision (D36)."
  value       = aws_route53_zone.awsds_pages_internal.zone_id
}

# Stage 7 step 1.1 - GitLab's [P] anchors, read by production/tooling/, production/pki/ and
# production/runners/ through terraform_remote_state.
output "gitlab_key_arn" {
  description = "The CMK under GitLab's two buckets and its data volume (alias/awsds-<env>-gitlab)."
  value       = module.gitlab_key.key_arn
}

output "gitlab_objects_bucket" {
  description = "GitLab's object storage, one prefix per object type; also config/gitlab.rb and the published certificates under pki/."
  value       = module.gitlab_objects.bucket_name
}

output "gitlab_objects_bucket_arn" {
  description = "The same bucket's ARN - what the host role's S3 statements name."
  value       = module.gitlab_objects.bucket_arn
}

output "gitlab_backup_bucket" {
  description = "gitlab-backup's upload target; every object expires after 30 days."
  value       = module.gitlab_backup.bucket_name
}

output "gitlab_backup_bucket_arn" {
  description = "The backup bucket's ARN."
  value       = module.gitlab_backup.bucket_arn
}

output "gitlab_secrets_secret_arn" {
  description = "The gitlab-secrets.json container. The host's first boot restores from it or pushes into it (1.5); the value never crosses Terraform."
  value       = aws_secretsmanager_secret.gitlab_secrets.arn
}

output "runner_token_secret_arn" {
  description = "The runner authentication token's container - the user copies the token in once the runner exists in GitLab (6.1)."
  value       = aws_secretsmanager_secret.runner_token.arn
}

output "test_runner_token_secret_arn" {
  description = "The test runner's authentication token container (Stage 8 decision 11) - the user copies the token in once the runner exists in GitLab."
  value       = aws_secretsmanager_secret.test_runner_token.arn
}

# Stage 8 step 4 - the deploy runner's anchors, read by production/runners/ through
# terraform_remote_state, and the alerts topic later stages adopt (decision 5).
output "deploy_runner_role_arn" {
  description = "The deploy runner's role, awsds-<env>-runner-deploy - the one principal every deploy role trusts."
  value       = module.deploy_runner_role.role_arn
}

output "deploy_role_arns" {
  description = "Each account's own deploy role, keyed by the account folder it lives in - the promotion roles production/sagemaker/ names."
  value       = local.deploy_role_arn_by_account
}

output "deploy_role_arns_by_name" {
  description = "Every deploy role the runner's role may assume, keyed by role name: each account's own and the roles a target's other slices hold (Stage 8 decision 19) - what production/runners/ renders the deploy runner's AWS profiles from."
  value       = local.deploy_role_arn_by_name
}

output "deploy_runner_instance_profile_name" {
  description = "The deploy runner's instance profile - the machine credential production/runners/ attaches (principle 2)."
  value       = aws_iam_instance_profile.deploy_runner.name
}

output "deploy_runner_token_secret_arn" {
  description = "The container of the deploy runner's authentication token (Stage 8 step 4.5)."
  value       = aws_secretsmanager_secret.deploy_runner_token.arn
}

output "alerts_topic_arn" {
  description = "awsds-<env>-alerts - the misuse rule's target, adopted by Stage 9, Stage 10 and Stage 12 (Stage 8 decision 5)."
  value       = aws_sns_topic.alerts.arn
}
