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
