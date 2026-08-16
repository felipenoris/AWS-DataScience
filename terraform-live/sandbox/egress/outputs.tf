# Outputs - readings for the Validation's before/after diff, NOT anchors: everything in
# this slice is [E] and new on every make up (step 8.6, Lesson 3, INT-05). The ids other
# slices may name are foundation/'s.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - expected ALL NEW after a make down/up cycle."
  value       = module.egress.interface_endpoint_ids
}

output "nat_gateway_id" {
  description = "The NAT's id under design A, null under B - [E], anchors nothing."
  value       = module.egress.nat_gateway_id
}

output "nat_public_ip" {
  description = "What the internet sees while design A egress exists - released with the slice."
  value       = module.egress.nat_public_ip
}
