# What this slice reads and does not own. Two remote states and one AMI parameter.
#
# BOTH READS ARE SAME-ACCOUNT, so neither carries a profile: the backend the caller inits
# against is already this account's, and a profile literal in a .tf file is the thing pass 2
# forbade (Lesson 14).

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# THE [E] SLICE THIS ONE NOW HANGS OFF, AND IT REPLACES A ROUTE WITH TWO SEPARATE NEEDS
# (6c step 5.8, 2026-09-06). Until the move this slice read `vpn/` for one thing: an ENI to
# point a default route at. There is no default route anywhere in the estate now (D38), so what
# it reads instead is `egress/` - VPC-SharedServices' interface endpoints - for two reasons that
# arrive together and are worth keeping apart:
#
#   1. THE SHELL. Session Manager reaches this host through the `ssm`, `ssmmessages` and
#      `ec2messages` endpoints that step 5.5 put in this VPC one step ahead of this host. It is
#      the reason those three are there, and it is why this dependency is HARD rather than
#      convenient: without them there is no way in at all. That is also why they must not be
#      proxied, which `no_proxy` below is what guarantees.
#   2. THE BYPASS LIST. `no_proxy` is generated (5.6) from the very services this VPC declares,
#      so it cannot disagree with the endpoints that exist. Eight of its names are not derivable
#      from a service token - `ecr.dkr` alone answers on `*.dkr.ecr.<region>.amazonaws.com` - so
#      a transcribed list would be wrong for the busiest path a BUILD host takes, and wrong
#      silently: an entry that matches nothing merely sends the pull to Squid.
#
# A DESTROYED `egress/` MAKES THIS AN ERROR RATHER THAN A MYSTERY, which is the right shape:
# reading an output of a slice that is down fails the plan by name. The rank in
# scripts/tfhygiene/layers.py records the order and the helper script enforces it, because a
# rank is not a control (Lesson 5).
data "terraform_remote_state" "egress" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/egress/terraform.tfstate"
    region = var.region
  }
}

# THE HUB, for one value: the proxy's name is a record in a zone this VPC is associated with, but
# the PORT and the fact that a proxy is the only way out are this estate's convention rather than
# something the host can discover. The address itself is never pasted - `proxy.awsds.internal`
# resolves through the apex zone (2.1), and the record moved with the host at 4.8's repair.

# THE AMI IS x86_64, AND IT IS THE POINT OF THE SLICE. The sagemaker-distribution base the
# dev-env image is built FROM publishes `-cpu` and `-gpu` tags and no arm64 variant at all
# (measured 2026-08-21 from the public registry's tag list), and SMUS spaces run on x86
# instance types - so an arm64 builder would either fail or produce an image no space can
# run. sandbox/probes/ stays on Graviton for the opposite reason: nothing it measures is
# architecture-specific.
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

data "aws_partition" "current" {}

locals {
  zone = var.zone_ids[var.zone_index]

  # THE PROXY, AS EVERY CLIENT ON THIS HOST HAS TO BE TOLD ABOUT IT. A name rather than an
  # address (4.8's record), and the private one: a spoke reaches 3128 over a PEERING, and a
  # peering carries the private address only - the Elastic IP would resolve perfectly and time
  # out with no message (Lesson 44).
  proxy_url = "http://proxy.awsds.internal:3128"

  # GENERATED, NEVER TRANSCRIBED (5.6). This is the list of names that must NOT go to the proxy,
  # and getting it wrong is silent in both directions: too short and an endpoint call is proxied
  # into a 403, too long and a service with no endpoint has no path at all.
  no_proxy = data.terraform_remote_state.egress.outputs.no_proxy
}
