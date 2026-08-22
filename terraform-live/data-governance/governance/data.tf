# What this slice reads and does not own.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The member accounts a project profile provisions into - resolved live so that no account id
# enters a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "aws_caller_identity" "development" {
  provider = aws.development
}

# The blueprint ids, resolved BY NAME on the domain (pass 2c only). Terraform's project-profile
# resource takes ids; the decision, the documentation and ./aws/studio.py all speak names, so
# the lookup happens here rather than opaque identifiers being pasted into a variable.
data "aws_datazone_environment_blueprint" "enabled" {
  for_each = var.profiles_enabled ? toset(local.category_one_blueprints) : toset([])

  domain_id = aws_datazone_domain.this.id
  name      = each.value
  managed   = true
}

# ------------------------------------------------------------------- the directory lookups
#
# WHO MAY CREATE A PROJECT (grants.tf, 2026-08-22). Two reads, both through the Identity
# alias, both resolving a NAME written in locals.tf to the id the grant takes. The groups
# themselves are NOT declared in Terraform anywhere and must not be: a group is person-shaped
# and its count grows with headcount, so it stays a directory object and what code owns is the
# ENTITLEMENT pointing at it - the identity seam of docs/plan/conventions.md, and the same
# split identity/sso/data.tf already makes for the permission-set half.
data "aws_ssoadmin_instances" "this" {
  provider = aws.identity
}

# `one()` rather than `[0]`: a second IdC instance must raise here instead of silently taking
# the first, which is the shape identity/sso/locals.tf argues for at length.
data "aws_identitystore_group" "profile_creators" {
  for_each = var.profiles_enabled ? toset([for p in local.project_profiles : p.group]) : toset([])

  provider          = aws.identity
  identity_store_id = one(data.aws_ssoadmin_instances.this.identity_store_ids)

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = each.value
    }
  }
}
