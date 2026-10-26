# Runbook — a SageMaker application, from a Sandbox project to Production

| | |
|---|---|
| **Scope** | What a team does to build, test, release and operate an application on the `app-etl` template: the repository and its GitLab project, the manifest the CI/CD CLI reads, the image, the code a job and a worker run, the Glue jobs, the workflows, the tests at each rung, the pipeline job by job, the release through Staging into Production, the chains that start the workflows there, the readings, the application's data in each stage, and what Sandbox may read of Production. The platform under it is Stages 7 to 10's build; this file is what runs per application and per release |
| **Operator** | Three hands, named at each step. The **data scientist**, in a Sandbox project and in GitLab, a Developer of the project; the **deployment manager** (`awsds/deployment-managers`, a Maintainer of the project, `DeploymentManagerAccess` in AWS), who merges, tags, admits a release at the gates and approves a model; the **infrastructure user** (`InfrastructureAccess`, the `awsds-infra-*` profiles), who writes the application's infrastructure, applies the `[P]` slices, raises and lowers the shared slices and records a promoted release. The **Governance Manager** approves a governed table's tags (§B). Which hand each act needs is §Q |
| **The rules** | **The repository is the deployable unit** (D41): the image carries the dependencies, the code is a job's input, the workflow is the activation, and a chain's state machine starts the workflow in Production. **The pipeline is the only writer of Staging and Production** (D17, D26): no project, no portal and no person deploys there, and no pipeline identity raises a shared slice (Stage 8 decision 27). **The job role reads governed data through Lake Formation, and nothing else holds a lake permission** (D13). **A name is a contract**: the application's name reaches Glue jobs, roles, prefixes, repositories and instruments, each listed in §S |
| **The picture around it** | Why the unit is an application and why a chain layer exists: [D41](../decisions/D41-sagemaker-application.md); what crosses the gate: [D28](../decisions/D28-workflow-contract.md); the template itself: [`examples/app-etl/README.md`](../../../examples/app-etl/README.md); the sittings that ran the first promotion: [`promotion.md`](promotion.md); a workflow's tasks inside a project: [`serverless-workflows.md`](serverless-workflows.md); GitLab's own procedures: [`gitlab.md`](gitlab.md); the governance cycle of a data product: [`docs/GOVERNANCE.md`](../../GOVERNANCE.md); every acronym: [`docs/GLOSSARY.md`](../../GLOSSARY.md) |
| **Written** | 2026-10-26, from the template at `v0.4.6` (promoted 2026-10-25, pipeline #102) and from the slices, scripts and stage records of Stages 8, 9 and 10. One application exists: every step here ran for `app-etl` unless it says otherwise, and no second application has been created, so §S's checklist is read from the code and not measured (Lesson 37) |

| Section | Audience | What it holds |
|---|---|---|
| [§A](#a-how-to-read-this-file) | both | how to read this file: the running example, the mental model, the vocabulary |
| [§O](#o-the-pieces) | both | the pieces: what an application is, where each piece lives in each stage, which identity runs it |
| [§Q](#q-who-does-what) | both | who does what: the acts of the data scientist, the deployment manager, the infrastructure user and the Governance Manager |
| [§R](#r-the-repository) | the data scientist | the repository: the layout, the name, the project files |
| [§L](#l-the-gitlab-project) | infrastructure | the GitLab project: protection, members, runners, the CI/CD variables, the mirror's allowlist |
| [§D](#d-the-development-cycle-in-sandbox) | the data scientist | the development cycle: a space, the deploy to `dev`, a run, the loop |
| [§E](#e-the-tests) | the data scientist | the tests: the ladder from the unit tests to Staging's leg, what each rung proves, how each kind of code is tested |
| [§M](#m-the-manifest-and-the-clis-stages) | the data scientist | the manifest and the CI/CD CLI: content, workflows, the `dev` and `test` stages, the variables, what the CLI does and does not do |
| [§I](#i-the-image) | the data scientist | the image: `FROM` base by digest, the lock, the smoke target, when it is built |
| [§C](#c-the-code-a-job-and-a-worker-run) | the data scientist | the code: `src/` for the processing job, `code/` for the worker's tasks, the two contracts |
| [§G](#g-the-glue-jobs) | both | the Glue jobs: the script, the operator in a project, the application slice in a target, the governed read |
| [§W](#w-the-workflows) | the data scientist | the workflows: the notation, the variables, the prefix classes, the rules the lint enforces, the result file |
| [§P](#p-the-pipeline-job-by-job) | both | the pipeline, job by job: stage, runner, rule, what it needs, what is set per application |
| [§T](#t-the-release-and-the-promotion) | both | the release and the promotion: the tag, what is raised first, the legs, the gates, the record |
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

**The mental model.** An application is a git repository. It is deployed four times on the way to
Production, and the four deployments differ in three things: *where* it runs (a Sandbox project, then
the Staging account, then the Production account), *what deploys it* (the CI/CD CLI into the projects,
the GitLab pipeline into the accounts) and *as whom it runs* (the project's role in a project, roles
written for the purpose in the accounts). Everything else, the code, the image, the workflow files, is
the same bytes from the first deployment to the last: the pipeline promotes a release, it never
rebuilds one. Keep those three axes in mind and every table in this file is a row per axis.

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
| **the CI/CD CLI** | `aws-smus-cicd-cli`, AWS's command-line tool for SageMaker Unified Studio: it reads the manifest, copies the application's files into a project and creates its workflows there. It never reaches Staging or Production. §M |
| **the manifest** | `manifest.yaml`, the CLI's description of the application: what to copy, which workflows to create, and the two projects (`dev`, `test`) it deploys to. §M |
| **the bundle** | the zip the CLI makes of the manifest's folders, the release's content; Staging and Production receive the bundle's files, rendered for the account. §M, §T |
| **a release** | a git tag `v<major>.<minor>.<patch>` on `main`; its pipeline builds the image, tests the bundle in a project, stores the bundle and promotes it. §T |
| **the image** | the container the processing job runs in: the application's dependencies installed from the lock, and no code. §I |
| **tag and digest** | an image's tag is a name that could be moved; its digest is a hash of its content that cannot. Every pin here is by digest. §I |
| **a project** | a SageMaker Unified Studio project in the Sandbox account: a workspace with its own S3 prefix, its own IAM role, its own KMS key and its own network settings, where a data scientist opens a notebook or a code editor (a *space*). §D |
| **the project role** | `datazone_usr_role_<project>_<env>`, the IAM role every call from a project runs as: a notebook's, a workflow's, a job's. §D |
| **the persona** | a person's AWS identity, an Identity Center permission set such as `DataScientistAccess` (Sandbox) or `DataScientistProdAccess` (Production), used from a laptop or the console. §Q |
| **the deploy roles** | the IAM roles the pipeline's jobs assume, one per account and purpose: `awsds-deploy-sandbox-test`, `awsds-deploy-staging`, `awsds-deploy-prod`. Only the deploy runner can assume them. §L, §P |
| **the job role** | `awsds-<env>-job-exec`, the one role every Glue and SageMaker job runs as in Staging and Production; it holds the Lake Formation grants. §G |
| **the execution role** | `awsds-<env>-wf-<key>`, one IAM role per workflow in Staging and Production: it starts the workflow's jobs and reaches the workflow's own prefixes, and nothing of the lake. §W, §X |
| **a permissions boundary** | an IAM ceiling attached to a role: whatever the role's policies allow, nothing beyond the boundary is granted. `awsds-<env>-app-boundary` caps every role an application's pipeline creates. §S |
| **a slice** | one Terraform root module with its own state, under `terraform-live/<account>/<slice>/`. An application has one slice per deployment account, `<env>/app/<app>/`, and shares `<env>/orchestration/`. §S |
| **`[P]`, `[D]`, `[E]`** | the three lifecycle layers of a slice (D11): permanent, applied by hand and never destroyed; a `[D]` host, stopped between sittings; ephemeral, destroyed between sittings so that nothing bills at rest. `make up` and `make down` raise and destroy the `[E]` slices of an account. §T, §X |
| **a sitting** | a working session in which the infrastructure user raises what a task needs, runs it and takes everything down again. §T |
| **the hub, the proxy, the endpoints** | the estate reaches the internet through one proxy in Production's `VPC-Networking` (the hub), and reaches AWS's own APIs through VPC interface endpoints inside each VPC. A job's or a worker's network has no internet route at all: it reaches an AWS API only through an endpoint its account's `egress/` slice holds, and those endpoints are `[E]`. §X |
| **the lake, Lake Formation, a share** | the governed data lives in the Data Governance account, in S3 buckets catalogued in its Glue Data Catalog. Lake Formation is the permission layer over that catalog: a consumer account receives a *share* (a grant on the account), its administrator *re-grants* it to a local role, and a query engine asks Lake Formation for short-lived credentials per table. The share is written over tags (`layer`, `classification`), not table names: tag-based access control, TBAC. §B |
| **a resource link** | a local catalog entry that points at a shared database in another account's catalog, so a query can name it. §B |
| **the outputs bucket** | `awsds-<env>-outputs`, each deployment account's own S3 bucket for what applications write, under the account's data key; not the lake. §B |
| **`app_outputs`** | each deployment account's own Glue database for the tables applications write into the outputs bucket. §B |
| **a chain** | in Staging and Production, the pair that starts a workflow: a Step Functions state machine, which starts the workflow's run and waits for it, and an EventBridge Scheduler schedule, which starts the machine on a cron. The workflow itself carries no schedule. §X |
| **the render** | `scripts/render-workflow.py`: the step that turns a workflow written for a project (with placeholders such as `{proj.id}`) into the copy an account runs, with the account's values. §W |
| **the lint** | `awsds-workflows lint`, the offline check of a workflow, a manifest or a plan against the rules of this estate; it runs on every push and in every promotion leg. §W |
| **`VersionId`** | S3 keeps every version of an object in a versioned bucket; a workflow in Staging and Production is pinned to the `VersionId` of its definition, so a later write to the same key changes nothing until a new release. §W, §T |
| **a dotenv report** | a GitLab mechanism by which a job hands values (an image digest, a SHA256) to later jobs of the same pipeline. §P |

---

## O. The pieces

An application is a GitLab repository on the `app-etl` template: `manifest.yaml`, one YAML per workflow
in the CI/CD CLI's notation, and the code the workflows' tasks run. It is deployed four times on the
way to Production, and the first table below is the map of those deployments along the three axes of
§A: where, by what, as whom. The `dev` and `test` projects are both in the Sandbox account, where
people work; Staging and Production are accounts with no project and no portal, where only the
pipeline writes and only workflows run.

| Stage | Where it runs | Deployed by | Identity of the tasks | Data |
|---|---|---|---|---|
| `dev` | the Sandbox project `eighth-experimentation` | the CI/CD CLI (`aws-smus-cicd-cli` 1.0.9), from a space, while the application is engineered | the project role, `datazone_usr_role_<project>_<env>` | the project's `shared/<app>/` prefix under the project key |
| `test` | the Sandbox project `test-experimentation` | the CLI, in the tag pipeline's `test-deploy` job, as `awsds-deploy-sandbox-test` (Stage 8 decision 19) | the project role | the project's `shared/<app>/`, emptied before each deploy |
| Staging | the Staging account, no project and no portal | the pipeline's `staging-deploy` as `awsds-deploy-staging`, from the release's bundle | `awsds-staging-wf-<workflow>` on the worker, `awsds-staging-job-exec` in every job | `awsds-staging-outputs` under `alias/awsds-staging-data`; the lake read-only through Staging's share |
| Production | the Production account, `VPC-Workloads` | the pipeline's `production-deploy` as `awsds-deploy-prod`, after two manual gates | `awsds-prod-wf-<workflow>`, `awsds-prod-job-exec` | `awsds-prod-outputs` under `alias/awsds-prod-data`; the lake read and, for the declared tables, written; the governed warehouse |

The second table says what each stage holds for one application, and the names each piece carries.
Read it as a dictionary: when a later section names `awsds-prod-wf-app-etl`, this is where the name's
pattern is.

| Piece | In `dev` and `test` | In Staging and Production |
|---|---|---|
| the workflow | `<app>_<project>_<workflow>`, every character outside `[A-Za-z0-9_]` turned into `_`, created by the CLI's `workflow.create` with the project role, the Tooling subnets, the project's group and key, tagged `CreatedBy=SMUS-CICD` and `Pipeline=<app>` | `awsds-<env>-wf-<key>`, an `awscc_mwaaserverless_workflow` of `<env>/orchestration/`, pinned to the S3 `VersionId` of its rendered definition and of its code package, `trigger_mode` `manual_only` |
| the execution role | the project role | `awsds-<env>-wf-<key>`, under `awsds-<env>-app-boundary`, holding the job starts, its prefixes of the outputs bucket and nothing of the lake |
| the log group | `/aws/mwaa-serverless/<domain>-<project>/<name>`, no retention | `/awsds/<env>/wf/<key>`, 90 days, under the data key |
| the Glue job | `<app>-{proj.id}`, created and updated by the task itself from `create_job_kwargs` | `awsds-<env>-<app>` and `awsds-<env>-<app>-<suffix>`, declared by `<env>/app/<app>/` on the job role and the account's Glue connection |
| a SageMaker job | the project role, the project's subnets, group and key, the application image by digest from Production's registry | the job role, the job subnets and group of `<env>/sagemaker/`, the data key, the same image by digest |
| the definitions and the code | `shared/<app>/{workflows,src,glue,code}/`, written by the CLI's `deploy` | `applications/<app>/<tag>/` in the outputs bucket, written by the release job with each workflow rendered for the account |
| the inbox and the results | `shared/<app>/inbox/`, `work/`, `outbox/`, `tables/`, `models/` | `inbox/<app>/`, `<app>/work/`, `<app>/outbox/`, `<app>/tables/`, `models/<app>/` in the outputs bucket (§W, the render table) |
| what starts a run | the CLI's `run`, or the manifest's `workflow.run` at the `test` deploy | a chain: the Step Functions machine `awsds-<env>-chain-<key>`, started by its EventBridge Scheduler schedule, by the Staging leg or by a person (§X) |
| the alert on a failure | none | the rules `awsds-<env>-wf-<key>-failed` and `awsds-<env>-chain-<key>-failed`, mailing `awsds-<env>-alerts` |

**What a release is made of.** D28 names the artifact classes that may cross into a deployment account,
and a release is three objects, one per class: the image in `awsds-prod-ecr-<app>` as
`v<semver>-<short sha>`, read by digest; the bundle, the CLI's zip of the manifest's folders, in
`s3://awsds-prod-releases/<app>/<tag>/<app>.zip`, read against its SHA256; and the tag's GitLab release,
whose notes name both. Each account's `release.tf` records the release it runs, so a by-hand apply after
a teardown runs the same one (Lesson 4): the slices are `[E]`, destroyed between sittings, and what
Terraform cannot read back from a file it would recreate from whatever is current.

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
| admit a release into Staging (`staging-gate`) and into Production (`production-gate`) | | yes, with the Staging artifacts and the Production plan in front of them (the jobs' artifacts, which GitLab serves; no S3 read, Stage 8 3.9) | | |
| register and approve a model version (`production-register`, `production-approve`) | | yes | | |
| raise and lower the hub, GitLab, the runners, Sandbox's and Staging's `egress/`, Production's `workloads-egress/` and the warehouse compute | | | yes, with `make` | |
| create the GitLab project, its runners and its CI/CD variables (§L) | | | yes, as GitLab's local administrator, with the slices' outputs | |
| write and apply the application's infrastructure (§S) | | | yes | |
| record a promoted release in the four `release.tf`s and push the mirror (3.7) | | | yes | |
| declare a governed table and its tags in the register before the first write (§B) | proposes the schema and the classification in a merge request | | applies, inside `DL-5`'s bracket | approves the classification |
| start a Production chain by hand, pause or resume a schedule (§X) | | | yes | |
| read a Production run: the executions, the workflow runs, the task instances | no: a persona's start or read is refused (Stage 10 6.2) | the run status, the executions and the schedules (Stage 10 decision 11); no S3 object (D31) | yes | |
| read the application's result in Production | the result file under `<app>/outbox/`, the `app_outputs` tables and the lake's `public` and `internal` tables through Athena, from any network (Stage 9 5.1, D39) | | yes | |
| read Staging | the catalog, nothing writable (Stage 9 8.4) | | yes | |

What no hand does: deploy into Staging or Production outside the pipeline, start a workflow in Production
from a portal (there is none), write governed data from Sandbox, or raise a shared slice from a pipeline
job.

---

## R. The repository

The repository is laid out so that each folder maps to one place the code will run, and the manifest,
the pipeline and the render read the folders by path: a file in the wrong folder is not copied, not
zipped or not rendered, and the failure shows at the first deploy. The layout is
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
├── Dockerfile         # the application image and the job image: the lock's dependencies, no code
├── tests/             # pytest, offline (§E)
├── samples/           # synthetic input: the smoke build, the tests, the `test` run and the inbox seed read it
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
`awsds/<app>`, the repository `awsds-prod-ecr-<app>`, the Glue jobs `awsds-<env>-<app>`, the workflow keys
`<app>` and `<app>-<suffix>`, every prefix of §W's render table, the model package group
`awsds-prod-model-<app>`, the bundle's key in the release store. Choose it once, since every IAM grant in
§S names it. A workflow's name and its `dag_id` hold the same characters: the CLI turns every other
character into `_` at creation but maps only `-` when `run` and `destroy` look the workflow up, so a name
with any other character is created under one name and found under none. Both are unique across the
applications a project holds, since `workflow.create` scans the project's whole shared root and the
first file in listing order wins a name or a `dag_id` (Stage 18's reading). The render turns a Glue
task's `<app>-<suffix>-{proj.id}` into `awsds-<env>-<app>-<suffix>`, so a Glue job's name in a workflow
opens with the application's name. An IAM role name holds 64 characters and the per-workflow role is
`awsds-staging-wf-<key>`, so a workflow key stays under 46 characters; a processing job's name,
`<app>-<timestamp>`, stays under SageMaker's 63.

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
   protected) is the only machine that can assume the deploy roles, and takes `test-deploy` and the
   promotion legs. The three are project runners of `awsds/app-etl`, linked to the other projects they
   serve and locked (`gitlab.md` §K); a new project is linked to each from the runner's edit page,
   **Other available project runners → Link**, after an administrator unlocks it for the link and locks
   it again.
5. **The CI/CD variables**, **Settings → CI/CD → Variables**, each protected, each read by `test-deploy`,
   which fails naming any that is empty. They describe the two Sandbox projects to the CLI, values the
   repository must not carry because they are an account's:

   | Variable | Value, and where it is read |
   |---|---|
   | `DOMAIN_ID`, `DOMAIN_REGION` | the SageMaker Unified Studio domain's id and Region: `awsds-workflows values` prints the id (`serverless-workflows.md` §T) |
   | `DEV_PROJECT_NAME`, `TEST_PROJECT_NAME` | the two Sandbox projects' names, `eighth-experimentation` and `test-experimentation` |
   | `SUBNET_AZ1`, `SUBNET_AZ2` | Sandbox's two private subnets, in zone order: `values` with `--subnet-name 'awsds-sandbox-private-*'` |
   | `DEV_PROJECT_SG`, `TEST_PROJECT_SG` | each project's own security group, `PROJECT_SG` of `values --project <id>` |
   | `DEV_PROJECT_KEY_ARN`, `TEST_PROJECT_KEY_ARN` | the ARN of each project's KMS key, whose id `values` prints as `PROJECT_KEY_ID` (`kmsKeyArn` of the project's Tooling environment) |
   | `TEST_PROJECT_S3_URI` | the `test` project's `s3Uri` of `default.s3_shared`, which `aws-smus-cicd-cli describe --connect` lists |
   | `TRAINING_IMAGE_URI` | AWS's XGBoost image by digest, `terraform -chdir=terraform-live/staging/sagemaker output -raw training_image_uri`; an application whose workflows name no `{env.TRAINING_IMAGE_URI}` still sets it, since the job checks every name |

   The rest of what a job reads arrives otherwise: `IMAGE_REPO`, `AWSDS_WORKFLOWS`, `LINT_INSTANCE_TYPES`
   and `LINT_ALGORITHM_REPOSITORIES` are the file's own; `JOB_IMAGE_URI`, `SCAN_DIGEST`, `BUNDLE_SHA256`,
   `BUNDLE_OBJECT` and `MODEL_PACKAGE_ARN` are earlier jobs' dotenv reports; `ECR_REGISTRY`, the proxy
   variables, the CA root at `/etc/gitlab-runner/certs/ca.crt` and the deploy profiles are the runners'.
6. **The mirror's allowlist**: the infrastructure repository lives on GitHub, and GitLab holds a copy of
   it, `awsds/infrastructure`, because the promotion jobs need its Terraform slices and scripts and a
   runner inside the VPN reaches GitLab, not GitHub. Each promotion job clones the mirror with its job
   token, so `awsds/infrastructure` → **Settings → CI/CD → Job token permissions** must admit the new
   project.
7. **Pages** needs no setting: the `pages` job on `main` publishes `public/` under the project's own name
   below `awsds-pages.internal`, shown under **Deploy → Pages**, reachable through the VPN.
8. **An accepted finding** of `pip-audit` is a line in `awsds/ci-gates`'s `baselines.gitlab-ci.yml`, in
   a list keyed by the project's path, and a new `gates-v*` tag (`gitlab.md` §G); the image's scan
   baseline is the Distribution lineage's, shared by every `awsds-prod-ecr-app-*`.

---

## D. The development cycle in Sandbox

A data scientist works in a *space*, a JupyterLab or Code Editor instance inside the Sandbox project,
on the house image (`awsds-sandbox-dev-env`). The space's `~/shared/` folder is the project's `shared/`
S3 prefix, its Python carries the CI/CD CLI (Stage 8 decision 22), and every command it runs holds the
project role's credentials, so nothing has to be configured to reach AWS. The checkout of the
application lives in the space or on the laptop. The loop:

1. **The tests and the lint**, §E's first two rungs, on the laptop or in the space.
2. **The worker's package.** The CLI copies files and builds nothing, so the zip a Python task runs
   from is built first:

   ```bash
   python3 -m zipfile -c code/<workflow>.zip code/<tasks>.py
   ```

3. **The deploy to `dev`.** "Deploy", for the CLI, means two things: copy the manifest's folders under
   the project's `shared/<app>/`, and create (or update) each workflow the manifest's `bootstrap`
   names, with the project's network and key. It runs none:

   ```bash
   aws-smus-cicd-cli deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
   ```

   `--skip-validation` because the CLI's pre-deployment validation simulates the IAM calls without their
   context keys and reads every conditioned SCP as a deny (a failure of the tool, not of the estate,
   Lesson 30); `--no-events` because the event it would publish has no handler in 1.0.9. The manifest's
   `${VAR}` names are read from the shell (§M): the domain, the project, the subnets, the group and the
   key, and `JOB_IMAGE_URI`, the image the last release's notes name. In a space the project role's
   credentials are the session's; on a laptop the CLI's boto3 reads no credential the `aws` CLI cached,
   so `aws configure export-credentials` or a fresh login precedes it. Which identity runs it, and from
   where, is Stage 8 decision 22: from a space as the project role, the identity the project's grants
   are written for (`sandbox/workflows/`, [`serverless-workflows.md`](serverless-workflows.md) §G), so no
   person gains a grant; the lab's first deploy ran from the laptop as the infrastructure user on
   2026-10-15, and the space run is owed ([`promotion.md`](promotion.md) §N.3). The deploying identity
   is a member of the project: for a non-member the CLI omits the network and the key and creates the
   workflow in the service's own network, printing one line, which is the quiet failure to watch for.
4. **A run**, and its reading:

   ```bash
   aws-smus-cicd-cli run --manifest manifest.yaml --targets dev --workflow <workflow>
   ```

   `run` returns once the service accepts the start and prints the run id; `get-workflow-run` and
   `list-task-instances` follow it (§V). The CLI fills each `{env.VAR}` of the workflow as the run's
   `OverrideParameters`, from the stage's `environment_variables`; a run started in the portal has no
   value for them, so a workflow the CLI made is read in the portal and never saved or run there
   (`serverless-workflows.md` §A).
5. **A change**: to the code in `src/`, `code/` or `glue/`, or to a workflow, is step 3 again, since the
   job reads the code as its input and the operator updates the Glue job from the definition
   (`update_config: true`); the image does not change, which is the point of keeping the code out of it
   (§I). `deploy` syncs without deleting, so a file a change removed stays in the prefix until it is
   emptied by hand (`aws s3 rm --recursive` on `shared/<app>/`, as `test-deploy` does). A change to a
   dependency is a new lock and a new release: the image is built by the tag pipeline alone, so a
   processing task has no image to run on until the first tag has pushed one. A workflow with Glue and
   worker tasks alone needs no image.
6. **The merge request**, whose branch pipeline runs `test`, Secret Detection and `pip-audit` on the test
   runner; a Maintainer merges, and `main`'s pipeline adds `pages`. Then the tag (§T).

**What the project gives, and what it does not.** The project role runs every task, inside the project's
network and under the project key, with the D13 boundary on every job: `NetworkConfig` with the two
private subnets and the project's group, `EnableNetworkIsolation`, inter-container encryption, the
project key on the volume and the output, an instance type inside the ceiling. These are the same
settings a job needs in Production, which is why a workflow written here runs there unchanged. The
operator's first describe of a job name needs the grant `sandbox/workflows/` holds for the project role,
once per project (§G of `serverless-workflows.md`). The project holds no Lake Formation grant on the
governed lake yet (6f decision 1), so a Glue task that reads a governed table runs in Staging first,
never in `dev`: in a project the application reads its inbox (§K). Each deploy spends one of the
workflow's 50 versions.

**Cost of the loop**: a worker task bills 0.088 USD per task-hour with a one-minute minimum, a processing
task holds its worker for its whole job, about 15 minutes and 0.03 USD for a one-second command in the
house image (6i's reading), and a Glue job bills its workers per DPU-hour. Sandbox's `egress/` must be up
for a run, `make up ENV=sandbox ONLY=egress` by the infrastructure user, and the space itself bills while
it runs.

---

## E. The tests

An application is tested on a ladder whose rungs cost more and prove more. The lower rungs run in
seconds on a laptop with nothing of AWS; the higher ones need accounts, roles and real data, and the
pipeline runs them where a person cannot skip them. What a rung cannot see is the next rung's: a unit
test cannot tell whether the job role may read a table, and Staging's leg is the first place that can.

| Rung | Runs | On synthetic data | Proves | Cannot see |
|---|---|---|---|---|
| the unit tests, `tests/` | `uv run pytest` on the laptop, in a space, and in `test` on every push | yes, `samples/` and fabricated inputs | the transformation, the worker's callables, the Glue script's reads, writes and the governed query it builds | an operator, a permission, the network, Spark's own semantics |
| the static checks | `uv run ruff check`, `ruff format --check`, the lint, Secret Detection, `pip-audit`, in `test` and the gates | | the workflow and the manifest against the rules of §W, a leaked secret, a vulnerable dependency with a fix | a value a placeholder resolves to |
| the image's smoke, `Dockerfile` target `smoke` | `build-image` on every tag, before the push | yes, `samples/` baked in | the job's command on the image with its dependencies, networking off, the output mount owned by root | the job's inputs and outputs in S3, the platform's staging |
| the worker's package | `build-task-code` on every tag | | every callable imports from the zip on the runner's Python 3.12 | the worker's own environment, which pre-installs what wins over the zip |
| a run in `dev` | the data scientist, §D | yes, the inbox the manifest seeds, or what the developer drops there | the workflow's shape: the operators, the templates, the project's permissions, the job on the image, the tasks' XComs | the governed read, the per-workflow role, the account's grants: "what a Sandbox run can test is the workflow's shape, not its jobs" (Stage 10 2.1) |
| the `test` project's run | `test-deploy` on every tag, after the image | yes | the bundle is complete (a missing include fails), the deploy creates every workflow, the one the manifest runs ends `SUCCESS` in a project emptied of earlier releases | the same as `dev`'s |
| Staging's leg | `staging-test` and `staging-model`, after the gate | no: the governed lake through Staging's share, `public` and `internal` rows | the rendered workflows under the per-workflow roles, the job role's grants, the network, the image pull, the governed read and the schema it expects (`GOVERNED_COLUMNS`), the table read back and counted, the model served and its predictions counted | nothing of Production's outputs, by design (`TM-25`); the warehouse load, which Staging has no warehouse for |
| Production's first run | a person, after `production-deploy`, followed to its end (§X) | no | the release in the account it was written for | a test it is not: a run read, with its evidence kept |

**What goes where.** A function is tested where its inputs are literals, so the template keeps every
read and write behind a thin function and tests the function: `transform` over a frame, `report` over
summaries, `training_sets` over rows, `model_quality` over a job description, `governed_query` and
`missing_columns` over a column list. The I/O around them is tested with *doubles*: a stand-in module
placed in `sys.modules` under the real module's name (`boto3`, `pyspark.sql`, `awsglue.utils`), so the
script's imports resolve without Spark or AWS and the test can read what the script asked of them:

- **The processing command** (`tests/test_pipeline.py`): `main()` over a temporary directory holding
  copies of `samples/`, asserting the files it leaves and the summary's counts.
- **The worker's tasks** (`tests/test_tasks.py`): `code/` on `pythonpath` (`pyproject.toml`'s pytest
  section), a double of `boto3` answering fabricated summaries, since the project installs no boto3 (the
  worker carries it); the XCom asserted as the JSON text the next task decodes.
- **The Glue script** (`tests/test_glue_script.py`): loaded with `runpy` over doubles of `awsglue.utils`,
  `pyspark.sql` and `boto3`, asserting what it reads, the column it adds, the one file it copies and the
  files it deletes, with and without its optional arguments; the governed table mocked by its column
  list, `SCHEMA`, and the query the script builds compared literally. A change to `GOVERNED_COLUMNS`
  therefore changes `SCHEMA` and the expected queries in the same commit, as a developer would, and the
  drift the Staging leg catches is the one the unit tests cannot: a column the governed table lacks
  (verification ix, read on `v0.4.5`).
- **A warehouse load** (`tests/test_load_warehouse.py`): the statements it builds, over a JDBC double.

**The rules of the tests.** No test reaches AWS: the test runner holds no AWS identity, by design (Stage
8 decision 11), so a test that calls boto3 for real fails there. No test reads real data: `samples/`
is synthetic, and a governed row enters the ladder at Staging's leg alone. A test prints what the code
prints, counts and paths, never a value. The lint is part of `test`: a workflow that fails a rule fails
the branch, before any deploy. The tests run on the laptop with `uv sync` and `uv run pytest`; in a
space, uv finds the distribution's CPython 3.12, which the project admits, and downloads none
(`UV_PYTHON_DOWNLOADS=never`).

**Testing the platform's half.** The application slice's plan is read before it is applied: by the legs
through `scripts/lint-plan.py`, and by hand by the infrastructure user with a fresh plan (Recipe A of
[`terraform-changes.md`](terraform-changes.md)); the render of a workflow for an account is read with
`./scripts/render-workflow.py <account> <workflow.yaml> --tag <tag> --image-uri <uri> --app <app>` as
the account's infrastructure profile, and `make check` renders the template's workflows against a
stand-in table offline. A deliberate break of the promotion, a tag from a branch whose workflow names an
undeclared Glue job or a column the governed table lacks, is run once to read the gate itself, with
Production untouched; Stage 10 3.2 and verification ix record the two that ran.

---

## M. The manifest and the CLI's stages

`manifest.yaml` is the CLI's description of the application, and the CLI is its only reader. It
separates *content*, the folders to copy, from *activation*, the workflows to create, and names the
*stages*, one SageMaker Unified Studio project each, the deploy writes into. After a deploy no AWS
service holds an application: what exists is the project's objects and its workflows. The template's
manifest:

| Field | What it holds, and the rule |
|---|---|
| `applicationName` | `<app>`; the first half of every workflow's name in a project, and the `Pipeline` tag by which two applications in one project differ |
| `content.storage[]` | the folders the CLI copies, each a `name` with `include` and `exclude` lists: `code` (the zips, named one by one), `src`, `glue`, `samples`, `workflows`. An include names a file or a folder, never a glob: `deploy` expands one, `bundle` in 1.0.9 does not, and the lint refuses one. No item names a connection, no `git`, `catalog` or `notebooks` content: the lint refuses content taken from outside the tag, since a release must be reproducible from the tag alone |
| `content.workflows[]` | each workflow the CLI creates in a project: its `workflowName`, the file `workflows/<name>.yaml`; `connectionName: default.workflow_serverless`; `code: code/<name>.zip` when the workflow has a Python or Bash task. A workflow left out of this list is still bundled and rendered for a deployment target, and never created in a project: `app-etl-warehouse`, Production's alone |
| `stages.dev`, `stages.test` | one SMUS project each, `stage: DEV` and `TEST`, the domain by `${DOMAIN_ID}` and `${DOMAIN_REGION}`, the project by name; `project.create` never true |
| `stages.<s>.environment_variables` | `JOB_IMAGE_URI`, `SUBNET_AZ1`, `SUBNET_AZ2`, `PROJECT_SG`, `PROJECT_KEY_ARN`, `TRAINING_IMAGE_URI`, each `${VAR}` from the shell; a workflow's `{env.VAR}` is one of these names, declared in both stages, filled on a run the CLI starts |
| `stages.<s>.bootstrap.actions` | `workflow.create` per workflow, which resolves the YAML's `{proj.*}` and `{domain.*}`, writes the resolved copy at the same key and calls `CreateWorkflow`; `workflow.run` with `trailLogs: true` in `test` alone, the run `test-deploy` follows (`wait` crashes 1.0.9) |
| `stages.<s>.deployment_configuration.storage[]` | where each content item lands: `connectionName: default.s3_shared`, `targetDirectory: <app>/<class>`; `samples` lands in `<app>/inbox`, the run's input. Every target directory sits under `<app>/`, since the project's root is shared between applications |

**Three kinds of placeholder.** A workflow written for a project cannot carry the project's id, role or
bucket, since the same file serves `dev`, `test` and, rendered, the accounts. `{proj.*}` and
`{domain.*}` are the CLI's variables, resolved per project by `workflow.create` (`{proj.id}`,
`{proj.iam_role_arn}`, `{proj.connection.default.s3_shared.s3Uri}`, `{domain.region}`). `{env.VAR}` is a
stage variable for a value no project holds (the image by digest, the subnets, the group, the key): the
CLI writes it into the definition as an Airflow parameter, `{{ params.VAR }}`, and fills it only in a run
it starts. `${VAR}` in the manifest is read from the shell at deploy time; inside a workflow file the CLI
leaves it as written, so it is never used there.

**What the CLI does with the manifest**, measured in the lab (2026-10-15 and 2026-10-16, D41) and by every
tag pipeline since: `deploy` syncs each storage item to its target directory with no `--delete` (which is
why `test-deploy` empties the prefix first); `workflow.create` makes the workflow with the project role,
the Tooling environment's subnets, group and key, the log group
`/aws/mwaa-serverless/<domain>-<project>/<name>` and six tags, under the name
`<app>_<project>_<workflow>`, copying a Python task's zip to `shared/operatorFiles/<workflow>-<ms>.zip`,
one object per deploy that nothing prunes; `run` starts one workflow and returns; `bundle` zips the
storage items' files as they are, the YAML with its variables unresolved, and builds nothing; `destroy`
removes the workflows the manifest names and the prefix, reading the Glue jobs from the definition the
service holds. `describe --connect` lists a project's connections; `monitor` and `logs` filter workflows
by the tags the CLI wrote, and neither has run here.

The stages' names, `dev` and `test`, their `environment_variables` names and the connection names are
fixed by the pipeline and the render: an application adds no stage, since Staging and Production are
the pipeline's.

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
  goes down the pipeline as `JOB_IMAGE_URI`, to the `test` run, to the release's notes and into each
  account's `release.tf`. The repository keeps the 30 newest tagged images and expires an untagged one
  after 14 days.
- **The scan gate** compares the push's CRITICAL and HIGH findings with the lineage's baseline in
  `awsds/ci-gates`, `GATES_BASELINE_SAGEMAKER_DISTRIBUTION` for every `awsds-prod-ecr-app-*`, and
  informs: a red scan job stops nothing, and the operator reads its log before a deployment (Stage 8
  decision 1, the user's amendment).
- **Who pulls it**: Sandbox's project roles and Staging's and Production's job roles, by digest, each
  named in the repository's pull principals and in the role's own statement (§S); the persona reads the
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

- The container has no network and no AWS credentials: SageMaker stages each `ProcessingInput` before
  the command starts and uploads each `ProcessingOutput` after it exits, as the job's role. The code
  reads files and writes files; nothing in it calls an AWS API.
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
  the manifest's `workflows[].code` and the orchestration slice's `code/<key>.zip` name it by the
  workflow's name. `build-task-code` imports the module from the zip on the runner's Python, so a
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
- The task runs as the execution role, the project role in a project and `awsds-<env>-wf-<key>` in a
  target, which reaches the prefixes the orchestration slice's `reads`, `writes` and `deletes` name and
  nothing else: a task that lists, reads or writes a new prefix needs its entry there (§S).

---

## G. The Glue jobs

AWS Glue runs a Spark script on workers it provisions per run, and it is the one engine here that
Lake Formation hands credentials to: when a Glue job reads a governed table, Lake Formation vends it a
short-lived credential for that table's files, and the job's own role never holds S3 access to the
lake (D13). That is why a Glue job is the task kind for governed data (D28 class 2c): it runs as the job
role, which holds the Lake Formation grants, inside the account's VPC through a *Glue connection* (the
object that puts Glue's workers into a VPC's subnets), and it is the only task that touches a lake
table. The template's `transform` reads the trades, writes the file the processing job reads, the
application's table and the training sets; Production's `load` writes the governed warehouse.

**The script**, `glue/<script>.py`: `getResolvedOptions` for its arguments, the optional ones read only
when present; Spark through `SparkSession.builder.getOrCreate()`; boto3 from the Glue worker for what
Spark cannot do (Spark names the files it writes, so the script copies the part file to the key the
next task expects and deletes the rest). It prints counts, names and paths. Its tests run it over
doubles (§E); Glue 6.0 runs it.

**In a project**, the Glue job is created by the workflow itself: the `GlueJobOperator` task creates
and updates the job from the definition, `job_name: <app>-{proj.id}` (the suffix form
`<app>-<suffix>-{proj.id}` for a second job), `iam_role_arn: "{proj.iam_role_arn}"`,
`update_config: true` and the whole `Command` in `create_job_kwargs`, with the project's two Glue network
connections, `datazone-glue-network-connection-{env.SUBNET_AZ1}-{proj.id}-dev` and its AZ2 twin, the log
prefix `datazone-{proj.id}-dev` and the project tag; `script_location` under the stage's `glue/` prefix.
The project role's `glue:GetJob` on a name not yet taken is `sandbox/workflows/`'s grant, whose statement
admits a name ending with the caller's project id, which is why the name ends with `{proj.id}`.

**In Staging and Production**, the job is Terraform's, not the workflow's: the application slice
`<env>/app/<app>/` declares it and the workflow only starts it (D41 item 9), so that what runs in
Production is written down and reviewed, and a workflow cannot invent a job. The slice's `aws_glue_job`
`awsds-<env>-<app>` runs on `job_role_arn` and `glue_connection_name` of `<env>/sagemaker/`, its script
`${release_prefix}/glue/<script>.py` under `applications/<app>/<tag>/`, Glue 6.0, `G.1X`, two workers,
`max_concurrent_runs = 1`, continuous CloudWatch logging to Glue's default groups, which `sagemaker/`
creates with a retention. The render drops the task's `job_desc`, `script_location`, `iam_role_arn`,
`update_config` and `create_job_kwargs`, and the promoted lint refuses a copy that keeps one; the
execution role holds `glue:GetJob`, `StartJobRun`, `GetJobRun`, `GetJobRuns` and `BatchStopJobRun` on the
declared names and no `CreateJob`, so a task naming an undeclared job fails closed. `scripts/lint-plan.py`
reads the slice's saved plan before each apply: every `aws_glue_job` the apply leaves names its script,
and every file or module its arguments name, under the release's `glue/` folder, and no module by its
PyPI name, which no job subnet can fetch.

**The governed read** is the slice's, not the workflow's: `default_arguments` carry `--SOURCE_TABLE`,
`lake.<database>.<table>` on an Iceberg catalog `lake` over the lake account's Glue catalog with
`glue.lakeformation-enabled=true` and the Lake Formation credential resolver (`--conf`), and
`--datalake-formats iceberg`; the workflow's `script_args` add the run's paths. Iceberg is the table
format of the lake, a layout of Parquet files plus metadata that lets an engine read a table at a
snapshot and commit a write atomically. The script reads the columns `GOVERNED_COLUMNS` names and
nothing else, and a governed table that lacks one fails the run naming the column, in Staging's leg
(verification ix, read on `v0.4.5`). In a project the same script reads the inbox's CSVs, since no
`--SOURCE_TABLE` reaches it there. `--SOURCE_SNAPSHOT` pins an Iceberg snapshot when given; nothing
passes it today.

**The governed write**, Production alone: the job role's named grant on `curated`'s tables (`SELECT`,
`INSERT`, `DELETE`, `ALTER`, `DESCRIBE`), the commit through Lake Formation's full-table-access mode with
the flag on in the lake account (`TM-26`), and `glue:UpdateTable` for the Iceberg metadata pointer. The
table exists before its first write, declared and tagged in the register (§B).

**The warehouse load**, Production alone: a second job, `awsds-prod-<app>-load`, started by its own
workflow and chain, reading the application's table and writing `trades.<table>` of the database
`governed` over JDBC on port 5439, with temporary credentials from `redshift-serverless:GetCredentials`
through `VPC-Workloads`' endpoint; the session is the job role's database user,
`IAMR:awsds-prod-job-exec`. The table is the deployer's, created by the manual job
`production-warehouse-ddl` from `warehouse/<table>.sql` through the Data API, and the role writes it
through the schema's default privileges (Stage 9 9.3). A run with the workgroup down fails at
`GetWorkgroup`: the compute is `[E]` and a person raises it (§X).

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

**The variables**, and what each becomes in a deployment target (Stage 10 decision 6's render table,
`scripts/render-workflow.py`). One file serves every stage because its account-specific values are
placeholders: the CLI fills them for a project, and the render fills them for an account, reading each
value from the Terraform state of the slice that owns it:

| In the YAML | In `dev` and `test` | In Staging and Production |
|---|---|---|
| `{proj.connection.default.s3_shared.s3Uri}<app>/glue/`, `.../src/` | the project's shared prefix | `s3://awsds-<env>-outputs/applications/<app>/<tag>/glue/`, `.../src/`: the release's tree, written once per release and never overwritten |
| `...<app>/inbox/` | the same, seeded from `samples/` | `s3://awsds-<env>-outputs/inbox/<app>/`, seeded from `samples/` when absent or different |
| `...<app>/work/`, `...<app>/outbox/`, `...<app>/tables/` | the same | `s3://awsds-<env>-outputs/<app>/work/`, `.../outbox/`, `.../tables/` |
| `...<app>/models/` | the same | `s3://awsds-<env>-outputs/models/<app>/` |
| `{proj.iam_role_arn}` | the project role | `awsds-<env>-job-exec` |
| `<app>-{proj.id}`, `<app>-<suffix>-{proj.id}` | the project's Glue job names | `awsds-<env>-<app>`, `awsds-<env>-<app>-<suffix>` |
| `{env.JOB_IMAGE_URI}` | the stage variable | the release's image by digest |
| `{env.TRAINING_IMAGE_URI}` | the stage variable | `training_image_uri` of `<env>/sagemaker/` |
| `{env.SUBNET_AZ1}`, `{env.SUBNET_AZ2}` | Sandbox's private subnets | the account's private subnets by zone id |
| `{env.PROJECT_SG}` | the project's group | `job_security_group_id` of `<env>/sagemaker/` |
| `{env.PROJECT_KEY_ARN}` | the project key | the account data key, `alias/awsds-<env>-data` |
| `{domain.region}` | the domain's Region | the account's Region |
| the Glue task's job-creation keys; a SageMaker task's `AmazonDataZoneProject` tag | read, and written | dropped |

A placeholder outside this table fails the render, and a placeholder left in the rendered copy fails
the promoted lint: a workflow names no other, and a new one is a change to the render and the lint, not
to the application. An S3 path outside `<app>/` under the project's prefix, or a class outside `glue`,
`src`, `inbox`, `work`, `outbox`, `tables` and `models`, fails the render the same way. The classes are
the application's prefix contract: `inbox/` is what a run reads, `work/` what tasks hand each other,
`outbox/` the result a reader or another application picks up, `tables/` the application's own table,
`models/` a training job's artifacts.

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
  `EnableNetworkIsolation: true`, `EnableInterContainerTrafficEncryption: true`, `VolumeKmsKeyId` and
  the output's `KmsKeyId` `{env.PROJECT_KEY_ARN}` (an output without it lands under the S3-managed key,
  `EXC-22`), an `InstanceType` of the ceiling the lint receives (`ml.t3.medium` to `ml.c5.xlarge`
  today), `ImageUri` `{env.JOB_IMAGE_URI}` or a `TrainingImage` of an algorithm repository the lint
  receives, by digest and never by tag; a job name with a per-run stamp,
  `{{ macros.time.strftime('%Y%m%dT%H%M%S', macros.time.gmtime()) }}`, since `{{ ts_nodash }}` is
  midnight on a manual run and two runs of one day would collide; a training task's `S3OutputPath` under
  `models/`, its channels in the outputs bucket and `action_if_job_exists: fail` (the rule `treino`).
  These settings are what the organization's policies refuse a job without, so a workflow carrying them
  runs in a project and in Production alike.
- The templates render at run creation with `macros`, `ti`, `params`, `ds` and `ts` alone; `dag_run` and a
  method on a macro's object fail the run before its first task.
- The last task writes the result file with an S3 operator (`S3CreateObjectOperator` over a task's XCom,
  or `S3CopyObjectOperator`), the operator of the inbox contract between applications (D41 item 10): a
  chain downstream reads `outbox/`, and a write under another application's `inbox/<app>/` is what
  starts its chain through a bridge (§X).
- A `PythonOperator` names `python_callable: <module>.<function>` from the workflow's zip; its
  `op_kwargs` carry prefixes, never data. A `BashOperator` runs an inline command or a script at the
  zip's root. An operator outside the service's list, `SageMakerNotebookOperator` among them, is refused.
- The definition stays under 50 KB, the account under 100 workflows and each under 50 versions, a
  deploy spending one.
- The promoted lint reads the rendered copy with `--promoted --prefix s3://<bucket>/applications/<app>/<tag>/`:
  every S3 path inside the account's outputs bucket, no `{proj.*}`, `{env.*}` or `{domain.*}` left, no
  project-scoped field (the rule `projeto`: a domain id, a project role, a project connection or log
  prefix), no image outside the repositories named (`imagem`), the caps (`limites`), the training task's
  settings (`treino`), the Glue task stripped of its creation keys. A workflow that only runs where the
  portal exists is not a promotable artifact (D28), and this is the check that says so before any
  deploy.

**Which workflows exist.** The manifest's `content.workflows` lists what a project receives; the bundle
carries every file of `workflows/`; the orchestration slice's `applications` map says which keys a
target creates, and a key the release's `release.tf` does not carry creates neither its workflow nor its
chain. The template's three: `<app>`, run in `test` and in every target; `<app>-train`, created in the
projects and run in the targets; `<app>-warehouse`, Production's alone, outside the manifest's list.

---

## P. The pipeline, job by job

A GitLab pipeline is a set of *jobs* grouped in *stages* that run in order; a job runs on a runner
chosen by its *tags*, under *rules* that say on which branch or tag it exists, after the jobs its
*needs* name, and a *manual* job waits for a person to start it. A job can hand values to later ones as
a dotenv report, and a *resource group* lets one job of a kind run at a time, so two pipelines never
write Staging together. `.gitlab-ci.yml` includes `awsds/ci-gates` at a commit (`gates-v<semver>` beside
it), the shared security jobs every pipeline of the estate runs, and declares nine stages: `test`,
`build`, `verify`, `deploy`, `release`, `staging-gate`, `staging`, `gate`, `production`. Which runner
takes a job is its tag: `.gates-uv` jobs carry `awsds-test`, the promotion jobs and `test-deploy` carry
`awsds-deploy`, and the rest are untagged, the build runner's. The promotion jobs extend `.promotion`:
the deploy image, a proxy check, and a clone of `awsds/infrastructure` at its default branch with the
job token into `$INFRA_DIR`, printing the commit, since the slices and the scripts live there (Stage 8
decision 2).

| Job | Stage, runner, rule | What it does | Set per application |
|---|---|---|---|
| `test` | `test`, test runner, every push and tag | `uv sync --locked`, ruff, pytest, the lint with `--image-repository $IMAGE_REPO`, each `LINT_INSTANCE_TYPES` and each `LINT_ALGORITHM_REPOSITORIES` | `IMAGE_REPO`; the algorithm repositories a training task names, or none |
| `secret_detection`, its gate, `pip-audit` | the gates project's, test runner | Secret Detection on branches; a vulnerability with a fix in the lock's runtime set blocks | `GATES_UV_PROJECTS: "."`; an accepted list in the gates project, keyed by the project's path |
| `pages` | `build`, test runner, `main` | `pdoc <package>` into `public/`, published | the package name |
| `build-image` | `build`, build runner, a tag `v<semver>` | BuildKit rootless: the `smoke` target, then `app` pushed as `$IMAGE_REPO:$CI_COMMIT_TAG-$CI_COMMIT_SHORT_SHA`; `SCAN_DIGEST` and `JOB_IMAGE_URI` as a dotenv report | nothing |
| `scan-gate` | `verify`, build runner, a tag | `.gates-ecr-scan` on `SCAN_REPOSITORY`, informative | `SCAN_REPOSITORY` |
| `build-task-code` | `build`, test runner, a tag | `code/<workflow>.zip` per workflow, the module imported from each zip | the workflows with worker tasks |
| `test-deploy` | `deploy`, deploy runner, a tag; `resource_group: <app>-test`, 45 min; `AWS_PROFILE=awsds-deploy-sandbox-test` | checks the twelve CI/CD variables and the hub, reads Sandbox's `sagemaker.api`, `glue` and `logs` endpoints, empties the `test` project's `<app>/` prefix, `bundle --targets test` (a missing include fails it), the SHA256 of `artifacts/<app>.zip` as `BUNDLE_SHA256`, `deploy --targets test`, the run read back by `get-workflow-run` until `SUCCESS` | the prefix emptied, the bundle's name, which workflow the manifest runs |
| `store-bundle` | `release`, build runner, a tag | the SHA256 checked, the bundle copied to `s3://awsds-prod-releases/<app>/<tag>/<app>.zip` as the runner's role, `BUNDLE_OBJECT` | the key |
| `release` | `release`, build runner, a tag | the tag's GitLab release with glab, its notes naming the bundle, its SHA256 and the image, no backtick in them; a tag whose `test` failed gets none | the release's name |
| `gate-without-proxy` | `verify`, manual on a branch | the pip-audit gate with the proxy removed, expected to fail (verification xiii) | nothing |
| `staging-gate` | `staging-gate`, build runner, manual, blocking; `resource_group: staging` | admits the tag into Staging; its `needs` name the release's jobs, so nothing starts past a failed one | nothing |
| `staging-check` | `staging`, deploy runner | `scripts/check-egress.py staging egress` as `awsds-deploy-staging`: every endpoint available and the DNS Firewall association complete; a slice that is down fails the job naming the command that raises it | nothing |
| `staging-deploy` | `staging`, deploy runner | the bundle read as `awsds-prod-runner-deploy` and checked; `release-application.py staging --lint --release-vars`, which renders and lints each workflow and writes the tree; the application slice's `release.auto.tfvars.json`, `gen-backend-hcl.py`, `gen-tfvars.py --pipeline`, `init`, a saved plan through `lint-plan.py`, `apply`; the orchestration slice applied; its release file kept as an artifact | `--app <app>` on the two scripts, the slice paths `app/<app>` |
| `staging-test` | `staging`, deploy runner | each chain's machine started, `awsds-staging-chain-<key>`, and polled every 60 s to `SUCCEEDED`, the execution and its history kept as artifacts; the application's table read back from `app_outputs` | the chains, in order; the table |
| `staging-model` | `staging`, deploy runner | `model-chain.py transform staging`: Production's newest approved version listed first, then Staging's own model served by a batch transform and deleted | only for an application with a model |
| `production-plan` | `gate`, deploy runner | the application slice's plan in Production, printed and kept, passed through `lint-plan.py`; read before the gate, never applied | `--app`, the paths |
| `production-gate` | `gate`, build runner, manual, blocking; `resource_group: production` | admits the tag into Production, by a `deployment-managers` member | nothing |
| `production-deploy` | `production`, deploy runner | `check-egress.py production workloads-egress`; the bundle read and checked; the release job, the application slice from a fresh saved plan through `lint-plan.py`, the orchestration slice; its release file kept | `--app`, the paths |
| `production-warehouse-ddl` | `production`, manual, allowed to fail | `warehouse/<table>.sql` through the Data API as `awsds-deploy-prod` on `awsds-prod-warehouse`, database `governed`, each statement followed and cancelled past 300 s | only for an application that loads the warehouse |
| `production-register`, `production-approve`, `production-transform` | `production`, manual, blocking; the transform follows the approval | the newest completed `<app>-train` job registered `PendingManualApproval` in `awsds-prod-model-<app>` with its evaluation as `ModelMetrics`; the approval by the deployment manager; the approved version served by a batch transform | only for an application with a model |

What the pipeline never does: raise or destroy a shared slice (`egress/`, `workloads-egress/`, the
warehouse compute), which the infrastructure user's `make up` and `make down` own (Stage 8 decision 27);
rebuild anything past `build-image` (Production receives the bytes `test` and Staging ran); apply a
Production plan it did not lint; write under `applications/` as anything but the deploy role. A job
named `image` is refused by GitLab, and a manual gate never carries `needs: []`, which would let it
start past a failed leg (`scripts/check-gitlab-ci.py` reads both).

---

## T. The release and the promotion

A release is a tag `v<major>.<minor>.<patch>` on `main`, created by a Maintainer, and *promotion* is
the tag's pipeline carrying one set of bytes through the `test` project, Staging and Production, with a
person's approval before each account. Before the tag, the infrastructure user raises what the
pipeline reads: the shared pieces are `[E]` and bill nothing while down, so a sitting opens by raising
them, in [`gitlab.md`](gitlab.md) §U's order, and the mirror must carry `main`:

1. `make hub-up`, `make gitlab-up BUILD=1`, the tunnel: the build runner takes the image and the
   untagged jobs, the deploy runner the `test` deploy and the legs, the test runner the tests.
2. `make up ENV=sandbox ONLY=egress`: the `test` run's endpoints; `test-deploy` reads them and fails in
   seconds while they are down.
3. `git push gitlab main` from the project folder, once `main` carries every slice and script the legs
   clone (the application and orchestration slices on the release the legs will record, the schedules'
   states as the sitting wants them): a stale mirror deploys yesterday's slice.
4. The tag, from a checkout of `awsds/<app>`'s `main`: `git tag v<semver> && git push origin v<semver>`.

Then, in order, with the readings each leaves (`promotion.md` §T and §V record the first runs):

| Step | Hand | What happens |
|---|---|---|
| `test`, `build-image`, `build-task-code`, `test-deploy`, `store-bundle`, `release` | the pipeline | the image, the zips, the `test` project's run to `SUCCESS`, the bundle stored, the release's notes |
| `make up ENV=staging ONLY=egress` | infrastructure user | Staging's endpoints, before the gate |
| `staging-gate` | deployment manager | the tag admitted |
| `staging-check`, `staging-deploy`, `staging-test`, `staging-model` | the pipeline | the release written under `awsds-staging-outputs/applications/<app>/<tag>/`, the slices applied, each chain run to `SUCCEEDED`, the governed read through Staging's share, the table read back, the model served; nothing torn down |
| `make up ENV=production ONLY=workloads-egress` | infrastructure user | Production's endpoints, before the gate; `ONLY=` always, since the command without it applies `runners/` without `BUILD=1` and destroys the build runner the gate runs on |
| `production-plan`, then `production-gate` | the pipeline; deployment manager | the plan read beside Staging's artifacts; the tag admitted |
| `production-deploy` | the pipeline | the same bundle and image into Production: the application slice, then the orchestration slice with the schedules as the slice declares them |
| a Production run | infrastructure user, or the schedule | each chain started and followed (§X); the first run of a new workflow read before the sitting ends |
| `production-warehouse-ddl`, `production-register`, `production-approve` | deployment manager, with the compute up for the DDL | the warehouse table, the model version registered and approved, the transform following |
| 3.7, the record | infrastructure user | the four `release.tf`s: the application slices' tag, digest and bundle SHA256, the orchestration slices' tag and each workflow's definition and code `VersionId`s, from the legs' `*-release.auto.tfvars.json` artifacts; the mirror pushed after the merge. An orchestration slice applied by hand on a stale default rolls its workflows back to the recorded release (read 2026-10-26) |
| the downs | infrastructure user | `make down ENV=staging` (the application and orchestration slices with `egress/`), `make down ENV=production ONLY=workloads-egress`, `make down ENV=sandbox`, `make gitlab-down`, `make hub-down`; `./aws/egress.py` reading zero burn |

A tag whose pipeline stops is spent: ECR refuses a second push of the tag, so the fix is a new patch
version. A release that must not reach Production stops at the gate, and Staging keeps it until the
user's `make down`. Staging's leg is where real data meets the application for the first time: the
governed read, the account's grants and the worker's network are read there, and a schema drift between
the application and the governed table fails there and nowhere earlier (verification ix).

---

## S. The infrastructure a new application needs

Every permission in this estate names its resource: the deploy role may manage the Glue jobs called
`awsds-<env>-app-etl-*` and no other, the job role may pull one image repository, the persona may read
one output prefix. A second application therefore needs its own names written into the same grants,
and its own slices beside `app-etl`'s. The `[P]` slices are applied by hand by the infrastructure user,
from a fresh plan (Recipe A of [`terraform-changes.md`](terraform-changes.md)), re-planned `No changes`;
the `[E]` ones are the pipeline's. Every item below names `app-etl` today. Each is read from the code;
no second application has been built, so the list is complete as far as the code says and unmeasured as
a procedure. The order is the dependency order.

| Where | What changes for `<app>` | Applied as |
|---|---|---|
| GitLab, `awsds/<app>` | §L whole: the project, its protection, members, the three runners linked, the twelve variables, the mirror's allowlist | the local administrator; the infrastructure user for the values |
| `production/registry/` (`[P]`) | `module "ecr_<app>"` on `ecr-repo`, `awsds-prod-ecr-<app>`, `pull_principal_arns = local.app_consumer_account_arns` (Sandbox and Staging); the outputs `ecr_<app>_repository_url` and the key `<app>` in `ecr_repository_arns`, which the job roles and the application slice read by name; the build runner's push statement reads the whole map, so it follows | `awsds-infra-prod` |
| `identity/sso/` (`[P]`) | the repository's name in `locals.tf`'s `ecr_repository_arns` and in `ReadAndPullTheApplicationImages` of `policies-data-scientists.tf`: the persona's read of the image and its scan | `awsds-infra-identity` |
| `staging/sagemaker/` and `production/sagemaker/` (`[P]`) | the job role's `PullTheApplicationImage` names `ecr_repository_arns["app-etl"]` alone (`locals.tf`, `job-role.tf`): a second repository joins the statement's resources; `registry.tf`'s `model_families` gains `<app>` for an application with a model (the package group and its policy); `training-image.tf` stays unless the model trains on another algorithm image | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/foundation/` and `production/foundation/` (`[P]`, with the alerts var-file; copies, `check-copies.py`) | `apply-application.tf`: `ManageTheApplicationGlueJob`'s resources (`awsds-<env>-<app>`, `awsds-<env>-<app>-*`), `ReadTheTrainingJobs` (`training-job/<app>-train-*`), `ServeTheModels` (`model/<app>-*`, `transform-job/<app>-*`); Production's `deploy-anchors.tf`, `RegisterAndApproveTheModel` on `awsds-prod-model-<app>` | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/data/` and `production/data/` (`[P]`) | `persona_read_prefixes` gains `<app>/outbox/`, the result file the persona reads from any network; nothing for the deploy role, whose prefixes `applications/`, `inbox/` and `models/` carry every application; `app_outputs` and its grants are shared; a new `curated` table is a declaration and its tags in the register, never a new grant, since Production's write covers `curated`'s tables as a set | `awsds-infra-staging`, `awsds-infra-prod` |
| `staging/app/<app>/` and `production/app/<app>/` (`[E]`, the pipeline's) | a copy of `app/app-etl/`: `main.tf` with the application's Glue jobs and its tables in `app_outputs` (the columns of each, since the deploy role declares the table and the job writes its rows), `data.tf` reading `ecr_<app>_repository_url`, `release.tf` with a null default until the first promotion records one; `backend.tf`; the slice's rows in `scripts/tfhygiene/layers.py` (`Slice(...)` for both accounts, rank 58 beside `app/app-etl`) and a pair in `scripts/check-copies.py` | the pipeline; by hand, the infrastructure user |
| `staging/orchestration/` and `production/orchestration/` (`[E]`, the pipeline's) | an entry per workflow in `applications` (the Glue jobs, the job-name prefixes, the `reads`, `writes` and `deletes` prefixes, each ending in `/` and never under `applications/`), an entry per chain in `chain_specs` with its cron and `schedule_enabled`, `chains/<key>.asl.json` per chain, a `bridges` entry for a chain an inbox write starts; `release.tf`'s default gains the workflows at the first record. One slice and one `release` tag hold every application's workflows today; its split per application is an open item (Stage 8 decision 27, `promotion.md` §N.5) | the pipeline; by hand, the infrastructure user |
| the scripts | `render-workflow.py`, `release-application.py` and `lint-plan.py` take `--app`, and the template's legs call the last two without it; `model-chain.py` names `app-etl` in a constant (`APP`), so a second application with a model needs the script parameterised; `aws/cicd.py`'s `APP_REPO` reads one repository; `.pre-commit-config.yaml`'s `render-workflow-check` names `examples/app-etl/` | a pull request on the infrastructure repository |
| `sandbox/workflows/` (`[P]`) | nothing per application: the grant is per project role, and both Sandbox projects hold it; `awsds-deploy-sandbox-test` reaches the `test` project's whole `shared/` prefix | |
| the mirror | `git push gitlab main` after the merge, before the first tag | the infrastructure user |
| the register, `data-governance/data/` (`[P]`) | only for an application that writes a governed table: §B | `awsds-infra-data`, inside `DL-5`'s bracket |

What the first tag reads for a new application, in order: `build-image` pushes into a repository that
must exist and admit the runner; `test-deploy` needs the project grant and the variables; the Staging
leg needs the deploy role's grants on the new job names and the application slice; Production's leg the
same, and the record. A step missing shows as a refusal in that job's log, naming the action and the
resource, which is the reading to keep.

Unmeasured for a second application, beside the list: a chain that starts after another's
(`MWAA Serverless Workflow Run Succeeded` events, Stage 10 decision 18) and an inbox bridge
(verification xxv); whether `staging/orchestration/` is split per application (Stage 8 decision 27);
and the job role, since every application in an account runs its jobs as `awsds-<env>-job-exec`, which
reads and writes the whole outputs bucket, and Stage 8 2.5 names a second application as the trigger to
give each its own role, `[P]` beside Stage 9's.

---

## X. Operating in Production

In Production nobody opens a portal and nobody runs a notebook: an application runs when its chain
starts it, and a person's acts are to raise what a run needs, to start a chain by hand when a schedule
is paused, to read a run back, and to pause or resume a schedule through a commit.

**What runs it.** Every production workflow starts from a chain (Stage 10 decision 13). A chain is a
Step Functions *state machine*, a small program AWS runs as a sequence of states: the Standard machine
`awsds-prod-chain-<key>` starts each of its workflows in order with `startWorkflowRun`, idempotent on a
`ClientToken` from the execution's name, and reads the run every 60 s with `getWorkflowRun` until
`SUCCESS`, or fails on `FAILED`, `TIMEOUT` or `STOPPED`; the machine times out at 14,400 s. The
EventBridge Scheduler schedule `awsds-prod-chain-<key>`, in the group `awsds-prod-chains`, starts the
machine on its cron, in UTC, with `flexible_time_window` off and a retry policy of three attempts
within an hour; the machine's input carries the chain's key and the scheduled time, which the Scheduler
fills (read 2026-10-26) and no chain forwards to a run. A run the schedule starts reads `RunType`
`ON_DEMAND` (verification xxiv). Why a chain rather than the workflow's own schedule: one object per
chain holds the cron and the pause, one execution history records every start, and a chain of several
workflows runs them in order without the workflows knowing each other. The template's three chains:
`app-etl` at 06:30, `app-etl-train` at 07:00 and `app-etl-warehouse` at 07:30 UTC.

**The schedule is the pause lever.** `schedule_enabled` in `production/orchestration/main.tf`'s
`chain_specs` sets the schedule `ENABLED` or `DISABLED`; a change is a commit and an apply, by the next
`production-deploy` once the mirror carries it, or by hand as `awsds-infra-prod` from a fresh plan with
the recorded release (Recipe A). Every schedule is `DISABLED` between sittings, since a run needs
`production/workloads-egress/`'s endpoints, which are `[E]` and destroyed between sittings so that they
bill nothing: a sitting that wants the scheduled runs raises the endpoints and turns the schedules on
by a commit, and turns them off before `make down`. A console change to a schedule is drift the next
apply reverts, so the commit is the only durable way.

**What must be up for a run**: the hub (`make hub-up`) for the `make up` check alone, since
`VPC-Workloads` has no proxy path; `make up ENV=production ONLY=workloads-egress` for the seven interface
endpoints (`sagemaker.api`, `glue`, `logs`, `kms`, `sts`, `secretsmanager`, `lakeformation`) and the DNS
Firewall; `GROUPS=redshift` adds `redshift-serverless`, and `make up ENV=production
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
the key's `Decrypt` and `GenerateDataKey` in the starter's session; the chain is the sanctioned starter,
and a persona's start is refused (Stage 10 6.2).

**Concurrency.** A Glue job runs one instance at a time (`max_concurrent_runs = 1`), so a second chain
execution over the first fails at `StartJobRun`; a workflow admits 20 concurrent runs by the service's
quota, and two objects under an inbox start two executions. One schedule per chain, spaced by the longest
run measured (the `app-etl` chain took 19 minutes on 2026-10-25, the train chain 7), is the template's
cadence.

**The model.** The train chain leaves a training job and its evaluation under `models/<app>/`; a person
registers and approves a version through the pipeline's manual jobs, which `awsds-prod-model-approval`
reports by mail, and the transform follows. A new approved version is served by the next
`production-transform`; nothing serves a model on a schedule in the template.

**A teardown** is `make down ENV=production`, which destroys every `[E]` slice of the account, the
orchestration slice among them (the workflows, the run history and their log groups with them) and the
application slice (the Glue jobs; the `app_outputs` table's delete needs the infrastructure user's own
grant, applied 2026-10-25); the outputs bucket, its objects and the jobs' log groups under `sagemaker/`
stay. Read every run's evidence before it (Lesson 4). The two slices bill nothing at rest and stand
between sittings, since `make down ENV=production ONLY=…` leaves them. A by-hand re-apply of the two
slices runs the recorded release, in the order application then orchestration, with the schedules as
the slice declares them.

**A rollback** is the record moved back: the four `release.tf` defaults set to the earlier release's
values and the two Production slices applied by hand as `awsds-infra-prod`, the release's objects still
under `applications/<app>/<earlier tag>/` (a release's tree is never overwritten) and its image still in
the repository (tags are immutable). A by-hand apply on a stale default was read to roll the workflows
back on 2026-10-26; a rollback as a procedure has not run.

**Cost of a run** (`docs/PRICING.md`'s measured rates): 0.088 USD per task-hour on the worker with a
one-minute minimum, a processing task holding its worker for its whole job; Glue's `G.1X` workers per
DPU-hour; a processing or training job's instance per second; about 0.005 USD per chain execution in
transitions; the endpoints about 0.070 USD per hour while up; the warehouse 1.44 USD per query-hour at
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
| why did a task fail | its stream `workflow_id=<workflow>/run_id=<id>/task_id=<task>/attempt=<n>.log` in `/awsds/<env>/wf/<key>` ([`log-debugging.md`](log-debugging.md) §W) |
| what did the Glue job do | `aws glue get-job-runs --job-name awsds-<env>-<app>`; the run's stream in `/aws-glue/jobs/logs-v2` (continuous logging), every line the script prints |
| what did the processing or training job print, did it respect the boundary | `aws sagemaker describe-processing-job`, `describe-training-job` (`FailureReason`, the network and key settings); the container's stream in `/aws/sagemaker/ProcessingJobs` or `/aws/sagemaker/TrainingJobs` |
| did the result land, under which key | `aws s3api head-object --bucket awsds-<env>-outputs --key <app>/outbox/<file>` with `--checksum-mode ENABLED`; `SSEKMSKeyId` the data key |
| what did the release write | `applications/<app>/<tag>/MANIFEST.sha256`, each object's SHA256 beside its bundled one; `aws mwaa-serverless get-workflow` for the definition's and the code's `VersionId` |
| was the failure announced | the rules' `TriggeredRules` metric in `AWS/Events` on `RuleName=awsds-<env>-wf-<key>-failed` and `awsds-<env>-chain-<key>-failed`, and `NumberOfNotificationsDelivered` on `TopicName=awsds-<env>-alerts`; the mail names the workflow, the run and the event id |
| which door did a call take, and as whom | CloudTrail's `vpcEndpointId` and `userIdentity` ([`log-debugging.md`](log-debugging.md) §C): a permission failure is a response, a network failure is the absence of one (Lesson 42) |
| is the layer as declared: roles bounded, no lake reach, two AZs and no default route, log groups with retention, the schedules' states, the definitions pinned, versions against the quota | `./aws/orchestration.py awsds-infra-prod` (`OR-1` to `OR-9`); `./aws/deploytargets.py` for the job role, the buckets and the grants; `./aws/cicd.py` for the deploy roles and the runners; `./aws/egress.py` for the endpoints and the burn |
| what a run cost | `make status` while it runs; the bill's lines (`docs/PRICING.md`) |

The failure rules are the monitoring: a run that ends `FAILED` or `TIMEOUT` fires
`awsds-<env>-wf-<key>-failed` from the service's own event, and an execution that ends `FAILED`,
`TIMED_OUT` or `ABORTED` fires `awsds-<env>-chain-<key>-failed`; both deliver to `awsds-<env>-alerts`,
whose e-mail subscription the account's `foundation/` holds, and a workflow failure inside a chain fires
both. A run that never started, because its schedule was `DISABLED` or its endpoints were down, fires
nothing: the absence is read from `list-executions` against the cron (Lesson 62). A sensor with
`soft_fail` ends an empty run `SUCCESS`, which no rule hears. No metric namespace of the service exists
in any account (verification xvi), so the logs and the events are the whole of the signal.

---

## B. The application's data

Three stores hold an application's data, and the difference between them is the whole of the
governance: the project's storage in Sandbox, which is the data scientist's; the outputs bucket of a
deployment account, which is the application's own working space and results; and the lake in the Data
Governance account, which is the governed product every consumer reads through Lake Formation. Three
catalogs sit over them: the Glue Data Catalog holds the tables' metadata, Lake Formation holds the
permissions over that metadata, and the SageMaker Catalog holds the business view people search.

**In a project**, the application reads and writes under the project's `shared/<app>/`, in the
project bucket `awsds-sandbox-smus-projects/<domain>/<project>/` under the project key: the inbox the
manifest seeds from `samples/`, `work/`, `outbox/`, `tables/` and `models/`. A project table it writes
is the project's own, in Sandbox's catalog, untagged and outside the register; the sandbox lake and the
sandbox warehouse are the group's and the project's stores ([`sandbox-lake.md`](sandbox-lake.md),
[`redshift-connection.md`](redshift-connection.md)). Nothing promotes out of a project: the repository
does (D21).

**In Staging and Production**, the account's outputs bucket `awsds-<env>-outputs` under the data key
holds everything the application writes: the release's tree, the inbox, `work/`, the result file, the
application's table as Parquet and the model artifacts. The table is catalogued in the account's own
database `app_outputs`, declared by the deploy role at each deploy with the columns the slice carries,
written by the job role, read by the persona through Athena's enforced workgroup `awsds-<env>-athena`
(results in `awsds-<env>-derived/results/`, expiring after 30 days, a 10 GB scan limit). The bucket is
registered with no Lake Formation location, so the catalog grants govern the metadata and IAM and the
bucket policy govern the objects; the persona reads `<app>/outbox/` alone of the objects.

**The governed lake** is read in place, never copied (Stage 9 decision 3, D20): the lake account's
LF-Tag share reaches Staging and Production as it reaches Sandbox, `layer IN (raw, curated) AND
classification IN (public, internal)`, re-granted locally to the job role, so a Glue job's
`--SOURCE_TABLE` reads the rows every consumer reads and `restricted` never. A tag-based share means
that a new table needs no new grant: the moment it carries the tags the expression names, every
consumer reads it, and a table without a `classification` tag matches no expression and is invisible.
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
3. The promotion: the job writes the rows through Lake Formation's full-table-access mode, the lake's
   flag on (`TM-26`); no grant changes. A `public` or `internal` table is readable by every consumer the
   moment it carries its tags; a `restricted` table, or a `restricted` column, stays out of the default
   share and is read through an explicit grant to enumerated principals, one register row each.
4. After the first write, the table is published in the SageMaker Catalog with its business metadata by
   the owner project (Stage 6f decision due 1, its shape open).

The authoritative product never lives in Production: the table is in the lake's catalog and the
lake's bucket. Production's local outputs, the model artifacts among them, stay in Production. The
template writes no governed table: its Glue job writes the application's own table in `app_outputs`,
and a publish task is an application's own (Stage 9 2.4, Stage 10 6.1).

**The warehouse.** A product that must also be queried in Redshift is loaded by a Production-only Glue
job into a schema of the database `governed` on `awsds-prod-warehouse` (§G); the schema and its 1 TB
quota, the role and the two database users are Stage 9 9.3's, created once per theme by the
infrastructure user through the Data API; the table's DDL is the application's `warehouse/<table>.sql`,
run by the manual job as the deploy role, its owner. A Sandbox project reads it through the datashare
the lake account registers, with the project's access role holding the catalog read and the Lake
Formation grant (`redshift-connection.md` §G); the compute bills per query-hour and a person raises it.

---

## N. What the application reaches

Reach is an intersection (Lesson 28): a task reads something only when a network path exists to it, its
IAM role allows the call, and, for governed data, Lake Formation grants it. The matrix names the three
for each kind of task in each stage; where one term is missing, the reach is absent by design.

| From | In `dev` and `test` (Sandbox) | In Staging and Production |
|---|---|---|
| a Glue task | the project role on the project's two Glue network connections, under the project key; reads and writes the project's `shared/<app>/`; the lake only once the project role holds a grant (6f decision 1, none today) | the job role on `glue_connection_name` of `<env>/sagemaker/`, in the job security group `awsds-<env>-jobs`; reads the lake through Lake Formation's vended credentials (the share's `SELECT`), writes the outputs bucket and `app_outputs`; in Production, writes `curated`'s declared tables and connects to the warehouse over JDBC through the `redshift-serverless` endpoint |
| a processing or training job | the project role, the project's subnets and group, network isolation; the image pulled by SageMaker's side from Production's registry by digest; inputs and outputs staged by the platform from the project prefix | the job role, the job subnets and group, network isolation, the data key; inputs and outputs staged from the outputs bucket; no lake bucket, ever (D13) |
| a Python or Bash task on the worker | the project role in the project's network: AWS through the VPC endpoints, S3 through the gateway endpoint, no internet, no proxy | `awsds-<env>-wf-<key>` on `awsds-<env>-wf-workers` in the private subnets: the interface endpoints of `workloads-egress/` (`egress/` in Staging), the S3 gateway, the declared prefixes of the outputs bucket, the data key for its XCom; no internet, no proxy |
| Athena | a person in the project's query editor, as the project role on the project's enforced workgroup: the project's tables; the lake's links once the project role holds a grant | the persona through `awsds-prod-athena` on `app_outputs` and the lake's `public` and `internal` tables, from any network; Staging's persona set holds no Athena action; no task in the template calls Athena, and the execution role holds no grant for it |
| Redshift | the sandbox warehouse through the project's connection, the Data page as the access role and a notebook through it (`redshift-connection.md` §J); the governed warehouse through the datashare alone, since Sandbox does not peer with `VPC-Workloads` | Production's job role over JDBC as `IAMR:awsds-prod-job-exec`; the deploy role through the Data API for the DDL; the persona refused a session (`DenyMintingARedshiftDatabaseSession`) |
| S3 | the project prefix; the sandbox lake through the project's S3 connection; the drop-box's `PutObject` as the persona from a laptop, never read back | the outputs and derived buckets; the lake's buckets only through Lake Formation's credentials in a Glue job; the release store read by the runner's own role |
| GitLab | a space clones over the VPN's names, with a persona PAT (INT-09, owed) | the deploy runner clones the mirror with the job token; no task reaches it |
| the internet | a space through the proxy's allow-list; a job and a worker never | never: anything a task needs is in the image, in the zip or behind an endpoint |

---

## K. Production data while developing in Sandbox

The question a data scientist asks first is how to develop against real data without copying
Production into Sandbox. The answer here is that there is no Production data to copy: the governed
product lives in the lake, not in Production, and every account reads that one lake in place.

- **The governed lake is the same table in every stage.** Sandbox, Staging and Production read the lake
  account's tables through one TBAC share, `restricted` excluded, so what a data scientist reads in
  Sandbox is what the application reads in Production, in place: no copy of Production's data is made
  for development (Lesson 1). Today the share's local re-grants in Sandbox name the persona, whose set
  carries no Athena action since D19's revision, and no project role holds a grant (6f decision 1), so a
  governed lake row is read from Sandbox through the warehouse's datashare alone, and the first read of
  a governed table by an application is Staging's leg.
- **Production's outputs stay in Production.** The persona reads the application's result file under
  `<app>/outbox/` and its `app_outputs` tables through Athena, and nothing else of `awsds-prod-outputs`;
  a read outside the named prefixes is refused by the bucket policy
  (`DenyThePersonaReadsOutsideTheNamedPrefixes`). A result copied into a project or the sandbox lake is
  the data scientist's own copy of something the persona may read, under the Sandbox perimeter, and its
  classification follows it; nothing in the design moves it for them.
- **The application develops on synthetic data.** `samples/` drives the tests, the smoke build, the
  `test` run and the inbox seed in every account; the Glue script's governed read is tested as the
  query it builds, over a mocked column list. A real governed input enters the loop as a column list
  the application reads (`GOVERNED_COLUMNS`), checked against the table at Staging's leg, and as the
  rows every consumer reads. A real file of the data scientist's own reaches Production's lake through
  the drop-box, `s3://awsds-data-dropbox/incoming/YYYY/MM/DD/<file>.csv`, written from Sandbox and never
  read back, which Production's pickup curates.
- **A product's shape is decided before its data exists.** The table a new application will write is
  declared and tagged in the register before the promotion that writes it, from the schema the data
  scientist proposed; the classification decides who reads it, and a `restricted` column is read only
  by whom a register row names.
- **The warehouse's governed data reaches a project through the datashare**, as the project's access
  role, never by a copy; the sandbox warehouse's schemas are where a project writes.
- **A proof needing Production itself** is a Staging run: Staging reads the governed lake through its
  own share and writes its own buckets and tables, so an integration test meets the definitions, rows
  and grants Production reads with nothing of Production touched (`TM-25`).

---

## Z. Standard and specific

What every application takes from the template unchanged, and what each one sets. A line in the first
column changed in one application diverges from the platform the pipeline and the render expect, and
the divergence shows at a deploy, a render or a lint, never at the edit.

| Standard, unchanged | Specific, set per application |
|---|---|
| the layout of §R; the `include:` of `awsds/ci-gates` and its commit; the stages, the runner tags, the `.promotion` template, the `rules` on a tag, the `resource_group`s, the manual gates and their `needs`, the dotenv reports and their names | `applicationName`, `IMAGE_REPO`, `SCAN_REPOSITORY`, `GATES_UV_PROJECTS`, the release's name, the `resource_group` of `test-deploy`, `LINT_ALGORITHM_REPOSITORIES` (empty without a training task), the `--app` and the slice paths on the promotion jobs |
| the Dockerfile's shape: `FROM` base by digest, the lock into a virtual environment, no code, the `app` and `smoke` targets, the job's command | the base digest (the developer's pin), a system package, the sample the smoke runs, the files the smoke checks |
| the manifest's stages `dev` and `test`, their `environment_variables` names, `default.s3_shared` and `default.workflow_serverless`, `workflow.create` and the `test` stage's `workflow.run` | the content items and their includes, the workflows and their zips, the target directories under `<app>/`, which workflow `test` runs |
| the CLI's variables and the render table's classes; the D13 settings on every job; `retries: 0`; the result file by an S3 operator; the lint's rules and the ceiling's instance types | each workflow's tasks, operators, arguments and prefixes; the Glue jobs' names and arguments; `GOVERNED_COLUMNS` and the tables' columns; the chains, their order and their cron |
| the processing job's contract (`/opt/ml/processing/`, `sudo chown`, `python -m`); the worker's package shape (one module, one zip per workflow, the worker's boto3) | the package, the command's arguments, the callables and their `op_kwargs` |
| the tests' shape: pytest offline, doubles for `awsglue`, `pyspark` and `boto3`, `samples/` as the fixture, the lint in `test` | the cases: the transformation's expected output, the column list, the statements |
| the application slice's shape (the job role, the Glue connection, Glue 6.0, `G.1X`, two workers, `max_concurrent_runs = 1`, the release prefix, `release.tf`'s validation) | the Glue jobs, their `default_arguments`, the tables and their columns, the warehouse load |
| the orchestration slice's base (the roles, the log groups, the workers' group, the schedule group, the failure rules, the module's tag) | the `applications` entries (`glue_jobs`, the job-name prefixes, `reads`, `writes`, `deletes`), the `chain_specs` entries, the ASL files, the `bridges` |
| the grants' shape in `foundation/`, `sagemaker/`, `data/`, `identity/sso/` and `registry/` | the names inside them: the repository, the Glue job names, the training and model prefixes, the package group, the outbox prefix |
| the readings of §V and the instruments | the chains to start, the table to read back, the model jobs |

---

*Stages: [stage-08-cicd-pipelines.md](../stages/stage-08-cicd-pipelines.md) ·
[stage-09-deployment-targets.md](../stages/stage-09-deployment-targets.md) ·
[stage-10-orchestration-promotion.md](../stages/stage-10-orchestration-promotion.md) · The first
promotion: [promotion.md](promotion.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
