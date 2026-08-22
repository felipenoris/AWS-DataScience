# THE ACCOUNT'S PROJECT KMS KEY (Stage 6 step 2.1).
#
# WHAT IT IS FOR: the resources a blueprint provisions in this account that take a customer
# key - the per-project SageMaker AI domain's EBS volumes and its home EFS, the blueprint's
# own artifacts. It is NOT the account's DATA key: docs/GOVERNANCE.md §Encryption puts one
# data CMK per account (alias/awsds-<env>-data, D31) and the derived zone lives under it. Two
# keys, two jobs - a project's scratch volume and a governed copy of the lake are not the same
# blast radius, and the second one's key policy is a control this module has no business
# widening.
#
# THE CONSUMER ARRIVED 2026-08-22 (v0.3.2) - the paragraph that stood here said "nothing names
# it as of pass 1" with verification (xx) as the revision trigger, and what fired the trigger
# was a measurement, not (xx): aws-samples' SMUS-IaC Tooling block passes the key as the
# KmsKeyArn REGIONAL PARAMETER (the wizard's optional "Data encryption" field, which the
# API-enabled configuration had silently left at the AWS managed key). Two consumers now name
# it: Tooling's KmsKeyArn in blueprints.tf, and the projects bucket's SSE in s3.tf.
#
# THE POLICY STOPPED BEING THE DELEGATE-TO-IAM DEFAULT AT v0.3.3 (2026-08-22), and the change
# was forced by a measurement: the first deploy to reach KMS validation died with "Could not
# resolve KMS key ... may not be accessible". The validator is the DATAZONE SERVICE PRINCIPAL
# (and the domain execution role, which lives in the DOMAIN account) - neither passes through
# delegate-to-IAM, which only reaches this account's own IAM principals. The statements below
# are the documented contract for a CMK handed to the Tooling blueprint
# (adminguide/sagemaker-unified-studio-provisioned-resources-key-permissions.html), adapted:
# our role names for the doc's console names, this Region for its us-east-1, and the
# category-1 roster for its full menu - the Redshift and Airflow CreateGrant statements are
# DELIBERATELY ABSENT because no enabled blueprint reaches either service; each joins in the
# same commit that promotes its blueprint out of category 2 (Lesson 14).
locals {
  # The IAM-delegation root statement the default policy had - kept first, because losing it
  # would orphan the key from its own account's administration.
  key_policy_iam_delegation = [
    {
      Sid       = "EnableIamPolicyDelegationInThisAccount"
      Effect    = "Allow"
      Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
      Action    = "kms:*"
      Resource  = "*"
    },
  ]

  # The domain-side principals: the datazone service principal always; the domain execution
  # role joins when the caller knows it (null before blueprints_enabled, like domain_id).
  smus_domain_principal = merge(
    { Service = ["datazone.amazonaws.com"] },
    var.domain_execution_role_arn != null ? { AWS = [var.domain_execution_role_arn] } : {}
  )

  key_policy_smus_domain = [
    # What the deploy-time validator and the domain's own operations need - DescribeKey is the
    # call the 2026-08-22 failure named ("resolve to its canonical ARN").
    {
      Sid       = "AllowKmsKeyUsageForSageMakerDomain"
      Effect    = "Allow"
      Principal = local.smus_domain_principal
      Action = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey",
        "kms:CreateGrant",
      ]
      Resource = "*"
    },
    {
      Sid       = "AllowSageMakerDomainKmsGrantPermissions"
      Effect    = "Allow"
      Principal = local.smus_domain_principal
      Action = [
        "kms:ListGrants",
        "kms:RevokeGrant",
      ]
      Resource = "*"
    },
    # CloudWatch Logs encrypts the blueprint-created log groups with this key. The doc's three
    # name patterns are kept even though airflow-*/mwaa-* wait on category-2 Workflows - a log
    # statement scoped by encryption context admits nothing until such a group exists.
    {
      Sid       = "AllowKmsPermissionsForCloudWatch"
      Effect    = "Allow"
      Principal = { Service = "logs.${var.region}.amazonaws.com" }
      Action = [
        "kms:Encrypt*",
        "kms:Decrypt*",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:Describe*",
      ]
      Resource = "*"
      Condition = {
        ArnLike = {
          "kms:EncryptionContext:aws:logs:arn" = [
            "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:datazone-*",
            "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:airflow-*",
            "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/mwaa-serverless*",
          ]
        }
      }
    },
    # The provisioning role's two service paths that exist in category 1: Athena result
    # encryption (the Tooling workgroup) and EMR Serverless.
    {
      Sid       = "AthenaKmsPermissions"
      Effect    = "Allow"
      Principal = { AWS = module.provisioning_role.role_arn }
      Action    = "kms:GenerateDataKey"
      Resource  = "*"
      Condition = {
        StringEquals = {
          "aws:CalledViaLast"   = "athena.amazonaws.com"
          "aws:ResourceAccount" = "$${aws:PrincipalAccount}"
        }
      }
    },
    {
      Sid       = "EmrServerlessKmsPermissions"
      Effect    = "Allow"
      Principal = { Service = "emr-serverless.amazonaws.com" }
      Action = [
        "kms:Decrypt",
        "kms:GenerateDataKey",
      ]
      Resource = "*"
      Condition = {
        ArnLike = {
          "aws:SourceArn" = "arn:${data.aws_partition.current.partition}:emr-serverless:${var.region}:${data.aws_caller_identity.current.account_id}:/applications/*"
        }
      }
    },
    {
      Sid       = "EmrServerlessKmsPermissionsForProvisioning"
      Effect    = "Allow"
      Principal = { AWS = module.provisioning_role.role_arn }
      Action = [
        "kms:Decrypt",
        "kms:GenerateDataKey",
      ]
      Resource = "*"
    },
  ]

  # The project-role statements are scoped by the DOMAIN id in the encryption context and the
  # principal tag, so they cannot exist before the domain does - the same gate domain_id
  # already rides for the blueprint configurations.
  # (comprehension-with-filter rather than a ternary: [] and a tuple of objects do not unify)
  key_policy_smus_project_roles = [for st in [
    {
      Sid       = "GrantKMSPermissionsForAllProjectRoles"
      Effect    = "Allow"
      Principal = { AWS = "*" }
      Action = [
        "kms:GenerateDataKey",
        "kms:Decrypt",
      ]
      Resource = "*"
      Condition = {
        StringEquals = {
          "aws:PrincipalTag/AmazonDataZoneDomain"       = var.domain_id
          "kms:EncryptionContext:aws:datazone:domainId" = var.domain_id
          "kms:ViaService"                              = ["datazone.${var.region}.amazonaws.com"]
        }
      }
    },
    {
      Sid       = "AllowCreateGrantForProjectRoles"
      Effect    = "Allow"
      Principal = { AWS = "*" }
      Action    = "kms:CreateGrant"
      Resource  = "*"
      Condition = {
        StringEquals = {
          "kms:EncryptionContext:aws:datazone:domainId" = var.domain_id
        }
        StringLike = {
          "kms:GrantConstraintType" = "EncryptionContextSubset"
        }
        Null = {
          "kms:GrantOperations" = "false"
        }
        "ForAllValues:StringEquals" = {
          "kms:GrantOperations" = [
            "Encrypt",
            "Decrypt",
            "ReEncryptFrom",
            "ReEncryptTo",
            "GenerateDataKey",
            "GenerateDataKeyWithoutPlaintext",
            "DescribeKey",
            "RetireGrant",
            "CreateGrant",
          ]
        }
      }
    },
  ] : st if var.domain_id != null]
}

module "project_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-project"
  description = "SMUS project resources in this account - blueprint-provisioned volumes and artifacts (Stage 6). NOT the data CMK."

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "awsds-project-key-smus"
    Statement = concat(
      local.key_policy_iam_delegation,
      local.key_policy_smus_domain,
      local.key_policy_smus_project_roles,
    )
  })
}
