# Runbook — a SageMaker application, from a Sandbox project to Production

| | |
|---|---|
| **Scope** | What a team does to build, test, release and operate an application on the `app-etl` template: the repository and its GitLab project, the manifest the CI/CD CLI reads, the image, the code a job and a worker run, the Glue jobs, the workflows, the tests at each rung, the pipeline job by job, the release through Staging into Production, the chains that start the workflows there, the readings, the application's data in each stage, and what Sandbox may read of Production. The platform under it is Stages 7 to 10's build; this file is what runs per application and per release |
| **Operator** | Three hands, named at each step. The **data scientist**, in a Sandbox project and in GitLab, a Developer of the project; the **deployment manager** (`awsds/deployment-managers`, a Maintainer of the project, `DeploymentManagerAccess` in AWS), who merges, tags, admits a release at the gates and approves a model; the **infrastructure user** (`InfrastructureAccess`, the `awsds-infra-*` profiles), who writes the application's infrastructure, applies the `[P]` slices and raises and lowers the shared slices. The **Governance Manager** approves a governed table's tags (§B). Which hand each act needs is §Q |
| **The rules** | **The repository is the deployable unit** (D41): the image carries the dependencies, the code is a job's input, the workflow is the activation, and a chain's state machine starts the workflow in each target. **The pipeline is the only writer of Staging and Production** (D17, D26): no project, no portal and no person deploys there, and no pipeline identity raises a shared slice (Stage 8 decision 27); a worker's rewrite of the code a deploy wrote is `TM-32`, open (Stage 19 decision 28). **Governed data is read through Lake Formation, never through S3** (D13): every project role carries `awsds-<env>-project-boundary`, a target's with the fence (Stage 19 decision 21 (b)), and release F's project roles hold no lake grant, the governed read being item 32 (Stage 19 decision 22 (a)). **A name is a contract**: the application's name reaches workflows, Glue jobs, prefixes, the stage-variables parameter, chains, repositories and instruments, each listed in §S |
| **The picture around it** | Why the unit is an application and why a chain layer exists: [D41](../decisions/D41-sagemaker-application.md); the deployment project in each target, the CLI's deploy there and the catalog's import: [Stage 19](../stages/stage-19-smus-native-data-product.md), decision 6 (b); what crosses the gate: [D28](../decisions/D28-workflow-contract.md); the template itself: [`examples/app-etl/README.md`](../../../examples/app-etl/README.md); the sittings that ran the first promotion: [`promotion.md`](promotion.md); a workflow's tasks inside a project: [`serverless-workflows.md`](serverless-workflows.md); GitLab's own procedures: [`gitlab.md`](gitlab.md); the governance cycle of a data product: [`docs/GOVERNANCE.md`](../../GOVERNANCE.md); every acronym: [`docs/GLOSSARY.md`](../../GLOSSARY.md) |
| **Written** | 2026-10-26, from the template at `v0.4.6` (promoted 2026-10-25, pipeline #102) and from the slices, scripts and stage records of Stages 8, 9 and 10. The targets' half read 2026-11-17 from the template at `v0.5.2` (release F, in Production since 2026-11-16, pipeline #129), `scripts/deploy-application.py` and the `<env>/studio/`, `<env>/foundation/` and `<env>/chains/` slices; where `main` carries release G's code (Stage 19 decision 26 (b), tagged `v0.6.0` at its sitting), the sentence says so. One application exists: every step here ran for `app-etl` unless it says otherwise, and no second application has been created, so §S's checklist is read from the code and not measured (Lesson 37) |

| Section | Audience | What it holds |
|---|---|---|
| [§A](#a-how-to-read-this-file) | both | how to read this file: the running example, the mental model, the vocabulary |
| [§O](#o-the-pieces) | both | the pieces: what an application is, where each piece lives in each stage, which identity runs it |
| [§Q](#q-who-does-what) | both | who does what: the acts of the data scientist, the deployment manager, the infrastructure user and the Governance Manager |
| [§R](#r-the-repository) | the data scientist | the repository: the layout, the name, the project files |
| [§L](#l-the-gitlab-project) | infrastructure | the GitLab project: protection, members, runners, the CI/CD variables, the mirror's allowlist |
| [§D](#d-the-development-cycle-in-sandbox) | the data scientist | the development cycle: a space, the deploy to `dev`, a run, the loop |
| [§E](#e-the-tests) | the data scientist | the tests: the ladder from the unit tests to Staging's leg, what each rung proves, how each kind of code is tested |
| [§M](#m-the-manifest-and-the-clis-stages) | the data scientist | the manifest and the CI/CD CLI: content, the catalog, workflows, the stages, the variables, what the CLI does and does not do |
| [§I](#i-the-image) | the data scientist | the image: `FROM` base by digest, the lock, the smoke target, when it is built |
| [§C](#c-the-code-a-job-and-a-worker-run) | the data scientist | the code: `src/` for the processing job, `code/` for the worker's tasks, the two contracts |
| [§G](#g-the-glue-jobs) | both | the Glue jobs: the script, the operator in every project, the governed read and write, the warehouse load |
| [§W](#w-the-workflows) | the data scientist | the workflows: the notation, the variables, the prefix classes, the rules the lint enforces, the result file |
| [§P](#p-the-pipeline-job-by-job) | both | the pipeline, job by job: stage, runner, rule, what it needs, what is set per application |
| [§T](#t-the-release-and-the-promotion) | both | the release and the promotion: the tag, what is raised first, the legs, the gates, the catalog's import |
| [§S](#s-the-infrastructure-a-new-application-needs) | infrastructure | the infrastructure a new application needs, slice by slice, and what is unmeasured |
| [§X](#x-operating-in-production) | both | operating in Production: the chains and their schedules, a run by hand, a pause, what must be up, a teardown, a rollback |
| [§V](#v-reading-a-run-back) | both | reading a run back: the log groups, the APIs, the failure rules, the instruments |
| [§B](#b-the-applications-data) | both | the application's data in each stage, and how a product reaches the lake and the warehouse |
| [§N](#n-what-the-application-reaches) | both | what the application reaches: Glue, Athena, Redshift, S3 and the lakes, per stage |
| [§K](#k-production-data-while-developing-in-sandbox) | the data scientist | Production data while developing in Sandbox: what the share admits, what never moves |
| [§Z](#z-standard-and-specific) | both | what every application shares, and what each one sets |

---

## A. How to read this file

**The running example.** Every section below uses the template application, `app-etl`, as its example,
so read its story once. A directory of CSV files holds trades: a date, a desk, an instrument, a quantity
and a price. The application's first workflow, `app-etl`, runs four tasks in order: a Glue job computes
each trade's notional (quantity times price) with Spark and writes one CSV; a SageMaker processing job
turns that CSV into a Parquet table and a JSON summary, running the application's own Python code in the
application's own container image; a small Python task on the workflow's worker reads the summaries and
builds the run's report; and an S3 task writes the report to the application's `outbox/` prefix. The
Glue job also writes the application's table and a training set, which a second workflow,
`app-etl-train`, trains an XGBoost model on and evaluates. A third workflow, `app-etl-warehouse`, loads
the application's table into the governed Redshift warehouse, in Production alone. Your application
will have other tasks and other data, and the same shape.

**The mental model.** An application is a git repository. It is deployed three times on the way to
Production, each time into a project, and the three deployments differ in three things: *where* it runs
(the `dev` project in Sandbox, then the deployment project `deploy-staging` in Staging, then
`deploy-production` in Production), *who runs the deploy* (the data scientist runs the CI/CD CLI from a
space into `dev`; the GitLab pipeline runs the same CLI as a deploy role into each target) and *as whom
it runs* (the role of the project it is deployed in). Everything else, the code, the image, the workflow
files, is the same bytes from the first deployment to the last: the pipeline promotes a release, it
never rebuilds one. Keep those three axes in mind and every table in this file is a row per axis.

**The vocabulary.** The words below recur in every section; each is defined here once, in the sense this
estate gives it, with the section that develops it.

| Word | What it means here |
|---|---|
| **application** | a repository holding `manifest.yaml`, the workflows and the code their tasks run; the unit that is deployed (D41). §R |
| **workflow** | an Amazon MWAA Serverless workflow: Apache Airflow run as a service, where a workflow is a YAML file naming tasks and the order between them, and AWS starts a small worker per task. There is no Airflow server to run or pay for at rest; a task bills while it runs. §W |
| **task, operator** | a task is one step of a workflow; its operator is the Airflow class that performs it. The operators here start a Glue job, start a SageMaker job, run a Python function or a shell command on the worker, or write an S3 object. §W |
| **the worker** | the small machine the workflow service starts per task (one vCPU, 3 GiB, Python 3.12, Airflow and boto3), with no internet. Python and Bash tasks run on it; a Glue or SageMaker task runs elsewhere and the worker only waits. §C |
| **XCom** | Airflow's channel between tasks: what a task returns, read by a later task's template. §C |
| **a Glue job** | AWS Glue, serverless Spark: the task kind that reads and writes governed data, since Lake Formation hands credentials to Glue and to no other engine here. §G |
| **a processing job, a training job** | SageMaker jobs: a container run on an instance SageMaker provisions, with inputs copied in before the command and outputs copied out after it; the container has no network. §C |
| **the CI/CD CLI** | `aws-smus-cicd-cli`, AWS's command-line tool for SageMaker Unified Studio: it reads the manifest, copies the application's files into a project and creates its workflows there; into a target it also imports the catalog the bundle carries. The data scientist runs it from a space into `dev`; the pipeline runs it as a deploy role into each target's deployment project, through `scripts/deploy-application.py` (Stage 19 decision 6 (b)), from the deploy image, which carries 1.0.9. The house image carries 1.0.9 in its own environment, which the template's `scripts/dev-cli.sh` runs by its path: up to the image's version 10 a space's `PATH` reaches the SageMaker Distribution's 1.0.8 first (§D). §M |
| **the manifest** | `manifest.yaml`, the CLI's description of the application: what to copy, the catalog to carry, which workflows to create, and the stages it deploys to, `dev`, `staging` and `prod`, each a project. §M |
| **the bundle** | the zip the CLI makes of the manifest's folders and of the `dev` project's catalog, the release's content; the CLI deploys the same zip into each target's deployment project. §M, §T |
| **a release** | a git tag `v<major>.<minor>.<patch>` on `main`; its pipeline builds the image, makes and stores the bundle and promotes it, the bundle's first run being Staging's leg (Stage 19 decision 19 (c)). §T |
| **the image** | the container the processing job runs in: the application's dependencies installed from the lock, and no code. §I |
| **tag and digest** | an image's tag is a name that could be moved; its digest is a hash of its content that cannot. Every pin here is by digest. §I |
| **a project** | a SageMaker Unified Studio project: a workspace with its own S3 prefix, its own IAM role, its own KMS key and its own network settings. In Sandbox a data scientist opens a notebook or a code editor in one (a *space*); Staging and Production each hold one deployment project, `deploy-staging` and `deploy-production`, which the pipeline deploys into (Stage 19 decision 6 (b)). §D, §O |
| **the project role** | `datazone_usr_role_<project>_<env>`, the IAM role every call from a project runs as, in every stage: a notebook's, a workflow's, a job's. §D |
| **the persona** | a person's AWS identity, an Identity Center permission set such as `DataScientistAccess` (Sandbox) or `DataScientistProdAccess` (Production), used from a laptop or the console. §Q |
| **the deploy roles** | the IAM roles the pipeline's jobs assume, one per account and purpose: `awsds-deploy-sandbox-test`, a member of the `dev` project, which makes the bundle and writes nothing; `awsds-deploy-staging` and `awsds-deploy-prod`, each an owner of its account's deployment project, which run the CLI's deploy there. They read the states the leg's scripts need and write none (`deploy-role-v0.5.0`). Only the deploy runner can assume them. §L, §P |
| **the job role** | `awsds-<env>-job-exec`, the role release T's Glue and SageMaker jobs ran as in Staging and Production. It keeps its Lake Formation grants, Production's write on `curated` alone, and Stage 9's producer proof runs as it; no template workflow does, since release F's jobs run as the project role. §G |
| **the execution role** | the role a workflow and its tasks run as: the role of the project the workflow is deployed in, in every stage. No workflow has a role of its own; release T's `awsds-<env>-wf-<key>` retired at Stage 19 item 31. §W, §X |
| **a permissions boundary** | an IAM ceiling attached to a role: whatever the role's policies allow, nothing beyond the boundary is granted. `awsds-<env>-project-boundary` caps every project role (D13); a target's carries the fence that closes the account's own buckets, keys, secrets and roles to the role (Stage 19 decision 21 (b)). §S |
| **a slice** | one Terraform root module with its own state, under `terraform-live/<account>/<slice>/`. An application has no slice of its own: its chains are entries of `<env>/chains/`, and the deployment project's grants are `<env>/studio/`'s and `<env>/foundation/`'s. §S |
| **`[P]`, `[D]`, `[E]`** | the three lifecycle layers of a slice (D11): permanent, applied by hand and never destroyed; a `[D]` host, stopped between sittings; ephemeral, destroyed between sittings so that nothing bills at rest. `make up` and `make down` raise and destroy the `[E]` slices of an account. §T, §X |
| **a sitting** | a working session in which the infrastructure user raises what a task needs, runs it and takes everything down again. §T |
| **the hub, the proxy, the endpoints** | the estate reaches the internet through one proxy in Production's `VPC-Networking` (the hub), and reaches AWS's own APIs through VPC interface endpoints inside each VPC. A job's or a worker's network has no internet route at all: it reaches an AWS API only through an endpoint its account's `egress/` slice holds, and those endpoints are `[E]`. §X |
| **the lake, Lake Formation, a share** | the governed data lives in the Data Governance account, in S3 buckets catalogued in its Glue Data Catalog. Lake Formation is the permission layer over that catalog: a consumer account receives a *share* (a grant on the account), its administrator *re-grants* it to a local role, and a query engine asks Lake Formation for short-lived credentials per table. The share is written over tags (`layer`, `classification`), not table names: tag-based access control, TBAC. §B |
| **a resource link** | a local catalog entry that points at a shared database in another account's catalog, so a query can name it. §B |
| **the outputs bucket** | `awsds-<env>-outputs`, each deployment account's own S3 bucket, under the account's data key; not the lake. It holds release T's objects and Stage 9's proof scripts; release F writes under its project's prefix of `awsds-<env>-smus-projects`. §B |
| **a chain** | in Staging and Production, the pair that starts a workflow: a Step Functions state machine, which finds the workflow by its name, starts its run with the stage variables the last deploy recorded and waits for it, and an EventBridge Scheduler schedule, which starts the machine on a cron. The workflow itself carries no schedule. `<env>/chains/` declares both (`orchestration-v0.3.1`). §X |
| **the lint** | `awsds-workflows lint`, the offline check of the manifest and the workflows against the rules of this estate; it runs in the pipeline's `test` job on every push, a tag's included. §W |
| **a dotenv report** | a GitLab mechanism by which a job hands values (an image digest, a SHA256) to later jobs of the same pipeline. §P |

---

## O. The pieces

An application is a GitLab repository on the `app-etl` template: `manifest.yaml`, one YAML per workflow
in the CI/CD CLI's notation, and the code the workflows' tasks run. It is deployed three times on the
way to Production, once per account and each time into a project, and the first table below is the map
of those deployments along the three axes of §A: where, by what, as whom. The `dev` project is in the
Sandbox account, where people work; Staging and Production are accounts where only the pipeline writes
and only workflows run, each holding one deployment project that the CLI deploys into as it does into
`dev` ([Stage 19](../stages/stage-19-smus-native-data-product.md) decision 6 (b); release F, `v0.5.2`,
in Production since 2026-11-16). Every promotion crosses an account: there is no Sandbox `test` stage
(decision 19 (c)), and the release's first run is Staging's leg.

| Stage | Where it runs | Deployed by | Identity of the tasks | Data |
|---|---|---|---|---|
| `dev` | `app-etl-dev`, a Sandbox project for the application alone (Stage 19 decision 18 (d)) | the CI/CD CLI (`aws-smus-cicd-cli` 1.0.9, the house image's, through `scripts/dev-cli.sh`), from a space, while the application is engineered (§D). The tag pipeline's `bundle` job names this project and deploys nothing | the project role, `datazone_usr_role_<project>_<env>` | the project's `shared/<app>/` prefix under the project key |
| Staging | `deploy-staging`, the Staging account's deployment project | the CLI, run by the pipeline's `staging-deploy` and `staging-catalog` as `awsds-deploy-staging`, from the release's bundle | the project role, `datazone_usr_role_5ido8bej1zoeq8_d6nu5aphq1e974`, on the worker and in every job | the project's `shared/<app>/` prefix of `awsds-staging-smus-projects` under the project key, and its database `app_etl`; nothing of the lake (Stage 19 decision 22 (a)) |
| Production | `deploy-production`, the Production account's deployment project, in `VPC-Workloads` | the CLI, run by the pipeline's `production-deploy` and `production-catalog` as `awsds-deploy-prod`, after two manual gates | the project role, `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow` | the project's `shared/<app>/` prefix of `awsds-prod-smus-projects` under the project key, and its database `app_etl`, whose product table the workflow lists in the catalog; the governed warehouse; nothing of the lake (decision 22 (a)) |

The second table says what each stage holds for one application, and the names each piece carries.
Read it as a dictionary: when a later section names `app_etl_deploy_production_app_etl`, this is where
the name's pattern is.

| Piece | In `dev` | In Staging and Production |
|---|---|---|
| the workflow | `<app>_<project>_<workflow>`, every character outside `[A-Za-z0-9_]` turned into `_`, created by the CLI's `workflow.create` with the project role, the Tooling subnets, the project's group and key, tagged `CreatedBy=SMUS-CICD` and `Pipeline=<app>` | the same rule in the deployment project, `app_etl_deploy_staging_app_etl` for instance, created by the stage's bootstrap with that project's role, Tooling subnets, group and key |
| the execution role | the project role | the deployment project's role, under `awsds-<env>-project-boundary` with the fence (Stage 19 decision 21 (b)); `<env>/studio/workflows.tf` adds what its jobs need, and it holds nothing of the lake |
| the log group | `/aws/mwaa-serverless/<domain>-<project>/<name>`, under the project key, no retention | the same name, no retention (`EXC-25`, until Stage 19 decision 27 (d)'s account-level policy, which waits on the AWS provider) |
| the Glue job | `<app>-{proj.id}`, created and updated by the task itself from `create_job_kwargs` | the same: `app-etl-<project id>`, and in Production `app-etl-load-<project id>` of `app-etl-warehouse`, each on the project role and the project's two Glue network connections |
| a SageMaker job | the project role, the project's subnets, group and key, the application image by digest from Production's registry | the same, with the deployment project's role, subnets, group and key |
| the definitions and the code | `shared/<app>/{workflows,src,glue,code}/`, written by the CLI's `deploy` | the same prefixes of the deployment project, written by the CLI's `deploy` from the bundle; the project role the workers run as can overwrite and delete `glue/`, `src/` and `workflows/`, another application's included (`TM-32`, open: Stage 19 decision 28) |
| the stage's variables | filled by the CLI on each run it starts | `/datascience/<env>/applications/<app>/stage-variables`, written by `deploy-application.py` after each deploy and read by each chain's machine (Stage 19 decision 23 (a)) |
| the inbox and the results | `shared/<app>/inbox/`, `work/`, `outbox/`, `tables/`, `models/`; the product table in the project's database `app_etl` | the same, in the deployment project |
| what starts a run | the CLI's `run`; never the portal, whose run carries no stage variable and fails at the template (§D) | a chain: the Step Functions machine `awsds-<env>-chain-<key>`, started by its EventBridge Scheduler schedule, by the Staging leg or by a person (§X); in Production also the `prod` stage's bootstrap, which runs `app-etl` at each deploy |
| the alert on a failure | none | the rules `awsds-<env>-wf-<app>-<workflow>-failed` and `awsds-<env>-chain-<key>-failed`, mailing `awsds-<env>-alerts` |

**What a release is made of.** D28 names the artifact classes that may cross into a deployment account,
and a release is three objects, one per class: the image in `awsds-prod-ecr-<app>` as
`v<semver>-<short sha>`, read by digest; the bundle, the CLI's zip of the manifest's folders, in
`s3://awsds-prod-releases/<app>/<tag>/<app>.zip`, read against its SHA256; and the tag's GitLab release,
whose notes name both. What a target runs persists in the target: nothing of the application is `[E]`,
the definitions and the code stay under the deployment project's prefix between sittings, and each
deploy records the stage's variables, the image's digest among them, in the parameter every chain run
reads (Stage 19 decision 23 (a)). Release T's record, a `release.tf` per account, retired at item 31,
and with it the code tree `applications/<app>/<tag>/`, whose writes were denied to all but the
release's role and `InfrastructureAccess` (Stage 10 decision 12); release F's code is the deploy's sync
into `shared/`, which the project role can rewrite, read by simulation 2026-11-17 (`TM-32`, Stage 19
decision 28, the user's).

---

## Q. Who does what

The acts are split between hands on purpose, and the split is the control: the person who writes the
code never deploys it into Production by hand, the person who approves a release is not the one who
tagged it in a hurry, and the identity that can change the account's permissions is not the one a
pipeline runs as. Every refusal a person meets while doing someone else's act is the design working,
and its wording is the reading to keep.

| Act | Data scientist | Deployment manager | Infrastructure user | Governance Manager |
|---|---|---|---|---|
| write the application, its tests, its workflows and its manifest; push a branch; open a merge request | yes | | | |
| run the tests, the lint and the gates on a branch | yes, on the laptop, in a space and on the test runner | | | |
| deploy to `dev` and run it there, as the project role | yes (§D) | | | |
| merge into `main` | | yes, as a Maintainer (`main` is protected) | | |
| create the release tag `v<semver>` (the release gate, Stage 8 2.1) | | yes, as a Maintainer | | |
| admit a release into Staging (`staging-gate`) and into Production (`production-gate`) | | yes, with the Staging leg's artifacts and `production-check`'s reading of Production's project in front of them (the jobs' artifacts, which GitLab serves; no S3 read, Stage 8 3.9) | | |
| register and approve a model version (`production-register`, `production-approve`) | | yes | | |
| raise and lower the hub, GitLab, the runners, Sandbox's and Staging's `egress/`, Production's `workloads-egress/` and the warehouse compute | | | yes, with `make` | |
| create the GitLab project, its runners and its CI/CD variables (§L) | | | yes, as GitLab's local administrator, with the slices' outputs | |
| write and apply the application's infrastructure (§S) | | | yes | |
| push the infrastructure repository's mirror to GitLab, which every leg clones at its default branch (§T) | | | yes | |
| declare a governed table and its tags in the register before the first write (§B) | proposes the schema and the classification in a merge request | | applies, inside `DL-5`'s bracket | approves the classification |
| start a Production chain by hand, pause or resume a schedule (§X) | | | yes | |
| read a Production run: the executions, the workflow runs, the task instances | no: a persona's start or read is refused (Stage 10 6.2) | the run status, the executions and the schedules (Stage 10 decision 11); no S3 object (D31) | yes | |
| read the application's result in Production | the lake's `public` and `internal` tables through Athena, from any network (Stage 9 5.1, D39); the product table through a subscription to its listing (Stage 19 4.12, not run). The persona's S3 read names `awsds-prod-outputs/app-etl/outbox/` alone (`production/data/persona.tf`), which release F does not write: its result file is under `deploy-production`'s prefix of `awsds-prod-smus-projects` | | yes | |
| read Staging | the catalog, nothing writable (Stage 9 8.4) | | yes | |

What no hand does: deploy into Staging or Production outside the pipeline, start a workflow in Production
from a portal, write governed data from Sandbox, or raise a shared slice from a pipeline job.

---

## R. The repository

The repository is laid out so that each folder maps to one place the code will run, and the manifest
and the pipeline read the folders by path: a file in the wrong folder is not copied or not zipped, and
the failure shows at the first deploy. The layout is
`docs/plan/conventions.md`'s "Application repository layout", and the template is
[`examples/app-etl/`](../../../examples/app-etl/README.md):

```
<app>/
├── src/<package>/     # the processing job's code: the job reads it as its input, never from the image (D28 class 2d)
│   ├── __main__.py    # the command, python -m <package>
│   └── pipeline.py    # the transformation
├── code/<tasks>.py    # the worker's Python tasks; the pipeline zips it as code/<workflow>.zip per workflow (class 2b)
├── glue/<script>.py   # one script per Glue job (class 2c)
├── workflows/<workflow>.yaml   # one definition per workflow, in the CLI's notation
├── manifest.yaml      # the application: its content, the folders the CLI copies, its stages
├── scripts/dev-cli.sh # the CI/CD CLI for the dev stage in a space (§D); no storage item names it, so it is never bundled
├── Dockerfile         # the application image and the job image: the lock's dependencies, no code
├── tests/             # pytest, offline (§E)
├── samples/           # synthetic input: the smoke build, the tests, a `dev` run and the inbox seed read it
├── warehouse/<table>.sql       # a warehouse table's DDL, when the application loads the governed warehouse
├── .gitlab-ci.yml     # the pipeline, with the shared gates of awsds/ci-gates
├── pyproject.toml, uv.lock, .python-version, .gitignore, README.md
```

Three folders hold code, and each is run by a different machine: `src/` by the processing job's
container (§C), `code/` by the workflow's worker (§C), `glue/` by Glue's Spark workers (§G). The
`workflows/` folder is the *activation*, what starts that code and in which order (§W); the rest is
*content*. `samples/` is a synthetic input that every automated test reads, so that no real data
enters the repository or a test.

**The name.** `<app>` is lowercase letters, digits and hyphens, and it travels: the GitLab project
`awsds/<app>`, the repository `awsds-prod-ecr-<app>`, the workflows `<app>` and `<app>-<suffix>` and the
names the CLI composes from them, the Glue jobs `<app>-<project id>`, the prefix `shared/<app>/` of every
project, the parameter `/datascience/<env>/applications/<app>/stage-variables`, the chains
`awsds-<env>-chain-<key>`, the model package group `awsds-prod-model-<app>`, the bundle's key in the
release store. Choose it once, since every grant in §S names it. A workflow's name and its `dag_id` hold the same characters: the CLI turns every other
character into `_` at creation but maps only `-` when `run` and `destroy` look the workflow up, so a name
with any other character is created under one name and found under none. Both are unique across the
applications a project holds, since `workflow.create` scans the project's whole shared root and the
first file in listing order wins a name or a `dag_id` (Stage 18's reading); a deployment project holds
every application of its target (§S). A Glue job's name ends with `-{proj.id}`: the project role's
`GetAGlueJobNoProjectHolds` admits `glue:GetJob` on `*-<project id>` alone (`sandbox/workflows/`,
`<env>/studio/workflows.tf`). A processing job's name, `<app>-<timestamp>`, stays under SageMaker's 63
characters.

**The project files.** `pyproject.toml` pins `requires-python` to the interpreter the image runs, base's
CPython 3.12, and lists the runtime dependencies alone under `dependencies`; the tools (`pytest`, `ruff`,
`pdoc`) sit in the `dev` group, which the image and the `pip-audit` gate leave out, so a test tool's
vulnerability never blocks a release and never ships in the image. `exclude-newer` holds the resolver
two weeks behind PyPI, the delay the infrastructure repository gives everything it pins, so that a
package published yesterday cannot reach the image before anyone has looked at it; it moves forward in
the same commit as `uv lock --upgrade`. `uv.lock` is what the image installs (`--locked`): a
`pyproject.toml` change without a new lock fails `test` at `uv sync --locked`.

**What a template change is.** `examples/app-etl/` in the infrastructure repository is the template's
source; a change reaches `awsds/app-etl` by the merge-request procedure of [`gitlab.md`](gitlab.md)
"The application template" (a fresh clone, the files swapped through `git archive`, a branch, the merge
request). A new application starts as a copy of the template with its name replaced, and keeps the
template's shape: §Z says which lines it changes.

---

## L. The GitLab project

GitLab holds the code, runs the pipeline and is where a release is gated. Three ideas carry the
section. A *protected* branch or tag is one only Maintainers may push or create, and GitLab marks a
pipeline as protected or not from the moment it is created. A *runner* is a machine that executes
pipeline jobs; a protected runner serves protected refs alone, so the only way for code to reach an AWS
identity is to be on `main` or on a release tag, which a Maintainer put there. A *CI/CD variable* is a
value GitLab injects into a job's environment; a protected one reaches protected pipelines alone.

The infrastructure user creates `awsds/<app>` as GitLab's local administrator, and every setting below
is a control (the runners' half is [`gitlab.md`](gitlab.md) §K, the gates' §G, the mirror's §M):

1. **The project**: group `awsds` → **New project → Create blank project**, visibility **Private**, no
   README. The first push brings the template's tree.
2. **Protection**: **Settings → Repository → Protected branches**, `main`, push and merge
   **Maintainers**; **Protected tags**, `v*`, create **Maintainers**. The protected tag is the whole of
   the release gate in GitLab CE: whoever may create it may release, and the build and deploy runners
   serve protected refs alone, so an unprotected branch's pipeline reaches no AWS identity. The
   protection is verified by a Developer's attempt to tag, never by reading the setting (Stage 8 1.0).
3. **Members**: `awsds/data-scientists` as **Developer**, `awsds/deployment-managers` as **Maintainer**
   (Stage 8 2.1). A pipeline that includes `awsds/ci-gates` runs with the permissions of whoever started
   it, so every member is a Reporter of the gates project too.
4. **The runners**: three machines, each with one reason to exist. The test runner (tag `awsds-test`)
   serves any branch, so it holds no AWS identity at all: whoever can push a branch can run code on it.
   The build runner (untagged, protected) holds the role that pushes images, and takes `build-image`,
   `scan-gate`, `store-bundle`, `release` and the two gates. The deploy runner (tag `awsds-deploy`,
   protected) is the only machine that can assume the deploy roles, and takes `bundle` and the
   promotion legs. The three are project runners of `awsds/app-etl`, linked to the other projects they
   serve and locked (`gitlab.md` §K); a new project is linked to each from the runner's edit page,
   **Other available project runners → Link**, after an administrator unlocks it for the link and locks
   it again.
5. **The CI/CD variables**, **Settings → CI/CD → Variables**, each protected. `bundle` reads these and
   fails naming any that is empty. They name the domain and the `dev` project to the CLI, values the
   repository must not carry because they are an account's:

   | Variable | Value, and where it is read |
   |---|---|
   | `DOMAIN_ID`, `DOMAIN_REGION` | the SageMaker Unified Studio domain's id and Region: `awsds-workflows values` prints the id (`serverless-workflows.md` §T). The promotion legs read `DOMAIN_REGION` too |
   | `DEV_PROJECT_NAME` | the `dev` project's name, of which `awsds-deploy-sandbox-test` is a member |

   The CLI refuses a manifest with any `${VAR}` unset, so `bundle` gives every other name the manifest
   reads the placeholder `unused-by-bundle`: the `dev` stage's network, key and account are a space's
   exports (§D step 3), and a target's are read from its project by `deploy-application.py` (§T). Read
   2026-11-15 through the API, the project held nine variables, each protected and unmasked: the three
   above, `ECR_REGISTRY`, and `SUBNET_AZ1`, `SUBNET_AZ2`, `DEV_PROJECT_SG`, `DEV_PROJECT_KEY_ARN` and
   `TRAINING_IMAGE_URI`, which no job reads and which may stay or go (`promotion.md` §N.8.2 step 0). The
   `test` project's four `TEST_PROJECT_*` were removed that day.

   The rest of what a job reads arrives otherwise: `IMAGE_REPO`, `AWSDS_WORKFLOWS`, `LINT_INSTANCE_TYPES`
   and `LINT_ALGORITHM_REPOSITORIES` are the file's own; `JOB_IMAGE_URI`, `SCAN_DIGEST`, `BUNDLE_SHA256`,
   `BUNDLE_OBJECT` and `MODEL_PACKAGE_ARN` are earlier jobs' dotenv reports; `ECR_REGISTRY`, the proxy
   variables, the CA root at `/etc/gitlab-runner/certs/ca.crt` and the deploy profiles are the runners'.
6. **The mirror's allowlist**: the infrastructure repository lives on GitHub, and GitLab holds a copy of
   it, `awsds/infrastructure`, because the promotion jobs run its scripts (`check-egress.py`,
   `deploy-application.py`, `model-chain.py`) and a runner inside the VPN reaches GitLab, not GitHub. Each promotion job clones the mirror with its job
   token, so `awsds/infrastructure` → **Settings → CI/CD → Job token permissions** must admit the new
   project.
7. **Pages** needs no setting: the `pages` job on `main` publishes `public/` under the project's own name
   below `awsds-pages.internal`, shown under **Deploy → Pages**, reachable through the VPN.
8. **An accepted finding** of `pip-audit` is a line in `awsds/ci-gates`'s `baselines.gitlab-ci.yml`, in
   a list keyed by the project's path, and a new `gates-v*` tag (`gitlab.md` §G); the image's scan
   baseline is the Distribution lineage's, shared by every `awsds-prod-ecr-app-*`.

---

## D. The development cycle in Sandbox

A data scientist works in a *space*, a JupyterLab or Code Editor instance inside the Sandbox project
that is the manifest's `dev` stage, on the house image (`awsds-sandbox-dev-env` version 11, `default-v0.10.0`,
the only version since 2026-11-03).
The space's `~/shared/` folder is the project's `shared/` S3 prefix, its house environment carries the
CI/CD CLI (Stage 8 decision 22), and every command it runs holds the project role's credentials. The
loop below ran end to end from a space on 2026-10-26 ([`promotion.md`](promotion.md) §N.3, Stage 10
2.1). Steps 1 and 6 carry what the image and the CLI do not yet do for the developer: git's credential
helpers, and the CLI's domain lookup, which the template's `scripts/dev-cli.sh` answers. Step 4, the MWAA
Serverless API's name in `NO_PROXY`, is what version 11 carries.

**The session is the infrastructure user's.** `make hub-up`; `make gitlab-up RUNNERS=0` while the
checkout is cloned or pushed; and Sandbox's endpoints with the MWAA Serverless group:

```bash
make up ENV=sandbox ONLY=egress GROUPS=mwaa
```

The MWAA Serverless API's only name is `airflow-serverless.<region>.api.aws`, which the proxy refuses to
the compute plane, so without the `mwaa` group's endpoint (`vpc-egress-v0.19.0`) every CLI call to the
service from a space reaches the proxy and is refused: `CreateWorkflow` read *"Failed to connect to proxy
URL"* on 2026-10-26, botocore's report of the proxy's `403 TCP_DENIED`. A run's own tasks need no group.
**The portal starts a space's app whenever one of the project's pages is open**, so every portal tab is
closed before `make down ENV=sandbox`, whose hook deletes the running apps: on 2026-10-26 the portal
re-created both projects' apps three minutes after the hook had deleted them, and an app it is starting
refuses the delete (*"State transition from [PendingCheckout] to [Deleting] is not allowed"*) until it
settles, so the down runs again.

1. **The checkout.** The persona signs in to GitLab through SAML, which hands `git` no credential, and
   creates a personal access token (*Edit profile → Access tokens*, the scopes `read_repository` and
   `write_repository`, the shortest expiry the work allows), typed at git's prompt and nowhere else. The
   space's `~/.gitconfig` names the CodeCommit credential helper for every host (`credential.helper !aws
   codecommit credential-helper --ignore-host-check $@`), whose credential GitLab refuses with *"HTTP
   Basic: Access denied"* before git would prompt, so each command resets the helper list for itself:

   ```bash
   git -c credential.helper= -c credential.helper='cache --timeout=3600' clone https://gitlab.awsds.internal/awsds/<app>.git
   ```

   The cache holds the token in memory for an hour, for the pushes that follow with the same two `-c`
   options. The clone travels the `Sandbox ↔ VPC-SharedServices` peering, never the proxy (INT-09), and
   needs the internal CA's root, which the house image's base installs and AWS's SageMaker Distribution
   cannot carry: a space without it stops at *"server certificate verification failed"*.
   With GitLab down, the application reaches the space as a tar dropped on its file browser (Stage 19
   pass 1, 2026-11-10). A tar built on a Mac takes `COPYFILE_DISABLE=1 tar --no-xattrs --no-acls
   --no-mac-metadata -c -f <file> <folder>`; otherwise macOS's `tar` adds an AppleDouble member (`._*`)
   per file, its own `tar -t` lists none of them, the space's `tar` extracts them, and the deploy uploads
   them to the shared root, where they stay (`SUP-348`). Python's `tarfile` lists every member.
2. **The tests and the lint**, §E's first two rungs, in the space or on the laptop.
3. **The values the manifest reads** (§M). The CLI refuses to load a manifest whose `${VAR}` is unset or
   empty, the stage the command does not target included. The project's own values come from its Tooling
   environment, read in the space by the `awsds-workflows` package's script, cloned rather than installed
   ([`serverless-workflows.md`](serverless-workflows.md) §T); `JOB_IMAGE_URI` is the image the last
   release's notes name, by digest, whose registry host carries Production's account id, typed and never
   written down; a name neither the deploy nor the run reads gets a placeholder:

   ```bash
   git clone --depth 1 https://github.com/felipenoris/awsds-workflows /tmp/awsds-workflows
   /opt/conda/bin/python /tmp/awsds-workflows/scripts/space_values.py > /tmp/space_values.json
   eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); k = "arn:aws:kms:%s:%s:key/%s" % (v["REGION"], v["ACCOUNT_ID"], v["PROJECT_KEY_ID"]); print("\n".join("export %s=%s" % p for p in (("DOMAIN_ID", v["DOMAIN_ID"]), ("DOMAIN_REGION", v["REGION"]), ("SUBNET_AZ1", v["SUBNET_AZ1"]), ("SUBNET_AZ2", v["SUBNET_AZ2"]), ("DEV_PROJECT_SG", v["PROJECT_SG"]), ("DEV_PROJECT_KEY_ARN", k))))')"
   export DEV_PROJECT_NAME=<dev project>
   export JOB_IMAGE_URI="<the release's image by digest>" TRAINING_IMAGE_URI="<the XGBoost image by digest, or unused-by-<app> when no run reads it>"
   export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
   ```

4. **The API's name in `NO_PROXY`**: version 11, `default-v0.10.0` (2026-10-26), carries it, and a space
   on it needs no export, read from a space at [`promotion.md`](promotion.md) §N.7.3. Versions 7 to 10
   lacked it and were deleted on 2026-11-03 ([`dev-env.md`](dev-env.md) §B); the export below is for a
   space on another image. Without the name boto3 sends the call to the proxy, which refuses it, even with
   the endpoint up. `getent hosts` answers the endpoint's `10.20.x` address:

   ```bash
   export NO_PROXY="$NO_PROXY,airflow-serverless.us-west-2.api.aws" no_proxy="$no_proxy,airflow-serverless.us-west-2.api.aws"
   ```

5. **The worker's packages.** The CLI copies files and builds nothing, so the zip a Python task runs from
   is built first, one per workflow the manifest names with a `code` field:

   ```bash
   python3 -m zipfile -c code/<workflow>.zip code/<tasks>.py
   ```

6. **The deploy to `dev`.** "Deploy", for the CLI, means two things: copy the manifest's folders under the
   project's `shared/<app>/`, and create (or update) each workflow the manifest's `bootstrap` names, with
   the project's network and key. It runs none. The command is the template's `scripts/dev-cli.sh`, which
   passes every argument to the CLI and answers two things for it. The CLI is the house image's, run by
   its path (`$AWSDS_PYTHON_ENV/bin/python`): the SageMaker Distribution's own `aws-smus-cicd-cli`, 1.0.8,
   comes first on the space's `PATH` and refuses the manifest's `code` field (*"Additional properties are
   not allowed ('code' was unexpected)"*). And the CLI 1.0.9 looks the domain up by name with
   `ListDomains` on every deploy with bootstrap actions, the manifest's id notwithstanding, which DataZone
   refuses to a project's role (*"User is not permitted to perform operation: ListDomains"*) though its
   IAM policy allows `datazone:List*`. The deploy roles' call returns the domain: the legs' deploys
   create their workflows through the same lookup (§T). The script answers the lookup with the
   manifest's `DOMAIN_ID` for each of its callers, and every other call is the CLI's own:

   ```bash
   scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
   ```

   Its first line names the CLI's version and interpreter, and it refuses to start, naming the variable,
   when `AWSDS_PYTHON_ENV` (a space on another image) or `DOMAIN_ID` (step 3 not run) is unset. From the
   house image `default-v0.10.0`, Sandbox's version 11 since 2026-10-26, the name `aws-smus-cicd-cli` is the house's too, through the base
   environment's activation hook (Stage 8 decision 22), and the script stays for the lookup until a CLI
   release takes the manifest's id ([issue 413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413), opened 2026-10-26).
   `--skip-validation` because the CLI's pre-deployment validation simulates the IAM calls without their
   context keys and reads every conditioned SCP as a deny (a failure of the tool, not of the estate,
   Lesson 30); `--no-events` because the event it would publish has no handler in 1.0.9. The refusal of
   `GetGroupProfile` it prints at each storage item, by the domain's resource policy, changes nothing.
   Which identity runs it is Stage 8 decision 22: from a space as the project
   role, the identity the project's grants are written for (`sandbox/workflows/`,
   [`serverless-workflows.md`](serverless-workflows.md) §G), so no person gains a grant; the lab's first
   deploy ran from the laptop as the infrastructure user on 2026-10-15, where the CLI's boto3 reads no
   credential the `aws` CLI cached, so `aws configure export-credentials` or a fresh login precedes it.
   The deploying identity is a member of the project: for a non-member the CLI omits the network and the
   key and creates the workflow in the service's own network, printing one line, which is the quiet
   failure to watch for. A deploy that stops after the copy leaves the copied files, which the next
   deploy syncs over, and its operator zips under `shared/operatorFiles/`, which nothing prunes.
7. **A run**, with the same script and `run`:

   ```bash
   scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow <workflow>
   ```

   `run` returns once the service accepts the start and prints the run id, after refusals of
   `ListTagsForResource` on other projects' workflows that change nothing; `get-workflow-run` and
   `list-task-instances` follow it (§V). The CLI fills each `{env.VAR}` of the workflow as the run's
   `OverrideParameters`, from the stage's `environment_variables`. A workflow the CLI made is read in the
   portal and never saved or run there: a run started from the portal carries the service's own
   `mwaa_serverless_workflow_id` alone and fails before any task, *"User template error: DAG template
   rendering failed: 'dict object' has no attribute 'SUBNET_AZ1'"* (Stage 10 xxix), and a save replaces
   the definition whole (`serverless-workflows.md` §A).
8. **A change**: to the code in `src/`, `code/` or `glue/`, or to a workflow, is steps 5 and 6 again,
   since the job reads the code as its input and the operator updates the Glue job from the definition
   (`update_config: true`); the image does not change, which is the point of keeping the code out of it
   (§I). `deploy` syncs without deleting, so a file a change removed stays in the prefix until it is
   emptied by hand (`aws s3 rm --recursive` on `shared/<app>/`). A change to a
   dependency is a new lock and a new release: the image is built by the tag pipeline alone, so a
   processing task has no image to run on until the first tag has pushed one. A workflow with Glue and
   worker tasks alone needs no image.
9. **The merge request**, pushed with step 1's options, whose branch pipeline runs `test`, Secret Detection
   and `pip-audit` on the test runner; a Maintainer merges, and `main`'s pipeline adds `pages`. Then the tag
   (§T). The token is revoked when the work ends (*Access tokens → Revoke*).

**What the project gives, and what it does not.** The project role runs every task, inside the project's
network and under the project key, with the D13 boundary on every job: `NetworkConfig` with the two
private subnets and the project's group, `EnableNetworkIsolation` on every job but a processing job
(Stage 20 decision 13, applied 2026-11-17), inter-container encryption, the project key on the volume
and the output, an instance type inside the ceiling. These are the same
settings a job needs in Production, which is why a workflow written here runs there unchanged. The
operator's first describe of a job name needs the grant `sandbox/workflows/` holds for the project role,
once per project and planned after the project exists, since the slice reads its role (§S; §G of
`serverless-workflows.md`). The application's projects, `app-etl-dev` and the
two deployment projects, hold no Lake Formation grant on the governed lake, so the application reads
its inbox in every stage (Stage 19 decision 22 (a)); the governed read is item 32, measured first in
`dev` (§G, §K). Each deploy spends one of the
workflow's 50 versions (read 2026-10-26: `eighth-experimentation`'s `app-etl` at 1, and the retired `test` stage's at 12).

**Cost of the loop**: a worker task bills 0.088 USD per task-hour with a one-minute minimum, a processing
task holds its worker for its whole job, and a Glue job bills its workers per DPU-hour; `app-etl`'s run of
2026-10-26 took 11 min 34 s, the Glue job 66 s on two G.1X workers and the processing job 5 min 21 s on
`ml.t3.medium`. Sandbox's `egress/` must be up for a run (eighteen endpoints, 0.180 USD/h, and 0.010 for
the `mwaa` group's one), and the space itself bills while it runs (0.050 USD/h on `ml.t3.medium`, 0.100
on `ml.t3.large`).

---

## E. The tests

An application is tested on a ladder whose rungs cost more and prove more. The lower rungs run in
seconds on a laptop with nothing of AWS; the higher ones need accounts, roles and real data, and the
pipeline runs them where a person cannot skip them. What a rung cannot see is the next rung's: a unit
test cannot tell whether a project role may write a table, and Staging's leg is the first place the
release runs under a target's grants.

| Rung | Runs | On synthetic data | Proves | Cannot see |
|---|---|---|---|---|
| the unit tests, `tests/` | `uv run pytest` on the laptop, in a space, and in `test` on every push | yes, `samples/` and fabricated inputs | the transformation, the worker's callables, the Glue script's reads, writes and the governed query it builds | an operator, a permission, the network, Spark's own semantics |
| the static checks | `uv run ruff check`, `ruff format --check`, the lint, Secret Detection, `pip-audit`, in `test` and the gates | | the workflow and the manifest against the rules of §W, a leaked secret, a vulnerable dependency with a fix | a value a placeholder resolves to |
| the image's smoke, `Dockerfile` target `smoke` | `build-image` on every tag, before the push | yes, `samples/` baked in | the job's command on the image with its dependencies, networking off, the output mount owned by root | the job's inputs and outputs in S3, the platform's staging |
| the worker's package | `build-task-code` on every tag | | every callable imports from the zip on the runner's Python 3.12 | the worker's own environment, which pre-installs what wins over the zip |
| a run in `dev` | the data scientist, §D | yes, the inbox the manifest seeds, or what the developer drops there | the workflow's shape: the operators, the templates, the project's permissions, the job on the image, the tasks' XComs | the deployment project's role under the fence (Stage 19 decision 21 (b)), the target's network and endpoints, a catalog import into a second project (`SUP-369`), the warehouse load |
| the bundle | `bundle` on every tag, after the image | | the bundle is complete (a missing include fails), the role that makes it reads the `dev` project, and the catalog it carries matches `product.json` (`scripts/check-catalog-export.py`) | every run: nothing of the tag runs in Sandbox since Stage 19 decision 19 (c), so a release that breaks a workflow is first seen in Staging |
| Staging's leg | `staging-deploy`, `staging-test`, `staging-catalog` and `staging-model`, after the gate | yes, the inbox the bundle's `samples/` seeds (Stage 19 decision 22 (a)) | the CLI's deploy and the catalog's import into a target's project, the workflows under the deployment project's role and its fence, the chains' lookup and stage variables, the network, the image pull, the product table written in `app_etl`, counted by the job and read back as Iceberg by the leg, the model trained, served and its predictions counted | the governed read, which no stage runs (item 32); the listing and the data product, Production's alone (decisions 20 (b) and 26 (b)); nothing of Production's outputs, by design (`TM-25`); the warehouse load, which Staging has no warehouse for |
| Production's first run | the `prod` stage's bootstrap inside `production-deploy`, followed to its end, and its second run in `production-catalog` after a first import (Stage 19 decisions 14 and 25) | yes, the sample, until item 32 | the release in the account it was written for, its product listed | a test it is not: a run read, with its evidence kept |

**What goes where.** A function is tested where its inputs are literals, so the template keeps every
read and write behind a thin function and tests the function: `transform` over a frame, `report` over
summaries, `training_sets` over rows, `model_quality` over a job description, `governed_query` and
`missing_columns` over a column list. The I/O around them is tested with *doubles*: a stand-in module
placed in `sys.modules` under the real module's name (`boto3`, `pyspark.sql`, `awsglue.utils`), so the
script's imports resolve without Spark or AWS and the test can read what the script asked of them:

- **The processing command** (`tests/test_pipeline.py`): `main()` over a temporary directory holding
  copies of `samples/`, asserting the files it leaves and the summary's counts, and a governed read's
  record beside a CSV carried into its summary as `source`.
- **The worker's tasks** (`tests/test_tasks.py`): `code/` on `pythonpath` (`pyproject.toml`'s pytest
  section), a double of `boto3` answering fabricated summaries, since the project installs no boto3 (the
  worker carries it); the XCom asserted as the JSON text the next task decodes, a summary's `source`
  carried into the report.
- **The Glue script** (`tests/test_glue_script.py`): loaded with `runpy` over doubles of `awsglue.utils`,
  `pyspark.sql` and `boto3`, asserting what it reads, the column it adds, the one file it copies and the
  files it deletes, with and without its optional arguments; the governed table mocked by its column
  list, `SCHEMA`, and its current snapshot, the query the script builds compared literally, and the
  record written once the prefix holds the CSV alone. A change to `GOVERNED_COLUMNS`
  therefore changes `SCHEMA` and the expected queries in the same commit, as a developer would, and the
  drift a governed read catches is the one the unit tests cannot: a column the governed table lacks
  (verification ix, read in Staging on `v0.4.5`; no stage runs the governed read since release F, item
  32).
- **A warehouse load** (`tests/test_load_warehouse.py`): the statements it builds, over a JDBC double.
- **The `dev` launcher** (`tests/test_dev_cli.py`): `scripts/dev-cli.sh` over a double of the CLI's
  package, the tests' own interpreter standing in for the house's: the lookup answered by
  `DOMAIN_ID` through the module and from inside it, the arguments passed through unchanged, the CLI's
  exit code kept, and each refusal before the CLI runs.

**The rules of the tests.** No test reaches AWS: the test runner holds no AWS identity, by design (Stage
8 decision 11), so a test that calls boto3 for real fails there. No test reads real data: `samples/`
is synthetic, and no rung reads a governed row until item 32 (Stage 19 decision 22 (a)). A test prints what the code
prints, counts and paths, never a value. The lint is part of `test`: a workflow that fails a rule fails
the branch, before any deploy. The tests run on the laptop with `uv sync` and `uv run pytest`; in a
space, uv finds the distribution's CPython 3.12, which the project admits, and downloads none
(`UV_PYTHON_DOWNLOADS=never`).

**Testing the platform's half.** The infrastructure user reads a slice's plan before applying it
(Recipe A of [`terraform-changes.md`](terraform-changes.md)). `make check` runs offline
`deploy-application.py --self-check` (the template's manifest against the deploy script),
`model-chain.py --check`, `aws/catalog.py --self-check` and `check-gitlab-ci.py`. Before a leg writes,
`deploy-application.py <account> --check` reads the deployment project, its Tooling values and the
deploy role's membership (§T). The render, `lint-plan.py` and the deliberate breaks that read them
(Stage 10 3.2, verification ix) retired with release T's path at Stage 19 item 31.

---

## M. The manifest and the CLI's stages

`manifest.yaml` is the CLI's description of the application, and the CLI is its only reader. It
separates *content*, the folders to copy, from *activation*, the workflows to create, and names the
*stages*, one SageMaker Unified Studio project each, the deploy writes into. After a deploy no AWS
service holds an application: what exists is the project's objects and its workflows. The template's
manifest:

| Field | What it holds, and the rule |
|---|---|
| `applicationName` | `<app>`; the first part of every workflow's name in a project, the `Pipeline` tag by which two applications in one project differ, and the `<app>` of the stage-variables parameter |
| `content.storage[]` | the folders the CLI copies, each a `name` with `include` and `exclude` lists: `code` (the zips, named one by one), `src`, `glue`, `samples`, `workflows`. An include names a file or a folder, never a glob: `deploy` expands one, `bundle` in 1.0.9 does not, and the lint refuses one. No item names a connection, no `git` or `notebooks` content: the lint refuses content taken from outside the tag, since a release must be reproducible from the tag alone, and the catalog is the next row's |
| `content.catalog` | `enabled: true`, `connectionName: project.default_lakehouse`, `skipPublish: true`: `bundle` exports what the `dev` project owns in the catalog, the product's asset with its description, README and classification and any glossary term, and a deploy into a target imports it into that project and lists nothing; the workflow's `publish` task lists, where `PUBLISH_LISTING` is `"true"` (Stage 19 decisions 14, 18 (d) and 20 (b)). `product.json` declares what the export may carry and `scripts/check-catalog-export.py` fails a bundle that carries more or lacks the asset: at `v0.5.2` the asset `trades_notional` and the data product `trades-notional`; on `main`, release G's, the asset alone, since `publish` creates the data product in Production (decision 26 (b)). The lint's rule `manifest` admits the item from `awsds-workflows` `196acee` (2026-11-12) |
| `content.workflows[]` | each workflow the CLI creates in a project: its `workflowName`, the file `workflows/<name>.yaml`; `connectionName: default.workflow_serverless`; `code: code/<name>.zip` when the workflow has a Python or Bash task. A workflow is created only in a stage whose bootstrap names it: `app-etl-warehouse` is in the list, and the `prod` stage alone creates it (Stage 19 decision 16 (b)) |
| `stages.dev`, `stages.staging`, `stages.prod` | one stage per account, each a project and each naming the domain by `${DOMAIN_ID}` and `${DOMAIN_REGION}`: `dev` (`stage: DEV`), the Sandbox project `${DEV_PROJECT_NAME}`; `staging` (`STAGING`), `deploy-staging`; `prod` (`PROD`), `deploy-production`. `project.create` is never true, and there is no Sandbox `test` stage (Stage 19 decision 19 (c)) |
| `stages.<s>.environment_variables` | the same names in every stage. `JOB_IMAGE_URI`, `SUBNET_AZ1`, `SUBNET_AZ2`, `PROJECT_SG`, `PROJECT_KEY_ARN`, `TRAINING_IMAGE_URI` and `ACCOUNT_ID` are each a `${VAR}` from the shell: in `dev` a space's exports (§D step 3); in a target, set by `deploy-application.py`, the network, key and account prefixed (`STAGING_*`, `PROD_*`) and read from the project, `JOB_IMAGE_URI` the release's image and `TRAINING_IMAGE_URI` the `<env>/sagemaker/` output. `PRODUCT_DATABASE` and `PUBLISH_LISTING` are literals: `app_etl`, the same name in every account's catalog, and `"true"` in `prod` alone, since Production alone lists a chain application's product (Stage 19 decision 20 (b)). `ACCOUNT_ID` is the account the Glue job's lineage names (decision 10). A workflow's `{env.VAR}` is one of these names, filled on a run the CLI starts and, in a target, by the chain's machine from the recorded variables. Every `${VAR}` of the file must be set and non-empty for any command, another stage's included (1.0.9's `find_missing_env_vars`, read in its code 2026-10-26) |
| `stages.<s>.bootstrap.actions` | `workflow.create` per workflow, which resolves the YAML's `{proj.*}` and `{domain.*}`, writes the resolved copy at the same key and calls `CreateWorkflow`, or `UpdateWorkflow` for one that exists. `dev` and `staging` create `app-etl` and `app-etl-train` and run none: the developer starts a run with the CLI's `run` (`wait` crashes 1.0.9), and Staging's leg starts the chains. `prod` also creates `app-etl-warehouse`, then runs `app-etl` with `trailLogs: true`, so a release ends with the product table written and listed (Stage 19 decision 14) |
| `stages.<s>.deployment_configuration.storage[]` | where each content item lands: `connectionName: default.s3_shared`, `targetDirectory: <app>/<class>`; `samples` lands in `<app>/inbox`, the run's input. Every target directory sits under `<app>/`, since the project's root is shared between applications |

**Three kinds of placeholder.** A workflow written for a project cannot carry the project's id, role or
bucket, since the same file serves every project. `{proj.*}` and
`{domain.*}` are the CLI's variables, resolved per project by `workflow.create` (`{proj.id}`,
`{proj.iam_role_arn}`, `{proj.connection.default.s3_shared.s3Uri}`, `{domain.region}`). `{env.VAR}` is a
stage variable for a value no project holds (the image by digest, the subnets, the group, the key): the
CLI writes it into the definition as an Airflow parameter, `{{ params.VAR }}`, and fills it only in a run
it starts, and a chain's machine fills it from the variables the deploy recorded (`SUP-282`, Stage 19
decision 23 (a)). `${VAR}` in the manifest is read from the shell at deploy time; inside a workflow file the CLI
leaves it as written, so it is never used there.

**What the CLI does with the manifest**, measured in the lab (2026-10-15 and 2026-10-16, D41), by the
`test` stage's deploys to 2026-11-11 and by release F's legs (pipeline #129, 2026-11-16): `deploy` syncs each storage item to its target directory with no `--delete` (a file
a release drops stays until a hand removes it, `SUP-348`); `workflow.create` makes the workflow with the project role,
the Tooling environment's subnets, group and key, the log group
`/aws/mwaa-serverless/<domain>-<project>/<name>` and six tags, under the name
`<app>_<project>_<workflow>`, copying a Python task's zip to `shared/operatorFiles/<workflow>-<ms>.zip`,
one object per deploy that nothing prunes; `run` starts one workflow and returns; `bundle` zips the
storage items' files as they are, the YAML with its variables unresolved, and builds nothing, exiting 0 even
for a project its caller cannot read (`SUP-352`); `deploy --bundle-archive-path <zip>` copies the
storage items from the manifest's folder and reads only the catalog from the archive (`SUP-286`), so
`deploy-application.py` extracts the bundle beside the tag's manifest; the catalog import runs before
the bootstrap, revises an asset of the same name in the project, creates no asset and no data product in
a second project of the domain, counting DataZone's conflict as an update (`SUP-369`), and fails only
when every item fails (`SUP-357`); `destroy`
removes the workflows the manifest names and the prefix, reading the Glue jobs from the definition the
service holds. `describe --connect` lists a project's connections; `monitor` and `logs` filter workflows
by the tags the CLI wrote, and neither has run here. On every `deploy` with bootstrap actions the project
step resolves the domain by name with `ListDomains`, and `workflow.create` finds the project's role the
same way: the deploy roles hold the call and DataZone answers it with the associated domain, while it
refuses the call to a project's role, which `scripts/dev-cli.sh` answers (§D; read in 1.0.9's
`project_manager.py` and measured 2026-10-26; reported upstream as [issue 413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413)).

The stages' names, `dev`, `staging` and `prod`, the targets' project names, the `environment_variables`
names and the connection names are fixed by the pipeline and by `deploy-application.py` (`STAGE`,
`DEPLOYMENT_PROJECT` and `STAGE_PREFIX` in `scripts/tfhygiene/projects.py`): an application adds no
stage.

---

## I. The image

A SageMaker processing job runs a container, and this estate runs it with networking off: nothing can
be downloaded while the job runs, so every dependency has to be inside the image before it starts. The
code, on the other hand, is deliberately *not* in the image (D41 item 7): it is copied into the job as
an input from S3, so that a code change is a deploy, in seconds, and an image build happens only when
the dependencies change. The application image is therefore the lock's packages and nothing else.

- **`FROM` base by digest**, `awsds-prod-ecr-base@sha256:…`. Base is the house's parent image, a
  derivative of AWS's SageMaker Distribution, and the notebook image data scientists work in descends
  from the same base, so the code runs in the job on the interpreter and the OS it was written against
  in a space (D17). The digest is the developer's pin (Stage 8 decision 26), moved deliberately when a
  space moves to a newer house image; `REGISTRY` is a build argument the build runner fills with
  `ECR_REGISTRY`, so no account is a literal.
- **The lock, not the project**: `uv sync --locked --no-dev --no-install-project` into a virtual
  environment of the image's own on base's interpreter, as root, read-only to the job, with no uv cache
  left in a layer; a check import of the one runtime dependency; the project files removed. `samples/`
  rides along for a job that has no input of its own.
- **Two targets.** `app` is what the pipeline pushes. `smoke` runs the job's command the way a
  processing job does, as the image's user, with `--network=none`, `src/` mounted read-only at
  `/opt/ml/processing/code`, the output directory created by root with mode 755, and checks the files
  the command must leave; a build whose smoke fails pushes nothing.
- **Built on a tag alone**, by `build-image` on the build runner with BuildKit rootless, pushed as
  `awsds-prod-ecr-<app>:v<semver>-<short sha>`. The repository's tags are immutable, so a second pipeline
  of one tag is refused at the push; the short sha keeps two builds of one release apart. The digest
  goes down the pipeline as `JOB_IMAGE_URI`, to the bundle job, to the release's notes and to each leg's
  deploy as `--image-uri`, which records it among the stage's variables (§T). The repository keeps the 30 newest tagged images and expires an untagged one
  after 14 days.
- **The scan gate** compares the push's CRITICAL and HIGH findings with the lineage's baseline in
  `awsds/ci-gates`, `GATES_BASELINE_SAGEMAKER_DISTRIBUTION` for every `awsds-prod-ecr-app-*`, and
  informs: a red scan job stops nothing, and the operator reads its log before a deployment (Stage 8
  decision 1, the user's amendment).
- **Who pulls it**: the role of the project a job runs in, by digest. The repository's policy admits
  the Sandbox and Staging accounts (`APP_REGISTRY_CONSUMERS`, `production/registry/ecr.tf`), and
  Production's roles pull by identity; no statement this repository writes grants a project role the
  pull, and release F's runs in all three stages are its measurement. The persona reads the
  repository's images and scan findings (Stage 7 5.6).

An application that adds a compiled dependency the lock resolves (a wheel for `linux/amd64`) needs
nothing more; one that needs a system package adds it in the Dockerfile under root, through the proxy
the build arguments carry. A dependency that must be in the notebook image too, for the iteration in a
space, is a house-image change ([`dev-env.md`](dev-env.md)), never a second base.

---

## C. The code a job and a worker run

Two kinds of code run in two different machines, and the difference decides where a function goes.
The processing job's code runs in the application image on an instance SageMaker provisions, with
files staged in and out and no network: it is where the heavy transformation goes. The worker's code
runs on the small machine the workflow service starts per task, with AWS reachable through boto3 and
nothing installed beyond what the service ships: it is where the glue between steps goes, a summary
read, a result written, never a data path. What each prints lands in a log group other roles in the
account read, so each prints versions, counts, names and paths, never a value of the data.

### The processing job's code, `src/`

- A Python package with a `__main__.py`, run as `python -m <package> --input DIR --output DIR`. It is the
  job's `code` input, downloaded from the stage's `src/` prefix to `/opt/ml/processing/code`; a change to
  it is a deploy, never a build.
- The platform creates every mount owned by root with mode 755, and the image runs as its own user, so
  the job's command opens with the `chown` the image's passwordless `sudo` allows, then runs the code
  from its mount, `exec` handing the job the interpreter's exit code so that a failing command fails the
  job:

  ```bash
  sudo -n chown "$(id -u)" /opt/ml/processing/output && cd /opt/ml/processing/code && exec python -m <package> --input /opt/ml/processing/input --output /opt/ml/processing/output
  ```

- The template's job sets `EnableNetworkIsolation: true`, so the container has no network and no AWS
  credentials: SageMaker stages each `ProcessingInput` before the command starts and uploads each
  `ProcessingOutput` after it exits, as the job's role. The code reads files and writes files; nothing
  in it calls an AWS API. A processing job may drop the setting since 2026-11-17 (Stage 20 decision
  13); its container then holds the job role's credentials and reaches what a worker task reaches
  (`TM-35`).
- The interpreter is the image's: `PATH` opens with the application's virtual environment, so `python`
  is base's CPython 3.12 with the lock's packages. An extension module is admitted, since it comes from a
  wheel the lock resolved for the image's platform. `pytest` runs the same package on the laptop and in
  a space.
- A package that cannot travel in the image, or a project that uv manages beside the application, is
  [`serverless-workflows.md`](serverless-workflows.md) §J1's folder (`awsds-workflows package-job`),
  the measured alternative for the house image; the template keeps the dependencies in the image.

### The worker's tasks, `code/`

- One module per application, `code/<tasks>.py`, holding each `PythonOperator`'s callable; the pipeline
  zips the module alone as `code/<workflow>.zip`, once per workflow with a Python or Bash task, since
  the manifest's `workflows[].code` names it by the workflow's name. `build-task-code` imports the module from the zip on the runner's Python, so a
  missing import fails the tag before any deploy.
- The worker is 1 vCPU and 3 GiB, Python 3.12, Airflow 3.0.6, the Amazon provider 9.32.0 and boto3
  1.43.1, with no internet and no proxy: a task writes against that boto3 and imports nothing the zip
  lacks. A third-party package travels only as a wheel built for the worker, at the zip's root, through
  `awsds-workflows package-task` (`serverless-workflows.md` §C), and a package the worker pre-installs
  wins over the zip's copy; the template needs none.
- The callable receives its `op_kwargs` and the Airflow context, and returns its XCom, which the worker
  renders as JSON text in a later task's template: a task that reads another's XCom decodes it
  (`training_job_name` in the template's `evaluate`), since indexing it as a dict failed in Staging on
  2026-10-24. Every XCom push takes `kms:GenerateDataKey` on the workflow's key, which the execution
  role and the key policy carry.
- The task runs as the project role in every stage, and reaches what the project's prefix and key
  admit; in a target the fence closes the account's own buckets, keys and secrets to it (Stage 19
  decision 21 (b)), so a task names no prefix outside the project's `shared/<app>/`. The template's
  `publish` calls DataZone as the project role through the `datazone` endpoint: `Get*`, `List*`,
  `Search*` and `CreateListingChangeSet` are the blueprint's
  `SageMakerStudioProjectRoleMachineLearningPolicy`'s, and `StartDataSourceRun` the house grant on
  Production's deployment project role alone (`<env>/studio/workflows.tf` under `project-roles.tf`'s
  `publishing_starts_the_source`, Stage 19 decision 17), the one stage whose `PUBLISH_LISTING` is true;
  elsewhere the task returns before it. Release G's `publish`, on `main`, also creates, revises and
  lists the data product, through `CreateDataProduct` and `CreateDataProductRevision` under
  `publishing_creates_the_data_product` (decision 26 (b)), which `production/studio/`'s apply at release
  G's sitting grants (`promotion.md` §N.8.5).

---

## G. The Glue jobs

AWS Glue runs a Spark script on workers it provisions per run, and it is the one engine here that
Lake Formation hands credentials to: when a Glue job reads a governed table, Lake Formation vends it a
short-lived credential for that table's files, and the job's own role never holds S3 access to the
lake (D13). That is why a Glue job is the task kind for governed data (D28 class 2c): it runs inside
the project's network through *Glue connections* (the objects that put Glue's workers into a VPC's
subnets), and it is the only task kind that reads or writes a table. The template's `transform` reads
the trades, writes the file the processing job reads, the application's table, the product table and
the training sets; Production's `load` writes the governed warehouse.

**The script**, `glue/<script>.py`: `getResolvedOptions` for its arguments, the optional ones read only
when present; Spark through `SparkSession.builder.getOrCreate()`; boto3 from the Glue worker for what
Spark cannot do (Spark names the files it writes, so the script copies the part file to the key the
next task expects and deletes the rest). It prints counts, names and paths. Its tests run it over
doubles (§E); Glue 6.0 runs it.

**In every project**, `dev` and the two deployment projects alike, the Glue job is created by the
workflow itself and runs as the project role: the `GlueJobOperator` task creates and updates the job
from the definition, `job_name: <app>-{proj.id}` (the suffix form `<app>-<suffix>-{proj.id}` for a
second job), `iam_role_arn: "{proj.iam_role_arn}"`, `update_config: true` and the whole `Command` in
`create_job_kwargs`, with the project's two Glue network connections,
`datazone-glue-network-connection-{env.SUBNET_AZ1}-{proj.id}-dev` and its AZ2 twin, the log prefix
`datazone-{proj.id}-dev`, whose groups `/output` and `/error` never expire (`EXC-25`), and the project
tag; `script_location` under the stage's `glue/` prefix. The project role's `glue:GetJob` on a name not yet taken is `GetAGlueJobNoProjectHolds`, the grant of
`sandbox/workflows/` in Sandbox and of `<env>/studio/workflows.tf` in a target, whose statement admits a
name ending with the caller's project id, which is why the name ends with `{proj.id}`. Release T's
application slice `<env>/app/<app>/`, which declared each target's job on the job role and left the
workflow only its start (D41 item 9), retired at Stage 19 item 31, D41 item 2 being reopened by
decision 6 (b).

**The governed read** is the script's, and no workflow passes it: with `--SOURCE_TABLE`,
`lake.<database>.<table>` on an Iceberg catalog `lake` over the lake account's Glue catalog with
`glue.lakeformation-enabled=true` and the Lake Formation credential resolver in the job's `--conf`, the
script reads the columns `GOVERNED_COLUMNS` names and nothing else, and a governed table that lacks one
fails the run naming the column (verification ix, read in Staging on `v0.4.5`, when release T's slice
passed the argument). Since release F every project reads the inbox's CSVs under `--SOURCE_PATH`
(Stage 19 decision 22 (a)); the governed read returns as item 32, with a stage variable naming the
table, the lake catalog's settings in the workflow's `--conf` and `DESCRIBE` and `SELECT` to each
project role in `<env>/data/`, measured first in `dev`. Iceberg is the table format of the lake, a
layout of Parquet files plus metadata that lets an engine read a table at a snapshot and commit a write
atomically. The read is at one snapshot, the one `--SOURCE_SNAPSHOT` names or else the table's current
one, the `current-snapshot-id` Iceberg reports to Spark, and the script writes `<stem>.source.json`
beside its CSV: the table, the snapshot and whether it was pinned. The processing job, which reads the
CSV's prefix, copies the record into its summary as `source`, and the worker's report carries it, so a
run's result names the snapshot it was computed from (Stage 8 3.3, option A, 2026-10-26). A table that
reports no current snapshot fails the run. Nothing passes `--SOURCE_SNAPSHOT`, and the parity of two
stages' snapshots by id waits until it is a requirement.

**The product table** is the application's write: the Iceberg table `app_etl.trades_notional` of the
project's own database, on the Spark catalog `glue_catalog` the job's `--conf` declares over the
account's Glue Data Catalog, written as the project role and read back and counted by the job (Stage
19 decision 2). The application writes nothing in the lake (decision 22).

**The governed write** is the job role's, in Production alone, and no template workflow runs as it: the
job role keeps its named grant on `curated`'s tables (`SELECT`, `INSERT`, `DELETE`, `ALTER`,
`DESCRIBE`), `CommitTheIcebergWrites` on `curated` alone, the commit through Lake Formation's
full-table-access mode with the flag on in the lake account (`TM-26`), and Stage 9's producer proof runs
as it. A governed table exists before its first write, declared and tagged in the register (§B).

**The warehouse load**, Production alone: the job `app-etl-load-<project id>`, created by the task of
`app-etl-warehouse` in `deploy-production` and run as its project role (Stage 19 decision 16 (b)),
started by its own chain (Stage 9 decision 15). It reads the product table and writes
`trades.trades_notional` of the database `governed` over JDBC on port 5439, from the project's security
group, which the warehouse's group admits (`production/warehouse/`, the rule `sgr-021fb49c3c05b5697`),
with temporary credentials from `redshift-serverless:GetCredentials` through `VPC-Workloads`' endpoint
(`production/studio/warehouse.tf`). The session is `IAMR:user-project@d7qcazihvr3s7k`, the name the
project role's own `RedshiftDbUser` tag gives it (`SUP-205`), created at the first `GetCredentials` and
granted `gov_trades_rw` on 2026-11-16 (verification xxxii: *"30 row(s) deleted, 10 inserted"*). The
table is the deployer's, created by the manual job `production-warehouse-ddl` from
`warehouse/<table>.sql` through the Data API as `awsds-deploy-prod`, and the role writes it through the
schema's default privileges (Stage 9 9.3). A run with the workgroup down fails at `GetWorkgroup`: the
compute is `[E]` and a person raises it (§X).

---

## W. The workflows

A workflow file is Airflow written as data: one YAML per workflow in `workflows/`, in the notation the
CI/CD CLI and the service share (dag-factory's). The file's first line is the editor's layout comment,
then `<dag_id>: { dag_id, tasks: { <task>: { operator, dependencies, ... } } }`: a *DAG* is Airflow's
name for a workflow, `dependencies` lists the tasks a task waits for, and each task's remaining keys
are the arguments of its operator, the Airflow class that performs it. The operators the template
runs, each measured: `GlueJobOperator`, `SageMakerProcessingOperator`, `SageMakerTrainingOperator`,
`PythonOperator` and `S3CreateObjectOperator`; `S3KeySensor`, `S3DeleteObjectsOperator`,
`S3CopyObjectOperator` and `BashOperator` ran in Stage 6i's project workflows. A value in double braces,
`{{ ... }}`, is a Jinja template the service renders when a run is created, with a short list of
variables (below).

**The variables**, and what each becomes in each stage. One file serves every stage because its
project-specific values are placeholders: the CLI resolves `{proj.*}` and `{domain.*}` for the project
it deploys into, and writes each `{env.VAR}` into the definition as a parameter that a run fills from
the stage's variables (§M):

| In the YAML | In `dev` | In Staging and Production |
|---|---|---|
| `{proj.connection.default.s3_shared.s3Uri}<app>/...` | `app-etl-dev`'s shared prefix, under the project key | the deployment project's shared prefix in `awsds-<env>-smus-projects`, under its key; each deploy syncs the bundle's `glue/`, `src/`, `code/` and `workflows/` over the last, and `samples/` into `inbox/`; the project role can rewrite `glue/`, `src/` and `workflows/` (`TM-32`) |
| `{proj.iam_role_arn}` | the project role | the deployment project's role |
| `<app>-{proj.id}`, `<app>-<suffix>-{proj.id}` | the project's Glue job names | the same rule, on the deployment project's id |
| `{env.JOB_IMAGE_URI}` | the space's export, the last release's image by digest | the release's image by digest, `--image-uri` |
| `{env.TRAINING_IMAGE_URI}` | the space's export | `training_image_uri` of `<env>/sagemaker/` |
| `{env.SUBNET_AZ1}`, `{env.SUBNET_AZ2}`, `{env.PROJECT_SG}`, `{env.PROJECT_KEY_ARN}` | the project's Tooling values, a space's exports | the deployment project's Tooling values, read by `deploy-application.py` |
| `{domain.region}`, `{domain.id}`, `{proj.id}` | the domain's Region and id, the project's id | the same domain, the deployment project's id |
| `{env.PRODUCT_DATABASE}` | `app_etl` (Stage 19 decision 2) | `app_etl` |
| `{env.PUBLISH_LISTING}` | `"false"` | `"false"` in Staging, `"true"` in Production (Stage 19 decision 20 (b)) |
| `{env.ACCOUNT_ID}` | the space's export, the account the Glue job's OpenLineage settings name (Stage 19 decision 10) | the account, read from the project |

A new `{env.VAR}` is a change to every stage of the manifest and to `deploy-application.py`, which fills
a target's. The prefix classes are the application's contract: `inbox/` is what a run reads, `work/`
what tasks hand each other, `outbox/` the result a reader or another application picks up, `tables/`
the application's own tables, `models/` a training job's artifacts. Every path sits under `<app>/` of
the project's shared prefix, which the project's applications share under one project role:
`PutObject` and `DeleteObject` read `allowed` on another application's `glue/` by simulation on
2026-11-17 (`TM-32`, open: Stage 19 decision 28).

**The rules every workflow obeys**, each a lint rule, a service cap or a measured behaviour, with the
reason beside it:

- `retries: 0` on every task: the service defaults to 1 and caps at 3, and a failure would run twice,
  which doubles a job's cost and hides the first failure. `execution_timeout` is at most 3,600 s, the cap
  on any task, a processing job's provisioning and image pull counted (about 13 minutes of overhead in
  6i), so a processing job's `MaxRuntimeInSeconds` is at most 2,820 s and a step past about 45 minutes
  is split or fire-and-poll (verification vii).
- No `schedule` and no `start_date` in the YAML: a production workflow starts from a chain (Stage 10
  decision 13), so that one lever pauses it and one record says when it ran; `OR-1` fails on a cron of
  its own.
- A SageMaker job's `config` is written whole, with the D13 settings the portal's forms cannot express:
  `NetworkConfig` with `{env.SUBNET_AZ1}`, `{env.SUBNET_AZ2}` and `{env.PROJECT_SG}`,
  `EnableNetworkIsolation: true` (the boundary asks it of every job but a processing job; the lint's `job`
  rule at the template's pin `196acee` asks it of a processing task too, and from `1a50ceb`, Stage 20
  step 6.4, leaves it to the task),
  `EnableInterContainerTrafficEncryption: true`, `VolumeKmsKeyId` and the output's `KmsKeyId`
  `{env.PROJECT_KEY_ARN}` (an output without it lands under the S3-managed key, `EXC-22`), an `InstanceType` of the ceiling the lint receives (`ml.t3.medium` to `ml.c5.xlarge`
  today), `ImageUri` `{env.JOB_IMAGE_URI}` or a `TrainingImage` of an algorithm repository the lint
  receives, by digest and never by tag; a job name with a per-run stamp,
  `{{ macros.time.strftime('%Y%m%dT%H%M%S', macros.time.gmtime()) }}`, since `{{ ts_nodash }}` is
  midnight on a manual run and two runs of one day would collide; a training task's `S3OutputPath` under
  `models/`, its channels under `work/` and `action_if_job_exists: fail` (the rule `treino`).
  These settings are what the organization's policies refuse a job without, so a workflow carrying them
  runs in a project and in Production alike.
- The templates render at run creation with `macros`, `ti`, `params`, `ds` and `ts` alone; `dag_run` and a
  method on a macro's object fail the run before its first task.
- The last task writes the result file with an S3 operator (`S3CreateObjectOperator` over a task's XCom,
  or `S3CopyObjectOperator`), the operator of the inbox contract between applications (D41 item 10): a
  chain downstream reads `outbox/`. `orchestration-v0.3.1` declares no bridge, so a write under another
  application's `inbox/` starts no chain (§X).
- A `PythonOperator` names `python_callable: <module>.<function>` from the workflow's zip; its
  `op_kwargs` carry prefixes, never data. A `BashOperator` runs an inline command or a script at the
  zip's root. An operator outside the service's list, `SageMakerNotebookOperator` among them, is refused.
- The definition stays under 50 KB, the account under 100 workflows and each under 50 versions, a
  deploy spending one.
- The lint's promoted mode (`--promoted --prefix`), which read release T's rendered copy, has no caller
  since Stage 19 item 31 (decision 16 (b)): a target receives the bundle's own file, which `test`'s lint
  reads.

**Which workflows exist.** The manifest's `content.workflows` lists the workflows a stage may create,
and each stage's bootstrap names the ones it creates: `<app>` and `<app>-train` in every stage,
`<app>-warehouse` in `prod` alone (Stage 19 decision 16 (b)). The bundle carries every file of
`workflows/`. A chain starts a workflow only where `<env>/chains/` names it: `applications` lists each
application's workflows and `chains` each machine, Production's three and Staging's two.

---

## P. The pipeline, job by job

A GitLab pipeline is a set of *jobs* grouped in *stages* that run in order; a job runs on a runner
chosen by its *tags*, under *rules* that say on which branch or tag it exists, after the jobs its
*needs* name, and a *manual* job waits for a person to start it. A job can hand values to later ones as
a dotenv report, and a *resource group* lets one job of a kind run at a time, so two pipelines never
write Staging together. `.gitlab-ci.yml` includes `awsds/ci-gates` at a commit (`gates-v<semver>` beside
it), the shared security jobs every pipeline of the estate runs, and declares nine stages: `test`,
`build`, `verify`, `bundle`, `release`, `staging-gate`, `staging`, `gate`, `production`. Which runner
takes a job is its tag: `.gates-uv` jobs carry `awsds-test`, the promotion jobs and `bundle` carry
`awsds-deploy`, and the rest are untagged, the build runner's. The promotion jobs extend `.promotion`:
the deploy image, a proxy check, and a clone of `awsds/infrastructure` at its default branch with the
job token into `$INFRA_DIR`, printing the commit, since the scripts live there (Stage 8 decision 2); a
leg applies no Terraform (Stage 19 decision 6 (b)).

| Job | Stage, runner, rule | What it does | Set per application |
|---|---|---|---|
| `test` | `test`, test runner, every push and tag | `uv sync --locked`, ruff, pytest, the lint with `--image-repository $IMAGE_REPO`, each `LINT_INSTANCE_TYPES` and each `LINT_ALGORITHM_REPOSITORIES` | `IMAGE_REPO`; the algorithm repositories a training task names, or none |
| `secret_detection`, its gate, `pip-audit` | the gates project's, test runner | Secret Detection on branches; a vulnerability with a fix in the lock's runtime set blocks | `GATES_UV_PROJECTS: "."`; an accepted list in the gates project, keyed by the project's path |
| `pages` | `build`, test runner, `main` | `pdoc <package>` into `public/`, published | the package name |
| `build-image` | `build`, build runner, a tag `v<semver>` | BuildKit rootless: the `smoke` target, then `app` pushed as `$IMAGE_REPO:$CI_COMMIT_TAG-$CI_COMMIT_SHORT_SHA`; `SCAN_DIGEST` and `JOB_IMAGE_URI` as a dotenv report | nothing |
| `scan-gate` | `verify`, build runner, a tag | `.gates-ecr-scan` on `SCAN_REPOSITORY`, informative | `SCAN_REPOSITORY` |
| `build-task-code` | `build`, test runner, a tag | `code/<workflow>.zip` per workflow, the module imported from each zip | the workflows with worker tasks |
| `bundle` | `bundle`, deploy runner, a tag; 15 min; `AWS_PROFILE=awsds-deploy-sandbox-test` | checks the three CI/CD variables, gives every other `${VAR}` of the manifest a placeholder, prints the caller, runs `bundle --targets dev`, which zips the tag's files and exports the `dev` project's catalog (a missing include fails it, and so does *"Failed to get project connections"*, the line the CLI logs for a project the role cannot read while still exiting 0), checks the export against `product.json` with `scripts/check-catalog-export.py`, and passes the SHA256 of `artifacts/<app>.zip` as `BUNDLE_SHA256` with `JOB_IMAGE_URI`. It deploys nothing and runs nothing (Stage 19 decision 19 (c)) | the bundle's name, `product.json` |
| `store-bundle` | `release`, build runner, a tag | the SHA256 checked, the bundle copied to `s3://awsds-prod-releases/<app>/<tag>/<app>.zip` as the runner's role, `BUNDLE_OBJECT` | the key |
| `release` | `release`, build runner, a tag | the tag's GitLab release with glab, its notes naming the bundle, its SHA256 and the image, no backtick in them; a tag whose `bundle` failed gets none | the release's name |
| `gate-without-proxy` | `verify`, manual on a branch | the pip-audit gate with the proxy removed, expected to fail (verification xiii) | nothing |
| `staging-gate` | `staging-gate`, build runner, manual, blocking; `resource_group: staging` | admits the tag into Staging; its `needs` name the release's jobs, so nothing starts past a failed one | nothing |
| `staging-check` | `staging`, deploy runner | `scripts/check-egress.py staging egress` as `awsds-deploy-staging`: every endpoint available and the DNS Firewall association complete, a slice that is down failing the job naming the command that raises it; then `deploy-application.py staging --check`: `deploy-staging`, its Tooling values and the deploy role's membership | nothing |
| `staging-deploy` | `staging`, deploy runner | the bundle read as `awsds-prod-runner-deploy` and checked against `BUNDLE_SHA256`; `deploy-application.py staging` as `awsds-deploy-staging`: the bundle extracted beside the tag's manifest, the stage's variables read from the project, the CLI's `deploy --targets staging --bundle-archive-path` (the files under the project's shared prefix, the catalog imported and listed nowhere, the workflows created or updated), its log read for the workflows' network (`SUP-285`), the import's `Failed: 0` (`SUP-357`) and each bootstrap workflow found `READY`, a first import admitted (`SUP-369`); then the stage's variables recorded in `/datascience/staging/applications/<app>/stage-variables`, and `STAGING_PROJECT_ID`, `STAGING_SHARED_URI` and `STAGING_CATALOG_PENDING` as a dotenv report | the manifest's `staging` stage |
| `staging-test` | `staging`, deploy runner | each chain's machine, `awsds-staging-chain-<key>`, started with an execution named `<tag>-<job id>-<chain>`, dots turned into dashes, and polled every 60 s to `SUCCEEDED`, the execution and its history kept as artifacts; then the report `${STAGING_SHARED_URI}<app>/outbox/report.json` read, and `glue get-table` on `app_etl.trades_notional`, which must answer `ICEBERG` (Stage 19 decision 24 (a)) | the chains, in order; the table |
| `staging-catalog` | `staging`, deploy runner | where `STAGING_CATALOG_PENDING` is `true`, `deploy-application.py staging --catalog-follow-up`: the project's source started and followed as the deploy role, the bundle's asset found in the project, the same bundle deployed again, failing on any failed item; otherwise it ends at once (Stage 19 decision 25) | nothing |
| `staging-model` | `staging`, deploy runner | `model-chain.py transform staging --project`: Production's newest approved version listed first, then Staging's own model, under the project's `models/` prefix, served by a batch transform as the project role and deleted | only for an application with a model |
| `production-check` | `gate`, deploy runner | `deploy-application.py production --check` as `awsds-deploy-prod`: `deploy-production`, its Tooling values and the deploy role's membership, so the gate is asked of nobody while the deploy behind it would stop | nothing |
| `production-gate` | `gate`, build runner, manual, blocking; `resource_group: production` | admits the tag into Production, by a `deployment-managers` member; its `needs` name the Staging leg's jobs and `production-check` | nothing |
| `production-deploy` | `production`, deploy runner, 90 min | `check-egress.py production workloads-egress`; the bundle read and checked; `deploy-application.py production` into `deploy-production`, as `staging-deploy` does: the `prod` stage's bootstrap creates the three workflows and runs `app-etl`, following its log to the run's end, so the deploy fails with the run (Stage 19 decision 14); `PROD_*` as a dotenv report | the manifest's `prod` stage |
| `production-catalog` | `production`, deploy runner, 90 min | where `PROD_CATALOG_PENDING` is `true`, `check-egress.py` and `deploy-application.py production --catalog-follow-up`, as `staging-catalog` does; the second bootstrap runs `app-etl` again, and its `publish` lists the asset's revision the second import wrote; otherwise it ends at once | nothing |
| `production-warehouse-ddl` | `production`, manual, allowed to fail | `warehouse/<table>.sql` through the Data API as `awsds-deploy-prod` on `awsds-prod-warehouse`, database `governed`, each statement followed and cancelled past 300 s | only for an application that loads the warehouse |
| `production-register`, `production-approve`, `production-transform` | `production`, manual, blocking; the transform follows the approval | `model-chain.py ... --project`: the newest completed `<app>-train` job registered `PendingManualApproval` in `awsds-prod-model-<app>` with its evaluation as `ModelMetrics`; the approval by the deployment manager; the approved version served by a batch transform | only for an application with a model |

What the pipeline never does: raise or destroy a shared slice (`egress/`, `workloads-egress/`, the
warehouse compute), which the infrastructure user's `make up` and `make down` own (Stage 8 decision 27);
apply any Terraform (Stage 19 decision 6 (b)); rebuild anything past `build-image` (Production receives
the bytes Staging ran); deploy or run anything in Sandbox. A job
named `image` is refused by GitLab, and a manual gate never carries `needs: []`, which would let it
start past a failed leg (`scripts/check-gitlab-ci.py` reads both).

---

## T. The release and the promotion

A release is a tag `v<major>.<minor>.<patch>` on `main`, created by a Maintainer, and *promotion* is
the tag's pipeline carrying one set of bytes through Staging and Production, with a
person's approval before each account. No stage of it is in Sandbox: the bundle is made from the tag's
files, and its first run is Staging's. Before the tag, the infrastructure user raises what the
pipeline reads: the shared pieces are `[E]` and bill nothing while down, so a sitting opens by raising
them, in [`gitlab.md`](gitlab.md) §U's order, and the mirror must carry `main`:

1. `make hub-up`, `make gitlab-up BUILD=1`, the tunnel: the build runner takes the image and the
   untagged jobs, the deploy runner the bundle and the legs, the test runner the tests. Sandbox's
   `egress/` stays down: no job reads it.
2. `git push gitlab main` from the project folder, once `main` carries every script the legs clone
   (`deploy-application.py`, `check-egress.py`, `model-chain.py` and `tfhygiene/`): a stale mirror runs
   yesterday's deploy.
3. The tag, from a checkout of `awsds/<app>`'s `main`: `git tag v<semver> && git push origin v<semver>`.

Then, in order, with the readings each leaves (`promotion.md` §T and §V record the first runs):

| Step | Hand | What happens |
|---|---|---|
| `test`, `build-image`, `build-task-code`, `bundle`, `store-bundle`, `release` | the pipeline | the image, the zips, the bundle made from the tag's files and the `dev` project's catalog, checked and stored, the release's notes |
| `make up ENV=staging ONLY=egress` | infrastructure user | Staging's endpoints, before the gate |
| `staging-gate` | deployment manager | the tag admitted |
| `staging-check`, `staging-deploy`, `staging-test`, `staging-catalog`, `staging-model` | the pipeline | the release's first run anywhere: `deploy-staging` read, the bundle deployed and its catalog imported unlisted, the stage's variables recorded, each chain run to `SUCCEEDED`, the report and the product table read back, a first import's second deploy, the model trained in Staging served; nothing torn down |
| `make up ENV=production ONLY=workloads-egress` | infrastructure user | Production's endpoints, before the gate; `ONLY=` always, since the command without it applies `runners/` without `BUILD=1` and destroys the build runner the gate runs on |
| `production-check`, then `production-gate` | the pipeline; deployment manager | `deploy-production` and the deploy role's membership read beside Staging's artifacts; the tag admitted |
| `production-deploy`, `production-catalog` | the pipeline | the same bundle and image into `deploy-production`, its bootstrap running `app-etl` to its end and `publish` listing the product; a first import's second deploy. The schedules stay as `production/chains/` declares them, `DISABLED` between sittings |
| a Production run | infrastructure user, or the schedule | each chain started and followed (§X); the first run of a new workflow read before the sitting ends |
| `production-warehouse-ddl`, `production-register`, `production-approve` | deployment manager, with the compute up for the DDL | the warehouse table, the model version registered and approved, the transform following; the model jobs stay manual until the train chain has run in `deploy-production` (§X) |
| the downs | infrastructure user | `make down ENV=staging` (`egress/`, Staging's one `[E]` slice), `make down ENV=production ONLY=workloads-egress`, `make gitlab-down`, `make hub-down`; `./aws/egress.py` reading zero burn |

Nothing is recorded by hand after a promotion: each deploy records the stage's variables in its
parameter (Stage 19 decision 23 (a)), and release T's record, the four `release.tf`s of Stage 8 3.7,
retired at item 31.

A tag whose pipeline stops is spent: ECR refuses a second push of the tag, so the fix is a new patch
version. A release that must not reach Production stops at the gate, and Staging keeps it at rest: the
pipeline destroys nothing there, and the project, its workflows and its product table stay, billing the
table's storage (Stage 8 decision 27). Staging's leg is where a release first runs under a target's
grants and network, on the sample, not real data, until item 32 brings the governed read (Stage 19
decision 22 (a)). The release in Production is `v0.5.2`; release G's tag, `v0.6.0`, is cut at its
sitting (`promotion.md` §N.8.5).

---

## S. The infrastructure a new application needs

Every permission in this estate names its resource: the deploy role may read the product tables of the
databases `deploy-project.tf` lists and serve the models named `app-etl-*`, the persona may read one
image repository and one output prefix. A second application therefore needs its own names written into
the same grants. It needs no slice of its own: the CLI deploys it into the deployment projects, and
`<env>/chains/` holds every application's chains. Every slice below is `[P]`, applied by hand by the
infrastructure user from a fresh plan (Recipe A of [`terraform-changes.md`](terraform-changes.md)),
re-planned `No changes`. Every item below names `app-etl` today. Each is read from the code; no second
application has been built, so the list is complete as far as the code says and unmeasured as a
procedure. Stage 17's tables "What pass 9 builds" and "What pass 10 builds" apply it to an application
with a model and to one that calls Bedrock, written and not built, and its step 9.5 orders `app-ml`'s
applies by its own table. Release T's checklist, an application slice and an orchestration entry per
application, retired at Stage 19 item 31. The order is the dependency order.

| Where | What changes for `<app>` | Applied as |
|---|---|---|
| GitLab, `awsds/<app>` | §L whole: the project, its protection, members, the three runners linked, the three variables, the mirror's allowlist | the local administrator; the infrastructure user for the values |
| `production/registry/` | `module "ecr_<app>"` on `ecr-repo`, `awsds-prod-ecr-<app>`, `pull_principal_arns = local.app_consumer_account_arns` (Sandbox and Staging); the outputs `ecr_<app>_repository_url` and the key `<app>` in `ecr_repository_arns`; the build runner's push statement reads the whole map, so it follows | `awsds-infra-prod` |
| `identity/sso/` | the repository's name in `locals.tf`'s `ecr_repository_arns` and in `ReadAndPullTheApplicationImages` of `policies-data-scientists.tf`: the persona's read of the image and its scan | `awsds-infra-identity` |
| `production/sagemaker/` | for an application with a model, `registry.tf`'s `model_families` gains `<app>` (the package group and its policy); `training-image.tf`, here and in `staging/sagemaker/`, stays unless the model trains on another algorithm image. The job role's `PullTheApplicationImage` names `app-etl`'s repository alone, and no application's job runs as it | `awsds-infra-prod` |
| Sandbox, the application's `dev` project | `<app>-dev`, created by the data scientist from the `experimentation` profile in the portal, as `app-etl-dev` was (Stage 19 1.5): its `DataLake` environment, the product database by *Data → Create database* (1.5's step 12) and its source, and `awsds-deploy-sandbox-test`, the bundle's reader, a member. The role's name carries ids the creation mints, so every Sandbox slice that names the role is planned after it | the data scientist in the portal |
| the deployment projects, `deploy-staging` and `deploy-production` | the application's product database, created in each before its first deploy as `app_etl` was: a `DataLake` environment by `datazone create-environment` with `--user-parameters name=glueDbName,value=<database>` (Stage 19 item 7, verification xix). The scripts know one deployment project per target (`DEPLOYMENT_PROJECT`, `scripts/tfhygiene/projects.py`), so a second application deploys beside `app-etl` | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/studio/` and `production/studio/` | Staging's `staging-test.tf`: `product_databases` gains the database, the deploy role's Lake Formation `DESCRIBE` on it and its tables for the leg's `staging-test`, applied after the deployment project's environment creates the database, since a grant on an absent database fails the apply (Stage 20 8.4). Nothing else for an application whose tasks are Glue, processing and training jobs: `workflows.tf` gives the deployment project's role, every application's, `GetAGlueJobNoProjectHolds` and the processing and training pairs, and its publishing statements name the domain. Another task kind gains its pair in that shape, and another service its fence and boundary change: Stage 17's tables write the transform pair, the model's tag and the registry's calls, and `genai.tf` | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/foundation/` and `production/foundation/` (with the alerts var-file; copies, `check-copies.py`) | `deploy-project.tf`'s `deployment_product_databases` gains the database, for the leg's read of the product table; for a model the pipeline's jobs register and serve, as `app-etl`'s, `apply-application.tf`'s `ReadTheTrainingJobs` (`training-job/<app>-train-*`) and `ServeTheModels` (`model/<app>-*`, `transform-job/<app>-*`), and Production's `deploy-anchors.tf`, `RegisterAndApproveTheModel` on `awsds-prod-model-<app>`; a model a task registers takes another shape (Stage 17 9.5). The stage-variables parameter and the chain statements already take every application (`applications/*`, `awsds-<env>-chain-*`) | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/data/` and `production/data/` | nothing for the application's run, whose product database is the project's and whose deploy role holds no grant on the outputs bucket. `persona_read_prefixes` names `app-etl/outbox/` of the outputs bucket, which release F does not write (§Q), and a persona read under the projects bucket is unbuilt; a governed table is the register's (§B) | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/chains/` and `production/chains/` | the application in `applications`, its workflows as the manifest names them (Staging's those the `staging` stage creates); a `chains` entry per chain (`definition_template`, `application`, `workflows`, `schedule_expression`, `schedule_enabled`) and `definitions/<key>.asl.json` per chain | `awsds-infra-staging`, `awsds-infra-prod` |
| the scripts | `deploy-application.py` reads the application's name from its manifest and requires `--image-uri`, which an application with no image lacks (Stage 17 pass 10); its `--self-check` and the hook `deploy-application-check` read `examples/app-etl/`; `model-chain.py` names `app-etl` in a constant (`APP`), so a second application with a model needs the script parameterised; `aws/cicd.py`'s `APP_REPO` reads one repository; `aws/catalog.py`'s `CHAIN_DEV_PROJECTS` names `app-etl-dev` by id | a pull request on the infrastructure repository |
| `sandbox/workflows/`, and `sandbox/bedrock/` for an application that calls Bedrock | the `dev` project's role in `project_roles`, which gives it the slice's grant, planned after the project exists: both slices read each listed role with `data "aws_iam_role"`, which fails at plan for a role that does not exist (Stage 17 9.5). `awsds-deploy-sandbox-test`, the bundle role, holds DataZone reads alone | `awsds-infra-sandbox-1` |
| the mirror | `git push gitlab main` after the merge, before the first tag | the infrastructure user |
| the register, `data-governance/data/` | only for an application that writes a governed table: §B | `awsds-infra-data`, inside `DL-5`'s bracket |

What the first tag reads for a new application, in order: `build-image` pushes into a repository that
must exist and admit the runner; `bundle` needs the role's membership of the `dev` project, the
variables and a `product.json`; the Staging leg needs the product database in `deploy-staging` and in
`deploy-project.tf`, and the application in `staging/chains/`; Production's leg the same in Production. A
step missing shows as a refusal in that job's log, naming the action and the resource, which is the
reading to keep.

Unmeasured for a second application, beside the list: a chain that starts after another's
(`MWAA Serverless Workflow Run Succeeded` events, Stage 10 decision 18) and an inbox bridge
(verification xxv), neither of which `orchestration-v0.3.1` declares; and the shared deployment project,
where every application of a target runs as one project role over one shared root: a reused workflow
name or DAG id takes the other's file, a `destroy` reaches the other's Glue job (D41's comparison,
"Isolation between applications"), and a worker can rewrite the other's code (`TM-32`, open: Stage 19
decision 28). A project per application separates the applications, never a worker from its own code
(decision 28 (b)), and is unbuilt.

---

## X. Operating in Production

In Production nobody opens a portal and nobody runs a notebook: an application runs when its chain
starts it or when a release's deploy runs it (§T), and a person's acts are to raise what a run needs, to
start a chain by hand when a schedule is paused, to read a run back, and to pause or resume a schedule
through a commit.

**What runs it.** Every scheduled run starts from a chain (Stage 10 decision 13), and the `prod` stage's
bootstrap runs `app-etl` once per deploy (Stage 19 decision 14). A chain is a Step Functions *state
machine*, a small program AWS runs as a sequence of states. The Standard machine
`awsds-prod-chain-<key>` reads the application's stage variables from
`/datascience/production/applications/<app>/stage-variables`, finds its workflow by name among the
account's first 100 (`listWorkflows`), failing `WorkflowNotDeployed` when none or more than one answers,
starts it with `startWorkflowRun`, idempotent on a `ClientToken` of the execution's name and the
workflow's, with the stage variables as `OverrideParameters`, and reads the run every 60 s with
`getWorkflowRun` until `SUCCESS`, or fails `WorkflowRunNotSucceeded` on `FAILED`, `TIMEOUT` or
`STOPPED`; the machine times out at 14,400 s. The
EventBridge Scheduler schedule `awsds-prod-chain-<key>`, in the group `awsds-prod-chains`, starts the
machine on its cron, in UTC, with `flexible_time_window` off and a retry policy of three attempts
within an hour; the machine's input carries the chain's key and the scheduled time, which the Scheduler
fills (read 2026-10-26) and no chain forwards to a run. A run the schedule starts reads `RunType`
`ON_DEMAND` (verification xxiv). Why a chain rather than the workflow's own schedule: one object per
chain holds the cron and the pause, one execution history records every start, and a chain of several
workflows runs them in order without the workflows knowing each other. The template's three chains in
Production: `app-etl` at 06:30, `app-etl-train` at 07:00 and `app-etl-warehouse` at 07:30 UTC; Staging's
two carry the first two crons, `DISABLED`, and its leg starts them.

**The schedule is the pause lever.** `schedule_enabled` in `production/chains/main.tf`'s `chains` sets
the schedule `ENABLED` or `DISABLED`; a change is a commit and an apply by hand as `awsds-infra-prod`
from a fresh plan (Recipe A), since no pipeline job applies Terraform. Every schedule is `DISABLED` between sittings, since a run needs
`production/workloads-egress/`'s endpoints, which are `[E]` and destroyed between sittings so that they
bill nothing: a sitting that wants the scheduled runs raises the endpoints and turns the schedules on
by a commit, and turns them off before `make down`. A console change to a schedule is drift the next
apply reverts, so the commit is the only durable way.

**What must be up for a run**: the hub (`make hub-up`) for the `make up` check alone, since
`VPC-Workloads` has no proxy path; `make up ENV=production ONLY=workloads-egress` for the eight interface
endpoints (`sagemaker.api`, `glue`, `logs`, `kms`, `sts`, `secretsmanager`, `lakeformation`, and
`datazone` for the publishing task and the Glue job's lineage posts) and the DNS Firewall; `GROUPS=redshift` adds `redshift-serverless`, and `make up ENV=production
ONLY=workloads-egress,warehouse-compute GROUPS=redshift` raises the compute, for a chain that loads the
warehouse. A run that meets the endpoints down fails at the worker's first AWS call, and the failure rule
says so.

**A run by hand**, as `awsds-infra-prod`:

```bash
aws stepfunctions start-execution --state-machine-arn "arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-<key>" --profile awsds-infra-prod --region us-west-2
```

```bash
aws stepfunctions describe-execution --execution-arn <the execution's ARN> --query '[status,startDate,stopDate,cause]' --output text --profile awsds-infra-prod --region us-west-2
```

```bash
aws stepfunctions get-execution-history --execution-arn <the execution's ARN> --reverse-order --max-items 20 --profile awsds-infra-prod --region us-west-2
```

The history names the workflow whose run failed, and the run's task instances name the task (§V). A
workflow started outside its chain, `aws mwaa-serverless start-workflow-run`, takes the IAM action and
the key's `Decrypt` and `GenerateDataKey` in the starter's session, and the recorded stage variables as
its `OverrideParameters`, without which the run fails before its first task (`SUP-282`); the chain is
the sanctioned starter, and a persona's start is refused (Stage 10 6.2).

**Concurrency.** The operator creates the Glue job with no `ExecutionProperty`, so a second run's fate
over the first is Glue's default, unread here (release T's slice declared `max_concurrent_runs = 1`); a
workflow admits 20 concurrent runs by the service's quota. One schedule per chain, spaced by the longest
run measured (the `app-etl` chain took 19 minutes on 2026-10-25, the train chain 7), is the template's
cadence.

**The model.** The train chain leaves a training job and its evaluation under the project's
`shared/<app>/models/`, where the model jobs read them with `--project`; a person registers and approves
a version through the pipeline's manual jobs, which `awsds-prod-model-approval` reports by mail, and the
transform follows. Production's newest training job is still release T's,
`app-etl-train-20261025T070126` under the outputs bucket, so the model jobs stay manual until
`awsds-prod-chain-app-etl-train` runs one in `deploy-production`. A new approved version is served by the next
`production-transform`; nothing serves a model on a schedule in the template.

**A teardown** of the application is not `make down`: nothing of it is `[E]`. `make down
ENV=production` destroys the account's `[E]` slices, `workloads-egress/` among them, and leaves the
deployment project, its workflows, their runs and log groups, the product table and `production/chains/`,
which bill nothing at rest but the table's storage. Removing the application from a target is the CLI's
`destroy` (§M), measured once in Staging on Stage 18's project (2026-10-19: *"staging: deleted=3
not_found=0 skipped=2 error=0"*, its `operatorFiles/` zip and its log group left behind); no stage log
records it on `deploy-staging` or `deploy-production`. Read every run's evidence before it (Lesson 4).

**A rollback** under the CLI has no procedure: the earlier release's bundle stays at
`s3://awsds-prod-releases/<app>/<tag>/<app>.zip` and its image in the repository (tags are immutable),
and no pipeline job deploys an earlier tag. A deploy syncs with no `--delete`, so a file the earlier
release lacks stays after its deploy (`SUP-348`); the projects bucket is versioned, so every object a
deploy or a worker overwrote keeps its earlier version (`TM-32`). Release T's rollback, the four
`release.tf` defaults moved back, retired at Stage 19 item 31.

**Cost of a run** (`docs/PRICING.md`'s measured rates): 0.088 USD per task-hour on the worker with a
one-minute minimum, a processing task holding its worker for its whole job; Glue's `G.1X` workers per
DPU-hour; a processing or training job's instance per second; about 0.005 USD per chain execution in
transitions; the endpoints 0.080 USD per hour while up; the warehouse 1.44 USD per query-hour at
4 RPU and nothing idle, so its `make down` is the guarantee.

---

## V. Reading a run back

A run leaves its record in three places, each read with its own tool: the chain's execution in Step
Functions, the workflow's run and its task instances in the workflow service, and each task's text in a
CloudWatch log group. A failure is announced by an EventBridge rule that mails the account's alerts
topic. Start from the question, and the table names the place:

| Question | Where the answer is |
|---|---|
| did the chain run, when, how did it end | `aws stepfunctions list-executions --state-machine-arn <machine>`; `describe-execution`; the execution's input (`scheduledTime` for a scheduled start); the machine's log group `/aws/vendedlogs/states/awsds-<env>-chains` |
| which workflow run did it start, and how did each task end | `get-execution-history` names the run id; `aws mwaa-serverless list-task-instances --workflow-arn <arn> --run-id <id>` and `get-task-instance`: read a task's `DurationInSeconds` and state, never the run's `RunState`, which lags its tasks |
| why did a task fail | its stream `workflow_id=<workflow>/run_id=<id>/task_id=<task>/attempt=<n>.log` in `/aws/mwaa-serverless/<domain>-<project>/<name>`, in every stage ([`log-debugging.md`](log-debugging.md) §W) |
| a run in `dev`, from the space | the same `mwaa-serverless` reads as the project role, which need the `mwaa` group and the API's name in `NO_PROXY` (§D); from a laptop, as the infrastructure user with `awsds-infra-sandbox-1` |
| what did the Glue job do | `aws glue get-job-runs --job-name <app>-<project id>`; the run's streams under `datazone-<project id>-dev/output` and `/error`, the job's `--custom-logGroup-prefix` |
| which snapshot of the governed table did a run read, where one reads it (item 32) | `source` in `shared/<app>/outbox/report.json` and in `shared/<app>/work/job/<stem>.summary.json`; the Glue run's line *"reading SELECT … VERSION AS OF <id>"* |
| what did the processing or training job print, did it respect the boundary | `aws sagemaker describe-processing-job`, `describe-training-job` (`FailureReason`, the network and key settings); the container's stream in `/aws/sagemaker/ProcessingJobs` or `/aws/sagemaker/TrainingJobs` |
| did the result land, under which key | `aws s3api head-object --bucket awsds-<env>-smus-projects --key <domain>/<project id>/shared/<app>/outbox/<file>` with `--checksum-mode ENABLED`; `SSEKMSKeyId` the project key |
| what did the release write | the leg's deploy log (`staging-deploy.log`, `production-deploy.log`, kept a year as artifacts); `/datascience/<env>/applications/<app>/stage-variables`, the variables the last deploy ran with; `aws mwaa-serverless get-workflow` for the definition's location under the project's `shared/` |
| was the failure announced | the rules' `TriggeredRules` metric in `AWS/Events` on `RuleName=awsds-<env>-wf-<app>-<workflow>-failed` and `awsds-<env>-chain-<key>-failed`, and `NumberOfNotificationsDelivered` on `TopicName=awsds-<env>-alerts`; the mail names the workflow, the run and the event id |
| which door did a call take, and as whom | CloudTrail's `vpcEndpointId` and `userIdentity` ([`log-debugging.md`](log-debugging.md) §C): a permission failure is a response, a network failure is the absence of one (Lesson 42) |
| is the layer as declared: the CLI's workflow names and no cron, the project role under its boundary and no release T role, two AZs and no default route, log groups with retention, a failure rule per workflow, the definitions under the project's `shared/`, the chain roles | `./aws/orchestration.py awsds-infra-prod` (`OR-1` to `OR-9`; `OR-2` fails on the CLI's log groups, `EXC-25`); `./aws/catalog.py` for the product's assets, listings and grants; `./aws/deploytargets.py` for the job role, the buckets and the grants; `./aws/cicd.py` for the deploy roles and the runners; `./aws/egress.py` for the endpoints and the burn |
| what a run cost | `make status` while it runs; the bill's lines (`docs/PRICING.md`) |

The failure rules are the monitoring: a run that ends `FAILED` or `TIMEOUT` fires
`awsds-<env>-wf-<app>-<workflow>-failed` from the service's own event, and an execution that ends `FAILED`,
`TIMED_OUT` or `ABORTED` fires `awsds-<env>-chain-<key>-failed`; both deliver to `awsds-<env>-alerts`,
whose e-mail subscription the account's `foundation/` holds, and a workflow failure inside a chain fires
both. A run that never started, because its schedule was `DISABLED` or its endpoints were down, fires
nothing: the absence is read from `list-executions` against the cron (Lesson 62). A sensor with
`soft_fail` ends an empty run `SUCCESS`, which no rule hears. No metric namespace of the service exists
in any account (verification xvi), so the logs and the events are the whole of the signal.

---

## B. The application's data

An application's data sits in the storage of the project it is deployed in, `dev`'s in Sandbox and the
deployment project's in each target, which is the application's working space and results, and in the
lake in the Data Governance account, the governed product every consumer reads through Lake Formation;
the difference between them is the whole of the governance. Three catalogs sit over them: the Glue Data
Catalog holds the tables' metadata, Lake Formation holds the permissions over that metadata, and the
SageMaker Catalog holds the business view people search.

**In a project**, `dev` and the deployment projects alike, the application reads and writes under the
project's `shared/<app>/`, in the account's project bucket
`awsds-<env>-smus-projects/<domain>/<project id>/` under the project key: the inbox the manifest seeds
from `samples/`, `work/`, `outbox/`, `tables/` and `models/`. Its product table,
`app_etl.trades_notional`, is the project's own, in the account's catalog and outside the register
(§G): `dev`'s database was created in the portal (1.5's step 12), each deployment project's by
`create-environment` (Stage 19 item 7, verification xix). In a target the boundary's fence denies the
project role every other bucket of the account (`fence.tf`, Stage 19 decision 21 (b)). In Sandbox the
sandbox lake and the sandbox warehouse are the group's and the project's stores
([`sandbox-lake.md`](sandbox-lake.md), [`redshift-connection.md`](redshift-connection.md)). Nothing
promotes out of a project: the repository does (D21).

**In Staging and Production**, the account's outputs bucket `awsds-<env>-outputs`, under the data key,
held release T's tree, its result file, its table in `app_outputs` and its model artifacts. Release F
writes nothing there, and `app_outputs` retired at Stage 19 item 31; Production's bucket keeps release
T's training job's artifacts, which the manual model jobs read (§X). The bucket is registered with no
Lake Formation location, so IAM and the bucket policy govern its objects. The persona's read names
`app-etl/outbox/` alone (`persona_read_prefixes`), a prefix release F does not write. The persona
queries on Athena's enforced workgroup `awsds-<env>-athena` (results in `awsds-<env>-derived/results/`,
expiring after 30 days, a 10 GB scan limit), and Staging's persona set holds no Athena action. The
product table's Athena read is unwritten (Stage 19 decision 24 (a)): `staging-test` reads its metadata
(§P).

**The governed lake** is read in place, never copied (Stage 9 decision 3, D20): the lake account's
LF-Tag share reaches Staging and Production as it reaches Sandbox, `layer IN (raw, curated) AND
classification IN (public, internal)`, re-granted locally by `<env>/data/` to the persona and the job
role, so a reader holds the rows every consumer reads and `restricted` never. No deployment project's
role holds a re-grant, since release F's application reads its inbox; item 32, not written, gives each
project role `DESCRIBE` and `SELECT` by the consumers' expression (Stage 19 decision 22 (a)). A
tag-based share means that a new table needs no new grant: the moment it carries the tags the
expression names, every consumer reads it, and a table without a `classification` tag matches no
expression and is invisible.
Staging reads nothing of Production's outputs (`TM-25`).

**Publishing a product in the lake** is Production's write, and the rite is
[`docs/GOVERNANCE.md`](../../GOVERNANCE.md) "Assigning the LF-Tags":

1. In Sandbox, the data scientist proposes the table's schema and its classification, column overrides
   included, in a merge request on the schema source.
2. Before the promotion that first writes it, the table and its tags are declared in
   `data-governance/data/` (`aws_glue_catalog_table`, `aws_lakeformation_resource_lf_tags`), the
   Governance Manager approving the classification and the infrastructure user applying as
   `awsds-infra-data` inside `DL-5`'s bracket; the producer README gains a row per tag assignment.
   Production's write grant covers `curated`'s tables as a set and carries no `CREATE_TABLE`, so a table
   is declared, never created by a job: the shape and the classification of a product are decided by
   people before any row exists.
3. The write: the rows are written as Production's job role through Lake Formation's full-table-access
   mode, the lake's flag on (`TM-26`); no grant changes, and no template workflow runs as the job role
   (§G). A `public` or `internal` table is readable by every consumer the moment it carries its tags;
   a `restricted` table, or a `restricted` column, stays out of the default share and is read through
   an explicit grant to enumerated principals, one register row each.
4. After the first write, the table is published in the SageMaker Catalog with its business metadata by
   `governed-lake`, the Governance Manager's project in Data Governance (Stage 6f decision 1, shape (b),
   taken 2026-10-26; `curated.trades` published at 11.6 the same day).

The authoritative lake product never lives in Production: the table is in the lake's catalog and the
lake's bucket. Production's local outputs, the model artifacts among them, stay in Production. The
template writes no governed table: its Glue job writes the application's own product,
`app_etl.trades_notional` in the project's database (Stage 19 decision 2). Stage 19 decision 6 (b)
makes that table a second road, a product in the catalog: the template's `publish` task lists it where
`PUBLISH_LISTING` is `true`, Production's deployment project alone (decision 20 (b), pass 4). At
`v0.5.2` the task lists the asset Production's import carries with `dev`'s metadata (2026-11-16); on
`main`, release G's task also creates the data product `trades-notional` over that asset and publishes
it (decision 26 (b)), from the tag `v0.6.0` at its sitting. In `dev` the task returns at once, and the
asset stays in the project's inventory, where the scientist curates the description, the README and
the classification the bundle carries to the targets (decision 18 (d)).

**The warehouse.** A product that must also be queried in Redshift is loaded by a Production-only Glue
job into a schema of the database `governed` on `awsds-prod-warehouse` (§G); the schema and its 1 TB
quota, the role (`gov_trades_rw` for `trades`) and the database users are Stage 9 9.3's, created once
per theme by the infrastructure user through the Data API, and the load's user,
`IAMR:user-project@d7qcazihvr3s7k`, holds the role since 2026-11-16; the table's DDL is the
application's `warehouse/<table>.sql`, run by the manual job as the deploy role, its owner. A Sandbox project reads it through the datashare
the lake account registers, with the project's access role holding the catalog read and the Lake
Formation grant (`redshift-connection.md` §G); the compute bills per query-hour and a person raises it.

---

## N. What the application reaches

Reach is an intersection (Lesson 28): a task reads something only when a network path exists to it, its
IAM role allows the call, and, for governed data, Lake Formation grants it. The matrix names the three
for each kind of task in each stage; where one term is missing, the reach is absent by design.

| From | In `dev` (Sandbox) | In Staging and Production |
|---|---|---|
| a Glue task | the project role on the project's two Glue network connections, under the project key; reads and writes the project's `shared/<app>/` and the product table in its database; the lake's tables only through a subscription fulfilled for the project, through their resource links in the project's `DataLake` database (`curated.trades` in `eighth-experimentation` since 6f 11.9, 2026-10-26), and `app-etl-dev` holds none | the project role on the project's two Glue network connections, under the project key, every other bucket of the account fenced off; reads and writes the project's `shared/<app>/` and `app_etl`; no lake grant until item 32 (Stage 19 decision 22 (a)); in Production, `app-etl-load-<project id>` connects to the warehouse over JDBC through the `redshift-serverless` endpoint as `IAMR:user-project@d7qcazihvr3s7k` |
| a training job or a model | the project role, the project's subnets and group, network isolation; the image pulled by SageMaker's side from Production's registry by digest; inputs and outputs staged by the platform from the project prefix | the project role, the project's subnets and group (`SUBNET_AZ1`, `SUBNET_AZ2`, `PROJECT_SG`), network isolation, the project key; the image by the release's digest; inputs and outputs staged from the project prefix; no lake bucket, ever (D13) |
| a processing job | as a training job when it sets `EnableNetworkIsolation: true`, as the template's jobs do; without it (Stage 20 decision 13, applied 2026-11-17) the container holds the project role's credentials and reaches what a worker task reaches: the VPC's endpoints and the proxy's allow-list (`TM-35`) | as a training job when isolated; without it, the project role's credentials, the VPC's interface endpoints and gateways, and a proxy that refuses the `Workloads` ranges every name (read 2026-11-11); no lake bucket, ever (D13) |
| a Python or Bash task on the worker | the project role in the project's network: AWS through the VPC endpoints (DataZone among them, the template's `publish`), S3 through the gateway endpoint, no internet, no proxy | the project role in the project's network, the subnets, group and key `workflow.create` reads from the project (`SUP-285`): the interface endpoints of `workloads-egress/` (`egress/` in Staging), `datazone` among them, the S3 gateway; no internet, no proxy |
| Athena | a person in the project's query editor, as the project role on the project's enforced workgroup: the project's tables; the lake's tables the project subscribed to, through their resource links (6f 11.10, 2026-10-26) | the persona through `awsds-prod-athena` on the lake's `public` and `internal` tables, from any network; Staging's persona set holds no Athena action; the product table's Athena read is unwritten (Stage 19 decision 24 (a)); no task in the template calls Athena |
| Redshift | the sandbox warehouse through the project's connection, the Data page as the access role and a notebook through it (`redshift-connection.md` §J); the governed warehouse through the datashare alone, since Sandbox does not peer with `VPC-Workloads` | Production's project role over JDBC as `IAMR:user-project@d7qcazihvr3s7k`, the load's, its other doors fenced (`redshift-data`, `sqlworkbench`); the deploy role through the Data API for the DDL; the persona refused a session (`DenyMintingARedshiftDatabaseSession`); Staging's project role fenced off every Redshift service |
| S3 | the project prefix; the sandbox lake through the project's S3 connection; the drop-box's `PutObject` as the persona from a laptop, never read back | the project's prefix of `awsds-<env>-smus-projects`, every other bucket of the account denied by the boundary's fence (`fence.tf`); no lake bucket; the release store read by the runner's own role |
| GitLab | a space clones over the `Sandbox ↔ VPC-SharedServices` peering, `gitlab.awsds.internal` answered by the apex zone every VPC is associated with, with a persona's personal access token and git's credential helpers reset (INT-09, measured 2026-10-26; §D) | the deploy runner clones the mirror with the job token; no task reaches it |
| the MWAA Serverless API | from a space, through the `mwaa` group's endpoint alone (`GROUPS=mwaa`, the name in `NO_PROXY`): the API's only name, under `.api.aws`, is refused by the compute plane's proxy; a task never calls it | the deploy runner's calls, the CLI's deploy among them, through the proxy's open build plane in `VPC-SharedServices`; the chain's machine through Step Functions' AWS SDK integration; a task never calls it |
| the internet | a space through the proxy's allow-list; a job and a worker never | never: anything a task needs is in the image, in the zip or behind an endpoint |

---

## K. Production data while developing in Sandbox

The question a data scientist asks first is how to develop against real data without copying
Production into Sandbox. The answer here is that there is no Production data to copy: the governed
product lives in the lake, not in Production, and every account reads that one lake in place.

- **The governed lake is the same table in every stage.** Sandbox, Staging and Production receive the
  lake account's tables through one TBAC share, `restricted` excluded, read in place: no copy of
  Production's data is made for development (Lesson 1). Today the share's local re-grants in Sandbox name
  the persona, whose set carries no Athena action since D19's revision; a project role holds what a
  subscription fulfilled for its project (`eighth-experimentation`'s `SELECT` on `curated.trades` since 6f
  11.9, 2026-10-26, read from the query editor at 11.10), so a governed lake row is read from Sandbox
  through that subscription or through the warehouse's datashare. No application's job reads a governed
  table in any stage since release F (Stage 19 decision 22 (a)): the governed read is item 32, measured
  first in `dev`.
- **Production's outputs stay in Production.** Release F's result file and product table are in
  `deploy-production`'s prefix of `awsds-prod-smus-projects`, under the project key, and in its database
  `app_etl`. The persona's S3 read names `app-etl/outbox/` of `awsds-prod-outputs` alone
  (`persona_read_prefixes`), a prefix release F does not write, and a read outside the named prefixes is
  refused by the bucket policy (`DenyThePersonaReadsOutsideTheNamedPrefixes`). A reader's road to the
  product is a subscription to Production's listing, which Stage 19 4.12 measures after release G. A
  result copied into a project or the sandbox lake is the data scientist's own copy, under the Sandbox
  perimeter, and its classification follows it; nothing in the design moves it for them.
- **The application develops on synthetic data.** `samples/` drives the tests, the smoke build, a
  `dev` run and the inbox seed in every project, and since release F it is every run's input in every
  stage, Production's product included (Stage 19 decision 22 (a)). The Glue script's governed read is
  tested as the query it builds, over a mocked column list; a real governed input enters the loop with
  item 32, as the column list the application reads (`GOVERNED_COLUMNS`), checked against the table by
  the job (verification ix, read in Staging on `v0.4.5`), and as the rows every consumer reads. A real
  file of the data scientist's own reaches Production's lake through
  the drop-box, `s3://awsds-data-dropbox/incoming/YYYY/MM/DD/<file>.csv`, written from Sandbox and never
  read back, which Production's pickup curates.
- **A lake product's shape is decided before its data exists.** The lake table a new application will
  write is declared and tagged in the register before the promotion that writes it, from the schema the
  data scientist proposed; the classification decides who reads it, and a `restricted` column is read
  only by whom a register row names. An application's own product, the table its job creates in the
  project's database, carries the description, README and classification the scientist curates on
  `dev`'s asset, which each target's import copies (Stage 19 decision 18 (d)).
- **The warehouse's governed data reaches a project through the datashare**, as the project's access
  role, never by a copy; the sandbox warehouse's schemas are where a project writes.
- **A proof needing Production itself** is a Staging run: `deploy-staging` runs the bundle Production
  runs in its own project, prefix and database, so an integration test meets the definitions and grants
  Production runs with nothing of Production touched (`TM-25`); its rows are the sample's until item 32,
  and the listing and the data product are Production's alone (Stage 19 decision 20 (b)).

---

## Z. Standard and specific

What every application takes from the template unchanged, and what each one sets. A line in the first
column changed in one application diverges from the platform the pipeline and the chains expect, and
the divergence shows at a deploy, a chain's run or a lint, never at the edit.

| Standard, unchanged | Specific, set per application |
|---|---|
| the layout of §R; the `include:` of `awsds/ci-gates` and its commit; the stages, the runner tags, the `.promotion` template, the `rules` on a tag, the `resource_group`s, the manual gates and their `needs`, the dotenv reports and their names | `applicationName`, `IMAGE_REPO`, `SCAN_REPOSITORY`, `GATES_UV_PROJECTS`, the release's name, `LINT_ALGORITHM_REPOSITORIES` (empty without a training task) |
| the Dockerfile's shape: `FROM` base by digest, the lock into a virtual environment, no code, the `app` and `smoke` targets, the job's command | the base digest (the developer's pin), a system package, the sample the smoke runs, the files the smoke checks |
| the manifest's stages `dev`, `staging` and `prod`, their `environment_variables` names, `default.s3_shared` and `default.workflow_serverless`, `workflow.create`, `content.catalog`'s settings | the content items and their includes, the workflows and their zips, which stage's bootstrap creates each, the target directories under `<app>/`, `product.json` |
| the CLI's variables and the prefix classes (§W); the D13 settings on every job; `retries: 0`; the result file by an S3 operator; the lint's rules and the ceiling's instance types | each workflow's tasks, operators, arguments and prefixes; the Glue jobs' names and arguments; `GOVERNED_COLUMNS` and the tables' columns; the chains, their order and their cron |
| the processing job's contract (`/opt/ml/processing/`, `sudo chown`, `python -m`); the worker's package shape (one module, one zip per workflow, the worker's boto3) | the package, the command's arguments, the callables and their `op_kwargs` |
| the tests' shape: pytest offline, doubles for `awsglue`, `pyspark` and `boto3`, `samples/` as the fixture, the lint in `test` | the cases: the transformation's expected output, the column list, the statements |
| the Glue task's shape (§G: `GlueJobOperator`, the job named `<app>-{proj.id}`, the project role, the project's two Glue network connections, the log prefix, Glue 6.0, `G.1X`, two workers, the project tag) | the Glue jobs, their `script_args` and `--conf`, the tables and their columns, the warehouse load |
| the chain module's base in `<env>/chains/` (the roles, the log group, the schedule group, the failure rules, the module's tag) | the `applications` entry and its workflows, the `chains` entries, the ASL files |
| the grants' shape in `foundation/`, `studio/`, `sagemaker/`, `data/`, `identity/sso/` and `registry/` | the names inside them (§S): the repository, the product database, the training and model prefixes, the package group, the outbox prefix |
| the readings of §V and the instruments | the chains to start, the table to read back, the model jobs |

---

*Stages: [stage-08-cicd-pipelines.md](../stages/stage-08-cicd-pipelines.md) ·
[stage-09-deployment-targets.md](../stages/stage-09-deployment-targets.md) ·
[stage-10-orchestration-promotion.md](../stages/stage-10-orchestration-promotion.md) · The first
promotion: [promotion.md](promotion.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
