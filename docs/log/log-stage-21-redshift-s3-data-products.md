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

## 2026-11-22 — §N.10's day 2: 2.5 to 2.8, the subscription, its revocation and the portal's load

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's words in this session's chat: *"Faça do
2.5 ao  2.8 prlo chro.e"*. The portal's acts in the Data Scientist User's Chrome session, owner of
`eighth-experimentation` and a member of `test-experimentation`; the reads as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and in `Data Governance`
(`awsds-infra-data`). Times UTC; 2.8 ran after midnight, on 2026-11-23.*

- **[Claude] 2.5, the request**: from `test-experimentation`, a subscription request to the data product
  `sandbox-trades-hot` (listing `4q8efayh74yxow`, revision 1), reason *"Stage 21 2.5: test-experimentation
  reads the product through its Redshift Serverless workgroup."*. `CreateSubscriptionRequest` at 23:45:56Z by
  the portal user, Data Governance's trail, answered `ACCEPTED` with no reviewer (`reviewerId` null); the
  requester owns the publishing project. The subscription `coq9ewxmav1zf4` read `APPROVED`.
- **[Claude] 2.5, the fulfilment**: two grants created by `SYSTEM` on the target `bbw4g031uhkopc`,
  `5plwofai6rdwr4` for the view's listing `5t9cxrhio6c8eo` (`trades_hot_by_desk`, asset `4o4k5h7uxxsj68`) at
  23:45:57.530 and `da65d7frv0lci8` for the table's listing `cl14qzshdc64y8` (`trades_hot`, asset
  `cgpzdjxcumuzrk`) at 23:45:57.773. Both read `GRANT_FAILED` at 23:46:34 and 23:46:35, each asset's
  `failureCause` *"Secret ARN can not be null or empty"*, `targetName` null. The consumer's target names its
  namespace's admin secret (2.4); the producer's assets came from the data source on
  `redshift-serverless.redshift` (`axsiuoykrswosw`), authenticated by IAM, which names no secret (`SUP-469`).
- **[Claude] What the failure wrote: nothing.** Both namespaces' `svv_datashares` empty (23:57:44 and
  23:58:23); their `sys_query_history` from 23:44 holds no `datashare`, `GRANT` or `REVOKE` statement but the
  admin users' reads; the consumer's databases are `dev` alone. Data Governance's trail holds
  `CreateSubscriptionRequest` and no `AcceptSubscriptionRequest`, `CreateSubscriptionGrant` or
  `UpdateSubscriptionGrantStatus`. Sandbox's holds no `redshift-data`, `redshift-serverless`, `redshift` or
  `secretsmanager` call from 23:44 to 23:59 but the infrastructure user's, and DataZone's only `AssumeRole`s
  are the portal user's sessions in the two project roles (23:45:03 to 23:45:15, 23:53:06).
- **[Claude] What the portal shows**: the consumer's side read *Subscription approved*. The producer's
  *Subscriptions → Access* read `sandbox-trades-hot | test-experimentation | Shared | 22 de novembro de 2026 às
  20:45`, and its *View access details* *Shared by* Data Scientist User and *Shared with*
  `test-experimentation`, with no grant status. Neither page shows the failure.
- **2.6 not run**: with both grants failed there is nothing to `SELECT` and no `ComputeSeconds` to compare. No
  space was started.
- **[Claude] 2.7, the revocation**: the producer's *Access* row, *Revoke*, the dialog *Revoke access* asking
  for *confirm*, with no box. `RevokeSubscription` at 23:56:34Z by the portal user, `retainPermissions`
  `false`; `coq9ewxmav1zf4` `REVOKED` (`updatedAt` 23:56:34.079); both grants answered
  `ResourceNotFoundException`, *"subscriptionGrant entity not found"*, at 23:57:10. No call reached Sandbox and
  neither namespace changed (above). The *Access* tab reads *No data available*. A revocation of a grant that
  wrote a datashare stays unmeasured.
- **[Claude] 2.8, the portal's load**: `eighth-experimentation`'s *Data → Add → Create table*, *Redshift table*,
  the file `stage21_portal_load.csv` (a header and three rows), the compute `Redshift
  (redshift-serverless.redshift)`, the database `sandbox` (offered `warehouse`, the namespace's default and
  preselected, `dev` and `sandbox`), the schema `lab` (offered `public` and `lab`), the table name
  `stage21_portal_load` filled from the file. *Next* answered *"Cannot infer schema"* with IAM's wording: the
  access role's session `<Identity Center user id>@<Tooling environment id>` *"is not authorized to perform:
  kms:GenerateDataKey on resource: arn:aws:kms:us-west-2:<account>:key/a81b1ef3-… because no identity-based
  policy allows the kms:GenerateDataKey action"*.
- **[Claude] 2.8 in the trail and the database**: the access role's session created 00:01:11Z, `sourceIdentity`
  the portal user. Its Query Editor V2 session listed databases and schemas as user 103, 00:01:14 to 00:02:10
  (`application_name` *Amazon Redshift Query Editor V2 - …*). `GenerateDataKey` refused at 00:02:24Z,
  `invokedBy` `fas.s3.amazonaws.com`, `requestParameters` null. The key is `alias/awsds-sandbox-project`, the
  default key of `awsds-sandbox-smus-projects` and of no other Sandbox bucket, so the upload went to that
  bucket through S3; the trail names no object, and no object under `eighth-experimentation`'s prefix is newer
  than 23:00. The access role holds no `s3:` or `kms:` action, and the bucket's policy only denies insecure
  transport. No `COPY` ran (`sys_query_history` from 00:00 holds none, `sys_load_error_detail` empty), `lab`
  holds no `stage21_portal_load`, and the namespace's default role `awsds-sandbox-warehouse-exec` was never
  reached. Nothing was granted (5b decision 5). Verification vii: the refusal is KMS's, to the connection's
  access role, at the upload, before any `COPY` (`SUP-470`).
- **[Claude] The consumer's namespace, read 00:05Z**: `pg_user` lists `rdsdb`, `admin` and
  `IAMR:awsds-sandbox-smus-provisioning` as superusers, and `IAMR:user-project@4gqfau9xuo6e4w` (user 102, a
  `SHOW SCHEMAS` at 23:29:15) not. The provisioning role's user ran at the deploy, 23:28:42 to 23:28:49:
  `CREATE ROLE "datazone_env_dahsfn6j8lqec0"`, `GRANT USAGE ON DATABASE awsdatacatalog` to it,
  `CREATE SCHEMA "project"`, `GRANT ALL ON SCHEMA "project"` and `GRANT ALL FOR tables IN SCHEMA project` to
  it, and `GRANT ROLE sys:superuser TO ROLE datazone_env_dahsfn6j8lqec0`. The role is the target's
  `authorizedPrincipals` (2.4), owned by the provisioning role's user, and no user holds it (`svv_user_grants`
  empty). A portal session carries `RedshiftDbRoles` `datazone_env_<environment id>` (`docs/SMUS.md`, read
  2026-10-10 on the warehouse's path), so a portal session on this workgroup would be a superuser session;
  unmeasured, 2.6 not having run (`SUP-471`).

## 2026-11-23 — §N.10's day 2: 2.9, the consumer's workgroup removed and the reverse applies

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's choice in this session's chat, *"Aceitar e
fazer 2.9"*, answering whether to accept `SUP-469` as 2.5's reading or to retry on a producer connection
authenticated by a secret. The user signed in again as the infrastructure user before it (*"usuário sso infra
logado."*), the token valid to 01:23:31. The portal's act in the Data Scientist User's Chrome session; the reads
and the applies as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`) and `Data Governance` (`awsds-infra-data`). Times UTC.*

- **The user's decision**: `SUP-469` is 2.5's reading. The retry on a connection authenticated by a secret is
  not run, so a Redshift asset shared by subscription stays unmeasured end to end.
- **[Claude] The portal's removal**: `test-experimentation`'s *Resource blueprints*, the deployment
  `redshift.stage21-consumer-redshift`'s delete, the dialog *Delete blueprint deployment* (*"Deleting a blueprint
  deployment is final and removes all connections created."*, the word *confirm*), then *"Blueprint deployment
  deleted successfully"* and the row *Delete in progress*. The trail: `DeleteEnvironment` at 00:24:42 in Data
  Governance by the domain execution role for the portal user; in Sandbox, `DeleteStack` at 00:24:54,
  `DeleteWorkgroup` at 00:24:57 and `DeleteNamespace` at 00:25:04, by `awsds-sandbox-smus-provisioning`.
- **[Claude] What is absent**: the environment `dahsfn6j8lqec0`, `DELETING` at 00:26:09, answered *"Environment
  not found"* at 00:26:26; the stack `DataZone-Env-dahsfn6j8lqec0` is `DELETE_COMPLETE`. Sandbox's workgroups
  and namespaces are `awsds-sandbox-warehouse` alone, at 4 and 8. The connection `4i2nv7u733e51s` is not found,
  its lineage job `50jlej783a7cb4` answers *"The given Job doesn't exist."*, removed before its first run was
  due, and the target `bbw4g031uhkopc` is not found; no secret named for the namespace exists, scheduled for
  deletion or not. None of the domain's ten projects holds a `RedshiftServerless` environment (blueprint
  `dlyaabb17hano0`, 00:27:34).
- **[Claude] The reverse applies**, N.9's day 3 and N.10's day 1 told first, both idle. From this branch at
  `d6e83d0b`: `data-governance/governance` planned *"Plan: 0 to add, 1 to change, 0 to destroy."*, the profile
  `experimentation`'s `environment_configurations`, and applied at 00:28:06, *"Apply complete! Resources: 0
  added, 1 changed, 0 destroyed."*. `sandbox/sagemaker` planned *"Plan: 0 to add, 1 to change, 3 to destroy."*:
  the `RedshiftServerless` blueprint configuration, its policy grant and the manage-access role's
  `AmazonDataZoneRedshiftManageAccessRolePolicy` attachment destroyed, the project key updated in place. Applied
  at 00:28:48, *"Apply complete! Resources: 0 added, 1 changed, 3 destroyed."*. Both re-planned *"No changes.
  Your infrastructure matches the configuration."* at 00:29.
- **[Claude] `US-3`** (`./aws/studio.py awsds-infra-data awsds-infra-sandbox-1`, 00:29 to 00:31, *"all checks
  passed"*): *"14 blueprint configuration(s) in awsds-infra-sandbox-1"*, *"all inside decision 5's category 1"*,
  and the domain account's Tooling configuration the note it was.

## 2026-11-23 — §N.10's day 2: pass 3, the warehouse's lineage and its removal

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's word in this session's chat, *"Sim, faça o
passo 3"*, answering a question that named pass 3's writes: `lineage_reader`, its secret and its grants on `lab`,
the second connection and the data source with *Import data lineage* in the portal, 3.3's statements creating
`lab.trades_hot_by_day`, and 3.5's removal. The portal's acts in the Data Scientist User's Chrome session; the SQL
as the warehouse's admin through the Data API; the reads as the infrastructure user with `InfrastructureAccess` in
`Sandbox Account 1` (`awsds-infra-sandbox-1`) and `Data Governance` (`awsds-infra-data`). Times UTC.*

- **[Claude] 3.1, the credentials**, 00:37:33 to 00:38:18: the password from `get-random-password`, never
  printed; `CREATE USER lineage_reader` from its MD5 hash, `GRANT ROLE "sys:operator"`, `USAGE ON SCHEMA lab` and
  `SELECT ON ALL TABLES IN SCHEMA lab`, each `FINISHED`; the secret `awsds-sandbox-stage21-lineage-reader`
  tagged `AmazonDataZoneProject` `avhvbqn37ty7m8`. Read back: user 109, `usesuper` false, the role
  `sys:operator`, five of `lab`'s tables granted.
- **[Claude] The second connection**, *Create connection* in `eighth-experimentation`, Redshift with *AWS
  Secrets Manager* and that secret: `sandbox-lineage-reader` (`5dpavlenb7xu34`), `CreateConnection` at 00:40:16 by
  the domain execution role. The form's JDBC URL named the database `dev`, edited to `sandbox`. `CREATING` to
  00:43:57, then `READY`, its `lineageSync` `null` throughout (`SUP-207`).
- **[Claude] 3.2, the data source**: `sandbox-lab-lineage` (`cyfqsfnyf4s8wg`) on that connection over
  `sandbox.lab`, *Import data lineage* checked, `publishOnImport` false, no schedule. `CreateDataSource` at
  00:46:52, the switch's time, then an `UpdateDataSource` by `datazone.amazonaws.com` at 00:46:53. At 00:47:17
  the connection read `lineageSync` `enabled: true`, the job `69cnpyuu9d7yfk` and `cron(51 0 * * ? *)`. The data
  source never ran.
- **[Claude] 3.3, the statements, run as the admin through the Data API**, not in the user's Query editor as the
  step says, to land before the pull at 00:51: `CREATE TABLE lab.trades_hot_by_day AS …` (query 16527491,
  00:47:56), the `INSERT … SELECT` into `lab.trades_hot_daily` (16527507, 00:48:31), the `UPDATE` (16527512,
  00:48:37) and the `MERGE` (16527519, 00:48:39), each `success`, the `MERGE` typed `OTHER` in
  `SYS_QUERY_HISTORY`. The `CREATE TABLE … AS` from `awsdatacatalog` was not run: the pull reads seven days, which
  held Stage 19 5.2's `CREATE TABLE lab.trades_hot AS SELECT * FROM
  awsdatacatalog.glue_db_blerpkhn9nj7o0.trades_notional` (query 14915514, 2026-11-22 19:42:15, user 103), and a
  statement after 00:51 reaches no pull before 3.5. `lab.trades_from_lake` does not exist.
- **[Claude] The pull**: the run `ajk9injla9unm8`, `createdBy` `SYSTEM` at 00:51:50, `IN_PROGRESS` at 00:54:21,
  `PARTIALLY_SUCCEEDED` at 00:54:42. `queryStartTime` 2026-11-16T00:51:50.324Z, `queryEndTime`
  2026-11-23T00:51:50.324Z, `totalQueriesProcessed` 19, `numQueriesFailed` 1, *"FATAL: Cannot connect to shared
  database "awsdatacatalog" created from Data Catalog ARN. Connect to a database in your cluster or a database
  created from a datashare instead and use cross-database query notation <shareddatabase>.<schema>.<object> to
  query the data in shared database."* The 19 match the window's successful `CTAS` (8), `DDL` (9) and `INSERT`
  (2) statements, by users 100, 103 and 107; the `UPDATE` and the `MERGE` are not among them. The failure is the
  `awsdatacatalog` CTAS, the only processed statement naming that database (`SUP-472`).
- **[Claude] 3.4, the nodes**: from 00:53:05 to 00:54:28 Data Governance's trail holds 26 `CreateLineageNode`
  by `datazone.amazonaws.com`, beside 16 `CreateLineageEvent`, 37 `CreateLineageNodeVersion`, 41
  `UpdateLineageNode` and 16 `UpdateLineageNodeVersion`. Ten are dataset nodes, `sandbox.lab.<table>` named by
  `arn:aws:redshift-serverless:us-west-2:<Sandbox>:table/awsds-sandbox-warehouse/sandbox/lab/<table>` (`view/` for
  `trades_hot_by_desk`); sixteen are job nodes, one per statement, `query-hash-<hash>` with its text in a
  `QueryForm`; the edges hang on a job-run node per execution, `<job>/<query id>#<n>#<n>` (`SUP-473`). Edges:
  `trades_hot` → `trades_hot_daily` by the CTAS of 22:56 and by the `INSERT … SELECT`; `trades_hot` →
  `trades_hot_by_day` by its CTAS; `trades_hot` → `trades_hot_by_desk` by `CREATE VIEW`. The `UPDATE` and the
  `MERGE` left no node, and `trades_hot` has no upstream. Statements with no input left a run into the table
  alone, and each `DROP TABLE` a run whose output is the dropped table: `wh_digits`, `wh_n`, `neg52.t`,
  `neg52_ctl`, `b52_test` and `b52_eighth`, gone from the warehouse, stand in the graph.
- **[Claude] The join to the assets**: each Redshift asset's `AssetCommonDetailsForm.sourceIdentifier` is its
  dataset node's ARN, and the asset nodes `c1cewufu08ayvk`, `4rgbeb8ey4f9qo` and `4ryiwpqegyjq1c` read the
  dataset nodes as upstream. `list-lineage-node-history` gives `trades_hot_daily` two versions (22:56:03 and
  00:48:32) and `trades_hot` four.
- **[Claude] The graph in the portal**, `trades_hot_daily`'s *Lineage* tab at depth 5: `sandbox.lab.trades_hot`
  (Table) → two job runs, `COMPLETE` → `sandbox.lab.trades_hot_daily` (Table) → *Cataloged* → `trades_hot_daily`
  (Asset / Inventory). `trades_hot`'s tab: the table → *Cataloged* → the inventory asset → *Published* → the
  published asset, nothing upstream of the table, so the graph does not reach the lake's `trades_notional`.
- **[Claude] 3.5, the removal**: the data source's *Edit connection* panel (*"The connection cannot be changed
  once the data source has been created."*; under the switch, *"Data lineage will be imported from all data
  sources that use this connection."*), *Import data lineage* unchecked and saved at 01:03:57; the connection
  read `enabled: false` at 01:04:11, its job and schedule kept. The data source deleted at 01:04:33 (*"Deleting
  this data source will not delete assets it has already published, but no new runs will occur."*), the
  connection removed at 01:05:16 (*Remove connection*, the word *confirm*). As the admin, 01:05:35 to 01:05:48:
  `REVOKE ROLE "sys:operator"`, `REVOKE ALL ON ALL TABLES IN SCHEMA lab`, `REVOKE USAGE ON SCHEMA lab`, `DROP USER
  lineage_reader`, each `FINISHED`, and `SVV_USER_INFO` holds no such user. The secret deleted at 01:06:08 with
  the step's seven-day window, deletion date 2026-11-30T01:06:08Z; rollback item 3 says no recovery window.
- **[Claude] What stays**: the connection answers *"Cannot find connection with id: 5dpavlenb7xu34"*, the data
  source *"The DataSource doesn't exist with dataSourceId=cyfqsfnyf4s8wg."*, the job *"The given Job doesn't
  exist. Try creating Job before accessing it."*. `eighth-experimentation` keeps one Redshift connection,
  `redshift-serverless.redshift`, `lineageSync` `enabled: false` on `cron(43 3 * * ? *)`, 6h decision 3's
  setting as found. The lineage nodes stay: `sandbox.lab.trades_hot_by_day`'s is read after the removal.
  `lab.trades_hot_by_day` (owner `dbadmin`, 10 rows) and `lab.trades_hot_daily` (10 rows after the `INSERT`) wait
  for Stage 19's step 7.

## 2026-11-23 — §N.10's day 2: pass 4, the federated catalog and its removal; rollback item 5

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's word in this session's chat, *"Autorizo o
passo 4. Login infra sso feito."*, and for rollback item 5 *"Pode avançar no 5.4"*, answering whether to run Stage
19's 5.4 with that item before the lowering. The portal's acts in the Data Scientist User's Chrome session; the SQL
as the warehouse's admin through the Data API; the rest as the infrastructure user with `InfrastructureAccess` in
`Sandbox Account 1` (`awsds-infra-sandbox-1`), `Data Governance` (`awsds-infra-data`) and `Production`
(`awsds-infra-prod`). Times UTC.*

- **[Claude] 4.1, the registration**: `register-namespace` at 01:23:29 answered `{"Status": "Registering"}`.
  `describe-data-shares-for-consumer` by the catalog's ARN listed nothing, while the producer's
  `describe-data-shares` held the `INTERNAL` datashare `…/ds_internal_namespace` associated to
  `DataCatalog/<account>`, `AUTHORIZED`. `associate-data-share-consumer` to the catalog's ARN at 01:26:51 made it
  `ACTIVE`. Lake Formation's `register-resource` of the datashare at 01:27:07: `HybridAccessEnabled` and
  `WithPrivilegedAccess` false, `VerificationStatus` `NOT_VERIFIED`. `glue create-catalog` `stage21_warehouse`
  at 01:27:09, its `FederatedCatalog` on `aws:redshift`, `CreateTime` 01:27:10, `aws:PermissionsModel`
  `LAKEFORMATION`. `get-catalogs --parent-catalog-id … --recursive` is refused, *"GetCatalogsRecursive is
  supported only at the account level"*; without `--recursive` it lists a child catalog per database, `warehouse`,
  `dev` and `sandbox`. `sandbox` holds the databases `public` and `lab`, and `lab` six tables: `trades_hot` (6
  columns), `trades_hot_daily` (2), `trades_hot_by_desk` (3, `TableType` `Table` where Redshift holds a view),
  `hello_jupyter_via_access` (3), `hello` (2) and `trades_hot_by_day` (3).
- **[Claude] The catalog's grants**: Lake Formation lists the creator's `InfrastructureAccess` alone, `ALL`,
  `ALTER`, `CREATE_CATALOG`, `CREATE_DATABASE`, `DESCRIBE` and `DROP` with grant option on the parent catalog;
  nothing on the child catalog or on `lab`, and no `IAMAllowedPrincipals`. Verification x's first half: no.
- **[Claude] 4.2**: `DESCRIBE` and `SELECT` on `stage21_warehouse/sandbox`'s `lab.trades_hot` to
  `eighth-experimentation`'s project role at 01:27:58, read back.
- **[Claude] 4.5's two applies on**, from this branch, which holds pull requests #323 and #363:
  `sandbox/warehouse/` with `all_projects_tag_enabled` and `data_transfer_role_enabled` true, *"Plan: 2 to
  add"*, the role `awsds-sandbox-warehouse-data-transfer` and its inline policy, applied 01:29:46 to 01:29:57 and
  re-planned *"No changes."* at 01:30:15. `sandbox/data/`, initialised in the worktree, with
  `data_transfer_key_statement_enabled` true: *"Plan: 0 to add, 1 to change, 0 to destroy."*, the data key's
  policy gaining `GenerateDataKeyDecryptDataTransferRole` (`kms:GenerateDataKey` and `kms:Decrypt` through S3 to
  the role), applied 01:31:00 to 01:31:15.
- **[Claude] 4.3, Redshift through the catalog**: the Query editor's data explorer lists the granted objects
  alone, `stage21_warehouse` → `sandbox` → `lab` → *tables (1)* `trades_hot`, *views (0)*. The table's menu
  offers *Preview data*, *Copy name* and *Refresh*, and *Preview data* opens an Athena cell, never a Redshift
  one. On `redshift-serverless.redshift`, database `sandbox`, `select * from
  "sandbox@stage21_warehouse"."lab"."trades_hot" limit 10` answered *ERROR: "sandbox@stage21_warehouse" does not
  exist*, with the toast `autocompleteMsg.getMetadataErrorAccessDenied`. The same session, `current_user`
  `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, reads four databases in `svv_redshift_databases`:
  `dev`, `sandbox` and `warehouse` local, `governed_trades` *shared via data catalog*; `show databases from data
  catalog` gives one, `glue_db_blerpkhn9nj7o0`. No read ran, so `sys_query_history` holds no `ComputeSeconds`
  for one. Verification x: no.
- **[Claude] 4.6 before data lake access**: Athena's runs of the preview at 01:31:20 and 01:32:19 failed
  *"GENERIC_INTERNAL_ERROR: No scheme for file system location: trades_hot"*.
- **[Claude] 4.5, data lake access**: `get-catalog` first (Lesson 60). `update-catalog` with the whole input was
  refused at 01:39:09, *"CatalogCustomProperties and IcebergOptimizationProperties can only be present for root
  catalog."*, the input carrying the `CustomProperties` that `get-catalog` returns; without them it passed at
  01:39:21, `DataLakeAccess` true and the transfer role, and the read-back kept `aws:PermissionsModel`. The
  catalog then carried `KmsKey` `AWS_OWNED_KMS_KEY`, `ManagedWorkgroupName` `<account>:stage21_warehouse`,
  `RedshiftDatabaseName` `dev` and `ManagedWorkgroupStatus` `CREATING`, `AVAILABLE` at 01:40:01. `redshift-serverless
  list-workgroups` and `list-namespaces` list `awsds-sandbox-warehouse` alone and `describe-clusters` nothing;
  `list-managed-workgroups` lists the managed workgroup, created 01:39:21.682, its `sourceArn` the catalog, with
  no capacity field. Sandbox's trail holds no creation of it by 01:44, only reads. No cluster was created, so
  `DenyRedshiftProvisionedClusters` had nothing to refuse.
- **[Claude] 4.6 with data lake access**: the preview at 01:40:59 and 01:41:51 failed *"GENERIC_INTERNAL_ERROR:
  Malformed request: ERROR: "sandbox@stage21_warehouse" does not exist"*, 5,956 and 6,406 ms of engine time, 0
  bytes scanned: the name and the answer of 4.3. Each run left the session's `GetManagedWorkgroup` calls in the
  trail, invoked by `redshift-data.amazonaws.com`. A diagnostic outside 4.2's text, `DESCRIBE` on the catalog
  `stage21_warehouse/sandbox` and on `lab` to the project role, 01:43:09 to 01:43:12, changed nothing: the run at
  01:43:19 failed the same. As the admin, `svv_datashares` and `svv_datashare_objects` list no `ds_internal`
  share. Verification xii's Athena half: no.
- **[Claude] 4.4, the data source**: `stage21-federated-lab` (`cpsozetz63bs7k`), *AWS Glue (Lakehouse)* on
  `project.default_lakehouse`, created 01:46:29 with *Enter the catalog name* `stage21_warehouse/sandbox`, which
  the review reads `<account>:stage21_warehouse/sandbox`; the database list offered `lab`; *Include \**, publish
  *No*, business names off, data quality on. *Import data lineage* was left checked as the form opened, the
  setting being the connection's. Run `5boqoxlhwbniq8`, on demand, 01:46:41 to 01:46:44, `SUCCESS`, one asset
  added, *Lineage import status: Completed*. The asset `dtbux9ndboiz9s`, `trades_hot`, type *Glue Table*, shown
  `stage21_warehouse.lab`; its form *AWS Glue table* holds the catalog id `<account>:stage21_warehouse/sandbox`, the
  table ARN `arn:aws:glue:us-west-2:<account>:table/stage21_warehouse/sandbox/lab/trades_hot`, six columns and a
  *Federated Table* block (`lab`, `trades_hot`, connection `aws:redshift`). Its source identifier is that Glue
  ARN, so it does not meet pass 3's lineage nodes, named by the Redshift ARN. `GetAsset` as Data Governance's
  `InfrastructureAccess` answered *"User is not permitted to perform operation: GetAsset"*, a non-member's
  refusal. The publish, request and approval half was not run, for the hour. Verification xi: the table imports,
  as a Glue table; the subscription is unmeasured.
- **[Claude] 4.8, the removal**: the asset deleted in the portal, then the data source (*"Data source
  deleted."*; `GetDataSource` not found at 01:52:25). `update-catalog` with `DataLakeAccess` false at 01:48:49:
  the access properties gone, `list-managed-workgroups` empty at 01:49:05. `delete-catalog` at 01:49:05,
  `get-catalog` *"Catalog not found."*; `deregister-resource` at 01:49:08, `describe-resource` *"Entity not
  found"*; `disassociate-data-share-consumer` at 01:49:23; `deregister-namespace` at 01:49:24, *"Deregistering"*,
  the datashare still `AUTHORIZED` to `DataCatalog/<account>` five seconds later and gone at 01:52:25. The
  orchestrating session was told before the applies. `sandbox/data/` off: *"Plan: 0 to add, 1 to change, 0 to
  destroy."*, applied 01:51:04 to 01:51:20, the key policy back to `EnableKeyAdministrationInThisAccount`,
  `AllowSandboxLakeAccessRoleViaS3` and `AllowRedshiftServerlessViaServiceInThisAccount`. `sandbox/warehouse/` off:
  *"Plan: 0 to add, 0 to change, 2 to destroy."*, applied 01:51:53 to 01:52:03, `get-role` `NoSuchEntity`. Both
  re-planned *"No changes."* by 01:53:11; `glue get-catalogs` lists none, and Lake Formation no datashare. The
  first `sandbox/data/` plan, at 01:50:10, had failed *"No valid credential sources found"*, `AWS_PROFILE` unset.
- **[Claude] The closing reads**, 01:53:11: `awsds-sandbox-warehouse` `AVAILABLE` at 4 RPU, no cluster;
  `warehouse.py` `WH-8` green, *"1 namespace(s), 1 workgroup(s), all expected"*, and `WH-9` reading
  `eighth-experimentation`'s `redshift-serverless.redshift` with `lineageSync` off.
- **[Claude] Rollback item 5**, after Stage 19 5.4's `REVOKE` (that stage's log): `lab` read at 01:57:00, six
  relations, `trades_hot_by_desk` the view, no `trades_from_lake` and no materialized view. `DROP VIEW
  lab.trades_hot_by_desk` at 01:57:33, then `DROP TABLE` of `lab.trades_hot_daily`, `lab.trades_hot_by_day` and
  `lab.trades_hot`, each `FINISHED` by 01:57:42; `lab` keeps `hello` and `hello_jupyter_via_access` (6h 6.4).
- **What stays**: the data product `sandbox-trades-hot`, its listing and its assets stay published over the
  dropped relations, with the source `sandbox-lab-trades-hot`, rollback item 1's second half. Pass 5 and the bill
  of the managed workgroup's nine minutes (6.5) are owed.

## 2026-11-23 — The lowering of §N.10's day 2 and §R's readings

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's word in this session's chat, *"Descer e
revogar"*, answering *"Desço agora (`make down ENV=sandbox` e `make hub-down`) e revogo as duas
assinaturas, ou só desço?"*. The `make` targets with `AUTO=1` from this session's shell, the reads as the
infrastructure user with `InfrastructureAccess`. The revocations of Stage 19 4.12 and Stage 20 5.0 ran during
the down, needing nothing up (both logs). Times UTC.*

- **[Claude] The portal**: the one tab of this sitting, in the Data Scientist User's Chrome session, closed at
  02:15:41 (`sagemaker-application.md` §D).
- **[Claude] `make down ENV=sandbox`**, 02:15:48 to 02:26:52, rc 0. The Studio apps step found no running app
  in Sandbox's nine domains. `probes` destroyed 4 resources (the two instances and their security groups),
  `warehouse-compute` 2 (`aws_redshiftserverless_usage_limit.compute` and the workgroup, 1m13s), `egress` 34,
  its last interface endpoint after 2m26s.
- **[Claude] `make hub-down`**, 02:27:43 to 02:27:48, rc 0: `awsds-prod-proxy` and `awsds-prod-vpn` stopped.
- **[Claude] `make status`**, 02:27:56: passive and active burns 0.0000 USD; every `[E]` slice down in the
  three accounts, the VPN, proxy and GitLab hosts stopped, no Studio app billing, no EMR Serverless
  application started and no OpenSearch Serverless collection.
- **[Claude] §R's readings**, 02:28:15: `./aws/egress.py awsds-infra-prod awsds-infra-staging
  awsds-infra-sandbox-1` *"all checks passed"*, `EG-5` read; §R's loop lists no Studio app in the nine
  domains; `list-workgroups`, `list-managed-workgroups` and `describe-clusters` answer empty in Sandbox.
  `catalog.py`, 02:29:25 to 02:32:30, *"all checks passed"*.
- **What N.10's day 2 leaves of this stage**: pass 5, on a Sandbox sitting with no warehouse; rollback item 1's
  second half, the data product `sandbox-trades-hot` with its listings and the source `sandbox-lab-trades-hot`,
  needing nothing up; 6.5's bill of the managed workgroup, read the day after.

## 2026-11-23 — Rollback item 1's second half: pass 2's data product, its assets and the source deleted

*Claude, in the session of `promotion.md` §N.10's day 2, on the user's word in this session's chat, *"Fazer
agora"*, answering whether to unpublish and delete `sandbox-trades-hot` and the source
`sandbox-lab-trades-hot` now or after pass 5. The portal's acts in the Data Scientist User's Chrome session, in
`eighth-experimentation`, in `catalog.md` §A's order, each object read on its page before its delete. The CLI
login had expired at 02:56, so no trail was read. Times UTC, the shell's clock read after each confirmation.*

- **[Claude] The data product** `sandbox-trades-hot` (`614tardy0iah3k`), read first: *Published*, two included
  assets, *Subscriber count* 0, published revision 2. *Actions → Unpublish*, whose dialog says the product can
  no longer be viewed or subscribed to, assets available only through it go with it, active subscriptions
  remain and individually published assets are not affected: *"Data product unpublished successfully."* by
  03:08:04, the page reading *Not published*. *Actions → Delete* (*"This action cannot be undone. All
  associated metadata will be permanently removed."*) by 03:08:31; the project's *Data products* tab then lists
  `my-data-product` alone.
- **[Claude] The assets**, each read with *Subscriber count* 0 and *No associated data products*: `trades_hot`
  (`cgpzdjxcumuzrk`, listing `cl14qzshdc64y8`) unpublished by 03:09:43 and deleted by 03:10:13; the view
  `trades_hot_by_desk` (`4o4k5h7uxxsj68`, listing `5t9cxrhio6c8eo`) unpublished by 03:11:03 and deleted by
  03:11:33; `trades_hot_daily` (`57py2yrv0o93ww`), *Not published yet*, deleted by 03:12:20. The unpublish
  dialog: the asset no longer discoverable, pending access requests cancelled, existing access kept. The
  generated business-name suggestions on each page were left unanswered.
- **[Claude] The source** `sandbox-lab-trades-hot` (`brnatob4h2kwb4`), read first: Amazon Redshift on
  `redshift-serverless.redshift`, *Ready*, two on-demand runs on 2026-11-22, the second adding the three assets.
  *Actions → Delete data source* (*"Deleting this data source will not delete assets it has already published,
  but no new runs will occur."*): *"Data source deleted."* by 03:13:10, the list reading *Deleting*, then four
  sources.
- **[Claude] The reads after**: the inventory holds `house-price`, `trades`, `to-run-in-background-tytue9` and
  `trades_notional`; a search of the entire catalog for `trades_hot` and for `sandbox-trades-hot` answers *No
  results found*. The tab closed at 03:14.
- **What is left of this stage**: pass 5 with its own rollback; 6.5's bill.

## 2026-11-23 — 6.5's Redshift half and 6.4's price of the managed workgroup, read with nothing up

*Claude's hand, in the session "Applies e infraestrutura SSO", on the user's *"Sim, registre"* in that session's
chat. The reads as the infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1` (`Sandbox
Account 1`), from 15:14 to 15:35: CloudWatch, Sandbox's trail and the user's reading of the trial's balance,
pasted at 15:05 (5b's log). Times UTC.*

- **[Claude] The managed workgroup's meter**: its `AWS/Redshift-Serverless` metrics publish under its own
  `workgroupId`, `fe7eb678-d356-477a-9f3a-1a4055bde9dc`, which `DeleteManagedWorkgroup`'s response gives
  `<account>:stage21_warehouse`: 23,040 `ChargedSeconds` and 4 `ComputeSeconds`, in the 01:30 interval alone.
  `redshift-data.amazonaws.com` called `GetCredentials` on that workgroup for
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` at 01:41:06, 01:41:57 and 01:43:26, one call per preview of
  4.6.
- **[Claude] The consumer's workgroup** `redshift-serverless-workgroup-dahsfn6j8lqec0`: 960 `ChargedSeconds` and
  126 `ComputeSeconds`, in the 23:30 and 00:00 intervals.
- **[Claude] The bill**: 2.30 USD and 0.10 at 0.0001 USD per RPU-second, both absorbed by the free trial, whose
  balance fell 3.22 USD after day 1's reading against 3.144 of `ChargedSeconds` over the warehouse and these
  two (5b's log, the user's *"$282.94 out of $300.00"*). xii's bill is answered; the base capacity stays unread.
  Cost Explorer's bill by service, the rest of 6.5, waits until it holds both days (`SUP-142`).
- **[Claude] The trail**: `CreateManagedWorkgroup` at 01:39:23 and `DeleteManagedWorkgroup` at 01:48:49, each in
  the infrastructure user's session with `invokedBy` `glue.amazonaws.com`, where the read at 01:44 found no
  creation (`SUP-045`); no `CreateCluster` over the sitting (Stage 9's 9.5a).
- **[Claude] Records**: this stage's `Status` row; `SUP-474`; 6.4's price in `docs/PRICING.md` §5, written with
  the readings (5b's log).

## 2026-11-23 — Pass 5's pre-flight, with nothing up

*Claude, in the session "N.10 dia 2, o resto: Stage 21 pass 5", started by the orchestrating session for
`promotion.md` §N.10's day 2's rest beside R2. Reads as the infrastructure user with `InfrastructureAccess`
through `awsds-infra-sandbox-1` (`Sandbox Account 1`) and `awsds-infra-data` (Data Governance), 15:58 to
16:10; no AWS write, nothing clicked in Chrome. Times UTC.*

- **[Claude] `make status`**, 15:58 to 15:59: passive and active burns 0.0000 USD, every `[E]` slice down, no
  Studio app billing.
- **[Claude] The ids pass 5 names**: the domain `awsds-studio` (`dzd-d8yrvx1ko7im6o`, `AVAILABLE`); the
  producer `eighth-experimentation` (`avhvbqn37ty7m8`) and the consumer `test-experimentation`
  (`4gqfau9xuo6e4w`). The project database is `glue_db_blerpkhn9nj7o0`, its `LocationUri`
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/`, holding the link
  `trades` alone; its source `5w1ic2yqcs5uog` runs daily at 21:25 UTC with `INCLUDE *` and `publishOnImport`
  false, last run `SUCCESS` on 2026-11-22. The producer's inventory holds `house-price`, `trades`,
  `to-run-in-background-tytue9` and `trades_notional`.
- **[Claude] Nothing of pass 5 exists**: no object and no version under `shared/stage21` or
  `dev/data/catalogs/stage21` (the bucket's versioning is `Enabled`, so the rollback's deletes leave
  noncurrent versions behind delete markers); `GetTable` on `stage21_images` answers `EntityNotFoundException`
  in the five project databases of both projects; a search for `stage21` finds no asset, no data product and
  no listing.
- **[Claude] The S3 Access Grants baseline**: the instance `default`, created 2026-08-22; seven locations, the
  lake's and one per project for `eighth-experimentation`, `test-experimentation`, `app-etl-dev`,
  `app-dbt-dev`, `app-ml-dev` and `app-genai-dev`, the last three created 2026-11-19, each with its project
  role; five grants, none from a subscription. Among them, `READWRITE` to `DataScientistAccess` on
  `eighth-experimentation`'s location with the scope `…/avhvbqn37ty7m8/shared/*`, since 2026-08-24 (Stage
  16's laptop vending), which already covers the prefix pass 5 publishes; 5.4's grant is read against these
  five.
- **[Claude] 5.5's question, from the records**: `sandbox/egress/` declares no `s3control` interface endpoint,
  and `SUP-091`'s reading of 2026-11-21 has a space's S3 Access Grants plugin reach
  `<account>.s3-control.us-west-2.amazonaws.com` through the proxy (`200 TCP_TUNNEL`). The plugin falls back to
  the project role's own credentials after a refused `GetDataAccess` (`SUP-093`), so 5.5's refusals are read in
  the trail's `GetDataAccess`, never in the notebook's result.
- **[Claude] The spaces**: none in any of Sandbox's nine domains. The trail holds eight `DeleteSpace` since
  2026-11-22 20:00, each as a project role in the portal's user session: `jup8h` (`app-etl-dev`) at 20:42:36,
  `jup-app-dbt-dev` at 21:45:01, then on 2026-11-23 `default-28f1b390-…` at 01:24:51 and `code` at 01:24:59
  (`eighth-experimentation`'s two domains), `jup` at 01:25:06, `jup-test-experimentation` at 01:25:42,
  `jup-app-genai-dev` at 01:26:14 and `jup-ml-dev` at 01:26:32. Pass 5 creates a JupyterLab space in each
  project.
- **[Claude] The approval**: the Data Scientist User owns both projects, so a request the user makes in the
  portal is accepted at creation, as 2.5's was. 5.4's request goes from `test-experimentation`'s notebook as
  the project role, an IAM member of that project alone, which leaves the approval and its permission to
  `eighth-experimentation`'s owner in the portal.
- **[Claude] Chrome**: this session holds no tab group; the user's signed-in tab is outside it.
- **[Claude] 1.4's generator** run on the laptop with Python 3: 20 PNGs of 64 by 64, 177 to 180 bytes each, 80
  KB in all, 13 `warm` and 7 `cold`; seeded, so the space writes the same files and the same `VALUES`.

## 2026-11-23 — 5.1's copy, ahead of the raise: the images uploaded through the portal's S3 browser

*Claude, in the session of §N.10's day 2's rest, on the user's word in this session's chat, *"Faça o upload
agora"*, answering *"Faço agora o upload pelo portal ou espero a subida?"*, after the orchestrating session
relayed the user's request to advance every write that needs nothing up. The R2 session told first. The
portal's acts in the Data Scientist User's Chrome session, in a tab of this session's own; the reads as the
infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`. Nothing was up. Times UTC.*

- **[Claude] Where 5.1's copy ran**: the plan copies the files from an `eighth-experimentation` space; with
  no space and no endpoint, the 20 files 1.4's generator wrote on the laptop at 16:0x went up through the
  portal instead, the generator being seeded, so the files are the ones a space writes.
- **[Claude] The portal**: *Data → S3 buckets → Project bucket*, `shared`, *Actions* (*Create folder*,
  *Upload files*, *Create table from contents*, *Copy*, *Publish to Catalog*, *Add business metadata*,
  *Share*, *Delete*). *Create folder* `stage21-images`, *"Successfully created folder "stage21-images"."*; then
  *Upload files* with the 20 PNGs, *"20 files uploaded successfully."* The tree also shows *Subscribed buckets*
  beside *Project bucket*.
- **[Claude] The objects**: a zero-byte folder key `shared/stage21-images/` at 16:25:12 and the 20 PNGs from
  16:26:10 to 16:26:12, 177 to 180 bytes each, `image/png`, `aws:kms` under `alias/awsds-sandbox-project`;
  `img-00.png` read back byte-identical to the laptop's.
- **[Claude] The identity**: the trail's management events of the page are the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` in the session `<user id>@5hkjdsy3umpi1c`, the portal's
  user: `GetEnvironment`, `DescribeDomain`, `ListApps`, `ListSpaces`, Glue's `GetConnections` and
  `GetCatalogs`, then `kms:GenerateDataKey` at 16:25:11 for the folder key. The page created no space and
  started no app: none in Sandbox's nine domains at 16:27.
- **What 5.1 keeps for the raise**: the Athena CTAS of `stage21_images` in `glue_db_blerpkhn9nj7o0`, and the
  two spaces.

## 2026-11-23 — 5.2, the prefix published as an S3 Object Collection, ahead of the raise

*Claude, in the session of §N.10's day 2's rest, on the user's word in this session's chat, *"Publique
agora"*, answering *"Publico agora o prefixo no catálogo (5.2), com classification `internal`?"*. The R2
session told first. The portal's acts in the Data Scientist User's Chrome session; the reads as the
infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1` and `awsds-infra-data`.
Nothing was up. Times UTC.*

- **[Claude] The publish**: on `shared/stage21-images/`, *Actions → Publish to Catalog* opens a panel
  *"Publish asset"* that holds one choice, *Subscription approval*, *Required* (the default, kept) or *Not
  required*, and no name, description or form. *Publish asset*: *"S3 folder stage21-images has been
  successfully published to the catalog."*, the page then reading *Published*, *Business name*
  `stage21-images`, *Asset type* *S3 Object Collection*, and the tabs *Objects*, *Details*, *Lineage*,
  *Data quality* and *Subscriptions*.
- **[Claude] The business metadata, after the publish**: the description *"Stage 21 pass 5: 20 synthetic
  single-colour PNG images (64x64), generated by a seeded script; their attributes are in the table
  stage21_images."* (*"Description updated successfully"*), then *Add Form* → `classification` (*"The data
  product's classification: public, internal, restricted or personal."*), valued `internal` (*"Form added
  successfully"*). The page then offered *Re-publish asset* (*"New revision is available to publish."*),
  whose panel is the publish's; re-published with *Required*.
- **[Claude] The asset** `dsmm79zurlnbww`, type `amazon.datazone.S3ObjectCollectionAssetType` revision 17,
  owned by `eighth-experimentation`, created by the Data Scientist User: revisions 1 at 16:34:05, 2 at
  16:34:08 (the publish), 3 at 16:35:14 (the description) and 4 at 16:35:59 (the form). Its
  `externalIdentifier` is the project id followed by the prefix's ARN with no separator,
  `avhvbqn37ty7m8arn:aws:s3:::awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/stage21-images/`.
  Its forms: `S3ObjectCollectionForm` (type revision 7) with `bucketName` empty, `bucketArn` the prefix's
  ARN above, the region, and the connection `4r53hkvntmahao`, `project.s3_default_folder`, whose
  `s3AccessGrantLocationId` is `eighth-experimentation`'s location `ef8251ea-…` with
  `registerS3AccessGrantLocation` true; `SubscriptionTermsForm`, `approvalRequired` `YES`; `classification`,
  `internal`.
- **[Claude] The listing** `3rnyg9wgrg1v2o`, `ACTIVE`, created 16:34:09, updated 16:36:23, at listing
  revision 4 over asset revision 4, carrying the three forms.
- **[Claude] The trail**, read at 16:37: Data Governance holds `CreateAssetRevision` at 16:34:08 and 16:35:14
  and `CreateListingChangeSet` at 16:34:09, each as `awsds-data-studio-domain-execution`, and
  `CreateLineageNode`, `CreateLineageNodeVersion` and `UpdateLineageNode` at 16:34:09 and 16:34:22; the later
  events had not arrived. No data source was created: `eighth-experimentation` lists the same four.

## 2026-11-23 — The two spaces, 5.1's table and 5.3's data product, after the raise

*Claude's hand, in the Data Scientist User's portal session, on the user's authorization in this session's
chat of the list's acts in order ("criar os dois spaces; o CTAS; o 5.3; …"). The user raised the
environment. Times UTC.*

- **[Claude] The spaces**: opening each project's JupyterLab from the portal created its default space,
  `default-28f1b390-0041-7068-8cc7-9ccef94277d1`, with a JupyterLab app `default` on `ml.t3.medium`:
  `eighth-experimentation`'s in domain `d-p6gthxc82ckg` at 16:43:35, `test-experimentation`'s in
  `d-lfgbdrjncmsu` at 16:46:40 (app 16:46:45). `list-apps` answers eighth's app `InService` with a
  `CreationTime` of 2026-11-22 18:55:59, before its space existed.
- **[Claude] 5.1's table**: the query editor on Athena in `eighth-experimentation`, *Limit 100* off, ran
  the stage's `CREATE TABLE stage21_images` over the generator's 20 rows, the location
  `<LocationUri>stage21_images/`. `StartQueryExecution` at 16:48:29 as the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, session `<user id>@5hkjdsy3umpi1c`, in the workgroup
  `workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c`. `glue get-table`: created 16:48:31, `EXTERNAL_TABLE` with
  `table_type` `ICEBERG`, columns `object_key`, `tone`, `width`, `height`, `size_bytes`, located at
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/stage21_images`.
- **[Claude] The source's run**: *Run* on `5w1ic2yqcs5uog` (Manage → Catalog management → Data sources),
  run `4udwjanark68wg`, type `PRIORITIZED`, 16:49:45 to 16:49:48, `SUCCESS`, added 1, unchanged 1 (`trades`).
  The asset `c5mzcsflx389zk` `stage21_images`, `amazon.datazone.GlueTableAssetType` revision 24, created
  16:49:47, its `externalIdentifier` the Glue table's ARN followed by `.avhvbqn37ty7m8`; forms
  `GlueTableForm`, `DataSourceReferenceForm`, `SubscriptionTermsForm` (`approvalRequired` `YES`) and
  `AssetCommonDetailsForm`. Not published (*Publish on import* off).
- **[Claude] 5.3's product**: *Manage → Catalog management → Assets → Create → Create data product*, name
  `sandbox-stage21-images`, the description *"Stage 21 pass 5: twenty synthetic 64x64 PNGs under
  shared/stage21-images/ and their Iceberg table stage21_images, for one sitting."*, *Browse assets* listing
  both (`stage21-images` as *S3 Object Collection*, `stage21_images` as *Glue Table*), *Create*: *"Data
  product created successfully"*, the product `bgclb83agkow0g` at 16:53:14. Its page read *Publish* disabled
  until *Add Form* → `classification` valued `internal` (*"Form added successfully"*, revision 2 at
  16:54:05); no metadata rule is set (`catalog.md` §M), so whether the form or the page's load enabled it
  is not separated. *Publish* → *"This data product will become discoverable to everyone in your
  organization and they can request access to this data product."* → *Publish*.
- **[Claude] The listings**, read at 16:54 as `awsds-infra-sandbox-1` (`awsds-infra-data`, a member of
  neither project, is refused `GetDataProduct`): the product listing `cuilocp2vj9zbk`, `ACTIVE`, revision 1
  over product revision 2, its items the S3 listing `3rnyg9wgrg1v2o` revision 4 and the table's new listing
  `4m03acvondth1s` revision 1, its forms `ownedByDataProductListing` naming both and `classification`
  `internal`. The table's listing reads `INACTIVE` on `get-asset` and `search-listings` returns it under no
  name: the product's publication published the table reachable through the product alone (`catalog.md`
  §P). The S3 listing stays `ACTIVE`, published on its own at 5.2.

## 2026-11-23 — 5.4 to 5.6: the product subscribed, an image read, a second subscription that writes

*Claude's hand, on the same authorization. The requests ran in `test-experimentation`'s space terminal as
its project role; the revocations in the Data Scientist User's portal session as `eighth-experimentation`'s
owner. Reads as `awsds-infra-sandbox-1` and `awsds-infra-data`. Times UTC.*

- **[Claude] 5.4, the request**: `create-subscription-request` on the product listing `cuilocp2vj9zbk` for
  the project `4gqfau9xuo6e4w`, the caller `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw/SageMaker`, at
  16:59:40: request `6mias4doyrhes0` answered `ACCEPTED` at creation, `reviewerId` null, its `createdBy` the
  Data Scientist User's id, owner of both projects, and not the role; the subscription `b6uw188klp591s`
  `APPROVED` at the same instant. No read-only approval was offered: DataZone resolved the space's
  project-role session to the space's user, so the pre-flight's way around the shared owner did not
  separate the identities. The Data Governance trail records the request with no `userIdentity.arn`.
- **[Claude] 5.4, the grants**: two subscription grants by `SYSTEM`, one per item. The S3 item's
  `41lmo2ob4vrngw` (target `dg143yovd8itu8`, the listing `3rnyg9wgrg1v2o`) `COMPLETED` at 17:00:55; the
  table's `5b711vxrc27e34` (target `ai0iw2p6vlxw5s`, the listing `4m03acvondth1s`) `COMPLETED` at
  17:00:32, `targetName` `stage21_images`. Neither carries `permissions` or `assetScope`.
- **[Claude] 5.4, S3 Access Grants**: one new grant `2459c1ea-5c0f-4b23-a725-56d2296c4562`, created
  17:00:46 by `CreateAccessGrant` as `eighth-experimentation`'s project role in session
  `AWSDataZone-Subscriptions`, invoked by `datazone.amazonaws.com`: grantee type `IAM`,
  `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw`, permission `READ`, location `ef8251ea-…` (the
  producer project's, whose role is the producer's project role), scope
  `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/stage21-images/*`, no
  application. The locations stay seven and the five baseline grants unchanged.
- **[Claude] 5.4, the Glue item (`CT-17`'s shape)**: `SELECT` on `glue_db_blerpkhn9nj7o0.stage21_images`
  to the account's `IAMPrincipals`, last updated 17:00:14 by the producer's project role (Stage 19
  verification vi's shape; `list-permissions` prints no condition), and the resource link
  `glue_db_4zojr4rr6bmnww.stage21_images` in the consumer's database.
- **[Claude] 5.5, the notebook**, `test-experimentation`'s terminal as the project role, from 17:02:27:
  a direct `aws s3 cp` of `img-00.png` answered *"An error occurred (403) when calling the HeadObject
  operation: Forbidden"*; `get-data-access --permission READ` on the scope answered credentials expiring
  18:02:29, `MatchedGrantTarget` the scope; on `shared/*`, *"You do not have READ permissions to the
  requested S3 Prefix"*; `--permission WRITE` on the scope, *"You do not have WRITE permissions to the
  requested S3 Prefix"*. The vended credentials are a session of the producer's project role,
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/access-grants-32edee89-…`. With them `img-00.png`
  downloaded, MD5 `3e79bce7e8ebb78d64ef14e0701b1b7b`, the generator's; `aws s3 ls` of the scope 21 lines;
  `aws s3 ls` of `shared/` refused, *"not authorized to perform: s3:ListBucket … because no session policy
  allows the s3:ListBucket action"*; an upload under the scope refused, *"not authorized to perform:
  kms:GenerateDataKey on resource: … because no session policy allows the kms:GenerateDataKey action"*.
  The write's refusal names KMS, so S3's decision on `s3:PutObject` is not read from it.
- **[Claude] 5.5, the portal**: `test-experimentation`'s *Data → S3 buckets → Subscribed buckets* lists the
  prefix with its 20 objects (177 to 180 bytes, 2026-11-23 13:26 local); opening `img-00.png` rendered the
  image, with *Download* and *Copy*.
- **[Claude] 5.5, the trail**: every `GetDataAccess` carries `eventSource` `s3.amazonaws.com` and the host
  `<account>.s3-control.us-west-2.amazonaws.com`. The terminal's three (17:02:29 to 17:02:31) as
  `…/SageMaker`, from `10.20.66.248` through `vpce-0cc3e139c1167ca83`, Sandbox's S3 gateway endpoint
  `awsds-sandbox-s3-gateway`: the terminal sets no `HTTPS_PROXY`, `HTTP_PROXY` or `NO_PROXY`. The
  portal's two (17:03:39 the prefix, 17:03:49 `img-00.png*`) as the consumer's project role in the user's
  session `28f1b390-…@bi356s1sacz0cw`, from the laptop's public address, with no endpoint id.
- **[Claude] 5.6, the revocation**: the product's *Subscriptions → Access*, the row *Shared*, *View access
  details* (*Shared by* the Data Scientist User, no permission shown), then *Revoke* (*"To confirm revoke,
  type 'confirm'"*, no option to keep the access). `RevokeSubscription` at 17:06:02 as
  `awsds-data-studio-domain-execution` in the user's session; the subscription `REVOKED`, both grants
  `REVOKE_IN_PROGRESS` at 17:06:32; `DeleteAccessGrant` at 17:07:04 by the producer's project role
  (`AWSDataZone-Subscriptions`). At 17:07:35 `get-data-access` READ answered *"You do not have READ
  permissions"*, while the credentials vended at 17:02:29 downloaded `img-01.png` at 17:07:36.
- **[Claude] 5.6, the second request**: on the product listing with `--asset-permissions
  'assetId=dsmm79zurlnbww,permissions={s3=[READ,WRITE]}'`, at 17:07:53: *"ValidationException … assetPermissions
  is only supported for S3ObjectCollection Listing"*. On the S3 listing `3rnyg9wgrg1v2o` with the same
  permissions, at 17:08:19: request `cka9znwbot9oy8` `ACCEPTED` at creation, subscription `cbfstcg0z2she8`
  `APPROVED`. `CreateAccessGrant` at 17:08:36: grant `1b8bfd2b-e352-472b-9d5a-ba23787f1fe6`, the same
  grantee, location and scope, `READWRITE`. A product's subscription grants its S3 item `READ`; write is
  asked on the asset's own listing, and only an asset published on its own has one.
- **[Claude] 5.6, the write**: `get-data-access --permission READWRITE` at 17:09:12, credentials expiring
  18:09:13, a session `access-grants-f84bf4dd-…` of the producer's project role; `written-5-6.png` (a copy
  of `img-01.png`) uploaded, `head-object` 178 bytes, `aws:kms`, version `JBaWjkchDqVZkWHuo7CqshDORAA0obT7`,
  last modified 17:09:16.

## 2026-11-23 — 5.7: the revocation with credentials vended just before, then the catalog's rollback

*Claude's hand, on the same authorization. The loop ran in `test-experimentation`'s space terminal as its
project role (`nohup bash /tmp/p57.sh`, 51 rounds about 34 s apart from 17:09:51): each round asked
`get-data-access --permission READ --duration-seconds 900` on the scope, then read `img-02.png` with three
held credentials. The revocation and the deletions ran in the Data Scientist User's portal session as
`eighth-experimentation`'s owner. Times UTC.*

- **[Claude] The held credentials**: `rw3600`, 5.6's `READWRITE` session, expiring 18:09:13; `r900`, a
  `READ` session vended at 17:09:49 for 900 s, expiring 17:24:50; `late`, the loop's last answered vend,
  17:10:26, expiring 17:25:27.
- **[Claude] The vend door**: the rounds at 17:09:51 and 17:10:26 answered; every round from 17:11:01 to the
  last was refused, *"An error occurred (AccessDenied) when calling the GetDataAccess operation"*. The
  portal's revocation of `cbfstcg0z2she8` recorded `RevokeSubscription` at
  17:11:12 and `DeleteAccessGrant` of `1b8bfd2b-…` at 17:11:14, so the refusal at 17:11:01 to 17:11:03
  precedes both in the trail by about nine seconds. Unexplained on this reading.
- **[Claude] The held credentials after the revocation**: `r900` read through 17:24:20 and failed from
  17:24:55; `late` read through 17:24:55 and failed from 17:25:29. Each failure is the CLI's *"An error
  occurred (400) when calling the HeadObject operation: Bad Request"*: `aws s3 cp` starts with a `HEAD`,
  whose response carries no error body, so the expired token surfaces as a bare 400 and not as
  `ExpiredToken`. `rw3600` read in every round, the last at 17:38:45, and at 17:30:36 uploaded
  `written-5-7.txt` (16 bytes, last modified 17:30:38) under the scope, 19 minutes 24 seconds after
  `DeleteAccessGrant`.
- **[Claude] 5.7's answer** against the page's *"credentials can be used for 15 minutes"*: a credential
  vended before a revocation lives its own duration, which the subscriber chooses; 5.5's call without
  `--duration-seconds` was given 3600 s, and those credentials wrote after the revocation.
- **[Claude] The catalog's rollback**, in `catalog.md` §A's order: the product `bgclb83agkow0g` was
  unpublished (*"Data product unpublished successfully"*) and deleted (*"This action cannot be undone. All
  associated metadata will be permanently removed."*); the S3 asset `dsmm79zurlnbww` unpublished (the
  dialog: *"This asset will no longer be discoverable and all pending access requests will be canceled.
  Users with existing access will retain their permissions."*) and deleted; the table asset
  `c5mzcsflx389zk`, read *"This asset is unpublished"* once the product was gone, deleted. The project's
  *Assets* page lists `house-price`, `trades`, `to-run-in-background-tytue9` and `trades_notional`, and its
  *Asset type* filter no longer offers *S3 Object Collection*. The data source `5w1ic2yqcs5uog` stays.
- **[Claude] Rollback item 5**, in `eighth-experimentation`: the query editor on Athena ran `DROP TABLE
  glue_db_blerpkhn9nj7o0.stage21_images` (*"Query executed successfully"*); the database then lists `trades`
  alone, and its Iceberg location `dev/data/catalogs/stage21_images` lists no object, with 4 noncurrent
  versions and 7 delete markers. From a new JupyterLab terminal as the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, the prefix read 23 entries (20 PNGs, `written-5-6.png`,
  `written-5-7.txt`, the folder key) and `aws s3 rm --recursive` of `shared/stage21-images/` ran at
  17:39:17; the prefix then lists nothing, with 23 noncurrent versions and 23 delete markers left to the
  bucket's lifecycle. The loop was stopped and the held credentials' files removed from the space first.
- **[Claude] The spaces**: *Code Spaces*, the card's *Delete*, the word *confirm*: eighth's
  `default-28f1b390-…` in `d-p6gthxc82ckg` at about 17:41, test's in `d-lfgbdrjncmsu` at about 17:42, both
  read *Deleting* and then *"You don't have any code spaces"*. Both portal tabs closed at 17:43.
- **[Claude] The trail, re-read at 17:50** through the CLI's cached role credentials, the SSO token having
  expired at 17:15:22: Sandbox's `GetDataAccess` at 17:11:03 carries `AccessDenied`, *"You do not have READ
  permissions to the requested S3 Prefix"*, the grant register's wording, `durationSeconds` 900. Between the
  last answered vend (17:10:27) and that refusal, the only S3 Control events are AWS Config's
  `GetAccessGrant` and `ListTagsForResource` at 17:10:40; `DeleteAccessGrant` follows at 17:11:14, so no
  write precedes the refusal in the trail. Data Governance's: the product's `UNPUBLISH` change set at
  17:24:52, `DeleteListing` of `cuilocp2vj9zbk` at 17:27:16 in the user's session (and one by
  `datazone.amazonaws.com` the same second), `DeleteDataProduct` at 17:27:17, the S3 asset's `UNPUBLISH` at
  17:28:01, `DeleteAsset` at 17:28:25 and 17:29:11. `get-asset` on both ids and `get-data-product` answer
  `ResourceNotFoundException`.
- **[Claude] What stays**: S3 Access Grants holds the five baseline grants and the seven locations,
  `ef8251ea` (`eighth-experimentation`'s folder) among them. The producer's project role reads
  `MaxSessionDuration` 3600; a vend longer than 3600 s was not attempted. The projects bucket is versioned,
  its rule `expire-noncurrent-versions` at 90 days, so the 27 noncurrent versions left by item 5 expire in
  February 2027.

## 2026-11-23 — The orchestrator's checks, the pull request and the lowering of Sandbox

*Claude's hand unless an entry names another; the orchestrating session's readings are its own, relayed to
this session and recorded here. Times UTC.*

- **[orchestrator] Acts 1 and 2 read at 17:27** as the infrastructure user in Sandbox: both JupyterLab spaces
  `InService` with their app on `ml.t3.medium` `InService`, in `d-p6gthxc82ckg` created 16:43:35 and in
  `d-lfgbdrjncmsu` 16:46:40; `glue_db_blerpkhn9nj7o0.stage21_images` `ICEBERG`, created 16:48:31, under
  `…/avhvbqn37ty7m8/dev/data/catalogs/stage21_images`.
- **[Claude] The checking protocol** (a report after each act, the orchestrator's *verificado* awaited before
  the catalog's rollback and before the lowering) reached this session after act 11, the message having
  queued during the turn, so the catalog's rollback ran without that check. The report of acts 3 to 11 went
  at about 17:47. At 17:48 `list-spaces` and `list-apps` read 0 and 0 in both domains.
- **[orchestrator] Acts 3 to 11 read at 17:49**, from the state the rollback left: the nine Sandbox domains
  hold zero spaces and zero apps; `stage21_images` answers `EntityNotFoundException`; the assets
  `dsmm79zurlnbww` and `c5mzcsflx389zk`, the product `bgclb83agkow0g` and the listing `cuilocp2vj9zbk` answer
  `ResourceNotFoundException`, while the positive control `bra0895x5fjzww` reads `trades`, so the absence is
  a deletion and not a lack of visibility; S3 Access Grants holds 5 grants and 7 locations, none naming
  `stage21`; `shared/stage21-images/` holds 0 current objects, 23 versions and 23 delete markers. Act 12
  checked on its side, to wait on the user's login.
- **[Claude] The pull request**: the branch synced with `origin/main` at
  `495ebb1a15b402965ba05ffb1f72b41a21007fb4` by a merge, `make check` *"check: OK"*, `check-aws-supplement.py`
  *"OK"*; pull request #394 opened at about 17:51, its CI passing.
- **[user] `./aws/login.py`** at about 18:09; the `awsds` token expires at 19:08:45, and `sts` answers as
  `InfrastructureAccess`.
- **[Claude] `make status` at 18:09**: Sandbox's `egress` `UP` with 27 resources and 18 interface endpoints,
  `probes` `UP` with 4, `warehouse-compute` down; no Studio app billing in any account; passive burn 0.8759
  USD/h across the estate, the hub, GitLab, its runners and the egress of Staging and Production included.
  R2 and the orchestrator told at 18:10, R2's copy queued behind its running turn.
- **[Claude] The first `make down ENV=sandbox`**, 18:11:09 to 18:11:47: `sandbox/probes` planned *"Plan: 0 to
  add, 0 to change, 4 to destroy."*, then *"Error: error asking for approval: EOF"*: the command ran with no
  terminal to answer Terraform's prompt. *"HALTED at terraform-live/sandbox/probes: terraform destroy failed
  above. The rows after it are untouched: terraform-live/sandbox/warehouse-compute,
  terraform-live/sandbox/egress."* Nothing was destroyed. The second run, `make down ENV=sandbox AUTO=1`,
  started at 18:12:50.
- **[Claude] The second run, `make down ENV=sandbox AUTO=1`**, 18:12:50 to 18:23:12: `sandbox/probes` *"Destroy
  complete! Resources: 4 destroyed."*, `sandbox/warehouse-compute` *"No changes. No objects need to be
  destroyed."*, `sandbox/egress` *"Plan: 0 to add, 0 to change, 27 to destroy."* then *"Destroy complete!
  Resources: 27 destroyed."*; the twelve `[P]` slices and `bootstrap/` refused as always; the Studio-app hook
  found no running app in the nine domains.
- **[Claude] §R's readings**: `make status` at 18:24:52 reads Sandbox's three `[E]` slices down with 0
  resources, no Studio app billing and no EMR Serverless application or OpenSearch Serverless collection in
  any account; the estate's passive burn 0.6875 USD/h and its active burn on `production/egress`,
  `production/workloads-egress` and `staging/egress`, R2's. `./aws/egress.py awsds-infra-prod
  awsds-infra-staging awsds-infra-sandbox-1` wrote *"all checks passed"*, Sandbox at 0 interface endpoints, 0
  NAT gateways, 0.000 USD/h, the 34 endpoints left in Production and Staging. §R's `list-apps` loop over
  Sandbox's domains printed nothing at 18:26:48. R2 and the orchestrator told at about 18:27.
- **[orchestrator] Act 12 read at 18:27:48** by `make status`: `sandbox/egress` down with 0 resources (state
  serial 566), `sandbox/probes` down with 0, `sandbox/warehouse-compute` down, no Studio app in any account,
  the estate's passive burn 0.6875 USD/h, the hub, GitLab, its runners and the egress of Staging and
  Production, all R2's.
- **[Claude] `./aws/catalog.py`, live**, 18:27:16 to 18:33:01 after the lowering: *"all checks passed"*, 14
  `pass` and 7 `note` over 12 listings; `CT-20` a note, *"no fulfilment among 5 grant(s); 0 S3 Object
  Collection listing(s)"*, the state the rollback left. `--self-check`: 47 of 47.

## 2026-11-23 — The user's decisions on pass 5's open questions

*The user's hand, in the orchestrating session's chat at about 18:3x UTC, relayed to this session by the
orchestrator; recorded by Claude. The recommendations went to the orchestrator at about 18:29.*

- **[user]** *"Aceito as três recomendações do N.10."*, which takes:
  1. **`TM-37` accepted**, option (a): the residual of sessions vended before a revocation, up to the
     producer role's 3600 s, with Sandbox's trail as its detection; reopened if AWS ends vended sessions at a
     revocation. Set aside: (b) IAM's *Revoke active sessions* on the producer's role at each revocation; (c)
     leaving it to Stage 11's review.
  2. **5.4 not run again** with a requester outside the owning project (`SUP-480`), option (a): the manual
     approval rests on Stage 19's measurement of 2026-11-22, and the S3 Object Collection's own half, the
     grant written on approval, was measured at 5.4 and 5.6.
  3. **The refusal of 17:11:03 recorded as observed and closed**, option (a): one occurrence, a refusal that
     came early rather than late. Set aside: a support case with AWS, a re-measurement with a tighter loop.
- **[Claude] Records**: `TM-37` and its channel row accepted in `threat-model.md`; the stage file's `Status`
  row.

## 2026-11-23 — `catalog.py`'s `CT-17` and `CT-18` read a table its data product's publication listed

*Claude's hand, in a session the orchestrating session started for this follow-up of the pass 5 report, with
AWS reads alone. Times UTC.*

- **[Claude] The change** (`aws/catalog.py`): `road_listings` builds the listings both ends of the catalog road
  judge from `search-listings`' rows and `get-listing`'s answers. A data product listing's items are read from
  its `items` and its `ownedByDataProductListing` form, the two naming the same listings in 5.3's
  `cuilocp2vj9zbk`; each item `search-listings` did not return is read with `get-listing` and, when it holds a
  `GlueTableForm`, judged as a listed table, owned by the project its listing names or else by the product's.
  `CT-17` and `CT-18` name such a table in their detail. `CT-18` keeps Stage 19 decision 4's rule, the form on
  the table's own listing, and a table with none fails with its product's form named: 5.3's product, its
  table with no form and the product `internal`, is that case, run on samples alone. A failed `get-listing` on
  an item leaves `CT-10`, `CT-11` and `CT-16` to `CT-19` a note.
- **[Claude] `./aws/catalog.py --self-check`**: *"56 of 56 cases as expected"*, nine new cases on 5.3's shape:
  the table read beside a searched one, an item in the forms alone, the owner taken from the product, a failed
  read, a lake table on the lake's road, an S3 Object Collection on neither road, the subscriber's grant
  explained, and both `CT-18` sentences. Five mutants of the new code each read red: no read of the omitted
  items 49 of 56, no `ownedByDataProductListing` 55, no owner fallback 55, no product named 54, an S3 Object
  Collection judged as a table 55.
- **[Claude] `make check`**: *"check: OK"*.
- **[Claude] `./aws/catalog.py`, live**, 18:55:16 to 19:05:26 as the infrastructure user, `InfrastructureAccess`
  in Data Governance, Sandbox, Staging and Production: *"all checks passed"*, 14 `pass` and 7 `note` over 12
  listings, no call failed. The two data product listings, `my-data-product` and `trades-notional`, carry items
  `search-listings` returns, so no table was read through a product alone: `CT-17` *"13 grants on
  app_etl.trades_notional, mydatabase.house-price: 1 fulfilment(s), each an approved subscription's, and 12 the
  owning project's or the blueprint's"*, `CT-18` *"house-price public; trades_notional internal"*, the readings of
  18:27. The self-check is the proof; whether `get-listing` answers an `INACTIVE` listing to
  `InfrastructureAccess` in Data Governance is not measured.
- **[Claude] Records**: `SUP-482`'s later reading; `catalog.md` §P and §V; the stage file's `Status` row.
