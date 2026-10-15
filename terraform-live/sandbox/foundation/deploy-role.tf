# deploy-role.tf - Stage 8 step 4.2 in this Sandbox unit: awsds-deploy-devenv-sandbox, the one role
# the supply chain writes into an account people work in with (INT-18). Since Stage 8 decision 18 it
# applies no slice: awsds/dev-env's register job creates the house image's version through the API, and
# its retire job deletes every version past the newest 10 that no space names. The domain writes stay
# the steward's, by hand (dev-env.md §B), and its ceiling denies them by name.
#
# The grants are what awsds/dev-env's release/versions.py calls: the dev-env image found by name, its
# versions created, read and deleted, their aliases read, and every space and domain read for the
# version it names. No IAM and no state: CreateImageVersion has no dependent action in the service authorization
# reference (read 2026-10-15), and SageMaker reads the repository as the role the image carries.
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
}

module "deploy_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.4.0"

  name            = var.deploy_role_name
  description     = "Stage 8's dev-env registration (INT-18, step 1.6, decision 18) - assumed only by the deploy runner's role; creates and retires the house image's versions, and applies no slice"
  env             = var.env
  runner_role_arn = local.deploy_runner_role_arn
  state_prefixes  = []

  inline_policies = {
    "dev-env-versions" = data.aws_iam_policy_document.dev_env_versions.json
  }

  boundary_denies_json = data.aws_iam_policy_document.dev_env_ceiling.json
}

data "aws_iam_policy_document" "dev_env_versions" {
  # The three list calls take no resource type, so "*" is their only form.
  statement {
    sid       = "FindTheImageTheSpacesAndTheDomains"
    effect    = "Allow"
    actions   = ["sagemaker:ListDomains", "sagemaker:ListImages", "sagemaker:ListSpaces"]
    resources = ["*"]
  }

  statement {
    sid    = "TheImageItsVersionsAndTheirAliases"
    effect = "Allow"
    actions = [
      "sagemaker:CreateImageVersion",
      "sagemaker:DeleteImageVersion",
      "sagemaker:DescribeImage",
      "sagemaker:DescribeImageVersion",
      "sagemaker:ListAliases",
      "sagemaker:ListImageVersions",
    ]
    resources = [
      "${local.dev_env_arn_prefix}:image/${local.dev_env_image_name}",
      "${local.dev_env_arn_prefix}:image-version/${local.dev_env_image_name}/*",
    ]
  }

  statement {
    sid       = "ReadTheSpacesAndTheDomains"
    effect    = "Allow"
    actions   = ["sagemaker:DescribeDomain", "sagemaker:DescribeSpace"]
    resources = ["${local.dev_env_arn_prefix}:domain/*", "${local.dev_env_arn_prefix}:space/*"]
  }
}

# The denies particular to this account, merged into the module's ceiling: no role created, changed or
# passed, and none of the domain writes that make a version selectable or repair a space.
data "aws_iam_policy_document" "dev_env_ceiling" {
  statement {
    sid    = "DenyEveryRoleChange"
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
    resources = ["*"]
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
