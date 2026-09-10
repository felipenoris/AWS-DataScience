# sagemaker-denies - Stage 6 step 3's statements, written once for two different objects.
#
# One intent enforced in two places diverges when the values are shared and the structure is
# duplicated (Lesson 33). Here the intent reaches two places by construction, not by choice -
#
#   the six persona permission sets   in terraform-live/identity/sso/, governing humans
#   the project boundary              in terraform-modules/sagemaker-prereqs/, governing the
#                                     roles the blueprint authors in each member account
#
# - different objects, in different accounts, provisioned by different services. What would
# have drifted is the structure: the action lists, the operator on each condition key, and
# which actions each key is legal on. So the structure lives here, as one document, and both
# callers compose it through `source_policy_documents` - the idiom policies-shared.tf already
# uses to reach six permission sets with one diff.
#
# Every operator below is null-safe, because getting it wrong is silent and fails in the same
# direction each time (Lesson 5):
#
#   ForAnyValue:StringNotEquals   on a missing multivalued key evaluates FALSE, so the deny
#                                 does not fire on a call that names no instance type. The
#                                 mirror image - ForAllValues: - evaluates TRUE on a missing
#                                 key and would deny every SageMaker call in the account.
#   Null ... = "true"             fires exactly when the key is absent: "the request said
#                                 nothing about a VPC" is the thing being refused.
#   BoolIfExists ... = "false"    fires when the key is absent or explicitly false, which is
#                                 how "must be present and true" is spelled. A plain Bool
#                                 would let an omission through.
#
# Each statement names its actions rather than sagemaker:*: a condition key that the action
# does not carry is a key that is always absent, so a Null- or IfExists-shaped deny over
# sagemaker:* would deny everything unconditionally while reading like a narrow control. The
# lists below are the actions whose API carries the field the key reflects.

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

  # VolumeKmsKeyId-carrying creates. CreateTransformJob does carry this one
  # (TransformResources.VolumeKmsKeyId), which is why the two lists differ.
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
  # The statement the whole network design rests on. A VpcOnly domain constrains Studio - the
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
  # The only control that stops an oversized job inside its first hour. D12's budget notifies
  # nobody by decision, so an ml.p4d parameter typed by mistake is discovered on a bill weeks
  # later. sagemaker:InstanceTypes covers CreateApp, CreateSpace, UpdateSpace and
  # CreateTrainingJob (read 2026-08-16), which is why this one is scoped to sagemaker:* - every
  # action that names an instance type is caught, and every action that does not is left alone
  # by the ForAnyValue operator rather than by an action list that would go stale.
  #
  # The space path is exempt (the user's decision, 2026-09-07): a JupyterLab or Code Editor
  # space may be created or resized at any type. The remote-IDE server needs >= 8 GB, which the
  # ml.t3.medium default does not have (6d step 7.1), and the user chose no ceiling on that path
  # over a wider list. `not_actions` rather than an action list keeps the reach bounded by the
  # key - every action that names an instance type - minus the three that create or resize a
  # space's app, so nothing goes stale when SageMaker adds a job action. A Deny with NotAction
  # reads as "every action in every service", and the condition is what keeps it SageMaker-only:
  # a request carrying no sagemaker:InstanceTypes is left alone.
  #
  # Simulated with simulate-custom-policy, ten cases (6d log 2026-09-07):
  # CreateTrainingJob/CreateProcessingJob at p4d/g5 explicitDeny, at ml.m5.large allowed;
  # CreateSpace/UpdateSpace/CreateApp at p4d/g5 allowed; ListSpaces, DescribeDomain,
  # s3:ListAllMyBuckets, glue:GetDatabases with no key allowed.
  #
  # What this gives up: an ml.p4d Code Editor space bills USD 30+/h and D12's budget notifies
  # nobody; the Tooling idle shutdown bounds an idle space and nothing bounds a busy one. Jobs,
  # endpoints and notebook instances keep the list below.
  statement {
    sid    = "DenySageMakerInstanceCeiling"
    effect = "Deny"
    not_actions = [
      "sagemaker:CreateApp",
      "sagemaker:CreateSpace",
      "sagemaker:UpdateSpace",
    ]
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
