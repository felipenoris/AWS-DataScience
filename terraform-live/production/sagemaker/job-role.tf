# Stage 9 step 3.1 - awsds-prod-job-exec, the role every pipeline-submitted job in this account runs
# as, and the job log groups it writes to.
#
# The name is a contract: Stage 5a step 1.4's drop-box statement and key statement in
# data-governance/data/ name it exactly, and ./aws/deploytargets.py DT-4 reads its trust and its S3
# grants. The trust admits the two job services and nothing else, so no person assumes it (D27's
# shape). iam:PassRole to it is granted in the passers' own slices (Stage 8's deploy roles, Stage 10's
# execution roles), scoped by iam:PassedToService.
#
# A SageMaker job reads no governed data: under the Workloads OU's job settings (step 3.5) its
# container has no network, and the platform stages inputs and outputs as this role, which holds no S3
# on a lake bucket (D13). The producer and the pickup are Glue jobs, which read and write the lake
# through Lake Formation's vended credentials; a SageMaker step reads what a Glue step staged into the
# outputs bucket.

locals {
  job_role_name = "awsds-${var.env}-job-exec"

  dropbox_arn    = data.terraform_remote_state.lake.outputs.bucket_arns["dropbox"]
  dropbox_prefix = data.terraform_remote_state.lake.outputs.dropbox_prefix
  lake_key_arn   = data.terraform_remote_state.lake.outputs.data_key_arn
  repository_arn = data.terraform_remote_state.registry.outputs.ecr_repository_arns["app-etl"]
  region_account = "${local.partition}:ec2:${var.region}:${local.account_id}"
}

module "job_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = local.job_role_name
  description = "Pipeline-submitted Glue and SageMaker jobs in this account (Stage 9 step 3.1): the lake through Lake Formation only, the drop-box pickup, the account's outputs and derived buckets, the application image, the job logs"

  permissions_boundary = null

  # SageMaker sends aws:SourceAccount when it assumes a job's role (the Sandbox app-etl job ran under
  # this statement, Stage 8 step 2.4). Glue's statement carries no condition: AWS Support's answer
  # quoted in prowler issue 2810 says Glue does not send the key, which would refuse every job run;
  # step 2.4's first Glue run reads it here. iam:PassRole is account-scoped, so only a principal of
  # this account can hand the role to Glue.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowSageMakerOfThisAccount"
        Effect    = "Allow"
        Principal = { Service = "sagemaker.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = local.account_id }
        }
      },
      {
        Sid       = "AllowGlue"
        Effect    = "Allow"
        Principal = { Service = "glue.amazonaws.com" }
        Action    = "sts:AssumeRole"
      },
    ]
  })

  inline_policies = {
    "job" = data.aws_iam_policy_document.job.json
  }
}

data "aws_iam_policy_document" "job" {
  # checkov:skip=CKV_AWS_111:PutMetricData takes no resource and is held to the job namespaces by its condition; the interface writes and Glue's tags are scoped to this account and region, the tags to Glue's one key, and every other write names its resource
  # checkov:skip=CKV_AWS_356:the catalog reads, the credential vending, the registry token, the Describe calls and the metrics take no narrower resource; Lake Formation answers on every catalog object (D13)

  # ------------------------------------------------------------ the lake, through Lake Formation
  #
  # The metadata reads every Lake Formation-aware engine makes, and the vending call itself. The data
  # arrives in credentials Lake Formation vends per table; this role holds no S3 on a lake bucket.
  statement {
    sid    = "ReadTheCatalogMetadata"
    effect = "Allow"
    actions = [
      "glue:BatchGetPartition",
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:GetTable",
      "glue:GetTableVersions",
      "glue:GetTables",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "VendTheLakeCredentials"
    effect    = "Allow"
    actions   = ["lakeformation:GetDataAccess"]
    resources = ["*"]
  }

  # An Iceberg commit ends in glue:UpdateTable, the metadata pointer moved on the Glue table, and
  # IAM is evaluated beside Lake Formation's ALTER (Lesson 28): the lake's curated tables, addressed
  # in the lake account's catalog, and this account's app_outputs tables, which the job writes rows
  # into. The lake account is read from its state (producer-proof.tf), never pasted.
  statement {
    sid     = "CommitTheIcebergWrites"
    effect  = "Allow"
    actions = ["glue:UpdateTable"]
    resources = [
      "arn:${local.partition}:glue:${var.region}:${local.lake_account_id}:catalog",
      "arn:${local.partition}:glue:${var.region}:${local.lake_account_id}:database/${data.terraform_remote_state.lake.outputs.database_names["curated"]}",
      "arn:${local.partition}:glue:${var.region}:${local.lake_account_id}:table/${data.terraform_remote_state.lake.outputs.database_names["curated"]}/*",
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:catalog",
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:database/app_outputs",
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:table/app_outputs/*",
    ]
  }

  # A Glue job given a network connection reads it as this role before it starts: Glue's
  # GlueJobRunnerSession called glue:GetConnection four times in Staging on 2026-10-19, as the role
  # of Stage 18 4.4's job. Read-only and held to this account's connections; step 2.4 decides
  # whether the producer has one.
  statement {
    sid     = "ReadTheJobsConnection"
    effect  = "Allow"
    actions = ["glue:GetConnection"]
    resources = [
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:catalog",
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:connection/*",
    ]
  }

  # ------------------------------------------------ the account's buckets (steps 1.1 and 1.2)
  statement {
    sid    = "ReadAndWriteTheAccountBuckets"
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${local.outputs_bucket_arn}/*", "${local.derived_bucket_arn}/*"]
  }

  statement {
    sid       = "ListTheAccountBuckets"
    effect    = "Allow"
    actions   = ["s3:GetBucketLocation", "s3:ListBucket"]
    resources = [local.outputs_bucket_arn, local.derived_bucket_arn]
  }

  # The account data CMK, through S3 alone. It is matched by its alias because production/data/
  # creates it at pass 3; the key policy there is the other half and names this role (step 1.1).
  statement {
    sid       = "UseTheAccountDataKeyThroughS3"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [local.account_key_arns]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = [local.data_key_alias]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }

  # ---------------------------------------------------- the drop-box pickup (Stage 5a step 1.4)
  #
  # The identity half of AllowProductionPickupReadDelete, AllowProductionPickupList and
  # AllowProductionPickupDecryptViaS3 in data-governance/data/. The drop-box is its own bucket (Stage
  # 5a decision 3), the one S3 grant in the lake account.
  statement {
    sid       = "PickUpFromTheDropBox"
    effect    = "Allow"
    actions   = ["s3:DeleteObject", "s3:GetObject"]
    resources = ["${local.dropbox_arn}/${local.dropbox_prefix}/*"]
  }

  statement {
    sid       = "ListTheDropBox"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.dropbox_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${local.dropbox_prefix}/*"]
    }
  }

  statement {
    sid       = "DecryptTheDropBox"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [local.lake_key_arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }

  # ------------------------------------------------------------------ the application image
  #
  # The service pulls a SageMaker job's image as this role, never through the VPC's ecr.* endpoints
  # (Stage 6i). The repository is in this account, so no repository policy is involved.
  statement {
    sid       = "MintTheRegistryToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "PullTheApplicationImage"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [local.repository_arn]
  }

  # --------------------------------------------------------------------- logs and metrics
  #
  # CreateLogGroup is granted on the declared groups alone, which exist, so a job never creates one.
  statement {
    sid    = "WriteTheJobLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
    ]
    resources = flatten([
      for arn in local.job_log_group_arns : [arn, "${arn}:*"]
    ])
  }

  statement {
    sid       = "PublishTheJobMetrics"
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values = [
        "/aws/sagemaker/ProcessingJobs",
        "/aws/sagemaker/TrainingJobs",
        "/aws/sagemaker/TransformJobs",
        "Glue",
      ]
    }
  }

  # Stage 9 step 9.4: the warehouse load, app-etl's Glue job awsds-<env>-app-etl-load, reads the
  # workgroup's endpoint and asks for temporary credentials on its database, then connects on its port
  # from the job's security group (9.1). workgroup/* because the id changes on every re-create of the
  # [E] compute; the session lands on the database user 9.3 created, IAMR:awsds-prod-job-exec, which
  # holds the schema's writes through its role, and the admin secret stays closed to this role.
  statement {
    sid       = "ConnectToTheGovernedWarehouse"
    effect    = "Allow"
    actions   = ["redshift-serverless:GetCredentials", "redshift-serverless:GetWorkgroup"]
    resources = ["arn:${local.partition}:redshift-serverless:${var.region}:${local.account_id}:workgroup/*"]
  }

  # ----------------------------------------------------------------- a job inside the VPC
  #
  # A SageMaker job in a VPC gets its interfaces from the service acting as this role (the SageMaker
  # execution role's documented list, read at 6i). A Glue job reaches the VPC through a connection and
  # also reads the route tables, the endpoints and the VPC's attributes, and tags its interfaces with
  # aws-glue-service-resource (AWSGlueServiceRole v5's EC2 statements, written here without its S3 and
  # IAM reads).
  statement {
    sid    = "DescribeTheNetwork"
    effect = "Allow"
    actions = [
      "ec2:DescribeDhcpOptions",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeRouteTables",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
      "ec2:DescribeVpcAttribute",
      "ec2:DescribeVpcEndpoints",
      "ec2:DescribeVpcs",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AttachTheJobsInterfaces"
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:CreateNetworkInterfacePermission",
      "ec2:DeleteNetworkInterface",
      "ec2:DeleteNetworkInterfacePermission",
    ]
    resources = [
      "arn:${local.region_account}:network-interface/*",
      "arn:${local.region_account}:security-group/*",
      "arn:${local.region_account}:subnet/*",
    ]
  }

  statement {
    sid     = "TagGluesInterfaces"
    effect  = "Allow"
    actions = ["ec2:CreateTags", "ec2:DeleteTags"]
    resources = [
      "arn:${local.region_account}:instance/*",
      "arn:${local.region_account}:network-interface/*",
      "arn:${local.region_account}:security-group/*",
    ]

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["aws-glue-service-resource"]
    }
  }
}

# ------------------------------------------------------------------- the job log groups
#
# Declared before any job runs, with a retention: the service that creates its own group gives it none
# (EXC-10). The names are the ones each service writes to by default. Each group is encrypted under the
# account data key, which CloudWatch Logs uses as its own service principal under production/data/'s
# AllowCloudWatchLogsForTheJobAndWorkflowGroups, scoped by the group's ARN as encryption context.
resource "aws_cloudwatch_log_group" "job" {
  # checkov:skip=CKV_AWS_338:retention is 30 days, Stage 3 decision 3's figure; the audit trail of record is CloudTrail, org-wide and Object-Locked since Stage 1d
  for_each = local.job_log_groups

  name              = each.value
  retention_in_days = var.log_retention_days
  kms_key_id        = data.terraform_remote_state.data.outputs.data_key_arn
}
