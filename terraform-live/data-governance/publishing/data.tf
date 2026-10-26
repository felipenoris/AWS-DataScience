# What this slice reads and does not own.
#
#   1. this account's identity          the flow-log role's confused-deputy guard and the domain
#                                       account the two service roles' trusts name
#   2. the lake's data/                 the registered bucket ARNs, the drop-box prefix and the lake
#                                       data key - the values D13's boundary is built from
#   3. the domain's governance/         on the second apply only: the domain id, the domain
#                                       execution role and the root domain unit. count-gated, as in
#                                       sandbox/sagemaker/, so the first apply plans without it

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

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
