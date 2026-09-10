# The one imported set - Stage 2 step 5.2, created by hand in Stage 1b step 3.
#
# It is not written like the other six because it is the credential the code applies as (1b step
# 3.9). A permission set whose only source is the state file that needs it to be applied is a
# cycle, and the Account Factory direct assignments (D32) are the only thing standing behind it.
# So: authored by hand, imported here, and the direct assignments stay.
#
# It is imported rather than left alone because an artefact nobody owns is worse than one
# somebody owns badly (Lesson 5), and this is the set that carries AdministratorAccess on every
# Terraform-managed account. It is also the cheap rehearsal step 5.5 asks for: the import
# mechanism is exercised here, where the worst outcome is that somebody cannot sign in, before
# it is pointed at org-policies/, where the worst outcome is an organization locked out of
# itself.
#
# ============================================================================================
# The import, on the command line rather than in an `import {}` block (decision 6)
# ============================================================================================
#
# Blocks are reviewable and live in git, which is the problem here: an
# aws_ssoadmin_account_assignment import id is
#   <principal_id>,GROUP,<account_id>,AWS_ACCOUNT,<permission_set_arn>,<instance_arn>
# so a block would put in a tracked file both an account id (aws/INDEX.md rule 1) and the group
# GUID this configuration is forbidden to hold (conventions: resolve a group by display name).
# The ids are measured by ./aws/import-ids.py into untracked aws/output/import-ids.txt §3, and
# the commands are:
#
#   terraform import aws_ssoadmin_permission_set.infrastructure          '<ps_arn>,<instance_arn>'
#   terraform import aws_ssoadmin_managed_policy_attachment.infrastructure_admin \
#                    'arn:aws:iam::aws:policy/AdministratorAccess,<ps_arn>,<instance_arn>'
#   terraform import 'aws_ssoadmin_account_assignment.infrastructure["<slug>"]' \
#                    '<group_id>,GROUP,<account_id>,AWS_ACCOUNT,<ps_arn>,<instance_arn>'
#
# The last one is the one that goes wrong (step 5.5a(iii)): it imports into a for_each, so the
# key must be exactly what this configuration computes - the slugs of locals.accounts. A wrong
# key does not error; it leaves an orphan in state and a create in the plan. Import one, run
# `plan`, then the rest.
#
# The gate afterwards is an empty plan, not a small one (step 5.5). Everything below was read
# back from the live object on 2026-08-16 for that reason - the description, the PT4H session,
# the single managed policy, the absence of an inline policy and of a boundary, and the
# CostCenter tag - because each is a diff waiting to happen on a set nobody meant to change.

# The fifth group, looked up here rather than in data.tf: it belongs to the imported half, and
# keeping the two halves' lookups apart lets a reader tell which is which.
data "aws_identitystore_group" "infrastructure" {
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "sso-group-infrastructure"
    }
  }
}

resource "aws_ssoadmin_permission_set" "infrastructure" {
  name         = "InfrastructureAccess"
  description  = "The builder: the identity terraform apply runs as"
  instance_arn = local.instance_arn

  session_duration = var.session_duration

  # The one tag that is not default_tags. This set was created in Stage 1b and the directory
  # carries CostCenter=stage-01b on it. Leaving it to default_tags (stage-02) would make the
  # first plan after the import rewrite a tag on the administrator set - the non-empty plan
  # step 5.5 exists to forbid.
  tags = {
    CostCenter = "stage-01b"
  }

  lifecycle {
    # Not `prevent_destroy`: this set is destroyed if its name changes, and prevent_destroy
    # would turn that into a plan error rather than into the thing that must not happen, a
    # state file that no longer describes the set the operator is signed in through. What
    # guards it is the name written out above, which 1b step 3.2 settled with three reasons
    # behind it.
    precondition {
      condition     = local.instance_arn != null
      error_message = "No IAM Identity Center instance in this Region - see permission-sets.tf."
    }
  }
}

# `AdministratorAccess`, the one named exception to "nothing gets AdministratorAccess"
# (docs/plan/conventions.md, IAM rules; D32). It covers one group, because an identity that
# authors IAM cannot be constrained by the IAM it authors - narrowing this set would be notation
# and not a control (Lesson 18). What contains it is detective and enumerated: 1b step 8.3's
# group-membership alarm, Object Lock in compliance mode, and CloudTrail with log file
# validation. Any other principal holding administrator is a finding, not a precedent.
resource "aws_ssoadmin_managed_policy_attachment" "infrastructure_admin" {
  instance_arn       = local.instance_arn
  managed_policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AdministratorAccess"
  permission_set_arn = aws_ssoadmin_permission_set.infrastructure.arn
}

# One assignment per Terraform-managed account, over locals.accounts itself - the same names the
# persona assignments resolve through. This set exists in exactly the accounts this repository
# applies into, so a further account folder and its assignment are one edit rather than two.
#
# `Staging` arrived here 2026-09-06, in the same edit Stage 6b step 4.6 added it to
# locals.accounts by renaming `development`.
#
# Not modelled, listed so that "not here" and "missed" stay distinguishable:
#   - The Account Factory direct assignments (D32, 1b step 3.8) - Control Tower's
#     AWSAdministratorAccess to the infrastructure user, in every vended account. 1b step 5.1
#     found they are re-created, which makes them a permanent property of a vended account
#     rather than something to model. They are also what stands behind this set: remove them
#     from an account before the group path is proven there, and the only remaining recovery
#     path is the Management root (D16 - D30 was reverted).
#   - `Policy Canary`, permanently. Its direct assignment is the only way into the account
#     (D29), there is no group and no awsds-infra-* profile behind it, and the account has no
#     state bucket and no slice by design.
#   - Management, Audit and Log Archive. No project persona holds anything there (1b step 4),
#     the infrastructure user included, and that is what D34 buys.
resource "aws_ssoadmin_account_assignment" "infrastructure" {
  for_each = local.accounts

  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.infrastructure.arn

  principal_id   = data.aws_identitystore_group.infrastructure.group_id
  principal_type = "GROUP"

  target_id   = local.account_ids[each.key]
  target_type = "AWS_ACCOUNT"

  lifecycle {
    precondition {
      condition     = local.account_ids[each.key] != null
      error_message = "No ACTIVE account named ${each.value}. See the note in assignments.tf: the names are exact, and section 2.4 of ./aws/list-identities.py is the roster."
    }
  }
}
