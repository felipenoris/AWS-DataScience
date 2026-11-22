# Names and ARNs the slice's files share.

locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id

  # staging/data/'s buckets and the account data CMK, by the names that slice gives them at step 4.1.
  # They are contracts, spelled here rather than read from a state that does not exist yet:
  #   awsds-<env>-outputs   Stage 10 decision 17: what awsds-prod-outputs holds for a workflow in
  #                         Production - its definition, code, result and inbox
  #   awsds-<env>-derived   step 4.2's results location (decision 11)
  # The governed lake is read through Lake Formation alone (decision 3), so no statement names a lake
  # bucket: D13's shape, as in Production.
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

  # The groups' ARNs, built from the names: a policy document that referenced the group resources would
  # be read only at the apply of any change to a group, and its role policy would plan as an update.
  job_log_group_arns = [
    for name in local.job_log_groups : "arn:${local.partition}:logs:${var.region}:${local.account_id}:log-group:${name}"
  ]

  region_account = "${local.partition}:ec2:${var.region}:${local.account_id}"
  repository_arn = data.terraform_remote_state.registry.outputs.ecr_repository_arns["app-etl"]
}
