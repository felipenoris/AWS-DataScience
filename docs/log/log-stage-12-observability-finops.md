# Log — Stage 12 — Observability, governance and FinOps

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-12-observability-finops.md`](../plan/stages/stage-12-observability-finops.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-18 — step 10's first runs: `OB-2` in Log Archive's CloudShell, the rest from the laptop

*Two read-only runs of `aws/observability.py` as PR #163 merged it, both between 00:06 and 00:16 UTC,
in an order this record does not fix. The CloudShell run is the user's; the laptop run is Claude's, in
a laptop session the user started with the procedure the cloud session wrote; the cloud session writes
this entry. The output is quoted verbatim but for one substitution, made nowhere else: Log Archive's
account id, in the bucket's name and the `OWNER` column of the user's paste and already replaced by
`<account-id>` in the laptop session's, becomes **`<Log Archive Account>`** in both. Left out is the
fixed text the script prints on every run: each section's command list and paragraph, and section 8's
key to the checks.*

### In Log Archive's CloudShell

*The user's, in the CloudShell of `<Log Archive Account>` in `us-west-2`, signed in as AWS Control
Tower Admin through `AWSAdministratorAccess`, from a `--depth 1` clone of `main` taken after PR #163
merged. The user printed sections 3 and 8 with `awk` and pasted them in the project thread at 00:16
UTC.*

- **[user] The run**:

  ```
  ~ $ python3 AWS-DataScience/aws/observability.py -
  region: us-west-2
    -  OK
  measuring - (ambient) ...

  wrote aws/output/observability.txt (all checks passed)
  ```

- **[user] Section 3, the trail and its bucket**, excerpt:

  ```
  PROFILE      TRAIL                                BUCKET                                                 KEY PREFIX    ORG TRAIL  HOME       OWNER         READ HERE
  - (ambient)  aws-controltower-BaselineCloudTrail  aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx  o-4z1leiit0c  True       us-west-2  <Log Archive Account>  yes

  BUCKET=aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx
    versioning  : Enabled
    object lock : COMPLIANCE / 90 days
    lifecycle   : RetentionRule Enabled: current 365 d, noncurrent 365 d
    floor       : 90 days
  ```

- **[user] Section 8, the checks**, excerpt:

  ```
  RESULT  ID    WHAT                          DETAIL
  note    OB-4  backup of production/vpn      not measured: awsds-infra-prod is not in this run
  note    OB-4  backup of production/proxy    not measured: awsds-infra-prod is not in this run
  note    OB-4  backup of production/tooling  not measured: awsds-infra-prod is not in this run
  pass    OB-1  log retention in - (ambient)  no group of this project in this account
  pass    OB-2  CloudTrail bucket lifecycle   every enabled rule expires at 90 days or later (RetentionRule Enabled: current 365 d, noncurrent 365 d); Object Lock COMPLIANCE / 90 days
  pass    OB-3  alarm targets in - (ambient)  no alarm in this account
  pass    OB-5  quotas in - (ambient)         every quota under 80%; the highest is Elastic IPs (account), 0 of 5 (0%)

  0 check(s) FAILED.
  ```

### From the laptop

*Claude's, in a laptop session: `./aws/observability.py` with no argument, from a clean worktree of
`origin/main` at `5e99bb9`, 00:13:01 to 00:15:04 UTC (the report's `generated` stamp), through the five
`awsds-infra-*` profiles (`data`, `identity`, `prod`, `sandbox-1`, `staging`), each the infrastructure
user with `InfrastructureAccess`, in `us-west-2`. The session reported in Portuguese, with sections 8
and 9 copied from the report, and the user pasted the report in the thread at 00:23 UTC; its other
readings are given here in English.*

- **[Claude, laptop] The environment at the reading**: the hub stopped (the three `[D]` hosts
  `stopped`), every `[E]` slice down (no interface endpoint in any VPC), no SageMaker job or app running.
- **[Claude, laptop] Section 8, the checks**, excerpt:

  ```
  RESULT  ID    WHAT                                     DETAIL
  note    OB-1  service groups in awsds-infra-sandbox-1  14 groups no slice declares, never expiring, 27.4 MB: the services' own (EXC-10 records Sandbox's), a decision rather than this check.
  note    OB-2  CloudTrail bucket lifecycle              aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx belongs to another account, Log Archive, which no profile here reaches: this check is decided by `python3 aws/observability.py -` in Log Archive's CloudShell, as AWS Control Tower Admin.
  note    OB-3  alarm targets in awsds-infra-prod        3 alarms notifying nobody (awsds-prod-gitlab-status-check, awsds-prod-proxy-status-check, awsds-prod-vpn-health): step 2 is not built, and no alarm measured carries an SNS action.
  note    OB-3  alarm targets in awsds-infra-sandbox-1   2 alarms notifying nobody (awsds-sandbox-warehouse-compute-capacity, awsds-sandbox-warehouse-data-storage): step 2 is not built, and no alarm measured carries an SNS action.
  note    OB-4  backup of production/vpn                 no AWS Backup plan in this account, so step 8.1 is not built: 1 volume uncovered (vol-0b1309dbd9c3cf347 8 GiB gp3); snapshots today: none.
  note    OB-4  backup of production/proxy               no AWS Backup plan in this account, so step 8.1 is not built: 1 volume uncovered (vol-098c1a6c96309bb32 8 GiB gp3); snapshots today: none.
  note    OB-4  backup of production/tooling             no AWS Backup plan in this account, so step 8.1 is not built: 2 volumes uncovered (vol-072c3d3dc9883b104 50 GiB gp3, vol-0b4ad4749eff32daf 12 GiB gp3); snapshots today: vol-072c3d3dc9883b104 by DLM policy-0cd541e97bea1d1c4.
  pass    OB-1  log retention in awsds-infra-data        no group of this project in this account
  pass    OB-1  log retention in awsds-infra-identity    no group of this project in this account
  pass    OB-1  log retention in awsds-infra-prod        every group of this project has a retention, 30 to 365 days (5 groups)
  pass    OB-1  log retention in awsds-infra-sandbox-1   every group of this project has a retention, 30 days (5 groups)
  pass    OB-1  log retention in awsds-infra-staging     every group of this project has a retention, 30 days (1 group)
  pass    OB-3  alarm targets in awsds-infra-data        no alarm in this account
  pass    OB-3  alarm targets in awsds-infra-identity    no alarm in this account
  pass    OB-3  alarm targets in awsds-infra-staging     no alarm in this account
  pass    OB-5  quotas in awsds-infra-data               every quota under 80%; the highest is Elastic IPs (account), 0 of 5 (0%)
  pass    OB-5  quotas in awsds-infra-identity           every quota under 80%; the highest is Elastic IPs (account), 0 of 5 (0%)
  pass    OB-5  quotas in awsds-infra-prod               every quota under 80%; the highest is gateway endpoints (account), 6 of 20 (30%)
  pass    OB-5  quotas in awsds-infra-sandbox-1          every quota under 80%; the highest is gateway endpoints (account), 2 of 20 (10%)
  pass    OB-5  quotas in awsds-infra-staging            every quota under 80%; the highest is gateway endpoints (account), 2 of 20 (10%)

  0 check(s) FAILED.
  ```

- **[Claude, laptop] Section 9**: `None. Every call in this report returned successfully.`
- **[Claude, laptop] Beside the checks.** Production holds no AWS Backup plan, and its resource opt-in
  reads EBS `True` and EC2 `True`. The one snapshot source is the DLM policy `policy-0cd541e97bea1d1c4`
  (`ENABLED`, target tag `awsds:dlm=gitlab-data`), over GitLab's data volume (`/dev/sdf`, 50 GiB); the
  three hosts' root volumes have none. `awsds-prod-proxy-status-check` is in `ALARM` since
  2026-10-16T23:42:56Z with no action, by design: its `treat_missing_data = "breaching"`
  (`terraform-live/production/proxy/main.tf`) keeps a stopped proxy from reading healthy, while
  `awsds-prod-gitlab-status-check` and `awsds-prod-vpn-health` take `notBreaching` and read `OK`. The
  session inferred that once step 2 wires an SNS action on that alarm, every `make hub-down` notifies.

### What the runs settle

- **[Claude] No check failed and no call failed.** The CloudShell run printed `(all checks passed)`,
  which the script prints only when section 9 lists no failed call and section 8 no failed check (the
  exit block of `aws/observability.py`), so it exited 0; the laptop session read exit code 0 and a
  section 9 that lists no failed call.
- **[Claude] `OB-2` passes, and the bucket reads as `INV-14` records it** since Stage 1d step 9
  (2026-08-15): the organization trail `aws-controltower-BaselineCloudTrail`, homed in `us-west-2`,
  writes under the prefix `o-4z1leiit0c` to a bucket with versioning `Enabled`, Object Lock
  `COMPLIANCE` / 90 days and one lifecycle rule, `RetentionRule`, which expires current and noncurrent
  versions at 365 days. The floor the check applies is 90 days, where the lock's retention and step
  3.2's floor meet.
- **[Claude] Every other verdict is the one predicted when the script was written** (PR #163): `OB-1`
  passes in all six accounts, Sandbox's never-expiring service groups a note that repeats `EXC-10`'s
  reading of 2026-10-17 (14 groups, 27.4 MB); `OB-3` is a note for Production's three alarms and
  Sandbox's two, none with an action, and `OB-4` for the four volumes of the three `[D]` hosts, until
  steps 2 and 8 are built (Lesson 50); `OB-5` passes, read with the environment down, so its rows hold
  no interface endpoint and no SageMaker usage.
- **[Claude] These were the instrument's first runs against AWS.** Its readers had met only a
  fabricated `aws` ([`aws/INDEX.md`](../../aws/INDEX.md)); here they parsed real responses from six
  accounts, under CloudShell's `python3` and the laptop's `uv`.

## 2026-10-18 — the `[P]` slices, the quotas and the bill

*Claude, session "Stage 12: observability [P] slices, alarms, quotas, cost", started by the orchestrating
session on the user's authorization of that day, in a worktree of `origin/main` at `2074b1b`, from about 19:50
UTC. Every AWS call ran as the infrastructure user with `InfrastructureAccess`, through the
five `awsds-infra-*` profiles and, for one Cost Explorer read, `awsds-policy-canary`, in `us-west-2` (Cost
Explorer in `us-east-1`). The environment was down throughout: the hub and GitLab stopped, no `[E]` slice
up.*

### Readings

- **[Claude] The estate held no dashboard and five alarms**, Production's three hosts' and Sandbox's two
  warehouse alarms, none with an action; the only topics were `awsds-prod-alerts` and
  `awsds-staging-alerts`, one confirmed subscription each, and Control Tower's `SecurityNotifications`.
- **[Claude] Prices**, the `AmazonCloudWatch` bulk offer for `us-west-2` (published
  2026-10-07T11:55:40Z) and the global `aws-other` one: standard alarm 0.10 and composite alarm 0.50 per
  alarm-month, Contributor Insights rule 0.50 a month plus 0.02 per million matched events, dashboard 3.00
  a month with three free of up to 50 metrics, free tiers of ten alarms, ten custom metrics and 5 GB of
  Logs Insights scans.
- **[Claude] The proxy access log**, Logs Insights over `/awsds/prod/proxy` from 2026-09-01 (3.1 MB
  scanned): September 12,829 requests and 1,597 refused, 66 active hours, ten of them with 50 refusals or
  more, the highest 367 at 2026-09-11 16:00; October 10,919 requests and 53 refused, 54 active hours. The
  most-requested destination in October is `events.gitlab.net`, 4,049 `CONNECT`s from the GitLab host's
  address between 2026-10-12 and 10-16, 17.3 MB sent by the client.
- **[Claude] The usage metrics.** `AWS/Usage` `ResourceCount` carries one metric per SageMaker app and job
  type with data in the 14 days to 2026-10-18 (`studio/JupyterLab-ml.t3.medium` at most 3,
  `processing-job/ml.t3.medium` at most 1, `studio/total_volume_size_in_gb` 368 on 2026-10-15 and 32 now),
  `InterfaceVPCEndpointsPerVPC` per VPC (Sandbox's at most 24) and `VPCsPerRegion` (Production 3 every
  hour). `SERVICE_QUOTA()` answered over each: 30 %, 48 % and 60 % at their peaks. `AWS/Route53Resolver`
  `VpcFirewallQueryVolume` carries the VPC id, and `AWS/Bedrock` the token counts with no dimension.
- **[Claude] The Athena workgroups**: Sandbox holds `primary` and each project's SQL and Spark
  workgroups; the SQL ones publish no metric and set no per-query cutoff, and the account lists no
  `AWS/Athena` metric.
- **[Claude] The SageMaker quotas**, `list-service-quotas` in the five accounts, 2,417 each and 2,324 with
  a usage metric: Sandbox reads 10 for each Studio type in use and for `ml.t3.medium` processing, 20, 8
  and 8 for Stage 17's three types; Production, Staging, Data Governance and Identity read 6, 4 and 0 for
  the same codes. `L-0263D0A3` (Elastic IPs) and `L-1B52E74A` (gateway endpoints) carry no usage metric.
- **[Claude] The bill**, one `get-cost-and-usage` per account by service and usage type, 2026-08-01 to
  10-17, six requests:

  | Account | August | September | October 1-17 |
  |---|---|---|---|
  | Sandbox | 43.81 | 45.55 | 21.50 |
  | Production | 4.11 | 21.31 | 29.19 |
  | Staging | 2.93 | 2.82 | 1.83 |
  | Data Governance | 1.36 | 2.82 | 2.00 |
  | Identity | 0.77 | 1.50 | 1.12 |
  | Policy Canary | 0.33 | 0.47 | 0.50 |
  | **Six accounts** | **53.31** | **74.48** | **56.15** |

  Net equals unblended in every account: no credit reaches these lines. The alarms' line,
  `USW2-CW:AlarmMonitorUsage`, billed 0.00 for 1.61 alarm-months in Production and 0.91 in Sandbox in
  September. The classification by usage type is `cost-model.md`'s.
- **[Claude] IAM**: 147 roles and no user in the five `awsds-infra-*` accounts, 60 of them
  service-linked.
- **[Claude] Hosted zones**: Staging holds `staging.awsds.internal`, billed 0.50 a month.

### Applies

- **[Claude] `production/foundation`, Production**: `awsds-prod-alerts`' policy gained
  `CloudWatchAlarmsOfThisAccount`. Baseline plan `No changes`; plan and apply `0 added, 1 changed, 0
  destroyed`, with `-var-file` on the project folder's `alerts.auto.tfvars`; re-plan `No changes`.
- **[Claude] `production/observability`, Production, new**: the dashboard `awsds-prod-hub`, the metric
  filters `awsds-prod-proxy-requests` and `awsds-prod-proxy-refusals`, the alarms `awsds-prod-proxy-refusals`
  and `awsds-prod-quota-vpcs-per-region`. `5 added, 0 changed, 0 destroyed`; re-plan `No changes`.
- **[Claude] `sandbox/observability`, Sandbox, new**: planned `9 to add, 0 to change, 0 to destroy` (the
  topic `awsds-sandbox-alerts`, its policy and e-mail subscription, the dashboard
  `awsds-sandbox-environment`, five quota alarms). **The apply did not run**: the session's auto-mode
  classifier refused it, and it is the user's.
- **[Claude] Before the applies** every peer session on the laptop was told the three slices and what each
  changes.

### After the applies

- **[Claude] `./aws/observability.py`** over the five profiles, report stamped 2026-10-18T20:30:17Z: the
  two new alarms `resolves`; `OB-3`
  fails in Production for `awsds-prod-gitlab-status-check`, `awsds-prod-proxy-status-check` and
  `awsds-prod-vpn-health` and in Sandbox for the two warehouse alarms, all unwired while one alarm notifies
  (`EXC-19`); `OB-1` passes with Production at 11 groups; `OB-4` notes and `OB-5` passes as at the first
  runs. Exit 2, no call failed.

## 2026-10-18 — `sandbox/observability` applied by the orchestrating session

*The apply is the orchestrating session's ("Execução local no Mac"), from a detached worktree at PR #179's
commit `d22eace`, as the infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`,
with `-var-file` on the project folder's `secrets/alerts.auto.tfvars`. Its result is quoted as that session
reported it to this one. The read-back below is Claude's, in the session "Stage 12: observability [P]
slices, alarms, quotas, cost", read-only, about 20:55 to 20:58 UTC.*

- **[Execução local no Mac] The apply**, 2026-10-18 20:54:20 to 20:54:34Z: *"Apply complete! Resources: 9
  added, 0 changed, 0 destroyed."*; re-plan *"No changes"*; the e-mail subscription `PendingConfirmation`.
  The user's authorization in that session's chat: *"autorizo todas as leituras e applies necessários"*.
  This session's own apply, before 20:30Z, had been refused by its auto-mode classifier and was not
  retried.
- **[Claude] Read back**: the topic `awsds-sandbox-alerts` exists, unencrypted, and
  `list-subscriptions-by-topic` reads one `email` subscription `PendingConfirmation`
  (`get-topic-attributes` still read 0 confirmed and 0 pending at about 20:55Z, and 1 pending by 20:58Z);
  the five `awsds-sandbox-quota-*` alarms carry one action each, four `OK` and
  `awsds-sandbox-quota-processing-ml-t3-medium` `INSUFFICIENT_DATA` with *"Unchecked: Initial alarm
  creation"* at 20:54:31Z; the dashboard `awsds-sandbox-environment` was last modified at 20:54:33Z. A
  re-plan at `d22eace` reads `No changes`.
- **[Claude] `./aws/observability.py`** over the five profiles, report stamped 2026-10-18T20:58:19Z, exit
  2, no call failed: `OB-3` fails in Production for the three `[D]` hosts' alarms, as before; in Sandbox
  for the five quota alarms, whose topic holds *"no confirmed subscription (1 pending)"*, and for the two
  warehouse alarms, still unwired (`EXC-19`). The quota alarms resolve once the user confirms the e-mail.

## 2026-10-18 — the warehouse alarms on the Sandbox topic, and the read that went circular

*Claude, session "Stage 12: observability [P] slices, alarms, quotas, cost", read-only, about 21:20 to
21:30 UTC, after the orchestrating session applied PR #181's `sandbox/warehouse/` (recorded in
[the 5b log](log-stage-05b-redshift-serverless.md), the same day).*

- **[Claude] Read back**: both warehouse alarms carry `awsds-sandbox-alerts` as their one action,
  configuration updated 21:19:26Z; the topic reads 0 confirmed, 1 pending and 1 deleted subscriptions.
- **[Claude] The two Sandbox slices read each other's state** once PR #181 merged: `sandbox/warehouse/`
  reads this stage's `alerts_topic_arn`, and `sandbox/observability/` read `sandbox/warehouse/`'s
  `namespace_name`, so an account holding neither (a Stage 14 unit, a rebuild) could plan neither first.
  `sandbox/observability/` now builds the name as `sandbox/warehouse/data.tf` does,
  `awsds-${var.env}-warehouse`, and reads no warehouse state. Code only: its re-plan reads `No changes`.

## 2026-10-19 — the Sandbox alerts subscription confirmed, and `OB-3` passing in Sandbox

*The user confirmed the subscription; Claude read it back, the orchestrating session of 2026-10-18's
third round, from the laptop as the infrastructure user (`awsds-infra-sandbox-1`, `InfrastructureAccess`
in `Sandbox Account 1`, and the other `awsds-infra-*` profiles), read-only, at 02:51 UTC.*

- **[user] The confirmation**: the e-mail subscription of `awsds-sandbox-alerts`, created by the slice's
  apply on 2026-10-18, confirmed from the link in AWS's message; the page read *"Subscription confirmed!"*.
- **[Claude] Read back**: `get-topic-attributes` reads 1 confirmed, 0 pending, 0 deleted, and
  `list-subscriptions-by-topic` one `email` subscription with an ARN, no longer `PendingConfirmation`.
- **[Claude] `./aws/observability.py`, 02:51:56Z, exit 2**: `OB-3` `pass` in Sandbox, *"every alarm
  notifies a topic that resolves (7 alarms)"*, the five quota alarms and the two warehouse alarms; `fail`
  in Production on the three `[D]` hosts' alarms alone, `EXC-19`'s remaining half; `OB-1` and `OB-5`
  `pass` in every account, `OB-2` and `OB-4` the notes of 2026-10-18.
