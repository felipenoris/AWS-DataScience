# The six persona permission sets - Stage 2 step 5.2.
#
# WRITTEN, NOT IMPORTED, AND THAT IS THE SUBSTANCE OF STAGE 1b STEP 3.9. An earlier version of
# the plan had all seven typed into a console at 1b and then re-expressed here, with step 5.5
# demanding the second expression match the first byte for byte - the same work twice, with a
# gate in the middle designed to fail on JSON whitespace. Nothing between 1b and Stage 5 needs
# any of these six, so they were never created by hand. THEIR FIRST APPLY IS A CREATE, and an
# empty plan here would mean nothing was written.
#
# The seventh - InfrastructureAccess - is in infrastructure-access.tf and IS imported: it is
# the credential this apply runs as, and a set whose only source is the state file that needs
# it to be applied is a cycle.
#
# A for_each OVER AN AUTHORED MAP, WHICH IS SAFE HERE AND WOULD NOT BE FOR THE ASSIGNMENTS. The
# map is locals.persona_sets - human-written, six rows, no data source anywhere near it. It is
# also why step 5.5a(iii)'s warning about importing into a for_each does not apply: nothing in
# this file is imported.

resource "aws_ssoadmin_permission_set" "persona" {
  for_each = local.persona_sets

  name         = each.value.name
  description  = each.value.description
  instance_arn = local.instance_arn

  session_duration = var.session_duration

  # No relay_state: a landing page belongs to the console experience Stage 6 designs, and one
  # set out of six carrying it would be the kind of difference nobody can explain later.

  lifecycle {
    # THE REGION, DIAGNOSED WHERE IT IS WRONG. An Identity Center instance is regional, so a
    # provider pointed at the wrong Region returns an EMPTY list rather than an error, and
    # `one()` turns that into null. Without this the failure surfaces as a provider complaint
    # about a malformed ARN, three resources away from the cause.
    precondition {
      condition     = local.instance_arn != null
      error_message = "No IAM Identity Center instance in this Region. The instance is regional and this organization's lives in the Region of terraform.auto.tfvars - regenerate it with ./scripts/gen-tfvars.py identity sso."
    }

    # THE PROFILE, CHECKED AGAINST THE SLICE RATHER THAN TRUSTED. Every command in this stage
    # carries AWS_PROFILE explicitly for Lesson 25's reason - a borrowed session outlives the
    # command that needed it, and every later error names the wrong account. This is the same
    # rule made mechanical: the identity plane is applied from the Identity account, and an
    # apply that reached here under another profile would fail somewhere less legible (the
    # backend, or a delegation the other account does not hold) with a message about S3 or
    # about SSO rather than about the profile.
    #
    # It compares the CALLER against the account this configuration itself names, so nothing
    # is hardcoded and no id enters a tracked file.
    precondition {
      condition     = data.aws_caller_identity.current.account_id == local.account_ids["identity"]
      error_message = "This slice is applied from the Identity account and this session is somewhere else. Use AWS_PROFILE=awsds-infra-identity (the infrastructure user, Identity account, InfrastructureAccess) - and check it with `aws sts get-caller-identity` before, not after."
    }
  }
}

# ------------------------------------------------------------------------- the inline policies
#
# ONE INLINE POLICY PER SET, EACH COMPOSED FROM THE SHARED DENY FRAGMENT PLUS ITS OWN
# STATEMENTS (policies-shared.tf, policies-data-scientists.tf, policies-approvers.tf).
#
# NO CUSTOMER-MANAGED POLICY AND NO PERMISSIONS BOUNDARY, BY DECISION 4 (settled 2026-08-16) -
# and the absence is written here rather than left to be noticed. Both would have to exist as
# an aws_iam_policy of the same name and path in EVERY account a set is provisioned into, and
# no governed account has a foundation/ slice yet. Stage 3 adds:
#
#   resource "aws_ssoadmin_permissions_boundary_attachment" "persona" { for_each = ... }
#
# one per set, pointing at the boundary its foundation/ created. What does NOT wait for that is
# the two denies a boundary was wanted for - they are in the shared fragment already.

resource "aws_ssoadmin_permission_set_inline_policy" "persona" {
  for_each = local.persona_sets

  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.persona[each.key].arn
  inline_policy      = local.inline_policies[each.key]

  lifecycle {
    # COUNT BEFORE WRITING (step 5.2), and fail at PLAN rather than at provisioning. A
    # permission set becomes an IAM role in every account it reaches, and an oversized policy
    # fails there - per account, after the apply reported success, in an account nobody is
    # watching. The threshold and the two limits behind it are in variables.tf.
    #
    # WHAT TO DO IF THIS FIRES: not "raise the number". The answer step 5.2 gives is a
    # customer-managed policy, which lands back on decision 4 and therefore on Stage 3.
    precondition {
      condition     = length(local.inline_policies[each.key]) <= var.inline_policy_max_bytes
      error_message = "Inline policy for ${local.persona_sets[each.key].name} is ${length(local.inline_policies[each.key])} characters, over the ${var.inline_policy_max_bytes} the plan allows. See step 5.2: the way out is a customer-managed policy, not a larger threshold."
    }
  }
}
