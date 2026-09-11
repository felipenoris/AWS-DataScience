# The Bedrock grant for SMUS project roles (Stage 6e step 3, decision 8 option b).
#
# WHY THIS SLICE EXISTS AT ALL. The blueprint that creates a project role attaches three
# AWS-managed policies to it, and 3.1 measured what they give: every `bedrock:InvokeModel*` allow
# lands on `foundation-model/*`, NONE on the system inference profile, and `ListInferenceProfiles`
# is granted nowhere. Since all three scoped models are inference-profile only, the role has the
# half of the grant that cannot be used without the half it does not have.
#
# WHY IT IS NOT IN THE BLUEPRINT. `awscc_datazone_environment_blueprint_configuration` carries
# fourteen attributes and exactly one is policy-shaped - `environment_role_permission_boundary`,
# which is how INT-15 imposes D13 - and a boundary only subtracts (measured from the provider
# schema, 2026-09-11). The service offers a CEILING FOR EVERY PROJECT ROLE AND A FLOOR FOR NONE.
# So there is no lever that would have granted this to every project at once, and this slice names
# the roles one at a time because that is the only shape there is.
#
# WHY NOT A ROLE OF OUR OWN. The alternative (decision 8's option c) was a role this repository
# authors, reached by SDK role chaining, whose trust policy would list the projects allowed. It
# puts "which projects" in a value we write instead of in where an attachment landed, and it gives
# cost attribution a dedicated principal. It was refused on one line: the caller would then be a
# principal OUTSIDE awsds-sandbox-project-boundary, and every other interactive call in this
# account is inside it. It is recorded as the shape to adopt at Stage 14, when "which projects"
# stops being a trivial question.
#
# WHAT CAN TAKE THIS AWAY. The role is the service's, not ours. A blueprint reconciliation may
# detach a policy nobody in the SMUS control plane knows about - INT-15's open half - and the
# symptom is an assistant that stops working with no diff in this repository. The check is a
# re-plan of this slice, which is why the runbook's section P ends with one.

resource "aws_iam_policy" "bedrock_assistant" {
  name        = "awsds-${var.env}-bedrock-assistant"
  description = "Invoke the scoped Claude models through their us. inference profiles. Stage 6e step 3; attached to SMUS project roles by this slice."
  policy      = data.aws_iam_policy_document.bedrock_assistant.json
}

data "aws_iam_policy_document" "bedrock_assistant" {
  # The invocation. Both ARN groups in one statement because both are required for one call:
  # the request names the profile, and the service evaluates the profile AND the foundation model
  # behind it.
  statement {
    sid       = "InvokeScopedClaudeModelsThroughSystemProfiles"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = concat(local.profile_arns, local.foundation_model_arns)
  }

  # Resolving a profile the client names. `GetInferenceProfile` is how the client maps an
  # application inference profile ARN to its backing model to pick the request shape - a case this
  # estate does not have, since the scoped set is three SYSTEM_DEFINED profiles. Without it the
  # client retries once with the other shape, so omitting it costs a round-trip rather than a
  # failure; it is here because the round-trip is per new model and the grant is already narrow.
  statement {
    sid       = "ResolveTheScopedProfiles"
    effect    = "Allow"
    actions   = ["bedrock:GetInferenceProfile"]
    resources = local.profile_arns
  }

  # `ListInferenceProfiles` takes no resource - it is the call that lets the client resolve `opus`
  # to a profile that exists in THIS account instead of applying a prefix blind. Without it the
  # client applies the region-derived prefix unchecked, and a wrong guess is a 400 at the first
  # prompt rather than a fallback.
  statement {
    sid       = "ListProfilesHasNoResource"
    effect    = "Allow"
    actions   = ["bedrock:ListInferenceProfiles"]
    resources = ["*"]
  }

  # NOT HERE, AND EACH ABSENCE IS A DECISION:
  #
  #   aws-marketplace:Subscribe / ViewSubscriptions
  #       The vendor's sample policy asks for them under aws:CalledViaLast = bedrock.amazonaws.com.
  #       This account reaches these models through the use-case form (Stage 6e step 2), and all
  #       three read `agreementAvailability: NOT_AVAILABLE` - no marketplace agreement exists for
  #       any of them. A permission granted for a vendor sentence rather than for a measured
  #       refusal is Lesson 41. Open question 9 closes it the day a call is refused naming them.
  #
  #   bedrock:ListFoundationModels, GetFoundationModel
  #       The blueprint's own policies already grant the first under the project role's
  #       EnableAmazonBedrockPermissions tag, and the client does not need the second.
  #
  #   Anything on bedrock-agent, guardrails, evaluation or data automation
  #       A coding assistant invokes a model. Every other Bedrock surface belongs to whoever asks
  #       for it, with its own decision.
}

resource "aws_iam_role_policy_attachment" "project" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.bedrock_assistant.arn

  lifecycle {
    # The role must be under the D13 boundary. This is the property decision 8 chose this option
    # to keep, and it is the one thing a hand-written role name can get wrong in a way that looks
    # fine: a name matching the pattern but belonging to a role somebody made by hand would put
    # the invocation outside every ceiling this estate wrote for interactive compute.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") != "" && endswith(try(data.aws_iam_role.project[each.value].permissions_boundary, ""), ":policy/${local.boundary_name}")
      error_message = "${each.value} does not carry the ${local.boundary_name} permissions boundary. A SMUS project role always does (INT-15); a role that does not is not one, and granting Bedrock to it would put the invocation outside D13."
    }
  }
}
