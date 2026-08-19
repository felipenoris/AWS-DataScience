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
# service-linked role cannot be granted the CMK cleanly. READ-side only today: the governed
# WRITE arrives at Stage 9, which amends this policy in the same slice (its step 2).
#
# permissions_boundary = null is the module's one legitimate case: a service role authored
# by the infrastructure user (the module's own variable note).

module "lf_registration_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-lf-registration"
  description = "Lake Formation registered-location access - vends governed reads of raw and curated (D13)"

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
          Sid      = "KmsDecryptZnLab"
          Effect   = "Allow"
          Action   = "kms:Decrypt"
          Resource = module.zn_lab_key.key_arn
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

resource "aws_lakeformation_lf_tag" "security_zone" {
  key    = "security-zone"
  values = ["zn-lab"]

  depends_on = [aws_lakeformation_data_lake_settings.this]
}
