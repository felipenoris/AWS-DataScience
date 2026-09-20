# The provider. Same shape as every slice (Stage 2 step 2.1): region from the generated tfvars,
# the five mandatory tags as default_tags, CostCenter naming the stage that created the resources.
#
# The wrong-account guard is the backend: this slice's state lives in this account's own
# awsds-<env>-tfstate, which admits no cross-account principal. There is no aliased provider and
# nothing here is cross-account - the namespace, its key, its log groups, its role and the project
# roles it grants to are all in this one account. D40's other class lives in Production and is
# applied by production/warehouse/ at Stage 9, never from here.

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
