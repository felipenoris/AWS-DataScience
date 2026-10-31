# Stage 19 — A data product on SageMaker Unified Studio's native path, through a SageMaker application

| | |
|---|---|
| **Status** | **Decision 6 taken 2026-10-31 by the user as (b), the AWS model** ([log](../../log/log-stage-19-smus-native-data-product.md)): *"Decido pelo modelo da AWS, com o uso previsto do SMUS e promoção entre ambientes via ferramenta SMUS CICD CLI"*. Staging and Production each gain a deployment project, the CI/CD CLI deploys every stage, and Production publishes its own product; D41 item 2 is reopened, 6f decision 4 reversed, `DenyDataZoneEntirely`'s revision trigger fired. Passes 3 and 4 rewritten the same day around [Stage 18](stage-18-staging-deployment-project.md)'s recipe, decisions 13 to 16 added, and **every decision taken the same day, one at a time**: 1 (a), 2 (a) with (d), 3 (a) gated by `PUBLISH_LISTING`, 4 (a), 5 as recommended with `eighth-experimentation` as Production's consumer, 9 (a), 11 rows by class for the governed accounts, 12 outside, 13 (b) with a subscription deny, 14 (a) with (d), 15 (a), 16 (b) against the recommendation; 7, 8 and 10 moot or amended by decision 6 (b). Nothing changed in AWS. **Written 2026-10-28, nothing run**: the plan, the review of the catalog across the plan and the estate, the user's three questions answered from measurements and dated pages, and every decision due with its recommendation. The readings of 2026-10-28 are read-only, as the infrastructure user; no apply, no AWS write, no portal act. Pass 0 runs with nothing up; passes 1 to 3 are Sandbox sittings; pass 4 runs as promotion sittings once passes 1 to 3 have run; pass 5 inside a Sandbox warehouse sitting after 4.12 |
| **Prerequisites** | [6f](stage-06f-data-governance.md) step 11, the catalog road live since 2026-10-26: `governed-lake`, its source over `curated`, one subscription fulfilled and read, decisions 1 to 5 taken (2026-10-27). `eighth-experimentation`'s `DataLake` environment (6f 11.7, `blerpkhn9nj7o0`, its database `glue_db_blerpkhn9nj7o0`) and `test-experimentation`'s (6f 2.0): a Glue table's subscription target is a `DataLake` environment's. The application template at `v0.4.6` with `scripts/dev-cli.sh` on the next tag ([Stage 8](stage-08-cicd-pipelines.md) decision 22, the waiting list), the loop from a space run on 2026-10-26 ([Stage 10](stage-10-orchestration-promotion.md) 2.1), `vpc-egress-v0.19.0`'s `mwaa` group and the `datazone` endpoint Sandbox's `egress/` carries in its `extra_services`. The Sandbox warehouse and the project's connection ([5b](stage-05b-redshift-serverless.md), [6h](stage-06h-redshift-connection.md), `EXC-17`) for pass 5. **For pass 4**: [Stage 18](stage-18-staging-deployment-project.md)'s passes 1 to 4 and 7, the recipe for a deployment project in a `Workloads` account, measured 2026-10-17 to 10-22 and unwound; the four deploy roles and the deploy runner ([Stage 8](stage-08-cicd-pipelines.md) pass 1); `staging/egress/` and `production/egress/`, each gaining a `datazone` endpoint; `data-governance/governance/` free of 6d decision 16's apply at the moment of 4.5's (Stage 18 2.7's rule: two stages never share one apply). Nothing blocks pass 0 or pass 1 |
| **Consumes** | [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D22](../decisions/D22-data-governance-account.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D40](../decisions/D40-redshift-warehouse.md), [D41](../decisions/D41-sagemaker-application.md); [Stage 18](stage-18-staging-deployment-project.md)'s measurements since decision 6 (b); [D27](../decisions/D27-catalog-maintenance.md), [D31](../decisions/D31-approver-read.md) and [D35](../decisions/D35-sandbox-cardinality.md) reviewed, none consumed |
| **Proves** | [INT-26](../integrations.md) (new): a table a workflow creates in a Sandbox project's own database becomes a published asset and a data product, another project reads it through a subscription DataZone fulfils inside one account, and the product reaches the warehouse by the path the tool intends. Since decision 6 (b): the same application promoted by the CLI into a deployment project in Staging and in Production, Production's project publishing the product and a Sandbox project subscribing across accounts, [INT-12](../integrations.md)'s association and [INT-23](../integrations.md)'s cross-account fulfilment as standing states on the `Workloads` accounts |

*Read with [`docs/GOVERNANCE.md`](../../GOVERNANCE.md) §The catalog road, [`docs/SMUS.md`](../../SMUS.md)
§The catalog surface and §The CI/CD tool, [D41](../decisions/D41-sagemaker-application.md) "Where production
runs", [6f](stage-06f-data-governance.md) step 11 and [Stage 18](stage-18-staging-deployment-project.md)
7.2, and [`runbooks/sagemaker-application.md`](../runbooks/sagemaker-application.md). The vendor sources
are the 2026-10-28 rows in [`docs/REFERENCES.md`](../../REFERENCES.md).*

---

**Objective:** exercise, by measurement, the way SageMaker Unified Studio intends a data product to be
produced and published when the producer is a SageMaker application: a data scientist builds the pipeline
in a Sandbox space; the application's workflow creates the table in the project's own Glue database and the
asset reaches the catalog by the tool's publication mechanism; the asset is packaged in a data product that
another project subscribes to through the catalog; the application is bundled and promoted with the
mechanisms the estate already has; part or all of the product reaches Redshift by the tool's path. Decide,
by measurement, which of the user's premises the estate honours in Sandbox, what Staging and Production
would need to honour them, and what each option costs.

## The premises

The user's words of 2026-10-28, which this stage is measured against:

> * cientista de dados trabalha no ambiente interativo sandbox construindo pipeline de dados que produz
>   novo produto de dado.
> * Produto de dado segue o conceito e funcionalidades pretendidas pelo SMUS para cientistas de dados.
>   Vamos exercitar sempre o caminho nativo da ferramenta.
> * Entendo que isso envolve em pipeline que, ao final, publica tabela no Glue Catalog do projeto, cadastra
>   como asset no datazone, e "empacota" em um produto de dados, a ser subcrito por outros usuários através
>   da ferramenta do DataZone.
> * Entendo que a aplicação envolve workflow que cria a tabela no glue, e procede etapa de publicação
>   (exceto se este não for o uso pretendido pela ferramenta).
> * Idealmente, empacotamos a aplicação e promovemos para os demais ambientes, sem alteração nos
>   mecanismos.
> * No plano atual, aceitamos refazer parte do procedimento do SMUS CLI "manualmente" para permitir deploy
>   em staging e production, pois foi avaliado que seria a melhor opção no momento. Agora adicionamos um
>   novo elemento: será que agora teremos que ter um portal SMUS em todos os ambientes para permitir
>   publicar produtos de dados?
> * Considerando a tabela publicada no glue catalog, eu consigo em seguida publicar no redshift? Imagino
>   que exista a opção de comandar ingestão no Redshift ou criar uma tabela externa. Gostaria de exercitar
>   o caso pretendido da ferramenta. O caso de uso é que a instituição usa o Redshift como data warehouse
>   para dados "quentes", e gostaria de publicar integralmente ou parte da informação do produto de dados
>   produzido pelo meu aplicativo SMUS na engine do Redshift.
> * Estou disposto a abrir mão de funcionalidades do Glue Catalog ou Lake Formation que, no estágio atual
>   de maturidade do SMUS, não são suportadas pelo caminho nativo do SMUS.
> * Idealmente, o que a aplicação SMUS produz não deveria implicar em execução de terraform. Ou seja, os
>   recursos da aplicação são gerenciados pelo SMUS, e as tabelas produzidas seguem os fluxos pretendidos do
>   SMUS para publicação e catalogação dos dados, sendo governado pelos fluxos padrões do SMUS, sem precisar
>   depender de terraform para criar tabelas ou bases de dados, no que se refere ao escopo dos efeitos
>   colaterais da execução de uma aplicação SMUS.
> * Permissionamento, assinatura, aprovação de acessos, idealmente ocorreriam pelo fluxo padrão suportado
>   pelo SMUS, sendo gerenciado e comandado pela ferramenta, sem precisar de execução de terraform.

The four premises every item below is read against: **P1** the tool's native path, always; **P2** a Glue
Data Catalog or Lake Formation feature the native path does not support may be given up, LF-Tags
included; **P3** an application's side effects, its tables, databases, assets and data products, need no
Terraform; **P4** permissions, subscriptions and approvals run through SMUS's own flows.

## The vocabulary this stage uses

| Term | Here |
|---|---|
| the product | one table the application writes, `trades_notional`, in the project's `DataLake` database, and the asset, listing and data product the catalog holds for it |
| the project database | the Glue database a `DataLake` environment creates under the project's `dev/data/catalogs/`: `glue_db_<environment id>` for an environment made from the configuration (6f 11.7, `glue_db_blerpkhn9nj7o0`), or the name a person chose in the portal's *Create database*, which makes one more `DataLake` environment per database (read 2026-10-28: `new_database`, environment `5i25j3k8mqz47k`, with its own daily source and no subscription target). The product's database is the second kind, one name in every project (decision 2) |
| the source | the Glue data source a `DataLake` environment creates over its database, daily, `publishOnImport` false, business-name generation off (6f decision 6, read 2026-10-20 and 2026-10-28) |
| the inventory | a project's assets before and apart from publication; a listing is the published form other projects search |
| the consumer | the project that subscribes, never a member of the owner project's, so the approval is a person's act (6f 2.1) |
| the road | `GOVERNANCE.md` §The catalog road, DataZone's named-resource grants at each approval |

## The plan and the estate against the premises

What each item does today, with its measurement or page, and what the premises do to it: keep, amend,
retire, or a decision for the user, named by its number in Decisions due. The review was read from
`main` `d4cabbb7` on 2026-10-28; the line references are that tree's.

### Decisions

| Item | Today | Under the premises |
|---|---|---|
| D13 | execution roles hold no S3 on registered prefixes; every tabular read meets Lake Formation (2026-08-07). `AllowFullTableExternalDataAccess` is `true` in Sandbox since SMUS's provisioning (2026-08-22; `TM-26`) | **keep**. P2 gives up LF-Tags, not Lake Formation: DataZone fulfils by writing Lake Formation grants (INT-23, 2026-10-22 and 2026-10-26). A full-table grantee of a Sandbox table may vend S3 credentials outside an engine: verification xi |
| D17 | people run code in Sandbox alone; `Workloads` denies the interactive surface and `datazone:*` (applied 2026-09-06) | **keep the interactive half, amend the DataZone half** (decision 6 (b), 2026-10-31): `DenyInteractiveSageMakerSurface` stands, a deployment project's `Tooling` has spaces off and creates no SageMaker AI domain (Stage 18 question i), and no person works in a target; `datazone:*` leaves the `Workloads` deny at 4.1. A member of a deployment project acts as its role in the portal (Stage 18 6.1), which decision 15's deny bounds |
| D19 | the derived zone is the SMUS project path, at the project grain, its expiry owed (open question 25, 2026-08-26) | **decision 12**: the product's table lives in that path (`dev/data/catalogs/`), so a published project table is either a product outside the zone's expiry rule or a copy inside it |
| D20 | Staging reads the lake read-only and "its catalog holds only what each deploy creates from the repository's schemas" (amended 2026-10-22, `TM-25`) | **amend** with decision 6 (b): Staging's catalog holds the deployment project's databases, and the table is what each *run* creates there under the `DataLake` environment's conditioned `CREATE_TABLE`; the application's `app_outputs` grants and `trades_notional` declaration retire (4.11); Staging holds no warehouse |
| D22 | the lake's governed write is Production's job role, `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DESCRIBE` with the grant option on `curated`, "No CREATE_TABLE: a curated table is declared in catalog.tf before its first write" (`data-governance/data/shares.tf:165-166`, applied 2026-10-22); the pilot of 2026-10-26 publishes the lake's tables from `governed-lake` | **amend** (decision 16 (b), 2026-10-31): the product lives in Production's project database, and the lake's declarations and `governed-lake`'s per-table list are untouched, but the lake's governed write passes from the job role to `deploy-production`'s project role, which loads the warehouse from `curated` (4.11); the one-enumerated-role sentence gains a dated line at 6.2 |
| D26 | one domain, a registry and never a runtime; a deployment target is never associated (6f decision 4, 2026-10-27); "the Glue + LF-Tags substrate is still built first ... so the portal is a storey, not the foundation" (its file) | **amend** (decision 6 (b), 2026-10-31): Staging and Production are associated as a standing state at 4.2, each holding one deployment project; the domain is still a registry, since a deployment project runs no space and no SageMaker AI domain, and its environments provision into the targets as the Sandbox ones do. 6f decision 4 is reversed by the same act; the substrate sentence describes the register's road alone |
| D27 | crawlers on `raw` and the drop-box, never on Iceberg; no principal can start them (open question 19) | **keep, moot here**: the engine creates the product's table and the project's source catalogues it |
| D28 | "Structure is applied rather than started: ... a governed table and its LF-Tags are declared in Terraform before the first write" and "no operator may reference a domain resource ... A workflow that only runs where the portal exists is not a promotable artifact" (its file, 2026-08-08, amended 2026-10-15) | **amend** (decision 6 (b)): under P3 a table is a side effect the workflow creates, in a project in every stage; the portal exists in every stage, so a task naming the domain and the project through the CLI's substitutions is promotable, and the promoted lint's rule against `{proj.*}`, `dzd-` and `datazone_usr_role_*` retires with the render (4.9); the per-workflow role gives way to the project role in each target, bounded by the D13 project boundary, `<env>/studio/`'s enumerated job grant and decision 15's deny; 9.4's DDL job keeps the pipeline; the warehouse workflow follows the CLI into Production's project (decision 16 (b)) |
| D31 | the approver reads through the project CMK and GitLab's gate; "which policy decides an approval" is 6f 4.3's | **keep**; decision 5 names who approves a product owned by a scientist's project |
| D35 | per-unit isolation "carried by Lake Formation grants, LF-Tags and per-pipeline execution roles"; the per-unit grant shape "arrives with the second business unit" | **amend** at N=2: P2 leaves the second option its file already names, per-account grants driven by the subscription workflow |
| D40 | the warehouse built by hand; `RedshiftServerless` and `LakehouseCatalog` excluded; the sandbox class "bypass[es] the catalog and Lake Formation"; `awsdatacatalog` read-only (2026-09-19) | **decision 9**, the Redshift leg; the blueprints stay excluded under every option but one |
| D41 | item 2, kept 2026-10-22: no project in a target; "What A gives up for now is a catalog publication and lineage from Production, and `DenyDataZoneEntirely`'s revision trigger already names that moment" | **item 2 reopened 2026-10-31** by decision 6 (b), the user's: alternative B, a project in each deployment account and the CLI deploying every stage, is built by pass 4 at Stage 18's measured price; items 5 (the chain layer) and 1, 3, 4, 6 to 8 stand; item 9 (the application slice owns the Glue job) retires for the targets, where the operator creates the job as in `dev` and `test` |

### Stages

| Item | Today | Under the premises |
|---|---|---|
| 5a | decision 5, LF-TBAC the default, "Revision trigger: Stage 6, when the DataZone fulfilment principal joins the permission plane" | **amend**: the trigger fired (INT-23, 2026-10-22; 6f 11.9, 2026-10-26) and the row is unamended; named-resource grants are the road's default, TBAC the register's. The classification scheme loses its carrier on a product with no tag: decision 4 |
| 5b | the sandbox class bypasses the catalog: "no catalog object, no LF-Tag, no Lake Formation grant"; layer 1 admits one project (`WH-7` fails on the wide tag); 2.4 `awsdatacatalog` read-only | follows decision 9; a second subscribing project hits 6h decision 8 first |
| 6a | verification xvi, "what shape is the Lake Formation grant it writes", answered by INT-23 and never marked; the deliverable "the Stage 5a lake table ... surfaced as a subscribed asset" done at 6f 11.10 | **keep as a record**; the two rows are stale |
| 6f | the road built on `curated.trades`; step 2's same-account readings (i to iv) never run; 7.2, the publish act after a deploy, unwritten; 4.3, which policy decides an approval, open | **keep**: this stage's passes 2 and 4 answer i, iii, iv and 7.2 on their own objects, and the results are cited there, not written there (the 6f session holds the stage). The 6f follow-up fixes `GOVERNANCE.md:737` and the check decision 11 names |
| 6g | 2.4's Athena read from a space, "refused rather than answered, since the project role holds no Lake Formation grant on the lake" | **closes on the road**: the subscription of 6f 11.8 is the project role's grant, read from the query editor at 11.10; the space's read is pass 2's viii |
| 6h | the connection by the portal (`EXC-17`); decision 3's `lineageSync` failing daily; decision 8, a second project, (a) the wide tag | decision 3 reopens in P1's direction (the sync is the tool's lineage, at 1.44 USD per query-hour); decision 8 goes live the day a second project needs the warehouse (pass 5) |
| 6i | the project role is the workflow's and the job's identity; the exercise wrote S3, no table | **keep**; pass 1 adds what 6i did not measure, a table created from a workflow |
| 8 | the application slice's table "declared here by the deploy role, which holds CREATE_TABLE on app_outputs" (`staging/app/app-etl/main.tf:91-92`); `lint-plan.py` fails "a plan that leaves no `aws_glue_job`"; the promoted lint's rule (a) refuses every `{proj.*}`, `dzd-`, `datazone_usr_role_*`; decision 26 the base pin | **amend** with decision 6 (b): the legs `staging-deploy` and `production-deploy` run the CLI's `deploy` from the stored bundle as the deploy role (4.9), the render, the promoted lint's rule (a) and `lint-plan`'s `aws_glue_job` rule retire with the application slices (4.11); `staging-test` reads the table in the project database (decision 14); the gates, `store-bundle`, `staging-gate` and `production-gate` stand |
| 9 | 2.1's write grant without `CREATE_TABLE`; 9.5's datashare across Production, Data Governance and Sandbox, and 9.7's read through the access role's grants (2026-10-25); decision 13's flag (`TM-26`); decision 15's Production-only load | 2.1 untouched under decision 6 (b); 9.5 to 9.7: decision 9; the flag: SMUS's provisioning sets it `true` in any account that gains a project (Stage 18 3.3), so Production's flag, off since 2026-10-25, comes back on at 4.6 and 4.7 turns it off again and reads what needs it (verification xx); decision 15's load workflow moves into Production's project and runs as its role (decision 16 (b)): 9.3's grants repeated for that role's `IAMR:` user, 9.5's datashare re-read over the objects that user owns, the 5439 ingress from the project's security group (4.11) |
| 10 | 3.3, MWAA Serverless emits no lineage of its own, a Glue job posts its own through a `datazone` endpoint, "Production cannot post at all" (decision 9, none for now); decision 6's render table drops `{proj.*}` and the project tag; 1.1, 2.4 and 4.2 kept by Stage 18's verdict | **rewritten around the CLI** (decision 6 (b); Stage 18 4.5's table says what the CLI does of each): 1.1's workflow resource, 2.4's versioned home and 4.2's API rung retire for application workflows, which the CLI creates in the project; the chain layer (3.4 to 3.7) stands and starts the CLI-made workflow by its composed name with KMS on the project key (Stage 18 0.4, vii); 3.1's failure rule stands; decision 9 is amended, Production's Glue job posting its lineage through the `datazone` endpoint 4.4 adds; the render table retires. The rewrite is the Stages 8-10 session's (What concerns the other sessions) |
| 11 | `TM-17` open; decision 12's data cells filters create nothing; `TM-25` to `TM-27` accepted | decision 12's native form is the approver's row and column filter at subscription (`SMUS.md`, read 2026-10-27), unrun; `TM-27` is written for lake tables and the product road needs its own entry (step 6.3) |
| 16 | the sandbox lake holds "no catalog registration" and no LF-Tag | **keep**: not a product's home; its graduation norm gains the catalog as a second exit |
| 17 | `EXC-11`, the `Tooling` model-package sources failing daily (77 runs on 2026-10-28); 7.4c's reading deferred to "a stage that owns governed data in Sandbox" | `EXC-11` is the first scheduled run P1 meets and does not depend on; 7.4c lands here (verification xi) |
| 18 | alternative B measured in Staging 2026-10-17 to 10-22, D41 item 2 kept; 7.2's table created by the Glue job's session under the conditioned `CREATE_TABLE`, imported by `start-data-source-run`, published by `create-listing-change-set`, subscribed across accounts | **the recipe pass 4 follows** since decision 6 (b): passes 1 to 4 and 7 built as standing states in both targets, pass 8's order the rollback; its costs, listed under decision 6, are accepted by the decision |

### Documents

| Item | Today | Under the premises |
|---|---|---|
| `GOVERNANCE.md` §Catalogs, §Access control, §Grants | "A publish writes to the third column only"; TBAC the default, named grants "for the exceptions"; a grant is a triple registered one row per grant | **amend** at close (step 6): the road's named grant is the product's default; the register carries fulfilments by class since 6f decision 2 |
| `GOVERNANCE.md` §LF-Tags, §Assigning the LF-Tags | "An untagged curated table ... is invisible to the default grants"; "A curated table exists before its first write"; "The rite below is designed and not yet exercised" (stale: `curated.trades` written 2026-10-23) | **decision 4** for the carrier; the rite's table declaration retires for a product under P3 and decision 6 (a); its publisher-list act stays under (a2) and retires under (a1) |
| `GOVERNANCE.md` §The development cycle | nodes 4, 7 and 8: the register, TBAC readers, the governed table published after Production; line 737 "until a lake table is published" (stale since 2026-10-26, the 6f follow-up's) | **amend** at close: publication at node 2, consumers through subscriptions |
| `GOVERNANCE.md` §Publishing and sharing | "Staging and Production are never associated (D26), so a deployment target neither publishes nor subscribes" | **rewritten** at close (decision 6 (b)): a deployment project publishes what its runs create and approves what Sandbox subscribes to; it subscribes to nothing (decision 14) |
| `SMUS.md` §The catalog surface, §The CI/CD tool | the road's readings of 2026-10-26/27; the CLI "deploys only into projects that already exist"; no `data product`, `subscription target`, `awsdatacatalog` or Redshift asset anywhere | **amend** at close with pass 2's product readings, the targets read 2026-10-28, and pass 5 |
| `architecture.md` | "nothing is ever provisioned into the domain account itself" (stale since `governed-lake`, 2026-10-26); no warehouse in the tree | **amend** at close |
| `threat-model.md` | `TM-17` open; `TM-25` presumes tags on what Staging reads; `TM-26` the Sandbox flag; `TM-27` the road's residual for lake tables | step 6.3 writes the product road's entry; `TM-17` gains weight (the project role is the product's every hand) |
| `AWS_STATE.md` | the register by class since 2026-10-27; "The grants SMUS-managed principals hold in Sandbox are not rows" (`CT-7`, `CT-8`); `EXC-17`'s trigger names a Terraform shape for a second connection | **decision 11** on the product's register; `EXC-17`'s trigger amended under P1 |

### Runbooks

| Item | Today | Under the premises |
|---|---|---|
| `sagemaker-application.md` §B, §K, §N | the four-step rite for "publishing a product in the lake", line 1140 "its shape open"; §K "no project role holds a grant"; §N "the lake only once the project role holds a grant" | the three stale lines are corrected in this stage's pull request (6f decision 1 and 11.8-11.10); the rite retires for a product under decision 6 (a), step 6.2 |
| `sagemaker-application.md` §M, §W, §D, §G | the manifest without `catalog`; the render table and its classes (`tables` exists); the loop from a space; the project-side Glue task | **keep and extend**: a `{env.PRODUCT_DATABASE}` variable, a publishing task, `content.catalog` (pass 3), the Iceberg write into the project database |
| `redshift-connection.md` | §J the notebook's connection; §G the governed share through the access role's grants (Terraform, SQL, an administrator's grant); `awsdatacatalog` "runs as the namespace role, which holds no policy at all (5b decision 5), and `WH-1b` keeps it that way" | **decision 9**; §J reused as written |
| `serverless-workflows.md` | the worker: Python 3.12, boto3 1.43.1, no internet, no proxy, the seven injected variables (`DataZoneDomainId`, `DataZoneProjectId` among them); the code archive; `EnableNetworkIsolation: true` on a processing job | **keep**: the publishing task is a `PythonOperator` on the worker, never a processing job |
| `sandbox-lake.md` | nothing catalogued, no LF-Tag | **keep**, the bucket out of this stage |

### Code, policies, instruments

| Item | Today | Under the premises |
|---|---|---|
| `examples/app-etl/` | `manifest.yaml` with `storage` and `workflows`, no `catalog`; `transform.py`'s `write_table` writes Parquet by path, no catalog call; no task touches the catalog; `render-workflow.py` removes keys, never a task; `test-deploy` empties the `test` project's `app-etl/` prefix before each deploy | **amend** (pass 1, decisions 1 to 3, 8): the Iceberg write into `{env.PRODUCT_DATABASE}`, the publishing task, the render's task-drop rule, `content.catalog`; a table registered in `test`'s catalog survives the prefix's emptying |
| `data-governance/data/` | `curated.trades` declared with `open_table_format_input`, tagged `internal`; `publishing.tf`'s per-table list and precondition; the write share without `CREATE_TABLE` | **untouched** (decision 6 (b)): the product never enters the lake; the lake road and the product road run side by side, `catalog.py` judging both (decision 11) |
| `<env>/data/` | `app_outputs`; `CREATE_TABLE` to the deploy role, the job role `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DESCRIBE` | decision 6 (b): the application's grants on `app_outputs` retire at 4.11, where the job role's remaining grants are read (decision 16 (b)) |
| `<env>/app/app-etl/` | `aws_glue_catalog_table.trades_notional`, Parquet, byte-identical in both targets (`check-copies.py`) | decision 6 (b): the slice retires at 4.11, table and Glue job both, the operator creating the job in the project as in `dev` and `test` (Stage 18 4.4); `check-copies.py` loses the pair |
| `terraform-modules/orchestration/` | the per-workflow role's five Glue job actions, no `glue:*Table*`, no `datazone:`, no `redshift` | **amend** (decisions 6 (b) and 16 (b), the Stages 8-10 session's): the workflow resource and its per-workflow role retire; the chain's machine takes a workflow name, and the chain role gains `kms:GenerateDataKey` and `Decrypt` on the project key (4.11) |
| `DenyDataZoneEntirely` | `datazone:*` denied on `Workloads`, no condition; "Revision trigger: the first time Production must publish a data product of its own" (`POLICIES.md:119`) | **the trigger fired 2026-10-31** (decision 6 (b)); the statement is revised at 4.1 in the shape decision 13 picks; the root's `datazone:CreateDomain` deny outside the `Data` OU and the Data OU's denies keep (`governed-lake` can hold no pipeline: `glue:CreateJob`, `StartJobRun` and `athena:StartQueryExecution` denied there) |
| `aws/catalog.py` | `CT-10` to `CT-12` judge lake listings alone; `CT-7` passes a project-owned grant; `CT-4` fails any `publishOnImport`; no check reads an inventory | **amend** (step 6.1): the product road's checks, decision 11 |
| `aws/datalake.py`, `aws/studio.py` | no check fails on a new database or table; environments never read; `US-3` admits the pilot's `Tooling` | **keep**; `studio.py` gains the environments and targets reading (step 6.1) |

## The user's questions, answered

**1. Is a workflow task that creates the Glue table and then publishes it the tool's intended use?**
Half of it. The table: yes, the engine that writes creates it. On 2026-10-22 a Glue job started by a
workflow in Staging's project, running as the project role in a `GlueJobRunnerSession` with no source
identity, wrote Parquet with `saveAsTable` and the trail holds one `glue:CreateTable`, admitted by the
`CREATE_TABLE` that the `DataLake` environment grants `IAMPrincipals` under
`context.datazone.projectId` (Stage 18 7.2 step 1); the same conditioned grants stand on
`glue_db_blerpkhn9nj7o0` on 2026-10-28 (`CREATE_TABLE`, `DESCRIBE`, `DROP` on the database; `ALTER`,
`DELETE`, `DESCRIBE`, `DROP`, `INSERT`, `SELECT` on its tables). The workflow editor's Glue Catalog Create
Table operator is the Amazon provider's `GlueCatalogCreateTableOperator` (provider 9.28.0; one of the
*"19 new operators"* of 2026-07-08; the MWAA Serverless operators page lists it in its Catalog family
beside `GlueCatalogCreateDatabaseOperator`, `GlueCatalogDeleteTableOperator` and the crawler operators,
read 2026-10-28): `database_name`, `table_name`, `table_input`, `catalog_id`, `if_exists` (`fail` or
`skip`), and its `execute` passes `DatabaseName`, `TableInput` and `CatalogId` alone to `create_table`,
so the `OpenTableFormatInput` Glue's `CreateTable` takes beside `TableInput` never travels: it registers
a table over files and cannot create an Iceberg table from nothing; a job's DDL can. The publication: the
tool's mechanism is the data source, not the task, and the operators page's ten families hold no
DataZone, listing or publish operator. A source's run imports the database's tables into the project's inventory
(`start-data-source-run` on 2026-10-22, one asset in 2 s; the schedule on 2026-10-27, which imported the
subscription's resource link), and a listing is a separate act, *Publish* in the portal (2026-09-13,
2026-10-26) or `create-listing-change-set --action PUBLISH` by API (2026-10-22, `ACTIVE` in 9 s), unless
the source's `publishOnImport` makes every import a publication (AWS's data-source page, read 2026-10-28:
*"Yes – assets are added to the project's inventory and published to the Amazon SageMaker Catalog"*; the
metadata page: *"If you didn't choose to publish assets automatically when you created the data source,
open the asset's details page and choose Publish asset"*). Who may: *"To curate, publish, or unpublish an
asset, you must be the owner or a contributor of the project the asset belongs to"*, and the project role
is a contributor of its own project (6f decision 5, 2026-10-18). No workflow operator publishes. So the
intended shape is: the job writes and registers; the source imports; the listing is published by a
person, by `publishOnImport`, or by the API (`CreateListingChangeSet`, `action PUBLISH`, `entityType
ASSET` or `DATA_PRODUCT`; `StartDataSourceRun` takes the identifiers and a token alone), which a
`PythonOperator` task can call as the project role, whose managed policy allows `CreateListingChangeSet`
(6f decision 5's simulation, 2026-10-18) and whose `StartDataSourceRun` is verification ii. A data
product is a person's packaging act on published or unpublished assets: *"Any unpublished data assets
that are in this data product will become published, but will only be available through this data
product"*, subscribed *"with a single request"*, granted by the owning project, its subscribers' access
following each republication. The recommendation is the task, with `publishOnImport` left off (decision
3): a source that publishes on import also publishes what it imports from a subscription, and `CT-4`
reads it as a failure.

**2. Does publishing data products natively need a SMUS project in Staging and Production?** For a
table that lives in Staging's or Production's own catalog, yes. Every path AWS documents for publishing a
table puts a project in the table's account (Stage 18 7.2's reading of 2026-10-17); the Glue data source
reads the project's own catalog through the project's connection with the project role as its
`dataAccessRole` (read 2026-10-28); a resource link cannot be subscribed to (the troubleshooting page,
2026-10-17); the CLI deploys into projects alone, every stage naming one (`upstream-releases.md`); and
`DenyDataZoneEntirely` denies `datazone:*` to every principal of `Workloads`, with no condition. A
project there means the account's association, which reopens D41 item 2, D26's "never associated", the
statement's revision trigger, 6f decision 4 and the price Stage 18 measured: `datazone:*` carved out for
good; the two SMUS roles seated as the account's Lake Formation administrators by a full replace of its
settings and `AllowFullTableExternalDataAccess` turned on (3.3, 2026-10-19); one project role under
AWS's managed policies in place of D28's per-workflow role, which every member acts as (6.1); the
workflow outside Terraform's state, its log groups never expiring, the Glue job the operator's (4.5); a
shared root where two applications' names collide (5.1 to 5.3); a subscription that shares the
producer's whole catalog through RAM and writes its Data Catalog resource policy (7.2); the residues a
teardown leaves (8.1 to 8.6); USD 1.52 for the window. The design that honours the premises without a
portal in every environment makes the lake the promoted product's home: Production's job creates the
table in `curated` (a `CREATE_TABLE` on the database to the job role, one declaration for every future
table, not one per table), `governed-lake`'s source over `curated` imports it on its schedule, and the
Governance Manager publishes it, the act 6f 7.2 owes an automation; the publisher's grant stays per
table, one `data-governance/data/` apply per product carrying its tag, or moves to the database grain
at the cost decision 6 states (6f decision 2's plan-time refusal turned into `CT-12`'s detection, the
`restricted` column of `sample_trades` grantable, the publishing role's unconditioned regrant reaching
every `curated` table before it is classified). Staging's copy stays unpublished,
read by the integration test in `app_outputs` as today. The consumer side is unchanged: a Sandbox
project subscribes and the owner approves. That is decision 6, recommended as (a). **Taken 2026-10-31 by
the user as (b)**, the AWS model: a deployment project in each target, the CLI deploying every stage,
Production publishing its own product, at the price this paragraph lists; pass 4 is its plan.

**3. How does the tool intend a product published from the Glue catalog to reach Redshift?** Not by a
fulfilment: SMUS fulfils a *Glue* asset into the subscriber's `DataLake` database and a *Redshift* asset
into the subscriber's Redshift (grants on the source table in the same database, a datashare and a view
across workgroups, an authorized datashare across accounts; the grant-access-to-redshift-asset page,
read 2026-10-28), never a Glue asset into Redshift storage. What the pages carry end to end inside the
tool is the read in place: the subscribed table "appear[s] in the AWS Glue Data Catalog as resources in
your account" and "You can then use Amazon Athena, Amazon Redshift, or Spark to query the tables"; a
Redshift Serverless workgroup mounts the Data Catalog as `awsdatacatalog`, read-only, reached as a
federated user with `USAGE` on it, Lake Formation vending the credentials and managing permissions "by
database user (IAMR:username)"; Redshift Serverless runs data lake queries on its own compute, Iceberg
v1 to v3, with no Spectrum charge. Making the data hot is then SQL in the warehouse: `CREATE TABLE AS`
or `INSERT INTO ... SELECT` from the Iceberg table ("You currently cannot use the COPY command to ingest
the contents of an Apache Iceberg table"), or a materialized view over the data lake table, which
Redshift maintains incrementally on Iceberg and, as an Iceberg materialized view, registers in the Glue
Data Catalog "making it discoverable by other engines", refreshed by hand; "Changes in permissions
managed by Lake Formation are not verified on querying a materialized view". A Redshift table made that
way is published as a `RedshiftTableAssetType` by a Redshift data source on the project's connection and
subscribed with a datashare, the tool's own flow for Redshift assets, whose subscriber needs a Redshift
subscription target: the `RedshiftServerless` blueprint's environment (D40 excludes it) or a custom
environment's target with a secret and a workgroup (`CreateSubscriptionTarget`, `AUTOMATIC` or
`MANUAL`). Nothing in this estate holds one: `eighth-experimentation`'s targets serve Bedrock models,
feature groups, model package groups and Glue tables, none `RedshiftTableAssetType`, its Redshift
connection notwithstanding (read 2026-10-28). Zero-ETL takes no S3, Iceberg or Glue-catalog source
(Redshift's and Glue's zero-ETL pages); COPY takes Parquet files, not an Iceberg table; the Region
list on Redshift's Iceberg-integration page, where a namespace registered as a federated catalog is
mounted as an external database, does not name `US West (Oregon)` (read 2026-10-28), and
`glue get-catalogs` answers an empty list in every account with a profile. Under D12 every path bills the
warehouse's compute alone: 0.36 USD per RPU-hour, 1.44 per query-hour at 4 RPU with a 60-second
minimum, data lake queries included, 0.024 per GB-month for what the copy stores; no zero-ETL fee; the
trial absorbs Sandbox's to 2026-12-19. What stands between the read in place and this estate is 5b
decision 5: the namespace role holds no policy and `WH-1b` keeps it so, while a federated user's read
of `awsdatacatalog` needs Lake Formation grants held by the database user's identity, which the
subscription's grant to `IAMPrincipals` under the project's context reaches only if that session
carries the context, unmeasured (9.7 needed a named grant on the access role). That is decision 9.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, run only after the user authorizes that action in chat, the other sessions on the laptop told first |
| **[user]** | the portal, a space, the console, and every decision |

## 0. What is already measured

- **0.1 A table created by a workflow's job lands in the project database under the conditioned
  grant** (Stage 18 7.2 step 1, 2026-10-22): `saveAsTable` with `--enable-glue-datacatalog`, one
  `glue:CreateTable` by the project role's `GlueJobRunnerSession`, `MANAGED_TABLE` under
  `dev/data/catalogs/`, no refusal. The grants on `glue_db_blerpkhn9nj7o0` read 2026-10-28 are the same
  shape; the provisioning role holds `ALL` with the grant option, the manage-access role `CREATE_TABLE`
  and `DESCRIBE` on the database and `DESCRIBE` and `SELECT` on its tables.
- **0.2 The source imports and the listing is a separate act** (Stage 18 7.2 step 2, 2026-10-22; 6f
  11.6, 2026-10-26; the schedule of 2026-10-27). A run's session is DataZone's `SYSTEM` on the project
  role, calling `glue:GetDatabase`, `GetTables` and `lakeformation:GetResourceLFTags`.
- **0.3 A same-account subscription has never been fulfilled here** (6f step 2 unrun); across accounts
  the fulfilment acted as each side's project role (Stage 18 7.2; 6f 11.9), and the manage-access role
  holds the Glue manage-access policy since 2026-10-20 (6f 0.10).
- **0.4 A data product exists and was never subscribed**: `my-data-product`, one item, revision 1,
  listing `czt1j8ttwsl8r4`, no subscription (2026-09-13; read 2026-10-28).
- **0.5 The consumer's daily source imports what it subscribed to** (2026-10-27 21:32 UTC): the
  resource link `trades` is an inventory asset of `eighth-experimentation`, unpublished. A re-listing
  would expose the table's metadata, not its rows: the fulfilment grant carries no grant option and a
  resource link cannot be subscribed to (the 6f session's reading of 2026-10-28, inferred).
- **0.6 No Redshift subscription target exists in any environment**, and no federated catalog in any
  account (2026-10-28); the warehouses' namespaces attach one role each, `awsds-<env>-warehouse-exec`.
- **0.7 Sandbox's `egress/` carries the `datazone` interface endpoint** in its `extra_services`, so a
  worker reaches DataZone with no proxy and no internet (`serverless-workflows.md`); Staging needed one
  added for the window (Stage 18 7.1).
- **0.8 The roster grew**: 24 managed blueprints and 24 managed asset types on 2026-10-28, one more of
  each than 2026-10-18's 23 (`SageMakerAIDomain` in `docs/SMUS.md`'s table since 2026-10-30;
  `S3TableBucketAssetType`, `SageMakerUnifiedStudioScheduleAssetType` and
  `SageMakerUnifiedStudioDataQualityRulesetAssetType` are in no document). Step 6.2 writes them.
- **0.9 The CLI 1.0.9 carries the catalog between projects and creates no table** (its installed code,
  read 2026-10-28). `content.catalog` takes `enabled` (*"ALL project-owned catalog resources are
  exported during bundle"*: glossaries, terms, form types, asset types, assets, data products),
  `skipPublish`, `connectionName` and `assets.access`, a list of listings the deploy requests a
  subscription to (`create_subscription_request` as the target project); a stage may set
  `catalog.disable`. `deploy` creates each resource in the target in that order and publishes those whose
  source listing was `ACTIVE`, polling the listing for 30 s: *"The create_listing_change_set API is
  asynchronous — it returns success even if the listing ultimately fails (e.g. missing Glue table)"*,
  and the guide: the import *"assumes that the underlying physical resources (e.g., Glue Tables, Glue
  Databases, S3 buckets) referenced by your catalog assets have the same name in both source and target
  environments"*. The asset's `DataSourceReferenceForm` is remapped to a target source whose filter names
  the same database, else stripped. No `create_table` and no `OpenTableFormatInput` anywhere in the
  package; its clients use boto3's default credentials, no role assumption. The README's *"Stage projects
  can belong to different SMUS domains, AWS accounts, and regions"* therefore rests on the caller's
  credentials.

## To execute

### 1. The product in `dev`: the table by the workflow, the asset by the source

A Sandbox sitting: `make hub-up`, `make gitlab-up` if the tag pipeline runs, `make up ENV=sandbox
ONLY=egress GROUPS=mwaa`, the deploy from a space through `scripts/dev-cli.sh`
([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §D). Decisions due 1 to 3 first.

- **1.1 [Claude] The application change, on a branch of `awsds/app-etl`** (decision 1): `transform.py`'s
  `write_table` writes the result as an Iceberg table into `{env.PRODUCT_DATABASE}` through Spark's
  catalog (`saveAsTable` with the Iceberg catalog `--conf` the targets already pass, the job's
  `--datalake-formats iceberg`), keeping the Parquet path for the processing task's input; the manifest's
  `environment_variables` gain `PRODUCT_DATABASE`, the one name decision 2 fixes, which the user creates
  in `dev` and in `test` through the portal's *Create database* before the first deploy (1.2's first
  act); `code/app_etl_tasks.py` gains `publish`, a `PythonOperator` task
  after `write_result`: it reads `DataZoneDomainId` and `DataZoneProjectId` from the worker's variables,
  finds the source whose filter names the database (`list-data-sources`), starts its run
  (`start-data-source-run`), waits for `SUCCESS`, finds the asset whose external identifier names the
  table (`search` on the inventory) and publishes its latest revision (`create-listing-change-set
  --action PUBLISH`); every call as the project role, through the `datazone` endpoint; the task returns
  at once where the stage variable `PUBLISH_LISTING` is not `true` (decision 3, 2026-10-31). The tests
  gain a catalog double, and `make check` passes; decision 8's render rule is moot since decision 6 (b).
- **1.2 [user] Create the product's database in `dev`** (*Data → Create database*, the name of decision
  2), **deploy to `dev` from a space** and run `app-etl`. **[Claude] reads** the new `DataLake`
  environment, its database, its daily source and whether it carries a subscription target (the one of
  2026-10-28 carries none); then the job's
  `glue:CreateTable` in Sandbox's trail, its session and the grant that admitted it, the table's format
  (`TableType`, `table_type` Iceberg, `IsRegisteredWithLakeFormation`) and location (verification i);
  the worker's `StartDataSourceRun` and `CreateListingChangeSet`, their `sourceIPAddress` the endpoint's
  and the policy that admitted each, or the refusal's wording (ii); the run's statistics and the asset's
  forms, the listing `ACTIVE` with `approvalRequired`, the `DataSourceReferenceForm` (iii); the
  lineage nodes and events, if decision 10 turned the job's OpenLineage settings on (v).
- **1.3 [user] The asset's business metadata in the portal**: a description, decision 4's form, a
  README. **[Claude] reads** what the forms hold and `CT-2` to `CT-6` on the new objects.
- **1.4 [user] Run `app-etl` a second time.** **[Claude] reads** whether the second run re-creates or
  overwrites the table, what the source's run reports (`updated`, `unchanged`) and whether the listing
  gains a revision: the product's idempotence.

### 2. The data product and the subscription

- **2.1 [user] Package the product**: in `eighth-experimentation`, *Data products → Create*, name
  `trades-notional`, the asset `trades_notional` as its item, a description, then *Publish*. **[Claude]
  reads** `CreateDataProduct` and the listing change set, the product's listing and its items.
- **2.2 [user] Create the consumer** (decision 5): a project from `experimentation`, and in it a
  `DataLake` environment from the profile's configuration, 6f 11.7's form (`create-environment` as
  `awsds-infra-sandbox-1`, a contributor, [Claude⚡] on the user's word), since a Glue table's
  subscription target is that environment's (6f 0.9) and a database made by *Create database* carried no
  target on 2026-10-28. **[Claude] reads** the environment, its target's `databaseName` and its daily
  source.
- **2.3 [user] Subscribe to the data product from the consumer, and approve in `eighth-experimentation`**
  as the owner decision 5 names. **[Claude] reads** verification vi (the writer, the grant's form and
  principal, the resource link, the times) and vii (one approval, every item).
- **2.4 [user] Read from the consumer**: the query editor on *Athena (SQL)* with no space, then a space's
  Spark session on the `project.spark.fineGrained` connection. **[Claude] reads** `GetDataAccess` and
  the bytes scanned (viii), and attempts, as the consumer's role from the space, a `GetObject` on the
  table's folder, D13's negative (xi).
- **2.5 [user] Revoke the subscription** in the owner project. **[Claude] reads** every piece gone, and
  whether a session opened before the revoke still reads (ix).
- **2.6 [Claude] The consumer's inventory the morning after**: whether its daily source imported the
  resource link (0.5's shape, x).

### 3. The bundle and `test`

- **3.1 [Claude] The manifest gains `content.catalog`** (`enabled` true, `connectionName`
  `project.default_lakehouse`, `skipPublish` false; 0.9): `bundle` then exports every catalog resource
  `dev` owns, the product's asset and data product among them, and `deploy --targets test` creates them
  in `test` and publishes the ones published in `dev`. The order the CLI runs is read in its code first
  (pass 0): the bootstrap's `workflow.run` must have created the table in `test`'s database of the same
  name before the listing, or the listing fails asynchronously and the deploy counts a publish failure.
  The lint's rule that refuses content from outside the tag is read against a `catalog` item that names
  no file ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §M).
- **3.2 [user] Create the product's database in `test`** (the same name), then **tag the application**;
  the pipeline's `test-deploy` bundles and deploys to `test` (Stage 8 2.5). **[Claude] reads** the
  bundle's `catalog/catalog_export.json`, the import's calls in the trail as `awsds-deploy-sandbox-test`
  (`CreateAsset`, `CreateDataProduct`, `CreateListingChangeSet`, any `AddPolicyGrant` the import adds to
  the root domain unit for `CREATE_GLOSSARY`, `CREATE_FORM_TYPE` and `CREATE_ASSET_TYPE`, which `CT-9`'s
  neighbours would read), and what `test` holds after: the table from the run, the asset with its
  `DataSourceReferenceForm` remapped or stripped, the product, the listing `ACTIVE` or failed (xii), and
  whether the project's own source, run after the import, updates the imported asset or creates a second
  one over the same table (xvii), the reading decision 14 rests on.
- **3.3 [Claude] The manifest gains the `staging` and `prod` stages** (decision 6 (b); Stage 18 4.1's
  form): each names the domain, its deployment project (`deploy-staging`, `deploy-production`), the
  stage's variables (`STAGING_*` and `PROD_*`, the project's subnets, security group and key read from
  its `Tooling` environment, `JOB_IMAGE_URI` by digest, `PRODUCT_DATABASE`), and the bootstrap of
  decision 14: `workflow.create` for each workflow, `app-etl-warehouse`'s in the `prod` stage alone
  (decision 16 (b)), `workflow.run` of `app-etl` with `trailLogs` in Production so the table exists
  before anything lists it. Stage 18 7.1's rule holds: every variable a
  workflow names is defined in every stage, so a workflow posting lineage carries the account in each.
  `.gitlab-ci.yml`'s legs change with it (4.9). Written on the branch of decision 1, lint-checked in the
  promoted mode until 4.9 retires that mode; nothing deploys to a target before pass 4.

### 4. The promoted product: a deployment project in each target, the CLI deploying every stage

Decision 6 (b), taken 2026-10-31. [Stage 18](stage-18-staging-deployment-project.md) built this shape
in Staging from 2026-10-17 to 10-22 and unwound it; this pass builds it in both targets as a standing
state, in Stage 18's order, each step citing the Stage 18 step whose measurement it repeats. Decisions
13 to 16 were taken on 2026-10-31. The sittings are promotion sittings ([`runbooks/promotion.md`](../runbooks/promotion.md)
§N), coordinated with the session holding Stages 8-10, whose objects 4.9 and 4.11 change. Production is
touched for the first time at 4.2: every reading Stage 18 made in Staging is made again there, since
the shape is the templates' and the account's own state is not.

- **4.1 [Claude] The SCP**: `DenyDataZoneEntirely` revised in `awsds-org-scp-ou-workloads.json` in the
  shape decision 13 took, the `ArnNotLike` exceptions for the three identity patterns and the new
  statement denying `datazone:CreateSubscriptionRequest` to every principal of `Workloads`;
  `POLICIES.md`'s row rewritten (the trigger, fired, becomes the record of this stage) and the new
  statement's row added; the battery's rows turned: `workloads: datazone:ListDomains` from `prod` and
  from Staging read `allow` as the infrastructure user, the deny half read as the canary under the
  candidate document on `Policy Test`, a `CreateSubscriptionRequest` row denied there, and the root
  baseline's `datazone:CreateDomain` row keeps its deny ([`scp-battery.md`](../runbooks/scp-battery.md)
  phase 4b).
  **[user]** applies `identity/org-policies/` as `awsds-infra-identity` from the saved plan, one
  in-place update of the `Workloads` document (the classifier refused Stage 18's SCP apply to Claude,
  1.3); **[Claude] reads** the re-plan, `./aws/org-policies.py`, the battery's phase `ou` and, from
  `awsds-infra-prod` and `awsds-infra-staging`, `datazone list-domains` answering (xviii). `AWS_STATE.md`
  gains the invariant that replaces `EXC-20`'s window: both `Workloads` accounts associated, each
  holding one project from `deployment`.
- **4.2 [user] Associate `Staging Account` and `Production`** in the console, Stage 18 2.1's path: the
  Infrastructure User, account **Data Governance**, permission set **`InfrastructureAccess`**, Amazon
  DataZone → `awsds-studio` → Account associations. **[Claude] reads** 2.2's: from each account
  `list-environment-blueprint-configurations` answers an empty list where it answered
  `UnauthorizedException`; RAM's share holds four principals; `./aws/studio.py` reads the two accounts
  associated (`US-2`, its Workloads rule inverted). D26 carries the dated amendment; the note on 6f
  decision 4 is the 6f session's to write, that stage being its.
- **4.3 [Claude] The lists**: `SMUS_ASSOCIATED` gains `staging` and `production`, then
  `SMUS_DEPLOYMENT_MEMBERS` gains both (Stage 18 2.3's order; the guard refuses an account in both lists
  and `profiles_enabled` flips while a deployment row precedes its associated row); the four readers
  that mean "accounts people work in" stay on `SMUS_MEMBERS`; `sandbox/foundation/`,
  `production/tooling/` and `staging/foundation/` re-plan `No changes` after each regeneration.
- **4.4 [Claude] `staging/studio/` and `production/studio/`**, Stage 18 2.4's slice as a `[P]` slice of
  each target: `terraform-modules/sagemaker-prereqs/` at its pinned tag (`v0.9.0` since 2026-10-30) with
  `blueprint_names` `["Tooling", "DataLake"]`, the D13 boundary, the Glue manage-access policy the
  module carries since `v0.8.0` (7.2's first environment failed without it), `workflows.tf` granting the
  project roles the job actions `sandbox/workflows/` grants (4.4's first run was refused `glue:GetJob`
  without it), `person-session.tf` under decision 15, `cost_center` `stage-19`; in Staging, `InfrastructureAccess`
  seated as a third Lake Formation administrator and the deploy role granted `DESCRIBE` and `SELECT` on
  the product database's tables, `staging-test`'s door (decision 14 (d)); the `studio` rank and
  `[P]` row in `layers.py`, `backend.py`'s `studio` emission, conventions §6 and `NETWORK.md` §2.1. Each
  target's `egress/` gains the `datazone` interface endpoint 7.1 needed (a `datazone` group or
  `extra_services`, `PRICING.md` §3's endpoint count). **[Claude⚡] applied twice per account as
  `awsds-infra-<env>`**: the prerequisites (Stage 18 read 14 to add), then, after 4.3's associated row,
  the two configurations and their grants; the boundary read back with `get-role`.
- **4.5 [Claude] The profile `deployment`** in `governance/`, Stage 18 2.6's form with two environment
  configurations: `Tooling` `ON_CREATE` with `enableSpaces` `"false"` locked and `DataLake` `ON_DEMAND`
  in each target, the `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to each target's InfrastructureAccess
  session group by its group id (2.7's correction), never to a persona group; `./aws/studio.py`'s `US-4`
  admits `deployment` as a standing profile. **[Claude⚡] applied as `awsds-infra-data`**, a plan that
  touches `experimentation` or 6d decision 16's objects stops the step; 6d's 2.7 and this apply never
  share one (Stage 18 2.7's rule).
- **4.6 [Claude⚡] The projects**: `deploy-staging` and `deploy-production` by `create-project` as each
  target's `awsds-infra-<env>` (3.1), their provisioning read (3.2: the stack `CREATE_COMPLETE`, no
  SageMaker AI domain, every refusal the roles' own IAM), what the blueprint created (3.3: the thirteen
  resources, the two SMUS roles seated as Lake Formation admins, `AllowFullTableExternalDataAccess` set
  `true`, the Access Grants instance and the Athena service-linked role). Then the product's database in
  each project: `create-environment` from `DataLake` with the name decision 2 (d) fixed, the API form of
  the portal's *Create database* (6f 11.7's call), and its reads: the database, its conditioned grants,
  its daily source (`publishOnImport` false) and its subscription target (xix).
- **4.7 [user] Production's flag**: `AllowFullTableExternalDataAccess`, turned off in Production on
  2026-10-25 (`TM-26`), is `true` again after 4.6; the user turns it off in the console as then, and 4.10
  and 4.12 read whether the project's engines or a fulfilment need it (xx). Staging's flag follows the
  same reading. The lake's flag is 6f's and untouched.
- **4.8 [Claude] The deploy roles**: `awsds-deploy-staging` and `awsds-deploy-prod` gain Stage 18 4.3's
  three inline documents in `<env>/foundation/deploy-role.tf` (the DataZone reads the CLI makes before
  `workflow.create`, the workflow calls on workflows tagged with the project, `iam:PassRole` of the
  project role to the service, the project's `shared/` prefix and the project key), **[Claude⚡]
  applied as `awsds-infra-<env>`**. Then the membership, 4.3's two steps: the role's first CLI call as a
  non-member stops at `ListConnections` and creates its `IAM_ROLE_SESSION_GROUP` profile, which
  **[user]** adds as `PROJECT_OWNER` by group id (`create-project-membership` as `awsds-infra-<env>`;
  the classifier refused Claude the grant in Stage 18). The portal's Workflows tool is unavailable in a
  deployment project (6.1), so a run is followed by the job's `get-workflow-run` loop and the console.
- **4.9 [Claude] The legs**: `staging-deploy` and `production-deploy` run `smus-cli deploy --targets
  staging` and `prod` from the stored bundle, extracted beside the release's manifest (Stage 18 4.2: the
  CLI 1.0.9 reads every local item from the manifest's folder), as `awsds-deploy-<env>` on the deploy
  runner, Stage 18's job `stage-18-deploy` the recipe; `release-application.py`'s render, the promoted
  lint mode and the orchestration slices' `release.auto.tfvars.json` workflows retire whole, the
  warehouse workflow deployed by the CLI into Production's project too (decision 16 (b)). `staging-test` reads the
  run's output under the project's `shared/` prefix and the table through decision 14's door. The
  template's merge request lands in `awsds/app-etl` at the next tag's sitting (`runbooks/promotion.md`
  §N.8.2), so the Stages 8-10 session's leg changes and decision 1's branch are one release.
- **4.10 [user] The release**, `runbooks/promotion.md`'s order: the tag, `test-deploy`, `store-bundle`,
  `staging-gate`, `staging-deploy`, `staging-test`, `production-gate`, `production-deploy`, then the
  first Production run of `app-etl` by the bootstrap's `workflow.run` (decision 14). **[Claude] reads**
  in each target: the workflow by its composed name `app_etl_<project>_app_etl`, the project role as
  its execution role, the project's subnets, security group and key (Stage 18 v), the deploy's calls in
  the trail as the deploy role (4.3's 174-call shape), the Glue job and the processing job created by
  the operators as the project role under the `Workloads` document (4.4), the table created in the
  product's database (i's reading in a target: `glue:CreateTable` by the project role's
  `GlueJobRunnerSession`, Iceberg, `IsRegisteredWithLakeFormation`), the catalog import's calls and what
  each project holds after it (xii's reading in a target), the publishing task's `StartDataSourceRun` and
  `CreateListingChangeSet` through the target's `datazone` endpoint (ii's reading in a target) and the
  listing `ACTIVE` in Production alone (decision 14), the job's lineage events posted through the same
  endpoint (7.1's run B shape, xxi), Staging's `make down` afterwards leaving the project, its
  environments and its database as `[P]` metadata (xxii).
- **4.11 [Claude] What Terraform stops declaring** (the Stages 8-10 session's hunks, planned here and
  applied by the user in the same sitting): `<env>/app/app-etl/` retires, table and Glue job, since
  the operator creates the job in the project (D41 item 9 for the targets); the application's grants
  on `app_outputs` leave `<env>/data/`; the orchestration module's workflow resource and per-workflow
  role retire (decision 16 (b)), and each target's `orchestration/` points every chain's machine, the
  warehouse chain's included, at the CLI-made workflow by name, the chain role holding `kms:GenerateDataKey` and
  `Decrypt` on the project key (Stage 18 0.4, vii: a non-member starts a workflow by IAM and the key);
  `check-copies.py` loses the application slices' pair, `lint-plan.py`'s `aws_glue_job` rule retires,
  `render-workflow.py --check` and the `.pre-commit-config.yaml` hook with it. Under decision 16 (b)
  `deploy-production`'s project role takes what the job role held for the load: the lake's write share on
  `curated` (`data-governance/data/shares.tf` and its README, D22 amended), 9.3's warehouse grants for an
  `IAMR:` user of that role with the default privileges, `GetCredentials` through the workgroup's project
  tag or a named grant, and a 5439 ingress on the warehouse's security group from the project's
  (`production/warehouse/`); decision 15's deny grows to the lake's catalog, `lakeformation:GetDataAccess`
  and the warehouse's credential and Data API calls (xxvii); the job role's remaining uses, 9.4's DDL job
  among them, are read and recorded, and 9.5's datashare re-read over objects the new user owns. Stage 10's 1.1, 2.4 and
  4.2 are rewritten in that stage's file by its session; Stage 10 decision 9 (no lineage from
  Production) is amended there. The chain is read at its next scheduled firing: the machine started the
  CLI-made workflow and waited on `GetWorkflowRun` (xxiii).
- **4.12 [user] A Sandbox project subscribes to Production's listing**, Stage 18 7.2's shape and 6f
  11.8's acts: `eighth-experimentation` requests (decision 5: the project whose warehouse connection pass
  5 reads through), the approver of decision 15 approves. **[Claude]
  reads** the fulfilment on both sides (the `SELECT` grant to Sandbox's `IAMPrincipals` under the
  consumer's context in Production, `CROSS_ACCOUNT_VERSION` 5 in the grant with Production's setting at
  its own value, the RAM share of Production's catalog, the three statements in Production's Data
  Catalog resource policy, the resource link and its `DESCRIBE` in Sandbox), the consumer's read from
  the query editor with no space, `CT-10` to `CT-12` on the product road (decision 11), 4.7's flag
  question (xx), and `GetDataAccess` in Production's trail for the read's identity (xxiv). The
  revocation is 2.5's, read on both sides.
- **4.13 [Claude] Staging's catalog under decision 14**: with `catalog.disable` on the `staging` stage,
  Staging's project holds the table and no asset until its daily source runs; what the source imports
  and leaves unpublished, read the morning after (xxv), and `CT-4`'s rule on it.

### 5. Redshift

Waits on decision 9, which decision 6 (b) leaves as written: the Sandbox warehouse reads the subscribed
product in place, the subscription now Production's listing (4.12) rather than the lake's, through
`eighth-experimentation`'s connection (`EXC-17`, decision 5), so 6h decision 8 stays deferred. Under its
recommendation, a warehouse sitting inside a Sandbox one (`sandbox/warehouse-compute/` up;
[`redshift-connection.md`](../runbooks/redshift-connection.md) §J).

- **5.1 [Claude⚡] The grant the read in place needs**: on the user's word, Lake Formation `DESCRIBE`
  and `SELECT` on the product's table to the identity the database user carries, read first from
  `SVV_*` as the admin (`IAMR:<project role>` for the access role's chain, 6h decision 8a), and `USAGE
  ON DATABASE awsdatacatalog` to it in SQL; nothing on the namespace role (5b decision 5 holds). Since
  decision 6 (b) the table is Production's and the grant, if xiii says the session carries no project
  context, is written in Production, from an administrator seat or by the project role as the table's
  creator (decision 9); the first attempt is the read with DataZone's grant alone.
- **5.2 [user] From a notebook** through §J's connection: `SELECT ... FROM
  awsdatacatalog.<project database>.trades_notional LIMIT 10`, then `CREATE TABLE lab.trades_hot AS
  SELECT ...` in the project's schema, then a materialized view over the Iceberg table and its
  `REFRESH`. **[Claude] reads** `GetDataAccess` in the trail with the session's identity (whether the
  project's context travels, xiii), `ComputeSeconds`, the copy's size, and what the Glue Data Catalog
  shows for the materialized view (xiv).
- **5.3 [user] Publish `lab.trades_hot` as a Redshift asset**: a Redshift data source on the project's
  connection (`publishOnImport` false, no schedule), one run, *Publish*. **[Claude] reads** the asset's
  type and forms, and whether a subscription from the consumer finds a target (xv). Nothing is subscribed
  while no Redshift target exists; what a target costs is decision 9's second half.
- **5.4 [user] Revoke 5.1's grant** at the sitting's end, drop the copy and the view, `make down`.

### 6. The checks and the documents

- **6.1 [Claude] The instruments**: `catalog.py` gains the product road (decision 11): every published
  listing of a project's own table judged by `CT-11`'s rules, `CT-10`'s join extended to a same-account
  fulfilment and to Production's cross-account one, a check on an inventory asset that is a resource link (0.5) if the 6f follow-up has not
  written it, `CT-5`'s rule for a project's sources as decision 3 reads it; `studio.py` reads each
  project's environments and subscription targets; `datalake.py`'s `DL-14` admits the consumer's
  registration.
- **6.2 [Claude] The documents**: `SMUS.md` (the product's readings, the targets, the roster of 0.8;
  §A deployment project in a `Workloads` account rewritten as the two projects that exist),
  `GOVERNANCE.md` (§Grants, §The development cycle, §Assigning the LF-Tags, §Publishing and sharing
  under decision 6 (b), the warehouse paragraph), `AWS_STATE.md` (the product's register row or its
  rule, `EXC-17`'s trigger, the association invariant of 4.1), `architecture.md`, `NETWORK.md` (the
  `studio` slices and the `datazone` endpoints), `runbooks/sagemaker-application.md` §B, §K, §M, §N,
  §P, §T, §W and §Z (the CLI's legs, the project per target, the publishing task in every stage),
  `runbooks/promotion.md` (the legs' new shape), `redshift-connection.md` for 5.1 and 5.2, D17, D19, D20, D22,
  D26, D28, D35, D41 and 5a decision 5 amended in place with dated lines (Stage 9 decision 15 by its
  session), `POLICIES.md`'s row (4.1),
  `integrations.md`'s INT-12 and INT-26, `history.md`; `GOVERNANCE.md:737` is the 6f follow-up's.
- **6.3 [Claude] The threat model**: an entry for the product road, the subscriber's full-table vend
  (xi), the re-listing channel (0.5), a materialized view that outlives a revoke (question 3), with the
  checks of 6.1 as its triggers; under decision 6 (b), an entry for the deployment projects, Stage 18's
  measured price as its residual: the project role every member acts as in Production, bounded by
  decision 15's deny; AWS's managed policies on it (`TM-17`, `TM-28` gain weight: the policies moved to
  v76/v47 on 2026-10-29 with no act of this estate); the two SMUS roles as Production's Lake Formation
  admins; the RAM share of Production's catalog at each fulfilment; `TM-26`'s Production half reopened
  at 4.6 and closed again at 4.7 if 4.10 and 4.12 read nothing needing the flag.
- **6.4 [Claude] `PRICING.md`** with pass 5's measured `ComputeSeconds` and the source runs' compute
  units; `cost-model.md`'s per-sitting row.

### 7. Close

- **7.1 [user]** Keep or delete the consumer project (its database is `Retain`), the data product and
  the listings, the copy in the warehouse.
- **7.2 [Claude]** `CLAUDE.md`'s Current position, `docs/plan/stages/INDEX.md`, `docs/GENERAL_PLAN.md`,
  `docs/log/INDEX.md`, the log.

## Verifications

| # | Question | Step |
|---|---|---|
| i | Does the Glue job's session create an Iceberg table in the project database under the conditioned `CREATE_TABLE`, registered with Lake Formation, and where? | 1.2 |
| ii | Does the worker's session of the project role start the source's run and publish the listing, through the `datazone` endpoint, and which policy admits each call? | 1.2 |
| iii | What does a run filtered to one table import, and does `publishOnImport` false leave it unpublished until the task publishes? | 1.2 |
| iv | Does the published asset carry a classification anywhere, and does the form of decision 4 travel to the listing and the data product? | 1.3, 2.1 |
| v | Does the job post lineage to the domain from Sandbox, and does the portal draw it on the asset's page now that the table is an asset (Stage 18 7.1 drew nothing)? | 1.2 |
| vi | In one account, which principal writes the fulfilment, in what form (a grant to `IAMPrincipals` under the consumer's context, or to its role), and does a resource link appear in the consumer's database? 6f verification i's same-account half | 2.3 |
| vii | Does one approval of a data product fulfil every item? 6f iv | 2.3 |
| viii | Does the consumer read through the query editor with no space and from a space's Spark session? | 2.4 |
| ix | Does revocation remove every piece, and does a session opened before it still read? 6f iii | 2.5 |
| x | Does the consumer's daily source import the resource link, and does anything notice? | 2.6 |
| xi | Can the consumer's role vend the table's objects directly, under Sandbox's `AllowFullTableExternalDataAccess` (`TM-26`, Stage 17 7.4c)? | 2.4 |
| xii | What does the bundle carry of the catalog, in what order does `deploy` import against the run, which policy grants does the import add to the domain unit, and what does `test` hold after? | 3.2 |
| xiii | From the warehouse, which identity reads `awsdatacatalog`, does it carry the project's context, and which Lake Formation grant admits it? | 5.2 |
| xiv | What does an Iceberg materialized view register in the Glue Data Catalog, and what does its refresh cost? | 5.2 |
| xv | Does a Redshift asset published from the connection find a subscription target in any project? | 5.3 |
| xvi | What did the sittings bill, by service? | 6.4 |
| xvii | After the CLI's catalog import, does the project's own source update the imported asset or create a second one over the same table? | 3.2 |
| xviii | With `DenyDataZoneEntirely` revised, does `datazone list-domains` answer from both targets, does the root's `CreateDomain` deny still bind them, and does the battery's phase `ou` read the document as decision 13 wrote it? | 4.1 |
| xix | Does a `DataLake` environment created by API with a chosen database name carry a subscription target, in a project with no person? | 4.6 |
| xx | With `AllowFullTableExternalDataAccess` off in Production, do the project's engines write and read the product, and does a fulfilment to Sandbox complete? Stage 9 decision 13's reading on a project's table | 4.7, 4.10, 4.12 |
| xxi | Does Production's Glue job post its lineage through the target's `datazone` endpoint as the project role, and does the portal draw it now that the table is an asset? | 4.10 |
| xxii | What does `make down ENV=staging` leave of a deployment project, and does `staging-check` read it as `[P]`? | 4.10 |
| xxiii | Does the chain's machine start the CLI-made workflow by its composed name and wait on `GetWorkflowRun`, with KMS on the project key alone? Stage 18 0.4 as a standing state | 4.11 |
| xxiv | Which identity does Production's trail record for the consumer's read, and which grant admits it? INT-23's cross-account reading on a product | 4.12 |
| xxv | With `catalog.disable` on the `staging` stage, what does Staging's daily source import, and does `CT-4` or `CT-5` notice an unpublished asset in a project with no person? | 4.13 |
| xxvi | Does a domain-defined designation (API-only since 2026-10-29) narrow what the Governance Manager may do in `deploy-production`'s portal, beside decision 15's deny on the person's session? | 4.12 |
| xxvii | Does decision 15's deny, grown to the lake's catalog, Lake Formation's data access and the warehouse's credential calls, refuse a person's session those writes while the warehouse workflow's worker session still loads `governed` from `curated`? | 4.11, 4.12 |

## Decisions due

1. **The application.** (a) `app-etl` extended: the Iceberg write, the publishing task, `content.catalog`,
   on a branch and the next tag; (b) a second application on the template, with its own GitLab project,
   image, registry row and slices. **Recommended: (a)**: the template is the house's application and the
   product is its existing output; (b) buys isolation at the price of every Stage 7-8 object a second
   application needs ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §Z).
   **Taken 2026-10-31 by the user as (a)** (*"conforme sua recomendação"*): `app-etl` extended on a
   branch that joins the next tag with decision 6 (b)'s leg changes and 3.3's stages, one release for
   both; the publishing task is exercised in `dev` and `test` (passes 1 to 3) before any tag reaches a
   deployment target.
2. **How the table is created, and in which database.** The hand: (a) the Glue job's Spark write into the
   project database, Iceberg, as Stage 18 7.2 did with Parquet; (b) the workflow editor's Glue Catalog
   Create Table operator, a `TableInput` without `OpenTableFormatInput`, so an external table over the
   job's Parquet, never Iceberg; (c) a `PythonOperator` calling `glue:CreateTable` with
   `OpenTableFormatInput`. The database: (d) one named database per project, created by the portal's
   *Create database* with the same name in `dev`, `test` and every consumer that promotes the product,
   the application's name `app_etl`; (e) the environment's default `glue_db_<environment id>`, different
   in every project. **Recommended: (a) and (d)**: one hand writes the data and the metadata, the
   catalog settings the targets already pass, and the conditioned `CREATE_TABLE` admitted the job's
   session on 2026-10-22; the CLI's catalog import assumes the same database name on both sides (0.9),
   which (e) breaks at the first `test` deploy; (b) and (c) separate the table from its writer and are
   measured only if (a) is refused. (d) is a portal act per project, the tool's own, and 1.2 reads
   whether such a database carries the subscription target the consumer needs.
   **Taken 2026-10-31 by the user as (a) with (d)** (*"ok em relação as recomendações"*): the Glue
   job's Spark write creates the Iceberg table in the project database `app_etl`, the same name in every
   project, created in the portal in Sandbox (1.2, 3.2) and by API in the deployment projects (4.6);
   1.4 reads that an Iceberg overwrite keeps the table, its listing and its grants across runs.
3. **How the asset is published.** (a) the workflow's task: the source's run, then the listing by name;
   (b) `publishOnImport` on the project's source, with the task starting the run alone; (c) the portal
   after each run, the pilot's way. **Recommended: (a)**: (b) publishes every import, a subscribed
   resource link included (0.5), and `CT-4` fails on it; (c) is a person in the loop of a pipeline. The
   task runs in `dev` and `test` alone (decision 8).
   **Taken 2026-10-31 by the user as (a)** (*"ok em relação as recomendações"*), with a stage variable as
   its gate: `PUBLISH_LISTING` `true` in `dev`, `test` and `prod`, `false` in `staging`, where the task
   neither starts the source nor publishes (decision 14); the sentence above on `dev` and `test` alone is
   the record of 2026-10-28, decision 8 being moot since decision 6 (b). Each run republishes, so the
   listing follows the newest revision (1.4).
4. **Where classification lives without an LF-Tag.** (a) a metadata form `classification` on the asset,
   required by the project, read by `CT-12`'s successor; (b) `internal` by convention for every product;
   (c) the LF-Tag assigned by hand by the Governance Manager on the lake's copy alone (4.4).
   **Recommended: (a) with (c)**: the form is the catalog's own carrier (6f 4.1-4.2), the approver sees
   it, and the lake keeps its tag for the register's readers; (b) states nothing.
   **Taken 2026-10-31 by the user as (a)** (*"ok em relação as recomendações"*): a form type
   `classification` with one field enumerated on the four values, filled in `dev` and carried by the
   bundle's catalog export, read by `CT-12`'s successor on every product listing, which fails a product
   `restricted` or `personal` or one with no form; (c) is moot since decision 6 (b), the product having no
   lake copy. The form type's owner, the producing project (recreated per project by the import) or a
   governance project once, is read at 3.2 (xii); a glossary term is the variant with a native
   vocabulary, same transport.
5. **The consumer, and who approves.** The consumer: a third project from `experimentation`
   (`test-experimentation` receives the application itself, so a subscription there reads a copy it
   already holds). The approver: the owner project's members, the Data Scientist User, or the Governance
   Manager added to `eighth-experimentation` as a member (6f 4.3), who then acts as the project role in
   it (Stage 18 6.1). **Recommended: a third project, and the Governance Manager as a member of the owner
   project** for this stage's approvals, 6f 4.3 read in the same act.
   **Taken 2026-10-31 by the user as recommended** (*"ok em relação as recomendações"*), with one
   refinement from decision 6 (b): the third project, created in the portal by the Data Scientist User, is
   pass 2's consumer, and the Governance Manager, a `PROJECT_CONTRIBUTOR` of `eighth-experimentation`,
   approves there, 6f 4.3 answered in the act; the consumer of Production's listing at 4.12 and pass 5 is
   `eighth-experimentation` itself, through the warehouse connection it already holds (`EXC-17`), the
   Governance Manager approving in `deploy-production` (decision 15), so 6h decision 8 stays deferred.
6. **Where the promoted product lives.** (a) **the lake**: Production's job creates `curated.<table>`
   (`CREATE_TABLE` on `curated` to the job role, one declaration for every future table), `governed-lake`
   publishes it, a Sandbox project subscribes; Staging's job creates its table in `app_outputs`,
   unpublished; the targets stay unassociated. The publisher's grain under (a) is a choice of its own:
   `publishing.tf` today grants `governed-lake`'s role `DESCRIBE` and `SELECT` with the grant option per
   table of `published_tables`, and refuses at plan a table or column tagged `restricted` or `personal`
   (6f decision 2, 2026-10-27, measured with `sample_trades` in the working copy).
   - **(a1) the database grain**: one grant with the grant option on every table of `curated`, present
     and future, no apply per product. Its cost, each piece re-read on 2026-10-28: the plan-time
     refusal becomes detection after the fact, `CT-12` reading each published table's live tags; the
     role holds the grant option on `sample_trades` too, whose column `counterparty` is `restricted`,
     and DataZone fulfils by name and reads no LF-Tag, so a published `sample_trades` would reach its
     subscribers whole; `SageMakerStudioProjectUserRolePolicy` v75's `LFResourceSharingPermissions`
     allows `lakeformation:BatchGrantPermissions` on `*` with no condition (6f decision 5's input), so
     any session of the publishing role can regrant what it holds with no listing and no approval
     between, and a table Production's job creates is regrantable the moment it exists, before anyone
     classifies it; `TM-27`'s residual widens from `publishing.tf`'s list to the whole database, and
     step 6.3 rewrites its bound and its triggers (a `CT-12` failure on any `curated` table, a grant on
     one outside an approved subscription, `CT-10`). 6f decision 2 is reopened by it.
   - **(a2) the per-table list kept**: the job creates the table, and before `governed-lake` publishes
     it the table joins `published_tables` with its tag assignment (`aws_lakeformation_resource_lf_tags`,
     a resource on a table Terraform did not create) in one `data-governance/data/` apply as
     `awsds-infra-data`, so the precondition reads a declared classification; a tag assigned by hand
     alone (decision 4 (c)) leaves it nothing to read and `CT-12` the only reader. The gate, the regrant
     bound and `TM-27` hold as written. Its cost is one apply per product table, a Terraform act on a
     grant and a tag, never on the table, which is also the moment the Governance Manager's
     classification is recorded.

   (b) **a project per deployment target**, alternative B: the association, the `Tooling`
   configuration, the `datazone:*` carve-out, the CLI deploying every stage, Stage 18's measured price
   (question 2). (c) **the targets as today**: the Terraform table, nothing published from Production,
   the native cycle Sandbox's alone. **Recommended: (a) with (a2)**: it meets `DenyDataZoneEntirely`'s
   trigger through the road 6f built, without an association, consistent with D41 item 2 and 6f
   decisions 2 and 4; P3 holds for the table and the database, and the one apply per product is the
   approval's record rather than a side effect. (a1) is the user's to take with the costs above; (b)
   with its dated price; (c) answers the user's fifth bullet with no.

   **Taken 2026-10-31 by the user as (b)**, against the recommendation: *"Decido pelo modelo da AWS, com
   o uso previsto do SMUS e promoção entre ambientes via ferramenta SMUS CICD CLI"*. The user's reading,
   from the exchange that preceded it: the AWS model is measured (Stage 18), what stopped it was its
   price on the perimeter and not an open hypothesis, and the price is accepted so that every stage
   runs one tool and one identity model, with publication and lineage from Production. Pass 4 is its
   plan; D41 item 2, D26, D17's DataZone half, D20, D28 and 6f decision 4 are amended as the review
   tables say; decisions 7 and 8 are moot, 13 to 16 due.
7. **The publication from the lake, under 6 (a).** (a) the source's daily schedule imports, the
   Governance Manager publishes the new asset in the portal; (b) a role in `Data Governance` the pipeline
   assumes starts the run and publishes, 6f 7.2's automation. **Recommended: (a)**: the publish is an
   approval-shaped act and the person is the Governance Manager; (b) is written once (a) has run twice.
   **Moot since 2026-10-31** (decision 6 (b)): Production's project publishes its own product through
   the publishing task; 6f 7.2's automation stays 6f's question for the lake's tables.
8. **The publishing task in a promoted copy.** (a) `render-workflow.py` drops a task carrying a marker
   (`awsds_sandbox_only: true`) in promoted mode, the lint refusing the marker's survival; (b) the task
   no-ops when the worker carries no `DataZoneDomainId`. **Recommended: (a)**: a task that only runs
   where the portal exists is not promotable (D28), and a dropped task is read in the rendered copy; (b)
   ships a domain reference the lint refuses. **Moot since 2026-10-31** (decision 6 (b)): the portal
   exists in every stage, the task runs in every stage as the project role, and there is no render.
9. **The Redshift leg.** (a) the read in place through `awsdatacatalog` from the project's connection,
   with the copy and the materialized view made in the project's own schema (sandbox class), the grant
   of 5.1 on the database user's identity; (b) the same copy published as a Redshift asset and subscribed
   with a datashare, which needs a Redshift subscription target: the `RedshiftServerless` blueprint (D40
   and D12 refuse it) or a custom environment's target with a secret and the workgroup
   (`CreateSubscriptionTarget`), the manage-access role writing grants and datashares; (c) the product's
   hot copy loaded by Production's warehouse workflow into `governed` (Stage 9 9.4's shape) and read
   through the datashare (9.7), the path built today, no catalog act; (d) none. **Recommended: (a) with
   5.3's publication read but not subscribed**: it is the tool's end-to-end path for a Glue asset, costs
   the warehouse's compute alone, and keeps D40; (b) is read as a second half once a target's shape is
   priced; (c) keeps the warehouse outside the premises.
   **Taken 2026-10-31 by the user as (a)** (*"ok em relação as recomendações"*): the read in place
   through `eighth-experimentation`'s connection on Production's subscribed product (decisions 5 and 6
   (b)), the copy and the view in the project's own schema, 5.3's Redshift asset published and never
   subscribed. Verification xiii decides 5.1's hand: if the Redshift session carries the project's
   context, DataZone's grant admits it; if not, a named grant in Production to the session's identity,
   written from an administrator seat there (decision 14 (d)'s shape for Staging) or by the project
   role's grant option as the table's creator, nothing to the namespace role (5b decision 5).
10. **Lineage in Sandbox.** The job's OpenLineage settings on in `dev` and `test` (Stage 18 7.1's
    configuration), off in the targets. **Recommended: on**, read at verification v; Production's lineage
    stays Stage 10 decision 9's. **Amended 2026-10-31** (decision 6 (b)): the settings stay on in the
    targets too, since the job posts through the `datazone` endpoint 4.4 adds (xxi), and Stage 10
    decision 9 is amended by its session.
11. **The product's register and checks.** (a) the product road judged by `catalog.py` (6.1), the
    register carrying no row for a project-owned fulfilment, DataZone's subscription its record; (b) one
    row by class as the lake road; (c) nothing. **Recommended: (a)**: SMUS's grants on project objects
    are already outside the register (`AWS_STATE.md`), and the check is what notices a grant no
    subscription explains. The inventory import of 0.5 stays an accepted residual with `publishOnImport`
    off, read by the 6f follow-up's check.
    **Recommendation revised 2026-10-31 in chat, to (b) for Production and Staging and (a) for Sandbox**:
    decision 6 (b) put the promoted product's fulfilment in Production, a governed account where the
    register's drift rule is the authority, so its grants, the RAM share and the catalog policy get one
    row by class as the lake road's do since 6f decision 2, while Sandbox's project-owned fulfilments
    stay outside the register as its objects already are; (a)'s checks run in every case.
    **Taken 2026-10-31 by the user so** (*"ok em relação as recomendações"*): 6.1 writes the product
    road's checks, 4.12 and 6.2 write the rows by class in `AWS_STATE.md`'s register, and its row on
    Production's Lake Formation is amended at 4.6 with the SMUS seats.
12. **D19 and the derived zone.** A published project table is a product outside open question 25's
    expiry rule, or a copy inside it. **Recommended: outside**, with a dated line in D19 at close: a
    product has an owner, a listing and subscribers, which a copy does not.
    **Taken 2026-10-31 by the user as outside** (*"ok em relação as recomendações"*): the rule open
    question 25 sets excludes `dev/data/catalogs/` by prefix or selects by tag, the product's life being
    its owner's; D19 gains two dated lines at 6.2, the product outside the rule and, since decision 6
    (b), the project path existing in Staging and Production as the product's home and never a person's
    derived zone, inside Stage 11's scan scope and data events by the name `awsds-<env>-smus-projects`,
    which 6.3 reads; a `retention` field on decision 4's form is the owner's declaration, optional.
13. **The shape of `DenyDataZoneEntirely`'s revision** (4.1). (a) the statement removed from the
    `Workloads` document: its three purposes (`POLICIES.md`) are met otherwise or intended now, a local
    domain by the root baseline's `datazone:CreateDomain` deny outside the `Data` OU, the self-association
    and the blueprint configuration by `<env>/studio/` as `awsds-infra-<env>`, the non-ML blueprints by
    the `deployment` profile's list and `governance/`'s creator grant; (b) the statement kept with
    `aws:PrincipalArn` exceptions for the deploy roles, InfrastructureAccess and the project roles,
    which DataZone's own sessions on the project role also need (Stage 18 6.2's correction); (c) kept
    with `StringNotEquals aws:PrincipalAccount` naming both accounts, Stage 18 1.1's form twice, which
    denies nothing while `Workloads` holds these two accounts alone. **Recommended: (a)**: (b) is
    Lesson 14's list, growing with every project and session class, and (c) is (a) with a statement that
    reads as a control and binds nobody (Lesson 56). The battery keeps the `CreateDomain` row and turns
    the two `ListDomains` rows to `allow`.
    **Recommendation revised 2026-10-31 in chat, to (b) with a subscription deny**: Production is also the
    hub account, GitLab, runners and proxy included, so the whole-namespace deny keeps covering every
    principal but the three patterns, and the exception fails closed, a new identity reading a refusal
    that names the SCP rather than finding a hole; the three `ArnNotLike` patterns cover any future
    project, so Lesson 14 weighs little in one statement. The acquisition: a second statement denying
    `datazone:CreateSubscriptionRequest` to every principal of `Workloads`, the excepted ones included,
    which turns decision 14's "a deployment project subscribes to nothing" from an intention into a
    control (Lesson 5), closing Staging's request for Production's listing (`TM-25`'s reverse) and
    Production's for a Sandbox one; a direct Share made by a Sandbox owner stays `CT-11`'s detection.
    **Taken 2026-10-31 by the user as (b) with the subscription deny** (*"Ok em relação a sua
    recomendação."*). 4.1 writes `DenyDataZoneEntirely` with `ArnNotLike` on `aws:PrincipalArn` for the
    SSO `InfrastructureAccess` role, `awsds-deploy-*` and `datazone_usr_role_*`, and the new statement
    beside it; the battery measures the deny half as the canary under the candidate document on
    `Policy Test` and the allow half as the infrastructure user from both targets; `POLICIES.md` gains
    the second statement's row.
14. **The catalog in the promoted stages, and the table's door for the integration test** (3.3, 4.9,
    4.13). The catalog: (a) `content.catalog` enabled with `skipPublish` true for the whole content, the
    publishing task publishing after each run in every stage where the listing is wanted, the `staging`
    stage with `catalog.disable` so Staging's sample data is never listed; (b) the CLI publishing at the
    deploy, in Production after a bootstrap `workflow.run` that creates the table first (3.1's order),
    Staging disabled as in (a); (c) every stage importing and publishing, Staging's listing included.
    The bootstrap: `workflow.create` for each workflow in both targets, `workflow.run` of `app-etl` in
    Production alone, the chain's schedule starting every later run (D41 item 5). The test's door: (d)
    `staging-test` reads the run's output files under the project's `shared/` prefix, which the deploy
    role already reads, and the table through Athena under a named Lake Formation grant to the deploy
    role written in `staging/studio/`, which seats InfrastructureAccess as a third Lake Formation admin
    there (Sandbox's shape); (e) the output files alone. **Recommended: (a) and (d)**: one publisher
    per stage, the task, whose listing follows the run that made the table; a Staging listing would
    offer sample data to every Sandbox project's search; (d) keeps the test reading the table it tests,
    at the price of one admin seat Stage 18 8.1 had to take anyway. xvii decides whether (a) leaves one
    asset per table.
    **Taken 2026-10-31 by the user as (a) with (d), and the bootstrap `workflow.run` in Production**
    (*"Ok em relação a sua recomendação"*): `content.catalog` enabled with `skipPublish` true, the
    publishing task the one publisher in `dev`, `test` and Production, the `staging` stage with
    `catalog.disable`; the `prod` stage's bootstrap runs `app-etl` with `trailLogs` at each deploy, so the
    release ends with the table and the listing in place (3.3); `staging/studio/` seats
    `InfrastructureAccess` as a third Lake Formation administrator and grants the deploy role `DESCRIBE`
    and `SELECT` on the product database's tables, and `staging-test` reads the output files and the
    table (4.4, 4.9); `assets.access` stays unused, which decision 13's deny enforces. Re-read if decision
    3 does not end in (a).
15. **Who approves a subscription to Production's listing** (4.12). (a) the Governance Manager as a
    `PROJECT_CONTRIBUTOR` of `deploy-production` (the V2 domain admits no viewer, Stage 18 6.1), approving
    in the portal, with Stage 18 6.2's deny on `aws:SourceIdentity` written in `production/studio/` so a
    person's session writes nothing (`person-session.tf`); (b) `accept-subscription-request` as the
    project's owner session group, `awsds-infra-prod`, the user's command in a sitting (Stage 18 7.2's
    form); (c) a manual pipeline job as `awsds-deploy-prod`, a `PROJECT_OWNER`. **Recommended: (a)**:
    P4 wants the approval in the tool's own flow and D31 names the approver; the deny was measured on
    the person's side on 2026-10-21 and binds DataZone's member and `SYSTEM` sessions too, leaving a
    deploy and a listing working while they only read. Its cost: a person who acts as Production's
    project role in the portal, reading the product it approves (D31's read) and nothing of the lake,
    which that role holds no grant on. (b) is the fallback while (a)'s deny is unapplied.
    **Taken 2026-10-31 by the user as (a)** (*"ok em relação a sua recomendação"*): the Governance
    Manager a `PROJECT_CONTRIBUTOR` of `deploy-production`, added by its owner (the user, as
    `awsds-infra-prod`) once `production/studio/`'s `person-session.tf` is applied, never before; the
    approval in the portal at 4.12; `accept-subscription-request` as the owner session group the fallback
    until then. One reading added at 4.12: whether the domain-defined designation of 2026-10-29 narrows a
    member's portal acts, which could replace part of the deny (xxvi).
16. **The warehouse workflow and the job role** (4.9, 4.11). Stage 9 decision 15's Production-only
    workflow loads the warehouse as `awsds-prod-job-exec`, which holds the lake's write share and the
    warehouse's grants; the CLI never creates it in a project (the manifest's note). (a) it stays on the
    Terraform path: `release-application.py`, the orchestration module's workflow resource and
    per-workflow role, `release.auto.tfvars.json`, for that workflow alone; (b) it moves to the project,
    its role the project role, which would need the lake share and the warehouse grants a project role
    never holds. **Recommended: (a)**: two paths for two kinds of workflow, the application's by the
    CLI and the lake's by Terraform, each with the identity its data demands; (b) hands a shared,
    AWS-written role the governed write D22 gives one enumerated role.
    **Taken 2026-10-31 by the user as (b)**, against the recommendation (*"(b)"*): one tool and one
    identity model for every workflow, the warehouse workflow included. What it carries, written into
    passes 3 and 4 the same day: `app-etl-warehouse` joins the manifest's `content.workflows` and the
    `prod` stage's bootstrap alone creates it (3.3); `deploy-production`'s project role takes what the job
    role held for the load, the lake's write share on `curated` (D22 amended), 9.3's warehouse grants for
    its own `IAMR:` user, `GetCredentials` and a 5439 ingress from the project's security group (4.11);
    decision 15's deny grows to the lake's catalog, Lake Formation's data access and the warehouse's
    credential and Data API calls (xxvii); the render, the promoted lint mode, `release-application.py`,
    the orchestration module's workflow resource and per-workflow role and `release.auto.tfvars.json`
    retire whole, every chain's machine starting a CLI-made workflow; the job role's remaining uses,
    9.4's DDL job among them, are read at 4.11; Stage 9 decision 15, D22 and D28 are amended by the
    sessions that hold them. The threat model's entry (6.3) carries the governed write held by a shared,
    AWS-written role that every member of Production's project assumes, decision 15's approver included.

## Cost

Measured rates, `us-west-2`, from [`docs/PRICING.md`](../../PRICING.md) and the pages read 2026-10-28:

- A Sandbox sitting: the hub's two `[D]` hosts and `sandbox/egress/`'s interface endpoints at 0.010 USD
  per hour each plus 0.010 per GB (`docs/NETWORK.md`), the `mwaa` group included; `cost-model.md`'s per
  session row.
- The workflow: MWAA Serverless 0.088 per task-hour (D7); the Glue job at 0.308 per DPU-hour on Glue
  6.0, two `G.1X` workers, about 0.05 per run of the length Stage 18 measured; the publishing task
  seconds on the worker.
- The catalog: metadata requests 10.00 per 100,000, storage 0.40 per GiB-month, a source's completed run
  in compute units at 1.776 each with 0.2 free a month, what a run over a one-table database consumes
  unmeasured (6f's Cost); no charge for a subscription, a data product or a listing (the DataZone
  pricing page, read 2026-10-28).
- The reads: Athena 5.00 per TB scanned, kilobytes here; a Spark session on `project.spark.fineGrained`
  at the Glue interactive-session rate.
- Pass 5: 1.44 per query-hour at 4 RPU with a 60-second minimum, data lake queries included in the
  RPU-hours, the copy at 0.024 per GB-month; the trial absorbs it to 2026-12-19 (287.51 USD left on
  2026-10-26).
- Stage 18's whole window in Staging billed USD 1.52 (2026-10-17 to 10-21); this stage's Sandbox passes
  are expected in the same order, measured at xvi.
- Pass 4 at rest, per target (Stage 18's Cost and 3.3): the project key, one customer-managed CMK at
  1.00 USD a month; the stack's log group at 731 days and the runs' groups, cents of storage; the
  `DataLake` source's daily run in compute units (1.776 each, 0.2 free a month), what a run over a
  one-table database consumes unmeasured; the Access Grants instance, the Athena service-linked role,
  the project, its environments, asset and listing free. The `datazone` endpoint in each target's
  `egress/` at 0.010 USD per hour while that slice is up, plus 0.010 per GB. Production's workflow runs
  cost what they cost today (D7), the operator's Glue job and processing job included.
- At rest in Sandbox nothing new: a project, its `DataLake` environment and database, an asset, a
  listing and a data product are `[P]` metadata, free; the project key exists. The stage creates no
  `[E]` resource of its own.

## Rollback

In this order, each write on the user's word: the subscription revoked
(`revoke-subscription --no-retain-permissions`, every piece read gone, 2.5's way); the data product's
listing and the asset's unpublished and both deleted by the owner in the portal; the table dropped by its
creator, the project role, from the query editor; the consumer project deleted
(`delete-project --skip-deletion-check`), its database kept by `Retain`; the application's branch left
unmerged or its publishing task gated. What stays: the lineage events and nodes, the source runs'
records and the listing's revisions, which no delete API reaches (`docs/SMUS.md`); the warehouse's copy
and view, dropped at 5.4.

Pass 4's rollback is Stage 18 pass 8 in each target, in its order and with its residues: the
subscription revoked and read gone on both sides; the applications removed by `delete-workflow` and
`delete-job`, the lineage entities, the `DataLake` sources, then the project with
`--skip-deletion-check` and its databases dropped once the stacks read gone; the Access Grants
location and instance, the Athena service-linked role, the log groups with no retention; the profile's
rows and the `deployment` profile, the blueprint configurations and their grants while the association
exists, the disassociation in the console, the rest of `<env>/studio/` from the working tree (the
projects bucket refuses `destroy`), Lake Formation's admins and `AllowFullTableExternalDataAccess`
returned by a full-replace `PutDataLakeSettings` (Lesson 60); the SCP's statement restored and the
battery's rows turned back; the deploy roles' documents and the `datazone` endpoints removed. What stays
in the domain: the members' user and group profiles, the lineage events and the subscription records
(Stage 18 8.1); in each account, the project key for its 30-day window. The application slices and the
orchestration module's workflow resources return from git.

## What this stage does not do

- Build a warehouse or enable the `RedshiftServerless` or `LakehouseCatalog` blueprint (D40): decision 9
  (b)'s target is read and priced, not built.
- Enable spaces or a SageMaker AI domain in a deployment project, or add a person to one beyond
  decision 15's approver (D17, Stage 18 question i and 6.1).
- Assign an LF-Tag to the product, or filter its rows and columns (P2; Stage 11 decision 12).
- Run 6f step 2 on `house-price`: what this stage reads on its own objects is cited there by the 6f
  session, never written there.
- Change the Data OU's denies, the root baseline's `datazone:CreateDomain` deny or any SCP statement
  but `DenyDataZoneEntirely` and the subscription deny 4.1 adds beside it.
- Vend an account or decide the per-unit grant shape (D35, Stage 14).

## What concerns the other sessions

- **Stage 6f's follow-up**: `GOVERNANCE.md:737`, the re-listing check (0.5), and 6f step 2's readings
  i, iii and iv, which pass 2 answers on the product; 6f 7.2 stays 6f's for the lake's tables (decision
  7 moot); 6f decision 4 is reversed by decision 6 (b), and the dated note in its row is that session's
  to write, since this session never edits the 6f file.
- **Stages 8-10** (the session "stages-8-10-nothing-up"): decision 6 (b) rewrites what Stage 18's
  verdict had kept. Stage 10's 1.1, 2.4 and 4.2 and its decision 9 are rewritten in that stage's file
  by its session, as 4.11 says; Stage 8's legs `staging-deploy`, `production-deploy` and `staging-test`
  take the CLI's form (4.9), decision 1's branch changes the template's workflow, manifest, script and
  tests, and 4.11 retires the application slices and `render-workflow.py`'s promoted mode; the
  orchestration module keeps its workflow resource for the warehouse workflow alone (decision 16). Each
  lands on the next tag's sitting, `runbooks/promotion.md` §N.8.2, and this stage's text is the
  obligation's record at both ends until that session writes its own (Lesson 34).
- **Stage 6d** (the session holding decision due 16): `governance/` is shared between 6d's 2.7 and this
  stage's 4.5; the two never share one apply (Stage 18 2.7's rule), and the `deployment` profile's
  `Tooling` configuration carries spaces off, never the `SageMakerAIDomain` blueprint.
- **"Redshift unload sem S3"**: pass 5 grants the warehouse's database user a Lake Formation read and
  nothing to the namespace role; `WH-1b` and 5b decision 5 stand.
- **"Mecanismo de cadastro no Glue"**: the `DataLake` environment `new_database` of 2026-10-28 is that
  session's or the user's; this stage neither uses nor removes it, and 1.1's `PRODUCT_DATABASE` names
  the database decision 2 (d) creates, the same name in every project.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Log:
[log-stage-19-smus-native-data-product.md](../../log/log-stage-19-smus-native-data-product.md)*
