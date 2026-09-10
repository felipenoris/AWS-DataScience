# The blueprint configurations (Stage 6 step 1.4) - the second apply of this module, and the
# reason for the flag.
#
# PutEnvironmentBlueprintConfiguration takes a domainIdentifier and no account parameter: the
# account it configures is the caller's. That is why enabling blueprints is something an
# associated account does against a shared domain, and why these resources live in the member
# account's slice rather than in data-governance/governance/ - step 1.4's own body says "user
# applies as that account's profile". The share's RAM permission is what lets it, and its name
# is AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess: measured 2026-08-21, RAM
# publishes six permissions for datazone:Domain and that is the one the console attaches.
#
# So the order is: this module's pass 1 (roles, boundary, key) -> the domain -> the console
# association -> this module again, with blueprints_enabled = true.
#
# The awscc provider is here for one attribute (versions.tf carries the measurement):
# environment_role_permission_boundary. The aws provider's equivalent resource has no such
# field, and without it the D13 boundary would have to be attached to blueprint-authored roles
# after the fact - a race with reconciliation, which is INT-15's fallback chain rather than its
# first answer. With it, the service attaches our boundary while creating the role. Verification
# (v) does not go away: it now asks whether the boundary survives, a question about
# reconciliation rather than about our timing.
#
# The identifier this resource takes is the name, not the id (measured 2026-08-21: twelve
# identical create failures, then one CLI contrast that succeeded). The two providers spell
# the same input differently - the aws provider's resource takes environment_blueprint_id,
# an id; this resource rides CloudFormation's contract, where EnvironmentBlueprintIdentifier
# is resolved by name among the domain's managed blueprints (the official example passes
# "DefaultDataLake" - a name) and the resolved id comes back in the separate read-only
# environment_blueprint_id. Fed the id, the handler looked for a blueprint named like an id -
# "Managed Environment Blueprint with <id> doesn't exist", all twelve - while
# get-environment-blueprint returned every one of those ids from the same profile (Lesson 32).
# Passing the name is diff-safe: the CFN schema marks EnvironmentBlueprintIdentifier
# createOnly + writeOnly, so the read never returns it and Terraform keeps what was sent.
# The name is routed through the data source's .name - the same string that went in - so the
# roster guard below (data.tf) is a declared dependency, not an unused declaration.
#
# Write-only cuts the other way too: EnvironmentRolePermissionBoundary is write-only as well,
# so a boundary stripped behind Terraform's back would never surface as a plan diff. The
# sentinel for verification (v) is ./aws/studio.py US-8 (the datazone read API does return
# the field, measured in the same sitting), not this file's plan.
#
# The regional parameters are read, not pasted (step 1.4). VpcId, Subnets and AZs come from
# this account's foundation/ state through the caller. The console recommends three subnets in
# three AZs and D9 built two - verification (iii): the apply either accepts two or it does not,
# and that answer is taken here rather than assumed anywhere.

resource "awscc_datazone_environment_blueprint_configuration" "enabled" {
  for_each = var.blueprints_enabled ? toset(var.blueprint_names) : toset([])

  domain_identifier                = var.domain_id
  environment_blueprint_identifier = data.aws_datazone_environment_blueprint.enabled[each.value].name
  enabled_regions                  = [var.region]

  provisioning_role_arn = module.provisioning_role.role_arn

  # Every configuration names the manage-access role, Tooling included. Tooling alone passed
  # null here at first - an undocumented assumption that the base environment, provisioning no
  # catalog, needed no subscription-fulfilment role. The service disagrees, and at deployment
  # time rather than at Put time: the configuration accepted the null on 2026-08-21, and the
  # first project whose policy grants let it get that far died with "Manage Access Role Arn for
  # environment blueprint id <Tooling's> not defined" - the project survived ACTIVE, the Tooling
  # environment failed before its CloudFormation stack existed. The console's own Enable-Tooling
  # wizard asks for this role, which is the reading the null contradicted (Lesson 16). It is the
  # same role the other ten name: AmazonDataZoneSageMakerManageAccessRolePolicy is AWS's one
  # SMUS manage-access policy, and a second role for Tooling would be a split nothing measures.
  manage_access_role_arn = module.manage_access_role.role_arn

  environment_role_permission_boundary = aws_iam_policy.project_boundary.arn

  # Tooling alone carries two more parameters: S3Location - the wizard's "S3 bucket for
  # projects", whose absence deploys and deletes every project into "Invalid S3 path provided
  # null" - and KmsKeyArn, the project CMK finding its consumer (kms.tf). Both names are
  # aws-samples' SMUS-IaC Tooling block, the same source as the grant principal. The merge is
  # not applied to the other ten: a regional-parameter change is an update to an applied
  # configuration, and an applied configuration is immutable through this provider
  # (docs/SMUS.md §Blueprints (b)), so widening all eleven would manufacture twenty more
  # impossible updates for zero behaviour.
  regional_parameters = [
    {
      region = var.region
      parameters = merge(
        {
          VpcId   = var.vpc_id
          Subnets = join(",", values(var.private_subnet_ids))
          AZs     = join(",", keys(var.private_subnet_ids))
        },
        each.value == "Tooling" ? {
          S3Location = "s3://${module.projects_bucket.bucket_name}"
          KmsKeyArn  = module.project_key.key_arn
        } : {}
      )
    },
  ]
}
