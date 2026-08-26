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

  # THE SANDBOX LAKE'S ACCESS ROLE (Stage 16 pass 2.2). The name is DERIVED from the convention
  # - awsds-<env>-<component>, docs/plan/conventions.md §6 - exactly as sandbox/lake/ derives it
  # from the same var.env, so this is the tree's ordinary way of naming a resource and not a
  # copy of another slice's state. What makes the derivation safe to repeat is the failure mode:
  # KMS VALIDATES the principals in a key policy, so if the two ever disagree this apply fails
  # with MalformedPolicyDocument naming an ARN that does not exist, rather than writing a
  # statement that admits nobody. That is also why the apply ORDER is lake/ first (layers.py's
  # `lake` rank comment: data -> lake -> data, three acts over two slices).
  lake_access_role_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-lake-access"

  # THE TWO SMUS SERVICE ROLES, ADOPTED 2026-08-26 (the user's decision, taken on the finding
  # below). They are Lake Formation data lake administrators in THIS account and nobody in this
  # repository made them so: the service added itself when the first project was created here
  # (2026-08-22). Development has no project and its plan reads `No changes`, which is what
  # attributes the cause; nothing in the estate reported it, because DL-5 measures `parameters`
  # and not `admins`.
  #
  # ADOPTION RATHER THAN REMOVAL, and the two halves of the reason: the Stage 6 create path was
  # measured AFTER these existed, so stripping them risks the one path this account's SMUS work
  # stands on; and removing them from the code would not remove them from AWS - it would only
  # make every future plan fight the service that put them there.
  #
  # NAMES, NOT PASTED ARNS: both are contracts of terraform-modules/sagemaker-prereqs, built the
  # same way every other name in this tree is. A drift between the two spellings fails the apply
  # by name - Lake Formation rejects an administrator that does not exist.
  smus_admin_role_arns = [
    for name in ["smus-manage-access", "smus-provisioning"] :
    "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-${name}"
  ]
}

module "consumer_data" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/consumer-data?ref=consumer-data-v0.4.0"

  env    = var.env
  region = var.region

  lake_catalog_id = data.aws_caller_identity.lake.account_id
  lake_databases  = data.terraform_remote_state.lake.outputs.database_names

  data_lake_admin_role_arn = local.infrastructure_access_role_arn
  data_scientist_role_arn  = local.data_scientist_role_arn

  # ------------------------------------------------------- what SMUS made of this account (v0.4.0)
  #
  # Both values are READ BACK from the account, never chosen here - see the local above. They are
  # in this slice and not in the module because `development/data/` has neither, and its plan
  # reading `No changes` across both bumps is what keeps the difference honest.
  additional_data_lake_admin_role_arns  = local.smus_admin_role_arns
  allow_full_table_external_data_access = true

  # ---------------------------------------------------- the lake's reader (Stage 16 pass 2.2)
  #
  # REACH IS AN INTERSECTION (Lesson 28), AND THIS IS THE HALF THAT LIVES IN THIS SLICE. The
  # other half is sandbox/lake/'s inline policy on the same role; neither one alone lets any
  # object in awsds-sandbox-lake be read, which is what step 2.3 records as a baseline BEFORE
  # any of this is applied.
  #
  # WHY THE STATEMENT IS NECESSARY AT ALL, measured rather than assumed (step 0.3, 2026-08-26):
  # this key's policy carries NO delegate-to-IAM statement - root holds the administrative
  # actions and none of the cryptographic ones, which is the whole of D31 - so an identity
  # policy in this account cannot grant kms:Decrypt on it. A new reader is admitted here or
  # it is not admitted.
  #
  # WHY IT IS A WIDENING, AND WHAT PAYS FOR IT: D31's own words are "kms:Decrypt to the project
  # execution roles and DataScientistAccess, and to nobody else". This is a third reader. What
  # keeps it inside the decision rather than beside it is that the role is not a human's: it is
  # a vending role with one bucket in its identity policy, assumable only by S3 Access Grants
  # (and, from pass 4, by named project roles), and every session it issues is scope-reduced to
  # one grant's prefix. The ViaService pin below is the same one the persona statement carries.
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
