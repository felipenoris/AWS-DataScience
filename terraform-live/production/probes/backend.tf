# The backend - partial configuration (Stage 2 step 2.5), live from the first init. The
# STATE is [P] even though every resource here is [E]: `make down` empties it, never deletes
# it, and an empty state is what proves the probes are gone.
#
#   ./scripts/gen-backend-hcl.py production probes   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production probes        (region, env, tag, zone_ids, account_folder, peer_cidrs)
#   terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {}
}
