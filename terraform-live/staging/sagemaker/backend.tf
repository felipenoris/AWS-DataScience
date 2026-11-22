# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice (6b step 4.2).
#
#   ./scripts/gen-backend-hcl.py staging sagemaker   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py staging sagemaker        (region, env, the registry map)
#   terraform init -backend-config=backend.hcl
#
# The state is encrypted with the account key, alias/awsds-staging-tfstate.

terraform {
  backend "s3" {}
}
