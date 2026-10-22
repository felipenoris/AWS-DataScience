# What this slice reads and does not own.
#
#   1. this account's identity and partition -> every ARN this slice builds
#   2. the lake's identity (aliased)          -> the catalog id the resource links and regrants address
#   3. data-governance/data/'s state          -> the shared database names
#   4. the jobs' VPC slice                    -> the [P] S3 gateway endpoint the outputs bucket trusts
#   5. two reserved SSO roles, by pattern     -> the data lake administrator and the persona
#
# The job role, the debug role, the deploy role and Stage 10's roles are named by their contract names
# and matched by aws:PrincipalArn, never read from a state: a policy naming a role through
# aws:PrincipalArn validates nothing, so it can be written before the role exists, and survives the
# role's re-creation under the same name (Stage 8 2.4's lesson).

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_caller_identity" "lake" {
  provider = aws.lake
}

data "terraform_remote_state" "lake" {
  backend = "s3"

  config = {
    bucket  = "awsds-${var.lake["data-governance"].env}-tfstate"
    key     = "data-governance/data/terraform.tfstate"
    region  = var.region
    profile = var.lake["data-governance"].profile
  }
}

data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/${var.vpc_slice}/terraform.tfstate"
    region = var.region
  }
}

# The AWSReservedSSO_* suffix is minted per account (1c decision 7), so both ARNs are matched by
# pattern; one() in locals.tf fails on zero and on two.
data "aws_iam_roles" "infrastructure_access" {
  name_regex  = "AWSReservedSSO_InfrastructureAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

data "aws_iam_roles" "data_scientist" {
  name_regex  = "AWSReservedSSO_DataScientistProdAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
