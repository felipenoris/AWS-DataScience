# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags - Lesson 14, a condition that must appear
# in N places by hand will be missing from one of them.
#
# THE WRONG-ACCOUNT GUARD IS THE BACKEND, not a precondition: this slice's state bucket
# exists only in its own account and admits no cross-account principal, so `terraform init
# -backend-config=backend.hcl` under the wrong profile fails before anything is planned.
# Applied as awsds-infra-sandbox-1 - D35: this folder is a business unit's sandbox, not
# *the* sandbox, and nothing here may say otherwise (step 3.3 of Stage 2).

provider "aws" {
  region = var.region

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
