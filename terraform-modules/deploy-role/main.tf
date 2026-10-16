# deploy-role - one deploy role of Stage 8 step 4 (INT-08, INT-18): the role, the ceiling it carries,
# its state access, and the alarm on anyone else assuming it. Four callers: production/, staging/ and
# sandbox/ foundation/, one deploy role per account the deploy runner reaches, and sandbox/workflows/,
# the role that deploys an application's release to the `test` project (Stage 8 decision 19). One
# module because the contract ./aws/cicd.py reads across the accounts - the runner's role as the only
# principal, sts:AssumeRole as the only action, a boundary on every role - must be one document, not
# four copies (Lesson 33).
#
# The trust names the runner's role by ARN, which IAM stores as the role's unique id: the runner's
# role must outlive its host, which is why production/foundation/ holds it as an anchor.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_kms_alias" "tfstate" {
  name = "alias/awsds-${var.env}-tfstate"
}

locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id

  state_bucket_arn = "arn:${local.partition}:s3:::awsds-${var.env}-tfstate"

  # One ceiling per account unless the caller names a second role's own (decision 19).
  boundary_name = coalesce(var.boundary_name, "awsds-${var.env}-deploy-boundary")

  # A role that applies no slice reads no state and gets no state policy: Sandbox's since Stage 8
  # decision 18, whose jobs create and delete image versions through the API.
  reads_state = length(var.state_prefixes) + length(var.state_read_keys) > 0
}

# ------------------------------------------------------------------------------- the ceiling
#
# A permissions boundary is a ceiling, not a grant, so it opens with `Allow *` and its content is the
# denies under it - the shape sagemaker-prereqs/boundary.tf argues, and the same reason checkov's
# grant rules misfire on it. What every deploy role is denied, whatever is granted to it later:
# changing a deploy role or the runner's role, and changing or removing a ceiling. The caller adds the
# denies particular to its account in `boundary_denies_json`.
data "aws_iam_policy_document" "boundary" {
  # checkov:skip=CKV_AWS_1:permissions BOUNDARY, not a grant - a total allow is the only shape a deny-shaped ceiling can have (sagemaker-prereqs/boundary.tf)
  # checkov:skip=CKV_AWS_49:idem - the "*" action IS the ceiling; the content is the Deny statements under it
  # checkov:skip=CKV_AWS_107:idem - no credential is exposed by a ceiling that grants nothing
  # checkov:skip=CKV_AWS_108:idem - a ceiling grants no read on anything
  # checkov:skip=CKV_AWS_109:idem
  # checkov:skip=CKV_AWS_110:idem - a boundary can only reduce privilege, never escalate it
  # checkov:skip=CKV_AWS_111:idem
  # checkov:skip=CKV_AWS_356:idem
  # checkov:skip=CKV2_AWS_40:idem
  source_policy_documents = var.boundary_denies_json == null ? [] : [var.boundary_denies_json]

  statement {
    sid       = "CeilingIsEverythingTheIdentityPolicyGrants"
    effect    = "Allow"
    actions   = ["*"]
    resources = ["*"]
  }

  statement {
    sid    = "DenyChangingTheDeployIdentities"
    effect = "Deny"
    actions = [
      "iam:AttachRolePolicy",
      "iam:DeleteRole",
      "iam:DeleteRolePermissionsBoundary",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PutRolePermissionsBoundary",
      "iam:PutRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
    ]
    resources = [
      "arn:${local.partition}:iam::${local.account_id}:role/awsds-deploy-*",
      "arn:${local.partition}:iam::${local.account_id}:role/awsds-*-runner-deploy",
    ]
  }

  # A deployment target's roles are the application's, and each carries the application ceiling:
  # a deploy role may create a role, or change a role's policies, only where that ceiling is on
  # it, and may remove no ceiling at all. The ceiling's own policy lands with the first
  # application slice (Stage 8 steps 2.4 and 3.0); until it exists no role can carry it, so the
  # deploy role can create none.
  dynamic "statement" {
    for_each = var.application_boundary_name == null ? [] : [1]

    content {
      sid    = "DenyRoleChangesOutsideTheApplicationCeiling"
      effect = "Deny"
      actions = [
        "iam:AttachRolePolicy",
        "iam:CreateRole",
        "iam:DeleteRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePermissionsBoundary",
        "iam:PutRolePolicy",
      ]
      resources = ["*"]

      condition {
        test     = "StringNotEquals"
        variable = "iam:PermissionsBoundary"
        values   = ["arn:${local.partition}:iam::${local.account_id}:policy/${var.application_boundary_name}"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.application_boundary_name == null ? [] : [1]

    content {
      sid       = "DenyRemovingACeiling"
      effect    = "Deny"
      actions   = ["iam:DeleteRolePermissionsBoundary"]
      resources = ["*"]
    }
  }

  statement {
    sid    = "DenyChangingTheCeilings"
    effect = "Deny"
    actions = [
      "iam:CreatePolicyVersion",
      "iam:DeletePolicy",
      "iam:DeletePolicyVersion",
      "iam:SetDefaultPolicyVersion",
      "iam:TagPolicy",
      "iam:UntagPolicy",
    ]
    resources = ["arn:${local.partition}:iam::${local.account_id}:policy/awsds-${var.env}-*-boundary"]
  }
}

resource "aws_iam_policy" "boundary" {
  name        = local.boundary_name
  description = "The ceiling of ${var.name} (Stage 8 step 4): everything its identity policies grant, minus changing a deploy identity or a ceiling, minus what the account adds."
  policy      = data.aws_iam_policy_document.boundary.json

  tags = {
    Name = local.boundary_name
  }
}

# ----------------------------------------------------------------------------------- the role
module "role" {
  source = "../iam-role"

  name                 = var.name
  description          = var.description
  permissions_boundary = aws_iam_policy.boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "OnlyTheDeployRunner"
        Effect    = "Allow"
        Principal = { AWS = var.runner_role_arn }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  inline_policies = merge(
    { for name, json in { "state" = one(data.aws_iam_policy_document.state[*].json) } : name => json if json != null },
    var.inline_policies,
  )
}

# The slices this role applies, in this account's state bucket: read and write under each prefix
# (the S3 backend's lock file sits beside the state object), read-only on the keys it only reads
# through terraform_remote_state, and the account's state key, which delegates to IAM.
data "aws_iam_policy_document" "state" {
  count = local.reads_state ? 1 : 0

  statement {
    sid       = "ListTheStatePrefixes"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.state_bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = concat([for p in var.state_prefixes : "${p}*"], var.state_read_keys)
    }
  }

  dynamic "statement" {
    for_each = length(var.state_prefixes) > 0 ? [1] : []

    content {
      sid       = "ReadAndWriteTheStateItApplies"
      effect    = "Allow"
      actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
      resources = [for p in var.state_prefixes : "${local.state_bucket_arn}/${p}*"]
    }
  }

  dynamic "statement" {
    for_each = length(var.state_read_keys) > 0 ? [1] : []

    content {
      sid       = "ReadTheStateItOnlyReads"
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = [for k in var.state_read_keys : "${local.state_bucket_arn}/${k}"]
    }
  }

  statement {
    sid       = "UseTheStateKey"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"]
    resources = [data.aws_kms_alias.tfstate.target_key_arn]
  }
}

# ------------------------------------------------------------------- the misuse alarm (4.6)
#
# An AssumeRole of this role by anyone but the runner's role, to the account's alerts topic. The caller
# is matched by its principal id, `<role unique id>:<session name>`: the role's own account records a
# caller from another account as type AWSAccount with no ARN, and both record shapes carry the principal
# id (read 2026-10-13 in Staging, and tested with EventBridge's TestEventPattern on both shapes).
# EventBridge classes STS AssumeRole as a read-only management event, and a rule in the default
# ENABLED state matches every event except those: only the state below makes the rule fire. It sees a
# successful assumption only, since a refused one records no roleArn; that one is read from the trail
# by its errorCode.
resource "aws_cloudwatch_event_rule" "misuse" {
  count = var.misuse_alarm ? 1 : 0

  name        = "awsds-${var.env}-deploy-misuse"
  description = "AssumeRole of ${var.name} by a caller other than the deploy runner's role (Stage 8 step 4.6, D14)"
  state       = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"

  event_pattern = jsonencode({
    source        = ["aws.sts"]
    "detail-type" = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource       = ["sts.amazonaws.com"]
      eventName         = ["AssumeRole"]
      requestParameters = { roleArn = [{ "equals-ignore-case" = module.role.role_arn }] }
      userIdentity      = { principalId = [{ "anything-but" = { prefix = "${var.runner_role_id}:" } }] }
    }
  })

  tags = {
    Name = "awsds-${var.env}-deploy-misuse"
  }
}

# The message names the event and leaves its record in CloudTrail: the whole event would carry the new
# session's access key id and session token into a mailbox. Every path below exists in both record
# shapes (userIdentity.arn does not, cross-account), and none is free text the caller chooses, because
# EventBridge does not escape an extracted value and a quote in one (a userAgent) would break the
# message. A multi-line string template is one quoted string per line.
resource "aws_cloudwatch_event_target" "misuse" {
  count = var.misuse_alarm ? 1 : 0

  rule      = aws_cloudwatch_event_rule.misuse[0].name
  target_id = "alerts-topic"
  arn       = var.alerts_topic_arn

  input_transformer {
    input_paths = {
      time           = "$.detail.eventTime"
      role           = "$.detail.requestParameters.roleArn"
      session        = "$.detail.requestParameters.roleSessionName"
      principal      = "$.detail.userIdentity.principalId"
      caller_type    = "$.detail.userIdentity.type"
      caller_account = "$.detail.userIdentity.accountId"
      source         = "$.detail.sourceIPAddress"
      event_id       = "$.detail.eventID"
    }
    input_template = chomp(<<-EOT
      "<aws.events.rule-name>: a deploy role was assumed by a caller other than the deploy runner's role."
      "When: <time>"
      "Role: <role>"
      "Caller: <principal> (type <caller_type>, account <caller_account>)"
      "Session name: <session>"
      "Source address: <source>"
      "CloudTrail event id: <event_id>"
      "The full record stays in CloudTrail; this message carries no credential."
    EOT
    )
  }
}
