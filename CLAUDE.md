
# General Objective

The objective of this project is to create a Data Science environment based on AWS cloud infrastructure, using my personal AWS account.

The goal is to achieve the following:

- All user access to the cloud infrastructure will be performed through a VPN.

- Use SageMaker as a development tool for Data Scientists.

- Protect data against leakage (DLP), mainly targeting SageMaker. There is no single AWS product that does
  this, so the requirement is broken into the four problems it has to solve:

	- sensitive-data discovery and classification: know which sensitive data exists and where it is stored.
	- fine-grained access control: restrict who can read which database, table, column and row.
	- egress control: restrict where data can be sent to from the development environment.
	- exfiltration detection: detect and alert on abnormal data access or data movement.

- SageMaker should have access to the internet. We'll explore implementing some restrictions, keeping the possibility of software updates, installing packages, and accessing a few websites.

- Use GitLab hosted on AWS for source-code control.

- Use GitLab Pages to host docs.

- Use GitLab CI/CD to automate tests, docs and deployment.

- Use three kinds of CI/CD pipelines:

	- pipeline to build a development environment: this will be the Docker container (or image) used by developers on SageMaker.
	- pipeline to build an application: this should build a Docker image of the app.
	- pipeline to deploy an application into the production environment.

- Explore the possibility of deploying a workflow developed in SageMaker (Airflow/MWAA) to production.

- Use an NFS solution to exchange files between users, the SageMaker environment and S3 buckets.

- Data-science assets and databases should not face the public internet. Later in the project we'll experiment with setting up a web server facing the public internet, accessing a backend or database protected in the private subnet.

- Let's avoid using IAM Users, in favor of assuming IAM Roles temporarily.

- Use AWS CloudWatch to monitor the cloud infrastructure.

- Use AWS Organizations + Control Tower to set up account permissions.

- Use AWS Lake Formation to share data cross-account.

- Use AWS Glue Data Catalog with data stored on S3 buckets, using ICEBERG format, as Data Warehouse.

- Use Amazon ECR as container registry.

## How this will be done

We will start from scratch: the starting point is a root AWS account created manually.

The project will be implemented incrementally.

I'll ask Claude to plan the next step and Claude will guide me on each step until we reach the project goals.

## Application source code layout

This is a template for an application developed by a data scientist and intended for deployment in a production environment.

```
app-etl/
├── src/
│   ├── main.py
│   ├── pipeline/
│   └── sql/
├── tests/
│   ├── test_pipeline.py
│   └── test_sql.py
├── .gitlab-ci.yml
├── Dockerfile # builds the application Docker container for deployment
├── terraform/ # uses predefined Terraform modules hosted at `terraform-modules`
│   ├── main.tf
│   ├── variables.tf
│   └── envs/
├── pyproject.toml
└── README.md
```

The development stack is similar to this application: <https://github.com/felipenoris/etl-cookbook-tutorial>.

# Guidelines

## AWS Region

All infrastructure will be deployed in the `us-west-2` Region.

## LOG

`LOG.md` contains all the actions performed during this project.
Never update `LOG.md`. I'll edit this file.

## Tools installed in the current environment

- terraform: <https://developer.hashicorp.com/terraform/install>.

- aws client: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>.

- uv: <https://docs.astral.sh/uv/>.

## `secrets` folder

This folder is ignored by git. It contains personal information. Never edit this folder. Claude can read the files in this folder to gather information.

## Accounts and Users

- The file `ACCOUNTS_AND_USERS.md` contains the AWS accounts and users.

- All accounts will be registered under an AWS Organization managed by the `Management Account`.

- Accounts will be used to isolate environments: (1) Sandbox, (2) Development, (3) Staging and (4) Production.

- Promotion happens from: Development -> Staging -> Production. Given that Sandbox is the experimentation environment.

- Infrastructure user: user with Administrator permissions.

- Data Scientist user: regular user, with no permissions to perform infrastructure changes, except for artifacts managed by AWS SageMaker. This user can write data, develop applications, and trigger CI/CD deploy pipelines that promote artifacts along the chain Development -> Staging -> Production. Sandbox work enters that chain by graduating into a Development repository through git, never by a pipeline.

- Deployment Manager user: approves deployment of artifacts along Development -> Staging -> Production.

- Governance Manager user: approves data subscriptions and other access to data. Domain owner of the SageMaker Unified Studio domain.

## terraform

- All infrastructure code will be in Terraform.

- Steps done manually by me will be recorded in the `LOG.md` file. Never update `LOG.md`. I'll edit this file.

- The Terraform code will have a subfolder for each controlled account (environment).

```
terraform-live/
├── identity/          # permission sets, groups and assignments (delegated admin)
├── sandbox/           # experimentation
│   ├── bootstrap/     # Terraform state bucket for this account
│   ├── foundation/    # VPC, subnets, KMS, IAM roles - free at rest, never destroyed
│   ├── data/          # scratch and derived-zone buckets, Athena workgroup, LF links
│   ├── egress/        # NAT and interface VPC endpoints - metered, destroyed per session
│   ├── vpn/           # WireGuard
│   ├── nfs/           # EFS
│   └── sagemaker/     # Studio domain and user profiles
├── development/       # pipeline engineering - same shape, no vpn/ and no nfs/
├── data-governance/   # the governed lake + the Unified Studio domain: no VPC, no user compute
├── staging/           # deployment target, driven by the promotion pipeline
└── production/        # deployment target + GitLab, runners, ECR, CodeArtifact
    └── app/
        └── app-etl/   # references the app-etl application source code by tag version

terraform-modules/ # reusable modules used by applications
├── step-function/
│   └── ...
└── iam-role/
    └── ...
```

The authoritative layout, with the `[P]`/`[D]`/`[E]` layer of every slice, is in `GENERAL_PLAN.md` §6.

## secrets folder

I'll store my personal information in the secrets folder. Never touch it. This folder is added to the `.gitignore`.

## References

On every interaction, add to `REFERENCES.md` all the internet links Claude used as references.

## `README.md`

Update `README.md` with information about how we are structuring our AWS resources. Also, document the project layout so that people can understand the files and main components.

## Pricing

For every new AWS service referenced, update `PRICING.md`.

# Claude memory

Edit this section with the main ideas gathered in this project, so that your future self will understand the context.

Never use external memory to store information. Store all your memory from this project in this session, and use it.

## Language

Use English when writing source code or any files in this repository.
When responding in chat, always write in Portuguese (Brazil).

## Expertise

This implementation plan assumes that the reader is a software or computer engineer with experience in software development and finance. The reader has basic knowledge of networking, AWS cloud services, and Terraform, and is familiar with Bash, Python, C, Rust, Julia, and R. Since DevOps is not the reader's primary area of expertise, provide sufficient context and explain the rationale behind DevOps-related tasks rather than assuming prior knowledge.

## git

You can edit files in the main branch, but never commit before asking.

Always commit changes to a separate branch with the `claude/` prefix.

Sometimes I'll commit the changes myself; in that case, there's nothing left for you to do.

When I authorize you, you can commit, push and open Pull Requests on GitHub. I'll merge them. After the merge, always synchronize the local folder with the upstream repo.

## Claude LOG

For every project step, review this section and add your own LOG, so that you can remember the current stage of this project.

Stage numbers refer to `GENERAL_PLAN.md`, which is the staged implementation plan for this project.
Always read `GENERAL_PLAN.md` before planning or executing a step.

### Current position

**Stage 0 (Baseline) is complete. Stage 1a (landing zone, accounts, OUs) is ready to start, with
nothing blocking it.** Decisions D1-D28 are **all** closed and recorded in `GENERAL_PLAN.md` §4. The
ninth revision (2026-08-08) adopted **SageMaker Unified Studio**: one DataZone **V2** domain in
Development (D26, official `aws-ia` Terraform module — domain via `aws`, blueprints/projects via
`awscc`), Glue Crawlers on raw + drop-box under a named catalog-maintenance exception (D27), and the
production workflow contract (D28: six artifact classes the pipeline creates; no domain or blueprint
ever touches a deployment target). D7 builds **two** orchestrators in Stage 10 and compares them:
(A) **MWAA Serverless** — Terraform path verified: `awscc_mwaaserverless_workflow`, from
`AWS::MWAAServerless::Workflow`; fallbacks CFN-stack wrapper, then `mw1.micro` — and (B) EventBridge
Scheduler + Step Functions + Lambda/Fargate, both with explicit per-workflow CloudWatch log groups. The
**nine** accounts in `ACCOUNTS_AND_USERS.md` (e-mails in `secrets/emails.md`) are the complete set. The SSO users are **four**: infrastructure, data scientist (formerly "sandbox user"), and — since 2026-08-08 — **deployment manager** and **governance manager**, split out of the single `Manager` persona because one signature must not be able to release a job *and* grant it the data it reads.
**Stage 1 is now two halves:** 1a is the slow, hard-to-undo part (Control Tower, the six Account Factory
accounts, the four OUs, break-glass) and ends at a state you can check; 1b is the fast, reversible part
(identity, SCP/RCP, detective controls, organization-wide enablement).

The shape to hold in mind, because every old habit contradicts some part of it:

- **Four environments, one axis of lifecycle:** Sandbox (experimentation — the unit of work is a
  notebook), Development (the unit of work is a pipeline), Staging and Production (deployment targets,
  written only by the pipeline). Promotion runs **Development → Staging → Production**; Sandbox feeds
  Development through **git graduation**, never through a pipeline (D21).
- **Three groups, not one sequence** (`ACCOUNTS_AND_USERS.md` carries the per-account classification):
  the **lifecycle** axis (Sandbox before the chain, then Development → Staging → Production), the
  **ownership** axis (Data Governance alone), and the **platform** accounts on neither (Management, Log
  Archive, Audit, Identity). *An account off the lifecycle axis is not "a production account"* — that
  question gets asked every time; the answer is that Data Governance and Identity are **high blast
  radius**, which is a different property from being production.
- **One account off that axis entirely:** Data Governance (D22) owns the governed lake; every environment
  reaches it through Lake Formation cross-account shares — read for Sandbox/Development, read plus
  **governed write** for Production's job role (the producer path). Nobody signs in to it interactively.
- **Four OUs, named for their policy sets (D23):** Security; Interactive (Sandbox + Development — the
  only OU where a domain may exist, D17); Data (no *user* compute — D27 carves out catalog maintenance:
  crawlers and table optimizers under the lake's own role, never on Iceberg tables); Workloads (Staging +
  Production — no interactive compute, no human control plane).
- **One unified domain, projects as the isolation unit (D26):** the DataZone V2 domain is registered in
  **Data Governance** (renamed from Data Management on 2026-08-08) because a domain is a registry of
  projects and data products — ownership axis, not lifecycle axis. **It holds no compute:** the
  `experimentation` project profile provisions into Sandbox, `engineering` into Development, and nothing
  is ever provisioned into the domain account itself. Sandbox×Development is therefore *strengthened*, not
  dissolved — it stops being "which URL did the person open" and becomes a property of the project.
  Lakehouse blueprint in its Glue/Athena form only — **never** the Redshift Serverless variant.
  Staging and Production are never associated. What crosses the gate is
  the D28 artifact set — image, workflow YAML in S3, per-workflow role, orchestration resource, log
  group, model package group — carried by the project's git repository, linted against domain-scoped
  references.
- **D18** gives the data scientist read-only permission sets on Staging and Production (data plane, no
  compute); **D19** keeps the derived zones (now per Interactive account) designed rather than left over.
- **Two access paths, not one.** "The VPN is the only entry point" is true because the tunnel is *full*,
  not because it routes into every VPC. Only Sandbox and Production are reachable at the VPC level;
  Development and Staging are used entirely through AWS API endpoints exited via the WireGuard Elastic IP
  — including the Unified Studio portal, which is a public endpoint even when project compute is
  VPC-only. The control there is `aws:SourceIp`, never `aws:SourceVpce` (§3).
- **D24:** the shared EFS lives in Sandbox only; Development gets neither its own nor a path to it, and
  the exchange between the two Interactive accounts is S3 and git. **D25:** the ingestion drop-box is
  picked up by Production's job role on the producer path — which also closed a hole where the `Data` OU
  SCP never denied Glue jobs.

`README.md` carries the argument for the account split, the summaries of the three AWS reference
architectures, and the three distinctions (Development×Experimentation, OU×Account, Data
Management×Production).

Two inputs are still needed from the user, neither blocking Stage 1: **which domain name to register**
(D15, blocks Stage 7) and the outcome of the AZ name-to-ID check in Stage 1b step 11, which decides whether
Stage 3 anchors subnets on list position or on AZ IDs. Both are tracked in `GENERAL_PLAN.md` §9, alongside
the fourteen cross-account integrations in §4.4 that have a fallback each but are not yet known to work.
Of those, **row 11 is the one to settle earliest**: organization-wide RAM sharing plus Lake Formation
cross-account version 3+ are enabled in Stage 1b step 9 and consumed in Stage 5 — and since D26 also
carry the domain's account associations (row 12) — and their absence makes a
share fail *silently*: the grant succeeds on the producer side and the resource never appears. **Row 13**
(CodeConnections from the unified domain to the self-hosted GitLab in a private subnet) is the one with
no convenience-preserving fallback; check it while building Stage 7.

State of the environment: nothing is provisioned in AWS beyond the manually created Management account.
The repository contains documentation only; `terraform/` is still empty and must be replaced by
`terraform-live/` and `terraform-modules/` in Stage 2.

### History

- **2026-08-07 / 2026-08-08 — Stage 0 (complete), and the plan.** Management account created manually by
  the user through the console; `aws` CLI 2.36, `terraform` 1.15 and `uv` installed locally;
  `~/.aws/config` still has no SSO profile. English review of `CLAUDE.md`, `README.md` and
  `REFERENCES.md` — PR #1, merged. `GENERAL_PLAN.md` was then written and revised ten times before any
  AWS resource existed, arriving at the nine-account / four-OU layout and D1-D28, all closed — the ninth
  revision adopting SageMaker Unified Studio (D26), the catalog-maintenance carve-out (D27) and the
  production workflow contract (D28), and the tenth placing the domain on the ownership axis — which
  renamed `Data Management` to **`Data Governance`**, needed no new account, and split the `Manager`
  persona into **Deployment Manager** and **Governance Manager**;
  `GLOSSARY.md` and `PRICING.md` were created along the way. The individual revisions are deliberately
  not recorded: with nothing provisioned they describe how the document changed, not how the environment
  did, and everything that survived them is in `GENERAL_PLAN.md` — §4 for the decisions and their
  rationale, §11 for the lab-versus-institution delta.

### Lessons carried forward

Findings from the planning period that are **not** recoverable by re-reading `GENERAL_PLAN.md`. Add to
this list only what would otherwise be relearned the hard way.

1. **A copy of governed data landing somewhere less governed is not a hole to be closed.** It is a
   property of every SageMaker installation, not something D18 introduced. The control is the data
   perimeter (§4.2), which stops the copy leaving the organization; preventing the copy was never the
   control. The first answer given on this got it wrong and treated it as a newly opened gap.
2. **A stand-in that shares an account with the thing it de-risks proves nothing about permissions.** A
   `staging` Glue namespace *inside* Production was once invented to substitute for a Staging account: it
   shared an IAM surface and a blast radius with its own subject, so it could catch a schema error and
   never a permission error — which is the failure class a cross-account promotion actually produces.
   That is why D20 exists.
3. **When a decision moves a resource across an account boundary, re-check every condition that
   referenced it — especially conditions pointing at ephemeral things.** This nearly shipped: Stage 5
   pinned the Data Governance bucket policies to the consumers' `aws:SourceVpce`, but interface endpoints
   are `[E]` (new IDs on every `make up`) and since D22 live in a *different* account, so nothing would
   ever repair them. Anchor on the `[P]` S3 **gateway** endpoint, or on `aws:SourceVpc`.
4. **State that lives only inside an `[E]` resource is this design's recurring failure mode** (§5.1 rule
   2). Three hits already — EFS, the Studio domain, MWAA's metadata database — and it will recur for
   every stateful service considered for the `make up`/`make down` cadence. Check it before adopting one.
5. **An intention is not a control.** "No compute in Data Governance" was written down for a whole
   revision before anyone noticed the `Data` OU SCP never denied Glue jobs (D25). Likewise the three Lake
   Formation shares assumed organization-wide RAM sharing and cross-account version 3+ that no stage
   enabled — and their absence makes a share fail *silently*, the grant succeeding while the resource
   never appears. For every stated property, name the policy line that enforces it.
6. **Prices are measured, not reasoned.** The AWS Price List bulk API
   (`pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<service>/current/<region>/index.json`) is public,
   needs no credentials, and answers in seconds what the pricing pages answer in paragraphs. It is also
   how a *missing component* was found rather than a price difference — CodeArtifact does not exist in
   `sa-east-1` — which the Region check done by reading had missed. `PRICING.md` is built this way.
7. **A rejected-on-cost option goes stale in the direction that flatters the rejection.** The D7 table
   ruled MWAA out on a standing-cost floor that `mw1.micro` and MWAA Serverless had since removed.
   Re-check the price and the shape of any service the plan rejected on cost before acting on it. The
   same pattern closed D26 a day later: Unified Studio was rejected partly for having no IaC path, and
   official Terraform support had arrived (2026-07) before the rejection was ever acted on.
8. **When the classic `aws` provider lacks a resource, check the CloudFormation registry and `awscc`
   before declaring a Terraform gap.** `AWS::MWAAServerless::Workflow` existed, and `awscc` exposes
   every registry type mechanically — the "open issue, no branch" on the classic provider was the wrong
   place to look. The `aws-ia` Unified Studio module itself splits the same way: domain via `aws`,
   projects and blueprints via `awscc`.
9. **The axis question applies to people as well as to resources.** The same pass that moved the domain
   onto the ownership axis split the `Manager` persona along it: **Deployment Manager** (lifecycle —
   approves releases) and **Governance Manager** (ownership — approves data access). This had been
   written into §11 as "what an institution would do, notational here" a few hours earlier, and that was
   wrong: with one persona, a single human writes a job that reads restricted data, approves its release
   **and** approves its access to that data. Three acts, one signature. Never assign one person to both
   groups. The related trap: the governance manager must **not** have blanket read on the data they gate
   — an approver who can already read everything is not exercising a control.
10. **Before placing a new resource in an account, ask which axis it is on — and check whether a
   *registry* is being confused with a *runtime*.** D26's first draft put the Unified Studio domain in
   Development because that is where people work. Wrong: a domain holds projects, profiles, blueprints
   and the catalog, while blueprints provision the compute into whichever account the profile names. It
   is an ownership-axis resource and belongs with the catalog it governs (which is also what makes
   subscription fulfilment a *local* Lake Formation grant). The recurring symptom of getting this wrong
   is the question "so is that a production account?" — the honest answer is that off-axis accounts are
   not production, they are cross-cutting, and some of them are high blast radius instead.
