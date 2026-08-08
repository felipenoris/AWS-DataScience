# AWS-DataScience

Blueprint for using AWS as a Data Science infrastructure provider.

- `CLAUDE.md` — goals and working rules.
- `GENERAL_PLAN.md` — the **plan core**: guiding principles, the account map, and the two indexes
  (stages and decisions). Read this first; it points at everything else.
- `plan/` — the plan itself, split so that a task reads only what it needs:
  - `plan/stages/` — one file per stage, each declaring the decisions it **consumes**.
  - `plan/decisions/` — one file per decision `D1`…`D31`, plus a one-line-per-decision `INDEX.md`.
  - `plan/architecture.md`, `plan/conventions.md`, `plan/integrations.md` (the `INT-nn` rows),
    `plan/cost-model.md`, `plan/open-questions.md`, `plan/lessons.md`,
    `plan/institutional-delta.md`, `plan/history.md`.
- `GLOSSARY.md` — every acronym the plan uses, plus its notation and the IAM condition keys it quotes.
- `ACCOUNTS_AND_USERS.md` — AWS accounts, the axis each sits on, and the SSO users.
- `PRICING.md` — per-unit AWS rates for `sa-east-1` and `us-west-2`, read from the AWS Price List bulk API.
  Unlike the cost figures in `plan/cost-model.md`, which are order-of-magnitude estimates, these are
  measured; the cost model says what is consumed, `PRICING.md` says what a unit of it costs.
- `LOG.md` — record of every step performed manually through the console.
- `REFERENCES.md` — external references used along the way.

---

## Account segregation

The environment is split across AWS accounts under a single AWS Organization. The cheaper alternative —
one account, with environments separated by tags, bucket prefixes and IAM policies — is simpler to build and
simpler to operate, so the split has to earn itself. It does, and the reasons below are specific to a data
science environment rather than generic "dev and prod should be separate" advice. The following sections
record which parts of the layout come from AWS's own reference architectures, which are this project's own
compromises, and the three distinctions the layout is built on.

### 1. The account is the only hard boundary AWS offers

Everything else in this section is a consequence of this one fact:

- **SCPs and RCPs attach to an OU or to an account.** There is no such thing as a Service Control Policy that
  applies to "resources tagged `Environment=production`". If a preventive control is going to be structural,
  the thing it applies to has to be an account.
- **Service quotas are per account and per region.**
- **IAM inside a single account is a soft boundary.** It is one `terraform apply` from being widened, and it
  is under permanent pressure from ordinary work — "just add `s3:*` to my role so I can finish this" is a
  reasonable request that is very hard to refuse forever.
- **Billing, Budgets and Cost Anomaly Detection** are naturally per account, so cost attribution and cost
  containment come for free with the split and have to be reconstructed with tags without it.

### 2. A notebook is unreviewed code holding a production-grade credential

This is the argument that carries the most weight here, and it has no equivalent in a conventional
application environment.

The SageMaker execution role runs code a person wrote seconds ago: unreviewed, untested, and quite possibly
pasted from a search result. Whatever that role can reach is reachable by that code. The same applies to every
package the notebook installs — a typosquatted PyPI name is enough, and it executes with the same credential.

In a conventional environment, code reaches production through review, CI and a deploy. In a data science
environment the *whole point* is that people can run something immediately, without any of that. Both
properties cannot hold in the same account: either the credential is trusted, or arbitrary code can assume it.

So the boundary being drawn is not "development code versus production code". It is **unreviewed compute
versus the production data plane** — and an account boundary is the only thing that holds it.

### 3. The Sandbox is the higher-risk account, not the lower-risk one

Counterintuitive, and load-bearing. The instinct is that the sandbox is the toy and production is what
deserves protection. In a data science environment it is the other way around:

- the **Sandbox** is where real data (read from Production) meets unreviewed code, interactively, with a
  browser session attached to it;
- **Production** runs only artifacts that passed a gate: a container image built by a runner, a model version
  approved in the registry, Terraform reviewed in a merge request.

The consequence shapes several stages of the plan: the data perimeter, the egress controls and the
fine-grained access model are built for the Sandbox first, not retrofitted to it later. Treating the Sandbox
as "the place where controls are relaxed because it is only a lab" inverts the threat model.

### 4. Blast radius of cost and quota

Not a security argument, and often the one that convinces people who are unmoved by the others.

A runaway training job, a GPU instance left running overnight and a Spark job scanning the entire lake are all
*normal accidents* of exploratory work — they are what exploration looks like when it goes wrong, not
misconduct. In a shared account they consume the same SageMaker instance quotas, the same NAT throughput and
the same budget as the production workload. With separate accounts, an experiment can only exhaust the
experimenter's own environment.

### 5. The split is what makes "Production is only changed by Terraform" enforceable

With a single account, "nobody changes production by hand" is a convention enforced by IAM policies that the
same people can influence. With separate accounts, the human permission sets assigned to Production simply do
not contain the control plane, and an SCP on the `Workloads` OU denies what is left. The same sentence stops
being a promise and becomes a control.

### 6. Where the boundary actually runs

Two refinements, both easy to state wrongly:

- **The boundary is the control plane, not the account.** Humans do use services hosted in Production —
  GitLab over the VPN, and read access to production data — but nobody changes Production *infrastructure*
  by hand.
- **Interactive compute lives only in the Interactive OU.** Since the ninth plan revision (D26), the
  interactive surface is **SageMaker Unified Studio**: one DataZone V2 domain, *registered* in the Data
  Governance account because a domain is a registry of projects and data products rather than a runtime,
  and whose project blueprints *provision compute* into Sandbox (`experimentation` profile) and Development
  (`engineering` profile) — and nowhere else, enforced by a Service Control Policy on the `Workloads` OU
  rather than left as an intention. Where the domain is registered and where code runs are two different
  questions, and only the second is an account-boundary question. SageMaker's *runtime*
  APIs — training and processing jobs, Model Registry, endpoints — do exist in Staging and
  Production, because that is where models are tested, retrained and served; the difference is that only a
  pipeline submits to them. A domain or an account association in a deployment target would put unreviewed
  code back inside the account boundary, which is precisely what the split exists to prevent — what
  crosses instead is a fixed artifact set (container image, workflow definition, per-workflow IAM role,
  orchestration resource, log group, model package group — D28), carried by git and created by the
  pipeline.

### 7. What crosses the boundary

Artifacts cross in one direction only, through the pipeline, and they pass through Staging on the way:

- container images (ECR),
- model versions (SageMaker Model Registry),
- workflow definitions and application code (a Git tag),
- the Terraform that instantiates them.

The chain is **Development → Staging → Production**. Staging receives the built artifact, runs the
integration tests against a sampled or synthetic dataset, and is torn down again; only then does the
**Deployment Manager**'s approval release the same artifact to Production. A failure in Staging stops the
chain, and Production is
never touched. Sandbox sits *before* the chain, not at its head: experimentation graduates into a
Development repository through git — a rewrite and a review, not an automated lift — and only what lands in
such a repository can be promoted.

Data crosses in the other direction: the governed lake lives in the Data Governance account, and its catalog
is shared read-only to Sandbox and Development through Lake Formation, so that all interactive work happens
against real data without making a copy of it. Production's job role holds the same share plus the *governed
write* — production ETL is the lake's producer. Staging is not part of any share — it never holds governed
data, for the reason given in the next section.

**And the two directions have two different approvers, deliberately.** The Deployment Manager approves
what *moves along the chain*; the **Governance Manager** approves who may *read the data* — subscriptions
in the SageMaker Catalog, LF-Tags, the classification scheme. Neither can do the other's job. With a
single approver, one person could write a job that reads restricted data, approve its release into
Production, and approve that job's access to the dataset: three acts, one signature. The split is what
makes the two arrows above independent of each other.

Anything that crosses outside this list — a shared S3 bucket used to hand files between accounts, for
instance — is a promotion path that bypasses the approval gate, and is therefore not built.

### 8. What the split costs

The split is not free, and the plan accepts the cost deliberately rather than pretending it away:

- one AWS Config recorder per governed account — every account except Management, so this cost grows with
  the account count;
- a duplicated network layer per account — interface VPC endpoints are the largest hourly line item in this
  project, and they exist on every side of the boundary;
- cross-account integrations that each have to be *proven* rather than assumed: Studio pulling a custom image
  from another account's ECR, CodeArtifact and KMS resource policies, Lake Formation sharing through AWS RAM,
  the model registry, and S3 bucket policies whose VPC endpoint conditions must admit a peer account's
  endpoint.

For a personal lab under a USD 50/month ceiling this is a real expense. It is also the part most worth
learning: any institution running this architecture pays exactly the same cost.

---

## What the AWS references recommend

The account layout above is not invented here. AWS publishes several multi-account reference architectures
for SageMaker, and they agree on more than they differ on. This section summarises what each one says, then
records what this project takes from them and — just as important — where it knowingly departs.

### 1. `aws-samples/amazon-sagemaker-secure-mlops`

<https://github.com/aws-samples/amazon-sagemaker-secure-mlops>

A deployable sample rather than a diagram, and the closest of the three to what this project is building: a
secure, VPC-only SageMaker environment with no internet access by default. Its core is a **three-account
group**:

- **Development** — hosts the SageMaker Studio domain used by data scientists and ML engineers, along with
  the S3 buckets, code repositories and CI/CD pipelines. Models are built, trained, validated and registered
  here.
- **Staging** — a *deployment target*. It receives validated and approved models from development and runs
  automated unit and integration tests against them. **Data scientists have read-only access.**
- **Production** — the final destination for tested models; online and batch inference.

The sentence that settles the question this project kept asking: **only the development account runs
SageMaker Studio.** Staging and Production function exclusively as deployment targets, with no Studio domain
of their own. The sample also notes one Studio domain per region per account, and a dedicated data-science
team account. Shared-services and data-governance account groups are offered as optional additions for
larger setups.

### 2. MLOps foundation roadmap for enterprises with Amazon SageMaker

<https://aws.amazon.com/blogs/machine-learning/mlops-foundation-roadmap-for-enterprises-with-amazon-sagemaker/>

A maturity roadmap rather than a fixed topology — the account set grows in phases as an organization's MLOps
practice matures, which makes it the most useful of the three for understanding *why* each account exists
rather than merely that it does. The accounts it names:

- **Data lake** — ingested data and the ETL pipelines that produce it. Separate from where people work.
- **Experimentation** — where data scientists research and collaborate in Studio notebooks.
- **Development** — the first production-grade stage, holding the ML pipelines; Studio moves here once the
  Studio UI is being used for MLOps rather than for exploration.
- **Tooling (or automation)** — code repositories, CI/CD pipelines, **the SageMaker Model Registry** and
  Amazon ECR.
- **Pre-production** and **Production** — introduced in the later, "reliable" phase.

The structurally important claim, and the one this project acts on: the Model Registry and the container
registry live in the **tooling** account — on the automation side of the boundary, not in the account where
data scientists have broad permissions. Whoever controls the registry controls what reaches production, so
it must not be modifiable by the people the approval gate is meant to gate.

### 3. MLOps Workload Orchestrator — architecture overview

<https://docs.aws.amazon.com/solutions/latest/mlops-workload-orchestrator/architecture-overview.html>

An AWS Solution shipped as CloudFormation, offering a single-account template and a multi-account one. Its
contribution to this project is mechanical rather than conceptual: the multi-account deployment is organized
by **AWS Organizations organizational unit IDs and account numbers** for development, staging and production.

That is the concrete confirmation that environments are expected to be expressed as **OUs**, not as tags or
naming conventions — which matters because Service Control Policies and Resource Control Policies attach to
an OU and to nothing else. It is the mechanical reason this project has a `Workloads` OU rather than an
`Environment=production` tag.

### What this project takes, and where it departs

| The references recommend | This project | Verdict |
|---|---|---|
| Studio only in the development / data-science accounts | The interactive surface only in the **Interactive OU** — since D26, one SageMaker unified domain (DataZone V2) registered in **Data Governance**, whose project blueprints provision compute into Sandbox and Development and nowhere else (D17, D21, D26) — enforced by two SCPs (Stage 1b step 7): the `Workloads` OU denies `sagemaker:CreateDomain`, `CreateUserProfile`, `CreatePresignedDomainUrl` **and `datazone:*` in full**, so a deployment target can neither host a domain nor associate itself to one; and the organization root denies `datazone:CreateDomain` everywhere except the `Data` OU, so "one domain, and it lives in Data Governance" is a control rather than a convention | **Adopted**, and made preventive rather than conventional |
| A staging / pre-production deployment target between development and production | The **Staging** account (D20) | **Adopted.** It was missing until 2026-08-08; the plan had tried to stand in for it with a Glue namespace inside Production, which shared an account and a blast radius with the thing it was meant to de-risk |
| Data scientists get read-only access in staging | `DataScientistStagingAccess` — read, no write of any kind (D18) | **Adopted verbatim.** A staging environment a person can write to stops being evidence of what the pipeline does |
| Environments expressed as Organizations OUs | Four OUs named for their policy sets (D23): `Workloads` holds Staging and Production, `Interactive` holds Sandbox and Development, `Data` holds Data Governance, `Security` holds the rest | **Adopted.** One SCP set per policy set, written once and inherited — an OU holding a single account forever would be a folder with one file |
| Model Registry and ECR in a Tooling / shared-services account | Both in the **Production** account (D14) | **Departure**, the main one remaining. No separate tooling account, on cost. The consequence is stated rather than hidden: there is no boundary between what builds and what runs, so a compromise of GitLab is a compromise of Production |
| A separate data lake / data management account | The **Data Governance** account (D22): the lake, its catalog, Lake Formation and the classification scheme, reached from every environment through cross-account shares | **Adopted** on 2026-08-08. It had been a departure; the section below on Data Governance vs. Production records why it stopped being one |
| Experimentation and development as distinct accounts | **Sandbox** (experimentation — the unit of work is a notebook) and **Development** (the unit of work is a pipeline), both in the Interactive OU (D21) | **Adopted** on 2026-08-08. It had been collapsed "because there is one user"; the section below on Development vs. Experimentation records what the boundary buys anyway |
| Staging holds data representative of production | Staging holds **sampled or synthetic data only**, never a copy of production | **Deliberate departure.** Staging is a deployment target where data scientists have read access and unattended tests run, so a full copy would make the less-defended of the two accounts the cheapest route to production data. The accepted cost: a test suite that catches permission, schema and wiring errors and misses whatever only appears at production distribution and volume |

### Why the shape is what it is

Three motivations underlie all of the above, and they are worth stating separately from the sources:

- **Studio is an IDE, not a runtime.** What runs in production is a container, a training job or an
  endpoint — never a notebook. A deployment target therefore has no reason to host a Studio domain, and one
  strong reason not to: a domain is an interactive entry point for unreviewed code into an account whose
  entire value is that only reviewed artifacts run there.
- **A promotion crosses an account boundary, and the errors it produces are permission errors as often as
  logic errors.** Only a real second account exercises that crossing. Anything inside the target account —
  a namespace, a prefix, a tag — is evaluated against the target's own IAM and will pass for the wrong
  reason.
- **Read-only in staging keeps staging honest.** The moment a person can adjust staging by hand to make a
  test pass, the test stops being evidence about the pipeline and becomes evidence about the person.

---

## Three distinctions the layout is built on

Three questions came up while adopting the reference architectures, and their answers explain most of the
account map. They are recorded here because each one looks like a nuance and is actually a load-bearing
design decision.

### Development vs. Experimentation

The difference is not code maturity — it is the **unit of work**, and everything else follows from it.

| | Experimentation (Sandbox) | Development |
|---|---|---|
| Unit of work | The notebook | The pipeline — a repository with tests, a SageMaker Pipeline |
| Expectation | Nothing survives | "Run it again on Tuesday and get the same answer" |
| Versioning | None, or informal | Git, CI, tagged artifacts |
| Cost profile | Spasmodic, human-driven (the GPU left on overnight) | Automated and predictable |
| Feeds into | Development, by graduation | Staging, by promotion |

In AWS's MLOps roadmap this is a *phase*, not just an account: an organization starts with experimentation
only, and the development account appears when the MLOps practice matures enough to have pipelines worth
engineering. In a large organization it is also a **people boundary** — data scientists on one side,
ML engineers on the other, so that neither inherits the other's mess.

This project has one user, so the people boundary is empty here — and the accounts are still separate,
because the boundary buys three things that do not depend on headcount: the promotion chain gets an honest
origin (what enters CI is already repository-shaped — the pipeline never has to pretend a notebook is an
artifact); the graduation step becomes **visible** (moving work from Sandbox to Development is a deliberate
git commit and a rewrite, not a gradual blurring inside one account — and the rewrite *is* the quality
gate); and cost attribution separates exploration from engineering. There is deliberately no automated path
that lifts a notebook out of Sandbox.

### OU vs. Account

Segregating "by OU" versus "by account" is a false choice — they are different layers of the same tree, and
you always have both. The useful formulation:

> **The account is the isolation boundary. The OU is the policy boundary.**

Accounts isolate: blast radius, service quotas, billing, credentials. OUs do exactly one thing accounts
cannot: they let a policy be written once and *inherited*, instead of remembered. SCPs and RCPs attach to
an OU or an account, never to a tag — and a guardrail attached account-by-account is a guardrail that
silently does not exist on the account someone forgot. Control Tower's controls and AWS's own multi-account
tooling (the MLOps Workload Orchestrator among them) operate on OUs for the same reason.

The corollary: **an OU earns its existence when two or more accounts need the same policy set.** An OU
holding one account forever is a folder with one file. So this project's OUs are named for their policy,
not for an environment — with one deliberate exception at the bottom of the table, whose value is not the
policy it carries but the disposable account it contains:

| OU | Accounts | The policy set it carries |
|---|---|---|
| Security | Log Archive, Audit, Identity | Control Tower guardrails; delegated administration |
| Interactive | Sandbox, Development | Interactive compute **allowed**; human infrastructure changes denied |
| Data | Data Governance | No *user* compute (the DataZone control plane and the catalog-maintenance role are carved out by name); deletion denied |
| Workloads | Staging, Production | No interactive compute; no human control plane |
| Policy Test | Policy Canary | **None** — this is the OU a *candidate* policy is attached to and exercised against, before it reaches anything real (D29) |

A per-environment OU tree (`Development` OU, `Staging` OU, `Production` OU, one account each) was
considered and rejected — every OU would hold exactly one account, so the tree would add names without
adding inheritance. The revision triggers are recorded in the plan (D23): a second production-like account
nests `Workloads` into `NonProd`/`Prod`; a second data domain does the same for `Data`.

**Why `Policy Test` is not that mistake, despite holding one account.** It is the one OU here whose value is
not inheritance at all. A Service Control Policy is a permission ceiling that AWS evaluates only when a
principal makes a call, so a candidate policy attached to an empty OU proves nothing beyond "the JSON
parsed" — the OU is worth having precisely *because* there is a disposable account inside it to make the
call. `Data`, by contrast, holds one account and would still be an OU if it held three; `Policy Test` would
stop making sense the day its account became something worth keeping. Different reasons, same shape, and
the plan's own test ("two or more accounts needing the same policy set") is the wrong one to apply here.

### Data Governance vs. Production

The Data Governance account is not "more production than production". The two sit on **different axes**:

- **Environment** (dev / staging / prod) is the *lifecycle* axis — how mature and how protected this
  instance of the **compute** is: the ETL job, the model, the endpoint.
- **Data ownership** is the other axis — who produces a dataset, answers for its quality, and sets its
  access policy. The lake is **state**, and it outlives every application that reads it.

Concretely, four things go wrong when the lake lives inside an environment account:

1. **Lifecycle mismatch.** Applications are deployed, rolled back, rebuilt; a lake is none of those. Tying
   the data's life to a deployable environment means the data is in the way every time the environment
   changes.
2. **Producer/consumer collapse.** If the team that runs the model shares an account with the data it
   reads, account-level access exists by default and Lake Formation grants become decoration. In a
   dedicated account, the cross-account share is the *only* path, so every access is an explicit grant —
   the same argument as the plan's D13, one level up.
3. **Many-to-many.** One environment holds many data domains; one domain serves many environments. Any
   layout that nests data inside an environment forces a copy per environment — which is how organizations
   end up with fourteen copies of the customer table.
4. **Different protection profile.** A data account wants Object Lock, long retention and deletion denied;
   an application account wants to be rebuildable. One policy set cannot want both, which is why Data
   Governance has its own OU.

In this project the split also simplifies enforcement: the environment accounts do not even *contain* the
lake buckets, so "the execution role has no direct S3 access to governed data" stops being a carefully
maintained exclusion and becomes a fact of the topology. Production remains special in exactly one way: its
job execution role holds the share's **governed write** — production ETL is the lake's producer, and that
is the only path by which governed data is ever written.

---

## The accounts

All under one AWS Organization governed by Control Tower.

| Account | OU | Purpose |
|---|---|---|
| Management | root | Organization owner. Bootstrap only, manual, through the console. Never managed by Terraform. |
| Log Archive | Security | Central, tamper-evident log store (S3 Object Lock). Created by Control Tower. |
| Audit | Security | Security guardian: GuardDuty, Security Hub, Macie, IAM Access Analyzer. Created by Control Tower. |
| Identity | Security | Delegated administration of IAM Identity Center: permission sets, groups, assignments. Separate from Audit so that access management and security monitoring do not share a blast radius. |
| Policy Canary | Policy Test | Deliberately empty, and disposable: the account a candidate SCP or RCP is exercised against before it reaches anything real (D29). An SCP is only evaluated when a principal makes a call, so a policy staging OU with no account inside it tests nothing — which is why this is an account and not just a folder. Holds an administrator principal and nothing else, because a deny exercised by a principal that lacked the permission anyway proves nothing about a ceiling. |
| Sandbox | Interactive | **Experimentation** — the unit of work is a notebook. Target of the unified domain's `experimentation` project blueprints (D26): interactive compute, unreviewed code against real (shared) data — the highest-risk account, per §3 above. Nothing here survives; nothing promotes from here. |
| Development | Interactive | **Development** — the unit of work is a pipeline: a repository with tests, git, CI. Target of the `engineering` project profile (D26). Work graduates in from Sandbox through git, and the promotion chain starts here. |
| Data Governance | Data | The **state and governance of data**: the governed lake (S3 + Iceberg), the Glue catalog, Lake Formation, classification, the ingestion drop-box, the Glue Crawlers on raw and drop-box (D27), and the **SageMaker Unified Studio domain** with SageMaker Catalog, project profiles, blueprints and account associations (D26). A registry, not a runtime: no user compute, no VPC, no interactive sign-in — every environment reaches it through cross-account shares, and the portal it hosts is used by people who can never administer the account. Renamed from `Data Management` on 2026-08-08. |
| Staging | Workloads | Deployment target. Receives the built artifact, runs the integration tests against sampled or synthetic data local to it, and is torn down again. No Studio domain, no Model Registry of its own, no GitLab, no share from the lake. Data scientists: read-only. |
| Production | Workloads | The software supply chain (GitLab, runners, ECR, CodeArtifact), the production SageMaker runtime including the Model Registry, and the lake's **producer**: its job role holds the governed write. No interactive compute, no human control-plane access. |

The full rationale for each placement — why the tooling sits in Production rather than in a separate Shared
Services account (D14), why Identity is its own account (D10), what the Staging account is and is not
(D20), where experimentation ends and development begins (D21), why the lake has its own account (D22), and
how the OUs were chosen (D23) — is recorded one file per decision in `plan/decisions/`
(index: `plan/decisions/INDEX.md`).
