#!/usr/bin/env bash
#
# org-policy-baseline.sh - the ceiling that already exists: every organization node, the
# policies attached to it, the Control Tower controls enabled on it, and the quota that
# says how much more will fit.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile in ~/.aws/config that declares
#             `sso_session = awsds` (see aws/INDEX.md).
#
#   run:      ./aws/org-policy-baseline.sh                   # awsds-infra-identity
#             ./aws/org-policy-baseline.sh awsds-infra-dev   # a different profile
#             ./aws/org-policy-baseline.sh -                 # no --profile: CloudShell on
#                                                            # MANAGEMENT, as CT Admin
#   writes:   aws/output/org-policy-baseline.txt   (untracked - see .gitignore)
#   reads:    organizations:DescribeOrganization, ListRoots,
#             ListOrganizationalUnitsForParent, ListPoliciesForTarget, DescribePolicy,
#             controltower:ListEnabledControls, servicequotas:ListServiceQuotas,
#             sts:GetCallerIdentity. This script never creates, updates or deletes anything.
#
# WHY THIS EXISTS. Stage 1c step 7.0 is a preflight: five measurements that every policy in
# 7.5-7.8 needs as input, collected in one pass *before* the first `create-policy`. Written
# out by hand they are a dozen commands with ids threaded between them, run in the evening,
# at the start of the one landing-zone step that has no in-account repair. Three of the five
# are here (7.0 steps 1, 2, 3) plus the quota (step 5); step 4 is per-account and lives in
# aws/account-bpa.sh, because its subject is the difference between accounts.
#
# The three things it is collected FOR, so that a reader knows what to do with each section:
#   - The ids, ARNs and full OU PATHS that 7.5's `aws:PrincipalOrgPaths` carve-out and 7.7's
#     control targets are written from. A path derived at 23:00 is how a policy lands on the
#     wrong node.
#   - The GAP. Control Tower's mandatory controls already deny changes to CloudTrail and to
#     the Config recorder on every registered OU, with the service-role carve-outs that keep
#     the landing zone able to update itself. Section 4 prints those documents so that 7.5
#     writes only what is missing instead of a second, thinner copy of them (verification
#     (iii) - which is a thing to read BEFORE writing, not to notice afterwards).
#   - The BUDGET. 10 SCPs and 10 240 characters per node, but 5 RCPs and 5 120 for RCPs, and
#     7.7 spends one more SCP slot on every OU it touches. Section 6 measures rather than
#     trusting a remembered number (Lesson 6 applied to a quota).
#
# IDENTITY, and the question this script answers by running. Organizations is administered
# from the management account, for which there is no local profile and never will be
# (guiding principle 1). Reads are a different matter: Stage 1b step 4 measured that a
# delegated administrator answers the Organizations read surface, and 2026-08-12 extended
# that to the trusted-access calls. Whether it extends to the *policy* reads
# (ListPoliciesForTarget, DescribePolicy) is Stage 1c verification (x), open at the time
# this script was written - so the script does not assume it: a denial is reported in full
# in the last section, with a non-zero exit, and the fallback is one line in CloudShell on
# the management account as `AWS Control Tower Admin`:
#
#     ./aws/org-policy-baseline.sh -
#
# Record in log/ which identity the answer actually required. `controltower
# list-enabled-controls` (section 5) is expected to need that fallback even if the
# Organizations reads do not - it is not an Organizations call at all.
#
# WHAT IT CANNOT SEE, stated because an empty block and a missing thing look alike:
#   - A policy type that is not ENABLED on the root cannot be listed per target: the call
#     raises instead of returning empty, and section 3 prints `(policy type not enabled)`.
#     Today that is the expected answer for RCP, tag and declarative policies - it is
#     Stage 1c step 7.2's precondition, measured rather than assumed.
#   - An UNREGISTERED target errors on list-enabled-controls rather than returning an empty
#     list, and section 5 keeps the two apart on purpose (Lesson 13). 7.7 may not enable a
#     control on an OU this call rejected.
#   - Accounts are not listed here at all. The tree with its accounts is
#     aws/list-identities.sh section 2.3; this script's subject is the NODES and what is
#     attached to them, which is why it prints ARNs and paths that one does not.

set -uo pipefail

PROFILE="${1:-${AWSDS_PROFILE:-awsds-infra-identity}}"
REGION="us-west-2"
QUOTA_REGION="us-east-1"   # Organizations quotas answer in us-east-1 only
SSO_SESSION="awsds"

# Normally run from inside the repository. The `-` fallback runs it in CloudShell, which has
# no repository, so the root is located rather than assumed and the report lands beside the
# script when there is none.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/org-policy-baseline.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/org-policy-baseline.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

NODES="$TMP/nodes.tsv"      # Kind <tab> Name <tab> Id <tab> Arn <tab> Path <tab> Depth
SEEN_POL="$TMP/seen-policies.txt"
ERRORS="$TMP/errors.txt"    # one line per failed call
: >"$NODES"; : >"$SEEN_POL"; : >"$ERRORS"

# `-` / `none` means ambient credentials: CloudShell, or an assumed role in the shell.
# PROFILE_OPT is deliberately left unquoted at the call site so that it expands to nothing
# when empty; profile names carry no spaces, so the word split is safe.
if [ "$PROFILE" = "-" ] || [ "$PROFILE" = "none" ]; then
  PROFILE_OPT=""
  PROFILE_LABEL="(none - ambient credentials, e.g. CloudShell)"
else
  PROFILE_OPT="--profile $PROFILE"
  PROFILE_LABEL="$PROFILE"
fi

# ------------------------------------------------------------------------------ helpers

# progress, on stderr, so it reaches the terminal and not the report
note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

# aws, always with this script's profile and region. </dev/null so that a call made from
# inside a `while read` loop cannot swallow the loop's input.
aws_() { command aws $PROFILE_OPT --region "$REGION" "$@" </dev/null; }

# capture a call: sets RUN_OUT and RUN_STATUS, logs a failure, prints nothing.
# TOLERATE holds a regex of error text that means "the question does not apply here", not
# "this failed" - a matched error sets RUN_TOLERATED and is kept out of the failure section,
# because a section that lists non-problems stops being read (the mirror of Lesson 13).
RUN_OUT=""; RUN_STATUS=0; RUN_TOLERATED=0; TOLERATE=""
run() {
  RUN_OUT=$(aws_ "$@" 2>&1)
  RUN_STATUS=$?
  RUN_TOLERATED=0
  if [ "$RUN_STATUS" -ne 0 ]; then
    if [ -n "$TOLERATE" ] && printf '%s' "$RUN_OUT" | grep -qE "$TOLERATE"; then
      RUN_OUT=""; RUN_STATUS=0; RUN_TOLERATED=1
      return 0
    fi
    printf 'aws %s\n    %s\n' "$*" "$(printf '%s' "$RUN_OUT" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    RUN_OUT=""
  fi
}

# run a call, echo it into the report, then its output (or the error it raised)
show() {
  printf '$ aws %s\n\n' "$*"
  local out status
  out=$(aws_ "$@" 2>&1)
  status=$?
  if [ "$status" -ne 0 ]; then
    printf '%s\n\n!! COMMAND FAILED (exit %s)\n\n' "$out" "$status"
    printf 'aws %s\n    %s\n' "$*" "$(printf '%s' "$out" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    return "$status"
  fi
  if [ -n "$out" ]; then printf '%s\n' "$out"; else printf '(empty result - the call succeeded and returned nothing)\n'; fi
  printf '\n'
}

# align a tab-separated stream into a table; empty cells must be written as "-"
tabulate() { column -t -s $'\t'; }

# ---------------------------------------------------------------------------- preflight

note "profile: $PROFILE_LABEL (region $REGION)"
if ! CALLER=$(command aws $PROFILE_OPT --region "$REGION" \
                sts get-caller-identity --query 'Arn' --output text 2>&1); then
  note ""
  note "cannot authenticate as '$PROFILE_LABEL':"
  printf '%s\n' "$CALLER" | sed '/^[[:space:]]*$/d; s/^/  /' >&2
  note ""
  note "log in first:"
  note "  aws sso login --sso-session $SSO_SESSION"
  note ""
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi
note "caller : $CALLER"

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'The organization ceiling as it stands: nodes, attached policies, enabled controls\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'region    : %s   (Organizations is global; quotas are read in %s)\n' "$REGION" "$QUOTA_REGION"
printf 'produced  : aws/org-policy-baseline.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. The organization: id, feature set, root, enabled policy types\n'
printf '  2. Every node - id, ARN and the full PATH a policy condition needs\n'
printf '  3. Policies attached per node, per policy type\n'
printf '  4. The documents of the policies found - what is ALREADY denied\n'
printf '  5. Control Tower controls enabled per node, and whether the node is registered\n'
printf '  6. The quota: how many policies fit on one node, and how large each may be\n'
printf '  7. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - THIS IS AN INPUT TO WRITING POLICY, not a record of it. Stage 1c step 7.0.\n'
printf '    What was decided from it goes in log/stage-01c-preventive-policies.md; the\n'
printf '    documents themselves go in terraform-live/identity/org-policies/policies/.\n'
printf '  - SECTION 4 IS THE ONE THAT SHRINKS THE WORK. Control Tower mandatory controls\n'
printf '    already deny changes to CloudTrail and to the Config recorder on every\n'
printf '    REGISTERED OU, with the carve-outs (AWSControlTowerExecution,\n'
printf '    aws-controltower-ConfigRecorderRole) that keep the landing zone able to update\n'
printf '    itself. Write only the gap: a hand-written duplicate costs SCP budget and adds\n'
printf '    a second place to get those carve-outs wrong.\n'
printf '  - `(policy type not enabled)` in section 3 is a MEASUREMENT, not a failure: the\n'
printf '    type has to be enabled on the root before anything of that type can attach\n'
printf '    (step 7.2). Only SERVICE_CONTROL_POLICY is expected to be enabled today.\n'
printf '  - IN SECTION 5, AN ERROR AND AN EMPTY LIST MEAN DIFFERENT THINGS. An unregistered\n'
printf '    target errors; a registered one with no elective control returns an empty list.\n'
printf '    7.7 may not enable a control on a target this call rejected (Lesson 13).\n'
printf '  - Every "$ aws ..." line is the exact command that produced the block under it,\n'
printf '    minus `--region` and the profile, which every command carries.\n'
printf '  - This is a point-in-time snapshot, not a source of truth: regenerate it rather\n'
printf '    than trusting a stale copy, and record intent in plan/ or log/, never here.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

# --------------------------------------------------------------------------------------
h1 "1. The organization: id, feature set, root, enabled policy types"

note "describing the organization..."
show organizations describe-organization \
    --query 'Organization.[Id,FeatureSet,MasterAccountId,Arn]' \
    --output table

printf 'FeatureSet must read ALL: RESOURCE_CONTROL_POLICY requires an organization with all\n'
printf 'features enabled, and half of Stage 1c has nowhere to attach without it.\n\n'

run organizations describe-organization --query 'Organization.Id' --output text
ORG_ID="${RUN_OUT:-<o-unknown>}"
printf 'ORG_ID=%s\n' "$ORG_ID"

h2 "1.2 The root, and the policy types that may be attached at all"

note "listing roots..."
show organizations list-roots \
    --query 'Roots[].[Id,Name,Arn]' \
    --output table

run organizations list-roots --query 'Roots[0].Id' --output text
ROOT_ID="${RUN_OUT:-<r-unknown>}"
printf 'ROOT_ID=%s\n\n' "$ROOT_ID"

show organizations list-roots \
    --query 'Roots[0].PolicyTypes[].[Type,Status]' \
    --output table

printf 'Expected today (measured 2026-08-11): SERVICE_CONTROL_POLICY ENABLED and nothing\n'
printf 'else. Step 7.2 enables RESOURCE_CONTROL_POLICY, TAG_POLICY and\n'
printf 'DECLARATIVE_POLICY_EC2 - from the MANAGEMENT account, as CT Admin; the Identity\n'
printf 'account can read this and cannot change it. After enabling, each must read ENABLED\n'
printf 'and not PENDING_ENABLE.\n'

# --------------------------------------------------------------------------------------
h1 "2. Every node - id, ARN and the full PATH a policy condition needs"

note "walking the OU tree..."

# The root is a node like any other for attachment purposes, and it is where 7.5 attaches.
run organizations list-roots --query 'Roots[0].Arn' --output text
ROOT_ARN="${RUN_OUT:--}"
printf 'ROOT\t(root)\t%s\t%s\t%s/%s/\t0\n' "$ROOT_ID" "$ROOT_ARN" "$ORG_ID" "$ROOT_ID" >>"$NODES"

# Breadth-first, because the tree is two levels deep (INV-03: `Sandboxes` under
# `Interactive`) and a one-level walk would silently miss every nested OU - the same failure
# a one-level Terraform for_each would have.
QUEUE="$TMP/queue.tsv"                                  # ParentId <tab> ParentPath <tab> Depth
printf '%s\t%s/%s/\t0\n' "$ROOT_ID" "$ORG_ID" "$ROOT_ID" >"$QUEUE"

while [ -s "$QUEUE" ]; do
  NEXT="$TMP/queue.next.tsv"; : >"$NEXT"
  while IFS=$'\t' read -r parent_id parent_path depth; do
    [ -n "${parent_id:-}" ] || continue
    run organizations list-organizational-units-for-parent \
        --parent-id "$parent_id" \
        --query 'OrganizationalUnits[].[Name,Id,Arn]' \
        --output text
    [ -n "$RUN_OUT" ] || continue
    printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r name id arn; do
      [ -n "${name:-}" ] || continue
      child_depth=$((depth + 1))
      printf 'OU\t%s\t%s\t%s\t%s%s/\t%s\n' \
        "$name" "$id" "$arn" "$parent_path" "$id" "$child_depth" >>"$NODES"
      printf '%s\t%s%s/\t%s\n' "$id" "$parent_path" "$id" "$child_depth" >>"$NEXT"
    done
  done <"$QUEUE"
  mv "$NEXT" "$QUEUE"
done

{
  printf 'KIND\tNAME\tID\tARN\tPATH (aws:PrincipalOrgPaths)\tDEPTH\n'
  cat "$NODES"
} | tabulate

printf '\n'
printf 'THE PATH COLUMN IS WHAT 7.5 IS WRITTEN FROM. `aws:PrincipalOrgPaths` is\n'
printf 'multi-valued, so its condition is ForAllValues:StringNotLike and never a bare\n'
printf 'StringNotLike; the value is the full path WITH the trailing slash, exactly as\n'
printf 'printed above. Use the `Data` row for the datazone:CreateDomain carve-out. Confirm\n'
printf 'any path against `aws organizations list-parents`, never against a screenshot.\n\n'
printf 'THE ARN COLUMN IS WHAT 7.7 IS WRITTEN FROM: `controltower enable-control` takes its\n'
printf '%s\n\n' '--target-identifier as an ARN, not as an id.'
printf 'DEPTH 2 IS EXPECTED AND IS INV-03. A node missing here that exists in the console\n'
printf 'means the walk was denied somewhere - check section 7 before believing the tree.\n'

# --------------------------------------------------------------------------------------
h1 "3. Policies attached per node, per policy type"

note "listing attached policies per node..."

printf 'One block per node. AwsManaged=True is Control Tower or AWS; False is this\n'
printf "project's. Nothing of this project's is expected here before Stage 1c step 7.5.\n"

while IFS=$'\t' read -r kind name id arn path depth; do
  [ -n "${id:-}" ] || continue
  h2 "3.x $kind $name  ($id)"
  for TYPE in SERVICE_CONTROL_POLICY RESOURCE_CONTROL_POLICY TAG_POLICY DECLARATIVE_POLICY_EC2; do
    printf '%s:\n' "$TYPE"
    TOLERATE='PolicyTypeNotEnabledException|policy type is not enabled'
    run organizations list-policies-for-target \
        --target-id "$id" --filter "$TYPE" \
        --query 'Policies[].[Name,Id,AwsManaged]' \
        --output text
    TOLERATE=""
    if [ "$RUN_TOLERATED" -eq 1 ]; then
      printf '  (policy type not enabled on the root - step 7.2 enables it)\n'
    elif [ -z "$RUN_OUT" ]; then
      printf '  (none attached)\n'
    else
      printf '%s\n' "$RUN_OUT" | sed 's/^/  /' | tr '\t' ' '
      # remember the SCP ids, so section 4 can print their documents once each
      if [ "$TYPE" = "SERVICE_CONTROL_POLICY" ]; then
        printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r pname pid pmanaged; do
          [ -n "${pid:-}" ] || continue
          printf '%s\t%s\t%s\n' "$pid" "$pname" "$pmanaged" >>"$SEEN_POL"
        done
      fi
    fi
    printf '\n'
  done
done <"$NODES"

printf 'EXPECT `aws-guardrails-*` ON EVERY REGISTERED OU, and expect those to already deny\n'
printf 'what 7.5 was going to write by hand for CloudTrail and Config. Read the documents in\n'
printf 'section 4 and write only the gap. GuardDuty is the part Control Tower does NOT cover\n'
printf 'here, which is why its four denies belong in awsds-org-scp-baseline.json.\n'

# --------------------------------------------------------------------------------------
h1 "4. The documents of the policies found - what is ALREADY denied"

if [ ! -s "$SEEN_POL" ]; then
  printf 'No service control policy was returned by section 3 - either none is attached\n'
  printf 'anywhere (which would contradict a Control Tower landing zone) or the listing was\n'
  printf 'denied. Check section 7 before concluding the first.\n'
else
  note "describing each policy found..."
  sort -u "$SEEN_POL" | while IFS=$'\t' read -r pid pname pmanaged; do
    [ -n "${pid:-}" ] || continue
    h2 "4.x $pname  ($pid, AwsManaged=$pmanaged)"
    show organizations describe-policy --policy-id "$pid" \
        --query 'Policy.Content' --output text
  done
  printf 'READ THESE FOR THREE THINGS: which actions are already denied (do not duplicate);\n'
  printf 'which principals are carved out (AWSControlTowerExecution,\n'
  printf 'aws-controltower-ConfigRecorderRole - the landing zone updates itself through\n'
  printf 'them); and how much of the per-node character budget they already spend.\n'
fi

# --------------------------------------------------------------------------------------
h1 "5. Control Tower controls enabled per node, and whether the node is registered"

note "listing enabled controls per node..."

printf 'This is 7.0 step 3 and 7.7 registration check in one call. AN UNREGISTERED TARGET\n'
printf 'ERRORS rather than returning an empty list - that distinction IS the check.\n'
printf 'Registration is expected for every non-foundational OU (each received an Account\n'
printf 'Factory vend, and Account Factory only offers registered OUs), but expected is not\n'
printf 'measured. The organization ROOT is not a control target and is skipped.\n\n'
printf 'This is a controltower: call, not an Organizations one, so the read boundary Stage\n'
printf '1b step 4 measured says nothing about it. If every row below failed, re-run in\n'
printf 'CloudShell on MANAGEMENT as CT Admin:  ./aws/org-policy-baseline.sh -\n'

while IFS=$'\t' read -r kind name id arn path depth; do
  [ "$kind" = "OU" ] || continue
  h2 "5.x OU $name  ($id)"
  printf 'target: %s\n\n' "$arn"
  show controltower list-enabled-controls \
      --target-identifier "$arn" \
      --query 'enabledControls[].[controlIdentifier,statusSummary.status,driftStatusSummary.driftStatus]' \
      --output table
done <"$NODES"

printf 'DIFF `Security` AGAINST `Identity` HERE (7.6). `Identity` was created outside\n'
printf "Control Tower's own flow, so it carries no policy set until code attaches one; what\n"
printf '`Security` has extra is mostly the foundational set about the log-archive and audit\n'
printf 'buckets, which means nothing for an account that holds neither. Record the diff.\n\n'
printf 'AND CHECK `Sandboxes` AGAINST `Interactive` after 7.7 enables the first control:\n'
printf 'whether a nested OU inherits an enabled control is verification (xi), and this is\n'
printf 'the call that answers it.\n'

# --------------------------------------------------------------------------------------
h1 "6. The quota: how many policies fit on one node, and how large each may be"

note "reading the Organizations quotas..."

printf 'Organizations quotas answer in %s only; that is why this one call changes region.\n\n' "$QUOTA_REGION"

printf '$ aws service-quotas list-service-quotas --service-code organizations --region %s\n\n' "$QUOTA_REGION"
QOUT=$(command aws $PROFILE_OPT --region "$QUOTA_REGION" \
         service-quotas list-service-quotas --service-code organizations \
         --query 'Quotas[].[QuotaName,Value]' --output text 2>&1)
QSTATUS=$?
if [ "$QSTATUS" -ne 0 ]; then
  printf '%s\n\n!! COMMAND FAILED (exit %s)\n\n' "$QOUT" "$QSTATUS"
  printf 'aws service-quotas list-service-quotas --service-code organizations\n    %s\n' \
    "$(printf '%s' "$QOUT" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
else
  {
    printf 'QUOTA\tVALUE\n'
    printf '%s\n' "$QOUT" | grep -iE 'polic|attach|size|maximum' | sort
  } | tabulate
  printf '\n(full list, unfiltered:)\n\n'
  printf '%s\n' "$QOUT" | sort | sed 's/\t/  /'
fi

printf '\n'
printf 'WHAT TO DO WITH THIS. Count the slots per node BEFORE writing, and remember that\n'
printf '7.7 consumes one more SCP slot on every OU it touches (the Region deny is\n'
printf 'implemented as an SCP that Control Tower attaches). SCPs and RCPs do not share a\n'
printf 'budget and the numbers differ - prefer one well-Sid-ed policy per node to several\n'
printf 'thin ones. A policy that will not attach is discovered at the END of the evening.\n'
printf 'If a quota is missing above, Service Quotas does not publish it: fall back to the\n'
printf "Organizations documentation and record which number you used and where it came from.\n"

# --------------------------------------------------------------------------------------
h1 "7. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
  printf '\nIf these are AccessDenied, WHICH CALLS FAILED IS THE ANSWER TO VERIFICATION (x):\n'
  printf '  - Organizations reads denied  -> the delegated-administrator read surface does\n'
  printf '    NOT extend to the policy calls, and 7.0 can never be a script from Identity.\n'
  printf '  - only controltower: denied   -> expected; that call is not an Organizations one.\n'
  printf 'Either way, re-run in CloudShell on MANAGEMENT as `AWS Control Tower Admin`:\n'
  printf '  ./aws/org-policy-baseline.sh -\n'
  printf 'and record in log/stage-01c-preventive-policies.md which identity each answer\n'
  printf 'actually required.\n'
else
  printf 'None. Every call in this report returned successfully - which also answers\n'
  printf 'verification (x) in the affirmative: the policy reads and list-enabled-controls\n'
  printf 'both answered as %s.\n' "$PROFILE_LABEL"
fi

printf '\nRegenerate with:  ./aws/org-policy-baseline.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 7)"
  exit 1
fi
note "wrote $OUT"
exit 0
