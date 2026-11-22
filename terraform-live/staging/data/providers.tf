# The providers. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars, the
# five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The backend is the wrong-account guard: awsds-staging-tfstate exists only in Staging and admits no
# cross-account principal. Applied as awsds-infra-staging.

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

# The lake's account, read-only: one data.aws_caller_identity read for its id, which the resource links
# and the regrants address. It creates nothing, so it carries no default_tags, and the profile arrives
# from the generated tfvars (DATA_LAKE in scripts/tfhygiene/backend.py), never as a literal here.
provider "aws" {
  alias   = "lake"
  region  = var.region
  profile = var.lake["data-governance"].profile
}
