# AWS CLI

Use CloudShell at AWS Console.

**Before typing a listing by hand, check [`aws/INDEX.md`](INDEX.md):** the read-only scripts there
already capture the Organization tree, the accounts, and the whole Identity Center directory into
`aws/output/`, from a named local profile rather than from CloudShell. What stays here are the one-off
recipes and anything the scripts do not cover.

## Signing in — one login per `sso-session`, and there are two

*Moved out of `CLAUDE.md` on 2026-08-15, which keeps the rule and not the mechanics.*

**The SSO token is keyed by the `sso-session` name, not by profile or account**, so one login covers every
profile that names that session — and this configuration has two sessions, because they are two different
people:

| `sso-session` | Who signs in | Profiles it covers |
|---|---|---|
| `awsds` | the **infrastructure user** | every `awsds-infra-*`, plus `awsds-policy-canary` |
| `awsds-ctadmin` | **`AWS Control Tower Admin`** (added 2026-08-15) | `awsds-ctadmin-orgfull-*` — `AWSOrganizationsFullAccess` in a member account, which is the only CLI this user has |

```bash
aws sso login --sso-session awsds
```

So the question is never *"which profile do I log in with"* — it is **which identity to pick in the
browser**, plus where the work is about to land. A profile whose session is not logged in fails in a way
that reads like a permission problem and is not; `aws sts get-caller-identity` before the first real call
is what tells the two apart, and the assumed-role ARN it prints is the evidence of *which* permission set
answered (`docs/GLOSSARY.md`, "Permission set").

## Lists accounts with IDs

Login as `AWS Control Tower Admin User`.

```
aws organizations list-accounts --query 'Accounts[].[Name,Id]' --output table
```
## Lists Identity Store ID (SSO)

```
aws sso-admin list-instances
```

## What every OU actually carries, statement by statement

Run as the **infrastructure user** on **Identity**, profile `awsds-infra-identity` — every Organizations
*policy* read answers from there; only `controltower list-enabled-controls` needs Management.

**Read the `Sid` list, never the policy id or its name** (Lesson 23): Control Tower packs per *enablement*,
so which of an OU's documents holds a given control differs between OUs, and "the region policy" is not a
stable way to refer to anything. This walk is depth-aware, which matters because `Sandboxes` is nested.

```bash
P=awsds-infra-identity; ROOT=$(aws organizations list-roots --profile $P --query 'Roots[0].Id' --output text); walk() { for ou in $(aws organizations list-organizational-units-for-parent --parent-id "$1" --profile $P --query 'OrganizationalUnits[].Id' --output text); do echo "=== $(aws organizations describe-organizational-unit --organizational-unit-id $ou --profile $P --query 'OrganizationalUnit.Name' --output text) ($ou)"; for pid in $(aws organizations list-policies-for-target --target-id $ou --filter SERVICE_CONTROL_POLICY --profile $P --query 'Policies[].Id' --output text); do [ "$pid" = "p-FullAWSAccess" ] && continue; echo "  $(aws organizations describe-policy --policy-id $pid --profile $P --query 'Policy.PolicySummary.Name' --output text) ($pid)"; aws organizations describe-policy --policy-id $pid --profile $P --query 'Policy.Content' --output text | python3 -c 'import json,sys; print("    "+", ".join(s.get("Sid","?") for s in json.load(sys.stdin)["Statement"]))'; done; walk "$ou"; done; }; walk $ROOT
```

To dump one document in full — the instrument for anything no probe can reach ([the battery
runbook](../docs/plan/runbooks/scp-battery.md), "the class the battery cannot reach"), such as confirming
`aws:AssumedRoot` is present in a `GRRESTRICTROOTUSER` condition:

```bash
aws organizations describe-policy --policy-id p-kve97k0o --profile awsds-infra-identity --query 'Policy.Content' --output text | python3 -m json.tool
```

## Busca alertas:

Métrics:

```
aws cloudwatch get-metric-statistics --namespace AWSDS/Security --metric-name IdentityCenterChangeCount --start-time "$(date -u -d '-6 hours' +%Y-%m-%dT%H:%M:%SZ)" --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --period 300 --statistics Sum
```

Alarm:

```
aws cloudwatch describe-alarm-history --alarm-name "Identity Center membership and assignment change" --history-item-type StateUpdate --max-records 10 --query 'AlarmHistoryItems[].[Timestamp,HistorySummary]' --output text
```
