# What this slice reads and does not own.
#
# One read, and it crosses an account boundary: production/registry/'s outputs carry the dev-env
# repository URL the image version is built from and the two repository ARNs the image role's
# statement names. An image URI copied by hand would put the registry account's id into a tracked
# file (aws/INDEX.md rule 1) and would go stale silently the day a repository is renamed
# (Lesson 48).
#
# What this slice does NOT read is sandbox/egress/'s generated NO_PROXY, and the reason is measured
# rather than chosen - see main.tf, "The environment this configuration cannot carry".

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "registry" {
  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.registry : v.env])}-tfstate"
    key     = "production/registry/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.registry : v.profile])
  }
}

locals {
  # The image URI, assembled rather than pasted. The repository is tag-immutable, so this string
  # names one digest.
  base_image = "${data.terraform_remote_state.registry.outputs.ecr_dev_env_repository_url}:${var.image_tag}"
}
