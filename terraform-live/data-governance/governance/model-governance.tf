# The model governance project (Stage 17 decision 13, taken 2026-10-19 as (b)).
#
# The console's Amazon Bedrock models tab enables a model by publishing a catalog asset owned by a
# project named GenerativeAIModelGovernanceProject. A project reaches the model by subscribing to the
# listing, and the grant's target is an application inference profile in the project's account (the
# console's and the portal's code, read 2026-10-19). In an associated account the tab's Manage stays
# greyed until that project exists and lists the caller as a member: "Model governance project does
# not exist", read in Sandbox's console the same day. Only the domain account's setup creates it, in
# the run that also configures the Bedrock blueprints and Tooling here, which D22 forbids, so this file
# writes the objects that run would make and nothing else.
#
# Both names are contracts with the console's code (Lesson 48): an associated account finds the
# project by its name, and the domain account's setup checks the profile by its name. The profile has
# no environment configuration. The console creates the project's environments itself, one custom
# environment per enabled model in the model's account, each holding a role of
# sandbox/model-access/.
#
# Terraform's identity creates the project and owns it: the role that created the domain owns the
# root domain unit, which creates a project with no grant (grants.tf). Sandbox's InfrastructureAccess
# joins as PROJECT_CONTRIBUTOR, the designation the console's own "Add IAM users or roles" writes for
# an associated account's role, through the role's session group, the principal a DataZone grant to
# an IAM role takes.
#
# The console publishes into this project, so a destroy fails while it holds assets or environments:
# a model is disabled in the console before the project goes.

resource "awscc_datazone_project_profile" "model_governance" {
  count = var.profiles_enabled ? 1 : 0

  name              = "Generative AI model governance"
  description       = "Stage 17 decision 13: the profile of the project that owns the Amazon Bedrock model listings. No environment configuration; the console creates one environment per enabled model."
  domain_identifier = aws_datazone_domain.this.id
  status            = "ENABLED"
}

resource "awscc_datazone_project" "model_governance" {
  count = var.profiles_enabled ? 1 : 0

  name               = "GenerativeAIModelGovernanceProject"
  description        = "Owns the Amazon Bedrock model assets the console's Amazon Bedrock models tab publishes (Stage 17 decision 13)."
  domain_identifier  = aws_datazone_domain.this.id
  project_profile_id = awscc_datazone_project_profile.model_governance[0].project_profile_id
}

resource "awscc_datazone_project_membership" "model_governance_sandbox_infrastructure" {
  count = var.profiles_enabled ? 1 : 0

  domain_identifier  = aws_datazone_domain.this.id
  project_identifier = awscc_datazone_project.model_governance[0].project_id
  designation        = "PROJECT_CONTRIBUTOR"

  member = {
    group_identifier = data.awscc_datazone_group_profile.sandbox_infrastructure_access.group_profile_id
  }
}
