# SageMaker Unified Studio — blueprints and configuration

A reference for what the SMUS/DataZone-V2 surface is made of, written 2026-08-19 while preparing
Stage 6's decisions. **Descriptive, not normative**: which blueprints this project enables is decided
in [`stage-06-unified-studio.md`](plan/stages/stage-06-unified-studio.md) (decisions 1, 4, 5) and
recorded in its log; prices quoted here are the measured ones from [`PRICING.md`](PRICING.md)
(Lesson 6 — a blank cell means *not measured yet*, never *free*). Source pages are in
[`REFERENCES.md`](REFERENCES.md), the 2026-08-16 documentation-pass block.

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
  pay-per-run (EMR Serverless) to billed-hourly-while-existing (the Workflows OnDemand MWAA
  environment, Redshift Serverless) — and the D12 budget notifies nobody, so a standing resource a
  project click created is the expensive kind of surprise.
- **Every enabled blueprint adds service-authored principals** (Lesson 17) and one more
  reconciliation surface the D13 boundary must survive (INT-15, Stage 6 verification (v)).
- **Enabling is cheap to do later** (one Terraform resource per account); disabling after
  environments were provisioned from it is not symmetrical. Start minimal.

### The eleven blueprints

The full list, from the *Supported blueprints* admin-guide page (read 2026-08-16 — there is no
"ML experience" blueprint; the per-project SageMaker AI domain comes from **Tooling**, correcting
D26's wording). "In this project" reflects the plan as written; Stage 6 decisions 4 and 5 are not
yet taken.

| Blueprint (API name) | What it provisions when a project uses it | Cost, where measured (`us-west-2`) | In this project |
|---|---|---|---|
| `Tooling` | The project's basic environment: the per-project **SageMaker AI domain**, project roles, security groups, the project S3 location — and the parameter surface Stage 6 step 1.5 locks (`sagemakerDomainNetworkType`, idle shutdown, `maxEbsVolumeSize`, TIP) | The apps it hosts: `ml.t3.medium` JupyterLab/Code Editor at **USD 0.050/h** each while running (`PRICING.md` §8) — the domain adds nothing to the hourly rate | **Enabled — mandatory**; nothing else provisions a working environment |
| `LakehouseCatalog` | The catalog/SQL surface on the Glue + Lake Formation substrate Stage 5 built — the query path D13 depends on | Athena SQL **USD 5.00/TB scanned** (`PRICING.md` §5); Glue catalog storage/requests negligible at lab scale | **Enabled** (D26's "Glue/Athena form"); whether alone or with `LakeHouseDatabase` is Stage 6 decision 4 |
| `LakeHouseDatabase` (API name `DataLake`) | The database-shaped variant of the same Lakehouse surface | As above — same Glue/Athena metering | Stage 6 decision 4: start with `LakehouseCatalog` alone, add this only when a concrete surface asks |
| `EMRServerless` | An EMR Serverless application per project — the VPC-capable Spark runtime replacing the Athena-Spark default (open question 12) | **USD 0.0526/vCPU-h + 0.0058/GB-h** (x86; ARM cheaper), billed only while a session runs (`PRICING.md` §5) | **Enabled** — Stage 6 decision 1's recommendation |
| `RedshiftServerless` | A Redshift Serverless workgroup + namespace | Not measured — its per-query **RPU minimum** would put a second, larger query bill on top of Athena's, which is why measuring was not needed (`PRICING.md` §5) | **Never enabled — excluded by D26/D12**, and `./aws/studio.py` `US-3` fails if it appears |
| `Workflows` (OnDemand) | A **provisioned MWAA (Airflow) environment** — billed hourly while it exists | MWAA `mw1.micro` **≈ USD 211.70/month** left up (`PRICING.md` §1) — the shape D7 rejected | **Off permanently** (D7/D28). The *serverless* Workflows surface is a different thing: Stage 10 verification (i) finds out what enables it (blueprint, profile parameter, or nothing) |
| `MLExperiments` | An **MLflow tracking server** for the project | Not measured. Known fixed floor under `VpcOnly`: the `aws.sagemaker.us-west-2.mlflow` interface endpoint, **+USD 0.010/h per account** (~USD 7/month), before the server itself | Off — deferred by Stage 6 decision 5 until the AI-models objective is exercised, **priced first** |
| `AmazonBedrockGenerativeAI` | The Bedrock generative-AI app surface (chat/flow apps over Bedrock models) | Not measured — token- and on-demand-billed | Off — same deferral as `MLExperiments`; the AI-models objective (`objectives.md`) maps to `bedrock:*` + SageMaker inference (Stage 1c's feature→API table) |
| `EMRonEC2` | EMR clusters on EC2 instances — standing instances while a cluster runs | Not measured | **No owning decision names it** — off by omission today; Stage 6 decision 5 should own it (allow-list, not a deny-list of three) |
| `PartnerApps` | Third-party partner ML applications | Not measured — partner-subscription billed | Same gap as `EMRonEC2` |
| `Quicksight` | The QuickSight analytics/dashboard surface | Not measured — per-user/session billed | Same gap as `EMRonEC2` |

**The gap the table makes visible:** Stage 6 decision 5 as currently written names three exclusions
(`Workflows`, `MLExperiments`, `AmazonBedrockGenerativeAI`) and leaves `EMRonEC2`, `PartnerApps`
and `Quicksight` with no owner — and `US-3` in [`aws/studio.py`](../aws/studio.py) only checks the
Redshift *absence*. The recorded recommendation is to take decision 5 as an **allow-list** —
"`Tooling`, `LakehouseCatalog`, `EMRServerless` exist; anything else is an amendment to this
decision" — and tighten `US-3` to match.

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
