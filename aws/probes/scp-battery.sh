#!/usr/bin/env bash
#
# scp-battery.sh - run the SCP probe battery of plan/runbooks/scp-battery.md.
#
#   run:      ./aws/probes/scp-battery.sh              # every phase
#             ./aws/probes/scp-battery.sh --phase ou   # one phase
#             ./aws/probes/scp-battery.sh --list       # what would run, and where
#   probes:   aws/probes/probes.sh - the data. Amending the battery means editing THAT file.
#   writes:   aws/output/scp-battery-<stamp>.txt (untracked), account ids masked.
#   exit:     0 when every probe met its expectation; 1 on a regression, an overreach or
#             a broken floor; 2 when the run could not be trusted (dead SSO session).
#
# WHAT THIS SCRIPT IS NOT ALLOWED TO DO, and the seam is deliberate: it never attaches,
# detaches, creates or updates a policy. The human attaches from the Management console;
# the script only measures what the attached ceiling does. A script that could both change
# the ceiling and report on it would be able to report on a ceiling it had just changed.
#
# WHETHER ANYTHING IS CREATED IS A DECLARED FIELD, NOT A JUDGEMENT. Every probe in probes.sh
# carries a mandatory `safety` value and the driver refuses to run one that does not:
#   ro       read-only; changes nothing even if fully allowed
#   dryrun   carries --dry-run, which the driver verifies is actually there
#   blocked  mutating, but a prerequisite named in the command does not exist, so removing
#            the deny only moves the failure one step later
#   creates  would really do something if the deny lifted. THREE probes, all in the root
#            phase, and the driver REFUSES to run them outside Policy Canary - that account
#            is the one place this project accepts the residual risk of an "allowed".
#
# THE THREE THINGS THIS ENCODES THAT A HAND-RUN BATTERY KEPT GETTING WRONG:
#   1. A dead SSO session makes every probe come back looking exactly like a deny. It
#      happened twice in one sitting. So the session is checked per account per phase, and
#      a non-answer ABORTS the run instead of being recorded (exit 2).
#   2. The outcome is read from the error WORDING, never from the exit code - and an
#      explicit-deny message names the policy id, which is the attribution.
#   3. "The service validates before authorizing" is a property of the ACTION, not of the
#      service (Lesson 21), so each probe declares the wording that proves authorization
#      was reached for that action. Anything else is UNTESTED - never silently "allowed".

set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
POLICY_DIR="$REPO/terraform-live/identity/org-policies/policies"
OUT_DIR="$REPO/aws/output"
REGION_DEFAULT=us-west-2

PHASE_FILTER=""
LIST_ONLY=0
DO_READBACK=1

while [ $# -gt 0 ]; do
  case "$1" in
    --phase)       PHASE_FILTER="${2:-}"; shift 2 ;;
    --list)        LIST_ONLY=1; shift ;;
    --no-readback) DO_READBACK=0; shift ;;
    -h|--help)     sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done

TMP=$(mktemp -d) || exit 70
RESULTS="$TMP/results"
: >"$RESULTS"
CHECKED="$TMP/checked"
: >"$CHECKED"
trap 'rm -rf "$TMP"' EXIT

N_OK=0; N_BAD=0; N_UNTESTED=0

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
note()  { printf '     %s\n' "$*"; }
mask()  { sed -E 's/[0-9]{12}/<acct>/g'; }

die() { printf '\n!! %s\n' "$*" >&2; exit "${2:-1}"; }

# ---------------------------------------------------------------- accounts

# One place mapping a probe's account token to a CLI profile. A token that is not here is a
# typo in probes.sh, and it stops the run rather than skipping a probe silently.
profile_for() {
  case "$1" in
    canary)   echo awsds-policy-canary ;;
    data)     echo awsds-infra-data ;;
    identity) echo awsds-infra-identity ;;
    dev)      echo awsds-infra-dev ;;
    sandbox1) echo awsds-infra-sandbox-1 ;;
    prod)     echo awsds-infra-prod ;;
    *)        return 1 ;;
  esac
}

# The session is checked once per account per phase - "immediately before each block of
# probes", which is what the runbook asks for and what the two mid-battery expiries taught.
ensure_session() {
  _acct="$1"; _phase="$2"
  grep -qx "$_phase/$_acct" "$CHECKED" && return 0
  _p=$(profile_for "$_acct") || die "unknown account token '$_acct' in probes.sh" 64
  if ! aws sts get-caller-identity --profile "$_p" >/dev/null 2>&1; then
    die "no usable session for profile $_p.
   Sign in as the infrastructure user and run the battery again:
       aws sso login --sso-session awsds
   Nothing was recorded for this phase - a dead session makes every probe read like a deny." 2
  fi
  echo "$_phase/$_acct" >>"$CHECKED"
}

# ------------------------------------------------- real ids (Lesson 21)

# Probes that must reach authorization need inputs that exist. Resolved once per
# account+region and cached, because the alternative - an invented id - is rejected before
# authorization and reports "untested" while reading like a pass.
resolve_ami() {
  _acct="$1"; _region="$2"; _cache="$TMP/ami.$_acct.$_region"
  [ -s "$_cache" ] && { cat "$_cache"; return 0; }
  _p=$(profile_for "$_acct")
  aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
      --profile "$_p" --region "$_region" --query Parameter.Value --output text 2>/dev/null >"$_cache"
  [ -s "$_cache" ] && grep -q '^ami-' "$_cache" || { echo "" >"$_cache"; }
  cat "$_cache"
}

resolve_subnet() {
  _acct="$1"; _region="$2"; _cache="$TMP/subnet.$_acct.$_region"
  [ -s "$_cache" ] && { cat "$_cache"; return 0; }
  _p=$(profile_for "$_acct")
  aws ec2 describe-subnets --profile "$_p" --region "$_region" \
      --query 'Subnets[0].SubnetId' --output text 2>/dev/null >"$_cache"
  grep -q '^subnet-' "$_cache" || { echo "" >"$_cache"; }
  cat "$_cache"
}

resolve_account_id() {
  _acct="$1"; _cache="$TMP/acctid.$_acct"
  [ -s "$_cache" ] && { cat "$_cache"; return 0; }
  _p=$(profile_for "$_acct")
  aws sts get-caller-identity --profile "$_p" --query Account --output text 2>/dev/null >"$_cache"
  cat "$_cache"
}

# ---------------------------------------------------------------- classify

# Reads the WORDING. The order matters: a dead session and an IAM-level deny both contain
# "AccessDenied", and only the SCP wording names a policy.
classify() { # stdin: command output; $1: regex proving authorization was reached; $2: exit code
  _allowed_re="$1"; _rc="$2"; _out=$(cat)

  if printf '%s' "$_out" | grep -Eq 'SSO session associated with this profile has expired|ExpiredToken|InvalidGrantException|Error loading SSO Token|Unable to locate credentials|security token included in the request is (expired|invalid)'; then
    echo "NOANSWER|"; return
  fi
  if printf '%s' "$_out" | grep -q 'explicit deny in a service control policy'; then
    _pid=$(printf '%s' "$_out" | grep -Eo 'p-[a-z0-9]{8,}' | head -1)
    echo "DENY-SCP|$_pid"; return
  fi
  if printf '%s' "$_out" | grep -q 'explicit deny in a resource control policy'; then
    _pid=$(printf '%s' "$_out" | grep -Eo 'p-[a-z0-9]{8,}' | head -1)
    echo "DENY-RCP|$_pid"; return
  fi
  if printf '%s' "$_out" | grep -q 'DryRunOperation'; then
    echo "ALLOWED|dry-run"; return
  fi
  if [ -n "$_allowed_re" ] && printf '%s' "$_out" | grep -Eq "$_allowed_re"; then
    echo "ALLOWED|reached-authorization"; return
  fi
  if [ "$_rc" -eq 0 ]; then
    echo "ALLOWED|succeeded"; return
  fi
  # An AccessDenied that names no policy is an IAM/permission-set deny, not the ceiling -
  # worth separating, because it answers a different question from the one being asked.
  if printf '%s' "$_out" | grep -Eq 'AccessDenied|UnauthorizedOperation|not authorized'; then
    echo "DENY-NOT-SCP|"; return
  fi
  echo "UNTESTED|"
}

# ---------------------------------------------------------------- the probe

# probe <phase> <account> <expect> <allowed-regex|-> <safety> <label> -- <command...>
#   expect : deny  - the ceiling must stop it
#            allow - it must still work (a cross-check, or the must-still-succeed floor)
#   safety : ro | dryrun | blocked | creates - MANDATORY, and it is where "does this create
#            anything?" is answered. `creates` runs in Policy Canary and nowhere else.
probe() {
  _phase="$1"; _acct="$2"; _expect="$3"; _allowed="$4"; _flags="$5"; _label="$6"
  shift 6
  [ "${1:-}" = "--" ] && shift
  [ "$_allowed" = "-" ] && _allowed=""

  if [ -n "$PHASE_FILTER" ] && [ "$PHASE_FILTER" != "$_phase" ]; then return 0; fi

  # The safety field is mandatory and is checked before the probe runs, so "does this create
  # anything?" is answered by the file rather than by whoever last read it.
  case "$_flags" in
    ro|dryrun|blocked) : ;;
    creates)
      if [ "$_acct" != "canary" ]; then
        die "probes.sh asks to run a 'creates' probe ('$_label') in '$_acct'.
   A probe that would really do something if the deny lifted may run in Policy Canary and
   nowhere else. Give it a --dry-run form, aim it at a prerequisite that does not exist
   ('blocked'), or move it to the canary." 64
      fi ;;
    *)
      die "probe '$_label' declares safety '$_flags', which is not one of
   ro | dryrun | blocked | creates. Every probe must say what it would do if the ceiling
   were removed - that classification is the file's answer to 'does this create anything',
   and a probe that does not carry it does not run." 64 ;;
  esac

  # A probe claiming `dryrun` had better carry the flag; the claim is what the reader trusts.
  case "$_flags" in
    dryrun) case " $* " in *" --dry-run "*) : ;; *)
      die "probe '$_label' is declared 'dryrun' but passes no --dry-run flag." 64 ;; esac ;;
  esac

  if [ "$LIST_ONLY" -eq 1 ]; then
    printf '  %-8s %-9s %-6s %s\n' "$_phase" "$_acct" "$_expect" "$_label"
    return 0
  fi

  ensure_session "$_acct" "$_phase"
  _p=$(profile_for "$_acct")

  # Substitute the placeholders that need a real, existing id.
  _cmd=""
  for _arg in "$@"; do
    case "$_arg" in
      *@AMI@*|*@SUBNET@*|*@ACCT@*)
        _region="$REGION_DEFAULT"
        case "$*" in *"--region "*) _region=$(printf '%s\n' "$@" | grep -A1 -x -- '--region' | tail -1) ;; esac
        _ami=$(resolve_ami "$_acct" "$_region")
        _sub=$(resolve_subnet "$_acct" "$_region")
        _aid=$(resolve_account_id "$_acct")
        # An id that could not be resolved must stop the probe, not be substituted as an
        # empty string: the call would then fail on a malformed argument and be classified
        # UNTESTED with no hint of why. Resolution itself can be *denied* - a region control
        # denies the ssm:GetParameter that finds the AMI - and that is worth saying out loud.
        case "$_arg" in
          *@AMI@*)    [ -n "$_ami" ] || { record "$_phase" "$_acct" "$_expect" "$_label" "UNTESTED" "no AMI resolvable in $_region"; return 0; } ;;
        esac
        case "$_arg" in
          *@SUBNET@*) [ -n "$_sub" ] || { record "$_phase" "$_acct" "$_expect" "$_label" "UNTESTED" "no subnet in $_region"; return 0; } ;;
        esac
        _arg=$(printf '%s' "$_arg" | sed -e "s|@AMI@|$_ami|g" -e "s|@SUBNET@|$_sub|g" -e "s|@ACCT@|$_aid|g") ;;
    esac
    _cmd="$_cmd $(printf '%q' "$_arg")"
  done

  _out=$(eval "aws $_cmd --profile $_p" 2>&1); _rc=$?
  _res=$(printf '%s' "$_out" | classify "$_allowed" "$_rc")
  _outcome=${_res%%|*}; _detail=${_res#*|}

  [ "$_outcome" = "NOANSWER" ] && die "probe '$_label' in $_acct returned a non-answer:
   $(printf '%s' "$_out" | mask | head -2)
   The run is stopped rather than recorded. Re-authenticate and start again." 2

  record "$_phase" "$_acct" "$_expect" "$_label" "$_outcome" "$_detail"
}

verdict() { # $1 expect, $2 outcome -> OK | BAD | NOTE
  case "$1/$2" in
    deny/DENY-SCP)      echo OK ;;
    deny/DENY-RCP)      echo OK ;;
    deny/ALLOWED)       echo BAD ;;
    deny/DENY-NOT-SCP)  echo NOTE ;;
    deny/UNTESTED)      echo NOTE ;;
    allow/ALLOWED)      echo OK ;;
    allow/DENY-SCP)     echo BAD ;;
    allow/DENY-RCP)     echo BAD ;;
    allow/DENY-NOT-SCP) echo BAD ;;
    allow/UNTESTED)     echo NOTE ;;
    *)                  echo NOTE ;;
  esac
}

record() {
  _v=$(verdict "$3" "$5")
  case "$_v" in
    OK)   N_OK=$((N_OK+1));       _mark="ok  " ;;
    BAD)  N_BAD=$((N_BAD+1));     _mark="FAIL" ;;
    *)    N_UNTESTED=$((N_UNTESTED+1)); _mark="note" ;;
  esac
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$_mark" "$1" "$2" "$3" "$5" "$6" "$4" >>"$RESULTS"
  printf '  %-4s %-8s %-9s %-6s %-13s %-22s %s\n' \
         "$_mark" "$1" "$2" "$3" "$5" "$6" "$4"
}

# ------------------------------------------------------- deployed vs repository

# Answers "is the thing being probed the thing in policies/?" before a single probe runs.
# Every amendment this project has made was uploaded by hand, and a battery run against the
# previous content looks exactly like a battery run against the current one.
readback() {
  bold "Read-back: what is attached, against terraform-live/.../policies/"
  ensure_session identity readback
  python3 "$HERE/readback.py" "$POLICY_DIR" "$(profile_for identity)"
  echo
}


# ---------------------------------------------------------------- run

mkdir -p "$OUT_DIR"
STAMP=$(date +%Y%m%dT%H%M%S)
REPORT="$OUT_DIR/scp-battery-$STAMP.txt"

if [ "$LIST_ONLY" -eq 1 ]; then
  bold "Probes defined in probes/probes.sh${PHASE_FILTER:+ (phase $PHASE_FILTER)}"
  printf '  %-8s %-9s %-6s %s\n' PHASE ACCOUNT EXPECT PROBE
  . "$HERE/probes.sh"
  exit 0
fi

bold "SCP battery - $(date '+%Y-%m-%d %H:%M:%S')${PHASE_FILTER:+  (phase $PHASE_FILTER)}"
echo "Runbook: plan/runbooks/scp-battery.md   Nothing here creates anything."
echo

[ "$DO_READBACK" -eq 1 ] && [ -z "$PHASE_FILTER" ] && readback

printf '  %-4s %-8s %-9s %-6s %-13s %-22s %s\n' MARK PHASE ACCOUNT EXPECT OUTCOME DETAIL PROBE
. "$HERE/probes.sh"

echo
bold "$N_OK as expected, $N_BAD unexpected, $N_UNTESTED not measured"
{
  echo "SCP battery - $(date '+%Y-%m-%d %H:%M:%S')"
  echo "mark	phase	account	expect	outcome	detail	probe"
  cat "$RESULTS"
  echo
  echo "$N_OK as expected, $N_BAD unexpected, $N_UNTESTED not measured"
} | mask >"$REPORT"
echo "Report: ${REPORT#$REPO/}"

if [ "$N_BAD" -gt 0 ]; then
  echo
  echo "A 'FAIL' row is one of two things, and they are not the same:"
  echo "  expect=deny,  outcome=ALLOWED   -> the ceiling has a hole. Read the row's probe."
  echo "  expect=allow, outcome=DENY-*    -> the ceiling reaches something it should not."
  exit 1
fi
exit 0
