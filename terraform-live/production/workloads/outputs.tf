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

# There are no outputs for the zones this slice does not own (Stage 6c step 1.2).
# production/foundation/ owns the awsds.internal apex and awsds-pages.internal; this VPC is
# associated into them, which is the opposite direction (step 2.5) and produces nothing for a
# caller to read.

# Stage 6c step 2.5 reads this from Production, to associate VPC-Networking after this account
# has authorized it. The authorization is written here; the association is not.
output "prod_awsds_internal_zone_id" {
  description = "prod.awsds.internal - associated with VPC-Workloads, VPC-SharedServices and VPC-Networking."
  value       = aws_route53_zone.prod_awsds_internal.zone_id
}
