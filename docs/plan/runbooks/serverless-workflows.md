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
| **§J** | the data scientist | a processing task in the house image, under the D13 boundary; a project with dependencies through `package-uv-job.py` |
| **§C** | the data scientist | code for a Python or Bash task: what the worker expects, packaging a uv project with `package-uv.sh`, the upload |
| **§V** | both | reading a run back, one instrument per question |
| **§X** | both | cleaning up |

**State, 2026-10-11.** **The processing task works end to end in Sandbox**: a sensor, a job in the house
image that summarises the sample, and the source deleted after the result landed under the project key
(run `f9L7CKQzmUQWQTR`). **A workflow with a code archive runs in Sandbox** (run `N05WyTNjUcdxbw0`):
a `PythonOperator` read the sample, wrote the same result and deleted the source. Before `vpc-v0.4.0`
its worker failed while preparing its environment, because the S3 gateway endpoint refused the bucket
the service keeps the code in (6i decision 7); a Bash task with an inline command, which has no archive,
ran all along. The exercise's archive was built by C6's recipe; C2's script is verified locally only. The two packaging scripts live in
`examples/sandbox-orchestration/operators/`: `package-uv.sh` for a Python or Bash task (§C2) and
`package-uv-job.py` for a processing job (§J1).

---

## §O — The pieces

| What | Where | Note |
|---|---|---|
| the definition | `s3://<projects bucket>/<domain>/<project>/dev/workflows/<name>.yaml` | written by the portal on each save; *View code* shows it |
| the code archive of a Python or Bash task | `.../dev/operatorFiles/<file>` | uploaded in *Settings → Storage*; one `.zip` is stored as uploaded, and the workflow pins its S3 version |
| the service's copy of that code | `mwaa-serverless-code-files-<AWS-owned account>-<region>-prod`, key `<account>/<workflow>/<version>/<upload's key>` | taken at each save and encrypted under the project key; each task's worker has `airflow-serverless.amazonaws.com` read it through the VPC's S3 gateway endpoint, whose policy must admit the family (`vpc-v0.4.0`, 6i decision 7) |
| the task logs | `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, one stream per task attempt | per project; no retention (`EXC-10`'s shape); the group outlives the workflow |
| a processing job's container output | `/aws/sagemaker/ProcessingJobs`, stream `<job>/algo-1-<n>` | account-wide: every project role in the account can read it |
| the identity | the project role, `datazone_usr_role_<project>_<env>`, session `AmazonMWAAServerless` on the worker, `SageMaker` inside a job | the D13 boundary applies to both |
| the network | the two private subnets and the project's security group, injected by the portal | no default route: AWS is reached through the VPC endpoints, S3 through the gateway endpoint |
| the key | the project CMK (`alias/awsds-<env>-project`) | the workflow's encryption, the job's volume and outputs, the bucket |

**The worker** is 1 vCPU and 3 GiB with Python 3.12, Airflow 3.0.6, the Amazon provider 9.32.0 and boto3
1.43.1. It has no internet and no proxy. A task holds its worker for its whole duration, sensor waits
included, and bills 0.088 USD per task-hour with a one-minute minimum. Measured on 2026-10-11:

- `python3` is `/opt/mwaa-serverless-venv/bin/python3`, 3.12.14, with pip 23.2.1 and boto3 1.43.1, and the
  tasks run as `mwaa-serverless-user`;
- the environment carries `AWS_REGION`, the seven variables the portal injects (`DataZoneDomainId`,
  `DataZoneProjectId`, `ProjectS3Path` among them) and no proxy variable;
- a name the Sandbox DNS Firewall does not list fails at resolution, as `[Errno 16] Device or resource
  busy` rather than a name error; `/awsds/sandbox/dns-firewall` shows the `BLOCK`.

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
| `ValidationException: Code not found in specified S3 location` | the save sent a code location under `dev/operatorFiles/` with no file there. A workflow with a Python or Bash task always sends the editor's pre-filled *Operator files zip S3 location* | upload the task's file in *Settings → Storage*; for a workflow that needs none (inline Bash, or no Python or Bash task), empty that field, and the save sends no `Code` |
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

### J1 — A project with dependencies: `package-uv-job.py`

The job has no network, so a project's dependencies either come with the house environment or travel in
the code input; nothing is installed at run time. Three things differ from a Python task's archive (§C):

- **The interpreter is the house environment's**, CPython 3.13 on Linux x86_64 today, not the worker's.
- **The code input is a folder, not an archive.** A `ProcessingInput` downloads an S3 prefix, and an
  extension module cannot be imported from a zip on `sys.path`.
- **The precedence is the worker's reversed.** `PYTHONPATH` comes before the house environment's
  site-packages, so a package in both would shadow the image's copy, the failure
  `images/dev-env/python/pyproject.toml` documents for numpy. The folder may hold only what the image
  lacks, and the project's versions must equal the image's for everything they share.

`examples/sandbox-orchestration/operators/package-uv-job.py` applies the three to a project uv manages.
Run it from a clone of this repository: in a space, where uv and the project's storage (`~/shared/`)
are both at hand, or on the laptop, carrying the folder to `shared/` afterwards.

1. **Prepare the project.**
   - It has a `pyproject.toml` and a current `uv.lock`.
   - Its `requires-python` admits the image's Python, 3.13 today.
   - Its own code is pure Python, and it runs as `python -m my_package` (a `__main__.py`).
2. **Check it against the image and build the folder:**

   ```bash
   ./examples/sandbox-orchestration/operators/package-uv-job.py ~/src/my-project /tmp/my-job
   ```

   The output folder must not exist yet. `--python` defaults to the `ARG PYTHON_VERSION` of
   `images/dev-env/Dockerfile` and `--platform` to `x86_64-manylinux_2_28`, so a new image moves the
   target with no flag. The house environment holds `onnxruntime` 1.30.0, which publishes no wheel older
   than `manylinux_2_28`, so the image's glibc is at least 2.28 and `manylinux2014` cannot describe it
   (measured 2026-10-11). Another value of either flag is accepted, with a note.
3. **If it reports a disagreement**, paste the block it prints into the project's `pyproject.toml`, run
   `uv lock`, and run step 2 again:

   ```toml
   [tool.uv]
   constraint-dependencies = [
     "boto3==1.43.92",
     ...
   ]
   ```

   The block pins every package the project shares with the image to the image's version. A lower bound
   of the project above an image version fails that lock, and then the dependency belongs in the image (a
   new image version, through [`dev-env.md`](dev-env.md)), not in the job. `--constraints` prints every
   image version in requirements form, for `uv pip compile -c` or `uv add -c`.
4. **Read what it printed**: the folder and its size, what comes from the image, what was vendored, and
   the top level, which is the project and the vendored packages only. Its last lines are the next steps.
5. **Copy the folder into the project's storage under a name of its own per version.** A processing input
   downloads the whole prefix, so a copy over an older folder would mix two versions. In a space:

   ```bash
   cp -r /tmp/my-job ~/shared/jobs/my-job-0.2.0
   ```

6. **Name it in the job's `config`**, beside the boundary's settings (§J), and import the definition (§A):

   ```yaml
   ProcessingInputs:
     - InputName: code
       S3Input:
         S3Uri: s3://<projects bucket>/<domain>/<project>/shared/jobs/my-job-0.2.0/
         LocalPath: /opt/ml/processing/code
         S3DataType: S3Prefix
         S3InputMode: File
         S3DataDistributionType: FullyReplicated
   AppSpecification:
     ContainerEntrypoint: [/bin/bash, -c]
     ContainerArguments:
       - 'sudo -n chown "$(id -u)" /opt/ml/processing/outbox && exec /opt/awsds/venv/bin/python -m my_package --input /opt/ml/processing/inbox --output /opt/ml/processing/outbox'
   Environment:
     PYTHONPATH: /opt/ml/processing/code
   ```

7. **A new image version changes the target.** Run the script from the commit that built the image the
   job names, so that its lock and its Dockerfile are that image's. A new version of the code is steps
   2, 5 and 6 under a new folder name. The job reads the prefix at each run, with no copy taken at a
   save, so this path works in Sandbox today.

**When the script refuses:**

| It says | Meaning | What to do |
|---|---|---|
| `no uv.lock in ...` | the project was never locked | `uv lock` in the project |
| `... exists - name a folder that does not` | the output folder is there already | a new folder, or remove the old one |
| `the project's lock and the house environment disagree` | a shared package at another version | step 3 |
| `not pure Python, so it cannot be built here for the job` | the project has extension modules | build its wheel on the target platform, in a pipeline (Stage 8) |
| `no wheels with a matching platform tag` | a vendored dependency publishes no wheel for the target | another version or another package, or the image |

**Measured 2026-10-11** on a throwaway uv project depending on `petl`, `requests`, `boto3` and `pyyaml`:
its fresh lock disagreed with the image on `boto3`, `botocore`, `charset-normalizer`, `idna` and
`urllib3`; with the printed block and a re-lock, 12 packages came from the image and only `petl` was
vendored, a 1.2 MB folder. The image's markers are evaluated by the script rather than by a resolver,
since the image holds `torch` from PyTorch's own index and packages with no wheel for every Python,
which a resolver refuses.

**The exercise's own job** needs none of this: `awsds-demo-job` has no dependencies, so its input is its
source tree, `shared/awsds-demo-job/`, with `PYTHONPATH` at `/opt/ml/processing/code/src`.

**The workflow deletes the source, not the job**: an isolated container cannot reach S3. The third task
is `S3DeleteObjectsOperator` on the inbox prefix, after the processing task.

**Print counts and paths, never data.** The container's output goes to an account-wide log group (§O).

**What a run costs and how long it takes** (measured 2026-10-11): about 15 minutes and 0.03 USD. The job
spends about 7.5 of its 8 minutes pulling the 6.97 GB house image before the container starts, and the
processing task holds its worker for the whole job.

---

## §C — Code for a Python or Bash task

**Status in Sandbox: runs since 2026-10-11.** The worker fetches the service's copy of the code (§O)
through the S3 gateway endpoint. Where the endpoint's policy does not admit
`mwaa-serverless-code-files-*-<region>-prod` (any VPC on `vpc-v0.3.1`, Staging and Production today), a
workflow with a code archive fails before its first task with `Execution environment preparation failed
due to an internal server error`, and only a CloudTrail network activity event names the refusal. C6's
recipe built the archive that ran; C2's script is verified locally.

### C1 — What the worker expects

- **One file or one archive.** A single `.py`, a single `.sh`, or a `.zip` holding several files; at
  most 250 MB, unzipped too, and 75 GB of code per account.
- **Everything at the archive's root**: your modules, your packages and every third-party package. The
  worker extracts the archive to `/usr/local/airflow/dags`, which is on `sys.path`, so a module at the
  root imports by its name.
- **Third-party packages built for the worker**: CPython 3.12 on Linux x86_64 today. A package installed
  for your laptop or for the house environment (Python 3.13) does not import there.
- **No package the worker already has.** A pre-installed package wins over the archive's copy (measured
  2026-10-11: the archive's PyYAML 6.0.1 lost to the worker's 6.0.2): Airflow, the Amazon provider, boto3
  and botocore, dag-factory, PyYAML, lz4 and the AWS encryption SDK family. Write against the worker's
  boto3 1.43.1.
- **No `__pycache__` or `.pyc`**: bytecode from another platform may not load.
- **No secret**: the archive is copied by the service and stored outside the account.

### C2 — Packaging a uv project with `package-uv.sh`

`examples/sandbox-orchestration/operators/package-uv.sh` turns a project that uv manages into the archive
C1 describes. Run it from a clone of this repository, where uv can reach PyPI: on the laptop, whose
browser uploads the archive, or in a space, which carries uv, and then download the archive from the
file browser.

1. **Prepare the project.**
   - It has a `pyproject.toml` and a current `uv.lock`: run `uv lock` in the project after any change.
   - Its `requires-python` admits the worker's Python, 3.12 today.
   - Its own code is pure Python. A project with extension modules cannot be built on a laptop for the
     worker, and the script refuses it.
   - An entry module, a small file beside the package rather than inside it, holds the function the
     task calls:

     ```python
     # tasks.py
     from my_package import pipeline


     def run(bucket: str, inbox: str, outbox: str, **_context):
         return pipeline.process(bucket, inbox, outbox)
     ```

2. **Run the script**, naming the project, the entry module and the archive to write:

   ```bash
   ./examples/sandbox-orchestration/operators/package-uv.sh ~/src/my-project ~/src/my-project/tasks.py ~/Downloads/my-task.zip
   ```

   `--python X.Y` and `--platform TAG` change the target; the defaults, 3.12 and `x86_64-manylinux2014`,
   are the worker the guide describes. The service can move the worker to another interpreter without
   notice, and a task log names the one it ran, in its paths (`.../python3.12/site-packages/...`): when
   that path changes, pass the new version. `OMIT="name ..."` leaves out more packages.
3. **Read what it printed**: the archive's size and its top level, which lists your package, the entry
   module and the third-party packages, and none of the worker's own (`boto3`, `botocore`, `yaml`,
   Airflow). Its last line is the next step.
4. **Upload the archive** in the workflow's *Settings → Storage → Python/Bash Operator Files*, and save.
5. **Name the callable** in the task (C4): `python_callable: tasks.run`, which the editor shows as *File*
   `tasks` and *Function* `run`. A Bash task runs `python3 -m my_package ...` from
   `/usr/local/airflow/dags`, where the archive is extracted.
6. **A new version of the code** is the same three moves: run the script, upload, save. The workflow
   keeps running the copy taken at its last save.

**When the script refuses:**

| It says | Meaning | What to do |
|---|---|---|
| `The lockfile at uv.lock needs to be updated` | `pyproject.toml` changed after the lock | `uv lock` in the project |
| `no wheels with a matching platform tag` | a dependency publishes no wheel for the target | it cannot travel in the archive: another version or another package |
| `not pure Python, cannot be built here for the worker` | the project has extension modules | build its wheel on the target platform, in a pipeline (Stage 8) |
| `over the 250 MB limit` | the archive is too big | `OMIT` more, or drop dependencies |

**What it does**, each step one rule of C1:

1. `uv export --locked --no-dev --no-emit-project --prune <name> ...` writes the locked closure as a
   requirements file. `--locked` refuses a stale lock, and `--prune` removes each package the worker
   pre-installs together with the dependencies only it needs, so `boto3` takes `s3transfer` and
   `jmespath` with it while `urllib3`, which `requests` also needs, stays.
2. `uv pip install --target <stage> --no-deps --only-binary :all: --python-version <X.Y>
   --python-platform <TAG> -r <file>` installs the target's wheels for that closure, with the lock's
   hashes. `--only-binary` refuses a source distribution, which would build for the laptop.
3. `uv build --wheel` builds the project from its `pyproject.toml`, refused unless it is pure Python, and
   the same install puts its package at the root.
4. The entry module is copied to the root.
5. uv's `.lock`, console scripts and bytecode are removed, and the stage is zipped by Python, since the
   house image carries `unzip` but no `zip`; an archive over 250 MB unzipped is refused.

**Measured 2026-10-11** on a throwaway uv project depending on `petl`, `requests`, `boto3` and `pyyaml`:
about 0.9 MB, holding the project, `tasks.py`, `petl` and `requests` with `certifi`,
`charset_normalizer`, `idna` and `urllib3`; no `boto3`, `botocore`, `s3transfer`, `jmespath` or `yaml`;
`charset_normalizer`'s compiled modules tagged `cp312-cp312-manylinux2014_x86_64`, and `cpython-313`
with `--python 3.13`.

**Keep the entry module thin.** The editor shows `python_callable` as a *File* and a *Function*, so a
root module that imports from the package is what it can display. A dotted path into the package,
`pkg.module.function`, is unmeasured here.

### C3 — What the archive holds

```
my-task.zip                  the CONTENTS of the staging folder, no folder of its own
├── tasks.py                 the entry module: python_callable: tasks.run
├── my_package/              your own package, from its wheel
├── my_package-0.1.0.dist-info/
├── petl/                    a third-party package, built for the worker
├── petl-1.7.29.dist-info/
└── ...
```

### C4 — Naming the code in the definition

```yaml
run_project:
  operator: airflow.providers.standard.operators.python.PythonOperator
  dependencies: [wait_for_file]
  python_callable: tasks.run
  op_kwargs:
    bucket: <projects bucket>
    inbox: <prefix>/inbox/
    outbox: <prefix>/outbox/
  retries: 0
```

`python_callable` is `<module>.<function>`. The function receives `op_kwargs` as keyword arguments, and
the Airflow context too if it accepts `**kwargs`. A Bash task names `bash_command`; a script from the
archive runs with `/usr/local/airflow/dags` as its working directory, the guide says. **An inline
`bash_command` needs no archive** and runs in a temporary folder (`/var/tmp/airflowtmp…`), measured
2026-10-11; `operators/bash/demo-bash-operator.probe.yaml` is the example, and the service renders it
through Jinja, so it carries no double brace. The exercise's template is
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
your-dependency`): run on a Mac, it installs the Mac's wheels of any compiled package. Use C2, or C6
by hand.

**A new version of the code needs a new save.** The workflow runs the copy taken at its last save, so
replacing the S3 object changes nothing until the workflow is saved or imported again.

### C6 — By hand, without uv

For a project uv does not manage. `examples/sandbox-orchestration/operators/build.sh` builds the
exercise's own archives this way.

```bash
rm -rf build && mkdir build
cp tasks.py build/
cp -R src/my_package build/
pip install -r requirements.txt --target build \
    --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:
find build -name __pycache__ -type d -prune -exec rm -rf {} +
(cd build && zip -qr ../my-task.zip . -x '*.pyc')
```

- Leave out of `requirements.txt` every package the worker pre-installs (C1).
- The `cd build` makes every path relative to the folder, so the archive has no top-level `build/`;
  `unzip -l my-task.zip | head` lists `tasks.py`, not `build/tasks.py`.
- With uv's pip interface the install line is `uv pip install --target build --python-platform
  x86_64-manylinux2014 --python-version 3.12 --only-binary :all: -r requirements.txt`, and
  `rm -f build/.lock` removes the lock file it leaves.

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
