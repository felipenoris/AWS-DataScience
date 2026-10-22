# app-boundary.tf - Stage 8 step 3.0: awsds-<env>-app-boundary, the ceiling every role the pipeline
# creates in this account carries. The deploy role's own ceiling refuses iam:CreateRole and every
# role-policy write on a role without it (DenyRoleChangesOutsideTheApplicationCeiling) and any change
# to it (DenyChangingTheCeilings, terraform-modules/deploy-role), so it is [P], the infrastructure
# user's, and exists before the first pipeline apply that creates a role.
#
# An allow-list of what Stage 10's workflow execution roles and chain roles do (its steps 1.3, 3.4 and
# 3.6): the jobs they start, one role to pass, the outputs bucket and the data key. What it does not
# allow it refuses, so no role the pipeline creates reaches a lake bucket, Lake Formation, another key
# or another role. The job role, awsds-<env>-job-exec, is Stage 9's [P] role and carries none.
#
# The same file in staging/foundation/ and production/foundation/, byte for byte
# (./scripts/check-copies.py).

locals {
  application_boundary_name = "awsds-${var.env}-app-boundary"

  # Built from the name, so the deploy role's documents that name the ceiling are known at plan time.
  application_boundary_arn = "arn:${local.partition}:iam::${local.account_id}:policy/${local.application_boundary_name}"
}

data "aws_iam_policy_document" "application_boundary" {
  # checkov:skip=CKV_AWS_111:a permissions boundary: the bounded roles' own policies carry the resources, and the boundary scopes S3, KMS and PassRole itself
  # checkov:skip=CKV_AWS_356:idem
  statement {
    sid    = "TheWorkflowsAndTheirJobs"
    effect = "Allow"
    actions = [
      "airflow-serverless:GetWorkflowRun",
      "airflow-serverless:StartWorkflowRun",
      "glue:BatchStopJobRun",
      "glue:GetJob",
      "glue:GetJobRun",
      "glue:GetJobRuns",
      "glue:StartJobRun",
      "sagemaker:AddTags",
      "sagemaker:CreateProcessingJob",
      "sagemaker:CreateTrainingJob",
      "sagemaker:DescribeProcessingJob",
      "sagemaker:DescribeTrainingJob",
      "sagemaker:StopProcessingJob",
      "sagemaker:StopTrainingJob",
      "states:StartExecution",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "PassOnlyTheJobRoleToSageMaker"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-job-exec"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["sagemaker.amazonaws.com"]
    }
  }

  statement {
    sid       = "TheOutputsBucketOnly"
    effect    = "Allow"
    actions   = ["s3:DeleteObject", "s3:GetObject", "s3:PutObject"]
    resources = ["arn:${local.partition}:s3:::awsds-${var.env}-outputs/*"]
  }

  statement {
    sid       = "ListTheOutputsBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:${local.partition}:s3:::awsds-${var.env}-outputs"]
  }

  statement {
    sid       = "TheDataKeyOnly"
    effect    = "Allow"
    actions   = ["kms:CreateGrant", "kms:Decrypt", "kms:DescribeKey", "kms:GenerateDataKey"]
    resources = ["arn:${local.partition}:kms:${local.region_account}:key/*"]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-data"]
    }
  }

  statement {
    sid    = "TheLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:CreateLogStream",
      "logs:DeleteLogDelivery",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:DescribeResourcePolicies",
      "logs:GetLogDelivery",
      "logs:GetLogEvents",
      "logs:ListLogDeliveries",
      "logs:PutLogEvents",
      "logs:PutResourcePolicy",
      "logs:UpdateLogDelivery",
    ]
    resources = ["*"]
  }
}

# IAM has no call that changes a managed policy's description: a change plans the replacement of the
# ceiling every application role carries.
resource "aws_iam_policy" "application_boundary" {
  name        = local.application_boundary_name
  description = "The ceiling of every role the pipeline creates in this account (Stage 8 step 3.0): what Stage 10's workflow and chain roles do, on the outputs bucket and the data key alone"
  policy      = data.aws_iam_policy_document.application_boundary.json

  tags = merge(local.deploy_anchor_tags, {
    Name = local.application_boundary_name
  })
}
