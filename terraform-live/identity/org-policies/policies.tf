# The ten documents - Stage 2 step 5.5, imported and never created.
#
# All ten already exist: written by hand in Stage 1c step 7 and pasted into the Management
# console as `AWS Control Tower Admin`. This stage adopts them. The import ids are emitted by
# ./aws/import-ids.py section 5a and are never typed; the address it suggests is
# `aws_organizations_policy.this["<name>"]`, which is what the for_each below computes.
#
# The apply that follows the import is not a no-op. Two things change on it:
#
#   - Five tags on ten policies. All ten carry none (measured 2026-08-16), and `default_tags`
#     adds the mandatory five. This is the first exercise of step 5.1's third delegation
#     statement, organizations:TagResource.
#   - Four descriptions. Three are empty or absent in AWS and one carries literal double quotes;
#     locals.tf names which. Authoring them here makes the repository the source of truth for an
#     attribute no tracked file held before.
#
# What must not change is `content` and `type`.

resource "aws_organizations_policy" "this" {
  for_each = local.policy_documents

  name        = each.key
  description = local.policy_descriptions[each.key]
  type        = local.policy_types[each.key]
  content     = each.value

  lifecycle {
    # The guard is against a replace more than against a destroy. `type` is ForceNew: a wrong
    # entry in locals.tf's type map plans a destroy and a create on a document attached to the
    # organization root, and for the width of that apply the ceiling is not there. With this set
    # the plan errors instead. Step 5.5a(iii)'s other named failure - an import under a key the
    # configuration does not compute - lands the same way: the orphan in state is a destroy, so
    # it stops rather than proposing.
    #
    # The price: retiring a document is a two-commit operation. Remove this block, apply, then
    # remove the document. The state buckets carry the same friction
    # (docs/plan/conventions.md §5.1 rule 1).
    prevent_destroy = true

    # Every write in this slice depends on the Organizations delegation of step 5.1, granted to
    # the `InfrastructureAccess` role in the Identity account and to nothing else. Run this from
    # another account and the failure is an AccessDenied on CreatePolicy or AttachPolicy, which
    # reads like the delegation is wrong and sends somebody to re-read a resource policy that is
    # fine. The condition compares the caller against the account this configuration resolves, so
    # nothing is hardcoded and no id enters a tracked file.
    precondition {
      condition     = data.aws_caller_identity.current.account_id == local.identity_account_id
      error_message = "This slice is applied from the Identity account and this session is somewhere else. Use AWS_PROFILE=awsds-infra-identity (the infrastructure user, Identity account, InfrastructureAccess) - and check it with `aws sts get-caller-identity` before, not after."
    }

    # An unsubstituted placeholder parses as JSON and attaches cleanly, and the deny it guards
    # then compares against the literal string `<ORG_ID>` and never fires (Lesson 5). render.py
    # refuses to write one; this refuses to apply one.
    precondition {
      condition     = length(local.survivors[each.key]) == 0
      error_message = "${each.key} still contains an unsubstituted <PLACEHOLDER> after rendering. locals.tf substitutes the same five tokens render.py does - a new one in the template needs a line in both."
    }

    # Step 5.2's "count before writing", against the tighter of the two Organizations limits.
    # var.policy_max_bytes explains why 5 120 and not 10 240.
    precondition {
      condition     = length(each.value) <= var.policy_max_bytes
      error_message = "${each.key} is ${length(each.value)} characters minified, over the ${var.policy_max_bytes} this slice enforces. Split the document or move a statement - an RCP node also has a limit of 5 documents, so splitting is not free."
    }

    # The repository-integrity checks. They are preconditions rather than a script because a
    # check that ran yesterday is not a precondition. They do not depend on `each`, so a failure
    # prints once per instance - ten identical messages, taken over a silent pass.
    precondition {
      condition     = length(local.unmapped_documents) == 0
      error_message = "policies/ holds ${join(", ", local.unmapped_documents)}, which attachments.json never attaches. A document nobody attached is a control nobody has (Lesson 5). Attach it in the map, or delete the file."
    }

    precondition {
      condition     = length(local.types_missing) == 0 && length(local.types_extra) == 0
      error_message = "locals.tf's policy_types has drifted from the document set - missing: ${join(", ", local.types_missing)}; stale: ${join(", ", local.types_extra)}. `type` is ForceNew, so a wrong or absent entry is a replace on an attached document."
    }

    precondition {
      condition     = length(local.descriptions_missing) == 0 && length(local.descriptions_extra) == 0
      error_message = "locals.tf's policy_descriptions has drifted from the document set - missing: ${join(", ", local.descriptions_missing)}; stale: ${join(", ", local.descriptions_extra)}."
    }
  }
}
