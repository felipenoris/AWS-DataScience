#!/usr/bin/env bash
#
# AZs.sh - the availability-zone name -> zone ID mapping, one listing per account, plus the
# comparison across them.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile below: the cached token is keyed by the
#             sso-session name, not by profile or account (see aws/INDEX.md).
#
#   run:      ./aws/AZs.sh                       every awsds-* profile in ~/.aws/config
#             ./aws/AZs.sh awsds-infra-dev ...   only the profiles named
#   writes:   aws/output/AZs.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeAvailabilityZones and sts:GetCallerIdentity. This script never
#             creates, updates or deletes anything.
#
# WHY THIS EXISTS. AWS maps AZ *names* (`us-west-2a`) to physical datacenters independently
# per account, so the same name can be a different datacenter in two accounts. The AZ *ID*
# (`usw2-az1`) is the stable identifier. The distinction has a bill attached: the two
# peerings into Production (D14, D21) are free within an AZ and USD 0.01/GB each way across
# AZs, and the divergence produces no error - only a line on the invoice. Measured first in
# Stage 1b step 6; the outcome is in plan/architecture.md §4.1 and plan/open-questions.md
# item 3, and is not repeated here (aws/INDEX.md: a snapshot is evidence, not intent).
#
# ONE DELIBERATE DEVIATION from aws/INDEX.md's "one profile per script": this script runs
# every profile it is given, because the comparison *between* accounts is the whole
# measurement. A single-profile version of it would answer nothing. Section 1 names the
# identity behind each block, which is what the one-profile rule exists to make visible.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - An account with no profile in ~/.aws/config is invisible here. `Staging` is the open
#     case - not vended, so not measured - and every Sandbox vended under Stage 14 will be
#     too until its profile exists.
#   - A profile whose call failed is reported as `(failed)` and excluded from the agreement
#     check in section 4. It is never counted as agreeing.
#   - The default listing shows the zones available to the account. Opt-in-required zones
#     (Local Zones, Wavelength) are excluded; nothing in this plan uses one.

set -uo pipefail

REGION="us-west-2"
SSO_SESSION="awsds"
PROFILE_PREFIX="awsds-"

cd "$(dirname "$0")/.."
OUT_DIR="aws/output"
OUT="$OUT_DIR/AZs.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/AZs.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"     # one line per failed call
CALLERS="$TMP/callers.tsv"   # profile <tab> caller ARN | (failed)
LIVE="$TMP/live.txt"         # the profiles that authenticated
: >"$ERRORS"; : >"$CALLERS"; : >"$LIVE"

# ------------------------------------------------------------------------------ helpers

# progress, on stderr, so it reaches the terminal and not the report
note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

# aws, always with an explicit profile and this script's region. </dev/null so that a call
# made from inside a `while read` loop cannot swallow the loop's input.
aws_() { local p="$1"; shift; command aws --profile "$p" --region "$REGION" "$@" </dev/null; }

# capture a call: sets RUN_OUT and RUN_STATUS, logs a failure, prints nothing
RUN_OUT=""; RUN_STATUS=0
run() { # run <profile> <aws args...>
  local p="$1"; shift
  RUN_OUT=$(aws_ "$p" "$@" 2>&1)
  RUN_STATUS=$?
  if [ "$RUN_STATUS" -ne 0 ]; then
    printf '[%s] aws %s\n    %s\n' \
      "$p" "$*" "$(printf '%s' "$RUN_OUT" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    RUN_OUT=""
  fi
}

# run a call, echo it into the report, then its output (or the error it raised)
show() { # show <profile> <aws args...>
  local p="$1"; shift
  printf '$ aws --profile %s %s\n\n' "$p" "$*"
  local out status
  out=$(aws_ "$p" "$@" 2>&1)
  status=$?
  if [ "$status" -ne 0 ]; then
    printf '%s\n\n!! COMMAND FAILED (exit %s)\n\n' "$out" "$status"
    printf '[%s] aws %s\n    %s\n' \
      "$p" "$*" "$(printf '%s' "$out" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    return "$status"
  fi
  if [ -n "$out" ]; then printf '%s\n' "$out"; else printf '(empty result - the call succeeded and returned nothing)\n'; fi
  printf '\n'
}

# align a tab-separated stream into a table; empty cells must be written as "-"
tabulate() { column -t -s $'\t'; }

# the zone ID this profile reports for this zone name, or "-" if it reports none
zone_id_of() { # zone_id_of <profile> <zone-name>
  awk -F'\t' -v k="$2" '$1==k {print $2; hit=1} END {if (!hit) print "-"}' "$TMP/map-$1.tsv"
}

# ------------------------------------------------------------ which profiles to measure

if [ "$#" -gt 0 ]; then
  PROFILES=$(printf '%s\n' "$@")
  PROFILE_SOURCE="named on the command line"
else
  PROFILES=$(command aws configure list-profiles 2>/dev/null | grep "^$PROFILE_PREFIX" | sort)
  PROFILE_SOURCE="every '$PROFILE_PREFIX*' profile in ~/.aws/config"
fi

if [ -z "$PROFILES" ]; then
  note "no profiles to measure ($PROFILE_SOURCE matched nothing)"
  exit 1
fi

# ---------------------------------------------------------------------------- preflight

note "region: $REGION"
while IFS= read -r p; do
  [ -n "$p" ] || continue
  if arn=$(command aws --profile "$p" --region "$REGION" \
             sts get-caller-identity --query 'Arn' --output text 2>&1); then
    printf '%s\t%s\n' "$p" "$arn" >>"$CALLERS"
    printf '%s\n' "$p" >>"$LIVE"
    note "  $p  OK"
  else
    printf '%s\t(failed)\n' "$p" >>"$CALLERS"
    printf '[%s] aws sts get-caller-identity\n    %s\n' \
      "$p" "$(printf '%s' "$arn" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    note "  $p  FAILED"
  fi
done <<PROFILES
$PROFILES
PROFILES

N_LIVE=$(grep -c . "$LIVE" || true)
if [ "${N_LIVE:-0}" -eq 0 ]; then
  note ""
  note "no profile authenticated. Log in first:"
  note "  aws sso login --sso-session $SSO_SESSION"
  note ""
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'AZs - availability-zone name to zone ID, per account\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'region    : %s\n' "$REGION"
printf 'profiles  : %s\n' "$PROFILE_SOURCE"
printf 'measured  : %s of %s\n' "$N_LIVE" "$(grep -c . "$CALLERS")"
printf 'produced  : aws/AZs.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Callers - the identity behind each block\n'
printf '  2. One listing per account\n'
printf '  3. The mappings side by side\n'
printf '  4. CHECK: do the accounts agree?\n'
printf '  5. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - AZ NAMES ARE PER-ACCOUNT LABELS; AZ IDS ARE THE STABLE IDENTIFIER. Two accounts\n'
printf '    showing the same name against different ids are naming different datacenters.\n'
printf '  - Every "$ aws ..." line is the exact command that produced the block under it,\n'
printf '    minus `--region %s`, which every command carries.\n' "$REGION"
printf '  - Section 3 is joined by this script from the calls in section 2.\n'
printf '  - A "(failed)" profile is excluded from the section 4 check, never counted as\n'
printf '    agreeing. Section 5 lists every call that failed.\n'
printf '  - An account with no profile on this laptop does not appear at all.\n'
printf '  - This is a point-in-time snapshot, not a source of truth: regenerate it rather\n'
printf '    than trusting a stale copy, and record intent in plan/ or log/, never here.\n'
printf '    What was decided from this measurement: plan/architecture.md 4.1 and\n'
printf '    plan/open-questions.md item 3.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

# --------------------------------------------------------------------------------------
h1 "1. Callers - the identity behind each block"

{
  printf 'PROFILE\tCALLER ARN\n'
  cat "$CALLERS"
} | tabulate
printf '\n'
printf 'Each row is `aws --profile <profile> sts get-caller-identity --query Arn`.\n'
printf 'A "(failed)" row means the profile did not authenticate - an expired SSO session is\n'
printf 'the usual cause. Its account is absent from sections 2-4, not agreeing with them.\n'

# --------------------------------------------------------------------------------------
h1 "2. One listing per account"

note "listing availability zones..."
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"

  show "$p" ec2 describe-availability-zones \
      --query 'sort_by(AvailabilityZones, &ZoneName)[].[ZoneName,ZoneId,ZoneType,State,OptInStatus]' \
      --output table

  run "$p" ec2 describe-availability-zones \
      --query 'sort_by(AvailabilityZones, &ZoneName)[].[ZoneName,ZoneId]' \
      --output text
  printf '%s\n' "$RUN_OUT" | grep -v '^$' >"$TMP/map-$p.tsv"
done <"$LIVE"

printf '\nThe five columns are ZoneName, ZoneId, ZoneType, State and OptInStatus. Anything\n'
printf 'other than `availability-zone` / `available` / `opt-in-not-required` is worth a\n'
printf 'second look before a subnet is placed there.\n'

# --------------------------------------------------------------------------------------
h1 "3. The mappings side by side"

ZONE_NAMES=$(cut -f1 "$TMP"/map-*.tsv 2>/dev/null | grep -v '^$' | sort -u)

if [ -z "$ZONE_NAMES" ]; then
  printf 'No zone returned by any profile. See section 5.\n'
else
  {
    printf 'ZONE NAME'
    while IFS= read -r p; do [ -n "$p" ] && printf '\t%s' "$p"; done <"$LIVE"
    printf '\n'
    while IFS= read -r z; do
      [ -n "$z" ] || continue
      printf '%s' "$z"
      while IFS= read -r p; do
        [ -n "$p" ] || continue
        printf '\t%s' "$(zone_id_of "$p" "$z")"
      done <"$LIVE"
      printf '\n'
    done <<ZONES
$ZONE_NAMES
ZONES
  } | tabulate
  printf '\n'
  printf 'One column per measured profile; the cell is the zone ID that account reports for\n'
  printf 'that zone name. A "-" means the account did not return that zone at all.\n'
fi

# --------------------------------------------------------------------------------------
h1 "4. CHECK: do the accounts agree?"

REF=$(head -n 1 "$LIVE")
DISAGREE=0

printf 'Reference: %s. Every other measured profile is compared against it.\n\n' "$REF"

{
  printf 'PROFILE\tVERDICT\n'
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    if [ "$p" = "$REF" ]; then
      printf '%s\treference\n' "$p"
    elif cmp -s "$TMP/map-$REF.tsv" "$TMP/map-$p.tsv"; then
      printf '%s\tsame mapping\n' "$p"
    else
      printf '%s\t!! DIFFERS\n' "$p"
      DISAGREE=$((DISAGREE + 1))
    fi
  done <"$LIVE"
} | tabulate
printf '\n'

if [ "$N_LIVE" -eq 1 ]; then
  printf 'NOTHING WAS COMPARED: only one account was measured, and it agrees with itself.\n'
  printf 'This is not a passing check - it is an absent one. Re-run against at least two\n'
  printf 'profiles before reading anything into section 3.\n\n'
elif [ "$DISAGREE" -eq 0 ]; then
  printf 'CHECK OK: the %s measured accounts return an identical name-to-ID mapping.\n\n' "$N_LIVE"
  printf 'This says nothing about an account that was not measured. A newly vended account\n'
  printf 'gets its own mapping at vend time, and nothing makes it match the ones above -\n'
  printf 'which is why anchoring on zone IDs is the standing rule rather than a reaction to\n'
  printf 'a divergence (plan/architecture.md 4.1).\n'
else
  printf '!! CHECK FAILED: %s profile(s) disagree with %s. The differing rows:\n\n' "$DISAGREE" "$REF"
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    [ "$p" = "$REF" ] && continue
    cmp -s "$TMP/map-$REF.tsv" "$TMP/map-$p.tsv" && continue
    printf '  %s vs %s\n\n' "$REF" "$p"
    {
      printf '  ZONE NAME\t%s\t%s\n' "$REF" "$p"
      while IFS=$'\t' read -r z ref_id; do
        [ -n "${z:-}" ] || continue
        other=$(zone_id_of "$p" "$z")
        [ "$other" = "$ref_id" ] && continue
        printf '  %s\t%s\t%s\n' "$z" "$ref_id" "$other"
      done <"$TMP/map-$REF.tsv"
    } | tabulate
    printf '\n'
  done <"$LIVE"
  printf 'Anchor subnets on zone IDs, never on list position. A `for_each` over\n'
  printf '`data.aws_availability_zones` by index places peered subnets in different\n'
  printf 'datacenters, which raises no error and shows up only as cross-AZ transfer.\n'
fi

NOT_MEASURED=$(awk -F'\t' '$2=="(failed)" {print "  " $1}' "$CALLERS")
if [ -n "$NOT_MEASURED" ]; then
  printf '\nNot measured, and therefore not covered by the verdict above:\n%s\n' "$NOT_MEASURED"
fi

# --------------------------------------------------------------------------------------
h1 "5. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
else
  printf 'None. Every call in this report returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/AZs.sh\n'

return "$DISAGREE"
}

# ---------------------------------------------------------------------------------- run

main >"$OUT"
status=$?

note ""
if [ "$status" -eq 0 ] && [ "$N_LIVE" -eq 1 ]; then
  note "wrote $OUT (1 account only - nothing was compared, see section 4)"
elif [ "$status" -eq 0 ]; then
  note "wrote $OUT ($N_LIVE accounts, mappings identical)"
else
  note "wrote $OUT ($status account(s) DISAGREE - see section 4)"
fi
if [ -s "$ERRORS" ]; then
  note "some calls failed - see section 5"
fi
exit "$status"
