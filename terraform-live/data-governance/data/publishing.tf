# Stage 6f step 11 - the lake published through the SageMaker Catalog (decision 1, shape (b), the
# pilot of 2026-10-26). This file declares two things for it. The grants a subscription becomes are
# not here: DataZone writes them as named-resource grants, acting as the publishing project's role.
# They are registered by reading (6f decision 2, 2026-10-27): the subscription is each grant's
# record, and ./aws/catalog.py CT-10 fails on a grant on a published table that neither this file
# nor an approved subscription explains.
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
  # The tables the publishing project may publish; ./aws/catalog.py's PUBLISHED_LAKE_TABLES is the
  # same list.
  published_tables = [aws_glue_catalog_table.trades.name]

  # 6f decision 2: a table enters the catalog road only when its classification and every
  # column's are public or internal. DataZone fulfils by name and reads no LF-Tag, so a restricted
  # column on a published table reaches every subscriber whole; restricted and personal data travel
  # on TBAC grants alone. Each lake table's assignments as this slice declares them, the table's and
  # its columns' together; a table with no entry here cannot be published.
  catalog_road_classifications = ["public", "internal"]
  declared_classifications = {
    (aws_glue_catalog_table.trades.name) = [
      for t in aws_lakeformation_resource_lf_tags.trades_table.lf_tag : t.value
      if t.key == aws_lakeformation_lf_tag.classification.key
    ]
    (aws_glue_catalog_table.sample_trades.name) = [
      for t in setunion(
        aws_lakeformation_resource_lf_tags.sample_trades_table.lf_tag,
        aws_lakeformation_resource_lf_tags.sample_trades_restricted_column.lf_tag,
      ) : t.value if t.key == aws_lakeformation_lf_tag.classification.key
    ]
  }

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

  lifecycle {
    precondition {
      condition = length(lookup(local.declared_classifications, each.value, [])) > 0 && alltrue([
        for v in lookup(local.declared_classifications, each.value, []) :
        contains(local.catalog_road_classifications, v)
      ])
      error_message = "curated.${each.value} is not public or internal on the table and on every column, or declares no classification here: 6f decision 2 keeps restricted and personal data off the catalog road."
    }
  }

  depends_on = [aws_lakeformation_permissions.publisher_database]
}
