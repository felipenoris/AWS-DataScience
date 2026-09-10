# The provider - Stage 2 step 2.1 (default_tags), applied to the organization's policy plane.
#
# The region is a variable and not a literal: docs/plan/architecture.md §4.1, and step 9.1's
# check scans for it. The value arrives from the generated, gitignored terraform.auto.tfvars
# (./scripts/gen-tfvars.py identity org-policies).
#
# Organizations is a global service, and its endpoint answers in us-east-1 whatever this says
# (measured 1d step 12). What `region` decides here is the backend's region and the S3 calls
# that read and write this slice's state: pointing it elsewhere breaks the state read, not a
# policy call, and the failure reads like a credentials problem.

provider "aws" {
  region = var.region

  # The five mandatory tags (docs/plan/conventions.md). Environment is `org` here: an
  # organization policy is a platform resource, sitting on neither the lifecycle axis nor the
  # ownership one - the same reading identity/sso/ makes of itself.
  #
  # CostCenter is stage-01c for the whole slice, the opposite arrangement to sso/, where six sets
  # were created by Stage 2 and one imported set overrode the tag to stage-01b. Every one of the
  # ten documents here was written and attached by hand in Stage 1c step 7 and this stage creates
  # none of them, so the value is the same for all ten and belongs in the default rather than in
  # ten overrides.
  #
  # All ten carry no tags at all - measured 2026-08-16 with list-tags-for-resource. So unlike
  # sso/, this slice cannot meet step 5.5's gate on the first plan: `default_tags` adds five tags
  # to ten policies, which is a create, not a drift. It is the first exercise of step 5.1's third
  # delegation statement (organizations:TagResource). The gate that applies here is zero diff on
  # `content` and on `type`.
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
