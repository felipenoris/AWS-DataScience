# deploy-role.tf - Stage 8 step 4.1 in Staging: awsds-deploy-staging, the promotion chain's role for
# steps 3.1-3.4 (INT-08), and the misuse alarm with the alerts topic it reaches (4.6, decision 5).
#
# What it does from the deploy runner: the CI/CD CLI's deploy into deploy-staging and the leg around it
# (Stage 19 steps 4.8 and 4.9), the start of the chains in staging-test, and the model chain's jobs. It
# applies no slice and writes no state: staging/egress/ is the user's `make up` / `make down` since
# decision 27 (2026-10-24), and the leg reads it before it writes (scripts/check-egress.py). Its grants
# are the inline document apply-application (apply-application.tf) and the managed policy
# deploy-project.tf attaches.
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

  # The names apply-application.tf and deploy-project.tf read, the same in production/foundation/.
  partition      = data.aws_partition.current.partition
  account_id     = data.aws_caller_identity.current.account_id
  region_account = "${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}"

  # Production's model registry (production/sagemaker/registry.tf): the deploy runner's home is that
  # account (D14), so the alias above resolves its id.
  registry_account_id = data.aws_caller_identity.deploy_runner.account_id
  registry_env        = one([for k, v in var.deploy_runner : v.env])
}

module "deploy_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.5.0"

  name            = var.deploy_role_name
  description     = "Stage 8's Staging leg (INT-08, steps 3.1-3.4) - assumed only by the deploy runner's role; deploys into deploy-staging through the CI/CD CLI, reads staging/egress/"
  env             = var.env
  runner_role_arn = local.deploy_runner_role_arn
  runner_role_id  = data.aws_iam_role.deploy_runner.unique_id
  state_prefixes  = []
  state_read_keys = [for s in ["foundation", "sagemaker", "data", "egress"] : "staging/${s}/terraform.tfstate"]

  inline_policies = {
    "apply-application" = data.aws_iam_policy_document.apply_application.json
  }

  misuse_alarm     = true
  alerts_topic_arn = aws_sns_topic.alerts.arn
}

# Staging's statements in apply-application.tf's document: the leg's read of the version it deploys,
# and the chain's machine it starts in staging-test and follows to its end (Stage 10 decision 19).
data "aws_iam_policy_document" "apply_application_in_this_account" {
  # checkov:skip=CKV_AWS_356:sagemaker:ListModelPackages has no resource type, so only "*" matches it; the registry's resource policy names this role

  # Step 3.2: the approved version, read in production/sagemaker/registry.tf's groups, whose resource
  # policy admits this role to the same two actions (Stage 9 step 3.2).
  statement {
    sid       = "ReadTheApprovedModelVersions"
    effect    = "Allow"
    actions   = ["sagemaker:DescribeModelPackage"]
    resources = ["arn:${local.partition}:sagemaker:${data.aws_region.current.region}:${local.registry_account_id}:model-package/awsds-${local.registry_env}-model-*/*"]
  }

  statement {
    sid       = "ListTheModelVersions"
    effect    = "Allow"
    actions   = ["sagemaker:ListModelPackages"]
    resources = ["*"]
  }

  statement {
    sid       = "StartTheChainInTheLeg"
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = ["arn:${local.partition}:states:${local.region_account}:stateMachine:awsds-${var.env}-chain-*"]
  }

  statement {
    sid       = "FollowTheChainInTheLeg"
    effect    = "Allow"
    actions   = ["states:DescribeExecution", "states:GetExecutionHistory"]
    resources = ["arn:${local.partition}:states:${local.region_account}:execution:awsds-${var.env}-chain-*:*"]
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
