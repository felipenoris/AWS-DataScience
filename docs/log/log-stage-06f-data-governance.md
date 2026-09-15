# Log — Stage 6f: data governance on the SageMaker Catalog

*The stage file is [`docs/plan/stages/stage-06f-data-governance.md`](../plan/stages/stage-06f-data-governance.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

## 2026-09-12/13 — a database and a table from the portal, before the stage existed

*Taken in 6d's thirteenth sitting and moved here when this stage was written; the query and quota half of
that sitting stays in [`log-stage-06d-unified-studio-remainder.md`](log-stage-06d-unified-studio-remainder.md).
Times are UTC; the sitting ran from 2026-09-13 01:45Z.*

### A database from the catalog

- **[user] Create database.** *Data → Catalogs → AwsDataCatalog* showed the Athena workgroup
  `workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c`. *Create database* made `mydatabase`, location
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/`. The
  questions: *"Entendi que isso se trata de uma base de dados no formato "Athena" que fica persistida no
  bucket S3 do projeto, correto?"* and *"O `mydatabase` aparece na interface como "Created by DataZone".
  Isso é Athena ou AWS Glue?"*

- **[Claude] A Glue database, written by the provisioning role.** `glue:CreateDatabase` at 01:45:38Z by
  `awsds-sandbox-smus-provisioning` through `datazone.amazonaws.com`: description *"Created by DataZone
  for project eighth-experimentation"*, `CreateTableDefaultPermissions: []`, no tables, and no object
  under `dev/data/`. The workgroup is the project's enforced one, with results in `dev/sys/athena/` under
  `alias/awsds-sandbox-project`.

- **[Claude] The project's `dev/` scope is LF-registered, and `GOVERNANCE.md` said it was not.**
  `lakeformation list-resources` in Sandbox returns one location, `…/avhvbqn37ty7m8/dev`, registered
  under `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` with hybrid access off. CloudTrail since
  2026-08-20 holds five `RegisterResource` calls by the provisioning role, this project's at its creation
  (2026-08-23 17:31:47Z), and four `DeregisterResource` calls for the deleted projects. Every grant in
  that window came from the provisioning role. The grants to `<account-id>:IAMPrincipals` and
  `arn:aws:identitystore:::user/*` all carry `context has datazone && context.datazone has projectId &&
  context.datazone.projectId=="<project-id>"`; the grants to `awsds-sandbox-smus-manage-access` carry no
  condition. For `mydatabase` the conditioned principals received `CREATE_TABLE`, `DESCRIBE` and `DROP`
  on the database, and `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DROP` and `DESCRIBE` on its tables. The
  manage-access role's only Lake Formation call, `CreateLakeFormationOptIn` on `mydatabase` at 01:45:46Z,
  was refused *"because no identity-based policy allows the lakeformation:CreateLakeFormationOptIn
  action"*. Neither SMUS role granted, revoked or registered anything on `raw` or `curated`.

### A table from an upload

- **[user] A table by upload.** Uploading a Parquet file created `house-price`, and the file stayed at
  `dev/local-uploads/1789265679189/house-price.parquet`. The questions: *"Esse arquivo parquet é o local
  para onde o AWS Glue referencia, de forma que o Athena ao executar consultas lê diretamente deste
  arquivo? Se eu apagar este arquivo do bucket, a tabela "quebra"?"*

- **[Claude] The table points at the folder.** `glue:CreateTable` at 02:14:48Z, by the project role from
  the browser: `EXTERNAL_TABLE`, `ParquetHiveSerDe`, location `…/dev/local-uploads/1789265679189/`,
  `IsRegisteredWithLakeFormation: true`. The folder name is the upload's time in milliseconds
  (02:14:39Z), and the database's `LocationUri` was not used. The 9,249-byte file is the only copy of the
  data.

- **[Claude] Recorded the same sitting.** `GOVERNANCE.md` (the `dev/` row and the corrected registration
  sentence), `SMUS.md` §S3 item 1b, open question 24 (the trail reading), `AWS_STATE.md` and
  `REFERENCES.md`. `./aws/datalake.py` gained `DL-14` and was run: a `note` for the project's `dev/`
  scope, all checks passed.

## 2026-09-13 — the first sitting: publish to catalog, a data product, and what neither changed

*The user published the table and built a data product on it by hand, then asked what the features are.
Claude answered from the vendor documentation, read the trail once the user signed in again, and wrote
this entry at the user's request. Times are UTC.*

- **[user] Publish and a data product, by hand.** *"No menu Data -> Catalogs -> AwsDataCatalog ->
  mydatabase -> tables -> house-price. Acionei a opção `Publish to Catalog`. Notei que isso fez a tabela
  aparecer na lista de `assets`acessível pelo menu Manage -> Catalog Management -> Assets."* Then *create a
  new data product with this asset*, published. The questions: whether *Share* works only inside one
  SageMaker domain; whether a data product is a set of assets; *"é algo específico do SageMaker, ou é a
  feature do Glue Catalog?"*; its reach and its use cases; whether data products are only Parquet files in
  project S3; and how it fits an institution whose lake is in Redshift, and whether a data scientist
  should create databases there.

- **[Claude] Answered from the documentation** (the 2026-09-13 rows in `REFERENCES.md`). The SageMaker
  Catalog's scope is the domain, with discovery crossing the account and Region boundary; a Share makes S3
  data available to chosen projects *"right away, without needing a subscription process"*; a data
  product groups assets into *"well-defined, self-contained packages"*; no mechanism between domains is
  named.

- **[Claude] The session expired mid-reading.** `lookup-events` in `Data Governance` returned *"The SSO
  session associated with this profile has expired or is otherwise invalid."* Sandbox's trail, read up to
  04:25Z, held no catalog write, because the catalog's writes are logged in `Data Governance`.

- **[user]** *"sso infrastructure logado. pode realizar as leituras."*

- **[Claude] What the clicks created, from `Data Governance`'s trail**, every call as
  `awsds-data-studio-domain-execution` with the user's Identity Center id in the session name:
  - 04:06:38Z `CreateDataSource`: type `GLUE` over `mydatabase` with `INCLUDE *`, `dataAccessRole` the
    project role, `publishOnImport: false`, no schedule, `enableBusinessNameGeneration: true`, connection
    `5pf7uc0ugllsb4`. `list-data-source-runs` returns none.
  - 04:06:41Z `CreateAsset`, `amazon.datazone.GlueTableAssetType`, external identifier the table's ARN;
    04:06:42Z `CreateListingChangeSet` `PUBLISH`, listing `house-price`.
  - 04:06:44Z to 04:06:54Z, by `datazone.amazonaws.com`: two `CreateLineageNode`, three
    `CreateLineageNodeVersion` and three `UpdateLineageNode` calls.
  - 04:08:18Z `CreateDataProduct` `my-data-product`, one item, the asset; 04:17:06Z its
    `CreateListingChangeSet` `PUBLISH`.

- **[Claude] What they did not change.** Sandbox's trail for the same window holds reads only, as the
  project role: `GetTable` from the browser, `GetTables` from a `SYSTEM` session, and
  `lakeformation:ListPermissions` from an `AWSDataZone-Subscriptions` session. No Glue or Lake Formation
  write, and no call by either SMUS role. The table's grants are its creator's (the project role, `ALL`
  with the grant option), and `list-lake-formation-opt-ins` is empty. `search-listings` returns the two
  listings, both `ACTIVE`; `list-subscriptions`, `list-subscription-requests` and
  `list-subscription-grants` return 0 for each.

- **[Claude] The domain's IAM administrator cannot read a project's inventory.** From
  `InfrastructureAccess` in `Data Governance`, `get-asset` and `get-data-product` were refused by
  DataZone, *"User is not permitted to perform operation: GetAsset"*, while `search-listings` and
  `get-data-source` answered.

## 2026-09-13 — the second sitting: the stage written

- **[user] The instruction.** *"Crie um plano stage 6f para governança de dados, explorando as features
  DataZone V2, Glue Catalog, oferecidas pelo SageMaker. Crie um log para este estágio associado a estes
  passos que eu já executei."* With four concerns: *"(1) teoricamente o ambiente interativo sagemaker é
  apenas para maturação de projetos. Um produto de dados produzido deveria ser publicado pelo pipeline
  executado no runtime sagemaker de produção. Isso seria implementado através de associação de contas?
  (2) ainterqção com redshift: estes produtos de dados podem ficar visíveis no Redshift? Ou é o inverso:
  as bases redshift deveriam constar no glue catalog? Quais produtos de bases de dados aws são compatíveis
  com o catálogo glue? (3) no runtime produção sagemaker, ele terá um outro catálogo glue associado? (4)
  estas associações são permitidas apenas dentro de um mesmo domínio sagemaker?"*

- **[Claude] Read for the answers.** The DataZone user guide: an account *"can be associated with one or
  more"* domains, and *"Access management for the AWS Glue Data Catalog assets using the AWS Lake
  Formation LF-TBAC method is not supported"*. Redshift: the auto-mounted `awsdatacatalog` database is
  read-only, and a namespace registered to the Glue Data Catalog becomes a federated catalog. The Glue
  crawler's supported data stores. In this repository: `studio.py` `US-3` fails on any blueprint
  configuration in `Data Governance`, and `GovernanceManagerAccess` carries the subscription approval
  verbs.

- **[Claude] Written.** The stage file with its steps, verifications and decisions due; `INT-23` in
  `integrations.md`; the stage's rows in `GENERAL_PLAN.md` and `stages/INDEX.md`; this log and its row in
  `docs/log/INDEX.md`; the catalog half of 6d's thirteenth sitting moved here; the sources in
  `REFERENCES.md`.

- **[user] The catalog's scope and the domain's place.** *"SageMaker Catalog e Glue Catalog são coisas
  diferentes?"*; *"Se a publicação/assinatura/share ocorre apenas dentro do domínio sagemaker, então a
  instituição inteira teria que usar um único domínio sagemaker para utilizar esta feature de forma
  institucional?"*; *"Pode aplicar as alterações necessárias e subir no PR. O runtime de produção vai ser
  associado ao mesmo domínio sagemaker? Esse domínio mora em qual conta? Os dados dos lakes de produção
  estão desenhados para morar na conta data governance ou produção?"*

- **[Claude] Answered, and a row corrected.** The Glue Data Catalog is per account and Region, the
  SageMaker Catalog per domain. The domain lives in `Data Governance`, Production is never associated
  (D26, `DenyDataZoneEntirely`), and the lake's data live in `Data Governance` (D22). The domain-topology
  row of `institutional-delta.md` named a domain per business data domain; it now reads one DataZone
  domain for the institution with a domain unit per business data domain, and the lake-placement and
  approval rows say "business data domain" too. The stage's boundary item 4 gained the domain units.
  Committed to the PR with the stage.

- **[user]** *"Então os catálogos (glue e sagemaker) moram na conta data governance. O domínio SageMaker
  também. E as outras contas todas se associam a este domínio. A conta Data Governance deveria ter camada
  interativa para permitir configuração do catálogo do sagemaker?"*

- **[Claude] Answered: no.** Two premises corrected: each account holds its own Glue Data Catalog
  (`mydatabase` and `house-price` are in Sandbox's), and only the interactive accounts are associated.
  Configuring the catalog is DataZone control-plane work from the portal or the API, whose catalog calls
  already run in `Data Governance` as the domain execution role; D22 and D26 keep compute out of the
  account, and `US-3` fails on any blueprint configuration there. Nothing was written.

## 2026-09-15 — the third sitting: LF-Tags beside the catalog, and the data-product cycle in `GOVERNANCE.md`

*No AWS call was made. Claude answered from the repository and the vendor documentation and wrote the
files at the user's requests; this entry was written at the user's request. Times are UTC.*

- **[user] 02:06Z.** *"No quadro comparando Glue Data Catalog e SageMaker Catalog, onde se encaixa nesse
  processo o controle de acesso por LF Tags?"*

- **[Claude] Answered.** An LF-Tag is Lake Formation's: it is assigned to a Glue object, and Lake
  Formation holds it, its inheritance and the evaluation. Two grant forms reach the same Lake Formation:
  the register's TBAC, with the attribute on the data, and the named-resource grants SMUS writes under
  `context.datazone.projectId`, with the attribute on the session.

- **[user] 02:15Z.** *"Registre essa distinção (TBAC vs ABAC) no stage 6f e no SMUS.md. Considerando que
  o SMUS é utilizado como ferramenta de desenvolvimento de produtos de dados, fornecendo as features de
  governança, em qual momento no fluxo de desenvolvimento de um produto de dados pelo SageMaker seriam
  atribuídas as LF Tags? O SageMaker não é autosuficiente ?"*

- **[Claude] Written, and answered.** The distinction went into the stage's catalog section and
  `SMUS.md` §S3 1b. No act read on 2026-09-12/13 assigned an LF-Tag; the tag belongs to the table's
  declaration in `Data Governance`, before the promotion that writes it. SageMaker covers development
  and the catalog, and the lake's entitlement is policy in the register.

- **[user] 02:34Z.** *"Pode ajustar tb GOVERNANCE.md. Considerando estas limitações do SageMaker, isso
  inutiliza as features de governança de dados disponibilizadas pela interface do SageMaker?"*

- **[Claude] Written, and answered: no.** `GOVERNANCE.md` §Access control gained the second form. The
  catalog keeps discovery, business metadata, ownership and the request record, data products, lineage,
  domain units and access between projects' own tables; a subscription as the entitlement to a lake
  table is what stays out. A shape (d) was proposed: the lake published as unmanaged assets, with the
  grant made in the register.

- **[user] 03:19Z.** *"Sim, inclua a forma (d) na 6f. Revise `GOVERNANCE.md` considerando as discussões
  desta sessão."* The instruction asked for the development cycle, publishing and sharing, business
  metadata, promotion between environments, the rite for assigning LF-Tags and the infrastructure it
  changes, in a text that *"vai apoiar a criação de uma apresentação sobre o tema"*, with an outline:
  accounts, catalogs and Lake Formation, access controls and LF-Tags, the development cycle.

- **[Claude] Written.**
  - The stage: shape (d) in 3.1, with 3.2, 3.3, verification v and decision due 1, which now recommends
    (d) if 3.1 finds it possible and (c) otherwise; 7.1 points at the new cycle section; the three-system
    table moved to `GOVERNANCE.md`.
  - `GOVERNANCE.md`: §Accounts, a diagram and a table of what each account holds; §Catalogs, the three
    systems side by side, a data product beside the lake and a warehouse, and a subsection each, the
    SageMaker Catalog's with its features; §Access control, the two forms side by side; §"The
    development cycle of a data product", a diagram and four subsections, the last the rite for a
    curated table's tags. Both diagrams rendered in a local browser without a syntax error.
  - `CLAUDE.md`'s routing row for `GOVERNANCE.md`.
  - One premise of the outline was not carried: Staging writes nothing into `Data Governance` (D20).

- **[user] 11:58Z.** *"Sim, escreva o log e suba no PR."*

- **[Claude] Corrected before the commit, reading the new text against its sources.**
  - "Lake Formation has no deny" had no source. Lake Formation's metadata-permissions page states the
    rule the argument needs, that a principal's permissions are the union of its grants, named-resource
    and LF-Tag alike (`REFERENCES.md`); the stage, `SMUS.md` and `GOVERNANCE.md` carry that rule instead.
  - A fulfilment grant had been written as the conditioned form. DataZone documents it as a
    named-resource grant, and its condition is verification i.
  - The chat had said the catalog does not read LF-Tags; whether a published asset shows them is 4.1.
  - Sentences about Stages 7-10 were narrowed to what those stages say, and the rite is marked designed
    and not exercised.
