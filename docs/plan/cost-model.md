# Cost model of the lab

The projection and its assumptions. **Authoritative per-unit rates live in [`docs/PRICING.md`](../PRICING.md)**, measured from the AWS Price List bulk API — never estimated here.
The operating model that produces these numbers is `docs/plan/conventions.md` §5.1.

---

## 5. Cost model

Because of D11 the relevant question is not "what does this cost per month" but "what is the floor when
nothing is running, and what does an hour of lab time add on top". Order-of-magnitude figures for
`us-west-2`, to be confirmed with the AWS Pricing Calculator before each stage.

**The floor — paid every month even with the lab shut down (~USD 25-34):**

| Item | Approx. USD/month | Note |
|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | 0 | These cost nothing at rest, so there is no reason to destroy them |
| GitLab EBS volume (50 GB gp3) | ~4.00 | Paid while the instance is stopped; this is the price of not rebuilding GitLab |
| Elastic IP for WireGuard | ~3.65 | All public IPv4 addresses are charged hourly, attached or not |
| KMS customer-managed keys | ~9.00 → ~10.00 → **~13.00** | ~1.00 per key **version** per month — the unit is a version and `docs/PRICING.md` §2 carries the rule; **the count below is a year-one figure**, because every key here rotates at the 365-day default and a rotation adds a version. The set at N=1: one per Terraform-managed account (Sandbox, Development, Data Governance, Staging, Production, Identity) plus a **dedicated derived-zone key in each Interactive account** (D31 — the key policy is what says who may read materialised `restricted` data, and it only works as a control if the key is not also serving state and logs). **Applied 2026-08-19 and the count is unchanged — only the naming moved, twice in one day**: those two keys are `alias/awsds-sandbox-data` and `alias/awsds-dev-data` — first named `-zn-lab` for the `security-zone` dimension, then renamed the same day when the user's revision **withdrew that dimension entirely**: encryption is **one data CMK per account** (`GOVERNANCE.md` §Encryption), no catalog attribute involved. `scratch` needed no key of its own: it is a prefix in the same bucket, not a bucket plus **D36's second state key, `alias/awsds-prod-tfstate-pki`** — created by `production/bootstrap/` on 2026-08-15, **not** by `production/pki/`, which has never existed and arrives at Stage 7 pass 1 (same reasoning applied to the CA root: a key shared with `foundation/` would put the root back inside the blast radius the slice exists to leave). **Three more landed on 2026-08-21 with Stage 6's passes 0 and 1, and this row had no clause any of them matched** — the supply-chain key `alias/awsds-prod-registry` (`production/registry/`, D14's option preservation: if the supply chain ever moves account, the slice leaves and takes its key with it) and **one project key per Interactive account**, `alias/awsds-<env>-project`, created by `terraform-modules/sagemaker-prereqs/` for the resources a blueprint provisions — which is NOT the account's data CMK, and `docs/GOVERNANCE.md` §Encryption's rule says why in as many words: one data key per account is one key for *data*, not a merger of every key in the account. **The open half of this row is settled and it cost exactly one key** (2026-08-18, Stage 5 decision 2, applied the same day): the lake takes **one** CMK, `alias/awsds-data-data`, covering all five `awsds-data-*` buckets including the drop-box — one data key per account, and the Data Governance account holds the lake. The old sentence here, "a CMK per data domain, Stage 5 step 1", described a design that no longer exists. **It stays a floor rather than a count for one reason only**, and it is now a named one: the first dataset whose blast radius argues for a key of its own is a second key, and Bucket Keys make that a bucket-level change rather than a migration |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~2.5-5 → **measured ~0.5** | **Measured 2026-08-14 (Stage 1d step 10) and the estimate was high by a factor of five, for a reason worth keeping: this row assumed a rate where the cost is an event.** Cost Explorer shows a single usage type, `USW2-ConfigurationItemRecorded` — **no rule evaluations at all** — totalling USD 2.28 month-to-date, of which USD 2.20 is one enrollment-day spike. The recurring remainder is ~USD 0.5/month at nine accounts. **An idle account bills almost nothing**; what bills is change. **One recorder per governed account — every account except Management** (D20-D22, D29 — `Policy Canary` is empty, but an enrolled account still carries a recorder, and enrolling it is what makes the policy test meaningful); **Management is confirmed unrecorded** — 1d 10.4 read an empty recorder *and* an empty delivery channel there, and the aggregator lists eight accounts, so this row's account count was right and verification (xiii) is closed. This row scales with the account count *and* with churn, so it is the line to re-read whenever an account is added or a build-out starts. **The last sentence this row used to carry is now falsified: restricting the recorded resource types is *not* the main cost lever.** Each account records 80-82 resources, a third of them AWS service defaults recorded once and never changed, so the entire exclusion list is worth under a dollar across the organization — **decision 4 declined it**. **Nor is `recordingFrequency: DAILY` a lever in this direction**: `docs/PRICING.md` §2 prices it at USD 0.012 per item-day against USD 0.003 per change, so it pays only above four changes per resource per day and would multiply this row rather than divide it |
| Route 53 **private** hosted zones (D15) | ~1.00-1.50 | USD 0.50/zone-month. **Three at N=1** (Stage 3 step 4.2): `sandbox.internal` — the one that multiplies with the business units — plus `prod.internal` and `pages.internal`, both owned by Production. **Development and Staging get none**: nothing in either is addressed by a private name, so a zone per VPC-bearing account would be USD 1.00/month resolving nothing. **No public zone before Stage 13** — D15 was revised on 2026-08-09 and the split-horizon design was dropped |
| Public domain + public hosted zone (D15 phase 2) | **0 until Stage 13**, then ~1.50 | ~USD 12-15/year amortised plus USD 0.50/zone-month. Registered only when the public web tier exists |
| Certificates (D15 phase 1) | **0** | The internal CA is generated by Terraform and its leaves are *imported* into ACM; ACM charges nothing for imported certificates. AWS Private CA (~USD 400/mo, ~USD 50/mo short-lived) is what this avoids |
| CodeArtifact | ~0.10 | USD 0.05/GB-month storage plus USD 0.05 per 10k requests; negligible at lab scale |
| Security Hub + IAM Access Analyzer | ~1-2 | **Access Analyzer external-access findings are free and are enabled in Stage 1b**; Security Hub charges per check and per finding and is enabled in **Stage 5 step 13**, with the first governed data (principle 9, as amended). Its checks run as Config rules, so it also nudges the Config row up. **Access Analyzer's other two finding types are not free and are not in this number**: *internal access* bills per resource monitored per month and is decided in **Stage 11 step 2.1** (scoped to the Data Governance and derived-zone buckets, not every bucket), *unused access* bills per principal per month in **Stage 12**. **Both measured 2026-08-17 (`docs/PRICING.md` §6): internal access USD 9.00 per resource-month, charged at setup** — the rate that made Stage 11's analyzer a create-read-delete instrument rather than a standing monitor — and unused access USD 0.20 per role/user-month |
| GuardDuty | 0 → ~3-5 | Enabled in **Stage 15** (Stage 4 step 10 until the 2026-08-18 split — the deferral is deliberate, its trade argued in `institutional-delta.md`). Free for the first 30 days per account, then driven by CloudTrail/VPC flow/DNS log volume. **Every optional protection plan arrives ON and Stage 15 step 3 switches them off**; the paid pair is decided in Stage 11 step 4, and they are the ones to watch against the ceiling |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |
| SageMaker unified domain — DataZone V2 metadata (D26) | ~0.50 | Requests USD 10 per 100k, metadata storage USD 0.40/GiB-month, global rates (`docs/PRICING.md`); cents at lab scale. The cost lever is which blueprints exist, not the domain itself |
| Staging, Development and Data Governance accounts at rest (D20-D22) | **0 (already counted)** | **This row is now a pointer, not a cost.** It used to add ~USD 3 for "a Config recorder and a KMS key per account" — but the Config row above already covers every governed account and the KMS row already counts every key, so charging these accounts again was a double count of ~USD 3. What is worth keeping is the *shape*: VPCs, buckets and IAM roles are free at rest; Staging's metered slice exists only during a promotion, Development's only while someone is working, and Data Governance has no metered slice at all — its data plane is serverless (the lake storage is in the S3 row above) |
| **Floor** | **~USD 25-34** | **The 2026-08-09 DNS revision is roughly neutral on this row and does not move the range:** −USD 1.00 for the domain and public zone, now deferred to Stage 13 (D15 phase 2), +USD 0.50 for the extra `pages.internal` zone, +USD 1.00 for the PKI key (D36). Net ≈ +USD 0.50. **A second, smaller movement since: +USD 1.00 for the lake CMK, applied 2026-08-18 (the KMS row's settled count) — the first row in this table that a build actually moved rather than a plan revision.** **And a third, 2026-08-21: +USD 3.00 for Stage 6's three CMKs** — `alias/awsds-prod-registry` and the two `alias/awsds-<env>-project` keys, taking the KMS row from ten to thirteen. **The range is deliberately NOT moved by adding 3**, and the reason is this row's own standing instruction: two independent re-sums of `docs/PRICING.md` §2's `us-west-2` column during the 2026-08-21 review disagreed on the base (25.25 against 25.75 — the gap is the DataZone row, added after the 2026-08-08 recompute), on top of an unapplied −USD 2-4.5 Config correction this row already holds back. A range whose base is uncertain by half a dollar cannot be corrected one row at a time. **Recompute the whole range at Stage 12 step 5, from the invoice** — and note that by then the KMS row is no longer a year-one figure (`docs/PRICING.md` §2's key-version rule). Up from the ~USD 15 first estimate: mostly the detective controls, plus the recorder for D29's disposable account. The low end is the first thirty days, while GuardDuty is still inside its free window; the high end is an ordinary month with GuardDuty billing and Config recording an active build-out. **Security Hub has a free window of its own, read 2026-08-20 and worth stating because the two do not overlap in time**: 30 days per account from *first enablement*, which for Security Hub starts at Stage 5 step 13 and for GuardDuty at Stage 15 — so "the first thirty days" is not one window the whole floor sits inside, it is two, opening at different stages. What the trials hide is only the *service* line; the **Config** cost they sit on top of starts immediately, because each control's compliance-state change writes an `AWS::Config::ResourceCompliance` item. **This is the *steady-state* floor. During the build-out it is lower — roughly ~USD 24-27 before Stage 5 — because Security Hub does not exist until Stage 5, and GuardDuty not until Stage 15 (the 2026-08-18 split), so the GuardDuty row joins the floor last of all** (principle 9, as amended: detection is enabled when there is something to detect). **Recomputed 2026-08-08 by summing the measured `us-west-2` column of `docs/PRICING.md` §2** — the "~USD 21-27" and "~USD 24-30" this row and its header used to carry both predated D29/D31 and both understated it. **What is still not in this row**, and is already decided elsewhere in the plan: the two Secrets Manager secrets — the VPN host key (Stage 4 decision 4, third review) and `gitlab-secrets.json` (Stage 7 step 1), the CloudWatch alarms the plan requires (root sign-in, the two deploy roles, the catalog-maintenance role, VPN, GitLab, budget — at USD 0.10 each this is ~USD 1-1.50), AWS Backup storage and Vault Lock (Stage 12 step 8), and the growth of the Object-Locked Log Archive bucket. Expect the measured floor at Stage 12 step 5 to land above this range, not below it. **The first row to be measured against a real bill moved down, not up** (Config, 2026-08-14: ~2.5-5 projected, ~0.5 billed), which takes ~USD 2-4.5 off the range as written — **not applied here on purpose**, because that row is churn-sensitive and this floor is a steady-state number for a lab that has not been built yet. Recompute the whole range at Stage 12 step 5, from the invoice, rather than adjusting it one row at a time |

**What a second business unit adds to the floor (D35).** Every row above is written for one Sandbox, and
`Sandbox` is the one account that multiplies. The terms a unit brings with it, and they are all rows that
already exist here rather than new kinds of cost: **one account** (free at rest, but one slot against the
organization quota), **one AWS Config recorder** — the row above already says it scales with the account
count, and this is the thing that makes it scale — **three KMS CMKs** at ~USD 1.00 each (the `tfstate` key, the
D31 account data key, and the project CMK `alias/awsds-<env>-project` that the unit's `sagemaker/` slice
creates — a unit's Sandbox is an Interactive account, so it is both a data consumer and a host for SMUS
projects), and, on the hourly side and
dominating everything else, **one full set of interface VPC endpoints**: 12 under design A, 14 under B, at
~USD 0.010/h each, so ~USD 0.12-0.14 per hour that unit is working. So a unit is roughly **+USD 3.5-5.5 on the floor** and **+~USD 0.16
per active hour** — against a USD 50 ceiling whose planning number already has about USD 7 of headroom, which
means the **second** unit is affordable and the third is a budget decision, not a formality.

**Do not treat those figures as measured.** They are the existing measured rates in `docs/PRICING.md` re-summed
for one more account; the per-unit total is measured properly at [Stage 14](stages/stage-14-sandbox-vending.md),
before the first vended unit rather than after it (Lesson 6). The number to watch there is the endpoint
row, because it is what decides whether **centralized interface endpoints shared by RAM** stop being the
institutional answer (`docs/plan/institutional-delta.md`) and become the arithmetic one — per-account endpoints
multiplied by account count is already the largest hourly item in this table.

Two cost levers worth applying rather than discovering later:

- **S3 Bucket Keys** on every SSE-KMS bucket. They cut KMS request charges by up to ~99%, and a data
  environment issues a KMS request per object operation — without this, KMS requests can quietly exceed
  the cost of the keys themselves. Free to enable; set it in the `s3-bucket` module from Stage 2.
- **Scope Macie deliberately** (Stage 11). Macie charges per GB inspected for sensitive-data discovery. Run
  it against a sampled prefix, not the whole lake, or it becomes the largest single line item in the
  project. The same caution applies to **CloudTrail S3 data events**, which bill per event: a single Spark
  job listing and reading thousands of objects generates a matching number of events.

**Per hour of lab time — added while the environment is up:**

| Item | Approx. USD/h |
|---|---|
| NAT Gateway (1) + its public IPv4 | ~0.050 + 0.045/GB processed — **zero under egress design B** (`docs/plan/architecture.md` §4.3) |
| **Interface VPC endpoints — per account, single AZ (D9)** | ~0.010 each. The list is per account role, not one list (Stage 3 step 8): **Sandbox** 12 (14 under design B; 11/13 between 2026-08-17, when `elasticfilesystem` left with the NFS requirement, and 2026-08-21, when `datazone` joined at Stage 6 step 4.2), **Development** 12 (14), **Staging** 9, **Production** 10-12. Double if spread across 2 AZs. **The Sandbox line is per business unit (D35)** — this is the term that multiplies |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| Internal ALB in front of GitLab/Pages (only while GitLab is up) | ~0.023 + LCU usage |
| **Production `egress/`** (only while runner builds or orchestration need it) | NAT ~0.050 + **endpoints ~0.100-0.120** — the endpoint half was missing from every earlier version of this table |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| WireGuard EC2 `t3.nano` | ~0.005 (`t4g.nano` at ~0.004 until the amd64 move of 2026-08-20; a `t3.medium` session is ~0.042) |
| Sandbox ↔ Production **and** Development ↔ Production VPC peering (two of them, D21) | free within an AZ; USD 0.01/GB each way across AZs — see `docs/plan/open-questions.md` item 3 |
| **Staging `egress/` during a promotion run** (D20) | ~0.140/h, but measured in *minutes* per promotion, not hours — `make up ENV=staging` is a pipeline step, and the pipeline tears it down. Budget ~USD 0.03 per promotion, not a standing hourly cost |
| **Development `egress/` + Studio apps** (D21) | ~0.160/h under design A (0.170 until the 2026-08-25 `datazone` removal), ~0.140 under B — which must re-add that endpoint, plus ~0.05/h per running app — but only while pipeline-engineering work is happening. A session is either exploratory (Sandbox up) or engineering (Development up), so the *typical* hourly burn does not double even though the worst case does |
| Athena, Glue | usage-based; negligible at lab scale |

**Two corrections to this table, applied 2026-08-08, and both moved the numbers up.**

- **The data plane had no endpoints.** `athena`, `glue` and `lakeformation` were missing from every
  account. Under design A the NAT hid it; under design B, with no NAT anywhere, it meant the design could
  not run a query at all — D13 routes every tabular read through an LF-aware engine. They are now in the
  **common core of both designs**, which is why both got more expensive: a Sandbox hour goes from ~0.14
  to ~0.170 under A and from ~0.11 to ~0.140 under B — the lists as then counted. The A figure has moved
  twice since: `elasticfilesystem` out on 2026-08-17 (D24 withdrawn), `datazone` in on 2026-08-21 (Stage 6
  step 4.2) and **out again on 2026-08-25** (issue #39), so **A reads 0.160 today**. B stays 0.140: the
  endpoint A just dropped is one B has to keep, having no NAT to reach DataZone through.
- **The gap between the designs survived the correction, and now rests on the right thing.** B is cheaper
  by exactly ~USD 0.030/h — the NAT and its address (0.050) less the two CodeArtifact endpoints (0.020) —
  in every account, for every list. The older claim that B trades the NAT for two endpoints and comes out
  ahead was right; it was just measured against a list that could not have executed a query. **The
  Stage 6 comparison is still not settled by this**: three cents an hour is a rounding error next to the
  friction D5 exists to measure.

**Projection:** ~USD 25-34 floor + 20 h/month × ~USD 0.18-0.45 (the lower end is a Sandbox hour under
design B; the upper a full-stack hour under design A: GitLab, its ALB, a runner build with Production's
endpoints, and one Interactive environment all at once) + a handful of promotions at ~USD 0.03 each ≈
**USD 29-43/month**, against the USD 50 ceiling (D12). **Read the top of that range as the planning
number, not the bottom** — it leaves roughly USD 7 of headroom, and the items listed as missing from the
floor row eat into it. Staging and Data Governance cost almost nothing precisely because neither ever has
standing compute; the number to watch is whether Sandbox and Development sessions actually stay disjoint,
which is what keeps the hourly line from doubling.
The single fastest way to breach the ceiling is a session that leaves `egress/` up: at ~USD 0.160/h that is
USD 3.84 for a forgotten day, and two of them cancel the entire headroom. **This used to say that the budget
alerts and Cost Anomaly Detection of Stage 1a step 2 are the primary control here; both were skipped by
decision on 2026-08-09, so there is no automatic control over it at all** — the exposure is carried by the
teardown discipline of the `[E]` layer (D11) and by whoever remembers to open Cost Explorer. Two forgotten
days are therefore detected at the end of the month, not on the day they happen.
Design B trades the NAT gateway for two CodeArtifact endpoints, so it is the *cheaper* of the two egress
options as well as the stricter one — which is worth knowing before the Stage 6 comparison starts.

**What the ceiling rules out:** always-on GitLab (~USD 60/month on its own), AWS Client VPN
(~USD 73/month, the D4 alternative), Network Firewall (~USD 290/month, option D5c) and an always-on MWAA
environment (~USD 212/month for `mw1.micro`, ~USD 358/month for `mw1.small` — D7 alternative A). Any of
these becomes affordable only as a short, deliberate experiment — which is precisely what the operating
model below is for. **D7 now commits to building MWAA rather than merely documenting it**, and this is the
line it has to respect: the environment is `[E]`, it exists for the length of a comparison run, and at
`mw1.micro` an eight-hour experiment costs ~USD 2.30. **MWAA Serverless** (USD 0.088 per task-hour, no
environment fee) removes the exposure entirely and is therefore the variant to try first. Authoritative
per-unit rates, for both `us-west-2` and `sa-east-1`, are in `docs/PRICING.md`. The same discipline applies
inside the unified domain (D26): the Lakehouse blueprint is enabled in its Glue/Athena form only — its
**Redshift Serverless** variant would put a second, larger query bill on top of Athena's, and it is
excluded by decision, not by omission.

**Guardrail:** AWS Budgets with e-mail alerts must exist before any compute is created (Stage 1).

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
