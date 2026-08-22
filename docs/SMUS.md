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
  2026-08-16): a RAM share DataZone initiates. Sandbox and Development are associated; **Staging and
  Production never are** (D28). **RUN 2026-08-21, and the invitation half of this line was wrong**:
  under Stage 1d's org-wide RAM enablement the share is created organization-scoped and
  **auto-accepts** — zero invitations either side, so *"invitations expiring in 7 days"* names a clock
  that never starts. §RAM below had the evidence for that before the measurement did.
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

- **Account association *is* a RAM share** the domain initiates on your behalf — which is why there
  is no public API for it. **Both particulars in this line were wrong and are now measured
  (2026-08-21).** The permission is
  **`AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`**; `AWSRAMPermissionDataZoneDefault`
  **does not exist in RAM at all** — it was a name copied out of the V1 user guide's prose, and
  `ram list-permissions --resource-type datazone:Domain` publishes six, none of them called that. It
  is also **152 actions against the resource-type default's 111**, the extras being the SMUS **V2**
  workbench surface (notebooks, cells, compute, connections, `GetDomainExecutionRoleCredentials`).
  And there is **no invitation to expire**: the share is organization-scoped, so it auto-accepts —
  the same behaviour the LF shares below already showed. **Read that permission as a CEILING on the
  share, never as access** (Lesson 28); what any principal can do is that ∩ its IAM ∩ the SCPs, and
  the Interactive OU carries no `datazone:` deny — open question 21.
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
material** — for this V2 domain the object to write is the project profile
(`awscc_datazone_project_profile`, in `terraform-live/data-governance/governance/profiles.tf` — Stage 6 step **1.5**, which this file already says twice above).

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
| blueprint | AWS | the service | the 23 in the table below (custom blueprints exist as a console feature; outside decision 5, so outside `US-3`'s allow-list) |
| blueprint configuration | Terraform, per member account (1.4) | domain × account | category 1's **eleven**, in Sandbox and in Development (applied 2026-08-21) |
| project profile + its environment configurations | domain admin (1.5) | the domain | `experimentation`, `engineering` |
| project | an authorized user, in the portal | the domain (registry) | step 2.4's throwaway first |
| environment | DataZone, through the provisioning role | the member account | read back by `US-8` / step 2.5 |
| environment profile | the V1 flow | — | none, by design |

### The installed profiles

The two project profiles this installation carries — created 2026-08-21 by the second apply of
`terraform-live/data-governance/governance/` (step 1.5), both `ENABLED`, read back by `US-4`:

| Profile | Provisions into | The unit of work (D21) | Who may create from it |
|---|---|---|---|
| `experimentation` | **Sandbox** | a notebook — experimentation happens where nothing downstream depends on it | `sso-group-data-scientists` |
| `engineering` | **Development** | a pipeline — where the promotion chain starts | `sso-group-deployment-managers` |

Identical in everything but the target account: **eleven environment configurations** (decision 5's
category 1), `Tooling` the only base — `ON_CREATE`, every other blueprint `ON_DEMAND`; a second base
cannot ride along on demand, which is what re-cut `ToolingLite` to category 3 (its row in the
blueprint table below) — and the same Tooling parameters, read back after the apply:

| Parameter | Value | Editable |
|---|---|---|
| `sagemakerDomainNetworkType` | `VpcOnly` | no |
| `lifecycleManagement` | `true` | no |
| `idleTimeoutInMinutes` | `60` | **yes** — the per-project default a member may tune, under the ceiling |
| `maxIdleTimeoutInMinutes` | `120` | no — the admin ceiling (step 8.1) |
| `maxEbsVolumeSize` | `100` (GB) | no |
| `enableTrustedIdentityPropagationPermissions` | `false` | no — decision 2, delivered |

#### Who may create a project, and from which profile

**The fourth column is a separate object from the other three, and forgetting that is how the
installation spent a day with two profiles nobody could instantiate.** A project profile is a
*template*; creating a project from it is an **authorization**, granted on a domain unit and named
`CREATE_PROJECT_FROM_PROJECT_PROFILE`. Listing the profiles in the portal is a read and needs
neither.

**Measured 2026-08-22, in step 1.7's portal sitting:** the portal offered both profiles and the
button returned `User is not permitted to perform operation: CreateProject` — **identical with the
tunnel up and down**, which is what ruled the network out. `list-policy-grants` on the root domain
unit then returned an **empty list** for `CREATE_PROJECT` *and*
`CREATE_PROJECT_FROM_PROJECT_PROFILE`, and the unit's only owner was the group profile whose
`rolePrincipalArn` is the `InfrastructureAccess` role that created the domain. So the only principal
that could create a project was the one that runs Terraform.

**The association above is the user's decision of 2026-08-22**, and the two halves are not the same
kind of claim:

- **`experimentation` → the data scientists** is a standing right. It is the Sandbox, where D21 is
  already decided.
- **`engineering` → the deployment managers** is the **instrument of D21's open half** — whether a
  person needs an interactive surface next to *Development's* data at all. It goes to the persona
  that owns the promotion chain the account exists to start, and if that question closes against the
  surface, the grant is removed. **That removal would be the expected outcome, not a regression.**

**The grain is per profile, not domain-wide** (`CREATE_PROJECT` would carry every profile the domain
gains later), and **every field of a grant is `createOnly`** in the CFN schema — there is no in-place
edit, so moving a profile to another group destroys and re-creates the grant, and a coarse grant
would not have been a cheap starting point to refine. The entity is the **root domain unit**, the
only one this design has; `include_child_domain_units` is `false`, describing today's shape rather
than restricting anything.

**Status: declared, not yet applied.** `terraform-live/data-governance/governance/grants.tf` was
written 2026-08-22 and `terraform validate` passes against the pinned providers
(`awscc_datazone_policy_grant`, awscc 1.98.0); the apply and the portal re-read are step 2.4's.

The account pinning is D21's boundary as a property of the *project* rather than of the URL a person
opened, and the two names are the `US-4` contract. The reasoning lives with the code
(`terraform-live/data-governance/governance/locals.tf`); this section is the index.

## Blueprints — the object

An **environment blueprint** is a provisioning template owned by AWS. It works in two steps:

1. **Enabling it in an associated account** (Stage 6 step 1.4) registers the template in that
   member account, naming the provisioning role, the manage-access role and the VPC parameters it
   may use. Enabling by itself creates no billed resource.

   **Two things about that resource were measured on 2026-08-21 and neither was what the plan
   assumed.** *(a)* **The API takes a `domainIdentifier` and no account parameter**, so
   `PutEnvironmentBlueprintConfiguration` configures the **caller's** account — which is why
   enabling blueprints is something an *associated* account does against a *shared* domain
   (the share's RAM permission is what lets it — `…DatazoneDomainExtendedServiceAccess`, measured
   2026-08-21; §RAM), and why the resources live in each member's
   `sagemaker/` slice rather than in `data-governance/governance/`. *(b)* **The resource this
   project uses is `awscc_datazone_environment_blueprint_configuration`, not the `aws` provider's**,
   because only the `awscc` one carries **`environment_role_permission_boundary`** — the field that
   makes DataZone attach the D13 boundary **while it creates a project role**, instead of the
   boundary being attached afterwards and racing reconciliation. That is INT-15's mechanism, and it
   is Lesson 8 (check `awscc` before declaring a Terraform gap) paying off rather than a workaround.
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

### Blueprint Categories

The three are the user's decision of 2026-08-19; **`undefined` is not a fourth choice but the absence
of one**, and it exists because the 2026-08-21 roster reading found thirteen blueprints no decision
covers. Mechanically, *every* blueprint requires a Terraform apply to exist — what distinguishes the
categories is what must happen **before** that apply:

| Category | Meaning | To enable |
|---|---|---|
| **1 — enabled by default** | in the step 1.4 map from the stage's first apply | nothing — born with the stage |
| **2 — on demand** | already authorized, with a **named trigger**; outside the map until it fires | commit + apply when the trigger fires — and the price measured at that moment if the row below lacks one (Lesson 6) |
| **3 — disabled** | outside the decision | an **amendment to Stage 6 decision 5**: price measured first, recorded in the stage log, then commit + apply. The *never* subset requires reopening an earlier decision instead |
| **`undefined`** | **nothing has been weighed** — the blueprint was never seen by the plan, or the decision that would have covered it named an object with no API identifier | decide its category first. **`US-3` fails on an `undefined` exactly as it fails on a category-3**, which is the point: a red battery that is merely uncategorised is indistinguishable from one that caught something |

The `US-3` allow-list in [`aws/studio.py`](../aws/studio.py) holds **category 1**; a category-2
blueprint joins the constant in the same commit that adds it to the step 1.4 map, so the check and
the code never disagree (Lesson 14).

### Blueprints

**THE ROSTER IS MEASURED, AND THE HEADING THIS REPLACES SAID *"the eleven blueprints"*.** Read
2026-08-21 from the live domain `awsds-studio` — `datazone list-environment-blueprints --managed`
returns **23**, and the console's *Blueprints* page lists **13**. The two reconcile exactly, and the
way they reconcile is the reason this table is keyed on the **API name**:

- **`AmazonBedrockGenerativeAI` is a console GROUPING, not an API blueprint.** The console shows one
  entry — *"consists of multiple blueprints"* — and the API returns the **seven** `AmazonBedrock*`
  rows below. Terraform and `US-3` can only name the seven. Stage 6 decision 5 put the *grouping* in
  category 1, which is why all seven arrive here as `undefined`: the decision was taken about an
  object that has no API identifier, so it does not carry to any of them by itself.
- **`LakeHouseDatabase` (console) is `DataLake` (API)** — the pair the plan already carried (Lesson 32).
- **12 direct + 7 from the grouping = 19**, leaving **four the API returns and the console never
  offers**: `LakehouseAdmin`, `S3Bucket`, `S3TableCatalog`, `ToolingLite`. Their descriptions below
  come from `get-environment-blueprint`, the only place they are written down.

**Three names in the previous table did not exist**: `EMRServerless` → **`EmrServerless`**, `EMRonEC2`
→ **`EmrOnEc2`**, `Quicksight` → **`QuickSight`**. All three were read off documentation prose and
none resolves — Lesson 38, and the reason the column header says *API name* rather than *name*.

Billing **shape** is read from documentation; billing **numbers** only where `PRICING.md` measured
them. The per-blueprint resource lists were re-read 2026-08-19 (that pass caught `LakehouseCatalog`
being Redshift-backed, Stage 6 decision 4); there is no "ML experience" blueprint, and the per-project
SageMaker AI domain comes from **`Tooling`** — both corrections to D26's wording, 2026-08-16.

Alphabetical by API name, the order `list-environment-blueprints` returns sorted — so a future roster
can be diffed against this table directly.

| Blueprint (API name) | What it provisions | Billing shape | Trigger | Category |
|---|---|---|---|---|
| `AmazonBedrockChatAgent` | A configurable generative AI app with a conversational interface | **Per use** — token-billed on demand, no standing resource (`PRICING.md` §5) | — | **1** |
| `AmazonBedrockEvaluation` | LLM evaluation for text generation, classification, question answering and summarization | **Per use** — token-billed; evaluation jobs bill the models they call | — | **1** |
| `AmazonBedrockFlow` | A configurable generative AI workflow | **Per use** — token-billed | — | **1** |
| `AmazonBedrockFunction` | A reusable component for including dynamic information in model output | **Per use** — token-billed | — | **1** |
| `AmazonBedrockGuardrail` | A reusable component for implementing safeguards on model output | **Per use** — token-billed; guardrail evaluation is its own unit | — | **1** |
| `AmazonBedrockKnowledgeBase` | A reusable component for providing your own data to apps | **Per use** — token-billed **plus** whatever vector store it stands up; the storage half is **not measured** and is the one shape here that can bill while idle | a project concretely needs retrieval over its own data — and **the vector store priced first** (Lesson 6). It is the only Bedrock row that is not purely per use, which is why it left category 1 on 2026-08-21 while its six siblings stayed | **2** |
| `AmazonBedrockPrompt` | A reusable set of inputs that guide model output | **Per use** — token-billed | — | **1** |
| `DataLake` (console: `LakeHouseDatabase`) | Per project: **Glue databases, Lake Formation permissions, an Athena workgroup** — the catalog/SQL surface on the Glue + LF substrate Stage 5 built, the query path D13 depends on | **Per use**: Athena SQL **USD 5.00/TB scanned** (`PRICING.md` §5); Glue catalog negligible at lab scale. No standing resource | default — configured at step 1.4 | **1** |
| `EmrOnEc2` | EMR clusters on EC2 instances — Spark, Hive and other big-data workloads from a reusable CloudFormation template | **Standing in practice** — instance-hours + EMR uplift while the cluster exists; a forgotten cluster bills on. Not measured | amend the decision (unowned until 2026-08-19) | **3** |
| `EmrOnEks` | Amazon EMR on EKS resources, same workload family as `EmrOnEc2` | **Standing in practice** — an EKS cluster underneath, plus EMR uplift. Not measured | — | **3** |
| `EmrServerless` | An EMR Serverless application per project — the VPC-capable Spark runtime replacing the Athena-Spark default (open question 12), and **the only engine whose compute connection documents an LF fine-grained mode** (`project.spark.fineGrained`; the notebook Spark Connect path is full-table on every engine). Under `VpcOnly` it asks for **four** optional endpoints against Glue interactive sessions' one (≈USD 0.06/h across both Interactive accounts under Stage 3's single-AZ rule, while the `egress/` slices are up) | **Per use**: **USD 0.0526/vCPU-h + 0.0058/GB-h** (x86; ARM cheaper), billed only while a session runs (`PRICING.md` §5). Near-standing tail: a **started** interactive application keeps one 4 vCPU/16 GB kernel worker even with no *pre-initialized capacity* configured (`autoStop` 30 min idle; the 60-min kernel timeout is not configurable) | default — **Stage 6 decision 1, taken 2026-08-21 as KEEP-or-REMOVE**: enabled at 1.4, and removed if either of the two in-stage readings comes out against it | **1** |
| `LakehouseAdmin` | *"Creates a unified data source across all Lakehouse catalogs in the account and automatically ingests and catalogs all available data."* **Read this row before categorising it**: an automatic, account-wide ingest-and-catalog is the shape `docs/GOVERNANCE.md` exists to prevent, and the account it would run in holds a governed lake | Not documented. Whatever a standing crawl of everything costs, plus the catalog it writes | **step 2.4 has measured** what the environment provisions, under whose role, and what the D13 boundary actually stops — **or** a category-1 blueprint proves it depends on this one. Until then it is not registered, so no project can create it | **2** |
| `LakehouseCatalog` | A new catalog in the SageMaker Lakehouse **backed by S3 tables or Redshift Managed Storage** — *not* the Glue/Athena surface its name suggests (the 2026-08-19 re-read) | RMS storage + the Redshift query path — the same cost family D12 excluded. Not measured | amend **decision 4** (2026-08-19); the Glue/Athena form this project uses is `DataLake` | **3** |
| `MLExperiments` | An **MLflow tracking server** for the project (OnDemand blueprint) | **Standing** — the server bills per hour while up (no idle shutdown like the apps have) + storage; **not measured**. Known floor under `VpcOnly`: the `aws.sagemaker.us-west-2.mlflow` interface endpoint, +USD 0.010/h per account | experiment tracking concretely needed; **measure the tracking-server price first** (Lesson 6) | **2** |
| `MLflowApp` | *"Creates an MLflow App for SageMaker Unified Studio."* **The same capability as `MLExperiments`, arriving twice** — categorise the pair together, so enabling one does not quietly imply the other | Not measured. App-shaped rather than server-shaped, so probably per app-hour — **unread** | — | **2** |
| `PartnerApps` | An IAM role and a Connection giving access to third-party Partner AI Apps | **Standing/subscription** — partner licence + deployed infrastructure; varies by partner. Not measured | amend the decision | **3** |
| `QuickSight` | The QuickSight analytics/dashboard surface inside a project | **Subscription** — per author/month + per reader session. Not measured | amend the decision. **Also blocked in fact**: the console reads *"QuickSight account not set up"* (2026-08-21) | **3** |
| `RedshiftServerless` | A Redshift Serverless workgroup + namespace | **Per use** with a **per-query RPU minimum** + storage — a second, larger query bill on top of Athena's (`PRICING.md` §5) | **Never** — excluded by **D26/D12**; enabling means reopening those decisions, not amending this one. `US-3` fails if it appears, with its own message | **3** |
| `S3Bucket` | *"Create S3 bucket for SageMaker Unified Studio project."* Not offered by the console — read from `get-environment-blueprint` | Storage + requests. Not measured. **The governing question is not cost**: a bucket born here has an encryption key and a policy nobody in this project chose (`docs/GOVERNANCE.md` §Encryption) | — | **1** |
| `S3TableCatalog` | *"Create S3 table catalog for SageMaker Unified Studio project."* Not offered by the console. **Possibly what `LakehouseCatalog` expands into when its S3-tables form is picked** — the same one-console-entry-to-many-API-rows shape as the Bedrock grouping. **Hypothesis, not a reading** | S3 Tables storage + maintenance. Not measured | — | **1** |
| `Tooling` | The project's basic environment: the per-project **SageMaker AI domain**, project roles, security groups, Athena workgroups, the project S3 location — and the parameter surface Stage 6 step 1.5 locks (`sagemakerDomainNetworkType`, idle shutdown, `maxEbsVolumeSize`, TIP). Mandatory — nothing else provisions a working environment | Per **app-hour running** (`ml.t3.medium` JupyterLab/Code Editor at **USD 0.050/h**, `PRICING.md` §8) + EBS. An open app bills whether used or not — the step 8 idle shutdown is what converts "up" into "in use" | default — mandatory | **1** |
| `ToolingLite` | *"Create basic resources for SageMaker Unified Studio project."* Not offered by the console. **Measured at step 1.5 (2026-08-21): a BASE variant, not a capability** — bundled in a project profile, the service demands `deployment_mode = ON_CREATE` (*"ToolingLite environment blueprint configuration must have deployment mode ON_CREATE"*, DataZone 400), so it cannot ride a `Tooling` profile as an on-demand extra, and a second base would double-provision every new project | Not documented. Presumably the same app-hour shape as `Tooling` with fewer resources — **unread** | amending the decision | **3** |
| `Workflows` | A **provisioned MWAA (Airflow) environment** from a CloudFormation template — billed hourly while it exists | **Standing**: MWAA `mw1.micro` **≈ USD 211.70/month** left up (`PRICING.md` §1) — the shape D7 rejected for daily use | **D28's documented last-rung fallback**: enabled only if INT-14's chain falls through at Stage 10 (`awscc_mwaaserverless_workflow`, then the CFN wrapper, then this) — and then as `[E]`, torn down between uses. The *serverless* Workflows surface is separate: Stage 10 verification (i) finds what enables it | **2** |

**ALL 23 ROWS CARRY A CATEGORY (user, 2026-08-21)** — settled against the measured roster rather than
against the console grouping decision 5 had addressed; closed at 12/5/6 and **re-cut to 11/5/7 the
same day**, when step 1.5's refusal measured `ToolingLite` as a second BASE (its row above).
**Category 1 is eleven**: `Tooling`, `DataLake`, `S3Bucket`, `S3TableCatalog`, `EmrServerless` and
six of the seven `AmazonBedrock*`. Category 2 is five, category 3 is seven, and **no row is
`undefined`** — which is what step 1.4 needed, because `US-3` fails on an uncategorised blueprint
exactly as it fails on a forbidden one.

**Three placements carry a consequence worth holding rather than rediscovering.**

**`AmazonBedrockKnowledgeBase` is in category 2 and its six siblings are in category 1** — the Bedrock
family is deliberately **not uniform**, so nothing downstream may reason about "the Bedrock blueprints"
as one thing. The reason is billing shape: the other six are purely token-billed, while a knowledge
base stands up a **vector store that bills while it exists**. That is the standing shape D12's silent
budget is worst at catching, and it is unmeasured — hence a category-2 trigger that names the
measurement (Lesson 6) instead of a category-1 default that would meet the bill first.

**`S3Bucket` and `S3TableCatalog` create storage this project did not author.** The governing question
is not their cost but their **encryption key and bucket policy**, which come from the blueprint rather
than from `docs/GOVERNANCE.md` §Encryption's per-account CMK rule. Stage 6 step 2.4's throwaway project
is where those fields get read (Lesson 16); verification (xviii) is the receiving end. **`ToolingLite`
moved 1 → 3 by measurement (step 1.5, 2026-08-21), and the trap its category-1 placement guarded
against does not exist in that form**: the service does not select the lighter variant on its own —
it refuses a profile that bundles it `ON_DEMAND`, which makes it a second BASE, present only by
explicit choice. A base beside `Tooling` would double-provision every new project with an unmeasured
shape, so it is disabled; if it ever returns, it returns as its own project profile, never as an
extra on these two.

**`LakehouseAdmin` is category 2, and the move is the clearest case in this table of what the
categories are *for*.**

> **It was placed in category 1 and moved on the same day, before anything was applied.** The
> category-1 row carried a note — *read it at step 2.4's throwaway project before a real project uses
> it* — and a note is an **intention, not a control** (Lesson 5): nothing executes it, and the
> capability exists from the apply regardless. In category 2 that same sentence becomes the **trigger**,
> which is the condition of enabling. The measurement stops being advice and starts being a gate.
> **The asymmetry is what makes it cheap**: nothing in `objectives.md` asks for this blueprint, no stage
> consumes it, and it was not known to exist before 2026-08-21 — so category 2 costs nothing anyone has
> named, while category 1 buys availability nobody requested. §Blueprints — the object already says it:
> *"Enabling is cheap to do later … disabling after environments were provisioned from it is not
> symmetrical. Start minimal."*
> **The counter-argument, recorded because it is not settled**: if *"a unified data source across all
> Lakehouse catalogs"* turns out to be how a project sees the shared catalog at all, this belongs in
> category 1 and its absence would break the point of the stage. That looks unlikely — `DataLake`
> provisions the per-project catalog surface and Stage 5 already established the lake path through
> resource links and Athena — but it is unread. Category 2 handles that uncertainty better than
> category 1 does: if step 2.4 finds a dependency, it moves up **with evidence**, before any real
> project exists. The failure mode of being wrong this way is a loud apply error; the other way it is an
> unmeasured account-wide ingest sitting one click from a project member.

> **And it is NOT Lake Formation's *data lake administrator*, which is what makes the name a trap.** The AWS portal text consulted on 2026-08-21 describes that other object — a privileged IAM
> principal designated under *Administration → Data lake administrators*, which this project already
> owns and already assigned (Stage 5 pass 4, `DL-6`, and `docs/ORGANIZATION.md` names who). **This
> blueprint's own description, from `get-environment-blueprint`, is a provisioning template**:
> *"Creates a unified data source across all Lakehouse catalogs in the account and **automatically
> ingests and catalogs all available data**."* The two share a word and nothing else, and reading one
> as the other is Lesson 38's shape in reverse — a real name attached to the wrong object.
>
> **What the risk actually is, stated so the trigger can retire it.** Enabling a blueprint provisions
> nothing — it *registers* a template, and the ingest happens only if a project creates an environment
> from it. So the concern was never the apply; it was that a category-1 placement puts an account-wide
> automatic ingest **one click from a project member**, in an account holding a governed lake. Whether
> the D13 boundary `awsds-<env>-project-boundary` and Lake Formation's own permissions stop that ingest
> reaching registered locations is **unmeasured** — squarely INT-15 and Stage 6 verification (v)'s
> question, what a service-authored role can do that this project did not grant. Note that the
> boundary's S3 deny names the **LF-registered** buckets, so it says nothing about the derived zone,
> which is where a project's outputs live.

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
in for a profile pinned to a member account, who creates it (domain setup or the Tooling
provisioning), **and the bucket's default encryption key** — which decides whether it sits inside
`docs/GOVERNANCE.md` §Encryption's per-account data CMK rule or outside every key this project chose —
are read at Stage 6 step 2.4's throwaway project (Lesson 16: record every field). **Stage 6's
verification (xviii) is the receiving end**, so the field list exists at both ends and not only here.

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

Three things in a member account all answer to "working storage" — **two buckets and a workgroup**, and
the third row read as a bucket until 2026-08-20, which is the error that made the destination question
below easy to miss:

| Object | Created by | Holds |
|---|---|---|
| the project path (`amazon-datazone-…`), a **bucket** | the service (2.4's reading settles by which hand) | `shared/` files, the blueprint workgroup's Athena output, workflow temp, the consumer Glue database location |
| `awsds-<env>-derived`, a **bucket** | `consumer-data` (Stage 5 pass 4a) | the persona's derived zone — per-user write, persona-grain read, the `scratch/` prefix |
| `awsds-<env>-athena`, **a workgroup, not a bucket** | `consumer-data` (Stage 5 pass 4a) | nothing of its own. The module creates exactly **one** bucket (`buckets.tf`); this is the *enforced* workgroup (`athena.tf`), and its results are forced into `s3://awsds-<env>-derived/results/` under a 10 GiB cap. **So the enforced results already live inside the derived zone** — they are not a third place |

The last row is a boundary worth stating: pass 4c scoped the persona's Athena run family to the two
*enforced* workgroup ARNs, and a blueprint-provisioned project workgroup is a third workgroup
outside that scope — exercised by project roles, not by the persona. **And the first row is where its
output lands**, which is the fact Stage 6's decision 6 must point at rather than assume: a project
workgroup writes into the *project path*, not into `awsds-<env>-derived`, unless Stage 6 step 2.4/2.6
measures that the location can be repointed and enforced. Record that answer **here** when it returns. Whether the two query paths
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
- **The `s3` entry in that list is the one to verify rather than provision on faith, and Stage 5 pass
  4d is why.** Each account already carries a `[P]` **gateway** endpoint for S3, whose prefix-list
  route is more specific than any default — so where that route is on an app subnet's route table,
  S3 traffic takes the **gateway**, and the request arrives carrying the **gateway's**
  `aws:SourceVpce`, not the interface endpoint's. Stage 5 measured exactly this on the VPN home and
  it cost a working control: a network condition written for one endpoint id silently failed to
  match traffic that took the other (Lesson 33). **What Stage 6 step 4.2 owes, therefore, is a
  measurement and not an assumption** — for each project subnet, which S3 route wins, and which
  endpoint id the resulting call presents in CloudTrail. Every `aws:SourceVpce` list the SMUS
  projects must satisfy (the lake's `trusted_vpce_ids`, the derived buckets') is written against
  that answer, and the failure mode if it is guessed is the 4d one: an `AccessDenied` on a path
  everybody believes is allowed.

**How it is enforced, not just chosen:** `VpcOnly` is already the blueprint **default** (read
2026-08-16). Stage 6 step 1.5 sets `sagemakerDomainNetworkType = VpcOnly` in both project profiles
and marks the parameter **non-Editable** — the *Editable* flag is what turns a default into a
control (Lesson 5): the parameter exists so nobody can flip a project to `PublicInternetOnly`.

### Custom images (BYOI) — and how they are named

A project's spaces run the **SageMaker Distribution** unless a custom image is attached to the
SageMaker AI domain `Tooling` provisions in the member account: an image, an image version and an app
image config, then the domain's `CustomImages` (Stage 6 step 5.1; INT-01/INT-17 are the open ends and
verification (vi) is where the working mechanism gets recorded).

**What such an image must satisfy** — the `public.ecr.aws/sagemaker/sagemaker-distribution` ancestor at
≥ `2.6-cpu`, **no `ENTRYPOINT`**, AWS's three owned paths, the EBS mount at `/home/sagemaker-user`, the
activity-monitor extension idle shutdown reads — is [`images/README.md`](../images/README.md)'s and
Stage 6 step 5.0's, and is deliberately **not repeated here**. What this section owns is the
**naming**, because naming is the part that outlives the hand build: Stage 8 step 1's pipeline inherits
whatever convention the first push wrote, and both repositories are **tag-immutable**, so a tag is
spent the first time it lands.

#### The repository is the name — the tag is everything else

```
<account-id>.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-dev-env:default-v0.1.0
└──────────────── registry ─────────────────┘└──── repository ────┘└──── tag ────┘
```

**Both repositories live in the Production account, and the `prod` in their names is where the
*registry* is, not who the image serves** — `terraform-live/production/registry/ecr.tf` builds them as
`awsds-${var.env}-ecr-*` with `env = prod`, and Sandbox and Development reach them by
`AllowConsumerAccountsToPull`. Reading the pair as "one for production, one for development" inverts
D17: there is **one** ancestor for every environment, and what gets promoted is the code, never a
per-environment image.

| Repository | What it is | Who pulls it |
|---|---|---|
| `awsds-prod-ecr-base` | the **common ancestor** (D17) — every application image is `FROM base`, `dev-env` included | Stage 8's pipeline; the consumer accounts carry the pull grant on purpose, so a project building its own image does not read a missing grant as a network fault |
| `awsds-prod-ecr-dev-env` | the **SMUS custom image (BYOI)** — the runtime a space actually starts | the member accounts, through `CustomImages` |

So the repository already answers *what the image is*. Putting that word back inside the tag —
`awsds-prod-ecr-dev-env:dev-env-…` — spends it twice in every pipeline line that ever references it.

#### The rule

**`<flavour>-v<major>.<minor>.<patch>`, and the same number in both repositories.**

The **flavour** is the axis this estate will actually branch on, decided by the user on 2026-08-22
while choosing the first tag: a project wanting **GPUs**, one wanting **Spark** libraries, and one
wanting neither are three different runtimes, and the plain one is named `default` rather than left
implicit. **The flavour axis reaches `base` too, and that is the half that is easy to miss** — a GPU
`dev-env` descends from `sagemaker-distribution:<version>-gpu`, a different digest and therefore a
different ancestor, so the branch happens at `base` first. If only `dev-env` carried the flavour, the
day a GPU base arrives `base:v0.1.0` silently starts meaning *the CPU one*.

**Why flavour first and version second**, when the ancestor itself writes `4.3.0-cpu` the other way
round: a lifecycle policy is the first thing that will ever select a subset of these tags, and *"keep
the last 3 GPU images"* is a rule worth having separately from the CPU ones, because a GPU image costs
several times the storage. ECR's simple selector, `tagPrefixList`, matches a **prefix** only, so
flavour-first is selectable with it and groups the flavours together in any listing.
**Stated honestly, this is convenience and not capability** (read 2026-08-22): the other selector,
`tagPatternList`, takes up to four `*` wildcards per string, would match `*-gpu` just as well, and is
the one AWS calls best practice. Two things to know before writing that first policy either way — the
two selectors are **mutually exclusive** within a rule, and *"if you specify multiple tags, only the
images with all specified tags are selected"*, which is an **AND** where a list reads like an OR.

**Why one number across both repositories.** `dev-env` is `FROM base`, so a change to `base` rebuilds
`dev-env` from its first layer — Julia, R and Rust download again. The two therefore never move alone,
and a shared number says so; **Stage 7 step 2.6**, which fills the CA-install layer with the internal
PKI root, is the first scheduled bump and takes both to `default-v0.2.0`.

**When a flavour graduates from a tag to its own repository.** The trigger is not size or taste, it is
reaching for a knob that exists **per repository and not per tag**: a different set of accounts allowed
to pull (the repository policy), a different retention (the lifecycle policy), a different scan
configuration, or a different KMS key. Until one of those differs, a flavour is a tag — reversible, and
one `module "ecr_…"` block cheaper.

**And the tag is not the identity — the digest is.** A tag is a movable pointer everywhere except here,
where `IMMUTABLE` freezes it on first landing; what Stage 6 step 5.1 registers as an image version and
what Stage 7 step 2.6 must be able to say it replaced is the **digest**, which is why both are recorded
in the stage log at push time. The image cannot be asked either: `dev-env`'s own
`/opt/awsds-runtimes.txt` records the **build-time** reference (`awsds/base:local`), not the ECR tag it
was later given.

**First applied 2026-08-22, Stage 6 step 5.0:** `default-v0.1.0` in both repositories.
