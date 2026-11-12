# The integration test's read of the product table (Stage 19 decision 14 (d), step 4.9): the
# Staging leg's `staging-test` reads, as awsds-deploy-staging, the table a release's run wrote in the
# deployment project's database. The run itself reads the table back and counts its rows as the
# project's role; what this grant adds is another principal finding the table in the catalog.
#
# DESCRIBE alone: the leg reads the table's metadata with glue:GetTable (the deploy role's
# ReadTheProductTablesMetadata, staging/foundation/). A read of its rows needs an engine, and
# Athena's enforced workgroup writes its results to awsds-staging-derived under the account data
# key, whose policies name their principals: that read is not written.
#
# The grant is this account's Lake Formation administrator's (InfrastructureAccess, seated by
# staging/data/) and is on a database DataZone created, by name: a database that does not exist
# fails the apply. This file is the account's own: Production's leg reads nothing of the kind.

variable "product_databases" {
  description = "The product databases of the applications deployed into this account's project, by name (Stage 19 decision 2 (d)): the same name in every account's catalog."
  type        = list(string)
  default     = ["app_etl"]
}

data "aws_iam_role" "deploy" {
  name = "awsds-deploy-${var.env}"
}

resource "aws_lakeformation_permissions" "deploy_product_database" {
  for_each = var.blueprints_enabled ? toset(var.product_databases) : toset([])

  principal   = data.aws_iam_role.deploy.arn
  permissions = ["DESCRIBE"]

  database {
    name = each.value
  }
}

resource "aws_lakeformation_permissions" "deploy_product_tables" {
  for_each = var.blueprints_enabled ? toset(var.product_databases) : toset([])

  principal   = data.aws_iam_role.deploy.arn
  permissions = ["DESCRIBE"]

  table {
    database_name = each.value
    wildcard      = true
  }
}
