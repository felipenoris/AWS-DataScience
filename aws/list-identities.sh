#!/usr/bin/env bash
#
# list-identities.sh - snapshot of the Organization tree and of the IAM Identity Center
# directory, as seen from the Identity account.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             The login authenticates against the access portal, not against an account:
#             the cached token is keyed by the sso-session name, so one login covers every
#             profile in ~/.aws/config that declares `sso_session = awsds`, and the profile
#             below only matters one step later, when a call trades that token for the
#             temporary credentials of its account's role. `aws sso login --profile
#             awsds-infra-identity` reaches the same session and is equivalent.
#             This is checked before any listing runs: a missing or expired token stops the
#             script with that command, leaving the previous snapshot untouched.
#
#   run:      ./aws/list-identities.sh
#   writes:   aws/output/list-identities.txt   (untracked - see .gitignore)
#   reads:    everything; this script never creates, updates or deletes anything.
#
# Identity: the `awsds-infra-identity` SSO profile, i.e. the Identity account acting as the
# IAM Identity Center delegated administrator (D10). Reads are not restricted from there -
# only *writes* against Management-targeted objects are - which is why the Organizations
# calls below answer even though only Management could change what they return
# (log/log-stage-01b-identity-and-controls.md, step 4).
#
# Two call styles, on purpose:
#   show  - prints the command and the CLI's own `--output table` under it. What a reader
#           sees is exactly what the CLI returned.
#   run   - captures `--output text` into RUN_OUT/RUN_STATUS, for values that later
#           commands need as arguments, or for rows this script joins into a table.
# Both record a failing call in the error log printed by section 6, so that an empty block
# is never ambiguous between "nothing there" and "the call was denied".

set -uo pipefail

PROFILE="awsds-infra-identity"
REGION="us-west-2"
SSO_SESSION="awsds"

cd "$(dirname "$0")/.."
OUT_DIR="aws/output"
OUT="$OUT_DIR/list-identities.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/list-identities.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ACCOUNT_MAP="$TMP/accounts.tsv"       # AccountId <tab> Name
USER_MAP="$TMP/users.tsv"             # UserId    <tab> UserName <tab> DisplayName
GROUP_MAP="$TMP/groups.tsv"           # GroupId   <tab> DisplayName
PS_MAP="$TMP/permission-sets.tsv"     # PsArn     <tab> Name
ERRORS="$TMP/errors.txt"              # one line per failed call
: >"$ACCOUNT_MAP"; : >"$USER_MAP"; : >"$GROUP_MAP"; : >"$PS_MAP"; : >"$ERRORS"

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
aws_() { command aws --profile "$PROFILE" --region "$REGION" "$@" </dev/null; }

# capture a call: sets RUN_OUT and RUN_STATUS, logs a failure, prints nothing.
# TOLERATE holds a regex of error names that mean "there is none of this", not "this
# failed" - get-permissions-boundary-for-permission-set raises rather than returning empty.
RUN_OUT=""; RUN_STATUS=0; TOLERATE=""
run() {
  RUN_OUT=$(aws_ "$@" 2>&1)
  RUN_STATUS=$?
  if [ "$RUN_STATUS" -ne 0 ]; then
    if [ -n "$TOLERATE" ] && printf '%s' "$RUN_OUT" | grep -qE "$TOLERATE"; then
      RUN_OUT=""; RUN_STATUS=0
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

# lookups against the maps above; all print "(unknown)" rather than nothing, so that a
# missing name is visible in the report instead of collapsing a column
lookup() { # lookup <file> <key> <field-number>
  awk -F'\t' -v k="$2" -v f="$3" '$1==k {print $f; hit=1} END {if (!hit) print "(unknown)"}' "$1"
}
account_name() { lookup "$ACCOUNT_MAP" "$1" 2; }
user_name()    { lookup "$USER_MAP"    "$1" 2; }
user_display() { lookup "$USER_MAP"    "$1" 3; }
group_name()   { lookup "$GROUP_MAP"   "$1" 2; }
ps_name()      { lookup "$PS_MAP"      "$1" 2; }

# align a tab-separated stream into a table; empty cells must be written as "-"
tabulate() { column -t -s $'\t'; }

# one labelled detail block, indented under a permission set. Distinguishes a failed call
# from a genuinely empty one, which is the whole point of not writing this as `|| echo`.
detail() { # detail <tolerated-error-regex|-> <label> <aws args...>
  local tol="$1" label="$2"; shift 2
  printf '  %s\n' "$label"
  [ "$tol" = "-" ] || TOLERATE="$tol"
  run "$@"
  TOLERATE=""
  if [ "$RUN_STATUS" -ne 0 ]; then
    printf '    !! call failed - see section 6\n'
  elif [ -z "$RUN_OUT" ] || [ "$RUN_OUT" = "None" ] || [ "$RUN_OUT" = "null" ]; then
    printf '    (none)\n'
  else
    case "$RUN_OUT" in
      *$'\t'*) printf '%s\n' "$RUN_OUT" | tabulate | sed 's/^/    /' ;;
      *)       printf '%s\n' "$RUN_OUT" | sed 's/^/    /' ;;
    esac
  fi
  printf '\n'
}

# ---------------------------------------------------------------------------- preflight

note "profile: $PROFILE (region $REGION)"
if ! CALLER=$(command aws --profile "$PROFILE" --region "$REGION" \
                sts get-caller-identity --query 'Arn' --output text 2>&1); then
  note ""
  note "cannot authenticate with profile '$PROFILE':"
  printf '%s\n' "$CALLER" | sed '/^[[:space:]]*$/d; s/^/  /' >&2
  note ""
  note "log in first:"
  note "  aws sso login --sso-session $SSO_SESSION"
  exit 1
fi
note "caller:  $CALLER"

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'list-identities - Organization and IAM Identity Center state\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE"
printf 'region    : %s\n' "$REGION"
printf 'caller    : %s\n' "$CALLER"
printf 'produced  : aws/list-identities.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Caller - the identity that produced this file\n'
printf '  2. Organization        2.1 ORG_ID and MGMT_ID  2.2 ROOT_ID and policy types\n'
printf '                         2.3 the OU tree  2.4 every account\n'
printf '  3. Identity Center     3.1 instances  3.2 CHECK: exactly one  3.3 groups\n'
printf '                         3.4 users  3.5 group memberships\n'
printf '  4. Permission sets     4.1 ARNs  4.2 described  4.3 what each one grants\n'
printf '  5. Assignments         5.1 every triple  5.2 grouped by account\n'
printf '  6. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - Every "$ aws ..." line is the exact command that produced the block under it,\n'
printf '    minus `--profile %s --region %s`, which every command carries.\n' "$PROFILE" "$REGION"
printf '  - NAME=value lines are shell variables reused by the commands that follow.\n'
printf '  - A table without a "$ aws" line above it was joined by the script from several\n'
printf '    calls; the calls are named in the paragraph next to it.\n'
printf '  - An empty block says which kind of empty it is. Section 6 lists every call that\n'
printf '    failed, so "(none)" always means none.\n'
printf '  - This is a point-in-time snapshot, not a source of truth: regenerate it rather\n'
printf '    than trusting a stale copy, and record intent in plan/ or log/, never here.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS\n'
printf 'AND EMAIL ADDRESSES. Do not copy either into a tracked file.\n'

# --------------------------------------------------------------------------------------
h1 "1. Caller - the identity that produced this file"

show sts get-caller-identity --output table

# --------------------------------------------------------------------------------------
h1 "2. Organization"

h2 "2.1 ORG_ID and MGMT_ID - the organization, and the account that manages it"

# ORG_ID is not a curiosity: it is the value both data-perimeter condition keys take, so it
# is printed as a named variable rather than left as an unlabelled row of the table below.
run organizations describe-organization \
    --query 'Organization.Id' \
    --output text
ORG_ID="$RUN_OUT"

printf '$ ORG_ID=$(aws organizations describe-organization \\\n'
printf '      --query Organization.Id \\\n'
printf '      --output text)\n'
printf '$ echo $ORG_ID\n'
printf '%s\n\n' "${ORG_ID:-(call failed - see section 6)}"

printf 'This id is what the two data-perimeter condition keys of plan/architecture.md are\n'
printf 'compared against: aws:PrincipalOrgID (is the CALLER inside my organization?) and\n'
printf 'aws:ResourceOrgID (is the RESOURCE being written to?). It is also the value\n'
printf 'terraform-live/identity/org-policies/render.sh substitutes for the <ORG_ID>\n'
printf 'placeholder of the Stage 1c policy documents - read it here, never paste it by hand.\n\n'

run organizations describe-organization \
    --query 'Organization.MasterAccountId' \
    --output text
MGMT_ID="$RUN_OUT"

printf '$ MGMT_ID=$(aws organizations describe-organization \\\n'
printf '      --query Organization.MasterAccountId \\\n'
printf '      --output text)\n'
printf '$ echo $MGMT_ID\n'
printf '%s\n\n' "${MGMT_ID:-(call failed - see section 6)}"

show organizations describe-organization \
    --query 'Organization.[Id,Arn,FeatureSet,MasterAccountId]' \
    --output table

h2 "2.2 ROOT_ID - the organization root, and the policy types enabled on it"

run organizations list-roots --query 'Roots[0].Id' --output text
ROOT_ID="$RUN_OUT"
printf 'ROOT_ID=%s\n\n' "${ROOT_ID:-(call failed - see section 6)}"

show organizations list-roots \
    --query 'Roots[].[Name,Id,Arn]' \
    --output table

# Which policy types are ENABLED here decides what can be attached to an OU at all: an
# SCP, an RCP, a tag policy or a declarative policy that is not ENABLED on the root
# cannot be attached anywhere, whatever the OU tree looks like.
show organizations list-roots \
    --query 'Roots[0].PolicyTypes[].[Type,Status]' \
    --output table

h2 "2.3 The OU tree, walked from the root"

# The tree is deeper than one level (Sandboxes is nested under Interactive), so this
# recurses. Two things come out of the walk: the indented tree printed first, and one
# pair of tables per parent - its child OUs, and the accounts sitting directly in it.
TREE=""

walk_ou() { # walk_ou <parent-id> <parent-label> <depth>
  local parent="$1" label="$2" depth="$3"
  local pad="" i=0
  while [ "$i" -lt "$depth" ]; do pad="$pad  "; i=$((i + 1)); done

  h2 "children of $label ($parent)"

  show organizations list-organizational-units-for-parent \
      --parent-id "$parent" \
      --query 'OrganizationalUnits[].[Name,Id,Arn]' \
      --output table

  show organizations list-accounts-for-parent \
      --parent-id "$parent" \
      --query 'Accounts[].[Name,Id,Status]' \
      --output table

  local accounts ous id name status ou_id ou_name
  run organizations list-accounts-for-parent \
      --parent-id "$parent" \
      --query 'Accounts[].[Id,Name,Status]' \
      --output text
  accounts="$RUN_OUT"

  while IFS=$'\t' read -r id name status; do
    [ -n "${id:-}" ] || continue
    TREE="${TREE}${pad}  AC ${name} (${id}) ${status}"$'\n'
  done <<ACCOUNTS
$accounts
ACCOUNTS

  run organizations list-organizational-units-for-parent \
      --parent-id "$parent" \
      --query 'OrganizationalUnits[].[Id,Name]' \
      --output text
  ous="$RUN_OUT"

  while IFS=$'\t' read -r ou_id ou_name; do
    [ -n "${ou_id:-}" ] || continue
    TREE="${TREE}${pad}  OU ${ou_name} (${ou_id})"$'\n'
    walk_ou "$ou_id" "$ou_name" $((depth + 1))
  done <<OUS
$ous
OUS
}

note "walking the OU tree..."
walk_ou "${ROOT_ID:-r-unknown}" "Root" 0 >"$TMP/ou-detail.txt"

printf 'Tree, joined by this script from the calls shown below.\n'
printf 'OU = organizational unit, AC = account; indentation is depth under the root.\n\n'
printf 'Root (%s)\n' "${ROOT_ID:-?}"
printf '%s' "$TREE"
cat "$TMP/ou-detail.txt"

h2 "2.4 Every account in the organization"

show organizations list-accounts \
    --query 'sort_by(Accounts, &Name)[].[Id,Name,Status]' \
    --output table

run organizations list-accounts --query 'Accounts[].[Id,Name]' --output text
printf '%s\n' "$RUN_OUT" >"$ACCOUNT_MAP"

# --------------------------------------------------------------------------------------
h1 "3. IAM Identity Center - the directory"

h2 "3.1 Identity Store instances"

show sso-admin list-instances \
    --query 'Instances[].[IdentityStoreId,InstanceArn,OwnerAccountId,Status]' \
    --output table

h2 "3.2 CHECK - there must be exactly one Identity Store"

run sso-admin list-instances --query 'length(Instances)' --output text
N_INSTANCES="$RUN_OUT"

printf '$ N_INSTANCES=$(aws sso-admin list-instances \\\n'
printf '      --query "length(Instances)" \\\n'
printf '      --output text)\n'
printf '$ echo $N_INSTANCES\n'
printf '%s\n\n' "${N_INSTANCES:-(call failed - see section 6)}"

if [ "${N_INSTANCES:-}" != "1" ]; then
  printf 'CHECK FAILED: expected exactly 1 Identity Store instance, found "%s".\n\n' "${N_INSTANCES:-}"
  printf 'Everything below addresses "the" Identity Store by its id, so the rest of this\n'
  printf 'report is not produced. Either a second instance exists - which contradicts the\n'
  printf 'single-directory assumption the plan is built on - or the call was denied.\n'
  h1 "6. Calls that failed"
  cat "$ERRORS"
  note "CHECK FAILED: found '${N_INSTANCES:-}' Identity Store instances, expected 1"
  return 1
fi
printf 'CHECK OK: exactly one instance. Its ids are used by every command below.\n\n'

run sso-admin list-instances --query 'Instances[0].IdentityStoreId' --output text
IDS="$RUN_OUT"
run sso-admin list-instances --query 'Instances[0].InstanceArn' --output text
INST="$RUN_OUT"
printf 'IDS=%s\n'  "$IDS"
printf 'INST=%s\n' "$INST"

h2 "3.3 Groups"

show identitystore list-groups \
    --identity-store-id "$IDS" \
    --query 'sort_by(Groups, &DisplayName)[].[DisplayName,GroupId,Description]' \
    --output table

run identitystore list-groups \
    --identity-store-id "$IDS" \
    --query 'sort_by(Groups, &DisplayName)[].[GroupId,DisplayName]' \
    --output text
printf '%s\n' "$RUN_OUT" >"$GROUP_MAP"

h2 "3.4 Users"

show identitystore list-users \
    --identity-store-id "$IDS" \
    --query 'sort_by(Users, &UserName)[].[UserName,DisplayName,UserId]' \
    --output table

show identitystore list-users \
    --identity-store-id "$IDS" \
    --query 'sort_by(Users, &UserName)[].[UserName,Name.GivenName,Name.FamilyName,Emails[0].Value,Emails[0].Type]' \
    --output table

run identitystore list-users \
    --identity-store-id "$IDS" \
    --query 'Users[].[UserId,UserName,DisplayName]' \
    --output text
printf '%s\n' "$RUN_OUT" >"$USER_MAP"

h2 "3.5 Group memberships"

# One table per group. UserName and DisplayName are resolved from 3.4's listing rather
# than by a describe-user per member, so a name here and a name there cannot disagree.
note "listing group memberships..."
while IFS=$'\t' read -r gid gname; do
  [ -n "${gid:-}" ] || continue
  printf '%s (%s)\n\n' "$gname" "$gid"
  printf '$ aws identitystore list-group-memberships \\\n'
  printf '      --identity-store-id $IDS \\\n'
  printf '      --group-id %s \\\n' "$gid"
  printf '      --query "GroupMemberships[].[MemberId.UserId,MembershipId]" \\\n'
  printf '      --output text\n\n'

  run identitystore list-group-memberships \
      --identity-store-id "$IDS" \
      --group-id "$gid" \
      --query 'GroupMemberships[].[MemberId.UserId,MembershipId]' \
      --output text
  members="$RUN_OUT"

  if [ "$RUN_STATUS" -ne 0 ]; then
    printf '  !! call failed - see section 6\n\n'
    continue
  fi
  if [ -z "$members" ]; then
    printf '  (no members)\n\n'
    continue
  fi

  {
    printf 'USERNAME\tDISPLAY NAME\tUSER ID\tMEMBERSHIP ID\n'
    while IFS=$'\t' read -r member_id membership_id; do
      [ -n "${member_id:-}" ] || continue
      printf '%s\t%s\t%s\t%s\n' \
        "$(user_name "$member_id")" "$(user_display "$member_id")" \
        "$member_id" "$membership_id"
    done <<MEMBERS
$members
MEMBERS
  } | tabulate | sed 's/^/  /'
  printf '\n'
done <"$GROUP_MAP"

# --------------------------------------------------------------------------------------
h1 "4. IAM Identity Center - permission sets"

h2 "4.1 The permission set ARNs"

show sso-admin list-permission-sets \
    --instance-arn "$INST" \
    --output table

run sso-admin list-permission-sets --instance-arn "$INST" \
    --query 'PermissionSets[]' --output text
PS_ARNS=$(printf '%s' "$RUN_OUT" | tr '\t' '\n' | grep -v '^$')

h2 "4.2 Permission sets, described"

# Joined by the script: one `describe-permission-set` per ARN listed in 4.1.
note "describing permission sets..."
{
  printf 'NAME\tSESSION\tPS ID\tDESCRIPTION\n'
  for ps in $PS_ARNS; do
    run sso-admin describe-permission-set \
        --instance-arn "$INST" \
        --permission-set-arn "$ps" \
        --query 'PermissionSet.[Name,SessionDuration,Description]' \
        --output text
    ps_nm=$(printf '%s' "$RUN_OUT" | cut -f1)
    ps_dur=$(printf '%s' "$RUN_OUT" | cut -f2)
    ps_desc=$(printf '%s' "$RUN_OUT" | cut -f3)
    [ "$ps_desc" = "None" ] && ps_desc="-"
    printf '%s\t%s\t%s\t%s\n' \
      "${ps_nm:--}" "${ps_dur:--}" "${ps##*/}" "${ps_desc:--}"
    printf '%s\t%s\n' "$ps" "${ps_nm:--}" >>"$PS_MAP"
  done
} | tabulate
printf '\nPS ID is the tail of the ARN listed in 4.1. SESSION is the maximum session\n'
printf 'duration, ISO-8601.\n'

h2 "4.3 What each permission set grants"

for ps in $PS_ARNS; do
  printf '\n%s  [%s]\n' "$(ps_name "$ps")" "${ps##*/}"
  printf '  arn: %s\n\n' "$ps"

  detail - "AWS managed policies (list-managed-policies-in-permission-set)" \
      sso-admin list-managed-policies-in-permission-set \
      --instance-arn "$INST" --permission-set-arn "$ps" \
      --query 'AttachedManagedPolicies[].[Name,Arn]' --output text

  detail - "Customer managed policy references (list-customer-managed-policy-references-in-permission-set)" \
      sso-admin list-customer-managed-policy-references-in-permission-set \
      --instance-arn "$INST" --permission-set-arn "$ps" \
      --query 'CustomerManagedPolicyReferences[].[Name,Path]' --output text

  detail ResourceNotFoundException "Permissions boundary (get-permissions-boundary-for-permission-set)" \
      sso-admin get-permissions-boundary-for-permission-set \
      --instance-arn "$INST" --permission-set-arn "$ps" \
      --query 'PermissionsBoundary' --output json

  detail - "Inline policy (get-inline-policy-for-permission-set)" \
      sso-admin get-inline-policy-for-permission-set \
      --instance-arn "$INST" --permission-set-arn "$ps" \
      --query 'InlinePolicy' --output text

  detail - "Tags (list-tags-for-resource)" \
      sso-admin list-tags-for-resource \
      --instance-arn "$INST" --resource-arn "$ps" \
      --query 'Tags[].[Key,Value]' --output text
done

# --------------------------------------------------------------------------------------
h1 "5. IAM Identity Center - assignments"

# An assignment is the triple (principal, permission set, account). No API lists them
# all, so this walks the two enumerable sides: for each permission set, the accounts it
# is provisioned to (list-accounts-for-provisioned-permission-set), then the assignments
# on that pair (list-account-assignments). Names come from 2.4, 3.3, 3.4 and 4.2.
h2 "5.1 Every assignment triple"

note "listing assignments (one call per permission set, then one per account it reaches)..."
{
  printf 'ACCOUNT\tACCOUNT ID\tPERMISSION SET\tPRINCIPAL TYPE\tPRINCIPAL\tPRINCIPAL ID\n'
  for ps in $PS_ARNS; do
    run sso-admin list-accounts-for-provisioned-permission-set \
        --instance-arn "$INST" \
        --permission-set-arn "$ps" \
        --query 'AccountIds[]' \
        --output text
    accounts=$(printf '%s' "$RUN_OUT" | tr '\t' '\n' | grep -v '^$')

    for acct in $accounts; do
      run sso-admin list-account-assignments \
          --instance-arn "$INST" \
          --account-id "$acct" \
          --permission-set-arn "$ps" \
          --query 'AccountAssignments[].[PrincipalType,PrincipalId]' \
          --output text
      assignments="$RUN_OUT"

      if [ "$RUN_STATUS" -ne 0 ]; then
        printf '%s\t%s\t%s\t-\t!! call failed, see section 6\t-\n' \
          "$(account_name "$acct")" "$acct" "$(ps_name "$ps")"
        continue
      fi
      if [ -z "$assignments" ]; then
        printf '%s\t%s\t%s\t-\t(provisioned, no assignment)\t-\n' \
          "$(account_name "$acct")" "$acct" "$(ps_name "$ps")"
        continue
      fi

      while IFS=$'\t' read -r ptype pid; do
        [ -n "${ptype:-}" ] || continue
        case "$ptype" in
          GROUP) pname=$(group_name "$pid") ;;
          USER)  pname=$(user_name "$pid") ;;
          *)     pname="(unknown principal type)" ;;
        esac
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
          "$(account_name "$acct")" "$acct" "$(ps_name "$ps")" "$ptype" "$pname" "$pid"
      done <<ASSIGNMENTS
$assignments
ASSIGNMENTS
    done
  done
} >"$TMP/assignments.tsv"

{
  head -n 1 "$TMP/assignments.tsv"
  tail -n +2 "$TMP/assignments.tsv" | sort -t $'\t' -k1,1 -k3,3 -k5,5
} | tabulate

printf '\nA "(provisioned, no assignment)" row is a permission set still provisioned into an\n'
printf 'account that no principal is assigned to any more.\n'

h2 "5.2 The same triples, grouped by account"

{
  printf 'ACCOUNT\tPERMISSION SET\tPRINCIPAL\n'
  tail -n +2 "$TMP/assignments.tsv" \
    | sort -t $'\t' -k1,1 -k3,3 -k5,5 \
    | awk -F'\t' '{printf "%s\t%s\t%s (%s)\n", $1, $3, $5, $4}'
} | tabulate

# --------------------------------------------------------------------------------------
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
else
  printf 'None. Every call in this report returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/list-identities.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"
status=$?

note ""
if [ "$status" -eq 0 ]; then
  if [ -s "$ERRORS" ]; then
    note "wrote $OUT (some calls failed - see section 6)"
  else
    note "wrote $OUT"
  fi
else
  note "wrote $OUT (INCOMPLETE - the section 3.2 check failed)"
fi
exit "$status"
