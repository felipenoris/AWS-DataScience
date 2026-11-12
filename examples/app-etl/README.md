# app-etl

Every CSV in a directory becomes a Parquet table and a JSON summary. The first application of the AWS
Data Science environment, and the template its other applications start from: the GitLab project
`awsds/app-etl` received this tree from the infrastructure repository's `examples/app-etl/`
(Stage 8 step 2.2) and holds it since. Since step 2.5 it is a SageMaker application (D41): a manifest
the CI/CD CLI deploys to a project, and its workflows: `app-etl`, five tasks over the trades, the last
listing the product in the SageMaker Catalog (Stage 19);
`app-etl-train`, an XGBoost model trained on what `app-etl` prepared (Stage 10 step 5.1); and
`app-etl-warehouse`, Production's load of the product into the governed warehouse (Stage 9 step 9.4),
which Production's project alone receives. The cycle an application on this template follows, from a
space to Production, hand by hand, is `docs/plan/runbooks/sagemaker-application.md` in the infrastructure
repository.

| Path | What it is |
|---|---|
| `src/app_etl/` | the code of the processing job: `pipeline.py` the transformation, `__main__.py` the command; the job reads it as its input, never from the image (D28 class 2d) |
| `code/app_etl_tasks.py` | the worker's tasks: `summarize`, the run's report from the job's summaries; `publish`, the product listed in the SageMaker Catalog; and `evaluate`, a training job's metrics written beside its model; the pipeline zips the file once per workflow, `code/app-etl.zip` and `code/app-etl-train.zip`, each workflow's `code` (class 2b) |
| `glue/transform.py` | the Glue job's script, the Spark transform over the trades: the CSV the processing job reads, the application's table and the training sets (class 2c) |
| `glue/load_warehouse.py` | Production's warehouse load: the product table into `trades.trades_notional` of the database `governed`, over JDBC as the project's role (class 2c) |
| `warehouse/trades.sql` | the warehouse table's DDL, run by the pipeline's manual job `production-warehouse-ddl` through the Data API as the deploy role, its owner (Stage 9 decision 6) |
| `workflows/` | the three workflow definitions, in the CI/CD CLI's notation |
| `manifest.yaml` | the application: its content, the folders the CLI copies and the catalog it carries, and its three stages, one account each: `dev`, the Sandbox project it is developed in, and `staging` and `prod`, each account's deployment project (the infrastructure repository's Stage 19 step 4.9) |
| `product.json` | the product the application declares: the catalog resources a release must carry and the ones it may, which the pipeline's `bundle` job holds the `dev` project's export to |
| `scripts/dev-cli.sh` | the CI/CD CLI for the `dev` stage in a space: the house image's CLI by its path, its domain lookup answered by `DOMAIN_ID`, the other stages' variables given a placeholder; no storage item names `scripts/`, so the bundle never carries it |
| `scripts/check-catalog-export.py` | the guard on a bundle's catalog export against `product.json`, run by the `bundle` job |
| `tests/` | pytest, offline, against `samples/`; the Glue script, the worker's tasks and `scripts/dev-cli.sh` run over doubles |
| `samples/` | synthetic trades: the input of the image's smoke test, of a Sandbox job and of the workflow's `inbox/` |
| `Dockerfile` | the application image, which is also the job image: `FROM` base by digest, the lock's dependencies in a virtual environment of their own on base's CPython 3.12, no code; target `app` is the image, `smoke` runs the job's command on it with `src/` mounted as the job's input |
| `.gitlab-ci.yml` | the pipeline, with the shared gates from `awsds/ci-gates` |
| `pyproject.toml`, `uv.lock` | the project and its lock; the resolver ignores anything published after `exclude-newer` |

No Terraform runs the application: the CI/CD CLI deploys it into a project in every account, the `dev`
project from a space and each deployment target's project from the pipeline (the infrastructure
repository's Stage 19 decision 6 (b)). What that repository holds for it is each target's project
prerequisites and the chains that start its workflows on a schedule, `terraform-live/<env>/studio/` and
`terraform-live/<env>/chains/`.

## The workflow

Five tasks, in order, every path under the project's shared prefix,
`{proj.connection.default.s3_shared.s3Uri}app-etl/`:

| Task | Operator | Reads | Writes |
|---|---|---|---|
| `transform` | `GlueJobOperator`: the Glue job `app-etl-<project id>`, created or updated by the task from `create_job_kwargs` (`update_config: true`), running `glue/transform.py` | `inbox/` | `work/glue/trades.csv`, one CSV with each trade's notional; on a governed read, `work/glue/trades.source.json` beside it, the table and the snapshot read |
| `process` | `SageMakerProcessingOperator`: a processing job on the application image, network-isolated, its volume under the project key, `src/` as its input `code`, the command `cd /opt/ml/processing/code && python -m app_etl` | `work/glue/` | `work/job/`: `trades.parquet` and `trades.summary.json`, which carries the governed read's record as `source` |
| `summarize` | `PythonOperator` on the worker: `app_etl_tasks.summarize`, from `code/app-etl.zip` | `work/job/*.summary.json` | its XCom, the run's report as JSON, each table's `source` with it |
| `write_result` | `S3CreateObjectOperator`: the XCom of `summarize`, pulled in its template | | `outbox/report.json` |
| `publish` | `PythonOperator` on the worker: `app_etl_tasks.publish`, as the project role through the `datazone` endpoint, in the domain and project the deploy substitutes (`{domain.id}`, `{proj.id}`), where the stage variable `PUBLISH_LISTING` is `true`: Production alone, once the CLI deploys it; in `dev` the task returns at once (Stage 19 decision 20 (b)) | the project's data source over `{env.PRODUCT_DATABASE}`, run and followed to `SUCCESS`; the inventory asset of `trades_notional` | the asset's latest revision as a listing, read `ACTIVE`; its XCom, the identifiers as JSON |

Every run overwrites the same keys: the Glue job keeps one file under `work/glue/` (Spark names the
file it writes, so the script copies it to `trades.csv` and deletes the rest), the processing job names
its outputs after that file, and the report replaces the previous one. The sample reaches `inbox/` by
the manifest's `samples` item, so a run in `dev` needs no input of its own.

The Glue job also writes `tables/trades_notional/`, the application's table as Parquet, read back and
counted against the rows it read, and `work/train/`, the training sets in XGBoost's CSV layout (the
label first, no header, every fifth row held out for validation) with `batch/batch.csv`, the features
alone. Every stage reads the inbox: the CLI deploys one definition to every project, and the workflow
names no governed table. The script also reads one, with `--SOURCE_TABLE`: the columns
`GOVERNED_COLUMNS` names, on an Iceberg catalog the job's `--conf` would declare over the lake
account's, at one snapshot, the one `--SOURCE_SNAPSHOT` names or else the table's current one, which
the job records beside the CSV and the summary and the report carry as `source`. The Terraform path
gave the argument to the job it declared in Staging and Production (Stage 9 step 8.5); under the CLI
the read waits for a workflow that passes it and a project role that holds the table (the
infrastructure repository's Stage 19, decision due 22). The unit tests mock the governed table with
the list's columns and compare the query it builds, so a change to `GOVERNED_COLUMNS` changes `SCHEMA`
and the expected queries in `tests/test_glue_script.py` with it.

The product (Stage 19 decision 2): with `--TABLE_DATABASE`, the stage variable `PRODUCT_DATABASE`, and
`--TABLE_NAME trades_notional`, the Glue job also writes the result as an Iceberg table of the project's
database, `glue_catalog.<database>.trades_notional` on the Spark catalog the job's `--conf` declares
over the account's Glue Data Catalog (`--datalake-formats iceberg`), read back and counted. The table is
the job's own `CreateTable` under the database's conditioned `CREATE_TABLE`, and a second run replaces
its data and keeps the table, so the listing `publish` makes and the grants a subscription writes
survive the runs. The source's run needs `datazone:StartDataSourceRun`, which the blueprint's policies
do not grant the project role and the house grant `terraform-live/sandbox/workflows/` does (Stage 19
1.1). The database is created in each project before the first deploy, the same name in every project,
never by the application. The same `--conf` turns on the OpenLineage listener Stage 18 step 7.1 measured
(Stage 19 decision 10): the job posts its lineage to the domain as the project role through the
`datazone` endpoint, naming the domain by `{domain.id}` and the account by the stage variable
`ACCOUNT_ID`; a post that fails leaves the job's result alone.

`app-etl-train` runs two tasks after `app-etl`: `train`, a SageMaker training job on AWS's XGBoost 3.0-5
by digest (`{env.TRAINING_IMAGE_URI}`), `ml.m5.large`, network-isolated in the job subnets, its volume
and its model under the project's key, the model under `models/`; and `evaluate`, which writes
`models/<job>/evaluation.json`, SageMaker's model-quality statistics with the validation RMSE and the
batch's row count. The training job's name comes to `evaluate` through `train`'s XCom, since
`{{ ts_nodash }}` is midnight in a manual run and two runs of one day would collide on it. The CLI
creates the workflow in `dev` and does not run it.

`app-etl-warehouse` is one Glue task, `load`: the job `app-etl-load-<project id>`, created by the
task as `app-etl`'s is, reads the product table and writes it into the governed warehouse, whose names
are the task's arguments. The manifest lists the workflow and the `prod` stage's bootstrap alone
creates it, since the warehouse is Production's; its chain starts it in a sitting that raises the
warehouse's compute.

The project's values are the CLI's variables (`{proj.id}`, `{proj.iam_role_arn}`,
`{proj.connection.default.s3_shared.s3Uri}`, `{domain.id}`, `{domain.region}`). What no project holds is a stage
variable, `{env.VAR}` in the workflow and `${VAR}` in the manifest, read from the shell:
`JOB_IMAGE_URI`, the image by digest; `SUBNET_AZ1` and `SUBNET_AZ2`, the domain's subnets, which name
the Glue connections and the job's network; `PROJECT_SG`, the project's own security group,
`DEV_PROJECT_SG` in the shell; `PROJECT_KEY_ARN`, the ARN of the project's own KMS
key (`kmsKeyArn` in its Tooling environment, whose id `awsds-workflows values` prints as
`PROJECT_KEY_ID`), `DEV_PROJECT_KEY_ARN` in the shell, the processing job's
`VolumeKmsKeyId`, which Sandbox's D13 boundary requires of every job
(`DenySageMakerJobsWithoutVolumeEncryption`); `PRODUCT_DATABASE`, the product's database, and
`PUBLISH_LISTING`, whether the run lists its product, both literals: `app_etl`, the same name in every
account's catalog, and `true` in `prod` alone, since Production alone lists the product; `ACCOUNT_ID`,
the account the job's lineage names. The `staging` and `prod` stages read theirs under the names
`STAGING_*` and `PROD_*`, which the pipeline's leg fills from the project's Tooling environment. The CLI
writes each `{env.VAR}` into the deployed definition as a parameter and fills it on a run it starts, as
the run's `OverrideParameters`. A chain's machine fills it too, from the record the leg keeps of the
stage's variables at each deploy; a run started in the portal has no value for them and fails before
its first task.

## Working on it

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run app-etl --input samples --output out
```

`uv run ruff check` and `uv run ruff format --check` are what the pipeline runs; `uv run pdoc app_etl`
serves the documentation the default branch publishes to Pages.

The workflow tooling is [`awsds-workflows`](https://github.com/felipenoris/awsds-workflows), installed
as a tool (`docs/plan/runbooks/serverless-workflows.md` §T). Its lint reads the manifest and the
workflow against the rules of a SageMaker application, offline; the pipeline runs it on every push,
with the application's repository as the one a literal `ImageUri` may name and the instance types of
the ceiling (`LINT_INSTANCE_TYPES` in `.gitlab-ci.yml`) as the ones a processing job may ask for:

```bash
awsds-workflows lint . --image-repository awsds-prod-ecr-app-etl --instance-type ml.t3.medium --instance-type ml.t3.large --instance-type ml.t3.xlarge --instance-type ml.m5.large --instance-type ml.m5.xlarge --instance-type ml.c5.large --instance-type ml.c5.xlarge
```

The deploy to the `dev` project runs the CI/CD CLI (`aws-smus-cicd-cli` 1.0.9) from a space on the house
image, as the project's role, with the shell variables the manifest reads, `JOB_IMAGE_URI` being the image
the last release's notes name. The workers' packages come first, one per workflow with a `code` field,
since `bundle` and `deploy` copy and never build; then the deploy, which copies the folders and creates
both workflows, and a run:

```bash
python3 -m zipfile -c code/app-etl.zip code/app_etl_tasks.py
```

```bash
python3 -m zipfile -c code/app-etl-train.zip code/app_etl_tasks.py
```

```bash
scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
```

```bash
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-etl
```

`scripts/dev-cli.sh` passes every argument to the CLI and answers three things for it. The CLI refuses
a manifest with an unset `${VAR}`, whatever the stage it deploys, so the script gives the `staging` and
`prod` stages' names a placeholder when the shell has none. The CLI is the house
image's, run by its path (`$AWSDS_PYTHON_ENV/bin/python`), since up to the house image's version 10 the
SageMaker Distribution's own 1.0.8 comes first on a space's `PATH` and refuses the manifest's `code`
field. And the CLI's domain lookup by name, a `ListDomains` call that DataZone refuses to a project's
role, is answered with `DOMAIN_ID` ([issue 413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413) asks the CLI to use the manifest's id). The
script refuses to start when `AWSDS_PYTHON_ENV` or `DOMAIN_ID` is unset. `--skip-validation` because the
CLI's pre-deployment validation simulates the IAM calls without their context keys and fails here every
time; `--no-events` because the event it would publish has no handler in 1.0.9. Which identity runs the
`dev` deploy, and from where, is Stage 8 decision 22; the session around it is the infrastructure
repository's `docs/plan/runbooks/sagemaker-application.md` §D.

## The pipeline

| Ref | Jobs | Runner |
|---|---|---|
| any branch | `test` (`uv sync --locked`, ruff, pytest, the workflow lint), `secret_detection` and its gate, `pip-audit` | the test runner, no AWS identity |
| `main` | the same, and `pages` | the test runner |
| a tag `v<semver>` | `test`, `pip-audit`, `build-image` (smoke, then the push as `v<semver>-<short sha>`), `scan-gate`, informative: it may fail and the pipeline goes on; `build-task-code` (the workers' zips); `bundle` (the release's bundle, made from the tag's files and the `dev` project's catalog, held to `product.json`; nothing is deployed in Sandbox); `store-bundle` (the bundle to `awsds-prod-releases`); `release` (the tag's GitLab release); the promotion: `staging-gate` (manual), `staging-check` (Staging's `egress/`, the user's to raise, and its deployment project read), `staging-deploy` (the CLI's deploy into the project), `staging-test` (both chains, the report and the product table), `staging-model` (the batch transform of Staging's model), `production-check` (Production's project and the deploy role's membership), `production-gate` (manual), `production-deploy` (the CLI's deploy, whose bootstrap runs `app-etl`); then Production's manual jobs `production-warehouse-ddl`, `production-register` and `production-approve`, and `production-transform` after the approval | the test runner, the build runner, and the deploy runner for `bundle` and the promotion |

A release is a tag `v<major>.<minor>.<patch>` on `main`, which only a Maintainer can create: the tag is
protected, and that protection is the release gate. ECR's tags are immutable, so a second pipeline for
the same tag is refused at the push; the short sha keeps two builds of one release apart. A tag whose
bundle fails gets no release, and the release's first run is Staging's leg: every promotion crosses an
account, and the pipeline deploys nothing in Sandbox (Stage 19 decision 19 (c)).

`bundle` runs as `awsds-deploy-sandbox-test`, a role that reads the `dev` project and its catalog and
writes nothing, and reads the GitLab project's CI/CD variables `DOMAIN_ID`, `DOMAIN_REGION` and
`DEV_PROJECT_NAME`. The CLI refuses a manifest with an unset `${VAR}`, so the job gives every name it
has no value for a placeholder. The role is a member of the `dev` project: `bundle` resolves the
project its stage names, and for a project its caller cannot read it logs *"Failed to get project
connections"* and still writes the bundle, so the job fails on that line. The bundle carries the
project's catalog as `catalog/catalog_export.json`, whatever the project owns: `product.json` declares
what a release carries, and `scripts/check-catalog-export.py` fails a bundle with a resource outside it,
without the product's asset or with no export at all. A resource the scientist adds to the product in
the `dev` project, a data product or a glossary term, joins `product.json` in the same merge request.
The bundle's SHA256 and the image go down
the pipeline as a dotenv report, and the release's notes name them. `bundle` resolves an `include` as a
file or a directory and not as a glob (`code/*.zip` is "Pattern not found" with the zip present, while
`deploy` expands it; read in 1.0.9's code and run offline on 2026-10-16), so the manifest names the zip
by its name. The job needs the hub and the deploy runner, and no Sandbox endpoint.

The promotion (Stage 8 step 3; Stage 19 step 4.9) runs on the deploy runner, each job cloning
`awsds/infrastructure` with the job token (Stage 8 decision 2), where the scripts it calls live. Staging's
egress and its deployment project are read; the bundle is read as the runner's own role and checked
against the SHA256 `bundle` passed; `scripts/deploy-application.py` extracts it beside the tag's
manifest, fills the stage's variables from the project's Tooling environment and runs the CLI's `deploy`,
which copies the files under the project's shared prefix, imports the catalog without listing anything
and creates or updates the stage's workflows; the script reads the deploy's log beyond its exit status
and records the stage's variables for the chains. The leg starts each chain's machine and follows it,
reads the report and the product table's metadata, `scripts/model-chain.py` serves Staging's own model by
a batch transform and counts the predictions, and nothing is torn down: Staging's `make down` is the
user's. Production's project is read before the manual gate, the deploy role's membership of it
included, and gets the same bundle and image; its deploy's bootstrap runs `app-etl` and follows the run,
whose last task lists the product. After
`production-deploy`, three jobs wait for a person: the warehouse's DDL once the compute is up; the
registration of the newest completed `app-etl-train` job as `PendingManualApproval`, once Production's
train chain has run; and its approval, the deployment manager's pause, which the batch transform of the
approved version follows. The jobs need the hub and the deploy runner, and a Production run
`production/workloads-egress/` (`make up ENV=production ONLY=workloads-egress`).

## The job contract

A SageMaker processing job runs the image with networking off, as the image's user, on mounts the platform
creates owned by root with mode 755: the code at `/opt/ml/processing/code`, the input and the output.
Its command therefore opens with the chown the image's passwordless `sudo` allows, then runs the code
from its mount:

```bash
sudo -n chown "$(id -u)" /opt/ml/processing/output && cd /opt/ml/processing/code && exec python -m app_etl --input /opt/ml/processing/input --output /opt/ml/processing/output
```

What the command prints lands in the account's shared processing-job log group, so it prints versions,
counts and file names, never a cell of data.
