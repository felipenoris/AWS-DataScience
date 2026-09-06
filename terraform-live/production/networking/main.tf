# production/networking/ - VPC-Networking, D38's hub (Stage 6c step 1.2, 2026-09-06).
#
# WHAT MAKES THIS VPC DIFFERENT FROM EVERY OTHER ONE IN THE ESTATE, and it is one sentence:
# **it is the only VPC whose public tier carries a route to an internet gateway.** Every other
# VPC in this account and every spoke is private by the ABSENCE of that route - the vpc module
# still creates a gateway in each (free, unattached to any path), because a module that varied
# its resource set per caller would make "is this VPC private?" a question about code rather
# than about a route table.
#
# WHAT IT IS NOT. It is not a shared NAT and cannot become one: peering shares an ADDRESS and
# never a PATH (Lesson 44; the AWS peering guide says it four times). A spoke reaching the
# internet through here does so as a CLIENT of an explicit HTTP/HTTPS proxy that runs on an
# instance in this VPC - an application-layer hop, not a routing one. That is D38's whole
# argument, and the reason there is no NAT gateway anywhere in the estate.
#
# AND IT CARRIES NO INTERFACE ENDPOINT WITH PRIVATE DNS - deliberately, and it is the
# structural repair of Lessons 40-43. A private hosted zone answers for its whole subtree, so
# an endpoint's private DNS inside the VPC the VPN client resolves through shadows the public
# name for the client too. The client plane and the compute plane must not share a resolver
# view; that is why endpoints live in the spokes and this VPC holds none.
#
# MODULES ARRIVE BY GIT TAG, NEVER BY BRANCH (docs/plan/conventions.md 6; Stage 3 step 1.1a).

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

  env               = var.env
  name_suffix       = var.name_suffix
  vpc_cidr          = var.vpc_cidr
  zone_ids          = var.zone_ids
  flow_log_role_arn = module.flow_log_role.role_arn
}
