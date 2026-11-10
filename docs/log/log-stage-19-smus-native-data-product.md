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
