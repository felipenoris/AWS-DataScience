# <env>/app/app-etl/ - the application's structure in a deployment target (Stage 8 steps 3.2 and 3.6,
# D41 item 9): its Glue job, awsds-<env>-app-etl (Stage 10 decision 20 (a)), which the workflow's
# transform task starts by name; the application's table in app_outputs, which that job writes and
# reads back (Stage 9 step 8.5); and in Production the warehouse load, awsds-prod-app-etl-load, which
# the workflow awsds-prod-wf-app-etl-warehouse starts (Stage 9 step 9.4, decision 15). Layer [E]: the
# Staging leg's `make down ENV=staging ONLY=app/app-etl` destroys it after the run (Stage 8 decision 27)
# and the user's `make down` otherwise, and `make up` never applies it (layers.py refusal 7); the
# pipeline applies it with the release it promotes.
#
# The job runs the release's script, which the release job copied under the release's prefix of the
# outputs bucket (Stage 10 decisions 1 and 12), as Stage 9's [P] awsds-<env>-job-exec, on the
# account's Glue connection, whose job group it carries (Stage 9 decision 12 (a)): the slice declares no
# network of its own. Its logs go to Glue's default groups, which sagemaker/ creates. The shape is the
# Glue task's create_job_kwargs in examples/app-etl/workflows/app-etl.yaml, where the operator creates
# the job in dev and test; the render drops those keys here (Stage 10 decision 6).
#
# The same file in staging/app/app-etl/ and production/app/app-etl/, byte for byte
# (./scripts/check-copies.py); release.tf is each account's own.

locals {
  name = "awsds-${var.env}-app-etl"

  outputs_bucket = data.terraform_remote_state.data.outputs.outputs_bucket_name
  release_prefix = var.release == null ? null : "s3://${local.outputs_bucket}/applications/app-etl/${var.release.tag}"

  # The governed source, read through Lake Formation's full-table-access mode on an Iceberg catalog over
  # the lake account's Glue catalog: Stage 9 step 2.4's settings, which committed curated.trades's write
  # on 2026-10-23, with the catalog named `lake`. The job reads with the account's regrants of the share,
  # SELECT and DESCRIBE, and its own role touches no lake prefix (D13).
  lake_catalog   = "lake"
  governed_table = "${local.lake_catalog}.${data.terraform_remote_state.data.outputs.curated_database}.${data.terraform_remote_state.data.outputs.curated_table}"
  lake_catalog_conf = join(" --conf ", [
    "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    "spark.sql.catalog.${local.lake_catalog}=org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.${local.lake_catalog}.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog",
    "spark.sql.catalog.${local.lake_catalog}.io-impl=org.apache.iceberg.aws.s3.S3FileIO",
    "spark.sql.catalog.${local.lake_catalog}.warehouse=s3://${data.terraform_remote_state.data.outputs.curated_bucket_name}/warehouse/",
    "spark.sql.catalog.${local.lake_catalog}.glue.id=${data.terraform_remote_state.data.outputs.lake_catalog_id}",
    "spark.sql.catalog.${local.lake_catalog}.glue.account-id=${data.terraform_remote_state.data.outputs.lake_catalog_id}",
    "spark.sql.catalog.${local.lake_catalog}.glue.region=${var.region}",
    "spark.sql.catalog.${local.lake_catalog}.client.region=${var.region}",
    "spark.sql.catalog.${local.lake_catalog}.glue.lakeformation-enabled=true",
    "spark.hadoop.fs.s3.credentialsResolverClass=com.amazonaws.glue.accesscontrol.AWSLakeFormationCredentialResolver",
    "spark.hadoop.fs.s3.useDirectoryHeaderAsFolderObject=true",
    "spark.hadoop.fs.s3.folderObject.autoAction.disabled=true",
  ])

  # The application's table, the prefix the workflow's --TABLE_PATH names in this account (the render's
  # `tables` class).
  table_name     = "trades_notional"
  table_location = "s3://${local.outputs_bucket}/app-etl/tables/${local.table_name}/"
}

resource "aws_glue_job" "this" {
  # checkov:skip=CKV_AWS_195:no security configuration - its CloudWatch encryption renames the job's log groups away from the ones sagemaker/ creates and the job role names, the outputs bucket's default encryption under the data key covers the job's writes, and the job keeps no bookmark
  count = var.release == null ? 0 : 1

  name              = local.name
  description       = "app-etl's Glue job (Stage 8 step 3.2): the release's glue/transform.py, started by the workflow awsds-${var.env}-wf-app-etl"
  role_arn          = data.terraform_remote_state.sagemaker.outputs.job_role_arn
  glue_version      = "6.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 50
  connections       = [data.terraform_remote_state.sagemaker.outputs.glue_connection_name]

  command {
    name            = "glueetl"
    script_location = "${local.release_prefix}/glue/transform.py"
    python_version  = "3"
  }

  # The governed read: --SOURCE_TABLE turns the script from the inbox to the governed table, on the
  # catalog --conf declares. The workflow's script arguments add the paths at each run.
  default_arguments = {
    "--SOURCE_TABLE"                     = local.governed_table
    "--datalake-formats"                 = "iceberg"
    "--conf"                             = local.lake_catalog_conf
    "--enable-continuous-cloudwatch-log" = "true"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  tags = {
    Name = local.name
  }
}

# The application's table: Parquet the Glue job overwrites and reads back at every run, declared here
# by the deploy role, which holds CREATE_TABLE on app_outputs (data/lakeformation.tf); the job role
# holds SELECT, INSERT, DELETE and ALTER on its tables, and the persona SELECT. Its location is in the
# outputs bucket, which Lake Formation does not register, so the job writes it with its own role.
resource "aws_glue_catalog_table" "trades_notional" {
  count = var.release == null ? 0 : 1

  database_name = data.terraform_remote_state.data.outputs.app_outputs_database
  name          = local.table_name
  description   = "app-etl's table: each trade with its notional, written by ${local.name} (Stage 9 step 8.5)"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
    EXTERNAL       = "TRUE"
  }

  storage_descriptor {
    location      = local.table_location
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "trade_date"
      type = "date"
    }

    columns {
      name = "desk"
      type = "string"
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

    columns {
      name = "notional"
      type = "double"
    }
  }
}

# Stage 9 step 9.4: the warehouse load, in Production alone, where the governed warehouse is. It reads
# the application's table and writes trades.trades_notional in the database governed over JDBC, on the
# account's Glue connection, whose group the warehouse's admits on its port (9.1); the compute is raised
# by hand, so a run with the workgroup down fails at GetWorkgroup.
resource "aws_glue_job" "load" {
  # checkov:skip=CKV_AWS_195:no security configuration - its CloudWatch encryption renames the job's log groups away from the ones sagemaker/ creates and the job role names; the job writes no S3 object and keeps no bookmark
  count = var.release != null && var.env == "prod" ? 1 : 0

  name              = "${local.name}-load"
  description       = "app-etl's warehouse load (Stage 9 step 9.4): the release's glue/load_warehouse.py, started by the workflow awsds-${var.env}-wf-app-etl-warehouse"
  role_arn          = data.terraform_remote_state.sagemaker.outputs.job_role_arn
  glue_version      = "6.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 20
  connections       = [data.terraform_remote_state.sagemaker.outputs.glue_connection_name]

  command {
    name            = "glueetl"
    script_location = "${local.release_prefix}/glue/load_warehouse.py"
    python_version  = "3"
  }

  default_arguments = {
    "--WORKGROUP"                        = "awsds-${var.env}-warehouse"
    "--DATABASE"                         = "governed"
    "--TARGET_TABLE"                     = "trades.${local.table_name}"
    "--enable-continuous-cloudwatch-log" = "true"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  tags = {
    Name = "${local.name}-load"
  }
}
