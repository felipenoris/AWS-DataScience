# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py <account> data   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py <account> data        (region, env, the lake map)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
