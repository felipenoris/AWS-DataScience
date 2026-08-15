#!/usr/bin/env bash
#
# org-trusted-access-services.sh - which AWS services are allowed to act across this
# organization, and which account administers each of them.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/org-trusted-access-services.sh                   # awsds-infra-identity
#             ./aws/org-trusted-access-services.sh awsds-infra-dev   # a different profile
#             ./aws/org-trusted-access-services.sh -                 # no --profile: run it
#                                                                    # inside CloudShell
#   writes:   aws/output/org-trusted-access-services.txt   (untracked - see .gitignore)
#   reads:    organizations:ListAWSServiceAccessForOrganization,
#             organizations:ListDelegatedAdministrators, sts:GetCallerIdentity.
#             This script never creates, updates or deletes anything.
#
# WHY THIS EXISTS. Trusted access is an organization-level allowlist keyed by *service
# principal*, switched on from the management account. What it grants is not an IAM
# permission and appears in no policy evaluation: it lets the service read the
# organization's structure and create service-linked roles inside member accounts. That is
# Lesson 10's "a service that sets itself up creates principals nobody chose", by design -
# so the list of who holds it is worth being able to re-read rather than remember.
# Delegated administration is the *second*, separate registration: which member account
# operates that service org-wide, so that the management account does not have to.
#
# The list is not static, and every stage that adds to it says so: `access-analyzer` in
# Stage 1b step 8.2, `ram` in Stage 1d step 11 (without which a Lake Formation grant
# silently becomes a pending RAM invitation), then GuardDuty at Stage 4, Security Hub at
# Stage 5 and Macie at Stage 11 - each of those delegations *enables* its service, which is
# why they are not here yet (Stage 1b step 8.1).
#
# IDENTITY, and why a management-account script has a member-account profile. Both calls
# are AWS Organizations reads, and Organizations is administered from the management
# account - for which there is no local profile and never will be (guiding principle 1).
# The default is `awsds-infra-identity`: a delegated administrator for *any* service may
# make a set of Organizations read-only calls, which Stage 1b step 4 measured from this
# account for the calls it used. These two were outside that set until the first run of
# this script, 2026-08-12, and **both returned** - so the read boundary measured in step 4
# covers them too, and no CloudShell session is needed to read this state.
# The script still does not assume it: a denial is reported in full, in section 4, with a
# non-zero exit - and the fallback is one line, in CloudShell on the management account as
# `AWS Control Tower Admin`:
#
#     ./aws/org-trusted-access-services.sh -
#
# Organizations is a global service; --region only picks the endpoint and changes nothing
# about what is returned.

set -uo pipefail

PROFILE="${1:-${AWSDS_PROFILE:-awsds-infra-identity}}"
REGION="us-west-2"
SSO_SESSION="awsds"

# The service principal section 3 is about. One edit moves the whole section.
FOCUS_PRINCIPAL="access-analyzer.amazonaws.com"

# Normally run from inside the repository. The `-` fallback runs it in CloudShell, which
# has no repository, so the root is located rather than assumed and the report lands beside
# the script when there is none.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/org-trusted-access-services.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/org-trusted-access.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"   # one line per failed call
: >"$ERRORS"

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

# aws, always with this script's profile and region. </dev/null so that a call made from
# inside a `while read` loop cannot swallow the loop's input.
aws_() { command aws $PROFILE_OPT --region "$REGION" "$@" </dev/null; }

# capture a call: sets RUN_OUT and RUN_STATUS, logs a failure, prints nothing.
# TOLERATE holds a regex of error text that means "the question does not apply here", not
# "this failed" - a matched error sets RUN_TOLERATED and is kept out of section 4, because
# a section that lists non-problems stops being read (the mirror image of Lesson 13).
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
printf 'Trusted access and delegated administration, per AWS service\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'region    : %s   (AWS Organizations is global; the region only picks an endpoint)\n' "$REGION"
printf 'produced  : aws/org-trusted-access-services.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Trusted access - the services allowed to act across this organization\n'
printf '  2. Delegated administrator for %s\n' "$FOCUS_PRINCIPAL"
printf '  3. Delegated administrators, service by service\n'
printf '  4. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - TWO DIFFERENT REGISTRATIONS, both made only from the management account:\n'
printf '      trusted access        "this SERVICE may act across my organization" - it may\n'
printf '                            read the org structure and create service-linked roles\n'
printf '                            in member accounts. Section 1.\n'
printf '      delegated administr.  "this ACCOUNT administers that service for the whole\n'
printf '                            organization". Sections 2 and 3.\n'
printf '    Trusted access is the prerequisite for the second, not a weaker form of it.\n'
printf '  - SECTION 1 IS AN INVENTORY NOBODY IN THIS PROJECT WROTE. Most of it was enabled\n'
printf '    by Control Tower when the landing zone was installed. A principal there that\n'
printf '    no stage accounts for is a finding, not a detail - docs/log/ and docs/AWS_STATE.md.\n'
printf '  - A service with trusted access and NO delegated administrator is administered\n'
printf '    from the management account. That is the default, not a gap. A service marked\n'
printf '    "no delegated administration for this service" is a third case: it holds\n'
printf '    trusted access and the API rejects the question, Control Tower being one.\n'
printf '  - Every "$ aws ..." line is the exact command that produced the block under it,\n'
printf '    minus `--region %s` and the profile, which every command carries.\n' "$REGION"
printf '  - AN EMPTY BLOCK AND A DENIED CALL ARE NOT THE SAME THING. A call that failed is\n'
printf '    printed with its error and listed again in section 4; anywhere else, empty\n'
printf '    means the call succeeded and returned nothing.\n'
printf '  - This is a point-in-time snapshot, not a source of truth: regenerate it rather\n'
printf '    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

# --------------------------------------------------------------------------------------
h1 "1. Trusted access - the services allowed to act across this organization"

note "listing trusted access..."
show organizations list-aws-service-access-for-organization \
    --query 'EnabledServicePrincipals[].ServicePrincipal' \
    --output table

printf 'Each row is a service that may read this organization and create its own roles\n'
printf 'inside member accounts. Add `DateEnabled` to the --query above to see when each one\n'
printf 'was switched on, which is what distinguishes a landing-zone default from something\n'
printf 'this project turned on.\n'

# --------------------------------------------------------------------------------------
h1 "2. Delegated administrator for $FOCUS_PRINCIPAL"

note "listing the delegated administrator for $FOCUS_PRINCIPAL..."
show organizations list-delegated-administrators \
    --service-principal "$FOCUS_PRINCIPAL" \
    --query 'DelegatedAdministrators[].[Name,Id,Status]' \
    --output table

printf 'Expected: the Audit account, ACTIVE - registered in Stage 1b step 8.2, and the\n'
printf 'precondition for the organization-level Access Analyzer that lives there. An empty\n'
printf 'result means the registration is absent, not that it is pending.\n'

# --------------------------------------------------------------------------------------
h1 "3. Delegated administrators, service by service"

note "listing delegated administrators for every enabled principal..."
run organizations list-aws-service-access-for-organization \
    --query 'EnabledServicePrincipals[].ServicePrincipal' \
    --output text
PRINCIPALS=$(printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | grep -v '^$' | sort)

if [ -z "$PRINCIPALS" ]; then
  printf 'No service principal returned - see section 4.\n'
else
  {
    printf 'SERVICE PRINCIPAL\tDELEGATED ADMIN\tACCOUNT ID\tSTATUS\n'
    while IFS= read -r sp; do
      [ -n "$sp" ] || continue
      TOLERATE='unrecognized service principal'
      run organizations list-delegated-administrators \
          --service-principal "$sp" \
          --query 'DelegatedAdministrators[].[Name,Id,Status]' \
          --output text
      TOLERATE=""
      if [ "$RUN_STATUS" -ne 0 ]; then
        printf '%s\t!! call failed - see section 4\t-\t-\n' "$sp"
      elif [ "$RUN_TOLERATED" -eq 1 ]; then
        printf '%s\t(no delegated administration for this service)\t-\t-\n' "$sp"
      elif [ -z "$RUN_OUT" ]; then
        printf '%s\t(none - management account)\t-\t-\n' "$sp"
      else
        printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r name id status; do
          [ -n "${name:-}" ] || continue
          printf '%s\t%s\t%s\t%s\n' "$sp" "$name" "$id" "$status"
        done
      fi
    done <<PRINCIPALS
$PRINCIPALS
PRINCIPALS
  } | tabulate
  printf '\n'
  printf 'Section 2 is one row of this table, kept separate because it is the one Stage 1b\n'
  printf 'step 8.2 creates and verifies. Everything else here is the landing zone, until a\n'
  printf 'later stage delegates GuardDuty (Stage 4), Security Hub (Stage 5), RAM (Stage 1d\n'
  printf 'step 11) or Macie (Stage 11).\n'
fi

# --------------------------------------------------------------------------------------
h1 "4. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
  printf '\nIf these are AccessDenied: both calls are AWS Organizations reads, and this\n'
  printf 'profile may not be inside the read-only set a delegated administrator is allowed.\n'
  printf 'Re-run from CloudShell on the MANAGEMENT account, as `AWS Control Tower Admin`:\n'
  printf '  ./aws/org-trusted-access-services.sh -\n'
  printf 'and record in docs/log/ which identity the answer actually required.\n'
else
  printf 'None. Every call in this report returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/org-trusted-access-services.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 4)"
  exit 1
fi
note "wrote $OUT"
exit 0
