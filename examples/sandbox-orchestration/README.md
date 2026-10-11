# Sandbox orchestration: the exercise's files

The files [Stage 6i](../../docs/plan/stages/stage-06i-sandbox-orchestration.md) runs: a Python project,
the operator files of its worker variants, the processing job's configuration, and a sample. The stage
file is the procedure and carries the reasoning; this file says what each piece is and where it goes.

The procedure for a reader who is not running the stage is
[`runbooks/serverless-workflows.md`](../../docs/plan/runbooks/serverless-workflows.md).

The code is written here and copied into the project, from a clone of this repository inside a space. The workflow definitions go the other way: the
portal generates and versions them, and after each pass the definition the portal holds is committed
under `definitions/` as the record of what ran (Stage 6i decision 1).

## Layout

| Path | What it is | Where it goes in the project |
|---|---|---|
| `awsds-demo-job/` | the Python project: one CSV in, one JSON summary out, standard library only. `python -m awsds_demo_job` reads and writes directories (the processing job's mode); `python -m awsds_demo_job.s3` reads and writes S3 prefixes (the worker's mode) | the whole folder, as `shared/awsds-demo-job/`: `demo-devenv-job`'s processing job reads it as its code input |
| `devenv-job/demo-devenv-job.probe.yaml` | `demo-devenv-job`'s definition for pass 2: the three tasks, the processing task's command a one-minute probe of the container's user and mounts | rendered, then imported with *Actions → Import definition file*: the editor's processing form has no field for the boundary's settings |
| `devenv-job/demo-devenv-job.project.yaml` | the same definition for pass 3: the project's command in the house environment's Python | imported the same way over the first |
| `operators/python/` | `demo_tasks.py`, the `PythonOperator` callable, and the vendored set in `requirements.txt` | built into `python-operator.zip` |
| `operators/python/demo-python-operator.yaml` | `demo-python-operator`'s definition: the sensor, then the `PythonOperator` task with `python_callable: demo_tasks.run` | rendered, then imported after `python-operator.zip` is uploaded in *Settings → Storage* |
| `operators/bash/` | `reach_pypi.sh`, the PyPI negative | built into `bash-operator.zip` |
| `operators/bash/demo-bash-operator.yaml` | `demo-bash-operator`'s exercise: the sensor, `run_command` running the package from the archive, and `reach_pypi.sh` by name | rendered, then imported after the probe is deleted (an import does not replace a saved workflow), with `bash-operator.zip` uploaded in *Settings → Storage* |
| `operators/bash/demo-bash-operator.probe.yaml` | the first version of `demo-bash-operator`: two Bash tasks with inline commands, the caller's identity and the PyPI negative, and no `Code` object, the control for Stage 6i decision 7 | rendered, then imported into a new, empty workflow with nothing uploaded in *Settings → Storage* |
| `operators/build.sh` | builds the exercise's two archives into `operators/dist/` (untracked), the vendored set for CPython 3.12 on manylinux2014 x86_64; for your own project use `package-uv.sh` | the archives are uploaded in *Settings → Storage* of their workflow |
| `operators/package-uv-job.py` | packages a uv project as a processing job's code input in the house image: a folder with the project and only the packages the house environment lacks, stopping on a version the two disagree on | the folder is copied into the project's `shared/` and named as the job's `code` input; the runbook's section J1 is its procedure |
| `operators/package-uv.sh` | packages any uv project (its `uv.lock` closure, minus the worker's pre-installed set, and the project's own wheel) plus an entry module into one archive for the worker | the archive is uploaded in *Settings → Storage*; the runbook's section C2 is its procedure |
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
A definition the portal saved goes the other way: `--placeholders` replaces each live value with its
placeholder, and the result is the copy in `definitions/`:

```bash
./examples/sandbox-orchestration/render.py --placeholders aws/output/sandbox-orchestration/demo-devenv-job/<NN>-<version>.yaml
```

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
| `wait_for_file` | `S3KeySensor` | as above, on `<DEMO_PREFIX>/python/inbox/?*`: a folder marker `inbox/` matches `*`, and this task, unlike `S3DeleteObjectsOperator`, leaves the marker in place |
| `run_project` | Python Operator | module `demo_tasks`, function `run`; op kwargs `{"bucket": "<PROJECTS_BUCKET>", "inbox": "<DEMO_PREFIX>/python/inbox/", "outbox": "<DEMO_PREFIX>/python/outbox/"}`; `python-operator.zip` in *Storage* |

### `demo-bash-operator`

The probe, `operators/bash/demo-bash-operator.probe.yaml`, has no sensor and no `Code` object:

| Task | Operator | Fields |
|---|---|---|
| `caller_identity` | Bash Operator | inline: the worker's Python and boto3, the region variables, where the STS endpoint resolves, and the caller's ARN from `GetCallerIdentity` |
| `reach_pypi` | Bash Operator | inline: the commands of `reach_pypi.sh`, after `caller_identity`; it is expected to fail |

The exercise, `operators/bash/demo-bash-operator.yaml`, which replaced the probe once a workflow with a `Code` object could run:

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | as above, on `<DEMO_PREFIX>/bash/inbox/?*`, for the same reason |
| `run_command` | Bash Operator | prints its folder and `PYTHONPATH`, then `cd /usr/local/airflow/dags && python3 -m awsds_demo_job.s3 --bucket <PROJECTS_BUCKET> --inbox <DEMO_PREFIX>/bash/inbox/ --outbox <DEMO_PREFIX>/bash/outbox/`; `bash-operator.zip` in *Storage* |
| `reach_pypi` | Bash Operator | `reach_pypi.sh`, after `run_command`; it is expected to fail |

## Running the project's tests

```bash
uv run python -m unittest discover -s examples/sandbox-orchestration/awsds-demo-job/tests
```
