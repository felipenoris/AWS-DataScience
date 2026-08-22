# THE TWO PROJECT PROFILES (Stage 6 step 1.5) - the pass 2c apply.
#
# WHY THEY WAIT. A project profile is a bundle of ENVIRONMENT CONFIGURATIONS, and each one
# names (blueprint, account, Region). The blueprint has to be CONFIGURED in that account first
# - which needs the account association, which is console-only and has no public API (step
# 1.3). So `profiles_enabled` is false until every member in SMUS_MEMBERS appears in
# SMUS_ASSOCIATED, and this file creates nothing before then. The alternative - creating them
# eagerly and letting the API refuse - would fail in the middle of an apply that had already
# created a domain.
#
# WHAT A PROFILE FIXES, AND WHY THAT IS THE CONTROL SURFACE: the blueprint set (which
# capabilities a project born of it can EVER exercise), the account and Region it provisions
# into, and the Tooling parameters with their Editable flags. Two of those are the levers this
# design actually pulls - which account, and which parameters the creator can no longer change.
#
# deployment_mode = ON_CREATE for Tooling, ON_DEMAND for the rest. Tooling is what provisions
# the working environment at all, so a project without it is not a project; the other ten
# are capabilities a project member enables when they need them, which keeps a new project from
# standing up an EMR Serverless application nobody asked for. Both are per-environment-
# configuration, which is the grain the API takes.

resource "awscc_datazone_project_profile" "this" {
  for_each = var.profiles_enabled ? local.project_profiles : {}

  name              = each.key
  description       = each.value.description
  domain_identifier = aws_datazone_domain.this.id
  status            = "ENABLED"

  environment_configurations = [
    for bp in local.category_one_blueprints : {
      name                     = bp
      environment_blueprint_id = data.aws_datazone_environment_blueprint.enabled[bp].id
      deployment_mode          = bp == "Tooling" ? "ON_CREATE" : "ON_DEMAND"
      deployment_order         = index(local.category_one_blueprints, bp)

      aws_account = { aws_account_id = local.member_account_ids[each.value.account] }
      aws_region  = { region_name = var.region }

      configuration_parameters = bp == "Tooling" ? {
        parameter_overrides = local.tooling_parameters
      } : null
    }
  ]
}
