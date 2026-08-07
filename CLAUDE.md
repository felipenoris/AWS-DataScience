
# General Objective

The objective of this project is to create a Data Science environment based on AWS cloud infrastructure, using my personal AWS account.

The goal is to achieve the following:

- All user access to the cloud infrastructure will be performed through a VPN.

- Use SageMaker as a development tool for Data Scientists.

- Use a DLP tool to protect data, targeting SageMaker (mainly).

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

## Language

Use English when writing source code or any files in this repository.
When responding in chat, always write in Portuguese (Brazil).

## git

Always commit changes to a separate branch with the `claude/` prefix. You can commit, push and open Pull Requests on GitHub. I'll merge them. After the merge, always synchronize the local folder with the upstream repo.

## Claude LOG

For every project step, review this section and add your own LOG, so that you can remember the current stage of this project.

### Stage 0 - Bootstrap not started (2026-08-07)

- The repository contains only documentation: `CLAUDE.md`, `LOG.md`, `README.md` (still the initial stub), `REFERENCES.md`, `LICENSE` and the git-ignored `secrets/` folder.
- The `terraform/` folder exists but is empty. No `terraform-live/` or `terraform-modules/` created yet. No AWS resource provisioned by code.
- Done manually by the user so far (per `LOG.md`): Management Account created in the AWS console; `aws` CLI and `terraform` installed locally.
- Accounts planned (`secrets/accounts.md`): Management (bootstrap only, never touched by code), Sandbox and Production.
- SSO users planned (`secrets/sso-users.md`): infrastructure (admin), sandbox (no infrastructure changes, except SageMaker-managed ones) and manager (approves deployments).
- Next step not decided yet. Natural candidate: bootstrap the AWS Organization (Sandbox and Production accounts + IAM Identity Center) and the Terraform remote state backend.

### Stage 0.1 - English review of the repository text (2026-08-07)

- Reviewed the English of `CLAUDE.md`, `README.md` and `REFERENCES.md`: spelling, capitalization of product names (GitLab, Docker, Terraform, SageMaker, AWS Lake Formation) and sentence-level grammar. No instruction changed its meaning.
- `LOG.md` and `secrets/` were left untouched, as required by the guidelines above.
