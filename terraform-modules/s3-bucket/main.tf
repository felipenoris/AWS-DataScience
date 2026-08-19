# s3-bucket - the bucket shape Stage 2's bootstrap slices proved, as a module: versioning,
# SSE-KMS with BUCKET KEYS ON and PUBLIC ACCESS BLOCKED UNCONDITIONALLY (Stage 3 step 1.1a's
# carried-over requirements - neither is a variable, deliberately), a TLS-only bucket policy,
# a noncurrent-version lifecycle, and prevent_destroy - which cannot be parameterised
# (lifecycle meta-arguments are static), so every bucket from this module is [P] by
# construction. An [E] bucket is a different thing and does not come from here.

# The three structural checkov suppressions of the bootstrap slices, same reasons (Stage 2
# step 6.5): access logging = a second bucket with the same content one governance layer
# thinner (Lesson 1); replication = a copy out of the one governed Region (1d step 12), Stage
# 12's question; notifications have no consumer before Stage 12. Skips must sit INSIDE the
# block - above it they are ordinary comments and checkov fails anyway (measured, Stage 2).
resource "aws_s3_bucket" "this" {
  # checkov:skip=CKV_AWS_18:access logging = a second bucket with the same content (Lesson 1)
  # checkov:skip=CKV_AWS_144:replication would copy data out of the one governed Region
  # checkov:skip=CKV2_AWS_62:no consumer for event notifications exists before Stage 12
  bucket = var.bucket_name

  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }

    # Bucket Keys on, unconditionally (1.1a): without them a data bucket issues a KMS request
    # per object operation (docs/plan/cost-model.md). The audit-granularity trade is recorded
    # at the bootstrap key (Stage 2 step 2.4) and re-asked only at D36's alarm.
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# TLS-only always; the caller's own statements (a perimeter branch, a drop-box asymmetry -
# Stage 5) are appended through var.additional_policy_statements, because S3 holds exactly
# ONE policy per bucket and a second aws_s3_bucket_policy would silently replace this one.
resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Sid       = "DenyInsecureTransport"
          Effect    = "Deny"
          Principal = { AWS = "*" }
          Action    = "s3:*"
          Resource  = [aws_s3_bucket.this.arn, "${aws_s3_bucket.this.arn}/*"]
          Condition = { Bool = { "aws:SecureTransport" = "false" } }
        }
      ],
      var.additional_policy_statements,
    )
  })

  # The public access block must exist before a policy is attached, or S3 can reject the
  # policy as public-granting on a bucket not yet closed (Stage 2, measured).
  depends_on = [aws_s3_bucket_public_access_block.this]
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # THE ONLY RULE THAT DELETES SOMETHING NOBODY REPLACED (v0.3.0, Stage 5 pass 4). The two
  # rules above are hygiene - a superseded version, an upload that never finished - and they
  # are unconditional because no caller wants either kept. This one removes a CURRENT object,
  # so it is opt-in and its absence is the default: a bucket whose contents disappear on a
  # timer is a decision about the DATA, and only the caller knows whether its bucket holds
  # results (D19: disposable by design) or the only copy of something.
  dynamic "rule" {
    for_each = var.expiration_days == null ? [] : [var.expiration_days]

    content {
      id     = "expire-current-versions"
      status = "Enabled"

      filter {}

      expiration {
        days = rule.value
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.this]
}
