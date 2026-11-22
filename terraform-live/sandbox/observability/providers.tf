# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars,
# the five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The backend is the wrong-account guard: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal. Every read stays in this account.
# Applied as awsds-infra-sandbox-1.

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
