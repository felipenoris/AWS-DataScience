# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated
# tfvars, the five mandatory tags as default_tags, CostCenter naming the stage that created
# the resources rather than the stage that happens to be open.
#
# THE WRONG-ACCOUNT GUARD IS THE BACKEND: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal.

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

# ------------------------------------------------------ the read-only lake provider
#
# ONE ALIAS, FOR EXACTLY ONE data.aws_caller_identity READ - the peering.tf / lake-slice idiom:
# it creates nothing, so it carries no default_tags, and the profile arrives from the generated
# tfvars (PROFILES in scripts/tfhygiene/backend.py), never as a literal here.
#
# Why the read exists at all: every resource link and every re-grant in this slice names the
# lake's CATALOG ID, and aws/INDEX.md rule 1 keeps account ids out of tracked files - so the id
# is resolved live from the profile that already names the account. An id pasted here would be
# the exact copy Lesson 3 warns about.

provider "aws" {
  alias   = "lake"
  region  = var.region
  profile = var.lake["data-governance"].profile
}
