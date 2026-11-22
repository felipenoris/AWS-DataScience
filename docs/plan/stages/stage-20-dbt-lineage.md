# Stage 20 — A dbt task in a SageMaker application, and its lineage in the catalog

| | |
|---|---|
| **Status** | **Written 2026-11-16; step 1.1's facts and decisions 1 to 7, 10 and 13 taken the same day; decisions 9 (b) and 11 (a) taken 2026-11-17, 9 moving 7 to (b); the application's draft run against simulated services on 2026-11-17 (0.15, 0.16), pass 1 and 4.1 to 4.3 done the same day with nothing up, 4.4's applies run and 4.6 written after them; the three stages and pass 8, the promotion, written 2026-11-18 with nothing up, 8.4's applies run and decisions 14 to 17 taken the same day; no Sandbox sitting yet** ([log](../../log/log-stage-20-dbt-lineage.md)): the plan, the user's questions answered from dated vendor pages, OpenLineage's released code and this estate's measurements, and each decision in the user's words. dbt runs on Athena, in a Bash task on the worker, on dbt Core 1.11, in a new application `app-dbt` in a Sandbox project of its own, promoted to Staging and Production by the CI/CD CLI (decision 9 (b)), whose passes are written before their sitting; Redshift and Glue with Spark are a later revision's, and a run past the worker's hour is compared in the runbook, measured by no pass. Decision 13 takes a processing job out of the network-isolation statement in Sandbox, Staging and Production, applied 2026-11-17. Pass 1 runs with nothing up; passes 2 and 3 are Sandbox sittings; pass 4 is decision 13's change, a laptop session's tags and applies on the user's word, with the SCP battery; pass 5 waits on [Stage 19](stage-19-smus-native-data-product.md) step 4.12 (decision 11 (a)); pass 8 is a GitLab sitting and a release sitting, R1 or R2 of [`promotion.md`](../runbooks/promotion.md) §N.11. On 2026-11-17: `examples/app-dbt/` written from the stage's prose, step 1.3's three criteria met by the simulation on the laptop's host archive (`aarch64-apple-darwin`, 28,621,986 bytes, 88,429,087 unzipped), 51 tests passing (1.2 to 1.4); `catalog.md`'s first version with 1.6's desk readings (1.5, 1.6); `upstream-releases.md`'s dbt and OpenLineage section (1.7); `sagemaker-denies-v0.3.0` and `sagemaker-prereqs-v0.11.0` tagged at `5f121541`, the callers pinned and the battery's rows written (4.1 to 4.3), each slice planned, then applied on the user's word from 16:01 to 16:09 UTC with `production/registry` first, every re-plan `No changes`, and the battery's processing row authorized and its training row refused, 53 as expected (4.4); the documents and checks that state the rule rewritten and `TM-35` written (4.6). The lint's `job` rule, the item 6.4 hands `awsds-workflows` after pass 4, relaxed the same day by that project's pull request #27, merged as `1a50ceb`, which `app-dbt` pinned until #28's merge. On 2026-11-18, with nothing up: `examples/app-dbt/` extended to the three stages of decisions 7 (b) and 9 (b), with the catalog block, `product.json` and its guard, the pipeline from the template, and the lock cut for Linux and macOS so the gates' `pip-audit` audits every pin; 84 tests passing, the lint *"ok: 4 arquivo(s)"*, and the simulation's thirteen cases as on 2026-11-17; passes 2, 3 and 5 rewritten for the application's own `dev` project, `app-dbt-dev`; pass 8 written, its four `[P]` slices written and planned (8.2); after PR #318's merge, the four applied on the user's word from 10:43 to 10:44 UTC, each re-planned `No changes` (8.4); decisions 14 (a), 15 (a), 16 (c) and 17 (b) taken at 14:02 UTC, and what each changes written with nothing up (8.5): `athena` in both egress slices' `core_services`, each slice planned 17 to add before and 18 after; the stage variable `LINEAGE_NAMESPACE` and `run-dbt.sh`'s `--namespace`, 86 tests passing, the lint *"ok: 4 arquivo(s)"* and the simulation's thirteen cases run again; `awsds-workflows`' change for 17 (b) opened as its pull request #28 on the user's word, and 17 (b)'s change in `app-dbt` written, the simulation run again, and pinned to #28's merge `4613ddc`, the lint *"ok: 4 arquivo(s)"*. 8.1 written on pull request #321, to be merged at R2's opening, R1 having run release G without it on 2026-11-22 (`promotion.md` §N.11.1 step 6, §N.11.2). On 2026-11-19 the user created `app-dbt-dev`, born with the blueprint's domain alone, its role carrying the boundary; its `sandbox/workflows/` line was applied with Stage 17's two on the user's word, `3 added` and re-planned `No changes`, and `CHAIN_DEV_PROJECTS` took its id (2.0, 8.1). The user added its two contributors the same night, and 2.0's starting state read as expected. After pull request #320's merge, 2.0's archive and tar were built from `main` at `103b4acc` and checked, the modes `['0o100755', '0o100755']` and no `._` member, closing 2.0. On 2026-11-19, on the user's word, 8.3's `DataLake` environments created, `deploy-staging-app-dbt` (`bg5ndpa5etujo0`) at 02:23 UTC and `deploy-production-app-dbt` (`adscxpx574cas0`) at 02:27, both `ACTIVE`, each with the database `app_dbt`, its conditioned grants and one daily source, and no subscription target (`SUP-184`); `staging/studio/`'s `product_databases` line applied at 02:27 from 8.3's branch, re-planned `No changes` (8.4). On 2026-11-19, with nothing up, sitting A's pre-flight read the archive and the tar unchanged since `103b4acc`, `app-dbt-dev` as 2.0 left it, `sandbox/workflows/` re-planned `No changes` and the endpoints, `mwaa` the one group the sitting needs; §2 took the sitting's order and its corrected commands, the dbt job's node under `app-dbt-dev` and 4.5's pin `4613ddc`. The same day 4.5's workflow `app-dbt-job`, its script and the manifest's lines were written on pull request #335, 97 tests passing and the lint *"ok: 6 arquivo(s)"*, and the second tar `app-dbt-job.tar` built from its commit `30ab3539`. On 2026-11-21, with nothing up, 2.1 done: `app_dbt` created at 02:42:55 UTC as the project's first `DataLake` environment, with its subscription target, its conditioned grants and its daily source at 02:43, and the editor's create and drop `SUCCEEDED` (the log). On 2026-11-21 sitting A ran in full in Sandbox ([the log](../../log/log-stage-20-dbt-lineage.md)): 2.2 to 2.6, 3.3, 3.4 and 4.5; i to vii, x, xii, xiii and xvi answered by their Sandbox halves (`SUP-391`, `SUP-400`), viii moot since 2.4 read one graph; ix read and decision 5 kept (a) on the user's word; xi yes with a limit (`SUP-402`); xv unanswered, `DeleteLineageEvent` refused to the infrastructure user in both accounts (`SUP-401`), so 7.1 and Rollback's step 6 wait on an identity the root domain unit's owners admit, and 3.4's foreign event stays in `notional_by_desk`'s graph on the user's word. 2.7's downs read 0.0000 USD/h, and `$HOME/tmp/stage20` went to the Trash. On 2026-11-21, after sitting A, 8.6's tree written on [pull request #349](https://github.com/felipenoris/AWS-DataScience/pull/349): `examples/app-dbt/` back at the tree 2.0's archive was built from, 4.5's job off it, the lint pin at `awsds-workflows` `4401f91`; the bundle rehearsed from the laptop before the curation, the guard *"OK"* on the two assets; 5.0's request ordered after 8.8's `bundle` job, in R2 since R1 of 2026-11-22 left pass 8, its link being an asset the bundle would carry (`SUP-197`). Then 8.6's curation saved by Claude through the portal session on the user's word, both assets at revision 5 with their description, README and `classification` `internal`, and the bundle rehearsed after it, the guard *"OK"* on the two assets: 8.6 done for a tag before 5.0. Left: pass 5 after Stage 19's 4.12, on §N.10's day 1; pass 8's remainder in R1 or R2 (`promotion.md` §N.11) before 2026-12-18 |
| **Prerequisites** | [6i](stage-06i-sandbox-orchestration.md) steps 4 and 5, a Python and a Bash task run from a code archive on the worker (2026-10-11), and `awsds-workflows package-task`, which builds that archive ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C). [Stage 19](stage-19-smus-native-data-product.md) pass 1's recipe: a workflow's Glue job writing an Iceberg table into a project database and posting OpenLineage events through Sandbox's `datazone` endpoint (2026-11-10), the graph drawn on the asset's page (2026-11-14). The application's own Sandbox project, `app-dbt-dev` (decision 7 (b)), the user's to create, with the workflows grant once its role joins `sandbox/workflows/`'s `project_roles` (2.0), and spaces on the house image's version 11 with the CI/CD CLI 1.0.9. `sandbox/egress/`'s `athena`, `glue`, `lakeformation`, `sts` and `datazone` endpoints, the first four in the endpoint module's core set and the fifth among the slice's extra services, and its `mwaa` group for a deploy from a space. For pass 4, a laptop session as the infrastructure user and the SCP battery ([`scp-battery.md`](../runbooks/scp-battery.md)). For pass 8, the deploy script taught an application with no image and its workgroup (step 8.1, pull request #321, merged at R2's opening, [`promotion.md`](../runbooks/promotion.md) §N.11.2), the GitLab project `awsds/app-dbt` (8.7), and the hub, GitLab and both targets' egress slices with an `athena` endpoint (decision 15). Nothing blocks pass 1 |
| **Consumes** | [D7](../decisions/D07-orchestration.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D41](../decisions/D41-sagemaker-application.md); [D12](../decisions/D12-budget-ceiling.md) for the cost |
| **Proves** | — (no `INT-nn` row: the worker's post reaches the domain in Data Governance through the `datazone` endpoint a Glue job's lineage already crosses, and no new wiring between accounts is built). What it does prove: whether a dbt project run as a task of a SageMaker application's workflow reads and writes the project's tables through an engine SageMaker Unified Studio itself uses, and whether the OpenLineage events dbt's wrapper posts land on the graph the portal draws for the assets, beside a Glue job's; and, under decision 9 (b), whether the application released by the CI/CD CLI does both in each deployment project |

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
| D41 | the SageMaker application is the deployable unit: `manifest.yaml`, the workflows in the CI/CD CLI's notation, the code | **keep**. `app-dbt` is an application of that shape with three stages, its own `dev` project and the two deployment projects, promoted by the CI/CD CLI (decisions 7 (b) and 9 (b)); `app-etl`, its `dev` project and its releases are not touched, and the deployment projects hold `app-dbt` beside it (pass 8) |

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
| Stage 19's release guard | `examples/app-etl/scripts/check-catalog-export.py` fails a release whose bundle export holds an asset `product.json` does not name, and the CLI's `bundle` exports whatever the `dev` project owns | **keep**, and copied: `app-dbt` carries the same guard over its own `product.json`, the two tables' assets (pass 8); this stage creates nothing in `app-etl-dev` (decision 7) |

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
deployed by the CI/CD CLI from a space into a Sandbox project of its own, the `dev` stage, and promoted
to Staging and Production (decisions 7 (b) and 9 (b)). Its workflow has two tasks, so that the graph has two emitters:

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
├── manifest.yaml             storage items code, glue, samples and workflows; content.catalog; the stages dev, staging and prod
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
├── .gitignore                code/*.zip, artifacts/ and the gates' reports, as examples/app-etl/.gitignore
├── pyproject.toml, uv.lock   dbt-core, dbt-athena and openlineage-dbt, by range and by lock, for Linux and macOS
├── product.json              the two tables' assets and the form classification, what a release carries
├── scripts/check-catalog-export.py  the release guard, the template's copy
├── scripts/dev-cli.sh        the template's copy but its usage line; ./scripts/check-copies.py reads no example
├── .gitlab-ci.yml            the template's pipeline, with no image and no model
├── tests/
└── README.md
```

- **The manifest** names the storage items `code` (the archive alone), `glue`, `samples` and `workflows`,
  each `include` a file or a folder and never a glob; the workflows `app-dbt`, with
  `code: code/app-dbt.zip`, and `app-dbt-probe`, with none, both on `default.workflow_serverless`; the
  catalog block of [Stage 19](stage-19-smus-native-data-product.md) decisions 19 (c) and 20 (b),
  `enabled`, `project.default_lakehouse` and `skipPublish: true` (decision 14); and three stages, one
  account each, the template's: `dev`, the application's own Sandbox project by `${DEV_PROJECT_NAME}`,
  and `staging` and `prod`, `deploy-staging` and `deploy-production`. `dev`'s and `staging`'s bootstraps
  create both workflows; `prod`'s creates `app-dbt` alone, then runs it and follows the run
  (`trailLogs`), so a release ends with both tables written in Production. Each stage's
  `environment_variables` are what the workflows read as `{env.NAME}`, declared by every stage since the
  deploy resolves every workflow the manifest names: `SUBNET_AZ1` and `SUBNET_AZ2` for the Glue job's
  connections, `ACCOUNT_ID`, `PRODUCT_DATABASE` (the literal `app_dbt`), the switches the readings
  turn, `LINEAGE_DOMAIN`, `LINEAGE_NAMES`, `LINEAGE_ENDPOINT` and `LINEAGE_ATTEMPTS`, and
  `LINEAGE_NAMESPACE` (decision 16 (c)). The Athena workgroup is no stage variable: both workflows name
  `{proj.connection.project.athena.workgroupName}`, the project's `project.athena` connection's, which
  the CLI resolves at the deploy (decision 17 (b)). In `dev` every one but the literal comes from the
  shell as `${NAME}`, and the CLI refuses a manifest whose variable is unset or empty
  ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D), so a switch at rest holds a
  word: `default` for the endpoint and for the attempts. A target reads `${<PREFIX>_SUBNET_AZ1}`,
  `${<PREFIX>_SUBNET_AZ2}` and `${<PREFIX>_ACCOUNT_ID}`, which its leg fills from the deployment project
  (8.1); `${DOMAIN_ID}` for `LINEAGE_DOMAIN`; its switches as literals: `as-built`, or `glue-arn` once
  3.1 reads a split graph, and `default`; and its namespace, `app-dbt-staging` or `app-dbt-prod`, where
  `dev` exports `app-dbt-dev`.
  `tests/test_manifest.py` holds each stage to that list.
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
  bash_command: "bash /usr/local/airflow/dags/run-dbt.sh --region '{domain.region}' --account '{env.ACCOUNT_ID}' --database '{env.PRODUCT_DATABASE}' --workgroup '{proj.connection.project.athena.workgroupName}' --domain '{env.LINEAGE_DOMAIN}' --names '{env.LINEAGE_NAMES}' --endpoint '{env.LINEAGE_ENDPOINT}' --attempts '{env.LINEAGE_ATTEMPTS}' --namespace '{env.LINEAGE_NAMESPACE}'"
  ```

  The command starts `bash` on the script by its full path, so the mode the worker's extraction leaves on
  the file plays no part, and the options follow, each value in single quotes: the command never ends in
  `.sh`, which the operator reads as the name of a template file (0.1). `LINEAGE_DOMAIN` is the domain's
  id, `LINEAGE_NAMES` is `as-built` or `glue-arn`, `LINEAGE_ENDPOINT` a URL or `default`,
  `LINEAGE_ATTEMPTS` a number, exported as botocore's `AWS_MAX_ATTEMPTS`, or `default`, and
  `LINEAGE_NAMESPACE` the job namespace of the run's events (decision 16 (c)). The CLI fills
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
  `--namespace`'s value, `app-dbt` when the option is left out (2.6); reads the product database's
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
- **What it leaves out**: an image (a workflow of a Glue task and a worker task needs none), a job, a
  model, and a publication: the catalog block imports the `dev` project's two assets into each target's
  project and lists nothing (decision 14). An inventory asset is enough for a graph.

## The catalog's runbook, section by section

`docs/plan/runbooks/catalog.md` (decision 10) is the procedure the request asks for: how the catalog is
configured and used, for whoever defines an asset, builds a data product, publishes, shares between
projects or reads a lineage graph. [`GOVERNANCE.md`](../../GOVERNANCE.md) keeps the model and
[`SMUS.md`](../../SMUS.md) the mechanism, and the runbook points at both. Step 1.5 writes it from what is
already measured, and step 6.2 completes §L with this stage's readings.

| Section | What it answers | Written from |
|---|---|---|
| §O The pieces | where the domain lives and what a project is in it; the three catalogs and what each decides; the catalog's objects (asset, revision, listing, data product, data source, subscription, metadata form, glossary, lineage node); who may do what, by project designation and by domain unit | `GOVERNANCE.md` §Catalogs, `SMUS.md` §The catalog surface, 6f step 1 |
| §A Assets | the ways an asset comes to exist: a project database imported by its `DataLake` environment's source, on its daily schedule or a member's run; a source over another Glue database, typed by name; a Redshift source; an asset created by hand (*"a one-time operation"*); a custom asset type through the API. The inventory against the published catalog, a revision, the `sourceIdentifier` an asset carries, what creating a source writes (Lake Formation grants and the discoverability tag), and the order a deletion takes (`SUP-366`) | 6f step 3, Stage 19 pass 1 and its retirement, AWS's pages on a Glue source and on an asset created by hand (read 2026-11-16), this stage's pass 8 |
| §M Business metadata | names, descriptions and the README; the generated names and the switch that keeps the generation off (6f decision 3); glossaries and terms; metadata forms, the project that owns one, and a domain unit's rule that requires one at publishing | 6f steps 4 and 5, Stage 19 decision 4 |
| §P Data products | a product against an asset; building one from assets, publishing and republishing it; its name being the domain's (`SUP-369`); what a subscriber gets from one request; how the CI/CD CLI carries a product between projects | Stage 19 passes 2 to 4 |
| §F The publication flow | from a table to a listing, act by act: the import, the curation, *Publish*, with `publishOnImport` as the short cut; who may publish; the approval switch on a listing; what publishing writes and what it leaves alone (no grant, no LF-Tag); unpublishing | 6f step 11, Stage 19 passes 1 and 2 |
| §S Sharing between projects | a subscription from request to grant: the request, the approval and when it is automatic, the fulfilment for a managed Glue or Redshift asset and the event for an unmanaged one; what lands in the consumer project (the resource link, the grant under the project's context); row and column filters; the Direct Share (`SUP-362`); a subscription across accounts; a revocation and what it leaves; what the catalog does not do (a grant by LF-Tag, a share across Regions, a subscription to a resource link) | 6f step 11, Stage 18 7.2, Stage 19 pass 2 |
| §L Lineage | the capture mechanisms, one by one, with what each needs (question 1's table); an event's anatomy; the node types and the rule that names a node; how a dataset meets an asset; a Glue job's settings; the dbt case from the project to the graph: the wrapper, the transport, the names, the archive, a failed post, and the forms that carry a run past the worker's hour; dbt's docs site against the catalog's graph; reading a graph (the *Lineage* tab, `ListLineageEvents`, `GetLineageNode`, `QueryGraph`) and deleting an event; who may post and who may read; the limits, and how each failure shows | Stage 18 7.1, Stage 19 verification v, this stage's passes 2, 3, 5 and 8 |
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
TOOL="awsds-workflows @ https://github.com/felipenoris/awsds-workflows/archive/37cb5a6260c8348cc208988e42090caf42a3a207.zip"
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

A Sandbox sitting under [`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D's rules,
sitting A of [`promotion.md`](../runbooks/promotion.md) §N.6 item 4. The user raises the hub and
`sandbox/egress/` with its `mwaa` group, which a deploy from a space needs; the application reaches a
space of its own `dev` project, `app-dbt-dev` (decision 7 (b)), as a tar with the archive inside, so
GitLab and the tunnel stay out of it; the deploy and the runs go through `scripts/dev-cli.sh`, which
gives the `staging` and `prod` stages' names a placeholder. The project's name is the user's at its
creation, `app-dbt-dev` in this file: the workflows' names below compose it, each `-` an `_`. Steps 2.0
and 2.1 need nothing up, as the same acts needed nothing in
[Stage 19](stage-19-smus-native-data-product.md), `app-etl-dev`'s creation and *Create database*, and the
query editor on 2026-11-14. The window opens at 2.2 and closes at 2.7, and Cost carries what it bills.

**The identities.** The laptop's commands are [Claude]'s reads as the infrastructure user in
`Sandbox Account 1`, permission set `InfrastructureAccess`, profile `awsds-infra-sandbox-1`. A lineage
node's id is read from `Data Governance`'s trail, the same user and set, profile `awsds-infra-data`. One
login covers both profiles and is the user's act. The portal, the space and the query editor are the
user's, as the owner of `app-dbt-dev`, and every command of the space runs as the project role.
With the tunnel down, each `aws` command of the laptop takes `NO_PROXY='*'` before it. The laptop's shell
is zsh (Lesson 84): the blocks below quote every `--query` and split no variable.

**The values** each laptop block starts from, and **a run's reading**, which each step repeats with its
own workflow's name ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §V): a task's
`Status` and `DurationInSeconds` are read, since the run's `RunState` lags its tasks, and a task's text
is the stream its `LogStream` names.

```bash
D=dzd-d8yrvx1ko7im6o; E=dnl3l158mbhrio; P=awsds-infra-sandbox-1; B=awsds-sandbox-smus-projects; WG=workgroup-dnl3l158mbhrio-55hp9teamegf4g
```

The two ids are the two segments of the project role's name, `datazone_usr_role_<project id>_<Tooling
environment id>`, which 2.0 reads: `app-dbt-dev`'s, read again on 2026-11-19 at 15:01 UTC.

```bash
N=app_dbt_app_dbt_dev_app_dbt_probe
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

**Sitting A in order.** The combined Sandbox sitting carries this pass, pass 3 and 4.5 on its first day
(§N.6 item 4), after 6d decision 6's reading ([`promotion.md`](../runbooks/promotion.md) §N.9.3), and
Stage 17's sittings B and C on the next two (§N.6 item 7). The pre-flight of 2026-11-19, with nothing up, read every input as 2.0 left it (the log). The sitting ran in full on 2026-11-21, 2.1's source at 02:43 UTC (the log). [user] is the
user's act, [Claude] a read, [Claude⚡] a write Claude runs on the user's word naming it. `GROUPS` names
the optional endpoint group a row needs beside `sandbox/egress/`'s always-on endpoints, which carry
Athena, Glue, Lake Formation, STS, ECR, `datazone` and `sagemaker.api`, S3 going through the `[P]`
gateway; `none` marks a row that calls from the VPC through those alone, and `-` a row that calls nothing
from it. The commands are each step's own.

| Order | Hand | Step and what runs | `GROUPS` | What it closes |
|---|---|---|---|---|
| 1 | [user] | 2.1, with nothing up: *Data → Create database* `app_dbt` in `app-dbt-dev`, then the editor's create and drop of `editor_probe` | - | the database 2.3 writes into; iii's editor half |
| 2 | [Claude] | 2.1's reads, the source's daily minute among them | - | the minute the sitting's runs keep clear of |
| 3 | [Claude] | 4.5's workflow, its script and the manifest's lines on a branch no tag carries, pass 1's tests and the lint at `4613ddc`, then a second archive and tar from that branch's commit by 2.0's commands | - | the tar 4.5 deploys: `app-dbt-job.tar`, built 2026-11-19 from commit `30ab3539` |
| 4 | [Claude] | The laptop's other sessions told before the first raise; `make status` | - | - |
| 5 | [user] | `make hub-up` | - | the proxy a space and a job reach |
| 6 | [user] | `make up ENV=sandbox GROUPS=mwaa`, day 1's raise (§N.9.2), which raises `sandbox/egress/` and `sandbox/probes/`; [Claude] `make status` | `mwaa` | the `airflow-serverless` endpoint every deploy and run from a space calls |
| 7 | [user] | 2.2: a JupyterLab space in `app-dbt-dev`, `app-dbt.tar` checked and extracted, the values, the deploy, the probe's run | `mwaa` | i's worker half, ii's first half, the endpoint's answer to `ListLineageEvents` |
| 8 | [Claude] | 2.2's reads: the copies, both workflows, the probe's run and log, the trail | - | - |
| 9 | [user] | 2.3: `app-dbt`'s run; [Claude] 2.3's reads | `mwaa` | i's modes, ii, iii's worker half, iv, v |
| 10 | [user] | 2.4: the source's *Run* in the portal, each table's *Lineage* tab; [Claude] 2.4's reads | - | vi, vii, xvi; one graph is 3.1's verdict, `as-built` staying in the targets |
| 11 | [user] | 2.5: the run and the source again; [Claude] 2.5's reads | `mwaa` | x |
| 12 | [user] | 3.1, on a split graph alone: `glue-arn` exported, the run, the source; [Claude] 3.1's reads | `mwaa` | viii; one graph is 3.1's verdict, `glue-arn` in the targets before pass 8's tag; neither form linking stops the stage (3.2) |
| 13 | [user] | 3.3: the three failing runs, each after its `export`, then the switches back at rest; [Claude] each run's reads | `mwaa` | ix, decision 5's input |
| 14 | [user] | 2.6, if the sitting has room: the archive run by hand in the space, `-- debug` then `-- run`; [Claude] the trail | none | the development loop |
| 15 | [user] | 3.4: a space of `test-experimentation`, the foreign event posted, the node read; [Claude] the answers; [Claude⚡] the event's delete | none | xi, xv |
| 16 | [user] | 4.5: `app-dbt-job.tar` in the space, §D step 3's values with the image's URI typed, the deploy, the run; [Claude] 4.5's reads | `mwaa` | xii's Sandbox half, xiii |
| 17 | [user] | 2.7: both spaces stopped, every portal tab closed, `make down ENV=sandbox`, `make hub-down`; [Claude] `make status`, §R's readings | - | zero burn |

- **2.0 Before the sitting, with nothing up**: the project, its grant and its image, then the starting
  state, the archive and the tar.
  - **[user] The project** `app-dbt-dev`, from the `experimentation` profile in the portal after 6d step 2.7's
    step 5, born with the blueprint's domain alone (the user, 2026-11-18), as `app-etl-dev` was ([Stage 19](stage-19-smus-native-data-product.md) step 1.5), and its members: the
    bundle role `awsds-deploy-sandbox-test`, which `bundle` reads the project as (8.6), and Sandbox's
    `InfrastructureAccess`, whose session reads the project from the laptop, both
    `PROJECT_CONTRIBUTOR`, added in the portal's member dialog, which lists a role's group by the role's
    name (Stage 19 item 17, 2026-11-14). The waiting list holds the act. **Created 2026-11-19** by the
    user at 00:17 UTC, born with the blueprint's domain alone; its members, read at 00:20, were the owner
    and the project's own role. **The contributors added 2026-11-19** by the user: at 00:54 UTC the
    project lists the bundle role's group (`06d426f2-…`) and Sandbox's `InfrastructureAccess` group
    (`839bcde8-…`), both `PROJECT_CONTRIBUTOR`, as `app-etl-dev` does.
  - **[Claude] The project read**: its id, its `Tooling` environment `ACTIVE`, its role, its workgroup
    and its members.

    ```bash
    aws datazone list-projects --domain-identifier $D --name app-dbt-dev --profile $P --region us-west-2 --query 'items[].[id,name]' --output text
    aws datazone list-environments --domain-identifier $D --project-identifier $E --profile $P --region us-west-2 --query 'items[].[id,name,status]' --output text
    aws iam list-roles --profile $P --query "Roles[?starts_with(RoleName, 'datazone_usr_role_$E')].RoleName" --output text
    aws iam get-role --role-name <the role> --profile $P --query Role.PermissionsBoundary.PermissionsBoundaryArn --output text
    aws datazone list-connections --domain-identifier $D --project-identifier $E --type ATHENA --profile $P --region us-west-2 --query 'items[].[connectionId, name, props.athenaProperties.workgroupName]' --output text
    aws datazone list-project-memberships --domain-identifier $D --project-identifier $E --profile $P --region us-west-2 --query 'members[].[designation, memberDetails.group.groupId || memberDetails.user.userId]' --output text
    ```

    Expected: the workgroup `workgroup-<project id>-<Tooling environment id>`, the role's two segments,
    and the role carrying `awsds-sandbox-project-boundary`, the precondition the next act's slice reads.
    `list-roles` omits `PermissionsBoundary` by documented contract, so the boundary is read with
    `get-role`.

    **Read 2026-11-19** at 00:20 UTC: the id `dnl3l158mbhrio`; `Tooling` `55hp9teamegf4g` and
    `SageMakerAIDomain` `4mxdm39fu4j05s`, both `ACTIVE`; the role
    `datazone_usr_role_dnl3l158mbhrio_55hp9teamegf4g`, carrying `awsds-sandbox-project-boundary`.
    `list-connections` was refused to the infrastructure user with DataZone's own wording, *"User is not
    permitted to perform operation: ListConnections"*, while the same call on `app-etl-dev`, whose
    members include that user's role, answered at 00:32. After the membership it answered at 00:55:
    `project.athena`, `workgroup-dnl3l158mbhrio-55hp9teamegf4g`.
  - **[Claude⚡] The workflows grant**, on the user's word naming the apply: `sandbox/workflows/`'s
    `project_roles` gains the role's name in `variables.tf`'s `default`, with a comment line naming the
    project, its creation date and its reading, as `app-etl-dev`'s does; planned after the project
    exists, since the slice reads each listed role with `data "aws_iam_role"`, which fails at plan for a
    role that does not exist, and applied as `awsds-infra-sandbox-1`, then re-planned `No changes`.
    Without it `load` stops on `glue:GetJob`
    ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §G). The slice's list is
    [open question 27](../open-questions.md)'s subject, which the line does not change.
    **Written and planned 2026-11-19**, with [Stage 17](stage-17-sandbox-machine-learning.md)'s lines for
    `app-ml-dev` and `app-genai-dev`: *"Plan: 3 to add, 0 to change, 0 to destroy."* at 00:29 UTC, the
    three attachments of `awsds-sandbox-workflows`. **Applied 2026-11-19** on the user's word, *"Apply
    complete! Resources: 3 added, 0 changed, 0 destroyed."* at 00:49:48 UTC, re-planned *"No changes."*
  - **[Claude⚡] The house image on the project's domain**, by
    [`dev-env.md`](../runbooks/dev-env.md) §C6, as release T's item 33 attached it for `app-etl-dev`,
    if the project's SageMaker AI domain does not list `awsds-sandbox-dev-env` version 11 after its
    creation: the space at 2.2 runs the CLI 1.0.9 from that image. **Not needed**: the project's domain
    `d-nt4ujzbdpeqm` pins version 11 on both app types from its creation (`US-13`, 2026-11-19).

  **[Claude] The starting state**, then the archive and the tar:

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
  three times; and no asset, the project being new. An object under `dev/data/catalogs/trades/`, where
  the Glue job's table lands (0.7), would be an earlier table's and goes to the user before the sitting.
  **Read 2026-11-19** at 00:55 UTC, each as expected: the workgroup `ENABLED`, enforced, on Athena engine
  version 3, its output under the project's `dev/sys/athena/`; `EntityNotFoundException` for the
  database and for the job; no workflow; `0` three times; no asset.

  The archive is built on the laptop from the merged tree, outside the repository, with the `TOOL` of the
  application's README, `awsds-workflows` at `4613ddc` (decision 17 (b)), and travels inside the tar, whose flags keep macOS's AppleDouble members out (`SUP-348`). An archive
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
  no `._` member. **Passed 2026-11-19** at 01:07 UTC, from `main` at `103b4acc`, pull request #320's
  merge: `package-task` *"26129224 bytes, 82844295 descompactados"*, 1.4's check
  `5102 82844295 ['0o100755', '0o100755']`, and the tar, 26,531,328 bytes, `51 37 []`; the log holds both
  digests. A rebuild during a sitting that fails on the laptop is built in the space before the deploy,
  which no sitting has done ([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §C2).
- **2.1 [user] Create the database `app_dbt`**, still with nothing up, in `app-dbt-dev` (*Data → Create
  database*), then the editor's baseline: in the project's query editor on *Athena (SQL)*, as
  the project role, the statement 2.3's model repeats from a worker, an Iceberg table created under the
  database's location, and its drop.

  ```sql
  CREATE TABLE app_dbt.editor_probe WITH (table_type='iceberg', is_external=false, location='s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/<the project's id>/dev/data/catalogs/app_dbt/editor_probe', format='parquet') AS SELECT 1 AS n;
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
  `ACTIVE`; the database described *"Created by DataZone for project app-dbt-dev"*, at
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/<the project's id>/dev/data/catalogs/`, with no
  default table permission; `IAMPrincipals` under the project's condition holding `CREATE_TABLE`,
  `DESCRIBE` and `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT`
  on its tables; a source on a daily cron at the minute of its creation, `publishOnImport` false, its
  filter naming `app_dbt`, hanging from the project's `project.default_lakehouse` connection, whose
  `glueLineageSyncEnabled` read `true` on each project's on 2026-10-18, never updated since creation
  ([`SMUS.md`](../../SMUS.md) §The catalog surface);
  both statements `SUCCEEDED`, and no current object under the dropped table's folder. The trail's
  `CreateTable` and `DeleteTable` (the loop above) give the session and the grant that admitted each
  (iii's baseline). A later sitting keeps its runs clear of the source's minute. If the editor's create
  is refused, the stage stops for the user with the refusal: 2.3 asks the same of a worker. Done
  2026-11-21 (the log). The portal's refusal naming the project profile, met first in `app-genai-dev`, is
  `SUP-390`'s: the project the portal has open is read before the act.
- **2.2 [user] The raises, the space, the deploy and the probe.** From the project folder, `make hub-up`,
  then

  ```bash
  make up ENV=sandbox ONLY=egress GROUPS=mwaa
  ```

  In the combined Sandbox sitting the raise is day 1's `make up ENV=sandbox GROUPS=mwaa`
  ([`promotion.md`](../runbooks/promotion.md) §N.9.2); with no `ONLY=` it raises `sandbox/probes/` beside
  `sandbox/egress/`, and a group other than `redshift` changes no slice (the pre-flight's `DRY=1` of the
  single start's raise, 2026-11-19; `scripts/slices.py`'s refusal 11). **[Claude]** tells the laptop's other sessions before the first raise and
  reads `make status` after the second. Then a JupyterLab space in `app-dbt-dev` on
  `awsds-sandbox-dev-env` version 11 (alias `0.10.0`), `ml.t3.medium`, the tar dropped on its file
  browser, and in its terminal the tar checked against the digest 2.0 built before it is extracted:

  ```bash
  echo '0b3ad0f98ed46af809cb539df0102f3c715723b9d07a868aad9192f41c21a1c8  app-dbt.tar' | sha256sum -c && tar -x -f app-dbt.tar && cd app-dbt
  ```

  The values the manifest's `dev` stage reads, §D step 3 without an image or a key; the project's name
  is typed, as 2.0 read it. The workgroup is no stage variable (decision 17 (b)), and 2.6's run by hand
  alone types it. The clone's head is read against the pin, `4613ddc`, which `awsds-workflows`' `main`
  held on 2026-11-19:

  ```bash
  git clone --depth 1 https://github.com/felipenoris/awsds-workflows /tmp/awsds-workflows
  git -C /tmp/awsds-workflows log -1 --format=%h
  /opt/conda/bin/python /tmp/awsds-workflows/scripts/space_values.py > /tmp/space_values.json
  eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); print("\n".join("export %s=%s" % p for p in (("DOMAIN_ID", v["DOMAIN_ID"]), ("DOMAIN_REGION", v["REGION"]), ("SUBNET_AZ1", v["SUBNET_AZ1"]), ("SUBNET_AZ2", v["SUBNET_AZ2"]), ("ACCOUNT_ID", v["ACCOUNT_ID"]))))')"
  export DEV_PROJECT_NAME=app-dbt-dev
  export LINEAGE_DOMAIN="$DOMAIN_ID" LINEAGE_NAMES=as-built LINEAGE_ENDPOINT=default LINEAGE_ATTEMPTS=default
  export LINEAGE_NAMESPACE=app-dbt-dev
  ```

  The deploy (§D step 6), which a line *"No custom VPC config"* stops, and the probe's run (§D step 7);
  `dev-cli.sh` gives every `STAGING_` and `PROD_` name a placeholder, and the `dev` stage reads none:

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
  for N in app_dbt_app_dbt_dev_app_dbt app_dbt_app_dbt_dev_app_dbt_probe; do W=$(aws mwaa-serverless list-workflows --profile $P --region us-west-2 --query "Workflows[?Name=='$N'].WorkflowArn | [0]" --output text); aws mwaa-serverless get-workflow --workflow-arn "$W" --profile $P --region us-west-2 --query '[Name, WorkflowVersion, WorkflowStatus, NetworkConfiguration.SubnetIds, NetworkConfiguration.SecurityGroupIds, EncryptionConfiguration.Type, LoggingConfiguration.LogGroupName]'; done
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

  **[Claude] reads** the run with `N=app_dbt_app_dbt_dev_app_dbt`, both tasks and
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
  namespace `app-dbt-dev` (decision 16 (c)), posted through the
  endpoint by the worker's session, beside the Glue job's (v);
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
  aws datazone get-lineage-node --domain-identifier $D --identifier 'app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run' --profile $P --region us-west-2 --query '[id, typeName, sourceIdentifier, formsOutput[].formName, upstreamNodes[].id, downstreamNodes[].id]'
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateLineageNode --start-time <2.3's first minute> --profile awsds-infra-data --region us-west-2 --query 'Events[].CloudTrailEvent' --output json | jq -r '.[] | fromjson | [.eventTime, (.additionalEventData | tostring)] | @tsv'
  ```

  This stage's assets are the project's two, whose external identifiers end
  `table/app_dbt/trades.<the project's id>` and `table/app_dbt/notional_by_desk.<the project's id>`
  (`SUP-343`). An asset's node answers to `amazon.datazone.asset/<asset id>`, a job's to
  `<namespace>.<name>`, the dbt job's namespace `app-dbt-dev` in `dev` (decision 16 (c)), and every
  other node to its id alone, which `Data Governance`'s trail gives with
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
  export ATHENA_WORKGROUP=workgroup-dnl3l158mbhrio-55hp9teamegf4g
  PYTHONPATH=/tmp/app-dbt-hand bash /tmp/app-dbt-hand/run-dbt.sh --region us-west-2 --account "$ACCOUNT_ID" --database app_dbt --workgroup "$ATHENA_WORKGROUP" --domain "$LINEAGE_DOMAIN" --names "$LINEAGE_NAMES" --namespace app-dbt-by-hand -- debug
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
  the graph is one, `LINEAGE_NAMES` stays `glue-arn` for the rest of the stage, and the `staging` and
  `prod` stages' literal becomes `glue-arn` in the manifest before pass 8's tag, with
  `tests/test_manifest.py`'s expectation.
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
  as that project's role, a project outside `app-dbt-dev`. The event's output is the pair of names under which 2.4 or 3.1 read the model's
  node, the namespace's account id typed in the space and never written down:

  ```bash
  python3 -c 'import datetime, json, sys, uuid; print(json.dumps({"eventType": "COMPLETE", "eventTime": datetime.datetime.now(datetime.timezone.utc).isoformat(), "run": {"runId": str(uuid.uuid4())}, "job": {"namespace": "stage-20-foreign", "name": "foreign-writer"}, "inputs": [], "outputs": [{"namespace": sys.argv[1], "name": sys.argv[2]}], "producer": "https://example.com/stage-20-foreign", "schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"}))' '<the namespace>' '<the name>' > /tmp/foreign-event.json
  ```

  ```bash
  aws datazone post-lineage-event --domain-identifier dzd-d8yrvx1ko7im6o --event fileb:///tmp/foreign-event.json --region us-west-2
  ```

  ```bash
  aws datazone get-lineage-node --domain-identifier dzd-d8yrvx1ko7im6o --identifier 'app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run' --region us-west-2 --query '[id, typeName, formsOutput[].formName]'
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

  Since 2026-11-17 `identity/sso/` and both `studio/` slices also carry [Stage 17](stage-17-sandbox-machine-learning.md)
  9.5's change, merged in the same pull request and applied with this one (Lesson 69): `identity/sso/`'s
  `data_scientist_prod` set names `awsds-prod-ecr-app-ml`, so `production/registry/` applies before
  `identity/sso/`, whose apply reaches `Data Governance` through the governance managers' set, which the
  user is told before it. Each row is Recipe A's steps 3 to 7, from `main` once it holds commit 2 (Lesson 79), the plan kept
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
  tags between, beside Stage 17 9.5's statements on the three slices that carry them; the second plan reads
  `No changes`. A plan that carries another stage's unapplied change
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
  stays as it is (xii). **Done 2026-11-17**: `production/registry/` at 16:00:08 UTC, then the five rows
  at 16:01:26, 16:02:03, 16:07:18, 16:08:13 and 16:09:05 UTC, each re-plan *"No changes."*; the battery
  from 16:03:10 UTC, *"53 as expected, 0 unexpected, 5 not measured"*, the processing row `ALLOWED` and
  the training row `DENY-SCP`; `DT-11` passing with the six job Sids; `make check` OK (the log).
- **4.5 [user] A processing job without isolation, in Sandbox**, in a sitting raised as 2.2's: a third
  workflow of `app-dbt`, `app-dbt-job`, one `SageMakerProcessingOperator` task on the house image, in
  the project's subnets and security group, with `EnableNetworkIsolation: false` and the statement's
  other settings as the template sends them. The deploy resolves every workflow the manifest names, so
  every stage declares its variables, `dev` the template's `DEV_PROJECT_SG` and `DEV_PROJECT_KEY_ARN`
  (§D step 3's line) and the image's URI, typed in the space and never written down, and each target its
  leg's `${<PREFIX>_PROJECT_SG}` and `${<PREFIX>_PROJECT_KEY_ARN}` with the image `none`. Its code is the
  storage item `job`, which every stage copies, since the lint's `codigo` rule reads a job's code input
  under a folder every stage copies. `dev`'s bootstrap alone creates it, and the workflow, its folder and
  their lines leave the tree before pass 8's tag (8.6), no target running a processing job of this
  stage. `awsds-workflows lint` at `app-dbt`'s pin `4613ddc` passes it: that commit carries `1a50ceb`'s
  `job` rule, which leaves the isolation to the task (6.4). Its script, `job/probe.py`, prints the
  caller's identity, a `SELECT 1` through the project's Athena workgroup, the product database as Glue
  returns it, `ListLineageEvents` on the domain, and what the proxy answers a request for a name on
  Sandbox's allow-list and for one off it, the pair `sandbox/probes/` requests: `https://pypi.org/`, and
  `http://example.com/`, a name no plane carries, never the domain's own URL, which 6d decision 6's
  `production/networking/` apply of 2026-11-20 added to Sandbox's plane. **Written 2026-11-19** with
  nothing up, commit `30ab3539` on pull request #335, whose squash merge carries it into `main` as
  `399f3365`: 97 tests passing, 11 of them the job's; ruff clean; the lint with the pipeline's instance types *"ok: 6
  arquivo(s)"*, refusing a copy with the encryption off (`job`) and a copy with the folder `job` in `dev`
  alone (`codigo`), and passing a copy with the isolation on. The image's pull, read the same day:
  Production's repository policy grants Sandbox Account 1 the pull actions, and
  `simulate-principal-policy` with `aws:RequestedRegion` (`SUP-008`) reads the project role's
  `BatchGetImage`, `GetDownloadUrlForLayer` and `GetAuthorizationToken` allowed by
  `SageMakerStudioProjectRoleMachineLearningPolicy`, whose create statement the role's
  `EnableSageMakerMLWorkloadsPermissions` `true` and the project tag satisfy.

  The second tar comes from that commit by 2.0's commands, in `$HOME/tmp/stage20/job/` beside 2.0's,
  which stays for 2.2 to 3.4: the archive 26,129,645 bytes, 1.4's check `5102 82845727 ['0o100755',
  '0o100755']`, 2.0's names with four entries of `app_dbt-0.1.0.dist-info/` apart, the README its
  metadata embeds among them; the tar `app-dbt-job.tar`, 26,556,928 bytes, `55 40 []`. In the space, the
  tar is checked and extracted beside the first tree:

  ```bash
  echo '903847a55dcc1b1510ccd4b0f0413c7e181e744ebe7215b9b1c86e59fb279abe  app-dbt-job.tar' | sha256sum -c && mkdir -p job && tar -x -f app-dbt-job.tar -C job && cd job/app-dbt
  ```

  2.2's values, its block run again in a terminal that no longer holds them, then the three names the job
  reads: the project's group and key from the same file, the key's ARN as §D step 3's line builds it, and
  the house image by digest, version 11's in Production's registry (`sha256:658c05d1…`), which the laptop
  reads and the user types:

  ```bash
  aws sagemaker describe-image-version --image-name awsds-sandbox-dev-env --version-number 11 --profile $P --region us-west-2 --query ContainerImage --output text
  ```

  ```bash
  eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); print("export DEV_PROJECT_SG=%s DEV_PROJECT_KEY_ARN=arn:aws:kms:%s:%s:key/%s" % (v["PROJECT_SG"], v["REGION"], v["ACCOUNT_ID"], v["PROJECT_KEY_ID"]))')"
  export JOB_IMAGE_URI="<the house image by digest>"
  ```

  The deploy and the run are 2.2's commands with the workflow's name:

  ```bash
  scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
  ```

  ```bash
  scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt-job
  ```

  **[Claude] reads** the copies and the workflows by 2.2's commands with the third name,
  `app_dbt_app_dbt_dev_app_dbt_job`, seven objects under `shared/app-dbt/` with `job/probe.py`; the run
  by pass 2's blocks; the job's description, its log and its calls in Sandbox's trail, by the session
  `SageMaker` (xii, xiii):

  ```bash
  aws sagemaker list-processing-jobs --name-contains app-dbt --max-results 3 --profile $P --region us-west-2 --query 'ProcessingJobSummaries[].[ProcessingJobName, ProcessingJobStatus, CreationTime]' --output text
  aws sagemaker describe-processing-job --processing-job-name <the job's name> --profile $P --region us-west-2 --query '[ProcessingJobStatus, FailureReason, NetworkConfig, ProcessingResources.ClusterConfig, RoleArn]'
  aws logs filter-log-events --log-group-name /aws/sagemaker/ProcessingJobs --log-stream-name-prefix <the job's name> --profile $P --region us-west-2 --query 'events[].message' --output text
  ```

  The step passes when the job is created, which the statement refused before 4.4, and ends `Completed`
  with each call answered, the proxy reading HTTP 200 for `pypi.org` and HTTP 403 for `example.com`, as
  `sandbox/probes/` expects them. A target's half of xiii is a reading of [`NETWORK.md`](../../NETWORK.md) until
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
  `awsds_demo_job/__main__.py`'s docstring, *"runs every job isolated"*. **Done 2026-11-17**, after
  4.4: each text above, Stage 9's 3.5 and Stage 10's rule for the caller of a job; `SO-5` reports a job
  without isolation as a note and `ML-6` no longer reads a Processing step's; `TM-35` accepted with
  decision 13, in the ledger and the network matrix.

### 5. Across projects

Waits on Stage 19 step 4.12, Production's listing of `trades_notional` approved for a Sandbox project
(decision 11 (a)). Stage 19's consumer is `eighth-experimentation`, and under decision 7 (b) the model
reads through `app-dbt-dev`'s own subscription, a second request on the same listing. It runs while that
listing is live, before the revocation step 4.12 ends with, the two sessions agreeing on the order. It
rides [`promotion.md`](../runbooks/promotion.md) §N.10's day 1 (§N.10.3 step 8), raised with
`GROUPS=redshift,mwaa`, after the subscriptions of §N.6 item 6, and is read by pass 2's blocks; 5.0 and
5.1 run before it with nothing up.

- **5.0 [user] `app-dbt-dev`'s request**, in the portal as the project's owner, on the listing 4.12
  publishes, and its approval by the approver Stage 19 decision 15 names, as 4.12's; its revocation joins
  4.12's at the end. **[Claude] reads** the subscription `APPROVED`, its grant and the resource link it
  writes in the subscription target's database: `app_dbt`, since 2.1's environment is the project's first
  `DataLake` environment, which carries the target (`SUP-184`); the project held the `Tooling` and
  `SageMakerAIDomain` environments alone on 2026-11-20. The project's source over `app_dbt` imports the
  link as an inventory asset at its next run (`SUP-197`), which a bundle carries: the request waits for
  8.8's `bundle` job, in R2 since R1 of 2026-11-22 left pass 8, and the asset leaves the project before a
  later tag (8.6).

- **5.1 [Claude] A model over the subscribed table**: a second source, `trades_notional` through the
  resource link 5.0 read, and a model `notional_by_desk_prod` in `app_dbt`. The link and its target are
  read first, with the subscription live:

  ```bash
  aws glue get-tables --database-name <the subscription target's database> --profile $P --region us-west-2 --query 'TableList[].[Name, TargetTable.DatabaseName, TargetTable.Name, IsRegisteredWithLakeFormation]' --output text
  ```

  The change goes through pass 1's tests and lint, then a new archive and a tar (2.0), on a branch no tag
  carries: the model reads a link only `app-dbt-dev` holds, which no target has. Its table's asset, if
  the project's source imports it, leaves the project before pass 8's tag, since the release guard fails
  a bundle that carries an asset `product.json` does not name (8.6).
- **5.2 [user] Deploy and run**, by 2.2's and 2.3's commands. **[Claude] reads** the worker's read under
  the subscription's grant, with `GetDataAccess` in the trail of the account that vends; the event's
  input name, which is the link's in Sandbox's catalog while the listing's asset carries Production's
  table ARN; and whether the graph joins Production's job, its table, the listing, the subscription and
  the dbt job. If it does not, the transformer resolves a link to its target (`glue:GetTable`'s
  `TargetTable`) and the run repeats (xiv).
- **5.3 [user] As a member of another project**, open the listing's *Lineage* tab. **[Claude] reads**
  what a consumer sees of the producer's jobs and of the dbt job downstream (xiv).

### 8. The promotion: `app-dbt` released through Staging and Production

Decision 9 (b): the release's bundle, made from the tag's files and `app-dbt-dev`'s catalog, deployed by
the CI/CD CLI into `deploy-staging` and then `deploy-production`, as `app-etl`'s releases since release F
([Stage 19](stage-19-smus-native-data-product.md) steps 4.9 to 4.11;
[`sagemaker-application.md`](../runbooks/sagemaker-application.md) §P, §S and §T). The pass runs after
passes 2 and 3, whose readings decide the targets' names (3.1), and after pass 5 when Stage 19's 4.12
comes first; after pull request #321's merge at R2's opening ([`promotion.md`](../runbooks/promotion.md)
§N.11.2; R1 left it on 2026-11-22), whose script change the legs need (8.1); and before 2026-12-18, when dbt Core 1.11's critical support ends (decision 6), or with the
archive moved to 1.12 and pass 1's tests, the simulation and 2.3 repeated on it. Passes 6 and 7 close the
stage after it. Step 8.2 and 8.4's four applies ran on 2026-11-18, 8.3 and 8.4's last apply on
2026-11-19; every other step is owed.

**The identities.** [Claude]'s reads and applies run as the infrastructure user, permission set
`InfrastructureAccess`: `Staging` by `awsds-infra-staging`, `Production` by `awsds-infra-prod`,
`Sandbox Account 1` by `awsds-infra-sandbox-1` and `Data Governance` by `awsds-infra-data`; one login
covers the four, the user's act. The pipeline's jobs run as their runners' profiles: `bundle` as
`awsds-deploy-sandbox-test`, the legs as `awsds-deploy-staging` and `awsds-deploy-prod`, the bundle's
object as `awsds-prod-runner-deploy`. GitLab's acts are the local administrator's and the deployment
manager's, the user's hands.

**What a target holds for `app-dbt`**, read 2026-11-18 with nothing up (the log):

| Piece | Staging, `deploy-staging` (`5ido8bej1zoeq8`) | Production, `deploy-production` (`d7qcazihvr3s7k`) | Who, and when |
|---|---|---|---|
| The product database `app_dbt`, its project grants and its daily source | the `DataLake` environment `deploy-staging-app-dbt` (`bg5ndpa5etujo0`), beside `deploy-staging-app-etl` (`54jhe9989w0tcg`, source `52f18khk7kdi4w`): the source `495urkkg5c7fyo`, and no subscription target (`SUP-184`) | `deploy-production-app-dbt` (`adscxpx574cas0`), beside `deploy-production-app-etl` (`azkybvkz7iea34`, source `5zggi2lr2ezy4w`): the source `bjfmkla36ed3ps`, no target | [Claude⚡] 8.3, created 2026-11-19 |
| The deploy role's read of the two tables' metadata | `deploy-project.tf`'s `deployment_product_databases`, applied 2026-11-18 (8.4); Lake Formation `DESCRIBE` by `staging-test.tf`'s `product_databases`, applied 2026-11-19 (8.4) | the IAM half alone, the file being a copy: Production's leg reads no table, and no Lake Formation grant is written | [Claude⚡] 8.4 |
| The Athena workgroup | `workgroup-5ido8bej1zoeq8-d6nu5aphq1e974`: `ENABLED`, enforced, engine 3, output under the project's `dev/sys/athena/`, `SSE_KMS` under the project key; the `Tooling` environment's `athenaWorkGroupName` | `workgroup-d7qcazihvr3s7k-59niwej9axztow`, the same settings | the project's `Tooling` environment |
| An `athena` interface endpoint | `awsds-staging-athena`, in `staging/egress/`'s list since 2026-11-18 | `awsds-prod-workloads-athena`, in `production/workloads-egress/`'s | decision 15 (a); `[E]`, the user's `make up` |
| The `datazone`, `glue`, `lakeformation` and `sts` endpoints | in the slice's list | in the slice's list | `[E]`, the user's `make up` |
| The Glue job `app-dbt-<project id>` | `GetAGlueJobNoProjectHolds` in `staging/studio/workflows.tf`, every application's | the same in `production/studio/` | applied |
| A processing job's isolation | `sagemaker:CreateProcessingJob` out of `DenySageMakerJobsWithoutNetworkIsolation` in the boundary `staging/studio/` composes (`sagemaker-prereqs-v0.11.0`) and in the `Workloads` OU's SCP: the release runs no SageMaker job, and dbt in a processing job (decision 2 (b)) would run under it | the same, `production/studio/` | applied 2026-11-17 (4.4) |
| The chains, `DISABLED` | `awsds-staging-chain-app-dbt` and `awsds-staging-chain-app-dbt-probe` | `awsds-prod-chain-app-dbt` | applied 2026-11-18 (8.4) |
| The stage variables | `/datascience/staging/applications/app-dbt/stage-variables`, written by `staging-deploy` | `/datascience/prod/applications/app-dbt/stage-variables`, by `production-deploy` | the leg |
| The two assets | imported by the leg, then revised by its second import (`SUP-369`) | the same | the leg |

- **8.1 [Claude] What the legs need of the scripts**, written in pull request #321, which teaches the
  scripts `app-ml` and `app-genai` from Stage 17's patches; this stage
  writes none of it:
  - `scripts/deploy-application.py`: `--image-uri` optional and `TRAINING_IMAGE_URI` exported only for
    an application that reads it, as Stage 17's `release_exports` proposes, `app-dbt` having neither;
    `--self-check` over every application, `app-dbt` among them;
  - `.pre-commit-config.yaml`'s `deploy-application-check`: its `files` pattern reading
    `examples/app-(etl|ml|genai|dbt)/`;
  - `scripts/model-chain.py` and `aws/cicd.py`: nothing, `app-dbt` having no model and no image;
  - `aws/catalog.py`'s `CHAIN_DEV_PROJECTS`: `app-dbt-dev`'s id, once 2.0 has read it. Written
    2026-11-19 on pull request #320, `--self-check` 39 of 39.

  Decision 17 (b), taken 2026-11-18, takes the workgroup from the project's connection, so the change
  carries no workgroup line. The step passes when `--self-check` prints each stage of each application
  `ok`, `app-dbt`'s naming `app_dbt_deploy_staging_app_dbt`, `app_dbt_deploy_staging_app_dbt_probe` and
  `app_dbt_deploy_production_app_dbt`, and `make check` is green. Without it a leg stops at the script's
  arguments, `--image-uri` being required. **Passed 2026-11-18 on
  [pull request #321](https://github.com/felipenoris/AWS-DataScience/pull/321)** (Stage 17's log), merged
  at R2's opening (`promotion.md` §N.11.2), R1 having run release G without it on 2026-11-22; `CHAIN_DEV_PROJECTS` gained
  `app-dbt-dev`'s id on 2026-11-19. The branch took `origin/main` at `5dfff219` by merge on 2026-11-20
  (`00113780`): `--self-check` printed every stage of the four applications `ok`, and `make check` OK.
- **8.2 [Claude] The `[P]` slices, written and planned 2026-11-18 with nothing up** (the
  log), each plan saved outside the repository:

  | Slice | Change | Plan |
  |---|---|---|
  | `staging/foundation/`, with the alerts var-file | `deploy-project.tf`'s `deployment_product_databases` gains `app_dbt`, so `ReadTheProductTablesMetadata` names `database/app_dbt` and `table/app_dbt/*` | *"Plan: 0 to add, 1 to change, 0 to destroy."* |
  | `production/foundation/`, with the alerts var-file | the same file, a copy `check-copies.py` holds | *"Plan: 0 to add, 1 to change, 0 to destroy."* |
  | `staging/chains/` | `app-dbt` in `applications` with both workflows; the chains `app-dbt` (`cron(0 9 * * ? *)`) and `app-dbt-probe` (`cron(30 9 * * ? *)`), `DISABLED`; `definitions/app-dbt.asl.json` and `app-dbt-probe.asl.json`, `app-ml-score`'s with the key and the comment changed | *"Plan: 12 to add, 1 to change, 0 to destroy."*: per chain a machine, a schedule, two rules and their targets; the chain role's policy gaining both workflows' ARNs and the parameter |
  | `production/chains/` | `app-dbt` and its one chain, `cron(0 9 * * ? *)`, `DISABLED`, the same definition | *"Plan: 6 to add, 1 to change, 0 to destroy."* |

  Each plan carried this change alone, and a plan of one of these slices from `main` carried it until
  8.4's applies (Lesson 69). Written at 8.4 and never before
  8.3: `staging/studio/staging-test.tf`'s `product_databases` gains `app_dbt`, since a database that
  does not exist fails that apply.
- **8.3 [Claude⚡] The product database in each deployment project**, after decisions 14 to 17 and
  before the tag, on the user's word naming each call: the `DataLake` environment by Stage 19 item 7's
  form (its verification xix), Staging's, then Production's.

  ```bash
  aws datazone create-environment --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier 5ido8bej1zoeq8 --environment-configuration-id d8f802ad-c74d-454a-84d1-e14012a434fa --environment-blueprint-identifier d8w7c3fmbsz5cg --name deploy-staging-app-dbt --user-parameters name=glueDbName,value=app_dbt --profile awsds-infra-staging --region us-west-2
  ```

  ```bash
  aws datazone create-environment --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier d7qcazihvr3s7k --environment-configuration-id f403ecfc-2450-4f7c-b31a-182b320d9271 --environment-blueprint-identifier d8w7c3fmbsz5cg --name deploy-production-app-dbt --user-parameters name=glueDbName,value=app_dbt --profile awsds-infra-prod --region us-west-2
  ```

  The configuration ids were read from the `app_etl` environments on 2026-11-18, DataZone refusing
  `GetProjectProfile` to each target's `InfrastructureAccess` (`SUP-157`). **[Claude] reads**, by 2.1's block with
  each target's values (8.9): the environment `ACTIVE`; the database at the project's catalogs folder;
  the project's conditioned grants; one source over `app_dbt`, daily and `publishOnImport` false, the
  one `--catalog-follow-up` expects; and the subscription target. Each deployment project then holds a
  `DataLake` environment, a database and a source per application.
  **Done 2026-11-19 by [Claude⚡] on the user's word** (the log). Read first, for Lesson 73: the CI/CD CLI
  resolves a connection by name and the project role from the first environment that provisions one, and
  the scripts select a source by its database, so a second `DataLake` environment changes no selection as
  long as it adds no connection and provisions the `Tooling` environment's role; the import's fallback to
  the first source is `SUP-389`. The configuration ids read again the same, and no `app_dbt` existed.
  `deploy-staging-app-dbt` (`bg5ndpa5etujo0`) created at 02:23:07 UTC, `ACTIVE` at 02:23:46;
  `deploy-production-app-dbt` (`adscxpx574cas0`) at 02:27:00, `ACTIVE` at 02:27:38. Each provisions the
  `Tooling` environment's role and adds no connection, the nine still the `Tooling` environment's. The
  database `app_dbt` is *"Created by DataZone for project deploy-<env>"* at the project's
  `dev/data/catalogs/`, with no create-table default, and the conditioned grants as `app_etl`'s; one source
  over it, `495urkkg5c7fyo` on `cron(23 2 * * ? *)` and `bjfmkla36ed3ps` on `cron(27 2 * * ? *)`, `READY`,
  `publishOnImport` false, on `project.default_lakehouse`. Neither environment carries a subscription
  target: a project's first `ACTIVE` `DataLake` environment alone gets one, whatever path created it, read
  across four projects the same day (`SUP-184`), and a deployment project subscribes to nothing (Stage 19
  decision 14). `./aws/catalog.py`'s `CT-14` reads *"2 source(s), over app_dbt, app_etl"* in both targets,
  and `./aws/studio.py`'s `US-11` three environments `ACTIVE` in each.
- **8.4 [Claude⚡] The applies**, on the user's word naming each, from plans taken again from a `main`
  that holds 8.2 (Lesson 79), each re-planned `No changes`: `staging/foundation/` and
  `production/foundation/` with the alerts var-file, `staging/chains/` and `production/chains/`, then
  `staging/studio/` once its line is written after 8.3. The laptop's other sessions are told first, and a
  session that holds `staging/studio/` is asked. **Run 2026-11-18 for the four slices** after PR #318's
  merge (the log): each plan from `main` carried 8.2's change alone, each apply matched it, each re-plan
  read `No changes`, and the three schedules read `DISABLED`. **`staging/studio/` applied 2026-11-19**,
  after 8.3, on the user's word: `product_databases` took `app_dbt`, planned from this step's branch
  (`main` at `573fe1df` and the line), *"2 added"* from 02:27:19 to 02:27:30 UTC, re-planned
  `No changes`; `awsds-deploy-staging` holds `DESCRIBE` on `app_etl`, `app_dbt` and their tables. The
  slice ran from pull request #328's branch, merged at 02:54:04 UTC as `6c3cc62d` with the head's tree,
  so `main` holds the line the apply ran from (Lesson 79).
- **8.5 [user] Decisions 14 to 17, and 3.1's verdict**; then **[Claude]** writes what each answer changes
  before 8.6: 14 (b)'s publish task, its data product and their grants; 15's endpoint, in both egress
  slices or in the module's group; 16 (b)'s namespace in the workflow's command, `run-dbt.sh` and the
  tests; 17 (b)'s workgroup in the workflow and the lint's new pin, or 17 (a)'s lines in 8.1; and the
  targets' `LINEAGE_NAMES` literal from 3.1. Each change passes pass 1's gates, and the simulation runs
  again on a change to `run-dbt.sh`. **Decisions 14 (a), 15 (a), 16 (c) and 17 (b) taken 2026-11-18**
  ("Decisions due"); written the same day with nothing up (the log): 15 (a)'s `athena` in
  `staging/egress/`'s and `production/workloads-egress/`'s `core_services`, each slice planned 17 to add
  before and 18 after, the one addition its endpoint, which the slice's first `make up` after the merge
  creates, release G's sitting the next (Lesson 69); 16 (c)'s `LINEAGE_NAMESPACE` in the manifest's
  three stages, the transform task's `--namespace '{env.LINEAGE_NAMESPACE}'`, `run-dbt.sh`'s option in
  place of `APP_DBT_NAMESPACE`, the tests, the README and 2.0's export: 86 tests passing, the lint at
  `1a50ceb` *"ok: 4 arquivo(s)"*, and the simulation's thirteen cases run again on the laptop's host
  archive from 14:15 to 14:17 UTC, the rendered transform task posting under `app-dbt-dev` and the run
  by hand under `app-dbt-by-hand`. 14 (a) writes nothing. **17 (b)'s change in `app-dbt` written
  2026-11-18** (the log): its two workflows naming `{proj.connection.project.athena.workgroupName}`,
  `ATHENA_WORKGROUP` out of the manifest, the rendering resolving the connection as the deploy does, the
  tests, the simulation's parameters, the README, and 2.0's and 2.6's blocks; 86 tests passing, the lint
  at `awsds-workflows` #28's head `2aa32cf` *"ok: 4 arquivo(s)"* with the pipeline's instance types, and
  the simulation's thirteen cases run again from 15:39 to 15:40 UTC, as at 14:15. #28 merged by the user
  at 15:50:35 UTC as `4613ddc`, its tree the branch's, and the pin moved to it in `.gitlab-ci.yml`, the
  README, the simulation and pass 2's archive line: the lint at `4613ddc` *"ok: 4 arquivo(s)"* with the
  pipeline's instance types, `package-task` the same at both commits. Owed: 3.1's verdict, which sitting
  A gives at 2.4 when the graph is one, `as-built` staying in the targets, and at 3.1 when it is split.
- **8.6 The release's content in `app-dbt-dev`**: **[user]** the two assets curated in the portal, as
  Stage 19's step 15 curated `app-etl-dev`'s: each one's description and README, and the form
  `classification`; and the project left holding nothing else a bundle would carry: pass 5's table asset
  deleted, and 4.5's workflow, with the folder, the manifest's lines and the tests `main`'s `399f3365`
  added for it (pull request #335's squash of `30ab3539`), and pass 5's model off the tagged tree.
  **[Claude]** the bundle rehearsed from the laptop, as Stage 19's step 17 rehearsed `app-etl`'s: the `bundle` job's script run by `bash`
  from a tar of the tree to be tagged, as `awsds-infra-sandbox-1`, a contributor of the project, with the
  three CI/CD variables exported; the export read, and `scripts/check-catalog-export.py` passing on the
  two assets and the form alone. The CLI's calls are reads, and Sandbox's trail is read after.
  **The tree written 2026-11-21 on [pull request #349](https://github.com/felipenoris/AWS-DataScience/pull/349)**
  (the log): `examples/app-dbt/` back at `c11a9829`'s tree `ec837c34`, the one `103b4acc` built 2.0's
  archive and tar from, so 4.5's workflow, folder, manifest lines, tests and README rows are off it; then the
  lint pin at `awsds-workflows` `4401f91`, which every application takes at its next tag (Stage 8 5.6's
  rule). ruff clean, 86 tests passing, the lint at `4401f91` *"ok: 4 arquivo(s)"* with the pipeline's
  instance types, and #321's `--self-check` on the tree `ok` for every stage, `app-dbt`'s at 9 variables
  with 8.1's names. Pass 5's model is on no branch, and 5.1 writes it on one no tag carries. 5.0's
  subscription writes a resource link in `app_dbt`, which the project's source imports as an inventory
  asset at its next run, `cron(43 2 * * ? *)` or a member's (`SUP-197`); the bundle would export it and
  the guard fail. So 5.0's request waits for 8.8's `bundle` job (`promotion.md` §N.11.1 step 5), in R2 since R1
  of 2026-11-22 left pass 8, and
  a later tag first deletes that asset with pass 5's table asset. **Rehearsed before the curation** at
  20:27 UTC, nothing curated yet: `build-task-code`'s script and then `bundle`'s, by `bash` in the tag's
  tree extracted from `git archive`, exit 0; the export the two assets with no description, README or
  form, the guard *"OK"*, and the session's 32 calls in Sandbox's trail every one a read.
  **Curated 2026-11-21** on the user's word in Claude's session (the log): each asset's description,
  README and `classification` `internal`, saved by Claude through the Data Scientist User's portal
  session from 20:38 to 20:43 UTC as revisions 3 to 5 of both, each read back by `get-asset`, and the six
  `CreateAssetRevision` the only writes in Data Governance's trail. **Rehearsed after the curation** at
  20:44 UTC, the same script and tree: exit 0, the export the two assets with their description, README
  and form and no form type, the guard *"OK"*, and the session's 32 calls in Sandbox's trail every one a
  read. Pass 5's table asset and 5.0's link asset exist only after 5.0, so a tag before it deletes
  nothing.
- **8.7 The GitLab sitting** ([`gitlab.md`](../runbooks/gitlab.md) §U), the hub and GitLab up: **R1 created
  `awsds/app-dbt` on 2026-11-22** (id 9, §L's steps 1 to 6 and the allowlist, read through GitLab's API,
  Stage 19's log), and the mirror's push and the first push are R2's opening (`promotion.md` §N.11.2). **[user]**
  `awsds/app-dbt` created as
  [`sagemaker-application.md`](../runbooks/sagemaker-application.md) §L's steps 1 to 6 say: the project,
  `main` and `v*` protected, the members, the three runners linked, the variables `DOMAIN_ID`,
  `DOMAIN_REGION` and `DEV_PROJECT_NAME` (`app-dbt-dev`), and `awsds/infrastructure`'s job-token
  allowlist admitting it ([`gitlab.md`](../runbooks/gitlab.md) §M, the infrastructure mirror's step 3);
  the mirror pushed at `main` (`git push gitlab main`, its step 5) once the merge holds 8.1 and 8.5,
  since the legs clone the scripts from it; and the first push, `examples/app-dbt/`'s tree at that
  merge as the project's `main`.
  **[Claude] reads** the branch pipeline: `test` (pytest, ruff, the lint *"ok: 4 arquivo(s)"*),
  `secret_detection` and its gate, and `pip-audit` over the runtime export's 78 pins, each audited; a
  finding is a line of `awsds/ci-gates`' baselines and a gates tag (§L step 8), or the lock moved.
- **8.8 The release sitting**, in [`promotion.md`](../runbooks/promotion.md) §N.8.4's form, R2 (§N.11.2):
  R1 of 2026-11-22 did not carry it, the user's choice, so its step 7 moved there: **[user]** the hub and GitLab with the
  build runner (`make gitlab-up BUILD=1`), `make up ENV=staging ONLY=egress` before the tag, the tag `v0.1.0` on `main` and
  `staging-gate`; `make down ENV=staging` after `staging-catalog`; `make up ENV=production
  ONLY=workloads-egress` before `production-gate`, then the gate. **[Claude]** tells the other sessions
  before the first raise, reads `make status` after each, and follows each job:

  | Job | Passes when |
  |---|---|
  | `build-task-code` | the archive's two modes read `0o100755` and both sizes are under 250 MB |
  | `bundle` | the guard passes on the two assets and the form, and the SHA256 goes to the dotenv |
  | `store-bundle`, `release` | the object is under `awsds-prod-releases/app-dbt/v0.1.0/` and the release's notes name it |
  | `staging-check` | the egress is read up, `awsds-staging-athena` is available, and the script reads the deploy role a member of the project |
  | `staging-deploy` | the first import is admitted (`STAGING_CATALOG_PENDING=true`), both workflows sit in the project's network, and the parameter is written |
  | `staging-test` | `awsds-staging-chain-app-dbt-probe`, then `awsds-staging-chain-app-dbt`, end `SUCCEEDED`, and both tables are Iceberg |
  | `staging-catalog` | the source runs, both assets are found, and the second deploy fails no item |
  | `production-check`, `production-gate` | the script reads the deploy role a member of `deploy-production` |
  | `production-deploy` | `awsds-prod-workloads-athena` is available, and the bootstrap's run of `app-dbt` ends `SUCCESS` |
  | `production-catalog` | the second import passes, its deploy running `app-dbt` again and swapping `notional_by_desk` (x) |

  A failure stops the sitting at the job's log, as release F's did (§N.8.4); the downs follow
  §N.8.4's.
- **8.9 [Claude] The readings per target**, after each leg, each account's trail after its delay
  (Lesson 62), by pass 2's blocks with the target's values:

  ```bash
  D=dzd-d8yrvx1ko7im6o; E=5ido8bej1zoeq8; P=awsds-infra-staging; B=awsds-staging-smus-projects; WG=workgroup-$E-d6nu5aphq1e974; N=app_dbt_deploy_staging_app_dbt
  ```

  ```bash
  D=dzd-d8yrvx1ko7im6o; E=d7qcazihvr3s7k; P=awsds-infra-prod; B=awsds-prod-smus-projects; WG=workgroup-$E-59niwej9axztow; N=app_dbt_deploy_production_app_dbt
  ```

  - the dbt task on Athena as the deployment project's role: both tasks' states and `transform`'s log,
    as 2.3 reads them; the statements in the workgroup; the model's table, its location under
    `dev/data/catalogs/app_dbt/notional_by_desk/` and the session that created it; and, in the account's
    trail, `StartQueryExecution`, `GetDataAccess` and `CreateTable` with the grant that admitted each,
    and the `vpcEndpointId` of each of the worker's calls (xviii);
  - its lineage events: `ListLineageEvents` from the run's first minute, six `SUCCESS` under the job
    namespace `app-dbt-staging` or `app-dbt-prod` (decision 16 (c)), and `PostLineageEvent` in the
    account's trail through its `datazone` endpoint (xix);
  - the nodes: 2.4's `get-lineage-node` on each asset's node, the model's output node carrying the
    account's table ARN, the dbt job's run upstream of it and the Glue job's node upstream of that, and
    whether the node is the target's own or one the accounts share (xx);
  - the catalog import: the project's assets by 2.4's `search`, each one's metadata against
    `app-dbt-dev`'s, its revision after the second import, and `./aws/catalog.py`'s rows (xxi);
  - Staging's probe: its log, as 2.2 reads it (xxii).
- **8.10 [user] Keep**: the release stays deployed in both targets, the schedules `DISABLED`, the tables
  billing their storage alone. Rollback's pass 8 half removes it.

### 6. The checks and the documents

- **6.1 [Claude] [`./aws/catalog.py`](../../../aws/catalog.py)** gains lineage readings as new `CT-`
  rows: a window's events by `processingStatus`, each asset of a project with or without a job upstream,
  and the dataset nodes no asset carries.
- **6.2 [Claude] The documents**: the runbook completed with the readings of passes 2 to 5 and 8;
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

- **7.1 [user] Keep or delete**: in `app-dbt-dev`, the workflows and the Glue job, the files under
  `shared/app-dbt/`, the database `app_dbt` with its assets and source, and the project itself; in the
  targets, the release, by 8.10; and the lineage events, by what xv read of `DeleteLineageEvent`. A
  delete follows Rollback's order and commands.
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
| xviii | In each target, does Athena admit the worker's session of the deployment project's role in the project's workgroup through the account's `athena` endpoint, does Lake Formation vend to it, and does the model become an Iceberg table under the project's catalogs folder, as iii read in Sandbox? | 8.8, 8.9 |
| xix | Does each target's worker post through its account's `datazone` endpoint: how many events, with which `processingStatus`, under which job namespace (decision 16 (c): `app-dbt-staging`, `app-dbt-prod`)? | 8.9 |
| xx | Are a target's job and dataset nodes its own, apart from Sandbox's and the other target's, and does each target's asset carry its own account's dbt run upstream? | 8.9 |
| xxi | Do a target's two assets carry `app-dbt-dev`'s curated metadata after the catalog import and its follow-up, and what does Production's second run do to the asset and to the graph (x)? | 8.8, 8.9 |
| xxii | What does Staging's probe read on a deployment project's worker against 2.2's reading in Sandbox: the glibc, the tools, the identity, the workgroup and `SELECT 1`? | 8.8 |

## Decisions due

The user took decisions 1 to 7, 10 and 13 one at a time on 2026-11-16, in the cloud session's thread,
after step 1.1's facts, 9 and 11 on 2026-11-17, on cards in the review of the plan's open decisions,
and 14 to 17 on 2026-11-18 in a laptop session's chat, after each was presented with its context, its
options and its recommendation; the log carries each question as it was asked and each answer in the
user's words. Taken: 1 to 7, 9 to 11 and 13 to 17. Settled by other decisions: 8. Moot: 12.

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
   user, who looks at it again then. **Looked at again 2026-11-21: (a) kept**, in the user's words
   *"Manter (a)"*, on 3.3's readings (ix): a refused, a rejected and an unanswered post each leave the
   task `SUCCESS` with exit code 0 and the task's log alone reports them; the unanswered adds six minutes,
   and each multiplies the log by 12 to 26.
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
   **Reopened 2026-11-17 by decision 9 (b) and moved to (b)**, as the card of 9 (b) stated it, *"Reabre a
   decisão 7 (projeto dev próprio)"*: a Sandbox project for `app-dbt` alone becomes the manifest's `dev`
   stage, as Stage 19 decision 18 (d) made `app-etl-dev`, since the CLI 1.0.9 bundles the `dev` project's
   whole catalog. The user creates it in the portal; its role joins `sandbox/workflows/`'s
   `project_roles` in one line and one apply (open question 27 keeps the list), and after Stage 19 step
   4.12 it holds the subscription pass 5 reads (decision 11 (a)). `eighth-experimentation` keeps its
   experiments.
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
   **Taken 2026-11-17 by the user as (b)**, the option *"Promover pela CLI (caminho AWS)"* on a card at
   22:19 UTC, in the review of the plan's open decisions under the user's default of 21:50 UTC, AWS's
   suggested path: `app-dbt` is promoted to Staging and Production by the CI/CD CLI, into the deployment
   projects, as `app-etl` is. It moves decision 7 to (b), and this stage takes the list above: pass 1's
   one-stage `examples/app-dbt/` is extended to the three stages, and the passes that bundle, release and
   read it in each target are written before the sitting that runs them. dbt Core 1.11's critical support
   ends 2026-12-18 (decision 6), so the release runs before that day or the archive moves to 1.12.
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
    **Taken 2026-11-17 by the user as (a)**, the option *"Depois da 4.12 do Stage 19"* on a card at
    22:21 UTC: the subscribed `trades_notional` is a model's input after Stage 19 step 4.12, the
    subscription held by `app-dbt`'s own `dev` project (decision 7 (b)).
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
14. **Production's listing of the application's tables** (8.5, 8.8). Under 9 (b) the release imports
    `app-dbt-dev`'s two assets into each deployment project, and the manifest's `skipPublish` lists
    nothing. (a) The inventory alone: no task of the application publishes, so each target's two tables
    are assets of its deployment project, read by its members and drawn in its lineage graph, and offered
    to no other project. (b) Production lists, as `app-etl` does (Stage 19 decisions 14 (a), 20 (b) and
    26 (b)): a `publish` task in `app-dbt`'s workflow with `PUBLISH_LISTING` true in `prod` alone, which
    starts Production's source and lists the two assets or a data product of them, whose name is the
    domain's (`SUP-369`); the task's grants read against a second application in the project, `CT-18`
    and Stage 19 decision 15's approver extended to it, and the lint's rules over the task.
    **Recommended: (a)**: both are SMUS's paths, the import landing in the inventory and a listing being
    the act that offers an asset to the domain's other projects, and no project consumes
    `notional_by_desk`. The stage's question is read on the inventory assets' graph, pass 5 reads a graph
    across a subscription with Stage 19's product, and (b) adds a publisher, its grants and a second
    product to the domain's business catalog before 2026-12-18. A later release can take (b) without
    changing what pass 8 reads. **Taken 2026-11-18 by the user as (a)**, in the user's words *"Em
    relação às demais, aceito as recomendações."* at 14:02 UTC: no task of `app-dbt` publishes, the
    manifest's `skipPublish: true` stands, and 8.5 writes nothing for it.
15. **The `athena` endpoint in the targets** (8.5, xviii). The `transform` task queries Athena from the
    deployment project's subnets, and neither `staging/egress/` nor `production/workloads-egress/` holds
    an `athena` endpoint: both override the module's core list without it, *"until a job here queries
    through it"* (`production/workloads-egress/main.tf`), and with no route out of a target's VPC (D38)
    the call fails as the `datazone` post did before its endpoint (Stage 18 7.1). (a) `athena` joins both
    slices' `core_services`, the change `staging/egress/main.tf`'s comment names for *"a job inside the
    VPC"* that queries: one interface endpoint each at 0.010 USD per hour plus 0.010 per GB while the
    slice is up ([`PRICING.md`](../../PRICING.md)), so every leg and every chain run of a sitting finds
    it, and `./scripts/check-egress.py` reads it from the slice's state with the rest. (b) An optional
    `athena` group: a `vpc-egress` tag past `v0.19.0`, both callers moved from `v0.17.0` with what the
    tags between carry, `staging/egress/` threading `optional_service_groups` as
    `production/workloads-egress/` does, and `GROUPS=athena` named in every sitting that runs
    `app-dbt`: the endpoint bills only in those sittings, and a sitting without the group fails at the
    pipeline's endpoint check or in the task. **Recommended: (a)**: an interface endpoint is AWS's path
    for an Athena client in a subnet with no route out, both slices' comments already name the change,
    and (b) saves 0.010 USD per hour per target at the price of a module tag and a group every sitting
    must remember. Either change is `[E]`, taken by the user's `make up`; the module names every
    endpoint `<prefix>-<service>`, so the pipeline's check by tag (`awsds-staging-athena`,
    `awsds-prod-workloads-athena`) reads both. **Taken 2026-11-18 by the user as (a)**, in the same
    answer as 14: `athena` joins both slices' `core_services`, written the same day with each slice's
    comment, and each slice planned with nothing up, 17 to add before and 18 after, the one addition
    `aws_vpc_endpoint.interface["athena"]` named `awsds-staging-athena` and
    `awsds-prod-workloads-athena` (the log). The endpoint exists from each slice's next `make up`.
16. **The dbt job's namespace in the domain** (8.5, xix, xx). `run-dbt.sh` exports
    `OPENLINEAGE_NAMESPACE` from `APP_DBT_NAMESPACE`, `app-dbt` when unset, and the workflow sets nothing,
    so every account's runs post their job under one namespace and one name, into one domain; the load
    task's Glue job carries the project's id in its name, `app-dbt-{proj.id}`. (a) `app-dbt` in every
    stage: one job node for every account's runs, told apart by the run alone. (b)
    `app-dbt-{proj.id}`, the Glue job's shape, passed by the task's command
    (`APP_DBT_NAMESPACE='app-dbt-{proj.id}' bash /usr/local/airflow/dags/run-dbt.sh …`), a variable the
    lint admits in the Glue task: one job node per project, so a target's graph holds its own account's
    runs. (c) A stage variable `LINEAGE_NAMESPACE`, a literal in each target and an export in `dev`.
    **Recommended: (b)**: the dbt job gets the per-project node the Glue job's name already gives the
    load task, with no stage variable and no change to `run-dbt.sh`, and xx reads what (a) would merge.
    Taken before Sandbox sitting A, it holds in `dev` from pass 2's first run, and 2.3's and 2.4's
    readings name its namespace; taken after, `dev`'s first runs keep `app-dbt`. **Taken 2026-11-18 by
    the user as (c)**, in the user's words *"Decisão 16: (c)"* at 14:02 UTC, against the
    recommendation: `LINEAGE_NAMESPACE` is a stage variable of every stage, the literals
    `app-dbt-staging` and `app-dbt-prod` in the targets and `app-dbt-dev` exported in `dev` (2.0's
    block), each stage's runs a job of their own; the task passes it as `run-dbt.sh`'s `--namespace`,
    which replaces `APP_DBT_NAMESPACE` and reads `app-dbt` when left out. Written the same day with its
    tests, and the simulation run again (8.5); taken before Sandbox sitting A, it holds in `dev` from
    pass 2's first run.
17. **The workgroup's source** (8.1, 8.5). The task names its workgroup by the stage variable
    `ATHENA_WORKGROUP`: a developer's export in `dev`, and in a target the value 8.1's `projects.py`
    change reads from the deployment project's `Tooling` environment (`athenaWorkGroupName`). Every
    project's `Tooling` environment also creates an Athena connection, `project.athena`, whose
    `workgroupName` is that workgroup (read 2026-11-18 in `deploy-staging`, `deploy-production` and
    `eighth-experimentation`), and the CLI 1.0.9 resolves `{proj.connection.<connection>.<property>}` at
    deploy. (a) The stage variable, as written: `ATHENA_WORKGROUP` in each stage, 8.1's two lines and a
    `dev` export. (b) `{proj.connection.project.athena.workgroupName}` in the task's command: the
    project's own connection, resolved by the CLI in every stage, with no stage variable, no export and
    no script change; `awsds-workflows`' lint at `1a50ceb` refuses the variable (`CLI_VARIABLES`), so
    (b) waits on that project's change and a new pin wherever `app-dbt` names `1a50ceb`
    (`.gitlab-ci.yml`, the README, the simulation) and in pass 2's `TOOL`. **Recommended by the user's
    criterion: (b)**, the path the CLI gives a workflow to a
    project's resource, as the Glue task reaches its shared prefix through
    `{proj.connection.default.s3_shared.s3Uri}`; (a) stays the fallback if the lint's release misses
    8.6, and its two lines in 8.1 leave with (b). **Taken 2026-11-18 by the user as (b)**, in the same
    answer as 14. `awsds-workflows`' change is committed in a local clone, on its branch
    `claude/workgroup-athena-cli-variable` (`2aa32cf`): the variable in `CLI_VARIABLES` as
    `<ATHENA_WORKGROUP>`, its tests, its guide's table, and the CLI 1.0.9's reading in its memory
    (`helpers/connections.py` gives an `ATHENA` connection's `workgroupName`, `helpers/context_resolver.py`
    resolves any connection's property, a dotted name included). It answers a copy of `app-dbt` naming
    the variable *"ok: 4 arquivo(s)"*, which `1a50ceb` refuses. Pushed and opened as
    [felipenoris/awsds-workflows#28](https://github.com/felipenoris/awsds-workflows/pull/28) on the
    user's word in this repository's chat (*"Autorizo push e PR"*, 15:29 UTC), and merged by the user at
    15:50:35 UTC as `4613ddc`, which `app-dbt` pins since, its side written the same day (8.5).

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
- Pass 8's sittings: the hub at 0.0310 per hour and GitLab's `t4g.large` at 0.0672 (the GitLab
  session's rows), the runners
  while they run; `staging/egress/`'s and `production/workloads-egress/`'s interface endpoints at 0.010
  per hour each plus 0.010 per GB while up, decision 15 (a)'s `athena` one more in each, and about 0.60
  of Config per `staging/egress` up and down; each leg's worker task-hours and Glue run at the rates
  above, Production's bootstrap and follow-up running `app-dbt` twice; each import's source run in
  compute units.
- At rest: nothing new. A database, its `DataLake` environment, an asset, a lineage event, a workflow
  and a chain are metadata or bill by use, the chains' schedules `DISABLED`, and the Glue job bills only
  while it runs; each project's tables bill their kilobytes. The stage's one `[E]` resource is decision
  15 (a)'s endpoint, which lives and dies with its egress slice. Its Terraform is pass 4's policy
  documents, `sandbox/workflows/`'s line (2.0) and pass 8's `[P]` slices, none of which bills; a refusal
  read at 2.1, 2.2 or 2.3 is brought to the user before any grant is written.

## Rollback

Each write is on the user's word, in this order: `app-dbt-dev`'s half, then pass 8's in each target.
The laptop's commands run as `awsds-infra-sandbox-1` with pass 2's values, in the forms that retired
`app-etl` from `eighth-experimentation` on 2026-11-14 (Stage 19's sitting), each object read before its
delete.

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

3. **[user] The assets, then the source**, in the portal, as a member of the project: the two assets
   2.4 read, by their external identifiers, and pass 5's if one stands. The source is deleted right
   after them and before its next daily run, which would import the tables again:
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

7. **[Claude⚡] `sandbox/workflows/`'s line, then [user] the project**, if 7.1 deletes `app-dbt-dev`:
   the role leaves `project_roles` and the slice is applied from `main`, since the slice reads each role
   by name and a missing one fails its plan; then the user deletes the project in the portal, and
   `aws/catalog.py`'s `CHAIN_DEV_PROJECTS` loses its id.

**[Claude] reads** the end by 2.0's block and 2.1's lists: no workflow, no job and no database; `0` under
`shared/app-dbt/`; the project's assets without this stage's two; its environments and sources without
the database's; and the tables' folders with no current object.

Pass 8's half, after 8.10's word, runs in each target as `awsds-infra-staging` or `awsds-infra-prod`
with 8.9's values, Staging's first:

8. **[Claude⚡] The chains and the read grant**: `app-dbt`'s entries leave `staging/chains/` and
   `production/chains/` with their definitions, and `app_dbt` leaves `staging/studio/staging-test.tf`'s
   `product_databases`, each applied from `main`, before the workflows the chains start and before the
   database the grant names.
9. **[Claude⚡] The workflows and the Glue job**, by step 1's commands with the target's values:
   `app_dbt_deploy_staging_app_dbt`, `app_dbt_deploy_staging_app_dbt_probe` and `app-dbt-5ido8bej1zoeq8`
   in Staging; `app_dbt_deploy_production_app_dbt` and `app-dbt-d7qcazihvr3s7k` in Production.
10. **[Claude⚡] The files and the stage variables**: step 2's commands over the project's
    `shared/app-dbt/`, then the leg's parameter:

    ```bash
    aws ssm delete-parameter --name /datascience/staging/applications/app-dbt/stage-variables --profile awsds-infra-staging --region us-west-2
    aws ssm delete-parameter --name /datascience/prod/applications/app-dbt/stage-variables --profile awsds-infra-prod --region us-west-2
    ```

11. **[user] The assets, then the source**, in the portal as an owner of the deployment project, by
    step 3's order (`SUP-366`).
12. **[user] The tables, then the database**, by step 4's statements as the project role, from the
    deployment project's query editor, the form Stage 19's rollback gives its table.
13. **[Claude⚡] The `DataLake` environment** `deploy-staging-app-dbt` or `deploy-production-app-dbt`, by
    step 5's command, after its database.
14. **[Claude⚡] The deploy role's list**: `app_dbt` leaves `deployment_product_databases` in both
    `foundation/` slices' `deploy-project.tf`, applied with the alerts var-file.

**[Claude] reads** each target's end by 8.9's blocks: no workflow named `app_dbt_*` and no job
`app-dbt-<project id>`; `0` under `shared/app-dbt/`; no parameter; the project's assets, sources and
environments without `app-dbt`'s; no database `app_dbt`; no chain `awsds-<env>-chain-app-dbt*`.

What stays: the trails' records; the runs' log groups, which carry no retention
([`serverless-workflows.md`](../runbooks/serverless-workflows.md) §X); the CLI's copies of the archive
under `shared/operatorFiles/`, one for each deploy; the noncurrent versions of the removed objects and of
the dropped tables' files, for the 90 days of the bucket's lifecycle; and whatever xv reads that a
deleted event leaves. Pass 4 is rolled back on its own: each caller's pin returned to the tag it held and
applied by 4.4's commands, the OU document's copy with it, and the battery's `ou` phase run again. A tag
never moves. Pass 8 leaves the bundle under `awsds-prod-releases/app-dbt/v0.1.0/`, the GitLab release
and its tag, and the project `awsds/app-dbt`, which the user archives or keeps; decision 15 (a)'s
endpoint leaves both slices' lists by a commit, taken by the next `make up`.

## What this stage does not do

- List the application's tables in Production or build a data product of them (decision 14), or
  enable a chain's schedule: a run in a target is a sitting's.
- Change `scripts/deploy-application.py`, `scripts/model-chain.py`, their hooks or `aws/cicd.py`: 8.1's
  change is pull request #321, merged at R2's opening ([`promotion.md`](../runbooks/promotion.md) §N.11.2).
- Build an image, or put dbt in the house image.
- Run dbt on Redshift or on Glue with Spark (decision 1), or in a processing job, in several tasks or
  in a Glue job (decision 2): the first two are a later revision's, and the runbook compares the rest.
- Lift the isolation of a training, tuning or AutoML job or of a model, or any other job statement
  (decision 13).
- Enable provisioned MWAA or Airflow's OpenLineage provider (D7), or use dbt's hosted platform.
- Publish a listing or a data product before pass 5, or assign an LF-Tag: the graph needs an inventory
  asset, and the runbook's publication and sharing sections are written from Stage 19's measurements.
- Touch `app-etl`, `app-etl-dev` or `app-etl`'s release: the deployment projects gain `app-dbt`'s
  database, source, assets and workflows beside `app-etl`'s.
- Change how a project role gets the workflows grant: `app-dbt-dev`'s role joins
  `sandbox/workflows/`'s list by its one line (2.0), and a form that serves every project is
  [open question 27](../open-questions.md).
- Use the warehouse, admit a second project to it (6h decision 8) or touch the connection's
  `lineageSync` (6h decision 3).

## What concerns the other sessions

- **Stage 19**: this stage's Sandbox objects live in `app-dbt-dev` (decision 7 (b)), a second
  subscriber to its step 4.12's listing (5.0), and pass 8 adds to `deploy-staging` and
  `deploy-production` a `DataLake` environment, a database, a source, two assets and the workflows
  beside `app-etl`'s, with `app_dbt` in both foundations' `deployment_product_databases` and in
  `staging-test.tf`'s `product_databases`. Pass 5 here waits on that step and runs before the
  revocation it ends with. Its step 6.2 rewrites
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
- **Stage 17 and the release sittings**: pass 8 shares `staging/chains/`, `production/chains/` and both
  `foundation/` slices with Stage 17's applications, so a plan of one carries the other's change once
  both are on `main` (Lesson 69); R1 ([`promotion.md`](../runbooks/promotion.md) §N.11.1) created 8.7's
  GitLab project with theirs on 2026-11-22 (its step 3), and R2's opening merges 8.1's script change beside
  `app-ml`'s and `app-genai`'s (pull request #321, moved from R1's step 6).
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
  at 9.38.0 where 9.32.0 was measured; and a Bash task's `env` and `append_env`, still unmeasured. The
  lint's `job` rule, asked after pass 4, no longer reads a processing task's `EnableNetworkIsolation`
  since that project's pull request #27, merged 2026-11-17 as `1a50ceb` with its guide's pages; its
  example job keeps the isolation. The lint in the authoring mode refused nothing of a one-stage
  application (0.15), and at `1a50ceb` it answers the three-stage one *"ok: 4 arquivo(s)"*
  (2026-11-18). Decision 17 (b) asks it for `{proj.connection.project.athena.workgroupName}` in
  `CLI_VARIABLES`, which the CLI 1.0.9 resolves and the lint at `1a50ceb` refuses: the change is
  `awsds-workflows`' pull request #28, merged 2026-11-18 as `4613ddc`, which `app-dbt` pins.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Log:
[log-stage-20-dbt-lineage.md](../../log/log-stage-20-dbt-lineage.md)*
