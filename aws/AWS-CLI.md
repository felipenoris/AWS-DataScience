# AWS CLI

Use CloudShell at AWS Console.

**Before typing a listing by hand, check [`aws/INDEX.md`](INDEX.md).** The read-only scripts there
capture the Organization tree, the accounts and the whole Identity Center directory into `aws/output/`,
from a named local profile rather than from CloudShell. This file holds the one-off recipes and what the
scripts do not cover.

## Signing in

The SSO token is keyed by the `sso-session` name, not by profile or account, so one login covers every
profile that names that session. This configuration has one session per person, as a rule:

| `sso-session` | Who signs in | Profiles it covers |
|---|---|---|
| `awsds` | the **infrastructure user** | every `awsds-infra-*`, plus `awsds-policy-canary` |
| `awsds-ctadmin` | **`AWS Control Tower Admin`** (added 2026-08-15) | `awsds-ctadmin-orgfull-*` — `AWSOrganizationsFullAccess` in a member account, the only CLI this user has |
| `awsds-scientist` | **Data Scientist User** (added 2026-08-17, Stage 4 step 8.3) | `awsds-scientist-sandbox` (`DataScientistAccess`) and `awsds-scientist-prod` (`DataScientistProdAccess`) — two permission sets, one person, one session |
| `awsds-deploy` | **Deployment Manager User** (idem) | `awsds-deploy-*` — `DeploymentManagerAccess` |
| `awsds-governance` | **Governance Manager User** (idem) | `awsds-governance-*` — `GovernanceManagerAccess` |
| `awsds-devenv` | **Dev Env Steward User** (idem) | `awsds-devenv-*` — `DevEnvStewardAccess` |

```bash
aws sso login --sso-session awsds
```

The question is which identity to pick in the browser, and where the work is about to land — never
which profile to log in with. A profile whose session is not logged in fails in a way that reads like a
permission problem. `aws sts get-caller-identity` before the first real call tells the two apart, and the
assumed-role ARN it prints is the evidence of which permission set answered (`docs/GLOSSARY.md`,
"Permission set").

The naming: the session names the **person**; the profile is `awsds-<person>-<account>`, and the segment
between names the **role** wherever one person holds several (`-infra-`, `-ctadmin-orgfull-`). The persona
rows drop that segment because person and role coincide. The exception: `awsds-scientist-sandbox` and
`awsds-scientist-prod` carry different permission sets, told apart by the account and not by the name.

### One session per person

The cache is keyed by the session name, so a shared session is a single token, and the profile you switch
to is not the identity you switch to. Point two profiles of two users at one session, log in as the first,
then use the second: the CLI calls `sso:GetRoleCredentials` with the first user's token asking for the
second user's role. The portal refuses, because that user has no such assignment — at credential vending
time, which is neither an IAM `AccessDenied` nor a missing grant (Stage 4 step 8.3's control-plane pair).
Lesson 25 is the general form.

`aws sso logout` clears the cache for every session, not only the one named, so switching persona by
persona costs the infrastructure user's token too. That is a re-login, never a lockout:
`InfrastructureAccess` is outside `DenyControlPlaneOffVpn` and signs in from any network.

## Account names and ids

Login as `AWS Control Tower Admin User`.

```
aws organizations list-accounts --query 'Accounts[].[Name,Id]' --output table
```

## Identity Store id

```
aws sso-admin list-instances
```

## The statements attached to each OU

Run as the **infrastructure user** on **Identity**, profile `awsds-infra-identity`: every Organizations
policy read answers from there; only `controltower list-enabled-controls` needs Management.

Read the `Sid` list, never the policy id or its name (Lesson 23): Control Tower packs per enablement, so
which of an OU's documents holds a given control differs between OUs. The walk is depth-aware because
`Sandboxes` is nested.

```bash
P=awsds-infra-identity; ROOT=$(aws organizations list-roots --profile $P --query 'Roots[0].Id' --output text); walk() { for ou in $(aws organizations list-organizational-units-for-parent --parent-id "$1" --profile $P --query 'OrganizationalUnits[].Id' --output text); do echo "=== $(aws organizations describe-organizational-unit --organizational-unit-id $ou --profile $P --query 'OrganizationalUnit.Name' --output text) ($ou)"; for pid in $(aws organizations list-policies-for-target --target-id $ou --filter SERVICE_CONTROL_POLICY --profile $P --query 'Policies[].Id' --output text); do [ "$pid" = "p-FullAWSAccess" ] && continue; echo "  $(aws organizations describe-policy --policy-id $pid --profile $P --query 'Policy.PolicySummary.Name' --output text) ($pid)"; aws organizations describe-policy --policy-id $pid --profile $P --query 'Policy.Content' --output text | python3 -c 'import json,sys; print("    "+", ".join(s.get("Sid","?") for s in json.load(sys.stdin)["Statement"]))'; done; walk "$ou"; done; }; walk $ROOT
```

To dump one document in full — the instrument for anything no probe can reach ([the battery
runbook](../docs/plan/runbooks/scp-battery.md), "the class the battery cannot reach"), such as confirming
`aws:AssumedRoot` is present in a `GRRESTRICTROOTUSER` condition:

```bash
aws organizations describe-policy --policy-id p-kve97k0o --profile awsds-infra-identity --query 'Policy.Content' --output text | python3 -m json.tool
```

## Identity Center change alerts

Metric:

```
aws cloudwatch get-metric-statistics --namespace AWSDS/Security --metric-name IdentityCenterChangeCount --start-time "$(date -u -d '-6 hours' +%Y-%m-%dT%H:%M:%SZ)" --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --period 300 --statistics Sum
```

Alarm:

```
aws cloudwatch describe-alarm-history --alarm-name "Identity Center membership and assignment change" --history-item-type StateUpdate --max-records 10 --query 'AlarmHistoryItems[].[Timestamp,HistorySummary]' --output text
```
