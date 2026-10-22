# What this slice reads and does not own.
#
#   1. this account's identity and partition -> every ARN this slice builds
#   2. production/registry/'s state           -> the application repository the job role pulls,
#                                                cross-account (Stage 8 step 3.0's pull grant
#                                                admits this account on the repository's side)
#
# Nothing is read from staging/data/: its buckets and its key name this slice's job role, so the
# role is applied first (step 4.5, as Production's pass 1 preceded its pass 3), and the bucket and
# alias names in locals.tf are the contracts ./aws/deploytargets.py reads. Nothing is read from the
# lake's state: the role reaches the lake through Lake Formation alone, by the read share decision 3
# gives this account.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# Cross-account, so the profile rides in the config, the idiom of sandbox/dev-env/. The state key is
# built from the registry map's one key, the registry account's folder (REGISTRY_HOME in
# scripts/tfhygiene/backend.py), never from a literal here.
data "terraform_remote_state" "registry" {
  backend = "s3"

  config = {
    bucket  = "awsds-${one([for k, v in var.registry : v.env])}-tfstate"
    key     = "${one(keys(var.registry))}/registry/terraform.tfstate"
    region  = var.region
    profile = one([for k, v in var.registry : v.profile])
  }
}
