# Stage 9 step 4.1 - Staging's data platform, step 1's shape without the governed write: the
# consumer-data call (the account data CMK, the LF settings, the resource links to the read share and
# the persona's re-grants), and beside it what consumer-data-v0.6.0 does not supply (buckets.tf,
# athena.tf, lakeformation.tf). Staging reads the governed lake read-only through the LF-Tag share
# Sandbox holds, writes only to its own catalog, buckets and key, and copies nothing (decision 3).
#
# The first apply is two, Recipe D (docs/plan/runbooks/terraform-changes.md): the LF settings alone
# under -target, read back (DT-5), IAMAllowedPrincipals revoked if it is still there, then the rest. A
# resource link or a database created while the create-time defaults still grant IAMAllowedPrincipals
# is born deferring to IAM, and clearing the settings afterwards does not reach it (step 1.3). The
# module writes CROSS_ACCOUNT_VERSION 4 and SET_CONTEXT TRUE; Staging read 1 and TRUE on 2026-10-22,
# and the version only governs how this account shares, which it never does.
#
# The key policy is enumerated: the account root administers the key and holds no cryptographic
# action, so delegation to IAM is impossible and every principal that decrypts is named here (D31).
# The approvers are named nowhere, and no Production principal either: Staging reads nothing of
# Production's outputs (decision 1). Every role is matched by aws:PrincipalArn under the account root,
# which KMS does not validate, so a role Stage 10 creates later is admitted by its name.

module "consumer_data" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/consumer-data?ref=consumer-data-v0.6.0"

  env = var.env

  lake_catalog_id = data.aws_caller_identity.lake.account_id
  lake_databases  = data.terraform_remote_state.lake.outputs.database_names

  data_lake_admin_role_arn = local.infrastructure_access_role_arn
  data_scientist_role_arn  = local.data_scientist_role_arn

  additional_data_key_policy_statements = [
    # The job role writes and reads both buckets (step 4.3, 3.1's ReadAndWriteTheAccountBuckets).
    {
      Sid       = "AllowTheJobRoleViaS3"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey"]
      Resource  = "*"
      Condition = {
        ArnEquals    = { "aws:PrincipalArn" = local.job_role_arn }
        StringEquals = { "kms:ViaService" = local.s3_via }
      }
    },
    # The persona reads, and writes nothing (DataScientistStagingAccess, DenyEveryWrite).
    {
      Sid       = "AllowTheDataScientistToDecryptViaS3"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt"]
      Resource  = "*"
      Condition = {
        ArnEquals    = { "aws:PrincipalArn" = local.data_scientist_role_arn }
        StringEquals = { "kms:ViaService" = local.s3_via }
      }
    },
    # The release job writes the release's tree and seeds the inbox (Stage 10); InfrastructureAccess
    # beside it, or Stage 8 3.8's by-hand parity is refused.
    {
      Sid       = "AllowTheReleaseRolesViaS3"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey"]
      Resource  = "*"
      Condition = {
        ArnEquals    = { "aws:PrincipalArn" = [local.deploy_role_arn, local.infrastructure_access_role_arn] }
        StringEquals = { "kms:ViaService" = local.s3_via }
      }
    },
    # A workflow encrypted under this key (Stage 10 decision 2): MWAA Serverless calls the key in its
    # caller's session, CreateGrant, GenerateDataKey and Decrypt in the one creating a workflow (Stage 18
    # 4.2, 2026-10-19). The data calls carry the workflow's ARN as encryption context; which condition
    # the CreateGrant carries is unread, so it is held to grants for an AWS resource.
    {
      Sid       = "AllowTheReleaseRolesForTheirWorkflows"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey"]
      Resource  = "*"
      Condition = {
        ArnEquals  = { "aws:PrincipalArn" = [local.deploy_role_arn, local.infrastructure_access_role_arn] }
        StringLike = { "kms:EncryptionContext:aws:airflow-serverless:workflow-arn" = local.workflow_arn_pattern }
      }
    },
    {
      Sid       = "AllowTheReleaseRolesToGrantTheWorkflowService"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:CreateGrant"]
      Resource  = "*"
      Condition = {
        ArnEquals = { "aws:PrincipalArn" = [local.deploy_role_arn, local.infrastructure_access_role_arn] }
        Bool      = { "kms:GrantIsForAWSResource" = "true" }
      }
    },
    # DescribeKey carries no grant or context key, so it stands alone.
    {
      Sid       = "AllowTheReleaseRolesToDescribeTheKey"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:DescribeKey"]
      Resource  = "*"
      Condition = {
        ArnEquals = { "aws:PrincipalArn" = [local.deploy_role_arn, local.infrastructure_access_role_arn] }
      }
    },
    # The chain role starts a run and reads it back (GetWorkflowRun decrypts, Stage 18 0.4).
    {
      Sid       = "AllowTheChainRoleForItsWorkflows"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey"]
      Resource  = "*"
      Condition = {
        ArnEquals  = { "aws:PrincipalArn" = local.chain_role_arn }
        StringLike = { "kms:EncryptionContext:aws:airflow-serverless:workflow-arn" = local.workflow_arn_pattern }
      }
    },
    # A workflow's execution role writes the result file and the inbox markers through S3, decrypts its
    # own workflow, and grants SageMaker the processing job's volume key in the submitting session (6i).
    {
      Sid       = "AllowTheWorkflowRolesViaS3"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt", "kms:GenerateDataKey"]
      Resource  = "*"
      Condition = {
        ArnLike      = { "aws:PrincipalArn" = local.workflow_role_pattern }
        StringEquals = { "kms:ViaService" = local.s3_via }
      }
    },
    {
      Sid       = "AllowTheWorkflowRolesForTheirWorkflows"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:Decrypt"]
      Resource  = "*"
      Condition = {
        ArnLike    = { "aws:PrincipalArn" = local.workflow_role_pattern }
        StringLike = { "kms:EncryptionContext:aws:airflow-serverless:workflow-arn" = local.workflow_arn_pattern }
      }
    },
    {
      Sid       = "AllowJobVolumeGrantsThroughSageMaker"
      Effect    = "Allow"
      Principal = { AWS = local.account_root }
      Action    = ["kms:CreateGrant", "kms:DescribeKey"]
      Resource  = "*"
      Condition = {
        ArnLike      = { "aws:PrincipalArn" = [local.workflow_role_pattern, local.deploy_role_arn] }
        StringEquals = { "kms:ViaService" = local.sagemaker_via }
      }
    },
    # CloudWatch Logs for the groups encrypted under this key, each named in the condition.
    {
      Sid       = "AllowCloudWatchLogsForTheJobAndWorkflowGroups"
      Effect    = "Allow"
      Principal = { Service = "logs.${var.region}.amazonaws.com" }
      Action    = ["kms:Encrypt*", "kms:Decrypt*", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:Describe*"]
      Resource  = "*"
      Condition = {
        ArnLike = { "kms:EncryptionContext:aws:logs:arn" = local.log_group_patterns }
      }
    },
  ]
}
