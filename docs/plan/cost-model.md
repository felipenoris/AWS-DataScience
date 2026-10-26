# Cost model of the lab

The bill, the floor and the session cost read from it, and the projection that follows. Per-unit rates
live in [`docs/PRICING.md`](../PRICING.md), measured from the AWS Price List and never estimated here. The
operating model that produces these numbers is `docs/plan/conventions.md` §5.1.

---

## 5. Cost model

Under D11 the question is the floor when nothing is running, plus what a session adds on top. Both are read
from Cost Explorer in every account with a CLI profile on 2026-10-18 (Stage 12 step 4.2): one
`get-cost-and-usage` per account, by service and usage type, unblended, `us-west-2`. Management, Log Archive
and Audit hold no profile and are not in these figures.

### The bill

| Account | August | September | October 1-17 |
|---|---|---|---|
| Sandbox | 43.81 | 45.55 | 21.50 |
| Production | 4.11 | 21.31 | 29.19 |
| Staging | 2.93 | 2.82 | 1.83 |
| Data Governance | 1.36 | 2.82 | 2.00 |
| Identity | 0.77 | 1.50 | 1.12 |
| Policy Canary | 0.33 | 0.47 | 0.50 |
| **The accounts read** | **53.31** | **74.48** | **56.15** |
| of which the floor | 9.90 | 32.47 | 21.79 |
| of which sessions | 43.22 | 41.93 | 34.11 |

USD. Net equals unblended in every account: no credit reaches these lines. The totals also hold the Cost
Explorer requests, 0.01 each (0.10, 0.06 and 0.25), and data transfer (0.09 in August, 0.02 in September). **D12's USD 50 ceiling was passed in
August and in September** with Management, Log Archive and Audit still unread, and its revision trigger, the first month above
the 29-43 projection, fired in August. The unread three carry at least their Config recorders, Security Hub
(about 13.5 for the organization in September against 4.48 here, `docs/PRICING.md` §2) and Log Archive's
buckets; Management's Cost Explorer reads the whole organization in one view, which is the user's to take.

### The floor

What a month bills with nothing running, line by line from the invoice. The last column prices the set that
exists on 2026-10-18 at the measured rates, so it is arithmetic over readings rather than a reading.

| Item | Invoice line | Aug | Sep | Oct 1-17 | A month, today's set | Note |
|---|---|---|---|---|---|---|
| KMS customer-managed keys | `us-west-2-KMS-Keys` | 5.34 | 11.13 | 6.12 | ~11 | 1.00 per key version-month; September by account: Production 3.80, Sandbox 2.99, Data Governance 1.99, Staging 1.34, Identity 1.00. Each yearly rotation adds a version (`docs/PRICING.md` §2) |
| EBS, the `[D]` hosts | `USW2-EBS:VolumeUsage.gp3` | 1.15 | 1.38 | 1.98 | 6.24 | 0.08/GB-month over GitLab's 62 GiB and the hub's 16 GiB, billed stopped or running. October holds GitLab from 2026-10-12; August, the buildbox and the Sandbox VPN host |
| SageMaker space volumes | `USW2-Studio:VolumeUsage.gp3` | 0.56 | 5.37 | 3.62 | 3.58 | 0.112/GB-month with every app stopped: 32 GB on 2026-10-18 and 368 GB on 2026-10-15 (`AWS/Usage` `studio/total_volume_size_in_gb`), so the row is whatever spaces exist |
| Public IPv4, idle | `USW2-PublicIPv4:IdleAddress` | 0.76 | 3.79 | 1.72 | ~3.1 | the WireGuard Elastic IP while its host is stopped, 0.005/h; September also paid the proxy's address until 6g decision 1 released it |
| ECR storage | `USW2-TimedStorage-ByteHrs` (ECR) | 0.28 | 1.59 | 1.55 | ~2.8 | 0.10/GB-month, 15.9 GB-month in September |
| Route 53 private zones | `HostedZone` | 1.50 | 4.00 | 2.50 | 2.50 | 0.50 per zone, charged on the first of each month: `awsds.internal`, `prod.` and `awsds-pages.internal` in Production, `sandbox.` in Sandbox, `staging.` in Staging. September's 4.00 carried the zones 6c retired |
| Secrets Manager | `USW2-AWSSecretsManager-Secrets` | 0.19 | 0.57 | 0.86 | ~1.6 | 0.40 per secret-month |
| Security Hub | `USW2-PaidComplianceCheck` | 0 | 4.48 | 3.33 | 0 | the FSBP standard paused since 2026-10-09 (`EXC-14`) |
| S3, DataZone, CloudWatch, snapshots | | 0.11 | 0.16 | 0.10 | ~0.2 | CloudWatch inside its free tiers; Stage 12's alarms add 0.40-0.70 |
| **Floor, the accounts read** | | **9.90** | **32.47** | **21.79** | **~31** | |

**Not billing yet**: the Redshift warehouse, inside its free trial until 2026-12-19 (*The warehouse*, below),
GuardDuty (Stage 15) and AWS Backup (Stage 12 step 8). August's floor is a partial month: most of it was
built during the month.

### Per session

What a session adds, from the same lines, with the rates the hours are counted at.

| Item | Invoice line | Rate (`docs/PRICING.md`) | Aug | Sep | Oct 1-17 | What the bill says about the hours |
|---|---|---|---|---|---|---|
| **Interface endpoints** | `USW2-VpcEndpoint-Hours`, `-Bytes` | 0.010 per endpoint-hour; Sandbox's 18 are 0.180/h, Staging's 7 0.070/h (11 and 0.110 until Stage 9 4.3a), `VPC-SharedServices`' 12 0.120/h, `VPC-Workloads`' 7 0.070/h; an optional group 0.010-0.070/h when named | 10.16 | 19.92 | 9.70 | Sandbox 991, 1,945 and 506 endpoint-hours: about 108 hours of its set in September and 28 in October's first 17 days. Production 435 in October, about 36 hours of `VPC-SharedServices`' |
| **AWS Config** | `USW2-ConfigurationItemRecorded` | 0.003 per item: 0.36-0.87 per Sandbox `[E]` cycle, 0.21-0.38 per GitLab cycle | 9.61 | 10.87 | 9.77 | a cycle costs the same whatever its length, so two short sessions cost twice one long one |
| EC2 hosts | `USW2-BoxUsage:*` | proxy `t3.micro` 0.0104, WireGuard `t3.nano` 0.0052, GitLab `t4g.large` 0.0672, build runner `m8i.xlarge` 0.2117, deploy and test runners `t3a.small` 0.0188 each, probes `t4g.nano` 0.0042 | 16.10 | 3.74 | 10.26 | August's 14.31 is the buildbox, 86 h of `t3.xlarge`; the hub ran 132 h in September and 64 h in October 1-17; October's build runner 27 h (5.76) and GitLab 38 h (2.54) |
| SageMaker apps | `USW2-Studio:<app>-<type>` | `ml.t3.medium` 0.050, `ml.t3.large` 0.100, `ml.t3.xlarge` 0.200 | 0.23 | 4.74 | 3.44 | JupyterLab on `ml.t3.medium` billed 0 for 17.5 h and 26.9 h in August and September and 1.26 for 25.2 h in October (the SageMaker free tier's two months, inferred) |
| Public IPv4, in use | `USW2-PublicIPv4:InUseAddress` | 0.005/h | 1.56 | 1.33 | 0.65 | the hub's two addresses while their hosts run |
| Bedrock (Claude) | the Marketplace token lines | per token | 0 | 1.30 | 0 | September's Stage 6e sessions |
| NAT gateways | `USW2-NatGateway-*` | 0.045/h plus its address | 5.52 | 0 | 0 | August, before 6c; none exists since (D38) |
| Workflows, Glue, jobs, DNS Firewall | | | 0.04 | 0.03 | 0.30 | the DNS Firewall 0.04, 0.02 and 0.01 of it |
| **Sessions, the accounts read** | | | **43.22** | **41.93** | **34.11** | |

The interface endpoints and the Config cycles are 73% of September's sessions. VPC peering billed 0.02 in
September: the hub hosts and every endpoint set sit in `usw2-az1`, where peering is free. **Transit Gateway was
the alternative and it is priced**: 5 attachments × 0.05/h ≈ USD 182/month standing before a byte
(`docs/PRICING.md` §7).

### What the projection had wrong

Each line names the invoice line that corrected it (Stage 12 validation 3).

- **The total.** Projected 29-43 a month; billed at least 53.31 in August and 74.48 in September in the
  accounts with a profile.
- **The hours.** The projection counted 20 lab hours a month; `USW2-VpcEndpoint-Hours` puts Sandbox's
  September at about 108, and `USW2-BoxUsage:t3.micro` the hub's at 132. The rates were right.
- **Config is a session cost.** The floor row read ~0.5 from the 2026-08-14 reading;
  `USW2-ConfigurationItemRecorded` billed 9.61, 10.87 and 9.77, almost all of it `[E]` churn. A stage's
  creates and deletes churn it too: 0.71 of Staging's 1.52 over Stage 18's window (2026-10-17 to
  2026-10-21, estimated).
- **The floor missed four lines**: the spaces' volumes (`USW2-Studio:VolumeUsage.gp3`, 5.37 in
  September), the public addresses while stopped (`PublicIPv4:IdleAddress`, 3.79 in September with two
  addresses idle), ECR at 1.59 against ~1.00, and Security Hub at 4.48 in the accounts read against 1-2 for
  the organization.
- **Staging holds a zone.** `staging.awsds.internal` bills 0.50 a month (`HostedZone`), where the floor said
  Staging held none.
- **The KMS row** read ~13 for a year-one set; `us-west-2-KMS-Keys` billed 11.13 in September. `alias/awsds-staging-project` joined on 2026-10-19 for Stage 18's life (`staging/studio/`), +1.00 a month while it exists; it is `PendingDeletion` since 2026-10-22, its deletion date 2026-11-21, and whether a key pending deletion bills is November's invoice to read.
- **The warehouse's first bill.** This file said no free trial absorbed its 9.48 USD; the Redshift
  Serverless trial did, and no Amazon Redshift line appears through October 17 (*The warehouse*).

### The projection, from the bill

A month at today's set and September's hours is about 31 of floor and 42 of sessions: **about USD 73 in the
accounts read, against a ceiling of 50.** October's first 17 days ran at 3.30 a day, about 102 for the month at that
pace (arithmetic). The floor alone leaves about 19 a month for sessions, and September's sessions cost about
0.39 per Sandbox session hour (41.93 over its ~108 hours, every account's session cost included), so the
ceiling holds about 49 such hours a month.

The levers, in the order the bill ranks them:

- **Endpoint hours.** A Sandbox session left up bills 0.18 USD an hour in endpoints alone, 4.32 for a
  forgotten day; `make down` is the guard, and `make status` the meter.
- **The number of `[E]` cycles.** Each costs 0.36-0.87 of Config whatever its length.
- **Spaces nobody deletes.** 0.112 per GB-month with every app stopped.
- **The key count**, which grows by a version per key and year from 2027-08.

### What a second business unit adds to the floor (D35)

Every row above is written for one Sandbox, and `Sandbox` is the one account that multiplies. A unit brings
**one account** (free at rest, but one slot against the organization quota), **one AWS Config recorder**,
**three KMS CMKs** at ~USD 1.00 each (the `tfstate` key, the D31 account data key, and the project CMK
`alias/awsds-<env>-project` that the unit's `sagemaker/` slice creates), and, dominating the hourly side,
**one full set of interface VPC endpoints**: 18, at 0.010 per endpoint-hour, so USD 0.18 per hour that unit
is working, plus its own Config cycles. A unit is roughly **+USD 3.5-5.5 on the floor** and **+~USD 0.23 per
active hour** (endpoints plus one `ml.t3.medium` app), against a ceiling the bill already passes.

Those figures are not measured: they are the measured rates in `docs/PRICING.md` re-summed for one more
account. The per-unit total is measured at [Stage 14](stages/stage-14-sandbox-vending.md), before the first
vended unit rather than after it (Lesson 6). Watch the endpoint row there: it decides whether **centralized
interface endpoints shared by RAM** stop being the institutional answer
(`docs/plan/institutional-delta.md`) and become the arithmetic one.

### Two cost levers worth applying rather than discovering later

- **S3 Bucket Keys** on every SSE-KMS bucket. They cut KMS request charges by up to ~99%, and a data
  environment issues a KMS request per object operation — without this, KMS requests can quietly exceed
  the cost of the keys themselves. Set in the `s3-bucket` module from Stage 2; the bill's KMS request line
  is under a cent a month.
- **Scope Macie deliberately** (Stage 11). Macie charges per GB inspected for sensitive-data discovery. Run
  it against a sampled prefix, not the whole lake, or it becomes the largest single line item in the
  project. The same caution applies to **CloudTrail S3 data events**, which bill per event: a single Spark
  job listing and reading thousands of objects generates a matching number of events.

### What the ceiling rules out

Always-on GitLab (~USD 60/month on its own), AWS Client VPN (~USD 73/month, the D4 alternative), Network
Firewall (~USD 290/month, option D5c) and an always-on MWAA environment (~USD 212/month for `mw1.micro`,
~USD 358/month for `mw1.small` — D7 alternative A). Any of these is affordable only as a short, deliberate
experiment, which is what the operating model is for. D7 builds no MWAA environment: **MWAA Serverless**
(USD 0.088 per task-hour, no environment fee) is the only orchestrator, and Stage 10 step 4.3's
`DenyProvisionedMwaa` makes the always-on environment a call the root SCP refuses. The same discipline applies inside the unified
domain (D26): the Lakehouse blueprint is enabled in its Glue/Athena form only — its **Redshift Serverless**
variant would put a second, larger query bill on top of Athena's, and is excluded by decision.

### The warehouse

**The warehouse is a third billing shape** ([D40](decisions/D40-redshift-warehouse.md)): a Redshift
Serverless workgroup at `base_capacity = 4` bills **0.00 at rest and 1.44 USD per hour a query runs**, so it
fits neither table above and is bounded instead by a control the service enforces, a `serverless-compute`
**usage limit** with `breach_action = deactivate`, applied in the act that creates the workgroup (10
RPU-hours a month since 2026-09-20). Three documented ways an idle warehouse bills anyway — an unclosed
transaction (up to **8.64 USD** before `SESSION TIMEOUT`), a connection pool's keep-alive, a cancelled query
— are why the guard is a ceiling rather than a notification. `make down ENV=sandbox` destroys the
workgroup, since Redshift Serverless has no pause, and leaves the Redshift Managed Storage, the price of
keeping the data between sessions.

**It exists in Sandbox since 2026-09-20, and its free trial has absorbed every cent.** Stage 5b's execution
measured **9.4767 USD**, 26.32 RPU-hours by `ComputeSeconds`, of which **6 h 33 min was one query nobody
was watching**, running at base capacity after its client stopped polling: 19% of the D12 ceiling in one
sitting. The Redshift Serverless console read *"Free trial credits remaining $287.90 out of $300.00"* and an
expiry of December 19, 2026 on 2026-10-17, and Cost Explorer carries no Amazon Redshift line through
October 17 (`docs/PRICING.md` §5, Stage 5b verification xiii). After that date the warehouse bills at the
rates above. On 2026-10-25 Sandbox read *"$287.51 out of $300.00"* and Production *"$299.71 out of $300.00"*, its window closing 2027-01-21, 90 days after its namespace (Stage 9's log); on 2026-10-26 Production read 299.69 after a sitting of two short statements, 0.02 USD where `ComputeSeconds` read 0.0079: the 60-second minimum per query is billed from the balance and absent from the metric. Stage 9 xxiv's sitting the same evening read 299.66 then 299.54, 0.12 USD against 0.0078 by the metric.

Three guards did not catch the runaway. `max_query_execution_time` did not stop the query, and three
explanations are live: Redshift exempts a superuser from the rule, the standalone parameter is not
enforced at all, or the statement, which read catalog tables alone, ran on the leader node and never
entered WLM, so neither the per-query limit nor the usage limit's refusal reached it. The test that
separates the three is a long query over a user table, run as a non-superuser and as the admin
([Stage 5b's log](../log/log-stage-05b-redshift-serverless.md), 2026-10-18, *A third candidate for the
runaway*). The usage limit is the second guard, and it did not stop the statement either: it kept
running through the two minutes the workgroup was breached on 2026-09-20, while the breach refused
every query that needed the compute. And `make status` read `0.0000 USD/h` throughout, because the
slice's authored `usd_per_hour` was 0.0; it is **1.44** since 2026-09-20, a ceiling rather than an
average.

**The warehouse's storage has its own ceiling, and it is not small.** A sandbox schema carries a **1 TB**
quota (`objectives.md`, 2026-09-20), which at 0.024 USD/GB-month is **24.58 USD a month if filled — 49% of
the D12 ceiling from one schema**, and **nothing bounds the number of schemas**: 32 of them at 1 TB reach the
32 TB a 4-RPU workgroup supports, at roughly 786 USD a month. So the quota bounds a *runaway*, not the bill,
and what bounds the bill is an alarm on the namespace's `DataStorage` metric
([Stage 6h](stages/stage-06h-redshift-connection.md) decision 7).

### The guardrail

AWS Budgets with e-mail alerts was to exist before any compute (Stage 1a). **D12's budget notifies
nobody**: the alerts were skipped by decision on 2026-08-09, [Stage 6e](stages/stage-06e-claude-code-bedrock.md)
8.3 re-opened it, and Stage 12 step 2.1 supplies the spend curve above. For the warehouse a budget is not
enough even when wired, since it notifies after the money is spent; the usage limit is the guard that
refuses.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
