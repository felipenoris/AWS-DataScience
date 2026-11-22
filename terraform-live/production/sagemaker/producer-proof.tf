# Stage 9 step 2.4 - awsds-prod-producer-proof, the [P] Glue job that proves the producer pair
# (INT-03's governed write, the direct put refused) and the pickup (INT-10) before an application
# writes governed data. No promotion writes curated.trades: the template's Glue job turns the inbox
# into one CSV and carries no schema, so the proof needs a job of its own (read 2026-10-22).
#
# The job runs as awsds-prod-job-exec on the account's Glue connection (decision 12 (a)), inside
# VPC-Workloads: its S3 calls arrive through the gateway endpoint the lake trusts (1.4), its Glue
# and Lake Formation calls through the interface endpoints production/workloads-egress/ raises, so
# the job runs only in a Production sitting with that slice up. The script is proofs/producer_proof.py,
# uploaded by the infrastructure user under applications/stage-09-proofs/<version>/glue/ of the
# outputs bucket, the one prefix family the bucket's principal branch and the data key admit that
# principal to from the laptop (Stage 10 decision 12's exemption); the job reads it as the job role.
#
# The write goes through Lake Formation's full-table-access mode, the one mode a Glue Spark job
# writes a registered table in (AWS's page "Using AWS Glue with AWS Lake Formation for Full Table
# Access", read 2026-10-23): the catalog `lake` is Iceberg's Glue catalog over the lake account's
# catalog, with `glue.lakeformation-enabled` on, so the data files are read and written with the
# credentials Lake Formation vends, a session of the lake's registration role, and the job's own
# role touches no lake prefix (D13). Two readings the first run takes, each named in the step:
# whether the mode admits a writer holding INSERT, DELETE and ALTER without ALL, which that page
# says a write requires; and whether the mode needs AllowFullTableExternalDataAccess on this
# account's Lake Formation settings, unset here and in the lake on 2026-10-23, which the page's
# first step asks for. A refusal on either names the layer; the step carries the fallback of each.
#
# One run per mode, `--MODE` passed at start-job-run: `producer` inserts the sample rows and attempts
# the direct put; `pickup` curates the drop-box's dated prefix into the same table and deletes what
# it consumed. The job is [P] with its slice and costs nothing at rest; a run meters Glue's DPU-hours
# (two G.1X workers, ten minutes minimum).

locals {
  producer_proof_name    = "awsds-${var.env}-producer-proof"
  producer_proof_version = "v0"
  producer_proof_prefix  = "applications/stage-09-proofs/${local.producer_proof_version}"
  producer_proof_script  = "s3://awsds-${var.env}-outputs/${local.producer_proof_prefix}/glue/producer_proof.py"

  # The lake account, the Iceberg catalog's id: read from the lake state's key ARN rather than pasted
  # (aws/INDEX.md rule 1), and the slice reads that state already for the drop-box.
  lake_account_id = element(split(":", local.lake_key_arn), 4)
  lake_catalog    = "lake"

  # The Spark settings AWS's page gives for an Iceberg catalog in full-table-access mode, one `--conf`
  # each: the catalog over the lake account's Glue catalog with Lake Formation vending on, EMRFS
  # resolving a registered table's credentials through Lake Formation, and the directory-object
  # settings the vended credentials require. The warehouse is the curated bucket's Iceberg root, used
  # for new tables alone; the table the proof writes exists (data-governance/data/catalog.tf).
  producer_proof_spark_conf = join(" --conf ", [
    "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    "spark.sql.catalog.${local.lake_catalog}=org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.${local.lake_catalog}.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog",
    "spark.sql.catalog.${local.lake_catalog}.io-impl=org.apache.iceberg.aws.s3.S3FileIO",
    "spark.sql.catalog.${local.lake_catalog}.warehouse=s3://${local.curated_bucket}/warehouse/",
    "spark.sql.catalog.${local.lake_catalog}.glue.id=${local.lake_account_id}",
    "spark.sql.catalog.${local.lake_catalog}.glue.account-id=${local.lake_account_id}",
    "spark.sql.catalog.${local.lake_catalog}.glue.region=${var.region}",
    "spark.sql.catalog.${local.lake_catalog}.client.region=${var.region}",
    "spark.sql.catalog.${local.lake_catalog}.glue.lakeformation-enabled=true",
    "spark.hadoop.fs.s3.credentialsResolverClass=com.amazonaws.glue.accesscontrol.AWSLakeFormationCredentialResolver",
    "spark.hadoop.fs.s3.useDirectoryHeaderAsFolderObject=true",
    "spark.hadoop.fs.s3.folderObject.autoAction.disabled=true",
    "spark.sql.catalog.skipLocationValidationOnCreateTable.enabled=true",
    "spark.sql.catalog.createDirectoryAfterTable.enabled=true",
    "spark.sql.catalog.dropDirectoryBeforeTable.enabled=true",
  ])

  curated_bucket = data.terraform_remote_state.lake.outputs.bucket_names["curated"]
  dropbox_bucket = data.terraform_remote_state.lake.outputs.bucket_names["dropbox"]
}

resource "aws_glue_job" "producer_proof" {
  # checkov:skip=CKV_AWS_195:no security configuration - its CloudWatch encryption renames the job's log groups away from the ones this slice creates and the job role names; the table's data is written under the lake's key by Lake Formation's vended session, and the job keeps no bookmark
  name              = local.producer_proof_name
  description       = "Stage 9 step 2.4's proof: the governed write of curated.trades through the Production share and the drop-box pickup, as awsds-${var.env}-job-exec, one run per --MODE (producer, pickup)"
  role_arn          = module.job_role.role_arn
  glue_version      = "6.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 20
  connections       = [aws_glue_connection.jobs.name]

  command {
    name            = "glueetl"
    script_location = local.producer_proof_script
    python_version  = "3"
  }

  # The names the script reads, each from the state that owns it; --MODE is overridden per run. No
  # fine-grained-access flag: the two Lake Formation modes exclude each other, and only the
  # full-table mode writes.
  default_arguments = {
    "--MODE"                             = "producer"
    "--LAKE_CATALOG"                     = local.lake_catalog
    "--CURATED_DATABASE"                 = data.terraform_remote_state.lake.outputs.database_names["curated"]
    "--CURATED_TABLE"                    = data.terraform_remote_state.lake.outputs.producer_table_name
    "--CURATED_BUCKET"                   = local.curated_bucket
    "--DROPBOX_BUCKET"                   = local.dropbox_bucket
    "--DROPBOX_PREFIX"                   = local.dropbox_prefix
    "--datalake-formats"                 = "iceberg"
    "--conf"                             = local.producer_proof_spark_conf
    "--enable-continuous-cloudwatch-log" = "true"
    "--job-language"                     = "python"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  tags = {
    Name = local.producer_proof_name
  }
}
