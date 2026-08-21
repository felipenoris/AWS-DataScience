# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py production registry   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production registry        (region, env, the consumer map)
#   terraform init -backend-config=backend.hcl
#
# THE ACCOUNT KEY, NOT D36's. production/bootstrap/ carries two KMS keys (Stage 2 step 3.4):
# alias/awsds-prod-tfstate for everything, and alias/awsds-prod-tfstate-pki for pki/ alone.
# This slice takes the first - nothing in it is a private key, and backend.py's one exception
# is keyed on the slice name `pki`.

terraform {
  backend "s3" {}
}
