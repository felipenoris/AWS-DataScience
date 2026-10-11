# The workflows grant for SMUS project roles (Stage 6i decision 6).
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
# the operator then creates still meet its four job denies.

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
