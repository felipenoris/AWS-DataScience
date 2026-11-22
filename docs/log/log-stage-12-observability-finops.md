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

## 2026-10-20 — step 6.1's Config reading of 2026-10-14 (PR #126), recorded and re-read

*Two Claude sessions. The reading of 2026-10-14 is the session that opened PR #126 (merged
2026-10-14T17:19:05Z), which wrote no log entry; its bullets are taken from that PR's body and the
`docs/PRICING.md` §2 paragraph it added. Its calls, as the body names them, were reads: Cost Explorer,
CloudWatch `AWS/Config`, CloudTrail `lookup-events` and `describe-configuration-recorders`, as the
infrastructure user with `InfrastructureAccess` and, on Policy Canary, `AWSAdministratorAccess`. The
re-read is Claude's, in the session the orchestrating session started on 2026-10-20 for Stage 12's log,
at the user's request in its chat: read-only, from the laptop, 22:58:53 to 23:00:47 UTC, through the five
`awsds-infra-*` profiles and `awsds-policy-canary`, the same identities, Cost Explorer in `us-east-1` and
the rest in `us-west-2`.*

### The reading of 2026-10-14

- **[Claude, PR #126] Cost Explorer**, AWS Config by usage type in the six accounts with a CLI profile:
  `USW2-ConfigurationItemRecorded` is the only usage type, and no rule evaluation is billed.

  | Account | August | September | October 1-13 |
  |---|---|---|---|
  | Sandbox | 6.32 | 7.27 | 3.02 |
  | Production | 1.10 | 3.13 | 1.90 |
  | Staging | 1.31 | 0.33 | 0.26 |
  | Data Governance | 0.41 | 0.11 | 0.28 |
  | Identity | 0.25 | 0.02 | 0.17 |
  | Policy Canary | 0.23 | 0.02 | 0.15 |

  September is 10.88 in all. Log Archive and Audit hold no profile and are unread.
- **[Claude, PR #126] The recorders**: each is `aws-controltower-BaselineConfigRecorder`, `CONTINUOUS`,
  all supported types, no exclusion.
- **[Claude, PR #126] Sandbox's items from 2026-09-14 to 10-13**, CloudWatch `ConfigurationItemsRecorded`
  by `ResourceType`: 1,816, of which 1,487 fall inside the eight `sandbox/egress` cycles that CloudTrail's
  `CreateVpcEndpoint` and `DeleteVpcEndpoints` bound. A cycle records 120-290 items (USD 0.36-0.87)
  whatever its length; a day without a session records 0-4. `AWS::EC2::NetworkInterface` 510,
  `AWS::EC2::VPCEndpoint` 331, `AWS::EC2::SecurityGroup` 176, `AWS::EC2::Subnet` 157 and `AWS::EC2::VPC`
  123 make 71% of the window, with `AWS::Config::ResourceCompliance` 279 beside them. Production recorded
  742 in the same window (`ResourceCompliance` 172, ENI 148, endpoint 138, instance 76).

### The re-read of 2026-10-20

- **[Claude] Cost Explorer**, six `get-cost-and-usage` requests over 2026-08-01 to 2026-10-14, the AWS
  Config service grouped by usage type: every figure of the table to the cent, net equal to unblended in
  each account. Unrounded, September is 10.866 USD for 3,622 items: the 10.88 above adds the rounded
  figures, and step 6.1's 10.87 of 2026-10-18 rounds the sum.
- **[Claude] CloudWatch**, `get-metric-data` daily sums from 2026-09-14T00:00Z to 10-14T00:00Z: Sandbox's
  `ResourceType` `All` is 1,816 and Production's 742, and every type above reads its figure.
- **[Claude] CloudTrail**, `lookup-events` in Sandbox over the same window: the eight cycles run from
  2026-09-14 13:15 to 2026-10-12 00:11 UTC. Sandbox's hourly `All`, summed from the hour of a cycle's
  first `CreateVpcEndpoint` to the hour after its last `DeleteVpcEndpoints`, gives 1,487, and 120 to 290
  a cycle; the other 329 items fall outside the cycles. The window holds 228 `CreateVpcEndpoint` and 181
  `DeleteVpcEndpoints` events: 65 and 17 of them refused with `Client.RequestLimitExceeded` under
  `InfrastructureAccess`, and 8 of each by `AWSServiceRoleForRedshift`, whose creates name a `vpce-svc-`
  endpoint service, so the event count is not the endpoint count.

## 2026-10-21 — step 5.2's layer letters, read against the bill on 2026-10-20 (PR #211), recorded

*Claude's sitting, no AWS call: the session that opened PR #211 (merged 2026-10-20T21:50:35Z) read the
bill's usage types in [`cost-model.md`](../plan/cost-model.md) at [`PRICING.md`](../PRICING.md)'s rates.
It wrote no entry, under the rule of that day; this one is written on 2026-10-21 from the PR's body and
diff, with no AWS call either.*

- **[Claude] 5.2, for open question 4: the bill moves no letter.** The reading uses 5.1's usage-type half
  alone, since the split by tag waits on 4.1, and its arithmetic is the step's table. Decision due 3 is
  written, recommending (a), every letter kept; the choice is the user's.
- **[Claude] [`institutional-delta.md`](../plan/institutional-delta.md)**, in the same PR: the lab column
  of the Networking, Egress control, Egress cost, Backups and Availability rows describes what is built,
  from D38, `NETWORK.md`, the bill and `OB-4`'s reading of no backup plan. The VPN row makes the WireGuard
  host the single point of failure for private-network access and leaves egress's to the proxy (the
  Availability row).

## 2026-10-22 — step 8.5, the internal CA root's rotation, written

*Claude, in the session `stages-7-8-pending` (branch `claude/stages-7-8-pending-03936d`), no AWS call:
the plan revised from a review of Stages 7 and 8, on the user's request to correct what the review found.*

- **[Claude] 8.5**: D36 §6 schedules the root's rotation, rehearsed once with its time recorded, at this
  stage, and this file carried nothing for it. The step names the surfaces a new root rebuilds and leaves
  its procedure to be written with it.

## 2026-11-05 — the `EC2 - Other` line by usage type, in every account with a profile

*Claude, read-only, in the session `ec2-other-daily-charge` (branch
`claude/ec2-other-daily-charge-8b47ca`), as the infrastructure user: `InfrastructureAccess` through the
`awsds-infra-*` profiles and `AWSAdministratorAccess` through `awsds-policy-canary`. Written 2026-11-09
from the session's readings. No account id appears below.*

- **[Claude] Cost Explorer**, one `get-cost-and-usage` per account (six requests, 0.06 USD): service
  `EC2 - Other`, daily, 2026-10-20 to 2026-11-04, by usage type. Production carries the line, 3.58 USD
  over the window: `USW2-EBS:VolumeUsage.gp3` at 0.2013 USD a day in October and 0.2080 from 2026-11-01
  (2.5161 and 2.6000 GB-month a day, 78 GiB over a 31-day and a 30-day month), and
  `USW2-EBS:SnapshotUsage` at 0.0049 to 0.0053 a day. Sandbox read 0.0128 on 2026-10-30 alone; Staging,
  Data Governance, Identity and `Policy Canary` read nothing.
- **[Claude] The objects behind it**, `describe-volumes`, `-instances` and `-snapshots` in Production:
  four `gp3` volumes, 78 GiB: `vol-0e0fff3694f95fa63` (50 GiB, `awsds-prod-gitlab-data`),
  `vol-0023e899ae8e330b3` (12 GiB, GitLab's root), `vol-0b1309dbd9c3cf347` and `vol-098c1a6c96309bb32`
  (8 GiB each, the VPN and proxy roots), the three hosts `stopped`; 78 × 0.08 / 30 = 0.208 USD a day, the
  bill's figure. The other five accounts hold no volume. Fourteen snapshots: seven of
  `vol-0e0fff3694f95fa63` under `policy-0776691c894780872` (7 kept) and seven of
  `vol-072c3d3dc9883b104`, 2026-10-19 to 10-25, whose policy `policy-0cd541e97bea1d1c4` answers
  `ResourceNotFoundException`, so no policy retires them.

## 2026-11-09 — step 5.3 written: GitLab's data volume read from its snapshots, and the plans of a smaller one

*Claude, read-only, the same session, after the user asked for the shrink to be prepared; the plans as the
infrastructure user (`InfrastructureAccess`, `awsds-infra-prod`), Terraform 1.16.6 and provider
`hashicorp/aws` 6.68.0, from the worktree. No account id appears below.*

- **[Claude] What measures the volume's use with the host stopped**: no `df` of it is recorded, and
  Production publishes no `CWAgent` metric.
- **[Claude] EBS direct API**, `aws ebs list-snapshot-blocks`, one call per snapshot: 2,467 blocks of
  512 KiB in `snap-00ad2f1f217e591eb` (2026-11-09 03:46 UTC) and in `snap-0e3a3c197eaf4208b` (2026-11-03),
  1.20 GiB of the 50 GiB, 2.4%. The volume is XFS mounted without `discard` (`user-data.sh.tftpl`), so a
  freed block still counts. The newest object in `awsds-prod-gitlab-backup` is the archive of 2026-10-26
  22:15:11 UTC, 14,356,480 bytes.
- **[Claude] `production/tooling/` planned**, each plan with `-var-file` naming the project folder's
  `secrets/saml.auto.tfvars`, nothing applied: as deployed, `No changes. Your infrastructure matches the
  configuration.`; with `-var data_volume_size=20`, `aws_ebs_volume.data will be updated in-place`,
  `size = 50 -> 20`, `Plan: 0 to add, 1 to change, 0 to destroy.`, a decrease AWS's page rules out;
  `plan -destroy`, `Plan: 0 to add, 0 to change, 17 to destroy.`, the set of Stage 7 step 8.2's
  rehearsal.
- **[Claude] Price List Query API**: EBS direct APIs' `List` at 0.0006 USD per 1,000 requests in
  `us-west-2` and 0.0011 in `sa-east-1` (`docs/PRICING.md` §8).
- **[Claude] Step 5.3 written**, with `runbooks/gitlab.md` §B's paragraph on a smaller volume; the sitting
  waits on the user (`waiting-on-the-user.md`).

## 2026-11-10 — step 5.3's sitting: GitLab's data volume destroyed, re-applied at 20 GiB and restored

*Claude and the user, the same session, the applies on the user's authorization in its chat for this
sitting: Claude's plans, applies and reads as the infrastructure user (`InfrastructureAccess`,
`awsds-infra-prod`), Terraform 1.16.6 and provider `hashicorp/aws` 6.68.0, from the worktree; the user's
acts in a Session Manager shell on the host. Times UTC. No account id appears below.*

- **[Claude] The other sessions told before any write**: the Stage 19 session, which held its
  `make hub-down` until the sitting's end, and the session that wrote `docs/AWS_SUPPLEMENT.md`.
- **[user] `make gitlab-up RUNNERS=0`**, the hub already up for the Stage 19 session.
- **[user] The reading before**: `/dev/nvme1n1     50G  1.1G   49G   3% /var/opt/gitlab`, and through
  `gitlab-rails runner` `{:projects=>6, :groups=>5, :users=>6, :runners=>3,
  :main=>"8d50f6851af08f394e18ac17099a4e5db68b3fc4", :tags=>14, :usage_ping=>false, :version_check=>false,
  :auto_devops=>false}`.
- **[user] The backup**, `gitlab-backup create STRATEGY=copy`: `2026-11-10 01:51:48 UTC -- Dumping
  PostgreSQL database gitlabhq_production ...` to `2026-11-10 01:51:58 UTC -- Backup
  1794275508_2026_11_10_19.4.2 is done.`, then `Deleting old backups ... done. (2 removed)`.
- **[Claude] The gate**: the archive `1794275508_2026_11_10_19.4.2_gitlab_backup.tar` in
  `awsds-prod-gitlab-backup`, 14,346,240 bytes, written 01:51:59; `./aws/supplychain.py`'s `SC-13` reading
  it `made by 19.4.2`, equal to `gitlab_ce_version`.
- **[Claude] `data_volume_size`'s default to 20** and the slice's three texts that named 50 GiB, committed
  and pushed before the plans (PR #285).
- **[Claude] The destroy**: `plan -destroy`, `Plan: 0 to add, 0 to change, 17 to destroy.`; its apply from
  01:55:28 to 01:56:56, `Apply complete! Resources: 0 added, 0 changed, 17 destroyed.`, the old host
  `i-0b4cb5f62e65abf70` terminated at 01:55:39.
- **[Claude] The re-apply**: `Plan: 17 to add, 0 to change, 0 to destroy.` with `aws_ebs_volume.data` at
  `size = 20`; its apply from 01:57:30 to 01:58:28, `Apply complete! Resources: 17 added, 0 changed, 0
  destroyed.`: the host `i-010c8217a1b3062dc` at `10.30.6.245`, the volume `vol-0f6fa0f0ae07f7064`, the DLM
  policy `policy-029a3e7e9dd6426be`.
- **[Claude] The first boot**, the host launched at 01:57:50: on the serial console, `gitlab Reconfigured!`
  at 513.86 s of uptime and the readiness probe `200` at 539.97 s; Session Manager `Online` at 02:07:17,
  `gitlab.awsds.internal` resolving to `10.30.6.245` on the laptop, the sign-in page `200` in 2.94 s.
- **[user] The boot log**, `/var/log/awsds-gitlab-boot.log`, the console's 64 KB window having scrolled
  past its markers: `mounted: /dev/nvme1n1 xfs    19.9G`, `gitlab-ce-19.4.2-ce.0.amazon2023.aarch64`,
  `restored from Secrets Manager`, `=== awsds gitlab first boot done: 2026-11-10T02:06:56+00:00 ===`.
- **[user] The restore**, `runbooks/gitlab.md` §B steps 1-3: the archive fetched from the bucket;
  `ok: down: puma: 0s, normally up` and `ok: down: sidekiq: 0s, normally up`; `2026-11-10 02:14:35 UTC --
  Unpacking backup ... done`, the database from 02:14:46 to `2026-11-10 02:15:33 UTC -- Restoring database
  ... done`, with six `ERROR:  must be owner of extension` lines (`pg_trgm`, `btree_gist` and `amcheck`,
  each twice) and `Source backup for the database ci doesn't exist. Skipping the task`; the repositories
  `done` at 02:15:35; `2026-11-10 02:15:51 UTC -- Restore task is done.`
- **[user] `gitlab-ctl reconfigure`**: `Infra Phase complete, 1/779 resources updated in 16 seconds`,
  `Cinc Client Run complete in 15.650629343 seconds` at 02:16:38, `gitlab Reconfigured!`, and three
  deprecations: `nginx['ssl_certificate'] has been deprecated. Please use
  gitlab_rails['nginx']['ssl_certificate'] instead.`, `nginx['ssl_certificate_key'] has been deprecated.
  Please use gitlab_rails['nginx']['ssl_certificate_key'] instead.` and `pages_nginx has been deprecated.
  Please use gitlab_pages['nginx'] instead.`
- **[user] `gitlab-ctl restart`** (`ok: run: puma: (pid 8328) 0s`, `ok: run: sidekiq: (pid 8343) 1s`), then
  `gitlab:check SANITIZE=true` straight after: `Internal API available: FAILED - Internal API unreachable`
  and `Sidekiq: ... Running? ... no`; the rest `OK` or `yes`, `All migrations up? ... yes`, the six
  projects with their namespaces, `Active users: ... 5` and `All projects are in hashed storage? ... yes`
  among them.
- **[user] `gitlab:doctor:secrets`**, 02:19:16 to 02:19:29: every model `failures: 0`, `Total: 0 row(s)
  affected`.
- **[user] The reading after**: `/dev/nvme1n1     20G  925M   20G   5% /var/opt/gitlab`, and the runner line
  identical to the one before.
- **[Claude] The sign-in page from the laptop**: `200` at 02:25:51 (2.89 s) and 02:36:37 (1.06 s).
- **[user] The two checks again**, puma and Sidekiq up 1,817 s: `Internal API available: OK`,
  `Redis available via internal API: OK`, `gitlab-shell self-check successful`,
  `Sidekiq: ... Running? ... yes`, `Number of Sidekiq processes (cluster/worker) ... 1/1`.
- **[Claude] The times** from the destroy's start at 01:55:28: the first boot done at 11 min 28 s, the
  restore's task at 20 min 23 s, `doctor:secrets` at 24 min 01 s. Stage 7 8.2's 24 min 16 s ran to the
  restored sign-in page, which this sitting did not time.
- **[Claude] The snapshots and the backup's expiry**: seven snapshots of `vol-072c3d3dc9883b104`
  (2026-10-19 to 10-25) and seven of `vol-0e0fff3694f95fa63` (2026-11-03 to 11-09), none yet of
  `vol-0f6fa0f0ae07f7064`; the bucket's rule `expire-current-versions` at 30 days, so the new archive
  leaves on 2026-12-11, the bucket holding six archives, 2026-10-13 to 2026-11-10.
- **[user] `make gitlab-down`**: the host `stopped` at 02:49:05. **[Claude]** At 02:53:49 the last two of
  SharedServices' interface endpoints read `deleting` and no runner instance exists. The hub stays up for
  the Stage 19 session.
- **[Claude] The texts that state the volume or price it**, in PR #285: item 11's list, and
  `docs/PRICING.md` §2 and §4, `runbooks/promotion.md`'s GitLab address and `runbooks/gitlab.md` §P, which
  item 11 missed; `docs/AWS_SUPPLEMENT.md`'s `SUP-314` takes the 2026-11-09 plan reading.

## 2026-11-10 — the reconfigure's NGINX deprecations: the template on GitLab 19.2's keys, planned

*Claude, the same session, at the user's request, read-only: GitLab's documentation and the omnibus
source read through web-fetch subagents, and `production/tooling/` planned at 03:08 UTC as the
infrastructure user (`InfrastructureAccess`, `awsds-infra-prod`), Terraform 1.16.6 and provider
`hashicorp/aws` 6.68.0, from the worktree. Nothing applied. No account id appears below.*

- **[Claude] GitLab's documentation**: `docs.gitlab.com/omnibus/settings/nginx/` and `.../ssl/`, both
  stating 19.2, put the GitLab vhost's settings under `gitlab_rails['nginx']` since 19.2, carry legacy
  `nginx[...]` vhost keys forward with a warning, an explicit new key winning, and give each service's
  vhost its own key (`gitlab_pages['nginx']`, `registry['nginx']`, `gitlab_kas['nginx']`); neither states
  a removal version. `docs.gitlab.com/administration/pages/` still documents `pages_nginx[...]`, and
  `docs.gitlab.com/update/deprecations/` has no entry for either.
- **[Claude] The omnibus source** at `master` (19.5.3): `nginx/libraries/nginx.rb`'s
  `translate_service_nginx_settings` prints the `pages_nginx` line and copies every key, `enable`
  included, to `gitlab_pages['nginx']` where the new key is unset; `gitlab/libraries/gitlab_rails.rb`'s
  `translate_client_settings` prints the `nginx['<key>']` line and copies to `gitlab_rails['nginx']`.
  `package/libraries/deprecations.rb`, the list that carries removal versions, holds none of the three.
- **[Claude] The template**: `gitlab_rails['nginx']['ssl_certificate']` and `['ssl_certificate_key']`,
  `gitlab_pages['nginx']['enable']`, `['ssl_certificate']` and `['ssl_certificate_key']`, the paths
  unchanged.
- **[Claude] `production/tooling/` planned** with `-var-file` naming the project folder's
  `secrets/saml.auto.tfvars`: `aws_s3_object.gitlab_rb will be updated in-place`, the five lines replaced
  and nothing else in the file, `Plan: 0 to add, 1 to change, 0 to destroy.` The data volume reads no
  change at 20 GiB. The apply and `awsds-gitlab-refresh` wait for the next GitLab session
  (`waiting-on-the-user.md`).

## 2026-11-10 — the NGINX keys applied and refreshed, the orphan snapshots deleted

*Claude and the user, the same session after PR #285's merge (`2d63dacc`, 03:29:08 UTC). Claude's AWS
calls ran as the infrastructure user in Production (`InfrastructureAccess`, `awsds-infra-prod`),
Terraform 1.16.6 and provider `hashicorp/aws` 6.68.0, from a worktree of `main`'s tree; the apply and
the deletion on the user's go-ahead in the session. The host's commands were the user's, in a Session
Manager shell. No account id appears below.*

- **[Claude] `production/tooling/` planned** at 03:42 UTC with `-var-file` naming the project folder's
  `secrets/saml.auto.tfvars`: `aws_s3_object.gitlab_rb will be updated in-place`, `Plan: 0 to add, 1 to
  change, 0 to destroy.` **Applied** from the saved plan, 03:42:59 to 03:43:10: `Modifications complete
  after 2s [id=awsds-prod-gitlab-objects/config/gitlab.rb]`, `Apply complete! Resources: 0 added, 1
  changed, 0 destroyed.`
- **[user] `make gitlab-up`**: the host started at 03:47:13 (its `LaunchTime`).
- **[user] The refresh and the reading**, from the shell:

  ```text
  sh-5.2$ sudo awsds-gitlab-refresh > /tmp/refresh.log 2>&1; echo "exit: $?"
  grep -n "deprecated" /tmp/refresh.log
  tail -3 /tmp/refresh.log
  sudo grep -rH 'ssl_certificate' /var/opt/gitlab/nginx/conf/
  exit: 0
  540:  * ruby_block[check_postgresql_version_is_deprecated] action run (skipped due to not_if)
  [2026-11-10T03:55:32+00:00] INFO: Report handlers complete
  Infra Phase complete, 5/782 resources updated in 19 seconds
  gitlab Reconfigured!
  /var/opt/gitlab/nginx/conf/service_conf/gitlab-rails.conf:  ssl_certificate /etc/gitlab/ssl/gitlab.awsds.internal.crt;
  /var/opt/gitlab/nginx/conf/service_conf/gitlab-rails.conf:  ssl_certificate_key /etc/gitlab/ssl/gitlab.awsds.internal.key;
  /var/opt/gitlab/nginx/conf/service_conf/gitlab-pages.conf:  ssl_certificate /etc/gitlab/ssl/awsds-pages.internal.crt;
  /var/opt/gitlab/nginx/conf/service_conf/gitlab-pages.conf:  ssl_certificate_key /etc/gitlab/ssl/awsds-pages.internal.key;
  ```

  **[Claude]** The one line matching `deprecated` names a skipped resource: no `has been deprecated` line
  printed. Each vhost's file under `service_conf/` names its own certificate.
- **[Claude] From the laptop, the tunnel up**: at 03:56:16, 44 s after the reconfigure's end, the sign-in
  page and `app-etl`'s Pages site both answered `502`. At 03:58:34 `openssl s_client` read
  `subject= /O=AWS-DataScience/CN=gitlab.awsds.internal` (SAN `DNS:gitlab.awsds.internal`) and, from
  `app-etl-ffa1fa.awsds-pages.internal`, `subject= /O=AWS-DataScience/CN=*.awsds-pages.internal` (SAN
  `DNS:*.awsds-pages.internal, DNS:awsds-pages.internal`), both `issuer= /O=AWS-DataScience/CN=awsds
  internal root CA` and `notAfter=Oct 22 06:35:12 2027 GMT`; the sign-in page answered `200` (2.72 s) and
  the site still `502`. From 03:59:00 the site answered `302` to `https://projects.awsds-pages.internal/auth`,
  and at 03:59:28, verified against the laptop's trust store, `gitlab sign-in: http=200 ssl_verify=0` and
  `pages: http=302 ssl_verify=0`.
- **[Claude] The new volume's first snapshot**: `snap-0fdbe96fbb0cd8be7`, 20 GiB, of
  `vol-0f6fa0f0ae07f7064` under `policy-029a3e7e9dd6426be`, started 03:59:02 and read `completed` at
  04:00:43.
- **[Claude] The fourteen snapshots no policy retires, deleted** (5.3 item 12, the user's decision). Re-read
  at 04:01:36: seven of `vol-072c3d3dc9883b104` under `policy-0cd541e97bea1d1c4` (2026-10-19 to 10-25)
  and seven of `vol-0e0fff3694f95fa63` under `policy-0776691c894780872` (2026-11-03 to 11-09), 50 GiB
  each, neither volume nor policy left; the account owned no AMI and held no Recycle Bin rule for EBS
  snapshots, so the deletion is final. `ec2 delete-snapshot` from 04:02:07 to 04:02:25, fourteen `rc=0`;
  the account then owned one snapshot, `snap-0fdbe96fbb0cd8be7`.
- **[user] `make gitlab-down`**: the host `stopped`, CloudTrail's `StopInstances` at 04:01:26 by the
  infrastructure user. **[Claude]** At 04:06:10 no interface endpoint was left in the SharedServices VPC,
  and at 04:06:37 none in Production; the hub's two hosts kept running for the Stage 19 session, told
  at 04:06.

## 2026-11-17 — decision due 1 taken on a card, with no AWS call

*Claude's sitting in a cloud session of the user's Claude project, no AWS call: the review of the plan's
open decisions the user asked for at 22:01 UTC, one card per decision under the user's default of
21:50 UTC (the path AWS suggests), recorded by pull request #317. Times are UTC.*

- **[user] Decision due 1**, at 22:52, on the card *"Que ação dar ao alarme de status do proxy, que
  dispara a cada hub-down?"*: *"Dados ausentes como OK"*, (b). `treat_missing_data` becomes
  `notBreaching` in 2.2's `[D]` apply of `production/proxy/`, in the hub sitting, with the alarm's action.
- **[Claude] 6e decision 6**, taken at 23:45 (that stage's log), reaches 2.1 and decision due 2: the
  budget's notification and Cost Anomaly Detection are the user's acts, and the ceiling stays decision
  due 2's.

## 2026-11-21 — 9.1 read with the environment up, and 2.2's `[D]` half written and planned against the live hub

*Claude, session "Stage 12: hub alarms and 9.1", started by the orchestrating session at the user's
request, in a worktree of `origin/main` at `b3b900b4`, from about 20:11 UTC. Every AWS call ran as the
infrastructure user with `InfrastructureAccess`, through the five `awsds-infra-*` profiles, in
`us-west-2`; none wrote, none reached Bedrock, and no plan file was kept. The environment was up for
`runbooks/promotion.md` §N.9's day 2, held by another session: both hub hosts running, Sandbox's
`egress/` with `GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent` and its `probes/`; GitLab stopped,
Staging's and Production's `egress/` and both warehouses down.*

### Readings

- **[Claude] `make status`**, about 20:15: `production/vpn` and `production/proxy` up, `sandbox/egress` up
  with 33 resources, `sandbox/probes` with 4, `production/tooling` stopped, every other `[E]` slice down;
  estimated burn 0.3590 USD/h.
- **[Claude] `./aws/observability.py`** over the five profiles, report stamped 2026-11-21T20:21:16Z: exit 2,
  no call failed. `OB-5` passes in every account; every quota reads its applied value, and each code's
  name reads back as its quota (`L-0263D0A3` *EC2-VPC Elastic IPs*, `L-29B6F2EB` *Interface VPC endpoints
  per VPC*, `L-1B52E74A` *Gateway VPC endpoints per Region*):

  | Account | Elastic IPs | Interface endpoints per VPC | Gateway endpoints | Hosted zones |
  |---|---|---|---|---|
  | Production | 1 of 5 | 0 of 50 in each of its three VPCs | 6 of 20 | 3 of 500 |
  | Sandbox | 0 of 5 | 24 of 50 (48 %) | 2 of 20 | 1 of 500 |
  | Staging | 0 of 5 | 0 of 50 | 2 of 20 | 1 of 500 |
  | Data Governance | 0 of 5 | 0 of 50 | 2 of 20 | 0 of 500 |
  | Identity | 0 of 5 | no VPC | 0 of 20 | 0 of 500 |

  SageMaker: one Code Editor app on `ml.t3.large` (`L-656A17FA`) and one JupyterLab on `ml.t3.medium`
  (`L-71FAF417`) in Sandbox, 1 of 10 each; no job or endpoint in any account. `OB-3` fails in Production
  for exactly `awsds-prod-gitlab-status-check`, `awsds-prod-proxy-status-check` and `awsds-prod-vpn-health`
  (`EXC-19`), all three `OK`, the proxy's with the hub running; Production's other four alarms, the
  refusals, the VPCs-per-Region quota and the two warehouse alarms, resolve to `awsds-prod-alerts` (one
  confirmed subscription), and Sandbox's seven resolve. `OB-1` passes, Production at 16 groups (30 to 365
  days); `OB-2` and `OB-4` note as before.
- **[Claude] The endpoint usage metric**, `AWS/Usage` `ResourceCount` `InterfaceVPCEndpointsPerVPC` on
  Sandbox's VPC, hourly maximum from 2026-11-07 to 2026-11-21T21:00Z: 15 datapoints, 19 in every session
  hour from 2026-11-10 to 2026-11-21T07:00Z and 24 at 19:00 and 20:00 on 2026-11-21, `SERVICE_QUOTA()` 50
  throughout. No datapoint is published for an hour with no endpoint.
- **[Claude] The 24 endpoints**, by `terraform output interface_endpoint_ids` on `sandbox/egress`: the 18
  of the base set, `airflow-serverless` (`mwaa`), `sagemaker.mlflow` (`mlflow`), `bedrock` and
  `bedrock-runtime` (`bedrock-base`), `bedrock-agent` and `bedrock-agent-runtime` (`bedrock-agent`).
  Counted from `vpc-egress-v0.19.0`'s `endpoints.tf`, every optional group adds `emr`'s seven and
  `redshift`'s one: 32, 64 % of the quota, under `awsds-sandbox-quota-interface-endpoints-per-vpc`'s 80 %.
- **[Claude] The hub hosts**, `describe-instances`: `awsds-prod-vpn` `i-011ffd7b6dde40a9a`, private
  `10.31.160.22`, Elastic IP `52.89.212.1`, on `ami-0bea529386a62a2ad` (`al2023-ami-2023.12.20260831.0`);
  `awsds-prod-proxy` still `i-0d42d0393c39eefdb`, the instance 6g decision 1 applied on 2026-09-17, private
  `10.31.160.140`, public `44.255.111.239` this run, on `ami-0e8ee1bc880594d50`
  (`al2023-ami-2023.12.20260917.1`); both started at 19:46. The parameter
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64` resolves to
  `ami-09f6e62a9fe578f92` (`al2023-ami-2023.12.20261120.0`), modified 2026-11-20T16:28:29Z.

### The code

- **[Claude] `terraform-modules/wireguard`**: an `alarm_actions` input, empty by default, on the health
  alarm, whose description no longer says no topic exists. Commit `ed563388` alone, then
  `wireguard-v0.7.0`, the next version after `wireguard-v0.6.0` on `git ls-remote --tags origin` at
  20:25, pushed with the branch and read back from origin on the same hash. `user-data.sh.tftpl` is
  untouched by it; against `wireguard-v0.6.0` the template differs in comment lines alone.
- **[Claude] `production/vpn/`** pins `wireguard-v0.7.0` and passes `production/foundation/`'s
  `alerts_topic_arn`.
- **[Claude] `production/proxy/`**: the status-check alarm takes `notBreaching` (decision due 1 (b)), the
  alerts topic and a description naming `./aws/proxy.py`.
- **[Claude] `production/tooling/`**: GitLab's alarm takes the alerts topic and a description naming
  `runbooks/gitlab.md` §U, §B and §V.
- **[Claude] `production/observability/`**: the hub dashboard's text says the three hosts' alarms read
  `OK` while stopped and notify the topic.

### The plans against the live hub

*Each with `-input=false` as `awsds-infra-prod`, its output read in full.*

- **[Claude] `production/proxy/`**, 20:21:09: `1 to add, 2 to change, 1 to destroy`. `aws_instance.this`
  is replaced on `ami`, masked (`SUP-312`), and on `user_data`, whose one difference is the first-render
  comment 6g decision 1 corrected after its apply (three lines out, two in). The alarm changes in place:
  `alarm_actions` gains `awsds-prod-alerts`, `treat_missing_data` `breaching` → `notBreaching`, the
  description, and `InstanceId` known after apply. `proxy.awsds.internal` changes in place from
  `10.31.160.140`; the reconfigure association does not change.
- **[Claude] `production/vpn/`**, with the module's local path (Recipe B step 1) at 20:24:30 and from
  `wireguard-v0.7.0` at 20:27:27, the two outputs identical: `2 to add, 3 to change, 2 to destroy`.
  `module.wireguard.aws_instance.this` is replaced on `ami` and on `user_data`, 65 changed lines, every one
  a comment; `aws_eip_association.this` is replaced with it, `52.89.212.1` moving to the new instance. In
  place: the alarm (`alarm_actions`, the description, `InstanceId`), `aws_route.tunnel_return` onto the new
  interface, and `vpn.awsds.internal` from `10.31.160.22`.
- **[Claude] `production/tooling/`**, 20:28:07, with `-var-file` on the project folder's
  `saml.auto.tfvars`, GitLab stopped: `0 to add, 1 to change, 0 to destroy`, the alarm alone
  (`alarm_actions`, the description). The instance plans nothing, its `ami` and `user_data` held by
  `ignore_changes`.
- **[Claude] `production/observability/`**, 20:28:36: `0 to add, 1 to change, 0 to destroy`, the dashboard's
  markdown alone.
- **[Claude] What the applies do to a session**: the proxy's replaces the estate's only internet exit, and
  the new host takes a new private and public address that the record follows; the tunnel's replaces the
  endpoint every client pins, whose Elastic IP and host key carry over, so no `.conf` changes. Neither runs
  while a spoke session needs the proxy or the tunnel; the hub sitting takes the tunnel down on the
  operator's device first (`runbooks/vpn.md` §K6) and plans again.

## 2026-11-21 — the hub sitting's pre-flight against the live hub, and `CreationTime` read against `CreateApp`

*Claude, a session the orchestrating session started at the user's request of 21:00 UTC to advance what
the running environment allows, in the worktree `hub-applies-proxy-vpn` on `claude/hub-applies-proxy-vpn`,
cut from `origin/main` at `4053faee`, from about 21:10 UTC. Every AWS call ran as the infrastructure user
with `InfrastructureAccess` in `us-west-2`, read-only: `awsds-infra-prod`, `awsds-infra-sandbox-1`, and
`make status`'s five profiles. No apply, no `--on-host`, no plan file kept. The environment was §N.9's day
2, held by another session: both hub hosts running since 19:46, Sandbox's `egress/` with four groups and
its `probes/`, the spaces `jup` and `code` in `d-m8m0uefej9kb`.*

### Readings

- **[Claude] `make status`**, 21:12:56 to 21:15:37: `production/vpn` and `production/proxy` up, one
  instance each, `sandbox/egress` up with 33 resources and `sandbox/probes` with 4, `production/tooling`
  stopped, every other `[E]` slice down; `studio/sandbox/jup` (JupyterLab, `ml.t3.medium`) since 20:07 and
  `studio/sandbox/code` (CodeEditor, `ml.t3.large`) *"about 1.74 USD so far since 2026-11-21 03:54 UTC"*;
  estimated burn 0.3590 USD/h.
- **[Claude] The plans**, `-input=false` as `awsds-infra-prod` on this branch, whose `terraform-live/` and
  `terraform-modules/` are `main`'s, each output read in full:
  - `production/proxy/`, 21:17:05: `1 to add, 2 to change, 1 to destroy`, resource for resource the plan of
    20:21:09. `aws_instance.this` is replaced on `ami` (masked) and `user_data`, destroy first (`-/+`); the
    alarm and `proxy.awsds.internal` change in place; the association does not change. It carries no `-n`.
  - `production/vpn/`, 21:17:21: `2 to add, 3 to change, 2 to destroy`, the plan of 20:27:27. The instance
    is replaced on `ami` and `user_data`, destroy first, with `associate_public_ip_address` `true -> false`
    inside the replacement (the module ignores its read-back, so it does not recur);
    `aws_eip_association.this` is replaced on `instance_id`; the alarm, `aws_route.tunnel_return` and
    `vpn.awsds.internal` change in place.
  - `production/observability/`, 21:17:37: `0 to add, 1 to change, 0 to destroy`, the dashboard's markdown.
- **[Claude] `./aws/proxy.py`**, without `--on-host`, stamped 21:21:57Z, exit 0: `i-0d42d0393c39eefdb`
  running, public `44.255.111.239`; `sandbox-foundation` holds 42 entries in the parameter; `PX-3` `note`,
  unanswered without `--on-host`. **`./aws/vpn.py`**, stamped 21:22:38Z, exit 0: `VP-1` to `VP-7` and
  `VP-9` pass, `VP-2` reading `52.89.212.1 -> i-011ffd7b6dde40a9a`, `VP-6` `awsds-prod-vpn-health` `OK`.
- **[Claude] Who used the hub**, `filter-log-events` over the three hours to about 21:25:
  - `/awsds/prod/vpn`: 166 sampler lines, `handshake=never` for `mbp` and `raspi` from 19:47:29 to
    21:22:49; `scutil --nc list` reads the laptop's four WireGuard profiles `Disconnected`.
  - `/awsds/prod/proxy`: 3,065 lines from three Sandbox sources. `10.20.15.119` at 19:50:52 (`10.32.0.10`
    and `example.com` `403 TCP_DENIED`, `pypi.org` `200`); `10.20.20.46` at 20:19:42 and 20:20:09 (the
    portal's `dzd-` domain, Redshift); `10.20.38.182`, `jup`: `pypi.org`, the portal, Redshift,
    `github.com` (6,550,620 bytes at 20:19:13), `raw.githubusercontent.com` (14,336 bytes at 20:19:16),
    `TM-01`'s probe at 20:29:25, and a `client-telemetry` and `cognito-identity` pair in `us-east-1` about
    every 2.5 s from 20:17:53 to the last line, 21:23:16.
- **[Claude] The idle shutdown**, CloudTrail `DeleteApp` by `AWSServiceRoleForAmazonSageMakerNotebooks`:
  `code` at 21:19:50, `jup` at 21:23:14. The domain's `IdleTimeoutInMinutes` is 60; both spaces read
  `InService` at 21:29:04.

### What each replacement does to a client

- **[Claude] The tunnel**: `scutil --nc show` reads `RemoteAddress : 52.89.212.1:51820` for `mbp` and
  `mbp-split-tunnel`, the Elastic IP the replaced association moves. The new host fetches its key from
  `awsds-prod-vpn-host-key`, the ARN `production/networking/` exports, and writes one `[Peer]` per entry
  of `peers.auto.tfvars`; neither appears in the plan.
- **[Claude] The proxy**: `proxy-on` in `~/.zshrc` exports `http://proxy.awsds.internal:3128`, Chrome's
  flag in `client-vpn-proxy-configuration.md` §4.1 names the same, and the house image's `https_proxy` is
  `ARG PROXY_URL=http://proxy.awsds.internal:3128` (`dev-env/Dockerfile` line 404), one value in every
  commit since `b7d37ff9` (2026-10-14), overridden by no build. Both spaces run `awsds-sandbox-dev-env`
  version 11. The proxy's apply re-points `proxy.awsds.internal` from `10.31.160.140`, the tunnel's
  `vpn.awsds.internal` from `10.31.160.22`, both in place, TTL 60.
- **[Claude] The new proxy's time to serve** is unmeasured. Its first boot installs the packages, renders
  the parameter while Squid is stopped (`(4) first render - squid is not running yet`), then starts Squid.
  An access stream is created at its first line, not at boot: `i-0d42d0393c39eefdb/access` at
  2026-09-18T17:13:54Z, its first event at 17:13:49Z, the day after that host was built.
- **[Claude] Squid on the new host**, from AWS's records read 2026-11-21: the AL2023.12 package list as of
  2023.12.20261021 has `squid` `6.13-1.amzn2023.0.6`, full support to 2029-06-30; release
  2023.12.20261112's core updated packages list `squid-6.13-1.amzn2023.0.7`; releases 2023.12.20261026 to
  20261109 and 20261117 to 20261120 list no squid. `al2023-ami-2023.12.20261120.0` installs from its own
  release's repository, so its Squid is `6.13-1.amzn2023.0.7` (inferred; `rpm -q squid` on the host is the
  reading). Squid 6.9's `acl` page gives `acl aclname dstdomain [-n] .foo.com ...`.

### `CreationTime` against `CreateApp` (`SUP-229`)

- **[Claude] CloudTrail**, `lookup-events` in Sandbox for `CreateApp`, `DeleteApp`, `CreateSpace` and
  `DeleteSpace` on 2026-11-21:
  - `code` in `d-m8m0uefej9kb`: `CreateSpace` 03:54:05, `CreateApp` 03:54:10, the idle `DeleteApp`
    05:04:31, `DeleteSpace` 18:34:05 by the infrastructure user, `CreateSpace` 20:08:41, `CreateApp`
    20:08:46. `describe-app` and `list-apps` (21:27:03) read `CreationTime` 03:54:10.197.
  - Restarts inside one space: `vscode` in `d-m8m0uefej9kb`, `CreateApp` at 03:29:56 and 07:09:41, reads
    03:29:56; `jup-ai`, 03:29:01 and 06:53:49, reads 03:29:01; `vscode` in `d-jaid1tvg20jv`, 03:30:54 and
    05:27:00, reads 03:30:54. `jup`, whose space was new at 20:07:15, reads 20:07:19.488, its one
    `CreateApp`.
  - The spaces' `LastModifiedTime`, `jup` 20:07:19.215 and `code` 20:08:45.303, did not move with the idle
    shutdown's `DeleteApp`.
- **[Claude] The API reference**, read 2026-11-21: DescribeApp's `CreationTime` says an application
  restarted within 24 hours of its last shutdown is an update and keeps its metadata; ListApps's
  `AppDetails` says only *"The creation time."*; neither names a space deleted and made again.
- `code`'s second run, 20:08:46 to 21:19:50, cost about 0.12 USD at 0.100 USD/h.

### The code

- **[Claude] `scripts/slices.py status`** bills an app from the later of its `CreationTime` and its
  space's, read with one `list-spaces` per account that has a billing app, and prints *"at most"*: a
  restart inside one space still dates from the first `CreateApp`. Exercised on the live `list-spaces`
  (`code` 20:08:41, `jup` 20:07:15) with `code`'s app at 21:15:37: *"0.1000 USD/h, at most 0.11 USD so
  far"*, *"since 2026-11-21 20:08 UTC"*; with the spaces unread, *"at most 1.74"* since 03:54; an app of a
  user profile and an app newer than its space keep the app's time; a dry run reads no space.
  `./scripts/slices.py status --env sandbox`, exit 0.
- **[Claude] `docs/AWS_SUPPLEMENT.md`**: `SUP-229` gains this reading, and its title says what holds now.
- **[Claude] Stage 12 step 2.2**: the hub sitting's block, window (a) recommended.
- **[The orchestrating session, relayed]** `production/vpn/` planned from `main` at `4053faee` at 21:30 UTC,
  `2 to add, 3 to change, 2 to destroy`, and saved for the user's authorization; this session ran no
  command on that slice from then on.

## 2026-11-22 — the hub sitting's applies: the tunnel host rebuilt on `t3.medium`, the proxy on `t3.small`

*Claude, in the same session and branch, at the request of the session coordinating the hub sitting,
from about 00:30 UTC, after pulling that session's `f44ef879` and merging `origin/main` at `65254241`. The
applies, the consoles and `./aws/observability.py` are the coordinating session's, relayed with their
times; `--on-host` and the SSM measurement ran on the user's word, and the re-probe is the user's. This
session's own AWS calls ran as the infrastructure user with `InfrastructureAccess` in Production
(`awsds-infra-prod`, `us-west-2`) from 00:39:49 to 00:40:14, read-only. No write. Times are UTC.*

### The tunnel host

- **[The coordinating session, relayed]** `production/vpn/` from `main` at `4053faee`, the saved plan of
  21:30, applied 2026-11-21 23:01:36 to 23:02:54: `2 added, 3 changed, 2 destroyed`, re-plan `No
  changes`. `main` moved to `8919ee39` (#351) at 23:00:52, after the plan was saved; `git diff` shows #351
  touches no input of the slice. The new host `i-0d6f67c37254eaa87`: `t3.nano`, `ami-09f6e62a9fe578f92`
  (`al2023-ami-2023.12.20261120.0-kernel-6.18-x86_64`), `10.31.160.47`. `./aws/vpn.py` passed every
  check, each of them describe-level.
- **[The coordinating session, relayed] Its console**: the user data's BEGIN at 23:02:31, then step (1),
  `dnf -y install wireguard-tools iptables-nft amazon-cloudwatch-agent`; the repository's metadata, 91 MB
  at 74 MB/s; at 25 s `Out of memory: Killed process 1962 (dnf)`, `anon-rss` 165,736 kB and about 348 MB
  swapped, the only dnf running, on 415 MiB of memory and 415 MiB of zram swap; then `Cloud-init 22.2.2
  received SIGTERM, exiting` as systemd stopped `cloud-final.service`; at 48 s update-motd's dnf
  (`70-available-updates`) killed too. The host had no `wireguard-tools`, no `wg0` and no CloudWatch
  agent, and `/awsds/prod/vpn` received no event after 23:02.
- **[The coordinating session, relayed]** #353 selected `t3.medium` in the tracked
  `instance_type.auto.tfvars`, merged as `2b180819`, and the host was rebuilt from `main` at that commit
  with `-replace=module.wireguard.aws_instance.this`, 23:22:32 to 23:23:46: `2 added, 3 changed,
  2 destroyed`, re-plan `No changes`. The new host `i-03ae94285145bff76`: `t3.medium`, the same image,
  `10.31.160.131`, ENI `eni-0131f5e6d80575e56`. Its console: BEGIN at 23:23:25, step (1) done at 23:24:02,
  37 s; the uplink `ens5`, the key in hand, `wg0.conf` for 2 peers, the sampler, the agent accepted, and
  `END - the tunnel endpoint is up` at 23:24:06. `52.89.212.1` associated; `vpn.awsds.internal` at
  `10.31.160.131`, TTL 60; the route `10.90.0.0/24` to the new ENI `active`; `awsds-prod-vpn-health` `OK`
  on the new instance, its action `awsds-prod-alerts`. SSM `Online` at 23:23:33.
- **[The coordinating session, on the user's word, relayed]** `./aws/vpn.py --on-host`: every check
  passes, `wg0` listening on 51820 with 2 peers, `10.90.0.2/32` and `10.90.0.3/32`. The stream
  `i-03ae94285145bff76/handshakes` from 23:24:25: `peer=mbp handshake=never` and `peer=raspi
  handshake=never`, about every 70 s. No client's handshake with the new host is read yet; it is the
  user's.
- **[Claude]** The tunnel was down from 23:01:38 to 23:24:06, about 22 minutes, and no device held it.

### A cold dnf's memory (`SUP-405`, `SUP-406`)

- **[The coordinating session, on the user's word, relayed]** SSM `AWS-RunShellScript` on the t3.medium at
  23:26, command `fbb03c56-7f5c-4d57-bc61-3fe28daa84e9`, the cache in throwaway directories under
  `/var/tmp`, deleted after; nothing installed. `MemTotal` 3835 MiB, no swap, 257 MiB used at rest (the
  CloudWatch agent 143 MiB RSS), 3351 MiB available. A cold `dnf install --downloadonly squid jq
  amazon-cloudwatch-agent`: exit 0, `VmHWM` 617 MiB, 26 s, a 204 MiB cache. A cold `dnf check-update`:
  exit 0, 623 MiB, 25 s.
- **[The coordinating session, relayed]** The proxy's console on the `t3.small`: `zram_generator::config:
  zram0: system has too much memory (1909MB), limit is 800MB, ignoring.`
- **[Claude] AWS's pages**, read 2026-11-22 (`docs/REFERENCES.md`): the AL2023 system-requirements page
  turns zram on by default since AL2023.3 for instance types under 800 MB, naming the nano sizes, and says
  that a `dnf upgrade` between some releases can need more than 512 MB; the page on package updates names
  no update-motd. A `t3.micro` read 913 MiB total on 2026-09-06 (Stage 6c's log), above the generator's
  limit, so a micro has no swap either.

### The proxy

- **[The coordinating session, relayed]** #354 made `t3.small` the slice's default, merged as `65254241`.
  `production/proxy/` from `main` at that commit, a saved plan, applied 23:51:42 to 23:53:26: `1 added,
  2 changed, 1 destroyed`, the instance replaced on `ami` and `user_data` with `instance_type` `t3.micro ->
  t3.small`; re-plan `No changes`. The §N.9 day 2 session confirmed first that no S3 write was in flight.
  The old host was destroyed in 1 min 3 s; the new `i-071bcc561f75b51d7`: `t3.small`, the same image,
  `10.31.160.128`. `proxy.awsds.internal` at `10.31.160.128`, TTL 60; `awsds-prod-proxy-status-check`
  `OK`, `notBreaching`, its action `awsds-prod-alerts`.
- **[The coordinating session, relayed] Its console**: `squid-6.13-1.amzn2023.0.7` installed, steps (2) to
  (4) with no `FAILED` line, (5) `systemctl enable --now squid`, (6), and `done - the proxy is up`.
- **[The coordinating session, relayed] The first requests** in the new instance's stream: 23:54:00,
  `10.20.54.175 CONNECT config.mlflow-telemetry.io:443 403 TCP_DENIED`; 23:54:03, `cognito-identity` and
  `client-telemetry` in `us-east-1`, `200 TCP_TUNNEL`. The proxy served nothing from 23:51:43 to 23:54:00,
  about 2 min 17 s.
- **[The coordinating session, on the user's word, relayed]** `./aws/proxy.py --on-host`, about 00:20 on
  2026-11-22: exit 0, `PX-1`, `PX-2` and `PX-3` pass, `sandbox_foundation allowlist -n 42`.
- **[The user, relayed]** `TM-01`'s re-probe at 00:20:41 from `jup`: `403` on both addresses and `200` on
  `pypi.org`, so `TM-01` is controlled. The curls' results and the log lines are in Stage 11's log of
  2026-11-22.

### `production/observability/` and `OB-3`

- **[The coordinating session, relayed]** `production/observability/` from `main` at `65254241`,
  00:22:16 to 00:22:27: `0 added, 1 changed, 0 destroyed`, the dashboard's markdown from *"The proxy's
  alarm reads `ALARM`..."* to *"The three hosts' alarms read `OK`..."*; re-plan `No changes`.
- **[The coordinating session, relayed]** `./aws/observability.py`: `OB-3` fails in Production on
  `awsds-prod-gitlab-status-check` alone, `production/tooling/`'s, which R1 applies after the admin
  secret's first rotation (2026-11-22 01:59:59 UTC); every other `OB-3`, and `OB-1` and `OB-5`, pass.
  `EXC-19` lifts with that apply.

### Read back by this session

- **[Claude]** `describe-instances` at 00:39:49: `awsds-prod-vpn` a running `t3.medium` at `10.31.160.131`,
  launched 23:23:14; `awsds-prod-proxy` a running `t3.small` at `10.31.160.128`, launched 23:52:54, public
  `184.36.57.235`; `awsds-prod-gitlab` a stopped `t4g.large`. `describe-addresses`: `52.89.212.1` on the
  tunnel host. `list-resource-record-sets` on `awsds.internal`: `proxy` and `vpn`, `A`, TTL 60, at those
  two addresses. `describe-alarms`: `awsds-prod-vpn-health` and `awsds-prod-proxy-status-check` `OK`,
  `notBreaching`, one action each, `awsds-prod-alerts`; `awsds-prod-gitlab-status-check` `OK`,
  `notBreaching`, no action. The proxy's alarm has read `OK` since 19:53:53 on 2026-11-21, through the
  replacement.

### The hub's cost lines

- **[The §N.9 day 2 session, relayed]** `docs/PRICING.md`, `runbooks/vpn.md`, this stage's 5.2 and Stage
  20's pass 8 priced the hub at D4's `t3.nano`, 0.0310/h, while the tracked file has selected `t3.medium`
  since #353 and that is what runs (that session's `describe-instances`: the tunnel host `t3.medium` and
  the proxy `t3.small`, both running). At `docs/PRICING.md` §8's rates the running hub is the `t3.medium`'s
  0.0416, the `t3.small`'s 0.0208 and the proxy's public IPv4 at 0.005: 0.0674/h, 49.20 for 730 hours, and
  0.0724/h with the VPN's Elastic IP, the floor line. On `t3.nano` the same sum is 0.0310/h, 22.63 for 730
  hours. Going from `t3.medium` back to `t3.nano` saves 0.0364/h, 26.57 for 730 hours.
- **[Claude]** Each of those lines now gives the running figure with D4's beside it, and stays true
  until decision due 4 is taken. `docs/PRICING.md`'s typical Sandbox hour carried the same `t3.nano`
  figure and takes the same correction. In 5.2's table the `[D]` reading is 49.20 against 8.90, the 132
  hours of September at 0.0674, so 40.30 a month more, beside 22.63 against 4.09 at 0.0310, 18.54: the 4.09
  is those hours at 0.0310, so it does not pair with 49.20. `scripts/tfhygiene/layers.py`'s vpn row stays
  0.0052: its comment says it prices the baseline and not the host, and `./aws/vpn.py`'s `VP-1` reports
  the gap.

### Records

- **[Claude]** This stage: the `Status` row, 2.2's sitting (step 3's `t3.micro` sentence now history, the
  done paragraph with what is owed), 5.2's hub row and decision due 4, the tunnel host's default size,
  with its options and no recommendation. `SUP-405` and `SUP-406` in `docs/AWS_SUPPLEMENT.md`, and
  AWS's pages in `docs/REFERENCES.md`. `docs/NETWORK.md`'s hub rows and diagram: `10.31.160.131` and
  `10.31.160.128`, with the sizes. `docs/AWS_STATE.md`: `EXC-19` narrowed to GitLab's alarm, the proxy
  alarm's `breaching` row and the `PX-3` row closed, the tunnel host's size. `waiting-on-the-user.md`: the
  Hub row and the size decision. `TM-01`'s records are in Stage 11's log.

## 2026-11-22 — step (0): a swap file and update-motd masked before the first boot's `dnf` (#356)

*Claude, in the session coordinating the hub sitting, at the user's request ("Faça esta tarefa aqui"), on
branch `claude/dnf-first-boot` from `main` at `65254241`, merged with `main` at `0e95f2f0` once #352 was
in. No AWS write: the plans below ran read-only as the infrastructure user with `InfrastructureAccess` in
Production (`awsds-infra-prod`, `us-west-2`), and nothing was applied. Times are UTC.*

### The change

- **[Claude] `wireguard-v0.8.1`.** The user data's new step (0) runs before step (1)'s `dnf`. It writes a
  1 GiB swap file with `dd`, adds it to `/etc/fstab`, and runs `systemctl mask --now update-motd.service`.
  Neither command is fatal: a host large enough builds without them, and step (1) is where a host too
  small says so. The argument sits in `main.tf` beside the `templatefile()` call: the nano's OOM of
  2026-11-21, a cold dnf's 617 and 623 MiB, and the 800 MB zram limit (`SUP-405`, `SUP-406`).
- **[Claude] `wireguard-v0.8.0` is abandoned** (Lesson 46). Tagged at 00:45:19 on `09548e07`, it carried
  the argument as comments inside the script. Rendered with production's peers, that came to about 16,432
  bytes, and the plan refused it: `expected length of user_data to be in the range (0 - 16384)`. EC2's
  16 KB counts comments. The tag stays on origin, never pinned. v0.8.1 (`9c1eeec6`, 00:51:44) moved the
  comments out. `CLAUDE.md`'s list of abandoned tags takes it in the orchestrating session's batch at the
  end of day 2.
- **[Claude] The callers** (`f763349d`, 00:53:15):
  - `production/vpn/` pins `wireguard-v0.8.1`.
  - `production/proxy/`'s user data gets the same commands, with the argument in the slice's `main.tf`.
  - The texts that state the sizes now say the first boot no longer decides them: `runbooks/vpn.md` §S6,
    the comment in the tracked `instance_type.auto.tfvars`, the proxy's `instance_type` description, and
    the proxy layer's comment in `scripts/tfhygiene/layers.py`.
  - These commits change no size. Decision due 4's option (d) names this PR, and the user took it
    (below).

### The plans, read-only

- **[Claude] `production/vpn/`**, planned after `git ls-remote` read `wireguard-v0.8.1` on origin at
  `9c1eeec6` and `init` fetched it: `Plan: 2 to add, 3 to change, 2 to destroy.`
  - The instance is replaced on `user_data` alone. Step (0) is the only change in it; the size stays
    `t3.medium` and the AMI stays the same.
  - The Elastic IP's association is replaced.
  - The route, the record and the alarm are updated in place.
- **[Claude] `production/proxy/`**: `Plan: 1 to add, 2 to change, 1 to destroy.`
  - The instance is replaced on `user_data`; the size stays `t3.small` and the AMI stays the same.
  - The record and the alarm are updated in place.
- **[Claude] The user data's size**, read from each plan's JSON:
  - the VPN's grows from 13,435 to 14,456 bytes, 1,928 under the cap;
  - the proxy's grows from 15,148 to 15,685, 699 under it.

  The proxy's margin is thin, because `squid.conf` and the render script ride inside its user data.

### What was not measured

- **[Claude] No first boot with step (0) has run, at any size.** The laptop has no Docker for a local
  AL2023 run.
- **[Claude] update-motd was read only by its service and its script.** The service is the cgroup in the
  nano's OOM line, and the script is `70-available-updates`. Whether a timer also starts it was not read;
  `mask` covers the service either way.
- **[Claude] On the nano the two `dnf` runs did not overlap.**
  - The first kill's task table, at 25.4 s, lists one `dnf` (pid 1962) and no update-motd.
  - update-motd (pid 1994) and its `dnf` (pid 2003) appear only in the second table, at 47.9 s, after
    cloud-init's SIGTERM.
  - Whether update-motd waits for `cloud-final.service` was not read. `SUP-406` now carries the sentence.

### Decision due 4 taken, and the nano selected (`90ce7675`)

- **[user]** *"sim, põe o nano no #356"*, shortly after 01:00 UTC. It answers the session's recommendation
  to put the VPN back on `t3.nano` inside this PR, and takes decision due 4 as (d), with `t3.nano`.
- **[Claude] The selection.** The tracked `instance_type.auto.tfvars` comments out its `t3.medium`
  assignment, so the variable's default, D4's `t3.nano`, governs.
- **[Claude] The re-plan**, read-only at 01:09: `Plan: 2 to add, 3 to change, 2 to destroy.` The instance
  is replaced: `instance_type` goes `"t3.medium" -> "t3.nano"`, and `user_data` forces the replacement.
- **[Claude] The records.**
  - The cost lines return to 0.0310/h, with the `t3.medium` figure kept as history where a comparison
    needs it: `PRICING.md`'s typical hour, hub bullet and unit line; `runbooks/vpn.md`'s burn cell and
    `make hub-up`; Stage 12's 5.2 row; Stage 20's pass 8.
  - Decision due 4 reads taken.
  - `waiting-on-the-user.md` drops its row, and the Hub row gains the VPN's apply.

### Owed

- **The user's word for `production/vpn/`'s apply** once this PR merges, from `main` (Lesson 79). Its first
  boot is the proof, and its console should show:
  - a `(0) swap:` line that names `/swapfile`;
  - `(0) update-motd masked`;
  - `(1) done`;
  - `END - the tunnel endpoint is up`.
- **After the apply:**
  - `docs/NETWORK.md`'s and `docs/AWS_STATE.md`'s VPN rows take the new host's address and size;
  - the §N.9 day 2 session takes the hub's rate;
  - the orchestrating session takes the index rows.
- **The proxy keeps `t3.small`.** Its user data's step (0) waits for an apply outside the §N.9 day 2
  sitting, since any proxy apply replaces the estate's single internet exit.

## 2026-11-22 — `production/vpn/` applied: the tunnel host back on `t3.nano`, and step (0)'s first boot

*Claude, in the session coordinating the hub sitting, on the user's word once #356 merged at 01:11:32
("fiz o merge. autorizo o apply."). The apply ran from the coordinating worktree fast-forwarded to `main`
at `13e277b4` (Lesson 79), as the infrastructure user with `InfrastructureAccess` in Production
(`awsds-infra-prod`, `us-west-2`). The §N.9 day 2 session and the orchestrating session were told before
the write. Times are UTC.*

### The apply

- **[Claude] The saved plan**, at 01:13: `Plan: 2 to add, 3 to change, 2 to destroy.`, as the read-only
  re-plan of 01:09 in the entry above.
  - The instance is replaced: `instance_type` goes `"t3.medium" -> "t3.nano"`, and `user_data` forces
    the replacement.
  - The Elastic IP's association is replaced.
  - The route, the record and the alarm are updated in place.
- **[Claude] The apply**, 01:14:51 to 01:16:26: `Apply complete! Resources: 2 added, 3 changed, 2
  destroyed.`
  - `i-03ae94285145bff76`, the `t3.medium` launched at 23:23:14, was terminated at 01:15:01.
  - `i-0e3ae32bacd61c9b2` launched at 01:15:54: `t3.nano` on 8 GiB gp3, `10.31.160.195`, ENI
    `eni-0d65d885376e9f668`, the Elastic IP `52.89.212.1` associated as `eipassoc-0deee4fd8a9a482a8`.
  - The tunnel was down from about 01:15 to `wg0`'s start at 01:17:21. No client held it: the
    `t3.medium`'s handshake stream reads `handshake=never` for both peers in all 190 of its lines, from
    23:24:25 to 01:13:55.
- **[Claude] The re-plan** at 01:17:24: `No changes.`, `-detailed-exitcode` 0.
- **[Claude] `main` moved during the apply.** #357 (`adfd1019`) merged at 01:16:23 and changed `CLAUDE.md`
  and `docs/SMUS-GRAPH-TOOLS.md` alone, so the applied configuration is `main`'s.

### The first boot: step (0)'s proof

Read with `get-console-output --latest` every 20 s until `END`:

- `BEGIN` at 01:16:05, on the kernel `6.18.62-127.179.amzn2023.x86_64`, the same image as the
  `t3.medium`'s.
- The kernel added `/dev/zram0` at 3.0 s of uptime, 424,956 KiB at priority 100, and `/swapfile` at
  14.2 s, 1,048,572 KiB at priority -2. Step (0) logged `(0) swap: /dev/zram0 415M;/swapfile 1024M` at
  01:16:13 and `(0) update-motd masked` at 01:16:14.
- Step (1)'s `dnf` ran from 01:16:14 to `(1) done` at 01:17:19, 65 s. The `t3.medium`'s took 37 s on
  2026-11-21.
  - The AL2023 repository's metadata, 91 MB at 68 MB/s, was in by 17.1 s of uptime.
  - The next repository's line came at 68.4 s. A cold parse peaks at about 620 MiB (`SUP-406`) on a
    host of 415 MiB, so the swap carried those 51 s (inferred: the host's memory was not read).
  - `Install  7 Packages`, 72 M to download and 249 M installed; `Complete!` at 80.1 s.
- `wg-quick@wg0` started at 01:17:21 for 2 peers. The CloudWatch agent accepted its configuration at
  01:17:25, and `END - the tunnel endpoint is up` came at 01:17:25.
- cloud-init: `finished at Sun, 22 Nov 2026 01:17:25 +0000`, `Up 86.16 seconds`.
- The console holds no `Out of memory`, `oom-kill` or `Killed process` line.

### The reads after it

- **[Claude] `./aws/vpn.py`** at 01:18:58: `0 check(s) FAILED`.
  - `VP-1` reads `t3.nano on 8 GiB gp3, state running`.
  - `VP-2` reads `52.89.212.1 -> i-0e3ae32bacd61c9b2`.
  - `VP-4` reads `HttpTokens=required`, and `VP-6` reads `awsds-prod-vpn-health (OK)`.
- **[Claude] The route and the record**, at 01:19:20: `10.90.0.0/24` to `eni-0d65d885376e9f668`,
  `active`; `vpn.awsds.internal` `A` `10.31.160.195`, TTL 60.
- **[Claude] The new handshake stream**, `i-0e3ae32bacd61c9b2/handshakes`: at 01:17:22 and at 01:18:24,
  `peer=mbp handshake=never` and `peer=raspi handshake=never`.

### The rate

- **[Claude]** The VPN bills `t3.nano`, 0.0052/h, from 01:15:54. The `t3.medium`'s 0.0416 stopped at
  01:15:01. The hub runs at 0.0310/h, or 0.0360 with the VPN's Elastic IP, against 0.0674 (0.0724). The
  §N.9 day 2 session has the times.

### What was not measured

- **[Claude] The host's memory**, so how far into the swap file the `dnf` went. Reading it needs SSM on
  the host, which the word for this apply does not cover. The console proves only that the install
  finished.
- **[Claude] A client's handshake** with the new host. That is the user's.

### Records

- **[Claude]** This stage: the `Status` row, 2.2's owed items and decision due 4. `docs/NETWORK.md`'s
  WireGuard row and diagram: `10.31.160.195` on `t3.nano`. `docs/AWS_STATE.md`'s VPN row.
  `runbooks/vpn.md` §S6. `SUP-406` takes the swap file as the measured remedy. `waiting-on-the-user.md`'s
  Hub row: the apply out, the client's handshake in.

### Owed

- A client's first handshake on the nano, the user's.
- The proxy's step (0), in an apply outside the §N.9 day 2 sitting: any proxy apply replaces the estate's
  single internet exit.
- The orchestrating session's index rows, at the end of day 2.
