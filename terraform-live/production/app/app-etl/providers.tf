# The provider. The shape of every slice (Stage 2 step 2.1): region from the generated tfvars, the
# five mandatory tags as default_tags. The backend is the wrong-account guard: awsds-<env>-tfstate
# exists only in its own account and admits no cross-account principal.

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

locals {
  tags = {
    Project     = var.project
    Environment = var.environment_tag
    ManagedBy   = "terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }
}
