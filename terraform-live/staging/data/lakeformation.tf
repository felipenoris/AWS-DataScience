# Stage 9 step 4.1 - what the account's Lake Formation administrator grants locally: the read the
# share gives, regranted to the job role. Staging received DESCRIBE and SELECT alone (decision 3), so
# it can regrant nothing more.
#
# The local regrant is a pair (measured at Stage 5a pass 4): DESCRIBE on the resource link, a local
# database, and the permission on the target, addressed through the lake's catalog id. Without the
# first the principal sees no database at all, holding every permission on the target.
#
# Every grant below needs the second apply of Recipe D (main.tf): the first seats the administrator
# and clears the create-time defaults. The regrants on the lake's objects need the share as well, so
# this slice applies after data-governance/data/'s Stage 9 change, and after staging/sagemaker/, since
# Lake Formation refuses a grant to a role that does not exist.

# ---------------------------------------------------------------- the job role on the lake

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
