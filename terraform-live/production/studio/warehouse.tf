# The warehouse load as the deployment project's role (Stage 19 decision 16 (b), step 4.11): the
# workflow app-etl-warehouse runs in deploy-production, and its Glue job, glue/load_warehouse.py,
# takes temporary credentials for the governed warehouse and writes over JDBC, as
# awsds-prod-job-exec did under ConnectToTheGovernedWarehouse (production/sagemaker/). The session is
# the role's own database user, IAMR:<role name>, which holds what the warehouse's SQL grants it
# (Stage 9 step 9.3's shape, written by hand in a warehouse sitting).
#
# This file is the account's own, as project-roles.tf and fence.tf are: Staging has no warehouse.
# The other two halves of the path are production/warehouse/'s ingress from the project's security
# group and the D13 boundary, whose fence denies the Data API and the query editor and leaves
# redshift-serverless (fence.tf).
#
# A workgroup's ARN carries an id the service generates, and the compute is [E], a new id at every
# `make up`: the statement names every workgroup of this account, which holds one.

data "aws_iam_policy_document" "warehouse_load" {
  statement {
    sid       = "ConnectToTheGovernedWarehouse"
    effect    = "Allow"
    actions   = ["redshift-serverless:GetCredentials", "redshift-serverless:GetWorkgroup"]
    resources = ["arn:${data.aws_partition.current.partition}:redshift-serverless:${var.region}:${data.aws_caller_identity.current.account_id}:workgroup/*"]
  }
}

resource "aws_iam_policy" "warehouse_load" {
  name        = "awsds-${var.env}-warehouse-load"
  description = "The warehouse load's session on the governed workgroup, as the deployment project's role (Stage 19 decision 16 (b))."
  policy      = data.aws_iam_policy_document.warehouse_load.json
}

resource "aws_iam_role_policy_attachment" "warehouse_load" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.warehouse_load.arn

  lifecycle {
    # A role outside this slice's D13 boundary is not a project role this estate governs.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") == module.sagemaker_prereqs.project_boundary_arn
      error_message = "${each.value} does not carry this account's D13 boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
