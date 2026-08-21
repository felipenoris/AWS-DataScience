# The backend - partial configuration (Stage 2 step 2.5).
#
#   ./scripts/gen-backend-hcl.py data-governance governance
#   ./scripts/gen-tfvars.py data-governance governance
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
