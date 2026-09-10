# What this slice reads and does not own.
#
# Each lookup keeps an identifier out of a tracked file:
#
#   1. the lake account's identity (aliased)     -> the catalog id every resource link and re-grant
#                                                   is addressed to
#   2. data-governance/data/'s state             -> the shared database names, so a rename on the
#                                                   producer side is a plan diff here rather than a
#                                                   link that resolves nothing
#   3. two permission-set roles, by pattern      -> the data lake administrator and the persona the
#                                                   share is re-granted to
#   4. this account's own identity and partition -> the key-policy statement in main.tf is the first
#                                                   ARN this slice builds outside the module. A
#                                                   consumer copy that passes no such statement
#                                                   declares neither, which is why they live here
#                                                   and not in a shared file

data "aws_caller_identity" "lake" {
  provider = aws.lake
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# ------------------------------------------------------------------ the lake's own state
#
# Cross-account, so the profile rides in the config - the same idiom data-governance/data/ uses in
# the opposite direction, and the same failure mode: a lake that has not been applied fails by name
# here instead of resolving to nothing three resources later. Beyond S3 the read needs kms:Decrypt
# on that account's alias/awsds-data-tfstate key; the profile is that account's InfrastructureAccess,
# which holds it.

data "terraform_remote_state" "lake" {
  backend = "s3"

  config = {
    bucket  = "awsds-${var.lake["data-governance"].env}-tfstate"
    key     = "data-governance/data/terraform.tfstate"
    region  = var.region
    profile = var.lake["data-governance"].profile
  }
}

# ------------------------------------------------- the data lake administrator (decision 5)
#
# The AWSReservedSSO_* suffix is minted per account (1c decision 7), so the ARN cannot be written
# down and the role is matched by pattern. one() in main.tf asserts exactly one match: zero means
# the permission set is not provisioned here, two means the pattern went stale.

data "aws_iam_roles" "infrastructure_access" {
  name_regex  = "AWSReservedSSO_InfrastructureAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

# ------------------------------------------------------------------- the persona (D18)
#
# The principal the share is re-granted to (the LF re-grants in the consumer-data module, D31).
# Provisioned in both Interactive accounts by identity/sso/'s DataScientistAccess assignment (D21).

data "aws_iam_roles" "data_scientist" {
  name_regex  = "AWSReservedSSO_DataScientistAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
