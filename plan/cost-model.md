# Cost model of the lab

The projection and its assumptions. **Authoritative per-unit rates live in [`PRICING.md`](../PRICING.md)**, measured from the AWS Price List bulk API — never estimated here.
The operating model that produces these numbers is `plan/conventions.md` §5.1.

---

## 5. Cost model

Because of D11 the relevant question is not "what does this cost per month" but "what is the floor when
nothing is running, and what does an hour of lab time add on top". Order-of-magnitude figures for
`us-west-2`, to be confirmed with the AWS Pricing Calculator before each stage.

**The floor — paid every month even with the lab shut down (~USD 21-27):**

| Item | Approx. USD/month | Note |
|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | 0 | These cost nothing at rest, so there is no reason to destroy them |
| GitLab EBS volume (50 GB gp3) | ~4.00 | Paid while the instance is stopped; this is the price of not rebuilding GitLab |
| Elastic IP for WireGuard | ~3.65 | All public IPv4 addresses are charged hourly, attached or not |
| KMS customer-managed keys (8) | ~8.00 | ~1.00 per key per month. **Eight:** one per Terraform-managed account (Sandbox, Development, Data Governance, Staging, Production, Identity) plus a **dedicated derived-zone key in each Interactive account** (D31 — the key policy is what says who may read materialised `restricted` data, and it only works as a control if the key is not shared with scratch, state and logs). The "(3)" this row used to say predated D20-D22. Data Governance may need more than one of its own (a CMK per data domain, Stage 5 step 1), so treat 8 as the floor rather than the number |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~2.5-5 | One recorder per governed account — **nine of the ten**, every account except Management (D20-D22, D29 — `Policy Canary` is empty, but an enrolled account still carries a recorder, and enrolling it is what makes the policy test meaningful); confirm in Stage 1 whether the landing zone also records the Management account. The estimate assumes an idle lab; a heavy `terraform apply` session records a configuration item per resource change and can multiply this. Control Tower allows restricting the recorded resource types — the main cost lever of the landing zone, applied in Stage 1 |
| Route 53 hosted zones (1 private + 1 public, D15) | ~1.00 | The public zone exists only for ACM DNS validation |
| Public domain registration (D15) | ~1.00 | ~USD 12-15/year amortised |
| CodeArtifact | ~0.10 | USD 0.05/GB-month storage plus USD 0.05 per 10k requests; negligible at lab scale |
| Security Hub + IAM Access Analyzer | ~1-2 | Enabled org-wide from Stage 1 (principle 9). Access Analyzer external-access findings are free; Security Hub charges per check and per finding |
| GuardDuty | 0 → ~3-5 | Free for the first 30 days per account, then driven by CloudTrail/VPC flow/DNS log volume. S3 Protection and Malware Protection are extra and are the ones to watch against the ceiling |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |
| EFS (shared filesystem + Studio homes, lifecycle to IA) | ~0.50 | `[P]` — cents at rest, and it buys the removal of the sync-to-S3-on-teardown machinery (`plan/conventions.md` §5.1 rule 2) |
| SageMaker unified domain — DataZone V2 metadata (D26) | ~0.50 | Requests USD 10 per 100k, metadata storage USD 0.40/GiB-month, global rates (`PRICING.md`); cents at lab scale. The cost lever is which blueprints exist, not the domain itself |
| Staging, Development and Data Governance accounts at rest (D20-D22) | **0 (already counted)** | **This row is now a pointer, not a cost.** It used to add ~USD 3 for "a Config recorder and a KMS key per account" — but the Config row above already covers all eight governed accounts and the KMS row now counts all six keys, so charging these three accounts again was a double count of ~USD 3. What is worth keeping is the *shape*: VPCs, buckets and IAM roles are free at rest; Staging's metered slice exists only during a promotion, Development's only while someone is working, and Data Governance has no metered slice at all — its data plane is serverless (the lake storage is in the S3 row above) |
| **Revised floor** | **~USD 24-30** | Up from the ~USD 15 first estimate: mostly from moving the detective controls into the landing zone (principle 9), plus ~USD 0.50-1 for D29's tenth account. The double-count fix above nets to zero — removing ~USD 3 of double-counted Config/KMS and adding ~USD 3 of previously under-counted KMS keys cancel — which is luck, not design, and is exactly the kind of thing Stage 12 step 5 exists to replace with a measured number. Still under the USD 50 ceiling, with less headroom than before |

Two cost levers worth applying rather than discovering later:

- **S3 Bucket Keys** on every SSE-KMS bucket. They cut KMS request charges by up to ~99%, and a data
  environment issues a KMS request per object operation — without this, KMS requests can quietly exceed
  the cost of the keys themselves. Free to enable; set it in the `s3-bucket` module from Stage 2.
- **Scope Macie deliberately** (Stage 11). Macie charges per GB inspected for sensitive-data discovery. Run
  it against a sampled prefix, not the whole lake, or it becomes the largest single line item in the
  project. The same caution applies to **CloudTrail S3 data events**, which bill per event: a single Spark
  job listing and reading thousands of objects generates a matching number of events.

**Per hour of lab time — added while the environment is up (~USD 0.25/h):**

| Item | Approx. USD/h |
|---|---|
| NAT Gateway (1) + its public IPv4 | ~0.050 + 0.045/GB processed — **zero under egress design B** (`plan/architecture.md` §4.3) |
| Interface VPC endpoints (9, single AZ per D9; 11 under design B) | ~0.090-0.110 (double if spread across 2 AZs) |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| Internal ALB in front of GitLab/Pages (only while GitLab is up) | ~0.023 + LCU usage |
| Production NAT + endpoints (only while runner builds need egress) | ~0.050 + 0.045/GB |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| WireGuard EC2 `t4g.nano` | ~0.004 |
| Sandbox ↔ Production **and** Development ↔ Production VPC peering (two of them, D21) | free within an AZ; USD 0.01/GB each way across AZs — see `plan/open-questions.md` item 3 |
| **Staging `egress/` during a promotion run** (D20) | ~0.10-0.15/h, but measured in *minutes* per promotion, not hours — `make up ENV=staging` is a pipeline step, and the pipeline tears it down. Budget ~USD 0.03 per promotion, not a standing hourly cost |
| **Development `egress/` + Studio apps** (D21) | Same shape as the Sandbox line items (~0.10-0.15/h endpoints + ~0.05/h per app), but only while pipeline-engineering work is happening. A session is either exploratory (Sandbox up) or engineering (Development up) — running both at once is the exception, so the *typical* hourly burn does not double even though the worst case does |
| EFS, Athena, Glue | usage-based; negligible at lab scale |

The endpoint count rose from 6 to 9 (11 under design B) because the Stage 3 list was incomplete: Studio in
VPC-only mode also needs `sagemaker.studio` and `kms`, and design B adds the two `codeartifact` endpoints.
At ~USD 0.01/h per endpoint per AZ this is the largest hourly item, so the list stays minimal and
single-AZ. The table now also carries the **Production** side — the runners' NAT and the GitLab ALB were
missing from earlier versions of this plan, which undercounted a full-stack hour.

**Projection:** ~USD 26 floor + 20 h/month × ~USD 0.28-0.40 (the upper end is a full-stack hour: GitLab,
its ALB, a runner build and one Interactive environment all running at once) + a handful of promotions at
~USD 0.03 each ≈ **USD 32-34/month**, against the USD 50 ceiling (D12). Staging and Data Governance cost
almost nothing precisely because neither ever has standing compute; the number to watch is whether Sandbox
and Development sessions actually stay disjoint, which is what keeps the hourly line from doubling.
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
