# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py staging data   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py staging data        (region, env, the lake map, the account folder)
#   terraform init -backend-config=backend.hcl
#
# The state is encrypted with the account key, alias/awsds-staging-tfstate.

terraform {
  backend "s3" {}
}
