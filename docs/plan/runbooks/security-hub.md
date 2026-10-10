# Runbook — Security Hub

| | |
|---|---|
| **Scope** | Security Hub CSPM as [Stage 5a step 13](../stages/stage-05a-data-foundation.md) built it, and the recurring acts its life needs: pausing the standard that bills (§P), putting it back (§R), reading the state from either side (§V), and what each failure means (§F). Disabling the service itself is §D, written from the documentation and never run |
| **Operator** | §P, §R and §D: **[user]** as **`AWS Control Tower Admin`** → account **Audit** → permission set **`AWSAdministratorAccess`**, CloudShell, `us-west-2`. Audit holds no CLI profile (D33/D34), so Claude runs nothing there. §V's member-side reads: the **infrastructure user**, permission set **`InfrastructureAccess`**, the `awsds-infra-*` profiles |
| **The rules** | Every governed account is **centrally managed**, so `disable-security-hub`, `batch-disable-standards` and `batch-enable-standards` are refused in a member; the only door is the policy in Audit. A policy with `ServiceEnabled: false` **does not apply to the delegated administrator**, which is why the pause removes the standard and keeps the service on. `update-configuration-policy` replaces every list it carries, so the whole policy is written on each call, from the read that precedes it |

## S. The pieces

- **The product is Security Hub CSPM**, the one that runs standards. The v2 product beside it (`*-v2` calls) is refused by step 13.0: enabling both hands the Config recorder to a service-linked one and takes it from Control Tower. `./aws/datalake.py` `DL-11` fails on v2's arrival.
- **Audit is the delegated administrator**, designated from Management 2026-08-20. Designating it enabled the hub there; nothing in the ceiling shapes `securityhub:` calls (`CT.MULTISERVICE.PV.1` does not exempt the service, so another Region is refused, which is the intent).
- **Central configuration, home Region `us-west-2`, aggregator `NO_REGIONS`.** One policy, **`awsds-fsbp-only`**, associated with the root; Management is self-managed (13.1c) and unrecorded by Config, so a root policy reaching it would give a bill and `WARNING` findings. Child OUs and accounts inherit the root's policy. Associations take up to 24 h to leave `PENDING`; the root and the suspended account of `EXC-01` never do.
- **The checks are Config rules** named `securityhub-*`, evaluated by Control Tower's `aws-controltower-BaselineConfigRecorder`. In the accounts with a profile they were the only Config rules present (read 2026-10-09). A standard removed deletes them; a standard added creates them again.
- **The meter is `USW2-PaidComplianceCheck`, 0.001 USD a check**, after a 30-day window per account that closed 2026-09-20. Finding ingestion is free under 10,000 a month, and the estate ingests about 800 a day per account. Measured with the standard on: about **0.45 USD/day** for the organization, 13.5 a month, 21 to 149 checks a day per account. With no standard: nothing. `docs/PRICING.md` carries the row.
- **The three states of the policy.** FSBP on (built 2026-08-20); the service on with **no standard** (the pause, since 2026-10-09, `EXC-14` in `docs/AWS_STATE.md`); the service off (§D, never run). `DL-11` reads the first as `ok`, the second as a note, and the standard off in *some* accounts as a failure, which is drift.

## P. Pausing the standard

Run 2026-10-09; the transcript is in [the stage log](../../log/log-stage-05a-data-foundation.md).

1. In Audit's CloudShell, find the policy and read it. The read is the state §R restores.

```bash
POLICY_ID=$(aws securityhub list-configuration-policies --region us-west-2 --query "ConfigurationPolicySummaries[?Name=='awsds-fsbp-only'].Id" --output text) && echo "$POLICY_ID"
```

```bash
aws securityhub get-configuration-policy --identifier "$POLICY_ID" --region us-west-2
```

2. Write the policy back with an empty standards list. The API accepts it (measured); `Description` is not passed and keeps saying "FSBP only" until §R.

```bash
aws securityhub update-configuration-policy --identifier "$POLICY_ID" --region us-west-2 --updated-reason 'Pause the FSBP checks, cost, <date>' --configuration-policy '{"SecurityHub":{"ServiceEnabled":true,"EnabledStandardIdentifiers":[],"SecurityControlsConfiguration":{"DisabledSecurityControlIdentifiers":[]}}}'
```

3. Read the associations (§V1). Every row goes `PENDING` because the update re-walks the tree; a first read seconds later shows part of the walk.

4. From a member profile, within minutes: `get-enabled-standards` is empty while `describe-hub` still answers, and the `securityhub-*` rule count falls (§V2). Findings are archived over 3 to 5 days and the archived ones deleted after 30; nobody reads them today (13.3's triage never ran), so nothing is exported first.

5. Record it: a log entry, `EXC-14` open, the `PRICING.md` row.

## R. Re-enabling the standard

1. The same read as §P1.

2. Write the policy with the FSBP ARN back. The ARN is the one the stage used; `describe-standards` lists it if in doubt.

```bash
aws securityhub update-configuration-policy --identifier "$POLICY_ID" --region us-west-2 --updated-reason 'FSBP back on, <date>' --configuration-policy '{"SecurityHub":{"ServiceEnabled":true,"EnabledStandardIdentifiers":["arn:aws:securityhub:us-west-2::standards/aws-foundational-security-best-practices/v/1.0.0"],"SecurityControlsConfiguration":{"DisabledSecurityControlIdentifiers":[]}}}'
```

3. Read the associations (§V1), then from a member `get-enabled-standards` reads the FSBP subscription `PENDING` then `READY`, and the rule count climbs back (§V2).

4. What follows: findings are generated from scratch, with duplicates possible for a few days where an archived one is still alive; the free window does not reopen; `PaidComplianceCheck` bills from the next full day. Any control disabled in 13.3's triage is a `DisabledSecurityControlIdentifiers` entry and goes in the same call, since the list is replaced whole.

5. Record it: a log entry, `EXC-14` closed, the `PRICING.md` row, `DL-11` back to `ok`.

## D. Disabling the service

Not run. Written from the documentation (`docs/REFERENCES.md`, read 2026-10-09), so it is a claim until exercised (Lesson 54).

- A policy with `ServiceEnabled: false` on the root disables the hub in every member and **not in Audit**: the association succeeds and the policy is not applied there. The members' archived findings are deleted after 30 days and their active findings, insights and settings after 90; re-enabling inside those windows restores them.
- Audit's own hub cannot be disabled while Audit is the delegated administrator. The full teardown is the policy above, then from Management `disable-organization-admin-account`, then in Audit `disable-security-hub`; it also removes `securityhub` from `INV-09`'s ten principals and four delegations, so `INV-09` is restated in the same sitting.
- Against the pause it saves Audit's own checks only, which the pause already stops, and it starts the deletion clocks. It is the right act only when the service is being retired, not paused.

## V. The readings

**V1, from Audit** (the operator above). Rows not yet settled:

```bash
aws securityhub list-configuration-policy-associations --region us-west-2 --query "ConfigurationPolicyAssociationSummaries[?AssociationStatus!='SUCCESS'].{Target:TargetId,Type:TargetType,Status:AssociationStatus}" --output table
```

Two rows stay `PENDING` for good: the root and the suspended account (`EXC-01`). Anything else still pending after 24 h is §F1.

**V2, from a member** (the infrastructure user; `<profile>` is one of `awsds-infra-sandbox-1`, `-staging`, `-prod`, `-data`, `-identity`):

```bash
aws securityhub get-enabled-standards --region us-west-2 --profile <profile> --query 'StandardsSubscriptions[].[StandardsArn,StandardsStatus]' --output text
```

```bash
aws configservice describe-config-rules --region us-west-2 --profile <profile> --query "ConfigRules[?starts_with(ConfigRuleName,'securityhub-')].ConfigRuleName" --output json | jq length
```

`describe-config-rules` paginates, and a `length()` query with `--output text` prints one number per page; the `--output json | jq length` form is the count.

**V3, the bill**, per account, from the same profiles (`ce:GetCostAndUsage` answers a member about its own spend; the organization total is Management's console):

```bash
aws ce get-cost-and-usage --profile <profile> --time-period Start=<YYYY-MM-DD>,End=<YYYY-MM-DD> --granularity DAILY --metrics UnblendedCost UsageQuantity --filter '{"Dimensions":{"Key":"USAGE_TYPE","Values":["USW2-PaidComplianceCheck"]}}' --output json | jq -r '.ResultsByTime[] | "\(.TimePeriod.Start) cost=\(.Total.UnblendedCost.Amount) checks=\(.Total.UsageQuantity.Amount)"'
```

Cost Explorer lags about a day.

**V4, the instrument**: `./aws/datalake.py`, section 11 and `DL-11`.

**The rule-deletion timeline, measured 2026-10-09** (update at 02:23 UTC; counts of `securityhub-*` rules):

| Account | about 02:25 UTC | 02:29 UTC |
|---|---|---|
| Sandbox | 191 | 24 |
| Staging | 309 | 205 |
| Production | 346 | 346 |
| Data Governance | 322 | 289 |
| Identity | 193 | 71 |

The deletion runs per account at its own pace; a count still above zero a day later is §F2.

## F. When something is wrong

1. **An association pending after 24 h**, other than the two that never settle: read `get-configuration-policy-association` for that target; a `FAILURE` carries its reason. A target under an SCP that denies `securityhub:` would fail this way; none does today.
2. **`securityhub-*` rules left with no standard enabled.** AWS retries a failed deletion every 12 h, but *"if you disabled Security Hub CSPM or don't have any other standards enabled, Security Hub CSPM can't try again"*: the rules are orphans and AWS Support removes them. Putting the standard back (§R) adopts them instead.
3. **A member's `batch-disable-standards` or `disable-security-hub` refused.** Expected: the account is centrally managed. The act is §P or §D, in Audit.
4. **`PaidComplianceCheck` still billing after §P.** Read V1 for the policy actually associated with the account's OU; a later policy applied to an OU overrides the root's. Then allow Cost Explorer its day.
5. **`DL-11` failing on "hub enabled without FSBP" in some accounts, not all.** Drift, not the pause: a self-managed designation or a second policy reached those accounts. V1 shows which.
