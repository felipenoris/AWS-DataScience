# The workflows grant for the deployment project's role (Stage 18 step 4.4): sandbox/workflows/'s
# three statements, for the stage's life. Their reasoning, and the runs that measured each gap, are
# sandbox/workflows/main.tf's.
#
# GlueJobOperator reads the job it names with glue:GetJob before it creates it, and
# SageMakerProcessingOperator describes the processing job name it proposes; the blueprint's managed
# policies allow both only on a job tagged with the caller's project, and a name not yet taken carries
# no tag. deploy-staging's first run stopped there, on glue:GetJob, "because no identity-based policy
# allows the glue:GetJob action" (2026-10-19, run 7MMhwSySe5SOWd1).
#
# Stage 18 step 8.1 empties project_roles and applies before the project is deleted, so the
# environment's stack deletes a role that carries only the policies it attached; 8.6 destroys the
# policy with the slice.

locals {
  processing_jobs = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"

  # A Glue job named for the caller's project, <app>-<project id> (D41): $${ keeps the policy
  # variable out of Terraform's interpolation.
  glue_jobs_named_for_the_caller = "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:job/*-$${aws:PrincipalTag/AmazonDataZoneProject}"
}

resource "aws_iam_policy" "workflows" {
  name        = "awsds-${var.env}-workflows"
  description = "sandbox/workflows/'s grant on the deployment project's role, for Stage 18's life: a workflow's operators check a Glue or processing job name before creating the job."
  policy      = data.aws_iam_policy_document.workflows.json
}

data "aws_iam_policy_document" "workflows" {
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
}

resource "aws_iam_role_policy_attachment" "project" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.workflows.arn

  lifecycle {
    # A role outside this slice's D13 boundary is not a project role this estate governs.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") == module.sagemaker_prereqs.project_boundary_arn
      error_message = "${each.value} does not carry this account's D13 boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
