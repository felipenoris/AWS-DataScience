# Names and ARNs the slice's files share.

locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id

  account_root = "arn:${local.partition}:iam::${local.account_id}:root"
  role_prefix  = "arn:${local.partition}:iam::${local.account_id}:role"

  infrastructure_access_role_arn = one(data.aws_iam_roles.infrastructure_access.arns)
  data_scientist_role_arn        = one(data.aws_iam_roles.data_scientist.arns)

  # The contracts, by name: the job role and the debug role (production/sagemaker/), the deploy role
  # (production/foundation/), and Stage 10's chain role and per-workflow execution roles.
  job_role_arn          = "${local.role_prefix}/awsds-${var.env}-job-exec"
  debug_role_arn        = "${local.role_prefix}/awsds-${var.env}-debug"
  deploy_role_arn       = "${local.role_prefix}/${var.deploy_role_name}"
  chain_role_arn        = "${local.role_prefix}/awsds-${var.env}-chain-exec"
  workflow_role_pattern = "${local.role_prefix}/awsds-${var.env}-wf-*"

  # The deployment manager, who reads workflow runs (Stage 10 decision 11). The reserved suffix is
  # minted per account, so the role is matched by pattern; it may not be provisioned in an account yet.
  deployment_manager_pattern = "${local.role_prefix}/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_DeploymentManagerAccess_*"

  # A MWAA Serverless workflow's ARN carries its name and a generated suffix, so the encryption context
  # the service binds to the workflow is matched by pattern (Stage 10 decision 2).
  workflow_arn_pattern = "arn:${local.partition}:airflow-serverless:${var.region}:${local.account_id}:workflow/awsds-${var.env}-wf-*"

  s3_via        = "s3.${var.region}.amazonaws.com"
  sagemaker_via = "sagemaker.${var.region}.amazonaws.com"

  outputs_bucket_name = "awsds-${var.env}-outputs"
  derived_bucket_name = "awsds-${var.env}-derived"
  outputs_bucket_arn  = "arn:${local.partition}:s3:::${local.outputs_bucket_name}"

  # The prefixes the release job writes from the deploy runner (Stage 10): the release's tree and the
  # inbox it seeds from the bundle's samples.
  deploy_prefixes = ["applications/", "inbox/"]

  # The log groups the data key encrypts or will: the job groups production/sagemaker/ declares, which
  # move under the key once it exists, and Stage 10's workflow and chain groups.
  log_group_patterns = [
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws/sagemaker/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws-glue/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/awsds/${var.env}/wf/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws/vendedlogs/states/awsds-${var.env}-chains",
  ]
}
