# The backend - partial configuration (Stage 2 step 2.5).
#
#   ./scripts/gen-backend-hcl.py data-governance publishing
#   ./scripts/gen-tfvars.py data-governance publishing
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
