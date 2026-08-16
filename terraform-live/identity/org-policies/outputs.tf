# What this slice reports - Stage 2 step 5.
#
# NO IDENTIFIER IS PRINTED HERE - not an account id, not the organization id, not a root or OU
# id, and not a policy id. An output is echoed on every apply and pasted into logs and chat
# windows afterwards (aws/INDEX.md rule 1), and this slice holds the whole set: the state file
# carries the organization id, the root id, every OU id it resolved and the id of all ten
# policies.
#
# THE POLICY IDS ARE THE ONE OMISSION WORTH JUSTIFYING, because they are genuinely useful - the
# detach command is the entire recovery path and it needs one. They live in two places already:
# `docs/log/log-stage-01c-preventive-policies.md`, recorded as each was attached, and
# `./aws/import-ids.py`, which regenerates them from the organization into untracked
# aws/output/. A third copy that appears on every apply is the one that gets pasted somewhere
# it should not.

output "policy_types" {
  description = "Each document and the policy type it is imported as. Printed because it is the attribute with no home in a tracked file and the one whose drift is a ForceNew replace - a reader can check all four types are represented without opening locals.tf."
  value       = local.policy_types
}

output "policy_document_bytes" {
  description = <<-EOT
    The minified size of each document, against the ceiling in var.policy_max_bytes.

    IT IS AN OUTPUT RATHER THAN A COMMENT BECAUSE THE NUMBER MOVES. Stage 6 and Stage 9 both
    come back to awsds-org-scp-perimeter.json, and every stage that adds a deny adds characters;
    the precondition in policies.tf is what FAILS, and this is what lets somebody watch the
    margin shrink before it does. Measured 2026-08-16: 201 characters at the smallest and 1 651
    at the largest, against 5 120.
  EOT
  value       = { for name, content in local.policy_documents : name => length(content) }
}

output "attachment_targets" {
  description = "Every managed attachment, by for_each key, and the target it names - `root` or an OU NAME, never an id. This is the map read back from what the configuration actually computed, which is the thing to compare against ./aws/import-ids.py section 5b before importing: a key that differs here is the failure step 5.5a(iii) names."
  value       = { for key, pair in local.attachment_pairs : key => pair.target }
}

output "attachment_count" {
  description = "How many attachments this slice manages, root and per-OU apart. Measured 2026-08-16 from what is attached: 6 on the organization root, 4 on an OU. The root six are why step 5.0 had to answer INT-20 before this slice could be written at all."
  value = {
    root = length([for pair in local.attachment_pairs : pair if pair.target == "root"])
    ou   = length([for pair in local.attachment_pairs : pair if pair.target != "root"])
  }
}
