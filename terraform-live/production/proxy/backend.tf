# The backend - partial configuration (Stage 2 step 2.5), live from the first init.
#
#   ./scripts/gen-backend-hcl.py production proxy   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production proxy        (region, env, tag, zone_ids, account_folder,
#                                                    rfc1918_cidrs)
#   terraform init -backend-config=backend.hcl
#
# NO HAND-WRITTEN TFVARS HERE, and the difference from vpn/ beside it is worth one line: this
# host holds no roster and no key. Its whole configuration - the allow-lists - is [P] data in an
# SSM parameter that networking/ owns, rendered at boot and re-rendered on a schedule, so there
# is nothing about it that a person edits in this directory.

terraform {
  backend "s3" {}
}
