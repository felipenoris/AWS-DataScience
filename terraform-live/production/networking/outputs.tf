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
  description = "The INT-05 anchor (step 3.2) - what Stage 5's bucket policies condition on."
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

# No zone outputs (Stage 6c step 1.2). production/foundation/ owns the awsds.internal apex and
# awsds-pages.internal; this VPC is associated into zones it does not own (step 2.5), and an
# association produces nothing for a caller to read.

# ------------------------------------------------- Stage 6c step 4.1, the hub's [P] anchors
#
# These carry the same output names sandbox/foundation/ exports for the VPN, so flipping
# VPN_HOMES at 4.12 changes an address and not a shape: identity/sso/ and data-governance/data/
# read a home's slice by key and must find the same keys here.
#
# `wireguard_eip_public_ip` is backed by an allocation transferred from Sandbox (4.5) and imported
# (4.6), never allocated here. Allocating one would produce a second address and a re-issue of
# every .conf, the fallback in the stage's risk table.

output "wireguard_security_group_id" {
  description = "The [P] WireGuard security group - production/vpn/ attaches it to the [D] host."
  value       = aws_security_group.wireguard.id
}

output "wireguard_host_key_secret_arn" {
  description = "The [P] host-key container. production/vpn/ passes it into the wireguard module, which grants its instance role GetSecretValue on exactly this ARN. The value is copied in by the user at 4.3 and never crosses Terraform."
  value       = aws_secretsmanager_secret.wireguard_host_key.arn
}

output "proxy_eip_public_ip" {
  description = "The address 4.12 re-keys the whole control plane onto. A VPN client's internet now crosses Squid, so every VPN-only condition that named the WireGuard EIP names this instead. Read through terraform_remote_state, never pasted."
  value       = aws_eip.proxy.public_ip
}

output "proxy_eip_allocation_id" {
  description = "The [P] proxy allocation - production/proxy/ associates it with the [D] host."
  value       = aws_eip.proxy.allocation_id
}

output "proxy_security_group_id" {
  description = "The [P] proxy security group. Admits TCP/3128 from every peered spoke and the tunnel; the policy that decides what those sources may reach is the allow-list, not this group."
  value       = aws_security_group.proxy.id
}

output "proxy_allowlist_parameter_name" {
  description = "The SSM parameter holding Squid's source-scoped allow-lists (4.9/4.10). production/proxy/ renders it at boot; ./aws/proxy.py diffs running against committed."
  value       = aws_ssm_parameter.proxy_allowlist.name
}

output "proxy_access_log_group_name" {
  description = "The [P] Squid access log (4.11) - Stage 11's egress evidence. The [D] proxy writes here and does not own it: a record that dies with the host it describes is not a record."
  value       = aws_cloudwatch_log_group.proxy_access.name
}

output "proxy_access_log_group_arn" {
  description = "The same group's ARN - the proxy's role is scoped to exactly this one, with no delete."
  value       = aws_cloudwatch_log_group.proxy_access.arn
}

output "wireguard_eip_allocation_id" {
  description = "The [P] Elastic IP allocation - production/vpn/ associates it with the [D] host. Not the id it had in Sandbox: a transfer mints a new one (measured 2026-09-06, the stage's verification 1)."
  value       = aws_eip.wireguard.allocation_id
}

output "wireguard_eip_public_ip" {
  description = "The address every client .conf pins, and the one thing the account move does not change. Read by identity/sso/ and data-governance/data/ through terraform_remote_state once VPN_HOMES flips at 4.12 - never pasted, because a paste is a copy nothing keeps in step and the failure mode is every persona denied every API call."
  value       = aws_eip.wireguard.public_ip
}
