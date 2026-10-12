# Outputs - readings for the Validation's before/after diff, not anchors: everything in this slice
# is [E] and new on every make up (step 8.6, Lesson 3, INT-05). The ids other slices may name are
# foundation/'s.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - expected all new after a make down/up cycle."
  value       = module.egress.interface_endpoint_ids
}

# `nat_gateway_id` and `nat_public_ip` went with the NAT itself at `vpc-egress-v0.6.0` (6c step
# 5.1), consumed by nothing across terraform-live/, aws/, scripts/ and docs/. The address the
# internet sees for this estate is the proxy's, a [P] output of `production/networking/` that
# survives `make down`. No policy names it (D39).

# ------------------------------------------------------------------- NO_PROXY (6c step 5.6)
#
# The one output of this slice meant to be consumed, and the one that is not an id: the list of
# names a client in this VPC must not send to the proxy, generated in the module from the services
# this slice declares, so it cannot disagree with the endpoints that were built and it changes in
# the same apply they do.
#
# Read it through terraform_remote_state, never by transcription (Lesson 3). Eight of the names in
# it are not derivable from the service token - `ecr.dkr` alone resolves as `*.dkr.ecr.<region>...`
# - so a copied list is wrong for the estate's busiest path, and wrong silently, since a bypass
# entry that matches nothing merely sends the call to Squid.
#
# `images/base` may not consume it. Every application image inherits from that one and runs as a
# Production job behind endpoints, so an `ENV HTTP_PROXY`/`ENV NO_PROXY` baked there would travel
# into a VPC whose list is different, and a wrong entry sends S3 and STS out through the proxy as
# public calls, past every `aws:SourceVpc` condition. Build time is a BuildKit `--build-arg`; run
# time is `ContainerEnvironmentVariables` on the app image configuration, or a JupyterLab lifecycle
# configuration, which for a SMUS domain must be attached in the console.

output "no_proxy" {
  description = "The literal NO_PROXY value for a client inside this VPC - comma-joined, no wildcard, no CIDR, no port."
  value       = module.egress.no_proxy
}

output "no_proxy_entries" {
  description = "The same list, one entry per element - for a consumer that renders its own separator."
  value       = module.egress.no_proxy_entries
}

# The third output, re-exported since Stage 7 step 1.7 (2026-10-12): every optional group's names,
# the list a client that outlives this [E] slice has to carry. In this VPC that client is the GitLab
# host: production/tooling/ is [D] and cannot read a destroyed slice's output, so its `no_proxy`
# variable carries a DATED COPY of this value, and ./aws/supplychain.py SC-11 compares the two in
# both directions. Known at plan time, from the endpoint-service catalog, whether or not the
# endpoints exist.
output "no_proxy_all_groups" {
  description = "NO_PROXY with every optional endpoint group's names, whatever GROUPS= this apply named - the literal production/tooling/'s no_proxy variable copies (Stage 7 step 1.3), and the one ./aws/supplychain.py SC-11 compares it with."
  value       = module.egress.no_proxy_all_groups
}
