# The Bedrock grant for an application's `dev` project (Stage 17 step 10.4; decisions 22 (a), 24 (b)
# and 27 (a)), attached to the roles in application_roles alone: app-genai-dev's.
#
# AWS's SageMakerStudioProjectUserRolePolicy v77 already gives such a role the invoke of an
# application inference profile tagged with its project (BRInvokeAppProfile), of a system inference
# profile and of a foundation model (ACInvoke), ApplyGuardrail and ListTagsForResource on a resource
# tagged with its project (BedrockResourceAccessPermissions), and TagResource for the AmazonDataZone*
# keys (BedrockTagResourcePermissions); read by simulation as app-genai-dev's role on 2026-11-19
# (10.1's set). What it lacks is what app-genai's `guardrail` task calls: list, create, read, update,
# publish and tag the application's own guardrail. This policy holds those and no invoke.
#
# Two switches, both false between sittings:
#   - application_guardrail_required adds a deny of an invocation that names no numbered version of a
#     guardrail of this account (10.4 step 4).
#   - account_guardrail_enabled creates the account's guardrail, its version and the account-level
#     configuration that enforces it on enforced_models (10.4 step 6). The configuration is the
#     account's, so the peers are told before an apply that turns it on.
#
# The role's statements are bound to the guardrails that carry its project tag, and AWS's TagResource
# statement asks for that tag on the resource, so the account's guardrail, which carries none, takes
# no write from the role: decision 27's deny in the targets is here the absence of a grant.
#
# The description names the switch-independent statements: a description change replaces the policy.

resource "aws_iam_policy" "bedrock_application" {
  name        = "awsds-${var.env}-bedrock-application"
  description = "Keep an application's own guardrail: list the account's, create one with the caller's project tag, read, update, publish and tag one of the caller's project. Stage 17 step 10.4; attached to SMUS project roles by this slice."
  policy      = data.aws_iam_policy_document.bedrock_application.json
}

data "aws_iam_policy_document" "bedrock_application" {
  # checkov:skip=CKV_AWS_356:ListGuardrails without an identifier and CreateGuardrail take no guardrail ARN, so only "*" matches them; the create is bound by its request tag, and the deny names every model on purpose

  # ListGuardrails without an identifier lists the DRAFT of every guardrail of the account, and the task
  # finds its guardrail there by name.
  statement {
    sid       = "ListTheAccountsGuardrails"
    effect    = "Allow"
    actions   = ["bedrock:ListGuardrails"]
    resources = ["*"]
  }

  # CreateGuardrail takes no guardrail resource type (Service Reference v1.5), so the create is bound by
  # its tags: the caller's project tag, alone, the one the task sends. Whether Bedrock also authorizes
  # that tag as bedrock:TagResource on the new guardrail is 10.4 step 1's reading: AWS's
  # BedrockTagResourcePermissions admits it only where the service presents it as the resource's tag.
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

  # The task's reads and writes on a guardrail that already carries the caller's project tag:
  # GetGuardrail on the DRAFT and on a version, UpdateGuardrail and CreateGuardrailVersion.
  statement {
    sid       = "KeepAGuardrailOfTheCallersProject"
    effect    = "Allow"
    actions   = ["bedrock:CreateGuardrailVersion", "bedrock:GetGuardrail", "bedrock:UpdateGuardrail"]
    resources = [local.guardrails]

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
    resources = [local.guardrails]

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

  # 10.4 step 4: an invocation is refused unless bedrock:GuardrailIdentifier names a numbered version of
  # a guardrail of this account. A negated operator matches an absent key, so a request that names no
  # guardrail is refused, and the DRAFT's ARN, which carries no version, does not match `guardrail/*:*`.
  dynamic "statement" {
    for_each = var.application_guardrail_required ? ["deny"] : []

    content {
      sid       = "DenyAnInvocationWithNoPublishedGuardrailOfTheAccount"
      effect    = "Deny"
      actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
      resources = ["*"]

      condition {
        test     = "ArnNotLike"
        variable = "bedrock:GuardrailIdentifier"
        values   = [local.guardrail_versions]
      }
    }
  }
}

resource "aws_iam_role_policy_attachment" "application" {
  for_each = toset(var.application_roles)

  role       = data.aws_iam_role.application[each.value].name
  policy_arn = aws_iam_policy.bedrock_application.arn

  lifecycle {
    # A role outside the D13 boundary is not a project role this estate governs, whatever its name.
    precondition {
      condition     = try(data.aws_iam_role.application[each.value].permissions_boundary, "") != "" && endswith(try(data.aws_iam_role.application[each.value].permissions_boundary, ""), ":policy/${local.boundary_name}")
      error_message = "${each.value} does not carry the ${local.boundary_name} permissions boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}

# ------------------------------------------------- the account's guardrail (10.4 step 6, decision 27 (a))
#
# A guardrail of the account's own, with a denied topic the application's guardrail does not hold, so a
# trace tells the two apart; its published version; and the account-level configuration that enforces
# that version on enforced_models, both content controls COMPREHENSIVE. The aws provider carries no
# account-level configuration and awscc 1.106.0 does (verification xlix). No project tag: no project
# role can write it. Created for the sitting and removed after it, with
# ListEnforcedGuardrailsConfiguration read empty.
resource "aws_bedrock_guardrail" "account" {
  count = var.account_guardrail_enabled ? 1 : 0

  name                      = "awsds-${var.env}-account-guardrail"
  description               = "The account's guardrail, enforced by the account-level configuration on the models this slice names (Stage 17 step 10.4, decision 27 (a))."
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
}

resource "aws_bedrock_guardrail_version" "account" {
  count = var.account_guardrail_enabled ? 1 : 0

  guardrail_arn = aws_bedrock_guardrail.account[0].guardrail_arn
  description   = "The version the account-level configuration enforces (Stage 17 step 10.4)."
  skip_destroy  = false
}

resource "awscc_bedrock_enforced_guardrail_configuration" "account" {
  count = var.account_guardrail_enabled ? 1 : 0

  guardrail_identifier = aws_bedrock_guardrail.account[0].guardrail_id
  guardrail_version    = aws_bedrock_guardrail_version.account[0].version

  model_enforcement = {
    included_models = var.enforced_models
    excluded_models = []
  }

  selective_content_guarding = {
    system   = "COMPREHENSIVE"
    messages = "COMPREHENSIVE"
  }
}
