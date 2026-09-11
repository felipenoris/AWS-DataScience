# What this slice reads and does not own.
#
# The account id, for the inference-profile ARNs. An inference profile is an ACCOUNT resource even
# when AWS defines it (`type: SYSTEM_DEFINED`), so its ARN carries the account segment and cannot
# be a literal in a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "current" {}

# Each project role, read rather than assumed. Two things come from it:
#
#   - A MISSING PROJECT FAILS AT PLAN with "no IAM role found", naming the role, instead of at
#     apply with a NoSuchEntity from the attachment. The list in project_roles is hand-written
#     after a project is created, so a typo is the expected error and it should be legible.
#   - THE BOUNDARY IS CHECKED (main.tf's precondition). A role that is not under
#     awsds-sandbox-project-boundary is not a project role this estate governs, whatever its name
#     looks like, and granting Bedrock to it would put the invocation outside D13 - which is the
#     exact property decision 8 chose this option to keep.
data "aws_iam_role" "project" {
  for_each = toset(var.project_roles)
  name     = each.value
}

locals {
  # The two ARN groups the grant needs, built from one map so they cannot disagree.
  #
  # The profile ARN is account- and region-scoped. The foundation-model ARN carries NO ACCOUNT (a
  # foundation model is not an account resource) and NO REGION on purpose: each us. profile routes
  # to us-east-1, us-east-2 and us-west-2 (Stage 6e step 0.2), so a region-pinned ARN would
  # authorize a third of the requests and refuse the rest, intermittently and by geography.
  profile_arns = [
    for model, profile in var.models :
    "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:inference-profile/${profile}"
  ]

  foundation_model_arns = [
    for model, profile in var.models :
    "arn:aws:bedrock:*::foundation-model/${model}"
  ]

  boundary_name = "awsds-${var.env}-project-boundary"
}
