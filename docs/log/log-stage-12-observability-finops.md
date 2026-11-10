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
