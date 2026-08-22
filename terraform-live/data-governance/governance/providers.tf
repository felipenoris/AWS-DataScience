# The provider. Same shape as every slice (Stage 2 step 2.1).
#
# THE WRONG-ACCOUNT GUARD IS THE BACKEND: awsds-data-tfstate exists only in Data Governance
# and admits no cross-account principal. Applied as awsds-infra-data.
#
# THE awscc PROVIDER carries the project profiles: awscc_datazone_project_profile is the only
# Terraform resource for them in either provider (measured against the pinned schemas
# 2026-08-21) - conventions §6 anticipated exactly this split, "domain + IAM through the aws
# provider, project profiles / blueprints / projects through awscc".

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
# TWO ALIASES, EACH FOR EXACTLY ONE data.aws_caller_identity READ - the idiom
# data-governance/data/providers.tf established. They create nothing, carry no default_tags,
# and their profiles arrive from the generated tfvars (SMUS_MEMBERS in
# scripts/tfhygiene/backend.py), never as literals here.
#
# Why the reads exist: each project profile's environment configuration names the ACCOUNT it
# provisions into, and aws/INDEX.md rule 1 keeps account ids out of tracked files.
#
# THE ALIAS KEYS ARE STATIC WHILE D35 SAYS SANDBOXES MULTIPLY - Terraform cannot for_each a
# provider. Unit 2 adds an alias here by hand, which is the same seam data-governance/data/
# already carries; AWS's own answer for the account-agnostic case is an ACCOUNT POOL
# (`datazone create-account-pool`, CLI-only), noted for Stage 14 and deliberately not adopted
# at N=1.

provider "aws" {
  alias   = "sandbox"
  region  = var.region
  profile = var.members["sandbox"].profile
}

provider "aws" {
  alias   = "development"
  region  = var.region
  profile = var.members["development"].profile
}

# ------------------------------------------------------- the read-only directory provider
#
# A THIRD ALIAS, SAME IDIOM, DIFFERENT REASON (2026-08-22, with grants.tf). The two above
# resolve an account id; this one resolves a GROUP id, and it exists because Identity Center
# is delegated to the Identity account (Stage 2 step 5, INV-15): the identity store cannot be
# read from Data Governance at all, so the name -> id lookup has to be taken where the
# directory lives. It creates nothing and carries no default_tags.
#
# WHY NOT PASS THE IDS IN: a group id is an identifier, and aws/INDEX.md rule 1 keeps those out
# of tracked files. Resolving from the DisplayName on every plan also makes a renamed or
# deleted group a readable plan failure instead of a grant pointing at nothing - the same
# argument the sagemaker-prereqs roster guard makes for blueprint names (Lesson 38).
provider "aws" {
  alias   = "identity"
  region  = var.region
  profile = var.identity_profile
}
