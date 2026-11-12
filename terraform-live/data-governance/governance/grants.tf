# Who may create a project, and from which profile (Stage 6).
#
# The gap was measured, not anticipated. Step 1.7's portal sitting found the profiles listed and
# the button dead: `User is not permitted to perform operation: CreateProject`, byte-identical
# with the tunnel up and down. `list-policy-grants` on the root domain unit returned an empty
# list for both CREATE_PROJECT and CREATE_PROJECT_FROM_PROJECT_PROFILE, and the unit's only owner
# was the group profile whose rolePrincipalArn is the InfrastructureAccess role that created the
# domain. The design had exactly one principal able to create a project, Terraform's own - a
# template nobody could instantiate. Listing a profile is a read; creating from it is a separate
# authorization, and nothing in the stage granted it.
#
# The grain is per profile, not domain-wide (user decision, 2026-08-22).
# CREATE_PROJECT_FROM_PROJECT_PROFILE names the profiles it admits; CREATE_PROJECT would hand a
# group every profile the domain has now and every one it gains later. The finer verb is what
# lets profiles answer to different personas along D21's line, and it makes the association
# reviewable: locals.tf's table says on one row where a profile provisions and who may
# instantiate it.
#
# Every field is createOnly in the CFN schema (measured 2026-08-22 against
# AWS::DataZone::PolicyGrant): principal, detail, entity, policy type. There is no in-place edit
# of a grant - moving one to another group destroys and re-creates, so a plan that says `-/+`
# here is correct. The coarse grain would not have been a cheap starting point to refine later.
#
# The entity is the root domain unit because this design does not subdivide the domain.
# `include_child_domain_units = false` describes today's shape rather than restricting anything;
# the day a domain unit is created, this flag is the decision about whether the grant follows it
# down, and it is re-read then rather than inherited.
resource "awscc_datazone_policy_grant" "create_project_from_profile" {
  for_each = var.profiles_enabled ? local.project_profiles : {}

  domain_identifier = aws_datazone_domain.this.id
  entity_type       = "DOMAIN_UNIT"
  entity_identifier = aws_datazone_domain.this.root_domain_unit_id
  policy_type       = "CREATE_PROJECT_FROM_PROJECT_PROFILE"

  # A profile with a null `group` grants its own account's InfrastructureAccess role, as the role's
  # IAM role session group. The role's ARN as a user principal is refused, "Group profile already
  # exists for the given User profile": it resolves to one session's user profile, a member of that
  # group (measured 2026-10-19).
  principal = {
    group = {
      group_identifier = (
        each.value.group != null
        ? data.aws_identitystore_group.profile_creators[each.value.group].group_id
        : local.infrastructure_access_group_ids[each.value.account]
      )
    }
  }

  detail = {
    create_project_from_project_profile = {
      project_profiles           = [awscc_datazone_project_profile.this[each.key].project_profile_id]
      include_child_domain_units = false
    }
  }
}

# Who may create a metadata form type, and owning which project (Stage 19 decision 4).
#
# Measured the way the grant above was: on 2026-11-09 the portal showed the data scientist *Create
# metadata forms* disabled, and `list-policy-grants` on the root domain unit had returned no
# CREATE_FORM_TYPE grant the day before. Decision 4 carries a product's classification in a metadata
# form type `classification` owned by the producing project; each key of var.form_type_owners is such a
# project. The grain is one project, never every project of the unit: a form type is visible to the
# whole domain and attachable by any project, so one owner serves them all, and a second owner is decision
# 4's owner question (Stage 19 3.2), not a default. OWNER admits the project's owners alone.
resource "awscc_datazone_policy_grant" "create_form_type" {
  for_each = var.form_type_owners

  domain_identifier = aws_datazone_domain.this.id
  entity_type       = "DOMAIN_UNIT"
  entity_identifier = aws_datazone_domain.this.root_domain_unit_id
  policy_type       = "CREATE_FORM_TYPE"

  principal = {
    project = {
      project_identifier  = each.key
      project_designation = each.value
    }
  }

  detail = {
    create_form_type = {
      include_child_domain_units = false
    }
  }
}

# What the CI/CD CLI's catalog import checks before it writes (Stage 19 step 4.5). Its pre-flight
# lists the root domain unit's CREATE_GLOSSARY, CREATE_FORM_TYPE and CREATE_ASSET_TYPE grants; where a
# type has none, whoever the grants of the other types name, it calls AddPolicyGrant for the target
# project's owners as the identity that deploys, and aborts the import if that call is refused (the
# CLI 1.0.9's helpers/catalog_import.py, read 2026-11-11; the unit held no CREATE_GLOSSARY and no
# CREATE_ASSET_TYPE grant that day). A deploy role holds no AddPolicyGrant and owns no domain unit, so
# the grants the CLI would write are declared here, one of each type per deployment project. They let
# that project's owners create a glossary, a form type or an asset type the project then owns, which
# is what the import does with one a bundle carries.
locals {
  catalog_import_grants = merge([
    for project, designation in var.catalog_import_projects : {
      for policy in ["CREATE_GLOSSARY", "CREATE_FORM_TYPE", "CREATE_ASSET_TYPE"] :
      "${project}:${policy}" => { project = project, designation = designation, policy = policy }
    }
  ]...)
}

resource "awscc_datazone_policy_grant" "catalog_import" {
  for_each = local.catalog_import_grants

  domain_identifier = aws_datazone_domain.this.id
  entity_type       = "DOMAIN_UNIT"
  entity_identifier = aws_datazone_domain.this.root_domain_unit_id
  policy_type       = each.value.policy

  principal = {
    project = {
      project_identifier  = each.value.project
      project_designation = each.value.designation
    }
  }

  detail = {
    create_glossary   = each.value.policy == "CREATE_GLOSSARY" ? { include_child_domain_units = false } : null
    create_form_type  = each.value.policy == "CREATE_FORM_TYPE" ? { include_child_domain_units = false } : null
    create_asset_type = each.value.policy == "CREATE_ASSET_TYPE" ? { include_child_domain_units = false } : null
  }
}
