# The ten documents - Stage 2 step 5.5, imported and never created.
#
# EVERY ONE OF THESE ALREADY EXISTS. They were written by hand in Stage 1c step 7 and pasted
# into the Management console as `AWS Control Tower Admin`; this stage adopts them. The import
# ids are emitted by ./aws/import-ids.py section 5a and are never typed - and the address it
# suggests is `aws_organizations_policy.this["<name>"]`, which is what the for_each below
# computes.
#
# THE APPLY THAT FOLLOWS THE IMPORT IS NOT A NO-OP, and pretending otherwise would make step
# 5.5's gate unreadable. Two things change on it, both predicted here rather than discovered:
#
#   - FIVE TAGS ON TEN POLICIES. All ten carry none today (measured 2026-08-16), and
#     `default_tags` adds the mandatory five. This is the first exercise of step 5.1's third
#     delegation statement, organizations:TagResource.
#   - FOUR DESCRIPTIONS. Three are empty or absent in AWS and one carries literal double
#     quotes; locals.tf names which, and authoring them here is the decision that the
#     repository is the source of truth for an attribute no tracked file held before.
#
# What must NOT change is `content` and `type`. That is the half of the plan to read.

resource "aws_organizations_policy" "this" {
  for_each = local.policy_documents

  name        = each.key
  description = local.policy_descriptions[each.key]
  type        = local.policy_types[each.key]
  content     = each.value

  lifecycle {
    # THE GUARD IS AGAINST A REPLACE, NOT REALLY AGAINST A DESTROY - and that is worth being
    # precise about, because the obvious reading undersells it. `type` is ForceNew: a wrong
    # entry in locals.tf's type map plans a destroy and a create on a document that is attached
    # to the organization root, and for the width of that apply the ceiling is not there. With
    # this set the plan ERRORS instead. Step 5.5a(iii)'s other named failure - an import under a
    # key the configuration does not compute - lands the same way: the orphan in state is a
    # destroy, so it stops rather than proposing.
    #
    # THE PRICE, so nobody is surprised by it: retiring a document is now a two-commit
    # operation. Remove this block, apply, then remove the document. That friction is the same
    # one the state buckets carry (docs/plan/conventions.md §5.1 rule 1) and it is deliberate.
    prevent_destroy = true

    # THE PROFILE, NAMED BEFORE THE API COMPLAINS ABOUT SOMETHING ELSE. Every write in this
    # slice depends on the Organizations delegation of step 5.1, which is granted to the
    # `InfrastructureAccess` ROLE IN THE IDENTITY ACCOUNT and to nothing else. Run this from
    # another account and the failure is an AccessDenied on CreatePolicy or AttachPolicy - which
    # reads like the delegation is wrong, and sends somebody to re-read a resource policy that
    # is fine. It compares the caller against the account this configuration itself resolves, so
    # nothing is hardcoded and no id enters a tracked file.
    precondition {
      condition     = data.aws_caller_identity.current.account_id == local.identity_account_id
      error_message = "This slice is applied from the Identity account and this session is somewhere else. Use AWS_PROFILE=awsds-infra-identity (the infrastructure user, Identity account, InfrastructureAccess) - and check it with `aws sts get-caller-identity` before, not after."
    }

    # An unsubstituted placeholder parses as JSON and attaches cleanly, and the deny it guards
    # then compares against the literal string `<ORG_ID>` and never fires. render.py refuses to
    # write one; this refuses to apply one. Lesson 5, in the substitution rather than in the
    # policy.
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

    # THE THREE REPOSITORY-INTEGRITY CHECKS, and they are here rather than in a script because a
    # check that ran yesterday is not a precondition. They do not depend on `each`, so a failure
    # prints once per instance - ten identical messages, which is noisy and unmistakable, and
    # the trade this file takes over a silent pass.
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
