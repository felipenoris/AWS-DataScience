# The backend - partial configuration (Stage 2 step 2.5). The state key is sandbox/app/app-etl/, under
# this account's own awsds-<env>-tfstate.
#
#   ./scripts/gen-backend-hcl.py sandbox app/app-etl   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py sandbox app/app-etl        (region, env, the folder, the registry map)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
