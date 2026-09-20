# The five buckets (steps 1.2, 1.4; docs/GOVERNANCE.md "Persistence") - one module call per name,
# every bucket [P] by construction (prevent_destroy in the module) and permanent twice over here:
# DenyLakeDeletionAndDeregistration denies s3:DeleteBucket to every principal in this account,
# InfrastructureAccess included.
#
# There is no athena-results bucket (step 1.5). Query output lands in each consumer's own derived
# zone (the SMUS project path since 2026-08-26, D19); a results bucket here would be an
# undesigned copy zone inside the governed account.

# ------------------------------------------------------- the perimeter (step 1.3, INT-05)
#
# One deny on every bucket - the resource-side half of the trusted-networks axis
# (docs/plan/architecture.md 4.2), in the data-perimeter-examples shape. Its legitimate branches:
#
#   branch 1  aws:SourceVpce in the consumers' [P] gateway endpoints, never the [E] interface
#             endpoints (Lesson 3, INT-05): those change id on every make up and live in
#             accounts this policy cannot see change.
#   branch 2  aws:PrincipalAccount = this account - the stage's own "looser and easier to
#             get right" option, chosen over naming the maintenance role alone: the crawler
#             runs in Glue with no VPC (D27's collision), and the infrastructure user works from
#             any network, so a role-only branch would lock the account's own administrator out
#             of the console path to its own lake.
#
# No branch names an address (D39). The one laptop path the lake carries, D18's drop-box write,
# is admitted by principal on the drop-box alone (dropbox_statements below).
#
# The carve-outs the deny must carry, or it breaks the design it protects:
#   aws:ViaAWSService       - D13 forces every tabular read through Athena/Lake Formation
#                             vended access, which arrives as a service-on-behalf call; a
#                             bare SourceVpce deny makes step 6 unusable (stage step 1.3).
#   aws:PrincipalIsAWSService - a service principal (CloudTrail delivering Stage 11's
#                             data-event trails into awsds-data-logs) presents no VPC, no
#                             IP and no account; without the guard the deny eats the
#                             delivery (the 3.4 shape, on a bucket).
#
# The s3:signatureAge cap is the preventive counterpart of Stage 11's presigned-URL detection: a
# presigned link is a bearer credential, and 15 minutes bounds how long a leaked one works.
# Milliseconds, per the condition key.

locals {
  # The test every perimeter statement shares: the call came through no consumer's gateway
  # endpoint, from no principal of this account, and not from a service acting for its caller.
  outside_trusted_networks = {
    StringNotEquals = {
      "aws:SourceVpce"       = local.trusted_vpce_ids
      "aws:PrincipalAccount" = data.aws_caller_identity.current.account_id
    }
    BoolIfExists = {
      "aws:ViaAWSService"         = "false"
      "aws:PrincipalIsAWSService" = "false"
    }
  }

  # The drop-box's network deny is in dropbox_statements, split so the writer's put is the one call
  # the lake admits from any network. A for-expression filter rather than a ternary, for the
  # reason the module call below gives.
  perimeter_statements = {
    for k, arn in local.bucket_arns : k => concat(
      [for s in [
        {
          Sid       = "DenyOutsideTrustedNetworks"
          Effect    = "Deny"
          Principal = { AWS = "*" }
          Action    = "s3:*"
          Resource  = [arn, "${arn}/*"]
          Condition = local.outside_trusted_networks
        },
      ] : s if k != "dropbox"],
      [
        {
          Sid       = "DenyStalePresignedUrls"
          Effect    = "Deny"
          Principal = { AWS = "*" }
          Action    = "s3:*"
          Resource  = [arn, "${arn}/*"]
          Condition = { NumericGreaterThan = { "s3:signatureAge" = "900000" } }
        },
      ],
    )
  }

  # The drop-box asymmetry (step 1.4; D18, D25, D27): three principals, three statements, nobody
  # holding two of the three. The writer cannot read back or list - confirmation is the PutObject
  # response, and versioning keeps overwritten versions internally. The date in the key is a
  # convention (incoming/<yyyy>/<mm>/<dd>/...); the policy scopes the prefix.
  #
  # Measured 2026-08-20 (Stage 5a pass 4d): the persona's PutObject succeeds; GetObject,
  # ListObjectsV2 and DeleteObject are each denied implicitly. The delete is worth stating - a
  # writer that can retract is a writer that can launder, so put-only is a claim about retraction
  # as well as about reading. AllowInteractiveWriterPutOnly is exercised, not merely attached
  # (Lesson 20). One residue by design: the writer cannot clean up after itself and the collector
  # is Stage 9's awsds-prod-job-exec, which does not exist yet, so the proof object is
  # uncollectable until then - AWS_STATE.md EXC-02 declares it so a later snapshot does not read
  # it as someone writing to the drop-box outside a recorded proof.
  dropbox_statements = [
    # The drop-box's network deny, in three statements so the writer's put is the one call the
    # lake admits from any network (D39): outside the trusted networks every other action is
    # refused to everyone, a put into the letterbox to everyone but the writer, and a put anywhere
    # else in the bucket to everyone. The writer is named by its own pattern and not through
    # writer_role_patterns, which grows with workload roles that keep the network test.
    {
      Sid       = "DenyOutsideTrustedNetworks"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      NotAction = "s3:PutObject"
      Resource  = [local.bucket_arns["dropbox"], "${local.bucket_arns["dropbox"]}/*"]
      Condition = local.outside_trusted_networks
    },
    {
      Sid       = "DenyLetterboxPutOutsideTrustedNetworksToAllButTheWriter"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action    = "s3:PutObject"
      Resource  = "${local.bucket_arns["dropbox"]}/${local.dropbox_prefix}/*"
      Condition = merge(local.outside_trusted_networks, {
        ArnNotLike = { "aws:PrincipalArn" = [local.data_scientist_writer_pattern] }
      })
    },
    {
      Sid         = "DenyPutOutsideTheLetterboxOffTrustedNetworks"
      Effect      = "Deny"
      Principal   = { AWS = "*" }
      Action      = "s3:PutObject"
      NotResource = "${local.bucket_arns["dropbox"]}/${local.dropbox_prefix}/*"
      Condition   = local.outside_trusted_networks
    },
    {
      Sid       = "AllowInteractiveWriterPutOnly"
      Effect    = "Allow"
      Principal = { AWS = [local.sandbox_root] }
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
    # read). The statement is here so the asymmetry is readable in one place, which keeps the
    # drop-box from becoming the exchange bucket D18 refuses.
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
