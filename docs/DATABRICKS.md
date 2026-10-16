# Databricks on AWS — how the platform works, read against this project's requirements

What Databricks is made of, read from its documentation on 2026-10-16 for the comparison with
SageMaker Unified Studio the user asked for that day: the Databricks on AWS docs
(`docs.databricks.com/aws/en/`), the platform release notes from September 2025 to October 2026, a
few databricks.com product and press pages, and three AWS Big Data Blog posts. Every URL is in
[`REFERENCES.md`](REFERENCES.md), group "Databricks". A date in the text is the page's own "last
updated" date or a release note's date, which dates a feature's stage. No price here is measured
(Lesson 6): a figure quoted is the documentation's, and the AWS `$/DBU` rates are on no page that
rendered.

[`SMUS.md`](SMUS.md) is the SageMaker Unified Studio counterpart. The last section reads
[`objectives.md`](plan/objectives.md) against Databricks, with the decisions the comparison turns
on: [D13](plan/decisions/D13-lake-formation-enforcement.md),
[D17](plan/decisions/D17-interactive-vs-runtime.md), [D28](plan/decisions/D28-workflow-contract.md),
[D38](plan/decisions/D38-single-egress-hub.md), [D39](plan/decisions/D39-access-by-identity.md) and
[D41](plan/decisions/D41-sagemaker-application.md).

## Names that changed in 2025 and 2026

The current docs use names that differ from the 2025 vocabulary, and search results still show the
old ones. The entries are from the platform release notes unless stated.

| Former name | Current name | Date of the entry |
|---|---|---|
| Databricks Jobs, Databricks Workflows | Lakeflow Jobs ("No migration is required") | 2025-06-11 |
| Delta Live Tables (DLT) | Lakeflow pipelines, built on Spark Declarative Pipelines, open-sourced the same day; "Lakeflow Spark Declarative Pipelines" | 2025-06-11, 2025-11-12 |
| The Pipelines and Workflows sidebar items | Jobs & Pipelines | 2025-06-18 |
| Databricks Assistant | Genie Code | 2026-03-11 |
| Databricks Asset Bundles (DABs) | Declarative Automation Bundles; the `databricks bundle` command is unchanged | 2026-03-16 |
| Databricks One | Genie, then Genie One | 2026-04-27, 2026-06-09 |
| Genie Spaces (AI/BI Genie) | Genie Agents | 2026-07-08 |
| Lakeview dashboards | AI/BI dashboards (the API keeps the Lakeview name); no new legacy dashboard since 2025-04-07 | 2024-07-04 |
| Vector Search | AI Search (the API paths and the SKU still say `VECTOR_SEARCH`) | 2026-06-01 |
| Delta Sharing | OpenSharing (the URLs still live under `/delta-sharing/`) | 2026-06-10 |
| Mosaic AI Gateway | "AI Gateway (legacy)" per endpoint, and Unity Gateway, GA | 2026-08-04 |
| Mosaic AI Model Serving | Model Serving | page of 2026-10-06 |
| Repos | Git folders | no date on the page |
| UniForm (Universal Format) | Iceberg reads | page of 2026-07-23 |
| Single user and Shared access modes | Dedicated and Standard | 2024-12-17, 2025-02-07 |
| Foundation Model Fine-tuning (Mosaic AI Model Training) | end of life; AI Runtime, serverless GPU, in its place | page of 2026-09-11 |
| Lakehouse Monitoring | Data quality monitoring: data profiling and anomaly detection | page of 2026-09-11 |
| Lakebase Provisioned | Lakebase (autoscaling; the navigation label is "Lakebase Postgres") | July 2026 |
| Community Edition | Free Edition, serverless-only | retired 2026-01-01 |
| Agent Bricks (Knowledge Assistant, Supervisor, Custom LLM) | "legacy"; Agent Bricks is now the code-first agent platform (its CLI, Agent Runtime) | 2026-10-12 |

The release-stage vocabulary (the release-types page, 2026-09-21): Private Preview is invite-only;
Beta reaches most customers, on by default for Premium and off for Enterprise, not for production;
Public Preview reaches every customer, SLA-backed, approved for production; then GA. Many pages
carry no label. The docs label previews explicitly, so an unlabeled page is in practice GA, and this
file says "no label on the page" rather than asserting it.

## The deployment on AWS

### The control plane and the two compute planes

- **The control plane** holds the backend services and the web application, "located in the
  Databricks account, not your cloud account" (the high-level-architecture page, 2026-09-11). The
  managed-services data lives there, encrypted at rest: notebook source, secrets, SQL queries and
  query history, AI/BI dashboards, Git credentials, AI Search indexes, Lakebase project data, Model
  Serving images (the customer-managed-keys page, 2026-10-02).
- **The classic compute plane** runs EC2 in the customer's AWS account, inside each workspace's VPC,
  with secure cluster connectivity by default: no public IPs, no open ports, an outbound HTTPS
  tunnel to the control plane on 443 (the classic-networking page, 2026-10-08). A classic workspace
  needs a "workspace storage bucket" in the customer's account, and Databricks plans to require a
  customer-managed VPC for new classic workspaces (the customer-managed-VPC page, 2026-10-08).
- **The serverless compute plane** runs "in a compute layer within your Databricks account", in the
  workspace's region, with no public IPs and without the SCC relay (the serverless-compute page,
  2026-09-11; the serverless-network-security page, 2026-10-06). It is "available by default in most
  workspaces" (the serverless page, 2026-10-15) and the default for jobs and pipelines.
- **Serverless workspaces** (GA 2026-01-29) come with serverless compute and "default storage" in
  the Databricks-owned account, use environment versions instead of Runtime versions and need no
  cloud infrastructure from the customer. Classic compute cannot reach default storage, credential
  vending to external engines is unsupported there, and the deployment guide says not to rely on
  default locations for production data (the serverless-workspaces and default-storage pages,
  2026-10-09).

### What stays in the customer's AWS account

Classic compute, the workspace storage bucket (SQL and job results, notebook revisions, cluster
logs, the workspace catalog, the deprecated DBFS root), and the data: Unity Catalog managed and
external tables and volumes live in S3 at external locations under storage credentials, each an IAM
role in the bucket's account (the external-locations page, 2026-09-11; the manual S3 setup page,
2026-10-06). The role trusts the Databricks Unity Catalog master role under an external ID, must be
self-assuming (enforced since 2025-01-20), and holds the object and bucket actions plus KMS where
the bucket is encrypted. A bucket in another account takes a role in that account.

### Network controls and the tier each needs

The reference architectures (page of 2026-05-20) are "Managed security" (the baseline), "Hardened
connectivity" and "Isolated environment" (all access private, named for financial services,
healthcare and government).

| Control | What it does | Tier the page names |
|---|---|---|
| Secure cluster connectivity and the customer-managed VPC | no public IPs; the VPC chosen at workspace creation, private subnets with NAT egress, egress on 443, 3306, 53, 8443-8445 and 6666, VPC endpoints for S3, STS and Kinesis | none stated |
| Back-end and front-end PrivateLink | classic compute to the control plane; users to the workspace | Enterprise |
| IP access lists | public-IP allow lists for the account console and the workspaces; "context-based ingress" (identity, request type and network source) is the recommended control since its GA of 2026-07-21 | Enterprise |
| Serverless egress control (network policies) | "Full Access" or "Restricted Access", the latter limited to Unity Catalog external locations plus listed FQDNs and buckets, for notebooks, jobs, warehouses, pipelines, Model Serving and Apps | Enterprise |
| Private connectivity from serverless to AWS resources | NCC private endpoints to Bedrock, DynamoDB, EMR, Glue, KMS, Lambda, RDS, Redshift, S3, Secrets Manager, STS, SNS and SQS | Enterprise, Public Preview |
| Customer-managed keys | the managed services and the workspace storage | Enterprise |
| Enhanced Security and Compliance add-on | the compliance security profile (FIPS 140 modules, a CIS Level 1 image, Nitro instances, TLS 1.2+), enhanced monitoring, automatic cluster update | Enterprise plus the add-on |

The private network gateway, which connects serverless compute to resources in the customer's VPC,
to on-premises systems and to the internet, is Private Preview (2026-08-24). A proxy between the
compute and the internet is not a documented shape: serverless egress is a network policy's list,
and classic compute egresses through whatever the customer's VPC provides.

### Account, workspaces, identities, tiers and billing

- One **account** (the console at `accounts.cloud.databricks.com`) holds workspaces; account admins
  create workspaces and manage identities, workspace admins manage one workspace, metastore admins
  govern Unity Catalog (the admin-concepts page, 2026-10-13).
- **Identities** are account-level users, service principals and groups, with identity federation on
  by default and account-level SCIM recommended; SSO is "unified login", one configuration for the
  account and its workspaces, with MFA at the identity provider; OAuth is preferred over personal
  access tokens, and "federation policies" give CI systems workload identity federation (pages of
  2026-09-16 to 2026-10-12). Binding a person's access to a network is the IP access lists' and
  context-based ingress's job, above.
- **Tiers**: Standard ended (every remaining workspace upgraded to Premium by 2025-10-01); Premium
  adds Unity Catalog, serverless, SQL and the AI features; Enterprise adds the security controls
  above (the standard-tier page). Unity Catalog needs "the Premium plan or above" (the
  create-metastore page, 2026-10-06). "The Premium tier on Azure Databricks corresponds to the
  Enterprise tier on AWS and GCP" (the pricing pages).
- **Billing** is in DBUs, "a normalized unit of processing capability per hour", per second, pay as
  you go or committed use; each serverless service has its own DBU rate; Photon instance types
  consume DBUs at a different rate; classic compute also bills the EC2 instances to the customer's
  AWS account ("your cloud provider still charges you for resources such as compute instances", the
  pricing page's trial FAQ). The account-wide record is `system.billing.usage`. The AWS `$/DBU`
  rates did not render on the pricing pages read; the one figure found is a third party's, Apache
  Airflow's provider page: USD 0.40 per DBU on all-purpose compute against 0.07 on jobs compute.

## The programming environment

### Notebooks and editors

- The notebook is Databricks's own web editor (no page names its component), "the primary tool for
  creating data science and machine learning workflows": Python, SQL, Scala and R per cell,
  real-time coauthoring, automatic versioning, built-in visualizations (the notebooks page,
  2026-10-12). The redesigned UI went GA on 2024-06-04; 2025 brought increments (a split view and
  tabs, a Python debugger with a variable explorer, `%skip`, a cell minimap, real-time collaboration
  in cells and files), not a new editor.
- Python runs on the IPython kernel (DBR 11.3 LTS and later). New notebooks are `.ipynb` by default
  since 2024-12-20; import and export cover `.ipynb`, source files, HTML and DBC. A Jupyter notebook
  is imported and run in the Databricks editor; the magics `%sql`, `%run`, `%fs`, `%sh` (the driver
  only), `%pip` and `%uv pip` (serverless environment 5 and later), and `display` and `dbutils`, are
  Databricks's, not Jupyter's.
- A notebook runs only attached to compute: a cluster, a SQL warehouse or serverless (the
  run-notebook page, 2026-09-11). A serverless notebook stops after 2.5 hours of execution by
  default.
- **Genie Code**, the former Assistant, sits in the notebook, the SQL editor, jobs, dashboards, the
  file editor and the pipelines editor: chat, inline edits, autocomplete, "Diagnose error", slash
  commands, and an agent mode that plans, runs cells and fixes errors with the user's approval (GA
  2026-03-11; "runs exclusively in Agent mode" since 2026-06-29). The agentic capabilities need
  "Partner-powered AI features" enabled on the account and the workspace; without them a
  Databricks-hosted model answers without agency. Billing is pay as you go with "150 free DBUs of
  LLM usage per month" per user since 2026-07-08.
- The **SQL editor** (tabs, autocomplete, a schema browser, results capped at 64,000 rows or 10 MB)
  runs on SQL warehouses; the **file editor** edits workspace files of almost any type, 500 MB each.

### The terminal and SSH

- The **web terminal** is a browser shell "from root inside the container of the compute driver
  node", on classic compute, on serverless CPU compute (environment version 2 and later) and on
  serverless GPU; not on jobs compute, not with process isolation, not on environment version 1, and
  "Enabling Docker Container Services disables web terminal". It is "disabled by default for all
  workspace users", an admin enables it, a session is capped at 12 hours per page load, and
  "Databricks does not support running Spark jobs from the web terminal" (the web-terminal page,
  2026-09-11). So a terminal does not need a provisioned machine; it needs the admin's switch.
- **SSH to the driver** on port 2200 with a public key is documented today only for Azure workspaces
  in a customer-managed VNet (the knowledge-base article of 2025-07-14); no AWS page states it
  supported or removed, and `ssh_public_keys` survives as a compute-policy attribute.
- The **SSH tunnel** (Beta, pages of 2026-10-14) is the current remote path: `databricks ssh
  connect` to serverless compute, CPU or GPU, or `databricks ssh setup` for a classic dedicated
  cluster on DBR 17.0 and later, over the workspace HTTPS endpoint with WebSocket, from VS Code
  1.110 and later with Remote - SSH, from Cursor or from IntelliJ; 10 connections per cluster,
  inactive sessions drop after an hour, and only `/Workspace`, `/Volumes` and `/dbfs` survive a
  restart. **Databricks Sandbox** (Beta) is a fixed 4 vCPU and 8 GB serverless box with a persistent
  home, for agent harnesses and IDE sessions, "not a general-purpose Spark runtime".

### Local IDEs

- **Databricks Connect** is a client library on Spark Connect: the code runs locally and the
  DataFrame operations on Databricks compute; Unity Catalog required; the client version must not
  exceed the Runtime's; serverless from Connect 15.1 (the Connect pages, 2026-09-11). No
  `display()`, no RDDs, no distributed ML training.
- The **VS Code extension** (Cursor too) defines, deploys and runs bundles, runs a file on a cluster
  or as a job, syncs a folder, and debugs notebooks cell by cell through Connect in a local `.venv`
  that uv builds to match the runtime's Python and packages. PyCharm uses Connect, the CLI and the
  SDKs; a JetBrains-built plugin exists (2024-08-19) and the current docs do not mention it. No
  JupyterLab page could be read: Connect works with "notebook servers", and inside the tunnel
  `.ipynb` files run on the remote `pythonEnv` kernel.

### Runtimes and environment versions

- **Databricks Runtime**, for classic compute: 14.3 LTS (Python 3.10, support to 2027-02-01), 15.4
  LTS (3.11, 2027-08-19), 16.4 LTS (3.12.3, 2028-05-09), 17.3 LTS (3.12.3, 2028-10-22), 18 LTS
  (3.12, JDK 21, 2029-06-10) and 19 (3.12.3, Spark 4.2.0, GA 2026-07-23), each with a "for Machine
  Learning" variant (MLflow 3.12.0 on 19) that runs only in Dedicated access mode (the runtime
  release notes, 2026-09-11). Support lasts three years after GA; after it the version is not
  selectable.
- **Serverless environment versions** give "a stable client API based on Spark Connect", each with a
  Python version and a pinned package set: 1 (3.10.12, support to 2027-03-12), 2 (3.11.10), 3 to 6
  (3.12.3; 6 released 2026-09-03, support to 2029-09-03) (the environment-version page, 2026-10-12).

### Customizing the environment

| Mechanism | Compute | What it does, and its limits |
|---|---|---|
| `%pip` and `%uv pip` in the notebook | every kind | notebook-scoped; "do not persist"; wheels from volumes or workspace files, private indexes; `%uv pip` on serverless environment 5 and later |
| The Environment pane and base environments | serverless | a base (Standard, ML, AI, a previous version, or a custom YAML) plus dependencies in `requirements.txt` syntax; admins publish up to 10 workspace base environments and star a default (GA 2026-04-24); "Serverless compute does not guarantee a specific CPU architecture" (the dependencies page, 2026-10-15) |
| Compute-scoped libraries | classic | PyPI, Maven, CRAN, volumes, S3, upload; a policy can auto-install up to 500 |
| Init scripts | classic only | a shell script at node start, cluster-scoped recommended, DBFS scripts at end of life; "Serverless compute doesn't support init scripts" |
| Databricks Container Services | classic | a Docker image per compute from Docker Hub or ECR on the `databricksruntime/*` bases; GA on dedicated compute, Beta on standard compute since 2026-05-19 (DBR 18 LTS and later); not with the ML runtime, not on serverless; it disables the web terminal, and `CMD` and `ENTRYPOINT` are ignored |
| "Environments" dependency mode | classic, DBR 19 and later, Beta | base environments on classic compute; disables Docker, init scripts and cluster libraries |
| Compute policies | classic | an admin's limits on `spark_version`, node types, autotermination, `docker_image`, `init_scripts`, tags, `ssh_public_keys`; serverless has no policies, only serverless budget policies |

No page offers a custom Jupyter kernel or a conda environment for the web notebook: Python runs on
the IPython kernel, and the mechanisms above are the customization. The one "kernel" a user picks is
the remote `pythonEnv` virtual environment inside the SSH tunnel. Read this as an absence in the
docs, not as a quoted limitation.

### Compute, and who provisions it

- Classic compute is all-purpose, jobs and pipelines compute in the customer's VPC; access modes
  Standard (several users, isolated by Lakeguard) and Dedicated (one user or group); single-node
  compute; Photon on by default. Admins and users with "Unrestricted cluster creation" create it
  freely; everyone else creates it only from an assigned policy, and "All users have the Personal
  Compute policy, which creates single-machine compute" (the configure page, 2026-10-12).
- Serverless covers notebooks, jobs, pipelines, SQL warehouses (which start in 2 to 6 seconds), AI
  Runtime (GPU, Public Preview) and Model Serving, with nothing to provision; "Serverless compute
  for jobs is the default for all tasks that support it".
- Free Edition, which replaced Community Edition (retired 2026-01-01), is "a serverless-only,
  quota-limited environment" with no classic compute, no SSO or SCIM and no private networking, for
  non-commercial use. The user's personal workspace could not exercise the terminal: a notebook's
  Terminal pane there reads "Requires cluster to be attached" (read 2026-10-16).

## Orchestration: Lakeflow Jobs

- "Lakeflow Jobs is workflow automation for Databricks": a job is a DAG of tasks with a trigger; the
  limits are 1,000 tasks per job, 2,000 concurrent task runs and 12,000 saved jobs per workspace
  (the jobs page, 2026-10-09).
- Task types: Notebook (with a "Visual data prep" sub-option), Python script, Python wheel, SQL,
  Pipeline, SQL alert, Dashboards, Power BI (Public Preview), dbt and dbt platform, JAR, Spark
  Submit, Run Job (another job, nested at most three deep), Genie Code (Beta), If/else and For each;
  there is no "Databricks app" task (the task page, 2026-10-07).
- Control flow: dependencies, "Run if" conditions (all succeeded, at least one failed, and the
  rest), If/else on task values or parameters, For each loops, disabled tasks (GA 2026-04-30), and
  repair runs that re-run only the failed subset and its dependents.
- Triggers: scheduled, table update (any or all of up to 10 Unity Catalog tables, with a minimum
  interval and a settle time), file arrival in a Unity Catalog location, model update (Beta),
  continuous, or none; up to five triggers per job (Beta 2026-10-05). Queueing is on by default for
  jobs created in the UI after 2024-04-15, and a queued run waits up to 48 hours.
- Compute: serverless jobs by default, with Photon and autoscaling on, where the "Standard"
  performance mode starts in 4 to 6 minutes and "Performance optimized" faster on the "same SKU",
  standard consuming "fewer DBUs"; classic jobs compute; SQL warehouses for SQL and dbt tasks;
  all-purpose compute, which "Databricks does not recommend ... for production jobs" (the compute
  page, 2026-09-15).
- Notifications go to e-mail, Slack, Teams, PagerDuty and webhooks; the Runs page covers 60 days
  across jobs and pipelines, "including runs started by external tools such as Apache Airflow"; a
  run links to its lineage; the `system.lakeflow` tables hold the history.
- Job as code: the Jobs API, the SDKs, the CLI, the VS Code extension, bundles (the UI writes its
  edits back to the bundle YAML since 2026-05-19) and Terraform. No job version history exists;
  "Switch to code version (YAML)" shows the definition.
- A cross-workspace dependency has no page: the Run Job task triggers jobs "in your Databricks
  workspace", and the only cross-workspace statement is a network one (serverless cross-workspace
  access, same region, Beta 2026-08-13).

### Apache Airflow beside Lakeflow Jobs

Airflow is not inside Databricks. Its page installs Airflow outside (2.5 and later, Python 3.8 to
3.11) with `apache-airflow-providers-databricks`, and the DAG calls the Jobs API:
`DatabricksRunNowOperator` (recommended because "it reduces duplication of job definitions"),
`DatabricksSubmitRunOperator`, `DatabricksSqlOperator`; the provider "is not directly supported by
Databricks" (the Airflow page, 2026-09-11). The provider's own `DatabricksWorkflowTaskGroup` creates
a job named `<dag>.<group>` and runs notebooks on job clusters at the jobs-compute rate. The
counterpart of a SMUS workflow, an Airflow DAG on MWAA Serverless ([`SMUS.md`](SMUS.md)), is
therefore Lakeflow Jobs, a native scheduler with its own DAG, triggers and queue; Airflow reaches
Databricks only from outside, as a client of that API.

## ETL: Lakeflow pipelines, Designer and Connect

- **Lakeflow** is the umbrella: Lakeflow Connect for ingestion, Lakeflow pipelines ("built on Apache
  Spark Declarative Pipelines"), Lakeflow Designer and Lakeflow Jobs; the Runtime includes
  **Photon**, "a high-performance Databricks-native vectorized query engine" (the data-engineering
  page, 2026-10-15).
- **Lakeflow pipelines** are the former Delta Live Tables ("no migration required"; `import dlt`
  becomes `from pyspark import pipelines as dp`): Python or SQL files declaring streaming tables,
  materialized views, views and sinks (Delta tables, Kafka topics); the graph is inferred, the
  orchestration and the retries are automatic, AUTO CDC handles out-of-order changes and SCD types 1
  and 2; **expectations** (`CONSTRAINT ... EXPECT`, with warn, drop or fail) are the data-quality
  rules, with their metrics in the UI and the event log. New pipelines default to serverless (the
  `ADVANCED` edition; 4 to 6 minutes to start in standard mode). The **Lakeflow Pipelines Editor**,
  "an IDE built for pipeline development" with the DAG, previews and Git folders, is GA since
  2026-05-04.
- **Lakeflow Designer** is the no-code canvas: "visual data prep files" as graphs of operators
  (filter, aggregate, join, reshape, user-defined operators), each step backed by code, edited in
  natural language by Genie Code, versioned in Git, scheduled as a Notebook task's "Visual data
  prep" sub-option and deployed through bundles; Public Preview 2026-04-22, GA 2026-06-16. It is the
  counterpart of SMUS's Visual ETL ([`SMUS.md`](SMUS.md)); where a `.vetl` flow graduates as the
  Glue script its editor generates ([D28](plan/decisions/D28-workflow-contract.md) class 2c), a
  visual data prep file is itself the deployable artifact.
- **Photon** replaces the JVM execution layer with a native C++ runtime for the operations it
  supports, on serverless, on SQL warehouses and on pipelines, and on by default on classic compute;
  not for UDFs, RDDs or stateful streaming; "Photon instance types consume DBUs at a different
  rate".
- **dbt** runs as a job task (dbt Core on a SQL warehouse through the `dbt-databricks` adapter) or
  through the "dbt platform" task (Public Preview). SQL alone is an ETL path: streaming tables and
  materialized views declared in Databricks SQL run as standalone pipelines.
- **Data quality monitoring**, the former Lakehouse Monitoring: anomaly detection (freshness and
  completeness per schema, Public Preview) and data profiling, on serverless, billed under
  `DATA_QUALITY_MONITORING`, with the results in Catalog Explorer and the system tables.
- **Lineage** is captured automatically, to the column level, for queries, notebooks, jobs,
  pipelines, dashboards, models and UDFs that read Unity Catalog data, shown in Catalog Explorer and
  kept in `system.access.table_lineage` and `column_lineage` for a year.

The Spark here is Databricks's own Runtime with Photon, in the customer's VPC (classic) or in the
Databricks account (serverless). SMUS's Visual ETL and Glue jobs run AWS Glue's Spark in the AWS
account, under Lake Formation ([`SMUS.md`](SMUS.md)).

## Dashboards and BI

- **AI/BI dashboards**, the former Lakeview: datasets from Unity Catalog tables, views and metric
  views, from SQL or from uploads; visualizations, filters with cross-filtering and drill-through,
  custom calculations, themes; 100 datasets and 15 pages per dashboard (the dashboards pages,
  2026-09-11 to 2026-10-12). Creating one needs the "Databricks SQL" entitlement and CAN USE on a
  SQL warehouse; the refresh task of a job needs a serverless or Pro warehouse; a serverless SQL
  warehouse needs "the Premium plan or above".
- **Publishing** snapshots the draft with "Share data permissions", the publisher's credentials (a
  user or a service principal), or "Individual data permissions", the viewer's own; viewers are
  workspace users, "All workspace users" or "Anyone in my account", account users without a
  workspace included, who get a view-only copy under the "Consumer access" entitlement. Schedules
  refresh the dashboard and send PDF, CSV or Excel by e-mail, Slack and Teams to up to 100
  subscribers. Embedding is basic (an iframe, Databricks sign-in) or external (viewers without
  Databricks accounts, a service principal's OAuth; GA 2026-04-09).
- "Published dashboards include a Genie Agent by default": natural-language questions over the
  dashboard's datasets (up to 30), and "explain a change" on a chart.
- Dashboards as code: export and import as `.lvdash.json`, the bundle resource `dashboards`,
  Terraform's `databricks_dashboard`, the Lakeview REST API and Git folders; a job's Dashboard task
  refreshes a published dashboard and mails its subscribers.
- **Genie Agents**, the former Genie Spaces, are curated natural-language interfaces over Unity
  Catalog datasets returning SQL, tables and charts; **Genie One** is the business user's front door
  (dashboards, Genie chat, Databricks Apps; "Consumer access" suffices), free with Genie Agents
  through 2027-01-31. Legacy dashboards cannot be created since 2025-04-07.
- **Databricks SQL** is the editor, the SQL warehouses (serverless, pro and classic, plus "Lakehouse
  Real-Time" in Beta), alerts (GA 2026-05-14), query history and metric views. **Power BI** gets a
  semantic model from a job task (Public Preview); Partner Connect lists Hex, Power BI, Preset,
  Qlik, Sigma, Tableau and ThoughtSpot.

The SMUS counterpart is Amazon QuickSight, a separate service that a blueprint enables per project
(category 3 here, not set up in the lab, [`SMUS.md`](SMUS.md)); Databricks's dashboards live inside
the workspace and share its identities and Unity Catalog's permissions.

## Data sources and ingestion

- **Lakeflow Connect** managed connectors: a Unity Catalog "connection" holding the credentials, an
  ingestion pipeline on serverless and destination streaming tables. The catalog page (2026-10-14)
  lists 62 SaaS connectors (Salesforce, Workday, ServiceNow, SharePoint, GitHub and GitLab among
  them, most of them in Beta by their last release note); the database connectors read MySQL,
  PostgreSQL, SQL Server and Oracle by change data capture through an "ingestion gateway" on classic
  compute in the customer's VPC, billed while the pipeline idles; the query-based connectors (GA
  2026-05-29) read any Lakehouse Federation source, Redshift included, by a cursor column and
  without a gateway. The connectors "are in various release states" and the overview gives no
  per-connector status.
- **Zerobus Ingest** is a push API (gRPC SDKs, REST, OTLP, MQTT and Kafka-compatible endpoints) that
  writes straight into Unity Catalog Delta tables, validated against the table's schema, at up to
  100 MB/s per stream.
- **Auto Loader** (`cloudFiles`, exactly once; S3 file notifications through SNS and SQS that
  Databricks creates, or Unity Catalog file events), **COPY INTO** (idempotent SQL loads) and the
  upload UI (5 GB per file, into a volume) cover files.
- **Lakehouse Federation** copies nothing: query federation over JDBC with pushdown for MySQL,
  PostgreSQL, Oracle, Teradata, SQL Server, **Amazon Redshift** (`host`, `port`, user and password;
  read-only; for "ad hoc reporting and proofs of concept"), Snowflake, BigQuery, Azure Synapse,
  Salesforce Data 360 and another Databricks; catalog federation over object storage for Hive
  metastores, **AWS Glue**, Snowflake, Palantir Foundry and Workday. Everything is read-only but a
  federated internal Hive metastore.
- **OpenSharing**, the former Delta Sharing: Databricks to Databricks, open sharing (a bearer token
  or OIDC) and sharing to external Iceberg clients; the Marketplace and Clean Rooms are built on it.
  Streaming sources are Kafka (`read_kafka`), Kinesis (polling or enhanced fan-out), Pub/Sub and
  Pulsar.

## Object storage

- The unit is the **external location**, an S3 path plus a storage credential, under which sit
  external tables, external volumes and the managed storage of catalogs and schemas; "Databricks
  recommends that you assign managed storage at the catalog level", with separate storage for
  development, staging and production (the managed-storage page, 2026-09-11; the deployment guide,
  2026-10-09).
- **Managed tables** are "the default and recommended table type": Delta by default, Apache Iceberg
  with `USING iceberg` (GA 2026-05-21, with predictive optimization on and serverless enabled);
  their files live in the schema's or the catalog's managed location and are deleted after a
  recovery window on `DROP`; "Path-based access is not supported except in Compatibility Mode".
  External engines reach them through the Unity REST API, the Iceberg REST catalog with credential
  vending (`/api/2.1/unity-catalog/iceberg-rest`, the privilege `EXTERNAL USE SCHEMA`), OpenSharing,
  or **Compatibility Mode** (Public Preview since 2025-10-21), read-only copies refreshed on a
  schedule for readers without those APIs.
- **Iceberg reads** on a Delta table, the former UniForm, generate Iceberg metadata asynchronously
  for read-only clients; "engines like Athena or Redshift" need `REORG ... UPGRADE UNIFORM`.
- **Volumes** hold non-tabular files at `/Volumes/<catalog>/<schema>/<volume>/` (landing zones,
  wheels and JARs, media, checkpoints). **DBFS** root and mounts are "deprecated and not
  recommended", and "New accounts are provisioned without access to these features" (the DBFS page,
  2026-09-11). **Workspace files** are capped at 500 MB. Instance profiles are the legacy access
  pattern.
- **Predictive optimization** (compaction, cleanup, statistics and automatic liquid clustering;
  Premium) is on by default for accounts created since 2024-11-11; **liquid clustering** "replaces
  table partitioning and `ZORDER`".

## Unity Catalog

- "The unified governance layer for data and AI built into Databricks", on by default for workspaces
  created after 2023-11-08; **one metastore per region**, linked to any number of that region's
  workspaces, on Premium; the namespace `catalog.schema.object` covers tables, views, volumes,
  functions, models and, since Unity Gateway, "services" (the Unity Catalog pages, 2026-09-11 to
  2026-10-06). The per-workspace Hive metastore survives as the catalog `hive_metastore`, a legacy
  feature Databricks recommends disabling.
- **Access control**: privileges with inheritance down the hierarchy (`USE CATALOG`, `USE SCHEMA`,
  `SELECT`, `MODIFY`, `CREATE TABLE`, `READ VOLUME`, `EXECUTE`, `BROWSE`, `MANAGE` and the rest),
  one owner per object; **ABAC** on governed tags (GA 2026-04-28; row-filter, column-mask, GRANT and
  DENY policies, up to 10,000 per metastore), recommended over per-table **row filters and column
  masks** (SQL UDFs, not on views, not served through the Iceberg REST and Unity REST APIs); and
  **workspace-catalog binding** (`OPEN` or `ISOLATED`, optionally read-only), the isolation lever
  between environments.
- **Governed tags** (GA 2026-04-02) are account-level tags with enforced values on catalogs,
  schemas, tables, columns, volumes, models, secrets and services; **data classification** (GA
  2026-04-20) scans new tables with an agent within 24 hours and feeds ABAC through automatic tags;
  **lineage** reaches the column level, with external assets since 2026-06-08; the **system tables**
  (the `system` catalog: audit events for 365 days, billing, compute, jobs, query history, Unity
  Catalog access events, classification results, serving logs) are free but for the query compute;
  AI-generated comments, **metric views** as governed KPIs, and the **Discover** page with domains
  (GA 2026-10-08) complete the surface.
- **Federated catalogs**: Hive metastore federation, AWS Glue included, mirrors a Glue catalog as a
  read-only foreign catalog, by a self-assuming IAM role, a service credential, `CREATE CONNECTION
  ... TYPE glue` and external locations for the table paths. "Writes are supported only for
  federated internal Hive metastores, not external Hive metastores or AWS Glue", and the sync
  "treats the schemas visible to the credential in AWS Glue as authoritative", so a lost Lake
  Formation permission drops and recreates schemas and their grants (the Glue federation page,
  2026-10-13). The old "Glue Data Catalog as the metastore"
  (`spark.databricks.hive.metastore.glueCatalog.enabled`) is "a legacy data governance model".
- **Open source**: Unity Catalog's server is Apache 2.0, with the Iceberg REST and Hive metastore
  interfaces (announced 2024-06-12); 25 engines read Databricks tables through the Unity REST API or
  the Iceberg REST catalog (Spark, Trino, DuckDB, Snowflake, Flink and PyIceberg among them).
  Athena, EMR, Glue, BigQuery and Fabric are not on that page.

### Interoperability with the AWS catalogs

- **AWS reading Databricks tables**: AWS Glue's "catalog federation for remote Apache Iceberg
  catalogs" (GA 2025-11-24) registers Unity Catalog as a Lake Formation federated catalog of the
  connection type `DATABRICKSICEBERGRESTCATALOG`, with a service principal's OAuth secret, and
  Athena, Redshift, EMR, Glue and SageMaker read it with Lake Formation vending scoped credentials,
  read-only; the tables must be managed Iceberg or Delta with Iceberg reads, with "External data
  access" and `EXTERNAL USE SCHEMA` granted on the Databricks side (the AWS blog of 2026-01-12).
- **Databricks reading Glue Iceberg tables**: natively by Glue federation (foreign Iceberg tables,
  GA by the release note of 2026-05-21 while the concepts page of 2026-09-11 still says "Public
  Preview"), or outside Unity Catalog by a Spark `rest` catalog against
  `glue.<region>.amazonaws.com/iceberg` with SigV4 (the AWS blog of 2025-01-23).
- **Redshift** is a federation source (above), a private-connectivity target from serverless (Public
  Preview, Enterprise) and an ingestion source for the query-based connectors. No page states that
  Athena or Redshift act as OpenSharing recipients.
- **Amazon Bedrock** is an external-model provider (`amazon-bedrock`, with Anthropic, Cohere, AI21
  and Amazon models), authenticated by a Unity Catalog service credential, an instance profile or
  keys and governed by the gateway; "Unity Gateway supports Amazon Bedrock Mantle" (2026-10-09).

## AI

### Foundation models and the gateway

- **Foundation Model APIs** host the models inside Databricks, pay per token, priority pay per
  token, or provisioned throughput on demand or reserved: Anthropic Claude (Haiku 4.5 to 5.5, Sonnet
  4.5 to 5.5, Opus 4.1 to 5.5, Fable 5 and 5.1), OpenAI GPT-5 to GPT-6.1, Google Gemini 3 to 4, Meta
  Llama 3.1 to 4, Qwen, Grok, GLM, Kimi, DeepSeek, and two embedding models (the supported-models
  page, 2026-10-13); Claude Fable 5 and 5.1 carry a 30-day retention of prompts and responses. They
  appear as "system-provided model services" in `system.ai`, for example `system.ai.claude-opus-5`.
  Foundation Model APIs are "a Databricks Designated Service" with data residency by Geos, and pay
  per token may store inputs and outputs up to 30 days for abuse detection.
- **External models** reach OpenAI, Azure OpenAI, Anthropic, Cohere, AI21, Google Vertex AI,
  **Amazon Bedrock** (`bedrock-runtime` and Bedrock Mantle) and custom OpenAI-compatible endpoints
  through the same serving API; PrivateLink to them is Public Preview.
- **Unity Gateway** (GA 2026-08-04; the per-endpoint "AI Gateway" is legacy) makes model services,
  model provider services, MCP services, skills and models Unity Catalog securables (`EXECUTE`,
  `CREATE SERVICE`, `MANAGE`), with rate limits (QPM and TPM, HTTP 429 beyond them), traffic
  splitting and fallbacks, usage tracking in `system.ai_gateway.usage`, inference tables (billed),
  budgets that alert or block ("not a strict cap"), guardrails as service policies (Beta), and
  governance of coding agents (Claude Code, Codex, Cursor, Gemini CLI).
- The **Playground** chats and compares models side by side; building agents there is "a legacy
  approach". **AI Functions** in SQL (`ai_query`, `ai_extract`, `ai_classify`, `ai_parse_document`,
  `ai_summarize`, `ai_translate`, `ai_mask`, `ai_forecast`, `vector_search` and more) run on
  serverless or pro warehouses and on DBR 15.4 and later; **batch inference** is `ai_query` over a
  table, as a pipeline, a job or a stream.

### Training with the user's data

- **Foundation Model Fine-tuning** reached end of life. **AI Runtime** (serverless GPU, Public
  Preview, enabled by an admin) takes its place: A10 and H100, B300 by waitlist, single and
  multi-GPU, Ray for multi-node, LoRA, QLoRA and full fine-tuning; notebook jobs run up to 24 hours
  and CLI jobs 14 days; custom Docker images (Beta) and a web terminal (Public Preview).
- Classical ML: the **ML Runtime** on classic compute (PyTorch, TensorFlow, XGBoost, LightGBM,
  MLlib, Optuna), **AutoML** (classification, regression, forecasting; a PyPI package since DBR 18.0
  ML), the **Feature Store** (Feature Views GA 2026-10-12, an online store on Lakebase), **managed
  MLflow 3** (experiments, tracing, evaluation, prompts, deployment jobs with approval steps) and
  **Models in Unity Catalog** (versions, aliases such as "Champion", no stages, shared across
  workspaces and by OpenSharing).

### Publishing endpoints

- **Model Serving** gives serverless REST endpoints to custom MLflow models, agents,
  Databricks-hosted and external models: CPU workloads of 4 to 16 GB and GPUs from one T4 to eight
  A10G; scale to zero after 30 idle minutes ("no SLA", a cold start of seconds to minutes); 1,000
  endpoints per workspace, 16 MB payloads, route optimization up to 300,000 QPS; inference tables
  and endpoint telemetry.
- **Agents** deploy since 2026-10-05 to the **Agent Runtime** on Databricks Apps (`agentbricks
  deploy`, 1 to 5 instances, the app's service principal), the Model Serving path being legacy. **AI
  Search**, the former Vector Search, offers standard endpoints of about 320 million vectors and
  storage-optimized ones above a billion, Delta Sync indexes with Databricks-computed embeddings and
  hybrid search, billed per vector search unit. **Databricks Apps** (Streamlit, Dash, Gradio,
  Node.js; billed per hour while running; a service principal each; deployed by UI, CLI, Git or
  bundles) and **Lakebase** (managed Postgres, GA 2026-01-22; projects, branches, scale to zero,
  synced tables from Unity Catalog) complete the serving side.

### Agents and assistants

- **Agent Bricks** is now "the Databricks agent developer platform", code first: the Agent Bricks
  CLI (Beta 2026-09-29; `agentbricks init`, `dev` and `deploy`, LangGraph and OpenAI Agents SDK
  templates), AgentKit and `DurableAgentServer` for durable execution, the Agent Runtime, the
  Databricks Sandbox, memory and sessions on Lakebase, and MLflow tracing and evaluation (LLM
  judges, production monitoring, human feedback). The tools are Unity Catalog functions, **MCP**
  services (Genie One's MCP server GA 2026-09-25; Databricks SQL, GitHub and Slack servers; external
  servers governed by Unity Catalog) and Genie Agents. The 2025 Agent Bricks products (the Knowledge
  Assistant over up to 10 sources, the Supervisor over up to 50 subagents, the Custom LLM) are
  "legacy" since 2026-10-12; Information Extraction continues on `ai_extract`.
- The assistants for people are **Genie Code** for developers (above), **Genie Agents** for analysts
  and **Genie One** for business users (with Slack and Teams apps, Google Sheets and Excel).

The SMUS counterpart is Bedrock's surface ([`SMUS.md`](SMUS.md): the six `AmazonBedrock*` blueprints
and the Generative AI menu with its playground, chat agents, prompts, guardrails, flows and
knowledge bases) plus SageMaker AI (JumpStart, training, the Model Registry, inference endpoints,
MLflow). Databricks hosts the frontier models itself and governs them, Bedrock included, through
Unity Gateway; SMUS reaches them through Bedrock in the account's region, under the SCP's model
allow-list.

## CI/CD and promotion between environments

### Declarative Automation Bundles

- A bundle, the former Databricks Asset Bundle, is a project folder whose `databricks.yml` declares
  `bundle`, `include`, `resources`, `targets`, `variables`, `workspace`, `run_as`, `permissions`,
  `presets` and `artifacts`, deployed to a target as one unit (the bundles pages, 2026-09-11). Its
  resources are jobs, pipelines, dashboards, Genie agents, apps, experiments, registered models,
  model serving endpoints, Unity Gateway services (Beta), AI Search endpoints and indexes, Lakebase
  objects, clusters, cluster policies, SQL warehouses, schemas, volumes, external locations, secret
  scopes and alerts.
- A target carries `mode: development` (names prefixed `[dev <user>]`, schedules paused, concurrent
  runs allowed) or `mode: production` (pipelines not in development, the Git branch checked against
  `git.branch`, `run_as` a service principal recommended); `presets` override the mode's defaults.
- The commands are `validate`, `plan`, `deploy -t <target>`, `run`, `destroy`, `generate` and
  `deployment bind` (which adopt an existing job, pipeline, dashboard or app), `summary` and `sync`;
  the templates `default-python` (on uv), `default-sql`, `dbt-sql`, `mlops-stacks` and `pydabs`
  (Python in place of YAML). The "direct deployment engine", with no Terraform underneath, is GA
  since 2026-06-10 and the default for CLI 1.3.0 and later. The workspace UI deploys a bundle to a
  target but "doesn't support deploying across different workspaces"; the VS Code extension runs the
  same commands; since 2026-05-19 an edit in the jobs UI writes back to the bundle's YAML.
- CI has documented examples for GitHub Actions (`databricks/setup-cli`, OIDC federation), Azure
  DevOps and Jenkins; no GitLab CI page exists (the CI/CD overview, 2026-10-07). CI authenticates as
  a service principal by OAuth M2M, or by workload identity federation without a Databricks secret.
  The pt-BR course "Automated Deployment with Declarative Automation Bundles" (4 hours,
  Professional, published 2026-05-08) covers the bundle's structure, variables, targets and
  templates, CI/CD with GitHub Actions, and local development in VS Code.

### Git integration

- **Git folders**, the former Repos, clone a repository into the workspace over HTTPS (no SSH) from
  GitHub, Bitbucket, GitLab including "GitLab Self-Managed", Azure DevOps and CodeCommit, with a Git
  proxy for a server off the internet; branch, commit, push, pull, merge, rebase and conflict
  resolution happen in the UI, pull requests in the provider; a working branch holds at most 1 GB. A
  notebook is an `.ipynb` file or a source file opening with `# Databricks notebook source`;
  queries, dashboards and alerts are files too (Public Preview); MLflow experiments and Genie Agents
  cannot be committed.
- A job can read its notebooks, scripts, SQL and dbt projects from a remote Git branch, tag or
  commit; Git folders are recommended "only for development iteration, not staging or production"
  (the jobs Git page, 2026-09-11).

### The recommended promotion model

- "Declarative Automation Bundles are the recommended approach to CI/CD on Databricks"; Terraform
  provisions the workspaces, the Unity Catalog objects and the admin resources; Git folders are
  "alternatives for source-controlling code only" (the CI/CD overview, 2026-10-07).
- **An environment is a workspace**: teams of up to about five engineers use dev and prod
  workspaces, larger teams add a staging workspace mirroring prod, regulated industries isolate
  workspaces and cloud accounts (the developer best-practices page, 2026-09-11); "Isolate
  environments with separate development, staging, and production workspaces" (the CI/CD flows
  page). The data side is **one metastore per region with `dev`, `staging` and `prod` catalogs**,
  the prod catalog bound `ISOLATED` to the prod workspace, personal schemas `dev_<user>`, production
  writes reserved to service principals and ownership held by groups.
- **Identities**: separate deployment and runtime service principals, one narrowly scoped principal
  per production workload, OIDC workload identity federation for CI; **trunk-based development**,
  artifacts versioned by commit hash, one bundle per project covering every environment and deployed
  to a team-owned path; tests in three layers (unit tests on the pull request, `bundle validate`
  plus a deploy to non-prod, integration tests in staging).
- **MLOps**: "deploy code, not models" (the promoted code retrains per environment; "deploy models"
  only when training is expensive), the model aliases "Challenger" and "Champion", a release branch
  triggering the production jobs; **MLOps Stacks** (`databricks bundle init mlops-stacks`) assumes
  separate dev, staging and prod workspaces and ships CI for GitHub Actions and Azure DevOps. The
  MLOps workflow page frames the stages as catalogs without requiring a workspace per stage; the
  best-practices page combines both.
- **Databricks Apps** promote as a bundle resource with the same targets, with `bundle run <app>`
  after the deploy because "deploy doesn't restart the app process".

In this project's terms ([D17](plan/decisions/D17-interactive-vs-runtime.md),
[D28](plan/decisions/D28-workflow-contract.md), [D41](plan/decisions/D41-sagemaker-application.md)):
the SageMaker application is a repository with `manifest.yaml`, workflows in the CI/CD CLI's
notation and code; the CLI deploys it between the Sandbox projects and bundles it; the GitLab
pipeline deploys the bundle into Staging and Production, which hold no project and no portal. The
Databricks shape of the same idea is the bundle, deployed by `databricks bundle deploy -t <target>`
from the pipeline's service principal into a workspace per environment. There the production
workspace is a whole workspace, with notebooks and a UI, and its isolation is the catalog binding,
the service principals, the compute policies and the permissions, not the absence of an interactive
surface.

## The requirements read against Databricks

[`objectives.md`](plan/objectives.md) is the specification. This section reads its bullets against
the pages above as a comparison aid; it decides nothing, and the SMUS column repeats what the stage
logs measured.

| Requirement | SMUS, as built | Databricks, as documented |
|---|---|---|
| Access by identity, the VPN only for private addresses ([D39](plan/decisions/D39-access-by-identity.md)) | Identity Center sessions; no network condition on a persona; the portal and JupyterLab reachable off the VPN | unified login with the identity provider's MFA, identity federation; a network binding exists as IP access lists and context-based ingress, both Enterprise |
| Notebooks and VS Code, as many instances as the user wants, each on a chosen compute and image | JupyterLab and Code Editor spaces on a chosen instance type and image; remote VS Code over SSM ([`remote-ide.md`](plan/runbooks/remote-ide.md)) | notebooks on serverless, or on classic compute created from a policy; the SSH tunnel (Beta) for VS Code and Cursor; a custom image only on classic compute, which also turns the web terminal off |
| The catalog and explorer, SQL | the SageMaker Catalog, Athena and the Query Editor, Redshift by connection | Unity Catalog and Catalog Explorer, the SQL editor on SQL warehouses; Redshift by federation, read-only |
| S3 inside the UI, the group's `sandbox-lake` | the project's S3 path and its S3 connections | external locations and volumes, the file browser of Catalog Explorer |
| Workflows and Visual ETL | MWAA Serverless workflows, Airflow DAGs; Visual ETL on Glue | Lakeflow Jobs, a native DAG scheduler with triggers; Lakeflow Designer on Spark and Photon |
| AI models inside the workbench | Bedrock's surface and SageMaker AI | Databricks-hosted models, external models, Unity Gateway, Model Serving, AI Runtime |
| Promotion Sandbox → Staging → Production by GitLab pipelines | the application, the CI/CD CLI, the bundle, headless targets ([D17](plan/decisions/D17-interactive-vs-runtime.md), [D28](plan/decisions/D28-workflow-contract.md), [D41](plan/decisions/D41-sagemaker-application.md)) | bundles deployed by a service principal into a workspace per environment; GitLab is a Git provider, not a documented CI example |
| Iceberg on S3 under the Glue Data Catalog and Lake Formation ([D13](plan/decisions/D13-lake-formation-enforcement.md)) | the lake, read by Athena and Redshift | Unity Catalog over its own S3 external locations; Glue read-only by federation, where Lake Formation's grant to the federation role is the ceiling and a lost grant rewrites the foreign schemas; AWS reads Databricks tables through Glue's Iceberg catalog federation |
| One internet egress and one proxy for the compute ([D38](plan/decisions/D38-single-egress-hub.md)) | the hub's Squid proxy; spokes without a default route | classic compute egresses through the customer's VPC, a NAT or a proxy of the customer's; serverless egress is a network policy's allow list (Enterprise); the control plane and the serverless plane stay outside the customer's VPC |
| DLP: discovery, fine-grained access, egress control, exfiltration detection | Macie and Lake Formation (Stage 11), the proxy, GuardDuty | data classification (GA 2026-04-20), ABAC with row filters and column masks, network policies, the audit system tables and the inference tables |
| GitLab, GitLab Pages and ECR on the intranet | built (Stage 7) | Git folders reach "GitLab Self-Managed" over HTTPS or a Git proxy; images come from ECR by instance profile on classic compute; Pages has no counterpart |
| The budget ceiling ([D12](plan/decisions/D12-budget-ceiling.md)), everything measured | measured per service in [`PRICING.md`](PRICING.md) | DBUs on top of EC2 (classic) or the serverless SKUs; Enterprise for the network controls above; no AWS rate rendered on the pricing pages |

## Open points

- The AWS `$/DBU` rates for jobs, all-purpose and SQL warehouse compute, and whether the cloud
  instance charges appear in `system.billing.usage`.
- Legacy port-2200 SSH on AWS: no page states it supported or removed.
- The GA note of Zerobus Ingest's base connector, of Hive metastore federation and of metric views;
  foreign Iceberg tables GA (2026-05-21) against the concepts page's "Public Preview" (2026-09-11).
- The sidebar's section names: the navigation page (2026-09-24) against the release note of
  2026-05-21 that renamed SQL to Lakehouse and grouped an Analytics section.
- A page describing a cross-workspace job dependency, and a job version history.
- Whether Athena or Redshift act as OpenSharing recipients.
