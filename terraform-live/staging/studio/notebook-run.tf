# The deny on a native notebook run by any session of the deployment project's role (6d decision 17,
# TM-34). datazone:StartNotebookRun takes a network configuration, and PUBLIC_INTERNET_ONLY would place
# the run, with the role's credentials and the project's data, outside D38's single egress. No condition
# key names a run's network (DataZone's service reference, read 2026-11-18), so the deny is whole.
#
# person-session.tf denies the call to a session that carries aws:SourceIdentity, a person's. This
# statement binds the rest: a workflow worker's session, which carries none, and any other path that
# calls as the role. No released workflow runs a notebook (Stage 8 5.6's lint refuses
# SageMakerNotebookOperator), and no trail of Sandbox, Staging, Production or Data Governance holds a
# StartNotebookRun since 2026-08-21 (read 2026-11-19).

data "aws_iam_policy_document" "notebook_run" {
  statement {
    sid       = "DenyTheProjectRoleANotebookRun"
    effect    = "Deny"
    actions   = ["datazone:StartNotebookRun"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "notebook_run" {
  name        = "awsds-${var.env}-notebook-run-deny"
  description = "No session of a deployment project's role starts a native notebook run (6d decision 17)."
  policy      = data.aws_iam_policy_document.notebook_run.json
}

resource "aws_iam_role_policy_attachment" "notebook_run" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.notebook_run.arn

  lifecycle {
    # A role outside this slice's D13 boundary is not a project role this estate governs.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") == module.sagemaker_prereqs.project_boundary_arn
      error_message = "${each.value} does not carry this account's D13 boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
