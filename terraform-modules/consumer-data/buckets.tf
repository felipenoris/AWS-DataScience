# The derived zone (D19, D31; Stage 5 step 9) - ONE designed destination per consumer account,
# with three prefix families that are three different contracts.
#
# WHY ONE BUCKET AND NOT TWO. The plan's topology files say "scratch + derived-zone buckets"
# while every line on the IAM side - D13's own wording, identity/sso/'s owed-grants note,
# 1b step 3.4 - says "scratch and derived PREFIXES". D13 is the origin and it is the prefix
# reading: "non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM
# access" - `scratch` there is a CLASS (everything Lake Formation does not govern), not a
# named resource. A second bucket would need either a third CMK the cost model does not carry
# or a key shared for no reason; the prefixes below carry the whole distinction and cost
# nothing (settled 2026-08-19, with the user).
#
#   results/                  the Athena workgroup's ENFORCED output location. Per-persona,
#                             not per-person - an enforced workgroup has exactly one result
#                             location and that is the ceiling on the whole design (Stage 5
#                             step 8; docs/GOVERNANCE.md, The grain). Written down as fact,
#                             not carried as debt: the system's real grain is
#                             min(SQL grain, derived-zone grain).
#   derived/${aws:userid}/    materialised copies, PER PRINCIPAL ON WRITE (D19 practice ii) -
#                             the s3:PutObject statement in identity/sso/ carries the policy
#                             variable. THE READ IS PERSONA-WIDE (pass 4c, decision 6's grain):
#                             ReadDerivedZoneObjects grants s3:GetObject across derived/*. So
#                             the prefix governs where a copy LANDS, not who may read it; what
#                             keeps other personas out is the zone CMK's key policy (D31). It
#                             governs the COPY rather than the source - Lesson 1's shape,
#                             managed rather than forbidden.
#   scratch/                  the notebook's working files - a downloaded CSV, an intermediate
#                             feature, a model checkpoint. Non-registered by definition, so
#                             plain IAM, which is exactly what D13 says about this class.
#
# THE PREFIXES ARE NOT CREATED HERE, and that is not an omission: S3 has no directories, so a
# prefix exists when an object is written under it. What makes them real is the IAM statement
# in identity/sso/ that scopes s3:PutObject to them and to nothing else (D19 practice i) -
# which is why the names above are a CONTRACT between two slices in two different accounts,
# and why they are written out in one place a human reads rather than only in a policy.
#
# STAGE 11 SCOPE, DECLARED HERE BECAUSE STAGE 11 CANNOT DISCOVER IT: this bucket is in Macie's
# scan scope and carries CloudTrail data events (D19 practice iv). It is where sensitive data
# actually accumulates, and it sits OUTSIDE the account Macie primarily watches.

# The ARN is BUILT FROM THE NAME rather than read from the module output, because the policy
# statement below is an INPUT to the same module call - the lake slice's idiom (locals.tf
# there), for the same reason: Terraform would otherwise have to resolve a resource against
# itself. S3 bucket ARNs carry no account and no region, so the string is exact.
locals {
  derived_bucket_name = "awsds-${var.env}-derived"
  derived_bucket_arn  = "arn:${data.aws_partition.current.partition}:s3:::${local.derived_bucket_name}"
}

module "derived" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.3.0"

  bucket_name = local.derived_bucket_name
  kms_key_arn = module.zone_key.key_arn

  # v0.3.0's reason for existing: DL-9 fails a *-derived bucket with no Expiration rule, and
  # before this the module could only expire NONCURRENT versions - which reaches nothing that
  # was never overwritten. D19 practice (iii) is about the current object.
  expiration_days = var.derived_expiration_days

  additional_policy_statements = [
    {
      # The preventive counterpart of Stage 11's presigned-URL detection, and the one branch of
      # the lake's perimeter that is worth copying onto a bucket holding COPIES: a presigned
      # link is a bearer credential, and 15 minutes bounds how long a leaked one works.
      # Milliseconds, per the condition key.
      Sid       = "DenyStalePresignedUrls"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action    = "s3:*"
      Resource  = [local.derived_bucket_arn, "${local.derived_bucket_arn}/*"]
      Condition = { NumericGreaterThan = { "s3:signatureAge" = "900000" } }
    },
  ]
}
