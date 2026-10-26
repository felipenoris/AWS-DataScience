# Runbook — Serverless workflows in a SageMaker project

*The stage that exercised this is [`stage-06i-sandbox-orchestration.md`](../stages/stage-06i-sandbox-orchestration.md),
and its readings are in [`log-stage-06i`](../../log/log-stage-06i-sandbox-orchestration.md). The reference files,
with a placeholder for every account-scoped value, are in
[`examples/sandbox-orchestration/`](../../../examples/sandbox-orchestration/README.md). The instrument is
`./aws/sandbox-orchestration.py`. The tool that fills a definition's placeholders and packages a task's
code is [`awsds-workflows`](https://github.com/felipenoris/awsds-workflows) (§T).*

A serverless workflow is a MWAA Serverless workflow that the project's *Workflows* page creates: a YAML
definition (Airflow 3.0.6 through dag-factory), run by workers the service starts per task, as the
project role, inside the project's network. Since [D41](../decisions/D41-sagemaker-application.md)
(2026-10-15) an application's workflow is created instead from its repository by the CI/CD CLI, which
deploys it to the `dev` and `test` projects (Stage 10 steps 2.1-2.2; the deploy to `dev` measured in the
lab that day). This runbook covers the three task kinds Stage 6i exercised: a SageMaker processing job in
the house image, a `PythonOperator` and a `BashOperator`.

| Section | Audience | What it holds |
|---|---|---|
| **§O** | both | the pieces: where the definition, the code, the logs and the runs live |
| **§T** | both | the tool, `awsds-workflows`: installing it, where it runs, and this lab's values |
| **§G** | infrastructure | the grant a project needs before its first processing task, once per project |
| **§A** | the data scientist | authoring rules every workflow obeys: the editor, the import, a workflow the CI/CD CLI made, the templates, the sensor |
| **§J** | the data scientist | a processing task in the house image, under the D13 boundary; a project with dependencies through `awsds-workflows package-job` |
| **§C** | the data scientist | code for a Python or Bash task: what the worker expects, packaging a uv project with `awsds-workflows package-task`, the upload |
| **§V** | both | reading a run back, one instrument per question |
| **§X** | both | cleaning up |

**State, 2026-10-12.** **The processing task works end to end in Sandbox**: a sensor, a job in the house
image that summarises the sample, and the source deleted after the result landed under the project key
(run `f9L7CKQzmUQWQTR`). **So does a project with dependencies** (run `aB2zorz48GP67hx`): the folder
`package-uv-job.py` built in a space, its pure-Python and extension modules imported from the code input
(§J1). **A workflow with a code archive runs in Sandbox** (run `N05WyTNjUcdxbw0`):
a `PythonOperator` read the sample, wrote the same result and deleted the source. Before `vpc-v0.4.0`
its worker failed while preparing its environment, because the S3 gateway endpoint refused the bucket
the service keeps the code in (6i decision 7); a Bash task with an inline command, which has no archive,
ran all along. The exercise's archive was built by C6's recipe. **Since 2026-10-12 the tool is
`awsds-workflows`** (§T), which replaced this repository's three scripts: `package-job` the
`package-uv-job.py` that built the folder above, `package-task` the `package-uv.sh` of §C2, and `render`
the examples' `render.py`. On the laptop each printed or built what its script did; no folder or archive
of the package has run in a job or on a worker yet.

---

## §O — The pieces

| What | Where | Note |
|---|---|---|
| the definition | `s3://<projects bucket>/<domain>/<project>/dev/workflows/<name>.yaml` | written by the portal on each save; *View code* shows it |
| the code archive of a Python or Bash task | `.../dev/operatorFiles/<file>` | uploaded in *Settings → Storage*; one `.zip` is stored as uploaded, and the workflow pins its S3 version |
| the service's copy of that code | `mwaa-serverless-code-files-<AWS-owned account>-<region>-prod`, key `<account>/<workflow>/<version>/<upload's key>` | taken at each save and encrypted under the project key; each task's worker has `airflow-serverless.amazonaws.com` read it through the VPC's S3 gateway endpoint, whose policy must admit the family (`vpc-v0.4.0`, 6i decision 7) |
| the task logs | `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, one stream per task attempt | per project; no retention (`EXC-10`'s shape); the group exists from the workflow's first save, before any run, and outlives the workflow |
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

**Two identities, one browser.** The portal runs as the Data Scientist user, and the readings in §V as the
infrastructure user. A CLI login whose browser step is answered in the browser holding the portal session
ends that session, and the next portal act lands on the sign-in page (seen twice on 2026-10-11, each
time right after such a login; the cause is inferred, not isolated).
`./aws/login.py` passes `--no-browser`: open the URL it prints in another browser or a private window
([`aws/AWS-CLI.md`](../../../aws/AWS-CLI.md), "Signing in"). The same day the CLI's `awsds` token was found
deleted from `~/.aws/sso/cache` mid-session, by an unknown hand; a new login restores it.

---

## §T — The tool: `awsds-workflows`

[`awsds-workflows`](https://github.com/felipenoris/awsds-workflows) is the package this runbook's commands
call. Its documentation, <https://felipenoris.github.io/awsds-workflows/> (in Portuguese), is the
reference for every option and every message; this section says how this lab uses it.

| Command | What it does | What it replaced on 2026-10-12 |
|---|---|---|
| `render <file>` | prints the file with its placeholders filled; with `--placeholders`, a saved definition with its values turned back into placeholders | `examples/sandbox-orchestration/render.py` |
| `values` | prints the values as JSON, the format of `--values-file` | `render.py --values` |
| `compare <first> <second>` | prints the content differences between two definitions (§A) | — |
| `package-job` | builds a processing job's code folder for the job's image (§J1) | `operators/package-uv-job.py` |
| `job-constraints` | prints the image environment's versions as requirements (§J1) | `package-uv-job.py --constraints` |
| `package-task` | builds a Python or Bash task's archive for the worker (§C2) | `operators/package-uv.sh` |
| `prepare-offline <project> <archive>` | writes the `.tar.gz` of a project folder prepared with its own interpreter, a processing job's code input that the job extracts on its volume; in the package since 2026-10-13 (`6bdbcad`) | — |
| `lint <path>` | checks an application folder, or one definition, against the rules of MWAA Serverless and of the pipeline, offline: each refusal is a line `file: rule: reason` with exit 1, otherwise `ok`; `--promoted --prefix` reads one rendered copy, `--image-repository` and `--instance-type` restrict a processing job. Since `ff25eae` (2026-10-24) the promoted mode refuses a Glue task that keeps `create_job_kwargs`, `script_location`, `iam_role_arn`, `update_config` or `job_desc` (Stage 10 2.3's rule (6)), and the manifest rule an `include` holding `*`, `?` or `[`, a glob the CLI 1.0.9's `bundle` does not expand. The rules are [Stage 8](../stages/stage-08-cicd-pipelines.md) 5.6's, and `app-etl`'s template (`examples/app-etl/.gitlab-ci.yml`) runs `lint .` with both, the application's repository and the ceiling's instance types | — |
| `lint-plan <plan.json> --prefix <s3-prefix>` | checks the Glue jobs of a saved Terraform plan, the JSON of `terraform show -json`, before the apply: in each `aws_glue_job` the apply leaves, the script and every file or module its arguments name lie under a `--prefix` (repeatable), and no module is named by its PyPI name; `ok: N job(s) do Glue: …` with exit 0, otherwise one `file: glue: address: reason` line per refusal with exit 1. Stage 10 2.3's rule (2c), since `ff25eae`; the promotion legs run it through `scripts/lint-plan.py` | — |

**Install it by URL, from its `main`**, never by name: the name is free on PyPI, and a package someone
else published there under it would install instead (the package's documentation, read 2026-10-11).

```bash
uv tool install git+https://github.com/felipenoris/awsds-workflows
```

```bash
uv tool upgrade awsds-workflows
```

The second command takes the newest commit of `main`: measured 2026-10-12 with uv 0.12.13, on an install
from a local git remote that gained a commit. The commit installed is the `commit_id` in
`direct_url.json`, under `$(uv tool dir)/awsds-workflows/`. The laptop's install was at `c9a4c20` on
2026-10-18, older than `lint` (`3c1708e`, 2026-10-16), and answered `invalid choice: 'lint'`; still at
`c9a4c20` on 2026-10-24, it answered `invalid choice: 'lint-plan'`. The
package needs Python 3.12 or newer, which uv installs. It calls `uv` as a program, and `aws` for
`--profile`.

**Where it runs:**

- **the laptop**: the readings below ran there on 2026-10-12. uv reaches PyPI, and `--profile` reads the
  account;
- **a space**: the tool not run there yet, its installation included; its `scripts/space_values.py` runs
  from a clone with no installation (below). The script `package-job` replaced built a
  job folder in a space (Stage 6i step 3.6). uv in a house-image space finds the distribution's
  interpreter only ([`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md)), so a project is packaged for the
  house environment with `UV_PYTHON="$AWSDS_PYTHON_ENV/bin/python"` set: 3.13 up to `default-v0.6.0`,
  3.12 from `default-v0.7.0`. `package-uv-job.py` set it on its own; the package passes on what the
  environment sets, which its documentation measured in a simulated space.

**This lab's values** are read as the infrastructure user (`felipenoris+infrastructure_user@…`), profile
`awsds-infra-sandbox-1`, account `Sandbox Account 1`, permission set `InfrastructureAccess`, with STS,
IAM, EC2 and SageMaker reads only:

```bash
awsds-workflows render <file> --profile awsds-infra-sandbox-1 --subnet-name 'awsds-sandbox-private-*' --image-name awsds-sandbox-dev-env
```

- `--subnet-name` matches the Sandbox private subnets, which fill `SUBNET_AZ1` and `SUBNET_AZ2` in zone
  order;
- `--image-name` reads the newest version of the house image registered in Sandbox, pinned by digest, as
  `JOB_IMAGE_URI`;
- `--project <id>` picks the project when the account holds more than one;
- `values` takes the same flags and prints the JSON, the account id included, so it is written under
  `aws/output/`, which is untracked, and never into a tracked file.

A data scientist without that identity reads the same values from a project space with the package's
`scripts/space_values.py`, which prints what `values` prints without `--image-name`; in a Sandbox space
on 2026-10-11 the two printed the same JSON, byte for byte
([its documentation](https://felipenoris.github.io/awsds-workflows/awsds_workflows.html#os-valores-de-dentro-de-um-espaco)).
On 2026-10-26 it ran from a shallow clone under `/tmp`, on the distribution's Python, for the values a
manifest reads in the `dev` deploy ([`sagemaker-application.md`](sagemaker-application.md) §D step 3); the
clone reaches GitHub through the proxy.

**The placeholders** of this repository's files are the package's names: `REGION`, `ACCOUNT_ID`,
`PROJECT_ROLE_NAME`, `PROJECT_ID`, `DOMAIN_ID`, `PROJECTS_BUCKET`, `PROJECT_KEY_ID`, `PROJECT_SG`,
`SUBNET_AZ1`, `SUBNET_AZ2` and `JOB_IMAGE_URI`. `render` refuses a file holding a placeholder with no
value, and names every one.

**Measured 2026-10-12 on the laptop**, the package at `937a66a` and again at `3499530`, the `main` of
that hour, against the scripts at `c0baddd`, with the same results at both commits:

- `render`, with the live Sandbox values, printed each of the twelve YAML files of
  `examples/sandbox-orchestration/` byte for byte as `render.py` printed it under the old names, and
  `--placeholders` gave each file back; `values` read what `render.py --values` read, its thirteen names
  folded into eleven;
- `package-job` built `awsds-demo-deps`'s folder as the same 176 files, different only in installation
  metadata: the temporary wheel's path, and the hash in `RECORD` of a console script the folder drops;
- `job-constraints`, over the house environment exported from its lock (§J1), printed the 452 versions
  `package-uv-job.py --constraints` printed;
- `package-task` built the 278 entries `package-uv.sh` built for a throwaway project depending on
  `petl`, `requests`, `boto3` and `pyyaml`.

---

## §G — The grant a project needs, once per project

A project role cannot run `SageMakerProcessingOperator`, nor create a Glue job from `GlueJobOperator`,
with the blueprint's policies alone, for three reasons, two measured on 2026-10-10 and one on 2026-10-16:

- **The operator describes the job name before creating it**, and the blueprint lets a project role
  describe only a job tagged with its own project. A name not yet taken carries no tag, so the first run
  fails with `AccessDeniedException` on `DescribeProcessingJob` before any job exists.
- **A create that carries tags is also authorized as `sagemaker:AddTags`**, and the blueprint excludes
  every `AmazonDataZone*` key from `AddTags` while requiring the job to carry `AmazonDataZoneProject`. The
  second run fails with `AccessDeniedException` on `sagemaker:AddTags`.
- **`GlueJobOperator` reads the job it names with `glue:GetJob` before it creates or updates it**, and the
  blueprint lets a project role read only a job tagged with its own project. A name not yet taken
  carries no tag, so the first run fails with `AccessDenied` on `glue:GetJob` before any job exists
  (the CI/CD CLI's run `u4AFogXA74olkqo`, 2026-10-16).

The grant is `terraform-live/sandbox/workflows/`, one policy and one attachment per project role:

1. Add the project role's name to `project_roles` in `variables.tf`. The role is
   `datazone_usr_role_<project id>_<environment id>`, read with `aws iam list-roles`.
2. Plan and apply the slice as the infrastructure user, `InfrastructureAccess`, in the account the project
   lives in. A precondition refuses a role without the D13 boundary.

Stage 18's deployment project in Staging held, until its removal on 2026-10-22, the same three statements from
`terraform-live/staging/studio/workflows.tf`, for the stage's life: its first run stopped on `glue:GetJob`
without them (2026-10-19, run `7MMhwSySe5SOWd1`).

The policy allows `DescribeProcessingJob` on a job with no project tag, `AddTags` of the caller's own
project tag alone, on a job with no project tag or with the caller's, and `glue:GetJob` on a job with no
project tag whose name ends with the caller's project id, `<app>-<project id>`, the name an application
gives its job (user, 2026-10-16). Another project's jobs stay out of reach. With the Glue statement applied, `CreateJob` with the project tag passed with nothing more, unlike the
processing job's `AddTags`: `GetJob` answered `EntityNotFoundException`, then `CreateJob` and `StartJobRun`
passed (Sandbox, 2026-10-16, 6i's log; Staging, 2026-10-19, Stage 18 4.4).

---

## §A — Authoring rules every workflow obeys

**Create empty, then import.** On the *Workflows* page, create a workflow, then *Actions → Import
definition file* with the rendered YAML (`awsds-workflows render <file> <§T's flags> > ~/Downloads/<name>.yaml`).
The editor's forms cannot express everything a definition can (§J), and an import keeps every field: the
saved definition differs from the imported one only by `is_paused_upon_creation: false`, keys reordered
and long strings folded.

**What the portal saved, against the file it came from.** `SO-3` writes every version of a workflow's
definition under `aws/output/sandbox-orchestration/<workflow>/`. With its placeholders back, `compare`
prints only what changed in content against `<file>`, the one imported; comments, key order, quotes and
folding do not count:

```bash
awsds-workflows render --placeholders aws/output/sandbox-orchestration/<workflow>/<nn>-<version>.yaml <§T's flags> > /tmp/saved.yaml
```

```bash
awsds-workflows compare <file> /tmp/saved.yaml
```

A change made in the portal that should stay is then written into the file by hand, with placeholders.
Measured 2026-10-12 on the six definitions Stage 6i recorded: each differs from its file by
`is_paused_upon_creation: false`, which the portal adds at every save and the service ignores, and two
by an edit the stage made on purpose ([`examples/sandbox-orchestration/`](../../../examples/sandbox-orchestration/README.md#placeholders)).

**An import does not replace a saved workflow.** Imported into a saved workflow's editor, the file becomes
a new workflow under the bare name, and its save is refused with `ConflictException: Workflow with given
name already exists` (measured 2026-10-11). Delete the old workflow first (*Workflows* list, *Delete
workflow*, type "confirm"), then save: CloudTrail reads `DeleteWorkflow` then `CreateWorkflow`, the ARN
suffix changes and the run and version history restart. The log group is named after the workflow and
keeps every run's logs.

**A workflow the CI/CD CLI made is read in the portal, never saved or run there.** It is named
`<application>_<project>_<workflow>`, carries the tag `CreatedBy=SMUS-CICD`, and its YAML lives where
the application's manifest put it, under the project's `shared/` in the lab's deploy (D41). Change it in
the application's repository and deploy again with the CLI.

- **A save from the portal** replaces the workflow whole (Lesson 60) and writes the editor's copy under
  `dev/workflows/`, a second definition beside the CLI's. Its Tags tab shows the CLI's six tags under a
  notice that tags come from the definition file, where the CLI never wrote them (it tags by
  `TagResource`), so the save would also drop the tags the CLI's `monitor` and `logs` filter by. Read in
  the portal on 2026-10-15 with no save; no save has measured either.
- **A run started from the portal** passes no `OverrideParameters`. The CLI writes each `{env.VAR}` of
  the workflow as `{{ params.VAR }}` and fills it only in a run it starts, from the stage's
  `environment_variables` (its 1.0.9 code, read 2026-10-15), so such a run gets none of their values.
  It carries the service's own `mwaa_serverless_workflow_id` alone and fails at the DAG's template
  before any task: *"User template error: DAG template rendering failed: 'dict object' has no attribute
  'SUBNET_AZ1'"* ([Stage 10](../stages/stage-10-orchestration-promotion.md) verification xxix, read
  2026-10-26). Start the run from the CLI, or with `start-workflow-run` carrying the parameters as
  `OverrideParameters`: DataZone does not gate a start, which takes the IAM action and, in the starter's
  session, `kms:GenerateDataKey` and `kms:Decrypt` on the project key (Stage 18 0.4, 2026-10-19). The
  CLI's `run` returns once the service accepts the start; `get-workflow-run` follows the run to its end.

**Save errors and their way through:**

| The portal says | What happened | Way through |
|---|---|---|
| `ValidationException: Code not found in specified S3 location` | the save sent a code location under `dev/operatorFiles/` with no file there. The editor pre-fills *Operator files zip S3 location* on every new workflow, a processing-only one included (2026-10-11), and a workflow with a Python or Bash task always sends it | upload the task's file in *Settings → Storage*; for a workflow that needs none (inline Bash, or no Python or Bash task), empty that field before the save, and the save sends no `Code` |
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
- `/opt/awsds/venv/bin/python` is the house environment (Python 3.13 up to `default-v0.6.0`, 3.12 from
  `default-v0.7.0`); `/opt/conda/bin/python` is the distribution's (3.12).

### J1 — A project with dependencies: `awsds-workflows package-job`

The job has no network, so a project's dependencies either come with the house environment or travel in
the code input; nothing is installed at run time. Three things differ from a Python task's archive (§C):

- **The interpreter is the house environment's**, not the worker's: CPython on Linux x86_64 at the image's
  `ARG PYTHON_VERSION`, 3.13 up to `default-v0.6.0` and 3.12 from `default-v0.7.0`.
- **The code input is a folder, not an archive.** A `ProcessingInput` downloads an S3 prefix, and an
  extension module cannot be imported from a zip on `sys.path`.
- **The precedence is the worker's reversed.** `PYTHONPATH` comes before the house environment's
  site-packages, so a package in both would shadow the image's copy, the failure
  `gitlab/awsds/dev-env/dev-env/python/pyproject.toml` documents for numpy. The folder may hold only what the image
  lacks, and the project's versions must equal the image's for everything they share.

`awsds-workflows package-job` (§T) applies the three to a project uv manages, against a file that lists
the image's environment. Run it from a clone of this repository, for the house environment's lock: on
the laptop, carrying the folder to `shared/` afterwards, or in a space, where the project's storage
(`~/shared/`) is at hand. In a house-image space uv finds only the distribution's interpreter, since the
image sets `UV_PYTHON_DOWNLOADS=never` and puts the house interpreter on no search path, so `package-job`
runs there with `UV_PYTHON="$AWSDS_PYTHON_ENV/bin/python"` set (§T); the package has not run in a space yet.

1. **Prepare the project.**
   - It has a `pyproject.toml` and a current `uv.lock`.
   - Its `requires-python` admits the image's Python: 3.12 from `default-v0.7.0`, 3.13 up to `default-v0.6.0`.
   - Its own code is pure Python, and it runs as `python -m my_package` (a `__main__.py`).
2. **Export the house environment, then check the project against it and build the folder**, from the
   recipe at the commit that built the image the job names: this repository's copy when
   `gitlab/mirror.json` names that commit, a clone of the GitLab project `awsds/dev-env` at it otherwise:

   ```bash
   uv export --frozen --no-dev --no-emit-project --no-hashes --directory gitlab/awsds/dev-env/dev-env/python > /tmp/house-env.txt
   ```

   ```bash
   awsds-workflows package-job ~/src/my-project /tmp/my-job --environment /tmp/house-env.txt --python 3.12
   ```

   The lock is the house environment: the image installs it with `uv sync --frozen`
   ([`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md)). The export reads the lock and needs no
   interpreter: it ran with downloads off and none to find (2026-10-12). `--python` is the
   `ARG PYTHON_VERSION` of `gitlab/awsds/dev-env/dev-env/Dockerfile` at that commit, 3.12 from `default-v0.7.0` and 3.13
   up to `default-v0.6.0`; `package-uv-job.py` read it on its own. The output folder must not exist yet. `--platform` defaults to `x86_64-manylinux_2_28`: the house
   environment holds `onnxruntime` 1.30.0, which publishes no wheel older than `manylinux_2_28`, so the
   image's glibc is at least 2.28 and `manylinux2014` cannot describe it (measured 2026-10-11).
3. **If it reports a disagreement**, paste the block it prints into the project's `pyproject.toml`, run
   `uv lock`, and run step 2's `package-job` again:

   ```toml
   [tool.uv]
   constraint-dependencies = [
     "boto3==1.43.92",
     ...
   ]
   ```

   The block pins every package the project shares with the image to the image's version, which also puts
   the project's local tests on the versions the job imports. A lower bound
   of the project above an image version fails that lock, and then the dependency belongs in the image (a
   new image version, through [`dev-env.md`](dev-env.md)), not in the job.
   `awsds-workflows job-constraints --environment /tmp/house-env.txt --python 3.12` prints every image
   version in requirements form, for `uv pip compile -c` or `uv add -c`.
4. **Read what it printed**: the folder and its size, what comes from the image (`da imagem`), what the
   folder carries (`na pasta`), and the top level (`raiz`), which is the project and the vendored
   packages only. Its last line is the next step.
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

7. **A new image version changes the target.** Export the environment, and read `--python`, from the
   commit that built the image the job names, so that the lock and the Dockerfile are that image's. A
   new version of the code is steps 2, 5 and 6 under a new folder name. The job reads the prefix at each
   run, with no copy taken at a save, so this path works in Sandbox today.

**When `package-job` refuses**, the messages a reader of this lab meets are below; the package's
documentation lists every one
([*A pasta de código com `package-job`*](https://felipenoris.github.io/awsds-workflows/awsds_workflows.html#a-pasta-de-codigo-com-package-job)).
uv's own messages arrive in English, after `uv ... falhou:`.

| It says | Meaning | What to do |
|---|---|---|
| `não há uv.lock em ...` | the project was never locked | `uv lock` in the project |
| `... já existe: nomeie uma pasta nova` | the output folder is there already | a new folder, or remove the old one |
| `o lock do projeto e o ambiente da imagem discordam` | a shared package at another version | step 3 |
| `não é Python puro` | the project has extension modules | build its wheel on the target platform, in a pipeline (Stage 8) |
| `no wheels with a matching platform tag` | a vendored dependency publishes no wheel for the target | another version or another package, or the image |
| `No interpreter found for Python <version>` | uv found no interpreter at the house environment's version for the project's lock check and build | in a house-image space, `UV_PYTHON="$AWSDS_PYTHON_ENV/bin/python"`; a space on another image has no `AWSDS_PYTHON_ENV`, so a house-image space or the laptop |

**Measured 2026-10-11** with `package-uv-job.py`, on a throwaway uv project depending on `petl`,
`requests`, `boto3` and `pyyaml`: its fresh lock disagreed with the image on `boto3`, `botocore`,
`charset-normalizer`, `idna` and `urllib3`; with the printed block and a re-lock, 12 packages came from
the image and only `petl` was vendored, a 1.2 MB folder. The image's markers are evaluated by the tool
rather than by a resolver, since the image holds `torch` from PyTorch's own index and packages with no
wheel for every Python, which a resolver refuses.

**Measured 2026-10-11 in a job**, `demo-devenv-deps` (Stage 6i step 3.8): the folder of `awsds-demo-deps`,
built by `package-uv-job.py` in a space and copied to `shared/jobs/awsds-demo-deps-0.1.0/`, ran in the
house image with no network; `package-job` builds the same 176 files (§T). The container printed:

```
python 3.13.15 at /opt/awsds/venv/bin/python
petl 1.7.29 from /opt/ml/processing/code/petl
msgspec 0.22.0 from /opt/ml/processing/code/msgspec, extension _core.cpython-313-x86_64-linux-gnu.so
pyarrow 24.0.0 from /opt/awsds/venv/lib/python3.13/site-packages/pyarrow, extension lib.cpython-313-x86_64-linux-gnu.so
```

A pure-Python package and an extension module both load from the code input, and the image's own copy
serves what the image holds. The outputs are byte for byte the laptop's, the Parquet table included. The
zero-byte folder markers the space's `shared/` writes into the prefix did not disturb the download.

**The exercise's first job** needs none of this: `awsds-demo-job` has no dependencies, so its input is its
source tree, `shared/awsds-demo-job/`, with `PYTHONPATH` at `/opt/ml/processing/code/src`.

**The workflow deletes the source, not the job**: an isolated container cannot reach S3. The third task
is `S3DeleteObjectsOperator` on the inbox prefix, after the processing task.

**Print counts and paths, never data.** The container's output goes to an account-wide log group (§O).

**What a run costs and how long it takes** (measured 2026-10-11): about 15 minutes and 0.03 USD. The job
spends about 7.5 of its 8 minutes pulling the 6.97 GB house image before the container starts, and the
processing task holds its worker for the whole job. `demo-devenv-deps`'s task held it 791 s for a command
of one second: about 3 minutes of provisioning before `ProcessingStartTime`, 7 of image pull, and 2.5
after `ProcessingEndTime` before the job reads `Completed`, which is what the operator waits on.

---

## §C — Code for a Python or Bash task

**Status in Sandbox: runs since 2026-10-11.** The worker fetches the service's copy of the code (§O)
through the S3 gateway endpoint. Where the endpoint's policy does not admit
`mwaa-serverless-code-files-*-<region>-prod` (any VPC on `vpc-v0.3.1`, Staging and Production today), a
workflow with a code archive fails before its first task with `Execution environment preparation failed
due to an internal server error`, and only a CloudTrail network activity event names the refusal. C6's
recipe built the archive that ran here. Archives of C2's `package-task` ran on a worker on 2026-10-12,
in a Python task and a Bash task outside this lab
([the package's documentation](https://felipenoris.github.io/awsds-workflows/awsds_workflows.html#o-codigo-de-uma-task-python-ou-bash)).

### C1 — What the worker expects

- **One file or one archive.** A single `.py`, a single `.sh`, or a `.zip` holding several files; at
  most 250 MB, unzipped too, and 75 GB of code per account.
- **Everything at the archive's root**: your modules, your packages and every third-party package. The
  worker extracts the archive to `/usr/local/airflow/dags`, which is on `sys.path`, so a module at the
  root imports by its name.
- **Third-party packages built for the worker**: CPython 3.12 on Linux x86_64 today. A package installed
  for your laptop does not import there, nor one built for the house environment of `default-v0.6.0` or
  earlier (Python 3.13).
- **No package the worker already has**: Airflow, the Amazon provider, boto3 and botocore, dag-factory,
  PyYAML, lz4 and the AWS encryption SDK family. In a Python task the pre-installed package wins over the
  archive's copy (measured 2026-10-11: the archive's PyYAML 6.0.1 lost to the worker's 6.0.2). A Bash
  task's `python3` imports the archive's copy first, since its `PYTHONPATH` starts with
  `/usr/local/airflow/dags` (measured outside this lab on 2026-10-12: the archive's `six` 1.16.0
  imported, though Airflow requires a `six` of its own). Write against the worker's boto3 1.43.1.
- **No `__pycache__` or `.pyc`**: bytecode from another platform may not load.
- **No secret**: the archive is copied by the service and stored outside the account.

### C2 — Packaging a uv project with `awsds-workflows package-task`

`awsds-workflows package-task` (§T) turns a project that uv manages into the archive C1 describes. Run
it where uv can reach PyPI: on the laptop, whose browser uploads the archive, or in a space, which
carries uv, and then download the archive from the file browser. The package has not run in a space
yet.

1. **Prepare the project.**
   - It has a `pyproject.toml` and a current `uv.lock`: run `uv lock` in the project after any change.
   - Its `requires-python` admits the worker's Python, 3.12 today.
   - Its own code is pure Python. A project with extension modules cannot be built on a laptop for the
     worker, and `package-task` refuses it.
   - For a Python task, an entry module, a small file beside the package rather than inside it, holds
     the function the task calls:

     ```python
     # tasks.py
     from my_package import pipeline


     def run(bucket: str, inbox: str, outbox: str, **_context):
         return pipeline.process(bucket, inbox, outbox)
     ```

2. **Run it**, naming the project, a Python task's entry module and the archive to write:

   ```bash
   awsds-workflows package-task ~/src/my-project ~/src/my-project/tasks.py ~/Downloads/my-task.zip
   ```

   An archive for Bash tasks only needs no entry module, and `--include`, repeated, puts a script or a
   binary the command calls at the root:

   ```bash
   awsds-workflows package-task ~/src/my-project ~/Downloads/my-task.zip --include ~/src/my-project/run.sh
   ```

   `--python X.Y` and `--platform TAG` change the target; the defaults, 3.12 and `x86_64-manylinux2014`,
   are the worker the guide describes. The service can move the worker to another interpreter without
   notice, and a task log names the one it ran, in its paths (`.../python3.12/site-packages/...`): when
   that path changes, pass the new version. `--omit PACKAGE`, repeated, leaves out more packages. Every
   option goes after the archive.
3. **Read what it printed**: the archive's size and its top level (`raiz`), which lists your package,
   the entry module and the third-party packages, and none of the worker's own (`boto3`, `botocore`,
   `yaml`, Airflow). Its last line (`próximo passo`) is the next step.
4. **Upload the archive** in the workflow's *Settings → Storage → Python/Bash Operator Files*, and save.
5. **Name the callable** in the task (C4): `python_callable: tasks.run`, which the editor shows as *File*
   `tasks` and *Function* `run`. A Bash task runs `python3 -m my_package ...` from
   `/usr/local/airflow/dags`, where the archive is extracted.
6. **A new version of the code** is the same three moves: run `package-task`, upload, save. The workflow
   keeps running the copy taken at its last save.

**When `package-task` refuses**, the messages a reader of this lab meets are below; the package's
documentation lists every one
([*O `.zip` com `package-task`*](https://felipenoris.github.io/awsds-workflows/awsds_workflows.html#o-zip-com-package-task)).

| It says | Meaning | What to do |
|---|---|---|
| `The lockfile at uv.lock needs to be updated` | `pyproject.toml` changed after the lock | `uv lock` in the project |
| `no wheels with a matching platform tag` | a dependency publishes no wheel for the target | it cannot travel in the archive: another version or another package |
| `não é Python puro` | the project has extension modules | build its wheel on the target platform, in a pipeline (Stage 8) |
| `acima do limite de 250000000 bytes do worker` | the archive is too big | `--omit` more, or drop dependencies |
| `já está na raiz do .zip` | the entry module or an `--include` file has the name of a package or of another file at the root | rename the file |
| `unrecognized arguments` | an option sits between the paths | put it after the archive |
| `No interpreter found for Python <version>` | uv finds no interpreter the project accepts and may not download one, as in a space | `UV_PYTHON` naming one: in a house-image space `/opt/conda/bin/python` is 3.12, and `$AWSDS_PYTHON_ENV/bin/python` is 3.12 from `default-v0.7.0` and 3.13 up to `default-v0.6.0` |

**What it does**, each step one rule of C1:

1. exports the project's locked closure, pruning every package the worker pre-installs together with
   the dependencies only they need;
2. installs the worker's wheels for that closure with the lock's hashes, refusing a source distribution,
   which would build for the laptop;
3. adds the project's own wheel, refused unless it is pure Python;
4. removes uv's `.lock`, console scripts and bytecode, then copies the entry module and each `--include`
   file to the root with its mode;
5. writes the archive with Python, since the house image carries `unzip` but no `zip`, and refuses one
   over 250 MB unzipped.

**Measured 2026-10-11** with `package-uv.sh`, on a throwaway uv project depending on `petl`, `requests`,
`boto3` and `pyyaml`: about 0.9 MB, holding the project, `tasks.py`, `petl` and `requests` with
`certifi`, `charset_normalizer`, `idna` and `urllib3`; no `boto3`, `botocore`, `s3transfer`, `jmespath`
or `yaml`; `charset_normalizer`'s compiled modules tagged `cp312-cp312-manylinux2014_x86_64`, and
`cpython-313` with `--python 3.13`. `package-task` builds the same entries (§T).

**Keep the entry module thin.** The editor shows `python_callable` as a *File* and a *Function*, so a
root module that imports from the package is what it can display. A dotted path into the package,
`pkg.module.function`, is unmeasured here.

### C3 — What the archive holds

```
my-task.zip                  the CONTENTS of the staging folder, no folder of its own
├── tasks.py                 the entry module: python_callable: tasks.run
├── run.sh                   a file of --include, with its mode
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
the Airflow context too if it accepts `**kwargs`. A Bash task names `bash_command`. The guide says a
script from the archive runs with `/usr/local/airflow/dags` as its working directory; every form
measured ran in the task's temporary folder instead, an inline command here on 2026-10-11 and a script
called by its full path outside this lab on 2026-10-12. Measured 2026-10-11:

- **A command that is a script's name** (`bash_command: reach_pypi.sh`) is rendered as a Jinja template
  from the archive into a temporary file, which the operator runs with `bash`; the script carries no
  double brace.
- **An inline `bash_command` needs no archive** and runs in a temporary folder (`/var/tmp/airflowtmp…`);
  the service renders it through Jinja too.
- **A Bash task's `PYTHONPATH` carries `/usr/local/airflow/dags`**, so `python3 -m <package>` imports the
  archive's package from any folder.

Outside this lab, on 2026-10-12, `python3 -m <package>` ran without a `cd`, and a script the archive
stored executable ran by its path, `/usr/local/airflow/dags/<script>.sh`: the worker keeps each file's
mode when it extracts the archive.

The templates are `examples/sandbox-orchestration/operators/python/demo-python-operator.yaml`,
`operators/bash/demo-bash-operator.yaml` and, with no archive, `operators/bash/demo-bash-operator.probe.yaml`.

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
  save time in the saver's session. The CI/CD CLI 1.0.9 takes this path: `workflow.create` copies the
  archive to `shared/operatorFiles/<workflow>-<ms>.zip`, one object per deploy that nothing prunes, and
  names it as `Code` (Stage 18 4.2, 4.3 and 4.5).

**The portal guide's dependency recipe omits the platform flags** (`pip install --target ./package
your-dependency`): run on a Mac, it installs the Mac's wheels of any compiled package. Use C2, or C6
by hand.

**A new version of the code needs a new save.** The workflow runs the copy taken at its last save, so
replacing the S3 object changes nothing until the workflow is saved or imported again. Every save takes a
new copy: a description-only edit moved `CodeSnapshottedAt` with the code unchanged, and the portal
uploads the file again at every save, a refused one included (measured 2026-10-11).

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
| What did a save in the portal change in the definition? | `SO-3` saves every version; `awsds-workflows render --placeholders` on it, then `compare` with the file it was imported from (§A) |
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

**The run's state lags its tasks.** `get-workflow-run` read `QUEUED` until 23:06:16Z while the sensor had
finished at 23:05:23Z and the job was being created (2026-10-11). Read progress from the task instances,
never from `RunState`.

---

## §X — Cleaning up

- **Delete a workflow** from the *Workflows* page. Its log group stays, with no retention.
- **Empty the inboxes** so the next run starts from a known state; the outboxes are the results.
- **Processing jobs cannot be deleted**: they stay listed, which is why `SO-5` fails only the newest.
- **A processing job's lineage stays too**: SageMaker creates a trial component per job, with artifacts
  and associations, removed with `delete-association`, `delete-trial-component` and `delete-artifact`
  (read in Staging, Stage 18 4.4 and 8.1). A project's deletion leaves these, the runs' log groups and the
  CLI's `operatorFiles/` copies ([`docs/SMUS.md`](../../SMUS.md), "What a teardown leaves").
- **The code archives** under `dev/operatorFiles/` stay with every version, since the bucket is versioned.
- **The code folders** under `shared/jobs/` stay, one per version (§J1 step 5); delete an old one only
  when no definition names it.
