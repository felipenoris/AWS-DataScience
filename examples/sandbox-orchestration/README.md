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
| `awsds-demo-deps/` | a uv project with dependencies: one CSV in, a JSON summary (byte for byte `awsds-demo-job`'s) and a Parquet table out. `petl` (pure Python) and `msgspec` (an extension module) are absent from the house environment; `pyarrow` is in it, pinned to the image's version | packaged by `awsds-workflows package-job` (the runbook's J1) into a folder of its own, copied as `shared/jobs/awsds-demo-deps-0.1.0/`: `demo-devenv-deps`'s processing job reads it as its code input |
| `devenv-job/demo-devenv-deps.yaml` | `demo-devenv-deps`'s definition: `demo-devenv-job`'s three tasks, with that folder as the code input and `PYTHONPATH` at its root | rendered, then imported into a new, empty workflow |
| `operators/python/` | `demo_tasks.py`, the `PythonOperator` callable, and the vendored set in `requirements.txt` | built into `python-operator.zip` |
| `operators/python/demo-python-operator.yaml` | `demo-python-operator`'s definition: the sensor, then the `PythonOperator` task with `python_callable: demo_tasks.run` | rendered, then imported after `python-operator.zip` is uploaded in *Settings → Storage* |
| `operators/bash/` | `reach_pypi.sh`, the PyPI negative | built into `bash-operator.zip` |
| `operators/bash/demo-bash-operator.yaml` | `demo-bash-operator`'s exercise: the sensor, `run_command` running the package from the archive, and `reach_pypi.sh` by name | rendered, then imported after the probe is deleted (an import does not replace a saved workflow), with `bash-operator.zip` uploaded in *Settings → Storage* |
| `operators/bash/demo-bash-operator.probe.yaml` | the first version of `demo-bash-operator`: two Bash tasks with inline commands, the caller's identity and the PyPI negative, and no `Code` object, the control for Stage 6i decision 7 | rendered, then imported into a new, empty workflow with nothing uploaded in *Settings → Storage* |
| `operators/build.sh` | builds the exercise's two archives into `operators/dist/` (untracked) by the runbook's C6 recipe, the vendored set for CPython 3.12 on manylinux2014 x86_64. Its Python archive carries PyYAML, which the worker pre-installs, so that the version reading tells the two copies apart (Stage 6i verification viii); `awsds-workflows package-task` leaves such a package out by design. For your own project use `package-task` (the runbook's C2) | the archives are uploaded in *Settings → Storage* of their workflow |
| `samples/sample.csv` | ten synthetic rows | a drop is a copy of it, from the clone, into a variant's `shared/orchestration-demo/<variant>/inbox/` |
| `definitions/` | each workflow's definition after each pass, every account-scoped value a placeholder | — |

## Placeholders

Every account-scoped value is a placeholder, under the names
[`awsds-workflows`](https://github.com/felipenoris/awsds-workflows) fills (the runbook's §T): `<REGION>`,
`<ACCOUNT_ID>`, `<PROJECT_ROLE_NAME>`, `<PROJECT_ID>`, `<DOMAIN_ID>`, `<PROJECTS_BUCKET>`,
`<PROJECT_KEY_ID>`, `<PROJECT_SG>`, `<SUBNET_AZ1>`, `<SUBNET_AZ2>` and `<JOB_IMAGE_URI>`. The exercise's
prefix is `<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo`. The pre-commit hook refuses an account
id in a tracked file, so the real values exist only on screen:

```bash
awsds-workflows values --profile awsds-infra-sandbox-1 --subnet-name 'awsds-sandbox-private-*' --image-name awsds-sandbox-dev-env
```

```bash
awsds-workflows render examples/sandbox-orchestration/devenv-job/demo-devenv-job.probe.yaml --profile awsds-infra-sandbox-1 --subnet-name 'awsds-sandbox-private-*' --image-name awsds-sandbox-dev-env
```

Both read as the infrastructure user's `InfrastructureAccess` in Sandbox (`awsds-infra-sandbox-1`).
A definition the portal saved goes the other way: `--placeholders` replaces each live value with its
placeholder, the result is the copy in `definitions/`, and `compare` prints what the portal changed
against the file it was imported from:

```bash
awsds-workflows render --placeholders aws/output/sandbox-orchestration/demo-devenv-job/<nn>-<version>.yaml --profile awsds-infra-sandbox-1 --subnet-name 'awsds-sandbox-private-*' --image-name awsds-sandbox-dev-env > /tmp/saved.yaml
```

```bash
awsds-workflows compare examples/sandbox-orchestration/devenv-job/demo-devenv-job.project.yaml /tmp/saved.yaml
```

Each record in `definitions/` against the file it was imported from, read on 2026-10-12:

| Record | What `compare` printed |
|---|---|
| `demo-devenv-job.probe`, `demo-devenv-job.project`, `demo-devenv-deps`, `demo-python-operator` | `is_paused_upon_creation: false`, which the portal adds at every save and the service ignores |
| `demo-bash-operator` | the same, and `description: "Stage 6i pass 5"`, the description-only save of Stage 6i verification vii |
| `demo-bash-operator.probe` | the same, and `endpoint_refusal`'s command, which the template changed after the run so that it counts the error code rather than the wording (Stage 6i step 5.0) |

## The workflows' tasks, as the portal asks for them

Every task carries `retries: 0`. `awsds-workflows render` on this file, with the flags above, prints these
tables with the values in place.

### `demo-devenv-job`

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | `bucket_key`: `s3://<PROJECTS_BUCKET>/<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/devenv/inbox/*`; `wildcard_match`: true; `poke_interval`: 30; `timeout`: 600; `soft_fail`: true |
| `run_project` | `SageMakerProcessingOperator` | `config`: the whole job request, carried by the rendered `devenv-job/demo-devenv-job.*.yaml`; the editor's form for this operator cannot express it |
| `remove_source` | `S3DeleteObjectsOperator` | `bucket`: `<PROJECTS_BUCKET>`; `prefix`: `<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/devenv/inbox/` |

### `demo-devenv-deps`

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | as above, on `<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/devenv-deps/inbox/?*`: a folder marker `inbox/` matches `*` and would start the job with no file |
| `run_project` | `SageMakerProcessingOperator` | `config`: `demo-devenv-job`'s, with the code input `shared/jobs/awsds-demo-deps-0.1.0/`, `PYTHONPATH` `/opt/ml/processing/code` and the command `python -m awsds_demo_deps` |
| `remove_source` | `S3DeleteObjectsOperator` | `bucket`: `<PROJECTS_BUCKET>`; `prefix`: `<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/devenv-deps/inbox/` |

### `demo-python-operator`

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | as above, on `<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/python/inbox/?*`: a folder marker `inbox/` matches `*`, and this task, unlike `S3DeleteObjectsOperator`, leaves the marker in place |
| `run_project` | Python Operator | module `demo_tasks`, function `run`; op kwargs `{"bucket": "<PROJECTS_BUCKET>", "inbox": "<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/python/inbox/", "outbox": "<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/python/outbox/"}`; `python-operator.zip` in *Storage* |

### `demo-bash-operator`

The probe, `operators/bash/demo-bash-operator.probe.yaml`, has no sensor and no `Code` object:

| Task | Operator | Fields |
|---|---|---|
| `caller_identity` | Bash Operator | inline: the worker's Python and boto3, the region variables, where the STS endpoint resolves, and the caller's ARN from `GetCallerIdentity` |
| `reach_pypi` | Bash Operator | inline: the commands of `reach_pypi.sh`, after `caller_identity`; it is expected to fail |

The exercise, `operators/bash/demo-bash-operator.yaml`, which replaced the probe once a workflow with a `Code` object could run:

| Task | Operator | Fields |
|---|---|---|
| `wait_for_file` | `S3KeySensor` | as above, on `<DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/bash/inbox/?*`, for the same reason |
| `run_command` | Bash Operator | prints its folder and `PYTHONPATH`, then `cd /usr/local/airflow/dags && python3 -m awsds_demo_job.s3 --bucket <PROJECTS_BUCKET> --inbox <DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/bash/inbox/ --outbox <DOMAIN_ID>/<PROJECT_ID>/shared/orchestration-demo/bash/outbox/`; `bash-operator.zip` in *Storage* |
| `reach_pypi` | Bash Operator | `reach_pypi.sh`, after `run_command`; it is expected to fail |

## Running the project's tests

```bash
uv run python -m unittest discover -s examples/sandbox-orchestration/awsds-demo-job/tests
```

`awsds-demo-deps` runs in its own environment, CPython 3.12 with the locked dependencies: the house
environment's Python from `default-v0.7.0`. 6i packaged it for 3.13, the house environment up to
`default-v0.6.0`, and an extension module built for one does not import in the other:

```bash
uv run --directory examples/sandbox-orchestration/awsds-demo-deps python -m unittest discover -s tests
```
