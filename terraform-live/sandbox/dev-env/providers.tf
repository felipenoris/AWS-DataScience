# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars,
# the five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The wrong-account guard is the backend: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal.
#
# There is no aliased provider although this slice reads the registry account. What it needs from
# Production is two values - the repository URL and the two repository ARNs - and both are outputs
# of production/registry/, so the read is a terraform_remote_state with a profile (data.tf) rather
# than a second provider. A provider would let this slice create something over there; a state read
# cannot.

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
