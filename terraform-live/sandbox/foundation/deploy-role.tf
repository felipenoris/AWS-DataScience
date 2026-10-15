# deploy-role.tf - Stage 8 step 4.2 in this Sandbox unit: awsds-deploy-devenv-sandbox, the one role
# the supply chain writes into an account people work in with (INT-18). It applies sandbox/dev-env/
# and nothing else, and it ends at the image version: the domain writes that make a version
# selectable stay the steward's, by hand (dev-env.md §B), and its ceiling denies them by name.
#
# Read from what sandbox/dev-env/ holds: the image, its versions and the two app image configurations,
# and the image role with its inline policy, which that slice owns with no ceiling. The ceiling lets
# this role change that one role and no other. The slice's cross-account read of
# production/registry/'s state is not granted here: how the pipeline reads it is pass 3's to settle.
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

locals {
  deploy_runner_role_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.deploy_runner.account_id}:role/awsds-${one([for k, v in var.deploy_runner : v.env])}-runner-deploy"

  dev_env_arn_prefix = "arn:${data.aws_partition.current.partition}:sagemaker:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}"
  dev_env_image_name = "awsds-${var.env}-dev-env"
  dev_env_image_role = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-sagemaker-image"
}

module "deploy_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.3.0"

  name            = var.deploy_role_name
  description     = "Stage 8's dev-env registration (INT-18, step 1.6) - assumed only by the deploy runner's role; applies sandbox/dev-env/, ending at the image version"
  env             = var.env
  runner_role_arn = local.deploy_runner_role_arn
  state_prefixes  = ["sandbox/dev-env/"]

  inline_policies = {
    "apply-dev-env" = data.aws_iam_policy_document.apply_dev_env.json
  }

  boundary_denies_json = data.aws_iam_policy_document.dev_env_ceiling.json
}

data "aws_iam_policy_document" "apply_dev_env" {
  # ListAliases: the provider reads an image version's aliases on every refresh and after a create,
  # read from CloudTrail on the infrastructure user's replace of version 5 (2026-10-12), so a plan of
  # the slice is refused without it although the slice sets no alias.
  statement {
    sid    = "TheImageAndItsVersions"
    effect = "Allow"
    actions = [
      "sagemaker:AddTags",
      "sagemaker:CreateImage",
      "sagemaker:CreateImageVersion",
      "sagemaker:DeleteImage",
      "sagemaker:DeleteImageVersion",
      "sagemaker:DeleteTags",
      "sagemaker:DescribeImage",
      "sagemaker:DescribeImageVersion",
      "sagemaker:ListAliases",
      "sagemaker:ListImageVersions",
      "sagemaker:ListTags",
      "sagemaker:UpdateImage",
    ]
    resources = [
      "${local.dev_env_arn_prefix}:image/${local.dev_env_image_name}",
      "${local.dev_env_arn_prefix}:image-version/${local.dev_env_image_name}/*",
    ]
  }

  statement {
    sid    = "TheAppImageConfigs"
    effect = "Allow"
    actions = [
      "sagemaker:AddTags",
      "sagemaker:CreateAppImageConfig",
      "sagemaker:DeleteAppImageConfig",
      "sagemaker:DeleteTags",
      "sagemaker:DescribeAppImageConfig",
      "sagemaker:ListTags",
      "sagemaker:UpdateAppImageConfig",
    ]
    resources = ["${local.dev_env_arn_prefix}:app-image-config/${local.dev_env_image_name}-*"]
  }

  statement {
    sid    = "TheImageRole"
    effect = "Allow"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DeleteRolePolicy",
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListRolePolicies",
      "iam:PutRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
    ]
    resources = [local.dev_env_image_role]
  }

  statement {
    sid       = "PassTheImageRoleToSageMaker"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [local.dev_env_image_role]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["sagemaker.amazonaws.com"]
    }
  }
}

# The denies particular to this account, merged into the module's ceiling: no role but the image role
# may be created, changed or passed, and none of the domain writes that make a version selectable.
data "aws_iam_policy_document" "dev_env_ceiling" {
  statement {
    sid    = "DenyRolesOtherThanTheImageRole"
    effect = "Deny"
    actions = [
      "iam:AttachRolePolicy",
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DeleteRolePermissionsBoundary",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PassRole",
      "iam:PutRolePermissionsBoundary",
      "iam:PutRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
    ]
    not_resources = [local.dev_env_image_role]
  }

  statement {
    sid    = "DenyTheDomainWrites"
    effect = "Deny"
    actions = [
      "sagemaker:CreateApp",
      "sagemaker:CreatePresignedDomainUrl",
      "sagemaker:CreateSpace",
      "sagemaker:CreateUserProfile",
      "sagemaker:DeleteApp",
      "sagemaker:DeleteDomain",
      "sagemaker:DeleteSpace",
      "sagemaker:DeleteUserProfile",
      "sagemaker:UpdateDomain",
      "sagemaker:UpdateSpace",
      "sagemaker:UpdateUserProfile",
    ]
    resources = ["*"]
  }
}
