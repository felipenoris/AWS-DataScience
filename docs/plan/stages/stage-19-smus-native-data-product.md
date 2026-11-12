# Stage 19 — A data product on SageMaker Unified Studio's native path, through a SageMaker application

| | |
|---|---|
| **Status** | **Decision 6 taken 2026-10-31 by the user as (b), the AWS model** ([log](../../log/log-stage-19-smus-native-data-product.md)): *"Decido pelo modelo da AWS, com o uso previsto do SMUS e promoção entre ambientes via ferramenta SMUS CICD CLI"*. Staging and Production each gain a deployment project, the CI/CD CLI deploys every stage, and Production publishes its own product; D41 item 2 is reopened, 6f decision 4 reversed, `DenyDataZoneEntirely`'s revision trigger fired. Passes 3 and 4 rewritten the same day around [Stage 18](stage-18-staging-deployment-project.md)'s recipe, decisions 13 to 16 added, and **every decision taken the same day, one at a time**: 1 (a), 2 (a) with (d), 3 (a) gated by `PUBLISH_LISTING`, 4 (a), 5 as recommended with `eighth-experimentation` as Production's consumer, 9 (a), 11 rows by class for the governed accounts, 12 outside, 13 (b) with a subscription deny, 14 (a) with (d), 15 (a), 16 (b) against the recommendation; 7 and 8 moot by decision 6 (b); **10 taken 2026-11-09** as amended by it, on in `dev` and `test` (*"Keep it on"*). **1.1 written 2026-10-31** in `examples/app-etl/`: the Iceberg write, the publishing task, the two stage variables, the tests, the render's interim rows; 3.1 and 3.3 wait on the inputs the same reading found missing (the lint's rule, the deployment projects' values); nothing changed in AWS that day. **Pass 1 prepared 2026-11-08** ([PR #283](https://github.com/felipenoris/AWS-DataScience/pull/283)): the publishing task takes its identifiers from the deploy's `{domain.id}` and `{proj.id}`, the project role holds `datazone:StartDataSourceRun` from `sandbox/workflows/` (applied 21:50 UTC, `awsds-sandbox-workflows` `v4`, the day's one AWS write), and the sitting's order with this pass's values is the list before 1.2: the window holds the hub, Sandbox's `egress/` and a space running a package unattended, the portal's acts come before it, the readings after it and GitLab's mirror at its next sitting; decision 10's OpenLineage settings are in the template since the same day ([PR #284](https://github.com/felipenoris/AWS-DataScience/pull/284)). **Pass 1's sitting run 2026-11-10** (01:28 to 04:09 UTC): four runs, the first three failing in `publish` on what the catalog answered (`SUP-343`, `SUP-345`) and fixed between them, the fourth `SUCCESS`; the product table is Iceberg and registered with Lake Formation, its asset imported and listed, 1.3's metadata kept across the source's updates and carried to the listing, the job's lineage linked to the asset in the domain; verification ii's negative was admitted (`SUP-346`, `TM-29`), and decision 17, taken 2026-11-11 as (a) with (d), keeps the grant with `CT-13` as its check; the mirror waits for the next GitLab sitting. **Prepared after it, 2026-11-10, nothing up**: pass 2's sitting in order (its portal half needs no window), 3.1's code reading (the bundle exports the catalog of its own stage's project, whole), decision 18 read against SMUS's own path and taken 2026-11-11 as (d), a project for the application alone as `dev` (1.5), and pass 4 read against pass 1. On two readings of the same day (the CLI's import writes `dev`'s account into a target's asset, and Sandbox's one Glue catalog holds `app_etl` once), **decision 19 taken 2026-11-11 as (c)**: no `test` stage, every promotion crossing an account, Sandbox → Staging → Production, with Staging importing the catalog unlisted; decision 20 taken the same day as (b): Production alone lists a chain application's product. **The estate reviewed against decisions 17 to 20 on 2026-11-11, and pass 4 opened with nothing up** (§The estate against decisions 17 to 20; [PR #288](https://github.com/felipenoris/AWS-DataScience/pull/288)): 4.2 done, Staging and Production associated by the RAM call the console makes (`SUP-349`); 4.1 written, its deny half measured on a candidate parked on `Policy Test`, **applied at 14:23 UTC** on the user's word, its allow half and the subscription deny read from both accounts (the battery 52 as expected, 0 unexpected, 5 not measured); 4.4 applied in `staging/studio/` and `production/studio/`, 16 added each and then the `Tooling` and `DataLake` configurations; 4.5's profiles `deployment-staging` and `deployment-production` applied; **4.6 done**: `deploy-staging` (`5ido8bej1zoeq8`) and `deploy-production` (`d7qcazihvr3s7k`) created, each with its `Tooling` environment and the database `app_etl`, whose environment carries a subscription target (xix); `AllowFullTableExternalDataAccess` `true` in both accounts from the provisioning until **4.7, the user's act of 2026-11-12** (01:50 UTC; `DT-13` passing, `EXC-23` closed, no vend in either trail while it stood); the project roles' grants, the deploy roles' policy and the CLI import's grants applied at 16:16 to 16:18 UTC, the five slices re-planning `No changes`; `awsds-deploy-staging` an owner of `deploy-staging` since the user's call of 2026-11-12, `awsds-deploy-prod`'s membership waiting for the role's first call; the role's reach in Production read the same day (`TM-30`) and the instruments reading the two projects (`US-11`, `US-12`, `DT-13`, `DT-14`, `CT-14`); **decision 21 taken the same day as (b)**, a fence in the targets' D13 boundary, written in `sagemaker-prereqs-v0.10.0` and **applied in both `studio/` slices at 18:25 UTC** on the user's word, the boundary at 15 statements in Production and 14 in Staging, `DT-14` passing and each role simulated under it; 4.3 written; the pipeline's change cut in two releases, T (the `test` stage retired on today's legs, written in the template the same day) and F (the CLI's legs, 4.9 to 4.11). **Release F written 2026-11-12 with nothing up** ([PR #291](https://github.com/felipenoris/AWS-DataScience/pull/291); §Release F as written): the template's three stages with the catalog and the warehouse workflow, the legs on `scripts/deploy-application.py`, the chain layer as `orchestration-v0.3.0` in `<env>/chains/`, and the grants around the deploy; every slice planned. **The grants that need nothing up applied the same day**, 03:40 to 03:42 UTC on the user's word: both `studio/` slices (2 added and 2 changed each), both `foundation/` slices (1 changed each) and `production/warehouse/` (1 added), the five re-planning `No changes`, `DT-13` and `DT-14` passing and each project role simulated as a worker and as a person. Both `chains/` slices are unapplied and nothing is in GitLab; the lint's rule is [`awsds-workflows` PR #25](https://github.com/felipenoris/awsds-workflows/pull/25), opened the same day on the user's word and theirs to merge; decisions 22 to 24 taken the same day, each as (a), the code standing as written. **Written 2026-10-28, nothing run**: the plan, the review of the catalog across the plan and the estate, the user's three questions answered from measurements and dated pages, and every decision due with its recommendation. The readings of 2026-10-28 are read-only, as the infrastructure user; no apply, no AWS write, no portal act. Pass 0 runs with nothing up; passes 1 to 3 are Sandbox sittings; pass 4 runs as promotion sittings once passes 1 to 3 have run; pass 5 inside a Sandbox warehouse sitting after 4.12 |
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
| D41 | item 2, kept 2026-10-22: no project in a target; "What A gives up for now is a catalog publication and lineage from Production, and `DenyDataZoneEntirely`'s revision trigger already names that moment" | **item 2 reopened 2026-10-31** by decision 6 (b), the user's: alternative B, a project in each deployment account and the CLI deploying every stage, is built by pass 4 at Stage 18's measured price; items 5 (the chain layer) and 1, 3, 4, 6 to 8 stand; item 9 (the application slice owns the Glue job) retires for the targets, where the operator creates the job as in `dev` and `test`; item 3's `test` project leaves the chain (decision 19 (c), 2026-11-11) |

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
| 8 | the application slice's table "declared here by the deploy role, which holds CREATE_TABLE on app_outputs" (`staging/app/app-etl/main.tf:91-92`); `lint-plan.py` fails "a plan that leaves no `aws_glue_job`"; the promoted lint's rule (a) refuses every `{proj.*}`, `dzd-`, `datazone_usr_role_*`; decision 26 the base pin | **amend** with decision 6 (b): the legs `staging-deploy` and `production-deploy` run the CLI's `deploy` from the stored bundle as the deploy role (4.9), the render, the promoted lint's rule (a) and `lint-plan`'s `aws_glue_job` rule retire with the application slices (4.11); `staging-test` reads the table in the project database (decision 14); the gates, `store-bundle`, `staging-gate` and `production-gate` stand; since decision 19 (c), `test-deploy` gives way to a bundle job and a release raises no Sandbox `egress/` |
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
| `examples/app-etl/` | `manifest.yaml` with `storage` and `workflows`, no `catalog`; `transform.py`'s `write_table` writes Parquet by path, no catalog call; no task touches the catalog; `render-workflow.py` removes keys, never a task; `test-deploy` empties the `test` project's `app-etl/` prefix before each deploy | **amend** (pass 1, decisions 1 to 3): the Iceberg write into `{env.PRODUCT_DATABASE}`, the publishing task and the two stage variables, written 2026-10-31 (1.1); `content.catalog` at 3.1 after the lint's release; the render's interim rows until 4.11; a table registered in `test`'s catalog survives the prefix's emptying |
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

## The estate against decisions 17 to 20

Read on 2026-11-11 at the user's request, with nothing up, from `main` at `d423543c`: what each of the
four decisions of that day changes in the estate, in the pipeline and in the documents, where the
change is written, whose hand it is and what it waits on. The Stages 8-10 session named below under
"What concerns the other sessions" is no longer running, so this review also carries those stages'
side: the dated amendments in the Stage 8 and Stage 10 files are this sitting's.

The decisions, in one line each: **17 (a)** keeps the publishing task's `StartDataSourceRun`, in every
project role that runs the task, with `CT-13` as its check; **18 (d)** makes a Sandbox project for
app-etl alone the manifest's `dev` stage, whose catalog the bundle carries; **19 (c)** retires the
`test` stage, so every promotion crosses an account; **20 (b)** lists the product in Production alone.

### The pipeline changes in two releases

Decision 19 (c) and decision 6 (b) both change the tag's pipeline, and they do not depend on each
other. The retirement of the `test` stage needs nothing of pass 4, so it ships first.

| | Release T: the `test` stage retired | Release F: the CLI's legs |
|---|---|---|
| Carries | decision 19 (c) and 20 (b) in the template, with pass 1's product table and publishing task, already in `examples/app-etl/` | decision 6 (b), 14, 16 (b) and 18 (d): 4.9 to 4.11 |
| Manifest | the stage `dev` alone, `PUBLISH_LISTING` false; `content.catalog` off | the stages `dev`, `staging` and `prod`; `content.catalog` enabled with `skipPublish`; `PUBLISH_LISTING` true in `prod` alone; the `prod` stage's bootstrap runs `app-etl` |
| Sandbox's job | `bundle` in place of `test-deploy`: `aws-smus-cicd-cli bundle --targets dev` as `awsds-deploy-sandbox-test`, no deploy, no run, no read of Sandbox's `egress/`; it fails on the CLI's *"Failed to get project connections"*, the line a non-member reads (`SUP-352`) | the same job, plus the guard on `catalog/catalog_export.json` (3.1) |
| `store-bundle`, `release`, the gates | unchanged but for their `needs` | unchanged |
| The legs | today's: `release-application.py`, the render, the application and orchestration slices | `deploy --targets staging` and `prod` from the extracted bundle with `--bundle-archive-path`, as the deploy role (4.9); the Terraform path retires (4.11) |
| The release's first run | Staging's leg, `staging-test` | the same |
| The lint | the pin `d856982c` passes the one-stage manifest (read 2026-11-11) | a release of `awsds-workflows` whose rule `manifest` admits `content.catalog` with `skipPublish` true and no `assets.access` |
| What it needs in AWS | items 15 to 18 of the table below: one `sandbox/workflows/` apply, the `dev` project and the role's membership of it | pass 4's items 1 to 14, then 4.10's sitting |
| Its sitting | the next GitLab sitting, [`runbooks/promotion.md`](../runbooks/promotion.md) §N.8.2, with a Staging leg | promotion sittings after pass 2 and 1.5 |

Release T was written on 2026-11-11 in `examples/app-etl/` (the manifest, `.gitlab-ci.yml`, the
README) and in `sandbox/workflows/deploy-role.tf`. The CLI 1.0.9's `bundle` ran on the laptop on the
one-stage manifest as Sandbox's `InfrastructureAccess`: exit 0, the same 11 files a `test-deploy`
bundle carried; the template's tests (72 passed, 1 skipped), ruff, the pinned lint and the render check
pass. Nothing of it is in GitLab until the mirror.

Release F was written on 2026-11-12, before release T's sitting (§Release F as written). `main`
holds both: `examples/app-etl/` is release F's tree from that day, and release T's is the tree of
commit `36bcf916`, which its merge request takes
([`runbooks/promotion.md`](../runbooks/promotion.md) §N.8.4). What release T's legs run did not
change: `scripts/release-application.py`, `render-workflow.py`, `lint-plan.py` and the slices
`<env>/app/app-etl/` and `<env>/orchestration/` are as they were, and `scripts/model-chain.py`
keeps the outputs layout unless a leg passes `--project`. Release F's Terraform sits beside them, in
new slices and in statements nothing of release T uses.

### What each decision changes, and where it stands

A **[P]** item needs nothing up. An apply is the user's from a saved plan, since the app's classifier
refused Claude every `terraform apply` of this sitting; a read, a `create-project` and the RAM call
were not refused.

| Item | Change | Decision | Where | Hand | Waits on | On 2026-11-11 |
|---|---|---|---|---|---|---|
| 1 | `DenyDataZoneEntirely` excepts the SSO `InfrastructureAccess` role, `awsds-deploy-*` and `datazone_usr_role_*`; `DenyDataZoneSubscriptionRequests` denies the request to all | 13 (b) | `identity/org-policies/`, `POLICIES.md`, the battery's rows | **[Claude⚡]** on the user's word | nothing | **applied** 14:23 UTC; the deny half measured on a candidate, the allow half and the subscription deny by the battery at 14:27 UTC (52 as expected, 0 unexpected, 5 not measured) |
| 2 | Staging and Production associated to the domain | 6 (b) | the domain's RAM share | **[Claude⚡]** | nothing | **done** 04:37 UTC (`SUP-349`) |
| 3 | `SMUS_ASSOCIATED` and `SMUS_DEPLOYMENT_MEMBERS` name both targets; the `studio` emission and rank | 6 (b) | `scripts/tfhygiene/` | [Claude] | item 2 | written; only `governance/`'s `members` moves |
| 4 | Each target's blueprint prerequisites: the two roles, the D13 boundary, the project key, the projects bucket, the log group, the person-session policy | 6 (b), 15 | `staging/studio/`, `production/studio/` | **[Claude⚡]** on the user's word | nothing | **applied**, 16 added each (Staging by 14:25 UTC, Production by 14:27), read back |
| 5 | Each target's `Tooling` and `DataLake` configurations, their grants and the workflows policy | 6 (b), 17 | the same slices, a second plan | **[Claude⚡]** on the user's word | items 1 and 4 | **applied** by 15:19 UTC, 5 added and 1 changed each; each target lists `Tooling` and `DataLake` |
| 6 | The profiles `deployment-staging` and `deployment-production` and their create grants | 6 (b) | `governance/`, `deployment_profiles_enabled` | **[Claude⚡]** on the user's word | item 5. Each target's `InfrastructureAccess` holds its group profile: Staging's since Stage 18 (`65b0f127-…`), Production's since its first `GetProject` on 2026-11-11 (`ca2735c9-…`; a list call creates none, `SUP-159`) | **applied** by 15:23 UTC, the second grant in a second apply (`SUP-353`); the switch on |
| 7 | The projects `deploy-staging` and `deploy-production`, and the database `app_etl` in each | 2 (d), 6 (b) | `datazone create-project`, `create-environment` | **[Claude⚡]** | item 6 | **done** 15:26 to 15:32 UTC: `5ido8bej1zoeq8` and `d7qcazihvr3s7k`, each with `Tooling` and the database's environment, which carries a subscription target (xix) |
| 8 | `AllowFullTableExternalDataAccess` after provisioning | 4.7 | Lake Formation's settings | **[user]** | item 7 | **done 2026-11-12**, 01:50 UTC: the user's `put-data-lake-settings` in each account, the settings as read with the flag `false`, the API write having been refused to Claude by the app's classifier. `true` in both from the provisioning (15:26 and 15:29 UTC) until then; after it the key absent, the three administrators and the parameters kept, `DT-13` passing |
| 9 | The workflows grant and the person-session deny on each project role | 15, 17 | `<env>/studio/project-roles.tf` | **[Claude⚡]** on the user's word | item 7 | **applied** 16:16 UTC, 2 added each |
| 10 | The three policy grants the CLI's catalog import checks on the root domain unit | 18 (d) | `governance/`, `catalog_import_projects` | **[Claude⚡]** on the user's word | item 7 | **applied** 16:18 UTC, 6 added with `-parallelism=1` (`SUP-351`, `SUP-353`) |
| 11 | The deploy roles' grant for the CLI's deploy into the project | 6 (b) | `<env>/foundation/deploy-project.tf` | **[Claude⚡]** on the user's word | item 7 | **applied** 16:17 UTC, 2 added each; simulated as each deploy role |
| 12 | The deploy roles made `PROJECT_OWNER` of their project | 6 (b) | `create-project-membership` | **[user]** | item 7; and the role's group profile, which DataZone creates at the role's first read of a project (`SUP-159`): `awsds-deploy-staging`'s exists since Stage 18 (`9bead345-…`, read 2026-11-11), `awsds-deploy-prod`'s waits for a pipeline run | **Staging's done 2026-11-12**, 01:50 UTC, the user's call, refused to Claude by the app's classifier: `deploy-staging` lists the group as `PROJECT_OWNER`. `awsds-deploy-prod`'s not started |
| 13 | `staging-test`'s door to the product table: the deploy role's Lake Formation grant and its Athena read | 14 (d) | `staging/studio/`, written with the leg | **[Claude⚡]** on the user's word | item 7 and 4.9 | **written and applied 2026-11-12** (03:40 UTC): `DESCRIBE` on `app_etl` and its tables in `staging/studio/staging-test.tf`, read by `glue:GetTable`; both grants read back, neither grantable; the Athena read not written, by decision 24 (a) |
| 14 | A `datazone` endpoint in each target's compute VPC | 6 (b) | `staging/egress/`, `production/workloads-egress/` | the next `make up` | nothing | written; 8 endpoints each |
| 15 | `awsds-deploy-sandbox-test` narrowed to the bundle's reads: the workflow, storage and key grants leave, every `PassRole` is denied | 19 (c) | `sandbox/workflows/deploy-role.tf` | **[user]** applies, in release T's sitting | the template's merge request, which stops calling what leaves | written; planned 0 to add, 3 to change, 2 to destroy |
| 16 | The Sandbox project for app-etl alone | 18 (d) | the portal, as the data scientist | **[user]** | nothing for the project; its database `app_etl` waits on item 20 | not started (1.5) |
| 17 | The bundle role a member of that project, and of `test-experimentation` no longer | 19 (c) | the portal or `create-project-membership` | **[user]** | item 16 | not started |
| 18 | That project's role in `project_roles`, and `DEV_PROJECT_NAME` in GitLab's CI/CD variables | 18 (d) | `sandbox/workflows/variables.tf`; GitLab | **[user]** applies | item 16 | not started |
| 19 | The application removed from `test-experimentation`: its two workflows, the Glue job `app-etl-<project id>`, the `shared/app-etl/` prefix | 19 (c) | the MWAA Serverless, Glue and S3 APIs | **[Claude⚡]** on the user's word | release T's first pipeline | not started |
| 20 | `eighth-experimentation`'s product retired, in the rollback's order, so the name `app_etl` is free | 2 (d), 19 (c) | the portal and the query editor | **[user]** | pass 2 and verification v's look | not started (1.5) |
| 21 | GitLab's CI/CD variables: the four `TEST_PROJECT_*` removed; `SUBNET_AZ1`, `SUBNET_AZ2`, `DEV_PROJECT_SG`, `DEV_PROJECT_KEY_ARN` and `TRAINING_IMAGE_URI` no longer read by any job | 19 (c) | `awsds/app-etl`'s settings | **[user]** | release T's merge request | not started |
| 22 | The form type `classification`'s owner | 4, 18 (d) | `governance/`'s `form_type_owners` | reading first | 1.5 | open |
| 23 | The lint's rule `manifest` admits `content.catalog` | 18 (d) | `awsds-workflows`, then the template's pin | [Claude], **[user]** merges | release F | **written 2026-11-12 as a patch** over `d856982c`: `content.catalog` passes with `skipPublish` true and no `assets.access`; its 6 new tests pass, and the suite's 7 failures are the pinned commit's own. The patch is `$HOME/tmp/stage19-awsds-workflows-catalog-rule.patch`, beside the saved plans. **Opened 2026-11-12** on the user's word as [`awsds-workflows` PR #25](https://github.com/felipenoris/awsds-workflows/pull/25), with that repository's guide, lab notes and memory: the new cases fail at `d856982` and pass on the branch, its three test jobs pass, and its lint answers the template `ok: 9 arquivo(s)`; the merge is the user's |
| 24 | The instruments: `studio.py` reads the targets associated, their two configurations and the deployment profiles; the battery's rows; `catalog.py`'s product road | 6 (b), 11, 13 | `aws/` | [Claude] | 6.1 for `catalog.py` | `studio.py` (`US-8`, `US-11`, `US-12`), `deploytargets.py` (`DT-13`, `DT-14`), `catalog.py` (`CT-13`'s trails, `CT-14`) and the battery written; `DT-14`'s row on the services each target's fence denies written 2026-11-12, after act 1's applies, and passing in both; the product road's checks at 6.1 |
| 25 | The fence in each target's D13 boundary: the account's buckets, customer managed keys, secrets and repositories, every `sts:AssumeRole`, and the services a target has no use for | 21 (b) | `terraform-modules/sagemaker-prereqs/` `v0.10.0`; `<env>/studio/main.tf` and `fence.tf` | **[Claude⚡]** on the user's word | nothing | **applied** 18:25 UTC, 1 changed each, the boundary at `v2`; `DT-14` passes in both, each role simulated under the attached boundary |
| 26 | The chain layer over the workflows the CLI creates: a machine finds its workflow by name and passes the run the stage's variables | 16 (b), 23 | `terraform-modules/orchestration` at `orchestration-v0.3.0`; `staging/chains/`, `production/chains/` | [Claude], **[user]** applies | the account's `orchestration/` gone first, its machines, roles and log group carrying the same names; a run needs 4.10's deploy | **written 2026-11-12**; planned 24 to add in Production and 18 in Staging; the definitions answer `OK` to `states:ValidateStateMachineDefinition` |
| 27 | The fence's warehouse half, and decision 15's deny grown to a warehouse session | 15, 16 (b), 21 (b) | `<env>/studio/fence.tf`, `main.tf`, `person-session.tf` | **[Claude⚡]** on the user's word | nothing | **written and applied 2026-11-12** with items 13 and 28: 2 added and 2 changed in each `studio/` at 03:40 UTC, the boundary at `v3` and the person-session policy at `v2`; each role simulated as a worker and as a person |
| 28 | The load's session on the governed workgroup, as Production's project role | 16 (b) | `production/studio/warehouse.tf`; `production/warehouse/`, 5439 from the project's security group; the warehouse's SQL for the role's `IAMR:` user | **[Claude⚡]** on the user's word; the SQL in a warehouse sitting | item 27 | **written and applied 2026-11-12**: `awsds-prod-warehouse-load` attached to the project's role (03:40 UTC) and `production/warehouse/`'s rule `sgr-021fb49c3c05b5697` (03:42 UTC); the role simulated `allowed` on `redshift-serverless:GetCredentials` as a worker and denied as a person; the SQL not run |
| 29 | The deploy role around the deploy: the stage variables' record, the pass of the project role to SageMaker, the product table's metadata | 14 (d), 23 | `<env>/foundation/deploy-project.tf` | **[Claude⚡]** on the user's word, the plan taking the alerts var-file | nothing | **written and applied 2026-11-12** (03:41 UTC): 1 changed in each, the policy at `v2` and 16 statements, 4,564 characters of 6,144 in Production and 4,579 in Staging |
| 30 | The template's release F: three stages, the catalog and its guard, the warehouse workflow, the legs | 6 (b), 14, 16 (b), 18 (d), 19 (c), 20 (b) | `examples/app-etl/`; `scripts/deploy-application.py`, `scripts/tfhygiene/projects.py`, `scripts/model-chain.py --project` | [Claude]; **[user]** the merge request | item 23 for the pin; items 16 to 18 for the `dev` project; 1.5 for `product.json`'s names | **written 2026-11-12**: 84 tests pass, the CLI 1.0.9's `describe` parses the three stages, `deploy-application.py --check` reads both projects |
| 31 | The Terraform path retired after release F's first promotion: `<env>/orchestration/` and `<env>/app/app-etl/` destroyed and their folders removed, with `release-application.py`, `render-workflow.py`, `lint-plan.py`, the application's grants on `app_outputs`, `apply-orchestration.tf`, `apply-application.tf`'s Glue and table statements, the application ceiling and `model-chain.py`'s outputs layout; the leg's two chain statements move to `deploy-project.tf` | 6 (b), 16 (b) | a pull request after the promotion | **[user]** destroys, [Claude] the pull request | 4.10 green in both targets | not written. Previewed 2026-11-12 with `plan -destroy`: 41 to destroy in `production/orchestration/`, 3 in `production/app/app-etl/`, nothing in Staging's two |
| 32 | The governed read as the project role: the workflow's argument and `--conf`, the Lake Formation read in `<env>/data/`, the deny's growth to the lake | 22 | the template; `<env>/data/`; `<env>/studio/person-session.tf` | [Claude]; **[user]** applies | a release after F, by decision 22 (a); a measurement in the `dev` project first | not written |

### The applies of pass 4 with nothing up, in order

Each is the infrastructure user's (`InfrastructureAccess`), run from the worktree that holds the
saved plan or re-planned from `main` after this branch merges (Lesson 79). `NO_PROXY='*'` and
`TF_PLUGIN_CACHE_DIR` as [`runbooks/terraform-changes.md`](../runbooks/terraform-changes.md) §1.

1. **The SCP**, account **Identity**, profile `awsds-infra-identity`: `terraform -chdir=terraform-live/identity/org-policies apply -input=false "$HOME/tmp/stage19-scp-41.tfplan"`.
   **[Claude] reads** after it, a minute or more later (`SUP-350`): the re-plan, `./aws/org-policies.py`,
   the battery's phase `ou`, `datazone list-domains` and `list-environment-blueprint-configurations` from
   both targets, `./aws/studio.py` (verification xviii). **Applied 2026-11-11 at 14:23 UTC, and read.**
2. **The prerequisites**, accounts **Staging Account** and **Production**, profiles `awsds-infra-staging`
   and `awsds-infra-prod`: `apply -input=false "$HOME/tmp/stage19-studio-staging-1.tfplan"` in
   `terraform-live/staging/studio`, and `stage19-studio-production-1.tfplan` in
   `terraform-live/production/studio`. Independent of 1. **Applied 2026-11-11**, 16 added in each.
3. **The configurations**: once 1 and 2 are applied, **[Claude] plans** each `studio/` again with no
   `-var`, expecting the two configurations, their grants, the key policy's statements and the workflows
   policy; **[user]** applies both. **Planned 2026-11-11**, 5 to add and 2 to change in each: account
   **Staging Account**, profile `awsds-infra-staging`, `terraform -chdir=terraform-live/staging/studio apply
   -input=false "$HOME/tmp/stage19-studio-staging-2.tfplan"`; account **Production**, profile
   `awsds-infra-prod`, the same in `terraform-live/production/studio` with
   `stage19-studio-production-2.tfplan`. **Applied 2026-11-11**, 5 added and 1 changed in each.
4. **The profiles**, account **Data Governance**, profile `awsds-infra-data`: **[Claude]** sets
   `deployment_profiles_enabled` true and plans `governance/`, expecting the two profiles and their two
   grants and nothing on `experimentation`; **[user]** applies. A plan that touches another profile
   stops the step. **Applied 2026-11-11**: the two profiles and one grant, then the second grant in an
   apply of its own, two grants of one type on one unit colliding when created at once (`SUP-353`).
5. **[Claude⚡] The projects and their database** (4.6), then **[user]** the flag (4.7). **Done
   2026-11-11**; the flag, `true` in both accounts after it, **turned off by the user on 2026-11-12**
   at 01:50 UTC (`DT-13` passing).
6. **The project's names into three slices**: `project-roles.tf` in each `studio/`,
   `deployment_project_role` in each `foundation/` (its plan takes the alerts var-file),
   `catalog_import_projects` in `governance/`; **[Claude] plans**, **[user]** applies. **Planned
   2026-11-11** and saved under `$HOME/tmp/`: `stage19-studio-staging-3.tfplan` and
   `stage19-studio-production-3.tfplan` (2 to add each), `stage19-foundation-staging-deploy-project.tfplan`
   and `stage19-foundation-production-deploy-project.tfplan` (2 to add each), and
   `stage19-governance-catalog-import.tfplan` (6 to add, applied with `-parallelism=1`). **Applied
   2026-11-11, 16:15 to 16:18 UTC**, on the user's word; the five slices re-plan `No changes`.
7. **The fence** (decision 21 (b)), accounts **Production** and **Staging Account**: `apply -input=false
   "$HOME/tmp/stage19-studio-production-fence.tfplan"` in `terraform-live/production/studio` as
   `awsds-infra-prod`, and `stage19-studio-staging-fence.tfplan` in `terraform-live/staging/studio` as
   `awsds-infra-staging`: 0 to add and 2 to change in each, the boundary's new version. **[Claude]
   reads** after them the re-plans, `DT-14` and the simulation as each role. **Applied 2026-11-11,
   18:25 UTC**, on the user's word: 1 changed in each, the boundary (`SUP-356`); both slices re-plan
   `No changes`, `DT-14` passes in both targets and each role reads the fence's denies under the
   attached boundary.

### Release F as written

Written 2026-11-12 with nothing up ([PR #291](https://github.com/felipenoris/AWS-DataScience/pull/291), the log), every call of the writing a read; act 1's applies ran the same day. What follows is what
the code is, the plans saved under `$HOME/tmp/`, and the order of the acts, each apply on the
user's word naming it and re-planned first if `main` moved.

| Piece | Where | Read or planned on 2026-11-12 |
|---|---|---|
| The manifest's stages `dev`, `staging` and `prod`; `content.catalog` with `skipPublish`; `app-etl-warehouse` in `content.workflows` | `examples/app-etl/manifest.yaml` | the CLI 1.0.9's `describe` lists the three targets and their bootstrap actions; the lint passes with item 23's patch and refuses the catalog item at the pinned commit |
| The warehouse workflow in the project: the task creates its Glue job, which reads the product table | `workflows/app-etl-warehouse.yaml`, `glue/load_warehouse.py` | the template's tests |
| The catalog's guard | `scripts/check-catalog-export.py`, `product.json` (the asset `trades_notional` required, the form type `classification` allowed) | its tests: an export with more, with less or absent fails |
| The legs | `.gitlab-ci.yml`: `staging-check`, `staging-deploy`, `staging-test`, `staging-model`, `production-check`, `production-deploy`, the model chain's jobs with `--project` | `scripts/check-gitlab-ci.py` |
| The leg's deploy | `scripts/deploy-application.py`, `scripts/tfhygiene/projects.py` | `--self-check` (in `make check`); `--check` as `InfrastructureAccess`: `deploy-staging` and `deploy-production` answer their subnets, security group, key and shared prefix, the caller a member of each |
| The chain layer | `terraform-modules/orchestration` at `orchestration-v0.3.0`, `<env>/chains/` | `stage19-chains-production.tfplan`, 24 to add; `stage19-chains-staging.tfplan`, 18 to add; the three definitions `OK` at 02:45 UTC |
| The fence's warehouse half, the deny's growth, Staging's `DESCRIBE`, Production's load policy | `<env>/studio/` | `stage19-f-production-studio.tfplan` and `stage19-f-staging-studio.tfplan`, 2 to add and 2 to change in each; **applied** 03:40 UTC |
| The deploy role around the deploy | `<env>/foundation/deploy-project.tf` | `stage19-f-production-foundation.tfplan` and `stage19-f-staging-foundation.tfplan`, 1 to change in each; **applied** 03:41 UTC |
| 5439 from the project's security group | `production/warehouse/` | `stage19-f-production-warehouse.tfplan`, 1 to add; **applied** 03:42 UTC |

A leg applies no Terraform. `scripts/deploy-application.py` checks the bundle's SHA256, reads the
project's Tooling environment for the stage's variables, extracts the bundle beside the tag's
manifest and runs the CLI's `deploy` with `--bundle-archive-path`. It fails on the exit status, on
a log with no *"Tooling VPC config"* line (`SUP-285`), on a catalog import whose summary reads
anything but `Failed: 0` (`SUP-357`) and on a workflow of the stage's bootstrap it cannot find by
name. Then it writes the stage's variables to `/awsds/<env>/applications/<app>/stage-variables`,
which a chain's machine reads and passes to the run it starts (decision 23).

The order of the acts:

1. **Nothing up, three applies that touch nothing release T uses**, before or after its sitting:
   both `studio/` slices (`awsds-infra-staging`, `awsds-infra-prod`); both `foundation/` slices, their
   plans taking the alerts var-file; `production/warehouse/`. **[Claude] reads** after them the
   re-plans, `DT-14`, and each project role simulated on `redshift-data`, `sqlworkbench` and
   `redshift-serverless:GetCredentials`. **Applied 2026-11-12, 03:40 to 03:42 UTC**, on the user's
   word, from the five saved plans; the five slices re-plan `No changes`, `DT-13` and `DT-14` pass
   in both targets, and the simulation reads Production's role `allowed` on
   `redshift-serverless:GetCredentials` as a worker and denied as a person, denied on
   `redshift-data` and `sqlworkbench` either way, and Staging's role denied on all three. `DT-14`
   reads the services each boundary's fence denies since the same sitting.
2. **The lint**: the pull request in `awsds-workflows` from item 23's patch, the user's merge; the
   template's `AWSDS_WORKFLOWS` takes that commit. **Opened 2026-11-12** as PR #25; the pin moves
   once it is merged.
3. **Release T's sitting and the Sandbox sitting** (the sittings below): the `dev` project for app-etl
   alone, its product curated at 1.5, and `product.json` brought to what that project owns.
4. **Release F's promotion sitting**, the hub, GitLab and Staging's `egress/` up:
   `staging/chains/` applied, Staging's `orchestration/` and `app/app-etl/` being down since its last
   `make down` (read 2026-11-12: nothing to destroy in either); the template's merge request from
   `examples/app-etl/` with the pin moved; the tag; `bundle` with the guard, `store-bundle`,
   `release`; `staging-gate`, `staging-check`, `staging-deploy`, `staging-test`, `staging-model`.
5. **`production-check`** fails once, on the membership: `awsds-deploy-prod`'s group profile exists
   from that call, the user makes it `PROJECT_OWNER` of `deploy-production` (item 12) and retries the
   job. Then `production-gate` and `production-deploy`, `production/workloads-egress/` up: the
   bootstrap creates the three workflows and runs `app-etl`, whose last task lists the product.
6. **Production's cut-over, after that deploy is green**: `production/orchestration/` destroyed (41)
   and `production/app/app-etl/` (3), as `awsds-infra-prod`; `production/chains/` applied (24). The
   CLI's workflows and the old ones carry different names, so the deploy needs no cut-over; the
   chain layer's names are the same in both slices, so the old one goes first. A chain started by
   hand reads xxix.
7. **A warehouse sitting**: the compute up; as the admin, `CREATE USER "IAMR:<the project role>"
   PASSWORD DISABLE NOCREATEDB NOCREATEUSER` and `GRANT ROLE gov_trades_rw` to it (Stage 9 9.3's
   shape); `production-warehouse-ddl`; the warehouse chain started by hand (xxxii).
8. **The retirement** (item 31), a pull request once both targets ran release F.

What release F leaves unwritten, each with its owner: the governed read, a later release's by
decision 22 (a) (item 32); the Athena read of the product table, unwritten by decision 24 (a);
the warehouse's SQL (act 7); the retirement
(item 31); `aws/orchestration.py`'s rules, which read the Terraform-made names and are written
with act 6 so that they are not red before it (Lesson 50);
Stage 10's 1.1, 2.4 and 4.2 and its decision 9, D22 and D28, and
[`runbooks/sagemaker-application.md`](../runbooks/sagemaker-application.md) §M, §P, §S, §T and §W,
which describe the legs GitLab runs until the merge request of act 4 lands (6.2).

### The sittings that follow, in order

1. **Nothing up, the user's applies**: the list above, each followed by Claude's reads. It ends with
   both deployment projects standing, their database `app_etl`, their grants and the deploy roles'
   policy.
2. **Nothing up, the portal**: the Sandbox project for app-etl alone and the bundle role's membership
   (items 16 and 17), which release T needs; pass 2's acts 1 to 3 in `eighth-experimentation` (the
   consumer project, the data product, the subscription, the approval, the query editor's read).
3. **A GitLab sitting with a Staging leg, release T** ([`runbooks/promotion.md`](../runbooks/promotion.md)
   §N.8.2): `sandbox/workflows/` applied, the template's merge request, the tag, the bundle, Staging's
   leg as the release's first run, Production's. The deploy roles' first call to the domain belongs to
   release F; nothing of this release reaches a deployment project.
4. **A Sandbox sitting**: pass 2's window (the space's Spark read, decision 17's reads as a
   non-member, xi's negative, the revoke), then 1.5 in the project for app-etl alone, once
   `eighth-experimentation`'s product is retired (item 20).
5. **Nothing up, release F written**: the lint's release (item 23), the manifest's `staging` and `prod`
   stages with `content.catalog`, the legs and `staging-test`'s door (4.9, item 13), 4.11's Terraform
   with the orchestration module's next tag, each planned. **Done 2026-11-12**, ahead of sittings 2
   to 4 (§Release F as written), act 1's applies and the lint's pull request with it; its merge stays
   the user's.
6. **Promotion sittings, release F**: `awsds-deploy-prod`'s membership at its first call (item 12), 4.10's
   release through both targets, 4.11's applies, 4.12's subscription from Sandbox, 4.13 the morning
   after.
7. **A Sandbox warehouse sitting**: pass 5, before 2026-12-19 if the trial is to absorb it.
8. **The close**: 6.1's `catalog.py`, 6.2's documents, 6.3's threat-model entries, 6.4, 7.

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
  after `write_result`: it takes the domain and the project from `{domain.id}` and `{proj.id}`,
  substituted at the deploy, reads the worker's `DataZoneDomainId` and `DataZoneProjectId` for a value
  left empty, finds the source whose filter names the database (`list-data-sources`), starts its run
  (`start-data-source-run`), waits for `SUCCESS`, finds the asset whose external identifier names the
  table (`search` on the inventory) and publishes its latest revision (`create-listing-change-set
  --action PUBLISH`); every call as the project role, through the `datazone` endpoint; the task returns
  at once where the stage variable `PUBLISH_LISTING` is not `true` (decision 3, 2026-10-31). The tests
  gain a catalog double, and `make check` passes; decision 8's render rule is moot since decision 6 (b).
  **Written 2026-10-31** on this repository's branch of the template, the mirror to `awsds/app-etl`
  being the next GitLab sitting's: `glue/transform.py` takes `--TABLE_DATABASE` and `--TABLE_NAME`, both
  or neither, an empty value no value, and writes `glue_catalog.<database>.<table>` with
  `write.format("iceberg").mode("overwrite").saveAsTable`, read back and counted; the workflow's Glue
  task passes them from `{env.PRODUCT_DATABASE}` and `trades_notional`, and its `DefaultArguments` gain
  `--datalake-formats iceberg` and the `--conf` that declares `glue_catalog` as Iceberg's `GlueCatalog`
  over the account's catalog with `S3FileIO`, the warehouse under the project's `tables/` class;
  `code/app_etl_tasks.py` gains `publish` and its helpers (`find_source` by the source's filter,
  `run_source` to `SUCCESS` within 600 s, `find_asset` by the external identifier's last two segments,
  `publish_asset` waiting for `ACTIVE` within 120 s, since the API answers before the listing exists),
  the gate on `publish_listing`, the XCom the identifiers as JSON; the workflow's fifth task `publish`
  after `write_result`; the manifest's two literals in `dev` and `test`, `PRODUCT_DATABASE: app_etl`
  and `PUBLISH_LISTING: "true"`, the one case a stage variable is not read from the shell;
  `scripts/render-workflow.py` renders the two to `app_outputs` and `false` and drops the Glue task's
  two arguments, so a target writes no product table and lists nothing until 4.11 retires the render
  (the runbook's §W table carries the rows); the README and the runbook's §M and §W rows. The tests:
  60 passed, the product table's four cases and the publication's nine among them; the pinned lint
  `d856982c` `ok` on the nine files; `make check` and the pre-commit hooks pass. Read on the way: the
  pinned lint refuses `content.catalog.enabled` (3.1), and the CLI refuses every command while a
  `${VAR}` is unset (3.3).
  **Prepared 2026-11-08**, nothing up, on `claude/stage-19-pass-1`: `publish` takes the domain and the
  project from `{domain.id}` and `{proj.id}` in its `op_kwargs`, which the CLI's context resolver
  substitutes at the deploy (its `domain` carries `id`, `name` and `region`, its `proj` `id`, `name`,
  `domain_id` and `iam_role_arn`), and reads the worker's `DataZoneDomainId` and `DataZoneProjectId`
  only for a value the deploy left empty: the seven variables the portal injects reached a task of a
  portal-created workflow (6i, 2026-10-11; `serverless-workflows.md` §O), the CLI's `CreateWorkflow`
  passes none (its code names no `EnvironmentVariables`), whether the service injects them into a
  CLI-created workflow is unmeasured, and the deploy's substitution holds in every stage. The sentence
  this paragraph first carried, that no reading had measured the variables on a worker, was a grep
  that never ran (Lesson 62's third instance). The project role holds no `datazone:StartDataSourceRun`:
  `SageMakerStudioProjectRoleMachineLearningPolicy` v47 grants `datazone:Get*`, `List*`, `Search*`,
  `CreateAsset*` and `CreateListingChangeSet` on `*`, `SageMakerStudioProjectUserRolePolicy` v76 a list
  of reads on the domain, the role's four other policies no `datazone` action, none inline, and the D13
  boundary allows what the identity policies grant (`simulate-principal-policy` answers `explicitDeny` to
  every call, `glue:GetTable` included, the conditioned denies read without their context keys, Lesson
  30). `sandbox/workflows/`'s policy gains `StartADataSourceRunInTheProjectsDomain`, the one action on
  the domain's ARN, planned `1 to change` and applied 2026-11-08 21:50 UTC (the policy at `v4`, both
  project roles attached, the plan after it `No changes`); 4.4's `workflows.tf` carries the same statement
  for each target's project role. The render's table gains `{domain.id}` and `{proj.id}`, `none` for a target.
  The tests: 61 passed.
  **Decision 10's settings, written 2026-11-08 before the sitting**: the Glue task's `--conf` carries
  Stage 18 7.1's OpenLineage listener after the Iceberg catalog (`transport.type` `amazon_datazone_api`
  on `{domain.id}`, `spark.glue.accountId`, `JOB_NAME`), the account from the stage variable
  `ACCOUNT_ID`, which `dev` and `test` read from the shell: the space's STS in `dev`, the deploy role's
  in `test-deploy`. The render drops it with the job-creation keys, so a target is unchanged until 4.11.
  The tests pass after it (61, 1 skipped), and the pinned lint `d856982c` answers `ok` on the nine files.
- **The sitting of pass 1, in order**, written 2026-11-08 with nothing up, so that the estate is up only
  for the deploy and the two runs: the portal's acts come before, the readings after, and GitLab is left
  to its next sitting, since the space receives the template as a file. `sagemaker-application.md` §D is
  the procedure, this list its order and this pass's values; every `make` runs in the project folder,
  pulled to the commit that carries this list.

  **Before the window**, nothing up:
  1. **[user] In the portal**, as the data scientist in `eighth-experimentation`: *Data → Create
     database*, the name `app_etl` (decision 2), **done 2026-11-08 23:41 UTC**; then decision 4's form
     type `classification`, owned by the project, from *Manage → Catalog management → Metadata forms*,
     with no metadata rule: a rule requiring the form on publishing acts on run 1's publication, which
     comes before 1.3 fills it, and AWS's page says what it does in the portal alone. The domain granted
     no project `CREATE_FORM_TYPE` (read 2026-11-08), and the portal showed the project's owner the button
     disabled (2026-11-09), so `data-governance/governance/` grants it to `eighth-experimentation`'s owners
     first (the user's (B): written 2026-11-09, applied 2026-11-10 00:36 UTC, grant `00KsayGIrZ`); the
     form's one field is a `String`, since the portal holds no enumerated type. **Created 2026-11-10
     00:44 UTC** and read back: revision 2, `ENABLED`, `classification: String`, nothing required, not
     searchable. The project holds no
     space (both `Tooling` domains read 0 on 2026-11-08), so no page of it starts an app.
  2. **[Claude] reads** the new `DataLake` environment, its database, its source and whether it carries
     a subscription target, 1.2's first half: read 2026-11-08 23:44 UTC (the log), no target.
  3. **[Claude] The package** `~/tmp/stage19-pass1.tar`, built on the laptop from the branch's commit:
     `stage19-pass1/app-etl/`, the 25 files of `git archive HEAD:examples/app-etl`, and
     `stage19-pass1/pass1.sh`, which runs the space's half unattended. It checks that the caller is
     `eighth-experimentation`'s project role, the space on the house image (`AWSDS_PYTHON_ENV`),
     `airflow-serverless.us-west-2.api.aws` resolving to the `mwaa` group's endpoint and the database
     `app_etl` answering; exports `ACCOUNT_ID` from STS and the values read 2026-11-08 from the project's
     `Tooling` environment (the domain, both project names, `subnet-016b5a3a62c739894`,
     `subnet-09d3399d6b0fec93a`, `sg-0fee1c059b82e3562`, the key `a81b1ef3-716f-4105-bb42-14184a6e2174`,
     the `test` stage's values as placeholders), `JOB_IMAGE_URI` as `v0.4.6`'s image by the digest
     `production/app/app-etl/release.tf` records, `TRAINING_IMAGE_URI` a placeholder; builds both zips;
     deploys to `dev`, stopping on the CLI's *"No custom VPC config"*; starts run 1 through the CLI and
     follows it to its end, then run 2 the same way, since a run started outside the CLI carries none of
     the stage's parameters; with `NEGATIVE=1`, verification ii's negative last, the project role
     starting `test-experimentation`'s source `3zp6fog9jep1qo`. The image's registry host carries
     Production's account id, so the tar stays outside the repository and is deleted after the sitting.
     `sandbox/egress/`'s plan with `GROUPS=mwaa`, read 2026-11-08: 28 to add, 0 to change, 0 to destroy.

  **The window**:
  4. **[user]** `make hub-up`, then `make up ENV=sandbox ONLY=egress GROUPS=mwaa`, its plan 3's. No
     tunnel and no GitLab: nothing in the window reaches either. The window keeps clear of 23:41 UTC,
     the source's own daily run (read 2026-11-08), which a `publish` starting the same source may meet;
     what DataZone answers to a second run of a source mid-run is unmeasured.
  5. **[user] In the portal**, once the apply ends: a JupyterLab space on the house image (version 11),
     the tar dropped on its file browser, and in its terminal:

     ```bash
     tar -x -f stage19-pass1.tar && cd stage19-pass1 && NEGATIVE=1 nohup bash pass1.sh > pass1.log 2>&1 &
     tail -f ~/stage19-pass1/pass1.log
     ```

     Each deploy spends one of the workflow's 50 versions (the `dev` project's `app-etl` at 1 on
     2026-10-26). That day's run took 694 s, `process` 459 of them and `transform` 91; `publish` is new.
  6. **1.3 [user] while run 2 runs**: the asset exists once the log reports run 1's `SUCCESS`, and run 2
     reaches `publish` about nine minutes after its start, so metadata written before then reaches run
     2's listing, which is 1.4's question.
  7. **[user]** after the log's `DONE`: `pass1.log` downloaded, the space stopped, every portal tab
     closed, `make down ENV=sandbox`, `make hub-down`, `make status`.

  **After the window**, nothing up:
  8. **[Claude] The readings of 1.2 to 1.4** (verifications i to iii and v), as `awsds-infra-sandbox-1`
     and `awsds-infra-data` with `NO_PROXY='*'`, the domain `dzd-d8yrvx1ko7im6o` and the project
     `avhvbqn37ty7m8`: `get-workflow-run` and `list-task-instances` for both runs (§V); the job and its
     runs; `aws glue get-table --database-name app_etl --name trades_notional` and its versions
     (`TableType`, `Parameters.table_type`, `IsRegisteredWithLakeFormation`,
     `StorageDescriptor.Location`, the database's `LocationUri` or the `--conf` warehouse); Lake
     Formation's permissions on both; `aws cloudtrail lookup-events` in Sandbox and Data Governance for
     `CreateTable`, `UpdateTable`, `StartDataSourceRun`, `CreateListingChangeSet` and
     `PostLineageEvent`, each event's `userIdentity.sessionContext`, `sourceIPAddress` and
     `vpcEndpointId`, or the refusal's wording; `list-data-source-runs`, `get-data-source-run` and its
     activities (the statistics, the asset's id); `search --search-scope ASSET
     --owning-project-identifier avhvbqn37ty7m8 --search-text trades_notional`, `get-asset` (the forms,
     `DataSourceReferenceForm` among them), `list-asset-revisions` and `get-listing` (`status`,
     `approvalRequired`) as `awsds-infra-sandbox-1`, a `PROJECT_CONTRIBUTOR` since 2026-10-15, since
     DataZone refuses Data Governance's `InfrastructureAccess` the project's inventory (*"User is not
     permitted to perform operation"*, 2026-11-08); the lineage events since the window's start and
     `list-lineage-node-history` on the asset; `./aws/catalog.py` and the `dev` project's environments
     and sources against 2026-11-08's reading (five environments, four sources, 9 listings, 7 sources
     in the domain). The session's script for these calls ran whole on 2026-11-08 against the estate
     before the sitting, every call answering but the four on the absent database.
  9. **The mirror, at the next GitLab sitting**: §K steps 1 to 3 from the commit pass 1 ran, on the
     laptop with the tunnel up and GitLab answering (1 min 42 s after its start): `git clone
     https://gitlab.awsds.internal/awsds/app-etl.git <new folder>`, `git switch -c stage-19-product`,
     `git rm -q -r .`, `git archive --format=tar -o <file> HEAD:examples/app-etl` (25 files), `tar -x -f
     <file> -C <folder>`, `git add -A`, a commit named `Stage 19 1.1: the product as an Iceberg table and
     its listing`, `git push -u origin stage-19-product`; the laptop's git holds the credential in the
     keychain and trusts the root (§C step 3). **[user]** opens the MR, whose pipeline runs `test`,
     `secret_detection` and `pip-audit` on the test runner, and merges it once green; `test-deploy` runs
     on a tag alone, and the tag (§T) waits for the next release's sitting, `promotion.md` §N.8.2. The
     local user's password is rotated in the same GitLab sitting.
- **1.2 [user] Create the product's database in `dev`** (*Data → Create database*, the name of decision
  2), **deploy to `dev` from a space** and run `app-etl`. **[Claude] reads** the new `DataLake`
  environment, its database, its daily source and whether it carries a subscription target (the one of
  2026-10-28 carries none); then the job's
  `glue:CreateTable` in Sandbox's trail, its session and the grant that admitted it, the table's format
  (`TableType`, `table_type` Iceberg, `IsRegisteredWithLakeFormation`) and location (verification i);
  the worker's `StartDataSourceRun` and `CreateListingChangeSet`, their `sourceIPAddress` the endpoint's
  and the policy that admitted each, or the refusal's wording (ii); the run's statistics and the asset's
  forms, the listing `ACTIVE` with `approvalRequired`, the `DataSourceReferenceForm` (iii); the
  lineage nodes and events the job's OpenLineage settings post (v).
  **Run 2026-11-10** (the log): the deploy from `eighth-experimentation`'s space, then four runs of 816 to
  936 s. `J3chim3kbCEXWZl` failed in `publish` on the asset's external identifier (`SUP-343`, fixed in
  `a858e376`), `wf5GVes1RglmGsM` on the change set's revision (`SUP-345`, `db22976c`) and
  `hiErIl5sGJSyRFx` on a republication's `UPDATING` (`ee6b8525`); `MmFs38SsxUFQ2xM` ran `SUCCESS`. The
  package was rebuilt after each fix. The first build's ten AppleDouble files stay in the project's
  `shared/app-etl/` (`SUP-348`), and Spark skipped the one under `inbox/`, since each run read the sample's
  10 rows. Verifications i to iii are answered, and v's domain half.
- **1.3 [user] The asset's business metadata in the portal**: a description, decision 4's form, a
  README. **[Claude] reads** what the forms hold and `CT-2` to `CT-6` on the new objects.
  **Written 2026-11-10** by the user from 03:04 to 03:06 UTC, before run `hiErIl5sGJSyRFx`: the
  description, the README and `classification` `internal`, asset revisions 3 to 5. The source's later
  updates, revisions 6 and 7 by `SYSTEM`, kept all three, and listing revision 4 onwards carries them
  (verification iv's first half). `catalog.py` passed every check with the product in it.
- **1.4 [user] Run `app-etl` a second time.** **[Claude] reads** whether the second run re-creates or
  overwrites the table, what the source's run reports (`updated`, `unchanged`) and whether the listing
  gains a revision: the product's idempotence.
  **Read 2026-11-10** over the three runs after the first: each run overwrote the table (`UpdateTable`
  on it, its creation time unchanged, version 3 at the end), the source reported `updated: 1`, and each
  republication added two listing revisions, the change set's and the publication past it (`SUP-345`'s
  three readings). The product is idempotent in its table and its listing.
- **1.5 [user] Pass 1 again in the project for app-etl alone** (decision 18 (d)), after pass 2 and
  verification v's look, since Sandbox's one catalog holds `app_etl` once (decision 19).
  `eighth-experimentation`'s product is retired first in the rollback's order: the data product, the
  listing and the asset by the owner, the table by the project role, then the database. The data
  scientist creates the project from `experimentation` in the portal, its name the user's; in it go 2.2's
  `DataLake` environment, 1.2's database and source, and `awsds-deploy-sandbox-test` as a member (3.1).
  Its project role joins `sandbox/workflows/`'s `project_roles`, and `form_type_owners` if decision 18's
  first reading leaves the form type to it, each applied on the user's word; `DEV_PROJECT_NAME` changes
  in the space and in the pipeline. Then 1.2's run, 1.3's metadata and 2.1's data product happen there.
  **[Claude] reads** i to v on its objects and `CT-13` over its source.
  **Amended 2026-11-11 by decision 20 (b)**: the manifest's `dev` stage carries `PUBLISH_LISTING`
  false, so the source runs from the portal after the run, the data product is created and left
  unpublished, and the readings are i, iv and v.
  **Amended 2026-11-11 (the estate reviewed)**: the project's creation, the bundle role's membership of
  it and its role in `sandbox/workflows/`'s `project_roles` come first, with release T (items 16 to 18
  of §The estate against decisions 17 to 20), since the pipeline's `bundle` job names the project; the
  database, the run and the metadata follow pass 2 as written. The template carries `PUBLISH_LISTING`
  false in `dev` since the same day.

### 2. The data product and the subscription

- **The sitting of pass 2, in order**, written 2026-11-10 with nothing up. Most of the pass is portal
  acts and readings, which need no window; only 2.4's Spark half, xi's negative and decision 17's reads
  need a space.

  **With nothing up**:
  1. **[user] The consumer and the approver** (decision 5). As the data scientist, the consumer project
     from `experimentation` in the portal, its name the user's: the profile creates `Tooling` alone on
     creation (a SageMaker AI domain, and the daily `Tooling` source, `EXC-11`'s third), `DataLake` being
     `ON_DEMAND` at order 1 (read 2026-11-10). Then, as `eighth-experimentation`'s owner, the Governance
     Manager added as `PROJECT_CONTRIBUTOR`: on 2026-11-10 the members are the owner, the project role's
     profile and Sandbox's `InfrastructureAccess` group (6f 4.3 answered in the act).
  2. **[Claude⚡ on the user's word] 2.2's environment**, 6f 11.7's `create-environment` from the
     profile's `DataLake` configuration, as `awsds-infra-sandbox-1` once the owner seats Sandbox's
     `InfrastructureAccess` group in the consumer, a seat whose keeping is already the user's decision;
     then its target's `databaseName` and its source.
  3. **[user] 2.1, 2.3 and 2.4's first half**: the data product `trades-notional` in
     `eighth-experimentation`, published; the subscription from the consumer; the approval as the
     Governance Manager; the query editor's read on *Athena (SQL)* with no space. **[Claude]** reads vi,
     vii and viii's first half after the acts.

  **The window**, the hub and `make up ENV=sandbox ONLY=egress`, no `GROUPS` since nothing deploys:
  4. **[user]** A JupyterLab space in the consumer on the house image; its Spark session on
     `project.spark.fineGrained` reads the table (viii) and stays open. In the space's terminal, as the
     consumer's role, decision 17's reads of `eighth-experimentation`'s source and run, then xi's
     negative; nothing printed is a value of the data:

     ```bash
     D=dzd-d8yrvx1ko7im6o; SRC=budryu9mt9y5u8; RUN=6bnfg5dk961bps
     B=awsds-sandbox-smus-projects; T=dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/trades_notional
     aws sts get-caller-identity --query Arn --output text
     aws datazone get-data-source --domain-identifier $D --identifier $SRC --query '{name: name, project: projectId}'
     aws datazone get-data-source-run --domain-identifier $D --identifier $RUN --query '{status: status, stats: runStatisticsForAssets}'
     aws datazone list-data-source-run-activities --domain-identifier $D --identifier $RUN --query 'items[].{table: technicalName, asset: dataAssetId}'
     aws s3api list-objects-v2 --bucket $B --prefix $T/ --max-items 1 --query 'Contents[].Key'
     aws s3api head-object --bucket $B --key $T/metadata/00003-a0aed729-d7b0-4a27-b035-7bda5426406f.metadata.json --query ContentLength
     ```

  5. **[user] 2.5**: the revoke in `eighth-experimentation`, then the open session's read again (ix).
  6. **[user]** The space stopped, every portal tab closed, `make down ENV=sandbox`, `make hub-down`,
     `make status`.

  **After the window**: **[Claude]** ix's pieces read gone, and 2.6 the morning after (x).
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

### 3. The bundle and the manifest's stages

- **3.1 [Claude] The manifest gains `content.catalog`** (`enabled` true, `connectionName`
  `project.default_lakehouse`, `skipPublish` false; 0.9): `bundle` then exports every catalog resource
  `dev` owns, the product's asset and data product among them, and `deploy --targets test` creates them
  in `test` and publishes the ones published in `dev`. The order the CLI runs is read in its code first
  (pass 0): the bootstrap's `workflow.run` must have created the table in `test`'s database of the same
  name before the listing, or the listing fails asynchronously and the deploy counts a publish failure.
  The lint's rule that refuses content from outside the tag is read against a `catalog` item that names
  no file ([`sagemaker-application.md`](../runbooks/sagemaker-application.md) §M).
  **Read 2026-10-31 at 1.1**: decision 14 makes `skipPublish` true, the task the publisher; the pinned
  lint `d856982c` refuses `content.catalog.enabled` by its rule `manifest` (*"o bundle levaria o que o
  projeto tem, e não a tag"*), so the item enters the manifest only with a lint release that admits a
  catalog item as the project's live catalog carried beside the tag, pinned in `.gitlab-ci.yml` by
  `AWSDS_WORKFLOWS`; and `test-deploy`'s `bundle` would then export the catalog as
  `awsds-deploy-sandbox-test`, whose DataZone reads for the export are written first
  (`sandbox/foundation/`'s deploy role). Which project `bundle --targets test` exports, `dev`'s or
  `test`'s, is the code reading that opens the step.
  **Read 2026-11-10 in the CLI 1.0.9's installed code** (`commands/bundle.py`,
  `helpers/catalog_export.py`): `bundle --targets <stage>` exports the catalog of that stage's project,
  every resource it owns, with no filter. The calls are `Search` by `owningProjectIdentifier` over assets,
  data products, glossaries and terms, `GetAsset` and `GetDataProduct` for each, and `SearchTypes` with
  `managed` false for the form and asset types the project owns: the reads the deploy role would need.
  The template's `test-deploy` runs `bundle --targets test` before its deploy, so it exports
  `test-experimentation`'s catalog, which owns nothing (read 2026-11-10). An export of `dev` would carry
  everything `eighth-experimentation` owns: `house-price`, the resource link `trades` (0.5),
  `trades_notional`, `my-data-product` and the form type `classification`. Neither carries the product
  with 1.3's metadata, which decisions 4 and 14 assumed: decision 18.
  **Amended 2026-11-11 by decision 18 (d)**: `test-deploy` bundles `dev`, the project for app-etl
  alone, as `awsds-deploy-sandbox-test`, which that project seats as a member for the export's reads. A
  pipeline guard fails a bundle whose `catalog/catalog_export.json` holds more than the declared product:
  its asset, its data product, the form type if the project owns it, and the terms it names. The rule
  `manifest` admits `content.catalog` in an `awsds-workflows` release pinned by `AWSDS_WORKFLOWS`.
  **Amended 2026-11-11 by decision 19 (c)**: the bundle job takes `test-deploy`'s place, bundling `dev`
  as `awsds-deploy-sandbox-test` with no deploy in Sandbox.
  **Written 2026-11-11 for release T**: the job `bundle` in the template's `.gitlab-ci.yml`, with
  `content.catalog` off, so it carries the tag's files alone and needs no export read; it fails on
  the CLI's *"Failed to get project connections"*, since `bundle` exits 0 for a project its caller is
  no member of (`SUP-352`, measured on the laptop). `sandbox/workflows/`'s role holds the project's
  reads and the export's four (`Search`, `SearchTypes`, `GetAsset`, `GetDataProduct`) and nothing else,
  planned 0 to add, 3 to change, 2 to destroy and applied in release T's sitting. The catalog, its
  guard and the lint's release are release F's: a failed export also leaves the bundle whole and the
  exit status 0, so the guard reads the archive for `catalog/catalog_export.json` before its content.
  **Written 2026-11-12 for release F**: `content.catalog` enabled with `skipPublish` true; the job
  `bundle` runs `scripts/check-catalog-export.py` over the archive against `product.json`, which
  declares the asset `trades_notional` as required, once, and the form type `classification` as
  allowed, the type's owner being unread (item 22). A data product or a glossary term the scientist
  adds at 1.5 joins the file in the same merge request. The lint's rule is item 23's patch.
- **3.2 [user] Create the product's database in `test`** (the same name), then **tag the application**;
  the pipeline's `test-deploy` bundles and deploys to `test` (Stage 8 2.5). **[Claude] reads** the
  bundle's `catalog/catalog_export.json`, the import's calls in the trail as `awsds-deploy-sandbox-test`
  (`CreateAsset`, `CreateDataProduct`, `CreateListingChangeSet`, any `AddPolicyGrant` the import adds to
  the root domain unit for `CREATE_GLOSSARY`, `CREATE_FORM_TYPE` and `CREATE_ASSET_TYPE`, which `CT-9`'s
  neighbours would read), and what `test` holds after: the table from the run, the asset with its
  `DataSourceReferenceForm` remapped or stripped, the product, the listing `ACTIVE` or failed (xii), and
  whether the project's own source, run after the import, updates the imported asset or creates a second
  one over the same table (xvii), the reading decision 14 rests on.
  **Amended 2026-11-11 by decision 19 (c)**: no database in `test` and no deploy there. The tag's
  pipeline runs the bundle job, and **[Claude] reads** the bundle's `catalog/catalog_export.json` against
  the guard (3.1); the import's calls, the domain unit's grants and what the target holds, xii and xvii,
  are read in Staging at 4.10 and 4.13.
  **Amended 2026-11-11 (the estate reviewed)**: release T's tag runs the bundle job with no catalog,
  and its first run is Staging's leg on today's Terraform path; the export is read at release F's
  tag. The import's policy grants are not left to the import: the CLI adds a missing
  `CREATE_GLOSSARY`, `CREATE_FORM_TYPE` or `CREATE_ASSET_TYPE` grant as the identity that deploys and
  aborts when it cannot (`SUP-351`), the root unit held none of the first and the third that day, and
  `governance/`'s `catalog_import_projects` declares the three per deployment project (4.5).
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
  **Read 2026-10-31 at 1.1**: the CLI 1.0.9 refuses every command while any `${VAR}` of the manifest is
  unset, the other stages' included (§M's `find_missing_env_vars`; Stage 18 4.1 set `STAGING_*` as CI/CD
  variables for the same reason), so the two stages are written at 4.9, once 4.6 and 4.8 give them
  their projects' values, and never before: until then `test-deploy` would stop at the first
  `${STAGING_*}`. `app-etl-warehouse`'s entry in `content.workflows`, its `create_job_kwargs` and
  `load_warehouse.py`'s read of the Iceberg product (decision 16 (b)) are written with them.
  **Amended 2026-11-11 by decision 18 (d)**: the `staging` stage's `catalog.disable` is decision 19's.
  The `prod` stage's bootstrap runs after the import, so the task's start of Production's source after
  it returns Production's table to the asset before the listing (decisions 17 (a) and 19).
  **Amended 2026-11-11 by decision 19 (c)**: the manifest's stages are `dev`, `staging` and `prod`; the
  `test` stage and its variables leave it, and the `staging` stage carries no `catalog.disable`.
  **Written 2026-11-11 for release T**: the `test` stage and its four variables left the manifest,
  which holds `dev` alone until 4.9 writes `staging` and `prod`. The pinned lint passes it, and the
  CLI 1.0.9's `bundle --targets dev` ran on it on the laptop.
  **Written 2026-11-12 for release F**: the stages `staging` and `prod` name `deploy-staging` and
  `deploy-production` and read `STAGING_*` and `PROD_*`, which no CI/CD variable holds: the leg
  fills them from each project's Tooling environment, whose `provisionedResources` name
  `privateSubnets`, `securityGroup`, `kmsKeyArn` and `nonGitProjectRepositoryLocation` (read
  2026-11-12 in both projects, `SUP-359`), and takes the training image from the account's
  `sagemaker/` state. The `prod` stage's bootstrap creates the three workflows and runs `app-etl`
  with `trailLogs`. `app-etl-warehouse`'s task creates its job as `app-etl`'s does, the
  warehouse's names its literal arguments, and `load_warehouse.py` reads the product table on
  `glue_catalog`. The CLI's `describe` parses the three stages.

### 4. The promoted product: a deployment project in each target, the CLI deploying every stage

Decision 6 (b), taken 2026-10-31. [Stage 18](stage-18-staging-deployment-project.md) built this shape
in Staging from 2026-10-17 to 10-22 and unwound it; this pass builds it in both targets as a standing
state, in Stage 18's order, each step citing the Stage 18 step whose measurement it repeats. Decisions
13 to 16 were taken on 2026-10-31. The sittings are promotion sittings ([`runbooks/promotion.md`](../runbooks/promotion.md)
§N), coordinated with the session holding Stages 8-10, whose objects 4.9 and 4.11 change. Production is
touched for the first time at 4.2: every reading Stage 18 made in Staging is made again there, since
the shape is the templates' and the account's own state is not.

**Read 2026-11-10 against pass 1.** Decision 17 (a), taken 2026-11-11, keeps 4.4's `StartDataSourceRun` statement in each
target. Decision 18 decides whether 3.3's stages carry `content.catalog` and 4.13's `catalog.disable` at
all. 4.10's readings take pass 1's shapes: the table under the product database's `LocationUri` (i), each
publication the listing revision past the change set's (`SUP-345`), and the lineage nodes found by id
from Data Governance's trail or by `amazon.datazone.asset/<id>` (`SUP-347`, xxi). A deploy never deletes
what a release drops (`SUP-348`), and the workflow scan reads the target project's whole shared root
(`SUP-287`). A file a release drops therefore stays a candidate in Production until a hand deletes it, so
4.10 reads the shared root after each deploy.

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
  **Written, measured and planned 2026-11-11** (the log): the two statements, `POLICIES.md`'s rows, the
  battery's rows (both `ListDomains` rows `allow`, a `CreateSubscriptionRequest` row per account and a
  `CreateSpace` row for Staging) and the wildcard check's entry. The battery before read 49 as
  expected, 0 unexpected, 5 not measured. The deny half was read as the canary under a candidate
  holding the two statements, `p-oktjrbxv`, parked on `Policy Test` from 04:31:41 to 04:33:14 UTC and
  deleted: three DataZone calls refused naming it, the floor answering, `ListDomains` answering again
  68 s after the detach (`SUP-350`). The candidate is made from the rendered document, never kept as a
  file: `jq '{Version, Statement: [.Statement[] | select(.Sid | startswith("DenyDataZone"))]}'` over
  `aws/output/rendered-policies/awsds-org-scp-ou-workloads.json`. The plan reads 1 to change, the
  document 2,499 to 2,840 bytes, saved as `$HOME/tmp/stage19-scp-41.tfplan`; the apply was refused to
  Claude by the classifier and is the user's.
  **Applied 2026-11-11, 14:23:31 to 14:23:46 UTC, by [Claude⚡] on the user's word** (*"Autorizo os 3
  applies"*): 0 added, 1 changed, 0 destroyed. The re-plan reads `No changes`, `./aws/org-policies.py`
  passes, `datazone list-domains` answers the shared domain from both targets (xviii), and the
  battery's phase `ou` at 14:27:22 UTC read 52 as expected, 0 unexpected, 5 not measured: both
  `ListDomains` rows `ALLOWED`, both `CreateSubscriptionRequest` rows `DENY-SCP` naming `p-83t232f4`.
- **4.2 [user] Associate `Staging Account` and `Production`** in the console, Stage 18 2.1's path: the
  Infrastructure User, account **Data Governance**, permission set **`InfrastructureAccess`**, Amazon
  DataZone → `awsds-studio` → Account associations. **[Claude] reads** 2.2's: from each account
  `list-environment-blueprint-configurations` answers an empty list where it answered
  `UnauthorizedException`; RAM's share holds four principals; `./aws/studio.py` reads the two accounts
  associated (`US-2`, its Workloads rule inverted). D26 carries the dated amendment; the note on 6f
  decision 4 is the 6f session's to write, that stage being its.
  **Done 2026-11-11 at 04:37:18 UTC by [Claude⚡]**, by the call the console makes: Data Governance's
  trail of 2026-10-19 shows the console's act as `ram:AssociateResourceShare` on the domain's share,
  followed by RAM's `datazone:PutDomainSharingPolicy` in the caller's session, and nothing else
  (`SUP-349`). Both accounts read `ASSOCIATED` at 04:37:19, the share holds three principals, Sandbox
  among them, no invitation exists, and each target reads the share `ACTIVE`. The DataZone read-back
  from the targets follows 4.1's apply; `./aws/studio.py` reads the refusal as that step pending and
  passes.
  **Read 2026-11-11 at 14:27 UTC, after 4.1's apply**: from each target `list-domains` answers the
  domain and `list-environment-blueprint-configurations` an empty list; `./aws/studio.py`'s `US-2`
  passes on both (14:40 UTC).
- **4.3 [Claude] The lists**: `SMUS_ASSOCIATED` gains `staging` and `production`, then
  `SMUS_DEPLOYMENT_MEMBERS` gains both (Stage 18 2.3's order; the guard refuses an account in both lists
  and `profiles_enabled` flips while a deployment row precedes its associated row); the four readers
  that mean "accounts people work in" stay on `SMUS_MEMBERS`; `sandbox/foundation/`,
  `production/tooling/` and `staging/foundation/` re-plan `No changes` after each regeneration.
  **Written 2026-11-11**: both lists carry both targets. Over every declared slice, laptop and
  pipeline, the generated tfvars differ from `main`'s in `governance/`'s `members` alone;
  `governance/`, `staging/foundation/` and `production/foundation/` plan `No changes`.
- **4.4 [Claude] `staging/studio/` and `production/studio/`**, Stage 18 2.4's slice as a `[P]` slice of
  each target: `terraform-modules/sagemaker-prereqs/` at its pinned tag (`v0.9.0` since 2026-10-30) with
  `blueprint_names` `["Tooling", "DataLake"]`, the D13 boundary, the Glue manage-access policy the
  module carries since `v0.8.0` (7.2's first environment failed without it), `workflows.tf` granting the
  project roles what `sandbox/workflows/` grants: the job actions (4.4's first run was refused
  `glue:GetJob` without them) and `datazone:StartDataSourceRun` on the domain (1.1, 2026-11-08),
  `person-session.tf` under decision 15, `cost_center` `stage-19`; in Staging, `InfrastructureAccess`
  seated as a third Lake Formation administrator and the deploy role granted `DESCRIBE` and `SELECT` on
  the product database's tables, `staging-test`'s door (decision 14 (d)); the `studio` rank and
  `[P]` row in `layers.py`, `backend.py`'s `studio` emission, conventions §6 and `NETWORK.md` §2.1. Each
  target's `egress/` gains the `datazone` interface endpoint 7.1 needed (a `datazone` group or
  `extra_services`, `PRICING.md` §3's endpoint count). **[Claude⚡] applied twice per account as
  `awsds-infra-<env>`**: the prerequisites (Stage 18 read 14 to add), then, after 4.3's associated row,
  the two configurations and their grants; the boundary read back with `get-role`.
  **Written and planned 2026-11-11**: the two slices are copies of each other but for
  `project-roles.tf` (`check-copies.py`), read their VPC through the generated `vpc_slice`
  (`foundation` in Staging, `workloads` in Production) and carry `cost_center` `stage-19`. Staging
  needs no third administrator seat: `staging/data/` seats `InfrastructureAccess` since 2026-10-22, and
  the module ignores what a service adds to the list. The deploy role's grant on the product
  database's tables is written with the leg that reads it (item 13). The prerequisites plan 16 to
  add in each account with `-var blueprints_enabled=false`; Staging's apply was refused to Claude by
  the classifier, so both are the user's. Both `egress/` slices name `datazone`.
  **The prerequisites applied 2026-11-11 by [Claude⚡] on the user's word**: Staging 14:23:58 to
  14:25:18 UTC, Production 14:25:29 to 14:26:49 UTC, 16 added in each and read back: the two roles
  and their managed policies, the boundary and the person-session policy attached to nothing, the
  key, the bucket, the log group; Lake Formation unchanged. **The configurations planned** at 14:30
  UTC with no `-var`: 5 to add, 2 to change, 0 to destroy in each. To add: `Tooling` and `DataLake`,
  their two grants and `awsds-<env>-workflows`. To change: the key policy, which gains the two
  project-role statements, and the person-session policy, its document known after apply and
  unchanged. Production's configurations point at VPC-Workloads. Saved as
  `stage19-studio-staging-2.tfplan` and `stage19-studio-production-2.tfplan`; the classifier refused
  Staging's to Claude, the user's sentence having named three applies.
  **The configurations applied 2026-11-11 by [Claude⚡] on the user's word** (*"Autorizo os 5
  passos"*): Staging 15:18:06 to 15:18:41 UTC, Production 15:18:55 to 15:19:28 UTC, 5 added and 1
  changed in each, both re-plans `No changes`. Each target lists `Tooling` and `DataLake` with its
  provisioning role, manage-access role, boundary, VPC and two private subnets.
  **The project roles' grants applied 2026-11-11**, 16:15 to 16:16 UTC, 2 added in each slice:
  `awsds-<env>-workflows` and `awsds-<env>-person-session-deny` on `deploy-staging`'s and
  `deploy-production`'s role.
- **4.5 [Claude] The profile `deployment`** in `governance/`, Stage 18 2.6's form with two environment
  configurations: `Tooling` `ON_CREATE` with `enableSpaces` `"false"` locked and `DataLake` `ON_DEMAND`
  in each target, the `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to each target's InfrastructureAccess
  session group by its group id (2.7's correction), never to a persona group; `./aws/studio.py`'s `US-4`
  admits `deployment` as a standing profile. **[Claude⚡] applied as `awsds-infra-data`**, a plan that
  touches `experimentation` or 6d decision 16's objects stops the step; 6d's 2.7 and this apply never
  share one (Stage 18 2.7's rule).
  **Written 2026-11-11 as two profiles**, `deployment-staging` and `deployment-production`: an
  environment configuration names one account, so one profile serves one target. They sit behind
  `deployment_profiles_enabled`, false until each target's configurations exist and its
  `InfrastructureAccess` has read a project of the domain once, which creates the group profile the
  grant names (`SUP-159`); with it false `governance/` plans `No changes`. `./aws/studio.py` admits the two names and
  judges each target's configurations against `Tooling` and `DataLake`. The same slice gains
  `catalog_import_projects`, the three policy grants the CLI's catalog import checks (`SUP-351`), one
  set per deployment project, written once 4.6 gives the project ids.
  **Rehearsed 2026-11-11** with the switch on in the working tree alone, as `awsds-infra-data`: 4 to
  add, 0 to change, 0 to destroy, the two profiles (`Tooling` `ON_CREATE` at order 0, `DataLake`
  `ON_DEMAND` at order 1) and their grants, nothing on `experimentation` or `lake-publishing`.
  Production's `InfrastructureAccess` held no group profile after `ListDomains`,
  `ListEnvironmentBlueprintConfigurations`, `ListProjects` and `GetDomain`, and holds one since its
  first `GetProject` (`ca2735c9-…`).
  **Applied 2026-11-11 by [Claude⚡] on the user's word**, the switch on: planned 4 to add at 15:20
  UTC; the apply created `deployment-staging` (`cpkm68sz0l185s`), `deployment-production`
  (`3o9zp0asbh2gi8`) and Production's grant and failed on Staging's with `ResourceConflict`, *"failed
  conditions: VERSION EQ"*, the two grants of one type on one unit created at once (`SUP-353`); a
  second apply created it at 15:23 UTC. The re-plan reads `No changes`, and `US-4` admits the five
  profiles.
- **4.6 [Claude⚡] The projects**: `deploy-staging` and `deploy-production` by `create-project` as each
  target's `awsds-infra-<env>` (3.1), their provisioning read (3.2: the stack `CREATE_COMPLETE`, no
  SageMaker AI domain, every refusal the roles' own IAM), what the blueprint created (3.3: the thirteen
  resources, the two SMUS roles seated as Lake Formation admins, `AllowFullTableExternalDataAccess` set
  `true`, the Access Grants instance and the Athena service-linked role). Then the product's database in
  each project: `create-environment` from `DataLake` with the name decision 2 (d) fixed, the API form of
  the portal's *Create database* (6f 11.7's call), and its reads: the database, its conditioned grants,
  its daily source (`publishOnImport` false) and its subscription target (xix).
  **The before, read 2026-11-11** in both targets: no `awsds-<env>-smus-projects` bucket, no project
  key alias, no `smus` or `datazone_usr_role_*` role, no boundary; Lake Formation with one
  administrator, `InfrastructureAccess`, `AllowFullTableExternalDataAccess` unset,
  `CROSS_ACCOUNT_VERSION` 4, both create-default lists empty. Stage 18 read Staging with no
  administrator; whether provisioning adds its two roles beside one that exists, or replaces the
  list, is read here.
  **Done 2026-11-11 by [Claude⚡] on the user's word** (the log): `deploy-staging` (`5ido8bej1zoeq8`)
  at 15:25:59 UTC, `SUCCESSFUL` at 15:27:41, and `deploy-production` (`d7qcazihvr3s7k`) at 15:29:29,
  `SUCCESSFUL` at 15:31:18; the databases by `create-environment` with the profile's `DataLake`
  configuration and `--user-parameters name=glueDbName,value=app_etl`, `deploy-staging-app-etl`
  (`54jhe9989w0tcg`) and `deploy-production-app-etl` (`azkybvkz7iea34`), each `ACTIVE` in about 40 s.
  Read after it, the same in both accounts: the thirteen resources with `enableSpaces` `false` and
  no SageMaker AI domain; the project role and the two Bedrock roles under the D13 boundary
  (`US-8`, which reads the targets since this sitting); no refusal from the SCP or the boundary.
  **Provisioning adds its two roles beside the administrator that exists**: three seats, the
  parameters and the empty create-default lists kept, the flag `true`, and `<env>/data/` plans `No
  changes` (`SUP-170`). The database carries the conditioned grants, a daily source with
  `publishOnImport` false and, xix, a subscription target over `app_etl`. Each project's members
  are the account's `InfrastructureAccess` group, `PROJECT_OWNER`, and the project role's own user
  profile, `PROJECT_CONTRIBUTOR`.
- **4.7 [user] Production's flag**: `AllowFullTableExternalDataAccess`, turned off in Production on
  2026-10-25 (`TM-26`), is `true` again after 4.6; the user turns it off in the console as then, and 4.10
  and 4.12 read whether the project's engines or a fulfilment need it (xx). Staging's flag follows the
  same reading. The lake's flag is 6f's and untouched.
  **Read 2026-11-11 after 4.6**: `true` in Production since 15:29:36 UTC and in Staging since
  15:26:05, the provisioning role's `PutDataLakeSettings`. `TM-26`'s Production half is open until
  the user's act (`SUP-112`: the flag turned off reads as an absent key).
  **Done 2026-11-12 by [user]**, from the CLI and not the console, one call per account:
  `put-data-lake-settings` with the settings `get-data-lake-settings` returned and the flag `false`,
  Production at 01:50:08 UTC and Staging at 01:50:16 (the trails). Read after it: the key absent in
  both, the three administrators, the parameters and the empty create-default lists kept; `DT-13`
  passing and `./aws/deploytargets.py` at 0 checks failed; no `GetDataAccess` in either trail while
  the flag stood, 10 h 24 min in Staging and 10 h 20 min in Production. `EXC-23` is closed and
  `TM-26`'s halves in the targets with it. A project created later in a target may set the flag
  again (`SUP-106`), which `DT-13` reads; xx stays 4.10's and 4.12's.
- **4.8 [Claude] The deploy roles**: `awsds-deploy-staging` and `awsds-deploy-prod` gain Stage 18 4.3's
  three inline documents in `<env>/foundation/deploy-role.tf` (the DataZone reads the CLI makes before
  `workflow.create`, the workflow calls on workflows tagged with the project, `iam:PassRole` of the
  project role to the service, the project's `shared/` prefix and the project key), **[Claude⚡]
  applied as `awsds-infra-<env>`**. Then the membership, 4.3's two steps: the role's first CLI call as a
  non-member stops at `ListConnections` and creates its `IAM_ROLE_SESSION_GROUP` profile, which
  **[user]** adds as `PROJECT_OWNER` by group id (`create-project-membership` as `awsds-infra-<env>`;
  the classifier refused Claude the grant in Stage 18). The portal's Workflows tool is unavailable in a
  deployment project (6.1), so a run is followed by the job's `get-workflow-run` loop and the console.
  **Written 2026-11-11** as `<env>/foundation/deploy-project.tf`, one file in both targets
  (`check-copies.py`): one managed policy on the deploy role, created once `deployment_project_role`
  names the project's role, since every scope is built from that name. It carries Stage 18 4.3's
  statements and the catalog import's reads and writes; `AddPolicyGrant` is not among them
  (`SUP-351`). Rendered with a placeholder name it holds 13 statements in 3,828 characters of 6,144;
  with the variable empty both slices plan `No changes`.
  **Planned 2026-11-11 with each project's role named**: 2 to add in each `foundation/`, the policy
  and its attachment, saved; `governance/`'s `catalog_import_projects` names both projects as
  `OWNER`, 6 to add. The applies are the next round.
  **Applied 2026-11-11 by [Claude⚡] on the user's word**: both `foundation/` slices at 16:16 to 16:17
  UTC, 2 added each, and `governance/` at 16:17 to 16:18 UTC with `-parallelism=1`, 6 added. The policy
  reads 13 statements at `v1` on each deploy role. Simulated as each role with the Region in the
  context (`SUP-008`): the project's reads, the catalog import's writes and the workflow calls
  `allowed` under the boundary and the organization, `AddPolicyGrant` `implicitDeny`, a subscription
  request the organization's `explicitDeny`, `PutObject` allowed under `shared/` and not under `dev/`.
  The membership stays the user's: the app's classifier refused Claude the call the same day.
  **Staging's membership made 2026-11-12 by [user]**, `create-project-membership` as
  `awsds-infra-staging` at 01:50:26 UTC: `deploy-staging` lists `awsds-deploy-staging`'s group
  (`9bead345-…`, read as that role's from the domain's account) as `PROJECT_OWNER` beside
  `InfrastructureAccess`'s. The role has made no call as a member; `awsds-deploy-prod`'s group does
  not exist until its first call, release F's, and its membership follows it.
- **4.9 [Claude] The legs**: `staging-deploy` and `production-deploy` run `smus-cli deploy --targets
  staging` and `prod` from the stored bundle, extracted beside the release's manifest (Stage 18 4.2: the
  CLI 1.0.9 reads every local item from the manifest's folder), as `awsds-deploy-<env>` on the deploy
  runner, Stage 18's job `stage-18-deploy` the recipe; `release-application.py`'s render, the promoted
  lint mode and the orchestration slices' `release.auto.tfvars.json` workflows retire whole, the
  warehouse workflow deployed by the CLI into Production's project too (decision 16 (b)). `staging-test` reads the
  run's output under the project's `shared/` prefix and the table through decision 14's door. The
  template's merge request lands in `awsds/app-etl` at the next tag's sitting (`runbooks/promotion.md`
  §N.8.2), so the Stages 8-10 session's leg changes and decision 1's branch are one release.
  **Amended 2026-11-11 (the estate reviewed)**: two releases. Release T, written that day, retires the
  `test` stage on today's legs and carries decision 1's branch; it is the next tag's. The CLI's legs
  are release F, written once 4.6 and 4.8 are applied: `deploy` reads the storage items from the
  manifest's folder and the catalog from the archive, so a leg extracts the stored bundle beside the
  tag's manifest and passes the archive as `--bundle-archive-path` (`commands/deploy.py`, read
  2026-11-11; `SUP-286`). The import returns failure only when every item it attempted failed, so the
  leg reads the summary's `Failed:` count (`SUP-357`).
  **Written 2026-11-12** ([PR #291](https://github.com/felipenoris/AWS-DataScience/pull/291); §Release F as written): `staging-deploy` and `production-deploy`
  run `scripts/deploy-application.py` of the infrastructure repository; `staging-check` and
  `production-check`, which takes `production-plan`'s place, read the project and the deploy role's
  membership of it, so a non-member fails before the gate; `staging-test` starts both chains, then
  reads the run's report under the shared prefix and the product table's metadata (decision 24);
  the model chain's jobs pass `--project`. A leg applies no Terraform.
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
  **The fence of decision 21 (b) is read against this step** (applied 2026-11-11): each target's
  boundary denies the project role every bucket of the account but the projects bucket, every
  customer managed key but the project key and every `sts:AssumeRole`, so a bucket or a role this
  step gives the role leaves the fence in the same change (`fence.tf`'s `fenced_bucket_names`, the
  module's `assumable_role_arns`), and a second key is a module tag. The fence's Redshift half is
  written here: the role's session denied on every workgroup but the one the warehouse workflow
  takes (`TM-30`).
  **Written 2026-11-12, in part** (§Release F as written; items 26 to 29). The chain layer is
  `orchestration-v0.3.0`, called by new `[P]` slices, `<env>/chains/`, since `<env>/orchestration/`
  is what release T's legs still apply: a machine lists the workflows and finds its own by name,
  the ARN carrying a suffix the service generates, and passes the run the stage's variables
  (decision 23); the chain role starts and reads the application's workflows by ARN pattern and
  uses the project key for them, and carries no application ceiling, which caps what the pipeline
  creates. The load as the project role: `GetCredentials` and `GetWorkgroup` on the account's
  workgroups in `awsds-prod-warehouse-load`, a named grant since a workgroup's ARN is an id the
  `[E]` compute renews; 5439 from the project's security group, whose own egress admits every
  destination (read 2026-11-12). The fence's Redshift half is by service: `redshift-data` and
  `sqlworkbench` denied in both targets, `redshift` and `redshift-serverless` too in Staging, which
  holds no warehouse; Production's workgroup is one, so the door the load takes,
  `redshift-serverless`, stays, and the session's reach is what the warehouse grants its
  `IAMR:` user. Decision 15's deny grows to a warehouse session. **Not written**: the lake's read
  for the project role and the deny's growth to the lake's catalog and `lakeformation:GetDataAccess`
  (decision 22 (a), a later release's): the application writes nothing in `curated`, so the role takes no write there
  under any option; the retirement (item 31); the warehouse's SQL; Stage 10's file.
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
  **Amended 2026-11-11 by decision 19 (c)**: Staging imports, so its project holds the asset the import
  created before the table, and its daily source, the morning after, revises it or creates a second
  (xvii); xxv reads the same morning what `CT-4` and `CT-5` say of it.

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
  registration. `CT-13`, written 2026-11-11 under decision 17 (a), judges each `StartDataSourceRun` in
  Sandbox's and Data Governance's trails against the source's project (`TM-29`); a start from another
  account reads unresolved until that account's trail is read, which this step adds for both targets.
  Decision 20 (b) adds a note, never a failure, on a listing a chain application's `dev` project owns,
  the projects named in the script by id from 1.5.
  **Written 2026-11-11**: `studio.py`'s deployment-target rules (`US-2` reads a target's refusal as
  4.1 pending and an empty answer after it as a failure, `US-3` judges its configurations against
  `Tooling` and `DataLake`, `US-4` admits the two deployment profiles, `US-6` passes on no SageMaker
  AI domain); run that day, all checks passed.
  **Written 2026-11-11, after 4.6**: `studio.py` reads each deployment project, its environments
  and their subscription targets (`US-11`), each role's trust policy in every account that holds a
  project role (`US-12`), and the domain account's project roles beside the others (`US-8`);
  `deploytargets.py` judges the full-table flag in both targets (`DT-13`, red from 4.6 until 4.7,
  passing since 2026-11-12, `EXC-23` closed) and what a project's role does not reach there (`DT-14`,
  passing since decision 21's applies);
  `catalog.py` reads both targets' trails for `CT-13` and judges a deployment project's sources
  (`CT-14`). The product road's own checks stay for the close.
- **6.2 [Claude] The documents**: `SMUS.md` (the product's readings, the targets, the roster of 0.8; §A
  deployment project in a `Workloads` account rewritten as the two projects that exist), `GOVERNANCE.md`
  (§Grants, §The development cycle, §Assigning the LF-Tags, §Publishing and sharing under decision 6 (b),
  the warehouse paragraph, the `test-experimentation` sentence), `AWS_STATE.md` (the product's register
  row or its rule, `EXC-17`'s trigger, the association invariant of 4.1), `architecture.md`, `NETWORK.md`
  (the `studio` slices and the `datazone` endpoints), `runbooks/sagemaker-application.md` §B, §K, §M, §N,
  §P, §T, §W and §Z (the CLI's legs, the project per target, the publishing task in every stage, no `test`
  stage), `runbooks/promotion.md` (the legs' new shape, a release with no Sandbox `egress/`),
  `redshift-connection.md` for 5.1 and 5.2, D17, D19, D20, D22, D26, D28, D35, D41 and 5a decision 5
  amended in place with dated lines (Stage 9 decision 15 by its session), `POLICIES.md`'s row (4.1),
  `integrations.md`'s INT-12 and INT-26, `history.md`; `GOVERNANCE.md:737` is the 6f follow-up's.
- **6.3 [Claude] The threat model**: an entry for the product road, the subscriber's full-table vend
  (xi), the re-listing channel (0.5), a materialized view that outlives a revoke (question 3), with the
  checks of 6.1 as its triggers; under decision 6 (b), an entry for the deployment projects, Stage 18's
  measured price as its residual: the project role every member acts as in Production, bounded by
  decision 15's deny; AWS's managed policies on it (`TM-17`, `TM-28` gain weight: the policies moved to
  v76/v47 on 2026-10-29 with no act of this estate); the two SMUS roles as Production's Lake Formation
  admins; the RAM share of Production's catalog at each fulfilment; `TM-26`'s Production half reopened
  at 4.6 and closed again at 4.7 if 4.10 and 4.12 read nothing needing the flag. `TM-29`, the start of
  another project's source, was written at pass 1 (2026-11-10) and follows decision 17.
  **The deployment projects' entry written 2026-11-11 as `TM-30`**, from a reading of the role's
  policies and a simulation as Production's role against the hub's assets (the log): what is closed,
  what holds by one layer, what the role holds by IAM. Decision 21 is its question, taken as (b)
  and applied the same day: the entry's status reads what the fence closed and what it left.
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
| i | Does the Glue job's session create an Iceberg table in the project database under the conditioned `CREATE_TABLE`, registered with Lake Formation, and where? **Measured 2026-11-10: yes.** `GlueJobRunnerSession` created `app_etl.trades_notional` through Sandbox's `glue` endpoint, `table_type` `ICEBERG`, registered, under the database's location `…/avhvbqn37ty7m8/dev/data/catalogs/` rather than the `--conf` warehouse; the conditioned `IAMPrincipals` `CREATE_TABLE` is the database's one grant the role meets | 1.2 |
| ii | Does the worker's session of the project role start the source's run and publish the listing, through the `datazone` endpoint, and which policy admits each call (`StartDataSourceRun` is `awsds-sandbox-workflows` `v4`'s statement, on the domain's ARN)? And is the role refused `start-data-source-run` on another project's source, DataZone's own authorization the only control left, read from the space on the user's word, since a success starts `test-experimentation`'s import? **Measured 2026-11-10: the first half yes, the second no.** Both calls came from the worker's session through `vpce-09e2724f4cf1ea60c`, the run admitted by `v4`'s statement and the change set by the managed policy's `CreateListingChangeSet` on `*`; the negative was admitted and its run `SUCCESS` imported nothing (`SUP-346`, decision 17) | 1.2 |
| iii | What does a run filtered to one table import, and does `publishOnImport` false leave it unpublished until the task publishes? **Measured 2026-11-10: yes.** The run over `app_etl` with `*` imported the database's one table (`added: 1`) and the later runs `updated: 1`; the asset stayed unlisted 32 minutes, until the task's first change set | 1.2 |
| iv | Does the published asset carry a classification anywhere, and does the form of decision 4 travel to the listing and the data product? **The first half measured 2026-11-10 (1.3)**: no LF-Tag; the form `classification` (`internal`) travels to the listing with the description and the README, and survives the source's updates. The data product is 2.1's | 1.3, 2.1 |
| v | Does the job post lineage to the domain from Sandbox, and does the portal draw it on the asset's page now that the table is an asset (Stage 18 7.1 drew nothing)? **The domain half measured 2026-11-10: yes.** 92 events were posted through the endpoint, all `SUCCESS`, and the domain chains the `inbox` prefix, the job run, the table's node, the asset's and the listing's. The portal's drawing is the user's look | 1.2 |
| vi | In one account, which principal writes the fulfilment, in what form (a grant to `IAMPrincipals` under the consumer's context, or to its role), and does a resource link appear in the consumer's database? 6f verification i's same-account half | 2.3 |
| vii | Does one approval of a data product fulfil every item? 6f iv | 2.3 |
| viii | Does the consumer read through the query editor with no space and from a space's Spark session? | 2.4 |
| ix | Does revocation remove every piece, and does a session opened before it still read? 6f iii | 2.5 |
| x | Does the consumer's daily source import the resource link, and does anything notice? | 2.6 |
| xi | Can the consumer's role vend the table's objects directly, under Sandbox's `AllowFullTableExternalDataAccess` (`TM-26`, Stage 17 7.4c)? | 2.4 |
| xii | What does the bundle carry of the catalog, in what order does `deploy` import against the run, which policy grants does the import add to the domain unit, and what does Staging hold after? | 3.2, 4.10 |
| xiii | From the warehouse, which identity reads `awsdatacatalog`, does it carry the project's context, and which Lake Formation grant admits it? | 5.2 |
| xiv | What does an Iceberg materialized view register in the Glue Data Catalog, and what does its refresh cost? | 5.2 |
| xv | Does a Redshift asset published from the connection find a subscription target in any project? | 5.3 |
| xvi | What did the sittings bill, by service? | 6.4 |
| xvii | After the CLI's catalog import, does the project's own source update the imported asset or create a second one over the same table? | 4.13 |
| xviii | With `DenyDataZoneEntirely` revised, does `datazone list-domains` answer from both targets, does the root's `CreateDomain` deny still bind them, and does the battery's phase `ou` read the document as decision 13 wrote it? **Measured 2026-11-11: the first and the third, yes.** `list-domains` answers the shared domain from both targets as `InfrastructureAccess`, and the battery's phase `ou` read 52 as expected, 0 unexpected, 5 not measured, its four DataZone rows as written. The root's `CreateDomain` deny was not exercised from a target: the statement is unchanged and attached (`org-policies.py`), its last exercise the canary's of 2026-08-21, and since the amendment it is the one policy between the three excepted principals and a local domain (Lesson 20) | 4.1 |
| xix | Does a `DataLake` environment created by API with a chosen database name carry a subscription target, in a project with no person? **Measured 2026-11-11: yes.** `create-environment` with `glueDbName` `app_etl` gave each deployment project `deploy-<env>-app-etl-default-target`, for `GlueTableAssetType` and `GlueViewAssetType`, its `databaseName` `app_etl` and its principal `abac:CURRENT_PROJECT`; the portal's *Create database* environment for the same name in `eighth-experimentation` carries none (`SUP-184`) | 4.6 |
| xx | With `AllowFullTableExternalDataAccess` off in Production, do the project's engines write and read the product, and does a fulfilment to Sandbox complete? Stage 9 decision 13's reading on a project's table | 4.7, 4.10, 4.12 |
| xxi | Does Production's Glue job post its lineage through the target's `datazone` endpoint as the project role, and does the portal draw it now that the table is an asset? | 4.10 |
| xxii | What does `make down ENV=staging` leave of a deployment project, and does `staging-check` read it as `[P]`? | 4.10 |
| xxiii | Does the chain's machine start the CLI-made workflow by its composed name and wait on `GetWorkflowRun`, with KMS on the project key alone? Stage 18 0.4 as a standing state. Since decision 23 it also passes the stage's variables: xxix | 4.11 |
| xxiv | Which identity does Production's trail record for the consumer's read, and which grant admits it? INT-23's cross-account reading on a product | 4.12 |
| xxv | With the import and no listing in Staging, what does Staging's daily source make of the imported asset, and does `CT-4` or `CT-5` notice an unpublished asset in a project with no person? | 4.13 |
| xxvi | Does a domain-defined designation (API-only since 2026-10-29) narrow what the Governance Manager may do in `deploy-production`'s portal, beside decision 15's deny on the person's session? | 4.12 |
| xxvii | Does decision 15's deny, grown to the lake's catalog, Lake Formation's data access and the warehouse's credential calls, refuse a person's session those writes while the warehouse workflow's worker session still loads `governed` from `curated`? As written on 2026-11-12 the deny covers a warehouse session alone and the load reads the product table: the lake's half follows the governed read's release (decision 22 (a)) | 4.11, 4.12 |
| xxviii | Does `workflow.run` with `trailLogs` in the `prod` stage's bootstrap follow the run to its end, and does the deploy fail with it? The CLI 1.0.9's `wait` crashes (`sagemaker-application.md` §M), and `trailLogs` is read in its code alone | 4.10 |
| xxix | Does a chain's machine find the CLI-made workflow by name with `ListWorkflows`, read the stage's variables from SSM and start the run with them as `OverrideParameters`, the run rendering every `{{ params.VAR }}`? The definitions answer `OK` to `ValidateStateMachineDefinition` (2026-11-12), which reads no run | 4.10 (`staging-test`), 4.11 |
| xxx | Does `scripts/deploy-application.py` read the deploy's log as the CLI 1.0.9 prints it in a target: the *"Tooling VPC config"* line, the import's `Failed:` count at zero in a first import, each workflow found by name? | 4.10 |
| xxxi | Does the batch transform run as the project's role under the fence, the model and its batch input under the project's shared prefix and key, the deploy role passing that role to SageMaker? | 4.10 (`staging-model`) |
| xxxii | Does the load's Glue job, created by the task in `deploy-production`, open its session as `IAMR:<project role>` through `GetCredentials` under the fence, the Data API and the query editor refused to the same role? The policies read so by simulation on 2026-11-12, which opens no session | the warehouse sitting |

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
   **Amended 2026-11-11 by decision 19 (c)**: `app_etl` is one name per account's catalog, in the `dev`
   project, Staging's and Production's; Sandbox's catalog holds it once, so no second Sandbox project
   takes it (1.5's order), and 3.2's database in `test` retires.
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
   **Amended 2026-11-11 by decision 19 (c)**: no `test` stage, so `PUBLISH_LISTING` is `true` in `dev`
   and `prod` and `false` in `staging`; whether `dev` lists is decision 20's.
   **Amended 2026-11-11 by decision 20 (b)**: `PUBLISH_LISTING` is `true` in `prod` alone; in `dev` the
   task neither starts the source nor lists.
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
   **The field and the grant, 2026-11-09** (the user's (B)): the portal offers no enumerated field type,
   so the field is a `String` whose value `CT-12`'s successor reads against the four; the producing
   project creates the form type under a `CREATE_FORM_TYPE` grant to its owners on the root domain unit,
   `data-governance/governance/`'s `form_type_owners`, which the domain did not hold; applied 2026-11-10
   00:36 UTC, the form created by the project's owner at 00:44 UTC (revision 2).
   **The owner, read 2026-11-10 on AWS's pages**: required, and the project whose members edit or delete
   the form; the portal lists every form in the domain, and no page ties attaching one to its owner. No
   call moves a form type to another owner, and `DeleteFormType` refuses one an asset uses, so the owner
   question 3.2 reads is cheapest to change before 1.3 attaches the form to `trades_notional`.
   **Amended 2026-11-11 by decision 18 (d)**: the form is filled in the project for app-etl alone
   (1.5) and carried by its export. Decision 18's first reading settles the owner. If a project attaches
   a form type another project owns, one owner serves every stage, `eighth-experimentation`'s form type
   or a governance project's, and the import neither exports nor recreates it. If not, the project for
   app-etl owns it, `form_type_owners` names that project, and the import's creation in each target
   meets a name the domain already holds.
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
    **Taken 2026-11-09 by the user** (*"Keep it on"*): on in `dev` and `test`, in the template since
    2026-11-08 (1.1), so pass 1's runs answer v; the targets' half stands as amended, Staging and
    Production unchanged until 4.11 retires the render that drops the settings.
    **Amended 2026-11-11 by decision 19 (c)**: on in `dev`, the `test` stage retired.
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
    **Amended 2026-11-11 by decision 18 (d)**: the bundle is `dev`'s, the project for app-etl alone,
    with `skipPublish` true as taken and the task the one publisher; whether `staging` keeps
    `catalog.disable` and `test` its import is decision 19's. The CLI imports before the bootstrap
    (`commands/deploy.py`), so Production's release imports, then its `workflow.run` creates the table
    and the task starts Production's source and lists.
    **Amended 2026-11-11 by decision 19 (c)**: the `staging` stage imports with `skipPublish`, its
    `catalog.disable` dropped and `PUBLISH_LISTING` false keeping it unlisted; Staging's import is the
    first, read at 4.10 and 4.13 (xii, xvii).
    **Amended 2026-11-11 by decision 20 (b)**: the task lists in Production alone.
    **Amended 2026-11-12 by decision 24 (a)**: `staging-test` reads the table's metadata with
    `glue:GetTable` and no row of it; the deploy role holds `DESCRIBE` on the product database
    and its tables and no `SELECT`, and the run's own read-back counts the rows.
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
17. **The start of another project's data source** (`SUP-346`, verification ii, `TM-29`). On 2026-11-10
    DataZone admitted `eighth-experimentation`'s project role starting `test-experimentation`'s source,
    though the role's profile is a member of its own project alone; the run imported nothing new. IAM
    cannot narrow the call. The Service Reference (read 2026-11-10) gives `StartDataSourceRun` no resource
    type and no condition key and maps `datazone:projectId` to no action, and DataZone authorizes the call
    against the domain. `awsds-sandbox-workflows` `v4` therefore lets each Sandbox project role start any
    source in the domain. 4.4's statement would give each target's role the same reach, so Sandbox's roles
    could start Production's sources and Production's role Sandbox's. A start runs the source's own import
    under the source's configuration and answers a run id. What a start colliding with the owner's run
    does is unmeasured. A source that publishes on import would publish what it imports, and `CT-4` keeps
    all nine off that (2026-11-10). Whether a non-member reads a run's activities is `TM-29`'s other half:
    the managed policy's `datazone:Get*` and `List*` grant those reads whatever this decision takes.
    (a) Keep the grant and accept the residual in `TM-29`, with compensations:
    - `CT-4` stays a gate on every source in the domain;
    - a new `catalog.py` check fails on any `StartDataSourceRun` in either trail whose caller's project,
      the id in the project role's name, is not the source's;
    - pass 2's sitting reads, from the consumer's space, what a non-member gets from `get-data-source-run`,
      `list-data-source-run-activities` and `get-data-source`.

    (b) Remove the grant: `publish` lists the revision the source's daily run last imported. This undoes
    decision 3 (a)'s order: a schema change reaches the listing a day late, and the first listing waits for
    the schedule. (c) Publish without the source: the task writes the asset's revisions itself
    (`CreateAssetRevision` with the Glue forms, the managed policy's `CreateAsset*`), under DataZone's
    membership check for that call, unmeasured. The task would rebuild what the import computes, off the
    native path. (d) Report the behaviour to AWS, the user's act, beside any of the three.
    **Recommended: (a) with (d)**. A start gives the caller a run id and does what the source's schedule
    does anyway. The compensations cover publication, the one effect with weight, and make every
    cross-project start visible. (b) and (c) give up the native path and leave the read half where it is.
    The recommendation moves to (b) if a start collides with the owner's run and fails it, or if any
    source in the domain comes to publish on import.
    **Taken 2026-11-11 by the user as (a) with (d)** (*"Ok em relação à recomendação na Decisão 17."*):
    the grant stays in `sandbox/workflows/`, and 4.4 writes it in each target. `CT-4` stays a gate.
    `./aws/catalog.py` `CT-13`, written the same day, judges every start in Sandbox's and Data
    Governance's trails. Its first run read six starts in CloudTrail's 90 days: four by the source's
    own project role, one by an Identity Center session on 2026-10-22 on a source no longer listed,
    and verification ii's, a note by its request id. Pass 2's sitting reads the non-member's half, and
    (d) is the user's report, its text in the stage log of 2026-11-11.
    **Read against SMUS's own path, 2026-11-11** (decision 18 (d)): the source's import, the listing's
    change set and DataZone's authorization are SMUS's own. The start from the task is the house's, on a
    grant AWS's managed policies leave out (`sandbox/workflows/main.tf`), and no bootstrap action of the
    CLI 1.0.9 starts a source (`bootstrap/handlers/`). AWS's own triggers are the source's schedule and a
    member's run in the portal, which (b) keeps: what (b) gives up is decision 3 (a)'s order, not the
    import. Under decision 18 (d) the start carries more. The import writes `dev`'s technical forms on a
    target's asset (decision 19), and the stage's own source, run by the task after it, returns the
    stage's table to the asset before the listing; under (b) the asset would carry Sandbox's table until
    the next scheduled run.
18. **How the product's business metadata reaches the targets** (3.1, 3.3, decisions 4 and 14). The CLI
    1.0.9 exports the catalog of the project of the stage it bundles, whole (3.1, read 2026-11-10). The
    pipeline's `bundle --targets test` exports `test-experimentation`'s, which owns nothing, and an export
    of `dev` carries every experiment `eighth-experimentation` owns. Decision 14 (a) assumed the bundle
    carries `dev`'s product with 1.3's metadata, and decision 4 that its form travels so; neither holds.
    **SMUS's own path**, read 2026-11-11 in AWS's catalog import and export guide, the manifest's
    page, the user guide's CI/CD page and the CLI's import code: the business catalog is authored in
    the source project, the `dev` stage, and `content.catalog` carries it to an independent project
    per stage. `bundle` exports every glossary, term, custom form type, asset type, asset and data
    product the source project owns, with no filter; resources shared into the project and AWS's
    managed types stay out, and no page asks for a project dedicated to one application. `deploy`
    imports them into the stage's project in that order. An asset whose `externalIdentifier`, without
    account and Region, matches one there gets a revision, else it is created; a custom form type the
    target project does not own is created there; nothing in the target is deleted; what was `ACTIVE`
    in the source is published unless `skipPublish`. The guide lists a name another project owns as a
    partial failure, and the code fails the deploy only when every import fails. The guide assumes the
    same Glue names in every stage and presents the export as the catalog versioned with the code. No
    page addresses stages that share one domain, as every stage here does (D22), where a form type's
    name is the domain's.
    (a) Decision 14 as taken: the bundle from `test`, whose own source creates the asset at 3.2's run,
    and the metadata typed again in `test` before each tag, a person in every release. (b) The bundle
    from `dev`, SMUS's path on `eighth-experimentation` as it is: the deploy role a member of
    `eighth-experimentation`, and `house-price`, the resource link
    `trades` and `my-data-product` promoted with the product. (c) Metadata as code: `content.catalog`
    stays off, and the template carries the product's description, README and classification in a file.
    `publish` writes them on the asset before the change set, in every stage that publishes:
    `CreateAssetRevision` with `AssetCommonDetailsForm` and decision 4's form, under the managed policy's
    `CreateAsset*`. Each stage's own source creates the asset, so xvii's second asset cannot arise, and the
    lint's refusal of `content.catalog` stays right.
    (d) SMUS's path with a `dev` project for the application alone: a Sandbox project holding app-etl's
    development and nothing else becomes the manifest's `dev` stage, with the product's database, its
    source and the data product. The scientist curates the description, README and classification in
    its portal, and the import carries them, the data product and any glossary term to every stage.
    The deploy role becomes a member to read its catalog, `content.catalog` is enabled with decision
    14's `skipPublish`, the pipeline bundles `dev`, and a pipeline guard fails a bundle whose
    `catalog_export.json` holds more than the declared product, since 1.0.9 has no filter. The lint's
    refusal of `content.catalog` is lifted in `awsds-workflows`. Pass 1 runs again in that project, and
    `eighth-experimentation` keeps its experiments.
    **Recommended: (d)**, under decision 6 (b)'s criterion: it is SMUS's own path, and it carries the
    data product and glossary terms besides the asset's metadata, which (c) would write in house code.
    The classification's control is `CT-12`'s successor on every product listing in each stage, so
    (c)'s review in a merge request would be a second control, not the load-bearing one. (c) stays the
    alternative if the dedicated project or the deploy role's membership is refused. Both rest on two
    readings first. One is whether a project attaches a form type another project owns in this domain
    (decision 4's owner question, which AWS's pages leave open); if it does, the form type is owned
    once outside the source project, and the import neither exports nor recreates it. The other is
    whether a source run keeps a revision written through the API as it kept the portal's (1.3,
    2026-11-10). xvii's other order, the import first and the stage's source after, is read at 3.2.
    (d) amends decisions 4 and 14, both the user's, and 3.1 and 3.3 with them.
    **Taken 2026-11-11 by the user as (d)** (*"A decisão 18 pela recomendação nativa (d) está ok."*):
    a Sandbox project for app-etl alone becomes the manifest's `dev` stage through `DEV_PROJECT_NAME`,
    and `eighth-experimentation` keeps its experiments; pass 1 runs again in that project at 1.5, after
    pass 2. Decisions 4 and 14 carry their amendments, 3.1 and 3.3 theirs. The two readings above come
    before 1.5's metadata, and decision 19 holds two more of the same day: the import's forms and its
    order against the bootstrap, and Sandbox's one Glue catalog.
19. **Where the catalog import is first read, and the product database in `test`** (3.2, 4.13,
    decisions 2, 14 and 18). Sandbox holds one Glue catalog for its projects, read 2026-11-11:
    `get-databases` lists `app_etl`, `glue_db_blerpkhn9nj7o0`, `mydatabase` and `new_database` under
    `eighth-experimentation`'s path, and `glue_db_4zojr4rr6bmnww` and `test_project_database` under
    `test-experimentation`'s, and a database is addressed by its name in its catalog. Decision 2 (d)'s
    `app_etl` therefore cannot be created in `test` while `dev` holds it, nor in decision 18's project
    while `eighth-experimentation` holds it (1.5). The CLI 1.0.9's `deploy` imports the catalog before
    the bootstrap (`commands/deploy.py`, read the same day). The import writes each asset's forms as
    `GetAsset` answered them in `dev`, except the `DataSourceReferenceForm`, remapped to the target
    project's source over the same database name or stripped, and each form type's revision
    (`helpers/catalog_import.py`). `GlueTableForm`'s `catalogId` and `tableArn` and
    `AssetCommonDetailsForm`'s `sourceIdentifier` carry `dev`'s account (pass 1's asset, 2026-11-10),
    and an asset the import creates keeps `dev`'s `externalIdentifier`. A target's first deploy thus
    creates the asset before the bootstrap's run creates the table, and the stage's source, started by
    the task, either revises it or creates a second asset over the table (xvii). A later deploy revises
    the stage's asset with `dev`'s forms, and the source run after it returns the stage's table to the
    asset before the listing (decision 17). The import's readings, xii and xvii, are representative only
    where the name matches `dev`'s in another account, and decision 14 gives Staging `catalog.disable`,
    so Production's first release would be the first.
    (a) Staging imports: the `staging` stage drops `catalog.disable`, its `skipPublish` and
    `PUBLISH_LISTING` false keeping it unlisted, and xii and xvii are read there, its daily source the
    run after the import (4.13's morning-after reading); `test` takes `catalog.disable` and a database
    name of its own, `PRODUCT_DATABASE` becoming a stage variable. (b) `test` as in (a), Staging
    unchanged: Production's first release is the import's first reading, under 4.10's rollback. (c) The
    `test` stage leaves the manifest and `test-deploy` the pipeline, Staging's leg becoming the first
    deploy, Stage 8 2.5's gate rewritten by the Stages 8-10 session.
    **Recommended: (a)**: it reads AWS's premise, the same names in another account, before Production,
    at the price of an unlisted asset that Staging's daily source imports anyway (xxv), and `test` keeps
    rehearsing the workflow and the task. If xvii shows a second asset, a target's first release goes
    without the import, so its own source creates the asset the next release's import revises. (a)
    amends decisions 2 and 14, both the user's.
    **Taken 2026-11-11 by the user as (c)**, with (a)'s Staging half (*"considerando a necessidade de
    haver isolamento entre ambientes, entendo que o ideal seria promover sempre entre contas diferentes.
    Ou seja, não haveria estágio test. A esteira de promoção seria sandbox -> staging -> production"*,
    then *"Sim, registre"*). The manifest's stages are `dev`, `staging` and `prod`, one account each, and
    every promotion crosses an account. The `test` project was D41 item 3's answer to targets with no
    project; decision 6 (b) gave each target one, and Staging's leg does what `test-deploy` did: a deploy
    role installs the tag's bundle into a project with no person, runs it, and `staging-test` reads it.
    What changes:
    - `test-deploy` leaves the pipeline: a bundle job makes the bundle from `dev` as
      `awsds-deploy-sandbox-test`, narrowed to the export's reads as a member of the `dev` project, and
      `store-bundle` keeps what Staging's leg runs first (Stage 8 decision 20);
    - the `staging` stage drops `catalog.disable` and imports with `skipPublish`, `PUBLISH_LISTING` false
      keeping Staging unlisted, so xii and xvii are read at Staging's leg and the morning after (4.10,
      4.13);
    - decision 2 (d) holds as one name per account's catalog, and decisions 3 and 10 lose their `test`
      rows;
    - a release no longer raises Sandbox's `egress/` (`runbooks/promotion.md`'s sitting);
    - `test-experimentation` stays a Sandbox project, holding 6d's blueprint pilot, 6f's `DataLake`
      environment and 6h decision 8's second project; only its stage ends.

    D41 item 3 carries its amendment; Stage 8's 2.5 and 3.3, the pipeline and the runbooks change with
    pass 4's legs (What concerns the other sessions).
20. **Which stage lists the product** (decisions 3, 18 and 19). The domain is one business catalog for
    every account (D22): a Sandbox data scientist searches Production's listings and reads one through a
    subscription, which grants `SELECT` and the link's `DESCRIBE` alone. Glue shows no second catalog: a
    table of another account enters Sandbox's catalog as a resource link with a local name, as `curated`
    and `raw` do (both links to the lake's databases, read 2026-11-11) and as a subscription's link does
    in the consumer's database (0.5's `trades`), so Production's `app_etl` never meets `dev`'s. The
    listings are where names repeat. Under decision 18 (d) Production's asset takes `dev`'s name,
    description, README and classification from the import, and decision 3 lists the product in `dev` and
    `prod`, so a search finds two `trades_notional` and two data products, told apart by the owning
    project alone; a form cannot mark the stage, since the import copies `dev`'s forms. How DataZone names
    a second link of the same table name in one consumer database is unmeasured.
    (a) Decision 3 as taken: `dev` and Production list. (b) Production alone lists: `dev` keeps the
    product in its inventory, its asset current for the scientist's metadata and the export, with
    `PUBLISH_LISTING` false and its source run on its schedule or from the portal.
    **Recommended: (b)**: a listing offers a product to every project in the domain, and `dev`'s is a
    working copy, so Sandbox's consumers subscribe to Production's. The listing code then runs by
    pipeline in Production first; pass 1 ran it in `dev`, and a change to it is exercised there by one
    deploy with `PUBLISH_LISTING` true, the listing then unpublished. (b) amends decision 3, the user's.
    **Taken 2026-11-11 by the user as (b)** (*"(b) Só Production"*), for the applications in the
    promotion chain (*"entendo que isso se refere aos aplicativos que fazem parte da esteira de promoção
    entre ambientes"*): the template's `dev` stage carries `PUBLISH_LISTING` false, written at 1.5 with
    `DEV_PROJECT_NAME`, and Production alone lists; a Sandbox project outside the chain publishes as SMUS
    lets it. The gate is the template's default, not a control. A member of the `dev` project still lists
    from the portal, since a member of any designation acts as the project role (`SMUS.md`, Stage 18
    6.1), and that role holds `CreateListingChangeSet` on every resource from AWS's policy (v47), so code
    in a space lists too. `CT-12`'s successor judges such a listing's classification as any other, and
    6.1's checks note it without failing. `sandbox/workflows/`'s `StartDataSourceRun` (decision 17) serves
    the listing code's exercise in `dev` alone. A deny of `CreateListingChangeSet` on the `dev` project's
    role would prevent such a listing and is not written: one call publishes and unpublishes, with no
    condition key to tell them apart (the Service Reference, read 2026-11-10), and the exercise takes
    both. Pass 2 lists in `eighth-experimentation` before 1.5 writes the default, and 1.5 retires that
    product.
21. **Whether this estate fences a deployment project's role off from the rest of its account, and
    where** (4.6, `TM-30`). The role runs the application's tasks in Production, the hub account, on
    three AWS managed policies under a boundary that names nothing of the hub. Read 2026-11-11 by
    simulation as the role: the hub's secrets, hosts, buckets, chains, model registry and IAM are
    closed to it. Three things hold by one layer each. `sts:AssumeRole` is allowed on every role, so a
    role's trust policy is the gate; no role in an account that holds a project role trusts that
    account's root (`US-12`).
    `kms:Decrypt` is allowed on every key through S3, and six of the hub's seven keys delegate to the
    account's IAM, so S3's implicit deny alone keeps GitLab's backups and the Terraform state from the
    role. The `glue` writes are allowed on the whole catalog, so Lake Formation alone keeps `curated`,
    `raw` and `app_outputs`. And the role holds, by IAM, Bedrock on every foundation model, AgentCore's
    managed browser and code interpreter, the assistants, a session on any Redshift Serverless
    workgroup through `sqlworkbench` and a pull of every repository of the registry. AWS moved both
    large policies on 2026-10-29 with no act of this estate.
    (a) Accept the reading: the layers that exist and the instruments' checks (`US-12`, `DT-14`) are
    the control, and nothing is written. (b) A deny in the targets' D13 boundary, which binds whatever
    AWS's next version grants: `terraform-modules/sagemaker-prereqs/` gains a list of the account's
    own resources its project roles never touch, and `production/studio/` names the hub's, the
    buckets but the projects bucket, the keys but the project key, the estate's secrets, every
    `sts:AssumeRole`, the deploy image's repository; with it the services a target has no use for,
    `bedrock:*`, `bedrock-agentcore:*`, `q:*` and `codewhisperer:*`. One module tag and one apply per
    target; a boundary's new version binds a live role at once. (c) The same denies as a statement of
    the `Workloads` SCP conditioned on `datazone_usr_role_*`, measured on a candidate first: it
    reaches a role a blueprint leaves with no boundary, AWS's template doing so for its two
    conditional EMR roles, and spends the document's size, 2,840 of 5,120 bytes today.
    **Recommended: (b)**, before 4.9: release F's first run is the first time application code runs
    as the role in Production. What (b) must not deny is what decision 16 (b) gives the role, the
    warehouse workflow's session on Production's workgroup, so the Redshift half is written with
    4.11. The decision is the user's.
    **Taken 2026-11-11 by the user as (b)** (*"(b) deny no boundary"*). Written the same day:
    `terraform-modules/sagemaker-prereqs/` at `v0.10.0` gains seven inputs, each off by default, and
    the boundary a deny per input that names something; both `studio/` slices pin the tag and set
    the same fence, every customer managed key of the account but the project key, the secrets named
    `awsds-*` and `redshift!*`, every `sts:AssumeRole`, and `bedrock`, `bedrock-agentcore`, `q` and
    `codewhisperer`, with the account's own lists in `fence.tf`: six buckets and the deploy image's
    repository in Production, three buckets in Staging. Planned: 0 to add and 2 to change in each,
    the boundary from 9 statements to 15 in Production (3,766 characters of 6,144) and to 14 in
    Staging (3,402), and the person-session policy, whose document is known after apply and does not
    change (`SUP-356`). Simulated as Production's role under the planned document: the assumption of
    the deploy role, the keys of GitLab and of the state through S3, both buckets through Access
    Grants, the estate's secrets, the deploy image, Bedrock, AgentCore's browser and the assistants
    read `explicitDeny`, the boundary's; the project's own prefix, the project key and an AWS
    managed key through S3, the application's image, the pass of itself to Glue, the domain's calls,
    the tables of `app_etl`, a Glue job's log group and the warehouse's credentials read `allowed`.
    `DT-14` reads the boundary's statements and every bucket of the account against them, and
    fails in both targets until the applies. No role is left assumable and Redshift is not fenced:
    4.11 writes both for the warehouse workflow.
    **Applied 2026-11-11, 18:25 UTC**, on the user's word (*"Autorizo os 2 applies"*): 1 changed in
    each slice, the boundary at `v2`, 15 statements in Production and 14 in Staging, the
    person-session policy untouched (`SUP-356`); both slices re-plan `No changes`. `DT-14` passes
    in both targets. Simulated as each project role under its attached boundary: Production reads
    row for row what the planned document read, 16 `explicitDeny` of the boundary's and 23
    `allowed`, AgentCore's code interpreter on its own resource among the denies; Staging reads 16
    `explicitDeny`, its deploy role's assumption, the data key and the state's key through S3,
    the outputs, derived and state buckets through Access Grants, a secret under either name,
    Bedrock, AgentCore and the assistants, and 22 `allowed`, the pull of the application's image
    from Production's registry among them. A simulation: neither role has run the application.
22. **The application's source in a target under the CLI** (4.9, 4.11; Stage 9 8.5). On the Terraform
    path the application slice gave each target's Glue job `--SOURCE_TABLE`: the governed
    `curated.trades`, on a second Iceberg catalog over the lake account's with Lake Formation's
    credential resolver in the job's `--conf`, read as the job role through the account's share. The
    CLI deploys one definition to every project, the job is the operator's, and its role is the
    project's, which holds no grant on the lake.
    (a) Release F reads the inbox in every stage, as `dev` does. The governed read returns in a later
    release: a stage variable naming the table, the lake catalog's settings in the workflow's
    `--conf`, `DESCRIBE` and `SELECT` by the consumers' tag expression to each project role in
    `<env>/data/`, and decision 15's deny grown to the lake's catalog and
    `lakeformation:GetDataAccess`. It is measured first in the `dev` project, where the lake
    catalog's settings sit beside the product's write for the first time. (b) The governed read in
    release F's first release, unmeasured in a project. (c) No governed read by a chain application,
    whose product is computed from what its own inbox receives.
    **Recommended: (a)**: release F already changes who deploys, who runs and where the data lands,
    and the lake catalog's `fs.s3` credential settings apply to every S3 call of the job, the product
    table's write included, a combination nothing has run. Its cost: until that release Production's
    product is computed from the sample, and Stage 9 8.5's reading is the Terraform path's alone.
    Under each option 4.11's sentence on the lake's write share narrows: the application reads
    `curated` and writes nothing there, so the project role takes a read and never the write.
    **Taken 2026-11-12 by the user as (a)** (*"Sim, como recomendado"*, the answer to decisions
    22 to 24 asked together): release F reads the inbox in every stage, as written, and the
    governed read is item 32, a later release's.
23. **How a run a chain starts gets the stage's variables** (4.11, xxiii, xxix). The CLI 1.0.9
    writes each `{env.VAR}` of a workflow into the deployed definition as `{{ params.VAR }}` and
    fills it only on a run it starts (`helpers/context_resolver.py`, `workflows/operations.py`;
    `SUP-282`): a run started without them fails before its first task, and a chain's machine
    starts the run.
    (a) The leg records the stage's variables, as the deploy filled them, in an SSM parameter,
    `/awsds/<env>/applications/<app>/stage-variables`; the machine reads it and passes it as
    `OverrideParameters`. The chains stay `[P]` and no pipeline job applies Terraform. (b) The
    pipeline applies the chains slice at each release with the release's values, the image's digest
    among them, as it applied `orchestration/`. (c) The leg writes each `{env.VAR}`'s value into the
    bundle's workflow files before the deploy, so the definition holds literals and any start works,
    the portal's included.
    **Recommended: (a)**: one record of what the last deploy ran with, read by the machine and by a
    person; (b) keeps Terraform in the legs, which decision 16 (b) retired; (c) changes the bundle's
    files between the release and the deploy. Its cost: one object per application and stage, written
    by the deploy role and read by the chain role, and a deploy that fails between the CLI and the
    record leaves the chains on the previous release's variables beside the new definitions.
    **Taken 2026-11-12 by the user as (a)** (the same answer): the record and its reader stand as
    written, `scripts/deploy-application.py` writing the parameter and `orchestration-v0.3.0`'s
    machines reading it; the deploy roles hold the `ssm` statement since that day's applies, and
    the chain roles take theirs with `<env>/chains/`. xxix reads a run at 4.10.
24. **The integration test's read of the product table** (item 13). Decision 14 (d) reads the table
    through Athena as the deploy role. Staging's enforced workgroup writes its results to
    `awsds-staging-derived` under the account data key, and the bucket's policy and the key's name
    their principals, so the read needs the deploy role in `staging/data/`'s bucket and key
    policies besides the Lake Formation grant and the IAM statements.
    (a) The leg reads the table's metadata with `glue:GetTable` under `DESCRIBE`: its type, its
    metadata location, its registration. The rows are counted by the run itself, which reads the
    table back as the project role and fails on a count that differs. (b) The Athena read as taken,
    `staging/data/`'s policies amended and `SELECT` granted.
    **Recommended: (a)** for release F; (b) the day a release needs another principal's read of the
    rows. It amends decision 14 (d), the user's.
    **Taken 2026-11-12 by the user as (a)** (the same answer): `staging-test` reads the table's
    metadata under the deploy role's `DESCRIBE` on `app_etl` and its tables, applied that day in
    `staging/studio/`; the Athena read, a `SELECT` grant and `staging/data/`'s policies are not
    written. Decision 14 carries the amendment.

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
unmerged or its publishing task gated; the project role's `datazone:StartDataSourceRun` removed by
reverting `sandbox/workflows/main.tf`'s statement and applying the slice. What stays: the lineage events and nodes, the source runs'
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
  orchestration module's workflow resource retires with the warehouse workflow's move (decision 16
  (b)). Since 1.1 (2026-10-31) `scripts/render-workflow.py` carries two interim rows and drops the Glue
  task's product-table arguments, which 4.11 retires with the render. Each lands on the next tag's
  sitting, `runbooks/promotion.md` §N.8.2, and this stage's text is the obligation's record at both
  ends until that session writes its own (Lesson 34).
  Decision 19 (c) (2026-11-11) adds the `test` stage's retirement: `test-deploy` gives way to the
  bundle job, `store-bundle` keeps what Staging's leg runs first (Stage 8 decision 20), and Stage 8's 2.5
  and 3.3 follow.
  **On 2026-11-11 no session held Stages 8-10**, and the user asked this one for the review across
  them: the dated amendments of decision 19 (c) in the Stage 8 and Stage 10 files, the runbooks and D41
  are this sitting's, and release F's rewrite of Stage 10's 1.1, 2.4 and 4.2 stays owed with 4.9.
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
