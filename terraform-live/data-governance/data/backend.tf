# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since data-governance/bootstrap/.
#
#   ./scripts/gen-backend-hcl.py data-governance data   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py data-governance data        (region, env, tag, consumer maps)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
