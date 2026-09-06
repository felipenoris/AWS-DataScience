# production/workloads/ - VPC-Workloads, the production runtime's network (Stage 6c step 1.3,
# 2026-09-06).
#
# PRIVATE BY THE ABSENCE OF ONE ROUTE, which is the whole of what distinguishes it from the hub
# next door. `public_internet_route = false` below leaves the internet gateway created and
# unattached to any path: "is this VPC private?" is then a question about a ROUTE TABLE - the
# object the answer is enforced in, which ./aws/networking.py reads and a console shows - rather
# than a question about which branch of a module ran.
#
# WHAT LANDS HERE, AND WHY THE ISOLATED TIER IS NOT IT. Stage 9's SageMaker runtime and Stage
# 10's MWAA Serverless workers take the PRIVATE tier, in TWO AZs. That two-AZ requirement is
# AWS's documented private-routing shape for MWAA Serverless and it is this estate's single D9
# exception - Stage 10 decision 3 bounds how far the duplication is allowed to go, and this
# comment exists so the exception is met as a decision rather than discovered as a bill.
#
# ITS INTERFACE ENDPOINTS ARE NOT HERE EITHER: they belong to the [E] slice
# production/workloads-egress/ (step 1.3a), which is torn down between sittings like every other
# egress slice. A VPC and its endpoints have different lifecycles, and D11 is that split.
#
# MODULES ARRIVE BY GIT TAG, NEVER BY BRANCH (docs/plan/conventions.md 6).

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

# The flow-log delivery role - the iam-role module's first caller. permissions_boundary is
# REQUIRED by the module; null here is the deliberate case: a service role authored by the
# identity that authors boundaries (Lesson 18). The role name and the log-group name are one
# contract: the vpc module creates "awsds-<env>-vpc-flow-logs" and this policy is scoped to
# exactly that group.
# THE NAME PREFIX, DERIVED ONCE (Stage 6c step 0.4, 2026-09-06). It mirrors the vpc module's own
# local so the flow-log ROLE and the LOG GROUP keep the single contract the comment above states:
# the module creates "<prefix>-vpc-flow-logs" and this policy is scoped to exactly that group.
# Empty suffix reproduces the pre-6c names byte for byte, which is what makes this slice's plan
# read `No changes` on the version bump alone.
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
        # The confused-deputy guard: only flow logs OF THIS ACCOUNT may assume the role.
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

  # THE LINE THAT MAKES THIS VPC PRIVATE, and it is a literal on purpose. Every other value this
  # slice takes is generated because it varies per environment; this one does not vary - being
  # unreachable from the internet is what VPC-Workloads IS (D38), permanently, in every region
  # this design is ever rebuilt in. A generated input would make it look like a setting.
  public_internet_route = false

  vpc_cidr          = var.vpc_cidr
  zone_ids          = var.zone_ids
  flow_log_role_arn = module.flow_log_role.role_arn
}
