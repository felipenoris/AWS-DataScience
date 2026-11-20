# What this slice reads and does not own.
#
# The account id, for the SageMaker ARN patterns: the ARN carries the account segment,
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
  sagemaker_arn_prefix = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}"

  # One AddTags statement per resource type whose tagged create a measurement refused, by Sid (main.tf).
  tagged_resources = {
    TagAModelPackageGroupWithTheCallersProject = "model-package-group/*"
    TagAnEndpointConfigWithTheCallersProject   = "endpoint-config/*"
    TagAnEndpointWithTheCallersProject         = "endpoint/*"
    TagAPipelineWithTheCallersProject          = "pipeline/*"
  }

  boundary_name = "awsds-${var.env}-project-boundary"
}
