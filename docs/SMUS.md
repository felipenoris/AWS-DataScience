# SageMaker Unified Studio — blueprints and configuration

A reference for what the SMUS/DataZone-V2 surface is made of, written 2026-08-19 while preparing
Stage 6's decisions. Prices quoted are the measured ones from [`PRICING.md`](PRICING.md) (Lesson 6 —
a cell without a number means *not measured yet*, never *free*). Source pages are in
[`REFERENCES.md`](REFERENCES.md), the 2026-08-16 documentation-pass block. **The blueprint
categories below were decided by the user on 2026-08-19**; folding them into Stage 6's decision
rows (4 and 5) and into `./aws/studio.py`'s `US-3` is owed when that stage's execution is prepared.

## Blueprints

An **environment blueprint** is a provisioning template owned by AWS. It works in two steps:

1. **Enabling it in an associated account** (Stage 6 step 1.4 —
   `aws_datazone_environment_blueprint_configuration`) registers the template in that member
   account, naming the provisioning role, the manage-access role and the VPC parameters it may use.
   Enabling by itself creates no billed resource.
2. **A project uses it**: when a project whose profile targets that account exercises the blueprint,
   DataZone provisions the real resources the template describes — into the member account, through
   the registered provisioning role.

A blueprint is therefore a **capability gate, not an example**: enabled, the feature exists in the
portal for every project the profile admits and the service holds the right to create those
resources in the account; disabled, the feature is absent. Three consequences follow:

- **The cost lever of Unified Studio is which blueprints exist**, not the domain (D26; the domain's
  metadata is cents per month, `PRICING.md` §5). What a blueprint provisions ranges from
  pay-per-use to billed-hourly-while-existing — the billing-shape column below — and the D12 budget
  notifies nobody, so a standing resource a project click created is the expensive kind of surprise.
- **Every enabled blueprint adds service-authored principals** (Lesson 17) and one more
  reconciliation surface the D13 boundary must survive (INT-15, Stage 6 verification (v)).
- **Enabling is cheap to do later** (one Terraform resource per account); disabling after
  environments were provisioned from it is not symmetrical. Start minimal.

### The three categories (user decision, 2026-08-19)

Mechanically, *every* blueprint requires a Terraform apply to exist — what distinguishes the
categories is what must happen **before** that apply:

| Category | Meaning | To enable |
|---|---|---|
| **1 — enabled by default** | in the step 1.4 map from the stage's first apply | nothing — born with the stage |
| **2 — on demand** | already authorized, with a **named trigger**; outside the map until it fires | commit + apply when the trigger fires — and the price measured at that moment if the row below lacks one (Lesson 6) |
| **3 — disabled** | outside the decision | an **amendment to Stage 6 decision 5**: price measured first, recorded in the stage log, then commit + apply. The *never* subset requires reopening an earlier decision instead |

The `US-3` allow-list in [`aws/studio.py`](../aws/studio.py) holds **category 1**; a category-2
blueprint joins the constant in the same commit that adds it to the step 1.4 map, so the check and
the code never disagree (Lesson 14).

### The eleven blueprints

The full list, from the *Supported blueprints* admin-guide page (read 2026-08-16 — there is no
"ML experience" blueprint; the per-project SageMaker AI domain comes from **Tooling**, correcting
D26's wording). Billing **shape** is read from documentation; billing **numbers** only where
`PRICING.md` measured them.

#### Category 1 — enabled by default

| Blueprint (API name) | What it provisions when a project uses it | Billing shape and measured cost (`us-west-2`) |
|---|---|---|
| `Tooling` | The project's basic environment: the per-project **SageMaker AI domain**, project roles, security groups, the project S3 location — and the parameter surface Stage 6 step 1.5 locks (`sagemakerDomainNetworkType`, idle shutdown, `maxEbsVolumeSize`, TIP). Mandatory — nothing else provisions a working environment | Per **app-hour running** (`ml.t3.medium` JupyterLab/Code Editor at **USD 0.050/h**, `PRICING.md` §8) + EBS. An open app bills whether used or not — the step 8 idle shutdown is what converts "up" into "in use" |
| `LakehouseCatalog` / `LakeHouseDatabase` (`DataLake`) | The catalog/SQL surface on the Glue + Lake Formation substrate Stage 5 built — the query path D13 depends on. **Which variant(s) is Stage 6 decision 4's call at execution** (recommendation: start with `LakehouseCatalog` alone) | **Per use**: Athena SQL **USD 5.00/TB scanned** (`PRICING.md` §5); Glue catalog negligible at lab scale. No standing resource |
| `EMRServerless` | An EMR Serverless application per project — the VPC-capable Spark runtime replacing the Athena-Spark default (open question 12; Stage 6 decision 1) | **Per use**: **USD 0.0526/vCPU-h + 0.0058/GB-h** (x86; ARM cheaper), billed only while a session runs (`PRICING.md` §5). The *pre-initialized capacity* option would be standing — not used |
| `AmazonBedrockGenerativeAI` | The Bedrock generative-AI app surface (chat/flow apps over Bedrock models) — the `objectives.md` AI-models feature (`bedrock:*` + SageMaker inference, Stage 1c's feature→API table) | **Per use** — token-billed (on-demand), no standing resource. **Not measured: a `PRICING.md` row is owed before the Stage 6 apply** (the upkeep rule — a row for every new service referenced), and under `VpcOnly` the Bedrock runtime endpoint(s) join the step 4.2 list at +USD 0.010/h each |

#### Category 2 — on demand (authorized; named trigger, then commit + apply)

| Blueprint (API name) | What it provisions | Billing shape | Trigger |
|---|---|---|---|
| `Workflows` (OnDemand) | A **provisioned MWAA (Airflow) environment** — billed hourly while it exists | **Standing**: MWAA `mw1.micro` **≈ USD 211.70/month** left up (`PRICING.md` §1) — the shape D7 rejected for daily use | **D28's documented last-rung fallback**: enabled only if INT-14's chain falls through at Stage 10 (`awscc_mwaaserverless_workflow`, then the CFN wrapper, then this) — and then as `[E]`, torn down between uses. The *serverless* Workflows surface is separate: Stage 10 verification (i) finds what enables it |
| `MLExperiments` | An **MLflow tracking server** for the project | **Standing** — the server bills per hour while up (no idle shutdown like the apps have) + storage; **not measured**. Known floor under `VpcOnly`: the `aws.sagemaker.us-west-2.mlflow` interface endpoint, +USD 0.010/h per account | Experiment tracking concretely needed; **measure the tracking-server price first** (Lesson 6) |

#### Category 3 — disabled (enabling requires amending the decision)

| Blueprint (API name) | What it provisions | Billing shape | Note |
|---|---|---|---|
| `RedshiftServerless` | A Redshift Serverless workgroup + namespace | Per use with a **per-query RPU minimum** + storage — a second, larger query bill on top of Athena's (`PRICING.md` §5) | **Never** — excluded by **D26/D12**; enabling means reopening those decisions, not amending this one. `US-3` fails if it appears, with its own message |
| `EMRonEC2` | EMR clusters on EC2 instances | Standing in practice — instance-hours + EMR uplift while the cluster exists; a forgotten cluster bills on. Not measured | disabled by decision (was unowned until 2026-08-19) |
| `PartnerApps` | Third-party partner ML applications | Standing/subscription — partner license + deployed infrastructure; varies by partner. Not measured | idem |
| `Quicksight` | The QuickSight analytics/dashboard surface | Subscription — per author/month + per reader session. Not measured | idem |

## SageMaker configuration

### `VpcOnly` — where the traffic runs

When `Tooling` provisions a project's SageMaker AI domain, the domain is created in one of two
network modes:

| Mode | Where app traffic runs |
|---|---|
| `PublicInternetOnly` | apps run with direct internet access through an **AWS-managed** network — outside the account's VPC, routes, security groups and flow logs |
| `VpcOnly` | apps attach ENIs **inside the account's private subnets** — every packet crosses the account's own routes, security groups and flow logs |

**Why this is load-bearing here:** the whole data perimeter
([`architecture.md`](plan/architecture.md) §4.2) is built from controls that only see traffic
inside the VPC — the gateway/interface **endpoint policies** (Stage 3's S3 allow-list), the
**`aws:SourceVpce`** conditions on bucket policies, the **flow logs**, and both D5 egress designs.
An app in `PublicInternetOnly` reads the lake and talks to the internet without touching any of
them: "private by default" would be true of the account and false of the thing the data scientist
actually runs. The same logic disables Athena Spark (it does not support VPC — open question 12,
Stage 6 step 1.6).

**The consequences of choosing it:**

- Apps have **no internet**, so every AWS service they reach needs a **VPC interface endpoint** in
  the account — the admin guide's required list is `athena`, `datazone`, `ec2`, `ec2messages`, `q`,
  `s3`, `sagemaker.api`, `sagemaker.runtime`, `glue`, `kms`, `secretsmanager`, `sts`, `ssm`,
  `ssmmessages` (read 2026-08-19; `REFERENCES.md`), plus per-blueprint optional ones. Each costs
  **USD 0.010/h** (~USD 7/month) per account, continuously — the hidden fixed cost a new blueprint
  can carry.
- One required entry cannot be satisfied in-Region: the `q` row pairs with
  `com.amazonaws.us-east-1.codewhisperer`, *available only in `us-east-1`* — a `us-west-2` VPC
  cannot reach it through an interface endpoint at all (Stage 6 step 4.2 records what that breaks).

**How it is enforced, not just chosen:** `VpcOnly` is already the blueprint **default** (read
2026-08-16). Stage 6 step 1.5 sets `sagemakerDomainNetworkType = VpcOnly` in both project profiles
and marks the parameter **non-Editable** — the *Editable* flag is what turns a default into a
control (Lesson 5): the parameter exists so nobody can flip a project to `PublicInternetOnly`.
