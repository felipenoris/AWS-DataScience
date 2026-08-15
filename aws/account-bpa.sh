#!/usr/bin/env bash
#
# account-bpa.sh - the ACCOUNT-level S3 Block Public Access setting, one row per account.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile below: the cached token is keyed by the
#             sso-session name, not by profile or account (see aws/INDEX.md).
#
#   run:      ./aws/account-bpa.sh                       every awsds-* profile
#             ./aws/account-bpa.sh awsds-infra-dev ...   only the profiles named
#             ./aws/account-bpa.sh -                    no --profile: CloudShell, for the
#                                                       three accounts that have none
#   writes:   aws/output/account-bpa.txt   (untracked - see .gitignore)
#   reads:    s3control:GetPublicAccessBlock and sts:GetCallerIdentity. This script never
#             creates, updates or deletes anything - the `put` command is PRINTED, not run.
#
# WHY THIS EXISTS, and why it is worth a script rather than a loop typed once. There are two
# Block Public Access settings and they are not the same control: the BUCKET-level one, which
# Stage 2's s3-bucket module sets on every bucket IT creates, and the ACCOUNT-level one below,
# which also covers the bucket somebody creates outside that module. Only the second is a
# blanket, and it has no cross-account API: it is set from inside each account, so "every
# member account" has to be a LIST or the one account nobody had a profile for is the one
# that keeps the hole.
#
# It is read three times, which is what makes it a script:
#   - BEFORE 7.4 step 1, as Stage 1c step 7.0 step 4: the plan assumes BPA is off everywhere
#     and that assumption had never been measured. Where the Account Factory blueprint
#     already set it, half of 7.4 is a no-op.
#   - AFTER 7.4 step 1, as the confirmation that every row now reads four times `true` -
#     BEFORE 7.5 attaches the SCP that denies changing it. In the other order the deny blocks
#     the very call that enables the setting it protects, in every account at once, and the
#     repair is a detach from the management account.
#   - AT EVERY VEND, forever (D34, D35). A new account lands with BPA unset and inherits the
#     root deny the moment it enters a governed OU; from then on only the carved-out
#     InfrastructureAccess role can set it (Stage 1c decision 7). Stage 14 owes a step for
#     this, and this script is how that step is checked.
#
# ONE DELIBERATE DEVIATION from aws/INDEX.md's "one profile per script", the same one AZs.sh
# takes and for the same reason: the subject is a per-account setting compared ACROSS
# accounts, so a single-profile version answers nothing. Section 1 names the identity behind
# every row, which is what the one-profile rule exists to make visible.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - MANAGEMENT, LOG ARCHIVE and AUDIT have no profile on this laptop and never will
#     (guiding principle 1; ORGANIZATION.md). They are invisible here. Run this script with
#     `-` inside CloudShell in each of them, as `AWS Control Tower Admin`, and record the
#     three answers by hand - section 4 prints the exact command.
#   - `Staging` is not vended, and every Sandbox beyond the first has no profile until
#     Stage 14 gives it one. Absent, not reassuring.
#   - EXC-01, the SUSPENDED `Sandbox` at the organization root, is not this project's and
#     cannot be acted on. It has no profile and belongs in no list here.
#   - This is the ACCOUNT setting only. A bucket may still be public-blocked or not on its
#     own; that is a different call (s3api get-public-access-block --bucket).

set -uo pipefail

REGION="us-west-2"
SSO_SESSION="awsds"
PROFILE_PREFIX="awsds-"

# Normally run from inside the repository. The `-` fallback runs it in CloudShell, which has
# no repository, so the root is located rather than assumed.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/account-bpa.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/account-bpa.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"     # one line per failed call
CALLERS="$TMP/callers.tsv"   # profile <tab> account id <tab> caller ARN | (failed)
ROWS="$TMP/rows.tsv"         # profile <tab> account <tab> 4 flags <tab> verdict
: >"$ERRORS"; : >"$CALLERS"; : >"$ROWS"

# ------------------------------------------------------------------------------ helpers

note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

# aws with an explicit profile, or with none when the profile is `-`
aws_() { # aws_ <profile> <args...>
  local p="$1"; shift
  if [ "$p" = "-" ] || [ "$p" = "none" ]; then
    command aws --region "$REGION" "$@" </dev/null
  else
    command aws --profile "$p" --region "$REGION" "$@" </dev/null
  fi
}

show() { # show <profile> <aws args...>
  local p="$1"; shift
  if [ "$p" = "-" ]; then printf '$ aws %s\n\n' "$*"; else printf '$ aws --profile %s %s\n\n' "$p" "$*"; fi
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

tabulate() { column -t -s $'\t'; }

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
LIVE="$TMP/live.txt"; : >"$LIVE"
while IFS= read -r p; do
  [ -n "$p" ] || continue
  if out=$(aws_ "$p" sts get-caller-identity --query '[Account,Arn]' --output text 2>&1); then
    acct=$(printf '%s' "$out" | awk '{print $1}')
    arn=$(printf '%s' "$out" | awk '{print $2}')
    printf '%s\t%s\t%s\n' "$p" "$acct" "$arn" >>"$CALLERS"
    printf '%s\t%s\n' "$p" "$acct" >>"$LIVE"
    note "  $p  OK"
  else
    printf '%s\t-\t(failed)\n' "$p" >>"$CALLERS"
    printf '[%s] aws sts get-caller-identity\n    %s\n' \
      "$p" "$(printf '%s' "$out" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    note "  $p  FAILED"
  fi
done <<PROFILES
$PROFILES
PROFILES

if [ ! -s "$LIVE" ]; then
  note ""
  note "no profile authenticated. log in first:"
  note "  aws sso login --sso-session $SSO_SESSION"
  note ""
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'Account-level S3 Block Public Access, one row per account\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profiles  : %s\n' "$PROFILE_SOURCE"
printf 'region    : %s   (the setting is account-wide; the region only picks an endpoint)\n' "$REGION"
printf 'produced  : aws/account-bpa.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Which accounts were measured, and as whom\n'
printf '  2. The raw answer, per account\n'
printf '  3. The verdict table - all four flags, side by side\n'
printf '  4. The accounts this laptop cannot reach, and how to read them\n'
printf '  5. How to SET it, and the ordering that must not be reversed\n'
printf '  6. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - `NoSuchPublicAccessBlockConfiguration` IS THE "NOT SET" ANSWER, and it is what\n'
printf '    to expect before Stage 1c step 7.4. It is reported as NOT SET, not as a failure.\n'
printf '  - THE TARGET STATE IS ALL FOUR FLAGS true, in every account. Three of four is not\n'
printf '    a partial pass: RestrictPublicBuckets alone still allows a public ACL, and\n'
printf '    BlockPublicAcls alone still allows a public bucket POLICY.\n'
printf '  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 4 names the ones this laptop\n'
printf '    cannot reach; an account absent from both section 3 and section 4 is an account\n'
printf '    nobody is measuring, which is the hole this script exists to make visible.\n'
printf '  - ORDER MATTERS AND IS IRREVERSIBLE-ISH: set BPA everywhere FIRST, then attach the\n'
printf '    SCP that denies changing it (7.5). Reversed, the deny blocks the enabling call in\n'
printf '    every account at once and the repair is a detach from the management account.\n'
printf '  - This is a point-in-time snapshot, not a source of truth: regenerate it rather\n'
printf '    than trusting a stale copy, and record intent in plan/ or log/, never here.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

# --------------------------------------------------------------------------------------
h1 "1. Which accounts were measured, and as whom"

{
  printf 'PROFILE\tACCOUNT\tCALLER ARN\n'
  while IFS=$'\t' read -r p acct arn; do
    printf '%s\t%s\t%s\n' "$p" "${acct:--}" "${arn:--}"
  done <"$CALLERS"
} | tabulate

printf '\n'
printf 'A `(failed)` row is a profile that did not authenticate - it is EXCLUDED from\n'
printf 'section 3 and never counted as compliant. `awsds-policy-canary` is on this list on\n'
printf 'purpose: it is the easiest account to forget precisely because it is supposed to\n'
printf 'stay empty, and it still has an S3 API.\n'

# --------------------------------------------------------------------------------------
h1 "2. The raw answer, per account"

while IFS=$'\t' read -r p acct; do
  [ -n "${p:-}" ] || continue
  h2 "2.x $p  ($acct)"
  OUT_RAW=$(aws_ "$p" s3control get-public-access-block --account-id "$acct" \
              --query 'PublicAccessBlockConfiguration' --output json 2>&1)
  STATUS=$?
  printf '$ aws --profile %s s3control get-public-access-block --account-id %s\n\n' "$p" "$acct"
  printf '%s\n\n' "$OUT_RAW"

  if [ "$STATUS" -ne 0 ]; then
    if printf '%s' "$OUT_RAW" | grep -q 'NoSuchPublicAccessBlockConfiguration'; then
      printf '=> NOT SET. This is the expected answer before 7.4 step 1, and it is not an\n'
      printf '   error: the account simply has no account-level configuration.\n'
      printf '%s\t%s\t-\t-\t-\t-\tNOT SET\n' "$p" "$acct" >>"$ROWS"
    else
      printf '=> THE CALL FAILED for another reason - see section 6. This is NOT evidence\n'
      printf '   about the setting either way.\n'
      printf '[%s] aws s3control get-public-access-block\n    %s\n' \
        "$p" "$(printf '%s' "$OUT_RAW" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
      printf '%s\t%s\t?\t?\t?\t?\tCALL FAILED\n' "$p" "$acct" >>"$ROWS"
    fi
  else
    f_acls=$(printf '%s' "$OUT_RAW"   | grep -o '"BlockPublicAcls"[^,}]*'       | grep -o 'true\|false')
    f_ign=$(printf '%s' "$OUT_RAW"    | grep -o '"IgnorePublicAcls"[^,}]*'      | grep -o 'true\|false')
    f_pol=$(printf '%s' "$OUT_RAW"    | grep -o '"BlockPublicPolicy"[^,}]*'     | grep -o 'true\|false')
    f_restr=$(printf '%s' "$OUT_RAW"  | grep -o '"RestrictPublicBuckets"[^,}]*' | grep -o 'true\|false')
    f_acls="${f_acls:--}"; f_ign="${f_ign:--}"; f_pol="${f_pol:--}"; f_restr="${f_restr:--}"
    if [ "$f_acls" = "true" ] && [ "$f_ign" = "true" ] && \
       [ "$f_pol" = "true" ] && [ "$f_restr" = "true" ]; then
      VERDICT="ALL FOUR true"
      printf '=> ALL FOUR true. Nothing to do here in 7.4 step 1.\n'
    else
      VERDICT="PARTIAL - fix"
      printf '=> PARTIAL. A configuration exists but does not block everything; 7.4 step 1\n'
      printf '   sets all four. Three of four is not a partial pass.\n'
    fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$p" "$acct" "$f_acls" "$f_ign" "$f_pol" "$f_restr" "$VERDICT" >>"$ROWS"
  fi
done <"$LIVE"

# --------------------------------------------------------------------------------------
h1 "3. The verdict table - all four flags, side by side"

{
  printf 'PROFILE\tACCOUNT\tBlockPublicAcls\tIgnorePublicAcls\tBlockPublicPolicy\tRestrictPublicBuckets\tVERDICT\n'
  cat "$ROWS"
} | tabulate

printf '\n'
TOTAL=$(wc -l <"$ROWS" | tr -d ' ')
GOOD=$(grep -c 'ALL FOUR true' "$ROWS" 2>/dev/null || true)
printf '%s of %s measured accounts have all four flags set.\n' "${GOOD:-0}" "$TOTAL"
printf 'THE MEASURED SET IS NOT THE ORGANIZATION - read section 4 before reading this as a\n'
printf 'pass. Three accounts have no profile here by design, and one account nobody\n'
printf 'measures is exactly the hole the account-level setting exists to close.\n'

# --------------------------------------------------------------------------------------
h1 "4. The accounts this laptop cannot reach, and how to read them"

printf 'MANAGEMENT, LOG ARCHIVE and AUDIT hold no project persona (guiding principle 1,\n'
printf 'ORGANIZATION.md), so they cannot appear above. The identity that reaches them is\n'
printf '`AWS Control Tower Admin` through the access portal, and the reading is done in\n'
printf 'CloudShell inside each one:\n\n'
printf '    ./aws/account-bpa.sh -\n\n'
printf 'With `-` the script uses ambient credentials and resolves the account id from\n'
printf 'sts:GetCallerIdentity, so the same command works in all three. Record each answer in\n'
printf 'log/log-stage-01c-preventive-policies.md by hand - a CloudShell run cannot write into\n'
printf 'this snapshot.\n\n'
printf 'ALSO NOT HERE, and none of the three is a gap:\n'
printf '  - `Staging` - not vended. It gets BPA AT THE VEND, with everything else deferred\n'
printf '    there (Stage 1a, "What the deferral leaves owed").\n'
printf '  - Every Sandbox beyond the first - no profile until Stage 14 vends it one, which\n'
printf '    is the stage that owes a BPA step of its own.\n'
printf '  - EXC-01, the SUSPENDED `Sandbox` at the organization root - not this project\n'
printf "    account, runs nothing, cannot be acted on. Do not add it to any list.\n"

# --------------------------------------------------------------------------------------
h1 "5. How to SET it, and the ordering that must not be reversed"

printf 'This script never writes. The command 7.4 step 1 runs, per account:\n\n'
printf '    aws s3control put-public-access-block --account-id <ACCT> --profile <PROFILE> \\\n'
printf '      --public-access-block-configuration \\\n'
printf '      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true\n\n'
printf 'Then re-run this script: every row must read ALL FOUR true BEFORE 7.5 attaches\n'
printf 'awsds-org-scp-baseline.json, which denies s3:PutAccountPublicAccessBlock everywhere\n'
printf 'except the carved-out InfrastructureAccess role (Stage 1c decision 7).\n\n'
printf 'AND NEVER DECLARE aws_s3_account_public_access_block IN A TERRAFORM SLICE. It looks\n'
printf 'exactly like something that belongs in foundation/, and after the deny is attached\n'
printf 'any apply or drift correction touching it fails from every principal except that\n'
printf 'one. plan/conventions.md carries the exclusion.\n'

# --------------------------------------------------------------------------------------
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing or unusable above. Note that\n'
  printf '`NoSuchPublicAccessBlockConfiguration` is NOT here: it is a valid answer, reported\n'
  printf 'as NOT SET in sections 2 and 3.\n\n'
  cat "$ERRORS"
  printf '\nIf a profile did not authenticate:  aws sso login --sso-session %s\n' "$SSO_SESSION"
else
  printf 'None. Every call in this report returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/account-bpa.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 6)"
  exit 1
fi
note "wrote $OUT"
exit 0
