# staging/foundation/ - Staging's [P] network (Stage 3 pass 1). One vpc-module instance plus
# its flow-log delivery role; the child private zone is in zones.tf and the peering toward the
# hub in peering-to-hub.tf.
#
# Modules are pinned by git tag, never by branch (docs/plan/conventions.md §6; Stage 3 step
# 1.1a). The host is GitHub over SSH, the transport the operator's remote already uses; moving
# to GitLab (D8, Stage 7) changes every caller's init. `terraform init` fetches these over the
# user's own git credentials, so a failure there is auth, not Terraform.

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

# The flow-log delivery role - the iam-role module's first caller. permissions_boundary is
# required by the module; null here is the deliberate case, a service role authored by the
# identity that authors boundaries (Lesson 18).
#
# The name prefix mirrors the vpc module's own local, so the role and the log group keep one
# contract: the module creates "<prefix>-vpc-flow-logs" and the policy below is scoped to
# exactly that group. An empty suffix reproduces the pre-Stage 6c names byte for byte, which is
# what makes this slice's plan read `No changes` on the version bump alone.
locals {
  name_prefix = var.name_suffix == "" ? "awsds-${var.env}" : "awsds-${var.env}-${var.name_suffix}"
}

module "flow_log_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "${local.name_prefix}-vpc-flow-logs"
  description = "VPC Flow Logs delivery to CloudWatch Logs (Stage 3 step 5)"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowVpcFlowLogsService"
        Effect    = "Allow"
        Principal = { Service = "vpc-flow-logs.amazonaws.com" }
        Action    = "sts:AssumeRole"
        # The confused-deputy guard: only flow logs of this account may assume the role.
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })

  inline_policies = {
    "deliver-to-cloudwatch-logs" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "WriteFlowLogStreams"
          Effect = "Allow"
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogGroups",
            "logs:DescribeLogStreams",
          ]
          Resource = "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.name_prefix}-vpc-flow-logs:*"
        }
      ]
    })
  }
}

module "vpc" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc?ref=vpc-v0.3.1"

  env               = var.env
  name_suffix       = var.name_suffix
  vpc_cidr          = var.vpc_cidr
  zone_ids          = var.zone_ids
  flow_log_role_arn = module.flow_log_role.role_arn
}
