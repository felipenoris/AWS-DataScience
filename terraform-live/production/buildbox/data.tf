# What this slice reads and does not own: two remote states and one AMI parameter.
#
# Both reads are same-account, so neither carries a profile - the backend the caller inits against
# is already this account's, and a profile literal in a .tf file is forbidden (Lesson 14).

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# The [E] slice this one hangs off since the move (6c step 5.8, 2026-09-06). It used to read `vpn/`
# for an ENI to point a default route at; there is no default route anywhere in the estate now
# (D38), so it reads `egress/` - VPC-SharedServices' interface endpoints - for two things:
#
#   1. The shell. Session Manager reaches this host through the `ssm`, `ssmmessages` and
#      `ec2messages` endpoints that step 5.5 put in this VPC one step ahead of this host. Without
#      them there is no way in at all, which is why the dependency is hard rather than convenient,
#      and why those three must not be proxied.
#   2. The bypass list. `no_proxy` is generated (5.6) from the services this VPC declares, so it
#      cannot disagree with the endpoints that exist. Eight of its names are not derivable from a
#      service token - `ecr.dkr` alone answers on `*.dkr.ecr.<region>.amazonaws.com` - so a
#      transcribed list would be wrong for the busiest path a build host takes, and wrong silently:
#      an entry that matches nothing merely sends the pull to Squid.
#
# Reading an output of a destroyed `egress/` fails the plan by name. The rank in
# scripts/tfhygiene/layers.py records the order and ./scripts/buildbox.py enforces it, because a
# rank is not a control (Lesson 5).
data "terraform_remote_state" "egress" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/egress/terraform.tfstate"
    region = var.region
  }
}

# The AMI is x86_64, which is the point of the slice. The sagemaker-distribution base the dev-env
# image is built from publishes `-cpu` and `-gpu` tags and no arm64 variant at all (measured
# 2026-08-21 from the public registry's tag list), and SMUS spaces run on x86 instance types, so an
# arm64 builder would either fail or produce an image no space can run. sandbox/probes/ stays on
# Graviton because nothing it measures is architecture-specific.
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_partition" "current" {}

locals {
  zone = var.zone_ids[var.zone_index]

  # The proxy, as every client on this host has to be told about it. A name rather than an address
  # (the record moved with the host at 4.8's repair, and resolves through the apex zone, 2.1), and
  # the private one: a spoke reaches 3128 over a peering, and a peering carries the private address
  # only - the Elastic IP would resolve perfectly and time out with no message (Lesson 44). The
  # port, and the fact that a proxy is the only way out, are this estate's convention rather than
  # something the host can discover.
  proxy_url = "http://proxy.awsds.internal:3128"

  # Generated, never transcribed (5.6). The names that must not go to the proxy; getting the list
  # wrong is silent in both directions - too short and an endpoint call is proxied into a 403, too
  # long and a service with no endpoint has no path at all.
  no_proxy = data.terraform_remote_state.egress.outputs.no_proxy
}
