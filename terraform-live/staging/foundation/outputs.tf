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
  description = "Public subnets by zone id - nothing lands here today; design A's NAT does (step 7)."
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnets by zone id - Studio apps (Stage 6)."
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
  description = "Where egress/ inserts design A's default route (steps 2.2, 7, 10)."
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

# Stage 6c step 2.5 reads this from Production, to associate VPC-Networking after this account
# has authorized it. The authorization is written here; the association is not.
output "staging_awsds_internal_zone_id" {
  description = "staging.awsds.internal - associated with this VPC and with VPC-Networking (INT-22)."
  value       = aws_route53_zone.staging_awsds_internal.zone_id
}

# Stage 8 step 4 - the Staging leg's deploy role, and the alerts topic later stages adopt (decision 5).
output "deploy_role_arn" {
  description = "awsds-deploy-staging - assumed only by the deploy runner's role (INT-08)."
  value       = module.deploy_role.role_arn
}

output "alerts_topic_arn" {
  description = "awsds-<env>-alerts - the misuse rule's target, adopted by Stage 9, Stage 10 and Stage 12 (Stage 8 decision 5)."
  value       = aws_sns_topic.alerts.arn
}

# Stage 9 step 4.6 - Production's Model Registry, read from Staging as the deploy role (INT-07's
# registry half, verification xii): the group ARNs begin with this prefix, production/sagemaker/
# registry.tf's `awsds-<env>-model-<family>`, and scripts/model-chain.py appends the family. Built from
# the same locals as the deploy role's grant on those groups (deploy-role.tf), so no second copy of
# the registry's account or naming exists here.
output "registry_model_package_group_arn_prefix" {
  description = "The start of every Model Registry group ARN in Production (awsds-<env>-model-<family>), which the Staging deploy role reads approved versions from (Stage 9 4.6)."
  value       = "arn:${local.partition}:sagemaker:${data.aws_region.current.region}:${local.registry_account_id}:model-package-group/awsds-${local.registry_env}-model-"
}
