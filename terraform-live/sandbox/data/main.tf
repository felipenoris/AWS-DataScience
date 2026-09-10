# The consumer side of the lake (Stage 5 pass 4, steps 8 and 9), layer [P].
#
# This slice is thin. Everything in it is the same design in both Interactive accounts - and in
# every business unit's Sandbox once D35's N passes 1 - so the design lives in
# terraform-modules/consumer-data/ and what changes per account is the values below. A setting that
# lives here instead of in the module will differ between accounts by accident (Lesson 14); this
# file says which account, not what.
#
# The apply is staged, and this is the file the operator reads before running it (Recipe D in
# docs/plan/runbooks/terraform-changes.md):
#
#   1. terraform apply -target=module.consumer_data.aws_lakeformation_data_lake_settings.this
#   2. ./aws/datalake.py  - read DL-6 for this account. If it still names IAM_ALLOWED_PRINCIPALS,
#      stop: revoke the virtual group before step 3, because the create-defaults act at creation
#      time and the first local catalog object is the resource link.
#   3. terraform apply     - the remainder, then re-plan to `No changes`.

locals {
  # one() fails on zero and on two - both are findings, and neither may quietly become an empty
  # admins list (which is the state that makes a held share invisible).
  infrastructure_access_role_arn = one(data.aws_iam_roles.infrastructure_access.arns)
  data_scientist_role_arn        = one(data.aws_iam_roles.data_scientist.arns)

  # The sandbox lake's access role (Stage 16 pass 2.2). The name is derived from the convention -
  # awsds-<env>-<component>, docs/plan/conventions.md §6 - exactly as sandbox/lake/ derives it from
  # the same var.env, so this is a naming rule rather than a copy of another slice's state. KMS
  # validates the principals in a key policy, so if the two ever disagree this apply fails with
  # MalformedPolicyDocument naming an ARN that does not exist, rather than writing a statement that
  # admits nobody. It is also why the apply order is lake/ first (layers.py's `lake` rank comment:
  # data -> lake -> data, three acts over two slices).
  lake_access_role_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-lake-access"
}

module "consumer_data" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  # v0.6.0 no longer creates the derived zone: D19 revised, the zone re-homed onto the SMUS project
  # path, and awsds-sandbox-derived and its enforced workgroup were destroyed 2026-08-26/27. The
  # data CMK stays, because the sandbox lake encrypts under it, minus its persona statement. The
  # `region` input went with the statement that consumed it.
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/consumer-data?ref=consumer-data-v0.6.0"

  env = var.env

  lake_catalog_id = data.aws_caller_identity.lake.account_id
  lake_databases  = data.terraform_remote_state.lake.outputs.database_names

  data_lake_admin_role_arn = local.infrastructure_access_role_arn
  data_scientist_role_arn  = local.data_scientist_role_arn


  # ---------------------------------------------------- the lake's reader (Stage 16 pass 2.2)
  #
  # Reach is an intersection (Lesson 28) and this is the half that lives in this slice. The other
  # half is sandbox/lake/'s inline policy on the same role; neither alone lets any object in
  # awsds-sandbox-lake be read, which is what step 2.3 records as a baseline before any of this is
  # applied.
  #
  # The statement is necessary because this key's policy carries no delegate-to-IAM statement
  # (measured at step 0.3, 2026-08-26): root holds the administrative actions and none of the
  # cryptographic ones, which is the whole of D31, so an identity policy in this account cannot
  # grant kms:Decrypt on it. A new reader is admitted here or it is not admitted.
  #
  # It is a widening. D31's words are "kms:Decrypt to the project execution roles and
  # DataScientistAccess, and to nobody else", and this is a third reader. It stays inside the
  # decision because the role is not a human's: it is a vending role with one bucket in its identity
  # policy, assumable only by S3 Access Grants (and, from pass 4, by named project roles), and every
  # session it issues is scope-reduced to one grant's prefix. It is now the only cryptographic
  # statement on the key - the persona's went with the derived zone (D19 revision) - so the vending
  # door is the one path to anything encrypted here.
  additional_data_key_policy_statements = [
    {
      Sid       = "AllowSandboxLakeAccessRoleViaS3"
      Effect    = "Allow"
      Principal = { AWS = local.lake_access_role_arn }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
      Resource  = "*"
      Condition = {
        StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
      }
    },
  ]
}
