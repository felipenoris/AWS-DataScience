
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

- Manager user: approves deployment of artifacts.

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
├── data-management/   # the governed lake: no VPC, no compute
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
nothing blocking it.** Decisions D1-D25 are **all** closed and recorded in `GENERAL_PLAN.md` §4 — D7, the
last one still open, was settled on 2026-08-08: Stage 10 builds **two** orchestrators and compares them,
(A) MWAA and (B) EventBridge + Step Functions + Lambda/Fargate, exactly as D5 does for egress. What
remains open inside D7 is only which MWAA shape (Serverless versus `mw1.micro`) and what happens to its
metadata database at teardown. The **nine** accounts in `ACCOUNTS_AND_USERS.md` (e-mails in
`secrets/emails.md`) are the complete set. The SSO user formerly called "sandbox user" is now the **data scientist** user.
**Stage 1 is now two halves:** 1a is the slow, hard-to-undo part (Control Tower, the six Account Factory
accounts, the four OUs, break-glass) and ends at a state you can check; 1b is the fast, reversible part
(identity, SCP/RCP, detective controls, organization-wide enablement).

The shape to hold in mind, because every old habit contradicts some part of it:

- **Four environments, one axis of lifecycle:** Sandbox (experimentation — the unit of work is a
  notebook), Development (the unit of work is a pipeline), Staging and Production (deployment targets,
  written only by the pipeline). Promotion runs **Development → Staging → Production**; Sandbox feeds
  Development through **git graduation**, never through a pipeline (D21).
- **One account off that axis entirely:** Data Management (D22) owns the governed lake; every environment
  reaches it through Lake Formation cross-account shares — read for Sandbox/Development, read plus
  **governed write** for Production's job role (the producer path). Nobody signs in to it interactively.
- **Four OUs, named for their policy sets (D23):** Security; Interactive (Sandbox + Development — the
  only OU where a Studio domain may exist, D17); Data (no compute at all); Workloads (Staging +
  Production — no interactive compute, no human control plane).
- **D18** gives the data scientist read-only permission sets on Staging and Production (data plane, no
  compute); **D19** keeps the derived zones (now per Interactive account) designed rather than left over.
- **Two access paths, not one.** "The VPN is the only entry point" is true because the tunnel is *full*,
  not because it routes into every VPC. Only Sandbox and Production are reachable at the VPC level;
  Development and Staging are used entirely through AWS API endpoints exited via the WireGuard Elastic IP
  — including Studio in Development, whose UI is a public endpoint even for a `VpcOnly` domain. The
  control there is `aws:SourceIp`, never `aws:SourceVpce` (§3).
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
the eleven cross-account integrations in §4.4 that have a fallback each but are not yet known to work.
Of those, **row 11 is the one to settle earliest**: organization-wide RAM sharing plus Lake Formation
cross-account version 3+ are enabled in Stage 1b step 9 and consumed in Stage 5, and their absence makes a
share fail *silently* — the grant succeeds on the producer side and the resource never appears.

State of the environment: nothing is provisioned in AWS beyond the manually created Management account.
The repository contains documentation only; `terraform/` is still empty and must be replaced by
`terraform-live/` and `terraform-modules/` in Stage 2.

### History

- **2026-08-07 - Stage 0 (complete).** Baseline recorded: Management account created manually by the user
  through the console; `aws` CLI 2.36, `terraform` 1.15 and `uv` installed locally; `~/.aws/config` still has
  no SSO profile. English review of `CLAUDE.md`, `README.md` and `REFERENCES.md` — PR #1, merged.
  `GENERAL_PLAN.md` written and then reviewed four times before any AWS resource existed. All of it landed
  in the plan itself, which is the single source of truth for stages 0-13, the numbered decisions and their
  rationale, the data perimeter (§4.2), the two egress designs (§4.3), the cross-account integrations to
  prove (§4.4), the cost and operating model (§5/§5.1), the open questions (§9) and the
  lab-versus-institution delta (§11). The intermediate drafts
  were deleted from both histories on 2026-08-07: nothing had been provisioned, so they described only how
  the document changed, not how the environment did.
- **2026-08-07 - fourth review, driven by two questions from the user.** *Does segregating Sandbox from
  Production make sense with SageMaker, or is the point to promote only code?* and *data scientists will
  have access to both accounts, read-only on the production lake.* The first was answered by checking AWS's
  own multi-account MLOps references (both in `REFERENCES.md`): Studio lives in the development account and
  the deployment targets have no domain — which became D17. The second was a requirement, not a question,
  and became D18 plus D19. **A correction worth carrying forward:** the first response treated
  "read the lake, write the result somewhere less governed" as a hole the new requirement opened. It is
  not — it is a property of every SageMaker installation, true of the Sandbox since Stage 5, and the
  reason it is tolerable is that the data perimeter (§4.2) stops the copy leaving the organization.
  Preventing the copy was never the control. `README.md` gained the account-segregation rationale and
  `GLOSSARY.md` was created in the same pass.
- **2026-08-08 - fifth review: the Staging account (D20).** The user added a `Staging` account to
  `secrets/accounts.md` and asked for the plan to follow the AWS recommendations properly. All three
  references — `amazon-sagemaker-secure-mlops`, the MLOps foundation roadmap, and the MLOps Workload
  Orchestrator — place a pre-production deployment target between the development account and production,
  and this plan had none. **A lesson worth keeping:** the previous revision had *noticed* the gap and
  invented a `staging` Glue namespace inside the Production account to fill it. That stand-in was wrong in
  a specific and instructive way — it shared an account, an IAM surface and a blast radius with the thing
  it was meant to de-risk, so it could catch a schema error but never a permission error, which is the
  failure class a cross-account promotion actually produces. It has been removed. Seven accounts now, a
  `Workloads` OU, a promotion chain with two named deploy roles, a third VPC that is deliberately *not*
  peered, and a cost floor of ~USD 19-24. `README.md` gained a section summarising each of the three
  references and a table of what this project adopts versus where it departs (tooling in Production, no
  data-lake account, sampled staging data).
- **2026-08-08 - sixth review: the nine-account layout (D21, D22, D23).** After the chat answered three
  questions — Development×Experimentation, OU×Account, Data Management×Production — the user reorganized
  the accounts to match: created **Development** (Sandbox becomes pure experimentation; the promotion
  chain now starts in Development, and Sandbox → Development is a git graduation, not a pipeline) and
  **Data Management** (the governed lake leaves the environment accounts; LF cross-account shares become
  the default read path, and Production's job role holds the governed write — the producer path). The
  file layout changed too: `ACCOUNTS_AND_USERS.md` at the repository root describes accounts and users;
  `secrets/` now holds only `emails.md`; the SSO "sandbox user" was renamed **data scientist**. OUs were
  settled as policy sets (D23): Security, Interactive, Data, Workloads — with the rejection of
  one-account-per-OU recorded, and nesting triggers written down. Two departures from the AWS references
  thereby closed (data account, experimentation/development split); the tooling-in-Production departure
  (D14) is the main one that remains. Plan-wide consequences: nine §4.4 integration rows (notably the
  Development↔Production peering for GitLab and the three LF shares), floor ~USD 21-27, six state
  buckets, Stage 5 rebuilt around the Data Management account with a consumer slice applied to both
  Interactive accounts, and Stage 9 reframed as "the deployment targets' platforms plus the producer
  path". `README.md` gained the three-distinctions section; `GLOSSARY.md` gained graduation, producer
  path and the four-OU entry.

- **2026-08-08 - seventh review: consistency pass over the nine-account layout (D24, D25).** The user asked
  for a sweep of every repository file against the reorganized account set. Two kinds of finding came out
  of it, and the second kind is the one worth remembering. The first was residue — counts and names the
  previous revision had not chased down (seven Config recorders, "Sandbox in its own OU", AFT "three
  accounts", `Environment=sandbox|production|shared`, ECR/CodeArtifact granted only to Sandbox, the
  `awsds-prod-raw-data` example naming a bucket D22 had moved). Mechanical, fixed in one pass.
  The second kind was **things the reorganization created and nobody had noticed were now unanswered**:
  the shared EFS had silently become Sandbox-only when a second Studio domain appeared (**D24** makes that
  a decision and records the revision trigger); the ingestion drop-box had a writer and no reader
  (**D25** puts the pickup in Production on the producer path, and in doing so exposed that the `Data` OU
  SCP never denied Glue jobs — so "no compute in Data Management" was an intention, not a control); and
  the three Lake Formation shares needed organization-wide RAM sharing plus cross-account version 3+,
  which no stage enabled. **The sharpest one, and the lesson to carry:** Stage 5 told the reader to pin
  the Data Management bucket policies to the consumers' `aws:SourceVpce` — but interface endpoints are
  `[E]`, so their IDs change on every `make up`, and since D22 they live in a *different account* from
  the policy, so nothing would repair it. The fix is to anchor on the `[P]` S3 **gateway** endpoints (or
  on `aws:SourceVpc`). The general form: **when a decision moves a resource across an account boundary,
  re-check every condition that referenced it — especially conditions pointing at ephemeral things.**
  Stage 1 was also split into 1a (landing zone, hard to undo, ends checkable) and 1b (identity, policies,
  detective controls, org-wide enablement).
- **2026-08-08 - eighth review: D7 closed, and prices stopped being estimates (`PRICING.md`).** The user
  asked a narrow question — *is the USD 360/month MWAA figure charged per hour, and is that infra `[P]`,
  `[D]` or `[E]`?* Both answers were in the plan (yes, per hour of *existence*, at one-second resolution,
  DAGs running or not; and `[E]`), but checking them exposed that the D7 options table had gone stale in
  the direction that mattered: **`mw1.micro`** (USD 0.29/h) and **MWAA Serverless** (USD 0.088 per
  task-hour, no environment fee, GA November 2025) did not exist when it was written, and Serverless
  dissolves the "USD 350/month floor" that §5 used to rule MWAA out. The user then decided D7 by
  **building both**: (A) MWAA and (B) EventBridge + Step Functions + Lambda/Fargate — the same
  build-both-and-compare shape as D5. SageMaker Pipelines and self-managed Airflow on ECS stay documented,
  unbuilt. **The `[E]` caveat is the part to carry forward:** MWAA takes ~20-30 min to create or delete,
  so it does not fit the `make up`/`make down` cadence, and its metadata database (run history, XComs,
  UI-defined connections) is state living only inside an `[E]` resource — the exact failure §5.1 rule 2
  exists to prevent, and the third time this project has hit it after EFS and the Studio domain.
  `PRICING.md` was created in the same pass and is a different kind of artifact from the rest of the
  repository: **measured, not reasoned.** Every rate comes from the AWS Price List bulk API
  (`pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<service>/current/<region>/index.json`), for
  `sa-east-1` and `us-west-2` side by side. Two things fell out of it that no amount of re-reading the
  plan would have produced: the São Paulo premium is **real and roughly 1.5-2.1x** (the 2026-08-07 guess
  of "~1.5-2x" was right), and **CodeArtifact does not exist in `sa-east-1`** — thirteen Regions, not
  including São Paulo — which the original Region check had missed and which is a *missing component* for
  D14 and egress design B, not a price difference. **The habit worth keeping: the bulk API is public, needs
  no credentials, and answers in seconds what the pricing pages answer in paragraphs.**
