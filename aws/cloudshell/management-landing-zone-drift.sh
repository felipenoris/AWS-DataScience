#!/usr/bin/env bash
#
# management-landing-zone-drift.sh - Stage 2 verification (iii): does the Organizations
# RESOURCE POLICY coexist with the Control Tower landing zone without raising drift?
#
#   needs:    CloudShell on the MANAGEMENT account, as `AWS Control Tower Admin` through
#             `AWSAdministratorAccess`. There is no laptop path - see IDENTITY below.
#
#   run:      ./aws/cloudshell/management-landing-zone-drift.sh              # CloudShell
#             ./aws/cloudshell/management-landing-zone-drift.sh <profile>    # if one ever exists
#   writes:   aws/output/cloudshell/management-landing-zone-drift.txt  (untracked)
#   reads:    controltower:ListLandingZones, GetLandingZone, ListLandingZoneOperations,
#             GetLandingZoneOperation; organizations:DescribeOrganization,
#             DescribeResourcePolicy, ListRoots, ListPolicies; sts:GetCallerIdentity.
#             It never creates, updates, resets or deletes anything.
#   exits:    0 the report was produced FROM MANAGEMENT | 1 a call failed
#             | 2 it ran somewhere else, so the report is not an answer - see below
#
# What is being asked, and why it is the last thing open in Stage 2. Step 5.1 put a
# resource-based policy on the organization itself - `organizations:PutResourcePolicy`,
# delegating the four policy types to the Identity account - and 5.1a then amended it. The
# organization is Control Tower's own object, so the question is whether the landing zone
# regards that document as drift. Every other verification in the stage was answerable from
# the Identity account; this one is a Management read, which is why it is a script in this
# folder rather than a line in a stage file.
#
# The headline field is `driftStatus`, and on its own it is a weak negative. Stage 1d
# verification (iv) established the reading discipline and this script inherits it: Control
# Tower watches a closed list of things it owns, so IN_SYNC confirms that nothing was tripped
# rather than predicting what a landing-zone update would do. The same fact is why 1c's ten
# customer SCPs never raised drift - a customer SCP is not Control Tower's object. A script
# that printed IN_SYNC and stopped would be reporting a clean bill it cannot issue.
#
# So three more readings, each of which makes the first one mean something:
#
#   - The manifest (section 3). It is what the landing zone is configured with - governed
#     Regions, the logging and security accounts, the retention days, the access-management
#     setting. Printed whole, on purpose: nothing in it concerns organization resource
#     policies, so IN_SYNC is silent about the 5.1 delegation rather than approving of it.
#
#     It is not the inventory of what drift detection compares - measured 2026-08-16, on the
#     first real run. The manifest contains no policy of any kind, not even the
#     `aws-guardrails-*` SCPs Control Tower demonstrably owns and 1c step 7.7 read one by one.
#     So it bounds the configuration and not the comparison: it proves resource policies are
#     not part of what the landing zone is set up to be, which is the narrower claim, and the
#     one this report makes.
#
#   - The operation history (section 4), the strongest evidence available without writing
#     anything. `driftStatus` is a flag; an operation is the landing zone actually doing work.
#     An update or reset that ran after the delegation was applied and returned SUCCEEDED is
#     positive evidence of coexistence, of a kind no flag can give. If the last operation
#     predates the delegation, say so - it means the landing zone has not yet had occasion to
#     disagree, which is a different answer and the honest one.
#
#   - The document itself (section 5). Read back from Management, including whether 5.1a's
#     `ArnLike` narrowing is still on both write statements. If Control Tower had quietly
#     reverted or replaced the resource policy, this is where it shows - and `DEL-10` going
#     red on the Identity side would be the same finding arriving later and further away.
#
# What this script cannot do (Lesson 22). The strong test is to make the landing zone
# re-evaluate - `update-landing-zone` or `reset-landing-zone` - and observe whether the
# delegation survives. Both are writes on the landing zone, both are slow and hard to undo,
# and neither is a measurement anybody should take to answer a question. So the failing case
# cannot be produced by this harness, the verification is by reading, and the report says
# which of its statements are readings rather than letting them pass as tests. The occasion
# for the strong test arrives on its own: the next real landing-zone update, whose section 4
# row is what to re-read afterwards.
#
# IDENTITY. Management holds no CLI profile by design (D33/D34) - the two
# `awsds-ctadmin-orgfull-*` profiles of 2026-08-15 carry `AWSOrganizationsFullAccess` in
# Identity and Development and reach Management not at all. So this is a CloudShell script
# like management-quotas.sh and audit-iam-analyser.sh: sign in to the access portal as
# `AWS Control Tower Admin`, open CloudShell on the Management account with
# `AWSAdministratorAccess`, paste or clone, run. It takes a profile argument in case one ever
# exists there.
#
# It refuses to interpret the result from anywhere else, which was measured rather than
# assumed (2026-08-16, run as `awsds-infra-identity` before the first real run). From a member
# account both landing-zone calls succeed and return empty: `list-landing-zones` gives `None`
# and `list-landing-zone-operations` gives `{"landingZoneOperations": []}`. Neither is an
# error, so exit codes say nothing, and section 4 read from the wrong account would state
# "the landing zone has never run" - a strong claim, wrong, and indistinguishable from the
# true one (Lesson 13; the same trap management-quotas.sh is built around and the one 1d step
# 9 paid for once). Hence: sections 2-4 are gated on the caller being Management, and a run
# from anywhere else exits 2.
#
# Section 5 is the exception, and it is a finding rather than a leak. `describe-resource-policy`
# answers from the Identity account - the 5.1 delegation grants it there deliberately, which is
# how step 5.0's reading 1 ran before the delegation existed. So "is the document still there
# and still narrowed to two statements" is answerable without Management at all, and
# `./aws/org-delegation.py` is the fuller instrument for it. What Management is needed for is
# everything above section 5.
#
# A second question, answered by a field this file already read (Stage 6b step 0.5).
# `GetLandingZone` returns `remediationTypes` alongside the version and the drift flag, and
# section 2 has printed it since the first run without saying what it decides. It is the
# account auto-enrollment switch: with `INHERITANCE_DRIFT` in that array, Control Tower reacts
# to Organizations `MoveAccount` events and re-baselines the moved account on its own; with
# the array empty, moving an account by hand between two registered OUs leaves the source OU's
# baseline and controls attached and raises inheritance drift. Stage 6b moves one account from
# `Interactive` to `Workloads`, so the switch decides whether its step 3.4 has a supported
# by-hand path at all, and the answer is a reading taken here. The feature needs landing zone
# 3.1 or later (this one is 4.0), and turning it on is an `update-landing-zone` - a write,
# printed in section 6 and not performed.
#
# No account ids are printed, in keeping with aws/INDEX.md rule 1: the report names the
# management account only as `is Management: yes|no`, and the delegation's principal is shown
# with its account digits masked.

set -uo pipefail

PROFILE="${1:--}"
REGION="us-west-2"          # the landing zone's home Region - Control Tower answers there
SSO_SESSION="awsds-ctadmin" # the CT Admin session, NOT `awsds` (that is the infrastructure user)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/../.."
  OUT_DIR="aws/output/cloudshell"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/management-landing-zone-drift.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/lz-drift.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
ERRORS="$TMP/errors.txt"
: >"$ERRORS"

if [ "$PROFILE" = "-" ] || [ "$PROFILE" = "none" ]; then
  PROFILE_OPT=""
  PROFILE_LABEL="(none - ambient credentials, e.g. CloudShell)"
else
  PROFILE_OPT="--profile $PROFILE"
  PROFILE_LABEL="$PROFILE"
fi

# ------------------------------------------------------------------------------ helpers

note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}

aws_() { command aws $PROFILE_OPT --region "$REGION" "$@" </dev/null; }

show() {
  printf '\n$ aws %s\n\n' "$*"
  local out status
  out=$(aws_ "$@" 2>&1); status=$?
  if [ "$status" -ne 0 ]; then
    printf '%s\n\n!! COMMAND FAILED (exit %s)\n\n' "$out" "$status"
    printf 'aws %s\n    %s\n' "$*" "$(printf '%s' "$out" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    return "$status"
  fi
  if [ -n "$out" ]; then printf '%s\n' "$out"; else printf '(empty result - the call succeeded and returned nothing)\n'; fi
  printf '\n'
}

RUN_OUT=""; RUN_STATUS=0
run() {
  RUN_OUT=$(aws_ "$@" 2>&1)
  RUN_STATUS=$?
  if [ "$RUN_STATUS" -ne 0 ]; then
    printf 'aws %s\n    %s\n' "$*" "$(printf '%s' "$RUN_OUT" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    RUN_OUT=""
  fi
}

tabulate() { column -t -s $'\t'; }

# Twelve digits anywhere become <ACCOUNT>. aws/INDEX.md rule 1 - no account id leaves this
# repository in a file, and a report pasted into a log is exactly how one would.
mask() { sed -E 's/[0-9]{12}/<ACCOUNT>/g'; }

# ---------------------------------------------------------------------------- preflight

note "profile: $PROFILE_LABEL (region $REGION)"
if ! CALLER=$(command aws $PROFILE_OPT --region "$REGION" \
                sts get-caller-identity --query 'Arn' --output text 2>&1); then
  note ""
  note "cannot authenticate as '$PROFILE_LABEL':"
  printf '%s\n' "$CALLER" | sed '/^[[:space:]]*$/d; s/^/  /' >&2
  note ""
  note "in CloudShell on Management there is nothing to log in to; from a laptop:"
  note "  aws sso login --sso-session $SSO_SESSION"
  note ""
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi
note "caller : $CALLER"

CALLER_ACCT=$(command aws $PROFILE_OPT --region "$REGION" \
                sts get-caller-identity --query 'Account' --output text 2>/dev/null)

run organizations describe-organization --query 'Organization.MasterAccountId' --output text
MGMT_ID="${RUN_OUT:-}"

IS_MGMT=no
[ -n "${MGMT_ID:-}" ] && [ "${CALLER_ACCT:-}" = "$MGMT_ID" ] && IS_MGMT=yes

# ------------------------------------------------------------------- read the landing zone

note "reading the landing zone..."

run controltower list-landing-zones --query 'landingZones[0].arn' --output text
LZ_ARN="${RUN_OUT:-}"

LZ_JSON="$TMP/lz.json"
: >"$LZ_JSON"
DRIFT="(unread)"; LZ_STATUS="(unread)"; LZ_VERSION="(unread)"; LZ_LATEST="(unread)"; LZ_REMED="(unread)"
AUTO_ENROLL="(unread)"
if [ -n "${LZ_ARN:-}" ] && [ "$LZ_ARN" != "None" ]; then
  run controltower get-landing-zone --landing-zone-identifier "$LZ_ARN" --output json
  printf '%s' "$RUN_OUT" >"$LZ_JSON"
  if [ "$RUN_STATUS" -eq 0 ]; then
    DRIFT=$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))["landingZone"]; print(d.get("driftStatus",{}).get("status","(absent)"))' "$LZ_JSON" 2>/dev/null || echo "(unparsed)")
    LZ_STATUS=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["landingZone"].get("status","(absent)"))' "$LZ_JSON" 2>/dev/null || echo "(unparsed)")
    LZ_VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["landingZone"].get("version","(absent)"))' "$LZ_JSON" 2>/dev/null || echo "(unparsed)")
    LZ_LATEST=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["landingZone"].get("latestAvailableVersion","(absent)"))' "$LZ_JSON" 2>/dev/null || echo "(unparsed)")
    LZ_REMED=$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["landingZone"].get("remediationTypes",[])) or "(none)")' "$LZ_JSON" 2>/dev/null || echo "(unparsed)")
    # The switch is the presence of the inheritance-drift remediation type, not the exact
    # spelling: AWS`s API reference writes it `INHERITANCE_DRIFT` and its user guide writes
    # `Inheritance Drift` in prose, so the match is case-insensitive and ignores the
    # separator. Anything else in the array is printed above and left uninterpreted.
    case "$(printf '%s' "$LZ_REMED" | tr 'A-Z' 'a-z' | tr -d '_ -')" in
      *inheritancedrift*) AUTO_ENROLL="on" ;;
      "(none)"|"")        AUTO_ENROLL="OFF" ;;
      "(unparsed)")       AUTO_ENROLL="(unparsed)" ;;
      *)                  AUTO_ENROLL="OFF" ;;
    esac
  fi
fi

# ------------------------------------------------------------------- the delegation itself

run organizations describe-resource-policy --output json
RP_JSON="$TMP/rp.json"
printf '%s' "$RUN_OUT" >"$RP_JSON"
RP_STATE="ABSENT"
[ "$RUN_STATUS" -eq 0 ] && [ -s "$RP_JSON" ] && RP_STATE="PRESENT"

# 5.1a's narrowing, counted rather than eyeballed: it belongs on the two write statements and
# on neither read statement. A count of 2 is the state DEL-10 reports green from Identity.
#
# The counter is written to a file rather than inlined as a heredoc inside a command
# substitution: that form parses, and it is the kind of shell that breaks silently the first
# time somebody edits it. CloudShell has python3.
COUNTER="$TMP/count_principalarn.py"
cat >"$COUNTER" <<'PY'
import json
import sys

doc = json.load(open(sys.argv[1]))["ResourcePolicy"]["Content"]
doc = json.loads(doc) if isinstance(doc, str) else doc
n = 0
for st in doc.get("Statement", []):
    cond = st.get("Condition", {})
    if any(
        "PrincipalArn" in key
        for operand in cond.values()
        if isinstance(operand, dict)
        for key in operand
    ):
        n += 1
print(n)
PY

ARNLIKE_N="(unread)"
if [ "$RP_STATE" = "PRESENT" ]; then
  if ! ARNLIKE_N=$(python3 "$COUNTER" "$RP_JSON" 2>/dev/null); then
    ARNLIKE_N="(unparsed)"
  fi
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'Control Tower landing zone - drift, and the Organizations resource policy\n'
printf 'Stage 2, verification (iii)\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$(printf '%s' "$CALLER" | mask)"
printf 'produced  : aws/cloudshell/management-landing-zone-drift.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Where this ran - read it FIRST; sections 2-4 answer only from Management\n'
printf '  2. The landing zone: status, version, DRIFT - and account AUTO-ENROLLMENT\n'
printf '  3. What the landing zone declares it manages - the manifest, whole\n'
printf '  4. Operations, and whether any ran AFTER the delegation\n'
printf '  5. The resource policy - and it answers from Identity too\n'
printf '  6. How to read all of this - and what it does NOT say\n'
printf '  7. Calls that failed\n'

# ======================================================================================
h1 "1. Where this ran - read it FIRST"

{
  printf 'FIELD\tVALUE\n'
  printf 'caller ARN\t%s\n' "$(printf '%s' "$CALLER" | mask)"
  printf 'is Management\t%s\n' "$IS_MGMT"
} | tabulate

printf '\n'
if [ "$IS_MGMT" = "yes" ]; then
  printf 'This ran in the MANAGEMENT account, which is the only place the landing zone answers.\n'
else
  printf '!! THIS DID NOT RUN IN THE MANAGEMENT ACCOUNT, SO SECTIONS 2-4 ARE NOT ANSWERS.\n'
  printf '   They are suppressed rather than printed empty, and this run exits 2.\n\n'
  printf 'MEASURED, NOT ASSUMED: from a member account both landing-zone calls SUCCEED AND\n'
  printf 'RETURN EMPTY - list-landing-zones gives None, list-landing-zone-operations gives an\n'
  printf 'empty list. Neither is an error, so an exit code would say nothing, and section 4\n'
  printf 'printed from here would state "the landing zone has never run": a strong claim,\n'
  printf 'wrong, and identical in the output to the true one (Lesson 13).\n\n'
  printf 'SECTION 5 STILL ANSWERS, and that is a property of the design rather than an\n'
  printf 'accident: organizations:DescribeResourcePolicy is granted to the Identity account by\n'
  printf 'the 5.1 delegation itself. ./aws/org-delegation.py is the fuller instrument there.\n\n'
  printf 'Re-run from CloudShell on Management as `AWS Control Tower Admin` through\n'
  printf '`AWSAdministratorAccess`.\n'
fi

# ======================================================================================
h1 "2. The landing zone: status, version, DRIFT - and account AUTO-ENROLLMENT"

if [ "$IS_MGMT" != "yes" ]; then
printf 'SUPPRESSED - this did not run in Management. See section 1: the calls behind this\n'
printf 'section succeed and return empty from a member account, so printing them here would\n'
printf 'manufacture an answer.\n'
else

{
  printf 'FIELD\tVALUE\n'
  printf 'landing zone\t%s\n' "$(printf '%s' "${LZ_ARN:-(unread)}" | mask)"
  printf 'status\t%s\n' "$LZ_STATUS"
  printf 'deployed version\t%s\n' "$LZ_VERSION"
  printf 'latest available\t%s\n' "$LZ_LATEST"
  printf 'DRIFT STATUS\t%s\n' "$DRIFT"
  printf 'remediation types\t%s\n' "$LZ_REMED"
  printf 'account auto-enrollment\t%s\n' "$AUTO_ENROLL"
} | tabulate

printf '\n'
case "$DRIFT" in
  IN_SYNC)
    printf 'IN_SYNC. Read section 6 before recording this as "the delegation is fine": it is\n'
    printf 'the expected answer and it is a WEAK NEGATIVE, because Control Tower compares a\n'
    printf 'closed list of objects it owns and section 3 is where that list is printed.\n' ;;
  DRIFTED)
    printf '!! DRIFTED. This is the answer verification (iii) was written to catch. Do NOT\n'
    printf 'assume the resource policy is the cause - section 3 says what is compared, and\n'
    printf 'the console names the drifted item. An OU moved by hand or an SCP detached from a\n'
    printf 'governed OU produces the same flag.\n' ;;
  *)
    printf 'The drift status could not be read (%s). That is not IN_SYNC - a field that was\n' "$DRIFT"
    printf 'not read and a field that said "no drift" are different answers (Lesson 13).\n' ;;
esac

printf '\n'
printf 'ACCOUNT AUTO-ENROLLMENT - the second switch, and it is a DIFFERENT question from drift.\n'
printf '`remediationTypes` is the landing zone opt-in that makes Control Tower react to an\n'
printf 'AWS Organizations `MoveAccount` event: the moved account inherits the destination OU`s\n'
printf 'baseline and controls, and the source OU`s are removed. Available from landing zone\n'
printf '3.1; this one reports its version two rows above.\n\n'
case "$AUTO_ENROLL" in
  on)
    printf 'ON. An account moved with `organizations move-account` between two REGISTERED OUs is\n'
    printf 're-baselined automatically, with eventual consistency - AWS documents minutes to\n'
    printf 'several hours. Two things it still does NOT do: it does not touch the Account Factory\n'
    printf 'PROVISIONED PRODUCT (its parameters keep the old OU and the old name until somebody\n'
    printf 'updates them), and it does not prevent `Moved member account` drift when the two OUs\n'
    printf 'differ in configuration. So the Control Tower `Update account` path stays the\n'
    printf 'supported one for an Account Factory account - Stage 6b step 3.4 - and this reading\n'
    printf 'is what says the by-hand fallback exists rather than what replaces the step.\n' ;;
  OFF)
    printf '!! OFF - `remediationTypes` is empty, which is the default and the state of every\n'
    printf 'landing zone that never opted in. Moving an account between registered OUs with\n'
    printf 'the AWS Organizations API or console then leaves the SOURCE OU`s baseline and\n'
    printf 'controls attached and raises INHERITANCE DRIFT: the account sits in the new OU\n'
    printf 'carrying the old OU`s Config rules, which is the failure mode Stage 6b step 3.4\n'
    printf 'refuses by using the Control Tower `Update account` path instead. Nothing here\n'
    printf 'needs the switch turned on; it needs the switch READ, so that the reason for\n'
    printf 'taking the console path is a measurement and not a memory.\n' ;;
  *)
    printf 'The field could not be read (%s). That is not "OFF" - an unread field and an empty\n' "$LZ_REMED"
    printf 'array are different answers (Lesson 13). Section 7 says whether the call failed.\n' ;;
esac

fi

# ======================================================================================
h1 "3. What the landing zone declares it manages - the manifest, whole"

if [ "$IS_MGMT" != "yes" ]; then
printf 'SUPPRESSED - see section 1.\n'
else

printf 'THIS IS WHAT MAKES SECTION 2 READABLE. The manifest is what the landing zone is\n'
printf 'CONFIGURED with: governed Regions, the logging and security accounts, retention, the\n'
printf 'access-management setting. Read it for ONE thing - whether anything in it concerns\n'
printf 'organization RESOURCE POLICIES. If nothing does, then IN_SYNC above is silent about\n'
printf 'the 5.1 delegation rather than approving of it.\n\n'
printf 'IT IS NOT THE INVENTORY OF WHAT DRIFT DETECTION COMPARES, and an earlier version of\n'
printf 'this section said it was. The manifest carries NO policy of any kind - not even the\n'
printf 'aws-guardrails-* SCPs Control Tower owns and 1c step 7.7 read one by one. So it\n'
printf 'bounds the CONFIGURATION, not the comparison. That is a narrower claim, and it is\n'
printf 'the one this report is entitled to make.\n\n'

if [ -s "$LZ_JSON" ]; then
  python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))["landingZone"].get("manifest",{}), indent=2, sort_keys=True))' "$LZ_JSON" 2>/dev/null | mask \
    || printf '(the manifest could not be parsed out of the response)\n'
else
  printf '(the landing zone was not read - see section 7)\n'
fi

fi

# ======================================================================================
h1 "4. Operations, and whether any ran AFTER the delegation"

if [ "$IS_MGMT" != "yes" ]; then
printf 'SUPPRESSED - and this is the section the suppression exists for. An empty list read\n'
printf 'from a member account says "the landing zone has never run", which is wrong and looks\n'
printf 'exactly like the true answer. See section 1.\n'
else

printf 'THE STRONGEST EVIDENCE THIS SCRIPT CAN GATHER, and it is stronger than the flag.\n'
printf 'A drift status is a comparison; an OPERATION is the landing zone doing work. An\n'
printf 'UPDATE or RESET that ran AFTER 2026-08-15 - when the resource policy was applied -\n'
printf 'and came back SUCCEEDED is positive evidence that the two coexist. If the newest\n'
printf 'row PREDATES the delegation, that is a different answer and the honest one: the\n'
printf 'landing zone has not yet had occasion to disagree, and the real test arrives with\n'
printf 'the next update rather than here.\n\n'
printf 'The delegation was applied 2026-08-15 and amended (5.1a) 2026-08-16.\n'

show controltower list-landing-zone-operations --max-items 20 --output json

fi

# ======================================================================================
h1 "5. The resource policy - and it answers from Identity too"

{
  printf 'FIELD\tVALUE\n'
  printf 'resource policy\t%s\n' "$RP_STATE"
  printf 'statements with a PrincipalArn condition\t%s\n' "$ARNLIKE_N"
} | tabulate

printf '\n'
if [ "$RP_STATE" = "PRESENT" ]; then
  if [ "$ARNLIKE_N" = "2" ]; then
    printf 'PRESENT, with the condition on exactly TWO statements - which is 5.1a as applied:\n'
    printf 'the two WRITE statements narrowed to the InfrastructureAccess role, the navigation\n'
    printf 'statement deliberately untouched. `DEL-10` reports the same thing from Identity;\n'
    printf './aws/org-delegation.py reports the same thing from the Identity side, with\n'
    printf 'all ten DEL-* checks rather than this one count.\n'
  else
    printf '!! PRESENT, but the PrincipalArn condition is on %s statement(s), not 2.\n' "$ARNLIKE_N"
    printf 'Either the document was changed since 5.1a, or something rewrote it. Compare\n'
    printf 'against the copy in the Stage 2 log before touching anything.\n'
  fi
else
  printf '!! ABSENT. The delegation is gone - which would mean every apply against\n'
  printf 'terraform-live/identity/org-policies/ now fails, and that the answer to\n'
  printf 'verification (iii) is the bad one. Re-read the Stage 2 log entry for 5.1 before\n'
  printf 'reapplying anything: the document is recorded there in full.\n'
fi

printf '\nThe document is NOT printed here. It carries account ids, it is recorded in full in\n'
printf 'docs/log/log-stage-02-terraform-foundation.md, and ./aws/org-delegation.py reads it\n'
printf 'from the Identity side with all ten DEL-* checks. This section answers "is it still\n'
printf 'there, and is it still narrowed" - not "what does it say".\n'

# ======================================================================================
h1 "6. How to read all of this - and what it does NOT say"

printf 'VERIFICATION (iii) IS ANSWERED BY READING, NOT BY TESTING, AND THE DIFFERENCE IS\n'
printf 'WORTH STATING RATHER THAN GLOSSING. The strong test is to make the landing zone\n'
printf 're-evaluate - `update-landing-zone` or `reset-landing-zone` - and see whether the\n'
printf 'delegation survives it. Both are writes on the landing zone, both are slow and hard\n'
printf 'to undo, and neither is a measurement anybody should take to answer a question. So\n'
printf 'the failing case cannot be produced here (Lesson 22), and what this report gives is:\n\n'
printf '  section 2   the flag Control Tower publishes            - a WEAK negative\n'
printf '  section 3   what that flag is actually comparing        - what makes it weak\n'
printf '  section 4   whether the landing zone has RUN since      - the positive evidence\n'
printf '  section 5   whether the document survived whatever ran  - the direct check\n\n'
printf 'THE PRECEDENT THAT SHAPES THE EXPECTATION: 1c attached ten customer policy documents\n'
printf 'across four types and none of them raised drift, because a customer SCP is not\n'
printf 'an object Control Tower owns. A resource policy on the organization is a newer object\n'
printf 'class and the same argument is expected to hold - but "expected to hold" is a\n'
printf 'prediction, and this report is what turns it into a dated reading.\n\n'
printf 'WHEN TO RE-RUN: after any landing-zone update, after any Control Tower version\n'
printf 'upgrade (compare the two version fields of section 2), and around Stage 6b`s rename\n'
printf 'and OU move - which is an ACCOUNT UPDATE on that one account, and therefore the event\n'
printf '1b verification (vi) has been waiting on. It is NOT 1d (iv) or 1d (xiv): those wait on\n'
printf 'an update to LOG ARCHIVE and to the Security OU`s accounts respectively, and an update\n'
printf 'to a member in Interactive re-baselines neither (corrected 2026-09-06 - the earlier\n'
printf 'wording named all three, which is one account`s event borrowed for two others).\n'
printf 'There is no `Staging` vend to re-run at: the quota was refused and Stage 6b makes the\n'
printf 'account by renaming `Development` instead.\n\n'
printf 'HOW AUTO-ENROLLMENT WOULD BE TURNED ON - NOT PERFORMED HERE, and the same line every\n'
printf 'script in this folder draws. It is `update-landing-zone` with the manifest re-sent\n'
printf 'unchanged and `--remediation-types INHERITANCE_DRIFT` added, which re-runs the landing\n'
printf 'zone across every governed account: a write, slow, and the exact operation section 6\n'
printf 'above declines to perform as a measurement. Stage 6b does NOT need it - step 3.4 takes\n'
printf 'the Control Tower `Update account` path, which re-baselines the account whether or not\n'
printf 'the switch is on. If it is ever wanted for its own sake, it is a decision with a\n'
printf 'stage, not a line in a report; note that it does not resolve inheritance drift\n'
printf 'retroactively - only accounts moved AFTER the opt-in are covered.\n'

# ======================================================================================
h1 "7. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'A FAILED CALL IS NOT A CLEAN READING. Anything above that depended on one of these\n'
  printf 'is unread, not fine.\n\n'
  mask <"$ERRORS"
else
  printf 'none - every call in this report returned.\n'
fi

printf '\n'
}

# A run from the wrong account must not clobber a good report. Sections 2-4 are suppressed
# there, so writing the file would replace a real Management reading with one that answers
# nothing, under a file name that still says it was the answer. Same rule the auth-failure
# path above states.
if [ "$IS_MGMT" = "yes" ]; then
  main | mask | tee "$OUT"
else
  main | mask
fi

note ""
if [ "$IS_MGMT" = "yes" ]; then
  note "report written to $OUT"
else
  note "NOT written to $OUT - the previous report, if any, is left untouched."
fi
if [ -s "$ERRORS" ]; then
  note "SOME CALLS FAILED - see section 7."
  exit 1
fi
if [ "$IS_MGMT" != "yes" ]; then
  # Not 0. Sections 2-4 were suppressed, so this run did not answer verification (iii), and a
  # zero exit is how a report that says nothing gets filed as one that says everything is fine.
  note "this did NOT run in the Management account - sections 2-4 are suppressed."
  note "re-run from CloudShell on Management as \`AWS Control Tower Admin\`."
  exit 2
fi
exit 0
