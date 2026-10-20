# Stage 18 — A deployment-only SageMaker project in Staging, measured and unwound

| | |
|---|---|
| **Status** | **Passes 0 to 3 and 5 done 2026-10-19, pass 4 done but 4.3, 7.1 done, 7.2 in progress; passes 6 and 8 to come. Decisions 1 to 3 taken by the applies of passes 1 and 2, 4 to 6 and 8 by the user; 7 is the verdict.** Every apply is the user's: the app's auto-mode classifier refuses them to Claude (*Protected-Scope IaC Apply*), so the user runs each from its saved plan ([log](../../log/log-stage-18-staging-deployment-project.md)). Pass 1: the carve-out is live (`EXC-20`): `identity/org-policies/` updated the `Workloads` document in place (the one Sid, 2,571 characters minified) and re-plans `No changes`; from Staging `datazone list-domains` answers while Production's is still the SCP's deny. Pass 2: `staging/studio/` holds the prerequisites, 14 added, re-plan `No changes`; 2.1 done by the user and read back, the domain's share holding Staging as a principal since 04:03:13Z and `list-environment-blueprint-configurations` answering an empty list from Staging; 2.3's two rows written; 2.5's second half applied at 04:31Z (2 added, 1 changed, re-plan `No changes`), so `Tooling` is configured in Staging; 2.6 and 2.7 applied, the `deployment` profile since 05:47:08Z and its grant to Staging's InfrastructureAccess session group since 05:58:00Z, after the first apply was refused a grant to the role as a user, `governance/` re-planning `No changes`. Question i was answered from the two managed bases' own templates: `ToolingLite` creates a SageMaker AI domain unconditionally and `Tooling` only when `enableSpaces` is `true`, so the `deployment` profile is `Tooling` with `enableSpaces` false and needs no `CreateDomain` carve-out. Pass 3: `deploy-staging` provisioned, its stack complete in 55 s, with no SageMaker AI domain, three roles under the D13 boundary, and the provisioning and manage-access roles made Staging's Lake Formation admins. Pass 4: 0.4 answered question vii; 4.4's two prerequisites, from Stages 8 and 10, applied by the user; `app-etl` tagged `v0.2.0` and `v0.2.1`, the second's bundle stored and its GitLab release failed on the notes' backticks (MR !4, the user's merge); 4.1's branch written. **4.2 done**: `v0.2.1`'s bundle deployed from its extracted folder, since the CLI 1.0.9 reads every local content item from the manifest's folder whatever `--bundle-archive-path` names, and the workflow carries the project's network, key and role (question v). **4.4's run `SUCCESS`** (808 s, `JSSr2Br9Zsf2b26`) once the user applied `staging/studio/workflows.tf`, `sandbox/workflows/`'s grant, after the first run was refused `glue:GetJob`: every task ran as the project role, the worker's calls through Staging's endpoints, the operator creating the Glue job and the processing job; `start-workflow-run` as the deploy identity waits on 4.3. **Pass 5's 5.1-5.3 run the same day**: `orchestration-demo` deployed beside `app-etl` and destroyed, neither touching the other; `dagid-copy`, reusing `app-etl`'s workflow name and DAG id, took and rewrote `app-etl`'s file, since the CLI 1.0.9 scans the whole shared root, and its `destroy` plan held `app-etl`'s Glue job, so decision 8 removed the copy by direct calls. **Decisions 4 to 6 taken by the user**: 4.3 at the next GitLab sitting, 7.2 on sample data, 5.4 answered by reading. **4.5 done** (question iii, but 4.3's identity), Stage 10's steps read against the CLI's deploy. **4.3 prepared 2026-10-20** (the deploy role's amendment applied by the user, the job committed on the branch's clone); **7.2's `DataLake` environment `ACTIVE`** the same day after the Glue manage-access policy, its table, publication and subscription waiting on a sitting. **7.1 done the same day**: the Glue job posts its own lineage as the project role, through a `datazone` endpoint `staging/egress/` gained for the window; without it each post read *"Network is unreachable"*. Pass 0: 0.1 read 2026-10-17 and 2026-10-18; 0.2 and 0.3 read 2026-10-18, the attached `Workloads` document with Stage 9's nine statements included; 0.5 is the battery Stage 9's log records after that apply. 2.3 written 2026-10-18 with no row: `sandbox/foundation/`, `production/tooling/` and `staging/foundation/` re-plan `No changes`. 5.4's quotas read: Staging admits ten SageMaker AI domains, the ceiling a `Tooling` base meets first. **Written 2026-10-17** from a cloud session with no AWS reading, on the user's word of that day at 18:28 UTC (*"vamos medir em staging o que falta para completar o quadro"*), the answer to the card of 2026-10-16 that offered to measure before [Stage 10](stage-10-orchestration-promotion.md) builds [D41](../decisions/D41-sagemaker-application.md) item 2. A measurement and its teardown, not a build: AWS's default shape for a deployment account, a SageMaker Unified Studio project that the CI/CD CLI deploys into and no person works in, is created once in `Staging`, read against this estate's perimeter, and unwound at pass 8 whatever the verdict. **D41 stands until the verdict** (8.9, decision 7): Stage 10 keeps item 2's design, no project in Staging or Production, while this stage runs. Nothing below is a measurement unless it carries its date |
| **Prerequisites** | **[Stage 8](stage-08-cicd-pipelines.md)**: `awsds-deploy-staging` and the deploy runner (pass 1), the deploy image `v0.2.0` with the CLI 1.0.9, and `app-etl` as an application whose release carries a bundle (2.5, 2.5a): no tag has run one, `awsds/app-etl`'s newest tag being `v0.1.0` (read 2026-10-16, the Stage 8 log), and the first carries the `process` task's `VolumeKmsKeyId` (PR #156), which `DenySageMakerJobsWithoutVolumeEncryption` requires in `Workloads` and under Sandbox's D13 boundary alike. **Two changes of other stages' later passes, which 4.4's run needs first** (read in the code 2026-10-18, neither applied): **[Stage 8](stage-08-cicd-pipelines.md) step 3.0's first half**, the application image's pull grant for Staging: the `process` task's image is `awsds-prod-ecr-app-etl` by digest, which the job's role pulls through the service ([6i](stage-06i-sandbox-orchestration.md)), and the repository admits `APP_REGISTRY_CONSUMERS` alone, `["sandbox"]` (`backend.py`), so Staging's row comes with a `staging` alias and identity read in `production/registry/`, whose `account_id_by_folder` resolves `sandbox` alone and fails the plan on any other key; and **[Stage 10](stage-10-orchestration-promotion.md) step 1.2's bump of `staging/foundation/` from `vpc-v0.3.1` to `vpc-v0.4.0`**, whose one functional change is `mwaa-serverless-code-files-*-<region>-prod` on the S3 gateway endpoint's policy: a worker reads a workflow's `Code` object, the archive a Python task's callable is imported from, out of that bucket, and without it the workflow fails at environment preparation, before its first task ([6i](stage-06i-sandbox-orchestration.md) decision 7). `app-etl` carries one (`code/app-etl.zip`, for `summarize`), as does 5.1's `demo-python-operator`, which matters if it is run. Stage 8's decision 23 places 3.0 in its pass 4, after Stage 9, and the bump is Stage 10's pass 2, so both run in this stage's window, after its decisions. **Both applied 2026-10-19 by the user**, and both slices re-plan `No changes`: `APP_REGISTRY_CONSUMERS` gains `staging`, with the alias and identity read in `production/registry/`, whose plan changes the `app-etl` repository's pull policy alone, Staging's account root added; and `staging/foundation/` pins `vpc-v0.4.0`, whose plan changes the S3 gateway endpoint's policy alone, the `mwaa-serverless-code-files-*` family added. **[6a](stage-06a-unified-studio.md)**: the domain `awsds-studio` and the profile machinery of `data-governance/governance/`. **[6b](stage-06b-development-becomes-staging.md) pass 1**: the unwinding order pass 8 repeats, measured on this account on 2026-09-06. **[6c](stage-06c-networking-hub.md)**: Staging's private routing and its 11 `[E]` endpoints, so a sitting is `make hub-up` then `make up ENV=staging ONLY=egress`, Stage 8 step 3.1's form, which names the one slice a sitting needs. **[Stage 9](stage-09-deployment-targets.md) pass 1's `identity/org-policies/` apply**: its job statements, on `main` since PR #144, were attached on 2026-10-18 at 19:54Z and the battery's `ou` phase read them after (Stage 9's log, PR #176; this stage's 0.3 read the attached document), so 1.3 follows that apply, and this stage's processing jobs run under them (risk "The `Workloads` document"). Stage 9 pass 5 (`staging/data/`, step 4) is not a prerequisite, and this stage runs before it (risk "The Lake Formation seat") |
| **Consumes** | [D7](../decisions/D07-orchestration.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D20](../decisions/D20-staging-account.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D41](../decisions/D41-sagemaker-application.md) |
| **Proves** | — (no `INT-nn` row: the association is [INT-12](../integrations.md)'s shape on an account INT-12 leaves out, and pass 8 removes it). It exercises [INT-23](../integrations.md) once, a subscription across two accounts over sample data (7.2, decision 5), and answers for Stage 10 how much of its steps 1.1, 2.4 and 4.2 a `deploy --targets staging` from the bundle does (4.5) |

*Read with [`docs/SMUS.md`](../../SMUS.md) (the blueprint table, the `ToolingLite` row, the CI/CD CLI),
D41's "What the lab measured on 2026-10-15", and 6b pass 1, whose steps pass 8 repeats. The report this
stage answers, in Portuguese, is `discussoes/runtime-sagemaker.md` in the Claude project's library.*

---

**Objective:** one project in `Staging`, created from a deployment-only project profile, whose only members
are the identities that deploy, holding two applications the CI/CD CLI deployed from their bundles; read for
what the blueprint creates in a `Workloads` account, what the CLI's `deploy` and `run` do there, what a
person can and cannot do in it, and what lineage and the catalog gain from it; then every piece removed in
the reverse order. The verdict says whether D41 item 2 holds (no project in Staging or Production, the
pipeline deploying the bundle itself) or its alternative replaces it (a project in each deployment
account, the CLI deploying every stage).

**Why Staging.** It carries Production's SCP document (`Workloads`), holds sample or synthetic data only
(D20), and was an associated account until 6b (2026-09-06), so both the association and its removal are
paths already measured on it. Production is not touched.

## The questions

Each is answered in the stage log with its date, the ones that come out fine included. Items i to vii are
the report's list of 2026-10-16; viii to x are the user's three lines of 2026-10-17; xi follows from Stage
6f's reading of the domain unit's policies.

| # | Question | Step |
|---|---|---|
| i | Does a project live in a `Workloads` account with spaces and apps still denied? `Tooling` creates a SageMaker AI domain per project, which `DenyInteractiveSageMakerSurface` refuses on `CreateDomain`; does `ToolingLite` create one? **Read 2026-10-19 from the templates** (the log): `ToolingLite`'s creates `AWS::SageMaker::Domain` with no condition, and `Tooling`'s creates it under `sageMakerDomainRequired`, `isDefaultTooling` and `enableSpaces == "true"`, so a `Tooling` environment with `enableSpaces` false creates none. Whether the deploy honours the profile's override of a parameter the blueprint marks not editable is 3.2's first reading; `experimentation` overrides `maxIdleTimeoutInMinutes`, also not editable, and its projects deploy **Measured 2026-10-19 at 3.2**: yes, for `Tooling` with spaces off. The project provisioned with no `CreateDomain` and no refusal from the SCP or the boundary. | 3.2 |
| ii | What does the blueprint create in a deployment account (roles and their policies, a domain, security groups, buckets and prefixes, keys, Glue databases, Athena workgroups, Lake Formation registrations and admins, data sources and their schedules, RAM shares), and which principals call `datazone:*` there? **Read 2026-10-19 at 3.3** (the log): thirteen stack resources, three bounded roles, one security group, two Glue connections, two Athena workgroups, a log group, the `dev/` prefix registered in Lake Formation, the two SMUS roles made Lake Formation admins, nine connections, no data source, no RAM share of its own. **Corrected 2026-10-20**: the provisioning also left an S3 Access Grants instance, `default`, created by the provisioning role at 06:06:50Z, and a location for the project's prefix, created by the project role's retry at 06:06:51Z; 3.3 read the first attempt's refusal alone. 7.2's `DataLake` environment adds a Glue database, its Lake Formation grants and a daily Glue data source. | 3.3 |
| iii | What does `deploy --targets staging` from `app-etl`'s release bundle write, as which identity, and how much of Stage 10's steps 1.1, 2.4 and 4.2 does it do; what stays to be built (the chain, the failure rule, Stage 8's manual gate, D28's per-workflow role)? **Answered 2026-10-19 at 4.5, but 4.3's identity**: the deploy writes the bundle's files under the project's `shared/` and a code copy under `operatorFiles/`, and creates or updates the workflow with the project's network, key and role, as the caller (4.3 measures `awsds-deploy-staging`); it does 1.2 and 4.2, 1.1 outside Terraform's state and 2.4 without a release-versioned home; the chain, the failure rule, the production gate and D28's per-workflow role stay to be built, the last impossible in this shape, which has one role per project | 4.2-4.5 |
| iv | Does a membership designation (`PROJECT_CATALOG_VIEWER` or another the API lists) give a person a view of the workflows and their runs with no write? | 6.1 |
| v | Does a profile with `enableSpaces` false and not editable give a project with no spaces, in which the CLI still deploys with the project's network and key? **The first half measured 2026-10-19 at 3.2**: the stack's `enableSpaces` reads `false`, and no domain or space exists. **The CLI's half measured 2026-10-19 at 4.2: yes**, the workflow created with the project's two subnets and security group and under the project key, which the CLI 1.0.9 resolved from the `Tooling` environment through its IAM connection fallback. | 3.2, 4.2 |
| vi | Does a boundary on the project role that denies the `airflow-serverless` writes to a person's session lock the editor and the portal's run button while the worker's session still runs the tasks, and which session key tells the two apart? | 6.2 |
| vii | Does a role that is not a member of the project find a CLI-made workflow by its composed name and start it, as Stage 10's chain role must? **Measured 2026-10-19 at 0.4**: yes. The service authorized the start by IAM alone, plus the starter's own `kms:Decrypt` and `kms:GenerateDataKey` on the workflow's key. | 0.4 |
| viii | Do two applications share one project cleanly (workflow names, storage prefixes, tags, the one project role), and does removing one leave the other's workflows and files? What does one project per application cost and change? **Measured 2026-10-19 at 5.1-5.3**: two applications whose workflows have distinct names share the project cleanly, apart by the workflow name `<application>_<project>_<workflow>`, the tag `Pipeline` and their prefixes, and destroying one left the other's workflow, runs, files and Glue job. A workflow name or DAG id shared across applications does not: the CLI 1.0.9 scans the whole shared root, and the copy took `app-etl`'s file, rewrote it, and drew a `destroy` plan holding `app-etl`'s Glue job. **The cost half answered 2026-10-19 at 5.4, by reading**: near nothing at rest, a prefix and a role per project, the collision gone by construction | 0.1, 5.1-5.4 |
| ix | Does the CLI's `run` start anything but a workflow, for an application whose manifest deploys a model or holds no workflow? The code says no (0.1), and 4.4 runs it once. **Measured 2026-10-19 at 4.4: no.** `run` listed the account's workflows, found the composed name and called `StartWorkflowRun` with the stage's five variables as `OverrideParameters`, and nothing else; `--workflow` is required, so a manifest with no workflow gives it nothing to start | 0.1, 4.4 |
| x | Does a Glue job the Staging project runs post lineage that the domain shows, and does a Sandbox project's subscription to an asset the Staging project publishes become a Lake Formation grant across the two accounts? **The first half measured 2026-10-19 at 7.1: yes, through an endpoint.** With AWS's OpenLineage settings the job posts its own events as the project role, which already holds `PostLineageEvent`, and the domain holds them, readable from both accounts; without a `datazone` endpoint in Staging's VPC each post failed *"Network is unreachable"*. The portal draws none of it, since no node is an asset | 7.1, 7.2 |
| xi | Do the domain unit's policies keep people out of the project: who may create a project from the deployment profile, add a member, or take ownership? | 6.1 |

## What this stage builds, and in which accounts

Every row is removed at pass 8, at the step the last column names.

| Where | What | Layer | Removed at |
|---|---|---|---|
| `identity/org-policies/` (amended) | the carve-out of `Staging Account` from `DenyDataZoneEntirely`, and from `sagemaker:CreateDomain` only if decision 1 lands on `Tooling`, by `aws:PrincipalAccount` against a new placeholder `<ACCOUNT_ID_STAGING>`; the battery's rows for both directions | — | 8.7 |
| Data Governance, console (user) | the association of `Staging Account` to `awsds-studio` | — | 8.4 |
| `scripts/tfhygiene/backend.py` | the `staging` rows of `SMUS_DEPLOYMENT_MEMBERS`, the list 2.3 wrote empty for an associated account no person works in, and of `SMUS_ASSOCIATED` | — | 8.2 |
| `staging/studio/` (new) | the blueprint prerequisites `sandbox/sagemaker/` holds, through `terraform-modules/sagemaker-prereqs/` (the provisioning and manage-access roles, the D13 boundary for the project role, the project key, the projects bucket, the log group), and on its second apply the configuration of decision 1's base blueprint alone, with its grant; `sandbox/workflows/`'s grant on `deploy-staging`'s project role (`workflows.tf`, 4.4); `DataLake`'s configuration and grant, for 7.2's table (decision 5, path A); `AmazonDataZoneGlueManageAccessRolePolicy` on the manage-access role (`manage-access.tf`, 7.2) | `[P]` for the stage's life | 8.1 (the attachment), 8.3, 8.6 |
| `data-governance/governance/` (amended) | the project profile `deployment`: the base blueprint's environment configuration and, for 7.2, `DataLake`'s on demand, with `enableSpaces` false and not editable where the blueprint has it; its create grant names the identity decision 3 picks and no persona group | — | 8.2 |
| The domain | the project `deploy-staging`, whose only members are the identities that deploy (decision 3), and its two environments, `Tooling` and, for 7.2, `DataLake` | DataZone's | 8.1 |
| Staging, by the provisioning | the S3 Access Grants instance `default` and the project prefix's location (created 2026-10-19 at 3.1), and the Glue database of 7.2's failed environment | the blueprint's | 8.1 |
| `staging/foundation/` (amended for 4.3, decision 4 taken) | the actions 4.2's CloudTrail list adds to `awsds-deploy-staging`, three inline documents in `deploy-role.tf` | `[P]` | 8.8 |
| `staging/egress/` (amended) | `datazone` in `extra_services`, the endpoint 7.1's Glue job posts lineage through | `[E]` | 8.8 |
| `awsds/app-etl` and one awsds-workflows example | a `staging` stage in `app-etl`'s manifest, on a measurement branch that is never merged; the example's two manifests, `orchestration-demo` and `dagid-copy` (5.1, 5.2), in a measurement folder on the laptop, never committed | — | 8.8 |

**Not built**: `staging/orchestration/`, a chain or a schedule, the Glue job's declaration in a Staging
slice (D41 item 9), anything in Production. **Why `staging/studio/` and not `staging/sagemaker/`**:
conventions §6 keeps `staging/sagemaker/` for Stage 9 step 4.3's job roles, which stay, and a slice
destroyed whole at 8.6 cannot share a folder with one that does not.

## Who executes each action

| Tag | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, only after the user authorizes that action in chat, with the SSO user, the account and the permission set stated first |
| **[user]** | the console and portal acts, GitLab settings, git pushes, and every log entry the user writes |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make, in the same sitting |
| **[pipeline]** | the deploy runner as `awsds-deploy-staging` |

## Step numbers are identifiers, not an order

| Pass | What | Who |
|---|---|---|
| **0** | preflight: the CLI read, the Sandbox environment as the before, Staging as it is, question vii in Sandbox | Claude; Claude⚡ for 0.4 |
| **1** | the carve-out, battery first | Claude, user, Claude⚡ |
| **2** | the association, the blueprint configuration, the profile | user, Claude⚡ |
| **3** | the project and what it created | Claude⚡; Claude reads |
| **4** | the deploy and the run, from the laptop, then from the deploy runner | Claude⚡; pipeline |
| **5** | a second application in the same project | Claude⚡ |
| **6** | a person in the project, and the boundary | user; Claude reads |
| **7** | lineage, and a subscription across accounts | Claude⚡; user |
| **8** | the unwinding, then the verdict | Claude⚡; user |

Pass 8 runs whatever the earlier passes found: a pass that fails stops the stage and goes to pass 8, which
removes only what exists, in its order.

## To execute

### 0. Preflight

- **0.1 — [Claude] The CLI 1.0.9's code, for what the passes rely on** (viii, ix): read 2026-10-17 from
  its sdist and again 2026-10-18, nothing executed; the log records the file and line of each answer.
  - **A stage names its project** by name, or with `create`, `profileName`, `owners`, `contributors` and
    `role`, and its domain by id, name or tags with a region and no account (`application_manifest.py`).
    The CLI calls AWS with the caller's credentials in that region and assumes no role, and a `deploy`
    takes the first stage `--targets` names, so one call deploys one stage in one account.
  - **With `create: false` a missing project stops the deploy** (*"make sure the SMUS project is
    pre-created manually"*). With `create: true` it calls `CreateProject` with the profile named, or the
    domain's only profile; an unknown profile name takes the first profile the domain lists, with a
    printed warning, and the deploy goes on. `role.policies` without an ARN creates an IAM role,
    `smus-<project>-role` unless `role.name` names it. It never enables a blueprint
    (`project_manager.py`).
  - **Two applications in one project** differ by the workflow name `<application>_<project>_<workflow>`
    and the tag `Pipeline`; the tag `Target` names the project they share. Their files share the
    project's storage root with no application prefix, and `workflow.create` scans that whole root and
    takes the first file per DAG id, so two applications with one DAG id can take each other's file
    [inferred from the code; measured 2026-10-19 at 5.2, the cause an attribute the scan reads under a
    name the manifest's model does not carry, `target_directory`, so it covers the whole root whatever
    `targetDirectory` says]. The copies under `operatorFiles/` are never pruned; a bundle lookup falls
    back to any zip in its folder; a name keeps only letters, digits and `_` at creation while `run` and
    `destroy` map only `-`, so an application's name stays within letters, digits and `-` (`deploy.py`,
    `bundle_storage.py`).
  - **`destroy` removes what the manifest declares**, never what a deploy recorded: the workflows by
    name; the S3 prefix `<root>/<targetDirectory>` with no trailing slash, so `exemplos/demo` also covers
    `exemplos/demo-x/` [inferred]; every catalog object the project owns, manual ones included, when the
    stage declares `deployment_configuration.catalog` without `disable: true`, which `app-etl`'s manifest
    does not; and the whole project when `project.create` is true. It deletes no IAM role
    (`destroy_validator.py`, `destroy_executor.py`).
  - **`run` starts the workflow `--workflow` names in each stage `--targets` lists**, and in every stage
    of the manifest when it lists none (`StartWorkflowRun`, the stage's variables as overrides), and
    returns without waiting; its `--command` reaches the Airflow CLI on provisioned MWAA only. Nothing in
    the code starts a notebook, a pipeline, a training job or an endpoint, and `destroy` knows only the
    `GlueJobOperator`'s job (`run.py`, `operator_registry.py`). The CLI's own ML examples train and
    deploy inside workflow tasks: `ml/training`, `ml/deployment` and `genai` through
    `SageMakerNotebookOperator`, which this estate's lint refuses (6d decision 14 (b)), and `mlops`
    from a processing job that creates the endpoint. Stage 10 step 5.4 serves a model by batch
    transform inside a workflow.
- **0.2 — [Claude] Read the Sandbox project's `Tooling` environment as the before** (ii): its
  CloudFormation stack's resources, each role's trust and policies, its data sources and their
  schedules, `./aws/studio.py`. Question ii is a comparison with this list. **Read 2026-10-18** (the
  log): each project's stack `DataZone-Env-<environment>` holds the same 14 resources and parameters
  but for its ids, created by the provisioning role as `datazone.amazonaws.com`: three roles under the
  D13 boundary, a `VpcOnly` SageMaker AI domain, a security group with every egress open, two Glue
  network connections, two Athena workgroups, the project's `dev/` prefix registered in Lake Formation
  under the project role, a log group at 731 days under the project key, and a schedule group. Outside
  the stack, the model-package data source runs daily at the project's creation minute and fails
  (`EXC-11`).
- **0.3 — [Claude] Read Staging as it is**: `./aws/studio.py`'s `US-6` (`datazone` reads denied in
  `Workloads`); CloudTrail's `datazone.amazonaws.com` events in Staging for 30 days, denials only
  expected; the `Workloads` document as attached, Stage 9 pass 1's statements in it (Prerequisites);
  Staging's Lake Formation admins (`get-data-lake-settings`); `awsds-deploy-staging`'s policy and
  ceiling, against the calls the CLI made in `test` (Stage 8 verification xix's list). **Read
  2026-10-18** (the log): `US-6` passes; CloudTrail holds 7 `datazone` events in 30 days, each the
  infrastructure user's `ListDomains` refused; the attached `Workloads` document has nine statements
  and equals `main`'s file, `DenyDataZoneEntirely` with no condition; Staging has no Lake Formation
  admin and no registered location; of the 34 actions `awsds-deploy-sandbox-test` holds for the CLI,
  `awsds-deploy-staging` holds `ec2:DescribeVpcEndpoints` alone, and its ceiling denies none of the
  others, so 4.3 amends the identity policy alone.
- **0.4 — [Claude⚡] Question vii, in Sandbox, with no Staging project**, in a raised session
  (`make hub-up`, then `make up ENV=sandbox`): the calls go from the laptop, but the run's tasks need
  `sandbox/egress`'s `[E]` endpoints ([6i](stage-06i-sandbox-orchestration.md)'s prerequisites). As
  `awsds-infra-sandbox-1`, first read whether `InfrastructureAccess` is a member of the `test` project
  (`EXC-17` leaves it unanswered), then `aws mwaa-serverless list-workflows` and `start-workflow-run`
  on the workflow the CLI made there, found by its composed name `<application>_<project>_<workflow>`,
  and `get-workflow-run` to its end. A non-member's run that starts shows that the service authorizes
  by IAM alone, which is what Stage 10's `awsds-<env>-chain-exec` needs; a refusal names the layer. One
  run, cents. **The reads ran 2026-10-18** (the log): `InfrastructureAccess` is not a member of `test`,
  whose `list-project-memberships` answers it anyway, and as a non-member it lists and reads
  `houseprice_etl_test_experimentation_houseprice_etl`; the run is what remains. **Run 2026-10-19**
  (the log): started at 18:32:41Z as the non-member, `SUCCESS` at 18:35:01Z, nothing refused. The
  start's only other authorization is KMS: `GenerateDataKey` and `Decrypt` on the project key under
  the starter's session, and a `Decrypt` on each `get-workflow-run`. The run took the workflow's
  `SUBNET_AZ1` and `SUBNET_AZ2` as overrides, which the YAML reads with no default.
- **0.5 — [Claude] Run the battery as it stands**: `./aws/probes/scp-battery.py --phase ou`, the before
  for 1.3. **Run 2026-10-18 at 19:55 UTC** after Stage 9's `Workloads` apply and recorded in Stage 9's
  log: 39 as expected, 0 unexpected, 7 not measured, Staging's `datazone:ListDomains` `DENY-SCP`.

### 1. The carve-out (D17, D26)

`DenyDataZoneEntirely` refuses every call this stage makes from Staging: the blueprint configuration is
written from the member account, and the CLI reads the project and its connections as the identity that
deploys.

- **1.1 — [Claude] Write it.** In `awsds-org-scp-ou-workloads.json`, `DenyDataZoneEntirely` gains
  `"Condition": {"StringNotEquals": {"aws:PrincipalAccount": "<ACCOUNT_ID_STAGING>"}}`. If decision 1
  lands on `Tooling`, `sagemaker:CreateDomain` leaves `DenyInteractiveSageMakerSurface` for a statement
  of its own under the same condition, so `CreateSpace`, `CreateApp`, `CreateUserProfile`,
  `CreatePresignedDomainUrl` and `StartSession` stay denied in Staging. `<ACCOUNT_ID_STAGING>` joins the
  substitutions of `locals.tf` and of `render.py`, resolved by the exact vended name `Staging Account`
  with `status == "ACTIVE"`, the way `identity_account_id` is, so no id enters a tracked file.
  `POLICIES.md`'s rows name the carve-out, this stage and 8.7; `docs/AWS_STATE.md` gains an `EXC-nn`
  for the window. Production stays under the whole deny. **Written 2026-10-19** without the
  `CreateDomain` split, decision 1's recommendation creating no SageMaker AI domain: the condition on
  `DenyDataZoneEntirely`, the placeholder resolved in `locals.tf` and `render.py` by the vended name, a
  precondition in `policies.tf` that refuses a placeholder surviving the rendering, `POLICIES.md`'s row
  and the README; `render.py` substituted every token and read the document at 2,571 characters
  minified. `EXC-20` is written when the apply lands.
- **1.2 — [Claude] Write the battery's rows** (`aws/probes/probes.py`): from `awsds-infra-staging`,
  `datazone list-domains` reaches authorization (the carve-out matches); from the canary under the
  candidate document, the same call is denied with the SCP's wording (the condition does not leak); if
  1.1 split `CreateDomain`, `sagemaker:CreateSpace` from Staging is still denied. **Written
  2026-10-19**: the Staging `ListDomains` row reads `allow` for the window, the `prod` row keeps the
  deny, and a Staging `CreateSpace` row (`blocked`, no such domain) reads that the rest of the document
  still binds the account. The runbook's phase 4b is the procedure for an amended per-OU document,
  re-probed in the OU's own accounts with nothing parked on `Policy Test`, so 1.3's first clause does
  not apply.
- **1.3 — [user + Claude⚡] Exercise, then attach**: the candidate on `Policy Test` first
  ([`scp-battery.md`](../runbooks/scp-battery.md)), then `identity/org-policies/` applied as
  `awsds-infra-identity`, expecting one in-place update of the `Workloads` document; then the battery's
  phase `ou`, and from `awsds-infra-prod` a `datazone list-domains` still denied. **Planned 2026-10-19** as
  `awsds-infra-identity`, `-input=false`: `aws_organizations_policy.this["awsds-org-scp-ou-workloads"]`
  updated in place and nothing else, the content differing in the one Sid; the apply was refused to
  Claude by the auto-mode classifier (*Protected-Scope IaC Apply*) and is the user's, from the saved
  plan, followed by the re-plan, `./aws/org-policies.py`, the battery's phase `ou` and the two
  `list-domains` probes (the log). **Applied 2026-10-19 by the user**, *"0 added, 1 changed, 0
  destroyed"*: the re-plan `No changes` (03:51Z), `./aws/org-policies.py` all checks passed, and at
  03:52Z Staging's `list-domains` answered an empty list, Production's was refused by the SCP
  (`p-83t232f4`) and Staging's `CreateSpace` by the same SCP; `EXC-20` records the window. The
  battery's phase `ou` at 03:53Z: *"40 as expected, 0 unexpected, 7 not measured"*, Staging's
  `ListDomains` `ALLOWED`, its `CreateSpace` and Production's `ListDomains` `DENY-SCP` (the log). Done.

### 2. The association, the blueprint and the profile (D26)

- **2.1 — [user] Associate `Staging Account`** in the console: sign in as the *Infrastructure User*,
  account **Data Governance**, permission set **`InfrastructureAccess`**, then Amazon DataZone → View
  Domains → `awsds-studio` → Account associations → request the association for `Staging Account`. The
  association raised no invitation on 2026-08-21 under org-wide RAM. **Done 2026-10-19 by the user**; RAM
  dates the share's new principal at 04:03:13Z.
- **2.2 — [Claude] Read it back**: as `awsds-infra-staging`, `datazone
  list-environment-blueprint-configurations` succeeds and returns an empty list, the call that cannot
  succeed before the association; `ram get-resource-shares --resource-owner OTHER-ACCOUNTS` holds the
  `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` share, and its permission is read against the
  `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess` that AWS's release note of 2026-07-30
  names for cross-account setups (*"Existing RAM resource shares do not auto-update"*). **Read 2026-10-19
  from 04:05Z**: the call exits 0 with `{"items": []}` where it read `UnauthorizedException` at 03:52Z;
  the share is `ACTIVE` with no invitation, its principals Staging and Sandbox; the permission is at
  version 10, the default and the only attachable version since 2026-06-04, so the share created
  2026-08-21 carries it. `./aws/studio.py` on the four infrastructure profiles passes, `US-2` reading
  Staging with the shared domain and none of its own. The domain holds an `ACTIVATED` IAM user profile
  for Staging's InfrastructureAccess role, the principal decision 3 names.
- **2.3 — [Claude] Give the deployment account a list of its own before any row moves.**
  `SMUS_MEMBERS` holds two meanings today, the accounts associated to the domain and the accounts people
  work in, and its readers outside `governance/` mean the second: `PERSONA_VENDING_ACCOUNTS` (the
  persona's vending policy in each member's `foundation/`), `interactive_private_cidrs()` (the GitLab
  security group's HTTPS sources), the `readers` of `production/sagemaker/` (Stage 9's model-status
  readers), and refusal 8 in `layers.py`, which would refuse `awsds-deploy-staging` every Staging slice.
  Staging is the first account that is associated and no person's workspace (Lesson 51). So the edit adds
  a list of deployment members, read by `governance/`'s `members` map and by `profiles_enabled`, and by
  none of the four. The order of `backend.py`'s note holds: `SMUS_ASSOCIATED` gains `staging` before the
  new list does, or `profiles_enabled` flips false and the next `governance/` apply destroys
  `experimentation`. After each regeneration, `sandbox/foundation/`, `production/tooling/` and
  `staging/foundation/` re-plan `No changes`. **Written 2026-10-18 with no row**:
  `SMUS_DEPLOYMENT_MEMBERS`, empty, beside `SMUS_ASSOCIATED`, and a guard that refuses an account in
  both lists at import; the three `governance/` comments that named `SMUS_MEMBERS` alone name both.
  Every slice's generated tfvars, laptop and pipeline, and refusal 8's answers are identical before and
  after, and a simulated `staging` row changes `governance/`'s emission alone, with `profiles_enabled`
  false while the row precedes its `SMUS_ASSOCIATED` row. The three slices re-planned `No changes`.
  **The rows written 2026-10-19**, `SMUS_ASSOCIATED` first. Over the 38 declared slices, the first row
  changes `staging/studio/`'s `blueprints_enabled` alone and the second `governance/`'s `members` alone,
  refusal 8 unchanged; the three slices re-plan `No changes` at 04:15Z, and `governance/` carries
  Stage 17's `MLflowApp` configuration alone.
- **2.4 — [Claude] Write `staging/studio/`**: `sandbox/sagemaker/`'s shape through
  `terraform-modules/sagemaker-prereqs/` at its pinned tag, `blueprints_enabled` from `SMUS_ASSOCIATED`,
  decision 1's blueprint alone in the configurations and their regional parameters (not the eleven), the
  D13 boundary field set; `layers.py` gains its rank and `[P]` row. Three rows go with it: the slice's
  entry in conventions §6, its row in `docs/NETWORK.md` §2.1 in `sandbox/sagemaker/`'s shape (it
  hands the blueprint Staging's VPC and private subnets, which `check-network-doc.py` does not
  require), and `backend.py`'s emission for the slice name `studio`, which the `sagemaker` branch
  gives by name today (`account_folder`, `lake`, `domain`, `blueprints_enabled`). **Written
  2026-10-19**: `staging/studio/` from `sandbox/sagemaker/`'s files on `sagemaker-prereqs-v0.6.0`, with
  `blueprint_names` a variable defaulting to `["Tooling"]` (decision 1 changes one line) and
  `cost_center` `stage-18`; the rank `studio` at 46 and the `[P]` row in `layers.py`, the `studio`
  emission in `backend.py`, the rows in conventions §6 and `NETWORK.md` §2.1. `terraform init` took
  `aws` 6.69.1 and `awscc` 1.106.0, and the lock carries the three platforms.
- **2.5 — [Claude⚡] Apply it twice as `awsds-infra-staging`**: the prerequisites, then, after 2.3's
  `SMUS_ASSOCIATED` row, the configuration and its grant; the boundary field read back with `get-role`,
  since it is write-only. **The first half planned 2026-10-19** as `awsds-infra-staging`: 14 to add,
  nothing changed or destroyed (the two roles with their managed-policy attachments, the boundary, the
  key and its alias, the bucket with its five settings, the log group); the apply refused to Claude by
  the classifier, so the user runs it from the saved plan, then the re-plan reads `No changes`.
  **Applied 2026-10-19 by the user**, *"14 added, 0 changed, 0 destroyed"*, the roles created at
  03:47:52Z; the re-plan `No changes` (03:52Z). Read back: the provisioning role trusted by
  `datazone.amazonaws.com` and `cloudformation.amazonaws.com`, the key `Enabled` and customer-managed,
  the bucket versioned with every public-access block on, the log group at 30 days, and Staging's Lake
  Formation settings as 0.3 read them (no admin, version 1). **The second half planned 2026-10-19** at
  04:13:56Z, saved as `stage18-studio-2.tfplan`: 2 to add, 1 to change, 0 to destroy. It creates the
  `Tooling` configuration with the boundary, the two roles and Staging's network, and its
  `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant to `CONTRIBUTOR` projects of the root unit; the project key's
  policy gains the domain execution role and the two project-role statements the module writes once a
  domain id exists. The apply takes decision 1's base. **Applied 2026-10-19 by the user**, *"2 added,
  1 changed, 0 destroyed"*, the configuration created at 04:31:00Z; the re-plan `No changes`
  (04:32:40Z). `./aws/studio.py`'s `US-3` reads Interactive accounts only, so the read-back was by
  hand: the configuration, Staging's only one, returns the boundary, the two roles and the regional
  parameters through DataZone's own API, while Cloud Control's read omits the boundary; the grant
  names `CONTRIBUTOR` projects of the root unit; the key policy holds nine statements; Staging holds
  no SageMaker AI domain and no stack beyond Control Tower's five.
- **2.6 — [Claude] Write the profile `deployment`** in `governance/`: `local.project_profiles` gains it,
  and `profiles.tf` takes each profile's blueprint list from the profile (every profile reads
  `category_one_blueprints` today); its base `ON_CREATE`; `experimentation`'s Tooling parameters, plus
  `enableSpaces` false and not editable where the blueprint carries it; its
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to decision 3's identity, never to
  `sso-group-data-scientists`. **Written 2026-10-19 behind a switch**: `locals.tf`'s
  `deployment_profile_enabled`, false, so `governance/`'s plan reads as before (04:21:26Z, `MLflowApp`
  alone). The `deployment` row (Staging, `["Tooling"]`, a null `group`), each profile's own blueprint
  list and overrides under a precondition holding Tooling first and category 1 only, the `staging`
  alias with Staging's identity and its InfrastructureAccess role resolved by name, and the grant to that
  role, whose principal 2.7 corrected to the role's session group. Set true in the working copy and back, the plan read 2 to add
  and 1 to change (04:21:59Z): the profile (`Tooling` alone, `ON_CREATE`, `experimentation`'s six Tooling
  overrides and `enableSpaces` `"false"` locked, a value the template's AllowedValues admit) and its
  grant, `experimentation`'s grant unchanged. `./aws/studio.py`'s `US-4` passed with any extra profile;
  it now fails on one outside the contract and reads `deployment` as this stage's window.
- **2.7 — [Claude⚡] Apply `governance/` as `awsds-infra-data`**: the profile and its grant added,
  `experimentation` unchanged. A plan that destroys
  `awscc_datazone_project_profile.this["experimentation"]` stops the step. Stage 17 pass 1's
  `MLflowApp` configuration on `experimentation` was planned and unapplied on 2026-10-18, so 2.7 runs
  after Stage 17's apply, and the two stages never share one. Its edit sets `deployment_profile_enabled`
  true, and its plan adds the profile and its grant and changes nothing else. **Planned 2026-10-19 at
  05:24:48Z**, after Stage 17 1.3's two applies were read in AWS and with no lock on the state: 2 to
  add, 0 to change, 0 to destroy, the profile and its grant identical to the working-copy plan of
  04:21:59Z, saved as `stage18-governance-27.tfplan`. The apply is the user's; it takes decision 1's
  `enableSpaces` half and decision 3. A checkout without the switch-on code plans the profile's
  destruction, so PR #196 merges right after the apply. **The user's apply, 2026-10-19**, created
  the profile (05:47:08Z, `ENABLED`: `Tooling` `ON_CREATE` in Staging, the seven overrides,
  `enableSpaces` `false` locked) and was refused the grant: *"Group profile already exists for the
  given User profile"*. The role's ARN as a user resolves to one session's user profile, a member
  of the role's `IAM_ROLE_SESSION_GROUP` profile; the grant now names that group, its id read by
  `awscc_datazone_group_profile` from `<domain>|<role ARN>`. Re-planned at 05:52:00Z: 1 to add,
  the grant alone, saved as `stage18-governance-27b.tfplan`. **Applied 2026-10-19 by the user**,
  *"1 added, 0 changed, 0 destroyed"*, the grant created 05:58:00Z; the re-plan `No changes`
  (06:01:20Z); the outputs name the creators `InfrastructureAccess (staging)` and
  `sso-group-data-scientists`, and `./aws/studio.py`'s `US-4` reads `deployment` in this stage's
  window. PR #196 merged at 06:00:44Z.

### 3. The project

- **3.1 — [Claude⚡] Create `deploy-staging`** from `deployment`, as decision 3 picks: `datazone
  create-project` as `awsds-infra-staging`, then `list-project-memberships` read back, the creating role
  its only member. **Done 2026-10-19 at 06:05:28Z**, the call allowed to Claude where the applies were
  not: the project created by the IAM user profile of the infrastructure user's session, its one member
  Staging's InfrastructureAccess session group as `PROJECT_OWNER`. The CLI's newer options,
  `--project-execution-role`, `--resource-tags` and `--membership-assignments`, were left out: the
  measurement is AWS's default shape.
- **3.2 — [Claude] Read whether it provisioned** (i, v): the environment's status and, on a failure, the
  refused call and the policy its wording names. An environment that fails pins its configuration
  (Lesson 39), so a failure here goes to pass 8, which deletes the project before the configuration.
  **Read 2026-10-19**: the stack `CREATE_COMPLETE` at 06:06:38Z, 55 s after it began; the project
  `SUCCESSFUL` and `Tooling` `ACTIVE` by 06:07:27Z. Its parameters read `enableSpaces` `false`, so the
  profile's override of a parameter the blueprint locks reached the deploy. Every refused call was
  the provisioning role's or the project role's own IAM (*"no identity-based policy allows"*): probes
  before a create, a first `CreateSecurityGroup` that its retry passed, and the project role's
  `s3:CreateAccessGrantsLocation` in an account with no Access Grants instance. None came from the SCP
  or the boundary.
- **3.3 — [Claude] Read what the blueprint created** (ii): the environment's stack against 0.2's list;
  each role's trust, policies and boundary; the security groups and their rules; the buckets, prefixes
  and keys; Glue databases and Athena workgroups; Lake Formation's registrations, admins and opt-ins;
  the data sources and their schedules (`EXC-11`'s cron in Sandbox); RAM shares; and CloudTrail's
  `datazone.amazonaws.com` events in Staging grouped by principal, the list a carve-out by principal
  would name (decision 2). **Read 2026-10-19** (the log): the thirteen resources match 0.2's Sandbox
  list but the SageMaker AI domain; the provisioning role made the CloudFormation, EC2, Glue, Logs,
  Lake Formation, Scheduler, Athena and KMS calls, the DataZone service assumed the roles, and the one
  principal calling `datazone:` in Staging was InfrastructureAccess.

### 4. The deploy and the run (D28, D41)

- **4.1 — [Claude] Add a `staging` stage** to `app-etl`'s manifest on a measurement branch: the domain,
  `deploy-staging`, Staging's stage variables (`SUBNET_AZ1`, `SUBNET_AZ2`, `PROJECT_SG` and
  `PROJECT_KEY_ARN` from the Staging project, `JOB_IMAGE_URI` by digest), the `workflow.create` action,
  no `workflow.run`. **Written 2026-10-19** on `awsds/app-etl`'s branch `stage-18-staging`, cut from
  `main` at `v0.2.0`: the stage `STAGING`, its variables named `STAGING_*` apart from the Sandbox
  stages', `workflow.create` alone.
- **4.2 — [Claude⚡] Deploy from the laptop** as `awsds-infra-staging`: `deploy --targets staging` with
  the release's bundle, `--skip-validation --no-events` (D41's flags). Read what it wrote: the objects
  under the project's storage, the workflow by its composed name, `manual_only`, its execution role (the
  project role, D41 item 4), its network and key (v), its log group and retention, its tags, its
  versions (each deploy spent one on 2026-10-16, of a workflow's 50), and whether the Glue job was
  created by the operator rather than declared (D41 item 9). CloudTrail's list of the deploy's calls is
  the input of 4.3. **Done 2026-10-19** (the log). With `--bundle-archive-path` from a checkout of the
  branch, the CLI 1.0.9 wrote the checkout's files and none of the bundle's, then stopped at
  `workflow.create` on the `code/app-etl.zip` the checkout lacks: a `content.storage` item naming no
  connection is read from the manifest's folder whenever a manifest is given (`commands/deploy.py`). From
  `v0.2.1`'s bundle extracted, the branch's manifest beside it, the deploy wrote the seven files and
  created `app_etl_deploy_staging_app_etl`: `manual_only`, one version, the project role, network and key,
  its log group with no retention, the tag `STAGE=STAGING`, and no Glue job. CloudTrail holds 174 calls by
  InfrastructureAccess: 150 DataZone reads, `airflow-serverless:CreateWorkflow`, `GetWorkflow` and
  `TagResource`, `logs:CreateLogGroup`, and twelve KMS calls on the project key made by MWAA Serverless
  (`CreateGrant`, `GenerateDataKey`, `Decrypt`), S3 (`GenerateDataKey`, `Decrypt`) and Logs (`DescribeKey`)
  under the caller's session, with `cloudformation:DescribeStacks` and `datazone:GetGroupProfile` refused,
  both benign.
- **4.3 — [pipeline] The same deploy as `awsds-deploy-staging`** (decision 4): the role made an owner
  of `deploy-staging` first, since DataZone refuses a non-member's reads (`EXC-17`'s refusal); the
  actions 4.2's list adds to the role, written in `staging/foundation/` and applied as
  `awsds-infra-staging`; the job on a measurement branch the user protects in `awsds/app-etl` for the
  window, since the deploy runner takes protected refs only (Lesson 67 is the cost: protecting the
  branch extends the runner to it). `awsds-deploy-staging` holds `datazone:GetEnvironment`,
  `ListEnvironmentBlueprints`, `ListEnvironments` and `ListConnections` before its first deploy: without
  them the CLI 1.0.9 creates the workflow in the service's default worker network under a service-managed
  key and prints one line, and MWAA Serverless offers no condition key an SCP could require a network
  with (the CLI's code, read 2026-10-18, PR #189). **Prepared 2026-10-20**: the amendment, three inline
  documents in `staging/foundation/deploy-role.tf`, applied by the user 2026-10-20 (3 added, re-plan `No changes`); the
  job `stage-18-deploy` on the branch, below, committed as `caf1ff6` and `6a23b4d` in the laptop's clone
  and pushed at the next GitLab sitting. The branch's `test` fails the workflow lint since 7.1, the
  workflow naming `ACCOUNT_ID`, which only the staging stage defines, and a failed stage skips every
  later job, manual ones included, so the job carries `needs: []` (the checklist session's reading of
  2026-10-20, the lint reproduced here). `ECR_REGISTRY`, which the job reads beside `DOMAIN_ID` and
  `DOMAIN_REGION`, is the protected project variable Stage 8's job 193 added, read in GitLab before the
  run. The role has no group profile in the domain yet, so its first run is refused as a non-member and
  creates one, and the membership by group id follows, as in Sandbox.
- **4.4 — [Claude⚡] Run it** (ix), once the Prerequisites' Stage 8 3.0 half and `vpc-v0.4.0` are
  applied (both 2026-10-19): the sample input placed, then `run --targets staging --workflow` from the laptop, and `start-workflow-run` as the deploy identity; `get-workflow-run` to the end; the
  tasks' identity, subnets and endpoints read from CloudTrail and the logs. **The first run, 2026-10-19**
  (`7MMhwSySe5SOWd1`, the log): the deploy had placed the sample in `inbox/`; the worker came up in
  Staging's AZ1 private subnet with the project's security group, past the environment preparation
  `vpc-v0.4.0` admits, and `transform` was refused `glue:GetJob` to the project role through Staging's `glue`
  endpoint, *"because no identity-based policy allows the glue:GetJob action"*; the three later tasks never
  ran. The role carries the blueprint's three managed policies and none of `sandbox/workflows/`'s grant,
  which every Sandbox project role holds ([serverless-workflows.md](../runbooks/serverless-workflows.md)
  §G), so `staging/studio/workflows.tf` attaches the same three statements as `awsds-staging-workflows`
  for the stage's life. **The second run, 2026-10-19** (`JSSr2Br9Zsf2b26`, `SUCCESS`, 808 s), after the
  user's apply: the operators created the Glue job `app-etl-<project id>` with the project tag and the
  processing job `app-etl-20261019T205205` on `ml.t3.medium`, Staging's first, which no statement of the
  `Workloads` document refused; `report.json` reads the sample's ten rows. The worker's calls left
  Staging's AZ1 private subnet through its `glue`, `sagemaker.api`, `kms` and `logs` endpoints; the Glue and
  SageMaker sessions of the same role called from AWS's own addresses. The run created three log groups
  with no retention and SageMaker lineage entities (8.1). `start-workflow-run` as the deploy identity
  waits on 4.3 (decision 4).
- **4.5 — [Claude] Read the deploy against Stage 10** (iii): one row per Stage 10 step, done by the CLI
  or not, with what replaces it: 1.1 (`awscc_mwaaserverless_workflow` against `workflow.create`, which
  leaves the workflow outside Terraform's state), 1.2 (the network), 1.3 (the project role against D28's
  per-workflow role), 2.4 (the definitions home against the project's storage), 4.2 (the API rung the
  CLI is), 3.1 to 3.7 (the failure rule and the chain layer, which nothing in the CLI builds) and
  Stage 8's manual gate. **Done 2026-10-19**, from 4.2, 4.4, pass 5 and 7.1's measurements: the table
  below. 4.3's half, the same deploy as `awsds-deploy-staging`, waits on decision 4.

#### Stage 10's steps against the CLI's deploy

| Stage 10 step | What D41's design builds | What the CLI's deploy into `deploy-staging` did (2026-10-19) | Verdict |
|---|---|---|---|
| 1.1, the workflow resource | `awscc_mwaaserverless_workflow` per application, its definition and code pinned by S3 version, the execution role, a log group `/awsds/<env>/wf/<app>` at 90 days, in Terraform's state | `workflow.create` called `CreateWorkflow`, then `UpdateWorkflow` at each redeploy (versions 1 to 3), with the project key; the log group `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, no retention; a new `operatorFiles/<workflow>-<ms>.zip` per deploy, never pruned | Done outside Terraform's state, with a log group that never expires (`EXC-10`'s shape); `destroy`'s plan, read from the manifest and the service, stands where a Terraform plan would |
| 1.2, the network | `network_configuration` always, the two private subnets, the endpoint set | The CLI read the project's two subnets, security group and key from the `Tooling` environment and set them; the worker called through Staging's `glue`, `sagemaker.api`, `kms` and `logs` endpoints | Done by the CLI, from the project; the deploy role needs 4.3's DataZone reads for it |
| 1.3, the execution role | `awsds-<env>-wf-<app>`, enumerated permissions, `awsds-<env>-app-boundary`; the jobs under `awsds-<env>-job-exec` (D28) | The project role is every workflow's execution role and the Glue and processing jobs' role, carrying AWS's three managed policies and, added here, `sandbox/workflows/`'s grant, without which the first run was refused `glue:GetJob` | Not D28: one role per project, its permissions AWS's to change (Lesson 72), shared by every application in the project; no per-workflow role exists in this shape |
| 2.4, the definitions home | the rendered YAML and code under `workflows/<app>/<tag>/` of the account's outputs bucket, their `VersionId`s pinned, read back against the release's manifest | The files land under the project's `shared/<targetDirectory>/`, resolved in place at each deploy; no tag in the path, no version pinned; the lookups scan the whole `shared/` root, so an application sharing a workflow name or DAG id takes the other's file (5.2) | Partly: a home with no release in its path and no isolation between applications; the bundle's SHA256 is Stage 8's `store-bundle`, and a stored bundle deploys only extracted beside a manifest (4.2) |
| 4.2, the API rung | `CreateWorkflow` and `UpdateWorkflow` from the release job, a workflow outside Terraform's state | The CLI is that rung: `CreateWorkflow`, then `UpdateWorkflow`, the service calling `kms:CreateGrant` and `GenerateDataKey` on the project key and `logs:DescribeLogGroups` in the caller's session | Done, with DataZone reads Stage 10's rung does not need |
| D41 item 9, the Glue job | declared by the application slice in Staging and Production; the role holds no `glue:CreateJob` | Created by the operator at the first run, tagged with the project, its settings updated at each run (`update_config`), 7.1's included | Not item 9's Staging and Production form: the operator owns the job, as in `dev` and `test` |
| 3.1, the failure rule | an EventBridge rule on `aws.airflow-serverless` failures to the alerts topic | nothing | To build either way |
| 3.2, the diagnosis path | the service's APIs and the log group | The same APIs read 4.4's two runs (`get-task-instance`, its `LogStream`, the log group under the project key) | The same either way |
| 3.3, lineage | decision 9, Production's lineage | The Glue job posts its own events as the project role, through a `datazone` endpoint in the VPC (7.1) | Available in the project shape; Production needs the endpoint and a way past `DenyDataZoneEntirely` |
| 3.4 to 3.7, the chain layer | a state machine and a schedule per chain, the chain roles, the chain's failure rule | nothing: `run` starts one workflow and returns (ix); a non-member starts the workflow by IAM alone, with `kms:GenerateDataKey` and `Decrypt` on the workflow's key (0.4, vii) | To build either way; the chain role takes KMS on the project key, the workflow's key |
| Stage 8 3.5, the production gate | a blocking manual job before the Production leg | nothing: `deploy --targets <stage>` deploys the stage it is named | The pipeline's job either way |

#### The job `stage-18-deploy`

4.3's job goes into `stage-18-staging`'s `.gitlab-ci.yml` between `test-deploy` and `store-bundle`'s
comment. GitLab holds the branch at `6eb795c`, pushed at 7.1; the laptop's clone `$HOME/tmp/app-etl-check`
holds the job as `caf1ff6` and `6a23b4d`, two commits ahead, and fetches `main` alone, so it shows no
upstream for the branch. A session without that clone clones `awsds/app-etl`, switches to
`stage-18-staging`, inserts the block there, commits and pushes. The block is the two commits'
addition, byte for byte.

```yaml
# Stage 18 step 4.3, on this measurement branch alone: v0.2.1's stored bundle deployed into Staging's
# deployment project as awsds-deploy-staging, with this branch's manifest and workflow beside it, then
# run once as the same role (4.4's second half). The deploy runner takes protected refs only, so the
# branch is protected for Stage 18's window; the job is manual. The bundle is read with the runner's own
# role (decision 20); the account, the subnets, the project's security group and its key are read at run
# time, so no account-specific value sits here or in a CI/CD variable. A deploy that names no network
# from the Tooling environment stops: without it the workflow lands in the service's own network.
stage-18-deploy:
  stage: deploy
  # Started apart from the test stage: the workflow lint fails this branch, whose workflow names
  # ACCOUNT_ID, a staging value alone (7.1), and a failed stage skips every later job, manual ones
  # included.
  needs: []
  tags: [awsds-deploy]
  resource_group: app-etl-staging
  timeout: 45m
  rules:
    - if: $CI_COMMIT_BRANCH == "stage-18-staging"
      when: manual
  variables:
    BUNDLE_OBJECT: s3://awsds-prod-releases/app-etl/v0.2.1/app-etl.zip
    BUNDLE_SHA256: 7fb374d15c23953cb6ad6d9f5473f97d2c83ff2db167703a5a830d96add95fff
    IMAGE_DIGEST: sha256:247ec6b661ceb03d2927e1ce5a3c07d9287280a639abed18ce8daf898ed4ce0c
    STAGING_PROJECT_NAME: deploy-staging
  script:
    - |
      set -eu
      for name in DOMAIN_ID DOMAIN_REGION ECR_REGISTRY; do
        eval "value=\${$name:-}"
        if [ -z "$value" ]; then echo "FATAL: the CI/CD variable $name is not set"; exit 1; fi
      done
      export STAGING_PROJECT_NAME
      export JOB_IMAGE_URI="$ECR_REGISTRY/$IMAGE_REPO@$IMAGE_DIGEST"
      echo "== the bundle, read with the runner's own role"
      AWS_PROFILE=awsds-prod-runner-deploy aws s3 cp "$BUNDLE_OBJECT" bundle.zip
      echo "$BUNDLE_SHA256  bundle.zip" | sha256sum -c -
      mkdir extracted
      python3 -m zipfile -e bundle.zip extracted
      cp manifest.yaml extracted/manifest.yaml
      cp workflows/app-etl.yaml extracted/workflows/app-etl.yaml
      export AWS_PROFILE=awsds-deploy-staging
      echo "== who deploys"
      aws sts get-caller-identity --query Arn --output text
      echo "== Staging's values, read at run time"
      STAGING_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
      STAGING_SUBNET_AZ1="$(aws ec2 describe-subnets --filters 'Name=tag:Name,Values=awsds-staging-private-*-az1' --query 'Subnets[0].SubnetId' --output text)"
      STAGING_SUBNET_AZ2="$(aws ec2 describe-subnets --filters 'Name=tag:Name,Values=awsds-staging-private-*-az2' --query 'Subnets[0].SubnetId' --output text)"
      project_id="$(aws datazone list-projects --domain-identifier "$DOMAIN_ID" --name "$STAGING_PROJECT_NAME" --query 'items[0].id' --output text)"
      STAGING_PROJECT_SG="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=datazone-$project_id-dev" --query 'SecurityGroups[0].GroupId' --output text)"
      STAGING_PROJECT_KEY_ARN="$(aws kms describe-key --key-id alias/awsds-staging-project --query KeyMetadata.Arn --output text)"
      for name in STAGING_SUBNET_AZ1 STAGING_SUBNET_AZ2 STAGING_PROJECT_SG STAGING_PROJECT_KEY_ARN; do
        eval "value=\${$name}"
        case "$value" in ""|None) echo "FATAL: $name could not be read"; exit 1;; esac
      done
      export STAGING_ACCOUNT_ID STAGING_SUBNET_AZ1 STAGING_SUBNET_AZ2 STAGING_PROJECT_SG STAGING_PROJECT_KEY_ARN
      echo "project $project_id, subnets $STAGING_SUBNET_AZ1 $STAGING_SUBNET_AZ2, security group $STAGING_PROJECT_SG"
      cd extracted
      echo "== deploy to staging, as awsds-deploy-staging"
      rc=0
      aws-smus-cicd-cli deploy --manifest manifest.yaml --targets staging --skip-validation --no-events > ../deploy.log 2>&1 || rc=$?
      cat ../deploy.log
      if [ "$rc" -ne 0 ]; then echo "FATAL: the deploy failed"; exit "$rc"; fi
      if ! grep -q "Tooling VPC config" ../deploy.log; then echo "FATAL: the deploy named no network from the Tooling environment"; exit 1; fi
      echo "== run, as awsds-deploy-staging"
      aws-smus-cicd-cli run --workflow app-etl --targets staging --manifest manifest.yaml > ../run.log 2>&1
      cat ../run.log
      arn="$(sed -n 's/.*ARN: \(arn:[^ ]*\).*/\1/p' ../run.log | tail -1)"
      run_id="$(sed -n 's/.*Run ID: \([^ ]*\).*/\1/p' ../run.log | tail -1)"
      if [ -z "$arn" ] || [ -z "$run_id" ]; then echo "FATAL: run.log names no workflow ARN or run id"; exit 1; fi
      for i in $(seq 1 80); do
        state="$(aws mwaa-serverless get-workflow-run --workflow-arn "$arn" --run-id "$run_id" --query 'RunDetail.RunState' --output text)"
        echo "$(date -u +%H:%M:%SZ) $state"
        case "$state" in SUCCESS|FAILED|TIMEOUT|STOPPED) break;; esac
        sleep 30
      done
      aws mwaa-serverless get-workflow-run --workflow-arn "$arn" --run-id "$run_id" --output json > ../run.json
      cat ../run.json
      grep -q '"RunState": "SUCCESS"' ../run.json
  artifacts:
    when: always
    paths: [deploy.log, run.log, run.json]
    expire_in: 90 days
```

### 5. Several applications in one project

- **5.1 — [Claude⚡] Deploy a second application into `deploy-staging`**: an awsds-workflows example
  with a Python task (`demo-python-operator`), its manifest's `staging` stage naming the same project,
  its DAG id and its prefix distinct from `app-etl`'s, its bundle in a folder of its own (0.1). Read
  the two workflows' names, the two prefixes, the tags, and whether either deploy changed the other's
  files. **Done 2026-10-19** (the log): `orchestration-demo`, bundled into its own folder and deployed
  from the extracted bundle, created `orchestration_demo_deploy_staging_demo_python_operator` under
  `orchestration-demo/python/`, its tag `Pipeline=orchestration-demo`, and changed none of `app-etl`'s files
  or its workflow.
- **5.2 — [Claude⚡] The shared DAG id**: a copy of the second application whose workflow reuses
  `app-etl`'s DAG id, deployed once; read whether `workflow.create` took or rewrote `app-etl`'s file,
  0.1's inference, then `app-etl` redeployed from its bundle and its workflow read back. **Done
  2026-10-19**: the copy, `dagid-copy`, its workflow named `app-etl` with `dag_id: app-etl`, read and
  rewrote `app-etl/workflows/app-etl.yaml` (a byte-identical new version) and was created from `app-etl`'s
  definition; the scan covers the whole shared root, since it reads `target_directory` where the manifest's
  model carries `targetDirectory`, and `app-etl/` lists before `dagid-copy/`. `app-etl`'s redeploy read
  its own file, first in the listing, and took version 2.
- **5.3 — [Claude⚡] Remove the second one**: `destroy --targets staging` on its manifest, which says
  `project.create: false` and declares `deployment_configuration.catalog` only with `disable: true`:
  `destroy` deletes every catalog object the project owns, manual ones included, when a stage declares
  the catalog without `disable: true`, and the whole project with `create: true` (0.1). Read that
  `app-etl`'s workflow, runs, files and catalog survive, and list what `destroy` left behind (the
  `operatorFiles/` copies, the log group). **Done 2026-10-19 for `orchestration-demo`**: its plan held its
  workflow and its two prefixes, and `--force` deleted those three, the catalog skipped by `disable:
  true`; `app-etl`'s workflow, runs, Glue job and files survived, and the project owns no catalog object.
  It left its `operatorFiles/` copy and its log group. **`dagid-copy`'s plan holds `app-etl`'s Glue job**,
  read from the copy's definition, so its destroy was not run: decision 8 removed the copy's workflow and
  its `dagid-copy/` prefix by direct calls (21:34Z), `app-etl`'s workflow and Glue job intact, the copy's
  `operatorFiles/` copy and log group left as `destroy` would leave them.
- **5.4 — [Claude reads, user decides] One project per application** (decision 6): the quotas AWS
  publishes, read 2026-10-17, are 1,000 projects and 1,000 environments per account and Region in
  SageMaker Unified Studio (*"the depletion of resource quotas in one project can affect all other
  projects within the account"*) and 1,000 environments per DataZone domain; MWAA Serverless allows
  100 workflows and 50 versions of each per account and Region, which every application spends
  whatever the project count. Read Staging's values in Service Quotas, and what a second project costs
  at rest and adds to question ii's list; a second project is created only on the user's word. **Read
  2026-10-18** (the log): Staging's DataZone and MWAA Serverless quotas are AWS's defaults, the same as
  Sandbox's (`Environments in a domain` 1,000; 100 workflows, 50 versions each, 100 concurrent runs,
  76,800 MB of code storage), and Service Quotas lists no project quota. SageMaker's `Total domains`
  reads 10 in Staging and 500 in Sandbox against a default of 2, neither requested, so a `Tooling`
  base, one SageMaker AI domain per project (0.2), admits ten projects in Staging. What a second
  project costs at rest waits on 3.3's list. **Answered 2026-10-19 by reading** (decision 6): the
  `deployment` profile creates no SageMaker AI domain (question i), so the ten-domain quota does not bound
  it and 1,000 environments per domain does; each project adds 3.3's thirteen stack resources, of which
  only the log group's storage bills at rest; and its own `shared/` prefix and its own role, both named
  by the project id, so one project per application removes pass 5's collision by construction and
  gives each application a role of its own, the nearest this shape comes to D28's per-workflow role.
  **Unmeasured, by decision**: whether a second project's provisioning rewrites Staging's Lake Formation
  admins, which the first set (OQ 24) through `PutDataLakeSettings`, a full-replace API (Lesson 60); it
  matters once Stage 9's `staging/data/` declares admins of its own.

### 6. A person in the project (D18)

- **6.1 — [user] Add the data scientist with the narrowest designation the API offers** (iv, xi), sign
  in to the portal as that person and read what the project shows (the workflows, a run and its logs,
  the editor, the run button); try each write and read its refusal in CloudTrail. Then try, as the same
  person, to create a project from `deployment`, to add a member and to take ownership, which the domain
  unit's policies govern (`ADD_TO_PROJECT_MEMBER_POOL` is open to every user, read at Stage 6f). **Inputs
  read 2026-10-20** (the log): the narrowest designation is `PROJECT_CATALOG_VIEWER`; the root domain unit
  grants `CREATE_PROJECT_FROM_PROJECT_PROFILE` for `deployment` to Staging's InfrastructureAccess session
  group alone and `OVERRIDE_PROJECT_OWNERS` to nobody, so the person is expected to be refused the
  project and the ownership, and as a viewer the member, the project's owner being the gate rather than
  the pool. The person signs in from a separate browser profile: a CLI login answered in a browser
  holding a portal session ends that session. When 6.1 runs is decision 9.
- **6.2 — [Claude reads, user decides] The boundary on the project role** (vi), only if 6.1 shows a
  person's write landing: read the session's name and context keys of a portal action against a
  worker's task (6h read the portal's session as `<user id>@<env id>` and a space's as `SageMaker`); a
  deny conditioned on the person's session is written in `staging/studio/` and re-read on both sides
  only if a key separates them.

### 7. Lineage and the catalog (D26)

- **7.1 — [Claude⚡] Lineage from a Staging Glue job** (x): `app-etl`'s Glue task with Glue 5.0's
  OpenLineage configuration naming the domain, its role holding `datazone:PostLineageEvent`; the
  domain's `list-lineage-events` read twice with a delay (Stage 10 verification xix's form), then the
  portal's graph. **Done 2026-10-19** (the log): the job is Glue 6.0 and the role already held
  `datazone:PostLineageEvent` through `SageMakerStudioProjectUserRolePolicy` v75, so the settings went into
  `app-etl`'s branch alone (`6eb795c`). Run A, with no endpoint: the job succeeded and every post failed
  *"Network is unreachable"*, no event and no CloudTrail call in either account. `staging/egress/` then
  gained `datazone`, by the user's `make up`. Run B: 12 events `SUCCESS`, posted by the project role's IAM
  profile, S3 dataset nodes and job-run nodes the domain links, and no graph in the portal, since no
  node is an asset. CloudTrail read each post as `PostLineageEvent` by the role's `GlueJobRunnerSession`
  through the new endpoint, and the 12 events again after a delay. The branch's workflow lint fails
  since `6eb795c` (2026-10-20): the workflow names `ACCOUNT_ID`, which only the staging stage defines,
  and the lint wants every variable a workflow names in every stage, so an application posting its
  lineage defines the account in each stage.
- **7.2 — [user + Claude reads] A subscription across accounts** (x, decision 5): the Staging project
  publishes the Glue task's output table, sample data; the Sandbox project subscribes and the Staging
  owner approves; read the grants DataZone writes in each account and through RAM (INT-23's claim), and
  whether a Sandbox notebook reads the table. Revoked at 8.1. AWS's pages, read 2026-10-17, set the
  publishing side's terms: the table Lake Formation-managed, its location registered in Lake Formation
  or hybrid mode with no `IAMAllowedPrincipals`, the publishing project's role holding `DESCRIBE` and
  `SELECT` with the grant option, and no LF-TBAC; the subscriber gets `SELECT`, and a resource link
  cannot be subscribed to, so the Sandbox project cannot republish what it receives. Every path those
  pages document for publishing a table puts a project in the table's account, which is what makes
  this step a question for the verdict. **The path, 2026-10-20**: Staging held no Glue database and its Lake
  Formation admins were the two SMUS roles alone, with Lake Formation-only defaults, so no principal this
  repository writes could create the table; the user chose path A, `DataLake` (the console's Lakehouse
  Database) in Staging and in the `deployment` profile, on demand, whose environment has the provisioning
  role, a Lake Formation admin, create the project's database and its grants. Its order: `staging/studio/`
  applied (2 to add, planned), then `governance/` (1 to change, planned), then the environment created in
  `deploy-staging`, then the Glue task writing its output as a table there, the publication, the
  subscription and the approval. **The first environment failed** (`c2ej62w956q2a8`, 2026-10-20): the
  manage-access role was refused `lakeformation:CreateLakeFormationOptIn`, which
  `AmazonDataZoneSageMakerManageAccessRolePolicy`, the module's one attachment, does not grant, the refusal
  every Sandbox `DataLake` environment has met since 2026-09-13; `staging/studio/manage-access.tf`
  attaches `AmazonDataZoneGlueManageAccessRolePolicy` (the user's apply, 2026-10-20, after a first
  refused for the policy's `service-role/` path). **The second environment is `ACTIVE`**
  (`d6ogysnx78dguo`, 02:02:28Z): the database `glue_db_d6ogysnx78dguo` under the project's `dev/` scope,
  the project-conditioned grants and the manage-access role's grantable ones, the opt-in passing, a Glue
  data source on the database scheduled daily at 02:02 UTC, and Lake Formation's admins unchanged. The
  failed environment's database, `glue_db_c2ej62w956q2a8`, survived both deletions, an orphan for 8.1.
  **What is left needs a sitting**, the hub and Staging's egress up:
  1. **[Claude⚡] The table**: the Glue task writes its output as a table, `trades`, in
     `glue_db_d6ogysnx78dguo`, located under the database's `dev/data/catalogs/`, which the project role may
     do under the provisioning role's project-conditioned `CREATE_TABLE`; the job gains
     `--enable-glue-datacatalog`, and `transform.py` and the workflow change on the measurement branch,
     deployed from `v0.2.1`'s extracted bundle with the branch's files beside it. **Prepared 2026-10-20**
     by the checklist session: branch `stage-18-table` at `e14e910` in the clone `$HOME/tmp/app-etl-table`,
     cut from `caf1ff6` and not pushed, the change below. Its 16 tests and ruff pass and its lint fails
     as the branch's does, `TABLE_DATABASE` beside `ACCOUNT_ID` (read again here). The deploy exports
     `STAGING_TABLE_DATABASE`, the environment's `glueDBName`, which the 4.3 job does not read. A second
     run drops and recreates the table (`overwrite`, Spark's V1 path), and a grant on the dropped table
     goes with it [inferred]: after the subscription the task does not run again before the reads.
     Unmeasured: whether the job's `GlueJobRunnerSession` carries `context.datazone.projectId`, which
     the `CREATE_TABLE` grant is conditioned on; a refusal reads *"Insufficient Lake Formation
     permission(s)"* on `CreateTable`, after the CSV is written.
  2. **[Claude⚡] The asset**: a run of the project's Glue data source, `start-data-source-run`, since it
     publishes nothing on import (`publishOnImport` false) and its daily schedule fires at 02:02 UTC;
     then the asset published as the project's owner, Staging's InfrastructureAccess.
  3. **[user] The subscription**: from `test-experimentation`, whose `DataLake` environment
     `test-experimentation-lakehouse` is `ACTIVE` since 2026-10-20 (created after
     `sagemaker-prereqs-v0.8.0`, PR #207) and is the subscription target on that side; Staging's
     environment carries `deploy-staging-lakehouse-default-target` for `GlueTableAssetType` and
     `GlueViewAssetType`. **[Claude⚡]** The approval, `accept-subscription-request` as Staging's owner.
  4. **[Claude] The reads**: the Lake Formation grants DataZone writes in Staging and in Sandbox, the RAM
     share, the resource link in Sandbox's database, the writing role of each (INT-23's claim); then
     **[user]** a Sandbox notebook in a space reads the table.
- **7.3 — [Claude] Redshift is read, not measured**: Staging has no warehouse, and a Sandbox project
  reading a governed Redshift table is INT-24, Stage 9 step 9.7's. AWS's pages, read 2026-10-17: a
  subscription to a Redshift asset across accounts adds a datashare that the producer side authorizes
  and the consumer side associates, with both accounts associated, both warehouses encrypted and RA3
  or Serverless, and the subscribed tables appear as views in the consumer's warehouse; a direct
  datashare, with no DataZone, gives a database of `SELECT` only. The pages name no Lake Formation step
  on either path, the property INT-24's shapes are measured by.

#### 7.2's table change

The checklist session's `stage-18-table` (`e14e910`) against `caf1ff6`. Saved to a file, the block
goes onto `stage-18-staging` with `git apply`, and the result equals `e14e910`'s tree (read
2026-10-20). Its blank context lines carry no leading space, which `git apply` accepts.

```diff
diff --git a/glue/transform.py b/glue/transform.py
index a9e7f9a..3f4628b 100644
--- a/glue/transform.py
+++ b/glue/transform.py
@@ -7,6 +7,11 @@ into the target's prefix, which the overwrite empties first, then copies the par
 target's key and deletes what Spark wrote, with the boto3 the Glue worker carries. A second run
 overwrites the one object, so the processing job that reads the prefix finds one file and names
 its outputs after it. Glue 6.0 runs it; the test runs it over doubles of awsglue, pyspark and boto3.
+
+A run that names --TABLE_DATABASE and --TABLE_NAME also writes the result as a Parquet table of the
+Glue Data Catalog, a managed table at the database's location, which needs the job's
+--enable-glue-datacatalog. Stage 18 step 7.2 names the Staging project's DataLake database; a run
+that names neither writes no table, and one naming only one of the two stops before reading.
 """

 from __future__ import annotations
@@ -45,7 +50,21 @@ def keep_one_file(target: str) -> None:
     s3.delete_objects(Bucket=bucket, Delete={"Objects": leftovers})


+TABLE_OPTIONS = ["TABLE_DATABASE", "TABLE_NAME"]
+
+
+def table_options(argv: list[str]) -> dict[str, str]:
+    """The table's database and name when the run names both; empty when it names neither."""
+    named = [name for name in TABLE_OPTIONS if f"--{name}" in argv]
+    if not named:
+        return {}
+    if named != TABLE_OPTIONS:
+        raise ValueError(f"--TABLE_DATABASE and --TABLE_NAME go together; the run names {named}")
+    return getResolvedOptions(argv, TABLE_OPTIONS)
+
+
 def main() -> None:
+    table = table_options(sys.argv)
     arguments = getResolvedOptions(sys.argv, ["SOURCE_PATH", "TARGET_PATH"])
     target = arguments["TARGET_PATH"]
     spark = SparkSession.builder.getOrCreate()
@@ -58,6 +77,10 @@ def main() -> None:
     )
     keep_one_file(target)
     print(f"wrote {target}")
+    if table:
+        name = f"{table['TABLE_DATABASE']}.{table['TABLE_NAME']}"
+        result.coalesce(1).write.mode("overwrite").format("parquet").saveAsTable(name)
+        print(f"wrote the table {name}")


 if __name__ == "__main__":
diff --git a/manifest.yaml b/manifest.yaml
index 03c64af..c8e4e63 100644
--- a/manifest.yaml
+++ b/manifest.yaml
@@ -125,6 +125,8 @@ stages:
       PROJECT_SG: ${STAGING_PROJECT_SG}
       PROJECT_KEY_ARN: ${STAGING_PROJECT_KEY_ARN}
       ACCOUNT_ID: ${STAGING_ACCOUNT_ID}
+      # Stage 18 step 7.2: the DataLake environment's glueDBName, which the Glue task writes `trades` to.
+      TABLE_DATABASE: ${STAGING_TABLE_DATABASE}
     bootstrap:
       actions:
         - type: workflow.create
diff --git a/tests/test_glue_script.py b/tests/test_glue_script.py
index d39bc93..4ec1e71 100644
--- a/tests/test_glue_script.py
+++ b/tests/test_glue_script.py
@@ -31,6 +31,7 @@ class FakeWriter:
         self.log = log
         self.options = {}
         self.save_mode = None
+        self.format_name = None

     def option(self, key, value):
         self.options[key] = value
@@ -40,9 +41,16 @@ class FakeWriter:
         self.save_mode = name
         return self

+    def format(self, name):
+        self.format_name = name
+        return self
+
     def csv(self, path):
         self.log["write"] = (path, self.options, self.save_mode)

+    def saveAsTable(self, name):
+        self.log["table"] = (name, self.format_name, self.save_mode)
+

 class FakeFrame:
     def __init__(self, log):
@@ -96,7 +104,7 @@ class FakeS3:
         self.deleted.append([item["Key"] for item in Delete["Objects"]])


-def run_script(monkeypatch, log, keys):
+def run_script(monkeypatch, log, keys, extra=()):
     """Run the script as Glue would, with its three libraries doubled; return the S3 double."""
     s3 = FakeS3(keys)

@@ -125,7 +133,7 @@ def run_script(monkeypatch, log, keys):
         "boto3": boto3,
     }.items():
         monkeypatch.setitem(sys.modules, name, module)
-    argv = ["transform.py", "--SOURCE_PATH", SOURCE, "--TARGET_PATH", TARGET]
+    argv = ["transform.py", "--SOURCE_PATH", SOURCE, "--TARGET_PATH", TARGET, *extra]
     monkeypatch.setattr(sys, "argv", argv)
     runpy.run_path(str(SCRIPT), run_name="__main__")
     return s3
@@ -140,9 +148,27 @@ def test_the_script_reads_transforms_and_writes_one_file(monkeypatch, capsys):
     assert log["write"] == ("s3://bucket/app-etl/work/glue/", {"header": True}, "overwrite")
     assert s3.copied == [(PART, "app-etl/work/glue/trades.csv")]
     assert s3.deleted == [[PART, "app-etl/work/glue/_SUCCESS"]]
+    assert "table" not in log
     assert capsys.readouterr().out == f"wrote {TARGET}\n"


+def test_the_script_writes_the_table_a_run_names(monkeypatch, capsys):
+    log = {}
+    table = ["--TABLE_DATABASE", "glue_db_example", "--TABLE_NAME", "trades"]
+    run_script(monkeypatch, log, [PART], table)
+    assert log["write"] == ("s3://bucket/app-etl/work/glue/", {"header": True}, "overwrite")
+    assert log["table"] == ("glue_db_example.trades", "parquet", "overwrite")
+    printed = capsys.readouterr().out
+    assert printed == f"wrote {TARGET}\nwrote the table glue_db_example.trades\n"
+
+
+def test_the_script_refuses_half_a_table(monkeypatch):
+    log = {}
+    with pytest.raises(ValueError, match="go together"):
+        run_script(monkeypatch, log, [PART], ["--TABLE_NAME", "trades"])
+    assert "read" not in log
+
+
 def test_the_script_refuses_more_than_one_part_file(monkeypatch):
     second = "app-etl/work/glue/part-00001-0f6a-c000.csv"
     with pytest.raises(RuntimeError, match="one part file expected"):
diff --git a/workflows/app-etl.yaml b/workflows/app-etl.yaml
index 4c4ae9f..3f33626 100644
--- a/workflows/app-etl.yaml
+++ b/workflows/app-etl.yaml
@@ -13,6 +13,10 @@ app-etl:
       script_args:
         "--SOURCE_PATH": "{proj.connection.default.s3_shared.s3Uri}app-etl/inbox/"
         "--TARGET_PATH": "{proj.connection.default.s3_shared.s3Uri}app-etl/work/glue/trades.csv"
+        # Stage 18 step 7.2: the result also as the table the Staging project publishes, in its
+        # DataLake environment's database, a stage variable.
+        "--TABLE_DATABASE": "{env.TABLE_DATABASE}"
+        "--TABLE_NAME": trades
       create_job_kwargs:
         Command:
           Name: glueetl
@@ -28,6 +32,8 @@ app-etl:
             - datazone-glue-network-connection-{env.SUBNET_AZ2}-{proj.id}-dev
         DefaultArguments:
           "--custom-logGroup-prefix": datazone-{proj.id}-dev
+          # Stage 18 step 7.2: the Glue Data Catalog as Spark's metastore, which the table needs.
+          "--enable-glue-datacatalog": "true"
           # Stage 18 step 7.1: the OpenLineage listener posting to the domain, the Spark settings
           # SageMaker Unified Studio documents for a Glue job; the account is a stage variable.
           "--conf": "spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener --conf spark.openlineage.transport.type=amazon_datazone_api --conf spark.openlineage.transport.domainId={domain.id} --conf spark.glue.accountId={env.ACCOUNT_ID} --conf spark.openlineage.facets.custom_environment_variables=[AWS_DEFAULT_REGION;GLUE_VERSION;GLUE_COMMAND_CRITERIA;GLUE_PYTHON_VERSION;] --conf spark.openlineage.columnLineage.datasetLineageEnabled=True --conf spark.glue.JOB_NAME=app-etl-{proj.id}"
```

### 8. The unwinding, then the verdict

The reverse of passes 1 to 3, in 6b pass 1's order, each step read back before the next.

- **8.1 — [Claude⚡] Remove what the project holds, then the project**: the subscription and the asset,
  the orphaned database `glue_db_c2ej62w956q2a8` of 7.2's failed environment, dropped by Staging's
  InfrastructureAccess once it joins the admins (it holds no Lake Formation permission there, and the
  two admins trust DataZone and, for the provisioning role, CloudFormation alone): a `PutDataLakeSettings`
  keeping the two SMUS roles and every other field, then `DROP` granted to itself on both databases
  (unmeasured; 8.6 empties the list),
  the applications, the workflows grant's attachment (`project_roles` emptied in `staging/studio/`, applied,
  so the stack deletes a role carrying only the policies it attached), the Glue job the operator created,
  the lineage entities SageMaker created for the three processing jobs (three trial components, one per
  job, the four artifacts they share and twelve associations, read 2026-10-20; the jobs themselves
  cannot be deleted), the Glue data source on the `DataLake` database, the
  project, whose deletion deletes its two environments' stacks; the stacks read gone; then
  `glue_db_d6ogysnx78dguo` dropped like the orphan, since the `DataLake` template keeps its database
  (`DeletionPolicy: Retain`, `lessons.md`), and both read by name (`get-database` answers Lake Formation's
  refusal for a database that exists, `EntityNotFoundException` for one that does not); then the S3
  Access Grants location for the project's prefix and the account's `default`
  instance, both created at the project's provisioning; 7.1's lineage events and nodes and the project
  role's `IAM` user profile, domain objects, read and recorded;
  the CLI's log groups and the run's (`/aws/sagemaker/ProcessingJobs`, `datazone-<project>-dev/error` and
  `/output`), which carry no retention, deleted or recorded under `EXC-10`'s shape.
- **8.2 — [Claude⚡] Remove the profile and the rows in one edit**: the `deployment` profile and its grant,
  the `SMUS_DEPLOYMENT_MEMBERS` row and the `SMUS_ASSOCIATED` row (6b step 1.6's rule: one list alone
  flips `profiles_enabled`), with the switch, the `staging` alias and its two data sources, and
  `./aws/studio.py`'s `WINDOW_PROFILE_NAMES`; `governance/` applied as `awsds-infra-data`, `experimentation`
  unchanged.
  The list itself stays, empty, until the verdict says whether a deployment account is ever a member.
- **8.3 — [Claude⚡] Destroy the blueprint configurations and their grants**, `Tooling`'s and `DataLake`'s,
  in `staging/studio/` as `awsds-infra-staging`, while the association exists: only the member deletes them.
- **8.4 — [user] Disassociate `Staging Account`**, the console path of 2.1 → Disassociate (6b step 1.4).
- **8.5 — [Claude] Read the association back**: `list-environment-blueprint-configurations` from Staging
  fails with `UnauthorizedException` (6b step 1.5), and RAM holds no DataZone share.
- **8.6 — [Claude⚡] Destroy the rest of `staging/studio/`**: the projects bucket listed with its versions
  and delete markers and emptied, the slice destroyed with the workflows policy and the Glue manage-access
  attachment in it, the folder and its `layers.py` row deleted, the project key's deletion date in the log;
  Staging's Lake Formation admins, the two SMUS roles since 3.3 and InfrastructureAccess since 8.1, emptied
  by `PutDataLakeSettings` carrying every other field as read (a full replace, Lesson 60):
  `CROSS_ACCOUNT_VERSION` 1 and `SET_CONTEXT` `TRUE`, both from before the stage, and the default lists
  empty, the state InfrastructureAccess's own call left on 2026-09-06 (6b's unwinding); then read back to
  0.3's empty list with those parameters.
- **8.7 — [Claude⚡] Restore the SCP**: the carve-out and the placeholder removed, `identity/org-policies/`
  applied, the battery's rows removed, and from `awsds-infra-staging` a `datazone list-domains` denied
  with the SCP's wording; the `EXC-nn` closed.
- **8.8 — [user + Claude] Close the repositories**: the measurement branches deleted unmerged, the
  protected branch unprotected, the deploy role's added actions removed and applied, and `datazone` taken
  out of `staging/egress/`'s `extra_services`.
- **8.9 — [Claude reads, user decides] The verdict** (decision 7): the answers to i to xi in the log;
  then D41 item 2 kept, with the measurements in place of the argument, or reopened, with Stage 10's
  steps 1.1, 2.4 and 4.2 rewritten around the CLI; `SMUS.md` gains what the blueprint creates in a
  deployment account; `POLICIES.md`'s revision trigger on `DenyDataZoneEntirely` names the result.

## Deliverables

- The log's answers to questions i to xi, each with its date and its reading.
- 4.5's table of Stage 10's steps against the CLI's deploy.
- 3.3's list of what the blueprint creates and which principals call `datazone:*` in a deployment
  account.
- The verdict on D41 item 2, as the user takes it at 8.9.
- An estate equal to 0.3's reading: no association, no profile, no project, no `staging/studio/`, the
  `Workloads` document as before.

## Validation

- `./aws/studio.py` green at 0.3 and at 8.5, with `US-6` back to `Workloads` denying `datazone` reads.
- The battery green at 1.3 and at 8.7.
- `data-governance/governance/`, `staging/foundation/`, `sandbox/foundation/` and `production/tooling/`
  re-planning `No changes` after 8.2 and 8.8.

## Cost

Rates measured in `us-west-2` (`docs/PRICING.md`): Staging's 12 endpoints, `datazone` among them since 7.1, at USD 0.120 an hour
while up, with the hub; MWAA Serverless at 0.088 per task-hour; Glue 6.0 and later at 0.308 per DPU-hour in `us-west-2` (offer of 2026-10-12; `app-etl`'s job is `GlueVersion: "6.0"`), 0.44 before; the DataZone domain's
metadata in cents per month. A project's environment holds no compute of its own unless the blueprint
starts one, which question ii reads. The stage's spend is read from Cost Explorer at 8.9, not estimated
(Lesson 6).

## Decisions due while executing

Each is decided during the stage and written into the stage log with its recommendation (Lesson 16).

1. **The base blueprint** (1.1, 2.4, 3.1). Recommended on 2026-10-17: `ToolingLite` first, then
   `Tooling` if it failed; **revised 2026-10-19 from the two templates: `Tooling`, with `enableSpaces`
   false and not editable in the `deployment` profile**. `ToolingLite` is category 3 as a second base on
   the eleven-blueprint profiles, and `SMUS.md` says it returns, if ever, as a profile of its own, which
   `deployment` is; its template (`ToolingLiteDefault-prod-20260723`, the log) creates
   `AWS::SageMaker::Domain` with no condition, creates no project role (`executionRoleArn` is a
   parameter), no log group and no Lake Formation registration, and exports the VPC, subnets, security
   group and key the CLI reads, so it needs the `CreateDomain` carve-out and brings less than `Tooling`.
   `Tooling`'s template (`ToolingDefault-prod-20260918`) creates the SageMaker AI domain only under
   `sageMakerDomainRequired`, `isDefaultTooling` and `enableSpaces == "true"`: with spaces off it
   creates the project role under the configuration's boundary, the log group, the security group, the
   Glue connections, the Lake Formation registration of the project prefix and the same four outputs,
   and calls no `CreateDomain`; with spaces on it needs the carve-out, and Staging's quota admits ten
   such domains (5.4). The blueprint marks `enableSpaces` not editable, as it marks
   `maxIdleTimeoutInMinutes`, which `experimentation` overrides and whose projects deploy; whether this
   override reaches the deploy is 3.2's first reading. **A custom Tooling blueprint is a third candidate since
   2026-10-09** (the upstream readings of 2026-10-18, PR #189): a CloudFormation template this repository
   writes, registered with `CreateEnvironmentBlueprint --blueprint-category TOOLING` (no CloudFormation
   type, so a hand object). The guide's minimum template for an Identity Center domain holds a bucket, a
   log group, the project role and the three default connections and no SageMaker AI domain, so question
   i needs no `CreateDomain` carve-out. The CLI 1.0.9 then takes a workflow's subnets, security group and
   key from the environment's `privateSubnets`, `securityGroup` and `kmsKeyArn`, so the template exposes
   them, or the workflow is created outside the VPC under a service-managed key. **Written to the
   recommendation on 2026-10-19**: `staging/studio/`'s `blueprint_names` and 2.6's `deployment` row;
   2.5's second apply takes the base and 2.7 the parameter, both by the user's hand. **Taken
   2026-10-19** by those two applies.
2. **The carve-out's form** (1.1). Recommended: **by account, for the stage's window**: which principals
   call `datazone:*` in a deployment account is what 3.3 measures, so a carve-out by principal cannot be
   written before it. A carve-out by principal is the form a permanent one would take, from 3.3's list.
   Moving Staging out of `Workloads` is refused: it would drop every job-settings deny with it.
3. **Who creates the project, and who owns it** (2.6, 3.1). Recommended: **`awsds-infra-staging`, with
   `datazone create-project`, and no manifest says `project.create: true`**. With `create: true` the
   CLI's `destroy` deletes the whole project (0.1), so removing one application could take the other's
   project with it, and AWS's rollback guide calls `create: false` the typical production setup. The
   profile's grant names that role, which owns the project for 4.2; `awsds-deploy-staging` joins as an
   owner before 4.3, and no person is a member before 6.1. The CLI creating it as the deploy role is
   the alternative: it measures the CLI's creation path and ties the project's life to a `destroy`.
   **Written to the recommendation on 2026-10-19**: 2.6's grant names Staging's InfrastructureAccess role,
   and 2.7 takes it. **Taken 2026-10-19** by 2.7's applies, the grant naming the role's
   session group.
4. **Whether 4.3 runs as `awsds-deploy-staging`** (4.3). Recommended: **yes**, since the variant under
   test is a project the pipeline deploys into with no person in it, and the actions the role gains are
   the price of adopting it. Its cost is a protected branch in `awsds/app-etl` for the window and an amendment of the
   deploy role, both removed at 8.8. **Taken 2026-10-19 by the user**, to the recommendation: 4.3 runs at
   the next GitLab sitting.
5. **Whether 7.2's subscription runs** (7.2). Recommended: **yes**, on sample data only: INT-23 is
   unexercised, and the user's third line asks whether a Sandbox project reads what a production project
   publishes. **Taken 2026-10-19 by the user**, to the recommendation: 7.2 runs, on sample data. Its path,
   taken 2026-10-20: `DataLake` in the `deployment` profile, the project's own database (path A).
6. **A second project for 5.4** (5.4). Recommended: **read only**: the role, the storage and the stack
   are per project by construction, and the quota and the cost are readings; the quotas were read
   2026-10-18, and the cost waits on 3.3. **Taken 2026-10-19 by the user**, to the recommendation: 5.4
   answered by reading, the Lake Formation admins left unmeasured.
7. **The verdict** (8.9). Taken by the user on the answers; recommended at 8.9 from them.
8. **How `dagid-copy` is removed** (5.3). Its `destroy` plan holds `app-etl`'s Glue job, read from the
   copy's definition, which is `app-etl`'s (5.2). Recommended: **the copy's workflow and its `dagid-copy/`
   prefix removed by direct calls**, `mwaa-serverless delete-workflow` and `s3 rm`, which reach nothing of
   `app-etl`'s: the plan already reads what `destroy` would delete, and running it would delete `app-etl`'s
   job and its run history to repeat that reading. The alternatives: the copy's `destroy`, then `app-etl`'s
   job read gone and recreated by its next run; or the copy kept to 8.1, which removes `app-etl`'s job
   anyway. **Taken 2026-10-19 by the user**, to the recommendation: the direct calls ran at 21:34Z.
9. **When 6.1 runs** (6.1). Recommended: **with the environment down, before 4.3**, as the checklist
   session proposed on 2026-10-20. 6.1 needs the portal and the control plane alone, both reached by
   identity (D39): the person sees the workflow and its four runs with their logs, and a run started
   from the portal fails at environment preparation with no endpoint up, CloudTrail's `StartWorkflowRun`
   answering the authorization question either way while one `FAILED` run joins the history. 6.1 ends
   with the person's membership deleted and read gone, since decisions 3 and 4 want 4.3 in a project
   with no person in it. Adding and deleting the membership are writes as the project's owner, the user's
   commands while the classifier refuses Claude a membership grant (Stage 8's log, *Permission Grant*).
   If 6.1 shows a write landing, 6.2 waits for a sitting with the environment up. The alternative is 6.1
   after 4.3, inside the next sitting: the person's run reaches a worker, and 6.2 is read in that sitting.

## Risks

- **`SMUS_MEMBERS` gaining Staging changes four things outside the domain** (2.3): the persona's vending
  policy in `staging/foundation/`, the GitLab security group's sources, Production's model-status
  readers, and refusal 8 on every Staging slice. 2.3 split the list on 2026-10-18, so Staging's row
  goes to `SMUS_DEPLOYMENT_MEMBERS`; nothing refuses a `staging` row in `SMUS_MEMBERS`, and the
  re-plans are what catch one.
- **The order of the two rows**: a deployment row before the `SMUS_ASSOCIATED` row flips
  `profiles_enabled` false and destroys `experimentation`, or fails on its projects; 2.7 and 8.2 read
  the plan's destroy count before applying.
- **An incomplete configuration pins its projects both ways** (Lesson 39): pass 8 deletes the project
  before the configuration, and the configuration before the association.
- **The carve-out admits every Staging principal to DataZone for the window.** IAM still grants nothing:
  `DataScientistStagingAccess` holds no `datazone:` action (read 2026-10-17 in
  `terraform-live/identity/sso/policies-data-scientists.tf`), and the deploy role gains only 4.3's
  actions. The `EXC-nn` and 8.7 bound the window.
- **The Lake Formation seat.** SMUS made itself a Lake Formation admin in Sandbox (open question 24); if
  the blueprint does the same in Staging, a `staging/data/` built while the project exists would be
  reachable by it. This stage runs before Stage 9 pass 5, 3.3 reads the admins, and 8.6 reads them back.
  **Measured 2026-10-19 at 3.3**: the provisioning role's three `PutDataLakeSettings` at 06:05:34Z set
  Staging's admins, an empty list until then, to itself and the manage-access role. 8.6 reads them
  back by hand, since `./aws/datalake.py` `DL-13` reads the lake's accounts alone.
  **Since 2026-10-20 the manage-access seat can act**: 7.2's `AmazonDataZoneGlueManageAccessRolePolicy`
  gives that role `GrantPermissions`, `RevokePermissions` and `RegisterResource` on `*`, where the
  SageMaker policy gave no `lakeformation:` action; the seat reaches Staging's catalog alone while
  `staging/data/` does not exist, and 8.6 removes the policy with the slice.
- **The `Workloads` document carries Stage 9 pass 1's job statements, attached since 2026-10-18 at
  19:54Z** (PR #144; the apply and its battery in Stage 9's log). An apply of `identity/org-policies/`
  attaches what `main` holds, so 1.1 edits `main`'s document, and 1.3's plan changes only
  `DenyDataZoneEntirely` and, if 1.1 split it, `CreateDomain`'s statement. The two stages never share an
  apply.
- **Residues**: the CLI's log groups carry no retention, the workflows' versions and run history leave
  with the project, and the project key waits out its deletion window.
