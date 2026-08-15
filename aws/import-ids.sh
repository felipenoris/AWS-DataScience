#!/usr/bin/env bash
#
# import-ids.sh - the exact strings `terraform import` takes, for every object Stage 2
# step 5 brings into state. The import manifest.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/import-ids.sh                    # awsds-infra-identity
#             ./aws/import-ids.sh -                  # CloudShell, ambient credentials
#   writes:   aws/output/import-ids.txt   (untracked - see .gitignore)
#   reads:    organizations:DescribeOrganization, ListRoots, ListOrganizationalUnitsForParent,
#             ListAccountsForParent, ListPolicies, ListTargetsForPolicy,
#             sso-admin:ListInstances, ListPermissionSets, DescribePermissionSet,
#             ListManagedPoliciesInPermissionSet, GetInlinePolicyForPermissionSet,
#             ListAccountsForProvisionedPermissionSet, ListAccountAssignments,
#             identitystore:DescribeGroup, DescribeUser, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 the manifest was produced | 1 a call failed
#
# WHY THIS IS A SCRIPT OF ITS OWN, AND NOT A SECTION IN list-identities.sh. That file answers
# "who can reach what" and is read by a person, who tolerates a stale line and notices a wrong
# one. THIS file is a RENDERING whose only consumer is a shell. Its failure mode is different
# in kind: a wrong id does not read oddly, it imports the wrong object - or, more often,
# imports nothing under an address the configuration does not use, leaving `terraform plan`
# proposing to CREATE a policy that already exists while an orphan sits in state. That is the
# dangerous outcome Stage 2's Risks name, and it is worth a file that does one job.
#
# THE DIVISION OF LABOUR, WHICH IS THE DISCIPLINE OF SECTION 5. This script is authoritative
# about the RIGHT-HAND SIDE - the id. It is NOT authoritative about the left-hand side, the
# Terraform address: that belongs to the configuration, and only the configuration knows
# whether a resource is `aws_organizations_policy.baseline` or
# `aws_organizations_policy.this["awsds-org-scp-baseline"]`. So every line carries a SUGGESTED
# address that must be checked against the code, and the section says so rather than implying
# a copy-paste is safe.
#
# THE ONE THAT GOES WRONG, stated where it will be read: AN IMPORT INTO A `for_each` RESOURCE.
# The address is `...this["<key>"]` and the key has to be exactly what the configuration
# COMPUTES, not what reads naturally. A wrong key does not error. Import ONE, run `plan`, and
# only then import the rest.
#
# WHAT IT DELIBERATELY REFUSES TO EMIT, in section 4 - because the expensive mistake here is
# importing something that must stay outside Terraform, and an operator working from a
# complete-looking list will import all of it:
#   - Control Tower's `aws-guardrails-*` policies. Managing them from Terraform puts Terraform
#     and Control Tower in a fight over the same object: landing-zone drift (Stage 2 step 5.4).
#   - Control Tower's permission sets, `AWSAdministratorAccess` first among them. A permission
#     set provisioned into Management cannot even be altered from Identity - measured
#     2026-08-12, Stage 1b step 5.1 - and the deny is anchored on the SET, so it covers that
#     set's assignments in every account.
#   - The Account Factory DIRECT assignments (D32). They are a permanent property of a vended
#     account, not something to model.
# These are LISTED, with the reason, rather than filtered silently: a manifest that quietly
# omits things is one nobody can tell apart from a manifest that missed them.
#
# IDENTITY. `awsds-infra-identity`, which is both the Identity Center delegated administrator
# (D10) and an account whose Organizations reads already answer (Stage 1c verification (x)).
# One profile reaches both planes, which is why this is one script.

set -uo pipefail

PROFILE="${1:-${AWSDS_PROFILE:-awsds-infra-identity}}"
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
OUT="$OUT_DIR/import-ids.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/import-ids.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"
POLICIES="$TMP/policies.tsv"    # TYPE <tab> PID <tab> PNAME <tab> OURS(yes|no)
ATTACH="$TMP/attach.tsv"        # PID <tab> PNAME <tab> TARGET_ID <tab> TARGET_NAME <tab> TARGET_TYPE
PSETS="$TMP/psets.tsv"          # PS_ARN <tab> PS_NAME <tab> OURS(yes|no)
ASSIGN="$TMP/assign.tsv"        # PS_ARN <tab> PS_NAME <tab> ACCT_ID <tab> PRINCIPAL_TYPE <tab> PRINCIPAL_ID <tab> PRINCIPAL_NAME
MANAGED="$TMP/managed.tsv"      # PS_ARN <tab> PS_NAME <tab> MANAGED_ARN
INLINE="$TMP/inline.tsv"        # PS_ARN <tab> PS_NAME <tab> yes|no
: >"$ERRORS"; : >"$POLICIES"; : >"$ATTACH"; : >"$PSETS"; : >"$ASSIGN"; : >"$MANAGED"; : >"$INLINE"

if [ "$PROFILE" = "-" ] || [ "$PROFILE" = "none" ]; then
  PROFILE_OPT=""
  PROFILE_LABEL="(none - ambient credentials, e.g. CloudShell)"
else
  PROFILE_OPT="--profile $PROFILE"
  PROFILE_LABEL="$PROFILE"
fi

POLICY_TYPES="SERVICE_CONTROL_POLICY RESOURCE_CONTROL_POLICY TAG_POLICY DECLARATIVE_POLICY_EC2"

# ------------------------------------------------------------------------------ helpers

note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

aws_() { command aws $PROFILE_OPT --region "$REGION" "$@" </dev/null; }

RUN_OUT=""; RUN_STATUS=0
run() {
  RUN_OUT=$(aws_ "$@" 2>&1)
  RUN_STATUS=$?
  if [ "$RUN_STATUS" -ne 0 ]; then
    printf 'aws %s\n    %s\n' "$*" "$(printf '%s' "$RUN_OUT" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"
    RUN_OUT=""
  fi
}

# EVERY `--output text` LIST IS RE-EMITTED WITH printf '%s\n', NEVER printf '%s', and the
# difference is a whole element. `$(...)` strips trailing newlines, so `printf '%s' "$RUN_OUT"`
# hands the pipeline a stream whose LAST line has no terminator - and `while read` returns
# false at that point, so the loop body never runs for it. One managed policy becomes zero;
# five accounts become four. Nothing errors and nothing is empty, so the manifest just comes
# out one row short - which is exactly the failure section 6 warns about, arriving from
# inside the script instead of from AWS. Found here on the first run, 2026-08-15.

tabulate() { column -t -s $'\t'; }

# `terraform import` takes ONE string on the right. Emitting it with the suggested address on
# the left and the object named above keeps the two halves visibly separate - which is the
# whole point of section 5.
imp() { # imp <what> <suggested address> <import id>
  printf '# %s\n' "$1"
  printf "terraform import '%s' '%s'\n\n" "$2" "$3"
}

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

# ---------------------------------------------------------------- the organization anchors

note "reading the organization anchors..."

run organizations describe-organization --query 'Organization.[Id,MasterAccountId]' --output text
ORG_ID=$(printf '%s' "$RUN_OUT" | cut -f1)
MGMT_ID=$(printf '%s' "$RUN_OUT" | cut -f2)

run organizations list-roots --query 'Roots[0].[Name,Id]' --output text
ROOT_NAME=$(printf '%s' "$RUN_OUT" | cut -f1)
ROOT_ID=$(printf '%s' "$RUN_OUT" | cut -f2)

# Walk the tree breadth-first: depth is 2 (D23, `Sandboxes` under `Interactive`) and a walk
# written for depth 1 misses it silently - the same nesting that breaks a single-level
# `for_each` in Stage 2 step 5.3.
NODES="$TMP/nodes.tsv"   # KIND <tab> NAME <tab> ID <tab> PATH
: >"$NODES"
printf 'ROOT\t%s\t%s\t%s/%s/\n' "$ROOT_NAME" "$ROOT_ID" "$ORG_ID" "$ROOT_ID" >>"$NODES"
QUEUE="$TMP/queue"; NEXT="$TMP/next"
printf '%s\t%s/%s/\n' "$ROOT_ID" "$ORG_ID" "$ROOT_ID" >"$QUEUE"
while [ -s "$QUEUE" ]; do
  : >"$NEXT"
  while IFS=$'\t' read -r pid ppath; do
    [ -n "${pid:-}" ] || continue
    run organizations list-organizational-units-for-parent \
        --parent-id "$pid" --query 'OrganizationalUnits[].[Name,Id]' --output text
    [ -n "$RUN_OUT" ] || continue
    printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r nname nid; do
      [ -n "${nid:-}" ] || continue
      printf 'OU\t%s\t%s\t%s%s/\n' "$nname" "$nid" "$ppath" "$nid" >>"$NODES"
      printf '%s\t%s%s/\n' "$nid" "$ppath" "$nid" >>"$NEXT"
    done
  done <"$QUEUE"
  mv "$NEXT" "$QUEUE"
done

# The `Data` OU and its single account. <ACCOUNT_ID_DATA> feeds awsds-org-scp-ou-data.json;
# <ORG_PATH_DATA> feeds awsds-org-scp-BASELINE.json (the DenyDataZoneDomainOutsideDataOu
# condition). Stage 2 step 5.5a(ii): derive from the OU, never by account NAME (1d step 9
# recorded why a name lookup returns None here).
OU_ID_DATA=$(awk -F'\t' '$2=="Data" {print $3; exit}' "$NODES")
ORG_PATH_DATA=$(awk -F'\t' '$2=="Data" {print $4; exit}' "$NODES")
ACCOUNT_ID_DATA=""
if [ -n "${OU_ID_DATA:-}" ]; then
  run organizations list-accounts-for-parent --parent-id "$OU_ID_DATA" \
      --query 'Accounts[].Id' --output text
  ACCOUNT_ID_DATA=$(printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | head -1)
  N_DATA_ACCTS=$(printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | wc -l | tr -d ' ')
else
  N_DATA_ACCTS=0
fi

# ----------------------------------------------------------------- the organization policies

note "listing the organization policies, all four types..."

for ptype in $POLICY_TYPES; do
  run organizations list-policies --filter "$ptype" \
      --query 'Policies[?AwsManaged==`false`].[Id,Name]' --output text
  [ -n "$RUN_OUT" ] || continue
  printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r pid pname; do
    [ -n "${pid:-}" ] || continue
    case "$pname" in
      awsds-*) OURS=yes ;;
      *)       OURS=no  ;;
    esac
    printf '%s\t%s\t%s\t%s\n' "$ptype" "$pid" "$pname" "$OURS" >>"$POLICIES"
  done
done

note "listing each policy's targets..."
while IFS=$'\t' read -r ptype pid pname ours; do
  [ "$ours" = "yes" ] || continue
  run organizations list-targets-for-policy --policy-id "$pid" \
      --query 'Targets[].[TargetId,Name,Type]' --output text
  [ -n "$RUN_OUT" ] || continue
  printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r tid tname ttype; do
    [ -n "${tid:-}" ] || continue
    printf '%s\t%s\t%s\t%s\t%s\n' "$pid" "$pname" "$tid" "$tname" "$ttype" >>"$ATTACH"
  done
done <"$POLICIES"

# --------------------------------------------------------------------- Identity Center

note "reading the Identity Center instance..."

run sso-admin list-instances --query 'Instances[0].[InstanceArn,IdentityStoreId]' --output text
INSTANCE_ARN=$(printf '%s' "$RUN_OUT" | cut -f1)
STORE_ID=$(printf '%s' "$RUN_OUT" | cut -f2)

if [ -n "${INSTANCE_ARN:-}" ]; then
  note "listing permission sets..."
  run sso-admin list-permission-sets --instance-arn "$INSTANCE_ARN" \
      --query 'PermissionSets' --output text
  printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | while IFS= read -r psarn; do
    run sso-admin describe-permission-set --instance-arn "$INSTANCE_ARN" \
        --permission-set-arn "$psarn" --query 'PermissionSet.Name' --output text
    psname="${RUN_OUT:-(unnamed)}"
    # "Ours" is exactly the set Stage 2 imports: InfrastructureAccess and nothing else. The
    # other six persona sets are WRITTEN in step 5, never imported (Stage 1b step 3.9), and
    # Control Tower's are landing-zone drift if touched.
    case "$psname" in
      InfrastructureAccess) OURS=yes ;;
      *)                    OURS=no  ;;
    esac
    printf '%s\t%s\t%s\n' "$psarn" "$psname" "$OURS" >>"$PSETS"
  done

  note "listing assignments..."
  while IFS=$'\t' read -r psarn psname ours; do
    [ "$ours" = "yes" ] || continue

    run sso-admin list-managed-policies-in-permission-set --instance-arn "$INSTANCE_ARN" \
        --permission-set-arn "$psarn" --query 'AttachedManagedPolicies[].Arn' --output text
    printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | while IFS= read -r marn; do
      printf '%s\t%s\t%s\n' "$psarn" "$psname" "$marn" >>"$MANAGED"
    done

    run sso-admin get-inline-policy-for-permission-set --instance-arn "$INSTANCE_ARN" \
        --permission-set-arn "$psarn" --query 'InlinePolicy' --output text
    if [ -n "$RUN_OUT" ] && [ "$RUN_OUT" != "None" ]; then
      printf '%s\t%s\tyes\n' "$psarn" "$psname" >>"$INLINE"
    else
      printf '%s\t%s\tno\n' "$psarn" "$psname" >>"$INLINE"
    fi

    run sso-admin list-accounts-for-provisioned-permission-set --instance-arn "$INSTANCE_ARN" \
        --permission-set-arn "$psarn" --query 'AccountIds' --output text
    printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | while IFS= read -r acct; do
      run sso-admin list-account-assignments --instance-arn "$INSTANCE_ARN" \
          --account-id "$acct" --permission-set-arn "$psarn" \
          --query 'AccountAssignments[].[PrincipalType,PrincipalId]' --output text
      [ -n "$RUN_OUT" ] || continue
      printf '%s\n' "$RUN_OUT" | while IFS=$'\t' read -r ptype2 prid; do
        [ -n "${prid:-}" ] || continue
        prname="(unresolved)"
        if [ "$ptype2" = "GROUP" ]; then
          run identitystore describe-group --identity-store-id "$STORE_ID" \
              --group-id "$prid" --query 'DisplayName' --output text
          prname="${RUN_OUT:-(unresolved)}"
        elif [ "$ptype2" = "USER" ]; then
          run identitystore describe-user --identity-store-id "$STORE_ID" \
              --user-id "$prid" --query 'UserName' --output text
          prname="${RUN_OUT:-(unresolved)}"
        fi
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
          "$psarn" "$psname" "$acct" "$ptype2" "$prid" "$prname" >>"$ASSIGN"
      done
    done
  done <"$PSETS"
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'The import manifest - what `terraform import` takes, for Stage 2 step 5\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profile   : %s\n' "$PROFILE_LABEL"
printf 'caller    : %s\n' "$CALLER"
printf 'produced  : aws/import-ids.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. The anchors, and the values the policy TEMPLATES need\n'
printf '  2. The organization policies and their targets\n'
printf '  3. Identity Center - the instance, the sets, the assignments\n'
printf '  4. WHAT MUST NOT BE IMPORTED, and why - read before section 5\n'
printf '  5. THE MANIFEST - the `terraform import` lines\n'
printf '  6. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - THIS SCRIPT OWNS THE RIGHT-HAND SIDE, NOT THE LEFT. The id after the address is\n'
printf '    measured and correct. The ADDRESS is a suggestion: only the configuration knows\n'
printf '    whether the resource is `.baseline` or `.this["awsds-org-scp-baseline"]`.\n'
printf '  - AN IMPORT INTO A `for_each` RESOURCE IS THE ONE THAT GOES WRONG. The key has to\n'
printf '    be exactly what the configuration COMPUTES. A wrong key does not error - it\n'
printf '    leaves an orphan in state and a create in the plan. Import ONE, run `plan`, then\n'
printf '    the rest.\n'
printf '  - SECTION 4 IS NOT A FOOTNOTE. Importing a Control Tower policy or permission set\n'
printf '    is landing-zone drift, and the objects are listed there rather than filtered out\n'
printf '    so that an omission is distinguishable from an oversight.\n'
printf '  - THE IDS HERE ARE IDENTIFIERS. This file is untracked, like every snapshot under\n'
printf '    aws/output/. Nothing in it is copied into a tracked file (aws/INDEX.md rule 1) -\n'
printf '    which is also why Stage 2 decision 6 leans towards `terraform import` on the\n'
printf '    command line rather than `import {}` blocks, whose `id` would live in git.\n'

# ======================================================================================
h1 "1. The anchors, and the values the policy TEMPLATES need"

{
  printf 'NAME\tVALUE\tWHAT IT IS\n'
  printf 'ORG_ID\t%s\tthe value aws:PrincipalOrgID and aws:ResourceOrgID are compared against\n' "${ORG_ID:-(unread)}"
  printf 'ROOT_ID\t%s\tthe organization root - the target of six of the ten documents\n' "${ROOT_ID:-(unread)}"
  printf 'MGMT_ID\t%s\tthe management account; the ARN namespace of every organizations:: ARN\n' "${MGMT_ID:-(unread)}"
  printf 'INSTANCE_ARN\t%s\tthe Identity Center instance - the tail of every sso-admin import id\n' "${INSTANCE_ARN:-(unread)}"
  printf 'IDENTITY_STORE\t%s\tthe directory the group GUIDs belong to\n' "${STORE_ID:-(unread)}"
} | tabulate

printf '\n'
printf 'THE THREE PLACEHOLDERS IN terraform-live/identity/org-policies/policies/*.json, and\n'
printf 'what Terraform has to substitute for each (Stage 2 step 5.5a):\n\n'

{
  printf 'PLACEHOLDER\tRESOLVED VALUE\tWHERE TERRAFORM GETS IT\n'
  printf '<ORG_ID>\t%s\tdata.aws_organizations_organization.this.id\n' "${ORG_ID:-(unread)}"
  printf '<ORG_PATH_DATA>\t%s\tthe Data OU path, composed from the org, root and OU ids\n' "${ORG_PATH_DATA:-(unread)}"
  printf '<ACCOUNT_ID_DATA>\t%s\tthe single account under the Data OU - derived from the OU\n' "${ACCOUNT_ID_DATA:-(unread)}"
} | tabulate

printf '\n'
printf 'TWO THINGS ABOUT THAT TABLE THAT ARE NOT DECORATION.\n\n'
printf '  - `templatefile()` CANNOT READ THESE TEMPLATES. The placeholders are angle-bracketed,\n'
printf '    not ${...}, on purpose (render.sh explains why, and it anticipated this stage). The\n'
printf '    Terraform side is `replace(file(...), "<ORG_ID>", ...)`, wrapped in\n'
printf '    `jsonencode(jsondecode(...))` so BOTH sides are normalised the same way - which is\n'
printf '    what turns "the same document" from a claim about whitespace into one about content.\n'
printf '  - <ACCOUNT_ID_DATA> IS DERIVED FROM THE OU, NEVER FROM AN ACCOUNT NAME. Stage 1d step\n'
printf '    9 recorded why: a name filter returns None here, because the account is called\n'
printf '    `Data Governance Account` and not `Data Governance`. The Data OU holds exactly one\n'
printf '    account, so the OU is the safe handle.\n'
printf '\n'
printf 'Accounts under the Data OU: %s (expected: 1 - if this reads more, the derivation above\n' "${N_DATA_ACCTS:-0}"
printf 'is ambiguous and the document needs an explicit choice rather than a head -1).\n'

# ======================================================================================
h1 "2. The organization policies and their targets"

printf 'AwsManaged policies (FullAWSAccess, RCPFullAWSAccess) are excluded - they are AWS`s\n'
printf 'and cannot be imported. What is left is everything this organization created.\n\n'

if [ -s "$POLICIES" ]; then
  {
    printf 'OURS\tTYPE\tPOLICY ID\tNAME\n'
    sort -k4 "$POLICIES" | awk -F'\t' '{printf "%s\t%s\t%s\t%s\n", $4, $1, $2, $3}'
  } | tabulate
else
  printf '(none found - see section 6)\n'
fi

printf '\n'
printf 'THE ATTACHMENTS, which are separate objects and separate imports. `aws_organizations_\n'
printf 'policy_attachment` takes `<target_id>:<policy_id>` - the ONE import id in this file\n'
printf 'that is a composite with a colon rather than commas.\n\n'

if [ -s "$ATTACH" ]; then
  {
    printf 'POLICY\tPOLICY ID\tTARGET\tTARGET ID\tTARGET TYPE\n'
    sort "$ATTACH" | awk -F'\t' '{printf "%s\t%s\t%s\t%s\t%s\n", $2, $1, $4, $3, $5}'
  } | tabulate
  printf '\n'
  NROOT=$(awk -F'\t' '$5=="ROOT"' "$ATTACH" | wc -l | tr -d ' ')
  NOU=$(awk -F'\t' '$5=="ORGANIZATIONAL_UNIT"' "$ATTACH" | wc -l | tr -d ' ')
  printf '%s attachment(s) to the ROOT, %s to an OU.\n' "$NROOT" "$NOU"
  printf 'THE ROOT COUNT IS THE ONE THAT DECIDES THE SIZE OF STAGE 2 - it is what Stage 2\n'
  printf 'step 5.0 and ./aws/org-delegation.sh`s DEL-6 are about. If the delegation cannot\n'
  printf 'reach root attachments, every one of those rows stays console-managed.\n'
else
  printf '(no attachments found - see section 6)\n'
fi

# ======================================================================================
h1 "3. Identity Center - the instance, the sets, the assignments"

if [ -s "$PSETS" ]; then
  {
    printf 'IMPORT?\tNAME\tPERMISSION SET ARN\n'
    sort -k3 "$PSETS" | awk -F'\t' '{printf "%s\t%s\t%s\n", $3, $2, $1}'
  } | tabulate
else
  printf '(no permission sets found - see section 6)\n'
fi

printf '\n'
printf 'ONLY `InfrastructureAccess` IS MARKED yes, AND THAT IS THE DESIGN, NOT A FILTER BUG.\n'
printf 'The other six persona sets - DataScientistAccess, DataScientistStagingAccess,\n'
printf 'DataScientistProdAccess, DeploymentManagerAccess, GovernanceManagerAccess,\n'
printf 'DevEnvStewardAccess - are WRITTEN in Stage 2 step 5 and were never typed into a\n'
printf 'console (Stage 1b step 3.9), so there is nothing to import and their first apply is a\n'
printf 'CREATE. An empty plan there would mean nothing was written.\n'

printf '\n'
h2 "Assignments of the imported set"

if [ -s "$ASSIGN" ]; then
  {
    printf 'ACCOUNT\tPRINCIPAL TYPE\tPRINCIPAL\tPRINCIPAL ID\tPERMISSION SET\n'
    sort "$ASSIGN" | awk -F'\t' '{printf "%s\t%s\t%s\t%s\t%s\n", $3, $4, $6, $5, $2}'
  } | tabulate
  printf '\n'
  printf 'THE PRINCIPAL ID IS A GUID AND THE IMPORT NEEDS IT - but the CONFIGURATION must not\n'
  printf 'carry it. `plan/conventions.md` requires a group to be resolved by DISPLAY NAME\n'
  printf 'through `data.aws_identitystore_group`, because group IDs are properties of ONE\n'
  printf 'directory instance: federate to a corporate IdP and every hardcoded GUID becomes a\n'
  printf 'resource that matches nothing. So the GUID goes on the import command line and the\n'
  printf 'display name goes in the code - and this table is where the two are seen together.\n'
else
  printf '(no assignments found for the imported set - see section 6)\n'
fi

# ======================================================================================
h1 "4. WHAT MUST NOT BE IMPORTED, and why"

printf 'Listed rather than filtered out, so that "not here" and "missed" stay distinguishable.\n\n'

h2 "Control Tower's policies - importing one is landing-zone drift"

if awk -F'\t' '$4=="no"' "$POLICIES" | grep -q .; then
  {
    printf 'TYPE\tPOLICY ID\tNAME\n'
    awk -F'\t' '$4=="no" {printf "%s\t%s\t%s\n", $1, $2, $3}' "$POLICIES" | sort -k3
  } | tabulate
else
  printf '(none)\n'
fi
printf '\n'
printf 'These are generated and owned by the landing zone (Stage 2 step 5.4). Importing one\n'
printf 'puts Terraform and Control Tower in a fight over the same object. If the REGION\n'
printf 'restriction is ever to be in code, the resource is `aws_controltower_control` - the\n'
printf 'control, not the SCP it emits.\n'

h2 "Control Tower's permission sets - and one of them cannot even be reached"

if awk -F'\t' '$3=="no"' "$PSETS" | grep -q .; then
  {
    printf 'NAME\tPERMISSION SET ARN\n'
    awk -F'\t' '$3=="no" {printf "%s\t%s\n", $2, $1}' "$PSETS" | sort
  } | tabulate
else
  printf '(none)\n'
fi
printf '\n'
printf '`AWSAdministratorAccess` is the one to know about: a permission set PROVISIONED INTO\n'
printf 'MANAGEMENT cannot be altered from the Identity account at all - measured 2026-08-12,\n'
printf 'Stage 1b step 5.1 - and the deny is anchored on the SET rather than on the target\n'
printf 'account, so it covers that set`s assignments in EVERY account. Anything touching it\n'
printf 'runs as `AWS Control Tower Admin` on Management.\n'
printf '\n'
printf 'ALSO NOT MODELLED: the Account Factory DIRECT assignments (D32). `Policy Canary` still\n'
printf 'carries one, permanently - it is the only way into that account. A direct assignment is\n'
printf 'a property of a vended account, not an entitlement this repository designs.\n'
printf '\n'
printf 'AND NOT IN ANY STATE FILE, EVER: the four users, the five groups and the memberships.\n'
printf 'They are people. `plan/conventions.md`, "The identity seam".\n'

# ======================================================================================
h1 "5. THE MANIFEST - the \`terraform import\` lines"

printf 'CHECK EVERY ADDRESS AGAINST THE CONFIGURATION BEFORE RUNNING A LINE. The id is\n'
printf 'measured; the address is a suggestion in the shape Stage 2 step 5.3 implies\n'
printf '(`for_each` in org-policies/, written-out resources in sso/).\n'
printf '\n'
printf 'Run them from inside the slice directory, with the right profile:\n'
printf '\n'
printf '    AWS_PROFILE=awsds-infra-identity terraform import ...\n'
printf '\n'
printf 'and NEVER through `eval $(aws sts assume-role ...)` - an exported credential outlives\n'
printf 'the command that needed it and every later error then names the wrong account\n'
printf '(Lesson 25).\n'

h2 "5a. terraform-live/identity/org-policies/ - the documents"

if [ -s "$POLICIES" ]; then
  while IFS=$'\t' read -r ptype pid pname ours; do
    [ "$ours" = "yes" ] || continue
    imp "$pname  ($ptype)" "aws_organizations_policy.this[\"$pname\"]" "$pid"
  done <"$POLICIES"
else
  printf '(nothing to emit)\n\n'
fi

h2 "5b. terraform-live/identity/org-policies/ - the attachments"

printf '# ONE PER (policy, target) PAIR. The import id is <target_id>:<policy_id>.\n'
printf '# Import the FIRST one, run `terraform plan`, and only then the rest - if the\n'
printf '# for_each key is wrong the import succeeds and the plan proposes a create.\n\n'

if [ -s "$ATTACH" ]; then
  while IFS=$'\t' read -r pid pname tid tname ttype; do
    imp "$pname -> $tname ($ttype)" \
        "aws_organizations_policy_attachment.this[\"$pname:$tname\"]" \
        "$tid:$pid"
  done <"$ATTACH"
else
  printf '(nothing to emit)\n\n'
fi

h2 "5c. terraform-live/identity/sso/ - the imported permission set"

if [ -n "${INSTANCE_ARN:-}" ] && [ -s "$PSETS" ]; then
  while IFS=$'\t' read -r psarn psname ours; do
    [ "$ours" = "yes" ] || continue
    imp "$psname - the permission set itself" \
        "aws_ssoadmin_permission_set.infrastructure" \
        "$psarn,$INSTANCE_ARN"
  done <"$PSETS"

  while IFS=$'\t' read -r psarn psname marn; do
    imp "$psname - managed policy $(basename "$marn")" \
        "aws_ssoadmin_managed_policy_attachment.infrastructure[\"$(basename "$marn")\"]" \
        "$marn,$psarn,$INSTANCE_ARN"
  done <"$MANAGED"

  while IFS=$'\t' read -r psarn psname has; do
    [ "$has" = "yes" ] || continue
    imp "$psname - its inline policy" \
        "aws_ssoadmin_permission_set_inline_policy.infrastructure" \
        "$psarn,$INSTANCE_ARN"
  done <"$INLINE"
else
  printf '(nothing to emit - the Identity Center instance was not read, see section 6)\n\n'
fi

h2 "5d. terraform-live/identity/sso/ - the assignments"

printf '# SIX comma-separated fields, in this order:\n'
printf '#   <principal_id>,<principal_type>,<target_id>,<target_type>,<permission_set_arn>,<instance_arn>\n'
printf '# The principal id is the GUID; the CONFIGURATION resolves the same group by display\n'
printf '# name through data.aws_identitystore_group (section 3).\n\n'

if [ -s "$ASSIGN" ] && [ -n "${INSTANCE_ARN:-}" ]; then
  while IFS=$'\t' read -r psarn psname acct ptype2 prid prname; do
    imp "$psname for $prname on account $acct" \
        "aws_ssoadmin_account_assignment.infrastructure[\"$prname:$acct\"]" \
        "$prid,$ptype2,$acct,AWS_ACCOUNT,$psarn,$INSTANCE_ARN"
  done <"$ASSIGN"
else
  printf '(nothing to emit)\n\n'
fi

# ======================================================================================
h1 "6. Calls that failed"

if [ -s "$ERRORS" ]; then
  cat "$ERRORS"
  printf '\nA MANIFEST WITH A FAILED CALL IN IT IS INCOMPLETE, NOT WRONG - and the difference\n'
  printf 'matters: importing from a short list leaves objects unmanaged with an empty plan,\n'
  printf 'which looks exactly like success. Fix the failure and regenerate before importing.\n'
else
  printf 'None. Every call returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/import-ids.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 6; the manifest is INCOMPLETE)"
  exit 1
fi
note "wrote $OUT"
exit 0
