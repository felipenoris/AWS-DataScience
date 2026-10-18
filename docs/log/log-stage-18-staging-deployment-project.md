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
