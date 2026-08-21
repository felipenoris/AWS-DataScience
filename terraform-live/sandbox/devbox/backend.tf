# The backend - partial configuration (Stage 2 step 2.5), live from the first init. The
# STATE is [P] even though every resource here is [E]: `./scripts/devbox.py down` empties it,
# never deletes it, and an empty state is what proves the host is gone.
#
#   ./scripts/gen-backend-hcl.py sandbox devbox   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py sandbox devbox        (region, env, tag, zone_ids, account_folder)
#   terraform init -backend-config=backend.hcl
#
# All three are what ./scripts/devbox.py does for you; they are written out here because a
# slice that can only be applied through a script is a slice nobody can debug.

terraform {
  backend "s3" {}
}
