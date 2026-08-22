# WHO MAY CREATE AN ENVIRONMENT FROM EACH BLUEPRINT (Stage 6, added 2026-08-22) - the
# blueprint-level twin of data-governance/governance/grants.tf, one authorization layer down.
#
# THE GAP THIS CLOSES WAS MEASURED THE SAME WAY AS THAT FILE'S, one day later. With the
# CREATE_PROJECT_FROM_PROJECT_PROFILE grants applied, the first real project creation got
# PAST the project check and died on the next one: "Falha na implantacao do ambiente do
# projeto Tooling ... Caller is not authorized to create environment using blueprintId
# <Tooling's id>", the project rolled back (list-projects empty, no SageMaker domain, no
# stack in the member account - nothing provisioned, nothing billed). Creating a project and
# creating the environments inside it are SEPARATE authorizations, and nothing granted the
# second: list-policy-grants read ZERO CREATE_ENVIRONMENT_FROM_BLUEPRINT grants on all 22
# blueprint configurations (11 per member account, 2026-08-22).
#
# WHY THE GAP EXISTS AT ALL - the same cause as the profile gap: the console's "enable
# blueprint" flow does two things (create the configuration AND fill "Authorized domain
# units", which emits this grant), while PutEnvironmentBlueprintConfiguration - what the
# resource in blueprints.tf calls - does only the first. Enabling a blueprint and authorizing
# its use are distinct objects, and step 1.4 delivered one of them.
#
# THE ENTITY IDENTIFIER IS UNDOCUMENTED, AND IT IS NOT THE CFN PRIMARY KEY. The API reference
# gives no format; every publicly derivable spelling (bare id, domain|id, ARN) is rejected
# with "Format of EnvironmentBlueprintConfigurationId is invalid". The accepted form -
# measured 2026-08-22, then confirmed against AWS's own sample
# (aws-samples/sample-automate-sagemaker-unified-studio-using-iac, which passes
# "${AWS::AccountId}:${EnvironmentBlueprintId}") - is <account-id>:<blueprint-id>, where the
# ACCOUNT IS THE CONFIGURATION'S OWNER: this member account, not the domain's (fed the domain
# account the API answers "does not exist in account"). Which is also why this resource lives
# HERE rather than beside the profile grants in data-governance/governance/: the entity being
# granted on is this account's configuration, created three resources up in blueprints.tf.
#
# THE PRINCIPAL IS COPIED FROM THAT SAMPLE, NOT DESIGNED: every project in the root domain
# unit, designation CONTRIBUTOR. What CONTRIBUTOR means for this policy type is documented
# nowhere; the sample is a working end-to-end implementation whose ON_CREATE Tooling deploys
# at project creation - exactly our failure mode - so its principal is a measurement where a
# choice of our own would be a guess (Lesson 38 cuts both ways). The one deliberate
# divergence: the sample sets include_child_domain_units = true, this file says false - the
# same argument grants.tf already carries, that this domain is not subdivided, so the flag
# describes today's shape and is re-read the day a domain unit is created, not inherited.
#
# for_each RIDES THE CONFIGURATIONS, so the grant is born and dies with its blueprint: a
# category-2 blueprint joining var.blueprint_names arrives authorized in the same apply, and
# nothing has to be remembered by hand (Lesson 14). Without its grant every ON_DEMAND
# blueprint fails exactly like Tooling did, one capability-enable at a time.
#
# TWO MECHANICAL FACTS THE SHAPE ENCODES (both measured against awscc 1.98.0):
#   - the detail's CFN type is "Unit" (an empty object), which this provider renders as a
#     JSON STRING attribute - hence jsonencode({}), not {};
#   - every field is createOnly (same CFN schema as the profile grants), so any change here
#     plans as -/+ - correct rather than alarming.
resource "awscc_datazone_policy_grant" "create_environment_from_blueprint" {
  for_each = awscc_datazone_environment_blueprint_configuration.enabled

  domain_identifier = var.domain_id
  entity_type       = "ENVIRONMENT_BLUEPRINT_CONFIGURATION"
  entity_identifier = "${data.aws_caller_identity.current.account_id}:${each.value.environment_blueprint_id}"
  policy_type       = "CREATE_ENVIRONMENT_FROM_BLUEPRINT"

  principal = {
    project = {
      project_designation = "CONTRIBUTOR"
      project_grant_filter = {
        domain_unit_filter = {
          domain_unit                = var.root_domain_unit_id
          include_child_domain_units = false
        }
      }
    }
  }

  detail = {
    create_environment_from_blueprint = jsonencode({})
  }
}
