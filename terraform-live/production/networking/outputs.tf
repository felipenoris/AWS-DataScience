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

# NO ZONE OUTPUTS, AND THE ABSENCE IS THE DESIGN (Stage 6c step 1.2). production/foundation/
# owns prod.internal and pages.internal; this VPC is ASSOCIATED into zones it does not own,
# which is the opposite direction (step 2.5) and produces nothing for a caller to read.

# ------------------------------------------------- Stage 6c step 4.1, the hub's [P] anchors
#
# The same output NAMES sandbox/foundation/ exports for the VPN, so that flipping VPN_HOMES at
# 4.12 is a change of address and not a change of shape - identity/sso/ and
# data-governance/data/ read a home's slice by key and must find the same keys here.
#
# ONE OF THAT SET IS MISSING ON PURPOSE UNTIL 4.6: `wireguard_eip_public_ip`. The address is
# transferred from Sandbox rather than allocated (4.5), so the resource that backs that output
# arrives with the `import {}` block of 4.6, not with this file. Declaring the output first
# would mean allocating a second address, which is the fallback in the stage's risk table.

output "wireguard_security_group_id" {
  description = "The [P] WireGuard security group - production/vpn/ attaches it to the [D] host."
  value       = aws_security_group.wireguard.id
}

output "wireguard_host_key_secret_arn" {
  description = "The [P] host-key container. production/vpn/ passes it into the wireguard module, which grants its instance role GetSecretValue on exactly this ARN. The VALUE is copied in by the user at 4.3 and never crosses Terraform."
  value       = aws_secretsmanager_secret.wireguard_host_key.arn
}

output "proxy_eip_public_ip" {
  description = "THE ADDRESS 4.12 RE-KEYS THE WHOLE CONTROL PLANE ONTO. A VPN client's internet now crosses Squid, so every VPN-only condition that named the WireGuard EIP names this instead. Read through terraform_remote_state, never pasted."
  value       = aws_eip.proxy.public_ip
}

output "proxy_eip_allocation_id" {
  description = "The [P] proxy allocation - production/proxy/ associates it with the [D] host."
  value       = aws_eip.proxy.allocation_id
}

output "proxy_security_group_id" {
  description = "The [P] proxy security group. Admits TCP/3128 from every peered spoke and the tunnel; the policy that decides what those sources may REACH is the allow-list, not this group."
  value       = aws_security_group.proxy.id
}

output "proxy_allowlist_parameter_name" {
  description = "The SSM parameter holding Squid's source-scoped allow-lists (4.9/4.10). production/proxy/ renders it at boot; ./aws/proxy.py diffs running against committed."
  value       = aws_ssm_parameter.proxy_allowlist.name
}
