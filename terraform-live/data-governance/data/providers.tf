# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags. CostCenter is stage-05 - the Stage 4 log
# recorded what a wrong slice-level default costs (four resources tagged stage-03 while being
# Stage 4's), so this slice starts with its own.
#
# THE WRONG-ACCOUNT GUARD IS THE BACKEND: awsds-data-tfstate exists only in Data Governance
# and admits no cross-account principal. Applied as awsds-infra-data.

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

# --------------------------------------------------- the read-only peer providers
#
# THREE ALIASES, EACH FOR EXACTLY ONE data.aws_caller_identity READ - the peering.tf idiom:
# they create nothing, so they carry no default_tags, and the profiles arrive from the
# generated tfvars (PROFILES in scripts/tfhygiene/backend.py), never as literals here.
#
# Why the reads exist at all: the drop-box statements and the zn-lab key policy name
# cross-account principals, and aws/INDEX.md rule 1 keeps account ids out of tracked files -
# so each id is resolved live from the profile that already names the account. An id pasted
# here would be the exact copy Lesson 3 warns about.
#
# THE ALIAS KEYS ARE STATIC ("sandbox", "development", "production") WHILE D35 SAYS CONSUMERS
# MULTIPLY. Terraform cannot for_each a provider, so unit 2 adds an alias here by hand - the
# same seam Stage 14's sandbox-unit module already owns on the consumer side; this file is on
# that stage's edit list by construction.

provider "aws" {
  alias   = "sandbox"
  region  = var.region
  profile = var.consumers["sandbox"].profile
}

provider "aws" {
  alias   = "development"
  region  = var.region
  profile = var.consumers["development"].profile
}

provider "aws" {
  alias   = "production"
  region  = var.region
  profile = var.producers["production"].profile
}
