# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# account's state bucket exists since its bootstrap/ slice.
#
#   ./scripts/gen-backend-hcl.py <account> workflows   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py <account> workflows        (region, env, environment_tag, deploy_role_name, deploy_runner)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
