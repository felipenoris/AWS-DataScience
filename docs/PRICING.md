# Pricing

Prices for region `sa-east-1`.

`us-west-2` is shown alongside it in every table, because that is the region the project actually deploys
in (`CLAUDE.md`) and the region all the estimates in `docs/plan/cost-model.md` were written for. Having both
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
offer file only when something in it changes. **The EMR Serverless and DNS Firewall rows were read on
2026-08-16** (offer files `ElasticMapReduce` 2026-07-17, `AmazonRoute53`), when the Stage 6 revision made
both services load-bearing: EMR Serverless is the VPC-capable replacement for the Athena Spark default the
stage disables, and DNS Firewall is egress design A's allowlist mechanism.

**The three `t3` rows added on 2026-08-21 came through a different door, and it is named rather
than glossed** (`t3.xlarge`/`t3.2xlarge` in §8 and §3, for Stage 6's `sandbox/buildbox/`): the
`AmazonEC2` bulk offer file for one region is hundreds of megabytes, so those were read with
**`aws pricing get-products`** — the Price List *Query* API, same catalogue, filtered server-side
on `instanceType`/`location`/`operatingSystem=Linux`/`tenancy=Shared`/`preInstalledSw=NA`/
`capacitystatus=Used`. It needs credentials where the bulk endpoint does not, which is the only
difference that matters to a reader repeating it. The numbers are still measured, not estimated,
and the `1.62` ratio they land on is the same one every other `t3` row in this file carries.

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

The `~USD 350/month` that `docs/GENERAL_PLAN.md` used to quote is `0.49 × 730 = 357.70` — `mw1.small` in
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
that — D17 keeps interactive and orchestration compute out of the deployment targets and `docs/plan/conventions.md` §6 places
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
INT-14 of the plan).

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
environment role. Against the data-perimeter design in `docs/plan/architecture.md` §4.2, that is an argument for
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

## 2. The monthly floor (`docs/plan/cost-model.md`), re-priced

Paid every month even with the lab shut down. Same rows as `docs/plan/cost-model.md`, same assumptions, both regions.

| Item | Rate (`sa-east-1`) | Rate (`us-west-2`) | `sa-east-1` /month | `us-west-2` /month |
|---|---|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | — | — | **0** | **0** |
| GitLab EBS volume (50 GB gp3) | 0.152 USD/GB-mo | 0.08 USD/GB-mo | 7.60 | 4.00 |
| Elastic IP for WireGuard (idle or in use) | 0.005 USD/h | 0.005 USD/h | 3.65 | 3.65 |
| KMS customer-managed keys (one tfstate key per Terraform-managed account, plus one data CMK per account that holds data — the lake's `alias/awsds-data-data` and each Interactive account's (D31) — plus D36's second state key `alias/awsds-prod-tfstate-pki`, created by `production/bootstrap/` on 2026-08-15 (**`production/pki/` has never existed**; it arrives at Stage 7 pass 1) — plus the supply-chain key `alias/awsds-prod-registry` (`production/registry/`) and one project key per Interactive account, `alias/awsds-<env>-project` (`terraform-modules/sagemaker-prereqs/`), **all three applied 2026-08-21**; the encryption rule's one copy is `docs/GOVERNANCE.md` §Encryption) | 1.00 USD/key-mo | 1.00 USD/key-mo | 13.00 | 13.00 |
| S3 data + state + backups (~25 GB Standard) | 0.0405 USD/GB-mo | 0.023 USD/GB-mo | ~1.50 | ~1.00 |

**The KMS row's unit is a key VERSION, not a key, and that is a rule rather than a rate** — read from
AWS's KMS pricing and key-rotation pages (`docs/REFERENCES.md`), never from the bulk API, so §0's "every
number came from the Price List API" stays exactly true: the *rate* above is the API's, this paragraph is
the documentation's. A rotation-enabled CMK bills **1 version in its first year, 2 after its first
rotation, 3 after its second, and is capped there**. Every CMK in this design sets
`enable_key_rotation = true` with no `rotation_period_in_days`, i.e. the 365-day default — measured live
2026-08-21, `True 365` on every key. **So the count cell above is a YEAR-ONE figure**: the Stage 2
bootstrap keys (created 2026-08-15) reach 2 versions around 2027-08 and 3 around 2028-08, and the same
clock starts for each later key on its own creation date. The multi-year consequence belongs to
`docs/plan/cost-model.md`'s Floor row, which already defers a full recompute to Stage 12 step 5. **The
levers, named without choosing between them:** fewer keys; rotation disabled on a *named* key — which is
not free, because FSBP `KMS.4` runs org-wide under `awsds-fsbp-only` and suppressing a control there is a
policy edit that turns that policy custom (Stage 5 step 13.3); or D12's ceiling revised.
| ECR images (~10 GB) | 0.10 USD/GB-mo | 0.10 USD/GB-mo | 1.00 | 1.00 |
| AWS Config, every governed account (**Management is the one not recorded — confirmed 2026-08-14**, verification (xiii)) | 0.003 USD/item | 0.003 USD/item | 2.50-5.00 → **billed ~0.5** | 2.50-5.00 |
| Route 53 **private** hosted zones (**3 at N=1**: `sandbox.internal` per business unit, plus `prod.internal` and `pages.internal`, both in Production — Development and Staging get none, Stage 3 step 4.2) | 0.50 USD/zone-mo (global) | 0.50 USD/zone-mo | 1.00-1.50 | 1.00-1.50 |
| Route 53 **public** hosted zone (D15 phase 2 — **Stage 13 only**) | 0.50 USD/zone-mo (global) | 0.50 USD/zone-mo | 0 → 0.50 | 0 → 0.50 |
| Public domain registration (D15 phase 2 — **Stage 13 only**) | registrar, region-independent | idem | 0 → ~1.00 | 0 → ~1.00 |
| ACM **imported** certificates (D15 phase 1 — the internal CA's leaves) | free | free | 0 | 0 |
| CodeArtifact | **not available — see §9** | 0.05 USD/GB-mo + 0.05/10k req | **n/a** | ~0.10 |
| Security Hub + IAM Access Analyzer (Security Hub **after its own 30-day free window**) | 0.001 USD/check (first 100k) | 0.001 USD/check | 1.00-2.00 | 1.00-2.00 |
| GuardDuty (after the 30-day free window) | 1.75 USD/GB, 0.000007 USD/event | 1.00 USD/GB, 0.000004 USD/event | 0 → 5.00-9.00 | 0 → 3.00-5.00 |
| WireGuard EBS (8 GB) + CloudWatch logs | 0.152 USD/GB-mo; logs 0.90 USD/GB | 0.08; logs 0.50 USD/GB | ~1.80 | ~1.00 |
| ~~EFS (shared filesystem + project storage, IA)~~ | **removed — the NFS requirement was withdrawn 2026-08-17 (D24 with it)** | | **0** | **0** |
| SageMaker unified domain — DataZone V2 metadata (D26) | 10.00/100k req + 0.40/GiB-mo (global) | idem | ~0.50 | ~0.50 |
| ~~Staging, Development, Data Governance at rest~~ | **removed — double count** | | **0** | **0** |
| **Floor** | | | **~USD 30-43** (central ~36) | **~USD 25-34** (central ~30) |

The São Paulo floor is roughly **1.25-1.4x** the Oregon one — less than the 1.72x of the metered services,
because so much of the floor is region-flat: KMS, Config, Route 53, Security Hub, the domain and the
Elastic IP are identical in both regions.

The low end of each range is the first thirty days, while GuardDuty is inside its free window; the high end
is an ordinary month with GuardDuty billing, Config at the top of its range and Security Hub at the top of
its.

**And one correction from a real bill, 2026-08-14 (Stage 1d step 10) — the first row here to move from
list-rate arithmetic to what was actually charged.** The Config row projected USD 2.50-5.00/month and the
organization is billing **~USD 0.5**. The error was not in the rate, which is right, but in the *shape*: the
projection treated configuration items as a rate per account per month, and they are an event per change.
Nine accounts recording once, at enrollment, cost USD 2.20 in a single day and then almost nothing. **What
this row is really sensitive to is churn, so it will move with the build-out and not with the account
count** — which is why the range is kept beside the measurement rather than replaced by it, and why
Stage 12 step 5 re-reads it after Stages 2-3 rather than accepting ~0.5 as steady state. **The related trap,
priced in §4 and worth naming here:** `recordingFrequency: DAILY` is *not* the cheaper mode at this change
rate — USD 0.012 per item-day against USD 0.003 per change puts the break-even at four changes per resource
per day.

**Two corrections applied on 2026-08-08, in opposite directions.** The "Staging, Development, Data
Governance at rest" row charged a Config recorder and a KMS key for those accounts a second time —
the Config row already covers every governed account — so ~USD 3 came out. The KMS row said "(3)" and
predated D20-D22; there is one customer-managed key per Terraform-managed account plus the D31 derived-zone
keys, so ~USD 3 went back in.

**And a third correction, on the same date: the `us-west-2` floor was restated from ~USD 24-30 to
~USD 25-34.** The earlier figure was carried over rather than summed; adding this table's own `us-west-2`
column row by row gives 25.25 at the low end and 33.75 at the high end. The `sa-east-1` column was already
consistent with its own rows, which is why only one side moved. The number to trust in the end is still the
one Stage 12 step 5 measures against the real bill — this is arithmetic over list rates, not an invoice.

---

## 3. Per hour of lab time (`docs/plan/cost-model.md`), re-priced

| Item | `sa-east-1` USD/h | `us-west-2` USD/h | Ratio |
|---|---|---|---|
| NAT Gateway (1) | 0.093 + 0.093/GB | 0.045 + 0.045/GB | 2.07 |
| Interface VPC endpoint (each, per AZ) | 0.021 + 0.01/GB | 0.010 + 0.01/GB | 2.10 |
| — Sandbox, 12 endpoints, single AZ (D9), design A (12 until 2026-08-17 when `elasticfilesystem` left with the NFS requirement, 11 until 2026-08-21 when `datazone` joined at Stage 6 step 4.2) | 0.252 | 0.120 | 2.10 |
| — Sandbox, 14 endpoints, design B (`datazone` is required under `VpcOnly` in either design) | 0.294 | 0.140 | (design B needs CodeArtifact — see §9) |
| — Development 12 / Staging 9 / Production 10-12 | 0.252 / 0.189 / 0.210-0.252 | 0.120 / 0.090 / 0.100-0.120 | 2.10 |
| GitLab EC2 `t4g.large` | 0.1072 | 0.0672 | 1.60 |
| — `t3.large`, the x86 equivalent | 0.1344 | 0.0832 | 1.62 |
| Stage 6 build host `t3.xlarge` (`sandbox/buildbox/`, `[E]`) | 0.2688 | **0.1664** | 1.62 |
| Internal ALB | 0.034 + 0.011/LCU-h | 0.0225 + 0.008/LCU-h | 1.51 |
| SageMaker Studio JupyterLab / CodeEditor `ml.t3.medium` | 0.081 | 0.050 | 1.62 |
| SageMaker processing job `ml.t3.medium` | 0.066 | — | |
| WireGuard EC2 `t3.nano` (`t4g.nano` at 0.0067 / 0.0042 until 2026-08-20) | 0.0084 | 0.0052 | 1.62 |
| Public IPv4 address (in use or idle) | 0.005 | 0.005 | **1.00** |
| VPC peering data (each way) | 0.01/GB | 0.01/GB | **1.00** |
| Internet data transfer out, first 10 TB (see §7 note) | 0.150/GB | 0.090/GB | 1.67 |
| Inter-region transfer to the other region | 0.16/GB out of São Paulo | 0.02/GB into São Paulo | asymmetric |

**Typical Sandbox hour** (its endpoints + one Studio app + WireGuard, plus the NAT under design A):
design A `sa-east-1` **≈ 0.46/h**, `us-west-2` **≈ 0.23/h**; design B **≈ 0.40** and **≈ 0.20**
(each up by one endpoint since 2026-08-21 — `datazone`, Stage 6 step 4.2).

**Full-stack hour** (a design-A Sandbox + GitLab + its ALB + Production's NAT **and its endpoints**):
`sa-east-1` **≈ 0.91/h**, `us-west-2` **≈ 0.47/h**.

**Both figures rose on 2026-08-08** — from 0.37/0.19 and 0.79/0.41 — for two reasons recorded in
`docs/plan/cost-model.md`: the endpoint list was missing `athena`, `glue` and `lakeformation`, without which
D13's access path has no route at all under design B; and Production's *endpoints* were never counted in a
full-stack hour, only its NAT.

Note that `docs/plan/cost-model.md` quotes NAT at USD 0.050/h in `us-west-2`; the measured gateway rate is
**0.045**, plus 0.005 for its public IPv4 — which is where the round 0.050 comes from.

---

## 4. What the USD 50 ceiling rules out (D12)

| Option | `sa-east-1` USD/month | `us-west-2` USD/month | Where it appears |
|---|---|---|---|
| Always-on GitLab (`t4g.large` + 50 GB gp3 + ALB) | 78.26 + 7.60 + 24.82 = **110.68** | 49.06 + 4.00 + 16.43 = **69.49** | D8, `docs/plan/cost-model.md` |
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
| **EMR Serverless** x86 (USD/vCPU-h · USD/GB-h) | 0.09048 · 0.00988 | 0.052624 · 0.0057785 | 1.72 |
| EMR Serverless ARM (USD/vCPU-h · USD/GB-h) | 0.07241 · 0.007956 | 0.042094 · 0.004628 | 1.72 |
| EMR Serverless storage beyond 20 GB (USD/GB-h) | 0.000211 | 0.000111 | 1.90 |
| **Lake Formation** filtering (USD per TB scanned) | 2.75 | 2.25 | 1.22 |
| Lake Formation storage optimizer (USD per TB) | 2.75 | 2.25 | 1.22 |
| Lake Formation metadata objects (USD per 100k-mo) | 1.00 | 1.00 | **1.00** |
| Lake Formation API requests (USD per 1M) | 1.00 | 1.00 | **1.00** |
| **EFS** Standard (USD/GB-mo) | 0.57 | 0.30 | 1.90 |
| EFS Standard-IA (USD/GB-mo) | 0.044 | 0.025 | 1.76 |
| EFS Archive (USD/GB-mo) | 0.0166 | 0.008 | 2.08 |
| EFS IA reads/writes (USD/GB) | 0.019 | 0.010 (read) | 1.90 |
| **ECR** storage (USD/GB-mo) | 0.10 | 0.10 | **1.00** |
| **KMS** customer-managed key, per key **version** (USD/key-version-mo) | 1.00 | 1.00 | **1.00** |
| KMS requests (USD per 10 000) | 0.03 | 0.03 | **1.00** |

Athena at 9.00 USD/TB in São Paulo makes the two cost levers in `docs/plan/cost-model.md` — **S3 Bucket Keys** and
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

- Of the two Lakehouse-named blueprints only the Glue/Athena one is enabled — `LakeHouseDatabase` (API
  name `DataLake`), Stage 6 decision 4. `LakehouseCatalog` (Redshift Managed Storage) and the separate
  `RedshiftServerless` blueprint provision a query path whose per-RPU minimum would put a second, larger
  bill on top of Athena's — excluded by decision, not omission (`docs/SMUS.md` carries the category
  table).
- The per-project SageMaker AI apps (provisioned by the **Tooling** blueprint — read 2026-08-16; D26
  wrote "ML experience", a name the blueprint list does not carry) bill exactly like the Studio apps in §8
  (`ml.t3.medium` at 0.081/0.050 USD/h) — the domain adds nothing to the hourly rate.

### Amazon Bedrock — the `AmazonBedrock*` blueprints (Stage 6 decision 5: six in category 1, `KnowledgeBase` in 2)

**Named for the console's `AmazonBedrockGenerativeAI` until 2026-08-21**, when the roster reading found that grouping has no API identifier: the domain publishes `AmazonBedrockChatAgent`, `Evaluation`, `Flow`, `Function`, `Guardrail`, `KnowledgeBase` and `Prompt` as seven separate blueprints. The rates below are unaffected — they are the model's, not the blueprint's — but **`AmazonBedrockKnowledgeBase` is NOT among the six**: it adds a shape this section does not price — a knowledge base stands up a vector store, which bills while it exists rather than per token — and it was moved to **category 2** on 2026-08-21 for exactly that reason, with a trigger that names the measurement. Price it when the trigger fires (Lesson 6), not at the first invoice. So category 1 carries **six** `AmazonBedrock*` blueprints, not seven.

**Read 2026-08-21** from `AmazonBedrock/current/{us-west-2,sa-east-1}/index.json`, both published
`2026-08-20`. The row was **owed before the Stage 6 step 1.4 apply** — the upkeep rule asks for one per
new service referenced, and decision 5 put this blueprint in category 1 with the cell empty.

**The billing shape is what matters more than any single rate: per use, token-metered, no standing
resource.** Enabling the blueprint costs nothing; a project that never opens a chat app costs nothing.
That is why it sits in category 1 beside `DataLake` rather than in category 2 beside MLflow.

On-demand, in-region, per **1 000 tokens** (`us-west-2`):

| Model | Input | Output |
|---|---|---|
| Nova Micro | 0.000035 | 0.00014 |
| Nova Lite | 0.00006 | 0.00024 |
| Nova Pro | 0.0008 | 0.0032 |
| Nova Premier | 0.0025 | 0.0125 |
| Claude 3 Haiku | 0.00025 | — |
| Claude 3 Sonnet | 0.0030 | — |

**Two gaps in that table are readings, not omissions** (Lesson 6 — a cell without a number means *not
measured*, never *free*):

- **The `us-west-2` offer file carries no `output-tokens` usagetype for any Claude model** — only
  `input-tokens`. Every current Claude model is reached through a **cross-region inference profile**, and
  those SKUs are published under the profile's home region rather than under `us-west-2`. So the two
  Claude rows above are the legacy in-region SKUs and are **not** what a SMUS chat app would actually
  bill; price the specific model against the inference profile before anyone leans on it.
- **Batch, Flex and Priority tiers exist for the Nova family** (roughly ×0.5, ×0.5 and ×1.75 of the
  on-demand rate respectively) and are not in the table because nothing in this design selects one.

**And a `sa-east-1` finding for §9, which is why the file is read in both regions:** the São Paulo offer
carries **no Claude and no Nova model at all** — its catalogue is DeepSeek, Qwen, Llama, Mistral, GPT-OSS
and friends. The Ratio column is therefore not "a premium"; it is **absent**, and a move would be a change
of *model*, not of price. That is a larger fact than any rate above.

**What this does not price:** provisioned throughput (model units by the hour — the one Bedrock shape that
*is* standing, and the one D12 would notice), model customisation, Knowledge Bases (which bill their own
vector store), and Guardrails. None is reachable from the blueprint as enabled.

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
| GuardDuty **S3 Protection** — S3 data events analyzed, first 500M/mo (each; Stage 11 step 4) | 0.00000176 | 0.0000008 | 2.20 |
| GuardDuty **Malware Protection for EC2** — EBS data scanned (USD/GB; Stage 11 step 4) | 0.06 | 0.03 | 2.00 |
| GuardDuty S3 Malware Protection data scanned (USD/GB) | 0.123 | 0.09 | 1.37 |
| GuardDuty Malware Protection for S3 — object scan requests above 1k/mo (each) | 0.000293 | 0.000215 | 1.36 |
| **Macie** S3 bucket inventory (USD per bucket-day) | 0.0033 | 0.0033 | **1.00** |
| Macie sensitive-data discovery, first tier (USD/GB) | 2.25 | 1.00 | **2.25** |
| Macie automated object monitoring (USD per 100k object-days) | 0.0225 | 0.01 | 2.25 |
| **Security Hub** checks, first 100k (each) | 0.001 | 0.001 | **1.00** |
| Security Hub finding ingestion above 10k (each) | 0.00003 | 0.00003 | **1.00** |
| **IAM Access Analyzer** internal access (USD per monitored resource per analyzer-month — charged at setup, then on the 1st; Stage 11 step 2.1) | 9.00 | 9.00 | **1.00** |
| Access Analyzer unused access (USD per IAM role/user per month; Stage 12) | 0.20 | 0.20 | **1.00** |
| Access Analyzer custom policy checks (per API request) | 0.002 | 0.002 | **1.00** |
| **Amazon Inspector** ECR enhanced scanning, initial scan (USD/image) | 0.11 | 0.09 | 1.22 |
| Inspector ECR re-scan (each — continuous scanning re-scans on every new CVE) | 0.01 | 0.01 | **1.00** |
| **Secrets Manager** secret (USD/secret-mo; `gitlab-secrets.json`, Stage 7 step 1.1) | 0.40 | 0.40 | **1.00** |
| Secrets Manager API calls (per 10k) | 0.05 | 0.05 | **1.00** |
| **CloudWatch** logs ingested, Standard class (USD/GB) | 0.90 | 0.50 | 1.80 |
| CloudWatch logs, Infrequent Access class (USD/GB) | 0.45 | — | |
| CloudWatch logs storage (USD/GB-mo) | 0.0408 | 0.03 | 1.36 |
| CloudWatch Logs Insights scanned (USD/GB) | 0.009 | 0.005 | 1.80 |
| CloudWatch standard alarm (USD/alarm-mo) | 0.135 | 0.10 | 1.35 |
| CloudWatch **custom metric**, first 10 000 (USD/metric-mo) | 0.30 | 0.30 | **1.00** |
| **SNS** API requests, above the first 1M/month (each) | 0.0000005 | 0.0000005 | **1.00** |
| SNS e-mail / e-mail-JSON notifications, above the first 1 000/month (each) | 0.00002 | 0.00002 | **1.00** |
| SNS HTTP/HTTPS notifications, above the first 100 000/month (each) | 0.0000006 | 0.0000006 | **1.00** |
| SNS SMS, per message delivered | *not in the Price List API* | *not in the Price List API* | — |
| **Route 53** hosted zone, first 25 (USD/zone-mo) | 0.50 (global) | 0.50 | **1.00** |
| Route 53 Resolver DNS Firewall, first 1B queries (USD per million) | 0.60 | — | |
| Route 53 Resolver queries, first 1B (USD per million) | 0.40 | — | |

**A metric emitted by a CloudWatch Logs metric filter is a custom metric, at USD 0.30/metric-month.** That
is three times the alarm beside it, and it is avoidable: custom metrics are metered only for the hours in
which datapoints are actually published, so a metric filter created **without a default value** publishes
nothing in a quiet month and costs nothing. This is why the break-glass filter (Stage 1a step 5) leaves the
default value empty and the alarm treats missing data as `notBreaching`, rather than emitting a `0` every
minute for the reassurance of a continuous line.

**SNS SMS is the one row in this file that could not be measured, and it is recorded as a gap rather than
guessed (Lesson 6).** The `AmazonSNS` offer file carries an `SMS` delivery-attempt SKU priced at
`0.0000000000` — that is the *attempt*, not the message; the per-message price is per destination country
and, in several countries, per carrier, and AWS publishes it only on the AWS End User Messaging SMS pricing
page and its downloadable CSV, not in the bulk API (checked `AmazonSNS`, `AmazonPinpoint` and
`AWSEndUserMessaging3pFees` on 2026-08-09 — the last two carry only WhatsApp rows for `BR`). Two facts that
make the gap tolerable here: the only SMS this environment sends is the break-glass alarm (Stage 1a step 5),
so the volume is single-digit messages per year, and **Brazil supports short codes but neither long codes nor
sender IDs**, so there is no origination identity to buy and no registration to file — AWS sends over its
shared short-code pool on a best-effort basis. The one thing to check before relying on the channel is the
**SMS sandbox**: a new account can only send to *verified* destination numbers, which is a one-time console
step and not a cost.

**Macie is the one to watch in São Paulo: 2.25x, the largest premium in this file.** The plan already says
to scope Macie to a sampled prefix rather than the whole lake (`docs/plan/cost-model.md`); in `sa-east-1` that instruction is
worth more than twice as much.

**The Access Analyzer internal-access rate is the measurement that redesigned a step (2026-08-17,
Lesson 6):** at USD 9.00 per monitored resource per month — identical in both Regions, and charged at
setup rather than prorated — six resources would exceed the entire D12 ceiling, which is why Stage 11
step 2.1 runs the analyzer as an enumerated-ARN, create-read-delete instrument instead of a standing
monitor.

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
| Route 53 Resolver **DNS Firewall** — domain stored (USD/name-mo) | 0.0005 | 0.0005 | **1.00** |
| DNS Firewall queries inspected (USD per 1M, first 1B) | 0.60 | 0.60 | **1.00** |
| Internet data transfer out, first 10 TB (USD/GB) | 0.150 | 0.090 | 1.67 |
| — next 40 TB / next 100 TB / above 150 TB | 0.138 / 0.126 / 0.114 | 0.085 / 0.070 / 0.050 | |
| Transfer São Paulo → Oregon (USD/GB) | 0.16 | — | |
| Transfer Oregon → São Paulo (USD/GB) | — | 0.02 | |

**Note on data transfer out.** Two offer files disagree. The `AWSDataTransfer` offer — the current,
unified one, and the source of the table above — gives `sa-east-1` 0.150 USD/GB for the first 10 TB. The
older per-service `AmazonEC2` offer still carries a São Paulo tier of 0.25 USD/GB. The `us-west-2` figure
of 0.090 matches what `docs/plan/architecture.md` §4.3 already assumed, which is a point in favour of the unified
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
| EC2 `t4g.micro` (1 GiB) | 0.0134 | 0.0084 | 1.60 |
| EC2 `t4g.small` (2 GiB) | 0.0268 | 0.0168 | 1.60 |
| EC2 `t4g.medium` (4 GiB) | 0.0536 | 0.0336 | 1.60 |
| EC2 `t4g.large` (8 GiB) | 0.1072 | 0.0672 | 1.60 |
| EC2 `t3.nano` (0.5 GiB, x86) | 0.0084 | 0.0052 | 1.62 |
| EC2 `t3.micro` (1 GiB, x86) | 0.0168 | 0.0104 | 1.62 |
| EC2 `t3.medium` (4 GiB, x86) | 0.0672 | 0.0416 | 1.62 |
| EC2 `t3.large` (8 GiB, x86) | 0.1344 | 0.0832 | 1.62 |
| EC2 `t3.xlarge` (4 vCPU, 16 GiB, x86) — **the Stage 6 build host** | 0.2688 | **0.1664** | 1.62 |
| EC2 `t3.2xlarge` (8 vCPU, 32 GiB, x86) | 0.5376 | 0.3328 | 1.62 |
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
| SageMaker training / batch transform `ml.m5.xlarge` (USD/h while the job runs) | 0.367 | 0.23 | 1.60 |
| SageMaker hosting (real-time endpoint) `ml.m5.xlarge` (USD/h while the endpoint exists) | 0.367 | 0.23 | 1.60 |
| SageMaker Serverless Inference (USD/s **per GB of memory**, 1-6 GB tiers, linear) | 0.00002 | 0.00002 | **1.00** |

`t4g` (Graviton) is ~20% cheaper than `t3` for the same memory in both regions, which is the sizing
argument D8 makes for GitLab, and it holds in São Paulo unchanged.

**The six burstable rows above are the same-memory pairs, measured 2026-08-20** (offer file
`AmazonEC2`, published `2026-08-20T22:12:05Z`, read from the bulk endpoint of §0 for both regions in
one sitting) — added when the WireGuard host moved off Graviton onto amd64 at the user's direction,
which is the one place in this project where that ~20% is *paid* rather than saved. The premium is
**+23.8% in `us-west-2`** and **+25.4% in `sa-east-1`**, and it is flat across the three sizes:
`0.0052 / 0.0042`, `0.0104 / 0.0084`, `0.0416 / 0.0336`. In the money that matters here — a `[D]`
host billed only while a lab session runs — the baseline `t3.nano` costs **+0.0010 USD/h** over the
`t4g.nano` it replaced, and the `t3.medium` currently selected costs **+0.0080 USD/h** over
`t4g.medium`. **Nothing about D8's GitLab sizing changes**: that argument is about an 8 GiB
always-on host, where the same ~20% is ~13 USD/month.

**The three SageMaker serving rows were measured 2026-08-16 for Stage 10 step 5, and the shape matters
more than the rate:** batch transform bills only while the job runs and Serverless Inference scales to
zero between requests — the two D11-compatible serving shapes — while a hosting **endpoint bills every
hour it exists** (0.23 × 730 ≈ **USD 168/month** for one `ml.m5.xlarge`), the model-serving analogue of
§1.1's environment fee and what rules a standing endpoint out under D12. Serverless Inference's
documented limit, recorded with its price: it supports **no VPC configuration**, so it sits outside the
network perimeter (Stage 10 decision 4 names batch transform for exactly this pair of reasons).

---

## 9. What moving to São Paulo would actually change

**One thing that is not a price at all: `AWS CodeArtifact does not exist in sa-east-1`.** It is offered in
thirteen Regions — `us-east-1`, `us-east-2`, `us-west-2`, `ap-south-1`, `ap-southeast-1`,
`ap-southeast-2`, `ap-northeast-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `eu-west-3`, `eu-south-1`,
`eu-north-1` — and São Paulo is not among them. The Region check recorded in `docs/plan/architecture.md` §4.1 on
2026-08-07 missed this, and it matters twice: **D14** puts CodeArtifact in the supply chain, and **egress
design B (D5)** depends on it as the *only* package path when there is no NAT. In São Paulo, design B as
written is not buildable; it would need a self-hosted proxy (devpi, a Cargo mirror such as panamax) or
design A only.

**And the numbers:**

| Figure | `sa-east-1` | `us-west-2` | Ratio |
|---|---|---|---|
| Monthly floor (§2) | ~USD 30-43, central ~36 | ~USD 25-34, central ~30 | ~1.25-1.4x |
| Typical lab hour (§3) | ~USD 0.38-0.44 | ~USD 0.19-0.22 | ~2.0x |
| Full-stack hour (§3) | ~USD 0.91 | ~USD 0.47 | ~1.9x |
| **Projection at 20 h/month** | **~USD 38-61** | **~USD 29-43** | |
| Against the D12 ceiling of USD 50 | **breaches it** at anything above a light month | **~USD 7** at the top of the range | |

So the answer to "could this project run in São Paulo?" changed on 2026-08-08, and not in São Paulo's
favour: **technically yes except for CodeArtifact, but it no longer fits under the USD 50 ceiling once the
data-plane endpoints are counted.** Interface endpoints carry the sharpest premium in this file (2.10x) and
the correction added three of them to every account, so São Paulo absorbed the change roughly twice over.
The first overrun there would be a session that leaves a design-A Sandbox `egress/` up for a full day:
24 h × 0.345 = **USD 8.28** in `sa-east-1` against 24 h × 0.170 = USD 4.08 in `us-west-2`.

---

## 10. Free, or not separately metered

Worth stating explicitly, because their absence from the tables above is a fact and not an omission:

AWS Organizations, AWS Control Tower itself (you pay for what it provisions — Config, CloudTrail, S3 — not
for the service), IAM and IAM Identity Center — including **centralized root access management**, both
capabilities, and the `sts:AssumeRoot` sessions it grants (Stage 1a step 6); the only cost those carry is
indirect, one break-glass SMS per privileged session — AWS Budgets (first two budgets), IAM Access Analyzer
external-access findings, AWS Cost Anomaly Detection, VPC / subnets / route tables / internet gateway /
security groups / NACLs, **AWS Resource Access Manager (the share itself is not metered; you pay for the
shared resource)**, **AWS CloudFormation** (stacks managing AWS-namespace resources are free — only
third-party resource-type handler operations bill; it is the deploy mechanism of every SMUS project
environment since 2026-08-22, one `DataZone-Env-…` stack each), S3 gateway VPC endpoints, ECR pull-through cache (you pay only for the stored
images), SageMaker Studio **domains** and user profiles at rest (only running apps and home-directory
storage bill), the first 30 days of GuardDuty per account, and — **read 2026-08-20, and it is a second,
separate window rather than the same one** — the first 30 days of **Security Hub CSPM** per account, from
that account's first enablement. The two windows open at different stages (Security Hub at Stage 5 step 13,
GuardDuty at Stage 15), so "the first thirty days" is never one date for the whole floor. **What neither
trial covers is the AWS Config cost underneath**: Security Hub's checks run as Config rules, and each
control's compliance-state change writes an `AWS::Config::ResourceCompliance` item from day one.

---

## 11. What this file does not price

Anything whose volume is unknown until the environment runs: Config configuration items during a heavy
`terraform apply`, CloudTrail data events under a Spark job, GuardDuty log volume, Macie GB inspected,
Athena TB scanned, inter-AZ traffic driven by the AZ-mapping question in
`docs/plan/open-questions.md` item 3, and the domain registration itself (registrar price, per TLD). Stage 12
replaces the estimated rows in §2 and §3 with figures from the real bill; the per-unit rates in this file
do not change at that point — only the quantities they are multiplied by.
