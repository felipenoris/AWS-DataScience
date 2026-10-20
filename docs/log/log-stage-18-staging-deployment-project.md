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

## 2026-10-19 — 3.1, the project

- **[Claude] `deploy-staging` created at 06:05:27Z** as `awsds-infra-staging`, on the user's
  authorization in this session for the stage's writes: `datazone create-project --name
  deploy-staging` from the `deployment` profile exited 0. The app's classifier let this call through,
  where it had refused every `terraform apply` of the stage. The project was created at 06:05:28Z by
  the IAM user profile of the infrastructure user's session in Staging's InfrastructureAccess, its
  environment deployment `PENDING_DEPLOYMENT`. The CLI's newer options, `--project-execution-role`,
  `--resource-tags`, `--membership-assignments` and `--project-category`, were left out, so the
  project is AWS's default shape. The other sessions were told before the call.
- **[Claude] `list-project-memberships`**: one member, Staging's InfrastructureAccess session group,
  `PROJECT_OWNER`. The group is the member, not the session that created the project.
- **[Claude] The environment started deploying**: `Tooling` `CREATING` at 06:05:49Z, the stack
  `DataZone-Env-…` `CREATE_IN_PROGRESS` in Staging since 06:05:43Z.

## 2026-10-19 — 3.2 and 3.3, the environment and what it created

- **[Claude] 3.2, read at 06:05 to 06:08 UTC** as `awsds-infra-staging`: the stack
  `DataZone-Env-…` began at 06:05:43Z and reached `CREATE_COMPLETE` at 06:06:38Z; the project read
  `SUCCESSFUL`, `Tooling` `ACTIVE`, at 06:07:27Z. The stack's parameters: `enableSpaces` `false`,
  `isDefault` and `enableCustomProjectProfiles` `true`, `permissionsBoundaryArn` the stage's boundary,
  `enableScheduling`, `enableAthena`, `enableAthenaSparkWorkgroup`, `enableGlueNetworkConnection`,
  `enableNetworkIsolation`, `enableRolesWithoutBoundary` and the Bedrock switch `true`,
  `logGroupRetention` 731. The profile's locked `enableSpaces` reached the deploy.
- **[Claude] 3.3, the thirteen resources**: two Athena workgroups, the Bedrock Lambda and service roles,
  `CDKMetadata`, the schedule group, two `GlueNetworkConnection`s, the Lake Formation registration of the
  project prefix, the log group, `ToolingSecurityGroup` with its ingress, and `ToolingUserRole`. 0.2's
  Sandbox list less `SageMakerSpacesDefaultDomain`. The outputs carry `VpcExport`,
  `PrivateSubnetsExport`, `SecurityGroup` and `KmsKeyExport`, the names the CI/CD CLI reads, the key
  `staging/studio/`'s project key.
  - The roles, all three under `awsds-staging-project-boundary`: `datazone_usr_role_<project>_<env>`,
    trusted by `datazone.amazonaws.com` and `auth.datazone.amazonaws.com`, a list of fourteen service
    principals (`airflow-serverless`, `sagemaker`, `glue`, `lakeformation` and `bedrock` among them),
    the two Redshift principals and the provisioning role, with `SageMakerStudioProjectUserRolePolicy`,
    `SageMakerStudioProjectRoleMachineLearningPolicy` and `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy`;
    `AmazonBedrockServiceRole-…`, trusted by `bedrock.amazonaws.com`, four Bedrock policies;
    `AmazonBedrockLambdaExecutionRole-…`, trusted by `lambda.amazonaws.com`, three.
  - The security group `datazone-<project>-dev`: all traffic in from itself, all traffic out to
    `0.0.0.0/0`, in a VPC with no route out but the endpoints and the hub.
  - Two Glue network connections, one per private subnet; the Athena workgroups
    `sagemaker-studio-spark-workgroup-<project>` and `workgroup-<project>-<env>`, the second writing to
    the project's `dev/sys/athena/`, both enforcing their configuration; the log group
    `datazone-<project>-dev` at 731 days under the project key.
  - Lake Formation: the project's `dev` prefix registered under the project role, hybrid access off.
    The admin list, empty until then, holds `awsds-staging-smus-provisioning` and
    `awsds-staging-smus-manage-access`, set by the provisioning role's three `PutDataLakeSettings` at
    06:05:34Z (open question 24's Sandbox pattern); `CROSS_ACCOUNT_VERSION` 1.
  - DataZone: nine connections (`default.s3_shared`, `project.s3_default_folder`, `project.iam`,
    `project.athena`, `project.default_lakehouse`, `project.spark.compatibility`,
    `project.spark.fineGrained`, `serverless.spark`, `default.workflow_serverless`), and no data source,
    where each Sandbox project holds `EXC-11`'s failing one.
  - RAM: Staging owns no share; it receives the domain's alone. The projects bucket holds five objects
    under the project's prefix, written 06:06:48 to 06:06:50Z: the `dev/` and `shared/` markers and
    `shared/`'s `.libs.json`, `README.md` and `getting_started.ipynb`.
- **[Claude] CloudTrail in Staging from 06:04Z**, four pages: the DataZone service's `AssumeRole`
  calls (25), the provisioning role's CloudFormation, EC2, Glue, Logs, Lake Formation, Scheduler, Athena,
  KMS and S3 calls, and InfrastructureAccess's `datazone:` calls, the only principal calling DataZone in
  Staging. Every refusal read *"no identity-based policy allows"*: the provisioning role's
  `athena:GetWorkGroup` and `ListTagsForResource`, `logs:DescribeIndexPolicies` and
  `DescribeResourcePolicies`, `ec2:DescribeSecurityGroupRules`, `servicequotas:GetServiceQuota` and a
  first `ec2:CreateSecurityGroup` (decoded: `allowed` false, no explicit deny), whose retry created the
  group; the project role's `s3:CreateAccessGrantsLocation`, with no Access Grants instance in the
  account. None came from the SCP or the boundary.
- **[Claude] The instruments**: `./aws/studio.py` all checks passed, `US-6` with no SageMaker AI domain
  in Staging; `./aws/datalake.py` all checks passed, its `DL-13` reading the lake's accounts alone, so
  Staging's two seats are this log's reading and 8.6's, by hand.

## 2026-10-19 — 0.4, question vii, the non-member's run

- **[Claude] 0.4, through a subagent of this session**, after `make up ENV=sandbox ONLY=egress AUTO=1`
  raised Sandbox's endpoints. As `awsds-infra-sandbox-1`, InfrastructureAccess, a non-member of
  `test-experimentation`: `list-workflows` and `get-workflow` found
  `houseprice_etl_test_experimentation_houseprice_etl`, `READY`, `manual_only`, created
  2026-10-16T02:40:45Z, its execution role the `test` project's role, its key the project key, one
  `GlueJobOperator` task, two earlier CLI runs `SUCCESS`. One `start-workflow-run` at 18:32:39 to
  18:32:41Z, exit 0, `STARTING`, with `SUBNET_AZ1` and `SUBNET_AZ2` as overrides, since the YAML reads
  `{{ params.SUBNET_AZ1 }}` and `{{ params.SUBNET_AZ2 }}` with no default and both CLI runs had passed
  them.
- **[Claude] The run**: `QUEUED` from 18:33:00Z, `RUNNING` at 18:35:08Z, `SUCCESS` read at 18:36:45Z;
  the service's own times `StartedOn` 18:32:45Z, `CompletedOn` 18:35:01Z, `Duration` 136, no error.
  The polled state lagged the work by about two minutes. The task ran 18:33:28 to 18:35:00Z, attempt
  1, its Glue job run `SUCCEEDED` in 64 s, 128 DPU-seconds, on a worker in Sandbox's private range;
  the task's `UpdateJob` changed the Glue job's `LastModifiedOn` alone.
- **[Claude] CloudTrail, 18:31:39 to 18:42Z**: `StartWorkflowRun` by InfrastructureAccess with no
  error, to the public endpoint; in the same second, invoked by `airflow-serverless.amazonaws.com`
  under the starter's session, KMS `GenerateDataKey` and `Decrypt` on the project key with the
  workflow's ARN as encryption context, and one `Decrypt` for each later `get-workflow-run`. No
  DataZone call on the start path. The service assumed its roles seven times. The only errors were
  benign: the Glue session's two `DeleteNetworkInterface` *"currently in use"*, both deletes passing
  at 18:37:38Z, and the MWAA Serverless service role's ten `AttachNetworkInterface` retries on the
  worker's ENI. **Question vii: yes**, the service authorizes by IAM alone, with the starter's own
  KMS grant on the workflow's key; Stage 10's `chain-exec` takes both actions, and its chain passes the
  workflow's stage variables.

## 2026-10-19 — pass 4 begins: the environment raised, app-etl's release, 4.1's branch

- **[user] The sitting**: `make hub-up` and `make gitlab-up`, the tunnel up (*"Ambiente já está no
  ar"*, *"vpn habilitada"*), and the request *"Peço planejar a executar o maior número possível de
  etapas do stage 18 que dependem desse ambiente no ar. Pode disparar quantas tarefas em paralelo
  forem necessárias. Você está autorizado a utilizar a sessão no chrome, realizar todos os applies
  necessários."*
- **[Claude] Both egress slices raised**, the other sessions told first: `make up ENV=sandbox
  ONLY=egress AUTO=1`, Sandbox's `sagemaker.api`, `glue` and `logs` endpoints `available`; `make up
  ENV=staging ONLY=egress AUTO=1`, *"20 added, 0 changed, 0 destroyed"*, eleven interface endpoints
  `available` (`athena`, `studio`, `ecr.api`, `ecr.dkr`, `glue`, `kms`, `lakeformation`, `logs`,
  `sagemaker.api`, `sagemaker.runtime`, `sts`).
- **[Claude] The quota 4.4 meets**: Staging's `ml.t3.medium for processing job usage` is 4 and its
  `ml.m5.large` 0; `app-etl`'s `process` task runs on `ml.t3.medium`.
- **[Claude] `app-etl`'s release**, the Prerequisites' first tag, recorded in full in [Stage 8's
  log](log-stage-08-cicd-pipelines.md): the template reached GitLab's `main` (MR !2, the user's
  merge), its eleven CI/CD variables were set through the user's Chrome session, the user tagged
  `v0.2.0`, and pipeline #51's `test-deploy` failed three times, the last after a successful deploy
  and run in the `test` project; the fix is MR !3, for `v0.2.1`.
- **[Claude] 4.1**: the branch `stage-18-staging` (`d8550e0`) on `awsds/app-etl`, the manifest's
  `staging` stage added to `main`'s, never to be merged.

## 2026-10-19 — 4.2 and 4.4: the deploy into `deploy-staging`, the first run

- **[Claude] `v0.2.1`'s release**, recorded in full in [Stage 8's log](log-stage-08-cicd-pipelines.md):
  pipeline #55's `test-deploy` passed as job 223 and `store-bundle` wrote
  `s3://awsds-prod-releases/app-etl/v0.2.1/app-etl.zip`, SHA256
  `7fb374d15c23953cb6ad6d9f5473f97d2c83ff2db167703a5a830d96add95fff`, the image
  `awsds-prod-ecr-app-etl@sha256:247ec6b661ceb03d2927e1ce5a3c07d9287280a639abed18ce8daf898ed4ce0c`; the
  `release` job failed on the notes' backticks, and MR !4 is the fix.
- **[Claude] 4.2, first form, 20:04:57 to 20:06:20Z**, as `awsds-infra-staging`: `deploy --manifest
  manifest.yaml --targets staging --bundle-archive-path <the bundle> --skip-validation --no-events` from
  a checkout of `stage-18-staging`, exit 1, *"No operator code found in S3 for: app-etl (code:
  code/app-etl.zip)"*. The CLI 1.0.9 printed *"Deploying '<item>' from local filesystem"* for each of the
  five storage items and wrote six files of the checkout and none of the bundle: a `content.storage` item
  naming no `connectionName` is read from the manifest's folder whenever a manifest is given
  (`smus_cicd/commands/deploy.py`, read 2026-10-19), and the checkout holds no `code/app-etl.zip`, which
  the pipeline builds.
- **[Claude] 4.2, second form, 20:07:34 to 20:09:33Z**: the bundle's SHA256 checked, the archive
  extracted into an empty folder with the branch's manifest beside it, and the same command run there
  without `--bundle-archive-path`: exit 0, *"Total files deployed: 7"*, the workflow created. The bundle
  holds the seven content files and no manifest. The CLI found the network and key through the `Tooling`
  environment, *"No managed Tooling.GA/Tooling.Lightning blueprint found; will try the IAM connection
  fallback"*, then *"Resolved Tooling config for project 'deploy-staging'"*, naming the project's two
  subnets, its security group and its key.
- **[Claude] What it wrote**, read 20:09 to 20:10Z: seven objects under the project's `shared/app-etl/`
  (`code/app-etl.zip`, `glue/transform.py`, `inbox/trades.csv`, the three `src/app_etl/` files and
  `workflows/app-etl.yaml`, resolved, 4,686 bytes against the bundle's 4,198), the first form's six
  overwritten; `app_etl_deploy_staging_app_etl` `READY`, `manual_only`, no schedule, one version
  `2f1e8e79d4e438da2eefec9ecc496ba3`; its execution role the project role
  `datazone_usr_role_d1veybt5oak4uo_bujd259b8g9zps` (D41 item 4); the project's two subnets and
  security group; `CUSTOMER_MANAGED_KEY`, the project key; the log group
  `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-d1veybt5oak4uo/app_etl_deploy_staging_app_etl`, no retention,
  under KMS; the code object under `shared/operatorFiles/`; the tags `AmazonDataZoneProject`,
  `AmazonDataZoneDomain`, `Target=deploy-staging`, `CreatedBy=SMUS-CICD`, `STAGE=STAGING` and
  `Pipeline=app-etl`. No Glue job exists: the operator creates it at the run (D41 item 9). **Question
  v's second half: yes.**
- **[Claude] CloudTrail, 20:07:30 to 20:09:34Z**, read again at 20:28Z, the input of 4.3: 174 calls by
  InfrastructureAccess. `datazone:` 150, all reads: `GetConnection` 72, `ListConnections` 18,
  `ListProjects` 11, `ListEnvironments` 10, `GetProject` 8, `GetUserProfile` 7,
  `ListProjectMemberships` 7, `GetGroupProfile` 7 refused, `GetDomain` 3, `GetEnvironment` 3,
  `ListDomains` 3, `ListEnvironmentBlueprints` 1. `airflow-serverless:CreateWorkflow`, `GetWorkflow`
  and `TagResource`; `logs:CreateLogGroup`; `sts:GetCallerIdentity`; `cloudformation:DescribeStacks` 7,
  each *"Stack with id cicd-test-domain-stack does not exist"*. Twelve KMS calls on the project key,
  each made by a service under the caller's session: MWAA Serverless's `CreateGrant` 2 (the grantee
  `airflow-serverless.us-west-2.amazonaws.com`), `GenerateDataKey` 3 and `Decrypt` 1 with the
  workflow's ARN as encryption context; S3's `GenerateDataKey` 1 and `Decrypt` 4; Logs' `DescribeKey` 1.
  DataZone assumed roles eight times, and the project role's session called `athena:GetWorkGroup` eight
  times. The S3 writes are data events, which `lookup-events` does not return. The list read at 20:10Z
  held 13 names and 18 calls: CloudTrail delivered the rest later (Lesson 62).
- **[Claude] 4.4, the first run**, the Stage 17 session told first: `run --workflow app-etl --targets
  staging --manifest manifest.yaml` from the extracted bundle's folder, 20:16:22Z, exit 0, *"Run ID:
  7MMhwSySe5SOWd1"*, `STARTING`, the stage's five variables passed as `OverrideParameters`. Its calls:
  `GetDomain`, `ListProjects`, `ListConnections`, `ListWorkflows`, `ListTagsForResource` and
  `StartWorkflowRun`, the last from the laptop through no VPC endpoint. **Question ix: no**, `run`
  started that one workflow run and nothing else.
- **[Claude] The run**: `QUEUED` from 20:17:01Z, `FAILED` read at 20:18:35Z; the service's `StartedOn`
  20:16:32Z, `CompletedOn` 20:17:15Z, `Duration` 43, *"Workflow execution failed, please check the task
  execution logs for more details"*. `transform` `FAILED`, attempt 1, 20:17:08 to 20:17:14Z; `process`,
  `summarize` and `write_result` `UPSTREAM_FAILED`. The task's log reads *"Execution environment is
  ready"* at 20:17:10Z, past the preparation `vpc-v0.4.0`'s endpoint policy admits (6i decision 7), then
  *"An error occurred (AccessDeniedException) when calling the GetJob operation: User:
  arn:aws:sts::<acct>:assumed-role/datazone_usr_role_d1veybt5oak4uo_bujd259b8g9zps/AmazonMWAAServerless
  is not authorized to perform: glue:GetJob on resource:
  arn:aws:glue:us-west-2:<acct>:job/app-etl-d1veybt5oak4uo because no identity-based policy allows the
  glue:GetJob action"*.
- **[Claude] Where the worker ran**, CloudTrail 20:16:20 to 20:19:30Z:
  `AWSServiceRoleForAmazonMWAAServerless` created its network interface in
  `awsds-staging-private-usw2-az1` with the project's security group, and the project role's session
  `AmazonMWAAServerless` called from an address in that subnet: `kms:Decrypt` through Staging's `kms`
  endpoint, `glue:GetJob` through `glue`, `logs:CreateLogStream` through `logs`.
  `airflow-serverless.amazonaws.com` assumed roles seven times and called `kms:Decrypt` three times and
  `GenerateDataKey` twice; ECS's six `AttachNetworkInterface`, five refused *"already has an interface
  attached"*, are the retries Sandbox's runs show.
- **[Claude] The cause**, read 20:21Z: the project role carries the blueprint's three AWS managed
  policies and the boundary `awsds-staging-project-boundary`, and nothing else. Sandbox's two project
  roles also carry `awsds-sandbox-workflows` (`sandbox/workflows/`), whose `GetAGlueJobNoProjectHolds`
  answers this refusal ([serverless-workflows.md](../plan/runbooks/serverless-workflows.md) §G, measured
  2026-10-16). No step of this stage had given the deployment project's role that grant.
- **[Claude] The grant written**: `staging/studio/workflows.tf`, `sandbox/workflows/`'s three
  statements as `awsds-staging-workflows`, attached to the role `project_roles` names, with a
  precondition on the slice's own boundary ARN; 8.1 empties the list before the project is deleted.
  Planned 20:23:37Z, *"Plan: 2 to add, 0 to change, 0 to destroy."*, the policy and the attachment, the
  plan saved for the user's apply.
- **[Claude] Re-planned** at 20:42:12Z, after Stage 17's `governance/` apply had moved a state this
  slice reads: unchanged, 2 to add, the saved plan replaced.
- **[user] Applied `staging/studio/`** as `awsds-infra-staging`, from that plan: *"aws_iam_policy.workflows:
  Creation complete after 1s [id=arn:aws:iam::<acct>:policy/awsds-staging-workflows]"*,
  *"aws_iam_role_policy_attachment.project["datazone_usr_role_d1veybt5oak4uo_bujd259b8g9zps"]: Creation
  complete after 0s"*, *"Apply complete! Resources: 2 added, 0 changed, 0 destroyed."*
- **[Claude] Read back**: the re-plan reads `No changes` (20:47:40Z); `awsds-staging-workflows` was
  created at 20:46:41Z, version `v1`, its Sids `DescribeAProcessingJobNoProjectHolds`,
  `TagAProcessingJobWithTheCallersProject` and `GetAGlueJobNoProjectHolds`, and it is attached to the
  project role beside the blueprint's three policies.
- **[Claude] 4.4, the second run**, the same command from the same folder, 20:47:53Z, exit 0, *"Run ID:
  JSSr2Br9Zsf2b26"*. `SUCCESS` read at 21:02:31Z; the service's `StartedOn` 20:48:04Z, `CompletedOn`
  21:01:32Z, `Duration` 808, no error. Each task attempt 1, `SUCCESS`:
  - `transform`, 20:48:41 to 20:51:25Z, 164 s: *"Creating job: app-etl-d1veybt5oak4uo"*, the worker's
    `glue:GetJob` answered `EntityNotFoundException` at 20:48:46Z, then `CreateJob` and `StartJobRun`.
    The job carries the project role, the two Glue network connections, Glue 6.0, two `G.1X` workers, no
    security configuration and one tag, `AmazonDataZoneProject`; its run `jr_5d56c4cd…` `SUCCEEDED`,
    20:48:46 to 20:51:23Z, 131 s, 262 DPU-seconds.
  - `process`, 20:52:01 to 21:00:09Z, 488 s: the worker's `DescribeProcessingJob` answered
    `ValidationException` (*"Could not find requested job with name: app-etl-20261019T205205"*), then
    `CreateProcessingJob`. The job `app-etl-20261019T205205` `Completed`, created 20:52:06Z, processing
    ended 20:57:53Z: `ml.t3.medium`, within Staging's quota of 4; the volume key set; network isolation
    and inter-container encryption on; the project's two subnets and security group; the project role;
    the image by digest from `awsds-prod-ecr-app-etl`; the tags `AmazonDataZoneProject`,
    `AmazonDataZoneDomain` and `AmazonDataZoneScopeName=dev`, the last two not in the definition. No
    statement of the `Workloads` document refused it, Staging's first SageMaker job.
  - `summarize`, 21:00:47 to 21:00:53Z, 6 s, and `write_result`, 21:01:25 to 21:01:32Z, 7 s.
- **[Claude] The outputs** under the project's `shared/app-etl/`: `work/glue/trades.csv`, 436 bytes,
  20:51:12Z; `work/job/trades.parquet`, 2,126 bytes, and `trades.summary.json`, 511 bytes, 20:57:50Z;
  `outbox/report.json`, 332 bytes, 21:01:33Z, reading `"rows": 10`, the input `trades.csv` with SHA256
  `a84e2ff352f746eed76c0c7643703831c08fcd88c45ee386070b07c6ad2d2dac`, the sums `notional` 49850.5,
  `price` 701.2399999999999 and `quantity` 1530.
- **[Claude] CloudTrail, 20:47:50 to 21:02:40Z**, read at 21:05Z: the project role in five sessions. The
  worker's, `AmazonMWAAServerless`, called from Staging's private range through Staging's endpoints:
  `glue` 30 (`GetJob`, `CreateJob`, `StartJobRun`, `GetJobRun` 27), `sagemaker.api` 19
  (`DescribeProcessingJob` 18, `CreateProcessingJob`), `kms` 11 and `logs` 4. The managed services'
  sessions called from AWS's own addresses, through no endpoint of Staging's: `GlueJobRunnerSession`
  (the job's network interfaces and tags, `glue:GetConnection` 4, `logs:CreateLogGroup` 2, KMS),
  `GlueVpcAuthSession`, `AnalyticsValidation` (three `DryRun` EC2 calls), and `SageMaker` (the job's
  network interface, `ecr:GetAuthorizationToken`, `BatchGetImage` 3, `GetDownloadUrlForLayer` 33,
  `logs:CreateLogGroup`, KMS). The refusals: `SageMaker`'s direct `kms:CreateGrant` on the project key
  (*"no identity-based policy allows the kms:CreateGrant action"*), with the job going on as 6i
  measured in Sandbox; one `ecr:BatchGetImage` `InvalidParameterException` on the repository name's
  pattern; the Glue session's two `DeleteNetworkInterface` *"currently in use"*; ECS's 15
  `AttachNetworkInterface` retries. `sagemaker.amazonaws.com` created a trial component,
  `app-etl-20261019T205205-aws-processing-job`, four lineage artifacts (three `DataSet`, one `Image`)
  and four associations.
- **[Claude] The log groups the run created**, none with retention: `/aws/sagemaker/ProcessingJobs`
  (20:57:40Z, no CMK) and the Glue job's `datazone-d1veybt5oak4uo-dev/error` (20:49:14Z) and `/output`
  (20:50:03Z), beside 4.2's workflow group, `EXC-10`'s shape in Staging.
- **[Claude] 4.4's first half done.** `start-workflow-run` as the deploy identity waits on 4.3
  (decision 4).

## 2026-10-19 — pass 5: two applications in one project, the shared DAG id, the destroy

- **[user] Merged PR #201** (21:12:35Z) and asked for pass 5: *"I merged #201. I authorize the push to the
  recreated branch and a new PR; continue with pass 5 (5.1 to 5.3)."*
- **[Claude] The CLI 1.0.9's code, read again before the writes**: `workflow.create` resolves each
  manifest workflow against the YAML files it lists, registering every top-level key and nested
  `dag_id`, the first file per name winning; the operator code is matched by basename the same way;
  `destroy` deletes the workflow by its composed name, every object under each `<root>/<targetDirectory>`,
  and each Glue job a `GlueJobOperator` task names in the workflow's definition as the service holds it,
  the catalog only when a stage declares it without `disable: true`, the project only with `create: true`
  (`bootstrap/handlers/workflow_create_handler.py`, `commands/deploy.py`, `helpers/destroy_validator.py`).
  Without `--force` it prints its plan and asks.
- **[Claude] 5.1, the second application**: `orchestration-demo`, 6i's `demo-python-operator` in the
  CLI's notation (the sensor and the Python task, `bucket`, `inbox` and `outbox` from
  `{proj.connection.default.s3_shared.bucket}`, `{domain.id}` and `{proj.id}`), its code the archive of
  `examples/sandbox-orchestration/operators/build.sh` (996,233 bytes), `project.create: false`, the
  catalog `disable: true`, its storage under `orchestration-demo/python/`. `bundle --targets staging`
  into a folder of its own, 970,357 bytes, extracted with the manifest beside it, then `deploy`
  21:19:41 to 21:21:01Z, exit 0: two files, the code copied to `operatorFiles/`,
  `orchestration_demo_deploy_staging_demo_python_operator` created, `READY`, `manual_only`, one version,
  the project role, network and key, its log group with no retention, the tags `Pipeline=orchestration-demo`
  and `Target=deploy-staging` beside the CLI's four. Against a snapshot taken before it, three objects
  were added, all under its prefix and `operatorFiles/`, and none of `app-etl`'s changed; `app-etl`'s
  workflow read the same version, definition, code and modification time.
- **[Claude] 5.2, the shared DAG id**: `dagid-copy`, the same application with its workflow named
  `app-etl` and `dag_id: app-etl`, its storage under `dagid-copy/python/`. `deploy` 21:22:10 to 21:23:28Z,
  exit 0, printed *"Reading workflow from S3: s3://awsds-staging-smus-projects/dzd-d8yrvx1ko7im6o/d1veybt5oak4uo/shared/app-etl/workflows/app-etl.yaml"*
  and *"Resolved workflow uploaded to"* the same key, then created `dagid_copy_deploy_staging_app_etl`
  with `app-etl`'s definition. **0.1's inference holds, by a cause 0.1 did not name**:
  `_derive_workflow_search_prefixes` (`commands/deploy.py`) reads `target_directory`, an attribute the
  manifest's `StorageConfig` does not carry (`targetDirectory`), so both lookups fall back to the
  project's whole `shared/` root, and `app-etl/` lists before `dagid-copy/`. The rewrite wrote a new
  version of `app-etl/workflows/app-etl.yaml`, byte-identical to the one before (4,686 bytes, its
  versions read 20:06:11, 20:09:08, 20:09:31 and 21:23:26Z); the copy's code was its own,
  `dagid-copy.zip`, copied as `operatorFiles/app-etl-<n>.zip`, the name `app-etl`'s own copies carry.
- **[Claude] `app-etl` redeployed from its bundle**, 21:25:48 to 21:27:48Z, exit 0, the manifest read
  from the branch with `git show` after a first attempt stopped on the clone's other branch, before any
  AWS call: it read its own file, first in the listing, and updated its workflow, `♻️  Workflow already
  existed, updated`, to version 2 (`5a2ce43100dc50c21b0357ab5c67f4ae`), its seven files and a new
  `operatorFiles/` copy rewritten; the copy's workflow unchanged.
- **[Claude] 5.3, the plans**, each `destroy --targets staging` answered `n`: `orchestration-demo`'s
  lists its workflow, its two prefixes and its two tasks `skipped`; `dagid-copy`'s lists its workflow,
  its two prefixes, `process`, `summarize` and `write_result` `skipped`, and **`glue_job:
  app-etl-d1veybt5oak4uo`**, `app-etl`'s Glue job, read from the copy's definition. The copy's destroy is
  not run: it is the user's decision.
- **[Claude] 5.3, `orchestration-demo` destroyed**, `--force`, 21:28:54 to 21:29:12Z, exit 0: *"Catalog
  deletion is disabled (disable: true) — skipping"*, *"staging: deleted=3 not_found=0 skipped=2
  error=0"*: the workflow and the two prefixes' two objects. It left
  `operatorFiles/demo-python-operator-<n>.zip` and its log group, no retention. `app-etl`'s workflow
  (version 2), its two runs, its Glue job with its one job run, and its files survived, and so did the
  copy; the project owns no catalog object.
- **[user] Decision 8 taken**: *"remove dagid-copy with direct calls only, delete-workflow for its workflow
  and s3 rm for its dagid-copy/ prefix, leaving app-etl's Glue job in place."*
- **[Claude] The copy removed**, the Stage 17 session told first, as `awsds-infra-staging`: the workflow
  `dagid_copy_deploy_staging_app_etl` read `READY` with no run, and its prefix two objects, the copy's
  `dagid-copy.zip` and its own YAML, 795 bytes, never resolved, since its deploy had read `app-etl`'s;
  `delete-workflow` at 21:34:37Z, exit 0, then `s3 rm --recursive` on `shared/dagid-copy/` at 21:34:38Z,
  the two objects deleted, exit 0. Against a snapshot taken before: the workflow and the two objects
  gone, nothing else changed; `app-etl`'s workflow at version 2, its Glue job with its one job run. Left
  behind, as `destroy` would leave them: the copy's `operatorFiles/app-etl-<n>.zip` beside `app-etl`'s two,
  `orchestration-demo`'s `operatorFiles/` copy, and the two applications' log groups, empty and with no
  retention. 5.3 is done.

## 2026-10-19 — 7.1: lineage from the Staging Glue job

- **[user] The request**: *"Go on to 7.1 with the environment up: write what the lineage needs and hand me
  the applies."*
- **[Claude] What AWS's pages require**, read 2026-10-19: the Spark settings SageMaker Unified Studio
  documents for a Glue job, `spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener`
  with `spark.openlineage.transport.type=amazon_datazone_api`, the domain, the account and the job name;
  OpenLineage built into Glue 5.0 and later, for Spark DataFrames only (`transform.py` uses DataFrames);
  S3 paths yield S3 dataset nodes, and a graph shows only when a node is an asset; and, for a job in a
  VPC, *"make sure the Amazon DataZone VPC endpoint is deployed in that VPC"*.
- **[Claude] What Staging already holds**, read 2026-10-19: the project role carries the tag
  `AmazonDataZoneDomain=dzd-d8yrvx1ko7im6o`, so `SageMakerStudioProjectUserRolePolicy` v75's
  `DataZoneUserPermissions` grants it `datazone:PostLineageEvent` on its domain; the D13 boundary's
  ceiling is `*`; the DNS Firewall admits `*.amazonaws.com` and `*.api.aws`; the domain's share carries
  `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess` version 10, the default, whose 154 actions
  include `PostLineageEvent`, `ListLineageEvents` and `GetLineageEvent`; the domain has no customer CMK.
  Staging's VPC holds no `datazone` endpoint (issue #39). The domain's `list-lineage-events` read empty
  at 22:00:16Z, as Data Governance's InfrastructureAccess and as Staging's.
- **[Claude] The lineage settings**, `awsds/app-etl`'s branch `stage-18-staging` at `6eb795c`: the
  `transform` task's `DefaultArguments` gain `--conf` with AWS's seven settings, the domain as
  `{domain.id}`, the job name `app-etl-{proj.id}`, and the account as the staging stage's `ACCOUNT_ID`
  variable, read from the shell at deploy. `v0.2.1`'s bundle, its workflow YAML and manifest taken
  from the branch, deployed 21:57:52 to 21:59:51Z, exit 0 (a first attempt stopped at the manifest's
  validation, `JOB_IMAGE_URI` unset, before any call): the resolved YAML names the domain and
  `{{ params.ACCOUNT_ID }}`, and the workflow took version 3 (`f2ed9786ea16afcbf6b88cc93d92e937`).
- **[Claude] The endpoint, written and planned, not applied**: `staging/egress/` gains `datazone` in
  `extra_services`, planned 22:00:57Z, *"Plan: 1 to add, 0 to change, 0 to destroy."*,
  `com.amazonaws.us-west-2.datazone` with private DNS and the module's policy. Run A goes first,
  without it, so the run says whether the event leaves the VPC with no endpoint.
- **[Claude] Run A, no endpoint**: the workflow started at 22:00:13Z; the Glue job took the settings at
  22:01:10Z (`update_config`), and its run `jr_9aea84f7…` `SUCCEEDED`, 22:01:10 to 22:03:40Z, 118 s.
  The driver's error stream reads *"Registered listenerio.openlineage.spark.agent.OpenLineageSparkListener"*,
  then twice *"Could not emit lineage w/ exception"*, *"Failed to send lineage event to DataZone"*,
  caused by *"software.amazon.awssdk.core.exception.SdkClientException: Unable to execute HTTP request:
  Network is unreachable (SDK Attempt Count: 4)"* from `DefaultDataZoneClient.postLineageEvent`, each
  holding the listener about 33 s; the job went on. The domain's `list-lineage-events` read empty, and
  neither Staging's CloudTrail nor Data Governance's holds a `PostLineageEvent` since 22:00Z: the event
  never left the VPC (Lesson 42). The job's driver posts from Staging's network, which has no route to
  DataZone, so the endpoint is the measured premise.
- **[Claude] Run A's end and the second reading**: `4pwrFUq1NSnnUMI` `SUCCESS`, 22:00:17 to 22:14:04Z,
  826 s; at 22:16:40Z the domain's `list-lineage-events` still read 0 from both accounts, the second
  reading after a delay that "nothing" needs (Lesson 62).
- **[user] The endpoint applied**, `make up ENV=staging ONLY=egress AUTO=1`, as `awsds-infra-staging`
  (*"rodei o make up do staging"*). **[Claude] Read back**: `vpce-0fc40278dfb516cc8`,
  `com.amazonaws.us-west-2.datazone`, `available` since 22:51:18Z, private DNS for
  `datazone.us-west-2.amazonaws.com` and `datazone.us-west-2.api.aws`; `staging/egress/` re-plans `No
  changes` (22:54:18Z).
- **[Claude] Run B, with the endpoint**: the workflow `V4eBnEgINa6pd4U` started at 22:54:33Z; the Glue
  run `jr_a1422806…` `SUCCEEDED`, 22:55:25 to 22:57:47Z, 122 s. The driver's error stream reads
  *"Successfully posted a LineageEvent: 4kj1qq1kak6hsg in Domain: dzd-d8yrvx1ko7im6o"* and the same for
  each later event, the first 4.7 s after the application started. At 22:59Z the domain's
  `list-lineage-events` read 12 events, from both accounts, each `processingStatus` `SUCCESS`, created by
  the domain's `IAM` user profile of the project role `datazone_usr_role_d1veybt5oak4uo_bujd259b8g9zps`:
  4 `START`, 4 `RUNNING` and 4 `COMPLETE`, for the job `app_etl_d1veybt5oak4uo` in the namespace
  `default` (the `-` of `spark.glue.JOB_NAME` turned to `_`) and four of its Spark sub-jobs. The datasets
  are S3 paths, `s3://awsds-staging-smus-projects` with the inputs `…/app-etl/inbox` and
  `…/app-etl/inbox/trades.csv` and the output `…/app-etl/work/glue`. `get-lineage-node` on the write's job
  run reads a `JobRunLineageNodeType` with one upstream node and, downstream, a
  `DatasetLineageNodeType` whose `sourceIdentifier` is the output's S3 URI. No node is an asset, and the
  portal draws lineage only on an asset's page, so this run gives the portal no graph; 7.2's
  publication is where one would appear. CloudTrail held no lineage call in either account at 22:59Z.
- **[Claude] Run B's end and the second reading**: `V4eBnEgINa6pd4U` `SUCCESS`, 22:54:43 to 23:08:24Z,
  820 s. At 23:10:59Z the domain's `list-lineage-events` read the same 12 events from both accounts.
  CloudTrail had delivered the calls by then: in Staging, twelve `PostLineageEvent` by the project role's
  session `GlueJobRunnerSession`, each through `vpce-0fc40278dfb516cc8`, the new endpoint; in Data
  Governance, DataZone's own processing as `datazone.amazonaws.com` (`CreateLineageNode` 2,
  `CreateLineageNodeVersion` 3, `UpdateLineageEvent` 6, `UpdateLineageNode` 11,
  `UpdateLineageNodeVersion` 9), and this session's reads logged in both accounts. 7.1 is done.

## 2026-10-19 — 4.5: Stage 10's steps read against the CLI's deploy

- **[user] The request**: *"Go on with 4.5, the reading of the deploy against Stage 10; I will take the
  environment down and merge PR #203."*
- **[Claude] 4.5 written**, from this day's measurements and no new AWS call but one read: the Glue job's
  `--conf` carries the account rendered from the run's `ACCOUNT_ID` override, so `create_job_kwargs` is a
  template field. The stage file's table holds one row per Stage 10 step. The CLI does 1.2 and 4.2; 1.1
  outside Terraform's state, with a log group that never expires; 2.4 without a release-versioned home,
  its lookups scanning the whole `shared/` root; not D28's per-workflow role (1.3), one project role
  serving every application; not D41 item 9's declared Glue job; and nothing of 3.1, 3.4 to 3.7 or Stage
  8's production gate. Question iii is answered but for 4.3's identity, which waits on decision 4.
- **[user] The environment taken down** (*"Derrubei todo o ambiente. Pode verificar."*). **[Claude] Read
  back** at about 23:25Z: Production's three hosts `awsds-prod-gitlab`, `-proxy` and `-vpn` `stopped`, and
  no instance running, no interface endpoint and no NAT gateway in Production, Staging, Sandbox or Data
  Governance, so Staging's `datazone` endpoint went down with `staging/egress/`; no Redshift workgroup in
  Sandbox, no SageMaker app `InService` and no processing job in progress in Sandbox or Staging.

## 2026-10-19 — the pending decisions, one by one

- **[user] Decision 4 taken**: *"Decision 4: yes, 4.3 runs as awsds-deploy-staging at the next GitLab
  sitting."*
- **[user] Decision 5 taken**: *"Decision 5: yes, 7.2's subscription runs on sample data."*
- **[user] Decision 6 taken**, after asking what 5.4 answers and why it would need a project: *"sim,
  "read-only""*. **[Claude] 5.4 answered by reading**: no SageMaker AI domain per `deployment` project, so
  the environments-per-domain quota bounds it; 3.3's thirteen resources per project, the log group's
  storage the only charge at rest; a prefix and a role per project, removing pass 5's collision by
  construction. Left unmeasured, by the decision: whether a second provisioning rewrites Staging's Lake
  Formation admins.
- **[user] Decision 6 recorded above; the decisions done** but 7, the verdict, at 8.9.

## 2026-10-20 — 4.3 and 7.2 prepared, with the environment down

- **[user] The request**: *"Prepare 4.3 and 7.2 now: write and plan the deploy role's amendment and 7.2's
  table, and give me the acts for the next sitting."* A first plan stopped on an expired SSO token; the
  user signed in with `./aws/login.py`.
- **[Claude] 4.3's amendment**, `staging/foundation/deploy-role.tf`: three inline documents on
  `awsds-deploy-staging`, `sandbox/workflows/`'s test deploy role scoped to `deploy-staging` (the DataZone
  reads, the workflow calls on a workflow tagged with the project, the project role passed to MWAA
  Serverless alone, the project's `shared/` prefix, the project key matched by `kms:ResourceAliases`),
  naming the project role and the key rather than looking them up, so the project's deletion at 8.1
  leaves the slice planning. The deploy role's ceiling, `awsds-staging-deploy-boundary` at
  `deploy-role-v0.3.0`, is a `*` ceiling whose denies reach none of these. Planned 01:09:49Z, *"Plan: 3 to
  add, 0 to change, 0 to destroy."*, the plan saved for the user's apply.
- **[Claude] 4.3's job**, `stage-18-deploy` on `awsds/app-etl`'s `stage-18-staging` (`caf1ff6`, committed
  in the clone, pushed at the next GitLab sitting): manual, on the deploy runner; the bundle read with the
  runner's own role and checked against its SHA256; the branch's manifest and workflow beside it; the
  account, the subnets, the project's security group and its key read at run time as
  `awsds-deploy-staging`; `deploy --targets staging`, stopping when the log names no network from the
  `Tooling` environment; then `run` and `get-workflow-run` to the end.
- **[Claude] The membership's order**: `awsds-deploy-staging` has no group profile in the domain yet
  (Cloud Control's `<domain>|<role ARN>` read answers `NotFound`); in Sandbox the test role's appeared at
  its first DataZone call and the membership by group id followed (2026-10-19). `deploy-staging`'s
  members read: Staging's InfrastructureAccess session group `PROJECT_OWNER`, and the project role's
  own `IAM` user profile, the one that posted 7.1's events, `PROJECT_CONTRIBUTOR`.
- **[Claude] 7.2's readings**: Staging holds no Glue database; its Lake Formation admins are the two SMUS
  roles alone, and `CreateDatabaseDefaultPermissions` and `CreateTableDefaultPermissions` are empty, so a
  new database and table are Lake Formation's alone; the one registered location is the project's
  `…/d1veybt5oak4uo/dev`, registered with the project role, not hybrid. `list-permissions` on the catalog
  and on that location answers an empty list to the infrastructure user, who is no admin there, which
  proves nothing either way (Lesson 13). No principal this repository writes can create the database a
  published table needs: the path is the user's decision.
- **[user] 4.3's amendment applied**, `staging/foundation/` from the saved plan, as `awsds-infra-staging`:
  *"module.deploy_role.module.role.aws_iam_role_policy.inline["deployment-project-reads"]: Creation
  complete after 1s [id=awsds-deploy-staging:deployment-project-reads]"*, the same for `-workflows` and
  `-storage`, *"Apply complete! Resources: 3 added, 0 changed, 0 destroyed."* **[Claude] Read back**: the
  re-plan reads `No changes` (01:16:24Z); `awsds-deploy-staging` holds five inline policies, `apply-egress`,
  `state` and the three, their Sids as written.
- **[user] 7.2's path**: *"Vamos pela decisão A (recommended): add the DataLake blueprint"*.
- **[Claude] Path A written and planned**: `staging/studio/`'s `blueprint_names` gains `DataLake`, planned
  01:19:06Z, *"Plan: 2 to add, 0 to change, 0 to destroy."*, its configuration with `Tooling`'s VPC,
  subnets, provisioning and manage-access roles and boundary, and its `CREATE_ENVIRONMENT_FROM_BLUEPRINT`
  grant; `governance/`'s `deployment` row gains `DataLake`, planned 01:19:45Z, *"Plan: 0 to add, 1 to
  change, 0 to destroy."*, the profile's second environment configuration, `ON_DEMAND`, order 1, blueprint
  `d8w7c3fmbsz5cg`, in Staging. Both plans saved for the user's applies, `staging/studio/` first. No
  instrument reads Staging's configurations against a list: `./aws/studio.py` US-3 reads the Interactive
  accounts, and US-6 refuses a SageMaker AI domain in Staging, which `DataLake` does not create.
- **[user] 7.2's applies**, from the saved plans: `staging/studio/` as `awsds-infra-staging`,
  *"module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["DataLake"]: Creation
  complete after 7s [id=dzd-d8yrvx1ko7im6o|d8w7c3fmbsz5cg]"*, the grant after it, *"Apply complete!
  Resources: 2 added, 0 changed, 0 destroyed."*; then `governance/` as `awsds-infra-data`,
  *"awscc_datazone_project_profile.this["deployment"]: Modifications complete after 6s
  [id=dzd-d8yrvx1ko7im6o|dalofykyytykgg]"*, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*
- **[Claude] Read back**, 01:38:55Z: both slices re-plan `No changes`; Staging lists two blueprint
  configurations, `Tooling` (`4k186sfh08eqxc`) and `DataLake` (`d8w7c3fmbsz5cg`, updated 01:36:09Z); the
  `deployment` profile lists `Tooling` `ON_CREATE` order 0 and `DataLake` `ON_DEMAND` order 1
  (`b6bc931f-9f6b-4d15-b02d-aa65d4dd3d46`); Staging's Lake Formation admins are still the two SMUS roles.
- **[Claude] The environment created**, the two other sessions told first, as `awsds-infra-staging`:
  `datazone create-environment` with that configuration and blueprint, name `deploy-staging-lakehouse`,
  01:39:17Z, exit 0, `c2ej62w956q2a8` `CREATING`.
- **[Claude] The environment failed**, `CREATE_FAILED` read 01:40:18Z: *"Failed to deploy DataLake add-on for
  environment c2ej62w956q2a8: User:
  arn:aws:sts::<acct>:assumed-role/awsds-staging-smus-manage-access/AmazonDataZoneEnvironmentDeployer-<acct>
  is not authorized to perform: lakeformation:CreateLakeFormationOptIn on resource:
  arn:aws:lakeformation:us-west-2:<acct>:catalog:<acct> because no identity-based policy allows the
  lakeformation:CreateLakeFormationOptIn action"*, the stack `DataZone-Env-c2ej62w956q2a8`
  `DELETE_COMPLETE`. CloudTrail, 01:39 to 01:41Z: the provisioning role created the stack,
  `glue:CreateDatabase` of `glue_db_c2ej62w956q2a8`, three `lakeformation:GrantPermissions` and two
  `BatchGrantPermissions`, a `glue:UntagResource` refused, then the manage-access role's opt-in refused
  and the stack deleted. After it: no Glue database, Lake Formation's two admins and one registered
  location unchanged. Sandbox's projects hold the same `CREATE_FAILED` `DataLake` environment, on the
  same refusal, since 6f (2026-09-13) and 2026-10-15 (Stage 17's log): the blueprint has never deployed
  here.
- **[Claude] The cause, read**: the manage-access role carries `AmazonDataZoneSageMakerManageAccessRolePolicy`
  v4 alone, `sagemaker-prereqs`'s one attachment, and its document names no `CreateLakeFormationOptIn`;
  `AmazonDataZoneGlueManageAccessRolePolicy` v18 does, with the grants a subscription to a Glue table
  becomes. `staging/studio/manage-access.tf` attaches it to Staging's role for the window, beside the
  module's attachments, which `iam-role-v0.1.0` makes one by one: planned 01:42:35Z, *"Plan: 1 to add, 0
  to change, 0 to destroy."*, saved for the user's apply. The failed environment is deleted and created
  again after it.
- **[user] The attachment's first apply failed**: *"NoSuchEntity: Policy
  arn:aws:iam::aws:policy/AmazonDataZoneGlueManageAccessRolePolicy does not exist or is not attachable."*
  **[Claude] The cause**: the policy lives under `/service-role/`,
  `arn:aws:iam::aws:policy/service-role/AmazonDataZoneGlueManageAccessRolePolicy`, attachable, while the
  SageMaker one has no path; the listing that found it had printed the name after the last `/` alone
  (Lesson 38). Fixed in `manage-access.tf`, re-planned 01:46:16Z, *"Plan: 1 to add, 0 to change, 0 to
  destroy."*, the plan saved again.
