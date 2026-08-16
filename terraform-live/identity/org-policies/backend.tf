# The backend - Stage 2 step 4.
#
# DECLARED FROM THE FIRST `init`, AND THAT IS THE RULE RATHER THAN THE EXCEPTION. Only
# bootstrap/ migrates, because only bootstrap/ has to run before the bucket that holds its own
# state exists (step 2.2). Every other slice in this repository - this one included - declares
# its backend up front and never holds local state at all. There is no migration to perform
# here and nobody should go looking for one.
#
# WHY THE BLOCK IS EMPTY. `backend` cannot interpolate anything - no var, no local - so the
# bucket, the key and the REGION would have to be literals in a .tf file, which
# docs/plan/architecture.md forbids and step 9.1's check rejects. Partial configuration is the
# reconciliation: the literals live in a per-slice backend.hcl, which is generated, is not a
# .tf file and is gitignored.
#
#   ./scripts/gen-tfvars.py      identity org-policies
#   ./scripts/gen-backend-hcl.py identity org-policies
#   terraform init -backend-config=backend.hcl
#
# Both generated files come from scripts/tfhygiene/backend.py - one table, two writers - so
# the region the backend records and the region the provider uses cannot disagree. The state
# lands in the Identity account's own bucket under identity/org-policies/terraform.tfstate,
# beside identity/sso/, sharing the bucket and the account state key: the two slices are
# separated by DELEGATION, not by secrecy (step 5), and neither holds anything the other's
# reader may not see.
#
# WHAT THIS PARTICULAR STATE FILE HOLDS, said out loud because it is not the usual answer: the
# full text of every preventive document in the organization, plus the root and OU ids they are
# attached to. That is not a secret - the documents are tracked in policies/ - but it is a map
# of the ceiling, and it is one more reason the bucket is SSE-KMS under an account-local key
# whose policy is the read control (bootstrap/).

terraform {
  backend "s3" {}
}
