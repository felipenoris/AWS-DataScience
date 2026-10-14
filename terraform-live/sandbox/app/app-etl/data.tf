# What this slice reads and does not own: this account's network and data key, the outputs bucket
# sandbox/data/ holds, and the application repository in the registry account. Each state key is built
# from the account folder, which no .tf file re-derives from the env token (Lesson 14).

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "data" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/data/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "registry" {
  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.registry : v.env])}-tfstate"
    key     = "production/registry/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.registry : v.profile])
  }
}

# The S3 gateway endpoint's prefix list, the one destination the job's security group admits besides
# the VPC's own interface endpoints: with networking off, the platform still moves a job's outputs to S3
# through the job's interfaces.
data "aws_vpc_endpoint" "s3" {
  id = data.terraform_remote_state.foundation.outputs.s3_gateway_endpoint_id
}
