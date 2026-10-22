# Names and ARNs the slice's files share.

locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id

  # staging/data/'s buckets and the account data CMK, by the names that slice gives them at step 4.1.
  # They are contracts, spelled here rather than read from a state that does not exist yet:
  #   awsds-<env>-outputs   Stage 10 decision 17 (taken 2026-10-15): what awsds-prod-outputs holds
  #                         for a workflow in Production - its definition, code, result and inbox
  #   awsds-<env>-derived   step 4.2's results location, the name decision 11 recommends
  #   awsds-<env>-data      the mirror's content, read and written through Lake Formation alone
  #                         (step 4.1), so no statement below names it: D13's shape, as in Production
  outputs_bucket_arn = "arn:${local.partition}:s3:::awsds-${var.env}-outputs"
  derived_bucket_arn = "arn:${local.partition}:s3:::awsds-${var.env}-derived"
  data_key_alias     = "alias/awsds-${var.env}-data"
  account_key_arns   = "arn:${local.partition}:kms:${var.region}:${local.account_id}:key/*"

  # The groups a SageMaker job and a Glue job write to. Each service creates its own on first use
  # with no retention (EXC-10, measured at 6i and in this account at Stage 18 4.4), so the slice
  # declares them first (step 4.3). None existed here when the slice was written (read 2026-10-22).
  job_log_groups = toset([
    "/aws/sagemaker/ProcessingJobs",
    "/aws/sagemaker/TrainingJobs",
    "/aws/sagemaker/TransformJobs",
    "/aws-glue/jobs/output",
    "/aws-glue/jobs/error",
    "/aws-glue/jobs/logs-v2",
  ])

  region_account = "${local.partition}:ec2:${var.region}:${local.account_id}"
  repository_arn = data.terraform_remote_state.registry.outputs.ecr_repository_arns["app-etl"]
}
