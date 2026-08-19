# The workgroup (Stage 5 step 8, D19 practice i) - the resource that makes "the output location
# is not the user's choice" a fact rather than a hope.
#
# EnforceWorkGroupConfiguration IS THE WHOLE POINT. The console calls it "override client-side
# settings"; without it the result location is whatever the client asks for, which makes the
# derived zone a suggestion and D19 practice (i) a comment. Every other setting here is
# ordinary; this one is the control.
#
# THE PRIMARY WORKGROUP IS DELIBERATELY LEFT ALONE (Lesson 5 - the absence is written down).
# Athena creates `primary` in every account and it enforces nothing. What keeps a persona out
# of it is not a setting on that workgroup but the IAM statement in identity/sso/, which scopes
# athena:StartQueryExecution to THIS workgroup's ARN and to no other. Deleting or reconfiguring
# `primary` from here would be Terraform adopting an object it did not create, in every account,
# for a defence the identity plane already provides.

resource "aws_athena_workgroup" "this" {
  name        = "awsds-${var.env}-athena"
  description = "The governed query path for this account - enforced result location in the derived zone, per-query scan cap (D19)"

  # [P] by D11: a workgroup costs nothing at rest and destroying it would orphan the query
  # history that explains what was run. force_destroy stays off for the same reason.
  state = "ENABLED"

  configuration {
    enforce_workgroup_configuration = true

    # Athena workgroup metrics are CloudWatch CUSTOM metrics and are billed as such
    # (docs/PRICING.md's discipline: measured, not assumed - and nothing here reads them yet).
    # Stage 12 owns dashboards and turns this on with a consumer in hand.
    publish_cloudwatch_metrics_enabled = false

    # The cost guard. A query over this limit is CANCELLED (var's note) - which bounds what a
    # runaway can bill, rather than zeroing it: the bytes scanned up to the cancellation are billed.
    bytes_scanned_cutoff_per_query = var.scan_limit_bytes

    result_configuration {
      # INTO THE DERIVED ZONE, not into a results bucket of its own (Stage 5 step 8's
      # instruction): query output then lands under the lifecycle, the CMK and the Macie scope
      # designed for it, instead of in a second, undesigned copy zone.
      output_location = "s3://${local.derived_bucket_name}/results/"

      # SSE-KMS under the account's zone key, stated rather than inherited from the bucket
      # default: the workgroup writes the object, so the workgroup is where the encryption
      # choice is visible to whoever reads this file. Same key, so the two cannot disagree.
      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = module.zone_key.key_arn
      }
    }
  }
}
