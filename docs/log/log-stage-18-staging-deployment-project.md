# Log — Stage 18 — A deployment-only SageMaker project in Staging

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-18-staging-deployment-project.md`](../plan/stages/stage-18-staging-deployment-project.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-17 — the stage written in a cloud session, nothing run in AWS

- **[user] Staging is measured before D41 item 2 is revisited.** In a thread of the Claude project, the
  card of 2026-10-16 15:59 UTC asked *"Medir um projeto só de implantação em Staging antes de rever a
  D41?"*, its first option *"Medir antes"* reading *"Escrevo num PR do AWS-DataScience um passo que cria
  em Staging um projeto só de implantação; a D41 vale até o resultado."* At 18:28 UTC the user answered
  in words, *"Ok, vamos medir em staging o que falta para completar o quadro."*, with three lines of
  investigation that the stage file holds as questions viii to x, and the session closed the card on
  *"Medir antes"*. The stage is PR #156, merged at 21:03 UTC as `f8e5285`. The cloud session holds no
  AWS credential: no `aws` call ran in it, so nothing in this file is a measurement of AWS.
- **[Claude] 0.1 read in the CLI 1.0.9's sdist, nothing executed.** The stage file summarizes each
  answer with its module; the file and line of each are the 2026-10-18 entry below.
- **[user] The `process` task's volume key goes into PR #156.** At 19:54 UTC the user asked whether the
  stage could start: *"Avalie se é possível iniciar a execução do estágio 18 considerando o que já foi
  implementado do plano até o momento, ou se existe algum pré-requisito que ainda não está
  completo."* The answer was read in the repository at `main` `a10be54` and PR #156 `39bb369`: 0.1 is
  done and 0.2 and 0.4 can run from the laptop; 0.3, 0.5 and 1.3 wait on Stage 9 pass 1's
  `identity/org-policies/` apply and battery; 1.1 waits on decisions 1 to 3; passes 4, 5 and 7 wait on
  app-etl's first tag, whose bundle they deploy, and which first needs a `VolumeKmsKeyId` on the
  `process` task, since `DenySageMakerJobsWithoutVolumeEncryption` requires one under Sandbox's D13
  boundary and in `Workloads` [inferred: the application has not run]. The card of 20:00 UTC asked
  *"Corrijo agora a chave do volume (VolumeKmsKeyId) da task process do app-etl, no PR #156?"*, and at
  20:45 UTC the user chose *"Sim, no PR #156"*, whose consequence read *"A task process passa a usar a
  chave do projeto em dev e test, e a primeira tag pede duas variáveis de CI/CD novas no GitLab."* The
  change is PR #156's commit `c340648`: the stage variable `PROJECT_KEY_ARN` in both stages of
  `examples/app-etl/manifest.yaml`, from the CI/CD variables `DEV_PROJECT_KEY_ARN` and
  `TEST_PROJECT_KEY_ARN`, without which `test-deploy` stops. The user sets both in GitLab's
  `awsds/app-etl`, each to its project's `kmsKeyArn`, before the application's first tag.

## 2026-10-18 — 0.1's file and line, read again in the cloud session

- **[user] The log is asked for.** At 06:21 UTC the user asked *"Houve algum avanço no Stage 18 nesta
  sessão que deixou de ser documentada em log do estágio?"* Step 0.1 asks this log for the file and
  line of each answer, and no Stage 18 log existed, so the session read the sdist again for this file.
- **[Claude] 0.1, each answer's file and line.** The sdist is `aws_smus_cicd_cli-1.0.9.tar.gz`, sha256
  `173e91af8733f80d65bf06baf7800d33e4569a608a3982f95b8d2bd24292eff6`, PyPI's published digest. Code
  paths are under its `src/smus_cicd/`, examples under its `examples/`, and nothing was executed.
  - **A stage's project and domain.** `ProjectConfig` holds `name`, `create` (default `False`),
    `profile_name`, `owners`, `contributors` and `role` (`application/application_manifest.py:188-198`);
    `DomainConfig` holds a required `region` and an optional `name`, `tags` and `id`, and no account
    (`:17-23`). Every client is a `boto3.client` with the caller's credentials and that region
    (`helpers/boto3_client.py:15-51`), and no `assume_role` call exists in the package. `deploy` refuses
    a call with no `--targets` and deploys the first stage listed (`commands/deploy.py:348-355`);
    `destroy` refuses no `--targets` and takes every stage listed (`commands/destroy.py:70-75`); `run`
    takes every stage listed, and every stage of the manifest when `--targets` is absent
    (`commands/run.py:174-178`, the loop at `:551`).
  - **Project creation** (`helpers/project_manager.py`). With `create: false` a missing project stops the
    deploy: *"Project '…' not found, make sure the SMUS project is pre-created manually before using the
    SMUS CLI"* (`:104-108`; `handle_error` exits 1, `helpers/error_handler.py:6-9`). With
    `create: true` (`:111-113`) it calls `CreateProject` (`:497`). With no profile named it takes the
    domain's only one and refuses zero or several (`:383-395`); a name the domain does not list falls
    back to the first profile listed, printing *"⚠️ Profile '…' not found. Using default profile:
    '…'"*, and the deploy goes on (`:457-468`). `role.policies` with no ARN creates the role
    `role.name`, by default `smus-<project>-role` (`:171-187`, `:647-648`), and with an ARN attaches
    the policies to that role (`:188-197`). `PutEnvironmentBlueprintConfiguration` appears nowhere, so
    no call enables a blueprint.
  - **Two applications in one project.** A workflow is named `<application>_<project>_<workflow>`, each
    character outside `[A-Za-z0-9_]` mapped to `_` at creation (`commands/deploy.py:2165-2189`), while
    `run` and `destroy` map only `-` (`commands/run.py:557-563`; `helpers/destroy_validator.py:437`
    through `helpers/airflow_serverless.py:911-926`). It is created with the tags `Pipeline` (the
    application), `Target` (the project), `STAGE`, `CreatedBy`, `AmazonDataZoneDomain` and
    `AmazonDataZoneProject` (`bootstrap/handlers/workflow_create_handler.py:315-320`), so two
    applications in one project differ by `Pipeline` alone; `monitor` selects by `Pipeline` and
    `Target` (`commands/monitor.py:102-103`). A storage item lands at `<s3Uri>/<targetDirectory>/`, the
    connection's root with no application prefix (`helpers/deployment.py:43-44`), and the first item's
    root is the prefix `workflow.create` scans (`commands/deploy.py:597-610`, the root returned at
    `:924-925` and `:1197-1198`). The scan, `_find_dag_files_in_s3` (`:1891-1993`, called at
    `workflow_create_handler.py:219`), takes its prefixes from `_derive_workflow_search_prefixes`
    (`:1995-2017`), which tests for an attribute `target_directory` (`:2007`) that `StorageConfig`
    spells `targetDirectory` (`application/application_manifest.py:113-121`), so it always falls back
    to the whole root (`:2014-2015`). Every YAML there registers its top-level keys and nested
    `dag_id`s, the first file winning (`:1961`, `:1965`); each manifest workflow is looked up by its
    `workflowName` (`:1973-1975`), and a miss raises `WorkflowYamlNotFoundError` (`:1984`). Two
    applications with one workflow name can therefore take each other's file [inferred]. Each deploy
    writes a task's code to a new `operatorFiles/<workflow>-<epoch ms>` object and none is pruned,
    against what the code's comment calls an account-wide code-storage quota of 75 GB (`:2023`,
    `:2118-2125`). A bundle lookup takes the first zip whose name contains the application's, ignoring
    case, then any zip in the folder (`helpers/bundle_storage.py:103-158`, the fallbacks at `:131-136`
    and `:152-155`).
  - **`destroy` removes what the manifest declares.** The workflows by name
    (`helpers/destroy_validator.py:437`); the prefix `<root>/<targetDirectory>` with no trailing slash
    (`_resolve_s3_targets`, `:209-298`, built at `:241-245`), whose objects are listed by `Prefix` and
    deleted (`helpers/destroy_executor.py:351-376`, `helpers/s3.py:31-41`), so `exemplos/demo` also
    takes `exemplos/demo-x/` [inferred]; the catalog objects the project owns, manual ones included,
    only when the stage declares `deployment_configuration.catalog` without `disable: true`
    (`destroy_validator.py:540-543`, the warning at `:650-656`), which `examples/app-etl/manifest.yaml`
    does not; and the project when `project.create` is true (`destroy_executor.py:626-647`). No IAM
    role is deleted: `_delete_role` (`helpers/iam.py:177-200`) has no caller.
  - **`run`** goes the MWAA Serverless way when a workflow's connection has the type
    `WORKFLOWS_SERVERLESS` (`commands/run.py:57-73`), passes the stage's `environment_variables` as
    `OverrideParameters` (`:589-597`, `helpers/airflow_serverless.py:472-501`) and returns with the
    run id, without waiting; `--command` reaches provisioned MWAA only (`run.py:32`, `:118-120`,
    `:388`). None of `start_notebook_execution`, `start_pipeline_execution`, `create_training_job`,
    `create_processing_job`, `create_transform_job`, `create_endpoint`, `invoke_endpoint` and
    `start_job_run` appears in the package, and `destroy`'s operator registry holds `GlueJobOperator`
    alone (`helpers/operator_registry.py:46-52`). The CLI's examples train and deploy inside workflow
    tasks: `ml/training`, `ml/deployment` and `genai` through `SageMakerNotebookOperator` (line 5 of
    each workflow under `analytic-workflow/`), and `mlops-pipeline`'s `deploy_pipeline` through a
    `SageMakerProcessingOperator` that runs `deploy_model.py --endpoint-name`
    (`end-to-end-data-ml-pipeline/examples/mlops-pipeline/workflows/deploy_pipeline.yaml:9`, `:24`,
    `:37-41`), a script the sdist does not carry.

## 2026-10-18 — pass 0's readings from the laptop and 2.3 written, the environment down

*Every entry below is Claude's, session "Stage 18: readings and the deployment-members list".*

- **[Claude] The session's terms.** Started by the orchestrating session ("Execução local no Mac") on
  the user's instruction of 2026-10-18 to run every step that needs neither the environment up nor the
  user, with reads as the infrastructure user and the Terraform applies those steps need. This stage's
  share named no apply, and none ran. Every call below is the infrastructure user's, permission set
  `InfrastructureAccess`, through the `awsds-infra-*` profiles; the environment was down (0.0000 USD/h,
  read by the orchestrating session at about 19:45 UTC).
- **[Claude] 0.2, read 19:50 to 20:05 UTC.** `./aws/studio.py` at 19:50:25Z: 0 checks failed; two
  SageMaker AI domains in Sandbox, both `VpcOnly`, idle 60 min under a 120 min ceiling; 11 blueprint
  configurations; the profile `experimentation`; `test-experimentation` and `eighth-experimentation`,
  both `ACTIVE`. Each project's `Tooling` environment is the stack `DataZone-Env-<environment>`,
  created by `awsds-sandbox-smus-provisioning` with `datazone.amazonaws.com` as the source (CloudTrail's
  `CreateStack` for `test` at 2026-10-15 06:05:33Z), no stack role, termination protection off. The two
  stacks hold the same 14 resources, and their parameters differ only in the two ids:
  - `ToolingUserRole`, `datazone_usr_role_<project>_<environment>`: trusted by `datazone.amazonaws.com`
    and `auth.datazone.amazonaws.com`, by fourteen service principals (`airflow-serverless`,
    `sagemaker`, `glue`, `lakeformation`, `scheduler` and `access-grants.s3` among them) under
    `aws:SourceAccount`, by Redshift's two under an `sts:ExternalId` on the account's database users,
    and by the provisioning role; the two trusts are identical up to order. Boundary
    `awsds-sandbox-project-boundary`, sessions of one hour. Attached: `SageMakerStudioProjectUserRolePolicy`,
    `SageMakerStudioProjectRoleMachineLearningPolicy` and `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy`,
    plus this estate's `awsds-sandbox-workflows` on both, and `awsds-sandbox-bedrock-assistant` and
    `awsds-sandbox-warehouse-project-<project>` on `eighth`. Tags include
    `RedshiftDbUser=user-project@<project>` and the project's `SageMakerSpacesDomainId`.
  - `BedrockServiceRole` (trusted by `bedrock.amazonaws.com` under source account and ARN; four
    AWS-managed Bedrock service policies) and `BedrockLambdaExecutionRole` (trusted by
    `lambda.amazonaws.com`; `AWSLambdaBasicExecutionRole` and two Bedrock function policies), both
    under the boundary.
  - `SageMakerSpacesDefaultDomain`, the project's SageMaker AI domain; `ToolingSecurityGroup`
    `datazone-<project>-dev`, all traffic in from itself and all traffic out to `0.0.0.0/0`; two
    `GlueNetworkConnection`s, one per private subnet; the Athena workgroups
    `workgroup-<project>-<environment>` and `sagemaker-studio-spark-workgroup-<project>`; the prefix
    `awsds-sandbox-smus-projects/<domain>/<project>/dev` registered in Lake Formation under the project
    role, hybrid access off; the log group `datazone-<project>-dev`, 731 days, under the project key; the
    schedule group `SageMakerUnifiedStudio-<project>-dev`; `CDKMetadata`.
  - The parameters a deployment profile would turn: `enableSpaces`, `enableScheduling`, `enableAthena`,
    `enableAthenaSparkWorkgroup`, `enableGlueNetworkConnection`, `enableEmrEc2Blueprint`,
    `enableNetworkIsolation`, `enableRolesWithoutBoundary` and the four Bedrock switches `true`;
    `sagemakerDomainNetworkType` `VpcOnly`; `ec2InstanceTypes` `ml.t3.medium`; `logGroupRetention` `731`.
  - Outside the stack, read as `awsds-infra-data`, which DataZone answers on both projects: each
    project's `Tooling-default-sagemaker-modelpackagegroup-datasource` runs at the project's creation
    minute, `cron(32 17 * * ? *)` for `eighth` (55 `FAILED`, 1 `RUNNING`) and `cron(6 6 * * ? *)` for
    `test`, created 2026-10-15 06:06:40Z (2 `FAILED`, 1 `RUNNING`), every failure
    `VALIDATION_EXCEPTION`: `EXC-11`'s shape on a second project. `eighth` also holds a Glue data source
    with no schedule, and each project one `CREATE_FAILED` DataLake environment whose stack was deleted
    about 30 s after its creation. Each project has `datazone-<project>-dev/error` and `/output` log
    groups with no retention, outside the stack. Sandbox's Lake Formation admins are
    `awsds-sandbox-smus-manage-access`, `awsds-sandbox-smus-provisioning` and `InfrastructureAccess`,
    with `CROSS_ACCOUNT_VERSION` 4.
- **[Claude] 0.3, read 19:50 to 20:07 UTC.** `US-6` passes for Staging. CloudTrail's
  `datazone.amazonaws.com` events in Staging from 2026-09-18 to 2026-10-18: 7, each `ListDomains` by
  `InfrastructureAccess` refused `AccessDenied` (2026-09-19, 09-20, 10-11, 10-15, 10-17, and two at
  19:49Z on 10-18, during this session's `studio.py` run); no other principal and no other call. The
  `Workloads` document, read after the orchestrating session's apply of 19:54Z: nine statements
  (`DenyInteractiveSageMakerSurface`, `DenyDataZoneEntirely`, `DenyAthenaSparkStartSession`,
  `DenySageMakerJobsOffVpc`, `DenySageMakerInstanceCeiling`, `DenySageMakerJobsWithoutNetworkIsolation`,
  `DenySageMakerJobsWithoutInterContainerEncryption`, `DenySageMakerJobsWithoutVolumeEncryption`,
  `DenySageMakerServerlessInference`), attached to the OU `Workloads` alone, 2,499 characters, its
  content equal to the file on `origin/main` at `2074b1b`; `DenyDataZoneEntirely` is `datazone:*` with
  no condition. Staging's Lake Formation settings: no admin, no read-only admin, no default
  permission on new databases or tables, `CROSS_ACCOUNT_VERSION` 1, no registered location; this is
  what 8.6 reads back. `awsds-deploy-staging`: trusted by `awsds-prod-runner-deploy` alone, ceiling
  `awsds-staging-deploy-boundary` at v1, inline `apply-egress` (EC2 reads, its VPC's interface
  endpoints, Route 53 zone association, the DNS Firewall and its query log) and `state` (its state
  prefixes and key). `awsds-deploy-sandbox-test`, written from the CLI's 158 events in `test`, allows
  34 actions (`datazone` 12, `airflow-serverless` 9, `s3` 5, `kms` 4, `logs` 2, `ec2` 1, `iam` 1), and
  `awsds-deploy-staging` holds one of them, `ec2:DescribeVpcEndpoints`. Its ceiling denies none of the
  other 33: its denies cover role changes outside `awsds-staging-app-boundary`, the deploy identities
  and the ceilings, never `iam:PassRole` [inferred from the documents; nothing ran as the role].
- **[Claude] 0.4's reads, 20:08 UTC; the run is owed.** `list-project-memberships` on
  `test-experimentation` answered both `awsds-infra-data` and `awsds-infra-sandbox-1`: an Identity
  Center user, the data scientist, as `PROJECT_OWNER`, and the project role's IAM user profile and one
  group as `PROJECT_CONTRIBUTOR`. No member is the `InfrastructureAccess` role, and DataZone answers
  this read to it while it refuses `list-connections` (`EXC-17`). As that non-member,
  `mwaa-serverless list-workflows` returns six workflows, the CLI's
  `houseprice_etl_test_experimentation_houseprice_etl` and `houseprice_etl_eighth_experimentation_houseprice_etl`
  among them, and `get-workflow` reads the first: execution role the `test` project role, security
  groups and subnets, a customer-managed key, `manual_only`, the log group
  `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, and the tags `Pipeline=houseprice-etl`,
  `Target=test-experimentation`, `STAGE=TEST`, `CreatedBy=SMUS-CICD`, `AmazonDataZoneDomain` and
  `AmazonDataZoneProject`, which 0.1 read in the code. Question vii's finding half is answered by IAM
  alone; `start-workflow-run` and the run wait on `make hub-up` and `make up ENV=sandbox`.
- **[Claude] 0.5, cited.** The battery's phase `ou` ran once, by the orchestrating session after its
  `identity/org-policies/` apply, started 19:55:13 UTC: *"39 as expected, 0 unexpected, 7 not
  measured"*, recorded in Stage 9's log (commit `22f3422` on that session's branch). Its file
  `scp-battery-20261018T165513.txt` reads Staging's `datazone:ListDomains` `DENY-SCP` under the
  `Workloads` policy and Sandbox's `ListDomains` succeeding. It is 1.3's before; no second battery ran.
- **[Claude] 2.3 written, no row.** `scripts/tfhygiene/backend.py` gains `SMUS_DEPLOYMENT_MEMBERS`,
  empty, beside `SMUS_ASSOCIATED`, and a guard that refuses at import an account in both it and
  `SMUS_MEMBERS`; `governance/`'s `members` map and `profiles_enabled` read both lists, and the four
  other readers read `SMUS_MEMBERS` alone. `governance/`'s three comments that named `SMUS_MEMBERS`
  alone name both, and the comment on `APP_REGISTRY_CONSUMERS` drops Stage 8's retired by-hand run.
  Every slice's generated tfvars, laptop and pipeline (36 slices), and refusal 8's answers for the four
  deploy profiles are identical before and after. A simulated `staging` row, never written, changes
  `governance/`'s emission alone, `profiles_enabled` `true` after its `SMUS_ASSOCIATED` row and `false`
  before it. The re-plans, `-input=false`: `sandbox/foundation/` as `awsds-infra-sandbox-1`,
  `No changes` (20:03:11Z); `production/tooling/` as `awsds-infra-prod` with the SAML var-file,
  `No changes` (20:03:37Z); `staging/foundation/` as `awsds-infra-staging` with the alerts var-file,
  `No changes` (20:04:14Z); `data-governance/governance/` as `awsds-infra-data`, `Plan: 0 to add, 1 to
  change, 0 to destroy` (20:04:45Z), the change being `awscc_datazone_project_profile.this["experimentation"]`
  gaining the `MLflowApp` environment configuration: Stage 17 pass 1's unapplied edit (PR #157),
  nothing of 2.3's.
- **[Claude] 5.4's quotas, read 20:00 to 20:15 UTC.** DataZone in Staging and Sandbox, each AWS's
  default: `Environments in a domain` 1,000, `Data source runs/data source/day` 25, `Assets` 1,000,000,
  `Asset Types` 1,000; Service Quotas lists no project quota. MWAA Serverless in both, each the
  default: 100 workflows per account, 50 versions per workflow, 100 concurrent runs, 76,800 MB of code
  storage, 50 KB per definition, 100 KB of XCom, and a task timeout of 60, for which Service Quotas
  gives no unit. SageMaker: `Total domains`
  10 in Staging and 500 in Sandbox against a default of 2; Studio spaces 50 and 6,000 (default 6);
  user profiles 50 and 6,000 (default 2); SageMaker Projects 500 in both. Neither account's request
  history names these codes; Sandbox's holds Stage 17's three open requests. A `Tooling` base creates
  one SageMaker AI domain per project (0.2), so it admits ten projects in Staging [inferred]. Staging
  admits 4 `ml.t3.medium` processing jobs (the default), the type `app-etl`'s `process` task names;
  `ml.m5.large` and `ml.m5.xlarge` read 0 (Sandbox 10, 8 and 8). Decision 6 is the user's.
- **[Claude] 7.3's record.** 7.3 was written 2026-10-17 by the cloud session that wrote the stage,
  from AWS's pages that `docs/REFERENCES.md` lists under "Data across accounts in SageMaker Unified
  Studio" (read 2026-10-17); no AWS call ran for it, Staging having no warehouse, and this session did
  not read the pages again.
- **[Claude] Amends the 2026-10-17 entry's "0.2 and 0.4 can run from the laptop".** 0.2 did, today.
  0.4's calls go from the laptop, but its run's tasks need `sandbox/egress`'s `[E]` endpoints (6i's
  prerequisites), so the run waits on a raised session; the step says so now, under the profile
  `awsds-infra-sandbox-1`, the one that exists.

## 2026-10-18 — what 4.4's run needs from other stages, read in the code

*Claude's hand, in a task the orchestrating session ran on the laptop (branch
`claude/stages-09-10-18-readings`), with the environment down. Repository reads and one `--dry-run`; no
AWS write, and neither change below was applied.*

- **[Claude] The application image's pull grant.** `app-etl`'s `process` task names its image as
  `{env.JOB_IMAGE_URI}`, the release's `awsds-prod-ecr-app-etl` by digest, and a processing job pulls it as
  the job's role through the service (6i). In `production/registry/`, that repository's pull principals
  are `local.app_consumer_account_arns`, built from `APP_REGISTRY_CONSUMERS`, `["sandbox"]` in
  `scripts/tfhygiene/backend.py`; the slice holds one aliased provider, `sandbox`, and
  `account_id_by_folder` one key, so a `staging` row fails the plan on the index until a `staging` alias
  and identity read join it. That is Stage 8 step 3.0's first half, which Stage 8's decision 23 places in
  its pass 4, after Stage 9.
- **[Claude] The code bucket on Staging's S3 gateway endpoint.** `staging/foundation/` calls `vpc` at
  `vpc-v0.3.1` with no `s3_endpoint_allowed_bucket_names`, so the endpoint carries the module's default
  list. Between `vpc-v0.3.1` and `vpc-v0.4.0` the module's one change in code is
  `mwaa-serverless-code-files-*-<region>-prod` in that list (`git diff`; the rest is comments and
  descriptions). 6i decision 7 measured a workflow with a `Code` object failing at environment preparation
  without it, and left Staging on `vpc-v0.3.1` until such a workflow runs there; Stage 10 step 1.2 makes the
  bump, and that stage's log of today leaves it to its pass 2. `app-etl` carries a `Code` object
  (`code/app-etl.zip`, for `summarize`), and 5.1's `demo-python-operator` imports `demo_tasks.run` from its
  archive.
- **[Claude] The sitting.** `./scripts/slices.py up --env staging --dry-run` at `28f340c` lists two `[E]`
  slices, `staging/egress` and `staging/probes`, whose header says not to run it as written; `make up`
  passes `ONLY=` to `--only` (Stage 8 step 4.4). PR #186, open on 2026-10-18, retires `staging/probes/`,
  after which `staging/egress` is the account's only `[E]` slice. The Prerequisites now say `make up
  ENV=staging ONLY=egress`, which holds either way, name the two changes above for 4.4, and 4.4 waits on
  both.
- **[Claude] Stale text corrected.** The Prerequisites and the risk "The `Workloads` document" said Stage 9
  pass 1's job statements were merged and not attached. They were attached at 19:54Z today, the battery's
  `ou` phase reading them after ([Stage 9's log](log-stage-09-deployment-targets.md)), and this stage's 0.3
  read the attached document.

## 2026-10-19 — passes 1 and 2.4 written and planned, the two bases' templates read, the applies refused to Claude

*Claude's hand, in this stage's session on the laptop ("Stage 18 — Staging deployment project"), on the
user's word of 2026-10-19: *"iniciar o Stage 18 passa a ser a prioridade. Mapeie tudo que é necessário
... Em seguida execute todas as etapas que conseguir fazer sem minha intervenção. Você está autorizado a
executar todos os comandos de apply e leitura do ambiente."* Every AWS call below is a read as the
infrastructure user (`InfrastructureAccess`), through `awsds-infra-data`, `awsds-infra-identity` and
`awsds-infra-staging`; the environment was down. Account ids are replaced by the account's name. Times
are UTC.*

- **[Claude] The state at the start.** Every `awsds-infra-*` profile held a live session. The domain
  `awsds-studio` (`dzd-d8yrvx1ko7im6o`) is `AVAILABLE` with one profile, `experimentation`; its managed
  roster holds `Tooling` (`4k186sfh08eqxc`) and `ToolingLite` (`6b5j1ajb2pzh3k`), both updated
  2026-09-23. From `awsds-infra-staging`, `datazone list-domains` is refused with an explicit deny in
  the service control policy `p-83t232f4`, the `Workloads` document: 0.3's reading repeated.
- **[Claude] Question i read from the templates, before anything is created.** `get-environment-blueprint`
  gives each blueprint's `provisioningProperties.cloudFormation.templateUrl`, an S3 access-point URL that
  refuses a plain fetch (`InvalidRequest`, SigV4 only); `s3api get-object` as `awsds-infra-data` read
  both into the session's scratch directory: `DataZone-Amazon-SageMaker-ToolingLiteDefault-prod-20260723`
  (159,043 bytes) and `DataZone-Amazon-SageMaker-ToolingDefault-prod-20260918` (245,988 bytes).
  - `ToolingLite`: one user parameter, `s3BucketLocation` (optional, editable), and 24 template
    parameters, `executionRoleArn` among them. Resources: `ProjectBucket` when no location is given
    (`amazon-sagemaker-<account>-<region>-<project>`, Retain), `ToolingSecurityGroup` (all egress to
    `0.0.0.0/0`) when a VPC is given and no security group is passed, up to sixteen Glue network
    connections, `AthenaWorkgroup`, `EventBridgeScheduleGroup`, and **`SageMakerSpacesDefaultDomain`,
    `AWS::SageMaker::Domain`, with no condition**, `VpcOnly` when a VPC is given, its default space
    settings' execution role the `executionRoleArn` parameter. No IAM role, no log group, no Lake
    Formation resource. Its outputs include `VpcExport`, `PrivateSubnetsExport`, `SecurityGroup` and
    `KmsKeyExport`, the names the CI/CD CLI reads a workflow's network and key from.
  - `Tooling`: 65 template parameters. `SageMakerSpacesDefaultDomain` carries the condition
    `sageMakerDomainRequired` = `isDefaultTooling` and `enableSpaces == "true"`, where `isDefaultTooling`
    = `enableCustomProjectProfiles == "true"` and `isDefault == "true"`, parameters the service sets and
    true in the two Sandbox stacks 0.2 read, which hold the domain. `ToolingUserRole` is created with
    `PermissionsBoundary` = `permissionsBoundaryArn` when given, AWS's
    `SageMakerStudioProjectUserRolePermissionsBoundary` otherwise, and the three managed policies 0.2
    read; `ToolingCloudWatchLogGroup`, `LakeFormationResourceToRegisterProjectsS3Location` (the project
    prefix under `s3BucketArn`, registered under the user role) and the security group are
    unconditional; `EventBridgeScheduleGroup` needs `enableScheduling`, the Athena workgroups their
    flags, the Bedrock roles `enableAmazonBedrockProjectServiceRoles`. The same four network and key
    outputs.
  - So both managed bases create a SageMaker AI domain, `ToolingLite` always and `Tooling` only with
    spaces on: a `Tooling` environment whose profile sets `enableSpaces` false calls no
    `sagemaker:CreateDomain`, and `DenyInteractiveSageMakerSurface` needs no carve-out for it. The live
    blueprint marks `enableSpaces` not editable (`isEditable` false), as it marks
    `maxIdleTimeoutInMinutes`, which `experimentation` overrides to 120 and whose projects deploy, so a
    profile's override of such a parameter reaches the deploy for one parameter; 3.2 reads it for this
    one. Decision 1's recommendation is revised to `Tooling` with `enableSpaces` false; the user decides.
- **[Claude] 1.1 written.** `awsds-org-scp-ou-workloads.json`'s `DenyDataZoneEntirely` gains
  `StringNotEquals aws:PrincipalAccount <ACCOUNT_ID_STAGING>`; `locals.tf` resolves the placeholder by
  the vended name `Staging Account` and `ACTIVE`, as `identity_account_id` is, and renders it sixth;
  `render.py` reads it from `organizations list-accounts` and refuses any count but one; `policies.tf`
  gains a precondition refusing a placeholder that survives the rendering; `POLICIES.md`'s row and the
  README carry the window. No `CreateDomain` split, decision 1's recommendation needing none.
  `render.py` as `awsds-infra-identity`: every placeholder substituted, the `Workloads` document 3,768
  bytes as written and 2,571 minified, margin 2,549.
- **[Claude] 1.2 written.** `probes.py`'s Staging `ListDomains` row reads `allow` for the window, the
  `prod` row keeps the deny, and a new Staging `CreateSpace` row (`blocked`, domain `d-0000000000000`)
  reads that the rest of the document still binds the account. An amendment to a per-OU document is the
  runbook's phase 4b, re-probed in the OU's own accounts with nothing parked on `Policy Test`, so 1.3's
  "the candidate on `Policy Test` first" does not apply.
- **[Claude] 1.3 planned, not applied.** `identity/org-policies/` as `awsds-infra-identity`,
  `-input=false`, about 03:26: `aws_organizations_policy.this["awsds-org-scp-ou-workloads"]` updated in
  place and nothing else, the content differing in the one Sid, the plan saved outside the repository.
  The apply was refused to Claude by the app's auto-mode classifier (*Protected-Scope IaC Apply*), the
  user's authorization in the chat notwithstanding, and so was `staging/studio/`'s below. Both are the
  user's to run from the saved plans, after which this stage owes the re-plan, `./aws/org-policies.py`,
  the battery's phase `ou`, the two `list-domains` probes and `EXC-20`.
- **[Claude] 2.4 written.** `staging/studio/` from `sandbox/sagemaker/`'s files on
  `sagemaker-prereqs-v0.6.0`, with `blueprint_names` a variable defaulting to `["Tooling"]` and
  `cost_center` `stage-18`; `layers.py` gains the rank `studio` at 46 and the `[P]` row; `backend.py`
  the `studio` emission (`account_folder`, `lake`, `domain`, `blueprints_enabled` from
  `SMUS_ASSOCIATED`, false today); conventions §6 and `NETWORK.md` §2.1 their rows. `terraform init`
  took `aws` 6.69.1 and `awscc` 1.106.0; the lock carries the three platforms; `make check` passes.
- **[Claude] 2.5's first half planned, not applied.** As `awsds-infra-staging`, about 03:28: 14 to add,
  nothing changed or destroyed: `awsds-staging-smus-provisioning` and `awsds-staging-smus-manage-access`
  with their managed-policy attachments, `awsds-staging-project-boundary`, the key
  `alias/awsds-staging-project`, `awsds-staging-smus-projects` with its five settings, and
  `/awsds/staging/studio` at 30 days. Refused to Claude as above.
- **[Claude] What the stage waits on now**, in order: the two applies; 2.1, the association, in Data
  Governance's DataZone console; decisions 1 to 3, 1 as revised; Stage 17 1.1, since 2.7's `governance/`
  apply carries Stage 17 pass 1's `MLflowApp` configuration and the two stages never share one; the
  `SMUS_ASSOCIATED` and `SMUS_DEPLOYMENT_MEMBERS` rows after the association, then 2.5's second apply
  and 2.6; then pass 3 from the laptop. 0.4's run needs `make hub-up` and `make up ENV=sandbox`; passes
  4 and 7 need `app-etl`'s first tag (a GitLab session, with `DEV_PROJECT_KEY_ARN` and
  `TEST_PROJECT_KEY_ARN` set) and `make hub-up` with `make up ENV=staging ONLY=egress`, with Stage 8
  3.0's first half and Stage 10 1.2's `vpc-v0.4.0` applied before 4.4.

## 2026-10-19 — the two applies, by the user's hand, and the readings after them

- **[user] Both applies, from the saved plans, in the app's terminal on the worktree.** The output was
  pasted into the chat; the ids it carries stay in the slices' states. `identity/org-policies/` as
  `awsds-infra-identity`: `aws_organizations_policy.this["awsds-org-scp-ou-workloads"]: Modifications
  complete after 1s`, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*, the outputs reading
  `awsds-org-scp-ou-workloads = 2571` and the four OU and six root attachments unchanged.
  `staging/studio/` as `awsds-infra-staging`: *"Apply complete! Resources: 14 added, 0 changed, 0
  destroyed."*, the key created in 25 s and the bucket's lifecycle configuration in 58 s, the outputs
  naming the two roles, the boundary, the key and the regional parameters (`AZs = usw2-az1,usw2-az2`,
  Staging's two private subnets and its VPC), the values 2.5's second apply sends.
- **[Claude] Read back, 03:51 to 03:53 UTC**, as the infrastructure user. `identity/org-policies/`
  re-plans `No changes` (03:51:24Z) and `./aws/org-policies.py` writes `all checks passed`.
  `staging/studio/` re-plans `No changes` (03:52:42Z); `awsds-staging-smus-provisioning` and
  `awsds-staging-smus-manage-access` were created at 03:47:52Z, the first trusted by
  `datazone.amazonaws.com` and `cloudformation.amazonaws.com` and carrying no boundary of its own; the
  key behind `alias/awsds-staging-project` is `Enabled`, customer-managed, created 03:48:02Z;
  `awsds-staging-smus-projects` is versioned with its four public-access blocks on; `/awsds/staging/studio`
  keeps 30 days; Staging's Lake Formation settings read as at 0.3: no admin, `CROSS_ACCOUNT_VERSION` 1.
- **[Claude] The carve-out, measured at 03:52:49Z.** `datazone list-domains` as `awsds-infra-staging`
  answers `{"items": []}`, the account's own domains; as `awsds-infra-prod` it is refused with *"an
  explicit deny in a service control policy"* naming `p-83t232f4`, the `Workloads` document; `sagemaker
  create-space` on a made-up domain as `awsds-infra-staging` is refused by the same wording, so the
  document's other statements still bind Staging; `list-environment-blueprint-configurations` on
  `awsds-studio` as `awsds-infra-staging` reads `UnauthorizedException`, DataZone's own refusal of an
  account not yet associated, the call 2.2 expects to succeed after 2.1. `EXC-20` records the window and
  `AWS_STATE.md` section C the objects `staging/studio/` holds.
- **[Claude] The battery's phase `ou`, 03:52:53 to 03:53:57Z** (`./aws/probes/scp-battery.py --phase ou`,
  report `scp-battery-20261019T005253.txt` under `aws/output/`): *"40 as expected, 0 unexpected, 7 not
  measured"*, one row more than Stage 9's 39 of 2026-10-18, the new `CreateSpace` row. Staging's
  `datazone:ListDomains` reads `ALLOWED, succeeded`, its `sagemaker:CreateSpace` `DENY-SCP p-83t232f4`,
  Production's `datazone:ListDomains` `DENY-SCP p-83t232f4`, and Sandbox's `ListDomains` still
  `ALLOWED`; the seven not measured are the ones Stage 9's log names, the processing-job rows whose
  quotas read 0 in Production. 1.3 is done; 1.1's `EXC-nn` is `EXC-20`.

## 2026-10-19 — the association read back, 2.3's rows, 2.5's second half planned, 2.6 written

- **[user] 2.1, the association.** The user associated `Staging Account` to `awsds-studio` in Data
  Governance's DataZone console, by the path the 6a log records, and wrote in chat *"Fiz a associação,
  pode continuar"*. RAM dates the act: the domain's share gained Staging as a principal at 04:03:13Z.
- **[Claude] 2.2, read back from 04:05 UTC** as the infrastructure user. `datazone
  list-environment-blueprint-configurations --domain-identifier dzd-d8yrvx1ko7im6o` as
  `awsds-infra-staging` exits 0 with `{"items": []}`, where it read `UnauthorizedException` at 03:52Z.
  `ram get-resource-shares --resource-owner OTHER-ACCOUNTS` there holds
  `DataZone-EXTENDED_ACCESS-dzd-d8yrvx1ko7im6o-ORG-ONLY`, `ACTIVE`, created 2026-08-21, and no
  invitation exists. Read from Data Governance, the share's principals are Staging (04:03:13Z) and
  Sandbox (2026-08-21). Its permission is `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`
  at version 10, the default and the only `ATTACHABLE` version, created 2026-06-04: the share carries
  the current version, so the release note's *"Existing RAM resource shares do not auto-update"* does
  not reach it. `./aws/studio.py` with the four infrastructure profiles writes `all checks passed`:
  `US-2` reads Staging seeing the shared domain and owning none, `US-6` Production's DataZone reads
  denied, and Staging holds no SageMaker AI domain. Run with every `awsds-*` profile it exits 1, the
  persona, deploy and Control Tower sessions not being signed in. `search-user-profiles --user-type
  DATAZONE_IAM_USER` as `awsds-infra-data` lists an `ACTIVATED` IAM user profile for Staging's
  InfrastructureAccess role, its ARN carrying the SSO path: the principal decision 3 names.
- **[Claude] 2.3's rows.** `SMUS_ASSOCIATED` gained `staging`, then `SMUS_DEPLOYMENT_MEMBERS`. After
  each row, every declared slice's generated tfvars, laptop and pipeline, and refusal 8's answers for
  every profile were compared with the previous set, 38 slices: the first row changes
  `staging/studio/`'s `blueprints_enabled` from false to true and nothing else, the second adds
  `staging` to `governance/`'s `members` map and nothing else, and refusal 8 is unchanged. Re-planned
  at 04:15Z: `sandbox/foundation/`, `production/tooling/` (the SAML var-file) and `staging/foundation/`
  (the alerts var-file) `No changes`; `governance/` 0 to add, 1 to change, 0 to destroy, the
  `MLflowApp` configuration of `experimentation` alone (Stage 17 pass 1's, `deployment_order` 11), as
  on 2026-10-18.
- **[Claude] 2.5's second half planned at 04:13:56Z** as `awsds-infra-staging`, saved to
  `$HOME/tmp/stage18-studio-2.tfplan`: 2 to add, 1 to change, 0 to destroy. The `Tooling`
  configuration takes region `us-west-2`, the boundary `awsds-staging-project-boundary`, the two
  roles, and the regional parameters `AZs` `usw2-az1,usw2-az2`, the project key, `S3Location`
  `s3://awsds-staging-smus-projects`, Staging's two private subnets and its VPC. Its
  `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant goes to `CONTRIBUTOR` projects of the root domain unit,
  child units excluded. The project key's policy gains the domain execution role in two statements,
  and `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`, which the module
  writes once a domain id exists. The apply is the user's; it takes decision 1's base, `Tooling`.
- **[Claude] 2.6 written behind a switch.** `governance/`'s `locals.tf` holds
  `deployment_profile_enabled = false`, the `deployment` row (Staging, `["Tooling"]`, a null `group`)
  and each profile's own overrides; `profiles.tf` reads each profile's blueprint list under a
  precondition holding Tooling first and category 1 only; `providers.tf` gains the `staging` alias,
  `data.tf` Staging's identity and its InfrastructureAccess role by name; `grants.tf` grants a profile
  with no group to that role's ARN as DataZone's user identifier. Planned at 04:21:26Z with the switch
  off: 0 to add, 1 to change, `MLflowApp` alone, as before. Set true in the working copy and back
  afterwards, at 04:21:59Z: 2 to add, 1 to change. The profile holds `Tooling` alone, `ON_CREATE`,
  order 0, in Staging's account, with `experimentation`'s six Tooling overrides and `enableSpaces`
  `"false"` locked (the template's AllowedValues are `"true"` and `"false"`, default `"true"`); the
  grant is `CREATE_PROJECT_FROM_PROJECT_PROFILE` on the root unit to Staging's InfrastructureAccess
  role; `experimentation`'s grant is unchanged. `./aws/studio.py`'s `US-4` passed with any extra
  profile, reporting "one, as contracted"; it now fails on a profile outside the contract and reads
  `deployment` as Stage 18's window.

## 2026-10-19 — 2.5's second half, by the user's hand, and its read-back

- **[user] 2.5's second apply, from the saved plan**, in the app's terminal on the worktree, as
  `awsds-infra-staging`. The output, ids left out: the project key *"Modifications complete after 6s"*,
  the `Tooling` configuration *"Creation complete after 17s"*, its grant *"Creation complete after
  6s"*, and *"Apply complete! Resources: 2 added, 1 changed, 0 destroyed."* The outputs name the two
  roles, the boundary, the key and the regional parameters as the first half's did. The session had
  said the apply takes decision 1's base, `Tooling`, and that another base had to be named before
  it; none was, so the base is decided on the recommendation of 2026-10-19.
- **[Claude] Read back, 04:32 to 04:36 UTC**, as the infrastructure user. `staging/studio/` re-plans
  `No changes` (04:32:40Z). `get-environment-blueprint-configuration` for `Tooling` from Staging: created
  04:31:00Z, `enabledRegions` `us-west-2`, the provisioning and manage-access roles,
  `environmentRolePermissionBoundary` `awsds-staging-project-boundary`, and the regional parameters
  `AZs` `usw2-az1,usw2-az2`, the project key, `S3Location` `s3://awsds-staging-smus-projects`,
  Staging's two private subnets and its VPC; `list-environment-blueprint-configurations` holds that one
  configuration and no other. `list-policy-grants` on it: one `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant
  to `CONTRIBUTOR` projects of the root domain unit, child units excluded, created 04:31:00Z. The key
  behind `alias/awsds-staging-project` holds nine statements, the domain execution role in
  `AllowKmsKeyUsageForSageMakerDomain` and `AllowSageMakerDomainKmsGrantPermissions`, and
  `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles` among them. Staging
  holds no SageMaker AI domain, and its live CloudFormation stacks are Control Tower's five baseline
  stack sets of 2026-08-09. `./aws/studio.py` on the four infrastructure profiles: `all checks
  passed`, `US-4` reading `experimentation` alone.
- **[Claude] The boundary is readable, by one of the two reads.** DataZone's own
  `get-environment-blueprint-configuration` returns `environmentRolePermissionBoundary` in Staging, and
  in Sandbox for the `Tooling` configuration of 2026-08-22, where `list-environment-blueprint-configurations`
  returns it too. Cloud Control's `get-resource` for `AWS::DataZone::EnvironmentBlueprintConfiguration`,
  the read `awscc` makes, omits it. `lessons.md`'s entry of 2026-08-22, *"no read returns it"*, carries
  this reading now; a plan still cannot show the field's drift.

## 2026-10-19 — 4.4's two prerequisites written and planned

- **[Claude] The application image's pull grant for Staging** (Stage 8 step 3.0's first half, which
  this stage's Prerequisites run in its window). `APP_REGISTRY_CONSUMERS` gains `staging`;
  `production/registry/` gains the `staging` alias, its profile read from `app_consumers`, the identity
  read, and `staging` in `account_id_by_folder`. Planned at 04:53:07Z as `awsds-infra-prod`, saved to
  `$HOME/tmp/stage18-registry.tfplan`: 0 to add, 1 to change, 0 to destroy, the `app-etl`
  repository's pull policy gaining one principal, read against `awsds-infra-staging`'s caller identity
  as Staging's account root. The ceiling half of 3.0 is not written; 4.4 does not need it.
- **[Claude] `staging/foundation/` on `vpc-v0.4.0`** (Stage 10 step 1.2's bump). The module's one
  functional change between the tags is the S3 gateway default list gaining
  `mwaa-serverless-code-files-*-<region>-prod`; the rest is description text, and the slice passes
  no list of its own. Planned at 04:53:32Z as `awsds-infra-staging` with the alerts var-file, saved to
  `$HOME/tmp/stage18-staging-foundation.tfplan`: 0 to add, 1 to change, 0 to destroy, the S3
  gateway endpoint's policy gaining that family's bucket and object ARNs alone.
- The two applies are the user's.

## 2026-10-19 — 4.4's two prerequisites, by the user's hand, and the readings after them

- **[user] Both applies, from the saved plans**, in the app's terminal on the worktree.
  `production/registry/` as `awsds-infra-prod`: the `app-etl` repository policy *"Modifications
  complete after 1s"*, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*
  `staging/foundation/` as `awsds-infra-staging`: the S3 gateway endpoint *"Modifications complete
  after 7s"*, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*
- **[Claude] Read back, 05:11 to 05:16 UTC**, as the infrastructure user. Both slices re-plan
  `No changes` (05:11:51Z and 05:12:11Z). `awsds-prod-ecr-app-etl`'s policy holds one statement,
  `AllowConsumerAccountsToPull`, for Staging's and Sandbox's account roots, with
  `ecr:BatchCheckLayerAvailability`, `BatchGetImage`, `GetDownloadUrlForLayer` and `DescribeImages`.
  Staging's S3 gateway endpoint holds `AllowWithinOrganization` and `AllowAwsOwnedServiceBuckets`, the
  second with 16 resources, the `mwaa-serverless-code-files-*-us-west-2-prod` bucket and object ARNs
  among them. `./aws/egress.py` and `./aws/networking.py` on the four infrastructure profiles: all
  checks passed.
- **[Claude] `EG-4` learns the MWAA Serverless family.** Its comment holds one pattern per family of
  the gateway's AWS-owned list, so that a deleted entry cannot stay `pass` (Lesson 13), and the
  `mwaa-serverless-code-files` family of `vpc-v0.4.0` had none: Sandbox's row, which has carried the
  family since 2026-10-11, never showed it. With the pattern, `EG-4` reads `mwaa-code` in Sandbox and
  Staging and not in Production's three VPCs, which are on `vpc-v0.3.1`; the family's absence stays
  a reading, never a failure.

## 2026-10-19 — Stage 17's applies read back, 2.7 planned

- **[user] Stage 17 1.3's two applies**, in that stage's session ([its log](log-stage-17-sandbox-machine-learning.md) is
  its own record); the user wrote here *"acredito que os applies do Stage 17 rodaram"*.
- **[Claude] Read back at 05:23:40Z**, as the infrastructure user, before anything was planned here:
  `experimentation`, last updated 05:12:33Z, holds twelve environment configurations, `MLflowApp`
  `ON_DEMAND` at order 11 the last; Sandbox holds twelve blueprint configurations, `MLflowApp`'s
  created 05:11:58Z. The domain holds that one profile. `governance/`'s state object was last written
  05:12:40Z, and no lock object stood beside it at 05:24:05Z. Stage 17's session reported its
  `governance/` re-plan `No changes` at 05:13:39 to 05:14:00Z.
- **[Claude] 2.7 planned at 05:24:48Z** as `awsds-infra-data`, `deployment_profile_enabled` set
  true, saved to `$HOME/tmp/stage18-governance-27.tfplan`: 2 to add, 0 to change, 0 to destroy, the
  `deployment` profile and its `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant, both identical to the
  working-copy plan of 04:21:59Z; `experimentation` untouched. The other sessions were told before the
  apply, Stage 17's with the hazard that its checkout, cut from `main` without PR #196, would plan
  the profile's destruction after the apply; it answered that it plans `governance/` no more until
  PR #196 is in its branch. The apply is the user's.

## 2026-10-19 — 2.7's first apply: the profile created, the grant refused, the grant re-planned

- **[user] 2.7's apply, from the saved plan**, in the app's terminal on the worktree, as
  `awsds-infra-data`: *"awscc_datazone_project_profile.this["deployment"]: Creation complete after
  7s"*, then the grant refused, *"Group profile already exists for the given User profile (Service:
  DataZone, Status Code: 400 ...) ErrorCode: InvalidRequest"*, at `grants.tf` line 28.
- **[Claude] What the apply left**, read at 05:43 to 05:50 UTC: `governance/`'s state holds the
  `deployment` profile and no grant for it; the root domain unit holds one
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant, `experimentation`'s, so nothing was half-created. The
  profile is `ENABLED`, created 05:47:08Z, `Tooling` `ON_CREATE` at order 0 in Staging's account,
  with `experimentation`'s six Tooling overrides and `enableSpaces` `false`, locked.
- **[Claude] Why the grant was refused.** The role's ARN names two DataZone objects.
  `get-user-profile` with it returns an `IAM` user profile whose `principalId` and `sessionName`
  carry one session, the infrastructure user's, and whose `groupProfileId` points at a group profile;
  `get-group-profile` with the same ARN returns that group profile, `ASSIGNED`, with
  `rolePrincipalArn` the role and no group name: an `IAM_ROLE_SESSION_GROUP`, which
  `search-group-profiles` lists beside the two other accounts' InfrastructureAccess roles. A grant to
  the ARN as a user lands on the session's profile, which a group profile already covers. The service
  model admits the ARN as a user identifier and documents nothing of the group.
- **[Claude] The grant re-written to the group.** `grants.tf` names a group in every grant again:
  the IdC group for `experimentation`, the role's session group for `deployment`, its id read by
  `awscc_datazone_group_profile`, since Cloud Control's `GetResource` for
  `AWS::DataZone::GroupProfile` resolves `<domain>|<role ARN>` to the profile (read before the
  edit). With no lock on the state at 05:51:29Z, re-planned at 05:52:00Z as `awsds-infra-data`, saved
  to `$HOME/tmp/stage18-governance-27b.tfplan`: 1 to add, 0 to change, 0 to destroy, the grant on the
  root unit for the `deployment` profile, its `group_identifier` the session group's id;
  `experimentation`'s grant untouched. The apply is the user's.

## 2026-10-19 — 2.7's grant, by the user's hand, and the read-back

- **[user] The grant's apply, from the saved plan**, as `awsds-infra-data`:
  *"awscc_datazone_policy_grant.create_project_from_profile["deployment"]: Creation complete after
  7s"*, *"Apply complete! Resources: 1 added, 0 changed, 0 destroyed."* The outputs name the creators,
  `"deployment" = "InfrastructureAccess (staging)"` and `"experimentation" =
  "sso-group-data-scientists"`. Then the user merged PR #196 (06:00:44Z) and wrote *"fiz o merge do
  #196"*.
- **[Claude] Read back at 06:01 UTC.** `governance/` re-plans `No changes` (06:01:20Z). The root domain
  unit holds two `CREATE_PROJECT_FROM_PROJECT_PROFILE` grants, child units excluded:
  `sso-group-data-scientists` for `experimentation` (2026-08-22) and Staging's InfrastructureAccess
  session group for `deployment` (05:58:00Z). `./aws/studio.py` on the four infrastructure profiles:
  all checks passed, `US-4` reading *"deployment, experimentation - experimentation as contracted,
  deployment in Stage 18's window"*. Decisions 1 to 3 are taken by the applies; 2.7 is done.
