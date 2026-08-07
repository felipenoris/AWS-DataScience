
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

**Stage 0 (Baseline) is complete. Stage 1 (Organization, accounts and identity) is ready to start —
it is no longer blocked.**

The blockers were cleared on 2026-08-07: the region is `us-west-2` (D1), the six account e-mails are all
in `secrets/accounts.md`, the VPN is WireGuard (D4), the lab is ephemeral (D11), and Identity Center
administration is delegated to a dedicated Identity account (D10). Two decisions are deliberately deferred
to the stage that needs them: the SageMaker egress restriction mechanism (D5, Stage 6) and the production
orchestrator (D7, Stage 10). Neither blocks Stages 1-5.

State of the environment: nothing is provisioned in AWS beyond the manually created Management account.
The repository contains documentation only; `terraform/` is still empty and must be replaced by
`terraform-live/` and `terraform-modules/` in Stage 2.

### History

- **2026-08-07 - Stage 0.** Baseline recorded: Management account created manually by the user; `aws` CLI
  2.36, `terraform` 1.15 and `uv` installed locally; `~/.aws/config` has no SSO profile yet.
- **2026-08-07 - Stage 0.** English review of `CLAUDE.md`, `README.md` and `REFERENCES.md` (spelling,
  product-name capitalization, grammar). No instruction changed its meaning. PR #1, merged.
- **2026-08-07 - Stage 0.** `GENERAL_PLAN.md` created: stages 0-13 and decisions D1-D10. Six decisions were
  left open (region, VPN technology, SageMaker egress restriction, DLP approach, orchestrator, Identity
  Center administration); they are recorded there rather than here.
- **2026-08-07 - Stage 0.** Decisions taken by the user: region `us-west-2` (D1), WireGuard for the VPN
  (D4), native AWS combination for DLP (D6, now reflected in the four sub-items of the objective above),
  an ephemeral lab (D11) and a USD 50/month budget ceiling (D12). D5 and D7 deferred.
  The Log Archive and Audit account e-mails were added to `secrets/accounts.md`.
- **2026-08-07 - Stage 0.** D11 refined into a three-layer operating model in `GENERAL_PLAN.md` §5.1:
  `[P]` persistent (free at rest — including the VPC itself), `[D]` dormant (GitLab and WireGuard are
  stopped, not destroyed) and `[E]` ephemeral (NAT, VPC interface endpoints, SageMaker, EFS). The rule is
  "pay nothing while idle", not "destroy everything".
- **2026-08-07 - Stage 0.** Region settled: `us-west-2`, chosen on cost, and it stays there. Data residency
  is not a concern — this is a test with no real data. The project mirrors something that would run in
  `sa-east-1` in practice, but that move is **hypothetical and not planned work**: the only consequence is
  keeping region literals out of the Terraform (`GENERAL_PLAN.md` §4.1), which is good practice regardless.
  Recorded there for reference: São Paulo has every service this project needs, including SageMaker Studio
  GPU instances and Graviton — so the answer to "would anything break there?" is no.
- **2026-08-07 - Stage 0.** Number of AZs reviewed and **D9 kept as it was** (2 for subnets, 1 for metered
  endpoints). A third AZ buys nothing here: 2 already satisfies every managed service that requires
  multiple AZs (ALB, RDS Multi-AZ, EKS), and the lab has no availability requirement. Its only real
  argument is more chances of finding scarce GPU capacity (`ml.g5`, `p5`); against that, every per-AZ
  metered resource multiplies — six interface endpoints go from ~USD 0.06/h to ~USD 0.18/h. Open item
  recorded in `GENERAL_PLAN.md` §9: AWS maps AZ names to physical datacenters independently per account,
  so `us-west-2a` in Sandbox need not be the same datacenter as in Production. That is checked in Stage 1,
  once the accounts exist, and decides whether Stage 3 anchors subnets on list position or on AZ IDs.
- **2026-08-07 - Stage 0.** **D10 decided: Identity Center administration is delegated to a dedicated
  Identity account** (a sixth account, now in `secrets/accounts.md`). The instance itself cannot leave the
  Management account; only its administration is delegated, via
  `register-delegated-administrator --service-principal sso.amazonaws.com`. The point is that Terraform
  then manages permission sets without ever holding Management credentials, which is what turns
  "the Management account is bootstrap-only" into something enforced instead of merely intended.
  The user chose a dedicated account over the Audit account so that Audit stays the security guardian
  and Identity owns access management — I had recommended reusing Audit to avoid a sixth AWS Config
  recorder (~USD 0.50-1/month); the separation-of-duties argument won, and the cost is accepted.
  Three consequences carried into Stage 1: assignments *targeting* the Management account stay manual
  there; the Identity account is as sensitive as Management, so the Sandbox user gets no access to it;
  and Control Tower's own permission sets are left alone to avoid landing-zone drift.
