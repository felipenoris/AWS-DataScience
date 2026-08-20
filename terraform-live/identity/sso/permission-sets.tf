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

    # THE ADDRESSES ARE CHECKED FOR BEING ADDRESSES - Stage 4 step 8.1, and this is the one
    # precondition in this repository that guards against a LOCKOUT rather than against a
    # failed apply.
    #
    # `DenyControlPlaneOffVpn` denies `*` on `*` unless aws:SourceIp matches this list. IAM
    # does not validate the list: a value that is not a CIDR simply matches nothing, so a
    # foundation/ output that came back null, empty or renamed renders as `/32` and the
    # statement becomes an unconditional deny of everything for all six personas - applied
    # successfully, reported as a clean apply, discovered by a person who cannot sign in.
    # variables.tf refuses an EMPTY vpn_homes map for the same reason; this is the other half,
    # where the map has rows and the state behind one of them did not answer.
    #
    # A plan-time failure naming the home is the cheap version of that discovery.
    precondition {
      condition = alltrue([
        for cidr in local.vpn_egress_cidrs :
        can(cidrnetmask(cidr)) && endswith(cidr, "/32")
      ])
      error_message = "A VPN home's Elastic IP did not read back as an address: ${jsonencode(local.vpn_egress_cidrs)}. DenyControlPlaneOffVpn would apply cleanly and deny every call from every network for all six personas. Check that each vpn_homes account's foundation/ slice is applied and still exports wireguard_eip_public_ip (Stage 4 step 2.1)."
    }

    # THE ENDPOINT IDS GET THE SAME GUARD (2026-08-20) - and 4d's controls entry is why this
    # one exists at all: the precondition above predicted the right SYMPTOM for the wrong
    # CAUSE (it guards a malformed address list, and the defect arrived through a well-formed
    # list whose key was absent on the S3 path). The asymmetry worth naming: a bad entry here
    # is not a lockout - it silently un-fixes the S3 path, a REGRESSION to the 4d defect that
    # only a behavioural proof would notice. Same price for the cheap version: a plan-time
    # failure naming the value.
    precondition {
      condition = alltrue([
        for id in local.vpn_egress_vpce_ids :
        can(regex("^vpce-[0-9a-f]+$", id))
      ])
      error_message = "A VPN home's gateway endpoint did not read back as a vpce id: ${jsonencode(local.vpn_egress_vpce_ids)}. DenyControlPlaneOffVpn's aws:SourceVpce branch would go quiet and the tunnel's S3 path would be explicitly denied again (the 4d defect). Check that each vpn_homes account's foundation/ still exports s3_gateway_endpoint_id and dynamodb_gateway_endpoint_id (Stage 3 step 1; INT-05)."
    }
  }
}

# ------------------------------------------------------- the one AWS-managed policy on a persona
#
# CloudWatchLogsReadOnlyAccess, on the FOUR sets that run Logs Insights - Stage 4, 2026-08-17.
# The whole argument lives here rather than four times in the policy documents, which now carry
# a pointer to this block.
#
# WHY A MANAGED POLICY AT ALL, when every other grant in this slice is authored. Because
# enumerating the calls of a CONSOLE surface is a race that cannot be won, and it was lost twice
# in one sitting. The set was granted Logs Insights from the start and the console failed on
# logs:GetLogGroupFields; that was fixed by deriving the missing actions from AWS's own
# documented console-permission list - three of them, not the one observed - and the console then
# failed on logs:DescribeFieldIndexes, WHICH IS NOT IN THAT LIST. The method was sound and the
# source was stale: a console acquires calls faster than any list documents them, so the next
# enumeration would have failed too. AWS maintains this policy for exactly that reason - it is on
# version 12, and v12 added a namespace (observabilityadmin) that nobody here would have guessed.
#
# WHY IT IS SAFE TO BE BROAD: read-only by construction. Its actions are logs:Describe*, Get*,
# List*, StartQuery, StopQuery, TestMetricFilter, FilterLogEvents, StartLiveTail, StopLiveTail,
# cloudwatch:GenerateQuery, GenerateQueryResultsSummary and three observabilityadmin reads. No
# Put*, no Delete*, no Create*. And it composes UNDER every deny already on these sets: the
# shared fragment and DenyControlPlaneOffVpn both still apply, a deny always winning, so the
# blast radius of a future AWS change is bounded by them rather than open.
#
# WHAT IS BEING ACCEPTED, NAMED SO IT IS A CHOICE AND NOT A SIDE EFFECT (decided by the user,
# 2026-08-17):
#
#   1. AWS AUTHORS THIS POLICY. A future version reaches these personas with no diff in this
#      repository - the exact shape Lesson 11 warns about, taken deliberately here because the
#      alternative is a grant that is provably wrong every few months. The mitigation is the
#      paragraph above: it can only ever add reads, under the denies.
#   2. logs:StartLiveTail / StopLiveTail arrive with it, and Live Tail is BILLED PER MINUTE.
#      Nothing measures it (D12 declined budget alerts), so it is a cost surface opened without
#      a measurement - Lesson 6 acknowledged rather than satisfied.
#   3. cloudwatch:GenerateQuery and GenerateQueryResultsSummary arrive too, which partly
#      undoes the decision to defer the cloudwatch: namespace to Stage 6. It does NOT include
#      cloudwatch:GetMetricData, so the console's metrics panel still fails - that one stays
#      deferred, with a workload in front of it.
#
# WHY NOT DevEnvStewardAccess. Its ReadBuildPipelineLogs is narrow on purpose - the build's own
# logs, not a console surface - and it never failed. Different surface, different treatment.
# GovernanceManagerAccess holds no logs action at all.
#
# WHY AN AWS-MANAGED POLICY WORKS WHERE A CUSTOMER-MANAGED ONE DID NOT (Stage 2 decision 4): a
# customer-managed policy must exist as an aws_iam_policy of the same name in EVERY account the
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
