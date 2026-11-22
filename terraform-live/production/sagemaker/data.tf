# What this slice reads and does not own.
#
# Each lookup keeps an identifier out of a tracked file:
#
#   1. this account's identity and partition -> every ARN this slice builds
#   2. the Sandbox identity (aliased)         -> the account the read-status statement names
#   3. foundation/'s state                    -> the two deploy roles the package groups name, and
#                                                the alerts topic the debug alarm and the
#                                                approval rule publish to
#   4. registry/'s state                      -> the application repository the job role pulls
#   5. data-governance/data/'s state          -> the drop-box, its prefix and the lake data key
#   6. the production persona, by pattern     -> the only principal the debug role trusts
#   7. production/data/'s state               -> the account data key's ARN, for the job log groups
#
# From production/data/ the slice reads that ARN alone: its buckets and its key name this slice's
# job role, so the role is applied first (Stage 9's pass 1 before pass 3), and the bucket and alias
# names below are the contracts ./aws/deploytargets.py reads.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "registry" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/registry/terraform.tfstate"
    region = var.region
  }
}

# The account data key's ARN, the key the job log groups are encrypted under (job-role.tf). The null
# default is what a first build reads: the role precedes production/data/, whose Lake Formation grants
# name it, so the groups carry the AWS-owned key until the apply after data/'s, and DT-12 reads the key
# each group carries.
data "terraform_remote_state" "data" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/data/terraform.tfstate"
    region = var.region
  }

  defaults = {
    data_key_arn = null
  }
}

# Cross-account, so the profile rides in the config, the idiom of sandbox/data/: a lake that has
# not been applied fails by name here instead of resolving to nothing three resources later.
data "terraform_remote_state" "lake" {
  backend = "s3"

  config = {
    bucket  = "awsds-${var.lake["data-governance"].env}-tfstate"
    key     = "data-governance/data/terraform.tfstate"
    region  = var.region
    profile = var.lake["data-governance"].profile
  }
}

# The AWSReservedSSO_* suffix is minted per account (1c decision 7), so the ARN cannot be written
# down and the role is matched by pattern. one() in debug.tf asserts exactly one match: zero means
# DataScientistProdAccess is not provisioned here, two means the pattern went stale.
data "aws_iam_roles" "data_scientist_prod" {
  name_regex  = "AWSReservedSSO_DataScientistProdAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
