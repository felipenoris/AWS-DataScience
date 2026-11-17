# app-ml

A churn table becomes XGBoost's training and scoring sets, and the model trained on them travels from
the Sandbox project it is trained in to Staging and Production. The second application of the AWS Data
Science environment, on the template `examples/app-etl` set (the infrastructure repository's Stage 17
pass 9), and like it a SageMaker application (D41): a manifest the CI/CD CLI deploys to a project, and
its workflows. The GitLab project `awsds/app-ml` receives this tree from the infrastructure
repository's `examples/app-ml/` (Stage 17 step 9.5).

The model is trained in the `dev` project alone. A release's bundle carries it; each target proposes it
as a version of the account's model package group, `PendingManualApproval`; the account's deploy role
approves the version that carries the release's hash; and a batch transform serves that version and
checks its AUC on a labelled holdout the training never reads.

| Path | What it is |
|---|---|
| `src/app_ml/` | the processing jobs' code, the standard library alone: `prepare.py`, whose `train` mode writes XGBoost's training and validation sets from `churn.csv` and whose `score` mode writes the batch set and its labels from `holdout.csv`. The job reads it as its input, never from the image (D28 class 2d) |
| `code/app_ml_tasks/` | the worker's tasks, a project with a lock of its own (`code/pyproject.toml`, `code/uv.lock`): `evaluate`, `publish`, `register`, `resolve` and `check`, each a workflow's Python task, and `track`, the module app-ml-train's Bash task runs with the MLflow client |
| `code/app-ml-*.zip` | built before a bundle and never committed, each workflow's `code` (class 2b): `app-ml-train.zip` is `awsds-workflows package-task` over `code/`, the package and the MLflow client's closure; the other two are the package alone |
| `workflows/` | the three workflow definitions, in the CI/CD CLI's notation |
| `manifest.yaml` | the application: four folders of this tree, the item `model` that reads the `dev` project's candidate into a bundle, the three workflows, and three stages, one account each |
| `samples/` | the synthetic churn table (`churn.csv`, 400 rows) and the labelled holdout (`holdout.csv`, 200 other customers), deployed to each project's `app-ml/inbox/` |
| `scripts/make-samples.py` | the generator of `samples/`, seed `20261117` |
| `scripts/training-source.py` | `TRAINING_SOURCE`: the SHA-256 of git's listing of `src/`, `samples/` and `workflows/app-ml-train.yaml` at HEAD, or `dirty` |
| `scripts/dev-cli.sh` | the CI/CD CLI for the `dev` stage in a space, app-etl's script with `TRAINING_SOURCE` set on every call and `MLFLOW_APP_ARN` required |
| `scripts/check-model-bundle.py` | the guard on a release's model, run by the `bundle` job |
| `tests/` | pytest, offline: the job's code against `samples/`; the worker's tasks over boto3 clients stubbed at the worker's botocore 1.43.1; the track task over a double of MLflow; the scripts over git repositories and a double of the CLI built in a temporary folder. The tests that need git skip where none is on `PATH` |
| `Dockerfile` | the job image both prepare tasks run in: `FROM` base by digest; the runtime set is empty, so the image is base's CPython 3.12 and a virtual environment with nothing in it; `smoke` runs both modes on it |
| `.gitlab-ci.yml` | the pipeline, with the shared gates from `awsds/ci-gates` |
| `pyproject.toml`, `uv.lock` | the project, its lock and the tests' tools, the worker's boto3 among them; in both projects the resolver ignores anything published after `exclude-newer` |

The model's image is AWS's XGBoost 3.0-5 by digest, `TRAINING_IMAGE_URI`, which trains and serves it.
No Terraform runs the application: the CI/CD CLI deploys it into a project in every account. What the
infrastructure repository holds for it is each target's model package group, the project roles' and
deploy roles' statements, and the chains that start its workflows, `terraform-live/<env>/chains/`.

## The workflows

Every job runs in the project's subnets with network isolation, its volume and output encrypted with
the project's key and tagged with the project's id (D13). The lint reads the processing, training and
transform requests; the model is created by a Python task, whose CreateModel request the tests assert.
Every task has `retries: 0`, and every path below is under the project's shared prefix.

**app-ml-train**, which the `dev` stage alone creates:

| Task | Runs | What it does |
|---|---|---|
| `prepare` | a processing job, `ml.t3.medium` | `python -m app_ml.prepare train` over `app-ml/inbox/churn.csv` alone: `app-ml/work/train/train/train.csv` and `app-ml/work/train/validation/validation.csv`, one row in five to validation, the label first, no header |
| `train` | a training job, `ml.m5.large` | XGBoost, `binary:logistic`, `eval_metric` `auc`, 50 rounds of depth 3; the archive under `app-ml/models/<job>/output/` |
| `evaluate` | Python | the job's final `validation:auc` written as `app-ml/models/<job>/evaluation.json`, SageMaker's model-quality shape for a binary classifier, and the pointer `app-ml/models/last-run.json`; fails under `MIN_AUC` |
| `track` | Bash | `python3 -m app_ml_tasks.track`: one run in the experiment `app-ml` of the MLflow App `MLFLOW_APP_ARN`, with the hyperparameters, `validation_auc`, the job's names and the evaluation |
| `publish` | Python | the candidate: `app-ml/models/latest/model.tar.gz` and `evaluation.json`, then `model.json`, which names the training job, both images by digest, the AUC, the archive's SHA-256 and `TRAINING_SOURCE`. Every check runs before the first write, and `model.json` is written last |

**app-ml-register**:

| Task | Runs | What it does |
|---|---|---|
| `register` | Python | reads `model.json` and the archive under `MODEL_PREFIX`; fails on an archive whose SHA-256 is not the one `model.json` names and on a serving image that is not the stage's `TRAINING_IMAGE_URI`; copies the archive and the evaluation to `app-ml/models/sha256/<hash>/` and calls CreateModelPackage in `MODEL_PACKAGE_GROUP`: that copy, the serving image, the evaluation as the model's quality metrics, the hash in the description, which UpdateModelPackage cannot change, and the status `PendingManualApproval`. Where a version of the group already carries the hash, it proposes none. It creates no group and sets no other status (Stage 17 decision 16 (b)) |

**app-ml-score**:

| Task | Runs | What it does |
|---|---|---|
| `prepare` | a processing job, `ml.t3.medium` | `python -m app_ml.prepare score` over `app-ml/inbox/holdout.csv` alone: `app-ml/work/score/batch/batch.csv` and `app-ml/work/score/labels/labels.csv`, one order |
| `resolve` | Python | the model `app-ml-score-<project id>`. Where `MODEL_SOURCE` is `registry`, it serves the one version of `MODEL_PACKAGE_GROUP` whose description carries `model.json`'s hash, only when the version is `Approved` and the archive it names has that hash; where it is `prefix`, the archive beside `model.json`, compared with it. CreateModel as the project role, in the project's subnets and security group, network isolation on, the project tag; a model of that name left by a failed run is deleted first |
| `score` | a batch transform, `ml.m5.large` | the batch set through that model, by the workflow's constant name, into `app-ml/predictions/<ds_nodash>/batch.csv.out` |
| `check` | Python | one probability between 0 and 1 per batch line, their AUC against the labels by rank, the report `app-ml/outbox/score-report.json` with the model's hash and version; fails under `MIN_AUC` |
| `cleanup` | DeleteModel | the model `resolve` created; the service ignores `trigger_rule`, so a failed run leaves it, which bills nothing, for the next `resolve` to delete |

The stage variables, which the workflows read as `{env.VAR}`:

| Variable | `dev` | `staging` | `prod` |
|---|---|---|---|
| `MIN_AUC` | `0.70` | `0.70` | `0.70` |
| `MODEL_PREFIX` | `app-ml/models/latest` | `app-ml/bundle/model` | `app-ml/bundle/model` |
| `MODEL_SOURCE` | `prefix` | `registry` | `registry` |
| `MODEL_PACKAGE_GROUP` | `app-ml-dev` | `awsds-staging-model-app-ml` | `awsds-prod-model-app-ml` |
| `MLFLOW_APP_ARN` | the shell's | `none` | `none` |
| `TRAINING_SOURCE` | `scripts/dev-cli.sh`'s | `none` | `none` |
| `JOB_IMAGE_URI`, `TRAINING_IMAGE_URI`, `SUBNET_AZ1`, `SUBNET_AZ2`, `PROJECT_SG`, `PROJECT_KEY_ARN` | the shell's | the leg's, from the project's Tooling environment | the same |

`dev` creates the three workflows and runs none. `staging` and `prod` create app-ml-register and
app-ml-score and write the bundle's `model/` to `app-ml/bundle/model/`; `prod`'s bootstrap then runs
app-ml-register and follows its log. `MIN_AUC` takes one value in every stage, which the release's guard
reads.

## The model's path

1. In the `dev` project, app-ml-train trains, evaluates, tracks and publishes a candidate under
   `app-ml/models/latest/`. A later run replaces it.
2. A tag `v<semver>`: `bundle` reads the item `model` from the `dev` project into the bundle's `model/`
   folder as its caller (SUP-374). Neither `bundle` nor `deploy` fails where the item read nothing, so
   `scripts/check-model-bundle.py` fails a bundle without `model/model.tar.gz`, `model/evaluation.json`
   and `model/model.json`, an archive whose SHA-256 is not the one `model.json` names, an AUC under
   `MIN_AUC`, and a candidate whose training source is not the tag's. The model's hash and its training
   job go down the pipeline with the bundle's SHA256, and the release's notes name them.
3. Staging: the deploy writes the model under `app-ml/bundle/model/`; `staging-test` starts the chain
   app-ml-register, approves the proposed version as Staging's deploy role (`scripts/model-chain.py
   approve` in the infrastructure repository), starts the chain app-ml-score and fails unless the report
   names the release's hash.
4. Production: the deploy's bootstrap runs app-ml-register, which proposes the version; the manual job
   `production-approve` approves it as Production's deploy role, and Production's chain app-ml-score
   serves it from then on.

`TRAINING_SOURCE` ties the candidate to the code that trained it. `scripts/dev-cli.sh` computes it over
the checkout on every call and the deploy writes it as `dev`'s stage variable; `publish` copies it into
`model.json`; the guard computes it again over the tag. A candidate trained before a change to the
features, the sample or the training request fails the release, and so does one trained from an
uncommitted change, whose value is `dirty`. Commit first, deploy and train, then tag that commit or a
later one that leaves those paths alone. The value is the deployer's own statement: it catches a stale
candidate, and it is no control over a member who writes the candidate's prefix by hand.

## Working on it

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run python -m app_ml.prepare train --input samples --output out/train
```

`uv run ruff check` and `uv run ruff format --check` are what the pipeline runs; `uv run pdoc app_ml
./code/app_ml_tasks` serves the documentation the default branch publishes to Pages.
`uv run python scripts/make-samples.py` writes `samples/` again from the seed, the same bytes.

The workflow tooling is [`awsds-workflows`](https://github.com/felipenoris/awsds-workflows), installed
as a tool (`docs/plan/runbooks/serverless-workflows.md` §T). Its lint reads the manifest and the
workflows against the rules of a SageMaker application, offline, with this application's repository and
XGBoost's as the ones an image may name and the ceiling's instance types:

```bash
awsds-workflows lint . --image-repository awsds-prod-ecr-app-ml --algorithm-repository sagemaker-xgboost --instance-type ml.t3.medium --instance-type ml.t3.large --instance-type ml.t3.xlarge --instance-type ml.m5.large --instance-type ml.m5.xlarge --instance-type ml.c5.large --instance-type ml.c5.xlarge
```

At the commit the pipeline pins, the rule `manifest` refuses the item `model`, which names a connection,
so the lint fails this application until `AWSDS_WORKFLOWS` moves to the commit that admits it behind
`--model-item model`, which the invocation then passes.

The deploy to the `dev` project runs the CI/CD CLI (`aws-smus-cicd-cli` 1.0.9) from a space on the house
image, as the project's role, with the shell variables the manifest reads: `DOMAIN_ID`, `DOMAIN_REGION`,
`DEV_PROJECT_NAME`, `JOB_IMAGE_URI` (the image the last release's notes name), `TRAINING_IMAGE_URI`,
`SUBNET_AZ1`, `SUBNET_AZ2`, `DEV_PROJECT_SG`, `DEV_PROJECT_KEY_ARN` and `MLFLOW_APP_ARN`. The workers'
archives come first, since `bundle` and `deploy` copy and never build:

```bash
awsds-workflows package-task code code/app-ml-train.zip
```

```bash
find code/app_ml_tasks -name __pycache__ -prune -exec rm -rf {} +
python3 -m zipfile -c code/app-ml-register.zip code/app_ml_tasks
python3 -m zipfile -c code/app-ml-score.zip code/app_ml_tasks
```

Then a bundle, since the item `model` names a connection and a deploy reads the model from a bundle, the
deploy, which copies the folders and creates the workflows, and a run:

```bash
scripts/dev-cli.sh bundle --manifest manifest.yaml --targets dev
```

```bash
scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
```

```bash
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-ml-train
```

`scripts/dev-cli.sh` is app-etl's: the house image's CLI by its path, its domain lookup answered with
`DOMAIN_ID`, the `staging` and `prod` stages' names given a placeholder when the shell has none. It also
refuses to start without `MLFLOW_APP_ARN`, and exports `TRAINING_SOURCE` as `scripts/training-source.py`
computes it, whatever the shell holds, printing it on stderr. The session around a deploy, the endpoint
groups it raises among them, is the infrastructure repository's
`docs/plan/runbooks/sagemaker-application.md` §D.

## The pipeline

| Ref | Jobs | Runner |
|---|---|---|
| any branch | `test` (`uv sync --locked`, `uv lock --check` of `code/`, ruff, pytest, the workflow lint), `secret_detection` and its gate, `pip-audit` of `code/`'s lock | the test runner, no AWS identity |
| `main` | the same, and `pages` | the test runner |
| a tag `v<semver>` | `test`, `pip-audit`, `build-image` (smoke, then the push as `v<semver>-<short sha>`), `scan-gate`; `build-task-code` (the workers' archives, each imported on CPython 3.12); `bundle` (the tag's files and the `dev` project's candidate, then the guard); `store-bundle`; `release`; the promotion: `staging-gate` (manual), `staging-check`, `staging-deploy`, `staging-test` (register, approve, score, the report), `production-check`, `production-gate` (manual), `production-deploy` (whose bootstrap runs app-ml-register), then the manual `production-approve` | the test runner, the build runner, and the deploy runner for `bundle` and the promotion |

The gate `pip-audit` reads `code/`'s lock alone (`GATES_UV_PROJECTS`): the application's own runtime set
is empty, and the gate stops on an export that pins nothing. A release is a tag on `main`, which only a
Maintainer can create. `bundle` runs as `awsds-deploy-sandbox-test`, a member of the `dev` project,
whose read of the candidate is step 9.5's: a list and a read of `app-ml/models/latest/` alone. The CLI
lists the connection's whole location first and goes on when that listing is refused, and the job fails
on *"Error syncing"*, the line the CLI prints when it cannot read the item. The legs clone `awsds/infrastructure` with the job token and run its
`scripts/deploy-application.py` and `scripts/model-chain.py`, as app-etl's do; Staging's
`staging/egress` is the user's to raise before the tag, and Production's `production/workloads-egress`
for its leg. The model jobs app-etl's pipeline holds (`production-register`, `production-transform`) have
no counterpart here: a task registers, and the chains serve.

## The job contract

A SageMaker processing job runs the image with networking off, as the image's user, on mounts the platform
creates owned by root with mode 755: the code at `/opt/ml/processing/code`, the input and the output.
Each prepare task's command therefore opens with the chown the image's passwordless `sudo` allows, then
runs the code from its mount:

```bash
sudo -n chown "$(id -u)" /opt/ml/processing/output && cd /opt/ml/processing/code && exec python -m app_ml.prepare train --input /opt/ml/processing/input --output /opt/ml/processing/output
```

What the command and the tasks print lands in the account's log groups, so they print versions, counts,
names, hashes and metrics, never a value of the data.
