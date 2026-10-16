# Stage 9 step 3.2 - the Model Registry: one package group per application or model family, each with
# its resource policy written now rather than improvised in Stage 10 (D28 item 6).
#
# The registry is the promotion boundary: a version is approved here, on the far side of the gate
# from the person who trained it. Three statements per group:
#
#   register and approve   awsds-deploy-prod alone (CreateModelPackage, UpdateModelPackage)
#   read the versions      awsds-deploy-staging, which deploys the approved one (INT-07's registry half)
#   read the status        the Sandbox readers decision 10 names, matched by aws:PrincipalArn in an
#                          account the D35 map names, so no statement carries arn:aws:iam::*:
#
# The Sandbox readers are two principals, because a data scientist reaches AWS as either: the
# persona's reserved role from a laptop or the console, and the project role from a space or a
# workflow. Each needs its own side's allow as well: the persona's ReadSageMakerStatus in identity/sso/,
# and the project role's in the SMUS managed policy (SageMakerCrossAccountPermissions, v44, read on
# AWS's page 2026-10-16: DescribeModelPackage, DescribeModelPackageGroup and ListModelPackages on any
# resource of another account). Step 3.4 measures both.
#
# Inside this account a resource policy constrains nobody an identity policy already admits, and the
# infrastructure user that writes this one is outside every claim it makes (Lesson 18).
#
# A package group costs nothing at rest. When the registry first holds a version, re-read EXC-11
# (./aws/catalog.py CT-6), whose trigger is the Model Registry being used.

locals {
  model_families = toset(["app-etl"])

  deploy_prod_arn    = data.terraform_remote_state.foundation.outputs.deploy_role_arns[var.account_folder]
  deploy_staging_arn = data.terraform_remote_state.foundation.outputs.deploy_role_arns["staging"]
  sandbox_account_id = data.aws_caller_identity.sandbox.account_id

  status_reader_patterns = [
    "arn:${local.partition}:iam::${local.sandbox_account_id}:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_DataScientistAccess_*",
    "arn:${local.partition}:iam::${local.sandbox_account_id}:role/datazone_usr_role_*",
  ]
}

resource "aws_sagemaker_model_package_group" "this" {
  for_each = local.model_families

  model_package_group_name        = "awsds-${var.env}-model-${each.key}"
  model_package_group_description = "${each.key}'s model versions: registered and approved by the Production deploy role alone (Stage 9 step 3.2, D28 item 6)"

  tags = {
    Name = "awsds-${var.env}-model-${each.key}"
  }
}

resource "aws_sagemaker_model_package_group_policy" "this" {
  for_each = aws_sagemaker_model_package_group.this

  model_package_group_name = each.value.model_package_group_name

  resource_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "RegisterAndApproveAsTheProductionDeployRole"
        Effect    = "Allow"
        Principal = { AWS = local.deploy_prod_arn }
        Action    = ["sagemaker:CreateModelPackage", "sagemaker:UpdateModelPackage"]
        Resource  = "arn:${local.partition}:sagemaker:${var.region}:${local.account_id}:model-package/${each.value.model_package_group_name}/*"
      },
      {
        Sid       = "ReadTheVersionsAsTheStagingDeployRole"
        Effect    = "Allow"
        Principal = { AWS = local.deploy_staging_arn }
        Action    = ["sagemaker:DescribeModelPackage", "sagemaker:ListModelPackages"]
        Resource  = "arn:${local.partition}:sagemaker:${var.region}:${local.account_id}:model-package/${each.value.model_package_group_name}/*"
      },
      {
        Sid       = "ReadTheStatusFromSandbox"
        Effect    = "Allow"
        Principal = { AWS = "arn:${local.partition}:iam::${local.sandbox_account_id}:root" }
        Action = [
          "sagemaker:DescribeModelPackage",
          "sagemaker:DescribeModelPackageGroup",
          "sagemaker:ListModelPackages",
        ]
        Resource = [
          each.value.arn,
          "arn:${local.partition}:sagemaker:${var.region}:${local.account_id}:model-package/${each.value.model_package_group_name}/*",
        ]
        Condition = {
          ArnLike = { "aws:PrincipalArn" = local.status_reader_patterns }
        }
      },
    ]
  })
}
