# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars,
# the five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The backend is the wrong-account guard: awsds-staging-tfstate exists only in Staging and admits
# no cross-account principal. Applied as awsds-infra-staging. The registry's state is read through
# the profile the generated registry map carries (data.tf), with no provider of its own.

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
