# WHO MAY CREATE A PROJECT, AND FROM WHICH PROFILE (Stage 6, added 2026-08-22).
#
# THE GAP THIS CLOSES WAS MEASURED, NOT ANTICIPATED. Step 1.7's portal sitting found the two
# profiles listed and the button dead: `User is not permitted to perform operation:
# CreateProject`, byte-identical with the tunnel up and down. `list-policy-grants` on the root
# domain unit then returned an EMPTY list for both CREATE_PROJECT and
# CREATE_PROJECT_FROM_PROJECT_PROFILE, and the unit's only owner was the group profile whose
# rolePrincipalArn is the InfrastructureAccess role that created the domain. So the design had
# exactly one principal able to create a project, and it was Terraform's own - a template
# nobody could instantiate. Listing a profile is a READ; creating from it is a separate
# authorization, and nothing in the stage granted it.
#
# THE GRAIN IS PER PROFILE, NOT DOMAIN-WIDE (user decision, 2026-08-22).
# CREATE_PROJECT_FROM_PROJECT_PROFILE names the profiles it admits;  CREATE_PROJECT would hand
# a group every profile the domain has now and every one it gains later. The finer verb is
# what lets `experimentation` and `engineering` answer to different personas, which is the
# whole point of D21 having drawn a line between them - and it is what makes the association
# reviewable: locals.tf's table says, on one row, where a profile provisions AND who may
# instantiate it.
#
# EVERY FIELD IS createOnly IN THE CFN SCHEMA (measured 2026-08-22 against
# AWS::DataZone::PolicyGrant): principal, detail, entity, policy type. There is no in-place
# edit of a grant - moving `engineering` to another group DESTROYS and re-creates, and a plan
# that says `-/+` here is correct rather than alarming. It also means the coarse grain would
# not have been a cheap starting point to refine later.
#
# THE ENTITY IS THE ROOT DOMAIN UNIT because this design does not subdivide the domain.
# `include_child_domain_units = false` is therefore describing today's shape rather than
# restricting anything; the day a domain unit is created, this flag is the decision about
# whether the grant follows it down, and it should be re-read then rather than inherited.
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
