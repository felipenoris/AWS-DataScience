# The state bucket and the key that encrypts it - Stage 2 step 2.1. NOTHING ELSE.
#
# WHY THIS SLICE CONSUMES NO MODULE (step 2.3). terraform-modules/s3-bucket and kms-key arrive
# at step 7, and docs/plan/conventions.md requires modules to be consumed BY GIT TAG - which
# cannot exist before the module does. Beyond the ordering: bootstrap is the slice that makes
# every other slice possible, and giving it a dependency on the tree it bootstraps is how a
# repository acquires a cycle nobody can unwind at 23:00. Plain resources, deliberately, and
# they stay that way after step 7 exists.
#
# LAYER [P] (D11). Nothing here is destroyed between sessions and `make down` cannot reach it -
# the bucket holds its own state, so destroying it is a two-phase operation in reverse. That is
# what prevent_destroy says out loud.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# ---------------------------------------------------------------------------- the state key
#
# WHICH KEY THIS IS (step 2.4), since conventions §6 puts "KMS keys" in foundation/: it is not
# that key and it cannot be - foundation/ does not exist at bootstrap time, and identity/ and
# data-governance/ have no foundation/ slice at all. This is the one-per-Terraform-managed-
# account STATE key that docs/PRICING.md §2 already counts at ~USD 1.00/key-month. A
# foundation/ key, where one exists, is the general-purpose key for that account's data and
# logs, and it is an ADDITIONAL object: a key shared between state and data makes "who may read
# the state" and "who may read the data" the same question (the D31/D36 argument, one level
# down).

resource "aws_kms_key" "tfstate" {
  description = "Terraform state encryption - ${var.env}"

  enable_key_rotation     = true
  deletion_window_in_days = 30

  # THE KEY POLICY IS THE ONLY PLACE "WHO CAN READ THIS STATE" IS EXPRESSED, which is why it is
  # written out rather than left to the service default (they are the same document; writing it
  # makes it reviewable, and checkov requires it). It delegates to IAM instead of enumerating
  # principals: the account's IAM policies decide, and today that means InfrastructureAccess.
  # Lesson 18 applies and is worth stating - the infrastructure user AUTHORS this policy, so it
  # does not constrain them; what remains is the CloudTrail record of a kms:Decrypt.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableIamPolicyDelegationInThisAccount"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      }
    ]
  })

  tags = {
    Name = "awsds-${var.env}-tfstate"
  }
}

resource "aws_kms_alias" "tfstate" {
  name          = "alias/awsds-${var.env}-tfstate"
  target_key_id = aws_kms_key.tfstate.key_id
}

# ------------------------------------------------------------------------- the state bucket

# THREE CHECKOV SUPPRESSIONS, DECIDED HERE RATHER THAN DISCOVERED AT THE KEYBOARD (step 6.5).
# A state bucket trips all three by construction, and each reason is structural:
#
#   CKV_AWS_18  server access logging would be a SECOND bucket in this account holding a
#               record of every read of the state - the same secrets, one governance layer
#               thinner (Lesson 1). CloudTrail already records the API calls that matter and
#               Stage 11 owns S3 data events.
#   CKV_AWS_144 cross-region replication is a Stage 12 item with no line in
#               docs/plan/cost-model.md, and it would put a readable copy of every state file
#               outside the single Region this organization is confined to (1d step 12).
#   CKV2_AWS_62 event notifications have no consumer: there is no queue, no topic and no
#               function in this account, and Stage 12 is where "who is told when state
#               changes" becomes a question with an answer.
#
# The skips are INSIDE the resource because that is where checkov reads them - above the block
# they are ordinary comments and the check fails anyway, which is how the first run of this
# slice was measured.
resource "aws_s3_bucket" "tfstate" {
  # checkov:skip=CKV_AWS_18:access logging = a second bucket with the same secrets (see above)
  # checkov:skip=CKV_AWS_144:replication is Stage 12, and it would copy state out of Region
  # checkov:skip=CKV2_AWS_62:no consumer for the notifications exists in this account
  bucket = "awsds-${var.env}-tfstate"

  # Both halves of docs/plan/conventions.md §5.1 rule 1, and they say different things:
  # force_destroy refuses to empty the bucket, prevent_destroy refuses to plan its removal.
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.tfstate.arn
    }

    # S3 Bucket Keys - docs/plan/cost-model.md. Without this, every object write is its own
    # kms:GenerateDataKey call at USD 0.03/10k; with it, one call covers many objects. A state
    # file is written on every apply, so this is not theoretical.
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# TLS-ONLY, WRITTEN RATHER THAN INHERITED. checkov demands it at step 6.5 anyway, and a policy
# the linter adds for you is a policy nobody read. It denies the transport, not the principal:
# the deny is on aws:SecureTransport = false, so it costs nothing and closes the one case where
# a state file could cross a network in clear text.
resource "aws_s3_bucket_policy" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  policy = data.aws_iam_policy_document.tfstate.json

  # The public access block must be in place BEFORE a bucket policy is attached, or S3 can
  # reject the policy as public-granting on a bucket that is not yet closed. Terraform cannot
  # infer this from the arguments - both resources only reference the bucket.
  depends_on = [aws_s3_bucket_public_access_block.tfstate]
}

data "aws_iam_policy_document" "tfstate" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.tfstate.arn,
      "${aws_s3_bucket.tfstate.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# EVERY APPLY WRITES A VERSION, and a lifecycle rule added later does not reach what has
# already accumulated - which is the whole reason this is here on day one rather than at
# Stage 12. The retention is a cost choice (step 2, decision 3), not a compliance one.
resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    id     = "expire-noncurrent-state-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.state_noncurrent_version_days
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

  # The bucket must be versioned before a noncurrent-version rule means anything.
  depends_on = [aws_s3_bucket_versioning.tfstate]
}
