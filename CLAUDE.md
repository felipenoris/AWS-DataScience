
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

## Segregation by accounts

- The file `secrets/accounts.md` contains the AWS account information to use.

- All accounts will be registered under an AWS Organization managed by the `Management Account`.

- Accounts will be used to isolate environments: Sandbox and Production.

## Single-sign-on users (`secrets/sso-users.md`)

- Infrastructure user: user with Administrator permissions.

- Sandbox user: regular user, with no permissions to perform infrastructure changes, except for artifacts managed by AWS SageMaker. This user can write data, develop applications, and trigger CI/CD deploy pipelines to promote artifacts from the Sandbox to the Production environment.

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
nothing blocking it.** Decisions D1-D16 are closed and recorded in `GENERAL_PLAN.md` §4, with the single
exception of D7 (production orchestrator), deliberately deferred to Stage 10 because that is where it is
consumed. The six accounts in `secrets/accounts.md` are the complete set.

Two inputs are still needed from the user, neither blocking Stage 1: **which domain name to register**
(D15, blocks Stage 7) and the outcome of the AZ name-to-ID check in Stage 1 step 16, which decides whether
Stage 3 anchors subnets on list position or on AZ IDs. Both are tracked in `GENERAL_PLAN.md` §9.

State of the environment: nothing is provisioned in AWS beyond the manually created Management account.
The repository contains documentation only; `terraform/` is still empty and must be replaced by
`terraform-live/` and `terraform-modules/` in Stage 2.

### History

- **2026-08-07 - Stage 0 (complete).** Baseline recorded: Management account created manually by the user
  through the console; `aws` CLI 2.36, `terraform` 1.15 and `uv` installed locally; `~/.aws/config` still has
  no SSO profile. English review of `CLAUDE.md`, `README.md` and `REFERENCES.md` — PR #1, merged.
  `GENERAL_PLAN.md` written and then reviewed three times before any AWS resource existed. All of it landed
  in the plan itself, which is the single source of truth for stages 0-13, decisions D1-D16 and their
  rationale, the data perimeter (§4.2), the two egress designs (§4.3), the cost and operating model
  (§5/§5.1), the open questions (§9) and the lab-versus-institution delta (§11). The intermediate drafts
  were deleted from both histories on 2026-08-07: nothing had been provisioned, so they described only how
  the document changed, not how the environment did.
