
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

- Data Scientist user: regular user, with no permissions to perform infrastructure changes, except for artifacts managed by AWS SageMaker. This user can write data, develop applications, and trigger CI/CD deploy pipelines to promote artifacts from the Sandbox to the Production environment.

- Manager user: approves deployment of artifacts.

## terraform

- All infrastructure code will be in Terraform.

- Steps done manually by me will be recorded in the `LOG.md` file. Never update `LOG.md`. I'll edit this file.

- The Terraform code will have a subfolder for each controlled account (environment).

```
terraform-live/
├── sandbox/
│   ├── networking/
│   ├── shared-services/
│   └── app/
|        └── app-etl/ # references the app-etl application source code by tag version
└── production/
    └── ...

terraform-modules/ # reusable modules used by applications
├── step-function/
│   └── ...
└── iam-role/
    └── ...
```

## secrets folder

I'll store my personal information in the secrets folder. Never touch it. This folder is added to the `.gitignore`.

## References

On every interaction, add to `REFERENCES.md` all the internet links Claude used as references.

## `README.md`

Update `README.md` with information about how we are structuring our AWS resources. Also, document the project layout so that people can understand the files and main components.

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

**Stage 0 (Baseline) is complete. Stage 1 (Organization, accounts and identity) is ready to start, with
nothing blocking it.** Decisions D1-D23 are closed and recorded in `GENERAL_PLAN.md` §4, with the single
exception of D7 (production orchestrator), deliberately deferred to Stage 10 because that is where it is
consumed. The **nine** accounts in `ACCOUNTS_AND_USERS.md` (e-mails in `secrets/emails.md`) are the
complete set. The SSO user formerly called "sandbox user" is now the **data scientist** user.

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

`README.md` carries the argument for the account split, the summaries of the three AWS reference
architectures, and the three distinctions (Development×Experimentation, OU×Account, Data
Management×Production).

Two inputs are still needed from the user, neither blocking Stage 1: **which domain name to register**
(D15, blocks Stage 7) and the outcome of the AZ name-to-ID check in Stage 1 step 16, which decides whether
Stage 3 anchors subnets on list position or on AZ IDs. Both are tracked in `GENERAL_PLAN.md` §9, alongside
the nine cross-account integrations in §4.4 that have a fallback each but are not yet known to work.

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
