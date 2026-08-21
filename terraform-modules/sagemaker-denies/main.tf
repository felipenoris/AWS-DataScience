# sagemaker-denies - Stage 6 step 3's statements, WRITTEN ONCE FOR TWO DIFFERENT OBJECTS.
#
# THIS MODULE EXISTS BECAUSE OF LESSON 33, and it is worth stating rather than leaving to be
# re-derived: one intent enforced in two places diverges, and sharing the VALUES while
# duplicating the STRUCTURE is what makes it look like it cannot. The intent here is enforced
# in two places by construction, not by choice -
#
#   the six PERSONA permission sets   in terraform-live/identity/sso/, governing humans
#   the project BOUNDARY              in terraform-modules/sagemaker-prereqs/, governing the
#                                     roles the blueprint authors in each member account
#
# - because they are different objects, in different accounts, provisioned by different
# services. What would have drifted is the STRUCTURE: the action lists, the operator on each
# condition key, and which actions each key is legal on. So the structure lives here, as one
# document, and both callers compose it through `source_policy_documents` - the idiom
# policies-shared.tf already uses to reach six permission sets with one diff.
#
# WHY EVERY OPERATOR BELOW IS NULL-SAFE, spelled out because getting it wrong is silent and
# expensive in the SAME direction each time (Lesson 5 - an intention is not a control):
#
#   ForAnyValue:StringNotEquals   on a MISSING multivalued key evaluates FALSE, so the deny
#                                 does not fire on a call that names no instance type. The
#                                 mirror image - ForAllValues: - evaluates TRUE on a missing
#                                 key and would deny every SageMaker call in the account.
#   Null ... = "true"             fires exactly when the key is ABSENT: "the request said
#                                 nothing about a VPC" is the thing being refused.
#   BoolIfExists ... = "false"    fires when the key is absent OR explicitly false, which is
#                                 how "must be present and true" is spelled. A plain Bool
#                                 would let an omission through.
#
# AND WHY EACH STATEMENT NAMES ITS ACTIONS RATHER THAN sagemaker:*: a condition key that the
# action does not carry is a key that is always absent, so a Null- or IfExists-shaped deny
# over sagemaker:* would deny everything unconditionally while reading like a narrow control.
# The lists below are the actions whose API carries the field the key reflects.

locals {
  # The VpcConfig-carrying creates. CreateTransformJob is deliberately absent: batch transform
  # has no VpcConfig of its own - it inherits the Model's, which is why CreateModel is here.
  vpc_config_actions = [
    "sagemaker:CreateTrainingJob",
    "sagemaker:CreateProcessingJob",
    "sagemaker:CreateHyperParameterTuningJob",
    "sagemaker:CreateAutoMLJob",
    "sagemaker:CreateAutoMLJobV2",
    "sagemaker:CreateModel",
  ]

  # EnableNetworkIsolation-carrying creates - the same set: a job that runs in our subnets and
  # can still open arbitrary outbound connections from inside the container is half a control.
  network_isolation_actions = local.vpc_config_actions

  # EnableInterContainerTrafficEncryption - distributed training/processing only. A single-
  # instance job has no inter-container traffic and the API does not carry the field.
  inter_container_actions = [
    "sagemaker:CreateTrainingJob",
    "sagemaker:CreateProcessingJob",
    "sagemaker:CreateHyperParameterTuningJob",
    "sagemaker:CreateAutoMLJob",
    "sagemaker:CreateAutoMLJobV2",
  ]

  # VolumeKmsKeyId-carrying creates. CreateTransformJob DOES carry this one
  # (TransformResources.VolumeKmsKeyId), which is why the two lists are not the same list.
  volume_kms_actions = [
    "sagemaker:CreateTrainingJob",
    "sagemaker:CreateProcessingJob",
    "sagemaker:CreateHyperParameterTuningJob",
    "sagemaker:CreateAutoMLJob",
    "sagemaker:CreateAutoMLJobV2",
    "sagemaker:CreateTransformJob",
  ]
}

data "aws_iam_policy_document" "this" {

  # ------------------------------------------------------------------ the VPC requirement
  #
  # THE STATEMENT THE WHOLE NETWORK DESIGN RESTS ON. A VpcOnly domain constrains STUDIO - the
  # notebook the person types in. It says nothing about the training or processing job that
  # notebook launches through the API, which carries its own network configuration and, left
  # unconstrained, runs in an AWS-managed network where no endpoint policy, no
  # aws:SourceVpce condition and no flow log can see it. Without this, "private by default"
  # is true of the account and false of the thing the data scientist actually runs.
  statement {
    sid       = "DenySageMakerJobsOffVpc"
    effect    = "Deny"
    actions   = local.vpc_config_actions
    resources = ["*"]

    condition {
      test     = "Null"
      variable = "sagemaker:VpcSubnets"
      values   = ["true"]
    }
  }

  # -------------------------------------------------------------------- the cost ceiling
  #
  # THE ONLY CONTROL THAT STOPS AN OVERSIZED INSTANCE INSIDE ITS FIRST HOUR. D12's budget
  # notifies nobody by decision, so an ml.p4d parameter typed by mistake is discovered on a
  # bill weeks later. sagemaker:InstanceTypes covers CreateApp, CreateSpace, UpdateSpace and
  # CreateTrainingJob (read 2026-08-16), which is why this one is scoped to sagemaker:* -
  # every action that names an instance type is caught, and every action that does not is
  # left alone by the ForAnyValue operator rather than by an action list that would go stale.
  statement {
    sid       = "DenySageMakerInstanceCeiling"
    effect    = "Deny"
    actions   = ["sagemaker:*"]
    resources = ["*"]

    condition {
      test     = "ForAnyValue:StringNotEquals"
      variable = "sagemaker:InstanceTypes"
      values   = var.allowed_instance_types
    }
  }

  # ------------------------------------------------------- the three hardening requirements
  #
  # Separate statements rather than three conditions on one, because conditions inside a
  # statement are ANDed: a single statement would deny only the job that violates all three.
  statement {
    sid       = "DenySageMakerJobsWithoutNetworkIsolation"
    effect    = "Deny"
    actions   = local.network_isolation_actions
    resources = ["*"]

    condition {
      test     = "BoolIfExists"
      variable = "sagemaker:NetworkIsolation"
      values   = ["false"]
    }
  }

  statement {
    sid       = "DenySageMakerJobsWithoutInterContainerEncryption"
    effect    = "Deny"
    actions   = local.inter_container_actions
    resources = ["*"]

    condition {
      test     = "BoolIfExists"
      variable = "sagemaker:InterContainerTrafficEncryption"
      values   = ["false"]
    }
  }

  statement {
    sid       = "DenySageMakerJobsWithoutVolumeEncryption"
    effect    = "Deny"
    actions   = local.volume_kms_actions
    resources = ["*"]

    condition {
      test     = "Null"
      variable = "sagemaker:VolumeKmsKey"
      values   = ["true"]
    }
  }
}
