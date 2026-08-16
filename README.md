# AWS-DataScience

Blueprint for using AWS as a Data Science infrastructure provider.

- `CLAUDE.md` — the working rules, and where the current position is recorded. It is size-budgeted
  (20 KB, enforced by `scripts/check-plan-refs.py`), so narrative that grows lives in `docs/plan/`.
- `docs/` — **the documentation tree**, and the only place documentation lives: the plan core, `docs/plan/`,
  `docs/log/`, and the reference files named below. Everything outside it is code, configuration, or the
  working rules themselves.
- `docs/GENERAL_PLAN.md` — the **plan core**: guiding principles, the account map, the two indexes
  (stages and decisions), and the **write** map that says where new content goes. Read this first. The
  **read** map — which file answers which question — is kept only in `CLAUDE.md`, "What to read, and when".
- `docs/plan/` — the plan itself, split so that a task reads only what it needs:
  - `docs/plan/objectives.md` — **what the project must achieve**, in the user's own words. The specification
    every stage is measured against; it lived in `CLAUDE.md` until 2026-08-15 and is copied nowhere.
  - `docs/plan/stages/` — one file per stage, each declaring the decisions it **consumes**.
  - `docs/plan/decisions/` — one file per decision `D1`…`D37`, plus a one-line-per-decision `INDEX.md`. All
    are settled; `D30` was settled as a *revert* and keeps its file, so the record shows what was tried.
  - `docs/plan/runbooks/` — a procedure followed in full and in order, rather than remembered. Two today:
    `break-glass.md`, which says when the Management account root may be used, what to do with it, and what
    watches its use; and `scp-battery.md`, the probe battery run whenever a policy is attached or amended —
    the two distinguishable outcomes of each probe, so a deny is *measured* rather than assumed.
  - `docs/plan/architecture.md`, `docs/plan/conventions.md`, `docs/plan/integrations.md` (the `INT-nn` rows),
    `docs/plan/cost-model.md`, `docs/plan/open-questions.md`, `docs/plan/lessons.md`,
    `docs/plan/institutional-delta.md`, `docs/plan/history.md`.
- `docs/GLOSSARY.md` — every acronym the plan uses, plus its notation and the IAM condition keys it quotes.
- `docs/ORGANIZATION.md` — the account map (one section per account, and the axis each sits on), **the two
  families of IAM role**, and the entitlement plane above them: the SSO users, the seven permission sets,
  the five groups, and the assignment triples binding them to accounts.
- `docs/PRICING.md` — per-unit AWS rates for `sa-east-1` and `us-west-2`, read from the AWS Price List bulk API.
  Unlike the cost figures in `docs/plan/cost-model.md`, which are order-of-magnitude estimates, these are
  measured; the cost model says what is consumed, `docs/PRICING.md` says what a unit of it costs.
- `docs/log/` — record of every step performed manually through the console, **one file per stage**, mirroring
  `docs/plan/stages/` (`docs/log/log-stage-NN-*.md` ↔ `docs/plan/stages/stage-NN-*.md` — the same slug, with a `log-`
  prefix, so the two files never share a name). `docs/log/INDEX.md` says what each file
  records, so finding a step never means reading every log.
- `terraform-live/` — the deployed tree: **one folder per controlled account, sliced into independently
  applied units**, each slice carrying a `[P]`/`[D]`/`[E]` layer. `terraform-live/README.md` explains how it
  is organised and what is in it today; the authoritative slice-by-slice layout is `docs/plan/conventions.md` §6,
  so the two cannot drift. Two things already live here: the five `bootstrap/` slices of Stage 2, and
  `identity/org-policies/`, which holds the ten organization policy documents (SCP, RCP, tag, declarative
  EC2) with `POLICIES.md` indexing every statement and its reason.
- `terraform-modules/` — the reusable modules, consumed **by git tag, never by branch**. `terraform-live/`
  composes; it does not define.
- `.pre-commit-config.yaml` and `.tflint.hcl` — the repository's Terraform gates (Stage 2 step 6):
  `terraform fmt`, `terraform validate`, `tflint` and `checkov` as a *required* check, since a policy gate
  that can be skipped is a policy suggestion.
- `aws/AWS-CLI.md` — the `aws` recipes run by hand, and which identity runs each of them.
- `aws/` — read-only scripts that photograph what is actually deployed, one text snapshot per script under
  the untracked `aws/output/`. `aws/INDEX.md` says which script writes which file and which section of it
  answers which question. Not infrastructure code: nothing here creates or changes a resource — **with one
  fenced exception, `aws/probes/`**, the SCP battery, which has to *attempt* the calls a policy forbids
  because that is the only way to measure a preventive control. It creates nothing, attaches nothing, and is
  run deliberately rather than to gather information.
- `docs/AWS_STATE.md` — the reconciliation layer between the plan, the `docs/log/` and the snapshots: what a snapshot
  is *expected* to show (`INV-nn`), which differences are already accounted for (`EXC-nn`), and what a later
  stage will change. Carries no identifiers and no reasoning on purpose — those live in the snapshot and in
  `docs/plan/decisions/`.
- `docs/REFERENCES.md` — external references used along the way.
- `scripts/` — repository hygiene, not infrastructure: `check-plan-refs.py` validates the plan's internal
  links and stable-ID references, and `gen-backend-hcl.py` / `gen-tfvars.py` write each slice's untracked
  `backend.hcl` and `terraform.auto.tfvars`. A `backend` block interpolates nothing and a `.tf` file may not
  carry a **Region** literal, so those values have to live somewhere else; that somewhere is two generated
  files, neither a `.tf` and neither ever committed, both written from one table so they cannot disagree.
  Four more are the **checks over the Terraform tree** — no Region literal or index-selected AZ in a `.tf`,
  no `aws_s3_account_public_access_block` in any slice, no wildcard-account ARN in an identity-plane policy,
  no OU left out of the authored attachment map, and — `check-bootstrap-parity.py` — no drift between the
  five `bootstrap/` slices, which are one slice copied five times because a module would have to be consumed
  by a git tag that does not exist yet. `slices.py` is the sixth and it is also a *target*: it owns D11's
  layer table and the `up`/`down`/`status` machinery behind the `Makefile`, and as a check it fails when a
  slice on disk declares no layer — the direction that costs money, since `make down` skips in silence what
  it has never heard of.
- `Makefile` — how those checks are run: `make check` offline, `make check-ou` with an SSO session. The same
  scripts sit behind the `pre-commit` hooks, so the commit gate and the target cannot disagree.
  `make` itself is a convenience, not a dependency — every target is a direct call to scripts
  that also run standalone — and `make clean` returns a clone to its just-cloned state: it
  removes `aws/output/`, `.venv/` and the caches, by name, and never touches `secrets/`. **There is
  no CI yet** — GitLab is Stage 7 — and Stage 8 adds a third caller rather than a rewrite.
  It also carries **D11's lifecycle** since Stage 2 step 8: `make slices` prints which slice is `[P]`,
  `[D]` or `[E]`; `make up ENV=<account-folder>` applies the ephemeral ones and starts the dormant ones;
  `make down ENV=…` reverses it; `make status` says what is up and what it burns per hour. **All four are
  honest no-ops today** — every slice on disk is `[P]` — and they were written before the first `[E]` slice
  (Stage 3's `egress/`) rather than after it, so the first teardown that matters meets a `make down` that
  already refuses what it must: a `[P]` slice, a missing `ENV`, `production/pki/` (D36) and `bootstrap/`,
  which holds its own state.
- `pyproject.toml`, `.python-version`, `uv.lock` — **every script in this repository but two is Python 3,
  run through uv** (2026-08-15; they began as shell). The scripts keep their paths and carry the shebang
  `#!/usr/bin/env -S uv run --quiet`, so `./scripts/<name>.py` and `./aws/<name>.py` resolve the pinned
  interpreter and the three shared packages with no activation step: `aws/awslib` (the snapshot scripts'
  common plumbing), `scripts/repohygiene` (project-file checks) and `scripts/tfhygiene` (Terraform-tree
  checks) — the last two deliberately independent of AWS and of each other. Runtime dependencies: none,
  standard library only, which is what keeps the CloudShell fallback (`python3 aws/<name>.py -`) working
  where uv does not exist. The two scripts that exist *only* for CloudShell —
  `aws/cloudshell/management-quotas.sh` and `aws/cloudshell/audit-iam-analyser.sh`, the readings of the
  accounts no profile reaches — stay shell on purpose: standalone single files, needing no
  environment, writing `aws/output/cloudshell/`. `ruff` (dev-only) lints and formats the tree
  through `pre-commit`. A fresh clone needs no setup step: the first script invocation
  bootstraps everything - `uv run` fetches the pinned interpreter if it is absent, creates
  `.venv/` and installs the packages - so `uv sync` exists only as a way to do the same
  thing ahead of time. A fresh clone needs no setup step: the first script invocation
  bootstraps everything - `uv run` fetches the pinned interpreter if it is absent, creates
  `.venv/` and installs the packages - so `uv sync` exists only as a way to do the same
  thing ahead of time.

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

**Whose credential that is, is the whole argument.** The code runs as the *execution role* — the role
SageMaker assumes — and not as the role the person signed in with. So restricting what a data scientist may
*click* does not restrict what their notebook may *reach*, and a control written against the wrong one of the
two constrains nothing. `docs/ORGANIZATION.md`, "The two families of IAM role", carries the distinction and what
actually happens when a job runs.

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
| Studio only in the development / data-science accounts | The interactive surface only in the **Interactive OU** — since D26, one SageMaker unified domain (DataZone V2) registered in **Data Governance**, whose project blueprints provision compute into Sandbox and Development and nowhere else (D17, D21, D26) — enforced by two SCPs (Stage 1c step 7): the `Workloads` OU denies `sagemaker:CreateDomain`, `CreateUserProfile`, `CreatePresignedDomainUrl` **and `datazone:*` in full**, so a deployment target can neither host a domain nor associate itself to one; and the organization root denies `datazone:CreateDomain` everywhere except the `Data` OU, so "one domain, and it lives in Data Governance" is a control rather than a convention | **Adopted**, and made preventive rather than conventional |
| A staging / pre-production deployment target between development and production | The **Staging** account (D20) | **Adopted.** It was missing until 2026-08-08; the plan had tried to stand in for it with a Glue namespace inside Production, which shared an account and a blast radius with the thing it was meant to de-risk |
| Data scientists get read-only access in staging | `DataScientistStagingAccess` — read, no write of any kind (D18) | **Adopted verbatim.** A staging environment a person can write to stops being evidence of what the pipeline does |
| Environments expressed as Organizations OUs | OUs named for their policy sets (D23): `Workloads` holds Staging and Production, `Interactive` holds Development plus a nested `Sandboxes` for the per-unit Sandbox accounts, `Data` holds Data Governance, `Security` holds Log Archive and Audit, and `Identity` holds the identity plane | **Adopted.** One SCP set per policy set, written once and inherited — an OU holding a single account forever would be a folder with one file. Two of the OUs came from execution rather than design: `Identity`, because a foundational `Security` OU would not take the account, and `Sandboxes`, which groups a cardinality class and carries no policy of its own |
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
| Security | Log Archive, Audit | Control Tower guardrails. **Foundational** — Control Tower owns it, and it will not accept an account it did not create there |
| Identity | Identity | No user compute — `DenyUserCompute`, the same statement as `Data`'s and none of its neighbours (1c step 7.6): there is nothing to run in the identity plane, so a compromise of it cannot be turned into compute inside it. Split out of `Security` on 2026-08-09 because the vend into a foundational OU was refused (D23) — so whatever guardrails `Security` carried by being foundational have to be attached here explicitly |
| Interactive | Development, and the nested `Sandboxes` OU | Interactive compute **allowed**, minus **exactly one statement**: no *classic* SageMaker notebook instance (1c step 7.6, 2026-08-13). The lightest set in the tree, and why it is not heavier is below the table. What keeps the data scientist from changing infrastructure is `DataScientistAccess`, an *identity* policy, not this OU |
| Interactive → Sandboxes | Sandbox, one per business unit (D35) | **None of its own, by rule** (D37): nothing is attached or enabled here unless it *differs* from `Interactive`, so what reaches a Sandbox is the organization-root set plus that one deny, inherited. It is a container for a *cardinality class*, not a policy boundary |
| Data | Data Governance | No *user* compute (the DataZone control plane and the catalog-maintenance role are carved out by name); deletion denied |
| Workloads | Staging, Production | No interactive compute; no human control plane |
| Policy Test | Policy Canary | **None of this project's** — this is the OU a *candidate* policy is attached to and exercised against, before it reaches anything real (D29). It does carry the Control Tower controls every governed OU has (the `us-west-2` ceiling and the two root-user controls, 1c step 7.7), so a candidate is measured against the same floor as everything else |

A per-environment OU tree (`Development` OU, `Staging` OU, `Production` OU, one account each) was
considered and rejected — every OU would hold exactly one account, so the tree would add names without
adding inheritance. The revision triggers are recorded in the plan (D23): a second production-like account
nests `Workloads` into `NonProd`/`Prod`; a second data domain does the same for `Data`.

**Two OUs in the table above came from execution, not from this argument, and they are the reason the test
needs a third clause.** `Identity` exists because Control Tower refused to vend the account into `Security`,
which is a *foundational* OU it owns — so the account's policy set has to be attached rather than inherited,
which is precisely what makes it a real OU rather than a folder. `Sandboxes` exists to group the one class of
account that multiplies (D35), and it carries **no policy set of its own**: whatever `Interactive` carries
inherits down into it. So the full test is *an OU earns its existence when two or more accounts need the same
policy set, **or** when it exists to contain a class of account* — a disposable one (`Policy Test`) or a
multiplied one (`Sandboxes`). The nesting also means the organization's OU depth is 2, which is a fact any
code enumerating OUs has to be written against (D34).

**And one clarification about `Interactive` that this table used to get wrong.** It read "human
infrastructure changes denied", as though the OU carried an SCP saying so. It does not, and no SCP in this
design does: what keeps a data scientist from creating a VPC is the `DataScientistAccess` permission set and
its permissions boundary — an **identity** policy. The distinction is not pedantic, because an SCP survives a
mistake in a permission set and a permission set does not survive a mistake in itself. The literal SCP was
considered and is not written for a reason worth knowing: it would have to exempt the identity that *builds*
all the infrastructure in these accounts, and a standing exemption for the builder is the shape D30 proposed
and had reverted. So `Interactive` is the OU where the organization-root ceiling is very nearly the whole
ceiling — interactive compute is allowed because nothing denies it — **plus exactly one statement, adopted
2026-08-13**: no *classic* SageMaker notebook instance. That one was adopted precisely because it is the
candidate that needs no exemption at all. Unified Studio's notebooks and VS Code editors are **spaces and
apps**, a different API surface, so the deny removes an ungoverned way in — one that bypasses the domain,
the VPC-only app configuration and the `dev-env` image gate in a single call — without costing a single
feature the environment is for.

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

**The account map is in [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md)**: an index table of account → OU → axis →
purpose → the policy set that OU carries, then one section per account saying what it holds and what it
deliberately does not — and, after them, the two families of IAM role, the seven permission sets, the
five SSO groups and the assignment triples binding them to accounts.

It is not summarised here on purpose. A second account list is a list that drifts, and it drifts in the
direction of whichever file was edited last.

What this file adds instead is the *argument* for that map: §1-§8 above are why the boundary runs where it
does, and the sections below are how an account comes into existence.

The full rationale for each placement — why the tooling sits in Production rather than in a separate Shared
Services account (D14), why Identity is its own account (D10), what the Staging account is and is not
(D20), where experimentation ends and development begins (D21), why the lake has its own account (D22), and
how the OUs were chosen (D23) — is recorded one file per decision in `docs/plan/decisions/`
(index: `docs/plan/decisions/INDEX.md`).

---

## How OUs and accounts are created

`docs/ORGANIZATION.md` says *which* accounts exist. This section says *how one comes into existence* — a process
that is deliberately not uniform: most accounts are created by hand from the console, and exactly one class
of account is destined for a Terraform-driven flow. The asymmetry is the point, and the reasoning behind it
is recorded in D32, D33, D34 and D35.

### 1. The Organization is deliberately outside Terraform

The first principle of the plan keeps the Management account out of Terraform entirely. Nothing in this
repository will ever declare `aws_organizations_account` or `aws_organizations_organizational_unit`, and the
landing zone itself — Control Tower, its guardrails, its baseline — is enabled through the console and
recorded in `docs/log/log-stage-01a-landing-zone.md`.

That is not a temporary shortcut awaiting codification. It has a direct and useful consequence: **creating an
OU or an account from the console cannot make any Terraform state inconsistent**, because a state file only
tracks what a configuration declares, and no configuration declares these. There is no drift to reconcile,
now or after Terraform starts holding state for everything else.

### 2. Two classes of account, and the boundary between them

Read the account map with the question *"how many of these will exist in five years?"* and it splits in two
(D35):

| Class | Accounts | Cardinality | How it is created |
|---|---|---|---|
| **Structural** | Management, Log Archive, Audit, Identity, Policy Canary, Data Governance, **Development**, Staging, Production | **one, always** | manually, from the console, by the owner named in §3 |
| **Multiplied** | **Sandbox** | **one per business unit** | automated, in Terraform — Stage 14 |

The boundary is not a convenience. It is **exactly the graduation boundary of D21**: in Sandbox the unit of
work is a notebook and the account is for experimentation; in Development the unit of work is a pipeline and
the promotion chain begins. Experimentation is naturally per-business-unit — each unit explores its own data,
with its own people, on its own schedule — while engineering is institutional: one discipline, one set of
repositories, one chain. So the chain reads **N Sandboxes → one Development → one Staging → one
Production**, and the multiplication sits entirely *upstream* of the approval gate, which is the cheapest
place for it to be. N is 1 today.

Two consequences worth stating explicitly, because both are easy to assume wrongly:

- **The promotion chain is untouched by N.** One Development means one set of pipelines, one deploy role
  pair, one approval gate, however many business units exist.
- **Per-unit isolation ends at the graduation boundary.** A unit's experimentation is private to it; its
  engineering is not. Past that line, whatever isolation is required is carried by Lake Formation grants,
  LF-Tags and per-pipeline execution roles — never by an account boundary that is deliberately not there.

### 3. Who creates accounts, and why it is neither root nor the infrastructure user

Accounts are vended through **Control Tower's Account Factory**, from the AWS access portal, as the
`AWS Control Tower Admin` user — **never from the root user**, which gets a Service Catalog portfolio error
by design (D33). That user is Control Tower's own creation rather than this project's, and **its reach is
wider than its name suggests** — wide enough that it is worth reading before trusting any other claim in this
section. `docs/ORGANIZATION.md` ("`AWS Control Tower Admin`") carries the group matrix, what it reaches in each
account, and what permanently limits it.

This was originally sized as a bootstrap credential with an end date. **D34 withdrew that retirement**, on a
premise change rather than a change of mechanism: a sandbox for a new line of work, a second data domain, a
per-workload staging account are ordinary requests, and each of them is an account. A capability that is
exercised indefinitely gets a permanent owner instead of an end date — creating OUs, vending accounts,
enrolling accounts and landing-zone updates, console only.

The alternative was a narrower identity (`AWSServiceCatalogEndUserAccess`, vending only). It was rejected
because **creating an OU is part of the stated job** and the Control Tower console is documented as reachable
only by members of `AWSControlTowerAdmins`; splitting the work across two identities to avoid a permission
one of them holds anyway buys nothing. What the choice does buy is that **the infrastructure user gains no
*standing* reach into the Management account**, which keeps D32's shape intact — *standing* being the precise
word, since that user administers the `Identity` account and an Identity Center delegated administrator can
edit `AWSControlTowerAdmins` membership. The assignment is absent; the path is watched rather than closed
(`docs/ORGANIZATION.md`, "The limit of the separation of duties").

Keeping that identity standing has a price, and it is paid as three permanent controls rather than as a
window that closes — MFA on the user, S3 Object Lock in *compliance* mode on the log archive, and the alarm
on Control Tower group membership. Why none of the three is optional, and why compliance mode specifically,
is in `docs/ORGANIZATION.md`.

What belongs here is the part that is an argument rather than a control: **separation of duties, none, and
that is the honest word.** The identity that creates accounts also administers the account holding the audit
trail, and nobody approves a vend. One human, one lab — recorded in `docs/plan/institutional-delta.md` rather than
argued away.

### 4. What is filled into the vending form

Account Factory asks for an account name, an e-mail address, the destination OU, and **`SSOUserEmail`**. That
last field looks like a contact field and is not: it grants administrative access to the account through
Identity Center. So it always takes the **infrastructure user**, identically on every account (D32) — never
the account's own e-mail address, and never another persona. The result is one administrator, one MFA device,
across every vended account.

Note also that the Identity Center directory is **not empty** at this point: Control Tower populated it with
its own groups and permission sets, and those groups are **pre-wired permission ceilings** — each already
carries its assignments, so adding one person to one of them is an organization-wide grant made by a single
membership edit. No project persona ever joins one. Which groups they are, what each already grants, and the
one that is no longer empty are in `docs/ORGANIZATION.md` ("The groups and permission sets that arrived with it").

### 5. The gate, which comes before the account exists

An account request is answered in this order (D34):

1. **Which axis is it on, and which OU's policy set does it need?** The axes are lifecycle (dev / staging /
   prod), data ownership, and platform. If an existing placement fits — and "another sandbox" almost always
   means the nested `Sandboxes` OU — the account joins it and inherits SCP, RCP, tag policy and the region
   control for free. Note where that inheritance actually comes from today: `Sandboxes` carries no set of
   its own by rule (D37) and `Interactive` above it carries a single deny, so what a new Sandbox inherits is
   the **organization-root** set plus that one statement and `Interactive`'s Control Tower controls. That is
   the ceiling, and it is the reason placing the account correctly is enough.
2. **If no policy set fits, the request is an OU decision, not an account decision** (D23: an OU earns its
   existence when two or more accounts need the same policy set). It then goes through the `Policy Canary`
   battery (D29) before being attached anywhere real.
3. **The post-vend baseline is code that already exists** — which is the whole reason account N+1 is cheap:
   the state bucket slice, the identity assignments, OU membership for the policy set, `foundation/` if the
   account needs a VPC, an SSO profile, and the mandatory tags. For an *interactive* account, name what it
   actually pulls in: Stage 3 (VPC, private hosted zone associations), Stage 4 (peering and VPN reach) and
   Stage 6 (domain association and a project profile). Naming that list is what makes the real cost of "just
   one more sandbox" visible at the moment somebody asks for it, which is the point of having a gate.
4. **Quota headroom is a standing item, not a one-off pre-flight.** Keep slack for a failed provisioning that
   has to be retried; a closed account holds both its slot and its e-mail address for roughly 90 days.

### 6. Why manual creation is safe here — and the failure it *does* introduce

The safety argument is §1: nothing declares the Organization, so nothing can drift. But the failure mode that
replaces drift is worse in one specific way — **it is silent**. Drift is code and reality disagreeing, and
`terraform plan` reports it. This is reality holding something the code never mentioned, and `terraform plan`
reports *"No changes"*. A console-vended account is **invisible**, not **drifted**, and three things are
exactly where that matters:

- **SCP/RCP attachments**, which attach to OUs. An OU created from the console carries no policy set until
  code attaches one.
- **Permission set assignments.** A vended account arrives holding only the direct Account Factory assignment
  and nothing from the group model.
- **Enumerated ARN and account-ID conditions**, which this project's conventions require to be lists rather
  than wildcards. A new account is silently outside every one of them.

The mechanism that answers this — a mechanism, not a checklist line — is:

> **The floor is discovered, the grants are enumerated.**

In [`terraform-live/identity/org-policies/`](terraform-live/identity/org-policies/README.md) — the tree is
explained in [`terraform-live/README.md`](terraform-live/README.md), and every statement in it — of all four
policy types — is
indexed, with its reason, in [`POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) — anything that must
cover *everything* (the organization-root SCP/RCP set, the tag policy, the declarative policy) is attached
to the **root**, so an OU or account created yesterday from the console inherits it with nobody having to
remember. The **per-OU** documents are a different shape and cannot be discovered — each OU has a *different*
document — so they are an authored map, and what `for_each` over the Organizations data sources buys there is
the **check** that fails when a new OU appears in no map (Stage 2 step 9.3).
Permission set assignments stay **explicit**, because a new account silently acquiring `DataScientistAccess`
is precisely the failure the design exists to prevent.

Two properties already work in this flow's favour: SCPs attach to the **OU**, so a new Sandbox inherits its
whole policy set simply by being placed correctly (D23 paying off), and Lake Formation cross-account **v3**
can grant to an OU or to a list, so there is no mechanical ceiling on the number of consumer accounts.

### 7. Where automation goes, and the ladder it climbs

Automation goes where the multiplication is. Vending is not an all-or-nothing choice between "keep doing it
by hand" and "adopt a whole product" — there are three rungs, and naming only the outer two is how the status
quo wins by forfeit (D34):

| Rung | What it is | What it costs |
|---|---|---|
| 1. **Today** | Account Factory from the console, by the owner in §3 | nothing; the request has no diff and no review |
| 2. **The middle** | `aws_servicecatalog_provisioned_product` against the **Account Factory product**, with `AccountEmail`, `AccountName`, `ManagedOrganizationalUnit` and the SSO fields as provisioning parameters | one Terraform slice; a principal with Service Catalog rights **in Management**, which reopens the ownership question; and `prevent_destroy`, because terminating that resource **closes an account** |
| 3. **AFT** (Account Factory for Terraform) | the full product: its own management account, pipelines, per-account customization repositories | a dedicated account slot plus metered services |

**Rung 2 is what Stage 14 uses**, for the Sandbox class only. The account is still created *by Account
Factory*, so Control Tower enrolment, guardrails and baseline are untouched — what changes is only who fills
in the form. The goal of that stage is that adding a business unit is a merge request whose single input is
the unit's name.

The structural accounts stay on rung 1 indefinitely, and that is a considered position rather than
procrastination: automating a form that is filled in nine times, once each, would be code written to be run
once per account and read every time it is changed.

**When this is revisited.** Account creation becoming frequent enough that the post-vend baseline is run from
memory rather than read, or a second human joining — at which point the ladder is walked from rung 1, not
jumped to rung 3, with the cost of whichever rung is chosen *measured* into `docs/PRICING.md` first. For the
Sandbox class specifically, the trigger is a business unit needing its own **Development**, which would move
an account off the structural side of the table and break the "the chain is untouched by N" property the
whole split rests on.
