# What this slice reads and does not own.
#
#   1. this account's VPC slice       the VPC and the private subnets the blueprint configuration
#                                     is pointed at: foundation/ in Staging, workloads/ in
#                                     Production, where foundation/ is VPC-SharedServices (the
#                                     generated `vpc_slice`)
#   2. the lake's data/               the registered bucket ARNs, the drop-box prefix and the lake
#                                     data key, which the D13 boundary is built from
#   3. the domain's governance/       once the blueprints are enabled: the domain id, the domain
#                                     execution role ARN and the root domain unit id. count-gated,
#                                     so the prerequisites plan with no read of the domain account
#   4. this account                   its id and partition, for the ARN patterns of the workflows
#                                     grant, and each project role it attaches to: a role that does
#                                     not exist fails at plan, naming it
#
# The second and third cross an account boundary; their profiles arrive keyed by account folder
# from the generated tfvars, never as a literal (Lesson 14).

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/${var.vpc_slice}/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "lake" {
  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.lake : v.env])}-tfstate"
    key     = "data-governance/data/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.lake : v.profile])
  }
}

data "terraform_remote_state" "governance" {
  count = var.blueprints_enabled ? 1 : 0

  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.domain : v.env])}-tfstate"
    key     = "data-governance/governance/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.domain : v.profile])
  }
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_iam_role" "project" {
  for_each = toset(var.project_roles)
  name     = each.value
}
