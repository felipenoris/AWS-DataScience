# app-etl

Every CSV in a directory becomes a Parquet table and a JSON summary. The first application of the AWS
Data Science environment, and the template its other applications start from: the GitLab project
`awsds/app-etl` received this tree from the infrastructure repository's `examples/app-etl/`
(Stage 8 step 2.2) and holds it since.

| Path | What it is |
|---|---|
| `src/app_etl/` | the code: `pipeline.py` the transformation, `__main__.py` the command a processing job runs |
| `tests/` | pytest, offline, against `samples/` |
| `samples/` | synthetic trades, the input of the image's smoke test and of a Sandbox job |
| `Dockerfile` | the application image, which is also the job image: `FROM` base by digest, the project in a virtual environment of its own on base's CPython 3.12; target `app` is the image, `smoke` runs the job's command on it |
| `.gitlab-ci.yml` | the pipeline, with the shared gates from `awsds/ci-gates` |
| `pyproject.toml`, `uv.lock` | the project and its lock; the resolver ignores anything published after `exclude-newer` |

The Terraform that runs the application is not here: each environment's slice is
`terraform-live/<env>/app/app-etl/` in the infrastructure repository (Stage 8 decision 12), and Sandbox's
is applied by hand while the application is engineered (step 2.4). The workflow definition and its code
(`workflow/`) and the Glue scripts (`glue/`) join this tree at Stage 10.

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

## The pipeline

| Ref | Jobs | Runner |
|---|---|---|
| any branch | `test` (`uv sync --locked`, ruff, pytest), `secret_detection` and its gate, `pip-audit` | the test runner, no AWS identity |
| `main` | the same, and `pages` | the test runner |
| a tag `v<semver>` | `test`, `pip-audit`, `build-image` (smoke, then the push as `v<semver>-<short sha>`), `scan-gate` | the test runner, then the build runner |

A release is a tag `v<major>.<minor>.<patch>` on `main`, which only a Maintainer can create: the tag is
protected, and that protection is the release gate. ECR's tags are immutable, so a second pipeline for
the same tag is refused at the push; the short sha keeps two builds of one release apart.

## The job contract

A SageMaker processing job runs the image with networking off, as the image's user, on mounts the platform
creates owned by root with mode 755. Its command therefore opens with the chown the image's passwordless
`sudo` allows:

```bash
sudo -n chown "$(id -u)" /opt/ml/processing/output && python -m app_etl --input /opt/ml/processing/input --output /opt/ml/processing/output
```

What the command prints lands in the account's shared processing-job log group, so it prints versions,
counts and file names, never a cell of data.
