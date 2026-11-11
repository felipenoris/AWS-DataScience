# The blueprint prerequisites of this account's deployment project (Stage 19 step 4.4, decision 6
# (b)), layer [P]: a SageMaker Unified Studio project the CI/CD CLI deploys applications into, in
# which no person works and no space runs (D17).
#
# The module is the one sandbox/sagemaker/ calls. What differs in a deployment target is the list of
# blueprints, Tooling and DataLake alone (variables.tf), and the slice's name: <env>/sagemaker/ is
# the job-role slice of Stage 9 in these accounts (conventions §6).
#
# This file is one of the files staging/studio/ and production/studio/ hold as copies
# (scripts/check-copies.py). What one account adds lives in a file of its own.
#
# A project and its environments are not here: DataZone owns them, and a Terraform resource for one
# would fight the blueprint (conventions §6). The project is created with `datazone create-project`
# from the `deployment` profile of this account (data-governance/governance/), and its role's name,
# minted at that moment, is written into project-roles.tf afterwards.
#
# The order of the applies:
#
#   1. the prerequisites: the two roles, the D13 boundary, the project key, the projects bucket and
#      the log group. No datazone: call, so `-var blueprints_enabled=false` plans it before the
#      account is associated or the Workloads SCP admits the caller
#   2. the two blueprint configurations and their grants, once the account is associated
#      (backend.SMUS_ASSOCIATED) and DenyDataZoneEntirely excepts InfrastructureAccess
#   3. after the project exists: the workflows grant and the deny on a person's session, on the
#      roles project-roles.tf names

locals {
  # The lake's Lake Formation-registered locations, raw and curated. The drop-box is not among
  # them: files land there by IAM and are catalogued afterwards (D18).
  lake_registered_bucket_arns = [
    data.terraform_remote_state.lake.outputs.bucket_arns["raw"],
    data.terraform_remote_state.lake.outputs.bucket_arns["curated"],
  ]

  # The one sanctioned direct write, the expression identity/sso/locals.tf builds for the persona.
  lake_dropbox_write_arn = format(
    "%s/%s/*",
    data.terraform_remote_state.lake.outputs.bucket_arns["dropbox"],
    data.terraform_remote_state.lake.outputs.dropbox_prefix,
  )
}

module "sagemaker_prereqs" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-prereqs?ref=sagemaker-prereqs-v0.10.0"

  env    = var.env
  region = var.region

  vpc_id             = data.terraform_remote_state.network.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.network.outputs.private_subnet_ids

  lake_registered_bucket_arns = local.lake_registered_bucket_arns
  lake_dropbox_write_arn      = local.lake_dropbox_write_arn
  lake_data_key_arn           = data.terraform_remote_state.lake.outputs.data_key_arn

  allowed_instance_types = var.allowed_instance_types

  # The fence around the deployment project's role (Stage 19 decision 21 (b), TM-30): what the role
  # never touches in this account, denied in the boundary so that AWS's next policy version cannot
  # reach it. The two lists are the account's own (fence.tf); the rest is the same in both targets.
  # No role is assumable and Redshift is not fenced: step 4.11 writes what the warehouse workflow
  # needs (decision 16 (b)).
  fenced_bucket_names     = var.fenced_bucket_names
  fenced_repository_names = var.fenced_repository_names
  fence_customer_keys     = true
  fenced_secret_names     = ["awsds-*", "redshift!*"]
  fence_role_assumption   = true
  fenced_services         = ["bedrock", "bedrock-agentcore", "q", "codewhisperer"]

  blueprint_names = var.blueprint_names

  blueprints_enabled = var.blueprints_enabled
  # The domain account is read from the lake's data-key ARN, field 4: the lake and the domain share
  # the Data Governance account, and the lake state is read unconditionally.
  domain_account_id = element(split(":", data.terraform_remote_state.lake.outputs.data_key_arn), 4)
  domain_execution_role_arn = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.domain_execution_role_arn
    : null
  )
  domain_id = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.domain_id
    : null
  )
  root_domain_unit_id = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.root_domain_unit_id
    : null
  )
}
