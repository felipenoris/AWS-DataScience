# The backend - partial configuration (Stage 2 step 2.5), live from the first init. The state is
# [P] even though every resource here is [E]: `./scripts/buildbox.py down` empties it, never
# deletes it, and an empty state is what proves the host is gone.
#
#   ./scripts/gen-backend-hcl.py production buildbox   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production buildbox        (region, env, tag, zone_ids, account_folder)
#   terraform init -backend-config=backend.hcl
#
# ./scripts/buildbox.py runs all three. They are written out here so the slice can also be applied
# and debugged by hand.

terraform {
  backend "s3" {}
}
