# Log — Stage 19 — A data product on SageMaker Unified Studio's native path

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-19-smus-native-data-product.md`](../plan/stages/stage-19-smus-native-data-product.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-28 — the stage written, with read-only measurements and nothing changed in AWS

- **[user] The request**, in a session started from the session "Mecanismo de cadastro no Glue", in the
  user's words: *"Crie um plano que exercite a forma nativa do SMUS de produzir dados e publicá-los,
  através de uma aplicação SMUS."*, with the eight bullets the stage file quotes under "The premises".
  The session ran on the user's laptop with the infrastructure user signed in (*"usuario infra sso
  logado para o que for necessário de leituras"*); every `aws` call below is a read as
  `InfrastructureAccess`, in `Data Governance` (`awsds-infra-data`), `Sandbox Account 1`
  (`awsds-infra-sandbox-1`), `Staging Account` and `Production` (`awsds-infra-staging`,
  `awsds-infra-prod`), each confirmed by `sts get-caller-identity` first. No apply, no AWS write, no
  portal act.
- **[Claude] The review**, read from the repository at `main` `d4cabbb7` and recorded in the stage
  file's "The plan and the estate against the premises": the twelve decisions, the fourteen stages, the
  five documents, the four runbooks, the code, the policies and the three instruments the brief listed.
  Two stale lines the brief named were confirmed: `runbooks/sagemaker-application.md:1140` (*"its shape
  open"*, decision 1 taken 2026-10-26) and `docs/GOVERNANCE.md:737-739` (*"until a lake table is
  published"*, `curated.trades` published 2026-10-26). The first is corrected in this stage's pull
  request; the second sits beside Stage 6f's text and goes to the 6f follow-up session, which confirmed
  it will fix it (its message of this sitting).
- **[Claude] The instruments, run from the worktree**: `./aws/catalog.py` wrote `aws/output/catalog.txt`,
  *"all checks passed"*: nine listings, seven data sources, 20 project-conditioned `IAMPrincipals`
  grants (`CT-8`), the catalog road at one listing (`curated.trades`, `governed-lake`, approval `YES`)
  with one subscription (`eighth-experimentation`, `APPROVED`, its grant `COMPLETED`) and five grants on
  the table, each explained (`CT-10`); `CT-6` noting the two `Tooling` model-package sources, 77 failed
  runs across them (`EXC-11`). `./aws/studio.py` wrote `aws/output/studio.txt`: `US-1` to `US-10`
  passing, `US-3` noting the pilot's `Tooling` in the domain account, 13 configurations in Sandbox, the
  three profiles; the persona and deploy profiles not signed in read `FAILED` in its section 10, as the
  infrastructure user's session covers none of them.
- **[Claude] Readings of the domain**, as `awsds-infra-data` and `awsds-infra-sandbox-1`:
  - the domain lists 24 managed blueprints (`RedshiftServerless`, `LakehouseCatalog`, `LakehouseAdmin`,
    `DataLake`, `S3TableCatalog`, `Workflows`, `SageMakerAIDomain` among them) and 24 managed asset types,
    `GlueTableAssetType`, `GlueViewAssetType`, `RedshiftTableAssetType`, `RedshiftViewAssetType`,
    `S3ObjectCollectionAssetType`, `S3TableBucketAssetType`, `SageMakerUnifiedStudioScheduleAssetType`
    and `SageMakerUnifiedStudioDataQualityRulesetAssetType` among them, one more of each than the 23
    `docs/SMUS.md` counted on 2026-10-18 and 6f 3.1 on 2026-09-18;
  - four projects: `eighth-experimentation` (2026-08-23), `test-experimentation` (2026-10-15),
    `GenerativeAIModelGovernanceProject` (2026-10-19) and `governed-lake` (2026-10-26), all in the root
    domain unit;
  - `eighth-experimentation` holds five environments: `Tooling` (`5hkjdsy3umpi1c`, `ACTIVE`),
    `eighth-experimentation-lakehouse` (`blerpkhn9nj7o0`, `ACTIVE`, 6f 11.7), `ml-demo-mlflow`
    (`ACTIVE`), the failed `create-datalake-database-env-mydatabase-…` (`4lrapnc3syxd74`, 6f decision
    6) and **`create-datalake-database-env-new_database-1793168541728` (`5i25j3k8mqz47k`, `ACTIVE`,
    created 2026-10-28T06:22:22Z by the Data Scientist User's profile)**: a database created in the
    portal is one `DataLake` environment per database, with its Glue database `new_database` under the
    project's `dev/data/catalogs/` and its own daily data source at `cron(22 6 * * ? *)`, no run yet.
    This session neither created nor touches it;
  - the project's eleven connections, the Redshift one `redshift-serverless.redshift` (`REDSHIFT`,
    database `dev`, workgroup `awsds-sandbox-warehouse`, `lineageSync` enabled at `cron(43 3 * * ? *)`,
    6h decision 3) among them; its subscription targets: the `Tooling` environment's two, for
    `BedrockModelAssetType` and for `SageMakerFeatureGroupAssetType` and
    `SageMakerModelPackageGroupAssetType` (the manage-access role), and the `DataLake` environment's one,
    `eighth-experimentation-lakehouse-default-target`, for `GlueTableAssetType` and `GlueViewAssetType`,
    `manageAccessRole` the project role, `databaseName` `glue_db_blerpkhn9nj7o0`. **No environment carries
    a target for `RedshiftTableAssetType` or `RedshiftViewAssetType`**, the connection notwithstanding;
  - the `experimentation` profile's configurations: `Tooling` `ON_CREATE` and twelve `ON_DEMAND`
    (`DataLake`, `S3Bucket`, `S3TableCatalog`, `EmrServerless`, the seven Bedrock ones, `MLflowApp`), no
    `RedshiftServerless` and no `LakehouseCatalog` (D40); `lake-publishing` holds `Tooling` alone with
    `enableSpaces=false`;
  - the data sources: three Glue sources over `eighth-experimentation`'s databases (`mydatabase`,
    `glue_db_blerpkhn9nj7o0`, `new_database`), all `publishOnImport` false, the first with business-name
    generation on and no schedule, the other two off and daily, each with the project role as
    `dataAccessRole` through the `project.default_lakehouse` connection; one over
    `test-experimentation`'s `glue_db_4zojr4rr6bmnww` (`cron(51 2 * * ? *)`, 8 runs `SUCCESS`, 0
    assets); `governed-lake`'s over `curated` (no run); the two `Tooling` model-package sources, one
    `RUNNING` in each project at the time of the read;
  - **the subscription's resource link was imported as an inventory asset**: the source over
    `glue_db_blerpkhn9nj7o0` ran `SCHEDULED` on 2026-10-27T21:32:10Z (`b24fih4tl7905s`, `SUCCESS`, 2 s,
    `added: 1`), and `eighth-experimentation`'s inventory holds `trades` (`cm329mc3bqu39s`,
    `GlueTableAssetType`, external identifier the resource link `glue_db_blerpkhn9nj7o0/trades`, created
    21:32:12Z, no listing) beside `house-price`. `./aws/catalog.py` reads no inventory, so no check
    noticed. Sent to the 6f session as information; its reply confirms the reading and takes the check
    into the 6f follow-up it proposes, leaving the decision on the unpublished asset to this stage;
  - the data product `my-data-product` (`cqrp6eqjjpvvgw`, `CREATED`, revision 1, one item, the asset
    `house-price`), its listing `czt1j8ttwsl8r4` `ACTIVE` at revision 1 over the asset listing's
    revision 2, with no subscription; the one subscription in the domain is `6ubv3kbnjqjogg`, the
    `trades` listing's, `APPROVED` (6f 11.8).
- **[Claude] Readings of the two Glue catalogs and Lake Formation**, as `awsds-infra-sandbox-1`:
  - `glue_db_blerpkhn9nj7o0`, `new_database` and `mydatabase` share the location
    `s3://awsds-sandbox-smus-projects/<domain>/<project>/dev/data/catalogs/`; the first holds the
    resource link `trades` (target `curated.trades` in the lake's catalog, `IsRegisteredWithLakeFormation`
    false), the second nothing, the third `house-price` over its upload folder;
  - on `glue_db_blerpkhn9nj7o0`: `IAMPrincipals` under `context.datazone.projectId=="avhvbqn37ty7m8"`
    hold `CREATE_TABLE`, `DESCRIBE` and `DROP` on the database and `ALTER`, `DELETE`, `DESCRIBE`,
    `DROP`, `INSERT` and `SELECT` on its tables; `awsds-sandbox-smus-provisioning` holds `ALL` with the
    grant option on the database; `awsds-sandbox-smus-manage-access` holds `CREATE_TABLE` and `DESCRIBE`
    (grantable `DESCRIBE`) on the database and `DESCRIBE` and `SELECT` on its tables; the project role
    holds `ALL`, `DESCRIBE` and `DROP` on the resource link it created. Sandbox's settings: three
    administrators (`InfrastructureAccess` and the two SMUS seats), `AllowFullTableExternalDataAccess`
    `true`, `CROSS_ACCOUNT_VERSION` 4, `SET_CONTEXT` `TRUE`, both create-default lists empty;
  - `glue get-catalogs` answers an empty list in Sandbox, Data Governance, Staging and Production: no
    federated catalog and no Redshift Managed Storage catalog exists anywhere;
  - the namespaces `awsds-sandbox-warehouse` (database `warehouse`, default role
    `awsds-sandbox-warehouse-exec`, the only role attached) and `awsds-prod-warehouse` (the same shape,
    `awsds-prod-warehouse-exec`), each `AVAILABLE` with no workgroup; Production's `app_outputs` holds
    `trades_notional` (`EXTERNAL_TABLE`, `s3://awsds-prod-outputs/app-etl/tables/trades_notional/`,
    not registered with Lake Formation), the table Terraform declares.
- **[Claude] The vendor pages and the installed CLI**, read 2026-10-28 and listed in
  `docs/REFERENCES.md`'s rows of this date: the stage file's "The user's questions, answered" carries
  each quote with its page.
- **[Claude] The peer sessions**, told as information: the 6f session (the inventory import above and
  `GOVERNANCE.md:737`) and the Stages 7-10 session (the three hunks this stage's pull request makes in
  `runbooks/sagemaker-application.md`), which answered that its merged branch touched none of them and
  that the Stages 8-10 work now sits in the session "stages-8-10-nothing-up", not yet writing. The
  "Redshift unload sem S3" session was not written to: the stage file records what concerns it.
- **[Claude] Written**: the stage file, this log, the rows in `docs/plan/stages/INDEX.md`,
  `docs/GENERAL_PLAN.md` and `docs/log/INDEX.md`, `INT-26` in `docs/plan/integrations.md`, the
  references and the price rows, and the runbook's three stale hunks, in one pull request against
  `main`. Every decision the stage names is due, none taken.

## 2026-10-31 — decision 6 taken as (b), the AWS model; passes 3 and 4 rewritten; nothing changed in AWS

- **[user] The questions before the decision**, in this session from 2026-10-28 to 2026-10-31: what the
  stage plans; whether Staging and Production should stay without a SMUS project and how that would
  work; which steps put a table in Terraform; whether every premise is compatible with no project in
  the targets; what SMUS's intended out-of-the-box use is for production, publication, promotion and
  Redshift; whether the AWS model could be adopted whole or this stage had to validate something first;
  decision 6's context and alternatives. Each answered from the stage file, Stage 18's measurements,
  `docs/SMUS.md`, `docs/plan/upstream-releases.md` and the decision files, with no AWS call.
- **[Claude] The reading that preceded the decision**: the AWS model is measured (Stage 18, Staging,
  2026-10-17 to 10-22); what kept D41 item 2 on 2026-10-22 was its price on the perimeter, not an open
  hypothesis; the stage as written validated the hybrid's hypotheses in pass 4 and the ones both designs
  share in passes 1 to 3, not the AWS model's; the Redshift subscription target is open under either
  design (0.6). The recommendation (a) with (a2) was restated with its reasons.
- **[user] Decision 6**, verbatim: *"Decido pelo modelo da AWS, com o uso previsto do SMUS e promoção
  entre ambientes via ferramenta SMUS CICD CLI"*. Taken as (b), against the recommendation.
- **[Claude] Written**: the stage file (Status, Prerequisites, Consumes and Proves; the review tables'
  rows for D17, D20, D22, D26, D28, D41, Stages 8, 9, 10 and 18, `GOVERNANCE.md` §Publishing, the data
  and application slices, the orchestration module and `DenyDataZoneEntirely`; question 2's dated
  outcome; 3.2's verification xvii and the new 3.3, the manifest's `staging` and `prod` stages; pass 4
  rewritten as 4.1 to 4.13 on Stage 18's recipe, each step citing the Stage 18 step it repeats; pass 5's
  note; 6.2 and 6.3; verifications xvii to xxv; decision 6 taken, 7 and 8 moot, 10 amended, 13 to 16
  due with recommendations; Cost, Rollback, What this stage does not do and What concerns the other
  sessions), D41 (the Status line, the section "Item 2 reopened 2026-10-31", the revision trigger), D26's
  dated amendment, `POLICIES.md`'s `DenyDataZoneEntirely` row (the trigger fired, the deny standing until
  4.1's apply), `integrations.md` INT-26, `docs/plan/stages/INDEX.md`, `docs/GENERAL_PLAN.md`,
  `docs/plan/decisions/INDEX.md`, `docs/log/INDEX.md`, `docs/plan/waiting-on-the-user.md` and
  `CLAUDE.md`'s Current position. No apply, no AWS write, no portal act.
- **[Claude] Left to other sessions**, recorded in the stage's "What concerns the other sessions": the
  note on 6f decision 4, the 6f session's; Stage 10's 1.1, 2.4, 4.2 and decision 9 and Stage 8's legs,
  the Stages 8-10 session's (4.9, 4.11); `governance/` shared with 6d's 2.7 (4.5).
- **[Claude] The branch**: the session's branch `claude/estagio-19-planejamento-f55cae` had been merged
  as PR #275 and its remote deleted, so this sitting's work is on `claude/stage-19-decision-6-aws-model`,
  cut from `main` at `52ca42e9`.
- **[user] Decision 13**, verbatim: *"Ok em relação a sua recomendação."*, to the recommendation
  restated in chat as (b) with a subscription deny, revised from the file's (a) because Production is
  also the hub account; recorded in the stage file with the revision's reasons. Decisions 14 to 16
  are presented one at a time, at the user's request.
- **[user] Decision 14**, verbatim: *"Ok em relação a sua recomendação"*, to (a) with (d) and the
  bootstrap `workflow.run` in Production, as presented in chat; recorded in the stage file.
- **[user] Decision 15**, verbatim: *"ok em relação a sua recomendação"*, to (a), the Governance
  Manager as a contributor of `deploy-production` under the person-session deny, (b) the fallback
  until the deny is applied; verification xxvi added for the domain-defined designation.
- **[user] Decision 16**, verbatim: *"(b)"*, against the recommendation: the warehouse workflow moves
  into Production's project with the project role as its identity. **[Claude]** recorded with what it
  carries (the lake's write share, 9.3's grants and the 5439 ingress to the project role, decision 15's
  deny grown, the render and the orchestration module's workflow resource retired whole, verification
  xxvii), and the review rows, 3.3, 4.9, 4.11, 6.2, D41's note, `CLAUDE.md` and the waiting list
  brought to it. Decisions 13 to 16 are taken; 1 to 5, 9, 11 and 12 stay due.
- **[user] Decision 1**, verbatim: *"conforme sua recomendação"*, to (a): `app-etl` extended on a branch
  that joins the next tag with decision 6 (b)'s changes.
- **[user] Decision 2**, verbatim: *"ok em relação as recomendações"*, to (a) with (d): the Spark write
  into a named database `app_etl`, the same name in every project.
- **[user] Decision 3**, verbatim: *"ok em relação as recomendações"*, to (a), the workflow's task, with
  the stage variable `PUBLISH_LISTING` as its gate; 1.1 brought to it.
- **[user] Decision 4**, verbatim: *"ok em relação as recomendações"*, to (a), a metadata form
  `classification` on the asset; (c) moot since decision 6 (b).
- **[user] Decision 5**, verbatim: *"ok em relação as recomendações"*, as recommended with the refinement:
  a third `experimentation` project as pass 2's consumer, the Governance Manager a contributor of
  `eighth-experimentation` for its approvals, and `eighth-experimentation` the consumer of Production's
  listing at 4.12 and pass 5. Decisions 1 to 5 and 13 to 16 are taken; 9, 11 and 12 stay due.
- **[user] Decision 9**, verbatim: *"ok em relação as recomendações"*, to (a), the read in place through
  `eighth-experimentation`'s connection on Production's subscribed product, 5.3's Redshift asset read and
  not subscribed; 5.1 brought to decision 6 (b).
- **[user] Decision 11**, verbatim: *"ok em relação as recomendações"*, to the recommendation revised in
  chat: rows by class in the register for what lands in Production and Staging, none for Sandbox's
  project-owned fulfilments, `catalog.py`'s product-road checks in every case.
- **[user] Decision 12**, verbatim: *"ok em relação as recomendações"*, to outside: the product outside
  open question 25's expiry rule, D19 to gain two dated lines at 6.2. **Every decision of the stage is
  taken**; the waiting list's row for them is removed, `CLAUDE.md` and the indexes brought to it. Pass 1
  waits on a Sandbox sitting and on decision 1's branch of `awsds/app-etl`.

## 2026-10-31 — 1.1 written: the application change in `examples/app-etl/`, nothing run in AWS

- **[user]** *"Sim, 1.1 agora"*, on the branch of PR #281, the template's copy in this repository; the
  mirror to `awsds/app-etl` is the next GitLab sitting's.
- **[Claude] Written**: `glue/transform.py` (the product table as Iceberg on `glue_catalog`, both options
  or neither, read back and counted), `workflows/app-etl.yaml` (the Glue task's two arguments, the
  `--datalake-formats` and `--conf` defaults, the fifth task `publish`), `code/app_etl_tasks.py`
  (`publish` and its helpers, the gate on `publish_listing`), `manifest.yaml` (`PRODUCT_DATABASE:
  app_etl`, `PUBLISH_LISTING: "true"` in `dev` and `test`, literals), the tests (`FakeWriter.format` and
  `saveAsTable`, `FakeSession.table` returning a frame, four product-table cases; `FakeDataZone` and nine
  publication cases), `README.md`, `scripts/render-workflow.py` (`{env.PRODUCT_DATABASE}` to
  `app_outputs`, `{env.PUBLISH_LISTING}` to `false`, the Glue task's `--TABLE_DATABASE` and
  `--TABLE_NAME` dropped, an invariant that none survives) and `runbooks/sagemaker-application.md`'s §M
  and §W rows. `uv run pytest`: 60 passed, 1 skipped; ruff clean; the pinned lint `d856982c` through
  `uvx` from GitHub: `ok: 9 arquivo(s)`; `./scripts/render-workflow.py --check` OK; `make check` OK;
  the pre-commit hooks pass.
- **[Claude] Read on the way**, recorded in 3.1 and 3.3: the pinned lint's rule `manifest` refuses
  `content.catalog.enabled` (*"o bundle levaria o que o projeto tem, e não a tag"*), so 3.1 waits on a
  lint release and on the deploy role's DataZone reads for the export; the CLI 1.0.9 refuses every
  command while any `${VAR}` of the manifest is unset, so the `staging` and `prod` stages, and
  `app-etl-warehouse`'s entry, are written at 4.9 with their projects' values. The lint's rule on
  `{env.NOME}` wants each name declared in every stage, which the two literals satisfy. The local
  `awsds-workflows` (`~/.local/bin`) predates `lint`; the clone at `~/src/awsds-workflows` is at
  `ff25eae`, behind the pin.

## 2026-11-08 — pass 1 taken into this session; the preparation with nothing up

- **[user]**, verbatim: *"Faça esta tarefa aqui: “Stage 19 pass 1: mirror and first Sandbox run”"*, then
  *"Existe algo que pode ser preparado ou executado para este stage agora antes de subir o ambiente?"*.
- **[Claude] The branch**: PR #281 merged at 21:17 UTC (squash, `39a50b26`), its branch retired;
  `claude/stage-19-pass-1` cut from `main` in the same worktree, the project folder at the same commit. No
  other session of this project running (the one in an AWS-DataScience worktree idle since 2026-11-05).
- **[Claude] Before-readings**, the SSO session valid, the hub and GitLab `stopped`: `./aws/catalog.py` all
  checks passed (9 listings, 7 sources, no `app_etl` database); `./aws/studio.py` passed, its failed calls
  the persona profiles without a token; `eighth-experimentation` (`avhvbqn37ty7m8`, the manifest's `dev`)
  holds five environments (`Tooling`, `eighth-experimentation-lakehouse`, `new_database` of 2026-10-28,
  `mydatabase` `CREATE_FAILED` since 2026-09-13, `ml-demo-mlflow`) and four sources, `new_database`'s daily
  at 06:22 UTC with 11 `SUCCESS`; ten MWAA Serverless workflows in Sandbox, `app_etl_eighth_experimentation_app_etl`
  of 2026-10-26 among them; the Glue job `app-etl-avhvbqn37ty7m8` carries `--custom-logGroup-prefix` alone
  in its `DefaultArguments` (modified 2026-10-26). The mirror's tarball: 25 files from `39a50b26`, the CI
  `include` at `gates-v0.6.0`'s commit, the lint pin `d856982c`.
- **[Claude] Read**: the project role `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` carries six managed
  policies and none inline; `SageMakerStudioProjectRoleMachineLearningPolicy` v47 grants `datazone:Get*`,
  `List*`, `Search*`, `CreateAsset*`, `CreateListingChangeSet`, `CreateSubscriptionRequest` and
  `RevokeSubscription` on `*`, `SageMakerStudioProjectUserRolePolicy` v76 reads on the domain, the other
  four no `datazone` action; the boundary `awsds-sandbox-project-boundary` v2 allows `*` and denies the job
  settings, the lake prefixes and the lake key. `StartDataSourceRun` is granted by none. `simulate-principal-policy`
  answered `explicitDeny` to every action asked, `glue:GetTable` included: the conditioned denies without
  their context keys (Lesson 30), so the simulation measures nothing here. `DenyDataZoneEntirely` is the
  Workloads OU's alone; the baseline denies `datazone:CreateDomain` outside the Data OU. Sandbox's `egress/`
  lists `datazone` among its services. The CLI's `context_resolver.py` substitutes `{domain.id}`, `{domain.name}`,
  `{domain.region}`, `{proj.id}`, `{proj.name}`, `{proj.domain_id}`, `{proj.iam_role_arn}` and the
  connections at the deploy; no document or snapshot of this estate measures `DataZoneDomainId` or
  `DataZoneProjectId` on a worker.
- **[Claude] Written**: `publish` takes `domain` and `project` from `{domain.id}` and `{proj.id}` in the
  workflow's `op_kwargs`, the worker's variables read only for a value left empty; the tests (61 passed),
  `scripts/render-workflow.py` (`none` for both in a target), the runbook's §W row;
  `sandbox/workflows/main.tf` gains the statement `StartADataSourceRunInTheProjectsDomain`
  (`datazone:StartDataSourceRun` on the domain's ARN), planned as `awsds-infra-sandbox-1`: `1 to change`,
  the policy's new version, nothing else; `serverless-workflows.md` §G and the stage file's 1.1 and 4.4.
  `make check` passes. **Nothing applied**: the apply waits on the user's word in this chat.
- **[Claude] A credential exposed**: a keychain probe for `gitlab.awsds.internal` printed the GitLab
  user's password into the session's tool output; it is written nowhere else, and its rotation is
  recommended once GitLab is up.
- **[user]**, verbatim: *"Autorizo o apply"*. **[Claude⚡] Applied** 21:50 UTC as `awsds-infra-sandbox-1`,
  the saved plan: `0 added, 1 changed, 0 destroyed`, `awsds-sandbox-workflows` at `v4` with
  `StartADataSourceRunInTheProjectsDomain`, attached to both project roles, the plan after it `No
  changes`; no other session of this project was running.
- **[user]**, verbatim: *"Vou ter que parar esta sessão por aqui. Atualize sua memória orientando as
  próximas sessões sobre como prosseguir. Avalie novamente o que pode ser antecipado neste momento sem o
  ambiente no ar. Faça as correções necessárias no plano e suba no PR aberto."* **[Claude]** the sitting's
  order written in the stage file before 1.2, with this pass's values (`v0.4.6`'s digest for
  `JOB_IMAGE_URI`, both project names, the placeholders, both zips, the readings' commands); two rows in
  the waiting list (the sitting; the password's rotation); `CLAUDE.md`'s bullet. What stays for the
  sitting: the mirror's push (the tunnel), the portal's database, the deploy and the runs, the readings.
  The session ends with the hub, GitLab and Sandbox's `egress/` down; the grant is the day's one write.
  The day's work is [PR #283](https://github.com/felipenoris/AWS-DataScience/pull/283).
- **[user]**, verbatim: *"Faça uma revisão no log, verifique se tudo que foi feito nesta sessão está
  corretamente registrado para as próximas sessões entenderem o estado atual do plano. Revise o restante
  das atividades deste estágio considerando o andamento até o momento, e corrija o que for necessário."*
  **[Claude] A correction**: the sentence above, *no document or snapshot of this estate measures
  `DataZoneDomainId` or `DataZoneProjectId` on a worker*, is false. Stage 6i's log holds the measurement
  (2026-10-11: a task of the portal-created `demo-bash-operator` printed the seven `DataZone*` variables
  the portal injects, `get-workflow` returning no `EnvironmentVariables`) and `serverless-workflows.md`
  §O repeats it. The grep that answered nothing never ran: one of its paths was a zsh glob with no match,
  the shell refused the whole command, and `2>/dev/null` hid the refusal (Lesson 62, a third instance
  written there; Lesson 30). What is unmeasured is a CLI-created workflow's worker: the CLI's code passes
  no `EnvironmentVariables`, and 6i's reading was of a portal-created one. The change stands on that
  ground, and the stage file's 1.1 says so. Also corrected in the review: the 1.1 specification
  sentence (the identifiers from the deploy), the header's status, verification ii (the cross-project
  negative the grant's comment and §G name), `terraform-live/README.md`'s bullet on `sandbox/workflows/`
  (missing `glue:GetJob` since 2026-10-16 and the DataZone statement, and calling the test deploy role
  unapplied), the stage index and the plan's row.
- **[user]**, verbatim: *"Faça uma revisão adicional na documentação do projeto e docstrings. Suba os
  ajustes no mesmo PR."* **[Claude]** brought to the task's design: the template's README (`publish`
  among the worker's tasks, the deploy's identifiers, the grant its source run needs, both zips the dev
  deploy builds, `{domain.id}` among the CLI's variables), `sagemaker-application.md` §C (the task's
  DataZone calls and their policies), §B (the second road an application's own product takes since
  decision 6 (b)) and §N (DataZone among the worker's endpoints), `serverless-workflows.md` §O (the
  variables read on a portal-created workflow, a CLI-created one unmeasured), `docs/SMUS.md` (the project
  role's DataZone grants, v47 and v76, and the house's one), and the two test modules' docstrings.

## 2026-11-08 — pass 1's sitting prepared, its window narrowed

- **[user]**, verbatim: *"prossiga com o estágio 19"*.
- **[Claude] Before the sitting**: the branch `claude/estagio-19-97b0ac` at `e36d0a3f` (PR #283's merge),
  equal to `origin/main`; the project folder on `main` at the same commit, clean. The SSO session valid as
  the infrastructure user (`awsds-infra-prod`, `awsds-infra-sandbox-1`, `awsds-infra-data`, each
  `InfrastructureAccess`). `awsds-prod-vpn`, `awsds-prod-proxy` and `awsds-prod-gitlab` `stopped`; Sandbox
  holds no interface endpoint. The peer sessions on the laptop idle. The mirror's archive from `e36d0a3f`
  holds 25 files; the digest the list's step 4 carries is `production/app/app-etl/release.tf`'s.
- **[Claude] Decision 10 found missing from 1.1**: the stage file's decision 10 recommends the job's
  OpenLineage settings on, amended 2026-10-31 to keep them on in the targets, and verification v reads
  them at 1.2, but 1.1's workflow carried none. Written in the template as commit `6370da60`: the Glue
  task's `--conf` gains Stage 18 7.1's settings after the Iceberg catalog; the manifest's `dev` and `test`
  stages gain `ACCOUNT_ID`, the account `spark.glue.accountId` names, read from STS by whoever deploys and
  exported by `test-deploy`; the README and `sagemaker-application.md` §M, §W and §D follow. The render
  drops the job-creation keys that carry it, so the targets are unchanged. The tests 61 passed and 1
  skipped, the pinned lint `d856982c` `ok` on nine files, `make check` OK. The stage's status calls
  decision 10 "moot or amended" and records no verdict of the user's on it; the chat asks for one.
- **[user]**, verbatim: *"revise os próximos passos, preparando o necessário, de forma a minimizar o
  tempo em que o ambiente precisa ficar no ar"*.
- **[Claude] The window narrowed**, read with nothing up as the infrastructure user:
  - `sandbox/egress/`'s plan with `GROUPS=mwaa` on `vpc-egress-v0.19.0`: 28 to add, 0 to change, 0 to
    destroy, 19 interface endpoints among them (`airflow-serverless`, `datazone`, `glue`,
    `lakeformation` and `sts` included).
  - `eighth-experimentation`'s `Tooling` environment: the subnets `subnet-016b5a3a62c739894` and
    `subnet-09d3399d6b0fec93a`, the security group `sg-0fee1c059b82e3562`, the key
    `a81b1ef3-716f-4105-bb42-14184a6e2174`. Both `Tooling` domains hold 0 spaces.
  - The `dev` workflow `app_etl_eighth_experimentation_app_etl`'s last run, started 2026-10-26 05:55
    UTC, `SUCCESS` in 694 s: `process` 459, `transform` 91, `summarize` 5, `write_result` 6.
  - DataZone refuses `awsds-infra-data` the project's inventory: `search`, `get-asset` and
    `list-asset-revisions` answer *"User is not permitted to perform operation"*;
    `awsds-infra-sandbox-1`, a `PROJECT_CONTRIBUTOR`, reads the asset `cm329mc3bqu39s` (`trades`).
    `get-lineage-node` on that asset's id answers that the node does not exist, and no lineage was
    ever posted for it.
  - The readings' script, the stage file's item 8, run whole against the estate: every call answered
    but the four on the absent database `app_etl` (`EntityNotFoundException`).
  - The package `~/tmp/stage19-pass1.tar`: the template's 25 files from `6370da60`, identical to `git
    archive`, and `pass1.sh` (`bash -n` clean, its parsing of the CLI's `run` output tested, its
    follower read the run of 2026-10-26 to `SUCCESS`); sha256 `d9fff051995e5429…`.

  The order is the stage file's list before 1.2: the portal's database and form type before the
  window; in it the hub, `egress/` and a space, 1.3 during run 2; the readings after it; GitLab, the
  tunnel and the PAT out of the window, the mirror's MR at the next GitLab sitting with the password's
  rotation. The waiting list's row, the stage index's row and `CLAUDE.md`'s bullet follow. No AWS write;
  the work is [PR #284](https://github.com/felipenoris/AWS-DataScience/pull/284).
- **[user]**, verbatim: *"Vc está me sugerindo tomar a decisão 10 neste momento? Pode me dar o contexto e
  as opções? Sobre os passos antes de subir o ambiente, criei o database `app_etl`no `AwsDataCatalog` no
  projeto `eighth-experimentation`. Não entendi o que é para fazer no passo 2 (formulário de metadados).
  Pode esclarecer?"*
- **[Claude] 1.2's first half, read** at 23:44 UTC as `awsds-infra-sandbox-1` and `awsds-infra-data`,
  nothing up:
  - The database `app_etl`, created 23:41:18 UTC by `awsds-sandbox-smus-provisioning` (session
    `AmazonDataZoneEnvironmentDeployer-<Sandbox>`) through `datazone.amazonaws.com`, *"Created by
    DataZone for project eighth-experimentation"*; its `LocationUri` the projects bucket's
    `…/avhvbqn37ty7m8/dev/data/catalogs/`, `CreateTableDefaultPermissions` empty, no table.
  - Lake Formation on it: Sandbox's `IAMPrincipals` `CREATE_TABLE`, `DESCRIBE` and `DROP` under the
    condition `context.datazone.projectId=="avhvbqn37ty7m8"` (verification i's conditioned grant, `CT-8`'s
    form); `awsds-sandbox-smus-provisioning` `ALL` with the grant option;
    `awsds-sandbox-smus-manage-access` `CREATE_TABLE` and `DESCRIBE`, `DESCRIBE` grantable. No grant
    names the project role.
  - The environment `create-datalake-database-env-app_etl-1794181260651` (`chz5jdb80ohocw`), `ACTIVE`,
    created 23:41:02 UTC by the user's portal session through Data Governance's
    `awsds-data-studio-domain-execution`, on the `DataLake` blueprint `d8w7c3fmbsz5cg` and the
    configuration `40631117-…`: `glueDBName` `app_etl`, the stack `DataZone-Env-chz5jdb80ohocw`,
    `glueOutputUri` the same prefix, `userRoleArn` the project role. No subscription target, as the one
    of 2026-10-28.
  - The source `<Sandbox>-AwsDataCatalog-app_etl-default-datasource` (`budryu9mt9y5u8`): `GLUE`, `READY`,
    enabled, `publishOnImport` false, `enableBusinessNameGeneration` false, daily at
    `cron(41 23 * * ? *)`, on the connection `5pf7uc0ugllsb4` with no environment id, the project role its
    `dataAccessRole`, the filter `app_etl` `INCLUDE *`, `autoImportDataQualityResult` true; no run. The
    project holds six environments and five sources. The readings' script took the environment from the
    source, which names none, and now falls back to the environment named for the database.
- **[Claude] Decision 4's form, read before the user creates it**: the domain's root unit
  `bzq0cbh2gd0f4g` (`awsds-studio`), owned by Data Governance's `InfrastructureAccess` group profile
  (`7ee243ab-…`) alone and with no child unit, holds no `CREATE_FORM_TYPE` and no `CREATE_GLOSSARY`
  grant. AWS's page names the path *Manage → Catalog management → Metadata forms* and the field types
  `String`, `Integer`, `Long`, `Float`, `Double`, `Boolean`, `Date` and `Business glossary`, none
  enumerated; a field can be `Required`, and a domain unit's metadata rule makes a form required on
  publishing. Decision 4's "one field enumerated on the four values" has no such field in the portal: a
  `String` the check reads, or a `Business glossary` field over a glossary of the four terms.
- **[Claude] Decision 10's context, read for the user's question**: `SageMakerStudioProjectUserRolePolicy`
  v76 on the project role carries `datazone:PostLineageEvent`, as v75 did at Stage 18 7.1. The sitting of
  2026-10-31 recorded decision 10 as amended and took the others one at a time; the chat sets out its
  options for the user's verdict. No AWS write.

## 2026-11-09 — decision 10 taken

- **[user]**, verbatim: *"Keep it on"*, to decision 10 as set out in chat on 2026-11-08: the Glue job's
  OpenLineage settings on in `dev` and `test`, about 24 lineage events from pass 1's two runs that no API
  deletes, the targets unchanged until 4.11.
- **[Claude] Recorded**: the stage file's decision 10 and status, the waiting list's row, `CLAUDE.md`'s
  bullet and the log index. The package `~/tmp/stage19-pass1.tar` already carries the settings
  (`6370da60`), so nothing is rebuilt. Decision 4's form type stays open, its two paths put to the user
  in chat. No AWS write.
## 2026-11-09 — decision 4's form type: the `CREATE_FORM_TYPE` grant written and planned

- **[user]**, verbatim: *"sobre o formulário, (B)"*: the `CREATE_FORM_TYPE` grant first, then the form
  with a `String` field, as set out in chat on 2026-11-08.
- **[user]**, verbatim: *"Acabei de entrar no SMUS com Data Scientist, e no menu Manage -> Metadata Forms
  o botão "Create metadata forms" aparece mas desabilitado"*.
- **[Claude] Read** as `awsds-infra-sandbox-1`: `eighth-experimentation`'s members are one
  `PROJECT_OWNER` user, the portal user whose session created the database's environment, a
  `PROJECT_CONTRIBUTOR` user and Sandbox's `InfrastructureAccess` group profile (`839bcde8-…`) as
  `PROJECT_CONTRIBUTOR`, so the grant's designation is `OWNER`. The pinned `awscc` schema takes a
  project principal (`project_identifier`, `project_designation`) and `detail.create_form_type`.
- **[Claude] Written**: `data-governance/governance/grants.tf`'s `awscc_datazone_policy_grant.create_form_type`
  over the new `form_type_owners` (`avhvbqn37ty7m8 = "OWNER"`), on the root domain unit with
  `include_child_domain_units` false; `terraform validate` passes. **Planned** as `awsds-infra-data`:
  `1 to add, 0 to change, 0 to destroy`, the grant alone, so no other tree's apply is pending on the slice
  (Lesson 79). `docs/SMUS.md` gains the authorization beside the project and environment ones; the stage
  file's pre-window item 1 and decision 4, and the waiting list, follow. The apply waits on the user's
  word.

## 2026-11-10 — the `CREATE_FORM_TYPE` grant applied in Data Governance

- **[user]**, verbatim: *"Sim, aplique"*, to the apply of `data-governance/governance/`'s saved plan.
- **[Claude] Told** the one peer session on this repository, *EC2-Other cobrança diária com ambiente
  down*, before the apply; the other sessions on this machine are another repository's.
- **[Claude⚡] Applied** the saved plan as `awsds-infra-data` (the infrastructure user,
  `InfrastructureAccess`, Data Governance), 00:35:53 to 00:36:12 UTC:
  `awscc_datazone_policy_grant.create_form_type["avhvbqn37ty7m8"]` created in 7 s, *"Apply complete!
  Resources: 1 added, 0 changed, 0 destroyed."* The re-plan answers *"No changes. Your infrastructure
  matches the configuration."*
- **[Claude] Read back**: `list-policy-grants` on the root domain unit `bzq0cbh2gd0f4g` for
  `CREATE_FORM_TYPE` returns one grant, `00KsayGIrZ`: principal project `avhvbqn37ty7m8`, designation
  `OWNER`, `includeChildDomainUnits` false, created 00:36:00 UTC by the user profile `9e7cfd86-…`.
  `catalog.py` tabulates the domain unit's grants and judges only the two override types (`CT-9`), so no
  check moves. The form `classification` is the user's next act in the portal.

## 2026-11-10 — the form type `classification` created in the portal

- **[user]**, verbatim:
  > O form de metadata tb tem um campo `owning project`, que escolhi como sendo o `eighth-experimentation`.
  >
  > No formulário de campo, os campos disponíveis são:
  >
  > * display name (optional)
  > * technical name
  > * Description (optional)
  > * Field type
  > * minimum / maximum length (both optional)
  > * Search filters -> Searchable (checkbox)
  > * Requirement Options -> Required when publishing (checkbox) / Required when subscribing (checkbox)
  >
  > Preenchi apenas display e technical name, field type. Deixei os outros desmarcados.
- **[Claude] Read** at 00:45 UTC as `awsds-infra-sandbox-1` and `awsds-infra-data`, the two answers
  identical: `get-form-type` `classification` is revision `2`, `ENABLED`, owned by `avhvbqn37ty7m8`,
  created by the user profile `28f1b390-…` (the project's owner) at 00:44:24 UTC, its description
  *"The data product’s classification: public, internal, restricted or personal."*, no imports. Its
  Smithy model is one structure `classification` with one member `classification: String`, both
  displayed as `Classification`, with no required, length or searchable trait. `search-types` over the
  domain's non-managed form types returns it alone. Data Governance's `InfrastructureAccess`, no member
  of the project, reads the form type, where DataZone refuses it the project's assets.
- **[Claude] Read** Data Governance's trail since the apply: two `CreateFormType` calls from the portal
  through `awsds-data-studio-domain-execution` in the session `user-28f1b390-…`, answered revision 1 at
  00:41:53 UTC and revision 2 at 00:44:24 UTC, each with `owningProjectIdentifier` `avhvbqn37ty7m8` and
  `status` `ENABLED`; the trail redacts the model. `GetFormType`'s `createdAt` is the newest revision's.
  No other DataZone write since the apply. The list's item 1 is done; the window is next.
- **[user]**, verbatim: *"não entendi o motivo da vinculação de Owning Project ao metadata form, tendo em
  vista que o objetivo é compartilhar este mesmo form entre vários assets, entre vários projetos"*.
- **[Claude] Read** for the question, AWS's pages (the five URLs in `docs/REFERENCES.md`'s entry of
  2026-11-10): `CreateFormType` requires `owningProjectIdentifier`; only the owning project's members
  create, edit or delete a form; the portal lists every form in the domain; `DeleteFormType` refuses a
  form type an asset or asset type uses, and the portal deletes only a disabled form detached from every
  asset; no page says whether another project may attach a form. The CLI offers `create-`, `get-` and
  `delete-form-type`, no update. The answer in chat: the owner governs the form's edits, not its use,
  and decision 4's owner question stays 3.2's (xii), cheapest to change before 1.3 attaches the form.

## 2026-11-10 — pass 1's window

- **[user]**, verbatim: *"Abrir agora"*, to opening pass 1's window with the form as it stands, its
  owner `eighth-experimentation` kept as recommended and decision 4's owner question left to 3.2.
- **[Claude] Told** the peer session *EC2-Other cobrança diária com ambiente down* at 00:58 UTC: the
  hub's two hosts and Sandbox's `egress/` up for about an hour, then down.
- **[Claude] Read** `make status` at 01:01 UTC as the infrastructure user: `production/vpn`,
  `production/proxy` and `production/tooling` stopped, one instance each; `sandbox/egress` and every
  other metered slice down but Production's `app/app-etl` (3 resources) and `orchestration` (41), both
  at 0.0000 USD/h; the estimated burn 0.0000 USD/h. The readings' `since` is 00:58 UTC.
- **[Claude] A message from the peer session** *EC2-Other cobrança diária com ambiente down*, answered at
  01:33 UTC, information only: the user authorized there Stage 12 step 5.3's GitLab data-volume swap in
  Production (`make gitlab-up RUNNERS=0`, a backup, `production/tooling/` destroyed and re-applied, the
  restore), which uses the hub's proxy until the restore ends, and it asks that this window's
  `make hub-down` wait for its word. Nothing in the window reaches GitLab, and that sitting changes no
  Sandbox or Data Governance slice. The window's item 7 keeps `make down ENV=sandbox`; `make hub-down`
  goes to the later of the two sittings, the user's call.
- **[user]**, verbatim: *"Ambos no ar"*, after `make hub-up` and `make up ENV=sandbox ONLY=egress
  GROUPS=mwaa`.
- **[Claude] Read** at 01:34 to 01:35 UTC: `awsds-prod-vpn` and `awsds-prod-proxy` running since 01:28:07
  and 01:28:10 UTC, both status checks `ok`, `awsds-prod-gitlab` stopped. Sandbox's `egress/` is `UP`
  with 28 resources (0.18 USD/h by the static table): 19 interface endpoints created 01:28:49 to
  01:30:06 UTC, every one `available` with private DNS, `airflow-serverless` (the `mwaa` group) and
  `datazone` among them, beside the two gateway endpoints of 2026-08-16.
- **[user]** The space's `pass1.log`, pasted after run 1; its lines of record verbatim, the accounts
  redacted:

  ```
  == 2026-11-10T01:57:18Z the house image and the MWAA Serverless endpoint
  airflow-serverless.us-west-2.api.aws -> 10.20.50.217 (the mwaa group's endpoint)
  == 2026-11-10T01:57:18Z the product's database
  app_etl s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/
  == 2026-11-10T01:57:20Z deploy to dev
  2026-11-10 01:57:24,867 - smus_cicd.utils - WARNING - Failed to get group profile for 839bcde8-f8b8-4ada-936a-1441352db302: An error occurred (AccessDeniedException) when calling the GetGroupProfile operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: datazone:GetGroupProfile on resource: arn:aws:datazone:us-west-2:<Data Governance>:domain/dzd-d8yrvx1ko7im6o because no resource-based policy allows the datazone:GetGroupProfile action
  📊 Total files deployed: 21
  2026-11-10 01:58:38,326 - smus_cicd.datazone - INFO - No managed Tooling.GA/Tooling.Lightning blueprint found; will try the IAM connection fallback
  2026-11-10 01:58:51,355 - smus_cicd.airflow_serverless - INFO - Workflow app_etl_eighth_experimentation_app_etl already exists, updating it
  2026-11-10 01:59:07,241 - smus_cicd.airflow_serverless - INFO - Workflow app_etl_eighth_experimentation_app_etl_train already exists, updating it
  ✅ Deployment completed successfully!
  == 2026-11-10T01:59:11Z run1: start
  2026-11-10 01:59:14,105 - smus_cicd.airflow_serverless - WARNING - Failed to fetch tags for workflow app_etl_test_experimentation_app_etl: An error occurred (AccessDeniedException) when calling the ListTagsForResource operation: [...] because no identity-based policy allows the airflow-serverless:ListTagsForResource action
  📋 Run ID: J3chim3kbCEXWZl
  02:01:47Z run1 RUNNING | transform=RUNNING/-s
  02:03:18Z run1 RUNNING | process=RUNNING/-s transform=SUCCESS/113s
  02:11:20Z run1 RUNNING | process=SUCCESS/494s summarize=QUEUED/-s transform=SUCCESS/113s
  02:13:21Z run1 RUNNING | process=SUCCESS/494s publish=RUNNING/-s summarize=SUCCESS/7s transform=SUCCESS/113s write_result=SUCCESS/12s
  02:15:21Z run1 FAILED | process=SUCCESS/494s publish=FAILED/14s summarize=SUCCESS/7s transform=SUCCESS/113s write_result=SUCCESS/12s
  FATAL 2026-11-10T02:15:22Z run1: the run did not end in SUCCESS (exit 3); the session's laptop reads the task logs
  ```

  The same refusal of `GetGroupProfile` recurs at each storage item, and of `ListTagsForResource` on
  `test-experimentation`'s other two workflows.
- **[Claude] Read** `publish`'s task log as `awsds-infra-sandbox-1`: *"source run bjlb9a7r15lx1s:
  SUCCESS, {"added": 1, "failed": 0, "unchanged": 0, "updated": 0}"*, then *"RuntimeError: 0 asset(s)
  for app_etl/trades_notional in the project, one expected"* in `find_asset`. The source run, as
  `awsds-infra-data`: `PRIORITIZED`, created 02:12:55, run 02:12:57 to 02:12:59, updated 02:13:14 UTC,
  `lineageSummary.importStatus` `SUCCESS`, its snapshot the filter `app_etl` with `*`; its one activity
  `trades_notional` `SUCCEEDED_CREATED`, asset `4j6p77v7dm2840`. The search as
  `awsds-infra-sandbox-1` at 02:17 UTC answers that asset, `amazon.datazone.GlueTableAssetType`
  revision 24, created by `SYSTEM` at 02:12:58 UTC, its external identifier
  `arn:aws:glue:us-west-2:<Sandbox Account 1>:table/app_etl/trades_notional.avhvbqn37ty7m8`: the
  project's id suffixed to the table, which the match on `database/table` missed. The test double had
  written the identifier as `app_etl/trades_notional`, a shape nobody read (Lesson 78). No search item
  carries a revision.
- **[Claude] Found in the package**: macOS's `tar` wrote 37 AppleDouble entries (`._*`) beside the 26
  files, and macOS's own `tar -t` lists none of them (Lesson 62); the space's `tar` extracted them, and
  the deploy carried ten into the project's `shared/app-etl/`: four under `src/`, two under `glue/`,
  `inbox/._trades.csv` and three under `workflows/`. Spark's file listing skips names starting with
  `.`; the readings count the rows the job read against the sample's.
- **[Claude] Fixed** (`a858e376`): `names_table` takes the table with or without the project's suffix;
  `find_asset` asks the search again for up to 120 s while it answers nothing and fails at once on two
  matches; the result drops `asset_revision`; the double carries the item's shape as read. 69 passed,
  1 skipped; ruff clean; the pinned lint `ok: 9 arquivo(s)`. The package rebuilt from it with
  `COPYFILE_DISABLE=1`: 26 files and no AppleDouble entry by Python's `tarfile`, 246,784 bytes,
  sha256 `abfb21321596cbec…`; the first kept as `~/tmp/stage19-pass1-run1.tar` until the sitting ends.
  The rerun's run 1 is the job's second write of the table and the source's second run over an asset
  that exists, and its listing the first; 1.3 stays between the rerun's two runs.
- **[Claude] Correction** to the entry above on the double: the 2026-10-28 entry and `SUP-197` gave the
  subscriber's asset's external identifier as *"the resource link `glue_db_blerpkhn9nj7o0/trades`"*, the
  link and not the field. Read again 2026-11-10, the project's three assets carry the ARN with the
  project's suffix: `house-price` (the user's publish of 2026-09-13), `trades` (`cm329mc3bqu39s`, the
  subscriber's import of 2026-10-27) and `trades_notional`. The double's `app_etl/trades_notional`
  followed that prose, Lesson 38's identifier read out of prose, rather than a shape nobody read.
  `SUP-197` gains the reading, `SUP-343` the behaviour and `SUP-344` the form type's revisions.
- **[user]**, verbatim: *"faça rebase em relação à main"*. **[Claude]** `main` held one commit past the
  branch, `cc61288a` (#286, `docs/AWS_SUPPLEMENT.md`); the branch is pushed, and `CLAUDE.md` says a pushed
  branch is never rebased, so it took `origin/main` by a merge (`ea8dc1cf`), clean.
- **[user]** The space's `pass1.log` of the rerun, pasted after it stopped; its lines of record verbatim,
  the account redacted:

  ```
  == 2026-11-10T02:29:04Z the house image and the MWAA Serverless endpoint
  airflow-serverless.us-west-2.api.aws -> 10.20.50.217 (the mwaa group's endpoint)
  == 2026-11-10T02:29:04Z the product's database
  app_etl s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/
  == 2026-11-10T02:29:06Z deploy to dev
  📊 Total files deployed: 11
    📦 Operator code for 'app-etl' -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/operatorFiles/app-etl-1794277832078.zip
  2026-11-10 02:30:45,374 - smus_cicd.airflow_serverless - INFO - Successfully updated workflow: arn:aws:airflow-serverless:us-west-2:<Sandbox Account 1>:workflow/app_etl_eighth_experimentation_app_etl-VgCIaTD1xJ
  ✅ Deployment completed successfully!
  == 2026-11-10T02:31:02Z run1: start
  📋 Run ID: wf5GVes1RglmGsM
  02:33:39Z run1 RUNNING | transform=RUNNING/-s
  02:35:40Z run1 RUNNING | process=RUNNING/-s transform=SUCCESS/99s
  02:43:12Z run1 RUNNING | process=SUCCESS/493s summarize=QUEUED/-s transform=SUCCESS/99s
  02:45:13Z run1 RUNNING | process=SUCCESS/493s publish=RUNNING/-s summarize=SUCCESS/10s transform=SUCCESS/99s write_result=SUCCESS/7s
  02:47:13Z run1 FAILED | process=SUCCESS/493s publish=FAILED/138s summarize=SUCCESS/10s transform=SUCCESS/99s write_result=SUCCESS/7s
  FATAL 2026-11-10T02:47:13Z run1: the run did not end in SUCCESS (exit 3); the session's laptop reads the task logs
  ```

  The deploy carried 11 files where run 1's carried 21, the ten AppleDouble files gone; the refusals of
  `GetGroupProfile` and `ListTagsForResource` recur as in run 1.
- **[Claude] Read** `publish`'s task log at 02:48 UTC as `awsds-infra-sandbox-1`: *"source run
  dtqdppeykx4ivk: SUCCESS, {"added": 0, "failed": 0, "unchanged": 0, "updated": 1}"*, then *"RuntimeError:
  listing ct5d0innrgw3v4 revision 1 not ACTIVE after 120 s"* in `publish_asset`: the search found the
  asset this time. At 02:50 UTC, `get-listing` on `ct5d0innrgw3v4` answers revision 2 `ACTIVE`, created
  02:44:45.249 and updated 02:44:46.015 UTC, carrying asset revision 2; revision 1 answers `CREATING`, its
  `updatedAt` its `createdAt` (02:44:45.249 UTC); revision 3 does not exist. `get-asset 4j6p77v7dm2840`:
  revision 2, created 02:44:41.240 UTC by the source run's update, the first revision 02:12:58.834 UTC,
  `listing` `ct5d0innrgw3v4` `ACTIVE`, no description. Sandbox's trail holds one `CreateListingChangeSet`,
  at 02:44:45 UTC, by the project role's session `AmazonMWAAServerless` from `10.20.123.235`, on
  `4j6p77v7dm2840` with `PUBLISH`, answered `{"listingRevision": "1", "listingId": "ct5d0innrgw3v4"}`. The
  product is listed; the task waited on the revision the change set answered, which never activates
  (`SUP-345`).
- **[Claude] Fixed** (`db22976c`): `publish_asset` reads the listing at its latest revision until one at
  or past the change set's is `ACTIVE`, waits past an older one (the previous publication, the case of
  every later run), fails on a status other than `CREATING`, and returns the asset revision the listing
  carries; the timeout is read at call time. The double answers the measured shape: the change set's
  revision `CREATING`, the next `ACTIVE`. 71 passed, 1 skipped; ruff clean; the pinned lint `ok: 9
  arquivo(s)`.
- **[Claude] Rebuilt the package** from `db22976c` with `COPYFILE_DISABLE=1 tar --no-xattrs --no-acls
  --no-mac-metadata`: 26 files, no AppleDouble entry and no extended-attribute header by Python's
  `tarfile`, 211,456 bytes, sha256 `f025601521980f23…`. The previous build, `COPYFILE_DISABLE=1` alone,
  carried `LIBARCHIVE.xattr.com.apple.provenance` and `SCHILY.xattr.com.apple.provenance` headers on its
  37 members. `pass1.sh` gains `SKIP_RUN1=1`, which deploys and starts the second run alone.
- **[Claude] Proposed** one run after 1.3 in place of the two of the sitting's step 5: run
  `J3chim3kbCEXWZl` created the table and imported the asset (`added: 1`), and run `wf5GVes1RglmGsM`
  overwrote the table, updated the asset (`updated: 1`) and made the first listing, so 1.2 is run and
  1.4's source half read; one run after 1.3 answers whether the listing gains a revision (1.4) and whether
  the form travels to it (1.3, verification iv). The choice is the user's.
- **[Claude] A message from the peer session** *EC2-Other cobrança diária com ambiente down*, received
  after 02:55 UTC: its GitLab sitting (Stage 12 step 5.3) has ended, GitLab `stopped` at 02:49:05 UTC by
  the user's `make gitlab-down` and no interface endpoint in Production at 02:55:18 UTC, the hub's VPN and
  proxy `running`; `make hub-down` is this window's again at its end. Its host is now
  `i-010c8217a1b3062dc` (`10.30.6.245`), the data volume 20 GiB, the restore read as before (6 projects,
  `main` at `8d50f685`, 14 tags); `production/tooling/` was applied from PR #285's branch, so no plan or
  apply of that slice before its merge (Lesson 79); the GitLab local user's password rotation is left to
  the next GitLab sitting, this pass's mirror.
- **[user]**, verbatim: *"Sim, uma run"*, to the proposal above: 1.3 written in the portal first, then
  the third package with `SKIP_RUN1=1 NEGATIVE=1`, its one run and verification ii's negative.
- **[user]**, verbatim: *"Segue o log. Veja se está ok, pois aparentemente terminou com erro. Vou manter o
  ambiente no ar até você analisar. Estando tudo ok, me avise para derrubar o ambiente, ou para rodar um
  novo teste."* The third package's `pass1.log`, its lines of record verbatim:

  ```
  == 2026-11-10T03:07:26Z the identity: this space must be eighth-experimentation's
  the project role: SageMaker
  == 2026-11-10T03:07:28Z the house image and the MWAA Serverless endpoint
  airflow-serverless.us-west-2.api.aws -> 10.20.50.217 (the mwaa group's endpoint)
  == 2026-11-10T03:07:30Z deploy to dev
  📊 Total files deployed: 11
  ✅ Deployment completed successfully!
  == 2026-11-10T03:09:18Z run1 skipped (SKIP_RUN1=1): the first publication is run wf5GVes1RglmGsM's, and 1.3 was written before this start
  == 2026-11-10T03:09:18Z run2: start
  📋 Run ID: hiErIl5sGJSyRFx
  03:11:53Z run2 RUNNING | transform=RUNNING/-s
  03:13:54Z run2 RUNNING | process=RUNNING/-s transform=SUCCESS/94s
  03:21:26Z run2 RUNNING | process=SUCCESS/490s summarize=QUEUED/-s transform=SUCCESS/94s
  03:23:27Z run2 RUNNING | process=SUCCESS/490s publish=RUNNING/-s summarize=SUCCESS/7s transform=SUCCESS/94s write_result=SUCCESS/12s
  03:25:27Z run2 FAILED | process=SUCCESS/490s publish=FAILED/18s summarize=SUCCESS/7s transform=SUCCESS/94s write_result=SUCCESS/12s
  FATAL 2026-11-10T03:25:28Z run2: the run did not end in SUCCESS (exit 3); the session's laptop reads the task logs
  ```

  The script stops at the `FATAL`, so verification ii's negative did not run.
- **[Claude] Read** at 03:28 to 03:31 UTC as `awsds-infra-sandbox-1`. `publish`'s task log: *"source run
  5bzy0z4wh4sr2o: SUCCESS, {"added": 0, "failed": 0, "unchanged": 0, "updated": 1}"*, then
  *"RuntimeError: listing ct5d0innrgw3v4 revision 3 is UPDATING"*. The listing: revision 4 `ACTIVE`,
  updated 03:23:01.355 UTC, carrying asset revision 6; revision 3 `ACTIVE`, updated 03:23:00.426 UTC,
  carrying asset revision 2; revision 2 `ACTIVE` and revision 1 `CREATING` as before; revision 5 absent.
  Sandbox's trail: `CreateListingChangeSet` at 03:23:00 UTC by the project role's session
  `AmazonMWAAServerless` from `10.20.40.253` through `vpce-09e2724f4cf1ea60c`, the
  `com.amazonaws.us-west-2.datazone` interface endpoint with private DNS, answered
  `{"listingRevision": "3", "listingId": "ct5d0innrgw3v4"}`. `list-asset-revisions`: 1 and 2 by `SYSTEM`
  (02:12:58 and 02:44:41 UTC), 3 to 5 by the data scientist's profile `28f1b390-…` at 03:04:05, 03:05:51
  and 03:06:10 UTC (1.3), 6 by `SYSTEM` at 03:22:56 UTC (the source run). Revision 6 keeps 1.3's
  metadata: the description *"trades_notional description"*, the README in `AssetCommonDetailsForm` and
  `classification` `{"classification": "internal"}` (form revision 2). Listing revision 4 carries all
  three, beside `SubscriptionTermsForm` `approvalRequired` `YES`. The CLI's model (aws-cli 2.37.12) lists
  `ListingStatus` as `CREATING`, `ACTIVE`, `INACTIVE`: no `UPDATING`. So 1.3 is read (the source run's
  update keeps the business metadata, and the form travels to the listing: verification iv's first
  half), 1.4 is read (each republication adds two listing revisions, the change set's and the
  publication), and the change set takes the `datazone` endpoint (verification ii). The product is
  republished; the task failed on a status it did not know (`SUP-345`).
- **[Claude] Fixed** (`ee6b8525`): the task waits for a listing revision past the change set's, the one
  carrying the publication in both readings, with `CREATING` and `UPDATING` pending. The fix of
  `db22976c` took a revision at or past the change set's, which on this republication would have taken
  revision 3's previous asset revision for the publication. The double models both readings. 72 passed,
  1 skipped; ruff clean; the pinned lint `ok: 9 arquivo(s)`.
- **[user]**, verbatim: *"aproveite para fazer rebase em relação à main"*. **[Claude]** `main` held one
  commit past the branch, `2d63dacc` (#285, Stage 12 step 5.3); the branch is pushed, so it took
  `origin/main` by a merge (`1f93e61b`), clean, `examples/app-etl/` unchanged by it.
- **[Claude] Rebuilt the package** from `ee6b8525`, identical at `1f93e61b`: 26 files, no AppleDouble entry
  and no extended-attribute header by Python's `tarfile`, 212,480 bytes, sha256 `1a452386c0a4605d…`;
  `pass1.sh` as the third package's.
- **[Claude] Proposed** a fourth run with `SKIP_RUN1=1 NEGATIVE=1`: the task's first `SUCCESS`, a second
  reading of a republication's revisions, which the fix relies on, and verification ii's negative. The
  choice is the user's.
- **[user]**, verbatim: *"Sim, rodar de novo"*, to the fourth run: the fourth package with
  `SKIP_RUN1=1 NEGATIVE=1`, 1.3 not rewritten.
- **[Claude] A message from the peer session** *EC2-Other cobrança diária com ambiente down*, received
  during the fourth run: the user authorized `production/tooling/`'s apply, which changes the S3 object
  `gitlab.rb` alone (GitLab 19.2's NGINX keys), and a short GitLab session (`make gitlab-up RUNNERS=0`,
  `awsds-gitlab-refresh` on the host, `make gitlab-down`, 10 to 15 minutes up); `make hub-down` waits for
  its word that GitLab is down, since `make gitlab-up` refuses with the proxy stopped; no Sandbox, Staging
  or Data Governance slice changes. This window's end becomes `make down ENV=sandbox`, then
  `make hub-down` on the peer's word.
- **[user]**, verbatim: *"segue o `pass1.log`"*. The fourth package's log, its lines of record verbatim:

  ```
  == 2026-11-10T03:40:30Z the identity: this space must be eighth-experimentation's
  == 2026-11-10T03:40:33Z deploy to dev
  📊 Total files deployed: 11
  ✅ Deployment completed successfully!
  == 2026-11-10T03:42:24Z run1 skipped (SKIP_RUN1=1): the first publication is run wf5GVes1RglmGsM's, and 1.3 was written before this start
  == 2026-11-10T03:42:24Z run2: start
  📋 Run ID: MmFs38SsxUFQ2xM
  03:45:00Z run2 RUNNING | transform=RUNNING/-s
  03:47:01Z run2 RUNNING | process=RUNNING/-s transform=SUCCESS/121s
  03:54:33Z run2 RUNNING | process=SUCCESS/463s summarize=QUEUED/-s transform=SUCCESS/121s
  03:56:33Z run2 SUCCESS | process=SUCCESS/463s publish=SUCCESS/20s summarize=SUCCESS/11s transform=SUCCESS/121s write_result=SUCCESS/8s
  == 2026-11-10T03:56:34Z verification ii's negative: test-experimentation's Glue source, started as this project's role
  {
      "id": "dn5hi8qtcminbk",
      "status": "REQUESTED"
  }
  exit 0
  == 2026-11-10T03:56:36Z DONE. Stop the space (Compute -> Spaces), close every portal tab, then on the laptop: make down ENV=sandbox, make hub-down, make status
  ```
- **[Claude] Read** at 03:58 to 04:01 UTC as `awsds-infra-sandbox-1`. `publish`'s task log: *"source run
  6bnfg5dk961bps: SUCCESS, {"added": 0, "failed": 0, "unchanged": 0, "updated": 1}"*, *"listing
  ct5d0innrgw3v4 revision 6: ACTIVE, asset revision 7"*, and the XCom `{"asset": "4j6p77v7dm2840",
  "asset_revision": "7", "listing_revision": "6", "published": true, "source_run": "6bnfg5dk961bps", …}`:
  the task's first `SUCCESS`. Sandbox's trail: the change set at 03:56:05 UTC from `10.20.117.132`
  through `vpce-09e2724f4cf1ea60c`, answered revision 5. The listing: revision 5 `ACTIVE` at
  03:56:05.061 UTC carrying asset revision 6, revision 6 `ACTIVE` at 03:56:06.592 UTC carrying asset
  revision 7, revision 7 absent; the asset's revision 7 by `SYSTEM` at 03:56:00.659 UTC, its description
  kept. The third reading of `SUP-345`'s model: the publication is the revision past the answered one.
- **[Claude] Read the negative**, as `awsds-infra-sandbox-1` and `awsds-infra-data`: run `dn5hi8qtcminbk`
  of `test-experimentation`'s (`4gqfau9xuo6e4w`) source `3zp6fog9jep1qo` over `glue_db_4zojr4rr6bmnww`,
  `publishOnImport` false: `PRIORITIZED`, `SUCCESS`, run 03:56:37.5 to 03:56:38.5 UTC, every statistic
  0, `lineageSummary.importStatus` `SUCCESS`. Sandbox's trail and Data Governance's, one shared event:
  `StartDataSourceRun` at 03:56:35 UTC by `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`'s session
  `SageMaker` from `10.20.44.67` through `vpce-09e2724f4cf1ea60c`, no error, answered
  `{"id": "dn5hi8qtcminbk", "status": "REQUESTED"}`. The caller's DataZone profile, `a06a10c7-…` (`IAM`,
  that role's ARN), is a `PROJECT_CONTRIBUTOR` of `eighth-experimentation` alone: `test-experimentation`'s
  members are the data scientist (`PROJECT_OWNER`), its own project role's profile `084a724b-…`, and the
  group profiles `839bcde8-…` (Sandbox's `InfrastructureAccess`) and `06d426f2-…`. Verification ii's
  negative half is answered against the plan: DataZone admits a project role's start of a source in a
  project it is no member of, and the one control left is IAM's `datazone:StartDataSourceRun` on the
  domain's ARN, `awsds-sandbox-workflows` `v4`'s statement (`SUP-346`). The run imported nothing.
- **[Claude] Two messages from the peer session** *EC2-Other cobrança diária com ambiente down*: its short
  GitLab session's refresh ended and was read at 03:59 UTC, and `make gitlab-down` follows; it asked
  whether this session uses GitLab. **[Claude] Answered** at 04:00 UTC: GitLab unused here, the mirror to
  `awsds/app-etl` left to the next GitLab sitting with the local user's password rotation, and
  `make hub-down` waiting for its word that the host is `stopped`.
- **[Claude] A message from the peer session** *EC2-Other cobrança diária com ambiente down*, received
  after 04:01 UTC, information only: GitLab `stopped` since 04:01:25 UTC, so `make hub-down` is this
  window's again.
- **[user]**, verbatim: *"Sim, prossiga"*, to the readings after the window and the preparation of a
  decision on `SUP-346`.
- **[Claude] Read the window's end** as the infrastructure user: Sandbox's trail holds `egress/`'s
  `DeleteVpcEndpoints` at 04:00:59 UTC, Production's the hub's two `StopInstances` at 04:09:47 and
  04:09:50 UTC (GitLab's at 04:01:26 UTC, the peer's). `make status` at 04:25 UTC: `production/vpn`,
  `production/proxy` and `production/tooling` stopped, `sandbox/egress` down, Production's `app/app-etl`
  (3) and `orchestration` (41) as at 01:01 UTC, the burn 0.0000 USD/h. Sandbox holds no SageMaker app
  but `Deleted` ones, the space's JupyterLab app `jup8gb` (created 01:40:12 UTC) among them.
- **[Claude] The readings of 1.2 to 1.4** (step 8): the session's script ran 04:05 to 04:06 UTC as
  `awsds-infra-sandbox-1` and `awsds-infra-data` with `NO_PROXY='*'`, since 00:58 UTC, 55 calls answered
  and two refused (verification v below), then single reads to 04:40 UTC:
  - **Verification i**: the project role's session `GlueJobRunnerSession` created
    `app_etl.trades_notional` at 02:01:27 UTC, `glue:CreateTable` from `10.20.61.79` through
    `vpce-08ef07f449aeea464` (`com.amazonaws.us-west-2.glue`, created 01:29:16 UTC). The table:
    `TableType` `EXTERNAL_TABLE`, `table_type` `ICEBERG`, `IsRegisteredWithLakeFormation` true, six columns
    (`trade_date`, `desk`, `instrument`, `quantity`, `price`, `notional`), its location the database's
    `LocationUri`, `…/avhvbqn37ty7m8/dev/data/catalogs/trades_notional`, not the `--conf` warehouse under
    `tables/`: Iceberg's Glue catalog takes a database's location first. `UpdateTable` at 02:33:16,
    03:11:22 and 03:44:53 UTC by the same session and endpoint, `skipArchive` true: the table at version
    3, one version kept, its creation time unchanged. The database's Lake Formation grants are the
    conditioned `IAMPrincipals` `CREATE_TABLE`, `DESCRIBE` and `DROP`, the provisioning role's and the
    manage-access role's, so the conditioned `CREATE_TABLE` admitted the job's session; on the table the
    project role holds `ALL`, `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT`, each grantable,
    the creator's.
  - **The rows**: each of the four Glue runs logged *"read 10 row(s)"*, wrote 10 to the Parquet path and
    10 to `glue_catalog.app_etl.trades_notional` (`datazone-avhvbqn37ty7m8-dev/output`): the sample's ten
    rows, so `inbox/._trades.csv` was not read.
  - **Verification ii**: the four `StartDataSourceRun` on `budryu9mt9y5u8` (02:12:55, 02:44:38, 03:22:54
    and 03:55:58 UTC) and the three `CreateListingChangeSet` (02:44:45, 03:23:00 and 03:56:05 UTC) are the
    project role's session `AmazonMWAAServerless`, one worker address in `10.20.0.0/16` per run, every
    call through `vpce-09e2724f4cf1ea60c`, no error, each one shared event in both trails. Of the role's
    policies read 2026-11-08, `SageMakerStudioProjectRoleMachineLearningPolicy`'s `CreateListingChangeSet`
    on `*` admits the change set and `awsds-sandbox-workflows` `v4` on the domain's ARN is the one grant of
    `StartDataSourceRun`. The negative is the entry above's.
  - **Verification iii**: the source's filter is `app_etl` with `*`; run `bjlb9a7r15lx1s` `added: 1`
    (`SUCCEEDED_CREATED`), then `dtqdppeykx4ivk`, `5bzy0z4wh4sr2o` and `6bnfg5dk961bps` `updated: 1`
    (`SUCCEEDED_UPDATED`); the scheduled run `bp4qjoy7ptpwgg` (2026-11-09 23:47:48 UTC, the 23:41 cron)
    imported nothing. With `publishOnImport` false the asset stayed unlisted from its import at 02:12:58
    UTC to the task's first change set at 02:44:45 UTC, neither trail holding one between. The asset at
    revision 7 carries `GlueTableForm` (type revision 13), `DataSourceReferenceForm` (the source and its
    latest run), `SubscriptionTermsForm`, `AssetCommonDetailsForm` and `classification`, its listing
    `ACTIVE`.
  - **Verification v**: 92 `PostLineageEvent`, 23 per Glue run, as `GlueJobRunnerSession` through the
    `datazone` endpoint, each one shared event in both trails; `list-lineage-events` answers 92 items, each
    `SUCCESS`, `createdBy` the project role's profile. Data Governance's trail holds 16 `CreateLineageNode`
    by `datazone.amazonaws.com`, ids and `sourceIdentifier` in `additionalEventData`: nine job nodes and
    five dataset nodes during the first run (02:00:59 to 02:01:38 UTC), the Glue table's `d0m1zl6r8q3uvk`
    among them (its `sourceIdentifier` the table's ARN, its name the S3 location); the asset's
    `aqp9vg9lq7dsb4` (`amazon.datazone.asset/4j6p77v7dm2840`) at the import, 02:13:15 UTC; the listing's
    `5v236akrsvu74g` at the publication, 02:45:02 UTC. `get-lineage-node` chains them: the `inbox`
    prefix's node, the job run `arcyltahr9rxn4` (`atomic_replace_table_as_select`, its event 03:44:53 UTC),
    the table's node, the asset's and the listing's. The domain carries the job's lineage to the asset;
    whether the portal draws it on the asset's page is the user's look. The script's `get-lineage-node`
    and `list-lineage-node-history` on the asset's id answered `ResourceNotFoundException`: an asset id is
    no node identifier, and the table's node refuses its own `sourceIdentifier` (`SUP-347`).
  - **The AppleDouble objects**: run 1's ten `._*` objects (163 bytes each, uploaded 01:58:03 to 01:58:37
    UTC) are still under `shared/app-etl/`, two under `glue/`, `inbox/._trades.csv`, four under `src/` and
    three under `workflows/`; the three later deploys, 11 files each, removed none (`SUP-348`). Deleting
    them is an S3 write, the user's call.
  - **`./aws/catalog.py`**: all checks passed. Against 2026-11-08's reading (9 listings, 7 sources): 10
    listings, the tenth `trades_notional` at revision 6; 9 sources, each `publishOnImport` false (`CT-4`),
    the two new ones `app_etl`'s (created 2026-11-08 23:41:28 UTC, 5 runs `SUCCESS`) and
    `test-experimentation`'s `test_project_database` source, from the `DataLake` environment the data
    scientist's portal session created there on 2026-11-09 at 19:53:02 UTC; the same session's second,
    `mydatabase`, 19:53:53 UTC, reads `VALIDATION_FAILED`. `eighth-experimentation` holds six environments,
    2026-11-08's five and `app_etl`'s.
- **[Claude] Read for `SUP-346`'s decision**: the Service Reference's DataZone JSON (`v1.5`, 278 actions,
  read 2026-11-10) gives `StartDataSourceRun` no resource type and no condition key, as it gives
  `CreateListingChangeSet`, `PostLineageEvent`, `GetLineageNode`, `CreateDataSource` and
  `UpdateDataSource`; its one resource type is `domain`, and it maps `datazone:domainId`,
  `datazone:projectId` and `datazone:userId` to no action, as on 2026-10-18 (`SUP-191`). Run 1's refusals
  of `GetGroupProfile` name the domain's ARN as the resource, and `v4`'s statement on that ARN is the role's
  one grant of `StartDataSourceRun`: DataZone authorizes against the domain whatever the reference lists,
  and IAM narrows the call to the domain and no further. `StartDataSourceRun`'s API page says nothing on who
  may call it. The HTML Service Authorization Reference answered its title alone to the fetch.
- **[user]**, verbatim, during the writing: *"revisite o restante do plano para o estágio 19 e avance no
  que for possível neste momento sem subir o ambiente. adiante a preparação das próximas etapas no que for
  possível. atualize o log com seu avanço e suba o progresso no mesmo PR."*
- **[Claude] The session's packages deleted from the laptop**: `~/tmp/stage19-pass1.tar` and
  `~/tmp/stage19-pass1-run1.tar`, whose `pass1.sh` carried the Production registry's account id,
  `~/tmp/stage19-readings.sh` and the scratchpad's four package copies. The user's saved copies of
  `pass1.log` carry account ids too, the user's to keep or delete.
- **[Claude] 3.1's code reading**, in the CLI 1.0.9 `uv tool` installed on the laptop
  (`aws-smus-cicd-cli`): `commands/bundle.py` takes the first stage `--targets` names, or the stage whose
  `stage` is `DEV` when none, and `helpers/catalog_export.py` exports every catalog resource that stage's
  project owns, with no filter from the manifest. Its calls are `Search` with `owningProjectIdentifier`
  over `ASSET`, `DATA_PRODUCT`, `GLOSSARY` and `GLOSSARY_TERM`, `GetAsset` or `GetDataProduct` per item,
  and `SearchTypes` with `managed` false, a type kept when its `owningProjectId` is the project's. The
  same searches as `awsds-infra-sandbox-1` at 04:41 UTC: `test-experimentation` owns no asset, product,
  glossary or term, and the one custom form type its search answers, `classification`, is
  `eighth-experimentation`'s; `eighth-experimentation` owns the assets `house-price`, `trades` and
  `trades_notional`, the product `my-data-product` and `classification`. The template's `test-deploy`
  bundles the `test` stage, so its export would be empty, while decisions 4 and 14 assumed the product's
  metadata travels from `dev`: decision 18 written, the user's, (c) recommended, the metadata kept as code
  in the template and written on the asset by `publish`.
- **[Claude] Read for pass 2's order** as `awsds-infra-sandbox-1` and `awsds-infra-data`, 04:41 to 04:42
  UTC: `eighth-experimentation`'s members are the data scientist (`PROJECT_OWNER`), the project role's
  profile (`PROJECT_CONTRIBUTOR`, the `createdBy` of pass 1's lineage events) and Sandbox's
  `InfrastructureAccess` group (`PROJECT_CONTRIBUTOR`); the Governance Manager is no member yet. The
  `experimentation` profile holds 14 configurations: `Tooling` `ON_CREATE` at order 0, the other 13
  `ON_DEMAND`, `DataLake` at order 1 and `SageMakerAIDomain` at 13. A consumer created in the portal
  therefore holds `Tooling` alone, and 2.2's `DataLake` environment is an act of its own.
- **[Claude] Written with nothing up**: pass 2's sitting in order in the stage file, its portal half
  needing no window and its window the hub with Sandbox's `egress/` and no `GROUPS`, the consumer role's
  reads for decision 17 and xi's negative in one block; pass 4 read against pass 1, decisions 17 and 18
  bearing on 4.4, 3.3 and 4.13, and 4.10 reading pass 1's shapes (`SUP-345`, `SUP-347`) and the shared
  root after each deploy (`SUP-348`, `SUP-287`); 6.1's cross-project start check under decision 17 (a) and
  6.3's note on `TM-29`; `runbooks/sagemaker-application.md` §D on a tar built on a Mac (`SUP-348`).
  `waiting-on-the-user.md` gains decision 18 and pass 2's portal acts. No AWS write; the work joins
  [PR #284](https://github.com/felipenoris/AWS-DataScience/pull/284).

## 2026-11-11 — decision 17 taken and `CT-13` written; SMUS's own path read for decision 18

- **[user]**, verbatim: *"Ok em relação à recomendação na Decisão 17. Já na Decisão 18, qual é o caminho
  natural de uso do SMUS ?"*
- **[Claude] Decision 17 recorded as (a) with (d)**: the stage file, `TM-29` accepted, and the waiting
  list, which drops decision 17's row and gains (d)'s report as an act of the user's.
- **[Claude] `CT-13` written in `aws/catalog.py`**: `lookup-events` for `StartDataSourceRun` in
  Sandbox's and Data Governance's trails. Sandbox's copy is read first: the domain's copy of a
  cross-account call carries the caller's account and the role's id alone (`userIdentity.type`
  `AWSAccount`, read on verification ii's event). The registry's copy of the same request and every
  refused call are skipped. A project role's start is judged against the source's project from
  `ListDataSources`, and verification ii's request id (`01d1d646-…`) is a note through
  `MEASURED_CROSS_PROJECT_STARTS`. The classifier was exercised on eight fabricated events (own,
  cross, measured, an administrator, the service, unresolved, an Identity Center session, an unknown
  source), each answered as expected and no e-mail address reaching a caller label. Run from 02:04 UTC
  as `awsds-infra-sandbox-1` and `awsds-infra-data`: all checks passed, `CT-13` a note. It read six
  starts in CloudTrail's 90 days:
  - four by `eighth-experimentation`'s role on its own source `budryu9mt9y5u8`, pass 1's;
  - verification ii's start of `3zp6fog9jep1qo`, the measured note;
  - one on 2026-10-22 at 00:34:06 UTC by an Identity Center session in Data Governance, on
    `aqm5tebc42cufk`, a source no longer listed. Its event carries no session issuer and an
    `onBehalfOf` user, and its principal id carries the person's e-mail address, which the check drops.
- **[Claude] SMUS's own path read for decision 18**: AWS's catalog import and export guide, the
  manifest's page and the user guide's CI/CD page, through a fetching agent, and the CLI 1.0.9's
  `helpers/catalog_import.py` and `commands/deploy.py`:
  - the guide exports from the source project, its example the `dev` environment, every resource that
    project owns with no filter, shared-in resources and managed types excluded; no page asks for a
    project dedicated to one application;
  - the import matches an asset by its `externalIdentifier` without account and Region, or by name, and
    writes a revision on a match or creates the asset; it creates a custom form type the target project
    does not own, deletes nothing, and publishes what was `ACTIVE` in the source unless `skipPublish`;
  - the guide lists a name another project owns as a partial failure, and `deploy` fails only when every
    catalog import fails; the user guide maps each stage to an independent project;
  - the guide presents the export as the catalog versioned with the code, assumes the same Glue names in
    every stage, and never addresses stages that share one domain.
  Decision 18 now carries SMUS's path and option (d), a `dev` project for the application alone, and the
  recommendation moves from (c) to (d) under decision 6 (b)'s criterion; the waiting list's row follows.
- **[Claude] (d)'s report drafted** for the user to send to AWS, through a support case or the console's
  feedback:

  ```text
  Subject: Amazon DataZone (SageMaker Unified Studio) admits StartDataSourceRun from a non-member

  In a SageMaker Unified Studio domain in us-west-2 (dzd-d8yrvx1ko7im6o), the IAM role of project A
  started a data source owned by project B, of which the role's DataZone user profile is not a member.

  - Caller: project A's role, datazone_usr_role_<project A>_<environment>, from a SageMaker space;
    its user profile is a PROJECT_CONTRIBUTOR of project A only.
  - Call: StartDataSourceRun on project B's data source 3zp6fog9jep1qo, 2026-11-10 03:56:35 UTC,
    request id 01d1d646-13a9-434c-848c-13df03911521.
  - Result: no error, the response REQUESTED, the run SUCCESS (it imported nothing new).
  - The role's one grant of the action is datazone:StartDataSourceRun on the domain's ARN, which a
    workflow needs to start its own project's data source before it publishes.
  - The Service Authorization Reference lists no resource type and no condition key for
    StartDataSourceRun, and maps datazone:projectId to no action, so IAM cannot scope the grant to
    the caller's own project.

  Questions:
  1. Is DataZone expected to check project membership for StartDataSourceRun, as it does for
     GetAsset?
  2. If not, can a resource type or a condition key such as datazone:projectId be added for it?
  ```

## 2026-11-11 — decision 18 taken; the import's forms and Sandbox's one catalog read

- **[user]**, verbatim: *"A decisão 18 pela recomendação nativa (d) está ok. Vc entende que a decisão 17
  tb está indo na recomendação nativa do SMUS?"*
- **[Claude] Decision 18 recorded as (d)**: the stage file's record, decisions 4 and 14 and steps 3.1 and
  3.3 amended, and step 1.5 written, pass 1 again in a project for app-etl alone after pass 2.
- **[Claude] The CLI 1.0.9's import read again** for the question on decision 17, in
  `helpers/catalog_export.py`, `helpers/catalog_import.py`, `commands/deploy.py` and
  `bootstrap/handlers/`:
  - the export keeps each asset's forms as `GetAsset` answers them; the import remaps the
    `DataSourceReferenceForm` to the target project's source over the same database name, or strips it,
    and each form type's revision, and writes every other form unchanged, the exported forms replacing
    the target asset's on a revision;
  - on pass 1's asset as read on 2026-11-10, `GlueTableForm`'s `catalogId` and `tableArn` and
    `AssetCommonDetailsForm`'s `sourceIdentifier` carry the account, and so does the
    `externalIdentifier`, which the import's `create_asset` passes unchanged;
  - `deploy` runs the bundle's deployment, its catalog import included, then the bootstrap actions;
  - no bootstrap handler starts a data source: they cover workflows, MWAA Serverless runs, connections,
    QuickSight datasets, printing and waiting.
- **[Claude] Sandbox's Glue databases read** as `awsds-infra-sandbox-1` (`InfrastructureAccess`):
  `get-databases` lists both projects' databases in one catalog, `app_etl` among
  `eighth-experimentation`'s, so decision 2 (d)'s name cannot be created in a second Sandbox project.
- **[Claude] Decision 19 written**, the user's: where the import is first read and the product database
  in `test`, (a) recommended, Staging importing unlisted and `test` on a database of its own. The waiting
  list's decision 18 row becomes decision 19's.
- **[Claude] Decision 17 read against SMUS's own path**, the user's question, as a note in the stage
  file: the import, the listing and DataZone's authorization are SMUS's own, the start from the task the
  house's. (b) keeps AWS's own trigger, the schedule, so decision 17's sentence that (b) gives up the
  native path was imprecise: (b) gives up decision 3 (a)'s order. Under decision 18 (d) the task's start
  is what returns a target's table to its asset after the import.

## 2026-11-11 — decision 19 taken: every promotion across accounts

- **[user]**, verbatim: *"Esse é um bom ponto: o glue catalog é único para a conta toda. Logo o que está
  em desenvolvimento no sandbox compartilha o mesmo namespace do estágio test. Neste caso, considerando a
  necessidade de haver isolamento entre ambientes, entendo que o ideal seria promover sempre entre contas
  diferentes. Ou seja, não haveria estágio test. A esteira de promoção seria sandbox -> staging ->
  production. O q vc acha?"*
- **[user]**, verbatim, during the answer: *"Outra coisa: em sandbox, o data scientist deveria poder ver o
  catálogo de produção como read-only. Neste caso, ele verá dois catálogos (um do sandbox e outro do
  production), com potencialmente nomes de bases de dados repetidas?"*
- **[Claude] Read for the answer**, with nothing up: D41 item 3 and its consequences (the `test` project
  as the CLI's one stage beyond `dev` while the targets held no project), the manifest's `test` stage
  (`workflow.create` and `workflow.run` with `trailLogs`), and `runbooks/promotion.md`'s release sitting,
  which raises Sandbox's `egress/` for `test-deploy`'s run. As `awsds-infra-sandbox-1`
  (`InfrastructureAccess`), `glue get-database` on `curated` and `raw`: both are resource links to
  databases of the same names in another account's catalog.
- **[Claude] Answered**: retiring `test` agreed with, with the reasons and what it changes. Sandbox's
  engines see one Glue catalog, a Production table entering it as a resource link with a local name; the
  domain's business catalog is one for every account and would show `dev`'s and Production's product
  under one name, so Production alone listing was recommended.
- **[user]**, verbatim: *"Sim, registre"*
- **[Claude] Decision 19 recorded as (c)**, with (a)'s Staging half: decisions 2, 3, 10 and 14 amended,
  steps 3.1, 3.2, 3.3 and 4.13, verifications xii, xvii and xxv, the decisions and stages tables, 6.2 and
  the other sessions' list; pass 3's heading names the bundle and the manifest's stages. D41 item 3
  amended in its file and its index row. Decision 20 written, the user's, (b) recommended: Production
  alone lists. The waiting list's decision 19 row becomes decision 20's.

## 2026-11-11 — decision 20 taken: Production alone lists a chain application's product

- **[user]**, verbatim: *"(b) Só Production"*
- **[user]**, verbatim, during the record: *"No contexto da decisão 20, entendo que isso se refere aos
  aplicativos que fazem parte da esteira de promoção entre ambientes. Mas, mesmo seguindo com a publicação
  da listagem só em production, um usuário poderia publicar em dev se quisesse?"*
- **[Claude] Read for the answer**, with nothing up: `docs/SMUS.md`'s deployment-project section and Stage
  18's verification iv, where a member of any designation acts as the project role in the portal, the V2
  domain refusing the catalog designations; and `sandbox/workflows/main.tf`'s note that AWS's
  `SageMakerStudioProjectRoleMachineLearningPolicy` (v47) grants the project role `CreateListingChangeSet`
  on every resource.
- **[Claude] Decision 20 recorded as (b)**, scoped to the applications in the promotion chain: decisions 3
  and 14, 1.5 and 6.1 amended, the waiting list's row removed. The record says the gate is the template's
  default, not a control: a member of the `dev` project still lists from the portal or from code, `CT-12`'s
  successor judges that listing's classification, and 6.1's checks note it without failing.
- **[Claude] Answered**: yes, `PUBLISH_LISTING` false binds the template and no one else. A member of the
  `dev` project lists from the portal or from code in a space, both as the project role, which AWS's
  policy (v47) grants `CreateListingChangeSet` on every resource; `CT-12`'s successor and 6.1's note cover
  such a listing. A deny of `CreateListingChangeSet` on that role would prevent it and is not
  recommended: one call publishes and unpublishes, the Service Reference giving it no condition key
  (read 2026-11-10), and the listing code's exercise in `dev` takes both.
- **[user]**, verbatim: *"Mais tarde"*, to starting pass 2's portal acts; they stay in the waiting list.

## 2026-11-11 — the branch checked against `main` and the log reviewed

- **[user]**, verbatim: *"sincronize a branch com a main. revise o log para garantir que todas as
  informações estão atualizadas e suba no PR."*
- **[Claude] The branch**: `origin/main` at `0f20b98c` (#287) is already in it, merged at `78c27358` on
  2026-11-10 at 04:51 UTC, a merge this log had not recorded; nothing to merge.
- **[Claude] The review**, this log against the branch's commits from `6370da60` to `3660a6ab`, the stage
  file, the indexes and the waiting list, with no AWS call:
  - the entries of decisions 17 to 20 leave out two files each of their commits changed, `CLAUDE.md`'s
    Current position and this log's index row (`2d705592`, `96972fac`, `2c15ed27`, `3660a6ab`);
  - `docs/plan/stages/INDEX.md` and `docs/GENERAL_PLAN.md` still read pass 1's sitting as not run: the
    stage index's row brought to it and to decisions 17 to 20, the plan's to it and to 19 and 20, inside
    its 40,000-byte cap (39,987 after);
  - the stage file's decision 20 gains the deny weighed and not written, and pass 2's listing in
    `eighth-experimentation`, which comes before 1.5 writes the default and which 1.5 retires;
  - the waiting list's Stage 19 rows read current: the mirror, the GitLab password's rotation, the
    AppleDouble objects, verification v's look, decision 17 (d)'s report and pass 2's portal acts.

## 2026-11-11 — the estate reviewed against decisions 17 to 20; pass 4 opened with nothing up

A new session, on the branch `claude/pr-284-smus-pipeline-d233a3`, cut from `main` at `d423543c`
([PR #284](https://github.com/felipenoris/AWS-DataScience/pull/284)'s squash). The session that ran
pass 1 answered that it leaves the stage and holds nothing open.

- **[user]**, verbatim: *"O PR #284 envolveu algumas decisões importantes para o projeto, o que implicou
  em mudanças relevantes. Em especial, a esteira de promoção de aplicação SMUS deixou de ter o stage
  "test", publicando sandbox -> staging -> production. Entendo que isso tem efeitos colaterais na esteira
  implementada via gitlab CI/CD. Peço que faça uma revisão ampla do plano, considerando as decisões
  tomadas no PR #284, no sentido de mapear todas as alterações necessárias no ambiente para adequá-lo às
  decisões tomadas. Revise os planos, as etapas necessárias para implementação das mudanças, e os
  artefatos de documentação, considerand o que foi feito no PR #284. Considerando o ambiente fora do ar
  (ou seja, sem rodar make up), o usuário sso infra atualmente logado, faça toda a preparação e
  implantação do que for possível de ser implantado neste momento, além de planejamento das etapas que
  envolvem a implementação das alterações necessárias bem como o restante to stage 19. Autorizo todas as
  escritas e applies necessárias no ambiente considerando este pedido."*
- **[Claude] The sessions told** before the first write: the two peers on this laptop, the session of
  pass 1 and its fork, each with the list of slices this sitting writes.
- **[Claude] The identity**: `sts get-caller-identity` on `awsds-infra-identity`, `-data`, `-sandbox-1`,
  `-staging` and `-prod` answers `InfrastructureAccess`, and on `awsds-policy-canary`
  `AWSAdministratorAccess`, all as the infrastructure user.

**4.1, the `Workloads` SCP (decision 13 (b)).**

- **[Claude] Written**: `DenyDataZoneEntirely` gains `ArnNotLike` on `aws:PrincipalArn` for the SSO
  `InfrastructureAccess` role (the baseline's pattern), `awsds-deploy-*` and `datazone_usr_role_*`, and
  `DenyDataZoneSubscriptionRequests` is new beside it; `POLICIES.md`'s two rows, the document's
  description (403 characters of 512), the battery's rows (the two `ListDomains` rows turned to `allow`,
  a `CreateSubscriptionRequest` row and Staging's `CreateSpace` row added) and the wildcard check's
  whitelist entry with its reason.
- **[Claude] The battery before**, `./aws/probes/scp-battery.py --phase ou` at 04:29:14 UTC, with the
  rows as `main` holds them: *"49 as expected, 0 unexpected, 5 not measured"*, both `ListDomains` rows
  `DENY-SCP p-83t232f4`.
- **[Claude] The deny half, on a candidate parked on `Policy Test`.** The infrastructure user is one of
  the three excepted principals, so no profile in a `Workloads` account reads the deny. The candidate is
  the document's two DataZone statements alone, created as `awsds-infra-identity` under the delegation's
  `DelegatePolicyLifecycleToIdentity`:
  - 04:30:47, the canary with nothing parked: `datazone list-domains` answers `{"items": []}`, and
    `create-subscription-request` on a domain, a listing and a project that do not exist answers
    DataZone's own *"User is not permitted to perform operation: CreateSubscriptionRequest"*, the wording
    that proves authorization was reached;
  - 04:31:17, `create-policy` answers `p-oktjrbxv`; 04:31:41, attached to `Policy Test`
    (`ou-zhj6-ebwso7wp`), which carried `FullAWSAccess` and Control Tower's two guardrail documents;
  - 04:31:51, the canary's `list-domains` is refused; at 04:32:59 `list-domains`,
    `list-environment-blueprints` and `create-subscription-request` each read *"with an explicit deny in
    a service control policy"* naming `p-oktjrbxv`, while `sts get-caller-identity` and `ec2
    describe-vpcs` answer;
  - 04:33:14 detached, 04:33:15 deleted; `Policy Test` carries its three documents again and no
    `awsds-canary*` policy is listed. `list-domains` is still refused at 04:33:33, 04:33:40 and 04:34:01
    and answers at 04:34:22, 68 s after the detach (`SUP-350`).
- **[Claude] Planned** as `awsds-infra-identity` at 04:35:31 UTC, `-input=false`:
  `aws_organizations_policy.this["awsds-org-scp-ou-workloads"]` updated in place and nothing else, the
  condition, the new statement and the description, 2,499 to 2,840 bytes; saved as
  `$HOME/tmp/stage19-scp-41.tfplan`. **The apply was refused to Claude** by the app's auto-mode
  classifier (*Protected-Scope IaC Apply*), the user's authorization in chat notwithstanding, as at
  Stage 18 1.3: it is the user's, from the saved plan.

**4.2, the association.**

- **[Claude] The console's act read in the trail.** Data Governance's CloudTrail for 2026-10-19 04:00 to
  04:06 UTC, the user's association of Staging at Stage 18 2.1: `ram:GetResourceShares` by the
  permission `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, `ram:AssociateResourceShare`
  with one principal at 04:03:13, and `datazone:PutDomainSharingPolicy` at 04:03:14, invoked by
  `ram.amazonaws.com` in the same session. No other write (`SUP-349`).
- **[Claude⚡] Associated by that call**, as `awsds-infra-data`, at 04:37:18 UTC: `ram
  associate-resource-share` on `DataZone-EXTENDED_ACCESS-dzd-d8yrvx1ko7im6o-ORG-ONLY` with Staging's and
  Production's account ids, read from STS. Both answer `ASSOCIATING`, then `ASSOCIATED` at 04:37:19; the
  trail holds the call and two `PutDomainSharingPolicy` (04:37:20, 04:37:21), each policy naming three
  principals. The share's principals are Sandbox (2026-08-21), Staging and Production; no invitation
  exists in either account, and each reads the share `ACTIVE` as `OTHER-ACCOUNTS`. The DataZone
  read-back, `list-environment-blueprint-configurations`, is refused to both by the SCP, which still
  stands whole: it follows 4.1's apply.

**4.3 to 4.5 and 4.8, written and planned.**

- **[Claude] The lists**: `SMUS_ASSOCIATED` and `SMUS_DEPLOYMENT_MEMBERS` gain `staging` and
  `production`, and `backend.py` emits for the slice name `studio`, with `vpc_slice` (`foundation` in
  Staging, `workloads` in Production). Over every declared slice, laptop and pipeline, the generated
  tfvars differ from `main`'s in `governance/`'s `members` alone; the two `studio` slices are new.
- **[Claude] `staging/studio/` and `production/studio/`** from Stage 18's slice: `sagemaker-prereqs-v0.9.0`
  with `Tooling` and `DataLake`, the workflows grant with decision 17's `StartDataSourceRun`, the deny
  on a person's session; copies of each other but for `project-roles.tf` (`check-copies.py`). Both
  accounts read clean of the names first: no `awsds-<env>-smus-projects` bucket, no project key alias,
  no `smus` or `datazone_usr_role_*` role, no boundary, no log group. Their Lake Formation settings, the
  before of 4.6: one administrator, `InfrastructureAccess`, `AllowFullTableExternalDataAccess` unset,
  `CROSS_ACCOUNT_VERSION` 4, `SET_CONTEXT` `TRUE`, both create-default lists empty. Planned with
  `-var blueprints_enabled=false` at 04:43:21 (Staging) and 04:43:38 UTC (Production): *"16 to add, 0 to
  change, 0 to destroy"* each, the two roles and their three managed-policy attachments, the boundary,
  the key and its alias, the bucket with its five settings, the log group and the person-session
  policy; saved as `$HOME/tmp/stage19-studio-staging-1.tfplan` and `-production-1.tfplan`. **Staging's
  apply was refused to Claude** by the classifier, with no reason given; Production's was not tried.
  Both are the user's.
- **[Claude] `governance/`**: provider aliases for the two targets, the profiles `deployment-staging`
  and `deployment-production` (an environment configuration names one account, so one profile per
  target) behind `deployment_profiles_enabled`, false, their grant to each account's
  `InfrastructureAccess` session group, and `catalog_import_projects`, empty. Planned at 04:41:40 and
  04:49:33 UTC as `awsds-infra-data`: `No changes`.
- **[Claude] The CLI's import read for 4.8**, in the CLI 1.0.9's `helpers/catalog_import.py`,
  `helpers/catalog_export.py` and `commands/bundle.py`: the import's pre-flight on the domain unit's
  policy grants (`SUP-351`), and the bundle's silent export failure (`SUP-352`). `list-policy-grants`
  on the root unit, as `awsds-infra-data`: `CREATE_GLOSSARY` 0, `CREATE_FORM_TYPE` 1, `CREATE_ASSET_TYPE`
  0, `CREATE_PROJECT_FROM_PROJECT_PROFILE` 2, `ADD_TO_PROJECT_MEMBER_POOL` 1.
- **[Claude] `<env>/foundation/deploy-project.tf`**, the same file in both targets: one managed policy
  on the deploy role, created once `deployment_project_role` names the project's role. Both slices plan
  `No changes` with it empty (04:50 UTC, the alerts var-file from the project folder's `secrets/`);
  with a placeholder role name the plan reads 2 to add and the policy 13 statements in 3,828
  characters of 6,144.
- **[Claude] `staging/egress/` and `production/workloads-egress/`** name `datazone` in their
  `extra_services`, 8 endpoints each at the next `make up`.

## 2026-11-11 — release T written: the `test` stage retired in the template, the bundle role narrowed

The same sitting, nothing up, no AWS write but the reads below.

- **[Claude] The pipeline's change cut in two releases**, the stage file's §The estate against
  decisions 17 to 20: T, decision 19 (c) on today's Terraform legs, and F, the CLI's legs (4.9 to
  4.11). T needs nothing of pass 4.
- **[Claude] The template, `examples/app-etl/`**: the manifest holds the stage `dev` alone, with
  `PUBLISH_LISTING` false (decision 20 (b)); `.gitlab-ci.yml`'s job `bundle` stands where `test-deploy`
  stood, in a stage `bundle`, and the six `needs` that named `test-deploy` name it; the README. The
  job needs `DOMAIN_ID`, `DOMAIN_REGION` and `DEV_PROJECT_NAME` and gives the other stage variables a
  placeholder. Read after it: 72 tests passed and 1 skipped, ruff clean, the pinned lint `d856982c`
  *"ok: 9 arquivo(s)"*, `render-workflow.py --check` and `check-gitlab-ci.py` `OK`.
- **[Claude] The CLI 1.0.9's `bundle` on the one-stage manifest**, on the laptop in a scratch copy with
  the two zips built, as `awsds-infra-sandbox-1` (a contributor of `eighth-experimentation`) at 05:01:52
  UTC, `DEV_PROJECT_NAME` that project: exit 0, *"Bundle created: ./artifacts/app-etl.zip (24076 bytes)"*,
  11 files, the tree a `test-deploy` bundle carried. Its only refusal is the `GetGroupProfile` warning
  every caller reads.
- **[Claude] The same command on a project the caller is no member of**, `governed-lake`, at 05:02:30
  UTC: exit 0 and the archive written again, after *"ERROR - Failed to get project connections for
  governed-lake: AWS Permission Error: ... ListConnections operation: User is not permitted to perform
  operation: ListConnections"*. The job's guard was first written from the code, on the string *"Error
  getting DataZone project info"*, which this run does not print; it greps the line the run printed,
  absent from the member's log (`SUP-352`).
- **[Claude] `sandbox/workflows/deploy-role.tf`**: the role keeps its name and its project reads, gains
  the export's `Search`, `SearchTypes`, `GetAsset` and `GetDataProduct`, loses the workflow, log-group,
  S3 and key statements and the `PassRole`, and its ceiling denies every role change and every
  `PassRole`; `test_project_role` and the key alias read leave the slice. Planned as
  `awsds-infra-sandbox-1` at 05:00:41 UTC: *"0 to add, 3 to change, 2 to destroy"*, the boundary, the
  role's description and `project-reads` changed, the inline policies `storage` and `workflows`
  destroyed; saved as `$HOME/tmp/stage19-sandbox-workflows-bundle-role.tfplan`. Not applied: it goes with
  the template's merge request, since GitLab's `main` still runs `test-deploy`.
- **[Claude] `./aws/studio.py`** with the deployment targets' rules, on the five infrastructure
  profiles at 05:05 UTC: all checks passed. `US-2` notes the SCP's refusal in Staging and in Production
  as 4.1 pending, `US-6` passes on no SageMaker AI domain in either, `US-3` reads Sandbox's 14
  configurations and `US-4` the three profiles the domain holds.
- **[Claude] The documents**: the stage file's map of what each decision changes, with the order of the
  applies; Stage 8's 2.5, 3.3, decision 19 and its standing rows; D41's item 3 note; the application
  runbook's §O, §L, §M, §P, §T and §S; `promotion.md` §N.8.2 as release T's sitting; `AWS_STATE.md`'s
  row on the association; `NETWORK.md`, `PRICING.md` and `cost-model.md` for the `datazone` endpoint
  and the `studio` slices; `SUP-349` to `SUP-352`; the waiting list's two rows. The phrase-level
  amendments in Stage 10, the decisions and the smaller documents were made by a subagent of this
  session from the same facts.
- **[Claude] The `bundle` job's script run as written**, on the laptop with the same identity: with the
  project the caller belongs to it exits 0 and prints the bundle's SHA256; with `governed-lake` it
  stops at *"FATAL: the role could not read the project governed-lake: is it a member of it?"*, exit 1.
- **[Claude] The role-session groups read** in the domain, for the memberships release T and 4.8 move
  (`search-group-profiles --group-type IAM_ROLE_SESSION_GROUP`, then `get-group-profile` on each: such a
  profile carries no name, its `rolePrincipalArn` names the role). Five exist: Sandbox's, Data
  Governance's and Staging's `InfrastructureAccess`, `awsds-deploy-sandbox-test`
  (`06d426f2-84d6-38ae-a991-6806981d9520`) and `awsds-deploy-staging` (`9bead345-…`, Stage 18's, which
  outlived that stage's unwinding). Production's `InfrastructureAccess` and `awsds-deploy-prod` have
  none: neither has called the domain. `test-experimentation`'s members: its owner, one contributor
  user, Sandbox's `InfrastructureAccess` group and the bundle role's group, a `PROJECT_CONTRIBUTOR`.
- **[Claude] The gates and the pull request**: `make check` and `make check-ou` `OK`, the commit hooks
  passing on both commits; the branch at `main`'s tip plus two commits, pushed, and
  [PR #288](https://github.com/felipenoris/AWS-DataScience/pull/288) opened. The three saved plans
  (`stage19-scp-41`, `stage19-studio-staging-1`, `stage19-studio-production-1`) wait for the user's
  apply, and the bundle role's for release T's sitting.

## 2026-11-11 — the `Workloads` SCP and both `studio/` slices applied; the allow half read; the next plans

The same day, a later sitting, nothing up. The user authorized the three saved plans in chat: *"Autorizo
os 3 applies"*. The app's classifier let each through on that sentence.

- **[Claude] Before the writes**: every `awsds-infra-*` profile answered as `InfrastructureAccess` and
  the canary's as `AWSAdministratorAccess`; no other session was running on the laptop.
- **[Claude⚡] The SCP (4.1)**, account Identity, `awsds-infra-identity`, the saved plan
  `stage19-scp-41.tfplan`: 14:23:31 to 14:23:46 UTC, *"0 added, 1 changed, 0 destroyed"*, `p-83t232f4`
  at 2,840 bytes. The re-plan reads `No changes` and `./aws/org-policies.py` passes every check.
- **[Claude⚡] The prerequisites (4.4)**, the saved plans: `staging/studio/` as `awsds-infra-staging`,
  14:23:58 to 14:25:18 UTC, and `production/studio/` as `awsds-infra-prod`, 14:25:29 to 14:26:49 UTC,
  each *"16 added, 0 changed, 0 destroyed"*.
- **[Claude] DataZone from the targets (xviii)**, at 14:27 UTC as each account's `InfrastructureAccess`:
  `list-domains`, which the SCP refused at 05:05 UTC, answers `dzd-d8yrvx1ko7im6o awsds-studio
  AVAILABLE`, and `list-environment-blueprint-configurations` answers an empty list.
- **[Claude] The battery's phase `ou`** at 14:27:22 UTC, 3 min 36 s after the SCP's apply: **52 as
  expected, 0 unexpected, 5 not measured**. Both `datazone:ListDomains` rows read `ALLOWED`, and both
  `datazone:CreateSubscriptionRequest` rows `DENY-SCP` naming `p-83t232f4`: the allow half and the
  subscription deny, measured in the accounts themselves. Report `scp-battery-20261111T112722.txt`.
- **[Claude] What the first applies created, read back** in both accounts, `<env>` being `staging` and
  `prod`: the roles `awsds-<env>-smus-provisioning` (created 14:24:08 UTC in Staging, 14:25:38 in
  Production; trusted by `cloudformation` and `datazone`; `SageMakerStudioProjectProvisioningRolePolicy`)
  and `awsds-<env>-smus-manage-access` (`AmazonDataZoneGlueManageAccessRolePolicy` and
  `AmazonDataZoneSageMakerManageAccessRolePolicy`); the policies `awsds-<env>-project-boundary` and
  `awsds-<env>-person-session-deny`, attached to nothing; the project key behind
  `alias/awsds-<env>-project`, `Enabled`, customer-managed; the bucket `awsds-<env>-smus-projects`,
  versioned, its four public-access blocks on, `aws:kms`; the log group `/awsds/<env>/studio` at 30
  days. Lake Formation in each still reads one administrator and the flag unset.
- **[Claude] The configurations planned (4.4's second apply)**, with no `-var`: Staging at 14:30:12 UTC,
  Production at 14:30:33 UTC, each *"5 to add, 2 to change, 0 to destroy"*. To add: the `Tooling` and
  `DataLake` configurations, their two `create_environment_from_blueprint` grants and
  `awsds-<env>-workflows`. To change: the project key's policy, which gains
  `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`, and the
  person-session policy, whose document is known after apply and whose content does not change.
  Staging's configurations point at `vpc-0a2dadcbab22702e7`, Production's at VPC-Workloads,
  `vpc-06e421bd113984822`. Saved as `$HOME/tmp/stage19-studio-staging-2.tfplan` and
  `stage19-studio-production-2.tfplan`.
- **[Claude] Staging's second apply refused by the classifier** at about 14:31 UTC, *Protected-Scope
  IaC Apply*: the user's sentence named three applies and this is a fourth. Not retried; it and
  Production's wait for the user's word or hand.
- **[Claude] Production's `InfrastructureAccess` had no profile in the domain** after the reads of
  14:27 UTC: `search-user-profiles --user-type DATAZONE_IAM_USER` listed the same role of Sandbox, Data
  Governance and Staging and not Production's, and Cloud Control's `<domain>|<role ARN>` read answered
  `NotFound`, where `governance/`'s plan with the profiles on would have stopped. Read call by call
  from `awsds-infra-prod`: `list-projects` (14:36:52 UTC, four projects) and `get-domain` (14:37:21)
  left it `NotFound`; four seconds after `get-project` on `governed-lake` (14:37:28) the group profile
  read `ASSIGNED`, `ca2735c9-66e3-3eea-9434-c8de08536d0b`. As a non-member the role was answered
  `GetProject`, `ListProjectMemberships` (three members) and `ListEnvironments` (`Tooling`), and
  refused `ListConnections` (`SUP-157`). `SUP-159` carries the reading.
- **[Claude] `governance/`'s profiles planned as a rehearsal (4.5)**, `deployment_profiles_enabled`
  true in the working tree alone and put back, as `awsds-infra-data` from 14:39:04 to 14:39:36 UTC:
  *"4 to add, 0 to change, 0 to destroy"*, `deployment-staging` and `deployment-production` (each
  `Tooling` `ON_CREATE` at order 0 with its seven overrides and `DataLake` `ON_DEMAND` at order 1,
  `ENABLED`) and their `CREATE_PROJECT_FROM_PROJECT_PROFILE` grants on the root unit; nothing on
  `experimentation` or `lake-publishing`. The data sources read both targets' session groups,
  Staging's `65b0f127-7cf5-4201-89ee-73b420b5f958`. The plan of record is taken after the second
  `studio/` applies, the switch committed with it.
- **[Claude] `./aws/studio.py`** at 14:40 UTC on the five infrastructure profiles and the canary: 0
  checks failed. `US-2` passes on both targets seeing the shared domain and owning none, `US-3` notes
  no configuration in either until the second apply, `US-6` passes on no SageMaker AI domain.

## 2026-11-11 — the configurations and the profiles applied; `deploy-staging` and `deploy-production` created with their database

The same day, nothing up. The user authorized the five steps listed in chat, the two second `studio/`
applies, `governance/`'s profiles and each target's project with its database: *"Autorizo os 5 passos"*.
The app's classifier let every call through.

- **[Claude] Before the writes**, 15:17 UTC: the three profiles answered as `InfrastructureAccess`; the
  one other session on the laptop, idle, was told of the writes and of the slices applied from this
  branch.
- **[Claude⚡] The configurations (4.4's second apply)**, from the saved plans: `staging/studio/` 15:18:06
  to 15:18:41 UTC and `production/studio/` 15:18:55 to 15:19:28 UTC, each *"5 added, 1 changed, 0
  destroyed"*, the person-session policy's document unchanged once known. Both re-plan `No changes`.
  From each target `list-environment-blueprint-configurations` reads `Tooling` (`4k186sfh08eqxc`) and
  `DataLake` (`d8w7c3fmbsz5cg`), each with the account's provisioning role, manage-access role, D13
  boundary, VPC and two private subnets, `Tooling` with the projects bucket as its S3 location.
- **[Claude⚡] The profiles (4.5)**, `deployment_profiles_enabled` true, planned as `awsds-infra-data` at
  15:20:35 UTC: *"4 to add, 0 to change, 0 to destroy"*, the grants naming Staging's group
  `65b0f127-…` and Production's `ca2735c9-…`. The apply, 15:21:15 to 15:21:42 UTC, created
  `deployment-staging` (`cpkm68sz0l185s`), `deployment-production` (`3o9zp0asbh2gi8`) and Production's
  grant, and failed on Staging's: *"failed conditions: VERSION EQ [S] (Service: DataZone, Status Code:
  409 ...). ErrorCode: ResourceConflict"*, the two grants of one type on one unit created at once
  (`SUP-353`). `list-policy-grants` read that grant absent; the re-plan read 1 to add, and its apply,
  15:22:50 to 15:23:10 UTC, created it. The re-plan after it reads `No changes`; the switch is
  committed (`7792da20`).
- **[Claude] Before the projects**, 15:25 UTC, both targets: Lake Formation with one administrator, the
  flag unset, `CROSS_ACCOUNT_VERSION` 4, `SET_CONTEXT` `TRUE`, no registered location; no
  `datazone_usr_role_*` role, no `DataZone-Env-*` stack, no Access Grants instance; the Glue databases
  `app_outputs`, `curated` and `raw`, and `default` in Staging alone.
- **[Claude⚡] `deploy-staging` (4.6)**, `create-project` from `deployment-staging` as
  `awsds-infra-staging` at 15:25:59 UTC: `5ido8bej1zoeq8`. Its `Tooling` environment (`d6nu5aphq1e974`)
  read `ACTIVE` and the project `SUCCESSFUL` at 15:27:41 UTC, the stack created at 15:26:13. Then the
  database: `create-environment` with the profile's `DataLake` configuration (`d8f802ad-…`), the
  blueprint and `--user-parameters name=glueDbName,value=app_etl`, named `deploy-staging-app-etl`, at
  15:28:27 UTC: `54jhe9989w0tcg`, `ACTIVE` at 15:29:07.
- **[Claude⚡] `deploy-production` (4.6)**, the same two calls as `awsds-infra-prod`: the project
  `d7qcazihvr3s7k` at 15:29:29 UTC, its `Tooling` (`59niwej9axztow`) `ACTIVE` at 15:31:00 and the
  project `SUCCESSFUL` at 15:31:18; the environment `deploy-production-app-etl` (`azkybvkz7iea34`, the
  configuration `f403ecfc-…`) at 15:31:41 UTC, `ACTIVE` at 15:32:24.
- **[Claude] What provisioning created (3.2 and 3.3's readings), the same in both accounts**: the
  `Tooling` stack's thirteen resources, Stage 18's list, with `enableSpaces` `false`, the account's D13
  boundary as `permissionsBoundaryArn`, and no SageMaker AI domain; the project role
  `datazone_usr_role_<project>_<environment>` and the two Bedrock roles, all three under the boundary;
  the security group `datazone-<project>-dev` in the account's compute VPC, all traffic in from itself
  and out to `0.0.0.0/0`; two Glue network connections; the log group `datazone-<project>-dev` at 731
  days under the project key; nine connections; five objects under the project's prefix; the Access
  Grants instance `default` and `AWSServiceRoleForAmazonAthena`. Each project has two members: the
  account's `InfrastructureAccess` session group as `PROJECT_OWNER`, and the project role's own IAM
  user profile as `PROJECT_CONTRIBUTOR`.
- **[Claude] Lake Formation after it**: the provisioning role's three `PutDataLakeSettings` (15:26:05
  UTC in Staging, 15:29:35 in Production) added `awsds-<env>-smus-provisioning` and
  `awsds-<env>-smus-manage-access` beside `InfrastructureAccess`, kept the parameters and both empty
  create-default lists, and set `AllowFullTableExternalDataAccess` `true` in both accounts (`SUP-170`).
  The project's `dev` prefix is registered under the project role, hybrid access off. `staging/data/`
  and `production/data/` plan `No changes`, and `DT-5` passes. Production holds a `default` Glue
  database it did not have. **The flag is 4.7, the user's**: `TM-26`'s Production half is open again
  since 15:29 UTC.
- **[Claude] The database (verification xix)**: `app_etl` in each account, *"Created by DataZone for
  project deploy-<env>"*, its location the project's `dev/data/catalogs/`, no create-table default, no
  table. On it the account's `IAMPrincipals` hold `CREATE_TABLE`, `DESCRIBE` and `DROP` under
  `context.datazone.projectId=="<project>"`, and `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DROP` and
  `DESCRIBE` on its tables; the provisioning role `ALL`, grantable; the manage-access role
  `CREATE_TABLE` and grantable `DESCRIBE`, with grantable `DESCRIBE` and `SELECT` on the tables, its
  `CreateLakeFormationOptIn` passing. The source `<account>-AwsDataCatalog-app_etl-default-datasource`
  is `READY`, enabled, `publishOnImport` false, daily at the minute of its creation (`cron(28 15 * * ?
  *)` in Staging, `cron(32 15 * * ? *)` in Production), its filter `app_etl` `INCLUDE *`. **The
  environment carries a subscription target**, `deploy-<env>-app-etl-default-target`, for
  `GlueTableAssetType` and `GlueViewAssetType`, its `databaseName` `app_etl`, its manage-access role the
  project role, its principal `abac:CURRENT_PROJECT`; the portal's own environment for `app_etl` in
  `eighth-experimentation` read with none at 15:48 UTC (`SUP-184`).
- **[Claude] The trails of the two windows**, 233 events in Staging and 245 in Production: the
  provisioning role made 119 and 120 of them, the DataZone service 39 in each, and
  `InfrastructureAccess` was the one principal calling `datazone:`. No refusal named an SCP or the
  boundary: the provisioning role's `athena:GetWorkGroup` and `ListTagsForResource`,
  `logs:DescribeIndexPolicies` and `DescribeResourcePolicies`, `ec2:DescribeSecurityGroupRules`,
  `servicequotas:GetServiceQuota` and a first `ec2:CreateSecurityGroup`, and the project role's
  `s3:CreateAccessGrantsLocation`, Stage 18's list. The manage-access role's `RevokePermissions` from
  `IAM_ALLOWED_PRINCIPALS` answered `InvalidInputException`, nothing to revoke.
- **[Claude] The instruments**: `./aws/studio.py` reads the deployment targets' project roles since this
  sitting, `US-8` passing on three bounded roles in each; at 15:44 UTC 0 checks failed, `US-3` passing
  on each target's two configurations and `US-4` on the five profiles. `./aws/deploytargets.py` at
  15:41 UTC: 0 checks failed.
- **[Claude] The next applies written and planned**, the projects' names in three slices:
  `project-roles.tf` in each `studio/` (2 to add each, the workflows grant and the person-session deny
  on the project role); `deployment_project_role` in each `foundation/` (2 to add each, the deploy
  role's policy and its attachment, the alerts var-file read from the project folder's `secrets/`);
  `catalog_import_projects` in `governance/` (6 to add, three grants per project as `OWNER`, applied
  with `-parallelism=1`). Saved under `$HOME/tmp/` as `stage19-studio-staging-3.tfplan`,
  `stage19-studio-production-3.tfplan`, `stage19-foundation-staging-deploy-project.tfplan`,
  `stage19-foundation-production-deploy-project.tfplan` and `stage19-governance-catalog-import.tfplan`.
  Not applied: a round the user has not named.

## 2026-11-11 — the supplement reviewed against the sitting's findings

The same day, nothing up, reads alone, at the user's request: *"Veja oportunidades de atualizar o
AWS_SUPPLEMENT.md com base nas descobertas desta sessão."* Every finding of the four entries above was
read against the supplement; the readings below are the ones the review added.

- **[Claude] The domain's IAM user profiles**, `search-user-profiles --user-type DATAZONE_IAM_USER` as
  `awsds-infra-data` at 15:59 UTC: 50. Thirty are `awsds-deploy-sandbox-test`'s and six
  `awsds-deploy-staging`'s, each with its own `sessionName` of the form `botocore-session-<digits>`; four
  are the accounts' `InfrastructureAccess` roles', one each, named for the person; ten are project
  roles', with no session name, five of them of projects no longer listed. Each detail carries
  `groupProfileId` (`SUP-158`).
- **[Claude] The six projects' member lists**, `list-project-memberships` as `awsds-infra-data`, a member
  of two of them: every project that holds a `Tooling` environment lists its own project role's user
  profile as `PROJECT_CONTRIBUTOR`, the two deployment projects included; the model governance project,
  which holds none, lists two groups (`SUP-157`, `SUP-158`).
- **[Claude] AWS Config and the Glue databases**: in the trails already read, `AWSServiceRoleForConfig`'s
  `glue:GetDatabase` answered `AccessDenied`, *"An unknown error occurred"*, on Staging's `app_etl` at
  15:29:52 UTC and on Production's `default` at 15:32:22 and `app_etl` at 15:34:32, each within three
  minutes of the database's creation. `AWSConfigServiceRolePolicy` is at v97 and allows the action.
  `configservice list-discovered-resources --resource-type AWS::Glue::Database` at 16:01 UTC returned
  nothing in Sandbox (nine Glue databases), Data Governance (five), Staging and Production (five each)
  and Identity (none); the recorder in both targets is Control Tower's, every supported type,
  continuous (`SUP-355`).
- **[Claude] Each target's `default` database**: the provisioning role's `ALL` and `IAMPrincipals`'
  `DESCRIBE` under the project's condition; Staging's existed before the project, Production's was
  created by the provisioning at 15:30:49 UTC (`SUP-170`).
- **[Claude] The CLI 1.0.9's `commands/deploy.py`, read again**: the catalog import opens the archive
  `--bundle-archive-path` names and reads `catalog/catalog_export.json` in it, returning success with no
  archive, with no such member or with the stage's catalog disabled (`SUP-286`); it returns failure only
  when every attempted item failed (`SUP-357`).
- **[Claude] Written in the supplement**: `SUP-354` (a subscription request naming nothing is refused,
  from the readings of 04:30 and 14:27 UTC), `SUP-355`, `SUP-356` (the `studio/` plans' two changes and
  their applies' one) and `SUP-357`; readings appended to `SUP-157`, `SUP-158`, `SUP-170`, `SUP-184` and
  `SUP-286`; `SUP-353` named among the Terraform section's pointers.

## 2026-11-11 — the user's acts and the next applies asked of Claude, each refused by the app's classifier

The same day, nothing up. No write reached AWS in this entry.

- **[user]**, verbatim: *"Sobre "atos seus" e "os 5 applies seguintes", você pode executar todos esses
  passos?"*, on the flag (4.7), the deploy role's membership (item 12) and the five saved plans.
- **[Claude] Before the attempts**, 16:08 UTC: the three profiles as `InfrastructureAccess`; the one
  other session on the laptop told. Production's trail of 2026-10-25 read for the console's own write
  of the flag: one `PutDataLakeSettings` at 17:44:31 UTC carrying the whole structure with
  `allowFullTableExternalDataAccess` `false`, after which the key reads absent (`SUP-112`).
- **[Claude] Three calls refused by the app's auto-mode classifier, none retried**:
  `lakeformation put-data-lake-settings` in Production, the settings as read with the flag `false`
  (*Modify Shared Resources*); `datazone create-project-membership` of `awsds-deploy-staging`'s group as
  `PROJECT_OWNER` of `deploy-staging` (*Permission Grant*, as at Stage 18); and the first of the five
  applies, `stage19-studio-staging-3.tfplan` (*Protected-Scope IaC Apply*), the user's sentence being a
  question where the applies of 14:23 and 15:18 UTC followed *"Autorizo"*.
- **[Claude] Read after them**, 16:10 UTC: the flag `true` and three administrators in both targets,
  `deploy-staging`'s two members, the project role's three managed policies. Nothing changed. The two
  acts stay the user's, and the five applies wait for the user's word naming them or the user's hand.

## 2026-11-11 — the next applies run: the project roles' grants, the deploy roles' policy, the CLI import's grants

The same day, nothing up. The user, verbatim: *"Autorizo os 5 applies"*. The app's classifier let each
through.

- **[Claude] Before the writes**, 16:15 UTC: the three profiles as `InfrastructureAccess`; the one other
  session on the laptop, told of these applies at 16:08 UTC, idle.
- **[Claude⚡] `staging/studio/` and `production/studio/`**, from the saved plans, 16:15:49 to 16:16:02
  UTC and 16:16:11 to 16:16:22 UTC: each *"2 added, 0 changed, 0 destroyed"*, `awsds-<env>-workflows` and
  `awsds-<env>-person-session-deny` attached to the project role.
- **[Claude⚡] `staging/foundation/` and `production/foundation/`**, 16:16:33 to 16:16:45 UTC and
  16:16:55 to 16:17:09 UTC: each *"2 added, 0 changed, 0 destroyed"*, `awsds-<env>-deploy-project` and its
  attachment to the deploy role.
- **[Claude⚡] `governance/`**, with `-parallelism=1`, 16:17:19 to 16:18:31 UTC: *"6 added, 0 changed, 0
  destroyed"*, the three grants of each project, each created in 6 to 13 s with no conflict (`SUP-353`).
- **[Claude] Read after them**: the five slices re-plan `No changes`, 16:18 to 16:20 UTC, the
  foundations with the alerts var-file. Each project role carries its three AWS policies and the two of
  `studio/`. Each deploy role carries three managed policies; `awsds-<env>-deploy-project` is at `v1`
  with 13 statements, 3,828 characters in Staging and 3,816 in Production, its `PassRole` naming the
  project role and its workflow statements the project's id. The root unit reads `CREATE_GLOSSARY` and
  `CREATE_ASSET_TYPE` for both deployment projects as `OWNER`, and `CREATE_FORM_TYPE` for them and
  `eighth-experimentation`.
- **[Claude] The deploy roles' grants simulated**, `iam simulate-principal-policy` as each account's
  `InfrastructureAccess` at 16:28 UTC, the context naming `aws:RequestedRegion` (`SUP-008`):
  `datazone:GetProject`, `ListConnections`, `CreateAsset`, `CreateGlossary` and `ListPolicyGrants`,
  `airflow-serverless:ListWorkflows` and, with the project's tag, `CreateWorkflow` read `allowed` under
  the boundary and the organization; `datazone:AddPolicyGrant` `implicitDeny`;
  `datazone:CreateSubscriptionRequest` `explicitDeny`, the organization's; `iam:PassRole` of the project
  role to `airflow-serverless.amazonaws.com` and `kms:GenerateDataKey` on the project key `allowed`; with
  `aws:ResourceOrgID` in the context, `s3:PutObject` and `GetObject` `allowed` under the project's
  `shared/` prefix and `implicitDeny` under `dev/`. The deploy boundary's document, read beside it, is
  `Allow *` with four denies on role and boundary changes. A simulation, not an exercise: the roles'
  first calls are release F's.
- **[Claude] The instruments**, 16:21 to 16:25 UTC: `./aws/studio.py`, `./aws/deploytargets.py` and
  `./aws/cicd.py`, 0 checks failed each; `CI-2` reads both deploy roles under their boundary.
- **[Claude] What pass 4 still owes with nothing up**: the flag (4.7) and `awsds-deploy-staging`'s
  membership of `deploy-staging`, both the user's.

## 2026-11-11 — the project role's reach in Production read; the instruments extended to the two projects

The same day, nothing up, reads alone. Asked what could be advanced with nothing up, Claude named this
review and the instruments; the user, verbatim: *"Sim, faça os dois"*.

- **[Claude] The role's policies**, `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow`, read at 17:24 UTC
  as `awsds-infra-prod`: `SageMakerStudioProjectUserRolePolicy` v76 (162 statements, 55,309 characters),
  `SageMakerStudioProjectRoleMachineLearningPolicy` v47 (90, 32,586),
  `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9 (13, 4,720), `awsds-prod-workflows` and
  `awsds-prod-person-session-deny` (4 each), no inline policy; the boundary `awsds-prod-project-boundary`,
  9 statements, `Allow *` with denies on the lake's prefixes, the lake's data key and five job settings;
  17 tags, `EnableAmazonBedrockPermissions` `true` among them.
- **[Claude] The statements classified**: 269 allow statements, 179 with a write action, 98 of them
  naming the project through `${aws:PrincipalTag/...}` and 81 not (`SUP-358`).
- **[Claude] What the unbound allows meet, read from the resources' side.** Trust policies, in the
  five accounts with a profile (53, 34, 45, 31 and 19 roles): `AWSControlTowerExecution` alone trusts a
  root, the management account's; none trusts its own account's root or any principal. Tags in
  Production: no resource wears `for-use-with-all-datazone-projects`; the project's tag is on ten
  resources, all its own; the eight secrets carry no DataZone tag. Lake Formation: `IAM_ALLOWED_PRINCIPALS`
  holds `ALTER`, `CREATE_CATALOG` and `CREATE_DATABASE` on the catalog; `curated`, `raw` and
  `app_outputs` are granted to named principals, every page read. The Access Grants instance: one
  location, the project's prefix under the project role, no grant, no resource policy. Key policies:
  the keys of GitLab, the state, the PKI state, the registry, the proxy log and the projects delegate
  `kms:*` to the account's IAM; the data key names its principals. Bucket policies: no hub bucket
  allows the account's root or any principal.
- **[Claude] The simulator calibrated**: `s3:GetObject` on the project's own prefix read `implicitDeny`
  until the context carried the role's tags as `aws:PrincipalTag/<key>`; `MissingContextValues` named
  none of them (`SUP-008`).
- **[Claude] Simulated as the role**, the Region, the organization id and the role's tags in the
  context. `implicitDeny`: `GetSecretValue` and `PutSecretValue` on GitLab's secrets, the deploy runner's
  token and the warehouse admin secret; `ssm:StartSession` and `SendCommand`, `ec2:StartInstances`,
  `StopInstances` and `ModifyInstanceAttribute`; `GetObject`, `PutObject` and `ListBucket` on each hub
  bucket called directly; a location on a hub bucket; `kms:Decrypt` on GitLab's key called directly; a
  pass of the job role; five IAM writes; the pipeline's Glue job; `PutImage` on the deploy image's
  repository; the chain, a schedule, a workflow with no project tag, the model registry, the alerts
  topic, a hub log group, `lambda:` and `cloudformation:` writes; `redshift-serverless:GetCredentials`
  called directly and the Data API on an untagged workgroup; `ec2:CreateVpcEndpoint` on a subnet and a
  security group, and the security-group and route writes. `allowed`: `secretsmanager:ListSecrets`;
  `sts:AssumeRole` on the deploy role, the runner's role and the job role; `kms:Decrypt` and
  `GenerateDataKey` through S3 on the keys of GitLab, the state, the data and the projects; the object
  reads and writes on a hub bucket for a request carrying Access Grants credentials;
  `s3:PutAccessGrantsInstanceResourcePolicy`; `glue:DeleteDatabase` and `CreateDatabase` on `curated`
  and the catalog, and the table reads and writes there under `glue:LakeFormationPermissions`
  `Enabled`; `lakeformation:BatchGrantPermissions`, `GetDataAccess` and `CreateDataCellsFilter`; the
  pull of the deploy image; `bedrock:InvokeModel` on a foundation model; AgentCore's
  `StartBrowserSession`, `StartCodeInterpreterSession` and `InvokeCodeInterpreter`; `q:SendMessage`,
  `codewhisperer:GenerateRecommendations`, `bedrock:GenerateQuery`, `datazone:GenerateCode`;
  `GetCredentials` on any workgroup through `sqlworkbench` or the Data API, with
  `sqlworkbench:CreateConnection` and `DriverExecute`; `datazone:CreateAsset` and
  `CreateListingChangeSet`. `explicitDeny`, the organization's: `datazone:CreateSubscriptionRequest`.
  Not read: the SageMaker job calls, whose organization statements need the request's settings.
- **[Claude] The routes of the projects' subnets**, both targets: the VPC, the S3 and DynamoDB
  gateways, and a peering to VPC-Networking's four ranges; `NETWORK.md`'s proxy planes
  `production-workloads` and `staging-foundation` hold no entry. No organization policy names a Glue
  job's network.
- **[Claude] `./aws/deploytargets.py`**, 17:39 UTC: `DT-13`, the full-table flag, fails in both targets
  (`EXC-23`), the script's only two failures; `DT-14` passes its four rows in each, Production's on
  eight secrets and one location.
- **[Claude] `./aws/studio.py`**, 17:43 UTC, 0 checks failed: `US-8` reads the domain account's three
  blueprint roles under `awsds-data-project-boundary` beside the others; `US-11` reads `deploy-staging`
  and `deploy-production` alone in their targets, two environments `ACTIVE` each, with their
  subscription targets; `US-12` reads 22, 28, 13 and 15 roles in Sandbox, Production, Staging and Data
  Governance, none trusting its account's root or any principal.
- **[Claude] `./aws/catalog.py`**, 17:46 and 17:48 UTC, all checks passed. Before the change it already
  read the two projects' sources as Data Governance's `InfrastructureAccess`, a member of neither
  (`SUP-157`): one Glue source each over `app_etl`, no publish on import, no generated names, no run
  yet. After it `CT-13` reads four trails and `CT-14` passes on both projects.
- **[Claude] Written**: `TM-30`; decision 21, due and the user's; `INV-22` and `EXC-23`; `SUP-358` and
  the readings on `SUP-008` and `SUP-157`; `NETWORK.md`'s row on the projects' groups, from the routes
  read; `aws/INDEX.md`.

## 2026-11-11 — decision 21 taken as (b): the fence written in the boundary module, tagged and planned

The same day, nothing up, no AWS write. The user, verbatim: *"(b) deny no boundary"*.

- **[Claude] The module**, `terraform-modules/sagemaker-prereqs/`: seven inputs, each off by default
  (`fenced_bucket_names`, `fence_customer_keys`, `fenced_secret_names`, `fence_role_assumption` with
  `assumable_role_arns`, `fenced_repository_names`, `fenced_services`), and in the boundary one deny
  per input that names something. The key statement denies `kms:*` on the account's keys whose
  aliases are neither the project key's nor `alias/aws/*`, by `ForAllValues:StringNotLike` on
  `kms:ResourceAliases`. Validated alone.
- **[Claude] The callers**, `production/studio/` and `staging/studio/`: `main.tf`, a copy in both, sets
  the same fence, and `fence.tf`, the account's own beside `project-roles.tf`, lists the buckets and
  repositories: six buckets and `awsds-prod-ecr-deploy` in Production, three buckets in Staging, each
  list every bucket of the account but the projects bucket (`s3api list-buckets`, read that hour).
- **[Claude] Rehearsed against the local module** before the tag (18:03 and 18:04 UTC): *"0 to add, 2 to
  change, 0 to destroy"* in each, the boundary and the person-session policy, whose document is known
  after apply (`SUP-356`). The boundary goes from 9 statements and 2,425 characters to 15 and 3,766 in
  Production and to 14 and 3,402 in Staging, of 6,144.
- **[Claude] Simulated as Production's project role under the planned document**
  (`--permissions-boundary-policy-input-list`, the Region and the role's tags in the context).
  `explicitDeny`, the boundary's: `sts:AssumeRole` on the deploy role; `kms:Decrypt` through S3 on the
  keys of GitLab and of the state; `GetObject` and `PutObject` on `awsds-prod-gitlab-backup` and
  `GetObject` on `awsds-prod-tfstate` with Access Grants credentials; `GetSecretValue` on GitLab's
  secrets and on the warehouse admin secret; the pull of the deploy image; `bedrock:InvokeModel`;
  AgentCore's `StartBrowserSession`; `q:SendMessage`, `codewhisperer:GenerateRecommendations`,
  `bedrock:GenerateQuery`. `allowed`: the project's own prefix, read and written; the project key and
  an `alias/aws/s3` key through S3; the pull of the application's image; the pass of itself to Glue;
  `datazone:CreateAsset` and `CreateListingChangeSet`, `lakeformation:GetDataAccess`,
  `secretsmanager:ListSecrets`; the table writes of `app_etl`; a Glue job's log group; the
  warehouse's credentials through the Data API, left for 4.11.
- **[Claude] The tag**: the module's commit `4c6bb4f2`, then `sagemaker-prereqs-v0.10.0` on it, the
  latest on origin being `v0.9.0`; `git ls-remote --tags origin` answers the tag at that commit.
- **[Claude] Planned against the tag**, 18:08 and 18:09 UTC, both slices re-initialised: the same two
  changes in each, the boundary's new statements `DenyTheAccountsOwnBuckets`,
  `DenyCustomerKeysButTheProjectKey`, `DenyTheAccountsOwnSecrets`, `DenyAssumingAnyRole`,
  `DenyServicesNoProjectUsesHere` and, in Production, `DenyTheAccountsOwnRepositories`. Saved as
  `$HOME/tmp/stage19-studio-production-fence.tfplan` and `stage19-studio-staging-fence.tfplan`. Not
  applied.
- **[Claude] `./aws/deploytargets.py`** reads the boundary's fence and every bucket of the account
  against it (`DT-14`): run after the change, 4 checks failed, `DT-13` and the fence's row in each
  target, the second until the applies.

## 2026-11-11 — the fence applied in both targets; the boundary, `DT-14` and each role read under it

The same day, nothing up. The user, verbatim: *"Autorizo os 2 applies"*. The app's classifier let each
through.

- **[Claude] Before the writes**, 18:24 UTC: both profiles as `InfrastructureAccess`; the one other
  session on the laptop, idle, told of the two applies at 18:25 UTC.
- **[Claude⚡] `production/studio/`**, from the saved plan, 18:25:13 to 18:25:31 UTC: *"0 added, 1
  changed, 0 destroyed"*, `awsds-prod-project-boundary`. The person-session policy, planned as a
  change, was not updated (`SUP-356`).
- **[Claude⚡] `staging/studio/`**, from the saved plan, 18:25:44 to 18:25:58 UTC: the same on
  `awsds-staging-project-boundary`.
- **[Claude] Read after them**: both slices re-plan `No changes` (18:26 UTC). Production's boundary is at
  `v2`, the default since 18:25:25 UTC, 15 statements and 3,766 characters, the boundary of 3 roles;
  Staging's at `v2` since 18:25:53 UTC, 14 statements and 3,402 characters, 3 roles; `v1` stays in each
  as a non-default version. The new statements: `DenyTheAccountsOwnBuckets`,
  `DenyCustomerKeysButTheProjectKey`, `DenyTheAccountsOwnSecrets`, `DenyAssumingAnyRole`,
  `DenyServicesNoProjectUsesHere` and, in Production, `DenyTheAccountsOwnRepositories`.
- **[Claude] `./aws/deploytargets.py`**, 18:29 UTC: `DT-14` passes every row in both targets, the fence's
  statements present and every bucket of the account named but the projects bucket, 6 in Production and
  3 in Staging. 2 checks failed, `DT-13` in each target (`EXC-23`), the flag being the user's.
- **[Claude] Simulated as Production's project role under the attached boundary**, 18:29 and 18:33 UTC,
  the Region, the organization id and the role's tags in the context: 40 decisions, the same row for row
  as under the planned document, run again beside it. 16 `explicitDeny`, each matched in
  `awsds-prod-project-boundary`: `sts:AssumeRole` on the deploy role; `kms:Decrypt` through S3 on the
  keys of GitLab and of the state; `GetObject` and `PutObject` on `awsds-prod-gitlab-backup` and
  `GetObject` on `awsds-prod-tfstate` with Access Grants credentials; `GetSecretValue` on GitLab's
  secrets and on the warehouse admin secret; the pull of the deploy image; `bedrock:InvokeModel`;
  AgentCore's `StartBrowserSession` and, on the code interpreter's own resource,
  `StartCodeInterpreterSession` and `InvokeCodeInterpreter`; `q:SendMessage`,
  `codewhisperer:GenerateRecommendations`, `bedrock:GenerateQuery`. 23 `allowed`: the project's own
  prefix, read and written; the project key and an `alias/aws/s3` key through S3; the pull of the
  application's image; the pass of itself to Glue; `datazone:CreateAsset` and `CreateListingChangeSet`,
  `lakeformation:GetDataAccess`, `secretsmanager:ListSecrets`; the table writes of `app_etl`; a Glue
  job's log group; the warehouse's credentials through the Data API. `glue:CreateDatabase` asked with
  no resource read `implicitDeny` under both documents.
- **[Claude] What the fence leaves, as the same role**, 18:38 UTC, each `allowed` under the attached
  boundary: `glue:CreateDatabase` and `DeleteDatabase` on the catalog and on `curated`;
  `lakeformation:BatchGrantPermissions` and `CreateDataCellsFilter`;
  `redshift-serverless:GetCredentials` through `sqlworkbench`, with `sqlworkbench:CreateConnection`
  and `DriverExecute`; the pull of `awsds-prod-ecr-app-etl` and of `awsds-prod-ecr-dev-env`;
  `datazone:GenerateCode`; `secretsmanager:ListSecrets`; `s3:PutAccessGrantsInstanceResourcePolicy`.
- **[Claude] Simulated as Staging's project role under its attached boundary**, 18:35 UTC, 39 decisions.
  16 `explicitDeny`, each matched in `awsds-staging-project-boundary`: `sts:AssumeRole` on
  `awsds-deploy-staging`; `kms:Decrypt` through S3 on the data key and on the state's key; `GetObject`
  and `PutObject` on `awsds-staging-outputs`, `GetObject` on `awsds-staging-derived` and on
  `awsds-staging-tfstate` with Access Grants credentials; `GetSecretValue` on a secret named
  `awsds-staging-*` and on one named `redshift!*`, the account holding none; Bedrock, AgentCore and the
  assistants as in Production. 22 `allowed`: the project's own prefix, the project key and an
  `alias/aws/s3` key through S3, the pull of the application's image from Production's registry (the
  identity side), the pass of itself to Glue, the domain's calls, the table writes of `app_etl`, a
  Glue job's log group.
- **[Claude] The simulator and the key statement**, 18:41 UTC: with no `kms:ResourceAliases` in the
  context, `kms:Decrypt` on the project key through S3 read `explicitDeny`, the fence's; with the key's
  alias in the context, `allowed`. GitLab's key read `explicitDeny` both ways (`SUP-008`).
- **[Claude] A simulation, not an exercise**: neither role has made a call but the provisioning's, and
  the application first runs as them at release F.
- **[Claude] Written**: decision 21's note, item 25 and step 7 of the ordered applies; `TM-30`, fenced,
  with what the fence leaves; `INV-22` and `AWS_STATE.md`'s row on the targets; the fence's row removed
  from `waiting-on-the-user.md`; the readings on `SUP-008` and `SUP-356`.
- **[Claude] What pass 4 still owes with nothing up**: the flag (4.7) and `awsds-deploy-staging`'s
  membership of `deploy-staging`, both the user's.

## 2026-11-12 — the user's acts: the flag off in both targets, `awsds-deploy-staging` an owner of `deploy-staging`; the readings after them

Nothing up. The three acts are the user's, as the infrastructure user from the project folder; every
call of Claude's in this entry is a read. The user, verbatim: *"Rodei os comandos:"*, the paste below,
then *"Fiz o merge."* The paste carries the commands and no output.

```text
➜  AWS-DataScience git:(main) NO_PROXY='*' aws lakeformation put-data-lake-settings --profile awsds-infra-prod --region us-west-2 --data-lake-settings "$(NO_PROXY='*' aws lakeformation get-data-lake-settings --profile awsds-infra-prod --region us-west-2 --query DataLakeSettings --output json | jq '.AllowFullTableExternalDataAccess = false')"
➜  AWS-DataScience git:(main) NO_PROXY='*' aws lakeformation put-data-lake-settings --profile awsds-infra-staging --region us-west-2 --data-lake-settings "$(NO_PROXY='*' aws lakeformation get-data-lake-settings --profile awsds-infra-staging --region us-west-2 --query DataLakeSettings --output json | jq '.AllowFullTableExternalDataAccess = false')"
➜  AWS-DataScience git:(main) NO_PROXY='*' aws datazone create-project-membership --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier 5ido8bej1zoeq8 --designation PROJECT_OWNER --member groupIdentifier=9bead345-cd5a-3881-abb8-e68cc17e2e9b --profile awsds-infra-staging --region us-west-2
```

- **[user] The three calls as the trails hold them** (read by Claude at 01:54 UTC):
  `PutDataLakeSettings` in Production at 01:50:08 UTC and in Staging at 01:50:16, each from the CLI as
  the account's `InfrastructureAccess` role, the whole structure with
  `allowFullTableExternalDataAccess` `false`; `CreateProjectMembership` in Staging's trail at
  01:50:26, `PROJECT_OWNER`, the group `9bead345-…` on `5ido8bej1zoeq8`. No event carries an error.
  This is step 4.7 in both targets and item 12's Staging half.
- **[Claude] Before the reads**, 01:53 UTC: both target profiles as `InfrastructureAccess`; Data
  Governance's and Sandbox's the same before their own reads.
- **[Claude] The settings after**, 01:53:33 UTC in Production and 01:53:34 in Staging: the three
  administrators (`InfrastructureAccess`, the provisioning role, the manage-access role),
  `CROSS_ACCOUNT_VERSION` 4 and `SET_CONTEXT` `TRUE`, both create-default lists empty, and no
  `AllowFullTableExternalDataAccess` key. A `false` written by the CLI reads back as an absent key, as
  the console's of 2026-10-25 did (`SUP-112`). Each trail holds four `PutDataLakeSettings` since
  2026-11-11 12:00 UTC, the provisioning's three and the user's: the database's environment, created
  after the project, and the fence's applies wrote none.
- **[Claude] The provisioning's three writes, read again in the same listing**: in each account one
  names `InfrastructureAccess` and the manage-access role, one the three administrators, and one the
  three administrators with `allowFullTableExternalDataAccess` `true`, the only one carrying the key.
  Staging's three are of 15:26:05 UTC. Production's first, the two administrators, is of 15:29:35 and
  the other two of 15:29:36, so the write that set Production's flag is of 15:29:36, a second after
  the time this log's entry on 4.6 gives the three. The flag stood 10 h 24 min in Staging and 10 h 20
  min in Production.
- **[Claude] No vend while it stood**, 02:01 UTC: `cloudtrail lookup-events` for `GetDataAccess` since
  2026-10-20 holds 48 events in Production, the last on 2026-10-26 (`awsds-prod-job-exec`), and 20 in
  Staging, the last on 2026-10-25 (`awsds-staging-job-exec`); neither holds one of 2026-11-11 or
  2026-11-12.
- **[Claude] `./aws/deploytargets.py`**, 01:55 to 01:57 UTC: `DT-13` passes in both targets, *"0
  check(s) FAILED"* where 18:29 UTC read 2. Against that snapshot the report differs in the flag's two
  rows, `DT-13`'s two and the order of the administrators (`SUP-108`), and in nothing else. The script
  exits 1 on its section 14, the liveness probes of the ten profiles whose users are not signed in.
- **[Claude] The flag in the four accounts**, 02:01:53 UTC: `true` in Sandbox and in Data Governance,
  absent in Staging and in Production.
- **[Claude] `deploy-staging`'s members**, 01:54:47 UTC, `list-project-memberships` as
  `awsds-infra-staging`: the group `65b0f127-…`, `PROJECT_OWNER`; the user `081362b4-…`,
  `PROJECT_CONTRIBUTOR`, which `get-user-profile` gives as the project role's own profile; the group
  `9bead345-…`, `PROJECT_OWNER`. `get-group-profile` from the domain's account at 01:59 UTC gives
  `9bead345-…` as `awsds-deploy-staging`'s and `65b0f127-…` as Staging's `InfrastructureAccess`
  role's, both `ASSIGNED`; from Staging the same call is refused to `InfrastructureAccess`, *"no
  resource-based policy allows the datazone:GetGroupProfile action"* (`SUP-157`). The deploy role has
  made no call as a member: its first is release F's.
- **[user] PR #288 merged**, 01:44:55 UTC, squashed into `37de14cc` on `main`; the tree is the branch
  head's (`4bf88079`, an empty diff) and the remote branch is deleted, so the six slices applied from
  the branch are on `main`. This entry and its documents are on `claude/stage-19-pass-4-flag-off`, cut
  from that commit in the same worktree.
- **[Claude] Written**: 4.7 done, items 8 and 12 and the ordered applies' fifth step; `EXC-23` closed,
  the flag's row and the targets' row in `AWS_STATE.md`; `TM-26`, both targets' halves closed; the
  flag's row removed from `waiting-on-the-user.md` and the membership's cut to Production's half;
  `SUP-112` retitled, with the two readings of how the flag is turned off.
- **[Claude] What pass 4 owes with nothing up**: nothing. `awsds-deploy-prod`'s membership of
  `deploy-production` waits for the role's first call, and verification xx for 4.10 and 4.12, both
  release F's.

## 2026-11-12 — release F written with nothing up: the chain layer, the grants around a deploy, the template's stages and the legs

Nothing up. The user, verbatim: *"Faça esta tarefa aqui: “Stage 19: release F, os legs da CLI de CI/CD”"*,
then, while the work ran, *"fiz o merge do #289"*. Every AWS call of this entry is a read; nothing was
applied and nothing reached GitLab. One module tag was pushed to GitHub.

- **[user] PR #289 merged**, 02:22:37 UTC, squashed into `36bcf916`. This entry's work is on
  `claude/stage-19-release-f`, cut from that commit in the same worktree, and is PR #291.
- **[Claude] Read in the CLI 1.0.9's installed code** before any design: `helpers/context_resolver.py`
  writes each `{env.VAR}` of a workflow as `{{ params.VAR }}` and resolves `{proj.*}`, `{domain.*}` and
  `{stage.name}` at the deploy; `workflows/operations.py` and `commands/run.py` pass the stage's
  `environment_variables` as `OverrideParameters` (`SUP-282`); `helpers/airflow_serverless.py` names a
  workflow `<application>_<project>_<workflow>` and, on `ConflictException`, updates it in place; the
  manifest's schema takes `content.catalog` (`enabled`, `skipPublish`, `connectionName`,
  `assets.access`) and a stage's `bootstrap` actions `workflow.create` and `workflow.run` (`wait`,
  `trailLogs`). In the service's model `ListWorkflows` answers `Workflows[]` with `Name` and
  `WorkflowArn`, 100 a page at most, and `StartWorkflowRun` takes `OverrideParameters`.
- **[Claude] Read in AWS as `InfrastructureAccess`**: at 02:55 UTC each project's security group,
  `datazone-<project>-dev`, admits itself inbound and every destination outbound, in Staging and in
  Production; at 03:01 UTC `deploy-staging` holds the environments `Tooling` (`d6nu5aphq1e974`) and
  `deploy-staging-app-etl`, and the first answers its `provisionedResources` by name, the subnets,
  the security group, the key and the shared prefix among them (`SUP-359`).
- **[Claude] The chain layer**: `terraform-modules/orchestration` rewritten without the workflow
  resource. Planned from a local copy against both targets, and the three definitions it rendered
  for Production answered *"result": "OK"*, no diagnostic, to `stepfunctions
  validate-state-machine-definition` at 02:45 UTC. Committed as `b335ca31` and tagged
  `orchestration-v0.3.0`, origin's newest being `v0.2.1`; the tag and the branch pushed. The slices
  `staging/chains/` and `production/chains/` initialised on the tag, the provider locked at 6.73.0 on
  three platforms, and planned at 02:52 UTC: *"Plan: 24 to add, 0 to change, 0 to destroy."* in
  Production, *"Plan: 18 to add"* in Staging, saved as `$HOME/tmp/stage19-chains-<account>.tfplan`.
- **[Claude] The grants around a deploy**, planned 02:57 to 03:00 UTC and saved as
  `$HOME/tmp/stage19-f-<account>-<slice>.tfplan`: both `studio/` slices *"Plan: 2 to add, 2 to
  change, 0 to destroy."*, the boundary and the person-session policy changed in each, Production
  adding `awsds-prod-warehouse-load` and its attachment, Staging the deploy role's two `DESCRIBE`
  grants on `app_etl`; both `foundation/` slices *"Plan: 0 to add, 1 to change, 0 to destroy."* with the
  alerts var-file, `awsds-<env>-deploy-project` at 16 statements and 4,564 characters of 6,144;
  `production/warehouse/` *"Plan: 1 to add"*, the ingress from `deploy-production`'s security group.
- **[Claude] The slices release F retires, previewed** with `plan -destroy` at 03:15 UTC: 41 to
  destroy in `production/orchestration/`, 3 in `production/app/app-etl/`; Staging's two answer *"No
  objects need to be destroyed"*. Nothing destroyed.
- **[Claude] The template**, `examples/app-etl/`: the manifest's stages `dev`, `staging` and `prod`
  with `content.catalog` and `app-etl-warehouse`; that workflow's task creating its job; the load
  reading the product table; the legs; `product.json` and its guard; `scripts/dev-cli.sh`'s
  placeholders. 84 tests passed, 1 skipped. The CLI's `describe` lists the three targets and the
  `prod` stage's four bootstrap actions. `scripts/deploy-application.py --check` at 03:07 UTC read
  both projects, the caller a member of each; `--self-check` passes and joins `make check`.
- **[Claude] The lint**: the rule `manifest` rewritten over a copy of `awsds-workflows` at
  `d856982c`, in the session's scratch folder: the catalog item passes with `skipPublish` true and no
  `assets.access`. That copy's suite reads 373 passed and 7 failed, the pinned commit's own 367 and
  7; the patched lint answers the template *"ok: 9 arquivo(s)"*, and the pinned one *"manifest.yaml:
  manifest: content.catalog.enabled: o bundle levaria o que o projeto tem, e não a tag"*. Nothing was
  written in that repository. One `git fetch origin` ran in the user's checkout of it, which moved its
  remote-tracking refs and nothing else.
- **[Claude] Three choices the plan did not hold, written as decisions 22 to 24, the user's**: every
  stage reads the inbox, the governed read and the project role's lake grant unwritten (22); a chain's
  run takes the stage's variables from an SSM parameter the leg records (23); the Staging test reads
  the product table's metadata under `DESCRIBE`, the Athena read unwritten (24).
- **[Claude] Written**: the stage file's §Release F as written, items 13, 23 and 26 to 32, steps 3.1,
  3.3, 4.9 and 4.11, verifications xxviii to xxxii and decisions 22 to 24; `SUP-359`;
  `runbooks/promotion.md` §N.8.4; `TM-30`; the waiting list; conventions §6 and
  `terraform-live/README.md` for the two slices.
- **[Claude] Left for the user**: the three applies that need nothing up, each on a word naming it;
  the word to open the lint's pull request; decisions 22 to 24. No workflow of release F has run:
  every reading of the CLI in a target is 4.10's.

## 2026-11-12 — release F: the leg's deploy exercised over stubs

The same sitting, no AWS call. Claude's hand.

- **[Claude] `scripts/deploy-application.py`'s deploy path**, run with the project's values, the
  membership, the state read, the workflow listing and the SSM record replaced by stubs and a stand-in
  for the CLI: the bundle is extracted beside the tag's manifest, the stand-in runs there with
  `--bundle-archive-path` and reads the target stage's variables from the project and a placeholder
  for the other stages'; a clean run exits 0 with the nine stage variables recorded and the dotenv
  written; an import reporting `Failed: 2`, a CLI exiting 1 and a bundle whose SHA256 differs each
  exit 1 with nothing recorded. The CLI's output now reaches the job's log as it comes, since
  Production's deploy follows a run. What the real CLI prints in a target is verification xxx's.

## 2026-11-12 — release F's applies that need nothing up: both `studio/` slices, both `foundation/` slices, `production/warehouse/`

Nothing up. The user, verbatim: *"Autorizo os 5 applies"*, then, while they ran, *"Fiz o merge do
#290. Peço sincronizar."* The five applies are Claude's, as `InfrastructureAccess` in Staging and in
Production, each from the plan saved at 02:57 to 03:00 UTC; every other AWS call of this entry is a
read.

- **[Claude] Before the applies**, 03:37 to 03:40 UTC: both target profiles as `InfrastructureAccess`;
  the branch clean at `6a8b22a7`; the two other sessions on this machine told, *"Otimização de arquivos
  de memória"* and *"Worktrees para apagar"*.
- **[Claude] The applies**, one command each, each exit 0:

  | Slice | Profile | UTC | Terraform's count | What it wrote |
  |---|---|---|---|---|
  | `staging/studio/` | `awsds-infra-staging` | 03:40:12 to 03:40:27 | *"2 added, 2 changed, 0 destroyed"* | the boundary, the person-session policy, the deploy role's two Lake Formation grants |
  | `production/studio/` | `awsds-infra-prod` | 03:40:40 to 03:40:54 | *"2 added, 2 changed, 0 destroyed"* | the boundary, the person-session policy, `awsds-prod-warehouse-load` and its attachment |
  | `staging/foundation/` | `awsds-infra-staging` | 03:41:07 to 03:41:19 | *"0 added, 1 changed, 0 destroyed"* | `awsds-staging-deploy-project` |
  | `production/foundation/` | `awsds-infra-prod` | 03:41:39 to 03:41:51 | *"0 added, 1 changed, 0 destroyed"* | `awsds-prod-deploy-project` |
  | `production/warehouse/` | `awsds-infra-prod` | 03:42:03 to 03:42:13 | *"1 added, 0 changed, 0 destroyed"* | the ingress rule `sgr-021fb49c3c05b5697` |

  Each apply's count is its plan's: the person-session policy's document changed, so the difference
  `SUP-356` records does not appear.
- **[user] PR #290 merged**, 03:40:47 UTC, as `f878d781`, while the applies ran.
- **[Claude] `origin/main` merged into the branch**, commit `5d98178a` at 03:43:48 UTC, pushed:
  `CLAUDE.md`, `docs/GENERAL_PLAN.md`, `docs/log/INDEX.md` and `docs/plan/stages/INDEX.md` conflicted
  on Stage 19's status text and each takes `main`'s version. `main`'s commit changes nothing under
  `terraform-live/` or `terraform-modules/`.
- **[Claude] The re-plans**, 03:44:15 to 03:45:51 UTC from the merged tree, `-detailed-exitcode` 0 on
  each of the five: *"No changes. Your infrastructure matches the configuration."* The two
  `foundation/` plans took the alerts var-file.
- **[Claude] `./aws/deploytargets.py`**, 03:45:57 to 03:47:59 UTC: 42 rows `pass`, none failing and
  none a note; `DT-13` reads the flag off in both targets and `DT-14`'s six rows pass in each, the
  fence *"5 statements present"*. Exit 1 on its section 14, the ten profiles whose users are not
  signed in.
- **[Claude] What the applies left**, read 03:50 to 03:52 UTC:
  - `awsds-staging-project-boundary` at `v3` (03:40:23), 14 statements, 3,474 characters; its
    `DenyServicesNoProjectUsesHere` names `sqlworkbench:*`, `redshift:*`, `redshift-serverless:*`,
    `redshift-data:*`, `q:*`, `codewhisperer:*`, `bedrock:*` and `bedrock-agentcore:*`.
    `awsds-prod-project-boundary` at `v3` (03:40:49), 15 statements, 3,801 characters; the same
    statement without `redshift:*` and `redshift-serverless:*`. Each is the boundary of three roles.
  - `awsds-<env>-person-session-deny` at `v2` in both (Staging 03:40:25, Production 03:40:51), five
    statements: `DenyAPersonOpeningAWarehouseSession` denies `redshift-data:*`,
    `redshift-serverless:GetCredentials` and `sqlworkbench:*` where `aws:SourceIdentity` is present.
  - `awsds-prod-warehouse-load` at `v1` (03:40:49), one statement, `redshift-serverless:GetCredentials`
    and `GetWorkgroup` on the account's workgroups, attached to `deploy-production`'s role alone. That
    role carries six managed policies and `deploy-staging`'s five.
  - `awsds-<env>-deploy-project` at `v2` in both (Staging 03:41:17, Production 03:41:49), 16
    statements, 4,579 characters in Staging and 4,564 in Production:
    `RecordTheStageVariablesOfADeploy` on `/awsds/<env>/applications/*/stage-variables`,
    `PassTheProjectRoleToSageMaker` on the project's role, `ReadTheProductTablesMetadata` on `app_etl`.
  - Lake Formation in Staging: `awsds-deploy-staging` holds `DESCRIBE` on the database `app_etl` and
    `DESCRIBE` on its tables' wildcard, neither grantable. The database's other rows are the
    provisioning role's, the manage-access role's and the conditioned `IAMPrincipals` ones.
  - The governed warehouse's security group `sg-0f018ef6c4848a9a3` holds two ingress rules, both TCP
    5439: the job security group's (Stage 9 step 9.1) and `sgr-021fb49c3c05b5697`, from
    `sg-096dbe4cec76019dd`, which is `datazone-d7qcazihvr3s7k-dev`.
- **[Claude] Each project role simulated**, 03:49 UTC, `iam simulate-principal-policy` with the Region,
  the organization, the account and the role's own tags as context. A worker's session carries no
  `aws:SourceIdentity` and a person's does:

  | Call | Production, a worker | Production, a person | Staging, either |
  |---|---|---|---|
  | `redshift-serverless:GetCredentials` | `allowed`, by `awsds-prod-warehouse-load` | `explicitDeny`, the person-session policy | `explicitDeny`, the boundary; a person by the person-session policy too |
  | `redshift-serverless:GetWorkgroup` | `allowed` | `allowed` | `explicitDeny`, the boundary |
  | `redshift-data:ExecuteStatement`, `GetStatementResult` | `explicitDeny`, the boundary | `explicitDeny`, both policies | `explicitDeny` |
  | `sqlworkbench:CreateConnection` | `explicitDeny`, the boundary | `explicitDeny`, both policies | `explicitDeny` |
  | `redshift:GetClusterCredentials` | `implicitDeny`, context keys missing | the same | `explicitDeny`, the boundary |

  The simulator reads the policies and opens no session: the load's session is verification xxxii's.
- **[Claude] `DT-14` reads the fenced services**: a row added to `aws/deploytargets.py`, the
  services each account's `fence.tf` names against the boundary's
  `DenyServicesNoProjectUsesHere`. Run 03:58:09 to 04:00:08 UTC: 44 rows `pass`, none failing; the
  new row reads `bedrock`, `bedrock-agentcore`, `codewhisperer`, `q`, `redshift-data` and
  `sqlworkbench` in Production and the same with `redshift` and `redshift-serverless` in Staging.
- **[Claude] Written**: items 13, 24 and 27 to 29, §Release F as written's act 1 and the status row;
  `runbooks/promotion.md` §N.8.4 steps 1 to 3; `TM-30`; `AWS_STATE.md`'s targets row and the
  boundary's invariant; `SUP-356`'s complementary reading; the applies' row removed from the waiting
  list; `terraform-live/README.md`, `SMUS.md` and `aws/INDEX.md` for the fence; `NETWORK.md` for the
  warehouse's rule; `CLAUDE.md`'s row for Stage 19 in the form PR #290 gave it.
- **[Claude] What release F owes with nothing up**: the lint's pull request, on the user's word, and
  decisions 22 to 24. Both `chains/` slices stay unapplied: they are the promotion sitting's
  (`runbooks/promotion.md` §N.8.4).

## 2026-11-12 — the lint's pull request opened in `awsds-workflows`

Nothing up, no AWS call. The user, verbatim: *"Sim, abrir"*, to the question whether to open the
lint's pull request in that repository. Claude's hand; the writes are to GitHub, one branch and one
pull request in `awsds-workflows`.

- **[Claude] The repository as found**, 04:16 UTC: `origin/main` at `d856982`, the template's pin,
  with no commit after it and no open pull request; the user's checkout on `main` at `ff25eae`, one
  commit behind since this session's fetch, clean and not touched. The work ran in a clone of its
  own, in the session's scratch folder.
- **[Claude] Read again in the CLI 1.0.9's code** before the rule's wording went out:
  `helpers/catalog_import.py` publishes each imported asset and data product unless
  `skip_publish`, its docstring saying *"published only if they were published (listingStatus ==
  "ACTIVE") in the source project"*; `commands/deploy.py` hands each `assets.access` entry to
  `helpers/datazone.py`, which creates a subscription request for the target project unless one
  exists, waits for its approval and reads its grants; `application-manifest-schema.yaml` states
  that `enabled` exports every catalog resource the project owns and what `skipPublish` false
  publishes; `connectionName` under `content.catalog` is kept in the manifest's model and read by
  no command.
- **[Claude] The branch** `claude/lint-catalogo-skip-publish`, cut from `d856982`: item 23's patch,
  which applied clean, with three docstrings reworded and the refusal's last clause now *"com
  true, quem publica é uma task do workflow"*; that repository's guide (the rule's row and a
  warning that an enabled catalog carries what the stage's project owns), its lab notes and its
  memory. Two commits, `1b41a70` and `ea8f86f`.
- **[Claude] Checked there**: the six new cases fail on `d856982`'s `lint.py` and pass on the
  branch; the suite reads 373 passed, 7 failed and 2 skipped on the laptop, the seven being that
  repository's `prepare-offline` tests, which refuse a Mac (*"esta máquina é Darwin arm64, e a
  pasta só serve ao job preparada em Linux x86_64"*); `ruff check` and `ruff format --check`
  clean; the `pdoc` site builds. The branch's lint on `examples/app-etl/` with the pipeline's
  options, 04:22 UTC: *"ok: 9 arquivo(s)"*; `d856982`'s: *"manifest.yaml: manifest:
  content.catalog.enabled: o bundle levaria o que o projeto tem, e não a tag"*, exit 1. By the
  command on copies of that repository's `probe-worker`: the catalog on with no `skipPublish`,
  exit 1; with an `assets.access` entry, exit 1; in the admitted form, `ok`.
- **[Claude] The pull request**, 04:24:15 UTC:
  [`awsds-workflows` PR #25](https://github.com/felipenoris/awsds-workflows/pull/25), 8 files. Its three
  test jobs, Python 3.12, 3.13 and 3.14 on Ubuntu, ended `SUCCESS` by 04:25:00 UTC. The merge is
  the user's.
- **[Claude] Written here**: item 23, act 2, the status row and sitting 5 of the stage file;
  `runbooks/promotion.md` §N.8.4 step 4; the waiting list's row, now the merge; `REFERENCES.md`;
  `CLAUDE.md`'s row.
- **[Claude] What follows the merge**: the template's `AWSDS_WORKFLOWS` takes the merge commit, in
  this repository and then in release F's merge request.

## 2026-11-12 — decisions 22 to 24 taken by the user, each as (a)

Nothing up, no AWS call. Claude asked *"As decisões 22 a 24 ficam como recomendado?"* and the
user answered, verbatim: *"Sim, como recomendado"*. Claude's hand for the records.

- **[user] Decision 22 (a)**: release F reads the inbox in every stage; the governed read, with
  the project role's lake grant and the deny's growth to the lake, is a later release's (item 32).
- **[user] Decision 23 (a)**: a run a chain starts takes the stage's variables from the SSM
  parameter the leg records.
- **[user] Decision 24 (a)**: Staging's integration test reads the product table's metadata under
  `DESCRIBE`; the Athena read is not written, which amends decision 14 (d).
- **[Claude] Written**: the three decisions and decision 14's amendment in the stage file, with
  its status row, items 13 and 32, step 4.11's note and verification xxvii; the template's
  README; the row removed from the waiting list; `CLAUDE.md`'s row. No code changed: the
  template, the scripts and the slices were written under (a), and the applies of 03:40 to 03:42
  UTC carry 23's and 24's grants.

## 2026-11-12 — both pull requests merged by the user; the template's pin on the lint's merge commit

Nothing up, no AWS call. The user, verbatim: *"Fiz o merge do #25 e do #291"*. Claude's hand for
the pin and the records.

- **[user] `awsds-workflows` PR #25 merged**, 13:04:13 UTC, squashed into `196acee` on that
  repository's `main`; its tree is the branch head's (`ea8f86f`, an empty diff).
- **[user] PR #291 merged**, 13:04:29 UTC, squashed into `51bb0bc6` on `main`; the tree is the
  branch head's (`82248a17`, an empty diff) and the remote branch is deleted, so the five slices
  applied from the branch at 03:40 to 03:42 UTC are on `main`. This entry is on
  `claude/stage-19-lint-pin`, cut from that commit in the same worktree.
- **[Claude] The pin**: `AWSDS_WORKFLOWS` in `examples/app-etl/.gitlab-ci.yml` from `d856982c` to
  `196aceec092649551ed6451796b1c3c7983cfafb`. Run as the `test` job runs it, `uvx --from` the
  variable's value with the file's `--image-repository`, seven `--instance-type` and one
  `--algorithm-repository`, 13:06 UTC: the new pin answers *"ok: 9 arquivo(s)"*, exit 0; the old
  one *"manifest.yaml: manifest: content.catalog.enabled: o bundle levaria o que o projeto tem, e
  não a tag"*, exit 1. The template's tests read 84 passed and 1 skipped, and
  `scripts/check-gitlab-ci.py` passes.
- **[Claude] Release T's template is unchanged**: the tree of `36bcf916`, whose pin is `d856982c`
  and whose one-stage manifest that lint passes.
- **[Claude] Written**: item 23, act 2, the releases table, the status row and sitting 5 of the
  stage file; `runbooks/promotion.md` §N.8.4 step 4; the merge's row removed from the waiting
  list; `REFERENCES.md`; `CLAUDE.md`'s row.
- **[Claude] Not touched**: the user's checkout of `awsds-workflows`, on `main` at `ff25eae`, two
  commits behind its origin.

## 2026-11-14 — the project for app-etl alone created by the user; its role planned in `sandbox/workflows/`

Nothing up. Every AWS call of Claude's in this entry is a read; the project and its member dialog
are the user's acts in the portal, as the data scientist. The user, verbatim, over the sitting:
*"Me oriente em relação aos próximos passos que tenho que executar."*, the choice *"Projeto do
app-etl"*, then *"Criei o projeto app-etl-dev e adicionei o primeiro membro. Sobre
InfrastructureAccess, esse nome não aparece na lista.. Mas aparecem alguns nomes com prefixo
"AWSReservedSSO_InfrastructureAccess_", mas não consigo distinguir qual deles é o
InfrastructureAccess alvo."*

- **[user] Since the last entry**: PR #292 merged on 2026-11-12 at 13:16:02 UTC, squashed into
  `1c25ac52`, the tree the branch head's; the user's checkout of `awsds-workflows` fast-forwarded
  to `196acee` the same day. This entry is on `claude/stage-19-release-t-dev-project`, cut from
  `1c25ac52` in the same worktree.
- **[Claude] Read before the act**, from 01:49 UTC on 2026-11-14, as `InfrastructureAccess` in
  Sandbox and in Data Governance: the domain holds six projects; Sandbox holds two SageMaker AI
  domains, the two `Tooling` ones, under a quota *Total domains* of 500.
- **[user] The project**, `app-etl-dev`, from the profile `experimentation`: `CreateProject` in the
  domain account's trail at 02:06:28 UTC, by the domain's execution role in the data scientist's
  session. Read at 02:23 UTC: id `ceweti7jbiu1hs`, `ACTIVE`; one environment, `Tooling`
  (`6kvndq6t2757rk`), `ACTIVE`; in Sandbox the role
  `datazone_usr_role_ceweti7jbiu1hs_6kvndq6t2757rk`, created 02:07:04 under
  `awsds-sandbox-project-boundary` (`get-role`; `list-roles` carries no boundary field), and
  the two Bedrock roles the blueprint makes; a third SageMaker AI domain, `d-spi9kgo6x5b4`,
  `InService`; and the data source `Tooling-default-sagemaker-modelpackagegroup-datasource`,
  `READY` on `cron(7 2 * * ? *)`, the one `EXC-11` covers by name.
- **[Claude] The members, read twice**, 02:23:51 and 02:26:49 UTC, as `awsds-infra-sandbox-1`, no
  member of the project: the owner, an SSO user profile, and a `PROJECT_CONTRIBUTOR` whose `IAM`
  profile is the project's own role; no group. The domain account's trail, read to 02:22:01 UTC,
  holds the project's `CreateProject` and no `CreateProjectMembership`; its reads of those minutes
  are the portal's dialog, `SearchUserProfiles` 16 times and `SearchGroupProfiles` 10. The bundle
  role's membership was therefore not written when this was read.
- **[Claude] The name the portal lists for a role's group** is the role's own:
  `get-group-profile` from the domain's account answers each `IAM_ROLE_SESSION_GROUP` profile's
  `rolePrincipalArn`. Sandbox's `InfrastructureAccess` is
  `AWSReservedSSO_InfrastructureAccess_59e5b26af457128d` (the group `839bcde8-…`), read in Sandbox's
  IAM and as `awsds-infra-sandbox-1`'s caller; the same prefix with `ba1899ccb658ab35` is Data
  Governance's, `7edd72025c361e9b` Staging's, `c2bcabf74c885115` Production's and
  `a6d31eda0e5de20c` Identity's. The bundle role's group is `06d426f2-…`.
- **[Claude] `sandbox/workflows/`**: the project's role added to `project_roles` and the slice
  planned at 02:25:51 UTC as `awsds-infra-sandbox-1`: *"Plan: 1 to add, 3 to change, 2 to
  destroy."* The addition is the workflows policy on the new role. The rest is the bundle role's
  narrowing, written on 2026-11-11: the ceiling denies every `iam:PassRole` and loses the
  `DeleteWorkflow` deny, `project-reads` trades `ec2:DescribeVpcEndpoints` for the catalog export's
  four DataZone reads, and the inline policies `storage` and `workflows` go. Saved as
  `$HOME/tmp/stage19-t-sandbox-workflows.tfplan`; not applied.
- **[Claude] Written**: items 16 to 18, step 1.5 and the status row of the stage file;
  `runbooks/promotion.md` §N.8.2 step 0 with the project's id; the waiting list's row; `EXC-11`;
  `terraform-live/README.md`; `CLAUDE.md`'s row.
- **[Claude] Owed**: the user's confirmation of the member dialog, then the members read again;
  the apply, on the user's word; the bundle role's removal from `test-experimentation`.

## 2026-11-14 — `sandbox/workflows/` applied: the bundle role narrowed, the workflows policy on `app-etl-dev`'s role; the project's members

Nothing up. The user, verbatim: *"Autorizo o apply"*, the answer to *"Autoriza o apply de
sandbox/workflows/ no Sandbox Account 1?"*, then, while the turn ran, *"Adicionei o membro
`AWSReservedSSO_InfrastructureAccess_59e5b26af457128d`no projeto novo"*. The apply is Claude's, as
`InfrastructureAccess` in Sandbox; every other AWS call of this entry is a read.

- **[user] The members written**, in the portal: at 02:41:49 UTC `app-etl-dev` lists its owner,
  its own role and two groups, each `PROJECT_CONTRIBUTOR`: `06d426f2-…`, the bundle role
  `awsds-deploy-sandbox-test`'s, and `839bcde8-…`, Sandbox's `InfrastructureAccess`. Item 17's
  membership half.
- **[Claude] Before the apply**, 02:41 UTC: the Sandbox and Production profiles as
  `InfrastructureAccess`, the slice's second provider reading the runner's account; the branch
  clean at `4bd414d5`; the four other sessions of this repository told, *"SMUS CI/CD
  multi-account deployment"*, *"Releitura quinzenal de upstream-releases.md"*, *"Otimização de
  arquivos de memória"* and *"Worktrees para apagar"*.
- **[Claude] The apply**, 02:42:20 to 02:42:32 UTC, from the plan saved at 02:25: *"Apply
  complete! Resources: 1 added, 3 changed, 2 destroyed."* The re-plan at 02:42:47 UTC: *"No
  changes. Your infrastructure matches the configuration."*
- **[Claude] What it left**, read 02:42:59 UTC: `awsds-deploy-sandbox-test` holds one inline
  policy, `project-reads`, of three statements (`ReadTheProjectItsMembersAndItsConnections`,
  `ReadTheDomain`, `ExportTheCatalogTheProjectOwns`), and no managed policy; its ceiling
  `awsds-sandbox-deploy-test-boundary` is at `v2` of 02:42:29, four statements,
  `DenyEveryRoleChangeAndEveryPassRole` the first. `app-etl-dev`'s role carries AWS's three managed
  policies and `awsds-sandbox-workflows`.
- **[Claude] The bundle role simulated**, 02:44 to 02:45 UTC, the Region in the context:
  `iam:PassRole` of `app-etl-dev`'s role and of `test-experimentation`'s reads `explicitDeny`, the
  ceiling's; the MWAA Serverless writes, `glue:CreateJob`, `datazone:CreateAsset`,
  `CreateListingChangeSet`, `StartDataSourceRun` and `CreateProjectMembership` read
  `implicitDeny`; `s3:PutObject`, `GetObject` and `DeleteObject` on both projects' `shared/`
  prefixes read `implicitDeny` with the organization's id in the context (`SUP-008`); the
  project's reads and the catalog export's four read `allowed`. Simulated with the domain's ARN as
  the resource, those reads but `GetDomain` read `implicitDeny` under an allow on `*`, a reading
  appended to `SUP-008`.
- **[Claude] `./aws/cicd.py`**, 02:43:25 to 02:44:19 UTC: 12 rows `pass`, none failing, the four
  notes the runners' absence between sittings, the parity at one image and the excused
  assumptions of 2026-10-13; `CI-2` reads the role under its ceiling. Exit 1 on its section 10, the
  profiles whose users are not signed in.
- **[Claude] What changes for a release**: no job can deploy as `awsds-deploy-sandbox-test`, so
  GitLab's `main`, which still runs `test-deploy`, fails there until release T's merge request;
  no tag before it.
- **[Claude] Written**: items 15, 17 and 18, step 1.5 and the status row of the stage file;
  `runbooks/promotion.md` §N.8.2 step 0; the waiting list's row; `INT-25`; `SUP-008`;
  `terraform-live/README.md`; `CLAUDE.md`'s row.
- **[Claude] Owed**: the bundle role's group removed from `test-experimentation`, the user's;
  then release T's GitLab sitting.

## 2026-11-14 — the bundle role's removal from `test-experimentation` refused to a contributor

Nothing up. The user's hand for the attempt, from the project folder; Claude's calls are reads. The
user, verbatim: *"Fiz o merge do #295."*, then *"Tentei rodar o comando para remover o papel do
test-experimentation, mas falhou:"* and the paste below.

```text
AWS-DataScience git:(main) NO_PROXY='*' aws datazone delete-project-membership --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier 4gqfau9xuo6e4w --member groupIdentifier=06d426f2-84d6-38ae-a991-6806981d9520 --profile awsds-infra-sandbox-1 --region us-west-2

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the DeleteProjectMembership operation: User is not permitted to perform operation: DeleteProjectMembership DesignationPolicy does not allow access.
```

- **[user] PR #295 merged**, 02:51:10 UTC, squashed into `52a8e718`, so `sandbox/workflows/` as
  applied is on `main`. This entry is on `claude/stage-19-release-t-membership`, cut from that
  commit in the same worktree.
- **[Claude] The command was Claude's**, handed over from `runbooks/promotion.md` §N.8.2 step 0 as
  written on 2026-11-11, with the caveat that a contributor might be refused. The refusal is
  DataZone's own layer, not IAM's (`SUP-157`).
- **[Claude] `test-experimentation`'s members**, 02:53 UTC: the owner, the data scientist's SSO
  profile; the project's own role; and two groups, Sandbox's `InfrastructureAccess` (`839bcde8-…`)
  and the bundle role's (`06d426f2-…`), each `PROJECT_CONTRIBUTOR`. The caller holds the
  contributor designation, whose description of 2026-10-30 leaves member management to
  `PROJECT_OWNER`.
- **[Claude] Written**: the runbook's step with both membership writes as the owner's portal
  acts, its two commands for the infrastructure role removed; item 17; the waiting list's row; a
  reading appended to `SUP-157`.
- **[Claude] Owed**: the removal in the portal, as the data scientist, then the members read
  again.

## 2026-11-14 — the bundle role's group removed from `test-experimentation` by the user; release T prepared with nothing up

Nothing up. The user's act in the portal, as the data scientist; Claude's calls are reads. The
user, verbatim: *"Removi o membro pelo portal e fiz o merge do #296"*.

- **[user] PR #296 merged**, 03:19:16 UTC, squashed into `f29b8fdc`. This entry is on
  `claude/stage-19-release-t-prepared`, cut from that commit in the same worktree.
- **[user] The removal**: `DeleteProjectMembership` on `test-experimentation` for the group
  `06d426f2-…` at 03:18:53 UTC, with no error, by the domain's execution role in the data
  scientist's session, in the domain account's trail.
- **[Claude] The same trail, read to 03:18:53 UTC, holds the day's other membership writes**:
  two `CreateProjectMembership` on `app-etl-dev`, the bundle role's group at 02:41:09 and
  Sandbox's `InfrastructureAccess` group at 02:41:10, each `PROJECT_CONTRIBUTOR`, the portal's;
  and two `DeleteProjectMembership` on `test-experimentation` refused `AccessDenied`, at 02:51:35
  and 02:52:18, each by a session of Sandbox's `InfrastructureAccess` role, whose role id is the
  event's `principalId` and whose ARN the cross-account record leaves null; the user pasted one.
- **[Claude] The members after**, 03:19:58 UTC, as `awsds-infra-sandbox-1`:
  `test-experimentation` lists its owner, its own role and Sandbox's `InfrastructureAccess`
  group; `app-etl-dev` its owner, its own role, the bundle role's group and Sandbox's
  `InfrastructureAccess` group.
- **[Claude] Release T's preparation with nothing up is done** (`runbooks/promotion.md` §N.8.2
  step 0, items 15 to 18): the project, the bundle role's membership of it and of no other, the
  role narrowed, the project's role in `project_roles`. Left for the GitLab sitting: the
  template's merge request from `36bcf916`, `DEV_PROJECT_NAME` as `app-etl-dev`, the four
  `TEST_PROJECT_*` variables removed, the tag.
- **[Claude] Written**: item 17; the waiting list's row; `INT-25`; the runbook's step; the
  Sandbox row of `AWS_STATE.md`.

## 2026-11-14 — pass 2 read against the estate before its portal acts

Nothing up; every AWS call a read, as `InfrastructureAccess` in Sandbox and in Data Governance.
The user, verbatim: *"Fiz o merge do #297. Me oriente em relação ao pass 2 no portal."*

- **[user] PR #297 merged**, 03:22:39 UTC, squashed into `53e66180`. This entry is on
  `claude/stage-19-pass-2-readings`, cut from that commit in the same worktree.
- **[Claude] `eighth-experimentation`**, 03:25 to 03:26 UTC: its members are the owner, the project
  role's profile and Sandbox's `InfrastructureAccess` group, the Governance Manager no member
  yet; it owns the assets `house-price`, `trades` and `trades_notional` and the data product
  `my-data-product`, and no `trades-notional`; `trades_notional` is at revision 7, its listing
  `ct5d0innrgw3v4` `ACTIVE`, the form `classification` on it; no subscription or request names
  the project as approver. The Governance Manager's SSO profile in the domain is `ACTIVATED`.
- **[Claude] The approval the plan names may not happen.** Pass 2's step 3 has the Governance
  Manager approve. The data scientist owns the producer and whatever consumer that user
  creates, and AWS's approval page, read 2026-10-18 for 6f 2.1, approves at creation a request
  whose requester is a member of the owning project. Unmeasured in this estate: 6f 11.8's
  request waited, its requester a member of one project alone.
- **[Claude] `test-experimentation` as the consumer**, 03:26 to 03:28 UTC: its environment
  `test-experimentation-lakehouse` holds the target
  `test-experimentation-lakehouse-default-target` for Glue tables and views; its connections
  include `project.spark.fineGrained`, `project.athena` and `project.default_lakehouse`; its
  domain carries the house image. Decision 5 set it aside as the project that received the
  application, which ended with decision 19 (c).
- **[Claude] The house image on the three Sandbox domains**, 03:28:38 UTC: `eighth-experimentation`'s
  and `test-experimentation`'s carry `awsds-sandbox-dev-env`, version-less, on JupyterLab and the
  Code Editor; `app-etl-dev`'s, `d-spi9kgo6x5b4`, carries none. No domain holds a space.
- **[Claude] Written**: the reading under pass 2's sitting; item 33, the attach owed to
  `app-etl-dev`'s domain; the runbook's step 13; two rows of the waiting list, the attach's word
  and the consumer's choice.

## 2026-11-14 — pass 2's portal half done by the user: the product shared to `test-experimentation` and read

Nothing up. The acts are the user's in the portal, as the data scientist; every AWS call of
Claude's is a read, as `InfrastructureAccess` in Sandbox and in Data Governance. The user, verbatim:

```text
Fiz o pass 2.
Utilizei o `test-experimentation` como projeto consumidor.

Alguns comentários:

* para criar o produto de dados, o menu foi Manage -> Assets -> Create -> Create Data Product.
* Para o passo da assinatura, foi na mesma página de Assets (esta é a página de busca do catálogo, pelo que consegui entender). Clicando nos "..." do "trades_notional" -> share. Este botão navegou para o diálogo de "Create subscription for trades_notional", onde selecionei o projeto consumidor.
* No `test-experimentation`, a tabela apareceu na base glue do projeto, e consegui executar consulta pelo select: `SELECT * FROM "glue_db_4zojr4rr6bmnww"."trades_notional" LIMIT 10;`.
```

- **[user] The consumer is `test-experimentation`**, decision 5's amendment; no project was
  created and no environment.
- **[user] The acts as the domain account's trail holds them**, each by the domain's execution
  role in the data scientist's session (read to 03:46:14 UTC): `CreateProjectMembership` at
  03:35:22, the Governance Manager's SSO profile a `PROJECT_CONTRIBUTOR` of
  `eighth-experimentation`; `CreateDataProduct` at 03:38:11; `CreateListingChangeSet`, `PUBLISH`,
  on it at 03:38:28; `CreateSubscriptionRequest` at 03:40:28, the listing `dpx3r3w5msguc0` for the
  project `test-experimentation`. No `AcceptSubscriptionRequest`.
- **[Claude] The data product**, 03:47 UTC: `trades-notional`, `bvs7m8z4h6w70w`, revision 1, one
  item, the asset `trades_notional`, no description; its listing a `productListing` at revision 1
  carrying the asset's listing `ct5d0innrgw3v4` at revision 6.
- **[Claude] The access act is the owner's *Share***, by the user's account of the portal and by
  its record: the request `arjy3a2439emts` reads `ACCEPTED`, created and updated at 03:40:28.050,
  by the data scientist, with no reviewer and an empty reason; the subscription `d21t6zwyzrcas0`
  reads `APPROVED` with that request's id. `list-subscription-requests` by approver project, no
  status given, listed nothing. The first direct Share in this estate, on a Sandbox project's
  product and no lake listing (6f decision 5 bounds the lake's). The Governance Manager approved
  nothing, and a consumer's own request was not made (`SUP-360`).
- **[Claude] The fulfilment, in Sandbox's trail** (verification vi): 03:41:13,
  `BatchGrantPermissions` by `eighth-experimentation`'s project role, session
  `AWSDataZone-Subscriptions`, `SELECT` on `app_etl.trades_notional` to the account's
  `IAMPrincipals` under `context.datazone.projectId=="4gqfau9xuo6e4w"`, no grant option; 03:41:23,
  `glue:CreateTable` by `test-experimentation`'s project role, the same session name, the link
  `trades_notional` in `glue_db_4zojr4rr6bmnww` to `app_etl.trades_notional`; 03:41:24,
  `BatchGrantPermissions` by that role, `DESCRIBE` on the link to `IAMPrincipals` and to
  `arn:aws:identitystore:::user/*` under the same condition. No failure in either batch. No
  RAM write and no `glue:PutResourcePolicy` in those minutes. The subscription's grant
  `cm2l6qv25dsy6o`, target `test-experimentation-lakehouse-default-target`, reads `COMPLETED`
  at 03:41:33, the asset `GRANTED`: 65 s after the request (`SUP-195`).
- **[Claude] `list-permissions` after it**, 03:48 UTC: on the table, the conditioned `SELECT` of
  `IAMPrincipals` beside the owner role's creator grants; on the link, the conditioned `DESCRIBE`
  of `IAMPrincipals` and the consumer role's `ALL`, `DESCRIBE`, `DROP`; the `identitystore` grant
  is not listed, as `catalog.py` says of such grants. `glue get-table` on the link answers the
  target's creation time and creator.
- **[user] The read** (viii's first half): the query above, `c2b1fcc5-…`, in the workgroup
  `workgroup-4gqfau9xuo6e4w-bi356s1sacz0cw`, as `test-experimentation`'s project role in the
  user's session: `SUCCEEDED`, 03:42:13.070 to 03:42:14.960 UTC, 623 bytes scanned, Athena
  engine version 3; one `GetDataAccess`, `SELECT` on the link, at 03:42:14.
- **[Claude] vii** is read for a product of one item: the one request fulfilled the one asset.
- **[Claude] `./aws/catalog.py`**, 03:49:31 to 03:51:16 UTC: *"all checks passed"*, 11 rows
  `pass` and four notes, `CT-3`, `CT-6` (`EXC-11`), `CT-7` and `CT-13`'s measured negative; `CT-11`
  reads the lake's listing alone. Its
  section on what it cannot see said a direct Share had never run here: rewritten to this
  measurement.
- **[Claude] 6f's questions this touches**: verification ii, a direct Share's grant and approver,
  is read on this product and noted in that stage's row; 4.3's membership half is done, its
  approval as the Governance Manager not exercised.
- **[Claude] Written**: pass 2's steps, verifications vi to viii, decision 5's amendment and the
  status row; the waiting list (the consumer's row and the portal acts' row out, the window in
  the Sandbox sitting's row); `SUP-360`, a reading on `SUP-195`; `GOVERNANCE.md`'s Share row;
  `AWS_STATE.md`'s paragraph on project-owned objects; `aws/catalog.py`'s text; `CLAUDE.md`'s row.
- **[Claude] Owed**: the window, a space in `test-experimentation` (viii's Spark half, decision
  17's reads, xi), the revoke (ix) and the consumer's inventory the morning after (x); the
  portal's look at the lineage on the asset's page (v).

## 2026-11-14 — verification v's portal half: the lineage the asset's page draws

Nothing up, no AWS call of Claude's but one read of the domain's portal address. The user,
verbatim: *"Abri uma sessão no chrome do claude, e está aberto na página do lineage do
trades_notional."* Claude read the page through the Claude in Chrome extension, in a tab of its own
in the user's browser, the user's tab being outside the session's group; the portal answered
signed in as the Data Scientist User. Navigation and reading alone, no write in the portal; the
tab was closed after.

- **[Claude] The path**, 04:07 to 04:08 UTC: `eighth-experimentation`, *Manage → Assets*, the asset
  `trades_notional`, the tab *Lineage*. *Manage*'s *Catalog management* group lists *Assets*,
  *Subscription requests*, *Data sources*, *Metadata forms*, *Business glossaries* and *Custom
  asset types*, as far as the window showed; the asset's page is `/projects/<project>/catalog/assets/asset/<asset id>`, its
  tabs *Overview*, *Schema*, *Asset filter*, *Preview data*, *Lineage*, *Data profile*, *Data
  quality* and *Subscriptions*, the asset marked *Published*.
- **[Claude] What the tab draws**, *Graph depth* 5, left to right, the times as the portal shows
  them, UTC-03:00:
  - a node *Table / Amazon S3*, named by the domain's and the project's ids, 5 columns, *November
    10, 2026, 00:44*;
  - two nodes *Job Run / Apache Spark*, `app_etl_avhvbqn37ty7m8.atomic_re…` and
    `app_etl_avhvbqn37ty7m8.overwrite…`, each *Status: COMPLETE*, *November 10, 2026, 00:44*;
  - a node *Table / AWS Glue*, 6 columns, *November 10, 2026, 00:44*;
  - an edge *Cataloged* to `trades_notional`, *Asset / Inventory*, labelled *Base*, 6 columns,
    *November 10, 2026, 00:56*;
  - an edge *Published* to `trades_notional`, *Asset / Published*, 6 columns, *November 14,
    2026, 00:41*;
  - an edge *Access Requested* to `test-experimentation-lakehouse-def…`, *Subscription target /
    AWS Glue*, *Grant status: Granted*, 6 columns.
- **[Claude] Read against the domain's half** (2026-11-10): the portal draws the chain the domain
  held, the `inbox` prefix, the job's runs, the table, the asset and its listing, where Stage 18
  7.1 drew nothing. The last edge and the published node's time are pass 2's: the domain
  account's trail holds four lineage-node writes at 03:41:39 UTC, six seconds after the
  subscription's grant completed.
- **[Claude] Written**: verification v's row; item 20, which waited on this look; the row out of
  the waiting list.

## 2026-11-14 — `SUP-360` taken twice on `main`: the Share's entry is `SUP-362`

No AWS call. Claude's hand, on a peer session's information: the session *"Releitura quinzenal de
upstream-releases.md"* wrote at 04:41 UTC that `main` failed `./scripts/check-aws-supplement.py`.

- **[user] PR #298 merged**, 04:39:14 UTC, squashed into `850c5a37`. PR #294, the peer's, had
  merged at 04:12 UTC as `aa72e16b`. This entry is on `claude/stage-19-ahead`, cut from
  `850c5a37` in the same worktree.
- **[Claude] The failure, read on `850c5a37`** at 04:44 UTC: exit 1, *"FAIL  line 2716: SUP-360
  already names the entry at line 2064"*. PR #294 wrote `SUP-360`, a DataZone domain's RAM share
  and its managed permission's version, and `SUP-361`; this stage's branch wrote `SUP-360` for the
  portal's *Share* in `9eb8d166`, reading `SUP-359` as the highest id, and its last push,
  `e7aee8fe`, preceded PR #294's merge, so each branch's check passed. No text conflicted, the entries sitting in
  different sections, and the merge went in.
- **[Claude] The second entry renumbered `SUP-362`**, `main`'s highest being `SUP-361` and no
  other branch on origin holding the supplement: the entry, `GOVERNANCE.md`'s Share row, 6f's
  verification ii and step 2.3's note here. In this log the two entries above on pass 2 keep
  `SUP-360` as written; the entry they mean is `SUP-362`. Every other use of `SUP-360` in the tree
  is PR #294's.
- **[Claude] Written**: a rule beside the module tags' in `CLAUDE.md`: an id is read from
  `origin/main` at the commit and at every sync, and the check run on the synced tree.

## 2026-11-14 — step 6.1: `catalog.py`'s product road written and run with nothing up

Read-only, as the infrastructure user through `awsds-infra-data`, `awsds-infra-sandbox-1`,
`awsds-infra-staging` and `awsds-infra-prod`; no apply, no AWS write, no portal act. Claude's hand,
on the user's *"Sim, escrever"* to *"Escrevo agora os checks da estrada do produto no
catalog.py?"*.

- **[Claude] Read before the code**, each a shape the checks depend on, before the first run at
  05:17 UTC:
  - `list-subscriptions` and `list-subscription-requests --status ACCEPTED` return
    `trades-notional`'s subscription `d21t6zwyzrcas0` and its request `arjy3a2439emts` under the
    data product listing `dpx3r3w5msguc0` and under its asset listing `ct5d0innrgw3v4` alike;
    `list-subscription-grants` returns the grant `cm2l6qv25dsy6o` under the asset listing alone
    (`SUP-363`).
  - `list-subscriptions --owning-project-id` selects by subscriber and answers Data Governance's
    session, a member of none of the four projects asked: `test-experimentation` 1,
    `eighth-experimentation` 2 (`trades` of `governed-lake` and a Bedrock model's listing),
    `deploy-staging` 0, `deploy-production` 0.
  - Lake Formation's `list-permissions` answers whole in both targets: Staging 36 rows in 5
    pages, Production 39 in 5. Each target's `app_etl` carries the blueprint's grants under its
    deployment project's context and no table by name; `raw` and `curated` there are resource
    links (`glue get-database`, `TargetDatabase`), with no SMUS principal on either.
  - Sandbox's rows on `app_etl.trades_notional`: the owner role's creator grants and the
    fulfilment's `SELECT` to the account's `IAMPrincipals` under `test-experimentation`'s context;
    on `app_etl.ALL_TABLES`, the blueprint's to `IAMPrincipals` under `eighth-experimentation`'s
    context and to `awsds-sandbox-smus-manage-access`.
  - `glue get-table` shows a resource link by `TargetTable`: absent on `app_etl.trades_notional`
    and `mydatabase.house-price`, present on `glue_db_4zojr4rr6bmnww.trades_notional`.
  - `datazone search --search-scope ASSET --owning-project-identifier` answers the session of the
    account each project's environments live in, for the seven projects: 10 assets, 4 of them
    Glue tables, with `test-experimentation`, `app-etl-dev` and both deployment projects holding
    none.
  - A role session's user profile carries the role's ARN, equal to its session group's
    `rolePrincipalArn`, and that group's id (`deploy-production`'s creator, read by its profile).
  - The listing `house-price` carries no `classification` form; `trades_notional` reads
    `internal`.
- **[Claude] Written in `aws/catalog.py`**: `CT-15` to `CT-19`, section 7 of the report, the
  grants read in both targets beside the registry's and Sandbox's (which widens `CT-7` and `CT-8`
  to the targets, the catalog road they admit staying the registry's and Sandbox's), and
  `--self-check`, 34 cases on sample records. A refused `GetListing` counts as unread on both roads; before, the lake road passed
  over it as no lake listing.
- **[Claude] Run** 05:23:54 to 05:26:36 UTC, exit 0, *"all checks passed"*: 13 `pass`, 7 `note`,
  no failed call. 189 grants read, 85 SMUS-managed: registry 45, consumer 69, staging 36,
  production 39, each to its last page.
  - `CT-15` pass: 11 listings, none of `deploy-staging`, `deploy-production` or `app-etl-dev`.
  - `CT-16` note: `test-experimentation` reads `app_etl.trades_notional` by the owner's Share
    (`d21t6zwyzrcas0`); no deployment project subscribes.
  - `CT-17` pass: 13 grants on `app_etl.trades_notional` and `mydatabase.house-price`, 1
    fulfilment and 12 the owning project's or the blueprint's.
  - `CT-18` note: `house-price` with no form, by `EXC-24`; `trades_notional` `internal`.
  - `CT-19` note: `trades` in `eighth-experimentation`'s inventory, `glue_db_blerpkhn9nj7o0.trades`,
    a link to the registry's `curated.trades`, unlisted: 0.5's shape, read by an instrument.
  - `CT-8` pass on 40 `IAMPrincipals` grants; `CT-7` a note as before, 4 grants on the catalog
    road.
- **[Claude] The rules read failing**, in three runs of `main()` with a constant replaced, each
  writing a report of its own, deleted after:
  - No exception for `house-price`, `eighth-experimentation` as a chain's `dev` project, a
    fulfilment admitted `DESCRIBE` alone, every Glue table a link: `CT-17`, `CT-18` and `CT-19`
    failed, each on the expected object; `CT-10` failed on the lake's fulfilment; `CT-15` read a
    note naming the project's four listings.
  - `eighth-experimentation` as Staging's project and `test-experimentation` as Production's:
    `CT-15` failed on the four listings, `CT-16` on three subscriptions a deployment project
    holds and on the Share, `CT-14` on both projects' sources.
  - The Sandbox profile unsigned: `CT-17` and `CT-19` read notes naming what was not read, and
    none of `CT-15` to `CT-19` failed. `CT-10` failed there, on the lake's fulfilment with the
    consumer account unknown: a reading of that degraded run, the check left as it is.

  `--self-check` with a fulfilment admitted `INSERT` read 33 of 34 cases and exit 2.
- **[Claude] Written**: `EXC-24` in `AWS_STATE.md`; `SUP-363`; `aws/INDEX.md`; `POLICIES.md`'s row
  on the subscription deny; the stage file's 6.1, 2.6 and item 24; the owner's act on
  `house-price` in the waiting list; `--self-check` in `make check` and in pre-commit.

## 2026-11-14 — `EXC-24` kept by the user: `house-price` stays a note in `CT-18`

No AWS call. The user's decision, recorded by Claude's hand.

- **[user] *"Manter como nota"***, to *"Mantenho o house-price sem classificação como nota
  (EXC-24)?"*, the other answer offered being to let `CT-18` fail on the listing.
- **[Claude] Written**: the decision in `EXC-24`'s row, in step 6.1's note and in the waiting
  list. `UNCLASSIFIED_BY_EXCEPTION` keeps the asset's row; the owner's act that closes the
  exception stays the user's, on no date, and nothing waits on it.

## 2026-11-14 — PR #299 merged; this log reviewed against the session's transcript

No AWS call answered. Claude's hand, on the user's word: *"Fiz todos os merges. Antes de fecharmos
esta thread, confira se o log está devidamente atualizado com o andamento desta thread."*

- **[user] PR #299 merged**, 17:22:15 UTC, squashed into `c6065e4b`; the tree is the branch's. This
  entry is on `claude/stage-19-log-review`, cut from that commit in the same worktree.
- **[Claude] The review**, this log against the session's transcript, from its first message on
  2026-11-11 at 04:15 UTC to this one:
  - Every `terraform apply` the session ran is in an entry with its result, from
    `identity/org-policies` on 2026-11-11 at 14:23 UTC to `sandbox/workflows/` on 2026-11-14 at
    02:42, the `data-governance/governance` apply that ended in the provider's error at 15:21 UTC
    on 2026-11-11 among them. So are the four the app's classifier refused, all on 2026-11-11:
    the SCP's at 04:35 UTC and `staging/studio`'s after it, under the opening message's blanket
    authorization; `staging/studio`'s at 14:31, past the three applies named; and the one asked by
    a question, after 16:08.
  - Every AWS write outside Terraform is in an entry: the candidate SCP's life on `Policy Test`
    and the RAM association (2026-11-11, 04:31 to 04:37 UTC), both `create-project` and both
    `create-environment` calls (15:25 to 15:31), and the two refused the same day,
    `put-data-lake-settings` and `create-project-membership`. So are both module tags,
    `sagemaker-prereqs-v0.10.0` and `orchestration-v0.3.0`.
  - Every message of the user's that carried an authorization, a decision or an act is quoted.
    The ones not quoted are two questions on what could be advanced with nothing up, each
    answered in chat and followed by a quoted choice, and the note of #292's merge, which an
    entry records with its time.
  - Every pull request of the session carries its merge's time and commit: #288, #289, #291, #292
    and #295 to #298. #299's is this entry's.
  - Of the session's subagents, the one that edited files is named in its entry, release T's;
    the other three read the repository alone.
  - The session ran no `make up`, `make hub-up` or `make gitlab-up`.
- **[Claude] Found, and written**:
  - The stage file's `Status` row left 2.6's reading out of what pass 2 owes: verification x, one
    run of `./aws/catalog.py` after the consumer's source runs at 02:51 UTC on 2026-11-15, with
    nothing up, while the subscription stands.
  - `CLAUDE.md`'s row for this stage carried neither 6.1's product road nor that reading.
- **[Claude] Not read**: what is up. `make status` at 17:30 UTC read nothing, the SSO token having
  expired (*"Token has expired and refresh failed"*): 16 slices `UNREADABLE`, its USD 0.0000/h a
  floor and no measurement. The reading waits for the user's sign-in as the infrastructure user.

## 2026-11-14 — what is up, read at the session's close: nothing billing by the hour

Read-only, as the infrastructure user, signed in by the user: *"usuario sso infra logado. pode
prosseguir com as leituras."* Claude's hand.

- **[Claude] The identity**, 17:34 UTC: `InfrastructureAccess` on `awsds-infra-data`,
  `awsds-infra-sandbox-1`, `awsds-infra-staging` and `awsds-infra-prod`.
- **[Claude] `make status`**, 17:35:23 to 17:37:36 UTC, exit 0, no slice unreadable: the burn
  0.0000 USD/h. Stopped, one instance each: `production/vpn`, `production/proxy` and
  `production/tooling`. Down, with no resource: Production's `egress`, `workloads-egress`,
  `warehouse-compute`, `runners` and `probes`; Sandbox's `egress`, `warehouse-compute` and
  `probes`; Staging's `egress`, `app/app-etl` and `orchestration`. Production's `app/app-etl` (3)
  and `orchestration` (41) are up at no hourly rate, as on 2026-11-10.
- **[Claude] The schedules**, 17:38 UTC: Production's three in `awsds-prod-chains`,
  `awsds-prod-chain-app-etl`, `awsds-prod-chain-app-etl-train` and
  `awsds-prod-chain-app-etl-warehouse`, each `DISABLED`; Staging lists none.
- **[Claude] 2.6 is not due**: the consumer's source over `glue_db_4zojr4rr6bmnww`,
  `3zp6fog9jep1qo`, last ran on 2026-11-14 at 02:51:09 UTC, `SUCCESS`, 50 minutes before the link
  was created, and runs next at 02:51 UTC on 2026-11-15. `test-experimentation`'s inventory holds
  no asset, and its subscription `d21t6zwyzrcas0` reads `APPROVED`.
- **[Claude] Written**: `CLAUDE.md`'s sentence on the last reading of what is up.

## 2026-11-14 — the next sittings prepared with nothing up: the Sandbox sitting in order, release T's step 13 after it

Read-only, as the infrastructure user through `awsds-infra-sandbox-1` and `awsds-infra-data`; no apply,
no AWS write, no portal act. Claude's hand, on the user's message, verbatim: *"Prepare o que for
necessário para avançarmos na conclusão do estágio 19."*

- **[user] PR #300 merged**, 17:40:12 UTC, squashed into `234e0bde`. This entry is on
  `claude/preparacao-estagio-19-990c77`, cut from that commit in a worktree of its own.
- **[Claude] `eighth-experimentation`'s objects for item 20**, read from 17:45 UTC:
  - Six environments, among them `chz5jdb80ohocw`, `create-datalake-database-env-app_etl-…`, `ACTIVE`
    since 2026-11-08 23:41 UTC. Its stack `DataZone-Env-chz5jdb80ohocw` holds one resource, the
    `GlueDatabase` `app_etl`, and its template gives that resource and an Athena workgroup
    `DeletionPolicy` and `UpdateReplacePolicy` `Retain` (`SUP-184`).
  - The source `budryu9mt9y5u8` over `app_etl` (filter `app_etl`, `*`; `publishOnImport` false), daily at
    `cron(41 23 * * ? *)`, `ENABLED`, its last run `SUCCESS` at 23:47 UTC on 2026-11-13. It names no
    environment: its connection is `5pf7uc0ugllsb4`, `project.default_lakehouse`, the `Tooling`
    environment's.
  - The data products `my-data-product` and `trades-notional`; the assets `house-price`, `trades` and
    `trades_notional` (`4j6p77v7dm2840`).
  - The database `app_etl`, *"Created by DataZone for project eighth-experimentation"*, and its one table,
    `trades_notional`, Iceberg at version 3, created by the project role's `GlueJobRunnerSession`. Lake
    Formation on the database: the project's conditioned `IAMPrincipals` `CREATE_TABLE`, `DESCRIBE` and
    `DROP`, the provisioning role `ALL`, the manage-access role `CREATE_TABLE` and `DESCRIBE`; on the
    table, the subscription's conditioned `SELECT` and the project role's `ALL` and `SELECT`. Sandbox's
    Lake Formation administrators are the manage-access role, the provisioning role and
    `InfrastructureAccess`; the registered locations are the three projects' `dev` prefixes,
    `app-etl-dev`'s among them.
  - The application the space deployed on 2026-10-26 and again on 2026-11-10: the workflows
    `app_etl_eighth_experimentation_app_etl` and `app_etl_eighth_experimentation_app_etl_train`, the Glue
    job `app-etl-avhvbqn37ty7m8`, and 30 objects under `shared/app-etl/`, ten of them AppleDouble.
- **[Claude] Pass 2's window values read again**: the table's metadata `00003-a0aed729-…`; the run
  `6bnfg5dk961bps` `SUCCESS`, `updated: 1`, created 2026-11-10 03:55 UTC; the subscription
  `d21t6zwyzrcas0` `APPROVED`; its grant `cm2l6qv25dsy6o` `COMPLETED`, the asset `GRANTED`.
- **[Claude] `app-etl-dev`**: one environment, `Tooling`; nine connections, the manifest's
  `default.s3_shared` and `default.workflow_serverless` among them; one source, the `Tooling`
  model-package source, daily at 02:07 UTC.
- **[Claude] Item 33's attach checked**: `d-spi9kgo6x5b4`'s `DefaultUserSettings` holds the fields
  `dev-env.md` §C6 sends back and no `CustomImages`; `sandbox/dev-env/` initialised in this worktree
  (`gen-backend-hcl.py`, `gen-tfvars.py`, `init`), its `custom_images` output naming the two app image
  configurations the other two domains carry; no space in any of the three domains; the image at
  version 11, alias `0.10.0`.
- **[Claude] Item 22 read in the CLI 1.0.9's code**, no call: the export keeps a form type whose
  `owningProjectId` is the `dev` project, and the import resolves an asset's form by name with
  `get_form_type`. `classification` is `eighth-experimentation`'s, revision 2, `ENABLED`, so it travels on
  the asset's forms and never in `formTypes`. Once 1.5 creates the data product, the export carries it
  and the guard fails until `product.json` names it.
- **[Claude] Found**: release T's step 13 deploys into `app-etl-dev` from a space, and the run's Glue job
  writes `app_etl.trades_notional`, a database `eighth-experimentation` holds until item 20, so the step
  waits for the Sandbox sitting's database. The source `budryu9mt9y5u8` names `app_etl` and hangs from no
  environment, so the retirement deletes it by itself, before the asset.
- **[Claude] Release T's gates previewed** on `36bcf916`'s tree, extracted in the session's scratch
  folder: `uv sync --locked`; `ruff check` and `ruff format --check` clean; `pytest` 72 passed, 1 skipped;
  the lint at `d856982c` with the job's options *"ok: 9 arquivo(s)"*; `pip-audit` 2.10.1 (OSV) over the
  runtime set, `pyarrow` 25.0.1 alone, *"No known vulnerabilities found"* at 17:58 UTC. A preview: the
  gate's reading is the tag day's (Lesson 77).
- **[Claude] The tar of release T's tree**, built in the scratch folder from `git archive 36bcf916` with
  `COPYFILE_DISABLE=1` and `--no-xattrs --no-acls --no-mac-metadata`: 35 members, 25 files, no `._`
  name. A plain `tar -c` of the same folder wrote 70 members, 35 of them `._`.
- **[Claude] `SUP-364`**: `glue get-tables` at 17:50 UTC and `glue get-table-versions` at 18:07 answered
  `IsRegisteredWithLakeFormation` false for `app_etl.trades_notional` at version 3, and `glue get-table`
  true at 18:07, as pass 1's did on 2026-11-10. The Glue API reference's pages for `Table`, `GetTable`,
  `GetTables` and `GetTableVersions`, read by a subagent the same day, say nothing of which call fills
  the field.
- **[Claude] Written**: the stage file's §The Sandbox sitting, in order (steps 1 to 18), the sittings
  list, items 20, 22 and 33, 1.5's note, pass 2's step 6 and the status row; `promotion.md` §N.8.2 step 3
  (the local user's password before the first push) and step 13, and §N.8.4's `product.json` paragraph;
  the waiting list's rows on the password, the attach, the AppleDouble objects, the Sandbox sitting and
  release T; `SUP-184`'s reading and `SUP-364`; the four Glue pages in `docs/REFERENCES.md`;
  `docs/SMUS.md`'s *Create database* item; `CLAUDE.md`'s row.
- **[Claude] The branch's first push refused**, 18:15 UTC, by the app's auto-mode classifier as
  *Unsanctioned Communication*, after the commit `8bfc245d`; the push and the PR wait on the user's
  word in this chat. `CLAUDE.md`'s table of refusals gains the row.
- **[Claude] The push and the PR**, on the user's word in this chat, *"Autorizo push e PR"*: the branch
  pushed at 19:47:31 UTC, PR #301 opened at 19:47:55 UTC.

## 2026-11-14 — item 33: the house image attached to `app-etl-dev`'s domain

One AWS write, on the user's word in this chat: *"Autorizo o attach"*. Claude's hand, as the
infrastructure user through `awsds-infra-sandbox-1` (`InfrastructureAccess`, read at 20:04 UTC).

- **[Claude] The domain read**, 20:04 UTC: `d-spi9kgo6x5b4` is
  `SageMakerUnifiedStudio-ceweti7jbiu1hs-…-dev`, `app-etl-dev`'s, `InService` with no `FailureReason`.
- **[Claude] The peer told** before the write: the one other session on the laptop, *Worktrees para
  apagar*, idle.
- **[Claude] `dev-env.md` §C6's two commands**, their three files in the session's scratch folder rather
  than `$HOME/tmp`: the live `DefaultUserSettings`, ten keys and no `CustomImages`; `sandbox/dev-env/`'s
  `custom_images` output, `awsds-sandbox-dev-env-jupyterlab` and `awsds-sandbox-dev-env-codeeditor` on
  `awsds-sandbox-dev-env` with no version number; the edited block, whose diff against the live one
  carried the two entries alone.
- **[Claude] `update-domain`**, 20:05:22 UTC, exit 0, the domain's ARN answered.
- **[Claude] Read back**, 20:05:36 UTC: `InService`, no `FailureReason`, `LastModifiedTime` 20:05:24 UTC;
  the whole block's diff against the one read before carries the two `CustomImages` entries alone, and
  the block equals the one sent once keys are sorted; no space in the domain.
- **[Claude] Written**: item 33's row, §The Sandbox sitting's step 2 and the status row; the waiting
  list's row removed and the Sandbox row's first column; `promotion.md` §N.8.2 step 13's space;
  `dev-env.md` §C6's measured writes; `CLAUDE.md`'s row.
- **Not read**: the portal's picker (`dev-env.md` §C7), which the Sandbox sitting's space reads at its
  step 13.

## 2026-11-14 — PR #301 merged; release T's tar built for the Sandbox sitting

No AWS write. Claude's hand, in a session started from another session to run §The Sandbox sitting, in
order; the infrastructure user's identity read on `awsds-infra-sandbox-1` and `awsds-infra-data`
(`InfrastructureAccess`) at 20:19 UTC.

- **[user] PR #301 merged**, 20:10:12 UTC, squashed into `018fa717`. This entry is on
  `claude/amazing-gates-020988`, cut from that commit in a worktree of its own.
- **[Claude] Step 3, the tar**, 20:20 UTC, by the step's three commands:
  `$HOME/tmp/stage19-1.5/app-etl.tar` from `git archive 36bcf916`, 201,216 bytes, 35 members, 25 files
  and no `._` member, as measured on the same tree earlier that day. It is deleted after the sitting.
- **[Claude] Step 1 not due**: the consumer's source over `glue_db_4zojr4rr6bmnww` runs next at 02:51 UTC
  on 2026-11-15, and step 5's revoke waits for the reading.

## 2026-11-14 — step 18: `eighth-experimentation`'s application deleted, ahead of the Sandbox sitting

Three kinds of AWS write in Sandbox, on the user's word in this chat, *"Autorizo os deletes"*, given to the
question whether to delete step 18's objects in `eighth-experimentation`. Claude's hand, as the
infrastructure user through `awsds-infra-sandbox-1` (`InfrastructureAccess`, read at 20:50:27 UTC). The
step says nothing in steps 5 to 17 reads these objects, so it ran before the sitting rather than after it.

- **[Claude] Read before the deletes**:
  - the workflow `app_etl_eighth_experimentation_app_etl`, `READY`, `manual_only`, no schedule, five runs:
    `SUCCESS` on 2026-10-26, and pass 1's four on 2026-11-10, three `FAILED` and one `SUCCESS`;
    `app_etl_eighth_experimentation_app_etl_train`, `READY`, `manual_only`, no run;
  - the Glue job `app-etl-avhvbqn37ty7m8`, Glue 6.0 on two G.1X workers as the project role, five runs
    `SUCCEEDED` (2026-10-26 and 2026-11-10), no trigger;
  - 30 objects under `shared/app-etl/`, 50,942 bytes, ten of them AppleDouble (`._*`, 163 bytes each). One
    of the rest is `tables/trades_notional/part-00000-…-c000.snappy.parquet`, the job's `--TABLE_PATH`
    output; the product table's own files are its Glue location's, 4 data and 12 metadata objects under
    `dev/data/catalogs/trades_notional/`;
  - the bucket versioned, its lifecycle expiring noncurrent versions after 90 days, its policy one deny on
    insecure transport. No instrument under `aws/` or `scripts/` names these objects.
- **[Claude] The peer told** before the writes: *Worktrees para apagar*, idle, the one other session on
  the laptop.
- **[Claude] The deletes**, each exit 0: `mwaa-serverless delete-workflow` on both workflows at 20:50:40
  and 20:50:41 UTC; `glue delete-job` at 20:50:51; `aws s3 rm --recursive` on the prefix from 20:51:03 to
  20:51:05, 30 `delete:` lines.
- **[Claude] Read back**, 20:51:18 UTC: no workflow named `app_etl_eighth_experimentation_*`; `GetJob`
  answers *"Job not found"* (`EntityNotFoundException`); no current object under the prefix, the 30 kept
  as noncurrent versions until the lifecycle expires them. The workflows' log groups stay under `EXC-10`'s
  rule: `…/app_etl_eighth_experimentation_app_etl` at 80,569 bytes and `…_train` empty, neither with a
  retention. The product table's metadata is still `00003-a0aed729-…`, and the subscription's grant
  `cm2l6qv25dsy6o` reads `COMPLETED`, its asset `GRANTED`.
- **[Claude] Written**: step 18's note and the status row; the waiting list's row on the AppleDouble
  objects removed; `CLAUDE.md`'s row.

## 2026-11-14 — `EXC-24` closed by the owner's act; decision 17 (d)'s report deferred

Every AWS call of Claude's a read, as the infrastructure user through `awsds-infra-sandbox-1` and
`awsds-infra-data`; the act on `house-price` is the user's, in the portal as the data scientist. Claude's
hand. The user, verbatim: *"Sobre estes pontos, me oriente como fazer agora."*, on (d)'s report and
`EXC-24`; then *"Classifiquei o house-price como public e republiquei"* and *"sobre o relato à AWS, não
vou fazer neste momento. Guarde nas pendências do projeto."*

- **[Claude] The push and the PR**, on the user's word in this chat, *"Autorizo push e PR"*: the branch
  pushed at 20:55:51 UTC, PR #302 opened as a draft at 20:56:40 UTC, `make check` OK before it.
- **[Claude] (d)'s channel**: `aws support describe-severity-levels` in `us-east-1` answered
  `SubscriptionRequiredException` (*"Amazon Web Services Premium Support Subscription is required to use
  this service."*) on both profiles, so no technical case. AWS's vulnerability reporting page, read
  through a fetching agent: its Vulnerability Disclosure Program on HackerOne, or
  AWS Security's e-mail address, which the page names; a human acknowledgement within 24 hours; no support plan named; nothing
  disclosed publicly before a fix. The draft of 2026-11-11 went to the user with two lines added:

  ```text
  - Accounts: the domain's <domain account id>; the caller's <caller account id>, an associated account.
  - Impact: the caller cannot read project B's data or change its source, but it can start that
    source's import, with the source's own configuration, whenever it wants.
  ```

- **[user] The report deferred**, kept in the waiting list.
- **[Claude] `house-price` before the act**: the asset `dbund4fvvvt05s` at revision 1, its forms
  `GlueTableForm`, `DataSourceReferenceForm`, `SubscriptionTermsForm` and `CommonDetails`, no
  `classification`; its listing `cetyru4cvy1bio` `ACTIVE` at revision 2.
- **[user] The act**: the form `classification` added with `public`, and the asset republished.
- **[Claude] Read after it**, from 21:27 UTC:
  - asset revisions 2 to 4 by the owner's profile `28f1b390-…`: revision 2 at 21:25:20 UTC with
    `classification` `internal`, revision 3 at 21:25:41 with `public`, revision 4 at 21:26:09 with
    `public` and `SubscriptionTermsForm` `approvalRequired` `NO`, where revisions 1 to 3 read `YES`;
  - the listing at revision 4, `ACTIVE`, 21:26:11.734 UTC, carrying asset revision 4, `classification`
    `public` and `approvalRequired` `NO`; revision 3, 21:26:11.068, carrying asset revision 1, the
    change set's revision before the publication's, as `SUP-345` read;
  - Data Governance's trail at 21:28 UTC: `CreateAssetRevision` at 21:26:09 and `CreateListingChangeSet`
    `PUBLISH` on entity revision 4 at 21:26:11, each by the domain execution role in the portal;
    revisions 2 and 3's writes not yet listed (Lesson 62).
- **[Claude] Found**: the republication turned `house-price`'s subscription terms from approval required
  to none, in the revision the portal wrote two seconds before the publication. A request to the
  listing is now accepted at creation, so 6f step 2's approval act has nothing to approve. No check
  fails on it: `CT-11` reads the lake's listing alone, and `house-price` is a project's. Whether the
  publish dialog or the user chose it is the user's account to give.
- **[Claude] `EXC-24` closed in `aws/catalog.py`**: `UNCLASSIFIED_BY_EXCEPTION` emptied;
  `classification_findings` takes the exceptions as an argument, so the `--self-check` case on an
  excepted listing, which took the map's first entry, is built on a sample exception. 34 of 34 cases
  as expected, ruff clean. `./aws/catalog.py` from 21:29:20 to 21:32:00 UTC: all checks passed, `CT-18`
  *"house-price public; trades_notional internal"*; notes `CT-3`, `CT-6`, `CT-7`, `CT-13`, `CT-16`
  and `CT-19`.
- **[Claude] Written**: `EXC-24` closed in `docs/AWS_STATE.md`; `aws/INDEX.md`'s `catalog.py` row;
  step 6.1's note, decision 17's channel and the status row; the waiting list's row on `house-price`
  removed and (d)'s row brought to the reading; the vulnerability reporting page in
  `docs/REFERENCES.md`.

## 2026-11-14 — `house-price`'s listing kept without approval

No AWS call. The user's decision, recorded by Claude's hand.

- **[user] *"Manter sem aprovação"***, to whether `house-price`'s listing should require approval again,
  the other answer offered being to republish it with the approval required. The publish dialog's
  default was not read.
- **[Claude] Written**: 6f steps 2.2 and 4.3's notes, a request to `house-price` being accepted at
  creation whoever makes it; the waiting list's row on 6f step 2's portal acts; 6f's log.

## 2026-11-14 — the Sandbox sitting, steps 1 and 4: 2.6 read on a member's run, the raises

Reads as `awsds-infra-sandbox-1` and `awsds-infra-data`; the user's acts in the portal and from the
project folder.

- **[user] *"Antecipar a 2.6"***, to whether step 1 waits for the consumer source's scheduled run at
  02:51 UTC on 2026-11-15 or reads a run started by hand, so the window runs today.
- **[Claude] The baseline**, 21:57:42 UTC: the source `3zp6fog9jep1qo`'s last run `3vvwx8yf4ntuds`,
  `SCHEDULED`, `SUCCESS` at 02:51:09; `test-experimentation`'s inventory held 0 assets; the link
  `glue_db_4zojr4rr6bmnww.trades_notional` targeted `app_etl.trades_notional`; the subscription
  `d21t6zwyzrcas0` read `APPROVED`. The session *Worktrees para apagar* was told of the raises the same
  minute.
- **[user] The source run by hand** as the data scientist, in `test-experimentation`'s data sources:
  *"Rodei a fonte"*.
- **[Claude] The run**, read 22:06 UTC: `6gti1ji6rmgiog`, type `PRIORITIZED`, `SUCCESS`, created
  22:01:21.050, started 22:01:22.672, stopped 22:01:25.010; statistics `added` 1, `updated` 0,
  `unchanged` 0, `failed` 0; one activity, `trades_notional` `SUCCEEDED_CREATED`, asset
  `b5r73n41qe7jf4`. The inventory: `b5r73n41qe7jf4` `trades_notional`,
  `amazon.datazone.GlueTableAssetType`, created 22:01:24.615 UTC, unlisted. The link's `TargetTable`
  unchanged, `app_etl.trades_notional` in Sandbox.
- **[Claude] The trail**: Sandbox's holds no `StartDataSourceRun` since 21:55 UTC. Data Governance's
  holds one at 22:01:21, `AssumedRole` `awsds-data-studio-domain-execution`, session
  `user-28f1b390-0041-7068-8cc7-9ccef94277d1`, the portal user who requested `d21t6zwyzrcas0`, no
  error, on `3zp6fog9jep1qo`.
- **[Claude] `./aws/catalog.py`**, ending 22:09 UTC: all checks passed. `CT-19` notes two unlisted
  links, `trades_notional` in `test-experimentation` (`glue_db_4zojr4rr6bmnww.trades_notional ->
  consumer:app_etl.trades_notional`) and `trades` in `eighth-experimentation` (`->
  registry:curated.trades`). `CT-13` lists the start at 22:01:21 by
  `awsds-data-studio-domain-execution`, verdict `other`. The consumer's source: 1 asset, 27 runs,
  `SUCCESS`.
- **[Claude] Verification x read**: the consumer's source imports the resource link its subscription
  created, as an unlisted inventory asset, 0.5's shape. `CT-19` reads it as a note; no other
  instrument was read for a notice. The run was a member's start, not the schedule's: the scheduled
  run at 02:51 UTC on 2026-11-15 follows step 5's revoke and reads what the source does with an asset
  whose link is gone.
- **[user] The raises** from the project folder, on `main` at `018fa717`, `origin/main`'s: `make
  hub-up`, then `make up ENV=sandbox ONLY=egress GROUPS=mwaa`: *"Subi os dois"*.
- **[Claude] `make status`**, 22:31:42 to 22:34:58 UTC: `production/vpn` and `production/proxy` `UP`,
  one instance each, 0.0052 and 0.0154 USD/h; `sandbox/egress` `UP`, 28 resources, 0.1800 USD/h;
  `production/tooling` stopped; the estimated burn 0.2006 USD/h. A first run at 22:26 UTC was stopped
  at its sixth slice: without `TF_PLUGIN_CACHE_DIR` each slice was downloading its own providers.

## 2026-11-14 — the Sandbox sitting, steps 5 to 12: pass 2's window, the revoke, item 20, `app-etl-dev`'s database

The user's acts in the portal and in the space; Claude's reads as `awsds-infra-sandbox-1` and
`awsds-infra-data`.

- **[user] The space** `jup-std` in `test-experimentation`, JupyterLab on the house image, its app
  `InService` from 22:34:48 UTC on `d-lfgbdrjncmsu`.
- **[user] viii, the Spark read**: `%%pyspark project.spark.fineGrained`, `SELECT count(*) AS n FROM
  glue_db_4zojr4rr6bmnww.trades_notional`, `n` 10; started 22:47:18, 3 min 05.6 s with the session's
  creation. The connection is a Glue interactive session (`SPARK_GLUE`),
  `4gqfau9xuo6e4w-93939e2b-07b3-4c1b-b18a-e875438bd870`: Glue 5.0, 10 `G.1X` workers, an idle timeout of
  60 min, the consumer's project role (`get-session`, 23:05 UTC).
- **[user] Decision 17's reads** from the space's terminal, as
  `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw/SageMaker`: `get-data-source` on `budryu9mt9y5u8`
  answered `…-AwsDataCatalog-app_etl-default-datasource` and the project `avhvbqn37ty7m8`;
  `get-data-source-run` on `6bnfg5dk961bps` `SUCCESS`, `updated` 1; `list-data-source-run-activities`
  `trades_notional` and `4j6p77v7dm2840`. A non-member project's role reads another project's source, its
  run and its activities.
- **[user] xi's negative**: `head-object` on the table's `00003-a0aed729-…metadata.json` refused, `403
  Forbidden`; `list-objects-v2` on the table's folder answered one key,
  `…/trades_notional/data/00000-9-41aaf172-…-00001.parquet`.
- **[Claude] Found**: the listing is granted by the managed `SageMakerStudioProjectUserRolePolicy` v77,
  statement `AirflowListDomainS3Permissions`: `s3:ListBucket` on `${aws:PrincipalTag/DomainBucketName}`
  under the resource account's condition, with no `s3:prefix` condition. The statement beside it,
  `ListDomainS3BucketPermissions`, conditions the same action to the project's own prefix. The bucket's
  policy holds `DenyInsecureTransport` alone. Every project role of the domain lists every project's keys
  in `awsds-sandbox-smus-projects`, and a partitioned table's keys carry its partition values. No file of
  this repository records it.
- **[user] The revoke** in `eighth-experimentation` from the portal. The same cell run right after it
  read 10; run again at 23:01:21, `TABLE_OR_VIEW_NOT_FOUND`, 6.9 s. The same `list-objects-v2` answered
  the same key after the revoke.
- **[Claude] ix's pieces**, 23:03:15 UTC: the subscription `REVOKED`; the grant `cm2l6qv25dsy6o`
  `ResourceNotFoundException`; on `app_etl.trades_notional` the owning project role's
  `ALL,ALTER,DELETE,DESCRIBE,DROP,INSERT` and `SELECT` alone, the subscription's conditioned `SELECT`
  gone; the link `EntityNotFoundException`; `test-experimentation`'s asset `b5r73n41qe7jf4` still in its
  inventory.
- **[Claude] The trails**: Data Governance's `RevokeSubscription` on `d21t6zwyzrcas0` at 23:00:00 by
  `awsds-data-studio-domain-execution`, session `user-28f1b390-0041-7068-8cc7-9ccef94277d1`, no error,
  no `retainPermissions` in the request. Sandbox's `BatchRevokePermissions` at 23:00:52 by
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/AWSDataZone-Subscriptions`, one entry, and
  `DeleteTable` `trades_notional` at 23:01:02 by
  `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw/AWSDataZone-Subscriptions`, no errors.
- **[Claude] ix read**: the open session read through the link until the link's delete, 62 s after the
  revoke, and resolved no table after it. Whether a session reading by the target's name keeps reading
  past `BatchRevokePermissions` is not measured.
- **[user] The kernel closed**. **[Claude]** the session `STOPPING` at 23:07:29 and `STOPPED` at
  23:07:37 UTC, `ExecutionTime` 1151.9 s, `DPUSeconds` reported 0.0: about 1.4 USD at 10 DPU and 0.44
  USD/DPU-h, `docs/PRICING.md`'s Glue rate before 6.0, written for ETL.
- **[user] The space deleted** from the portal. **[Claude]** no space and no app on `d-lfgbdrjncmsu` at
  23:12:58 UTC.
- **[user] Steps 7 to 9** in the portal: the data product `trades-notional`, the asset `trades_notional`
  and the source `…-AwsDataCatalog-app_etl-default-datasource` deleted.
- **[Claude] Read** 23:12:58 UTC: the data product `bvs7m8z4h6w70w` and its listing `dpx3r3w5msguc0`
  `ResourceNotFoundException`; the asset `4j6p77v7dm2840` `ResourceNotFoundException`, its listing
  `ct5d0innrgw3v4` `INACTIVE`; the source `budryu9mt9y5u8` `ResourceNotFoundException`, ahead of its
  23:41 run; `my-data-product` (`cqrp6eqjjpvvgw`) `CREATED`. `eighth-experimentation` keeps the assets
  `house-price` and `trades`, and the sources over `new_database`, `glue_db_blerpkhn9nj7o0` and
  `mydatabase` beside the Tooling one.
- **[user] Step 10's drops** in the query editor, `DROP TABLE app_etl.trades_notional;` and `DROP
  DATABASE app_etl;`, then **step 11's** `delete-environment` on `chz5jdb80ohocw`, run by the user from
  the laptop as Sandbox's `InfrastructureAccess`, the step having it by Claude's hand on the user's word.
- **[Claude] Read** 23:18:38 UTC: `app_etl` `EntityNotFoundException`; the environment
  `ResourceNotFoundException`, its stack `DataZone-Env-chz5jdb80ohocw` `DELETE_COMPLETE` at 23:18:11.98;
  no grant on the database. The table's folder holds no current object: 16 versions noncurrent behind 31
  delete markers, the latest at 23:17:27, so the drop removed the files and the bucket's 90-day
  noncurrent expiration keeps them. `eighth-experimentation`'s environments: `Tooling`,
  `eighth-experimentation-lakehouse`, `create-datalake-database-env-new_database-…`, `ml-demo-mlflow` and
  the `CREATE_FAILED` `create-datalake-database-env-mydatabase-…`. The drops' `DeleteTable` and
  `DeleteDatabase` were not yet in Sandbox's trail at 23:19 (Lesson 62).
- **[Claude] The retirement's writes**, both trails read at 23:50 UTC, every portal call by
  `awsds-data-studio-domain-execution` for the data scientist's session `user-28f1b390-…`:
  - Sandbox: `DeleteApp` and `DeleteSpace` on `jup-std` (`d-lfgbdrjncmsu`) at 23:09:28 and 23:09:32, by
    `test-experimentation`'s project role in the user's session; `DeleteTable` `trades_notional` at
    23:17:26 and `DeleteDatabase` `app_etl` at 23:17:36, by `eighth-experimentation`'s project role
    (`datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, session `28f1b390-…@5hkjdsy3umpi1c`), no errors.
  - Data Governance: `CreateListingChangeSet` `UNPUBLISH` on `bvs7m8z4h6w70w` at 23:09:55 and
    `DeleteDataProduct` at 23:10:01; `DeleteDataSource` on `budryu9mt9y5u8` at 23:11:14 refused,
    `ValidationException` with no message; `UNPUBLISH` on `4j6p77v7dm2840` and `DeleteAsset` at 23:11:38;
    `DeleteDataSource` on `budryu9mt9y5u8` accepted at 23:11:51. The source's delete was refused while
    its imported asset stood and accepted 13 s after the asset's delete; the cause is inferred from the
    order, the refusal carrying no text. `DeleteEnvironment` on `chz5jdb80ohocw` at 23:18:00, by Sandbox's
    `AWSReservedSSO_InfrastructureAccess_…` from `aws-cli/2.37.12`.
- **[user] Step 12**: `app_etl` created in `app-etl-dev` from the portal.
- **[Claude] Read** 23:25 UTC: the environment `b9304qgv01an0w`,
  `create-datalake-database-env-app_etl-1794698623506`, `ACTIVE`, created 23:23:44; the database
  `app_etl`, *"Created by DataZone for project app-etl-dev"*, at
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/ceweti7jbiu1hs/dev/data/catalogs/`, created
  23:24:00. Lake Formation's grants under `context.datazone.projectId=="ceweti7jbiu1hs"` to the
  account's `IAMPrincipals`: `CREATE_TABLE,DESCRIBE,DROP` on the database, `ALTER,DELETE,DESCRIBE,DROP,
  INSERT` and `SELECT` on its tables; `awsds-sandbox-smus-provisioning` grantable `ALL` on the database;
  `awsds-sandbox-smus-manage-access` `CREATE_TABLE,DESCRIBE` with grantable `DESCRIBE`, and grantable
  `DESCRIBE` and `SELECT` on the tables. The source `5xkhlb1ubnrf9s`,
  `…-AwsDataCatalog-app_etl-default-datasource`, created 23:24:11.87, `cron(24 23 * * ? *)`, the minute of
  its creation as `SUP-184` read; `publishOnImport` false, business names off, the filter `app_etl`
  `INCLUDE *`, on the connection `d4r792pkc5soeo`; no run.

## 2026-11-14 — the Sandbox sitting, steps 13, 14 and 16: the deploy and run in `app-etl-dev`, the downs

The user's acts in the space and from the project folder; Claude's reads as `awsds-infra-sandbox-1` and
`awsds-infra-data`. The day's last entries ran past midnight UTC, on 2026-11-15.

- **[user] Step 13**: the space `jup-medium` in `app-etl-dev`, JupyterLab on `awsds-sandbox-dev-env`
  version 11, `ml.t3.medium` (`InService`, read 23:39 UTC); the tar extracted; §D step 3's values with
  `DEV_PROJECT_NAME` `app-etl-dev`, `TRAINING_IMAGE_URI` a placeholder and `JOB_IMAGE_URI` `v0.4.6`'s
  digest typed in the space; the two zips; `scripts/dev-cli.sh deploy --manifest manifest.yaml --targets
  dev --skip-validation --no-events`.
- **[user] The deploy's output**, 23:41:22 to 23:42:40 UTC: *"aws-smus-cicd-cli 1.0.9 on
  /opt/awsds/venv/bin/python, the domain lookup answered by DOMAIN_ID"*; 11 files under the project's
  `shared/app-etl/`; *"No managed Tooling.GA/Tooling.Lightning blueprint found; will try the IAM connection
  fallback"*, then the Tooling environment's two subnets, its security group and its key resolved; the
  workflows `app_etl_app_etl_dev_app_etl` and `app_etl_app_etl_dev_app_etl_train` created `READY` at
  23:42:28 and 23:42:40 with the project role. No *"No custom VPC config"*. `GetGroupProfile` refused at
  each storage item by the domain's resource policy, as §D says.
- **[Claude] The workflow**, 23:47 UTC: `READY`, the role `datazone_usr_role_ceweti7jbiu1hs_6kvndq6t2757rk`,
  `NetworkConfiguration` the project's security group and two subnets, `CUSTOMER_MANAGED_KEY` the project's
  key.
- **[user] The run**, `scripts/dev-cli.sh run … --workflow app-etl`: `huQUoGZvttPwAMs` started at
  23:48:48, after `ListTagsForResource` refused on eight other workflows, as §D says.
- **[Claude] The run followed**: `QUEUED` to 23:51:18, then the tasks `transform` 178 s, `process` 493 s,
  `summarize` 9 s, `write_result` 10 s and `publish` 6 s, each `SUCCESS`; the run `SUCCESS`, started
  23:48:54, completed 00:03:47 UTC, 893 s, within pass 1's 816 to 936 s. `publish` returned at once,
  `PUBLISH_LISTING` being false.
- **[Claude] Step 14's reads**:
  - the table, 00:05:35 UTC: `app_etl.trades_notional`, `EXTERNAL_TABLE`, `table_type` `ICEBERG`, 6
    columns, version 0, created 23:52:11 UTC by `datazone_usr_role_ceweti7jbiu1hs_6kvndq6t2757rk/
    GlueJobRunnerSession`, at
    `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/ceweti7jbiu1hs/dev/data/catalogs/trades_notional`,
    metadata `00000-2e5ee239-f867-4616-ab53-ee36e32084e0.metadata.json` (verification i on the project's
    objects);
  - Sandbox's trail: `CreateTable` on `app_etl.trades_notional` at 23:52:11 by that session from
    `10.20.37.25` through `vpce-0dc0ad9337ef70d9b`, `lakeFormationPrincipal` the project role,
    `insufficientLakeFormationPermissions` empty: the conditioned `CREATE_TABLE` of step 12's grant admitted
    it;
  - Data Governance's trail: 23 `PostLineageEvent` from 23:51:14 to 23:52:13 UTC, no error, the caller
    `AWSAccount` with the principal `…:GlueJobRunnerSession`, from `10.20.37.25` through
    `vpce-0959660994e34ad71` (v's domain half);
  - `./aws/catalog.py`, ending 00:19 UTC: all checks passed; `CT-13`'s latest start is 22:01:21's, so the
    task started no source; `app-etl-dev`'s source `5xkhlb1ubnrf9s` has no run and no asset. 9 listings,
    11 before item 20; `CT-16` passes with no subscription, `CT-17` reads `mydatabase.house-price` and
    `CT-18` `house-price` alone. `CT-19`'s inventory reads `test-experimentation`'s asset
    `trades_notional` against *"no such table"*, the link gone, the asset kept.
- **[user] Step 16**: the space `jup-medium` deleted, the portal's tabs closed, `make down ENV=sandbox` and
  `make hub-down`: *"Desci tudo"*.
- **[Claude] The readings that end a sitting**: `make status` from 00:13:57 to 00:16:07 UTC,
  `production/vpn`, `production/proxy` and `production/tooling` stopped, the estimated burn 0.0000 USD/h;
  `./aws/egress.py awsds-infra-prod awsds-infra-staging awsds-infra-sandbox-1` at 00:14 UTC, all checks
  passed, no interface endpoint and no NAT gateway in the three accounts; no space and no app on
  `d-p6gthxc82ckg`, `d-lfgbdrjncmsu` and `d-spi9kgo6x5b4`.
- **[Claude] Owed**: step 15, the user's portal acts in `app-etl-dev` (the source's run, the asset's
  metadata, the data product left unpublished), then step 17; the consumer source's scheduled run at
  02:51 UTC, the first after the revoke, read for what it does with the asset whose link is gone.

## 2026-11-15 — the Glue session's DPU-seconds and the interactive-session rate, with nothing up

Claude's reads as `awsds-infra-sandbox-1`, Sandbox's `InfrastructureAccess`.

- **[Claude] The Glue session re-read**: `glue get-session` at 00:31:20 UTC on
  `4gqfau9xuo6e4w-93939e2b-07b3-4c1b-b18a-e875438bd870`: `STOPPED`, `ExecutionTime` 1151.921 s,
  `DPUSeconds` 3248.638, `MaxCapacity` 10.0, `NumberOfWorkers` 10, and `DefaultArguments` carrying
  `--enable-auto-scaling` `true` and `--enable-lakeformation-fine-grained-access` `true`. The same call
  read `DPUSeconds` 0.0 at 23:07:41, 4 s after the stop; `list-sessions` at 00:30:15 read 3248.638 with
  `DefaultArguments` null. The field is below the service model's `ExecutionTime * MaxCapacity`, 11519.2,
  an average of 2.8 DPU (`SUP-368`). The 2026-11-14 entry's 1.4 USD assumed 10 DPU for the whole run.
- **[Claude] The rate**, the Price List's `AWSGlue` offer of 2026-11-08: `USW2-GlueInteractiveSession-DPU-Hour`
  0.44 USD per DPU-hour, `SAE1-GlueInteractiveSession-DPU-Hour` 0.69, and the `-Gen2` type for Glue 6.0
  and later 0.308 (`PRICING.md` §5). At 0.44 the field's DPU-seconds are 0.40 USD and the formula's 1.41.
- **[Claude] A correction**: `docs/SMUS.md` named `project.spark.fineGrained` as the EMR Serverless
  engine's connection. The 2026-11-14 connection read shows it a `SPARK` connection on Glue interactive
  sessions, and the row now says so.
- **[Claude] Owed**: Sandbox's `USW2-GlueInteractiveSession-DPU-Hour` line for 2026-11-14 once Cost
  Explorer holds the day (`runbooks/security-hub.md` V3's command with that usage type): 0.90 DPU-h if the
  bill counts `DPUSeconds`, 3.20 if it counts the formula.

## 2026-11-15 — step 17's commands, step 15's schedule and §R's third domain, with nothing up

Claude's reading of the CI/CD CLI's installed code and of the records. No AWS call: the infrastructure
user's SSO token had expired by 02:00 UTC.

- **[Claude] The sitting's cost, estimated in chat** from the trails' times and the recorded rates: about
  1.5 USD, 1.25 to 1.9, the largest lines the Glue session (0.40 at its `DPUSeconds`), AWS Config's cycle
  (0.36 to 0.87, `cost-model.md`'s range) and Sandbox's 19 endpoints for about 1.77 h (0.34 to 0.57); about
  3.1 if the bill counts the session's formula and each endpoint's clock hours. The standing floor is out
  of it. **[user]**, to whether the bill is recorded once Cost Explorer holds both days: *"Não precisa"*.
  `SUP-368`'s one line stays owed.
- **[Claude] Step 17 prepared**: the CLI 1.0.9's `bundle` read in the laptop's `uv tool` install. Its
  configuration carries the target's region alone (`commands/bundle.py`), so the manifest's domain id is
  unused: `helpers/utils.py` tries `DescribeStacks` on `cicd-test-domain-stack`, then calls `ListDomains`
  and takes the one domain listed, failing on two (`SUP-162`'s call, not measured on `bundle`). It reads the
  project, its members and its connections, then the catalog by `Search`, `SearchTypes`, `GetAsset` and
  `GetDataProduct` (`helpers/catalog_export.py`), and writes the archive under `./artifacts`; no call
  writes in AWS. The stage file's step 17 now carries the commands: the two code zips `build-task-code`
  builds, the placeholders the `bundle` job sets, the bundle, the guard.
- **[Claude] Step 15's source**: `5xkhlb1ubnrf9s`, on `cron(24 23 * * ? *)` since 23:24 UTC on 2026-11-14,
  had no run at 00:19 UTC and carries `publishOnImport` false (`CT-4`, that run). Its first scheduled run,
  at 23:24 UTC on 2026-11-15, imports the table unlisted, so the portal's run is needed only before that
  minute. Written in step 15 and in the waiting list's row.
- **[Claude] `runbooks/promotion.md` §R**: the loop over the Studio domains gains `app-etl-dev`'s
  `d-spi9kgo6x5b4`, which the readings at 00:16 UTC covered by hand.
- **[Claude] Owed**: the consumer source's scheduled run at 02:51 UTC, read once the infrastructure user
  signs in again.

## 2026-11-15 — the consumer source's scheduled run after the revoke, and step 17 rehearsed

Claude's reads as the infrastructure user: `awsds-infra-data` for the sources and their runs,
`awsds-infra-sandbox-1` for the consumer's inventory, the bundle and the trail. As `awsds-infra-data`,
`GetAsset` on the consumer's inventory asset was refused, *"User is not permitted to perform operation:
GetAsset"*: Data Governance's role is no member of `test-experimentation`.

- **[user] The sign-in** as the infrastructure user, by 02:41 UTC: *"Já fiz o login"*.
- **[Claude] Step 15's source**, 02:42 UTC: `5xkhlb1ubnrf9s` `READY`, `ENABLED`, `publishOnImport` false,
  `cron(24 23 * * ? *)`, created 23:24:11 UTC on 2026-11-14, no run. Step 15's note holds.
- **[Claude] The baseline**, 02:42 UTC: the consumer's source `3zp6fog9jep1qo`, on `cron(51 2 * * ? *)`, last
  ran at 22:01:22 on 2026-11-14 (`PRIORITIZED`, `lastRunAssetCount` 1); the asset `b5r73n41qe7jf4`
  `trades_notional` at revision 1, no listing, the forms `GlueTableForm`, `DataSourceReferenceForm`,
  `SubscriptionTermsForm` and `AssetCommonDetailsForm`, the inventory's one asset.
- **[Claude] Step 17 rehearsed** before step 15, from the worktree's `examples/app-etl/` with the stage
  file's commands, as `awsds-infra-sandbox-1`: `bundle` from 02:42:53 to 02:43:18 UTC, exit 0, 12 files in
  `artifacts/app-etl.zip` (25,093 bytes), the export's six sections empty (*"No catalog resources found for
  project ceweti7jbiu1hs"*); the guard *"FAIL  assets: trades_notional is in the export 0 time(s), once
  expected"*, exit 1. The CLI printed two `GetGroupProfile` refusals, *"no resource-based policy allows the
  datazone:GetGroupProfile action"*, for the group profiles `06d426f2-84d6-38ae-a991-6806981d9520` (the
  bundle role's) and `839bcde8-f8b8-4ada-936a-1441352db302`.
- **[Claude] The rehearsal's trail**, Sandbox, 02:42:50 to 02:43:30 UTC: 28 calls by the session, every one a
  read. `cloudformation:DescribeStacks` at 02:42:55, `ValidationException` *"Stack with id
  cicd-test-domain-stack does not exist"*; `datazone:ListDomains` at 02:42:56, answered; then
  `ListProjects`, `GetProject`, `GetUserProfile` (2), `ListProjectMemberships`, `GetGroupProfile` (2,
  `AccessDenied`), `ListConnections` (3), `GetConnection` (9), `ListEnvironments`, `Search` (4) and
  `SearchTypes` (2). `ListDomains` on `bundle` is measured, and `SUP-162` gains the reading.
- **[Claude] The scheduled run**, read 02:53 UTC: `4etghy8jms5o5s`, `SCHEDULED`, `SUCCESS`, 02:51:09.214 to
  02:51:10.521 UTC; `added`, `updated`, `unchanged` and `failed` 0, no activity, no error; the source's
  `lastRunAssetCount` 0. `glue_db_4zojr4rr6bmnww` holds no table. The asset `b5r73n41qe7jf4` unchanged:
  revision 1, no listing, the same four forms, still the inventory's one asset (verification x,
  `SUP-197`).
- **[Claude] `./aws/catalog.py`**, 02:54:36 to 02:57:13 UTC: all checks passed. `CT-19` reads
  `test-experimentation`'s `trades_notional` against *"no such table"*; the consumer's source 28 runs,
  `SUCCESS`; `CT-4` all 12 sources `publishOnImport` false; `CT-15` 9 listings, none of `app-etl-dev`;
  `CT-13`'s latest start still 22:01:21's. `app-etl-dev`'s `Tooling-default-sagemaker-modelpackagegroup-datasource`,
  on `cron(7 2 * * ? *)`, read `RUNNING` on its first run, a third source of `EXC-11`'s kind.
- **[Claude] Owed**: Sandbox's `USW2-GlueInteractiveSession-DPU-Hour` line for 2026-11-14 (`SUP-368`).

## 2026-11-15 — steps 15 and 17: the product curated in `app-etl-dev`, `product.json` requiring its data product

The user's acts in the portal as the Data Scientist User, with nothing up; Claude's reads as
`awsds-infra-data` (the source's runs) and `awsds-infra-sandbox-1` (the inventory, the data product, the
bundle), and the template's change.

- **[Claude] The instructions** for step 15 at 03:08 UTC, before the source's first scheduled run at 23:24
  UTC, so the run is the portal's: the description and README texts proposed, the form `classification`
  `internal`, the data product left unpublished, no JupyterLab or Code Editor opened.
- **[user] Step 15** in `app-etl-dev`: *"Fiz o passo 15"*.
- **[Claude] The source's run**: `577dc5ia9du07k`, `PRIORITIZED`, `SUCCESS`, created 03:11:22.274 and
  stopped 03:11:25.710 UTC; `added` 1, `updated`, `unchanged` and `failed` 0; one activity, `app_etl`
  `SUCCEEDED_CREATED`, the asset `c6z3pbg3drrs0g` `trades_notional`. `CT-13` reads its start at 03:11:22 by
  `awsds-data-studio-domain-execution`, verdict `other`, the portal's.
- **[Claude] The asset**: revision 1 by `SYSTEM` at 03:11:25.220, revisions 2 to 4 by the data scientist's
  profile `28f1b390-…` at 03:12:56, 03:13:18 and 03:13:45 UTC. Revision 4 carries the description, the README
  in `AssetCommonDetailsForm` and the form `classification` `{"classification":"internal"}` of type
  `classification` revision 2, which `get-form-type` names as `eighth-experimentation`'s (`avhvbqn37ty7m8`,
  `ENABLED`); no listing. A project attaches a form type another project owns: item 22's measurement,
  decision 4's first branch.
- **[Claude] The data product**: `5070mjwdvjwp3k` `trades-notional`, revision 1, `CREATED`, created
  03:14:56.022 UTC by the same profile, no description, one item, `ASSET` `c6z3pbg3drrs0g`.
- **[Claude] `./aws/catalog.py`**, 03:16:30 to 03:18:56 UTC: all checks passed. `CT-15`: 9 listings, none of
  `app-etl-dev`; `CT-19`'s inventory reads `app-etl-dev`'s `trades_notional` over `app_etl.trades_notional`,
  not a link; the source 1 run, `SUCCESS`, `lastRunAssetCount` 1. No app and no space on `d-p6gthxc82ckg`,
  `d-lfgbdrjncmsu` and `d-spi9kgo6x5b4`.
- **[Claude] Step 17**: the bundle from the template's folder with the stage file's commands, 03:19:45 to
  03:20:09 UTC, exit 0, `artifacts/app-etl.zip` 25,910 bytes, SHA256 `4b852993…21aacfe`. The export holds
  `assets` `trades_notional` (its forms `GlueTableForm` 13, `DataSourceReferenceForm` 5,
  `SubscriptionTermsForm` 2, `AssetCommonDetailsForm` 8 and `classification` 2, each by name and revision)
  and `dataProducts` `trades-notional`, its item the `dev` asset's id; `formTypes`, `glossaries`,
  `glossaryTerms` and `assetTypes` empty (xii's bundle half). The guard: *"FAIL  dataProducts:
  trades-notional is in the export and not in product.json"*, exit 1.
- **[Claude] The change**: `examples/app-etl/product.json` requires `dataProducts` `trades-notional` beside
  the asset, and the guard on the same archive answers *"OK"*. The test sample in
  `tests/test_catalog_export.py` carries the data product, and a new case fails a release without it. The
  template's gates: `uv sync --locked`, ruff check and format clean, `pytest` 85 passed and 1 skipped. The
  build outputs and the template's `.venv` were removed after.
- **[Claude] Owed**: Sandbox's `USW2-GlueInteractiveSession-DPU-Hour` line for 2026-11-14 (`SUP-368`).

## 2026-11-15 — `TM-29`'s trigger read and `TM-31` decided: the start grant kept in Production alone

The user's decision in the session's chat; Claude's reads with nothing up, as `awsds-infra-sandbox-1`,
`awsds-infra-staging` and `awsds-infra-prod`, and the edits.

- **[Claude] The options**, each with a recommendation: decision 17's (a) with (d) kept and `CT-13`
  widened to the reads; `TM-31` accepted.
- **[Claude] The readings behind them.** `SageMakerStudioProjectUserRolePolicy` at `v77` holds
  `ListDomainS3BucketPermissions`, `s3:ListBucket` and `s3:ListBucketVersions` on the domain bucket under
  `s3:prefix` `<domain>/<project>` and `<domain>/<project>/*`, beside `AirflowListDomainS3Permissions`,
  `s3:ListBucket` on the same bucket with no prefix condition, and its companions `AirflowS3BucketActions`
  (`GetEncryptionConfiguration`, `GetBucketPublicAccessBlock`) and `AirflowS3GetAccountPublicAccessBlock`.
  Sandbox's trail holds the reads of 2026-11-14 by `test-experimentation`'s role
  `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw`, each answered: `GetDataSource` on `budryu9mt9y5u8` at
  22:52:16, `GetDataSourceRun` on `6bnfg5dk961bps` at 22:52:18 and `ListDataSourceRunActivities` at
  22:52:19 UTC. Decision 20 (b) gives Sandbox's `StartDataSourceRun` the listing code's exercise in `dev`
  alone, and Staging's `PUBLISH_LISTING` is false, so its task returns before the start.
- **[user] The lens**: *"Revise as recomendações sobre essas duas decisões, considerando que estamos
  querendo seguir o uso pretendido padrão do SMUS, conforme recomendado pela AWS."*
- **[Claude] The revised recommendations**: decision 17 (b) in Sandbox and Staging and (a) in Production,
  read again at 4.13; the reads accepted as the platform's, with no new check; `TM-31` accepted, the
  bucket-policy deny left as the control a trigger reopens.
- **[user] The decision**: *"Sim, revisadas"*.
- **[Claude] The code**: `sandbox/workflows/main.tf` loses the statement
  `StartADataSourceRunInTheProjectsDomain`. `<env>/studio/workflows.tf` is one copy in both targets
  (`scripts/check-copies.py`, which failed on a first edit that removed the statement from Staging's copy
  alone), so the statement and the description's data-source clause stand behind a new variable in each
  account's `project-roles.tf`, `publishing_starts_the_source`, true in Production and false in Staging;
  the copy's comment carries the reasoning Sandbox's file held.
- **[Claude] The plans**, each slice's tfvars regenerated in this worktree: `sandbox/workflows/` `0 to add,
  1 to change, 0 to destroy`, `awsds-sandbox-workflows` in place, the statement removed;
  `staging/studio/` `2 to add, 0 to change, 2 to destroy`, `awsds-staging-workflows` replaced for its
  description and its attachment to `datazone_usr_role_5ido8bej1zoeq8_d6nu5aphq1e974` with it;
  `production/studio/` `No changes`, as `awsds-infra-prod`. The two plans that change something are saved
  outside the repository; the applies wait for the user's authorization.
- **[Claude] The report's lines** for decision 17 (d), beside the text of 2026-11-11:

  > A principal that is no member of a project reads that project's data source, its runs and each run's
  > activities (`GetDataSource`, `GetDataSourceRun`, `ListDataSourceRunActivities`), which name the tables
  > the project catalogues and their asset ids.
  >
  > `SageMakerStudioProjectUserRolePolicy`'s statement `AirflowListDomainS3Permissions` grants
  > `s3:ListBucket` on the domain bucket with no `s3:prefix` condition, so every project role lists the
  > object keys of every other project sharing the bucket, while its statement
  > `ListDomainS3BucketPermissions` grants the same listing under the project's own prefix.

## 2026-11-15 — decision 17's revision applied: the start grant out of Sandbox and Staging

The same day, nothing up. The user, verbatim: *"Autorizo os 2 applies"*. The app's classifier let each
through.

- **[Claude] Before the writes**: the two other sessions on the laptop, idle, told of the applies and of
  Lesson 79 until PR #302 merges, and a note left in the orchestrator's notes folder. The three profiles
  answered as the infrastructure user, `InfrastructureAccess` in Sandbox, Staging and Production.
- **[Claude] The plans, made again from `6d0b8238`** so that each apply reads the state of the moment:
  `sandbox/workflows/` `0 to add, 1 to change, 0 to destroy` and `staging/studio/` `2 to add, 0 to change,
  2 to destroy`, the diff in each the statement `StartADataSourceRunInTheProjectsDomain` alone and, in
  Staging, the description that forces the policy's replacement with its attachment.
- **[Claude⚡] `sandbox/workflows/`**, 04:31:44 to 04:31:54 UTC: *"0 added, 1 changed, 0 destroyed"*,
  `awsds-sandbox-workflows` modified in 2 s.
- **[Claude⚡] `staging/studio/`**, 04:32:02 to 04:32:17 UTC: *"2 added, 0 changed, 2 destroyed"*. In
  order: the attachment to `datazone_usr_role_5ido8bej1zoeq8_d6nu5aphq1e974` destroyed, the policy
  destroyed and created, the attachment created. The role went about two seconds without the policy, with
  nothing running in Staging.
- **[Claude] Read after them**: the three slices re-plan `No changes`, `production/studio/` as
  `awsds-infra-prod`. `awsds-sandbox-workflows` is at `v5`, updated 04:31:53 UTC, with
  `DescribeAProcessingJobNoProjectHolds`, `TagAProcessingJobWithTheCallersProject` and
  `GetAGlueJobNoProjectHolds`, attached to the three Sandbox project roles
  (`datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw`, `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`,
  `datazone_usr_role_ceweti7jbiu1hs_6kvndq6t2757rk`). `awsds-staging-workflows` is a `v1` created
  04:32:13 UTC with the same three statements, its description without the data-source clause, attached to
  `deploy-staging`'s role alone. `awsds-prod-workflows` is unchanged, `v1` since 2026-11-11 15:19:04 UTC,
  its four statements `StartADataSourceRunInTheProjectsDomain` among them, attached to
  `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow`.
- **[Claude] AWS's managed policies at the applies**: `SageMakerStudioProjectRoleMachineLearningPolicy`
  `v48` and `SageMakerStudioProjectUserRolePolicy` `v77`, both the default since 2026-11-13 20:47:08 UTC
  (open question 22's reading of 2026-11-14). Neither names `StartDataSourceRun` nor holds an `Allow` with
  `NotAction`; v48's DataZone actions are v47's with `datazone:UpdateAssetOwner` added to
  `DataZoneUserPermissions`, on `*`. The comment of `<env>/studio/workflows.tf` cited v47, read
  2026-11-08, and names v48 since; the plan reads no comment.
- **[Claude] Until PR #302 merges**, a plan of either slice from a tree without its commits restores the
  statement (Lesson 79).

## 2026-11-15 — PR #302 merged; the Lesson 79 window closed

Claude's reads of GitHub and git, no AWS call. The session `Stage 19: SUP-368's Glue line in the bill`
relayed the merge; each fact below was read here.

- **[user] PR #302 merged** at 04:52:26 UTC, squashed into `729a06da`, its head `dd488b0c` (`gh pr view
  302`).
- **[Claude] The three slices on `main`**: `sandbox/workflows/`, `staging/studio/` and `production/studio/`
  at `729a06da` are `dd488b0c`'s, `git diff` empty. The applies' plans were made from `6d0b8238`, which
  differs from it in one comment line of each `<env>/studio/workflows.tf` (v47 to v48). A plan from any
  tree holding `729a06da` keeps decision 17's revision, so the previous entry's window is closed.

## 2026-11-15 — release T's sitting prepared with nothing up: the gates, the two merge requests

Claude's reads on the laptop, with no AWS call: the infrastructure user's SSO token had expired. Each
tree was extracted with `git archive` into the session's scratch folder, outside the repository.

- **[Claude] Release T's gates** (`runbooks/promotion.md` §N.8.2 step 1), on `36bcf916:examples/app-etl`:
  `uv sync --locked`; `ruff check` *"All checks passed!"* and `ruff format --check` *"12 files already
  formatted"*; `pytest` 72 passed and 1 skipped; the lint at `d856982c` with the job's instance types and
  algorithm repository, *"ok: 9 arquivo(s)"*; `uv export` as the gate runs it, one pinned package,
  `pyarrow` 25.0.1, and `pip-audit` 2.10.1 against OSV, *"No known vulnerabilities found"*.
- **[Claude] `./scripts/check-gitlab-ci.py`**, `main`'s copy run over `36bcf916`'s tree and over `main`'s:
  *"OK"* on both, the one unread include GitLab's `Jobs/Secret-Detection.gitlab-ci.yml`.
- **[Claude] Release F's gates**, on `main`'s `examples/app-etl/` (`729a06da`): ruff clean, 85 passed and 1
  skipped, the lint at `196acee` *"ok: 9 arquivo(s)"*, `pip-audit` on `pyarrow` 25.0.1 with no finding.
- **[Claude] The template's merge request**: the clone `$HOME/tmp/app-etl` is on `main` at `8d50f68`, the
  merge of `kms-key-id`, clean, with tree `5a5970a2…`, the tree of `2d3160f1:examples/app-etl`. The merge
  request is `git diff 2d3160f1 36bcf916 -- examples/app-etl`: 12 files, 1,040 insertions and 214
  deletions, `scripts/dev-cli.sh` and `tests/test_dev_cli.py` new. GitLab's `main` is read at the sitting.
- **[Claude] `awsds/dev-env`'s merge request**: the copy under `gitlab/awsds/dev-env/` differs from
  `gitlab/mirror.json`'s `6eff905` in `.gitlab-ci.yml` alone, 5 insertions and 3 deletions (`b9e8601e`,
  PR #273). The clone `$HOME/tmp/dev-env-v0.10.0`, on its branch `the-releases-v0.10.0` at `fb5722b`, holds
  the copy's file as of the last mirror.
- **[Claude] That merge request's `pip-audit`**: the copy's `dev-env/python` lock exported as the gate does,
  454 pinned packages, each line marked `platform_machine == 'x86_64' and sys_platform == 'linux'`. On the
  laptop `pip-audit` audited 0 of 454, every marker false, and still printed *"No known vulnerabilities
  found"*; the gate's own count fails such a run. With the markers removed and Python 3.12, 454 of 454
  audited: 105 findings, 76 matched by id or alias in `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV`, 29 blocking with a
  fixed version (`langgraph` 1.2.11, `langgraph-sdk` 0.4.4, `msgpack` 1.2.2, `nltk` 3.10.3, `oauthlib`
  4.0.0, `opentelemetry-api` 1.45.1, `pillow` 12.3.0, `pyasn1` 0.6.4, `soupsieve` 2.9.2, `tornado`
  6.5.10), none without one, no accepted entry gone.
- **[Claude] The other sessions**: `Stage 19: SUP-368's Glue line in the bill` idle, its worktree with no
  commit past `main` and no change.
- **[Claude] Owed with a sign-in**: the Amazon Linux parameter (§N.8.2 step 1), `make status`, and the
  re-plans of `staging/chains/` and `production/chains/` against the plans of 2026-11-12.

## 2026-11-15 — the readings owed with a sign-in: the burn, the Amazon Linux parameter, the chains re-plans, the role groups

Claude's reads as the infrastructure user (`InfrastructureAccess`) after the user's sign-in; no AWS write.
They close the previous entry's list owed with a sign-in.

- **[Claude] `make status`**, finished 19:34 UTC: a burn of 0.0000 USD/h. The hub's two hosts and GitLab's
  `stopped`; the runners, both warehouses' compute and every egress slice `down`; Production's
  `app/app-etl/` (3 resources) and `orchestration/` (41) `UP`.
- **[Claude] The Amazon Linux parameter** (`runbooks/promotion.md` §N.8.2 step 1), as `awsds-infra-prod`:
  `ami-0dac6cd09676c9fb1`, version 201, modified 2026-11-12 at 19:49:40 UTC; 2026-10-27 read
  `ami-0829b74b2a8c619b7`. The runners the next `make gitlab-up` creates boot on it. Stage 8 xxvii's plan
  half still waits: runners created on the current image plan `No changes` with or without
  `ignore_changes`.
- **[Claude] The chains re-plans**, from this branch's tree, which holds `729a06da` (Lesson 79):
  `staging/chains/` 18 to add at 19:32:15 UTC, `production/chains/` 24 to add at 19:32:28 UTC. The text from
  *"Terraform will perform the following actions"* on hashes the same as the plans of 2026-11-12, 02:52
  UTC; above it only the order of the data-source reads differs. The new plans replace the old at §N.8.4
  step 5's paths, the old kept as `stage19-chains-{staging,production}-1112.*` in `$HOME/tmp/`.
- **[Claude] Staging's retired slices**: `staging/orchestration/` and `staging/app/app-etl/` each read 0
  resources by `state list`, as §N.8.4 step 5 requires. The first `init` of `staging/orchestration/`, run
  while `make status` was initialising the slices it reads on the same tree, stopped on *"Module not
  installed"* for `orchestration-v0.2.1`; a second `init` succeeded.
- **[Claude] The domain's role groups** (`search-group-profiles --group-type IAM_ROLE_SESSION_GROUP` as
  `awsds-infra-data`, then `get-group-profile` on each): nine profiles. Three are SSO groups
  (`sso-group-deployment-managers`, `sso-group-data-scientists`, `sso-group-governance-managers`). Six are
  roles' sessions: the `InfrastructureAccess` of Sandbox Account 1 (`839bcde8-…`), Production
  (`ca2735c9-…`), Data Governance (`7ee243ab-…`) and Staging (`65b0f127-…`), `awsds-deploy-sandbox-test`
  (`06d426f2-…`) and `awsds-deploy-staging` (`9bead345-…`). `awsds-deploy-prod` has none, as §N.8.4 step 7
  expects.

## 2026-11-15 — release T's sitting: the raises, the mirror, the template's merge request and its variables

The user's acts, as the user reported them in the chat, and Claude's reads as the infrastructure user
(`InfrastructureAccess`) and, for GitLab, through the user's browser session (`runbooks/promotion.md` §N.8.2
steps 2 to 4).

- **[user] PR #303 merged** at 19:43:28 UTC (`3a15f2f6`). The session went on in the same conversation, on
  the user's word, on a new branch cut from that commit.
- **[Claude] The other sessions told** before the first raise: `Stage 19: SUP-368's Glue line in the bill`
  and `Worktrees para apagar`, both idle.
- **[user] `make hub-up`, `make gitlab-up BUILD=1` and the tunnel.** EC2's launch times: the VPN host
  19:43:57 UTC, the proxy 19:44:00, GitLab 19:46:05, the deploy runner 19:46:28, the build and test runners
  19:46:37. The three runners run `ami-0dac6cd09676c9fb1`, the parameter's value since 2026-11-12, their
  first boot on it; GitLab lists the three `online` (runners 1, 3 and 4 of `awsds/app-etl`).
- **[user] The mirror**, `git push gitlab main` from the project folder. **[Claude]** `ls-remote` read
  `awsds/infrastructure`'s `main` at `3a15f2f6`, `origin/main`.
- **[Claude] Step 2's readings.** `./aws/cicd.py` (19:56:44 UTC): `CI-1` to `CI-9` pass, the failed calls
  those of the persona profiles nobody had signed in. `./aws/egress.py awsds-infra-prod
  awsds-infra-sandbox-1`: every check passes, Production's 12 interface endpoints (`EG-5`, about 0.120
  USD/h), Sandbox's `egress/` down. `make status` (finished 19:59:47 UTC): 0.4571 USD/h, the hub's two hosts,
  `egress/` (12), `tooling/` and `runners/` (13, the build runner with them) up; Staging, Sandbox,
  `workloads-egress/` and both warehouses' compute down.
- **[Claude] GitLab's `main` before step 4**: `awsds/app-etl` at `8d50f68`, the clone's commit, so the
  merge request is the diff read offline; tags `v0.4.0` to `v0.4.6`, `v0.4.7` free.
- **[user] The template's merge request**, by step 4's commands: branch `release-t`, commit `cf2d1a5` on
  `8d50f68`, `12 files changed, 1040 insertions(+), 214 deletions(-)`; merge request !13, its pipeline #113
  (20:07:21 to 20:08:01 UTC) green, the merge `355ab8c` (parents `8d50f68` and `cf2d1a5`) and its pipeline
  #114 (20:09:15 to 20:09:59 UTC) green. **[Claude] read**: `release-t`'s tree and `main`'s are
  `416a897c…`, the tree of `36bcf916:examples/app-etl`. Pipeline #113 ran `test`, `pip-audit`,
  `secret-detection-gate` and `secret_detection`, #114 those and `pages`, each on the test runner;
  `gate-without-proxy` stays `manual` in both.
- **[user] The CI/CD variables.** **[Claude] read** through the API in the user's session: nine, each
  protected and unmasked: `DOMAIN_ID`, `DOMAIN_REGION`, `DEV_PROJECT_NAME` (`app-etl-dev`), `SUBNET_AZ1`,
  `SUBNET_AZ2`, `DEV_PROJECT_SG`, `DEV_PROJECT_KEY_ARN`, `ECR_REGISTRY`, `TRAINING_IMAGE_URI`. The four
  `TEST_PROJECT_*` are gone.
- **[Claude] `awsds/dev-env`**: `main` still at `6eff905`, step 5's merge request not yet opened.

## 2026-11-15 — release T's sitting: `awsds/dev-env`'s merge request and the tag `v0.4.7`

The user's acts by §N.8.2 steps 5 and 6; Claude's reads through `ls-remote` and through the API in the
user's browser session.

- **[user] `awsds/dev-env`'s merge request**, by step 5's commands: branch `sts-global-probe-goes-on`,
  commit `b6ae110` on `6eff905`, `1 file changed, 5 insertions(+), 3 deletions(-)`; its pipeline #115
  (20:19:59 to 20:21:26 UTC) failed at `pip-audit`, as step 5 expects; the user merged past it as `717d80b`
  (20:21:45 UTC), and `main`'s pipeline #116 failed the same way. **[Claude] read**: `main`'s
  `.gitlab-ci.yml` identical to `gitlab/awsds/dev-env/.gitlab-ci.yml`; #116's `pip-audit` (job 676) 454
  pinned packages against OSV, 76 findings accepted, 29 `BLOCK` in `langgraph`, `langgraph-sdk`, `msgpack`,
  `nltk`, `oauthlib`, `opentelemetry-api`, `pillow`, `pyasn1`, `soupsieve` and `tornado`, the laptop's
  count of the same day; `recipe-checks`, `secret-detection-gate` and `secret_detection` green. The merge
  copied back with `./scripts/gitlab-mirror.py awsds/dev-env`: *"the copy already holds this commit's 14
  file(s)"*, `gitlab/mirror.json` moved to `717d80b`.
- **[user] The tag `v0.4.7`** on `awsds/app-etl`'s `main`; `ls-remote` reads it at `355ab8c`, the merge of
  !13. Its pipeline #117 started 20:22:09 UTC: `pip-audit` and `test` green on the test runner,
  `build-task-code` green, `build-image` running on the build runner from 20:22:44 UTC.
- **[pipeline] #117 to `release`**: `build-image` 20:22:44 to 20:25:32 UTC on the build runner, `bundle`
  20:25:35 to 20:25:59, `store-bundle` to 20:26:09, `release` to 20:26:20; `scan-gate` (allowed to fail)
  still running at 20:27 UTC; `staging-gate` `manual`. **[Claude] read `bundle`'s log** (job 683, the
  deploy runner): the caller `assumed-role/awsds-deploy-sandbox-test`, *"Project: app-etl-dev"*, *"Total
  files: 11"* (`code/` 2, `src/` 3, `glue/` 2, `samples/` 1, `workflows/` 3, `app-etl-warehouse.yaml` among
  them), `artifacts/app-etl.zip` 24,076 bytes, SHA256 `001eafbb4d90514802f14f97c75043b5d1d0241295e3b11d944f96c730c65826`;
  no *"Failed to get project connections"* and no *"Pattern not found"*. The CLI's two warnings, `GetGroupProfile`
  refused on `06d426f2-…` and `839bcde8-…`, are the ones of 2026-11-10. Sandbox's event history over 20:25:00
  to 20:27:30 UTC read empty at 20:27:32, inside the trail's delay (Lesson 62); the reading is made again.
- **[Claude] Sandbox's event history over `bundle`'s minutes**, read again at 20:45: 27 events from
  20:25:45, every one of `awsds-deploy-sandbox-test` read-only: `GetCallerIdentity`, `ListDomains`,
  `ListProjects`, `GetProject`, `ListProjectMemberships`, `GetUserProfile` twice, `ListConnections` three
  times, `GetConnection` ten times, `ListEnvironments`; refused `DescribeStacks` (CloudFormation) and
  `GetGroupProfile` twice. No write by that role.
- **[user] `make up ENV=staging ONLY=egress`, then `staging-gate`** (job 686, 20:42:50 to 20:42:55).
  `staging-check` green 20:42:59 to 20:43:12, `staging-deploy` green 20:43:15 to 20:46:50, `staging-test`
  started.
- **[pipeline] #117's Staging leg green** (logs read through the API in the user's session): `staging-test`
  (job 689, 20:46:53 to 21:09:41 UTC) started `awsds-staging-chain-app-etl`'s execution
  `v0-4-7-117-app-etl`, `SUCCEEDED` at 21:02:24, then `v0-4-7-117-app-etl-train`, `SUCCEEDED` at 21:09:35, and
  read the table `trades_notional` at `s3://awsds-staging-outputs/app-etl/tables/trades_notional/`;
  `staging-model` (job 690, 21:09:44 to 21:16:03) ran `app-etl-v0-4-7-20261115T211007` on the model of
  `app-etl-train-20261115T210324`, 30 predictions for 30 batch rows, and deleted the model; Production's
  registry read version 1 `Approved`. `production-plan` (job 691, 21:16:06 to 21:16:50): the application
  slice `0 to add, 2 to change, 0 to destroy`, the two Glue jobs' `script_location` from `v0.4.6/` to
  `v0.4.7/`. `production-gate` `manual`.
- **[Claude] `./aws/orchestration.py`** (step 8): `OR-1` to `OR-9` pass. Staging's two workflows `READY` on
  `v0.4.7`'s definitions (`OR-5`), version 1 of 50 each; Production's three still on `v0.4.6`'s; every chain's
  schedule `DISABLED`, its failure rule `ENABLED`. The failed calls are the persona profiles nobody had signed
  in.
- **[user] Stage 10 decision 11's Staging half** (§N.8.2 step 9): the profile `awsds-deploy-staging` added
  by step 9's four `aws configure set`, `aws sso login --sso-session awsds-deploy --no-browser` as the
  Deployment Manager User (its token cached at 21:28:23 UTC), and the three reads: `get-workflow-run` on
  `awsds-staging-wf-app-etl`'s last run, `ukdqPTEi5Tav4PL`, answered `SUCCESS`. **[Claude]** at 21:29:36 the
  infrastructure user's token no longer loaded, *"Error loading SSO Token: Token for awsds does not exist"*,
  its cache file gone and the Deployment Manager's the only one with a start URL (`SUP-016`'s shape);
  Staging's trail waits for the infrastructure user's next sign-in.
- **[user] `make up ENV=production ONLY=workloads-egress`, then `production-gate`** (job 692, 21:22:31 to
  21:22:36 UTC). **[pipeline] `production-deploy`** (job 693, 21:22:38 to 21:25:37): `workloads-egress/` read
  up, 8 interface endpoints and 1 DNS Firewall association `COMPLETE`; the bundle `001eafbb…` copied under
  `s3://awsds-prod-outputs/applications/app-etl/v0.4.7/`; the application slice *"0 added, 2 changed, 0
  destroyed"* (the two Glue jobs' scripts) and the orchestration slice planned `0 to add, 3 to change, 0 to
  destroy`, the three workflows, and applied. `production-warehouse-ddl` and `production-register` stay
  `manual`: neither belongs to release T's sitting (the warehouse is §N.8.3's and §N.8.4's, with its compute
  up; the model's registration is not on §N.8.2's list).
- **[user] The infrastructure user signed in again.** **[Claude] Staging's trail for step 9**, read at
  21:31:52 UTC: `ListWorkflows` (21:28:46), `ListWorkflowRuns` (21:28:50) and `GetWorkflowRun` on
  `ukdqPTEi5Tav4PL` (21:28:55) in the session `AWSReservedSSO_DeploymentManagerAccess_284ceedc4ee6111b`, and at
  21:28:55 the paired `Decrypt` in the same session, `invokedBy airflow-serverless.amazonaws.com`, its
  encryption context the workflow's ARN, no error. Stage 10 decision 11's Staging half read.
- **[Claude] `./aws/orchestration.py` after `production-deploy`**: 45 checks pass; Production's three
  workflows on `v0.4.7`'s definitions (`OR-5`), versions 4, 3 and 3 of 50; the three chains' schedules
  `DISABLED`, their failure rules `ENABLED` (`OR-9`).
- **[user] The cause of the infrastructure token's loss**, asked by Claude: the user ran `aws sso logout`
  before the Deployment Manager's sign-in, answered in Safari, and again before the infrastructure user's new
  sign-in. **[Claude]** The loss read at 21:29:36 UTC is `SUP-015`'s logout, which removes every cached token,
  not `SUP-016`'s shape named above; no `SUP` entry gains a reading. §N.8.2 step 9 now says the two
  `sso-session`s' tokens coexist without a logout.
- **[Claude] §N.8.2 step 14, 3.7**: the four `release.tf`s on `v0.4.7`'s values, each slice planning *"No
  changes"* at 21:51 UTC with both legs up (Stage 8's log). Taken while the chain of step 11 ran, before
  `make down ENV=staging` destroys the Staging slices it plans.
- **[Claude] §N.8.2 step 17's reads**, before any delete, as `awsds-infra-sandbox-1`: in `test-experimentation`
  the workflows `app_etl_test_experimentation_app_etl` and `app_etl_test_experimentation_app_etl_train`, the
  Glue job `app-etl-4gqfau9xuo6e4w` (created 2026-10-19 18:55 UTC, its script under the project's
  `shared/app-etl/glue/`), and 19 objects, 37,310 bytes, under the project's `shared/app-etl/`, written
  2026-10-25 22:59:05 to 23:12:50 UTC. `houseprice_etl_test_experimentation_houseprice_etl` is the third
  workflow named after the project, not the application's. The deletes wait for the user's word.
- **[Claude⚡] §N.8.2 step 11, on the user's word in chat** (*"Sim, inicie a chain"*), the other sessions told
  first: `start-execution` of `awsds-prod-chain-app-etl` as `awsds-infra-prod`, the execution
  `v0-4-7-by-hand-2026-11-15-app-etl`, started 21:43:28 and `SUCCEEDED` at 22:00:33 UTC (17 min 05 s, 62
  history events). The Glue run of 21:44:30 read `lake.curated.trades` at snapshot `8185032439141629913`, the
  same as Staging's leg, and `trades.summary.json` sits under the data key at 21:52:45 (Stage 8's log, 3.3 in
  Production).
- **[Claude] §N.8.2 step 12a.1, on the user's word in chat** (*"você pode avançar em paralelo com o passo
  12a"*), while the user ran step 13. In the laptop's clone, from `awsds/app-etl`'s `main` at `355ab8c`, the
  branch `xx-undeclared-glue-job` with the one line `job_name: app-etl-undeclared-{proj.id}`, commit
  `90f5cc1`, pushed at 22:11. The branch pipeline #119: `test` green at 22:11:56 (*"72 passed, 1 skipped"*,
  the lint *"ok: 9 arquivo(s)"*). `git ls-remote` read `v0.4.8` free, and the tag `v0.4.8` was pushed on
  `90f5cc1` at 22:12:31: pipeline #120.
- **[user] §N.8.2 step 13, the space's readings** (pasted verbatim from the space `default`'s terminal, a
  JupyterLab space of `app-etl-dev`): `type -a aws-smus-cicd-cli` lists `/opt/awsds/bin/aws-smus-cicd-cli`
  first, then `/opt/conda/bin/aws-smus-cicd-cli` and `/opt/awsds/bin/aws-smus-cicd-cli` again;
  `aws-smus-cicd-cli 1.0.9`; `10.20.38.251    airflow-serverless.us-west-2.api.aws`; `73`. Each is the
  expected reading. The clone of `awsds/app-etl` as the Data Scientist User, with the persona's token at git's
  prompt: *"Receiving objects: 100% (154/154)"*.
- **[user] `staging-gate` of #120** at 22:17:15. **[Claude] §N.8.2 step 12a read** (Stage 10's log, verification
  xx's second half): `staging-test` failed at 22:24:11 on *"FATAL: the chain app-etl ended FAILED"*, `transform`
  refused at `GetJob` on `awsds-staging-app-etl-undeclared`, `CreateJob` 0, both failure rules and two
  notifications fired, Production untouched, no Sandbox residue. The branch's deletion is the user's.
- **[user] §N.8.2 step 13's deploy and run**, from the clone at `355ab8c` with §D step 3's values,
  `JOB_IMAGE_URI` `v0.4.7`'s digest, the two zips, `scripts/dev-cli.sh deploy` and `run --workflow app-etl`.
  **[Claude]** `app_etl_app_etl_dev_app_etl` `READY`, modified 22:24:24 UTC, version `a9387b9d…`, the project
  role, its security group and two subnets, `CUSTOMER_MANAGED_KEY`; the run `bzJIxFT4Hn64Go8` `QUEUED` at
  22:26:37. The proxy's log `/awsds/prod/proxy` from 22:10 UTC: no line naming `airflow-serverless`, while the
  space's own traffic is logged (10.20.41.98: the `awsds-workflows` clone's `CONNECT github.com:443 200` at
  22:22:43, `cloudformation.us-west-2` 7 times, and the `cognito-identity` and `client-telemetry` calls 6d's log
  records, about 300 each in 20 minutes). The deploy's calls to the MWAA Serverless API took the `mwaa` group's
  endpoint.
- **[user] 12a's branch deleted** in GitLab and in the laptop's clone (Stage 10's log).
- **[Claude⚡] §N.8.2 step 17, on the user's word in chat** (*"Sim, remova"*), the other sessions told first, as
  `awsds-infra-sandbox-1`, each object read before its delete: `delete-workflow` of
  `app_etl_test_experimentation_app_etl` (`READY`, last run `FAILED`, no run in progress) at 22:36:46 and of
  `app_etl_test_experimentation_app_etl_train` (`READY`, no run) at 22:36:48; `delete-job` of
  `app-etl-4gqfau9xuo6e4w` (last run `SUCCEEDED` on 2026-10-25) at 22:36:59; `aws s3 rm --recursive` of the
  project's `shared/app-etl/` at 22:37:23, the 19 objects listed before it (the two code zips, the two Glue
  scripts, `src/`, the three workflow files, the inbox, outbox, table and `work/` objects). The bucket is
  versioned, so each key ends in a delete marker and its versions stay. Read back: the prefix lists no object,
  19 delete markers at 22:37 beside 17 older ones, `houseprice_etl_test_experimentation_houseprice_etl` the only
  workflow named after the project, the Glue job *"Job not found"*. The two workflows' log groups under
  `/aws/mwaa-serverless/` stay, under `EXC-10`'s rule.
- **[user] §N.8.2 step 15, a GitLab backup by hand** in a Session Manager shell on `awsds-prod-gitlab`: `sudo
  gitlab-backup create STRATEGY=copy`, 22:38:00 to 22:38:10 UTC, the eight projects' repositories and wikis
  dumped, *"Uploading backup archive to remote storage awsds-prod-gitlab-backup ... done (encrypted with
  aws:kms)"*, *"Backup 1794782280_2026_11_15_19.4.2 is done."* **[Claude]** read in the bucket as
  `awsds-infra-prod`: `1794782280_2026_11_15_19.4.2_gitlab_backup.tar`, 15,585,280 bytes, 22:38:11, `aws:kms`,
  expiring 2026-12-16 (`expire-current-versions`); release 19.4.2, the pinned one. The two older archives
  (2026-10-26 and 2026-11-10) stay until their own expiry.
- **[Claude] §N.8.2 step 13's run to its end**, as `awsds-infra-sandbox-1`: `bzJIxFT4Hn64Go8` `SUCCESS`, 22:26:25
  to 22:40:03 UTC, 817 s, within pass 1's 816 to 936 s. Its tasks `transform` 111 s, `process` 492 s,
  `summarize` 7 s, `write_result` 23 s and `publish` 6 s, each `SUCCESS`. The Glue run on `app-etl-ceweti7jbiu1hs`
  `SUCCEEDED` from 22:27:04, 85 s, 2 G.1X workers. The processing job `app-etl-20261115T222936` `Completed`,
  22:30:22 to 22:34:52, `ml.t3.medium`, network-isolated, on `awsds-prod-ecr-app-etl@sha256:14ae4d03…6126`, the
  digest `v0.4.7`'s `build-image` pushed. The report `shared/app-etl/outbox/report.json`, 332 bytes, at
  22:39:22. `app_etl.trades_notional`'s metadata moved to `00001-8dfc9699-….metadata.json` at 22:28:31: the run
  wrote the table the run of 2026-11-14 created. Step 13 done.
- **[user] Sandbox down** (§N.8.2 step 16's Sandbox half, taken early): `git credential-cache exit` in the space,
  the persona's token revoked, the space deleted, the portal's tabs closed, `make down ENV=sandbox`. **[Claude]**
  read at 22:55 UTC: no app and no space in Sandbox, its two gateway endpoints (S3, DynamoDB) alone,
  `sandbox/egress` down.
- **[user] §N.8.2 step 12b** (Stage 8's log, xv): the proxy stopped at 22:48:05 and started at 22:50:14, *Retry*
  on `staging-check` of #120 failing in 25 s on the FATAL line, then green.
- **[user] `make down ENV=staging`, then `make up ENV=staging`**, for release F's sitting (§N.8.4), which needs
  Staging's `orchestration/` and `app/app-etl/` destroyed. **[Claude]** `make status` at 22:55: `staging/egress`
  up with 17 resources, both slices down, each `state list` empty; Production's `workloads-egress/` kept up for
  release F, the burn 0.6171 USD/h.

## 2026-11-15 — release F's promotion sitting: step 5's re-plan

*The same evening, right after release T's sitting, which ended with steps 11 to 15 and 17 done and Production's
`workloads-egress/` kept up. Claude's hand as the infrastructure user with `InfrastructureAccess` in the
Staging Account (`awsds-infra-staging`). Times UTC.*

- **[Claude] §N.8.4 step 5, `staging/chains/` re-planned** at 22:57 into
  `$HOME/tmp/stage19-chains-staging-1115.tfplan`: *"18 to add, 0 to change, 0 to destroy"*, the module at
  `orchestration-v0.3.0`; the two chains `awsds-staging-chain-app-etl` (`cron(30 6 * * ? *)`) and
  `awsds-staging-chain-app-etl-train` (`cron(0 7 * * ? *)`), both schedules `DISABLED`, their failure rules and
  the workflows' failure rules `ENABLED`, the schedule group `awsds-staging-chains`, the log group
  `/aws/vendedlogs/states/awsds-staging-chains`, the exec and scheduler roles. The apply waits for the user's
  word naming it.
- **[Claude] The times of the two bullets above, corrected**: `make status` ended at 23:07:19 UTC (not 22:55),
  and the plan was saved at 23:08:34 (not 22:57), read from the files' modification times.
- **[Claude⚡] §N.8.4 step 5, `staging/chains/` applied** on the user's word in chat (*"Sim, aplique o chains"*),
  the other sessions told first, as `awsds-infra-staging`: the saved plan of 23:08:34, 23:11:18 to 23:11:44 UTC,
  *"18 added, 0 changed, 0 destroyed"*. The re-plan *"No changes"*, exit 0 under `-detailed-exitcode`. Read
  back: `awsds-staging-chain-app-etl` and `awsds-staging-chain-app-etl-train` created at 23:11:39, both
  schedules in `awsds-staging-chains` `DISABLED`, the two chain failure rules and the two workflow failure rules
  `ENABLED`.
- **[user] §N.8.4 step 6, the template's merge request**: branch `release-f`, commit `cdf9078` on `355ab8c`, from
  `3a15f2f6:examples/app-etl`; merge request !14, its branch pipeline #121 green (`test`, `pip-audit`,
  `secret_detection`, `secret-detection-gate`), merged at 23:12:33 UTC as `fc79a4d`. **[Claude] read**: the
  branch's tree and `main`'s are `22a98d0e…`, the tree of `3a15f2f6:examples/app-etl`. The mirror
  `awsds/infrastructure` was already at `3a15f2f6`. `git ls-remote` reads `v0.4.9` and `v0.5.*` free.
- **[user] The tag `v0.5.0`** on `fc79a4d`, pushed at 23:14:45 UTC: pipeline #123. **[pipeline]** `test` and
  `pip-audit` green at 23:15:03, `build-task-code` at 23:15:16, `build-image` at 23:17:51, `bundle` at 23:18:16,
  `store-bundle` at 23:18:25, `release` at 23:18:34; `staging-gate` `manual`. **[Claude] read** in `bundle`'s
  log: *"Bundle creation complete for target: dev"*, 12 files, then the guard *"the catalog the bundle carries,
  against product.json"*: glossaries 0, glossary terms 0, form types 0, asset types 0, *"assets: 1
  (trades_notional)"*, *"dataProducts: 1 (trades-notional)"*, *"OK"*; the bundle's SHA256 `1148ff0c…2b46`.
- **[user] `staging-gate`** of #123 (job 750, 23:18:55 to 23:19:00). **[pipeline]** `staging-check` (751) green,
  23:19:01 to 23:19:22; `staging-deploy` (752) failed, 23:19:25 to 23:21:20; `staging-test` and every later job
  skipped. `scan-gate` (746) failed at 23:23:56, allowed to (Stage 8 decision 1): *"Number of vulnerabilities for
  this image exceeds the maximum supported with Basic Scanning"*, the ending of #117's and #120's too.
- **[Claude] `staging-deploy` read** in its log: the CLI deployed into `deploy-staging` (`5ido8bej1zoeq8`), five
  storage items with 11 files under the project's shared prefix, the workflows `app_etl_deploy_staging_app_etl`
  (23:21:02) and `app_etl_deploy_staging_app_etl_train` (23:21:15) created `READY`, *"Deployment completed
  successfully!"*, exit 0. The catalog import: *"Remapped DataSourceReferenceForm to target data source
  52f18khk7kdi4w (db app_etl)"*, *"Resource trades_notional already exists (ConflictException), treating as
  update"*, then *"Failed to import dataProducts trades-notional: An error occurred (ValidationException) when
  calling the CreateDataProduct operation: Resource asset provided is not from same project"*; the summary
  *"0 created, 1 updated, 0 skipped (extra in target), 1 failed, 0 published"*. `deploy-application.py` stopped
  on *"the catalog import failed 1 item(s)"* (`SUP-357`'s check), before the stage's variables: no
  `/awsds/staging/applications/app-etl/stage-variables`, no `staging.env`.
- **[Claude] The cause read** in the Data Governance account's trail as `awsds-infra-data`: `CreateAsset` at
  23:20:49 into `deploy-staging` with `app-etl-dev`'s `externalIdentifier`, the Sandbox account's table ARN with
  `app-etl-dev`'s project id as suffix, answered `ConflictException` with no message; `CreateDataProduct` at
  23:20:50 with the item `c6z3pbg3drrs0g`, `app-etl-dev`'s asset (1.5), answered `ValidationException`. That
  `CreateAsset` is the only one into `deploy-staging` since 2026-11-09. Its source `52f18khk7kdi4w`, over Staging's
  `app_etl`, has run daily since 2026-11-12 adding 0, and Staging's `app_etl` holds no table. `Search` and
  `GetAsset` in the deploy projects are refused to the infrastructure user, not a member. The CLI's
  `_import_resource` records no target id on a conflict: `SUP-369`. xvii's premise does not hold: the import
  creates no asset in a target, whose asset can only come from its own source after a run writes the table.
- **[Claude] Staging after the job**, read 23:33: the two workflows `READY`, no stage-variables record, the chains'
  schedules `DISABLED`; `staging/orchestration` and `staging/app/app-etl` empty by `state list`, exit 0. Production
  untouched, on release T's `v0.4.7`. A retry of `staging-deploy` meets the same conflict while `deploy-staging`
  holds no asset of its own.
- **[Claude] Decision 25 written**, the user's: how a target's first import gets its asset.
- **[user] Decision 25**, verbatim: *"Sobre a Decisão 25, sigo a recomendação (b)."* **[Claude]** recorded in the
  stage file, with what (b) writes: the admitted case and the follow-up in `deploy-application.py`, the
  template's `staging-catalog` and `production-catalog`, the source's start in both `foundation/` slices, and
  `CT-13` judging a deploy role's start; the release `v0.5.1`.
- **[Claude] Decision 25 (b) written**, every call a read:
  - `scripts/deploy-application.py`: `read_log` admits a target's first import alone, every failed item a data
    product refused *"Resource asset provided is not from same project"* beside the asset's
    `ConflictException` line, and the dotenv carries `<PREFIX>_CATALOG_PENDING`; `--catalog-follow-up` starts
    the project's Glue source over `PRODUCT_DATABASE` (bound 900 s), waits for the bundle's assets in the
    project's search (bound 300 s) and deploys again, admitting nothing. `--self-check` passes ten log samples;
    job 752's lines, rebuilt, read admitted with `admit` and failed without.
  - `examples/app-etl/.gitlab-ci.yml`: `staging-catalog` after `staging-test`, needed by `production-check` and
    `production-gate`; `production-catalog` after `production-deploy`, 90 min. Each ends at once when its
    variable is not `true`.
  - Both `foundation/` slices: the deploy role's `StartTheProjectsSourceBeforeTheSecondImport`
    (`datazone:StartDataSourceRun`, `datazone:GetDataSourceRun`). Planned as the infrastructure user into
    `$HOME/tmp/stage19-d25-<env>-foundation.tfplan`: *"0 to add, 1 to change, 0 to destroy"* in each, the
    statement alone, the rendered policy 4,734 characters in Staging and 4,719 in Production. The roles read
    `awsds-deploy-staging` and `awsds-deploy-prod` in IAM.
  - `aws/catalog.py`: `CT-13` judges a deploy role's start as its deployment project's; `--self-check` 39 of 39.
  - `promotion.md` §N.8.4 step 6 carries `v0.5.1`'s order, `threat-model.md`'s `TM-29` the deploy roles.
- **[Claude⚡] Decision 25's grants, both `foundation/` slices applied** on the user's word in chat (*"Sim, aplique
  os foundation"*), the three other sessions told first, as the infrastructure user (`InfrastructureAccess`), on
  2026-11-16: Staging Account (`awsds-infra-staging`) 00:00:09 to 00:00:22 UTC, Production (`awsds-infra-prod`)
  00:00:29 to 00:00:41, each the saved plan, *"0 added, 1 changed, 0 destroyed"*. The re-plans *"No changes"*,
  exit 0 under `-detailed-exitcode`; IAM reads `awsds-staging-deploy-project` and `awsds-prod-deploy-project` at
  `v3`, each with `StartTheProjectsSourceBeforeTheSecondImport` granting `datazone:StartDataSourceRun` and
  `datazone:GetDataSourceRun`.
- **[user] §N.8.4 step 6.2**: PR #304 merged at 00:06:17 UTC on 2026-11-16 as `f9c3ab49`, then the mirror pushed.
  **[Claude] read**: GitLab's `awsds/infrastructure` `main` at `f9c3ab49`; `awsds/app-etl`'s `main` at `fc79a4d`, no
  merge request open, the tags to `v0.5.0`. `git diff 3a15f2f6 f9c3ab49 -- examples/app-etl` is one file,
  `.gitlab-ci.yml`, 52 insertions and 3 deletions. The rest of the sitting is recorded from the branch
  `claude/release-f-v051`, cut from `f9c3ab49`.
- **[user] §N.8.4 step 6.3, the template's merge request**: branch `release-f-catalog`, commit `0dd51d7e` on
  `fc79a4db`, from `f9c3ab49:examples/app-etl`; merge request !15, its branch pipeline #124 green (`test`,
  `pip-audit`, `secret_detection`, `secret-detection-gate`), merged at 00:10:25 UTC as `451d0ae2`, `main`'s
  pipeline #125 green. **[Claude] read**: the branch's root tree and `main`'s entry for entry those of
  `f9c3ab49:examples/app-etl`; `fc79a4db` to `451d0ae2` changes `.gitlab-ci.yml` alone; the tags to `v0.5.0`.
  `staging/egress` and `production/workloads-egress` up by `state list`, the hub's two hosts and GitLab running.
- **[user] §N.8.4 step 6.4, the tag `v0.5.1`** on `451d0ae2`: pipeline #126, created 00:13:41 UTC, `staging-catalog`
  (786) and `production-catalog` (791) among its jobs. **[pipeline]** `test` and `pip-audit` green at 00:13:58.
- **[user] `staging-gate`** of #126 (job 782, 00:20:00 to 00:20:05). **[pipeline]** `build-image` 00:13:59 to 00:16:44;
  `bundle` green at 00:17:11, the guard *"assets: 1 (trades_notional)"*, *"dataProducts: 1 (trades-notional)"*, *"OK"*;
  `release` at 00:17:27; `staging-check` (783) green, 00:20:11 to 00:20:33; `staging-deploy` (784) failed, 00:20:36
  to 00:22:39.
- **[Claude] `staging-deploy` read**: the CLI deployed, the import read as on 2026-11-15 (*"0 created, 1 updated, 0
  skipped (extra in target), 1 failed, 0 published"*), the two workflows found, and the script admitted it: *"the
  catalog's first import in this project (SUP-369): the data product waits for the project's own asset"*. Then
  *"deploy-application: aws ssm put-parameter: … AccessDeniedException … No access to reserved parameter name:
  awsds/staging/applications/app-etl/stage-variables"*: Parameter Store reserves every name beginning with `aws`
  (`SUP-067`, `conventions.md`'s `/datascience/<env>/…`), and release F's parameter, written 2026-11-12, began with
  `/awsds/`. No `staging.env`; `staging-test` and later skipped.
- **[Claude] The parameter moved to `/datascience/<env>/applications/<app>/stage-variables`** (Recipe B):
  `terraform-modules/orchestration` in `5765f562`, tagged `orchestration-v0.3.1` and read on origin at that
  commit; both `chains/` slices pinned to it; both `foundation/` slices' `ssm` resource; `tfhygiene/projects.py`'s
  `stage_variables_parameter`. `deploy-application.py --self-check` OK. Planned as the infrastructure user:
  `staging/foundation` and `production/foundation` *"0 to add, 1 to change"*, the `ssm` statement's resource alone;
  `staging/chains` *"0 to add, 3 to change"*, both machines' parameter name and the chain role's `ssm` resource;
  `production/chains` *"24 to add"* with the new name, for step 8. `SUP-067` carries the reading.
- **[Claude⚡] The parameter's three applies** on the user's word in chat (*"Sim, aplique os três"*, answering the
  question naming `staging/foundation`, `production/foundation` and `staging/chains`), the three other sessions
  told first, as the infrastructure user (`InfrastructureAccess`): `staging/foundation` 00:36:22 to 00:36:35 UTC and
  `production/foundation` 00:36:35 to 00:36:47, *"0 added, 1 changed, 0 destroyed"* each; `staging/chains`
  00:36:47 to 00:36:59, *"0 added, 3 changed, 0 destroyed"*. The three re-plans *"No changes"*, exit 0 under
  `-detailed-exitcode`; both Staging machines' definitions read `/datascience/staging/applications/app-etl/stage-variables`.
- **[user] PR #305 merged** at 00:40:01 UTC as `a45e3703`, then the mirror pushed. **[Claude] read**: GitLab's
  `awsds/infrastructure` `main` at `a45e3703`. The rest of the sitting is recorded from the branch
  `claude/release-f-staging-leg`, cut from `a45e3703`.
- **[user] `staging-deploy` retried** in #126: job 796, 00:40:39 to 00:42:39, green. **[Claude] read** in its log:
  *"awsds/infrastructure at a45e370374864b9fab4fa0babed41ddcda5833e9"*, *"bundle.zip: OK"*, *"the bundle of v0.5.1:
  12 file(s), a catalog export"*; the import as in job 784 (the reference remapped to the source `52f18khk7kdi4w`,
  *"Resource trades_notional already exists (ConflictException), treating as update"*, *"0 created, 1 updated, 0
  skipped (extra in target), 1 failed, 0 published"*) and the script's admission; then *"the stage's variables
  recorded in /datascience/staging/applications/app-etl/stage-variables: ACCOUNT_ID, JOB_IMAGE_URI,
  PRODUCT_DATABASE, PROJECT_KEY_ARN, PROJECT_SG, PUBLISH_LISTING, SUBNET_AZ1, SUBNET_AZ2, TRAINING_IMAGE_URI"*. The
  job's artifacts: `staging-deploy.log` and the dotenv report. The parameter read as `awsds-infra-staging`:
  `String`, version 1, modified 00:42:34 UTC. `staging-test` (785) started at 00:42:42.
- **[pipeline] `staging-test`** (785), 00:42:42 to 01:01:24 UTC, failed: *"00:58:12 app-etl SUCCEEDED"*,
  *"01:01:18 app-etl-train FAILED"*, *"FATAL: the chain app-etl-train ended FAILED"*. `staging-catalog` (786)
  and `staging-model` (787) skipped; the job's reads of the report and the product table did not run.
- **[Claude] The `app-etl` chain read** as `awsds-infra-staging`: execution `v0-5-1-126-app-etl`, 00:42:51 to
  00:57:55 UTC, `SUCCEEDED`; one `listWorkflows`, one `getParameter` of
  `/datascience/staging/applications/app-etl/stage-variables`, one `startWorkflowRun` on
  `app_etl_deploy_staging_app_etl` with the nine variables as `OverrideParameters`, fifteen `getWorkflowRun`.
  xxix reads yes for this chain in Staging.
- **[Claude] The `app-etl-train` chain's cause read**: execution `v0-5-1-126-app-etl-train`, 00:58:14 to
  01:01:16 UTC, *"WorkflowRunNotSucceeded"*; run `W373uHP9ZB5EvsW` of `app_etl_deploy_staging_app_etl_train`,
  00:58:24 to 00:59:22, `FAILED`: task `train` (`SageMakerTrainingOperator`) `FAILED` after 15 s, `evaluate`
  `UPSTREAM_FAILED`. The task's log, in
  `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-5ido8bej1zoeq8/app_etl_deploy_staging_app_etl_train`: the config
  rendered with the stage's variables, then *"AccessDeniedException … User: …:assumed-role/
  datazone_usr_role_5ido8bej1zoeq8_d6nu5aphq1e974/AmazonMWAAServerless is not authorized to perform:
  sagemaker:DescribeTrainingJob on resource: …:training-job/app-etl-train-20261116T005914 because no
  identity-based policy allows the sagemaker:DescribeTrainingJob action"*.
  `SageMakerStudioProjectRoleMachineLearningPolicy` v48 grants `DescribeTrainingJob`
  (`SageMakerDescribeUpdateDeletePermissions`) only when `aws:ResourceTag/AmazonDataZoneProject` equals the
  caller's, and a free name carries no tag: `SUP-267`'s processing case, for training. The role carries
  `awsds-staging-workflows` v1 with the processing and Glue statements alone; the project boundary allows the
  create under the conditions the workflow sets; the role is tagged `EnableSageMakerMLWorkloadsPermissions`
  `true`. The train workflow had never run under a project role: release T trained under the application
  role, and `app-etl-dev`, `eighth-experimentation` and `test-experimentation` created it with no run.
- **[Claude] A retry of `staging-test` cannot pass**: the job names each execution
  `$CI_COMMIT_TAG-$CI_PIPELINE_ID-<chain>`, and `StartExecution` answers `400 ExecutionAlreadyExists` for a
  closed execution's name, reusable 90 days after the close (the API reference, read the same night);
  `v0-5-1-126-app-etl` is closed. A tag never moves, so the template's change takes the tag `v0.5.2`.
- **[Claude] The fix written**:
  - both `studio/workflows.tf` copies gain `DescribeATrainingJobNoProjectHolds` and
    `TagATrainingJobWithTheCallersProject`, the processing pair's conditions on `training-job/*`; the
    description names training, so the policy is replaced;
  - the template's `staging-test` names its executions `$CI_COMMIT_TAG-$CI_JOB_ID-<chain>`;
  - simulated as the project role with `simulate-principal-policy`, the context `aws:RequestedRegion`,
    `aws:PrincipalArn` and the two principal tags (without `aws:RequestedRegion` the simulator answered
    `explicitDeny`, `AllowedByOrganizations` false): `DescribeTrainingJob` on a free name `implicitDeny`,
    `allowed` with the two statements, on another project's job `implicitDeny` with them; `AddTags` of the
    own project tag `implicitDeny`, `allowed` with them, of another project's `implicitDeny`.
    `CreateTrainingJob`, `PassRole` and the S3 calls are undecided by the simulator without the SMUS
    principal tags; the `app-etl` run passed the same role to its processing jobs under the same prefix;
  - planned as the infrastructure user: `staging/studio` and `production/studio` *"2 to add, 0 to change, 2
    to destroy"* each, the policy and its one attachment replaced, each policy at `AttachmentCount` 1;
    saved as `$HOME/tmp/stage19-training-<env>-studio.tfplan`.
- **[Claude⚡] Both `studio/` slices applied** on the user's word in chat (*"Sim, aplique os studio"*, answering
  the question naming `staging/studio` and `production/studio`), the three other sessions told first, as the
  infrastructure user (`InfrastructureAccess`), from the saved plans: `staging/studio` 01:20:29 to 01:20:43 UTC
  and `production/studio` 01:20:51 to 01:21:09, *"2 added, 0 changed, 2 destroyed"* each, the attachment and
  the policy destroyed and created in that order. Both re-plans *"No changes"*, exit 0 under
  `-detailed-exitcode`. `awsds-staging-workflows` v1, created 01:20:40, five statements;
  `awsds-prod-workflows` v1, created 01:21:06, six; each at `AttachmentCount` 1, on its deployment project's
  role. Simulated again against the applied policy, with the context above: `DescribeTrainingJob` on a free
  name and `AddTags` of the own project tag `allowed` by `awsds-staging-workflows`; another project's job and
  tag `implicitDeny`.
- **[user] §N.8.4 steps 6.5 and 6.6**: PR #306 merged at 01:25:26 UTC as `ced09fe4`, then the mirror pushed; the
  template's merge request !16, branch `release-f-execution-names`, its branch pipeline #127 green, merged at
  01:27:00 as `07348ffa`; the tag `v0.5.2` on `07348ffa`, pipeline #129, created 01:27:47. **[Claude] read**:
  GitLab's `awsds/infrastructure` `main` at `ced09fe4`; the tag's tree and `ced09fe4:examples/app-etl` the
  same 28 blobs (the SHA-256 of their sorted path and blob lists equal), `.gitlab-ci.yml` at `f8ddc5fe`. The
  rest of the sitting is recorded from the branch `claude/release-f-v052`, cut from `ced09fe4`.
  **[pipeline]** `pip-audit` and `test` green at 01:28:05, `build-task-code` at 01:28:15.
  `build-image` 01:28:08 to 01:30:51; `bundle` green at 01:31:17, the guard *"assets: 1 (trades_notional)"*,
  *"dataProducts: 1 (trades-notional)"*, *"OK"*; `store-bundle` at 01:31:26, `release` at 01:31:36;
  `staging-gate` (817) manual.
- **[Claude] Staging before the gate**: `deploy-staging`'s source `52f18khk7kdi4w` (`cron(28 15 * * ? *)`,
  `ENABLED`) read as `awsds-infra-data`, its four last runs `SCHEDULED`, `SUCCESS`, each *"added":0*, the
  latest at 15:37:23 on 2026-11-15, so the project holds no asset of its own; `datazone search` in the
  project refused to the same identity, a non-member (*"User is not permitted to perform operation:
  Search"*). The product table `app_etl.trades_notional` read as `awsds-infra-staging`: `ICEBERG`, registered
  with Lake Formation, created 00:45:42 UTC by `v0.5.1`'s `app-etl` run.
- **[user] `staging-gate`** of #129 (job 817, 01:39:54 to 01:39:58). **[pipeline]** `staging-check` (818) green,
  01:40:02 to 01:40:24; `staging-deploy` (819) green, 01:40:27 to 01:42:31. **[Claude] read** in its log:
  *"awsds/infrastructure at ced09fe41d6c97600d889488e0c8d9fa101c11aa"*, *"the bundle of v0.5.2: 12 file(s), a
  catalog export"*, *"0 created, 1 updated, 0 skipped (extra in target), 1 failed, 0 published"*, the
  *"Tooling VPC config"* line, both workflows *"already exists, updating it"* with the project role,
  *"Deployment completed successfully!"*, the first import's admission (`SUP-369`) and the nine variables
  recorded; the parameter at version 2, modified 01:42:27 UTC.
- **[Claude] The sitting's readings of the platform and its lessons**, written while `staging-test` ran, at
  the user's request (*"revise as lições aprendidas com esta sessão, e ao AWS_SUPPLEMENT"*):
  - the AWS CLI 2.37.12 passed a `file://` document to `--policy-input-list` one member per character,
    *"Value '[{, ", V, e, r, s, i, …]' at 'policyInputList' failed to satisfy constraint: Member must have
    length less than or equal to 10"*, on one line or several, and read the same document passed as the
    argument's text, `PolicyInputList.1` (`SUP-370`);
  - the chain machines' `getWorkflowRun` polls of `v0.5.1`'s runs, read from the two executions' histories,
    lagged the runs: `app-etl`'s `StartedOn` of 00:43:14 first appeared at 00:45:53, and `app-etl-train`'s
    run, 00:58:24 to 00:59:22, never read `RUNNING` (`SUP-273`'s later reading);
  - a non-member's reads of `deploy-staging`, above, joined `SUP-157`;
  - Lessons 82 (a refusal diagnosed as a shape and granted as a list), 83 (a retry reuses the names the first
    attempt spent) and 84 (the laptop's shell is zsh) written, and the parameter's name added to Lesson 5 as
    a naming rule nothing checked. Already recorded and not repeated: the simulator's Region and principal
    tags (`SUP-008`), the run state's lag (`SUP-273`), a non-member's catalog (`SUP-157`).
- **[pipeline] `staging-test`** of #129 (job 820) green, 01:42:35 to 02:07:27. **[Claude] read** in its log
  and in Staging: the chain execution `v0-5-2-820-app-etl` `SUCCEEDED`, 01:42:44 to 01:59:49 UTC, then
  `v0-5-2-820-app-etl-train`, 02:00:10 to 02:07:12; the run's report, *"rows": 10*, from `trades.csv`; the
  product table `trades_notional`, `ICEBERG`, registered, its metadata at `00001-…`. The training job
  `app-etl-train-20261116T020100` `Completed`, created 02:01:02, ended 02:03:46: the training pair's first
  pass, which does not separate whether the create needs `AddTags` (`SUP-267`).
- **[pipeline] `staging-catalog`** (821) green, 02:07:30 to 02:10:06, the first `--catalog-follow-up`.
  **[Claude] read** in its log: *"the project's source 52f18khk7kdi4w started: run cntcrgrt3c22og"*,
  *"SUCCESS: {"added": 1, "failed": 0, "unchanged": 0, "updated": 0}"*, *"the project holds
  trades_notional"*; the second deploy's import, *"Remapped DataSourceReferenceForm to target data source
  52f18khk7kdi4w (db_app_etl)"*, *"Resource trades-notional already exists (ConflictException), treating
  as update"*, *"0 created, 2 updated, 0 skipped (extra in target), 0 failed, 0 published"*; both workflows
  created, *"Deployment completed successfully!"*, and the stage's variables recorded. In the domain's
  CloudTrail, as `awsds-infra-data`: `StartDataSourceRun` at 02:07:53 UTC; a `CreateAsset` at 02:07:56,
  during the source's run; `CreateAssetRevision` on `as6m73yp8shr80` at 02:09:30, revision 2, and no
  `CreateAsset` from the import; `CreateDataProduct` in `deploy-staging` at 02:09:30 over
  `as6m73yp8shr80`, `ConflictException`, *"Conflict with dataProduct 5070mjwdvjwp3k"*. That product is
  `app-etl-dev`'s (`ceweti7jbiu1hs`), created 2026-11-15 03:14:56 UTC over `c6z3pbg3drrs0g`.
  `deploy-staging`'s four earlier `CreateDataProduct`, 23:20:50 to 01:41:54, each read *"Resource asset
  provided is not from same project"*, and the domain's other `trades-notional`, `bvs7m8z4h6w70w`, was
  deleted 2026-11-14 23:10:01. `GetDataProduct` refused to the same identity, a non-member. The API
  reference's and boto3's `CreateDataProduct` pages state a data product's name unique within the domain.
  The import mapped the asset by name (`SUP-369`'s later reading) and creates the data product in no
  target while `app-etl-dev` holds it, so decision 20's two data products cannot exist; decision 26
  written, due.
- **[pipeline] `staging-model`** (822) green, 02:10:09 to 02:16:33. **[Claude] read** xxxi: the batch
  transform `app-etl-v0-5-2-20261116T021037` `Completed` at 02:16:28 on the model of
  `app-etl-train-20261116T020100`, 10 predictions for 10 rows, the model deleted after. In Staging's
  CloudTrail: `CreateModel` at 02:10:39 by `awsds-deploy-staging`, the project role its execution role,
  in the project's two subnets and security group with network isolation, the model data under the
  project's `shared/` prefix; `CreateTransformJob` at 02:10:41 by the same role, input and output under
  that prefix, the output with the project's key `c6556c49-…`.
- **[pipeline] `production-check`** (823) failed, 02:16:36 to 02:16:54, on the membership, as step 7
  expects: *"the caller is no member of deploy-production: DataZone refuses it the project's
  connections"*. **[Claude] read** the group profile as `awsds-infra-data`:
  `c332eee6-eabe-33d0-b329-e6b85b4fcacd`, `ASSIGNED`, its `rolePrincipalArn` Production's
  `awsds-deploy-prod`. `make status ENV=production`: `workloads-egress` UP, 17 resources; release T's
  `orchestration/` (41) and `app/app-etl/` (3) UP.
- **[user] Decision 26 taken as (b)** (*"Sigo a (b)"*).
- **[user] `awsds-deploy-prod`'s membership**, account Production, as `awsds-infra-prod`, its output empty:

  ```
  NO_PROXY='*' aws datazone create-project-membership --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier d7qcazihvr3s7k --designation PROJECT_OWNER --member groupIdentifier=c332eee6-eabe-33d0-b329-e6b85b4fcacd --profile awsds-infra-prod --region us-west-2
  ```

  **[Claude] read** `deploy-production`'s memberships at 02:29:32 UTC: `PROJECT_OWNER` `c332eee6-…` beside
  the `PROJECT_OWNER` and the `PROJECT_CONTRIBUTOR` it held before.
- **[user] `production-check`'s retry** (job 831) green, 02:28:54 to 02:29:12: *"the caller is a member of
  the project"*. **[user] `production-gate`** (824) released at 02:29:55.
- **[pipeline] `production-deploy`** (825) green, 02:30:03 to 02:48:31 UTC: `production/workloads-egress/`
  read; *"the bundle of v0.5.2: 12 file(s), a catalog export"*; the import *"Resource trades_notional
  already exists (ConflictException), treating as update"* and *"Failed to import dataProducts
  trades-notional: … Resource asset provided is not from same project"*, `Created: 0`, `Updated: 1`,
  `Failed: 1`, admitted as the first import (*"the catalog's first import in this project
  (SUP-369)"*); the three workflows created; the stage's variables recorded in
  `/datascience/prod/applications/app-etl/stage-variables`. The bootstrap ran `app-etl`, run
  `dgLMl16T1snuRmT`, `SUCCESS` from 02:32:18 to 02:46:30: `transform` 130 s, `process` 493 s,
  `summarize` 10 s (10 rows, notional 49850.5), `write_result` 7 s, `publish` 21 s. `publish` ran the
  source `5zggi2lr2ezy4w` (run `anhgrpgqahg9e8`) and listed the asset `da1fycta6l71n4` at revision 1:
  *"listing 5hpftif3nnoj2o revision 2: ACTIVE, asset revision 1"*. The job followed the run to its end
  and ended 2 min after it (xxviii's follow half).
- **[pipeline] `production-catalog`** (826) started 02:48:34: *"the second import of v0.5.2 into
  deploy-production: trades_notional"*, the source's run `dk1lm51c3amxw0` started at 02:49:03, *"the
  project holds trades_notional"* at 02:49:22; the deploy's import *"Resource trades-notional already
  exists (ConflictException), treating as update"*, *"0 created, 2 updated, 0 skipped (extra in
  target), 0 failed, 0 published"*; the bootstrap's second run of `app-etl`, `RvUWg0Ij7xMyCT4`. The
  CLI's 14 warnings *"Failed to get group profile … AccessDeniedException"* match `staging-catalog`'s 14.
  The second run, `RvUWg0Ij7xMyCT4`, `SUCCESS` from 02:51:33 to about 03:07:40: `transform` 114 s,
  `process` 490 s, `summarize` 9 s, `write_result` 11 s, then `publish`. The job ended green at
  03:07:46 with the three workflows found and the stage's variables recorded again; its log carries
  none of the run's task lines, which `production-deploy`'s did. **[Claude] read** as `awsds-infra-prod`
  at 03:10 UTC: the listing `5hpftif3nnoj2o` `ACTIVE` at revision 4, updated 03:05:21, carrying the asset
  `da1fycta6l71n4` at revision 3 with `classification` among its forms; the asset owned by
  `deploy-production`, its description `dev`'s (*"Notional of each trade, quantity times price rounded to
  cents, written by app-et…"*). `make status` at 03:06: a burn of 0.6171 USD/h, `staging/egress/` still
  up (17), Production's hub, GitLab, the runners and `workloads-egress/` up, release T's
  `orchestration/` (41) and `app/app-etl/` (3) up.
- **[Claude] step 8's plans**, as `awsds-infra-prod`, saved under `$HOME/tmp/`:
  `production/orchestration/` destroy *"0 to add, 0 to change, 41 to destroy"*
  (`stage19-f-production-orchestration-destroy.tfplan`); `production/app/app-etl/` destroy *"0 to add,
  0 to change, 3 to destroy"* (`stage19-f-production-app-destroy.tfplan`): the Glue jobs
  `awsds-prod-app-etl` and `awsds-prod-app-etl-load` and the table `app_outputs.trades_notional` on
  `awsds-prod-outputs`, not the project's `app_etl.trades_notional`; `production/chains/` *"24 to add, 0
  to change, 0 to destroy"* (`stage19-f-production-chains.tfplan`), the machines
  `awsds-prod-chain-<chain>` and the three schedules `DISABLED`.
- **[Claude] Release G written** (decision 26 (b)), with every call a read and nothing applied: the
  `publish` task's data product, the workflow's `data_product` arguments, `product.json` requiring the
  asset alone, the grant `CreateTheProductsDataProductInTheProjectsDomain` in both `studio/` slices
  under `publishing_creates_the_data_product`, and `deploy-application.py` reading a first import on the
  conflict over an asset of the bundle's. Read: `SageMakerStudioProjectRoleMachineLearningPolicy` v48
  grants `datazone:Get*`, `Search*`, `CreateAsset*` and `CreateListingChangeSet`, and
  `SageMakerStudioProjectUserRolePolicy` v77 `*Compute*` alone, neither a data product's creation; the
  role's boundary `awsds-prod-project-boundary` v3 and the `Workloads` SCPs deny neither action; the
  Service Reference `v1.5` gives `CreateDataProduct`, `CreateDataProductRevision` and
  `StartDataSourceRun` no resource type and no condition key. Planned as `awsds-infra-prod`:
  `production/studio/` *"2 to add, 0 to change, 2 to destroy"*, `awsds-prod-workflows` and its
  attachment replaced on the description, the six statements unchanged and the seventh added;
  `staging/studio/` as `awsds-infra-staging`, *"No changes"*. `--self-check` passes with four samples
  more, and pipeline #129's `staging-deploy` and `staging-catalog` lines read as before: a first import
  admitted, a second with nothing pending.
- **[user] Step 8 authorized** (*"Autorizo o passo 8"*): the two destroys, `production/chains/`'s apply
  and the `app-etl` chain started by hand. The three peer sessions on the laptop were told first.
- **[Claude] Step 8's applies**, as the infrastructure user with `InfrastructureAccess` in Production
  (`awsds-infra-prod`), each from its saved plan: `production/orchestration/` 03:15:01 to 03:17:22 UTC,
  *"0 added, 0 changed, 41 destroyed"*: release T's three workflows `awsds-prod-wf-*`, their roles and
  security group `awsds-prod-wf-workers` (no network interface held it, and no other group referenced
  it), the machines, schedules and roles `awsds-prod-chain-*`; `production/app/app-etl/` 03:17:31 to
  03:17:41, *"0 added, 0 changed, 3 destroyed"*; `production/chains/` 03:17:55 to 03:18:20, *"24 added,
  0 changed, 0 destroyed"*, re-planning `No changes`.
- **[Claude] xxix's chain started by hand** at 03:19:10: `awsds-prod-chain-app-etl`, execution
  `step8-xxix-20261116T031909-app-etl`, the machine's first. A first attempt was refused `InvalidArn`
  before any execution existed: zsh read `$account:stateMachine` as a `:s` modifier (Lesson 84), and
  `${account}` fixed it. The history: `ssm:getParameter` of the stage variables, `listWorkflows`
  finding `app_etl_deploy_production_app_etl-6Hz8jUvCQb`, `startWorkflowRun` with the nine variables as
  `OverrideParameters` (`PUBLISH_LISTING` `true`, `PRODUCT_DATABASE` `app_etl`) answering the run
  `wITFYNHoLyyEsev`, `STARTING`, within 1 s of the start.
- **[user] `make down ENV=staging`**, reported during the chain's run (*"o ambiente staging foi
  derrubado"*). **[Claude] read** at 03:24:28 as `awsds-infra-staging`: the gateway endpoints for S3
  and DynamoDB alone, no interface endpoint, no NAT gateway.
- **[Claude] `./aws/orchestration.py awsds-infra-prod awsds-infra-staging`** after step 8: exit 2, *"13
  CHECK(S) FAILED"*, each a rule written to release T's contracts, which §Release F as written leaves
  to step 8. OR-9, three rows per account: `awsds-<env>-chain-exec` and `-chain-scheduler` with no
  boundary and `awsds-<env>-chain-events` absent, which `terraform-modules/orchestration` writes so by
  design (no role there touches data, and the pipeline creates none). OR-2, five rows and one count
  per account: the groups `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, created with each
  CLI-made workflow (Staging's two at 2026-11-15 23:21, Production's three at 2026-11-16 02:31 to
  02:32) and holding no retention, so D28 item 5's is unmet. The chains, the schedules `DISABLED` and
  the failure rules pass.
- **[Claude] xxix read in Production**: the run `wITFYNHoLyyEsev` `SUCCESS` from 03:19:16 to 03:33:45
  (`transform` 149 s, `process` 490 s, `summarize` 6 s, `write_result` 11 s, `publish` 22 s), and the
  execution `SUCCEEDED` at 03:36:15. Every parameter rendered: the Glue run `jr_d486b7fd3…`
  `SUCCEEDED` with `--TABLE_DATABASE app_etl`, the job's `--conf` carrying a 12-digit
  `spark.glue.accountId` and `transport.domainId=dzd-d8yrvx1ko7im6o`, its connections named after the
  two subnets, and no `{env.`, `{proj.`, `{domain.` or `params.` left in its arguments; the processing
  job `app-etl-20261116T032302` `Completed` on `awsds-prod-ecr-app-etl@sha256:e16283e0…`, in the two
  subnets, its volume under the project's key.
- **[user] The rules' rewrite and decision 27 authorized** (*"Sim, faça aqui"*), answering whether
  Claude rewrites `orchestration.py`'s rules and writes a decision on the log groups' retention.
- **[Claude] What the CLI's workflows carry**, read as `awsds-infra-prod` and `awsds-infra-staging`:
  three workflows in Production and two in Staging, each `<application>_<project>_<workflow>`,
  `READY`, `manual_only`, no cron. `get-workflow` on `app_etl_deploy_production_app_etl` and
  `app_etl_deploy_staging_app_etl`: the role `datazone_usr_role_<project id>_<environment id>`, the log
  group `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-<project id>/<workflow>`, two subnets and one
  security group, the definition in `awsds-<env>-smus-projects` under
  `dzd-d8yrvx1ko7im6o/<project id>/shared/app-etl/workflows/` with no `VersionId`, and
  `CUSTOMER_MANAGED_KEY`. The project role: under `awsds-<env>-project-boundary`, tagged
  `AmazonDataZoneProject` and `AmazonDataZoneDomain`, its trust naming `airflow-serverless.amazonaws.com`
  among eighteen service principals and the role `awsds-prod-smus-provisioning`, carrying `awsds-<env>-workflows`,
  `awsds-<env>-person-session-deny`, in Production `awsds-prod-warehouse-load`, and three AWS managed
  policies.
- **[Claude] The groups with no retention in the targets**, `describe-log-groups`: in Production the
  three workflow groups (02:31:49 to 02:32:13) and `datazone-d7qcazihvr3s7k-dev/error` and `/output`
  (02:33:20, 02:33:49); in Staging the two workflow groups (2026-11-15, 23:21:03 and 23:21:15) and
  `datazone-5ido8bej1zoeq8-dev/error` and `/output` (00:44:12, 00:44:50).
- **[Claude] `aws/orchestration.py` rewritten to the CLI's contracts**: `OR-1` reads every workflow of a
  target and fails one the CLI does not compose for the deployment project; `OR-2` the service's group
  for each workflow and a retention on every `/aws/mwaa-serverless/` group; `OR-3` the project role, its
  boundary, its trust and `<env>/studio/`'s policies, and fails a role named `awsds-<env>-wf-*`; `OR-4` a
  failure rule matching each workflow's ARN; `OR-5` the definition under the project's `shared/` prefix;
  `OR-9` the two chain roles with no managed policy (Lesson 72), the events role and the bridges gone.
- **[Claude] `./aws/orchestration.py awsds-infra-prod awsds-infra-staging`** at 03:57:54Z on the new
  rules: exit 2, *"5 CHECK(S) FAILED"*, each `OR-2`'s retention on one of the five workflow groups, every
  other check passing. `get-workflow`'s `CodeSnapshottedAt` reads null on
  `app_etl_deploy_production_app_etl_warehouse` alone.
- **[Claude] Decision 27 written** (who sets the retention; recommended (b), the deploy, after a
  `logs:PutRetentionPolicy` grant in both `foundation/` slices), `EXC-25` in `docs/AWS_STATE.md` naming
  the five groups, and its row in `waiting-on-the-user.md`. Nothing changed in AWS.
- **[Claude] `make status`** after the commit: `production/warehouse-compute` up, its workgroup
  `awsds-prod-warehouse` `AVAILABLE`, created at 03:45:46 UTC by the infrastructure user's Terraform
  1.16.6 (`CreateWorkgroup` in Production's trail), an apply this session did not run; the hub, GitLab
  with its runners, `egress/` and `workloads-egress/` up; Staging's slices down. Estimated burn 1.9771
  USD/h, 1.44 of it the warehouse's per-query-hour figure.
- **[Claude] The user's question, whether decision 27's recommendation (b) follows what AWS intends.**
  The pages read are in `docs/REFERENCES.md` under decision 27. Production's trail, read at 04:14 UTC:
  `CreateLogGroup` on the three workflow groups at 02:31:49, 02:32:01 and 02:32:13 in the session of
  `awsds-deploy-prod`, `invokedBy airflow-serverless.amazonaws.com`, each with a KMS key and no retention;
  on `datazone-d7qcazihvr3s7k-dev/error` and `/output` at 02:33:20 and 02:33:49 by the project role, with
  no key; the `UpdateWorkflow` calls from 02:50:53 to 02:51:20 naming each existing group in
  `loggingConfiguration.logGroupName`. The CLI 1.0.9's code composes that name for an IAM Identity Center
  domain (`build_idc_log_group_name`) and passes it in both calls: `SUP-254`'s *"passes no LogGroupName"*,
  repeated by `EXC-21`, `EXC-25`, decision 27 and `aws/orchestration.py`, took the group's name for the
  service's default. Corrected in each.
- **[Claude] CloudWatch Logs' account-level retention policy**, read in both targets before 04:28:05 UTC:
  `describe-account-policies --policy-type BOGUS_POLICY` refused with *"Member must satisfy enum value
  set: [DATA_PROTECTION_POLICY, FIELD_INDEX_POLICY, VPC_FLOW_LOGS_POLICY, RETENTION_POLICY,
  SUBSCRIPTION_FILTER_POLICY, TRANSFORMER_POLICY, METRIC_EXTRACTION_POLICY]"*, and `--policy-type
  RETENTION_POLICY` answering `{"accountPolicies": []}` in Production and in Staging. The AWS provider
  6.73.0, in a scratch configuration with no backend: `terraform validate` passes `METRIC_EXTRACTION_POLICY`
  and refuses `RETENTION_POLICY` and `BOGUS_POLICY` alike, *"expected policy_type to be one of
  ["DATA_PROTECTION_POLICY" "SUBSCRIPTION_FILTER_POLICY" "FIELD_INDEX_POLICY" "TRANSFORMER_POLICY"
  "METRIC_EXTRACTION_POLICY"]"*. CloudFormation's `AWS::Logs::AccountPolicy` schema in us-west-2 lists the
  same five types, and so does the AWS CLI 2.37.12's help.
- **[Claude] The targets' groups**, `describe-log-groups` after it: `storedBytes` 0 on the five workflow
  groups and the four DataZone groups, none with a retention; each target's `datazone-<project id>-dev`
  carries 731 days.
- **[Claude] Decision 27 revised**: the premise corrected, (a)'s two unmeasured behaviours answered
  (`SUP-253`, the `UpdateWorkflow` calls, the key policy read in `kms.tf`), option (d) added, the
  account-level retention policy, and the recommendation moved from (b) to (d) once the provider accepts
  the type, with (c) until then. `waiting-on-the-user.md`'s row and `EXC-25` follow. Nothing changed in
  AWS.
- **[user] Decision 27 taken as (d)** (*"Vamos conforme sua recomendação"*). **[Claude]** recorded in the
  stage file and its `Status` row, in `EXC-25` and a pointer in `EXC-10`, in `upstream-releases.md` (a
  `watch` row on the `aws` provider and an item of the next reading) and in `CLAUDE.md`'s row;
  `waiting-on-the-user.md`'s row removed. Nothing changed in AWS.
- **[user] Step 9** (*"Seguir para o passo 9"*), the answer to the session's next step. **[Claude]** the
  preconditions, read at 04:51 UTC as `awsds-infra-prod`: the workgroup `awsds-prod-warehouse`
  `AVAILABLE`, base 4 and max 8 RPU, private; the `redshift-serverless` endpoint `available` with private
  DNS; the machines `awsds-prod-chain-app-etl`, `-train` and `-warehouse`; one project role,
  `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow`. `./aws/warehouse.py awsds-infra-prod --sql`: every
  check passing, `WH-12` *"3 user-role grant(s)"*, no user for the project role. The three peer sessions
  on the laptop were told first.
- **[Claude] The admin's statements**, through `redshift-data` with the namespace's admin secret, in
  `governed`: `CREATE USER "IAMR:datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow" PASSWORD DISABLE
  NOCREATEDB NOCREATEUSER` `FINISHED` at 04:55:10 (20.97 s) and `GRANT ROLE gov_trades_rw TO` the same
  user at 04:55:13 (0.59 s). Read back at 04:56 by `./aws/warehouse.py --sql`: the user in `pg_user`,
  `usesuper` false, holding `gov_trades_rw`; `WH-12` *"4 user-role grant(s)"*. The register row is in
  `docs/AWS_STATE.md`.
- **[user] `production-warehouse-ddl`** of pipeline #129, green: the deploy image
  `awsds-prod-ecr-deploy@sha256:9965f1b2…`, the infrastructure mirror at `ced09fe4`, the
  `CREATE TABLE IF NOT EXISTS` `FINISHED` (`39abcaab-…`) and the count `FINISHED` (`898cdea1-…`),
  *"IAMR:awsds-deploy-prod … 30"*.
- **[Claude] xxxii's chain started by hand** at 05:00:10: `awsds-prod-chain-app-etl-warehouse`,
  execution `step9-xxxii-20261116T050008-app-etl-warehouse`. **[Claude] The project role simulated** at
  05:01 UTC, the worker's case of 2026-11-12 (the Region, the organization, the account and the role's
  tags as context): `redshift-serverless:GetCredentials` and `GetWorkgroup` `allowed` by
  `awsds-prod-warehouse-load`; `redshift-data:ExecuteStatement`, `GetStatementResult` and
  `sqlworkbench:CreateConnection` `explicitDeny` by `awsds-prod-project-boundary`, row for row as then.
- **[Claude] xxxii's chain failed** at 05:05:12 UTC, `WorkflowRunNotSucceeded`: the workflow run
  `hsG55GRjw5rXgzc` `FAILED`, its task `load` failed at 05:03:02 on the Glue job run `jr_028b3ec7a139…`
  (`FAILED`, 05:01:00 to 05:03:01). The job's output log: *"read 10 row(s) from
  glue_catalog.app_etl.trades_notional"*, *"connecting to
  jdbc:redshift://awsds-prod-warehouse.<account>.us-west-2.redshift-serverless.amazonaws.com:5439/governed
  as IAMR:user-project@d7qcazihvr3s7k"*, then *"ERROR: permission denied for schema trades"*. The trail:
  the job created at 05:00:59 by the task's session `AmazonMWAAServerless`; `GetCredentials` and
  `GetWorkgroup` at 05:02:48 by the project role's `GlueJobRunnerSession`, through
  `vpce-0b4195f2018bfbdf1`, no error. The database, read as the admin from 05:06: the user
  `IAMR:user-project@d7qcazihvr3s7k` auto-created, holding no role; its one session, at 05:02:50, ran
  `BEGIN`, a `DELETE FROM trades.trades_notional` refused *"permission denied for schema trades"*, and
  `ROLLBACK`; the table still 30 rows, 2026-10-01 to 2026-10-05.
- **[Claude] The cause**: the project role carries the tag `RedshiftDbUser = user-project@d7qcazihvr3s7k`,
  the tag Stage 18 read on Staging's project role, and the Glue job's session carries no session tag, so
  `GetCredentials` names the database user from the role's own tag. Act 7's `IAMR:<the project role's
  name>` is the name 6h measured through the Data page, where the connection's access role carries that
  value (`SUP-205`, `SUP-206`); Stage 9's log of 2026-10-25 records it as the access role's. The user
  created at 04:55:10 holds `gov_trades_rw` and no session reaches it: Production's project has no
  Redshift connection, so no access role. `gov_trades_rw` holds `USAGE` on `trades` and `SELECT`,
  `INSERT`, `DELETE` on `trades.trades_notional`, owned by `IAMR:awsds-deploy-prod`, so the grant of that
  role to the auto-created user is the fix.
- **[user] The fix's three acts** (*"Autorizo os três atos"*). **[Claude]** the three peer sessions told
  first; as the admin in `governed`: `GRANT ROLE gov_trades_rw TO "IAMR:user-project@d7qcazihvr3s7k"`
  `FINISHED` at 05:18:35 (0.39 s), `REVOKE ROLE gov_trades_rw FROM
  "IAMR:datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow"` at 05:18:37 (0.32 s) and `DROP USER` of the same
  at 05:18:39 (0.20 s). Read back: the dropped user gone from `pg_user`, and `svv_user_grants`
  `IAMR:user-project@d7qcazihvr3s7k` holding `gov_trades_rw`, `admin_option` false.
- **[Claude] xxxii's chain again** at 05:19:12, execution `step9-xxxii-20261116T051910-app-etl-warehouse`
  with the first run's input `{}`: `SUCCEEDED` at 05:24:14, the workflow run `3FYaeVb4I3M12N4` `SUCCESS`.
  The Glue job run `jr_b9dad624951…` `SUCCEEDED`, 05:20:08 to 05:22:39 (126 s), on the job the first run's
  task created; its output log: *"read 10 row(s) from glue_catalog.app_etl.trades_notional"*,
  *"connecting to … as IAMR:user-project@d7qcazihvr3s7k"* and *"trades.trades_notional: 30 row(s)
  deleted, 10 inserted, 10 counted for the load's dates, as IAMR:user-project@d7qcazihvr3s7k"*. The
  trail: `GetWorkgroup` at 05:22:23 and `GetCredentials` at 05:22:24 by the project role's
  `GlueJobRunnerSession`, through `vpce-0b4195f2018bfbdf1`, no error, `durationSeconds` 900. The
  database: one session at 05:22:25 in `governed`, `BEGIN`, the `DELETE`, ten `INSERT`s, `COMMIT` and the
  count. The table holds 10 rows, 2026-10-01 to 2026-10-05, two a day: release F's batch replaced Stage
  9's 30 rows on the same dates, and the datashare serves the 10. `./aws/warehouse.py awsds-infra-prod
  --sql` at 05:26: every check passing, `WH-12` *"4 user-role grant(s)"*. **xxxii reads yes**, the
  refused doors by the simulation of 05:01.
- **[user] Whether `production-register` of pipeline #129 runs.** **[Claude]** no, read at 05:35 UTC as
  `awsds-infra-prod`: the job is Stage 10 step 5.2's registration of the newest completed
  `app-etl-train-*` job, on no step of §N.8.4. Production's newest is `app-etl-train-20261025T070126`,
  trained under `v0.4.2`, and `awsds-prod-chain-app-etl-train`, recreated at step 8, holds no execution;
  `awsds-prod-model-app-etl` holds version 1, `Approved`, *"app-etl v0.4.2, trained by
  app-etl-train-20261025T011858"*. With `--project` the job reads that training job's evaluation under
  `deploy-production`'s shared prefix, where it never wrote, so it would fail. `production-register`,
  `production-approve` and `production-transform` stay `manual`, as in release T's pipeline.
- **[user] The sitting's downs** (*"Downs concluídos"*), as handed: `make down ENV=production
  ONLY=workloads-egress,warehouse-compute`, `make gitlab-down`, the tunnel and `make hub-down`.
  **[Claude] §R's readings** at 05:50 UTC as the infrastructure user: `./aws/egress.py` on Production,
  Staging and Sandbox Account 1, every check passing, the burn meter 0 interface endpoints, 0 NAT gateways
  and 0.000 USD/h in each; `make status`: `vpn`, `proxy` and `tooling` stopped, every `[E]` slice down,
  the estimated burn 0.0000 USD/h. Production holds no workgroup and no running instance, and the three
  schedules of `awsds-prod-chains` read `DISABLED`.

## 2026-11-16 — release G's sitting: step 1, `app-etl-dev`'s data product deleted

- **[user] Release G's step 1** (*"Sim, passo 1"*). **[Claude]** read first as `awsds-infra-sandbox-1`:
  `trades-notional` (`5070mjwdvjwp3k`) owned by `app-etl-dev`, revision 1, `CREATED`, created 2026-11-15,
  one item, the asset `c6z3pbg3drrs0g`; no data product listing in the domain, the one listing named
  `trades_notional` being Production's asset (`5hpftif3nnoj2o`, owned by `deploy-production`). Per project,
  each read as the profile whose session belongs to it: `deploy-production` and `deploy-staging` hold no
  data product, `eighth-experimentation` holds `my-data-product`. The runbook's read-back,
  `search --search-scope DATA_PRODUCT --search-text trades-notional`, answered `ValidationException`,
  *"OwningProjectId is mandatory for SearchScope - DATA_PRODUCT"*, and a search in a project the session
  is not a member of answered `AccessDeniedException` (`SUP-371`).
- **[user] The delete** (*"Apaguei"*), the runbook's command. **[Claude]** the trail: `DeleteDataProduct`
  on `5070mjwdvjwp3k` at 06:03:08 UTC, a shared event in Data Governance's trail whose caller is an assumed
  role of Sandbox Account 1, the infrastructure user's `InfrastructureAccess` session, CLI 2.37.12, no
  error. That session is a `PROJECT_CONTRIBUTOR` of `app-etl-dev` through its group profile `839bcde8-…`,
  so DataZone admits a contributor's delete. Read at 06:03:35: `get-data-product` `ResourceNotFoundException`,
  *"Requested dataProduct cannot be found in domain"*; `app-etl-dev`'s data product search empty; the asset
  `c6z3pbg3drrs0g` at revision 5; the listings unchanged.

## 2026-11-16 — the session reviewed; the readings with nothing up; the rest of the stage prepared

*After PR #307's merge. Claude's hand as the infrastructure user with `InfrastructureAccess`, every call a
read, from the branch `claude/stage-19-review-prep` cut from `c5e1718e`. Times UTC.*

- **[user] The request**, *"Revise os logs e as lições aprendidas, e o AWS_SUPPLEMENT, com relação ao
  andamento desta sessão"*, then the readings that need nothing up, the preparation of what is left and a
  new pull request.
- **[Claude] The lessons**: Lesson 84 gains the Bash tool's `grep`, ugrep 7.8.4, refusing
  `(verification |\b)xxvi\b` with *"empty (sub)expression"* and exit 2, silent behind `2>/dev/null`.
  Lesson 85 written: a name has a composer, from `SUP-254`'s log group, which the CLI names, and act 7's
  database user, which the project role's tag names. The supplement gains no entry: `get-tables` read
  `IsRegisteredWithLakeFormation` false on Staging's `app_etl.trades_notional` and `get-table` true in
  both targets, `SUP-364`'s behaviour.
- **[Claude] The instruments**, 06:26 to 06:35: `studio.py` 0 checks failed, `catalog.py` all checks
  passed, `orchestration.py` 5 failed, each `OR-2`'s retention on a CLI-named log group (`EXC-25`),
  `deploytargets.py` 0, `warehouse.py` 0 with notes for the absent workgroups, `datalake.py` 0. Each run's
  failed calls are `get-caller-identity` on the profiles with no session (the persona, deploy and
  `ctadmin` ones).
- **[Claude] xxiii**, at 06:27: the five machines' tasks are `ssm:getParameter`, `listWorkflows`,
  `startWorkflowRun` and `getWorkflowRun`; Production's `step8-xxix-20261116T031909-app-etl` polled
  `getWorkflowRun` 17 times in 174 events, `SUCCEEDED`, and Staging's `v0-5-2-820-app-etl` the same.
  `awsds-prod-chain-exec` and `awsds-staging-chain-exec` each hold `kms:GenerateDataKey` and `Decrypt`
  on one key, `alias/awsds-prod-project` and `alias/awsds-staging-project`. The five schedules read
  `DISABLED`.
- **[Claude] xxi's domain half**, at 06:28: Production's trail holds 69 `PostLineageEvent` from 02:33:49
  to 03:22:07, each by `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow`'s `GlueJobRunnerSession`
  through `vpce-0bb36cd25fa694b27`, no error, with a `sharedEventID`; Data Governance's holds the same 69,
  Staging's 46 through `vpce-0a908a1c053380d9c`, and 23 of Sandbox Account 1 through
  `vpce-0138fb056dc217988` on 2026-11-15 from 22:27:54. Data Governance's
  `CreateLineageNode` events name Production's asset node `b2eaaney9hlus0` (02:46:29) and listing node
  `chg3sfn08jn9xs` (02:46:36); `get-lineage-node` as `awsds-infra-data` chains the table's node
  `6i4aaj4f895ixc`, whose upstream holds two job-run nodes, to the asset's and the listing's.
- **[Claude] xxii**, at 06:28: `deploy-staging` `ACTIVE`, `Tooling` (`d6nu5aphq1e974`) and
  `deploy-staging-app-etl` (`54jhe9989w0tcg`) `ACTIVE` with their subscription targets; the database
  `app_etl` with `trades_notional`; `app_etl_deploy_staging_app_etl` and `…_train` `READY`; the parameter
  `/datascience/staging/applications/app-etl/stage-variables`; two gateway endpoints and no interface
  endpoint in the account.
- **[Claude] The sources and assets**, at 06:30. Staging's `52f18khk7kdi4w`, `cron(28 15 * * ? *)`,
  `publishOnImport` false: scheduled runs from 2026-11-12 to 2026-11-15 at 15:37:23, each adding nothing,
  and the prioritized run `cntcrgrt3c22og` at 02:07:53, `added: 1`; the asset `as6m73yp8shr80` at
  revision 2, unlisted. Production's `5zggi2lr2ezy4w`, `cron(32 15 * * ? *)`: scheduled runs at 15:44:02,
  then four prioritized runs on 2026-11-16, `anhgrpgqahg9e8` at 02:46:17 (`added: 1`), `dk1lm51c3amxw0`
  at 02:49:02 (`unchanged: 1`), `6r028y6qqief4g` at 03:05:14 and `d0b69cl22rdx5c` at 03:33:33 (`updated:
  1` each); the asset `da1fycta6l71n4` at revision 4, its listing `5hpftif3nnoj2o` `ACTIVE`. Neither
  project holds a data product. xvii reads yes for an update in Production; the scheduled runs after the
  imports start today, after 15:28 and 15:32.
- **[Claude] xxx**, from this log's readings of #129 and `./scripts/deploy-application.py --self-check`
  on `c5e1718e`'s tree: `OK`, both projects' nine variables and workflows read.
- **[Claude] The model chain's layout**, at 06:30: Staging's newest training job,
  `app-etl-train-20261116T020100`, ran as the project role and wrote its model and `evaluation.json`
  under `deploy-staging`'s `shared/app-etl/models/`, beside `staging-model`'s transform output.
  Production's newest is release T's `app-etl-train-20261025T070126`, as `awsds-prod-job-exec` under the
  outputs bucket, and `deploy-production`'s `shared/app-etl/models/` holds no object; the registry group
  holds version 1, `Approved`.
- **[Claude] Release G's step 3 re-planned** from `c5e1718e`'s tree into
  `$HOME/tmp/stage19-g-production-studio.tfplan` at 06:33:33: *"Plan: 2 to add, 0 to change, 2 to
  destroy"*, `awsds-prod-workflows` and its attachment replaced on the description's change, the new
  statement `CreateTheProductsDataProductInTheProjectsDomain` carrying `datazone:CreateDataProduct` and
  `CreateDataProductRevision`. `staging/studio/` at 06:34: *"No changes"*.
- **[Claude] Release G's merge request read**: GitLab's `main` holds `ced09fe4:examples/app-etl`, so it
  carries `git diff ced09fe4 c5e1718e -- examples/app-etl`, eight files and 490 lines added, the tree
  `3b43b395…`.
- **[Claude] 4.12's state**: no subscription to `5hpftif3nnoj2o` (revision 6); Production's Lake
  Formation parameters `CROSS_ACCOUNT_VERSION` `4` and `SET_CONTEXT` `TRUE`, three administrators, no
  full-table flag; no Data Catalog resource policy; three RAM shares Production owns, from 2026-10-18.
  `deploy-production`'s members: the owner groups `ca2735c9-…` and `c332eee6-…` and the project role's
  profile `40991e26-…` as contributor. The Governance Manager's user profile `e8a1f320-…` is no member,
  so decision 15 (a)'s membership comes before the approval. `eighth-experimentation`'s
  `blerpkhn9nj7o0` is `ACTIVE`.
- **[Claude] The retirement inventoried** (item 31): each of release T's four states pulled with exit 0,
  no resource and no output, `staging/orchestration/` at serial 33, `staging/app/app-etl/` 22,
  `production/orchestration/` 12 and `production/app/app-etl/` 6; `app_outputs` holds no table in either
  target. The admin secret of Production's warehouse reads `NextRotationDate` 2026-11-22 01:59:59, never
  rotated.
- **[Claude] Written**: the stage file's verifications xvii, xxi to xxiii, xxv and xxx, items 12, 19, 21
  and 31, the sittings in order and the retirement's inventory, 4.12's state and 5.1's reading rule;
  `runbooks/promotion.md` §N.6, §N.8.3 and §N.8.5; the waiting list's release rows, 4.12's new row, the
  GitLab backup's date and the Promotion row; `CLAUDE.md`'s row and Lesson 85.

## 2026-11-17 — `SUP-368`'s line in Sandbox's bill: the Glue session billed at its `DPUSeconds`

Claude's reads as `awsds-infra-sandbox-1`, Sandbox's `InfrastructureAccess`; no AWS write. Each Cost
Explorer read is one `get-cost-and-usage`, daily, unblended and net, by service and usage type: four
requests, 0.04 USD.

- **[Claude] Cost Explorer before it held the day**: at 05:05:57 UTC on 2026-11-15, 2026-11-14 and
  2026-11-15 held no line, and 2026-11-13 held 3 to 6 hours of its whole-day lines (the alarms 0.1000
  against 0.4000 on 2026-11-10 to 12, the dashboard 0.0083 against 0.0333, the secret 0.0069 against
  0.0333, Unified Studio's volumes 0.1111 against 0.5333 GB-month). At 00:02:33 UTC on 2026-11-16,
  2026-11-14 and 2026-11-15 still held none.
- **[Claude] The sessions**, `glue list-sessions` at 22:37:00 UTC on 2026-11-15, before release T's step 17
  removed `app-etl` from `test-experimentation`: one session in Sandbox,
  `4gqfau9xuo6e4w-93939e2b-07b3-4c1b-b18a-e875438bd870`, `STOPPED`, created 22:47:31.313 and completed
  23:07:37.219 UTC on 2026-11-14, `ExecutionTime` 1151.921, `DPUSeconds` 3248.638, `MaxCapacity` 10.0,
  Glue 5.0.
- **[Claude] The day held**, read 01:12:48 UTC on 2026-11-17: 2026-11-14 holds 47 lines, its last hour
  in. `USW2-VpcEndpoint-Hours` reads 38, Sandbox's 19 interface endpoints over 22:00 and 23:00 UTC;
  `USW2-ETL-DPU-Hour-Gen2` 0.082222 DPU-h and 0.0253 USD, `app-etl-dev`'s run started at 23:48:48; the
  whole-day lines at the values of 2026-11-10 to 12. 2026-11-13 is whole; 2026-11-15 holds 44 lines and
  9 endpoint hours, where the 2026-11-14 sitting's hour after midnight alone bills 19.
- **[Claude] The line**: `AWS Glue`, `USW2-GlueInteractiveSession-DPU-Hour`, 2026-11-14, 0.9025 DPU-h and
  0.3971 USD, unblended and net. The field gives 0.9024 DPU-h (3248.638 DPU-s) at 0.44 USD/DPU-h; the
  formula `ExecutionTime * MaxCapacity` gives 3.1998 DPU-h and 1.41 USD, and 1205.9 s from creation to
  completion at 10 DPU gives 3.3497 and 1.47. The bill charges `DPUSeconds` (`SUP-368`, Lesson 81,
  `PRICING.md` §5).

## 2026-11-17 — item 31, the retirement written: PR #308's code and its five saved plans

Claude's work in the worktree, the reads as the infrastructure user's `InfrastructureAccess`
(`awsds-infra-staging`, `awsds-infra-prod`); no apply, no AWS write.

- **[user] The request**, the answer to the wrap-up's question whether the retirement goes in PR #308:
  *"Yes, in this PR"*. Mid-turn: *"faça rebase em relação à main"*.
- **[Claude] The code** (the stage file's §The retirement as written): the four slices' folders,
  `release-application.py`, `render-workflow.py` and `lint-plan.py`, and both `foundation/` slices'
  `apply-orchestration.tf` and `app-boundary.tf` removed; `app_outputs` out of both `data/`; `model-chain.py`
  without the outputs layout, `--project` required; `layers.py` without ranks 58 and 59 and refusal 7; the
  gates, the Makefile, the hooks and the docs that named them. The corrections to the inventory: the chain
  statements stay in Staging, `apply-application.tf` keeps its egress, DNS Firewall and model-chain
  statements, the service-linked role's grant moves to `deploy-project.tf`, and the job role's
  `CommitTheIcebergWrites` names `app_outputs` too. `deploy-role-v0.3.0` refused an empty `state_prefixes`;
  `v0.5.0` takes it. `make check` passed.
- **[Claude] The rebase**, at the user's word, against `CLAUDE.md`'s rule that a pushed branch is never
  rebased: the work set aside as a local WIP commit, then `git rebase origin/main` onto `1d91d5b4` (PR #310).
  Three conflicts, both sides kept: `CLAUDE.md`'s Stage 19 row without #310's `SUP-368` clause, the stage
  file's Status row with #310's reading of 2026-11-17, and this log's two entries in date order. `make check`
  and the hooks passed on the rebased commit `e1daa970`, pushed alone with `--force-with-lease` against
  `9e686cd3`; PR #308 0 commits behind `main`.
- **[Claude] The plans**, each saved in `$HOME/tmp/` and read whole with `terraform show -json`:
  `staging/foundation/` and `production/foundation/` 0 to add, 5 to change, 5 to destroy each; both `data/`
  0, 0, 8; `production/sagemaker/` 0, 1, 0; nothing outside the retirement. `deploy_project` grows to 5,060
  characters in Staging and 5,045 in Production, of IAM's 6,144. The first `data/` plans answered *"No valid
  credential sources found"*: the backend and the default provider read `AWS_PROFILE`, which those runs had
  not exported.
- **[Claude] `SUP-260` read again**, CloudTrail's `lookup-events` in both targets from 2026-11-15 00:00 UTC:
  in Staging, `iam:CreateServiceLinkedRole` invoked by `airflow-serverless.amazonaws.com` in
  `awsds-deploy-staging`'s sessions at 20:46:18 UTC on 2026-11-15, a second before release T's first
  `CreateWorkflow` through Cloud Control, and at 23:21:03, a second before the CLI's first, both answered
  `InvalidInputException`; each session's second creation (20:46:27, 23:21:16) drew none. In Production,
  none: the CLI's three creations at 02:31:50, 02:32:02 and 02:32:14 UTC on 2026-11-16 drew none.
- **Owed**: the user's five applies after the merge; at the apply, `AWS_STATE.md`'s rows naming the
  retired path and `TM-30`'s list.

## 2026-11-17 — item 31 applied: PR #308's five saved plans, from its branch, read back

On the user's word, *"Authorize the 5 applies"*, Claude applied the saved plans from the branch before the
merge, which closes the Lesson 79 window. The two peer sessions on the laptop, both idle, were told first.
Every read as `awsds-infra-staging` or `awsds-infra-prod`, `InfrastructureAccess`.

- **[Claude⚡] The applies**, each `terraform apply -input=false <plan>` from the slice's folder:
  `staging/foundation/` 01:55:53 to 01:56:07 UTC, 0 added, 5 changed, 5 destroyed; `production/foundation/`
  to 01:56:24, the same; `staging/data/` to 01:56:40, 8 destroyed; `production/data/` to 01:56:53, 8
  destroyed; `production/sagemaker/` to 01:57:03, 1 changed. No warning.
- **[Claude] Read back**: each slice re-planned from the tree that applied, `No changes`. IAM in both
  accounts: `awsds-<env>-app-boundary`, `-deploy-orchestration-resources` and `-access` `NoSuchEntity`;
  each deploy role holds `apply-application` and `state` inline and `awsds-<env>-deploy-project` attached,
  at `v5` with `CreateTheWorkflowServiceLinkedRole`; its boundary `awsds-<env>-deploy-boundary` at `v2`,
  `CeilingIsEverythingTheIdentityPolicyGrants`, `DenyChangingTheDeployIdentities` and
  `DenyChangingTheCeilings`; `state` with `ListTheStatePrefixes`, `ReadTheStateItOnlyReads` and
  `UseTheStateKey`; Staging's `apply-application` with the two chain statements, Production's without.
  Glue `get-database` on `app_outputs`: `EntityNotFoundException` in both. `awsds-prod-job-exec`'s
  `CommitTheIcebergWrites` names the lake's `curated` catalog, database and tables alone. `data/`'s states
  hold 9 `aws_lakeformation_permissions` in Production and 8 in Staging, four of each in the consumer module.
- **[Claude] The instruments**: `./aws/deploytargets.py` 44 pass, `DT-14` reading *"raw, curated: named
  principals only"* in both; `./aws/cicd.py` 12 pass and 4 notes (`CI-1`, `CI-6`, `CI-8`, `CI-9`);
  `./aws/orchestration.py` only `OR-2`'s five retention failures (`EXC-25`), `OR-9` passing both targets'
  chains. Production's three schedules read `DISABLED` since their creation at 03:18:16 UTC on 2026-11-16,
  at 06:30, 07:00 and 07:30 UTC, each input carrying `<aws.scheduler.scheduled-time>` literally. Each
  script exits 1 on the profiles with no SSO token; the wording is the verdict.
- **[Claude] Written**: `AWS_STATE.md`'s rows on the retired path (`INV-22`, the deploy credential layer,
  the chain schedules, the deployment projects' changes, Lake Formation's governing row, the grant
  register) and `TM-30`'s list.

## 2026-11-17 — the plan reviewed against the estate, with nothing up

The user asked for a review of the plan after Stages 17, 19 and 20 moved, against the estate and SMUS's
intended path, with the readings, the corrections and the writes that need neither the environment up nor
the user's hand.

- **[Claude] Before the readings**: `aws sts get-caller-identity` answered as `InfrastructureAccess` on
  the profiles used; no other session of this project was running on the laptop.
- **[Claude] Plans from `main` at `80e996f5`**, 05:04:55 to 05:13:28 UTC, each saved and none applied:
  `staging/foundation/`, `production/foundation/`, `staging/data/`, `production/data/` and
  `production/sagemaker/` read `No changes`, so PR #308's merge at 02:13 UTC closed Lesson 79's window
  of item 31; `staging/studio/`, both `chains/`, `sandbox/sagemaker/` and `sandbox/workflows/` read `No
  changes`; `production/studio/` reads release G's step 3, *"Plan: 2 to add, 0 to change, 2 to destroy"*:
  `aws_iam_policy.workflows[0]` replaced on its description, gaining
  `CreateTheProductsDataProductInTheProjectsDomain`, and the project's attachment replaced with it.
- **[Claude] xvii's scheduled half and xxv's daily half**, `list-data-source-runs` and
  `list-data-source-run-activities` as `awsds-infra-data`: Staging's scheduled run `d2dkxz7n5oa7io`,
  2026-11-16 15:37:23 UTC, `{"added":0,"updated":1,"unchanged":0,"failed":0}`, its activity
  `SUCCEEDED_UPDATED` on `as6m73yp8shr80`; Production's `csxogqh8c7lzio`, 15:44:02 UTC, `unchanged: 1`
  on `da1fycta6l71n4`. `./aws/catalog.py` at 05:45 UTC: every check passes, `CT-15` among them, 10
  listings and none of `deploy-staging`. `get-asset` is refused to this principal, so whether Staging's
  update kept `dev`'s business metadata is unread.
- **[Claude] The GitLab backups' record**: the newest backup is the timer's of 2026-11-16 03:01 UTC,
  taken during release F's sitting, not release T's of 2026-11-15 22:38 UTC; under the bucket's 30-day
  rule it leaves on 2026-12-17. `promotion.md` §N.8.3 and the waiting list corrected.
- **[Claude] The code in a deployment project** (decision 28), `iam simulate-principal-policy` as
  `deploy-production`'s project role with the Region, the organization, the account and the role's
  tags in the context (`SUP-008`): `s3:PutObject` and `s3:DeleteObject` `allowed`, by
  `SageMakerStudioProjectUserRolePolicy`, on `shared/app-etl/glue/`, `src/` and `workflows/`, on
  `shared/operatorFiles/` and on an `app-ml` prefix. `awsds-prod-smus-projects`' policy holds
  `DenyInsecureTransport` alone, and its versioning reads `Enabled`.
- **[Claude] The registry, as the same role**: `UpdateModelPackage` and `DescribeModelPackage` on
  `awsds-prod-model-app-etl/1` read `implicitDeny` without the resource's `AmazonDataZoneProject` tag
  and `allowed` with it, by `SageMakerStudioProjectRoleMachineLearningPolicy`; `ListModelPackages` and
  `ListModelPackageGroups` on `*` and `DescribeModelPackageGroup` on the untagged group `allowed`.
  `TM-30`'s sentence on the registry corrected, and Stage 17 step 9.5 given a `Deny` of
  `UpdateModelPackage` (Lesson 72).
- **[Claude] Decisions put to the user**: decision 28, who can rewrite an application's code in a
  deployment project, with `TM-32`; decision 15 again before 4.12, a custom designation for the approver,
  since the premise that the V2 domain admits no viewer is contradicted by the designations read on
  2026-11-13. D07, D17, D20, D28 and D41 amended in place with dated lines (step 6.2's first lines), D41
  with a revision trigger: a CLI release that writes `{env.*}` into a workflow's `Environment` or exposes
  a project's network values retires a chain of one.
- **[Claude] Written**: the corrections the review found in the runbooks, the decisions, Stages 6h, 10,
  11, 17 and 20, `threat-model.md`, `integrations.md` (`INT-07`, `INT-25`), `AWS_STATE.md` (`INV-18`),
  `waiting-on-the-user.md`, `CLAUDE.md`, and the comments of the slices, modules and scripts that still
  named release T's path; Stage 17's and Stage 20's readings are in their own logs. Nothing in AWS
  changed by this entry.
- **[Claude] The runbooks rewritten for release F**, by a subagent of the review and read by the session:
  `sagemaker-application.md` (§A to §Z, §S pointing at Stage 17's tables, `TM-32` where the code is
  written) and `serverless-workflows.md`, no heading renamed. Left for step 6.2 or the stage that owns
  each: Production's `persona_read_prefixes` names a prefix release F does not write; the project role's
  pull of the application image, inferred from the runs and granted by no estate statement; whether every
  line a Glue script prints reaches `datazone-<id>-dev/output`; and in the template, release G's merge
  request's scope, the `build-task-code` comment, the README's job table without the catalog jobs and
  `load_warehouse.py`'s `IAMR:<the role's name>`, which xxxii contradicts.
- **[Claude] Release G's step 3 not applied**: with no Production run in progress (the three chains'
  state machines holding no `RUNNING` execution, their schedules `DISABLED`, the workflows' latest runs
  ended) and no other session of this project running, the apply of the saved plan was refused by the
  app's classifier, *Production Deploy*, under the user's authorization of the session's writes. The plan
  stays saved for the user's word naming it.

## 2026-11-17 — release G's step 3: `production/studio/` applied from its saved plan

On the user's word naming the apply, *"Autorizo o apply"*, the answer to *"Autoriza o apply de
`production/studio/` a partir do plano salvo do release G?"*, Claude applied the plan saved at 05:06 UTC
from `main` at `80e996f5`. Every call as `awsds-infra-prod`, `InfrastructureAccess`, in Production.

- **[Claude] Before the apply**, 13:09 to 13:11 UTC: `origin/main` still at `80e996f5`, no commit since
  touching `production/studio/` or a module, and this branch changing neither. The three chains' state
  machines hold no `RUNNING` execution and their schedules read `DISABLED`; the three MWAA Serverless
  workflows of `deploy-production` hold no run in progress, the latest ended 2026-11-16 05:22:41 UTC; no
  SageMaker processing or training job is `InProgress` and no Glue job run is running. The peer session of
  this project on the laptop, *Worktrees para apagar*, idle, was told first; the other works in another
  repository.
- **[Claude⚡] The apply**, `terraform apply -input=false <plan>` with Terraform 1.16.6, 13:11:44 to
  13:11:57 UTC: *"Apply complete! Resources: 2 added, 0 changed, 2 destroyed."* The project role held no
  workflows grant between the attachment's destruction and its re-creation, the apply's lines reading 1 s,
  0 s, 1 s and 0 s. The app's classifier let the apply through.
- **[Claude] Read back**: the re-plan from the same tree at 13:12:44 UTC, *"No changes. Your
  infrastructure matches the configuration."*; `awsds-prod-workflows` at `v1` of 13:11:54 UTC, one
  attachment, seven statements, the last `CreateTheProductsDataProductInTheProjectsDomain` granting
  `datazone:CreateDataProduct` and `CreateDataProductRevision` on the domain's ARN. `deploy-production`'s
  project role holds it beside AWS's three managed policies, `awsds-prod-warehouse-load` and
  `awsds-prod-person-session-deny`.
- **[Claude] The simulator answers nothing on the new pair**, 13:13 to 13:20 UTC, `iam
  simulate-principal-policy` as the project role with the Region, the organization, both accounts, the
  role's ARN and its 17 tags in the context. With the domain's ARN, in the Data Governance account, and
  with the same ARN rewritten to Production's account, `CreateDataProduct`, `CreateDataProductRevision`,
  `DeleteDataProduct` and `StartDataSourceRun` read `implicitDeny` naming no statement and carrying no
  organization or boundary detail; `GetDomain` read `allowed` by the managed policies. With no resource
  named, the organization and the boundary read `true` and the four `implicitDeny`. `StartDataSourceRun`
  runs under the same form of statement (`SUP-346`), so step 5's trail is the measurement; appended to
  `SUP-008`.
- **[Claude] Written**: `promotion.md` §N.6 item 1, §N.8.5 step 3 and its status line; the stage file's
  status row, §Release G as written, item 7 and decision 26; Stage 17's and Stage 20's notes on the
  slice; `serverless-workflows.md`; `waiting-on-the-user.md`'s release G and Stage 20 decision 13 rows;
  `CLAUDE.md`'s Stage 19 row and its classifier row; `SUP-008`.

## 2026-11-17 — decision 15's order, and the sittings that are left reordered, with nothing up

*Claude's hand, in a laptop session at the user's request of 13:42 UTC; no AWS call.*

- **[Claude] `promotion.md` §N.6 rewritten**, 14:08 UTC: each sitting holds one goal, what needs nothing up
  runs before it, and a Sandbox sitting raises no GitLab, the application reaching the space as a tar.
  Release G's sitting also creates `awsds/app-ml` and `awsds/app-genai` and takes the backup due before
  2026-12-17, and carries N.8.3 between 2026-11-22 and 2026-11-25; 4.12 follows it with nothing up; pass 5
  goes to the Sandbox warehouse sitting, before 2026-12-19. §N.5's second-application line names Stage 17's
  and Stage 20's applications, written in `examples/` and undeployed.
- **[Claude] Decision 15's order**, 14:22 UTC: the review against the tool's standard path (6d's log, the
  same day) reads (d) as AWS's own mechanism narrowed, and a designation is read across accounts only once
  the domain's RAM share moves to version 12. The waiting list's two rows say the order: the share, then
  xxvi, then (d).

## 2026-11-17 — the runbooks read for statements the estate has outgrown, with nothing up

*A subagent of a laptop session read the runbooks against the repository and the logs, read-only, with no
AWS call, and edited them in place; Claude applied its findings on `promotion.md` and checked one claim.*

- **[Claude, a subagent] Edited**, 13:54 to about 14:34 UTC: `sandbox-lake.md` (§T's second project exists:
  `wired_projects` names `eighth-experimentation` alone); `break-glass.md` (no member account holds root
  credentials since Stage 1a step 6); `sg-proxy.md` and `dev-env.md` (versions 7 to 10 deleted on
  2026-11-03, version 11 alone; the gallery's setting on the plane since 2026-09-09; the house image installs
  from the gallery); `log-debugging.md` (the workflows' log group is `EXC-25`'s
  `/aws/mwaa-serverless/<domain id>-<project id>/<workflow>`, release T's group gone with
  `<env>/orchestration/`); `terraform-changes.md` §1 (a leg applies no Terraform since release F, and the
  deploy roles write no state since item 31); `remote-ide.md` (§W's pin reading predates SageMaker
  Distribution `4.5.2-cpu`; §C's push); `gitlab.md` (`staging-gate` on the build runner, the bundle role in
  the deploy runner's profiles, the mirror's membership done 2026-10-24); `vpn.md` (one world-open rule, the
  burn rates from `layers.py`, the Sandbox plane's 41 names); `sagemaker-application.md` §D, version 11;
  `serverless-workflows.md` (`EXC-25`); `claude-code-sagemaker.md` (the model set alone open, M5's six
  actions attached and exercised, `vpc-egress-v0.19.0`); `scp-battery.md` (the quotas read 2026-10-24, the
  contrast row's expected answers). Its checks: `check-plan-refs.py` (3,680 links), `check-identifiers.py` and
  `check-copies.py` pass.
- **[Claude] `promotion.md`**, from its findings: the head names §N.6's order; §H step 4 and the record after
  it mark the deploy image's rebuild done on 2026-10-25 as `v0.3.0`; N.1 step 2 says no pipeline job runs
  Terraform since release F.
- **[Claude] Checked**, the subagent's note on Lesson 76: no pipeline definition runs Terraform
  (`examples/app-etl/.gitlab-ci.yml`, `gitlab/awsds/*/.gitlab-ci.yml`), both targets' deploy roles carry
  `state_prefixes = []`, and `scripts/tfhygiene/states.py` reads a state with `aws s3 cp` as JSON. `CLAUDE.md`'s
  line on the Terraform binary, the 1.16.7 rows of `upstream-releases.md` and the waiting list follow: the
  laptop's binary and the offline gates' pin move together, the image's pins at its next release.
- **[Claude, a subagent] Left open**: `aws/probes/probes.py`'s comments still read Production's processing
  quotas at 0, which ended on 2026-10-24, so `ResourceLimitExceeded` on a processing row no longer proves the
  ceiling where a quota is above zero; `sagemaker-ai-ml.md`, written the day before, was not reviewed in depth.

## 2026-11-17 — the CLI's project handling read: memberships and the project role, with nothing up

*Written by Claude, in the session that reviewed `docs/AWS_SUPPLEMENT.md` against the day's findings. No
call made.*

- **[Claude] What was read**: the released wheel `aws_smus_cicd_cli-1.0.9-py3-none-any.whl`, SHA-256
  `bd7258c0…4903`, the one `gitlab/awsds/deploy-image/requirements-cli.txt` pins. Its
  `helpers/project_manager.py` and `helpers/context_resolver.py` are byte-identical to `main` at
  `cdb8e3c18f`, the copy the standard-path reading of the same day cited (6d's log).
- **[Claude] What `deploy` does to an existing project**: `ensure_project_exists` runs
  `_update_existing_project`, which adds each manifest `owners` or `contributors` entry the project lacks
  with `CreateProjectMembership`, removes no member and lets the deploy go on after a refusal. Only under
  `project.create: true`, false by default, does it touch IAM: `role.policies` attached and the inline
  `SelfPassRolePolicy` written on `role.arn`, or `smus-<project>-role` created. `SUP-375`.
- **[Claude] What it means here**: `app-etl`'s manifest names no `owners`, `contributors`, `role` or
  `create`, so by this reading release F's deploys made no membership or IAM call, and decision 15's
  membership stays the owner's act by hand. An `owners` list in the manifest would have the deploy role add
  the member again at every deploy, with `datazone:CreateProjectMembership` on that role.
- **[Claude] The resolver**: `proj` holds `id`, `name`, `domain_id`, `iam_role`, `iam_role_arn`,
  `iam_role_name`, `kms_key_arn` and the connections, as the CLI's substitutions guide lists, and no subnet
  or security group: a documented contract, so no supplement entry.

## 2026-11-17 — decisions 28 and 15 and the RAM share's version taken on cards, with no AWS call

*Claude's sitting in a cloud session of the user's Claude project, no AWS call: the review of the plan's
open decisions the user asked for at 22:01 UTC, one card per decision under the user's default of
21:50 UTC (the path AWS suggests), recorded by pull request #317. Times are UTC.*

- **[user] Decision 28**, at 22:23, on the card *"Quem pode reescrever o código de uma aplicação num
  projeto de implantação?"*: *"Aceitar (padrão da CLI)"*, (c), against the card's recommendation (a).
  `TM-32` reads accepted.
- **[user] The domain's RAM share**, at 22:24, on the card *"Mover o compartilhamento RAM do domínio da
  versão 10 para a 12, a padrão da AWS?"*: *"Mover para a v12 (padrão)"*. **[Claude]** The user's RAM
  write in Data Governance, before xxvi and decision 15's membership, joins the waiting list.
- **[user] Decision 15**, at 22:26, on the card *"Quem aprova as assinaturas da listagem de Produção, na
  4.12 do Stage 19?"*: *"Designação própria do SMUS"*, (d), with (a) kept if xxvi reads no narrowing.

## 2026-11-18 — the entries of 2026-11-17 corrected, and readings carried out of this log

*Claude, a subagent of the orchestrating session, on the laptop, no AWS call.*

- **[Claude] The note left open** in the entry *"the runbooks read for statements the estate has outgrown"*,
  on `aws/probes/probes.py`'s comments reading Production's processing quotas at 0: answered the same day by
  commit `ca7f72bd`, 15:35:46 UTC, which pull request #313 merged at 15:48:50 UTC. Its two comments date the
  readings: Production's processing quotas read 0 on 2026-10-17 and, since 2026-10-24, 8 for `ml.m5.large`
  and 4 for `ml.m5.2xlarge`; an authorized processing row read `ResourceLimitExceeded` while they were 0;
  the training quotas of the three `ml.m5` types read 0 on 2026-10-20 and 20 each since 2026-10-24. The
  expected answers, `_JOB_AUTHORIZED`, are unchanged.
- **[Claude] The runbook's date**, in the same note: *"`sagemaker-ai-ml.md`, written the day before"* came on
  the note's own UTC day. Its first commit, `9493d2b1` on the branch `claude/project-thread-gu4gmf`, is dated
  00:01:16 UTC on 2026-11-17, and pull request #311 merged it as `80e996f5` at 04:39 UTC the same day.
- **[Claude] Item 31's applies**, in the entry *"item 31 applied"*. Its opening line *"Every read as
  `awsds-infra-staging` or `awsds-infra-prod`, `InfrastructureAccess`"* covers the applies too: each ran from
  the slice's folder under its profile, the form the stage file gives (`AWS_PROFILE=awsds-infra-staging
  terraform apply -input=false <plan>`). Its sentence *"Claude applied the saved plans from the branch before
  the merge, which closes the Lesson 79 window"* reads the other way: applying from the unmerged branch
  opened the window, since until the merge a plan of those slices from `main` reverted them (the stage file's
  §The retirement as written), and PR #308's merge at 02:13 UTC closed it, as the entry *"the plan reviewed
  against the estate"* records.
- **[Claude] Written from this log's readings**: `SUP-142` gains the Cost Explorer reads of 2026-11-15 to
  2026-11-17 from the entry on `SUP-368`'s line; step 6.2 gains, as owed, the leftovers the entry *"the plan
  reviewed against the estate"* recorded only here; `REFERENCES.md` gains the CLI's substitutions guide,
  which the entry on the CLI's project handling cites, read with `gh api` at `main` `d768153d57` and
  unchanged since 2026-03-24 (`487e489185`).

## 2026-11-19 — the domain's RAM share at version 13, decision 15 (d)'s designation and xxvi, `EXC-25` read

*Claude's sitting on the laptop, a side session of the orchestrating session, with nothing metered up.
Every call ran as the infrastructure user's `InfrastructureAccess`: `awsds-infra-data` (`<Data Governance
Account>`) for the share and the designation, and `awsds-infra-sandbox-1`, `awsds-infra-staging` and
`awsds-infra-prod` for the reads from the associated accounts. In the texts below the account ids are
`<Sandbox Account 1>`, `<Staging Account>`, `<Production Account>` and `<Data Governance Account>`, and the
user's address is `<infrastructure user>`. The designation calls ran the laptop's CLI 2.37.12 on botocore
1.44.5's DataZone model, copied from the `uv` cache into `AWS_DATA_PATH`. Times are UTC.*

- **[Claude] The share, read before the move**, 02:09 to 02:15:
  - `DataZone-EXTENDED_ACCESS-dzd-d8yrvx1ko7im6o-ORG-ONLY`: `ACTIVE`, `STANDARD`, created 2026-08-21T21:12:34Z.
  - Its permission, `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`: version 10, `ASSOCIATED`,
    `defaultVersion` false.
  - Its associations: three principals, `<Sandbox Account 1>` (2026-08-21) and `<Staging Account>` and
    `<Production Account>` (2026-11-11), and the domain as its one resource.
  - `list-permission-versions`: versions 1 to 12 `UNATTACHABLE`. **Version 13 is the default and the only
    `ATTACHABLE` version, created 2026-11-16T21:08:23Z.**
  - `get-permission`: version 13 holds version 12's 163 unique actions plus
    `datazone:GetSystemTableExportConfiguration`, 164 in all (166 entries, since `GetEnvironment` and
    `GetProject` have each been listed twice since version 10), and removes none. Versions 10 to 12 read as
    in `SUP-360`. `get-permission` dated every version at the second of the call (`SUP-382`, which Stage 17
    measured the same night).
  - `ram get-resource-policies` on the domain: one statement,
    `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess-org-principals`, with the three account roots,
    version 10's 152 actions and the `aws:PrincipalOrgID` condition.
- **[Claude] Put to the user**: the API attaches only a permission's default version, so version 12 cannot
  be attached, and the move to version 13 is final for an AWS managed permission (RAM's user guide).
- **[user] The move authorized** in this session's chat: *"Autorizo mover o ram share do domínio para a versão
  13"*. **[Claude]** The other four sessions on the laptop were told before the call (Stage 17 9.5, Stage 20
  8.3, 6h decision 3 and the orchestrator), and Stage 20 and 6h held their DataZone calls.
- **[Claude] The move**, 02:20:30 to 02:20:31: `aws ram associate-resource-share-permission
  --resource-share-arn <the share's ARN> --permission-arn
  arn:aws:ram::aws:permission/AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess --permission-version
  13 --replace` answered `{"returnValue": true}`. Data Governance's trail records
  `AssociateResourceSharePermission` at 02:20:31Z by `AWSReservedSSO_InfrastructureAccess_ba1899ccb658ab35`,
  with `replace` true, `permissionVersion` 13 and no error.
- **[Claude] Read after the move**:
  - 02:20:41: the share `ACTIVE`, `STANDARD`, its permission at version 13, `defaultVersion` true,
    `ASSOCIATED`, `lastUpdatedTime` 02:20:33. The share's own `lastUpdatedTime` is still 2026-08-21, and the
    four associations keep their earlier times.
  - 02:21:01: the domain's resource policy keeps the same statement, principals and condition, now with
    version 13's 164 actions. The added actions are `CreateDataApp`, `DeleteDataApp`, `GetDataApp`,
    `GetDesignation`, `GetGroupProfile`, `GetSystemTableExportConfiguration`, `ListDataApps`,
    `ListDeployableEnvironmentBlueprints`, `ListDesignations`, `ListSharedDataApps`, `UpdateAssetOwner` and
    `UpdateDataApp`.
  - The sessions were told at 02:21. Stage 20's `create-environment` calls followed, from Staging at
    02:23:05 and from Production at 02:26:58. Both answered, and none of that session's reads in either
    target from 02:21:40 was refused (`log-stage-20-dbt-lineage.md`, 2026-11-19). 6h's `UpdateConnection`
    followed its own reading of the share at 02:21:41.
- **[Claude] What the move changed for the associated accounts**, read as each account's `InfrastructureAccess`:
  - `get-group-profile` on `sso-group-data-scientists` answered from `<Sandbox Account 1>`, `<Staging
    Account>` and `<Production Account>` at 02:22:10 to 02:22:14. Version 10 refused this call (`SUP-157`).
  - The control, `get-project-profile` on `ds7ur2s2ce42vk`, was still refused in all three: *"User:
    arn:aws:sts::<Production Account>:assumed-role/AWSReservedSSO_InfrastructureAccess_c2bcabf74c885115/<infrastructure
    user> is not authorized to perform: datazone:GetProjectProfile on resource:
    arn:aws:datazone:us-west-2:<Data Governance Account>:domain/dzd-d8yrvx1ko7im6o because no resource-based
    policy allows the datazone:GetProjectProfile action"*.
  - `list-designations` and `get-designation PROJECT_CONTRIBUTOR` answered from all three at 02:26:05 to
    02:26:09. Sandbox was refused `ListDesignations` on 2026-11-14 (`SUP-360`).
  - Not called: `ListDeployableEnvironmentBlueprints`, `UpdateAssetOwner`, the Data App actions and
    `GetSystemTableExportConfiguration`. The laptop's CLI has none of them, and botocore 1.44.5 has no
    `GetSystemTableExportConfiguration`.
- **[Claude] The managed designations**, read from Data Governance at 02:24: `PROJECT_OWNER` and
  `PROJECT_CONTRIBUTOR`, `MANAGED`, deletion protection on, created by `system`. Their stored Cedar policies
  hold 23 and 18 statements and 158 and 150 unique actions, and differ from the admin guide's printed text
  (`SUP-385`).
- **[Claude] `deploy-production`'s members**, read from Production at 02:26: the two owner groups as
  `PROJECT_OWNER` and the project role's user profile as `PROJECT_CONTRIBUTOR`, as on 2026-11-16. The
  Governance Manager is not a member.
- **[Claude] The designation put to the user**: `subscription-approver`, a policy of three statements with
  the individual actions of Subscriptions' *Manage subscription approvals* (5), Catalog's *Read-only
  actions* (9) and the 17 Data Agent actions the stored `PROJECT_CONTRIBUTOR` holds. AWS's designations page
  requires the Data Agent in every custom designation.
- **[user] The creation authorized**: *"Autorizo criar a designation subscription-approver"*. **[Claude]** The
  four sessions were told before it.
- **[Claude] The first attempt refused**, 02:33:29 to 02:33:30: `aws datazone create-designation
  --domain-identifier dzd-d8yrvx1ko7im6o --name subscription-approver --description "…" --policy
  file://subscription-approver.cedar` answered *"An error occurred (ValidationException) when calling the
  CreateDesignation operation: Invalid designation policy: Designation policy validation error: the
  specified action is not a valid action group"*. Nothing was created. Data Governance's trail records
  `CreateDesignation` at 02:33:30Z with `ValidationException`. A custom designation's policy names action
  groups (`SUP-384`).
- **[Claude] The policy rewritten and put to the user**: three statements naming
  `Subscriptions::Action::"ManageSubscriptionApprovals"`, `Catalog::Action::"ReadOnlyActions"` and
  `DataAgent::Action::"AllActions"`. The first id was inferred from the pattern of the group ids a
  community article read in a designation made in the portal. One more attempt with Connections' two groups
  was proposed, only if the validation asked for them.
- **[user]** *"Pode tentar novamente"*.
- **[Claude] Created**, 02:46:45 to 02:46:47, with the same command and the rewritten policy:
  - The response: `id` `ahjm1h20oujxqo`, `designationType` `USER_CREATED`, `deletionProtection` true,
    `createdBy` `9e7cfd86-4ddb-4ea1-b43f-04417861d609`, `createdAt` 2026-11-19T02:46:46.779396Z. The validation
    did not ask for the Connections groups.
  - Data Governance's trail, read at 02:53: `CreateDesignation` at 02:46:46Z by the same role, no error, the
    response's `id` `ahjm1h20oujxqo`.
  - 02:47: `get-designation` returned the submitted policy byte for byte. `list-designations` listed the
    designation from `<Data Governance Account>`, `<Sandbox Account 1>`, `<Staging Account>` and
    `<Production Account>`, and `get-designation` answered from Production.
  - No membership was created.
- **[Claude] xxvi read from the designation as created** (the stage file's xxvi). By AWS's designation
  permissions page, its three groups expand to 5 Subscriptions actions, 9 Catalog reads and the Data Agent's
  actions. Cedar permits nothing else, so against `PROJECT_CONTRIBUTOR` it withholds the Project, the
  Connections, and the Notebooks and Querybooks categories, among them `GetEnvironmentCredentials` and the
  catalog's writes and publishing. Which Data Agent actions `AllActions` grants is not readable:
  `get-designation` returns the group as written, the page lists 14 actions and the managed designations
  store 17 (`SUP-385`). The portal's half needs the membership.
- **[Claude] `EXC-25`'s provider**, read at about 02:30:
  - The newest `hashicorp/aws` release is still 6.73.0 (2026-11-11).
  - `aws_cloudwatch_log_account_policy` validates `policy_type` with the AWS SDK's `PolicyType` enum.
  - The SDK's `service/cloudwatchlogs` added `RETENTION_POLICY` in v1.91.0 (2026-10-30, its changelog). The
    provider's `go.mod` pins v1.90.2, both at `v6.73.0` and on `main`.
  - PR #50873 documents the type and changes no `go.mod`. It is a draft from an external contributor,
    opened 2026-11-10 and untouched since 11:40 UTC that day.
  - The three `foundation/` slices lock 6.60.0 under `~> 6.60`.
- **[Claude] Written**:
  - the stage file: decisions 15 and 27, step 4.12, xxvi, the sittings' item 9 and the `Status` row;
  - `SUP-147`, `SUP-157`, `SUP-360` and `SUP-382` appended, and `SUP-384` and `SUP-385` new;
  - `upstream-releases.md`'s designations row, the provider's `RETENTION_POLICY` row and the next reading;
  - the waiting list, without the RAM share's row and the designation's row, and with 4.12's row rewritten;
  - `docs/SMUS.md`, `runbooks/catalog.md` and `runbooks/promotion.md` §N.6 item 4;
  - `REFERENCES.md`;
  - at the orchestrator's request, two rows other sessions' measurements of the same day had overtaken: the
    premise table's 6h row (6h decision 3 done, PR #327) and xix (`SUP-184`'s reading, PR #328).

## 2026-11-19 — pass 5's pre-flight: the access role holds no read of the subscribed product

*Claude, in the pre-flight session of the Sandbox warehouse sitting started by the orchestrating session,
as the infrastructure user, permission set `InfrastructureAccess`, through `awsds-infra-sandbox-1`
(account Sandbox Account 1), with `awsds-infra-prod` and `awsds-infra-data` read for their account ids
alone. Reads only, no apply and no AWS write. Times are UTC.*

- **[Claude] The policies on the two doors**, about 22:00: the access role
  `awsds-sandbox-warehouse-access-avhvbqn37ty7m8` carries two customer-managed policies,
  `awsds-sandbox-warehouse-project-avhvbqn37ty7m8` and `awsds-sandbox-warehouse-access-portal-avhvbqn37ty7m8`,
  and no inline one; the project role `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` carries seven, three of
  them AWS's (`SageMakerStudioProjectUserRolePolicy` among them) and four of this repository's.
- **[Claude] `simulate-principal-policy` with no context entries**: on both roles, `glue:GetTable` and
  `glue:GetDatabase` read `explicitDeny` on every resource, the lake account's `governed_trades` included, the
  read that works since 2026-10-25; the result carries `AllowedByOrganizations: false` and no matched
  statement. 6h's simulation of 2026-10-18 passed `aws:RequestedRegion` and `aws:PrincipalArn`, and this one
  did not, so the organization's verdict is unread here.
- **[Claude] `simulate-custom-policy` on the access role's two policies**, the identity half alone:

  | Resource | `glue:GetTable` | `glue:GetDatabase` |
  |---|---|---|
  | the lake account's `table/governed_trades/x`, the positive control | `allowed` | `allowed` |
  | Sandbox's `table/glue_db_blerpkhn9nj7o0/trades_notional` | `implicitDeny` | `implicitDeny` |
  | Production's `table/app_etl/trades_notional` | `implicitDeny` | `implicitDeny` |
  | Production's `database/app_etl` | `implicitDeny` | `implicitDeny` |

  `lakeformation:GetDataAccess`: `implicitDeny`. **`simulate-principal-policy` on the access role at 22:24**, with
  `aws:RequestedRegion=us-west-2` and `aws:PrincipalArn` in the context: `glue:GetTable` `allowed` on the
  positive control and `implicitDeny` on Sandbox's and Production's `trades_notional`, `GetDataAccess`
  `implicitDeny`, each with `AllowedByOrganizations: true`. So the read in place through §J's chain or the connection is
  refused by IAM at `glue:GetTable` before Lake Formation is consulted, as the governed share was on
  2026-10-25 until `ReadTheGovernedShareCatalog` was written. 5.1 names the Lake Formation and SQL pieces, not
  this one.
- **[Claude] The same simulator on the project role's policies** (`SageMakerStudioProjectUserRolePolicy` v77,
  `awsds-sandbox-warehouse-project-avhvbqn37ty7m8`, `SageMakerStudioProjectRoleMachineLearningPolicy`):
  `GetDataAccess` `allowed` by `LFforDL`, `glue:GetDatabase` `allowed` on Production's `database/app_etl`,
  `glue:GetTable` `implicitDeny` on the three tables. v77's `GlueDatalakePermissions` allows Glue on `*` when
  `glue:LakeFormationPermissions` is `Enabled`, a key the simulator cannot supply, so the direct door's table
  read is unanswered by the simulator rather than refused.
- **[Claude] The register**: the per-project database user holds `TEMP ON DATABASE sandbox` and `USAGE ON
  DATABASE governed_trades` (2026-10-25) and no `USAGE ON DATABASE awsdatacatalog`.
- **[Claude] The block written**: "The Sandbox warehouse sitting: pass 5 in order" in the stage file, before
  "To execute", with the access role's two absent pieces as the user's word before the sitting, or 5.2 through
  the direct door.

## 2026-11-19 — 5.2's door: the access role's statement written and planned, unapplied

*Claude, in the same session, on the user's "Sim, escreva" to the question whether to write the access
role's statement in PR #339; as the infrastructure user, permission set `InfrastructureAccess`, through
`awsds-infra-sandbox-1` (account Sandbox Account 1), with `awsds-infra-prod` (account Production) for two
reads and its account id. A plan from the branch, no apply and no AWS write. Times are UTC.*

- **[user] The door**: §J's chain, through the access role, answered *"Sim, escreva"*. The direct door as
  the project role stays the fallback the stage file names.
- **[Claude] Production's table and its location**, about 22:47, as `awsds-infra-prod`: `glue get-table` on
  `app_etl.trades_notional` reads `EXTERNAL_TABLE`, `table_type` `ICEBERG`, no partition keys, its location
  under `s3://awsds-prod-smus-projects/dzd-d8yrvx1ko7im6o/d7qcazihvr3s7k/dev/data/catalogs/`.
  `lakeformation list-resources` reads one registered location, `s3://awsds-prod-smus-projects/dzd-d8yrvx1ko7im6o/d7qcazihvr3s7k/dev`,
  role `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow`, `HybridAccessEnabled: false`, `VERIFIED`, last
  modified 2026-11-11 15:30 UTC. So the read takes `GetDataAccess`, and neither an S3 grant nor a partition
  action.
- **[Claude] The statement written**: `sandbox/warehouse/`'s new map `subscribed_products`, keyed by
  project id, its one entry `avhvbqn37ty7m8` naming `glue_db_blerpkhn9nj7o0`, `app_etl` and
  `trades_notional`; two dynamic statements in `project_access_portal`, after `ReadTheGovernedShareCatalog`:
  `ReadTheSubscribedProductsCatalog`, the four Glue reads on Sandbox's catalog, the link database and its
  tables and on Production's catalog, `app_etl` and `trades_notional`, and
  `LakeFormationVendsTheSubscribedProductsData`, `lakeformation:GetDataAccess` on `*`. Production's id is
  resolved by the aliased provider `production` and `data.aws_caller_identity.production`, its profile from a
  new `producers` emission of `scripts/tfhygiene/backend.py` for a SMUS member's `warehouse` slice, the
  `data-governance/data/` idiom.
- **[Claude] The plan from the branch**, 22:49:04 to 22:49:17, as `awsds-infra-sandbox-1` with
  `-input=false -var all_projects_tag_enabled=false -var data_transfer_role_enabled=false`: *"Plan: 0 to add,
  1 to change, 0 to destroy."*, `aws_iam_policy.project_access_portal["avhvbqn37ty7m8"]` updated in place. Of
  the new statement's Glue ARNs, three carry Sandbox's account and three Production's, read from the plan's
  JSON against each profile's account with no id printed. The planned document is 2,224 characters without
  whitespace, under IAM's 6,144.
- **[Claude] `simulate-custom-policy` on the two planned statements**, 22:51, one resource per call:
  `glue:GetTable` and `glue:GetDatabase` `allowed` on Sandbox's catalog, `database/glue_db_blerpkhn9nj7o0` and
  `table/glue_db_blerpkhn9nj7o0/trades_notional`, and on Production's catalog, `database/app_etl` and
  `table/app_etl/trades_notional`; `implicitDeny` on Production's `table/app_etl/other_table` and
  `database/curated`, the negative controls; `lakeformation:GetDataAccess` `allowed`. The whole planned
  document was refused at the simulator's 2,000 characters (`SUP-006`), and one call lost its ARNs to zsh's
  `:c` modifier (Lesson 84) before the run above. A call naming the eight resources at once returned one result per
  action, its resource the pattern `arn:aws:glue:${Region}:${Account}:${ResourceType}/${ResourcePath}` and its
  decision `implicitDeny`, the aggregate; the verdicts above are the per-resource ones.
- **[Claude] Written with it**: the slice README's row for `project_access_portal`, runbook
  `redshift-connection.md` §G's paragraph for a subscribed product, the stage file's block (before it item 3,
  the pieces table) and its Status row, and `waiting-on-the-user.md`'s row. What follows is the apply from
  `main` after PR #339's merge, on the user's word.

## 2026-11-20 — 5.2's door applied from `main`

*Claude, the orchestrating session, on the user's "autorizo o apply no warehouse" in its chat, after the
merges of PR #339 (15:51:55 UTC) and PR #340 (15:52:10 UTC); as the infrastructure user, permission set
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (account Sandbox Account 1), with
`awsds-infra-prod` (account Production) for the aliased provider's account id. One AWS write, the apply.
Times are UTC.*

- **[user] The word**: *"autorizo o apply no warehouse"*, sent while the session waited on a new SSO
  login; the session read valid again at 15:56:16.
- **[Claude] The plan from `main`** at `7af1ec3d`, from 15:56:48, the slice initialised in the worktree
  (`gen-backend-hcl.py`, `gen-tfvars.py`, `init -backend-config=backend.hcl -input=false`), with
  `-input=false -var all_projects_tag_enabled=false -var data_transfer_role_enabled=false`, saved: *"Plan:
  0 to add, 1 to change, 0 to destroy."*, `aws_iam_policy.project_access_portal["avhvbqn37ty7m8"]` updated
  in place, its diff the two statements `ReadTheSubscribedProductsCatalog` and
  `LakeFormationVendsTheSubscribedProductsData` and nothing else.
- **[Claude] The other session told** before the apply: the pre-flight's session, the one peer on the
  machine, idle.
- **[Claude] The apply of the saved plan**, 15:57:30 to 15:57:40: *"Apply complete! Resources: 0 added, 1
  changed, 0 destroyed."* The policy `awsds-sandbox-warehouse-access-portal-avhvbqn37ty7m8` reads default
  version `v4`, updated at 15:57:39.
- **[Claude] The re-plan**, 15:58:02, the same switches: *"No changes. Your infrastructure matches the
  configuration."*
- **[Claude] `simulate-principal-policy` as `awsds-sandbox-warehouse-access-avhvbqn37ty7m8`**, about 15:58,
  one resource per call, `aws:RequestedRegion` and `aws:PrincipalArn` in the context: `allowed` for
  `glue:GetDatabase` on Sandbox's `database/glue_db_blerpkhn9nj7o0` and Production's `database/app_etl`, for
  `glue:GetTable` on Sandbox's `table/glue_db_blerpkhn9nj7o0/trades_notional` and Production's
  `table/app_etl/trades_notional`, and for `lakeformation:GetDataAccess` on `*`; `implicitDeny` for
  `glue:GetTable` on Production's `table/app_etl/some_other_table`, `glue:GetDatabase` on
  `database/other_db` and `glue:CreateTable` on `table/app_etl/trades_notional`, the negative controls; the
  organization allowing each. The IAM half of 5.2's door is open; Lake Formation's admission and the SQL
  grants stay 4.12's and the sitting's (the stage file's pieces table).

## 2026-11-20 — Release G placed in R1, and decision 27 (d)'s provider read

*Claude, in the session that regrouped the sittings (Stage 8's log, this day), with nothing up: the
Terraform registry's and GitHub's public APIs read at about 17:04 and 17:05, no AWS call. Times are UTC.*

- **[Claude] Release G** (decision 26 (b)) rides R1 (`promotion.md` §N.11.1 step 4), after `EXC-13`'s
  rotation and before 2026-12-17. 4.12's membership with `subscription-approver` and xxvi's portal half need
  neither the release nor anything up and come first (§N.6 item 3); 4.12's request and approval follow the
  release (item 6). Pass 5 to 5.3 is on §N.10's day 1, 5.4 on day 2.
- **[Claude] Decision 27 (d)'s provider**: the registry's newest `hashicorp/aws` is 6.73.0, published
  2026-11-11; `go.mod` at `v6.73.0` and on `main` both name `service/cloudwatchlogs` v1.90.2, below the
  v1.91.0 that `upstream-releases.md` watches for. `EXC-25` stands.

## 2026-11-20 — Release G's pre-flight with nothing up

*Claude, in the session that applied 6d decision 6 and Stage 17 decision 7 the same day, on the user's request to prepare every pending sitting before raising anything and to minimise the plan's running time (*"otimize o plano e faça todas as preparações necessárias para que o tempo necessário para executar o plano seja minimizado"*). As the infrastructure user with `InfrastructureAccess`, read-only, through `awsds-infra-staging` (account
Staging), `awsds-infra-prod` (account Production) and `awsds-infra-sandbox-1` (account Sandbox Account 1).
Times are UTC.*

- **[Claude] `./scripts/deploy-application.py staging --check` and `production --check`**, with
  `DOMAIN_ID` and `DOMAIN_REGION` set as the pipeline sets them: each exit 0, `deploy-staging` and
  `deploy-production` with their roles, subnets, security group, key and shared prefix read, and *"the
  caller is a member of the project"*.
- **[Claude] `./scripts/check-gitlab-mirror.py --plan`**: exit 0, `GM-1` to `GM-8` passing, the copy at
  `awsds/dev-env` `717d80b57541` of 2026-11-15, the Dockerfile's `NO_PROXY_LIST` and the account's list from
  a plan of `sandbox/egress/` at 73 entries, sha256 `61f1e1646df12c14` on both sides.
- **[Claude] Release G's gate, dry**: `pip-audit` 2.10.1 over each lock's runtime set (`uv export --frozen --no-dev`), an approximation of
  the gates' job, which `awsds/ci-gates` holds: *"No known vulnerabilities found"* for `app-etl` (one
  package), `app-ml`'s `code` (48) and `app-dbt` (78), at 20:36 UTC. The gate itself runs on the laptop
  the day of each tag, before the tag (Lesson 77).

## 2026-11-21 — 4.12's membership: the Governance Manager in `deploy-production` as `subscription-approver`

*Claude's hand on the user's word in chat, *"Autorizo a membership"*, through `awsds-infra-prod`
(Production, the infrastructure user with `InfrastructureAccess`), the project's owner, with the estate
down. The session the user opened in `awsds-workflows` was told before the write. Times are UTC.*

- **[Claude] The client**: the laptop's `aws-cli/2.37.12` has no `--user-created-designation-id`, so the
  call ran with botocore 1.44.5's DataZone model staged through `AWS_DATA_PATH`, whose help lists the
  option.
- **[Claude] The members before**: two groups `PROJECT_OWNER` and one user `PROJECT_CONTRIBUTOR`.
- **[Claude] The call**, 17:56:59 to 17:57:00: `create-project-membership` on `deploy-production` with the
  Governance Manager's user profile as `userIdentifier`, `--designation USER_CREATED_DESIGNATION
  --user-created-designation-id ahjm1h20oujxqo`. Exit 0, an empty body.
- **[Claude] The members after**: the same three, and the Governance Manager's user profile as
  `USER_CREATED_DESIGNATION` with `userCreatedDesignationId` `ahjm1h20oujxqo`.
- **Left of 4.12**: xxvi's portal half, read before the approval; after R1, `eighth-experimentation`'s
  request on the listing release G creates and the Governance Manager's approval in the portal.

## 2026-11-22 — R1: the warehouse secret's first rotation in Production, and GitLab up for release G

*Claude, in the session that drives R1 ([`runbooks/promotion.md`](../plan/runbooks/promotion.md) §N.11.1)
on the user's word in chat, *"sim, o R1 vai ser hoje"*, reading as `awsds-infra-prod` (account
Production, the infrastructure user with `InfrastructureAccess`) and `awsds-infra-sandbox-1`; the user's
acts are named. Times are UTC.*

- **[Claude] Step 1, the rotation with nothing up** (§N.8.3 step 1, `EXC-13`'s Production half).
  Production's trail on `redshift!awsds-prod-warehouse-dbadmin`: `RotationStarted` at 01:11:55;
  `PutSecretValue` into `AWSPENDING` by `AWSServiceRoleForRedshift` at 01:13:08; `UpdateSecretVersionStage`
  to `AWSCURRENT` by the same role, `CompleteRotation` `Succeeded` with *"Rotation completed"* and
  `RotationSucceeded` at 01:17:08; no `RotationFailed`. `describe-secret`, six reads from 02:00:15 to
  02:05:27: `LastRotatedDate` 01:17:08.980, `NextRotationDate` 2026-12-22 01:59:59, rotation enabled.
  Production held no workgroup: its last `DeleteWorkgroup` is of 2026-11-16 05:33, no `CreateWorkgroup`
  follows it, and `list-workgroups` answers none. The rotation started 48 minutes before the 01:59:59 that
  `NextRotationDate` named and succeeded with no workgroup, as Sandbox's first did on 2026-10-20; whether
  the database took the new password is step 5's reading.
- **[Claude] The poll that missed it**: a loop waiting for `LastRotatedDate` to contain `2026-11-22`
  matched none of its six reads, the CLI printing `2026-11-21T22:17:08.980000-03:00` in the laptop's zone
  (`SUP-435`). §N.8.3 step 1 now reads with `TZ=UTC`.
- **[Claude] `make status`** at 02:07:11: `production/vpn` and `production/proxy` up, `production/tooling`
  stopped, `sandbox/egress` up with 33 resources and `sandbox/probes` with 4, every other `[E]` slice down;
  Sandbox's JupyterLab and Code Editor apps up since 2026-11-21 20:07 and 20:08 (N.9's day 2).
- **[user] Step 2**: the tunnel up, the laptop's first handshake on the `t3.nano` tunnel host at 01:33:09
  (Stage 12's log); `make gitlab-up BUILD=1`, GitLab's host started at 02:09:39 and running with both
  status checks `ok` at 02:11:46, the deploy, test and build runners launched from 02:09:59 to 02:10:07.
- **[Claude] `production/tooling/` applied** at 02:12:56 on the user's word, *"autorizo o apply do
  tooling"*: Stage 12 2.2's alarm action, and `EXC-19` closed (Stage 12's log).
- **[Claude] Production read before release G's leg**: `app_etl_deploy_production_app_etl`, `_train` and
  `_warehouse` `READY`; `deploy-production` (`d7qcazihvr3s7k`) `ACTIVE`, a search for a data product it
  owns answering none; `app_etl`'s newest run `wITFYNHoLyyEsev`, of 2026-11-16 03:19:11. Inside one page
  `list-workflow-runs` orders runs by no time (`SUP-436`), and it carried `RunType` on every run in
  Sandbox, Staging and Production (`SUP-251`, read again).
- **[user] Step 3's backup by hand**, `sudo gitlab-backup create STRATEGY=copy` in a Session Manager
  shell on the host. **[Claude] read** at 03:00 in `awsds-prod-gitlab-backup`:
  `1795315677_2026_11_22_19.4.2_gitlab_backup.tar`, 15,708,160 bytes, uploaded at 02:48:08, `aws:kms`,
  expiring 2026-12-23 by the rule `expire-current-versions`; its release, 19.4.2, is `gitlab_ce_version`'s.
  The newest backup now leaves the bucket on 2026-12-23, where the one of 2026-11-16 leaves on 2026-12-17.
- **[user] Step 3's projects** by `sagemaker-application.md` §L's steps 1 to 6, as GitLab's local
  administrator: `awsds/app-ml` (id 7) at 02:50:58, `awsds/app-genai` (8) at 02:55:07 and `awsds/app-dbt`
  (9) at 02:56:40. **[Claude] read** through GitLab's API in the user's browser session at about 03:10: each
  private and empty; `main` protected, push and merge `Maintainers`, no force push; `v*` protected, create
  `Maintainers`; `awsds/data-scientists` a Developer and `awsds/deployment-managers` a Maintainer, no direct
  member; the runners 1 (`awsds-prod-runner`, untagged, `ref_protected`), 3 (`awsds-prod-runner-deploy`,
  `awsds-deploy`, `ref_protected`) and 4 (`awsds-prod-runner-test`, `awsds-test`, `not_protected`) linked,
  each still locked; `DOMAIN_ID` `dzd-d8yrvx1ko7im6o`, `DOMAIN_REGION` `us-west-2` and `DEV_PROJECT_NAME`
  `app-ml-dev`, `app-genai-dev` or `app-dbt-dev`, each protected and unmasked. `awsds/infrastructure`'s
  job-token allowlist, inbound enabled, holds the three beside `awsds/app-etl` and itself.
