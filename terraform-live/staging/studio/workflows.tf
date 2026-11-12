# The workflows grant on the deployment project's role (Stage 19 step 4.4): the statements
# sandbox/workflows/ attaches to every Sandbox project role, whose reasoning and measurements are
# that slice's main.tf. In a deployment project the role is every workflow's execution role and the
# role of the Glue and processing jobs its operators create (Stage 18 step 4.4: without the grant
# the first run was refused glue:GetJob).
#
# The policy exists once the blueprints are enabled, since its last statement names the domain. It
# is attached to the roles project-roles.tf names.

locals {
  processing_jobs = "arn:${data.aws_partition.current.partition}:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"

  # A Glue job named for the caller's project, <app>-<project id> (D41): $${ keeps the policy
  # variable out of Terraform's interpolation.
  glue_jobs_named_for_the_caller = "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:job/*-$${aws:PrincipalTag/AmazonDataZoneProject}"
}

resource "aws_iam_policy" "workflows" {
  count = var.blueprints_enabled ? 1 : 0

  name        = "awsds-${var.env}-workflows"
  description = "sandbox/workflows/'s grant on a deployment project's role: a workflow's operators check a Glue or processing job name before creating the job, and the publishing task starts the project's data source."
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
  # 19 decisions 3 and 17). The action takes no resource type below the domain and no condition key,
  # so the grant reaches every data source of the domain (TM-29); ./aws/catalog.py CT-13 judges each
  # start against the source's project.
  statement {
    sid       = "StartADataSourceRunInTheProjectsDomain"
    effect    = "Allow"
    actions   = ["datazone:StartDataSourceRun"]
    resources = ["arn:${data.aws_partition.current.partition}:datazone:${var.region}:*:domain/${data.terraform_remote_state.governance[0].outputs.domain_id}"]
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
