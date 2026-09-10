# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags (Lesson 14).
#
# The wrong-account guard is the backend, not a precondition: this slice's state bucket
# exists only in its own account and admits no cross-account principal, so `terraform init
# -backend-config=backend.hcl` under the wrong profile fails before anything is planned.
# Applied as awsds-infra-staging.


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
