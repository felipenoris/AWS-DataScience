# Stage 6f step 11 - the lake published through the SageMaker Catalog (decision 1, shape (b), the
# pilot of 2026-10-26). This file declares two things for it. The grants a subscription becomes are
# not here: DataZone writes them as named-resource grants, acting as the publishing project's role,
# and ./aws/catalog.py reads them into the grant register (6f decision 2's first option).
#
# 1. The two SMUS administrator seats. The first environment of a project in an account writes
#    PutDataLakeSettings as the provisioning role, adding itself and the manage-access role; in
#    Sandbox (2026-08-22) it kept Parameters at 4/TRUE and both create-defaults empty (open
#    question 24). Declared here before the publishing project exists, the list stays this
#    slice's: the re-plan after that environment reads No changes if the service wrote those two
#    seats and nothing else, and a diff names what it changed (step 11.4). An administrator can
#    grant itself anything in raw and curated, which is TM-27's residual.
#
# 2. The publisher's grant, the exception GOVERNANCE.md §Grants admits for the catalog road:
#    DESCRIBE on curated, and DESCRIBE and SELECT with the grant option on each published table,
#    named rather than tagged, because DataZone documents no LF-TBAC support for the Glue assets it
#    manages and fulfils a subscription by regranting what the publishing role holds.

locals {
  # The tables the publishing project may publish. One for the pilot; a second is a decision 2
  # row (a `restricted` or `personal` table is never added here before that decision).
  published_tables = [aws_glue_catalog_table.trades.name]

  smus_admin_seats = var.lake_publishing_enabled ? [for r in data.aws_iam_role.smus_seat : r.arn] : []
}

# The two roles data-governance/publishing/ creates, by the name terraform-modules/sagemaker-prereqs/
# gives them. Read rather than built, so a seat whose role does not exist yet fails at plan, naming
# it, instead of at the settings apply.
data "aws_iam_role" "smus_seat" {
  for_each = var.lake_publishing_enabled ? toset(["provisioning", "manage-access"]) : toset([])

  name = "awsds-${var.env}-smus-${each.value}"
}

# The publishing project's role. A missing role fails at plan with its name; a role outside the D13
# boundary is not a project role this estate governs, and the precondition below refuses it.
data "aws_iam_role" "lake_publisher" {
  count = var.lake_publisher_role == null ? 0 : 1

  name = var.lake_publisher_role
}

resource "aws_lakeformation_permissions" "publisher_database" {
  count = var.lake_publisher_role == null ? 0 : 1

  principal   = data.aws_iam_role.lake_publisher[0].arn
  permissions = ["DESCRIBE"]

  database {
    name = aws_glue_catalog_database.curated.name
  }

  lifecycle {
    precondition {
      condition     = var.lake_publishing_enabled
      error_message = "lake_publisher_role is set while LAKE_PUBLISHERS is empty: the publisher grant follows the seats and the profile (Stage 6f step 11)."
    }

    precondition {
      condition     = data.aws_iam_role.lake_publisher[0].permissions_boundary == "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:policy/awsds-${var.env}-project-boundary"
      error_message = "the publisher role carries no awsds-data-project-boundary: it is not a role the Tooling configuration authored under D13."
    }
  }
}

resource "aws_lakeformation_permissions" "publisher_tables" {
  for_each = var.lake_publisher_role == null ? toset([]) : toset(local.published_tables)

  principal                     = data.aws_iam_role.lake_publisher[0].arn
  permissions                   = ["DESCRIBE", "SELECT"]
  permissions_with_grant_option = ["DESCRIBE", "SELECT"]

  table {
    database_name = aws_glue_catalog_database.curated.name
    name          = each.value
  }

  depends_on = [aws_lakeformation_permissions.publisher_database]
}
