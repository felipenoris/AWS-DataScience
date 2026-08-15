#!/usr/bin/env bash
#
# audit-iam-analyser.sh - the IAM Access Analyzer analyzers of one account and Region: what
# each one is, what it is scoped to, and what it has found.
#
#   run:      IN CLOUDSHELL, on the Audit account, as `AWS Control Tower Admin`. CloudShell
#             does not have this repository, so upload this one file - Actions -> Upload
#             file - and run it where it lands:
#
#                 bash audit-iam-analyser.sh
#
#             It notices there is no repository around it and writes the report beside
#             itself instead of into aws/output/cloudshell/. Download it from the same menu, or read it
#             there and paste what matters into docs/log/.
#
#             with a named profile, if one ever exists for this account:
#
#                 ./aws/cloudshell/audit-iam-analyser.sh <profile>
#                 AWSDS_AUDIT_PROFILE=<profile> ./aws/cloudshell/audit-iam-analyser.sh
#
#   writes:   aws/output/cloudshell/audit-iam-analyser.txt   (untracked - see .gitignore)
#   reads:    accessanalyzer:ListAnalyzers, GetAnalyzer, ListArchiveRules, ListFindingsV2,
#             sts:GetCallerIdentity and - only to name the account - organizations:
#             DescribeAccount. This script never creates, updates or deletes anything.
#
# WHY IT DEFAULTS TO NO PROFILE, which is the opposite of every other script here.
# `aws/INDEX.md` asks for one named profile per script, with the reason that profile can
# see what it sees. The reason here is that there is no profile, and that is deliberate
# rather than missing: the organization-level analyzer lives in the **Audit** account
# (Stage 1b step 8.2), and no project persona holds an assignment there - `docs/ORGANIZATION.md`
# records that as permanent, for the same reason Log Archive has none. The only human who
# reaches Audit is `AWS Control Tower Admin`, through Control Tower's own group, and D33/D34
# keep that identity in the console. So the intended run is CloudShell **inside Audit**, and
# the argument exists so the script does not have to be rewritten the day that changes.
#
# WHAT IT CANNOT SEE, stated because an empty section and a missing one look alike:
#   - ANOTHER ACCOUNT. Access Analyzer is per-account: run from anywhere else this reports
#     that account's analyzers, not Audit's, and says so in section 1 rather than failing.
#     The delegated-administrator *registration* is the other half and lives in
#     ./aws/org-trusted-access-services.py, which reads it from the Identity account.
#   - ANOTHER REGION. Analyzers are regional. This reads us-west-2 only.
#   - THE ZONE OF TRUST IS NOT VISIBLE IN A FINDING. It is the analyzer's `type`, which is
#     why section 5 checks it: an ACCOUNT analyzer in Audit runs, stays ACTIVE, reports
#     nothing outside Audit, and looks exactly like a working organization analyzer
#     (Lesson 13). NO FINDINGS IS NOT EVIDENCE EITHER WAY - see section 4.

set -uo pipefail

# `-` / `none` means ambient credentials: CloudShell, or an assumed role in the shell.
PROFILE="${1:-${AWSDS_AUDIT_PROFILE:-none}}"
REGION="us-west-2"
SSO_SESSION="awsds"

# The account this is meant to run in, matched by name against Organizations. No account id
# is written into a tracked file (aws/INDEX.md, rule 1), so the check is on the name.
EXPECTED_ACCOUNT_MATCH="Audit"

# The intended runtime is CloudShell, which does NOT have this repository - the script is
# uploaded on its own (CloudShell: Actions -> Upload file). So the repository root is
# located rather than assumed, and the report lands beside the script when there is no
# repository to land in. Writing to `aws/output/cloudshell/` relative to a home directory that is not
# the repo is how a snapshot ends up somewhere nobody looks.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/../.."
  OUT_DIR="aws/output/cloudshell"
  STANDALONE=0
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
  STANDALONE=1
fi
OUT="$OUT_DIR/audit-iam-analyser.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/audit-iam-analyser.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"        # one line per failed call
ANALYZERS="$TMP/analyzers.tsv"  # name <tab> arn <tab> type <tab> status
: >"$ERRORS"; : >"$ANALYZERS"

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
# "this failed" - a matched error sets RUN_TOLERATED and is kept out of the last section.
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
  note "the intended run is CloudShell on the Audit account, as AWS Control Tower Admin."
  note "with a profile instead:  aws sso login --sso-session $SSO_SESSION"
  note ""
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi
ACCOUNT_ID=$(command aws $PROFILE_OPT --region "$REGION" \
               sts get-caller-identity --query 'Account' --output text 2>/dev/null)
note "caller : $CALLER"

# Name the account rather than trusting the operator to be where they think they are. This
# is the check the console wizard did not have: it named the zone of trust and never the
# account the analyzer was born in (Stage 1b step 8.2, log entry of 2026-08-12).
TOLERATE='AccessDenied|AWSOrganizationsNotInUse'
run organizations describe-account --account-id "$ACCOUNT_ID" \
    --query 'Account.Name' --output text
ACCOUNT_NAME="$RUN_OUT"
TOLERATE=""
if [ -z "$ACCOUNT_NAME" ]; then
  ACCOUNT_NAME="(could not resolve - the Organizations read was denied from here)"
  ACCOUNT_VERDICT="UNCONFIRMED"
elif printf '%s' "$ACCOUNT_NAME" | grep -q "$EXPECTED_ACCOUNT_MATCH"; then
  ACCOUNT_VERDICT="OK"
else
  ACCOUNT_VERDICT="WRONG ACCOUNT"
fi
note "account: $ACCOUNT_NAME [$ACCOUNT_VERDICT]"

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'IAM Access Analyzer - the analyzers of one account, and what they found\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'account   : %s   [%s]\n' "$ACCOUNT_NAME" "$ACCOUNT_VERDICT"
printf 'region    : %s   (analyzers are regional - another Region is invisible here)\n' "$REGION"
printf 'produced  : aws/cloudshell/audit-iam-analyser.sh   (index: aws/INDEX.md)\n'
[ "$STANDALONE" -eq 1 ] && printf 'note      : run outside the repository - this report is beside the script, not in aws/output/cloudshell/\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Where this ran - and whether it is the account it was meant to run in\n'
printf '  2. The analyzers in this account and Region\n'
printf '  3. Each analyzer in full: tags, and its archive rules\n'
printf '  4. Findings\n'
printf '  5. CHECK: one analyzer, ORGANIZATION, ACTIVE\n'
printf '  6. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - THE ZONE OF TRUST IS THE `type` COLUMN, and it is the whole point of section 5.\n'
printf '    ORGANIZATION means anything reachable from outside THIS ORGANIZATION is a\n'
printf '    finding. ACCOUNT means anything reachable from outside THIS ACCOUNT is - which\n'
printf '    in Audit would report on an almost empty account and miss the entire estate,\n'
printf '    while staying ACTIVE and raising nothing.\n'
printf '  - NO FINDINGS IS NOT EVIDENCE THAT THE ANALYZER WORKS, and it is not evidence\n'
printf '    that nothing is exposed either. Access inside the organization is not external\n'
printf '    to an organization zone of trust, and the estate is nearly empty until Stages\n'
printf '    2-3. What section 4 is for is the day that stops being true.\n'
printf '  - Every "$ aws ..." line is the exact command that produced the block under it,\n'
printf '    minus `--region %s` and the profile, which every command carries.\n' "$REGION"
printf '  - AN EMPTY BLOCK AND A DENIED CALL ARE NOT THE SAME THING. A call that failed is\n'
printf '    printed with its error and listed again in section 6.\n'
printf '  - This is a point-in-time snapshot, not a source of truth: regenerate it rather\n'
printf '    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

# --------------------------------------------------------------------------------------
h1 "1. Where this ran - and whether it is the account it was meant to run in"

{
  printf 'FIELD\tVALUE\n'
  printf 'caller ARN\t%s\n' "$CALLER"
  printf 'account name\t%s\n' "$ACCOUNT_NAME"
  printf 'expected to match\t%s\n' "$EXPECTED_ACCOUNT_MATCH"
  printf 'verdict\t%s\n' "$ACCOUNT_VERDICT"
} | tabulate
printf '\n'

case "$ACCOUNT_VERDICT" in
  OK)
    printf 'This is the account Stage 1b step 8.2 puts the organization analyzer in.\n' ;;
  UNCONFIRMED)
    printf '!! The account NAME could not be read, so nothing below is attributed to a\n'
    printf 'named account. The caller ARN above carries the account id - check it by eye\n'
    printf 'before reading sections 2-5 as being about Audit.\n' ;;
  *)
    printf '!! THIS IS NOT THE AUDIT ACCOUNT. Sections 2-5 describe a different account,\n'
    printf 'and an empty section 2 here says nothing about the organization analyzer. This\n'
    printf 'is the exact mistake the console wizard produced on 2026-08-12: it named the\n'
    printf 'zone of trust and never the account the analyzer was created in.\n' ;;
esac

# --------------------------------------------------------------------------------------
h1 "2. The analyzers in this account and Region"

note "listing analyzers..."
show accessanalyzer list-analyzers \
    --query 'sort_by(analyzers, &name)[].[name,type,status,createdAt,lastResourceAnalyzedAt]' \
    --output table

run accessanalyzer list-analyzers \
    --query 'sort_by(analyzers, &name)[].[name,arn,type,status]' --output text
printf '%s\n' "$RUN_OUT" | grep -v '^$' >"$ANALYZERS"
N_ANALYZERS=$(grep -c . "$ANALYZERS" || true)

printf 'The plan creates exactly one here: `awsds-org-external-access`, type ORGANIZATION\n'
printf '(Stage 1b step 8.2). `lastResourceAnalyzedAt` empty on a freshly created analyzer is\n'
printf 'normal - it fills in once the first scan completes.\n'
printf '\n'
printf 'The paid half - unused-access findings, an ORGANIZATION_UNUSED_ACCESS analyzer - is\n'
printf 'Stage 12 and must NOT appear here yet. Two analyzers of that type is a bill.\n'

# --------------------------------------------------------------------------------------
h1 "3. Each analyzer in full: tags, and its archive rules"

if [ "${N_ANALYZERS:-0}" -eq 0 ]; then
  printf 'No analyzer in this account and Region, so nothing to detail. If this was meant\n'
  printf 'to be Audit, see the verdict in section 1 before concluding anything.\n'
else
  while IFS=$'\t' read -r name arn type status; do
    [ -n "${name:-}" ] || continue
    h2 "$name"

    show accessanalyzer get-analyzer --analyzer-name "$name" --output table

    printf '  archive rules\n\n'
    show accessanalyzer list-archive-rules --analyzer-name "$name" \
        --query 'archiveRules[].[ruleName,createdAt,updatedAt]' --output table
  done <"$ANALYZERS"

  printf 'An ARCHIVE RULE SUPPRESSES FINDINGS THAT MATCH IT, at creation time and forever\n'
  printf 'after. None is expected here: the plan creates no rule, so a rule appearing in\n'
  printf 'this section is a finding about the finding pipeline (Lesson 13 - a control that\n'
  printf 'silently stops reporting looks exactly like one that has nothing to report).\n'
fi

# --------------------------------------------------------------------------------------
h1 "4. Findings"

if [ "${N_ANALYZERS:-0}" -eq 0 ]; then
  printf 'No analyzer, so no findings. That is arithmetic, not a clean bill of health.\n'
else
  while IFS=$'\t' read -r name arn type status; do
    [ -n "${name:-}" ] || continue
    h2 "$name  ($type)"

    show accessanalyzer list-findings-v2 --analyzer-arn "$arn" \
        --query 'findings[].[status,findingType,resourceType,resourceOwnerAccount,resource]' \
        --output table

    run accessanalyzer list-findings-v2 --analyzer-arn "$arn" \
        --query 'length(findings)' --output text
    printf '  count: %s\n' "${RUN_OUT:-(call failed - see section 6)}"
    printf '\n'
  done <"$ANALYZERS"

  printf 'THE COUNT IS THE EVIDENCE, NOT THE EMPTY TABLE. `--output table` on an empty list\n'
  printf 'prints nothing at all, which is indistinguishable from a command that did not run\n'
  printf -- '- so the count line above is printed even when it is 0.\n'
  printf '\n'
  printf 'A finding here names a resource reachable from OUTSIDE the zone of trust. With an\n'
  printf 'ORGANIZATION analyzer that means outside this organization entirely: a bucket\n'
  printf 'policy, a role trust policy, a KMS key policy or a queue policy granting to a\n'
  printf 'principal that is not one of ours. `resourceOwnerAccount` says which account it\n'
  printf 'is in, which is what makes an organization analyzer worth more than nine account\n'
  printf 'ones.\n'
fi

# --------------------------------------------------------------------------------------
h1 "5. CHECK: one analyzer, ORGANIZATION, ACTIVE"

# A failed row is recorded in a FILE, not in a variable. The table below is built inside a
# `| tabulate` pipeline, and the left side of a pipe runs in a subshell - so a variable set
# in there is lost by the time the verdict is printed, and the verdict would read OK while
# the table above it reads !! DIFFERS. A verdict that cannot disagree with its own table is
# Lesson 13 wearing a different hat.
FAILED_MARK="$TMP/check-failed"
rm -f "$FAILED_MARK"

if [ "${N_ANALYZERS:-0}" -eq 0 ]; then
  printf '!! CHECK FAILED: no analyzer in this account and Region.\n'
  : >"$FAILED_MARK"
else
  {
    printf 'ANALYZER\tTYPE\tSTATUS\tVERDICT\n'
    while IFS=$'\t' read -r name arn type status; do
      [ -n "${name:-}" ] || continue
      verdict="OK"
      [ "$type" = "ORGANIZATION" ] || { verdict="!! NOT AN ORGANIZATION ZONE OF TRUST"; : >"$FAILED_MARK"; }
      [ "$status" = "ACTIVE" ] || { verdict="!! NOT ACTIVE"; : >"$FAILED_MARK"; }
      printf '%s\t%s\t%s\t%s\n' "$name" "$type" "$status" "$verdict"
    done <"$ANALYZERS"
  } | tabulate
  printf '\n'

  if [ "$N_ANALYZERS" -gt 1 ]; then
    printf '!! %s analyzers in one account and Region. Each one is a separate zone of trust\n' "$N_ANALYZERS"
    printf 'reporting separately; an unused-access one also bills per resource per month.\n'
    : >"$FAILED_MARK"
  fi
fi

if [ -f "$FAILED_MARK" ]; then CHECK_FAILED=1; else CHECK_FAILED=0; fi

printf '\n'
if [ "$ACCOUNT_VERDICT" != "OK" ]; then
  printf 'AND THE VERDICT ABOVE IS SCOPED TO THE WRONG QUESTION: section 1 could not confirm\n'
  printf 'this is the Audit account, so a passing check here is a check about some other\n'
  printf 'account. Read section 1 first.\n'
elif [ "$CHECK_FAILED" -eq 0 ]; then
  printf 'CHECK OK: exactly one analyzer, ORGANIZATION zone of trust, ACTIVE, in the Audit\n'
  printf 'account. This is what Stage 1b step 8.2 is required to leave behind - and it says\n'
  printf 'nothing about whether anything has been found, which section 4 covers.\n'
fi

# --------------------------------------------------------------------------------------
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
else
  printf 'None. Every call in this report returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/cloudshell/audit-iam-analyser.sh   (CloudShell, on Audit)\n'

return "$CHECK_FAILED"
}

# ---------------------------------------------------------------------------------- run

main >"$OUT"
status=$?

note ""
if [ "$ACCOUNT_VERDICT" = "WRONG ACCOUNT" ]; then
  note "wrote $OUT (WRONG ACCOUNT - see section 1)"
elif [ "$status" -ne 0 ]; then
  note "wrote $OUT (CHECK FAILED - see section 5)"
else
  note "wrote $OUT"
fi
if [ -s "$ERRORS" ]; then
  note "some calls failed - see section 6"
fi
exit "$status"
