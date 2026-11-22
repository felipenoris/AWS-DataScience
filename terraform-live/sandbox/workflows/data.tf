# What this slice reads and does not own.
#
# The account id, for the job ARN patterns: a SageMaker or Glue job ARN carries the account
# segment, which cannot be a literal in a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# Each project role, read rather than assumed: a missing project fails at plan, naming the role,
# and main.tf's precondition reads the role's permissions boundary. The roles are the service's,
# minted when a project is created in the portal.
data "aws_iam_role" "project" {
  for_each = toset(var.project_roles)
  name     = each.value
}

# The project key, by the alias sagemaker-prereqs gives it: the projects bucket encrypts under it,
# and the bundle role decrypts a trained model with it (deploy-role.tf).
data "aws_kms_alias" "project" {
  name = "alias/awsds-${var.env}-project"
}

locals {
  processing_jobs = "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"
  training_jobs   = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:training-job/*"
  transform_jobs  = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:transform-job/*"
  models          = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model/*"

  # Each application whose `dev` project trains a model: the project id is its role's own
  # AmazonDataZoneProject tag, read rather than copied; the versions are its group's; the model prefix
  # sits in the project's shared location, <domain>/<project>/shared/ (docs/SMUS.md, §S3), which the
  # project's default.s3_shared connection names. A statement id takes letters and digits alone.
  model_applications = {
    for app, m in var.model_applications : app => {
      sid_suffix     = join("", [for word in split("-", app) : title(word)])
      project_id     = data.aws_iam_role.project[m.project_role].tags["AmazonDataZoneProject"]
      model_versions = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model-package/${m.model_package_group}/*"
      model_prefix   = "${var.datazone_domain_id}/${data.aws_iam_role.project[m.project_role].tags["AmazonDataZoneProject"]}/shared/${m.model_prefix}/"
    }
  }

  # The bucket sagemaker-prereqs names for the projects, the Tooling blueprint's S3Location.
  projects_bucket = "awsds-${var.env}-smus-projects"

  # A Glue job named for the caller's project, <app>-<project id>: the project id is the role's own
  # AmazonDataZoneProject tag, so one statement serves every role listed. $${ keeps the policy
  # variable out of Terraform's interpolation, as main.tf's AddTags statement does.
  glue_jobs_named_for_the_caller = "arn:aws:glue:${var.region}:${data.aws_caller_identity.current.account_id}:job/*-$${aws:PrincipalTag/AmazonDataZoneProject}"

  boundary_name = "awsds-${var.env}-project-boundary"
}
