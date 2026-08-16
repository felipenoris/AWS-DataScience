# Provider and backend - Stage 2 steps 2.1 (default_tags) and 2.5 (partial backend).
#
# THE BACKEND BLOCK IS COMMENTED OUT ON PURPOSE, and this is the one slice in the tree where
# that is true. Step 2.2's chicken-and-egg: this slice CREATES the bucket that will hold its
# own state, so phase 1 applies with LOCAL state and phase 2 migrates into S3:
#
#   1. terraform init                                     (no backend - local state)
#      terraform apply                                    (creates the key and the bucket)
#   2. uncomment the terraform{} block below
#      ./scripts/gen-backend-hcl.py sandbox bootstrap      (writes the untracked backend.hcl)
#      terraform init -backend-config=backend.hcl -migrate-state
#   3. rm -f terraform.tfstate terraform.tfstate.backup   (they carry account ids and ARNs;
#                                                          .gitignore covers them, deleting
#                                                          them is what makes that moot)
#
# Every OTHER slice in this repository declares its backend from the first `init` and never
# holds local state at all (step 4) - there is no migration to perform anywhere else.
#
# WHY THE BLOCK IS EMPTY. `backend` cannot interpolate anything - no var, no local - so the
# bucket, the key and the REGION would have to be literals in a .tf file, which
# docs/plan/architecture.md forbids and step 9.1's check rejects. Partial configuration is
# the reconciliation: the literals live in a per-slice backend.hcl, which is generated, is
# not a .tf file and is gitignored.

terraform {
  backend "s3" {}
}

provider "aws" {
  region = var.region

  # THE FIVE MANDATORY TAGS (docs/plan/conventions.md), applied here rather than per resource
  # because NOTHING WOULD STOP AN UNTAGGED CREATE: 1c's tag-enforcement SCP names
  # ec2:RunInstances and nothing else (measured 2026-08-15), so an untagged bucket is created
  # happily and surfaces months later as a cost report with a hole in it. default_tags makes
  # the convention a property of the provider instead of a line to repeat - Lesson 14, a
  # condition that must appear in N places by hand will be missing from one of them.
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
