# The workflows grant on the deployment project's role (Stage 19 step 4.4): the statements
# sandbox/workflows/ attaches to every Sandbox project role, whose reasoning and measurements are
# that slice's main.tf; the same pair for the training job app-etl-train creates; the pair for the
# transform job and the tag of the model app-ml's tasks create, with the registration of app-ml's
# model versions, which the role cannot approve (Stage 17 step 9.5); where project-roles.tf sets
# publishing_starts_the_source, the publishing task's start of the project's data source; and where
# it sets publishing_creates_the_data_product, the task's creation and revision of the product's data
# product. In a deployment project the role is every workflow's execution role and the role of the
# Glue, processing, training and transform jobs its operators create (Stage 18 step 4.4: without the
# grant the first run was refused glue:GetJob; SUP-267).
#
# The policy exists once the blueprints are enabled, since its last statement can name the domain.
# It is attached to the roles project-roles.tf names.

locals {
  processing_jobs = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"
  training_jobs   = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:training-job/*"
  transform_jobs  = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:transform-job/*"
  models          = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model/*"

  # app-ml's package group in this account's registry (<env>/sagemaker/registry.tf) and its versions,
  # and every version of the account's registry.
  app_ml_model_group    = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model-package-group/awsds-${var.env}-model-app-ml"
  app_ml_model_versions = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model-package/awsds-${var.env}-model-app-ml/*"
  model_versions        = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model-package/*"

  # A Glue job named for the caller's project, <app>-<project id> (D41): $${ keeps the policy
  # variable out of Terraform's interpolation.
  glue_jobs_named_for_the_caller = "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:job/*-$${aws:PrincipalTag/AmazonDataZoneProject}"

  # A description change replaces the policy, so each clause follows the statement it names.
  publishing_steps = compact([
    var.publishing_starts_the_source ? "starts the project's data source" : "",
    var.publishing_creates_the_data_product ? "creates or revises the product's data product" : "",
  ])
  workflows_description = join("", [
    "sandbox/workflows/'s grant on a deployment project's role: a workflow's operators check a Glue, processing, training or transform job name before creating the job, a task tags a model with the caller's project and registers app-ml's model versions, which the role cannot approve",
    length(local.publishing_steps) > 0 ? ", and the publishing task ${join(" and ", local.publishing_steps)}" : "",
    ".",
  ])
}

resource "aws_iam_policy" "workflows" {
  count = var.blueprints_enabled ? 1 : 0

  name        = "awsds-${var.env}-workflows"
  description = local.workflows_description
  policy      = data.aws_iam_policy_document.workflows[0].json
}

data "aws_iam_policy_document" "workflows" {
  count = var.blueprints_enabled ? 1 : 0

  # A processing job that carries no AmazonDataZoneProject tag, which includes every name not yet taken.
  statement {
    sid       = "DescribeAProcessingJobNoProjectHolds"
    effect    = "Allow"
    actions   = ["sagemaker:DescribeProcessingJob"]
    resources = [local.processing_jobs]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["true"]
    }
  }

  # A CreateProcessingJob with tags is also authorized as sagemaker:AddTags, which the blueprint
  # refuses for every AmazonDataZone* key: the caller's own project tag, alone, on a job that carries
  # no project tag or already the caller's.
  statement {
    sid       = "TagAProcessingJobWithTheCallersProject"
    effect    = "Allow"
    actions   = ["sagemaker:AddTags"]
    resources = [local.processing_jobs]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }
  }

  # SageMakerTrainingOperator describes the job name before CreateTrainingJob (SUP-268), and the
  # blueprint's DescribeTrainingJob, like its DescribeProcessingJob, requires the caller's project tag.
  statement {
    sid       = "DescribeATrainingJobNoProjectHolds"
    effect    = "Allow"
    actions   = ["sagemaker:DescribeTrainingJob"]
    resources = [local.training_jobs]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["true"]
    }
  }

  # The training job's tags, authorized as sagemaker:AddTags under the same conditions as the
  # processing job's.
  statement {
    sid       = "TagATrainingJobWithTheCallersProject"
    effect    = "Allow"
    actions   = ["sagemaker:AddTags"]
    resources = [local.training_jobs]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }
  }

  # SageMakerTransformOperator describes the job name before CreateTransformJob (SUP-372), and the
  # blueprint's DescribeTransformJob, like its DescribeTrainingJob, requires the caller's project tag.
  statement {
    sid       = "DescribeATransformJobNoProjectHolds"
    effect    = "Allow"
    actions   = ["sagemaker:DescribeTransformJob"]
    resources = [local.transform_jobs]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["true"]
    }
  }

  # The transform job's tags, authorized as sagemaker:AddTags under the same conditions as the
  # processing job's.
  statement {
    sid       = "TagATransformJobWithTheCallersProject"
    effect    = "Allow"
    actions   = ["sagemaker:AddTags"]
    resources = [local.transform_jobs]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }
  }

  # The model a task creates with the caller's project tag (app-ml's resolve), whose tags are
  # authorized as sagemaker:AddTags under the same conditions.
  statement {
    sid       = "TagAModelWithTheCallersProject"
    effect    = "Allow"
    actions   = ["sagemaker:AddTags"]
    resources = [local.models]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }
  }

  # app-ml's register task proposes a version PendingManualApproval in this account's group, and its
  # register and resolve tasks read the group's versions (Stage 17 decision 16 (b)).
  statement {
    sid    = "RegisterAndReadTheModelVersions"
    effect = "Allow"
    actions = [
      "sagemaker:CreateModelPackage",
      "sagemaker:DescribeModelPackage",
      "sagemaker:ListModelPackages",
    ]
    resources = [local.app_ml_model_group, local.app_ml_model_versions]
  }

  # The approval is the deploy role's. AWS's SageMakerStudioProjectRoleMachineLearningPolicy allows
  # UpdateModelPackage, and CreateModelPackage with any status, on a version that carries the role's
  # AmazonDataZoneProject tag in any group (read by simulation 2026-11-17 in both targets), so each
  # refusal is a Deny (Lesson 72) over every version of the account (Lesson 82). StringNotEquals also
  # refuses a create that names no status; the register task names PendingManualApproval.
  statement {
    sid       = "DenyApprovingAModelVersion"
    effect    = "Deny"
    actions   = ["sagemaker:UpdateModelPackage"]
    resources = [local.model_versions]
  }

  statement {
    sid       = "DenyRegisteringAVersionNotPending"
    effect    = "Deny"
    actions   = ["sagemaker:CreateModelPackage"]
    resources = [local.model_versions]

    condition {
      test     = "StringNotEquals"
      variable = "sagemaker:ModelApprovalStatus"
      values   = ["PendingManualApproval"]
    }
  }

  # GetJob on a Glue job that carries no project tag and whose name ends with the caller's project id.
  # The create that follows is the blueprint's own GlueCreateAndTagPermissions.
  statement {
    sid       = "GetAGlueJobNoProjectHolds"
    effect    = "Allow"
    actions   = ["glue:GetJob"]
    resources = [local.glue_jobs_named_for_the_caller]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["true"]
    }
  }

  # The publishing task starts the run of the project's data source before it lists the asset (Stage
  # 19 decisions 3 and 17), in the one stage that lists: the catalog import writes dev's technical
  # forms on the stage's asset, and the run returns the stage's table to it before the listing
  # (decision 19). AWS's managed policies grant the project role no StartDataSourceRun
  # (SageMakerStudioProjectRoleMachineLearningPolicy v48, SageMakerStudioProjectUserRolePolicy v77),
  # so this statement is the one step of the publication off SMUS's own path. The action takes no
  # resource type below the domain and no condition key, so the grant reaches every data source of
  # the domain (TM-29); ./aws/catalog.py CT-13 judges each start against the source's project.
  dynamic "statement" {
    for_each = var.publishing_starts_the_source ? ["start"] : []

    content {
      sid       = "StartADataSourceRunInTheProjectsDomain"
      effect    = "Allow"
      actions   = ["datazone:StartDataSourceRun"]
      resources = ["arn:${data.aws_partition.current.partition}:datazone:${var.region}:*:domain/${data.terraform_remote_state.governance[0].outputs.domain_id}"]
    }
  }

  # The publishing task creates the product's data product over the listed asset, revises it when
  # its items or description differ, and lists it (Stage 19 decision 26 (b)): a data product's name
  # is the domain's, so one stage owns it. AWS's managed policies grant the project role
  # CreateListingChangeSet, Get* and Search* and neither of these actions. Both take no resource
  # type below the domain and no condition key (Service Reference v1.5), so the statement names the
  # domain, as the start's does; DataZone's own check of the owning project is the bound below it.
  dynamic "statement" {
    for_each = var.publishing_creates_the_data_product ? ["product"] : []

    content {
      sid       = "CreateTheProductsDataProductInTheProjectsDomain"
      effect    = "Allow"
      actions   = ["datazone:CreateDataProduct", "datazone:CreateDataProductRevision"]
      resources = ["arn:${data.aws_partition.current.partition}:datazone:${var.region}:*:domain/${data.terraform_remote_state.governance[0].outputs.domain_id}"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "project" {
  for_each = var.blueprints_enabled ? toset(var.project_roles) : toset([])

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.workflows[0].arn

  lifecycle {
    # A role outside this slice's D13 boundary is not a project role this estate governs.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") == module.sagemaker_prereqs.project_boundary_arn
      error_message = "${each.value} does not carry this account's D13 boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
