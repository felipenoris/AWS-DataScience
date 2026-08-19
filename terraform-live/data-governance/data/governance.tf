# Step 6, pass 2 - the governance manager's own grants (decision 5).
#
# WHY THIS FILE EXISTS SEPARATELY FROM maintenance.tf: those grants are MACHINERY - what the
# catalog needs to maintain itself, named-resource by necessity. These are the first grants
# made to a HUMAN persona, and they are the delivery of decision 5's second half: "the
# governance manager is never an admin ... and receives SPECIFIC GRANTS instead, each in the
# register" (docs/AWS_STATE.md, the Lake Formation grant register).
#
# WHAT THE PERSONA IS FOR, in its own words: locals.tf in identity/sso/ describes the set as
# "The catalog, never the rows." docs/GOVERNANCE.md assigns it the tagging job - "Assigning
# LF-Tags to datasets is the Governance Manager's responsibility." The grants below are that
# sentence made executable and nothing more.
#
# THE TWO HALVES ARE IN DIFFERENT SLICES AND BOTH ARE REQUIRED, which is the trap worth
# naming: the IAM half already exists (identity/sso/policies-approvers.tf,
# `AdministerLakeFormation` - AddLFTagsToResource, GrantPermissions, CreateLFTag, ...) and it
# is NOT sufficient on its own. Lake Formation authorizes separately: holding
# lakeformation:AddLFTagsToResource in IAM and holding ASSOCIATE on the tag in Lake Formation
# are two different grants, and the persona needs both. A reading of one slice therefore
# proves nothing about the persona's actual reach - the pair does.
#
# WHY NO GRANT OPTION ANYWHERE BELOW: permissions_with_grant_option would let the governance
# manager re-grant tag association to other principals, which is a delegation nobody has
# decided. Decision 5 named the persona's own grants, not a delegation plane. It stays absent
# until a decision asks for it.

# ------------------------------------------------------ ASSOCIATE on the three LF-Tag keys
#
# ASSOCIATE is what lets a principal ASSIGN the tag to a Data Catalog resource, and granting
# it implicitly grants DESCRIBE on the tag (AWS Lake Formation documentation, read
# 2026-08-19 - docs/REFERENCES.md). One grant per key, values enumerated from the tag
# resources themselves so a value added to the ontology cannot be silently missing here -
# writing the list literally would be Lesson 14's shape (a set that must agree in N places).
#
# businessunit is absent for the same reason it is absent from the ontology: it has no values
# at N=1 (D35), so there is no tag to associate.

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

resource "aws_lakeformation_permissions" "gm_associate_security_zone" {
  principal   = local.governance_manager_role_arn
  permissions = ["ASSOCIATE"]

  lf_tag {
    key    = aws_lakeformation_lf_tag.security_zone.key
    values = aws_lakeformation_lf_tag.security_zone.values
  }
}

# ------------------------------------------------- DESCRIBE on the catalog it has to tag
#
# WITHOUT THESE THE PERSONA SEES AN EMPTY CATALOG, and that is not a hypothetical: with Lake
# Formation enforcing, glue:GetDatabases and glue:GetTables return only what the caller holds
# LF permissions on. The IAM half grants the API call; Lake Formation decides what the call
# RETURNS. A governance manager who cannot enumerate a table cannot tag it, and the failure
# looks like an empty list rather than an error (Lesson 13's shape - so it is worth stating
# that the negative here is silent).
#
# DESCRIBE IS METADATA AND NOT DATA, which is what keeps this inside D31 rather than against
# it: it returns the name, the schema and the location - never a row. The three routes from
# the catalog to the rows stay closed by the persona's own IAM deny (`DenyReadingTheRows`:
# athena:*, lakeformation:GetDataAccess, s3:Get*), and this file adds no SELECT anywhere.
#
# The table wildcard covers tables that do not exist yet - the crawlers' inferred tables
# arrive without anybody re-granting, which is the point of a wildcard here and would be the
# defect in an Allow reaching data.

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
