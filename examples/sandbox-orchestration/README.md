# Sandbox orchestration: the exercise's files

The files [Stage 6i](../../docs/plan/stages/stage-06i-sandbox-orchestration.md) runs: a Python project,
the operator files of its worker variants, the processing job's configuration, and a sample. The stage
file is the procedure and carries the reasoning; this file says what each piece is and where it goes.

The code is written here and copied into the project, from a clone of this repository inside a space. The workflow definitions go the other way: the
portal generates and versions them, and after each pass the definition the portal holds is committed
under `definitions/` as the record of what ran (Stage 6i decision 1).

## Layout

| Path | What it is | Where it goes in the project |
|---|---|---|
| `awsds-demo-job/` | the Python project: one CSV in, one JSON summary out, standard library only. `python -m awsds_demo_job` reads and writes directories (the processing job's mode); `python -m awsds_demo_job.s3` reads and writes S3 prefixes (the worker's mode) | the whole folder, as `shared/awsds-demo-job/`: `demo-devenv-job`'s processing job reads it as its code input |
| `devenv-job/demo-devenv-job.probe.yaml` | `demo-devenv-job`'s definition for pass 2: the three tasks, the processing task's command a one-minute probe of the container's user and mounts | rendered, then imported with *Actions → Import definition file*: the editor's processing form has no field for the boundary's settings |
| `devenv-job/demo-devenv-job.project.yaml` | the same definition for pass 3: the project's command in the house environment's Python | imported the same way over the first |
| `devenv-job/no_operator_code.py` | a docstring and nothing else | uploaded in *Settings → Storage*: the portal refuses a save with no operator file. Any `.py` does |
| `operators/python/` | `demo_tasks.py`, the `PythonOperator` callable, and the vendored set in `requirements.txt` | built into `python-operator.zip` |
| `operators/bash/` | `reach_pypi.sh`, the PyPI negative | built into `bash-operator.zip` |
| `operators/build.sh` | builds both archives into `operators/dist/` (untracked), the vendored set for CPython 3.12 on manylinux2014 x86_64 | the archives are uploaded in *Settings → Storage* of their workflow |
| `samples/sample.csv` | ten synthetic rows | a drop is a copy of it, from the clone, into a variant's `shared/orchestration-demo/<variant>/inbox/` |
| `render.py` | fills the placeholders with the live values, read-only, and prints to stdout | — |
| `definitions/` | each workflow's definition after each pass, account ids replaced | — |

## Placeholders

Every account-scoped value is a placeholder: `<SANDBOX_ACCOUNT_ID>`, `<REGISTRY_ACCOUNT_ID>`, `<REGION>`,
`<PROJECT_ROLE_NAME>`, `<PROJECT_KEY_ID>`, `<PROJECTS_BUCKET>`, `<DOMAIN_ID>`, `<PROJECT_ID>`,
`<PROJECT_SG>`, `<SUBNET_AZ1>`, `<SUBNET_AZ2>`, `<IMAGE_DIGEST>`, and `<DEMO_PREFIX>`, which is
`<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo`. The pre-commit hook refuses an account
id in a tracked file, so the real values exist only on screen:

```bash
./examples/sandbox-orchestration/render.py --values
```

```bash
./examples/sandbox-orchestration/render.py examples/sandbox-orchestration/devenv-job/demo-devenv-job.probe.yaml
```

Both read as the infrastructure user's `InfrastructureAccess` in Sandbox (`awsds-infra-sandbox-1`).

## The workflows' tasks, as the portal asks for them

Every task carries `retries: 0`. `render.py README.md` prints these tables with the values in place.

### `demo-devenv-job`

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | `bucket_key`: `s3://<PROJECTS_BUCKET>/<DEMO_PREFIX>/devenv/inbox/*`; `wildcard_match`: true; `poke_interval`: 30; `timeout`: 600; `soft_fail`: true |
| `run_project` | `SageMakerProcessingOperator` | `config`: the whole job request, carried by the rendered `devenv-job/demo-devenv-job.*.yaml`; the editor's form for this operator cannot express it |
| `remove_source` | `S3DeleteObjectsOperator` | `bucket`: `<PROJECTS_BUCKET>`; `prefix`: `<DEMO_PREFIX>/devenv/inbox/` |

### `demo-python-operator`

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | as above, on `<DEMO_PREFIX>/python/inbox/*` |
| `run_project` | Python Operator | module `demo_tasks`, function `run`; op kwargs `{"bucket": "<PROJECTS_BUCKET>", "inbox": "<DEMO_PREFIX>/python/inbox/", "outbox": "<DEMO_PREFIX>/python/outbox/"}`; `python-operator.zip` in *Storage* |

### `demo-bash-operator`

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | as above, on `<DEMO_PREFIX>/bash/inbox/*` |
| `run_command` | Bash Operator | `python3 -m awsds_demo_job.s3 --bucket <PROJECTS_BUCKET> --inbox <DEMO_PREFIX>/bash/inbox/ --outbox <DEMO_PREFIX>/bash/outbox/`; `bash-operator.zip` in *Storage* |
| `reach_pypi` | Bash Operator | `reach_pypi.sh`, after `run_command`; it is expected to fail |

## Running the project's tests

```bash
uv run python -m unittest discover -s examples/sandbox-orchestration/awsds-demo-job/tests
```
