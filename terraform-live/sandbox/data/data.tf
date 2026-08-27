# What this slice reads and does not own.
#
# THREE LOOKUPS, EACH KEEPING AN IDENTIFIER OUT OF A TRACKED FILE:
#
#   1. The lake account's identity (aliased)       -> the catalog id every resource link and
#                                                     re-grant is addressed to
#   2. data-governance/data/'s state               -> the shared database NAMES, so a rename on
#                                                     the producer side is a plan diff here
#                                                     rather than a link that resolves nothing
#   3. Two permission-set roles, BY PATTERN        -> the data lake administrator and the
#                                                     persona the share is re-granted to
#
#   4. THIS ACCOUNT'S OWN identity and partition -> added 2026-08-26, and the sentence they
#                                                   replaced said they never would be. It was
#                                                   true while every ARN this slice built was
#                                                   built inside the module; the key-policy
#                                                   statement in main.tf is the first one built
#                                                   HERE, so the premise expired rather than
#                                                   the rule. Development's copy of this slice
#                                                   passes no such statement and therefore
#                                                   declares neither - which is why they are in
#                                                   the Sandbox file and not in a shared one

data "aws_caller_identity" "lake" {
  provider = aws.lake
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# ------------------------------------------------------------------ the lake's own state
#
# Cross-account, so the profile rides in the config - the same idiom data-governance/data/ uses
# in the opposite direction, and the same failure mode: a lake that has not been applied fails
# BY NAME here instead of resolving to nothing three resources later. What the read needs beyond
# S3 is kms:Decrypt on that account's alias/awsds-data-tfstate key; the profile is that account's
# InfrastructureAccess, which holds it.

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
# BY PATTERN, NEVER PASTED: the AWSReservedSSO_* suffix is minted per account (1c decision 7),
# so the ARN cannot be written down. one() in main.tf asserts exactly one match - zero means the
# permission set is not provisioned here, two means the pattern went stale; both must fail by
# name rather than index into nothing.

data "aws_iam_roles" "infrastructure_access" {
  name_regex  = "AWSReservedSSO_InfrastructureAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

# ------------------------------------------------------------------- the persona (D18)
#
# The principal the share is re-granted to (the LF re-grants in the consumer-data module)
# (D31). Provisioned in BOTH Interactive accounts by identity/sso/'s DataScientistAccess
# assignment (D21).

data "aws_iam_roles" "data_scientist" {
  name_regex  = "AWSReservedSSO_DataScientistAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
