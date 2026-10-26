# The provider. Same shape as every slice (Stage 2 step 2.1), and the second provider sandbox/sagemaker/
# carries for the same attribute: the blueprint configuration's environment_role_permission_boundary
# exists in awscc alone (terraform-modules/sagemaker-prereqs/versions.tf).

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

provider "awscc" {
  region = var.region
}
