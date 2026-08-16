# The backend - partial configuration (Stage 2 step 2.5), live from the first init: the
# state bucket exists (bootstrap/ made it), so there is no two-phase dance. The STATE is
# [P] even though every resource here is [E] - `make down` empties it, never deletes it.
#
#   ./scripts/gen-backend-hcl.py production egress   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production egress        (region, env, tag, zone_ids, account_folder)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
