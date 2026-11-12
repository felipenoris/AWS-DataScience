# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the account's
# state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py staging chains   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py staging chains        (region, env, the folder)
#   terraform init -backend-config=backend.hcl
#
# Applied by the infrastructure user, as awsds-infra-staging: no pipeline job applies this slice.

terraform {
  backend "s3" {}
}
