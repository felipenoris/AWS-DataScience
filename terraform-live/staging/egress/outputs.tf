# Outputs - readings for the Validation's before/after diff, NOT anchors: everything in
# this slice is [E] and new on every make up (step 8.6, Lesson 3, INT-05). The ids other
# slices may name are foundation/'s.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - expected ALL NEW after a make down/up cycle."
  value       = module.egress.interface_endpoint_ids
}

# `nat_gateway_id` AND `nat_public_ip` STOOD HERE UNTIL 6c step 5.1 (2026-09-06) and went with the
# NAT itself at `vpc-egress-v0.6.0`. Nothing consumed either - checked before removing, across
# terraform-live/, aws/, scripts/ and docs/ - which is what made this a deletion rather than a
# migration. **The address the internet now sees for this estate is the PROXY's**, and that one is
# a [P] output of `production/networking/`: it survives `make down`, so unlike these two it can be
# named by a condition, which is what 4.12 does.
