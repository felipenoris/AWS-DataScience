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

## 2026-11-17 — the passes read against the laptop and the estate, with nothing up

Read by a subagent of the plan's review session as Sandbox's `InfrastructureAccess`, read-only. Nothing
was applied or written in AWS.

- **[Claude, a subagent] Pass 1 on the laptop**: `examples/app-dbt` exists neither in the worktree, nor in
  the project folder, nor on `origin/main`, where `git grep -l app-dbt` finds the stage file and this log
  alone; the draft and 0.16's fixtures are in the cloud session's tarball. The laptop is Darwin `arm64`
  with no container runtime, so 1.3's simulation, whose archive is built for `x86_64-manylinux_2_28`,
  cannot load its compiled modules here; `openlineage-sql` 1.55.0 publishes a macOS universal2 wheel.
  uv 0.12.13 and CPython 3.12.13 are installed, the pinned `awsds-workflows` resolves, and `bash` resolves
  to 3.2.57 before Homebrew's 5.3.15.
- **[Claude, a subagent] Versions on PyPI**: dbt-core's 1.11 line ends at 1.11.17 (2026-11-06), 1.12.7 the
  latest; `dbt-athena` 1.11.1 needs dbt-core `>=1.8.0rc1,<2.0` and pyathena `<3.35`; `openlineage-dbt`,
  `-python` and `-sql` at 1.55.0 (2026-10-29); a lock cut today takes dbt-core 1.11.16, as the draft's.
- **[Claude, a subagent] Passes 2 and 3's prerequisites hold**: the project role in `project_roles`;
  `sandbox/egress` on `vpc-egress-v0.19.0` with `datazone`; the house image's `NO_PROXY` naming
  `datazone.us-west-2.amazonaws.com`; image version 11 `CREATED`; the Athena workgroup `ENABLED`,
  enforced, engine 3, `SSE_KMS` under `dev/sys/athena/`; no `app_dbt` database, Glue job or workflow, and
  the three prefixes empty; `dev/` registered with the project role; the managed policy at v77 carrying
  Athena on tagged workgroups, `PostLineageEvent`, the Glue table writes and `GetDataAccess`.
- **[Claude, a subagent] Pass 4**: `sagemaker-denies-v0.3.0` and `sagemaker-prereqs-v0.11.0` are the next
  free tags (`git ls-remote --tags origin`), the second contended by Stage 17 passes 9 and 10; the files
  the stage did not name, written into 4.2 and 4.6.
- **[Claude] Written**: pass 1's head, the tree, 2.0, decision 9 (b)'s list, the D13 row, 4.2, 4.6 and
  "What concerns the other sessions" corrected; the waiting list's rows for the tarball and decisions 9
  and 11. Nothing in AWS changed.

## 2026-11-17 — pass 1 and pass 4's 4.1 to 4.3 handed out, and the catalog's runbook written

*Claude's hand, and a subagent's where marked, in a laptop session at the user's request of 13:42 UTC. No
AWS call for these steps.*

- **[Claude] The work handed out**, 13:53 to 13:54 UTC: 1.2 to 1.4, `examples/app-dbt/`, to one subagent,
  written again from the stage's prose, the waiting list's alternative to the cloud session's tarball; 1.5
  and 1.6, `docs/plan/runbooks/catalog.md`, to another; and 4.1 to 4.3 to a subagent working in a worktree
  of its own, which pushes the module tags alone. 1.2 to 1.4 and 4.1 to 4.3 are in progress at this entry.
- **[Claude, a subagent] 1.5 and 1.6**, done at about 14:30 UTC: `catalog.md`, 71,234 bytes, sections O, A,
  M, P, F, S, L and V, written from the repository and from the guide's pages read 2026-11-17, with the
  portal not re-read, which is the user's act. §L holds 1.6's desk readings, a processing job with a waiting
  task, several Bash tasks by `--select` and a Glue job as runtime, each with what carries a run past the
  worker's hour and what nothing measured, and no dbt reading yet. Its checks: every relative link and
  anchor resolves, `./scripts/check-plan-refs.py` prints `OK`, the 31 `SUP` ids and the two `EXC` ids it
  cites exist, and it holds no 12-digit number and no `@`.
- **[Claude, a subagent] The contradictions it read between sources**, left to the files that own them: the
  incoming-requests page is *Subscriptions* in the release notes of 2026-10-20 and *Subscription requests*
  in the guide and the portal; a database outside the environment is typed or picked from suggestions on
  the page of 2026-11-17, where the stage's layout says typed; what a source created on the *Data sources*
  page writes is unmeasured against `SUP-191`; every connection read had lineage on from creation, where the
  page says it is off by default (`SUP-207`); Stage 19's step 8 heading puts the source before the asset,
  against its own reading of 2026-11-14 and `SUP-366`; two lines of `GOVERNANCE.md` and two of `SMUS.md` are
  stale; `aws/catalog.py`'s `CT-3` header still reads zero subscriptions; `SUP-195`'s three statements in
  Staging's catalog policy against 6f 11.9's per-resource policies.
- **[Claude] Written**, 14:08 UTC: `promotion.md` §N.6 item 6, passes 2 and 3 in a Sandbox sitting with
  `GROUPS=mwaa` and no GitLab, before 2026-12-18, and 4.5 once 4.4's applies ran; item 2 places 4.4's five
  applies, with the battery's Phase 4b, before Stage 17 9.5's, both `studio/` slices taking the two changes
  in one apply (Lesson 69).

## 2026-11-17 — pass 1's 1.2 to 1.4 and 1.7, and pass 4's 4.1 to 4.3: the subagents' results

*Two subagents' hands where marked, then Claude's, in the laptop session of the user's request of 13:42 UTC.
No AWS write; the tags are the only push.*

- **[Claude, a subagent] 1.2 to 1.4**, 14:02 to 14:50 UTC, all from `examples/app-dbt/` with no pipe: 31
  files written from the stage's prose, the cloud draft's tarball not being on the laptop.
  - `uv lock`: *"Resolved 86 packages in 1.82s"*, dbt-core 1.11.16, dbt-athena 1.11.1, openlineage-* 1.55.0
    and PyAthena 3.34.0 under `exclude-newer = "2026-11-03T00:00:00Z"`.
  - The lint at the template's pin: *"ok: 4 arquivo(s)"*. `package-task . code/app-dbt.zip --platform
    x86_64-manylinux_2_28 --include code/run-dbt.sh`: *"code/app-dbt.zip: 26126295 bytes, 82835578
    descompactados, para o CPython 3.12 em x86_64-manylinux_2_28"*; ten `.so` modules, `openlineage_sql`
    asking for GLIBC_2.28 and the others 2.16 at most; boto3, botocore and PyYAML absent.
  - The simulation, `tests/simulation/simulate.py --fixtures`, on the host archive (`aarch64-apple-darwin`,
    28,621,986 bytes, 88,429,087 unzipped), since the laptop has no container runtime: every case's exit,
    calls and events equal the draft's table. The first build posted six signed events, *"Done. PASS=2
    WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=2"*, three `StartQueryExecution` naming the workgroup with no
    `ResultConfiguration` and no S3 call; the second, `--names glue-arn`, swapped the table and renamed
    every dataset to the Glue table's ARN; with the port closed and `--attempts 1` it ended 0 with no
    event; a failing test ended 1 (*"Done. PASS=1 WARN=0 ERROR=1"*). Step 1.3's three criteria are met.
  - `uv run pytest`: *"51 passed, 3 skipped in 5.24s"*, the skips being the three files' stored modes while
    untracked; ruff, the identifier rule (*"31 files scanned, 0 finding(s)"*), `check-plan-refs.py` and
    `check-aws-supplement.py` clean.
  - Not read on the laptop: the probe's glibc line (absent on macOS) and its count before `load` runs,
    both 2.2's on the worker.
- **[Claude, a subagent in a worktree of its own] 4.1 to 4.3**, to 14:58 UTC: commit `5f121541` gives
  `sagemaker-denies` a `network_isolation_actions` list of five actions; `a808764a` pins
  `sagemaker-denies-v0.3.0` in `identity/sso` and `identity/org-policies` and `sagemaker-prereqs-v0.11.0` in
  `sandbox/sagemaker` (from v0.9.0) and both `studio/` slices (from v0.10.0), drops the action from the
  `Workloads` document and rewrites `POLICIES.md`'s row; `dca3427c` turns the processing row into an
  authorized contrast and adds *"workloads: CreateTrainingJob not isolated"*, `--list --phase ou` showing 58
  rows. Each tag pushed alone, both at `5f121541cf16a7f70c5d7993db7340204edd3cd6`, re-read at the end.
  Read-only plans: `identity/org-policies` *"Plan: 0 to add, 1 to change, 0 to destroy."*, the document
  2,840 → 2,808 bytes; `identity/sso` *"0 to add, 6 to change"*, every persona set losing the action;
  `sandbox/sagemaker` *"0 to add, 1 to change"*, the boundary alone; each `studio/` *"2 to add, 2 to change,
  2 to destroy"*, carrying Stage 17 9.5's change too. Its notes: 4.1's `git push … --tags` was not run, the
  tags going one at a time; `scripts/slices.py` has no plan, so Recipe A ran.
- **[Claude] Folded in**, 15:08 to 15:25 UTC: the examples committed (`4ecaa95b` for `app-dbt`, its three
  scripts recorded executable), the subagent's branch merged (`9dc27110`, one conflict in
  `scp-battery.md`'s training row, both sides' facts kept), and both `studio/` slices planned again from the
  merged tree, *"Plan: 2 to add, 2 to change, 2 to destroy."* each; 4.4's order gains `production/registry/`
  first (Stage 17 9.5), and 1.7's section is written in `upstream-releases.md`.

## 2026-11-17 — 4.4 applied with Stage 17's 9.5, the battery read, and 4.6 written

*Claude's hand, in the laptop session of the user's request of 13:42 UTC, on the user's message after
pull requests #26 and #313 merged: "Autorizo os applies do item 2" (`promotion.md` §N.6 item 2). Every
AWS call ran as the infrastructure user (`InfrastructureAccess`). Nothing was up.*

- **4.4's applies**, from a branch cut at `origin/main` `13581cd0`, which holds commit 2 (Lesson 79); each
  plan saved under the session's scratchpad and read statement by statement first, each followed by a
  re-plan reading *"No changes."*. `production/registry` went first (Stage 17 9.5), at 16:00:08 UTC.

  | Order | Slice | Plan | Applied (UTC) |
  |---|---|---|---|
  | 1 | `identity/sso/` | 0 to add, 6 to change | 16:01:26 |
  | 2 | `identity/org-policies/` | 0 to add, 1 to change | 16:02:03 |
  | 3 | `sandbox/sagemaker/` | 0 to add, 1 to change | 16:07:18 |
  | 4 | `staging/studio/` | 2 to add, 2 to change, 2 to destroy | 16:08:13 |
  | 5 | `production/studio/` | 2 to add, 2 to change, 2 to destroy | 16:09:05 |

  Each persona set and the `Workloads` document lost `sagemaker:CreateProcessingJob` from
  `DenySageMakerJobsWithoutNetworkIsolation`; the document's description changed with it, and
  `data_scientist_prod` gained Stage 17 9.5's repository. Each boundary changed the statement's action
  list alone. The `studio/` plans
  carried 9.5's workflows policy too; their person-session policy, known only after apply, read identical
  before and after.
- **The battery**, Phase 4b, 16:03:10 to 16:04:34 UTC, a minute after the document's apply (`SUP-350`):
  *"53 as expected, 0 unexpected, 5 not measured"*. In Production: *"workloads: CreateProcessingJob not
  isolated still authorized (Stage 20 decision 13 contrast)"* `ALLOWED` at `reached-authorization`;
  *"workloads: CreateTrainingJob not isolated (DenySageMakerJobsWithoutNetworkIsolation)"* `DENY-SCP`;
  the processing job's off-VPC, ceiling, inter-container and volume-key rows `DENY-SCP` as before. The
  report is `aws/output/scp-battery-20261117T130310.txt`, stamped in local time.
- **`DT-11`** (16:06:41 UTC): *"pass  DT-11  awsds-org-scp-ou-workloads on Workloads  attached, the 6
  job Sids present"*. The run exits 1 on the persona and Control Tower profiles, which were not signed
  in. `make check`: *"check: OK"*.
- **4.6**, after the applies. The rule is rewritten in `serverless-workflows.md` §J,
  `sagemaker-application.md` §C, §D and §W, and §N's matrix, whose processing job leaves the training
  job's row. Stage 9 step 3.1's design note now holds of a training job and a model, and 3.5's list names
  the narrowed statement; so does Stage 10's rule for the caller of a job. In `sagemaker-ai-ml.md`, the
  table's row excludes the action, and the settings bullet and the processing-job paragraph are dated
  with the applies. The demo job's docstring is rewritten. `./aws/sandbox-orchestration.py` `SO-5` now
  reports a job without isolation as a note, not a failure. `./aws/sandbox-ml.py` no longer reads a
  Processing step's isolation in `ML-6`. `aws/INDEX.md`'s rows follow. `threat-model.md` gains `TM-35`,
  accepted by the user with decision 13 on 2026-11-16, with its row in the network matrix.
- **Left**: 4.5, the job without isolation in Sandbox (`TM-35`'s measurement), in sitting A. 6.4's item for
  `awsds-workflows`, the lint's `job` rule, which still refuses such a task.

## 2026-11-17 — 6.4's lint item taken by `awsds-workflows`, and `app-dbt` pinned to it

*Claude's hand, in a cloud session of the user's Claude project, on the user's question of 18:55 UTC
after `awsds-workflows` pull request #27 merged, "há algo que precisa ser ajustado no projeto
`AWS-DataScience`?", and the user's choice of 19:19 UTC on a card, "Abrir o PR agora". No AWS call.*

- **`awsds-workflows` pull request #27**, opened 17:58 UTC on the user's choice of 17:39 UTC (*"Ok, pode
  fazer conforme sua recomendação"*, the option "Correções + regra job"), merged 18:55 UTC as `1a50ceb`.
  The rule `job` no longer reads a processing task's `EnableNetworkIsolation` and keeps the project's
  network, `EnableInterContainerTrafficEncryption`, the 2,820 s ceiling, a listed instance type and, in
  the promoted mode, `VolumeKmsKeyId`. The package's guide states the isolation as the job's choice, and
  its example job keeps it. The same pull request corrects the rule `manifest`'s reason for an
  `include` `*` on an item that names a connection, which the CLI 1.0.9 turns into a sync of the
  connection's whole folder.
- **The applications against `1a50ceb`**, at `7816fbe`, each with its pipeline's options: `app-etl` 9
  files, `app-ml` with `--model-item model` 6, `app-genai` 3 and `app-dbt` 4, each `ok`.
- **`app-dbt` pinned to `1a50ceb`** in `README.md` and `tests/simulation/simulate.py`. `package-task` is
  the same at `37cb5a6` and `1a50ceb`, whose diff touches the lint alone. `app-etl` (`196acee`), `app-ml`
  and `app-genai` (`37cb5a6`) keep their pins.
- **The text that said the lint still refuses**: this stage's Status, 4.5 and the item for
  `awsds-workflows`, whose other asks stay open; `TM-35`'s state, whose revision trigger "the lint's `job`
  rule relaxed" fired and leaves the list; `sagemaker-application.md`'s template job; and
  `sagemaker-ai-ml.md`'s processing-job paragraph, with its lint paragraph and operator table, which
  still described the lint before `37cb5a6`.

## 2026-11-17 — decisions 9 and 11 taken on cards in the review of the plan's open decisions

*Claude's sitting in a cloud session of the user's Claude project, no AWS call: the review of the plan's
open decisions the user asked for at 22:01 UTC, one card per decision under the user's default of
21:50 UTC (the path AWS suggests), recorded by pull request #317. Times are UTC.*

- **[user] The order of the review**, at 22:18, on the card *"Em que ordem quer ver as 64 decisões?"*:
  *"Por urgência"*.
- **[user] Decision 9**, at 22:19, on the card *"Promover o app-dbt para Staging e Produção pela CLI, ou
  mantê-lo só no Sandbox?"*: *"Promover pela CLI (caminho AWS)"*, against the card's recommendation.
  **[Claude]** Decision 7 moved to (b), a Sandbox project for `app-dbt` alone, the user's act on the
  waiting list; pass 1's one-stage `examples/app-dbt/` is extended to the three stages by passes written
  before the sitting that runs them.
- **[user] Decision 11**, at 22:21, on the card *"Quando ler a linhagem do dbt entre projetos e entre
  contas?"*: *"Depois da 4.12 do Stage 19"*, (a).

## 2026-11-18 — `app-dbt` in three stages and pass 8 written, with nothing up

*Claude, a subagent of the orchestrating session, in a laptop session on the orchestrator's brief that
carries decisions 7 (b) and 9 (b). Read-only AWS calls as the infrastructure user, permission set
`InfrastructureAccess`, through `awsds-infra-sandbox-1`, `awsds-infra-staging` and `awsds-infra-prod`; no
AWS write and no apply. Times are UTC.*

- **[Claude, a subagent] `examples/app-dbt/` in three stages**: the manifest's `dev`
  (`${DEV_PROJECT_NAME}`), `staging` (`deploy-staging`) and `prod` (`deploy-production`), `ATHENA_WORKGROUP`
  a stage variable of each, the catalog block with `skipPublish` (Stage 19 decisions 19 (c) and 20 (b)),
  and the `prod` bootstrap creating `app-dbt` and running it with `trailLogs`; `product.json` and
  `scripts/check-catalog-export.py`, the release guard; `.gitlab-ci.yml` from `app-etl`'s, on
  `gates-v0.6.0` and `awsds-workflows` at `1a50ceb`, with no image and each target's `athena` endpoint
  checked by its tag; `scripts/dev-cli.sh`, the README and the tests.
- **[Claude, a subagent] The lock** cut for Linux and macOS (`[tool.uv] environments`): *"Resolved 84
  packages"*, `httpx2-jsfetch` 1.0 and `tzdata` 2026.6 removed, `uv.lock` from 118,358 to 107,302 bytes, the
  runtime export from 80 pins to 78. pip-audit 2.10.1 skips a pin whose marker its runner does not match,
  and the gates' job fails when it audits fewer packages than the export pins.
- **[Claude, a subagent] The simulation** on the new lock, 01:46:49 to 01:48:23: exit 0, each of the
  thirteen cases' exit code, AWS calls and events as on 2026-11-17; the host archive 28,622,038 bytes,
  88,429,179 unzipped.
- **[Claude, a subagent] The targets read**, as `awsds-infra-staging` and `awsds-infra-prod`:
  - 01:00 to 01:20: each deployment project's Athena workgroup, `workgroup-5ido8bej1zoeq8-d6nu5aphq1e974`
    and `workgroup-d7qcazihvr3s7k-59niwej9axztow`, `ENABLED`, enforced, engine 3, its output under the
    project's `dev/sys/athena/` with `SSE_KMS`;
  - 01:37:37: Staging's `Tooling` environment provisions `athenaWorkGroupName`; 01:42:07: the workgroup's
    key is the project key;
  - 01:42:36: DataZone refuses `GetProjectProfile` to each target's `InfrastructureAccess`; the `app_etl`
    environments and sources, `deploy-staging-app-etl` `54jhe9989w0tcg` with source `52f18khk7kdi4w`, and
    Production's `azkybvkz7iea34` with source `5zggi2lr2ezy4w`;
  - 01:42:54: the `DataLake` environment configurations `d8f802ad-c74d-454a-84d1-e14012a434fa` (Staging)
    and `f403ecfc-2450-4f7c-b31a-182b320d9271` (Production), blueprint `d8w7c3fmbsz5cg`;
  - 02:10:21: both projects buckets exist; Staging's VPC holds `awsds-staging-s3-gateway` and
    `awsds-staging-dynamodb-gateway` alone, and VPC-Workloads no `awsds-prod-workloads-*` endpoint, both
    egress slices down;
  - 02:24:57: each deployment project's Athena connection, `project.athena`, `53jdm59v7gx0uo` in Staging
    and `cyrwjkq9blui6o` in Production, naming its workgroup;
  - 02:25:43: each deployment project's members, two groups as `PROJECT_OWNER` and one user as
    `PROJECT_CONTRIBUTOR`.
- **[Claude, a subagent] Sandbox read** as `awsds-infra-sandbox-1`, 02:12:51: `eighth-experimentation`'s
  Athena connection, `project.athena` (`cb9s1q15id7no0`), naming `workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c`;
  its members, one owner and three contributors.
- **[Claude, a subagent] Pass 8's `[P]` slices** written and planned (8.2), the identities read at
  01:57:50, each plan saved outside the repository and none applied:
  - `staging/foundation/`, with the alerts var-file, 01:58:32 to 01:58:48: *"Plan: 0 to add, 1 to change, 0
    to destroy."*, the deploy role's policy alone;
  - `production/foundation/`, with the alerts var-file, 01:59:43 to 02:00:02: the same line and the same
    change;
  - `staging/chains/`, 02:00:34 to 02:00:48: *"Plan: 12 to add, 1 to change, 0 to destroy."*;
  - `production/chains/`, 02:01:29 to 02:01:42: *"Plan: 6 to add, 1 to change, 0 to destroy."*.

  None carried another stage's change. `staging/studio/staging-test.tf`'s `product_databases` is
  described and not written: its apply fails while `app_dbt` does not exist.
- **[Claude, a subagent] The gates on the final tree**: 02:29:48, `make check` failed on
  `./scripts/check-plan-refs.py`, two hard-coded account counts in the stage file, rewritten; 02:31:38,
  `make check` OK. 02:31:49, `uv sync --locked` *"Resolved 84 packages"*, pytest *"84 passed"*, ruff *"All
  checks passed!"* and *"16 files already formatted"*; 02:32:01, the lint at `1a50ceb` with the pipeline's
  instance types *"ok: 4 arquivo(s)"*; 02:32:19 to 02:33:28, `package-task` for `x86_64-manylinux_2_28`:
  5,102 entries, 26,128,940 bytes, 82,843,244 unzipped, `run-dbt.sh` and `app_dbt/bin/dbt` at `0o100755`.
  `./scripts/check-gitlab-ci.py`, with the untracked pipeline added to its listing: `app-dbt`'s 19 jobs, 29
  names resolved, 109 script items in 9 files, OK; `check-identifiers.py`'s scan of the 8 untracked files:
  none.
- **[Claude, a subagent] Written in the stage file**: the Status, the Prerequisites and the Proves rows;
  passes 2, 3 and 5 for `app-dbt-dev`, the note under "To execute" removed; pass 8, its targets' table
  and steps 8.1 to 8.10; verifications xviii to xxii; decisions 14 to 17 due, each with its
  recommendation; Cost, Rollback, "What this stage does not do" and "What concerns the other sessions".
  `scripts/deploy-application.py`, `scripts/model-chain.py`, their hooks, `aws/cicd.py` and
  `sandbox/workflows/` are untouched: 8.1 and 2.0 describe their changes. Nothing in AWS changed.

## 2026-11-18 — 8.4's applies in Staging and Production

*Claude, the orchestrating session, on the laptop after the merge of PR #318 at 10:34:57, at the user's
word in the session's chat: "Autorizo os applies do estágio 20 8.4". The infrastructure user, permission
set `InfrastructureAccess`, through `awsds-infra-staging` and `awsds-infra-prod`, on a branch cut from
`main` at `ce39062d` (Lesson 79). No other Claude session ran on the laptop, read before the first apply.
Times are UTC.*

- **[Claude] The plans from `main`**, each saved outside the repository: `staging/foundation/` and
  `production/foundation/`, with the alerts var-file, *"Plan: 0 to add, 1 to change, 0 to destroy."* each,
  the deploy role's policy gaining `database/app_dbt` and `table/app_dbt/*` and losing nothing;
  `staging/chains/`, *"Plan: 12 to add, 1 to change, 0 to destroy."*, and `production/chains/`, *"Plan: 6
  to add, 1 to change, 0 to destroy."*, the chain role's policy gaining the workflows' ARNs, their
  encryption context and the stage-variables parameter. Each carried 8.2's change alone.
- **[Claude] The applies** of the saved plans:
  - `staging/foundation/`, 10:43:19 to 10:43:33: `awsds-staging-deploy-project` modified in 2 s, *"Apply
    complete! Resources: 0 added, 1 changed, 0 destroyed."*;
  - `production/foundation/`, 10:43:43 to 10:43:55: `awsds-prod-deploy-project` in 1 s, the same line;
  - `staging/chains/`, 10:44:03 to 10:44:19: the machines `awsds-staging-chain-app-dbt` and
    `awsds-staging-chain-app-dbt-probe` with their schedules, failure rules and targets, *"Apply complete!
    Resources: 12 added, 1 changed, 0 destroyed."*;
  - `production/chains/`, 10:44:29 to 10:44:44: `awsds-prod-chain-app-dbt` with its schedule, rules and
    targets, *"Apply complete! Resources: 6 added, 1 changed, 0 destroyed."*.
- **[Claude] The re-plans**, with `-detailed-exitcode`: exit 0 and *"No changes. Your infrastructure
  matches the configuration."* on the four slices. `list-schedules`: the six schedules of
  `awsds-staging-chains` and the six of `awsds-prod-chains` `DISABLED`, the three new ones among them.
- **[Claude]** Lesson 69's window is closed: a plan of these slices from `main` no longer carries this
  stage's change. 8.4's last apply, `staging/studio/`, waits on its line, written after 8.3.

## 2026-11-18 — decisions 14 to 17 taken, and what each changes written with nothing up

*Claude, the orchestrating session, on the laptop, in the session's chat: the four decisions presented one
at a time with their context, options and recommendation, at the user's request of 11:53 UTC ("Sobre as
recomendações para o Estágio 20, me apresente o contexto, as opções e as recomendações para as decisões
14 a 17 uma a uma"), and the user's answer at 14:02 UTC. Reads and plans only, as the infrastructure user,
permission set `InfrastructureAccess`, through `awsds-infra-staging` and `awsds-infra-prod`; nothing
written to AWS. Times are UTC.*

- **[user] Decisions 14 to 17**, on the question *"Você aceita as recomendações 14 (a), 15 (a), 16 (b) e
  17 (b), ou prefere responder uma a uma?"*: *"Decisão 16: (c)"*, *"Em relação às demais, aceito as
  recomendações."*, *"Pode refletir estas escolhas no plano e avançar na preparação do que for possível
  fazer neste momento sem o ambiente no ar."* Taken: 14 (a), 15 (a), 16 (c) and 17 (b).
- **[Claude] 14 (a)**: nothing written; the manifest's `skipPublish: true` stands and no task publishes.
- **[Claude] 15 (a)**: `athena` added to `core_services` in `staging/egress/main.tf` and
  `production/workloads-egress/main.tf`, each comment giving the reason; the DNS Firewall lists unchanged,
  `*.amazonaws.com.` and `*.api.aws.` covering the endpoint's names. Each slice planned with nothing up
  between 14:10 and 14:15, before and after the edit, each plan saved outside the repository: *"Plan: 17
  to add, 0 to change, 0 to destroy."*, then *"Plan: 18 to add, 0 to change, 0 to destroy."*, the one
  address the second plan alone holds `module.egress.aws_vpc_endpoint.interface["athena"]`, service
  `com.amazonaws.us-west-2.athena`, private DNS on, tag `Name` `awsds-staging-athena` and
  `awsds-prod-workloads-athena`, and every other resource planned the same in both. None applied: the
  endpoint exists from each slice's next `make up`.
- **[Claude] 16 (c)** in `examples/app-dbt/`: `LINEAGE_NAMESPACE` in the manifest's three stages,
  `${LINEAGE_NAMESPACE}` in `dev` and the literals `app-dbt-staging` and `app-dbt-prod` in the targets;
  the transform task's command ending `--namespace '{env.LINEAGE_NAMESPACE}'`; `run-dbt.sh` taking
  `--namespace`, letters, digits, `.`, `_` and `-`, `app-dbt` when left out, in place of
  `APP_DBT_NAMESPACE`; the tests, the simulation's run by hand and `dev` parameters, the README, and the
  stage's 2.0 block exporting `app-dbt-dev`. `uv run pytest`: *"86 passed in 5.57s"*; ruff clean; the lint
  at `1a50ceb`: *"ok: 4 arquivo(s)"*. `scripts/deploy-application.py` needs nothing: it gives a
  placeholder to every name another stage alone reads, and records the stage's declared variables.
- **[Claude] The simulation run again** on the change to `run-dbt.sh` (8.5), 14:15:32 to 14:17:08, on the
  host archive `package-task` at `1a50ceb` built (`aarch64-apple-darwin`, 28,624,802 bytes, 88,437,386
  unzipped): exit 0, each case's exit code, AWS calls and events as on 2026-11-17. The events' job
  namespace: `app-dbt` in every case that starts `run-dbt.sh` without the option, `app-dbt-dev` in the
  rendered transform task's six, `app-dbt-by-hand` in the run by hand's four.

  | Case | Exit code | Seconds | AWS calls | Events the listener received | Task log, bytes and lines | Peak memory, kB |
  |---|---|---|---|---|---|---|
  | A first `dbt build`, the names as built | 0 | 8.0 | 17 | 6, 6 signed | 3,741 and 37 | 244,352 |
  | A second build, `--names glue-arn` | 0 | 2.8 | 28 | 6, 6 signed | 3,731 and 37 | 204,624 |
  | A database Glue does not hold | 1 | 0.2 | 1 | 0 | 649 and 3 | not read |
  | The probe workflow's command, rendered | 0 | 0.8 | 10 | 0 | 10,232 and 234 | not read |
  | The `transform` task's command, rendered | 0 | 2.6 | 17 | 6, 6 signed | 3,746 and 37 | 203,760 |
  | By hand, `-- debug` | 0 | 1.5 | 4 | 0 | 3,489 and 53 | 145,312 |
  | By hand, `-- run` | 0 | 2.6 | 25 | 4, 4 signed | 3,196 and 33 | 195,280 |
  | Every file of the archive at mode 644 | 0 | 6.4 | 17 | 6, 6 signed | 3,624 and 37 | 244,320 |
  | The profile with `skip_workgroup_check: true` | 0 | 6.3 | 27 | 6, 6 signed | 3,746 and 37 | 245,488 |
  | The endpoint's port closed, `--attempts 1` | 0 | 2.7 | 17 | 0 | 147,696 and 775 | 203,728 |
  | The endpoint's port closed, botocore's default attempts | 0 | 45.6 | 28 | 0 | 148,225 and 781 | 204,432 |
  | The endpoint answering 403 | 0 | 2.7 | 17 | 6, each refused | 82,824 and 181 | 203,568 |
  | A test that fails | 1 | 2.7 | 17 | 6, 6 signed | 4,069 and 42 | 203,440 |

- **[Claude] 17 (b)**: the CLI 1.0.9's code read in the laptop's tool environment: `helpers/connections.py`
  sets an `ATHENA` connection's `workgroupName` from `athenaProperties.workgroupName`, and
  `helpers/context_resolver.py` flattens every connection of the project and resolves
  `{proj.connection.<connection>.<property>}`, matching a connection name with dots before the property.
  `awsds-workflows` cloned into the session's scratch folder, its branch
  `claude/workgroup-athena-cli-variable` committed as `2aa32cf` on `1a50ceb`: `CLI_VARIABLES` gains
  `{proj.connection.project.athena.workgroupName}` as `<ATHENA_WORKGROUP>`, with a test of the
  translation, a test of the lint's `projeto` rule, the guide's table row and the CLI's reading in
  `.claude/memory/cicd-cli.md`. Its tests, the network-marked deselected: 407 passed, 2 skipped;
  `tests/test_prepare_offline.py` fails on this Mac on `main` as on the branch, at the tool's platform
  guard (*"esta máquina é Darwin arm64, e a pasta só serve ao job preparada em Linux x86_64"*), and runs
  on Ubuntu in that project's pipeline. A copy of `app-dbt` whose two workflows name the variable: the
  branch's lint *"ok: 4 arquivo(s)"*; the lint at `1a50ceb` *"projeto: variável da CLI sem tradução:
  {proj.connection.project.athena.workgroupName}"* on both workflows, plus two `glue` findings on `load`'s
  script location, a refused translation leaving the text untranslated for the later rules. Not pushed:
  the push and the pull request wait on the user's word in this chat; `app-dbt`'s side lands after the
  merge.
- **[Claude] The plan's files**: the stage file's decisions, Status, 8.1, 8.5, the application's text, 2.0,
  2.3, 2.6, 8.9 and xix; `waiting-on-the-user.md`, `promotion.md` §N.6 item 2, `NETWORK.md`, and
  `CLAUDE.md`'s row.

## 2026-11-18 — `awsds-workflows`' pull request #28 for decision 17 (b)

*Claude, the orchestrating session, on the laptop, at the user's word in the session's chat: "Autorizo
push e PR", answering "Autoriza o push e o pull request do branch do awsds-workflows para a decisão 17
(b)?". No AWS call. Times are UTC.*

- **[Claude] Before the push**: `awsds-workflows`' `origin/main` still at `1a50ceb`, the branch's base, so
  nothing to merge; on the branch, `ruff check` and `ruff format --check` clean, and
  `tests/test_render.py` with `tests/test_lint.py` *"211 passed"*.
- **[Claude] The push and the pull request**: `claude/workgroup-athena-cli-variable` at `2aa32cf` pushed
  by 15:29:44 and [felipenoris/awsds-workflows#28](https://github.com/felipenoris/awsds-workflows/pull/28)
  opened against `main` by 15:29:56, its description in pt-BR as that repository writes its prose: the
  change, the CLI 1.0.9's reading, the reason, the verification, and the two `glue` findings that follow
  a refused translation at `1a50ceb`. The desktop app bound it to the session; its checks had not started
  at 15:30. Left: its merge, the user's; then 17 (b)'s change in `app-dbt` with the pin at the merge
  commit (8.5).

## 2026-11-18 — 17 (b)'s change in `app-dbt`, its pin waiting on `awsds-workflows` #28

*Claude, the orchestrating session, on the laptop, at the user's word in the session's chat: "Fiz o merge.
Pode fazer a mudança." No AWS call. Times are UTC.*

- **[Claude] The merge read before the change**:
  [PR #319](https://github.com/felipenoris/AWS-DataScience/pull/319) merged at 15:33:19 as `df49898b`,
  its tree equal to the session branch's head; `awsds-workflows` #28
  open, mergeable, its checks passed, and that repository's `main` still at `1a50ceb`. The pin waits on
  #28's merge, the user's; the rest of the change was written on a branch cut from `df49898b`.
- **[Claude] The change**: both workflows name `{proj.connection.project.athena.workgroupName}`, the
  transform task's `--workgroup` and the probe's second argument; `ATHENA_WORKGROUP` leaves the
  manifest's three stages and `LEG_FILLS`; `tests/rendering.py` resolves the connection's workgroup as
  the deploy does, `workgroup-simulated-project`, the value the simulation's services hold; the README
  and the stage's 2.0 type the workgroup for the run by hand alone. `uv run pytest`: *"86 passed in
  5.57s"*; ruff clean.
- **[Claude] The lint**, from `examples/app-dbt/` with the pipeline's `--instance-type` list: at #28's
  head `2aa32cf`, *"ok: 4 arquivo(s)"*; at `1a50ceb`, *"projeto: variável da CLI sem tradução:
  {proj.connection.project.athena.workgroupName}"* on both workflows and the two `glue` findings on
  `load`'s script location, exit 1.
- **[Claude] The simulation run again**, 15:39:19 to 15:40:46, on 14:15's host archive (`run-dbt.sh`,
  the package and the lock unchanged since): exit 0, every case's exit code, AWS calls and events as at
  14:15, the task logs the same to the byte but the failing test's, 4,068 bytes against 4,069; the probe's
  and the transform task's rendered commands carry `workgroup-simulated-project`.

  | Case | Exit code | Seconds | AWS calls | Events the listener received | Task log, bytes and lines | Peak memory, kB |
  |---|---|---|---|---|---|---|
  | A first `dbt build`, the names as built | 0 | 6.5 | 17 | 6, 6 signed | 3,741 and 37 | 244,304 |
  | A second build, `--names glue-arn` | 0 | 2.8 | 28 | 6, 6 signed | 3,731 and 37 | 204,320 |
  | A database Glue does not hold | 1 | 0.2 | 1 | 0 | 649 and 3 | not read |
  | The probe workflow's command, rendered | 0 | 0.8 | 10 | 0 | 10,232 and 234 | not read |
  | The `transform` task's command, rendered | 0 | 2.8 | 17 | 6, 6 signed | 3,746 and 37 | 203,744 |
  | By hand, `-- debug` | 0 | 1.5 | 4 | 0 | 3,489 and 53 | 145,344 |
  | By hand, `-- run` | 0 | 2.7 | 25 | 4, 4 signed | 3,196 and 33 | 195,328 |
  | Every file of the archive at mode 644 | 0 | 6.2 | 17 | 6, 6 signed | 3,624 and 37 | 243,600 |
  | The profile with `skip_workgroup_check: true` | 0 | 6.1 | 27 | 6, 6 signed | 3,746 and 37 | 245,056 |
  | The endpoint's port closed, `--attempts 1` | 0 | 2.7 | 17 | 0 | 147,696 and 775 | 203,696 |
  | The endpoint's port closed, botocore's default attempts | 0 | 44.5 | 28 | 0 | 148,225 and 781 | 204,448 |
  | The endpoint answering 403 | 0 | 2.8 | 17 | 6, each refused | 82,824 and 181 | 203,600 |
  | A test that fails | 1 | 2.7 | 17 | 6, 6 signed | 4,068 and 42 | 203,728 |

- **[Claude] Left**: the pin moved from `1a50ceb` to #28's merge commit in `.gitlab-ci.yml`, the README,
  `tests/simulation/simulate.py` and the stage's `TOOL`, and the lint read again at that commit.

## 2026-11-18 — `awsds-workflows` #28 merged, and `app-dbt` pinned to it

*Claude, the orchestrating session, on the laptop, at the user's word in the session's chat: "Fiz o merge
do #28". No AWS call. Times are UTC.*

- **[Claude] The merge read**: [`awsds-workflows` #28](https://github.com/felipenoris/awsds-workflows/pull/28)
  merged at 15:50:35 as `4613ddce2bfd2bf43cf79aa4d6bc1d07a9dbc362`, its tree `733f9c2` the same as the
  branch head `2aa32cf`'s. Between `1a50ceb` and `4613ddc` the diff touches `src/awsds_workflows/render.py`,
  its two test files, `docs/index.md` and `.claude/memory/cicd-cli.md`; `package-task` is the same at both.
- **[Claude] The pin moved** from `1a50ceb` to `4613ddc` in `examples/app-dbt/.gitlab-ci.yml` (the
  archive URL and its comment), the README (the `TOOL` line and the sentence naming the pin),
  `tests/simulation/simulate.py`, the stage file's pass 2 and the two sentences of
  `runbooks/sagemaker-ai-ml.md` that name `app-dbt`'s pin.
- **[Claude] The lint at `4613ddc`**, from `examples/app-dbt/` with the pipeline's `--instance-type` list,
  15:51:40: *"ok: 4 arquivo(s)"*. `uv run pytest` at 15:54:10: *"86 passed in 5.01s"*; `ruff check` *"All
  checks passed!"*, `ruff format --check` *"16 files already formatted"*.
- **[Claude] The records**: the waiting list's row for #28 removed; the stage's 8.5, decision 17, `Status`
  and the note to the other sessions, the Current position row, `promotion.md` §N.6 item 2 and the log
  index's row say merged. Left for 17 (b): 3.1's verdict in sitting A.

## 2026-11-18 — 8.1 written in `promotion.md` §N.6 item 10's pull request

*Claude, the orchestrating session, on the laptop, no AWS call. Times are UTC.*

- **[Claude] 8.1** is in [pull request #321](https://github.com/felipenoris/AWS-DataScience/pull/321),
  §N.6 item 10's, whose checks are in Stage 17's log of the same day: `--self-check` prints `app-dbt`'s
  stages `ok`, *"staging: 9 variable(s); app_dbt_deploy_staging_app_dbt,
  app_dbt_deploy_staging_app_dbt_probe"* and *"prod: 9 variable(s); app_dbt_deploy_production_app_dbt"*,
  with no state read and no image. `aws/catalog.py`'s `CHAIN_DEV_PROJECTS` waits on 2.0.
- **[Claude] The pin's path, for this log**: `app-dbt` moved to `37cb5a6` on 2026-11-17 with `app-ml` and
  `app-genai` (Stage 17's log of that day), to `1a50ceb` the same day (6.4), and to `4613ddc` today.

## 2026-11-19 — 2.0: `app-dbt-dev` created, its `sandbox/workflows/` line planned and `CHAIN_DEV_PROJECTS` written

*The user created the project in the portal. Claude, the orchestrating session, read it as the
infrastructure user through `awsds-infra-sandbox-1` and `awsds-infra-data`, reads only. Times are UTC.*

- **[user] The act**: *"Criei os projetos"*, with Stage 17's two (that log's entry of the same night).
- **[Claude] The project read**, by 2.0's commands at 00:19 and 00:20: the id `dnl3l158mbhrio`, created
  00:17:19, `ACTIVE` under `experimentation`; `Tooling` `55hp9teamegf4g` and `SageMakerAIDomain`
  `4mxdm39fu4j05s`, both `ACTIVE` by 00:20:41; the role `datazone_usr_role_dnl3l158mbhrio_55hp9teamegf4g`,
  carrying `awsds-sandbox-project-boundary` by `get-role`. 2.0's `list-roles` command read `None` on every
  role, the field omitted by documented contract, and the stage file now reads the boundary with `get-role`.
- **[Claude] The members**: the owner and the project's own role, an `IAM` user profile, and no group: the
  bundle role and `InfrastructureAccess` are not members yet. `list-connections` was refused to the
  infrastructure user, *"User is not permitted to perform operation: ListConnections"*, and answered the
  same caller on `app-etl-dev` at 00:32 (`project.athena`, `workgroup-ceweti7jbiu1hs-6kvndq6t2757rk`), so
  the workgroup is read after the membership.
- **[Claude] The house image**: the domain `d-nt4ujzbdpeqm` pins version 11 on both app types (`US-13`
  `pass` at 00:25), so 2.0's §C6 step is not needed.
- **[Claude] The workflows grant**: the role's line written with Stage 17's two and planned at 00:29,
  *"Plan: 3 to add, 0 to change, 0 to destroy."*; the apply waits on the user's word.
- **[Claude] `aws/catalog.py`'s `CHAIN_DEV_PROJECTS`** gains `dnl3l158mbhrio`, 8.1's last item:
  `--self-check` *"39 of 39 cases as expected"*. The live run, ending 00:36:16, wrote *"all checks
  passed"*, `CT-15` naming *"(app-etl-dev, app-dbt-dev)"*; its exit 1 is three `search` calls refused on
  the three new projects, *"User is not permitted to perform operation: Search"*, which `CT-19` notes as
  inventories not read. The infrastructure user's membership is what the instrument needs there too.
- **[Claude] Left**: the two contributors, then the workgroup's reading and 2.0's starting state; the
  apply.

## 2026-11-19 — 2.0's workflows grant applied with Stage 17's two lines

*Claude, the orchestrating session, ran the apply on the user's word, as `awsds-infra-sandbox-1`, the
infrastructure user's `InfrastructureAccess` in Sandbox, from the saved plan of 00:29. No other session was
running on the laptop. Times are UTC.*

- **[user] The authorization**: *"Autorizo o apply"*, answering the question that named `sandbox/workflows/`
  and its `3 to add`.
- **[Claude] The apply**, 00:49:36 to 00:49:48: one `aws_iam_role_policy_attachment.project` per role, each
  *"Creation complete after 1s"*, then *"Apply complete! Resources: 3 added, 0 changed, 0 destroyed."*
- **[Claude] The re-plan**, ending 00:50:15: *"No changes. Your infrastructure matches the configuration."*,
  exit 0 under `-detailed-exitcode`.
- **[Claude] The roles read**: `list-attached-role-policies` on `app-dbt-dev`'s, `app-ml-dev`'s and
  `app-genai-dev`'s roles lists `awsds-sandbox-workflows` beside AWS's
  `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy`, `SageMakerStudioProjectRoleMachineLearningPolicy`
  and `SageMakerStudioProjectUserRolePolicy`.
- **[Claude] Lesson 79**: the slice was applied from pull request #320's branch, so a plan of it from `main`
  proposes removing the three attachments until that pull request merges.
- **[Claude] Left**: the project's two contributors, then the workgroup's reading and 2.0's starting state.

## 2026-11-19 — 2.0: the contributors added, the workgroup and the starting state read

*The user added the members in the portal. Claude, the orchestrating session, read them as the
infrastructure user through `awsds-infra-sandbox-1` and `awsds-infra-data`, reads only. Times are UTC.*

- **[user] The act**: *"Editei os três projetos adicionando os contributors solicitados. Pode verificar."*
  The user asked first which name the member dialog shows for `InfrastructureAccess`, and Claude answered
  `AWSReservedSSO_InfrastructureAccess_59e5b26af457128d`, Sandbox's, as Stage 19's log of 2026-11-14 read it.
- **[Claude] The members**, read at 00:54:50: `app-dbt-dev`, `app-ml-dev` and `app-genai-dev` each list the
  owner, the project's own role and two `PROJECT_CONTRIBUTOR` groups, as `app-etl-dev` does. From the
  domain's account, `get-group-profile` answers each group's `rolePrincipalArn`: `06d426f2-…` is
  `awsds-deploy-sandbox-test` and `839bcde8-…` is `AWSReservedSSO_InfrastructureAccess_59e5b26af457128d`.
- **[Claude] The workgroups**, by `list-connections` at 00:55:11, refused before the membership:
  `app-dbt-dev`'s `project.athena` names `workgroup-dnl3l158mbhrio-55hp9teamegf4g`, `app-ml-dev`'s
  `workgroup-5rzplmk81vma34-5ae0dd6m1suvbk` and `app-genai-dev`'s `workgroup-b8fz4ovppjijv4-c9sdti5d2gaqs0`.
- **[Claude] 2.0's starting state**, at 00:55:40, each as expected: the workgroup `ENABLED`, enforced, on
  *"Athena engine version 3"*, its output under the project's `dev/sys/athena/`; *"Database app_dbt not
  found."* and *"Job not found."*; no `app_dbt_` workflow; `0` objects under `dev/data/catalogs/trades/`,
  `dev/data/catalogs/app_dbt/` and `shared/app-dbt/`; `search` answering with no asset.
- **[Claude] `./aws/catalog.py`** again: the run ending 00:58:58 wrote *"all checks passed"* and exited 0: the three `search` calls refused at 00:36 now answer, and `CT-19` reads every inventory, *"13 assets in 10 projects, 7 of them Glue tables"*.
- **[Claude] Left**: 2.0's archive and tar, built from the merged tree after pull request #320's merge,
  which moves `app-dbt`'s pin to `4613ddc`; then sitting A.

## 2026-11-19 — 2.0: the archive and the tar built from `main` at `103b4acc`

*Claude, in a session started by the orchestrating session, on the laptop with nothing up, no AWS call.
Times are UTC.*

- **[Claude] The tree**: `main` at `103b4acc`, pull request #320's merge at 01:02:23, which pins `app-dbt`
  to `awsds-workflows` `4613ddc`. At 01:06:53, 2.0's `git archive` of `examples/app-dbt` at that commit
  into `$HOME/tmp/stage20`, absent before: `source.tar`, 409,600 bytes, 51 members of which 36 files,
  extracted there.
- **[Claude] The archive**, 01:07:09 to 01:07:14, `package-task . code/app-dbt.zip --platform
  x86_64-manylinux_2_28 --include code/run-dbt.sh` with the README's `TOOL`, exit 0: *"code/app-dbt.zip:
  26129224 bytes, 82844295 descompactados, para o CPython 3.12 em x86_64-manylinux_2_28"*. 1.4's check
  printed `5102 82844295 ['0o100755', '0o100755']`, the draft's 5102 entries (0.15). Ten `.so` modules,
  `openlineage_sql` asking for GLIBC_2.28 and the others 2.16 at most; no `boto3`, `botocore` or `yaml`
  at the root, no bytecode, `testzip()` clean. SHA256 `7906e411f557393cf444cec20737022476505c512082776aee3fb9d60a3e1e07`.
- **[Claude] The tar**, 01:07:44, 2.0's `COPYFILE_DISABLE=1 tar --no-xattrs --no-acls --no-mac-metadata`
  from `examples/`, exit 0: `app-dbt.tar`, 26,531,328 bytes. The listing printed `51 37 []`: 51 members,
  37 files (the tree's 36 and the archive), no `._` member. No member carries a pax header, though the
  extracted files hold macOS's `com.apple.provenance` attribute; the four scripts are `0o755`, and the
  archive inside is byte-identical to the one built. SHA256
  `0b3ad0f98ed46af809cb539df0102f3c715723b9d07a868aad9192f41c21a1c8`.
- **[Claude] Left**: sitting A uploads `$HOME/tmp/stage20/app-dbt.tar` into a space of `app-dbt-dev`; its
  `sha256sum` there reads the digest above.

## 2026-11-19 — 8.3: the `DataLake` environments, and `staging/studio/`'s line applied

*Claude, in a session started by the orchestrating session, on the user's word in this session's chat:
"Autorizo os três atos", the answer to a question that named the two `create-environment` calls and the
apply of `staging/studio/`'s saved plan, each with its command. The infrastructure user, permission set
`InfrastructureAccess`, through `awsds-infra-staging` and `awsds-infra-prod`; reads also through
`awsds-infra-sandbox-1` and `awsds-infra-data`. The laptop's three other sessions (Stage 19, Stage 17 9.5
and 10.4, 6h decision 3) were told before the first write. Times are UTC.*

- **[Claude] Lesson 73, before the calls**, read in the CI/CD CLI 1.0.9's wheel unpacked in the laptop's
  `uv` cache, its four files matching the wheel's `RECORD`, and in this repository:
  - the CLI keys a project's connections by name (`helpers/connections.py`), the project's listing first
    and each environment's after it, and resolves `{proj.connection.<name>.<property>}` by name
    (`helpers/context_resolver.py`); it takes the project role from the first environment that
    provisions a `userRoleArn` (`get_project_user_role_arn`), and the `Tooling` environment by its
    blueprint, then by the `IAM` connection;
  - its catalog import remaps a `DataSourceReferenceForm` by the asset's `databaseName`, and falls back
    to the first source listed (`SUP-389`); its bootstrap action `datazone.create_connection` creates in
    `environments[0]`, an action no manifest here names;
  - `deploy-application.py`'s `product_source`, behind `--catalog-follow-up`, and `app_etl_tasks.py`'s
    `find_source` select the source whose filter names the stage's database and require exactly one;
    `scripts/tfhygiene/projects.py` finds the `Tooling` environment by `isDefaultToolingEnvironment`;
    `aws/catalog.py`'s `CT-14` expects one source per database, `aws/studio.py`'s `US-11` every
    environment `ACTIVE`. Release G's leg (`promotion.md` §N.8.5) and the template's pipelines run
    through these alone.

  No selector picks by position among what a second `DataLake` environment adds, if that environment
  adds no connection and provisions the same role.
- **[Claude] The targets read**, 02:10:44 to 02:15:24: each project held `Tooling` and
  `deploy-<env>-app-etl`, the latter's configuration the step's (`d8f802ad-…` in Staging, `f403ecfc-…`
  in Production) on the blueprint `d8w7c3fmbsz5cg`; that environment provisions `cloudFormationStackId`,
  `glueDBName`, `glueOutputUri` and `userRoleArn`, the last the `Tooling` environment's role; each
  project's nine connections are the `Tooling` environment's; one source each, `52f18khk7kdi4w` and
  `5zggi2lr2ezy4w`, on `project.default_lakehouse`. No environment named `deploy-<env>-app-dbt`, and no
  Glue database `app_dbt`: each catalog held `app_etl`, `curated`, `default` and `raw`.
- **[Claude] `staging/studio/`'s line**, `product_databases = ["app_etl", "app_dbt"]`, planned from this
  worktree's tree (`origin/main` at `573fe1df` and the line) from 02:17:56 to 02:18:24 into
  `$HOME/tmp/stage20-8-4-staging-studio.tfplan`: *"Plan: 2 to add, 0 to change, 0 to destroy."*, the
  `aws_lakeformation_permissions` `deploy_product_database` and `deploy_product_tables` on `app_dbt`.
- **[Claude] The domain's RAM share**: the Stage 19 session announced its permission's replacement at
  02:20 and reported the share at version 13 at 02:20:41, version 12 reading `UNATTACHABLE`. No DataZone
  call ran between the two messages; at 02:21:40 `list-environments` and `list-connections` answered in
  both targets as before.
- **[Claude⚡] The environments**, by the step's commands:
  - Staging, 02:23:05 to 02:23:07: exit 0, `bg5ndpa5etujo0` `CREATING`; `ACTIVE` read at 02:23:46, its
    deployment `SUCCESSFUL`;
  - Production, 02:26:58 to 02:27:00: exit 0, `adscxpx574cas0`; `ACTIVE` read at 02:27:38.
- **[Claude] 8.3's reads**, by 2.1's block, Staging at 02:24:03 and Production at 02:28:23, the same in
  both but the ids:
  - the environment provisions the stack `DataZone-Env-<environment id>`, `glueDBName` `app_dbt`,
    `glueOutputUri` the project's `dev/data/catalogs/` and the `Tooling` environment's `userRoleArn`;
  - the database `app_dbt`, *"Created by DataZone for project deploy-staging"* (`deploy-production`), at
    the project's `dev/data/catalogs/`, `CreateTableDefaultPermissions` `[]`, created at 02:23:25 and
    02:27:16;
  - the account's `IAMPrincipals` under `context.datazone.projectId=="<project>"` hold `CREATE_TABLE`,
    `DESCRIBE` and `DROP` on it, and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT` on its
    tables; the provisioning role `ALL`, grantable; the manage-access role `CREATE_TABLE` and grantable
    `DESCRIBE`, and grantable `DESCRIBE` and `SELECT` on the tables;
  - one source over it, `<account>-AwsDataCatalog-app_dbt-default-datasource`: `495urkkg5c7fyo` on
    `cron(23 2 * * ? *)` and `bjfmkla36ed3ps` on `cron(27 2 * * ? *)`, the minute of each one's
    creation; `READY`, `ENABLED`, `publishOnImport` false, no business-name generation, its filter
    `app_dbt` `INCLUDE *`, no environment, hanging from `project.default_lakehouse` (`5xxm5bdolo1fdc`,
    `5uc9mhko5zvfgw`), whose `glueLineageSyncEnabled` reads `true`;
  - the nine connections, every one still the `Tooling` environment's;
  - **no subscription target** on either new environment, read at 02:24:03, 02:24:29 and 02:25:33 in
    Staging and at 02:28:23 in Production, while `deploy-staging-app-etl` keeps
    `deploy-staging-app-etl-default-target` (created by `SYSTEM` 2026-11-11 at 15:28:54,
    `GlueTableAssetType` and `GlueViewAssetType`, `abac:CURRENT_PROJECT`, database `app_etl`). Neither
    Data Governance's nor Staging's trail holds a `CreateSubscriptionTarget` since 2026-11-11 15:00, that
    target's included: the trail does not record the `SYSTEM` write under that name.
- **[Claude] The target across projects**, between 02:25:35 and 02:26:58, each project's environments in
  creation order with their targets: in `eighth-experimentation`, `eighth-experimentation-lakehouse`
  (2026-10-26) carries one, `create-datalake-database-env-new_database-…` (2026-10-28) none, and the
  earlier `mydatabase` environment is `CREATE_FAILED`; in `test-experimentation`,
  `test-experimentation-lakehouse` (2026-10-20) carries one,
  `create-datalake-database-env-test_project_database-…` (2026-11-09) none; in `app-etl-dev`, the
  portal's `create-datalake-database-env-app_etl-…` (2026-11-14), its one `DataLake` environment, carries
  one. A project's first `ACTIVE` `DataLake` environment carries a default target,
  whatever path created it, and a later one none (`SUP-184`, appended). A deployment project subscribes to
  nothing (Stage 19 decision 14), so no step reads the absent target.
- **[Claude⚡] `staging/studio/` applied**, 02:27:19 to 02:27:30, the saved plan: both grants created in
  1 s and 2 s, *"Apply complete! Resources: 2 added, 0 changed, 0 destroyed."* The re-plan, 02:27:45 to
  02:28:09 with `-detailed-exitcode`: exit 0, *"No changes. Your infrastructure matches the
  configuration."* `list-permissions`: `awsds-deploy-staging` holds `DESCRIBE`, no grant option, on
  `app_etl`, `app_dbt` and each one's tables; `awsds-deploy-prod` holds nothing on either.
- **[Claude] `./aws/catalog.py`**, 02:29:00 to 02:31:33: exit 0, *"all checks passed"*; `CT-14` passes in
  both targets, *"2 source(s), over app_dbt, app_etl"*.
- **[Claude] `./aws/studio.py`**, 02:31:46 to 02:34:35: *"0 check(s) FAILED"*, 50 passing, the failed
  calls the persona profiles of the sessions not signed in; `US-11` passes in both targets,
  *"deploy-staging alone, 3 environment(s) ACTIVE"* and the same for `deploy-production`, its table
  listing each new environment with `app_dbt` and no target.
- **[Claude] Lesson 79's window**: `staging/studio/` was applied from this branch, so until its pull
  request merges, a plan of the slice from `main` proposes destroying the two grants.

## 2026-11-19 — 8.4: pull request #328 merged, `staging/studio/`'s window closed

*Claude, the orchestrating session, read the merge with `gh` and `git`, no AWS call. Times are UTC.*

- **[user] The merge**: *"Fiz o merge"*, of pull request #328, merged at 02:54:04 as `6c3cc62d`.
- **[Claude] The tree**: `6c3cc62d`'s tree is the branch head `9be8cf75`'s, `d08b994e`, so `main` holds
  `staging/studio/`'s `app_dbt` line the apply of 02:27 ran from, and Lesson 79's window, a plan from `main`
  proposing to destroy the two grants, is closed.

## 2026-11-19 — sitting A's pre-flight, with nothing up

*Claude, in a session started by the orchestrating session, on the laptop with nothing up: reads as the
infrastructure user, permission set `InfrastructureAccess`, through `awsds-infra-sandbox-1`, two
`terraform plan` runs, a `make up` dry run, and the GitHub API on `awsds-workflows`. No write. Times are
UTC.*

- **[Claude] The archive and the tar** (pre-flight 1): `examples/app-dbt/` holds the same tree,
  `ec837c34`, at `103b4acc` and at `origin/main` `0d5b573b`, and no commit between them touches it.
  `$HOME/tmp/stage20/app-dbt.tar` and the archive in its tree still read 2.0's digests, `0b3ad0f9…` and
  `7906e411…`, and the tar lists `51 37 []`. Nothing is rebuilt.
- **[Claude] `app-dbt-dev`** (pre-flight 2), from 15:01:45:
  - `dnl3l158mbhrio` `ACTIVE`; `Tooling` `55hp9teamegf4g` and `SageMakerAIDomain` `4mxdm39fu4j05s`,
    both `ACTIVE`, and no other environment;
  - the owner and three `PROJECT_CONTRIBUTOR`s: the project's own role (`8af0750c-…`, an `IAM` profile
    by `get-user-profile`), the bundle role's group (`06d426f2-…`) and Sandbox's `InfrastructureAccess`
    group (`839bcde8-…`);
  - `project.athena` (`dbddoq8ox6s3gw`, on the `Tooling` environment) naming
    `workgroup-dnl3l158mbhrio-55hp9teamegf4g`: `ENABLED`, enforced, *"Athena engine version 3"*, its
    output under the project's `dev/sys/athena/`;
  - the role carrying `awsds-sandbox-project-boundary`, and `awsds-sandbox-workflows` beside AWS's three
    policies;
  - 2.0's starting state as at 00:55: *"Database app_dbt not found."*, *"Job not found."*, no `app_dbt_`
    workflow, `0` objects three times, no asset and no data source, so 2.1 is not done;
  - the load task's two Glue network connections,
    `datazone-glue-network-connection-<subnet>-dnl3l158mbhrio-dev` in `us-west-2a` and `us-west-2b`, on
    the project's security group; the project's SageMaker AI domain `InService`, pinning
    `awsds-sandbox-dev-env` version 11 on both app types.
- **[Claude] The workflows grant** (pre-flight 3): `sandbox/workflows/` planned from this session's branch
  (`origin/main` at `0d5b573b`) from 15:03:30 to 15:04:05: *"No changes. Your infrastructure matches the
  configuration."*, exit 0 under `-detailed-exitcode`. With `-var training_pair_enabled=true`, 15:04:24
  to 15:04:38: *"Plan: 0 to add, 1 to change, 0 to destroy."*, `aws_iam_policy.workflows` in place with
  `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject` added. That change is
  Stage 17's training pair (its 9.5), applied in its sitting B after 2.2's readings (a) and (b). It
  reaches every listed role, `app-dbt-dev`'s among them, and grants on training jobs alone, which no run
  of this stage creates. No plan was saved.
- **[Claude] The endpoints** (pre-flight 4), read in `sandbox/egress/` and in `vpc-egress-v0.19.0`, its
  pin:
  - the module's core set: `sts`, `logs`, `kms`, `ecr.api`, `ecr.dkr`, `athena`, `glue` and
    `lakeformation`; the slice's extras: `sagemaker.api`, `sagemaker.runtime`, `sagemaker.studio`,
    `s3tables`, `datazone`, `ssm`, `ssmmessages`, `ec2messages`, `ec2` and `secretsmanager`; S3 through
    the `[P]` gateway;
  - a space's deploy and run call MWAA Serverless at `airflow-serverless.us-west-2.api.aws`, the `mwaa`
    group's one endpoint, beside DataZone, S3 and STS; a worker calls Glue, Athena, Lake Formation, STS,
    S3 and DataZone's `PostLineageEvent`; 4.5's operator calls `sagemaker.api`, and its job ECR, Athena,
    Glue, STS, DataZone and the proxy. All but MWAA Serverless are up with the slice, so `mwaa` is the
    one group, and `mwaa,mlflow,bedrock-base` holds it;
  - `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base DRY=1`, which runs nothing, lists
    `sandbox/egress/` and `sandbox/probes/` as its `[E]` slices and refuses `warehouse-compute/`
    (refusal 11);
  - the proxy's Sandbox plane carries GitHub's names since 2026-09-19 (6d decision 6), so 2.2's clone has
    a path, and `awsds-workflows`' `main` reads `4613ddc`, *"identical"* to the pin by the API's compare.
- **[Claude] §2's commands** (pre-flight 5), read against decisions 14 to 17, the pin `4613ddc` and
  `LINEAGE_NAMESPACE`:
  - 2.4's and 3.4's `get-lineage-node` named the dbt job's node under `app-dbt`, the namespace
    `run-dbt.sh` reads when `--namespace` is left out; under 16 (c) the transform task passes
    `app-dbt-dev` in `dev`, so the node is
    `app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run`. Corrected. The recorded
    events under `tests/fixtures/` carry `app-dbt`; no step of the sitting reads them.
  - 4.5 named the lint at `1a50ceb`; `app-dbt` pins `4613ddc`, one commit ahead of it by the compare.
    Corrected, with 4.5's proxy controls: `pypi.org` on the plane, and never the domain's own URL off it,
    which 6d decision 6's apply adds.
  - The values line and 2.6's export take the ids read above; 2.2's extraction checks 2.0's digest
    first, its clone's head is read against the pin, and 2.2 names the combined sitting's raise.
  - The rest reads as written: the workflows' names compose as `app-etl`'s did
    (`app_etl_app_etl_dev_app_etl`, Stage 19's log); the log group is Stage 19 decision 27's
    `/aws/mwaa-serverless/<domain id>-<project id>/<workflow>`; every field the blocks query is in the
    AWS CLI 2.37.12's output shapes (`get-workflow`, `list-lineage-events`, `get-lineage-node`,
    `list-data-source-runs`, `list-data-source-run-activities`), which carries `post-lineage-event` and
    `delete-lineage-event`. 14 (a) and 15 (a) change nothing in `dev`, and 17 (b)'s workgroup is the
    CLI's to resolve at the deploy.
- **[Claude] 3.1's verdict** (pre-flight 6), which 8.5 owes: 2.4 gives it when the graph is one,
  `as-built` staying in the targets' literal; 3.1 when it is split, `glue-arn` then written in the
  manifest and `tests/test_manifest.py` before pass 8's tag; neither form linking stops the stage (3.2).
- **[Claude] 4.5's workflow is unwritten**: the stage writes it at the pass, on a branch no tag carries,
  so its tar is a second one, and §2's order places it before the sitting, with 2.1's acts.
- **[Claude] Left**: 2.1's acts, the user's, with nothing up; 4.5's workflow and its tar; then sitting A
  by §2's order.

## 2026-11-19 — 4.5's workflow and the second tar, with nothing up

*Claude, in a session started by the orchestrating session, on the laptop with nothing up: reads as the
infrastructure user, permission set `InfrastructureAccess`, through `awsds-infra-sandbox-1` and
`awsds-infra-prod`, the offline tests, the lint and one build. No write to AWS. Times are UTC.*

- **[Claude] The workflow** `app-dbt-job`, its script `job/probe.py`, the manifest's lines and the tests,
  commit `30ab3539` on pull request #335:
  - one `SageMakerProcessingOperator` task, `retries: 0`: the image `{env.JOB_IMAGE_URI}`; the entrypoint
    `/opt/conda/bin/python /opt/ml/processing/code/probe.py`, the Region, the workgroup, the database and
    the domain as options; `ml.t3.medium` with 10 GB under `{env.PROJECT_KEY_ARN}`;
    `EnableNetworkIsolation: false` and `EnableInterContainerTrafficEncryption: true` in the project's two
    subnets and `{env.PROJECT_SG}`; the code input `app-dbt/job/` under the shared prefix; 900 s; the tag
    `AmazonDataZoneProject` `{proj.id}`; no output;
  - the manifest: `app-dbt-job` in `content.workflows` and in `dev`'s bootstrap alone; `JOB_IMAGE_URI`,
    `PROJECT_SG` and `PROJECT_KEY_ARN` in every stage, `dev` reading `${JOB_IMAGE_URI}`,
    `${DEV_PROJECT_SG}` and `${DEV_PROJECT_KEY_ARN}`, a target `none` and its leg's prefixed names; the
    storage item `job` in every stage;
  - `uv run pytest` *"97 passed"*, 11 of them `tests/test_job.py`'s; `ruff check` *"All checks passed!"*
    and `ruff format --check` clean; `awsds-workflows lint` at `4613ddc` with the pipeline's seven
    instance types *"ok: 6 arquivo(s)"*, exit 0.
- **[Claude] The lint's controls**, three altered copies outside the repository: the encryption off,
  exit 1, *"job: task job: NetworkConfig.EnableInterContainerTrafficEncryption tem de ser true"*; the
  folder `job` mapped in `dev` alone, exit 1, *"codigo: task job: a entrada de código"* under
  `shared/app-dbt/job/` *"está fora de"* the four folders every stage copies; the isolation on, exit 0.
  The second is why every stage maps `job`; the third is `1a50ceb`'s rule leaving the isolation to the
  task, which `tests/test_job.py` holds at `false`.
- **[Claude] The image's pull by the project role**, a precondition of the job no step had read:
  - `awsds-prod-ecr-dev-env`'s repository policy holds one statement, `AllowConsumerAccountsToPull`,
    granting Sandbox Account 1 `BatchCheckLayerAvailability`, `BatchGetImage`, `GetDownloadUrlForLayer`
    and `DescribeImages`;
  - `simulate-principal-policy` on `datazone_usr_role_dnl3l158mbhrio_55hp9teamegf4g` without context
    read `explicitDeny`, `AllowedByOrganizations: false` and no matched statement, `SUP-008`'s shape; the
    perimeter SCP denies an ECR push outside the organization alone, and the RCP an identity outside it.
    With `aws:RequestedRegion=us-west-2`, `BatchGetImage`, `GetDownloadUrlForLayer` and
    `GetAuthorizationToken` read `allowed` by `SageMakerStudioProjectRoleMachineLearningPolicy`, its
    `SageMakerECRPermissions` on every repository and its token statement on the caller's account;
  - that policy's `SageMakerCreatePermissions` asks for `EnableSageMakerMLWorkloadsPermissions` `true` and
    the project tag, and the role carries both, `AmazonDataZoneProject` `dnl3l158mbhrio`;
    `SageMakerStudioProjectUserRolePolicy`'s `AllowPassRoleOnProjectRoles` passes it to SageMaker;
  - `awsds-sandbox-dev-env` version 11 reads `CREATED`, its `BaseImage` and `ContainerImage` one URI by
    digest, `awsds-prod-ecr-dev-env@sha256:658c05d1…456c19f9`.
- **[Claude] The second archive and tar**, from `30ab3539` by 2.0's commands, without the `rm -rf`, in
  `$HOME/tmp/stage20/job/`:
  - `package-task` from 16:36:43 to 16:36:48, *"26129645 bytes, 82845727 descompactados, para o CPython
    3.12 em x86_64-manylinux_2_28"*; 1.4's check `5102 82845727 ['0o100755', '0o100755']`;
  - against 2.0's archive, the same 5,102 names and four entries apart, all in
    `app_dbt-0.1.0.dist-info/`: `METADATA` from 20,086 to 21,518 bytes, the README the package embeds,
    and `RECORD`, `direct_url.json` and `uv_cache.json` at their sizes;
  - the tar `app-dbt-job.tar`, 26,556,928 bytes, `55 40 []`: 2.0's members with `job/`, `job/probe.py`,
    the third definition and `tests/test_job.py`;
  - SHA256: the tar `903847a55dcc1b1510ccd4b0f0413c7e181e744ebe7215b9b1c86e59fb279abe`, the archive
    `74f8bc3948df4ff2a2f509995be361c97c85d19ddc4424b12a95240d79a129ec`; 2.0's tar still `0b3ad0f9…`.
- **[Claude] Left**: 2.1's acts, the user's, with nothing up; then sitting A by §2's order, 4.5 from
  `app-dbt-job.tar`. Pull request #335's merge carries the workflow into `main`, and 8.6 takes it off the
  tree before pass 8's tag.

## 2026-11-19 — sitting A's raise aligned with `promotion.md` §N.9's day 1

*Claude, in the same session, after merging `origin/main` at `c11a9829`, which carries pull request
#334's §N.9: the combined Sandbox sitting in three days, sitting A on day 1. Reads only.*

- **[Claude] The raise**: §N.9.2 raises day 1 with `make up ENV=sandbox GROUPS=mwaa`, after `make hub-up`
  and 6d decision 6's apply. The stage file's order and 2.2 named the single start's
  `GROUPS=mwaa,mlflow,bedrock-base`, and now name day 1's. The slices are the same: `slices.py up` takes
  `warehouse-compute/` only when `--groups` names `redshift` (refusal 11), so the pre-flight's dry run,
  `sandbox/egress/` and `sandbox/probes/`, holds for `GROUPS=mwaa`.
- **[Claude] A refusal**: `make up ENV=sandbox GROUPS=mwaa DRY=1`, which runs nothing, was refused by the
  session's auto-mode classifier, *"Destructive or Unwanted Actions"*, and not retried; the `Makefile`
  and `scripts/slices.py` were read in its place.

## 2026-11-20 — Pass 5 on §N.10's day 1, and pass 8 in R1 or R2

*Claude, in the session that regrouped the sittings (Stage 8's log, this day), with nothing up and no AWS
call; the plan revised.*

- **[Claude] Pass 5** rides `promotion.md` §N.10's day 1 (§N.10.3 step 8), raised with
  `GROUPS=redshift,mwaa`, after the subscriptions of §N.6 item 6; 5.0 and 5.1 run before it with nothing up.
- **[Claude] Pass 8** follows pull request #321's merge in R1 (§N.11.1 step 6). Its release sitting is R1
  when N.9's day 1 has run and 8.5 and 8.6 are done, otherwise R2, before 2026-12-18, with the build runner
  (`make gitlab-up BUILD=1`). 8.7's `awsds/app-dbt` and its job-token allowlist entry are R1's step 3.

## 2026-11-20 — Pull request #321's branch synced with `main`

*Claude, in the session that applied 6d decision 6 and Stage 17 decision 7 the same day, on the user's request to prepare every pending sitting before raising anything and to minimise the plan's running time (*"otimize o plano e faça todas as preparações necessárias para que o tempo necessário para executar o plano seja minimizado"*). The merge in a temporary worktree of this session, detached at the pull request's branch,
`190b2424`; the one AWS read as the infrastructure user with `InfrastructureAccess` through
`awsds-infra-sandbox-1` (account Sandbox Account 1).*

- **[Claude] The merge** of `origin/main` at `5dfff219` (#344): one conflict, in
  `docs/plan/runbooks/sagemaker-application.md` §S's table, resolved by keeping this branch's row for the
  scripts and `main`'s row for `sandbox/workflows/` and `sandbox/bedrock/` (`application_roles`,
  `model_applications`).
- **[Claude] The checks** on the merged tree: `./scripts/deploy-application.py --self-check` exit 0, every
  stage of `app-etl`, `app-ml`, `app-genai` and `app-dbt` `ok`, `app-etl`'s nine variables per stage as on
  `main` and `app-dbt`'s twelve; `make check` OK; pre-commit's hooks passed on the merge commit.
- **[Claude] The push**: `00113780` to `claude/plano-estagios-execucao-5f64d8-n6-item10`
  (`190b2424..00113780`). R1's step 6 merges it after Production's leg, synced again with what `main` gained.
- **[Claude] 5.0's target**: `list-environments` on `app-dbt-dev` reads `Tooling` and `SageMakerAIDomain`
  alone, both `ACTIVE` since 2026-11-19, so 2.1's *Create database* makes the project's first `DataLake`
  environment, which carries the subscription target (`SUP-184`), and 5.0's link lands in `app_dbt`.
- **[Claude] 8.8's gate, dry**: `pip-audit` 2.10.1 over each lock's runtime set (`uv export --frozen --no-dev`), an approximation of
  the gates' job, which `awsds/ci-gates` holds: *"No known vulnerabilities found"* for `app-etl` (one
  package), `app-ml`'s `code` (48) and `app-dbt` (78), at 20:36 UTC. The gate itself runs on the laptop
  the day of each tag, before the tag (Lesson 77).

## 2026-11-21 — 2.1: `app_dbt` created in `app-dbt-dev`, and the editor's baseline

*The user acted in the portal as the Data Scientist User, with nothing up. Claude, in the session that
prepared every pending sitting (#345), read it as the infrastructure user through `awsds-infra-sandbox-1`
and `awsds-infra-data`, reads only. Times are UTC.*

- **[user] The first attempt**, refused by the portal, pasted verbatim:

  ```
  [Error] Insufficient permissions to create a new database. Please add a LakeHouseDatabase blueprint deployment setting with On Demand mode to the project profile.
  ```

  then *"Eu entrei novamente e agora funcionou..."*.
- **[Claude] The refusal read**: the profile `experimentation` (`dh60xbal05q64w`, last updated 2026-11-18
  18:45:34) carries `DataLake` (`d8w7c3fmbsz5cg`, the console's `LakeHouseDatabase`) as `ON_DEMAND`; the
  domain's `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant on that blueprint in Sandbox names `CONTRIBUTOR`
  projects of the domain unit `awsds-studio` (`bzq0cbh2gd0f4g`), created 2026-08-22. Data Governance's trail
  places the refused attempts in `app-genai-dev` (`b8fz4ovppjijv4`): the portal's `GetProjectProfile` and
  `ListDeployableEnvironmentBlueprints` on it at 02:36:30, 02:37:52 and 02:39:52, each answered, in the
  Data Scientist User's session on `awsds-data-studio-domain-execution`. The portal opened `app-dbt-dev` at
  02:41:01. `app-genai-dev` has the same profile, domain unit and two environments, and the user as its
  owner, so the refusal is unattributed (`SUP-390`).
- **[user] The act**, on `app-dbt-dev`: *Data → Catalogs → AwsDataCatalog → Create database* `app_dbt`,
  then the query editor's create of `editor_probe` and its drop; *"2.1 feito"*.
- **[Claude] 2.1's reads**, at 02:49:36, each as expected (`SUP-184`, 0.7):
  - the environment `au9oegx70xvyts`, `create-datalake-database-env-app_dbt-1795228956827`, `ACTIVE`,
    created 02:42:38, beside `Tooling` and `SageMakerAIDomain`; its subscription target `algy8t6358fits`,
    `<environment>-default-target`, created 02:43:05. The project's first `DataLake` environment carries
    it, and 5.0's link lands in `app_dbt`;
  - the database, created 02:42:55 by the provisioning role's `AmazonDataZoneEnvironmentDeployer` session:
    *"Created by DataZone for project app-dbt-dev"*, at
    `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/dnl3l158mbhrio/dev/data/catalogs/`, with no default
    table permission;
  - Lake Formation: `IAMPrincipals` under the project's condition holding `CREATE_TABLE`, `DESCRIBE` and
    `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT` on its tables;
    `awsds-sandbox-smus-manage-access` `CREATE_TABLE` and grantable `DESCRIBE` on the database, grantable
    `DESCRIBE` and `SELECT` on its tables; the provisioning role every permission, grantable;
  - the source `3uof8bs4x693f4`, `READY`, `cron(43 2 * * ? *)`, created 02:43:06, `publishOnImport` false,
    its filter `app_dbt`, on `project.default_lakehouse` (`6h4cpmm4m2g74g`), `LAKEHOUSE`,
    `glueLineageSyncEnabled` `true`. The sittings' runs keep clear of 02:43 UTC;
  - the workgroup's statements: the `CREATE TABLE` at 02:46:01, a `SELECT * FROM app_dbt.editor_probe LIMIT
    100` at 02:46:25 and the `DROP TABLE` at 02:47:54, each `SUCCEEDED`;
  - under the dropped table's folder, no current object: four versions and seven delete markers;
  - the trail: `CreateTable` at 02:46:02 and `DeleteTable` at 02:47:57 as the project role, invoked by
    `athena.amazonaws.com`, the session's `sourceIdentity` the Data Scientist User's Identity Center id, no
    VPC endpoint, `insufficientLakeFormationPermissions` empty and the project role the Lake Formation
    principal: the conditioned grant admitted both (iii's baseline, the editor's half).
- **[user] Seen, not clicked**: the database's page now offers *"Change asset ownership across projects"*,
  *"Transfer metadata and subscription management to another project while retaining your AWS Lake
  Formation permissions, if applicable."* (`docs/plan/upstream-releases.md`).
- **Left**: sitting A from row 3 of its order, on §N.9's day 1.

## 2026-11-21 — Sitting A: 2.2, the space, the deploy and the probe

*Claude, in the session running `promotion.md` §N.9's day 1 on the user's *"Começar agora"*: the raise,
the render and decision 6's reading are 6d's log's entry of the same day. The space's acts are the
user's, as the Data Scientist User; the space's terminal runs as `app-dbt-dev`'s project role. Claude's
reads as the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (account
Sandbox Account 1). Times are UTC.*

- **[user] The space**: `jup` in `app-dbt-dev`'s blueprint domain, JupyterLab on `ml.t3.medium`,
  `awsds-sandbox-dev-env` version 11, created 03:28:04 and `InService` at 03:40:39, its app at 10.20.28.126.
- **[user] The tar**, dropped on the file browser: `sha256sum -c` read *"app-dbt.tar: FAILED"* three
  times while the upload ran, then *"app-dbt.tar: OK"*, and the tar extracted. The clone's head `4613ddc`,
  the pin; the values by `space_values.py` and the exports as written.
- **[user] The deploy**, *"aws-smus-cicd-cli 1.0.9 on /opt/awsds/venv/bin/python"*: the five files synced
  to `shared/app-dbt/` from 04:03:56; *"No managed Tooling.GA/Tooling.Lightning blueprint found; will try
  the IAM connection fallback"*, then the Tooling configuration resolved to the project's two subnets, its
  security group `sg-040ed6781b8c4449e` and Sandbox's project key, with no *"No custom VPC config"* line;
  the operator code uploaded once per `workflow.create` action, two copies for this deploy; both workflows
  created `READY` at 04:04:35 and 04:04:47; *"Deployment completed successfully!"*
- **[user] The probe's run**, `VulTqaEATnNLvZa` at 04:05:05. Before it, the CLI's `run` listed every
  workflow in the account and read `ListTagsForResource` refused on the nine of other projects, *"because
  no identity-based policy allows the airflow-serverless:ListTagsForResource action"*, as the project
  role's session `SageMaker`.
- **[Claude] The copies and the workflows**: under `shared/app-dbt/`, `code/app-dbt.zip` 26,129,224 bytes,
  `glue/load.py` 2,859, `inbox/trades.csv` 362, `workflows/app-dbt.yaml` 3,794 and
  `workflows/app-dbt-probe.yaml` 7,390, the two definitions larger than the tar's 3,508 and 7,389 by the
  values the CLI resolved; under `shared/operatorFiles/`, two copies of 26,129,224 bytes, the size of the
  laptop's archive. Both workflows `READY`, `manual_only`, in the project's two subnets and its security
  group, `CUSTOMER_MANAGED_KEY`, each logging under `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-dnl3l158mbhrio/`.
- **[Claude] The probe's run**: `SUCCESS` from 04:05:08 to 04:05:54, its one task `probe`, `BashOperator`,
  `SUCCESS` in 10 seconds, the worker's interface at 10.20.71.155 (04:05:14). Its log: the folder
  `/var/tmp/airflowtmp…`; `python3` at `/opt/mwaa-serverless-venv/bin/python3`, `bash`, `mktemp`, `cp`,
  `chmod` and `dirname` under `/usr/bin`; the script ran in the task's folder and in `mktemp -d`'s, the
  latter under `/usr/local/airflow/dags/`; Python 3.12.16 on *"Linux-6.1.190-x86_64-with-glibc2.34"*,
  glibc 2.34; Amazon Linux 2023.12.20261119; 2 CPUs, `MemTotal` 7,952,724 kB, no cgroup limit file; `/tmp`
  9,963 MiB free; 166 distributions, among them `apache-airflow` 3.0.6, `apache-airflow-providers-amazon`
  9.38.0, `boto3` 1.43.1, `sagemaker_studio` 1.0.28, `PyAthena` 3.17.1, `redshift-connector` 2.1.8,
  `duckdb` 2.0.0 and `dag-factory` 1.0.0; 36 variable names, `PYTHONPATH`, `TMPDIR` and three
  `OVERDRIVE__CMK__*` among them; the caller the project role's session `AmazonMWAAServerless`; the
  workgroup `workgroup-dnl3l158mbhrio-55hp9teamegf4g` `ENABLED`, enforced, Athena engine version 3, its
  output under the project's `dev/sys/athena/`; the database `app_dbt` at the project's
  `dev/data/catalogs/`; `SELECT 1` `SUCCEEDED`; the count of `trades` `FAILED` *"TABLE_NOT_FOUND"*, expected
  before 2.3; `ListLineageEvents` 10 events, each `SUCCESS`.
- **[Claude] The trail**, after its delay, each call from 10.20.71.155 as `AmazonMWAAServerless`:
  `GetCallerIdentity` through `sts`'s endpoint, `GetDatabase` through `glue`'s, `GetWorkGroup` and two
  `StartQueryExecution` through `athena`'s, `ListLineageEvents` through `datazone`'s; one `GetDatabase`
  invoked by `athena.amazonaws.com`. AWS Config's `GetDatabase` was refused twice at 04:06:48.
- **[Claude] 2.2 passes**: i's worker half, glibc 2.34; ii's first half, `SELECT 1`; the endpoint's answer
  to `ListLineageEvents`. A script runs in `mktemp`'s folder, so `run-dbt.sh` keeps its form. The
  expected *"one copy of the archive for each deploy"* reads one copy per workflow the deploy creates.
- **[user] 2.3**, `app-dbt`'s run `SzzngX9q8O3hZ7k` at 04:14:33, from the same terminal, the same nine
  `ListTagsForResource` refusals before it.
- **[Claude] 2.3's run**: `SUCCESS` from 04:14:39 to 04:18:21; `load`, `GlueJobOperator`, `SUCCESS` in 103
  seconds, which created the Glue job `app-dbt-dnl3l158mbhrio`, its run `SUCCEEDED` from 04:15:23 to
  04:16:55 (76 seconds of execution); `transform`, `BashOperator`, `SUCCESS` in 48 seconds. The task log
  reads the step's criteria: *"run-dbt.sh: dbt from /usr/local/airflow/dags/app_dbt/bin, this script
  executable"*; *"Running OpenLineage dbt wrapper version 1.55.0"*; *"Running with dbt=1.11.16"* and
  *"Registered adapter: athena=1.11.1"*, the lock's `dbt-core` and `dbt-athena`; the model *"OK 3 in
  5.38s"*, the test *"PASS in 2.65s"*, *"Done. PASS=2 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=2"*; six
  *"Successfully posted a LineageEvent: … in Domain: dzd-d8yrvx1ko7im6o"*, the transport's *"does not
  support timeout"*, *"Emitted 6 OpenLineage events"*, *"Underlying dbt execution returned 0"*; *"run-dbt.sh:
  peak memory 290516 kB, exit code 0"*.
- **[Claude] The tables**: `trades`, `EXTERNAL_TABLE`, `table_type` `ICEBERG`, registered with Lake
  Formation, at the project's `dev/data/catalogs/trades`, created 04:16:42 by the project role's session
  `GlueJobRunnerSession`, version 0; `notional_by_desk`, the same type, at
  `dev/data/catalogs/app_dbt/notional_by_desk/d37c35ec-…`, created 04:18:11 by `AmazonMWAAServerless`,
  version 1, its description *"The notional each desk traded, quantity times price summed over the desk's
  trades."* The model's location holds one Parquet file of 402 bytes, its metadata JSON and two Avro
  files. Lake Formation registers each project's `dev/` prefix with the project's role, `app-dbt-dev`'s
  among them, which covers both locations.
- **[Claude] The statements**, each under the workgroup's enforced output: the create at 04:18:09
  (`DDL`, 296 bytes scanned), the constant `SELECT '{"rowcount":3,"data_scanned_in_bytes":296}'` at
  04:18:12 and the test at 04:18:14, each `SUCCEEDED`, each carrying dbt's comment with `dbt_version`
  1.11.16.
- **[Claude] The events**, each `SUCCESS`, each created by `8af0750c-…`: the six dbt events under the job
  namespace `app-dbt-dev` (decision 16 (c)), the parent `dbt-run-app_dbt` and the nodes
  `awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run` and `….build.test`; the Glue job's 14 under
  `default`, from `app_dbt_dnl3l158mbhrio`. Saved to `$HOME/tmp/stage20/events-2.3/`. dbt's datasets are
  `awsathena://athena.us-west-2.amazonaws.com` `awsdatacatalog.app_dbt.trades` and
  `….notional_by_desk`, each with a `symlinks` facet naming the Glue table (`table/app_dbt/<table>`,
  `TABLE`), the output with `columnLineage` on `desk` and `notional`; the Glue job's output is
  `s3://awsds-sandbox-smus-projects` `…/dev/data/catalogs/trades`, its `symlinks` naming
  `table/app_dbt/trades`, its input the project's `shared/app-dbt/inbox`.
- **[Claude] The trail**: the Glue job from 10.20.1.240 as `GlueJobRunnerSession`, `CreateTable` `trades`
  through `glue`'s endpoint and 14 `PostLineageEvent` through `datazone`'s; the dbt task from 10.20.47.7 as
  `AmazonMWAAServerless`, `GetWorkGroup` and three `StartQueryExecution` through `athena`'s, `CreateTable`
  `notional_by_desk` and two `GetDataAccess` invoked by `athena.amazonaws.com`, `UpdateTable` through
  `glue`'s (`persist_docs`), six `PostLineageEvent` through `datazone`'s. No refusal.
- **[Claude] 2.3 passes**: i's modes, ii, iii's worker half, iv and v.

## 2026-11-21 — Sitting A: 2.4, the source's run and one graph

*Claude, in the same session. The portal's acts are the user's, as the Data Scientist User; Claude's reads
as the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account 1)
and `awsds-infra-data` (Data Governance) for the trail. Times are UTC.*

- **[user] 2.4**: the source `app_dbt` run in the portal, *Manage → Data sources*, after 2.3's run.
- **[Claude] The run**: `d2cehnogthh2c0`, `PRIORITIZED`, created 04:34:56, `SUCCESS`, `added` 2, `updated`
  0, `unchanged` 0, `failed` 0, `lineageSummary.importStatus` `SUCCESS`. The activities: `trades`
  `SUCCEEDED_CREATED`, asset `bra0895x5fjzww`; `notional_by_desk` `SUCCEEDED_CREATED`, asset `daefcycb3hhhn4`,
  its technical description the model's. Each activity's `lineageSummary.eventStatus` reads `None`.
- **[Claude] The assets**: `GlueTableAssetType`, revision 1, created by `SYSTEM` at 04:34:58, unlisted, their
  external identifiers `table/app_dbt/trades.dnl3l158mbhrio` and `table/app_dbt/notional_by_desk.dnl3l158mbhrio`
  (`SUP-343`), each `DataSourceReferenceForm` naming the run. `notional_by_desk`'s `GlueTableForm` carries
  `tableDescription`, *"The notional each desk traded, quantity times price summed over the desk's trades."*,
  and each column's `columnDescription`: `desk` *"The desk."*, `notional` *"The sum of quantity times price
  over the desk's trades, rounded to cents."*, the Glue table's comments `persist_docs` wrote. The asset's
  own `description` is empty and it holds no time-series form. `trades` carries no description: its table
  has no comments, `persist_docs` writing a model's alone, and `sources.yml`'s descriptions reach only the
  lineage node's `DatasetSchemaForm`.
- **[Claude] The graph**, from the asset back, by `get-lineage-node`, `list-lineage-node-history` and the
  node's version at each event (`--event-timestamp`): `notional_by_desk`'s asset node `6ljn21swt4l0y8` hangs
  from `6w7hp2vvi8kscw`, the dataset node `arn:aws:glue:us-west-2:<Sandbox>:table/app_dbt/notional_by_desk`;
  its version at 04:18:14 has upstream the job run `5cqirhi3wi3lw0`,
  `app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run/01a1fc53-9635-…`, whose upstream is
  `3s0gk0eg2o68pc`, `arn:aws:glue:us-west-2:<Sandbox>:table/app_dbt/trades`, the node `trades`' asset node
  `avyjoalaki4cy8` hangs from. That node's versions at 04:16:41 and 04:16:42 have upstream the Glue job's runs
  `b8r5wfvogmhmds` (`default.app_dbt_dnl3l158mbhrio.overwrite_by_expression.glue_catalog_app_dbt_trades/…`)
  and `514rsn88f19h5c` (`….atomic_replace_table_as_select.app_dbt_trades/…`), each from `cvurzd3gyts5qo`,
  the project's `shared/app-dbt/inbox`. The test's run `by4b2cm6q5sas0` (`….build.test/01a1fc53-9637-…`,
  04:18:18) hangs from the model's node. A node read at its latest version shows that event's edges alone:
  `6w7hp2vvi8kscw`'s latest, the test's, reads no upstream.
- **[Claude] vi passes**: the model's output node is the Glue table's ARN, the symlink honoured in an event
  with no Glue environment properties, and dbt's input is the node the Spark job wrote (`SUP-391`). Data
  Governance's trail since 04:14 holds 13 `CreateLineageNode`, 4 dataset nodes and 9 job nodes, none with an
  `awsathena://` identifier; no job run's node and no asset's node is among them. The graph is one, so
  decision 3 (b)'s transformer and 3.1 are not needed.
- **[Claude] The nodes' facets**: the job nodes, `….build.run` (`JobForm` `BATCH`, `DBT`, `MODEL`; `QueryForm`,
  the compiled SQL with the model's comment), `….build.test` (`JobForm` `TEST`) and the parent
  `app-dbt-dev.dbt-run-app_dbt`, carry no edges; the runs carry them, each `JobRunForm` naming the parent run
  `01a1fc53-46be-…`, the model's from 04:18:09 to 04:18:14, `COMPLETE`. The model's output node at 04:18:14
  holds `DatasetSchemaForm` with both columns' descriptions and `ColumnLineageForm`: `desk` from `trades`'
  `desk`, `notional` from `price` and `quantity`, each source table named
  `awsathena://athena.us-west-2.amazonaws.com/awsdatacatalog.app_dbt.trades`. The test left
  `DataQualityResultForm` on the node, `{"evaluations":[{"types":["not_null"],"details":{"COLUMN_NAME":"desk"},"status":"PASS"}]}`,
  and nothing on the asset.
- **[Claude] xvi passes**: the model's and its columns' descriptions reach the asset through the Glue table's
  comments. vii's portal half, what the *Lineage* tab draws, is the user's look.
- **[Claude] vii, the portal's half**, at the user's request, in the user's Chrome session through Claude in
  Chrome, the portal signed in as the Data Scientist User, from 04:46 to 04:52; reads and view toggles only.
  The project's *Manage → Assets*, `notional_by_desk`, *Lineage*, graph depth 5: one graph, left to right, the
  inbox (*Table / Amazon S3*, 5 columns, 01:16 UTC-03:00), the two Spark runs (*Job Run / Apache Spark*,
  `COMPLETE`), `awsdatacatalog.app_dbt.trades` (*Table / AWS Glue*, 5 columns), the dbt model's run (*Job
  Run*, `COMPLETE`, 01:18), `awsdatacatalog.app_dbt.notional_by_desk` (*Table / AWS Glue*), and an edge
  labelled *Cataloged* to the asset (*Asset / Inventory*, *Base*, 2 columns, 01:34). The portal names the two
  tables by dbt's names, each node's latest version. The model's node at its latest version, the test's,
  shows no columns, and selecting `price` on `trades` lights `price` on the inbox and nothing downstream.
  The node's panel reads *Source Type* `GlueTableDatasetSourceType`, the table's ARN as *Source
  Identifier*, *Created By* the project's role, and under *Additional Properties* the test's
  `dataQualityAssertions` facet (`"assertion": "not_null"`, `"actual": "0"`). Its *History* lists two
  versions at 01:18; *View Lineage* on the model run's opens the graph based on that version, the test's run
  drawn beside the asset under the node, and the node's *Schema* tab: `desk` from 1 column, `notional` from
  2, each *Type: unknown* with *View transformation*, the sources `price` and `quantity` under *Table:
  awsathena://athena.us-west-2.amazonaws.com/awsdatacatalog.app_dbt.trades*. *Highlight* on `price` lights
  `price` on `trades` and on the inbox: the column lineage crosses from dbt's step into the Glue job's, the
  Athena name resolved to the Glue table's node. The asset's *Data quality* tab reads *Rulesets (0)*,
  *Rule results (0)*, *Run history (0)*. The project's overview shows the banner *"Project profile
  blueprints have been changed for your project"* with *Update project*, not clicked.
- **[Claude] vii passes**: the portal draws one graph from the S3 input through the Glue job, `trades` and
  the dbt job to `notional_by_desk`, with column lineage at the model run's version; the test leaves its
  assertion on the model's node, as a facet and as the node's latest version, and nothing on the asset.

## 2026-11-21 — Sitting A: 2.5, the second run's swap

*Claude, in the same session. The space's acts are the user's, as the Data Scientist User; Claude's reads as
the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account 1).
Times are UTC.*

- **[user] 2.5**, `app-dbt`'s run `JCrmBgSmNqRrTXg` at 04:57:25, by 2.3's command from the same terminal,
  its variables read first (`echo "$DOMAIN_ID $LINEAGE_NAMESPACE"`), the same nine `ListTagsForResource`
  refusals before it.
- **[Claude] The run**: `StartedOn` 04:57:30, `CompletedOn` 05:03:13; `load`, `GlueJobOperator`, `SUCCESS` in
  219 seconds, the Glue job's run `jr_cebf2ded…` `SUCCEEDED` from 04:58:18 to 05:01:40 (173 seconds of
  execution, the first run's 76); `transform`, `BashOperator`, `SUCCESS` in 54 seconds. The task log: *"OK
  created sql table model app_dbt.notional_by_desk … OK 3 in 12.66s"*, *"PASS not_null_notional_by_desk_desk
  … PASS in 3.70s"*, *"Done. PASS=2 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=2"*, six posted events, *"Emitted 6
  OpenLineage events"*, *"Underlying dbt execution returned 0"*, *"run-dbt.sh: peak memory 293544 kB, exit
  code 0"*.
- **[Claude] The reads lag the run at both ends**, polled every 22 seconds: `get-workflow-run` read `QUEUED`
  and `list-task-instances` nothing through 04:59:28, `load` first listed at 04:59:50, while
  `list-workflow-runs` read `RUNNING` from 04:57:30 and the Glue job had started at 04:58:18; at the end
  `transform` and the run read `RUNNING` through 05:05:22, `SUCCESS` at 05:05:44, while dbt's log ended at
  05:03:11. The task instances lag as the run's
  state does, by about two and a half minutes (`serverless-workflows.md`'s *"The run's state lags its
  tasks"*, 2026-10-11).
- **[Claude] The statements**, each `SUCCEEDED` with no `StateChangeReason`: 05:02:52 `create table
  "awsdatacatalog"."app_dbt"."notional_by_desk__ha" with ( table_type='iceberg', is_external=false,
  location=…`; 05:02:56 `alter table app_dbt.notional_by_desk rename to app_dbt.notional_by_desk__bkp`;
  05:02:57 `alter table app_dbt.notional_by_desk__ha rename to app_dbt.notional_by_desk`; 05:03:00 `drop
  table if exists app_dbt.notional_by_desk__bkp`; 05:03:03 the constant `SELECT`, rowcount 3; 05:03:05 the
  test. The swap of 0.13, as 0.16 ran it.
- **[Claude] The trail**, every call as the project role's session `AmazonMWAAServerless`, invoked by
  `athena.amazonaws.com`: 05:02:54 `CreateTable` `notional_by_desk__ha`. Each rename is first an
  `UpdateTable` refused `UnsupportedOperationResponse`, *"RenameTable endpoint is not supported for Glue
  Catalog."*, `additionalEventData` `{"IcebergRestOperation":"renameTable"}`, its parameters the prefix
  `catalogs/<Sandbox>` and the source and destination names (05:02:56, 05:02:57), then a `CreateTable` of
  the new name and a `DeleteTable` of the old: `notional_by_desk__bkp` created at 05:02:56 and
  `notional_by_desk` deleted at 05:02:57; `notional_by_desk` created and `notional_by_desk__ha` deleted at
  05:02:58. The drop is `DeleteTable` `notional_by_desk__bkp` at 05:03:02; `persist_docs` the `UpdateTable`
  of `notional_by_desk` at 05:03:04 from 10.20.56.170 through `glue`'s endpoint. The Glue job's write is an
  `UpdateTable` of `trades` at 05:01:27 as `GlueJobRunnerSession` from 10.20.37.237 through the same
  endpoint, `trades` now at version 1 with its creation time of 04:16:42.
- **[Claude] The table**: `notional_by_desk` created 05:02:58 (the first run's 04:18:11), updated 05:03:04,
  `VersionId` 1 as the first run's, one version in `get-table-versions`, its description kept, at
  `…/app_dbt/notional_by_desk/378cf5f7-04a0-4d83-b7f1-083b293f390e` (the first run's `d37c35ec-…`).
  `notional_by_desk__ha` and `notional_by_desk__bkp` read `EntityNotFoundException`.
- **[Claude] The objects**: under the new location four current objects written at 05:02:55, one Parquet of
  399 bytes, the metadata JSON and two Avro files; under the first location no current object, its four
  versions noncurrent beside seven delete markers of 05:03:02, the drop's second: two each on the
  Parquet file, the manifest and the manifest list, one on the metadata JSON. The bucket's versioning keeps
  the first run's files as noncurrent versions.
- **[Claude] The grants**: Lake Formation lists on the table the project role's `ALL`, `ALTER`, `DELETE`,
  `DESCRIBE`, `DROP`, `INSERT` and its `SELECT`, the two rows the first run's table read at 04:43.
- **[Claude] The events**, each `SUCCESS`: dbt's six under `app-dbt-dev`, from the parent's `START` at
  05:02:41 to its `COMPLETE` at 05:03:10; the Glue job's 14 under `default`, from 05:00:38 to 05:01:29.
- **[Claude] x's half passes**: the swap ran, no rename or drop refused, the grants unchanged; the asset and
  the graph wait on the source's second run.
- **[user] 2.5's source**: `app_dbt` run again in the portal, *Manage → Data sources*, after the run.
- **[Claude] The source's run**: `6fipr3qxr7for4`, `PRIORITIZED`, created 05:09:58, `SUCCESS`, `added` 0,
  `updated` 2, `unchanged` 0, `failed` 0, `lineageSummary.importStatus` `SUCCESS`. The activities: `trades`
  and `notional_by_desk` `SUCCEEDED_UPDATED`, on the assets `bra0895x5fjzww` and `daefcycb3hhhn4`.
- **[Claude] The assets keep their ids**, each at revision 2, created by `SYSTEM` at 05:10:00 beside revision
  1 of 04:34:58, each `DataSourceReferenceForm` naming the run. `notional_by_desk`'s `GlueTableForm` names
  the new location, `…/notional_by_desk/378cf5f7-…`, and `updateTime` 05:03:04, where revision 1 named
  `d37c35ec-…` and 04:18:14; the table's description and both columns' descriptions are kept, `persist_docs`
  having written them on the new table. `trades`' form names `updateTime` 05:01:27, its location unchanged.
- **[Claude] The graph keeps its nodes**: Data Governance's trail, read through `awsds-infra-data` at
  05:14:46, holds no `CreateLineageNode` since 04:57, beside 20 `PostLineageEvent`, the Glue job's 14 from
  05:00:53 to 05:01:29 and dbt's six at 05:03:10 and 05:03:11. Every node gained versions under its own id:
  the table nodes `6w7hp2vvi8kscw` (`notional_by_desk`) at 05:03:04 and 05:03:10, beside 04:18:14 and
  04:18:18, and `3s0gk0eg2o68pc` (`trades`) at 05:01:24, 05:01:27 and 05:03:04, beside 04:16:41, 04:16:42
  and 04:18:14; the job nodes `….build.run` (`6eael36d03lyfk`) at 05:03:04, `….build.test`
  (`dpv0jnpy6a2ln4`) and the parent (`6fbpvdjy84hq4w`) at 05:03:10; the asset nodes `avyjoalaki4cy8` and
  `6ljn21swt4l0y8` at 05:10:00, the source's run, beside 04:34:58.
- **[Claude] The second run's job runs**: `6w7hp2vvi8kscw`'s version at 05:03:04 hangs from the model's run
  `c5hbxzn5im6lcg` (`….notional_by_desk.build.run/01a1fc7c-a7a7-…`, from 05:02:52 to 05:03:04, upstream
  `3s0gk0eg2o68pc`), its `JobRunForm` naming the first run's job,
  `app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run`, and the parent run
  `01a1fc7c-38ff-…`. The test's run `c8e2sp3c5j8f4g` (`….build.test/01a1fc7c-a7a9-…`, 05:03:10) hangs from
  the node, whose latest version, the test's, reads downstream that run and the asset node and no upstream.
  `3s0gk0eg2o68pc`'s versions at 05:01:24 and 05:01:27 hang from the Glue job's runs `4rt71px23p3ksw`
  (`….overwrite_by_expression.glue_catalog_app_dbt_trades/01a1fc7b-0898-…`) and `3uv1vzb973rh1s`
  (`….atomic_replace_table_as_select.app_dbt_trades/01a1fc7b-0745-…`), each from the inbox
  `cvurzd3gyts5qo`.
- **[Claude] x passes**: the swap leaves `notional_by_desk` a new table at a new location, created 05:02:58,
  with the first table's grants; the asset keeps its id and takes revision 2 at the new location; the graph
  keeps its nodes, a dataset node being the table's ARN, which names the table and not its location, and
  each run adds its job runs under the same jobs and a version to each node.

## 2026-11-21 — Sitting A: 3.3, the posts that fail

*Claude, in the same session. The space's acts are the user's, as the Data Scientist User, from `jup`'s
terminal as `app-dbt-dev`'s project role; Claude's reads as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account 1) and, for the proxy's log,
`awsds-infra-prod` (Production). Times are UTC.*

- **[user] 3.3**, as one chain Claude wrote: each of the step's `export`s, then `scripts/dev-cli.sh run
  --manifest manifest.yaml --targets dev --workflow app-dbt`, then a boto3 poll of the run's state before
  the next. The runs, each run's `OverrideParameters` carrying the switches as exported:
  `y0LYsay860ExnUB` at 05:25:34 (`LINEAGE_DOMAIN=dzd_canaryprobe0000`), `2n9VT4BUgGDzjEI` at 05:35:59
  (`LINEAGE_ENDPOINT=http://127.0.0.1:9`, `LINEAGE_ATTEMPTS=1`) and `W79iKwIMko7AROp` at 05:42:06
  (`https://datazone.us-west-2.api.aws:8443`, one attempt). The chain ended *"em repouso:
  dzd-d8yrvx1ko7im6o default default"*.
- **[Claude] The poll stopped the chain after the first run**: `boto3.client("mwaa-serverless")` failed
  `GetWorkflowRun` with `ProxyConnectionError`, *"Tunnel connection failed: 403 Forbidden"*, and the
  proxy's log reads five `CONNECT airflow-serverless.us-west-2.api.aws:443 403 … TCP_DENIED` from `jup`'s
  10.20.28.126 from 05:25:35 to 05:25:40, with that host in both of the image's `NO_PROXY` variables. A
  second attempt was refused the same way. The CLI's `run`, from the same terminal at 05:25:34, left no
  `airflow-serverless` line in that log. Measured on the laptop at 05:33: botocore decides the proxy
  against `airflow-serverless.us-west-2.amazonaws.com`, the host it composes from the service's endpoint
  prefix, and not against the `.api.aws` host the request goes to (`SUP-395`). With that host added to
  `NO_PROXY` and an explicit `endpoint_url`, the poll read `y0LYsay860ExnUB` `SUCCESS` at 05:35:55 and the
  chain went on.
- **[Claude] The runs**, each `SUCCESS` with `load` and `transform` `SUCCESS`, beside 2.3's and 2.5's. The
  emit phase runs from dbt's *"Done. PASS=2 …"* to the wrapper's *"Emitted … OpenLineage events"*; the log
  is the `transform` task's, counted in its messages' bytes:

  | Run | The post | `transform` | Emit phase | The log |
  |---|---|---|---|---|
  | 2.3's `SzzngX9q8O3hZ7k` | six events posted | 48 s | 2.6 s | 64 events, 17,653 bytes |
  | 2.5's `JCrmBgSmNqRrTXg` | six events posted | 54 s | 2.5 s | 64 events, 17,652 bytes |
  | `y0LYsay860ExnUB`, refused | `AccessDeniedException` | 67 s | 2.4 s | 352 events, 211,566 bytes |
  | `2n9VT4BUgGDzjEI`, rejected | `ConnectionRefusedError`, then `EndpointConnectionError` | 50 s | 2.6 s | 1,540 events, 466,887 bytes |
  | `W79iKwIMko7AROp`, unanswered | `ConnectTimeoutError` | 426 s | 362.4 s | 1,420 events, 441,139 bytes |

- **[Claude] The wrapper's lines are the same in all three**: each of the six events' failures is printed
  twice, in the wrapper's two log formats, as *"OpenLineage client failed to emit event …"* with its
  traceback and a `RuntimeError: Failed to send lineage event to DataZone Domain …` line of 2,134 to 9,155
  bytes that carries the event, the compiled SQL included; then *"Emitted 0 OpenLineage events"*,
  *"Underlying dbt execution returned 0"*, *"run-dbt.sh: peak memory … kB, exit code 0"* and *"Command
  exited with return code 0"*. The refusal is IAM's: *"…
  assumed-role/datazone_usr_role_dnl3l158mbhrio_55hp9teamegf4g/AmazonMWAAServerless is not authorized to
  perform: datazone:PostLineageEvent on resource: arn:aws:datazone:us-west-2:<Sandbox>:domain/* because no
  identity-based policy allows the datazone:PostLineageEvent action"*, the resource in the caller's
  account, where the step expected the service's error for a domain it does not hold. The closed port
  reads *"Could not connect to the endpoint URL:
  "http://127.0.0.1:9/v2/domains/dzd-d8yrvx1ko7im6o/lineage/events""*; the unanswered port *"Connect
  timeout on endpoint URL:
  "https://datazone.us-west-2.api.aws:8443/v2/domains/dzd-d8yrvx1ko7im6o/lineage/events""*, the first at
  05:48:01, 62 seconds after *"Done."*, botocore's 60-second connect timeout once per event.
- **[Claude] ix**: a refused, a rejected and an unanswered post each leave the task `SUCCESS`, the
  script's exit code 0 and *"Emitted 0 OpenLineage events"*, as in 0.16. The refused and the rejected add
  nothing to the 2.5 seconds the posts take; the unanswered adds six minutes, 60 seconds for each of the six
  events at one attempt, as the step computed. Each multiplies the log by 12 to 26. Nothing outside the
  task's log reports a failed post: decision 5's input, which goes back to the user.

## 2026-11-21 — Sitting A: 3.4, another project's event on `notional_by_desk`

*Claude, in the same session. The space's acts are the user's, as the Data Scientist User, from the
terminal of a space of `test-experimentation` (`4gqfau9xuo6e4w`) as that project's role; Claude's reads
and the delete as the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1`
(Sandbox Account 1) and `awsds-infra-data` (Data Governance); the portal in the user's Chrome session
through Claude in Chrome. Times are UTC.*

- **[user] 3.4**, aws-cli 2.37.0 in the space: the step's event, its output the pair under which 2.4 read
  the model's node, `arn:aws:glue:us-west-2:<Sandbox>:table` and `app_dbt/notional_by_desk`, the job
  `stage-20-foreign` `foreign-writer`, the run `791b1044-…`; the post answered the id `bbmyjshqm00c5s`.
  Then `get-lineage-node` on `app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run`
  answered `6eael36d03lyfk` with the forms `QueryForm`, `JobForm` and `AdditionalPropertiesLineageForm`.
- **[Claude] The domain accepted the event**: `processingStatus` `SUCCESS`, `eventTime` 05:42:00,
  `createdAt` 05:42:10. Data Governance's trail holds the `PostLineageEvent` at 05:42:10 from
  10.20.104.205 through `vpce-03abb012f13500645` with no error, and a `CreateLineageNode` by
  `datazone.amazonaws.com` at 05:42:17. The table's node `6w7hp2vvi8kscw` took a version at 05:42:00, its
  upstream the run `bdgva1yjktix3k` (`amazon.datazone.JobRunLineageNodeType`,
  `stage-20-foreign.foreign-writer/791b1044-…`, `JobForm` and `JobRunForm`), its downstream the asset's
  node `6ljn21swt4l0y8`; the job's node is `bgib8sahkbeets` (`stage-20-foreign.foreign-writer`,
  `JobForm`). Both new nodes name as creator the Data Scientist User's id, where the workflow's events name
  the project role: a post from a space's terminal carries the person.
- **[Claude] The portal**, read from 05:44 to 05:46, signed in as the Data Scientist User; reads and view
  toggles only. `app-dbt-dev`'s `notional_by_desk`, *Lineage*: `foreign-writer` as a *Job Run*,
  `COMPLETE`, 02:42 UTC-03:00, beside the dbt model's run of 02:03 (2.5's), both drawn into the table; the
  table's node labelled `app_dbt/notional_by_desk`, the foreign event's name, where vii read
  `awsdatacatalog.app_dbt.notional_by_desk`; the foreign run's panel, *Source Identifier*
  `stage-20-foreign.foreign-writer` and *Created By* the Data Scientist User. The portal draws the latest
  run of each job upstream of a node, and names a node by its latest version.
- **[Claude] xi: yes to both, with a limit.** The domain accepts from one project's role an event about
  another project's table, adds it as a version of that table's node and draws the foreign job on the
  table's tab; a role outside the project reads the project's job node, the compiled SQL in its
  `QueryForm` included (`TM-29`'s shape, on lineage). The Data Scientist User is `PROJECT_OWNER` of both
  projects, so the reading does not separate the project from the person.
- **[user] The delete**, in chat: *"Autorizo o delete"*, answering Claude's question that named
  `delete-lineage-event` of `bbmyjshqm00c5s`, as Sandbox and then as Data Governance. The other sessions
  on this machine told at 05:50.
- **[Claude⚡] Both refused**, from the laptop, aws-cli 2.37.12. As Sandbox at 05:50:51: *"… is not
  authorized to perform: datazone:DeleteLineageEvent on resource: …:domain/dzd-d8yrvx1ko7im6o because no
  resource-based policy allows the datazone:DeleteLineageEvent action"*. As Data Governance, the domain's
  account, at 05:50:54: *"User is not permitted to perform operation: DeleteLineageEvent"*, DataZone's own
  wording, IAM having let the call through. A member account reaches the domain through the RAM share's
  managed permission `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`: versions 13 and 14, the
  second the share's since 05:45:59 (pull request #347), each carry `PostLineageEvent` and the lineage
  reads and neither carries `DeleteLineageEvent`. The root domain unit's one owner is an Identity Center
  group (`7ee243ab-…`), and no IAM principal.
- **[user] The event stays**: *"Deixe e registre"*. The step's fallback, the posting space's role, is a
  Sandbox principal under the same resource policy, and was not run.
- **[Claude] xv is not answered**: no identity this session holds may call `DeleteLineageEvent`, so what
  it removes stays unmeasured. AWS's lineage authorization and API pages name neither who may call it nor
  what it removes (read 2026-11-21). `bbmyjshqm00c5s` stays in the graph, the portal drawing
  `foreign-writer` into `notional_by_desk`; 7.1 and Rollback's step 6, which delete the events by what xv
  reads, wait on an identity the root domain unit's owners would have to admit.

## 2026-11-21 — Sitting A: 2.6, the same project by hand

*Claude, in the same session. The space's acts are the user's, as the Data Scientist User, from `jup`'s
terminal as `app-dbt-dev`'s project role; Claude's reads as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account 1) and `awsds-infra-data` (Data
Governance). Times are UTC.*

- **[user] 2.6**, the step's commands from `~/app-dbt`, the variables read first (*"dzd-d8yrvx1ko7im6o |
  as-built | conta definida"*): the archive unpacked to `/tmp/app-dbt-hand`, then `run-dbt.sh …
  --namespace app-dbt-by-hand` with `-- debug` and with `-- run`. Both print *"dbt from /tmp/tmp.…/bin,
  this script not executable"* and *"/opt/conda/bin/python3 3.12.14
  Linux-6.12.115-140.210.amzn2023.x86_64-x86_64-with-glibc2.39"*, where the worker reads 3.12.16 on Linux
  6.1.190 with glibc 2.34. `debug`: *"This dbt command produces no lineage; running it without OpenLineage
  events"*, *"Connection test: [OK connection ok]"*, *"All checks passed!"*, peak memory 159,304 kB, exit
  code 0. `run`: *"OK created sql table model app_dbt.notional_by_desk … [OK 3 in 13.98s]"*, *"Done. PASS=1
  …"*, four events posted at 06:18:13 (`ckenjo1twzcqds`, `61luuzkqhux72o`, `dnwj5sxhkowff4`,
  `6qldbu4jy3iz68`), *"Emitted 4 OpenLineage events"*, peak memory 194,416 kB, exit code 0. As 0.16 read.
- **[Claude] The statements and the table**: 2.5's swap, each statement `SUCCEEDED`: the create at
  06:17:58; the renames at 06:18:02 and 06:18:04, each an `UpdateTable` refused
  `UnsupportedOperationResponse` and then a `CreateTable` and a `DeleteTable`; the drop at 06:18:07; the
  model's second statement at 06:18:10. `notional_by_desk` created 06:18:05 and updated 06:18:11,
  `VersionId` 1, one version, its description kept, at
  `…/app_dbt/notional_by_desk/4e686f34-677c-45e5-8678-7d4c31a7c5f6`; `notional_by_desk__ha` and
  `notional_by_desk__bkp` read `EntityNotFoundException`; the project role's two grant rows unchanged. The
  asset `daefcycb3hhhn4` stays at revision 2, its `GlueTableForm` naming 2.5's location `378cf5f7-…`,
  until the source's next run.
- **[Claude] The space's session against the worker's**: in Sandbox's trail every call is the project
  role's session `SageMaker` from `jup`'s 10.20.28.126, user agent `Boto3/1.43.75 …
  os/linux#6.12.115…`: Athena's `StartQueryExecution` through `vpce-0150fe6c7648118a7`; the client's Glue
  calls through `vpce-015a9ee19ec1b45af`, `persist_docs`' `UpdateTable` at 06:18:11 among them; the four
  `PostLineageEvent` at 06:18:13 through `vpce-03abb012f13500645`; Athena's own Glue calls from
  `athena.amazonaws.com`. 2.5's worker called as the session `AmazonMWAAServerless` from 10.20.56.170.
  Data Governance's trail records the four posts as `AWSAccount`, with the same address and endpoint, so
  the domain's account does not tell the two apart; it adds two `CreateLineageNode` by
  `datazone.amazonaws.com` at 06:18:25. Two `GetDatabase` calls Glue made itself under the client's
  `GetDatabases`, at 06:17:57, read *"Insufficient Lake Formation permission(s): Required Describe on
  curated"* and *"… on raw"*.
- **[Claude] The graph keeps its dataset nodes and adds a job**: the four events' and the new nodes'
  creator is `28f1b390-…`, the Data Scientist User's profile (type `SSO`), where the workflow's events
  carry `8af0750c-…`, the profile of `datazone_usr_role_dnl3l158mbhrio_55hp9teamegf4g` (type `IAM`). The
  jobs `app-dbt-by-hand.awsdatacatalog.app_dbt.app_dbt.notional_by_desk` (`dm0hfd9w4k7ehc`, `QueryForm`,
  `JobForm`, `AdditionalPropertiesLineageForm`) and `app-dbt-by-hand.dbt-run-app_dbt` (`bhng3gchuguzyo`)
  were created at 06:18:25. `6w7hp2vvi8kscw` took a version at 06:18:11, named
  `awsdatacatalog.app_dbt.notional_by_desk` again, its upstream the run `axu3omqltim74g`
  (`…notional_by_desk/01a1fcc1-5bb4-…`) from `3s0gk0eg2o68pc`, which took a version at the same second, its
  downstream the asset's node `6ljn21swt4l0y8`.
- **[Claude] The development loop, read**: a person's run joins the workflow's graph as a job of its own
  between the same dataset nodes. The graph tells it by the job's namespace, which the person chooses
  (`app-dbt` when `--namespace` is left out), and by each version's creator, which DataZone sets: the
  person's profile from a space, the role's from the workflow. The job's name follows the dbt command,
  `run` against the workflow's `build`, not the person. A run by hand moves the table to a new location,
  and the asset follows at the source's next run.

## 2026-11-21 — Decision 5 looked at again after 3.3

*Claude, in the same session; the decision is the user's, in chat.*

- **[user] Decision 5 keeps (a)**: *"Manter (a)"*, answering Claude's question on 3.3's readings (ix).
  dbt's exit code decides the task, and a failed post stays a warning in the task's log. The stage file's
  decision 5 carries the date.

## 2026-11-21 — Sitting A: 4.5, a processing job without isolation

*Claude, in the same session. The tar, the deploy and the run are the user's, in `jup`'s terminal as
`app-dbt-dev`'s project role; Claude's reads as the infrastructure user with `InfrastructureAccess`, through
`awsds-infra-sandbox-1` (account Sandbox Account 1) and `awsds-infra-prod` (account Production). Times are
UTC.*

- **[user] The tar and the exports**: *"app-dbt-job.tar: OK"*, the tree extracted to `job/app-dbt`; 2.2's
  values, then `DEV_PROJECT_SG`, `DEV_PROJECT_KEY_ARN` and `JOB_IMAGE_URI`, the house image by digest in
  Production's registry (`sha256:658c05d1…`).
- **[user] The deploy**: seven files synced to `shared/app-dbt/`; `app_dbt_app_dbt_dev_app_dbt` and
  `app_dbt_app_dbt_dev_app_dbt_probe` updated, `app_dbt_app_dbt_dev_app_dbt_job` created `READY`. The
  CLI's S3 Access Grants plugin asked `GetDataAccess` for `shared/` and for each definition: eight refusals
  from 06:45:31 to 06:46:05, from the proxy host's address through Production's S3 gateway endpoint
  (`SUP-042`, `SUP-093`), as 2.2's deploy read six from 04:04:24. The copies ran on the role's own
  credentials.
- **[user] The run**: 2.2's nine `ListTagsForResource` refusals, then *"Successfully started workflow run:
  yNcXniA0X0rn8G1"*.
- **[Claude] The copies and the workflow**: under `shared/app-dbt/`, seven objects: `code/app-dbt.zip`
  26,129,645 bytes, `job/probe.py` 6,103, `workflows/app-dbt-job.yaml` 2,342, `workflows/app-dbt-probe.yaml`
  7,390 and `workflows/app-dbt.yaml` 3,794, with `glue/load.py` and `inbox/trades.csv` unchanged. Under
  `shared/operatorFiles/`, three copies, at 06:45:33, 06:45:46 and 06:45:58. The job's workflow `READY`,
  `manual_only`, created 06:46:06, in the project's two subnets and `sg-040ed6781b8c4449e`, under
  `CUSTOMER_MANAGED_KEY`.
- **[Claude] The create**: `CreateProcessingJob` at 06:47:20 as the project role's session
  `AmazonMWAAServerless`, `Boto3/1.43.1`. It came from the worker's interface `eni-09bca8eafcf24448b` at
  10.20.102.138 (created 06:46:42 by `AWSServiceRoleForAmazonMWAAServerless`), through
  `vpce-042889be2db64615e` (`sagemaker.api`). Its `networkConfig`: `enableNetworkIsolation` `false`,
  `enableInterContainerTrafficEncryption` `true`, the project's two subnets and its group; `ml.t3.medium`,
  10 GB under the project's key.
  - SageMaker's checks around the create, as the project role: five `CreateNetworkInterface` answered
    `DryRunOperation` at 06:47:20 and 06:47:21 (sessions `AnalyticsValidation`, `SageMaker`, and
    `AmazonMWAAServerless` invoked by `sagemaker.amazonaws.com`), and two `BatchGetImage` from Amazon
    public addresses.
  - A `kms:CreateGrant` on the project's key at 06:47:22, as the session `SageMaker` from 32.184.5.219,
    refused *"because no identity-based policy allows the kms:CreateGrant action"*. The same grant invoked
    by `sagemaker.amazonaws.com` answered in the same second, and so did the volume's grant by
    `ec2-frontend-api.amazonaws.com` at 06:47:26. The job ran past the refusal.
- **[Claude] The job's interfaces**, created by SageMaker as the project role's session `SageMaker` from
  34.214.211.121, both in `subnet-09d3399d6b0fec93a`: `eni-0d5e959e28a522ec7` at 10.20.127.40 (06:47:53)
  and `eni-085f0964023533252` at 10.20.72.88 (06:47:55), described
  `pipeline-<Sandbox>-215bb7e6615b3de8c510cdf43d4c8a59-1` and `-2`. Every call of the container came from
  the second.
- **[Claude] The image's pull**: `GetAuthorizationToken` at 06:48:06 from 52.39.237.48, an Amazon public
  address, `aws-sdk-go`. Then `BatchGetImage` and 42 `GetDownloadUrlForLayer` invoked by
  `ecr.amazonaws.com`, to 06:49:02, as the project role's session `SageMaker`, and one `BatchGetImage` from
  52.39.237.48 refused `InvalidParameterException` on `repositoryName`. No call of the pull came through a
  Sandbox endpoint or from the job's interfaces.
- **[Claude] The job**: `Completed`, no `FailureReason`; created 06:47:20, `ProcessingStartTime` 06:48:06,
  `ProcessingEndTime` 06:55:11, the container's lines at 06:54:52 and 06:54:53. The run `SUCCESS` from
  06:46:36 to 06:57:24, 647 seconds; `job_1`, `SageMakerProcessingOperator`, `SUCCESS` in 612. The polls
  read the job `Completed` at 06:57:27, and the run `SUCCESS` only at 06:59:00.
- **[Claude] The job's log**, `/aws/sagemaker/ProcessingJobs`, one line per reading:
  - Python 3.12.14 as user 1000;
  - the image's proxy `http://proxy.awsds.internal:3128` and its file, *"no_proxy entries: 73; no_proxy
    sha256 : 61f1e1646df12c14"*;
  - `boto3 1.43.75`, and the caller, the project role's session `SageMaker`;
  - `SELECT 1` `SUCCEEDED` through the project's workgroup, its output under `dev/sys/athena/`, rows
    `[['_col0'], ['1']]`;
  - `app_dbt` at `…/dev/data/catalogs/`;
  - `ListLineageEvents`: 10 events, each `SUCCESS`;
  - *"on the plane: https://pypi.org/ HTTP 200"* and *"on no plane: http://example.com/ HTTP 403
    Forbidden"*.
- **[Claude] The job's calls**, in Sandbox's event history, each from 10.20.72.88 as the project role's
  session `SageMaker`, `Boto3/1.43.75`, each answered:
  - `GetCallerIdentity` at 06:54:51 through `vpce-01faaff304e0184b0` (`sts`);
  - `StartQueryExecution`, two `GetQueryExecution` and `GetQueryResults` from 06:54:51 to 06:54:52 through
    `vpce-0150fe6c7648118a7` (`athena`);
  - `GetDatabase` at 06:54:52 through `vpce-015a9ee19ec1b45af` (`glue`);
  - `ListLineageEvents` at 06:54:52 through `vpce-03abb012f13500645` (`datazone`).

  The job's own log calls came from 52.39.237.48 at 06:54:58: `CreateLogGroup` answered
  `ResourceAlreadyExistsException`, then `CreateLogStream`.
- **[Claude] The proxy**, `/awsds/prod/proxy`, both lines stamped 06:54:53: `10.20.72.88 CONNECT
  pypi.org:443 200 30324 1783 TCP_TUNNEL` and `10.20.72.88 GET http://example.com/ 403 3391 133
  TCP_DENIED`.
- **[Claude] 4.5 passes**: the job was created, ended `Completed` and had each call answered, with the
  proxy at 200 for `pypi.org` and 403 for `example.com`, as `sandbox/probes/` expects them.
  - xii: yes. A project role in Sandbox creates a job without isolation; 4.4's battery of 2026-11-17 read
    the processing job `ALLOWED` in Production and the training job `DENY-SCP`.
  - xiii's Sandbox half: yes. STS, Athena, Glue and the domain answered through their interface
    endpoints, the proxy passed its allow-list and no name off it. The target's half stays the step's
    reading of 2026-11-11.
  - Rows 1 to 16 of sitting A are done. Row 17 joins 6d's lowering at the day's end (`promotion.md`
    §N.9.3 step 10).

## 2026-11-21 — Sitting A: 2.7, the downs

*Claude, in the same session. The portal's acts are the user's as the Data Scientist User, the downs the
user's as the infrastructure user with `InfrastructureAccess`; Claude's reads through
`awsds-infra-sandbox-1` (Sandbox Account 1) and `make status`. Times are UTC.*

- **[user] The space**: `jup`'s app deleted at 07:09:24 and the space itself at 07:46:59, through the
  portal.
- **[user] The downs**: `make down ENV=sandbox`, its interface endpoints deleted from 07:50:30 to 07:53:47,
  and `make hub-down`, the hosts stopped at 07:56:33 and 07:56:35.
- **[Claude] `make status` and §R's readings**, from 08:00: 0.0000 USD/h, no interface endpoint, no NAT
  gateway and no Studio app in Sandbox (6d's log carries the readings).
- **[Claude] `$HOME/tmp/stage20`** moved to the Trash as `stage20-2026-11-21`, 102 MB: 2.0's `source.tar`
  and `app-dbt.tar`, the job's tar in `job/`, the extracted tree and the nine event files of 2.3, whose
  readings the 2.3 entry holds. 2.0's commands rebuild the folder from `rm -rf`.
- **[Claude] Sitting A is done**, rows 1 to 17. Left: pass 5 after Stage 19's 4.12, on §N.10's day 1; 7.1
  and Rollback's step 6, which wait on an identity that may call `DeleteLineageEvent` (xv); pass 8's
  remainder in R1 or R2, before 2026-12-18.

## 2026-11-21 — 8.6: the tree to be tagged, and the bundle rehearsed before the curation

*Claude, in a session the orchestrating session started for 8.6, with the hub and Sandbox up for N.9's day
2, which this work does not use. Reads as the infrastructure user with `InfrastructureAccess`, through
`awsds-infra-sandbox-1` (Sandbox Account 1) and `awsds-infra-data` (Data Governance); the portal read in
Claude's own tab group of the user's Chrome, signed in as the Data Scientist User, reads only. Account ids
in pasted output became `<Sandbox Account 1>`. Times are UTC.*

- **[Claude] The portal's identity**, about 20:20: the account menu reads *Data Scientist User*; the project's
  *Members* page lists that user as *Owner* of `app-dbt-dev`, and `awsds-deploy-sandbox-test`, the
  infrastructure user's `AWSReservedSSO_InfrastructureAccess_…` and the project role as *Contributor*, as
  `list-project-memberships` reads them.
- **[Claude] The assets before the curation**: `trades` (`bra0895x5fjzww`) and `notional_by_desk`
  (`daefcycb3hhhn4`), each at revision 2 by `SYSTEM`, no description, `AssetCommonDetailsForm` holding the
  table's ARN alone, no `classification`; the project owns no data product and no glossary. The form type
  `classification` is at revision 2, `ENABLED`, owned by `eighth-experimentation`. The texts were proposed to
  the user in chat, each README under 1,500 of the 4,096 characters.
- **[Claude] The tree**, on pull request #349: `git restore --source=c11a9829` over `examples/app-dbt/`, whose
  tree `ec837c34` is `103b4acc`'s, the one 2.0 built the archive and the tar from; `399f3365`'s six files for
  4.5 are off it. Then the lint pin moved from `4613ddc` to `awsds-workflows` `4401f91` in `.gitlab-ci.yml`,
  the README and the simulation; between the two commits only `src/awsds_workflows/lint.py` changed in the
  package. `uv sync --locked`, ruff check and format clean, `pytest` *"86 passed"*; the lint with the
  pipeline's instance types *"ok: 4 arquivo(s)"* at `4613ddc` and at `4401f91`. #321's
  `deploy-application.py --self-check`, run in a copy of its branch holding this tree: *"ok    staging: 9
  variable(s); app_dbt_deploy_staging_app_dbt, app_dbt_deploy_staging_app_dbt_probe"*, *"ok    prod: 9
  variable(s); app_dbt_deploy_production_app_dbt"*, every other application `ok`, *"OK"*.
- **[Claude] `build-task-code`'s script**, by `bash` at 20:26 in the tag's tree, extracted from `git archive`
  of the branch's head (36 files): exit 0, *"code/app-dbt.zip: 5102 entries, 26129234 bytes, 82844337
  unzipped, modes {'run-dbt.sh': '0o100755', 'app_dbt/bin/dbt': '0o100755'}"*. Against 2.0's archive, read in
  the Trash where 2.7 left it: the same 5,102 members, and only four differ, all in
  `app_dbt-0.1.0.dist-info/`: `METADATA`, which embeds the README (`readme = "README.md"`), `RECORD`,
  `direct_url.json`, which names the build's temporary folder, and `uv_cache.json`. The archive's digest
  thus moves with the README and the build folder, never with the code alone.
- **[Claude] The pipeline's `pip-audit`**, by the gates' commands at 20:29: 78 pins exported, 78 audited, *"No
  known vulnerabilities found"*. The gate reads a feed, so it runs again on the day of the tag (Lesson 77).
- **[Claude] The bundle before the curation**, `bundle`'s script by `bash` in the same tree, as
  `awsds-infra-sandbox-1` with `DOMAIN_ID`, `DOMAIN_REGION` and `DEV_PROJECT_NAME` exported, from 20:27:34 to
  20:28:01: exit 0, `artifacts/app-dbt.zip` 25,501,926 bytes, six files (the catalog export, `code/app-dbt.zip`,
  `glue/load.py`, `samples/trades.csv` and the two workflows); no *"Pattern not found"* and no *"Failed to get
  project connections"*. The guard: *"assets: 2 (notional_by_desk, trades)"*, every other section 0, *"OK"*.
  Each asset carries `GlueTableForm` 13, `DataSourceReferenceForm` 5, `SubscriptionTermsForm` 2 and
  `AssetCommonDetailsForm` 8, no description, no README.
- **[Claude] Sandbox's trail** for that minute: 32 calls by the session from 20:27:35 to 20:28:00, each a read:
  `DescribeStacks` refused `ValidationException`, `ListDomains`, `ListProjects`, `GetProject`,
  `ListProjectMemberships`, two `GetUserProfile`, two `GetGroupProfile` answered (`SUP-360`), four
  `ListConnections`, nine `GetConnection`, `ListEnvironments`, four `Search`, two `SearchTypes`, two `GetAsset`
  and `GetCallerIdentity`. CloudTrail records `Search` and `SearchTypes` with `readOnly` false.
- **[Claude] Read against R1**: 5.0's subscription writes its resource link in `app_dbt`, and the project's
  source `3uof8bs4x693f4` (`cron(43 2 * * ? *)`) imports a link as an inventory asset (`SUP-197`), which the
  bundle exports and the guard fails. `promotion.md` §N.11.1 step 5 now has 5.0's request wait for step 7's
  `bundle` job.

## 2026-11-21 — 8.6: the curation saved through the portal, and the bundle rehearsed after it

*Claude, in the same session. The portal in Claude's own tab group of the user's Chrome, signed in as the
Data Scientist User, the group closed after the saves. Reads as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account 1) and `awsds-infra-data` (Data
Governance, the domain's account). Times are UTC.*

- **[Claude] The word**: the user's *"Autorizo a curadoria"* in this session's chat, answering the
  question that named saving the two assets' curation with the texts shown in full. The orchestrating
  session had relayed the same authorization from its own chat; this session did not act on the relay.
  The four other sessions on the laptop were told before the first save.
- **[Claude] The identity**, read again before the first save: the account menu reads *Data Scientist
  User*, project `dnl3l158mbhrio`.
- **[Claude] The saves**, each one revision by the Data Scientist User, read back by `get-asset` after
  each:

  | Asset | Revision | At | The portal's act |
  |---|---|---|---|
  | `trades` | 3 | 20:38:26 | the description, by the edit icon beside *No description* and its check mark: *"Description updated successfully"* |
  | `trades` | 4 | 20:39:56 | the README, by *Create Readme* and the editor's *Save* |
  | `trades` | 5 | 20:40:47 | the form, by *Add Form*, *Classification*, *Next*, `internal` and *Save*: *"Form added successfully"* |
  | `notional_by_desk` | 3 | 20:41:47 | the description, the same way |
  | `notional_by_desk` | 4 | 20:42:29 | the README |
  | `notional_by_desk` | 5 | 20:43:12 | the form, `internal` |

  Each description reads as shown; `AssetCommonDetailsForm` holds `readMe` beside `sourceIdentifier`,
  equal to the text shown (1,282 and 1,484 characters, the file's final newline dropped); `classification`
  is at type revision 2 holding `{"classification":"internal"}`. Revisions 1 and 2 stay `SYSTEM`'s. Neither
  asset was published: *Generate suggestions* and *Publish* were never clicked.
- **[Claude] What the portal showed beyond `catalog.md`**: the README is a Monaco code editor with a
  *Side By Side Preview* switch. Each text went in through the editor's own API (`executeEdits` over the
  whole model) rather than typed, read back equal and rendered by the preview before *Save*. *Add Form*
  opens a panel in two steps: *Select a form*, which offered `Classification` alone, with its description
  and *1 fields*, and *Enter field values*, one optional text field. `get-form-type` reads its model as one
  `String` with no list of values, its description naming `public`, `internal`, `restricted` or
  `personal`, so the field takes any text.
- **[Claude] Data Governance's trail** from 20:37:30 to 20:43:40: six `CreateAssetRevision`, at the six
  times above on `bra0895x5fjzww` and `daefcycb3hhhn4`, by the role `awsds-data-studio-domain-execution`
  in the user's session; every other call with `readOnly` false a `Search` or a `SearchTypes`, and no
  `CreateListingChangeSet`. Sandbox's trail holds none of the six.
- **[Claude] The bundle after the curation**, the script and tree of 20:27, from 20:44:32 to 20:44:57:
  exit 0, `artifacts/app-dbt.zip` 25,503,094 bytes,
  `BUNDLE_SHA256=4ca00173830a4c390c507a8e32e744a4b9afad5d2b16df805a8c2fce5bba41f3`, the same six files. The
  guard: *"formTypes: 0"*, *"assets: 2 (notional_by_desk, trades)"*, every other section 0, *"OK"*. Each
  asset carries its description, the `readMe` equal to the text saved and `classification` at revision 2
  with `{"classification":"internal"}`, beside the four forms of 20:27; the form type travels in no
  `formTypes`, its owner being `eighth-experimentation` (Stage 19 item 22).
- **[Claude] Sandbox's trail** for that minute, read at 20:47: 32 calls by the session from 20:44:33 to
  20:44:57, the set of 20:27: `DescribeStacks` refused `ValidationException`, `ListDomains`,
  `ListProjects`, `GetProject`, `ListProjectMemberships`, two `GetUserProfile`, two `GetGroupProfile`
  answered, four `ListConnections`, nine `GetConnection`, `ListEnvironments`, four `Search`, two
  `SearchTypes`, two `GetAsset` and `GetCallerIdentity`, each a read. A read at 20:45:39 had found the
  window empty.

## 2026-11-22 — 5.0's request pending, and #321 synced with `main` after release G

*Claude, on the user's request of the session to run every step that needs nothing up: the request made as
the Data Scientist User, `app-dbt-dev`'s owner, in the user's own Chrome session, which the user offered
for SMUS acts; AWS read as the infrastructure user with `InfrastructureAccess` in `Data Governance Account`
(`awsds-infra-data`). Times UTC.*

- **[Claude] 5.0's request**, from `app-dbt-dev`'s page of `trades-notional` (`dr8t27tte8ezdc`) at 08:28:16Z:
  `CreateSubscriptionRequest` as `awsds-data-studio-domain-execution` for `dnl3l158mbhrio`; the request
  `6oy7kvmszacaa8` reads `PENDING`. Its approval follows Stage 19's xxvi portal half, as 4.12's
  (`6gtjmvdzma9n9s`, 08:27:36Z) does, and 5.1's model, archive and tar follow the link.
- **[Claude] #321's branch** took `origin/main` at `77fc285a` by merge in a scratch worktree, 29 commits of
  `main` since `00113780`, no conflict: `./scripts/deploy-application.py --self-check` printed every stage of
  `app-etl`, `app-ml`, `app-genai` and `app-dbt` `ok`, `make check` OK, and pre-commit's hooks passed on the
  merge commit `e6538fb0`, pushed to `claude/plano-estagios-execucao-5f64d8-n6-item10`
  (`00113780..e6538fb0`). The pull request reads `MERGEABLE`; its merge is the user's, before R2.

## 2026-11-22 — #321 merged after R1

*The user merged the pull request on GitHub and told the session that started this one; Claude read the
object and the tree with nothing up, no AWS call. Times UTC.*

- **[user] The merge**: pull request #321, 8.1's script change with `app-ml`'s and `app-genai`'s.
- **[Claude] The object**, read with `gh pr view 321` at 13:30: `MERGED` at 13:28:54Z, the merge commit
  `81d70158` on `main`, a single commit over `ba6455cf`. `scripts/`, `examples/`, `aws/` and
  `.pre-commit-config.yaml` at `81d70158` equal the branch's head `e6538fb0`, and `ba6455cf` changed none of
  them since the branch's sync at `77fc285a`.
- **[Claude] The tree**: `./scripts/deploy-application.py --self-check` on a tree whose scripts and examples
  equal `81d70158`, at 13:31, exit 0: every stage of `app-etl`, `app-ml`, `app-genai` and `app-dbt` `ok`,
  `app-dbt`'s staging and prod at 9 variables, the samples *"14 log(s) read as expected, and the composed
  name"*, and *"OK"*.
- **Left of 8.1**: the mirror's push at R2's opening, `git pull` and `git push gitlab main` with GitLab up
  (`promotion.md` §N.11.2 step 1), before `app-dbt`'s first push.

## 2026-11-22 — 5.0's approval, and the link in `app_dbt`

*The approval was clicked by the side session that guides the Governance Manager's acts, in the Governance
Manager's Chrome profile the user opened for it, on the user's word in that session's chat (Stage 19's log,
the same day). This session read the fulfilment as the infrastructure user with `InfrastructureAccess` in
Data Governance (`awsds-infra-data`), Production (`awsds-infra-prod`) and Sandbox Account 1
(`awsds-infra-sandbox-1`), nothing up. Times UTC.*

- **[user] The word**: *"Autorizo aprovar ambos"*, Stage 19 4.12's request and this one.
- **[Claude, side session] The approval**: `6oy7kvmszacaa8`, comment *"Approved for Stage 20 5.0 by the
  Governance Manager (subscription-approver)."*, saved at 14:05:14; the portal's toast *"Subscription request
  has successfully been approved."*, and no request left pending.
- **[Claude] The request and its subscription**: `ACCEPTED`, `reviewerId` the Governance Manager's profile
  `e8a1f320-…`, updated 14:05:14.630; `AcceptSubscriptionRequest` at 14:05:14 in Data Governance's trail as
  the domain execution role in the Governance Manager's session. Subscription `6n3yg1rsytsemo` `APPROVED`;
  grant `5c4l81od6jm3o0` created 14:05:16.530 and `COMPLETED` at 14:05:21.061, 4.5 s, target
  `algy8t6358fits` (environment `au9oegx70xvyts`), its entity the asset listing `5hpftif3nnoj2o`, the asset
  `da1fycta6l71n4` at revision 6 `GRANTED`.
- **[Claude] Production**: one `BatchGrantPermissions` at 14:05:19 by `deploy-production`'s project role,
  `SELECT` on `app_etl.trades_notional` to Sandbox's `IAMPrincipals` under
  `context.datazone.projectId=="dnl3l158mbhrio"`, `CROSS_ACCOUNT_VERSION` `5`, no grant option, listed at
  14:05:19.048. No RAM or Glue policy call: 4.12's share `LakeFormation-V5-2Y5MBO5ADP` and its three
  per-resource policies of 14:04:46 serve it (`SUP-195`).
- **[Claude] The link in `app_dbt`**: `glue:CreateTable` at 14:05:20 by `app-dbt-dev`'s project role in an
  `AWSDataZone-Subscriptions` session: `trades_notional`, to Production's `app_etl.trades_notional`, beside
  `notional_by_desk` and `trades`. `BatchGrantPermissions` at 14:05:20, `DESCRIBE` on it to `IAMPrincipals`
  and to `arn:aws:identitystore:::user/*` under the project's condition, no failure; `list-permissions`
  shows the first and the project role's `ALL`, `DESCRIBE`, `DROP` with grant option (`SUP-109`). This is
  5.1's first reading: the link is `trades_notional`, its target `app_etl.trades_notional` in Production.
- **[Claude] The asset to come**: the project's source over `app_dbt`, `3uof8bs4x693f4` on
  `cron(43 2 * * ? *)`, last run 02:54:41 `SUCCESS` with two assets, imports the link as an inventory asset
  at its next run, 2026-11-23 at 02:43 (`SUP-197`); 8.6 deletes it before R2's tag.
- **Left of 5.0**: the revocation, with 4.12's, after `promotion.md` §N.10's day 2. 5.1's model, its archive
  and its tar follow with nothing up.

## 2026-11-22 — 5.1: the link read, the model on a branch no tag carries, the archive and the tar

*Claude, in a session started by the orchestrating session, on the laptop with nothing up: reads as the
infrastructure user, permission set `InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account
1) and `awsds-infra-prod` (Production), the offline tests, the lint and two builds. No write to AWS.
Production's account id, which the link's `TargetTable` names, was compared by script and is not copied.
Times UTC.*

- **[Claude] The link and its target**, 5.1's command on `app_dbt` at 14:54:57, exit 0:

  ```text
  notional_by_desk	None	None	False
  trades	None	None	False
  trades_notional	app_etl	trades_notional	False
  ```

  `get-table` on the link: its catalog Sandbox's, `TargetTable` Production's catalog, `app_etl`,
  `trades_notional`, `us-west-2`; `TableType` present and empty, `CreatedBy` empty, no `StorageDescriptor`,
  `Parameters` or `CreateTime`. DataZone's `CreateTable` at 14:05:20, by the project role's
  `AWSDataZone-Subscriptions` session in Sandbox's trail, named no table type: its `tableInput` holds `name`,
  `retention` 0, `targetTable` and `isRowFilteringEnabled` `false`, as `eighth-experimentation`'s at 14:05:02
  in `glue_db_blerpkhn9nj7o0`. The target, as `awsds-infra-prod`: `EXTERNAL_TABLE`, `table_type` `ICEBERG`,
  updated at 04:52:00 under `deploy-production`'s `dev/data/catalogs/trades_notional`, with the columns
  `trade_date` `date`, `desk` `string`, `instrument` `string`, `quantity` `int`, `price` `double` and
  `notional` `double`.
- **[Claude] The adapter and the link**, read in the lock's `dbt-athena` 1.11.1 after `uv sync --locked`:
  `list_relations_without_caching`, the cache `dbt build` fills from `glue:GetTables`, skips only a table
  with no `TableType` key, so the link enters the cache as a table of `app_dbt`; `get_table_type` raises
  *"Table type cannot be None for table …"* on an empty type; in a build of this project its callers read
  a model's own relation (the table materialization's old relation, `athena__drop_relation`, the location
  and column reads), while `dbt docs generate`'s catalog reads every table of a schema. `run-dbt.sh` runs
  `build`, so the link beside the models takes no part in a run; `docs generate` over `app_dbt` fails while
  it stands (`SUP-453`).
- **[Claude] The source and the model**, commit `2de42b7a` on the branch
  `claude/stage-20-5.1-notional-by-desk-prod`, cut from `main` at `6c30f9be` (pull request #375's merge),
  pushed, and never merged:
  - `sources.yml`: `trades_notional`, a second table of the source `app_dbt`, its six columns described;
  - `notional_by_desk_prod.sql`: `round(sum(notional), 2)` by `desk` from it, `materialized='table'`,
    `table_type='iceberg'`, `native_drop=true`, as `notional_by_desk`; in `schema.yml` its description and a
    `not_null` test on `desk`;
  - `tests/test_dbt_project.py` holding both models, both sources and both tests; `dbt_project.yml`'s
    comment, and the README's opening line, `transform` row and lineage paragraph;
  - from `examples/app-dbt/`: `ruff check` *"All checks passed!"* and `ruff format --check` clean after one
    reformat; `uv run pytest` *"88 passed"*; `awsds-workflows lint .` at `4401f91` with the pipeline's seven
    instance types *"ok: 4 arquivo(s)"*, exit 0; pre-commit's hooks passed on the commit. The simulation
    did not run: 1.3 runs it at a change of the lock or of `run-dbt.sh`, and neither changed.
- **[Claude] The archive and the tar**, by 2.0's commands from `2de42b7a` with the README's `TOOL`,
  `awsds-workflows` at `4401f91`, which the pipeline's `build-task-code` also pins; `$HOME/tmp/stage20` was
  absent, so nothing was removed:
  - `git archive` of `examples/app-dbt` at 15:01:34 (tree `46914522`): `source.tar`, 409,600 bytes, 52
    members of which 37 files;
  - `package-task` from 15:01:43 to 15:01:47, exit 0: *"code/app-dbt.zip: 26130142 bytes, 82846577
    descompactados, para o CPython 3.12 em x86_64-manylinux_2_28"*; 1.4's check
    `5103 82846577 ['0o100755', '0o100755']`; ten `.so` modules, no `boto3`, `botocore` or `yaml` at the
    root, no bytecode, `testzip()` clean. SHA256
    `3ee04adeaf600a736223b96f395e4c082f10c3bbb361c567e0aa1d99dd9914f3`;
  - against an archive built the same way from `main` at `6c30f9be` in a scratch folder, 26,129,271 bytes
    and 82,844,381 unzipped: one name more, `app_dbt/project/models/notional_by_desk_prod.sql`, and seven
    entries apart, `dbt_project.yml`, `schema.yml` and `sources.yml`, and `METADATA`, `RECORD`,
    `direct_url.json` and `uv_cache.json` in `app_dbt-0.1.0.dist-info/`; every dependency the same;
  - the tar at 15:02:10, 2.0's `COPYFILE_DISABLE=1 tar --no-xattrs --no-acls --no-mac-metadata` from
    `examples/`, exit 0: `app-dbt.tar`, 26,535,936 bytes, `52 38 []`; no pax header, the four scripts
    `0o755`, and the archive inside byte-identical to the one built. SHA256
    `b86bec1e9048e67cef1fe896ead3e470ec7e7adc8d65ff6d00c19dc434900ac0`.
- **Left**: 5.2 and 5.3 on `promotion.md` §N.10's day 1, `$HOME/tmp/stage20/app-dbt.tar` checked in the
  space against the digest above in place of 2.0's. The link's inventory asset, imported at the source's
  next run (2026-11-23, 02:43), and pass 5's table asset leave `app-dbt-dev` before R2's tag (8.6).

## 2026-11-22 — 5.2 and 5.3: the model over the subscription, its run, and one graph across the accounts

*Claude, in the session running `promotion.md` §N.10's day 1, started by the orchestrating session, on the
user's *"Sim, deploy e run"*. The space's acts ran in the user's Chrome session as the Data Scientist User,
through Claude in Chrome; the space's terminal runs as `app-dbt-dev`'s project role. Claude's reads as the
infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (Sandbox Account 1) and
`awsds-infra-prod` (Production). The account ids the trails and the nodes carry were compared by script and
are not copied. Times UTC.*

- **[Claude, in the user's session] The space**: `jup-app-dbt-dev` in `app-dbt-dev`'s blueprint domain
  `d-nt4ujzbdpeqm`, JupyterLab on `ml.t3.medium`, `awsds-sandbox-dev-env` version 12, idle timeout 120
  minutes, created 18:50:53 through the portal on the user's *"Autorizo tudo"* (6h's log of the same day).
- **[Claude, in the user's session] The tar**: `$HOME/tmp/stage20/app-dbt.tar` uploaded through the file
  browser in three parts of 8,789, 8,789 and 8,336 KB, since the upload tool takes no file over 10 MB, and
  joined at 19:51:37; 5.2's `sha256sum -c` passed and the tar extracted to `~/app-dbt`. `awsds-workflows`
  cloned at 19:51:55, its head `4401f91`, the pin; `space_values.py`'s values exported with
  `DEV_PROJECT_NAME=app-dbt-dev` and 2.2's lineage variables, `LINEAGE_NAMESPACE=app-dbt-dev` and
  `LINEAGE_NAMES=as-built`.
- **[Claude, in the user's session] The deploy** at 19:52:41, `scripts/dev-cli.sh deploy --manifest
  manifest.yaml --targets dev --skip-validation --no-events`, *"aws-smus-cicd-cli 1.0.9 on
  /opt/awsds/venv/bin/python"*: `app-dbt.zip`, `load.py` and `trades.csv` synced from 19:53:09, the two
  definitions rewritten with the values the CLI resolved at 19:53:46 and 19:54:01; *"No managed Tooling.GA/Tooling.Lightning blueprint found; will try
  the IAM connection fallback"*, then the Tooling configuration resolved to the project's two subnets and
  Sandbox's project key `a81b1ef3-…`; the operator code uploaded once per `workflow.create`; *"Workflow
  already existed, updated"* for `app_dbt_app_dbt_dev_app_dbt` and `app_dbt_app_dbt_dev_app_dbt_probe`, each
  `READY`; *"Deployment completed successfully!"*
- **[Claude, in the user's session] The run** at 19:54:58, `scripts/dev-cli.sh run --manifest manifest.yaml
  --targets dev --workflow app-dbt`: *"Successfully started workflow run: aDQs9e9XhwPTr1j"*, `run exit=0`,
  after the `ListTagsForResource` refusals on other projects' workflows 2.2 read.
- **[Claude] The copies and the workflow**: under `shared/app-dbt/`, `code/app-dbt.zip` 26,130,142 bytes,
  5.1's archive; `glue/load.py` 2,859; `inbox/trades.csv` 362; `workflows/app-dbt.yaml` 3,794 and
  `workflows/app-dbt-probe.yaml` 7,390. Under `shared/operatorFiles/`, two copies of 26,130,142 bytes at
  19:53:39 and 19:53:54. The workflow `READY`, `manual_only`, `CUSTOMER_MANAGED_KEY`, version `98492eda…`,
  modified 19:53:48.
- **[Claude] The run**: `aDQs9e9XhwPTr1j`, `ON_DEMAND`, `SUCCESS` from 19:55:19 to 19:59:20 (240 s). `load`,
  `GlueJobOperator`, `SUCCESS` in 110 s, the Glue job's run `SUCCEEDED` from 19:56:06 to 19:57:43 (78 s of
  execution, Glue 6.0, two `G.1X`); `transform`, `BashOperator`, `SUCCESS` in 58 s. The task log:
  *"Running with dbt=1.11.16"*, *"Registered adapter: athena=1.11.1"*, `notional_by_desk_prod` *"OK"*,
  *"Done. PASS=4 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=4"*, ten *"Successfully posted a LineageEvent"*,
  *"Emitted 10 OpenLineage events"*, *"Underlying dbt execution returned 0"*, *"run-dbt.sh: peak memory
  316152 kB, exit code 0"*.
- **[Claude] The table**: `notional_by_desk_prod` in `app_dbt`, `EXTERNAL_TABLE`, `table_type` `ICEBERG`,
  created 19:59:09 and updated 19:59:12 by `persist_docs`, its description *"The notional each desk traded
  in Production, summed over the trades of Production's app_etl.trades_notional, read through the
  project's subscription."* Its create, the statement `8aa2fda4-…`, `DDL`, 193 bytes scanned, from 19:59:07
  to 19:59:09 in `workgroup-dnl3l158mbhrio-55hp9teamegf4g`, Athena engine version 3.
- **[Claude] The read under the subscription's grant**: Production's trail holds, at 19:59:08,
  `GetDataAccess` on `arn:aws:glue:us-west-2:<Production>:table/app_etl/trades_notional`, `SELECT`, invoked
  by `glue.amazonaws.com` for `requesterService` `ATHENA`, `LakeFormationTrustedCallerInvocation` `true`,
  `userIdentity.type` `AWSAccount` from Sandbox, its principal `app-dbt-dev`'s project role in the session
  `AmazonMWAAServerless`, no error. With it, under the create's query id, a `BatchGetTable` at 19:59:07 and
  two `GetTable` at 19:59:08; and a `GetTable` at 19:58:53 for `requesterService` `UNKNOWN`. Sandbox's
  trail holds the link's `GetTable` at 19:59:08, invoked by `athena.amazonaws.com` and by
  `glue.amazonaws.com`; `CreateTable` and `UpdateTable` of `notional_by_desk_prod`; `StartQueryExecution`
  through `athena`'s endpoint and ten `PostLineageEvent` through `datazone`'s, from one private address in
  Sandbox's VPC. No refusal:
  two `GetTable` on `notional_by_desk_prod` answered `EntityNotFoundException` before its create.
- **[Claude] The events**, each `SUCCESS`, each created by `8af0750c-…`, saved to
  `$HOME/tmp/stage20/events-5.2/`: ten under the namespace `app-dbt-dev`, the parent `dbt-run-app_dbt` and
  each model's `build.run` and `build.test`. `notional_by_desk_prod`'s `build.run` reads
  `awsdatacatalog.app_dbt.trades_notional`, its `symlinks` facet naming `table/app_dbt/trades_notional`
  under Sandbox's catalog: the link's name in Sandbox's catalog, as 5.2 expected, where the listing's asset
  carries Production's table ARN.
- **[Claude] The graph**, by `get-lineage-node` and `list-lineage-node-history`, from the dbt run back:
  - the run `4j4wmws3dx28wg` (`…notional_by_desk_prod.build.run/01a204d7-6e57-763d-…`, 19:59:12), its job
    `d49qt21fttenps`, upstream `degibg9msuotn4` and downstream `aha80rzgv86gpc`,
    `arn:aws:glue:us-west-2:<Sandbox>:table/app_dbt/notional_by_desk_prod`, from which the test's run
    `64oxhbt2ru9q8g` hangs;
  - `degibg9msuotn4` is `arn:aws:glue:us-west-2:<Sandbox>:table/app_dbt/trades_notional`, the link. Its
    first version, created by `SYSTEM` at 14:05:21 with the grant's completion, carries
    `SubscriptionTargetLineageForm` under the name `create-datalake-database-env-app_dbt-…-default-target`,
    its upstream `chg3sfn08jn9xs`; its version at 19:59:12, dbt's, reads both edges;
  - `chg3sfn08jn9xs` is the listing's node, `amazon.datazone.listing/5hpftif3nnoj2o`, `ListingLineageForm`.
    Downstream, the two subscription targets: the link, and `cfn1fxmbtecdg0`,
    `eighth-experimentation-lakehouse-default-target` on `glue_db_blerpkhn9nj7o0.trades_notional` at
    14:05:12, 4.12's. Upstream, `b2eaaney9hlus0`, the asset `da1fycta6l71n4` (05:03:24);
  - upstream of the asset, `6i4aaj4f895ixc`, `arn:aws:glue:us-west-2:<Production>:table/app_etl/trades_notional`
    (04:52:00), from the Spark job run `ccbq2oraclodcg`
    (`default.app_etl_d7qcazihvr3s7k.atomic_replace_table_as_select.app_etl_trades_notional/01a20198-…`,
    R1's), itself from `6vxboppwovk0eo`, Production's `shared/app-etl/inbox`.
- **[Claude] xiv's first half: yes.** The graph joins Production's job, its table, the asset, the listing,
  the subscription target and the dbt job. The join is the subscription target's node, which the grant
  writes under the link's ARN, the name dbt's symlink resolves to (`SUP-391`). The transformer 5.2 held in
  reserve is not needed, and the run did not repeat.
- **[Claude, in the user's session] 5.3**, read at 20:09 as the Data Scientist User in
  `eighth-experimentation`, a subscriber of the listing through 4.12; reads and view toggles only. The
  listing `trades_notional`, *"Subscription approved"*, *Lineage* at graph depth 5: 11 nodes and 11 edges.
  Production's `shared/app-etl/inbox` (Amazon S3, 5 columns); the two Spark job runs
  `overwrite_by_expression…` and `atomic_replace_table_as_select…`, `COMPLETE`, 01:51 and 01:52 UTC-03:00;
  Production's Glue table, named `dzd-d8yrvx1ko7im6o/d7qcazihvr3s7k/dev/data/catalogs/trades_notional`;
  the asset, *Asset / Inventory*, 02:03; the listing, *Base* *Asset / Published*, 11:05;
  `eighth-experimentation-lakehouse-default-target`, drawn as a *Subscription target* with *Grant status:
  Granted*; the link, drawn as a Glue table named `awsdatacatalog.app_dbt.trades_notional`, 16:59; the dbt
  model's job with its latest run `COMPLETE`; `awsdatacatalog.app_dbt.notional_by_desk_prod`, 2 columns;
  the test's job with its latest run.
- **[Claude] xiv's second half, with a limit**: a member of a consuming project sees the producer's job
  runs, its table, the asset, the listing, every subscription target, and another consuming project's dbt
  job downstream. The portal names `app-dbt-dev`'s subscription target by its latest version, dbt's, so it
  draws a table and not a *Subscription target* (3.4's reading of a node's name). The Data Scientist User
  owns `app-dbt-dev` as well as `eighth-experimentation`, so the reading does not separate a member of
  another project from a member of the consuming one. The Governance Manager, a contributor of
  `eighth-experimentation` and no member of `app-dbt-dev`, had no browser connected to the extension.
- **Left of pass 5**: 5.0's revocation with 4.12's, after §N.10's day 2. `notional_by_desk_prod`'s asset,
  if the source over `app_dbt` imports it at 02:43 on 2026-11-23, leaves `app-dbt-dev` with the link's
  before R2's tag (8.6). `jup-app-dbt-dev` was left `InService` under its idle timeout, with `~/app-dbt`
  and the tar in its home; its JupyterLab tab was closed at 20:14.

## 2026-11-23 — R2's pre-flight for `app-dbt` with nothing up, and the read before its tag

*Claude's hand, a side session of the session coordinating 2026-11-22's batch, on the branch
`claude/prep-pending-sittings-369d94` from `main` at `b89b5a0f`. No AWS call: each job ran on the laptop
over `examples/app-dbt/`'s tree at `b89b5a0f`, copied outside the worktree, on CPython 3.12.13 and uv
0.12.13. Times UTC.*

- **[Claude] The `test` job**, at 02:14: `uv sync --locked`, `ruff check` and `ruff format --check`
  clean; `pytest` 86 passed in a copy that is a git repository, as the GitLab project is (83 passed and 3
  skipped in one that is not, the skips reading `run-dbt.sh`'s stored mode through git); the lint at the
  pin `4401f91` *"ok: 4 arquivo(s)"* with the pipeline's instance types.
- **[Claude] The `pip-audit` job**, at 02:17, its script read from this repository's
  `ci-gates/gates.gitlab-ci.yml` and run verbatim with `GATES_UV_PROJECTS=.`: *"78 of 78 pinned
  package(s) audited, 0 blocking vulnerability(ies)"*, *"No known vulnerabilities found"*, exit 0. A
  dated verdict: R2 runs it again on the day of the tag (Lesson 77).
- **[Claude] The `build-task-code` job**, at 02:23, its script as written: `code/app-dbt.zip` 5,102
  entries, 26,129,277 bytes, 82,844,382 unzipped, `run-dbt.sh` and `app_dbt/bin/dbt` at `0o100755`, exit
  0. 5.1's archive, one model larger, read 5,103 entries.
- **[Claude] `./scripts/deploy-application.py --self-check`**: `app-dbt`'s two stages `ok` at 9 variables,
  with 8.1's three workflow names.
- **[Claude] The read before the tag**: `promotion.md` §N.11.2 step 2 now has Claude read `app-dbt-dev`'s
  assets after 8.6's deletion and before `app-dbt`'s tag, `trades` and `notional_by_desk` expected alone
  (2.4's read), since `bundle`'s guard, `scripts/check-catalog-export.py`, fails on any asset
  `product.json` does not list, and a protected tag never moves (Lesson 86). 5.0's subscription
  `6n3yg1rsytsemo` (request `6oy7kvmszacaa8`) was revoked before any import of its link, by §N.10's day 2
  (pull request #384), so 8.6 deletes pass 5's table asset alone.
- **[Claude] `SUP-391`** gains 5.2's reading of 2026-11-22 (this log), the subscription target's node joining
  the graph across the accounts; the entry held the one-account reading of 2026-11-21.
- **Not run here**: `secret_detection`, GitLab's analyzer; `bundle` and every leg, which need Sandbox
  and GitLab.
