# Stage 20 — A dbt task in a SageMaker application, and its lineage in the catalog

| | |
|---|---|
| **Status** | **Written 2026-11-16; step 1.1's facts and decisions 1 to 7, 10 and 13 taken the same day; the application's draft run against simulated services on 2026-11-17 (0.15, 0.16); nothing run in AWS** ([log](../../log/log-stage-20-dbt-lineage.md)): the plan, the user's questions answered from dated vendor pages, OpenLineage's released code and this estate's measurements, and each decision in the user's words. dbt runs on Athena, in a Bash task on the worker, on dbt Core 1.11, in a new application `app-dbt` in `eighth-experimentation`; Redshift and Glue with Spark are a later revision's, and a run past the worker's hour is compared in the runbook, measured by no pass. Decision 13 takes a processing job out of the network-isolation statement in Sandbox, Staging and Production. No sitting made an AWS call. Pass 1 runs with nothing up; passes 2 and 3 are Sandbox sittings; pass 4 is decision 13's change, a laptop session's tags and applies on the user's word, with the SCP battery; pass 5 waits on [Stage 19](stage-19-smus-native-data-product.md) step 4.12 and on decision due 11 |
| **Prerequisites** | [6i](stage-06i-sandbox-orchestration.md) steps 4 and 5, a Python and a Bash task run from a code archive on the worker (2026-10-11), and `awsds-workflows package-task`, which builds that archive ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C). [Stage 19](stage-19-smus-native-data-product.md) pass 1's recipe: a workflow's Glue job writing an Iceberg table into a project database and posting OpenLineage events through Sandbox's `datazone` endpoint (2026-11-10), the graph drawn on the asset's page (2026-11-14). `eighth-experimentation`: the workflows grant (`sandbox/workflows/`), spaces on the house image's version 11 with the CI/CD CLI 1.0.9. `sandbox/egress/`'s `athena`, `glue`, `lakeformation`, `sts` and `datazone` endpoints, the first four in the endpoint module's core set and the fifth among the slice's extra services, and its `mwaa` group for a deploy from a space. For pass 4, a laptop session as the infrastructure user and the SCP battery ([`scp-battery.md`](../runbooks/scp-battery.md)). Nothing blocks pass 1 |
| **Consumes** | [D7](../decisions/D07-orchestration.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D41](../decisions/D41-sagemaker-application.md); [D12](../decisions/D12-budget-ceiling.md) for the cost |
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
by measurement, whether a dbt project run inside SageMaker Unified Studio joins its lineage and catalog,
with dbt on Athena in a Bash task of the workflow (decisions 1 and 2), and what that costs.

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

Answering step 1.1 the same day, on how lineage is produced and read in the institution (21:48 UTC):

> Sobre este aspecto, considere que não tem nada oficial ou bem estruturado pela instituição. Existem
> apenas propostas de utilizar a ferramenta de lineage do dbt, então estou entendendo que envolve usar o
> dbt-docs. Como o dbt já é utilizado em alguns pipelines na instituição, isso facilitaria adoção. Mas
> esta proposta não considera o fato de que o SMUS, que está sendo implantado na instituição, trata
> lineage via DataZone.
>
> A proposta do estágio 20 é exercitar o caminho em que os pipelines novos desenvolvidos via SMUS emitem
> lineage para o DataZone, e suporte casos de uso de usuários que desejam utilizar DBT como ferramenta
> dentro do SMUS.

And on the network isolation of a processing job in this estate (22:32 UTC):

> Sobre "No laboratório um processing job roda isolado da rede, por uma regra de proteção contra
> vazamento de dados", acho que isso não faz mais sentido. O processing job deveria rodar na VPC do
> projeto. Podemos reabrir este ponto no AWS-DataScience para ajustar?
>
> Um Processing Job deveria ter a mesma capacidade que um cientista de dados teria se ele mesmo abrir um
> space no projeto. A única diferença é que no caso do Processing job este processamento é comandado por
> um workflow.

The premises every item below is read against: **P1** SageMaker Unified Studio's standard path and AWS's
recommendation wherever one exists, each deviation named with its reason; **P2** dbt is one task of a
SageMaker application's workflow, and one emitter of lineage among several; **P3** the catalog is the
lineage register for every source, and an event counts when the portal draws it on an asset's graph, not
when the API accepts it; **P4** the stage serves the pipelines people build in SageMaker Unified Studio
from now on and the people who want dbt as a tool inside it: the institution holds nothing official on
lineage, and its proposals name dbt's own lineage tool, the docs site; **P5** dbt runs in a Bash task on
the worker (decision 2), which holds a run of under an hour, while a typical run of the institution's
can pass one (step 1.1): the forms that carry such a run are compared in the runbook and measured by no
pass; **P6** a processing job reaches what a space of its project reaches, a workflow starting it in a
person's place (decision 13).

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
| D13, and Stage 6a step 3 | execution roles hold no S3 on the lake's registered prefixes (D13), and a SageMaker job runs network-isolated (Stage 6a step 3's statement, which D13 does not name): `DenySageMakerJobsWithoutNetworkIsolation` in the boundary a project role carries, in the persona sets and on the `Workloads` OU | **decision 13**, taken: a processing job leaves that statement in Sandbox, Staging and Production and runs in its project's subnets and security group as the project role; a training, tuning or AutoML job and a model stay under it, and the roles' lack of S3 on the lake's prefixes does not move. Pass 4 makes the change |
| D17 | people run code in Sandbox alone, in a space; a deployment target has no interactive surface | **keep**. A space is where the application is written and deployed from, never a pipeline's step: no operator starts one, and the portal's notebook task, a training job, is not offered here (6d decision due 14 (b), 2026-10-10) |
| D26 | one domain, in Data Governance, a registry and never a runtime | **keep**. The wrapper posts to that domain through Sandbox's `datazone` endpoint, the door the Glue job's listener uses (`SUP-097`) |
| D28 | the workflow starts whatever runs; on the worker runs *"orchestration code"*, class (2b), *"never a data path"*; a step that reads or writes governed data is an engine's | **keep**. dbt on the worker is class (2b): the client compiles SQL and the engine, Athena under Lake Formation's vending, reads and writes. Two of dbt's own paths put the client on the data, and the application takes neither: `dbt seed`, which carries rows through the client, and the Athena adapter's default drop, which deletes a table's files with the client's own S3 calls (0.13) |
| D41 | the SageMaker application is the deployable unit: `manifest.yaml`, the workflows in the CI/CD CLI's notation, the code | **keep**. `app-dbt` is an application of that shape with one stage, `dev`; `app-etl`, its `dev` project and its releases are not touched (decision 7) |

### Stages

| Item | Today | Under the premises |
|---|---|---|
| 6f 6.1 | the domain held two lineage nodes, an asset and its listing, written by the publish of 2026-09-13, and no engine's event (read 2026-10-18) | **superseded** by Stage 18 7.1 and Stage 19 verification v; `GOVERNANCE.md` still carries the reading (step 6.2) |
| 6i steps 4 and 5 | a Python and a Bash task ran code from an archive on the worker (2026-10-11) | **keep**, the base of decision 2 (a) |
| Stage 10 verification xix | MWAA Serverless *"emits nothing of its own, and a job posts only what it is configured to post"* (2026-10-25) | **keep**: the reason a dbt task posts its own events |
| Stage 18 7.1, `SUP-097` | a Glue job with no route to the `datazone` endpoint holds its listener about 33 s per attempt and still succeeds; with the endpoint it posts | **keep**; what the same failure costs a dbt task is step 3.3's reading |
| Stage 19 decision 10, verification v | the template's Glue task posts lineage in Sandbox, and the portal draws the S3 input, the job runs, the table and the catalog's edges on the asset's tab (2026-11-14) | **keep**: the graph this stage adds a dbt job to |
| Stage 19 verification ii | a worker's session of the project role called the domain through Sandbox's `datazone` endpoint: the template's `publish` task started a source's run and published a listing (2026-11-10) | **keep**: the door the wrapper's post takes, with `datazone:PostLineageEvent`, which the project role holds through `SageMakerStudioProjectUserRolePolicy` (Stage 18 7.1) and no worker has used |
| Stage 19 decision 17 | a Sandbox project role holds no `datazone:StartDataSourceRun` (revised 2026-11-15); a source imports on its daily schedule or on a member's run in the portal | **keep**: the import of this stage's tables is the schedule's or the user's act (step 2.4) |
| Stage 19's release guard | `examples/app-etl/scripts/check-catalog-export.py` fails a release whose bundle export holds an asset `product.json` does not name, and the CLI's `bundle` exports whatever the `dev` project owns | **keep**: this stage creates nothing in `app-etl-dev` (decision 7) |

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
wrapper posting to a lineage server; the user's institution holds proposals for the first and nothing
official (step 1.1). The wrapper is the one that speaks to DataZone. It runs `dbt`, reads the artifacts
when the command ends and emits a `START` and a `COMPLETE` or `FAIL` event for the command, for each
model and for the tests of each model, with the table's schema, the compiled SQL, the tests' assertions
and a column-lineage facet it derives by parsing the compiled SQL (OpenLineage 1.55.0, the released
wheels read 2026-11-16); for dbt v2, which the wrapper's code calls dbt Core v2, it reads dbt's
OpenTelemetry output while the run is live.

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
(`provider://{cluster_identifier or workgroup}.{region_name}:{port}`); no pass here reads what the
domain builds from dbt's, Redshift being a later revision's (decision 1).

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
  3 GiB, 250 MB of code and 3,600 s a task. It is the form this stage runs (decision 2).
- **A Python task** calling dbt's `dbtRunner`. There the worker's pre-installed packages win over the
  archive's copies (measured 2026-10-11), so dbt runs on Airflow's versions of every package both need.
  Airflow 3.0.6's constraint file for Python 3.12 pins `click` 8.2.1, `protobuf` 4.25.8 and `sqlparse`
  0.5.3, each below the floor dbt-core 1.11.16 and 1.11.17 share (8.3.0, 6.0 and 0.5.5), and `mmh3`
  5.2.0, above `dbt-athena` 1.11.1's ceiling of 4.2.0; a worker read outside this lab on 2026-10-13
  carried that file's SQLAlchemy, redshift-connector and PyAthena. The probe's list of the installed
  distributions reads the rest (2.2).
- **A SageMaker processing job.** Until pass 4 every job here is network-isolated, so its container
  reaches no engine and holds no credentials. With decision 13 applied, a processing job runs in its
  project's subnets and security group as the project role, and the same wrapper runs there, at an ML
  instance's price and start time, for a client that only sends SQL: a processing task here held its
  worker 791 s for a command of one second on the house image (2026-10-11). It is the place for a run
  that outgrows the worker, with one constraint: the task that waits on the job is a task, capped at
  3,600 s like every other, so the job is started with `wait_for_completion: false` and a
  `SageMakerProcessingSensor` task waits for it, each try ended by the task's `execution_timeout` and
  retried up to three times, about four hours a waiting task (0.12). Nothing has measured that form on
  the service, and no pass here does (decision 2).
- **Several Bash tasks**, each running one part of the project (`dbt build --select`), a later task's
  models reading the tables an earlier one built: no job, for a project whose parts each fit the hour.
  It does nothing for a single model that passes it, and it moves the project's order from dbt's graph
  into the workflow.
- **A Glue job as dbt's runtime**, the form of awslabs' `runner-dbt-aws-airflow`: Airflow operators that
  run dbt and its adapter inside a Glue Spark job, a Glue interactive session or a Glue Python shell job
  (its Glue 6.0 run used `dbt-spark` on the job's own session). A Glue job here has no route to PyPI, so
  every wheel would travel under the application's prefix, and the operators would ride in the worker's
  code package, the next item's form. A Glue job already runs in the project's network, and
  `GlueJobOperator`'s `resume_glue_job_on_retry` makes a retried try find the run it started instead of
  starting another (0.12).
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
| MWAA Serverless user guide, custom code and operators | a code package of at most 250 MB carries what the worker lacks, *"such as the HTTP, Snowflake, or dbt providers"*, installed with `pip … --platform manylinux2014_x86_64 --python-version 3.12 --only-binary=:all:`; *"The pre-installed version takes precedence"*; no dbt operator, no word on OpenLineage | the base of decision 2 (a) and of the forms it does not offer, a Python task calling `dbtRunner` and a provider's operator in the package; `awsds-workflows package-task` is that recipe for a uv project |
| AWS Big Data Blog, 2025-06-24, lineage from dbt, Airflow and Spark | dbt on Amazon Redshift; `dbt-ol run`, *"just a wrapper on top of the standard `dbt run` command"*, with an HTTP transport to a proxy: an API Gateway, a queue and a Lambda that may transform an event before it posts it to the domain, the post's Airflow example needing the `name` and `namespace` of its inputs and outputs changed; the direct transport is for *"cases where you don't need additional controls on your OpenLineage event stream"* | decision 4 takes the direct transport and decision 3 (b) does the transformation in the client. The blog's engine, Redshift, is a later revision's (decision 1) |
| awslabs `runner-dbt-aws-airflow` 1.0.0 | Airflow operators that run dbt inside a Glue Spark job, a Glue interactive session, a Glue Python shell job, EMR Serverless or an EMR step; a `[lineage]` extra pins OpenLineage 1.50.0, wraps `dbt` in `dbt-ol` and posts with `datazone:PostLineageEvent`; *"Any failure in the OL pipeline is logged but does NOT change dbt's exit code"*; its sample event names a dataset `main.br_nation` under the namespace `dbt_project`, and the page describes no renaming toward an asset's identifier | it names MWAA, not MWAA Serverless; its default variant installs dbt at run time from the internet, which no job here reaches, and its air-gapped variant needs dbt-core on Airflow's scheduler. Decision 2 (d) and decision 5 (a) |
| AWS Big Data Blog, 2022-04-21 and 2023-11-29, `dbt-glue` | dbt on Glue interactive sessions: Spark SQL over the Glue Data Catalog, with Hudi, Delta Lake and Iceberg and Lake Formation; a "trusted" adapter, *"not maintained by dbt Labs"* (dbt's own page: *"Maintained by: Community"*, *"dbt support: Not Supported"*) | a later revision's (decision 1): a session bills per DPU-hour while it lives (`SUP-368`), and `dbt-glue` has no release for dbt Core 1.11 (0.10) |
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
assumes and nobody read, through shell commands and a `python3` script over the worker's own boto3, since
a worker read outside this lab on 2026-10-13 carried no `aws` client: the worker's glibc and
distribution; which of the tools `run-dbt.sh` calls its `PATH` holds; the task's folder and its mounts,
and whether a script written in that folder and in a `mktemp` folder runs; the CPUs and the memory the
task sees; `sys.path`; the installed distributions with their versions; the names (never the values) of
its environment variables; the caller's identity; the project's Athena workgroup with its engine version
and enforced output; the product database as Glue returns it; a `SELECT 1` and a count of `trades`
through Athena as the worker's session; and `ListLineageEvents` on the domain. Each call is tried once,
with a 10-second connect timeout, and prints its answer or one line `REFUSED` with the error's type and
text, so a door with no path costs seconds and the task ends `SUCCESS` whatever a call answered.

```text
examples/app-dbt/
├── manifest.yaml             storage items code, glue, samples and workflows; no content.catalog; the stage dev
├── workflows/app-dbt.yaml    the tasks load and transform
├── workflows/app-dbt-probe.yaml
├── glue/load.py              the CSV to the Iceberg table app_dbt.trades
├── samples/trades.csv
├── src/app_dbt/              the application's pure-Python package
│   ├── lineage.py            the transformer of decision 3 (b)
│   ├── bin/dbt               dbt Core's console script, stored executable
│   └── project/              the dbt project, as package data: dbt_project.yml, profiles.yml, models/
├── code/run-dbt.sh           what the Bash task calls, stored executable
├── code/app-dbt.zip          built by package-task, out of git (.gitignore, as the template's)
├── .gitignore                code/*.zip, as examples/app-etl/.gitignore
├── pyproject.toml, uv.lock   dbt-core, dbt-athena and openlineage-dbt, by range and by lock
├── scripts/dev-cli.sh        the template's copy, a pair ./scripts/check-copies.py gains
├── tests/
└── README.md
```

- **The manifest** names the storage items `code` (the archive alone), `glue`, `samples` and `workflows`,
  each `include` a file or a folder and never a glob; the workflows `app-dbt`, with
  `code: code/app-dbt.zip`, and `app-dbt-probe`, with none, both on `default.workflow_serverless`; and
  one stage, `dev`, whose bootstrap creates both. The stage's `environment_variables` are what the
  workflows read as `{env.NAME}`: `SUBNET_AZ1` and `SUBNET_AZ2` for the Glue job's connections,
  `ACCOUNT_ID`, `PRODUCT_DATABASE` (the literal `app_dbt`), `ATHENA_WORKGROUP`, and the switches the
  readings turn, `LINEAGE_DOMAIN`, `LINEAGE_NAMES`, `LINEAGE_ENDPOINT` and `LINEAGE_ATTEMPTS`. Every one
  but the literal comes from the shell as `${NAME}`, and the CLI refuses a manifest whose variable is
  unset or empty ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D), so a switch at
  rest holds a word: `default` for the endpoint and for the attempts.
- **The dbt project** declares `app_dbt.trades` as a source and one model, `notional_by_desk`
  (`materialized='table'`, `table_type='iceberg'`, `native_drop=true`), with descriptions, `persist_docs`
  and the test. Its `profiles.yml` holds no value of the account: `type: athena`,
  `database: awsdatacatalog` and `threads: 1` are written in it, and the Region, the schema, `work_group`
  and `s3_data_dir` come from `env_var()`. It names no `s3_staging_dir`, which the adapter does not
  require: no statement then carries a `ResultConfiguration`, and the workgroup's enforced output places
  the query results (0.16). For an Iceberg table the adapter writes the table's `location` itself,
  `<s3_data_dir><schema>/<table>/<uuid>`, whatever the workgroup enforces for query results (0.13).
  `s3_data_dir` is the product database's own location, which the script reads from Glue before it starts
  dbt. The portal gives every database of a project one location, the project's catalogs folder,
  `s3://awsds-sandbox-smus-projects/<domain id>/<project id>/dev/data/catalogs/` (0.7), so the model's
  files land under `dev/data/catalogs/app_dbt/notional_by_desk/<uuid>/` and, by Stage 19's reading of a
  Glue job's table, the Glue job's under `dev/data/catalogs/trades/`, a folder named by the table alone.
  Both sit inside the `dev/` that project creation registers with Lake Formation; whether Athena writes
  there as the worker's session is a reading (iii). `native_drop` keeps the worker off the data (D28):
  with it the adapter drops an Iceberg table by an Athena statement and skips its own S3 deletion before
  a create, where its default deletes the files with the client's S3 calls and the table through Glue's
  API (0.13). If Athena refuses an Iceberg table there, the stage stops for the user with the refusal:
  the adapter's default, a Hive table in Parquet whose files the enforced workgroup places, has no drop
  by statement, and each later run would delete the old files from the worker.
- **The task's values travel on the command line**, the way the template's `publish` task takes its
  domain and project:

  ```yaml
  bash_command: "bash /usr/local/airflow/dags/run-dbt.sh --region '{domain.region}' --account '{env.ACCOUNT_ID}' --database '{env.PRODUCT_DATABASE}' --workgroup '{env.ATHENA_WORKGROUP}' --domain '{env.LINEAGE_DOMAIN}' --names '{env.LINEAGE_NAMES}' --endpoint '{env.LINEAGE_ENDPOINT}' --attempts '{env.LINEAGE_ATTEMPTS}'"
  ```

  The command starts `bash` on the script by its full path, so the mode the worker's extraction leaves on
  the file plays no part, and the options follow, each value in single quotes: the command never ends in
  `.sh`, which the operator reads as the name of a template file (0.1). `LINEAGE_DOMAIN` is the domain's
  id, `LINEAGE_NAMES` is `as-built` or `glue-arn`, `LINEAGE_ENDPOINT` a URL or `default`, and
  `LINEAGE_ATTEMPTS` a number, exported as botocore's `AWS_MAX_ATTEMPTS`, or `default`. The CLI fills
  each `{env.VAR}` on every run it starts, from the stage's `environment_variables` as the shell holds
  them at that run ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D), so a reading
  that turns a switch is an `export` and a run, not a deploy, and spends none of the workflow's 50
  versions. In a workflow made in the portal, a Bash task read the seven variables the portal injects
  unset or empty in its environment (6i's log, 2026-10-11); whether a workflow the CLI creates carries
  them is unmeasured, and so is a Bash task's `env`. A workflow's own `Environment.Variables` exist since
  2026-11-04, set at create or update and never by a run, and the CLI 1.0.9 sets none and passes none on
  its update ([`upstream-releases.md`](../upstream-releases.md), MWAA Serverless): the command line is
  the path.
- **`run-dbt.sh`** takes those options and, after `--`, the dbt command, `build` when none is given, and
  stops with exit 2 on an option it does not know or a value left out. It copies the project to a
  temporary folder, since dbt writes `target/` and `logs/` beside it; puts the folder of the `dbt`
  console script first on `PATH` (the next item); exports the Region as `AWS_DEFAULT_REGION`, the only
  one the transport's client has once `endpointOverride` takes its `region`'s place (0.9),
  `DO_NOT_TRACK=1`, `AWS_MAX_ATTEMPTS` when `--attempts` names a number, and `OPENLINEAGE_NAMESPACE`,
  `app-dbt` unless the caller's `APP_DBT_NAMESPACE` names another (2.6); reads the product database's
  location from Glue (`GetDatabase`), exits 3 when it has none, and exports it for the profile's
  `s3_data_dir`; writes `openlineage.yml` in the temporary folder and names it in `OPENLINEAGE_CONFIG`,
  the first place the client looks; and calls the wrapper as
  `python3 -c 'import sys; from openlineage.dbt import main; sys.exit(main())'`, the package having no
  `__main__`. It prints the values it ran with, where `dbt` ran from, whether its own mode came through
  the extraction, the interpreter, the peak memory of the wrapper and of the dbt it started, and the
  wrapper's exit code, which is dbt's and becomes the task's. The script is never rendered as a template
  and holds no double brace.
- **The `dbt` the wrapper starts** is a file of the application. The wrapper runs `dbt` by name as a
  subprocess, and `package-task` removes console scripts, so the package carries dbt Core's own,
  `src/app_dbt/bin/dbt`, stored executable:

  ```python
  #!/usr/bin/env python3
  import sys

  from dbt.cli.main import cli

  if __name__ == "__main__":
      sys.exit(cli())
  ```

  It travels as package data because dbt-core installs a folder `dbt/` at the archive's root, where
  `--include` would put a file of that name, and `package-task` refuses the pair (0.15). Its first line
  matters: the wrapper reads the engine from a Python script without starting it, and runs
  `dbt --version` on a shell script, which asks PyPI for the newest release (0.16). `run-dbt.sh` uses the
  file where it sits when its mode came through the worker's extraction, as a script at an archive's root
  did outside this lab (0.1), and otherwise a copy it marks executable in the temporary folder; its first
  line of output says which.
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

  Either form's `amazon_datazone_api` block gains `endpointOverride` when `LINEAGE_ENDPOINT` is not
  `default`.
- **The archive** is one build, `package-task` with `--platform x86_64-manylinux_2_28` and
  `--include code/run-dbt.sh`: 26 MB, 83 MB unzipped, 5,102 entries (0.15), against the service's 250 MB
  for each size. The wrapper imports OpenLineage's SQL parser at module level, and that parser's only
  Linux x86_64 wheel is tagged `manylinux_2_28`: of the archive's ten compiled modules it alone asks for
  glibc 2.28, the others for 2.16 at most. The guide lists `duckdb` 2.0.0 as pre-installed, whose Linux
  wheel for Python 3.12 is tagged `manylinux_2_27` and `manylinux_2_28`: a worker that carries the
  guide's set has glibc 2.27 at least, the one read on 2026-10-13 carried no `duckdb`, and the probe
  reads the glibc itself (2.2). On a worker below 2.28 the wrapper imports in no task, and the stage
  stops for the user with the reading and the ways on: a wheel of the parser built from OpenLineage's
  source for the worker's glibc; or dbt alone on the worker, from a `manylinux2014` build (22.5 MB, 0.8),
  with the events relayed by `dbt-ol send-events` from the artifacts that run saves, by a Glue job or by
  hand from a space. `pyproject.toml` names the three packages by range (`dbt-core>=1.11,<1.12`,
  `dbt-athena>=1.11,<1.12`, `openlineage-dbt>=1.55,<2`) and carries the template's `exclude-newer`, an
  instant two weeks before the lock is cut, so `uv.lock` holds the newest releases older than that: under
  an instant of 2026-11-03, dbt-core 1.11.16, since 1.11.17 is of 2026-11-06 (0.15). The archive leaves
  out what the worker pre-installs, boto3 and botocore among them, so the adapter and the transport call
  AWS with the worker's boto3 1.43.1.
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
| §L Lineage | the capture mechanisms, one by one, with what each needs (question 1's table); an event's anatomy; the node types and the rule that names a node; how a dataset meets an asset; a Glue job's settings; the dbt case from the project to the graph: the wrapper, the transport, the names, the archive, a failed post, and the forms that carry a run past the worker's hour; dbt's docs site against the catalog's graph; reading a graph (the *Lineage* tab, `ListLineageEvents`, `GetLineageNode`, `QueryGraph`) and deleting an event; who may post and who may read; the limits, and how each failure shows | Stage 18 7.1, Stage 19 verification v, this stage's passes 2, 3 and 5 |
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
  at most 250 MB, unzipped too, to `/usr/local/airflow/dags`. In a Python task the worker's pre-installed
  package wins over the archive's copy (PyYAML 6.0.1 lost to 6.0.2). A Bash task's `python3` imports the
  archive's copy first, and a script stored executable runs by its full path (both outside this lab,
  2026-10-12). In this lab a Bash task started in a folder of its own, `/var/tmp/airflowtmp…`, with
  `PYTHONPATH` naming `/usr/local/airflow/dags` ahead of the worker's own packages and `AWS_REGION` and
  `AWS_DEFAULT_REGION` set, its `python3` the worker's 3.12.14; and the operator read a command that was
  a script's name as a template file, which it rendered into a temporary file and ran with `bash` (6i's
  log, 2026-10-11). `awsds-workflows package-task` builds the archive from a uv project and its lock, and
  removes console scripts.
- **0.2 The worker** (§O of the same runbook, 2026-10-11): 1 vCPU and 3 GiB, Python 3.12.14, Airflow
  3.0.6, boto3 1.43.1, no internet and no proxy; the project role in a session named
  `AmazonMWAAServerless`, in the project's private subnets and security group; 0.088 USD per task-hour
  with a one-minute minimum. A task's `execution_timeout` is at most 3,600 s
  ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §W), whatever the task, the one
  that waits on a job included (0.12). Its session reaches the domain through Sandbox's `datazone`
  endpoint: the template's `publish` task, a Python task, started a source's run and published a listing
  from it (Stage 19 verification ii, 2026-11-10). The project role holds `datazone:PostLineageEvent`
  through `SageMakerStudioProjectUserRolePolicy` (Stage 18 7.1, 2026-10-19), and no worker has posted an
  event. No reading exists of a worker's glibc or distribution. A worker read outside this lab on
  2026-10-13 showed its task two CPUs and 4.9 GB of memory with no cgroup limit below them, a `/tmp` of
  9.7 GB on a device of its own, no `aws`, `tar` or `unzip`, and 164 distributions, PyAthena 3.17.1 among
  them and no `duckdb`, which is why the probe reads the CPUs the task may use and the memory limit
  beside the totals.
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
  Athena workgroup is `workgroup-<project id>-<Tooling environment id>`,
  `workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c` in `eighth-experimentation`, its configuration enforced and
  its output under the project's `dev/sys/athena/`; a query from the portal's editor ran in it on Athena
  engine version 3 on 2026-10-26 (6f step 11.10). Project creation registers the project's `dev/` with
  Lake Formation and grants `DATA_LOCATION_ACCESS` on it. The portal's *Create database* deploys a
  `DataLake` environment with a daily source; gives the database the project's catalogs folder as its
  location, `s3://awsds-sandbox-smus-projects/<domain id>/<project id>/dev/data/catalogs/`, the one
  location every database of the project shares (Stage 19's log, 2026-10-28); and grants `CREATE_TABLE`,
  `DESCRIBE` and `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT`
  on its tables. Each grant goes to the account's `IAMPrincipals` under a condition on the session's
  `context.datazone.projectId` ([`SMUS.md`](../../SMUS.md) §S3). A Glue job's session carries that
  attribute (0.3) and so does the query editor's (Stage 19 verification viii, 2026-11-14); whether a
  worker's does is verification ii here. A Glue job's Iceberg table landed at the database's location
  followed by the table's name, whatever warehouse its settings named (Stage 19's log, 2026-11-10), and a
  `DROP TABLE` of that table through Athena, from the editor as the project role, left its folder with no
  current object, its versions noncurrent behind delete markers (2026-11-14). The network path exists:
  `athena`, `glue`, `lakeformation` and `sts` are in the endpoint module's core set and `datazone` among
  `sandbox/egress/`'s extra services, and the dbt client makes no S3 call (0.16). `sandbox/workflows/`'s
  statement `GetAGlueJobNoProjectHolds` covers the job `app-dbt-<project id>` before it exists. The
  project's inventory already holds an asset named `trades`, its source's import of the resource link a
  subscription wrote in `glue_db_blerpkhn9nj7o0` (`SUP-197`), so this stage's assets are told from it by
  their external identifier, the table's ARN with the project's id suffixed (`SUP-343`). No reading
  exists of the worker's session through Athena, or of an Iceberg table created through Athena as a
  project role.
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
  alone and refuses it. `dbt-glue` has no release for dbt Core 1.11: 1.10.19 of 2026-02-18 asks
  `dbt-core~=1.10.19`, and the next, 1.12.3 of 2026-08-27 and 1.12.4 of 2026-09-10, ask the 1.12 line;
  `dbt-spark` 1.11.0 of 2026-07-16 admits dbt-core from 1.8, its `session` extra asking `pyspark`.
- **0.11 The catalog's procedures the runbook is written from**: the publication of a governed table and
  a subscription fulfilled (6f step 11, 2026-10-26 and 2026-10-27); a subscription across accounts (Stage
  18 7.2, 2026-10-22); the asset a project's source imports, the data product, the Direct Share
  (`SUP-362`), the subscription inside one account, a data product's name being the domain's (`SUP-369`)
  and the retirement order (`SUP-366`) (Stage 19, 2026-11-10 to 2026-11-16).
- **0.12 The task cap, and a job past it** (AWS's MWAA Serverless pages in their Markdown form and
  Airflow's released wheels, read 2026-11-16; nothing measured on the service). The quotas page gives a
  *Maximum task execution timeout* of 60 minutes, in a table with no column for what can be raised
  (*"You can request increases for some quotas, but other quotas can't be increased."*). The parameters
  page validates `execution_timeout` at 3,600 seconds, `retries` from 0 to 3 and `retry_delay` up to 300
  seconds, ignores `deferrable`, and names neither `wait_for_completion` nor a sensor's `mode`,
  `poke_interval` or `timeout`. The operators page lists `GlueJobSensor` and
  `SageMakerProcessingSensor`. The cap covers the task that waits on a processing job, which is why
  the lint holds a job's `MaxRuntimeInSeconds` at 2,820 s
  ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §W), and the lint asks
  `retries: 0` of every task. In `apache-airflow-task-sdk` 1.0.6, the SDK beside the worker's Airflow
  3.0.6, a try ended by the task's `execution_timeout` raises `AirflowTaskTimeout` and is retried while
  retries remain, and a try ended by a sensor's own `timeout` raises `AirflowSensorTimeout` and fails
  the task for good. In `apache-airflow-providers-amazon` 9.38.0, the version the guide's table lists,
  `SageMakerProcessingOperator` waits by default, has no `on_kill` and gives a retried try a second job
  (`action_if_job_exists: timestamp`), so its form for a long job is `wait_for_completion: false`, then
  `SageMakerProcessingSensor`; `GlueJobOperator` leaves the run going when its try is ended
  (`stop_job_run_on_kill` false) and, with `resume_glue_job_on_retry`, a retried try finds that run by
  its `--airflow_task_uuid` argument. One waiting task with three retries covers about four hours.
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
- **0.14 The statement that isolates a job** (this repository at `main` `c5e1718` and AWS's pages in
  their Markdown form, read 2026-11-16). `DenySageMakerJobsWithoutNetworkIsolation` is one statement of
  [`terraform-modules/sagemaker-denies/`](../../../terraform-modules/sagemaker-denies/main.tf), over
  `CreateTrainingJob`, `CreateProcessingJob`, `CreateHyperParameterTuningJob`, `CreateAutoMLJob`,
  `CreateAutoMLJobV2` and `CreateModel`, the list it shares with `DenySageMakerJobsOffVpc`. It binds
  whoever calls the action (Lesson 66), from three places: the persona sets (`identity/sso/`); the
  document of the `Workloads` OU, where Staging and Production sit (`identity/org-policies/`, a copy a
  precondition compares with the pinned tag); and the project boundary of `sagemaker-prereqs`
  (`sandbox/sagemaker/`, `staging/studio/`, `production/studio/`, `data-governance/publishing/`). It is
  [6a](stage-06a-unified-studio.md) step 3's, of 2026-08-16, older than D38, which left no spoke a
  default route; `objectives.md` asks no isolation of a job. The workflow's other tasks already run in
  the project's network as the project role: the Glue job on the project's connections, the Python and
  Bash tasks on the worker ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §N). The
  proxy admits a plane by its source range ([`NETWORK.md`](../../NETWORK.md)): Sandbox's VPC meets the
  allow-list a space meets, and the `Workloads` ranges of Staging and Production meet an empty one.
  AWS's page on a processing job in a VPC: *"This allows the processing job to connect to resources
  that exist in your VPC."*, with no word on network isolation. Its page on internet-free mode is
  titled for training and inference containers and names `CreateTrainingJob`,
  `CreateHyperParameterTuningJob` and `CreateModel`: *"No AWS credentials are made available to the
  container runtime environment."* The Tooling blueprint's `enableNetworkIsolation` *"Enables network
  isolation for training and deployed inference containers."*, and reads `true` in both Tooling stacks
  here ([Stage 17](stage-17-sandbox-machine-learning.md) step 0.8).
- **0.15 The archive and the lock, built from the application's draft** (2026-11-17, a build host outside
  this estate, Ubuntu 24.04 with glibc 2.39 and uv 0.11.32, no AWS call; this stage's log carries the
  readings). The draft is the application as "The application, task by task" lays it out, written outside
  the repository. Under `exclude-newer = "2026-11-03T00:00:00Z"` uv refused dbt-core pinned at 1.11.17, a
  release of 2026-11-06; with the three packages named by range the lock took dbt-core 1.11.16,
  `dbt-athena` 1.11.1 and OpenLineage 1.55.0, 86 packages, PyAthena 3.34.0, `click` 8.5.0, `protobuf`
  6.33.6, `sqlparse` 0.6.1 and `mmh3` 4.1.0 among them. `package-task` (awsds-workflows `196acee`)
  refused `--include code/dbt`, a file named as the folder dbt-core installs at the archive's root (*"dbt
  já está na raiz do .zip"*), which is why the console script travels inside the application's package.
  With `--platform x86_64-manylinux_2_28` and `--include code/run-dbt.sh` it built the archive in about
  five seconds: 26,119,606 bytes, 82,819,034 unzipped, 5,102 entries, `run-dbt.sh` and `app_dbt/bin/dbt`
  stored with mode 755, and no boto3 or botocore at its root; a second build of the same tree differed by
  two bytes, in the project's own metadata. Of its ten compiled modules `openlineage_sql` alone asks for
  `GLIBC_2.28`, and the others for 2.16 at most. `unzip` keeps the stored modes, and
  `python3 -m zipfile -e` extracts every file at mode 644. `awsds-workflows lint` in the authoring mode
  read the draft *"ok: 4 arquivo(s)"*, and `dbt parse` over the project ended 0 with placeholder values,
  no credential and a closed proxy.
- **0.16 The draft run as the task runs it, against simulated services** (2026-11-17, the same host, no
  AWS call; the last of four runs of the cases, 01:06 to 01:08 UTC, is the one quoted). The worker is a
  CPython 3.12 environment holding `apache-airflow` 3.0.6 under its constraint file and boto3 1.43.1,
  with the archive extracted beside it and first on `PYTHONPATH`. Each case runs the task's command as
  the service renders it, `bash -c "bash <folder>/run-dbt.sh …"`, in a temporary folder with an empty
  environment. AWS is moto 5.2.5's Athena, Glue, S3 and STS behind a proxy that records every call and
  gives each Athena statement its Glue side effect, and a listener that stands for the domain through
  `endpointOverride`. The simulation reads the client's side alone: Athena's, Glue's and Lake Formation's
  authorization, the engine's own effects, the domain's processing of an event and the worker itself are
  passes 2 and 3's.
  - **A first `dbt build`, the names as built**: exit 0 in 7.9 s, the wrapper and dbt peaking at 213,096
    kB of resident memory (189,184 to 222,188 kB over the cases that ran a model), a log of 3.5 kB in 34
    lines. It made 17 calls: `glue:GetDatabase` (the script's), `glue:GetDatabases`, `glue:GetTables`,
    `sts:GetCallerIdentity` twice, `athena:GetWorkGroup`, three `athena:StartQueryExecution` (the create,
    a constant `SELECT` that carries its result, and the test), each naming the workgroup and no
    `ResultConfiguration`, with their `GetQueryExecution` and `GetQueryResults`, `glue:GetTable` twice
    and one `glue:UpdateTable` (`persist_docs`); and no S3 call. dbt printed *"Done. PASS=2 WARN=0
    ERROR=0 SKIP=0 NO-OP=0 TOTAL=2"*. After dbt ended the wrapper posted 6 signed events of 1.9 to 7.6
    kB, a `START` and a `COMPLETE` for each of three jobs under the namespace `app-dbt`:
    `dbt-run-app_dbt`, `awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run` and `….build.test`.
    Each post left a line with the event's id (*"Successfully posted a LineageEvent: … in Domain: …"*),
    then *"Emitted 6 OpenLineage events"* and *"Underlying dbt execution returned 0"*. The datasets were
    `awsdatacatalog.app_dbt.trades` and `awsdatacatalog.app_dbt.notional_by_desk` under
    `awsathena://athena.us-west-2.amazonaws.com`, each with a `symlinks` facet naming
    `table/app_dbt/<table>` under `arn:aws:glue:us-west-2:<account>`, the account `sts:GetCallerIdentity`
    answered. The model's output carried `schema`, `documentation` and `columnLineage` (`desk` from
    `trades.desk`, `notional` from `trades.price` and `trades.quantity`), and the test's input a
    `dataQualityAssertions` facet, the `not_null` on `desk` holding.
  - **A second build, the names renamed**: exit 0 in 6.4 s, 28 calls. The statements were the swap of
    0.13: the create of `notional_by_desk__ha`, two `ALTER TABLE … RENAME TO`, a `DROP TABLE IF EXISTS`
    of `notional_by_desk__bkp`, the constant `SELECT` and the test. With `--names glue-arn` every dataset
    of the six events, and every input field of a `columnLineage` facet, carried the namespace
    `arn:aws:glue:us-west-2:<account>:table` and the name `app_dbt/<table>`, the symlinks unchanged.
  - **The engine's detection**: with dbt Core's own console script the wrapper read dbt's version from
    the file in 0.07 s; with a shell script in its place it ran `dbt --version`, 1.9 s and a request to
    PyPI.
  - **A post that fails**: with the endpoint's port closed and `--attempts 1`, exit 0 in 5.9 s and
    *"Emitted 0 OpenLineage events"*; with botocore's default attempts, exit 0 in 51.5 s (45 to 58 s over
    the runs). With the listener answering 403 `AccessDeniedException`, exit 0 in 5.8 s, six posts
    received and none emitted. Each warning (*"OpenLineage client failed to emit event"*) prints the
    whole event, the compiled SQL included: the logs were 125 kB and 77 kB against 3.5 kB.
  - **A test that fails**: dbt's exit code 1 was the wrapper's, the script's and the task's, in 5.9 s,
    with *"Done. PASS=1 WARN=0 ERROR=1"* and 6 events, three `START`, one `COMPLETE` and two `FAIL`.
  - **A database Glue does not hold**: exit 1 in 0.3 s on the script's own `GetDatabase`
    (`EntityNotFoundException`), before dbt started.
  - **Both workflows' commands**, translated as the CLI translates them and rendered by Jinja2 3.1.6 with
    every stage variable: the probe ended 0 in 0.8 s, its ten calls each on one line, a call the
    simulation answers with an error among them as one `REFUSED` line; `transform` ended 0 in 5.7 s with
    the first build's calls and events.
  - **By hand**, with `APP_DBT_NAMESPACE=app-dbt-by-hand`: `-- debug` ended 0 in 2.8 s with four calls
    and no event; `-- run` ended 0 in 6.1 s with 4 events under that namespace, the model's job named
    `awsdatacatalog.app_dbt.app_dbt.notional_by_desk`.
  - **Every file at mode 644**, the archive extracted by `python3 -m zipfile -e`: exit 0 in 7.9 s, the
    first line ending *"dbt from /tmp/tmp.…/bin, this script not executable"*, the same calls and events.
  - **The profile with `skip_workgroup_check: true`**: exit 0, no `athena:GetWorkGroup` among its calls
    and no `ResultConfiguration` in a statement: the way on if that one read is refused to a worker, at
    the cost of a new archive.
  - **The account a tracked file may name**: the runs above carried moto's default account, twelve digits
    the repository's identifier check refuses. Under `MOTO_ACCOUNT_ID=000000000000`, the twelve digits
    the check admits, both builds and the failing test read the same exit codes and six events each, the
    events and the trail naming that account alone (02:08 UTC).

## To execute

### 1. With nothing up: the application, the lineage configuration, the runbook's first version

No AWS session: a cloud session or the laptop, wherever `uv` reaches PyPI. Step 1.1's facts and decisions
1 to 7 and 10 are taken. What holds this pass on the user, read on the laptop on 2026-11-17: the draft and
0.16's fixtures are in the cloud session's `stage-20/app-dbt-review-2026-11-17.tar.gz`, which neither the
laptop nor `origin/main` holds, so the user copies it to the laptop, or the pass writes the application
from "The application, task by task" and regenerates the fixtures with 1.3's simulation; 1.2 builds the
one-stage shape of decision 9 (a), which is open; 1.5's reading of the portal's menus is a portal act.
1.3 runs on Linux x86_64: its archive's compiled modules, built for `x86_64-manylinux_2_28`, load on no
Darwin arm64 host, and the laptop holds no container runtime; on the laptop the simulation alone takes a
host archive built with `--platform aarch64-apple-darwin`, recorded in the log. A draft of the application went
through steps 1.2 to 1.4 outside the repository on 2026-11-17, against simulated services (0.15, 0.16);
this pass writes it under `examples/app-dbt/` and repeats each command on the tree it commits. The
commands run from `examples/app-dbt/`, and `awsds-workflows` runs from the commit the template's pipeline
pins, whatever the machine has installed:

```bash
TOOL="awsds-workflows @ https://github.com/felipenoris/awsds-workflows/archive/196aceec092649551ed6451796b1c3c7983cfafb.zip"
```

- **1.1 [user] The institution's dbt, answered 2026-11-16** (the log carries the words). The engines
  are AWS's own: the sources are tables of the Glue Data Catalog or of Redshift, and the processing is
  Athena's, Redshift's or a Glue Spark job's, beside data kept in the project's S3; the adapter's name
  was not known. dbt is dbt Core, run by the institution itself, and this stage takes 1.11 for now
  (decision 6). Nothing official exists on lineage, only proposals to use dbt's docs site (P4). A
  project holds tens of models, and a typical run can pass one hour. A processing job should run in
  the project's VPC (decision 13); whether one in the institution already does was not said.
- **1.2 [Claude] The application** `examples/app-dbt/` (decision 7), as "The application, task by task"
  lays it out: the manifest, the two workflows, the Glue script after the template's, the sample, the
  package with the dbt project, the transformer and the console script, `run-dbt.sh`,
  `scripts/dev-cli.sh` as the template's copy, and the README. The two scripts are committed with the
  executable bit (`git update-index --chmod=+x <file>` where the file system keeps none), and `uv lock`
  cuts the lock under an `exclude-newer` two weeks before the day of the cut, the template's rule. The
  tests: `dbt parse` over the project with placeholder values, no credential and no network; each
  workflow's `bash_command` translated as the CLI translates it, rendered by Jinja under
  `StrictUndefined` with every stage variable and parsed by `bash -n`; the manifest's stage declaring
  every `{env.NAME}` a workflow reads; `run-dbt.sh`'s refusals, exit 2 on an option it does not know and
  on a value left out; the stored modes of the two scripts; and the Glue script over doubles, as the
  template's.

  ```bash
  uv lock
  uv run pytest
  uvx --from "$TOOL" awsds-workflows lint .
  ```

  The step passes when the tests are green and the lint prints `ok` with the files it read, *"ok: 4
  arquivo(s)"* on the draft (0.15). The repository's hooks read the folder at the commit: `ruff check`
  and `ruff format --check` at 100 columns, the identifier check and the 500 KB limit of a file, the
  draft's lock being 118 KB. No pipeline runs the tests, the application having no GitLab project
  (decision 9): these commands are the gate, and the log carries their output. What the lint refuses in
  an application of one stage goes to 6.4's list.
- **1.3 [Claude] The lineage configuration and the transformer**: `run-dbt.sh` writes either form of
  `openlineage.yml`; `app_dbt/lineage.py` rewrites each Athena dataset of an event, the inputs, the
  outputs and every `columnLineage` input field, to the namespace `arn:aws:glue:<region>:<account>:table`
  and the name `<database>/<table>`. The tests feed the transformer the events the wrapper built for
  `athena` in 0.16's runs, kept as fixtures, and assert the names of both forms. The fixtures and the
  simulation name the account `000000000000`, which moto takes from `MOTO_ACCOUNT_ID` and the identifier
  check admits (0.16). The simulation of 0.16 is kept in `tests/simulation/`, outside `pytest`'s
  collection, since it builds a worker's environment and starts moto: it runs by hand in this pass and at
  each change of the lock. The step passes when a build posts six signed events and ends 0 in either form
  of the names; ends 0 with no event emitted when the listener's port is closed and `--attempts` is 1;
  and ends with dbt's exit code, 1, when the model's test fails.
- **1.4 [Claude] The archive**, one build, the options after the archive's path as
  [`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C2 asks, then the stored sizes and
  modes:

  ```bash
  uvx --from "$TOOL" awsds-workflows package-task . code/app-dbt.zip --platform x86_64-manylinux_2_28 --include code/run-dbt.sh
  ```

  ```bash
  python3 -c 'import sys, zipfile; z = zipfile.ZipFile(sys.argv[1]); print(len(z.infolist()), sum(i.file_size for i in z.infolist()), [oct(z.getinfo(n).external_attr >> 16) for n in ("run-dbt.sh", "app_dbt/bin/dbt")])' code/app-dbt.zip
  ```

  The step passes when `package-task` refuses nothing, the archive and its unzipped size are each under
  250 MB (iv) and the check prints `['0o100755', '0o100755']`: the draft read 26,119,606 bytes and
  `5102 82819034 ['0o100755', '0o100755']` (0.15). The archive stays out of git, and 2.0 builds it again
  from the merged tree.
- **1.5 [Claude] The runbook's first version**, `docs/plan/runbooks/catalog.md` (decision 10), as "The
  catalog's runbook, section by section" lays it out: every section, §L without the dbt case's readings,
  from what Stages 6f, 18 and 19 measured and from AWS's pages, the catalog's that `REFERENCES.md` holds
  for those stages and the lineage pages of 2026-11-16. The portal's menus are read again on the day,
  the catalog's items having moved on 2026-09-17, 2026-10-08 and 2026-10-20 (the release notes). A
  statement with no measurement in this estate says so.
- **1.6 [Claude] The desk readings**, for the runbook's §L: the forms that carry a run past the
  worker's hour (question 4), a processing job in its project's network with a waiting task, several
  Bash tasks by `--select` and a Glue job as dbt's runtime, each with what it needs and what nothing
  here measured (0.12, 0.14); and, in one paragraph, the names the wrapper gives the other adapters'
  datasets (0.9), Redshift and Glue with Spark being a later revision's (decision 1).
- **1.7 [Claude] [`upstream-releases.md`](../upstream-releases.md)** gains dbt Core, `dbt-athena` and
  OpenLineage, with the ranges this stage takes, the versions its lock holds and the dates that move
  them: dbt Core 1.11's critical support ends 2026-12-18.

### 2. The Sandbox sitting: dbt on a worker, and its events

A Sandbox sitting under [`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D's rules.
The user raises the hub and `sandbox/egress/` with its `mwaa` group, which a deploy from a space needs;
the application reaches a space of `eighth-experimentation` as a tar with the archive inside, so GitLab
and the tunnel stay out of it; the deploy and the runs go through `scripts/dev-cli.sh`. Steps 2.0 and 2.1
need nothing up, as the same acts needed nothing in [Stage 19](stage-19-smus-native-data-product.md),
*Create database* on 2026-11-08 and the query editor on 2026-11-14. The window opens at 2.2 and closes at
2.7, and Cost carries what it bills.

**The identities.** The laptop's commands are [Claude]'s reads as the infrastructure user in
`Sandbox Account 1`, permission set `InfrastructureAccess`, profile `awsds-infra-sandbox-1`. A lineage
node's id is read from `Data Governance`'s trail, the same user and set, profile `awsds-infra-data`. One
login covers both profiles and is the user's act. The portal, the space and the query editor are the
user's, as a member of `eighth-experimentation`, and every command of the space runs as the project role.
With the tunnel down, each `aws` command of the laptop takes `NO_PROXY='*'` before it. The laptop's shell
is zsh (Lesson 84): the blocks below quote every `--query` and split no variable.

**The values** each laptop block starts from, and **a run's reading**, which each step repeats with its
own workflow's name ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §V): a task's
`Status` and `DurationInSeconds` are read, since the run's `RunState` lags its tasks, and a task's text
is the stream its `LogStream` names.

```bash
D=dzd-d8yrvx1ko7im6o; E=avhvbqn37ty7m8; P=awsds-infra-sandbox-1; B=awsds-sandbox-smus-projects; WG=workgroup-$E-5hkjdsy3umpi1c
```

```bash
N=app_dbt_eighth_experimentation_app_dbt_probe
W=$(aws mwaa-serverless list-workflows --profile $P --region us-west-2 --query "Workflows[?Name=='$N'].WorkflowArn | [0]" --output text)
R=$(aws mwaa-serverless list-workflow-runs --workflow-arn "$W" --profile $P --region us-west-2 --max-results 1 --no-paginate --query 'WorkflowRuns[0].RunId' --output text)
aws mwaa-serverless get-workflow-run --workflow-arn "$W" --run-id "$R" --profile $P --region us-west-2 --query '[RunDetail.RunState, OverrideParameters]'
aws mwaa-serverless list-task-instances --workflow-arn "$W" --run-id "$R" --profile $P --region us-west-2 --query 'TaskInstances[].[TaskInstanceId, OperatorName, Status, DurationInSeconds]' --output text
aws mwaa-serverless get-task-instance --workflow-arn "$W" --run-id "$R" --task-instance-id <a task instance's id> --profile $P --region us-west-2 --query '[TaskId, Status, DurationInSeconds, LogStream, ErrorMessage]'
aws logs get-log-events --log-group-name "/aws/mwaa-serverless/$D-$E/$N" --log-stream-name '<the LogStream>' --start-from-head --profile $P --region us-west-2 --query 'events[].message' --output json | jq -r '.[]'
```

Sandbox's trail is read after its delay (Lesson 62), by event name, the worker's calls being the ones of
the project role's session `AmazonMWAAServerless`:

```bash
for e in <event names>; do aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=$e --start-time <the run's first minute> --profile $P --region us-west-2 --query 'Events[].CloudTrailEvent' --output json | jq -r '.[] | fromjson | [.eventTime, .eventName, (.userIdentity.arn // "-" | split("/") | last), (.userIdentity.invokedBy // "-"), .sourceIPAddress, (.vpcEndpointId // "-"), (.errorCode // "-"), (.additionalEventData // {} | tostring)] | @tsv'; done
```

- **2.0 [Claude] Before the sitting, with nothing up**: the starting state, then the archive and the tar.

  ```bash
  aws athena get-work-group --work-group $WG --profile $P --region us-west-2 --query 'WorkGroup.[State, Configuration.EnforceWorkGroupConfiguration, Configuration.EngineVersion.EffectiveEngineVersion, Configuration.ResultConfiguration.OutputLocation]' --output text
  aws glue get-database --name app_dbt --profile $P --region us-west-2
  aws glue get-job --job-name app-dbt-$E --profile $P --region us-west-2 --query Job.Name
  aws mwaa-serverless list-workflows --profile $P --region us-west-2 --query "Workflows[?starts_with(Name, 'app_dbt_')].Name" --output text
  for k in dev/data/catalogs/trades/ dev/data/catalogs/app_dbt/ shared/app-dbt/; do aws s3api list-objects-v2 --bucket $B --prefix $D/$E/$k --profile $P --region us-west-2 --query 'length(Contents || `[]`)'; done
  aws datazone search --domain-identifier $D --search-scope ASSET --owning-project-identifier $E --profile $P --region us-west-2 --query 'items[].assetItem.[identifier,name,externalIdentifier]' --output text
  ```

  Expected: the workgroup `ENABLED` and enforced, on Athena engine version 3, its output under
  `dev/sys/athena/` (0.7); `EntityNotFoundException` for the database and for the job; no workflow; `0`
  three times; and the project's assets, the older `trades` (`cm329mc3bqu39s`) among them. Objects under
  `dev/data/catalogs/trades/`, where the Glue job's table lands (0.7), are an older table's and go to the
  user before the sitting.

  The archive is built on the laptop from the merged tree, outside the repository, with pass 1's `TOOL`,
  and travels inside the tar, whose flags keep macOS's AppleDouble members out (`SUP-348`). An archive
  rebuilt during a sitting (2.2, 2.3, 5.1) comes from the session branch's commit, since nothing merges
  during a sitting, and that commit merges after it:

  ```bash
  rm -rf "$HOME/tmp/stage20" && mkdir -p "$HOME/tmp/stage20" && git archive --output="$HOME/tmp/stage20/source.tar" <the merged commit> examples/app-dbt && tar -x -f "$HOME/tmp/stage20/source.tar" -C "$HOME/tmp/stage20"
  ```

  ```bash
  cd "$HOME/tmp/stage20/examples/app-dbt" && uvx --from "$TOOL" awsds-workflows package-task . code/app-dbt.zip --platform x86_64-manylinux_2_28 --include code/run-dbt.sh
  ```

  ```bash
  cd "$HOME/tmp/stage20/examples" && COPYFILE_DISABLE=1 tar --no-xattrs --no-acls --no-mac-metadata -c -f "$HOME/tmp/stage20/app-dbt.tar" app-dbt
  ```

  ```bash
  python3 -c 'import sys, tarfile; t = tarfile.open(sys.argv[1]); print(len(t.getnames()), sum(m.isfile() for m in t.getmembers()), [n for n in t.getnames() if n.split("/")[-1].startswith("._")])' "$HOME/tmp/stage20/app-dbt.tar"
  ```

  The step passes when 1.4's check on the new archive prints the two modes `0o100755` and the tar lists
  no `._` member. `package-task` has built for the worker on this laptop (2026-10-12) and never this
  project: if the build or the check fails there, the archive is built in the space before the deploy,
  which no sitting has done ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C2).
- **2.1 [user] Create the database `app_dbt`**, still with nothing up, in `eighth-experimentation` (*Data
  → Create database*), then the editor's baseline: in the project's query editor on *Athena (SQL)*, as
  the project role, the statement 2.3's model repeats from a worker, an Iceberg table created under the
  database's location, and its drop.

  ```sql
  CREATE TABLE app_dbt.editor_probe WITH (table_type='iceberg', is_external=false, location='s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/app_dbt/editor_probe', format='parquet') AS SELECT 1 AS n;
  ```

  ```sql
  DROP TABLE app_dbt.editor_probe;
  ```

  **[Claude] reads** the new `DataLake` environment, the database, its grants, its daily source and the
  source's connection, then the editor's statements and what the drop left:

  ```bash
  aws datazone list-environments --domain-identifier $D --project-identifier $E --profile $P --region us-west-2 --query 'items[].[id,name,status]' --output text
  aws glue get-database --name app_dbt --profile $P --region us-west-2 --query 'Database.[Name, Description, LocationUri, CreateTableDefaultPermissions]'
  aws lakeformation list-permissions --resource '{"Database":{"Name":"app_dbt"}}' --profile $P --region us-west-2 --query 'PrincipalResourcePermissions[].[Principal.DataLakePrincipalIdentifier, join(`,`, Permissions), Condition.Expression]' --output text
  aws lakeformation list-permissions --resource '{"Table":{"DatabaseName":"app_dbt","TableWildcard":{}}}' --profile $P --region us-west-2 --query 'PrincipalResourcePermissions[].[Principal.DataLakePrincipalIdentifier, join(`,`, Permissions), Condition.Expression]' --output text
  aws datazone list-data-sources --domain-identifier $D --project-identifier $E --profile $P --region us-west-2 --query 'items[].[dataSourceId,name,status,connectionId,environmentId,schedule.schedule]' --output text
  aws datazone get-data-source --domain-identifier $D --identifier <the source's id> --profile $P --region us-west-2 --query '[name, status, publishOnImport, schedule.schedule, connectionId, configuration.glueRunConfiguration.relationalFilterConfigurations[].databaseName]'
  aws datazone get-connection --domain-identifier $D --identifier <the source's connectionId> --profile $P --region us-west-2 --query '[name, type, props.lakehouseProperties.glueLineageSyncEnabled]'
  aws athena batch-get-query-execution --query-execution-ids $(aws athena list-query-executions --work-group $WG --max-results 4 --no-paginate --profile $P --region us-west-2 --query 'QueryExecutionIds' --output text) --profile $P --region us-west-2 --query 'QueryExecutions[].[Status.SubmissionDateTime, Status.State, StatementType, Status.StateChangeReason, Query]'
  aws s3api list-object-versions --bucket $B --prefix $D/$E/dev/data/catalogs/app_dbt/editor_probe/ --profile $P --region us-west-2 --query '[length(Versions[?IsLatest] || `[]`), length(DeleteMarkers || `[]`)]'
  ```

  Expected, by `SUP-184` and 0.7: an environment `create-datalake-database-env-app_dbt-<epoch ms>`,
  `ACTIVE`; the database described *"Created by DataZone for project eighth-experimentation"*, at
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/`, with no
  default table permission; `IAMPrincipals` under the project's condition holding `CREATE_TABLE`,
  `DESCRIBE` and `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT`
  on its tables; a source on a daily cron at the minute of its creation, `publishOnImport` false, its
  filter naming `app_dbt`, hanging from the project's `project.default_lakehouse` connection, whose
  `glueLineageSyncEnabled` read `true` on 2026-10-18 ([`SMUS.md`](../../SMUS.md) §The catalog surface);
  both statements `SUCCEEDED`, and no current object under the dropped table's folder. The trail's
  `CreateTable` and `DeleteTable` (the loop above) give the session and the grant that admitted each
  (iii's baseline). A later sitting keeps its runs clear of the source's minute. If the editor's create
  is refused, the stage stops for the user with the refusal: 2.3 asks the same of a worker.
- **2.2 [user] The raises, the space, the deploy and the probe.** From the project folder, `make hub-up`,
  then

  ```bash
  make up ENV=sandbox ONLY=egress GROUPS=mwaa
  ```

  **[Claude]** tells the laptop's other sessions before the first raise and reads `make status` after the
  second. Then a JupyterLab space in `eighth-experimentation` on `awsds-sandbox-dev-env` version 11
  (alias `0.10.0`), `ml.t3.medium`, the tar dropped on its file browser, and in its terminal:

  ```bash
  tar -x -f app-dbt.tar && cd app-dbt
  ```

  The values the manifest reads, §D step 3 without an image or a key; the workgroup's name is typed,
  since the Tooling environment's values do not carry it:

  ```bash
  git clone --depth 1 https://github.com/felipenoris/awsds-workflows /tmp/awsds-workflows
  /opt/conda/bin/python /tmp/awsds-workflows/scripts/space_values.py > /tmp/space_values.json
  eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); print("\n".join("export %s=%s" % p for p in (("DOMAIN_ID", v["DOMAIN_ID"]), ("DOMAIN_REGION", v["REGION"]), ("SUBNET_AZ1", v["SUBNET_AZ1"]), ("SUBNET_AZ2", v["SUBNET_AZ2"]), ("ACCOUNT_ID", v["ACCOUNT_ID"]))))')"
  export DEV_PROJECT_NAME=eighth-experimentation ATHENA_WORKGROUP=workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c
  export LINEAGE_DOMAIN="$DOMAIN_ID" LINEAGE_NAMES=as-built LINEAGE_ENDPOINT=default LINEAGE_ATTEMPTS=default
  ```

  The deploy (§D step 6), which a line *"No custom VPC config"* stops, and the probe's run (§D step 7):

  ```bash
  scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
  ```

  ```bash
  scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt-probe
  ```

  **[Claude] reads** the copies and both workflows, then the probe's run and its log by the blocks above,
  and the trail's `GetCallerIdentity`, `GetWorkGroup`, `StartQueryExecution`, `GetDatabase` and
  `ListLineageEvents`:

  ```bash
  aws s3 ls s3://$B/$D/$E/shared/app-dbt/ --recursive --profile $P --region us-west-2
  aws s3 ls s3://$B/$D/$E/shared/operatorFiles/ --profile $P --region us-west-2
  for N in app_dbt_eighth_experimentation_app_dbt app_dbt_eighth_experimentation_app_dbt_probe; do W=$(aws mwaa-serverless list-workflows --profile $P --region us-west-2 --query "Workflows[?Name=='$N'].WorkflowArn | [0]" --output text); aws mwaa-serverless get-workflow --workflow-arn "$W" --profile $P --region us-west-2 --query '[Name, WorkflowVersion, WorkflowStatus, NetworkConfiguration.SubnetIds, NetworkConfiguration.SecurityGroupIds, EncryptionConfiguration.Type, LoggingConfiguration.LogGroupName]'; done
  ```

  Expected: five objects under `shared/app-dbt/`, `code/app-dbt.zip`, `glue/load.py`, `inbox/trades.csv`
  and the two definitions under `workflows/`, and under `shared/operatorFiles/` one copy of the archive
  for each deploy, of the size the laptop built
  ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C5); each workflow in the project's
  two subnets and security group, under the project key; the probe's task `SUCCESS`. The step passes when
  the probe's log reads glibc 2.28 or later (i); `python3`, `bash`, `mktemp`, `cp`, `chmod` and `dirname`
  on `PATH`; a script written in the `mktemp` folder running; the identity the project role's session
  `AmazonMWAAServerless`; the workgroup as 2.0 read it; the database's location; and `SELECT 1`
  `SUCCEEDED` (ii's first half). The count of `trades` reads a failed query that names the missing table,
  which is expected here. The log's other lines are readings: the distribution and the pre-installed
  packages against the guide's table, which [`upstream-releases.md`](../upstream-releases.md) owes for
  the Amazon provider; the CPUs and the memory; the names of the variables a workflow the CLI made
  carries; `PYTHONPATH` in a workflow with no archive. The step stops for the user on glibc below 2.28,
  with the ways on "The archive" names; on `GetDatabase` or `SELECT 1` refused or unanswered, with the
  refusal and before any grant is written (Cost); and on a connection error from `ListLineageEvents`, the
  endpoint's reading (Lesson 42), a refusal by the service being a reading for v. If a script runs in the
  task's folder alone, `run-dbt.sh` takes `mktemp -d -p "$PWD"`, a new archive and a deploy, before 2.3.
- **2.3 [user] Run `app-dbt`**, from the space:

  ```bash
  scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt
  ```

  **[Claude] reads** the run with `N=app_dbt_eighth_experimentation_app_dbt`, both tasks and
  `transform`'s log; the Glue job and the two tables; the model's files and Lake Formation's
  registrations; the statements; the events, each read back into a file; and the trail's
  `StartQueryExecution`, `GetWorkGroup`, `CreateTable`, `UpdateTable`, `GetDataAccess` and
  `PostLineageEvent`:

  ```bash
  aws glue get-job-runs --job-name app-dbt-$E --max-results 3 --profile $P --region us-west-2 --query 'JobRuns[].[Id,JobRunState,StartedOn,CompletedOn,ErrorMessage]' --output table
  for t in trades notional_by_desk; do aws glue get-table --database-name app_dbt --name $t --profile $P --region us-west-2 --query 'Table.[Name, TableType, Parameters.table_type, IsRegisteredWithLakeFormation, StorageDescriptor.Location, CreatedBy, Description, CreateTime, VersionId]' --output text; done
  aws s3 ls s3://$B/$D/$E/dev/data/catalogs/app_dbt/notional_by_desk/ --recursive --profile $P --region us-west-2
  aws lakeformation list-resources --profile $P --region us-west-2 --query 'ResourceInfoList[].[ResourceArn, RoleArn]' --output text
  aws athena batch-get-query-execution --query-execution-ids $(aws athena list-query-executions --work-group $WG --max-results 12 --no-paginate --profile $P --region us-west-2 --query 'QueryExecutionIds' --output text) --profile $P --region us-west-2 --query 'QueryExecutions[].[Status.SubmissionDateTime, Status.State, StatementType, ResultConfiguration.OutputLocation, Statistics.DataScannedInBytes, Status.StateChangeReason, Query]'
  aws datazone list-lineage-events --domain-identifier $D --timestamp-after <the run's first minute> --profile $P --region us-west-2 --query 'items[].[id, processingStatus, eventTime, eventSummary.openLineageRunEventSummary.eventType, eventSummary.openLineageRunEventSummary.job.namespace, eventSummary.openLineageRunEventSummary.job.name, createdBy]' --output text
  aws datazone get-lineage-event --domain-identifier $D --identifier <an event's id> --profile $P --region us-west-2 "$HOME/tmp/stage20/event-<n>.json"
  ```

  The step passes when both tasks read `SUCCESS` and `transform`'s log holds, as 0.16's did: *"Running
  with dbt="* and the lock's version, and *"Registered adapter: athena=1.11.1"*; *"Done. PASS=2 WARN=0
  ERROR=0 SKIP=0 NO-OP=0 TOTAL=2"*; six lines *"Successfully posted a LineageEvent: … in Domain: …"*,
  then *"Emitted 6 OpenLineage events"* and *"Underlying dbt execution returned 0"*; and the script's
  *"peak memory … kB, exit code 0"*. The transport's warning *"does not support timeout"* is a good run's
  too. The readings: the Glue job's table and events, the baseline; the model's table, `TableType` and
  `table_type`, its location under `dev/data/catalogs/app_dbt/notional_by_desk/<uuid>`, the session that
  created it and the grant that admitted it, and whether Lake Formation's registration of `dev/` covers
  the location (ii, iii); the statements, the create, the constant `SELECT` and the test, each placed by
  the workgroup's enforced output; dbt's times, the script's first line (where `dbt` ran from, the
  script's own mode), the peak memory and the task's duration (iv); six events `SUCCESS` under the job
  namespace `app-dbt`, posted through the endpoint by the worker's session, beside the Glue job's (v);
  the description `persist_docs` wrote on the table.

  The step stops for the user when the model's statement or an Iceberg table is refused, with the refusal
  and never a Hive table in its place ("The dbt project"). The other refusals have a way on:
  `GetWorkGroup` alone refused, the profile takes `skip_workgroup_check: true` (0.16); `glue:UpdateTable`
  refused, `persist_docs` leaves the project and xvi reads no; each is a new archive, a deploy and this
  step again. Posts refused or unanswered leave the task green and are v's reading and decision 5's
  input. If `transform` cannot read `trades`, the probe runs once more: its count reads whether the
  worker's session reads the Glue job's table.
- **2.4 [user] Run the database's source in the portal** (the project's data sources, the one 2.1 read,
  *Run*), then open each table's asset and its *Lineage* tab. **[Claude] reads** the run, the assets and
  the nodes:

  ```bash
  aws datazone list-data-source-runs --domain-identifier $D --data-source-identifier <the source's id> --profile $P --region us-west-2 --query 'items[].[id, type, status, runStatisticsForAssets, lineageSummary.importStatus]'
  aws datazone list-data-source-run-activities --domain-identifier $D --identifier <the run's id> --profile $P --region us-west-2 --query 'items[].[technicalName, dataAssetStatus, dataAssetId, technicalDescription, lineageSummary.eventStatus]' --output text
  aws datazone search --domain-identifier $D --search-scope ASSET --owning-project-identifier $E --profile $P --region us-west-2 --query 'items[].assetItem.[identifier,name,externalIdentifier]' --output text
  aws datazone get-asset --domain-identifier $D --identifier <an asset's id> --profile $P --region us-west-2 --query "formsOutput[?formName=='GlueTableForm'].content | [0]" --output text
  aws datazone get-lineage-node --domain-identifier $D --identifier amazon.datazone.asset/<an asset's id> --profile $P --region us-west-2 --query '[id, typeName, sourceIdentifier, upstreamNodes[].id, downstreamNodes[].id]'
  aws datazone get-lineage-node --domain-identifier $D --identifier 'app-dbt.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run' --profile $P --region us-west-2 --query '[id, typeName, sourceIdentifier, formsOutput[].formName, upstreamNodes[].id, downstreamNodes[].id]'
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateLineageNode --start-time <2.3's first minute> --profile awsds-infra-data --region us-west-2 --query 'Events[].CloudTrailEvent' --output json | jq -r '.[] | fromjson | [.eventTime, (.additionalEventData | tostring)] | @tsv'
  ```

  This stage's assets are the two whose external identifier ends `table/app_dbt/trades.avhvbqn37ty7m8`
  and `table/app_dbt/notional_by_desk.avhvbqn37ty7m8` (`SUP-343`); the older `trades` names
  `glue_db_blerpkhn9nj7o0`. An asset's node answers to `amazon.datazone.asset/<asset id>`, a job's to
  `<namespace>.<name>`, and every other node to its id alone, which `Data Governance`'s trail gives with
  its `sourceIdentifier` (`SUP-347`); `get-lineage-node` on each id chains them. The graph is one when
  `notional_by_desk`'s asset has the dbt job's run upstream and that run has, upstream, the node the Glue
  job wrote, the one `trades`' asset hangs from: the model's output node then carries the table's ARN,
  the symlink honoured (vi). It is split when dbt's datasets are nodes of their own under
  `awsathena://athena.us-west-2.amazonaws.com/awsdatacatalog.app_dbt.<table>`, and pass 3 opens with 3.1.
  The other readings: what the job and the job-run nodes are called and which facets they keep, the
  compiled SQL among them; what the portal draws, the user's look, from the S3 input through the Glue
  job, `trades` and the dbt job to `notional_by_desk`, with or without column lineage, and what the
  test's assertions left (vii); and the model's and the columns' descriptions on the asset (xvi).
- **2.5 [user] Run `app-dbt` again**, by 2.3's command, then the source, as in 2.4. **[Claude] reads**,
  by 2.3's and 2.4's blocks, what a second `dbt build` does (x): the statements, expected the swap of
  0.13 as 0.16 ran it, the create of `notional_by_desk__ha`, two `ALTER TABLE … RENAME TO`, a
  `DROP TABLE IF EXISTS` of `notional_by_desk__bkp`, the constant `SELECT` and the test, with the session
  and the grant that admitted each rename and the drop (the trail's `CreateTable`, `UpdateTable` and
  `DeleteTable`); the table's `CreateTime`, `VersionId` and location against the first run's; what the
  drop left under the first location and what the grants on the table read:

  ```bash
  aws s3api list-object-versions --bucket $B --prefix $D/$E/dev/data/catalogs/app_dbt/notional_by_desk/ --profile $P --region us-west-2 --query '[length(Versions[?IsLatest] || `[]`), length(DeleteMarkers || `[]`)]'
  aws lakeformation list-permissions --resource '{"Table":{"DatabaseName":"app_dbt","Name":"notional_by_desk"}}' --profile $P --region us-west-2 --query 'PrincipalResourcePermissions[].[Principal.DataLakePrincipalIdentifier, join(`,`, Permissions), Condition.Expression]' --output text
  ```

  and, after the source's run, the asset (the same id or a new one, by 2.4's `search` and activities) and
  the graph: new job runs under the same job, and the dataset nodes' versions. A rename or the drop
  refused stops the step for the user with the statement's `StateChangeReason`: every later run of the
  model needs the swap.
- **2.6 [user] The same project by hand, from the space's terminal**, if the sitting has room: the
  archive unpacked beside the space's own Python and run through the script, under another job namespace.

  ```bash
  mkdir -p /tmp/app-dbt-hand && python3 -m zipfile -e code/app-dbt.zip /tmp/app-dbt-hand
  PYTHONPATH=/tmp/app-dbt-hand APP_DBT_NAMESPACE=app-dbt-by-hand bash /tmp/app-dbt-hand/run-dbt.sh --region us-west-2 --account "$ACCOUNT_ID" --database app_dbt --workgroup "$ATHENA_WORKGROUP" --domain "$LINEAGE_DOMAIN" --names "$LINEAGE_NAMES" -- debug
  ```

  Then the same line ending `-- run`. The archive leaves out boto3, botocore and PyYAML, which the
  space's Python holds as the worker's does. The script's second line names the interpreter: the
  archive's compiled modules are the worker's, so anything but Python 3.12 on Linux x86_64 stops the
  step. In 0.16, `debug` ended 0 with no event and `run` posted four under the namespace, the model's job
  named `awsdatacatalog.app_dbt.app_dbt.notional_by_desk`. **[Claude] reads** the space's session against
  the worker's in the trail, and how the graph tells a person's run from the workflow's, a second job on
  the same nodes: the scientist's development loop.
- **2.7 [user] The downs**: the space stopped, every portal tab closed, then `make down ENV=sandbox` and
  `make hub-down`. **[Claude]** `make status`, [`promotion.md`](../runbooks/promotion.md) §R's readings,
  and `$HOME/tmp/stage20` deleted once the log holds what the event files read.

### 3. The names made to meet, and what a failed post leaves

The same sitting or the next Sandbox one, under pass 2's raises, values and reads. A switch is an
`export` in the space and a run, with no deploy, and each run's `OverrideParameters` is read back before
its result is. Steps 3.1 and 3.2 run only if 2.4 reads a split graph.

- **3.1 [user] A run with the names renamed** (decision 3 (b)), from the space, then the source's run and
  the *Lineage* tabs, as in 2.4:

  ```bash
  export LINEAGE_NAMES=glue-arn
  scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt
  ```

  **[Claude] reads**, by 2.3's and 2.4's blocks (viii): the events' datasets, each under the namespace
  `arn:aws:glue:us-west-2:<Sandbox>:table` with the name `app_dbt/<table>` (`get-lineage-event`); the
  nodes the run created; whether `notional_by_desk`'s asset now has the dbt job's run upstream, and the
  Glue job's node upstream of that; and what became of the first runs' nodes under the Athena name. If
  the graph is one, `LINEAGE_NAMES` stays `glue-arn` for the rest of the stage.
- **3.2 [Claude] If the renamed form does not link either**, the stage stops for the user with the
  readings. A Glue `environment-properties` facet the application makes up is never the remedy: it tells
  the catalog a Glue job ran.
- **3.3 [user] Runs that fail to post**, each a different failure and a switch of the task, 2.3's run
  after each `export`. A domain id the service does not hold, which the service answers with an error:

  ```bash
  export LINEAGE_DOMAIN=dzd_canaryprobe0000
  ```

  A closed port on the worker itself, a refused connection:

  ```bash
  export LINEAGE_DOMAIN="$DOMAIN_ID" LINEAGE_ENDPOINT=http://127.0.0.1:9 LINEAGE_ATTEMPTS=1
  ```

  The `datazone` endpoint's own name on a port its security group does not admit, no answer:

  ```bash
  export LINEAGE_ENDPOINT=https://datazone.us-west-2.api.aws:8443 LINEAGE_ATTEMPTS=1
  ```

  And the switches back at rest:

  ```bash
  export LINEAGE_ENDPOINT=default LINEAGE_ATTEMPTS=default
  ```

  `LINEAGE_ATTEMPTS` is 1 in the last two, since the transport takes no timeout: botocore's defaults, a
  60-second connect timeout and five attempts, would hold each unanswered event about five minutes, and
  one attempt holds the six about six minutes in all. **[Claude] reads**, for each run, the wrapper's
  lines, its exit code, the task's state and the time the failure added over 2.3's (ix), decision 5's
  input; and the log's size, since each failed post prints its whole event, the compiled SQL included
  (125 kB against 3.5 kB in 0.16). In 0.16 a refused post and a closed port each ended the task 0 in
  about 6 s with *"Emitted 0 OpenLineage events"*.
- **3.4 [user] Who may write and read a graph**, from the terminal of a space of `test-experimentation`,
  as that project's role. The event's output is the pair of names under which 2.4 or 3.1 read the model's
  node, the namespace's account id typed in the space and never written down:

  ```bash
  python3 -c 'import datetime, json, sys, uuid; print(json.dumps({"eventType": "COMPLETE", "eventTime": datetime.datetime.now(datetime.timezone.utc).isoformat(), "run": {"runId": str(uuid.uuid4())}, "job": {"namespace": "stage-20-foreign", "name": "foreign-writer"}, "inputs": [], "outputs": [{"namespace": sys.argv[1], "name": sys.argv[2]}], "producer": "https://example.com/stage-20-foreign", "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"}))' '<the namespace>' '<the name>' > /tmp/foreign-event.json
  ```

  ```bash
  aws datazone post-lineage-event --domain-identifier dzd-d8yrvx1ko7im6o --event fileb:///tmp/foreign-event.json --region us-west-2
  ```

  ```bash
  aws datazone get-lineage-node --domain-identifier dzd-d8yrvx1ko7im6o --identifier 'app-dbt.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run' --region us-west-2 --query '[id, typeName, formsOutput[].formName]'
  ```

  **[Claude] reads** whether the domain accepts an event about another project's table (the post's answer
  and the event's `processingStatus`), whether the portal draws the foreign job on that table's tab, and
  whether a role outside the project reads the job's facets, the compiled SQL among them (xi; `TM-29`'s
  shape, on lineage). Then **[Claude⚡]**, on the user's word, the foreign event's delete, and what it
  removed of the event, its nodes and the edge the portal drew (xv). The AWS CLI carries the operation
  from 2.35.5, by its changelog, and the laptop's read 2.37.12 on 2026-11-16 (`SUP-370`); if DataZone
  refuses the laptop's identity, the same command runs from the space that posted, whose `aws --version`
  is read first:

  ```bash
  aws datazone delete-lineage-event --domain-identifier $D --identifier <the foreign event's id> --profile $P --region us-west-2
  ```

### 4. A processing job in its project's network

Decision 13's change, which no other pass waits on: `sagemaker:CreateProcessingJob` leaves the action
list of `DenySageMakerJobsWithoutNetworkIsolation` (0.14). A laptop session makes it, on the user's word,
the other sessions on the laptop told first; 4.5 is a Sandbox sitting's. Every command is the
infrastructure user's, permission set `InfrastructureAccess`, and one login, the user's act, covers the
four profiles 4.4 names.

- **4.1 [Claude] The module**, by Recipe B of [`terraform-changes.md`](../runbooks/terraform-changes.md).
  In `terraform-modules/sagemaker-denies/main.tf`, `network_isolation_actions` becomes a list of its own,
  the five actions that stay (`CreateTrainingJob`, `CreateHyperParameterTuningJob`, `CreateAutoMLJob`,
  `CreateAutoMLJobV2` and `CreateModel`), where it is `local.vpc_config_actions` today (Lesson 51).
  `sagemaker-prereqs` changes in nothing: its boundary sources the denies by path (`boundary.tf`), so a
  tag of its own is what carries them to its callers.

  ```bash
  terraform -chdir=terraform-modules/sagemaker-denies init -backend=false && terraform -chdir=terraform-modules/sagemaker-denies validate
  terraform -chdir=terraform-modules/sagemaker-prereqs init -backend=false && terraform -chdir=terraform-modules/sagemaker-prereqs validate
  ```

  A module change is exercised by planning a caller, never by `validate`: before the commit
  `staging/studio/`'s `source` points at `../../../terraform-modules/sagemaker-prereqs`, the slice is
  initialised and planned as 4.4 does, the plan read, the `source` returned to its `?ref=` and `init` run
  again. Commit 1 holds the module alone. Then, one command each, each output read:

  ```bash
  git log --oneline -1
  git ls-remote --tags origin 'sagemaker-denies-v*' 'sagemaker-prereqs-v*'
  git tag sagemaker-denies-v0.3.0
  git tag sagemaker-prereqs-v0.11.0
  git push -u origin <branch> --tags
  git ls-remote --tags origin sagemaker-denies-v0.3.0 sagemaker-prereqs-v0.11.0
  ```

  The two versions are the next after `v0.2.0` and `v0.10.0`, the newest origin held on 2026-11-17; the
  second command reads them again at the tagging, a peer may have taken one. The last command passes on
  two lines, each the hash of commit 1, a tab and the tag's ref.
- **4.2 [Claude] The callers**, commit 2: `identity/sso/policies-sagemaker.tf` and
  `identity/org-policies/job-denies.tf` take the new `sagemaker-denies` tag, and
  `policies/awsds-org-scp-ou-workloads.json` takes the statement's new list in the same commit, which
  `policies.tf`'s precondition compares on every plan; `sandbox/sagemaker/`, `staging/studio/` and
  `production/studio/` take the new `sagemaker-prereqs` tag, each plan read for what the tags between its
  pin and the new one carry beside the statement (`sandbox/sagemaker/` pins `v0.9.0`). The two `studio/`
  slices hold one `main.tf`, which `./scripts/check-copies.py` compares, so their pins move together.
  `data-governance/publishing/` keeps its pin: the scope is Sandbox, Staging and Production. The persona
  sets compose one fragment, so every account a set is assigned in follows, and a set assigned outside
  those accounts is named to the user before the apply: the governance managers' set is assigned in
  `Data Governance` (`identity/sso/locals.tf`), so the change reaches that account. The SCP's description
  in `identity/org-policies/locals.tf` says *network-isolated* and changes with the statement.
  `sandbox/model-access/`'s two roles carry Sandbox's boundary and follow it with no apply of their own.
  [`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md)'s row is rewritten in the
  same sitting, and `./scripts/check-index.py` run.
- **4.3 [Claude] The battery's rows** (`aws/probes/probes.py`): the `ou` row *"workloads:
  CreateProcessingJob not isolated"* becomes an `allow` row, a contrast that has to stay authorized;
  `_training_job` takes the isolation as an argument, where it sends `--enable-network-isolation` always,
  and a row *CreateTrainingJob not isolated* becomes the one that exercises the statement, beside the
  compliant training row that is its contrast. [`scp-battery.md`](../runbooks/scp-battery.md)'s table
  follows, in its Phase 4b.
- **4.4 [Claude⚡] The applies**, each from a plan read first and each on the user's word naming it. Every
  one removes an action from a deny, so no order of them locks a caller out; the order below puts the OU
  document and its battery before the targets' roles.

  | Order | Slice | Account | Profile |
  |---|---|---|---|
  | 1 | `identity/sso/` | `Identity` | `awsds-infra-identity` |
  | 2 | `identity/org-policies/` | `Identity` | `awsds-infra-identity` |
  | 3 | `sandbox/sagemaker/` | `Sandbox Account 1` | `awsds-infra-sandbox-1` |
  | 4 | `staging/studio/` | `Staging` | `awsds-infra-staging` |
  | 5 | `production/studio/` | `Production` | `awsds-infra-prod` |

  Each row is Recipe A's steps 3 to 7, from the branch that holds commit 2 (Lesson 79), the plan kept
  outside the repository:

  ```bash
  export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
  ./scripts/gen-backend-hcl.py <account> <slice> && ./scripts/gen-tfvars.py <account> <slice>
  AWS_PROFILE=<profile> terraform -chdir=terraform-live/<account>/<slice> init -backend-config=backend.hcl -input=false
  AWS_PROFILE=<profile> terraform -chdir=terraform-live/<account>/<slice> plan -input=false -out="$HOME/tmp/<account>-<slice>.tfplan"
  ```

  ```bash
  AWS_PROFILE=<profile> terraform -chdir=terraform-live/<account>/<slice> apply -input=false "$HOME/tmp/<account>-<slice>.tfplan"
  AWS_PROFILE=<profile> terraform -chdir=terraform-live/<account>/<slice> plan -input=false
  ```

  A plan passes when it changes the statement's action list and nothing else, or what 4.2 read of the
  tags between; the second plan reads `No changes`. A plan that carries another stage's unapplied change
  stops its row until that stage applies it (Lesson 69): `production/studio/` held release G's from
  2026-11-16 to its apply on 2026-11-17 ([`promotion.md`](../runbooks/promotion.md) §N.8.5 step 3), so
  that slice's plan here carries pass 4's change alone. A minute or more after `identity/org-policies/`'s apply
  (`SUP-350`), Phase 4b's battery, whose workloads rows run in Production as `awsds-infra-prod`, then
  `make check`:

  ```bash
  ./aws/probes/scp-battery.py --phase ou
  ```

  **[Claude] reads** the battery's verdicts, the processing row authorized and the training row refused
  with the others as they were, and `./aws/deploytargets.py` `DT-11`, which reads the document's Sids and
  stays as it is (xii).
- **4.5 [user] A processing job without isolation, in Sandbox**, in a sitting raised as 2.2's: a third
  workflow of `app-dbt`, one `SageMakerProcessingOperator` task on the house image, in the project's
  subnets and security group, with `EnableNetworkIsolation: false` and the statement's other settings as
  the template sends them. The manifest's stage gains the template's `DEV_PROJECT_SG` and
  `DEV_PROJECT_KEY_ARN` (§D step 3's line) and the image's URI, typed in the space and never written
  down. The workflow is written at this pass, and `awsds-workflows lint` refuses it by its `job` rule,
  which is expected until 6.4's item is taken. Its script prints the caller's identity, a `SELECT 1`
  through the project's Athena workgroup, the product database as Glue returns it, `ListLineageEvents` on
  the domain, and what the proxy answers a request for a name on Sandbox's allow-list and for one off it.
  The deploy and the run are 2.2's commands with the workflow's name. **[Claude] reads** the run by pass
  2's blocks, the job's description and its calls in Sandbox's trail, by the session `SageMaker` (xii,
  xiii):

  ```bash
  aws sagemaker list-processing-jobs --name-contains app-dbt --max-results 3 --profile $P --region us-west-2 --query 'ProcessingJobSummaries[].[ProcessingJobName, ProcessingJobStatus, CreationTime]' --output text
  aws sagemaker describe-processing-job --processing-job-name <the job's name> --profile $P --region us-west-2 --query '[ProcessingJobStatus, FailureReason, NetworkConfig, ProcessingResources.ClusterConfig, RoleArn]'
  ```

  The step passes when the job is created, which the statement refused before 4.4, and ends `Completed`
  with each call answered. A target's half of xiii is a reading of [`NETWORK.md`](../../NETWORK.md) until
  a release carries such a job: there a job takes the deployment project's subnets and group,
  `datazone-<project>-dev`, which the leg reads from the project itself
  (`scripts/deploy-application.py`), and they reach the VPC's interface endpoints and gateways and a
  proxy that refuses the `Workloads` ranges every name (read 2026-11-11).
- **4.6 [Claude] The documents and the checks that state the rule**:
  [`serverless-workflows.md`](../runbooks/serverless-workflows.md) §J;
  [`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D, §W and §N's matrix, where a
  processing job leaves the training job's row; [Stage 9](stage-09-deployment-targets.md) step 3.1's *"A
  SageMaker job reads no governed data"*, which stays true of a training job and becomes, for a
  processing job, what its role is granted; `./aws/sandbox-orchestration.py` `SO-5` and
  `./aws/sandbox-ml.py`'s reading of a pipeline's Processing step, each of which counts a processing job
  without isolation as outside the boundary; and a [`threat-model.md`](../threat-model.md) entry: a
  processing job's container holds its role's credentials and a path to the VPC's endpoints and, in
  Sandbox, to the proxy's allow-list, the application choosing isolation job by job (`app-etl`'s tasks
  keep `EnableNetworkIsolation: true`). Three more texts state the rule:
  [`sagemaker-application.md`](../runbooks/sagemaker-application.md) §C's *"no network and no AWS
  credentials"*, [`sagemaker-ai-ml.md`](../runbooks/sagemaker-ai-ml.md)'s statement that a pipeline's
  steps take *"the same actions"* and its paragraph on a pipeline's processing step, and
  `awsds_demo_job/__main__.py`'s docstring, *"runs every job isolated"*.

### 5. Across projects

Waits on Stage 19 step 4.12, `eighth-experimentation`'s subscription to Production's listing, and on
decision due 11. It runs while that subscription is live, before the revocation step 4.12 ends with, the
two sessions agreeing on the order. It is a Sandbox sitting raised as 2.2's and read by pass 2's blocks.

- **5.1 [Claude] A model over the subscribed table**: a second source, `trades_notional` through the
  resource link the subscription writes, in `glue_db_blerpkhn9nj7o0` by 6f step 11's reading, and a model
  `notional_by_desk_prod` in `app_dbt`. The link and its target are read first, with the subscription
  live:

  ```bash
  aws glue get-tables --database-name glue_db_blerpkhn9nj7o0 --profile $P --region us-west-2 --query 'TableList[].[Name, TargetTable.DatabaseName, TargetTable.Name, IsRegisteredWithLakeFormation]' --output text
  ```

  The change goes through pass 1's tests and lint, then a new archive and a tar (2.0).
- **5.2 [user] Deploy and run**, by 2.2's and 2.3's commands. **[Claude] reads** the worker's read under
  the subscription's grant, with `GetDataAccess` in the trail of the account that vends; the event's
  input name, which is the link's in Sandbox's catalog while the listing's asset carries Production's
  table ARN; and whether the graph joins Production's job, its table, the listing, the subscription and
  the dbt job. If it does not, the transformer resolves a link to its target (`glue:GetTable`'s
  `TargetTable`) and the run repeats (xiv).
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

- **7.1 [user] Keep or delete**: the workflows and the Glue job, the files under `shared/app-dbt/`, the
  database `app_dbt` with its assets and source, and the lineage events, by what xv read of
  `DeleteLineageEvent`. A delete follows Rollback's order and commands.
- **7.2 [Claude]** This file's Status, the index rows, the log, the waiting list.

## Verifications

| # | Question | Step |
|---|---|---|
| i | Which glibc, distribution and pre-installed packages does the worker carry; does the archive (`manylinux_2_28`) import on it; does a script written in the task's folder or in a `mktemp` folder run there, and what mode does the extraction leave on the archive's scripts? | 2.2, 2.3 |
| ii | Does Athena admit the worker's session of the project role in the project's workgroup, and does Lake Formation vend to it under the project's context? | 2.2, 2.3 |
| iii | Does a dbt model become an Iceberg table through Athena as the project role, from the query editor and from a worker: which grant admits it, do its files land under the database's location, where the adapter writes them (0.13), and does Lake Formation's registration cover that location? | 2.1, 2.3 |
| iv | What does dbt cost on a worker: the archive's size, the start, the run's time and its peak memory, against 250 MB, 1 vCPU, 3 GiB and 3,600 s? | 1.4, 2.3 |
| v | Does the worker's session post through the `datazone` endpoint: how many events, and with which `processingStatus`? | 2.3 |
| vi | With the events as the wrapper builds them, does the model's node take the Glue table's ARN, the symlink honoured, and is dbt's input the node the Spark job wrote? | 2.4 |
| vii | Does the portal draw one graph, from the S3 input through the Glue job, `trades` and the dbt job to `notional_by_desk`, with column lineage, and what does a test's event leave on it? | 2.4 |
| viii | With the datasets renamed in the client, do the nodes link to the assets, and what became of the first run's nodes? | 3.1 |
| ix | What does a refused, a rejected and an unanswered post leave: the wrapper's log, its exit code, the task's state and the time added? | 3.3 |
| x | What does a second run's swap by rename (0.13) do to the table, to its grants, to the asset and to the graph? | 2.5 |
| xi | Does the domain accept, from one project's role, an event about another project's table, and does a role outside a project read that project's job node, its SQL included? | 3.4 |
| xii | With `sagemaker:CreateProcessingJob` out of the isolation statement, is a processing job without network isolation authorized, for a project role in Sandbox and for a caller in Production, and is a training job without it still refused? | 4.4, 4.5 |
| xiii | What does that job's container reach as the project role in Sandbox: STS, Athena, Glue and the domain through the endpoints, the proxy's allow-list and no name off it? And what does the network give a job in a target, by reading? | 4.5 |
| xiv | Across a subscription, does the graph join the producer's job, the listing, the subscription and the consumer's dbt job, and what does a member of another project see of each? | 5.2, 5.3 |
| xv | What does `DeleteLineageEvent` remove: the event, its nodes, the edges the portal draws? | 3.4, 7.1 |
| xvi | Do a model's and its columns' descriptions reach the asset through the Glue table's comments? | 2.4 |
| xvii | What did the sittings bill, by service? | 6.3 |

## Decisions due

The user took the decisions below one at a time on 2026-11-16, in the cloud session's thread, after
step 1.1's facts; the log carries each question as it was asked and each answer in the user's words.
Taken: 1 to 7, 10 and 13. Settled by other decisions: 8. Moot: 12. Due later, each with the
recommendation that holds until then: 9 and 11.

1. **The engine, and so the adapter.** **Taken 2026-11-16: (a)**, in the user's words *"(a).
   Futuramente podemos revisar o plano para incluir outros conectores."* (a) Athena over the project's
   Glue Data Catalog, Iceberg tables, `dbt-athena`: the engine the portal's query editor uses on a
   project's Lakehouse, with nothing to keep up, billed by the bytes scanned, its adapter maintained by
   dbt Labs; its dataset names are the ones verification vi has to read. Not taken, and a later
   revision's to bring in: (b) Redshift Serverless, `dbt-redshift`, the engine of AWS's own dbt lineage
   example, its names under a rule of AWS's own page; (c) Glue with Spark, where `dbt-glue`, the adapter
   for Glue interactive sessions, has no release for dbt Core 1.11 (0.10), which leaves `dbt-spark` on a
   Glue job's own session. The stage therefore holds no warehouse sitting, and decision 12 is moot.
2. **Where dbt runs.** **Taken 2026-11-16: (a)**, a Bash task on the worker, from a `package-task`
   archive: the pattern of AWS's MWAA guide on the serverless worker. dbt is a client that sends SQL,
   which is what D28 lets a worker run; the task costs a fraction of a cent and needs no image. The
   worker's 3,600 s hold the whole `dbt build`, and a typical run of the institution's can pass an hour
   (step 1.1), so the stage measures a short run alone. The forms that carry a longer one were offered
   beside it and are compared in the runbook (1.6), measured by no pass: (b) a processing job in its
   project's network with a waiting task (decision 13 and 0.12), which Claude recommended as a second
   measurement; (c) several Bash tasks by `--select`; (d) a Glue job as dbt's runtime. Not offered: a
   Python task calling `dbtRunner`, which runs dbt on Airflow's versions of every package they share,
   three of which Airflow 3.0.6's constraint file pins below the floor dbt-core 1.11.16 and 1.11.17 share
   (`click`, `protobuf`, `sqlparse`); a provider's operator in the code package.
3. **How dbt's dataset names meet the assets.** **Taken 2026-11-16: (a) first, and (b) if the graph
   splits.** (a) the events as the wrapper builds them: one run tells what the domain does with a
   symlink no Glue job sent, which is what any dbt project posts unchanged. (b) OpenLineage's
   `transform` transport with a transformer of the application, which rewrites each Athena dataset, and
   each `columnLineage` input field, to the form the page's general rule turns into the table's ARN: the
   remedy AWS's troubleshooting page gives for a mismatch (*"fix the namespace and name of the dataset
   in the lineage event"*), as a small class in the application that leaves OpenLineage's package as
   released. Not taken: the transformer from the first run, which leaves unread whether it is needed;
   AWS's proxy sample, the transformation in a Lambda behind an API Gateway and a queue, three services
   to do what (b) does. A Glue `environment-properties` facet added to make the domain read the symlink
   is not an option: it tells the catalog a Glue job ran.
4. **The transport.** **Taken 2026-11-16: (a)**, `amazon_datazone_api`: the client calls
   `PostLineageEvent` as the worker's role through the `datazone` endpoint. The role holds the action
   and the endpoint exists; it is the path AWS's blog gives a stream that needs no extra control, and
   the one transformation this stage may need runs in the client (decision 3). Not taken: (b) the HTTP
   transport to AWS's proxy sample, whose endpoint *"uses a public API endpoint with no authentication
   or authorization mechanism"*, which no compute here reaches; (c) a file transport, the events
   written to S3 and posted by a later task.
5. **What a failed post does to the task.** **Taken 2026-11-16: (a)**, the wrapper's default: dbt's
   exit code decides the task and a failed post is a warning in its log, which is also awslabs' runner's
   rule. A transformation that succeeded is not undone by a catalog that did not answer. Not taken: (b)
   strict, the script failing the task when the wrapper logged a failed post; (c) two tasks, each on a
   worker of its own: `transform` runs dbt and saves the artifacts under the application's prefix,
   `lineage` fetches them and runs `dbt-ol send-events`, so a run shows the lineage's state apart from
   the data's and a post is retried without running dbt again. (c) is the form for a pipeline whose
   lineage has to be complete for the run to count as done: Claude brings 3.3's readings back to the
   user, who looks at it again then.
6. **The dbt line.** **Taken 2026-11-16: (a) for now**, in the user's words *"Sugiro seguirmos com a
   versão 1.11 por enquanto."* (a) dbt Core 1.11, pinned by `uv.lock`: the newest line `package-task`
   builds today, under dbt's critical support until 2026-12-18. (b) dbt Core 1.12, in active support
   until 2027-07-15: its parser dependency is published as a source distribution whose build downloads a
   `manylinux_2_28` wheel from dbt's GitHub release for the building machine, which `package-task`
   refuses (0.10); the archive would take that wheel fetched by hand and checked against the hashes the
   source distribution carries, and it asks the worker for glibc 2.28, as this stage's archive does. (c)
   dbt v2: its supported-features page names no Athena, the wrapper reads it through OpenTelemetry
   instead of the artifacts, and its runtime is under dbt's own licence agreement (*"If your organization
   has a strict requirement for an Apache 2.0 licensed runtime, install dbt OSS instead"*). The move to
   (b) stays 6.4's first item, 1.11's support ending inside the stage's own calendar: Claude told the
   user so, and no objection came.
7. **The application, its project and its input.** **Taken 2026-11-16: (a)**, a new application,
   `app-dbt`, Sandbox only, in `eighth-experimentation`, with a Glue task of its own loading the input.
   The project's role is one of `sandbox/workflows/`'s `project_roles`, so the Glue task's `glue:GetJob`
   is granted and the stage applies no Terraform for it, and after Stage 19 step 4.12 the project holds
   the subscription pass 5 reads. Not taken: (b) the same in a new project. Every project has the
   workflow surface, and its Python and Bash tasks run on the blueprint's policies alone; a new
   project's role is absent from `project_roles` until one line and one apply add it, and without them
   the Glue task stops on `glue:GetJob`
   ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §G). A form that gives every
   project the grant with no apply is [open question 27](../open-questions.md), which the user raised
   on this option and left outside the stage. (c) `app-etl` extended with a dbt task: its release
   guard fails a bundle whose export holds an asset `product.json` does not name, and its release G is
   in flight, so nothing of this stage lands in `app-etl-dev`.
8. **The processing-job hypothesis.** **Settled by decisions 2 and 13**: dbt in a processing job is
   compared at the desk and written into the runbook (1.6), in the form decision 13 opens, a job in its
   project's network with the wrapper posting as the project role, and measured by no pass. The form an
   isolated container forced, an engine inside it (`dbt-duckdb` over staged files) and the events
   relayed by a worker task, is left out: its events name files no asset carries.
9. **Promotion.** (a) Sandbox only: one stage, no bundle, no release; (b) the application promoted to
   Staging and Production by the CI/CD CLI, as `app-etl` is. **Recommended: (a)**: whether dbt's lineage
   joins the catalog is answered in Sandbox. What (b) would need is listed for the stage that takes it:
   the worker's archive built and pinned by the pipeline (D28 class (2b)), the task's reach from a
   target's VPC (Athena, Glue, Lake Formation, STS and DataZone, read against each target's `egress/`
   slice), a product database in each deployment project, a `dev` project of the application's own
   (Stage 19 decision 18 (d)), the lint's rules over a Bash task with an archive, the promoted mode having
   retired with release T (Stage 19 item 31), and the lineage's account and domain as stage variables.
10. **Where the catalog's runbook lives.** **Taken 2026-11-16: (a)**, a new
    `docs/plan/runbooks/catalog.md`, with `GOVERNANCE.md` keeping the model and `SMUS.md` the
    mechanism. It is a procedure, read by whoever configures the catalog, in the runbooks' lettered
    form, and §L holds what the request asks of lineage: the capture mechanisms, an event's anatomy,
    how a dataset meets an asset, the dbt case, how events are read and deleted, what fails and how it
    shows. Not taken: (b) sections added to `GOVERNANCE.md`; (c) sections added to `SMUS.md`.
11. **The reading across projects.** (a) after Stage 19 step 4.12, with the subscribed `trades_notional`
    as a model's input; (b) now, with a listing of this stage's own table published from
    `eighth-experimentation` and subscribed from `test-experimentation`; (c) not in this stage.
    **Recommended: (a)**: it reads the graph across a subscription and across accounts with the product
    that exists; (b) adds a listing and a subscription this stage otherwise leaves out, on a project
    Stage 19 is still reading.
12. **The warehouse connection's own lineage capture.** **Moot since decision 1 (a)**: the stage holds
    no warehouse sitting. The capture AWS automates for Redshift stays 6h decision 3's question.
13. **The network isolation of a SageMaker job.** **Taken 2026-11-16**: the direction in the user's
    words (the premises' last quotation), the scope on a card, *"Processing job, nos três ambientes"*.
    (a) `sagemaker:CreateProcessingJob` leaves `DenySageMakerJobsWithoutNetworkIsolation` in Sandbox,
    Staging and Production, wherever the statement is composed (0.14): **taken**. (b) the same in
    Sandbox alone, which gives an application one shape in `dev` and another in a target. (c) the
    statement removed for every job and model. A processing job then runs in its project's subnets and
    security group as the project role and reaches what the workflow's Glue job and worker tasks reach
    there, a space's reach in Sandbox. What stays: a training, tuning or AutoML job and a model under
    the statement, the scope AWS's page on internet-free mode and the Tooling blueprint's
    `enableNetworkIsolation` give network isolation; `DenySageMakerJobsOffVpc`, the instance ceiling,
    inter-container encryption and the volume key on every job; the roles' lack of S3 on the lake's
    registered prefixes (D13); and an application's own choice of isolation, job by job. What goes: the
    guarantee that a processing job's container holds no credentials and touches only its declared
    inputs and outputs. Pass 4 makes the change, and no pass runs dbt in such a job (decision 2).

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
- Pass 4: the applies change policy documents and bill nothing; 4.5's job on `ml.t3.medium` at 0.050
  per hour, and the worker's task-hours while it waits.
- At rest: nothing new. A database, its `DataLake` environment, an asset, a lineage event and a workflow
  are metadata, and the Glue job bills only while it runs. The stage creates no `[E]` resource and, under
  decision 7 (a), applies no Terraform but pass 4's policy documents: a refusal read at 2.1, 2.2 or 2.3
  is brought to the user before any grant is written.

## Rollback

Each write is on the user's word, in this order. The laptop's commands run as `awsds-infra-sandbox-1`
with pass 2's values, in the forms that retired `app-etl` from this project on 2026-11-14 (Stage 19's
sitting), each object read before its delete.

1. **[Claude⚡] The workflows and the Glue job**:

   ```bash
   aws mwaa-serverless list-workflows --profile $P --region us-west-2 --query "Workflows[?starts_with(Name, 'app_dbt_')].[Name, WorkflowArn]" --output text
   aws mwaa-serverless delete-workflow --workflow-arn <each ARN> --profile $P --region us-west-2
   aws glue delete-job --job-name app-dbt-$E --profile $P --region us-west-2
   ```

2. **[Claude⚡] The files under the project's `shared/app-dbt/`**:

   ```bash
   aws s3 ls s3://$B/$D/$E/shared/app-dbt/ --recursive --profile $P --region us-west-2
   aws s3 rm s3://$B/$D/$E/shared/app-dbt/ --recursive --profile $P --region us-west-2
   ```

3. **[user] The assets, then the source**, in the portal, as a member of the project. Each of this
   stage's two assets is deleted, told from the older `trades` by its external identifier (2.4). The
   source is deleted right after them and before its next daily run, which would import the tables again:
   DataZone refuses the delete while an asset the source imported stands (`SUP-366`). The same delete
   from the laptop is a contributor's and unread:

   ```bash
   aws datazone delete-data-source --domain-identifier $D --identifier <the source's id> --profile $P --region us-west-2
   ```

4. **[user] The tables, then the database**, in the project's query editor on *Athena (SQL)*, as the
   project role, one statement a run: a `DROP TABLE` for each table **[Claude]** lists first, pass 5's
   `notional_by_desk_prod` and what a failed swap left among them, then the database.

   ```bash
   aws glue get-tables --database-name app_dbt --profile $P --region us-west-2 --query 'TableList[].[Name, TableType, StorageDescriptor.Location]' --output text
   ```

   ```sql
   DROP TABLE app_dbt.notional_by_desk;
   DROP TABLE app_dbt.trades;
   DROP DATABASE app_dbt;
   ```

5. **[Claude⚡] The `DataLake` environment**, after the database is gone, since its stack keeps the
   database by `Retain` (`SUP-184`):

   ```bash
   aws datazone delete-environment --domain-identifier $D --identifier <the environment's id> --profile $P --region us-west-2
   ```

6. **[Claude⚡] The lineage events**, if xv reads that `DeleteLineageEvent` removes what the graph shows,
   each by its id from 2.3's list:

   ```bash
   aws datazone delete-lineage-event --domain-identifier $D --identifier <an event's id> --profile $P --region us-west-2
   ```

**[Claude] reads** the end by 2.0's block and 2.1's lists: no workflow, no job and no database; `0` under
`shared/app-dbt/`; the project's assets without this stage's two; its environments and sources without
the database's; and the tables' folders with no current object.

What stays: the trails' records; the runs' log groups, which carry no retention
([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §X); the CLI's copies of the archive
under `shared/operatorFiles/`, one for each deploy; the noncurrent versions of the removed objects and of
the dropped tables' files, for the 90 days of the bucket's lifecycle; and whatever xv reads that a
deleted event leaves. Pass 4 is rolled back on its own: each caller's pin returned to the tag it held and
applied by 4.4's commands, the OU document's copy with it, and the battery's `ou` phase run again. A tag
never moves.

## What this stage does not do

- Promote the application: no bundle, no release, no stage but `dev` (decision 9).
- Build an image, or put dbt in the house image.
- Run dbt on Redshift or on Glue with Spark (decision 1), or in a processing job, in several tasks or
  in a Glue job (decision 2): the first two are a later revision's, and the runbook compares the rest.
- Lift the isolation of a training, tuning or AutoML job or of a model, or any other job statement
  (decision 13).
- Enable provisioned MWAA or Airflow's OpenLineage provider (D7), or use dbt's hosted platform.
- Publish a listing or a data product before pass 5, or assign an LF-Tag: the graph needs an inventory
  asset, and the runbook's publication and sharing sections are written from Stage 19's measurements.
- Touch `app-etl`, `app-etl-dev`, a deployment project or a release.
- Change how a project role gets the workflows grant: `sandbox/workflows/`'s list stays as it is, and
  a form that serves every project is [open question 27](../open-questions.md).
- Use the warehouse, admit a second project to it (6h decision 8) or touch the connection's
  `lineageSync` (6h decision 3).

## What concerns the other sessions

- **Stage 19**: this stage adds a database, a source, assets, two workflows and a Glue job to
  `eighth-experimentation`, the consumer of its step 4.12 and the project its instruments read. Pass 5
  here waits on that step and runs before the revocation it ends with. Its step 6.2 rewrites
  [`sagemaker-application.md`](../runbooks/sagemaker-application.md) §N and §W, which 4.6 here edits for
  a processing job: the step that lands second starts from the other's text. Its release G applied
  `production/studio/` on 2026-11-17, before pass 4 (4.4).
- **Every stage whose jobs or checks carry the isolation statement** (pass 4):
  [9](stage-09-deployment-targets.md) step 3.1's design note and 3.5's document,
  [10](stage-10-orchestration-promotion.md)'s rules for a processing task,
  [6i](stage-06i-sandbox-orchestration.md)'s `SO-5`, and 17's training jobs, which keep the statement.
  Pass 4 edits `identity/sso/`, `identity/org-policies/`, `sandbox/sagemaker/`, `staging/studio/` and
  `production/studio/`: a session that holds one of those slices is told first.
- **6f's follow-up**: `GOVERNANCE.md` §Data lineage and the feature table's Lineage cell, rewritten at
  6.2.
- **Stage 11**: 6.3's threat-model entry, with 3.4's readings, and 4.6's.
- **Stages 6d and 17**: a Sandbox sitting of theirs can carry pass 2 with the `mwaa` group added.
- **Stage 17 passes 9 and 10**: they edit `identity/sso/`, `identity/org-policies/`, both `studio/` slices
  and `sagemaker-prereqs`, and read the module's next tag at tagging, so `sagemaker-prereqs-v0.11.0` goes
  to whichever stage tags first, and the four shared slices carry both stages' changes in one apply once
  both are on `main` (Lesson 69).
- **The `awsds-workflows` project** (6.4): a way to hand `package-task` a wheel fetched by hand, for a
  dependency published as a download-at-install source distribution, which it refuses today
  (`dbt-core-experimental-parser`, decision 6 (b)); an `--include` that takes a folder and a destination
  inside the archive, since the dbt project and the `dbt` console script travel as package data until
  then, and a way to keep a console script, which it removes (0.15); `WORKER_PROVIDED` against the
  guide's table of 2026-11-16, which lists `duckdb` 2.0.0 and a DuckDB provider and the Amazon provider
  at 9.38.0 where 9.32.0 was measured; a Bash task's `env` and `append_env`, still unmeasured; and, after
  pass 4, the lint's `job` rule, which refuses a processing task without `EnableNetworkIsolation: true`,
  with the pages and the example that state it. The lint in the authoring mode refused nothing of a
  one-stage application (0.15).

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Log:
[log-stage-20-dbt-lineage.md](../../log/log-stage-20-dbt-lineage.md)*
