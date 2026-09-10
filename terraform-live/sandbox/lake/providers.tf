# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags, CostCenter naming the stage that created
# the resources rather than the stage that happens to be open.
#
# The wrong-account guard is the backend: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal.
#
# There is no second, aliased provider because nothing here crosses an account boundary. The bucket,
# the key it encrypts under, the access role, the Access Grants location and every grant are objects
# of this account, and the only principals named are its own reserved SSO roles and, from pass 4
# onwards, its own SMUS project roles. sandbox/data/ needs an aliased provider because the lake it
# consumes lives elsewhere.

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
