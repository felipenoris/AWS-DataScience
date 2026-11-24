# Stage 21 — Redshift tables and S3 objects as data products in SageMaker Unified Studio

| | |
|---|---|
| **Status** | **2026-11-24, pass 8 written with nothing up, decision 5 due** ([log](../../log/log-stage-21-redshift-s3-data-products.md)): on the user's request of 14:39 UTC, pass 4's failure read against AWS's pages, and the three statements the request rested on checked. A Lake Formation-managed datashare is read by Redshift alone; Athena and Spark reach the warehouse's tables through the federated catalog, Spark only through the Glue Iceberg REST catalog's extension endpoint; and the Iceberg engines may write under a grant, DDL refused. Pass 4 seated no `AWSServiceRoleForRedshift` among Lake Formation's read-only administrators, a step of Lake Formation's prerequisites, and granted the project role while the portal's Redshift session reaches Glue and Lake Formation as the access role (`SUP-139`); Redshift's Region list for Iceberg compatibility omits US West (Oregon), where every call of pass 4 succeeded. 8.1 to 8.3 need nothing up; the sitting rides SB2 under decision 5, before the free trial ends on 2026-12-19. Before it, **2026-11-23, pass 5 done to 5.7 with rollback items 1, 5 and 6** ([log](../../log/log-stage-21-redshift-s3-data-products.md)), no warehouse: 20 synthetic PNGs under `eighth-experimentation`'s `shared/stage21-images/` and their Iceberg table `stage21_images` in the data product `sandbox-stage21-images`, subscribed by `test-experimentation`. Verification xiv yes: the prefix publishes from the S3 browser with the approval switch alone, and the product's publication leaves the table's listing `INACTIVE` and outside `SearchListings` (`SUP-479`, `SUP-482`). xv: one S3 Access Grant, `READ`, to the subscriber's project role on the producer's location, scoped to the prefix; a request from a space is recorded as the space's user, so it was accepted at creation (`SUP-480`, `SUP-481`), and by the user's choice 5.4 is not run again with a requester outside the owning project, the manual approval resting on Stage 19's of 2026-11-22. xvi yes: the portal and a terminal read an image, the terminal reaching S3 Control through the spoke's S3 gateway endpoint (`SUP-091`); a vend outside the scope, a listing of `shared/` and a `READ` session's write refused. xvii yes: write is asked on the asset's own listing, never through the product, and the `READWRITE` session wrote. xviii: the vend was refused 31 s after the grant's deletion, and at the second revocation nine seconds before the trail's `RevokeSubscription`, recorded as observed and closed by the user's choice; sessions vended before a revocation live their own duration, a 3600 s one writing 19 minutes after (`SUP-092`); `TM-37` accepted by the user the same day, *"Aceito as três recomendações do N.10."*. `catalog.py` gained `CT-20`, and its `CT-17` and `CT-18` reach a table its product's publication listed through the product listing's items, `CT-18` taking the product's form for it (Stage 19 decision 4 extended by the user, self-check 62 of 62, `SUP-482`). The lowering ran 18:12:50 to 18:23:12 UTC, Sandbox at zero. Owed: 6.5's bill by service once Cost Explorer holds both days (`SUP-142`), xix. Before it, **2026-11-23, 6.5's Redshift half read from the free trial, nothing up** ([log](../../log/log-stage-21-redshift-s3-data-products.md)): the managed workgroup charged 23,040 RPU-seconds, 2.30 USD, for 4 `ComputeSeconds`, metered under its own UUID, and the consumer's workgroup 960, 0.10, both absorbed by the trial. xii's bill is answered and its base capacity stays unread; 6.4's price is in [`docs/PRICING.md`](../../PRICING.md) §5. The trail holds the managed workgroup's `CreateManagedWorkgroup`, invoked by Glue, and no `CreateCluster` (`SUP-474`, Stage 9's 9.5a). Owed: pass 5 with its own rollback; 6.5's bill by service once Cost Explorer holds both days (`SUP-142`). Before it, **2026-11-22 and 23, `promotion.md` §N.10's day 2: passes 2 to 4 run, 2.6 not run, rollback item 5 done** ([log](../../log/log-stage-21-redshift-s3-data-products.md)): 2.4's two slices applied; 2.2's source imported three assets once the access role held `ExecuteStatement` (`SUP-460`); 2.3 published the data product `sandbox-trades-hot`, `lab.trades_hot` and its view `lab.trades_hot_by_desk`; 2.4's consumer workgroup `redshift-serverless-workgroup-dahsfn6j8lqec0` deployed in `test-experimentation`, its deploy granting the role `datazone_env_dahsfn6j8lqec0` `sys:superuser` (`SUP-471`). 2.5's subscription was accepted at creation and both grants failed, *"Secret ARN can not be null or empty"*, nothing written in either namespace while both portals read it shared (`SUP-469`); 2.6 had nothing to read; 2.7 revoked it. 2.8's load was refused by KMS to the access role at the upload, before any `COPY` (`SUP-470`), answering verification vii. On the user's choice the same night, `SUP-469` is 2.5's reading and the retry on a connection authenticated by a secret is not run. 2.9 done 2026-11-23 by 00:31 UTC: the consumer's deployment deleted in the portal, nothing of it left, `data-governance/governance/` then `sandbox/sagemaker/` applied with the switch off and re-planned *"No changes."*, `US-3` green. Pass 3 done 2026-11-23, 00:37 to 01:06 UTC: `lineage_reader` and its secret, the connection `sandbox-lineage-reader` carrying no lineage job until its data source's *Import data lineage* wrote one (`SUP-207`); 3.3's statements run as the admin through the Data API to land before the pull. The pull read seven days and ended `PARTIALLY_SUCCEEDED`, answering verification viii: `CREATE TABLE … AS`, `INSERT … SELECT` and `CREATE VIEW` inside `lab` became edges, the `UPDATE` and the `MERGE` did not, and Stage 19 5.2's `CREATE TABLE … AS` from `awsdatacatalog`, in the window, was the run's one failure, so `lab.trades_from_lake` was not created (`SUP-472`). Verification ix: the dataset nodes join the three Redshift assets by their ARN, and the graph does not reach the lake's `trades_notional` or a Glue job's events (`SUP-473`). 3.5 removed the data source, the connection and its job, the user and the secret (seven-day window); the nodes stay. Pass 4 done 2026-11-23, 01:23 to 01:53 UTC: the namespace registered to the Data Catalog, the federated catalog `stage21_warehouse` arriving with no `IAMAllowedPrincipals`, and 4.2's grant; Redshift in the producer's workgroup resolves no `"sandbox@stage21_warehouse"`, answering verification x no (`SUP-475`). 4.4's Glue data source imported `trades_hot` as a Glue table asset keyed by the Glue table's ARN (`SUP-476`), xi's first half; the subscription was not run. Data lake access created a managed Redshift Serverless workgroup that only `ListManagedWorkgroups` lists, under an AWS-owned key, and no cluster, and `update-catalog` refuses the `CustomProperties` `get-catalog` returns (`SUP-474`); Athena through it fails on the same name, answering xii but for 6.5's bill. 4.8 removed every object, both slices re-planned *"No changes."*, and the closing reads passed, `WH-8` green. Rollback item 5 done at 01:57 UTC with Stage 19's 5.4: the view and the three tables dropped, `lab` kept. The lowering from 02:15:48 to 02:27:56 UTC, `make status` at 0.0000 USD/h, §R's readings and `catalog.py` passing. Rollback item 1's second half done 2026-11-23, 03:08 to 03:13 UTC, in the portal: the data product `sandbox-trades-hot` unpublished and deleted, its three assets deleted after the two listings' unpublish, then the source `sandbox-lab-trades-hot`. Before it, **2026-11-22, 2.2 attempted as Stage 19's step 6 on `promotion.md` §N.10's day 1** ([log](../../log/log-stage-21-redshift-s3-data-products.md)): the Redshift data source failed creation, the access role lacking `redshift-data:ListDatabases` (`SUP-460`), the four metadata reads applied the same evening (21:23 UTC), so 2.2 runs again on §N.10's day 2 and 2.3 waits for its asset; 2.1's copy `lab.trades_hot` exists, 10 rows, with no materialized view over the link (`SUP-459`). Before it, **Pass 1 done 2026-11-18**. Written 2026-11-17: the plan, the user's questions of 2026-11-17 answered from AWS's pages read that day and from this estate's measurements, and decisions 1 to 3, taken the same day: 1 (b), the consumer's own workgroup by the `RedshiftServerless` blueprint for one sitting; 2 (a), a second connection by secret for lineage; 3 (b), the federated catalog with data lake access for one sitting. 1.3's readings, 2026-11-18 with nothing up: the blueprint's template holds the base capacity at 4 RPU through a locked `redshiftBaseCapacity`, so decision 1 stands. 1.5's code written the same day, off by default, both slices planned *"No changes."*; the tag `sagemaker-prereqs-v0.12.0` pushed the same night by Recipe B and `sandbox/sagemaker/` moved to it, re-planned *"No changes."*. **1.3's wizard half read 2026-11-22** and left by *Cancel*: the form asks for a provisioning role and a manage-access role, the two every configuration names, so the checklist's step 4 closes with no change; the blueprint's configuration read absent before and after, and the trail holds no write. 4.5's data transfer role written and merged 2026-11-18 with [pull request #323](https://github.com/felipenoris/AWS-DataScience/pull/323), `data_transfer_role_enabled` off, planned *"Plan: 2 to add"* with it on. Passes 2 to 4 ride the Sandbox warehouse sitting ([`runbooks/promotion.md`](../runbooks/promotion.md) §N.6 item 9), before 2026-12-19 if the free trial is to absorb them; their commands, and pass 5's, follow each pass's steps. Pass 5 needs no warehouse and rides any Sandbox sitting with a space in both projects. **Passes 2 to 4's rows written 2026-11-19, nothing up**, in "The Sandbox warehouse sitting: passes 2 to 4 in order": the four slices re-planned from `main` with the counts the commands carry, pass 2's raise corrected to one `make up`, and every plan of `sandbox/warehouse/` naming both switches. **4.5's write path taken 2026-11-22, decision 4 (b)**: `sandbox/data/`'s key policy names the data transfer role for the sitting, AWS's `GenerateDataKeyDecryptDataTransferRole` behind `data_transfer_key_statement_enabled`, off by default; planned *"No changes."* off and *"Plan: 0 to add, 1 to change, 0 to destroy."* on, not applied |
| **Prerequisites** | [5b](stage-05b-redshift-serverless.md) and [6h](stage-06h-redshift-connection.md): the Sandbox warehouse at 4 base RPUs and `eighth-experimentation`'s connection, which writes and reads the schema `lab` in the `sandbox` database (6h passes 0 to 2, 2026-10-10). [Stage 19](stage-19-smus-native-data-product.md)'s Glue road: a table imported by a project's source, published, packaged in a product and subscribed inside one account (verification vi, 2026-11-14); its pass 5, whose 5.3 publishes the estate's first Redshift asset and subscribes nothing. `test-experimentation`'s `DataLake` environment ([6f](stage-06f-data-governance.md) 2.0), the Glue subscription target. The account's S3 Access Grants instance, created by SageMaker Unified Studio with one location per project ([`docs/SMUS.md`](../../SMUS.md), "The vending surface under that same path", 2026-08-23). For pass 2's subscription, 1.5's code merged and tagged, off by default (decision 1 (b)). For pass 8's sitting, 8.3's code merged, off by default, and decision 5. Nothing blocks pass 1 |
| **Consumes** | [D13](../decisions/D13-lake-formation-enforcement.md), [D26](../decisions/D26-unified-studio.md), [D40](../decisions/D40-redshift-warehouse.md); [D12](../decisions/D12-budget-ceiling.md) for the cost; [D31](../decisions/D31-approver-read.md) for the data key's readers (decision 4); 6h decisions 3 and 8, [Stage 9](stage-09-deployment-targets.md) decisions 5 and 14 and Stage 19 decision 9, each read against its premises; [D22](../decisions/D22-data-governance-account.md) for pass 8's reading of Production, Data Governance and Sandbox |
| **Proves** | — (no `INT-nn` row: everything runs in Sandbox, and the domain in Data Governance is reached through the doors Stage 19 measured). What it does prove: whether SageMaker Unified Studio's standard path carries a Redshift table, the namespace seen through the Glue Data Catalog, and an S3 prefix of images through publication, a data product and a subscription as it carries a Glue table; which engine and which compute the consumer needs for each; and what lineage the catalog draws for the warehouse |

*Read with [`docs/GOVERNANCE.md`](../../GOVERNANCE.md) §The catalog road and its paragraph on a data
product, the lake and a warehouse, [`docs/SMUS.md`](../../SMUS.md) §The catalog surface,
[`runbooks/catalog.md`](../runbooks/catalog.md) §A, §P, §S and §L,
[`runbooks/redshift-connection.md`](../runbooks/redshift-connection.md) §P, §G, §J and §T, Stage 9 decision 5
and Stage 19 decision 9. The vendor sources are the 2026-11-17 rows in
[`docs/REFERENCES.md`](../../REFERENCES.md), and pass 8's the 2026-11-24 row.*

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
decision for the user, named by its number in Decisions due. Read from `main` `7816fbe` on 2026-11-17; pass
8's rows from `676800d` on 2026-11-24.

| Item | Today | Under the premises |
|---|---|---|
| D40 | one warehouse per account by hand; the `RedshiftServerless` and `LakehouseCatalog` blueprints disabled, the first for its default of 128 base RPUs and a workgroup per project | **amend for one sitting**: decision 1 (b) enables the blueprint for `test-experimentation`, its base capacity locked at 4 RPU, and removes it at 2.9; D40's file records the sitting at 6.2 |
| D13 | execution roles hold no S3 on the lake's registered prefixes | **keep**: pass 5's prefix is in the producer's project path, which Lake Formation does not register |
| D26 | one domain, in Data Governance | **keep** |
| 6h decision 3 | the connection's `lineageSync`, off since 2026-11-19; its 39 daily runs at 03:43 UTC before it all failed | **keep** as the user's; pass 3 reads a lineage run with the workgroup up and leaves the setting as it found it |
| 6h decision 8 | how a second project is admitted to the warehouse; taken 2026-11-17 as (a), the tag `for-use-with-all-datazone-projects=true`, its switch written 2026-11-18 and off | **keep** as taken, standing since 2026-11-22 ([pull request #363](https://github.com/felipenoris/AWS-DataScience/pull/363)): 6h's apply on §N.10's day 1 puts `test-experimentation` in the map under the tag, with no schema. Decision 1 (b) admits no project of its own, and every plan of `sandbox/warehouse/` here names the tag true |
| Stage 9 decision 5 | Production's namespace reaches Lake Formation as a Lake Formation-managed datashare mapped to a federated database; data lake access refused for the managed cluster against `DenyRedshiftProvisionedClusters` and D12; 9.5a's reading owed only if the federated catalog comes back | **keep** in Production. **Decision 3 (b)**: the federated catalog comes back in Sandbox for one sitting, and 9.5a's reading is taken there. 9.5a read 2026-11-23: a Serverless workgroup and no cluster, under an AWS-owned key (`SUP-474`); pass 8 measures Athena's and Spark's reach over the shape, and the decision stays the user's |
| Stage 9 decision 14 | (a): Data Governance registers Production's datashare and grants it, the registration permanent under `DenyLakeDeletionAndDeregistration` | **keep**: pass 8 registers nothing outside Sandbox, and weighs a registration of Production's namespace to Data Governance's catalog without building it |
| D22 | Data Governance holds state and no compute | **keep**: pass 8 reads that no page names the account of a managed workgroup for another account's namespace |
| Sandbox's Lake Formation settings | `consumer-data` sets the administrators and `Parameters`, and no read-only administrator | **amend for one sitting**: 8.5 seats `AWSServiceRoleForRedshift` among the read-only administrators by `put-data-lake-settings`, outside Terraform, and 8.14 takes it out |
| The access role in `sandbox/warehouse/` | `glue:GetCatalogs` on this account's catalogs; no statement names `stage21_warehouse` | **amend for one sitting**: 8.3's `federated_catalog_read_enabled`, off by default, gives it the catalog's metadata reads, and 8.8 grants it in Lake Formation |
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
  `test-experimentation` is in no map: not admitted until 6h's standing apply on §N.10's day 1 ([pull
  request #363](https://github.com/felipenoris/AWS-DataScience/pull/363)), which puts it in the map under
  the wide tag, with no schema.
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
  - the console's enable wizard (the checklist's step 4), read by the user on 2026-11-22 and cancelled: a
    provisioning role and a manage-access role, each new or existing, the two `blueprints.tf` names on every
    configuration, and no regional parameter; nothing to declare.
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

Inside the Sandbox warehouse sitting (`make hub-up`, then `make up ENV=sandbox GROUPS=redshift`, which
raises `sandbox/egress/` with the `redshift` endpoint group, the warehouse's compute and `sandbox/probes/`
in one apply), spaces in both projects. When Stage 19's pass 5 runs in
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
  the portal, from the project's *Resource blueprints* page (*Deploy*). While the configuration and its
  grant stand, every contributor of every `experimentation` project can deploy the same workgroup from that
  page ([`SMUS.md`](../../SMUS.md) §Resource blueprints), and `make status` reads no Redshift workgroup, so
  the variables stay on for the sitting alone and 2.9 reads every project before turning them off.
  **[Claude] reads** the environment and its stack; the namespace and the workgroup, their base
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
  namespace absent, and no `RedshiftServerless` environment in any project of the domain
  (`datazone list-environments` per project, the blueprint's id as filter) nor any workgroup in Sandbox
  but the warehouse's. **[Claude⚡]** On the user's word, 1.5's variables off, `data-governance/governance/`
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
# 2.4 ⚡ the other sessions told first, sandbox/sagemaker/ at sagemaker-prereqs-v0.14.0; this order on
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
CREATE TABLE lab.trades_from_lake AS SELECT * FROM awsdatacatalog.glue_db_blerpkhn9nj7o0.<the link 4.12 read>;
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
  `data_transfer_role_arn`; applied for the sitting from a `main` that holds it and 6h's standing tag
  ([pull request #363](https://github.com/felipenoris/AWS-DataScience/pull/363)), the tag named true and
  the switch on. Two readings
  the code could not take: the data key's policy delegates to IAM only through Redshift Serverless, so a write
  through S3 needs the key policy to name the role, AWS's `GenerateDataKeyDecryptDataTransferRole`, a D31
  widening for the sitting (decision 4 (b)): `sandbox/data/`'s `data_transfer_key_statement_enabled`, applied
  after the role exists and off again before the role goes; and `update-catalog` takes the whole
  `CatalogInput`, so `get-catalog` comes first (Lesson 60).
  **[Claude] reads** what AWS Glue creates (a cluster or a Serverless workgroup, in Sandbox or out of it,
  its namespace, key and base capacity), the creation in CloudTrail under its caller, and whether
  `DenyRedshiftProvisionedClusters` refused it.
- **4.6 [user] Athena reads the table** through the federated catalog, from the producer's query editor
  and, if 4.4 subscribed it, from the consumer's. **[Claude] reads** the managed compute's usage where the
  account shows it, and the bill by usage type the next day.
- **4.7 An RMS catalog**: not run, since decision 3 took (b).
- **4.8 [Claude⚡] Removed in the sitting**: data lake access off, the catalog deleted, the namespace's
  registration withdrawn, `data_transfer_key_statement_enabled` then `data_transfer_role_enabled` off and
  applied, each read back absent.

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
# main that holds pull requests #323 and #363: the page's trust (glue, redshift) and policy (glue:GetCatalog,
# glue:GetDatabase, kms:GenerateDataKey, kms:Decrypt); its ARN is the output data_transfer_role_arn.
# Every plan of the slice names both switches (Lessons 51, 69). 6h decision 8 (a)'s wide tag stands since
# 2026-11-22 (pull request #363), applied at 6h's step 7 on day 1, and false fails the `projects`
# validation, a map of two since that pull request. A plan reading 9 to add, 2 to change, 6h's reading
# before its apply (2026-11-22), means step 7 has not run: stop. The 2 to add below are the role and its
# inline policy, that plan's difference from the tag's alone (7 to add, 2 to change), read 2026-11-22.
TAG=true
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse plan -input=false \
  -var all_projects_tag_enabled=$TAG -var data_transfer_role_enabled=true \
  -out="$HOME/tmp/s21-warehouse-transfer.tfplan"                                        # 2 to add
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse apply -input=false \
  "$HOME/tmp/s21-warehouse-transfer.tfplan"
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse output -raw data_transfer_role_arn
# decision 4 (b) ⚡ the key statement naming the role, once the role exists: KMS refuses a principal that
# does not. Never with -refresh=false or -minimal-refresh on this slice (OQ 24).
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data plan -input=false \
  -var data_transfer_key_statement_enabled=true -out="$HOME/tmp/s21-data-key-on.tfplan"   # 1 to change
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data apply -input=false \
  "$HOME/tmp/s21-data-key-on.tfplan"
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
# then the key statement off, so the key policy never names a deleted role
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data plan -input=false \
  -out="$HOME/tmp/s21-data-key-off.tfplan"                                              # 1 to change
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data apply -input=false \
  "$HOME/tmp/s21-data-key-off.tfplan"
# then sandbox/warehouse/ planned with the transfer switch off and applied: the role and its policy go
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse plan -input=false \
  -var all_projects_tag_enabled=$TAG -var data_transfer_role_enabled=false \
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

### 8. The federated catalog again: why pass 4's reads failed, then Athena and Spark over it

Written 2026-11-24 with nothing up, on the user's request of 14:39 UTC in a cloud session's thread:
*"Revise o plano do stage associado incluindo esta etapa de investigação e configuração da
funcionalidade."* Pass 4 registered the namespace and created the catalog, and neither Redshift nor Athena
resolved `"sandbox@stage21_warehouse"` (`SUP-475`). Pass 8 reads which prerequisite or grant pass 4
missed, configures the shape AWS's pages give, and measures a read by Redshift, Athena and Spark and a
write by each Iceberg engine, under decision 5. It runs before 7's close: the numbers are identifiers,
not an order.

**What AWS's pages say**, read 2026-11-24 in their `.md` form where one exists
([`docs/REFERENCES.md`](../../REFERENCES.md)), against the three statements the request rested on:

- **A Lake Formation-managed datashare is read by Redshift alone: holds.** *"You can query Amazon Redshift
  datashares managed by Lake Formation with Amazon Redshift. Athena doesn't support querying Amazon
  Redshift datashares managed by Lake Formation."* (Lake Formation's notes on Redshift datashares).
  Production's `trades_lf`, registered in Data Governance as the federated database `governed_trades`
  (Stage 9 decisions 5 and 14), is that shape.
- **Athena and Spark reach the warehouse's tables through the namespace registered as a federated
  catalog: holds, through two doors.** Lake Formation's page on creating the catalog names *"Apache
  Iceberg compatible analytical engines such as Athena and Apache Spark on Amazon EMR"*, which data lake
  access serves: *"To enable these query engines to read and write to Amazon Redshift namespaces, AWS Glue
  creates a managed Amazon Redshift cluster with the compute and storage resources required to perform
  read and write operations without impacting Amazon Redshift data warehouse workloads."* Athena reads the
  catalog as one registered with Glue: *"Athena can read and write data stored in Redshift clusters or
  serverless namespaces that have been registered in the AWS Glue Data Catalog."* (Athena's page), and
  *"Athena doesn't support a multi-catalog experience."* (Lake Formation's notes on these catalogs).
  Spark reads it through Glue's Iceberg REST catalog: *"RMS tables are accessible only from the extension
  endpoint in AWS Glue Iceberg REST Catalog."* (the same notes), the endpoint's page giving *"Endpoint :
  https://glue.{{us-east-1}}.amazonaws.com/extensions"* and *"These additional APIs are used when you
  access tables stored in Amazon Redshift managed storage."* No page says whether the standard endpoint,
  `https://glue.<region>.amazonaws.com/iceberg`, serves a federated catalog's tables; 8.12 tries both.
  Redshift's federated permissions, the other registration model, is Redshift's alone: *"Access from
  engines other than Redshift is not supported"* (Redshift's considerations for it). Pass 4's catalog
  carried `aws:PermissionsModel` `LAKEFORMATION`, the model the Iceberg engines read.
- **Outside engines only read: does not hold as written.** The pages give read and write and refuse DDL:
  the creation page above; Athena's, *"DDL operations, including setting AWS Glue Data Catalog
  configuration and operations on Amazon Redshift managed storage tables, are not supported."*; Lake
  Formation's notes, *"Data Definition Language (DDL) operations on the catalog from engines like Athena,
  Amazon EMR Spark, or others, including setting catalog configurations, are not supported."*; and the
  SageMaker Lakehouse FAQ, *"However, you must have appropriate write permissions on the tables to write
  data to them."* A consumer is read-only by its grant, `SELECT` without `INSERT`; 8.11 to 8.13 measure
  both.

**Pass 4's failure, by cause**, each read against pass 4's entry in the log:

| Cause | The page or the estate | It would explain | Read or removed by |
|---|---|---|---|
| The Redshift service-linked role is no Lake Formation read-only administrator | *"To query the Amazon Redshift tables in the federated catalog from Amazon Redshift Query Editor v2, ensure that the Read only administrator role policy contains the ARN for the Amazon Redshift service-linked role-`AWSServiceRoleForRedshift`."* (Lake Formation's prerequisites, a step done by `put-data-lake-settings`), the role its roles table describes as *"Discovers the federated catalog, queries Amazon Redshift tables in the federated catalog."* `consumer-data` sets no read-only administrator, and pass 4 named none | both reads: neither the producer's workgroup nor the managed one mounted the catalog | 8.2 reads the settings; 8.5 seats the role |
| The Redshift session's principal held neither half of the reach (Lesson 28) | The portal's Redshift session calls Glue and Lake Formation as the access role, never as the project role its database user is named after (`SUP-139`; [`redshift-connection.md`](../runbooks/redshift-connection.md) §G, measured on `governed_trades` on 2026-10-25). 4.2 granted the project role, and no statement of the access role names `stage21_warehouse`: on this account's catalogs it holds `glue:GetCatalogs` (`ListTheCatalogsTheQueryEditorOffers`), and its database and table reads name `governed_trades` (`ReadTheGovernedShareCatalog`, written after Glue refused it `glue:GetTable` on 2026-10-25) and the subscription's link database (`ReadTheSubscribedProductsCatalog`). The editor's toast, `autocompleteMsg.getMetadataErrorAccessDenied`, is a refusal | Redshift's read; Athena's ran as the project role, which held the grant | 8.1 reads the refused call and its caller; 8.3's statement and 8.8's grants to both roles remove it |
| The namespace was not mounted for want of use | *"When you register a serverless namespace that’s not being actively used, the AWS Glue Data Catalog won’t mount that namespace as a catalog until the namespace is used again."* (Redshift's overview). The workgroup ran statements before and after the registration (the log), and the page defines no window | both, for a while | 8.7 registers after a statement; 8.9 reads the mount at 0, 5 and 15 minutes |
| The data key lacks the page's statement for Redshift | Lake Formation's prerequisites write four statements into a customer managed key. The data key holds Redshift Serverless's path (`AllowRedshiftServerlessViaServiceInThisAccount`), the root's metadata actions (`EnableKeyAdministrationInThisAccount`) and, for a sitting, the transfer role's, and not `RedshiftAllowAccessPolicy`, the path through `redshift.<region>.amazonaws.com`. [inferred] The registration and its datashare are Redshift's calls, not Redshift Serverless's | both, if the mount reads the key on that path | 8.1 reads KMS's refusals; 8.3 writes the statement only if one shows |
| The database's isolation level | *"To access tables in data warehouses registered to the AWS Glue Data Catalog, the database’s isolation level must be SNAPSHOT."* and *"Attempting to access tables with an isolation level of SERIALIZABLE will result in an error."* (Redshift's overview). 6h created `sandbox` with no clause (6h's log, 1.1), and its level is unread: Redshift's page on isolation levels gives *"SNAPSHOT isolation is the default isolation level when creating provisioned clusters and serverless workgroups"*, a workgroup's creation and not a `CREATE DATABASE` | a table's read once the name resolves, not the name: the failure after pass 4's | 8.6 reads it |
| The Region | Redshift's overview: *"Apache Iceberg compatibility with Amazon Redshift is available in the following AWS Regions:"*, a list that names US West (N. California) and not US West (Oregon). Every call of pass 4 succeeded in `us-west-2`, and data lake access created its managed workgroup there (`SUP-474`) | both, if the mount is what the list withholds | [`upstream-releases.md`](../upstream-releases.md)'s row, read again before the sitting; the cause left if 8.9 and 8.11 fail with the seat, the grants and any key statement in place |
| The producer's own workgroup | The overview mounts the catalogs *"on all provisioned clusters and serverless workgroups in the same AWS Region under the same account."*; `SUP-475` left a read from another warehouse unmeasured | Redshift's read alone; the managed workgroup failed the same | not separable in Sandbox, which holds one warehouse (D40) |

**How the shape fits Production, Data Governance, Sandbox and D40**:

- Pass 8 stays in Sandbox (P4): the catalog, its managed workgroup and every grant are Sandbox's, for one
  sitting.
- Production's namespace could be registered to Data Governance's catalog, since the registration names
  an account: *"`consumer-identifiers`: An array with a single element, containing the unique identifier
  of the account you’re registering the cluster or namespace to."* (Redshift's page on registering). What
  it would cost, each against a decision: the datashare registered in Data Governance is permanent there,
  `DenyLakeDeletionAndDeregistration` refusing its deregistration in the `Data` OU (Stage 9 decision 14
  (a)); data lake access creates compute, no page names the account a catalog's managed workgroup runs in
  when the namespace is another account's, and D22 keeps compute out of Data Governance; Production's
  data key would name a transfer role, decision 4 (b)'s widening of D31 in Production; and the catalog
  does not cross accounts whole: *"Cross-account sharing is not supported at the federated catalog level.
  However, you can share individual databases and tables from within a federated catalog across AWS
  accounts."* (Lake Formation's notes), under cross-account version 4, which Sandbox's settings carry.
- Redshift mounts such a catalog only in the account that holds it, *"in the same AWS Region under the
  same account"* (Redshift's overview), so Sandbox's warehouse keeps Production's rows through the Lake
  Formation-managed datashare whatever pass 8 reads.
- Pass 8 therefore changes no decision by itself. Stage 9 decision 5 stands as the user's while the
  datashare serves every Redshift reader; 9.5a's premise was read on 2026-11-23 as a Serverless workgroup
  and no cluster, under an AWS-owned key (`SUP-474`). An Iceberg engine over Production's warehouse is a
  question D40 already holds, *"A query engine is a choice per workload, not per estate"*, with `INT-24`
  naming *"a federated catalog read by Athena or a Lake Formation-managed datashare"*; pass 8's readings
  are what such a workload's decision would rest on.

**Before the sitting, with nothing up**:

- **8.1 [Claude] Pass 4's trail**, 2026-11-23 from 01:23 to 01:53 UTC, inside the event history's 90
  days: every refused call of Glue, Lake Formation, KMS, Redshift, Redshift Serverless and the Redshift
  Data API, with its caller, `errorCode` and `errorMessage`. It answers to which principal the editor's
  catalog read was refused, whether KMS refused a Redshift path, and which calls the managed workgroup
  made, as whom.
- **8.2 [Claude] The readings**: Sandbox's Lake Formation settings, saved, with their read-only
  administrators and `Parameters`; `AWSServiceRoleForRedshift`'s ARN; the data key's policy against the
  page's four statements; the access role simulated for `glue:GetCatalog` and `glue:GetTable` on the
  catalog's ARNs, expected `implicitDeny`; the Spark connection, `project.spark.fineGrained` read in
  `test-experimentation` on 2026-11-14 (`SUP-368`), listed or not in `eighth-experimentation`, and if
  only the consumer holds one, 8.8's grants name that project's role too, with the form of a session's
  `%%configure` cell on it from the portal's page; the Region list read again.
- **8.3 [Claude] The code, off by default**, merged before the sitting and planned with each switch on and
  off, the counts written here: `sandbox/warehouse/`'s `federated_catalog_read_enabled`, giving the
  producer's access role `glue:GetCatalog`, `glue:GetDatabase`, `glue:GetDatabases`, `glue:GetTable` and
  `glue:GetTables` on the account's catalog, `catalog/stage21_warehouse`, `catalog/stage21_warehouse/*`,
  `database/stage21_warehouse/*` and `table/stage21_warehouse/*`, the forms of the transfer role's
  statement and of 4.4's table ARN, with `lakeformation:GetDataAccess` only if 8.1 shows Redshift asking
  for it; and, only if 8.1 shows KMS refusing Redshift's path, AWS's `RedshiftAllowAccessPolicy` behind
  its own switch in `sandbox/data/`. The seat and the grants are calls of the sitting, as 4.2's were.

**In the sitting**: SB2 under decision 5 ([`promotion.md`](../runbooks/promotion.md) §N.12.1), whose
raise adds `redshift` for Stage 19's xiv; a JupyterLab space in `eighth-experimentation`. Each write is on
the user's word naming it, the other sessions told first and the `awsds` token's `expiresAt` read before
each plan (`SUP-465`); from 8.4 to 8.14 every plan of `sandbox/warehouse/` names its three switches
(Lessons 51, 69). The slices come before the seat, so no apply of `sandbox/data/` runs while it stands.

- **8.4 [Claude⚡] The slices**, from a `main` that holds 8.3: `sandbox/warehouse/` with the transfer role
  and the catalog read on, then `sandbox/data/` with the transfer role's key statement on (decision 4
  (b)), and 8.3's Redshift statement if it was written.
- **8.5 [Claude⚡] The seat**: the settings read and saved whole, `AWSServiceRoleForRedshift` added to
  `ReadOnlyAdmins`, and the structure written back by `put-data-lake-settings` with everything else as
  read: the call replaces the whole structure (Lesson 60), and an omitted `Parameters` resets
  `CROSS_ACCOUNT_VERSION` (`consumer-data`'s first hazard, INT-11). Read back and diffed, the seat the
  only difference; a refused put stops the pass. **[Claude] reads** `sandbox/data/`'s plan after it:
  *"No changes."* says the provider leaves an unmanaged `read_only_admins` alone, and a planned removal
  is recorded, no apply of the slice running before 8.14 removes the seat.
- **8.6 [Claude⚡] The table**: `lab.stage21_fed`, lowercase as the overview requires of a registered
  object, created and filled with three rows as the admin through the Data API; **[Claude] reads**
  `sandbox`'s isolation level. If it is not snapshot isolation, the table's read is expected to fail after
  the name resolves, and the `ALTER DATABASE` that changes 6h's database is the user's call in the
  sitting.
- **8.7 [Claude⚡] The registration and the catalog**, 4.1's commands and its reads, after 8.6's
  statements have used the namespace.
- **8.8 [Claude⚡] Lake Formation grants** to the producer's access role and its project role: `DESCRIBE`
  on `stage21_warehouse`, on its child catalog `stage21_warehouse/sandbox` and on `lab`; `DESCRIBE` and
  `SELECT` on `lab.stage21_fed`. Each read back.
- **8.9 [user] Redshift reads** `"sandbox@stage21_warehouse"."lab"."stage21_fed"` from the producer's
  Query editor, the name 4.3 used. **[Claude] reads** the same session's `svv_redshift_databases` at 0, 5
  and 15 minutes after 8.8, `governed_trades` its positive control (Lesson 62); `sys_query_history`; and
  the trail's Glue and Lake Formation calls of the minutes, their caller and any refusal.
- **8.10 [Claude⚡] Data lake access**, 4.5's update with `CatalogInput`'s fields from `get-catalog` and
  without `CustomProperties` (`SUP-474`), read back `AVAILABLE`, and `list-managed-workgroups`.
- **8.11 [user] Athena reads** the table from the producer's query editor, by the name the preview gives
  as in 4.6, then its `INSERT` of one row, expected refused under `SELECT`, the wording read. **If Athena
  answers *"does not exist"* again, the pass stops here**: no Spark and no write, 8.14 at once, and decision
  5 returns to the user with the causes left, the Region and the isolation level among them.
- **8.12 [user] Spark reads** the table in a notebook on the project's Spark connection, a Glue 5.0
  session as the project role: the extension endpoint's catalog and the standard endpoint's, each set in
  the session's configuration before its first statement, as the commands give; a `SELECT` through each,
  then an `INSERT`, expected refused. **[Claude] reads** `GetDataAccess` and the session's identity in the
  trail. A hang or an S3 refusal is read against the S3 gateway endpoint's allow-list
  (`AllowAwsOwnedServiceBuckets`, `terraform-modules/vpc/endpoints.tf`) with the bucket named, and
  nothing changes in the sitting. The session stays open for 8.13.
- **8.13 [Claude⚡] then [user] The write**: `INSERT` granted on `lab.stage21_fed` to the project role;
  one row from Athena and one from Spark; **[Claude] reads** both rows in Redshift as the admin and the
  table's files nowhere but Redshift managed storage; the grant revoked and read back; the Glue session
  stopped by hand (Lesson 81).
- **8.14 [Claude⚡] Removed in the sitting**, each read back absent: data lake access off by the same
  update, `list-managed-workgroups` empty; the grants revoked; the catalog deleted and the registration
  withdrawn in 4.8's order; the seat taken out by `put-data-lake-settings` with the structure read then,
  and the result diffed against 8.5's saved file; `sandbox/data/` with its switches off, then
  `sandbox/warehouse/` with both of pass 8's off; `lab.stage21_fed` dropped. Then the sitting's closing
  reads as in "The Sandbox warehouse sitting" item 7, with `list-managed-workgroups` empty, the settings
  equal to the saved file and no federated catalog in `glue get-catalogs`.

**After it**: **8.15 [Claude]** the bill by usage type the next day (6.5), the managed workgroup under its
own UUID (`SUP-474`) and the Glue session by its `DPUSeconds` (`SUP-368`); a `SUP-nnn` per behaviour no
page states; [`catalog.md`](../runbooks/catalog.md) and
[`redshift-connection.md`](../runbooks/redshift-connection.md) §G with the readings; D40's file and Stage
9 decision 5's row with what was read, no decision changed by them.

About 2 hours in the sitting: 20 minutes of slices and seat, 30 of table, registration and Redshift's read
with its 15-minute wait, 15 of data lake access and Athena, 30 of Spark with the session's start, 10 of
writes, and 15 of removal.

**The commands of pass 8**, in a shell that ran pass 2's first block (`S`, `A`, `q`). Every `$A` and
`$ROLE` a colon follows is braced (Lesson 84). The `jq` programs and the Spark settings are unrun.

```bash
# 8.1 pass 4's refused calls, one file per event source
mkdir -p "$HOME/tmp"
for src in glue lakeformation kms redshift redshift-serverless redshift-data; do
  aws cloudtrail lookup-events --lookup-attributes "AttributeKey=EventSource,AttributeValue=${src}.amazonaws.com" \
    --start-time 2026-11-23T01:23:00Z --end-time 2026-11-23T01:53:00Z --profile $S --output json \
    > "$HOME/tmp/s21-p8-trail-${src}.json"
done
for src in glue lakeformation kms redshift redshift-serverless redshift-data; do
  jq -r '.Events[].CloudTrailEvent | fromjson | select(.errorCode != null)
    | [.eventTime, .eventName, (.userIdentity.arn // .userIdentity.invokedBy // "-"), .errorCode,
       (.errorMessage // "-")] | @tsv' "$HOME/tmp/s21-p8-trail-${src}.json"
done
# 8.2 the settings saved whole, the role, the key, the access role's reach, the Spark connection
aws lakeformation get-data-lake-settings --profile $S --query DataLakeSettings --output json \
  > "$HOME/tmp/s21-p8-lf-before.json"
jq '{ReadOnlyAdmins, Parameters}' "$HOME/tmp/s21-p8-lf-before.json"
SLR=$(aws iam get-role --role-name AWSServiceRoleForRedshift --query Role.Arn --output text --profile $S)
aws kms get-key-policy --key-id alias/awsds-sandbox-data --policy-name default --query Policy \
  --output text --profile $S
aws iam simulate-principal-policy --profile $S \
  --policy-source-arn "arn:aws:iam::${A}:role/awsds-sandbox-warehouse-access-avhvbqn37ty7m8" \
  --action-names glue:GetCatalog glue:GetTable --resource-arns \
  "arn:aws:glue:us-west-2:${A}:catalog/stage21_warehouse" \
  "arn:aws:glue:us-west-2:${A}:table/stage21_warehouse/sandbox/lab/stage21_fed" \
  --query 'EvaluationResults[].[EvalActionName,EvalResourceName,EvalDecision]' --output text
aws datazone list-connections --domain-identifier $D --project-identifier $P --type SPARK --profile $S
# 8.4 ⚡ the slices, the transfer role and the catalog read first, then the key statement; TAG as 4.5's
# block says, 6h decision 8 (a)'s wide tag standing
TAG=true
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse plan -input=false \
  -var all_projects_tag_enabled=$TAG -var data_transfer_role_enabled=true \
  -var federated_catalog_read_enabled=true -out="$HOME/tmp/s21-p8-warehouse-on.tfplan"   # 8.3's count
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse apply -input=false \
  "$HOME/tmp/s21-p8-warehouse-on.tfplan"
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data plan -input=false \
  -var data_transfer_key_statement_enabled=true -out="$HOME/tmp/s21-p8-data-on.tfplan"     # 1 to change
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data apply -input=false \
  "$HOME/tmp/s21-p8-data-on.tfplan"
# 8.5 ⚡ the seat, the structure written back whole, read back and diffed
jq --arg slr "$SLR" '.ReadOnlyAdmins = ((.ReadOnlyAdmins // []) + [{DataLakePrincipalIdentifier: $slr}])' \
  "$HOME/tmp/s21-p8-lf-before.json" > "$HOME/tmp/s21-p8-lf-seat.json"
aws lakeformation put-data-lake-settings --data-lake-settings "file://$HOME/tmp/s21-p8-lf-seat.json" \
  --profile $S
aws lakeformation get-data-lake-settings --profile $S --query DataLakeSettings --output json \
  > "$HOME/tmp/s21-p8-lf-after.json"
diff "$HOME/tmp/s21-p8-lf-before.json" "$HOME/tmp/s21-p8-lf-after.json"            # the seat alone
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data plan -input=false \
  -var data_transfer_key_statement_enabled=true                                     # read, not applied
# 8.6 ⚡ the table, as the admin; a statement's rows as pass 2's block says
q "create table lab.stage21_fed (id integer, source varchar(16))"
q "insert into lab.stage21_fed values (1, 'redshift'), (2, 'redshift'), (3, 'redshift')"
q "select database_name, database_isolation_level from svv_redshift_databases"
# 8.7 ⚡ 4.1's block: register-namespace, describe-data-shares-for-consumer, associate-data-share-consumer,
# register-resource, create-catalog, get-catalogs and list-permissions, unchanged
# 8.8 ⚡ both roles: DESCRIBE on the catalog, its child and lab; DESCRIBE and SELECT on the table
for ROLE in awsds-sandbox-warehouse-access-avhvbqn37ty7m8 datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c; do
  PR="DataLakePrincipalIdentifier=arn:aws:iam::${A}:role/${ROLE}"
  aws lakeformation grant-permissions --principal "$PR" --permissions DESCRIBE --profile $S \
    --resource "{\"Catalog\": {\"Id\": \"${A}:stage21_warehouse\"}}"
  aws lakeformation grant-permissions --principal "$PR" --permissions DESCRIBE --profile $S \
    --resource "{\"Catalog\": {\"Id\": \"${A}:stage21_warehouse/sandbox\"}}"
  aws lakeformation grant-permissions --principal "$PR" --permissions DESCRIBE --profile $S \
    --resource "{\"Database\": {\"CatalogId\": \"${A}:stage21_warehouse/sandbox\", \"Name\": \"lab\"}}"
  aws lakeformation grant-permissions --principal "$PR" --permissions DESCRIBE SELECT --profile $S \
    --resource "{\"Table\": {\"CatalogId\": \"${A}:stage21_warehouse/sandbox\", \"DatabaseName\": \"lab\",
      \"Name\": \"stage21_fed\"}}"
done
aws lakeformation list-permissions --resource "{\"Table\": {\"CatalogId\": \"${A}:stage21_warehouse/sandbox\",
  \"DatabaseName\": \"lab\", \"Name\": \"stage21_fed\"}}" --profile $S
# 8.10 ⚡ data lake access: CatalogInput's fields from get-catalog, CustomProperties left out (SUP-474)
ROLE_ARN=$(AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse output -raw data_transfer_role_arn)
aws glue get-catalog --catalog-id "${A}:stage21_warehouse" --profile $S --output json \
  > "$HOME/tmp/s21-p8-catalog.json"
jq --arg role "$ROLE_ARN" '.Catalog | {Description, FederatedCatalog, Parameters,
    CreateDatabaseDefaultPermissions, CreateTableDefaultPermissions,
    CatalogProperties: {DataLakeAccessProperties: {DataLakeAccess: true, DataTransferRole: $role}}}
  | with_entries(select(.value != null))' "$HOME/tmp/s21-p8-catalog.json" > "$HOME/tmp/s21-p8-dla-on.json"
aws glue update-catalog --catalog-id "${A}:stage21_warehouse" \
  --catalog-input "file://$HOME/tmp/s21-p8-dla-on.json" --profile $S
aws glue get-catalog --catalog-id "${A}:stage21_warehouse" --profile $S \
  --query Catalog.CatalogProperties.DataLakeAccessProperties                   # ManagedWorkgroupStatus
aws redshift-serverless list-managed-workgroups --profile $S
# 8.13 ⚡ INSERT for the write, then revoked
PR="DataLakePrincipalIdentifier=arn:aws:iam::${A}:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"
TBL="{\"Table\": {\"CatalogId\": \"${A}:stage21_warehouse/sandbox\", \"DatabaseName\": \"lab\", \"Name\": \"stage21_fed\"}}"
aws lakeformation grant-permissions --principal "$PR" --permissions INSERT --resource "$TBL" --profile $S
q "select source, count(*) from lab.stage21_fed group by source order by source"
aws lakeformation revoke-permissions --principal "$PR" --permissions INSERT --resource "$TBL" --profile $S
# 8.14 ⚡ data lake access off, then 8.8's loop with revoke-permissions, then 4.8's block from delete-catalog
# to deregister-namespace
jq '.CatalogProperties.DataLakeAccessProperties = {DataLakeAccess: false}' \
  "$HOME/tmp/s21-p8-dla-on.json" > "$HOME/tmp/s21-p8-dla-off.json"
aws glue update-catalog --catalog-id "${A}:stage21_warehouse" \
  --catalog-input "file://$HOME/tmp/s21-p8-dla-off.json" --profile $S
aws redshift-serverless list-managed-workgroups --profile $S                                   # empty
# the seat out: the structure read now, less the role, written back, diffed against 8.5's file
aws lakeformation get-data-lake-settings --profile $S --query DataLakeSettings --output json \
  > "$HOME/tmp/s21-p8-lf-now.json"
jq --arg slr "$SLR" '.ReadOnlyAdmins = [(.ReadOnlyAdmins // [])[] | select(.DataLakePrincipalIdentifier != $slr)]' \
  "$HOME/tmp/s21-p8-lf-now.json" > "$HOME/tmp/s21-p8-lf-unseat.json"
aws lakeformation put-data-lake-settings --data-lake-settings "file://$HOME/tmp/s21-p8-lf-unseat.json" \
  --profile $S
aws lakeformation get-data-lake-settings --profile $S --query DataLakeSettings --output json \
  > "$HOME/tmp/s21-p8-lf-end.json"
diff "$HOME/tmp/s21-p8-lf-before.json" "$HOME/tmp/s21-p8-lf-end.json"      # none, or [] for an absent list
# then the key statement off, then the transfer role and the catalog read off
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data plan -input=false \
  -out="$HOME/tmp/s21-p8-data-off.tfplan"                                                 # 1 to change
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/data apply -input=false \
  "$HOME/tmp/s21-p8-data-off.tfplan"
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse plan -input=false \
  -var all_projects_tag_enabled=$TAG -var data_transfer_role_enabled=false \
  -var federated_catalog_read_enabled=false -out="$HOME/tmp/s21-p8-warehouse-off.tfplan"   # 8.3's count
AWS_PROFILE=$S terraform -chdir=terraform-live/sandbox/warehouse apply -input=false \
  "$HOME/tmp/s21-p8-warehouse-off.tfplan"
q "drop table lab.stage21_fed"
```

```sql
-- 8.9 [user], the Query editor on awsds-sandbox-warehouse, database sandbox; the list again at 5 and 15 min
SELECT * FROM "sandbox@stage21_warehouse"."lab"."stage21_fed";
SELECT database_name, database_type FROM svv_redshift_databases ORDER BY 1;
-- 8.11 and 8.13 [user], Athena, by the name the preview gives (4.6): the read, then the row
INSERT INTO <the preview's name> VALUES (10, 'athena');
```

```python
# 8.12 [user], the session's settings, given in its %%configure cell before its first statement (the cell's
# form read at 8.2): the extension endpoint as fedext, the standard endpoint as fedrest, with Glue's pages'
# keys; glue.account-id and glue.catalog-arn are the blog's lines for a session with Lake Formation's
# fine-grained access, the ARN in the form the blog writes.
account = "<account>"
conf = {
    "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    "spark.sql.catalog.fedext": "org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.fedext.type": "glue",
    "spark.sql.catalog.fedext.glue.id": f"{account}:stage21_warehouse/sandbox",
    "spark.sql.catalog.fedext.client.region": "us-west-2",
    "spark.sql.catalog.fedext.glue.account-id": account,
    "spark.sql.catalog.fedext.glue.catalog-arn": f"arn:aws:glue:us-west-2:{account}:stage21_warehouse/sandbox",
    "spark.sql.catalog.fedrest": "org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.fedrest.type": "rest",
    "spark.sql.catalog.fedrest.uri": "https://glue.us-west-2.amazonaws.com/iceberg",
    "spark.sql.catalog.fedrest.warehouse": f"{account}:stage21_warehouse/sandbox",
    "spark.sql.catalog.fedrest.rest.sigv4-enabled": "true",
    "spark.sql.catalog.fedrest.rest.signing-name": "glue",
}
spark.sql("SELECT * FROM fedext.lab.stage21_fed").show()
spark.sql("SELECT * FROM fedrest.lab.stage21_fed").show()
spark.sql("INSERT INTO fedext.lab.stage21_fed VALUES (20, 'spark')")    # refused at 8.12, admitted at 8.13
```

### The Sandbox warehouse sitting: passes 2 to 4 in order

Written 2026-11-19 with nothing up, for the Sandbox warehouse sitting the orchestrating session runs
([`promotion.md`](../runbooks/promotion.md) §N.6 item 9): `make hub-up`, then `make up ENV=sandbox
GROUPS=redshift`, which raises `sandbox/egress/`, the warehouse's compute and `sandbox/probes/` in one
apply; a JupyterLab space in each project on `ml.t3.medium`. Passes 2 to 4 follow Stage 19's pass 5 to its
5.3 (Stage 19's "The Sandbox warehouse sitting: pass 5 in order"), so 2.1 finds Stage 19's copy and 2.2 is
5.3's source, and 6h's wide tag stands, applied on day 1 (6h decision 8 (a), pull request #363). Pass 5
follows passes 2 to 4 on the sitting's day 2
(`promotion.md` §N.10.4), with a space in each project. Its
values, read that day (the log): from `main`, `sandbox/sagemaker/` plans `No changes`, and `3 to add, 1 to
change` with `redshift_serverless_enabled=true`; `data-governance/governance/` `No changes`, and `0 to add,
1 to change` (the profile `experimentation`) with it; `sandbox/warehouse/` `2 to add` with
`data_transfer_role_enabled=true` and the tag off, the counts this file's commands carry; pass 4's
commands name the tag true since 6h's standing answer, and carry the same count for a plan after 6h's step
7, read by difference. Read again on 2026-11-22 from `main` at `82edff32` with nothing up (the log):
`sandbox/sagemaker/` at `sagemaker-prereqs-v0.14.0` and `data-governance/governance/` with the same counts;
`sandbox/warehouse/` 9 to add and 2 to change with both switches true, 7 and 2 with the tag alone, the
difference `aws_iam_role.data_transfer` and its inline policy. These
`sandbox/warehouse/` counts hold since Stage 19's access-role statement (PR #339, pass 5's before it item 3)
was applied from `main` on 2026-11-20 at 15:57 UTC; before it each plan of the slice also showed
`aws_iam_policy.project_access_portal["avhvbqn37ty7m8"]` updated in place (Lesson 69). The profile
`dh60xbal05q64w` and the blueprint `dlyaabb17hano0` read as 1.3 wrote them.

**Before it, with nothing up**:

1. **[Claude] The readings** above, done 2026-11-19 (the log), and the corrections they made in place:
   pass 2's raise is one `make up`, and every plan of `sandbox/warehouse/` names both switches, since 6h
   decision 8 (a)'s tag shares the slice with 4.5's role (Lessons 51 and 69).
2. **[user] 1.3's wizard half**: the console's enable wizard for the `RedshiftServerless` blueprint read and
   cancelled on 2026-11-22, nothing to declare (the log).
3. **[user] 4.5's write path**: taken 2026-11-22, decision 4 (b): `sandbox/data/`'s key policy names the
   data transfer role for the sitting (`GenerateDataKeyDecryptDataTransferRole`, a D31 widening);
   `sandbox/data/` plans `No changes`, and `0 to add, 1 to change` (the data key's policy) with
   `data_transfer_key_statement_enabled=true`.

**In the sitting**, each slice initialised first in a tree on `main` (`./scripts/gen-backend-hcl.py
<account folder> <slice>`, `./scripts/gen-tfvars.py <account folder> <slice>`, then `init
-backend-config=backend.hcl -input=false`), and every write on the user's word naming it, the other
sessions told first:

1. **Pass 2, from 2.1**: 2.1's view and daily table over Stage 19's copy; 2.2 again as Stage 19's step 6,
   whose source of day 1 failed creation (`SUP-460`) and is deleted first, the access role's Data API reads
   applied 2026-11-22; then 2.3's publication and data product. About 25 minutes.
2. **2.4, the consumer's workgroup**: the applies in 2.4's order, sagemaker then governance; the compute
   added to `test-experimentation` in the portal; its reads. A base capacity above 4 RPUs is removed at once
   by 2.9's steps. About 45 minutes, the stack's creation included.
3. **2.5 to 2.8**: the request and the approval, the datashare read in both namespaces, the consumer's read
   from the editor and from `test-experimentation`'s notebook, the revocation, the portal's *Create table*.
   About 60 minutes.
4. **2.9, the consumer's workgroup removed**: the portal's removal, then the applies in the reverse order,
   each re-planned `No changes`; `US-3` green. About 25 minutes.
5. **Pass 3, lineage**: `lineage_reader`, its secret and the second connection, the data source with
   lineage, the statements, the graph, then 3.5's removal. About 45 minutes, the pull's five minutes
   included.
6. **Pass 4, the namespace in the Glue Data Catalog**: 4.1 to 4.4, then 4.5 with the transfer role and
   then its key statement applied, 4.6, and 4.8 at once, the key statement removed before the role. The managed compute's base capacity is unread, so 4.6's reads are the
   only queries on it; at 128 RPUs, the blueprint template's own default (1.3), a query's 60-second
   minimum costs 0.77 USD. About 75 minutes.
7. **[Claude] The closing reads**: the consumer's workgroup and the managed compute sit outside `make down`,
   `make status` and the usage limit, so before the lowering:

   ```bash
   aws redshift-serverless list-workgroups --profile awsds-infra-sandbox-1 --region us-west-2 --query 'workgroups[].[workgroupName,status,baseCapacity]' --output text
   ```

   ```bash
   aws redshift describe-clusters --profile awsds-infra-sandbox-1 --region us-west-2 --query 'Clusters[].[ClusterIdentifier,ClusterStatus]' --output text
   ```

   ```bash
   ./aws/warehouse.py awsds-infra-sandbox-1
   ```

   `awsds-sandbox-warehouse` alone, no cluster, and `WH-8` green, its extra-object check.
8. **[user] The rollback's item 5** with Stage 19's 5.4: the view `lab.trades_hot_by_desk` dropped, then the
   tables `lab.trades_hot_daily`, `lab.trades_hot_by_day`, `lab.trades_from_lake` where 3.3 created it, and
   `lab.trades_hot`; then 6h's 6.4.

About 4 hours 30 minutes of passes 2 to 4, beside Stage 19's 5.3, which they share.

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
| xxi | Which prerequisite or grant did pass 4 miss: the trail's refused calls and their callers, the read-only administrators, the data key's statements? | 8.1, 8.2 |
| xxii | With `AWSServiceRoleForRedshift` seated and both roles granted, does Redshift list the catalog's database and read its table, and after how long? | 8.4 to 8.9 |
| xxiii | Does Athena read the table through data lake access, and is its `INSERT` refused under `SELECT`, with which wording? | 8.10, 8.11 |
| xxiv | Does Spark read the table through the extension endpoint, the standard endpoint or neither, and is its `INSERT` refused under `SELECT`? | 8.12 |
| xxv | With `INSERT` granted, do Athena's and Spark's rows land in the warehouse, read by Redshift? | 8.13 |
| xxvi | What did pass 8's sitting bill, the managed workgroup and the Glue session apart? | 8.15 |

## Decisions due

The user took decisions 1 to 3 on 2026-11-17 in the cloud session's thread, one card at a time at the
user's request: decision 1 on its card at 21:55 UTC, decisions 2 and 3 in words at 21:55 UTC. At 21:50 UTC
the user set the rule the recommendations follow: *"Revise as recomendações considerando que iremos
exercitar o caminho sugerido pela AWS por padrão."* Decision 4 on 2026-11-22, in this stage's session on
the laptop. The log carries each question as it was asked and each answer in the user's words. Taken: 1
to 4. Due: 5, opened 2026-11-24 with pass 8.

1. **The consumer of a Redshift asset, and its subscription target** (2.4). **Taken 2026-11-17: (b)**, on
   the card whose option read *"Caminho documentado pela AWS: o consumidor ganha um workgroup só dele por
   uma sessão, com a capacidade base no mínimo; o warehouse do Sandbox não muda."* AWS's pages describe a
   subscription delivered to *"the Amazon Redshift Serverless workgroup created for the project"*. The
   `RedshiftServerless` blueprint, category 3 in [`docs/SMUS.md`](../../SMUS.md), is enabled for
   `test-experimentation` for one sitting through 1.5's code, its base capacity locked at 4 RPU before the
   create, and removed at 2.9; between the warehouse and that workgroup the fulfilment is the
   datashare-and-view shape. It amends D40 and D12 for the sitting, admits no second project to the
   warehouse, and turns 6h decision 8 (a)'s switch on nowhere. If the blueprint will not hold the floor, decision 1 returns
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
4. **The data transfer role on the account data key** (4.5). **Taken 2026-11-22: (b)**, the user's
   *"Ampliar na sessão"*: `sandbox/data/`'s key policy names `awsds-sandbox-warehouse-data-transfer` for the
   sitting with AWS's `GenerateDataKeyDecryptDataTransferRole`, `kms:GenerateDataKey` and `kms:Decrypt`
   under `kms:ViaService = s3.<region>.amazonaws.com`, behind `data_transfer_key_statement_enabled`, applied
   after the role and removed before it at 4.8. AWS's prerequisites page asks for the statement when a
   customer managed key encrypts the namespace, and the namespace's key is the account data key, whose root
   holds no cryptographic action (D31). It amends D31 for the sitting: a fourth reader, a service's role
   trusted by Glue and Redshift alone, whose identity policy holds no S3 action and which no bucket policy
   names, so it reads no object of `awsds-sandbox-lake`. The recommendation followed the rule of
   2026-11-17, P1 and decision 3 (b)'s measured Athena read; this file had left (a) open as a reading. Not
   taken: (a) the key policy unchanged, 4.5's reads run and a write through S3 refused, so 4.6's read
   through data lake access would likely be refused by this estate's key rather than measured on AWS's
   path.
5. **The federated catalog again, with Athena and Spark** (pass 8). **Due**, opened 2026-11-24 on the
   user's request of 14:39 UTC.
   - **Recommended: (a)**, 8.1 to 8.3 with nothing up, then the sitting in SB2: the seat, the grants to
     both roles and data lake access; Redshift, Athena and Spark read `lab.stage21_fed`, and Athena and
     Spark each write one row under an `INSERT` granted for minutes; everything removed in the sitting.
     It is AWS's documented path, the rule of 2026-11-17, and it answers the third statement by a
     measurement, inside the free trial to 2026-12-19. Its costs: `AWSServiceRoleForRedshift` reads every
     object and grant of Sandbox's Lake Formation for the sitting; the access role reads the catalog's
     metadata; decision 4 (b)'s fourth reader of the data key returns for the sitting; a table of `lab` is
     writable by the project role for minutes; about 8 USD of managed compute if the trial does not absorb
     it.
   - **The alternatives**: (b) the same without the write, 8.13 not run and verification xxv left to the
     pages; (c) 8.1 and 8.2 alone, the causes read from the trail and the estate and no sitting, so
     verifications xxii to xxvi stay unanswered and the Iceberg engines' reach unmeasured in this estate.

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
- Pass 8 (decision 5): the managed workgroup charged 23,040 RPU-seconds, 2.30 USD, for pass 4's three failed
  reads, 7,680 each, about 0.77 USD [inferred: 128 RPU for the 60-second minimum], absorbed by the free
  trial (`SUP-474`, [`docs/PRICING.md`](../../PRICING.md)); pass 8's ten queries or so, about 8 USD. A Glue 5.0 session at 0.44 per DPU-hour, 0.40 USD
  for 1,152 seconds on 2026-11-14 (`SUP-368`). The warehouse inside the trial.
- At rest: nothing new. Every object a pass creates is removed at its end, the consumer's workgroup and
  namespace at 2.9, but the assets and listings, which are metadata.

## Rollback

Each write is on the user's word, in this order, each object read before its delete.

1. **[user] The subscriptions revoked** (2.7, 5.7), then **the listings unpublished and the data products
   deleted**, in the order [`catalog.md`](../runbooks/catalog.md) §A's deletion takes.
2. **[Claude⚡] The federated catalog and data lake access** (4.8), if 4.8 did not run: the switch off, the
   catalog deleted, the registration withdrawn, `sandbox/data/`'s `data_transfer_key_statement_enabled` off
   and applied, then `data_transfer_role_enabled` off and applied.
3. **[Claude⚡] The lineage credentials** (3.5), if 3.5 did not run: the second connection by a member, the
   user dropped, the secret deleted with no recovery window.
4. **[user] then [Claude⚡] The consumer's workgroup** (2.9), if 2.9 did not run: the compute removed in
   the portal and read absent with its stack; 1.5's variables off, `data-governance/governance/` then
   `sandbox/sagemaker/` applied and re-planned `No changes`.
5. **[user] The tables and the images**: `DROP VIEW lab.trades_hot_by_desk`, then `DROP TABLE` of
   `lab.trades_hot_daily`, `lab.trades_hot_by_day` (3.3), `lab.trades_from_lake` (3.3, where it was created)
   and `lab.trades_hot` unless Stage 19 keeps its copy; the files under `shared/stage21-images/` and the
   table `stage21_images`.
6. **[user] `make down ENV=sandbox`**, every portal tab closed first
   ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D).
7. **[Claude⚡] Pass 8's objects** (8.14), if 8.14 did not run, before that sitting's `make down` (item 6):
   data lake access off, the grants revoked, the catalog deleted and the registration withdrawn in 4.8's
   order, `AWSServiceRoleForRedshift` taken out of the read-only administrators with the structure read
   then, `sandbox/data/`'s switches off and applied, then `sandbox/warehouse/`'s
   `federated_catalog_read_enabled` and `data_transfer_role_enabled` off and applied; `lab.stage21_fed`
   dropped.

## What this stage does not do

- Promote a product, or touch Production's warehouse, its datashare or its federated database.
- Build a SageMaker application: the tables come from SQL in the query editor and the files from a space.
- Keep a federated catalog, data lake access, the data transfer role's key statement, the consumer's
  workgroup, the `RedshiftServerless` blueprint, `sys:operator`, `AWSServiceRoleForRedshift`'s read-only
  seat or the access role's catalog reads past its sitting.
- Register Production's namespace, or create a federated catalog in Data Governance: pass 8 weighs the
  shape against the accounts and builds it nowhere.
- Grant the namespace's default role a policy (5b decision 5), even for 2.8.
- Enable the `LakehouseCatalog` or `LakehouseAdmin` blueprints, or create an RMS catalog (decision 3 (b)).
- Build S3 Metadata tables or an S3 table bucket: read, not built.
- Put unstructured files in the governed lake's buckets.

## What concerns the other sessions

- **Stage 19**: its pass 5 shares the warehouse sitting. Its 5.3 asset is the one 2.2 reads when it ran
  first, and its 5.4 revocation waits for pass 2's end. Pass 8 shares SB2 with its xiv, both needing the
  raise's `redshift`.
- **6h**: its decision 8 (a) stands since 2026-11-22 ([pull request
  #363](https://github.com/felipenoris/AWS-DataScience/pull/363)). From its step 7 on §N.10's day 1,
  `test-experimentation`, this stage's consumer, is in the warehouse's map under the wide tag, with no
  schema there and no portal connection to it (6h's 5.2b uses the notebook's direct door), and every plan
  of `sandbox/warehouse/` here names the tag true. Pass 2's subscription lands on the consumer's own
  workgroup; decision 1's open case, a project that adds the existing workgroup in the portal, needs no
  further admission from day 1 and stays unmeasured. Pass 3 reads a lineage run; 6h decision 3 was done
  2026-11-19, the project connection's `lineageSync` off and its database `sandbox`. Pass 8 creates and
  drops `lab.stage21_fed` in its sitting and reads `sandbox`'s isolation level; an `ALTER DATABASE` on it
  is the user's call there.
- **6d, 17, 19 and 20**: 1.5's variables ride `sagemaker-prereqs`, `sandbox/sagemaker/` and
  `data-governance/governance/`, which their applies plan too. Off by default, they plan `No changes` in
  another stage's tree; the sitting's apply is announced to the other sessions first, and `US-3` reads red
  until 2.9.
- **Stage 9**: pass 4 brings the federated catalog back in Sandbox alone, and decision 3 (b) takes 9.5a's
  reading there, the question of its verification xxiii; its decision 5 holds in Production, where nothing
  changes. Pass 8 brings the catalog back once more in Sandbox, for Athena's and Spark's reads, and
  changes neither decision 5 nor decision 14 (a).
- **Stage 11**: 6.4's threat-model entries, `sys:operator` held by a project and an S3 Access Grants
  credential that outlives its revocation; decision 4's fourth reader of the account data key, for the
  sitting. Pass 8's seat of `AWSServiceRoleForRedshift` among Lake Formation's read-only administrators and
  a `lab` table writable by a project role, each for its sitting.
- **Stage 20**: its pass 5 makes `eighth-experimentation` a consumer of Production's listing; this stage
  makes it the producer of two data products and, if 4.4 imports, a federated catalog's asset, each retired
  at the end.
- **Stage 12**: the bills of decision 1 (b)'s workgroup and decision 3 (b)'s managed workgroup, read at
  6.5 against D12, and pass 8's managed workgroup and Glue session, read at 8.15.
