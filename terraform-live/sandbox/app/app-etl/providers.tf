# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars, the five
# mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The wrong-account guard is the backend: this slice's state lives in this account's own
# awsds-<env>-tfstate. The one cross-account read, production/registry/'s state, carries its own profile
# in the remote-state configuration (data.tf), as sandbox/dev-env/'s does.

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
