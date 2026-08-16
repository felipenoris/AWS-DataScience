# The backend - partial configuration (Stage 2 step 2.5), live from the first init: unlike
# bootstrap/, this slice's state bucket already exists, so there is no two-phase dance.
#
#   ./scripts/gen-backend-hcl.py sandbox foundation   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py sandbox foundation        (region, env, tag, vpc_cidr, zone_ids)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
