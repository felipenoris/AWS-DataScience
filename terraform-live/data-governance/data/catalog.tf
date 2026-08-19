# The catalog (steps 3.1, 4.1, 4.2) - three databases, the sample Iceberg table, and its
# maintenance owner. EVERY DATABASE depends_on THE SETTINGS TRIO: the IAM-fallback defaults
# act at creation time, so a database created before 5.2 lands is born deferring to IAM and
# clearing the default later does not reach it (the measured 2026-08-18 finding).

# --------------------------------------------------------------------- the three databases
#
# raw and curated are step 3.1's; dropbox is pass 1's answer to the question
# docs/GOVERNANCE.md left open ("which catalog database holds the drop-box crawler's
# inferred tables is fixed at Stage 5 pass 1"): its own database, so crawler-created tables
# inherit layer=dropbox rather than wearing raw's value wrongly.

resource "aws_glue_catalog_database" "raw" {
  name = "raw"

  depends_on = [aws_lakeformation_data_lake_settings.this]
}

resource "aws_glue_catalog_database" "curated" {
  name = "curated"

  depends_on = [aws_lakeformation_data_lake_settings.this]
}

resource "aws_glue_catalog_database" "dropbox" {
  name = "dropbox"

  depends_on = [aws_lakeformation_data_lake_settings.this]
}

# ------------------------------------------------- the tag assignments (5.1, GOVERNANCE.md)
#
# Inheritance does the rest: a database's tags flow to its tables and their columns unless
# overridden below. The asymmetry between raw and curated is decision 1's, verbatim:
# raw (and dropbox, same rationale - user-supplied arrivals) carry classification=internal,
# the FAIL-OPEN default the user chose; curated carries NO classification at the database -
# an untagged table there matches no TBAC expression and is invisible, fail-closed by
# absence.

resource "aws_lakeformation_resource_lf_tags" "raw_db" {
  database { name = aws_glue_catalog_database.raw.name }

  lf_tag {
    key   = aws_lakeformation_lf_tag.layer.key
    value = "raw"
  }
  lf_tag {
    key   = aws_lakeformation_lf_tag.classification.key
    value = "internal"
  }
  lf_tag {
    key   = aws_lakeformation_lf_tag.security_zone.key
    value = "zn-lab"
  }
}

resource "aws_lakeformation_resource_lf_tags" "curated_db" {
  database { name = aws_glue_catalog_database.curated.name }

  lf_tag {
    key   = aws_lakeformation_lf_tag.layer.key
    value = "curated"
  }
  lf_tag {
    key   = aws_lakeformation_lf_tag.security_zone.key
    value = "zn-lab"
  }
}

resource "aws_lakeformation_resource_lf_tags" "dropbox_db" {
  database { name = aws_glue_catalog_database.dropbox.name }

  lf_tag {
    key   = aws_lakeformation_lf_tag.layer.key
    value = "dropbox"
  }
  lf_tag {
    key   = aws_lakeformation_lf_tag.classification.key
    value = "internal"
  }
  lf_tag {
    key   = aws_lakeformation_lf_tag.security_zone.key
    value = "zn-lab"
  }
}

# ----------------------------------------------------------- the sample Iceberg table (4.1)
#
# The stage's working piece - the share deliverables query it from both consumers, and the
# classification pair reads its column list. Created through the Glue API's Iceberg path
# (metadata_operation CREATE writes the initial metadata to S3) - no crawler ever points at
# it (D27: Iceberg is catalog-native), and no Athena DDL is needed in this account, which
# is what lets 4.3's SCP amendment sequence freely.

resource "aws_glue_catalog_table" "sample_trades" {
  name          = "sample_trades"
  database_name = aws_glue_catalog_database.curated.name
  table_type    = "EXTERNAL_TABLE"

  open_table_format_input {
    iceberg_input {
      metadata_operation = "CREATE"
      version            = "2"
    }
  }

  storage_descriptor {
    location = "s3://${local.bucket_names["curated"]}/warehouse/sample_trades"

    columns {
      name = "trade_id"
      type = "bigint"
    }
    columns {
      name = "trade_date"
      type = "date"
    }
    columns {
      name = "instrument"
      type = "string"
    }
    columns {
      name = "quantity"
      type = "double"
    }
    columns {
      name = "price"
      type = "double"
    }
    # The deliberately restricted column (4.1, revised 2026-08-17): the share deliverable
    # must prove entitlement SCOPED BY THE SCHEME - this column absent from a default
    # consumer read - not merely that the share works.
    columns {
      name = "counterparty"
      type = "string"
    }
  }

  depends_on = [module.bucket]
}

# Table-level classification - curated's database carries none (fail-closed by absence), so
# the sample table declares its own; the restricted column overrides it below, most-specific
# wins.
resource "aws_lakeformation_resource_lf_tags" "sample_trades_table" {
  table {
    database_name = aws_glue_catalog_database.curated.name
    name          = aws_glue_catalog_table.sample_trades.name
  }

  lf_tag {
    key   = aws_lakeformation_lf_tag.classification.key
    value = "internal"
  }
}

resource "aws_lakeformation_resource_lf_tags" "sample_trades_restricted_column" {
  table_with_columns {
    database_name = aws_glue_catalog_database.curated.name
    name          = aws_glue_catalog_table.sample_trades.name
    column_names  = ["counterparty"]
  }

  lf_tag {
    key   = aws_lakeformation_lf_tag.classification.key
    value = "restricted"
  }
}

# --------------------------------------------------- the maintenance owner (4.2, decision 4)
#
# Glue automatic compaction under the maintenance role - the table-optimizer runs the D27
# carve-out and the Data OU SCP already name, no scheduler in a no-compute account. Config is
# free at rest; runs are metered (USD 0.44/DPU-h, docs/PRICING.md 5). The consequence
# accepted with the decision - athena:StartQueryExecution joining DenyUserCompute - is an
# SCP act (battery phase 4b), not this slice's.

resource "aws_glue_catalog_table_optimizer" "sample_trades_compaction" {
  catalog_id    = data.aws_caller_identity.current.account_id
  database_name = aws_glue_catalog_database.curated.name
  table_name    = aws_glue_catalog_table.sample_trades.name
  type          = "compaction"

  configuration {
    role_arn = module.catalog_maintenance_role.role_arn
    enabled  = true
  }
}
