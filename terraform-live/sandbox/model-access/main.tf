# The two roles of the console's model access (Stage 17 decision 13, taken 2026-10-19 as (b)).
#
# A model enabled in the console's Amazon Bedrock models tab is a catalog asset of the governance
# project (data-governance/governance/model-governance.tf), and its form names a role that a custom
# environment of that project holds in this account (the console's code, read 2026-10-19):
#
#   the provisioning role   DataZone assumes it when a project's subscription to a model's listing is
#                           granted, and creates the project's application inference profile of the
#                           model, tagged AmazonDataZoneProject (inferred from AWS's policy for it,
#                           AmazonDataZoneBedrockModelManagementPolicy v1)
#   the consumption role    the playground's: a person's subscription to a model's playground listing
#                           is fulfilled by a connection whose credentials the browser takes
#
# Left to itself, the console creates both on the first Submit, under AWS's policies and outside the
# D13 boundary (decision 13 (a)). It does not when they exist:
#
#   - Before it processes a model, Submit looks in this account for a role whose name contains
#     AmazonSageMakerBedrockModelManagementRole-<domain account> and creates one when none exists;
#     a role chosen per model is read only afterwards. The Manage roles dialog preselects the same
#     name. So the provisioning role takes that name, built from the domain account the governance
#     state names, and the console adopts it. The name breaks the awsds-<env>-<component> convention
#     because the console's code is the reader (Lesson 48): if AWS renames it, Submit creates its own
#     role again, which iam list-roles shows.
#   - The consumption role is chosen in each playground model's Manage roles dialog, "Use a single
#     existing custom role for the model".
#
# Both are trusted by DataZone alone, as AWS's role pages write the trust: sts:AssumeRole and
# sts:SetContext under aws:SourceAccount, the domain account DataZone acts for. Both carry the D13
# boundary, which subtracts only the lake and the job settings from what they hold, so no principal
# here is an exception to it.

locals {
  partition         = data.aws_partition.current.partition
  account_id        = data.aws_caller_identity.current.account_id
  domain_account_id = element(split(":", data.terraform_remote_state.governance.outputs.domain_arn), 4)

  application_inference_profiles = "arn:${local.partition}:bedrock:${var.region}:${local.account_id}:application-inference-profile/*"
}

data "aws_iam_policy_document" "datazone_trust" {
  statement {
    sid     = "DataZoneAssumesTheModelRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:SetContext"]

    principals {
      type        = "Service"
      identifiers = ["datazone.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.domain_account_id]
    }
  }
}

# ---------------------------------------------------------------------- the provisioning role
#
# A policy of its own in place of AWS's managed one, statement for statement, with one narrowing:
# AWS's CreateApplicationInferenceProfileUsingFoundationModels admits a profile of any foundation
# model, and here the two create statements name var.project_models alone. The two statements on
# application-inference-profile/* keep AWS's conditions word for word, since they are what DataZone's
# calls were written against: a create or tag carries the AmazonDataZoneProject key, and a delete
# reaches only a profile tagged with it.
data "aws_iam_policy_document" "model_management" {
  statement {
    sid       = "ManageApplicationInferenceProfile"
    effect    = "Allow"
    actions   = ["bedrock:CreateInferenceProfile", "bedrock:TagResource"]
    resources = [local.application_inference_profiles]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["false"]
    }

    condition {
      test     = "Null"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["false"]
    }
  }

  statement {
    sid       = "DeleteApplicationInferenceProfile"
    effect    = "Allow"
    actions   = ["bedrock:DeleteInferenceProfile"]
    resources = [local.application_inference_profiles]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["false"]
    }
  }

  # A cross-Region profile's models live in every Region it routes to, so the foundation-model ARNs
  # carry no Region, as the SCP's do.
  statement {
    sid       = "CreateApplicationInferenceProfileUsingFoundationModels"
    effect    = "Allow"
    actions   = ["bedrock:CreateInferenceProfile"]
    resources = [for m in keys(var.project_models) : "arn:${local.partition}:bedrock:*::foundation-model/${m}"]
  }

  statement {
    sid     = "CreateApplicationInferenceProfileUsingBedrockModels"
    effect  = "Allow"
    actions = ["bedrock:CreateInferenceProfile"]
    resources = [
      for m, p in var.project_models : "arn:${local.partition}:bedrock:${var.region}:${local.account_id}:inference-profile/${p}" if p != ""
    ]
  }
}

module "model_provisioning_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "AmazonSageMakerBedrockModelManagementRole-${local.domain_account_id}"
  description          = "The model provisioning role of the console's model access (Stage 17 decision 13) - DataZone creates a project's application inference profile of a model in var.project_models; named so the console adopts it."
  assume_role_policy   = data.aws_iam_policy_document.datazone_trust.json
  permissions_boundary = data.terraform_remote_state.sagemaker.outputs.project_boundary_arn

  inline_policies = {
    "model-management" = data.aws_iam_policy_document.model_management.json
  }
}

# ----------------------------------------------------------------------- the consumption role
#
# AWS's consumption policy (InvokeDomainInferenceProfiles: the domain's application inference
# profiles, those carrying no project tag; the Bedrock sessions tagged with the DataZone user and
# domain) and the statement AWS's role page adds per model, written once for every model:
# foundation-model/* reached through this account's application inference profiles. The models are
# not listed here on purpose. The SCP is the ceiling, and 7.3's model outside the scoped set must be
# refused by it rather than by this role, or the refusal would prove nothing about the SCP (Lesson 20).
# AWS's policy moves without this repository being asked (Lesson 11).
data "aws_iam_policy_document" "invoke_through_application_inference_profiles" {
  statement {
    sid       = "AllowInferenceProfileToInvokeFoundationModels"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = ["arn:${local.partition}:bedrock:*::foundation-model/*"]

    condition {
      test     = "ArnLike"
      variable = "bedrock:InferenceProfileArn"
      values   = ["arn:${local.partition}:bedrock:*:${local.account_id}:application-inference-profile/*"]
    }
  }
}

module "model_consumption_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-bedrock-model-consumption"
  description          = "The model consumption role of the console's model access (Stage 17 decision 13) - the playground's; chosen per model in the console's Manage roles dialog."
  assume_role_policy   = data.aws_iam_policy_document.datazone_trust.json
  permissions_boundary = data.terraform_remote_state.sagemaker.outputs.project_boundary_arn

  managed_policy_arns = [
    "arn:${local.partition}:iam::aws:policy/service-role/AmazonDataZoneBedrockModelConsumptionPolicy",
  ]

  inline_policies = {
    "invoke-through-application-inference-profiles" = data.aws_iam_policy_document.invoke_through_application_inference_profiles.json
  }
}
