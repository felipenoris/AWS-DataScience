
# General Objective

The objective of this project is to create a Data Science environment base on AWS cloud infrastructure, using my personal AWS Account.

The goal is to achieve the following:

- All access from users to cloud infrastructure will be performed using a VPN.

- Use SageMaker as a development tool for Data Scientists.

- Use a DLP tool to protect data, targeting Sage Maker (mainly).

- SageMaker should have access to the internet. We'll explore implementing some restrictions, keeping the possibility of software updates, installing packages, and accessing a few websites.

- Use gitlab hosted at AWS for source-code control.

- use gitlab pages to host docs.

- use gitlab CI/CD to automate tests, docs and deployment.

- Use three kinds of CI/CD piplines:

	- pipeline to build a development environment: this will be the docker container (or image) used by developers on SageMaker.
	- pipeline to build an application: this should build a docker image of the app.
	- pipeline to deploy an application into production environment.

- Explore the possibility of deploying a workflow developed in SageMaker (Airflow/MWAA) to production.

- use a NFS solution to exchange files between users, SageMaker environment and S3 buckets.

- data-science assets and databases should not face the public internet. Later in the project we'll experiment setting up a web server facing the public internet, accessing a backend or database protected in the private subnet.

- Let's avoid using IAM Users, in favor of assuming IAM Roles temporarely.

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
├── terraform/ # use of predefined terraform modules hosted at `terraform-modules`
│   ├── main.tf
│   ├── variables.tf
│   └── envs/
├── pyproject.toml
└── README.md
```

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

- the file `secrets/accounts.md` contains AWS account information to use.

- All accounts will be registered under an AWS Organization managed by the `Management Account`.

- Accounts will be used to isolate environments: Sandbox, Production.

## Single-sign-on users (`secrets/sso-users.md`)

- Infrastructure user: user with Administrator permissions.

- Sandbox user: regular user, with no permissions to perform infrastructure change, except artifacts managed by AWS SageMaker. This user can write data, develop applications, and trigger CI/CD deploy pipelines to promote artifacts from Sandbox to Production environment.

## terraform

- All infrastructure code will be in terraform.

- Steps done manually by me will be recorded in the `LOG.md` file. Never update `LOG.md`. I'll edit this file.

- The `terraform` will have subfolders for each account (environment) controlled.

```
terraform-live/
├── sandbox/
│   ├── networking/
│   ├── shared-services/
│   └── app/
|        └── app-etl/ # references app-etl (an application) repository source code by tag version
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

Edit this section with your main ideas gathered in this project, so that your future-self will understand the context.

## Language

Use english when writing source code or any files in this repository.
When responding to chat, always write in Portuguese (Brazil).