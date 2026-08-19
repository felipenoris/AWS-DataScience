# The consumer side of the lake (Stage 5 pass 4, steps 8 and 9), layer [P].
#
# THIS SLICE IS DELIBERATELY THIN. Everything in it is the SAME design in both Interactive
# accounts - and in every business unit's Sandbox once D35's N passes 1 - so the design lives in
# terraform-modules/consumer-data/ and what changes per account is the four values below.
# A setting that lives here instead of in the module is a setting that will differ between
# accounts by accident (Lesson 14); this file exists to say WHICH account, not WHAT.
#
# THE APPLY IS TWO STEPS, and this is the file the operator reads before running it (Recipe D
# in docs/plan/runbooks/terraform-changes.md):
#
#   1. terraform apply -target=module.consumer_data.aws_lakeformation_data_lake_settings.this
#   2. ./aws/datalake.py  - read DL-6 for THIS account. If it still names IAM_ALLOWED_PRINCIPALS,
#      STOP: revoke the virtual group before step 3, because the create-defaults act at CREATION
#      time and the first local catalog object is the resource link.
#   3. terraform apply     - the remainder, then re-plan to `No changes`.

locals {
  # one() fails on zero and on two - both are findings, and neither may quietly become an empty
  # admins list (which is the state that makes a held share invisible).
  infrastructure_access_role_arn = one(data.aws_iam_roles.infrastructure_access.arns)
  data_scientist_role_arn        = one(data.aws_iam_roles.data_scientist.arns)
}

module "consumer_data" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/consumer-data?ref=consumer-data-v0.2.0"

  env    = var.env
  region = var.region

  lake_catalog_id = data.aws_caller_identity.lake.account_id
  lake_databases  = data.terraform_remote_state.lake.outputs.database_names

  data_lake_admin_role_arn = local.infrastructure_access_role_arn
  data_scientist_role_arn  = local.data_scientist_role_arn
}
