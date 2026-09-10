# The provider - Stage 2 step 2.1 (default_tags).
#
# The backend is not here. It lives in backend.tf alone, because it is the one part of a bootstrap
# slice that differs between a migrated slice and a fresh one (step 2.2's two-phase apply).
# Everything in this file is identical in all five bootstrap slices, and step 3.5's check enforces
# that.
#
# The region is a variable and not a literal: docs/plan/architecture.md §4.1, and step 9.1's check
# scans for it. The value arrives from the generated, gitignored terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> bootstrap).

provider "aws" {
  region = var.region

  # The mandatory tags (docs/plan/conventions.md), applied here rather than per resource because
  # nothing would stop an untagged create: 1c's tag-enforcement SCP names ec2:RunInstances and
  # nothing else (measured 2026-08-15), so an untagged bucket is created happily and surfaces
  # months later as a cost report with a hole in it. default_tags makes the convention a property
  # of the provider instead of a line to repeat (Lesson 14).
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
