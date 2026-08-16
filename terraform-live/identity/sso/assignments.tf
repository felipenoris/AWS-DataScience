# The group -> account assignments - Stage 2 step 5.3.
#
# ENUMERATED, WHICH IS HALF OF D34's RULE AND THE HALF THIS SLICE OWNS. "The floor is
# discovered, the grants are enumerated": org-policies/ buys coverage from the attachment
# point, and this file writes every grant out one by one - because an account acquiring
# DataScientistAccess by simply existing is the exact failure the design exists to prevent.
#
# A for_each OVER A HUMAN-AUTHORED MAP IS STILL ENUMERATION (docs/plan/conventions.md, the D35
# note). What the rule forbids is a for_each over a DATA SOURCE - an assignment keyed on
# data.aws_organizations_organization.accounts grants by discovery. The map is in locals.tf,
# every row was typed by somebody, and the data source appears only to turn one of those typed
# names into the id the API requires.
#
# THE PRINCIPAL IS A GROUP, NEVER A USER (conventions): a group assignment is one object no
# matter how many people are in it, and a user assignment is one per person, created one API
# call at a time. The single exception in the whole organization is Account Factory's direct
# assignment to the infrastructure user (D32), which is documented in infrastructure-access.tf
# and deliberately not modelled.

resource "aws_ssoadmin_account_assignment" "persona" {
  for_each = local.assignments

  instance_arn       = local.instance_arn
  permission_set_arn = local.permission_set_arns[each.value.set]

  principal_id   = local.group_ids[each.value.group]
  principal_type = "GROUP"

  target_id   = local.account_ids[each.value.account]
  target_type = "AWS_ACCOUNT"

  lifecycle {
    # THE NAME THAT DID NOT RESOLVE, NAMED. locals.account_ids yields null when no ACTIVE
    # account carries the written name, and null reaches the API as a malformed target - an
    # error that says nothing about which of ten rows was wrong. Stage 1d step 9 paid for this
    # once: `Log Archive` matches nothing, because the account is `Log Archive Account`.
    precondition {
      condition     = local.account_ids[each.value.account] != null
      error_message = "No ACTIVE account named ${local.accounts[each.value.account]} (assignment ${each.key}). Names are exact and Control Tower vended every account with an ` Account` suffix; there is also a SUSPENDED account called plain `Sandbox`. The roster is section 2.4 of ./aws/list-identities.py - read it before editing locals.accounts."
    }
  }

  # THE SET MUST CARRY ITS POLICY BEFORE ANYBODY IS ASSIGNED TO IT. Terraform cannot infer this
  # - the assignment references the permission set, not its inline policy - and without it the
  # graph is free to provision a set with NO policy into an account and attach the policy
  # afterwards. That window is short and it is real: a set with no policy is a role with no
  # permissions, and the person who signs in during it files a bug against the design.
  depends_on = [aws_ssoadmin_permission_set_inline_policy.persona]
}
