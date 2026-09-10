# The six persona permission sets - Stage 2 step 5.2.
#
# Written, not imported, which is the substance of Stage 1b step 3.9. Nothing between 1b and
# Stage 5 needs any of these six, so they were never created by hand: their first apply is a
# create, and an empty plan here would mean nothing was written.
#
# The seventh - InfrastructureAccess - is in infrastructure-access.tf and is imported: it is
# the credential this apply runs as, and a set whose only source is the state file that needs
# it to be applied is a cycle.
#
# A for_each over an authored map is safe here and would not be for the assignments. The map is
# locals.persona_sets - human-written, six rows, no data source anywhere near it. Step
# 5.5a(iii)'s warning about importing into a for_each does not apply either: nothing in this
# file is imported.

resource "aws_ssoadmin_permission_set" "persona" {
  for_each = local.persona_sets

  name         = each.value.name
  description  = each.value.description
  instance_arn = local.instance_arn

  session_duration = var.session_duration

  # No relay_state: a landing page belongs to the console experience Stage 6 designs, and one
  # set out of six carrying it would be a difference nobody can explain later.

  lifecycle {
    # The Region, diagnosed where it is wrong. An Identity Center instance is regional, so a
    # provider pointed at the wrong Region returns an empty list rather than an error, and
    # `one()` turns that into null. Without this the failure surfaces as a provider complaint
    # about a malformed ARN, three resources away from the cause.
    precondition {
      condition     = local.instance_arn != null
      error_message = "No IAM Identity Center instance in this Region. The instance is regional and this organization's lives in the Region of terraform.auto.tfvars - regenerate it with ./scripts/gen-tfvars.py identity sso."
    }

    # The profile is checked against the slice rather than trusted. Every command in this stage
    # carries AWS_PROFILE explicitly (Lesson 25), and this makes the rule mechanical: the
    # identity plane is applied from the Identity account, and an apply that reached here under
    # another profile would fail somewhere less legible - the backend, or a delegation the
    # other account does not hold - with a message about S3 or about SSO rather than about the
    # profile.
    #
    # It compares the caller against the account this configuration itself names, so nothing
    # is hardcoded and no id enters a tracked file.
    precondition {
      condition     = data.aws_caller_identity.current.account_id == local.account_ids["identity"]
      error_message = "This slice is applied from the Identity account and this session is somewhere else. Use AWS_PROFILE=awsds-infra-identity (the infrastructure user, Identity account, InfrastructureAccess) - and check it with `aws sts get-caller-identity` before, not after."
    }
  }
}

# ------------------------------------------------------------------------- the inline policies
#
# One inline policy per set, each composed from the shared deny fragment plus its own statements
# (policies-shared.tf, policies-data-scientists.tf, policies-approvers.tf).
#
# No customer-managed policy and no permissions boundary, by decision 4 (settled 2026-08-16).
# Both would have to exist as an aws_iam_policy of the same name and path in every account a set
# is provisioned into, and no governed account has a foundation/ slice yet. Stage 3 adds:
#
#   resource "aws_ssoadmin_permissions_boundary_attachment" "persona" { for_each = ... }
#
# one per set, pointing at the boundary its foundation/ created. The two denies a boundary was
# wanted for do not wait for that: they are in the shared fragment already.

resource "aws_ssoadmin_permission_set_inline_policy" "persona" {
  for_each = local.persona_sets

  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.persona[each.key].arn
  inline_policy      = local.inline_policies[each.key]

  lifecycle {
    # Count before writing (step 5.2), failing at plan rather than at provisioning. A
    # permission set becomes an IAM role in every account it reaches, and an oversized policy
    # fails there - per account, after the apply reported success, in an account nobody is
    # watching. The threshold and the two limits behind it are in variables.tf.
    #
    # If this fires, the answer step 5.2 gives is a customer-managed policy, which lands back
    # on decision 4 and therefore on Stage 3, never a larger number.
    precondition {
      condition     = length(local.inline_policies[each.key]) <= var.inline_policy_max_bytes
      error_message = "Inline policy for ${local.persona_sets[each.key].name} is ${length(local.inline_policies[each.key])} characters, over the ${var.inline_policy_max_bytes} the plan allows. See step 5.2: the way out is a customer-managed policy, not a larger threshold."
    }

    # The addresses are checked for being addresses - Stage 4 step 8.1. This is the one
    # precondition in this repository that guards against a lockout rather than against a
    # failed apply, and it fails at plan naming the home.
    #
    # `DenyControlPlaneOffVpn` denies `*` on `*` unless aws:SourceIp matches this list. IAM
    # does not validate the list: a value that is not a CIDR simply matches nothing, so a
    # foundation/ output that came back null, empty or renamed renders as `/32` and the
    # statement becomes an unconditional deny of everything for all six personas - applied
    # successfully, reported as a clean apply, discovered by a person who cannot sign in.
    # variables.tf refuses an empty vpn_homes map for the same reason; this is the other half,
    # where the map has rows and the state behind one of them did not answer.
    precondition {
      condition = alltrue([
        for cidr in local.vpn_egress_cidrs :
        can(cidrnetmask(cidr)) && endswith(cidr, "/32")
      ])
      error_message = "A VPN home's Elastic IP did not read back as an address: ${jsonencode(local.vpn_egress_cidrs)}. DenyControlPlaneOffVpn would apply cleanly and deny every call from every network for all six personas. Check that each vpn_homes account's foundation/ slice is applied and still exports wireguard_eip_public_ip (Stage 4 step 2.1)."
    }

    # The endpoint ids get the same guard (2026-08-20), because the precondition above
    # predicted the right symptom for the wrong cause: it guards a malformed address list, and
    # the defect arrived through a well-formed list whose key was absent on the S3 path (4d's
    # controls entry). A bad entry here is not a lockout - it silently un-fixes the S3 path, a
    # regression to the 4d defect that only a behavioural proof would notice. Same price for
    # the cheap version: a plan-time failure naming the value.
    precondition {
      condition = alltrue([
        for id in local.vpn_egress_vpc_ids :
        can(regex("^vpc-[0-9a-f]+$", id))
      ])
      error_message = "A VPN home did not read back as a vpc id: ${jsonencode(local.vpn_egress_vpc_ids)}. DenyControlPlaneOffVpn's aws:SourceVpc branch would go quiet and every call a persona makes THROUGH A VPC ENDPOINT from the tunnel would be explicitly denied - the 4d defect for S3, and the 2026-08-23 one for every service holding an interface endpoint. Check that each vpn_homes account's foundation/ still exports vpc_id (Stage 3 step 1)."
    }
  }
}

# ------------------------------------------------------- the one AWS-managed policy on a persona
#
# CloudWatchLogsReadOnlyAccess, on the four sets that run Logs Insights - Stage 4, 2026-08-17.
# The argument lives here rather than four times in the policy documents, which carry a pointer
# to this block.
#
# A managed policy, where every other grant in this slice is authored, because enumerating the
# calls of a console surface is a race that cannot be won, and it was lost twice in one sitting.
# The set was granted Logs Insights from the start and the console failed on
# logs:GetLogGroupFields; that was fixed by deriving the missing actions from AWS's own
# documented console-permission list - three of them, not the one observed - and the console then
# failed on logs:DescribeFieldIndexes, which is not in that list. The method was sound and the
# source was stale: a console acquires calls faster than any list documents them, so the next
# enumeration would have failed too. AWS maintains this policy for that reason - it is on version
# 12, and v12 added a namespace (observabilityadmin) that nobody here would have guessed.
#
# It is safe to be broad because it is read-only by construction. Its actions are logs:Describe*,
# Get*, List*, StartQuery, StopQuery, TestMetricFilter, FilterLogEvents, StartLiveTail,
# StopLiveTail, cloudwatch:GenerateQuery, GenerateQueryResultsSummary and three
# observabilityadmin reads. No Put*, no Delete*, no Create*. It composes under every deny already
# on these sets: the shared fragment and DenyControlPlaneOffVpn both still apply, a deny always
# winning, so the blast radius of a future AWS change is bounded by them.
#
# What is accepted (decided by the user, 2026-08-17):
#
#   1. AWS authors this policy. A future version reaches these personas with no diff in this
#      repository - the shape Lesson 11 warns about, taken here because the alternative is a
#      grant that is provably wrong every few months. The mitigation is the paragraph above: it
#      can only ever add reads, under the denies.
#   2. logs:StartLiveTail / StopLiveTail arrive with it, and Live Tail is billed per minute.
#      Nothing measures it (D12 declined budget alerts), so it is a cost surface opened without
#      a measurement - Lesson 6 acknowledged rather than satisfied.
#   3. cloudwatch:GenerateQuery and GenerateQueryResultsSummary arrive too, which partly
#      undoes the decision to defer the cloudwatch: namespace to Stage 6. It does not include
#      cloudwatch:GetMetricData, so the console's metrics panel still fails - that one stays
#      deferred, with a workload in front of it.
#
# Not DevEnvStewardAccess: its ReadBuildPipelineLogs is narrow by design - the build's own logs,
# not a console surface - and it never failed. GovernanceManagerAccess holds no logs action at
# all.
#
# An AWS-managed policy works where a customer-managed one did not (Stage 2 decision 4): a
# customer-managed policy must exist as an aws_iam_policy of the same name in every account the
# set is provisioned into, which is why the boundary was deferred. An AWS-managed policy exists
# in every account by definition.
resource "aws_ssoadmin_managed_policy_attachment" "cloudwatch_logs_readonly" {
  for_each = toset([
    "data_scientist",
    "data_scientist_staging",
    "data_scientist_prod",
    "deployment_manager",
  ])

  instance_arn       = local.instance_arn
  managed_policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/CloudWatchLogsReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.persona[each.key].arn
}

# ------------------------------------------------------------------------------------------
# The customer-managed reference the comment above says did not work. What changed is whether
# the constraint is met (user decision of 2026-08-23, strategy 1-A; consumer: `s3-read-write/`).
# Decision 4 deferred the boundary because a customer-managed policy must exist as an
# aws_iam_policy of the same name in every account the set is provisioned into, and no governed
# account had a foundation/ slice to put one in. Both member accounts have had one since
# Stage 3, so the object is created there -
# terraform-live/{sandbox,development}/foundation/persona-vending.tf, which carries the whole
# argument for what it authorizes - and this is the reference.
#
# The statement is not inline like every other grant in this slice because `DataScientistAccess`
# renders at 10217 characters against the 10240 precondition, and the statement costs ~251.
# See "The size discipline" in README.md: the answer to a full document is a customer-managed
# policy, not a larger threshold, because the threshold is the IAM inline-role limit this set
# becomes in every account it reaches.
#
# The apply order is the members first. Provisioning resolves the name in each target account:
# applied here first, DataScientistAccess fails to provision in both members - an entitlement
# outage whose message names a policy, not a slice. The order out is the reverse: this reference
# is removed before the objects are.
#
# One reference, two accounts. Unlike the assignments, this resource is per permission set, not
# per (set, account) - the accounts come from wherever the set is assigned, which is why the
# object has to exist in each of them and why backend.py's PERSONA_VENDING_ACCOUNTS follows the
# assignment rows rather than the other way round.
#
# No `path` on either side. The reference carries a name and a path, both default to "/", and
# leaving both implicit keeps them equal by construction rather than by two literals agreeing.
resource "aws_ssoadmin_customer_managed_policy_attachment" "persona_vending" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.persona["data_scientist"].arn

  customer_managed_policy_reference {
    name = var.persona_vending_policy_name
  }
}
