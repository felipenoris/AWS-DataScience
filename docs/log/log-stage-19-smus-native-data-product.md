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
