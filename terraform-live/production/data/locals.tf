# Names and ARNs the slice's files share.

locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id

  account_root = "arn:${local.partition}:iam::${local.account_id}:root"
  role_prefix  = "arn:${local.partition}:iam::${local.account_id}:role"

  infrastructure_access_role_arn = one(data.aws_iam_roles.infrastructure_access.arns)
  data_scientist_role_arn        = one(data.aws_iam_roles.data_scientist.arns)

  # The contracts, by name: the job role and the debug role (production/sagemaker/), the deploy role
  # (production/foundation/), and Stage 10's chain role (production/chains/). workflow_role_pattern and
  # workflow_arn_pattern name release T's per-workflow roles and workflows, retired by Stage 19 item 31:
  # no role or workflow matches them, so the statements that use them admit nothing. The CI/CD CLI's
  # workflows run as the deployment project's role, encrypted under alias/awsds-<env>-project.
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

  # The prefixes the deploy role reaches from the deploy runner (Stage 10): the release's tree and the
  # inbox it seeds from the bundle's samples, both written.
  deploy_prefixes = ["applications/", "inbox/"]

  # The log groups the data key encrypts or will: the job groups production/sagemaker/ declares and
  # associates with the key, Stage 10's workflow and chain groups, and the governed warehouse's three
  # audit groups (Stage 9 step 9.1, decision 8), under Redshift's /aws/redshift/ prefix.
  log_group_patterns = [
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws/sagemaker/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws-glue/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws/redshift/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/awsds/${var.env}/wf/*",
    "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:/aws/vendedlogs/states/awsds-${var.env}-chains",
  ]
}
