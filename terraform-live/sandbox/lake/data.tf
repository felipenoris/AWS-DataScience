# What this slice reads and does not own.
#
# The lookups, none of them crossing an account boundary:
#
#   1. this account's identity + partition -> the Access Grants instance ARN the trust pins, and
#                                             the account id the grants are addressed to. Both are
#                                             built, never pasted (aws/INDEX.md 1)
#   2. alias/awsds-<env>-data              -> the account data CMK, decision 1(a). By alias: the
#                                             alias is the contract GOVERNANCE.md writes down, the
#                                             key id is not
#   3. one reserved role per tenant        -> the grantees of pass 3, by pattern. This is what makes
#                                             var.tenants self-verifying: one() fails the plan on a
#                                             permission set that is not provisioned in this account
#   4. the Access Grants instance          -> not read and not declared; its ARN is built, in
#                                             iam.tf. It is SMUS-born (2026-08-22) and the service
#                                             keeps writing to it, so adopting it would put
#                                             Terraform in a race with its author (Lesson 17). The
#                                             provider offers no data source - measured against
#                                             hashicorp/aws v6.61.0, 2026-08-26: only the managed
#                                             resource exists, and `terraform validate` says so by
#                                             name

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# --------------------------------------------------------------- the account data CMK (D31)
#
# GOVERNANCE.md §Encryption: every data bucket encrypts under the data CMK of the account it lives
# in. Naming the key here grants nothing on its own, because the key policy carries no
# delegate-to-IAM statement: measured 2026-08-26, its two statements are the account's administrative
# actions and the persona's ViaService use, and neither hands kms:Decrypt to IAM. Pass 2.2 is the
# other half.

data "aws_kms_alias" "data" {
  name = "alias/awsds-${var.env}-data"
}

# ------------------------------------------------------------------- the tenants' grantees
#
# The AWSReservedSSO_* suffix is minted per account (1c decision 7), so the ARN cannot be written
# down and the role is matched by pattern. one() asserts exactly one match: zero means the permission
# set is not provisioned here (an invented tenant), two means the pattern went stale.

data "aws_iam_roles" "tenant" {
  for_each = var.tenants

  name_regex  = "AWSReservedSSO_${each.value}_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
