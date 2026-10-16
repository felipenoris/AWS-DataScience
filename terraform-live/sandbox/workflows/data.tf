# What this slice reads and does not own.
#
# The account id, for the job ARN patterns: a SageMaker or Glue job ARN carries the account
# segment, which cannot be a literal in a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The project key, by the alias sagemaker-prereqs/kms.tf gives it: the projects bucket is encrypted
# under it, and the test deploy role (deploy-role.tf) uses it through S3 and the workflow service.
data "aws_kms_alias" "project" {
  name = "alias/awsds-${var.env}-project"
}

# Each project role, read rather than assumed: a missing project fails at plan, naming the role,
# and main.tf's precondition reads the role's permissions boundary. The roles are the service's,
# minted when a project is created in the portal.
data "aws_iam_role" "project" {
  for_each = toset(var.project_roles)
  name     = each.value
}

locals {
  processing_jobs = "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"

  # A Glue job named for the caller's project, <app>-<project id>: the project id is the role's own
  # AmazonDataZoneProject tag, so one statement serves every role listed. $${ keeps the policy
  # variable out of Terraform's interpolation, as main.tf's AddTags statement does.
  glue_jobs_named_for_the_caller = "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:job/*-$${aws:PrincipalTag/AmazonDataZoneProject}"

  boundary_name = "awsds-${var.env}-project-boundary"
}
