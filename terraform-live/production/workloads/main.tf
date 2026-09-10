# production/workloads/ - VPC-Workloads, the production runtime's network (Stage 6c step 1.3,
# 2026-09-06).
#
# One absent route is what distinguishes it from the hub next door. `public_internet_route = false`
# below leaves the internet gateway created and unattached to any path, so "is this VPC private?"
# is a question about a route table - the object the answer is enforced in, which
# ./aws/networking.py reads and a console shows - rather than about which branch of a module ran.
#
# Stage 9's SageMaker runtime and Stage 10's MWAA Serverless workers take the private tier, in two
# AZs, not the isolated one. That two-AZ requirement is AWS's documented private-routing shape for
# MWAA Serverless and is this estate's single D9 exception; Stage 10 decision 3 bounds how far the
# duplication may go, so the exception is met as a decision rather than discovered as a bill.
#
# Its interface endpoints are not here either: they belong to the [E] slice
# production/workloads-egress/ (step 1.3a), torn down between sittings like every other egress
# slice. A VPC and its endpoints have different lifecycles, and D11 is that split.
#
# Modules arrive by git tag, never by branch (docs/plan/conventions.md 6).

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

  env         = var.env
  name_suffix = var.name_suffix

  # The line that makes this VPC private, and a literal on purpose. Every other value this slice
  # takes is generated because it varies per environment; this one does not vary - being
  # unreachable from the internet is what VPC-Workloads is (D38), in every region this design is
  # rebuilt in. A generated input would make it look like a setting.
  public_internet_route = false

  vpc_cidr          = var.vpc_cidr
  zone_ids          = var.zone_ids
  flow_log_role_arn = module.flow_log_role.role_arn
}
