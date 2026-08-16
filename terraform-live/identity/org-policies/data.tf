# What this slice reads and does not own - Stage 2 step 5.
#
# THREE LOOKUPS, AND EACH ONE EXISTS TO KEEP AN IDENTIFIER OUT OF A TRACKED FILE. Between them
# they produce the same five values render.py substitutes, by the same names, so that step
# 5.5's claim - the import compares a document against itself - is about the same substitution
# performed twice and not about two substitutions that happen to agree (decision 5).
#
#   1. The organization and its root   -> <ORG_ID>, <ROOT_ID>
#   2. Every OU at every depth, by NAME -> <OU_ID_DATA>, and the id behind each authored
#                                          attachment target in attachments.json
#   3. The Data OU's accounts           -> <ACCOUNT_ID_DATA>, and <ORG_PATH_DATA> composed
#                                          from (1) and (2)
#
# NOTHING HERE HAS A LIFECYCLE, which is the other half of step 5's slice split: `sso/` names
# no aws_organizations_* MANAGED resource, and this slice names no aws_ssoadmin_* one. A read
# owns nothing.
#
# ACCOUNTS AND OUs ARE VENDED FROM THE CONSOLE, BY DECISION AND PERMANENTLY (D34). That is why
# every one of these is a data source and none is a resource, and it is why step 9.3's
# `make check-ou` exists at all: an OU nobody attached a document to cannot show up as drift in
# a state file that never declared it.

# READ FOR ONE PURPOSE: the profile precondition in policies.tf. Applying this slice from
# anywhere but the Identity account fails, but it fails at the Organizations API with a message
# about a delegation - which reads like the delegation is broken rather than like the session is
# in the wrong account. The precondition names the profile instead. It is the same instrument
# the sso/ sitting added on 2026-08-16, for the same reason and against the same account.
#
# There is no aws_partition here, unlike sso/: this slice builds no ARN in HCL. The ARNs the
# documents carry are inside the tracked JSON, where a partition is not interpolated at all.
data "aws_caller_identity" "current" {}

# --------------------------------------------------------------------- the organization root

# One read for two of the five values. `roots` is a list because the API returns one, and
# `one()` in locals.tf turns "exactly one" from an assumption into an assertion: an
# organization with no root is not a case to route around.
data "aws_organizations_organization" "this" {}

# ------------------------------------------------------------------ every OU, at every depth

# VERIFICATION (iv), AND THE REASON IT IS THIS DATA SOURCE AND NOT THE PLAIN ONE.
# `aws_organizations_organizational_units` returns the children of ONE parent, and the nesting
# here is two deep: `Sandboxes` sits under `Interactive` (D23). A single level would resolve
# the four OUs that carry a document today and would silently fail to resolve the first
# document ever attached to a nested OU - the failure arriving as a null id at apply time,
# which is the direction that does not announce itself. The descendant form was confirmed to
# exist in the pinned provider before this file relied on it (versions.tf).
#
# WHAT IT DOES *NOT* DO, because step 5.3 point 1 is easy to misread: it does not discover
# attachments. Which document reaches which OU is authored in attachments.json and nowhere
# else - a for_each over discovered OUs would attach something to `Sandboxes` and silently
# reverse D37. This read only turns an authored NAME into the id the API needs.
data "aws_organizations_organizational_unit_descendant_organizational_units" "all" {
  parent_id = local.root_id

  lifecycle {
    # An OU the map names and the organization does not have. `make check-ou` reports the same
    # thing against the live tree; this is the half that stops an APPLY, because a check that
    # ran yesterday is not a precondition.
    postcondition {
      condition = length(
        setsubtract(local.ou_names_required, toset([for ou in self.children : ou.name]))
      ) == 0
      error_message = "attachments.json names an OU this organization does not have, at any depth. Run ./scripts/check-ou-coverage.py to see which, and either attach the document to an OU that exists or record the OU in .ou_with_no_document with the reason."
    }

    # TWO OUs MAY LEGALLY SHARE A NAME under different parents, and a name-keyed map would
    # quietly keep one of them. That is a document attached to the wrong OU with nothing in the
    # plan to show for it, so it stops here instead.
    postcondition {
      condition = alltrue([
        for name in local.ou_names_required :
        length([for ou in self.children : ou.id if ou.name == name]) == 1
      ])
      error_message = "an OU name in attachments.json matches more than one OU in this organization. Organizations permits duplicate names under different parents; this slice keys attachments by name and cannot tell them apart. Rename one, or key that attachment by id in a future revision of the map."
    }
  }
}

# ---------------------------------------------------------------- the Data OU's one account

# <ACCOUNT_ID_DATA> IS DERIVED FROM THE OU, NEVER FROM AN ACCOUNT NAME - step 5.5a(ii), and 1d
# step 9 is where that was paid for once already: Control Tower vended every account with an
# ` Account` suffix, so `Log Archive` resolves to nothing while `Log Archive Account` resolves.
# The OU is the safe direction: the id follows from the OU the document is about.
#
# The consumer is awsds-org-scp-ou-data.json's catalog-maintenance carve-out (D27), whose ARN
# may not name a wildcard account.
data "aws_organizations_organizational_unit_child_accounts" "data_ou" {
  parent_id = local.ou_id_data

  lifecycle {
    # EXACTLY ONE, and a second account is not a case to route around - it is a change to the
    # account map (D35: every account in this design except `Sandbox` is structural). render.py
    # stops on the same condition with the same reasoning, so the two mechanisms fail together
    # rather than one rendering what the other refuses.
    postcondition {
      condition     = length([for a in self.accounts : a.id if a.status == "ACTIVE"]) == 1
      error_message = "expected exactly ONE active account directly under the Data OU. The account map changed, and the D27 carve-out in awsds-org-scp-ou-data.json cannot be rendered until the plan says which account it names."
    }
  }
}
