# The backend, in a file of its own - Stage 2 steps 2.2, 2.5 and 3.5.
#
# A separate file for three lines, because every bootstrap/ slice creates the bucket that will hold
# its own state: each applies once with local state and then migrates (2.2). While that is pending
# the block cannot be declared, and a block commented out inside providers.tf would make
# providers.tf differ between a migrated slice and a fresh one - the file step 3.5's parity check
# compares across the five bootstrap slices. Isolated here, the transition is one file with two
# known forms and the others stay byte-identical.
#
# The two phases, which this file is the whole of:
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
# Every other slice declares its backend from the first `init` and never holds local state at all
# (step 4), so there is no migration to perform anywhere else.
#
# The block is empty because `backend` cannot interpolate anything, no var and no local, so the
# bucket, the key and the region would have to be literals in a .tf file - which
# docs/plan/architecture.md forbids and step 9.1's check rejects. Partial configuration is the
# reconciliation: the literals live in a per-slice backend.hcl, generated, not a .tf file, and
# gitignored.

terraform {
  backend "s3" {}
}
