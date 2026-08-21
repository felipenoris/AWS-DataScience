# What this slice reads and does not own.
#
# THREE READS, TWO OF THEM CROSS-ACCOUNT:
#
#   1. this account's foundation/     the VPC, the private subnets by ZONE ID, the endpoint
#                                     security group - what the blueprint configuration is
#                                     pointed at (step 1.4: read through terraform_remote_state,
#                                     never pasted)
#   2. the LAKE's data/               the registered bucket ARNs, the drop-box prefix and the
#                                     lake data key - the three values D13's boundary is built
#                                     from. A bucket renamed on the producer side becomes a
#                                     plan diff here rather than a deny that stops matching
#   3. the DOMAIN's governance/       the domain id, on the second apply only. count-gated:
#                                     before pass 2 the state does not exist, and an
#                                     unconditional read would fail every pass-1 plan
#
# THE SECOND AND THIRD CROSS AN ACCOUNT BOUNDARY, so - unlike a same-account read - each needs
# a PROFILE in the data source's config, and a profile literal never sits in a .tf file
# (Lesson 14): both arrive keyed by account folder from the generated tfvars.

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "lake" {
  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.lake : v.env])}-tfstate"
    key     = "data-governance/data/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.lake : v.profile])
  }
}

data "terraform_remote_state" "governance" {
  count = var.blueprints_enabled ? 1 : 0

  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.domain : v.env])}-tfstate"
    key     = "data-governance/governance/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.domain : v.profile])
  }
}
