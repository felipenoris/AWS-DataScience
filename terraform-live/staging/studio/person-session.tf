# The deny on a person's session of the deployment project's role (Stage 18 step 6.2, decision 11).
# DataZone assumes the project role for a person the project admits with the person's DataZone profile
# id as the session's source identity; the workers' sessions (MWAA Serverless, Glue, SageMaker) carry
# none (read 2026-10-21). A deny conditioned on aws:SourceIdentity being present binds the person's
# session alone: the objects in the projects bucket, the workflows, the jobs and the catalog's tables,
# and DataZone's notebooks, the writes 6.1's contributor made and the application's.
#
# Stage 18 step 8.1 empties project_roles before the project is deleted; 8.6 destroys the policy with
# the slice.

# The module's projects bucket (sagemaker-prereqs, s3.tf), read so that a renamed bucket fails the plan
# rather than leaving a deny that matches nothing; after the module, which creates it.
data "aws_s3_bucket" "projects" {
  bucket = "awsds-${var.env}-smus-projects"

  depends_on = [module.sagemaker_prereqs]
}

resource "aws_iam_policy" "person_session" {
  name        = "awsds-${var.env}-person-session-deny"
  description = "Stage 18 6.2: a person's session of a deployment project's role, which carries aws:SourceIdentity, writes no object, workflow, job, table or notebook."
  policy      = data.aws_iam_policy_document.person_session.json
}

data "aws_iam_policy_document" "person_session" {
  statement {
    sid       = "DenyAPersonWritingTheProjectsObjects"
    effect    = "Deny"
    actions   = ["s3:PutObject*", "s3:DeleteObject*", "s3:RestoreObject"]
    resources = ["${data.aws_s3_bucket.projects.arn}/*"]

    condition {
      test     = "Null"
      variable = "aws:SourceIdentity"
      values   = ["false"]
    }
  }

  statement {
    sid    = "DenyAPersonChangingTheWorkflows"
    effect = "Deny"
    actions = [
      "airflow-serverless:CreateWorkflow",
      "airflow-serverless:UpdateWorkflow",
      "airflow-serverless:DeleteWorkflow",
      "airflow-serverless:StartWorkflowRun",
      "airflow-serverless:StopWorkflowRun",
      "airflow-serverless:TagResource",
      "airflow-serverless:UntagResource",
    ]
    resources = ["*"]

    condition {
      test     = "Null"
      variable = "aws:SourceIdentity"
      values   = ["false"]
    }
  }

  # The Glue and processing jobs the workflow's operators create and run, and the catalog's tables.
  statement {
    sid    = "DenyAPersonChangingTheJobsAndTables"
    effect = "Deny"
    actions = [
      "glue:Create*",
      "glue:Update*",
      "glue:Delete*",
      "glue:Start*",
      "glue:Stop*",
      "glue:Put*",
      "glue:BatchCreate*",
      "glue:BatchDelete*",
      "glue:BatchStop*",
      "glue:BatchUpdate*",
      "sagemaker:Create*",
      "sagemaker:Update*",
      "sagemaker:Delete*",
      "sagemaker:Start*",
      "sagemaker:Stop*",
      "sagemaker:AddTags",
    ]
    resources = ["*"]

    condition {
      test     = "Null"
      variable = "aws:SourceIdentity"
      values   = ["false"]
    }
  }

  # The querybook's calls 6.1 read in CloudTrail, CreateCell and StartNotebookCompute among them, which
  # the CLI's model does not carry; a name IAM does not know matches nothing in a deny.
  statement {
    sid    = "DenyAPersonWritingNotebooks"
    effect = "Deny"
    actions = [
      "datazone:CreateNotebook",
      "datazone:UpdateNotebook",
      "datazone:DeleteNotebook",
      "datazone:StartNotebookRun",
      "datazone:StopNotebookRun",
      "datazone:StartNotebookImport",
      "datazone:StartNotebookExport",
      "datazone:StartNotebookSync",
      "datazone:StartNotebookCompute",
      "datazone:CreateCell",
      "datazone:UpdateCell",
      "datazone:DeleteCell",
    ]
    resources = ["*"]

    condition {
      test     = "Null"
      variable = "aws:SourceIdentity"
      values   = ["false"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "person_session" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.person_session.arn

  lifecycle {
    # A role outside this slice's D13 boundary is not a project role this estate governs.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") == module.sagemaker_prereqs.project_boundary_arn
      error_message = "${each.value} does not carry this account's D13 boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
