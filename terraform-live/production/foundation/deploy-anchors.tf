# deploy-anchors.tf - Stage 8 step 4's [P] half in the deploy runner's home: the runner's role, its
# instance profile and its token's container (4.3), this account's deploy role (4.1), and the misuse
# alarm with the alerts topic it reaches (4.6, decision 5). The runner's host is production/runners/'s,
# [E].
#
# The runner's role is an anchor because IAM stores a role named in a trust policy as the role's
# unique id: a role re-created under the same name is a new principal, and every deploy role would
# refuse the next session's runner. The build runner's role lives with its host because no trust
# policy names it.
#
# The names are contracts. ./aws/cicd.py reads `awsds-<env>-runner-deploy` as the runner's Name tag and
# role (CI-1, CI-4), the deploy roles by DEPLOY_ROLES' names (CI-2, CI-3) and the rule by its
# `deploy-misuse` substring (CI-7); Staging's and Sandbox's foundation/ build their trust from the
# runner's name.

# One alias per target account, each for exactly one identity read; they create nothing, so they
# carry no default_tags. The keys are fixed by var.deploy_targets' validation: Terraform cannot
# for_each a provider, so a vended Sandbox unit adds its alias here (D35).
provider "aws" {
  alias   = "deploy_staging"
  region  = var.region
  profile = var.deploy_targets["staging"].profile
}

provider "aws" {
  alias   = "deploy_sandbox"
  region  = var.region
  profile = var.deploy_targets["sandbox"].profile
}

data "aws_caller_identity" "deploy_staging" {
  provider = aws.deploy_staging
}

data "aws_caller_identity" "deploy_sandbox" {
  provider = aws.deploy_sandbox
}

# The account's state key, which delegates to IAM: the runner role's read of the registry's state
# decrypts with it (decision 14).
data "aws_kms_alias" "tfstate" {
  name = "alias/awsds-${var.env}-tfstate"
}

locals {
  deploy_runner_name = "awsds-${var.env}-runner-deploy"
  registry_state_key = "${var.account_folder}/registry/terraform.tfstate"

  deploy_anchor_tags = {
    CostCenter = "stage-08"
  }

  # Every deploy role the runner may assume: this account's own and one per target, each ARN built
  # from an account id an aliased provider resolved (aws/INDEX.md rule 1), and, keyed by name, the
  # same plus the roles a target's other slices hold (decision 19) - the runner's AssumeRole list
  # and the profiles production/runners/ renders.
  deploy_target_account_ids = {
    staging = data.aws_caller_identity.deploy_staging.account_id
    sandbox = data.aws_caller_identity.deploy_sandbox.account_id
  }
  deploy_role_arn_by_account = merge(
    { (var.account_folder) = module.deploy_role.role_arn },
    { for k, t in var.deploy_targets : k => "arn:${data.aws_partition.current.partition}:iam::${local.deploy_target_account_ids[k]}:role/${t.role}" },
  )
  deploy_role_arn_by_name = merge(
    { for k, arn in local.deploy_role_arn_by_account : reverse(split("/", arn))[0] => arn },
    merge([for k, t in var.deploy_targets : { for r in t.other_roles : r => "arn:${data.aws_partition.current.partition}:iam::${local.deploy_target_account_ids[k]}:role/${r}" }]...),
  )
  deploy_role_arns = values(local.deploy_role_arn_by_name)

  releases_bucket_arn = "arn:${data.aws_partition.current.partition}:s3:::awsds-${var.env}-releases"
}

# ------------------------------------------------------------------- the runner's role (4.3)
module "deploy_runner_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = local.deploy_runner_name
  description = "GitLab deploy runner - assumes the deploy roles; reads its token, the CA root, the deploy image and the registry's state, and nothing else (Stage 8 step 4.3, decision 14)"

  # A service role only the infrastructure user authors, as the build runner's is (Lesson 18).
  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowEc2Service"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ]

  inline_policies = {
    "deploy" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "AssumeTheDeployRoles"
          Effect   = "Allow"
          Action   = "sts:AssumeRole"
          Resource = local.deploy_role_arns
        }
      ]
    })

    "boot" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "ReadTheRegistrationToken"
          Effect   = "Allow"
          Action   = "secretsmanager:GetSecretValue"
          Resource = aws_secretsmanager_secret.deploy_runner_token.arn
        },
        # The name is production/pki/'s contract; that slice's state is not readable from here.
        {
          Sid      = "ReadTheCaRoot"
          Effect   = "Allow"
          Action   = "ssm:GetParameter"
          Resource = "arn:${data.aws_partition.current.partition}:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/datascience/${var.env}/pki/ca-root-pem"
        },
      ]
    })

    # Decision 14: a deploy job reads production/registry/'s state (the repository URLs and ARNs a
    # dev-env or application slice names) through the runner's own profile, since no other account's
    # deploy role can read this account's state bucket. One object, read only.
    "registry-state" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "ListTheRegistryState"
          Effect   = "Allow"
          Action   = "s3:ListBucket"
          Resource = "arn:${data.aws_partition.current.partition}:s3:::awsds-${var.env}-tfstate"
          Condition = {
            StringEquals = { "s3:prefix" = local.registry_state_key }
          }
        },
        {
          Sid      = "ReadTheRegistryState"
          Effect   = "Allow"
          Action   = "s3:GetObject"
          Resource = "arn:${data.aws_partition.current.partition}:s3:::awsds-${var.env}-tfstate/${local.registry_state_key}"
        },
        {
          Sid      = "DecryptTheRegistryState"
          Effect   = "Allow"
          Action   = "kms:Decrypt"
          Resource = data.aws_kms_alias.tfstate.target_key_arn
        },
      ]
    })

    # The release store (Stage 8 decision 20): a promotion leg reads the bundle a tag's release names
    # as the runner's own role, since the bucket lives in this account and no other account's deploy
    # role reaches it. The bucket and its key are production/registry/'s, applied after this slice,
    # so both are named, the key by its alias, never read from that slice's state.
    "releases" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "ListTheReleases"
          Effect   = "Allow"
          Action   = "s3:ListBucket"
          Resource = local.releases_bucket_arn
        },
        {
          Sid      = "ReadABundle"
          Effect   = "Allow"
          Action   = "s3:GetObject"
          Resource = "${local.releases_bucket_arn}/*"
        },
        {
          Sid      = "DecryptItUnderTheRegistryKey"
          Effect   = "Allow"
          Action   = "kms:Decrypt"
          Resource = "*"
          Condition = {
            "ForAnyValue:StringEquals" = { "kms:ResourceAliases" = "alias/awsds-${var.env}-registry" }
            StringEquals               = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
          }
        },
      ]
    })

    # The deploy jobs run in an image the build runner builds from this repository's toolchain
    # (Stage 8 step 3.1), pushed to a repository of its own in production/registry/.
    "deploy-image" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "MintTheRegistryToken"
          Effect   = "Allow"
          Action   = "ecr:GetAuthorizationToken"
          Resource = "*"
        },
        {
          Sid    = "PullTheDeployImage"
          Effect = "Allow"
          Action = [
            "ecr:BatchCheckLayerAvailability",
            "ecr:BatchGetImage",
            "ecr:GetDownloadUrlForLayer",
          ]
          Resource = "arn:${data.aws_partition.current.partition}:ecr:${var.region}:${data.aws_caller_identity.current.account_id}:repository/awsds-${var.env}-ecr-deploy"
        },
      ]
    })
  }
}

# The runner role's unique id: the misuse rule names the runner's sessions by it (4.6).
data "aws_iam_role" "deploy_runner" {
  name = module.deploy_runner_role.role_name
}

resource "aws_iam_instance_profile" "deploy_runner" {
  name = local.deploy_runner_name
  role = module.deploy_runner_role.role_name

  tags = merge(local.deploy_anchor_tags, {
    Name = local.deploy_runner_name
  })
}

resource "aws_secretsmanager_secret" "deploy_runner_token" {
  # checkov:skip=CKV2_AWS_57:no rotation - the token is minted in GitLab's UI (Stage 8 step 4.5) and replaced there, never by a Lambda that GitLab does not know about
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - the containment is the resource policy below, the shape of the build runner's token container
  name        = "${local.deploy_runner_name}-token"
  description = "The deploy runner's authentication token (glrt-...), copied in by the user once the runner exists in GitLab (Stage 8 step 4.5) and read by every [E] deploy runner at boot. Never written by Terraform."

  recovery_window_in_days = 30

  tags = merge(local.deploy_anchor_tags, {
    Name = "${local.deploy_runner_name}-token"
  })
}

resource "aws_secretsmanager_secret_policy" "deploy_runner_token" {
  secret_arn = aws_secretsmanager_secret.deploy_runner_token.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyValueReadExceptDeployRunnerAndInfrastructure"
        Effect    = "Deny"
        Principal = "*"
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
        Condition = {
          StringNotLike = {
            "aws:PrincipalArn" = [
              module.deploy_runner_role.role_arn,
              local.infrastructure_access_arn_pattern,
            ]
          }
        }
      }
    ]
  })
}

# -------------------------------------------------------------------- the deploy role (4.1)
#
# What it applies from the runner: production/app/* (step 3.6), and no other slice - the pipeline
# never runs `make up` or `make down ENV=production`. The application half of its grant lands with the
# first application slice (steps 2.4 and 3.0); until then it holds its state access and nothing else.
module "deploy_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.3.0"

  name            = var.deploy_role_name
  description     = "Stage 8's promotion into Production (INT-08, step 3.6) - assumed only by the deploy runner's role; applies production/app/* slices"
  env             = var.env
  runner_role_arn = module.deploy_runner_role.role_arn
  runner_role_id  = data.aws_iam_role.deploy_runner.unique_id
  state_prefixes  = ["${var.account_folder}/app/"]

  application_boundary_name = "awsds-${var.env}-app-boundary"

  misuse_alarm     = true
  alerts_topic_arn = aws_sns_topic.alerts.arn
}

# --------------------------------------------------------------- the alerts topic (decision 5)
#
# awsds-<env>-alerts: the misuse rule's target here, and the account's topic Stage 9, Stage 10 and
# Stage 12 adopt. Its subscriber is the operator's address, which no tracked file may carry: it arrives
# from an untracked alerts.auto.tfvars the user writes, and the check below says on every plan when it
# has not.
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
