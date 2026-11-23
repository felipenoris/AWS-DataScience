# What a model call needs in this account (Stage 17 step 10.5; decisions 22 (a), 23 (a), 24 (b) and
# 27 (a); TM-36): the application inference profile app-genai invokes, the deployment project's role's
# statements for the boundary's three sets of calls, and the account's own guardrail with the
# account-level configuration that enforces it. The boundary's half is main.tf's bedrock_exception, and
# fence.tf no longer fences bedrock. The application's own guardrail is no resource here: a task of its
# workflow creates and publishes it (decision 24 (b)).
#
# This file is one of the files staging/studio/ and production/studio/ hold as copies
# (scripts/check-copies.py).

locals {
  # Decision 23 (a)'s model, served in this Region alone: an application inference profile copied from
  # the foundation model routes to that Region and nowhere else. A foundation model's ARN carries no
  # account.
  app_genai_model_arn = "arn:${data.aws_partition.current.partition}:bedrock:${var.region}::foundation-model/amazon.nova-lite-v1:0"

  # Every guardrail of this account, and every numbered version of one: a version's ARN is the
  # guardrail's with `:<version>` appended, and the DRAFT's carries none.
  app_genai_guardrails        = "arn:${data.aws_partition.current.partition}:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:guardrail/*"
  app_genai_guardrail_version = "${local.app_genai_guardrails}:*"

  # The deployment project's id, from its role's AmazonDataZoneProject tag: AWS's
  # SageMakerStudioProjectUserRolePolicy (BRInvokeAppProfile, v77) admits the invoke of an application
  # profile that carries the role's own value (verification xli). null while project-roles.tf is empty.
  deployment_project_id = one(distinct([
    for r in var.project_roles : data.aws_iam_role.project[r].tags["AmazonDataZoneProject"]
  ]))

  stage_17_tags = { CostCenter = "stage-17" }
}

# ------------------------------------------------------------------------ the inference profile
#
# The application's MODEL_ID: scripts/deploy-application.py reads it from the output
# app_genai_inference_profile_arn as the deploy role, whose state_read_keys name this slice's state.
# Tagged with the deployment project, the shape of the profile SageMaker Unified Studio's own model
# subscription creates (decision 22), which DenyDataZoneSubscriptionRequests refuses in Workloads.
resource "aws_bedrock_inference_profile" "app_genai" {
  name        = "awsds-${var.env}-app-genai"
  description = "app-genai's model in this account: Amazon Nova Lite in this Region alone (Stage 17 decision 23 (a))."

  model_source {
    copy_from = local.app_genai_model_arn
  }

  tags = merge(
    local.stage_17_tags,
    local.deployment_project_id == null ? {} : { AmazonDataZoneProject = local.deployment_project_id },
  )
}

# ------------------------------------------------------- the account's guardrail (decision 27 (a))
#
# A guardrail of the account's own, with a denied topic the application's guardrail does not hold, so a
# trace tells the two apart: Sandbox's definition of 10.4 step 6, created there on 2026-11-22. No
# project tag, and the boundary denies the three writes on it (DenyWritingTheAccountsGuardrail), so no
# project role writes it. It stays under the AWS-owned key: a customer key meets
# DenyCustomerKeysButTheProjectKey (decision 24).
resource "aws_bedrock_guardrail" "account" {
  name                      = "awsds-${var.env}-account-guardrail"
  description               = "The account's guardrail, enforced on every model invocation of the account by the account-level configuration (Stage 17 decision 27 (a))."
  blocked_input_messaging   = "This request was blocked by the account's guardrail, awsds-${var.env}-account-guardrail."
  blocked_outputs_messaging = "This answer was withheld by the account's guardrail, awsds-${var.env}-account-guardrail."

  topic_policy_config {
    topics_config {
      name       = "Legal advice"
      definition = "Opinions or recommendations on a person's legal rights or obligations in a particular case: whether to sue, settle or sign, or how a contract, a law or a regulation applies to them."
      examples = [
        "Should I sue you over the late refund?",
        "Does my contract let me cancel without paying the fee?",
        "Can I legally withhold payment until the order arrives?",
      ]
      type = "DENY"
    }
  }

  tags = local.stage_17_tags
}

resource "aws_bedrock_guardrail_version" "account" {
  guardrail_arn = aws_bedrock_guardrail.account.guardrail_arn
  description   = "The version the account-level configuration enforces (Stage 17 decision 27 (a))."
  skip_destroy  = false
}

# The configuration names no model list, which Cloud Control's schema for
# AWS::Bedrock::EnforcedGuardrailConfiguration describes as enforced on all models (read 2026-11-23).
# awscc 1.106.0 cannot send named models alone (SUP-466). This shape has not been applied anywhere:
# Staging's apply is its first reading, and Production's waits on it. Both content controls are
# COMPREHENSIVE, which assesses content whatever its guard tags. The configuration's calls are outside
# the boundary's ceiling, and InfrastructureAccess holds them (verification xlix). The aws provider
# carries no such resource, and awscc's carries no tags.
resource "awscc_bedrock_enforced_guardrail_configuration" "account" {
  guardrail_identifier = aws_bedrock_guardrail.account.guardrail_id
  guardrail_version    = aws_bedrock_guardrail_version.account.version

  selective_content_guarding = {
    system   = "COMPREHENSIVE"
    messages = "COMPREHENSIVE"
  }
}

# ------------------------------------------------------- the project role's statements
#
# The boundary's three sets of calls, granted to the deployment project's role in its own words, so the
# path does not rest on a version of AWS's policies (TM-30). The guardrail task's statements are
# sandbox/bedrock/application.tf's, measured in Sandbox on 2026-11-22 (10.4 readings 1 and 2), with the
# task's ListTagsForResource beside its reads. The description names every statement: a description
# change replaces the policy.
resource "aws_iam_policy" "app_genai" {
  name        = "awsds-${var.env}-app-genai"
  description = "app-genai's model call on its inference profile under a published guardrail of the account, ApplyGuardrail on the account's guardrails, and the calls that keep a guardrail of the caller's project. Stage 17 step 10.5."
  policy      = data.aws_iam_policy_document.app_genai.json

  tags = local.stage_17_tags
}

data "aws_iam_policy_document" "app_genai" {
  # checkov:skip=CKV_AWS_356:ListGuardrails without an identifier and CreateGuardrail take no guardrail ARN, so only "*" matches them; the create is bound by its request tag

  statement {
    sid       = "InvokeTheApplicationsModelUnderAPublishedGuardrail"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = [aws_bedrock_inference_profile.app_genai.arn, local.app_genai_model_arn]

    condition {
      test     = "ArnLike"
      variable = "bedrock:GuardrailIdentifier"
      values   = [local.app_genai_guardrail_version]
    }
  }

  statement {
    sid       = "ApplyTheAccountsGuardrails"
    effect    = "Allow"
    actions   = ["bedrock:ApplyGuardrail"]
    resources = [local.app_genai_guardrails]
  }

  # ListGuardrails without an identifier lists the DRAFT of every guardrail of the account, and the task
  # finds its guardrail there by name.
  statement {
    sid       = "ListTheAccountsGuardrails"
    effect    = "Allow"
    actions   = ["bedrock:ListGuardrails"]
    resources = ["*"]
  }

  # The create is bound by its tags: the caller's project tag, alone, the one the task sends.
  statement {
    sid       = "CreateAGuardrailTaggedWithTheCallersProject"
    effect    = "Allow"
    actions   = ["bedrock:CreateGuardrail"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }
  }

  # The task's reads and writes on a guardrail that already carries the caller's project tag.
  statement {
    sid    = "KeepAGuardrailOfTheCallersProject"
    effect = "Allow"
    actions = [
      "bedrock:CreateGuardrailVersion",
      "bedrock:GetGuardrail",
      "bedrock:ListTagsForResource",
      "bedrock:UpdateGuardrail",
    ]
    resources = [local.app_genai_guardrails]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }
  }

  # The two tags the task writes after a publish, the definition's hash and the version, on a guardrail
  # of the caller's project. The resource tag is required, with no IfExists: an untagged guardrail
  # cannot be claimed.
  statement {
    sid       = "TagAGuardrailOfTheCallersProjectWithItsDefinition"
    effect    = "Allow"
    actions   = ["bedrock:TagResource"]
    resources = [local.app_genai_guardrails]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["awsds:definition-sha256", "awsds:definition-version"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "app_genai" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.app_genai.arn

  lifecycle {
    # A role outside this slice's D13 boundary is not a project role this estate governs.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") == module.sagemaker_prereqs.project_boundary_arn
      error_message = "${each.value} does not carry this account's D13 boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
