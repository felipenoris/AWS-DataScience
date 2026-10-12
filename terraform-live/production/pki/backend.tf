# The backend - partial configuration (Stage 2 step 2.5), under D36's SECOND key.
#
#   ./scripts/gen-backend-hcl.py production pki   (writes the untracked backend.hcl; its kms_key_id
#                                                  is alias/awsds-prod-tfstate-pki, the one slice
#                                                  scripts/tfhygiene/backend.py keys on by name)
#   ./scripts/gen-tfvars.py production pki        (region, env, tag, account_folder)
#   terraform init -backend-config=backend.hcl
#
# This state file holds the internal CA's root private key, so "who can read Production state" and
# "who can mint a certificate for any internal name" must stay two questions: the key was created by
# production/bootstrap/ on 2026-08-15 (pki-key.tf) and has encrypted nothing until this slice's
# first apply. Never destroyed: layers.NEVER_DESTROY refuses it whatever its layer says.

terraform {
  backend "s3" {}
}
