# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags, CostCenter naming the stage that created
# the resources rather than the stage that happens to be open.
#
# THE WRONG-ACCOUNT GUARD IS THE BACKEND: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal.
#
# ONE PROVIDER, AND THE ABSENCE OF A SECOND IS THE DESIGN. Nothing here crosses an account
# boundary: the bucket, the key it encrypts under, the access role, the Access Grants location
# and every grant are objects of THIS account, and the only principals named are its own
# reserved SSO roles and (from pass 4 onwards) its own SMUS project roles. Compare
# sandbox/data/, which needs an aliased provider precisely because the lake it consumes lives
# somewhere else - the contrast is the point of this bucket's whole compensation argument
# (Stage 16: "it never leaves the account").

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
