#!/usr/bin/env bash
#
# org-delegation.sh - can the Identity account manage the ORGANIZATION'S POLICIES, and
# exactly which of them? The standing instrument for INT-20.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/org-delegation.sh                 # awsds-infra-identity
#             ./aws/org-delegation.sh -               # no --profile: CloudShell on
#                                                     # MANAGEMENT, as CT Admin
#   writes:   aws/output/org-delegation.txt   (untracked - see .gitignore)
#   reads:    organizations:DescribeResourcePolicy, DescribeOrganization, ListRoots,
#             ListOrganizationalUnitsForParent, ListPoliciesForTarget, DescribePolicy,
#             sts:GetCallerIdentity. It never creates, updates or deletes anything.
#   exits:    0 the report was produced | 1 a call failed unexpectedly | 2 a check FAILED
#
# WHY THIS EXISTS. Permission sets reach the Identity account through the IAM Identity
# Center delegated administrator, which Stage 1b step 1 proved. SCPs, RCPs, tag policies and
# declarative policies DO NOT: they are AWS Organizations objects, and reaching them needs a
# second, different mechanism - a RESOURCE-BASED DELEGATION POLICY on the organization
# (organizations:PutResourcePolicy), written from Management. Nothing before Stage 2 step 5.1
# creates it, and INT-20 records the plausible failure as "the delegation works and still
# cannot touch a root attachment". Since Stage 1c put SIX OF THE TEN DOCUMENTS ON THE ROOT,
# that outcome costs most of terraform-live/identity/org-policies/ rather than a corner of
# it - which is why Stage 2 answers this before writing a line of that slice.
#
# THE TRAP THIS SCRIPT IS BUILT AROUND, and it is the reason section 4 exists as a warning
# rather than as a result. ORGANIZATIONS *READS* ALREADY ANSWER FROM THE IDENTITY ACCOUNT
# WITHOUT ANY POLICY DELEGATION - measured 2026-08-12/13 (Stage 1c verification (x)), because
# a delegated administrator for ANY service may read the organization. So `describe-policy`
# succeeding here proves nothing about the policy delegation: it returns the same answer
# before and after step 5.1, which is Lesson 13 exactly. THE ONLY DECISIVE READ IS THE
# DELEGATION DOCUMENT ITSELF, and the only decisive test is a WRITE - which this script
# deliberately does not perform. That line is the same one aws/probes/ draws: a measurement
# that changes a policy is a human act on Management.
#
# So what this script decides is SCOPE, by reading (Lesson 22): does a delegation exist, does
# it name this account, which policy TYPES does it admit, and - the half that fails silently -
# does its Resource list reach the ROOT and the NESTED OUs. AWS documents that naming a single
# OU "excludes child OUs and accounts under child OUs", and this organization is two levels
# deep (D23: `Sandboxes` under `Interactive`).
#
# IDENTITY. Default profile is `awsds-infra-identity` - the account the delegation is FOR,
# which is the only place the answer means anything. The `-` fallback is CloudShell on
# Management as `AWS Control Tower Admin`, and it answers a different question: it shows the
# document from the side that wrote it, and it always succeeds, so a green run there says
# nothing about whether Identity can use it. Prefer the profile.

set -uo pipefail

PROFILE="${1:-${AWSDS_PROFILE:-awsds-infra-identity}}"
REGION="us-west-2"
SSO_SESSION="awsds"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/org-delegation.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/org-delegation.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"
CHECKS="$TMP/checks.tsv"     # RESULT <tab> ID <tab> WHAT <tab> DETAIL
TARGETS="$TMP/targets.tsv"   # CLASS <tab> NODE_NAME <tab> NODE_ID <tab> TYPE <tab> PID <tab> PNAME
RESPOL="$TMP/respol.json"
: >"$ERRORS"; : >"$CHECKS"; : >"$TARGETS"

if [ "$PROFILE" = "-" ] || [ "$PROFILE" = "none" ]; then
  PROFILE_OPT=""
  PROFILE_LABEL="(none - ambient credentials, e.g. CloudShell)"
else
  PROFILE_OPT="--profile $PROFILE"
  PROFILE_LABEL="$PROFILE"
fi

POLICY_TYPES="SERVICE_CONTROL_POLICY RESOURCE_CONTROL_POLICY TAG_POLICY DECLARATIVE_POLICY_EC2"

# ------------------------------------------------------------------------------ helpers

note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

show() { printf '\n$ aws %s\n\n' "$*"; }

aws_() { command aws $PROFILE_OPT --region "$REGION" "$@" </dev/null; }

RUN_OUT=""; RUN_STATUS=0; RUN_ERR=""
run() {
  RUN_OUT=$(aws_ "$@" 2>"$TMP/stderr")
  RUN_STATUS=$?
  RUN_ERR=$(cat "$TMP/stderr")
  if [ "$RUN_STATUS" -ne 0 ]; then
    RUN_OUT=""
  fi
}
# run(), and log the failure. Used everywhere except the two calls whose failure is an
# ANSWER rather than an error - section 2's, which is the whole point of this script.
runlog() {
  run "$@"
  if [ "$RUN_STATUS" -ne 0 ]; then
    printf 'aws %s\n    %s\n' "$*" "$(printf '%s' "$RUN_ERR" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
  fi
}

tabulate() { column -t -s $'\t'; }
check() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >>"$CHECKS"; }

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

CALLER_ACCT=$(command aws $PROFILE_OPT --region "$REGION" \
                sts get-caller-identity --query 'Account' --output text 2>/dev/null)

# --------------------------------------------------------------- the delegation document

note "reading the organization resource policy..."

# The ONE call whose failure is the answer. Three outcomes have to stay distinguishable:
#   - a document                       -> a delegation exists; sections 3 and 5 read it
#   - ResourcePolicyNotFoundException  -> no delegation. Step 5.1 has not run. NOT a denial
#   - AccessDenied / anything else     -> the read itself was refused, which is a THIRD state
# Collapsing the last two is the mistake this script exists to make impossible.
run organizations describe-resource-policy --query 'ResourcePolicy.Content' --output text
RESPOL_STATUS="$RUN_STATUS"
RESPOL_ERR="$RUN_ERR"
RESPOL_STATE="unknown"
if [ "$RESPOL_STATUS" -eq 0 ] && [ -n "$RUN_OUT" ]; then
  printf '%s\n' "$RUN_OUT" >"$RESPOL"
  RESPOL_STATE="present"
elif printf '%s' "$RESPOL_ERR" | grep -qi 'ResourcePolicyNotFound'; then
  RESPOL_STATE="absent"
elif printf '%s' "$RESPOL_ERR" | grep -qi 'AccessDenied\|not authorized\|explicit deny'; then
  RESPOL_STATE="denied"
else
  RESPOL_STATE="error"
  printf 'aws organizations describe-resource-policy\n    %s\n' \
    "$(printf '%s' "$RESPOL_ERR" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
fi

# ------------------------------------------------------ what is attached, and to what class

note "finding the documents a write would have to reach..."

runlog organizations list-roots --query 'Roots[0].[Name,Id]' --output text
ROOT_NAME=$(printf '%s' "$RUN_OUT" | cut -f1)
ROOT_ID=$(printf '%s' "$RUN_OUT" | cut -f2)

runlog organizations describe-organization \
    --query 'Organization.[Id,MasterAccountId]' --output text
ORG_ID=$(printf '%s' "$RUN_OUT" | cut -f1)
MGMT_ID=$(printf '%s' "$RUN_OUT" | cut -f2)

collect_target() {   # $1 = CLASS (ROOT|OU), $2 = node name, $3 = node id
  local class="$1" nname="$2" nid="$3" ptype
  for ptype in $POLICY_TYPES; do
    runlog organizations list-policies-for-target --target-id "$nid" \
        --filter "$ptype" --query 'Policies[].[Id,Name]' --output text
    [ -n "$RUN_OUT" ] || continue
    printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r pid pname; do
      [ -n "${pid:-}" ] || continue
      case "$pname" in FullAWSAccess|RCPFullAWSAccess) continue ;; esac
      case "$pname" in aws-guardrails-*) continue ;;   # Control Tower's own - never ours
      esac
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$class" "$nname" "$nid" "$ptype" "$pid" "$pname" \
        >>"$TARGETS"
    done
  done
}

if [ -n "${ROOT_ID:-}" ]; then
  collect_target ROOT "$ROOT_NAME" "$ROOT_ID"
  # breadth-first: `Sandboxes` is at depth 2, and a walk written for depth 1 misses it
  # silently - which is the same nesting the delegation's Resource list has to survive.
  QUEUE="$TMP/queue"; NEXT="$TMP/next"
  printf '%s\n' "$ROOT_ID" >"$QUEUE"
  while [ -s "$QUEUE" ]; do
    : >"$NEXT"
    while read -r parent_id; do
      [ -n "${parent_id:-}" ] || continue
      runlog organizations list-organizational-units-for-parent \
          --parent-id "$parent_id" --query 'OrganizationalUnits[].[Name,Id]' --output text
      [ -n "$RUN_OUT" ] || continue
      printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r nname nid; do
        [ -n "${nid:-}" ] || continue
        printf '%s\n' "$nid" >>"$NEXT"
        printf '%s\t%s\n' "$nname" "$nid" >>"$TMP/ous.tsv"
      done
    done <"$QUEUE"
    mv "$NEXT" "$QUEUE"
  done
  if [ -f "$TMP/ous.tsv" ]; then
    while IFS=$'\t' read -r nname nid; do
      [ -n "${nid:-}" ] || continue
      collect_target OU "$nname" "$nid"
    done <"$TMP/ous.tsv"
  fi
fi

# ------------------------------------------------------------- decompose the delegation

# Reading the document is the instrument (Lesson 22). What is checked is SCOPE, in the three
# places it fails silently: the policy TYPES it admits, whether the Resource list reaches the
# ROOT, and whether it reaches OUs AT ANY DEPTH rather than one named OU.
cat >"$TMP/decompose.py" <<'PY'
import json, sys

path, org_id, root_id, identity_acct = sys.argv[1:5]
doc = json.load(open(path))
stmts = doc.get("Statement", [])
if isinstance(stmts, dict):
    stmts = [stmts]

def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

actions, resources, principals, conds = set(), set(), set(), []
for s in stmts:
    if s.get("Effect") != "Allow":
        continue
    for a in as_list(s.get("Action")):
        actions.add(a)
    for r in as_list(s.get("Resource")):
        resources.add(r)
    p = s.get("Principal")
    if isinstance(p, dict):
        for v in p.values():
            for x in as_list(v):
                principals.add(x)
    else:
        for x in as_list(p):
            principals.add(x)
    if s.get("Condition"):
        conds.append(s["Condition"])

def covers(action):
    for a in actions:
        if a in ("*", "organizations:*"):
            return True
        if a == action:
            return True
        if a.endswith("*") and action.startswith(a[:-1]):
            return True
    return False

# The write half Stage 2 step 5.1 requires, and the two that must be ABSENT.
WRITE = ["organizations:CreatePolicy", "organizations:UpdatePolicy",
         "organizations:DeletePolicy", "organizations:AttachPolicy",
         "organizations:DetachPolicy"]
FORBID = ["organizations:EnablePolicyType", "organizations:DisablePolicyType"]
READ = ["organizations:DescribeOrganization", "organizations:ListRoots",
        "organizations:ListOrganizationalUnitsForParent", "organizations:ListChildren",
        "organizations:ListParents", "organizations:ListAccounts",
        "organizations:ListPolicies", "organizations:ListPoliciesForTarget",
        "organizations:ListTargetsForPolicy", "organizations:ListTagsForResource"]

out = {
    "principals": sorted(principals),
    "resources": sorted(resources),
    "actions": sorted(actions),
    "write_missing": [a for a in WRITE if not covers(a)],
    "read_missing": [a for a in READ if not covers(a)],
    "forbidden_granted": [a for a in FORBID if covers(a)],
    "identity_named": any(identity_acct in p for p in principals) or "*" in principals,
    "wildcard_principal": "*" in principals,
    # Resource coverage, the half that fails silently.
    "root_covered": any(
        r == "*" or root_id in r or (":root/" in r and r.endswith("*")) for r in resources),
    "ou_wildcard": any(
        r == "*" or (":ou/" in r and r.rstrip().endswith("*")) for r in resources),
    "ou_single_named": sorted(
        r for r in resources if ":ou/" in r and not r.rstrip().endswith("*")),
    "policy_type_conditions": sorted({
        v for c in conds
        for op, kv in c.items()
        for k, vals in kv.items() if k.lower() == "organizations:policytype"
        for v in (vals if isinstance(vals, list) else [vals])
    }),
    "n_statements": len(stmts),
}
json.dump(out, sys.stdout, indent=2, sort_keys=True)
PY

DEC="$TMP/decomposed.json"
if [ "$RESPOL_STATE" = "present" ]; then
  python3 "$TMP/decompose.py" "$RESPOL" "${ORG_ID:-}" "${ROOT_ID:-}" "${CALLER_ACCT:-}" \
    >"$DEC" 2>>"$ERRORS" || RESPOL_STATE="unparseable"
fi

jq_() { python3 -c "import json,sys;d=json.load(open('$DEC'));v=d.get('$1');print(json.dumps(v) if isinstance(v,(list,dict)) else v)" 2>/dev/null; }

# ------------------------------------------------------------------------------- checks

case "$RESPOL_STATE" in
  absent)
    check note "DEL-1" "an organization resource policy exists" \
      "NO - ResourcePolicyNotFoundException. This is the EXPECTED answer before Stage 2 step 5.1, and it is NOT a denial: the call was authorized and returned 'there is none'. Every check below is vacuous until it runs."
    ;;
  denied)
    check fail "DEL-1" "an organization resource policy exists" \
      "UNKNOWN - the READ itself was refused, so this run cannot tell 'no delegation' from 'a delegation this account may not see'. Re-run from CloudShell on Management: ./aws/org-delegation.sh -"
    ;;
  present)
    check pass "DEL-1" "an organization resource policy exists" \
      "yes - $(jq_ n_statements) statement(s); the document is in section 2"
    ;;
  unparseable)
    check fail "DEL-1" "an organization resource policy exists" \
      "a document was returned and did not parse as JSON - see section 6"
    ;;
  *)
    check fail "DEL-1" "an organization resource policy exists" \
      "the call failed for a reason that is neither 'not found' nor a denial - see section 6"
    ;;
esac

if [ "$RESPOL_STATE" = "present" ]; then
  if [ "$(jq_ wildcard_principal)" = "True" ]; then
    check fail "DEL-2" "the principal is this account, not everyone" \
      "Principal is \"*\" - every account in the organization can manage every policy in it, including Control Tower's own guardrails. This is wider than Stage 2 step 5.1 designs and wider than INT-20 accepts."
  elif [ "$(jq_ identity_named)" = "True" ]; then
    check pass "DEL-2" "the principal is this account, not everyone" \
      "the calling account is named in the Principal"
  else
    check fail "DEL-2" "the principal is this account, not everyone" \
      "the calling account is NOT in the Principal: $(jq_ principals). Either this run is in the wrong account, or the delegation was written for a different one."
  fi

  MISSING_W=$(jq_ write_missing)
  if [ "$MISSING_W" = "[]" ]; then
    check pass "DEL-3" "the write half is granted" "Create/Update/Delete/Attach/DetachPolicy all covered"
  else
    check fail "DEL-3" "the write half is granted" \
      "missing: $MISSING_W. terraform apply against identity/org-policies/ fails on the first of these it needs."
  fi

  MISSING_R=$(jq_ read_missing)
  if [ "$MISSING_R" = "[]" ]; then
    check pass "DEL-4" "the read half is granted" "every list/describe Stage 2 step 5.1 names is covered"
  else
    check note "DEL-4" "the read half is granted" \
      "missing from the delegation: $MISSING_R - which may still WORK, because a delegated administrator for any service may read the organization anyway (see section 4). Grant them regardless: relying on the other delegation makes this one's scope a fiction."
  fi

  FORB=$(jq_ forbidden_granted)
  if [ "$FORB" = "[]" ]; then
    check pass "DEL-5" "EnablePolicyType/DisablePolicyType are NOT granted" "correctly absent"
  else
    check fail "DEL-5" "EnablePolicyType/DisablePolicyType are NOT granted" \
      "granted: $FORB. Disabling a policy type on the root DETACHES EVERY POLICY OF THAT TYPE AT ONCE. Nothing in this design needs it after 1c step 7.2."
  fi

  if [ "$(jq_ root_covered)" = "True" ]; then
    check pass "DEL-6" "the Resource list reaches the ROOT" \
      "yes - and this is the one that decides the size of Stage 2: six of the ten documents are attached to the root"
  else
    check fail "DEL-6" "the Resource list reaches the ROOT" \
      "NO. The root ARN (root/$ORG_ID/$ROOT_ID) is not covered by: $(jq_ resources). Six of the ten attached documents are on the root, so identity/org-policies/ can hold at most the four per-OU ones. This is INT-20's predicted outcome, not a mistake to fix by widening blindly."
  fi

  if [ "$(jq_ ou_wildcard)" = "True" ]; then
    check pass "DEL-7" "the Resource list reaches NESTED OUs" \
      "a wildcard OU ARN is present, so depth 2 (Sandboxes under Interactive) is covered"
  else
    SINGLE=$(jq_ ou_single_named)
    check fail "DEL-7" "the Resource list reaches NESTED OUs" \
      "no wildcard OU ARN. AWS documents that naming a single OU 'excludes child OUs and accounts under child OUs', and this organization is two levels deep (D23). Named OUs: $SINGLE"
  fi

  PT=$(jq_ policy_type_conditions)
  if [ "$PT" = "[]" ]; then
    check note "DEL-8" "scoped by organizations:PolicyType" \
      "no PolicyType condition - the delegation admits EVERY policy type, present and future. Wider than Stage 2 step 5.1 designs, and it is a Deny-by-omission that will not announce itself."
  else
    check pass "DEL-8" "scoped by organizations:PolicyType" "$PT"
  fi
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'Can the Identity account manage the organization POLICIES - INT-20\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'produced  : aws/org-delegation.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Where this ran - read it FIRST\n'
printf '  2. The organization resource policy, and which of three states it is in\n'
printf '  3. What the delegation grants, decomposed - the checks\n'
printf '  4. WHAT THIS SCRIPT CANNOT ANSWER, and why a green run is not a green delegation\n'
printf '  5. The documents a write would have to reach, by target class\n'
printf '  6. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - SECTION 4 IS NOT A DISCLAIMER, IT IS THE MAIN FINDING. Organizations READS\n'
printf '    already answer from the Identity account with no policy delegation at all\n'
printf '    (Stage 1c verification (x)), so nothing that merely reads is evidence here.\n'
printf '    What this script decides is SCOPE, by reading the delegation document.\n'
printf '  - THREE STATES, NOT TWO, in section 2. "No delegation" and "the read was denied"\n'
printf '    are different facts and only one of them is the expected pre-5.1 answer.\n'
printf '  - A `note` IN SECTION 3 BEFORE STEP 5.1 IS NOT A FAILURE. Until the delegation\n'
printf '    exists there is nothing to check, and the report says that rather than passing.\n'

# ======================================================================================
h1 "1. Where this ran - read it FIRST"

printf 'Every other section is about whatever account answered, so this is the section that\n'
printf 'says whether the answer is about the right one. The delegation is FOR the Identity\n'
printf 'account; a run from Management shows the same document from the side that wrote it\n'
printf 'and always succeeds, which answers a different question.\n\n'

{
  printf 'FIELD\tVALUE\n'
  printf 'caller ARN\t%s\n' "$CALLER"
  printf 'account id\t%s\n' "${CALLER_ACCT:-(unknown)}"
  printf 'management account\t%s\n' "${MGMT_ID:-(unread)}"
  printf 'organization\t%s\n' "${ORG_ID:-(unread)}"
  printf 'root\t%s (%s)\n' "${ROOT_NAME:-(unread)}" "${ROOT_ID:-}"
} | tabulate

printf '\n'
if [ -n "${MGMT_ID:-}" ] && [ "${CALLER_ACCT:-}" = "$MGMT_ID" ]; then
  printf 'THIS RAN IN THE MANAGEMENT ACCOUNT. Management is outside every SCP and owns the\n'
  printf 'organization, so section 3 measures the DOCUMENT and not the reach of the delegated\n'
  printf 'administrator. Re-run as ./aws/org-delegation.sh to get the answer that matters.\n'
else
  printf 'This ran in a member account, which is where the delegation has to work.\n'
fi

# ======================================================================================
h1 "2. The organization resource policy"

show "organizations describe-resource-policy"

case "$RESPOL_STATE" in
  present)
    printf 'STATE: PRESENT - a delegation exists.\n\n'
    python3 -m json.tool "$RESPOL" 2>/dev/null || cat "$RESPOL"
    ;;
  absent)
    printf 'STATE: ABSENT - ResourcePolicyNotFoundException.\n\n'
    printf 'This is the EXPECTED answer before Stage 2 step 5.1, and it is an ANSWER rather\n'
    printf 'than a failure: the call was authorized and reported that there is no such policy.\n'
    printf 'Keeping this apart from a denial is the whole reason this section prints a state\n'
    printf 'rather than an empty block - a listing that returns nothing and a listing that was\n'
    printf 'refused look identical otherwise (Lesson 13).\n\n'
    printf 'raw error: %s\n' "$(printf '%s' "$RESPOL_ERR" | head -n 2 | tr '\n' ' ')"
    ;;
  denied)
    printf 'STATE: DENIED - the READ itself was refused.\n\n'
    printf 'This run cannot tell "there is no delegation" from "there is one and this account\n'
    printf 'may not see it". Re-run from CloudShell on Management as AWS Control Tower Admin:\n'
    printf '  ./aws/org-delegation.sh -\n\n'
    printf 'raw error: %s\n' "$(printf '%s' "$RESPOL_ERR" | head -n 2 | tr '\n' ' ')"
    ;;
  *)
    printf 'STATE: %s - see section 6.\n\n' "$(printf '%s' "$RESPOL_STATE" | tr '[:lower:]' '[:upper:]')"
    printf 'raw error: %s\n' "$(printf '%s' "$RESPOL_ERR" | head -n 2 | tr '\n' ' ')"
    ;;
esac

# ======================================================================================
h1 "3. What the delegation grants, decomposed"

printf 'Reading the document is the instrument, because the principal that would exercise it\n'
printf 'is the one running Terraform and attempting the call is a write (Lesson 22). Each\n'
printf 'check below is a place the delegation fails SILENTLY - it attaches, it looks right,\n'
printf 'and the apply is refused on the one document nobody tested.\n\n'

{
  printf 'RESULT\tID\tWHAT\tDETAIL\n'
  awk -F'\t' '$1=="fail"' "$CHECKS"
  awk -F'\t' '$1=="note"' "$CHECKS"
  awk -F'\t' '$1=="pass"' "$CHECKS"
} | tabulate

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
printf '\n%s check(s) FAILED.\n' "$NFAIL"

if [ "$RESPOL_STATE" = "present" ]; then
  printf '\nThe raw decomposition, so any row above can be re-derived:\n\n'
  cat "$DEC"
fi

# ======================================================================================
h1 "4. WHAT THIS SCRIPT CANNOT ANSWER"

printf 'TWO THINGS, AND THE FIRST IS THE REASON THE SECOND MATTERS.\n\n'
printf '1. A SUCCESSFUL READ IS NOT EVIDENCE OF THIS DELEGATION. Organizations reads already\n'
printf '   answer from the Identity account without any policy delegation - measured in Stage\n'
printf '   1b step 4 and Stage 1c verification (x), because a delegated administrator for ANY\n'
printf '   service may read the organization. ./aws/org-policies.sh runs green from here today\n'
printf '   and always has. So `describe-policy` succeeding proves nothing, and a script built\n'
printf '   on it would return OK before AND after step 5.1 - which is not a verification\n'
printf '   (Lesson 13). That is why section 3 reads the delegation document instead.\n\n'
printf '2. THE DECISIVE TEST IS A WRITE, AND IT IS NOT PERFORMED HERE. Stage 2 step 5.0 names\n'
printf '   it precisely: `organizations update-policy` against `awsds-org-tag-policy` with its\n'
printf '   own current content - the least dangerous document in the organization, because its\n'
printf '   enforcement is off (`enforced_for` unset), so an identical rewrite changes nothing\n'
printf '   even if it lands somewhere nobody expected. NOT the baseline SCP. That call belongs\n'
printf '   to a human, for the same reason aws/probes/ is fenced off from the rest of aws/: a\n'
printf '   measurement that can change a policy is run deliberately, not to gather information.\n\n'
printf 'WHAT A FAILED DEL-6 MEANS, since it is the outcome INT-20 predicts. It does not mean\n'
printf 'the delegation is broken. It means terraform-live/identity/org-policies/ holds the four\n'
printf 'per-OU documents and the six on the root stay console-managed - Stage 2 step 5.0 records\n'
printf 'that as a scope decision rather than as a defect, and step 9.2 keeps all ten in scope by\n'
printf 'reading policies/*.json regardless of who manages them.\n'

# ======================================================================================
h1 "5. The documents a write would have to reach"

printf 'This project`s documents only - Control Tower`s aws-guardrails-* are filtered out,\n'
printf 'and so are FullAWSAccess and RCPFullAWSAccess. THE CLASS COLUMN IS THE POINT: ROOT\n'
printf 'rows are the ones DEL-6 decides, OU rows the ones DEL-7 decides.\n\n'

if [ -s "$TARGETS" ]; then
  {
    printf 'CLASS\tNODE\tNODE ID\tTYPE\tPOLICY ID\tPOLICY NAME\n'
    sort "$TARGETS"
  } | tabulate
  printf '\n'
  NROOT=$(awk -F'\t' '$1=="ROOT"' "$TARGETS" | wc -l | tr -d ' ')
  NOU=$(awk -F'\t' '$1=="OU"' "$TARGETS" | wc -l | tr -d ' ')
  printf '%s document(s) on the ROOT, %s on an OU.\n' "$NROOT" "$NOU"
  printf 'Expected shape as of 2026-08-15: 6 on the root, 4 on OUs (AWS_STATE.md).\n'
else
  printf '(nothing found - see section 6)\n'
fi

# ======================================================================================
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  cat "$ERRORS"
  printf '\nIf these are AccessDenied, retry from CloudShell on Management as\n'
  printf '`AWS Control Tower Admin`:  ./aws/org-delegation.sh -\n'
else
  printf 'None. Every call returned successfully.\n'
  printf '(Section 2 reporting ABSENT is not a failure - it is that call answering.)\n'
fi

printf '\nRegenerate with:  ./aws/org-delegation.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 6)"
  exit 1
fi
if [ "$NFAIL" -gt 0 ]; then
  note "wrote $OUT ($NFAIL CHECK(S) FAILED - see section 3)"
  exit 2
fi
if [ "$RESPOL_STATE" = "absent" ]; then
  note "wrote $OUT (NO DELEGATION YET - expected before Stage 2 step 5.1)"
  exit 0
fi
note "wrote $OUT (all checks passed)"
exit 0
