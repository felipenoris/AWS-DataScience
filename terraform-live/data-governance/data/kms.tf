# The account data CMK (step 1.1, decision 2) - one key for the whole lake, drop-box included:
# encryption granularity is per account (docs/GOVERNANCE.md "Encryption"), and this account holds
# the five lake buckets. The binding is each bucket's default-encryption configuration
# (buckets.tf); no catalog attribute is involved. A dataset whose blast radius argues for a key of
# its own is a new module call here plus Bucket Keys re-pointing - a bucket-level change, not a
# migration.
#
# The policy is passed rather than defaulted, because two cross-account statements must ride on
# the key object (Lesson 14):
#
#   - the drop-box writers (D18): SSE-KMS PutObject needs GenerateDataKey, and a multipart
#     upload needs Decrypt with it (the error otherwise names S3, not KMS - stage step 1.4's
#     warning). Scoped kms:ViaService=S3, so the persona cannot use the key outside an S3 call.
#   - the pickup (D25, INT-10): awsds-prod-job-exec reads SSE-KMS objects, so kms:Decrypt.
#     The role exists at Stage 9; until then the ArnLike matches nothing, which is the
#     recorded "pickup half unexercised" state.
#
# What the single key costs (decision 3's deviation, docs/GOVERNANCE.md "Encryption"): these
# grants land on the account key, so at the KMS layer the matched principals reach every lake
# bucket - the drop-box's isolation rests on the S3 statements and Lake Formation alone.

# The module address moved from zn_lab_key to data_key; this block keeps the applied key object
# in place and can be dropped once every caller has applied.
moved {
  from = module.zn_lab_key
  to   = module.data_key
}

module "data_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-data"
  description = "Account data CMK - SSE-KMS for every lake bucket (raw, curated, artifacts, logs, dropbox)"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableIamPolicyDelegationInThisAccount"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowDropBoxWritersViaS3"
        Effect    = "Allow"
        Principal = { AWS = [local.sandbox_root] }
        Action    = ["kms:GenerateDataKey", "kms:Decrypt"]
        Resource  = "*"
        Condition = {
          StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
          ArnLike      = { "aws:PrincipalArn" = local.writer_role_patterns }
        }
      },
      {
        # The crawlers' log encryption (maintenance.tf's security configuration): CloudWatch
        # Logs encrypts with the key itself, as a service principal - the crawler role's own
        # KMS grant does not cover it. Scoped by the log-group encryption context, so the
        # service can use this key for /aws-glue/* in this account and for nothing else.
        Sid       = "AllowCloudWatchLogsEncryptionForGlue"
        Effect    = "Allow"
        Principal = { Service = "logs.${var.region}.amazonaws.com" }
        Action    = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:Describe*"]
        Resource  = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*"
          }
        }
      },
      {
        Sid       = "AllowProductionPickupDecryptViaS3"
        Effect    = "Allow"
        Principal = { AWS = local.production_root }
        Action    = "kms:Decrypt"
        Resource  = "*"
        Condition = {
          StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
          ArnLike      = { "aws:PrincipalArn" = local.prod_job_exec_pattern }
        }
      },
    ]
  })
}
