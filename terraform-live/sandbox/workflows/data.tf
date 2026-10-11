# What this slice reads and does not own.
#
# The account id, for the processing-job ARN pattern: a SageMaker job ARN carries the account
# segment, which cannot be a literal in a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "current" {}

# Each project role, read rather than assumed: a missing project fails at plan, naming the role,
# and main.tf's precondition reads the role's permissions boundary. The roles are the service's,
# minted when a project is created in the portal.
data "aws_iam_role" "project" {
  for_each = toset(var.project_roles)
  name     = each.value
}

locals {
  processing_jobs = "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"

  boundary_name = "awsds-${var.env}-project-boundary"
}
