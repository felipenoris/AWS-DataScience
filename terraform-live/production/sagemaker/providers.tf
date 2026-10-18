# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars,
# the five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The backend is the wrong-account guard: awsds-prod-tfstate exists only in Production and admits
# no cross-account principal. Applied as awsds-infra-prod.

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

# ------------------------------------------------- the read-only reader provider
#
# One alias, for one data.aws_caller_identity read, the idiom of production/registry/providers.tf:
# it creates nothing, so it carries no default_tags, and the profile arrives from the generated
# tfvars (SMUS_MEMBERS in scripts/tfhygiene/backend.py), never as a literal here. The package
# groups' read-status statement names the Sandbox account (decision 10), and aws/INDEX.md rule 1
# keeps account ids out of tracked files.
#
# The alias key is static while D35 says sandboxes multiply. Terraform cannot for_each a provider,
# so a second unit adds an alias here by hand, as production/registry/ does.

provider "aws" {
  alias   = "sandbox"
  region  = var.region
  profile = var.readers["sandbox"].profile
}
