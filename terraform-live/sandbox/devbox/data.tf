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

# THE [D] SLICE THIS ONE HANGS OFF, and the dependency is real rather than tidy: the route
# below points at the WireGuard host's ENI, so this slice cannot be applied before vpn/ has
# been, and the host must be RUNNING or the route is a blackhole rather than an error. The
# rank in scripts/tfhygiene/layers.py (vpn 40, devbox 55) is what records the order; the
# helper script is what enforces it, because a rank is not a control (Lesson 5).
data "terraform_remote_state" "vpn" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/vpn/terraform.tfstate"
    region = var.region
  }
}

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
}
