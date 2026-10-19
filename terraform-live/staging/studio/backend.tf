# The backend - partial configuration (Stage 2 step 2.5).
#
#   ./scripts/gen-backend-hcl.py staging studio
#   ./scripts/gen-tfvars.py staging studio
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
