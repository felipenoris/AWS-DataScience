# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the account's
# state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py staging orchestration   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py staging orchestration        (region, env, the folder, the zone ids)
#   terraform init -backend-config=backend.hcl
#
# The pipeline applies this slice as awsds-deploy-staging (Stage 10 step 1.5, INT-14), whose state
# grant names this prefix; a by-hand apply runs as awsds-infra-staging.

terraform {
  backend "s3" {}
}
