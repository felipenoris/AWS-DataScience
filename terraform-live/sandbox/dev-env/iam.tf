# The role the image object carries.
#
# CreateImage requires a RoleArn and the API stores it on the image; the vendor's console flow
# offers to attach AmazonSageMakerFullAccess to it, which this estate does not do to any principal
# (D31, and the IAM rules in docs/plan/conventions.md). What the role is asked to do here is bounded
# and knowable: the image and its version are metadata about a container in another account's
# repository, so the role gets that account's two repositories and nothing else.
#
# What the role is NOT is the principal that pulls the image when a space starts. That is the
# project role the Tooling blueprint authors, under the D13 boundary, and the pull is a second grant
# in a second account - the repository policy's AllowConsumerAccountsToPull is the other half
# (Lesson 28). Step 2.5 measures which principal CloudTrail records; until it has, this role's
# permissions are a floor, not a description.
#
# No KMS statement: both repositories encrypt under the registry CMK, and ECR holds its own grants
# on that key and decrypts on the caller's behalf (terraform-live/production/registry/kms.tf).
#
# No permissions boundary: the rule in docs/plan/conventions.md binds roles a non-administrator can
# create or influence. This one is authored by the infrastructure user in code, is assumable only by
# the SageMaker service in this account, and holds four read actions.

data "aws_iam_policy_document" "image_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }

    # The confused-deputy guard: the service may assume this role only on this account's behalf.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

data "aws_iam_policy_document" "image_read" {
  statement {
    sid    = "ReadTheDevEnvImage"
    effect = "Allow"

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:DescribeImages",
      "ecr:GetDownloadUrlForLayer",
    ]

    # The four actions the repository policy admits, on the two repositories that exist. Both ARNs
    # are read from the registry's own state: an ARN carries the account id, and the pair has to
    # agree with the repository policy or the grant is half a grant (Lesson 28).
    resources = values(data.terraform_remote_state.registry.outputs.ecr_repository_arns)
  }

  statement {
    sid       = "GetAnEcrToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
}

module "image_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-sagemaker-image"
  description          = "The role the dev-env SageMaker image carries (Stage 6d step 2.1) - read on the registry account's two repositories, and nothing else."
  assume_role_policy   = data.aws_iam_policy_document.image_trust.json
  permissions_boundary = null

  inline_policies = {
    "ecr-read" = data.aws_iam_policy_document.image_read.json
  }
}
