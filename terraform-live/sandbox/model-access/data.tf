# What this slice reads and does not own.
#
#   1. the domain's governance/   the domain ARN, whose account segment is the domain account: the
#                                 provisioning role's name carries it, and both trust policies name
#                                 it as aws:SourceAccount. Read rather than pasted (aws/INDEX.md rule 1)
#   2. this account's sagemaker/  the D13 boundary, project_boundary_arn, which both roles carry
#
# The first crosses an account boundary, so its profile arrives keyed by account folder from the
# generated tfvars, as sandbox/sagemaker/'s does; a profile literal never sits in a .tf file.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "governance" {
  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.domain : v.env])}-tfstate"
    key     = "data-governance/governance/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.domain : v.profile])
  }
}

data "terraform_remote_state" "sagemaker" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/sagemaker/terraform.tfstate"
    region = var.region
  }
}
