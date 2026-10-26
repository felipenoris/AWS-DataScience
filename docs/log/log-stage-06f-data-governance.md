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

## 2026-09-18 — `catalog.py`, the domain's authorization, and what a publish did not do

*Claude's sitting, read-only throughout, as `awsds-infra-data` and `awsds-infra-sandbox-1`. It closes
steps 1.1, 1.2 and 1.3 and answers verification vi ahead of step 4.1. Times are UTC.*

### The instrument

- **[Claude] `./aws/catalog.py` written and run.** Two fixed profiles, nine checks `CT-1`..`CT-9`,
  `aws/output/catalog.txt`. First run: `CT-1`, `CT-2`, `CT-4`, `CT-7`, `CT-8`, `CT-9` pass; `CT-3`,
  `CT-5`, `CT-6` are notes. Its row is in [`aws/INDEX.md`](../../aws/INDEX.md).

- **[Claude] `CT-1`'s first draft was wrong, and the way it was wrong is the finding.**
  `datazone list-domains` **in an associated member account returns the shared domain**, so the draft
  read the association as a second domain and failed `CT-1` against `D26`. The discriminator is
  `managedAccountId`, which names the owning account and reads the same on both sides of an
  association. Rewritten against that field: the consumer account **sees** the domain and **owns**
  none.

- **[Claude] The three classifiers were exercised against fabricated grants** (Lesson 13's discipline):
  `touches_lake` on seven cases — the lake's three databases, a tag expression and the registered raw
  prefix caught, the project's own database, table and `dev/` scope not — and `is_smus_principal` on
  six, with `DataScientistAccess` and `awsds-data-catalog-maintenance` as the negative controls. No
  account id reaches the report.

### 1.1 — the domain's authorization, read on the root domain unit

- **[Claude] Of the policy types that apply to a domain unit, one carries a grant and one carries the
  default.** `CREATE_PROJECT`, `CREATE_DOMAIN_UNIT`, `CREATE_GLOSSARY`, `CREATE_FORM_TYPE` and
  `CREATE_ASSET_TYPE` are **empty**; `CREATE_PROJECT_FROM_PROJECT_PROFILE` names **one Identity Center
  group**; and **`ADD_TO_PROJECT_MEMBER_POOL` reads `{"user":{"allUsersGrantFilter":{}}}`** — every user
  of the domain may be added to any project's member pool, which is DataZone's default and the axis
  open question 20 is written on.

- **[Claude] Both override types are empty**, so the owner project's approval is the control on the
  catalog road: `OVERRIDE_DOMAIN_UNIT_OWNERS` and `OVERRIDE_PROJECT_OWNERS` name nobody. `CT-9` is that
  reading.

- **[Claude] Two policy types are refused to `InfrastructureAccess`** — `CREATE_ENVIRONMENT` and
  `USE_ASSET_TYPE`, `AccessDeniedException` on `ListPolicyGrants` — and four are rejected as not
  applicable to a domain unit. The report prints `DENIED` for the first pair and does not ask for the
  second: a refused read and an empty policy are different facts (0.6's ceiling, measured again).

### 1.2 — the domain execution role, and what its managed policy carries

- **[Claude] `awsds-data-studio-domain-execution` holds one AWS-managed policy and no inline policy**:
  `SageMakerStudioDomainExecutionRolePolicy`, **at version 23**, trusted by `datazone.amazonaws.com`,
  with **no permissions boundary**. Three of its statements decide where decision due 5 can live:
  - `DataZonePermissions` grants the **whole approval cycle** — `AcceptSubscriptionRequest`,
    `RejectSubscriptionRequest`, `CreateSubscriptionGrant`, `DeleteSubscriptionGrant`,
    `RevokeSubscription` — **and `AddPolicyGrant` / `RemovePolicyGrant`**, so the role can change the
    domain's own authorization policies, the ones 1.1 just read.
  - It also grants `datazone:GetEnvironmentCredentials`, the API open question 20 is about, on the
    service's own role rather than on a persona.
  - `AmazonQPermissionsStatement` grants **`q:PassRequest`**, which lets Amazon Q act with the caller's
    credentials. [Stage 6d](../plan/stages/stage-06d-unified-studio-remainder.md) step 10.5 proposes
    denying that action on the argument that *"the managed policy does not grant it today"* — true of the
    **project** role's policy, and **false of this one**. The deny that step writes is therefore not
    redundant, and its target list is what the reading changes.
  - `AllowSetTrustedIdentity` grants `sts:SetContext`, trusted identity propagation's own action, on a
    role in a domain where the Tooling parameter is locked `"false"` (open question 13).

  The policy is AWS's and versioned, so every sentence above is dated to v23 (Lesson 11).

### The catalog as it stands, and what publishing did not change

- **[Claude] Two listings, no access act.** `house-price` (a `GlueTableAssetType`, revision 2) and
  `my-data-product`, both owned by `eighth-experimentation`. Subscriptions, subscription requests and
  subscription grants are **zero on both**, which confirms 0.4 from the other side: a publish is
  metadata, and nothing on the catalog road has granted anything.

- **[Claude] A second data source exists, and the blueprint wrote it.** Beside the Glue source 0.4
  recorded, `Tooling-default-sagemaker-modelpackagegroup-datasource` tracks
  `SageMakerModelPackageGroupAssetType` and **runs on `cron(32 17 * * ? *)`** — a daily schedule nobody
  in this repository chose, created with the project's Tooling environment (Lesson 17). It was `RUNNING`
  when read, at 17:38Z, with `lastRunAssetCount` 0. `CT-6` names it rather than leaving it to be
  discovered.

- **[Claude] The AI half of decision due 3 has a reading now**: the Glue source carries
  `enableBusinessNameGeneration: true` and the SageMaker source `false`. Neither publishes on import
  (`CT-4`), so no listing has ever been created without a person asking for it.

- **[Claude] `CT-7` passes, and it is the check the stage exists for.** Twelve grants are held by
  SMUS-managed principals — the conditioned `IAMPrincipals` entries, the project role, the provisioning
  role and the manage-access role — and **every one is on a project-owned object**: `mydatabase`,
  `default`, `mydatabase.house-price` and the project's `dev/` data location. None reaches `raw`,
  `curated`, `dropbox` or an LF-Tag. The lake and the catalog do not touch yet, measured rather than
  assumed.

- **[Claude] Every `IAMPrincipals` grant carries the project condition** (`CT-8`): all five read
  `context has datazone && context.datazone has projectId && context.datazone.projectId=="<project>"`,
  written by `awsds-sandbox-smus-provisioning`. Without that condition the principal is the whole
  account.

### Verification vi, answered before its step: a published asset shows no LF-Tag

- **[Claude] `get-listing` on `house-price` carries `lakeFormationDetails: {}`** — the field exists and
  is empty. The listing's forms are `AwsConfigurationForm`, `CommonDetails`, `DataSourceReferenceForm`,
  `GlueTableForm` and `SubscriptionTermsForm`; `GlueTableForm` carries the column names and types and
  no tag.

- **[Claude] There was nothing for it to show.** `list-lf-tags` in **Sandbox returns none** — the
  ontology (`layer`, `businessunit`, `classification`) is defined in `Data Governance` alone — and
  `get-resource-lf-tags` on `mydatabase.house-price` returns no assigned tag. So the answer to
  verification vi is **no**, and this reading cannot yet separate *the catalog does not display
  LF-Tags* from *this asset has none*: the separating case is a lake table published under decision 1,
  and 4.1 stays open for it. What follows today is 4.1's own alternative — `classification` and `layer`
  reach the catalog through a glossary or a required metadata form, not for free.

- **[Claude] `list-lineage-events` returns empty.** The two lineage nodes 0.4 recorded were written by
  the publish itself; no OpenLineage event was ever posted, which is 6.2's starting point.

### 3.1's API half, and what it leaves to the vendor pages

- **[Claude] Shape (a) has its targets.** Sandbox's Glue catalog carries the resource links `raw` and
  `curated`, both with `TargetDatabase` in the registry account's catalog — Stage 5 pass 4's objects,
  still there. Whether a DataZone Glue data source accepts a resource link as its `databaseName` is
  not answerable by reading and stays this step's first vendor question.

- **[Claude] Shape (b) starts from nothing.** `list-environment-blueprint-configurations` in
  `Data Governance` returns **zero**. That is `US-3` passing, and it is also (b)'s whole cost: the
  configuration would be the first object ever configured in that account, against D22.

- **[Claude] Shape (d) needs no custom asset type.** `search-types --managed --search-scope
  ASSET_TYPE` returns **23**, including `GlueTableAssetType` — the type `house-price` already carries
  — all owned by `dzd_amazon_datazone_domain_project`. What this does not settle is whether a Glue
  table can be published **unmanaged**, which is a property of the fulfilment and not of the type, and
  is the second vendor question.

- **[Claude] The manage-access role already writes the grant form 3.2 describes, on a project
  object.** `awsds-sandbox-smus-manage-access` holds `DESCRIBE` on `mydatabase.house-price` and
  `SELECT` on its columns, **both with the grant option**. So the shape (a) and (b) would need is one
  the service already produces for project-owned tables; the untested case is the same grant on a lake
  table across the account boundary, where every cross-account grant must carry the option anyway
  (Stage 5 pass 3's finding).

## 2026-09-18 — step 3.1's documentation half, and what it costs decision due 1

*Claude's sitting, no AWS call: four vendor pages read in the browser, recorded in
[`REFERENCES.md`](../REFERENCES.md) the same sitting.*

- **[Claude] A Glue data source takes any database by name, and the dropdown is the tell.** *"You can
  either choose an AWS Glue database from the dropdown or type a database name… If you want to bring
  assets from a database that is not created by the environment, then you must type the name of the
  database instead of selecting it from the dropdown."* The dropdown offers the environment's
  publishing and subscription databases and nothing else. So shape (a) is mechanically possible: the
  resource links `raw` and `curated` are local databases and can be typed.

- **[Claude] Creating the data source is an access act, and this is what the step did not know.**
  *"When an AWS Glue data source is created, Amazon DataZone creates the Lake Formation 'read only'
  permissions for the IAM role of the environment that is used to create the data source to access
  **all the tables** in the AWS Glue databases used in the data source."* That grant is written at
  **creation**, over the **whole database**, before any subscription exists and before anyone
  approves anything. Under shape (a) pointing a data source at the lake's resource links would grant
  a Sandbox environment role read over every table in `raw` or `curated` — wider than the TBAC share
  it sits beside, and invisible to the register unless somebody reads for it. `catalog.py`'s `CT-7`
  is what would report it.

- **[Claude] It also tags the database.** `DataZoneDiscoverable_${domainId}: true` on the Glue
  database, written when the grant is made. An attribute assigned to describe becomes a selector the
  moment a rule is written over it (Lesson 29), and this one is AWS's, on a database this repository
  owns.

- **[Claude] Shape (d) does not exist for a Glue table as this stage wrote it.** *Managed* is a
  property of the **asset type**, not a publisher's choice: the concepts page names Glue tables and
  Redshift tables and views as managed, and says that *"for all other asset types (unmanaged assets)"*
  DataZone emits an EventBridge event instead of fulfilling. The domain's 23 managed types include
  `GlueTableAssetType`, which is what `house-price` already carries. Publishing the lake unmanaged
  therefore needs a **custom asset type** standing for a table DataZone can see and has been told not
  to fulfil — at the price of a type whose schema the catalog does not derive and whose meaning no
  other tooling shares.

- **[Claude] Two riders, recorded because they will be looked for.** Cross-**Region** sharing of Glue
  assets is not supported; this estate's shares are cross-**account**, same Region, so it does not
  bite. And the manage-access role's requirement is four permissions, not two: `DESCRIBE` and
  `DESCRIBE GRANTABLE` on the database, `DESCRIBE`, `SELECT`, `DESCRIBE GRANTABLE` and
  `SELECT GRANTABLE` on the table — which is the shape 1.3 found it already holding on the project's
  own table.

- **[Claude] Decision due 1's recommendation is re-read, and it moved.** It recommended (d) if
  possible and (c) otherwise. (d) is not possible without a custom asset type; (a) is possible and
  costs more than the step credited it with — a grant at creation, over a whole database. So the
  recommendation is now **(c)**, the lake kept out of the catalog and read through TBAC re-grants,
  with **(d) as the shape to revisit** if discoverability of the lake turns out to matter more than
  keeping every lake grant in the register. The choice is the user's, and both remaining shapes leave
  the TBAC model intact.

- **[Claude] Step 5.1 is not closed.** The Glue data-source page names the switch — *Automated
  business name generation*, *"whether to automatically generate metadata for assets as they're
  imported from the source"* — and `CT-5` has read it **on**. What the sitting did not find is the
  page that says **where the generation runs and what it sends**, which is the half 5.1 exists for
  and the half decision due 3 needs. Four slug guesses missed and the doc search returned only API
  and SDK pages for `BusinessNameGenerationConfiguration`.

## 2026-09-18 — steps 6.2, 8.1 and 9.1, the three that needed no AWS call

*Claude's sitting. One vendor page read for 6.2 and recorded in [`REFERENCES.md`](../REFERENCES.md);
8.1 and 9.1 are written from what 1.1 and 1.3 already measured.*

### 6.2 — the engines, and a switch that is not where the step looked for it

- **[Claude] Lineage arrives three ways, and only one of them is a toggle.** Automatic capture from
  **AWS Glue and Amazon Redshift databases** added to the domain; **Spark ETL job runs in AWS Glue
  v5.0 and higher**, from the console or a notebook; and the **OpenLineage-compatible APIs** for
  anything else. Two node types carry it, a dataset node (auto-generated for published Glue and
  Redshift assets, hand-made for the rest) and a job (run) node with its history.

- **[Claude] The automatic half is configured on the blueprint.** *"Domain administrators can
  configure lineage while setting up data lake and data warehouse built-in blueprints, which ensures
  that all data source runs created from those resources are enabled for automatic lineage capture."*
  The eleven blueprint configurations here are **Terraform** (`US-3`), so turning lineage on is a
  reviewed code change to `sandbox/sagemaker/`, not a console click. That fits the reading this
  stage already had: `list-lineage-events` is **empty**, and the two nodes 0.4 recorded came from the
  publish itself.

- **[Claude] What the page does not say went to the stage that owns it** (Lesson 34): it names no
  orchestrator, and **MWAA Serverless is this estate's only one**. [Stage 10](../plan/stages/stage-10-orchestration-promotion.md)
  gained step **3.3** — run `app-etl` once, read `list-lineage-events`, and take one of three
  branches depending on whether the service emits, can be made to emit through Airflow's own
  OpenLineage provider, or emits nothing and the event becomes a line in the `app-etl` contract.

### 8.1 — the warehouse row

- **[Claude] Written into [`institutional-delta.md`](../plan/institutional-delta.md).** The lab builds
  **nothing** — D26 and D12 exclude `RedshiftServerless` — and the catalog is ready for it anyway:
  `RedshiftTableAssetType` and `RedshiftViewAssetType` are two of the 23 managed asset types 1.3 read.
  The institution registers the warehouse to the Glue Data Catalog as a **federated catalog**, which
  puts its schemas under the same Lake Formation permissions as the lake, publishes both asset types
  in one catalog, and lets scientists read governed schemas while writing only their own. The delta
  that matters: **one permission system over two storage engines**, and a warehouse outside Lake
  Formation needs its own grants, its own review and its own register, with the classification an
  LF-Tag carries stopping at the warehouse's edge. The revision trigger is the first workload Athena
  serves badly, and the reading to take then is whether federation preserves the TBAC expressions
  this estate grants by — DataZone's own Glue path already refuses LF-TBAC (3.2).

### 9.1 — what a domain unit scopes, written into Stage 14

- **[Claude] A domain unit is the object this estate's cardinality maps onto**, and
  [Stage 14](../plan/stages/stage-14-sandbox-vending.md) now says so beside the CIDR, the peerings and
  the zone: a vend adds a **domain unit**, never a second domain (the vendor documents no publishing,
  subscription or Share between domains). What it scopes, from the concepts page and from 1.1's
  reading of the live domain: the **authorization policies** per unit and per type — on this domain's
  root unit exactly one carries a grant — the **delegation** those policies exist for (*"a delegated
  authority from account owners to domain unit owners"*), and **glossaries, metadata forms and custom
  asset types** owned per unit.

- **[Claude] One thing a second vend has to look at first.** `ADD_TO_PROJECT_MEMBER_POOL` reads
  `allUsersGrantFilter` — every user of the domain. With one business unit that is the same set of
  people either way; with two it is the difference between units that can see each other's projects
  and units that cannot, and nothing in Stage 14's module touches it. Recorded there as the first
  reading the second vend takes, rather than as a decision taken now with N = 1.

## 2026-09-19 — the blueprint's own data source has been failing since the day it was created

*Claude's sitting, read-only, as `awsds-infra-data` and `awsds-infra-sandbox-1`, after the merge. It
began as a re-run of the instruments and turned up something no instrument was reading.*

### The three instruments agree, and one reading did not fit

- **[Claude] `catalog.py`, `studio.py` and `datalake.py` all clean.** `catalog.py` every check green;
  `studio.py` **0 checks FAILED** (`US-1`..`US-9`, with `US-2`'s two notes the resting state);
  `datalake.py` 30 passes and two notes, both recorded — `DL-13`'s two service-appointed Lake
  Formation seats and `DL-14`'s project `dev/` registration.

- **[Claude] What did not fit was `CT-6`'s subject.** The check named
  `Tooling-default-sagemaker-modelpackagegroup-datasource` as a cron nobody wrote, and the live
  `status` field read `RUNNING` — so the reading looked healthy. `list-data-source-runs` says
  otherwise: **25 `FAILED` and one `RUNNING`**, every run `SCHEDULED`, the oldest **2026-08-24**, the
  day after the Tooling environment created it.

### Why the live status hid it

- **[Claude] A run's `stoppedAt` equals its successor's `startedAt`.** The 2026-09-17 run started at
  17:38:11Z and stopped at 2026-09-18 17:38:11Z, when the next one fired. So a daily source always
  shows exactly one `RUNNING` run — the current 24-hour window — and **the field that describes the
  data source reads healthy however long it has been failing**. The history is the only place the
  failure is visible.

- **[Claude] The error is the same on every run**, read from 2026-09-17's:
  `VALIDATION_EXCEPTION`, *"Failed to run the data source. Please check if RAM share is correctly
  configured between Amazon SageMaker and Amazon DataZone"*. Its configuration snapshot tracks
  `SageMakerModelPackageGroupAssetType` over an **empty list**, with
  `enableBusinessNameGeneration: false`.

- **[Claude] It costs nothing and creates nothing**: `lastRunAssetCount` 0 on every run, no asset, no
  hourly meter. Recorded as [`AWS_STATE.md`](../AWS_STATE.md) **`EXC-11`** rather than fixed — the
  source tracks an asset type this estate has never produced, and the RAM share its error names
  belongs to a SMUS↔DataZone path no stage has built. It becomes a real gap when the Model Registry
  is used (Stage 9), and the alternative is a decision to delete the data source.

### The check that missed it, and the shape of the repair

- **[Claude] `CT-6` read the schedule and stopped there.** It was written to name a cron nobody
  wrote (Lesson 17) and passed over 26 days of daily failures, because it never asked how the runs
  ended. It now reads `list-data-source-runs` per source and judges on the **completed** runs.

- **[Claude] It is a note, not a failure, and the reason is Lesson 50.** A check that fails every run
  while a recorded exception stands teaches its reader to skip it. `FAILING_BY_EXCEPTION` names this
  one source with its exception id and date; `CT-6` reports it as a note citing `EXC-11`, and
  **fails on any other scheduled source whose completed runs have all failed**. Exercised against
  fabricated names, including a near-miss (`…-datasource-2`), which fails as it should. Closing
  `EXC-11` means deleting the row, and the check turns red the same day if the failure survives.

- **[Claude] The report's data-source table gained a `RUNS` column**, so the contrast that hid this —
  `STATUS RUNNING` beside `25 FAILED, 1 RUNNING` — is on one line.

## 2026-10-18 — readings with the environment down: the lineage nodes, 5.1, decision 5's DataZone half and `EXC-11` counted

*Claude's sitting (session `stage06f-readings`, started by the orchestrating session on the user's
instruction of the day to run the steps that need no environment), read-only throughout, as
`awsds-infra-data` and `awsds-infra-sandbox-1`, from about 19:45Z. Nothing was applied. The environment
was down (`make status` read 0.0000 USD/h). Vendor pages were read with the web fetch tool and are
paraphrased here; [`REFERENCES.md`](../REFERENCES.md) lists them. Times are UTC.*

### The instrument, re-run, and `EXC-11` counted

- **[Claude] `./aws/catalog.py` at 19:47Z: exit 0.** `CT-1`, `CT-2`, `CT-4`, `CT-7`, `CT-8` and `CT-9`
  pass; `CT-3`, `CT-5` and `CT-6` are notes. The domain has two projects, `eighth-experimentation` and
  `test-experimentation`; two listings, zero subscriptions, requests and grants; fourteen SMUS grants
  (twelve on 2026-09-18), all on project-owned objects, the two new ones being the second project's
  `default` entry and its `dev/` data location; seven `IAMPrincipals` entries (five), every one with the
  project condition. The domain's policy grants are as 2026-09-18: only
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` names a group, `ADD_TO_PROJECT_MEMBER_POOL` is
  `allUsersGrantFilter`, both override types are empty.
- **[Claude] `CT-6` exempts by name, and the name now covers two sources.** The run printed both in one
  sentence and never said there were two. Per project, from `list-data-sources`, `get-data-source` and
  `list-data-source-runs`: `eighth-experimentation`'s, created 2026-08-23 on `cron(32 17 * * ? *)`, has
  **55 `FAILED` runs and one `RUNNING`**, the oldest 2026-08-24 (25 on 2026-09-19);
  `test-experimentation`'s, created 2026-10-15 06:06Z with its Tooling environment on
  `cron(6 6 * * ? *)`, has **2 `FAILED` and one `RUNNING`**, the oldest 2026-10-16. That is 57 failed
  runs, every one `SCHEDULED`, `lastRunAssetCount` 0. The newest failed run of each carries
  `VALIDATION_EXCEPTION` and the RAM-share message of 2026-09-19, word for word. Each project's
  Tooling environment creates one, so a third project adds a third.
- **[Claude] `catalog.py` now says how many.** The `CT-6` note groups the excepted sources by name and
  prints their number with each project and cron; an unexcepted failing source still fails the check and
  now names its project. Re-run once, `ruff` clean.

### 5.1 and verification viii — where the AI generation runs

- **[Claude] The page was `autodoc`.** The four slug guesses of 2026-09-18 missed it; a search for the
  feature's own name found it in the DataZone guide and in the Unified Studio guide. Both say the feature
  is powered by Bedrock and inherits its controls and automated abuse detection; both list US West
  (Oregon) among the supported Regions; both use Bedrock's cross-Region endpoint for US East (Ohio) alone
  for names and descriptions, and the Unified Studio page adds glossary-term generation, which uses it in
  every supported Region. Business names are switched on per data source or by `predictionConfiguration`
  at `CreateAsset`; the quotas are 50,000 name and 10,000 description generations a month.
- **[Claude] What it sends comes from AWS's launch post, not from the pages.** The post (2024-04-02)
  says table names, column names and the producer's optional metadata, and no table rows unless the user
  puts them in the metadata. It does not name the model (the service manages the choice and may change
  it) and says nothing about storage, training or opting out. The 2025-07-01 post for custom assets
  shows a table name, columns and types as the input and is silent on sample rows.
- **[Claude] The pricing page puts business names under compute.** Descriptions bill by token as
  `PRICING.md` has them (USD 0.015 input, 0.075 output per 1,000); names bill as compute, USD 1.776 per
  unit with 0.2 free a month, per completed ingestion or name-generation job.
- **[Claude] Against 6e and D1.** For `us-west-2` the pages use the in-Region endpoint, so D1 holds for
  names and descriptions; glossary-term generation would leave the Region and nothing here uses it. 6e's
  retention mode is a setting of the account's own Bedrock use, and no page says it reaches the service's
  calls. The model is not named, so the per-model exceptions on Bedrock's abuse-detection page (read
  again: Fable 5 and 5.1 retain all traffic up to 30 days, most OpenAI models retain the traffic a
  classifier flags) can be neither ruled in nor out for it.
- **[Claude] Nothing has generated here.** The Glue source (`CreateDataSource` at 2026-09-13 04:06:38Z,
  `enableBusinessNameGeneration: true`, `publishOnImport: false`) has no run; `CreateAsset` at 04:06:41Z
  carries no `predictionConfiguration`; 90 days of Data Governance's trail hold no `StartDataSourceRun`;
  and the only `bedrock.amazonaws.com` events in that window, in either account, are AWS Config's own list
  calls. The service's calls would not appear there, so the last reading is not evidence.

### 6.1 and verification ix — the two publish-time nodes

- **[Claude] The trail named them.** The publish's two `CreateLineageNode` calls (04:06:44Z and
  04:06:53Z, `invokedBy datazone.amazonaws.com`, `requestParameters` null) carry the node in
  `additionalEventData`: `69dcbz6ii1j6hc`, source `amazon.datazone.asset/dbund4fvvvt05s`, and
  `58w6xmloxbpvkg`, source `amazon.datazone.listing/cetyru4cvy1bio`, both
  `amazon.datazone.DatasetLineageNodeType`. Three `CreateLineageNodeVersion` and three
  `UpdateLineageNode` calls follow. No other lineage event is in 90 days of either trail, no
  `PostLineageEvent` either, and `list-lineage-events` returns `items: []`.
- **[Claude] `GetLineageNode` was not refused.** As `awsds-infra-data`, where `GetAsset` is refused,
  both nodes read; the lineage page says the two read operations are open to every domain user. The
  persona's read is therefore not owed.
- **[Claude] What they link.** The asset node has no name and no forms, `upstreamNodes: []`,
  `downstreamNodes: [58w6xmloxbpvkg]` and two versions in `list-lineage-node-history`. The listing node,
  named `house-price`, has the asset upstream, nothing downstream, one version and four forms:
  `ListingLineageForm` (asset revision 1, listing revision 2, owner `eighth-experimentation`,
  `GlueTableAssetType`, `ACTIVE`), `DatasetSchemaForm` (13 columns), `DatasetForm` (`datasetType`
  `LISTING`) and `ColumnLineageForm`, which makes each listing column's source the same-named asset
  column. So the publish links an asset to its listing, column by column, and nothing outside the
  catalog: no job, no run, no source table and no S3 object.

### 6.2's blueprint claim, corrected

- **[Claude] No lineage field exists where the stage looked.** `get-environment-blueprint-configuration`
  for `DataLake` in Sandbox returns the provisioning and manage-access role ARNs, the boundary, the Region
  and its parameters (AZs, subnets, VPC) and no lineage field; the installed CLI's help for
  `create-data-source` and `put-environment-blueprint-configuration` does not mention lineage; and
  `terraform-live` and `terraform-modules` hold no file that does.
- **[Claude] The Glue sync is a connection property, and it is on.** The DataZone service model carries
  `glueLineageSyncEnabled` on the IAM and lakehouse connection properties and `lineageSync` on Redshift's
  and Snowflake's. `ListConnections` as `awsds-infra-sandbox-1` returns, in both projects,
  `project.default_lakehouse` (`LAKEHOUSE`) and `project.iam` (`IAM`) with `glueLineageSyncEnabled: true`.
  Neither trail holds an `UpdateConnection` in 90 days, so the value is the creation default. The stage's
  *switched on in the blueprint (Terraform here)* was wrong twice: the setting is not in the blueprint,
  and no Terraform declares it. An empty `list-lineage-events` says that nothing emitted.
- **[Claude] The Redshift side, told by the 6h session and read again.** The 6h session
  (`warehouse-5b-6h`) answered the note about the membership with the state of the Redshift connection's
  lineage sync, which it had not recorded. `get-connection` on `redshift-serverless.redshift` returns
  `lineageSync` with `enabled: true`, `cron(43 3 * * ? *)` and a lineage job; `list-job-runs` on that job
  returns eight runs, one a day from 2026-10-11, **all `FAILED`**; `get-job-run` on the newest returns
  zero queries processed and a `RedshiftData` status 400, *"Redshift endpoint doesn't exist in this
  region."*, the workgroup being `[E]` and down. The Glue sync on, the Redshift sync on and failing,
  and no event in the domain are the same reading: nothing has emitted yet.

### Who can read what: a membership dated 2026-10-15

- **[Claude] `ListConnections`, `GetConnection` and `GetAsset` answer in Sandbox and are refused in Data
  Governance.** `list-connections` as `awsds-infra-sandbox-1` returned 11 connections for
  `eighth-experimentation` and 9 for `test-experimentation`; as `awsds-infra-data` it returns
  *"User is not permitted to perform operation: ListConnections"*. `get-asset` of `dbund4fvvvt05s` is
  refused in Data Governance (0.6, reproduced) and answers in Sandbox. The 6h log records
  `ListConnections` refused to `awsds-infra-sandbox-1` on 2026-09-21 and twice on 2026-10-10.
- **[Claude] What changed is a membership.** Each project lists three members: `PROJECT_OWNER`, the data
  scientist user; `PROJECT_CONTRIBUTOR`, the project's own role, an `IAM` user profile; and
  `PROJECT_CONTRIBUTOR`, a group profile whose `rolePrincipalArn` is the Sandbox `InfrastructureAccess`
  role. Data Governance's trail holds the two `CreateProjectMembership` calls for that group, as
  `awsds-data-studio-domain-execution` with the data scientist user's session name: 06:15:15Z on
  2026-10-15 for `test-experimentation` and 06:15:45Z for `eighth-experimentation`, a portal act. The
  refusals are DataZone's project-membership check, not IAM, and the Data Governance session is still
  not a member. The 6h session was told the same day.

### Decision due 5 — DataZone's half

- **[Claude] The project role is a DataZone user and a contributor of its own project.**
  `search-user-profiles` lists an `IAM` profile, `ACTIVATED`, for each of six `datazone_usr_role_*`
  roles (four belong to deleted projects) and for the `InfrastructureAccess` role of three accounts;
  `list-project-memberships` and `get-user-profile` put the two live project roles at
  `PROJECT_CONTRIBUTOR`.
- **[Claude] AWS's pages put the checks on membership**, read the same day: publishing needs owner or
  contributor and lets the publisher switch approval off; a request needs a project; approving,
  rejecting and revoking need the owning project; a request is approved at creation when the requester
  is owner or contributor of both projects.
- **[Claude] The IAM half, simulated, and the simulator's trap.** `iam simulate-principal-policy` on both
  project roles, with no context key: every action reads `explicitDeny` with
  `AllowedByOrganizations: False`, `glue:GetTable`, `datazone:GetDomain` and `bedrock:InvokeModel`
  among them, because the Region ceiling SCP tests `aws:RequestedRegion` and the key is absent. With
  `aws:RequestedRegion=us-west-2` supplied, `CreateSubscriptionRequest`, `RevokeSubscription`,
  `CreateListingChangeSet` and `CreateAsset` read `allowed` (`SageMakerStudioProjectRoleMachineLearningPolicy`
  v45 matched) and `AcceptSubscriptionRequest`, `RejectSubscriptionRequest`, `CreateSubscriptionGrant` and
  `AddPolicyGrant` read `implicitDeny`. The boundary `awsds-sandbox-project-boundary` v2 holds no
  `datazone:` statement. `SageMakerStudioProjectUserRolePolicy` v75 grants `datazone:PostLineageEvent`
  on the domain by principal tag, and the lineage page puts that write's authorization at IAM alone.
- **[Claude] No call as a project role exists to read.** The trail's `CreateListingChangeSet` (2),
  `CreateAsset` (1) and `CreateDataProduct` (1) are the portal calls of 2026-09-13; none of
  `CreateSubscriptionRequest`, `RevokeSubscription`, `AcceptSubscriptionRequest` and
  `CreateSubscriptionGrant` is in either trail. The call itself is a write from a space, owed with the
  environment up and the user's authorization.

### What the approval page changes for step 2

- **[Claude] A request by a member of both projects is approved at creation.** The two live projects
  share their owner and the `InfrastructureAccess` group, so a request as the data scientist user from
  `test-experimentation` to `house-price` would be approved with nothing to approve, and 2.2 would read
  the auto-approved path. Step 2.1 of the stage file now says so.

### Recorded the same sitting

- **[Claude]** The stage file (status, prerequisites, 0.6, 1.3, 2.1, 5.1, 6.1, 6.2, decisions 3 to 5,
  cost, boundary item 2, 8.1 and the closing list), `GOVERNANCE.md` (the catalog row, the recorded-in
  cell, three sentences that still called 4.1 and decision 1 open or `(d)` recommended), `AWS_STATE.md`
  `EXC-11`, `SMUS.md`'s catalog-surface section, `REFERENCES.md`, `PRICING.md`'s compute row,
  `aws/INDEX.md` and `catalog.py`.

## 2026-10-18 — decision due 3's last input: no condition key reaches business-name generation

*Claude's reading, in the task `stages-06fgh-readings` the orchestrating session ran on the user's
approval of 2026-10-18, with no AWS call: the Service Authorization Reference page for Amazon DataZone and
its machine-readable copy, read with the web fetch tool and paraphrased here, and the DataZone model of
the laptop's CLI, 2.37.12. [`REFERENCES.md`](../REFERENCES.md) lists both sources.*

- **[Claude] The condition keys.** The page defines six: `aws:RequestTag/${TagKey}`,
  `aws:ResourceTag/${TagKey}`, `aws:TagKeys`, `datazone:domainId`, `datazone:projectId` and
  `datazone:userId`, and one resource type, `domain`, with `aws:ResourceTag`. No action row names any of
  the three `datazone:` keys: the action-level keys are the tag keys on `CreateDomain`, `TagResource` and
  `UntagResource`, and `aws:ResourceTag` reaches the domain's own actions through `domain`. The
  machine-readable copy agrees, the three `datazone:` keys in its top-level list and in no action's
  `ActionConditionKeys`.
- **[Claude] The actions that carry the switch.** `CreateAsset`, `CreateAssetRevision`,
  `CreateDataSource`, `UpdateDataSource` and `StartDataSourceRun` take no resource type and no condition
  key. In the CLI model the switch is `--prediction-configuration businessNameGeneration={enabled=…}` on
  `create-asset` and `create-asset-revision`, and `--recommendation enableBusinessNameGeneration=…` on
  `create-data-source` and `update-data-source`.
- **[Claude] The generation's own actions.** `StartMetadataGenerationRun`, `CancelMetadataGenerationRun`,
  `GetMetadataGenerationRun`, `ListMetadataGenerationRuns`, `AcceptPredictions` and `RejectPredictions`
  take no resource type and no condition key. The CLI model gives `start-metadata-generation-run` a
  `--type` or `--types` of `BUSINESS_DESCRIPTIONS`, `BUSINESS_NAMES` or `BUSINESS_GLOSSARY_ASSOCIATIONS`,
  and no key reads it.
- **[Claude] What it leaves for the decision.** An IAM deny reaches generation only as a whole action,
  and no policy reaches the flag. Whether a data source's own run calls any IAM action to generate is not
  on the page. The decision stays the user's; the stage file's decision due 3 carries the reading.

## 2026-10-20 — the manage-access role's Glue policy in the module and applied, and the failed `DataLake` environments read

*Claude, in a session the Stage 18 session started, from the worktree `verificar-ambiente-down-e95914` on
the branch `claude/gifted-thompson-d4f635`, cut from `origin/main` at `fa69fe19`, the pull request
being #207. The requirement came from Stage 18 7.2's entries of the same night, read on PR #203's branch,
where they stay until it merges. AWS reads as the infrastructure user with `InfrastructureAccess` in
`Sandbox Account 1` (`awsds-infra-sandbox-1`), and in `Staging` (`awsds-infra-staging`) for the control
reading; Claude created, changed and deleted nothing in AWS, the one change being the user's apply
below. The first readings ran 02:10 to 02:15 UTC, their times read back from the trails.*

- **[Claude] The two policies** (`iam get-policy-version`). `awsds-sandbox-smus-manage-access` carries
  `AmazonDataZoneSageMakerManageAccessRolePolicy` alone, at v4 (updated 2026-02-12): thirteen statements
  over SageMaker, RAM, S3, ECR and KMS, and no `lakeformation:` action. `AmazonDataZoneGlueManageAccessRolePolicy`,
  v18 (updated 2026-02-12), lives under `service-role/`; its `LakeformationResourceSharing` statement
  grants `CreateLakeFormationOptIn`, `GrantPermissions`, `BatchGrantPermissions`, `RevokePermissions`,
  `RegisterResource` and the data cells filter actions on `*`, and its other statements reach Glue
  databases and tables in the role's own account, RAM shares made through Lake Formation, `iam:PassRole`
  of `datazone_usr_role*` to Lake Formation and Glue, and `kms:Decrypt` on keys tagged
  `datazone:projectId` `proj-all`. Stage 18 measured the pair in Staging the same night (7.2).
- **[Claude] The failed environments** (`datazone list-environments`, `get-environment`). Two, both from
  the `experimentation` profile's `DataLake` configuration (`40631117-4a84-42b1-b2dc-c2deef6c3d52`), both
  `CREATE_FAILED` with `provisionedResources` null and the failure *"Failed to deploy DataLake add-on for
  environment <id>: User: arn:aws:sts::<acct>:assumed-role/awsds-sandbox-smus-manage-access/AmazonDataZoneEnvironmentDeployer-<acct>
  is not authorized to perform: lakeformation:CreateLakeFormationOptIn … because no identity-based policy
  allows the lakeformation:CreateLakeFormationOptIn action"*:
  - `4lrapnc3syxd74`, `create-datalake-database-env-mydatabase-1789263919641`, in `eighth-experimentation`,
    `glueDbName` `mydatabase`, created 2026-09-13 01:45:21Z;
  - `d42fq38p5bkbdc`, `create-datalake-database-env-test-1792044496398`, in `test-experimentation`,
    `glueDbName` `test`, created 2026-10-15 06:08:17Z.

  The name's suffix is the portal's epoch in milliseconds. The domain's other two projects hold none:
  `GenerativeAIModelGovernanceProject`'s six Bedrock environments and `deploy-staging`'s two are `ACTIVE`.
- **[Claude] What each failure left, from Sandbox's trail** (`cloudtrail lookup-events`). 2026-09-13:
  `CreateStack` 01:45:33Z and `CreateDatabase` of `mydatabase` 01:45:38Z, both by the provisioning role
  through `datazone.amazonaws.com`; the manage-access role's `CreateLakeFormationOptIn` refused 01:45:46Z;
  `DeleteStack` 01:46:04Z; no `DeleteDatabase`. `mydatabase` exists, holding `house-price`. 2026-10-15: the
  same sequence for `test` (06:08:29 to 06:09:00Z), then `DeleteDatabase` of `test` at 06:08:58Z by
  `test-experimentation`'s project role from the laptop's address, as the portal acts; `get-database`
  answers `EntityNotFoundException`. Both stacks, `DataZone-Env-<id>`, read `DELETE_COMPLETE`.
- **[Claude] Whether deleting a failed environment takes its database, read in Staging.** Stage 18 7.2's
  failed `c2ej62w956q2a8` followed the same sequence (`CreateDatabase` of `glue_db_c2ej62w956q2a8`
  01:39:36Z, the opt-in refused 01:39:46Z, `DeleteStack` 01:40:04Z); its `DeleteEnvironment` at 02:01:00Z
  was followed by a second `DeleteStack` at 02:01:12Z and no `DeleteDatabase` through 02:06Z.
  `glue get-database` as the infrastructure user, no Lake Formation administrator there, answers
  *"Insufficient Lake Formation permission(s): Required Describe on glue_db_c2ej62w956q2a8"*, the same as
  for the `ACTIVE` environment's `glue_db_d6ogysnx78dguo`, and `EntityNotFoundException` for a name that
  does not exist: the database outlived both the failure and the deletion. A `get-databases` listing as
  that user shows neither (Lesson 62).
- **[Claude] Where a Glue subscription lands** (`datazone list-subscription-targets`). Each `Tooling`
  environment, in both Sandbox projects and in `deploy-staging`, carries two targets: one for
  `BedrockModelAssetType`, and `Tooling-default-target` for `SageMakerFeatureGroupAssetType` and
  `SageMakerModelPackageGroupAssetType`. Staging's `ACTIVE` `DataLake` environment carries
  `deploy-staging-lakehouse-default-target` for `GlueTableAssetType` and `GlueViewAssetType`. No Sandbox
  project holds a target for a Glue table, so 2.2's subscription to `house-price` has nowhere to land
  until the consumer project holds an `ACTIVE` `DataLake` environment.
- **[Claude] What a new environment adds**, read from Staging's: a database `glue_db_<environment id>`
  under the project's `dev/data/catalogs/`, the project-conditioned grants, and a Glue data source over
  that database alone, `cron(2 2 * * ? *)`, `publishOnImport` false, business-name generation off, its
  data access role the project role.
- **[Claude] The module change**, `terraform-modules/sagemaker-prereqs/roles.tf`: the Glue policy's ARN,
  with its `service-role/` path, added to `module "manage_access_role"`'s `managed_policy_arns`, and
  `blueprints.tf`'s comment that called the SageMaker policy the role's one policy corrected. `validate`
  passed. Planned from `sandbox/sagemaker/` against the local module (Recipe B step 1), 02:17:49 to
  02:18:20Z: *"Plan: 1 to add, 0 to change, 0 to destroy."*, the one resource
  `module.sagemaker_prereqs.module.manage_access_role.aws_iam_role_policy_attachment.managed["arn:aws:iam::aws:policy/service-role/AmazonDataZoneGlueManageAccessRolePolicy"]`.
  That plan was deleted unapplied, and the caller re-pinned to `v0.7.0` and re-initialised. The module
  committed at 02:19:10Z and tagged `sagemaker-prereqs-v0.8.0`, the next version read from
  `git ls-remote --tags origin` at tagging, `v0.7.0` the newest there.
- **[Claude] The push refused**: `git push` of the branch with the tag, and of the branch alone, both
  refused by the app's auto-mode classifier (*Out-of-Place Publication*). The caller's bump, its saved
  plan and the pull request wait on the tag reaching origin.
- **[Claude] Decision due 6 written** in the stage file, with step 2.0 before 2.2: the two environments'
  handling, the user's.
- **[Claude] Recorded the same sitting**, committed at 02:28:02Z: the stage file's step 2.0 and decision
  due 6; `SMUS.md` (the manage-access seat, the portal's *Create database*, the `DataLake` row);
  `INT-23`; open question 24's amendment; a platform bullet in `lessons.md`; `waiting-on-the-user.md`;
  `CLAUDE.md`'s 6f and Module tags bullets; the 6f rows of `GENERAL_PLAN.md`, `stages/INDEX.md` and
  `log/INDEX.md`.
- **[Claude] Handed to the Stage 18 session** through the shared notes folder: Staging's
  `glue_db_c2ej62w956q2a8` outlived its environment, 7.2's "no Glue database" having come from a
  listing Lake Formation filters; a later bump of `staging/studio/` past `v0.6.0` deletes its
  `manage-access.tf` in the same change, with a `moved` block to the module's attachment; and PR #203's
  `lessons.md` entry, which exists only on that branch, can point at `sagemaker-prereqs-v0.8.0`.
- **[user] The push authorized** in this session's chat: *"Autorizo o push do branch
  claude/gifted-thompson-d4f635 e da tag sagemaker-prereqs-v0.8.0 para origin. Depois siga com o bump do
  sandbox/sagemaker, o plan salvo e o PR."*
- **[Claude] Pushed**, the branch and the tag; `git ls-remote --tags origin sagemaker-prereqs-v0.8.0`
  answers `d9bfba01ba333ba5d10a8fb4b96041ca9f9b74e6`, the tagged commit.
- **[Claude] The caller bumped and planned**: `sandbox/sagemaker/main.tf` pins
  `sagemaker-prereqs-v0.8.0`, `init` fetched it from origin, and the plan as `awsds-infra-sandbox-1`,
  02:31:23 to 02:31:53Z, reads *"Plan: 1 to add, 0 to change, 0 to destroy."*, the same attachment as the
  local plan. Saved to `$HOME/tmp/s6f-sagemaker-prereqs-v080.tfplan` for the user's apply (step 2.0).
- **[Claude] The pull request**, #207, opened at 02:33:48Z with the module commit (02:19:10Z), the
  records (02:28:02Z) and the caller's bump (02:32:18Z); `make check` and `make check-docs` read `OK`,
  and every commit passed the hooks.
- **[user] 2.0's apply**, from the project folder on `main`, of the saved plan, as `awsds-infra-sandbox-1`:
  *"module.sagemaker_prereqs.module.manage_access_role.aws_iam_role_policy_attachment.managed["arn:aws:iam::aws:policy/service-role/AmazonDataZoneGlueManageAccessRolePolicy"]:
  Creation complete after 1s
  [id=awsds-sandbox-smus-manage-access/arn:aws:iam::aws:policy/service-role/AmazonDataZoneGlueManageAccessRolePolicy]"*,
  *"Apply complete! Resources: 1 added, 0 changed, 0 destroyed."*
- **[Claude] Read back.** The trail's `AttachRolePolicy` of the Glue policy on
  `awsds-sandbox-smus-manage-access`, by the `InfrastructureAccess` session, at 02:38:53Z; a lookup at
  02:40Z had not yet listed it (Lesson 62). The re-plan from this branch, 02:39:51 to 02:40:21Z, reads
  *"No changes. Your infrastructure matches the configuration."* (`-detailed-exitcode` 0), and
  `list-attached-role-policies` lists the Glue and the SageMaker manage-access policies. `main` still pins
  `v0.7.0`, so a plan of the slice from `main` would detach the policy until this branch merges.
- **[Claude] `./aws/catalog.py`**, 02:40:44 to 02:41:34Z: *"all checks passed"*. `CT-7` *"14 SMUS grants,
  all on project-owned objects"*, the count of 2026-10-18; `CT-8` *"all 7 carry context.datazone.projectId"*;
  `CT-4` all four data sources `publishOnImport` false; `CT-5` notes `mydatabase`'s data source, business-name
  generation on (decision due 3). No grant changed with the attachment: DataZone has not asked the role
  to act since.
- **[Claude] `mydatabase`'s data source**, for decision due 6: `6kk4bknmo46o0g`, created 2026-09-13
  04:06:38Z at the publish, on the connection `project.default_lakehouse` (`LAKEHOUSE`), whose environment
  is the project's `Tooling` (`5hkjdsy3umpi1c`), not the failed `4lrapnc3syxd74`.
- **[Claude] Recorded and pushed** at 02:42:50Z: the apply's date in the stage file, `SMUS.md`, `INT-23`,
  open question 24, `AWS_STATE.md` (the manage-access role's two policies), `CLAUDE.md` and the indexes;
  `waiting-on-the-user.md` lost the apply's row and gained PR #207's merge, since `main` pins `v0.7.0`.

## 2026-10-20 — decision due 6 taken, `test-experimentation`'s `DataLake` environment created

*Claude, in the same session and worktree, AWS as the infrastructure user with `InfrastructureAccess` in
`Sandbox Account 1` (`awsds-infra-sandbox-1`). The two writes below are `datazone delete-environment`
and `create-environment`, run on the user's decision; the Stage 18 session was told first, and no other
session on the laptop was running. Times are UTC.*

- **[user] Decision due 6**, after asking for its context: *"Vamos seguir sua recomendação ajustada"*,
  the adjusted recommendation being to delete `test-experimentation`'s failed record and create its
  `DataLake` environment now, and to leave `eighth-experimentation`'s record until step 2 ends.
- **[Claude] The Stage 18 session told**, before the writes: the two DataZone writes in Sandbox, nothing
  in Staging touched, and `main`'s `v0.7.0` pin on `sandbox/sagemaker/` until PR #207 merges.
- **[Claude] Before**, 02:49:45Z: `test-experimentation` holds `Tooling` `ACTIVE` and `d42fq38p5bkbdc`
  `CREATE_FAILED`; Lake Formation's administrators are the manage-access role, `InfrastructureAccess` and
  the provisioning role, both create-defaults empty, `Parameters` 4/`TRUE`; two registered locations, the
  projects' `dev/` prefixes; Glue lists `curated`, `default`, `mydatabase` and `raw`. Sandbox's `DataLake`
  configuration names blueprint `d8w7c3fmbsz5cg` and the manage-access role.
- **[Claude⚡] The failed record deleted**: `delete-environment` of `d42fq38p5bkbdc` at 02:50:03Z, exit 0;
  `DELETING` at 02:50:11Z and not found at 02:50:30Z. The trail: `DeleteEnvironment` 02:50:05Z, then a
  `DeleteStack` of the already deleted `DataZone-Env-d42fq38p5bkbdc` by the provisioning role at
  02:50:17Z, and no `DeleteDatabase`.
- **[Claude⚡] The environment created**: `create-environment` at 02:50:55Z with the `experimentation`
  profile's `DataLake` configuration (`40631117-4a84-42b1-b2dc-c2deef6c3d52`, blueprint `d8w7c3fmbsz5cg`),
  name `test-experimentation-lakehouse`, no user parameter: `4zojr4rr6bmnww` `CREATING`, and `ACTIVE` at
  02:51:33Z, 37 s after its creation, `lastDeployment` `SUCCESSFUL`.
- **[Claude] What it holds.** `provisionedResources`: `glueDBName` `glue_db_4zojr4rr6bmnww`,
  `glueOutputUri` `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/4gqfau9xuo6e4w/dev/data/catalogs/`,
  `userRoleArn` the project role, and the stack `DataZone-Env-4zojr4rr6bmnww` (`CREATE_COMPLETE`
  02:51:08Z), one resource, `GlueDatabase`. Its template, `DataZone-Amazon-SageMaker-DataLakeDefault-prod-20250618`,
  declares that database and an Athena workgroup this stack did not create, both with `DeletionPolicy`
  and `UpdateReplacePolicy` `Retain`: why every failed environment's database outlived its stack. The
  subscription target `test-experimentation-lakehouse-default-target` serves `GlueTableAssetType` and
  `GlueViewAssetType`, its `manageAccessRole` the project role. The Glue data source `3zp6fog9jep1qo`, on
  `project.default_lakehouse` (the `Tooling` environment's connection), covers the new database alone,
  `cron(51 2 * * ? *)`, the minute of its creation, `publishOnImport` false, business-name generation off,
  data quality import on, its data access role the project role.
- **[Claude] The grants, from the trail**, 02:51:13 to 02:51:24Z: `CreateDatabase` of
  `glue_db_4zojr4rr6bmnww` by the provisioning role; its `BatchGrantPermissions` to `<acct>:IAMPrincipals`
  and `arn:aws:identitystore:::user/*`, each under `context.datazone.projectId=="4gqfau9xuo6e4w"`,
  `CREATE_TABLE`, `DESCRIBE` and `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`,
  `INSERT` and `SELECT` on its tables; its three `GrantPermissions` to the manage-access role,
  grantable `DESCRIBE` and `CREATE_TABLE` on the database and grantable `DESCRIBE` and `SELECT` on its
  tables. Then the manage-access role's `CreateLakeFormationOptIn` for the conditioned `IAMPrincipals` on
  the database, **passing**, its first call allowed in Sandbox, and its `RevokePermissions` of `ALL` from
  `IAM_ALLOWED_PRINCIPALS`, *"InvalidInputException"*, nothing to revoke under empty defaults. Last, the
  provisioning role's `TagResource` of the database with the four `AmazonDataZone*` tags. Staging's 7.2
  pattern, call for call, without its refused `UntagResource`.
- **[Claude] Lake Formation after**: the same three administrators, empty create-defaults, `Parameters`
  4/`TRUE`, two registered locations. The administrators came back in another order, and three more reads
  gave two orders with no `PutDataLakeSettings` in the trail since 2026-10-15: the list is unordered.
- **[Claude] `./aws/catalog.py`**, 02:53:44 to 02:54:43Z: *"all checks passed"*. `CT-7` *"21 SMUS grants,
  all on project-owned objects"*, the seven new ones on `glue_db_4zojr4rr6bmnww` (the provisioning role's
  creator grant among them); `CT-8` *"all 10 carry context.datazone.projectId"*; `CT-4` *"all 5 carry
  publishOnImport false"*; `CT-5` and `CT-6` note what they noted at 02:40Z, the new source not yet run.
- **[Claude] `./aws/datalake.py`**, 02:54:43 to 02:56:01Z: *"wrote aws/output/datalake.txt (some calls FAILED
  - see section 14)"*, exit 1. Section 14 holds seven `sts get-caller-identity` calls of the Control Tower,
  deploy, dev-env, governance and scientist profiles, whose SSO sessions were not signed in. Every check
  passes or notes: `DL-13` in Sandbox the required seat and the two SMUS seats, `DL-14` the two projects'
  `dev/` registrations, `DL-5` and `DL-6` passing in Sandbox.
- **[Claude] What 2.0 leaves for step 2**: `test-experimentation`, 2.1's recommended consumer, holds the
  Glue subscription target 2.2 needs; `eighth-experimentation` holds `house-price` and its failed record,
  whose deletion is 2.7.
- **[Claude] Recorded and pushed** at 02:56:35Z: decision due 6 taken and 2.7 in the stage file;
  `AWS_STATE.md` (the environment in the SMUS row, `CT-7` at 21); `SMUS.md` (the template's `Retain`, the
  seat's first calls); `INT-23`; open question 24; `lessons.md` (the database the template keeps, and the
  administrators' unordered list); `waiting-on-the-user.md` lost decision due 6's row; `CLAUDE.md` and the
  indexes. The Stage 18 session's note gained the template's `Retain`: Staging's two `DataLake` databases
  stay unless its unwinding deletes them by name.

## 2026-10-20 — the stage's remaining steps re-read against the session

*Claude, the same session, at the user's request; no AWS call. The reading of `CT-6` is
`aws/catalog.py`'s code.*

- **[user] The request**: *"Confira se o PR #207 tem no log todo o andamento desta sessão. Revise o plano
  das etapas que faltam deste estágio do plano considerando o andamento desta sessão e faça as correções
  necessárias. Revise novamente o log em relação ao andamento desta sessão e suba as alterações no PR."*
- **[Claude] The stage file corrected**:
  - the AWS writes carry `[Claude⚡]`, as "Who executes each action" defines it: 2.0's deletion and
    creation, and 2.7;
  - section 0: 0.1 names the `DataLake` environment behind a portal database, 0.9 the Glue subscription
    target, 0.10 the manage-access role acting in Lake Formation and the template's `Retain`;
  - 2.0 keeps one reading: the new data source's first run, 2026-10-21 at 02:51 UTC. `CT-6` fails on a
    scheduled source whose completed runs all failed unless `FAILING_BY_EXCEPTION` names it, and only
    `EXC-11`'s `Tooling` source is named; the run lists the database as the project role, whose
    conditioned grants need `context.datazone.projectId` on that session, unmeasured;
  - 2.1: a new consumer project needs its own `DataLake` environment; 2.2: the two Sandbox roles that can
    write the grant, and whether the subscribed table lands in `glue_db_4zojr4rr6bmnww`;
  - 3.1 (a) and decision due 1: the manage-access role holds the IAM half of the grants since
    2026-10-20, and Sandbox's TBAC shares carry the grant option, so under (c) the lake stays out of the
    catalog because nothing publishes it or points a data source at its resource links, which `CT-7`
    reads;
  - 5.1 and decision due 3: a `DataLake` environment's source arrives with generation off; decision due
    6: its execution; 10.2: each database a clean-up deletes by name;
  - Cost: a data source run is ingestion, billed in compute units per completed job (`PRICING.md` §5),
    which corrects the line of 02:28Z that counted requests alone; `SMUS.md`'s `DataLake` row and
    `AWS_STATE.md` carry the same.
- **[Claude] The log re-read against the session**: the two writes marked `[Claude⚡]`; the first entry's
  heading and provenance corrected, the user's apply being part of it; the pull request, the records,
  the checks and the hand-over to the Stage 18 session added to both entries.

## 2026-10-26 — decision due 1 taken as (b), and the pilot written and planned

*Claude, in a session started from another session with the user's decision relayed; AWS read as the
infrastructure user with `InfrastructureAccess` in `Data Governance Account` (`awsds-infra-data`) and
`Sandbox Account 1` (`awsds-infra-sandbox-1`), reads and `terraform plan` alone, and one write the user
authorized in this session's chat: the release of a state lock this session's plan had left. Times UTC.*

- **[user] Decision due 1**, relayed: shape (b), as a pilot, for SageMaker Unified Studio's native flow,
  subscription and approval in the portal granting and DataZone fulfilling, with no Terraform apply per
  grant; one `internal` table, `curated.trades`, published by a project in `Data Governance` and
  subscribed by `eighth-experimentation`, read before anything widens. The complement, in the user's
  words: *"vamos priorizar a solução nativa do SMUS, mesmo que isso implique em não utilizar as LF-TAGS"*.
- **[Claude] The lake account before**, read before 19:00Z: no VPC (`describe-vpcs` `[]`); zero blueprint
  configurations; the Data Catalog resource policy *"Policy not found"*; Lake Formation's administrators
  the `InfrastructureAccess` seat alone, `Parameters` 4/`TRUE`, `AllowFullTableExternalDataAccess` `true`
  since 2026-10-23 (Stage 9 decision 13, so the brief's "unset" was a reading from before that date),
  both default lists empty; the RAM shares it owns all `LakeFormation-V4-*`. The first `glue` call failed
  on the laptop's proxy and passed with `NO_PROXY='*'`.
- **[Claude] The two templates**, read with signed `s3 cp` from the blueprints' `templateUrl` (an unsigned
  `curl` is refused for SigV4): `ToolingDefault-prod-20260918` takes `vpcId`, `subnets` and
  `availabilityZones` with no default, creates `ToolingSecurityGroup` in the VPC unless
  `vpcConnectionSecurityGroup` is passed, and Glue network connections while `enableGlueNetworkConnection`
  is `true`, neither of them a user parameter; the project role reads `vpcId` in two tags alone; and
  `LakeFormationResourceToRegisterProjectsS3Location` carries no `DeletionPolicy`.
  `DataLakeDefault-prod-20250618` imports `s3BucketPath-<project>-<scope>`, which only the same account's
  Tooling stack exports. So shape (b) needs a VPC in `Data Governance`, and a project deleted there calls
  `lakeformation:DeregisterResource`, which the Data OU's `DenyLakeDeletionAndDeregistration` denies to
  every principal.
- **[Claude] The code** (the stage's step 11.1): `data-governance/publishing/`, a new `[P]` slice at rank
  46 holding the VPC `10.70.0.0/16` through `vpc-v0.4.0` with `public_internet_route = false` and no
  peering, its flow-log role, and `sagemaker-prereqs-v0.8.0` with `Tooling` alone; `governance/`'s
  profile `lake-publishing` and its create grant to `sso-group-governance-managers`; `data/`'s two SMUS
  seats and the publisher's grant (`publishing.tf`); `backend.py`'s `LAKE_PUBLISHERS`, its `VPC_CIDRS` and
  `ZONE_IDS` rows and the `publishing` emission; `layers.py`'s rank and row. The instruments with it:
  `US-3` and `US-4` (`studio.py`), `CT-7` (`catalog.py`), the projects bucket out of `DL-1` and `DL-2` and
  `DL-13`'s reason in the lake (`datalake.py`), `NT-1` (`networking.py`), `egress.py`'s text.
- **[Claude] The plans**, as `awsds-infra-data`, saved under the session's scratchpad. The switch off:
  `publishing/` *"Plan: 44 to add, 0 to change, 0 to destroy."*, `governance/` and `data/` *"No changes."*
  The switch on in the working copy, then restored and the tfvars regenerated: `publishing/` *"Plan: 46 to
  add, 0 to change, 0 to destroy."*; `governance/` *"Plan: 2 to add, 0 to change, 0 to destroy."*, the
  profile with `experimentation`'s six Tooling overrides and `enableSpaces` `false` locked, and its
  grant; `data/` refused at plan, *"reading IAM Role (awsds-data-smus-manage-access): couldn't find
  resource"* and the same for the provisioning role, the refusal the lookups exist for before 11.2.
- **[Claude] A lock left by a plan.** The first switch-on run lost DNS mid-plan (*"dial tcp: lookup
  cloudcontrolapi.us-west-2.amazonaws.com: no such host"*) and could not release `governance/`'s lock:
  the object `data-governance/governance/terraform.tfstate.tflock` read `Operation` `OperationTypePlan`,
  created 19:04:26Z by this run, with the four other sessions on the laptop idle.
- **[user]** Asked whether to release it, against `CLAUDE.md`'s rule on `force-unlock`: *"Sim, libere"*.
- **[Claude⚡] The lock released** at 19:22Z, `terraform force-unlock -force` on that lock's id as
  `awsds-infra-data`, and the object read gone; both switch-on plans re-run after, leaving no lock on
  `governance/` or `data/`.
- **[Claude] The instruments on today's estate**, with the amended checks: `./aws/catalog.py` *"all checks
  passed"*; `./aws/studio.py`'s checks all pass, `US-3` *"no blueprint configured in the domain account"*
  and `US-4` the two contracted profiles, its exit 1 from the sign-in of profiles other than the
  infrastructure user's; `./aws/datalake.py` no failure, `DL-1` and `DL-2` on the five lake buckets,
  `DL-5`, `DL-6` and `DL-7` passing, `DL-13` the lake's `InfrastructureAccess` seat alone;
  `./aws/networking.py` no failure, with no `NT-1` row, Data Governance holding no VPC. Both exit 1 on
  the same unsigned profiles.
- **[Claude] Recorded**: the stage file (status, decision 1 taken, decisions 2 to 5, step 11, the
  verifications x to xiii, 3.3 and 7.2, the cost); D22 and D26 amended, and D22's index row;
  `GOVERNANCE.md` (§Grants' catalog road, §Access control, the accounts and catalogs tables, the
  development cycle); Stage 11 decision 12 re-read; `SMUS.md`; `NETWORK.md`; conventions §6;
  `AWS_STATE.md` section C; `TM-27`; the producer README; `terraform-live/README.md`; `ORGANIZATION.md`.

## 2026-10-26 — 11.2: `data-governance/publishing/` applied

*Claude, the same session; AWS as the infrastructure user with `InfrastructureAccess` in `Data Governance
Account` (`awsds-infra-data`). The apply is Claude's, on the user's word below; the four other sessions on
the laptop were told first. Times UTC.*

- **[user]** *"Autorizo o 11.2: apply de data-governance/publishing/ com LAKE_PUBLISHERS vazio, como
  infrastructure user, conta Data Governance, InfrastructureAccess (awsds-infra-data), aceitando a VPC
  10.70.0.0/16."*
- **[Claude] The other sessions told** before the apply, each message delivered to its inbox: "Pendências
  estágios 7-10" (busy), "Chat lateral", "Worktrees para apagar" and "CI/CD CLI remedy" (idle).
- **[Claude] The plan**, 20:05:10Z, with `LAKE_PUBLISHERS` empty and `blueprints_enabled = false` in the
  regenerated tfvars: *"Plan: 44 to add, 0 to change, 0 to destroy."*, saved.
- **[Claude⚡] The apply** of the saved plan, 20:05:22Z to 20:06:53Z: *"Apply complete! Resources: 44
  added, 0 changed, 0 destroyed."* The re-plan at 20:07:29Z: *"No changes."* `data/` at 20:10:46Z and
  `governance/` at 20:11:25Z re-plan *"No changes."*, and no lock is left on any of the three states.
- **[Claude] Read back**, 20:07 to 20:08Z: `vpc-01b526900ef0ef311`, `10.70.0.0/16`, named
  `awsds-data-vpc`, not default; six subnets, private `10.70.0.0/18` and `10.70.64.0/18`, isolated
  `10.70.128.0/20` and `10.70.144.0/20`, public `10.70.160.0/24` and `10.70.161.0/24`, in `usw2-az1` and
  `usw2-az2`, none mapping a public address; every route table carrying the S3 and DynamoDB prefix lists
  alone, no `0.0.0.0/0`; the internet gateway attached and unrouted; both gateway endpoints `available`;
  the flow log `ACTIVE`, `ALL` traffic, into `awsds-data-vpc-flow-logs`; zero peerings. The roles, created
  20:05:31Z: `awsds-data-smus-provisioning` trusting `datazone.amazonaws.com` and
  `cloudformation.amazonaws.com` under `aws:SourceAccount` this account, with
  `SageMakerStudioProjectProvisioningRolePolicy`; `awsds-data-smus-manage-access` trusting
  `datazone.amazonaws.com` the same way, with the SageMaker and Glue manage-access policies;
  `awsds-data-vpc-flow-logs` trusting `vpc-flow-logs.amazonaws.com`. The boundary
  `awsds-data-project-boundary` at `v1`; `alias/awsds-data-project` `Enabled`, customer-managed;
  `awsds-data-smus-projects` versioned, all four public-access blocks on, `aws:kms` with the Bucket Key;
  `/awsds/data/studio` and `awsds-data-vpc-flow-logs` at 30 days. Unchanged: Lake Formation's settings,
  the `InfrastructureAccess` seat alone with 4/`TRUE`, the full-table flag `true` and both default lists
  empty; zero blueprint configurations.
- **[Claude] `./aws/datalake.py`**, done 20:09:54Z: no failure; `DL-1` and `DL-2` on the five lake buckets,
  `awsds-data-smus-projects` left out; `DL-7` nine shares out; `DL-13` the lake's seat alone. Exit 1 on the
  unsigned profiles, as before.

## 2026-10-26 — 11.3: the switch, and `data/`, `publishing/` and `governance/` applied

*Claude, the same session; AWS as the infrastructure user with `InfrastructureAccess` in `Data Governance
Account` (`awsds-infra-data`), and the directory read through `awsds-infra-identity`. The three applies are
Claude's, on the user's word below; the four other sessions on the laptop were told first. Times UTC.*

- **[user]** *"Autorizo o 11.3: LAKE_PUBLISHERS = ["data-governance"] e os três applies na ordem data/,
  publishing/, governance/, como infrastructure user, conta Data Governance, InfrastructureAccess
  (awsds-infra-data)."*
- **[Claude] 11.2's last instruments**, which finished as this step began: `./aws/networking.py` at
  20:14:25Z, no failure, `NT-1` a note on `vpc-01b526900ef0ef311` (`10.70.0.0/16`, the pilot's), `NT-5`
  six VPCs with no overlap, `NT-7` its flow log present; `./aws/studio.py` at 20:16:48Z, before the
  configuration existed, `US-2` no SageMaker domain in Data Governance and `US-3` no configuration
  there; `./aws/egress.py` at 20:17:54Z, no failure, `EG-1` the organization condition on both new
  gateway endpoints and `EG-4` the AWS-owned bucket allow on the S3 one. Each exits 1 on the unsigned
  profiles alone.
- **[Claude] The other sessions told** before the first apply, each message delivered: "Pendências estágios
  7-10" and "CI/CD CLI remedy" (busy), "Chat lateral" and "Worktrees para apagar" (idle).
- **[Claude] The switch**: `LAKE_PUBLISHERS = ["data-governance"]` in `backend.py`, the three tfvars
  regenerated: `lake_publishing_enabled = true` for `data/` and `governance/`, `blueprints_enabled = true`
  for `publishing/`.
- **[Claude⚡] `data/`**. Lake Formation before, 20:15:41Z: the `InfrastructureAccess` seat alone,
  `Parameters` 4/`TRUE`, the flag `true`, both default lists empty. The plan, 20:16:04Z: *"Plan: 0 to add,
  1 to change, 0 to destroy."*, `aws_lakeformation_data_lake_settings.this` with `admins` gaining
  `awsds-data-smus-manage-access` and `awsds-data-smus-provisioning` and *"(8 unchanged attributes
  hidden)"*. The apply, 20:16:21Z to 20:16:33Z: *"Apply complete! Resources: 0 added, 1 changed, 0
  destroyed."* The re-plan at 20:16:54Z: *"No changes."* Lake Formation after: the three seats,
  `Parameters` 4/`TRUE`, the flag `true`, both default lists empty.
- **[Claude⚡] `publishing/`**. The plan, 20:17:23Z: *"Plan: 2 to add, 1 to change, 0 to destroy."*: the
  `Tooling` configuration, its `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant, and the project key's policy
  gaining `awsds-data-studio-domain-execution` in two statements and the project-role statements
  (`GrantKMSPermissionsForAllProjectRoles` and its `kms:CreateGrant` sibling). The apply, 20:17:37Z to
  20:18:17Z: *"Apply complete! Resources: 2 added, 1 changed, 0 destroyed."* The re-plan at 20:18:37Z:
  *"No changes."*
- **[Claude⚡] `governance/`**. The plan, 20:19:20Z: *"Plan: 2 to add, 0 to change, 0 to destroy."*, the
  profile and its grant, nothing of `experimentation` destroyed. The apply, 20:19:31Z to 20:20:04Z: *"Apply
  complete! Resources: 2 added, 0 changed, 0 destroyed."* The re-plan at 20:20:36Z: *"No changes."*
- **[Claude] Read back**, from 20:20:50Z: the `Tooling` configuration (blueprint `4k186sfh08eqxc`),
  created 20:18:00Z, `us-west-2`, the boundary `awsds-data-project-boundary`, the two roles, and the
  regional parameters `AZs`, `KmsKeyArn`, `S3Location`, `Subnets`, `VpcId`; its grant to `CONTRIBUTOR`
  projects of the root domain unit `bzq0cbh2gd0f4g`, child units excluded; three profiles `ENABLED`, the
  model governance one, `experimentation` and `lake-publishing` (`cc45618tw9f7yo`), the last with `Tooling`
  `ON_CREATE` at order 0 in this account and `us-west-2`, and the overrides `sagemakerDomainNetworkType`
  `VpcOnly`, `lifecycleManagement` `ENABLED`, `idleTimeoutInMinutes` 60 (editable),
  `maxIdleTimeoutInMinutes` 120, `maxEbsVolumeSize` 100, `enableTrustedIdentityPropagationPermissions`
  `false` and `enableSpaces` `false`; on the root unit, `CREATE_PROJECT_FROM_PROJECT_PROFILE` for
  `lake-publishing` to the group the directory names `sso-group-governance-managers`, and for
  `experimentation` to `sso-group-data-scientists`, as before.
- **[Claude] The trail**: one `PutDataLakeSettings` in the lake since 20:00Z, at 20:16:31Z, the apply's, by
  the infrastructure user's session. The project key's policy holds nine statements, as Staging's did at
  Stage 18 2.5.
- **[Claude] The instruments after the three applies**: `./aws/studio.py` at 20:23:10Z, no failure, `US-3`
  a note on `Tooling`, the pilot's, and `US-4` passing with `lake-publishing`, `US-2` no SageMaker domain
  in Data Governance; `./aws/datalake.py` at 20:24:36Z, no failure, `DL-5` 4/`TRUE` and `DL-6` passing in
  the lake, `DL-13` a note on its required seat and the two SMUS seats, declared; `./aws/catalog.py` at
  20:25:42Z, *"all checks passed"*, `CT-7` 21 SMUS grants, all on project-owned objects, `CT-8` and `CT-9`
  passing. `studio.py` and `datalake.py` exit 1 on the unsigned profiles alone.
- **[Claude] Recorded**: the switch row in `backend.py`; the stage file (status, 11.3 done); `AWS_STATE.md`
  (the lake's three administrators, section C's row); `SMUS.md`; `GOVERNANCE.md`; conventions §6; D22; the
  producer README; the hand-over note.

## 2026-10-26 — 11.4: `governed-lake` created by the Governance Manager, and what its environment wrote

*The user in the portal as the Governance Manager user; Claude read AWS as the infrastructure user with
`InfrastructureAccess` in `Data Governance Account` (`awsds-infra-data`), reads alone. Times UTC.*

- **[user] The project**, in the portal as the Governance Manager user: `governed-lake` from
  `lake-publishing`. Then: *"Criei o projeto. Mas não sei qual Data Governance InfrastructureAccess é para
  adicionar. Aparecem os nomes com códigos, então não consigo saber qual é."*
- **[Claude] Which role**: the domain's `IAM` user profiles mapped to their accounts by ARN. Data
  Governance's `InfrastructureAccess` is `AWSReservedSSO_InfrastructureAccess_ba1899ccb658ab35` (profile
  `9e7cfd86-4ddb-4ea1-b43f-04417861d609`); `…_59e5b26af457128d` is Sandbox's and `…_7edd72025c361e9b`
  Staging's, a residue of Stage 18.
- **[user]** *"Adicionei AWSReservedSSO_InfrastructureAccess_ba1899ccb658ab35 no projeto"*.
- **[Claude] The project**: `3j4l4xmvz7fggg`, `ACTIVE`, created 20:30:00Z by an `SSO` profile, the Governance
  Manager user's; its stack `DataZone-Env-52webn93119ouo` started 20:30:14Z and `CREATE_COMPLETE`; the
  environment `Tooling` `52webn93119ouo` `ACTIVE`. Members: the Governance Manager as `PROJECT_OWNER`;
  the project role's `IAM` profile and the session group of Data Governance's `InfrastructureAccess`
  (`ASSIGNED`, the user's addition) as `PROJECT_CONTRIBUTOR`.
- **[Claude] The stack**, thirteen resources as Staging's at Stage 18 3.3: `ToolingUserRole`
  (`datazone_usr_role_3j4l4xmvz7fggg_52webn93119ouo`), `BedrockServiceRole` and
  `BedrockLambdaExecutionRole`, all three under `awsds-data-project-boundary`; `ToolingSecurityGroup` and
  its ingress rule; `GlueNetworkConnection0` and `1`; two Athena workgroups; the log group; the schedule
  group; `LakeFormationResourceToRegisterProjectsS3Location`; the CDK metadata. Its parameters: the pilot's
  VPC and its two private subnets, `enableSpaces` `false`, `enableAthena` `true`,
  `enableS3AccessGrantsForTools` `true`, the boundary, the projects bucket. No SageMaker AI domain.
- **[Claude] Outside the stack**: the S3 Access Grants instance `default`, created 20:31:21Z by DataZone's
  environment deployer session, with one location, the project's prefix, under the project role;
  `AWSServiceRoleForAmazonAthena`, created 20:30:53Z; nine connections in the project, `project.iam` and
  `project.default_lakehouse` among them; no data source, as Staging's project had none; two subscription
  targets on the `Tooling` environment, for Bedrock models and for feature groups and model package groups,
  none for Glue tables.
- **[Claude] Lake Formation and Glue, from the trail** (20:29 to 20:45Z), every write the provisioning
  role's: `CreateConnection` twice at 20:30:34Z; `RegisterResource` of
  `awsds-data-smus-projects/dzd-d8yrvx1ko7im6o/3j4l4xmvz7fggg/dev/` under the project role at 20:30:53Z;
  `CreateDatabase` of `default` in the lake's catalog at 20:31:21Z, no location and no create-table
  default; `BatchGrantPermissions` at 20:31:22Z, `DESCRIBE` on `default` and `DATA_LOCATION_ACCESS` on the
  project's `dev/` to `IAMPrincipals` and `arn:aws:identitystore:::user/*`, each under
  `context.datazone.projectId=="3j4l4xmvz7fggg"`. The creator's `ALL` on `default` is the provisioning
  role's. No `PutDataLakeSettings` since 20:17Z: with both seats declared, the provisioning wrote no
  settings. Neither seat granted anything on `raw`, `curated` or `dropbox`.
- **[Claude] The settings and the plan after**, 20:34Z: Lake Formation unchanged, the three seats,
  `Parameters` 4/`TRUE`, the flag `true`, both default lists and the read-only administrators empty;
  `data/` re-plans *"No changes."*. Verification x is answered: the first environment changed no setting
  `data/` declares and granted nothing on the lake.

## 2026-10-26 — 11.5: the publisher's grant applied

*Claude, the same session; AWS as the infrastructure user with `InfrastructureAccess` in `Data Governance
Account` (`awsds-infra-data`). The apply is Claude's, on the user's word below; the four other sessions on
the laptop were told first. Times UTC.*

- **[user]** *"Autorizo o 11.5: apply de data-governance/data/ com o grant do publicador (DESCRIBE em
  curated; DESCRIBE e SELECT com grant option em trades) ao papel do governed-lake, como infrastructure
  user, conta Data Governance, InfrastructureAccess (awsds-infra-data)."*
- **[Claude] The other sessions told**, each message delivered: "Pendências estágios 7-10", "Chat lateral"
  and "Worktrees para apagar" (idle), "CI/CD CLI remedy" (busy).
- **[Claude] Before**, 21:04:53Z: Lake Formation's three seats, `Parameters` 4/`TRUE`, the flag `true`,
  both default lists empty. `lake_publisher_role` defaults to
  `datazone_usr_role_3j4l4xmvz7fggg_52webn93119ouo`, read at 11.4; the plan, 21:05:23Z: *"Plan: 2 to add, 0
  to change, 0 to destroy."*, `publisher_database[0]` and `publisher_tables["trades"]`, the preconditions
  passing (the switch set, the role under `awsds-data-project-boundary`).
- **[Claude⚡] The apply**, 21:05:34Z to 21:06:10Z: *"Apply complete! Resources: 2 added, 0 changed, 0
  destroyed."* The re-plan at 21:06:36Z: *"No changes."*
- **[Claude] Read back**: `list-permissions` refuses a principal with no resource (*"Resource is mandatory
  if Principal is set in the input"*), so each resource was read and filtered to the role: `DESCRIBE` on
  `curated`, no grant option; `DESCRIBE` and `SELECT` on `curated.trades`, each with the grant option.
  Lake Formation at 21:06:49Z: three administrators, `Parameters` 4/`TRUE`, both default lists empty.
- **[Claude] The instruments**: `./aws/datalake.py` at 21:08:23Z, no failure, `DL-5`, `DL-6` and `DL-7`
  passing and `DL-13` noting the two declared seats; `./aws/catalog.py` at 21:09:31Z, *"all checks
  passed"*, `CT-7` a note naming the catalog road's three grants, the publisher role's on `curated` and
  on `curated.trades`, and `CT-8` twelve `IAMPrincipals` grants, all conditioned on a project (ten before
  `governed-lake`). `datalake.py` exits 1 on the unsigned profiles alone.
- **[Claude] Recorded**: the stage file (11.5 done), the grant register's two rows in `AWS_STATE.md`, the
  producer README.

## 2026-10-26 — 11.6: `trades` published from `governed-lake`

*The user in the portal as the Governance Manager user; Claude read AWS as the infrastructure user with
`InfrastructureAccess` in `Data Governance Account` (`awsds-infra-data`), a contributor of `governed-lake`
since 11.4, and in `Sandbox Account 1` (`awsds-infra-sandbox-1`), reads alone. Times UTC.*

- **[user] The step's menu was not there**: *"Entendi que é no SMUS, certo? Não encontrei menu "data
  sources" no SMUS."*
- **[Claude] The step corrected** to the path the portal offered on 2026-09-13 (this log's first sitting):
  *Data → Catalogs → AwsDataCatalog → `curated` → tables → `trades` → Publish to Catalog*, an act that
  creates its own data source with business-name generation on.
- **[user]** *"Executei estas etapas no portal"*, the path above, as the Governance Manager user.
- **[Claude] The trail**, every write as `awsds-data-studio-domain-execution` in the session
  `user-e8a1f320-…`, the Governance Manager's DataZone profile: `CreateDataSource` at 21:17:26Z,
  `CreateAsset` at 21:17:28Z, `CreateListingChangeSet` `PUBLISH` at 21:17:29Z; then two `CreateLineageNode`
  by `datazone.amazonaws.com` at 21:17:32Z. No `GrantPermissions`, `BatchGrantPermissions`,
  `RevokePermissions`, `RegisterResource`, `PutDataLakeSettings`, `CreateTable` or `UpdateTable` in the
  account from 21:15Z, read at 21:20:16Z with the creation events already delivered.
- **[Claude] The data source**: `aus07vzuom8ntc`, named after the account's catalog and `curated`, type
  `GLUE`, `READY`, over `curated` with `INCLUDE *`, `publishOnImport` false,
  `enableBusinessNameGeneration` true, the project role as its data access role, no schedule, no run.
- **[Claude] The asset and its listing**: `c9joopl3avwd1s`, `trades`, `amazon.datazone.GlueTableAssetType`,
  revision 1, external identifier the table's ARN suffixed with the project id; its forms `GlueTableForm`,
  `DataSourceReferenceForm`, `SubscriptionTermsForm` and `CommonDetails`, with `lakeFormationDetails`
  empty and nothing naming `classification` or an LF-Tag, though the table carries
  `classification=internal` (verification vi's lake half: the catalog shows no LF-Tag). The listing
  `b3bagfgnvev3tc` is `ACTIVE`, and Sandbox's `search-listings` finds it, owned by `3j4l4xmvz7fggg`.
- **[Claude] Lake Formation**, at 21:18:38Z, every grant on `curated`, on its table wildcard, on `trades`
  and on `sample_trades`: the publisher's three of 11.5, the Governance Manager's `DESCRIBE`s,
  `InfrastructureAccess`'s, the maintenance role's and Production's share, and nothing new. The source's
  creation wrote no grant (verification xi), as Sandbox's publish of 2026-09-13 wrote none.
- **[Claude] `./aws/catalog.py`** at 21:22:13Z, *"all checks passed"*: `CT-3` five access acts across nine
  listings; `CT-4` all five sources with `publishOnImport` false; `CT-5` noting two sources that generate
  business names, `mydatabase`'s and `curated`'s; `CT-7` the catalog road's three grants alone.

## 2026-10-26 — 11.7: `eighth-experimentation`'s `DataLake` environment

*Claude, the same session; AWS as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`), a contributor of `eighth-experimentation` since 2026-10-15. The write is Claude's,
on the user's word below; the five other sessions on the laptop were told first, the warehouse sitting's
message delivered into its running turn. Times UTC.*

- **[user]** *"Autorizo o 11.7: create-environment do DataLake no eighth-experimentation, como
  infrastructure user, conta Sandbox Account 1, InfrastructureAccess (awsds-infra-sandbox-1), mantendo o
  registro falho 4lrapnc3syxd74."*
- **[Claude] Before**, 21:25:00Z: the project's environments `Tooling` `ACTIVE`, `ml-demo-mlflow` `ACTIVE`
  and `4lrapnc3syxd74` `CREATE_FAILED`, the last on the `DataLake` configuration
  `40631117-4a84-42b1-b2dc-c2deef6c3d52`, which confirms the id (`GetProjectProfile` from Sandbox is refused,
  *"no resource-based policy allows the datazone:GetProjectProfile action"*); Lake Formation's three seats,
  `Parameters` 4/`TRUE`, both default lists empty; the Glue databases `curated`, `default`,
  `glue_db_4zojr4rr6bmnww`, `mydatabase` and `raw`, `mydatabase` holding `house-price`.
- **[Claude⚡] The create**, 21:25:23Z: `create-environment` with that configuration, blueprint
  `d8w7c3fmbsz5cg`, name `eighth-experimentation-lakehouse`; `blerpkhn9nj7o0` `CREATING` at 21:25:24Z and
  `ACTIVE` at 21:26:00Z, `lastDeployment` `SUCCESSFUL`. DataZone took a second environment from one
  configuration beside the failed record, so 2.7 did not have to come first.
- **[Claude] What it holds**: the database `glue_db_blerpkhn9nj7o0` under the project's
  `dev/data/catalogs/`, no create-table default; the stack `DataZone-Env-blerpkhn9nj7o0`; the subscription
  target `eighth-experimentation-lakehouse-default-target` (`3qjec3ymbu5p5c`) for `GlueTableAssetType` and
  `GlueViewAssetType`, its `manageAccessRole` the project role and its authorized principal
  `abac:CURRENT_PROJECT`; a Glue data source over the database, `5w1ic2yqcs5uog`, `READY`, daily
  `cron(25 21 * * ? *)`, the minute of its creation.
- **[Claude] The writes, from Sandbox's trail**: `CreateDatabase` at 21:25:41Z, two `BatchGrantPermissions`
  at 21:25:49Z and three `GrantPermissions` at 21:25:50Z, all the provisioning role's; the manage-access
  role's `CreateLakeFormationOptIn` at 21:25:50Z, passing, and its `RevokePermissions` from
  `IAM_ALLOWED_PRINCIPALS` at 21:25:51Z, *"InvalidInputException"*, nothing to revoke; the provisioning
  role's `TagResource` at 21:25:52Z. 2.0's pattern, call for call. On the database: `IAMPrincipals` with
  `CREATE_TABLE`, `DESCRIBE` and `DROP` under `eighth-experimentation`'s condition, the provisioning role's
  creator `ALL`, and the manage-access role's `CREATE_TABLE` and `DESCRIBE`, `DESCRIBE` grantable.
- **[Claude] After**: `mydatabase` still holds `house-price`; Lake Formation's settings unchanged.

## 2026-10-26 — 11.8 and 11.9: the subscription, its approval, and what the fulfilment wrote

*The user in the portal as the Data Scientist User and as the Governance Manager user; Claude read AWS as the
infrastructure user with `InfrastructureAccess` in `Data Governance Account` (`awsds-infra-data`) and in
`Sandbox Account 1` (`awsds-infra-sandbox-1`), contributor of both projects, reads and `terraform plan`
alone. Times UTC.*

- **[user]** *"Pedi a assinatura da trades como Data Scientist User no eighth-experimentation e aprovei como
  Governance Manager no governed-lake. Leia o 11.8 e o 11.9."*
- **[Claude] The request and its approval**: `blqgeezyxnosnk`, created 21:34:55Z by an `SSO` profile, the Data
  Scientist User's, for `eighth-experimentation`, reason *"test"*; `ACCEPTED` at 21:36:15Z, its reviewer the
  Governance Manager's profile. The subscription `6ubv3kbnjqjogg` `APPROVED`; its grant `d2zjuni9kjonio` to
  the target `3qjec3ymbu5p5c` `IN_PROGRESS` from 21:36:17Z and `COMPLETED`, the asset `GRANTED`, at
  21:37:18Z, 63 s after the approval.
- **[Claude] Verification vii, from the trail**: `CreateSubscriptionRequest` at 21:34:55Z and
  `AcceptSubscriptionRequest` at 21:36:15Z, both as `awsds-data-studio-domain-execution`, in sessions named
  after the person, `user-28f1b390-…` and `user-e8a1f320-…`. The approval ran as the domain execution role
  under DataZone's ownership check, and `GovernanceManagerAccess` made no call.
- **[Claude] The fulfilment in Data Governance**, the publishing role
  `datazone_usr_role_3j4l4xmvz7fggg_52webn93119ouo` in `AWSDataZone-Subscriptions` sessions with no source
  identity: `BatchGrantPermissions` and `ram:CreateResourceShare` at 21:36:50Z, then four
  `glue:PutResourcePolicy`, 21:36:50Z to 21:36:51Z, on `database/*` (twice), `table/*/*` and `catalog`,
  each with `enableHybrid` `TRUE`; nothing refused.
  - The grant: `SELECT` on `curated.trades` to Sandbox's `IAMPrincipals` under
    `context.datazone.projectId=="avhvbqn37ty7m8"`, no grant option.
  - The share: `LakeFormation-V5-ZKUYXYESG4`, created 21:36:49Z, `allowExternalPrincipals` false, resources
    the lake's `catalog`, `database/*` and `table/*/*`, its one principal Sandbox's account, three
    permissions; `ACTIVE` among Sandbox's received shares, no invitation pending.
  - The policies are per resource, not the account's: `glue get-resource-policy` still answers *"Policy not
    found"*, and `glue get-resource-policies` lists them. The new ones grant Sandbox's account root the
    Glue table and partition actions, reads and writes, on `catalog`, `database/*` and `table/*/*` under
    `aws:PrincipalOrgID`, and restate `AWSRAMPermissionLFTag…` statements for the three consumer accounts
    under `glue:EvaluatedByLakeFormationTags`. Per-resource policies already stood on `database/curated` and
    `table/curated/*` since 2026-10-22, from Production's named share. Lake Formation still gates every
    write: no Sandbox principal holds `ALTER` or `DROP` on a lake table.
- **[Claude] The fulfilment in Sandbox**, `eighth-experimentation`'s role in an `AWSDataZone-Subscriptions`
  session with no source identity, at 21:37:09Z: `CreateTable` of the resource link `trades` in
  `glue_db_blerpkhn9nj7o0`, targeting the lake's `curated.trades`, and `BatchGrantPermissions`, `DESCRIBE`
  on it to `IAMPrincipals` under the project's condition; the creator holds `ALL`, `DESCRIBE` and `DROP`,
  grantable. Glue reports the link's `CreateTime` as the target table's, 2026-10-22.
- **[Claude] The slices and the instruments**: `data/` re-plans *"No changes."* at 21:40:42Z, DataZone's
  grant, share and policies being no declared resource; `./aws/catalog.py` at 21:42:11Z, *"all checks
  passed"*, `CT-7` naming the catalog road's grants, the publisher's three and the fulfilment's `SELECT`,
  `CT-8` seventeen conditioned `IAMPrincipals` grants, `CT-3` seven access acts across nine listings;
  `./aws/datalake.py` at 21:43:36Z, no failure, `DL-5` 4/`TRUE`, `DL-7` ten shares out, `DL-13` the two
  declared seats.
- **[Claude] The warehouse sitting told** at 21:40Z that the subscription had run, with its times: it had
  asked the user to hold it until its 9.7 read after the re-grant.

## 2026-10-26 — 11.10: `eighth-experimentation` reads `curated.trades` through the subscription

*The user in the portal as the Data Scientist User; Claude read AWS as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and `Data Governance Account`
(`awsds-infra-data`), reads alone. Times UTC.*

- **[user]** *"A consulta rodou com sucesso quando selecionei Athena (SQL) como compute"*, in
  `eighth-experimentation`'s query editor, with no space.
- **[Claude] The query**: `f71c904f-7fa4-42f6-9526-413c8b7a4074` in `workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c`,
  *"SELECT * FROM "glue_db_blerpkhn9nj7o0"."trades" LIMIT 10"*, `SUCCEEDED`, submitted 21:47:19Z, 535 bytes
  scanned, 1,550 ms in the engine, Athena engine version 3.
- **[Claude] Sandbox's trail**: at 21:47:13Z an `ExecuteQuery` as `awsds-sandbox-warehouse-access-avhvbqn37ty7m8`,
  the project's Redshift connection, the editor's first compute; at 21:47:19Z `ExecuteQuery` and, invoked by
  `sqlworkbench.amazonaws.com`, `StartQueryExecution`, both as the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` with the Data Scientist User's profile as source
  identity; at 21:47:20Z `lakeformation:GetDataAccess` for `SELECT`, invoked by `athena.amazonaws.com` on the
  resource link `glue_db_blerpkhn9nj7o0/trades` and by `glue.amazonaws.com` on the lake's `curated/trades`.
  No error.
- **[Claude] Data Governance's trail**: the same vend at 21:47:20Z, `GetDataAccess` for `SELECT` on
  `curated/trades` by `AWSAccount`, invoked by `glue.amazonaws.com`, the cross-account form Stage 18 7.2
  read. Verification xiii is answered: a Sandbox project reads a lake table through the catalog road, its
  project role holding no TBAC grant.
