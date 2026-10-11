# A record of the S3 requests this account's VPC endpoints refuse (Stage 6i decision 7).
#
# An endpoint policy's refusal is S3's answer to the caller, and CloudTrail writes it to the bucket
# owner's trail, so a refused read of an AWS-owned bucket leaves nothing in this account. CloudTrail
# network activity events are the exception: the endpoint owner records the requests that pass
# through its endpoints, and errorCode VpceAccessDenied keeps only the refused ones. The trail logs
# those alone, from this region, and no management event, which the organization trail already
# records, so it names the bucket a refused request wanted and nothing else.
#
# A trail and not a CloudTrail Lake event data store: CreateEventDataStore answered "CloudTrail Lake
# is no longer accepting new customers" for this account (2026-10-11).
#
# The trail and its bucket are an instrument. They exist until decision 7 closes and are then
# destroyed by hand: the bucket takes force_destroy, and its objects expire after 7 days.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  name      = "awsds-${var.env}-endpoint-refusals"
  account   = data.aws_caller_identity.current.account_id
  partition = data.aws_partition.current.partition
  trail_arn = "arn:${local.partition}:cloudtrail:${var.region}:${local.account}:trail/${local.name}"
}

resource "aws_s3_bucket" "refusals" {
  # checkov:skip=CKV_AWS_18:access logging = a second bucket about an instrument's own deliveries (Lesson 1)
  # checkov:skip=CKV_AWS_144:replication would copy data out of the one governed Region
  # checkov:skip=CKV2_AWS_62:no consumer for event notifications; the files are read by hand
  # checkov:skip=CKV_AWS_145:SSE-S3, since a CMK needs a CloudTrail grant in its key policy and outlives this 7-day instrument by its deletion window; the bucket holds refusal metadata, not data
  # checkov:skip=CKV_AWS_21:CloudTrail never writes a key twice, so no object would ever have a second version
  bucket        = local.name
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "refusals" {
  bucket = aws_s3_bucket.refusals.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "refusals" {
  bucket = aws_s3_bucket.refusals.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "refusals" {
  bucket = aws_s3_bucket.refusals.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "refusals" {
  bucket = aws_s3_bucket.refusals.id

  rule {
    id     = "expire-after-the-measurement"
    status = "Enabled"

    filter {}

    expiration {
      days = 7
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# TLS-only, and CloudTrail's two documented statements, each bound to this one trail by
# aws:SourceArn so no other trail can deliver here.
resource "aws_s3_bucket_policy" "refusals" {
  bucket = aws_s3_bucket.refusals.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = { AWS = "*" }
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.refusals.arn, "${aws_s3_bucket.refusals.arn}/*"]
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      },
      {
        Sid       = "CloudTrailAclCheck"
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "s3:GetBucketAcl"
        Resource  = aws_s3_bucket.refusals.arn
        Condition = { StringEquals = { "aws:SourceArn" = local.trail_arn } }
      },
      {
        Sid       = "CloudTrailWrite"
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.refusals.arn}/AWSLogs/${local.account}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"  = "bucket-owner-full-control"
            "aws:SourceArn" = local.trail_arn
          }
        }
      },
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.refusals]
}

resource "aws_cloudtrail" "refusals" {
  # checkov:skip=CKV_AWS_35:SSE-S3 on the bucket, for CKV_AWS_145's reason
  # checkov:skip=CKV_AWS_67:one region by design - the endpoints it watches are this region's
  # checkov:skip=CKV_AWS_252:no subscriber; the files are read by hand
  # checkov:skip=CKV2_AWS_10:no CloudWatch Logs delivery; the files are read by hand
  name                          = local.name
  s3_bucket_name                = aws_s3_bucket.refusals.id
  is_multi_region_trail         = false
  include_global_service_events = false
  enable_log_file_validation    = true
  enable_logging                = true

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

  # CreateTrail checks that it can write to the bucket, so the policy goes first.
  depends_on = [aws_s3_bucket_policy.refusals]
}
