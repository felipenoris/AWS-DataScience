# The backend - partial configuration (Stage 2 step 2.5).
#
#   ./scripts/gen-backend-hcl.py <account> sagemaker
#   ./scripts/gen-tfvars.py <account> sagemaker
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
