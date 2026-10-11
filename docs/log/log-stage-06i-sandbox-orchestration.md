# Log — Stage 6i — Sandbox orchestration

*The stage file is [`docs/plan/stages/stage-06i-sandbox-orchestration.md`](../plan/stages/stage-06i-sandbox-orchestration.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an AWS write; `[user]` is something done by hand, with any measurement pasted verbatim.*

*Identifiers are redacted as [`INDEX.md`](INDEX.md) requires: an account id becomes the account's name
in angle brackets, an e-mail address inside an ARN becomes that user's role. Everything else in a pasted
output stays verbatim. All times UTC.*

---

## 2026-10-10 — pass 0: the readings, the CLI, the instrument and the files

*Written by Claude in the sitting that ran it, at the user's instruction to start pass 0. Every reading is
Claude's own, from `awsds-infra-sandbox-1` (account `<Sandbox Account 1>`, permission set
`InfrastructureAccess`). Nothing was written to AWS.*

### [user] 0.2 — the CLI

**[user]** "Atualizei o aws cli para v2.37.12."

**[Claude]** `aws --version` reads `aws-cli/2.37.12`, and `aws mwaa-serverless create-workflow help`
carries `--code`. `get-workflow` on the two earlier workflows returns `Code` and `CodeSnapshottedAt` as
null: neither has a Python or Bash task.

### [Claude] 0.1 — the identifiers

| What | Value |
|---|---|
| project | `avhvbqn37ty7m8`, domain `dzd-d8yrvx1ko7im6o`, the only project role in the account |
| project key | `alias/awsds-sandbox-project`, the role's `KmsKeyId` tag, `Enabled`, `CUSTOMER` |
| project storage | `awsds-sandbox-smus-projects`, prefixes `dev/` and `shared/` under the project; no `shared/orchestration-demo/` yet |
| network the portal puts on a workflow | `awsds-sandbox-private-usw2-az1` and `-usw2-az2`, security group `datazone-avhvbqn37ty7m8-dev` |
| house image | `awsds-sandbox-dev-env` version 5, `sha256:8ec04e357792e4cb1beaace2c1dcfde0f60ba6074195cc31091452e11db89dd6`, in `<Production Account>`'s `awsds-prod-ecr-dev-env` |

`./aws/devenv.py` exited 2 on `DE-2` alone: the state of `sandbox/egress` holds no outputs because the
slice is down, the expected reading between sessions.

### [Claude] Readings the plan did not have

- **The portal stores the visual layout as the definition's first line**, a YAML comment carrying each
  task's canvas position: `# {"S3-task":{"x":430,"y":230}}`. The task's operator is the full class path,
  `airflow.providers.amazon.aws.operators.s3.S3CopyObjectOperator`.
- **A task instance id is `ex_<uuid>_<task id>_<attempt>`**, and a retried task lists every attempt with
  its own status (`UP_FOR_RETRY`, then `FAILED`), in an order that is not the attempts' order.
- **`MyWorkflow` holds five versions** (2026-08-27 to 2026-09-10) and `simple-s3-copy` one, so every
  definition edit of 6d's sittings is still readable with `get-workflow --workflow-version`.
- **The workflows' log groups are encrypted with the project key** and have no retention.

### [Claude] 0.3 — `./aws/sandbox-orchestration.py`, the before

Exit 0. `SO-1` notes the three contract workflows absent, `SO-5` no processing job, `SO-6`
`/aws/sagemaker/ProcessingJobs` absent, `SO-7` an empty `orchestration-demo/` and no package uploaded,
`SO-8` no `CreateProcessingJob` in the trail window.

A self-test pointed the contract at the two earlier workflows, in memory, to exercise `SO-2`..`SO-4`
before any contract workflow exists:

- `SO-1` attributed both creations to the project role from CloudTrail;
- `SO-2` passed both: the project role, both private subnets in two AZs, no default route, the project's
  security group and key;
- `SO-3` saved all six versions, and the sanitized copies carried no account id to replace.

It also found one defect, fixed before the commit: `SO-4` read a retried task's state from the last
attempt the listing returned, and reported `UP_FOR_RETRY` for a run whose last attempt `FAILED`. The
self-test's outputs were deleted.

### [Claude] 0.4 — the files

`examples/sandbox-orchestration/` holds the following, and the repository layout in `README.md` names it:

- the project `awsds-demo-job`, whose 6 tests pass;
- the two paste-ready processing configurations;
- the operator files and their build script;
- the sample;
- `render.py`.

`render.py --values` read the same project, security group and subnets as 0.1, which the portal also
uses, and the probe configuration rendered to valid JSON.

## 2026-10-10 — pass 1: the project in `shared/`

*The copy is the user's; every reading is Claude's own, from `awsds-infra-sandbox-1` (account
`<Sandbox Account 1>`, permission set `InfrastructureAccess`) and `awsds-infra-prod` (account
`<Production Account>`, the same permission set) after the user signed in again. Nothing was written
to AWS by Claude.*

### [user] The session raised, and the project copied

**[user]** "Subi o ambiente. Clonei o repositório no alvo. Copiei o awsds-demo-job na pasta shared:"

```
agemaker-user@default:~/shared/awsds-demo-job$ ls
pyproject.toml  src  tests
```

### [Claude] 1.2 — the objects read back

- **The hub is up:** `awsds-prod-vpn` and `awsds-prod-proxy` are `running`, launched 23:54:49Z and
  23:54:52Z. Sandbox's VPC holds 19 interface endpoints `available`, `sagemaker.api`, `logs`, `sts`, `kms`,
  `ecr.api` and `ecr.dkr` among them.
- **The copy reached S3 at 00:32:12-13Z**, under `shared/awsds-demo-job/`. Its six files have the
  repository's byte counts, file by file: 759, 288, 1675, 2394, 1569 and 3700.
- **The objects are encrypted with the project key.** `head-object` reads `aws:kms` with the project key
  (`a81b1ef3-…`) and `BucketKeyEnabled: true`, and each object carries a version id.
- **The clone itself is outside `shared/`**, since no repository folder appears among the prefixes.
- **A stray object** remains from the path the plan named first:
  `orchestration-demo/devenv/code/pyproject.toml` (759 bytes). No contract reads it.
- **`./aws/sandbox-orchestration.py` exits 0.** `SO-7` passes on the project's code (6 objects, the entry
  point present), on the three variants' empty `inbox/` and on the encryption. The `SO-1`, `SO-5`, `SO-6`
  and `SO-8` notes stand until pass 2.

The path the user chose replaced the plan's `orchestration-demo/devenv/code/`. The job's code input,
`SO-7` and the stage's contract were moved to `shared/awsds-demo-job/` in the same sitting.

## 2026-10-10 — pass 2: the first save refused, and why

*The portal session is the user's; every reading is Claude's own, from `awsds-infra-sandbox-1`.*

### [user] The save

**[user]** "Ao salvar o workflow, ele pede Storage -> Definition S3:
`s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/workflows`, CloudWatch log group -
optional `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-avhvbqn37ty7m8/demo-devenv-job` (estes são os valores que
aprecem preenchidos por padrão). E ao salvar, falha com a mensagem: ValidationException: Code not found in
specified S3 location"

### [Claude] What the portal sent, from CloudTrail

The two attempts were `CreateWorkflow` calls at 00:50:47Z and 00:51:27Z, both refused with
`ValidationException` and `Code not found in specified S3 location`.

- **The caller** is the project role, with the portal's session name `<Identity Center user id>@<environment id>`.
- **Every request carries `code.s3Location`**, pointing at `dev/operatorFiles/<workflow name>.zip`. The
  first named `MyWorkflow-1791679674427.zip`, the editor's default name before the rename. The second named
  `demo-devenv-job.zip`. No object exists under `dev/operatorFiles/`, and the prefix does not exist at all.
- **The portal changed between the two dates.** `simple-s3-copy`'s `CreateWorkflow` at 2026-09-10 03:55:15Z
  carried `code: null` and succeeded. Today the portal sends a code location even for a workflow with no
  Python or Bash task, and uploads nothing to it when no operator file was added in *Settings → Storage*.
- **Both requests carry the state the portal injects:**
  - seven `environmentVariables`: `DataZoneDomainRegion`, `DataZoneEnvironmentId`, `ProjectS3Path`,
    `DataZoneProjectId`, `DataZoneDomainId`, `DataZoneStage` (`prod`) and `DataZoneEndpoint`;
  - the tag `AmazonDataZoneProject`;
  - `triggerMode: manual_only`;
  - the project key;
  - the project's two private subnets and security group.
  September's request carried the same seven variables.

### [Claude] What the portal wrote and removed, from the bucket's versions

At each attempt the portal wrote `dev/workflows/demo-devenv-job.yaml` (374 bytes), and a delete marker
followed one second after the refusal. The definition it generated holds one task, `wait_for_file`, as
`airflow.providers.amazon.aws.sensors.s3.S3KeySensor`, with `bucket_key` and `wildcard_match: true`. The
first save came before the other two tasks existed.

### [Claude] The way through

Upload one operator file in the workflow's *Settings → Storage*, so that the portal writes the zip its
request names: `examples/sandbox-orchestration/devenv-job/no_operator_code.py`, a docstring and nothing
else.

## 2026-10-10 — pass 2: the save goes through, twice, and the processing form

*The portal session is the user's; every reading is Claude's own, from `awsds-infra-sandbox-1`.*

### [user] The placeholder, and the form

**[user]** "importei um script hello.py com print('hello') na seção Storage e com isso a interface permitiu
eu salvar o workflow."

**[user]** "No SageMaker Processing Operator não aparece campo config onde posso colar o JSON. Em vez disso
aparece um formulário com vários campos: Task name, Processing job name, Data (input), Data (output),
Contianer image URI, Container entrypoint, Container arguments, instance type, instance count, volume,
execution role arn. Como alternativa, existe a opção "Actions -> Import definition file" para o Workflow
como um todo."

### [Claude] What the save made

- **Two workflows, one name.** `CreateWorkflow` succeeded twice from one save, at 01:00:57Z and 01:00:59Z,
  and the account now holds `demo-devenv-job-W6HvorwGu9` and `demo-devenv-job-1N0Y70z8Jr`. The service
  appends a suffix to the ARN, so a name is not unique. Each workflow is `READY` with one version.
- **One file is uploaded as it is.** Each workflow's `Code` is `dev/operatorFiles/hello.py`, not a zip,
  each with its own S3 version and `CodeSnapshottedAt` (01:00:57.7Z and 01:00:59.4Z).
- **Both definitions hold one task**, `wait_for_file`. The form could not express the processing job, so
  it was never added.
- **`SO-1` now fails on a duplicated name.** `./aws/sandbox-orchestration.py` reads the newest of the two
  in detail; `SO-2` and `SO-3` pass on it.

### [Claude] The processing job, as a definition

The form has no field for `NetworkConfig`, for either KMS key or for the tags, so a job it builds meets the
boundary's four denies and the project-tag condition. This is decision due 14's notebook operator again,
but this operator can be configured past it: the definition carries the whole `config`.

`examples/sandbox-orchestration/devenv-job/demo-devenv-job.probe.yaml` and `.project.yaml` replace the two
JSON configurations. Both rendered with `render.py` and parsed with PyYAML:

- three tasks in a chain, through `dependencies`;
- `EnableNetworkIsolation` and `EnableInterContainerTrafficEncryption` as booleans;
- the probe's `/bin/bash` command, and the project's `/opt/awsds/venv/bin/python` command with its
  `PYTHONPATH`.

### [user] The import, and the editor's validation

**[user]** "Ele conseguiu importar o yaml. Mas ao validar, mostrou a seguinte mensagem no SageMaker Processing
Operator: ContainerArguments: Container argument is required."

**[Claude]** The import took the whole definition. The editor's validation, not the API, demands
`ContainerArguments`, because `CreateProcessingJob` takes an `AppSpecification` without them. Both
definitions now split the command into a program and its arguments:

- the probe: `["/bin/bash", "-c"]` and the script;
- the project: `[".../venv/bin/python", "-m", "awsds_demo_job"]` and `--input`/`--output`.

Both rendered and parsed again.

### [user] Every workflow deleted, one imported into an empty workflow

**[user]** "Apaguei todos os workflows existentes. Criei um novo vazio, importei o yaml, e salvou com sucesso
sem precisar importar um script python vazio em storage."

### [Claude] What CloudTrail and the workflow read

All of it was called by the project role in the portal's session.

- **The deletions**, from 01:17:51Z to 01:19:07Z: `simple-s3-copy` and `MyWorkflow`, 6d step 4's two
  workflows, then both `demo-devenv-job` twins. A deleted workflow takes its run history with it
  (Lesson 4), and **its log group stays**: `MyWorkflow`'s holds 21,448 bytes and `simple-s3-copy`'s 1,743.
  6d's run evidence now lives in those groups and in 6d's log.
- **Two refusals on the way.** `UpdateWorkflow` was refused with "Workflow validation failed: The DAG
  definition is invalid since it does not contain any tasks" (01:18:31Z), and `CreateWorkflow` with
  "Workflow with given name already exists" (01:18:47Z). **The name is checked**, so the earlier twins were
  two creates that raced past the check 2 s apart.
- **The workflow, `demo-devenv-job-Pjx5WDCyKO`**, created 01:19:39Z, is `READY` with `Code` null: saved with
  no operator file, so the code location the portal sent on the earlier saves is not sent on every path.
- **The import kept every field the form cannot show:** `NetworkConfig` (isolation, inter-container
  encryption, both subnets, the project's security group), both KMS keys, the `AmazonDataZoneProject` tag,
  `StoppingCondition` and `ContainerArguments`. The portal re-serialized the file: folded scalars split
  `{{ ts_nodash }}` across a line, which a YAML reader folds back to one space, and it added
  `is_paused_upon_creation: false`. It kept the layout comment as written.
- **`./aws/sandbox-orchestration.py`:** `SO-1`, `SO-2` and `SO-3` pass on it, and `SO-6` notes its log
  group with no retention.

### [user] The first run fails

**[user]** "O job falhou: There was an error executing run Pzs3TlvfHhqOK6M: Workflow execution failed, please
check the task execution logs for more details"

### [Claude] Why: the operator's existence check meets the project role's tag condition

`get-workflow-run` reads run `Pzs3TlvfHhqOK6M` as `ON_DEMAND` and `FAILED`, 84 s from 01:27:38Z. Its
three tasks:

| Task | Status | Seconds |
|---|---|---|
| `wait_for_file` | `SUCCESS` | 5 |
| `run_project` | `FAILED` | 8 |
| `remove_source` | `UPSTREAM_FAILED` | 0 |

The task log of `run_project`:

```
An error occurred (AccessDeniedException) when calling the DescribeProcessingJob operation: User:
arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/AmazonMWAAServerless
is not authorized to perform: sagemaker:DescribeProcessingJob on resource:
arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:processing-job/demo-devenv-20261011T000000 because no
identity-based policy allows the sagemaker:DescribeProcessingJob action
```

- **The refusal precedes the job.** `SageMakerProcessingOperator.execute()` in Amazon provider 9.32.0, read at
  the provider's tag, always calls `_get_unique_job_name`. It describes the proposed name, counts only a
  `ValidationException` as "absent" and re-raises anything else. Neither parameter turns it off:
  `action_if_job_exists` takes `timestamp` or `fail`, and both check.
- **No `CreateProcessingJob` was called.**
- **The project role may describe only what carries its tag.** `SageMakerDescribeUpdateDeletePermissions`
  in `SageMakerStudioProjectRoleMachineLearningPolicy` grants `DescribeProcessingJob` only when
  `aws:ResourceTag/AmazonDataZoneProject` equals the principal's tag, and a name not yet taken carries none.
- **The editor's own SageMaker Processing task would fail the same way** under the default managed policy,
  before the boundary's job denies were ever reached.
- **`{{ ts_nodash }}` rendered as the day's midnight** (`20261011T000000`): a manual run's logical date is
  the run id's `scheduled__2026-10-11T00:00:00+00:00`. Every run of a day would therefore propose one job
  name and share one `outbox/` folder.
- The sample stayed in `inbox/`, because `remove_source` never ran.

### [Claude⚡] Decision 6 applied: `sandbox/workflows/`

*Authorized in chat by the user ("sim"), after the plan was shown. The two peer sessions were told before
the apply. Run as the infrastructure user, `InfrastructureAccess` on `awsds-infra-sandbox-1`
(`<Sandbox Account 1>`), after the user signed in again: the cached SSO token had expired at 01:35:32Z,
and Terraform refreshes the token where the CLI reuses cached role credentials.*

- **The plan:** `2 to add, 0 to change, 0 to destroy`, with the boundary precondition passing on the
  project role.
- **The apply, from the saved plan:** `awsds-sandbox-workflows` created and attached to
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, `Apply complete! Resources: 2 added, 0 changed, 0
  destroyed.`
- **The re-plan:** `No changes. Your infrastructure matches the configuration.`, exit 0.

The commit that carried the slice first met checkov's `CKV_AWS_382`, which fails on `main` as well. It
flags two probe security groups whose egress names VPC ranges only: `sandbox/probes`' peering probe and
`staging/probes`' INT-09 probe. Each now carries the inline skip its siblings carry. The hook also scans
the module clones that `terraform init` leaves under `.terraform/modules/`, which hold older copies of
those files, so the local clones were removed before the commit.

### [user] The second run, refused before its first task

**[user]** "Falhou: There was an error executing run TLnY6WiydHqF6q6: User template error: DAG template
rendering failed: 'dag_run' is undefined. Check your template for invalid variable references."

### [Claude] The service renders the definition's templates when it creates a run

- **No task ran.** `get-workflow-run` reads `FAILED` with `StartedOn` null, `Duration` null and no task
  instance. The run died at creation, so it cost nothing.
- **The supported context is short.** The guide's *Template Variables, Filters and Macros* page names
  `macros`, `ti`/`task_instance`, `params`, `ds`, `ds_nodash`, `ts` and `ts_nodash`, plus the macros
  `datetime`, `timedelta`, `dateutil`, `time`, `uuid`, `random`, `ds_add` and `ds_format`. `dag_run`,
  `run_id` and `logical_date` are absent, and an undefined name refuses the run.
- **The stamp moved to a macro.** The job name and the outbox now take
  `{{ macros.datetime.utcnow().strftime('%Y%m%dT%H%M%S') }}`, one value per run. Both definitions rendered
  through a sandboxed, strict Jinja environment to `demo-devenv-<UTC stamp>`.

### [user] The third run, refused at creation too

**[user]** "Falhou: There was an error executing run pP721KRCHwBfio7: User template error: DAG template
rendering failed: access to attribute 'strftime' of 'datetime' object is unsafe.. Check your template for
invalid variable references."

### [Claude] The service's sandbox is stricter than Jinja's default

Jinja's standard sandbox allows `strftime` on a `datetime`. The service's refuses a method called on an
object a macro returned, while it let `macros.datetime.utcnow()`, an attribute of the class, through. The
stamp now calls only the `time` module's own functions:
`{{ macros.time.strftime('%Y%m%dT%H%M%S', macros.time.gmtime()) }}`. It rendered through an immutable,
strict sandbox to `demo-devenv-<UTC stamp>`. If the service refuses this one too, the fallback is the epoch
seconds, `{{ macros.time.time() | int }}`, a built-in filter on a module function.

### [user] The fourth run: the template passes and the create is refused

**[user]** "Falhou: There was an error executing run FVyFira1LY3BuGi: Workflow execution failed, please
check the task execution logs for more details"

### [Claude] The existence check passed, and the create met `AddTags`

- **The tasks:** `wait_for_file` `SUCCESS` in 5 s, `run_project` `FAILED` in 12 s, `remove_source`
  `UPSTREAM_FAILED`. No processing job exists.
- **Decision 6's grant works for the check.** `run_project` reached `CreateProcessingJob`, so
  `DescribeProcessingJob` on the free name was allowed. The task log:

  ```
  ClientError: An error occurred (AccessDeniedException) when calling the CreateProcessingJob operation:
  User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/AmazonMWAAServerless
  is not authorized to perform: sagemaker:AddTags on resource:
  arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:processing-job/demo-devenv-20261011T023457 because no
  identity-based policy allows the sagemaker:AddTags action
  ```

- **Verification iii is answered: no.** A create that carries tags is also authorized as
  `sagemaker:AddTags`. `SageMakerTagPermissions` excludes every `AmazonDataZone*` key, while
  `SageMakerCreatePermissions` demands the job carry `AmazonDataZoneProject`. With the blueprint's policies
  alone, a project role cannot create a processing job.
- **The job name stamp worked:** `demo-devenv-20261011T023457`, the run's own time.
- **Every import since 02:07Z went through `DeleteWorkflow` and then `CreateWorkflow`**, about 30 s apart.
  The ARN suffix is new each time (`It0FUChSnC`, `ODN4LiixCM`, `j39HQ6kTxG`), and the run and version
  history restart with it. The log group is named after the workflow, so it keeps every run's logs.

### [Claude] The second statement, simulated

`simulate-principal-policy` on the project role read `explicitDeny` with `AllowedByOrganizations: false`
for both calls. The simulator evaluates the SCPs without the request's network context, and the real call
had passed that layer, so it cannot answer this question. `simulate-custom-policy` evaluated the slice's
policy alone. For `AddTags` with `AmazonDataZoneProject` equal to the caller's project tag:

| Case | Decision |
|---|---|
| a new job | `allowed` |
| a job already carrying the caller's project | `allowed` |
| a job carrying another project's tag | `implicitDeny` |
| a request tag with another project's value | `implicitDeny` |
| a second tag key in the request | `implicitDeny` |

`DescribeProcessingJob` read `allowed` on an untagged name and `implicitDeny` on another project's job.

### [Claude⚡] The second statement applied

*Authorized in chat by the user ("pode aplicar"), after the plan read `0 to add, 1 to change, 0 to
destroy`. The two peer sessions were told before the apply. Run as the infrastructure user,
`InfrastructureAccess` on `awsds-infra-sandbox-1` (`<Sandbox Account 1>`), after the user signed in
again: the token was refused with `UnauthorizedException: Session token not found or invalid` at
02:40Z, though its cache file read `expiresAt 03:03:34Z`.*

- **The plan:** `aws_iam_policy.workflows` updated in place, the statement
  `TagAProcessingJobWithTheCallersProject` added.
- **The apply, from the saved plan:** `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.`
- **The re-plan:** `No changes`, exit 0.
- **The policy** reads `DefaultVersionId` `v2` with one attachment.
- **The description stays the first statement's.** Changing an `aws_iam_policy` description forces a new
  policy, so the code comments carry the second statement.

## 2026-10-11 — pass 2: the first processing job

*The run is the user's, in the portal. The readings are Claude's, from `awsds-infra-sandbox-1`
(`<Sandbox Account 1>`, `InfrastructureAccess`) and, for the image pull, `awsds-infra-prod` (Production,
`InfrastructureAccess`). Nothing was written to AWS.*

### [user] The fifth run

**[user]** "Falhou:" and then "There was an error executing run 8A08SDQqOTkjDCQ: Workflow execution
failed, please check the task execution logs for more details"

### [Claude] The boundary admits the job, and the container cannot write its output

- **The tasks:** `wait_for_file` `SUCCESS` in 3 s, `run_project` `FAILED` in 762 s, `remove_source`
  `UPSTREAM_FAILED`. The sample stays in `inbox/`.
- **The job, `demo-devenv-20261011T024724`**, was created at 02:47:26Z with the four settings and the tag:
  isolation `True`, inter-container encryption `True`, the project key on the volume and the output, and
  `AmazonDataZoneProject` `avhvbqn37ty7m8`. **Verification v is answered: yes.** It ended `Failed`,
  `AlgorithmError: , exit code: 1`.
- **The container's output**, stream `demo-devenv-20261011T024724/algo-1-1791687033` of
  `/aws/sagemaker/ProcessingJobs`:

  ```
  uid=1000(sagemaker-user) gid=100(users) groups=100(users)
  total 12
  drwxr-xr-x. 4 0 0 4096 Oct 11 02:51 code
  drwxr-xr-x. 2 0 0 4096 Oct 11 02:51 inbox
  drwxr-xr-x. 2 0 0 4096 Oct 11 02:57 outbox
  touch: cannot touch '/opt/ml/processing/outbox/probe': Permission denied
  ```

  **Verification ii is answered: no.** The image runs as `sagemaker-user`, the platform creates every mount
  as root with mode 755, and the exit code is `touch`'s.
- **The timeline:** created 02:47:26Z, `ProcessingStartTime` 02:50:34Z, the container's output at
  02:58:00Z, `ProcessingEndTime` 02:58:20Z. The operator polls every 30 s, read `Failed` at 02:59:59Z, and
  the task ended at 03:00:04Z. 7.4 of the job's 7.75 minutes passed before the container started: the pull
  of `default-v0.5.0`, 6,969,138,672 bytes compressed in Production's registry, and the inputs' staging.
- **The cost:** about 0.027 USD, 14 task-minutes at 0.088/h and 465 s of `ml.t3.medium` at 0.050/h.

### [Claude] The pull, the door, the existence check and the key

- **The pull (verification iv): yes, as the project role.** Production's CloudTrail holds three
  `BatchGetImage` on `awsds-prod-ecr-dev-env` by digest `sha256:8ec04e35…9dd6`. Each reads
  `userIdentity.type` `AWSAccount`, the account Sandbox and the principal `AROA47P7U4BDOUDA4B63F:SageMaker`,
  which is the project role's id with the session name `SageMaker`.

  | Time | Source | Reading |
  |---|---|---|
  | 02:47:27Z | `35.165.252.115` | the Java SDK, at the create |
  | 02:47:28Z | `184.32.187.109` | the Java SDK in Lambda, at the create |
  | 02:50:34Z | `ecr.amazonaws.com` | invoked by `ecr.amazonaws.com` at the job's start: the pull |

  None carries a `vpcEndpointId`. The platform pulls the image outside Sandbox's network, so the isolated
  job needs no ECR endpoint.
- **The door (verification vi):** `CreateProcessingJob` and all 26 `DescribeProcessingJob` came through
  `vpce-0a72d9d2674245821`, Sandbox's `sagemaker.api` interface endpoint, from `10.20.95.168` in
  `awsds-sandbox-private-usw2-az2`, as the project role with session name `AmazonMWAAServerless`. No
  network interface holds that address after the run.
- **The existence check (verification xiv, first half): yes.** The first `DescribeProcessingJob`, at
  02:47:26Z, got `ValidationException` "Could not find requested job with name:
  demo-devenv-20261011T024724", and the create followed in the same second. The other 25 were the
  operator's polls on the tagged job.
- **The volume key worked through the operator's session.** At 02:47:29Z the project role, session
  `AmazonMWAAServerless`, invoked by `sagemaker.amazonaws.com`, created a grant on the project key for
  `sagemaker.us-west-2.amazonaws.com` (`Encrypt`, `Decrypt`, `ReEncryptFrom`, `ReEncryptTo`,
  `GenerateDataKeyWithoutPlaintext`, `CreateGrant`). At 02:47:34Z `ec2-frontend-api.amazonaws.com` created a
  `Decrypt` grant from it.
- **One `CreateGrant` was refused, and the job went on.** At 02:47:29Z the project role, session
  `SageMaker`, called `kms:CreateGrant` on the project key directly, from `44.248.190.216` (the Java SDK in
  Lambda): "User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker
  is not authorized to perform: kms:CreateGrant on resource:
  arn:aws:kms:us-west-2:<Sandbox Account 1>:key/a81b1ef3-716f-4105-bb42-14184a6e2174 because no
  identity-based policy allows the kms:CreateGrant action". `SageMakerKmsPermissions` (v44) allows
  `CreateGrant` only with `kms:ViaService` `sagemaker.*.amazonaws.com`, which a direct call does not carry.
  Whether the refusal reaches the output's encryption is verification xiii, in pass 3.

### [Claude] The definition, read back and committed

`./aws/sandbox-orchestration.py` saved version `f945560d2f98f67e2b8773e68a0399f4`. `render.py` gained
`--placeholders`, the reverse of a render, and the copy is
`examples/sandbox-orchestration/definitions/demo-devenv-job.probe.yaml`; rendering it again gives the saved
file byte for byte. Parsed against the imported template, the portal kept every field and added one,
`is_paused_upon_creation: false`. The rest is formatting: keys reordered and long strings folded.

### [Claude] 2.5 — the `sudo` probe

The probe's command now reads `id; ls -ln /opt/ml/processing; sudo -n chown "$(id -u)"
/opt/ml/processing/outbox && echo CHOWN-OK; ls -ln /opt/ml/processing; touch /opt/ml/processing/outbox/probe
&& echo WRITE-OK`. `sudo` works in a space (2026-09-08); whether it works in a processing container is the
question. `-n` makes it fail at once where it would ask for a password.

### [user] The sixth run

**[user]** "Rodou com sucesso"

### [Claude] 2.5 measured: `sudo` works inside a processing job

- **The run, `oGsqYXMR64rsD8D`:** `wait_for_file` `SUCCESS` in 5 s, `run_project` `SUCCESS` in 759 s,
  `remove_source` `SUCCESS` in 5 s.
- **The job, `demo-devenv-20261011T033717`**, created at 03:37:18Z through the same endpoint from
  `10.20.80.32` (the az2 private subnet again), ran from 03:40:11Z to 03:47:46Z, 455 s, and ended
  `Completed`. Its stream in `/aws/sagemaker/ProcessingJobs`:

  ```
  uid=1000(sagemaker-user) gid=100(users) groups=100(users)
  total 12
  drwxr-xr-x. 4 0 0 4096 Oct 11 03:40 code
  drwxr-xr-x. 2 0 0 4096 Oct 11 03:40 inbox
  drwxr-xr-x. 2 0 0 4096 Oct 11 03:47 outbox
  CHOWN-OK
  total 12
  drwxr-xr-x. 4    0 0 4096 Oct 11 03:40 code
  drwxr-xr-x. 2    0 0 4096 Oct 11 03:40 inbox
  drwxr-xr-x. 2 1000 0 4096 Oct 11 03:47 outbox
  WRITE-OK
  ```

- **The output:** `outbox/20261011T033717/probe`, 0 bytes, written at 03:47:42Z, `aws:kms` with the project
  key and `BucketKeyEnabled`. The upload's `GenerateDataKey` (03:47:41Z) was the project role in the session
  `SageMaker`, through S3. The direct `CreateGrant` was refused again at the create (03:37:25Z), and the
  output's encryption did not need it: verification xiii for the probe's object.
- **`remove_source`** put delete markers on `inbox/sample.csv` and `inbox/` at 03:50:36Z. The bucket is
  versioned, so the sample's version stays.
- **The job session's calls** (CloudTrail user name `SageMaker`): at the create, a dry-run
  `CreateNetworkInterface` and a `BatchGetImage`; the job's network interface at 03:39:56Z
  (`CreateNetworkInterface`, `CreateNetworkInterfacePermission`); `GetAuthorizationToken` at 03:40:10Z and
  42 `GetDownloadUrlForLayer` by 03:41:09Z; three `Decrypt` through S3 at 03:40:53Z, the inputs;
  `CreateLogStream` at 03:47:34Z; `Decrypt` and `GenerateDataKey` through S3 at 03:47:12Z and 03:47:41Z,
  the output. One more `BatchGetImage`, at 03:40:10Z, was refused with `InvalidParameterException` on its
  `repositoryName`, beside the one that served the pull.
- **The pull's six minutes:** the last layer URL at 03:41:09Z and the container's output at 03:47:27Z, the
  download and extraction of the 6.97 GB image on `ml.t3.medium`.
- **The cost:** about 0.028 USD, 15 task-minutes (0.022) and 455 s of `ml.t3.medium` (0.0063).

### [Claude] Pass 2 closed: the instrument and the definition

- **`SO-5` failed on the first job forever.** A processing job cannot be deleted, so the failed probe stays
  listed. `SO-5` now fails a setting outside the boundary on any job and a failed outcome on the newest job
  only; an earlier failure is a note. The instrument exits 0.
- **The definition** in `definitions/demo-devenv-job.probe.yaml` is now version
  `9254485323655d399d7f36267799fc04`, the one that ran. It renders back to the saved file byte for byte, and
  the portal again added only `is_paused_upon_creation: false`.

### [Claude] Pass 3 prepared

`devenv-job/demo-devenv-job.project.yaml` now runs `/bin/bash -c` with one argument: `sudo -n chown "$(id -u)"
/opt/ml/processing/outbox && exec /opt/awsds/venv/bin/python -m awsds_demo_job --input /opt/ml/processing/inbox
--output /opt/ml/processing/outbox`. `exec` hands the job the interpreter's exit code. `PYTHONPATH` stays
`/opt/ml/processing/code/src`. It renders and parses.

## 2026-10-11 — pass 3: the project's command

*The import and the run are the user's, in the portal; the sample's drop is the user's, from a space.
The readings are Claude's, from `awsds-infra-sandbox-1` (`<Sandbox Account 1>`, `InfrastructureAccess`).
Nothing was written to AWS.*

### [user] 3.1 and 3.2 — the import, the drop and the run

**[user]** "Rodou com sucesso"

### [Claude] The session expired before the reading

The instrument's first call was refused, `Token has expired and refresh failed`, and the user signed in
again as the infrastructure user: **[user]** "infra sso logado".

### [Claude] 3.3 — the run read

- **The run, `f9L7CKQzmUQWQTR`:** `wait_for_file` `SUCCESS` in 7 s, `run_project` `SUCCESS` in 758 s,
  `remove_source` `SUCCESS` in 7 s. The workflow is version `e7180b061abe4bc96561b0470ab8792a`, created
  04:00:35Z: the import replaced it again, so it holds one version and this run alone.
- **The job, `demo-devenv-20261011T041223`**, created at 04:12:25Z through `vpce-0a72d9d2674245821` from
  `10.20.49.77`, the az1 private subnet this time. It ran from 04:15:17Z to 04:23:23Z, 485 s, and ended
  `Completed`. Its stream in `/aws/sagemaker/ProcessingJobs`, at 04:22:58Z:

  ```
  python 3.13.15 at /opt/awsds/venv/bin/python
  sample.csv: 10 rows -> /opt/ml/processing/outbox/sample.result.json
  1 file(s) processed
  ```

  The interpreter is decision 2's house environment, reached by absolute path behind `exec`.
- **The result:** `outbox/20261011T041223/sample.result.json`, 378 bytes, written at 04:23:16Z, `aws:kms`
  with the project key and `BucketKeyEnabled`. Its `sha256` field is the sample's,
  `1a8127eba56e0574a845f42f84e8222af7d1d23f5bec33c36849d7cbd877a58a`, with `rows` 10. The same command run on
  the laptop over `samples/sample.csv` wrote a file with the same sha256,
  `1b2bc4d73bc49bca1a23a6d0971c1365362e785826a33adfcebec7925a248191`: the job's output is byte for byte the
  local run's. `InfrastructureAccess` read the object, decrypting it with the project key.
- **`inbox/` is empty** and `outbox/` holds the probe's object and this result.
- **The keys at the create** repeat the probe's pattern: the grant through SageMaker allowed (04:12:27Z),
  the direct `CreateGrant` in the session `SageMaker` refused, and the volume's `Decrypt` grant from
  `ec2-frontend-api.amazonaws.com` (04:12:32Z).
- **The cost:** about 0.029 USD, 15 task-minutes (0.022) and 485 s of `ml.t3.medium` (0.0067). Verification
  xii for this run.
- **The definition**, `definitions/demo-devenv-job.project.yaml`, renders back to the saved file byte for
  byte. The portal again added only `is_paused_upon_creation: false`.
- **Verifications answered:** i (the editor offers the processing operator as a form, and the import carries
  what the form cannot) and xiii (the result is under the project key).

### [user] 3.4 — the run with an empty inbox

**[user]** "Rodou com sucesso"

### [Claude] 3.4 read: `soft_fail` ends the run `SUCCESS`, and the API names the skip `NONE`

- **The run, `2T6nhkziKgM3GA2`:** `SUCCESS`, `Duration` 647 s, from 04:59:23Z to 05:10:10Z.
- **One task instance, not three.** `RunDetail.TaskInstances` holds only `wait_for_file`, and
  `get-task-instance` reads its `Status` as `NONE`, not `SKIPPED`, with `DurationInSeconds` 611. The two
  downstream tasks have no task instance at all. The API alone cannot tell a skipped task from one never
  scheduled; the task log can.
- **The sensor's log:** 21 pokes of `.../devenv/inbox/*`, every 30 s from 05:00:02Z to 05:10:04Z, then
  `Skipping task.` at 05:10:05Z and `Task finished` at 05:10:10Z.
- **No processing job** was created; the job list is the three of passes 2 and 3.
- **The wait's cost:** 611 s of one task, about 0.015 USD, the figure the plan carried. Verification xi is
  answered: yes, and that.

## 2026-10-11 — pass 4: `demo-python-operator`

### [Claude] 4.1 — the archive and the definition

- **`operators/build.sh`** built `python-operator.zip`: 187 entries, 996,234 bytes, with `demo_tasks.py`,
  `awsds_demo_job/`, petl 1.7.28 (`py3-none-any`) and PyYAML 6.0.1 (`cp312`, `manylinux2014_x86_64`, its
  `_yaml` compiled for x86_64). The first build also carried uv's `.lock` from `--target`; the script now
  removes it.
- **The guide, re-read** ("Using Python and Bash operators"): `python_callable` takes `<module>.<function>`,
  the code is extracted to `/usr/local/airflow/dags`, and a pre-installed package wins over a bundled one.
  PyYAML is in that set, so verification viii expects the worker's copy.
- **The definition**, `operators/python/demo-python-operator.yaml`: the sensor on `python/inbox/*`, then
  `PythonOperator` with `python_callable: demo_tasks.run` and the bucket, inbox and outbox as `op_kwargs`.
  It renders and parses.
- **A folder marker satisfies `inbox/*`.** A space's `mkdir` left zero-byte keys ending in `/`
  (`devenv/inbox/` at 01:25:25Z), `S3KeySensor` with `wildcard_match` lists the prefix and `fnmatch`es
  each key, and `*` matches the empty rest of `inbox/`. `demo-devenv-job` never met it, because
  `S3DeleteObjectsOperator` removes the marker with the files. The worker variants delete only what they
  processed, so a second run would fire on the marker alone. Their sensors watch `inbox/?*`, which needs
  one character after the slash (tested with `fnmatch` on both keys).

### [user] 4.2 — the workflow, and the *Python Operator* form

**[user]** "Abrindo o python operator, no campo file aparece `demo_tasks`, function `run`."

### [Claude] 4.2 read before the run: the archive is stored as uploaded

- **The form split the import's `python_callable: demo_tasks.run`** into *File* `demo_tasks` and *Function*
  `run`: the *File* field names a module inside the uploaded archive.
- **The workflow `demo-python-operator-4ftmCaOAtJ`**, created 05:32:42Z by the project role, is `READY` with
  one version, `761c2c8e445a9dbad1e41e11f251679e`. `SO-1`, `SO-2` and `SO-3` pass.
- **The code (verification vii, first half):** `Code` is `dev/operatorFiles/python-operator.zip`, pinned to
  S3 version `8As0tFX6IybJm5RY_Rnq28psRCxTxryx`, uploaded 05:32:39Z and snapshotted 05:32:43Z. The object
  is 996,234 bytes under the project key, and its sha256 (`4e95f1a7…b6da`) equals the archive
  `build.sh` made: the portal stored one `.zip` as it was, neither nested nor re-zipped. Pass 2's `hello.py`
  is still beside it, two versions.

### [user] 4.2 — the first run

**[user]** "Falhou: `There was an error executing run hmcXpEy18zOKCPR: Workflow execution failed, please check
the task execution logs for more details`"

### [Claude] The worker failed before any task: its code fetch

- **The tasks:** `wait_for_file` `FAILED` in 102 s, `run_project` `UPSTREAM_FAILED`. The sensor's log holds
  two lines, `Preparing the execution environment.` at 05:35:55.613Z and `Execution environment preparation
  failed due to an internal server error.` at 05:35:55.664Z. No task code ran, the sensor's included.
- **The worker:** its network interface was created at 05:35:28Z by the service-linked role
  (`AmazonMWAAServerless-vpc-networking`) and attached by ECS at 05:35:31Z, address `10.20.2.142` in the az1
  private subnet. Its only call in CloudTrail is `CreateLogStream` through the logs endpoint at 05:35:55Z.
- **Its DNS and flow logs at 05:35:55Z:** it resolved `logs.us-west-2.amazonaws.com` (the endpoint,
  `10.20.10.146`) and `s3.us-west-2.amazonaws.com` (public addresses, reached through the gateway route), and
  held one connection with S3, `3.5.84.222:443`: 12 packets each way, 3,112 bytes out and 6,156 in. The
  archive is 996,234 bytes, so it never came down.
- **The comparison:** 3.4's worker, in a workflow with no `Code`, resolved only
  `awsds-sandbox-smus-projects.s3.us-west-2.amazonaws.com`, the sensor's listing, and never the path-style
  name.
- **The service keeps its own copy of the code.** At the creation (05:32:42Z) it read the archive from the
  projects bucket in the portal's session (a `Decrypt` through S3) and called `GenerateDataKey` three times
  with the encryption context `aws:airflow-serverless:workflow-arn`. At the run it called `Decrypt` with that
  context at 05:35:21Z and 05:35:55Z. `CodeSnapshottedAt` and the guide's 75 GB per-account code quota say
  the same.
- **The S3 gateway endpoint's policy** (`terraform-modules/vpc/endpoints.tf`, Stage 3 step 3.4) admits the
  organization's buckets and seven AWS-owned bucket families, and nothing else.
- **The reading, not yet measured:** the worker fetches the code's snapshot from a bucket the service owns,
  the endpoint's allow-list refuses it, and the platform reports the refusal as an internal error. The
  project's own bucket is ruled out by reading: every layer over the project role's read of
  `dev/operatorFiles/` allows it (identity `s3:GetObject*` on the project's prefix, the endpoint's
  organization statement, the bucket's TLS-only policy, the S3-scoped KMS grant), and a KMS refusal would
  have left an event. Nothing held here names the service's bucket: a path-style request carries it in the
  URL, which neither log sees, and a gateway endpoint's refusal lands in no trail of ours (Lesson 55).
- **What the workflows without `Code` never met:** the processing job and the S3 tasks read the project's
  bucket, which the organization statement admits. The worker variants are the first to depend on an
  AWS-owned bucket the list does not name, so pass 5 meets the same refusal.

### [user] Where the code is stored

**[user]** "O arquivo zip do storage fica num bucket fora da minha conta?"

### [Claude] The upload is in the account; the copy the service keeps is not in its bucket

- **The upload is in the account**, measured earlier: `dev/operatorFiles/python-operator.zip` in the
  projects bucket, the version the workflow's `Code` pins, byte for byte the built archive.
- **The service generates one more data key for a workflow with code.** At creation, `GenerateDataKey`
  under the project key with the workflow's encryption context ran twice for `demo-devenv-job` (04:00:39Z)
  and three times for `demo-python-operator` (05:32:43Z).
- **It wrote nothing into the projects bucket.** Of its 3,257 object versions, the only two written between
  05:32:30Z and 05:34:00Z are the portal's: the archive (05:32:39Z) and the definition (05:32:41Z).
- **Reading:** the copy the service keeps, encrypted under the project key, lives in storage the service
  owns, which no reading here reaches. Its bucket and its account are unread.

### [user] Which control refuses the snapshot

**[user]** "Entendi que o snapshot do código é gerenciado pelo serviço. Neste caso, qual controle está barrando o
acesso ao snapshot?"

### [Claude] The worker's only path to S3 is the gateway endpoint

- **The route:** the worker's subnet, `awsds-sandbox-private-usw2-az1`, has no default route. Its table holds
  the local range, the peerings and two prefix lists, and `pl-68a54001` (`com.amazonaws.us-west-2.s3`) goes to
  `vpce-0cc3e139c1167ca83`, the S3 gateway endpoint.
- **The address:** `3.5.84.222`, the worker's only S3 peer, sits in that prefix list's `3.5.80.0/21`. Its
  request passed through the endpoint, and the endpoint's policy was evaluated on it.
- **The policy's two statements** (`terraform-modules/vpc/endpoints.tf`): `AllowWithinOrganization` needs
  `aws:ResourceOrgID` to be this organization's, which an AWS-owned bucket's is not, and
  `AllowAwsOwnedServiceBuckets` names seven bucket families, none of them MWAA Serverless's. An endpoint
  policy is an allow-list, so the request matches neither and is refused, whatever its signer.
- **The other layers do not refuse a read of an AWS-owned bucket.** The SCP's S3 statement denies writes
  outside the organization only (`DenyS3ObjectWriteOutsideOrganization`), the security group allows all
  egress, and the flow log reads `ACCEPT` both ways with a reply from S3: the refusal is S3's answer, not a
  dropped packet. It lands in the bucket owner's trail, not here.

### [user] Decision 7: prepare (a)

**[user]** "Pode preparar a medição da opção (a)"

### [Claude] 4.2a prepared: the store, planned and not applied

- **`sandbox/endpoint-audit/`**, rank 57, `[P]`: one CloudTrail Lake event data store,
  `awsds-sandbox-endpoint-refusals`, with one selector (`eventCategory` `NetworkActivity`, `eventSource`
  `s3.amazonaws.com`, `errorCode` `VpceAccessDenied`), this region only, 7-day retention, termination
  protection off, `EXTENDABLE_RETENTION_PRICING`. Registered in `layers.py`, `conventions.md` §6 and
  `terraform-live/README.md`.
- **The plan:** `1 to add, 0 to change, 0 to destroy`, saved, as `InfrastructureAccess` on
  `awsds-infra-sandbox-1`. The provider (6.64.0) accepts the `errorCode` field and the `NetworkActivity`
  category. Nothing was applied.
- **The prices, from the Price List API:** ingestion 0.75 USD per GB at one-year extendable retention
  (`USW2-Ingestion-Bytes-1yearstore-Live-CloudTrail-Logs`), queries 0.005 USD per GB scanned
  (`USW2-QueryScanned-Bytes`), and network activity events on a trail 0.000001 each
  (`USW2-NetworkEventsRecorded`). A handful of refusals costs fractions of a cent. Rows added to
  `docs/PRICING.md` §6.
- **The account holds no other trail or store:** `describe-trails` lists only
  `aws-controltower-BaselineCloudTrail`, the organization's, and `list-event-data-stores` is empty. This is
  `POLICIES.md`'s revision trigger for its CloudTrail absence, and the plan proposes no statement.
- **The positive control** is a read of `sentinel-cogs`, a public bucket in the region that the allow-list
  does not name.
