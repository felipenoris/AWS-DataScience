# Lake Formation - the permission model made real (step 5), in the ORDER the 2026-08-18
# baseline reading demands (docs/AWS_STATE.md, the Lake Formation row; log entry one).

# --------------------------------------------- 5.2 + 5.3 + 5.4: the trio, ONE resource
#
# THE FIRST APPLY OWES THREE THINGS AT ONCE, all in this resource, and the order against the
# databases below is load-bearing:
#
#   1. NAME THE ADMINS (5.3, decision 5): InfrastructureAccess alone. The measured state is
#      DataLakeAdmins: [] - nobody can change these settings until this lands. The
#      governance manager is deliberately NOT here (an approver who can already grant
#      everything exercises no control - Lesson 9, D31); Stage 6's DataZone fulfilment
#      principal is the named revision trigger.
#   2. CARRY THE PARAMETERS EXPLICITLY (5.4, INT-11): this resource REPLACES the whole
#      DataLakeSettings structure - naming admins and omitting parameters RESETS
#      CROSS_ACCOUNT_VERSION to 1, after which every share appears to succeed and never
#      arrives, with no error anywhere. The values are written FROM THE READING
#      (4 / TRUE, confirmed three times, last 2026-08-18), not from memory. DL-5 brackets
#      every apply of this slice.
#   3. EMPTY BOTH DEFAULT-PERMISSION BLOCKS (5.2): the measured state grants ALL to
#      IAM_ALLOWED_PRINCIPALS at creation time, which makes Lake Formation a bookkeeping
#      layer over plain IAM (D13 as decoration). They act AT CREATION, so this must land
#      BEFORE any database exists - every database below depends_on this resource.
#
#      AND THIS IS THE ONE OBLIGATION THE PLAN CANNOT PROVE - measured 2026-08-18, in the
#      pinned provider (aws ~> 6.60), and it is why the apply is two steps rather than one:
#
#        - both are BLOCKS, Computed+Optional, so omitting them plans as
#          `after_unknown: true` - Terraform states no intention about them at all;
#        - `create_database_default_permissions = []` is REFUSED ("not expected here - did
#          you mean to define a block?"), so an explicitly empty list is not expressible;
#        - a `{}` block would declare ONE entry with computed fields, which is not zero.
#
#      Omission is therefore the only form available, and whether it CLEARS or merely
#      LEAVES ALONE is a property of the provider that the plan does not state. The
#      difference is invisible afterwards and expensive: a database created while the
#      defaults still stand is born deferring to IAM, and clearing them later does not
#      reach it (Lesson 5, with no error anywhere).
#
#      SO IT IS MEASURED INSTEAD OF ASSUMED. The apply runs in two steps - this resource
#      alone first (`-target`), then `./aws/datalake.py` DL-6 read against the account,
#      and only then the rest, which is where the first database is created. `-target` is
#      the documented "operator knows an order the graph does not" escape and this is that
#      case: the graph orders the two correctly, but a graph cannot pause to be read.
#      If DL-6 comes back still naming IAM_ALLOWED_PRINCIPALS, the remedy is step 5.2's
#      other half - revoke, then re-read - BEFORE the second apply, not after.

resource "aws_lakeformation_data_lake_settings" "this" {
  admins = [local.infrastructure_access_role_arn]

  parameters = {
    CROSS_ACCOUNT_VERSION = "4"
    SET_CONTEXT           = "TRUE"
  }

}

# ------------------------------------------------------------- the registration role (5.1)
#
# LF vends data access for registered locations THROUGH a role, and with SSE-KMS buckets the
# documented path is a custom role holding S3 + KMS on exactly the registered prefixes - the
# service-linked role cannot be granted the CMK cleanly.
#
# THIS POLICY IS THE VENDING CEILING FOR EVERY GOVERNED ACCESS TO THE TWO LOCATIONS, FROM ANY
# ACCOUNT: the engine can sit in Production (Stage 9's job) while the credentials it receives
# are a session of THIS role - so what these statements allow is the most any LF grant can
# ever deliver, and the grants stay the per-principal gate underneath. Widening this widens a
# ceiling, not anyone's access.
#
# THE WRITE HALF LANDED 2026-08-20, AND ITS HISTORY IS THE POINT (stage 5 log, that entry).
# This block shipped read-only at pass 1, its comment deferring the write to "Stage 9, which
# amends this policy (its step 2)" - but Stage 9's own file never carried that amendment, and
# Stage 5's file meanwhile scheduled a decision on the belief that in-account Athena could
# already load rows. The first governed write ever attempted (2026-08-19) measured all three
# files at once: DENIED, the vended AWSLF session naming kms:GenerateDataKey. The mechanism
# side was the true one (Lesson 32), and the write half lands here, early, instead of failing
# inside Stage 9's 2.4 cross-account job with four more pieces on the path.
#
# s3:DeleteObject is the one action below REASONED rather than measured: the engine's own
# failure-path cleanup and Iceberg maintenance (VACUUM, rewrites) delete data files, and a
# put-only ceiling strands every failed commit where no engine can remove it.
#
# permissions_boundary = null is the module's one legitimate case: a service role authored
# by the infrastructure user (the module's own variable note).

module "lf_registration_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-lf-registration"
  description = "Lake Formation registered-location access - vends governed reads and writes of raw and curated (D13)"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "LakeFormationService"
        Effect    = "Allow"
        Principal = { Service = "lakeformation.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })

  inline_policies = {
    registered-locations-read = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "S3ReadRegisteredLocations"
          Effect = "Allow"
          Action = ["s3:GetObject", "s3:ListBucket"]
          Resource = [
            local.bucket_arns["raw"],
            "${local.bucket_arns["raw"]}/*",
            local.bucket_arns["curated"],
            "${local.bucket_arns["curated"]}/*",
          ]
        },
        {
          Sid      = "KmsDecryptDataKey"
          Effect   = "Allow"
          Action   = "kms:Decrypt"
          Resource = module.data_key.key_arn
        },
      ]
    })

    # The write half - a SECOND inline policy rather than new statements in the first, so the
    # diff that created it is pure addition, its revert is one deletion, and each policy's
    # name stays true to what it holds. Object-level actions carry object ARNs only.
    registered-locations-write = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "S3WriteRegisteredLocations"
          Effect = "Allow"
          Action = ["s3:PutObject", "s3:DeleteObject"]
          Resource = [
            "${local.bucket_arns["raw"]}/*",
            "${local.bucket_arns["curated"]}/*",
          ]
        },
        {
          Sid      = "KmsGenerateDataKey"
          Effect   = "Allow"
          Action   = "kms:GenerateDataKey"
          Resource = module.data_key.key_arn
        },
      ]
    })
  }
}

# ------------------------------------------------------------------ the registrations (5.1)
#
# raw and curated only - the drop-box, artifacts and logs stay UNREGISTERED by design
# (docs/GOVERNANCE.md "Persistence": D13's non-registered class, plain IAM). Deregistering
# is denied by the Data OU SCP (DenyLakeDeletionAndDeregistration) - the quiet failure it
# closes is a prefix returning to plain IAM with every object still in place.

resource "aws_lakeformation_resource" "raw" {
  arn      = local.bucket_arns["raw"]
  role_arn = module.lf_registration_role.role_arn

  # The registration must not race the settings trio - admins first, then structure.
  depends_on = [aws_lakeformation_data_lake_settings.this, module.bucket]
}

resource "aws_lakeformation_resource" "curated" {
  arn      = local.bucket_arns["curated"]
  role_arn = module.lf_registration_role.role_arn

  depends_on = [aws_lakeformation_data_lake_settings.this, module.bucket]
}

# ------------------------------------------------------------- the LF-Tag ontology (step 2)
#
# THE ONE COPY OF THE MODEL IS docs/GOVERNANCE.md (decisions 1-3, 2026-08-18) - these
# resources are its rendering, value for value. businessunit is RESERVED there and absent
# here on purpose: an LF-Tag requires at least one value, and the dimension has none until
# the second business unit exists (D35).
#
# A THIRD TAG EXISTED HERE FOR ONE DAY: security-zone (value zn-lab), created 2026-08-18 and
# withdrawn 2026-08-19 (the user's revision). No TBAC expression ever used it, and no AWS
# mechanism connects an LF-Tag to a CMK - the tag-to-key link was only a naming convention.
# Encryption is per ACCOUNT now (docs/GOVERNANCE.md "Encryption"; kms.tf).
#
# Creating an LF-Tag requires an admin, so every tag depends on the settings trio.

resource "aws_lakeformation_lf_tag" "classification" {
  key    = "classification"
  values = ["public", "internal", "restricted", "personal"]

  depends_on = [aws_lakeformation_data_lake_settings.this]
}

resource "aws_lakeformation_lf_tag" "layer" {
  key    = "layer"
  values = ["dropbox", "raw", "curated"]

  depends_on = [aws_lakeformation_data_lake_settings.this]
}
