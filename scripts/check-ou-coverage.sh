#!/usr/bin/env bash
#
# check-ou-coverage.sh - Stage 2 step 9.3. Every OU is accounted for, and the authored map
# still describes what is attached.
#
#   needs:    a live SSO session - the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./scripts/check-ou-coverage.sh          # awsds-infra-identity
#             ./scripts/check-ou-coverage.sh -        # no --profile: CloudShell on Management
#   reads:    organizations:ListRoots, ListOrganizationalUnitsForParent, ListPoliciesForTarget,
#             sts:GetCallerIdentity - and terraform-live/identity/org-policies/. It never
#             creates, updates, attaches or detaches anything.
#   exit:     0 clean | 1 a check FAILED | 2 could not run (no session, or a call failed)
#
# WHY THIS CHECK CARRIES MORE THAN ITS SIZE. Accounts and OUs are vended from the console, by
# decision and permanently (D34), so nothing in Terraform declares them and they cannot drift.
# The risk runs the other way and it is silent: a new OU with no document attached, and
# `terraform plan` reporting "No changes" because a state file tracks only what a configuration
# declares. Step 5.3 moved the per-OU coverage guarantee out of the apply and into here, so
# this script is where that risk is actually paid for.
#
# THE TWO-LIST SHAPE IS THE POINT. attachments.json lists the OUs that carry a document AND the
# OUs that deliberately carry none, with the reason. A check that treated "absent" and
# "deliberately absent" alike would either fail forever or pass on a real gap - the same answer
# on success and on failure, which is not a check (Lesson 13). `Sandboxes` is the entry that
# has to be named: it is the only OU whose emptiness a future reader will try to fix (D37).
#
# THREE THINGS IT DOES NOT LOOK AT, so a green run is not read as more than it is:
#
#   - CONTROL TOWER'S OWN DOCUMENTS. Every governed OU carries aws-guardrails-* documents that
#     this project neither wrote nor may edit. A document counts as ours only when a file of
#     that name exists in policies/, which is a stronger binding than a name prefix and the
#     reason the map may hold names at all (Lesson 23 warns against naming a document whose
#     PACKING somebody else owns - these are the ones we own).
#   - ACCOUNT-LEVEL ATTACHMENTS. This design has none: the census is the root plus four OUs,
#     and the delegation's account/* entry is an unexercised over-grant (step 5.0). The full
#     per-node census is ./aws/org-policies.sh section 1, which is the instrument for that.
#   - WHETHER A DOCUMENT'S CONTENT IS RIGHT. That is POLICIES.md and check-index.sh.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

MAP="terraform-live/identity/org-policies/attachments.json"
POLICY_DIR="terraform-live/identity/org-policies/policies"
TYPES="SERVICE_CONTROL_POLICY RESOURCE_CONTROL_POLICY TAG_POLICY DECLARATIVE_POLICY_EC2"

PROFILE="${1:-awsds-infra-identity}"
[ "$PROFILE" = "-" ] && PROFILE=""

fail=0
say() { printf '%s\n' "$*"; }
bad() { fail=1; printf '  FAIL  %s\n' "$*"; }

aws_() { if [ -n "$PROFILE" ]; then aws --profile "$PROFILE" "$@"; else aws "$@"; fi; }
has()  { printf '%s\n' "$2" | grep -Fxq "$1"; }   # $1 in the newline-separated list $2

for t in jq aws; do
  command -v "$t" >/dev/null || { say "$t is not on PATH"; exit 2; }
done
[ -f "$MAP" ] || { say "no authored map at $MAP"; exit 2; }
jq -e . "$MAP" >/dev/null || { say "$MAP does not parse"; exit 2; }

# The session is checked before anything else and its failure is exit 2, never exit 0. A
# coverage check reporting "clean" because it could not reach AWS is the worst output this
# script could produce (CLAUDE.md: check the caller identity before running aws commands).
WHO=$(aws_ sts get-caller-identity --query 'Arn' --output text 2>&1) || {
  say "no usable session${PROFILE:+ for profile $PROFILE}:"
  say "  $WHO"
  say "  sign in as the INFRASTRUCTURE USER, Identity account, InfrastructureAccess:"
  say "      aws sso login --sso-session awsds"
  exit 2
}
say "== identity =="
say "  $WHO${PROFILE:+  (profile $PROFILE)}"

# ---------------------------------------------------------------- the organization's OUs
ROOT=$(aws_ organizations list-roots --output json 2>&1) || { say "list-roots failed: $ROOT"; exit 2; }
ROOT_ID=$(printf '%s' "$ROOT" | jq -r '.Roots[0].Id')
[ -n "$ROOT_ID" ] && [ "$ROOT_ID" != "null" ] || { say "could not read the organization root"; exit 2; }

# Breadth-first over the whole tree, not one level. The nesting is two deep today (Sandboxes
# under Interactive, D23) and a single ListOrganizationalUnitsForParent over the root's
# children would enumerate neither the nested OU nor anything below it - the same silent
# under-reach step 5.3 refuses in a for_each.
OU_TSV=""            # one "id<TAB>name" per line, every depth
QUEUE="$ROOT_ID"
while [ -n "$QUEUE" ]; do
  parent=$(printf '%s\n' "$QUEUE" | head -1)
  QUEUE=$(printf '%s\n' "$QUEUE" | tail -n +2)
  page=$(aws_ organizations list-organizational-units-for-parent --parent-id "$parent" --output json 2>&1) \
    || { say "list-organizational-units-for-parent $parent failed: $page"; exit 2; }
  children=$(printf '%s' "$page" | jq -r '.OrganizationalUnits[] | [.Id, .Name] | @tsv')
  [ -n "$children" ] || continue
  OU_TSV="${OU_TSV}${children}"$'\n'
  QUEUE="${QUEUE}"$'\n'"$(printf '%s' "$children" | cut -f1)"
  QUEUE=$(printf '%s\n' "$QUEUE" | grep -v '^$')
done
OU_TSV=$(printf '%s' "$OU_TSV" | grep -v '^$')
OU_NAMES=$(printf '%s\n' "$OU_TSV" | cut -f2)
say "  root $ROOT_ID, $(printf '%s\n' "$OU_NAMES" | grep -c '^') OU(s) at every depth"

WITH_DOC=$(jq -r '.ou | keys[]' "$MAP")
WITHOUT_DOC=$(jq -r '.ou_with_no_document | keys[]' "$MAP")

# ---------------------------------------------------------------- 1. every OU is accounted for
say
say "== 1. every OU appears in the authored map, or in its deliberately-empty list =="
while IFS=$'\t' read -r id name; do
  [ -n "$name" ] || continue
  if has "$name" "$WITH_DOC"; then
    say "  $name -> $(jq -r --arg n "$name" '.ou[$n] | join(", ")' "$MAP")"
  elif has "$name" "$WITHOUT_DOC"; then
    say "  $name -> no document, on purpose: $(jq -r --arg n "$name" '.ou_with_no_document[$n]' "$MAP" | cut -c1-58)..."
  else
    bad "OU '$name' ($id) is in neither list of $MAP"
    say "          attach a document and add it to .ou, or record in .ou_with_no_document why it carries none"
  fi
done <<EOF
$OU_TSV
EOF

# The other direction: a map entry for an OU that no longer exists is a for_each key that
# fails an apply, and a reason nobody can act on.
say
say "== 2. every OU the map names still exists =="
n_missing=0
while IFS= read -r name; do
  [ -n "$name" ] || continue
  has "$name" "$OU_NAMES" || { bad "the map names OU '$name', which the organization does not have"; n_missing=1; }
done <<EOF
$WITH_DOC
$WITHOUT_DOC
EOF
[ "$n_missing" -eq 0 ] && say "  none missing"

# ---------------------------------------------------------------- 3. the documents exist
say
say "== 3. every document the map names is a file in policies/ =="
n_absent=0
while IFS= read -r doc; do
  [ -n "$doc" ] || continue
  [ -f "$POLICY_DIR/$doc.json" ] || { bad "map names '$doc', but $POLICY_DIR/$doc.json does not exist"; n_absent=1; }
done < <(jq -r '[.root[], (.ou | to_entries[] | .value[])] | unique[]' "$MAP")
[ "$n_absent" -eq 0 ] && say "  all present"

# ---------------------------------------------------------------- 4. authored == attached
say
say "== 4. what is attached matches what the map authors =="
say "  (this project's documents only - a policy counts as ours when policies/<name>.json exists)"

attached_ours() {          # $1 = target id -> our documents attached to it, sorted, one per line
  local target="$1" t out all=""
  for t in $TYPES; do
    out=$(aws_ organizations list-policies-for-target --target-id "$target" --filter "$t" --output json 2>&1) \
      || return 1
    all="${all}$(printf '%s' "$out" | jq -r '.Policies[].Name')"$'\n'
  done
  printf '%s' "$all" | grep -v '^$' | while IFS= read -r name; do
    [ -f "$POLICY_DIR/$name.json" ] && printf '%s\n' "$name"
  done | sort
}

count() { [ -z "$1" ] && printf '0' || printf '%s' "$(printf '%s\n' "$1" | grep -c '^')"; }

compare() {                # $1 = label, $2 = target id, $3 = authored names (newline separated)
  local label="$1" target="$2" authored actual
  actual=$(attached_ours "$2") || { bad "$label: list-policies-for-target failed"; return; }
  authored=$(printf '%s\n' "$3" | grep -v '^$' | sort)
  if [ "$authored" = "$actual" ]; then
    say "  $label: $(count "$actual") document(s), as authored"
    return
  fi
  bad "$label: the map and the organization disagree"
  comm -23 <(printf '%s\n' "$authored") <(printf '%s\n' "$actual") | grep -v '^$' | sed 's/^/          authored, NOT attached: /'
  comm -13 <(printf '%s\n' "$authored") <(printf '%s\n' "$actual") | grep -v '^$' | sed 's/^/          attached, NOT authored: /'
}

compare "root ($ROOT_ID)" "$ROOT_ID" "$(jq -r '.root[]' "$MAP")"
while IFS=$'\t' read -r id name; do
  [ -n "$name" ] || continue
  compare "OU $name" "$id" "$(jq -r --arg n "$name" '.ou[$n][]? // empty' "$MAP")"
done <<EOF
$OU_TSV
EOF

say
[ "$fail" -eq 0 ] && say "OK" || say "FAILED"
exit "$fail"
