#!/usr/bin/env bash
#
# tf-backends.sh - the Terraform state buckets and their keys, one row per account, side by
# side. The preflight for Stage 2 steps 2 and 3, and the standing regression after them.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/tf-backends.sh                        # every awsds-* profile
#             ./aws/tf-backends.sh awsds-infra-prod       # only the ones named
#             ./aws/tf-backends.sh -                      # CloudShell, ambient credentials
#   writes:   aws/output/tf-backends.txt   (untracked - see .gitignore)
#   reads:    s3api:ListBuckets, GetBucketVersioning, GetBucketEncryption,
#             GetPublicAccessBlock, GetBucketPolicy, GetBucketLifecycleConfiguration,
#             GetObjectLockConfiguration, kms:ListAliases, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is a
# PER-ACCOUNT fact whose meaning is the comparison BETWEEN accounts: a state bucket that is
# versioned, encrypted under a customer-managed key and closed to the public in five accounts
# and merely versioned in the sixth is the sixth account's hole, and a single-profile version
# would answer nothing. Same shape as account-bpa.sh and AZs.sh, and it pays the rule back
# the same way - section 1 prints the caller ARN of every profile.
#
# WHAT IT IS FOR, IN TWO PHASES.
#
#   BEFORE Stage 2 steps 2 and 3: "is anything already there". A bucket that already exists
#   under the name the bootstrap slice is about to claim turns the first apply into either a
#   BucketAlreadyOwnedByYou or - worse, if somebody else owns the name - a create that fails
#   after the KMS key was made. Reading first costs seconds.
#
#   AFTER them: "did every bootstrapped account get the same treatment". That is otherwise
#   one `terraform plan` per account, in six directories, with six profiles - which is the
#   kind of check that gets done once.
#
# THE THING IT MAKES VISIBLE THAT NOTHING ELSE DOES - Stage 2 step 3.4's two keys. "The PKI
# key" is two different objects: the key that encrypts the production/pki/ STATE FILE, and
# whatever key the CA itself uses. Only the first belongs to Stage 2, and it cannot be created
# by the pki/ slice, because a backend is configured at `init` - before the slice has ever
# applied. So production/bootstrap/ creates TWO keys and Production is the one account whose
# alias list should read two rather than one. Section 4 is where that is either true or not.
#
# BUCKET NAMES ARE DISCOVERED, NEVER ASSUMED. The convention is awsds-<env>-tfstate
# (docs/plan/conventions.md), but the <env> token for the Identity account is not settled in any
# plan file, and a script that hardcodes a guess reports a correctly-named bucket as missing.
# So it lists what is there and matches on `tfstate`, which also catches the failure a
# hardcoded name cannot see: a state bucket somebody named something else.

set -uo pipefail

PROFILE_PREFIX="awsds-"
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
OUT="$OUT_DIR/tf-backends.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/tf-backends.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"
CALLERS="$TMP/callers.tsv"   # PROFILE <tab> ACCOUNT <tab> ARN
BUCKETS="$TMP/buckets.tsv"   # PROFILE <tab> BUCKET <tab> VERS <tab> SSE <tab> KEY <tab> BPA <tab> TLS <tab> LIFECYCLE <tab> LOCK
ALIASES="$TMP/aliases.tsv"   # PROFILE <tab> ALIAS <tab> KEY_ID
CHECKS="$TMP/checks.tsv"     # RESULT <tab> ID <tab> WHAT <tab> DETAIL
: >"$ERRORS"; : >"$CALLERS"; : >"$BUCKETS"; : >"$ALIASES"; : >"$CHECKS"

# ------------------------------------------------------------------------------ helpers

note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

aws_() { # aws_ <profile> <aws args...>
  local p="$1"; shift
  if [ "$p" = "-" ] || [ "$p" = "none" ]; then
    command aws --region "$REGION" "$@" </dev/null
  else
    command aws --profile "$p" --region "$REGION" "$@" </dev/null
  fi
}

RUN_OUT=""; RUN_STATUS=0; RUN_ERR=""
run() { # run <profile> <aws args...>   - logs nothing; the caller decides what an error means
  local p="$1"; shift
  RUN_OUT=$(aws_ "$p" "$@" 2>"$TMP/stderr")
  RUN_STATUS=$?
  RUN_ERR=$(cat "$TMP/stderr")
  [ "$RUN_STATUS" -eq 0 ] || RUN_OUT=""
}
logerr() { printf '[%s] aws %s\n    %s\n' "$1" "$2" \
             "$(printf '%s' "$3" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"; }

tabulate() { column -t -s $'\t'; }
check() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >>"$CHECKS"; }

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
    printf '%s\n' "$p" >>"$LIVE"
    note "  $p  OK"
  else
    printf '%s\t-\t(failed)\n' "$p" >>"$CALLERS"
    logerr "$p" "sts get-caller-identity" "$out"
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

# ------------------------------------------------------------------- measure each account

# Resolve a KMS key ARN or id back to its alias, so the table says `alias/awsds-prod-tfstate`
# rather than a uuid. The alias is the thing a human recognises and the thing 3.4's split is
# expressed in; the id is what the API returns.
alias_of() { # alias_of <profile> <key arn or id>
  local p="$1" key="$2" kid
  [ -n "$key" ] || { printf '-'; return; }
  kid="${key##*/}"
  awk -F'\t' -v p="$p" -v k="$kid" '$1==p && $3==k {print $2; found=1; exit}
                                    END {if (!found) print "(no alias)"}' "$ALIASES"
}

while IFS= read -r p; do
  [ -n "$p" ] || continue
  note "measuring $p ..."

  # KMS aliases first, so the bucket rows can name a key rather than a uuid.
  run "$p" kms list-aliases --query 'Aliases[?starts_with(AliasName,`alias/awsds`)].[AliasName,TargetKeyId]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "kms list-aliases" "$RUN_ERR"
  elif [ -n "$RUN_OUT" ]; then
    printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r aname akey; do
      [ -n "${aname:-}" ] || continue
      printf '%s\t%s\t%s\n' "$p" "$aname" "$akey" >>"$ALIASES"
    done
  fi

  run "$p" s3api list-buckets --query 'Buckets[].Name' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "s3api list-buckets" "$RUN_ERR"
    continue
  fi
  ALLB=$(printf '%s' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | sort)
  printf '%s\n' "$ALLB" >"$TMP/allb-$p.txt"

  # Match on `tfstate` rather than on a composed name - see the header.
  printf '%s\n' "$ALLB" | grep -i 'tfstate' | while IFS= read -r b; do
    [ -n "$b" ] || continue

    run "$p" s3api get-bucket-versioning --bucket "$b" --query 'Status' --output text
    VERS="${RUN_OUT:-NOT SET}"
    [ "$VERS" = "None" ] && VERS="NOT SET"

    run "$p" s3api get-bucket-encryption --bucket "$b" \
        --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.[SSEAlgorithm,KMSMasterKeyID]' \
        --output text
    if [ "$RUN_STATUS" -ne 0 ]; then SSE="NOT SET"; KEY="-";
    else
      SSE=$(printf '%s' "$RUN_OUT" | cut -f1)
      KEY=$(printf '%s' "$RUN_OUT" | cut -f2)
      [ "$KEY" = "None" ] && KEY=""
      KEY=$(alias_of "$p" "$KEY")
    fi

    run "$p" s3api get-public-access-block --bucket "$b" \
        --query 'PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]' \
        --output text
    if [ "$RUN_STATUS" -ne 0 ]; then BPA="NOT SET"
    else
      NTRUE=$(printf '%s' "$RUN_OUT" | tr '\t' '\n' | grep -c '^True$')
      BPA="$NTRUE/4"
    fi

    # The TLS-only statement checkov requires in Stage 2 step 2.1. Matching on the CONDITION
    # rather than on a Sid: the statement's name is the author's, the condition is the control.
    run "$p" s3api get-bucket-policy --bucket "$b" --query 'Policy' --output text
    if [ "$RUN_STATUS" -ne 0 ]; then TLS="no policy"
    elif printf '%s' "$RUN_OUT" | grep -q 'aws:SecureTransport'; then TLS="yes"
    else TLS="NO"; fi

    run "$p" s3api get-bucket-lifecycle-configuration --bucket "$b" \
        --query 'Rules[].[ID,Status]' --output text
    if [ "$RUN_STATUS" -ne 0 ]; then LC="none"
    else
      NRULES=$(printf '%s\n' "$RUN_OUT" | sed '/^$/d' | wc -l | tr -d ' ')
      LC="${NRULES} rule(s)"
      run "$p" s3api get-bucket-lifecycle-configuration --bucket "$b" \
          --query 'Rules[?NoncurrentVersionExpiration!=`null`].ID' --output text
      [ -n "$RUN_OUT" ] && LC="$LC, noncurrent" || LC="$LC, NO noncurrent"
    fi

    run "$p" s3api get-object-lock-configuration --bucket "$b" \
        --query 'ObjectLockConfiguration.ObjectLockEnabled' --output text
    if [ "$RUN_STATUS" -ne 0 ]; then LOCK="off"; else LOCK="${RUN_OUT:-off}"; fi

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$p" "$b" "$VERS" "$SSE" "$KEY" "$BPA" "$TLS" "$LC" "$LOCK" >>"$BUCKETS"
  done
done <"$LIVE"

# ------------------------------------------------------------------------------- checks

while IFS= read -r p; do
  [ -n "$p" ] || continue
  N=$(awk -F'\t' -v p="$p" '$1==p' "$BUCKETS" | wc -l | tr -d ' ')
  if [ "$N" -eq 0 ]; then
    check note "BK-0" "$p has a state bucket" \
      "none found. Expected BEFORE Stage 2 steps 2 and 3 have run in this account; a REGRESSION after. Nothing below is checked for this account."
    continue
  fi
  check pass "BK-0" "$p has a state bucket" "$N found"

  while IFS=$'\t' read -r xp b vers sse key bpa tls lc lock; do
    [ "$xp" = "$p" ] || continue
    [ "$vers" = "Enabled" ] \
      && check pass "BK-1" "versioning on $b" "Enabled" \
      || check fail "BK-1" "versioning on $b" \
           "$vers - without versioning a corrupt apply overwrites the only copy of the state, and S3 native locking (use_lockfile, D3) has nothing to fall back on."
    case "$sse" in
      aws:kms) check pass "BK-2" "SSE-KMS on $b" "key $key" ;;
      AES256)  check fail "BK-2" "SSE-KMS on $b" \
                 "AES256 - SSE-S3, not a customer-managed key. The key policy is where 'who can read this state' is expressed, and D36 has no other mechanism (Lesson 18)." ;;
      *)       check fail "BK-2" "SSE-KMS on $b" "$sse" ;;
    esac
    [ "$key" = "(no alias)" ] && check note "BK-2" "SSE-KMS on $b" \
      "the key has no alias, so nothing in a report can name it. Aliases are free; add one."
    [ "$bpa" = "4/4" ] \
      && check pass "BK-3" "block public access on $b" "4/4" \
      || check fail "BK-3" "block public access on $b" \
           "$bpa - three of four is not a partial pass: RestrictPublicBuckets alone still allows a public ACL."
    [ "$tls" = "yes" ] \
      && check pass "BK-4" "TLS-only policy on $b" "aws:SecureTransport present" \
      || check fail "BK-4" "TLS-only policy on $b" \
           "$tls - Stage 2 step 2.1 writes it explicitly rather than letting checkov add it, because a policy the linter wrote is a policy nobody read."
    case "$lc" in
      *", noncurrent"*) check pass "BK-5" "noncurrent-version lifecycle on $b" "$lc" ;;
      *)                check fail "BK-5" "noncurrent-version lifecycle on $b" \
                          "$lc - every apply writes a version, and a rule added later does not reach what already accumulated (Stage 2 step 2.1)." ;;
    esac
    [ "$lock" = "off" ] || check note "BK-6" "no Object Lock on $b" \
      "Object Lock reads '$lock'. Nothing in this design puts it on a STATE bucket - INV-14 is the CloudTrail bucket in Log Archive - and a locked state bucket cannot be re-encrypted or cleaned up."
  done <"$BUCKETS"
done <"$LIVE"

# BK-7: the two-key split of Stage 2 step 3.4, which only Production should show.
while IFS=$'\t' read -r p acct arn; do
  case "$arn" in "(failed)") continue ;; esac
  case "$p" in *prod*) ;; *) continue ;; esac
  NPKI=$(awk -F'\t' -v p="$p" '$1==p && $2 ~ /pki/' "$ALIASES" | wc -l | tr -d ' ')
  if [ "$NPKI" -ge 1 ]; then
    check pass "BK-7" "the pki STATE key exists in $p" \
      "$(awk -F'\t' -v p="$p" '$1==p && $2 ~ /pki/ {printf "%s%s", sep, $2; sep=", "}' "$ALIASES")"
  else
    check note "BK-7" "the pki STATE key exists in $p" \
      "no alias matching 'pki'. Expected until Stage 2 step 3 runs. After it, this is the check that production/pki/ shares the Production bucket under its OWN key (D36) rather than under the account state key - one bucket, two keys, two answerable questions."
  fi
done <"$CALLERS"

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'Terraform state buckets and their keys, one row per account\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profiles  : %s\n' "$PROFILE_SOURCE"
printf 'region    : %s\n' "$REGION"
printf 'produced  : aws/tf-backends.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Which accounts were measured, and as whom\n'
printf '  2. The state buckets found, side by side\n'
printf '  3. The checks\n'
printf '  4. The KMS aliases, and Stage 2 step 3.4`s two keys\n'
printf '  5. The accounts nothing here is measuring\n'
printf '  6. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - "NO STATE BUCKET" IS THE EXPECTED ANSWER UNTIL STAGE 2 STEPS 2 AND 3 HAVE RUN.\n'
printf '    It is reported as a `note`, not as a failure, and it becomes a REGRESSION the\n'
printf '    moment that account has been bootstrapped.\n'
printf '  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 5 names the ones nothing\n'
printf '    reached; an account in neither section 2 nor section 5 is the hole this script\n'
printf '    exists to expose - the same rule account-bpa.sh carries.\n'
printf '  - BUCKET NAMES ARE DISCOVERED, matching on `tfstate`. A state bucket named\n'
printf '    something else still shows up here; one named nothing at all does not exist.\n'
printf '  - THE KEY COLUMN NAMES AN ALIAS. `(no alias)` means the bucket is encrypted under\n'
printf '    a key nothing can refer to by name, which makes every later report unreadable.\n'

# ======================================================================================
h1 "1. Which accounts were measured, and as whom"

printf 'A profile is an (account, permission set) pair; every awsds-* profile here resolves\n'
printf 'to the infrastructure user. A `(failed)` row is a profile that did not authenticate,\n'
printf 'never a compliant one.\n\n'

{
  printf 'PROFILE\tACCOUNT\tCALLER ARN\n'
  cat "$CALLERS"
} | tabulate

# ======================================================================================
h1 "2. The state buckets found, side by side"

if [ -s "$BUCKETS" ]; then
  {
    printf 'PROFILE\tBUCKET\tVERSIONING\tSSE\tKEY\tBPA\tTLS-ONLY\tLIFECYCLE\tOBJ LOCK\n'
    sort "$BUCKETS"
  } | tabulate
else
  printf 'NONE FOUND IN ANY MEASURED ACCOUNT.\n\n'
  printf 'This is the expected state before Stage 2 steps 2 and 3. What the report is worth\n'
  printf 'right now is section 5 and the `allb` note below: it proves the names the bootstrap\n'
  printf 'slice is about to claim are free.\n'
fi

printf '\n'
printf 'Every bucket in each measured account, so a state bucket under an unexpected name is\n'
printf 'visible rather than absent:\n\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  if [ -s "$TMP/allb-$p.txt" ] && grep -q . "$TMP/allb-$p.txt"; then
    sed 's/^/  /' "$TMP/allb-$p.txt"
  else
    printf '  (no buckets at all in this account)\n'
  fi
done <"$LIVE"

# ======================================================================================
h1 "3. The checks"

{
  printf 'RESULT\tID\tWHAT\tDETAIL\n'
  awk -F'\t' '$1=="fail"' "$CHECKS"
  awk -F'\t' '$1=="note"' "$CHECKS"
  awk -F'\t' '$1=="pass"' "$CHECKS"
} | tabulate

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
printf '\n%s check(s) FAILED.\n' "$NFAIL"

# ======================================================================================
h1 "4. The KMS aliases, and Stage 2 step 3.4's two keys"

printf 'PRODUCTION IS THE ONE ACCOUNT THAT SHOULD SHOW TWO. Stage 2 step 3.4 splits the key\n'
printf 'that encrypts production/pki/`s STATE from the account`s general state key, because\n'
printf 'D36 puts the CA root private key in that state file: one key for both would make "who\n'
printf 'can read Production state" and "who can mint a certificate for any internal name" the\n'
printf 'same permission. Every other account shows one.\n\n'

if [ -s "$ALIASES" ]; then
  {
    printf 'PROFILE\tALIAS\tTARGET KEY\n'
    sort "$ALIASES"
  } | tabulate
else
  printf '(no awsds-* aliases in any measured account - expected before Stage 2 step 2)\n'
fi

# ======================================================================================
h1 "5. The accounts nothing here is measuring"

printf 'Read this BEFORE reading section 3 as a pass.\n\n'
printf '  - Management, Log Archive and Audit hold NO CLI profile, by design, and none of\n'
printf '    them is a Terraform-managed account: Management is bootstrap-only (principle 1),\n'
printf '    and the other two are Control Tower`s. They have no state bucket and must not.\n'
printf '  - `Policy Canary` deliberately gets NO state bucket either (D29, docs/plan/architecture\n'
printf '    §3): an account whose point is to stay empty. Its profile authenticates, so it\n'
printf '    appears in section 1 with no bucket - and that is the correct reading, not a gap.\n'
printf '  - `Staging` has no profile because the account is UNVENDED, held on the account cap\n'
printf '    (Stage 1a). Stage 2 step 3.2 skips its bootstrap slice for exactly this reason.\n'
printf '  - Every Sandbox beyond the first has no profile until Stage 14 vends it (D35).\n'
printf '\n'
printf 'So the expected shape once Stage 2 steps 2 and 3 are done is FIVE state buckets -\n'
printf 'sandbox-1, dev, data, prod, identity - and a sixth when Staging is vended.\n'

# ======================================================================================
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  cat "$ERRORS"
  printf '\nA NoSuchBucket-shaped error is not listed here: a bucket that does not exist is\n'
  printf 'read as "not created yet" by the checks, which is section 3`s BK-0 note.\n'
else
  printf 'None. Every call returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/tf-backends.sh\n'

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
note "wrote $OUT (all checks passed)"
exit 0
