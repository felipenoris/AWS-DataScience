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

  principal = {
    group = {
      group_identifier = data.aws_identitystore_group.profile_creators[each.value.group].group_id
    }
  }

  detail = {
    create_project_from_project_profile = {
      project_profiles           = [awscc_datazone_project_profile.this[each.key].project_profile_id]
      include_child_domain_units = false
    }
  }
}
