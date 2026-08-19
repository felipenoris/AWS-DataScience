# SageMaker Unified Studio — the object model, blueprints, configuration

A reference for what the SMUS/DataZone-V2 surface is made of, written 2026-08-19 while preparing
Stage 6's decisions; **the object-model and S3 sections were added later the same day**, from the
terminology page and the project-profile admin pages (their links: [`REFERENCES.md`](REFERENCES.md),
beside the 2026-08-16 documentation-pass block). Prices quoted are the measured ones from
[`PRICING.md`](PRICING.md) (Lesson 6 — a cell without a number means *not measured yet*, never
*free*). **The blueprint categories below were decided by the user on 2026-08-19 — Stage 6
decisions 4 and 5, recorded in [the stage log](log/log-stage-06-unified-studio.md)**;
`./aws/studio.py`'s `US-3` measures them.

## The object model — domain, project, and the profiles between them

Definitions quoted below are the documentation's wording, read 2026-08-19.

### Domain

The domain **is** the SMUS instance: "the organizing entity for connecting together your assets,
users, and their projects" — one portal URL (AWS-issued; D15 phase 1 needs no domain of ours), one
sign-on wiring (IdC here), one **SageMaker Catalog**, whose scope is the domain: what a project
publishes is discoverable by every project in the domain, and by nothing outside it. Mechanically it
is `aws_datazone_domain` with `domain_version = "V2"` — without that argument the same resource
creates plain DataZone (V1), which is *not* Unified Studio ([`GLOSSARY.md`](GLOSSARY.md)).

Three properties this design leans on:

- **A domain is a registry, not a runtime** — Stage 6's most-easily-misread sentence. It holds
  projects, profiles, blueprint configurations and the catalog; all compute comes from blueprints,
  and no blueprint is enabled in the domain account. Here the domain lives in `Data Governance`,
  where `sagemaker:Create*` is denied (1c step 7.6) — a denial that stays free precisely because of
  this split (Stage 6 step 0.4).
- **Member accounts join by *account association*** — console-only (**no public API**, read
  2026-08-16): a RAM share DataZone initiates, invitations expiring in 7 days. Sandbox and
  Development are associated; **Staging and Production never are** (D28).
- **The domain and IdC must share a Region** (Stage 6 step 1.1) — `us-west-2` twice, and neither can
  move afterwards.

Inside a domain, **domain units** subdivide it: assets and authorization policies (project creation,
project membership, environment-profile creation, glossary creation, …) can be organized and granted
at domain-unit grain. Nothing in this plan creates one — the admission control this design needs
rides on the two project profiles and the IdC groups.

**The name trap:** the per-project **SageMaker AI domain** the Tooling blueprint provisions in the
member account is the classic Studio object — apps, spaces, EBS volumes — and shares nothing with
the SMUS domain but the word. One SMUS domain ↔ many projects; each project ↔ its own SageMaker AI
domain.

### RAM under this surface

RAM is AWS **Resource Access Manager** — the cross-account sharing service, never memory
([`GLOSSARY.md`](GLOSSARY.md) owns the definition). It is the machinery under two SMUS seams, one
visible and one that should stay invisible:

- **Account association *is* a RAM share** the domain initiates on your behalf
  (`AWSRAMPermissionDataZoneDefault`) — which is why there is no public API for it and why an
  unaccepted invitation expires in 7 days (§Domain above).
- **Cross-account catalog access rides Lake Formation cross-account sharing, which rides RAM.** The
  substrate is already exercised: Stage 5's TBAC shares are RAM shares, measured at INT-11's close
  as 4 `ACTIVE` with **0 invitations** in both consumers — the zero is Stage 1d step 11's
  `ram enable-sharing-with-aws-organization` doing its job. Without the org-wide enablement, every
  recreated share is a hand-accepted invitation (INT-11's fallback column prices that tax). A
  catalog subscription fulfilled across accounts lands on this same path.
- The organization half lives in Management: `ram.amazonaws.com` is a trusted-access principal, with
  `AWSServiceRoleForResourceAccessManager` (INV-09).

### Project

The unit the data scientist inhabits. The docs give it three capabilities, worth keeping in their
words: "business context for the user's work", "a collaboration boundary", and "a permissions
boundary which gives users access to all the project artifacts and data/compute permissions after
the users are added". A domain holds several projects; a user can sit in several; the creator
becomes the first **owner**, and owners add **members** (owners or contributors). Artifacts stay
inside the project unless published to the catalog.

What a project physically *is* in the member account is whatever the blueprints its profile bundles
have provisioned: the SageMaker AI domain and its apps (Tooling), the project roles, the
consumer-side Glue database and Athena workgroup (`DataLake`), the project S3 path (§S3 below), the
file storage.

One console sentence deserves quoting, because it is AWS's own argument for this design's shape:
"Projects do not provide strong security isolation. To limit cross-domain and cross-project resource
discovery you can consider creating projects in separate accounts." That is what the two profiles
pinned to two accounts do (D21/D35): the *account* boundary carries the isolation the project
boundary does not.

### The project's "permissions boundary" — grant-shaped, and a name collision

The third capability in the definition above is a boundary of **membership**: being added to the
project is what *grants* — the project roles' powers, and the data the project subscribed to. It is
a concession mechanism wearing a restriction's name, and what it can natively restrict is thin:

- the member's **designation** — owner vs contributor — plus the domain's authorization policies
  over who creates projects, who joins, who assumes ownership;
- the **surface** — inherited from the profile: which blueprints exist, which parameters are locked.
  The member does not choose it; it came with the mold;
- **which assets the project reaches** — every catalog asset crosses a subscription request approved
  by the producer project. Membership ≠ access to the domain's data.

What it does not hold is the isolation sentence quoted above — so every restriction this design
actually counts on lives *outside* the project object, in four layers whose intersection is the
answer (Lesson 28):

| Layer | The control |
|---|---|
| the **IAM permissions boundary** — the literal object | `awsds-<env>-project-boundary` (Stage 6 step 2.1; name contract `US-8`), imposed on the roles the blueprint authors: no `s3:*` on LF-registered prefixes (D13), the drop-box `PutObject` + lake-data-key KMS pair as the one sanctioned direct write. Whether it **survives blueprint reconciliation** is INT-15, measured at step 2.5 |
| OU SCPs | reach every IAM principal in the member accounts, project roles included — why the Athena Spark disable is an SCP (step 1.6), never an edit to blueprint-authored policies (Lesson 11) |
| Lake Formation | what a project *queries* is governed by LF grants, not IAM — broad IAM with no grant reads no table (Lesson 28's producer-README section) |
| network | `VpcOnly` non-Editable, the endpoint policies, both egress designs (§`VpcOnly` below) |

**The name collision, named:** the docs' "permissions boundary" (membership, above) and the IAM
*permissions boundary* ([`GLOSSARY.md`](GLOSSARY.md): a policy capping what a role can ever be
granted) are two objects sharing three words. The D13 control is the IAM one; a sentence saying
"the project's permissions boundary" without qualification is ambiguous in exactly the way this
file exists to prevent.

### Project profile

"A template for projects … a collection of blueprints, which are configurations used to create
projects. A project profile can define if a particular blueprint is enabled during the creation of
the project, or available later for the project users to enable on demand." Domain-admin-only,
created in the domain account (Stage 6 step 1.5). What one fixes, per the custom-create console flow
(read 2026-08-19):

| Field | What it fixes |
|---|---|
| the blueprint set | which capabilities projects born of it can ever exercise — carried as environment configurations, § below |
| account and Region | pinned per profile, **or** deferred to project creation (all associated accounts, or *account pools*). Here: pinned — `experimentation` → Sandbox, `engineering` → Development |
| Tooling deployment settings | the parameter surface step 1.5 locks: `sagemakerDomainNetworkType = VpcOnly`, idle shutdown, `maxEbsVolumeSize`, TIP (decision 2) — **non-Editable** (Lesson 5: the *Editable* flag is what turns a default into a control) |
| project files storage | Amazon S3 or a Git repository (§S3 below) |
| authorization | which users/groups may create projects from it — grantable domain-wide or per domain unit |
| readiness | a profile can exist disabled, to be customized before anyone can instantiate it |

The two profile names are a contract with `./aws/studio.py` (`US-4`).

### Environment configuration

The per-blueprint entry *inside* a project profile — the grain the `CreateProjectProfile` API takes.
Each one names the blueprint it exercises, the target account and Region, a **deployment mode**
(*on create*: provisioned the moment the project is born; *on demand*: sits in the portal until a
project member enables it — the API spelling of the enabled-vs-available distinction in the profile
definition above), and the blueprint's parameters, **each with its own Editable flag**. One profile
holds one per blueprint it bundles. Both SMUS levers this project pulls live at exactly this grain:
*which account* a project provisions into, and *which parameters* its creator can no longer change.

### Environment — and the V1 "environment profile"

An **environment** is what exercising one blueprint leaves behind: the provisioned resource set for
one project × blueprint × account. The portal shows it inside the project; the resources are real,
in the member account. Conventions §6's rule follows: the `sagemaker/` slices declare *prerequisites
only, never a project environment* — DataZone owns environments, and a Terraform resource for one
would fight the blueprint (Stage 6 step 2.1).

An **environment profile** is the *DataZone-V1* template: one blueprint × account × parameters,
created within a project, from which project members then created environments by hand — the flow
`aws_datazone_environment_profile` / `CreateEnvironmentProfile` serve. In V2 that role moved into
the project profile's environment configurations — the choice of surface moved from the project
member (after creation) to the domain admin (before). The entity survives in V2's authorization
model (a blueprint configuration carries "create environment profiles using this blueprint"
policies, grantable to projects and to domain-unit owners) but nothing in this plan touches it. The
practical rule has Lesson 32's shape: **material speaking "environment profile" is V1-flow
material** — for this V2 domain the object to write is the project profile (the `aws-ia` module's
`project-profile` submodule, Stage 6 step 1.2).

### The chain, in one place

blueprint (AWS-owned template)
→ **blueprint configuration** — enabled per domain × member account, naming the provisioning role,
the manage-access role and the VPC parameters (step 1.4)
→ **environment configuration** — a project profile bundles it: account, Region, mode, locked
parameters
→ **project profile** — the template an authorized user instantiates (step 1.5)
→ **project** — the registry object in the domain
→ **environment** — the provisioned resources in the member account, one per exercised blueprint.

| Object | Written by | Lives in | In this design |
|---|---|---|---|
| blueprint | AWS | the service | the eleven below (custom blueprints exist as a console feature; outside decision 5, so outside `US-3`'s allow-list) |
| blueprint configuration | Terraform, per member account (1.4) | domain × account | category 1's four, in Sandbox and in Development |
| project profile + its environment configurations | domain admin (1.5) | the domain | `experimentation`, `engineering` |
| project | an authorized user, in the portal | the domain (registry) | step 2.4's throwaway first |
| environment | DataZone, through the provisioning role | the member account | read back by `US-8` / step 2.5 |
| environment profile | the V1 flow | — | none, by design |

## Blueprints

An **environment blueprint** is a provisioning template owned by AWS. It works in two steps:

1. **Enabling it in an associated account** (Stage 6 step 1.4 —
   `aws_datazone_environment_blueprint_configuration`) registers the template in that member
   account, naming the provisioning role, the manage-access role and the VPC parameters it may use.
   Enabling by itself creates no billed resource.
2. **A project uses it**: when a project whose profile targets that account exercises the blueprint,
   DataZone provisions the real resources the template describes — into the member account, through
   the registered provisioning role. The resource set this leaves behind is an **environment**
   (§object model above).

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
D26's wording; **re-read 2026-08-19 for the per-blueprint resource lists — which caught
`LakehouseCatalog` being Redshift-backed**, Stage 6 decision 4). Billing **shape** is read from
documentation; billing **numbers** only where `PRICING.md` measured them.

#### Category 1 — enabled by default

| Blueprint (API name) | What it provisions when a project uses it | Billing shape and measured cost (`us-west-2`) |
|---|---|---|
| `Tooling` | The project's basic environment: the per-project **SageMaker AI domain**, project roles, security groups, the project S3 location — and the parameter surface Stage 6 step 1.5 locks (`sagemakerDomainNetworkType`, idle shutdown, `maxEbsVolumeSize`, TIP). Mandatory — nothing else provisions a working environment | Per **app-hour running** (`ml.t3.medium` JupyterLab/Code Editor at **USD 0.050/h**, `PRICING.md` §8) + EBS. An open app bills whether used or not — the step 8 idle shutdown is what converts "up" into "in use" |
| `LakeHouseDatabase` (API name **`DataLake`**) | Per project: **Glue databases, Lake Formation permissions, an Athena workgroup** — the catalog/SQL surface on the Glue + LF substrate Stage 5 built, the query path D13 depends on (Stage 6 decision 4: this variant alone; `LakehouseCatalog` is category 3) | **Per use**: Athena SQL **USD 5.00/TB scanned** (`PRICING.md` §5); Glue catalog negligible at lab scale. No standing resource |
| `EMRServerless` | An EMR Serverless application per project — the VPC-capable Spark runtime replacing the Athena-Spark default (open question 12), and **the only engine whose compute connection documents an LF fine-grained mode** (`project.spark.fineGrained`; the notebook Spark Connect path is full-table on every engine). **Contingent on Stage 6 decision 1, reopened 2026-08-19**: under `VpcOnly` it asks for **four** optional endpoints against Glue interactive sessions' one (≈USD 0.06/h across both Interactive accounts under Stage 3's single-AZ rule, while the `egress/` slices are up — the decision row carries the corrected numbers and the two in-stage readings) — if that decision lands on Glue sessions, this row leaves the map (Glue needs no blueprint) | **Per use**: **USD 0.0526/vCPU-h + 0.0058/GB-h** (x86; ARM cheaper), billed only while a session runs (`PRICING.md` §5). Near-standing tail: a **started** interactive application keeps one 4 vCPU/16 GB kernel worker even with no *pre-initialized capacity* configured (`autoStop` 30 min idle; the 60-min kernel timeout is not configurable) |
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
| `LakehouseCatalog` | A new catalog in the SageMaker Lakehouse **backed by Amazon Redshift Managed Storage** — *not* the Glue/Athena surface its name suggests (the 2026-08-19 re-read; Stage 6 decision 4) | RMS storage + the Redshift query path — the same cost family D12 excluded. Not measured | disabled by decision 4 (2026-08-19); the Glue/Athena form this project uses is `DataLake`, category 1 |
| `EMRonEC2` | EMR clusters on EC2 instances | Standing in practice — instance-hours + EMR uplift while the cluster exists; a forgotten cluster bills on. Not measured | disabled by decision (was unowned until 2026-08-19) |
| `PartnerApps` | Third-party partner ML applications | Standing/subscription — partner license + deployed infrastructure; varies by partner. Not measured | idem |
| `Quicksight` | The QuickSight analytics/dashboard surface | Subscription — per author/month + per reader session. Not measured | idem |

## S3 — the project's own storage, and where the lake is not

Four distinct S3 relationships meet the SMUS surface; confusing any two of them costs an afternoon.
All read 2026-08-19 except where dated otherwise.

**1. The project S3 path — the project's working storage.** Purpose, in the doc's words: "a secure,
project-isolated location for storing temporary execution data and other project-related artifacts",
structured `<bucket>/<domain_id>/<project_id>/<project_scope>/` "to ensure separation between
projects". Three named tenants: "the location for the provisioned consumer AWS Glue database, Athena
Workgroup output, and temporary storage for individual workflow runs". The bucket pattern in AWS's
2025-09 shared-storage announcement is `amazon-datazone-<account-id>-<region>-<domain-id>`; the
`shared/` scope mounts as a folder in JupyterLab and Code Editor (a space's *personal* work is its
EBS volume, not S3). **Not yet observed in this project** — the exact bucket, which account it lands
in for a profile pinned to a member account, and who creates it (domain setup or the Tooling
provisioning) are read at Stage 6 step 2.4's throwaway project (Lesson 16: record every field).

**2. Project files storage — S3 or Git.** A project-profile field. The terminology page still says a
default CodeCommit git connection is provided; the 2025-09 announcement makes S3 the default, born
of CodeCommit's deprecation. Two spellings of one object (Lesson 32) — what the console actually
offers is recorded when step 1.5 runs, and the GitLab connection is Stage 7's surface
(INT-09/INT-13).

**3. The lake — reached through the catalog, never mounted.** Governed data enters a project by
publish/subscribe on the SageMaker Catalog, fulfilled on the Lake Formation substrate Stage 5 built
(the TBAC shares; applied grants in `docs/AWS_STATE.md`'s register). The `DataLake` blueprint
provisions the *consumer-side* Glue database and workgroup, whose **output** lands in the project
path — the `awsds-data-*` buckets themselves stay behind Lake Formation. The enforcement that keeps
it that way is D13's boundary (Stage 6 step 2.1): no `s3:*` on LF-registered prefixes for project
roles, with the drop-box `PutObject` on the dated prefix as the one sanctioned direct write
([`GOVERNANCE.md`](GOVERNANCE.md) §Drop-box, INT-10).

**4. Existing buckets as catalog assets.** An existing bucket or prefix can be published into the
catalog as an **S3 Object Collection** asset — a curated, versioned *metadata* object under
subscription rules. No stage uses it: this lake's path into the catalog is tables on the LF
substrate, not object collections.

Three buckets in a member account all answer to "working storage", and are three different objects:

| Bucket | Created by | Holds |
|---|---|---|
| the project path (`amazon-datazone-…`) | the service (2.4's reading settles by which hand) | `shared/` files, the blueprint workgroup's Athena output, workflow temp, the consumer Glue database location |
| `awsds-<env>-derived` | `consumer-data` (Stage 5 pass 4a) | the persona's derived zone — per-user write, persona-grain read, the `scratch/` prefix |
| `awsds-<env>-athena` | `consumer-data` (Stage 5 pass 4a) | the **enforced** workgroup's results (10 GiB, → `results/`) |

The last row is a boundary worth stating: pass 4c scoped the persona's Athena run family to the two
*enforced* workgroup ARNs, and a blueprint-provisioned project workgroup is a third workgroup
outside that scope — exercised by project roles, not by the persona. Whether the two query paths
stay parallel or converge (TIP — Stage 6 decision 2) is Stage 6's to measure, not this file's to
assert.

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
actually runs. The same logic disables Athena Spark — its sessions and executors run outside the VPC
(no `NetworkConfiguration` in the API; the 2026-04 PrivateLink release moved only where a session is
reached *from*, not where it runs — open question 12, Stage 6 step 1.6).

**The consequences of choosing it:**

- Apps have **no internet**, so every AWS service they reach needs a **VPC interface endpoint** in
  the account — the admin guide's required list is `athena`, `datazone` + `datazone-fips`, `ec2`,
  `ec2messages`, `q`, `s3`, `sagemaker.api`, `sagemaker.runtime`, `glue`, `kms`, `secretsmanager`,
  `sts`, `ssm`, `ssmmessages` (re-read 2026-08-19; `REFERENCES.md` — Stage 6 step 4.2 points here
  rather than carrying a second copy), plus per-blueprint optional ones. Each costs
  **USD 0.010/h** (~USD 7/month) per account, continuously — the hidden fixed cost a new blueprint
  can carry.
- One required entry cannot be satisfied in-Region: the `q` row pairs with
  `com.amazonaws.us-east-1.codewhisperer`, *available only in `us-east-1`* — a `us-west-2` VPC
  cannot reach it through an interface endpoint at all (Stage 6 step 4.2 records what that breaks).

**How it is enforced, not just chosen:** `VpcOnly` is already the blueprint **default** (read
2026-08-16). Stage 6 step 1.5 sets `sagemakerDomainNetworkType = VpcOnly` in both project profiles
and marks the parameter **non-Editable** — the *Editable* flag is what turns a default into a
control (Lesson 5): the parameter exists so nobody can flip a project to `PublicInternetOnly`.
