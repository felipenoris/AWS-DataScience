#!/usr/bin/env bash
#
# declarative-ec2.sh - the four EC2 settings awsds-org-declarative-ec2 declares, read back
# from each account, one row per account per attribute.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/declarative-ec2.sh                       every awsds-* profile
#             ./aws/declarative-ec2.sh awsds-infra-dev ...   only the profiles named
#             ./aws/declarative-ec2.sh -                     no --profile: CloudShell, for
#                                                            the three accounts with none
#   writes:   aws/output/declarative-ec2.txt   (untracked - see .gitignore)
#   reads:    ec2:GetImageBlockPublicAccessState, ec2:GetSnapshotBlockPublicAccessState,
#             ec2:GetSerialConsoleAccessStatus, ec2:GetInstanceMetadataDefaults,
#             organizations:DescribeEffectivePolicy, sts:GetCallerIdentity.
#             This script never creates, updates or deletes anything.
#   exits:    0 every measured account matches the document | 1 a call failed or a value
#             does not match
#
# WHY THIS EXISTS AND THE BATTERY DOES NOT COVER IT. A declarative policy is enforced in the
# SERVICE's control plane, not in authorization - so it produces no "explicit deny", names no
# policy id, and governs service-linked roles, which no SCP does. The SCP battery can only
# show that an account is REFUSED when it tries to change one of these settings. It cannot
# show what the setting IS, and the setting is the control. That is this script.
#
# The two instruments answer different questions and both are needed:
#
#   ./aws/probes/scp-battery.sh --phase decl   does the account get refused, and does it
#                                              receive OUR exception message?
#   ./aws/declarative-ec2.sh                   is the value actually what the document says?
#
# WHAT MAKES THE SECOND QUESTION NON-OBVIOUS: attaching this policy CHANGES EXISTING STATE in
# every account it reaches, which none of 7.5/7.6/7.7's documents do - those only constrain
# future calls. Detaching rolls each attribute back to whatever it was before the attach
# (AWS Organizations user guide). So "attached" and "in effect" are two facts here, and only
# the second one is a control.
#
# TWO VOCABULARIES, and they do not match, which is the trap this script exists to absorb:
# the policy document writes `block_all_sharing` and `disabled`; the EC2 API answers
# `block-all-sharing` and `false`. The expected values below are therefore written in the
# API's spelling and mapped by hand - deriving them from the JSON would be a translation
# nobody reviews.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - MANAGEMENT, LOG ARCHIVE and AUDIT have no profile on this laptop and never will
#     (guiding principle 1). Run this with `-` in CloudShell inside each and record the three
#     answers by hand. MANAGEMENT MATTERS HERE IN A WAY IT DOES NOT ELSEWHERE: it is exempt
#     from SCPs and RCPs, but AWS documents no such exemption for declarative policies, so a
#     root attach is expected to reach it. That expectation is UNMEASURED until someone runs
#     this there, and it is the one reading that decides it.
#   - `Staging` is not vended; every Sandbox beyond the first has no profile until Stage 14.
#   - EXC-01, the SUSPENDED `Sandbox` at the organization root, is not this project's.

set -uo pipefail

REGION="us-west-2"
SSO_SESSION="awsds"
PROFILE_PREFIX="awsds-"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/declarative-ec2.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/declarative-ec2.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"; : >"$ERRORS"
ROWS="$TMP/rows.tsv";     : >"$ROWS"
CALLERS="$TMP/callers.tsv"; : >"$CALLERS"
BAD=0

note() { printf '%s\n' "$*" >&2; }
h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
tabulate() { column -t -s $'\t'; }

aws_() { # aws_ <profile> <args...>
  local p="$1"; shift
  if [ "$p" = "-" ] || [ "$p" = "none" ]; then
    command aws --region "$REGION" "$@" </dev/null
  else
    command aws --profile "$p" --region "$REGION" "$@" </dev/null
  fi
}

# ------------------------------------------------------------------ the four attributes
#
# name | the aws ec2 sub-command | the --query that isolates the value | expected (API spelling)
#
# The expected column is the DOCUMENT translated into what the API answers. Change the
# document and this list has to change with it - which is deliberate: the translation is
# where a mistake would otherwise hide, so it is written where a reviewer will see it.
ATTRS=$(cat <<'ROWS'
image_block_public_access	get-image-block-public-access-state	ImageBlockPublicAccessState	block-new-sharing
snapshot_block_public_access	get-snapshot-block-public-access-state	State	block-all-sharing
serial_console_access	get-serial-console-access-status	SerialConsoleAccessEnabled	False
instance_metadata_defaults.http_tokens	get-instance-metadata-defaults	AccountLevel.HttpTokens	required
ROWS
)

# ------------------------------------------------------------ which profiles to measure

if [ "$#" -gt 0 ]; then
  PROFILES=$(printf '%s\n' "$@")
  PROFILE_SOURCE="named on the command line"
else
  PROFILES=$(command aws configure list-profiles 2>/dev/null | grep "^$PROFILE_PREFIX" | sort)
  PROFILE_SOURCE="every '$PROFILE_PREFIX*' profile in ~/.aws/config"
fi
[ -n "$PROFILES" ] || { note "no profiles to measure ($PROFILE_SOURCE matched nothing)"; exit 1; }

note "region: $REGION"
LIVE="$TMP/live.txt"; : >"$LIVE"
while IFS= read -r p; do
  [ -n "$p" ] || continue
  if out=$(aws_ "$p" sts get-caller-identity --query '[Account,Arn]' --output text 2>&1); then
    printf '%s\t%s\t%s\n' "$p" "$(printf '%s' "$out" | awk '{print $1}')" "$(printf '%s' "$out" | awk '{print $2}')" >>"$CALLERS"
    printf '%s\t%s\n' "$p" "$(printf '%s' "$out" | awk '{print $1}')" >>"$LIVE"
    note "  $p  OK"
  else
    printf '%s\t-\t(failed)\n' "$p" >>"$CALLERS"
    printf '[%s] sts get-caller-identity\n    %s\n' "$p" "$(printf '%s' "$out" | head -2 | tr '\n' ' ')" >>"$ERRORS"
    note "  $p  FAILED"
  fi
done <<PROFILES
$PROFILES
PROFILES

if [ ! -s "$LIVE" ]; then
  note ""
  note "no profile authenticated. log in first:"
  note "  aws sso login --sso-session $SSO_SESSION"
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi

# ------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'EC2 declarative policy - the settings, read back per account\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'document  : terraform-live/identity/org-policies/policies/awsds-org-declarative-ec2.json\n'
printf 'profiles  : %s\n' "$PROFILE_SOURCE"
printf 'region    : %s\n' "$REGION"
printf 'produced  : aws/declarative-ec2.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - A `MISMATCH` row is not necessarily a failure of the policy. Before the document\n'
printf '    is attached EVERY row mismatches, and that is the before-reading. After the\n'
printf '    attach, a mismatch is either an account the attachment does not reach or a\n'
printf '    setting that was changed and did not roll forward - both are findings.\n'
printf '  - `not-set` IS AN ANSWER, not an error: it is what an account returns for an\n'
printf '    attribute nobody has ever configured. It is reported as a mismatch, because a\n'
printf '    control that is not set is not a control.\n'
printf '  - THE MEASURED SET IS NOT THE ORGANIZATION. Section 4 names the accounts this\n'
printf '    laptop cannot reach; one of them is MANAGEMENT, and whether a root-attached\n'
printf '    declarative policy reaches it is UNDECIDED by AWS documentation.\n'
printf '  - Section 3 is the effective policy as Organizations computes it, which answers a\n'
printf '    different question from section 2: what the account is SUPPOSED to have, versus\n'
printf '    what EC2 actually reports. Those disagree while an attachment propagates.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

h1 "1. Which accounts were measured, and as whom"
{ printf 'PROFILE\tACCOUNT\tCALLER ARN\n'; cat "$CALLERS"; } | tabulate

h1 "2. The settings, per account"
{
  printf 'PROFILE\tATTRIBUTE\tEXPECTED\tACTUAL\tVERDICT\n'
  while IFS=$'\t' read -r p acct; do
    [ -n "${p:-}" ] || continue
    while IFS=$'\t' read -r aname sub query want; do
      [ -n "${aname:-}" ] || continue
      got=$(aws_ "$p" ec2 "$sub" --query "$query" --output text 2>&1)
      if [ $? -ne 0 ]; then
        printf '[%s] ec2 %s\n    %s\n' "$p" "$sub" "$(printf '%s' "$got" | head -2 | tr '\n' ' ')" >>"$ERRORS"
        printf '%s\t%s\t%s\t%s\t%s\n' "$p" "$aname" "$want" "(call failed)" "CALL FAILED"
        BAD=$((BAD+1))
        continue
      fi
      [ -n "$got" ] && [ "$got" != "None" ] || got="not-set"
      if [ "$got" = "$want" ]; then
        printf '%s\t%s\t%s\t%s\t%s\n' "$p" "$aname" "$want" "$got" "ok"
      else
        printf '%s\t%s\t%s\t%s\t%s\n' "$p" "$aname" "$want" "$got" "MISMATCH"
        BAD=$((BAD+1))
      fi
    done <<ATTRS
$ATTRS
ATTRS
  done <"$LIVE"
} | tee "$ROWS" | tabulate

printf '\n'
printf 'EXPECTED is awsds-org-declarative-ec2.json translated into the spelling the EC2 API\n'
printf 'answers in. The document says `block_all_sharing` and `disabled`; the API says\n'
printf '`block-all-sharing` and `False`. That mapping is written by hand in this script and\n'
printf 'has to be updated with the document - it is the one place the two can silently\n'
printf 'disagree.\n'

h1 "3. The effective declarative policy, as Organizations computes it"
while IFS=$'\t' read -r p acct; do
  [ -n "${p:-}" ] || continue
  printf -- '--- %s ---\n\n' "$p"
  out=$(aws_ "$p" organizations describe-effective-policy \
          --policy-type DECLARATIVE_POLICY_EC2 \
          --query 'EffectivePolicy.PolicyContent' --output text 2>&1)
  if [ $? -ne 0 ]; then
    if printf '%s' "$out" | grep -q 'EffectivePolicyNotFoundException\|PolicyTypeNotEnabledException'; then
      printf 'no effective EC2 declarative policy for this account.\n'
      printf 'Before the attach this is the expected answer; after it, it is a finding.\n\n'
    else
      printf '%s\n\n' "$out"
      printf '[%s] organizations describe-effective-policy\n    %s\n' \
        "$p" "$(printf '%s' "$out" | head -2 | tr '\n' ' ')" >>"$ERRORS"
    fi
  elif [ -z "$out" ] || [ "$out" = "{}" ] || [ "$out" = "None" ]; then
    # Measured 2026-08-14: with the policy type ENABLED but nothing attached, Organizations
    # answers `{}` rather than raising EffectivePolicyNotFoundException. An empty object and
    # a missing policy are the same fact and neither is an error - which is worth saying,
    # because a script that only handled the exception would print `{}` as if it were content.
    printf '{}  - no EC2 declarative policy reaches this account.\n'
    printf 'Before the attach this is the expected answer; after it, it is a finding.\n\n'
  else
    printf '%s\n\n' "$out"
  fi
done <"$LIVE"

printf 'Section 2 is EC2 reporting the setting; this section is Organizations reporting the\n'
printf 'intent. A disagreement between them means an attachment that has not taken effect,\n'
printf 'which is a state that exists and resolves on its own - re-run before acting on it.\n'

h1 "4. The accounts this laptop cannot reach"
printf 'MANAGEMENT, LOG ARCHIVE and AUDIT hold no project persona (guiding principle 1).\n'
printf 'Reach them as `AWS Control Tower Admin` through the access portal and run, in\n'
printf 'CloudShell inside each:\n\n'
printf '    ./aws/declarative-ec2.sh -\n\n'
printf 'MANAGEMENT IS THE ONE THAT MATTERS AND IT IS NOT A FORMALITY. SCPs and RCPs skip the\n'
printf 'management account by design; AWS documents NO SUCH EXEMPTION for declarative\n'
printf 'policies, and they are enforced in the service control plane rather than in\n'
printf 'authorization, which is where that exemption lives. So a root attach is EXPECTED to\n'
printf 'reach Management - the first time in this project that a root-attached document\n'
printf 'does - and the only way to find out is to read it there. Record the answer in\n'
printf 'docs/log/log-stage-01c-preventive-policies.md.\n\n'
printf 'Also absent, and none is a gap: `Staging` (not vended), every Sandbox beyond the\n'
printf 'first (no profile until Stage 14), and EXC-01, the suspended `Sandbox` that is not\n'
printf 'this project account.\n'

h1 "5. Calls that failed"
if [ -s "$ERRORS" ]; then
  cat "$ERRORS"
  printf '\nIf a profile did not authenticate:  aws sso login --sso-session %s\n' "$SSO_SESSION"
else
  printf 'None. Every call in this report returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/declarative-ec2.sh\n'

}

main >"$OUT"

# The counter is incremented inside a subshell in section 2, so it is recovered from the
# rows rather than trusted - the same class of bug org-policies.sh hit with POL_OK.
N_BAD=$(grep -c 'MISMATCH\|CALL FAILED' "$ROWS" 2>/dev/null || true)
N_ALL=$(wc -l <"$ROWS" | tr -d ' ')

note ""
note "wrote $OUT  ($((N_ALL - 1 - ${N_BAD:-0})) of $((N_ALL - 1)) readings match the document)"
if [ -s "$ERRORS" ] || [ "${N_BAD:-0}" -gt 0 ]; then
  note "MISMATCH or failed call present - see sections 2 and 5."
  exit 1
fi
exit 0
