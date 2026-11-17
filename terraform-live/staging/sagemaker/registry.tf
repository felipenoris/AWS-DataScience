# Stage 17 step 9.5 - Staging's Model Registry: a package group per family whose versions a task
# registers in this account, which staging-test approves.
#
#   app-ml   registered by the register task as the deployment project's role (Stage 17 decision
#            16 (b)), approved by awsds-deploy-staging
#
# No resource policy: no other account reads these versions, since the model reaches each account in
# the release's bundle, and inside this account the identity policies admit the calls
# (staging/studio/workflows.tf for the project role, staging/foundation/deploy-role.tf for the deploy
# role). app-etl's versions stay in Production's registry (production/sagemaker/registry.tf).
#
# A package group costs nothing at rest.

locals {
  # SageMaker has no call that updates a group, so a changed description replaces the group.
  model_families = {
    "app-ml" = {
      description = "app-ml's model versions in Staging: registered by a task as the deployment project's role, approved by the Staging deploy role alone (Stage 17 decision 16 (b))"
    }
  }
}

resource "aws_sagemaker_model_package_group" "this" {
  for_each = local.model_families

  model_package_group_name        = "awsds-${var.env}-model-${each.key}"
  model_package_group_description = each.value.description

  tags = {
    Name = "awsds-${var.env}-model-${each.key}"
  }
}
