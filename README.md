# AWS-DataScience

Blueprint for using AWS as a Data Science infrastructure provider.

- `CLAUDE.md` — goals and working rules.
- `GENERAL_PLAN.md` — the staged implementation plan (stages, decisions, cost model).
- `GLOSSARY.md` — every acronym the plan uses, plus its notation and the IAM condition keys it quotes.
- `LOG.md` — record of every step performed manually through the console.
- `REFERENCES.md` — external references used along the way.

---

## Account segregation

The environment is split across seven AWS accounts under a single AWS Organization. The cheaper alternative —
one account, with environments separated by tags, bucket prefixes and IAM policies — is simpler to build and
simpler to operate, so the split has to earn itself. It does, and the reasons below are specific to a data
science environment rather than generic "dev and prod should be separate" advice. The next section records
which parts of the layout come from AWS's own reference architectures and which are this project's own
compromises.

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
- **Interactive compute lives only in the Sandbox.** SageMaker Studio (domain, user profiles, JupyterLab and
  Code Editor apps) exists in the Sandbox account and nowhere else, enforced by a Service Control Policy on
  the `Workloads` OU rather than left as an intention. SageMaker's *runtime* APIs — training and processing
  jobs, Pipelines, Model Registry, endpoints — do exist in Staging and Production, because that is where
  models are tested, retrained and served; the difference is that only a pipeline submits to them. A Studio
  domain in a deployment target would put unreviewed code back inside the account boundary, which is
  precisely what the split exists to prevent.

### 7. What crosses the boundary

Artifacts cross in one direction only, through the pipeline, and they pass through Staging on the way:

- container images (ECR),
- model versions (SageMaker Model Registry),
- workflow definitions and application code (a Git tag),
- the Terraform that instantiates them.

The chain is **Sandbox → Staging → Production**. Staging receives the built artifact, runs the integration
tests against a sampled or synthetic dataset, and is torn down again; only then does a human approval release
the same artifact to Production. A failure in Staging stops the chain, and Production is never touched.

Data crosses in the other direction, read-only: production catalog resources are shared to the Sandbox through
Lake Formation, so that development happens against real data without making a copy of it. Staging is not part
of that share — it never holds production data, for the reason given in the next section.

Anything that crosses outside this list — a shared S3 bucket used to hand files between accounts, for
instance — is a promotion path that bypasses the approval gate, and is therefore not built.

### 8. What the split costs

The split is not free, and the plan accepts the cost deliberately rather than pretending it away:

- one AWS Config recorder per governed account, and there are now seven of them;
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
team account. Shared-services and data-management account groups are offered as optional additions for
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
| Studio only in the development / data-science account | Studio only in **Sandbox** (D17), enforced by an SCP on the `Workloads` OU denying `sagemaker:CreateDomain`, `CreateUserProfile` and `CreatePresignedDomainUrl` | **Adopted**, and made preventive rather than conventional |
| A staging / pre-production deployment target between development and production | The **Staging** account (D20) | **Adopted.** It was missing until 2026-08-08; the plan had tried to stand in for it with a Glue namespace inside Production, which shared an account and a blast radius with the thing it was meant to de-risk |
| Data scientists get read-only access in staging | `DataScientistStagingAccess` — read, no write of any kind (D18) | **Adopted verbatim.** A staging environment a person can write to stops being evidence of what the pipeline does |
| Environments expressed as Organizations OUs | `Workloads` OU holding Staging and Production; `Sandbox` in its own OU | **Adopted.** One SCP set for both deployment targets, written once |
| Model Registry and ECR in a Tooling / shared-services account | Both in the **Production** account (D14) | **Departure.** No separate tooling account, on cost. The consequence is stated rather than hidden: there is no boundary between what builds and what runs, so a compromise of GitLab is a compromise of Production |
| A separate data lake / data management account | The lake lives inside the Sandbox and Production accounts | **Departure.** The lab conflates *environment* with *data domain*; a real organization has many domains per environment |
| Experimentation and development as distinct accounts | Collapsed into one **Sandbox** account | **Departure**, and an easy one: with a single user there is no handover between the two, so the distinction buys nothing |
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

## The accounts

Seven accounts, all under one AWS Organization governed by Control Tower.

| Account | OU | Purpose |
|---|---|---|
| Management | root | Organization owner. Bootstrap only, manual, through the console. Never managed by Terraform. |
| Log Archive | Security | Central, tamper-evident log store (S3 Object Lock). Created by Control Tower. |
| Audit | Security | Security guardian: GuardDuty, Security Hub, Macie, IAM Access Analyzer. Created by Control Tower. |
| Identity | Security | Delegated administration of IAM Identity Center: permission sets, groups, assignments. Separate from Audit so that access management and security monitoring do not share a blast radius. |
| Sandbox | Sandbox | Where data scientists work. SageMaker Studio, interactive compute, unreviewed code — the highest-risk account, per §3 above. Its own OU, because interactive compute is allowed here and nowhere else. |
| Staging | Workloads | Deployment target. Receives the built artifact, runs the integration tests against sampled or synthetic data, and is torn down again. No Studio domain, no Model Registry of its own, no GitLab. Data scientists: read-only. |
| Production | Workloads | Production data platform, the software supply chain (GitLab, runners, ECR, CodeArtifact) and the production SageMaker runtime including the Model Registry. No interactive compute, no human control-plane access. |

The full rationale for each placement — why the tooling sits in Production rather than in a separate Shared
Services account (D14), why Identity is its own account (D10), and what the Staging account is and is not
(D20) — is recorded in `GENERAL_PLAN.md` §4.
