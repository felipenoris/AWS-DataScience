# Stage 20 — A dbt task in a SageMaker application, and its lineage in the catalog

| | |
|---|---|
| **Status** | **Written 2026-11-16, nothing run** ([log](../../log/log-stage-20-dbt-lineage.md)): the plan, the user's questions answered from dated vendor pages, OpenLineage's released code and this estate's measurements, and every decision due with its recommendation, none taken. The sitting that wrote it made no AWS call. Pass 1 runs with nothing up; passes 2 and 3 are Sandbox sittings; pass 4 is a warehouse sitting inside Sandbox's free trial, which ends 2026-12-19; pass 5 waits on [Stage 19](stage-19-smus-native-data-product.md) step 4.12 and on decision due 11 |
| **Prerequisites** | [6i](stage-06i-sandbox-orchestration.md) steps 4 and 5, a Python and a Bash task run from a code archive on the worker (2026-10-11), and `awsds-workflows package-task`, which builds that archive ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C). [Stage 19](stage-19-smus-native-data-product.md) pass 1's recipe: a workflow's Glue job writing an Iceberg table into a project database and posting OpenLineage events through Sandbox's `datazone` endpoint (2026-11-10), the graph drawn on the asset's page (2026-11-14). `eighth-experimentation`: the workflows grant (`sandbox/workflows/`), spaces on the house image's version 11 with the CI/CD CLI 1.0.9, the warehouse's admission. `sandbox/egress/`'s `athena`, `glue`, `lakeformation`, `sts` and `datazone` endpoints, and its `mwaa` group for a deploy from a space. For pass 4, the Sandbox warehouse and the project's connection ([5b](stage-05b-redshift-serverless.md), [6h](stage-06h-redshift-connection.md), `EXC-17`). Nothing blocks pass 1 |
| **Consumes** | [D7](../decisions/D07-orchestration.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D40](../decisions/D40-redshift-warehouse.md), [D41](../decisions/D41-sagemaker-application.md); [D12](../decisions/D12-budget-ceiling.md) for the cost |
| **Proves** | — (no `INT-nn` row: the worker's post reaches the domain in Data Governance through the `datazone` endpoint a Glue job's lineage already crosses, and no new wiring between accounts is built). What it does prove: whether a dbt project run as a task of a SageMaker application's workflow reads and writes the project's tables through an engine SageMaker Unified Studio itself uses, and whether the OpenLineage events dbt's wrapper posts land on the graph the portal draws for the assets, beside a Glue job's |

*Read with [`docs/GOVERNANCE.md`](../../GOVERNANCE.md) §Data lineage, [`docs/SMUS.md`](../../SMUS.md)
§The workflow surface and §The catalog surface,
[`runbooks/serverless-workflows.md`](../runbooks/serverless-workflows.md) §C,
[`runbooks/sagemaker-application.md`](../runbooks/sagemaker-application.md) §D,
[Stage 19](stage-19-smus-native-data-product.md) verification v and
[Stage 18](stage-18-staging-deployment-project.md) step 7.1. The vendor sources are the 2026-11-16 rows in
[`docs/REFERENCES.md`](../../REFERENCES.md).*

---

**Objective:** exercise, by measurement, a SageMaker application whose workflow runs dbt for one
transformation step, and make the lineage that step emits visible in the catalog: the task runs a dbt
project against tables of the project's own database, OpenLineage's wrapper turns the run into events,
the events reach the domain through `PostLineageEvent`, and the portal draws them on the assets'
*Lineage* tab in one graph with the events of the Glue job that feeds the model. Write the catalog's
runbook: how an asset is defined, what a data product is, how publication and sharing between projects
run, and how lineage works, with every capture mechanism listed and the dbt case worked through. Decide,
by measurement, whether what an institution built on dbt joins SageMaker Unified Studio's lineage and
catalog, on which engine and in which kind of task, and what each option costs.

## The premises

The user's words of 2026-11-16, which this stage is measured against:

> exercitar uma aplicação SMUS que possui task que utiliza o DBT para uma etapa de transformação de dados
> de pipeline, emitindo lineage de forma que fique visível no DataZone.
>
> Incluir neste estágio elaboração de runbook sobre configurações do catálogo DataZone, contemplando como
> definir assets, produtos de dados, fluxo de publicação e compartilhamento de dados entre projetos, e uma
> seção detalhando a funcionalidade de lineage. Listar em lineage quais são os mecanismos que permitem
> capturar eventos de lineage (será que é restrito a tasks glue (spark)?). Esta seção sobre lineage
> abordaria o caso do DBT, que irá emitir eventos utilizando o padrão OpenLineage.
>
> Contexto deste experimento: na instituição já existem pipelines usando DBT para emitir lineage. Entendo
> que a feature de lineage do DBT é num formato específico do DBT (não sei ao certo). Num cenário em que a
> instituição passa a usar o SMUS, entendo que o DBT se encaixa como um Task de workflow, de forma que o
> DBT deixa de ser o único componente que emite eventos de lineage. Gostaria de explorar o DataZone como
> ferramenta de catálogo de lineage que captura eventos de todas as fontes: sejam eventos de um glue job,
> sejam eventos de pipelines que foram implementados com base no DBT. Como a instituição escolheu o DBT e
> está avaliando o uso do SMUS, uma dúvida é se o que foi feito em DBT consegue "conversar" com o que o
> SMUS oferece como ferramenta de lineage e catálogo de dados.
>
> Entendo que o SMUS não oferece task específica para um job DBT. Neste caso, uma possível solução é subir
> um space com o DBT para executar (SageMaker Processing Operator).

And, a minute later:

> Nesta tarefa, considere, sempre que possível, o caminho padrão proposto pelo que o SMUS oferece, e
> recomendações da AWS.

The premises every item below is read against: **P1** SageMaker Unified Studio's standard path and AWS's
recommendation wherever one exists, each deviation named with its reason; **P2** dbt is one task of a
SageMaker application's workflow, and one emitter of lineage among several; **P3** the catalog is the
lineage register for every source, and an event counts when the portal draws it on an asset's graph, not
when the API accepts it; **P4** where dbt runs is open: the processing job the request names is a
hypothesis, compared with the worker's Python and Bash tasks.

## The vocabulary this stage uses

| Term | Here |
|---|---|
| the worker | the MWAA Serverless container that runs a `PythonOperator` or `BashOperator` task as the project role: 1 vCPU, 3 GiB, Python 3.12, no internet ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §O) |
| the adapter, the engine | dbt's plugin for one SQL engine, and that engine: `dbt-athena` for Athena over the Glue Data Catalog, `dbt-redshift` for the warehouse, `dbt-glue` for Glue interactive sessions. dbt compiles the models to SQL and the engine runs it; dbt itself moves no data |
| the artifacts | the files dbt writes into its `target/` folder: `manifest.json` (every model, source and test with its parents), `run_results.json` (what the last command ran, with times and statuses) and `catalog.json` (the columns the engine reports, written by `dbt docs generate`) |
| the wrapper | `dbt-ol`, OpenLineage's command that runs `dbt` and turns its artifacts into events (the package `openlineage-dbt`) |
| an event | an OpenLineage RunEvent: one run of one job, its state (`START`, `COMPLETE`, `FAIL`), its input and output datasets, each named by a namespace and a name, and facets (the schema, the column lineage, the SQL) |
| the transport | where the OpenLineage client sends an event: `amazon_datazone_api` calls DataZone's `PostLineageEvent` with the caller's credentials |
| a node, its `sourceIdentifier` | what the domain keeps for a dataset, a job and a job run; the `sourceIdentifier` is the string the domain derives from an event's names and the one an asset carries in its `AssetCommonDetailsForm`, which is how a dataset meets an asset |
| the symlink | the OpenLineage dataset facet `symlinks`: a second name for the same dataset, such as the Glue table's for a table Athena wrote |
| the graph | what the portal's *Lineage* tab draws for an asset: the nodes whose identifiers chain to the asset's |

## The plan and the estate against the premises

What each item holds today, with its measurement or page, and what this stage does to it: keep, amend, or
a decision for the user, named by its number in Decisions due. The review was read from `main` `c5e1718`
on 2026-11-16.

### Decisions

| Item | Today | Under the premises |
|---|---|---|
| D7 | workflows run on MWAA Serverless alone; provisioned MWAA is denied at the root (`airflow:CreateEnvironment`, amended 2026-09-05) | **keep**. dbt is a task of a serverless workflow. AWS's guide for dbt on Airflow and Airflow's OpenLineage provider are written for provisioned MWAA: they are read, never built (question 4) |
| D13 | execution roles hold no S3 on the lake's registered prefixes, and a SageMaker job runs network-isolated: `DenySageMakerJobsWithoutNetworkIsolation` in the boundary a project role carries and on the `Workloads` OU | **keep**. It is what turns the processing-job hypothesis into an engine inside the container (decision 2 (c)): a job's container reaches no Athena, Glue, Redshift or DataZone and holds no credentials |
| D17 | people run code in Sandbox alone, in a space; a deployment target has no interactive surface | **keep**. A space is where the application is written and deployed from, never a pipeline's step: no operator starts one, and the portal's notebook task, a training job, is not offered here (6d decision due 14 (b), 2026-10-10) |
| D26 | one domain, in Data Governance, a registry and never a runtime | **keep**. The wrapper posts to that domain through Sandbox's `datazone` endpoint, the door the Glue job's listener uses (`SUP-097`) |
| D28 | the workflow starts whatever runs; on the worker runs *"orchestration code"*, class (2b), *"never a data path"*; a step that reads or writes governed data is an engine's | **keep**. dbt on the worker is class (2b): the client compiles SQL and the engine reads and writes, Athena under Lake Formation's vending or Redshift under its grants. Two of dbt's own paths put the client on the data, and the application takes neither: `dbt seed`, which carries rows through the client, and the Athena adapter's default drop, which deletes a table's files with the client's own S3 calls (0.13) |
| D40 | the warehouse is built by hand; a project writes one schema of the class database `sandbox` through an access role ([`redshift-connection.md`](../runbooks/redshift-connection.md) §J) | **keep**. Pass 4 writes dbt's tables into `lab` through that chain and admits no second project (6h decision 8 stays deferred) |
| D41 | the SageMaker application is the deployable unit: `manifest.yaml`, the workflows in the CI/CD CLI's notation, the code | **keep**. `app-dbt` is an application of that shape with one stage, `dev`; `app-etl`, its `dev` project and its releases are not touched (decision 7) |

### Stages

| Item | Today | Under the premises |
|---|---|---|
| 6f 6.1 | the domain held two lineage nodes, an asset and its listing, written by the publish of 2026-09-13, and no engine's event (read 2026-10-18) | **superseded** by Stage 18 7.1 and Stage 19 verification v; `GOVERNANCE.md` still carries the reading (step 6.2) |
| 6h decision 3 | the project's Redshift connection carries `lineageSync` on, daily at 03:43 UTC, every run `FAILED` with the workgroup down at that hour (`EXC-17`, `SUP-207`); owed to the user | **decision 12**: one successful run read in pass 4, the mechanism AWS automates for Redshift, beside dbt's events for the same statements |
| 6i steps 4 and 5 | a Python and a Bash task ran code from an archive on the worker (2026-10-11) | **keep**, the base of decision 2 (a) |
| Stage 10 verification xix | MWAA Serverless *"emits nothing of its own, and a job posts only what it is configured to post"* (2026-10-25) | **keep**: the reason a dbt task posts its own events |
| Stage 18 7.1, `SUP-097` | a Glue job with no route to the `datazone` endpoint holds its listener about 33 s per attempt and still succeeds; with the endpoint it posts | **keep**; what the same failure costs a dbt task is step 3.3's reading |
| Stage 19 decision 10, verification v | the template's Glue task posts lineage in Sandbox, and the portal draws the S3 input, the job runs, the table and the catalog's edges on the asset's tab (2026-11-14) | **keep**: the graph this stage adds a dbt job to |
| Stage 19 verification ii | a worker's session of the project role called the domain through Sandbox's `datazone` endpoint: the template's `publish` task started a source's run and published a listing (2026-11-10) | **keep**: the door the wrapper's post takes, with `datazone:PostLineageEvent`, which the project role holds through `SageMakerStudioProjectUserRolePolicy` (Stage 18 7.1) and no worker has used |
| Stage 19 decision 17 | a Sandbox project role holds no `datazone:StartDataSourceRun` (revised 2026-11-15); a source imports on its daily schedule or on a member's run in the portal | **keep**: the import of this stage's tables is the schedule's or the user's act (step 2.4) |
| Stage 19's release guard | `scripts/check-catalog-export.py` fails a release whose bundle export holds an asset `product.json` does not name, and the CLI's `bundle` exports whatever the `dev` project owns | **keep**: this stage creates nothing in `app-etl-dev` (decision 7) |

### Documents, runbooks and code

| Item | Today | Under the premises |
|---|---|---|
| `GOVERNANCE.md` §Data lineage, and the feature table's Lineage cell | lineage *"arrives with Stage 6's domain"*, with two limits (it records and does not propagate classification; only instrumented paths appear); the table's cell holds 6f 6.1's two nodes | **amend** at 6.2: the mechanisms, the measured graph, the dbt case in one paragraph, a pointer to the runbook |
| `SMUS.md` §The catalog surface | the catalog's objects and what each measured; lineage in one cell | **amend** at 6.2: the node identifiers and how a dataset meets an asset |
| `serverless-workflows.md` §C | the archive's rules and `package-task`'s recipe | **amend** at 6.2: a dbt archive as a worked case |
| A runbook of the catalog | none: the model is `GOVERNANCE.md`'s, the mechanism `SMUS.md`'s, the procedures are spread over Stages 6f, 18 and 19 | **decision 10**: `docs/plan/runbooks/catalog.md`, written at 1.5 and completed at 6.2 |
| `awsds-workflows` | `package-task` builds a worker's archive from a uv project; `--include` takes files; `lint` checks an application | **keep**; what dbt asks of it is listed for that project (step 6.4), never built here |
| [`upstream-releases.md`](../upstream-releases.md), MWAA Serverless | read 2026-11-13: a workflow's `Environment.Variables`, which the CLI 1.0.9 does not set; operator classes from a code package, unvalidated by the service; the guide's pre-installed set with the Amazon provider at 9.38.0, where a worker measured 9.32.0, its own version owed to a task's reading | **keep**; the probe's list of the worker's packages is that reading (2.2), and step 1.7 adds dbt and OpenLineage to the file |
| `./aws/catalog.py` | reads the catalog's objects (`CT-` rows); no lineage reading | **amend** at 6.1 |

## The user's questions, answered

**1. Is lineage capture restricted to Glue (Spark) tasks?** No. AWS's pages (read 2026-11-16) describe
five ways an event reaches the domain, and Spark on Glue is one engine in two of them:

| Mechanism | Who emits | What AWS's pages say | In this estate |
|---|---|---|---|
| The portal's own tools | SageMaker Unified Studio, with nothing configured | automated for a JupyterLab notebook on a Glue or an EMR Serverless Spark session (*"Spark DataFrames only; remote workflow execution"*: a notebook scheduled as a workflow; an interactive session carries the settings in a `%%configure` cell), a Visual ETL flow in Glue's compatibility mode (*"Not supported"* in fine-grained mode) and the query editor on Amazon Redshift | unmeasured: no reading exists of a notebook's or the query editor's lineage |
| A data source or a connection with *Import data lineage* | DataZone, on the source's run | a Glue source captures the crawlers that fed its tables (*"Lineage is captured only for crawlers which imported less than 250 tables in a crawler run"*); a Redshift source parses the queries in the system tables, daily, leaving out external tables, `COPY` and `UNLOAD`, `MERGE` and `UPDATE`, and datashares; *"For every connection created, lineage is not automatically enabled"* | the Lakehouse and IAM connections carry `glueLineageSyncEnabled` true as their creation default (`SUP-207`) and no project runs a crawler; the Redshift connection's sync has failed on every run read, the workgroup down at its hour (`EXC-17`) |
| An engine the producer configures | the engine's OpenLineage listener | *"AWS Glue jobs in AWS Glue console"*: *"Not automated by default"*, the job is given the domain's id; Glue 5.0 and later carry the libraries *"for Spark DataFrames only. Dynamic DataFrames are not supported."*; EMR Serverless from 7.5, EMR on EC2 from 7.11, EMR on EKS from 7.12 | measured: `app-etl`'s Glue job posts its events (Stage 18 7.1, Stage 19 verification v) |
| Any OpenLineage producer, through `PostLineageEvent` | the producer's own client | *"capture and store lineage events beyond what is available in Amazon SageMaker Unified Studio"*; the `amazon_datazone_api` transport *"was merged into OpenLineage version 1.33.0"*; AWS's blog of 2025-06-24 shows dbt, Airflow and Spark through it | **dbt's door, and this stage's subject.** The same door admits Airflow's OpenLineage provider, which needs provisioned MWAA (D7) |
| The catalog's own acts | DataZone | a node for each asset and each listing (`amazon.datazone.asset/<id>`, `amazon.datazone.listing/<id>`) | measured: the edges *Cataloged*, *Published* and *Access Requested* (Stage 19 verification v) |

What emits nothing: MWAA Serverless itself (Stage 10 verification xix), so a workflow's Python or Bash
task leaves a trace only when its code posts one; a task's own boto3 or pandas code; and, absent from
AWS's support matrix, Athena and a SageMaker processing or training job. The door's limits, from the same
pages: *"Currently, Amazon SageMaker Unified Studio only supports RunEvents"*, *"OpenLineage 1.22.0+
versions are supported"*, *"LineageEvent has a size limit of 300KB"*, and a graph shows only when at
least one of its nodes is an asset.

**2. Is dbt's lineage a format of its own?** Yes: dbt's own lineage is a file in dbt's format, and dbt
Core sends it to no other tool. Every command that parses the project writes `manifest.json`, whose
`parent_map` and `child_map` hold *"the first-order parents of each resource"* and its children (dbt's
page, updated 2026-09-08, which never uses the word lineage), and `dbt docs` draws that file as a graph
of models. Column-level lineage is offered in two places, dbt's hosted platform (*"Requires an Enterprise
or Enterprise+ plan with Catalog access"*) and dbt v2 run locally (*"Requires strict static analysis"*);
the page names dbt Core 1.x nowhere (dbt's page, updated 2026-10-01). OpenLineage is not dbt's format: it
is an open standard of events, with an integration that reads dbt's files. So "dbt emitting lineage" in
an institution is one of three things: the dbt docs site, the hosted platform's catalog, or OpenLineage's
wrapper posting to a lineage server; which one is a fact the user holds (step 1.1). The wrapper is the
one that speaks to DataZone. It runs `dbt`, reads the artifacts when the command ends and emits a `START`
and a `COMPLETE` or `FAIL` event for the command, for each model and for the tests of each model, with the
table's schema, the compiled SQL, the tests' assertions and a column-lineage facet it derives by parsing
the compiled SQL (OpenLineage 1.55.0, the released wheels read 2026-11-16); for dbt v2, which the
wrapper's code calls dbt Core v2, it reads dbt's OpenTelemetry output while the run is live.

**3. Does what was built on dbt "talk" to SageMaker Unified Studio's lineage and catalog?** In three
layers, each with its own answer.

*Execution*: yes by design, unmeasured here. A dbt project is SQL and a client. The client runs as a
workflow task, and the SQL runs on an engine the portal itself uses, Athena over the project's Glue Data
Catalog or Amazon Redshift. A table a model creates in a project database is imported as an asset by that
database's own data source, as `app-etl`'s table was (Stage 19 pass 1).

*Lineage*: yes by AWS's own pages, on one condition this stage measures: the names dbt gives its datasets
have to resolve to the `sourceIdentifier` the assets carry. The domain derives a dataset node's
identifier from the event. For an event that carries Glue's `environment-properties` it reads the
dataset's symlink and builds the table's ARN; for a namespace that begins with `redshift` it builds a
Redshift ARN from the namespace and the name; *"In all other cases, dataset nodes' sourceIdentifier is
populated using <namespace>/<name>"*. `dbt-athena`'s events name a dataset
`awsathena://athena.<region>.amazonaws.com` and `awsdatacatalog.<database>.<table>`, with a symlink that
names the Glue table (namespace `arn:aws:glue:<region>:<account>`, name `table/<database>/<table>`); they
carry no Glue `environment-properties`. Under the page's rule the node is then
`awsathena://athena.<region>.amazonaws.com/awsdatacatalog.<database>.<table>`, not the
`arn:aws:glue:<region>:<account>:table/<database>/<table>` the asset holds, and dbt's nodes would stand
apart from the assets and from the Glue job's nodes. The troubleshooting page's one sentence on the
symlink sits under Glue's own jobs (*"Check if your dataset node has glue arn prefix in the namespace of
the node or in the "symlink" facet of the node."*), and for an event another producer publishes its
remedy is the names: *"If not matching, fix the namespace and name of the dataset in the lineage event
and publish the lineage event again."* The first run therefore posts the events as the wrapper builds
them and reads what the domain does with a symlink no Glue job sent (verification vi). If the graph is
split, OpenLineage's `transform` transport renames the datasets in the client, before the post, to the
namespace `arn:aws:glue:<region>:<account>:table` and the name `<database>/<table>`: the one form the
general rule turns into the ARN, and the form a third party's hand-posted event needed before the portal
drew it (Classmethod's test of 2026-07-12). It is the remedy the page gives, and the kind of change
AWS's own sample makes in a Lambda for its Airflow example (decision 3).
`dbt-redshift`'s names (`redshift://<workgroup>.<account>.<region>.redshift-serverless.amazonaws.com:5439`
and `<database>.<schema>.<table>`) have the form of the page's own example for a serverless workgroup,
whose stated result is the table's ARN; the convention the page quotes beside that example is shorter
(`provider://{cluster_identifier or workgroup}.{region_name}:{port}`), and pass 4 reads what the domain
builds from dbt's.

*Metadata*: partly. A model's description and its columns' reach the asset only if dbt writes them to
the Glue table as comments (`persist_docs`) and the source imports them (verification xvi). A test's
result travels in the event as a `dataQualityAssertions` facet, for which AWS's pages name no place on
the asset. Business names, glossary terms and metadata forms stay the catalog's.

**4. SageMaker Unified Studio has no dbt task: is a space, or a processing job, the way to run it?**
No operator of the service's list runs dbt, and the MWAA Serverless guide's page on custom code names dbt
only as a provider a code package may carry. The ways, compared at decision 2:

- **A Bash task on the worker**, from an archive `package-task` builds. It is the pattern of AWS's MWAA
  guide moved to the serverless worker: the archive plays the guide's virtual environment, and the project
  is copied to a temporary folder before `dbt` runs. A Bash task's `python3` is a process of its own whose
  path starts with the archive, so dbt meets its own dependencies. The limits are the worker's: 1 vCPU,
  3 GiB, 250 MB of code and 3,600 s a task.
- **A Python task** calling dbt's `dbtRunner`. There the worker's pre-installed packages win over the
  archive's copies (measured 2026-10-11), so dbt runs on Airflow's versions of every package both need.
  Airflow 3.0.6's constraint file for Python 3.12 pins `click` 8.2.1, `protobuf` 4.25.8 and `sqlparse`
  0.5.3, each below dbt-core 1.11.17's floor (8.3.0, 6.0 and 0.5.5), and `mmh3` 5.2.0, above `dbt-athena`
  1.11.1's ceiling of 4.2.0; a worker read outside this lab on 2026-10-13 carried that file's SQLAlchemy,
  redshift-connector and PyAthena. The probe's list of the installed distributions reads the rest (2.2).
- **A SageMaker processing job.** In this estate every job is network-isolated (D13), so its container
  reaches no engine and holds no credentials: dbt can only drive an engine inside the container
  (`dbt-duckdb` over staged files), with the lineage relayed afterwards from the saved artifacts and
  naming files no asset carries. In an estate that lets a job reach the VPC the same wrapper runs there,
  at an ML instance's price and start time, for a client that only sends SQL: a processing task here held
  its worker 791 s for a command of one second on the house image (2026-10-11). It is the place for a run
  that outgrows the worker.
- **A Glue job as dbt's runtime**, the form of awslabs' `runner-dbt-aws-airflow`: Airflow operators that
  run dbt and its adapter inside a Glue Spark job, a Glue interactive session or a Glue Python shell job
  (its Glue 6.0 run used `dbt-spark` on the job's own session). A Glue job here has no route to PyPI, so
  every wheel would travel under the application's prefix, and the operators would ride in the worker's
  code package, the next item's form.
- **A provider's operator in the code package**, the form the MWAA Serverless guide names: an operator
  class the worker imports, bound to the worker's Airflow and to its pre-installed versions, which the
  service does not validate ([`upstream-releases.md`](../upstream-releases.md), MWAA Serverless). AWS
  names no such operator for dbt Core. The provider Airflow publishes under dbt's name,
  `apache-airflow-providers-dbt-cloud` (4.4.2 in Airflow 3.0.6's constraint file), starts jobs on dbt's
  hosted platform; an operator that runs dbt Core on the worker is a third party's, unread here.
- **A space** is a person's JupyterLab or Code Editor (D17), not a step: no operator starts one, and the
  portal's notebook task runs a notebook as a SageMaker training job, which the D13 boundary refuses and
  6d decision due 14 (b) took off the menu. A space is where the dbt project is written and tried by hand
  (step 2.6).

AWS's own documented paths for dbt, against this estate (each read 2026-11-16):

| AWS's source | What it shows | Against this estate |
|---|---|---|
| Amazon MWAA user guide, "Using dbt with Amazon MWAA" | provisioned MWAA: a startup script builds a virtual environment with `dbt-core==1.9.4`, `dbt-redshift==1.9.1` and `dbt-postgres==1.9.0`; a `BashOperator` copies the project from `/usr/local/airflow/dags/dbt` to `/tmp` and runs `dbt run --project-dir … --profiles-dir …`; nothing on lineage | provisioned MWAA is denied at the root (D7). The pattern moves to the serverless worker: decision 2 (a) |
| MWAA Serverless user guide, custom code and operators | a code package of at most 250 MB carries what the worker lacks, *"such as the HTTP, Snowflake, or dbt providers"*, installed with `pip … --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:`; *"The pre-installed version takes precedence"*; no dbt operator, no word on OpenLineage | the base of decision 2 (a), (b) and (e); `awsds-workflows package-task` is that recipe for a uv project |
| AWS Big Data Blog, 2025-06-24, lineage from dbt, Airflow and Spark | dbt on Amazon Redshift; `dbt-ol run`, *"just a wrapper on top of the standard `dbt run` command"*, with an HTTP transport to a proxy: an API Gateway, a queue and a Lambda that may transform an event before it posts it to the domain, the post's Airflow example needing the `name` and `namespace` of its inputs and outputs changed; the direct transport is for *"cases where you don't need additional controls on your OpenLineage event stream"* | decision 4 takes the direct transport and decision 3 (b) does the transformation in the client. The blog's engine is pass 4's |
| awslabs `runner-dbt-aws-airflow` 1.0.0 | Airflow operators that run dbt inside a Glue Spark job, a Glue interactive session, a Glue Python shell job, EMR Serverless or an EMR step; a `[lineage]` extra pins OpenLineage 1.50.0, wraps `dbt` in `dbt-ol` and posts with `datazone:PostLineageEvent`; *"Any failure in the OL pipeline is logged but does NOT change dbt's exit code"*; its sample event names a dataset `main.br_nation` under the namespace `dbt_project`, and the page describes no renaming toward an asset's identifier | it names MWAA, not MWAA Serverless; its default variant installs dbt at run time from the internet, which no job here reaches, and its air-gapped variant needs dbt-core on Airflow's scheduler. Decision 2 (d) and decision 5 (a) |
| AWS Big Data Blog, 2022-04-21 and 2023-11-29, `dbt-glue` | dbt on Glue interactive sessions: Spark SQL over the Glue Data Catalog, with Hudi, Delta Lake and Iceberg and Lake Formation; a "trusted" adapter, *"not maintained by dbt Labs"* (dbt's own page: *"Maintained by: Community"*, *"dbt support: Not Supported"*) | decision 1 (c), read at the desk: a session bills per DPU-hour while it lives (`SUP-368`) |
| dbt's pages for Athena and for Iceberg on AWS | `dbt-athena`, maintained by dbt Labs; Iceberg tables through Athena engine version 3, as table and incremental materializations; *"dbt doesn't manage Lake Formation permissions"* | decision 1 (a): Athena is the engine the portal's query editor uses on a project's Lakehouse |

## The application, task by task

`app-dbt` is an application of the template's shape
([`examples/app-etl/`](../../../examples/app-etl/README.md)), written under `examples/app-dbt/` and
deployed by the CI/CD CLI from a space into `eighth-experimentation`, with one stage, `dev` (decision
7). Its workflow has two tasks, so that the graph has two emitters:

| Task | Operator | What it does | Its lineage |
|---|---|---|---|
| `load` | `GlueJobOperator`, the job `app-dbt-{proj.id}`, the template's settings (Glue 6.0, two `G.1X` workers, the project's network connections) | reads `trades.csv` from the application's inbox and writes the Iceberg table `app_dbt.trades` through Spark's catalog | the Spark listener, with the template's settings (Stage 19 decision 10) |
| `transform` | `BashOperator` on the worker, from the archive; `dependencies: [load]`, `retries: 0` | runs `dbt build` through the wrapper: the model `notional_by_desk`, an Iceberg table Athena makes from `trades`, and one `not_null` test | the wrapper's events, through `amazon_datazone_api` |

A second workflow, `app-dbt-probe`, holds one inline Bash task and no archive. It prints what the plan
assumes and nobody read, through `ldd --version` and a `python3` script over the worker's own boto3, since
a worker read outside this lab on 2026-10-13 carried no `aws` client: the worker's glibc and distribution,
the CPUs and the memory the task sees, the installed distributions with their versions, the names (never
the values) of its environment variables, the caller's identity, the project's Athena workgroup with its
engine version, a `SELECT 1` through Athena as the worker's session, and `ListLineageEvents` on the
domain, answered or refused.

```text
examples/app-dbt/
├── manifest.yaml             storage items code, glue, samples and workflows; no content.catalog; the stage dev
├── workflows/app-dbt.yaml    the tasks load and transform
├── workflows/app-dbt-probe.yaml
├── glue/load.py              the CSV to the Iceberg table app_dbt.trades
├── samples/trades.csv
├── src/app_dbt/              the application's pure-Python package
│   ├── lineage.py            the transformer of decision 3 (b)
│   └── project/              the dbt project, as package data: dbt_project.yml, profiles.yml, models/
├── code/run-dbt.sh           what the Bash task calls
├── code/dbt                  a shim that starts dbt's own entry point, dbt.cli.main
├── code/app-dbt.zip          built by package-task, out of git
├── pyproject.toml, uv.lock   dbt-core, dbt-athena and openlineage-dbt, pinned
├── scripts/dev-cli.sh        the template's copy
├── tests/
└── README.md
```

- **The dbt project** declares `app_dbt.trades` as a source and one model, `notional_by_desk`
  (`materialized='table'`, `table_type='iceberg'`, `native_drop=true`), with descriptions,
  `persist_docs` and the test. Its `profiles.yml` holds no value of the account: `type: athena`,
  `database: awsdatacatalog` and `threads: 1` are written in it, and the Region, the schema,
  `work_group`, `s3_staging_dir` and `s3_data_dir` come from `env_var()`. For an Iceberg table the
  adapter writes the table's `location` itself, under `s3_data_dir`, whatever the workgroup enforces
  for query results (0.13). `s3_data_dir` is the product database's own location, which the script
  reads from Glue before it starts dbt, so the model's table sits under the location the portal gave
  the database (2.1); whether Athena writes it there as the worker's session is a reading (iii).
  `native_drop` keeps the worker off the data (D28): with it the adapter drops an Iceberg table by an
  Athena statement and skips its own S3 deletion before a create, where its default deletes the files
  with the client's S3 calls and the table through Glue's API (0.13). If Athena refuses an Iceberg
  table there, the stage stops for the user with the refusal: the adapter's default, a Hive table in
  Parquet whose files the enforced workgroup places, has no drop by statement, and each later run
  would delete the old files from the worker.
- **The task's values travel on the command line**, the way the template's `publish` task takes its
  domain and project: `bash_command` calls `/usr/local/airflow/dags/run-dbt.sh` by its full path with the
  Region (`{domain.region}`) and one option per stage variable: `ACCOUNT_ID`, `PRODUCT_DATABASE`,
  `ATHENA_WORKGROUP`, and the switches the readings turn, `LINEAGE_DOMAIN` (the domain's id),
  `LINEAGE_NAMES` (`as-built` or `glue-arn`), `LINEAGE_ENDPOINT`, `LINEAGE_ATTEMPTS` (exported as
  botocore's `AWS_MAX_ATTEMPTS`) and `DBT_TARGET`. The CLI fills each `{env.VAR}` on every run it starts,
  from the stage's `environment_variables`
  ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D), so a reading that turns a
  switch is a run, not a deploy, and spends none of the workflow's 50 versions. Whether a workflow the CLI
  creates carries the variables the portal injects is unmeasured, and so is a Bash task's `env`. A
  workflow's own `Environment.Variables` exist since 2026-11-04, set at create or update and never by a
  run, and the CLI 1.0.9 sets none and passes none on its update
  ([`upstream-releases.md`](../upstream-releases.md), MWAA Serverless): the command line is the path.
- **`run-dbt.sh`** copies the project to a temporary folder, since dbt writes `target/` and `logs/`
  beside it; exports the Region as `AWS_DEFAULT_REGION`, the only one the transport's client has once
  `endpointOverride` takes its `region`'s place (0.9); reads the product database's location from Glue
  (`GetDatabase`) and exports it for the profile's `s3_data_dir`; writes `openlineage.yml` there and
  names it in `OPENLINEAGE_CONFIG`, the first place the client looks; sets
  `OPENLINEAGE_NAMESPACE=app-dbt` and `DO_NOT_TRACK=1`; puts the archive's folder on `PATH`, because the
  wrapper starts `dbt` as a subprocess and `package-task` removes console scripts, so the shim `dbt`,
  which `--include` stores executable at the archive's root, runs `python3 -m dbt.cli.main`; calls the
  wrapper as `python3 -c 'import sys; from openlineage.dbt import main; sys.exit(main())'`, the package
  having no `__main__`; and prints the peak memory of the run. The script holds no double brace.
- **The lineage configuration** is one file, in one of two forms, which `LINEAGE_NAMES` picks (decision
  3):

  ```yaml
  # the events as the wrapper builds them
  transport:
    type: amazon_datazone_api
    domainId: <domain id>
    region: us-west-2
  ```

  ```yaml
  # the datasets renamed in the client before the post
  transport:
    type: transform
    transformer_class: app_dbt.lineage.GlueTableNames
    transformer_properties:
      region: us-west-2
      account_id: "<account id>"
    transport:
      type: amazon_datazone_api
      domainId: <domain id>
      region: us-west-2
  ```

- **The archive** comes in two builds, because the wrapper imports OpenLineage's SQL parser at module
  level and that parser's only Linux x86_64 wheel is tagged `manylinux_2_28`: **A**, dbt and OpenLineage,
  built with `--platform x86_64-manylinux_2_28`; **B**, dbt alone for `x86_64-manylinux2014`, the fallback
  when the probe reads a glibc below 2.28. On such a worker the wrapper imports in no task, and the stage
  stops for the user with the reading and the ways on: a wheel of the parser built from OpenLineage's
  source for the worker's glibc, or the events relayed with `dbt-ol send-events` from the artifacts B's
  run saves, by a Glue job or by hand from a space. The guide lists `duckdb` 2.0.0 as pre-installed,
  whose Linux wheel for Python 3.12 is tagged `manylinux_2_27` and `manylinux_2_28`: the worker's glibc is
  then 2.27 at least, A needs 2.28, and the probe reads which it is.
- **What it leaves out**: an image (a workflow of a Glue task and a worker task needs none), a
  `content.catalog` block, a publication, and every stage but `dev`. An inventory asset is enough for a
  graph.

## The catalog's runbook, section by section

`docs/plan/runbooks/catalog.md` (decision 10) is the procedure the request asks for: how the catalog is
configured and used, for whoever defines an asset, builds a data product, publishes, shares between
projects or reads a lineage graph. [`GOVERNANCE.md`](../../GOVERNANCE.md) keeps the model and
[`SMUS.md`](../../SMUS.md) the mechanism, and the runbook points at both. Step 1.5 writes it from what is
already measured, and step 6.2 completes §L with this stage's readings.

| Section | What it answers | Written from |
|---|---|---|
| §O The pieces | where the domain lives and what a project is in it; the three catalogs and what each decides; the catalog's objects (asset, revision, listing, data product, data source, subscription, metadata form, glossary, lineage node); who may do what, by project designation and by domain unit | `GOVERNANCE.md` §Catalogs, `SMUS.md` §The catalog surface, 6f step 1 |
| §A Assets | the ways an asset comes to exist: a project database imported by its `DataLake` environment's source, on its daily schedule or a member's run; a source over another Glue database, typed by name; a Redshift source; an asset created by hand (*"a one-time operation"*); a custom asset type through the API. The inventory against the published catalog, a revision, the `sourceIdentifier` an asset carries, what creating a source writes (Lake Formation grants and the discoverability tag), and the order a deletion takes (`SUP-366`) | 6f step 3, Stage 19 pass 1 and its retirement, AWS's pages on a Glue source and on an asset created by hand (read 2026-11-16) |
| §M Business metadata | names, descriptions and the README; the generated names and the switch that keeps the generation off (6f decision 3); glossaries and terms; metadata forms, the project that owns one, and a domain unit's rule that requires one at publishing | 6f steps 4 and 5, Stage 19 decision 4 |
| §P Data products | a product against an asset; building one from assets, publishing and republishing it; its name being the domain's (`SUP-369`); what a subscriber gets from one request; how the CI/CD CLI carries a product between projects | Stage 19 passes 2 to 4 |
| §F The publication flow | from a table to a listing, act by act: the import, the curation, *Publish*, with `publishOnImport` as the short cut; who may publish; the approval switch on a listing; what publishing writes and what it leaves alone (no grant, no LF-Tag); unpublishing | 6f step 11, Stage 19 passes 1 and 2 |
| §S Sharing between projects | a subscription from request to grant: the request, the approval and when it is automatic, the fulfilment for a managed Glue or Redshift asset and the event for an unmanaged one; what lands in the consumer project (the resource link, the grant under the project's context); row and column filters; the Direct Share (`SUP-362`); a subscription across accounts; a revocation and what it leaves; what the catalog does not do (a grant by LF-Tag, a share across Regions, a subscription to a resource link) | 6f step 11, Stage 18 7.2, Stage 19 pass 2 |
| §L Lineage | the capture mechanisms, one by one, with what each needs (question 1's table); an event's anatomy; the node types and the rule that names a node; how a dataset meets an asset; a Glue job's settings; the dbt case from the project to the graph: the wrapper, the transport, the names, the archive, a failed post; reading a graph (the *Lineage* tab, `ListLineageEvents`, `GetLineageNode`, `QueryGraph`) and deleting an event; who may post and who may read; the limits, and how each failure shows | Stage 18 7.1, Stage 19 verification v, this stage's passes 2 to 5 |
| §V The instruments | `./aws/catalog.py`'s rows, the CLI's reads of each object, and the trail each act lands in | 6f, Stage 19, step 6.1 |

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, run only after the user authorizes that action in chat, the other sessions on the laptop told first |
| **[user]** | the portal, a space, the console, and every decision |

## 0. What is already measured

- **0.1 A Python and a Bash task run code from an archive on the worker** (6i steps 4 and 5, 2026-10-11;
  [`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C). The worker extracts one `.zip` of
  at most 250 MB to `/usr/local/airflow/dags`. In a Python task the worker's pre-installed package wins
  over the archive's copy (PyYAML 6.0.1 lost to 6.0.2). A Bash task's `python3` imports the archive's
  copy first, and a script stored executable runs by its full path (both outside this lab, 2026-10-12).
  `awsds-workflows package-task` builds the archive from a uv project and its lock, and removes console
  scripts.
- **0.2 The worker** (§O of the same runbook, 2026-10-11): 1 vCPU and 3 GiB, Python 3.12.14, Airflow
  3.0.6, boto3 1.43.1, no internet and no proxy; the project role in a session named
  `AmazonMWAAServerless`, in the project's private subnets and security group; 0.088 USD per task-hour
  with a one-minute minimum. A task's `execution_timeout` is at most 3,600 s
  ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §W). Its session reaches the domain
  through Sandbox's `datazone` endpoint: the template's `publish` task, a Python task, started a source's
  run and published a listing from it (Stage 19 verification ii, 2026-11-10). The project role holds
  `datazone:PostLineageEvent` through `SageMakerStudioProjectUserRolePolicy` (Stage 18 7.1, 2026-10-19),
  and no worker has posted an event.
- **0.3 A workflow's Glue job writes an Iceberg table into a project database, and its lineage is
  drawn** (Stage 19 pass 1, 2026-11-10 and 2026-11-14). In `eighth-experimentation`, `app-etl`'s Glue 6.0
  job wrote `app_etl.trades_notional` under the `DataLake` environment's conditioned grants and posted its
  events through the `datazone` endpoint: 92 events, all `SUCCESS`. The asset's *Lineage* tab drew the S3
  input, two job runs, the Glue table and the edges *Cataloged*, *Published* and *Access Requested*
  (verification v). The database, its asset and its source were retired on 2026-11-14 in the order
  `SUP-366` forces.
- **0.4 A node's name and how it is read** (`SUP-347`, 2026-11-10): the Glue table's node carries the
  `sourceIdentifier` `arn:aws:glue:us-west-2:<Sandbox>:table/app_etl/trades_notional`. `GetLineageNode`
  refuses that ARN as an identifier and answers to the node's id, to `amazon.datazone.asset/<asset id>`
  and to a job's `<namespace>.<name>`; the node ids are in Data Governance's trail.
- **0.5 An unreachable endpoint and a Glue job** (`SUP-097`, Stage 18 7.1, 2026-10-19): with no
  `datazone` endpoint the listener waits about 33 s per attempt, posts nothing, and the job still
  succeeds; with the endpoint it posted 12 events.
- **0.6 MWAA Serverless emits nothing of its own** (Stage 10 verification xix, 2026-10-25): 44 events in
  the domain, every one from a Glue job that carried the settings, none from nine workflow runs.
- **0.7 The project's doors a dbt client needs exist, and none was read from a worker.** The project's
  Athena workgroup is `workgroup-<project id>-<Tooling environment id>`, its configuration enforced and
  its output under the project's `dev/sys/athena/`. Project creation registers the project's `dev/` with
  Lake Formation and grants `DATA_LOCATION_ACCESS` on it; the portal's *Create database* grants
  `CREATE_TABLE`, `DESCRIBE` and `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`,
  `INSERT` and `SELECT` on its tables. Each grant goes to the account's `IAMPrincipals` under a condition
  on the session's `context.datazone.projectId` ([`SMUS.md`](../../SMUS.md) §S3). A Glue job's session
  carries that attribute (0.3) and so does the query editor's (Stage 19 verification viii, 2026-11-14);
  whether a worker's does is verification ii here. No reading exists of the worker's session through
  Athena, of a table created through Athena as a project role, or of the workgroup's engine version.
- **0.8 dbt and the wrapper against a simulated DataZone** (2026-11-08, a build host outside this estate,
  no AWS call; this stage's log carries the readings). `package-task` (awsds-workflows `d856982`) built
  an archive of dbt-core 1.11.17 and `dbt-athena` 1.11.1 for `manylinux2014`: 22,489,562 bytes,
  72,686,012 unzipped, PyAthena 3.34.0 inside. With `openlineage-dbt` 1.55.0 and
  `--platform x86_64-manylinux_2_28`: 26,141,853 bytes, 82,894,731 unzipped. It refused dbt-core 1.12.6
  (0.10). One `dbt-ol run` over two models made 6 signed `POST /v2/domains/<domain>/lineage/events`, all
  after dbt ended. With the endpoint's port closed the wrapper exited 0 after 58.3 s, about 10 s an
  event. A `dbt-ol build` over a seed, two models and two tests wrote 8 events of 1,913 to 5,527 bytes;
  the seed emitted none and was not an input of the model that read it. `DO_NOT_TRACK=1` silenced dbt's
  telemetry, each send of which waits up to 5 s.
- **0.9 The wrapper's released code** (OpenLineage 1.55.0 of 2026-10-29, the wheels read 2026-11-16).
  It handles `run`, `seed`, `snapshot`, `test`, `build` and `retry`, and passes any other command to
  `dbt` untouched. It starts `dbt` as a subprocess and returns dbt's exit code; a failed post is a warning
  (*"OpenLineage client failed to emit event"*). `send-events` emits from the last run's artifacts
  without running dbt. A dataset is `<database>.<schema>.<table>` under the adapter's namespace:
  `awsathena://athena.<region>.amazonaws.com` for `athena`, `redshift://<host>:<port>` for `redshift`,
  `arn:aws:glue:<region>:<account>` for `glue`. For `athena` alone it adds the Glue symlink, taking the
  account from the profile's `assume_role_arn` or from `sts:GetCallerIdentity`, and leaving the symlink
  out when neither answers. The job namespace is `OPENLINEAGE_NAMESPACE`, `dbt` by default, and a model's
  job is named `<database>.<schema>.<project>.<model>`, with `.build.run` under `dbt build` and
  `.build.test` for its tests. The DataZone transport takes `domainId`, `region` and `endpointOverride`,
  posts RunEvents alone, and *"does not support timeout"*. Its boto3 client is built with botocore's
  defaults, and with `endpointOverride` set it is given no Region, which then comes from the
  environment. The `transform` transport wraps another transport and passes each event through a class
  of the caller's.
- **0.10 What builds today** (PyPI, read 2026-11-16): dbt-core 1.11.17, `dbt-athena` 1.11.1 and
  `dbt-redshift` 1.11.2. dbt-core 1.12.7 requires `dbt-core-experimental-parser` from 2.0.11, which PyPI
  holds only as a source distribution whose build downloads a prebuilt wheel for the building machine's
  platform from dbt's GitHub release, `manylinux_2_28` for Linux x86_64; `package-task` installs wheels
  alone and refuses it.
- **0.11 The catalog's procedures the runbook is written from**: the publication of a governed table and
  a subscription fulfilled (6f step 11, 2026-10-26 and 2026-10-27); a subscription across accounts (Stage
  18 7.2, 2026-10-22); the asset a project's source imports, the data product, the Direct Share
  (`SUP-362`), the subscription inside one account, a data product's name being the domain's (`SUP-369`)
  and the retirement order (`SUP-366`) (Stage 19, 2026-11-10 to 2026-11-16).
- **0.12 The warehouse's door** ([`redshift-connection.md`](../runbooks/redshift-connection.md) §J, 6h
  passes 0 to 2): a project role assumes `awsds-sandbox-warehouse-access-<project>` with the project's id
  as the external id and connects to the workgroup `awsds-sandbox-warehouse`, database `sandbox`, schema
  `lab`, as `IAMR:<project role>`; `5439/tcp` admits the project's security group; `GetCredentials` needs
  the `redshift` endpoint group.
- **0.13 The Athena adapter's released code** (`dbt-athena` 1.11.1 of 2026-09-07, the wheel read
  2026-11-16). `work_group` and `skip_workgroup_check` are profile keys. With `work_group` set, the
  adapter calls `athena:GetWorkGroup` to learn whether the workgroup enforces an output location, unless
  `skip_workgroup_check` is true. For a Hive table under such a workgroup its `CREATE TABLE AS` carries
  no location and Athena places the files, which is what dbt's page describes (`s3_data_naming`
  *"ignores any configured buckets and uses the location configured in the workgroup"*). For an Iceberg
  table it always carries `location`, built from `s3_data_dir` (the model's or the profile's; without
  one, `tables/` under `s3_staging_dir`) and from `s3_data_naming`, `schema_table_unique` by the
  profile's default, and an Iceberg table materialization refuses a naming without `unique` and any
  `external_location`. A first run creates the table in one statement; a later run creates
  `<table>__ha`, renames the table to `<table>__bkp`, renames the new one into place and drops the
  backup. By default the adapter does two things with its own clients, as the caller and outside Lake
  Formation's vending: before a create it lists the new location in S3 and deletes what it finds, and
  it drops a relation *"via Glue and S3 APIs"*, every object under the table's location deleted and
  then `glue:DeleteTable`. The model's `native_drop` (*"Relation drop operations will be performed
  with SQL, not direct Glue API calls"*) turns the drop of an Iceberg table or a view into an Athena
  statement and skips the deletion before a create; a Hive table has no such path. `persist_docs` is
  the adapter's `glue:UpdateTable`.

## To execute

### 1. With nothing up: the application, the lineage configuration, the runbook's first version

No AWS session: the laptop or a cloud session, wherever `uv` reaches PyPI. Step 1.1's facts first, then
decisions due 1 to 7 and 10.

- **1.1 [user] The institution's dbt** (the facts Decisions due opens with): the adapter and engine, the
  dbt line, how lineage is produced and read there today, a project's size and a run's length, and
  whether a job there may reach the network. **[Claude]** reorders decisions 1, 2 and 6 by them and
  records the change in the log.
- **1.2 [Claude] The application** `examples/app-dbt/` (decision 7), as "The application, task by task"
  lays it out: the manifest, the two workflows, the Glue script, the sample, the package with the dbt
  project, the script and the shim, the lock. Its tests are green: `dbt parse` over the project with
  placeholder values, the Glue script over doubles as the template's, and `awsds-workflows lint` in the
  authoring mode. What the lint refuses in an application of one stage goes to 6.4's list.
- **1.3 [Claude] The lineage configuration and the transformer**: `run-dbt.sh` writes either form of
  `openlineage.yml`; `app_dbt/lineage.py` rewrites each Athena dataset of an event, the inputs, the
  outputs and every `columnLineage` input field, to the namespace `arn:aws:glue:<region>:<account>:table`
  and the name `<database>/<table>`. The tests feed the transformer events shaped as the wrapper builds
  them for `athena` and assert the names of both forms; they also run the wrapper over a local engine
  against a simulated DataZone through `endpointOverride`, and assert that the file named by
  `OPENLINEAGE_CONFIG` is the one read and the wrapper's exit code with the endpoint closed.
- **1.4 [Claude] The archives** A and B built with `package-task`, their sizes and unzipped sizes against
  250 MB (iv), every refusal read.
- **1.5 [Claude] The runbook's first version**, `docs/plan/runbooks/catalog.md` (decision 10), as "The
  catalog's runbook, section by section" lays it out: every section, §L without the dbt case's readings,
  from what Stages 6f, 18 and 19 measured and from AWS's pages, the catalog's that `REFERENCES.md` holds
  for those stages and the lineage pages of 2026-11-16. The portal's menus are read again on the day,
  the catalog's items having moved on 2026-09-17, 2026-10-08 and 2026-10-20 (the release notes). A
  statement with no measurement in this estate says so.
- **1.6 [Claude] The desk readings**: `dbt-glue` against Glue interactive sessions and their bill
  (`SUP-368`), with the names the wrapper gives its datasets, the namespace
  `arn:aws:glue:<region>:<account>` and dbt's dotted name, which the page's general rule does not turn
  into a table's ARN either, for decision 1 (c); `dbt-redshift`'s authentication methods against §J's
  chain, for pass 4; awslabs' runner's Glue variants against the lint's rule for a Glue job's modules,
  for decision 2 (d); dbt in a processing job, in this estate's form and where a job reaches the VPC,
  for decision 8.
- **1.7 [Claude] [`upstream-releases.md`](../upstream-releases.md)** gains dbt Core, `dbt-athena`,
  `dbt-redshift` and OpenLineage, with the pins this stage takes and the dates that move them: dbt Core
  1.11's critical support ends 2026-12-18.

### 2. The Sandbox sitting: dbt on a worker, and its events

A Sandbox sitting: `make hub-up`; `make up ENV=sandbox ONLY=egress GROUPS=mwaa`; the application reaches
a space of `eighth-experimentation` as a tar, the archive of 1.4 inside it; the deploy and the runs go
through `scripts/dev-cli.sh` ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D).
Every portal tab is closed before `make down ENV=sandbox`.

- **2.1 [user] Create the database `app_dbt`** in `eighth-experimentation` (*Data → Create database*).
  **[Claude] reads** the new `DataLake` environment, its database and location, its daily source
  (`publishOnImport`, its connection's lineage setting), the grants on the database, and the project's
  Athena workgroup with its engine version and enforced output.
- **2.2 [user] Deploy to `dev` from a space and run `app-dbt-probe`.** **[Claude] reads** the task's log:
  the worker's glibc and distribution, which pick archive A or B (i); the pre-installed packages against
  the guide's table, the reading [`upstream-releases.md`](../upstream-releases.md) owes for the Amazon
  provider; the names of the variables a workflow the CLI made carries; the identity; the
  workgroup's read and the `SELECT 1` as the worker's session, with their entries in Sandbox's trail (ii's
  first half); the `list-lineage-events` read through the endpoint.
- **2.3 [user] Run `app-dbt`.** **[Claude] reads** the Glue job's table and events, the baseline; the
  `transform` task's Athena and Glue calls in the trail and `GetDataAccess` with the session's identity
  (ii); the model's table: the call that created it and the grant that admitted it, its `TableType` and
  `table_type`, whether its files landed under the database's location, as the profile asks (0.13), and
  whether that location is registered with Lake Formation (iii); dbt's own lines: the start, the compile,
  the run and the test times, the peak memory the script prints, the task's duration (iv); the wrapper's
  lines and `PostLineageEvent` in the trail, the events' count and `processingStatus` from
  `list-lineage-events`, each event read back with `get-lineage-event` (v).
- **2.4 [user] Run the database's source in the portal, then open each table's *Lineage* tab.** **[Claude]
  reads** the assets and their `sourceIdentifier`, then `get-lineage-node` on each identifier form, the
  node ids taken from Data Governance's trail (`SUP-347`): whether the model's output node took the
  table's ARN or the Athena name, whether dbt's input is the node the Spark job wrote, what the job and
  the job-run nodes are called, whether the portal draws column lineage, and what the test's assertions
  left (vi, vii); what the assets show of dbt's descriptions (xvi).
- **2.5 [user] Run `app-dbt` again.** **[Claude] reads** what a second `dbt build` does: the adapter
  builds `notional_by_desk__ha`, renames the table aside, renames the new one into place and drops the
  old by an Athena statement (0.13), so the reading is the statements in the trail, which grant admits
  each rename and the drop, what the drop leaves under the old table's location, what the swap does to
  the table's Glue identity, to its grants and to the asset at the source's next run; and what the
  graph shows for a second run: new job runs under the same job, and the nodes' versions (x).
- **2.6 [user] The same project by hand, from the space's terminal**, if the sitting has room: the
  archive unpacked into a folder on `PYTHONPATH`, `dbt debug` and one `dbt run` through the wrapper with
  another `OPENLINEAGE_NAMESPACE`. **[Claude] reads** the session in the trail and how the graph tells a
  person's run from the workflow's: the scientist's development loop.

### 3. The names made to meet, and what a failed post leaves

The same sitting or the next Sandbox one. Steps 3.1 and 3.2 run only if 2.4 reads a split graph.

- **3.1 [user] A run with `LINEAGE_NAMES` set to `glue-arn`** (decision 3 (b)): the same archive, no
  deploy. **[Claude] reads** 2.4's identifiers again (viii), and what became of the first run's nodes.
- **3.2 [Claude] If the renamed form does not link either**, the stage stops for the user with the
  readings: decision 1's next engine is the next rung, never a Glue `environment-properties` facet the
  application makes up.
- **3.3 [user] Runs that fail to post**, each a different failure and a switch of the task: a wrong
  `LINEAGE_DOMAIN` (the service answers with an error); a `LINEAGE_ENDPOINT` naming a closed port (a
  refused connection); one naming the `datazone` endpoint's own name on a port its security group does
  not admit (no answer), with `LINEAGE_ATTEMPTS` at 1, since the transport takes no timeout and
  botocore's defaults, a 60-second connect timeout and five attempts, would hold each event about five
  minutes. **[Claude] reads** the wrapper's log lines, its exit code, the task's state and the time each
  failure added (ix): decision 5's input.
- **3.4 [user] Who may write and read a graph**, from a space of `test-experimentation`, with commands
  Claude hands over: one `post-lineage-event` whose job names `app_dbt.notional_by_desk` as its output,
  and one `get-lineage-node` on `app-dbt`'s job node. **[Claude] reads** whether the domain accepts an
  event about another project's table and draws it on that table's tab, and whether a role outside the
  project reads the job's facets, the compiled SQL among them (xi; `TM-29`'s shape, on lineage); then
  what `delete-lineage-event` removes of the foreign event (xv).

### 4. Redshift: the same models on the warehouse

A warehouse sitting inside a Sandbox one, inside the free trial:
`make up ENV=sandbox GROUPS=redshift,mwaa`, the `mwaa` group for the deploy from a space, shared with
Stage 19's pass 5 when both are owed. Decision due 12 first.

- **4.1 [Claude] The target**: `profiles.yml` gains a `redshift` target (the workgroup's endpoint,
  database `sandbox`, schema `lab`, IAM authentication); the archive gains `dbt-redshift`; the shim
  assumes the project's access role before it starts `dbt`, so the database session is the chain's and the
  wrapper's post stays the project role's. The input is a first model of literal rows, never a seed
  (D28).
- **4.2 [user] Deploy, and run with `DBT_TARGET` set to `redshift`.** **[Claude] reads** the database
  user in dbt's log, the tables in `lab`, `ComputeSeconds`, the events' dataset names, and the nodes'
  `sourceIdentifier` against the form AWS's rule gives,
  `arn:aws:redshift-serverless:<region>:<account>:table/<workgroup>/<database>/<schema>/<table>` (xii).
- **4.3 [user] A Redshift data source over `lab`** on the project's connection, Stage 19 step 5.3's when
  it exists, with *Import data lineage* ticked, and one run. **[Claude] reads** whether a source on a
  connection whose database is `dev` reaches `sandbox`, the assets and their `sourceIdentifier`, whether
  dbt's nodes linked, and the *Lineage* tab (xii).
- **4.4 [Claude] The connection's own capture** (decision 12). The connection's sync is already on, daily
  at 03:43 UTC (`SUP-207`), so a run inside the sitting is had in this order: 4.3's source saved with
  *Import data lineage* ticked and ten minutes waited, the page giving a first pull about 5 minutes after
  enabling; if no run starts, **[Claude⚡]** the schedule moved to the sitting's hour with
  `update-connection`, the connection's whole properties passed back as `get-connection` read them
  (Lesson 60), and moved back after the run. The run is read with `list-job-runs` and `get-job-run` on
  the connection's `lineageJobId`: its status, the queries it processed and the ones it failed, dbt's
  among them, the events it posted, and how the graph shows Redshift's job and dbt's for the same tables
  (xiii). The daily runs failed with the workgroup down at their hour (`SUP-207`), so this run is the
  first to test what the page asks of the connection's credentials, the `sys:operator` role and `SELECT`
  on the tables; the page leaves out of the capture external tables, `COPY` and `UNLOAD`, `MERGE` and
  `UPDATE`, and datashares. dbt builds a table under an intermediate name and renames it into place, so
  the name the capture's node carries is part of the reading. `./aws/warehouse.py` `WH-9` turns to `fail`
  the day a run completes (`EXC-17`), by design, and the sitting records the run it caused. The reading
  goes to 6h decision 3.
- **4.5 [user] Drop the tables** from `lab`, then `make down`.

### 5. Across projects

Waits on Stage 19 step 4.12, `eighth-experimentation`'s subscription to Production's listing, and on
decision due 11. It runs while that subscription is live, before the revocation step 4.12 ends with, the
two sessions agreeing on the order.

- **5.1 [Claude] A model over the subscribed table**: a second source, `trades_notional` through the
  resource link the subscription writes, in `glue_db_blerpkhn9nj7o0` by 6f step 11's reading, and a model
  `notional_by_desk_prod` in `app_dbt`.
- **5.2 [user] Deploy and run.** **[Claude] reads** the worker's read under the subscription's grant,
  with `GetDataAccess` in the trail of the account that vends; the event's input name, which is the
  link's in Sandbox's catalog while the listing's asset carries Production's table ARN; and whether the
  graph joins Production's job, its table, the listing, the subscription and the dbt job. If it does not,
  the transformer resolves a link to its target (`glue:GetTable`'s `TargetTable`) and the run repeats
  (xiv).
- **5.3 [user] As a member of another project**, open the listing's *Lineage* tab. **[Claude] reads**
  what a consumer sees of the producer's jobs and of the dbt job downstream (xiv).

### 6. The checks and the documents

- **6.1 [Claude] [`./aws/catalog.py`](../../../aws/catalog.py)** gains lineage readings as new `CT-`
  rows: a window's events by `processingStatus`, each asset of a project with or without a job upstream,
  and the dataset nodes no asset carries.
- **6.2 [Claude] The documents**: the runbook completed with passes 2 to 5's readings;
  [`GOVERNANCE.md`](../../GOVERNANCE.md) §Data lineage and its feature table's Lineage cell rewritten;
  [`SMUS.md`](../../SMUS.md) §The catalog surface with the node identifiers and the dbt reading;
  [`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C with the dbt archive;
  [`sagemaker-application.md`](../runbooks/sagemaker-application.md) with a pointer.
- **6.3 [Claude] The registers**: an [`AWS_SUPPLEMENT.md`](../../AWS_SUPPLEMENT.md) entry for each
  behaviour the pages do not state; [`AWS_STATE.md`](../../AWS_STATE.md)'s expected readings;
  [`PRICING.md`](../../PRICING.md) and [`cost-model.md`](../cost-model.md) with what the sittings billed
  (xvii); a [`threat-model.md`](../threat-model.md) entry for what an event carries and who reads it: the
  compiled SQL and the schema's names sent to the domain, `PostLineageEvent` open to every project role,
  the graph open to every user of the domain, with 3.4's readings.
- **6.4 [Claude] What dbt asks of `awsds-workflows`**, written for that project and not built here
  (What concerns the other sessions).
- **6.5 [Claude] The answer to the user's question**, in this file's Status and in the runbook's §L: what
  was built on dbt joins the catalog's lineage or does not, on which engine, with which change to the
  events.

### 7. Close

- **7.1 [user] Keep or delete**: the workflows and the Glue job, the database `app_dbt` with its assets
  and source, and the lineage events, by what xv read of `DeleteLineageEvent` (Rollback).
- **7.2 [Claude]** This file's Status, the index rows, the log, the waiting list.

## Verifications

| # | Question | Step |
|---|---|---|
| i | Which glibc, distribution and pre-installed packages does the worker carry, and does archive A (`manylinux_2_28`) import on it? | 2.2 |
| ii | Does Athena admit the worker's session of the project role in the project's workgroup, and does Lake Formation vend to it under the project's context? | 2.2, 2.3 |
| iii | Does a dbt model become an Iceberg table through Athena as the project role: which grant admits it, do its files land under the database's location, where the adapter writes them (0.13), and does Lake Formation's registration cover that location? | 2.3 |
| iv | What does dbt cost on a worker: the archive's size, the start, the run's time and its peak memory, against 250 MB, 1 vCPU, 3 GiB and 3,600 s? | 1.4, 2.3 |
| v | Does the worker's session post through the `datazone` endpoint: how many events, and with which `processingStatus`? | 2.3 |
| vi | With the events as the wrapper builds them, does the model's node take the Glue table's ARN, the symlink honoured, and is dbt's input the node the Spark job wrote? | 2.4 |
| vii | Does the portal draw one graph, from the S3 input through the Glue job, `trades` and the dbt job to `notional_by_desk`, with column lineage, and what does a test's event leave on it? | 2.4 |
| viii | With the datasets renamed in the client, do the nodes link to the assets, and what became of the first run's nodes? | 3.1 |
| ix | What does a refused, a rejected and an unanswered post leave: the wrapper's log, its exit code, the task's state and the time added? | 3.3 |
| x | What does a second run's swap by rename (0.13) do to the table, to its grants, to the asset and to the graph? | 2.5 |
| xi | Does the domain accept, from one project's role, an event about another project's table, and does a role outside a project read that project's job node, its SQL included? | 3.4 |
| xii | On Redshift, do dbt's names give the ARN AWS's rule documents, and does the node link to the asset a Redshift source imports? | 4.2, 4.3 |
| xiii | What does the connection's own capture post for the statements dbt ran, and how does the graph show both? | 4.4 |
| xiv | Across a subscription, does the graph join the producer's job, the listing, the subscription and the consumer's dbt job, and what does a member of another project see of each? | 5.2, 5.3 |
| xv | What does `DeleteLineageEvent` remove: the event, its nodes, the edges the portal draws? | 3.4, 7.1 |
| xvi | Do a model's and its columns' descriptions reach the asset through the Glue table's comments? | 2.4 |
| xvii | What did the sittings bill, by service? | 6.3 |

## Decisions due

Facts only the user holds reorder decisions 1, 2 and 6, and step 1.1 asks for them: which adapter and
engine the institution's dbt projects use; which dbt line (dbt Core 1.x and its minor, dbt v2, or the
hosted platform); how lineage is produced and read there today (dbt's docs site, the platform's catalog,
or the wrapper posting to a lineage server); the size of a project and the length of a run; and whether
a SageMaker job there may reach the network. Each recommendation below is the one that holds without
them.

1. **The engine, and so the adapter.** (a) Athena over the project's Glue Data Catalog, Iceberg tables,
   `dbt-athena`: the engine the portal's query editor uses on a project's Lakehouse, with nothing to keep
   up, billed by the bytes scanned, its adapter maintained by dbt Labs; its dataset names are the ones
   verification vi has to read. (b) Redshift Serverless, `dbt-redshift`: the engine of AWS's own dbt
   lineage example, its names under a rule of AWS's own page; here a metered sitting on a warehouse
   built by hand (D40) that admits one project. (c) Glue interactive sessions, `dbt-glue`: Spark SQL over
   the Glue Data Catalog, the adapter AWS's Professional Services built, community-maintained, a session
   billed per DPU-hour while it lives; the wrapper names its datasets under
   `arn:aws:glue:<region>:<account>` with dbt's dotted name, which the documented rule does not turn into
   the table's ARN either. (d) the institution's adapter, when 1.1 names another.
   **Recommended: (a) first and (b) in pass 4, with (c) read at the desk (1.6)**: (a) and (b) are the
   engines a SageMaker Unified Studio project already carries; (a) costs cents and runs in the sitting
   Stage 19 already knows; (b) is where AWS's example and rule stand. Between them the stage reads the
   hard case and the documented one. 1.1's answer moves the institution's engine to the front.
2. **Where dbt runs.** (a) a Bash task on the worker, from a `package-task` archive: the pattern of AWS's
   MWAA guide on the serverless worker. (b) a Python task calling `dbtRunner`: no subprocess, and
   Airflow's versions of every package dbt shares with it, three of which Airflow 3.0.6's constraint file
   pins below dbt-core 1.11.17's floor (`click`, `protobuf`, `sqlparse`). (c) a SageMaker processing job:
   here an engine inside an isolated container and the lineage relayed afterwards; where a job reaches
   the VPC, the same wrapper on an ML instance. (d) a Glue job as dbt's runtime, awslabs' runner: dbt on
   the job's own Spark session. (e) a provider's operator in the code package. **Recommended: (a)**: dbt
   is a client that sends SQL, which is what D28 lets a worker run; the task costs a fraction of a cent
   and needs no image, and it is the form AWS's own guide gives dbt on Airflow. (c) stays the hypothesis
   decision 8 compares, and the size of a run is the fact that would move it: a project that outgrows
   1 vCPU, 3 GiB or 3,600 s belongs in a job.
3. **How dbt's dataset names meet the assets.** (a) the events as the wrapper builds them, read first;
   (b) OpenLineage's `transform` transport with a transformer of the application, which rewrites each
   Athena dataset, and each `columnLineage` input field, to the form the page's general rule turns into
   the table's ARN; (c) another engine whose names match by rule, decision 1 (b); (d) AWS's proxy sample,
   the transformation in a Lambda behind an API Gateway and a queue. **Recommended: the ladder (a), (b),
   (c)**: (a) costs one run and tells what the domain does with a symlink no Glue job sent, which is what
   an institution's unmodified pipelines would post; (b) is the remedy AWS's troubleshooting page gives
   for a mismatch (*"fix the namespace and name of the dataset in the lineage event"*), as a small class
   in the application that leaves OpenLineage's package as released; (d) adds three services to do what
   (b) does. A Glue `environment-properties` facet added to make the domain read the symlink is not an
   option: it tells the catalog a Glue job ran.
4. **The transport.** (a) `amazon_datazone_api`: the client calls `PostLineageEvent` as the worker's role
   through the `datazone` endpoint; (b) the HTTP transport to AWS's proxy sample; (c) a file transport,
   the events written to S3 and posted by a later task. **Recommended: (a)**: the role holds the action
   and the endpoint exists; it is the path AWS's blog gives a stream that needs no extra control, and the
   one transformation this stage may need runs in the client (decision 3 (b)); and the sample's endpoint
   *"uses a public API endpoint with no authentication or authorization mechanism"*, which no compute
   here reaches.
5. **What a failed post does to the task.** (a) the wrapper's default: dbt's exit code decides the task
   and a failed post is a warning in its log, which is also awslabs' runner's rule; (b) strict: the
   script fails the task when the wrapper logged a failed post; (c) two tasks, each on a worker of its
   own: `transform` runs dbt and saves the artifacts under the application's prefix, `lineage` fetches
   them and runs `dbt-ol send-events`, so a run shows the lineage's state apart from the data's and a
   post is retried without running dbt again. **Recommended: (a) for the exercise, and (a) or (c) chosen
   after 3.3's reading**: a transformation that succeeded is not undone by a catalog that did not answer,
   and (c) is the form for a pipeline whose lineage has to be complete for the run to count as done.
6. **The dbt line.** (a) dbt Core 1.11, pinned by `uv.lock`: the newest line `package-task` builds
   today, under dbt's critical support until 2026-12-18. (b) dbt Core 1.12, in active support until
   2027-07-15: its parser dependency is published as a source distribution whose build downloads a
   `manylinux_2_28` wheel from dbt's GitHub release for the building machine, which `package-task`
   refuses (0.10); the archive would take that wheel fetched by hand and checked against the hashes the
   source distribution carries, and it asks the worker for glibc 2.28, as archive A does. (c) dbt v2: its
   supported-features page names no Athena, the wrapper reads it through OpenTelemetry instead of the
   artifacts, and its runtime is under dbt's own licence agreement (*"If your organization has a strict
   requirement for an Apache 2.0 licensed runtime, install dbt OSS instead"*); read at the desk only if
   it is the institution's line. **Recommended: (a) now and (b) when it builds**: the wrapper's artifact
   path is the one an institution's existing dbt Core pipelines would use, and 1.11's support ends inside
   the stage's own calendar, so (b)'s build is 6.4's first item.
7. **The application, its project and its input.** (a) a new application, `app-dbt`, Sandbox only, in
   `eighth-experimentation`, with a Glue task of its own loading the input; (b) the same in a new project,
   which costs one `sandbox/workflows/` apply for the grant and 6h decision 8 before pass 4; (c) `app-etl`
   extended with a dbt task. **Recommended: (a)**: `app-etl`'s release guard fails a bundle whose export
   holds an asset `product.json` does not name, and its release G is in flight, so nothing of this stage
   lands in `app-etl-dev`; `eighth-experimentation` holds the workflows grant, the warehouse's admission
   and, after Stage 19 step 4.12, the subscription pass 5 reads.
8. **The processing-job hypothesis.** (a) compared at the desk and written into the runbook: what a job
   gives and costs against the worker, in this estate and in one whose jobs reach the network; (b)
   measured in this estate's form: `dbt-duckdb` in an isolated job on the house image, its code input
   built by `awsds-workflows package-job`, the artifacts saved to the job's output and the events relayed
   by a worker task; (c) measured where a job reaches the VPC, outside this estate. **Recommended:
   (a)**: (b) spends a processing job's overhead, 791 s of a worker held for a command of one second on
   the house image (6i, 2026-10-11), to read a relay decision 5 (c) reads on the worker, and its events
   name files no asset carries; (c) is the institution's to run, with this stage's archive and script as
   its starting point.
9. **Promotion.** (a) Sandbox only: one stage, no bundle, no release; (b) the application promoted to
   Staging and Production by the CI/CD CLI, as `app-etl` is. **Recommended: (a)**: whether dbt's lineage
   joins the catalog is answered in Sandbox. What (b) would need is listed for the stage that takes it:
   the worker's archive built and pinned by the pipeline (D28 class (2b)), the task's reach from a
   target's VPC (Athena, Glue, Lake Formation, STS and DataZone, read against each target's `egress/`
   slice), a product database in each deployment project, the lint's promoted mode over a Bash task with
   an archive, and the lineage's account and domain as stage variables.
10. **Where the catalog's runbook lives.** (a) a new `docs/plan/runbooks/catalog.md`, with
    `GOVERNANCE.md` keeping the model and `SMUS.md` the mechanism; (b) sections added to `GOVERNANCE.md`;
    (c) sections added to `SMUS.md`. **Recommended: (a)**: it is a procedure, read by whoever configures
    the catalog, in the runbooks' lettered form, and §L holds what the request asks of lineage: the
    capture mechanisms, an event's anatomy, how a dataset meets an asset, the dbt case, how events are
    read and deleted, what fails and how it shows.
11. **The reading across projects.** (a) after Stage 19 step 4.12, with the subscribed `trades_notional`
    as a model's input; (b) now, with a listing of this stage's own table published from
    `eighth-experimentation` and subscribed from `test-experimentation`; (c) not in this stage.
    **Recommended: (a)**: it reads the graph across a subscription and across accounts with the product
    that exists; (b) adds a listing and a subscription this stage otherwise leaves out, on a project
    Stage 19 is still reading.
12. **The warehouse connection's own lineage capture.** (a) one run read in pass 4's sitting, the
    connection's `lineageSync` left as it stands afterwards; (b) not read. **Recommended: (a)**: it is
    the capture AWS automates for Redshift, the warehouse engine the user named in Stage 19's premises,
    and one run tells 6h decision 3 what the sync is worth beside dbt's events; it is a query on the
    warehouse's meter, inside the trial.

## Cost

Measured rates, `us-west-2`, from [`docs/PRICING.md`](../../PRICING.md):

- A Sandbox sitting: the hub's two `[D]` hosts, `sandbox/egress/`'s interface endpoints at 0.180 USD per
  hour for the set and 0.010 for the `mwaa` group's one, and a space at 0.050 per hour on `ml.t3.medium`
  ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D).
- The workflow: the worker at 0.088 per task-hour with a one-minute minimum, so the dbt task and the
  probe cost a fraction of a cent a run; the Glue job at 0.308 per DPU-hour on two `G.1X` workers, about
  0.01 a run at the 66 s the template's job took on 2026-10-26.
- Athena: 5.00 per TB scanned, kilobytes here; a statement that creates a table bills the bytes it
  scans.
- The catalog: metadata requests at 10.00 per 100,000 with 4,000 a month free per account, storage at
  0.40 per GiB-month with 20 MB free, a source's run in compute units at 1.776 each with 0.2 a month
  free. A run posts events by the ten.
- Pass 4: 1.44 per query-hour at 4 RPU with a 60-second minimum; the trial absorbs it until 2026-12-19.
- Decision 8 (b), if taken: a processing job on `ml.t3.medium` at 0.050 per hour and the worker's
  task-hours while it waits.
- At rest: nothing new. A database, its `DataLake` environment, an asset, a lineage event and a workflow
  are metadata, and the Glue job bills only while it runs. The stage creates no `[E]` resource and, under
  decision 7 (a), applies no Terraform: a refusal read at 2.2 or 2.3 is brought to the user before any
  grant is written.

## Rollback

In this order, each write on the user's word: the two workflows deleted from the *Workflows* page and the
Glue job `app-dbt-<project id>` deleted; the files under the project's `shared/app-dbt/` removed, the
operator archives staying as the versioned bucket keeps them
([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §X); the assets, the source and the
database in the order `SUP-366` forces: each asset deleted, the source deleted, the tables and then the
database dropped from the query editor as the project role, the `DataLake` environment deleted; pass 4's
tables dropped from `lab` and its Redshift source deleted, unless it is Stage 19's; the lineage events
deleted with `DeleteLineageEvent`, if xv reads that it removes what the graph shows. What stays: the
trails' records, the runs' log groups, and whatever xv reads that a deleted event leaves.

## What this stage does not do

- Promote the application: no bundle, no release, no stage but `dev` (decision 9).
- Build an image, or put dbt in the house image.
- Change the D13 boundary or an SCP so that a SageMaker job reaches the network (decision 8).
- Enable provisioned MWAA or Airflow's OpenLineage provider (D7), or use dbt's hosted platform.
- Publish a listing or a data product before pass 5, or assign an LF-Tag: the graph needs an inventory
  asset, and the runbook's publication and sharing sections are written from Stage 19's measurements.
- Touch `app-etl`, `app-etl-dev`, a deployment project or a release.
- Admit a second project to the warehouse (6h decision 8), or switch the connection's `lineageSync` off
  or on (6h decision 3): step 4.4 moves its schedule for one run and moves it back, on the user's word.

## What concerns the other sessions

- **Stage 19**: this stage adds a database, a source, assets, two workflows and a Glue job to
  `eighth-experimentation`, the consumer of its step 4.12 and the project its instruments read. Pass 5
  here waits on that step and runs before the revocation it ends with, and pass 4 shares its pass 5's
  warehouse sitting and its step 5.3's Redshift source.
- **6h**: decision 3 receives 4.4's reading; decision 8 stays deferred.
- **6f's follow-up**: `GOVERNANCE.md` §Data lineage and the feature table's Lineage cell, rewritten at
  6.2.
- **Stage 11**: 6.3's threat-model entry, with 3.4's readings.
- **Stages 6d and 17**: a Sandbox sitting of theirs can carry pass 2 with the `mwaa` group added.
- **The `awsds-workflows` project** (6.4): a way to hand `package-task` a wheel fetched by hand, for a
  dependency published as a download-at-install source distribution, which it refuses today
  (`dbt-core-experimental-parser`, decision 6 (b)); an `--include` that takes a folder, since the dbt
  project travels as package data until then; `WORKER_PROVIDED` against the guide's table of 2026-11-16,
  which lists `duckdb` 2.0.0 and a DuckDB provider and the Amazon provider at 9.38.0 where 9.32.0 was
  measured; a Bash task's `env` and `append_env`, still unmeasured.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Log:
[log-stage-20-dbt-lineage.md](../../log/log-stage-20-dbt-lineage.md)*
