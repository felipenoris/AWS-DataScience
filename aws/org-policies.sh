#!/usr/bin/env bash
#
# org-policies.sh - what governs each node RIGHT NOW, by Sid, with inheritance resolved -
# and the handful of checks that no probe can perform.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/org-policies.sh                   # awsds-infra-identity
#             ./aws/org-policies.sh -                 # no --profile: CloudShell on
#                                                     # MANAGEMENT, as CT Admin
#   writes:   aws/output/org-policies.txt   (untracked - see .gitignore)
#   reads:    organizations:ListRoots, ListOrganizationalUnitsForParent, ListAccountsForParent,
#             DescribeOrganizationalUnit, ListPoliciesForTarget, DescribePolicy,
#             sts:GetCallerIdentity. This script never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# ALL FOUR POLICY TYPES CARRY THEIR ID SINCE 2026-08-15, and the omission it fixes was not
# cosmetic. Section 1 used to list `SERVICE_CONTROL_POLICY` documents with their ids and
# reduce the RCP to a presence check, while the tag policy and the declarative policy did
# not appear at all - so THREE OF THE TEN ATTACHED DOCUMENTS had no id in any snapshot and
# existed only in log/stage-01c-preventive-policies.md. That was survivable while they were
# console-managed and stops being survivable at Stage 2 step 5.5, where the id is the
# argument `terraform import` takes. Reading one filter is also how a read-back reports
# three attached documents as absent (Lesson 13, and 1c nearly did it).
#
# WHY THIS EXISTS, AND HOW IT DIFFERS FROM org-policy-baseline.sh - which walks the same
# tree and would otherwise be a duplicate of it.
#
#   org-policy-baseline.sh is a PREFLIGHT, run once before writing policy (Stage 1c step
#   7.0). It prints whole documents, the quota and the organization's metadata, and its
#   question is "what already exists that I must not duplicate".
#
#   THIS script is a CHECK, run after every policy change and at every vend. It prints no
#   document bodies at all - only `Sid` lists - and its questions are:
#
#     1. what is attached where, condensed enough to diff by eye;
#     2. what actually governs a given ACCOUNT once inheritance is resolved;
#     3. do the statements that no probe can reach still say what they must.
#
# THE THREE THINGS THAT MADE IT WORTH WRITING, each one a lesson that has already cost
# something:
#
#   - LESSON 23 - a managed service owns its artifacts' packing. Control Tower packs per
#     ENABLEMENT, not per control, and inconsistently: the two root-user controls landed in
#     the original guardrail on Policy Test, Workloads and Interactive, and in the REGION
#     document on Identity and Data. So a document cannot be identified by its id or by the
#     job it was created for, and every section here binds to `Sid`.
#
#   - LESSON 22 - a control whose principal the harness cannot produce is verified by
#     READING, not by attempting. `GRRESTRICTROOTUSER` is conditioned on an ARN no Identity
#     Center role can ever match, so the SCP battery is structurally blind to it: it was
#     enabled on Policy Test without `ExemptAssumeRoot` while the battery reported 61 of 61
#     as expected. Section 3 is that class, and it is the reason this script exits 2.
#
#   - D37 - `Sandboxes` carries nothing unless it DIFFERS from `Interactive`, so reading the
#     OU tells you nothing about what governs the accounts inside it. Section 2 resolves the
#     chain so that the answer does not depend on remembering that.
#
# IDENTITY. Every Organizations *policy* read answers from the Identity account as the
# delegated administrator - Stage 1c verification (x), measured 2026-08-13. The `-` fallback
# is CloudShell on Management as `AWS Control Tower Admin`, for the day that stops being true.
# Nothing here needs `controltower:*`, which is the one surface a member account cannot read.

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
OUT="$OUT_DIR/org-policies.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/org-policies.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

NODES="$TMP/nodes.tsv"       # KIND <tab> NAME <tab> ID <tab> ANCESTORS(space-sep, incl self)
ACCTS="$TMP/accounts.tsv"    # NAME <tab> ID <tab> PARENT_ID <tab> ANCESTORS
NODEPOL="$TMP/nodepol.tsv"   # NODE_ID <tab> PID <tab> PNAME   - SCP ONLY
NODERCP="$TMP/nodercp.tsv"   # NODE_ID <tab> PNAME            - RCP names, for CHK-5
NODEALL="$TMP/nodeall.tsv"   # NODE_ID <tab> TYPE <tab> PID <tab> PNAME - all four types
ERRORS="$TMP/errors.txt"
CHECKS="$TMP/checks.tsv"     # RESULT <tab> ID <tab> WHAT <tab> DETAIL
: >"$NODES"; : >"$ACCTS"; : >"$NODEPOL"; : >"$NODERCP"; : >"$NODEALL"; : >"$ERRORS"; : >"$CHECKS"

# NODEPOL stays SCP-only ON PURPOSE. Sections 2, 3 and 4 resolve inheritance and read
# conditions, and only an SCP composes down the tree the way those sections describe: an RCP
# bounds a resource rather than a principal, a tag policy reports instead of denying, and a
# declarative policy is not a permission boundary in either direction. Widening NODEPOL
# would have made section 2's "N statements in force over this account" quietly wrong.
# NODEALL is the inventory; NODEPOL is the ceiling.
POLICY_TYPES="SERVICE_CONTROL_POLICY RESOURCE_CONTROL_POLICY TAG_POLICY DECLARATIVE_POLICY_EC2"

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
h2() { printf '\n--- %s ---\n\n' "$*"; }

# </dev/null so a call made inside a `while read` loop cannot swallow the loop's input.
aws_() { command aws $PROFILE_OPT --region "$REGION" "$@" </dev/null; }

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

# record a check result: pass|fail|note, an id, what was checked, the detail
check() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >>"$CHECKS"; }

# One statement per line: SID <tab> compact JSON of everything else in the statement.
# Binding to the Sid is the whole point (Lesson 23); the second column is what the
# read-only checks in section 3 grep, because they are about conditions.
cat >"$TMP/stmt.py" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
stmts = doc.get("Statement", [])
if isinstance(stmts, dict):
    stmts = [stmts]
for s in stmts:
    sid = s.get("Sid", "(no Sid)")
    rest = {k: v for k, v in s.items() if k != "Sid"}
    print(sid + "\t" + json.dumps(rest, separators=(",", ":"), sort_keys=True))
PY

# fetch a policy document once, cache it, and emit its statement lines
POL_OK=0
policy_stmts() {   # $1 = policy id -> prints SID <tab> REST, sets POL_OK
  local pid="$1" f="$TMP/pol-$pid.json" s="$TMP/stmt-$pid.tsv"
  POL_OK=0
  if [ ! -s "$s" ]; then
    if [ ! -s "$f" ]; then
      run organizations describe-policy --policy-id "$pid" --query 'Policy.Content' --output text
      [ -n "$RUN_OUT" ] || return 1
      printf '%s\n' "$RUN_OUT" >"$f"
    fi
    python3 "$TMP/stmt.py" "$f" >"$s" 2>>"$ERRORS" || return 1
  fi
  POL_OK=1
  cat "$s"
}

# The two wrappers below exist because POL_OK is set inside `policy_stmts`, and a caller
# that reads it through `$(...)` gets the PARENT's stale value - the subshell's assignment
# never comes back. So anything used from a command substitution has to answer with its
# own output rather than with a flag. The per-policy cache is a file, so it survives the
# subshell perfectly well; only the variable does not.
# NOTE the join: BSD `paste -sd ', '` reads that as a LIST of delimiters used in rotation,
# so it alternates comma and space instead of writing ", " between items. awk joins.
sids_of() {        # $1 = policy id -> "SID, SID, ..."  or the unreadable marker
  local out
  out=$(policy_stmts "$1" | cut -f1 | awk '{printf "%s%s", sep, $0; sep=", "}')
  if [ -n "$out" ]; then printf '%s' "$out"
  else printf '(document unreadable - see section 5)'; fi
}
nstmts_of() { policy_stmts "$1" | wc -l | tr -d ' '; }

# WHAT PLAYS THE PART OF A `Sid` DIFFERS BY TYPE, and section 1 lists all four since
# 2026-08-15. This is deliberately the same extraction as
# terraform-live/identity/org-policies/check-index.sh, and for the same reason: the property
# worth printing is "what entries does this document contain", and a type nobody taught the
# script about is named rather than skipped - a listing that silently drops a document is
# exactly the omission this section was widened to fix.
cat >"$TMP/entries.py" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
if "Statement" in doc:                       # SCP and RCP: the IAM grammar
    stmts = doc["Statement"]
    if isinstance(stmts, dict):
        stmts = [stmts]
    out = [s.get("Sid", "(no Sid)") for s in stmts]
elif "tags" in doc:                          # tag policy: one entry per tag key
    out = [v["tag_key"]["@@assign"] for v in doc["tags"].values()]
elif "ec2_attributes" in doc:                # declarative policy: one per attribute
    out = list(doc["ec2_attributes"].keys())
else:
    out = ["(unrecognised document - no Statement, tags or ec2_attributes key)"]
print(", ".join(out))
PY

entries_of() {     # $1 = policy id -> "ENTRY, ENTRY, ..."  or the unreadable marker
  local pid="$1" f="$TMP/pol-$pid.json" out
  if [ ! -s "$f" ]; then
    run organizations describe-policy --policy-id "$pid" --query 'Policy.Content' --output text
    [ -n "$RUN_OUT" ] || { printf '(document unreadable - see section 5)'; return 0; }
    printf '%s\n' "$RUN_OUT" >"$f"
  fi
  out=$(python3 "$TMP/entries.py" "$f" 2>>"$ERRORS")
  if [ -n "$out" ]; then printf '%s' "$out"
  else printf '(document unreadable - see section 5)'; fi
}

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

# ------------------------------------------------------------------- collect the tree

note "walking the OU tree..."

run organizations list-roots --query 'Roots[0].[Name,Id]' --output text
ROOT_NAME=$(printf '%s' "$RUN_OUT" | cut -f1)
ROOT_ID=$(printf '%s' "$RUN_OUT" | cut -f2)
if [ -z "${ROOT_ID:-}" ]; then
  note "could not read the organization root - see the failures section of $OUT"
  printf 'FATAL: organizations list-roots returned nothing.\n' >"$OUT"
  cat "$ERRORS" >>"$OUT"
  exit 1
fi
printf 'ROOT\t%s\t%s\t%s\n' "$ROOT_NAME" "$ROOT_ID" "$ROOT_ID" >>"$NODES"

# breadth-first, depth-agnostic: `Sandboxes` sits at depth 2 and a walk written for
# depth 1 would miss it silently (D23, D34).
QUEUE="$TMP/queue"; NEXT="$TMP/next"
printf '%s\t%s\n' "$ROOT_ID" "$ROOT_ID" >"$QUEUE"
while [ -s "$QUEUE" ]; do
  : >"$NEXT"
  while IFS=$'\t' read -r parent_id parent_anc; do
    [ -n "${parent_id:-}" ] || continue
    run organizations list-organizational-units-for-parent \
        --parent-id "$parent_id" --query 'OrganizationalUnits[].[Name,Id]' --output text
    [ -n "$RUN_OUT" ] || continue
    printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r name id; do
      [ -n "${id:-}" ] || continue
      printf 'OU\t%s\t%s\t%s %s\n' "$name" "$id" "$parent_anc" "$id" >>"$NODES"
      printf '%s\t%s %s\n' "$id" "$parent_anc" "$id" >>"$NEXT"
    done
  done <"$QUEUE"
  mv "$NEXT" "$QUEUE"
done

note "listing accounts per node..."
while IFS=$'\t' read -r kind name id anc; do
  [ -n "${id:-}" ] || continue
  run organizations list-accounts-for-parent \
      --parent-id "$id" --query 'Accounts[].[Name,Id]' --output text
  [ -n "$RUN_OUT" ] || continue
  printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r aname aid; do
    [ -n "${aid:-}" ] || continue
    printf '%s\t%s\t%s\t%s\n' "$aname" "$aid" "$id" "$anc" >>"$ACCTS"
  done
done <"$NODES"

note "listing attached policies per node, all four types..."
while IFS=$'\t' read -r kind name id anc; do
  [ -n "${id:-}" ] || continue
  for ptype in $POLICY_TYPES; do
    run organizations list-policies-for-target --target-id "$id" \
        --filter "$ptype" --query 'Policies[].[Id,Name]' --output text
    [ -n "$RUN_OUT" ] || continue
    printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r pid pname; do
      [ -n "${pid:-}" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$id" "$ptype" "$pid" "$pname" >>"$NODEALL"
      case "$ptype" in
        SERVICE_CONTROL_POLICY)  printf '%s\t%s\t%s\n' "$id" "$pid" "$pname" >>"$NODEPOL" ;;
        RESOURCE_CONTROL_POLICY) printf '%s\t%s\n'     "$id" "$pname"        >>"$NODERCP" ;;
      esac
    done
  done
done <"$NODES"

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'What governs each node right now - by Sid, with inheritance resolved\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'produced  : aws/org-policies.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Attached per node, all four policy types, with ids - no document bodies\n'
printf '  2. What governs each ACCOUNT, inheritance resolved - SCPs only, see below\n'
printf '  3. The read-only checks - the class no probe can reach\n'
printf '  4. The ceiling at a glance, per OU\n'
printf '  5. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - BIND TO THE Sid, NEVER TO THE POLICY ID OR ITS NAME (Lesson 23). Control Tower\n'
printf '    packs per ENABLEMENT and does it inconsistently across OUs, in THREE measured\n'
printf '    shapes: the root-user controls sit in the original guardrail on `Policy Test`,\n'
printf '    `Workloads` and `Interactive`; in the REGION document on `Identity` and `Data`;\n'
printf '    and on `Security` the two enablements split across BOTH documents at once - a\n'
printf '    new one for the Region control, the pre-existing AWS guardrail for the root\n'
printf '    ones. "The region policy" is not a stable way to refer to anything.\n'
printf '  - SECTION 3 IS THE POINT OF THIS SCRIPT. Those statements are invisible to the\n'
printf '    SCP battery in BOTH directions, because every principal this project can obtain\n'
printf '    is an Identity Center role (Lesson 22). A green battery says nothing about them,\n'
printf '    and a FAIL here is a real defect however clean ./aws/probes/scp-battery.sh ran.\n'
printf '  - SECTION 1 LISTS ALL FOUR TYPES; SECTION 2 RESOLVES ONLY SCPs, and that is not an\n'
printf '    omission. Only an SCP composes down the tree as a ceiling over a principal. An\n'
printf '    RCP bounds a RESOURCE, a tag policy REPORTS rather than denying (enforced_for is\n'
printf '    unset here), and a declarative policy sets a service attribute rather than an\n'
printf '    authorization boundary. Folding them into "N statements in force" would produce\n'
printf '    a number that is confidently wrong.\n'
printf '  - AN OU ROW SAYING "nothing attached" IS NOT AN UNGOVERNED OU. `Sandboxes` carries\n'
printf '    nothing by decision (D37) and is fully governed by inheritance - section 2 is\n'
printf '    where that question is actually answered, per account.\n'
printf '  - This is a point-in-time snapshot, not a source of truth. Regenerate rather than\n'
printf '    trusting a stale copy; expectations live in AWS_STATE.md, intent in plan/.\n'

# ======================================================================================
h1 "1. Attached per node, all four policy types, with ids"

printf 'FullAWSAccess and RCPFullAWSAccess are omitted here - they allow everything and\n'
printf 'their presence is checked in section 4 instead. What is left is the ceiling.\n'
printf '\n'
printf 'THE ID IN BRACKETS IS THE ONLY PLACE OUTSIDE THE 1c LOG THAT CARRIES IT, and it is\n'
printf 'what Stage 2 step 5.5 passes to `terraform import`. Bind your READING to the entry\n'
printf 'names (Lesson 23); use the id as an argument, never as a name for the document.\n'
printf 'The entry column means something different per type, on purpose: `Sid`s for an SCP\n'
printf 'or an RCP, tag KEYS for a tag policy, ATTRIBUTE names for a declarative policy.\n'

while IFS=$'\t' read -r kind name id anc; do
  [ -n "${id:-}" ] || continue
  h2 "$kind $name  ($id)"
  FOUND=0
  for ptype in $POLICY_TYPES; do
    TFOUND=0
    while IFS=$'\t' read -r nid ntype pid pname; do
      [ "$nid" = "$id" ] || continue
      [ "$ntype" = "$ptype" ] || continue
      case "$pname" in FullAWSAccess|RCPFullAWSAccess) continue ;; esac
      if [ "$TFOUND" -eq 0 ]; then printf '  [%s]\n' "$ptype"; TFOUND=1; fi
      FOUND=1
      printf '    %s  (%s)\n' "$pname" "$pid"
      printf '        %s\n' "$(entries_of "$pid")"
    done <"$NODEALL"
  done
  [ "$FOUND" -eq 0 ] && printf '  (nothing attached beyond FullAWSAccess / RCPFullAWSAccess)\n'
done <"$NODES"

# ======================================================================================
h1 "2. What governs each ACCOUNT, inheritance resolved"

printf 'SCPs are inherited down the tree and denies compose, so the ceiling over an account\n'
printf 'is the union of every statement on every ancestor. This section is the answer to\n'
printf '"what applies here", and it is the reason a nested OU carrying nothing (D37) costs\n'
printf 'nothing: read the account, not the folder.\n'

while IFS=$'\t' read -r aname aid parent anc; do
  [ -n "${aid:-}" ] || continue
  h2 "ACCOUNT $aname  ($aid)"
  CHAIN=""
  for nid in $anc; do
    NNAME=$(awk -F'\t' -v n="$nid" '$3==n {print $2; exit}' "$NODES")
    CHAIN="${CHAIN:+$CHAIN -> }$NNAME"
  done
  printf '  inherits from: %s\n\n' "$CHAIN"
  TOTAL=0
  for nid in $anc; do
    NNAME=$(awk -F'\t' -v n="$nid" '$3==n {print $2; exit}' "$NODES")
    while IFS=$'\t' read -r pnid pid pname; do
      [ "$pnid" = "$nid" ] || continue
      case "$pname" in FullAWSAccess) continue ;; esac
      TOTAL=$((TOTAL + $(nstmts_of "$pid")))
      printf '  from %-14s %s\n' "$NNAME" "$pname"
      printf '  %-19s   %s\n' "" "$(sids_of "$pid")"
    done <"$NODEPOL"
  done
  printf '\n  %s statements in force over this account.\n' "$TOTAL"
done <"$ACCTS"

# ======================================================================================
h1 "3. The read-only checks - the class no probe can reach"

printf 'Each of these is a statement whose condition selects a principal this project cannot\n'
printf 'produce, so attempting the call proves nothing and reading the document is the only\n'
printf 'instrument (Lesson 22). See plan/runbooks/scp-battery.md, "the class the battery\n'
printf 'cannot reach", for the same table written as a procedure.\n\n'

# --- CHK-1 / CHK-2: the two root-user controls -----------------------------------------
SEEN_ROOTCTL=0
while IFS=$'\t' read -r nid pid pname; do
  NNAME=$(awk -F'\t' -v n="$nid" '$3==n {print $2; exit}' "$NODES")
  policy_stmts "$pid" >"$TMP/cur.tsv" || continue
  [ "$POL_OK" -eq 1 ] || continue

  LINE=$(awk -F'\t' '$1=="GRRESTRICTROOTUSER"' "$TMP/cur.tsv")
  if [ -n "$LINE" ]; then
    SEEN_ROOTCTL=1
    if printf '%s' "$LINE" | grep -q 'aws:AssumedRoot'; then
      check pass "CHK-1" "ExemptAssumeRoot on $NNAME" "$pname ($pid) - aws:AssumedRoot present"
    else
      check fail "CHK-1" "ExemptAssumeRoot on $NNAME" \
        "$pname ($pid) - NO aws:AssumedRoot: sts:AssumeRoot is denied into every account under $NNAME, which is 1a step 6's only member-account recovery. Disable and re-enable the control WITH the parameter; it has no false value."
    fi
  fi

  LINE=$(awk -F'\t' '$1=="GRRESTRICTROOTUSERACCESSKEYS"' "$TMP/cur.tsv")
  if [ -n "$LINE" ]; then
    if printf '%s' "$LINE" | grep -q 'aws:AssumedRoot'; then
      check fail "CHK-2" "no access-key exemption on $NNAME" \
        "$pname ($pid) - aws:AssumedRoot present, and it must not be: a root access key minted inside a privileged session is a standing, unscoped, SCP-immune credential (D16)."
    else
      check pass "CHK-2" "no access-key exemption on $NNAME" "$pname ($pid) - correctly unexempted"
    fi
  fi
done <"$NODEPOL"
[ "$SEEN_ROOTCTL" -eq 0 ] && \
  check note "CHK-1" "root-user controls" "not enabled on any OU - nothing to check"

# --- CHK-3: D27's service guard --------------------------------------------------------
SEEN_D27=0
while IFS=$'\t' read -r nid pid pname; do
  NNAME=$(awk -F'\t' -v n="$nid" '$3==n {print $2; exit}' "$NODES")
  policy_stmts "$pid" >"$TMP/cur.tsv" || continue
  [ "$POL_OK" -eq 1 ] || continue
  LINE=$(awk -F'\t' '$1=="DenyCatalogMaintenanceRunsExceptMaintenanceRole"' "$TMP/cur.tsv")
  [ -n "$LINE" ] || continue
  SEEN_D27=1
  if printf '%s' "$LINE" | grep -q 'aws:PrincipalIsAWSService'; then
    check pass "CHK-3" "D27 service guard on $NNAME" "$pname ($pid) - aws:PrincipalIsAWSService present"
  else
    check fail "CHK-3" "D27 service guard on $NNAME" \
      "$pname ($pid) - the carve-out has no aws:PrincipalIsAWSService guard, so a service principal inherits the exemption."
  fi
done <"$NODEPOL"
[ "$SEEN_D27" -eq 0 ] && \
  check note "CHK-3" "D27 service guard" "the Data OU document is not attached anywhere - nothing to check"

# --- CHK-4: D37, Sandboxes carries nothing ---------------------------------------------
SB_ID=$(awk -F'\t' '$2=="Sandboxes" {print $3; exit}' "$NODES")
if [ -n "${SB_ID:-}" ]; then
  EXTRA=$(awk -F'\t' -v n="$SB_ID" '$1==n && $3!="FullAWSAccess" {printf "%s%s", sep, $3; sep=", "}' "$NODEPOL")
  if [ -z "$EXTRA" ]; then
    check pass "CHK-4" "D37 - Sandboxes carries nothing" "only FullAWSAccess, governed by Interactive through inheritance"
  else
    check fail "CHK-4" "D37 - Sandboxes carries nothing" \
      "attached: $EXTRA. Either this is a deliberate divergence from Interactive - in which case write it down in D37 and in the stage log - or it is drift."
  fi
else
  check note "CHK-4" "D37 - Sandboxes" "no OU named Sandboxes in the tree"
fi

# --- CHK-5: RCPFullAWSAccess everywhere (INV-11) ---------------------------------------
while IFS=$'\t' read -r kind name id anc; do
  [ -n "${id:-}" ] || continue
  if awk -F'\t' -v n="$id" '$1==n && $2=="RCPFullAWSAccess"' "$NODERCP" | grep -q .; then
    check pass "CHK-5" "RCPFullAWSAccess on $name" "present"
  else
    check fail "CHK-5" "RCPFullAWSAccess on $name" \
      "MISSING - an RCP set with no allow is a closed door, so this denies everything at this node."
  fi
done <"$NODES"

{
  printf 'RESULT\tID\tWHAT\tDETAIL\n'
  awk -F'\t' '$1=="fail"' "$CHECKS"
  awk -F'\t' '$1=="note"' "$CHECKS"
  awk -F'\t' '$1=="pass"' "$CHECKS"
} | tabulate

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
printf '\n%s check(s) FAILED.\n' "$NFAIL"
if [ "$NFAIL" -gt 0 ]; then
  printf 'A failure here is a real defect no matter how clean the battery ran - these\n'
  printf 'statements are the ones it cannot see.\n'
fi

# ======================================================================================
h1 "4. The ceiling at a glance, per OU"

{
  printf 'OU\tGUARDRAIL\tREGION CEILING\tROOT CONTROLS\tPROJECT SCP\n'
  while IFS=$'\t' read -r kind name id anc; do
    [ "$kind" = "OU" ] || continue
    G="-"; R="-"; U="-"; P="-"
    while IFS=$'\t' read -r nid pid pname; do
      [ "$nid" = "$id" ] || continue
      case "$pname" in
        aws-guardrails-*) G="yes" ;;
        awsds-org-scp-*)  P="yes" ;;
      esac
      policy_stmts "$pid" >"$TMP/cur.tsv" 2>/dev/null || continue
      [ "$POL_OK" -eq 1 ] || continue
      awk -F'\t' '$1=="CTMULTISERVICEPV1"' "$TMP/cur.tsv" | grep -q . && R="yes"
      awk -F'\t' '$1=="GRRESTRICTROOTUSER"' "$TMP/cur.tsv" | grep -q . && U="yes"
    done <"$NODEPOL"
    printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$G" "$R" "$U" "$P"
  done <"$NODES"
} | tabulate

printf '\n'
printf 'READ THE GAPS, NOT THE YESES. Exactly ONE is expected, and it is not drift:\n'
printf '  - `Sandboxes` is blank across the row by decision (D37) and its accounts are\n'
printf '    governed by `Interactive` - section 2 shows that resolved.\n'
printf 'Every other OU carries a guardrail, a Region ceiling and the root controls. `Security`\n'
printf 'joined them on 2026-08-14 (Stage 1d step 12, decision 10), which closed open question\n'
printf '16 - so a `Security` row reading `-` under REGION CEILING or ROOT CONTROLS is now a\n'
printf 'REGRESSION, not the inherited gap it used to be.\n'
printf 'Anything else missing from this table is drift. AWS_STATE.md INV-11 and INV-12 hold\n'
printf 'the expected shape, and are what this table should be diffed against.\n'
printf '\n'
printf 'AND THE TABLE CANNOT BE REGRESSION-TESTED FOR TWO OF THE NINE ACCOUNTS. `Log Archive`\n'
printf 'and `Audit` hold no CLI profile by design, so ./aws/probes/scp-battery.sh has no reach\n'
printf 'into them and never will. Whatever the `Security` row says here is the ONLY standing\n'
printf 'instrument over those two accounts; the probes behind it were run by hand, once, in\n'
printf 'CloudShell (Stage 1d step 12.2).\n'

# ======================================================================================
h1 "5. Calls that failed"

if [ -s "$ERRORS" ]; then
  cat "$ERRORS"
  printf '\nIf these are AccessDenied, retry from CloudShell on Management as\n'
  printf '`AWS Control Tower Admin`:  ./aws/org-policies.sh -\n'
else
  printf 'None. Every call returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/org-policies.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 5)"
  exit 1
fi
if [ "$NFAIL" -gt 0 ]; then
  note "wrote $OUT ($NFAIL CHECK(S) FAILED - see section 3)"
  exit 2
fi
note "wrote $OUT (all checks passed)"
exit 0
