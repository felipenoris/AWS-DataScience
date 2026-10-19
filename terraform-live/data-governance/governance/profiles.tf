# The project profiles (Stage 6 step 1.5) - the pass 2c apply.
#
# They wait on the account association. A project profile is a bundle of environment
# configurations, each naming (blueprint, account, Region), and the blueprint has to be
# configured in that account first - which needs the account association, console-only with no
# public API (step 1.3). `profiles_enabled` is false until every account in SMUS_MEMBERS and
# SMUS_DEPLOYMENT_MEMBERS appears in SMUS_ASSOCIATED, and this file creates nothing before then.
# Creating them eagerly and letting the API refuse would fail in the middle of an apply that had
# already created a domain.
#
# A profile fixes the blueprint set (which capabilities a project born of it can ever exercise),
# the account and Region it provisions into, and the Tooling parameters with their Editable
# flags. The levers this design pulls are the account and the parameters the creator can no
# longer change. Each profile names its own blueprints and overrides (locals.tf).
#
# deployment_mode = ON_CREATE for Tooling, ON_DEMAND for the rest. Tooling provisions the working
# environment, so a project without it is not a project; the others are capabilities a project
# member enables when needed, which keeps a new project from standing up an EMR Serverless
# application nobody asked for. Both are per-environment-configuration, the grain the API takes.

resource "awscc_datazone_project_profile" "this" {
  for_each = var.profiles_enabled ? local.project_profiles : {}

  name              = each.key
  description       = each.value.description
  domain_identifier = aws_datazone_domain.this.id
  status            = "ENABLED"

  environment_configurations = [
    for bp in each.value.blueprints : {
      name                     = bp
      environment_blueprint_id = data.aws_datazone_environment_blueprint.enabled[bp].id
      deployment_mode          = bp == "Tooling" ? "ON_CREATE" : "ON_DEMAND"
      deployment_order         = index(each.value.blueprints, bp)

      aws_account = { aws_account_id = local.member_account_ids[each.value.account] }
      aws_region  = { region_name = var.region }

      # locals.blueprint_parameters says which blueprints carry overrides and why the two
      # non-Tooling entries exist (the UpdateProjectProfile required-parameter validation);
      # locals.profile_parameters says which a profile passes.
      configuration_parameters = contains(keys(local.profile_parameters[each.key]), bp) ? {
        parameter_overrides = local.profile_parameters[each.key][bp]
      } : null
    }
  ]

  lifecycle {
    precondition {
      condition = (
        each.value.blueprints[0] == "Tooling" &&
        alltrue([for bp in each.value.blueprints : contains(local.category_one_blueprints, bp)])
      )
      error_message = "A profile bundles blueprints of decision 5's category 1 only, Tooling first (locals.tf)."
    }
  }
}
