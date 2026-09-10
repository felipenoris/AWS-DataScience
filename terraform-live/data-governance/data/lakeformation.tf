# Lake Formation - the permission model made real (step 5), in the order the 2026-08-18 baseline
# reading demands (docs/AWS_STATE.md, the Lake Formation row; log entry one).

# ------------------------------------------- 5.2 + 5.3 + 5.4: the settings, one resource
#
# The first apply owes three things at once, all in this resource, and the order against the
# databases below is load-bearing:
#
#   1. Name the admins (5.3, decision 5): InfrastructureAccess alone. The measured state is
#      DataLakeAdmins: [] - nobody can change these settings until this lands. The governance
#      manager is not here: an approver who can already grant everything exercises no control
#      (Lesson 9, D31). Stage 6's DataZone fulfilment principal is the named revision trigger.
#   2. Carry the parameters explicitly (5.4, INT-11): this resource replaces the whole
#      DataLakeSettings structure, so naming admins and omitting parameters resets
#      CROSS_ACCOUNT_VERSION to 1, after which every share appears to succeed and never
#      arrives, with no error anywhere. The values are written from the reading (4 / TRUE,
#      confirmed three times, last 2026-08-18), not from memory. DL-5 brackets every apply of
#      this slice.
#   3. Empty both default-permission blocks (5.2): the measured state grants ALL to
#      IAM_ALLOWED_PRINCIPALS at creation time, which makes Lake Formation a bookkeeping layer
#      over plain IAM (D13 as decoration). They act at creation, so this must land before any
#      database exists - every database below depends_on this resource.
#
#      This is the one obligation the plan cannot prove - measured 2026-08-18, in the pinned
#      provider (aws ~> 6.60), and why the apply is two steps rather than one:
#
#        - both are blocks, Computed+Optional, so omitting them plans as
#          `after_unknown: true` - Terraform states no intention about them at all;
#        - `create_database_default_permissions = []` is refused ("not expected here - did
#          you mean to define a block?"), so an explicitly empty list is not expressible;
#        - a `{}` block would declare one entry with computed fields, which is not zero.
#
#      Omission is the only form available, and whether it clears or merely leaves alone is a
#      property of the provider the plan does not state. The difference is invisible afterwards
#      and expensive: a database created while the defaults still stand is born deferring to
#      IAM, and clearing them later does not reach it (Lesson 5, with no error anywhere).
#
#      So it is measured. The apply runs in two steps - this resource alone first (`-target`),
#      then `./aws/datalake.py` DL-6 read against the account, and only then the rest, which is
#      where the first database is created. `-target` is the documented "operator knows an order
#      the graph does not" escape: the graph orders the two correctly, but a graph cannot pause
#      to be read. If DL-6 comes back still naming IAM_ALLOWED_PRINCIPALS, the remedy is step
#      5.2's other half - revoke, then re-read - before the second apply, not after.

resource "aws_lakeformation_data_lake_settings" "this" {
  admins = [local.infrastructure_access_role_arn]

  parameters = {
    CROSS_ACCOUNT_VERSION = "4"
    SET_CONTEXT           = "TRUE"
  }

}

# ------------------------------------------------------------- the registration role (5.1)
#
# LF vends data access for registered locations through a role, and with SSE-KMS buckets the
# documented path is a custom role holding S3 + KMS on exactly the registered prefixes - the
# service-linked role cannot be granted the CMK cleanly.
#
# This policy is the vending ceiling for every governed access to the two locations, from any
# account: the engine can sit in Production (Stage 9's job) while the credentials it receives are
# a session of this role. What these statements allow is the most any LF grant can deliver, and
# the grants stay the per-principal gate underneath. Widening this widens a ceiling, not anyone's
# access.
#
# The write half is here rather than in Stage 9: the first governed write attempted (2026-08-19)
# was denied, the vended AWSLF session naming kms:GenerateDataKey (Lesson 32; stage 5 log).
# Leaving it to Stage 9 would fail inside its 2.4 cross-account job with four more pieces on the
# path.
#
# s3:DeleteObject is the one action below reasoned rather than measured: the engine's own
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

    # The write half - a second inline policy rather than new statements in the first, so its
    # revert is one deletion and each policy's name stays true to what it holds. Object-level
    # actions carry object ARNs only.
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
# raw and curated only - the drop-box, artifacts and logs stay unregistered by design
# (docs/GOVERNANCE.md "Persistence": D13's non-registered class, plain IAM). Deregistering is
# denied by the Data OU SCP (DenyLakeDeletionAndDeregistration); the quiet failure it closes is a
# prefix returning to plain IAM with every object still in place.

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
# The model lives in docs/GOVERNANCE.md (decisions 1-3, 2026-08-18); these resources are its
# rendering, value for value. businessunit is reserved there and absent here: an LF-Tag requires
# at least one value, and the dimension has none until the second business unit exists (D35).
#
# A security-zone tag (value zn-lab) existed here from 2026-08-18 to 2026-08-19. No TBAC
# expression ever used it, and no AWS mechanism connects an LF-Tag to a CMK - the tag-to-key link
# was only a naming convention. Encryption is per account (docs/GOVERNANCE.md "Encryption";
# kms.tf).
#
# Creating an LF-Tag requires an admin, so every tag depends on the settings resource.

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
