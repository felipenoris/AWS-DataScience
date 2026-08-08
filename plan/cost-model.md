# Cost model of the lab

The projection and its assumptions. **Authoritative per-unit rates live in [`PRICING.md`](../PRICING.md)**, measured from the AWS Price List bulk API — never estimated here.
The operating model that produces these numbers is `plan/conventions.md` §5.1.

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
| KMS customer-managed keys | ~8.00 | ~1.00 per key per month. The set: one per Terraform-managed account (Sandbox, Development, Data Governance, Staging, Production, Identity) plus a **dedicated derived-zone key in each Interactive account** (D31 — the key policy is what says who may read materialised `restricted` data, and it only works as a control if the key is not shared with scratch, state and logs). Data Governance may need more than one of its own (a CMK per data domain, Stage 5 step 1), so this row is a floor rather than a count |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~2.5-5 | **One recorder per governed account — every account except Management** (D20-D22, D29 — `Policy Canary` is empty, but an enrolled account still carries a recorder, and enrolling it is what makes the policy test meaningful); confirm in Stage 1 whether the landing zone also records the Management account. This row scales with the account count, so it is the line to re-read whenever an account is added. The estimate assumes an idle lab; a heavy `terraform apply` session records a configuration item per resource change and can multiply this. Control Tower allows restricting the recorded resource types — the main cost lever of the landing zone, applied in Stage 1 |
| Route 53 hosted zones (1 private + 1 public, D15) | ~1.00 | The public zone exists only for ACM DNS validation |
| Public domain registration (D15) | ~1.00 | ~USD 12-15/year amortised |
| CodeArtifact | ~0.10 | USD 0.05/GB-month storage plus USD 0.05 per 10k requests; negligible at lab scale |
| Security Hub + IAM Access Analyzer | ~1-2 | **Access Analyzer external-access findings are free and are enabled in Stage 1b**; Security Hub charges per check and per finding and is enabled in **Stage 5 step 13**, with the first governed data (principle 9, as amended). Its checks run as Config rules, so it also nudges the Config row up |
| GuardDuty | 0 → ~3-5 | Enabled in **Stage 4 step 10**, with the first internet-facing resource. Free for the first 30 days per account, then driven by CloudTrail/VPC flow/DNS log volume. S3 Protection and Malware Protection are extra, are decided in Stage 11 step 4, and are the ones to watch against the ceiling |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |
| EFS (shared filesystem + Studio homes, lifecycle to IA) | ~0.50 | `[P]` — cents at rest, and it buys the removal of the sync-to-S3-on-teardown machinery (`plan/conventions.md` §5.1 rule 2) |
| SageMaker unified domain — DataZone V2 metadata (D26) | ~0.50 | Requests USD 10 per 100k, metadata storage USD 0.40/GiB-month, global rates (`PRICING.md`); cents at lab scale. The cost lever is which blueprints exist, not the domain itself |
| Staging, Development and Data Governance accounts at rest (D20-D22) | **0 (already counted)** | **This row is now a pointer, not a cost.** It used to add ~USD 3 for "a Config recorder and a KMS key per account" — but the Config row above already covers every governed account and the KMS row already counts every key, so charging these accounts again was a double count of ~USD 3. What is worth keeping is the *shape*: VPCs, buckets and IAM roles are free at rest; Staging's metered slice exists only during a promotion, Development's only while someone is working, and Data Governance has no metered slice at all — its data plane is serverless (the lake storage is in the S3 row above) |
| **Floor** | **~USD 25-34** | Up from the ~USD 15 first estimate: mostly the detective controls, plus the recorder for D29's disposable account. The low end is the first thirty days, while GuardDuty is still inside its free window; the high end is an ordinary month with GuardDuty billing and Config recording an active build-out. **This is the *steady-state* floor. During Stages 1b-3 it is lower — roughly ~USD 24-27 — because GuardDuty does not exist until Stage 4 and Security Hub until Stage 5** (principle 9, as amended: detection is enabled when there is something to detect). **Recomputed 2026-08-08 by summing the measured `us-west-2` column of `PRICING.md` §2** — the "~USD 21-27" and "~USD 24-30" this row and its header used to carry both predated D29/D31 and both understated it. **What is still not in this row**, and is already decided elsewhere in the plan: the Secrets Manager secret holding `gitlab-secrets.json` (Stage 7 step 1), the CloudWatch alarms the plan requires (root sign-in, the two deploy roles, the catalog-maintenance role, VPN, GitLab, budget — at USD 0.10 each this is ~USD 1-1.50), AWS Backup storage and Vault Lock (Stage 12 step 8), and the growth of the Object-Locked Log Archive bucket. Expect the measured floor at Stage 12 step 5 to land above this range, not below it |

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
| NAT Gateway (1) + its public IPv4 | ~0.050 + 0.045/GB processed — **zero under egress design B** (`plan/architecture.md` §4.3) |
| **Interface VPC endpoints — per account, single AZ (D9)** | ~0.010 each. The list is per account role, not one list (Stage 3 step 8): **Sandbox** 12 (14 under design B), **Development** 11 (13), **Staging** 9, **Production** 10-12. Double if spread across 2 AZs |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| Internal ALB in front of GitLab/Pages (only while GitLab is up) | ~0.023 + LCU usage |
| **Production `egress/`** (only while runner builds or orchestration need it) | NAT ~0.050 + **endpoints ~0.100-0.120** — the endpoint half was missing from every earlier version of this table |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| WireGuard EC2 `t4g.nano` | ~0.004 |
| Sandbox ↔ Production **and** Development ↔ Production VPC peering (two of them, D21) | free within an AZ; USD 0.01/GB each way across AZs — see `plan/open-questions.md` item 3 |
| **Staging `egress/` during a promotion run** (D20) | ~0.140/h, but measured in *minutes* per promotion, not hours — `make up ENV=staging` is a pipeline step, and the pipeline tears it down. Budget ~USD 0.03 per promotion, not a standing hourly cost |
| **Development `egress/` + Studio apps** (D21) | ~0.160/h under design A, ~0.130 under B, plus ~0.05/h per running app — but only while pipeline-engineering work is happening. A session is either exploratory (Sandbox up) or engineering (Development up), so the *typical* hourly burn does not double even though the worst case does |
| EFS, Athena, Glue | usage-based; negligible at lab scale |

**Two corrections to this table, applied 2026-08-08, and both moved the numbers up.**

- **The data plane had no endpoints.** `athena`, `glue` and `lakeformation` were missing from every
  account. Under design A the NAT hid it; under design B, with no NAT anywhere, it meant the design could
  not run a query at all — D13 routes every tabular read through an LF-aware engine. They are now in the
  **common core of both designs**, which is why both got more expensive: a Sandbox hour goes from ~0.14
  to ~0.170 under A and from ~0.11 to ~0.140 under B.
- **The gap between the designs survived the correction, and now rests on the right thing.** B is cheaper
  by exactly ~USD 0.030/h — the NAT and its address (0.050) less the two CodeArtifact endpoints (0.020) —
  in every account, for every list. The older claim that B trades the NAT for two endpoints and comes out
  ahead was right; it was just measured against a list that could not have executed a query. **The
  Stage 6 comparison is still not settled by this**: three cents an hour is a rounding error next to the
  friction D5 exists to measure.

**Projection:** ~USD 25-34 floor + 20 h/month × ~USD 0.19-0.46 (the lower end is a Sandbox hour under
design B; the upper a full-stack hour under design A: GitLab, its ALB, a runner build with Production's
endpoints, and one Interactive environment all at once) + a handful of promotions at ~USD 0.03 each ≈
**USD 29-43/month**, against the USD 50 ceiling (D12). **Read the top of that range as the planning
number, not the bottom** — it leaves roughly USD 7 of headroom, and the items listed as missing from the
floor row eat into it. Staging and Data Governance cost almost nothing precisely because neither ever has
standing compute; the number to watch is whether Sandbox and Development sessions actually stay disjoint,
which is what keeps the hourly line from doubling.
The single fastest way to breach the ceiling is a session that leaves `egress/` up: at ~USD 0.170/h that is
USD 4.08 for a forgotten day, and two of them cancel the entire headroom — which is why the budget alerts
and Cost Anomaly Detection of Stage 1a step 2 are the primary control here, not a convenience.
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
per-unit rates, for both `us-west-2` and `sa-east-1`, are in `PRICING.md`. The same discipline applies
inside the unified domain (D26): the Lakehouse blueprint is enabled in its Glue/Athena form only — its
**Redshift Serverless** variant would put a second, larger query bill on top of Athena's, and it is
excluded by decision, not by omission.

**Guardrail:** AWS Budgets with e-mail alerts must exist before any compute is created (Stage 1).

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
