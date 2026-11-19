# What this slice reads and does not own.
#
# The account id, for the model package group ARN pattern: the ARN carries the account segment,
# which cannot be a literal in a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# Each project role, read rather than assumed: a missing project fails at plan, naming the role,
# and main.tf's precondition reads the role's permissions boundary. The roles are the service's,
# minted when a project is created in the portal.
data "aws_iam_role" "project" {
  for_each = toset(var.project_roles)
  name     = each.value
}

locals {
  model_package_groups = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model-package-group/*"

  boundary_name = "awsds-${var.env}-project-boundary"
}
