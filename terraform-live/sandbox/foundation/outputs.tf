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
  description = "Private subnets by zone id - Studio apps (Stage 6)."
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

# ------------------------------------------------------- Stage 4 step 2, the VPN anchors
#
# Four outputs, four different readers, none of them in this slice: sandbox/vpn/ associates
# the address, attaches the group and hands the secret's ARN to the host's boot fetch,
# identity/sso/ names the public IP in step 8's deny (the repository's first cross-account
# remote-state read), and Stage 7 admits the group id from another account entirely.
# Everything here survives make down by construction.

output "wireguard_eip_allocation_id" {
  description = "The [P] Elastic IP allocation - sandbox/vpn/ associates it with the [D] host."
  value       = aws_eip.wireguard.allocation_id
}

output "wireguard_eip_public_ip" {
  description = "THE ADDRESS STEP 8 PINS THE WHOLE CONTROL PLANE TO, and a branch of Stage 5 step 1.3's bucket policy (INT-05). Read by identity/sso/ through terraform_remote_state, never pasted: pasted, it would be a copy that nothing keeps in step with a reallocation, and the failure mode is every persona denied every API call."
  value       = aws_eip.wireguard.public_ip
}

output "wireguard_security_group_id" {
  description = "The [P] WireGuard security group. Admitted BY ID from Production (Stage 7's GitLab) - never the client CIDR, which the instance SNATs away (step 1.2)."
  value       = aws_security_group.wireguard.id
}

output "wireguard_host_key_secret_arn" {
  description = "The [P] host-key secret container (step 2.2a; decision 4, third review). sandbox/vpn/ passes it into the module, which grants its instance role GetSecretValue on exactly this ARN and hands it to the boot fetch. The VALUE never crosses Terraform: written by the user at enrollment (step 4.3), read by the host at first boot."
  value       = aws_secretsmanager_secret.wireguard_host_key.arn
}
