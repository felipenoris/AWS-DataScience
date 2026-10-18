# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py production sagemaker   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production sagemaker        (region, env, the lake and reader maps)
#   terraform init -backend-config=backend.hcl
#
# The state is encrypted with the account key, alias/awsds-prod-tfstate: nothing here is a
# private key, and backend.py's one exception is keyed on the slice name `pki`.

terraform {
  backend "s3" {}
}
