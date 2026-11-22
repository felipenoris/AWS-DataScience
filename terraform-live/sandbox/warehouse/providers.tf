# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars,
# the five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The wrong-account guard is the backend: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal. Everything this slice creates is in
# this one account: the namespace, its key, its log groups, its roles and the project roles it
# grants to. D40's other class lives in Production and is applied by production/warehouse/ at
# Stage 9, never from here.

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

# ------------------------------------------- the read-only producer provider (Stage 19 pass 5)
#
# One alias for one data.aws_caller_identity read, the data-governance/data idiom: it creates
# nothing, so it carries no default_tags, and its profile arrives from the generated tfvars
# (`producers`, backend.DATA_PRODUCERS), never as a literal here. The access role's statement for a
# subscribed product names the producer's catalog, and aws/INDEX.md rule 1 keeps account ids out of
# tracked files, so the id is resolved live from the profile that names the account.

provider "aws" {
  alias   = "production"
  region  = var.region
  profile = var.producers["production"].profile
}
