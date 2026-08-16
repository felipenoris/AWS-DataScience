output "vpc_id" {
  description = "The VPC id - also the aws:SourceVpc anchor where a service has no gateway endpoint (step 3.3)."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "The VPC CIDR, echoed for cross-slice reads."
  value       = aws_vpc.this.cidr_block
}

output "s3_gateway_endpoint_id" {
  description = "THE INT-05 ANCHOR - the [P] id Stage 5's bucket policies condition on, read through terraform_remote_state, never pasted (step 3.2). The only endpoint id any policy may name (Lesson 3)."
  value       = aws_vpc_endpoint.s3.id
}

output "dynamodb_gateway_endpoint_id" {
  description = "The DynamoDB gateway endpoint id - same [P] class as the S3 one."
  value       = aws_vpc_endpoint.dynamodb.id
}

output "public_subnet_ids" {
  description = "Public subnet ids, keyed by zone id."
  value       = { for k, s in aws_subnet.public : k => s.id }
}

output "private_subnet_ids" {
  description = "Private subnet ids, keyed by zone id."
  value       = { for k, s in aws_subnet.private : k => s.id }
}

output "isolated_subnet_ids" {
  description = "Isolated subnet ids, keyed by zone id."
  value       = { for k, s in aws_subnet.isolated : k => s.id }
}

output "public_route_table_id" {
  description = "The public tier's route table - where step 6.3's tunnel route lands (Sandbox)."
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "Private route tables, keyed by zone id - where egress/ inserts design A's default route (step 2.2) and step 6.3's peering routes land."
  value       = { for k, rt in aws_route_table.private : k => rt.id }
}

output "isolated_route_table_id" {
  description = "The isolated tier's route table - carries the gateway endpoints and nothing else, ever."
  value       = aws_route_table.isolated.id
}

output "endpoints_security_group_id" {
  description = "The endpoint SG (step 2.4) - egress/ attaches it to every interface endpoint."
  value       = aws_security_group.endpoints.id
}

output "tier_security_group_ids" {
  description = "Baseline tier SGs (public/private/isolated), for the workloads later stages put there."
  value       = { for k, sg in aws_security_group.tier : k => sg.id }
}
