# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py sandbox warehouse-compute   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py sandbox warehouse-compute (region, env, environment_tag, account_folder, zone_ids)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
