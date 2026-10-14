# The consumer side of the lake (Stage 5a pass 4, steps 8 and 9), layer [P].
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
  # session it issues is scope-reduced to one grant's prefix. It is the only statement on the key
  # that admits a call through S3 - the persona's went with the derived zone (D19 revision) - so
  # the vending door is the one path to an S3 object encrypted here.
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

    # ---------------------------------------- the warehouse's own encryption (Stage 5b step 1.1)
    #
    # WHY IT HAS TO BE HERE. `CreateNamespace` was refused on 2026-09-20 with `ValidationException:
    # Unable to create namespace. The key '...' is inaccessible`, and the cause is D31 working as
    # designed: this key's policy grants the account root the administrative actions and NONE of the
    # cryptographic ones, so no identity policy in this account can reach it. The refusal names the
    # resource-based policy in as many words - `no resource-based policy allows the kms:Encrypt
    # action` - which is also how it was separated from an identity-policy gap (Lesson 42's shape at
    # the KMS layer: read the wording, never the exit code).
    #
    # WHY THE WAREHOUSE TAKES THIS KEY AT ALL. docs/GOVERNANCE.md's per-account encryption rule: one
    # data CMK per account, and a Redshift namespace in Sandbox is a data store in Sandbox exactly as
    # awsds-sandbox-lake is. The alternative - an AWS-managed key for the warehouse - would make
    # "who can read this account's data" two answers instead of one.
    #
    # WHY THE SHAPE IS `root` + ViaService AND NOT A NAMED ROLE. A key policy naming a role ARN
    # grants that role directly, whatever its IAM says; the `root` form delegates to IAM, so this
    # statement admits only a principal whose own identity policy already allows the action AND whose
    # call arrives through Redshift Serverless. Both halves must hold. That keeps D31's line intact
    # where D31 draws it: an approver with ReadOnlyAccess gains nothing, because ReadOnlyAccess
    # carries no kms:Decrypt, and a persona gains nothing, because reading data through this service
    # needs a database session and `redshift-serverless:GetCredentials` is withheld from
    # DataScientistAccess (Stage 5b step 2.3).
    #
    # THE ACTION LIST IS AWS'S OWN for this service, and each one is load-bearing at a different
    # moment: DescribeKey and Encrypt/GenerateDataKey* at `CreateNamespace`, which is where the
    # refusal above happened; CreateGrant because Redshift Serverless creates a grant and then uses
    # THAT for every later read and write - so this statement is the door to creating the warehouse,
    # not the door the warehouse uses afterwards; ReEncrypt* and Decrypt for the key rotation path.
    # AWS's note on the service: Redshift Serverless "does not support encryption context or confused
    # deputy headers, so access for this service is scoped using kms:ViaService only" - which is why
    # there is no EncryptionContext condition to add and why the ViaService pin is the whole scope.
    {
      Sid       = "AllowRedshiftServerlessViaServiceInThisAccount"
      Effect    = "Allow"
      Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
      Action = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:CreateGrant",
        "kms:DescribeKey",
      ]
      Resource = "*"
      Condition = {
        StringEquals = { "kms:ViaService" = "redshift-serverless.${var.region}.amazonaws.com" }
      }
    },

    # ------------------------------------------ an application job's writes (Stage 8 step 2.4)
    #
    # An application's job role writes its outputs to awsds-<env>-outputs below, a data bucket under
    # this key (docs/GOVERNANCE.md, Encryption). The role is [E], in sandbox/app/<app>/, and a key
    # policy naming a role stores the role's unique id, so the role the next session creates would not
    # be the one named. The statement therefore admits through the account root, which delegates to
    # IAM, and names the roles in a condition evaluated on every call: a role called
    # awsds-<env>-app-*-job, whose own policy allows the action, calling through S3. Both halves must
    # hold, as for the warehouse above. It is D31's fourth reader, of the third's shape: a role no
    # person holds, its identity policy naming one prefix of one bucket.
    {
      Sid       = "AllowApplicationJobRolesViaS3"
      Effect    = "Allow"
      Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
      Resource  = "*"
      Condition = {
        StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
        ArnLike = {
          "aws:PrincipalArn" = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-app-*-job"
        }
      }
    },
  ]
}

# ------------------------------------------------------ the applications' outputs (Stage 8 step 2.4)
#
# Where an application run by hand in this account writes, one prefix per application: the Sandbox
# counterpart of production/data/'s output buckets (Stage 9). [P], since the module's buckets are, and
# disposable by declaration: an output is the result of an engineering run, reproducible from the
# application's release, so every object expires after 30 days. Under the data key; the application
# job roles reach it through the statement above. CostCenter names Stage 8, over this slice's
# default_tags, which name Stage 5.
module "outputs_bucket" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.4.0"

  bucket_name     = "awsds-${var.env}-outputs"
  kms_key_arn     = module.consumer_data.data_key_arn
  expiration_days = 30
  tags            = { CostCenter = "stage-08" }
}
