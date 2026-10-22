# Stage 9 step 4.3 - awsds-staging-job-exec, the role every pipeline-submitted job in this account runs
# as, and the job log groups it writes to: step 3.1's role in Production, written for the account
# that rehearses it (D20), so a permission a job lacks fails here before the gate.
#
# The name is a contract: Stage 8 step 2.5 makes Stage 9's awsds-<env>-job-exec the job role in
# Staging and Production (the user's decision of 2026-10-22), Stage 10 decision 6's render table maps
# it per account, and ./aws/deploytargets.py DT-4 reads its trust and its S3 grants. The trust admits
# the two job services and nothing else, so no person assumes it (D27's shape). iam:PassRole to it is
# granted in the passers' own slices (awsds-deploy-staging, Stage 10's execution roles), scoped by
# iam:PassedToService.
#
# What Production's role holds and this one does not: the drop-box pickup, since D20 keeps this
# account off the lake. What it holds that Production's role reads from Data Governance, it reads
# from the mirror here, through Lake Formation alone (step 4.1).

module "job_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-job-exec"
  description = "Pipeline-submitted Glue and SageMaker jobs in this account (Stage 9 step 4.3): the mirror through Lake Formation only, the account's outputs and derived buckets, the application image, the job logs"

  permissions_boundary = null

  # The trust of production/sagemaker/job-role.tf, statement for statement: SageMaker sends
  # aws:SourceAccount when it assumes a job's role, and Glue's statement carries no condition, since
  # AWS Support's answer quoted in prowler issue 2810 says Glue does not send the key (step 2.4 reads
  # it). iam:PassRole is account-scoped, so only a principal of this account can hand the role to Glue.
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

  # ---------------------------------------------------------- the mirror, through Lake Formation
  #
  # The metadata reads every Lake Formation-aware engine makes, and the vending call itself. The
  # mirror's data arrives in credentials Lake Formation vends per table (step 4.1 registers its
  # location); this role holds no S3 on awsds-<env>-data, as Production's holds none on the lake.
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
    sid       = "VendTheMirrorCredentials"
    effect    = "Allow"
    actions   = ["lakeformation:GetDataAccess"]
    resources = ["*"]
  }

  # A Glue job given a network connection reads it as this role before it starts: Glue's
  # GlueJobRunnerSession called glue:GetConnection four times in this account on 2026-10-19, as the
  # role of Stage 18 4.4's job. Read-only and held to this account's connections.
  statement {
    sid     = "ReadTheJobsConnection"
    effect  = "Allow"
    actions = ["glue:GetConnection"]
    resources = [
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:catalog",
      "arn:${local.partition}:glue:${var.region}:${local.account_id}:connection/*",
    ]
  }

  # ---------------------------------------------------- the account's buckets (steps 4.1, 4.2)
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

  # The account data CMK, through S3 alone. It is matched by its alias because staging/data/
  # creates it at step 4.1; the key policy there is the other half and names this role.
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

  # ------------------------------------------------------------------ the application image
  #
  # The service pulls a SageMaker job's image as this role, never through the VPC's ecr.* endpoints
  # (6i; Stage 18 4.4 read the same pull in this account on 2026-10-19, session SageMaker). The
  # repository is Production's: its policy admits this account (Stage 8 step 3.0, applied
  # 2026-10-19), and this statement is the identity half a cross-account pull needs. ECR decrypts
  # the layers through its own grants on the repository key, so no KMS statement rides with it (7.3).
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
      for group in aws_cloudwatch_log_group.job : [group.arn, "${group.arn}:*"]
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

  # ----------------------------------------------------------------- a job inside the VPC
  #
  # The statements of production/sagemaker/job-role.tf: a SageMaker job in a VPC gets its interfaces
  # from the service acting as this role, and a Glue job reaches the VPC through a connection, reads
  # the route tables, the endpoints and the VPC's attributes, and tags its interfaces with
  # aws-glue-service-resource (AWSGlueServiceRole v5's EC2 statements, without its S3 and IAM reads).
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
# (EXC-10). Stage 18 4.4's job created /aws/sagemaker/ProcessingJobs here on 2026-10-19 and its pass 8
# deleted it on 2026-10-22; a group a job creates before this apply is imported, never re-created
# (ResourceAlreadyExistsException), and the apply then sets its retention.
resource "aws_cloudwatch_log_group" "job" {
  # checkov:skip=CKV_AWS_158:the account data CMK is staging/data/'s and arrives at step 4.1 with the CloudWatch Logs statement step 1.1 lists; the groups move under it then, and carry the AWS-owned key until that apply
  # checkov:skip=CKV_AWS_338:retention is 30 days, the figure of Production's job groups; the audit trail of record is CloudTrail, org-wide and Object-Locked since Stage 1d
  for_each = local.job_log_groups

  name              = each.value
  retention_in_days = var.log_retention_days
}
