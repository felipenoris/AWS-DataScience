# sandbox/foundation/ - the [P] network of a business unit's sandbox (Stage 3 pass 1).
# One vpc-module instance plus its flow-log delivery role; the sandbox.internal zone is in
# zones.tf. Pass 2 (the peering requester toward Production, the cross-account zone
# associations) lands here in its own sitting, additively.
#
# MODULES ARRIVE BY GIT TAG, NEVER BY BRANCH (docs/plan/conventions.md §6; Stage 3 step
# 1.1a). The host the first callers pin is GITHUB, over SSH - the transport the operator's
# remote already uses - and moving to GitLab (D8, Stage 7) is every caller's init changing
# with it, recorded there. `terraform init` fetches these over the user's own git
# credentials: a failure there is auth, not Terraform.

data "aws_partition" "current" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

# The flow-log delivery role - the iam-role module's first caller. permissions_boundary is
# REQUIRED by the module; null here is the deliberate case: a service role authored by the
# identity that authors boundaries (Lesson 18). The role name and the log-group name are one
# contract: the vpc module creates "awsds-<env>-vpc-flow-logs" and this policy is scoped to
# exactly that group.
module "flow_log_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-vpc-flow-logs"
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
          Resource = "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:awsds-${var.env}-vpc-flow-logs:*"
        }
      ]
    })
  }
}

module "vpc" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc?ref=vpc-v0.1.0"

  env               = var.env
  vpc_cidr          = var.vpc_cidr
  zone_ids          = var.zone_ids
  flow_log_role_arn = module.flow_log_role.role_arn
}
