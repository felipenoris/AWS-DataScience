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
