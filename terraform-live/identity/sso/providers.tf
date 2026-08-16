# The provider - Stage 2 step 2.1 (default_tags), applied to the identity plane.
#
# WHY THE REGION IS A VARIABLE and not a literal: docs/plan/architecture.md §4.1, and step
# 9.1's check scans for it. The value arrives from the generated, gitignored
# terraform.auto.tfvars (./scripts/gen-tfvars.py identity sso).
#
# ONE THING THAT IS NOT OBVIOUS FROM THE REGION LINE: an Identity Center instance is a
# REGIONAL object and this organization's lives in us-west-2, so `region` here is not
# incidental - point it elsewhere and data.aws_ssoadmin_instances returns an empty list rather
# than an error, and every resource below fails on an index into nothing. That failure mode is
# why data.tf asserts the instance count instead of indexing straight into [0].

provider "aws" {
  region = var.region

  # THE FIVE MANDATORY TAGS (docs/plan/conventions.md). Environment is `org` here: the identity
  # plane is a PLATFORM resource, not an environment - it sits on neither the lifecycle axis
  # nor the ownership one.
  #
  # CostCenter DEFAULTS TO THIS STAGE AND ONE RESOURCE OVERRIDES IT. The six persona sets are
  # created here, so stage-02 is true of them. `InfrastructureAccess` was created by hand in
  # Stage 1b and carries CostCenter=stage-01b in the directory today - so the imported resource
  # sets that tag explicitly. This is not cosmetic: default_tags would otherwise plan a tag
  # rewrite on the first apply after the import, which is exactly the non-empty plan step 5.5
  # forbids.
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment_tag
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
