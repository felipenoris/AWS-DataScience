# The ten attachments - Stage 2 step 5.5, and they are separate objects from the documents.
#
# "THE WHOLE org-policies/ SET" GLOSSES OVER THIS AND IT IS THE EXPENSIVE HALF. An attachment is
# its own resource with its own import (`<target_id>:<policy_id>`), and a document that is
# imported while its attachment is not passes the empty-plan gate in silence: Terraform holds a
# policy, the organization holds a policy attached to the root, and nothing in the plan mentions
# the attachment because nothing declared it. That is why the deliverable names attachments
# explicitly and why ./aws/import-ids.py section 5b emits one line per pair.
#
# SIX TO THE ROOT, FOUR TO AN OU. The root six are the reason step 5.0 had to run first: a
# delegated administrator that could not manage a root attachment would have left most of this
# file console-managed (INT-20, answered - all three readings succeeded).

resource "aws_organizations_policy_attachment" "this" {
  for_each = local.attachment_pairs

  policy_id = aws_organizations_policy.this[each.value.document].id
  target_id = each.value.target_id

  lifecycle {
    # THIS IS WHERE prevent_destroy ACTUALLY BITES, and the policies.tf copy is the weaker of
    # the two. Organizations refuses to delete an attached policy, so a `terraform destroy`
    # would detach all ten FIRST and only then fail on the documents - taking the ceiling down
    # on the way to an error. Guarding the attachment is what stops that at the plan.
    #
    # It also converts step 5.5a(iii)'s named failure into a hard stop. An attachment imported
    # under a key this configuration does not compute is an orphan: the plan proposes a create
    # for the right key and a DESTROY for the orphan, and "a wrong key does not error" stops
    # being true.
    #
    # THE PRICE: removing an attachment from attachments.json now fails the apply until this
    # block is removed and put back. Detaching a preventive control deliberately is exactly the
    # operation that should cost two commits.
    prevent_destroy = true
  }
}
