
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

This folder is ignored by git. It contains personal information. Never edit this folder, and never
write anything into it. Claude can read the files in this folder to gather information.

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

- Two trees: `terraform-live/` (one subfolder per controlled account, sliced by lifecycle layer) and
  `terraform-modules/` (reusable modules, consumed by git tag). **The authoritative layout, with the
  `[P]`/`[D]`/`[E]` layer of every slice, is in [`plan/conventions.md`](plan/conventions.md) §6** —
  kept in one place on purpose, so the two copies cannot drift.

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

For every project step, review this section and add your own LOG, so that you can remember the current
stage of this project.

Stage numbers refer to `plan/stages/`. **Always read `GENERAL_PLAN.md` before planning or executing a
step** — it is the plan core and carries both indexes — then read only the stage file and the decisions
its `Consumes` row lists.

### What to read, and when

| Task | Read |
|---|---|
| Anything | this file + `GENERAL_PLAN.md` (plan core: principles, account map, both indexes) |
| Execute a stage | [`plan/stages/`](plan/stages/INDEX.md)`stage-NN-*.md`, the decisions in its **Consumes** row, and [`plan/conventions.md`](plan/conventions.md) |
| Plan, review, or settle a decision | add [`plan/lessons.md`](plan/lessons.md) and [`plan/open-questions.md`](plan/open-questions.md) |
| Look up a decision | [`plan/decisions/INDEX.md`](plan/decisions/INDEX.md) first — open a decision file only for its reasoning |
| Cost of a new service | [`PRICING.md`](PRICING.md) — measured from the Price List API, never estimated (Lesson 6) |
| Cross-account wiring | [`plan/integrations.md`](plan/integrations.md), rows `INT-01`…`INT-16` |
| "What would an institution do?" | [`plan/institutional-delta.md`](plan/institutional-delta.md) |

Do not open by habit: [`plan/history.md`](plan/history.md), [`plan/institutional-delta.md`](plan/institutional-delta.md).
Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1b step 7` — never by section or row number.

### Current position

- **Stage 0 complete. Stage 1a is ready to start, with nothing blocking it.**
- **Nothing is provisioned in AWS** beyond the Management account, created manually by the user.
- The repository is documentation only; `terraform/` is empty and is replaced by `terraform-live/`
  and `terraform-modules/` in Stage 2.
- **All thirty-one decisions (D1-D31) are closed** — see [`plan/decisions/INDEX.md`](plan/decisions/INDEX.md).
- Inputs still needed from the user, neither blocking Stage 1: **which domain name to register**
  (D15, blocks Stage 7), and the AZ name-to-ID check in Stage 1b step 6, which decides whether Stage 3
  anchors subnets on list position or on AZ IDs.
- Integration risks worth settling earliest: **INT-11** (organization-wide RAM sharing + Lake Formation
  cross-account v3 — enabled in Stage 1b, consumed in Stage 5, and its absence makes a share fail
  *silently*) and **INT-13** (CodeConnections from the domain to the private GitLab — the one row with no
  convenience-preserving fallback).
- **2026-08-08: the plan was split** out of the two large files into `GENERAL_PLAN.md` (core + indexes)
  and `plan/`. Nothing about the plan's content changed in that split.

**Budget for this section: ~1 KB.** It states *state*, not reasoning. Reasoning belongs in the decision
file; narrative belongs in [`plan/history.md`](plan/history.md).

### Lessons carried forward

**Read [`plan/lessons.md`](plan/lessons.md) before planning, reviewing, or settling a decision.**
The fifteen titles are kept here so a lesson can be *recognised* without opening the file; the
reasoning that makes each one usable is in the file, and the titles alone are not a substitute.

1. **A copy of governed data landing somewhere less governed is not a hole to be closed.**
2. **A stand-in that shares an account with the thing it de-risks proves nothing about permissions.**
3. **When a decision moves a resource across an account boundary, re-check every condition that referenced it — especially conditions pointing at ephemeral things.**
4. **State that lives only inside an `[E]` resource is this design's recurring failure mode**
5. **An intention is not a control.**
6. **Prices are measured, not reasoned.**
7. **A rejected-on-cost option goes stale in the direction that flatters the rejection.**
8. **When the classic `aws` provider lacks a resource, check the CloudFormation registry and `awscc` before declaring a Terraform gap.**
9. **The axis question applies to people as well as to resources.**
10. **Before placing a new resource in an account, ask which axis it is on — and check whether a *registry* is being confused with a *runtime*.**
11. **A decision that changes *who authors* an IAM policy invalidates every claim made about that policy.**
12. **An edition or tier limit can reach a load-bearing control, not just a convenience.**
13. **A verification command that returns empty on both success and failure is not a verification.**
14. **A blanket carve-out written by hand across several policies is a control that will be missing from one of them.**
15. **Recommending against something is not the same as it being wrong, and the record should show which happened.**

