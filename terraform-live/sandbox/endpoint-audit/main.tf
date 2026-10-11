# A record of the S3 requests this account's VPC endpoints refuse (Stage 6i decision 7).
#
# An endpoint policy's refusal is S3's answer to the caller, and CloudTrail writes it to the bucket
# owner's trail, so a refused read of an AWS-owned bucket leaves nothing in this account. CloudTrail
# network activity events are the exception: the endpoint owner records the requests that pass
# through its endpoints, and errorCode VpceAccessDenied keeps only the refused ones. The store
# holds those alone, from this region, so it names the bucket a refused request wanted.
#
# The store is an instrument. It exists until decision 7 closes and is then destroyed by hand:
# termination protection is off, and the retention is the 7-day minimum.

resource "aws_cloudtrail_event_data_store" "endpoint_refusals" {
  # checkov:skip=CKV_AWS_294:a CMK is USD 1/key-month and its deletion window outlives this 7-day instrument; the store holds refusal metadata, not data - the judgement sandbox/warehouse records for its audit groups and Stage 3 for flow logs
  name                           = "awsds-${var.env}-endpoint-refusals"
  multi_region_enabled           = false
  organization_enabled           = false
  retention_period               = 7
  termination_protection_enabled = false
  billing_mode                   = "EXTENDABLE_RETENTION_PRICING"

  advanced_event_selector {
    name = "S3 requests a VPC endpoint policy refused"

    field_selector {
      field  = "eventCategory"
      equals = ["NetworkActivity"]
    }

    field_selector {
      field  = "eventSource"
      equals = ["s3.amazonaws.com"]
    }

    field_selector {
      field  = "errorCode"
      equals = ["VpceAccessDenied"]
    }
  }
}
