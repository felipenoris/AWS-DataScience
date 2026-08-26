# Lake Formation, consumer side (Stage 5 pass 4). Three things in dependency order, and the
# first one is a PREREQUISITE that pass 3 discovered rather than planned.

# --------------------------------------------------- the settings: the account joins LF at all
#
# MEASURED ON BOTH CONSUMERS 2026-08-19, BEFORE THIS WAS WRITTEN: DataLakeAdmins [], and both
# accounts' RAM already holding their two shares ACTIVE while glue:GetDatabases returned
# nothing. AWS requires at least one data lake administrator in the RECEIVING account before a
# shared resource is visible there at all - so an empty consumer catalog has two causes that
# look identical (the share never arrived, or the account is not yet a Lake Formation account)
# and only the RAM side separates them. DL-7 reports the two branches apart since pass 3.
#
# THIS RESOURCE CARRIES THE SAME TWO HAZARDS THE PRODUCER SIDE MET, and neither is expressible
# in the plan - which is why the apply is TWO STEPS here as well (Recipe D, Lesson 27):
#
#   1. PARAMETERS ARE REPLACED WHOLESALE (INT-11). This resource writes the entire
#      DataLakeSettings structure: naming admins and omitting `parameters` RESETS
#      CROSS_ACCOUNT_VERSION to 1. Both consumer accounts were READ on 2026-08-19 and both
#      already carry 4/TRUE - set by nobody in this repository, and defended by nobody until
#      now. The values below come FROM THAT READING, not from memory. This was a genuine
#      surprise: INT-11 was written about the producer, and the hazard turns out to be
#      symmetric.
#
#   2. THE CREATE-DEFAULTS ACT AT CREATION TIME (step 5.2's finding, generalised). Both
#      accounts read IAM_ALLOWED_PRINCIPALS/ALL on both blocks today. Omission is the ONLY
#      expressible form - `= []` is refused because they are blocks, and a `{}` block declares
#      one entry rather than zero - so whether omission CLEARS them or LEAVES THEM STANDING is
#      a property of the provider that the plan does not state.
#
#      THE FIRST LOCAL CATALOG OBJECT HERE IS THE RESOURCE LINK BELOW. A link created while the
#      defaults still stand is born deferring to plain IAM, and clearing them afterwards does
#      not reach it. So: this resource alone under -target, then ./aws/datalake.py DL-6 read
#      against the account, and only then the rest. If DL-6 still names IAM_ALLOWED_PRINCIPALS,
#      STOP and revoke before applying the remainder.
#
#      Pass 1 measured that omission clears, in this provider version. That reading did not
#      retire the split (Lesson 27) and does not retire it here either.

#   3. A THIRD HAZARD, FOUND 2026-08-26 AND OF A DIFFERENT KIND - the two above are about what
#      this resource OMITS, this one is about what it DISPLACES. `admins` is a list, replaced
#      wholesale like `parameters`, and SageMaker Unified Studio ADDS ITSELF to it: the first
#      project created in Sandbox (2026-08-22) left awsds-sandbox-smus-manage-access and
#      awsds-sandbox-smus-provisioning standing as data lake administrators, and set
#      allow_full_table_external_data_access to true beside them. Nobody in this repository
#      asked for either (Lesson 17 - a service that sets itself up creates principals nobody
#      chose), and NO GATE HERE COULD SEE IT: DL-5 reads `parameters` and not `admins`, so the
#      drift surfaced only because Stage 16 ran a plan for an unrelated reason (Lesson 31's
#      neighbour). Development, which has no project yet, still re-plans `No changes` - which is
#      what attributes the cause.
#
#      THE ANSWER IS ADOPTION, NOT REMOVAL, taken by the user 2026-08-26. Applying the narrow
#      list would strip live administrators from the service whose create path Stage 6 measured
#      AFTER they existed; and removing them from the code does not remove them from AWS, it
#      only makes every future plan fight the service. So both are inputs below, and the
#      account that has a project declares them.
#
#      WHAT ADOPTION DOES NOT SETTLE, said here rather than implied: whether a SMUS provisioning
#      role SHOULD be a Lake Formation administrator is a governance question - an administrator
#      can grant itself anything in the local catalog, the resource links to the governed lake
#      included. That is a Stage 6 residue and an open question, not something this module
#      decides by carrying a variable.

resource "aws_lakeformation_data_lake_settings" "this" {
  admins = concat([var.data_lake_admin_role_arn], var.additional_data_lake_admin_role_arns)

  # NULL LEAVES IT UNDECLARED, which is this resource's own default and what every consumer
  # without a SMUS project wants. It is an input rather than a constant because the value is
  # not ours: it is read back from the account that has one.
  allow_full_table_external_data_access = var.allow_full_table_external_data_access

  parameters = {
    CROSS_ACCOUNT_VERSION = "4"
    SET_CONTEXT           = "TRUE"
  }
}

# ------------------------------------------------------------------ the resource links (step 8)
#
# A resource link is a LOCAL catalog database that points at a shared one. It is what makes the
# lake's `raw` and `curated` addressable from an Athena query in this account; without it the
# share is held and unusable.
#
# THE LOCAL NAME IS THE TARGET NAME, deliberately: a query written in Sandbox and a query
# written in Development then read identically, and identically to one written against the lake
# itself. A prefixed local name would make the same table have three spellings.
#
# THE DROP-BOX IS NOT HERE, and its absence is the design working (Lesson 29): the default share
# is gated on `layer IN (raw, curated)`, so the letterbox never travelled. var.lake_databases
# comes from the lake slice's own output, so a drop-box key appearing in this map means the gate
# has been changed on the producer side - a finding, not a convenience.

resource "aws_glue_catalog_database" "link" {
  for_each = { for k, name in var.lake_databases : k => name if k != "dropbox" }

  name = each.value

  target_database {
    catalog_id    = var.lake_catalog_id
    database_name = each.value
  }

  # THE ORDER IS LOAD-BEARING, not cosmetic: no link can resolve before this account has an
  # administrator, and a link created before the create-defaults are cleared is born wrong in a
  # way nothing later repairs.
  depends_on = [aws_lakeformation_data_lake_settings.this]
}

# ---------------------------------------------------------------------- the re-grants (step 8)
#
# WHY A RE-GRANT EXISTS AT ALL, and it is the sentence pass 3 corrected the design with: a
# cross-account grant lands on the ACCOUNT, never on a principal inside it. Nothing here can
# read a row until this account's own data lake administrator passes the permission on to a
# local principal - which is why every cross-account grant on the producer side carries the
# grant option, and why an administrator can only pass on what it received with it
# (docs/GOVERNANCE.md, Grants).
#
# TWO GRANTS PER SHARED OBJECT, AND THEY ARE NOT INTERCHANGEABLE - this is Lake Formation's
# documented pair and the half people miss is the first:
#
#   the LINK    a local database object. DESCRIBE on it is what makes the link VISIBLE in the
#               catalog to the persona. Without it the persona sees no database at all, even
#               holding every permission on the target.
#   the TARGET  the shared object, addressed through the OWNER's catalog id. This is where
#               SELECT lives, and it is written as the same LF-Tag expression the account
#               received - because that is the only thing it may pass on.

resource "aws_lakeformation_permissions" "link_describe" {
  for_each = aws_glue_catalog_database.link

  principal   = var.data_scientist_role_arn
  permissions = ["DESCRIBE"]

  database {
    name = each.value.name
  }

  depends_on = [aws_lakeformation_data_lake_settings.this]
}

resource "aws_lakeformation_permissions" "shared_databases" {
  principal   = var.data_scientist_role_arn
  permissions = ["DESCRIBE"]

  lf_tag_policy {
    # THE CATALOG ID IS THE PRODUCER'S. These tags are not this account's objects: they were
    # created in Data Governance and travelled with the share, and a grant written over them
    # has to say whose they are.
    catalog_id    = var.lake_catalog_id
    resource_type = "DATABASE"

    # THE VALUE LIST IS LITERAL, exactly as it is on the producer side and for the same reason
    # (shares.tf's note): this is a SUBSET, and a `layer` value added to the ontology tomorrow
    # must not join a persona's reach by inheritance. The literal is the control.
    #
    # NO classification GATE ON THE DATABASE GRANT, deliberately: `curated`'s database carries
    # no classification at all (fail-closed by absence, decision 1), so an expression naming
    # classification would not match it - and a database that does not match cannot be read
    # through its link, which is the whole of this pass.
    expression {
      key    = "layer"
      values = ["raw", "curated"]
    }
  }

  depends_on = [aws_lakeformation_data_lake_settings.this]
}

resource "aws_lakeformation_permissions" "shared_tables" {
  principal = var.data_scientist_role_arn

  # SELECT is the read; DESCRIBE is what makes the table enumerable. No INSERT, DELETE, ALTER or
  # DROP: this persona writes through the drop-box and its own derived zone, never into raw or
  # curated (D18, D19). The governed WRITE is Stage 9's, in Production, to a different principal.
  permissions = ["SELECT", "DESCRIBE"]

  lf_tag_policy {
    catalog_id    = var.lake_catalog_id
    resource_type = "TABLE"

    # TWO expression blocks in ONE grant is an AND. Two separate grants would be an OR and would
    # hand back the drop-box the `layer` gate exists to exclude.
    expression {
      key    = "layer"
      values = ["raw", "curated"]
    }

    # restricted and personal are absent BY ENUMERATION - the classification rule made
    # executable. curated.sample_trades carries `internal` at the table and `restricted` on its
    # `counterparty` column, so this grant is also the stage's column-level proof: the column is
    # EXPECTED to be absent from this persona's column list (verification x, read as a column
    # list rather than as rows - the table was applied empty).
    expression {
      key    = "classification"
      values = ["public", "internal"]
    }
  }

  depends_on = [aws_lakeformation_data_lake_settings.this]
}
