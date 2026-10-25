# Stage 9 steps 1.3 and 2.3 - what the account's Lake Formation administrator grants locally.
#
# The local regrant is a pair (measured at Stage 5a pass 4): DESCRIBE on the resource link, a local
# database, and the permission on the target, addressed through the lake's catalog id. Without the
# first the principal sees no database at all, holding every permission on the target.
#
# Every grant below needs the second apply of Recipe D (main.tf): the first seats the administrator
# and clears the create-time defaults. The regrants on the lake's objects need the share as well, so
# this slice applies after data-governance/data/'s Stage 9 change (pass 2 before pass 3).

# ---------------------------------------------------------------- the job role on the lake (2.3)

resource "aws_lakeformation_permissions" "job_link_describe" {
  for_each = module.consumer_data.resource_link_names

  principal   = local.job_role_arn
  permissions = ["DESCRIBE"]

  database {
    name = each.value
  }
}

resource "aws_lakeformation_permissions" "job_shared_databases" {
  principal   = local.job_role_arn
  permissions = ["DESCRIBE"]

  lf_tag_policy {
    catalog_id    = data.aws_caller_identity.lake.account_id
    resource_type = "DATABASE"

    expression {
      key    = "layer"
      values = ["raw", "curated"]
    }
  }
}

# The read every consumer holds: raw and curated, public and internal (shares.tf's expression).
resource "aws_lakeformation_permissions" "job_shared_tables" {
  principal   = local.job_role_arn
  permissions = ["SELECT", "DESCRIBE"]

  lf_tag_policy {
    catalog_id    = data.aws_caller_identity.lake.account_id
    resource_type = "TABLE"

    expression {
      key    = "layer"
      values = ["raw", "curated"]
    }

    expression {
      key    = "classification"
      values = ["public", "internal"]
    }
  }
}

# The governed write: curated's tables by name, as the grantor granted them to this account
# (data-governance/data/shares.tf). ALTER rides with the write, since an Iceberg commit rewrites the
# table's metadata.
resource "aws_lakeformation_permissions" "job_curated_write" {
  principal   = local.job_role_arn
  permissions = ["SELECT", "INSERT", "DELETE", "ALTER", "DESCRIBE"]

  table {
    catalog_id    = data.aws_caller_identity.lake.account_id
    database_name = data.terraform_remote_state.lake.outputs.database_names["curated"]
    wildcard      = true
  }
}

# ------------------------------------------------------------ the applications' database (1.3)
#
# What applications write to the outputs bucket, catalogued locally: the release's deploy creates its
# tables (Stage 8 3.2), the job role writes their rows, the persona reads them. The data sits under
# awsds-<env>-outputs, which no Lake Formation registration covers, so these grants govern the catalog
# and IAM and the bucket policy govern the objects.
resource "aws_glue_catalog_database" "app_outputs" {
  name        = "app_outputs"
  description = "Tables applications write to awsds-${var.env}-outputs (Stage 9 step 1.3)"

  depends_on = [module.consumer_data]
}

resource "aws_lakeformation_permissions" "release_app_outputs_database" {
  principal   = local.deploy_role_arn
  permissions = ["CREATE_TABLE", "DESCRIBE"]

  database {
    name = aws_glue_catalog_database.app_outputs.name
  }
}

resource "aws_lakeformation_permissions" "release_app_outputs_tables" {
  principal   = local.deploy_role_arn
  permissions = ["ALTER", "DROP", "DESCRIBE"]

  table {
    database_name = aws_glue_catalog_database.app_outputs.name
    wildcard      = true
  }
}

# The infrastructure user applies and destroys an application slice the deploy role may have applied
# (Stage 8 decision 27 and its 3.8 by hand). Lake Formation gives a table's creator its permissions and
# no one else, and the account's administrator holds DESCRIBE alone without a grant, so the user's
# destroy of a table the deploy role created is refused "Required Drop". The deploy role's catalog
# operations, no data permission.
resource "aws_lakeformation_permissions" "infrastructure_app_outputs_tables" {
  principal   = local.infrastructure_access_role_arn
  permissions = ["ALTER", "DROP", "DESCRIBE"]

  table {
    database_name = aws_glue_catalog_database.app_outputs.name
    wildcard      = true
  }
}

resource "aws_lakeformation_permissions" "job_app_outputs_database" {
  principal   = local.job_role_arn
  permissions = ["DESCRIBE"]

  database {
    name = aws_glue_catalog_database.app_outputs.name
  }
}

resource "aws_lakeformation_permissions" "job_app_outputs_tables" {
  principal   = local.job_role_arn
  permissions = ["SELECT", "INSERT", "DELETE", "ALTER", "DESCRIBE"]

  table {
    database_name = aws_glue_catalog_database.app_outputs.name
    wildcard      = true
  }
}

resource "aws_lakeformation_permissions" "persona_app_outputs_database" {
  principal   = local.data_scientist_role_arn
  permissions = ["DESCRIBE"]

  database {
    name = aws_glue_catalog_database.app_outputs.name
  }
}

resource "aws_lakeformation_permissions" "persona_app_outputs_tables" {
  principal   = local.data_scientist_role_arn
  permissions = ["SELECT", "DESCRIBE"]

  table {
    database_name = aws_glue_catalog_database.app_outputs.name
    wildcard      = true
  }
}
