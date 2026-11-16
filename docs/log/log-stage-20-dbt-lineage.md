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
