# Log — Stage 20 — A dbt task in a SageMaker application, and its lineage in the catalog

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-20-dbt-lineage.md`](../plan/stages/stage-20-dbt-lineage.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-11-16 — the stage written from vendor pages, released packages and the repository, with no AWS call

- **[user] The request**, in a cloud session, in the user's words: a Stage 20 whose scope is *"exercitar
  uma aplicação SMUS que possui task que utiliza o DBT para uma etapa de transformação de dados de
  pipeline, emitindo lineage de forma que fique visível no DataZone"*, with the runbook, the context and
  the processing-job hypothesis the stage file quotes under "The premises"; *"Suba um PR no
  AWS-DataScience com o planejamento deste novo estágio."*; and, a minute later, *"Nesta tarefa,
  considere, sempre que possível, o caminho padrão proposto pelo que o SMUS oferece, e recomendações da
  AWS."* The session held no AWS credential: it made no AWS call, no apply and no portal act, and read
  the repository at `main` `c5e1718`, vendor pages, and packages from PyPI.
- **[Claude] The review of the repository**, recorded in the stage file's "The plan and the estate
  against the premises": D7, D13, D17, D26, D28, D40 and D41; Stages 6f, 6h, 6i, 10, 18 and 19;
  `GOVERNANCE.md`, `SMUS.md`, the runbooks `serverless-workflows.md`, `sagemaker-application.md` and
  `redshift-connection.md`; `./aws/catalog.py`. The readings the design turns on:
  - Stage 19's release guard, `scripts/check-catalog-export.py`, fails a release whose bundle export
    holds an asset `product.json` does not name, and the CLI's `bundle` exports whatever the `dev`
    project owns, so nothing of this stage is created in `app-etl-dev`;
  - `eighth-experimentation` holds nothing of `app-etl` since 2026-11-14, its application deleted and
    its product retired that day (Stage 19's step 18 and item 20), and it keeps the workflows grant and
    the warehouse's admission;
  - a worker's session of the project role called the domain through Sandbox's `datazone` endpoint
    (Stage 19 verification ii, 2026-11-10) and the role holds `datazone:PostLineageEvent` (Stage 18
    7.1), while no worker has posted an event;
  - D28 lets a worker run *"orchestration code"*, *"never a data path"*: a dbt client that sends SQL to
    an engine is inside it, and `dbt seed`, which carries rows through the client, is not;
  - the processing task of 6i held its worker 791 s for a command of one second on the house image
    (2026-10-11), and `app-etl`'s Glue job ran 66 s on two `G.1X` workers (2026-10-26).
- **[Claude] AWS's lineage pages** (the SageMaker Unified Studio user guide, read 2026-11-16):
  - the support matrix, in two tables. The tools: a JupyterLab notebook on a Glue or an EMR Serverless
    Spark session is *"Automated"* (*"Spark DataFrames only; remote workflow execution"*), a Visual ETL
    flow is *"Automated"* in Glue's compatibility mode and *"Not supported"* in fine-grained mode, and
    the query editor on Amazon Redshift is *"Automated"*. The services: a Glue crawler and Amazon
    Redshift are *"Automated by default in SageMaker Unified Studio"* (*"Redshift System tables will be
    used to retrieve user queries"*), *"AWS Glue jobs in AWS Glue console"* and EMR are *"Not automated
    by default"* (EMR Serverless from 7.5, EMR on EC2 from 7.11, EMR on EKS from 7.12). No row names
    Athena, dbt, Airflow or MWAA;
  - the tools page: *"OpenLineage libraries for Spark are built into AWS Glue v5.0+ for Spark DataFrames
    only. Dynamic DataFrames are not supported."*; *"LineageEvent has a size limit of 300KB"*; a
    notebook's session takes its job name from a `%%configure` cell, and *"for AWS Glue Spark executions
    in notebooks, lineage capture is automated when scheduled with workflow in shared environment using
    remote workflows"*;
  - the connections page: *"For every connection created, lineage is not automatically enabled"*; the
    switch is *Import data lineage* on the data source's connection details; *"Lineage is captured only
    for crawlers which imported less than 250 tables in a crawler run"*; a Redshift source's run is
    daily, from the system tables, with a first pull about 5 minutes after enabling;
  - the support page: *"capture and store lineage events beyond what is available in Amazon SageMaker
    Unified Studio"*; the `amazon_datazone_api` transport *"was merged into OpenLineage version
    1.33.0"*. The page on OpenLineage: *"Currently, Amazon SageMaker Unified Studio only supports
    RunEvents"*; *"OpenLineage 1.22.0+ versions are supported"*;
  - the `sourceIdentifier` page: a job node is `<namespace>.<name>` and a job run
    `<job's namespace>.<job's name>/<run_id>`; a dataset becomes a Glue table's ARN through its symlink
    when the event's `environment-properties` carries `GLUE_VERSION` and its like; a namespace that
    begins with `redshift` becomes a Redshift ARN, `redshift-serverless` in the namespace giving
    `arn:aws:redshift-serverless:<region>:<account>:table/<workgroup>/<database>/<schema>/<table>`;
    the page's example for a serverless workgroup names the dataset
    `redshift://<workgroup>.<account>.<region>.redshift-serverless.amazonaws.com:5439` and
    `<database>.<schema>.<table>`, the form `dbt-redshift`'s events carry, while the convention it
    quotes for the namespace is `provider://{cluster_identifier or workgroup}.{region_name}:{port}`;
    *"In all other cases, dataset nodes' sourceIdentifier is populated using <namespace>/<name>"*; the
    page names no Athena, Trino, Iceberg or dbt, and states nothing on case;
  - the permissions page: `GetLineageNode`, `ListLineageNodeHistory` and `QueryGraph` are open to every
    user of the domain; posting needs `datazone:PostLineageEvent`; the Redshift capture needs the
    connection's credentials to hold the `sys:operator` role and `SELECT` on the tables;
  - the troubleshooting page, read in its Markdown form for the exact words. For an event published
    programmatically: *"Lineage graphs are only visible in Amazon SageMaker Unified Studio if at least
    one node of the graph is an asset."* and *"If not matching, fix the namespace and name of the dataset
    in the lineage event and publish the lineage event again."* Under Glue's own jobs, the page's one
    mention of the symlink: *"Check if your dataset node has glue arn prefix in the namespace of the node
    or in the "symlink" facet of the node."* The page names no Athena and no dbt. The Redshift capture
    leaves out external tables, `COPY` and `UNLOAD`, `MERGE` and `UPDATE`, events over 16 MB and
    datashares, and its runs are read with `list-job-runs` and `get-job-run` on the connection's
    `lineageJobId`;
  - the API's operations: `PostLineageEvent`, `GetLineageEvent`, `ListLineageEvents`,
    `DeleteLineageEvent`, `QueryGraph`, `GetLineageNode`, `ListLineageNodeHistory`.
- **[Claude] AWS's catalog pages.** Of the pages asked for on 2026-11-16, those on data products, their
  publication, subscription, approval and republication, on an asset created by hand, on a Glue data
  source and on a metadata form loaded. The pages on publishing, on subscribing to a managed asset and
  on granting access were asked for under names the guide does not use and did not load;
  `REFERENCES.md` holds them under their own names from 6f's and Stage 19's readings, and step 1.5
  reads them again before the runbook quotes one.
- **[Claude] AWS's guidance for dbt** (read 2026-11-16): the Amazon MWAA guide's dbt page, for
  provisioned MWAA (a virtual environment with `dbt-core==1.9.4`, `dbt-redshift==1.9.1` and
  `dbt-postgres==1.9.0`, a `BashOperator` that copies the project to `/tmp`, nothing on lineage); the
  MWAA Serverless guide's page on custom code (a package of at most 250 MB, *"such as the HTTP,
  Snowflake, or dbt providers"*, *"The pre-installed version takes precedence."*, a table of the
  pre-installed packages that now lists `duckdb` 2.0.0, a DuckDB provider and the Amazon provider at
  9.38.0, no dbt operator and no word on OpenLineage); the Big Data Blog's post of 2025-06-24 (dbt on
  Redshift, `dbt-ol run`, an HTTP transport to a proxy of API Gateway, SQS and a Lambda that may
  transform an event before it posts it to the domain, the post's Airflow example needing the `name`
  and `namespace` of its inputs and outputs changed; the direct transport for *"cases where you don't
  need additional controls on your OpenLineage event stream"*; the sample's endpoint public and
  unauthenticated);
  awslabs' `runner-dbt-aws-airflow` 1.0.0 (dbt inside a Glue Spark job, a Glue interactive session, a
  Glue Python shell job, EMR Serverless or an EMR step; a `[lineage]` extra on OpenLineage 1.50.0; a
  failed post never changes dbt's exit code; written for MWAA); the two posts on `dbt-glue`.
- **[Claude] dbt's pages** (read 2026-11-16): `manifest.json` holds `parent_map` and `child_map`, and
  the page never uses the word lineage; column-level lineage is the hosted platform's (*"Requires an
  Enterprise or Enterprise+ plan with Catalog access"*) or dbt v2's, run locally with strict static
  analysis; dbt Core 1.12 is in active support until 2027-07-15, 1.11 in critical support until
  2026-12-18, and dbt v2.0 was released on 2026-09-14 under its own licence agreement; dbt v2's
  supported features name no Athena; `dbt-athena` is maintained by dbt Labs and `dbt-glue` by the
  community (*"dbt support: Not Supported"*); under an Athena workgroup with a default output location
  `s3_data_naming` *"ignores any configured buckets and uses the location configured in the
  workgroup"*; *"dbt doesn't manage Lake Formation permissions"*.
- **[Claude] OpenLineage** (its naming and dbt pages, and the 1.55.0 wheels of 2026-10-29 unpacked and
  read): the wrapper starts `dbt` from `PATH` as a subprocess and returns its exit code; it imports
  `openlineage_sql` at module level, whose only Linux x86_64 wheel is tagged `manylinux_2_28`; a dataset
  is `<database>.<schema>.<table>` under `awsathena://athena.<region>.amazonaws.com`,
  `redshift://<host>:<port>` or `arn:aws:glue:<region>:<account>` by adapter; for `athena` it adds a
  symlink of namespace `arn:aws:glue:<region>:<account>` and name `table/<database>/<table>`, the
  account read from the profile's `assume_role_arn` or from `sts:GetCallerIdentity`; generic tests are
  gathered into one test job per model; the `amazon_datazone_api` transport takes `domainId`, `region`
  and `endpointOverride` and no timeout, builds its boto3 client with botocore's defaults, and gives
  it no Region when `endpointOverride` is set; the `transform` transport passes each event through a
  class of the caller's; the configuration is read from `OPENLINEAGE_CONFIG`, then `openlineage.yml` in
  the working directory, then the home directory.
- **[Claude] PyPI and Airflow's constraint file** (read 2026-11-16): dbt-core 1.11.17 (2026-11-06) and
  1.12.7 (2026-11-12), `dbt-athena` 1.11.1, `dbt-redshift` 1.11.2, `dbt-duckdb` 1.11.1. dbt-core 1.12.7
  requires `dbt-core-experimental-parser` from 2.0.11, published as a source distribution alone, whose
  build downloads a prebuilt `manylinux_2_28` wheel from dbt's GitHub release for the building machine
  and checks it against embedded hashes. `duckdb` 2.0.0's Linux wheels for x86_64 are tagged
  `manylinux_2_27` and `manylinux_2_28`. Airflow 3.0.6's constraint file for Python 3.12 pins `click`
  8.2.1, `protobuf` 4.25.8, `sqlparse` 0.5.3 and `mmh3` 5.2.0, against dbt-core 1.11.17's floors of
  8.3.0, 6.0 and 0.5.5 and `dbt-athena` 1.11.1's ceiling of 4.2.0 on `mmh3`; it also pins OpenLineage's
  packages at 1.37.0.
- **[Claude] The Athena adapter's released code** (the `dbt-athena` 1.11.1 wheel of 2026-09-07, unpacked
  and read 2026-11-16): `work_group` and `skip_workgroup_check` are profile keys, which the two pages
  read on dbt's site do not name; with `work_group` set the adapter calls `athena:GetWorkGroup`, and for
  a Hive table under a workgroup that enforces its output its `CREATE TABLE AS` carries no location; for
  an Iceberg table it always carries `location`, from `s3_data_dir` or `tables/` under `s3_staging_dir`,
  named by `s3_data_naming` (`schema_table_unique` by default), and the materialization refuses a naming
  without `unique`; a first run creates the table in one statement, and a later run swaps a `__ha`
  table in by two renames, through a `__bkp` name it then drops. By default the adapter's own S3
  client lists and empties the new location before a create, and a drop is its own calls too
  (*"Dropping relation via Glue and S3 APIs"*): every object under the table's location deleted, then
  `glue:DeleteTable`. With the model's `native_drop` (*"Relation drop operations will be performed
  with SQL, not direct Glue API calls"*) an Iceberg table or a view is dropped by an Athena statement
  and the deletion before a create is skipped; a Hive table keeps the default. `persist_docs` is the
  adapter's `glue:GetTable` and `glue:UpdateTable`.
- **[Claude] The readings of 2026-11-08, carried in** from the notes of an earlier cloud session: a
  build host outside this estate, no AWS call.
  - `awsds-workflows package-task` (`d856982`) refused dbt-core 1.12.6, and refused dbt-core 1.11.17
    with OpenLineage for `x86_64-manylinux2014`, `openlineage-sql` 1.55.0 having Linux wheels for
    `manylinux_2_28` alone. It built dbt-core 1.11.17 with `dbt-athena` 1.11.1 for
    `x86_64-manylinux2014`: 22,489,562 bytes, 72,686,012 unzipped, PyAthena 3.34.0 inside. With
    `openlineage-dbt` and `openlineage-python` 1.55.0 and `--platform x86_64-manylinux_2_28`:
    26,141,853 bytes, 82,894,731 unzipped.
  - `dbt-ol run` over two models, with the `amazon_datazone_api` transport and `endpointOverride` naming
    a local server: 6 `POST /v2/domains/<domain>/lineage/events` signed with boto3's credentials, each
    with a `Client-Token`, all at the end of dbt's run, and the warning
    `AmazonDataZoneTransport does not support timeout`. With the server's port closed: dbt's exit code,
    0, after 58.3 s, each of the 6 events failing after about 10 s of attempts
    (`Failed to send lineage event to DataZone`).
  - `dbt-ol build` over one seed, two models and two tests of one model, with the `file` transport
    (dbt-core 1.12.6, `dbt-duckdb` 1.11.1): 8 RunEvents of 1,913 to 5,527 bytes, with the facets
    `columnLineage`, `schema`, `documentation`, `dataSource`, `dbt_model`, `dataQualityAssertions` and
    `sql`; the seed emitted no event and was not an input of the model that read it.
  - Each send of dbt's telemetry (`snowplow_tracker`) waits up to 5 s, and `DO_NOT_TRACK=1` switches it
    off.
  - A third party's test, read that day (Classmethod, 2026-07-12): an event posted by hand showed in
    the portal only after a dataset took the namespace `arn:aws:glue:<region>:<account>:table` and the
    name `<database>/<table>`, the ARN of a table that was an asset.
- **[Claude] What the readings changed in the design**, each written where the stage file uses it:
  - the names: under the page's rule a `dbt-athena` dataset does not become the Glue table's ARN, so the
    first run posts the events as built and reads what the domain does with the symlink, and the second
    renames the datasets in the client through the `transform` transport (decision 3);
  - the archive: the parser's wheel asks for glibc 2.28, which nobody read on a worker, so the probe
    workflow runs first and a second archive, dbt alone for `manylinux2014`, is built beside the first;
  - the dbt line: 1.11, which `package-task` builds, with 1.12's parser a fetched wheel away (decision
    6);
  - the kind of task: a Bash task, since a Python task would run dbt on Airflow's pins (decision 2);
  - the project: `eighth-experimentation`, not `app-etl-dev` (decision 7);
  - the input: a Glue task of the application's own, so that the graph has two emitters, and no seed;
  - the model's files: for an Iceberg table the adapter writes the location itself, so the profile
    names the product database's own location, and a second run's swap by rename is step 2.5's
    reading;
  - the model's drop: the adapter's default deletes a table's files with the client's own S3 calls,
    which D28 keeps off a worker, so the model sets `native_drop` and a refused Iceberg table stops
    the stage for the user instead of falling back to a Hive table.
- **[Claude] The quotations**: each sentence the stage file, this log and `REFERENCES.md` quote from
  a vendor's page was read in the page itself on 2026-11-16, AWS's pages in their Markdown form, and a
  quotation from OpenLineage's or the Athena adapter's code is the wheel's own string.
- **[Claude] Written**: the stage file, this log, the rows in `docs/plan/stages/INDEX.md`,
  `docs/log/INDEX.md`, `docs/GENERAL_PLAN.md`, `CLAUDE.md`'s Current position,
  `docs/plan/waiting-on-the-user.md` and `docs/REFERENCES.md`, in one pull request against `main`.
  Every decision the stage names is due, none taken. The pull request takes no `SUP`, `TM`, `EXC` or
  `INT` id: each is written in the sitting that measures its subject.

## 2026-11-16 — step 1.1's facts and the decisions in the user's words; the job's isolation reopened

- **[user] The walk**, asked in the cloud session's thread at 20:27 UTC: *"Vamos passar sobre cada
  item. Pergunte um de cada vez, com o contexto e itens que tenho que responder."* **[Claude]** asked
  step 1.1's facts and then the decisions one message at a time, each with its context, its options
  and its numbered items, and the user answered in the same thread. The answers below are verbatim,
  the times UTC. The session made no AWS call and applied nothing.
- **[user] The engine and the adapter** (20:32). The items asked: the engine dbt runs its SQL on today,
  the adapter's name, and whether that engine would stay with SageMaker Unified Studio.

  > 1. No lab, vamos nos ater ao que temos no próprio ambiente AWS. Vamos considerar que as fontes de
  >    dados serão tabelas no Glue Catalog ou no Redshift. O SMUS será o ambiente de desenvolvimento,
  >    então poderemos utilizar athena, redshift, ou glue jobs (Spark) para os processamentos, além de
  >    manipulação de dados persistidos diretamente em S3 do projeto.
  > 2. não sei.
  > 3. como dito no item 1, vamos nos ater ao que temos na própria AWS.

- **[user] The dbt line** (20:41). The items asked: dbt Core or the hosted platform, and the version.

  > dbt Core , código aberto, instalado e executado pela própria instituição.
  >
  > Sugiro seguirmos com a versão 1.11 por enquanto.

  **[Claude]** read the second sentence as decision 6 (a) and told the user so in the next message,
  keeping the move to 1.12 for the day its archive builds (6.4's first item), since 1.11's critical
  support ends 2026-12-18, and asking for an objection. None came. The version the institution runs
  was not stated.
- **[user] Lineage today** (21:48). The items asked: where lineage is read today, and whether the
  pipelines already emit OpenLineage.

  > Sobre este aspecto, considere que não tem nada oficial ou bem estruturado pela instituição. Existem
  > apenas propostas de utilizar a ferramenta de lineage do dbt, então estou entendendo que envolve usar
  > o dbt-docs. Como o dbt já é utilizado em alguns pipelines na instituição, isso facilitaria adoção.
  > Mas esta proposta não considera o fato de que o SMUS, que está sendo implantado na instituição,
  > trata lineage via DataZone.
  >
  > A proposta do estágio 20 é exercitar o caminho em que os pipelines novos desenvolvidos via SMUS
  > emitem lineage para o DataZone, e suporte casos de uso de usuários que desejam utilizar DBT como
  > ferramenta dentro do SMUS.

  **[Claude]** told the user that the premises take these words and that the runbook's §L gains a
  comparison of the dbt docs lineage with the catalog's, which the proposal leaves out.
- **[user] A project's size and a run's length** (21:54). The items asked: how many models a typical
  project holds (tens, hundreds or thousands) and how long a full run takes.

  > 1. dezenas.
  > 2. um caso típico pode demorar mais de 1h. então talvez seja melhor exercitar o caso em que o dbt
  >    roda dentro de um task que não tenha este limite de 60 minutos.

- **[Claude] The task cap, read again**, because no kind of task is outside it. AWS's MWAA Serverless
  pages (read 2026-11-16 in their Markdown form, through a page-reading agent): the quotas page's table
  has the columns Resource and Default, a row *Maximum task execution timeout* of 60 minutes and no
  column saying which quota is adjustable (*"You can request increases for some quotas, but other
  quotas can't be increased."*); the parameters page validates `execution_timeout` at a maximum of
  3,600 seconds, `retries` between 0 and 3 with a default of 1, and `retry_delay` between 0 and 300
  seconds with a default of 300; it lists `deferrable`, `trigger_rule` and `sla` among the task
  parameters it ignores, and names neither `wait_for_completion` nor a sensor's `mode`,
  `poke_interval` or `timeout`; the operators page lists `GlueJobSensor` and
  `SageMakerProcessingSensor`. This estate's own records: the cap covers the task that waits on a
  processing job, whose `MaxRuntimeInSeconds` is therefore at most 2,820 s, and a longer step is
  *"split or fire-and-poll"*, which nothing here has measured
  ([`sagemaker-application.md`](../plan/runbooks/sagemaker-application.md) §W, Stage 10 verification
  vii); the lint asks `retries: 0` of every task. **[Claude]** told the user at 21:59 that the limit
  holds for every task, the one that waits on a job included.
- **[user] The waiting form**, asked in the project's chat at 22:28: *"Então com DBT seria isso:
  disparar sem `wait-for-completion` e uma task separada de wait com retry a cada 60min, correto?"*
- **[Claude] Airflow's released code, for that question** (wheels from PyPI, read 2026-11-16):
  `apache-airflow-task-sdk` 1.0.6, uploaded 2025-08-29, the SDK beside the worker's Airflow 3.0.6, and
  `apache-airflow-providers-amazon` 9.38.0, uploaded 2026-10-17, the version the guide's pre-installed
  table lists.
  - Which try is retried (`airflow/sdk/execution_time/task_runner.py`): `AirflowFailException` and
    `AirflowSensorTimeout` end the task `FAILED` (*"If a sensor in reschedule mode reaches timeout,
    task should not retry."*, in a branch every sensor mode takes), while `AirflowTaskTimeout`,
    `AirflowException` and `AirflowRuntimeError` go to `UP_FOR_RETRY` while retries remain (*"We
    should allow retries if the task has defined it."*). A task with an `execution_timeout` runs
    inside a timeout that calls the operator's `on_kill()` and raises `AirflowTaskTimeout`.
  - So a waiting task is retried when its try ends by the task's own `execution_timeout`, and fails
    for good when the sensor's `timeout` ends it first. With the service's three retries, one waiting
    task covers about four hours.
  - `GlueJobOperator`: `wait_for_completion` is true and `stop_job_run_on_kill` false by default, so
    a try the cap ends leaves the run going. Below Airflow 3.3 `durable` takes the value of
    `resume_glue_job_on_retry`, false unless set, which makes a retried try look for the run it
    started, by the `--airflow_task_uuid` argument, instead of starting another.
  - `SageMakerProcessingOperator`: `wait_for_completion` is true by default, the class has no
    `on_kill`, and `action_if_job_exists` is `timestamp`, so a retried try starts a second job. Its
    form for a job past the cap is `wait_for_completion: false`, then `SageMakerProcessingSensor`.

  **[Claude]** answered the user at 22:38: the form holds when dbt runs in a job, each try of the
  wait has to end by the task's cap and not by the sensor's `timeout`, and one waiting task covers
  about four hours; none of it is measured on the service.
- **[user] The job's network isolation** (22:32), on the sentence of the fifth question that a
  processing job in this estate runs isolated from the network:

  > Sobre "No laboratório um processing job roda isolado da rede, por uma regra de proteção contra
  > vazamento de dados", acho que isso não faz mais sentido. O processing job deveria rodar na VPC do
  > projeto. Podemos reabrir este ponto no AWS-DataScience para ajustar?
  >
  > Um Processing Job deveria ter a mesma capacidade que um cientista de dados teria se ele mesmo abrir
  > um space no projeto. A única diferença é que no caso do Processing job este processamento é
  > comandado por um workflow.

  The fifth question's items were whether a processing job in the institution may run in the
  project's VPC without network isolation, whether one already did and reached Redshift or Athena,
  and whether the institution means to require isolation as this estate does. **[Claude]** took the
  message as that fact's answer, a job runs in the project's VPC, and said so; whether a job in the
  institution already ran so was not stated.
- **[Claude] The rule, read at `main` `c5e1718`**, recorded in the stage file's 0.14 and decision 13:
  - `DenySageMakerJobsWithoutNetworkIsolation` is one statement of
    [`terraform-modules/sagemaker-denies/`](../../terraform-modules/sagemaker-denies/main.tf), pinned
    at `sagemaker-denies-v0.2.0`, over `CreateTrainingJob`, `CreateProcessingJob`,
    `CreateHyperParameterTuningJob`, `CreateAutoMLJob`, `CreateAutoMLJobV2` and `CreateModel`. Three
    callers compose it: the persona sets (`identity/sso/`), the `Workloads` OU's document
    (`identity/org-policies/`, whose JSON a precondition compares with the pinned tag) and the
    project boundary of `sagemaker-prereqs`, which `sandbox/sagemaker/`, `staging/studio/`,
    `production/studio/` and `data-governance/publishing/` call.
  - It is Stage 6a step 3's, of 2026-08-16, and the module gives its reason: *"a job that runs in our
    subnets and can still open arbitrary outbound connections from inside the container is half a
    control"*. D38, taken after it, left no spoke a default route. `objectives.md` asks no isolation
    of a job.
  - The application's other tasks already run in the VPC with the project role: the Glue job on the
    project's network connections and the Python and Bash tasks on the worker
    ([`sagemaker-application.md`](../plan/runbooks/sagemaker-application.md) §N).
  - The proxy admits a plane by its source range: Sandbox's whole VPC meets SageMaker's allow-list,
    and Staging's and Production's `Workloads` ranges meet an empty one
    ([`NETWORK.md`](../NETWORK.md)). A processing job in a project's subnets and security group
    would therefore reach what a space reaches in Sandbox, and what the Glue job and the worker
    reach in a target. Nothing measured it.
  - AWS's pages (read 2026-11-16, Markdown form, through the page-reading agent). On a processing
    job in a VPC: *"SageMaker AI uses the subnet and security group details to create the network
    interfaces and attaches them to the processing containers."*, and *"This allows the processing
    job to connect to resources that exist in your VPC."*; the page names network isolation nowhere.
    On internet-free mode, a page titled for training and inference containers, which names
    `CreateTrainingJob`, `CreateHyperParameterTuningJob` and `CreateModel` and no processing job:
    *"No AWS credentials are made available to the container runtime environment."*, and *"Network
    isolation can be used in conjunction with a VPC."* The Tooling blueprint's parameter
    `enableNetworkIsolation`: *"Enables network isolation for training and deployed inference
    containers."*, which reads `true` in both Tooling stacks here (Stage 17 step 0.8).
  - What follows a change, none of it edited in this sitting and all of it pass 4's: the module's
    action list and a new tag, the callers' pins and the OU document's copy,
    [`POLICIES.md`](../../terraform-live/identity/org-policies/POLICIES.md)'s row, the battery's
    rows, `./aws/sandbox-orchestration.py`'s `SO-5`, the runbooks' statements of the rule, Stage 9
    step 3.1's note, a threat-model entry, and `awsds-workflows`' lint, whose `job` rule refuses a
    processing task without `EnableNetworkIsolation: true`. `./aws/deploytargets.py`'s `DT-11` reads
    the statements by `Sid` and stays as it is.
- **[user] The scope of that change**, on a card **[Claude]** posted at 22:38 with three options: the
  processing job in Sandbox, Staging and Production, which Claude recommended; the processing job in
  Sandbox alone; or every job and model. The user chose the first at 22:46, *"Processing job, nos três
  ambientes"*. **[Claude]** answered that training, tuning, AutoML and models stay isolated and that
  the change is written as decision 13, its tags and applies a laptop session's on the user's word.
- **[Claude] PyPI, for decision 1's Glue option** (read 2026-11-16, the JSON of each release):
  `dbt-glue` has no 1.11 release. Its 1.10.19, of 2026-02-18, requires `dbt-core~=1.10.19` and
  `dbt-spark~=1.9.3`; the next are 1.12.3, of 2026-08-27, and 1.12.4, of 2026-09-10, which requires
  `dbt-core~=1.12.4`, `dbt-spark~=1.11.0` and Python 3.10 or later. `dbt-spark` 1.11.0, of
  2026-07-16, requires `dbt-core<2.0,>=1.8.0rc1`, and its extra `session` asks
  `pyspark<5.0.0,>=3.0.0`. With dbt Core 1.11, Glue with Spark is therefore `dbt-spark` on the
  session of a Glue job, never `dbt-glue`'s interactive sessions.
- **[user] The decisions**, one question each, in the order asked. The options are as each question
  listed them, and the last column is the whole of the user's message. Decision 6 was question 11
  and stood answered since 20:41.

  | Decision | Asked | The options as asked | Claude recommended | Answered | The user's answer |
  |---|---|---|---|---|---|
  | 1, the engine | 22:47 | (a) Athena with `dbt-athena`; (b) Redshift Serverless with `dbt-redshift`, in a warehouse sitting inside the free trial; (c) Glue with Spark, `dbt-spark` inside a Glue job, `dbt-glue` having no 1.11 release | (a) first, (b) in the warehouse sitting, (c) read in the documentation alone | 22:49 | *"(a). Futuramente podemos revisar o plano para incluir outros conectores."* |
  | 2, where dbt runs | 22:53 | (a) a Bash task on the worker, for a run under 60 minutes; (b) a processing job in the project's VPC, started without waiting and awaited by a second task; (c) several Bash tasks, each with a part of the project (`dbt build --select`); (d) a Glue job as dbt's runtime | (a), then (b) once decision 13 is applied; (c) and (d) compared in the runbook | 22:54 | *"(a)"* |
  | 3, the dataset names | 22:55 | (a) the first run posts the events as `dbt-ol` builds them, and a transformer in the application renames the datasets only if the graph comes out split; (b) the transformer from the first run; (c) AWS's sample proxy, an API Gateway, a queue and a Lambda | (a) | 22:56 | *"(a)"* |
  | 4, the transport | 22:57 | (a) direct, the OpenLineage client calling `PostLineageEvent` as the project role; (b) AWS's sample proxy, over HTTP; (c) a file in S3 that a following task posts | (a) | 23:01 | *"(A)"* |
  | 5, a failed post | 23:03 | (a) the wrapper's default, the task ending by dbt's result and the failed post a warning in the log; (b) strict, the script failing the task; (c) two tasks, one running dbt and one posting | (a) for the exercise, (c) looked at again with 3.3's readings | 23:06 | *"(A)"* |
  | 7, the application | 23:06 | (a) a new `app-dbt`, Sandbox only, in `eighth-experimentation`; (b) the same in a new project, at the cost of one `sandbox/workflows/` apply; (c) `app-etl` extended with a dbt task | (a) | 23:09 | *"(A)."*, followed by the doubt below |
  | 10, the runbook's home | 23:11 | (a) a new `docs/plan/runbooks/catalog.md`; (b) sections added to `GOVERNANCE.md`; (c) sections added to `SMUS.md` | (a) | 23:15 | *"Sobre a pergunta 13, opção (a)."*, followed by the question on a grant for every project, below |

- **[Claude] How answers 1 and 2 were read**, each told to the user in the next message. Answer 1:
  Redshift, the stage's fourth pass until then, and Glue with Spark leave the stage for a later
  revision of the plan (*"Me corrija se o Redshift era para ficar."*, 22:53). Answer 2: the option as
  lettered, a Bash task alone, so the stage measures a run under 60 minutes and the other forms are
  compared in the runbook, measured by no pass, decision 13 standing as this estate's change (*"Se a
  intenção era (a) e depois (b), é só dizer."*, 22:55). No correction came to either.
- **[user] A doubt on decision 7's option (b)**, at 23:09 with the answer and again at 23:11:

  > Uma dúvida: se eu criar um projeto novo ele não tem por padrão acesso a feature de workflow?

  > Não entendi por qual motivo a opção (b) implicaria em alteração de terraform no `sanbox/workflows`

  **[Claude]** answered from [`serverless-workflows.md`](../plan/runbooks/serverless-workflows.md) §G
  and `terraform-live/sandbox/workflows/`. A new project has the workflow surface with no blueprint
  change, and its Python and Bash tasks run on the blueprint's policies alone. What it lacks is the
  slice's three statements, attached to each role named in `project_roles`, a list written by hand
  because SageMaker Unified Studio mints the role with the project; without them the stage's Glue
  task stops on `glue:GetJob`. The question had called them *"a permissão de workflows"*, which read
  as the feature being off. The answer (a) stood.
- **[user] A grant for every project**, asked at 23:15 with the last answer:

  > Sobre esta necessidade de apply, não poderia adotar uma solução que funcione para todos os
  > projetos, de forma que a criação de um projeto novo não precisse de apply para cada nome novo de
  > projeto?

  **[Claude]** read two pages of AWS's admin guide (2026-11-16, Markdown form, through the
  page-reading agent, each quotation confirmed character for character). The managed Tooling
  blueprint's page lists ten parameters, none of which adds a policy to a role the blueprint creates,
  and one setting for all of them: *"You set the permissions boundary at the blueprint configuration
  level using the `PermissionsBoundaryArn` regional parameter."* The custom Tooling blueprints' page:
  *"In an Identity Center-based domain, omit it, because your template creates the project role
  itself."*, its sample template giving that role AWS's three managed policies and no boundary, and
  *"You can create a project with a project profile that uses a custom Tooling blueprint only by
  using the API. You can't create this type of project through the SageMaker user interface."*
  Claude answered at 23:20 with four options: (a) the slice discovers the roles by name, which ends
  the hand-written line and keeps one apply for each new project; (b) a function attaches the policy
  when the role is created, an EventBridge rule and a Lambda holding `iam:AttachRolePolicy`, which
  nothing here measured; (c) a custom Tooling blueprint, whose template would name the policy, at the
  price of projects created through the API alone and of a template this repository maintains; (d)
  the list kept and the question recorded in the plan, outside this stage. Claude recommended (d):
  this stage needs no apply for its project, and `sandbox/bedrock/` and `sandbox/warehouse/` keep
  lists of the same kind, so an answer would serve all of them; (b) is the first to measure where
  projects are created often. Two sentences of that message said more than was read. *"o laboratório
  criou três projetos desde agosto"*: the reading is the list, which holds three roles, of projects
  created 2026-08-22, 2026-10-15 and 2026-11-14, and the projects created in that time were not
  counted. *"também vale abrir um caso com ela"*, of AWS, the gap being in its managed policies:
  Sandbox holds no Premium Support subscription (read 2026-11-14, Stage 19 decision 17 (d)), so a
  technical case is one the institution opens.
- **[user] The answer on that grant**, at 23:23: *"(D)."* The list stays as it is. The question is
  [open question 27](../plan/open-questions.md), with the four options and what each one needs
  measured, and [`waiting-on-the-user.md`](../plan/waiting-on-the-user.md) carries its row.
- **[Claude] Written**, in the commit that carries this entry: the stage file, with the premises in
  the user's words, the review rows, question 4 and its table, sections 0.2, 0.10, 0.12 and 0.14,
  steps 1.1, 1.6, 1.7 and 3.2, the fourth pass replaced by decision 13's change with verifications
  xii and xiii, the decisions as taken, and the cost, the rollback and what concerns the other
  sessions; `docs/plan/waiting-on-the-user.md`; `docs/plan/open-questions.md`, with question 27;
  `docs/plan/history.md`, with decision 13's entry; `docs/plan/stages/INDEX.md` and
  `docs/log/INDEX.md`; `CLAUDE.md`'s Current position; `docs/REFERENCES.md`. No module, slice,
  policy document or script was edited: pass 4 names each of them for the laptop session that takes
  it.

## 2026-11-17 — the plan reviewed for execution: the draft built and run against simulated services

- **[user] The request**, in the cloud session's thread at 23:39 UTC on 2026-11-16: *"Revise o plano do
  estágio novo, refinando o q for necessário, detalhando o passo a passo, e verificando se é exequível.
  Suba as correções necessárias no mesmo PR."* **[Claude]** answered at 23:40 that the stage would be
  read again step by step and each step checked against the repository and the packages. Claude read
  *"exequível"* as three checks: every step of "To execute" names its commands, who runs them, what is
  read, when it passes and when it stops; every command and every name is read against the repository,
  the runbooks, `awsds-workflows` and the released packages; and what runs with no AWS credential is run.
  The session made no AWS call, no apply and no portal act.
- **[Claude] The host and the trees.** The cloud session's host, outside this estate: Ubuntu 24.04.5 with
  glibc 2.39, uv 0.11.32, CPython 3.12.3 and jq 1.7, reaching PyPI and GitHub, with no AWS credential.
  This repository at `f3ac422`, the branch's head over `main` `c5e1718`, until the merge recorded below.
  `awsds-workflows` at `196acee`, the commit `examples/app-etl/.gitlab-ci.yml` pins. Each time below is
  UTC, from a file's modification time, a log's own line or the session's record of the command. The
  draft, the simulation and each run's files stay outside git, the pull request carrying the plan alone:
  they are kept among the cloud session's project files as `stage-20/app-dbt-review-2026-11-17.tar.gz`,
  which the laptop does not hold.
- **[Claude] The draft**, the application as "The application, task by task" lays it out, written in a
  scratch folder at 23:50 on 2026-11-16: `pyproject.toml`, `manifest.yaml` with its one stage, the
  workflows `app-dbt` and `app-dbt-probe`, `code/run-dbt.sh`, the package `src/app_dbt/` with the dbt
  project (the model `notional_by_desk`, `schema.yml`, `sources.yml` and the profile), the transformer
  `lineage.py` and the console script `bin/dbt`, a sample, and a stub where the Glue script goes. It
  holds no test, no README and no `scripts/dev-cli.sh`, and `ruff format --check` would rewrite one line
  of `lineage.py`: pass 1 writes the application from it and owes each of them.
- **[Claude] The lock and the archive** (the stage file's 0.15), `package-task` run from
  `awsds-workflows` `196acee` with `--platform x86_64-manylinux_2_28`:
  - At 23:50 on 2026-11-16, the three packages pinned as the plan named them (dbt-core 1.11.17,
    `dbt-athena` 1.11.1, `openlineage-dbt` 1.55.0) and no `exclude-newer`: `uv lock` resolved 86
    packages. With `--include code/run-dbt.sh --include code/dbt`, the shim the plan placed at the
    archive's root, `package-task` answered *"dbt já está na raiz do .zip: renomeie"* and the file's
    path. With `--include code/run-dbt.sh` alone it took 4.4 s to build 26,152,032 bytes, 82,944,996
    unzipped.
  - That archive, read: 5,104 entries, `run-dbt.sh` and `app_dbt/bin/dbt` stored with mode 755, and ten
    compiled modules, of which `openlineage_sql` asks for `GLIBC_2.28` and the nine others for 2.16 at
    most (`objdump -T`). `python3 -m zipfile -e` extracted every file at mode 644.
  - At 00:08, with the template's `exclude-newer` at `2026-11-03T00:00:00Z`, two weeks before the day,
    `uv lock` refused the pin: *"`dbt-core` was filtered by `exclude-newer` to only include packages
    uploaded before 2026-11-03T00:00:00Z. The requested version, v1.11.17, was published at
    2026-11-06T07:08:30.809Z."* With the packages named by range (`dbt-core>=1.11,<1.12`,
    `dbt-athena>=1.11,<1.12`, `openlineage-dbt>=1.55,<2`), the lock cut at 00:10 holds dbt-core 1.11.16
    of 2026-10-14, `dbt-athena` 1.11.1 and OpenLineage 1.55.0, 86 packages in 118,218 bytes. PyPI's
    metadata gives 1.11.16 the floors of 1.11.17, `click>=8.3.0`, `protobuf>=6.0` and `sqlparse>=0.5.5`
    (read 00:31).
  - At 01:05, the archive of the draft as the runs below used it: 26,119,606 bytes, 82,819,034 unzipped,
    5,102 entries, the two scripts at mode 755, the same ten compiled modules with the same glibc
    readings, and no boto3 or botocore at its root. A second build of the same tree, at 01:22, held
    26,119,608 bytes and the same root.
  - `awsds-workflows lint .` in the authoring mode read *"ok: 4 arquivo(s)"* at 01:20, and again at 01:23
    with the tool installed from its archive's URL at `196acee`, the form pass 1's `TOOL` takes.
- **[Claude] The simulation** (the stage file's 0.16). The worker is a CPython 3.12 environment holding
  `apache-airflow` 3.0.6 under its constraint file and boto3 1.43.1, the archive extracted beside it and
  first on `PYTHONPATH`. AWS is moto 5.2.5's Athena, Glue, S3 and STS behind a proxy that records each
  call and gives an Athena statement its effect in Glue, a create, a rename or a drop, and a listener
  that stands for the domain's endpoint through `endpointOverride`, answering 200, answering 403 or
  closed. Each case runs the task's command as the service renders it,
  `bash -c "bash <folder>/run-dbt.sh …"`, in a temporary folder under an empty environment. The cases ran
  four times, from 00:11, 00:45, 00:50 and 01:06. The first ran eleven of them on a harness that left two
  cases' calls in one trail file; the three others ran thirteen and agree case by case on the exit code,
  the calls and the events. The last, 01:06 to 01:08:

  | Case | Exit code | Seconds | AWS calls | Events the listener received | Task log, bytes and lines | Peak memory, kB |
  |---|---|---|---|---|---|---|
  | A first `dbt build`, the names as built | 0 | 7.9 | 17 | 6 | 3,453 and 34 | 213,096 |
  | A second build, `--names glue-arn` | 0 | 6.4 | 28 | 6 | 3,443 and 34 | 195,096 |
  | A database Glue does not hold | 1 | 0.3 | 1 | 0 | 1,008 and 12 | dbt not started |
  | The probe workflow's command, rendered | 0 | 0.8 | 10 | 0 | 7,321 and 254 | not read |
  | The `transform` task's command, rendered | 0 | 5.7 | 17 | 6 | 3,453 and 34 | 194,800 |
  | By hand, `-- debug` | 0 | 2.8 | 4 | 0 | 2,828 and 52 | 137,104 |
  | By hand, `-- run` | 0 | 6.1 | 25 | 4 | 2,900 and 30 | 189,184 |
  | Every file of the archive at mode 644 | 0 | 7.9 | 17 | 6 | 3,380 and 34 | 212,924 |
  | The profile with `skip_workgroup_check: true` | 0 | 8.3 | 27 | 6 | 3,458 and 34 | 222,188 |
  | The endpoint's port closed, `--attempts 1` | 0 | 5.9 | 17 | 0 | 124,912 and 772 | 194,664 |
  | The endpoint's port closed, botocore's default attempts | 0 | 51.5 | 28 | 0 | 125,442 and 772 | 194,972 |
  | The endpoint answering 403 | 0 | 5.8 | 17 | 6, each refused | 77,463 and 178 | 194,592 |
  | A test that fails | 1 | 5.9 | 17 | 6 | 3,781 and 39 | 194,828 |

  A case that follows another in the same simulated account meets the model's table and swaps it, the 25
  to 28 calls against 17. Over the four runs the default attempts against a closed port took 47.4, 45.0,
  57.5 and 51.5 s. Each of the ten cases that built or ran the model carries the transport's warning
  *"AmazonDataZoneTransport does not support timeout"*. The three cases whose posts failed read *"Emitted
  0 OpenLineage events"* and ended 0. What each case printed, its statements and its events are in 0.16.
- **[Claude] The account in the fixtures**, at 02:08: the runs above carried moto's default account,
  twelve digits the identifier check refuses in a tracked file. Under `MOTO_ACCOUNT_ID=000000000000`, the
  twelve digits the check admits, the two builds and the failing test read the same exit codes and six
  events each, the events and the trail naming that account alone. Pass 1's fixtures take that account
  (1.3).
- **[Claude] Every `aws` command of the stage file, read by the AWS CLI**: 59 commands and none refused,
  at 02:38 over the stage file as this entry's commit holds it, after 58 at 02:14 and 59 at 02:21 over
  its earlier text. A script takes each `aws` command out of the file's code blocks, gives each
  placeholder and shell variable a value, and runs it with aws-cli 1.46.3 (2026-11-05, the newest PyPI
  carries, reporting botocore 1.43.62), invented credentials and an endpoint on a closed local port. A
  command the CLI parses and validates against the service's model reaches *"Could not connect to the
  endpoint URL"*, and one it refuses stops before that. By service: `datazone` 19, `mwaa-serverless` 10,
  `glue` 8, `s3` 5, `athena` 5, `lakeformation` 4, `s3api` 3, `sagemaker` 2, `cloudtrail` 2 and `logs` 1.
  Each `--query` was then evaluated on the output shape botocore's model gives the operation: every path
  resolves but `Parameters.table_type` of `glue get-table`, a key of a free map. Eight operations have no
  earlier use in this repository: `datazone delete-lineage-event`, `get-asset`, `get-connection`,
  `get-lineage-event`, `get-lineage-node`, `list-data-source-runs` and `post-lineage-event`, and
  `s3api list-object-versions`. The check reads the CLI's parsing and the answer's shape, and no
  authorization and no behaviour of a service. The laptop runs the CLI's version 2, 2.37.12 on 2026-11-16
  (`SUP-370`), whose changelog (read 02:32, newest 2.40.4) names the delete from 2.35.5, *"Adds support
  for deleting lineage events in Amazon DataZone."*, `mwaa-serverless` from 2.31.38 and DataZone's
  lineage from 2.17.4. A space's CLI version is unread, and 3.4 reads it before the command runs there.
- **[Claude] The CLI's pagination in a command substitution** (`SUP-327`, read again). The plan's
  substitutions took the ids of a list call with `--max-items N` under `--output text`. Against a local
  stand-in for Athena that holds ten ids and honours `MaxResults` and `NextToken`, with aws-cli 1.46.3,
  at 02:09 and again at 02:31:
  `athena list-query-executions --max-items 4 --query QueryExecutionIds --output text` sent one request
  with no `MaxResults` and printed the four ids and a line `None`, and the substitution handed
  `batch-get-query-execution` five ids, `None` the fifth; `--max-results 4 --no-paginate` sent
  `MaxResults` 4 and printed the four ids alone, and `--max-results 4` by itself did the same. The stage
  file's substitutions take `--max-results N --no-paginate`.
- **[Claude] The shell and Python lines of the plan**, each run as written, at 02:14 and 02:15: the `jq`
  filter of pass 2's trail loop, over two invented events, one with every field and one with no optional
  field, printed two tab-separated lines with `-` and `{}` where a field was absent (jq 1.7);
  `git archive --output` and `tar -x`, on a scratch repository, extracted the application's folder alone
  with `run-dbt.sh` executable; the tar's member check printed `4 2 []`; 3.4's line printed a RunEvent
  that parses as JSON; and 2.2's line printed one `export` for each of the five names from a
  `space_values.json`.
- **[Claude] What the repository says of each pass**, read at `f3ac422` and again on the merged tree:
  - Pass 1 needs no AWS session, and its commands ran on the draft: `uv lock`, the lint and
    `package-task`. The rules it takes from the template are `examples/app-etl/pyproject.toml`'s
    `exclude-newer` and the hooks' `ruff` at 100 columns.
  - Pass 2's deploy and runs are §D's steps of
    [`sagemaker-application.md`](../plan/runbooks/sagemaker-application.md), through the template's
    `scripts/dev-cli.sh`. `make up ENV=sandbox ONLY=egress GROUPS=mwaa` raises what a deploy from a space
    needs: `athena`, `glue`, `lakeformation` and `sts` are in the endpoint module's core set, `datazone`
    is among `sandbox/egress/`'s extra services, and `mwaa` is an optional group of the slice. *Create
    database* and what it leaves are `SUP-184`'s, and the tar's flags `SUP-348`'s. No file answers the
    worker's side: its glibc, whether a script runs from its folders, and whether the project role's
    session on a worker passes Athena, Glue and Lake Formation. The probe reads the first two, and the
    editor's baseline and the first run the third, each with its stop.
  - Pass 3 turns each switch by an `export` and a run, with no deploy. What the domain does with either
    form of the names is its reading.
  - Pass 4 changes `sagemaker-denies`, whose newest tag is `v0.2.0`, and tags `sagemaker-prereqs` after
    `v0.10.0`, its boundary sourcing the denies by path. The callers are `identity/sso/`,
    `identity/org-policies/` with the OU's document, `sandbox/sagemaker/`, `staging/studio/` and
    `production/studio/`, by Recipes A and B of
    [`terraform-changes.md`](../plan/runbooks/terraform-changes.md). The battery's row is *"workloads:
    CreateProcessingJob not isolated (DenySageMakerJobsWithoutNetworkIsolation)"*
    (`aws/probes/probes.py`).
  - Pass 5 waits on [Stage 19](../plan/stages/stage-19-smus-native-data-product.md) step 4.12 and on
    decision due 11.
  - Rollback follows what Stage 19 did to retire `app-etl`'s application from `eighth-experimentation` on
    2026-11-14.
- **[Claude] What the review changed in the plan**, each written where the stage file uses it:
  - **The console script.** The plan carried a shim `code/dbt` to the archive's root through `--include`,
    a name `package-task` refuses. dbt Core's own console script travels as package data,
    `src/app_dbt/bin/dbt`, a Python file: with a shell script in its place the wrapper ran
    `dbt --version`, 1.9 s and a request to PyPI, and it takes 0.07 s to read the version from a Python
    file. `run-dbt.sh` uses a copy it marks executable where the extraction dropped the file's mode.
  - **The lock.** The plan pinned dbt-core 1.11.17, which the template's two-week `exclude-newer` keeps
    out of a lock cut that day. The three packages are named by range and the lock holds what the rule
    admits, and question 4 and decision 2 name the floors 1.11.16 and 1.11.17 share.
  - **The profile.** `s3_staging_dir` left `profiles.yml`. The adapter does not require it, and without
    it no statement carried a `ResultConfiguration`, so the workgroup's enforced output places the
    results.
  - **The task's command** starts `bash` on the script and passes each value in single quotes: the mode
    the worker's extraction leaves on `run-dbt.sh` plays no part, and the command does not end in `.sh`.
  - **The archive** is one build. The second archive, dbt alone for `manylinux2014`, left the application
    and stays as a way on if the probe reads a glibc below 2.28.
  - **The probe workflow** reads more: the tools on `PATH`, the task's folder and whether a script runs
    from it and from a `mktemp` folder, `sys.path`, the workgroup's enforced output, the database as Glue
    returns it and a count of `trades`. Each call is tried once and prints its answer or one `REFUSED`
    line.
  - **Pass 2** gained the identities and their profiles, the values each block starts from, a run's
    reading and the trail's loop as commands; step 2.0, the starting state, the archive and the tar, with
    nothing up; the editor's baseline in 2.1, the model's statement run from the query editor before a
    worker runs it; each step's expected readings, its pass and its stop; and step 2.7, the downs.
  - **Pass 3** gained the switches as `export` lines, one attempt on the runs whose endpoint does not
    answer, 3.4's commands and the CLI version that carries the delete.
  - **Pass 4** gained the modules' validation and the plan of a caller before the commit, the tags'
    commands, the table of applies with each account and profile, Recipe A's commands, the battery's
    command and 4.5's reads.
  - **Pass 5** gained the read of the link, and **Rollback** its commands, their order, their identities
    and what stays.
  - **Section 0**: 0.1, 0.2 and 0.7 carry more of what was already read, and 0.15 and 0.16 are new.
  - **The header, the tables and the lists**: the Status and Prerequisites rows, verifications i and iii,
    7.1's list of what a delete covers, and the `awsds-workflows` item of "What concerns the other
    sessions".
  - **Text**: no placeholder in angle brackets inside a quotation in italics, `git archive --output`
    where a pipe hid an exit code (Lesson 46), and the fixtures' account.
- **[user] `main` into the open branches**, in the project's chat at 02:21 and relayed to this session:
  *"Avise as sessões em andamento para fazer rebase em relação à main"*. **[Claude]** brought `main`
  `bcda72a`, pull requests #310 and #308, into the branch at 02:23 by a merge, commit `47be64d`, and
  pushed it: a pushed branch is never rebased here (`CLAUDE.md`, "The branch and its PR"). Claude told
  the user so in the thread and offered the rebase, with a forced push, on the user's word. The one
  conflict was `docs/log/INDEX.md`, where `main` rewrote Stage 19's row beside this stage's; the
  repository's six checks passed on the merged tree.
- **[Claude] The plan against what the merge brought**: Stage 19's item 31, release T's Terraform path
  retired and applied 2026-11-17, and its new order.
  - Unchanged: the modules, their callers and their pins (`identity/org-policies/` and `identity/sso/` at
    `sagemaker-denies-v0.2.0`, `sandbox/sagemaker/` at `sagemaker-prereqs-v0.9.0`, `staging/studio/` and
    `production/studio/` at `v0.10.0`, `data-governance/publishing/` at `v0.8.0`), origin's newest tags,
    `DT-11`, the runbooks' sections this stage names, and Stage 19 step 4.12 with the revocation it ends
    with. This stage's files name nothing of the retired path.
  - A job a release carries in a target takes the deployment project's subnets and group,
    `datazone-<project>-dev`, which `scripts/deploy-application.py` reads from the project itself. 4.5's
    sentence named `<env>/sagemaker/`'s job group, release T's network, and now names the project's.
  - `production/studio/` holds release G's unapplied change since 2026-11-16, so pass 4's apply of that
    slice follows release G's (Lesson 69). `staging/studio/main.tf` and `production/studio/main.tf` are
    one file under `./scripts/check-copies.py`, so 4.2 moves their pins together.
  - Stage 19's release guard is `examples/app-etl/scripts/check-catalog-export.py`, the path the review
    table now carries.
  - Stage 19 step 6.2 rewrites [`sagemaker-application.md`](../plan/runbooks/sagemaker-application.md) §N
    and §W, which 4.6 edits for a processing job: "What concerns the other sessions" says that the step
    that lands second starts from the other's text.
- **[Claude] What the simulation does not read**: Athena's, Glue's and Lake Formation's authorization of
  the worker's session; the engine's own effects, moto answering a statement without running it; what the
  domain does with an event, a symlink or a renamed dataset; and the worker itself, its glibc, its
  folders and its pre-installed packages. Passes 2 and 3 read each of them.
- **[Claude] Written**, in the commit that carries this entry: the stage file, as listed above;
  `docs/plan/waiting-on-the-user.md`, decision 13's row with release G's apply before
  `production/studio/`'s, and the Sandbox sitting's row with this stage's passes 2 and 3;
  `docs/log/INDEX.md`; `docs/AWS_SUPPLEMENT.md`, `SUP-327`'s reading of 2026-11-17; `docs/REFERENCES.md`.
  The pull request takes no new `SUP`, `TM`, `EXC` or `INT` id, and no module, slice, policy document or
  script was edited.
