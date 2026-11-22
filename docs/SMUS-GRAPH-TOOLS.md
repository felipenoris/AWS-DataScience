# Visual ETL, ML pipelines and workflows in SageMaker Unified Studio

How the portal's graph tools differ, how each reaches a workflow, and what starts a SageMaker
application's run in this estate. Read on 2026-11-21, for the comparison the user asked for that day,
from the files listed under "Where each fact is kept" and from AWS's pages: the ML pipelines, visual
workflows, Visual ETL scheduling and MWAA Serverless operators pages, and the user guide's release notes,
all in [`REFERENCES.md`](REFERENCES.md). Little here is measured, and each section says what is. The
linked files hold the current state; this file is a dated synthesis and does not follow them.

## The graphs

| | Visual ETL | ML pipelines | Workflows |
|---|---|---|---|
| A node is | a source, a transform or a target inside one Spark program | a step: a SageMaker job (processing, training) or an action on a result (a condition, a registration) | a task: an operator that runs a Glue job, a SageMaker job or a pipeline, or Python or Bash on the worker |
| An edge carries | the data, from one node to the next | a dependency, usually one step's output read by another | the order of execution; a task's return value is read downstream as `{{<task>.output}}` |
| What runs the graph | Glue's Spark, as the one script the editor generates | SageMaker Pipelines, which creates each step's job as the pipeline's role | MWAA Serverless: Airflow 3.0.6 with the Amazon provider 9.38.0 (read 2026-11-13), on a 1 vCPU, 3 GiB worker |
| The object | the file `<name>.vetl` under `src/dataflows/` in the project's repository | a SageMaker pipeline, defined in JSON (`CreatePipeline`, `StartPipelineExecution`) | a workflow, defined in YAML (`CreateWorkflow`, `StartWorkflowRun`) |

The ML pipeline and the workflow both orchestrate jobs; a Visual ETL flow is one job's program. A flow
therefore fills at most one task of a workflow, while an ML pipeline is either started by one task or
converted into tasks.

## Visual ETL and a workflow

AWS documents two routes that schedule a flow, and both run it as a notebook (read 2026-10-13 and
2026-11-21; unmeasured). The editor's schedule is an EventBridge Scheduler schedule whose target is
`CreateTrainingJob`; the workflow route is a DAG whose `NOTEBOOK_PATH` names the `.vetl`. MWAA Serverless
lists `SageMakerNotebookOperator` as its only Unified Studio artifact executor. The editor shows the script
it generates and can convert the flow to a notebook. No page read exports a flow into a Glue job task.

In this estate the notebook route meets the [D13](plan/decisions/D13-lake-formation-enforcement.md)
boundary: a notebook task is a training job with no network setting, and
[6d](plan/stages/stage-06d-unified-studio-remainder.md) decision due 14 (b) keeps the portal's notebook
task out. A flow graduates as the script its editor generates, into the application's `glue/` as a Glue
job ([D28](plan/decisions/D28-workflow-contract.md) class (2c)), and a `GlueJobOperator` task runs it. The
`.vetl` and its schedule stay in the project.

## An ML pipeline and a workflow

### A pipeline converted into a workflow

The ML pipelines page exports a definition as JSON alone (*Download pipeline definition (JSON)*), the
format `CreatePipeline` takes, and names no workflow (re-read 2026-11-21).

The conversion exists on the workflows side (released 2026-06-04; read 2026-11-21; unmeasured).
*Create Workflow → Import SageMaker Pipeline* lists the account's pipelines and converts the latest version
of the one chosen into a workflow's YAML and its visual DAG. The workflow is a copy that a later change to
the pipeline does not reach, and no schedule comes across; a model evaluation step followed by a condition
step is not supported. The page restricts the import to IAM domains and names no operator for the
converted tasks.

`awsds-studio` is an Identity Center domain (`IAM_IDC`), yet its portal shows Feature Store, which AWS
documents for IAM-based domains alone ([Stage 17](plan/stages/stage-17-sandbox-machine-learning.md)
verification xxvii). Whether *Create Workflow* offers the import here is therefore a reading for Stage 17's
pass 5, and so, if it does, is whether the converted tasks keep each step's network, key and tags, which
the D13 boundary requires of every job.

### A pipeline started by a workflow

MWAA Serverless's operators page lists `SageMakerStartPipelineOperator`, `SageMakerStopPipelineOperator`
and `SageMakerPipelineSensor` (re-read 2026-11-21). The start operator calls `StartPipelineExecution` with
`pipeline_params`, a templated field, and returns the execution's ARN ([`SUP-372`](AWS_SUPPLEMENT.md)).

Stage 17 decision 19 (b) designs this path for `app-ml`, in the `dev` project alone. The workflow
`app-ml-pipeline` creates or updates the pipeline `app-ml-{proj.id}` from `pipeline/definition.json` in the
worker's archive (`upsert`), starts an execution and waits for it (`start`), and reads the execution's
steps and the training job's AUC (`check`). The definition travels as a file because the CI/CD CLI's bundle
has no content type for a pipeline. The workflow has never run.

The service shapes that wait:

- `wait_for_completion` is false by default: without it the task returns the ARN, and the next task runs
  while the pipeline is still executing.
- The service ignores `deferrable`, so the wait holds a worker, billed at 0.088 USD per task-hour.
- `execution_timeout` is at most 3,600 s, so one task cannot wait for a pipeline that runs longer than an
  hour.
- Each step's job is created by the pipeline's role, the project role in the design, under the D13
  boundary, so the definition carries each step's network, key and tags. Whether a definition admits a
  parameter inside `VpcConfig` and `Tags` is unmeasured (verification lxi).

### The links compared

| | The start operator | The import |
|---|---|---|
| The pipeline afterwards | stays a SageMaker object, with its own executions | is copied once into the workflow's tasks |
| A later change to the pipeline | reaches the next run | does not reach the workflow |
| What runs the steps | SageMaker Pipelines | MWAA Serverless, through operators the page does not name |
| Where AWS offers it | in any workflow, as an operator on the service's list | in IAM domains |
| In this estate | designed (`app-ml-pipeline`), never run | unread |

Neither link lets a pipeline start a workflow.

## The workflow in a SageMaker application

```text
EventBridge Scheduler                         when: the cron and the pause
└─ Step Functions, one machine per chain      in what order; waits for each run
   └─ workflow (MWAA Serverless)              what one run executes
      ├─ GlueJobOperator → Glue job (the script a Visual ETL flow generated)
      ├─ SageMakerProcessingOperator, SageMakerTrainingOperator → SageMaker job
      ├─ SageMakerStartPipelineOperator → ML pipeline, a graph SageMaker runs
      └─ PythonOperator, BashOperator → code on the worker
```

The workflow controls each run: which tasks run, in what order, with which parameters. The CI/CD CLI's
`run` starts nothing but workflows ([Stage 18](plan/stages/stage-18-staging-deployment-project.md)
question ix, measured 2026-10-19).

The start comes from above the workflow ([D41](plan/decisions/D41-sagemaker-application.md),
[Stage 10](plan/stages/stage-10-orchestration-promotion.md) decision 13). In Staging and Production an
EventBridge Scheduler schedule starts a Step Functions state machine per chain. The machine starts the
workflow with `StartWorkflowRun`, reads `GetWorkflowRun` every 60 s until `SUCCESS`, fails on `FAILED`,
`TIMEOUT` or `STOPPED`, and times out at 14,400 s. One object per chain holds the cron and the pause, and
one execution history records every start. The `prod` stage's bootstrap also runs `app-etl` once per
deploy ([Stage 19](plan/stages/stage-19-smus-native-data-product.md) decision 14). In Sandbox a member
starts a workflow from the portal or with the CLI's `run`.

A task starts a service, never a portal tool: a Glue job, a SageMaker job, a SageMaker pipeline, or code on
the worker. Visual ETL reaches a run as the Glue job its script became, and an ML pipeline as a nested
graph that SageMaker runs and the workflow sees as one task.

Two acts stand outside every workflow: the deploy, which the CLI makes when the GitLab pipeline calls it
(the bundle's code and workflows, the catalog's import), and the approval of a model version, which a
deploy role makes.

In one sentence: in a SageMaker application the workflow controls each run and its tasks start the
services, while the chain starts the workflow in Staging and Production and a member starts it in Sandbox.

## What is unmeasured

- A Visual ETL task or schedule in this estate ([`SMUS.md`](SMUS.md), the workflow surface).
- Whether *Create Workflow* offers the import in `awsds-studio`, and what the converted tasks carry.
- An ML pipeline started by a task: who creates each step's job, whether the pipeline's tags reach it, and
  a parameter inside `VpcConfig` and `Tags` (Stage 17 verification lxi).
- The ML pipelines editor's step forms against the D13 boundary (Stage 17 step 5.3).

## Where each fact is kept

| Subject | File |
|---|---|
| The workflow surface, Visual ETL's routes and the pipeline import | [`SMUS.md`](SMUS.md), the workflow surface |
| The AI/ML menu's ML pipelines entry, and the workflows of `app-ml` | [`sagemaker-ai-ml.md`](plan/runbooks/sagemaker-ai-ml.md) §E and §W |
| What the provider's SageMaker operators call | [`AWS_SUPPLEMENT.md`](AWS_SUPPLEMENT.md), `SUP-372` |
| Authoring a workflow, and the service's limits | [`serverless-workflows.md`](plan/runbooks/serverless-workflows.md) |
| The chain and a run in Production | [`sagemaker-application.md`](plan/runbooks/sagemaker-application.md) §X |
| Decision 19 and the pipeline increment | [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md), decision 19 and step 9.8 |
| The import as a release, and what it moves | [`upstream-releases.md`](plan/upstream-releases.md), the SMUS table |
| The pages read | [`REFERENCES.md`](REFERENCES.md) |
