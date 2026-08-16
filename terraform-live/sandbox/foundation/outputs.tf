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
  description = "THE INT-05 ANCHOR (step 3.2) - what Stage 5's bucket policies condition on."
  value       = module.vpc.s3_gateway_endpoint_id
}

output "dynamodb_gateway_endpoint_id" {
  description = "The DynamoDB gateway endpoint id."
  value       = module.vpc.dynamodb_gateway_endpoint_id
}

output "public_subnet_ids" {
  description = "Public subnets by zone id - Stage 4's WireGuard host lands in one."
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnets by zone id - Studio apps (Stage 6), EFS mounts (Stage 5)."
  value       = module.vpc.private_subnet_ids
}

output "isolated_subnet_ids" {
  description = "Isolated subnets by zone id - empty on purpose (step 1.4)."
  value       = module.vpc.isolated_subnet_ids
}

output "public_route_table_id" {
  description = "Where step 6.3's tunnel route toward GitLab lands (pass 2)."
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

output "sandbox_internal_zone_id" {
  description = "The sandbox.internal hosted zone id."
  value       = aws_route53_zone.sandbox_internal.zone_id
}
