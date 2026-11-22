# The workflows grant for SMUS project roles (Stage 6i decision 6; the Glue statement, Stage 10
# decision 12, user 2026-10-16; the training, transform and model statements and the registration in
# an application's own group, Stage 17 step 9.5 and decision 7 (a)). It holds what a workflow's
# operators need, and nothing only a notebook creates (decision 7 (a)). It holds no
# datazone:StartDataSourceRun: a Sandbox project's data source imports on its schedule or on a
# member's run in the portal, SMUS's own triggers (Stage 19 decision 17).
#
# SageMakerProcessingOperator describes the job name it proposes before it creates the job, and
# counts only a ValidationException as "absent" (Amazon provider 9.32.0, the MWAA Serverless
# worker's; no parameter turns the check off). The blueprint's SageMakerStudioProjectRoleMachine-
# LearningPolicy grants DescribeProcessingJob only on a job tagged with the caller's project, and a
# name not yet taken carries no tag, so the project role is refused before any job exists
# (measured 2026-10-10, run Pzs3TlvfHhqOK6M).
#
# The grant below covers exactly that gap: a processing job that carries no AmazonDataZoneProject
# tag, which includes every name not yet taken. A job another project created carries its own tag
# and stays out of reach, since SMUS refuses a CreateProcessingJob without the tag. A job created
# untagged by a principal outside SMUS is describable by the project roles listed here.
#
# The boundary is untouched: awsds-sandbox-project-boundary denies no Describe call, and the jobs
# the operators then create still meet its four job denies.

# The description names the first statement only: it forces a new policy when it changes, and the
# comment above each statement is where the grant is described.
resource "aws_iam_policy" "workflows" {
  name        = "awsds-${var.env}-workflows"
  description = "Describe a SageMaker processing job that carries no project tag, so a workflow's operator can check a name before creating the job. Stage 6i; attached to SMUS project roles by this slice."
  policy      = data.aws_iam_policy_document.workflows.json
}

data "aws_iam_policy_document" "workflows" {
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

  # CreateProcessingJob with tags is also authorized as sagemaker:AddTags, and the blueprint's
  # SageMakerTagPermissions excludes every AmazonDataZone* key, while its SageMakerCreatePermissions
  # requires the job to carry AmazonDataZoneProject. So a project role cannot create the job the
  # blueprint's own condition asks for (measured 2026-10-10, run FVyFira1LY3BuGi). This statement
  # allows that one tag with the caller's own value, alone, on a job that carries no project tag or
  # already the caller's, so a job of another project cannot be claimed.
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
  # The pair exists while training_pair_enabled is true: it reaches every role listed, the role of the
  # project where Stage 17's 2.2 reads the tag gap on a notebook's training job among them.
  dynamic "statement" {
    for_each = var.training_pair_enabled ? ["describe"] : []

    content {
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
  }

  # The training job's tags, authorized as sagemaker:AddTags under the same conditions as the
  # processing job's, behind the describe's switch.
  dynamic "statement" {
    for_each = var.training_pair_enabled ? ["tag"] : []

    content {
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

  # A versioned model package takes no tag argument and is authorized against its group's tags
  # (SUP-408, measured from a space): the blueprint's SageMakerCreatePermissions admits a version, of
  # any status, in a group carrying the caller's project tag. This statement admits the register task's
  # request in its application's `dev` group (model_applications) whatever the group carries: that
  # group's versions, from the role of the project that owns it, with the status PendingManualApproval
  # alone, the one the task names. The approval in a `dev` project is the member's, in the portal.
  dynamic "statement" {
    for_each = local.model_applications

    content {
      sid       = "RegisterAPendingVersionFor${statement.value.sid_suffix}"
      effect    = "Allow"
      actions   = ["sagemaker:CreateModelPackage"]
      resources = [statement.value.model_versions]

      condition {
        test     = "StringEquals"
        variable = "aws:PrincipalTag/AmazonDataZoneProject"
        values   = [statement.value.project_id]
      }

      condition {
        test     = "StringEquals"
        variable = "sagemaker:ModelApprovalStatus"
        values   = ["PendingManualApproval"]
      }
    }
  }

  # GlueJobOperator reads the job it names with glue:GetJob before it creates or updates it, and
  # counts only an EntityNotFoundException as "absent" (Amazon provider 9.32.0). The blueprint's
  # SageMakerStudioProjectUserRolePolicy grants GetJob only on a job tagged with the caller's
  # project, and a name not yet taken carries no tag, so the project role is refused before any job
  # exists (measured 2026-10-16, the CI/CD CLI's run u4AFogXA74olkqo). This statement allows GetJob
  # on a job that carries no project tag and whose name ends with the caller's project id, the name
  # an application gives its job (<app>-<project id>, D41): another project's job stays out of reach
  # by its tag, and an untagged job of any other name by its name. The create that follows is the
  # blueprint's own GlueCreateAndTagPermissions, exercised by the first run after this grant: the
  # operator read EntityNotFoundException and created the job with the project tag (2026-10-16, run
  # JO9MJ2BMRo7RL1Z).
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
}

resource "aws_iam_role_policy_attachment" "project" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.workflows.arn

  lifecycle {
    # A role outside the D13 boundary is not a project role this estate governs, whatever its name.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") != "" && endswith(try(data.aws_iam_role.project[each.value].permissions_boundary, ""), ":policy/${local.boundary_name}")
      error_message = "${each.value} does not carry the ${local.boundary_name} permissions boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
