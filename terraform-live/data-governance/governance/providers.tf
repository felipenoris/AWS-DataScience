# The provider. Same shape as every slice (Stage 2 step 2.1).
#
# The wrong-account guard is the backend: awsds-data-tfstate exists only in Data Governance
# and admits no cross-account principal. Applied as awsds-infra-data.
#
# The awscc provider carries the project profiles: awscc_datazone_project_profile is the only
# Terraform resource for them in either provider (measured against the pinned schemas
# 2026-08-21). conventions §6 names the split - "domain + IAM through the aws provider,
# project profiles / blueprints / projects through awscc".

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

# --------------------------------------------------- the read-only member providers
#
# One alias per data.aws_caller_identity read - the idiom data-governance/data/providers.tf
# established. An alias exists here only to resolve the account a project profile provisions
# into: each profile's environment configuration names that account, and aws/INDEX.md rule 1
# keeps account ids out of tracked files. They create nothing, carry no default_tags, and their
# profiles arrive from the generated tfvars (SMUS_MEMBERS in scripts/tfhygiene/backend.py),
# never as literals here.
#
# The alias keys are static while D35 says sandboxes multiply, because Terraform cannot for_each
# a provider. Unit 2 adds an alias here by hand, the same seam data-governance/data/ carries.
# AWS's own answer for the account-agnostic case is an account pool
# (`datazone create-account-pool`, CLI-only), noted for Stage 14 and not adopted at N=1.

provider "aws" {
  alias   = "sandbox"
  region  = var.region
  profile = var.members["sandbox"].profile
}


# ------------------------------------------------------- the read-only directory provider
#
# Same idiom, resolving a group id rather than an account id (grants.tf). Identity Center is
# delegated to the Identity account (Stage 2 step 5, INV-15), so the identity store cannot be
# read from Data Governance at all and the name -> id lookup has to be taken where the directory
# lives. It creates nothing and carries no default_tags.
#
# The ids are not passed in: a group id is an identifier, and aws/INDEX.md rule 1 keeps those out
# of tracked files. Resolving from the DisplayName on every plan also makes a renamed or deleted
# group a readable plan failure instead of a grant pointing at nothing - the argument the
# sagemaker-prereqs roster guard makes for blueprint names (Lesson 38).
provider "aws" {
  alias   = "identity"
  region  = var.region
  profile = var.identity_profile
}
