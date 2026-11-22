# Log — Stage 21 — Redshift tables and S3 objects as data products in SageMaker Unified Studio

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-21-redshift-s3-data-products.md`](../plan/stages/stage-21-redshift-s3-data-products.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-11-17 — the stage written from AWS's pages and the repository, with no AWS call

*Claude's sitting in a cloud session, no AWS call: AWS's pages read through a fetcher, recorded in
[`REFERENCES.md`](../REFERENCES.md) the same sitting.*

- **[user] The request**, in a cloud session's thread at 19:12 and 19:14 UTC, quoted whole in the stage
  file's "The premises": how to structure SageMaker Unified Studio, by AWS's recommendation, for publishing
  and sharing data products between teams; how Redshift meets the Glue Data Catalog and the SageMaker
  Catalog with its lineage; whether a Redshift table can be a data product by the standard path; which
  datasets the Glue Data Catalog holds; whether reading Redshift data requires a given compute, where a
  Parquet file on S3 leaves the engine free; whether the Glue Data Catalog holds images; and *"Se para
  responder estas perguntas for necessário exercitar no lab, planeje um novo stage do plano para isso."*
  The same thread had answered from 17:54 UTC why the portal's *Create table → Redshift table* failed in
  the institution's environment with *"Cannot find default IAM role on this cluster"* (code 30001, `IAM
  role ARN "none"`): the namespace holds no default IAM role, and the user changed nothing there (18:54
  UTC). The session held no AWS credential and made no apply and no portal act; it read the repository at
  `main` `7816fbe`, then `922c4d0`.
- **[Claude] The review of the repository**, recorded in the stage file's "The plan and the estate against
  the premises" and "0. What is already measured": D12, D13, D26 and D40; 5b, 6f and 6h; Stage 9 decision 5
  and its 9.5a; Stage 19's 0.6, decision 9 and verifications v to ix; `GOVERNANCE.md`, `SMUS.md`,
  `catalog.md`, `redshift-connection.md` and `promotion.md` §N.6; `./aws/warehouse.py` and
  `./aws/catalog.py`. The readings the design turns on:
  - no Redshift subscription target in any environment and no federated catalog in any account (Stage 19
    0.6, 2026-10-28);
  - the Sandbox namespace's default role, `awsds-sandbox-warehouse-exec`, holds no policy (5b decision 5),
    so the portal's *Create table → Redshift table* is expected to fail here on S3, not on a missing default
    role;
  - `test-experimentation` is in no map and 6h decision 8 is untaken; its (a), the wide tag, gives every
    project role the workgroup from a notebook or the Data API (6h, simulated 2026-10-18);
  - Stage 9 decision 5 took the datashare in Production on 2026-10-22 against the managed cluster data lake
    access creates, and 9.5a's reading is owed only if the federated catalog comes back;
  - the account's S3 Access Grants instance holds one location per project and no grant
    (`SMUS.md`, 2026-08-23);
  - the connection's `lineageSync` failed on every run read (`EXC-17`).
- **[Claude] AWS's pages, read 2026-11-17**, recorded in `REFERENCES.md` (two entries under "SageMaker and
  shared storage", one under "Data platform") and quoted in the stage file's "The user's questions,
  answered": SageMaker Unified Studio's pages on managed assets, the fulfilment of a Redshift and of a Glue
  asset, the Redshift and Glue data sources, data products, the S3 Object Collection and S3 Access Grants, a
  project's Redshift compute, Redshift lineage and the domain's organization; DataZone's
  `CreateSubscriptionTarget`; Lake Formation's and Redshift's pages on the federated catalog, its
  prerequisites and limits, and the RMS catalog; Glue's pages on tables, classifiers, formats, views and the
  Iceberg REST catalog; Athena's catalog registrations; Glue's, Redshift's and the lakehouse's pricing; S3
  Metadata.
- **[Claude] What the pages leave open or contradict**, each a step of the stage:
  - cross-Region subscriptions: the Glue and Redshift asset pages say none is supported, and the unmanaged
    asset's page supports Glue tables and views and Redshift tables and views across standard Regions with
    the blueprint enabled in both; written into `catalog.md` §S;
  - the compute behind data lake access: *"a managed Amazon Redshift cluster"* on the federated catalog's
    page, *"an Amazon Redshift managed serverless-workgroup"* on the RMS catalog's, *"a service-managed
    Amazon Redshift Serverless workgroup"* on Glue's pricing page; no page names its account or base
    capacity (decision 3, 4.5);
  - a Redshift subscription target for a project admitted by hand: no page, and `CreateSubscriptionTarget`'s
    reference names no Redshift type or form (decision 1, 2.4);
  - a Glue data source over a federated catalog: the catalog can be typed, and no page says its tables
    import, nor as which type (4.4);
  - an S3 Object Collection's grantee and how a subscriber reads it: no page (5.4, 5.5);
  - pages that answered nothing: the portal's page on creating a table, an empty stub in English and
    Japanese, with the guide's PDF failing; Lake Formation's page on accessing catalogs, a client error as
    `.md` and the guide's title alone as `.html`; What's New's search, which renders by script.
- **[Claude] 1.4's generator, run on the session's host** with Python's standard library: 20 PNG files of
  64 × 64, 177 to 180 bytes each and 3,580 in all, every chunk's CRC and each image's decompressed size
  checked, `file` reading the first as *"PNG image data, 64 x 64, 8-bit/color RGB, non-interlaced"*; 13
  labelled `quente` and 7 `fria`.
- **[Claude] The stage written**, decisions 1 to 3 put to the user and none taken; the indexes,
  `GENERAL_PLAN.md`'s route, `CLAUDE.md`'s Current position, the waiting list, `catalog.md` §S and
  `promotion.md` §N.6 item 9 amended in the same pull request.

## 2026-11-17 — decisions 1 to 3 taken, and the stage revised for them

*Claude's sitting in the same cloud session, no AWS call.*

- **[user] The order of the decisions**, at 21:47 UTC: *"Me apresente cada decisão necessária, uma de cada
  vez, com as opções e a recomendação"*. **[Claude]** The card that put the three together was withdrawn,
  and decision 1 went on a card of its own, recommending (a).
- **[user] The rule for the recommendations**, at 21:50 UTC: *"Revise as recomendações considerando que
  iremos exercitar o caminho sugerido pela AWS por padrão"*. **[Claude]** Decision 1's recommendation
  became (b), the workgroup AWS's pages name as a Redshift subscription's destination, its base capacity
  at the floor, on a new card; decisions 2 and 3 kept (a) and (b), already the forms AWS's pages document.
- **[user] Decision 1**, at 21:55 UTC, on the card *"Escolher quem assina a tabela Redshift no teste do
  Stage 21"*: *"b: workgroup próprio pelo blueprint"*.
- **[user] Decisions 2 and 3**, at 21:55 UTC: *"aceito as recomendações das decisões 2 e 3, considerando que
  é o caminho que a AWS documenta"*.
- **[Claude] The stage revised for the choices**, read against `docs/SMUS.md`'s `RedshiftServerless` row
  (category 3, *Never*) and its checklist for promoting a blueprint: 1.3 reads the blueprint's parameters
  and template; 1.5 writes its code behind variables that default to off; 2.4 is the consumer's workgroup
  by the blueprint, 2.5 to 2.7 the datashare-and-view shape between two namespaces, and 2.9 the
  workgroup's removal; 3.1 and 3.5 keep decision 2 (a) alone; 4.7 and verification xiii do not run;
  verification xx is added. The waiting list's decisions row is removed.

## 2026-11-18 — pass 1 with nothing up: 1.3's readings and 1.5's code

*Claude, a subagent of the orchestrating session, in that session's worktree. Read-only calls from the laptop
as the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` in `Sandbox Account 1`
and `awsds-infra-data` in `Data Governance Account`; the plans read the other members through their profiles.
AWS's pages through a fetcher, AWS's SMUS-IaC sample through `gh api`, the CLI's help and skeletons on the
laptop. Nothing applied and nothing written in AWS. Account ids are replaced by `<Sandbox Account 1>` and
`<Data Governance Account>`, the infrastructure user's address by `<infrastructure user>`. Times are UTC.*

- **[Claude] The asset types**, 00:39 to 00:41: `datazone search-types --managed --search-scope ASSET_TYPE`
  lists 24, the count of 2026-10-28, with every type Stage 19's log names that day. `get-asset-type` refuses
  Sandbox's caller, which `search-types` answers:

  ```
  An error occurred (AccessDeniedException) when calling the GetAssetType operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_InfrastructureAccess_59e5b26af457128d/<infrastructure user> is not authorized to perform: datazone:GetAssetType on resource: arn:aws:datazone:us-west-2:<Data Governance Account>:domain/dzd-d8yrvx1ko7im6o because no resource-based policy allows the datazone:GetAssetType action
  ```

  As `awsds-infra-data`: `RedshiftTableAssetType` revision 18, `RedshiftViewAssetType` 19 and
  `S3ObjectCollectionAssetType` 17, each requiring one form (`RedshiftTableForm` 7, `RedshiftViewForm` 8,
  `S3ObjectCollectionForm` 7) beside optional ones. The Redshift forms require `columns`, 1 to 1,600; the S3
  form requires `bucketArn` and references the S3 connection the asset came from.
- **[Claude] The consumer's environments and targets**, 00:40 to 00:41: `test-experimentation` holds
  `Tooling` (`bi356s1sacz0cw`), `test-experimentation-lakehouse` (`4zojr4rr6bmnww`) and two
  `create-datalake-database-env-…` on the same `DataLake` configuration, one `ACTIVE` and one
  `VALIDATION_FAILED`. `list-subscription-targets` returns `type: null` for every target; `get-subscription-target`
  answers it. The lakehouse environment's `ai0iw2p6vlxw5s` is `GlueSubscriptionTargetType`, database
  `glue_db_4zojr4rr6bmnww`, for the Glue table and view types, authorized to `abac:CURRENT_PROJECT`, its
  manage-access role the project role `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw`. `Tooling` carries a
  `BedrockModelSubscriptionTargetType` and a `BaseSubscriptionTargetType` (feature groups and model package
  groups), each authorized to the project role's ARN. No Redshift target; the other two environments hold none.
- **[Claude] The blueprint and its template**, 00:41 to 00:45: the domain lists 24 managed blueprints, the
  count of 2026-10-28.
  `RedshiftServerless` is `dlyaabb17hano0`, created 2026-05-13. Its template, read with `s3api get-object`
  through the `templateUrl`'s access point alias (an unsigned `curl` read 400), is
  `DataZone-Amazon-SageMaker-RedshiftServerlessDefault-prod-20250515.template.json`, 10,532 bytes,
  `LastModified` 2026-11-13T19:43:40Z:
  - `redshiftBaseCapacity` and `redshiftMaxCapacity` are `Number`s with no `AllowedValues`, defaults 128 and 0.
    The workgroup gets `BaseCapacity` only when the base is not 128, `MaxCapacity` only when the maximum is
    not 0, and `PricePerformanceTarget` `{Level: 50, Status: ENABLED}` only when the base is 128;
  - the namespace's `DefaultIamRoleArn` and only `IamRoles` entry are `userRoleArn`; its `KmsKeyId` and the
    managed admin secret's key are `kmsKeyArn` when DataZone passes one; `ManageAdminPassword` follows
    `provisionManagedSecret`;
  - the workgroup imports `privateSubnets-<project>-<scope>` and `securityGroup-<project>-<scope>`, which the
    project's `Tooling` stack exports (`cloudformation list-exports`: two subnets and `sg-05e52373c14288c22`
    for `test-experimentation`, beside `kmsKeyArn-4gqfau9xuo6e4w-dev`, the key aliased
    `awsds-sandbox-project`); `PubliclyAccessible` false; `search_path` `project, $user, public`;
  - `datazoneEnvironmentEnvironmentId`, `datazoneEnvironmentProjectId` and `userRoleArn` have no default and
    are DataZone's; `createRedshiftResources` defaults to true, `connectToRMSCatalog` to false.

  The blueprint's ten user parameters are optional and not editable, and four defaults differ from the
  template's: `redshiftMaxCapacity` `"512"` (template 0), `provisionManagedSecret` `"true"` (false), and the
  names `redshift-serverless-workgroup` and `redshift-serverless-namespace` (`datazone-workgroup`,
  `datazone-namespace`). `redshiftBaseCapacity` is `"128"` in both; `connectionName` is `project.redshift`.
  `isUpdateSupported` is true for both capacities.
- **[Claude] The key and the roles**, 00:45 to 00:53: the adminguide's key-permissions page names one Redshift
  statement, `RedshiftCreateGrantKmsPermissions`: `kms:CreateGrant` for the provisioning role through
  `redshift-serverless.*.amazonaws.com`, on a key in the caller's account. The provisioning role's
  `SageMakerStudioProjectProvisioningRolePolicy` (v86, created 2026-11-17T21:17:09Z) allows `kms:CreateGrant`
  through `airflow`, `neptune-graph` and `s3vectors` alone; its `RSMng`, `RedshiftCreate` and `RssMng`
  statements allow a namespace's and a workgroup's create, read, update and delete, `RssMng`'s
  `UpdateWorkgroup` on resources tagged `AmazonDataZoneProject`, which the root's
  `DenyRedshiftCostGuardTamperingExceptInfrastructure` denies to every role but `InfrastructureAccess`.
  `AmazonDataZoneRedshiftManageAccessRolePolicy` (v5, 2026-02-12) allows `AuthorizeDataShare`,
  `DescribeDataShares` and `AssociateDataShareConsumer` on datashares named `datazone*`, the Data API on
  workgroups, and a workgroup's or namespace's create and delete only when called via Glue or Lake Formation;
  the SageMaker (v4) and Glue (v18) manage-access policies carry no `redshift:` action. The consumer's project
  role trusts `redshift.amazonaws.com` and `redshift-serverless.amazonaws.com` (an `sts:ExternalId` on
  `dbuser:*/*`), carries `awsds-sandbox-project-boundary` and the tag
  `RedshiftDbUser=user-project@4gqfau9xuo6e4w`. `SageMakerStudioProjectUserRolePolicy` (v77) reads and writes
  a secret only when its `AmazonDataZoneProject` tag is the caller's project (`AllowGetSecretForRedShift`).
- **[Claude] The producer's connection**, 00:46 to 00:48: `eighth-experimentation` holds eleven connections. Its
  Redshift one, `redshift-serverless.redshift` (`axsiuoykrswosw`), names the workgroup
  `awsds-sandbox-warehouse`, database `dev`, no secret, the access role
  `awsds-sandbox-warehouse-access-avhvbqn37ty7m8`, and `lineageSync` enabled on `cron(43 3 * * ? *)`, job
  `ayya3b95j0zvo0`. The job's five latest runs, 2026-11-13 to 2026-11-17 at 03:44, are all `FAILED`, the
  newest processing no query: *"Redshift endpoint doesn't exist in this region. (Service: RedshiftData, Status
  Code: 400, …)"*.
- **[Claude] S3 Access Grants**, 00:48: the instance `default`, created 2026-08-22, with four locations: the
  bucket `awsds-sandbox-lake` (2026-08-26, role `awsds-sandbox-lake-access`) and the project prefixes of
  `eighth-experimentation` (2026-08-23), `test-experimentation` (2026-10-15) and `app-etl-dev` (2026-11-14),
  each with its project role. Five `READWRITE` grants to IAM principals: four on the lake's per-group prefixes
  (three persona permission sets and `eighth-experimentation`'s project role) and one to `DataScientistAccess`
  on `eighth-experimentation`'s `shared/`. None from a subscription.
- **[Claude] The namespace's road into the Glue Data Catalog**, 00:44 to 00:52, from AWS's pages and the CLI's
  help: `register-namespace` takes `ServerlessIdentifier={NamespaceIdentifier,WorkgroupIdentifier}` and exactly
  one consumer account; Redshift's page spells the key `NamespaceIdentifer`, and Lake Formation's grant example
  passes `--cli-input-cli-json`. Lake Formation's sequence is `describe-data-shares`,
  `associate-data-share-consumer` to `arn:aws:glue:<region>:<account>:catalog`, `register-resource` on the
  datashare (*"This is a mandatory step"*), then `glue create-catalog` with `FederatedCatalog`
  `{Identifier: <datashare ARN>, ConnectionName: "aws:redshift"}` and, for data lake access,
  `CatalogProperties.DataLakeAccessProperties`. The deletion page names `glue delete-catalog` alone. The data
  transfer role trusts `glue.amazonaws.com` and `redshift.amazonaws.com`; its documented policy allows
  `glue:GetCatalog`, `glue:GetDatabase`, `kms:GenerateDataKey` and `kms:Decrypt`, no S3 action, though the page
  says the role moves data to and from S3.
- **[Claude] The console's enable wizard**, the checklist's step 4, is unread: this sitting had no console. It
  is the user's act before 2.4.
- **[Claude] 1.5's code**, written by 01:12, each half behind `redshift_serverless_enabled`, default false:
  - `terraform-modules/sagemaker-prereqs/`: the switch (`variables.tf`); `local.configured_blueprints`,
    `RedshiftServerless` beside `var.blueprint_names`, which the configuration and its grant iterate
    (`blueprints.tf`) and the roster guard reads (`data.tf`); `RedshiftCreateGrantKmsPermissions` for the
    provisioning role (`kms.tf`); `AmazonDataZoneRedshiftManageAccessRolePolicy` on the manage-access role
    (`roles.tf`);
  - `terraform-live/data-governance/governance/`: the switch (`variables.tf`); `local.admitted_blueprints`,
    category 1 plus `RedshiftServerless` last, so no other environment's `deployment_order` moves, and its
    overrides `redshiftBaseCapacity` and `redshiftMaxCapacity` at `"4"`, not editable (`locals.tf`); the
    blueprint lookup and the profile's precondition read `admitted_blueprints` (`data.tf`, `profiles.tf`);
  - `terraform fmt`, the module's `validate`, `tflint` on both, `checkov` (36 passed and 0 failed on the module,
    72 and 0 on the slice), `check-tf-conventions`, `check-identifiers` and `slices.py check` green.
- **[Claude] The plans**, 01:14 to 01:19, `-input=false`: `sandbox/sagemaker/` as `awsds-infra-sandbox-1`, its
  `source` pointed at the module's local path (Recipe B), saved: *"No changes. Your infrastructure matches the
  configuration."*, 43 no-ops. With `redshift_serverless_enabled = true` written into `main.tf`, unsaved:
  *"Plan: 3 to add, 1 to change, 0 to destroy."*, the `RedshiftServerless` configuration, its
  `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant, the policy attachment, and the key's policy in place. `main.tf` was
  put back, compared byte for byte with its copy, and the slice re-initialised at
  `?ref=sagemaker-prereqs-v0.11.0`, its lock file unchanged. `data-governance/governance/` as
  `awsds-infra-data`, saved: *"No changes. …"*, 23 no-ops; with `-var redshift_serverless_enabled=true`,
  unsaved: *"Plan: 0 to add, 1 to change, 0 to destroy."*, `experimentation` gaining `RedshiftServerless`,
  `ON_DEMAND`, order 14, blueprint `dlyaabb17hano0`, both overrides `"4"` and not editable.
- **[Claude] The tag**, read at 01:46: `git ls-remote --tags origin 'sagemaker-prereqs-v*'` lists
  `sagemaker-prereqs-v0.11.0` as the latest, so the next is `sagemaker-prereqs-v0.12.0`. Recipe B's commits,
  the tag and `sandbox/sagemaker/`'s pin and switch are the orchestrating session's.
- **[Claude] The commands of passes 2 to 5**, written from these readings. A ⚡ marks a write Claude runs on the
  user's word alone; every other command of Claude's is a read. The placeholders in angle brackets are the
  sitting's values; the workgroup's and namespace's names assume the blueprint's defaults reach the stack,
  whose parameters 2.4 reads.

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

  Pass 2:

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
  # 2.4 ⚡ the other sessions told first, sandbox/sagemaker/ at sagemaker-prereqs-v0.12.0; this order on
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

  Pass 3:

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
  CREATE TABLE lab.trades_from_lake AS SELECT * FROM awsdatacatalog.<project database>.trades_notional;
  ```

  Pass 4:

  ```bash
  # 4.1 ⚡ Recipe D's order: each object alone, read back for IAMAllowedPrincipals before the next
  NSID='ServerlessIdentifier={NamespaceIdentifier=awsds-sandbox-warehouse,WorkgroupIdentifier=awsds-sandbox-warehouse}'
  aws redshift register-namespace --namespace-identifier "$NSID" --consumer-identifiers "$A" --profile $S
  aws redshift describe-data-shares-for-consumer --consumer-arn "arn:aws:glue:us-west-2:$A:catalog" \
    --profile $S
  DS='<the datashare ARN listed, ending /ds_internal_namespace in Lake Formation's example>'
  aws redshift associate-data-share-consumer --data-share-arn "$DS" \
    --consumer-arn "arn:aws:glue:us-west-2:$A:catalog" --profile $S
  aws lakeformation register-resource --resource-arn "$DS" --profile $S
  aws glue create-catalog --name stage21_warehouse --catalog-input "$(jq -cn --arg ds "$DS" '{
    Description: "Stage 21: the Sandbox warehouse namespace", CreateDatabaseDefaultPermissions: [],
    CreateTableDefaultPermissions: [], FederatedCatalog: {Identifier: $ds, ConnectionName: "aws:redshift"}}')" \
    --profile $S
  aws glue get-catalogs --parent-catalog-id "$A:stage21_warehouse" --recursive --profile $S
  aws lakeformation list-permissions --resource "{\"Catalog\": {\"Id\": \"$A:stage21_warehouse\"}}" \
    --profile $S
  # 4.2 ⚡ the table's catalog id as 4.1's reads give it
  aws lakeformation grant-permissions --principal \
    "DataLakePrincipalIdentifier=arn:aws:iam::$A:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c" \
    --resource "{\"Table\": {\"CatalogId\": \"$A:stage21_warehouse/sandbox\", \"DatabaseName\": \"lab\",
      \"Name\": \"trades_hot\"}}" --permissions DESCRIBE SELECT --profile $S
  # 4.3 and 4.6 the session's identity, and the compute
  q "select user_id, query_id, start_time, query_text from sys_query_history
     where start_time > '<the read>' order by start_time"
  # 4.5 ⚡ the transfer role in sandbox/warehouse/ behind its variable, applied for the sitting: the page's
  # trust (glue, redshift) and policy (glue:GetCatalog, glue:GetDatabase, kms:GenerateDataKey, kms:Decrypt).
  # The update passes the whole input get-catalog returned with DataLakeAccessProperties added: whether
  # UpdateCatalog drops what it is not passed is unread (Lesson 60).
  aws glue get-catalog --catalog-id "$A:stage21_warehouse" --profile $S
  aws glue update-catalog --catalog-id "$A:stage21_warehouse" --catalog-input '<that input, with
    CatalogProperties.DataLakeAccessProperties = {DataLakeAccess: true, DataTransferRole: <its ARN>}>' \
    --profile $S
  aws glue get-catalog --catalog-id "$A:stage21_warehouse" --profile $S    # the managed compute, its status
  aws redshift-serverless list-workgroups --profile $S
  aws redshift describe-clusters --profile $S
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateCluster \
    --start-time <the switch> --profile $S                  # a refusal by DenyRedshiftProvisionedClusters
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateWorkgroup \
    --start-time <the switch> --profile $S
  # 4.8 ⚡ in the sitting, each read back absent: data lake access off by the same update, then the catalog.
  # The deletion page names the catalog's delete alone; the order after it is 4.1's reversed.
  aws glue delete-catalog --catalog-id "$A:stage21_warehouse" --profile $S
  aws lakeformation deregister-resource --resource-arn "$DS" --profile $S
  aws redshift disassociate-data-share-consumer --data-share-arn "$DS" \
    --consumer-arn "arn:aws:glue:us-west-2:$A:catalog" --profile $S
  aws redshift deregister-namespace --namespace-identifier "$NSID" --consumer-identifiers "$A" --profile $S
  # then sandbox/warehouse/'s transfer-role variable off, planned and applied
  ```

  Pass 5:

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
  SELECT * FROM (VALUES ...) AS t (object_key, tom, width, height, size_bytes);
  ```
- **[Claude, the orchestrating session] 1.5's Recipe B**, 02:01 to 02:05: commit `e9f85352`, the module
  alone, its hooks run with `pre-commit run --files` while a subagent's edits stood unstaged in the worktree;
  `git ls-remote` read `sagemaker-prereqs-v0.11.0` as origin's newest, so the tag `sagemaker-prereqs-v0.12.0`,
  pushed alone with the branch and read back on origin at `e9f85352`; `sandbox/sagemaker/` moved to it with
  its switch in `d52604a1`. `terraform init` downloaded the tag, and `sandbox/sagemaker/` and
  `data-governance/governance/` planned *"No changes. Your infrastructure matches the configuration."* with
  the switches off. `SUP-377` (`GetAssetType`) and `SUP-378` (the template's sentinels) written from 1.3's
  readings, and a dated reading appended to `SUP-193`.

## 2026-11-18 — the commands of passes 2 to 5 copied into the stage file

*Claude, a subagent of the orchestrating session, on the laptop, no AWS call.*

- **[Claude] The copy**: the eight fenced blocks of the bullet *The commands of passes 2 to 5*, in the entry
  of 2026-11-18 above, copied into the stage file after each pass's steps, each pass with a lead in the
  plan's voice; the block of variables opens pass 2's commands, and passes 3 to 5 run in a shell that ran
  it. The stage file's `Status` row and step 1.3 point at the passes. A script compared each copy with the
  entry's block, de-indented: identical but for the two changes below.
- **[Claude] zsh**: the eleven `$A` a colon follows, all in pass 4, braced: `${A}:catalog`,
  `${A}:role/…`, `${A}:stage21_warehouse`. In zsh 5.9 on the laptop, with a stand-in value `acct`,
  `"glue:$A:catalog"` printed `glue:acctatalog`, `$A:role/x` printed `acctole/x`, and
  `"$A:stage21_warehouse"` failed with *"bad substitution"*, exit 1; each braced form printed the account,
  the colon and the word (Lesson 84). No other parameter in the blocks is followed by a colon.
- **[Claude] English identifiers**: step 1.4's generator labels an image `warm` or `cold`, where it wrote
  `quente` and `fria`, and names the column `tone`, where it named `tom`, as does pass 5's `CREATE TABLE`.
  The generator, run on the laptop with Python 3.9.6: 20 files, 13 `warm` and 7 `cold`, the split the
  first entry of this log records under the old labels.
- **[Claude]** The entry of 2026-11-18 above keeps the first version, with the unbraced `$A` and the column
  `tom`. Cutting it from the log is the user's call.

## 2026-11-18 — 4.5's data transfer role written and planned, not applied

*Claude, a subagent of the orchestrating session, in a worktree of its own, on the laptop with nothing up;
the orchestrating session pushed the branch, opened the pull request and wrote the stage file's commands.
The infrastructure user, permission set `InfrastructureAccess`, through `awsds-infra-sandbox-1`. Times are
UTC.*

- **[Claude] The code**, in the commit of 6h decision 8 (a)'s switch: `sandbox/warehouse/`'s
  `data_transfer_role_enabled`, default false, creates `awsds-sandbox-warehouse-data-transfer`, trusted by
  `glue.amazonaws.com` and `redshift.amazonaws.com` with no condition, as AWS's prerequisites page writes
  it; `glue:GetCatalog` and `glue:GetDatabase` on the account's catalog and on `stage21_warehouse`, its
  children and their databases (`federated_catalog_name`, validated to `^[a-z0-9_-]+$`); `kms:GenerateDataKey`
  and `kms:Decrypt` on the account data key; the output `data_transfer_role_arn`.
- **[Claude] The plans**: with `-var data_transfer_role_enabled=true`, 16:42:17, *"Plan: 2 to add, 0 to
  change, 0 to destroy."*, the role and its inline policy; with both switches, 16:56:01, *"Plan: 2 to add, 1
  to change, 0 to destroy."*; with both off, *"No changes."*
- **[Claude] What the code could not read**: the data key's policy delegates to IAM only through Redshift
  Serverless (`AllowRedshiftServerlessViaServiceInThisAccount`), so a write by the managed compute through S3
  is refused until `sandbox/data/`'s key policy names the role, AWS's `GenerateDataKeyDecryptDataTransferRole`
  and a D31 widening; and `UpdateCatalog` takes a whole `CatalogInput`, so 4.5 reads `get-catalog` first.
  Step 4.5 and pass 4's commands name the variable, the saved plan and the output, and 4.8's teardown plans
  the slice without it.
- **[Claude] The pull request**: [#323](https://github.com/felipenoris/AWS-DataScience/pull/323).

## 2026-11-19 — passes 2 to 4's pre-flight, with nothing up

*Claude, in the pre-flight session of the Sandbox warehouse sitting started by the orchestrating session,
as the infrastructure user, permission set `InfrastructureAccess`, through `awsds-infra-sandbox-1`
(account Sandbox Account 1) and `awsds-infra-data` (account Data Governance). Reads and plans only, no
apply and no AWS write. Times are UTC.*

- **[Claude] The plans from `main`**, each `-input=false`, saved and not applied:

  | UTC | Slice | Variables | Plan |
  |---|---|---|---|
  | 21:44:37 | `sandbox/warehouse/` | `data_transfer_role_enabled=true` | `2 to add` |
  | 21:52:31 | `sandbox/sagemaker/` | none | `No changes` |
  | 21:53:01 | `sandbox/sagemaker/` | `redshift_serverless_enabled=true` | `3 to add, 1 to change, 0 to destroy`: the `RedshiftServerless` blueprint configuration, its policy grant, `AmazonDataZoneRedshiftManageAccessRolePolicy` on the manage-access role; the project key's policy |
  | 21:53:54 | `data-governance/governance/` | none | `No changes` |
  | 21:54:23 | `data-governance/governance/` | `redshift_serverless_enabled=true` | `0 to add, 1 to change, 0 to destroy`: `awscc_datazone_project_profile.this["experimentation"]` |

  The counts are the ones the stage's commands carry.
- **[Claude] Two corrections made in place in the stage file**: pass 2's raise is one `make up ENV=sandbox
  GROUPS=redshift`, which raises `sandbox/egress/` with the group, the compute and `sandbox/probes/`,
  where the text had a separate `ONLY=egress` first; and 4.5's and 4.8's plans of `sandbox/warehouse/` name
  `all_projects_tag_enabled` beside `data_transfer_role_enabled`, since a plan naming one switch takes the
  other at its default and 6h decision 8 (a)'s tag may stand (Lessons 51 and 69).
- **[Claude] What `make down` and `make status` do not see**: the consumer's workgroup (decision 1 (b)) and
  the managed compute of decision 3 (b) are no slice's, and `make status` reads no Redshift workgroup, so
  the block closes with `list-workgroups`, `describe-clusters` and `./aws/warehouse.py`'s `WH-8`.
- **[Claude] The block written**: "The Sandbox warehouse sitting: passes 2 to 4 in order" in the stage
  file, after the close and before the verifications.

## 2026-11-20 — Pass 5 on the warehouse sitting's day 2, and the switches re-planned

*Claude, in the session that regrouped the sittings (Stage 8's log, this day), with nothing up. Plans as the
infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (account Sandbox Account 1)
and `awsds-infra-data` (Data Governance), from `origin/main` `30855d92`'s tree, 17:10:43 to 17:13:42; no AWS
write. Times are UTC.*

- **[Claude] The switches**, each default *"No changes."*: `sandbox/sagemaker/` with
  `redshift_serverless_enabled=true` *"Plan: 3 to add, 1 to change, 0 to destroy."*;
  `data-governance/governance/` with the same *"Plan: 0 to add, 1 to change, 0 to destroy."*;
  `sandbox/warehouse/` with `data_transfer_role_enabled=true` *"Plan: 2 to add, 0 to change, 0 to destroy."*
  and with `all_projects_tag_enabled=true` *"Plan: 0 to add, 1 to change, 0 to destroy."*
- **[Claude] Pass 5** follows passes 2 to 4 on `promotion.md` §N.10's day 2 (§N.10.4), a space in each
  project.
- **[Claude] The stage file's commands and rollback aligned**: 3.3 reads the link 4.12 read; both plans of
  `sandbox/warehouse/` take the wide tag from `TAG`, `false` while 6h decision 8 (a)'s tag is per sitting;
  the drops name the view `lab.trades_hot_by_desk` first, then `lab.trades_hot_daily`,
  `lab.trades_hot_by_day`, `lab.trades_from_lake` and `lab.trades_hot`; 6h decision 3's sentence says it was
  done 2026-11-19.

## 2026-11-22 — 4.5's write path taken, decision 4 (b), and 1.3's wizard half

*Claude, in the session "Stage 21" started by the orchestrating session of `promotion.md` §N.9's day 2, in a
worktree of its own, on the laptop with the environment up. Reads and plans as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (account Sandbox Account 1); AWS's prerequisites page
through a fetcher. No apply and no AWS write. The question was asked in Portuguese and is translated here;
the user's answer is quoted as given. Account ids are replaced by `<Sandbox Account 1>`. Times are UTC.*

- **[Claude] The blueprint before the wizard**, 01:50:19: `get-environment-blueprint` on `dlyaabb17hano0`
  reads `RedshiftServerless`, `createdAt` and `updatedAt` 2026-05-13T21:31:31Z, and the ten user parameters
  1.3 recorded, each optional and not editable, with the same defaults. `get-environment-blueprint-configuration`
  answers:

  ```
  aws: [ERROR]: An error occurred (ResourceNotFoundException) when calling the GetEnvironmentBlueprintConfiguration operation: EnvironmentBlueprintConfiguration for domainId dzd-d8yrvx1ko7im6o, accountId <Sandbox Account 1> and environmentBlueprintId dlyaabb17hano0 is not present
  ```

  `list-environment-blueprint-configurations` lists 14 configurations, `RedshiftServerless` not among them;
  IAM lists 57 roles and 10 customer managed policies.
- **[Claude] AWS's page**, `redshift-ns-prereqs.html`, read again: the key policy for *"a customer managed key
  to encrypt the data in the Amazon Redshift cluster/namespace"* holds four statements,
  `RedshiftAllowAccessPolicy`, `RedshiftServerlessAllowAccessPolicy`, `DirectMetadataAccess` and
  `GenerateDataKeyDecryptDataTransferRole`. The last names the data transfer role directly, with
  `kms:GenerateDataKey` and `kms:Decrypt` under `kms:ViaService` S3. The page shows no update date.
- **[Claude] The question**, asked in the chat after the wizard's route: (a) reads alone, the key policy
  unchanged, a write through S3 refused and its wording the reading, so 4.6's Athena read through data lake
  access likely refused by this estate's key; (b) the key policy names the role for one sitting, AWS's
  statement behind a switch off by default, applied after the role and removed before it, a fourth reader of
  the account data key whose identity policy holds no S3 action. Recommended (b), the stage file holding no
  explicit recommendation, by the rule of 2026-11-17, P1 and decision 3 (b)'s measured Athena read.
- **[user] The answer**: *"Ampliar na sessão"*, decision 4 (b).
- **[Claude] The code**: `sandbox/data/`'s `data_transfer_key_statement_enabled`, default false
  (`variables.tf`), appends `GenerateDataKeyDecryptDataTransferRole` to `additional_data_key_policy_statements`
  through `concat` (`main.tf`): the principal `awsds-<env>-warehouse-data-transfer`, derived from the
  convention as `lake_access_role_arn` is, `kms:GenerateDataKey` and `kms:Decrypt`, `kms:ViaService`
  `s3.<region>.amazonaws.com`. The `consumer-data` module is untouched.
- **[Claude] The plans**, from the worktree after `init` (the lock file unchanged, `hashicorp/aws` 6.62.0),
  each `-input=false` with a full refresh, saved to a scratch folder and not kept for the sitting:

  | UTC | Variables | Plan |
  |---|---|---|
  | 02:13:27 to 02:13:44 | none | *"No changes. Your infrastructure matches the configuration."* |
  | 02:13:50 to 02:14:02 | `data_transfer_key_statement_enabled=true` | *"Plan: 0 to add, 1 to change, 0 to destroy."*: `module.consumer_data.module.data_key.aws_kms_key.this` updated in place, its policy gaining the statement with the principal `arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-warehouse-data-transfer`, the three statements before it unchanged |
- **[Claude] The text that follows**: in the stage file, steps 4.5 and 4.8, pass 4's commands (the statement
  planned and applied after the role's output, and off before the role at 4.8), the sitting's block, the
  rollback, decision 4 and the `Consumes` row; `sandbox/warehouse/`'s `iam.tf` comment and README row;
  `consumer-data`'s README rows; `promotion.md` §N.10.1 and §N.10.4; the row in `waiting-on-the-user.md`
  removed.
- **[Claude] The template object**, about 02:20: `s3api head-object` on the `templateUrl`'s object through its
  access point alias reads `LastModified` 2026-11-21T01:19:23Z, `ContentLength` 10532 and `ETag`
  `"d516acd3183d361cf3b92a12ec19dd95"`, where 1.3 read `LastModified` 2026-11-13T19:43:40Z and 10,532 bytes on
  2026-11-18; the blueprint's `updatedAt` stays 2026-05-13T21:31:31Z (`SUP-361`).
- **[user] The wizard**, opened in the DataZone console as the infrastructure user with `InfrastructureAccess`
  in Sandbox Account 1, in a browser profile of its own, by the route this session gave (*Associated
  domains*, `awsds-studio`, *Blueprints*, `RedshiftServerless`, *Enable*), and left by **Cancel**. Reported in
  Portuguese and translated here; every label is as posted. The screen *Enable RedshiftServerless* offers
  **Provisioning role**, *Create and use a new service* or *Use an existing service role*, and **Manage Access
  role**, *Create and use a new service role* or *Use an existing service role*. *Create* shows no name for
  the role it would create, and *Use an existing* lists many names.
- **[Claude] The console's calls**, read in Sandbox's trail (DataZone in `us-west-2`, IAM in `us-east-1`), the
  browser's user agent apart from the CLI's and Terraform's: the domain's page from 02:28:29 (`ListDomains`,
  `GetDomain`, `ListEnvironmentBlueprints`, `ListEnvironmentBlueprintConfigurations`, `ListPolicyGrants` on
  `Tooling`'s configuration, `GetDomainUnit` on the root unit); the blueprint's page at 02:29:07
  (`GetEnvironmentBlueprint` on `dlyaabb17hano0`); the wizard at 02:29:14, with `GetEnvironmentBlueprint`,
  `iam:ListRoles` carrying `maxItems` 1000 and no `pathPrefix`, `GetDomainUnit` on the root unit and
  `ListDesignations`; the blueprint's page again at 02:32:12, the last console call at 02:32:13. No write:
  `PutEnvironmentBlueprintConfiguration`, `DeleteEnvironmentBlueprintConfiguration`, `CreatePolicyGrant` and
  `DeletePolicyGrant` return no event since 01:50 in Sandbox Account 1 or in Data Governance, and IAM's
  `CreatePolicy`, `PutRolePolicy` and `CreateServiceLinkedRole` none. The one `CreateRole` and
  `AttachRolePolicy`, at 02:02:39, are DataZone's environment deployer's (below).
- **[Claude] The blueprint after**, 02:33:12: `get-environment-blueprint` unchanged (`updatedAt` and the ten
  user parameters); `get-environment-blueprint-configuration` answers the same *"is not present"*; 14
  configurations with the same identifiers and `updatedAt`s; 10 customer managed policies. IAM lists 58 roles,
  the one more `AmazonBedrockFlowServiceRole-5er1gtql9ewbgw`, created 2026-11-22T02:02:39Z by
  `awsds-sandbox-smus-provisioning` in an `AmazonDataZoneEnvironmentDeployer-…` session that
  `datazone.amazonaws.com` invoked: an environment's deployment before the wizard opened.
- **[Claude] The form against `sagemaker-prereqs-v0.12.0`: the checklist's step 4 closes with no change.**
  `blueprints.tf` names `provisioning_role_arn` (`awsds-sandbox-smus-provisioning`) and
  `manage_access_role_arn` (`awsds-sandbox-smus-manage-access`) on every configured blueprint,
  `RedshiftServerless` included while `redshift_serverless_enabled` is true, and 1.5 attaches
  `AmazonDataZoneRedshiftManageAccessRolePolicy` to that manage-access role. The form shows no regional
  parameter, so nothing joins the `VpcId`, `Subnets` and `AZs` every configuration sends. Unlike `MLflowApp`'s
  form of 2026-10-18, it asks for a manage-access role and names no role it would create. The report holds no
  authorized-domain-units section; the console read the root unit and its designations as the wizard opened,
  the section `MLflowApp`'s form showed, which `grants.tf`'s grant on the root unit answers (inferred).
- **[Claude] The text that follows**: the stage file's `Status`, step 1.3 and the sitting's block;
  `docs/SMUS.md`'s `RedshiftServerless` row; `promotion.md` §N.10.1; the 1.3 row in `waiting-on-the-user.md`
  removed, with its mention in the Warehouse row.

## 2026-11-22 — pass 4's plans name 6h's standing tag

*Claude, in the same session, with no AWS call: 6h's session's readings relayed by its message, and its
branch, [pull request #363](https://github.com/felipenoris/AWS-DataScience/pull/363), read with `git`.*

- **[6h's session, by message] 6h decision 8 (a)'s window taken standing on 2026-11-22**, open and not
  applied: `test-experimentation` joins `sandbox/warehouse/`'s `projects`, and `all_projects_tag_enabled`
  is true by default. Its plans from its branch: `all_projects_tag_enabled=false` stops with `Error: Invalid
  value for variable`; both switches true, `9 to add, 2 to change, 0 to destroy`; the tag true and the
  transfer off, `7 to add, 2 to change, 0 to destroy`. After its apply the transfer plan would read `2 to
  add`, unmeasured.
- **[Claude] Read from the branch**: the apply is the warehouse sitting's 6h step 7 on `promotion.md`
  §N.10's day 1, from `main` after the merge, following 5.1's before half. 6h's 5.2b reads
  `test-experimentation`'s notebook through the direct door of `redshift-connection.md` §J and creates no
  portal connection, so pass 2's consumer holds no Redshift connection to the warehouse and its
  subscription target is unchanged.
- **[Claude] The text that follows**: pass 4's `TAG=true`, with a stop on a plan reading 6h's `9 to add, 2
  to change`; step 4.5 and its commands from a `main` that holds pull requests #323 and #363; 0.2, the
  premise row of 6h decision 8, decision 1's wording (it turns the switch on nowhere) and the 6h bullet.
  Decision 1's open case, a project that adds the existing workgroup in the portal, needs no further
  admission from day 1 and stays unmeasured.

## 2026-11-22 — passes 2 and 4's plans read again after pull request #369

*Claude, in the orchestrating session of `promotion.md` §N.9's day 2, with nothing up: read-only plans
with `-input=false`, Terraform 1.17.2, from 06:26 to 06:32 UTC. Nothing was saved or applied.*

- **[Claude] The trees**: `sandbox/sagemaker/` from the branch's merge of `origin/main` at `82edff32`,
  which pins `sagemaker-prereqs-v0.14.0` since #369; `data-governance/governance/`, `sandbox/data/` and
  `sandbox/warehouse/` from `86748b34`, whose files in those slices #369 did not change.
- **[Claude] `sandbox/sagemaker/`** (`awsds-infra-sandbox-1`): *"No changes."*; with
  `redshift_serverless_enabled=true`, *"Plan: 3 to add, 1 to change, 0 to destroy."*: the
  `RedshiftServerless` blueprint configuration, its `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant, the manage
  access role's `AmazonDataZoneRedshiftManageAccessRolePolicy` attachment, and the project key updated in
  place. 2.4's comment named `v0.12.0` and names `v0.14.0`.
- **[Claude] `data-governance/governance/`** (`awsds-infra-data`): *"No changes."*; with
  `redshift_serverless_enabled=true`, *"Plan: 0 to add, 1 to change, 0 to destroy."*, the profile
  `experimentation`.
- **[Claude] `sandbox/data/`**: *"No changes."*; with `data_transfer_key_statement_enabled=true`, *"Plan: 0
  to add, 1 to change, 0 to destroy."*, the data key's policy (decision 4 (b)).
- **[Claude] `sandbox/warehouse/`**: with both switches true, *"Plan: 9 to add, 2 to change, 0 to
  destroy."*; with the tag alone, 7, 2 and 0. The difference is `aws_iam_role.data_transfer[0]` and
  `aws_iam_role_policy.data_transfer[0]`, so 4.5's plan after 6h's step 7 reads 2 to add by difference, the
  count the stage file called unmeasured.

## 2026-11-22 — 2.2 attempted as Stage 19's step 6 on §N.10's day 1, and what day 2 finds

*Claude, in the session of `promotion.md` §N.10's day 1: the portal's wizard filled in the Data Scientist
User's Chrome session on the user's word in that session's chat (*"Cópia, view e Publish"*, 19:16:35 UTC);
reads as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`)
and `Data Governance Account` (`awsds-infra-data`). Times UTC. Stage 19's log holds the full reading.*

- **[Claude] 2.2's source**, Stage 19 pass 5's step 6: `sandbox-lab-trades-hot` on `eighth-experimentation`'s
  connection `redshift-serverless.redshift`, database `sandbox`, schema `lab`, *Include: trades_hot\**,
  *Publish assets to the Catalog* No, *Import data lineage* not enabled. Created at 19:47:23 as
  `c4n05wth04ll3k` and `FAILED_CREATION` at once: the connection's access role, in the session
  `SYSTEM@5hkjdsy3umpi1c` the project role opens, holds no `redshift-data:ListDatabases` (`SUP-460`). No
  run, no asset, so 2.3 has nothing to publish.
- **[Claude] What 2.1 finds on day 2**: `lab.trades_hot`, Stage 19 5.2's copy of
  `trades_notional`, made at 19:42:15 by `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, 10 rows,
  `AUTO(EVEN)`. No materialized view exists over the link: Redshift refuses one naming `awsdatacatalog`
  (`SUP-459`).
- **Left for day 2**: 2.2 again after the access role's `redshift-data` permission, the user's decision, or
  pass 2 starts at 2.1 without an asset; `c4n05wth04ll3k` stands until then.

## 2026-11-22 — 2.2's prerequisite applied: the access role's Data API reads

*Claude, in the session of `promotion.md` §N.10's day 1, recording an apply that Stage 19's log holds in full.
No AWS call for this entry. Times UTC.*

- **[Claude] The access role's four metadata reads**, `redshift-data:ListDatabases`, `ListSchemas`,
  `ListTables` and `DescribeTable` on Sandbox's workgroups, written on the user's *"Sim, escreva"* and applied on
  *"Sim, aplique"* at 21:23 in `sandbox/warehouse/` (0 added, 2 changed, re-planned `No changes`). The earlier
  entry's "Left for day 2" is answered: 2.2 runs again on day 2, `c4n05wth04ll3k` deleted first.

## 2026-11-22 — §N.10's day 2: the opening readings

*Claude, in the session of `promotion.md` §N.10's day 2, on the raise of 18:16 UTC that day 1 and N.9's day 3
share; reads as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`). Times UTC.*

- **[Claude] The other sessions told** at 22:37: N.9's day 3, whose 6d 7.5 window holds every AWS call of this
  session while it is open, and which lowers only by agreement, the last session to finish lowering.
- **[Claude] `make status`** at about 22:39: the hub's two hosts up, `sandbox/egress` with 25 interface
  endpoints, `sandbox/warehouse-compute` and `sandbox/probes` up; passive 0.3394 USD/h, the warehouse's active
  1.44 USD per query-hour. One Studio app bills, `jup` in `eighth-experimentation-ai-domain`, since 2026-11-21
  20:07. The apps of `jup-test-experimentation` and of `eighth-experimentation`'s `default-28f1b390-…` read
  `Deleted`, their spaces `InService`.
- **[Claude] The usage limit** `8627a6cb-…`, 10 RPU-hours, period `monthly`, `deactivate`, created by the day's
  raise: `UsageLimitConsumed` 2.0 and `UsageLimitAvailable` 7.0 in every quarter hour from 21:15 to 22:30;
  `ChargedSeconds` 4,916, 4,560 and 480 in the hours from 18:00, 19:00 and 20:00, and none since. The limit
  bites between 9 and 10 (`SUP-123`), so day 2 holds about seven RPU-hours on the warehouse, some 1.75
  query-hours at 4 RPUs.
- **[Claude] What 2.1 finds**: `lab.trades_hot`, 10 rows, its columns `trade_date date`, `desk varchar`,
  `instrument varchar`, `quantity integer`, `price double precision` and `notional double precision`, owner
  `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`; no view in `lab`. The source `c4n05wth04ll3k` reads
  `FAILED_CREATION`, its error naming `redshift-data:ListDatabases` for
  `awsds-sandbox-warehouse-access-avhvbqn37ty7m8/SYSTEM@5hkjdsy3umpi1c`; the access role's portal policy holds
  `ImportTheWarehousesMetadataForADataSource`, the four Data API reads on `workgroup/*`.

## 2026-11-22 — §N.10's day 2: 2.4's applies, 2.1, and 2.2 refused at its run

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's words in this session's chat: *"Faça 2.1
e 2.2 pelo chrome."* and *"Autorizo os dois applies."* (about 22:50). The applies and the reads as the
infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and `Data
Governance Account` (`awsds-infra-data`); the portal's acts in the Data Scientist User's Chrome session,
`eighth-experimentation`'s owner. N.9's day 3 told of each write first. Times UTC.*

- **[Claude] 2.4's applies**, from this branch at `main`'s `decc55d5`, the plans saved at 22:46 and 22:47 after
  each slice planned *"No changes."* without the switch:
  - `sandbox/sagemaker/` with `redshift_serverless_enabled=true`, 22:51:11 to 22:51:44: *"Apply complete!
    Resources: 3 added, 1 changed, 0 destroyed."*, the blueprint configuration `dlyaabb17hano0`, its
    `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant, AWS's `AmazonDataZoneRedshiftManageAccessRolePolicy` on
    `awsds-sandbox-smus-manage-access`, and the project key's policy;
  - `data-governance/governance/` with the same switch, 22:51:53 to 22:52:12: *"Apply complete! Resources: 0
    added, 1 changed, 0 destroyed."*, the profile `experimentation`;
  - each re-planned with the switch at 22:52 and 22:53: *"No changes."*.
- **[Claude] The profile** `dh60xbal05q64w` at 22:53:21: the configuration `RedshiftServerless`
  (`c12845c5-…`), `ON_DEMAND`, order 14, `redshiftBaseCapacity` and `redshiftMaxCapacity` `"4"` with
  `isEditable` false; DataZone's resolved parameters name the database `dev`, the workgroup
  `redshift-serverless-workgroup`, the namespace `redshift-serverless-namespace`, the schema `project`, the
  connection `project.redshift`, `provisionManagedSecret` `true` and `connectToRMSCatalog` `false`. The
  *Update project* banner N.9 saw on `eighth-experimentation` at 22:2x predates these applies: the trail
  holds four `UpdateProjectProfile` by the infrastructure user from 19:00:09 to 19:00:14 and one at 05:07:41.
  Neither session clicks it while the configuration stands.
- **[Claude] 2.1**, the Query Editor on `redshift-serverless.redshift`, database `sandbox`, *Limit 100* off,
  the editor's offer of its new version left with *Later*. `CREATE VIEW lab.trades_hot_by_desk` at 22:55:02
  (query 15519811) and `CREATE TABLE lab.trades_hot_daily AS …` at 22:56:02 (15519826), both `success` by
  user 103, `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, which owns the view and the table;
  `lab.trades_hot_daily` holds 5 rows. While the statement was typed the editor raised twice *"A problem
  occurred while getting autocompletion data"*, *"autocompleteMsg.getMetadataErrorAccessDenied"*.
- **[Claude] 2.2, Stage 19's step 6 again**: `c4n05wth04ll3k` deleted at about 22:58 from *Manage → Data
  sources*, *Actions → Delete data source*, the dialog reading *"Deleting this data source will not delete
  assets it has already published, but no new runs will occur."* The source created again with day 1's
  rules: `sandbox-lab-trades-hot`, `brnatob4h2kwb4`, Amazon Redshift on `redshift-serverless.redshift`
  (`awsds-sandbox-warehouse`), database `sandbox`, schema `lab`, *Include: trades_hot\**, *Publish assets to
  the Catalog* No, *Automated business name generation* Enabled, on demand. The wizard notes *"This
  connection does not support importing data lineage because it does not use an Amazon Redshift secret for
  authentication"*. Created at 22:59:17, `READY`.
- **[Claude] The creation and the run in Sandbox's trail**: at 22:59:18 the project role's session
  `SYSTEM@5hkjdsy3umpi1c` assumed `awsds-sandbox-warehouse-access-avhvbqn37ty7m8`, which called
  `GetCredentials` twice, `ListDatabases` (`database` `sandbox`) and at 22:59:19 `ListSchemas`
  (`schemaPattern` `lab`), each admitted. The run, started at 22:59:30, failed in 3 s, nothing added or
  updated: *"Data source run failed - VALIDATION_EXCEPTION User: …assumed-role/awsds-sandbox-warehouse-access-avhvbqn37ty7m8/SYSTEM@5hkjdsy3umpi1c
  is not authorized to perform: redshift-data:ExecuteStatement on resource: …workgroup/… because no
  identity-based policy allows the redshift-data:ExecuteStatement action (Service: RedshiftData, Status Code:
  400, …) (SDK Attempt Count: 3)"*. The trail holds three `ExecuteStatement` `AccessDenied` at 22:59:32,
  22:59:33 and 22:59:35, `requestParameters` `{}`, and no `ListTables` or `DescribeTable`.
- **[Claude] The statements the run asks for**, written in `sandbox/warehouse/iam.tf`:
  `ImportTheWarehousesMetadataForADataSource` gains `redshift-data:ExecuteStatement` on the workgroups, and
  `ReadTheDataSourcesOwnStatements` grants `DescribeStatement`, `GetStatementResult`, `CancelStatement` and
  `ListStatements` on `*` under `redshift-data:statement-owner-iam-userid = ${aws:userid}`, the shape of AWS's
  `RSDataIAMSession` in `SageMakerStudioProjectUserRolePolicy` v77. Access Analyzer's `validate-policy`: no
  finding. Planned from this branch at 23:02 with both switches named (`all_projects_tag_enabled=true`,
  `data_transfer_role_enabled=false`): *"Plan: 0 to add, 2 to change, 0 to destroy."*, the portal policies of
  `avhvbqn37ty7m8` and `4gqfau9xuo6e4w`, saved. Not applied: the user's word first.

## 2026-11-22 — §N.10's day 2: the access role's statement applied, 2.2's run read

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's words in this session's chat:
*"Autorizo o apply do warehouse"* (about 23:08). As the infrastructure user with `InfrastructureAccess` in
`Sandbox Account 1` (`awsds-infra-sandbox-1`); the portal's act in the Data Scientist User's Chrome session,
`eighth-experimentation`'s owner. N.9's day 3 and the session preparing the SSO infrastructure told first;
N.9 answered that its 6d 7.5 window was not open. Times UTC.*

- **[Claude] `sandbox/warehouse/` applied** from this branch, the plan saved at 23:02, 23:09:33 to 23:09:46:
  *"Apply complete! Resources: 0 added, 2 changed, 0 destroyed."*, the portal policies
  `awsds-sandbox-warehouse-access-portal-avhvbqn37ty7m8` and `-4gqfau9xuo6e4w`. Re-planned at 23:10:07 with
  both switches named: *"No changes."*.
- **[Claude] 2.2's run**, *Run* on `brnatob4h2kwb4` in the portal: run `501gj8x6pmqck0`, created 23:10:43,
  started 23:10:44.29, stopped 23:10:53.68, `SUCCESS`, added 3, updated 0, unchanged 0, failed 0; the
  failed run `be2j095629d6kw` stays in the list. The include rule `trades_hot*` took the view with the
  tables:

  | Asset | Id | Type, revision | Forms |
  |---|---|---|---|
  | `trades_hot` | `cgpzdjxcumuzrk` | `amazon.datazone.RedshiftTableAssetType` 18 | `RedshiftTableForm`, `DataSourceReferenceForm`, `SubscriptionTermsForm`, `AssetCommonDetailsForm` |
  | `trades_hot_daily` | `57py2yrv0o93ww` | `amazon.datazone.RedshiftTableAssetType` 18 | the same |
  | `trades_hot_by_desk` | `4o4k5h7uxxsj68` | `amazon.datazone.RedshiftViewAssetType` 19 | `RedshiftViewForm`, `DataSourceReferenceForm`, `SubscriptionTermsForm`, `AssetCommonDetailsForm` |

  Each asset stands at revision 2, unlisted, owned by `avhvbqn37ty7m8`. `AssetCommonDetailsForm`'s
  `sourceIdentifier` is `arn:aws:redshift-serverless:us-west-2:<account>:table/awsds-sandbox-warehouse/sandbox/lab/<name>`
  for a table and `…:view/awsds-sandbox-warehouse/sandbox/lab/trades_hot_by_desk` for the view; the
  `externalIdentifier` reads `avhvbqn37ty7m8:redshift:serverless:awsds-sandbox-warehouse:<account>:us-west-2:sandbox:lab:<TABLE|VIEW>:<name>`.
  `get-asset` answers `awsds-infra-sandbox-1`, a contributor of the project, and refuses `awsds-infra-data`
  with *"User is not permitted to perform operation: GetAsset"*, as Stage 19's log read on 2026-11-14.
- **[Claude] The run in Sandbox's trail**: as `awsds-sandbox-warehouse-access-avhvbqn37ty7m8/SYSTEM@5hkjdsy3umpi1c`,
  `ExecuteStatement` at 23:10:45 and 23:10:46, each `statementName` `Console Query: <uuid>`, database
  `sandbox`; `DescribeStatement` and `GetStatementResult` on each; no `ListTables`, `DescribeTable` or
  `ListStatements`. `sys_query_history` between 23:10:40 and 23:11:00 holds one statement, query 15519947 at
  23:10:47 by user 103, `success`: a catalog query over `pg_catalog.svv_all_columns`,
  `svv_redshift_columns`, `pg_constraint` and `pg_attribute`, filtered to schema `lab` and the names
  `trades_hot`, `trades_hot_daily` and `trades_hot_by_desk`. The first statement is not in it. `SUP-460`
  gains the reading, and the two statements' comments in `iam.tf` say what the run calls.

## 2026-11-22 — §N.10's day 2: 2.3, the table, the view and their data product published

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's words in this session's chat: *"Sim, faça
2.3 e 2.4 pelo chrome"* (about 23:20). The portal's acts in the Data Scientist User's Chrome session,
`eighth-experimentation`'s owner; the reads as the infrastructure user with `InfrastructureAccess` in `Sandbox
Account 1` (`awsds-infra-sandbox-1`), a contributor of the project. N.9's day 3 and the session preparing the SSO
infrastructure told first. Times UTC.*

- **[Claude] The asset pages** each opened with the business-name generation's suggestions pending:
  `trades_hot` *"7 suggestions ready for review — 1 business name · 6 column business names"*, the name
  *Daily Trading Transactions by Desk and Instrument*; `trades_hot_by_desk` *"4 suggestions ready for review —
  1 business name · 3 column business names"*, *Daily Hot Trades by Desk with Notional Values*. Neither was
  accepted or rejected, and each listing carries them as `SuggestionForm`.
- **[Claude] `trades_hot` published**: *Publish*, the panel *Publish asset* (*"This asset will become
  discoverable to everyone in your organization and they can request access to this asset."*), *Subscription
  approval* left at its default *Required*, *Publish asset*: *"Table trades_hot has been published to the
  catalog."* Listing `cl14qzshdc64y8`, revision 2, `ACTIVE`, created 23:21:18.029 and updated 23:21:19.164, the
  asset's revision 2; forms `AssetCommonDetailsForm`, `AwsConfigurationForm`, `DataSourceReferenceForm`,
  `RedshiftTableForm`, `SubscriptionTermsForm` (`approvalRequired` `YES`) and `SuggestionForm`.
- **[Claude] `trades_hot_by_desk` published** the same way: listing `5t9cxrhio6c8eo`, revision 2, `ACTIVE`,
  created 23:22:02.144, the asset's revision 2, `RedshiftViewForm` in place of the table's form. The toast
  calls it a table: *"Table trades_hot_by_desk has been published to the catalog."*
- **[Claude] The data product**: *Assets → Create → Create data product*, name `sandbox-trades-hot`,
  description *"Stage 21 pass 2: the Sandbox warehouse's lab.trades_hot and its view lab.trades_hot_by_desk."*,
  the view and the table, *Create* at 23:23: `614tardy0iah3k`, *Not published*, *Included assets: 2*.
  *Metadata Forms → Add Form* offered one form, *Classification* (*"The data product's classification: public,
  internal, restricted or personal."*, 1 field); `internal` saved at 23:24:15, the product's revision 2.
  *Publish*, the dialog *"This data product will become discoverable to everyone in your organization and they
  can request access to this data product."*, *Publish*: *"Data product published successfully."* Listing
  `4q8efayh74yxow`, revision 1, `ACTIVE`, created 23:24:45.910, the product's revision 2; forms
  `classification` `{"classification":"internal"}` and `ownedByDataProductListing` naming `5t9cxrhio6c8eo` and
  `cl14qzshdc64y8`, its items the two asset listings at revision 2. The product's publication wrote no new
  revision of either asset listing.
- **[Claude] `CT-18` after the publication** (`./aws/catalog.py`, 23:26:18 to 23:29:32, exit 2): `pass`, *"house-price
  public; trades_notional internal"*. The check reads `GlueTableAssetType` listings alone, and a data product
  listing only for the asset listings it carries, so neither Redshift listing nor the product's
  `classification` form is in its reading; 6.3's amendment of `catalog.py` names S3 Object Collections and not
  Redshift listings. `CT-17` fails on Production's grants to `awsds-sandbox-warehouse-access-avhvbqn37ty7m8` on
  `app_etl.trades_notional`, `DESCRIBE` on the table and `SELECT` on its columns: Stage 19 5.1's Lake Formation
  half, which Stage 19's step 7 revokes. `CT-6` lists the source `sandbox-lab-trades-hot`, `REDSHIFT`, no
  schedule, 3 assets, 1 failed run and 1 successful.

## 2026-11-22 — §N.10's day 2: 2.4, the consumer's compute in `test-experimentation`

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's words in this session's chat: *"Sim, faça
2.3 e 2.4 pelo chrome"*. The portal's act in the Data Scientist User's Chrome session, a member of
`test-experimentation`; the reads as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`). Times UTC.*

- **[Claude] The deploy**: `test-experimentation`'s *Resource blueprints*, *Deploy*. *Managed blueprints* offered
  *EMR Serverless*, *Lakehouse Database*, *MLflow App*, *Redshift Serverless* and *S3 Bucket*, beside *"Have an
  existing resource you want to bring in? Create a connection instead."* *Redshift Serverless*, then *Input
  parameters*: a name (*"The name cannot be changed after creation."*) and a description, and no capacity field.
  Name `stage21-consumer-redshift`, description *"Stage 21 2.4: the consumer's workgroup, removed at 2.9."*,
  *Deploy*: *"Blueprint deployment created successfully"*, the deployment `redshift.stage21-consumer-redshift`,
  its parameters as the profile reads them (database `dev`, base and maximum 4, schema `project`, connection
  `project.redshift`, `provisionManagedSecret` `true`, `connectToRMSCatalog` `false`).
- **[Claude] The environment** `dahsfn6j8lqec0`, created 23:27:14.416 by the Data Scientist User from the
  configuration `c12845c5-…` of the blueprint `dlyaabb17hano0`, `ACTIVE` and its deployment `SUCCESSFUL` at
  23:29:00. Its stack `DataZone-Env-dahsfn6j8lqec0`, created 23:27:27, `CREATE_COMPLETE` by 23:28:48, holds two
  resources: `AWS::RedshiftServerless::Namespace` `redshift-serverless-namespace-dahsfn6j8lqec0` (23:27:32) and
  `AWS::RedshiftServerless::Workgroup` `redshift-serverless-workgroup-dahsfn6j8lqec0` (23:28:28). Sandbox's trail:
  `CreateNamespace` at 23:27:31 and `CreateWorkgroup` at 23:27:34, each admitted, by
  `awsds-sandbox-smus-provisioning/AmazonDataZoneEnvironmentDeployer-<account>`; no `UpdateWorkgroup` to 23:31.
- **[Claude] The workgroup**: `AVAILABLE`, base 4 and maximum 4 RPUs, as `CreateWorkgroup` asked; price-performance
  target disabled, not publicly accessible, enhanced VPC routing off; subnets `awsds-sandbox-private-usw2-az1`
  (`subnet-016b5a3a62c739894`) and `-az2` (`subnet-09d3399d6b0fec93a`); security group `sg-05e52373c14288c22`,
  `datazone-4gqfau9xuo6e4w-dev`, the project's (*"Security group for the project."*), all traffic in from itself
  and out to `0.0.0.0/0`. The request set `search_path` alone, read back as `project, $user, public`, beside the
  service's defaults: `max_query_execution_time` 14400, `require_ssl` true, `enable_user_activity_logging` true,
  `auto_mv` true. Its tags name the domain, the project, the environment, the blueprint `RedshiftServerless` and
  the scope `dev`. The workgroup is outside the warehouse's usage limit, `make down` and `make status`.
- **[Claude] The namespace**: `AVAILABLE`, database `dev`, admin user `admin` with the password managed in
  Secrets Manager (`redshift!redshift-serverless-namespace-dahsfn6j8lqec0-admin-…`), the namespace and the secret
  both under `alias/awsds-sandbox-project`; its default IAM role and its only role are `test-experimentation`'s
  project role, `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw`; no log export.
- **[Claude] The connection** `project.redshift` (`4i2nv7u733e51s`), `REDSHIFT`, on the environment: workgroup
  storage, database `dev`, the JDBC and JDBC IAM URLs on port 5439, the temporary directory
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/4gqfau9xuo6e4w/dev/redshift-tmp/`, `READY`. Its
  `lineageSync` is `enabled` `true`, job `50jlej783a7cb4`, on `cron(28 23 * * ? *)`, the minute of the
  creation: a daily lineage run nobody chose, which 2.9's removal ends before its first.
- **[Claude] The Redshift subscription target** `bbw4g031uhkopc`, `redshift.stage21-consumer-redshift-default-target`,
  created 23:28:52.677: `type` `null` in `list-subscription-targets`, provider *Amazon SageMaker*, manage-access
  role `awsds-sandbox-smus-manage-access`, `authorizedPrincipals` `datazone_env_dahsfn6j8lqec0`, applicable to
  `RedshiftViewAssetType` and `RedshiftTableAssetType`, its form `RedshiftServerlessSubscriptionTargetConfigForm`
  naming the database `dev`, the namespace's admin secret, the workgroup and the schema `project`. Verification
  iii has its target, so 2.5 to 2.7 may run.
- **[Claude] Sandbox's workgroups** at 23:31: `awsds-sandbox-warehouse` (4 and 8) and
  `redshift-serverless-workgroup-dahsfn6j8lqec0` (4 and 4). `test-experimentation` holds six environments, the
  new one among them, and `create-datalake-database-env-mydatabase-…` stays `VALIDATION_FAILED` from 2026-11-09.
