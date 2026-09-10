# The provider. Same shape as every slice (Stage 2 step 2.1).
#
# The wrong-account guard is the backend: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal.
#
# The awscc provider is declared here and configured identically, because the module's blueprint
# configuration needs one attribute the aws provider does not carry
# (environment_role_permission_boundary - terraform-modules/sagemaker-prereqs/versions.tf). It
# carries no default_tags: awscc has no such block, and the resource it creates is a configuration
# rather than a taggable object.

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
