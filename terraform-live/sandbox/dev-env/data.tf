# What this slice reads and does not own.
#
# One read, and it crosses an account boundary: production/registry/'s outputs carry the two
# repository ARNs the image role's statement names. An ARN copied by hand would put the registry
# account's id into a tracked file (aws/INDEX.md rule 1) and would go stale silently the day a
# repository is renamed (Lesson 48).
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
