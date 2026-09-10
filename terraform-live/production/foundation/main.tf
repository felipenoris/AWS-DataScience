# production/foundation/ - Production's [P] network (Stage 3 pass 1), built now because
# Stage 7 (GitLab) cannot start before it exists (D14). One vpc-module instance plus its
# flow-log delivery role; the awsds.internal apex and awsds-pages.internal are in zones.tf. Pass 2
# (the peering accepter - Sandbox and nothing else, step 6.2, since 6c step 3.1 retired the
# Staging one - and the association authorizations of 4.4, as a for_each over a map of peers so
# the second apply is additive) lands here in its own sitting.
#
# Modules arrive by git tag, never by branch (docs/plan/conventions.md §6; Stage 3 step 1.1a). The
# first callers pin GitHub over SSH, the transport the operator's remote already uses; moving to
# GitLab (D8, Stage 7) changes every caller's init, recorded there. `terraform init` fetches these
# over the user's own git credentials, so a failure there is auth, not Terraform.

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

# The flow-log delivery role - the iam-role module's first caller. permissions_boundary is required
# by the module; null here is the deliberate case, a service role authored by the identity that
# authors boundaries (Lesson 18). The role name and the log-group name are one contract: the vpc
# module creates "<prefix>-vpc-flow-logs" and this policy is scoped to exactly that group.
#
# The prefix is derived once (Stage 6c step 0.4, 2026-09-06) and mirrors the vpc module's own
# local, so the role and the log group keep that contract. An empty suffix reproduces the pre-6c
# names byte for byte, which is what makes this slice's plan read `No changes` on the version bump
# alone.
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
