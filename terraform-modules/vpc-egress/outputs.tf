# Outputs - for the Validation's before/after diff, not for anchoring: everything this
# module creates is [E] and holds new ids on every make up (step 8.6, Lesson 3, INT-05). No
# policy, no condition, no other slice may name any id below. The [P] anchors live in
# foundation/: the gateway endpoint id and aws:SourceVpc.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - the ids the Validation expects to be all new after a make down/up cycle, which is exactly why nothing may reference them."
  value       = { for s, ep in aws_vpc_endpoint.interface : s => ep.id }
}

# No `nat_gateway_id` and no `nat_public_ip`: the NAT is gone (5.1). The address the internet sees
# for this estate is the proxy's, a [P] output of `production/networking/` - the difference D38
# bought, an egress address that survives `make down` and can therefore be named by a condition,
# which neither of those ever could.
