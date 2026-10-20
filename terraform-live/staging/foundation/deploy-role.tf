# deploy-role.tf - Stage 8 step 4.1 in Staging: awsds-deploy-staging, the promotion chain's role for
# steps 3.1-3.4 (INT-08), and the misuse alarm with the alerts topic it reaches (4.6, decision 5).
#
# What it applies from the deploy runner: staging/egress/, which since 6c is interface endpoints and
# the DNS Firewall with no NAT, and staging/app/* (step 3.2). The egress half of its grant is below;
# the application half lands with staging/app/app-etl/ (step 3.0).
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
    # Stage 18 step 4.3, for the stage's life: the CLI's deploy into the deployment project.
    "deployment-project-reads"     = data.aws_iam_policy_document.deployment_project_reads.json
    "deployment-project-workflows" = data.aws_iam_policy_document.deployment_project_workflows.json
    "deployment-project-storage"   = data.aws_iam_policy_document.deployment_project_storage.json
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

# ----------------------------------------- Stage 18 step 4.3: the deploy into the deployment project
#
# The CLI 1.0.9's `deploy --targets staging` and `run` as this role, into `deploy-staging`: the grants
# sandbox/workflows/deploy-role.tf gives the test deploy role, scoped to this project, from what 4.2's
# CloudTrail list read under InfrastructureAccess (2026-10-19). Without the DataZone environment and
# connection reads the CLI creates the workflow in the service's own network under an AWS-owned key and
# prints one line (Stage 18 PR #189). Nothing here reads another slice's object: the project role and the
# key are named, not looked up, so Stage 18 step 8.1 deletes the project and this slice still plans; step
# 8.8 removes the three documents. DataZone's membership layer is not IAM: the role is made an owner of
# the project by hand (EXC-17).
locals {
  deployment_project_role_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/${var.deployment_project_role}"
  # The project's id, the second segment of its role's name, datazone_usr_role_<project>_<environment>.
  deployment_project_id = regex("^datazone_usr_role_([a-z0-9]+)_", var.deployment_project_role)[0]
  # Where the CLI writes: <domain>/<project>/shared/ in the projects bucket, the application's folders
  # and operatorFiles/ under it.
  deployment_projects_bucket_arn = "arn:${data.aws_partition.current.partition}:s3:::awsds-${var.env}-smus-projects"
  deployment_shared_prefix       = "${var.datazone_domain_id}/${local.deployment_project_id}/shared/"
  deployment_workflows           = "arn:${data.aws_partition.current.partition}:airflow-serverless:${local.region_account}:workflow/*"
  deployment_log_groups          = "arn:${data.aws_partition.current.partition}:logs:${local.region_account}:log-group:/aws/mwaa-serverless/${var.datazone_domain_id}-${local.deployment_project_id}/*"
  deployment_keys                = "arn:${data.aws_partition.current.partition}:kms:${local.region_account}:key/*"
}

# The CLI resolves the domain, the project, its membership, its environments and its connections before
# it copies anything; GetDomain alone takes a resource type, the domain's ARN in the domain account.
data "aws_iam_policy_document" "deployment_project_reads" {
  statement {
    sid    = "ReadTheProjectItsMembersAndItsConnections"
    effect = "Allow"
    actions = [
      "datazone:GetConnection",
      "datazone:GetEnvironment",
      "datazone:GetGroupProfile",
      "datazone:GetProject",
      "datazone:GetUserProfile",
      "datazone:ListConnections",
      "datazone:ListDomains",
      "datazone:ListEnvironmentBlueprints",
      "datazone:ListEnvironments",
      "datazone:ListProjectMemberships",
      "datazone:ListProjects",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadTheDomain"
    effect    = "Allow"
    actions   = ["datazone:GetDomain"]
    resources = ["arn:${data.aws_partition.current.partition}:datazone:${var.region}:*:domain/${var.datazone_domain_id}"]
  }
}

# The workflow calls, on a workflow tagged with the project: the CLI tags the workflow at its creation,
# and the tag scopes every later call. ListWorkflows takes no resource type.
data "aws_iam_policy_document" "deployment_project_workflows" {
  statement {
    sid       = "ListTheWorkflows"
    effect    = "Allow"
    actions   = ["airflow-serverless:ListWorkflows"]
    resources = ["*"]
  }

  statement {
    sid       = "CreateAWorkflowOfTheProject"
    effect    = "Allow"
    actions   = ["airflow-serverless:CreateWorkflow"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [local.deployment_project_id]
    }
  }

  # TagResource may re-apply the project tag with the project's own value and never another's.
  statement {
    sid    = "UpdateTagRunAndReadAWorkflowOfTheProject"
    effect = "Allow"
    actions = [
      "airflow-serverless:GetTaskInstance",
      "airflow-serverless:GetWorkflow",
      "airflow-serverless:GetWorkflowRun",
      "airflow-serverless:ListTagsForResource",
      "airflow-serverless:ListTaskInstances",
      "airflow-serverless:ListWorkflowRuns",
      "airflow-serverless:ListWorkflowVersions",
      "airflow-serverless:StartWorkflowRun",
      "airflow-serverless:TagResource",
      "airflow-serverless:UpdateWorkflow",
    ]
    resources = [local.deployment_workflows]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = [local.deployment_project_id]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [local.deployment_project_id]
    }
  }

  # CreateWorkflow and UpdateWorkflow pass the project role to the service the workflow runs as.
  statement {
    sid       = "PassTheProjectRoleToTheService"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [local.deployment_project_role_arn]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["airflow-serverless.amazonaws.com"]
    }
  }

  # The workflow's log group, created in the caller's session at the workflow's creation; an update
  # meets it and lists the account's groups (sandbox/workflows/deploy-role.tf, measured 2026-10-19).
  statement {
    sid       = "CreateAndReadTheWorkflowsLogGroup"
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup", "logs:FilterLogEvents", "logs:GetLogEvents"]
    resources = [local.deployment_log_groups]
  }

  statement {
    sid       = "DescribeTheLogGroupsOnUpdate"
    effect    = "Allow"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["arn:${data.aws_partition.current.partition}:logs:${local.region_account}:log-group:*"]
  }
}

# The project's shared/ prefix in the projects bucket, and the project key it encrypts under, named by
# its alias so that no key is looked up: the data keys of the uploads, the reads and the run's start,
# and the grants the service creates on the caller's behalf at the workflow's creation.
data "aws_iam_policy_document" "deployment_project_storage" {
  statement {
    sid       = "ListTheProjectsSharedPrefix"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.deployment_projects_bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${local.deployment_shared_prefix}*"]
    }
  }

  statement {
    sid       = "ReadAndWriteUnderTheProjectsSharedPrefix"
    effect    = "Allow"
    actions   = ["s3:AbortMultipartUpload", "s3:GetObject", "s3:PutObject"]
    resources = ["${local.deployment_projects_bucket_arn}/${local.deployment_shared_prefix}*"]
  }

  statement {
    sid       = "UseTheProjectKey"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:DescribeKey", "kms:GenerateDataKey"]
    resources = [local.deployment_keys]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-project"]
    }
  }

  statement {
    sid       = "LetTheServiceGrantItselfTheProjectKey"
    effect    = "Allow"
    actions   = ["kms:CreateGrant"]
    resources = [local.deployment_keys]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-project"]
    }

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
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
