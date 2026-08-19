# Step 7, pass 3 - the cross-account shares (D22, INT-03, INT-11).
#
# WHAT A SHARE IS HERE: one LF-TBAC grant per consumer ACCOUNT, written over the step 2
# ontology rather than over table names. Lake Formation renders it as an AWS RAM resource
# share; because the consumers sit in this organization, it should arrive without an
# invitation to accept - INT-11's whole point. A PENDING invitation is not a nuisance, it is
# the finding: the org-sharing path is not doing the work, the share arrived through the
# fallback tax, and it will reappear at every rebuild. DL-7 fails on exactly that.
#
# THE CONSUMERS ARE THE TWO INTERACTIVE ACCOUNTS AND NOT PRODUCTION: Production's share
# carries the governed WRITE and arrives with Stage 9, which has a job role to receive it.
# Sharing into an account with no consumer in it is a grant nobody asked for.
#
# ---------------------------------------------------------------------------------------
# THE GRANT OPTION IS NOT OPTIONAL, AND THIS IS THE FILE'S ONE LOAD-BEARING SENTENCE
#
# A cross-account grant lands on the ACCOUNT, never on a principal inside it. Nothing in the
# consumer account can use it until that account's own data lake administrator grants it
# onward to a local principal - and an administrator can only pass on what it received WITH
# THE GRANT OPTION. AWS states it as an imperative: "Because the data lake administrator must
# grant permissions on shared resources to the principals in the grantee account, you must
# always grant cross-account permissions with the grant option" (Data sharing using tag-based
# access control), and the regranting page shows the same requirement from the receiving side.
#
# WITHOUT IT NOTHING ERRORS: the apply succeeds, the RAM share appears, the resource shows up
# in the consumer catalog, and every attempt to grant it to a person fails - one pass later,
# in another account, on somebody else's screen.
#
# AND IT IS NOT A DELEGATION OF THE SHARE. A resource shared WITH an account can be granted
# only to principals IN that account - never onward to another account, to an organization
# (not even its own), nor to IAMAllowedPrincipals. That bound is AWS's, not ours to enforce:
# the grant option buys the consumer's administrator the single step the design already
# requires of it, and no reach beyond the account line.
#
# ---------------------------------------------------------------------------------------
# WHY THE EXPRESSIONS CARRY `layer` AND NOT ONLY `classification`
#
# docs/GOVERNANCE.md's default grant reads `classification IN (public, internal)`, described
# as "both layers". Applied literally against the catalog AS TAGGED, that expression also
# matches the DROP-BOX database, which carries classification=internal for decision 1's
# fail-open reason (a user-supplied arrival is internal, not invisible).
#
# The drop-box is a letterbox. Its entire contract is that a writer may PutObject and never
# read back (GOVERNANCE.md "Drop-box"), so a consumer-side SELECT over its tables is the one
# direction the asymmetry exists to forbid. The rows would not in fact arrive - the drop-box
# bucket is deliberately NOT registered with Lake Formation, so a query falls back to plain
# IAM and no consumer persona holds s3:Get on it - but a second control catching the miss of
# a first is not a reason to leave the first one wrong, and the METADATA (table names, schema,
# S3 paths) would arrive regardless.
#
# So the gate is written where the intention already was: "both layers" means raw and curated.
#
# THE TWO GRANTS ARE DELIBERATELY NOT THE SAME EXPRESSION:
#
#   DATABASE   layer IN (raw, curated)                                     -> DESCRIBE
#   TABLE      layer IN (raw, curated) AND classification IN (public, internal)
#                                                                          -> SELECT, DESCRIBE
#
# The database grant may NOT carry the classification gate: curated's database deliberately
# carries no classification at all (fail-closed by absence, decision 1), so any expression
# naming classification fails to match it - and a database that does not match cannot be
# resource-linked, which is the whole of step 8's consumer side. The classification gate
# belongs where the ROWS are, and that is the table grant.
#
# What that costs, stated rather than discovered: a consumer may DESCRIBE the curated
# database. Enumerating the tables inside it is a separate permission - the governance manager
# needed an explicit ALL_TABLES DESCRIBE in pass 2 for precisely this reason (Lesson 28) - so
# an untagged curated table is EXPECTED to stay invisible. Expected, not proven: the
# instrument is a consumer-side glue:GetTables, and it is pass 4's to run.
#
# ---------------------------------------------------------------------------------------
# THE 7.1 PREREQUISITE THAT TURNED OUT TO BE CONDITIONAL - MEASURED, NOT ASSUMED
#
# Two AWS pages disagree in emphasis. The LF-TBAC considerations page says flatly that using
# LF-TBAC to grant cross-account access "requires additions to the Data Catalog resource
# policy" - which is what this stage's step 7.1 recorded on 2026-08-17. The Prerequisites page
# is more specific: the glue:ShareResource addition is needed if the account is ALREADY
# sharing through an AWS Glue Data Catalog resource policy (the version 1/2 path), and "is not
# required if your account has made no cross-account grants using the AWS Glue Data Catalog
# resource policy".
#
# MEASURED 2026-08-19 in this account: glue:GetResourcePolicy returns EntityNotFoundException,
# "Policy not found". No resource policy exists, this account has never shared that way, and
# the cross-account version is 4. So no aws_glue_resource_policy is written here and nothing
# is set to EnableHybrid: a policy added "to be safe" would be a real permission surface and a
# hybrid-mode interaction adopted for a condition that does not hold.
#
# THE READING IS FALSIFIABLE AND THE FALSIFIER IS CHEAP. If the flat statement is the true
# one, this grant applies without error and NO RAM share appears. Step 7.3's readings are that
# test - `ram get-resource-shares --resource-owner SELF` on this side, the catalog on the
# other - and a missing share is the answer, not a mystery.

# ------------------------------------------------------------------- the database share (7.2)

resource "aws_lakeformation_permissions" "share_databases" {
  for_each = local.consumer_accounts

  principal = each.value

  permissions                   = ["DESCRIBE"]
  permissions_with_grant_option = ["DESCRIBE"]

  lf_tag_policy {
    resource_type = "DATABASE"

    # THE VALUE LIST IS WRITTEN LITERALLY ON PURPOSE - the exact inverse of governance.tf,
    # where the lists are read from the tag resources so a new ontology value cannot go
    # missing. Here a new value must NOT arrive: this is a SUBSET, and a `layer` added to the
    # ontology tomorrow joining every consumer share by inheritance is the widening nobody
    # decided. The literal is the control.
    expression {
      key    = aws_lakeformation_lf_tag.layer.key
      values = ["raw", "curated"]
    }
  }
}

# ---------------------------------------------------------------------- the table share (7.2)

resource "aws_lakeformation_permissions" "share_tables" {
  for_each = local.consumer_accounts

  principal = each.value

  # SELECT is the read; DESCRIBE is what makes the table enumerable. No INSERT, DELETE, ALTER
  # or DROP anywhere: the consumer side of this design writes through the drop-box and its own
  # derived zone, never into raw or curated (D18, D19). The governed WRITE is Stage 9's, in
  # Production, and it is a different grant to a different principal.
  permissions                   = ["SELECT", "DESCRIBE"]
  permissions_with_grant_option = ["SELECT", "DESCRIBE"]

  lf_tag_policy {
    resource_type = "TABLE"

    # TWO expression blocks in ONE grant is an AND, which is what the drop-box exclusion needs:
    # "If multiple LF-Tags are granted to a principal with a single grant, the principal can
    # access only Data Catalog resources that have all of the LF-Tags." Two separate grants
    # would be an OR and would share the drop-box back.
    expression {
      key    = aws_lakeformation_lf_tag.layer.key
      values = ["raw", "curated"]
    }

    # restricted and personal are absent BY ENUMERATION, and that is the classification rule
    # made executable: they travel only on explicit grants to named principals, each recorded
    # in the register (GOVERNANCE.md "Grants"). curated.sample_trades carries internal at the
    # table and restricted on its `counterparty` column - so this grant is also the stage's
    # column-level proof, and the column is expected to be absent from a consumer's SELECT.
    expression {
      key    = aws_lakeformation_lf_tag.classification.key
      values = ["public", "internal"]
    }
  }
}
