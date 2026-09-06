# The backend, in a file of its own - Stage 2 steps 2.2, 2.5 and 3.5.
#
# WHY A SEPARATE FILE FOR THREE LINES. EVERY bootstrap/ slice creates the bucket that will hold
# its own state, so every one of them applies once with LOCAL state and then migrates (2.2).
# While that is pending the block cannot be declared - and a block commented out inside
# providers.tf would make providers.tf differ between a migrated slice and a fresh one, which
# is precisely the file step 3.5's parity check compares across the five bootstrap slices.
# Isolated here, the transition is ONE file with two known forms and the other five are
# byte-identical.
#
# THE TWO PHASES, and this file is the whole of the transition:
#
#   1. ./scripts/gen-tfvars.py <account> bootstrap
#      terraform init                                   (block still commented - local state)
#      terraform apply                                  (creates the key and the bucket)
#   2. uncomment the block below
#      ./scripts/gen-backend-hcl.py <account> bootstrap  (writes the untracked backend.hcl)
#      terraform init -backend-config=backend.hcl -migrate-state
#      rm -f terraform.tfstate terraform.tfstate.backup  (they carry account ids and ARNs;
#                                                         .gitignore covers them, deleting
#                                                         them is what makes that moot)
#
# Every OTHER slice in this repository declares its backend from the first `init` and never
# holds local state at all (step 4) - there is no migration to perform anywhere else.
#
# WHY THE BLOCK IS EMPTY. `backend` cannot interpolate anything - no var, no local - so the
# bucket, the key and the REGION would have to be literals in a .tf file, which
# docs/plan/architecture.md forbids and step 9.1's check rejects. Partial configuration is the
# reconciliation: the literals live in a per-slice backend.hcl, which is generated, is not a
# .tf file and is gitignored.

# terraform {
#   backend "s3" {}
# }
