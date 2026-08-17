# AWS CLI

Use CloudShell at AWS Console.

**Before typing a listing by hand, check [`aws/INDEX.md`](INDEX.md):** the read-only scripts there
already capture the Organization tree, the accounts, and the whole Identity Center directory into
`aws/output/`, from a named local profile rather than from CloudShell. What stays here are the one-off
recipes and anything the scripts do not cover.

## Signing in — one login per `sso-session`, and there is one session per PERSON

*Moved out of `CLAUDE.md` on 2026-08-15, which keeps the rule and not the mechanics.*

**The SSO token is keyed by the `sso-session` name, not by profile or account**, so one login covers every
profile that names that session — and this configuration has **one session per human being**, which is the
rule rather than a description of how many there happen to be:

| `sso-session` | Who signs in | Profiles it covers |
|---|---|---|
| `awsds` | the **infrastructure user** | every `awsds-infra-*`, plus `awsds-policy-canary` |
| `awsds-ctadmin` | **`AWS Control Tower Admin`** (added 2026-08-15) | `awsds-ctadmin-orgfull-*` — `AWSOrganizationsFullAccess` in a member account, which is the only CLI this user has |
| `awsds-scientist` | **Data Scientist User** (added 2026-08-17, Stage 4 step 8.3's pair) | `awsds-scientist-sandbox` (`DataScientistAccess`) and `awsds-scientist-prod` (`DataScientistProdAccess`) — **two permission sets, one person, so one session** |
| `awsds-deploy` | **Deployment Manager User** (idem) | `awsds-deploy-*` — `DeploymentManagerAccess` |
| `awsds-governance` | **Governance Manager User** (idem) | `awsds-governance-*` — `GovernanceManagerAccess` |
| `awsds-devenv` | **Dev Env Steward User** (idem) | `awsds-devenv-*` — `DevEnvStewardAccess` |

```bash
aws sso login --sso-session awsds
```

So the question is never *"which profile do I log in with"* — it is **which identity to pick in the
browser**, plus where the work is about to land. A profile whose session is not logged in fails in a way
that reads like a permission problem and is not; `aws sts get-caller-identity` before the first real call
is what tells the two apart, and the assumed-role ARN it prints is the evidence of *which* permission set
answered (`docs/GLOSSARY.md`, "Permission set").

**The naming, so a seventh row does not have to invent one:** the session names the **person**; the profile
is `awsds-<person>-<account>`, with the segment between naming the **role** wherever one person holds
several (`-infra-`, `-ctadmin-orgfull-`). The persona rows drop that segment because the person and the
role coincide — with one exception worth knowing rather than fixing: `awsds-scientist-sandbox` and
`awsds-scientist-prod` carry **different** permission sets, told apart by the account and not by the name.

### Why one session per person is a rule and not tidiness

Because the cache is keyed by the session **name**: a shared session is a single token, and the profile you
switch to is not the identity you switch to. Point two profiles of two different users at one session, log
in as the first, then use the second, and the CLI calls `sso:GetRoleCredentials` with the **first** user's
token asking for the **second** user's role. It does not hand over the wrong credential — the portal
refuses, because that user has no such assignment — but it refuses **from the portal, at credential vending
time**, which is neither of the two failures anybody is usually looking at. In a reading that turns on
telling an IAM `AccessDenied` apart from a missing grant (Stage 4 step 8.3's control-plane pair), that is a
third refusal wearing the same clothes. Lesson 25 is the general form.

**And `aws sso logout` clears the cache for every session, not the one you name** — so switching persona by
persona costs the infrastructure user's token too. That is a re-login, never a lockout:
`InfrastructureAccess` is deliberately outside `DenyControlPlaneOffVpn`, so it signs in from any network.

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
