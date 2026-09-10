# Outputs - readings for the Validation's before/after diff, not anchors: everything in this slice
# is [E] and new on every make up (step 8.6, Lesson 3, INT-05). The ids other slices may name are
# foundation/'s.

output "interface_endpoint_ids" {
  description = "Endpoint id per service token - expected ALL NEW after a make down/up cycle."
  value       = module.egress.interface_endpoint_ids
}

# The address the internet sees for this estate is the proxy's, a [P] output of
# `production/networking/`. It survives `make down`, so unlike anything here it can be named by a
# condition, which is what 4.12 does.

# ------------------------------------------------------- NO_PROXY (6c step 5.6, 2026-09-06)
#
# The one output of this slice meant to be consumed, and the exception to the warning above: it is
# not an id. It is the list of names a client in this VPC must not send to the proxy, generated in
# the module from the services this slice declares, so it cannot disagree with the endpoints that
# were built and it changes in the same apply they do.
#
# Read it through terraform_remote_state, never by transcription (Lesson 3). Eight of its names are
# not derivable from the service token - `ecr.dkr` alone resolves as `*.dkr.ecr.<region>...` - so a
# copied list is wrong for the estate's busiest path and wrong silently, since a bypass entry that
# matches nothing merely sends the call to Squid.
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
