# What this slice reads and does not own.
#
# FOUR LOOKUPS, NONE OF THEM CROSSING AN ACCOUNT BOUNDARY:
#
#   1. this account's identity + partition -> the Access Grants instance ARN the trust pins,
#                                             and the account id the grants are addressed to.
#                                             Both are BUILT, never pasted (aws/INDEX.md 1)
#   2. alias/awsds-<env>-data              -> the account data CMK, decision 1(a). By ALIAS,
#                                             because the alias is the contract GOVERNANCE.md
#                                             writes down and the key id is not
#   3. one reserved role PER TENANT        -> the grantees of pass 3, by PATTERN. This is also
#                                             what makes var.tenants self-verifying: one()
#                                             fails the plan on a permission set that is not
#                                             provisioned in this account
#   4. the Access Grants INSTANCE          -> NOT read and NOT declared; its ARN is BUILT, in
#                                             iam.tf. It is SMUS-born (2026-08-22) and the
#                                             service keeps writing to it, so adopting it would
#                                             put Terraform in a race with its author (Lesson
#                                             17). A data source would have been the third way
#                                             and the provider has none - measured against
#                                             hashicorp/aws v6.61.0, 2026-08-26: only the
#                                             managed resource exists, and `terraform validate`
#                                             says so by name

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# --------------------------------------------------------------- the account data CMK (D31)
#
# GOVERNANCE.md §Encryption: every data bucket encrypts under the data CMK of the account it
# lives in. This bucket is the newest reader of that key, and - because the key policy carries
# no delegate-to-IAM statement (measured 2026-08-26: its two statements are the account's
# ADMINISTRATIVE actions and the persona's ViaService use, and neither hands kms:Decrypt to
# IAM) - naming it here grants nothing on its own. Pass 2.2 is the other half.

data "aws_kms_alias" "data" {
  name = "alias/awsds-${var.env}-data"
}

# ------------------------------------------------------------------- the tenants' grantees
#
# BY PATTERN, NEVER PASTED: the AWSReservedSSO_* suffix is minted per account (1c decision 7),
# so the ARN cannot be written down. one() asserts exactly one match - zero means the
# permission set is not provisioned here (an invented tenant), two means the pattern went
# stale; both must fail by name rather than index into nothing.

data "aws_iam_roles" "tenant" {
  for_each = var.tenants

  name_regex  = "AWSReservedSSO_${each.value}_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
