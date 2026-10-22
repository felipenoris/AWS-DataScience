# What this slice reads and does not own, each state key built from the account folder (Lesson 14):
# sagemaker/'s job role and Glue connection (Stage 9 decision 12 (a)), data/'s outputs bucket, and
# production/registry/'s application repository, read through the profile the registry map names.
# The deploy role's state_read_keys name the first two (foundation/'s deploy-role files); the runner's
# own role reads the registry's state (decision 14).

data "terraform_remote_state" "sagemaker" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/sagemaker/terraform.tfstate"
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
    key     = "${one(keys(var.registry))}/registry/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.registry : v.profile])
  }
}
