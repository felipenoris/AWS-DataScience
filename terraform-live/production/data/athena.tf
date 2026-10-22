# Stage 9 step 1.2 - the enforced workgroup (decision 11). Enforced, the workgroup replaces the
# client's result location, encryption and expected bucket owner with its own (the console's "override
# client-side settings"), so every query's result lands under the derived bucket's results/ prefix,
# under the account data CMK, and a query past the scan limit is cancelled (decision 2). One enforced
# location, not one per principal: within-persona visibility of results is the stage's stated limit
# (risk 6, TM-19).

resource "aws_athena_workgroup" "this" {
  name        = "awsds-${var.env}-athena"
  description = "Enforced results location and scan limit for this account's queries (Stage 9 step 1.2)"
  state       = "ENABLED"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query     = var.scan_limit_bytes

    result_configuration {
      output_location       = "s3://${module.derived_bucket.bucket_name}/results/"
      expected_bucket_owner = local.account_id

      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = module.consumer_data.data_key_arn
      }
    }
  }
}
