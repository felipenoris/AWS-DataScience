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

### [user] 4.2a authorized

**[user]** "pode aplicar e fazer as consultas. usuário sso infrastructure logado."

### [Claude⚡] 4.2a — the store refused: CloudTrail Lake takes no new customers

*Authorized in chat by the user. The two peer sessions were told before the apply. Run as the
infrastructure user, `InfrastructureAccess` on `awsds-infra-sandbox-1` (`<Sandbox Account 1>`).*

- **The re-plan**, after the `checkov` skip comment: `1 to add, 0 to change, 0 to destroy`.
- **The apply failed at the create:**

  ```
  Error: creating CloudTrail Event Data Store (awsds-sandbox-endpoint-refusals): operation error
  CloudTrail: CreateEventDataStore, https response error StatusCode: 400, RequestID:
  72dfacc9-0343-41df-af84-ecb1c53e1386, InvalidParameterException: CloudTrail Lake is no longer accepting
  new customers. Existing customers can continue to use their event data stores.
  ```

- **Nothing was created:** `terraform state list` is empty and `list-event-data-stores` returns nothing.
- **No guide page read for 4.2a says so.** The CloudTrail guide's page on network activity events offers an
  event data store beside a trail, and the 2024 announcement does too. The account had never created a
  store, so it is a new customer.
- **The other instrument is a trail**, with the same selector, delivering to a bucket of its own. Whether
  network activity events cover a gateway endpoint is still unread; the announcement names S3 and never
  says "gateway".

### [Claude] The refused slice removed from the branch

`sandbox/endpoint-audit/` describes a resource AWS no longer creates for this account, so it left the
branch with its rows in `layers.py`, `conventions.md` §6 and `terraform-live/README.md`; git history keeps
it. The failed apply left an empty state, `sandbox/endpoint-audit/terraform.tfstate` (619 bytes), in
`awsds-sandbox-tfstate`, which stays: removing it is a write nobody asked for, and a trail built under the
same slice name would reuse it. `docs/PRICING.md` keeps the Lake prices, marked closed to new customers.

## 2026-10-11 — pass 5 prepared, the session left down

*Written by Claude in the sitting that ran it. Every reading is Claude's own, from `awsds-infra-sandbox-1`
(account `<Sandbox Account 1>`, permission set `InfrastructureAccess`). Nothing was written to AWS.*

### [Claude] The state before

- **`make status`:** every slice down, estimated burn USD 0.0000/h. `sandbox/egress` holds 0 resources
  and the hub's two hosts are stopped.
- **`./aws/sandbox-orchestration.py` exits 2 on `SO-4` alone:** `demo-python-operator`'s run
  `hmcXpEy18zOKCPR` is `FAILED`. `python/inbox/` still holds the sample, `demo-bash-operator` does not
  exist, and no call failed.

### [user] The scope

**[user]** chose "Só 3, sem AWS": the upkeep and the control's files, with no AWS write. For the next
raise the user chose "GROUPS=redshift", so it is `make up ENV=sandbox GROUPS=redshift` and 6h's negatives
can share the window.

### [Claude] 5.0 written, not run

The probe version of `demo-bash-operator` and the instrument's contract for it are in the stage file's
5.0. Neither has run on a worker.

## 2026-10-11 — 5.0: the probe run, and decision 7's premise

*The session was raised by the user. The portal acts are Claude's, in the user's Chrome through Claude in
Chrome, signed in as the Data Scientist user; the file was chosen by the user in Chrome's file dialog.
Every reading is Claude's own, from `awsds-infra-sandbox-1` (`<Sandbox Account 1>`,
`InfrastructureAccess`). Account ids are redacted as `INDEX.md` requires, and the portal's session name
as `<Identity Center user id>@<environment id>`.*

### [user] The session and the authorization

**[user]** "Subi o ambiente com GROUPS=redshift, pode importar o probe e fazer as leituras necessárias",
then "autorizo os applies necessários".

**[Claude]** The hub's two hosts `running` since 20:14:07Z and 20:14:10Z; Sandbox's VPC holds 20 interface
endpoints `available`, `redshift-serverless` among them.

### [Claude] The probe gained a positive control

`endpoint_refusal`, a third task with no dependency, lists `sentinel-cogs` (a public bucket in the
region) with virtual-hosted and path-style addressing. The project role's
`SageMakerStudioProjectUserRolePolicy` v75 (`DataLakeCrossAccountS3Permissions`) allows `s3:ListBucket`
on any other account's bucket and the boundary (`v2`) allows all but the lake's prefixes, so only the
gateway endpoint's policy can refuse it.

### [Claude⚡] 5.0 — the import, the save and the run, in the portal

- **The browser.** The built-in browser held no portal session and has no file upload; Claude in Chrome
  answered after the user connected it. The import creates its file input outside the page, so the user
  chose `demo-bash-operator.yaml` in Chrome's dialog. The editor showed the three Bash Operator tasks.
- **The first save was refused** at 20:38:16Z: `CreateWorkflow` carried `code.s3Location`
  `<domain>/<project>/dev/operatorFiles/demo-bash-operator.zip`, the editor's pre-filled *Operator files
  zip S3 location*, and the service answered `ValidationException: Code not found in specified S3
  location`. Nothing was uploaded.
- **The second save** at 20:39:00Z, with that field emptied in *Settings → Storage*, carried `code` null
  and succeeded: `demo-bash-operator-Q7BcYzndcz`, `READY`, version `477429955fdcf7c5ce58a1a953ccbda6`,
  `manual_only`, the project role, both private subnets, the project's security group and key. Both
  requests carried the seven environment variables.
- **The run**, `b7FgLsjotHxaCde`, started by the portal's session at 20:39:34Z.

### [Claude] 5.0 read: the `Code` object is decision 7's variable

- **The run:** `FAILED`, 92 s from 20:39:39Z. `caller_identity` `SUCCESS` in 9 s, `endpoint_refusal`
  `FAILED` in 5 s, `reach_pypi` `FAILED` in 15 s. The worker prepared its environment for every task,
  where a workflow with a `Code` object failed before its first.
- **`caller_identity`**, worker `10.20.18.160` in `awsds-sandbox-private-usw2-az1`:

  ```
  cwd: /var/tmp/airflowtmpjdoxn9ot
  env: DataZoneDomainId= DataZoneDomainRegion= DataZoneEndpoint= DataZoneEnvironmentId= DataZoneProjectId= DataZoneStage= ProjectS3Path=
  python 3.12.14 at /opt/mwaa-serverless-venv/bin/python3
  boto3 1.43.1 botocore 1.43.1 from /opt/mwaa-serverless-venv/lib/python3.12/site-packages/boto3
  AWS_REGION us-west-2 AWS_DEFAULT_REGION us-west-2
  sts endpoint https://sts.us-west-2.amazonaws.com resolves to 10.20.51.63
  caller arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/AmazonMWAAServerless
  ```

  `/usr/local/airflow/dags` held the user's shell files, owned by `mwaa-serverless-user`, the DAG file
  dag-factory generated (`f2db88a4-….py`, 711 bytes), an `ex_<uuid>` folder and `logs/`. **Verification
  x: the project role, session `AmazonMWAAServerless`.** CloudTrail's `GetCallerIdentity` at 20:40:23Z came
  from `10.20.18.160` through `vpce-01a0b145d0f80a185`, Sandbox's `sts` interface endpoint. An inline
  command runs in a temporary folder, not in `/usr/local/airflow/dags`, and the seven variables the portal
  injects reach the task, though `get-workflow` returns no `EnvironmentVariables`.
- **`reach_pypi`**, worker `10.20.105.187` in `awsds-sandbox-private-usw2-az2`:

  ```
  proxy:
  resolve: pypi.org failed: OSError(16, 'Device or resource busy')
  urllib: URLError(OSError(16, 'Device or resource busy'))
  urllib: no answer from pypi.org
  urllib: 2 s
  pip 23.2.1 from /opt/mwaa-serverless-venv/lib/python3.12/site-packages/pip (python 3.12)
  Could not fetch URL https://pypi.org/simple/six/: connection error: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/six/ (Caused by NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0x7f6305f06de0>: Failed to establish a new connection: [Errno 16] Device or resource busy'))
  ERROR: Could not find a version that satisfies the requirement six (from versions: none)
  ERROR: No matching distribution found for six
  pip: download failed, exit 1
  pip: 2 s
  ```

  `/awsds/sandbox/dns-firewall` holds the cause: at 20:41:01Z, `10.20.105.187` asked for `pypi.org.` and
  `pypi.org.us-west-2.compute.internal.`, A and AAAA, and got `NXDOMAIN` with `firewall_rule_action`
  `BLOCK` (rule group `rslvr-frg-833312daf8ef47fc`). **Verification ix: the reach fails in about 2 s,
  visibly, at name resolution**; the worker's resolver reports the firewall's `NXDOMAIN` as errno 16, not
  as a name error, and no packet left for PyPI.
- **`endpoint_refusal`:**

  ```
  virtual 20:40:17 list sentinel-cogs
  virtual refused: AccessDenied - Access Denied
  path 20:40:17 list sentinel-cogs
  path refused: AccessDenied - Access Denied
  ```

  Both styles were refused in about 35 ms each. The task's exit 1 was the probe's own criterion, which
  expected the wording "because no VPC endpoint policy allows": S3 gives that detail only to a requester
  in the bucket owner's account. The template now counts the `AccessDenied` code, and the definition the
  portal holds keeps the first criterion.
- **`./aws/sandbox-orchestration.py`:** `SO-1`, `SO-2` and `SO-3` pass on `demo-bash-operator`, `SO-3`
  reading "the probe, no Code object"; `SO-4` is a note.
- **The cost:** three tasks at the one-minute minimum, about 0.0044 USD.
- **The definition**, `definitions/demo-bash-operator.probe.yaml`, renders back to the saved file byte
  for byte; the portal added only `is_paused_upon_creation: false`.

## 2026-10-11 — 4.2a: the trail, applied, and the two runs it watches

*Authorized in chat by the user ("autorizo os applies necessários"). The four peer sessions were told
before the apply. Run as the infrastructure user, `InfrastructureAccess` on `awsds-infra-sandbox-1`
(`<Sandbox Account 1>`), after the user signed in again ("infra sso logado"): Terraform's first `init`
met `UnauthorizedException: Session token not found or invalid` while the CLI still answered from its
cached role credentials.*

### [Claude] `sandbox/endpoint-audit/`, a trail this time

One trail, `awsds-sandbox-endpoint-refusals`, in this region only, with no global service events, log
file validation on and one advanced selector (`eventCategory` `NetworkActivity`, `eventSource`
`s3.amazonaws.com`, `errorCode` `VpceAccessDenied`), so it records no management event. Its bucket has the
same name: SSE-S3, public access blocked, ACLs disabled, TLS-only, CloudTrail's two statements bound to
the trail by `aws:SourceArn`, a 7-day expiry and `force_destroy`. Registered again in `layers.py`
(rank 57), `conventions.md` §6 and `terraform-live/README.md`; checkov 16 passed, 9 skipped, 0 failed.
`init` reused the empty state object.

### [Claude⚡] The apply

- **The plan:** `7 to add, 0 to change, 0 to destroy`.
- **The apply, from the saved plan:** `Apply complete! Resources: 7 added, 0 changed, 0 destroyed.`
- **The re-plan:** `No changes`, exit 0.
- **The trail:** `IsLogging` `True` since 20:49:49Z, no delivery error, the three field selectors as
  declared. `describe-trails` lists `aws-controltower-BaselineCloudTrail` and this one.
- **`POLICIES.md`'s CloudTrail revision trigger is met**, and no statement follows.

### [Claude⚡] The positive control and the measurement, started

From the portal's *Workflows* list, *Run now*, in the user's Chrome:

- `demo-bash-operator`, run `0ilW00z6Z1CZfWf`, created 20:51:52Z. Its `endpoint_refusal` listed
  `sentinel-cogs` at 20:52:34Z with both addressing styles, refused both times with `AccessDenied - Access
  Denied`;
- `demo-python-operator`, run `mObMMosGwVA98XO`, created 20:52:06Z, the sample still in `python/inbox/`.

### [Claude] 4.2a read: the refused bucket, named

The trail delivered three network activity files at 20:57:31Z to 20:57:44Z, under
`AWSLogs/<Sandbox Account 1>/CloudTrail-NetworkActivity/`, a prefix of its own beside `CloudTrail/`. All
three records came through `vpce-0cc3e139c1167ca83`, Sandbox's S3 gateway endpoint, with `errorCode`
`VpceAccessDenied` and `errorMessage` "The request was denied due to a VPC endpoint policy":

| Time | Event | Caller | Resource |
|---|---|---|---|
| 20:52:34Z | `ListObjects` | the project role, session `AmazonMWAAServerless`, from `10.20.41.160` | `arn:aws:s3:::sentinel-cogs` |
| 20:52:34Z | `ListObjects` | the same | `arn:aws:s3:::sentinel-cogs` |
| 20:52:51Z | `GetObject` | `userIdentity.type` `AWSService`, `invokedBy` and source `airflow-serverless.amazonaws.com` | `arn:aws:s3:::mwaa-serverless-code-files-<AWS-owned account>-us-west-2-prod/<Sandbox Account 1>/demo-python-operator-4ftmCaOAtJ/761c2c8e445a9dbad1e41e11f251679e/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/operatorFiles/python-operator.zip` |

- **The positive control answered: network activity events cover a gateway endpoint**, and a
  path-style request names its bucket as a virtual-hosted one does (verification xv, second half). The
  owner's account reads `HIDDEN_DUE_TO_SECURITY_REASONS` in `resources`.
- **The code fetch is the service's own request**, not the project role's: a `GetObject` by
  `airflow-serverless.amazonaws.com` of the snapshot the service took at the workflow's creation, keyed
  by account, workflow, version and the upload's own key (verification xv, first half). The worker's
  DNS and flow logs match it: `10.20.38.127` resolved `s3.us-west-2.amazonaws.com` at 20:52:51Z and
  exchanged 12 packets each way with `16.15.35.200:443`, 3,108 bytes out and 6,156 in, the first
  failure's counts within 4 bytes.
- **Decision 7's reading is measured**, and (a)'s family is `mwaa-serverless-code-files-*-<region>-prod`,
  the wildcard standing for the service's account id.

### [Claude⚡] 4.2a: `vpc-v0.4.0`, and `sandbox/foundation` applied

*The user signed in again after Terraform met `Session token not found or invalid` a second time
("usuário sso infra logado"). No peer session was running at the apply. Run as the infrastructure user,
`InfrastructureAccess` on `awsds-infra-sandbox-1` (`<Sandbox Account 1>`), by
`runbooks/terraform-changes.md` Recipe B.*

- **The module:** `default_aws_buckets` gains `mwaa-serverless-code-files-*-${region}-prod`. A plan of
  `sandbox/foundation` against the local module read `0 to add, 1 to change, 0 to destroy`, the S3
  gateway endpoint's policy alone; the caller's `source` was reverted and re-initialised.
- **Commit 1 and the tag:** the module alone (`1305f38`), tagged `vpc-v0.4.0` after `git ls-remote`
  read `vpc-v0.3.1` as the newest; origin answered `1305f389…	refs/tags/vpc-v0.4.0`.
- **Commit 2:** `sandbox/foundation` takes `vpc-v0.4.0` (`c8299a6`); the hook first refused it with
  `Module source has changed` until the slice was re-initialised. The other four callers stay on
  `vpc-v0.3.1`.
- **The plan:** `0 to add, 1 to change, 0 to destroy`, the two ARNs of the family added to
  `AllowAwsOwnedServiceBuckets`.
- **The apply, from the saved plan:** `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.`
- **The re-plan:** `No changes`, exit 0; the live policy of `vpce-0cc3e139c1167ca83` carries both ARNs.

### [Claude⚡] The re-run, from the CLI

The portal in the user's Chrome had lost its session (the sign-in page), so the run was started as the
infrastructure user: `aws mwaa-serverless start-workflow-run`, run `N05WyTNjUcdxbw0`, 21:08:54Z. The
portal's own call carries only the workflow ARN and a client token, so the run is the same one; the
caller differs.

### [Claude] 4.3 — the re-run read: a `Code` object runs on the private tier

- **The run, `N05WyTNjUcdxbw0`:** `SUCCESS`, 96 s from 21:09:06Z. `wait_for_file` `SUCCESS` in 8 s,
  `run_project` `SUCCESS` in 6 s. Each task's log opens with `Preparing the execution environment.`
  and, a second later, `Execution environment is ready.` (21:09:46Z and 21:10:37Z), the line the two
  failed runs never reached.
- **`run_project`'s output:**

  ```
  python 3.12.14 at /opt/mwaa-serverless-venv/bin/python3
  caller arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/AmazonMWAAServerless
  import petl: 1.7.28 from /usr/local/airflow/dags/petl/__init__.py
  import yaml: 6.0.2 from /opt/mwaa-serverless-venv/lib64/python3.12/site-packages/yaml/__init__.py
  sample.csv: 10 rows -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/orchestration-demo/python/outbox/20261011T211041Z/sample.result.json; source deleted
  1 object(s) processed
  ```

  **Verification viii: yes, and the pre-installed copy wins.** `petl`, absent from the worker, imported
  from the archive; the archive's PyYAML 6.0.1 lost to the worker's 6.0.2. **Verification x** for a
  Python task: the project role, session `AmazonMWAAServerless`.
- **The result:** `python/outbox/20261011T211041Z/sample.result.json`, 378 bytes, `aws:kms` with the
  project key and `BucketKeyEnabled`; its sha256, `1b2bc4d7…a248191`, is the processing job's result's
  and the local run's. `python/inbox/` holds only its folder marker.
- **`./aws/sandbox-orchestration.py` exits 0:** `SO-4` passes on `demo-python-operator`, `SO-7` reads
  its inbox empty and one object in its outbox.
- **The cost:** two tasks at the one-minute minimum, about 0.0029 USD; the failed run before it,
  `mObMMosGwVA98XO` (125 s, its sensor 89 s), about 0.0022.
- **The definition**, `definitions/demo-python-operator.yaml`, renders back to the saved file byte for
  byte; the portal added only `is_paused_upon_creation: false`.

## 2026-10-11 — pass 5: `demo-bash-operator`, the exercise

*The session stayed up from the passes before. The user merged the previous PR, asked for pass 5 and
authorized the AWS writes it needs ("pode aplicar as escritas necessárias na aws"), and later the
deletion of the probe workflow by name. The portal acts are Claude's, in the user's Chrome through
Claude in Chrome, signed in as the Data Scientist user (the user signed in); the definition file was
chosen by the user in Chrome's dialog. Every reading is Claude's own, from `awsds-infra-sandbox-1`
(`<Sandbox Account 1>`, `InfrastructureAccess`).*

### [Claude] 5.1 — the definition and the archive

- **`operators/bash/demo-bash-operator.yaml`**: the sensor on `bash/inbox/?*`; `run_command`, an inline
  command that prints its working directory and `PYTHONPATH`, changes to `/usr/local/airflow/dags` and
  runs `python3 -m awsds_demo_job.s3`; and `reach_pypi`, whose command is the script's name. It renders
  and parses, and each command passes `bash -n`.
- **`operators/build.sh`** built `bash-operator.zip`, 4,849 bytes: `reach_pypi.sh` and `awsds_demo_job/`
  at its root.

### [Claude⚡] 5.2 — the drop, the import, the save and the run

- **The drop:** the portal's *Files* page created `orchestration-demo/bash/` and `bash/inbox/` as folder
  markers (21:30:15Z and 21:30:36Z) and uploaded the repository's sample there, 279 bytes, through the
  dialog's file input.
- **The import:** *Actions → Import definition file* in the probe's editor. The editor then held the
  three tasks under the workflow's bare name.
- **The archive:** *Settings → Storage → Python/Bash Operator Files* took `bash-operator.zip` through its
  file input. The field below it became *Operator file S3 location*, "stored directly (no zip)", at
  `dev/operatorFiles/bash-operator.zip`.
- **The first save was refused** at 21:33:41Z: `CreateWorkflow` answered `ConflictException: Workflow
  with given name already exists`. The import does not replace a saved workflow; the archive was
  uploaded all the same (S3 version `DXBHpJbq…`, 21:33:37Z).
- **The probe deleted**, with the user's approval: `demo-bash-operator-Q7BcYzndcz`, from the portal's
  *Workflows* list, *Delete workflow* and the word "confirm" (`DeleteWorkflow`, 21:35:22Z). Its two runs
  went with it; its log group stays.
- **The second save** at 21:35:48Z created `demo-bash-operator-K04PshmXlc`, `READY`, version
  `ab2013f4ee6c013b506e61a3dc0790a5`, its `Code` `dev/operatorFiles/bash-operator.zip` pinned to S3
  version `OH84z4Jv…` (4,849 bytes), snapshotted at 21:35:48Z.
- **The run**, `xn9EZ2kgVIMcI7h`, started by the portal at 21:36:22Z.

### [Claude] 5.3 — the run read

- **The run:** `FAILED` by design, 148 s from 21:36:28Z. `wait_for_file` `SUCCESS` in 4 s,
  `run_command` `SUCCESS` in 9 s, `reach_pypi` `FAILED` in 13 s. Each task's environment `ready`.
- **`run_command`:**

  ```
  cwd /var/tmp/airflowtmp2nab7fnd PYTHONPATH=/usr/local/airflow/dags:/usr/local/airflow/dags:/opt/mwaa-serverless-venv/lib/python3.12/site-packages
  python 3.12.14 at /opt/mwaa-serverless-venv/bin/python3
  sample.csv: 10 rows -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/orchestration-demo/bash/outbox/20261011T213800Z/sample.result.json; source deleted
  1 object(s) processed
  ```

  A Bash task's `PYTHONPATH` already carries the folder the archive is extracted to.
- **`reach_pypi`**: the operator ran `['/usr/bin/bash', 'tmp6wm8sj1x.sh']`, the script rendered as a
  template into a temporary file, and it printed the 5.0 readings again: no proxy variable, `OSError(16,
  'Device or resource busy')` at resolution, urllib in 2 s, pip 23.2.1 failing in 4 s, exit 1.
- **The result:** `bash/outbox/20261011T213800Z/sample.result.json`, 378 bytes, `aws:kms` with the
  project key and `BucketKeyEnabled`, sha256 `1b2bc4d7…a248191`: the processing job's, the Python
  task's and the local run's. `bash/inbox/` holds only its folder markers.
- **`./aws/sandbox-orchestration.py` exits 0** with every check passing: `SO-4` reads "reach_pypi
  FAILED and every other task SUCCESS, as designed", `SO-3` the exercise's `Code`, `SO-7` an empty inbox
  and one result. The stage's first validation item holds.
- **The trail** delivered no file after 21:00Z: neither re-run met a refusal.
- **The cost:** three tasks at the one-minute minimum, about 0.0044 USD.

### [Claude⚡] Verification vii, the second half: an edit takes a new snapshot

The workflow's description was set to "Stage 6i pass 5" in the portal's settings and saved:
`UpdateWorkflow` at 21:42:08Z, `code` pinned to the same S3 version `OH84z4Jv…`. The workflow gained
version `b960b35f53191b41210702df9be10475`, and `CodeSnapshottedAt` moved from 21:35:48Z to 21:42:08Z,
the code unchanged. The description lands in the definition itself, as a top-level `description`.
`definitions/demo-bash-operator.yaml` is that version, rendered back byte for byte.

## 2026-10-11 — step 3.5: a processing job whose project has dependencies

*The user merged pass 5's PR and asked for this exercise in chat: "Peço exercitar o caso de um SageMaker
Processing Operator com dependências externas, num projeto com dependências gerenciadas pelo uv." After
the plan was shown, the user authorized its AWS writes ("Pode seguir (Recomendado)"), and the three peer
sessions were told before the first one. The session stayed up from pass 5 (hub and Sandbox endpoints,
`GROUPS=redshift`). The portal acts are Claude's, in the user's Chrome through Claude in Chrome, signed in
as the Data Scientist user (the user signed in); the definition file was chosen by the user in Chrome's
dialog. The space's commands are the user's. Every reading is Claude's own, from `awsds-infra-sandbox-1`
(`<Sandbox Account 1>`, `InfrastructureAccess`).*

### [Claude] 3.5 — the project and its folder, on the laptop

- **`awsds-demo-deps`** (`examples/sandbox-orchestration/awsds-demo-deps/`): one CSV in, a JSON summary
  and a Parquet table out. It depends on `petl` (pure Python) and `msgspec` (an extension module), both
  absent from the house environment, and on `pyarrow`, which the house environment holds at 24.0.0.
  Its command prints each dependency's version, the folder it was imported from and its extension module.
- **The fresh lock disagreed with the image**, and `package-uv-job.py` stopped on it: "pyarrow: 26.0.0 in
  the lock, 24.0.0 in the image". The block it printed, `constraint-dependencies = ["pyarrow==24.0.0"]`,
  went into the project's `pyproject.toml`, and `uv lock` moved pyarrow 26.0.0 to 24.0.0 (J1 step 3).
- **The tests**: 8 pass on CPython 3.13.13 with the locked versions. Under pyarrow 26.0.0 the same tests
  passed and the interpreter then hung at exit, the main thread waiting in Arrow's thread pool
  destructor; under 24.0.0 it exited at once. Observed once, on macOS arm64, and not chased further.
- **The local run's summary is byte for byte `awsds-demo-job`'s result** for the sample, sha256
  `1b2bc4d7…a248191`, 378 bytes; the Parquet table is 1,404 bytes, sha256 `31787bc6…8d77b75`.
- **The folder**: 1,735,854 bytes in 176 files, for CPython 3.13 on `x86_64-manylinux_2_28`. From the
  image: pyarrow. Vendored: msgspec 0.22.0 (`msgspec/_core.cpython-313-x86_64-linux-gnu.so`, 438,984
  bytes) and petl 1.7.29.
- **`demo-devenv-deps`** (`devenv-job/demo-devenv-deps.yaml`) is `demo-devenv-job` with the code input at
  `shared/jobs/awsds-demo-deps-0.1.0/`, `PYTHONPATH` at its root, the command `python -m
  awsds_demo_deps`, the job-name prefix `demo-devenv-deps-` and the variant `devenv-deps`. The sensor
  waits on `inbox/?*`, since a folder marker `inbox/` matches `*`.
- **`./aws/sandbox-orchestration.py`** learned the fourth workflow, each processing workflow's code input
  and `PYTHONPATH` (`SO-3`), and an extension module built for another interpreter (`SO-7`). Its run
  before any write exited 0, `demo-devenv-job`'s new `SO-3` assertions passing.

### [Claude⚡] 3.7 — the import and the save

- **The portal session had expired** when the editor's *Actions* menu was first opened, after the user
  signed in to the CLI as the infrastructure user; the user signed in to the portal again as the Data
  Scientist user. A minute later the CLI's token for the `awsds` session was gone from
  `~/.aws/sso/cache` (the folder modified at 22:30Z, the file absent): a deletion, which is what `aws sso
  logout` does, and not an expiry. Who deleted it is not known. The user signed in to the CLI again.
- **The import** went into a new, empty workflow: *Create workflow*, *Actions → Import definition file*,
  *Upload a local file*. The editor then held the three tasks as `demo-devenv-deps`.
- ***Settings → Storage*** offered *Operator files zip S3 location* filled with
  `dev/operatorFiles/demo-devenv-deps.zip`, with no file uploaded. The field was emptied before the save:
  pass 5's probe was refused with `Code not found in specified S3 location` from the same state.
- **The save** at 22:36:12Z (`CreateWorkflow` by the project role) created
  `demo-devenv-deps-5EVIcrWSh3`, `READY`, version `912d88aeae83fca25c3085fc7537b775`, `Code` null. Its
  log group, `/aws/mwaa-serverless/<domain>-<project>/demo-devenv-deps`, existed from the save, empty and
  with no retention.

### [user] 3.6 — the folder built in a space, and the first attempt refused

The user started a new space, `jupyter-houseimage`, cloned this branch into `~/AWS-DataScience` and ran
J1 step 2 as written. The pasted output:

```
sagemaker-user@default:~$ cd ~/AWS-DataScience && ./examples/sandbox-orchestration/operators/package-uv-job.py examples/sandbox-orchestration/awsds-demo-deps /tmp/awsds-demo-deps-0.1.0
error: No interpreter found for Python 3.14 in virtual environments, managed installations, or search path

hint: A managed Python download is available for Python 3.14, but Python downloads are set to 'never'
```

### [Claude] Why the script could not run in a space, and the fix

- **uv reads `.python-version` from the script's folder upwards**, wherever the command is typed, so the
  repository's 3.14 (the tooling's) chose the script's own interpreter, and the image's
  `UV_PYTHON_DOWNLOADS=never` refused to fetch it. Reproduced on the laptop with the space's layout: uv's
  downloads off, no managed Python, a 3.12 on `PATH`. Running from another folder failed the same way.
- **Past that, the project's `uv export --locked` and `uv build` need a CPython 3.13**, the project's
  `.python-version`, and in a space the house interpreter is on no search path: it was installed under
  `/opt/awsds/python` by a `uv python install` whose `UV_PYTHON_INSTALL_DIR` lives only in its build step.
  The simulation's next refusal read "No interpreter found for Python 3.13 in managed installations or
  search path".
- **The fix**, commit `fcc760b`: the shebang asks for `--python >=3.11`, the script's own requirement, and
  the uv commands it runs name `$AWSDS_PYTHON_ENV/bin/python` through `UV_PYTHON` when the house image
  sets that variable. In the simulation the unchanged command then built the folder; on the laptop the
  output is unchanged but for install metadata.

### [user] 3.6 — the folder built in the space, and copied

```
sagemaker-user@default:~/AWS-DataScience$ which python
/opt/conda/bin/python
sagemaker-user@default:~/AWS-DataScience$ which uv
/opt/conda/bin/uv
sagemaker-user@default:~/AWS-DataScience$ cd ~/AWS-DataScience && git pull
...
Updating 8bc26ee..fcc760b
Fast-forward
 examples/sandbox-orchestration/operators/package-uv-job.py | 15 +++++++++++++--
 1 file changed, 13 insertions(+), 2 deletions(-)
sagemaker-user@default:~/AWS-DataScience$ ./examples/sandbox-orchestration/operators/package-uv-job.py examples/sandbox-orchestration/awsds-demo-deps /tmp/awsds-demo-deps-0.1.0
/tmp/awsds-demo-deps-0.1.0: 1735841 bytes, for CPython 3.13 on x86_64-manylinux_2_28
from the image (1): pyarrow
vendored (2): msgspec==0.22.0, petl==1.7.29
top level: awsds_demo_deps, awsds_demo_deps-0.1.0.dist-info, msgspec, msgspec-0.22.0.dist-info, petl, petl-1.7.29.dist-info
next: copy the folder into the project's storage (in a space: cp -r <folder> ~/shared/<name>/),
      name that prefix as the job's code input at /opt/ml/processing/code, and set
      PYTHONPATH: /opt/ml/processing/code in the job's Environment
sagemaker-user@default:~/AWS-DataScience$ mkdir -p ~/shared/jobs && cp -r /tmp/awsds-demo-deps-0.1.0 ~/shared/jobs/
sagemaker-user@default:~/AWS-DataScience$ find ~/shared/jobs/awsds-demo-deps-0.1.0 -type f | wc -l
176
```

### [Claude] 3.6 read: the folder in S3

- **192 objects under `shared/jobs/awsds-demo-deps-0.1.0/`**, written 22:57:32Z to 22:57:51Z: the 176
  files, 1,735,841 bytes, and 16 zero-byte folder markers, one per folder, which the space's `shared/`
  creates.
- **The 176 files have the names and sizes of the folder the simulation built**, the extension module
  among them.
- **`./aws/sandbox-orchestration.py` exits 0**: `SO-1` `demo-devenv-deps` `READY`, created by the project
  role; `SO-2` its network and key; `SO-3` the code input `shared/jobs/awsds-demo-deps-0.1.0/` and
  `PYTHONPATH` `/opt/ml/processing/code`; `SO-7` "176 object(s), the entry point present, 1 extension
  module(s) for the job".

### [Claude⚡] 3.7 — the drop and the run

- **The drop**, by the user from the space: `orchestration-demo/devenv-deps/inbox/sample.csv`, 279 bytes,
  at 23:03:49Z, with the folder markers `devenv-deps/` and `devenv-deps/inbox/`.
- **The run**, `aB2zorz48GP67hx`, started by the portal at 23:04:21Z.

### [Claude] 3.8 — the run read

- **The run:** `SUCCESS`, 909 s from 23:04:42Z. `wait_for_file` `SUCCESS` in 5 s (23:05:18Z),
  `run_project` `SUCCESS` in 791 s, `remove_source` `SUCCESS` in 6 s (23:19:51Z). `get-workflow-run`
  read `QUEUED` until 23:06:16Z, after the sensor had finished and while the job was being created: the
  run's state lags its task instances.
- **The job:** `demo-devenv-deps-20261011T230601`, created 23:06:03Z through Sandbox's `sagemaker.api`
  endpoint (`SO-8`; the endpoint's id changed with the session's), processing from 23:08:56Z to
  23:16:26Z, 450 s, `Completed`. The container ran its command at 23:16:11Z and printed:

  ```
  python 3.13.15 at /opt/awsds/venv/bin/python
  petl 1.7.29 from /opt/ml/processing/code/petl
  msgspec 0.22.0 from /opt/ml/processing/code/msgspec, extension _core.cpython-313-x86_64-linux-gnu.so
  pyarrow 24.0.0 from /opt/awsds/venv/lib/python3.13/site-packages/pyarrow, extension lib.cpython-313-x86_64-linux-gnu.so
  sample.csv: 10 rows -> sample.summary.json, sample.parquet
  1 file(s) processed
  ```

  **Verification xvi: yes.** A vendored pure-Python package and a vendored extension module load from
  the code input, and the house environment serves the package it holds. The folder markers in the
  prefix did not disturb the download.
- **The outputs**, under `devenv-deps/outbox/20261011T230601/` at 23:16:21Z, both `aws:kms` with the
  project key and `BucketKeyEnabled`: `sample.summary.json`, 378 bytes, sha256 `1b2bc4d7…a248191`, byte
  for byte `awsds-demo-job`'s result and pass 3's; `sample.parquet`, 1,404 bytes, sha256
  `31787bc6…8d77b75`, byte for byte the laptop's, pyarrow 24.0.0 on macOS arm64 and on Linux x86_64
  writing the same file.
- **The inbox is gone**, the marker `devenv-deps/inbox/` with the sample; `devenv-deps/` stays.
- **`./aws/sandbox-orchestration.py` exits 0**, every check passing or a standing note: `SO-4`
  `demo-devenv-deps` three tasks `SUCCESS`, `SO-5` the job isolated, encrypted, with the project's role,
  key and tag and the house image, `SO-7` the inbox empty and two results.
- **The definition** the portal saved is the imported one plus `is_paused_upon_creation: false`;
  `definitions/demo-devenv-deps.yaml` renders back to it byte for byte.
- **The cost:** 15.2 task-minutes (5 s and 6 s billed at the one-minute minimum, and 791 s), 0.022 USD,
  plus 450 s of `ml.t3.medium`, 0.006 USD: about 0.029 USD, pass 3's figure.
