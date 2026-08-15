#!/usr/bin/env bash
#
# management-quotas.sh - the AWS Organizations quotas, and whether the account-cap increase has landed.
#
#   needs:    CloudShell on the MANAGEMENT account, as `AWS Control Tower Admin`.
#             There is no laptop path - see IDENTITY below.
#
#   run:      ./aws/cloudshell/management-quotas.sh                    # ambient credentials (CloudShell)
#             ./aws/cloudshell/management-quotas.sh <profile>          # if a profile ever reaches Management
#   writes:   aws/output/cloudshell/management-quotas.txt   (untracked - see .gitignore)
#   reads:    servicequotas:ListServiceQuotas, GetServiceQuota,
#             ListRequestedServiceQuotaChangeHistoryByQuota,
#             organizations:DescribeOrganization, ListAccounts, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything, and it never REQUESTS an increase.
#   exits:    0 the report was produced | 1 a call failed
#
# WHY THIS EXISTS, AND IT IS ONE NUMBER. The `Staging` vend is the last item the landing zone
# left open, and it is held on `Maximum number of accounts` - measured 10 during Stage 1c
# step 7.0, against the 15 that were requested. Stage 2 step 3.2 skips staging/bootstrap/ for
# exactly that reason, and Stage 8 is the first stage that actually needs the account. So
# "has the increase landed" is a question somebody asks every few weeks, and it should not
# require remembering which console page shows it.
#
# THE MEASUREMENT ONLY MEANS SOMETHING FROM MANAGEMENT, and this is the trap the script is
# built around. From a MEMBER account the same quota reads 0.0 - Service Quotas answers about
# the account it is asked in, and a member account has no authority to create accounts at all.
# Since 7.7 a governed member does not even get the 0.0: the Region ceiling denies
# servicequotas:* in us-east-1 outright, naming its policy (measured 2026-08-15). Either
# way a run from awsds-infra-identity does not return the real number, it returns a MEANINGLESS
# one, and 0.0 read as "the cap is zero" is worse than no reading. Section 1 therefore resolves
# which account answered BEFORE printing any quota, and refuses to interpret the number if it
# is not Management - the same check audit-iam-analyser.sh makes for the same reason.
#
# QUOTA CODES ARE DISCOVERED, NEVER TYPED. `list-service-quotas` is paged and printed whole,
# and the account cap is then picked out by NAME. A hardcoded `L-...` that AWS renames or
# re-scopes reports the wrong number confidently, which is the failure mode this whole folder
# is written against. The full list is worth printing anyway: Stage 1c step 7.0 established
# that Service Quotas publishes NO policy-size quota for `organizations`, and that absence is
# only visible if the list is shown rather than filtered.
#
# THE QUOTAS OF A GLOBAL SERVICE LIVE IN us-east-1, and the first authoritative run proved
# it (2026-08-15): from Management, us-west-2 answers NoSuchResourceException for the whole
# `organizations` service-code - not an empty list. Organizations is homed in N. Virginia,
# so the three service-quotas calls below carry `--region us-east-1` explicitly (the last
# --region on a command wins), while sts/organizations stay on the script's default Region.
# The 1a log recorded the same fact from the console: the increase had to be requested
# under us-east-1.
#
# WHAT IT DELIBERATELY DOES NOT DO: request an increase. `request-service-quota-increase` is a
# write, it is one command, and it belongs to a human on Management - the same line aws/probes/
# draws. The script prints the command with its arguments filled in and stops there.
#
# IDENTITY. Management holds no CLI profile by design (D33/D34), so this is a CloudShell
# script like audit-iam-analyser.sh: sign in to the access portal as `AWS Control Tower Admin`,
# open CloudShell on the Management account with `AWSAdministratorAccess`, clone or paste, run.
# It takes a profile argument in case one ever exists there, and refuses to interpret the
# result from anywhere else.

set -uo pipefail

PROFILE="${1:--}"
REGION="us-west-2"
QUOTAS_REGION="us-east-1"   # Organizations is global and homed in N. Virginia - see the header
SSO_SESSION="awsds"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/../.."
  OUT_DIR="aws/output/cloudshell"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/management-quotas.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/management-quotas.XXXXXX")
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

# ------------------------------------------------------------------ read the account cap

note "listing the organizations quotas..."

run service-quotas list-service-quotas --region "$QUOTAS_REGION" --service-code organizations \
    --query 'Quotas[].[QuotaCode,QuotaName,Value,Adjustable]' --output text
QUOTAS="$TMP/quotas.tsv"
printf '%s\n' "$RUN_OUT" >"$QUOTAS"

# Pick the account cap by NAME, and print what matched, so a rename is visible rather than
# silently producing a different row.
CAP_LINE=$(grep -i 'number of accounts' "$QUOTAS" | head -1)
CAP_CODE=$(printf '%s' "$CAP_LINE" | cut -f1)
CAP_NAME=$(printf '%s' "$CAP_LINE" | cut -f2)
CAP_VALUE=$(printf '%s' "$CAP_LINE" | cut -f3)

# The APPLIED value can differ from the default one; get-service-quota is the authority.
APPLIED=""
if [ -n "${CAP_CODE:-}" ]; then
  run service-quotas get-service-quota --region "$QUOTAS_REGION" \
      --service-code organizations --quota-code "$CAP_CODE" \
      --query 'Quota.Value' --output text
  APPLIED="${RUN_OUT:-}"
fi

run organizations list-accounts --query 'length(Accounts)' --output text
N_ACCOUNTS="${RUN_OUT:-?}"

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'AWS Organizations quotas - and whether the account cap has moved\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'produced  : aws/cloudshell/management-quotas.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Where this ran - read it FIRST, the number is meaningless elsewhere\n'
printf '  2. The account cap, and how much of it is spent\n'
printf '  3. Pending increase requests\n'
printf '  4. Every organizations quota, unfiltered\n'
printf '  5. How to request an increase - NOT performed here\n'
printf '  6. Calls that failed\n'

# ======================================================================================
h1 "1. Where this ran - read it FIRST"

{
  printf 'FIELD\tVALUE\n'
  printf 'caller ARN\t%s\n' "$CALLER"
  printf 'account id\t%s\n' "${CALLER_ACCT:-(unknown)}"
  printf 'management account\t%s\n' "${MGMT_ID:-(unread)}"
  printf 'is Management\t%s\n' "$IS_MGMT"
} | tabulate

printf '\n'
if [ "$IS_MGMT" = "yes" ]; then
  printf 'This ran in the MANAGEMENT account, which is the only place the number in section 2\n'
  printf 'means anything.\n'
else
  printf '!! THIS DID NOT RUN IN THE MANAGEMENT ACCOUNT, SO SECTION 2 IS NOT AN ANSWER.\n\n'
  printf 'Service Quotas answers about the account it is asked in, and a member account has no\n'
  printf 'authority to create accounts at all - so the cap reads 0.0 there. That is not "the\n'
  printf 'cap is zero"; it is "you asked the wrong account", and the two look identical if\n'
  printf 'nobody checks. Re-run from CloudShell on Management as `AWS Control Tower Admin`.\n'
fi

# ======================================================================================
h1 "2. The account cap, and how much of it is spent"

if [ -n "${CAP_LINE:-}" ]; then
  {
    printf 'FIELD\tVALUE\n'
    printf 'quota name\t%s\n' "$CAP_NAME"
    printf 'quota code\t%s\n' "$CAP_CODE"
    printf 'default value\t%s\n' "$CAP_VALUE"
    printf 'APPLIED value\t%s\n' "${APPLIED:-(unread)}"
    printf 'accounts in the organization\t%s\n' "$N_ACCOUNTS"
  } | tabulate
  printf '\n'
  printf 'THE APPLIED VALUE IS THE ONE THAT DECIDES. A default and an applied quota differ\n'
  printf 'exactly when an increase has been granted, which is the whole question here.\n'
  printf '\n'
  printf 'Expected as of 2026-08-15: applied 10, requested 15, NOT yet granted. The count\n'
  printf 'includes the suspended account at the root that is not ours (docs/AWS_STATE.md EXC-01),\n'
  printf 'so it is one higher than the accounts this project owns.\n'
  printf '\n'
  printf 'WHAT IS WAITING ON IT: the `Staging` vend (Stage 1a, deferred), and with it\n'
  printf 'terraform-live/staging/bootstrap/ (Stage 2 step 3.2) and the Staging assignments of\n'
  printf 'Stage 2 step 5. Stage 8 is the first stage that cannot proceed without the account.\n'
else
  printf '(no quota whose name matches "number of accounts" - see section 4 for the full list,\n'
  printf 'and section 6 if the call failed. A rename is the likely cause, and it is why the\n'
  printf 'code is matched by name rather than hardcoded.)\n'
fi

# ======================================================================================
h1 "3. Pending increase requests"

if [ -n "${CAP_CODE:-}" ]; then
  show service-quotas list-requested-service-quota-change-history-by-quota --region "$QUOTAS_REGION" \
      --service-code organizations --quota-code "$CAP_CODE" \
      --query 'RequestedQuotas[].[Status,DesiredValue,Created,LastUpdated]' --output table
  printf 'A `CASE_OPENED` or `PENDING` row is the request still in flight. An `APPROVED` row\n'
  printf 'whose DesiredValue matches section 2`s APPLIED value is the increase having landed.\n'
  printf 'AN EMPTY TABLE MEANS NO REQUEST WAS EVER MADE THROUGH SERVICE QUOTAS - which is a\n'
  printf 'real possibility if it was raised as a support case instead, and it is not the same\n'
  printf 'as "the request was refused".\n'
else
  printf '(no quota code resolved - see section 2)\n'
fi

# ======================================================================================
h1 "4. Every organizations quota, unfiltered"

printf 'Printed whole rather than filtered, because an ABSENCE here is a finding: Stage 1c\n'
printf 'step 7.0 established that Service Quotas publishes NO policy-size quota for\n'
printf '`organizations`, so the SCP size budget is the documentation`s number and not a\n'
printf 'measurable one. That is only visible if the list is shown.\n\n'

if [ -s "$QUOTAS" ] && grep -q . "$QUOTAS"; then
  {
    printf 'CODE\tNAME\tVALUE\tADJUSTABLE\n'
    sort -k2 "$QUOTAS"
  } | tabulate
else
  printf '(nothing returned - see section 6)\n'
fi

# ======================================================================================
h1 "5. How to request an increase - NOT performed here"

printf 'This script reads. Requesting an increase is a write, and it belongs to a human on\n'
printf 'Management - the same line aws/probes/ draws around anything that can change state.\n'
printf 'The command, with the arguments already resolved:\n\n'
printf '    aws service-quotas request-service-quota-increase \\\n'
printf '        --region us-east-1 \\\n'
printf '        --service-code organizations \\\n'
printf '        --quota-code %s \\\n' "${CAP_CODE:-<resolve from section 2>}"
printf '        --desired-value 15\n\n'
printf 'Run it in CloudShell on Management as `AWS Control Tower Admin`, and record the\n'
printf 'request id in docs/log/log-stage-01a-landing-zone.md. The deferral`s owed list lives in\n'
printf 'docs/plan/stages/stage-01a-landing-zone.md, "What the deferral leaves owed".\n'

# ======================================================================================
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  cat "$ERRORS"
  printf '\nAn AccessDenied on service-quotas from a member account is the expected shape of\n'
  printf '"wrong account" - see section 1. A NoSuchResourceException names the wrong REGION:\n'
printf 'these quotas answer only in us-east-1 - see the header.\n'
else
  printf 'None. Every call returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/cloudshell/management-quotas.sh          (CloudShell on Management)\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 6)"
  exit 1
fi
if [ "$IS_MGMT" != "yes" ]; then
  note "wrote $OUT (NOT the management account - section 2 is not an answer)"
  exit 0
fi
note "wrote $OUT"
exit 0
