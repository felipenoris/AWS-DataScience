# Lake Formation, consumer side (Stage 5 pass 4). Three things in dependency order; the first is
# a prerequisite pass 3 discovered rather than planned.

# --------------------------------------------------- the settings: the account joins LF at all
#
# Measured on both consumers 2026-08-19: DataLakeAdmins [], and both accounts' RAM already
# holding their two shares ACTIVE while glue:GetDatabases returned nothing. AWS requires at
# least one data lake administrator in the receiving account before a shared resource is visible
# there at all, so an empty consumer catalog has two causes that look identical (the share never
# arrived, or the account is not yet a Lake Formation account) and only the RAM side separates
# them. DL-7 reports the two branches apart since pass 3.
#
# This resource carries the same two hazards the producer side met, neither expressible in the
# plan, so the apply is two steps here as well (Recipe D, Lesson 27):
#
#   1. Parameters are replaced wholesale (INT-11). This resource writes the entire
#      DataLakeSettings structure: naming admins and omitting `parameters` resets
#      CROSS_ACCOUNT_VERSION to 1. Both consumer accounts were read on 2026-08-19 and both
#      already carry 4/TRUE - set by nobody in this repository, and defended by nobody until
#      now. The values below come from that reading, not from memory. INT-11 was written about
#      the producer, and the hazard turns out to be symmetric.
#
#   2. The create-defaults act at creation time (step 5.2's finding, generalised). Both
#      accounts read IAM_ALLOWED_PRINCIPALS/ALL on both blocks today. Omission is the only
#      expressible form - `= []` is refused because they are blocks, and a `{}` block declares
#      one entry rather than zero - so whether omission clears them or leaves them standing is
#      a property of the provider that the plan does not state.
#
#      The first local catalog object here is the resource link below. A link created while the
#      defaults still stand is born deferring to plain IAM, and clearing them afterwards does
#      not reach it. So: this resource alone under -target, then ./aws/datalake.py DL-6 read
#      against the account, and only then the rest. If DL-6 still names IAM_ALLOWED_PRINCIPALS,
#      stop and revoke before applying the remainder.
#
#      Pass 1 measured that omission clears, in this provider version. That reading did not
#      retire the split (Lesson 27) and does not retire it here either.

#   3. A third hazard, found 2026-08-26: the two above are about what this resource omits, this
#      one about what it displaces. `admins` is a list, replaced wholesale like `parameters`, and
#      SageMaker Unified Studio adds itself to it. The first project created in Sandbox
#      (2026-08-22) left awsds-sandbox-smus-manage-access and awsds-sandbox-smus-provisioning
#      standing as data lake administrators, and set allow_full_table_external_data_access to
#      true beside them. Nobody in this repository asked for either (Lesson 17), and no gate here
#      could see it: DL-5 reads `parameters` and not `admins`, so the drift surfaced only because
#      Stage 16 ran a plan for an unrelated reason (Lesson 31). Development, which has no project
#      yet, still re-plans `No changes`, which is what attributes the cause.
#
#      The answer is the lifecycle block below. Adopting the two seats as inputs stopped the
#      deletion and was still wrong: it froze the list as it stood, so a seat the service adds
#      tomorrow is deleted by the next apply of this slice - the same failure one seat further
#      out. Adoption answered "which values" when the question was "whose attribute", so the
#      inputs are gone and the ownership is declared instead.
#
#      What the lifecycle block costs: Terraform stops defending the list. An administrator
#      nobody granted no longer appears as a plan diff - which is where it never appeared anyway,
#      DL-5 reading `parameters` and not `admins` - and the loss of var.data_lake_admin_role_arn
#      itself would go unnoticed here, a seat that is load-bearing (measured 2026-08-19: an
#      account with no administrator sees an empty catalog while holding its shares). So the
#      plan's defence is replaced, not dropped: ./aws/datalake.py DL-13 reads the list, fails on
#      the required seat's absence and reports every other one. A check is the better instrument
#      regardless - a plan diff only appears when somebody happens to plan this slice.
#
#      What none of this settles: whether a SMUS provisioning role should be a Lake Formation
#      administrator - an administrator can grant itself anything in the local catalog, the
#      resource links to the governed lake included. That is open question 24, filed against
#      Stage 6, whose act created them.

resource "aws_lakeformation_data_lake_settings" "this" {
  # The create-time list, and only that. One administrator is what a consumer account needs to
  # become a Lake Formation account at all; whatever the services in it add afterwards is
  # theirs, per the lifecycle block below.
  admins = [var.data_lake_admin_role_arn]

  parameters = {
    CROSS_ACCOUNT_VERSION = "4"
    SET_CONTEXT           = "TRUE"
  }

  # The same shape data-governance/data/catalog.tf uses for Iceberg's column mirror: Terraform
  # keeps this resource's existence, its `parameters` and its cleared create-defaults; the admin
  # list goes through the service. Hazard 3 above is the argument.
  #
  # Ignoring is safe on a resource that writes the whole structure because an ignored attribute
  # is planned from prior state, which refresh has just filled from AWS - so an update triggered
  # by some other attribute writes the list back as it found it, rather than as this file
  # imagines it. The one way to defeat that is `apply -refresh=false`, which would send a stale
  # list; do not use it on this slice.
  #
  # Measured 2026-08-26: with Sandbox holding three administrators live and this config declaring
  # one, the plan reads `No changes`.
  lifecycle {
    ignore_changes = [admins, allow_full_table_external_data_access]
  }
}

# ------------------------------------------------------------------ the resource links (step 8)
#
# A resource link is a local catalog database that points at a shared one. It is what makes the
# lake's `raw` and `curated` addressable from an Athena query in this account; without it the
# share is held and unusable.
#
# The local name is the target name, so a query written in Sandbox and one written in Development
# read identically, and identically to one written against the lake itself. A prefixed local name
# would give the same table three spellings.
#
# The drop-box is not here (Lesson 29): the default share is gated on `layer IN (raw, curated)`,
# so the letterbox never travelled. var.lake_databases comes from the lake slice's own output, so
# a drop-box key appearing in this map means the gate has been changed on the producer side - a
# finding, not a convenience.

resource "aws_glue_catalog_database" "link" {
  for_each = { for k, name in var.lake_databases : k => name if k != "dropbox" }

  name = each.value

  target_database {
    catalog_id    = var.lake_catalog_id
    database_name = each.value
  }

  # The order is load-bearing: no link can resolve before this account has an administrator, and
  # a link created before the create-defaults are cleared is born wrong in a way nothing later
  # repairs.
  depends_on = [aws_lakeformation_data_lake_settings.this]
}

# ---------------------------------------------------------------------- the re-grants (step 8)
#
# A cross-account grant lands on the account, never on a principal inside it (pass 3's
# correction to the design). Nothing here can read a row until this account's own data lake
# administrator passes the permission on to a local principal - which is why every cross-account
# grant on the producer side carries the grant option, and why an administrator can only pass on
# what it received with it (docs/GOVERNANCE.md, Grants).
#
# Two grants per shared object, Lake Formation's documented pair, and they are not
# interchangeable. The half people miss is the first:
#
#   the link    a local database object. DESCRIBE on it is what makes the link visible in the
#               catalog to the persona. Without it the persona sees no database at all, even
#               holding every permission on the target.
#   the target  the shared object, addressed through the owner's catalog id. This is where
#               SELECT lives, and it is written as the same LF-Tag expression the account
#               received - the only thing it may pass on.

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
    # The catalog id is the producer's. These tags are not this account's objects: they were
    # created in Data Governance and travelled with the share, and a grant written over them
    # has to say whose they are.
    catalog_id    = var.lake_catalog_id
    resource_type = "DATABASE"

    # The value list is literal, exactly as on the producer side and for the same reason
    # (shares.tf's note): this is a subset, and a `layer` value added to the ontology tomorrow
    # must not join a persona's reach by inheritance. The literal is the control.
    #
    # No classification gate on the database grant: `curated`'s database carries no
    # classification at all (fail-closed by absence, decision 1), so an expression naming
    # classification would not match it - and a database that does not match cannot be read
    # through its link.
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
  # curated (D18, D19). The governed write is Stage 9's, in Production, to a different principal.
  permissions = ["SELECT", "DESCRIBE"]

  lf_tag_policy {
    catalog_id    = var.lake_catalog_id
    resource_type = "TABLE"

    # Two expression blocks in one grant is an AND. Two separate grants would be an OR and would
    # hand back the drop-box the `layer` gate exists to exclude.
    expression {
      key    = "layer"
      values = ["raw", "curated"]
    }

    # restricted and personal are absent by enumeration - the classification rule made
    # executable. curated.sample_trades carries `internal` at the table and `restricted` on its
    # `counterparty` column, so this grant is also the stage's column-level proof: the column is
    # expected to be absent from this persona's column list (verification x, read as a column
    # list rather than as rows - the table was applied empty).
    expression {
      key    = "classification"
      values = ["public", "internal"]
    }
  }

  depends_on = [aws_lakeformation_data_lake_settings.this]
}
