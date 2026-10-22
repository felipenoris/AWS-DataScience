# The providers. The aws one has the shape of every slice (Stage 2 step 2.1): region from the
# generated tfvars, the five mandatory tags as default_tags. awscc reads no default tags, so the
# module tags the workflow from the same five values.
#
# The backend is the wrong-account guard: awsds-prod-tfstate exists only in Production and admits
# no cross-account principal.

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

provider "awscc" {
  region = var.region
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
