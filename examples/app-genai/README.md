# app-genai

Each support message of a sample is triaged by a model under the application's guardrail: a label of a
fixed list and a one-sentence summary, held to the sample by a check. The third application of the AWS
Data Science environment, on app-etl's template with no image, no job and no catalog (the infrastructure
repository's Stage 17 step 10.2), and the first that calls a model: Amazon Nova Lite
(`amazon.nova-lite-v1:0`) through each stage's application inference profile, under a guardrail the
application creates and publishes itself (Stage 17 decisions 23 (a) and 24 (b)). Its workflows are
`app-genai-triage`, which keeps the guardrail, triages the sample and checks the answers, and
`app-genai-probe`, one model call without a guardrail, which reads whether the stage refuses it. The
cycle an application on this template follows, from a space to Production, is
`docs/plan/runbooks/sagemaker-application.md` in the infrastructure repository.

| Path | What it is |
|---|---|
| `code/app_genai_tasks/` | the worker's tasks, one module each: `guardrail` (`ensure_guardrail`), `triage` (`triage_messages`), `check` (`check_answers`) and `probe` (`probe_unguarded`), with `common`; packed into `code/app-genai.zip`, both workflows' `code` (D28 class 2b) |
| `prompts/triage.md` | the system prompt: the instructions and the label list, which `check` reads too |
| `guardrail/definition.json` | the guardrail's definition: the members of a `CreateGuardrail` request but its name and its tags |
| `workflows/` | the two workflow definitions, in the CI/CD CLI's notation |
| `samples/messages.jsonl` | forty synthetic messages with their labels, three of them planted: the output of `scripts/make_sample.py` |
| `probes/operator.yaml` | a one-task workflow over `BedrockInvokeModelOperator`, outside the manifest, imported by hand for Stage 17 step 10.4 |
| `manifest.yaml` | the application: its content, the folders the CLI copies, and its three stages, one account each: `dev`, the Sandbox project it is developed in, and `staging` and `prod`, each account's deployment project |
| `scripts/make_sample.py` | the sample's generator, with a fixed seed; `--check` compares the committed file with its output |
| `scripts/build_archive.py` | the workers' archive: the package with the prompt and the definition beside it, fixed dates, no bytecode, imported from an extracted copy as the worker reads it |
| `scripts/dev-cli.sh` | the CI/CD CLI for the `dev` stage in a space, app-etl's script; no storage item names `scripts/`, so the bundle never carries it |
| `tests/` | pytest, offline: the tasks over `botocore.stub.Stubber` and doubles, the definition against botocore 1.43.1's models, the sample, the archive and the manifest against the package |
| `.gitlab-ci.yml` | the pipeline, with the shared gates from `awsds/ci-gates` |
| `pyproject.toml`, `uv.lock` | the project and its lock: no runtime dependency, since the worker carries boto3; the dev group pins boto3 and botocore 1.43.1, the worker's, so the stubs validate requests against its models; the resolver ignores anything published after `exclude-newer` |

No Terraform runs the application: the CI/CD CLI deploys it into a project in every account. What the
infrastructure repository's Stage 17 pass 10 gives it is each account's half of the model call: in each
target, `terraform-live/<env>/studio/genai.tf`, the application inference profile `awsds-<env>-app-genai`
and the project role's statements, and the boundary's exception, which admits an invocation naming a
numbered version of a guardrail of the account; in Sandbox, `sandbox/bedrock/` and
`sandbox/model-access/`; and the chains that start the workflows, `terraform-live/<env>/chains/`. The
application's guardrail is no resource of any slice: the `guardrail` task creates it in each project's
account.

## The workflows

`app-genai-triage` runs three tasks in order, every path under the project's shared prefix,
`{proj.connection.default.s3_shared.s3Uri}app-genai/`, each a `PythonOperator` on the worker with
`retries: 0`:

| Task | Callable | Reads | Writes |
|---|---|---|---|
| `guardrail` | `ensure_guardrail` | `guardrail/definition.json` beside the package; the guardrail `app-genai-<project id>` and its tags | the guardrail created or updated and a version published when the definition's SHA-256 is not the one its tag names, nothing otherwise; its XCom, the guardrail's id, ARN, version and hash as JSON |
| `triage` | `triage_messages` | `inbox/messages.jsonl`, `prompts/triage.md`, `guardrail`'s XCom | one Converse request per message; `work/<UTC time>/answers.jsonl`; its XCom, the totals as JSON |
| `check` | `check_answers` | `triage`'s XCom, the answers and the sample | `outbox/triage-report.json`, then the task fails on any failure the report names |

`app-genai-probe` is one task, `unguarded` (`probe_unguarded`): one Converse request with a fixed prompt
and no `guardrailConfig`, its outcome, `answered` or `refused`, written to `outbox/probe-report.json`
with the answer's length or the refusal's wording. It passes when the outcome equals the stage variable
`EXPECT_UNGUARDED`, so its run in Staging succeeds when the boundary refuses a call without the
guardrail. The bootstrap of `dev` and `staging` creates it, and `prod`'s does not. No bootstrap runs a
workflow.

### The guardrail

The definition holds one denied topic, investment advice; the content filters for sexual content,
violence, hate, insults and misconduct at medium strength, and the prompt-attack filter on the input at
high; e-mail addresses, telephone numbers, names, addresses and card numbers masked (`ANONYMIZE`); and
the two blocked messages. It names no guardrail profile, so the guardrail's own inference stays in
`us-west-2`, and the content filters and the denied topic take the Classic tier: the Standard tier
requires cross-Region inference (AWS's page on safeguard tiers, read 2026-11-17).

The task finds the guardrail by its name, `app-genai-<project id>`, in `ListGuardrails`. Where there is
none it creates it with the definition and the project's tag `AmazonDataZoneProject`. Where the tag
`awsds:definition-sha256` carries the definition's hash and the version the tag
`awsds:definition-version` names reads `READY`, it writes nothing. Otherwise it sends the whole
definition with `UpdateGuardrail`, a full replacement of the draft. Either write is followed by
`CreateGuardrailVersion`, the hash as the version's description, and by both tags. The hash is a tag
because the API reference documents no call that returns the description a version was published with;
the task returns whether `GetGuardrail` on the version gives it back (`version_description_is_hash`),
the reading Stage 17 step 10.4 records.

### The triage request

Each request carries the prompt as the system prompt, the message as the only content of the user's
turn inside a `guardContent` block, `temperature` 0, at most 200 output tokens, and `guardrailConfig`
naming the guardrail's ARN and the version `guardrail` returned, with the trace enabled. Once a request
holds a `guardContent` block the guardrail assesses only those blocks, so the instructions are not
assessed. A masked message also ends with the stop reason `guardrail_intervened`, so a record is
blocked by the trace's actions, `BLOCKED` against `ANONYMIZED`, never by the stop reason. The records
leave out the trace's matched values and the model output it returns, both unmasked.

### The check

The check asserts one answer for each message; for each answer no guardrail blocked, a JSON object at its
start, after an opening code fence if it has one, with a `label` of the prompt's list and a `summary` of
at most 200 characters (the prompt asks for 120); the message on the denied topic blocked by the
application guardrail's topic, by its own trace; the planted e-mail address and telephone number masked
in that trace and found in no answer, the number also as its last seven digits in another layout; and the
labels agreeing with the sample's on at least `MIN_ACCURACY` of the answers let through. The message that
tells the model to ignore its instructions asserts nothing of its own: blocked, it is recorded; let
through, its answer is held to the rules above. An ordinary message a guardrail blocks is recorded under
`unexpected_blocks` and left out of the accuracy. The report carries the model, the guardrail and its
version, the counts, the accuracy, the tokens and each failure, by message id and never with a message's
or an answer's text.

The parse stops at the end of the object an answer begins with (`json.JSONDecoder.raw_decode`), so text
after it fails no answer: Production's `m19` came back on 2026-11-23 as an object followed by a stray
`]`, and the same request answered without it on the retry. The report names those answers under
`text_after_object`, a closing fence aside, and the planted values are searched for in the whole answer,
that text included. Structured output, `Converse`'s `outputConfig` with a JSON schema, is the other
remedy, held back: it changes the request every stage sends, and what Nova Lite and the guardrail do with
it is unmeasured.

### The sample

`scripts/make_sample.py` draws forty messages from templates, one label each by construction, with the
seed 20261117. Three are planted: `m25`, an account message carrying the address
`jordan.reyes@example.com`, on a domain RFC 2606 reserves, and the number `+1 206-555-0142`, in the block
555-0100 to 555-0199 the North American numbering plan keeps for fiction; `m31`, a message telling the
model to ignore its instructions; and `m36`, a request for investment advice. A test holds the committed
file equal to the script's output.

### The stage variables

| Variable | `dev` | `staging` | `prod` |
|---|---|---|---|
| `MODEL_ID` | `${DEV_MODEL_ID}`: the ARN of the `dev` project's application inference profile, exported by the developer | `${STAGING_MODEL_ID}`: `awsds-staging-app-genai`'s ARN, from `staging/studio/`'s output | `${PROD_MODEL_ID}`: `awsds-prod-app-genai`'s ARN, from `production/studio/`'s output |
| `MIN_ACCURACY` | `0.80` | `0.80` | `0.80` |
| `EXPECT_UNGUARDED` | `answered`, then `refused` once Sandbox's deny of an unguarded call is applied (Stage 17 step 10.4) | `refused` | `refused`, which no workflow reads there |

Every ARN carries an account's id, so none is in this repository. The guardrail's ARN and its version
are no stage variable: `guardrail` returns them at each run. No task writes a message or an answer to
its log: each prints counts, message ids and the guardrail's identifiers.

## Working on it

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run python scripts/make_sample.py --check
```

`uv run ruff check` and `uv run ruff format --check` are what the pipeline runs. The `pages` job's
`pdoc` command, without `--output-directory`, serves the documentation the default branch publishes to
Pages.

The workflow tooling is [`awsds-workflows`](https://github.com/felipenoris/awsds-workflows), installed
as a tool (`docs/plan/runbooks/serverless-workflows.md` §T). Its lint reads the manifest and the
workflows it names against the rules of a SageMaker application, offline; the pipeline runs it on every
push with the ceiling's instance types (`LINT_INSTANCE_TYPES` in `.gitlab-ci.yml`), and with no image
repository, since the application has none:

```bash
awsds-workflows lint . --instance-type ml.t3.medium --instance-type ml.t3.large --instance-type ml.t3.xlarge --instance-type ml.m5.large --instance-type ml.m5.xlarge --instance-type ml.c5.large --instance-type ml.c5.xlarge
```

The pipeline pins the tooling at `4401f91`, the merge of `awsds-workflows` pull request #29, whose rule
`operador` also refuses the native notebook operator (the infrastructure repository's Stage 8 5.6). Since
pull request #26 (`37cb5a6`, Stage 17 step 10.3) the rule refuses by name `BedrockInvokeModelOperator`,
`BedrockRaGOperator` and `BedrockRetrieveOperator`: they write what they send and receive to the task
log, and their calls name no guardrail. The application calls the model with boto3 and passes the lint
at `37cb5a6` and at `196acee`, app-etl's pin (read 2026-11-17), and at `4401f91` (read 2026-11-23).
`probes/operator.yaml` uses `BedrockInvokeModelOperator` on purpose and is outside the manifest, so
`lint .` never reads it; `awsds-workflows lint probes/operator.yaml` passes at `196acee` and is refused
at `37cb5a6` and at `4401f91`.

The deploy to the `dev` project runs the CI/CD CLI (`aws-smus-cicd-cli` 1.0.9) from a space on the house
image, as the project's role, with `sandbox/egress` raised with the groups `mwaa` and `bedrock-base`.
The archive comes first, since `bundle` and `deploy` copy and never build:

```bash
python3 scripts/build_archive.py code/app-genai.zip
```

The shell carries what the manifest reads: `DOMAIN_ID`, `DOMAIN_REGION` and `DEV_PROJECT_NAME`, as for
app-etl, and `DEV_MODEL_ID`, the ARN of the project's application inference profile for Nova Lite, which
`aws bedrock list-inference-profiles --type-equals APPLICATION` lists. Then the deploy, which copies the
folders and creates both workflows, and the runs:

```bash
scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
```

```bash
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-genai-triage
```

```bash
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-genai-probe
```

`scripts/dev-cli.sh` is app-etl's, and app-etl's README says what it answers for the CLI. The first
triage run in a project creates the guardrail and publishes its version 1; a second run over the same
definition writes nothing.

`probes/operator.yaml` reaches the portal by hand (Stage 17 step 10.4, verification xl): `render` fills
`{env.MODEL_ID}` and `{domain.region}` from a values file holding `MODEL_ID` and `REGION`, and reads no
account without `--profile`. The filled text goes to the portal's workflow editor, never to the
repository:

```bash
awsds-workflows render probes/operator.yaml --values-file values.json
```

## The pipeline

| Ref | Jobs | Runner |
|---|---|---|
| any branch | `test` (`uv sync --locked`, ruff, pytest, the workflow lint), `secret_detection` and its gate | the test runner, no AWS identity |
| `main` | the same, and `pages` | the test runner |
| a tag `v<semver>` | `test`; `build-task-code` (the workers' archive); `bundle` (the release's bundle, made from the tag's files, failed when it carries a catalog; nothing is deployed in Sandbox); `store-bundle` (the bundle to `awsds-prod-releases`); `release` (the tag's GitLab release); the promotion: `staging-gate` (manual), `staging-check` (Staging's `egress/` with its Bedrock endpoints, the user's to raise, and its deployment project), `staging-deploy` (the CLI's deploy into the project), `staging-test` (the probe's chain, then the triage's, and both reports), `production-check` (Production's project and the deploy role's membership), `production-gate` (manual), `production-deploy` (the CLI's deploy, whose bootstrap creates `app-genai-triage` and runs nothing) | the test runner, the build runner for `store-bundle` and `release`, and the deploy runner for `bundle` and the promotion |

A release is a tag `v<major>.<minor>.<patch>` on `main`, which only a Maintainer can create: the tag is
protected, and that protection is the release gate. A tag whose bundle fails gets no release, and the
release's first run is Staging's leg. `pip-audit` does not run: `GATES_UV_PROJECTS` is unset, since the
lock's runtime set is empty and the gate ends the job on an empty export.

`bundle` runs as `awsds-deploy-sandbox-test`, a member of the `dev` project, and reads the GitLab
project's CI/CD variables `DOMAIN_ID`, `DOMAIN_REGION` and `DEV_PROJECT_NAME`. The CLI refuses a manifest
with an unset `${VAR}`, so the job gives every name it has no value for a placeholder, each stage's
`MODEL_ID` among them. It fails on a missing include, on the CLI's *"Failed to get project
connections"*, and on a bundle carrying `catalog/`, since the manifest declares no catalog and the
targets would import one. The bundle's SHA256 goes down the pipeline as a dotenv report, and the
release's notes name it with the bundle's object.

The promotion runs on the deploy runner, each job cloning `awsds/infrastructure` with the job token, where
the scripts it calls live. `staging-check` reads Staging's egress and then asks EC2 for an available
endpoint of `bedrock-runtime` and of `bedrock`, the group `bedrock-base`, which `check-egress.py` does not
name. `scripts/deploy-application.py` extracts the bundle beside the tag's manifest, fills the stage's
variables from the project and `MODEL_ID` from `<env>/studio/`'s output, runs the CLI's `deploy` and
records the stage's variables for the chains. `staging-test` starts `awsds-staging-chain-app-genai-probe`
and then `awsds-staging-chain-app-genai-triage`, follows each to its end, and reads both reports as the
deploy role: the probe's outcome `refused`, and the triage report's `passed`. Nothing is torn down:
Staging's `make down` is the user's. Production's project is read before the manual gate and gets the
same bundle; its bootstrap creates `app-genai-triage` and runs nothing. Production's first run is started
from `awsds-prod-chain-app-genai-triage`, outside the pipeline, and creates the guardrail there. The jobs
need the hub, the deploy runner, Staging's `egress/` and `production/workloads-egress/`, each raised with
the group `bedrock-base` for the sitting that runs the application.
