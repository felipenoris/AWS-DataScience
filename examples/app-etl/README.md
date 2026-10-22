# app-etl

Every CSV in a directory becomes a Parquet table and a JSON summary. The first application of the AWS
Data Science environment, and the template its other applications start from: the GitLab project
`awsds/app-etl` received this tree from the infrastructure repository's `examples/app-etl/`
(Stage 8 step 2.2) and holds it since. Since step 2.5 it is a SageMaker application (D41): a manifest
the CI/CD CLI deploys to a project, and a workflow of four tasks.

| Path | What it is |
|---|---|
| `src/app_etl/` | the code of the processing job: `pipeline.py` the transformation, `__main__.py` the command; the job reads it as its input, never from the image (D28 class 2d) |
| `code/app_etl_tasks.py` | the worker's task, `summarize`: the run's report from the job's summaries; the pipeline zips it as `code/app-etl.zip`, the workflow's `code` (class 2b) |
| `glue/transform.py` | the Glue job's script, the Spark transform over the trades (class 2c) |
| `workflows/app-etl.yaml` | the workflow definition, in the CI/CD CLI's notation |
| `manifest.yaml` | the application: its content, the folders the CLI copies, and its stages `dev` and `test` |
| `tests/` | pytest, offline, against `samples/`; the Glue script and the worker's task run over doubles |
| `samples/` | synthetic trades: the input of the image's smoke test, of a Sandbox job and of the workflow's `inbox/` |
| `Dockerfile` | the application image, which is also the job image: `FROM` base by digest, the lock's dependencies in a virtual environment of their own on base's CPython 3.12, no code; target `app` is the image, `smoke` runs the job's command on it with `src/` mounted as the job's input |
| `.gitlab-ci.yml` | the pipeline, with the shared gates from `awsds/ci-gates` |
| `pyproject.toml`, `uv.lock` | the project and its lock; the resolver ignores anything published after `exclude-newer` |

The Terraform that runs the application is not here: each environment's slice is
`terraform-live/<env>/app/app-etl/` in the infrastructure repository (Stage 8 decision 12), applied by the
pipeline; Sandbox's retired with decision 21, the `dev` and `test` projects being where the CLI deploys it.

## The workflow

Four tasks, in order, every path under the project's shared prefix,
`{proj.connection.default.s3_shared.s3Uri}app-etl/`:

| Task | Operator | Reads | Writes |
|---|---|---|---|
| `transform` | `GlueJobOperator`: the Glue job `app-etl-<project id>`, created or updated by the task from `create_job_kwargs` (`update_config: true`), running `glue/transform.py` | `inbox/` | `work/glue/trades.csv`, one CSV with each trade's notional |
| `process` | `SageMakerProcessingOperator`: a processing job on the application image, network-isolated, its volume under the project key, `src/` as its input `code`, the command `cd /opt/ml/processing/code && python -m app_etl` | `work/glue/` | `work/job/`: `trades.parquet` and `trades.summary.json` |
| `summarize` | `PythonOperator` on the worker: `app_etl_tasks.summarize`, from `code/app-etl.zip` | `work/job/*.summary.json` | its XCom, the run's report as JSON |
| `write_result` | `S3CreateObjectOperator`: the XCom of `summarize`, pulled in its template | | `outbox/report.json` |

Every run overwrites the same keys: the Glue job keeps one file under `work/glue/` (Spark names the
file it writes, so the script copies it to `trades.csv` and deletes the rest), the processing job names
its outputs after that file, and the report replaces the previous one. The sample reaches `inbox/` by
the manifest's `samples` item, so a `test` run needs no input of its own.

The project's values are the CLI's variables (`{proj.id}`, `{proj.iam_role_arn}`,
`{proj.connection.default.s3_shared.s3Uri}`, `{domain.region}`). What no project holds is a stage
variable, `{env.VAR}` in the workflow and `${VAR}` in the manifest, read from the shell:
`JOB_IMAGE_URI`, the image by digest; `SUBNET_AZ1` and `SUBNET_AZ2`, the domain's subnets, which name
the Glue connections and the job's network; `PROJECT_SG`, the project's own security group,
`DEV_PROJECT_SG` or `TEST_PROJECT_SG` in the shell; `PROJECT_KEY_ARN`, the ARN of the project's own KMS
key (`kmsKeyArn` in its Tooling environment, whose id `awsds-workflows values` prints as
`PROJECT_KEY_ID`), `DEV_PROJECT_KEY_ARN` or `TEST_PROJECT_KEY_ARN` in the shell, the processing job's
`VolumeKmsKeyId`, which Sandbox's D13 boundary requires of every job
(`DenySageMakerJobsWithoutVolumeEncryption`). The CLI fills them on a run it starts, as the run's
`OverrideParameters`; a run started in the portal has no value for them.

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

The deploy to the `dev` project runs the CI/CD CLI (`aws-smus-cicd-cli` 1.0.9) with the shell variables
the manifest reads, `JOB_IMAGE_URI` being the image the last release's notes name. The worker's package
comes first, since `bundle` and `deploy` copy and never build; then the deploy, which copies the folders
and creates the workflow, and a run:

```bash
python3 -m zipfile -c code/app-etl.zip code/app_etl_tasks.py
```

```bash
aws-smus-cicd-cli deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
```

```bash
aws-smus-cicd-cli run --manifest manifest.yaml --targets dev --workflow app-etl
```

`--skip-validation` because the CLI's pre-deployment validation simulates the IAM calls without their
context keys and fails here every time; `--no-events` because the event it would publish has no
handler in 1.0.9. Which identity runs the `dev` deploy, and from where, is Stage 8 decision 22.

## The pipeline

| Ref | Jobs | Runner |
|---|---|---|
| any branch | `test` (`uv sync --locked`, ruff, pytest, the workflow lint), `secret_detection` and its gate, `pip-audit` | the test runner, no AWS identity |
| `main` | the same, and `pages` | the test runner |
| a tag `v<semver>` | `test`, `pip-audit`, `build-image` (smoke, then the push as `v<semver>-<short sha>`), `scan-gate`, informative: it may fail and the pipeline goes on; `build-task-code` (the worker's zip); `test-deploy` (the bundle, the `test` project's prefix emptied, the deploy and the run); `store-bundle` (the bundle to `awsds-prod-releases`); `release` (the tag's GitLab release); the promotion: `staging-up`, `staging-deploy`, `staging-test`, `staging-down` (always), `production-plan`, `production-gate` (manual), `production-deploy` | the test runner, the build runner, and the deploy runner for `test-deploy` and the promotion |

A release is a tag `v<major>.<minor>.<patch>` on `main`, which only a Maintainer can create: the tag is
protected, and that protection is the release gate. ECR's tags are immutable, so a second pipeline for
the same tag is refused at the push; the short sha keeps two builds of one release apart. A tag whose
`test` run fails gets no release.

`test-deploy` runs as `awsds-deploy-sandbox-test` (Stage 8 decision 19) and reads the GitLab project's
CI/CD variables `DOMAIN_ID`, `DOMAIN_REGION`, `DEV_PROJECT_NAME`, `TEST_PROJECT_NAME`, `SUBNET_AZ1`,
`SUBNET_AZ2`, `DEV_PROJECT_SG`, `TEST_PROJECT_SG`, `DEV_PROJECT_KEY_ARN`, `TEST_PROJECT_KEY_ARN` and
`TEST_PROJECT_S3_URI`, the `test` project's `s3Uri` of `default.s3_shared`. Its run needs Sandbox's
egress up (`make up ENV=sandbox ONLY=egress`, as the infrastructure user), which the job reads before it
deploys; the bundle's SHA256 and the image go down the pipeline as a dotenv report, and the release's
notes name them. `bundle` resolves an `include` as a file or a directory and not as a glob (`code/*.zip`
is "Pattern not found" with the zip present, while `deploy` expands it; read in 1.0.9's code and run
offline on 2026-10-16), so the manifest names the zip by its name.

The promotion (Stage 8 step 3) runs on the deploy runner, each job cloning `awsds/infrastructure` with the
job token (Stage 8 decision 2), where the slices and the two scripts it calls live. Staging's egress is
raised; the bundle is read as the runner's own role and checked against the SHA256 `test-deploy` passed;
`scripts/release-application.py` writes its tree into the account's outputs bucket with the workflow
rendered by `scripts/render-workflow.py`, then the application and orchestration slices apply; the leg
starts the chain's machine and follows it, and Staging is torn down whatever the outcome. Production
gets a plan, the manual gate and the same bundle and image. The jobs need the hub and the deploy runner,
and a Production run `production/workloads-egress/` (`make up ENV=production`). Written 2026-10-22, not
yet run.

Read on 2026-10-16 and not yet run: the first tag's pipeline, which shows whether the `test` run reaches
`outbox/report.json`, the XCom of `summarize` pulled in `write_result`'s template, the project role's
pull of the image and its copy in the Glue script, and the release's notes on the lab's GitLab
(Stage 8 verifications xix, xx, xxiii, xxiv and xxvi).

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
