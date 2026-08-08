# Pricing

Prices for region `sa-east-1`.

`us-west-2` is shown alongside it in every table, because that is the region the project actually deploys
in (`CLAUDE.md`) and the region all the estimates in `GENERAL_PLAN.md` §5 were written for. Having both
columns is what makes the São Paulo premium a measurement instead of an impression.

---

## 0. Method

**Every number in this file was read from the AWS Price List bulk API, not estimated and not copied from a
pricing page.** The endpoint is public and needs no credentials:

```bash
curl -s 'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonMWAA/current/sa-east-1/index.json' | jq '.products, .terms.OnDemand'
```

Substitute the service code (`AmazonEC2`, `AmazonVPC`, `AWSELB`, `awskms`, `AmazonS3`, …) and the region.
The full list of service codes is at `offers/v1.0/aws/index.json`; the regions a service is offered in are
at `offers/v1.0/aws/<service>/current/region_index.json` — which is also how the CodeArtifact gap in §9
was found.

Read on **2026-08-08**. The individual offer files carry their own publication dates (MWAA 2026-04-20,
VPC 2026-07-24, S3 2026-08-07), so a rate can be a few months old without being stale — AWS republishes an
offer file only when something in it changes.

**What these prices are:** on-demand, list, pre-tax, in USD. They exclude the AWS Free Tier, any private
pricing, and Brazilian taxes, which are added on the invoice for accounts billed through AWS Brazil and
are not part of any figure below. Monthly figures use **730 hours** unless stated otherwise.

**Ratio column:** `sa-east-1 ÷ us-west-2`. It is worth reading as its own signal — the premium is not
uniform, and the services where it is **1.00** (KMS, Config, CloudTrail, Security Hub, Network Firewall,
Private CA, Lambda, public IPv4, VPC peering) are as interesting as the ones where it is 2x.

---

## 1. MWAA and the D7 alternatives

This is the table the file was created for. D7 builds **two** orchestrators in Stage 10 and compares them:
**(A)** MWAA, **(B)** EventBridge + Step Functions + Lambda/Fargate.

### 1.1 MWAA environment fee

Charged **per hour the environment exists**, at one-second resolution, whether or not a DAG runs. This is
the single most important fact about MWAA's cost model: it is not per execution, and an idle environment
costs the same as a busy one.

| Environment class | `sa-east-1` USD/h | `us-west-2` USD/h | Ratio | `sa-east-1` /month (730 h) | `us-west-2` /month |
|---|---|---|---|---|---|
| `mw1.micro` | 0.498617 | 0.29 | 1.72 | **364.00** | **211.70** |
| `mw1.small` | 0.842490 | 0.49 | 1.72 | **615.02** | **357.70** |
| `mw1.medium` | 1.272332 | 0.74 | 1.72 | 928.80 | 540.20 |
| `mw1.large` | 1.702174 | 0.99 | 1.72 | 1 242.59 | 722.70 |
| `mw1.xlarge` | 3.404348 | 1.98 | 1.72 | 2 485.17 | 1 445.40 |
| `mw1.2xlarge` | 6.808696 | 3.96 | 1.72 | 4 970.35 | 2 890.80 |

The `~USD 350/month` that `GENERAL_PLAN.md` used to quote is `0.49 × 730 = 357.70` — `mw1.small` in
`us-west-2`. At 744 hours (a 31-day month) the same environment is USD 364.56, which is where the "USD 360"
figure comes from. The ratio is a flat **1.72** across every class.

**The unit of billing is the *environment*** — the AWS resource created by `CreateEnvironment`
(`AWS::MWAA::Environment`). Not the account, not the user, not the DAG. The figures above are for **one**
environment, in one account, in one Region, for one month.

| Does it multiply the fee? | | |
|---|---|---|
| **Users** | No | No per-seat charge. Airflow UI access is IAM/Identity Center; one data scientist or twenty cost the same |
| **DAGs / pipelines** | No | DAGs live in an S3 bucket the environment reads. 1 or 200 DAGs, same fee |
| **Executions** | No | A DAG that runs hourly and a DAG that never runs cost the same in environment fee. This is what makes MWAA bad for sporadic use |
| **Number of environments** | **Yes, linearly** | Quota: **10 per account per Region**, adjustable |
| **Environment class** | **Yes** | `mw1.micro` → `mw1.2xlarge`, §1.1 |
| **Concurrency** | **Yes** | Autoscaling adds *worker instances*, billed per hour at the rates in §1.2. Quota: 25 workers per environment |
| **Extra schedulers / web servers** | **Yes** | Billed per hour while configured, not per use. Quota: 5 web servers per environment |
| **Metadata database storage** | **Yes** | Per GB-month, per environment |

The base environment fee includes **1 worker, 2 schedulers and 2 web servers** — read off AWS's own worked
example on the pricing page (Airflow 2.8.1); the composition can differ by Airflow version, so confirm it
for the version actually deployed. Everything beyond that is a separate hourly line. So volume reaches the
bill through **concurrency**, not through quantity: 200 DAGs staggered through the day fit in the included
worker; five DAGs that all fire at 03:00 scale workers out and cost money. The environment scales back down
to `MinWorkers` (default 1) when the queue drains — the environment fee does not.

**Consequence for the promotion chain (D20, D21).** Because the multiplier is the environment, giving
Development, Staging and Production each its own Airflow means **three** environments:
3 × USD 357.70 = **USD 1 073/month** in `us-west-2`, or USD 1 845 in `sa-east-1`. This plan does not do
that — D17 keeps interactive and orchestration compute out of the deployment targets and §6 places
`orchestration/` only under `production/` — but the architectural choice has a four-figure number attached,
and it is worth knowing before someone reasonably proposes "let's test the DAG in Staging first". The cheap
answer to that is an `[E]` environment for an hour, not a second standing one. **MWAA Serverless removes
the question entirely:** with no environment fee, there is nothing to multiply — see §1.3.

### 1.2 MWAA add-ons

| Item | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| Additional worker — small / medium / large (USD/h each) | 0.094565 / 0.189130 / 0.378261 | 0.055 / 0.11 / 0.22 | 1.72 |
| Additional scheduler — small / medium / large (USD/h each) | 0.094565 / 0.189130 / 0.378261 | 0.055 / 0.11 / 0.22 | 1.72 |
| Additional web server — small / medium / large (USD/h each) | 0.094565 / 0.094565 / 0.189130 | 0.055 / 0.055 / 0.11 | 1.72 |
| Metadata database storage (USD/GB-month) | 0.19 | 0.10 | 1.90 |

Auto-scaling adds worker hours on demand; extra schedulers and web servers are provisioned and billed for
the whole life of the environment, like the environment fee itself.

### 1.3 MWAA Serverless

GA November 2025. **No environment fee** — billed per task, for the task's duration, with a one-minute
minimum.

| Item | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| Managed task (USD per task-hour) | 0.104 | 0.088 | 1.18 |

This is the variant D7 tries first: it is Airflow with the cost shape of alternative B, and it is also the
one place in this file where the São Paulo premium nearly disappears (1.18x instead of 1.72x). Available in
both `us-west-2` and `sa-east-1`. Terraform: **`awscc_mwaaserverless_workflow`** (Cloud Control, from
`AWS::MWAAServerless::Workflow`); the classic `aws` provider has no Serverless resource yet (D28,
§4.4 row 14 of the plan).

**What you give up for that price**, and what you gain — this is not the same product with a different
invoice:

| | MWAA Serverless | MWAA provisioned |
|---|---|---|
| Workflow definition | **YAML** (DAG-factory format), with a converter for Python definitions | Python DAGs, custom operators, plugins |
| Airflow version | v3, Python 3.12, fixed | Selectable |
| Airflow web UI | **None** — monitoring through logs | Full web interface |
| Execution identity | **One IAM role per workflow**, task-isolated compute | One environment role shared by every task |
| Scheduling | EventBridge Scheduler, internally | Airflow scheduler |
| Startup | Each task provisions compute first | Warm, when worker capacity exists |
| Networking | Tasks can run in your VPC | Environment lives in your VPC |

The row that matters most to *this* project is not the price: **one execution role per workflow** is a
least-privilege property that provisioned MWAA cannot offer, since there every task inherits the same
environment role. Against the data-perimeter design in §4.2 of `GENERAL_PLAN.md`, that is an argument for
Serverless independent of cost. The row that argues the other way is the missing Airflow UI, which is a
real loss for a data scientist debugging a DAG.

### 1.4 Alternative B — the unit prices

| Item | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| EventBridge Scheduler — scheduled invocations (USD per million) | 1.70 | 1.00 | 1.70 |
| EventBridge — custom events received (USD per million) | 1.00 | 1.00 | 1.00 |
| Step Functions **Standard** — per state transition (USD) | 0.0000375 | 0.000025 | 1.50 |
| Step Functions **Express** — per request (USD) | 0.000001 | 0.000001 | 1.00 |
| Step Functions **Express** — duration, first 3.6M GB-s (USD/GB-s) | 0.00001667 | 0.00001667 | 1.00 |
| Lambda — duration, x86, tier 1 (USD/GB-s) | 0.0000166667 | 0.0000166667 | **1.00** |
| Lambda — duration, ARM, tier 1 (USD/GB-s) | 0.0000133334 | 0.0000133334 | **1.00** |
| Lambda — requests (USD each) | 0.0000002 | 0.0000002 | **1.00** |
| Fargate — vCPU (USD/h) | 0.0696 | 0.04048 | 1.72 |
| Fargate — memory (USD/GB-h) | 0.0076 | 0.004445 | 1.71 |
| Fargate ARM — vCPU (USD/h) | 0.0557 | 0.03238 | 1.72 |
| Fargate ARM — memory (USD/GB-h) | 0.00612 | 0.00356 | 1.72 |

**Lambda has no São Paulo premium at all.** Fargate has the full 1.72x. So under design B the region
choice barely matters for the orchestration and matters entirely for the container steps.

### 1.5 Worked comparison — one nightly workflow

Assumptions: 10 tasks per run, 10 minutes each (≈1.67 task-hours per run), one run per day, 30 days;
containers on ARM Fargate at 1 vCPU / 2 GB; ~12 Step Functions state transitions per run.

| Implementation | `sa-east-1` USD/month | `us-west-2` USD/month |
|---|---|---|
| **B** — EventBridge + Step Functions + Fargate (ARM) | schedules 0.00005 + transitions 0.014 + 50 Fargate-h **3.40** ⇒ **≈ 3.41** | 0.00003 + 0.009 + **1.98** ⇒ **≈ 1.99** |
| **A** — MWAA Serverless (50 task-hours) | **≈ 5.20** | **≈ 4.40** |
| **A** — MWAA `mw1.micro`, environment left up | **≈ 364.00** + task compute | **≈ 211.70** + task compute |
| **A** — MWAA `mw1.micro`, `[E]`, 8 h per comparison run | **≈ 3.99** per run | **≈ 2.32** per run |

The gap between the last two rows is the whole argument of the `[P]`/`[D]`/`[E]` model in one line: the
same environment costs USD 364 or USD 4 depending only on whether anyone remembers to destroy it. And the
gap between the first two rows is small enough that the D7 comparison will be decided by operational fit —
DAG portability, retry semantics, how a failure is observed — not by price. That is a better basis for a
decision than the USD 350 figure was.

---

## 2. The monthly floor (`GENERAL_PLAN.md` §5), re-priced

Paid every month even with the lab shut down. Same rows as §5, same assumptions, both regions.

| Item | Rate (`sa-east-1`) | Rate (`us-west-2`) | `sa-east-1` /month | `us-west-2` /month |
|---|---|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | — | — | **0** | **0** |
| GitLab EBS volume (50 GB gp3) | 0.152 USD/GB-mo | 0.08 USD/GB-mo | 7.60 | 4.00 |
| Elastic IP for WireGuard (idle or in use) | 0.005 USD/h | 0.005 USD/h | 3.65 | 3.65 |
| KMS customer-managed keys (3) | 1.00 USD/key-mo | 1.00 USD/key-mo | 3.00 | 3.00 |
| S3 data + state + backups (~25 GB Standard) | 0.0405 USD/GB-mo | 0.023 USD/GB-mo | ~1.50 | ~1.00 |
| ECR images (~10 GB) | 0.10 USD/GB-mo | 0.10 USD/GB-mo | 1.00 | 1.00 |
| AWS Config, 8 governed accounts | 0.003 USD/item | 0.003 USD/item | 2.00-4.50 | 2.00-4.50 |
| Route 53 hosted zones (1 private + 1 public) | 0.50 USD/zone-mo (global) | 0.50 USD/zone-mo | 1.00 | 1.00 |
| Public domain registration (D15) | registrar, region-independent | idem | ~1.00 | ~1.00 |
| CodeArtifact | **not available — see §9** | 0.05 USD/GB-mo + 0.05/10k req | **n/a** | ~0.10 |
| Security Hub + IAM Access Analyzer | 0.001 USD/check (first 100k) | 0.001 USD/check | 1.00-2.00 | 1.00-2.00 |
| GuardDuty (after the 30-day free window) | 1.75 USD/GB, 0.000007 USD/event | 1.00 USD/GB, 0.000004 USD/event | 0 → 5.00-9.00 | 0 → 3.00-5.00 |
| WireGuard EBS (8 GB) + CloudWatch logs | 0.152 USD/GB-mo; logs 0.90 USD/GB | 0.08; logs 0.50 USD/GB | ~1.80 | ~1.00 |
| EFS (shared filesystem + Studio homes, IA) | 0.044 USD/GB-mo | 0.025 USD/GB-mo | ~0.90 | ~0.50 |
| Staging, Development, Data Governance at rest | Config + 1 KMS key each | idem | ~3.00 | ~3.00 |
| **Floor** | | | **~USD 27-40** (central ~33) | **~USD 21-27** |

The São Paulo floor is roughly **1.4x** the Oregon one — less than the 1.72x of the metered services,
because so much of the floor is region-flat: KMS, Config, Route 53, Security Hub, the domain and the
Elastic IP are identical in both regions.

---

## 3. Per hour of lab time (`GENERAL_PLAN.md` §5), re-priced

| Item | `sa-east-1` USD/h | `us-west-2` USD/h | Ratio |
|---|---|---|---|
| NAT Gateway (1) | 0.093 + 0.093/GB | 0.045 + 0.045/GB | 2.07 |
| Interface VPC endpoint (each, per AZ) | 0.021 + 0.01/GB | 0.010 + 0.01/GB | 2.10 |
| — 9 endpoints, single AZ (D9) | 0.189 | 0.090 | 2.10 |
| — 11 endpoints, egress design B | 0.231 | 0.110 | (design B needs CodeArtifact — see §9) |
| GitLab EC2 `t4g.large` | 0.1072 | 0.0672 | 1.60 |
| — `t3.large`, the x86 equivalent | 0.1344 | 0.0832 | 1.62 |
| Internal ALB | 0.034 + 0.011/LCU-h | 0.0225 + 0.008/LCU-h | 1.51 |
| SageMaker Studio JupyterLab / CodeEditor `ml.t3.medium` | 0.081 | 0.050 | 1.62 |
| SageMaker processing job `ml.t3.medium` | 0.066 | — | |
| WireGuard EC2 `t4g.nano` | 0.0067 | 0.0042 | 1.60 |
| Public IPv4 address (in use or idle) | 0.005 | 0.005 | **1.00** |
| VPC peering data (each way) | 0.01/GB | 0.01/GB | **1.00** |
| Internet data transfer out, first 10 TB (see §7 note) | 0.150/GB | 0.090/GB | 1.67 |
| Inter-region transfer to the other region | 0.16/GB out of São Paulo | 0.02/GB into São Paulo | asymmetric |

**Typical Sandbox hour** (9 endpoints + NAT + one Studio app + WireGuard):
`sa-east-1` **≈ 0.37/h**, `us-west-2` **≈ 0.19/h**.

**Full-stack hour** (the above + GitLab + its ALB + Production's NAT and endpoints):
`sa-east-1` **≈ 0.79/h**, `us-west-2` **≈ 0.41/h**.

Note that `GENERAL_PLAN.md` §5 estimates NAT at USD 0.050/h in `us-west-2`; the measured rate is
**0.045**. The estimate was high by ~11%, in the safe direction.

---

## 4. What the USD 50 ceiling rules out (D12)

| Option | `sa-east-1` USD/month | `us-west-2` USD/month | Where it appears |
|---|---|---|---|
| Always-on GitLab (`t4g.large` + 50 GB gp3 + ALB) | 78.26 + 7.60 + 24.82 = **110.68** | 49.06 + 4.00 + 16.43 = **69.49** | D8, §5 |
| AWS Client VPN (1 endpoint association, 730 h) | 0.15/h → **109.50** | 0.10/h → **73.00** | D4 alternative |
| — plus each connected client | 0.05/h | 0.05/h | |
| AWS Network Firewall (1 endpoint) | 0.395/h → **288.35** + 0.065/GB | 0.395/h → **288.35** + 0.065/GB | D5 option (c) |
| AWS Private CA, general-purpose mode | **400.00** | **400.00** | D15 |
| AWS Private CA, short-lived certificate mode | **50.00** | **50.00** | D15 |
| MWAA `mw1.small`, always on | **615.02** | **357.70** | D7 (A) |
| MWAA `mw1.micro`, always on | **364.00** | **211.70** | D7 (A) |

Two of the plan's estimates are confirmed exactly (Client VPN ~73, Network Firewall ~290, both
`us-west-2`), and two of these prices are **region-flat**: Network Firewall and Private CA cost the same in
São Paulo as in Oregon.

---

## 5. Data platform

| Item | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| **S3** Standard, first 50 TB (USD/GB-mo) | 0.0405 | 0.023 | 1.76 |
| S3 Standard, next 450 TB | 0.039 | 0.022 | 1.77 |
| S3 Intelligent-Tiering, Archive Instant Access | 0.0083 | — | |
| S3 PUT/COPY/POST/LIST (USD per 1 000) | 0.007 | 0.005 | 1.40 |
| S3 GET and all others (USD per 10 000) | 0.0056 | 0.004 | 1.40 |
| **Glue** ETL (USD/DPU-h) | 0.69 | 0.44 | 1.57 |
| Glue Flex ETL (USD/DPU-h) | 0.45 | 0.29 | 1.55 |
| Glue crawler (USD/DPU-h) | 0.69 | 0.44 | 1.57 |
| Glue Iceberg compaction / optimization (USD/DPU-h) | 0.44 | 0.44 | **1.00** |
| Glue catalog statistics (USD/DPU-h) | 0.44 | 0.44 | **1.00** |
| Glue Data Catalog storage (USD per 100k objects-mo) | 1.00 | 1.00 | **1.00** |
| Glue Data Catalog requests (USD per 1M) | 1.00 | 1.00 | **1.00** |
| **Athena** SQL (USD per TB scanned) | 9.00 | 5.00 | 1.80 |
| Athena Spark (USD/DPU-h) | 0.35 | 0.35 | **1.00** |
| **Lake Formation** filtering (USD per TB scanned) | 2.75 | 2.25 | 1.22 |
| Lake Formation storage optimizer (USD per TB) | 2.75 | 2.25 | 1.22 |
| Lake Formation metadata objects (USD per 100k-mo) | 1.00 | 1.00 | **1.00** |
| Lake Formation API requests (USD per 1M) | 1.00 | 1.00 | **1.00** |
| **EFS** Standard (USD/GB-mo) | 0.57 | 0.30 | 1.90 |
| EFS Standard-IA (USD/GB-mo) | 0.044 | 0.025 | 1.76 |
| EFS Archive (USD/GB-mo) | 0.0166 | 0.008 | 2.08 |
| EFS IA reads/writes (USD/GB) | 0.019 | 0.010 (read) | 1.90 |
| **ECR** storage (USD/GB-mo) | 0.10 | 0.10 | **1.00** |
| **KMS** customer-managed key (USD/key-mo) | 1.00 | 1.00 | **1.00** |
| KMS requests (USD per 10 000) | 0.03 | 0.03 | **1.00** |

Athena at 9.00 USD/TB in São Paulo makes the two cost levers in §5 of the plan — **S3 Bucket Keys** and
partition/format discipline on the Iceberg tables — worth roughly twice as much there as in Oregon.

### SageMaker Unified Studio — the DataZone V2 domain (D26)

DataZone publishes **global, region-independent rates** in the Price List API (the offer file has no
per-region entries — one price everywhere the service exists):

| Item | USD | Unit |
|---|---|---|
| Metadata requests | 10.00 | per 100 000 requests |
| Metadata storage | 0.40 | per GiB-month |
| Compute units (metadata generation, data quality) | 1.776 | per compute unit |
| AI recommendations — input / output | 0.015 / 0.075 | per 1 000 tokens |

At lab scale the domain itself is **cents per month** — a single user cannot produce 100k metadata
requests by hand, and the metadata for a lake this size is megabytes. **The cost of Unified Studio is not
the domain; it is what the blueprints provision.** Two consequences the plan records as decisions rather
than discoveries:

- The **Lakehouse blueprint is enabled in its Glue/Athena form only** (D26). Its Redshift Serverless
  variant provisions a workgroup whose per-query RPU minimum would put a second, larger query bill on top
  of Athena's — excluded by decision, not omission.
- The **ML blueprint's** per-project SageMaker AI apps bill exactly like the Studio apps in §8
  (`ml.t3.medium` at 0.081/0.050 USD/h) — the domain adds nothing to the hourly rate.

---

## 6. Security, governance and observability

| Item | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| **AWS Config** configuration item recorded | 0.003 | 0.003 | **1.00** |
| Config daily recording (per item-day) | 0.012 | 0.012 | **1.00** |
| Config rule evaluations, first 100k | 0.001 | — | |
| **CloudTrail** management events, additional copies (each) | 0.00002 | 0.00002 | **1.00** |
| CloudTrail **data events** (each) | 0.000001 | 0.000001 | **1.00** |
| CloudTrail Insights events (each) | 0.0000035 | — | |
| **GuardDuty** CloudTrail events analyzed (each) | 0.000007 | 0.000004 | 1.75 |
| GuardDuty VPC flow + DNS logs, first 500 GB (USD/GB) | 1.75 | 1.00 | 1.75 |
| GuardDuty S3 Malware Protection data scanned (USD/GB) | 0.123 | 0.09 | 1.37 |
| **Macie** S3 bucket inventory (USD per bucket-day) | 0.0033 | 0.0033 | **1.00** |
| Macie sensitive-data discovery, first tier (USD/GB) | 2.25 | 1.00 | **2.25** |
| Macie automated object monitoring (USD per 100k object-days) | 0.0225 | 0.01 | 2.25 |
| **Security Hub** checks, first 100k (each) | 0.001 | 0.001 | **1.00** |
| Security Hub finding ingestion above 10k (each) | 0.00003 | 0.00003 | **1.00** |
| **CloudWatch** logs ingested, Standard class (USD/GB) | 0.90 | 0.50 | 1.80 |
| CloudWatch logs, Infrequent Access class (USD/GB) | 0.45 | — | |
| CloudWatch logs storage (USD/GB-mo) | 0.0408 | 0.03 | 1.36 |
| CloudWatch Logs Insights scanned (USD/GB) | 0.009 | 0.005 | 1.80 |
| CloudWatch standard alarm (USD/alarm-mo) | 0.135 | 0.10 | 1.35 |
| **Route 53** hosted zone, first 25 (USD/zone-mo) | 0.50 (global) | 0.50 | **1.00** |
| Route 53 Resolver DNS Firewall, first 1B queries (USD per million) | 0.60 | — | |
| Route 53 Resolver queries, first 1B (USD per million) | 0.40 | — | |

**Macie is the one to watch in São Paulo: 2.25x, the largest premium in this file.** The plan already says
to scope Macie to a sampled prefix rather than the whole lake (§5); in `sa-east-1` that instruction is
worth more than twice as much.

---

## 7. Network

| Item | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| NAT Gateway (USD/h) | 0.093 | 0.045 | 2.07 |
| NAT Gateway data processed (USD/GB) | 0.093 | 0.045 | 2.07 |
| Interface VPC endpoint (USD/h per endpoint per AZ) | 0.021 | 0.010 | 2.10 |
| Interface VPC endpoint data (USD/GB, up to 1 PB) | 0.01 | 0.01 | **1.00** |
| Gateway VPC endpoint (S3, DynamoDB) | free | free | — |
| Public IPv4 address, in use or idle (USD/h) | 0.005 | 0.005 | **1.00** |
| VPC peering, in and out (USD/GB each way) | 0.01 | 0.01 | **1.00** |
| Application Load Balancer (USD/h) | 0.034 | 0.0225 | 1.51 |
| ALB capacity unit (USD/LCU-h) | 0.011 | 0.008 | 1.38 |
| Client VPN endpoint association (USD/h) | 0.15 | 0.10 | 1.50 |
| Client VPN connection (USD/h) | 0.05 | 0.05 | **1.00** |
| Site-to-Site VPN connection (USD/h) | 0.05 | — | |
| Network Firewall endpoint (USD/h) | 0.395 | 0.395 | **1.00** |
| Network Firewall traffic (USD/GB) | 0.065 | 0.065 | **1.00** |
| Internet data transfer out, first 10 TB (USD/GB) | 0.150 | 0.090 | 1.67 |
| — next 40 TB / next 100 TB / above 150 TB | 0.138 / 0.126 / 0.114 | 0.085 / 0.070 / 0.050 | |
| Transfer São Paulo → Oregon (USD/GB) | 0.16 | — | |
| Transfer Oregon → São Paulo (USD/GB) | — | 0.02 | |

**Note on data transfer out.** Two offer files disagree. The `AWSDataTransfer` offer — the current,
unified one, and the source of the table above — gives `sa-east-1` 0.150 USD/GB for the first 10 TB. The
older per-service `AmazonEC2` offer still carries a São Paulo tier of 0.25 USD/GB. The `us-west-2` figure
of 0.090 matches what `GENERAL_PLAN.md` §4.3 already assumed, which is a point in favour of the unified
offer being the live one, but this is the one row in this file to verify against a real invoice before
relying on it. The first 100 GB/month out of AWS is free organization-wide and is not modelled here.

Interface VPC endpoints at 0.021 USD/h are the sharpest single difference for this project's operating
model: the plan already calls them "the largest hourly item" and keeps the list minimal and single-AZ, and
in São Paulo that discipline is worth exactly twice as much.

---

## 8. Compute

| Item | `sa-east-1` USD/h | `us-west-2` USD/h | Ratio |
|---|---|---|---|
| EC2 `t4g.nano` (0.5 GiB) | 0.0067 | 0.0042 | 1.60 |
| EC2 `t4g.small` (2 GiB) | 0.0268 | 0.0168 | 1.60 |
| EC2 `t4g.large` (8 GiB) | 0.1072 | 0.0672 | 1.60 |
| EC2 `t3.large` (8 GiB, x86) | 0.1344 | 0.0832 | 1.62 |
| EC2 `m5.large` (8 GiB, x86) | 0.1530 | 0.0960 | 1.59 |
| EBS `gp3` storage (USD/GB-mo) | 0.152 | 0.08 | 1.90 |
| EBS `gp3` provisioned IOPS (USD/IOPS-mo) | 0.0095 | — | |
| EBS snapshot storage (USD/GB-mo) | 0.068 | — | |
| SageMaker Studio JupyterLab `ml.t3.medium` | 0.081 | 0.050 | 1.62 |
| SageMaker notebook instance `ml.t3.medium` | 0.081 | 0.050 | 1.62 |
| SageMaker processing `ml.t3.medium` | 0.066 | — | |
| SageMaker notebook EBS (USD/GB-mo) | 0.266 | — | |
| Fargate vCPU / memory | 0.0696 / 0.0076 | 0.04048 / 0.004445 | 1.72 |
| Fargate ARM vCPU / memory | 0.0557 / 0.00612 | 0.03238 / 0.00356 | 1.72 |

`t4g` (Graviton) is ~20% cheaper than `t3` for the same memory in both regions, which is the sizing
argument D8 makes for GitLab, and it holds in São Paulo unchanged.

---

## 9. What moving to São Paulo would actually change

**One thing that is not a price at all: `AWS CodeArtifact does not exist in sa-east-1`.** It is offered in
thirteen Regions — `us-east-1`, `us-east-2`, `us-west-2`, `ap-south-1`, `ap-southeast-1`,
`ap-southeast-2`, `ap-northeast-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `eu-west-3`, `eu-south-1`,
`eu-north-1` — and São Paulo is not among them. The Region check recorded in `GENERAL_PLAN.md` §4 on
2026-08-07 missed this, and it matters twice: **D14** puts CodeArtifact in the supply chain, and **egress
design B (D5)** depends on it as the *only* package path when there is no NAT. In São Paulo, design B as
written is not buildable; it would need a self-hosted proxy (devpi, a Cargo mirror such as panamax) or
design A only.

**And the numbers:**

| Figure | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| Monthly floor (§2) | ~USD 27-40, central ~33 | ~USD 21-27, central ~23 | ~1.4x |
| Typical lab hour (§3) | ~USD 0.37 | ~USD 0.19 | ~1.9x |
| Full-stack hour (§3) | ~USD 0.79 | ~USD 0.41 | ~1.9x |
| **Projection at 20 h/month** | **~USD 40-49** | **~USD 29-31** | |
| Against the D12 ceiling of USD 50 | essentially no headroom | ~USD 20 of headroom | |

So the answer to "could this project run in São Paulo?" is: **technically yes except for CodeArtifact, but
it would sit against the USD 50 ceiling rather than comfortably under it** — and the first overrun would be
a session that leaves a NAT gateway and nine interface endpoints up for a full day: 24 h × 0.282 =
**USD 6.77** in `sa-east-1` against 24 h × 0.135 = USD 3.24 in `us-west-2`.

---

## 10. Free, or not separately metered

Worth stating explicitly, because their absence from the tables above is a fact and not an omission:

AWS Organizations, AWS Control Tower itself (you pay for what it provisions — Config, CloudTrail, S3 — not
for the service), IAM and IAM Identity Center, AWS Budgets (first two budgets), IAM Access Analyzer
external-access findings, AWS Cost Anomaly Detection, VPC / subnets / route tables / internet gateway /
security groups / NACLs, S3 gateway VPC endpoints, ECR pull-through cache (you pay only for the stored
images), SageMaker Studio **domains** and user profiles at rest (only running apps and home-directory
storage bill), and the first 30 days of GuardDuty per account.

---

## 11. What this file does not price

Anything whose volume is unknown until the environment runs: Config configuration items during a heavy
`terraform apply`, CloudTrail data events under a Spark job, GuardDuty log volume, Macie GB inspected,
Athena TB scanned, EFS throughput, inter-AZ traffic driven by the AZ-mapping question in
`GENERAL_PLAN.md` §9 item 3, and the domain registration itself (registrar price, per TLD). Stage 12
replaces the estimated rows in §2 and §3 with figures from the real bill; the per-unit rates in this file
do not change at that point — only the quantities they are multiplied by.
