# Stage 12 — Observability, governance and FinOps

| | |
|---|---|
| **Status** | **in progress since 2026-10-18** ([log](../../log/log-stage-12-observability-finops.md)). Step 10's `./aws/observability.py` written 2026-10-17. **Built in Production 2026-10-18**: `production/observability/` (the hub dashboard, the proxy log's two metric filters, the refusal alarm, the VPCs-per-Region quota alarm) and the CloudWatch statement on `awsds-prod-alerts`, both re-planning `No changes`. **`sandbox/observability/` was applied the same day by the orchestrating session** (9 added, `No changes` after), the topic's e-mail subscription confirmed by the user on 2026-10-19, so `OB-3` passes in Sandbox. 4.2 read the bill from the accounts with a profile: **at least USD 53.31 in August and 74.48 in September**, above D12's 50, and the model is rewritten from it. `OB-3` fails since the first wired alarm, by design, until the three `[D]` hosts' alarms are wired (`EXC-19`); Sandbox's two warehouse alarms notify `awsds-sandbox-alerts` since PR #181's apply. Scoped against [D38](../decisions/D38-single-egress-hub.md): no NAT panels, and three lines the hub creates — the proxy's access log and its refusal rate, the DNS Firewall's per-query charge, the peering bytes. 5.2 read the bill's usage types on 2026-10-20: no letter moves (decision due 3, the user's) |
| **Prerequisites** | any stage that created resources — and **one real invoice**, met: the August and September bills, read from Cost Explorer in every account with a CLI profile (2026-10-14 for Config, 2026-10-18 in full). Management, Log Archive and Audit hold no profile and are unread |
| **Consumes** | [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D38](../decisions/D38-single-egress-hub.md) |
| **Proves** | nothing new crosses an account boundary. What it **retires** is a set of estimates |

*Read with [`docs/plan/conventions.md`](../conventions.md) §5.1 (the three layers) and
[`docs/plan/cost-model.md`](../cost-model.md) (the projection this stage replaces with measurements).*

---

**Objective:** know what is running, what it costs, and be told when something breaks — from the bill, not
from the plan.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — only after the user authorizes that specific action in chat, with the SSO user / account / permission set stated first |
| **[user]** | the Billing console (Management only), the backup restore tests, and the log entries the user writes |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make |

## Step numbers are identifiers, not an order

Steps 1-3 are the observability half, 4-6 the cost half, 7-9 the governance half; **step 4 is the one with
a hard prerequisite** (a real bill) and steps 3.2 and 8.2 the ones with an irreversible floor.

---

## To execute

### 1. Build the dashboards

**Action:** a CloudWatch dashboard per account plus a hub dashboard. **Why:** every earlier stage measured
its own thing once; nothing shows the estate at a glance, and D38 made one account's two hosts a dependency
of every other account's session. **Explanation:** the panels are chosen so that a *stopped* hub host and a
*full* disk look different from each other.

- **1.1 — [Claude] Write the per-environment dashboard**: SageMaker app and job hours, Athena bytes
  scanned against the workgroup limit, GitLab instance and EBS, the `[E]` endpoint count, and — replacing
  the NAT panels that no longer have a resource — **the DNS Firewall query count** for that VPC.
  **Written 2026-10-18**: `awsds-sandbox-environment` in `sandbox/observability/` (applied the same day)
  and Production's panels inside `awsds-prod-hub` (1.2), one dashboard for both because CloudWatch's free
  tier holds three, counted once per bill (inferred, `docs/PRICING.md` §6); Staging gets its own with Stage 9's
  runtime, the third. **App and job hours have a source**: `AWS/Usage` `ResourceCount`, `Service=SageMaker`,
  one metric per app or job type (`studio/JupyterLab-ml.t3.medium`, `processing-job/ml.t3.medium`),
  read with data on 2026-10-18, so `EXC-10`'s "no running-app metric exists" read only the `AWS/SageMaker`
  namespace. The endpoint count is the same family's `InterfaceVPCEndpointsPerVPC` by `[P]` VPC id, and the
  DNS Firewall count `AWS/Route53Resolver` `VpcFirewallQueryVolume` by VPC id. **Athena against a workgroup
  limit has no source**: the enforced workgroup left with the derived zone (`AWS_STATE.md`, `DL-8`), and the
  project workgroups SMUS provisions publish no metric and set no `BytesScannedCutoffPerQuery`
  (`workgroup-<project>-<env>`, read 2026-10-18). GitLab's host is on the hub dashboard; its disk is not,
  since no host publishes a disk metric.
- **1.2 — [Claude] Write the hub dashboard**: the WireGuard host's state and handshake age, the **proxy's
  request rate, its 403 rate and its top destinations**, and **peering bytes cross-AZ**. The 403 rate
  reads as a design signal rather than a fault: a rising refusal rate means the allow-list is behind the
  work. **Applied 2026-10-18** in `production/observability/`: the host states through their alarms'
  graphs (a stopped host is a gap, a failing one is 1), the handshake age from `/awsds/prod/vpn`'s
  `handshake_age_s=` lines, `Requests` and `Refused` from two metric filters on `/awsds/prod/proxy`, and the
  destinations and refusals as Logs Insights tables with bytes each way. **Peering bytes have no metric**:
  they are a flow-log query over `awsds-prod-networking-vpc-flow-logs` and the spokes' groups, left as
  design.
- **1.3 — [Claude] Point every panel at a `[P]` log group or metric**, never at an `[E]` resource's id
  (Lesson 4) — a dashboard that empties on `make down` is a dashboard nobody trusts afterwards. **Held**:
  every panel reads a `[P]` group, an `AWS/Usage` metric by `[P]` VPC id, a SEARCH over dimension names,
  the warehouse's name or an alarm by name; the observability slices never read a `[D]` state.

### 2. Wire the alarms to a human

**Action:** alarms to the account's `awsds-<env>-alerts` topic (Stage 8 decision 5) for the failures nobody
would otherwise notice. **Why:** D12 deliberately left the budget notifying nobody, and every stage since
has added a thing that can fail quietly. **Explanation:** each alarm names the runbook that answers it, or
it is not worth creating.

- **2.1 — [user] Alarm the budget thresholds.** The D12 budget is a Management console object, and its
  threshold is [Stage 6e](stage-06e-claude-code-bedrock.md) decision 6's (8.3), so this step supplies the
  spend curve and the act is the user's. **The curve, read 2026-10-18 (4.2)**: at least USD 53.31 in August,
  74.48 in September and 56.15 for October 1-17, so D12's revision trigger (*"the first month the real bill
  exceeds the USD 29-43 projection"*) fired in August and nobody was told.
- **2.2 — [Claude] Alarm the hub**: either hub host stopped while a spoke session is up, and the proxy's
  403 rate over a threshold. Both point at [`runbooks/vpn.md`](../runbooks/vpn.md) and `./aws/proxy.py`.
  **Read 2026-10-18**: `awsds-prod-proxy-status-check` is in `ALARM` whenever the hub is stopped, its
  missing data `breaching` by design (`production/proxy/main.tf`), so an action on it as it stands
  would notify at every `make hub-down` (inferred); a hub host stopped while a spoke session is up is
  not the condition that alarm reads. **The `[P]` half applied 2026-10-18**: `awsds-prod-alerts` admits
  `cloudwatch.amazonaws.com` (`CloudWatchAlarmsOfThisAccount`, `aws:SourceArn` on this account's alarms and
  `aws:SourceAccount`), and `awsds-prod-proxy-refusals` alarms at **50 refusals in one hour**: from
  `/awsds/prod/proxy`, September refused 1,597 of 12,829 requests with ten hours at 50 or more, all during
  the allow-lists' build-out, and October 53 of 10,919 with none. `OB-3` reads both new alarms `resolves`.
  **The `[D]` half is owed at the next hub session**: an SNS action on `awsds-prod-vpn-health`,
  `awsds-prod-proxy-status-check` and `awsds-prod-gitlab-status-check`, applied in `production/vpn/`,
  `production/proxy/` and `production/tooling/` with the hosts started, since a `[D]` apply re-plans the
  SSM-resolved AMI and may replace the host; the proxy's alarm waits on decision due 1 first. Sandbox's
  two warehouse alarms take `awsds-sandbox-alerts` since 2026-10-18 (PR #181, `sandbox/warehouse/`
  reading this stage's `alerts_topic_arn`), applied by the orchestrating session. **The
  composite is not built**: no account holds both halves. The hub's state is Production's and a spoke
  session's is Sandbox's or Staging's (each spoke's `InterfaceVPCEndpointsPerVPC`), so the composite needs a
  signal across an account boundary, which this stage does not cross.
- **2.3 — [Claude] Alarm the pipelines and GitLab**: a failed promotion, a GitLab health-check failure, an
  unusual Athena scan volume. **Read 2026-10-18**: GitLab's health check is `awsds-prod-gitlab-status-check`,
  2.2's `[D]` half; an Athena scan volume has no metric while the project workgroups publish none (1.1); a
  failed promotion waits on Stage 10's chain, whose failure rule targets the account's topic.
- **2.4 — [Claude⚡] Apply, then [user] provoke one alarm of each class once** — an alarm that has never
  fired is a configuration, not an alarm (Lesson 13).

### 3. Set log retention everywhere

**Action:** an explicit retention on every log group. **Why:** the default is "forever", which costs money
quietly. **Explanation:** one retention in this estate is floored by a compliance-mode lock, and getting it
wrong is unrecoverable rather than merely expensive.

- **3.1 — [Claude] Set retention on every group this project creates**, including the proxy access log and
  the DNS query logs. **Read ahead on 2026-10-17**: every group the code names has a retention
  (`/awsds/prod/proxy` 365 days); the never-expiring ones are the services' own, 14 in Sandbox and 27.4 MB
  in all (`/aws/sagemaker/studio`, `ProcessingJobs`, each project's `datazone-<project>-dev` pair and eight
  `mwaa-serverless` groups, `EXC-10`), and none in Production, Staging, Data Governance or Identity.
- **3.2 — [Claude] Do not shorten the organization CloudTrail bucket's lifecycle below 90 days.** Its
  objects carry S3 Object Lock in **compliance** mode at 90 days (Stage 1d step 9), and its lifecycle rule
  expires versions at 365. **Shortening it below 90 makes the landing zone's own expirations start failing
  against locked versions, and the lock cannot be shortened to fix it.** 365 → anything ≥ 90 is safe;
  below 90 is unrecoverable (`INV-14`).

### 4. Activate cost allocation and read the first real bill

**Action:** turn on the cost allocation tags and reconcile the invoice against
[`cost-model.md`](../cost-model.md). **Why:** every price in this project is measured (Lesson 6), but the
*quantities* have only ever been projected. **Explanation:** everything else in this stage is
instrumentation around this step.

- **4.1 — [user] Activate the cost allocation tags in Billing** (Management account, console only).
- **4.2 — [Claude] Reconcile the invoice line by line against `cost-model.md`**, and rewrite the model from
  the invoice rather than patching it. **Done 2026-10-18** from Cost Explorer in every account with a
  profile (one `get-cost-and-usage` each, by service and usage type, August 1 to October 17; six requests,
  USD 0.06): **53.31 in August, 74.48 in September, 56.15 for October 1-17**, of which the monthly floor was
  9.90, 32.47 and 21.79 and the sessions 43.22, 41.93 and 34.11. `cost-model.md` is rewritten from those
  lines, each row naming its usage type. **Owed to the user**: Management, Log Archive and Audit, which hold
  no profile; Management's Cost Explorer reads the whole organization in one view, and September's Security
  Hub line alone was about 13.5 there against 4.48 in the accounts read.
- **4.3 — [Claude reads, user decides] Re-open the two estimates most likely to be wrong**: the interface
  endpoints (the largest hourly item, and since 6c there are more VPCs holding them) and GitLab's EBS (the
  largest idle item). Update `conventions.md` §5.1 with measured numbers. **Read 2026-10-18**: the
  endpoints are the bill's largest line, 10.16, 19.92 and 9.70 USD, Sandbox's 1,945 endpoint-hours in
  September being about 108 hours of its 18-endpoint session against the model's 20 lab hours a month;
  the `[D]` volumes billed 1.15, 1.38 and 1.98 (GitLab's 62 GiB since 2026-10-12). The §5.1 edit waits on
  the decision.
- **4.4 — [Claude reads, user decides] Settle the DNS Firewall's per-query bill.** Its job changed at 6c:
  it no longer filters the internet, it closes the recursive resolver as an exfiltration channel. If the
  query charge outweighs what it catches, retiring it is a legitimate outcome — but it is a decision with
  a recorded reason, not a silent deletion. **Read 2026-10-18**: `USW2-DNS-FirewallQueries` and
  `-FirewallDomainName` together billed 0.0417, 0.0152 and 0.0076 USD in Sandbox (64,114, 23,724 and 12,238
  queries) and 0.0001 in Staging in August, so the money does not decide it.

### 5. Re-check the layer assignments against the bill

**Action:** confirm each slice's `[P]`/`[D]`/`[E]` letter still earns itself. **Why:** conventions §5.1
rule 7 says a layer choice is re-opened by measurement, and this is the first measurement.
**Explanation:** the likely movers are a `[D]` whose idle EBS costs more than its rebuild, and an `[E]`
that is up so often it may as well be `[D]`.

- **5.1 — [Claude] Produce the per-slice actual spend** from the invoice plus `make status`' history.
  **The usage-type half, read 2026-10-18** (`cost-model.md`): every line is classed as floor or session
  by its usage type, which maps onto layers without tags (`VpcEndpoint-Hours` is the `egress/` slices,
  `BoxUsage:t3.micro` the proxy, `Studio:VolumeUsage.gp3` the spaces). The per-slice split by tag waits on
  4.1, the user's activation in Management.
- **5.2 — [Claude reads, user decides] Propose any letter changes**, each with the arithmetic beside it.
  **Read 2026-10-20** for open question 4, from 5.1's usage-type half alone, at `docs/PRICING.md`'s
  rates and 730 hours a month: **the bill moves no letter** (decision due 3). Each alternative costs
  more than the letter it would replace, or rests on a restore nobody has timed:

  | Slice | Letter | Alternative | Arithmetic | Reading |
  |---|---|---|---|---|
  | `sandbox/egress/` | `[E]` | `[P]`, never destroyed | 18 endpoints × 0.010 × 730 = 131.40 a month, against 19.45 billed in September (`USW2-VpcEndpoint-Hours`, 1,945 endpoint-hours, about 108 hours of the set) plus at most 7.27 of Sandbox's Config (`docs/PRICING.md` §2) | `[E]`: `[P]` costs 6.8 times September's endpoint line |
  | `production/egress/` | `[E]` | `[P]` | 12 × 0.010 × 730 = 87.60 a month, against 4.35 billed for October 1-17 (435 endpoint-hours) | `[E]` |
  | `production/tooling/` | `[D]` | `[E]`, destroyed and restored at every session | its two volumes, 12 + 50 GiB × 0.08 = 4.96 a month, stopped or running (`USW2-EBS:VolumeUsage.gp3`) | `[D]`: the rebuild is a first boot, 13 min 54 s for the fresh install of 2026-10-12 (Stage 7 step 8.1), and a restore, Stage 7 step 8.2's rehearsal, which has not run |
  | `production/vpn/`, `production/proxy/` | `[D]` | running between sessions | 0.0206/h (`t3.nano` 0.0052, `t3.micro` 0.0104, the proxy's address 0.005): 15.04 for 730 hours, against 2.72 for September's 132 hours (`USW2-BoxUsage:t3.micro`) | `[D]`: 12.32 a month more |
  | `production/vpn/`, `production/proxy/` | `[D]` | `[E]` | saves the two 8 GiB root volumes, 16 × 0.08 = 1.28 a month | `[D]`: each session's rebuild is a first boot (Lesson 68) |
  | `production/runners/` | `[E]` | `[D]`, stopped between sessions | three root volumes, 64 + 30 + 30 GiB × 0.08 = 9.92 a month stopped, against 5.76 billed for the build runner's 27 hours of October 1-17 | `[E]` |

  **Config bills a cycle, not an hour.** A Sandbox `[E]` cycle records 0.36-0.87 USD of configuration
  items whatever its length (`USW2-ConfigurationItemRecorded`), which is 2.0 to 4.8 hours of the set
  at 0.18/h: two sessions less than about two hours apart cost less with `sandbox/egress/` left up
  between them, and more than about five hours apart cost less cycled. It moves no letter: at
  September's 108 hours, `[P]` pays only past about 129 cycles a month at the dearest cycle,
  (131.40 − 19.45) / 0.87. The recorder's scope is step 6's.
  **Two idle lines are not letters.** The hub's largest is the WireGuard Elastic IP, 3.65 a month,
  `[P]` by `conventions.md` §5.1 rule 5, since every client `.conf` names it. GitLab's is the data
  volume's size: its daily snapshot holds about 1 GB of the 50 GiB (`docs/PRICING.md` §3), and EBS does
  not shrink a volume (`production/tooling/variables.tf`), so a smaller one is a migration.

### 6. Review the Config recorder scope against what it actually cost

**Action:** re-read Stage 1d step 10's decision with a bill. **Why:** the recorder was left alone on an
estimate of ~USD 0.5/month, and Management was deliberately left unrecorded. **Explanation:** a Config
conformance pack on top of the Control Tower guardrails is the natural next step **only if** the recorder's
real cost supports it. The first bill reading, 2026-10-14 (`docs/PRICING.md` §2), is USD 10.88 for
September, almost all of it `[E]` cycles at USD 0.36-0.87 per Sandbox `make up` + `make down`: the EC2/ENI
churn Stage 1d decision 4 named as its revision signal.

- **6.1 — [Claude] Read the recorder's actual line** from the invoice. **Done 2026-10-14** (`docs/PRICING.md`
  §2), and re-read 2026-10-18 over the accounts read: `USW2-ConfigurationItemRecorded` 9.61 in August, 10.87
  in September and 9.77 for October 1-17, so October runs above September. A build and its teardown bill
  it too: AWS Config was 0.71 of Staging's USD 1.52 over Stage 18's window (2026-10-17 to 2026-10-21,
  estimated, Cost Explorer read in Staging on 2026-10-22), the configuration items of its creates and
  deletes.
- **6.2 — [Claude reads, user decides] Add conformance packs, or record why not.**

### 7. Tighten the permission sets against real usage

**Action:** narrow `identity/sso/` using IAM Access Analyzer **unused-access** findings. **Why:** a review
reports what a reader thinks the policy says; the analyzer reports what was granted and never exercised.
**Explanation:** the personas were written narrow and then widened by six stages of "the object now
exists"; this is where the widening is paid back.

- **7.1 — [user] Enable an unused-access analyzer, then [Claude] read its findings** — note that it is a
  *different* analyzer from Stage 11's internal-access one, and priced differently. The analyzers are
  Audit's, the `access-analyzer` delegation (`INV-09`), which no profile reaches. **Counted 2026-10-18**:
  147 IAM roles and no IAM user across the `awsds-infra-*` accounts (Sandbox 43, Production 36, Staging 25,
  Data Governance 24, Identity 19), 60 of them service-linked. At USD 0.20 per role or user per month,
  charged at setup and then on the first of each month (the pricing page), one analyzer over these accounts
  is up to 29.40 USD at its creation, whether it is deleted the same day or kept; the page does not say
  whether service-linked roles count. The analyzer's exclusions (accounts, tags) are the cost lever, and
  the scope is the user's decision.
- **7.2 — [Claude] Propose the removals**, then **[Claude⚡] apply `identity/sso/`** as
  `awsds-infra-identity`, `terraform output inline_policy_bytes` still under the ceiling.

### 8. Build backup and recoverability

**Action:** an org-wide AWS Backup plan, Vault Lock over it, cross-region copies, and a **tested** RTO.
**Why:** every earlier stage protected against a permission failure; none protects against deletion.
**Explanation:** an untested backup is a hypothesis, so each restore is walked once — the same discipline
Stage 7 step 8.2 applies to GitLab.

- **8.1 — [Claude] Write the org-wide backup plan** through an Organizations backup policy, covering the
  EBS volumes of the `[D]` instances (GitLab, both hub hosts). **Read ahead on 2026-10-17**: a plan a
  backup policy makes follows the management account's resource opt-in, not the member's ([AWS Backup's
  cross-account page](https://docs.aws.amazon.com/aws-backup/latest/devguide/manage-cross-account.html)),
  so EBS and EC2 are opted in in Management, which `./aws/observability.py` cannot read. **Read
  2026-10-18** (`OB-4`): Production holds no backup plan, and its own opt-in reads EBS and EC2 on; the
  `[D]` hosts' volumes are four, 78 GiB of `gp3` in all (`production/vpn` and `production/proxy` 8 GiB
  each, `production/tooling` 50 GiB of data and 12 GiB of root), and the only snapshots are DLM's of
  the GitLab data volume. **Its prerequisites are Management acts, the user's**: enabling the
  `BACKUP_POLICY` type on the root; trusted access for AWS Backup, an eleventh service principal in
  `INV-09`; a delegation that writes backup policies from Identity, since `INV-15`'s policy-lifecycle
  statement is conditioned on the four types in use; and Management's resource opt-in for EBS and EC2.
  Control Tower's own AWS Backup integration is the alternative, `backup` disabled in the landing zone
  manifest (`INV-17`): it puts its central vault in a Central Backup account and its reports in a Backup
  Administrator account, both in the Security OU, two accounts this estate does not have with the
  account quota spent.
- **8.2 — [Claude⚡] Apply Vault Lock on the backup vault**, so a compromised administrator cannot delete
  the backups. **Read the lock's own irreversibility before applying it** — this is the second
  compliance-mode object in the estate, and 3.2's lesson applies.
- **8.3 — [Claude⚡] Configure cross-region copies** for every account's state bucket and the GitLab backup.
  **It meets the Region ceiling first**: `CT.MULTISERVICE.PV.1` allows `us-west-2` alone on every governed
  OU but `Sandboxes` (`INV-12`), and the landing zone governs that Region alone (`INV-17`), so the
  destination vault or bucket cannot be created in another Region. The copy is cross-account inside
  `us-west-2`, or D1 is re-opened: a decision, recorded before this step is written.
- **8.4 — [user] State and test the RTO, once each**: GitLab, the Terraform state, and the data lake. Write
  the three numbers in the log. GitLab's is Stage 7 step 8.2's rehearsal, which has not run: its
  verification (v), *"in how long?"*, is unanswered.
  **The SageMaker Unified Studio domain is a fourth object with no RTO and no backup**: `DeleteDomain` takes
  `cascadeDelete` since 2026-08-27, one call removing every project, environment and subscription with their
  resources, `aws_datazone_domain` has no such argument, and no SCP on the `Data` OU's path denies
  `datazone:DeleteDomain` (the upstream readings of 2026-10-18, PR #189). What a cascade leaves, this
  repository's buckets and keys included, is unread; the RTO is a rebuild of [6a](stage-06a-unified-studio.md),
  and a deny on the `Data` document would bind the identity that applies the slice too (Lesson 18), so
  whether one is written is the user's.
- **8.5 — [user] Rotate the internal CA's root once, and record the time** ([D36](../decisions/D36-internal-pki.md)
  §6): a new root in `production/pki/`, then every surface that trusts it rebuilt — the `dev-env` image by
  a release, the runners' user data at their next boot, GitLab's `trusted-certs` and the laptop's trust
  (runbook [`gitlab.md`](../runbooks/gitlab.md) §C) — and the measured time in the log. The root lives ten
  years, so this rehearsal is the only time the path is walked before it is needed (Lesson 5). Its
  procedure is written with this step; `gitlab.md` §C holds the leaves' re-issue alone.

### 9. Alarm the quotas that would silently break a session

**Action:** review Service Quotas and alarm the ones with a session-breaking failure mode. **Why:** the
account quota that forced the 2026-09-05 re-scope was discovered by being refused, which is the expensive
way to learn a limit. **Explanation:** the candidates are the ones this estate has actually approached.

- **9.1 — [Claude] Read the current utilisation** for SageMaker instance limits, **Elastic IPs (the default
  is five per Region and the hub holds one, the WireGuard host's, since the proxy took its instance's own
  address at 6g)**, VPC endpoints per VPC, and hosted zones. **Read ahead on 2026-10-17, environment
  down**: Elastic IPs 1 of 5 in Production; interface endpoints 0 of 50 in every VPC, so the reading that
  matters is taken with the environment up; hosted zones 3 of 500 in Production and 1 in Sandbox and in
  Staging. **`OB-5`, 2026-10-18, environment down**: the highest use is gateway endpoints, 6 of 20 in
  Production and 2 of 20 in Sandbox and in Staging; the reading with the environment up is still owed.
  **SageMaker, read 2026-10-18 in every `awsds-infra-*` account** (`list-service-quotas`, 2,417 quotas
  each, 2,324 of them with an `AWS/Usage` usage metric): Sandbox's Studio app quotas read 10 per type for
  the types in use (`L-71FAF417`, `L-2733D4D5`, `L-656A17FA`), processing on `ml.t3.medium` 10, and Stage
  17's three 20, 8 and 8; the other accounts read AWS's default for the same codes, **0 for `ml.m5.xlarge`
  training and for `ml.m5.large` endpoints and transform**, 4 for `ml.t3.medium` processing and 6 for each
  Studio type. The 14 days of usage metrics peak at 3 of 10 apps of one type and 1 processing instance;
  Sandbox's VPC at 24 of 50 interface endpoints; Production's VPCs at 3 of 5 every hour. The Elastic IP
  and gateway-endpoint quotas carry no usage metric.
- **9.2 — [Claude⚡] Set CloudWatch alarms** on each at 80 %, pointing at the request-increase path.
  **Applied in Production 2026-10-18**: `awsds-prod-quota-vpcs-per-region`, the one quota of 9.1 here with
  a usage metric and a measured approach. **Applied in Sandbox the same day** by the orchestrating
  session: five alarms, the three Studio types, the processing type and the VPC's interface endpoints.
  Each alarm
  reads its quota back from Service Quotas by code (Lesson 38), takes the quota's own usage metric and
  divides by `SERVICE_QUOTA()`, so an increase needs no apply. An 80 % alarm cannot see a quota of 0,
  which refuses the first use before any datapoint: reading the quota before a stage's first use is the
  control there, and Staging's and Production's zeros are Stage 9's to read before its first job.

### 10. Write `./aws/observability.py`

**Action:** a read-only instrument for this stage. **Why:** every other stage since 2 is pre-instrumented
and this one is not. **Explanation:** the checks are cheap because the facts are all `describe`-shaped.

- **10.1 — [Claude] Write the checks**: **`OB-1`** every log group this project creates carries an explicit
  retention (the sweep 3.1 is otherwise trusted to have done); **`OB-2`** the CloudTrail bucket's lifecycle
  is ≥ 90 days, which is `INV-14` made mechanical rather than remembered; **`OB-3`** every alarm has a
  notification target that resolves; **`OB-4`** the backup plan covers every `[D]` instance's volume, by
  reading `layers.py`'s `[D]` rows rather than a second list (Lesson 14); **`OB-5`** each quota in 9.1 is
  under 80 % of its limit.
- **10.2 — [Claude] Add it to [`aws/INDEX.md`](../../../aws/INDEX.md)** with its profile and its snapshot
  path, in the same commit as the script.
- **10.1, 10.2 — Written 2026-10-17**, from a cloud session with no AWS credentials:
  [`aws/observability.py`](../../../aws/observability.py), its row, its question table and its section in
  `aws/INDEX.md`. `OB-1` reads the project's groups (the `/awsds/` and `awsds-` namespace, or the
  `Project` tag) apart from the services' own, whose never-expiring groups, 3.1's reading, are a note
  (`EXC-10`). `OB-2` is decided only by the `-` run in Log Archive's CloudShell, where the bucket is, and
  also holds the lifecycle to the lock's own retention. `OB-3` resolves each SNS action to a topic of the
  same account and Region with a confirmed subscription, a policy that admits CloudWatch and a key
  CloudWatch can use. `OB-3` and `OB-4` read `note` until steps 2 and 8 wire their first alarm or write
  their first backup plan, then `fail` per alarm or volume left out (Lesson 50); `OB-4` takes 8.1's plan,
  whose id starts `orgs/`, on its selection alone, since Management's opt-in governs it. `OB-5` adds the
  gateway endpoints' Regional quota to 9.1's list and reads each quota code's name back (Lesson 38).
- **First runs, 2026-10-18** ([log](../../log/log-stage-12-observability-finops.md)): the user's `-` run
  in Log Archive's CloudShell passed `OB-2`, the bucket as `INV-14` records it, and a laptop session's
  run over the five `awsds-infra-*` profiles, the environment down, gave every verdict predicted:
  `OB-1` and `OB-5` pass, `OB-3` a note for Production's three alarms and Sandbox's two, none with an
  action, and `OB-4` a note for the `[D]` hosts' four volumes. No call failed. Validation 4 waits on
  steps 2 and 8.
- **After the Production apply, 2026-10-18**: `OB-3` reads `awsds-prod-proxy-refusals` and
  `awsds-prod-quota-vpcs-per-region` `resolves` (`awsds-prod-alerts`, 1 confirmed subscription, admitted
  by `CloudWatchAlarmsOfThisAccount`, no key), and **fails** in Production and Sandbox for the five alarms
  that still notify nobody, the half-built state Lesson 50 asks the check to name (`EXC-19`). Exit 2, no
  call failed.
- **After the Sandbox apply, 2026-10-18T20:58:19Z**: Sandbox's five quota alarms read `broken`, their
  topic holding *"no confirmed subscription (1 pending)"* until the user confirms the e-mail; the two
  warehouse alarms and Production's three `[D]` hosts' still notify nobody. Exit 2, no call failed.
- **After the warehouse apply, 2026-10-18** (the orchestrating session's reading, `awsds-infra-sandbox-1`):
  Sandbox's seven alarms `broken` on the unconfirmed subscription, the *"notifying nobody"* line gone.
  Production's three `[D]` hosts' alarms are the only unwired ones.
- **After the user confirmed the e-mail subscription, 2026-10-19T02:51:56Z**: `awsds-sandbox-alerts` holds
  one confirmed subscription and none pending, and `OB-3` passes in Sandbox, *"every alarm notifies a topic
  that resolves (7 alarms)"*. Production's three `[D]` hosts' alarms are the only `fail` (`EXC-19`).

---

## Decisions due

1. **The proxy status-check alarm's action** (2.2, the `[D]` half). As it stands the alarm is in `ALARM`
   every hour the hub is stopped, so an SNS action notifies at every `make hub-down`. (a) Wire it as it
   is; (b) make its missing data `notBreaching`, as the tunnel's and GitLab's are, and accept that a
   stopped proxy and a dead one read alike until a session starts it; (c) leave it unwired by decision
   and teach `OB-3` the exception. **Recommended: (b).** Stopping the proxy is D11's idle state rather
   than a failure, and the failure the `breaching` setting guarded against, a session that needs a
   stopped proxy, is already an error: a spoke's `make up` refuses while the proxy is stopped
   (`scripts/slices.py`, 6c step 7.2 as 6g decision 2 left it).
2. **D12's revision trigger fired** (2.1, 4.2): the bill exceeded the projection in August and in
   September. Raising the ceiling, cutting the session hours that dominate the bill, or wiring the budget
   (6e decision 6) are D12's to choose, the user's.
3. **The layer letters** (5.2, open question 4). The bill moves none. (a) Keep every letter; (b) demote
   `production/tooling/` to `[E]`, saving 4.96 a month, once Stage 7 step 8.2 has timed a restore.
   **Recommended: (a)**, with (b) re-read against 8.2's time. The lever the bill names is the session
   hours, decision due 2's.

## Cost

Priced 2026-10-18 from the Price List: the `AmazonCloudWatch` offer for `us-west-2` (published
2026-10-07T11:55:40Z) and the dashboards' global `aws-other` offer (`docs/PRICING.md` §6). Nothing here
bills by the hour.

| What | Count | USD/month |
|---|---|---|
| Dashboards, 3.00 each past the three free ones of up to 50 metrics, counted once per bill | 2 | 0 |
| Standard alarms, 0.10 each past the ten free ones | 7 (5 existed in the readable accounts) | 0.40-0.70 |
| Custom metrics from the two filters, 0.30 each past ten free, metered only for hours with data | 2 | 0 |
| The Sandbox topic, its e-mails and the Logs Insights scans of a dashboard view | 1 | 0 |

The low end assumes Management's two alarms, `RootActivityCount` (Stage 1a) and `IdentityCenterChangeCount`
(Stage 1b), are the only others; the high end bills every new alarm. A fourth dashboard anywhere in the
organization would cost 3.00 a month.

## Deliverables

- Dashboards per environment and one for the hub, every panel on a `[P]` source.
- Alarms wired to a human, each provoked once.
- Explicit retention on every log group, with `INV-14`'s floor respected.
- **`cost-model.md` rewritten from an invoice** rather than patched — the stage's central artifact.
- A backup plan with Vault Lock, cross-region copies, and three tested RTO numbers.
- **`./aws/observability.py`** — the mechanical half this stage did not have.

## Validation

1. Provoke one alarm per class and confirm the notification arrives (2.4).
2. Restore one backup of each kind (8.4) — a restore that has never run is not a backup.
3. Diff `cost-model.md` before and after 4.2; every changed row names the invoice line that changed it.
4. Run `./aws/observability.py`, and `python3 aws/observability.py -` in Log Archive's CloudShell for
   `OB-2` — `OB-1`..`OB-5` pass.

## Risks

- **Shortening the CloudTrail lifecycle below the 90-day lock is unrecoverable** (3.2, `INV-14`).
- **Vault Lock is the second irreversible control in the estate** — read its own documentation on the
  compliance-mode transition before applying, not after.
- **A dashboard on an `[E]` id empties at the first `make down`** (Lesson 4) — 1.3 is the control.
- **The unused-access analyzer bills per resource** like Stage 11's internal-access one; read the price
  before enabling it standing (Lesson 6).

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
