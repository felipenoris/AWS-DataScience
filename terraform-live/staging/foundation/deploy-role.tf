# deploy-role.tf - Stage 8 step 4.1 in Staging: awsds-deploy-staging, the promotion chain's role for
# steps 3.1-3.4 (INT-08), and the misuse alarm with the alerts topic it reaches (4.6, decision 5).
#
# What it applies from the deploy runner: staging/egress/, which since 6c is interface endpoints and
# the DNS Firewall with no NAT, staging/app/* (step 3.2) and staging/orchestration/ (Stage 10). The
# egress half of its grant is below; the application half lands here, beside the application ceiling
# awsds-staging-app-boundary (step 3.0), applied by the infrastructure user.
#
# The trust names the runner's role in the runner's home, built from the runner's name and the home's
# account id, which the alias below resolves (aws/INDEX.md rule 1). Production/foundation/ must exist
# first: IAM refuses a trust policy naming a role that does not.

provider "aws" {
  alias   = "deploy_runner"
  region  = var.region
  profile = one([for k, v in var.deploy_runner : v.profile])
}

data "aws_caller_identity" "deploy_runner" {
  provider = aws.deploy_runner
}

# The runner role's unique id: the misuse rule names the runner's sessions by it (4.6).
data "aws_iam_role" "deploy_runner" {
  provider = aws.deploy_runner
  name     = local.deploy_runner_role_name
}

locals {
  deploy_runner_role_name = "awsds-${one([for k, v in var.deploy_runner : v.env])}-runner-deploy"
  deploy_runner_role_arn  = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.deploy_runner.account_id}:role/${local.deploy_runner_role_name}"

  deploy_anchor_tags = {
    CostCenter = "stage-08"
  }

  region_account = "${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}"
}

module "deploy_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.3.0"

  name            = var.deploy_role_name
  description     = "Stage 8's Staging leg (INT-08, steps 3.1-3.4) - assumed only by the deploy runner's role; applies staging/egress/ and staging/app/* slices"
  env             = var.env
  runner_role_arn = local.deploy_runner_role_arn
  runner_role_id  = data.aws_iam_role.deploy_runner.unique_id
  state_prefixes  = ["staging/egress/", "staging/app/"]
  state_read_keys = ["staging/foundation/terraform.tfstate"]

  inline_policies = {
    "apply-egress" = data.aws_iam_policy_document.apply_egress.json
  }

  application_boundary_name = "awsds-${var.env}-app-boundary"

  misuse_alarm     = true
  alerts_topic_arn = aws_sns_topic.alerts.arn
}

# What staging/egress/ (vpc-egress) creates and reads: interface endpoints in this VPC, the DNS
# Firewall's lists, rule group, rules and association, its query log and the log group that receives
# it, and the organization id the endpoint policies carry. Resolver rules and resolver endpoints are
# absent on purpose: a deploy role that could forward this VPC's DNS elsewhere could open a channel the
# firewall exists to close.
data "aws_iam_policy_document" "apply_egress" {
  # checkov:skip=CKV_AWS_111:two writes take no ARN of this account - route53:AssociateVPCWithHostedZone acts on the zone AWS owns for each endpoint, and the CloudWatch Logs delivery calls take no resource at all; every other write is scoped to this account's ARNs
  # checkov:skip=CKV_AWS_356:idem
  statement {
    sid    = "ReadTheNetworkAndTheOrganization"
    effect = "Allow"
    actions = [
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeInstances",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribePrefixLists",
      "ec2:DescribeRouteTables",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
      "ec2:DescribeVpcAttribute",
      "ec2:DescribeVpcEndpointServices",
      "ec2:DescribeVpcEndpoints",
      "ec2:DescribeVpcs",
      "organizations:DescribeOrganization",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ManageTheInterfaceEndpoints"
    effect = "Allow"
    actions = [
      "ec2:CreateVpcEndpoint",
      "ec2:DeleteVpcEndpoints",
      "ec2:ModifyVpcEndpoint",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:ec2:${local.region_account}:vpc-endpoint/*",
      "arn:${data.aws_partition.current.partition}:ec2:${local.region_account}:vpc/${module.vpc.vpc_id}",
      "arn:${data.aws_partition.current.partition}:ec2:${local.region_account}:subnet/*",
      "arn:${data.aws_partition.current.partition}:ec2:${local.region_account}:security-group/*",
    ]
  }

  statement {
    sid       = "TagTheEndpoints"
    effect    = "Allow"
    actions   = ["ec2:CreateTags", "ec2:DeleteTags"]
    resources = ["arn:${data.aws_partition.current.partition}:ec2:${local.region_account}:vpc-endpoint/*"]
  }

  # An interface endpoint with private DNS associates a zone AWS manages with the VPC, on the caller's
  # authority.
  statement {
    sid       = "AssociateTheEndpointZones"
    effect    = "Allow"
    actions   = ["route53:AssociateVPCWithHostedZone"]
    resources = ["*"]
  }

  statement {
    sid    = "ManageTheDnsFirewallAndItsQueryLog"
    effect = "Allow"
    actions = [
      "route53resolver:AssociateFirewallRuleGroup",
      "route53resolver:AssociateResolverQueryLogConfig",
      "route53resolver:CreateFirewallDomainList",
      "route53resolver:CreateFirewallRule",
      "route53resolver:CreateFirewallRuleGroup",
      "route53resolver:CreateResolverQueryLogConfig",
      "route53resolver:DeleteFirewallDomainList",
      "route53resolver:DeleteFirewallRule",
      "route53resolver:DeleteFirewallRuleGroup",
      "route53resolver:DeleteResolverQueryLogConfig",
      "route53resolver:DisassociateFirewallRuleGroup",
      "route53resolver:DisassociateResolverQueryLogConfig",
      "route53resolver:GetFirewallDomainList",
      "route53resolver:GetFirewallRuleGroup",
      "route53resolver:GetFirewallRuleGroupAssociation",
      "route53resolver:GetResolverQueryLogConfig",
      "route53resolver:GetResolverQueryLogConfigAssociation",
      "route53resolver:ListFirewallDomains",
      "route53resolver:ListFirewallRules",
      "route53resolver:ListTagsForResource",
      "route53resolver:TagResource",
      "route53resolver:UntagResource",
      "route53resolver:UpdateFirewallDomains",
      "route53resolver:UpdateFirewallRule",
      "route53resolver:UpdateFirewallRuleGroupAssociation",
    ]
    resources = ["arn:${data.aws_partition.current.partition}:route53resolver:${local.region_account}:*"]
  }

  statement {
    sid    = "TheFirewallLogGroup"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:DeleteRetentionPolicy",
      "logs:ListTagsForResource",
      "logs:ListTagsLogGroup",
      "logs:PutRetentionPolicy",
      "logs:TagLogGroup",
      "logs:TagResource",
      "logs:UntagLogGroup",
      "logs:UntagResource",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:logs:${local.region_account}:log-group:/awsds/${var.env}/dns-firewall",
      "arn:${data.aws_partition.current.partition}:logs:${local.region_account}:log-group:/awsds/${var.env}/dns-firewall:*",
    ]
  }

  # The query log writes through a log delivery the caller creates, and the delivery edits the log
  # group's resource policy; none of these calls takes a resource ARN.
  statement {
    sid    = "DeliverTheQueryLog"
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:DeleteLogDelivery",
      "logs:DescribeLogGroups",
      "logs:DescribeResourcePolicies",
      "logs:GetLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutResourcePolicy",
      "logs:UpdateLogDelivery",
    ]
    resources = ["*"]
  }
}

# --------------------------------------------------------------- the alerts topic (decision 5)
#
# The same three resources and check as production/foundation/deploy-anchors.tf, for the same reasons;
# Stage 12 adopts both topics.
resource "aws_sns_topic" "alerts" {
  # checkov:skip=CKV_AWS_26:EventBridge cannot publish to a topic under the AWS-managed SNS key, whose policy admits no service, and a key of its own costs 1 USD a month per account; the messages are CloudTrail event metadata
  name = "awsds-${var.env}-alerts"

  tags = merge(local.deploy_anchor_tags, {
    Name = "awsds-${var.env}-alerts"
  })
}

resource "aws_sns_topic_policy" "alerts" {
  arn = aws_sns_topic.alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EventBridgeRulesOfThisAccount"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alerts.arn
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count = var.alert_email == null ? 0 : 1

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

check "alerts_reach_someone" {
  assert {
    condition     = var.alert_email != null
    error_message = "awsds-${var.env}-alerts has no subscriber: the misuse alarm notifies nobody until alert_email is set in an untracked alerts.auto.tfvars (Stage 8 decision 5)."
  }
}
