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
