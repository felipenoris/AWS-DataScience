# Step 6, pass 2 - the governance manager's own grants (decision 5).
#
# This file is separate from maintenance.tf because those grants are machinery - what the catalog
# needs to maintain itself, named-resource by necessity. These are the first grants made to a
# human persona, and they deliver decision 5's second half: "the governance manager is never an
# admin ... and receives SPECIFIC GRANTS instead, each in the register" (docs/AWS_STATE.md, the
# Lake Formation grant register).
#
# What the persona is for: locals.tf in identity/sso/ describes the set as "The catalog, never
# the rows." docs/GOVERNANCE.md assigns it the tagging job - "Assigning LF-Tags to datasets is
# the Governance Manager's responsibility." The grants below are that sentence made executable.
#
# Both halves are required and they live in different slices. The IAM half already exists
# (identity/sso/policies-approvers.tf, `AdministerLakeFormation` - AddLFTagsToResource,
# GrantPermissions, CreateLFTag, ...) and is not sufficient on its own: Lake Formation authorizes
# separately, so holding lakeformation:AddLFTagsToResource in IAM and holding ASSOCIATE on the
# tag in Lake Formation are two different grants and the persona needs both. A reading of one
# slice proves nothing about the persona's reach; the pair does.
#
# No grant option anywhere below: permissions_with_grant_option would let the governance manager
# re-grant tag association to other principals, a delegation nobody has decided. Decision 5 named
# the persona's own grants, not a delegation plane. It stays absent until a decision asks for it.

# ------------------------------------------------------------ ASSOCIATE on the LF-Tag keys
#
# ASSOCIATE lets a principal assign the tag to a Data Catalog resource, and granting it
# implicitly grants DESCRIBE on the tag (AWS Lake Formation documentation, read 2026-08-19 -
# docs/REFERENCES.md). One grant per key, values enumerated from the tag resources themselves so
# a value added to the ontology cannot be silently missing here; writing the list literally would
# be Lesson 14's shape.
#
# businessunit is absent for the same reason it is absent from the ontology: it has no values at
# N=1 (D35), so there is no tag to associate. The security-zone grant left with the tag itself
# when encryption became per account and carried no catalog dimension.

resource "aws_lakeformation_permissions" "gm_associate_classification" {
  principal   = local.governance_manager_role_arn
  permissions = ["ASSOCIATE"]

  lf_tag {
    key    = aws_lakeformation_lf_tag.classification.key
    values = aws_lakeformation_lf_tag.classification.values
  }
}

resource "aws_lakeformation_permissions" "gm_associate_layer" {
  principal   = local.governance_manager_role_arn
  permissions = ["ASSOCIATE"]

  lf_tag {
    key    = aws_lakeformation_lf_tag.layer.key
    values = aws_lakeformation_lf_tag.layer.values
  }
}

# ------------------------------------------------- DESCRIBE on the catalog it has to tag
#
# Without these the persona sees an empty catalog: with Lake Formation enforcing,
# glue:GetDatabases and glue:GetTables return only what the caller holds LF permissions on. The
# IAM half grants the API call; Lake Formation decides what the call returns. A governance
# manager who cannot enumerate a table cannot tag it, and the failure is an empty list rather
# than an error (Lesson 13).
#
# DESCRIBE is metadata and not data, which keeps this inside D31: it returns the name, the schema
# and the location, never a row. The routes from the catalog to the rows stay closed by the
# persona's own IAM deny (`DenyReadingTheRows`: athena:*, lakeformation:GetDataAccess, s3:Get*),
# and this file adds no SELECT anywhere.
#
# The table wildcard covers tables that do not exist yet, so the crawlers' inferred tables arrive
# without anybody re-granting. In an Allow reaching data the same wildcard would be the defect.

resource "aws_lakeformation_permissions" "gm_describe_database" {
  for_each = local.governed_databases

  principal   = local.governance_manager_role_arn
  permissions = ["DESCRIBE"]

  database { name = each.value }
}

resource "aws_lakeformation_permissions" "gm_describe_tables" {
  for_each = local.governed_databases

  principal   = local.governance_manager_role_arn
  permissions = ["DESCRIBE"]

  table {
    database_name = each.value
    wildcard      = true
  }
}
