# The backend - partial configuration (Stage 2 step 2.5), live from the first init. The state is
# [P] even though every resource here is [E]: `make gitlab-down` empties it, never deletes it, and
# an empty state is what proves the runner is gone.
#
#   ./scripts/gen-backend-hcl.py production runners   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production runners        (region, env, tag, zone_ids, account_folder)
#   terraform init -backend-config=backend.hcl
#
# `make gitlab-up` runs all three (scripts/slices.py). They are written out here so the slice can
# also be planned by hand.

terraform {
  backend "s3" {}
}
