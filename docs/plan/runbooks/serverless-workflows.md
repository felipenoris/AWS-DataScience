# Runbook — Serverless workflows in a SageMaker project

*The stage that exercised this is [`stage-06i-sandbox-orchestration.md`](../stages/stage-06i-sandbox-orchestration.md),
and its readings are in [`log-stage-06i`](../../log/log-stage-06i-sandbox-orchestration.md). The reference files,
with a placeholder for every account-scoped value, are in
[`examples/sandbox-orchestration/`](../../../examples/sandbox-orchestration/README.md). The instrument is
`./aws/sandbox-orchestration.py`.*

A serverless workflow is a MWAA Serverless workflow that the project's *Workflows* page creates: a YAML
definition (Airflow 3.0.6 through dag-factory), run by workers the service starts per task, as the
project role, inside the project's network. This runbook covers the three task kinds Stage 6i
exercised: a SageMaker processing job in the house image, a `PythonOperator` and a `BashOperator`.

| Section | Audience | What it holds |
|---|---|---|
| **§O** | both | the pieces: where the definition, the code, the logs and the runs live |
| **§G** | infrastructure | the grant a project needs before its first processing task, once per project |
| **§A** | the data scientist | authoring rules every workflow obeys: the editor, the import, the templates, the sensor |
| **§J** | the data scientist | a processing task in the house image, under the D13 boundary |
| **§C** | the data scientist | code for a Python or Bash task: the archive, its dependencies, the upload |
| **§V** | both | reading a run back, one instrument per question |
| **§X** | both | cleaning up |

**State, 2026-10-11.** **The processing task works end to end in Sandbox**: a sensor, a job in the house
image that summarises the sample, and the source deleted after the result landed under the project key
(run `f9L7CKQzmUQWQTR`). **A workflow with a code archive does not run in Sandbox today**: its worker
fails while preparing its environment, before any task, because the S3 gateway endpoint's allow-list
refuses the bucket the service keeps the code in (6i decision 7, open). §C describes the packaging that
was built and verified locally; nothing in it has run on a worker yet.

---

## §O — The pieces

| What | Where | Note |
|---|---|---|
| the definition | `s3://<projects bucket>/<domain>/<project>/dev/workflows/<name>.yaml` | written by the portal on each save; *View code* shows it |
| the code archive of a Python or Bash task | `.../dev/operatorFiles/<file>` | uploaded in *Settings → Storage*; one `.zip` is stored as uploaded, and the workflow pins its S3 version |
| the service's copy of that code | storage the service owns | taken at each save and encrypted under the project key; not written to the projects bucket, and its own bucket is unread (2026-10-11) |
| the task logs | `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, one stream per task attempt | per project; no retention (`EXC-10`'s shape); the group outlives the workflow |
| a processing job's container output | `/aws/sagemaker/ProcessingJobs`, stream `<job>/algo-1-<n>` | account-wide: every project role in the account can read it |
| the identity | the project role, `datazone_usr_role_<project>_<env>`, session `AmazonMWAAServerless` on the worker, `SageMaker` inside a job | the D13 boundary applies to both |
| the network | the two private subnets and the project's security group, injected by the portal | no default route: AWS is reached through the VPC endpoints, S3 through the gateway endpoint |
| the key | the project CMK (`alias/awsds-<env>-project`) | the workflow's encryption, the job's volume and outputs, the bucket |

**The worker** is 1 vCPU and 3 GiB with Python 3.12, Airflow 3.0.6, the Amazon provider 9.32.0 and boto3
1.43.1. It has no internet and no proxy. A task holds its worker for its whole duration, sensor waits
included, and bills 0.088 USD per task-hour with a one-minute minimum.

---

## §G — The grant a project needs, once per project

A project role cannot run `SageMakerProcessingOperator` with the blueprint's policies alone, for two
reasons measured on 2026-10-10:

- **The operator describes the job name before creating it**, and the blueprint lets a project role
  describe only a job tagged with its own project. A name not yet taken carries no tag, so the first run
  fails with `AccessDeniedException` on `DescribeProcessingJob` before any job exists.
- **A create that carries tags is also authorized as `sagemaker:AddTags`**, and the blueprint excludes
  every `AmazonDataZone*` key from `AddTags` while requiring the job to carry `AmazonDataZoneProject`. The
  second run fails with `AccessDeniedException` on `sagemaker:AddTags`.

The grant is `terraform-live/sandbox/workflows/`, one policy and one attachment per project role:

1. Add the project role's name to `project_roles` in `variables.tf`. The role is
   `datazone_usr_role_<project id>_<environment id>`, read with `aws iam list-roles`.
2. Plan and apply the slice as the infrastructure user, `InfrastructureAccess`, in the account the project
   lives in. A precondition refuses a role without the D13 boundary.

The policy allows `DescribeProcessingJob` on a job with no project tag, and `AddTags` of the caller's own
project tag alone, on a job with no project tag or with the caller's. Another project's jobs stay out of
reach.

---

## §A — Authoring rules every workflow obeys

**Create empty, then import.** On the *Workflows* page, create a workflow, then *Actions → Import
definition file* with the rendered YAML (`examples/sandbox-orchestration/render.py <file> > ~/Downloads/<name>.yaml`).
The editor's forms cannot express everything a definition can (§J), and an import keeps every field: the
saved definition differs from the imported one only by `is_paused_upon_creation: false`, keys reordered
and long strings folded.

**An import replaces the workflow.** Each import measured here appears in CloudTrail as `DeleteWorkflow`
then `CreateWorkflow`: the ARN suffix changes and the run and version history restart. The log group is named
after the workflow and keeps every run's logs.

**Save errors and their way through:**

| The portal says | What happened | Way through |
|---|---|---|
| `ValidationException: Code not found in specified S3 location` | the save sent a code location under `dev/operatorFiles/` with no file there | upload any `.py` in *Settings → Storage*, or import into a new empty workflow |
| `ContainerArguments: Container argument is required` | the editor, not the API, demands arguments on a processing task | split the command into a program (`ContainerEntrypoint`) and its arguments |
| two workflows of one name | two saves raced past the name check, 2 s apart | delete one; the name is checked otherwise |

**The first line of the YAML is the editor's layout**, a JSON comment such as
`# {"wait_for_file":{"x":120,"y":200},...}`. Keep it, and put no other comment in a file meant for
import.

**Templates render when the run is created**, with only `macros`, `ti`/`task_instance`, `params`, `ds`,
`ds_nodash`, `ts` and `ts_nodash`:

- `{{ ts_nodash }}` is the day's midnight on a manual run, so two runs on one day collide on it;
- `{{ dag_run... }}` fails the run before its first task ("'dag_run' is undefined");
- a method on an object a macro returned fails too ("access to attribute 'strftime' of 'datetime'
  object is unsafe");
- a module's own functions pass. A per-run stamp:
  `{{ macros.time.strftime('%Y%m%dT%H%M%S', macros.time.gmtime()) }}`.

**Parameters the service ignores or caps:** `deferrable`, `trigger_rule`,
`render_template_as_native_obj` and `do_xcom_push` are ignored, so a templated list arrives as a string.
`retries` defaults to 1, at most 3: write `retries: 0` on every task while developing, or a failure runs
twice. `execution_timeout` is at most 3,600 s.

**The file sensor.** `S3KeySensor` with `wildcard_match: true`, `poke_interval: 30`, `timeout: 600` and
`soft_fail: true`:

- a space's `mkdir` leaves a zero-byte folder marker `inbox/`, and `inbox/*` matches it. Watch
  `inbox/?*`, which needs one character after the slash, unless a later task deletes the whole prefix;
- `soft_fail` ends a run with an empty inbox `SUCCESS` after the timeout. The API then reads the sensor's
  status as `NONE`, not `SKIPPED`, and lists no instance for the tasks after it; only the task log says
  `Skipping task.` The wait bills its 10 minutes (about 0.015 USD).

**Drop a file from a space**, whose `~/shared/` is the project's `shared/` prefix:

```bash
mkdir -p ~/shared/orchestration-demo/<variant>/inbox && cp <file> ~/shared/orchestration-demo/<variant>/inbox/
```

---

## §J — A processing task in the house image

The portal's *SageMaker Processing* form has no field for `NetworkConfig`, either KMS key or the tags,
and a job without them is refused by the D13 boundary. Write the task's whole `config` in the YAML and
import it. The template is `examples/sandbox-orchestration/devenv-job/demo-devenv-job.project.yaml`.

**What the boundary requires** (`awsds-<env>-project-boundary`), on every job:

- `NetworkConfig.VpcConfig`: the project's two private subnets and its security group;
- `EnableNetworkIsolation: true`: the container has no network and no AWS credentials;
- `EnableInterContainerTrafficEncryption: true`, even for one instance;
- `ProcessingResources.ClusterConfig.VolumeKmsKeyId`: the project key;
- an instance type inside the boundary's ceiling; `ml.t3.medium` is the smallest it admits.

The project's own rules add `Tags: [{Key: AmazonDataZoneProject, Value: <project id>}]` and the output's
`KmsKeyId`, the project key.

**Inputs and outputs live under `/opt/ml/processing/`.** SageMaker downloads each `ProcessingInput` there
before the command starts and uploads each `ProcessingOutput` after it exits, as the project role. The
code is one more input: the project's package, read from `shared/`.

**The container user cannot write the output mount.** The house image runs as `sagemaker-user` (uid 1000)
and the platform creates every mount as root with mode 755, so a write fails with `Permission denied` and
the job ends `AlgorithmError: , exit code: 1`. The image's `sudo` works inside a job, so the command
opens with a `chown`:

```yaml
ContainerEntrypoint: [/bin/bash, -c]
ContainerArguments:
  - 'sudo -n chown "$(id -u)" /opt/ml/processing/outbox && exec /opt/awsds/venv/bin/python -m awsds_demo_job --input /opt/ml/processing/inbox --output /opt/ml/processing/outbox'
Environment:
  PYTHONPATH: /opt/ml/processing/code/src
```

- `exec` hands the job the interpreter's exit code;
- the interpreter is named by absolute path, because a `ContainerEntrypoint` replaces the image's entry
  point and its `PATH`;
- `/opt/awsds/venv/bin/python` is the house environment (Python 3.13); `/opt/conda/bin/python` is the
  distribution's (3.12).

### J1 — A project with dependencies

The job has no network, so a project's dependencies either come with the house environment or travel in
the code input; nothing is installed at run time. Three things differ from a Python task's archive (§C):

- **The interpreter is the house environment's**, CPython 3.13 on linux x86_64, not the worker's 3.12.
- **The code input is a folder, not an archive.** A `ProcessingInput` downloads an S3 prefix, and an
  extension module cannot be imported from a zip on `sys.path`.
- **The precedence is the worker's reversed.** `PYTHONPATH` comes before the house environment's
  site-packages, so a package in both would shadow the image's copy, the failure
  `images/dev-env/python/pyproject.toml` documents for numpy. The folder may hold only what the image
  lacks, and the project's versions must equal the image's for everything they share.

`examples/sandbox-orchestration/operators/package-uv-job.py` applies the three, for a uv project:

```bash
./examples/sandbox-orchestration/operators/package-uv-job.py <project dir> <output folder>
```

It reads the house environment from `images/dev-env/python/uv.lock`, takes the project's locked closure
for the job's platform, and sorts it three ways: provided by the image, vendored (absent from the
image), or in conflict. A conflict stops it and prints a block to add to the project's
`pyproject.toml`:

```toml
[tool.uv]
constraint-dependencies = [
  "boto3==1.43.92",
  ...
]
```

`uv lock` then resolves within the image's versions. A lower bound of the project above an image
version fails that lock, and then the dependency belongs in the image (a new image version, through
[`dev-env.md`](dev-env.md)), not in the job. Without a conflict it builds the folder: the project's
wheel and the vendored packages, built for the job's platform.

**Measured 2026-10-11** on a throwaway uv project depending on `petl`, `requests`, `boto3` and `pyyaml`:
its fresh lock disagreed with the image on `boto3`, `botocore`, `charset-normalizer`, `idna` and
`urllib3`; with the printed block and a re-lock, 12 packages came from the image and only `petl` was
vendored, a 1.2 MB folder.

**Using the folder:** copy it into the project's storage (from a space, `cp -r <folder>
~/shared/<name>/`), name that prefix as the `code` input at `/opt/ml/processing/code`, set
`PYTHONPATH: /opt/ml/processing/code`, and run `exec /opt/awsds/venv/bin/python -m <package>` after the
`chown`. The lock in the repository must be the one of the image version the job names. The demo job's
project has no dependencies, so its input is its source tree with `PYTHONPATH` at `src/`.

**The workflow deletes the source, not the job**: an isolated container cannot reach S3. The third task
is `S3DeleteObjectsOperator` on the inbox prefix, after the processing task.

**Print counts and paths, never data.** The container's output goes to an account-wide log group (§O).

**What a run costs and how long it takes** (measured 2026-10-11): about 15 minutes and 0.03 USD. The job
spends about 7.5 of its 8 minutes pulling the 6.97 GB house image before the container starts, and the
processing task holds its worker for the whole job.

---

## §C — Code for a Python or Bash task

**Status in Sandbox: blocked.** A workflow with a code archive fails before its first task with
`Execution environment preparation failed due to an internal server error`. The worker fetches the
service's copy of the code (§O) through the S3 gateway endpoint, and the endpoint's allow-list names no
MWAA Serverless bucket. 6i decision 7 holds the options. The packaging below is the guide's and was
verified locally.

### C1 — What the worker expects

- **One file or one archive.** A single `.py`, a single `.sh`, or a `.zip` holding several files; at
  most 250 MB, unzipped too, and 75 GB of code per account.
- **Everything at the archive's root**: your modules, your packages and every third-party package. The
  worker extracts the archive to `/usr/local/airflow/dags`, which is on `sys.path`, so a module at the
  root imports by its name.
- **Third-party packages built for the worker**: CPython 3.12, Linux, x86_64. A package installed for
  your laptop or for the house environment (Python 3.13) does not import there.
- **No package the worker already has.** The guide says a pre-installed package wins over the archive's
  copy (6i verification viii, unmeasured): Airflow,
  the Amazon provider, boto3 and botocore, dag-factory, PyYAML, lz4 and the AWS encryption SDK family.
  Write against the worker's boto3 1.43.1.
- **No `__pycache__` or `.pyc`**: bytecode from another platform may not load.
- **No secret**: the archive is copied by the service and stored outside the account.

### C2 — The layout

```
python-operator.zip          the archive: the CONTENTS of the staging folder, no folder of its own
├── demo_tasks.py            the module the task names: python_callable: demo_tasks.run
├── awsds_demo_job/          your own package, copied as it is
│   ├── __init__.py
│   ├── transform.py
│   └── s3.py
├── petl/                    a third-party package, installed for the worker
├── petl-1.7.28.dist-info/
└── ...
```

### C3 — Building it

`examples/sandbox-orchestration/operators/build.sh` is this procedure, with uv. By hand, with pip:

```bash
rm -rf build && mkdir build
cp demo_tasks.py build/
cp -R src/awsds_demo_job build/
pip install -r requirements.txt --target build \
    --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
find build -name __pycache__ -type d -prune -exec rm -rf {} +
(cd build && zip -qr ../python-operator.zip . -x '*.pyc')
```

With uv, the install line is
`uv pip install --target build --python-platform x86_64-manylinux2014 --python-version 3.12 --only-binary :all: -r requirements.txt`,
and `rm -f build/.lock` removes the lock file uv leaves in the target.

- `--only-binary` refuses a source distribution, which would compile for the machine that builds.
- The `cd build` makes every path relative to the folder, so the archive has no top-level `build/`.
- Check the root before uploading: `unzip -l python-operator.zip | head` lists `demo_tasks.py`, not
  `build/demo_tasks.py`.
- The worker has no internet, so every dependency is in the archive or pre-installed; nothing is
  installed at run time.

### C3a — A uv project

A project that uv manages, with a `pyproject.toml` and a `uv.lock`, is packaged by
`examples/sandbox-orchestration/operators/package-uv.sh`:

```bash
./examples/sandbox-orchestration/operators/package-uv.sh <project dir> <entry module .py> <archive .zip>
```

It runs five steps, each one a rule of C1:

1. `uv export --locked --no-dev --no-emit-project --prune <name> ...` writes the locked closure as a
   requirements file. `--locked` refuses a lock that no longer matches `pyproject.toml`, and `--prune`
   removes each package the worker pre-installs together with the dependencies only it needs, so `boto3`
   takes `s3transfer` and `jmespath` with it while `urllib3`, which `requests` also needs, stays.
2. `uv pip install --target <stage> --no-deps --python-platform x86_64-manylinux2014 --python-version 3.12
   --only-binary :all: -r <file>` installs the worker's wheels for that closure, with the lock's hashes.
3. `uv build --wheel` builds the project from its `pyproject.toml`, and the same install puts the wheel's
   package at the root. The project's `requires-python` must admit 3.12, or the install fails.
4. The entry module, the file `python_callable` names, is copied to the root beside the package.
5. uv's `.lock`, console scripts and bytecode are removed, the archive is zipped from inside the stage,
   and an archive over 250 MB unzipped is refused.

`OMIT="name ..."` prunes more packages. A dependency with no CPython 3.12 manylinux wheel fails step 2;
it cannot be built on a Mac for the worker.

**Measured 2026-10-11** on a throwaway uv project depending on `petl`, `requests`, `boto3` and `pyyaml`:
959,979 bytes, holding the project, `tasks.py`, `petl` and `requests` with `certifi`,
`charset_normalizer`, `idna` and `urllib3`; no `boto3`, `botocore`, `s3transfer`, `jmespath` or `yaml`;
`charset_normalizer`'s compiled modules tagged `cp312-cp312-manylinux2014_x86_64`.

**Keep the entry module thin.** The editor shows `python_callable` as a *File* and a *Function*, so a
root module such as `tasks.py` that imports from the package is what it can display. A dotted path into
the package, `pkg.module.function`, is unmeasured here.

### C4 — Naming the code in the definition

```yaml
run_project:
  operator: airflow.providers.standard.operators.python.PythonOperator
  dependencies: [wait_for_file]
  python_callable: demo_tasks.run
  op_kwargs:
    bucket: <projects bucket>
    inbox: <prefix>/inbox/
    outbox: <prefix>/outbox/
  retries: 0
```

`python_callable` is `<module>.<function>`, and the editor shows it as *File* `demo_tasks` and
*Function* `run`. The function receives `op_kwargs` as keyword arguments, and the Airflow context too if
it accepts `**kwargs`. A Bash task names `bash_command`; a script from the archive runs with
`/usr/local/airflow/dags` as its working directory. The template is
`examples/sandbox-orchestration/operators/python/demo-python-operator.yaml`.

### C5 — Giving the archive to the workflow

**The code is always one S3 object, never a folder.** The API's `Code` is an `S3Location`: a bucket, a key
and an optional version of a single `.py`, `.sh` or `.zip`. The worker extracts that one object, so a
prefix of loose files cannot be named, and a package with dependencies travels as a `.zip`.

- **In the portal**, *Settings → Storage → Python/Bash Operator Files* uploads files, and the *operator
  files S3 location* beside it is where they are stored (`dev/operatorFiles/` by default), not a source to
  read from. The guide: one file is stored as it is, several files are zipped into one archive, only
  `.py`, `.sh` and `.zip` are accepted, and the archive stays under 250 MB. Measured here: one `.zip`
  stored as uploaded, its S3 version pinned, its sha256 equal to the built archive's.
- **Through the API** (`create-workflow --code`, or Terraform's `awscc` from 1.99.0), the object can be
  any one the saver can read, such as an archive in the project's `shared/`. The service reads it at
  save time in the saver's session. Not exercised here.

**The portal guide's dependency recipe omits the platform flags** (`pip install --target ./package
your-dependency`): run on a Mac, it installs the Mac's wheels of any compiled package. Use C3 or C3a.

**A new version of the code needs a new save.** The workflow runs the copy taken at its last save, so
replacing the S3 object changes nothing until the workflow is saved or imported again.

---

## §V — Reading a run back

| Question | Instrument |
|---|---|
| Is the workflow on the project's role, network and key; which version runs; where is its code? | `./aws/sandbox-orchestration.py` (`SO-1`..`SO-3`), as `InfrastructureAccess` |
| How did each task end, and how long did it hold its worker? | `SO-4`; by hand, `aws mwaa-serverless list-task-instances --workflow-arn <arn> --run-id <id>`. Read a task's `DurationInSeconds`, never the run's |
| Why did a task fail? | its stream `workflow_id=<workflow>/run_id=<id>/task_id=<task>/attempt=<n>.log` in the workflow's log group |
| Did the job respect the boundary, and what did its container print? | `SO-5`; the job's stream in `/aws/sagemaker/ProcessingJobs` |
| Which door did a call take, and as whom? | `SO-8`; CloudTrail's `vpcEndpointId` and `userIdentity` on `CreateProcessingJob` |
| Did the result land, under which key? | `SO-7`; `aws s3api head-object` on the result |

**A failure in the editor's banner names no cause**: "Workflow execution failed, please check the task
execution logs for more details". The task log does, and for a processing task the job's
`FailureReason` and its container stream do.

**A failure before the first task** ("User template error: ...") is a template the service could not
render at run creation (§A).

---

## §X — Cleaning up

- **Delete a workflow** from the *Workflows* page. Its log group stays, with no retention.
- **Empty the inboxes** so the next run starts from a known state; the outboxes are the results.
- **Processing jobs cannot be deleted**: they stay listed, which is why `SO-5` fails only the newest.
- **The code archives** under `dev/operatorFiles/` stay with every version, since the bucket is versioned.
