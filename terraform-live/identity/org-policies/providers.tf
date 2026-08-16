# The provider - Stage 2 step 2.1 (default_tags), applied to the organization's policy plane.
#
# WHY THE REGION IS A VARIABLE and not a literal: docs/plan/architecture.md §4.1, and step
# 9.1's check scans for it. The value arrives from the generated, gitignored
# terraform.auto.tfvars (./scripts/gen-tfvars.py identity org-policies).
#
# ORGANIZATIONS IS A GLOBAL SERVICE AND THE REGION STILL MATTERS - for a reason that is not
# about Organizations. Its endpoint answers in us-east-1 whatever this says, which 1d step 12
# measured; what `region` decides here is the BACKEND's region and the S3 calls that read and
# write this slice's state. Pointing it elsewhere does not break a policy call, it breaks the
# state read - a failure that reads like a credentials problem.

provider "aws" {
  region = var.region

  # THE FIVE MANDATORY TAGS (docs/plan/conventions.md). Environment is `org` here: an
  # organization policy is a PLATFORM resource, sitting on neither the lifecycle axis nor the
  # ownership one - the same reading identity/sso/ makes of itself.
  #
  # COSTCENTER IS stage-01c FOR THE WHOLE SLICE, WHICH IS THE OPPOSITE ARRANGEMENT TO sso/.
  # There, six sets were CREATED by Stage 2 and one imported set overrode the tag to stage-01b.
  # Here every one of the ten documents was written and attached by hand in Stage 1c step 7 and
  # this stage creates none of them, so the honest value is the same for all ten and it belongs
  # in the default rather than in ten overrides.
  #
  # ALL TEN CARRY NO TAGS AT ALL TODAY - measured 2026-08-16 with list-tags-for-resource. So
  # unlike sso/, this slice CANNOT meet step 5.5's gate on the first plan: `default_tags` adds
  # five tags to ten policies, and that is a create, not a drift. It is the first exercise of
  # step 5.1's third delegation statement (organizations:TagResource). The gate that applies
  # here is the one 5.5 is actually about: zero diff on `content` and on `type`.
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
