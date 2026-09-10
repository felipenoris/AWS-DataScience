# The backend - Stage 2 step 4.
#
# Declared from the first `init`. Only bootstrap/ migrates, because only bootstrap/ has to run
# before the bucket that holds its own state exists (step 2.2). Every other slice, this one
# included, declares its backend up front and never holds local state.
#
# The block is empty because `backend` cannot interpolate anything - no var, no local - so the
# bucket, the key and the region would have to be literals in a .tf file, which
# docs/plan/architecture.md forbids and step 9.1's check rejects. Partial configuration is the
# reconciliation: the literals live in a per-slice backend.hcl, which is generated, is not a
# .tf file and is gitignored.
#
#   ./scripts/gen-tfvars.py      identity sso
#   ./scripts/gen-backend-hcl.py identity sso
#   terraform init -backend-config=backend.hcl
#
# Both generated files come from scripts/tfhygiene/backend.py - one table, two writers - so
# the region the backend records and the region the provider uses cannot disagree. The state
# lands in the Identity account's own bucket under identity/sso/terraform.tfstate, beside
# identity/org-policies/, sharing the bucket and the account state key: the two slices are
# separated by delegation, not by secrecy (step 5), and neither holds anything the other's
# reader may not see.

terraform {
  backend "s3" {}
}
