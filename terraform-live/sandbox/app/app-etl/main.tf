# sandbox/app/app-etl/ - the application, run in Sandbox by hand while it is engineered (Stage 8 step
# 2.4, decision 12). Layer [E]: `make down ENV=sandbox` destroys it, and `make up` never applies it
# (layers.py refusal 7); the infrastructure user applies it, never a pipeline (refusal 8).
#
# What it holds is what a SageMaker processing job needs to run the application image here: the job's
# execution role and its security group. The job itself is not a Terraform resource; outputs.tf carries
# its request, and a person submits it (the stage file's 2.4). Its output lands in sandbox/data/'s
# awsds-<env>-outputs under the account's data key, which admits this role by the statement there.
#
# The role's name is a contract with that statement, awsds-<env>-app-*-job, and with the pull grant on
# awsds-prod-ecr-app-etl, which admits this account (production/registry/, APP_REGISTRY_CONSUMERS). The
# image is pulled by the service as this role, outside the VPC (Stage 6i), so the security group admits
# only the two destinations a job with networking off still has: S3, through the gateway endpoint, for
# its outputs, and the VPC's interface endpoints, for its logs.

locals {
  job_name = "awsds-${var.env}-app-etl-job"

  repository_arn = data.terraform_remote_state.registry.outputs.ecr_repository_arns["app-etl"]
  data_key_arn   = data.terraform_remote_state.data.outputs.data_key_arn
  outputs_arn    = data.terraform_remote_state.data.outputs.outputs_bucket_arn
  region_account = "${data.aws_partition.current.partition}:ec2:${var.region}:${data.aws_caller_identity.current.account_id}"
}

module "job_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = local.job_name
  description = "app-etl's processing jobs in Sandbox (Stage 8 step 2.4): pull the application image, write its outputs prefix under the data key, log"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowSageMakerOfThisAccount"
        Effect    = "Allow"
        Principal = { Service = "sagemaker.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })

  inline_policies = {
    "job" = data.aws_iam_policy_document.job.json
  }
}

data "aws_iam_policy_document" "job" {
  # checkov:skip=CKV_AWS_111:the network-interface writes a VPC job makes take no resource SageMaker names in advance; they are scoped to this account's region below, and every other write names its resource
  # checkov:skip=CKV_AWS_356:idem - the registry token and the Describe calls take no resource at all
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

  statement {
    sid       = "WriteItsOutputsPrefix"
    effect    = "Allow"
    actions   = ["s3:PutObject", "s3:AbortMultipartUpload"]
    resources = ["${local.outputs_arn}/app-etl/*"]
  }

  statement {
    sid       = "ListItsOutputsPrefix"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.outputs_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["app-etl/*"]
    }
  }

  # The identity half of the data key; the key's own statement in sandbox/data/ is the other.
  statement {
    sid       = "EncryptItsOutputs"
    effect    = "Allow"
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = [local.data_key_arn]
  }

  # The job's volume is encrypted under the same key through a grant the service creates; the key
  # delegates its administrative actions, CreateGrant among them, to IAM, and the grant may only be
  # one AWS makes for its own resource.
  statement {
    sid       = "LetTheServiceEncryptTheVolume"
    effect    = "Allow"
    actions   = ["kms:CreateGrant", "kms:DescribeKey"]
    resources = [local.data_key_arn]

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }

  statement {
    sid    = "LogToTheProcessingJobsGroup"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/sagemaker/ProcessingJobs",
      "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/sagemaker/ProcessingJobs:*",
    ]
  }

  statement {
    sid       = "PublishTheJobMetrics"
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["/aws/sagemaker/ProcessingJobs"]
    }
  }

  # A job in a VPC gets its interfaces from the service acting as this role.
  statement {
    sid    = "DescribeTheNetwork"
    effect = "Allow"
    actions = [
      "ec2:DescribeDhcpOptions",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
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
      "arn:${local.region_account}:subnet/*",
      "arn:${local.region_account}:security-group/${aws_security_group.job.id}",
    ]
  }
}

# EC2 takes a group or rule description in a-zA-Z0-9 and . _-:/()#,@[]+=&;{}!$* alone, and refuses the
# apostrophe at apply, never at plan.
resource "aws_security_group" "job" {
  # checkov:skip=CKV2_AWS_5:attached by the processing jobs this slice's request starts, which Terraform does not create
  name        = local.job_name
  description = "app-etl processing jobs in Sandbox (Stage 8 step 2.4): no ingress; HTTPS to S3 and to the interface endpoints of the VPC"
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

  tags = {
    Name = local.job_name
  }
}

resource "aws_vpc_security_group_egress_rule" "s3" {
  security_group_id = aws_security_group.job.id
  description       = "S3 through the gateway endpoint - the outputs of the job"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  prefix_list_id    = data.aws_vpc_endpoint.s3.prefix_list_id
}

resource "aws_vpc_security_group_egress_rule" "endpoints" {
  security_group_id = aws_security_group.job.id
  description       = "the interface endpoints of the VPC - the logs of the job"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = data.terraform_remote_state.foundation.outputs.vpc_cidr
}
