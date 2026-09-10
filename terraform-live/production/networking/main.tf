# production/networking/ - VPC-Networking, D38's hub (Stage 6c step 1.2, 2026-09-06).
#
# This is the only VPC in the estate whose public tier carries a route to an internet gateway.
# Every other VPC here, and every spoke, is private by the absence of that route; the vpc module
# still creates a gateway in each (free, on no path), so "is this VPC private?" stays a question
# about a route table rather than about code.
#
# It is not a shared NAT and cannot become one: peering shares an address, never a path (Lesson
# 44). A spoke reaching the internet through here does so as a client of an explicit HTTP/HTTPS
# proxy running on an instance in this VPC - an application-layer hop, not a routing one, and the
# reason there is no NAT gateway anywhere in the estate (D38).
#
# It carries no interface endpoint with private DNS (Lessons 40-43). A private hosted zone answers
# for its whole subtree, so an endpoint's private DNS inside the VPC the VPN client resolves
# through would shadow the public name for the client too. The client plane and the compute plane
# must not share a resolver view, so endpoints live in the spokes and this VPC holds none.
#
# Modules arrive by git tag, never by branch (docs/plan/conventions.md 6; Stage 3 step 1.1a).

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

# The name prefix, derived once (Stage 6c step 0.4, 2026-09-06). It mirrors the vpc module's own
# local so that the flow-log role and the log group keep one contract: the module creates
# "<prefix>-vpc-flow-logs" and the role's policy below is scoped to exactly that group. An empty
# suffix reproduces the pre-6c names byte for byte, which is what makes this slice's plan read
# `No changes` on the version bump alone.
locals {
  name_prefix = var.name_suffix == "" ? "awsds-${var.env}" : "awsds-${var.env}-${var.name_suffix}"
}

# The flow-log delivery role, the iam-role module's first caller. permissions_boundary is required
# by the module; null here is the deliberate case, a service role authored by the identity that
# authors boundaries (Lesson 18).
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
        # The confused-deputy guard: only this account's flow logs may assume the role.
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
