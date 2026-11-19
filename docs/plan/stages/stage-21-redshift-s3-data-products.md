# Stage 21 — Redshift tables and S3 objects as data products in SageMaker Unified Studio

| | |
|---|---|
| **Status** | **Pass 1 done 2026-11-18** ([log](../../log/log-stage-21-redshift-s3-data-products.md)). Written 2026-11-17: the plan, the user's questions of 2026-11-17 answered from AWS's pages read that day and from this estate's measurements, and decisions 1 to 3, taken the same day: 1 (b), the consumer's own workgroup by the `RedshiftServerless` blueprint for one sitting; 2 (a), a second connection by secret for lineage; 3 (b), the federated catalog with data lake access for one sitting. 1.3's readings, 2026-11-18 with nothing up: the blueprint's template holds the base capacity at 4 RPU through a locked `redshiftBaseCapacity`, so decision 1 stands. 1.5's code written the same day, off by default, both slices planned *"No changes."*; the tag `sagemaker-prereqs-v0.12.0` pushed the same night by Recipe B and `sandbox/sagemaker/` moved to it, re-planned *"No changes."*; owed: the user's reading of the console's enable wizard before 2.4. 4.5's data transfer role written and merged 2026-11-18 with [pull request #323](https://github.com/felipenoris/AWS-DataScience/pull/323), `data_transfer_role_enabled` off, planned *"Plan: 2 to add"* with it on. Passes 2 to 4 ride the Sandbox warehouse sitting ([`runbooks/promotion.md`](../runbooks/promotion.md) §N.6 item 9), before 2026-12-19 if the free trial is to absorb them; their commands, and pass 5's, follow each pass's steps. Pass 5 needs no warehouse and rides any Sandbox sitting with a space in both projects |
| **Prerequisites** | [5b](stage-05b-redshift-serverless.md) and [6h](stage-06h-redshift-connection.md): the Sandbox warehouse at 4 base RPUs and `eighth-experimentation`'s connection, which writes and reads the schema `lab` in the `sandbox` database (6h passes 0 to 2, 2026-10-10). [Stage 19](stage-19-smus-native-data-product.md)'s Glue road: a table imported by a project's source, published, packaged in a product and subscribed inside one account (verification vi, 2026-11-14); its pass 5, whose 5.3 publishes the estate's first Redshift asset and subscribes nothing. `test-experimentation`'s `DataLake` environment ([6f](stage-06f-data-governance.md) 2.0), the Glue subscription target. The account's S3 Access Grants instance, created by SageMaker Unified Studio with one location per project ([`docs/SMUS.md`](../../SMUS.md), "The vending surface under that same path", 2026-08-23). For pass 2's subscription, 1.5's code merged and tagged, off by default (decision 1 (b)). Nothing blocks pass 1 |
| **Consumes** | [D13](../decisions/D13-lake-formation-enforcement.md), [D26](../decisions/D26-unified-studio.md), [D40](../decisions/D40-redshift-warehouse.md); [D12](../decisions/D12-budget-ceiling.md) for the cost; 6h decisions 3 and 8, [Stage 9](stage-09-deployment-targets.md) decision 5 and Stage 19 decision 9, each read against its premises |
| **Proves** | — (no `INT-nn` row: everything runs in Sandbox, and the domain in Data Governance is reached through the doors Stage 19 measured). What it does prove: whether SageMaker Unified Studio's standard path carries a Redshift table, the namespace seen through the Glue Data Catalog, and an S3 prefix of images through publication, a data product and a subscription as it carries a Glue table; which engine and which compute the consumer needs for each; and what lineage the catalog draws for the warehouse |

*Read with [`docs/GOVERNANCE.md`](../../GOVERNANCE.md) §The catalog road and its paragraph on a data
product, the lake and a warehouse, [`docs/SMUS.md`](../../SMUS.md) §The catalog surface,
[`runbooks/catalog.md`](../runbooks/catalog.md) §A, §P, §S and §L,
[`runbooks/redshift-connection.md`](../runbooks/redshift-connection.md) §P, §J and §T, Stage 9 decision 5
and Stage 19 decision 9. The vendor sources are the 2026-11-17 rows in
[`docs/REFERENCES.md`](../../REFERENCES.md).*

---

**Objective:** exercise, by measurement, the forms SageMaker Unified Studio offers a data product beyond a
Glue table on S3: a Redshift table, the warehouse's namespace seen through the Glue Data Catalog, and an S3
prefix of unstructured files. For each form, read whether another project reaches it through a
subscription the catalog fulfils, with which engine and on which compute, and what the lineage graph shows.
Answer the user's questions of 2026-11-17 where AWS's pages leave them open, and write what the
measurements show into the catalog's runbook.

## The premises

The user's words of 2026-11-17 (19:12 UTC), in a cloud session's thread, which this stage is measured
against:

> Gostaria de explorar e entender como estruturar o uso do SMUS, da forma recomendada pela AWS,
> considerando a feature de publicação e compartilhamento de produtos de dados entre equipes.
>
> Uma aplicação SMUS, potencialmente promovida para ambiente produtivo, é disparada por um workflow, que
> possui tasks que podem transformar dados, produzindo tabelas finais que podem ser transformadas em
> Assets, e agrupada em produtos de dados. Neste contexto, o glue catalog funciona como catálogo técnico,
> e o DataZone V2 funciona como catálogo de negócio, que embute feature de lineage.
>
> Gostaria de entender e explorar como estas funcionalidades se integram ao Redshift. Entendo que o
> Redshift é um data-warehouse. Ele ingere dados em formato próprio, e disponibiliza bases estruturadas,
> acessíveis via conexão a um projeto SMUS. O compute utilizado nesta conexão pode ser do próprio ambiente
> SMUS, via Redshift-serverless. Entendo que possível, construir um pipeline que resulte numa tabela no
> gluedb do projeto e que esta tabela pode ser ingerida para ser servida pelo Redshift. É possível definir
> uma tabela no redshift como produto de dados utilizando o caminho padrão das funcionalidades
> disponibilizadas pelo Redshift? Qual é a recomendação de uso do Redshift no contexto de produtos de dados
> do SMUS?
>
> Outro aspecto que gostaria de entender são os tipos de datasets que podem ser "cadastrados" num glue
> catalog. Entendi que é possível publicar um namespace do Redshift num glue catalog. Como isso é suportado
> pelo DataZone V2, e a ferramenta de lineage? O acesso ao dado restringe ou requer um tipo de compute
> específico (redshift cluster ou redshift serverless) para permitir o acesso ao dado? Pergunto isso pq no
> caso de um arquivo parquet no S3 tenho a liberdade de escolher um compute para tratar os dados
> (spark/athena/código python puro). O glue catalog suporta dados não estruturados, como imagens?
>
> Sei que são muitas perguntas desencontradas, mas estou com dificuldades de entender como estas
> ferramentas se encaixam e qual é a proposta de organização destes componentes que a AWS recomenda,
> considerando o que o SMUS disponibiliza.

And two minutes later (19:14 UTC):

> Se para responder estas perguntas for necessário exercitar no lab, planeje um novo stage do plano para
> isso.

The same thread had read, an hour before, the portal's *Create table → Redshift table* failing in the
institution's environment with *"Cannot find default IAM role on this cluster"* on a namespace that holds
no default IAM role. The flow uploads the file and runs a `COPY` with `IAM_ROLE default` (inferred from the
error, since the portal's page on creating a table is an empty stub), and the table it makes is a Redshift
table in the namespace's own storage, in no Glue database.

The premises every item below is read against: **P1** SageMaker Unified Studio's standard path and AWS's
recommendation wherever one exists, each deviation named with its reason; **P2** a form of data counts as
a data product when another project reads it through a subscription the catalog fulfils, not when it is
published; **P3** for each form, the engine the consumer reads with and the compute behind it are measured,
with the bill; **P4** Sandbox alone: two projects of one account and the domain in Data Governance, nothing
promoted, and Production's warehouse and its datashare untouched.

## The vocabulary this stage uses

| Term | Here |
|---|---|
| a Redshift asset | a table or a view that a Redshift data source imports into a project's inventory; a managed asset, which DataZone fulfils with grants it writes itself |
| a subscription target | where DataZone writes a subscription's access in the consumer's environment: for a Glue table, the `DataLake` environment's target, whose role writes the Lake Formation grant and the resource link (`SUP-193`, `SUP-195`); for a Redshift asset, a workgroup and a database of the consumer |
| the federated catalog | a Redshift namespace registered with the Glue Data Catalog and accepted by the Lake Formation administrator. The mapping is namespace → multi-level catalog, database → catalog, schema → database, table → table (Stage 9 9.5) |
| the federated database | the other shape, built in Production: a Lake Formation-managed datashare registered by the Lake Formation administrator and mapped to a database of the Glue Data Catalog (Stage 9 decision 5) |
| data lake access | the federated catalog's switch *"Access this catalog from Iceberg compatible engines"*. With it, AWS Glue creates a managed Redshift compute that serves Athena, Amazon EMR and Spark; Redshift itself reads the catalog without it |
| an RMS catalog | a catalog of the Glue Data Catalog whose tables are stored in Redshift managed storage, reached by Iceberg engines through the Glue Iceberg REST catalog's extension endpoint |
| an S3 Object Collection | the asset type for an S3 bucket or prefix in a project, its subscription fulfilled through S3 Access Grants |
| an access grant | an entry of the account's S3 Access Grants instance: a grantee, a location with a scope, and a permission (`READ`, `WRITE` or `READWRITE`). A session gets temporary credentials for the scope with `s3control get-data-access` |
| the consumer, the producer | `test-experimentation` and `eighth-experimentation`, the two Sandbox projects |
| the consumer's workgroup | the Redshift Serverless namespace and workgroup the `RedshiftServerless` blueprint creates for `test-experimentation` under decision 1 (b), its base capacity locked at 4 RPU, for pass 2 alone |

## The user's questions, answered

Each answer separates what AWS's pages say (read 2026-11-17, [`docs/REFERENCES.md`](../../REFERENCES.md)),
what this estate has measured, and what neither settles, with the step that measures it.

**1. How does Redshift meet the Glue Data Catalog and the SageMaker Catalog?** Through separate
mechanisms, in both directions:

| Mechanism | What AWS's pages say | In this estate |
|---|---|---|
| Redshift reads the Glue Data Catalog | the auto-mounted `awsdatacatalog` database; data lake queries from Serverless are *"not billed for separately"* (the pricing page, read 2026-10-28, `PRICING.md`) | unmeasured in Sandbox: the mount runs as the namespace role, which holds no policy (5b decision 5), and Stage 19 5.1 and 5.2 read it through the project's connection |
| The namespace registered with the Glue Data Catalog | the federated catalog. Redshift reads it with no switch (*"You don't need to enable data lake access to access the federated catalogs using Amazon Redshift."*); Athena, EMR and Glue ETL read it with data lake access | not built: Stage 9 decision 5 took the datashare in Production (2026-10-22). Pass 4 |
| A Lake Formation-managed datashare | registered and mapped to a federated database, read by Redshift under Lake Formation permissions | measured in Production (Stage 9 9.5 to 9.7, read to 2026-10-30) |
| A catalog stored in Redshift managed storage | an RMS catalog: Athena reads and writes its tables, with *"DDL operations ... on Amazon Redshift managed storage tables"* not supported and no time travel; *"RMS tables are accessible only from the extension endpoint in AWS Glue Iceberg REST Catalog"* | not built; the `LakehouseCatalog` blueprint that would create one is in category 3 (`docs/SMUS.md`). Decision 3 (c) |
| A Redshift data source in a project | *"import technical metadata of database tables and views from the Amazon Redshift data warehouse"*; the assets are managed | unmeasured: Stage 19 5.3 and pass 2 |
| Redshift lineage | the system tables' queries parsed daily into lineage for the data source's connection (question 5) | the connection's sync failed on every run read, the workgroup down at its hour (`EXC-17`). Pass 3 |

**2. Can a Redshift table be a data product by the standard path?** Yes, by AWS's pages. A Redshift table or
view is a managed asset: *"These assets are called managed assets and include Lake Formation-managed AWS
Glue Data Catalog tables, AWS Glue Data Catalog views (Multi Dialect Views), and Amazon Redshift tables and
views."* A data product groups assets (*"group data assets into well-defined, self-contained packages
called data products"*), and the page that builds one names no asset type. The fulfilment, on the page for
Redshift assets: *"When a subscription to an Amazon Redshift table or view is approved, Amazon SageMaker
Unified Studio can automatically add the subscribed asset to the Amazon Redshift Serverless workgroup
created for the project, so that members of the project can query the data using the Amazon Redshift query
editor link within the project."* By where the two sides live:

| Producer and consumer | What DataZone writes |
|---|---|
| one cluster, one database | *"grants permissions directly on the source table"* |
| one cluster, two databases | *"creates a view in the target database and permissions are granted on the created view"* |
| two clusters in one account | *"creates a datashare between the source and target cluster and creates a view on top of the shared table. Permissions are granted on the view."* |
| two accounts | the same, with the producer authorizing the cross-account datashare and the consumer associating it |
| two Regions | *"Cross-Region data sharing using Amazon Redshift is not supported."*, while the page on unmanaged assets says *"Cross-region subscriptions support AWS Glue tables, AWS Glue views, Amazon Redshift tables, and Amazon Redshift views across all standard (non-opt-in) AWS Regions."* The two pages disagree; this estate is one Region |

What no page settles: whether a project that added the warehouse through *Connect to existing compute
resources*, the only way this estate admits a project to a warehouse (D40, 6h), receives a Redshift
subscription target. None exists here (Stage 19 0.6, 2026-10-28). `CreateSubscriptionTarget` takes a
`type`, a `manageAccessRole`, `authorizedPrincipals` and a `subscriptionTargetConfig` of forms, and its
reference names no Redshift type or form. Under decision 1 (b), pass 2 measures the target AWS documents,
on a workgroup the `RedshiftServerless` blueprint creates for the consumer, and leaves that case open.

**3. What does AWS recommend for Redshift in a data product?** No page read states a default form for
shared data. The concepts page puts the two stores side by side, *"Amazon SageMaker Lakehouse unifies your
data across Amazon S3 data lakes and Amazon Redshift data warehouses"*, and the facts that decide between
them are these: a Redshift asset is read in Redshift, in the consumer's own workgroup (question 2); a
Redshift table reaches Athena, EMR or Spark through the federated catalog's data lake access, on a
service-managed Redshift Serverless workgroup billed at Redshift Serverless rates (question 6); a Glue table
on S3 is read, through its Lake Formation grant, by *"Amazon Athena, Amazon Redshift, or Spark"* (the page
on Glue assets). [inferred] A product meant for consumers who choose their engine is a Glue table on S3,
Iceberg here; a Redshift table as a product fits consumers who already work in Redshift, or a copy of the
lake product kept hot for them, which is Stage 19 decision 9 (a)'s shape. Stage 19 measured the first
(verification vi, 2026-11-14); this stage measures the second end to end.

**4. What can the Glue Data Catalog hold?**

- Tables over S3: the console's wizard takes Avro, CSV, JSON, XML, Parquet and ORC, partitioned or not, and
  Glue's crawlers classify `avro`, `orc`, `parquet`, `json`, `bson`, `xml`, `ion`, `csv`, a set of log
  formats, and the tables of JDBC databases (the classifiers page).
- Open table formats: Apache Iceberg (*"Specify creating a standard AWS Glue table, or a table in Apache
  Iceberg format."*), and Delta Lake and Apache Hudi, which Glue 3.0 and later read and write.
- Views: Data Catalog views, which *"support multiple SQL query engines"* (Athena, Redshift and Glue), over
  Iceberg, Hudi and Delta Lake tables, with no UDF and no view over another view.
- Resource links to tables, the form a subscription leaves in the consumer (`SUP-195`).
- Catalogs beside the default one: S3 table buckets, the Redshift namespaces registered as federated
  catalogs, remote Iceberg REST catalogs, and external systems reached through connections (*"data
  warehouses such as Amazon Redshift, Snowflake, cloud databases such as Amazon RDS, Amazon DynamoDB,
  Oracle"*), and RMS catalogs.

**5. A namespace in the Glue Data Catalog: what do the SageMaker Catalog and its lineage make of it?** The
pages leave most of it open. A Glue data source takes a catalog: *"You can either choose an AWS Glue
catalog from the dropdown or type a catalog name. The dropdown includes the default AWS Glue catalog for the
connection account."* The only sentence on a federated catalog is on the page for Glue assets: *"Support for
cross-account sharing of assets in a federated catalog within AWS Glue Data Catalog is not supported."* No
page says that a source imports a federated catalog's tables, nor what asset type they become. Lineage for
Redshift is a property of a connection, not of the Glue Data Catalog: *"Redshift System tables will be used
to retrieve user queries and lineage is generated by parsing those queries"*, enabled by the data source's
*Import data lineage* (*"For every connection created, lineage is not automatically enabled."*), daily,
the first pull about five minutes after the switch. The project role runs the Data API's statements, which
`SageMakerStudioProjectUserRolePolicy` holds; the connection's credentials need *"`sys:operator` role to
access the data from system tables for all user queries"* and `SELECT` on all the tables; the data source
page asks for a connection authenticated by a secret ([`catalog.md`](../runbooks/catalog.md) §A, read
2026-11-17). Left out: *"External Tables"*, *"Unload / Copy"*, *"Merge / Update"*, *"Datashares"*, and
events over 16 MB; no column lineage for temporary tables or `select *`. So a table read through
`awsdatacatalog` or a datashare draws no edge from the system tables, and the lake's edge into the warehouse
would come from another emitter. Pass 4 measures the import, pass 3 the lineage.

**6. Does reading require a given compute?** For Redshift data, yes. A Redshift asset is read in Redshift
(question 2). Read by another engine through the federated catalog or an RMS catalog, Redshift compute
stands behind it, in AWS Glue's pricing page: *"a service-managed Amazon Redshift Serverless workgroup is
used for compute resources"*, *"you are charged for the compute resources you use based on standard Amazon
Redshift Serverless rates"*, *"The Amazon Redshift Serverless managed workgroup is used to filter table
results"*, and *"There are no separate charges to query tables stored in Amazon Redshift using Amazon
Redshift."* The Lake Formation pages disagree on its shape: *"AWS Glue creates a managed Amazon Redshift
cluster"* on the federated catalog's page, *"an Amazon Redshift managed serverless-workgroup"* on the RMS
catalog's. No page names the account it runs in or its base capacity. A Glue table on S3 leaves the engine
to the consumer: Athena, Spark on Glue or EMR, Redshift through `awsdatacatalog`, each under the table's
Lake Formation grant. In this estate a project role holds no S3 on the lake's registered prefixes (D13), so
plain Python reads a subscribed table through an engine Lake Formation vends to, Athena from a notebook
among them, never by reading the files with boto3; a project's own database keeps its files in the project's
path, which the role reads. Decision 3 (b) measures the managed workgroup.

**7. Does the Glue Data Catalog hold unstructured data such as images?** No: a Glue table describes rows
and columns, and the built-in classifiers name structured and semi-structured formats and logs, no image
format. SageMaker Unified Studio's form for such files is the S3 Object Collection: *"For S3 data in
projects, SageMaker Catalog supports the creation of an asset type of S3 Object Collection for an Amazon S3
bucket or S3 prefix in the project."*, curated with *"business names, descriptions, README, glossary terms,
and metadata forms"*. Its subscription: *"Amazon SageMaker Unified Studio grants access to subscribed assets
using Amazon S3 Access Grants."*, read-only or read and write at the publisher's choice, and after a
revocation *"a project member may still get Amazon S3 Access Grants credentials for up to 5 minutes, and
credentials can be used for 15 minutes."* The page names neither the grantee nor how the subscriber reads.
The images' attributes belong in a table beside them, and Amazon S3 Metadata keeps a bucket's object
metadata in *"read-only, fully managed Apache Iceberg tables"* that Athena, EMR and Redshift query once the
table bucket is integrated with the Glue Data Catalog. Pass 5 measures a product of an S3 Object Collection
and a table of its images' attributes; S3 Metadata is read, not built.

**8. How does AWS organize the pieces?** The pages give the frame and leave the layout to the organization:
*"whether it's creating a single Amazon SageMaker unified domain for your enterprise or multiple domains for
different business units"*; domain units *"organize your assets and other domain entities under specific
business units and teams"*, with authorization policies on project profiles per unit; *"Every asset that
lives in the business data catalog has an owner project (also known as the producer project)"*, and *"A
subscriber (also known as a consumer project) is able to make a request to the owner project to gain access
to the asset."* No page read prescribes a number of domains, a project per team, or the form of shared data,
and no AWS post of 2025 or 2026 read for this stage does. This estate's answer to each is recorded
elsewhere: one domain in Data Governance (D26), a domain unit per business data domain as the institutional
pattern ([`GOVERNANCE.md`](../../GOVERNANCE.md), 6f step 9), a SageMaker application as the deployable unit
(D41), a Glue table on S3 as the product promoted to Production (Stage 19), and the warehouse admitted to a
project by hand (D40, 6h).

## The plan and the estate against the premises

What each item holds today, with its measurement or page, and what this stage does to it: keep, amend, or a
decision for the user, named by its number in Decisions due. Read from `main` `7816fbe` on 2026-11-17.

| Item | Today | Under the premises |
|---|---|---|
| D40 | one warehouse per account by hand; the `RedshiftServerless` and `LakehouseCatalog` blueprints disabled, the first for its default of 128 base RPUs and a workgroup per project | **amend for one sitting**: decision 1 (b) enables the blueprint for `test-experimentation`, its base capacity locked at 4 RPU, and removes it at 2.9; D40's file records the sitting at 6.2 |
| D13 | execution roles hold no S3 on the lake's registered prefixes | **keep**: pass 5's prefix is in the producer's project path, which Lake Formation does not register |
| D26 | one domain, in Data Governance | **keep** |
| 6h decision 3 | the connection's `lineageSync`, off since 2026-11-19; its 39 daily runs at 03:43 UTC before it all failed | **keep** as the user's; pass 3 reads a lineage run with the workgroup up and leaves the setting as it found it |
| 6h decision 8 | how a second project is admitted to the warehouse; taken 2026-11-17 as (a), the tag `for-use-with-all-datazone-projects=true`, its switch written 2026-11-18 and off | **keep** as taken: decision 1 (b) admits no second project to the warehouse, so this stage turns the switch on nowhere |
| Stage 9 decision 5 | Production's namespace reaches Lake Formation as a Lake Formation-managed datashare mapped to a federated database; data lake access refused for the managed cluster against `DenyRedshiftProvisionedClusters` and D12; 9.5a's reading owed only if the federated catalog comes back | **keep** in Production. **Decision 3 (b)**: the federated catalog comes back in Sandbox for one sitting, and 9.5a's reading is taken there |
| Stage 19 decision 9 | (a), taken 2026-10-31: the read in place through `awsdatacatalog`, 5.3's Redshift asset published and never subscribed; (b), the subscription with a target, *"read as a second half once a target's shape is priced"* | **keep** (a) for Stage 19; pass 2 here is (b)'s second half, under decision 1 |
| [`catalog.md`](../runbooks/catalog.md) | §A: a Redshift source unmeasured; §P: a product of several items unread; §S: no Redshift target, fulfilment from the pages; no S3 Object Collection | **amend**: the 2026-11-17 readings at 1.1, the measurements at 6.1 |
| [`docs/SMUS.md`](../../SMUS.md), "Existing buckets as catalog assets" | the S3 Object Collection, *"No stage uses it"* | **amend** at 6.2 |
| [`docs/SMUS.md`](../../SMUS.md), the `RedshiftServerless` row | category 3, *Never*: a 128-RPU workgroup one click from every member (D26, D40) | **amend** at 6.2 with the sitting's readings; the category stays 3 |
| [`docs/GOVERNANCE.md`](../../GOVERNANCE.md) | a data product, the lake and a warehouse in one paragraph; a Redshift `GRANT` as the fourth permission system | **amend** at 6.2, with what a subscription writes in each system |
| `./aws/warehouse.py` | `WH-9` fails while a connection's lineage sync is on or its database is not `sandbox`; `WH-12` and `WH-14` judge the themed schemas' grants | **read** after passes 2 and 3, **amend** at 6.3 for a subscription's datashare and a lineage run the stage chose |
| `./aws/studio.py` | `US-3` admits decision 5's category 1 and fails on `RedshiftServerless` with its own message | **read**: red while 1.5's variables are on, green after 2.9; no change |
| `./aws/catalog.py` | `CT-17` explains every grant on a project's listed Glue table; nothing reads S3 Access Grants | **amend** at 6.3: the grants of an S3 Object Collection's subscription, explained by it |

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, run only after the user authorizes that action in chat, the other sessions on the laptop told first |
| **[user]** | the portal, a space, the console, and every decision |

## 0. What is already measured

- **0.1 The Sandbox warehouse** ([5b](stage-05b-redshift-serverless.md), applied 2026-09-20): the
  namespace `awsds-sandbox-warehouse` and its workgroup at `base_capacity = 4`, a usage limit with
  `breach_action = deactivate`, 0.36 USD per RPU-hour, so 1.44 per query-hour at 4 RPU and nothing idle
  ([`docs/PRICING.md`](../../PRICING.md) §5). The free trial absorbs the bill to 2026-12-19 (287.51 of
  300.00 USD left on 2026-10-25). The namespace's default IAM role is `awsds-sandbox-warehouse-exec`, which
  holds no policy (5b decision 5, `WH-1b`).
- **0.2 The project's connection** ([6h](stage-06h-redshift-connection.md) passes 0 to 2,
  [`redshift-connection.md`](../runbooks/redshift-connection.md) §P): `eighth-experimentation` reaches the
  workgroup with IAM credentials through a per-project access role, as the database user
  `IAMR:datazone_usr_role_<project>_<env>`; its role holds `USAGE, CREATE` on `lab` in `sandbox`, and the
  project wrote `lab.hello` from the Query editor on 2026-10-10. The connection names `sandbox` since
  2026-11-19 (6h decision 3). The namespace holds `dev`, `sandbox` and `warehouse`. Its `lineageSync` is
  off since the same day; every run before it failed while the workgroup was down (`EXC-17`).
  `test-experimentation` is in no map: not admitted.
- **0.3 The catalog road for a Glue table** (Stage 19 verifications vi to viii, 2026-11-14; `SUP-195`): a
  project's source imports a table of its database, the asset is published and packaged in a product of
  one item, the consumer's request is approved, the owner's role grants `SELECT` under the consumer's
  project context and the consumer's role creates the resource link, `COMPLETED` 65 s after the request; the
  consumer read it from the query editor on Athena in 1.9 s and from a Glue Spark session.
- **0.4 Production's namespace in Lake Formation** (Stage 9 9.5 to 9.7, read to 2026-10-30): a Lake
  Formation-managed datashare, `USAGE ON DATASHARE … VIA DATA CATALOG`, registered by Data Governance's
  Lake Formation administrator and mapped to a federated database, read by Redshift.
- **0.5 No Redshift subscription target in any environment, and no federated catalog in any account**
  (Stage 19 0.6, 2026-10-28).
- **0.6 S3 Access Grants** ([`docs/SMUS.md`](../../SMUS.md), 2026-08-23): at a project's first
  provisioning SageMaker Unified Studio created the account's instance `default` and one location per
  project, its scope the project's prefix and its role the project role, with
  `enableS3AccessGrantsForTools = true` on the Tooling environment and no grant. One grant to
  `DataScientistAccess` lets a laptop vend project-role credentials for a project's prefix
  (`s3-read-write/`, [Stage 16](stage-16-sandbox-lake.md)). Requests bill 0.03 USD per 1,000.
- **0.7 Lineage in the catalog** (Stage 19 verification v, 2026-11-14): a Glue job's OpenLineage events,
  posted through Sandbox's `datazone` endpoint, drawn on the asset's *Lineage* tab with the catalog's own
  edges. No Redshift lineage has been read (`EXC-17`); the mechanisms are
  [`catalog.md`](../runbooks/catalog.md) §L.

## To execute

### 1. With nothing up: the readings, the decisions, the inputs

- **1.1 [Claude] The pages read 2026-11-17**, written the same day into
  [`docs/REFERENCES.md`](../../REFERENCES.md), "The user's questions, answered" and
  [`catalog.md`](../runbooks/catalog.md) §S. Done at writing.
- **1.2 [user] Decisions 1 to 3.** Taken 2026-11-17: 1 (b), 2 (a), 3 (b).
- **1.3 [Claude] The shapes the sittings write, read-only from the laptop** as `awsds-infra-sandbox-1`
  (`InfrastructureAccess`, `Sandbox Account 1`), a contributor of both Sandbox projects since 2026-10-15:
  - the managed asset types' forms, `datazone get-asset-type` on the Redshift table, Redshift view and S3
    Object Collection types, and the domain's roster against the 24 types of 2026-10-28;
  - the consumer's environments and their targets, `datazone list-environments` and
    `list-subscription-targets` on `test-experimentation`: the Glue target's `type`,
    `subscriptionTargetConfig` and `authorizedPrincipals`, beside which 2.4 reads the Redshift target;
  - the `RedshiftServerless` blueprint, `datazone get-environment-blueprint` and its template from
    `templateUrl`: every parameter with its default and `AllowedValues`, the base and maximum capacity's
    among them, and the console's enable wizard's fields ([`docs/SMUS.md`](../../SMUS.md)'s checklist for
    promoting a blueprint, steps 3 and 4); the adminguide's key-permissions page for the Redshift
    statements the project CMK lacks. If no parameter holds the base capacity at 4 RPU, decision 1 returns
    to the user before 1.5;
  - the producer's connections, `datazone list-connections` on `eighth-experimentation`, the Redshift one's
    `lineageSync` and its authentication;
  - the Access Grants instance, its locations and its grants, `s3control get-access-grants-instance`,
    `list-access-grants-locations` and `list-access-grants`;
  - the commands that register a namespace and create the federated catalog, from Lake Formation's
    `create-ns-catalog` and Redshift's namespace-registration pages, and the data transfer role's trust
    and policy from `redshift-ns-prereqs`.
  The commands of passes 2 to 5 are written from these readings before the sitting, after each pass's steps.
  **Done 2026-11-18**, 00:39 to 00:55 UTC, read-only, the asset types as `awsds-infra-data`, since
  `get-asset-type` refuses Sandbox's caller (the log; `SUP-377`, `SUP-378`). The readings 1.5
  and the sittings turn on:
  - the template `DataZone-Amazon-SageMaker-RedshiftServerlessDefault-prod-20250515` takes
    `redshiftBaseCapacity` and `redshiftMaxCapacity` as Numbers with no `AllowedValues`; a base other than
    its 128 becomes the workgroup's `BaseCapacity` and drops the price-performance target, so a locked
    override of 4 holds the floor and decision 1 stands. The blueprint's user parameter defaults
    `redshiftMaxCapacity` to 512, and no AWS page states whether a maximum may equal the base;
  - the namespace's default and only IAM role is the project role, and its key the template's `kmsKeyArn`
    when DataZone passes one, which 2.4 reads in the stack's parameters; the workgroup takes the `Tooling`
    stack's subnets and security group; every parameter without a default is DataZone's, none a user
    parameter;
  - the key-permissions page names one Redshift statement, `RedshiftCreateGrantKmsPermissions`, and the
    provisioning role's managed policy (v86) allows `kms:CreateGrant` through no Redshift endpoint;
  - that policy's `RssMng` allows `UpdateWorkgroup` on workgroups tagged `AmazonDataZoneProject`, which the
    root's `DenyRedshiftCostGuardTamperingExceptInfrastructure` denies to every role but
    `InfrastructureAccess`: a create or an *Update project* that calls it fails, read in the trail at 2.4;
  - `test-experimentation`'s only data target is its `DataLake` environment's `GlueSubscriptionTargetType`,
    authorized to `abac:CURRENT_PROJECT`, its manage-access role the project role; no Redshift target;
  - the producer's Redshift connection authenticates by IAM through its access role, database `dev`, its
    `lineageSync` on and failing every day;
  - the Access Grants instance holds four locations, the lake's and one for each of
    `eighth-experimentation`, `test-experimentation` and `app-etl-dev`, and five grants, none from a
    subscription;
  - the console's enable wizard (the checklist's step 4) is unread: the user's act before 2.4.
- **1.4 [Claude] The images' generator**, below, run by the user in pass 5; it writes PNG files with the
  standard library alone, so nothing is installed and no third-party picture is used:

  ```python
  import pathlib, random, struct, zlib

  def png(width, height, rgb):
      """Return the bytes of a PNG of one colour."""
      raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
      def chunk(kind, data):
          body = kind + data
          return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
      header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
      return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
              + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

  out = pathlib.Path("stage21-images")
  out.mkdir(exist_ok=True)
  random.seed(21)
  rows = []
  for i in range(20):
      rgb = [random.randrange(256) for _ in range(3)]
      data = png(64, 64, rgb)
      name = f"img-{i:02d}.png"
      (out / name).write_bytes(data)
      rows.append(f"('{name}', '{'warm' if rgb[0] > rgb[2] else 'cold'}', 64, 64, {len(data)})")
  print("SELECT * FROM (VALUES\n  " + ",\n  ".join(rows)
        + "\n) AS t (object_key, tone, width, height, size_bytes)")
  ```
- **1.5 [Claude] The code of decision 1 (b), off by default**, written from 1.3's readings in the order of
  [`docs/SMUS.md`](../../SMUS.md)'s checklist for promoting a blueprint, steps 1 to 6, each change behind a
  variable that defaults to off. In `sagemaker-prereqs`, at a new tag read from the remote at tagging:
  `RedshiftServerless` among the configured blueprints, and the project CMK's Redshift `CreateGrant`
  statements. In `data-governance/governance/`: an `ON_DEMAND` `RedshiftServerless` configuration in the
  `experimentation` profile, its base capacity and, if the template has one, its maximum locked at 4 RPU by
  parameter overrides that are not editable. `sandbox/sagemaker/` moves to the tag. Each slice is planned
  `No changes` with the variables off. `US-3`'s allow-list stays as it is, so the check reads red, with
  its own message, while the variables are on. **Written 2026-11-18**, each half behind a
  `redshift_serverless_enabled` that defaults to false:
  - `sagemaker-prereqs`: `RedshiftServerless` joins the configured set beside `var.blueprint_names`, so
    its roster guard and its grant follow; the project key gains `RedshiftCreateGrantKmsPermissions`; the
    manage-access role gains AWS's `service-role/AmazonDataZoneRedshiftManageAccessRolePolicy` (v5), which
    AWS's SMUS-IaC sample attaches and which holds the datashare authorization the other two policies lack;
  - `data-governance/governance/`: `experimentation` gains the `ON_DEMAND` configuration at order 14,
    `redshiftBaseCapacity` and `redshiftMaxCapacity` locked at `"4"`, and the profile's precondition
    admits the blueprint while the switch is on.

  Planned with the switches off, `sandbox/sagemaker/` against the module by its local path, then reverted
  to `?ref=sagemaker-prereqs-v0.11.0` and re-initialised: *"No changes."* in both slices, 43 and 23
  no-ops. With them on, unsaved: 3 to add and 1 to change in Sandbox (the configuration, its grant, the
  policy attachment; the key's policy), 1 to change in Data Governance (the profile). Tagged
  `sagemaker-prereqs-v0.12.0` the same night, after `git ls-remote` read `v0.11.0` as origin's newest, and
  `sandbox/sagemaker/` moved to it with its switch, Recipe B's second commit: *"No changes."* in both slices
  from that tree.

### 2. A Redshift table as a data product

Inside a Sandbox sitting (`make hub-up`, then `make up ENV=sandbox ONLY=egress`), the warehouse's compute
raised with `make up ENV=sandbox GROUPS=redshift`, spaces in both projects. When Stage 19's pass 5 runs in
the same sitting, its 5.2 copy and 5.3 asset are the ones 2.1 and 2.2 read, and its 5.4 waits for this
pass's end.

- **2.1 [user] The tables, in `eighth-experimentation`'s Query editor on the warehouse, database
  `sandbox`**: `lab.trades_hot` (Stage 19 5.2's copy, or a `CREATE TABLE ... AS` over a `VALUES` list of a
  few rows if 5.2 has not run), a view `lab.trades_hot_by_desk` over it, and `lab.trades_hot_daily`, a
  `CREATE TABLE ... AS` from `lab.trades_hot` for pass 3. **[Claude] reads** each table's owner from
  `SVV_TABLE_INFO` and `pg_tables`.
- **2.2 [user] A Redshift data source** on the project's Redshift connection, database `sandbox`, schema
  `lab`, the include rule `trades_hot*`, *Publish on import* off, no schedule, one run (Stage 19 5.3).
  **[Claude] reads** each asset's type and forms (`get-asset`), its `sourceIdentifier`, and the source's
  run.
- **2.3 [user] Publish the table and the view, and a data product of both**, with the `classification` form
  (Stage 19 decision 4). **[Claude] reads** the listings and `CT-18`.
- **2.4 The consumer's workgroup, under decision 1 (b).** **[Claude⚡]** On the user's word, the other
  sessions told first: 1.5's variables on, `sandbox/sagemaker/` then `data-governance/governance/` applied
  and re-planned `No changes`; `datazone get-project-profile` read for the configuration and its locked
  capacity. **[user]** A member of `test-experimentation` adds the Redshift Serverless compute on demand in
  the portal. **[Claude] reads** the environment and its stack; the namespace and the workgroup, their base
  and maximum capacity, key, subnets and security group; the connection the blueprint writes; and the
  Redshift subscription target the environment carries, its `type`, forms and `authorizedPrincipals`, beside
  the Glue target 1.3 read. A workgroup above 4 base RPUs is removed at once by 2.9's steps, and decision 1
  returns to the user; no target, or a refusal at the create, is verification iii's answer, and 2.5 to 2.7
  do not run.
- **2.5 [user] The consumer requests the product and the producer's owner approves.** **[Claude] reads**
  the subscription, a grant per asset and their times, and on both workgroups as their admins what DataZone
  wrote across two namespaces: by the pages, a datashare on the warehouse's namespace carrying the table and
  the view, the consumer's namespace as its consumer, a database created from it and a view on top in the
  consumer's workgroup, with `SVV_DATASHARES`, `SVV_DATASHARE_OBJECTS`, `SVV_DATASHARE_CONSUMERS`,
  `SVV_RELATION_PRIVILEGES` and `SYS_QUERY_HISTORY` for the statements and the users that ran them.
- **2.6 [user] The consumer reads through the subscription**: `SELECT` on what 2.5 found, from the Query
  editor and from a notebook through the connection the blueprint wrote; `lab.trades_hot_daily`, never
  subscribed, absent or refused. **[Claude] reads** the refusal's wording and both workgroups'
  `ComputeSeconds`.
- **2.7 [user] Revoke the subscription.** **[Claude] reads** what the revocation removes on each workgroup,
  the view, the datashare's objects or the datashare, and when, against
  [`catalog.md`](../runbooks/catalog.md) §S's revocation.
- **2.8 [user] The portal's *Create table → Redshift table*** in `eighth-experimentation`, with a CSV of a
  few rows. **[Claude] reads** the bucket and the prefix the portal uploads to, the `COPY` it runs and its
  refusal: the namespace's default role holds no policy (0.1), so the expected refusal is S3's, not the
  missing default role the institution's environment met. Nothing is granted to the role (5b decision 5).
- **2.9 The consumer's workgroup removed**, after 2.7. **[user]** The compute removed from
  `test-experimentation` in the portal. **[Claude] reads** the environment, its stack, the workgroup and the
  namespace absent. **[Claude⚡]** On the user's word, 1.5's variables off, `data-governance/governance/`
  then `sandbox/sagemaker/` applied, the reverse of 2.4's order, and re-planned `No changes`; `US-3` read
  green.

**The commands of pass 2**, written from 1.3's readings. A ⚡ marks a write Claude runs on the user's word
alone; every other command of Claude's is a read. The placeholders in angle brackets are the sitting's
values; the workgroup's and namespace's names assume the blueprint's defaults reach the stack, whose
parameters 2.4 reads. The first block sets the variables the commands of passes 2 to 5 read.

```bash
# Every block: the infrastructure user, InfrastructureAccess, Sandbox Account 1 unless G is named.
S=awsds-infra-sandbox-1 G=awsds-infra-data D=dzd-d8yrvx1ko7im6o P=avhvbqn37ty7m8 C=4gqfau9xuo6e4w
A=$(aws sts get-caller-identity --query Account --output text --profile $S)
SECRET=$(aws redshift-serverless get-namespace --namespace-name awsds-sandbox-warehouse \
  --query namespace.adminPasswordSecretArn --output text --profile $S)
q() { aws redshift-data execute-statement --workgroup-name awsds-sandbox-warehouse --database sandbox \
  --secret-arn "$SECRET" --sql "$1" --query Id --output text --profile $S; }
# A statement's rows: describe-statement --id until FINISHED, then get-statement-result --id. No waiter.
```

```sql
-- 2.1 [user], the Query editor on awsds-sandbox-warehouse, database sandbox. The table only where Stage 19's
-- 5.2 has not made it, in trades_notional's columns: the stage's CTAS over VALUES, as a create and an insert.
CREATE TABLE lab.trades_hot (trade_date DATE, desk VARCHAR(32), instrument VARCHAR(32),
  quantity DOUBLE PRECISION, price DOUBLE PRECISION, notional DOUBLE PRECISION);
INSERT INTO lab.trades_hot VALUES ('2026-11-02', 'rates', 'UST10Y', 10, 98.5, 985),
  ('2026-11-02', 'fx', 'EURUSD', 1000, 1.08, 1080), ('2026-11-03', 'rates', 'UST2Y', 20, 99.1, 1982);
CREATE VIEW lab.trades_hot_by_desk AS
  SELECT desk, COUNT(*) AS trades, SUM(notional) AS notional FROM lab.trades_hot GROUP BY desk;
CREATE TABLE lab.trades_hot_daily AS
  SELECT trade_date, SUM(notional) AS notional FROM lab.trades_hot GROUP BY trade_date;
```

```bash
# 2.1 the owners
q "select schemaname, tablename, tableowner from pg_tables where schemaname = 'lab'"
q "select schemaname, viewname, viewowner from pg_views where schemaname = 'lab'"
q "select \"schema\", \"table\", tbl_rows from svv_table_info where \"schema\" = 'lab'"
# 2.2 the source, its run, the assets (type, forms, AssetCommonDetailsForm's sourceIdentifier)
aws datazone list-data-sources --domain-identifier $D --project-identifier $P --type REDSHIFT --profile $S
aws datazone list-data-source-runs --domain-identifier $D --data-source-identifier <source> --profile $S
aws datazone list-data-source-run-activities --domain-identifier $D --identifier <run> --profile $S
aws datazone search --domain-identifier $D --owning-project-identifier $P --search-scope ASSET \
  --search-text trades_hot --profile $S
aws datazone get-asset --domain-identifier $D --identifier <asset> --profile $S
# 2.3 the listings, the product, CT-18
aws datazone search-listings --domain-identifier $D --search-text trades_hot --profile $S
aws datazone search --domain-identifier $D --owning-project-identifier $P --search-scope DATA_PRODUCT \
  --profile $S
./aws/catalog.py
# 2.4 ⚡ the other sessions told first, sandbox/sagemaker/ at sagemaker-prereqs-v0.12.0; this order on
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/sagemaker plan -input=false \
  -var redshift_serverless_enabled=true -out="$HOME/tmp/s21-sagemaker-on.tfplan"    # 3 to add, 1 to change
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/sagemaker apply -input=false \
  "$HOME/tmp/s21-sagemaker-on.tfplan"
AWS_PROFILE=$G terraform -chdir=terraform-live/data-governance/governance plan -input=false \
  -var redshift_serverless_enabled=true -out="$HOME/tmp/s21-governance-on.tfplan"   # 0 to add, 1 to change
AWS_PROFILE=$G terraform -chdir=terraform-live/data-governance/governance apply -input=false \
  "$HOME/tmp/s21-governance-on.tfplan"
# each slice re-planned with the same -var: No changes
aws datazone get-project-profile --domain-identifier $D --identifier dh60xbal05q64w --profile $G \
  --query "environmentConfigurations[?name=='RedshiftServerless']"
# [user] the Redshift Serverless compute added to test-experimentation in the portal. Where the entry is
# greyed (docs/SMUS.md's checklist, step 7), the user runs the call it would send:
AWS_PROFILE=awsds-infra-sandbox-1 aws datazone create-environment --domain-identifier dzd-d8yrvx1ko7im6o \
  --project-identifier 4gqfau9xuo6e4w --environment-configuration-id <get-project-profile's id> \
  --environment-blueprint-identifier dlyaabb17hano0 --name redshift-serverless --region us-west-2
# 2.4 the environment, its stack, the compute, the connection, the target
aws datazone list-environments --domain-identifier $D --project-identifier $C --profile $S
aws datazone get-environment --domain-identifier $D --identifier <env> --profile $S
aws cloudformation describe-stacks --stack-name <the stack get-environment names> --profile $S \
  --query 'Stacks[0].{status: StackStatus, parameters: Parameters}'
aws redshift-serverless get-workgroup --workgroup-name redshift-serverless-workgroup-<env> --profile $S \
  --query 'workgroup.{base: baseCapacity, max: maxCapacity, target: pricePerformanceTarget,
    subnets: subnetIds, groups: securityGroupIds}'
aws redshift-serverless get-namespace --namespace-name redshift-serverless-namespace-<env> --profile $S \
  --query 'namespace.{key: kmsKeyId, role: defaultIamRoleArn, roles: iamRoles,
    secret: adminPasswordSecretArn, db: dbName}'
aws datazone list-connections --domain-identifier $D --project-identifier $C --type REDSHIFT --profile $S
aws datazone list-subscription-targets --domain-identifier $D --environment-identifier <env> --profile $S
aws datazone get-subscription-target --domain-identifier $D --environment-identifier <env> \
  --identifier <target> --profile $S                      # the type, which the list reads null
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateWorkgroup \
  --start-time <the create> --profile $S   # a refusal by DenyRedshiftCostGuardTamperingExceptInfrastructure
# 2.5 the subscription, its grants, and what DataZone wrote in each namespace, as each admin
aws datazone list-subscriptions --domain-identifier $D --owning-project-id $C --profile $S
aws datazone list-subscription-grants --domain-identifier $D --subscription-id <subscription> --profile $S
q "select * from svv_datashares"
q "select * from svv_datashare_objects"
q "select * from svv_datashare_consumers"
q "select user_id, query_id, start_time, query_text from sys_query_history
   where start_time > '<the approval>' order by start_time"
SECRET2=$(aws redshift-serverless get-namespace --namespace-name redshift-serverless-namespace-<env> \
  --query namespace.adminPasswordSecretArn --output text --profile $S)
q2() { aws redshift-data execute-statement --workgroup-name redshift-serverless-workgroup-<env> \
  --database dev --secret-arn "$SECRET2" --sql "$1" --query Id --output text --profile $S; }
q2 "select * from svv_redshift_databases"
q2 "select * from svv_datashares"
q2 "select * from svv_relation_privileges where namespace_name = 'project'"
q2 "select user_id, query_id, start_time, query_text from sys_query_history
    where start_time > '<the approval>' order by start_time"
# 2.6 both workgroups' compute; the metric lands per half hour
aws cloudwatch get-metric-statistics --namespace AWS/Redshift-Serverless --metric-name ComputeSeconds \
  --dimensions Name=Workgroup,Value=<awsds-sandbox-warehouse, then the consumer's> \
  --start-time <the sitting's start> --end-time <now> --period 1800 --statistics Sum --profile $S
# 2.7 2.5's reads again after the revocation, each with its time
# 2.8 the portal's load: the COPY's text names the bucket and the prefix
q "select query_id, status, error_message, start_time, query_text from sys_query_history
   where query_type = 'COPY' and start_time > '<the create>'"
q "select * from sys_load_error_detail where start_time > '<the create>'"
# 2.9 [user] the compute removed in the portal; 2.4's reads find the environment, stack and compute absent.
# ⚡ The reverse of 2.4's order, each slice re-planned without the -var to No changes; ./aws/studio.py's US-3
AWS_PROFILE=$G terraform -chdir=terraform-live/data-governance/governance plan -input=false \
  -out="$HOME/tmp/s21-governance-off.tfplan"                                        # 0 to add, 1 to change
AWS_PROFILE=$G terraform -chdir=terraform-live/data-governance/governance apply -input=false \
  "$HOME/tmp/s21-governance-off.tfplan"
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/sagemaker plan -input=false \
  -out="$HOME/tmp/s21-sagemaker-off.tfplan"                         # 0 to add, 1 to change, 3 to destroy
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/sagemaker apply -input=false \
  "$HOME/tmp/s21-sagemaker-off.tfplan"
```

### 3. Lineage from the warehouse

In the same sitting, under decision 2.

- **3.1 [Claude⚡] The credentials**, on the user's word, under decision 2 (a): a database user
  `lineage_reader`, its password in a Sandbox secret, granted `sys:operator` and `SELECT` on `lab`'s tables
  by the admin; a member adds a second Redshift connection to `eighth-experimentation` with *AWS Secrets
  Manager*.
- **3.2 [user] The data source with *Import data lineage***, on the connection 3.1 chose, over `lab`; the
  switch time recorded, the first pull about five minutes after it. **[Claude] reads** the connection's
  `lineageSync` and the run's outcome (*"The job run fails if none of the queries are successfully
  processed; partially succeeds if some queries are successfully processed"*).
- **3.3 [user] The statements whose lineage is read**, between the switch and the pull: a
  `CREATE TABLE ... AS` and an `INSERT ... SELECT` inside `lab`, which the page supports; an `UPDATE` and
  a `MERGE`, which it leaves out; and, if Stage 19 5.2's read in place works, a `CREATE TABLE ... AS` from
  `awsdatacatalog`, an external table to the parser.
- **3.4 [user] The graph** on the assets' *Lineage* tab. **[Claude] reads** the lineage nodes and their
  `sourceIdentifier` against the Redshift assets', and which statements left edges.
- **3.5 [Claude⚡] The credentials removed** at the pass's end: the second connection, the user and the
  secret; the data source's lineage switched off. 6h decision 3's setting on the
  project's connection is left as found.

**The commands of pass 3**, in a shell that ran pass 2's first block:

```bash
# 3.1 ⚡ the password generated and never printed; the user created from its MD5 hash (md5sum on Linux)
PW=$(aws secretsmanager get-random-password --password-length 32 --exclude-punctuation \
  --require-each-included-type --query RandomPassword --output text --profile $S)
q "CREATE USER lineage_reader PASSWORD 'md5$(printf '%s%s' "$PW" lineage_reader | md5)'"
q "GRANT ROLE \"sys:operator\" TO lineage_reader"
q "GRANT USAGE ON SCHEMA lab TO lineage_reader"
q "GRANT SELECT ON ALL TABLES IN SCHEMA lab TO lineage_reader"
aws secretsmanager create-secret --name awsds-sandbox-stage21-lineage-reader \
  --secret-string "$(jq -cn --arg p "$PW" '{username: "lineage_reader", password: $p}')" \
  --tags Key=AmazonDataZoneProject,Value=$P --profile $S     # the tag AllowGetSecretForRedShift reads
unset PW
# [user] the second Redshift connection with AWS Secrets Manager and that secret; 3.2's source on it
# 3.2 the connection's lineage job and its run
aws datazone list-connections --domain-identifier $D --project-identifier $P --type REDSHIFT --profile $S
aws datazone get-connection --domain-identifier $D --identifier <connection> --profile $S \
  --query props.redshiftProperties.lineageSync
aws datazone list-job-runs --domain-identifier $D --job-identifier <lineageJobId> --profile $S
aws datazone get-job-run --domain-identifier $D --identifier <run> --profile $S
# 3.4 the nodes: their ids in Data Governance's trail (SUP-191), then each node and its history
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateLineageNode \
  --start-time <the pull> --profile $G
aws datazone get-lineage-node --domain-identifier $D --identifier <node> --profile $S
aws datazone list-lineage-node-history --domain-identifier $D --identifier <node> --profile $S
# 3.5 ⚡ after the user removes the second connection and switches the source's lineage off
q "REVOKE ROLE \"sys:operator\" FROM lineage_reader"
q "REVOKE ALL ON ALL TABLES IN SCHEMA lab FROM lineage_reader"
q "REVOKE USAGE ON SCHEMA lab FROM lineage_reader"
q "DROP USER lineage_reader"
aws secretsmanager delete-secret --secret-id awsds-sandbox-stage21-lineage-reader \
  --recovery-window-in-days 7 --profile $S
```

```sql
-- 3.3 [user], between the switch and the pull: two statements the page supports, two it leaves out
CREATE TABLE lab.trades_hot_by_day AS
  SELECT trade_date, desk, SUM(notional) AS notional FROM lab.trades_hot GROUP BY trade_date, desk;
INSERT INTO lab.trades_hot_daily SELECT trade_date, SUM(notional) FROM lab.trades_hot GROUP BY trade_date;
UPDATE lab.trades_hot_daily SET notional = notional WHERE trade_date = '2026-11-02';
MERGE INTO lab.trades_hot_daily USING (SELECT trade_date, SUM(notional) AS notional FROM lab.trades_hot
  GROUP BY trade_date) AS s ON trades_hot_daily.trade_date = s.trade_date
  WHEN MATCHED THEN UPDATE SET notional = s.notional
  WHEN NOT MATCHED THEN INSERT VALUES (s.trade_date, s.notional);
-- only where Stage 19's 5.2 read in place works
CREATE TABLE lab.trades_from_lake AS SELECT * FROM awsdatacatalog.<project database>.trades_notional;
```

### 4. The namespace in the Glue Data Catalog

In the same sitting or a second warehouse sitting, under decision 3. Recipe D's order (Stage 9 9.5): each
object created alone and read back for `IAMAllowedPrincipals` before anything is created inside it.

- **4.1 [Claude⚡] Register the Sandbox namespace and create the federated catalog**, on the user's word,
  with 1.3's commands: the registration as the namespace's owner, the acceptance and the catalog as
  Sandbox's Lake Formation administrator (`InfrastructureAccess`, `sandbox/data/`). **[Claude] reads** the
  catalog and its levels, `<catalog>/sandbox` → `lab` → `trades_hot`, and its default permissions.
- **4.2 [Claude⚡] Lake Formation grants** of `DESCRIBE` and `SELECT` on `lab.trades_hot` in the federated
  catalog to `eighth-experimentation`'s project role.
- **4.3 [user] Redshift reads the table through the federated catalog** from the producer's Query editor,
  by the name the query page gives. **[Claude] reads** the session's identity and `ComputeSeconds`.
- **4.4 [user] A Glue data source over the federated catalog** in `eighth-experimentation`, the catalog
  typed, the database `lab`; one run. **[Claude] reads** whether it imports, the asset type and the
  `sourceIdentifier`. If it imports: publish, the consumer's request and approval, and what DataZone
  writes, a Lake Formation grant and a resource link in one account or a refusal.
- **4.5 [Claude⚡] Data lake access**, under decision 3 (b): the data transfer role written in
  `sandbox/warehouse/` on 2026-11-18 ([pull request #323](https://github.com/felipenoris/AWS-DataScience/pull/323)): `data_transfer_role_enabled`,
  off by default, creates `awsds-sandbox-warehouse-data-transfer`, whose ARN is the output
  `data_transfer_role_arn`; applied for the sitting from a `main` that holds it; the switch on. Two readings
  the code could not take: the data key's policy delegates to IAM only through Redshift Serverless, so a write
  through S3 is refused until `sandbox/data/`'s key policy names the role (AWS's
  `GenerateDataKeyDecryptDataTransferRole`, a D31 widening and the user's decision); and `update-catalog`
  takes the whole `CatalogInput`, so `get-catalog` comes first (Lesson 60).
  **[Claude] reads** what AWS Glue creates (a cluster or a Serverless workgroup, in Sandbox or out of it,
  its namespace, key and base capacity), the creation in CloudTrail under its caller, and whether
  `DenyRedshiftProvisionedClusters` refused it.
- **4.6 [user] Athena reads the table** through the federated catalog, from the producer's query editor
  and, if 4.4 subscribed it, from the consumer's. **[Claude] reads** the managed compute's usage where the
  account shows it, and the bill by usage type the next day.
- **4.7 An RMS catalog**: not run, since decision 3 took (b).
- **4.8 [Claude⚡] Removed in the sitting**: data lake access off, the catalog deleted, the namespace's
  registration withdrawn, `data_transfer_role_enabled` off and applied, each read back absent.

**The commands of pass 4**, in a shell that ran pass 2's first block. Every `$A` a colon follows is braced
(`${A}:catalog`): zsh takes the colon after a bare parameter for a modifier (Lesson 84).

```bash
# 4.1 ⚡ Recipe D's order: each object alone, read back for IAMAllowedPrincipals before the next
NSID='ServerlessIdentifier={NamespaceIdentifier=awsds-sandbox-warehouse,WorkgroupIdentifier=awsds-sandbox-warehouse}'
aws redshift register-namespace --namespace-identifier "$NSID" --consumer-identifiers "$A" --profile $S
aws redshift describe-data-shares-for-consumer --consumer-arn "arn:aws:glue:us-west-2:${A}:catalog" \
  --profile $S
DS='<the datashare ARN listed, ending /ds_internal_namespace in Lake Formation's example>'
aws redshift associate-data-share-consumer --data-share-arn "$DS" \
  --consumer-arn "arn:aws:glue:us-west-2:${A}:catalog" --profile $S
aws lakeformation register-resource --resource-arn "$DS" --profile $S
aws glue create-catalog --name stage21_warehouse --catalog-input "$(jq -cn --arg ds "$DS" '{
  Description: "Stage 21: the Sandbox warehouse namespace", CreateDatabaseDefaultPermissions: [],
  CreateTableDefaultPermissions: [], FederatedCatalog: {Identifier: $ds, ConnectionName: "aws:redshift"}}')" \
  --profile $S
aws glue get-catalogs --parent-catalog-id "${A}:stage21_warehouse" --recursive --profile $S
aws lakeformation list-permissions --resource "{\"Catalog\": {\"Id\": \"${A}:stage21_warehouse\"}}" \
  --profile $S
# 4.2 ⚡ the table's catalog id as 4.1's reads give it
aws lakeformation grant-permissions --principal \
  "DataLakePrincipalIdentifier=arn:aws:iam::${A}:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c" \
  --resource "{\"Table\": {\"CatalogId\": \"${A}:stage21_warehouse/sandbox\", \"DatabaseName\": \"lab\",
    \"Name\": \"trades_hot\"}}" --permissions DESCRIBE SELECT --profile $S
# 4.3 and 4.6 the session's identity, and the compute
q "select user_id, query_id, start_time, query_text from sys_query_history
   where start_time > '<the read>' order by start_time"
# 4.5 ⚡ the transfer role, sandbox/warehouse/'s data_transfer_role_enabled, applied for the sitting from a
# main that holds pull request #323: the page's trust (glue, redshift) and policy (glue:GetCatalog,
# glue:GetDatabase, kms:GenerateDataKey, kms:Decrypt); its ARN is the output data_transfer_role_arn.
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse plan -input=false \
  -var data_transfer_role_enabled=true -out="$HOME/tmp/s21-warehouse-transfer.tfplan"   # 2 to add
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse apply -input=false \
  "$HOME/tmp/s21-warehouse-transfer.tfplan"
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse output -raw data_transfer_role_arn
# The update passes the whole input get-catalog returned with DataLakeAccessProperties added: whether
# UpdateCatalog drops what it is not passed is unread (Lesson 60).
aws glue get-catalog --catalog-id "${A}:stage21_warehouse" --profile $S
aws glue update-catalog --catalog-id "${A}:stage21_warehouse" --catalog-input '<that input, with
  CatalogProperties.DataLakeAccessProperties = {DataLakeAccess: true, DataTransferRole: <its ARN>}>' \
  --profile $S
aws glue get-catalog --catalog-id "${A}:stage21_warehouse" --profile $S    # the managed compute, its status
aws redshift-serverless list-workgroups --profile $S
aws redshift describe-clusters --profile $S
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateCluster \
  --start-time <the switch> --profile $S                  # a refusal by DenyRedshiftProvisionedClusters
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateWorkgroup \
  --start-time <the switch> --profile $S
# 4.8 ⚡ in the sitting, each read back absent: data lake access off by the same update, then the catalog.
# The deletion page names the catalog's delete alone; the order after it is 4.1's reversed.
aws glue delete-catalog --catalog-id "${A}:stage21_warehouse" --profile $S
aws lakeformation deregister-resource --resource-arn "$DS" --profile $S
aws redshift disassociate-data-share-consumer --data-share-arn "$DS" \
  --consumer-arn "arn:aws:glue:us-west-2:${A}:catalog" --profile $S
aws redshift deregister-namespace --namespace-identifier "$NSID" --consumer-identifiers "$A" --profile $S
# then sandbox/warehouse/ planned without the variable and applied: the role and its policy go
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse plan -input=false \
  -out="$HOME/tmp/s21-warehouse-transfer-off.tfplan"                                    # 2 to destroy
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse apply -input=false \
  "$HOME/tmp/s21-warehouse-transfer-off.tfplan"
```

### 5. Images as an S3 Object Collection

Any Sandbox sitting with a space in both projects; the warehouse is not needed.

- **5.1 [user] The images and their table**, in an `eighth-experimentation` space: 1.4's generator, the
  files copied to the project's `shared/stage21-images/`, and a table `stage21_images` in the project's
  database, an Iceberg `CREATE TABLE ... AS` over the generator's `VALUES` from the query editor on
  Athena, its location under the database's own (read with `glue get-database` first).
- **5.2 [user] Publish the prefix** from the portal's S3 browser, *Actions → Publish to Catalog*, with a
  name, a description and the `classification` form. **[Claude] reads** the asset's type and forms.
- **5.3 [user] The table's asset by the project's source, and a data product of both**, published.
  **[Claude] reads** the listings and `CT-18`.
- **5.4 [user] The consumer requests the product; the owner approves it read-only.** **[Claude] reads**
  `s3control list-access-grants` (the grantee and its type, the location, the scope and the permission),
  the Glue item's grant and link (`CT-17`), and what one request gave each item.
- **5.5 [user] The consumer reads an image** from the portal and from a notebook, where the session gets
  the scope's credentials with `s3control get-data-access`; a key outside the scope refused, a write
  refused. **[Claude] reads** whether a space reaches S3 Control at all (no interface endpoint names it in
  `docs/NETWORK.md`), and which identity the trail records.
- **5.6 [user] A second request approved read and write** after a revocation; one object written under the
  scope. **[Claude] reads** the grant's permission.
- **5.7 [user] Revoke, with credentials vended just before.** **[Claude] reads** `GetDataAccess` refused
  within five minutes and the vended credentials' last success, against the page's fifteen.

**The commands of pass 5**, in a shell that ran pass 2's first block:

```bash
# 5.1 [user], an eighth-experimentation space, as the project role: 1.4's generator, then
aws s3 cp --recursive stage21-images/ \
  s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/stage21-images/
aws glue get-database --name <the project database> --query Database.LocationUri
# 5.2 to 5.4 the asset, the grants by item, CT-17 and CT-18
aws datazone search --domain-identifier $D --owning-project-identifier $P --search-scope ASSET \
  --search-text stage21 --profile $S
aws datazone get-asset --domain-identifier $D --identifier <asset> --profile $S
aws datazone list-subscription-grants --domain-identifier $D --subscription-id <subscription> --profile $S
aws s3control list-access-grants --account-id "$A" --profile $S
./aws/catalog.py
# 5.5 [user], a test-experimentation notebook, as the project role
aws s3control get-data-access --account-id "$(aws sts get-caller-identity --query Account --output text)" \
  --permission READ \
  --target 's3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/stage21-images/*'
# 5.5 to 5.7 each call's identity and refusal
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=GetDataAccess \
  --start-time <the request> --profile $S
```

```sql
-- 5.1 [user], the query editor on Athena, the project database; the generator's VALUES list after AS
CREATE TABLE stage21_images
WITH (table_type = 'ICEBERG', is_external = false, location = '<LocationUri>/stage21_images/') AS
SELECT * FROM (VALUES ...) AS t (object_key, tone, width, height, size_bytes);
```

### 6. The checks and the documents

- **6.1 [Claude]** [`catalog.md`](../runbooks/catalog.md): §A, a Redshift source and an S3 Object
  Collection as measured; §P, a product of several items and of mixed types; §S, the Redshift target, its
  fulfilment and its revocation, and the S3 Object Collection's; §L, Redshift lineage.
- **6.2 [Claude]** [`docs/SMUS.md`](../../SMUS.md)'s paragraph on existing buckets as catalog assets and
  its `RedshiftServerless` row, with the sitting's readings; D40's file, with decision 1 (b)'s sitting;
  [`docs/GOVERNANCE.md`](../../GOVERNANCE.md)'s paragraph on a data product, the lake and a warehouse,
  with what a subscription writes in Lake Formation, in Redshift and in S3 Access Grants; and
  [`redshift-connection.md`](../runbooks/redshift-connection.md) §G for a project that reads the
  warehouse's tables through a subscription to its own workgroup.
- **6.3 [Claude]** `./aws/warehouse.py` (`WH-9` for a lineage run the stage chose, `WH-12` and `WH-14`
  for a subscription's datashare) and `./aws/catalog.py` (an S3 Object Collection's grants explained
  by its subscription), each self-check green.
- **6.4 [Claude]** A `SUP-nnn` per measured behaviour no page states, the next id read from `origin/main`
  at the commit; [`docs/PRICING.md`](../../PRICING.md) for the managed workgroup if 4.5 ran; the threat
  model's entries for 3.1's `sys:operator` and 5.7's credentials after a revocation (Stage 11).
- **6.5 [Claude]** The bill by service the day after each sitting.

### 7. Close

The stage's row in `CLAUDE.md`'s Current position, the index's state, the log, and the waiting list's
rows removed.

## Verifications

| # | Question | Step |
|---|---|---|
| i | Does a Redshift data source import a table and a view, and with which asset types, forms and `sourceIdentifier`? | 2.2 |
| ii | Does a data product of a Redshift table and a view publish, and what do its listings carry? | 2.3 |
| iii | Does the `RedshiftServerless` blueprint hold the consumer's base capacity at 4 RPU, and does its environment carry a Redshift subscription target, in which form and with which principals? | 1.3, 2.4 |
| iv | What does DataZone write across the two workgroups for an approved request: the datashare, its consumer, the database from it and the view, as which users and in what time? | 2.5 |
| v | Does the consumer read the subscribed table from the Query editor and from a notebook, and is an unsubscribed table of the same schema refused, with which wording? | 2.6 |
| vi | What does the revocation remove on each workgroup, and when? | 2.7 |
| vii | Where does the portal's *Create table → Redshift table* upload, which `COPY` does it run, and what refuses it when the default role holds no policy? | 2.8 |
| viii | Does a lineage run succeed with the workgroup up and decision 2's credentials, and which statements become edges: inside `lab`, `UPDATE` and `MERGE`, and a read through `awsdatacatalog`? | 3.2 to 3.4 |
| ix | Do the lineage nodes link to the Redshift assets, and does the graph join a Glue job's events? | 3.4 |
| x | Does the federated catalog arrive carrying `IAMAllowedPrincipals`, and does Redshift read its table under Lake Formation's grant? | 4.1 to 4.3 |
| xi | Does a Glue data source import a federated catalog's table, as which asset type, and does a subscription to it in one account complete? | 4.4 |
| xii | What does data lake access create, where, under which key and base capacity; does `DenyRedshiftProvisionedClusters` refuse it; does Athena read through it; and what did it bill? | 4.5, 4.6, 6.5 |
| xiii | Does an RMS catalog's table take writes from Athena and reads from Redshift? Not measured: decision 3 took (b) | — |
| xiv | Does an S3 prefix publish as an S3 Object Collection with its business metadata, and does a product of it and a Glue table publish? | 5.2, 5.3 |
| xv | What does an approved request write in S3 Access Grants: which grantee, location, scope and permission, and what does one request give each item of a mixed product? | 5.4 |
| xvi | Does the consumer read an image from the portal and from a notebook, does a space reach S3 Control, and are a key outside the scope and a write refused? | 5.5 |
| xvii | Does a read-and-write approval let the consumer write under the scope? | 5.6 |
| xviii | After a revocation, how long does `GetDataAccess` answer, and how long do credentials vended before it work? | 5.7 |
| xix | What did the sittings bill, by service? | 6.5 |
| xx | Does removing the consumer's compute delete its workgroup, namespace and stack, and does `US-3` read green with 1.5's variables off? | 2.9 |

## Decisions due

The user took the decisions below on 2026-11-17 in the cloud session's thread, one card at a time at the
user's request: decision 1 on its card at 21:55 UTC, decisions 2 and 3 in words at 21:55 UTC. At 21:50 UTC
the user set the rule the recommendations follow: *"Revise as recomendações considerando que iremos
exercitar o caminho sugerido pela AWS por padrão."* The log carries each question as it was asked and each
answer in the user's words. Taken: 1 to 3.

1. **The consumer of a Redshift asset, and its subscription target** (2.4). **Taken 2026-11-17: (b)**, on
   the card whose option read *"Caminho documentado pela AWS: o consumidor ganha um workgroup só dele por
   uma sessão, com a capacidade base no mínimo; o warehouse do Sandbox não muda."* AWS's pages describe a
   subscription delivered to *"the Amazon Redshift Serverless workgroup created for the project"*. The
   `RedshiftServerless` blueprint, category 3 in [`docs/SMUS.md`](../../SMUS.md), is enabled for
   `test-experimentation` for one sitting through 1.5's code, its base capacity locked at 4 RPU before the
   create, and removed at 2.9; between the warehouse and that workgroup the fulfilment is the
   datashare-and-view shape. It amends D40 and D12 for the sitting, admits no second project to the
   warehouse, and leaves 6h decision 8 (a)'s switch off. If the blueprint will not hold the floor, decision 1 returns
   to the user. Not taken: (a) `test-experimentation` admitted to the Sandbox warehouse under 6h decision 8
   (a), the tag `for-use-with-all-datazone-projects=true`, and a target written with
   `CreateSubscriptionTarget` if none appeared: the institution's own shape, a project that adds an
   existing workgroup, which stays unmeasured; (c) no consumer, Stage 19 decision 9 (a) as it stands.
2. **The credentials Redshift lineage runs with** (3.1). **Taken 2026-11-17: (a)**, in the user's words
   *"aceito as recomendações das decisões 2 e 3, considerando que é o caminho que a AWS documenta"*: a
   second connection in `eighth-experimentation`, authenticated by a secret for a database user
   `lineage_reader` holding `sys:operator` and `SELECT` on `lab`, created for the sitting and removed after.
   It is the form the data source page documents, the connection's credentials holding `sys:operator` and
   `SELECT` on all the tables, and the project's own identity stays unprivileged. While the grant stands,
   every member of the project can read the text of every query run on the warehouse, since the project
   role runs the lineage's statements and reads the connection's credentials. Not taken: (b) the existing
   IAM connection, its database user granted `sys:operator` for the sitting; (c) no Redshift lineage
   measured.
3. **The Iceberg engines' access to the warehouse** (pass 4). **Taken 2026-11-17: (b)**, in the same
   words: the federated catalog registered, read by Redshift and imported by a Glue source, then data lake
   access switched on for the sitting; what AWS Glue creates is read, Athena's read through it measured,
   everything removed in the sitting and the bill read the next day; Stage 9's 9.5a reading, owed since its
   decision 5, taken in Sandbox. It is the path AWS's pages give Athena, Amazon EMR and Spark to Redshift
   data. Question 6 asks what compute stands behind it, the pages disagree on its shape and name neither
   its account nor its size, and only a creation answers; a refusal by `DenyRedshiftProvisionedClusters` is
   a reading too. Not taken: (a) data lake access left off; (c) an RMS catalog besides, so 4.7 and
   verification xiii do not run; (d) none of pass 4.

## Cost

Measured rates, `us-west-2`, from [`docs/PRICING.md`](../../PRICING.md):

- A Sandbox sitting: the hub's two `[D]` hosts, `sandbox/egress/`'s interface endpoints at 0.180 USD per
  hour for the set, and a space at 0.050 per hour on `ml.t3.medium` in each project.
- The warehouse: 0.36 per RPU-hour, 1.44 per query-hour at 4 RPU, nothing idle; the free trial absorbs it
  to 2026-12-19. 6h's sitting of 2026-10-10 burned 2.44 USD by `ComputeSeconds`.
- The managed workgroup of decision 3 (b): *"standard Amazon Redshift Serverless rates"*, whose base
  capacity no page states; read at 4.5 and removed at 4.8. Whether the free trial covers it is a reading.
- Decision 1 (b): the consumer's workgroup at the same rate, at the 4 base RPUs the profile locks, with
  the 60-second minimum per query; whether the free trial covers a second workgroup is a reading.
- S3 Access Grants: 0.03 per 1,000 requests. S3: kilobytes. Athena: 5.00 per TB scanned, kilobytes.
- The catalog: metadata requests at 10.00 per 100,000 with 4,000 a month free per account; a source's run in
  compute units at 1.776 each with 0.2 a month free.
- At rest: nothing new. Every object a pass creates is removed at its end, the consumer's workgroup and
  namespace at 2.9, but the assets and listings, which are metadata.

## Rollback

Each write is on the user's word, in this order, each object read before its delete.

1. **[user] The subscriptions revoked** (2.7, 5.7), then **the listings unpublished and the data products
   deleted**, in the order [`catalog.md`](../runbooks/catalog.md) §A's deletion takes.
2. **[Claude⚡] The federated catalog and data lake access** (4.8), if 4.8 did not run: the switch off, the
   catalog deleted, the registration withdrawn, `data_transfer_role_enabled` off and applied.
3. **[Claude⚡] The lineage credentials** (3.5), if 3.5 did not run: the second connection by a member, the
   user dropped, the secret deleted with no recovery window.
4. **[user] then [Claude⚡] The consumer's workgroup** (2.9), if 2.9 did not run: the compute removed in
   the portal and read absent with its stack; 1.5's variables off, `data-governance/governance/` then
   `sandbox/sagemaker/` applied and re-planned `No changes`.
5. **[user] The tables and the images**: `DROP` of `lab.trades_hot_daily`, `lab.trades_hot_by_desk` and
   `lab.trades_hot` unless Stage 19 keeps its copy; the files under `shared/stage21-images/` and the table
   `stage21_images`.
6. **[user] `make down ENV=sandbox`**, every portal tab closed first
   ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D).

## What this stage does not do

- Promote a product, or touch Production's warehouse, its datashare or its federated database.
- Build a SageMaker application: the tables come from SQL in the query editor and the files from a space.
- Keep a federated catalog, data lake access, the consumer's workgroup, the `RedshiftServerless` blueprint
  or `sys:operator` past its sitting.
- Grant the namespace's default role a policy (5b decision 5), even for 2.8.
- Enable the `LakehouseCatalog` or `LakehouseAdmin` blueprints, or create an RMS catalog (decision 3 (b)).
- Build S3 Metadata tables or an S3 table bucket: read, not built.
- Put unstructured files in the governed lake's buckets.

## What concerns the other sessions

- **Stage 19**: its pass 5 shares the warehouse sitting. Its 5.3 asset is the one 2.2 reads when it ran
  first, and its 5.4 revocation waits for pass 2's end.
- **6h**: decision 1 (b) admits no second project to the warehouse, so its decision 8 (a), taken
  2026-11-17 with its switch written and off, is turned on nowhere here, and `WH-7` stays as it is. Pass 3 reads a lineage run, and its decision 3 stays the user's.
- **6d, 17, 19 and 20**: 1.5's variables ride `sagemaker-prereqs`, `sandbox/sagemaker/` and
  `data-governance/governance/`, which their applies plan too. Off by default, they plan `No changes` in
  another stage's tree; the sitting's apply is announced to the other sessions first, and `US-3` reads red
  until 2.9.
- **Stage 9**: pass 4 brings the federated catalog back in Sandbox alone, and decision 3 (b) takes 9.5a's
  reading there, the question of its verification xxiii; its decision 5 holds in Production, where nothing
  changes.
- **Stage 11**: 6.4's threat-model entries, `sys:operator` held by a project and an S3 Access Grants
  credential that outlives its revocation.
- **Stage 20**: its pass 5 makes `eighth-experimentation` a consumer of Production's listing; this stage
  makes it the producer of two data products and, if 4.4 imports, a federated catalog's asset, each retired
  at the end.
- **Stage 12**: the bills of decision 1 (b)'s workgroup and decision 3 (b)'s managed workgroup, read at
  6.5 against D12.
