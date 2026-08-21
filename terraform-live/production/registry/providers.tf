# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags.
#
# CostCenter IS stage-06, AND THE SLICE IS STAGE 7's. The convention names the stage that
# CREATED the resources rather than the one that designed them or the one that happens to be
# open (Stage 4's log recorded what the other reading costs), and these are created at Stage 6
# pass 0 - Stage 6 step 5.0 has nowhere to push otherwise. Stage 7's 5.b additions (the
# pull-through cache, the per-application repositories) land in the same slice and inherit
# this default deliberately: one slice, one cost centre, so the supply chain reads as one line
# on the bill instead of two halves nobody adds up.
#
# THE WRONG-ACCOUNT GUARD IS THE BACKEND: awsds-prod-tfstate exists only in Production and
# admits no cross-account principal. Applied as awsds-infra-prod.

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

# ------------------------------------------------- the read-only consumer providers
#
# TWO ALIASES, EACH FOR EXACTLY ONE data.aws_caller_identity READ - the idiom
# data-governance/data/providers.tf established: they create nothing, so they carry no
# default_tags, and the profiles arrive from the generated tfvars (REGISTRY_CONSUMERS in
# scripts/tfhygiene/backend.py), never as literals here.
#
# Why the reads exist at all: every policy in this slice enumerates consumer ACCOUNTS - the
# ECR repository policies, the CodeArtifact domain and repository policies, and the key policy
# - and aws/INDEX.md rule 1 keeps account ids out of tracked files. An id pasted here would be
# the copy Lesson 3 warns about.
#
# THE ALIAS KEYS ARE STATIC WHILE D35 SAYS SANDBOXES MULTIPLY. Terraform cannot for_each a
# provider, so unit 2 adds an alias here by hand - the same seam data-governance/data/ carries,
# and this file joins Stage 14's edit list by construction.

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
