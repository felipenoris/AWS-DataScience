# Outputs - readings for the Validation's before/after diff, not anchors: everything in this slice
# is [E] and new on every make up (step 8.6, Lesson 3, INT-05). The ids other slices may name are
# foundation/'s.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - expected all new after a make down/up cycle."
  value       = module.egress.interface_endpoint_ids
}

# `nat_gateway_id` and `nat_public_ip` went with the NAT itself at `vpc-egress-v0.6.0` (6c step
# 5.1), consumed by nothing across terraform-live/, aws/, scripts/ and docs/. The address the
# internet now sees for this estate is the proxy's, a [P] output of `production/networking/`: it
# survives `make down`, so unlike these two it can be named by a condition, which is what 4.12 does.

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
# public calls, past every `aws:SourceVpc` condition.
#
# `images/dev-env` does consume it, since 6d decision 8 (2026-09-10): that image runs in exactly one
# account, and both API-side mechanisms were measured unable to carry the value -
# ContainerEnvironmentVariables caps each value at 256 characters, and a lifecycle configuration
# cannot be updated in place. It arrives there as a `--build-arg`, never transcribed, and the image
# is therefore stale the moment this list changes: docs/plan/runbooks/dev-env.md E owns that chain.

output "no_proxy" {
  description = "The literal NO_PROXY value for a client inside this VPC - comma-joined, no wildcard, no CIDR, no port."
  value       = module.egress.no_proxy
}

output "no_proxy_entries" {
  description = "The same list, one entry per element - for a consumer that renders its own separator."
  value       = module.egress.no_proxy_entries
}
