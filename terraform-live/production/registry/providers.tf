# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags.
#
# CostCenter is stage-06 while the slice is Stage 7's. The convention names the stage that created
# the resources, and these are created at Stage 6 pass 0 - Stage 6 step 5.0 has nowhere to push
# otherwise. Stage 7's 5.b additions (the pull-through cache, the per-application repositories)
# land in the same slice and inherit this default, so the supply chain reads as one line on the
# bill.
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

# ------------------------------------------------- the read-only consumer providers
#
# Two aliases, each for exactly one data.aws_caller_identity read, following the idiom in
# data-governance/data/providers.tf: they create nothing, so they carry no default_tags, and the
# profiles arrive from the generated tfvars (REGISTRY_CONSUMERS in scripts/tfhygiene/backend.py),
# never as literals here.
#
# Every policy in this slice enumerates consumer accounts - the ECR repository policies, the
# CodeArtifact domain and repository policies, and the key policy - and aws/INDEX.md rule 1 keeps
# account ids out of tracked files (Lesson 3).
#
# The alias keys are static while D35 says sandboxes multiply. Terraform cannot for_each a
# provider, so unit 2 adds an alias here by hand - the same seam data-governance/data/ carries, and
# this file joins Stage 14's edit list by construction.

provider "aws" {
  alias   = "sandbox"
  region  = var.region
  profile = var.consumers["sandbox"].profile
}

provider "aws" {
  alias   = "staging"
  region  = var.region
  profile = var.consumers["staging"].profile
}
