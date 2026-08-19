# The five buckets (steps 1.2, 1.4; docs/GOVERNANCE.md "Persistence") - one module call per
# name, every bucket [P] by construction (prevent_destroy in the module) and PERMANENT twice
# over here: DenyLakeDeletionAndDeregistration denies s3:DeleteBucket to every principal in
# this account, InfrastructureAccess included. Slow down exactly where it feels routine.
#
# DELIBERATELY NOT CREATED (step 1.5): an athena-results bucket. Query output lands in each
# consumer's own derived zone, behind its enforced workgroup - a results bucket here would be
# an undesigned copy zone inside the governed account.

# ------------------------------------------------------- the perimeter (step 1.3, INT-05)
#
# ONE DENY, THREE LEGITIMATE BRANCHES, on every bucket - the resource-side half of the
# trusted-networks axis (docs/plan/architecture.md 4.2), the data-perimeter-examples shape:
#
#   branch 1  aws:SourceVpce in the consumers' [P] GATEWAY endpoints - never the [E]
#             interface endpoints (Lesson 3, INT-05): those change id on every make up and
#             live in accounts this policy cannot see change.
#   branch 2  aws:SourceIp = the WireGuard Elastic IPs - a list, per D35 (D18's laptop path).
#   branch 3  aws:PrincipalAccount = this account - the stage's own "looser and easier to
#             get right" option, chosen DELIBERATELY over naming the maintenance role alone:
#             the crawler runs in Glue with no VPC and no tunnel (D27's collision), and the
#             infrastructure user works off-VPN by decision (open question 17, option a) -
#             a role-only branch would lock the account's own administrator out of the
#             console path to its own lake.
#
# And two carve-outs the deny must carry or it breaks the design it protects:
#   aws:ViaAWSService       - D13 forces every tabular read through Athena/Lake Formation
#                             vended access, which arrives as a service-on-behalf call; a
#                             bare SourceVpce deny makes step 6 unusable (stage step 1.3).
#   aws:PrincipalIsAWSService - a service principal (CloudTrail delivering Stage 11's
#                             data-event trails into awsds-data-logs) presents no VPC, no
#                             IP and no account; without the guard the deny eats the
#                             delivery (the 3.4 shape, on a bucket).
#
# Plus the s3:signatureAge cap - the preventive counterpart of Stage 11's presigned-URL
# detection: a presigned link is a bearer credential, and 15 minutes bounds how long a
# leaked one works. Milliseconds, per the condition key.

locals {
  perimeter_statements = {
    for k, arn in local.bucket_arns : k => [
      {
        Sid       = "DenyOutsideTrustedNetworks"
        Effect    = "Deny"
        Principal = { AWS = "*" }
        Action    = "s3:*"
        Resource  = [arn, "${arn}/*"]
        Condition = {
          StringNotEquals = {
            "aws:SourceVpce"       = local.consumer_vpce_ids
            "aws:PrincipalAccount" = data.aws_caller_identity.current.account_id
          }
          NotIpAddress = { "aws:SourceIp" = local.wireguard_eip_cidrs }
          BoolIfExists = {
            "aws:ViaAWSService"         = "false"
            "aws:PrincipalIsAWSService" = "false"
          }
        }
      },
      {
        Sid       = "DenyStalePresignedUrls"
        Effect    = "Deny"
        Principal = { AWS = "*" }
        Action    = "s3:*"
        Resource  = [arn, "${arn}/*"]
        Condition = { NumericGreaterThan = { "s3:signatureAge" = "900000" } }
      },
    ]
  }

  # The drop-box asymmetry (step 1.4; D18, D25, D27): three principals, three statements,
  # nobody holding two of the three. The WRITER cannot read back or list - confirmation is
  # the PutObject response; versioning keeps overwritten versions internally. The date in
  # the key is a convention (incoming/<yyyy>/<mm>/<dd>/...); the policy scopes the prefix.
  dropbox_statements = [
    {
      Sid       = "AllowInteractiveWriterPutOnly"
      Effect    = "Allow"
      Principal = { AWS = [local.sandbox_root, local.development_root] }
      Action    = "s3:PutObject"
      Resource  = "${local.bucket_arns["dropbox"]}/${local.dropbox_prefix}/*"
      Condition = { ArnLike = { "aws:PrincipalArn" = local.writer_role_patterns } }
    },
    {
      Sid       = "AllowProductionPickupReadDelete"
      Effect    = "Allow"
      Principal = { AWS = local.production_root }
      Action    = ["s3:GetObject", "s3:DeleteObject"]
      Resource  = "${local.bucket_arns["dropbox"]}/${local.dropbox_prefix}/*"
      Condition = { ArnLike = { "aws:PrincipalArn" = local.prod_job_exec_pattern } }
    },
    {
      Sid       = "AllowProductionPickupList"
      Effect    = "Allow"
      Principal = { AWS = local.production_root }
      Action    = "s3:ListBucket"
      Resource  = local.bucket_arns["dropbox"]
      Condition = {
        ArnLike    = { "aws:PrincipalArn" = local.prod_job_exec_pattern }
        StringLike = { "s3:prefix" = "${local.dropbox_prefix}/*" }
      }
    },
    # Same-account IAM would suffice for the maintenance role (its inline policy carries the
    # read) - the statement is here so the asymmetry is READABLE in one place, which is what
    # keeps the drop-box from quietly becoming the exchange bucket D18 refuses.
    {
      Sid       = "AllowMaintenanceSchemaRead"
      Effect    = "Allow"
      Principal = { AWS = module.catalog_maintenance_role.role_arn }
      Action    = ["s3:GetObject", "s3:ListBucket"]
      Resource  = [local.bucket_arns["dropbox"], "${local.bucket_arns["dropbox"]}/${local.dropbox_prefix}/*"]
    },
  ]
}

module "bucket" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.2.0"

  for_each = local.bucket_names

  bucket_name = each.value
  kms_key_arn = module.data_key.key_arn

  # A for-expression, not a ternary: the two ternary arms (four statements vs none) are
  # tuples of different lengths and Terraform refuses the conditional before the module's
  # `any` could accept either.
  additional_policy_statements = concat(
    local.perimeter_statements[each.key],
    [for s in local.dropbox_statements : s if each.key == "dropbox"],
  )
}
