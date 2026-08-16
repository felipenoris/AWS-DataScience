# Outputs - for the Validation's before/after diff, NOT for anchoring: everything this
# module creates is [E] and holds new ids on every make up (step 8.6, Lesson 3, INT-05). No
# policy, no condition, no other slice may name any id below. The [P] anchors live in
# foundation/: the gateway endpoint id and aws:SourceVpc.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - the ids the Validation expects to be ALL NEW after a make down/up cycle, which is exactly why nothing may reference them."
  value       = { for s, ep in aws_vpc_endpoint.interface : s => ep.id }
}

output "nat_gateway_id" {
  description = "The NAT's id under design A, null under B - same [E] warning as above."
  value       = var.egress_mode == "A" ? aws_nat_gateway.this[0].id : null
}

output "nat_public_ip" {
  description = "The NAT's public address - what the internet sees while design A egress exists. Recorded for reading, never for a rule: it is released with the slice."
  value       = var.egress_mode == "A" ? aws_eip.nat[0].public_ip : null
}
