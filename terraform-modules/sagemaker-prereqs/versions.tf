# Version pin. Same constraint as every slice (Stage 2 step 1); the exact build is pinned by
# each caller's .terraform.lock.hcl - a module carries no lock file of its own.
#
# The awscc provider is here for two resources. aws_datazone_environment_blueprint_configuration
# (the aws provider's) has no environment_role_permission_boundary field, and that field is how the
# D13 boundary reaches roles DataZone authors rather than roles this repository authors (INT-15) -
# measured against the pinned schemas on 2026-08-21. awscc_datazone_policy_grant (grants.tf,
# 2026-08-22) exists in no other provider at all. conventions §6 anticipates the split - "domain +
# IAM through the aws provider, project profiles / blueprints / projects through awscc".

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.89"
    }
  }
}
