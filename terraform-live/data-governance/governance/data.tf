# What this slice reads and does not own.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The member account the project profile provisions into - resolved live so that no account id
# enters a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "aws_caller_identity" "staging" {
  provider = aws.staging
}

# The role granted the `deployment` profile (Stage 18 decision 3): Staging's InfrastructureAccess,
# resolved by name so neither the account id nor the role's suffix enters a tracked file. `one()`
# refuses a second match.
data "aws_iam_roles" "staging_infrastructure_access" {
  provider    = aws.staging
  name_regex  = "AWSReservedSSO_InfrastructureAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

# The DataZone group that role is: an IAM_ROLE_SESSION_GROUP profile, which every session of the
# role belongs to. Cloud Control resolves `<domain>|<role ARN>` to it (read 2026-10-19), so the
# group profile's id stays out of tracked files like the role's.
data "awscc_datazone_group_profile" "staging_infrastructure_access" {
  id = "${aws_datazone_domain.this.id}|${one(data.aws_iam_roles.staging_infrastructure_access.arns)}"
}

# The identity that presses *Manage* in Sandbox's console (Stage 17 decision 13): Sandbox's
# InfrastructureAccess, resolved the same way, and its session group, made in the portal on
# 2026-10-15 (INT-25), which model-governance.tf makes a member of the governance project.
data "aws_iam_roles" "sandbox_infrastructure_access" {
  provider    = aws.sandbox
  name_regex  = "AWSReservedSSO_InfrastructureAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "awscc_datazone_group_profile" "sandbox_infrastructure_access" {
  id = "${aws_datazone_domain.this.id}|${one(data.aws_iam_roles.sandbox_infrastructure_access.arns)}"
}


# The blueprint ids, resolved by name on the domain (pass 2c only). Terraform's project-profile
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
# Who may create a project (grants.tf). Two reads, both through the Identity alias, both
# resolving a name written in locals.tf to the id the grant takes. The groups themselves are
# declared in Terraform nowhere and must not be: a group is person-shaped and its count grows
# with headcount, so it stays a directory object and code owns the entitlement pointing at it -
# the identity seam of docs/plan/conventions.md, and the split identity/sso/data.tf makes for
# the permission-set half.
data "aws_ssoadmin_instances" "this" {
  provider = aws.identity
}

# `one()` rather than `[0]`: a second IdC instance must raise here instead of silently taking
# the first, which is the shape identity/sso/locals.tf argues for at length.
data "aws_identitystore_group" "profile_creators" {
  for_each = var.profiles_enabled ? toset([for p in local.project_profiles : p.group if p.group != null]) : toset([])

  provider          = aws.identity
  identity_store_id = one(data.aws_ssoadmin_instances.this.identity_store_ids)

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = each.value
    }
  }
}
