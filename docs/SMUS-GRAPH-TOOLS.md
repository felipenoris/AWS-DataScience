# Visual ETL, ML pipelines, workflows and MLflow in SageMaker Unified Studio

How the portal's graph tools differ, how each reaches a workflow, where MLflow records what they ran, and
what starts a SageMaker application's run in this estate. Read on 2026-11-21, for the comparison the user
asked for that day, from the files listed under "Where each fact is kept" and from AWS's pages: the ML
pipelines, visual workflows, Visual ETL scheduling and MWAA Serverless operators pages, the pipeline
editor's integration page, the MLflow pages of the developer guide and the user guide, and the user
guide's release notes; from MLflow's pages on tracking and tracing; and from the SageMaker and DataZone
service models the AWS CLI 2.37.12 carries. The pages are in [`REFERENCES.md`](REFERENCES.md). Little
here is measured, and each section says what is. The linked files hold the current state; this file is a
dated synthesis and does not follow them.

## The graphs

| | Visual ETL | ML pipelines | Workflows | MLflow |
|---|---|---|---|---|
| A node is | a source, a transform or a target inside one Spark program | a step: a SageMaker job (processing, training) or an action on a result (a condition, a registration) | a task: an operator that runs a Glue job, a SageMaker job or a pipeline, or Python or Bash on the worker | a run, the record of one execution of code: its parameters, metrics, tags and artifacts; in a trace, a span |
| An edge carries | the data, from one node to the next | a dependency, usually one step's output read by another | the order of execution; a task's return value is read downstream as `{{<task>.output}}` | a parent run's link to its child runs (the tag `mlflow.parentRunId`), or a span's to the spans it called; no edge orders an execution |
| What runs the graph | Glue's Spark, as the one script the editor generates | SageMaker Pipelines, which creates each step's job as the pipeline's role | MWAA Serverless: Airflow 3.0.6 with the Amazon provider 9.38.0 (read 2026-11-13), on a 1 vCPU, 3 GiB worker | nothing: a client logs what a notebook, a task or a job ran, the MLflow App stores it, and the UI draws it afterwards |
| The object | the file `<name>.vetl` under `src/dataflows/` in the project's repository | a SageMaker pipeline, defined in JSON (`CreatePipeline`, `StartPipelineExecution`) | a workflow, defined in YAML (`CreateWorkflow`, `StartWorkflowRun`) | an MLflow App, `mlflow-app/<id>`, an environment of the `MLflowApp` blueprint: experiments, runs, models and traces, its artifacts under the project's S3 prefix |

The ML pipeline and the workflow both orchestrate jobs; a Visual ETL flow is one job's program. A flow
therefore fills at most one task of a workflow, while an ML pipeline is either started by one task or
converted into tasks. MLflow orchestrates nothing: its trees are drawn from what code logged, after the
code ran. It records the runs the other graphs execute, and no workflow operator names it, so a task
reaches it through its own code or through a job request that names an app.

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

## MLflow and the graphs

The AI/ML entry *MLflow* opens Compute's *MLflow* tab, which lists the project's MLflow Apps (read
2026-11-21, Stage 17 0.9). *Open* mints a presigned URL (`CreatePresignedMlflowAppUrl`) and opens MLflow's
own UI, where the user guide places experiments, models and traces. `ml-demo-mlflow`, in
`eighth-experimentation`, runs MLflow 3.16.0 since its maintenance of 2026-11-15. A client reaches an app
through the interface endpoint `aws.sagemaker.<region>.mlflow`, the `mlflow` group of `sandbox/egress`,
with the app's ARN as its tracking URI.

The UI's graphs are views of those records (MLflow's pages, read 2026-11-21): an experiment's runs listed,
searched and compared, their metrics charted, child runs grouped under their parent, and a trace's span
tree with each span's latency on a timeline. A trace logged inside a run is shown with that run, and
MLflow 3.16.0 rebuilt the trace explorer and added links between spans. No view is an editor whose graph a
service executes.

### A run logged by a workflow task

MWAA Serverless's operators page lists no operator for MLflow (read 2026-11-16), so a task logs a run with
its own code. `app-ml-train`'s `track` is that task, designed for the `dev` project alone (Stage 17
decision 17, as decision 21 (b) left it). It is a Bash task, so the worker's `python3` imports the MLflow
client and the `sagemaker-mlflow` plugin from the task's archive before the worker's own packages
(`SUP-274`). It reads `last-run.json`, the pointer `evaluate` wrote, and logs one run to the experiment
`app-ml`, named after the training job: the hyperparameters, the validation AUC, four tags (the job, its
model data, its image and the evaluation's URI) and the evaluation file. `publish` runs after it, so the
release candidate is a run that was tracked. The app's ARN reaches the task as the stage variable
`MLFLOW_APP_ARN`, the literal `none` in a target; AWS's `ml/training` example uses an `MLFLOW` connection
instead, whose one property is a `trackingServerArn` (DataZone's service model).

The workflow has never run. The application's lock pins `mlflow-skinny` 3.16.0, the app's version; the
archive built and imported by CPython 3.12 on a build host on 2026-11-16 carried 3.10.1, 15,288,232 bytes
against the service's 250 MB. The import on a worker and the tracking call through the endpoint are Stage
17 verification xxxii.

A training job's container never logs its run. The D13 boundary refuses a training job without network
isolation, so the container reaches no MLflow App, and the run is logged from outside it: by a notebook,
which logs the parameters before `CreateTrainingJob` and reads the metrics back from
`DescribeTrainingJob`, or by tasks, as `evaluate` reads the AUC from the job and `track` logs it.

### A run that SageMaker records

Two SageMaker objects name an MLflow resource in their own API (the service model of the AWS CLI 2.37.12,
read 2026-11-21). `CreateTrainingJob` takes `MlflowConfig`, the resource's ARN with an experiment and a
run name, and `DescribeTrainingJob` returns the run's ids in `MlflowDetails`. `StartPipelineExecution`
takes `MlflowExperimentName`, and `DescribePipelineExecution` returns the execution's `MLflowConfig`, a
resource and an experiment. A training task could pass the first, since `SageMakerTrainingOperator` hands
its `config` to `CreateTrainingJob`; no request in this repository names either. Visual ETL has no such
link: Glue's service model names no MLflow field, and no page read joins a flow to an app.

The ML pipelines visual editor exposes the pipeline's link (the developer guide's *Add integration*, read
2026-11-21). *Integration → MLflow* on its toolbar picks a tracking server or an app and an experiment to
log the pipeline's metrics to, and *Update app and experiment* overrides both for one execution. The page
also says: "A default MLflow application will be created when you enter the pipeline visual editor." It
names neither SageMaker AI Studio nor Unified Studio, does not say whether the service or the step's code
writes the run, and says nothing on isolation. `CreateMlflowApp` carries `AccountDefaultStatus` and
`DefaultDomainIdList`, which make an app the account's or a domain's default, and `ml-demo-mlflow` read no
`AccountDefaultStatus` (Stage 17 1.7); no page read ties the editor's app to them.

Both links are unmeasured here, and both meet the boundary. A run the service writes would track a job
with no task, since the job's container reaches nothing; a run the step's code writes would fail on the
isolation every training job carries. An app the editor creates on entry would be an object nobody chose
([Lesson 17](plan/lessons.md)), in an account whose quota is three MLflow Apps (`ML-7`, Stage 17 1.7):
`ml-demo-mlflow` holds one, and `app-ml-dev`'s designed app would hold a second. Stage 17's step 5.3 enters
the editor.

### The writers of a run

| | A notebook in a space | A workflow task | SageMaker, for a job or an execution |
|---|---|---|---|
| What calls MLflow | the data scientist's code, through the `mlflow` endpoint | the task's code on the worker, through the same endpoint | the service or the step's code, unread |
| What the run holds | what the notebook logs: the parameters, the metrics read back, the model downloaded from the output path | `track`'s run: the hyperparameters, the AUC, the tags, the evaluation file | the pipeline's metrics, by the editor's page |
| Where in this estate | a Sandbox project with an app (Stage 17 1.6 and 3.1) | `app-ml-dev` alone (decision 17) | nowhere designed |
| State | unmeasured | designed, never run | unread |

### MLflow's registry and SageMaker's

MLflow keeps a model registry inside each app; the registry a release crosses is SageMaker AI's, a model
package group per stage ([`sagemaker-ai-ml.md`](plan/runbooks/sagemaker-ai-ml.md) §R). An app can copy one
into the other (the developer guide's page on automatic registration, read 2026-11-21): with the sync on,
`mlflow.register_model()` creates a model package group named after the MLflow model, with a suffix taken
from the app's ARN, and a version in it, whose approval stays a separate SageMaker call. `CreateMlflowApp`
leaves the sync off unless asked, and `ml-demo-mlflow` reads `AutoModelRegistrationDisabled` (Stage 17
1.7); `UpdateMlflowApp`'s documentation gives the opposite default to a call that omits the field (the
same service model), unmeasured. `app-ml`'s `register` task proposes each version in its stage's group,
and `track` logs no model, so the sync has nothing to copy. AWS's `ml/training` example registers through
MLflow, which Stage 17 verification lx reads.

## The workflow in a SageMaker application

```text
EventBridge Scheduler                         when: the cron and the pause
└─ Step Functions, one machine per chain      in what order; waits for each run
   └─ workflow (MWAA Serverless)              what one run executes
      ├─ GlueJobOperator → Glue job (the script a Visual ETL flow generated)
      ├─ SageMakerProcessingOperator, SageMakerTrainingOperator → SageMaker job
      ├─ SageMakerStartPipelineOperator → ML pipeline, a graph SageMaker runs
      └─ PythonOperator, BashOperator → code on the worker
         └─ the MLflow client → MLflow App, in dev alone (app-ml's track)
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

MLflow enters a run as a record that a task's code writes, in `dev` alone. The bundle carries no
experiment and no target holds an app (Stage 17 decision 17): a target's record of a model is its registry
version, with `dev`'s evaluation as its metrics and the training job's name in its metadata, and the score
report of its own run.

Two acts stand outside every workflow: the deploy, which the CLI makes when the GitLab pipeline calls it
(the bundle's code and workflows, the catalog's import), and the approval of a model version, which a
deploy role makes.

In one sentence: in a SageMaker application the workflow controls each run and its tasks start the
services, while the chain starts the workflow in Staging and Production, a member starts it in Sandbox,
and MLflow records the training runs of `dev` and starts nothing.

## What is unmeasured

- A Visual ETL task or schedule in this estate ([`SMUS.md`](SMUS.md), the workflow surface).
- Whether *Create Workflow* offers the import in `awsds-studio`, and what the converted tasks carry.
- An ML pipeline started by a task: who creates each step's job, whether the pipeline's tags reach it, and
  a parameter inside `VpcConfig` and `Tags` (Stage 17 verification lxi).
- The ML pipelines editor's step forms against the D13 boundary (Stage 17 step 5.3).
- A run logged to an MLflow App: from a space (Stage 17 1.6 and 3.1) and from a worker's Bash task
  (verification xxxii).
- The run SageMaker records for a training job's or a pipeline execution's MLflow configuration under the
  D13 boundary, and whether this portal's ML pipelines editor creates an MLflow App on entry, as which
  principal and as whose default (Stage 17 step 5.3 enters the editor).
- A model registered through MLflow reaching the SageMaker Model Registry, and under which group
  (verification lx).

## Where each fact is kept

| Subject | File |
|---|---|
| The workflow surface, Visual ETL's routes and the pipeline import | [`SMUS.md`](SMUS.md), the workflow surface |
| The AI/ML menu's ML pipelines entry, and the workflows of `app-ml` | [`sagemaker-ai-ml.md`](plan/runbooks/sagemaker-ai-ml.md) §E and §W |
| The MLflow entry, the app, its door and its version; `track` and its archive | [`sagemaker-ai-ml.md`](plan/runbooks/sagemaker-ai-ml.md) §E, "MLflow", and §W; [`track.py`](../examples/app-ml/code/app_ml_tasks/track.py) |
| Where a run is tracked, and why never from a job | [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md), decisions 2, 17 and 21, and "Why the experiment is logged from the space, and never from the job" |
| The app's environment, and the portal's MLflow entries | [`AWS_SUPPLEMENT.md`](AWS_SUPPLEMENT.md), `SUP-171` and `SUP-185` |
| What an MLflow App bills | [`PRICING.md`](PRICING.md), the MLflow rows |
| What the provider's SageMaker operators call | [`AWS_SUPPLEMENT.md`](AWS_SUPPLEMENT.md), `SUP-372` |
| Authoring a workflow, and the service's limits | [`serverless-workflows.md`](plan/runbooks/serverless-workflows.md) |
| The chain and a run in Production | [`sagemaker-application.md`](plan/runbooks/sagemaker-application.md) §X |
| Decision 19 and the pipeline increment | [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md), decision 19 and step 9.8 |
| The import as a release, and what it moves | [`upstream-releases.md`](plan/upstream-releases.md), the SMUS table |
| The pages read | [`REFERENCES.md`](REFERENCES.md) |
