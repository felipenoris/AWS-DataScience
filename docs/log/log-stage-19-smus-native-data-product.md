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
