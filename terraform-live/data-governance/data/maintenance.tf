# The catalog-maintenance role and its crawlers (step 3; D27) - the bounded set that
# produces catalog metadata, under one role, and the ONE principal the Data OU SCP's
# carve-out names.

# ------------------------------------------------------------------------- the role (3.2)
#
# THE NAME IS A CONTRACT, NOT A PREFERENCE: DenyCatalogMaintenanceRunsExceptMaintenanceRole
# (1c step 7.6) denies glue:StartCrawler, its schedule sibling and the column-statistics runs
# to every principal whose ARN is not exactly awsds-data-catalog-maintenance in this account
# (the table-optimizer actions are NOT in that list - POLICIES.md's Data OU non-coverage
# note). Under any other name the crawlers never run, failing closed with an error that
# names the OU policy, not the typo. ./aws/datalake.py DL-4 reads both the name and the trust.
#
# Trust: glue.amazonaws.com AND NOTHING ELSE - the role is not assumable interactively
# (D27); aws:SourceAccount pins the confused deputy. Its own protection is Stage 2's
# DenyIamPrincipalMutation on every persona set - verified by reading at 3.5, not rebuilt
# here.

module "catalog_maintenance_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-catalog-maintenance"
  description = "Glue crawlers over raw and the drop-box, Iceberg table optimizers (D27) - the one SCP carve-out principal"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "GlueServiceOnly"
        Effect    = "Allow"
        Principal = { Service = "glue.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })

  # Bespoke, never AWSGlueServiceRole (the conventions' IAM rules; D31's shape): each
  # statement names the job it exists for. The role DOES read data - a crawler samples
  # object contents to infer schema - which is D27's honest statement, scoped to exactly
  # the two crawled prefixes plus the compaction target.
  inline_policies = {
    catalog-maintenance = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "CrawlRawAndDropBox"
          Effect = "Allow"
          Action = ["s3:GetObject", "s3:ListBucket"]
          Resource = [
            local.bucket_arns["raw"],
            "${local.bucket_arns["raw"]}/*",
            local.bucket_arns["dropbox"],
            "${local.bucket_arns["dropbox"]}/${local.dropbox_prefix}/*",
          ]
        },
        {
          Sid    = "CompactCuratedWarehouse"
          Effect = "Allow"
          Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
          Resource = [
            local.bucket_arns["curated"],
            "${local.bucket_arns["curated"]}/warehouse/*",
          ]
        },
        {
          Sid      = "UseDataKey"
          Effect   = "Allow"
          Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
          Resource = module.data_key.key_arn
        },
        {
          Sid    = "CatalogReadWrite"
          Effect = "Allow"
          Action = [
            "glue:GetDatabase",
            "glue:GetDatabases",
            "glue:GetTable",
            "glue:GetTables",
            "glue:CreateTable",
            "glue:UpdateTable",
            "glue:BatchGetPartition",
            "glue:BatchCreatePartition",
            "glue:BatchUpdatePartition",
            "glue:GetPartition",
            "glue:GetPartitions",
            "glue:CreatePartition",
            "glue:UpdatePartition",
          ]
          Resource = [
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:catalog",
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/raw",
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/curated",
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:database/dropbox",
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/raw/*",
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/curated/*",
            "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:table/dropbox/*",
          ]
        },
        {
          # Measured at the first apply (2026-08-18): CreateCrawler with a security
          # configuration attached fails `not authorized to perform
          # glue:GetSecurityConfiguration` - the role must be able to READ the configuration
          # it runs under. Resource "*" because Glue security configurations have no ARN to
          # scope to; the account holds exactly one, created above.
          Sid      = "ReadOwnSecurityConfiguration"
          Effect   = "Allow"
          Action   = ["glue:GetSecurityConfiguration", "glue:GetSecurityConfigurations"]
          Resource = "*"
        },
        {
          Sid      = "VendedDataAccess"
          Effect   = "Allow"
          Action   = "lakeformation:GetDataAccess"
          Resource = "*"
        },
        {
          Sid      = "CrawlerLogs"
          Effect   = "Allow"
          Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
          Resource = "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*"
        },
      ]
    })
  }
}

# ------------------------------------- the role's own Lake Formation permissions (3.2, 4.2)
#
# With the IAM-fallback defaults emptied (5.2), catalog writes are governed by LF grants -
# including the maintenance role's own. OPERATIONAL grants, same-account, named-resource by
# design (TBAC is the CONSUMER method; this is machinery): each lands in the AWS_STATE.md
# grant register at apply. A crawler-created table grants its creator ALL automatically, so
# CREATE_TABLE is the whole crawler need; the optimizer needs the four verbs on the one
# table it compacts; DATA_LOCATION_ACCESS covers creating tables that point into the
# registered raw prefix (the drop-box is unregistered - no location grant exists to need).

resource "aws_lakeformation_permissions" "maintenance_create_raw" {
  principal   = module.catalog_maintenance_role.role_arn
  permissions = ["CREATE_TABLE", "DESCRIBE"]

  database { name = aws_glue_catalog_database.raw.name }
}

resource "aws_lakeformation_permissions" "maintenance_create_dropbox" {
  principal   = module.catalog_maintenance_role.role_arn
  permissions = ["CREATE_TABLE", "DESCRIBE"]

  database { name = aws_glue_catalog_database.dropbox.name }
}

resource "aws_lakeformation_permissions" "maintenance_raw_location" {
  principal   = module.catalog_maintenance_role.role_arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location { arn = aws_lakeformation_resource.raw.arn }
}

resource "aws_lakeformation_permissions" "maintenance_compact_sample" {
  principal   = module.catalog_maintenance_role.role_arn
  permissions = ["SELECT", "INSERT", "ALTER", "DESCRIBE"]

  table {
    database_name = aws_glue_catalog_database.curated.name
    name          = aws_glue_catalog_table.sample_trades.name
  }
}

# ------------------------------------------- the crawlers' encryption (added 2026-08-18)
#
# WHY THIS EXISTS AT ALL: it was not in the stage text - the commit gate found it
# (checkov CKV_AWS_195, "Glue component has a security configuration"), and the finding is
# real rather than a default worth skipping. D27's own honest sentence is that a crawler
# SAMPLES OBJECT CONTENTS to infer schema, so what it writes to CloudWatch sits closer to
# data than to metadata - and everything else touching this lake encrypts under the
# account data CMK. Leaving the logs under the AWS-managed key would be the one place the posture
# differs, for no reason anybody chose.
#
# WHAT IT COVERS, AND WHY ALL THREE MODES NAME THE KEY: for a CRAWLER only
# `cloudwatch_encryption` has a subject today - `s3_encryption` governs data a JOB writes
# (crawlers write to the catalog, not to S3) and bookmarks are a job concept, and
# `DenyUserCompute` denies Glue jobs in this account outright. The first draft therefore
# declared the other two DISABLED, and the gate was right to refuse it (CKV_AWS_99): a
# configuration that names the lake key for one mode and "off" for two is a statement about
# what happens to exist rather than about this lake, and it becomes a hole the day the
# configuration is attached to something that writes. Naming the key in all three says the
# whole thing once - the two without a subject cost nothing and cannot go stale.
#
# ITS ONE VISIBLE SIDE EFFECT: with a security configuration attached, Glue writes to
# /aws-glue/crawlers-role/<config>-<role> instead of /aws-glue/crawlers. The role's log
# statement is scoped to /aws-glue/* and covers both - deliberately, so this does not become
# a second thing to remember.

resource "aws_glue_security_configuration" "catalog_maintenance" {
  name = "awsds-${var.env}-catalog-maintenance"

  encryption_configuration {
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "SSE-KMS"
      kms_key_arn                = module.data_key.key_arn
    }

    s3_encryption {
      s3_encryption_mode = "SSE-KMS"
      kms_key_arn        = module.data_key.key_arn
    }

    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "CSE-KMS"
      kms_key_arn                   = module.data_key.key_arn
    }
  }
}

# ----------------------------------------------------------------------- the crawlers (3.6)
#
# Only where schema arrives from outside: the raw zone and the drop-box. NEVER on an Iceberg
# table (catalog-native; a crawler would fight the table's own metadata) and NEVER on a
# standing schedule (DPU-hour with a 10-minute minimum; cron-always out-costs the storage it
# catalogs) - both are DL-3's checks. The trigger today is ON-DEMAND, before a pickup;
# whether a compute-free event shape exists (S3 -> EventBridge -> Glue workflow, landing on
# the 3.4 service-guard side) is verification (iv), answered while executing, and the
# fallback costs only ordering.
#
# 4D MEASURED THE WORD THIS PARAGRAPH LEANED ON (2026-08-19/20; stage 5 log): "ON-DEMAND"
# HAS NO DEMANDER. The Data OU SCP admits StartCrawler only from the maintenance role or a
# service principal, the role's trust admits glue.amazonaws.com alone, and Schedule is null -
# so no person and no other service's role can demand a run, and the Glue scheduler never
# will (Lesson 22: closed by reading, after InfrastructureAccess measured the SCP deny).
# The no-cron choice above STANDS on its cost argument, DL-3 still checks it; what is open
# is the demander - open question 19, whose live candidate is exactly the event shape
# verification (iv) names, to be measured against the SCP's service guard rather than
# assumed to land on its allow side.

resource "aws_glue_crawler" "raw" {
  name          = "awsds-${var.env}-raw"
  database_name = aws_glue_catalog_database.raw.name
  role          = module.catalog_maintenance_role.role_arn

  security_configuration = aws_glue_security_configuration.catalog_maintenance.name

  s3_target {
    path = "s3://${local.bucket_names["raw"]}"
  }

  depends_on = [aws_lakeformation_permissions.maintenance_create_raw]
}

resource "aws_glue_crawler" "dropbox" {
  name          = "awsds-${var.env}-dropbox"
  database_name = aws_glue_catalog_database.dropbox.name
  role          = module.catalog_maintenance_role.role_arn

  security_configuration = aws_glue_security_configuration.catalog_maintenance.name

  s3_target {
    path = "s3://${local.bucket_names["dropbox"]}/${local.dropbox_prefix}"
  }

  depends_on = [aws_lakeformation_permissions.maintenance_create_dropbox]
}
