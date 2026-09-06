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

# ------------------------------------------------------- NO_PROXY (6c step 5.6, 2026-09-06)
#
# THE ONE OUTPUT OF THIS SLICE THAT IS MEANT TO BE CONSUMED, and the exception that proves the
# warning above: it is not an id. It is the list of names a client in THIS VPC must NOT send to
# the proxy, generated in the module from the very services this slice declares - so it cannot
# disagree with the endpoints that were built, and it changes in the same apply they do.
#
# READ IT THROUGH terraform_remote_state, NEVER BY TRANSCRIPTION (Lesson 3). Eight of the names in
# it are not derivable from the service token - `ecr.dkr` alone resolves as `*.dkr.ecr.<region>...`
# - so a copied list is wrong for the estate's busiest path and wrong silently, since a bypass
# entry that matches nothing merely sends the call to Squid.
#
# WHAT MAY NOT CONSUME IT: `images/base`. Every application image inherits from that one and runs
# as a Production job behind endpoints, so an `ENV HTTP_PROXY`/`ENV NO_PROXY` baked there would
# travel into a VPC whose list is different - and a wrong entry sends S3 and STS out through the
# proxy as public calls, past every `aws:SourceVpc` condition. Build time is a BuildKit
# `--build-arg`; run time is `ContainerEnvironmentVariables` on the app image configuration, or a
# JupyterLab lifecycle configuration, which for a SMUS domain must be attached in the console.

output "no_proxy" {
  description = "The literal NO_PROXY value for a client inside this VPC - comma-joined, no wildcard, no CIDR, no port."
  value       = module.egress.no_proxy
}

output "no_proxy_entries" {
  description = "The same list, one entry per element - for a consumer that renders its own separator."
  value       = module.egress.no_proxy_entries
}
