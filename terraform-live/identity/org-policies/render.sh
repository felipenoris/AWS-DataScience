#!/usr/bin/env bash
#
# render.sh - substitute the organization's own identifiers into the policy templates and
# report the size of each result against the Organizations limits.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./terraform-live/identity/org-policies/render.sh
#             ./terraform-live/identity/org-policies/render.sh awsds-infra-dev   # other profile
#   writes:   aws/output/rendered-policies/<name>.json   (UNTRACKED - .gitignore)
#   reads:    organizations:DescribeOrganization, ListRoots,
#             ListOrganizationalUnitsForParent, ListAccountsForParent,
#             sts:GetCallerIdentity.
#             It never creates, updates or deletes anything in AWS.
#
# WHY THE TEMPLATES CARRY PLACEHOLDERS AND NOT THE REAL IDS. Two independent reasons, and
# either one alone would be enough:
#   - The same organization id appears in awsds-org-scp-perimeter.json, in the tag and RCP
#     documents of step 7.8, and inside the OU path of the datazone carve-out. A value that
#     has to be typed correctly in four places will eventually be wrong in one of them, and
#     the direction it fails in is silent - a deny that never fires (Lesson 14). Generated
#     once, it cannot drift.
#   - At Stage 2 these documents move into Terraform, where the id comes from
#     `data.aws_organizations_organization.this.id` rather than from a literal. A template
#     with a placeholder is already that shape; a file with the id baked in would have to be
#     un-baked, which is an edit nobody remembers is pending.
# The rendered output lands in aws/output/, which is untracked, so no identifier enters a
# tracked file (aws/INDEX.md rule 1) - and the file there is what gets pasted into the
# console, byte for byte, so that Stage 2 step 5.5's import compares a document against
# itself instead of against a re-typing.
#
# WHAT IT CHECKS BESIDES SUBSTITUTING, because both failures are found at the END of the
# evening otherwise: that no placeholder survived (an unsubstituted <...> is a policy that
# attaches and denies nothing, or refuses to attach at all), that the JSON parses, and how
# many characters each document spends against the per-node budget.

set -uo pipefail

PROFILE="${1:-${AWSDS_PROFILE:-awsds-infra-identity}}"
REGION="us-west-2"
SSO_SESSION="awsds"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../../.."          # repository root
OUT_DIR="aws/output/rendered-policies"
SRC_DIR="terraform-live/identity/org-policies"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

note() { printf '%s\n' "$*" >&2; }
die()  { note ""; note "ERROR: $*"; exit 1; }

aws_() { command aws --profile "$PROFILE" --region "$REGION" "$@" </dev/null; }

# ---------------------------------------------------------------------------- preflight

if ! CALLER=$(aws_ sts get-caller-identity --query 'Arn' --output text 2>&1); then
  note "cannot authenticate as '$PROFILE':"
  printf '%s\n' "$CALLER" | sed '/^[[:space:]]*$/d; s/^/  /' >&2
  note ""
  note "log in first:  aws sso login --sso-session $SSO_SESSION"
  exit 1
fi
note "caller : $CALLER"

# ------------------------------------------------------------------- the identifiers

ORG_ID=$(aws_ organizations describe-organization --query 'Organization.Id' --output text 2>/dev/null)
[ -n "$ORG_ID" ] && [ "$ORG_ID" != "None" ] || die "could not read the organization id"

ROOT_ID=$(aws_ organizations list-roots --query 'Roots[0].Id' --output text 2>/dev/null)
[ -n "$ROOT_ID" ] && [ "$ROOT_ID" != "None" ] || die "could not read the root id"

# The Data OU, by NAME - the one lookup that would otherwise be a hand-copied id. If the OU
# is ever renamed this fails loudly here rather than producing a carve-out that matches
# nothing, which is the failure direction that does not announce itself.
OU_ID_DATA=$(aws_ organizations list-organizational-units-for-parent \
               --parent-id "$ROOT_ID" \
               --query 'OrganizationalUnits[?Name==`Data`].Id | [0]' --output text 2>/dev/null)
[ -n "$OU_ID_DATA" ] && [ "$OU_ID_DATA" != "None" ] \
  || die "no OU named 'Data' directly under $ROOT_ID - has it been renamed or nested?"

# aws:PrincipalOrgPaths is the full path WITH a trailing slash, and `Data` sits directly
# under the root, so this is the whole path. A nested OU would need one more segment - and
# `*` in place of the final slash only if the carve-out is meant to reach children.
ORG_PATH_DATA="$ORG_ID/$ROOT_ID/$OU_ID_DATA/"

# The Data Governance account id, resolved by OU MEMBERSHIP rather than pasted. The Data OU
# document (step 7.6) carves the catalog-maintenance role out of its crawler deny (D27), and
# an ARN condition may not name a wildcard account (`plan/conventions.md`) - so the id has to
# come from somewhere, and the only source that cannot go stale is the organization itself.
# Exactly one account is expected: `Data` holds Data Governance alone, and every account in
# this design except `Sandbox` is structural (D35). Two accounts here is not a rendering
# problem to route around, it is a change to the account map, so it stops.
ACCT_IDS_DATA=$(aws_ organizations list-accounts-for-parent --parent-id "$OU_ID_DATA" \
                  --query 'Accounts[?Status==`ACTIVE`].Id' --output text 2>/dev/null)
# shellcheck disable=SC2086
set -- $ACCT_IDS_DATA
[ "$#" -eq 1 ] || die "expected exactly ONE active account in the Data OU ($OU_ID_DATA), found $# - the account map changed, and the carve-out cannot be rendered until the plan says which account it names"
ACCOUNT_ID_DATA="$1"

note "org    : $ORG_ID"
note "root   : $ROOT_ID"
note "Data OU: $OU_ID_DATA"
note "path   : $ORG_PATH_DATA"
# Masked on purpose: this line is read off a terminal that gets pasted into log/, and an
# account id is one of the three things `CLAUDE.md` keeps out of tracked files. The full id
# is in the rendered document under aws/output/, which is untracked.
note "Data ac: ...${ACCOUNT_ID_DATA: -4}"
note ""

# ------------------------------------------------------------------------- rendering

# The documented limits, since Service Quotas publishes none of them for `organizations`
# (Stage 1c step 7.0 step 5, measured): SCPs are 10 per node and 10 240 characters per
# document since the May 2026 increase; RCPs were not part of it and are still 5 and 5 120.
# This script checks every document against the TIGHTER number on purpose - the same folder
# holds 7.8's RCP, one file among several, and a limit that is right for most of them is the
# kind that is discovered by the one it was wrong for.
LIMIT=5120

RENDERED=0
FAILED=0

render_one() { # render_one <path-to-template>
  local src="$1" base out
  base=$(basename "$src")
  out="$OUT_DIR/$base"

  sed -e "s|<ORG_ID>|$ORG_ID|g" \
      -e "s|<ROOT_ID>|$ROOT_ID|g" \
      -e "s|<OU_ID_DATA>|$OU_ID_DATA|g" \
      -e "s|<ORG_PATH_DATA>|$ORG_PATH_DATA|g" \
      -e "s|<ACCOUNT_ID_DATA>|$ACCOUNT_ID_DATA|g" \
      "$src" >"$out"

  # 1. no placeholder may survive
  if grep -q '<[A-Z_]\+>' "$out"; then
    note "  $base  UNSUBSTITUTED PLACEHOLDER:"
    grep -o '<[A-Z_]\+>' "$out" | sort -u | sed 's/^/      /' >&2
    FAILED=$((FAILED + 1))
    return 1
  fi

  # 2. it must be valid JSON
  if ! python3 -c "import json,sys; json.load(open('$out'))" 2>/dev/null; then
    note "  $base  INVALID JSON"
    FAILED=$((FAILED + 1))
    return 1
  fi

  # 3. the size, as pasted (the file's own bytes) and minified
  local raw min
  raw=$(wc -c <"$out" | tr -d ' ')
  min=$(python3 -c "import json;print(len(json.dumps(json.load(open('$out')),separators=(',',':'))))")
  if [ "$min" -gt "$LIMIT" ]; then
    note "  $base  TOO LARGE even minified: $min > $LIMIT"
    FAILED=$((FAILED + 1))
    return 1
  fi
  printf '  %-40s %5s bytes as written, %5s minified  (limit %s, margin %s)\n' \
    "$base" "$raw" "$min" "$LIMIT" "$((LIMIT - min))" >&2
  RENDERED=$((RENDERED + 1))
}

note "rendering $SRC_DIR/policies/ :"
for f in "$SRC_DIR"/policies/*.json; do
  [ -e "$f" ] || continue
  render_one "$f"
done

if [ -d "$SRC_DIR/canary" ]; then
  note ""
  note "rendering $SRC_DIR/canary/  (throwaway documents for the 7.3 battery):"
  for f in "$SRC_DIR"/canary/*.json; do
    [ -e "$f" ] || continue
    render_one "$f"
  done
fi

# ---------------------------------------------------------------------------- verdict

note ""
note "wrote $RENDERED file(s) to $OUT_DIR/"
if [ "$FAILED" -ne 0 ]; then
  note "$FAILED file(s) FAILED - nothing there is safe to paste"
  exit 1
fi
note ""
note "PASTE FROM $OUT_DIR/, not from $SRC_DIR/ - the templates still hold placeholders."
note "Record the returned policy id beside each filename in"
note "log/stage-01c-preventive-policies.md, as you attach it. An id read back out of a"
note "console you have just denied yourself access to is the failure that note prevents."
exit 0
