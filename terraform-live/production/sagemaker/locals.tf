# Names and ARNs the three files of this slice share.

locals {
  partition  = data.aws_partition.current.partition
  account_id = data.aws_caller_identity.current.account_id

  # Step 1.1's and 1.2's buckets and the account data CMK, by the names production/data/ gives them
  # at pass 3. They are contracts (./aws/deploytargets.py OUT_BUCKET, RESULTS_BUCKET and
  # PROD_CMK_ALIAS), so they are spelled here rather than read from a state that does not exist yet.
  outputs_bucket_arn = "arn:${local.partition}:s3:::awsds-${var.env}-outputs"
  derived_bucket_arn = "arn:${local.partition}:s3:::awsds-${var.env}-derived"
  data_key_alias     = "alias/awsds-${var.env}-data"
  account_key_arns   = "arn:${local.partition}:kms:${var.region}:${local.account_id}:key/*"

  # The groups a SageMaker job and a Glue job write to. Each service creates its own on first use
  # with no retention (EXC-10, measured at 6i), so the slice declares them first (step 3.1).
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
}
