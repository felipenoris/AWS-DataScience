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
