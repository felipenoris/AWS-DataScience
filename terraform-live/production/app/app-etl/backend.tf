# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the account's
# state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py <account> app/app-etl   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py <account> app/app-etl        (region, env, the folder, the registry map;
#                                                         --pipeline on the deploy runner)
#   terraform init -backend-config=backend.hcl
#
# The pipeline applies this slice as the account's deploy role (Stage 8 steps 3.2 and 3.6), whose
# state grant names the app/ prefix; a by-hand apply runs as the account's infrastructure profile.

terraform {
  backend "s3" {}
}
