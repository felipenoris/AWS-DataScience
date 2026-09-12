# Cost model of the lab

The projection and its assumptions. Per-unit rates live in [`docs/PRICING.md`](../PRICING.md), measured
from the AWS Price List bulk API and never estimated here.
The operating model that produces these numbers is `docs/plan/conventions.md` §5.1.

---

## 5. Cost model

Under D11 the question is the floor when nothing is running, plus what an hour of lab time adds on top.
Order-of-magnitude figures for `us-west-2`, to be confirmed with the AWS Pricing Calculator before each
stage.

The floor, paid every month even with the lab shut down (~USD 25-34):

| Item | Approx. USD/month | Note |
|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | 0 | These cost nothing at rest, so there is no reason to destroy them |
| GitLab EBS volume (50 GB gp3) | ~4.00 | Paid while the instance is stopped; this is the price of not rebuilding GitLab |
| Elastic IP for WireGuard | ~3.65 | All public IPv4 addresses are charged hourly, attached or not |
| KMS customer-managed keys | ~9.00 → ~10.00 → **~13.00** | ~1.00 per key **version** per month; the unit is a version and `docs/PRICING.md` §2 carries the rule. The count is a year-one figure, because every key here rotates at the 365-day default and a rotation adds a version. The set at N=1: one per Terraform-managed account (Sandbox, Data Governance, Staging, Production, Identity — **five since 2026-09-06**, when `awsds-dev-tfstate`'s key was scheduled for deletion at Stage 6b step 4.7 and the account it belonged to became Staging); plus a **data key in each Interactive account** (D31), `alias/awsds-sandbox-data` and `alias/awsds-dev-data`, applied 2026-08-19 — created for the derived zone, which left them on 2026-08-26 (D19 revised: Sandbox's now serves the sandbox lake, Development's is held empty, and the who-may-read control moved to the project CMKs already counted in this row; the keys stay, so the count does not move). Encryption is **one data CMK per account** (`GOVERNANCE.md` §Encryption), with no catalog attribute involved; `scratch` needs no key of its own, being a prefix in the same bucket rather than a bucket. Plus **D36's second state key, `alias/awsds-prod-tfstate-pki`** — created by `production/bootstrap/` on 2026-08-15, not by `production/pki/`, which has never existed and arrives at Stage 7 pass 1 (a key shared with `foundation/` would put the CA root back inside the blast radius the slice exists to leave). Three more landed on 2026-08-21 with Stage 6's passes 0 and 1: the supply-chain key `alias/awsds-prod-registry` (`production/registry/`, D14's option preservation — if the supply chain ever moves account, the slice leaves and takes its key with it) and **one project key per Interactive account**, `alias/awsds-<env>-project`, created by `terraform-modules/sagemaker-prereqs/` for the resources a blueprint provisions. A project key is not the account's data CMK: one data key per account is one key for *data*, not a merger of every key in the account (`docs/GOVERNANCE.md` §Encryption). The lake takes **one** CMK, `alias/awsds-data-data`, covering all five `awsds-data-*` buckets including the drop-box (Stage 5 decision 2, 2026-08-18, applied the same day) — one data key per account, and the Data Governance account holds the lake. It stays a floor rather than a count: the first dataset whose blast radius argues for a key of its own is a second key, and Bucket Keys make that a bucket-level change rather than a migration |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~2.5-5 → **measured ~0.5** | **Measured 2026-08-14** (Stage 1d step 10); the estimate was high by a factor of five because this row assumed a rate where the cost is an event. Cost Explorer shows a single usage type, `USW2-ConfigurationItemRecorded` — no rule evaluations at all — totalling USD 2.28 month-to-date, of which USD 2.20 is one enrollment-day spike. The recurring remainder is ~USD 0.5/month at nine accounts. An idle account bills almost nothing; what bills is change. **One recorder per governed account — every account except Management** (D20-D22, D29 — `Policy Canary` is empty, but an enrolled account still carries a recorder, and enrolling it is what makes the policy test meaningful). Management is confirmed unrecorded: 1d 10.4 read an empty recorder *and* an empty delivery channel there, and the aggregator lists eight accounts, so this row's account count was right and verification (xiii) is closed. The row scales with the account count *and* with churn, so re-read it whenever an account is added or a build-out starts. Restricting the recorded resource types is **not** the main cost lever: each account records 80-82 resources, a third of them AWS service defaults recorded once and never changed, so the entire exclusion list is worth under a dollar across the organization — decision 4 declined it. Nor is `recordingFrequency: DAILY` a lever in this direction: `docs/PRICING.md` §2 prices it at USD 0.012 per item-day against USD 0.003 per change, so it pays only above four changes per resource per day and would multiply this row rather than divide it |
| Route 53 **private** hosted zones (D15) | **2.50** | USD 0.50/zone-month. **Five since 2026-09-08**: the `awsds.internal` family Stage 6c pass 2 created — the apex plus `sandbox.`, `staging.` and `prod.` children — and `awsds-pages.internal` (`prod.internal` and `pages.internal` were destroyed at 2.6 on 2026-09-07, `sandbox.internal` at 6.5 on 2026-09-08). Zones cannot be renamed, so the two families coexist by construction. The steady state is five, and the apex multiplies with the business units rather than a per-unit apex of its own — one child zone per Sandbox, +USD 0.50/month each. **Staging gets none**: nothing in it is addressed by a private name, so a zone per VPC-bearing account would be USD 1.00/month resolving nothing. No public zone before Stage 13 (D15 revised 2026-08-09; the split-horizon design was dropped) |
| Public domain + public hosted zone (D15 phase 2) | **0 until Stage 13**, then ~1.50 | ~USD 12-15/year amortised plus USD 0.50/zone-month. Registered only when the public web tier exists |
| Certificates (D15 phase 1) | **0** | The internal CA is generated by Terraform and its leaves are *imported* into ACM; ACM charges nothing for imported certificates. AWS Private CA (~USD 400/mo, ~USD 50/mo short-lived) is what this avoids |
| CodeArtifact | ~0.10 | USD 0.05/GB-month storage plus USD 0.05 per 10k requests; negligible at lab scale |
| Security Hub + IAM Access Analyzer | ~1-2 | Access Analyzer external-access findings are free and are enabled in Stage 1b; Security Hub charges per check and per finding and is enabled in **Stage 5 step 13**, with the first governed data (principle 9, as amended). Its checks run as Config rules, so it also nudges the Config row up. Access Analyzer's other two finding types are not free and are not in this number: *internal access* bills per resource monitored per month and is decided in **Stage 11 step 2.1** (scoped to the Data Governance and derived-zone buckets, not every bucket); *unused access* bills per principal per month in **Stage 12**. Both measured 2026-08-17 (`docs/PRICING.md` §6): internal access **USD 9.00 per resource-month, charged at setup** — the rate that made Stage 11's analyzer a create-read-delete instrument rather than a standing monitor — and unused access USD 0.20 per role/user-month |
| GuardDuty | 0 → ~3-5 | Enabled in **Stage 15** (Stage 4 step 10 until the 2026-08-18 split; the deferral's trade is argued in `institutional-delta.md`). Free for the first 30 days per account, then driven by CloudTrail/VPC flow/DNS log volume. Every optional protection plan arrives on, and Stage 15 step 3 switches them off; the paid pair is decided in Stage 11 step 4, and they are the ones to watch against the ceiling |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |
| SageMaker unified domain — DataZone V2 metadata (D26) | ~0.50 | Requests USD 10 per 100k, metadata storage USD 0.40/GiB-month, global rates (`docs/PRICING.md`); cents at lab scale. The cost lever is which blueprints exist, not the domain itself |
| Staging and Data Governance accounts at rest (D20-D22) | **0 (already counted)** | The Config row above covers every governed account and the KMS row counts every key, so charging these accounts again was a double count of ~USD 3. The shape: VPCs, buckets and IAM roles are free at rest; Staging's metered slice exists only during a promotion, Development's only while someone is working, and Data Governance has no metered slice at all — its data plane is serverless (the lake storage is in the S3 row above) |
| **Floor** | **~USD 25-34** | Movements held back from the range: the 2026-08-09 DNS revision is roughly neutral (−USD 1.00 for the domain and public zone, deferred to Stage 13 under D15 phase 2; +USD 0.50 for the extra `pages.internal` zone; +USD 1.00 for the PKI key, D36 — net ≈ +USD 0.50); **+USD 1.00 for the lake CMK, applied 2026-08-18** (the KMS row's settled count, and the first row here a build moved rather than a plan revision); **+USD 3.00 on 2026-08-21 for Stage 6's three CMKs** — `alias/awsds-prod-registry` and the two `alias/awsds-<env>-project` keys, taking the KMS row from ten to thirteen; and **+USD 2.50/month of private hosted zones on 2026-09-06** — Stage 6c pass 2 created five, and three more stand until 6c step 2.6 retires them, so the transient is +4.00 and the steady state +2.50. The range is not corrected one row at a time because its base is uncertain: two independent re-sums of `docs/PRICING.md` §2's `us-west-2` column during the 2026-08-21 review disagreed (25.25 against 25.75 — the gap is the DataZone row, added after the 2026-08-08 recompute), on top of an unapplied −USD 2-4.5 Config correction (measured 2026-08-14: ~2.5-5 projected, ~0.5 billed, held back because that row is churn-sensitive and this floor is a steady-state number for a lab that has not been built yet). **Recompute the whole range at Stage 12 step 5, from the invoice** — by then the KMS row is no longer a year-one figure (`docs/PRICING.md` §2's key-version rule). Up from the ~USD 15 first estimate: mostly the detective controls, plus the recorder for D29's disposable account; recomputed 2026-08-08 by summing the measured `us-west-2` column of `docs/PRICING.md` §2, which the earlier "~USD 21-27" and "~USD 24-30" both understated. The low end is the first thirty days, while GuardDuty is still inside its free window; the high end is an ordinary month with GuardDuty billing and Config recording an active build-out. Security Hub has a free window of its own (read 2026-08-20): 30 days per account from *first enablement*, which for Security Hub starts at Stage 5 step 13 and for GuardDuty at Stage 15 — two windows opening at different stages, not one the whole floor sits inside. The trials hide only the *service* line; the **Config** cost underneath starts immediately, because each control's compliance-state change writes an `AWS::Config::ResourceCompliance` item. This is the **steady-state** floor: during the build-out it is lower, roughly ~USD 24-27 before Stage 5, because Security Hub does not exist until Stage 5 and GuardDuty not until Stage 15 (the 2026-08-18 split), so the GuardDuty row joins the floor last of all (principle 9, as amended: detection is enabled when there is something to detect). **Not in this row**, and decided elsewhere in the plan: the two Secrets Manager secrets — the VPN host key (Stage 4 decision 4, third review) and `gitlab-secrets.json` (Stage 7 step 1) — the CloudWatch alarms the plan requires (root sign-in, the two deploy roles, the catalog-maintenance role, VPN, GitLab, budget — at USD 0.10 each, ~USD 1-1.50), AWS Backup storage and Vault Lock (Stage 12 step 8), and the growth of the Object-Locked Log Archive bucket. Expect the measured floor at Stage 12 step 5 to land above this range, not below it |

**What a second business unit adds to the floor (D35).** Every row above is written for one Sandbox, and
`Sandbox` is the one account that multiplies. A unit brings **one account** (free at rest, but one slot
against the organization quota), **one AWS Config recorder** — what makes the row above scale with the
account count — **three KMS CMKs** at ~USD 1.00 each (the `tfstate` key, the D31 account data key, and the
project CMK `alias/awsds-<env>-project` that the unit's `sagemaker/` slice creates; a unit's Sandbox is an
Interactive account, so it is both a data consumer and a host for SMUS projects), and, dominating
everything on the hourly side, **one full set of interface VPC endpoints**: **18** as built (6c step 5.2,
counted from the slice's plan; no NAT anywhere), at ~USD 0.010/h each, so USD 0.18 per hour that unit is
working. A unit is roughly **+USD 3.5-5.5 on the floor** and **+~USD 0.23 per active hour** (endpoints plus
one `ml.t3.medium` app), against a USD 50 ceiling whose planning number has about USD 7 of headroom: the
second unit is affordable and the third is a budget decision.

Those figures are not measured: they are the measured rates in `docs/PRICING.md` re-summed for one more
account. The per-unit total is measured at [Stage 14](stages/stage-14-sandbox-vending.md), before the first
vended unit rather than after it (Lesson 6). Watch the endpoint row there: it decides whether
**centralized interface endpoints shared by RAM** stop being the institutional answer
(`docs/plan/institutional-delta.md`) and become the arithmetic one — per-account endpoints multiplied by
account count is already the largest hourly item in this table.

Two cost levers worth applying rather than discovering later:

- **S3 Bucket Keys** on every SSE-KMS bucket. They cut KMS request charges by up to ~99%, and a data
  environment issues a KMS request per object operation — without this, KMS requests can quietly exceed
  the cost of the keys themselves. Free to enable; set it in the `s3-bucket` module from Stage 2.
- **Scope Macie deliberately** (Stage 11). Macie charges per GB inspected for sensitive-data discovery. Run
  it against a sampled prefix, not the whole lake, or it becomes the largest single line item in the
  project. The same caution applies to **CloudTrail S3 data events**, which bill per event: a single Spark
  job listing and reading thousands of objects generates a matching number of events.

Per hour of lab time — added while the environment is up. Priced on the zero-NAT basis, from endpoint sets
counted at [6c](stages/stage-06c-networking-hub.md) step 7.4:

| Item | Approx. USD/h |
|---|---|
| ~~NAT Gateway (1) + its public IPv4~~ | **Gone from every account.** Zero NAT gateways exist ([D38](decisions/D38-single-egress-hub.md)); no spoke has a default route, and the internet is reached by *addressing* the proxy. A standing one would be ≈ USD 36.50/month, three quarters of the D12 ceiling, which is what makes "zero, with a per-VPC contingency" the design |
| **Interface VPC endpoints — per account, single AZ (D9)** | **0.010 each**, counts measured at 6c passes 5-6 from each slice's own plan: **Sandbox 18** = 0.180/h · **Staging 11** = 0.110/h · **`VPC-SharedServices` 13** = 0.130/h · **`VPC-Workloads` 0** — its emptiness is a written refusal, not an omission, and Stage 9/10 decides the list. **`VPC-Networking` carries none**, by the invariant that keeps the client plane resolving publicly. **The Sandbox line is per business unit (D35)**, the term that multiplies |
| **the optional endpoint groups** (`make up ENV=x GROUPS=…`) | **0 unless named.** `bedrock` is 4 endpoints ≈ 0.040/h; `emr` is 7 ≈ 0.070/h; `mwaa` is reserved and empty. A family nobody uses that day costs nothing, which is what 6c step 5.3 bought instead of disabling blueprints |
| **the proxy** — `production/proxy/`, `[D]` | **0.0104** (`t3.micro`; sized up from `t3.nano` after `dnf` was OOM-killed on 415 MiB) plus **USD 3.65/month** for its `[P]` Elastic IP. It replaces every NAT gateway in the estate and charges nothing per GB: an EC2 proxy does no metered "data processing" |
| WireGuard EC2 `t3.nano` — `production/vpn/`, `[D]` | ~0.005. Its Elastic IP was transferred rather than added, so the estate's address count did not move |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| Internal ALB in front of GitLab/Pages (only while GitLab is up) | ~0.023 + LCU usage |
| **the build host** — `production/buildbox/`, `[E]` | 0.2117 (`m8i.xlarge` since 2026-09-11; `t3.xlarge` was 0.1664) **plus `VPC-SharedServices`'s 0.130/h**, which since 6c step 5.8 is a *prerequisite* rather than a slice a build could avoid: the SSM endpoints are the host's only door. A build session is three bills, not one |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| VPC peering — **five**, hub-and-spoke | free within an AZ; USD 0.01/GB each way across AZs. With the hub hosts and every endpoint set pinned to `usw2-az1` the common path is free. **Transit Gateway was the alternative and it is priced**: 5 attachments × 0.05/h ≈ USD 182/month standing before a byte (`PRICING.md` §7) |
| **Staging `egress/` during a promotion run** (D20) | 0.110/h, measured in *minutes* per promotion rather than hours — `make up ENV=staging` is a pipeline step and the pipeline tears it down. Budget ~USD 0.02 per promotion, not a standing hourly cost |
| Athena, Glue | usage-based; negligible at lab scale |

The estate-wide fixed rate fell with the NAT, **0.470 → 0.390/h** across the four egress slices
(`scripts/tfhygiene/layers.py` carries the per-slice figures, and `make status` sums them). Sandbox's own
idle floor rose, **0.160 → 0.180**, because design B has to enumerate what the NAT covered silently. Per
gigabyte a NAT is 0.045 against an endpoint's 0.010, so the break-even is ≈ **0.57 GB/h**, which one
container pull passes in minutes.

The `Development egress/ + Studio apps` line went with that account's interactive life (6b), and the old
`Production egress/` row's *NAT ~0.050 + endpoints ~0.100-0.120* was a range over a set nobody had
counted. Both are replaced by the counted numbers above.

Net, derived over `PRICING.md`'s measured rates rather than measured: the floor moves by about
**+USD 4.65/month** (one address, one or two zones) and by about **−USD 2/month** as 6b destroys two KMS
keys. Every *session* hour falls, because the two NAT gateways at 0.050/h each are gone and the account
that carried the second Interactive endpoint set is now a headless Workload. Re-sum this table from
`PRICING.md` §3 at 6c step 7, and read the first month's invoice at Stage 12 step 5; the figures here are
arithmetic over measured rates, not a bill.

Two corrections applied 2026-08-08, both moving the numbers up, kept because the reasoning still explains
the endpoint half:

- **The data plane had no endpoints.** `athena`, `glue` and `lakeformation` were missing from every
  account. Under design A the NAT hid it; under design B, with no NAT anywhere, the design could not run a
  query at all — D13 routes every tabular read through an LF-aware engine. They are in the **common core
  of both designs**, so both got more expensive: a Sandbox hour goes from ~0.14 to ~0.170 under A and from
  ~0.11 to ~0.140 under B, on the lists as then counted. The A figure moved twice since:
  `elasticfilesystem` out on 2026-08-17 (D24 withdrawn), `datazone` in on 2026-08-21 (Stage 6 step 4.2)
  and out again on 2026-08-25 (issue #39), so **A reads 0.160**. B stays 0.140: the endpoint A dropped is
  one B has to keep, having no NAT to reach DataZone through.
- **The gap between the designs survived the correction.** B is cheaper by ~USD 0.030/h — the NAT and its
  address (0.050) less the two CodeArtifact endpoints (0.020) — in every account, for every list. The
  Stage 6 comparison is not settled by this: three cents an hour is a rounding error next to the friction
  D5 exists to measure.

**Projection:** ~USD 25-34 floor + 20 h/month × ~USD 0.18-0.45 (the lower end is a Sandbox hour under
design B; the upper a full-stack hour under design A: GitLab, its ALB, a runner build with Production's
endpoints, and one Interactive environment at once) + a handful of promotions at ~USD 0.03 each ≈
**USD 29-43/month**, against the USD 50 ceiling (D12). Read the top of that range as the planning number:
it leaves roughly USD 7 of headroom, and the items listed as missing from the floor row eat into it.
Staging and Data Governance cost almost nothing because neither ever has standing compute. Since
2026-09-06 there is one interactive account, so the number to watch is Sandbox's own concurrency, which
keeps the hourly line from doubling. After the 2026-09-05 repricing the projection is roughly
**USD 28-43** — the same shape, with the NAT rows removed and the hub's two lines added — and the ~USD 7
of headroom survives only because no NAT gateway stands.
The fastest way to breach the ceiling is a session that leaves `egress/` up: at ~USD 0.160/h that is
USD 3.84 for a forgotten day, and two of them cancel the headroom. The budget alerts and Cost Anomaly
Detection of Stage 1a step 2 were both skipped by decision on 2026-08-09, so there is no automatic control
over it: the exposure is carried by the teardown discipline of the `[E]` layer (D11) and by whoever
remembers to open Cost Explorer. Two forgotten days are detected at the end of the month, not on the day
they happen.
Design B trades the NAT gateway for two CodeArtifact endpoints, so it is the cheaper of the two egress
options as well as the stricter one.

**What the ceiling rules out:** always-on GitLab (~USD 60/month on its own), AWS Client VPN
(~USD 73/month, the D4 alternative), Network Firewall (~USD 290/month, option D5c) and an always-on MWAA
environment (~USD 212/month for `mw1.micro`, ~USD 358/month for `mw1.small` — D7 alternative A). Any of
these is affordable only as a short, deliberate experiment, which is what the operating model below is
for. D7 commits to building MWAA, and this is the line it has to respect: the environment is `[E]`, it
exists for the length of a comparison run, and at `mw1.micro` an eight-hour experiment costs ~USD 2.30.
**MWAA Serverless** (USD 0.088 per task-hour, no environment fee) removes the exposure and is the variant
to try first. Per-unit rates for both `us-west-2` and `sa-east-1` are in `docs/PRICING.md`. The same
discipline applies inside the unified domain (D26): the Lakehouse blueprint is enabled in its Glue/Athena
form only — its **Redshift Serverless** variant would put a second, larger query bill on top of Athena's,
and is excluded by decision.

**Guardrail:** AWS Budgets with e-mail alerts must exist before any compute is created (Stage 1).

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
