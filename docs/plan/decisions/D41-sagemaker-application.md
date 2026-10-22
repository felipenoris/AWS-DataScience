# D41 — The SageMaker application as the deployable unit: the CI/CD CLI between Sandbox projects, the pipeline from its bundle, and the scheduler layer above the workflows

**Status:** Decided (2026-10-15, user): the deployable unit is a SageMaker application, a repository
holding `manifest.yaml`, its workflows in the SageMaker Unified Studio CI/CD CLI's notation and its
code. The CLI deploys it from the repository into the `dev` project and the `test` project, both in
Sandbox, and makes the bundle; the pipeline deploys the bundle to Staging and Production, where one
Step Functions state machine per chain starts the workflows and one EventBridge Scheduler schedule
starts the machine, the shape of `terraform-reference/`'s `modules/orchestration/`. Amends
[D7](D07-orchestration.md), [D26](D26-unified-studio.md) and [D28](D28-workflow-contract.md) in place,
each with a dated line. The first CLI deploy into a project ran in the lab the same day.

**In one line:** the application is the unit, the CI/CD CLI carries it between the Sandbox projects
and bundles it, the pipeline deploys the bundle, and design B is built as the layer that schedules and
chains the workflows, not as a replacement for them.

**Related decisions:** [D7](D07-orchestration.md), [D17](D17-interactive-vs-runtime.md),
[D20](D20-staging-account.md), [D21](D21-development-account.md), [D26](D26-unified-studio.md),
[D28](D28-workflow-contract.md)

**Referenced by stages:** [Stage 8](../stages/stage-08-cicd-pipelines.md),
[Stage 10](../stages/stage-10-orchestration-promotion.md),
[Stage 18](../stages/stage-18-staging-deployment-project.md);
[6i](../stages/stage-06i-sandbox-orchestration.md) measured the Sandbox half it builds on

---

## What is revised, and what is not

Three decisions move and the rest of the plan stays. D26's amendment of 2026-09-05 called the CI/CD
CLI an exporter on the Sandbox side, and D7's of the same day left design B, EventBridge Scheduler
plus Step Functions, as INT-14's terminal fallback, documented and not built, with D28's class (4)
naming it only if the ladder fell through. Since 2026-10-15 the CLI is the deployer between the
Sandbox projects and the bundle's maker, and design B is the layer above the workflows: a state
machine starts a chain's workflows in order and a schedule starts the machine. What stays: the
workflow runs the tasks, MWAA Serverless only (D7); Staging and Production have no domain, no project
and no portal, and only the pipeline writes them (D17, D20, D26); the artifact classes, the
per-workflow execution role, the named log group and the promotion lint (D28); the `Workloads` SCP;
and Stage 10's steps 1, 3, 5 and 6, which gain the chain's pieces.

## The decision

The user took the items on 2026-10-15: 1 to 6 at 04:40 UTC, 7 and 8 at 05:29 UTC, 9 and 10 at
05:45 UTC, each as recommended but 7, confirmed the deploy mechanism of item 5 at 15:43 UTC, and
took item 1's `{env.VAR}`, in place of a `${VAR}` the CLI leaves as written, at 23:55 UTC.

1. **The application format.** An application is a repository holding `manifest.yaml`,
   `workflows/<name>.yaml` in the CLI's notation and the code its tasks run: `src/` and the
   `Dockerfile` for the processing task, `code/` for the worker's Python and Bash tasks, `glue/` for
   the Glue scripts (`docs/plan/conventions.md`, "Application repository layout"). The workflow's
   YAML names a project's values as the CLI's variables (`{proj.id}`, `{proj.iam_role_arn}`,
   `{proj.connection.default.s3_shared.s3Uri}`, `{domain.region}`) and a value no project holds as a
   stage variable, `{env.VAR}` (the image by digest, the job subnets, the data key), so one file serves
   every stage. The CLI writes an `{env.VAR}` as `{{ params.VAR }}` and fills it only in a run it starts,
   passing the stage's `environment_variables` as the run's `OverrideParameters`, and leaves a `${VAR}`
   in a workflow's YAML as written (its 1.0.9 code, read 2026-10-15; Stage 10 verification xxix).
   The awsds-workflows examples take the same form, one YAML per example, and its `render` learns
   the CLI's variables for an import into the portal without the CLI.
2. **Where production runs.** Without a project: the pipeline creates the workflow from the bundle,
   with the per-workflow role (D28), and a run is read by API, CloudWatch and EventBridge. The
   alternative, a project in Staging and in Production with the CLI deploying every stage, would
   associate the two accounts to the domain, provision the Tooling blueprint in each, carve
   `datazone:*` out of the `Workloads` SCP and make the project role the execution role. The user
   chose on 2026-10-17 to measure that alternative before Stage 10 builds this item, in Staging, with
   a project whose only member is the identity that deploys
   ([Stage 18](../stages/stage-18-staging-deployment-project.md)). **Kept by that verdict, the user's on
   2026-10-22.** The alternative works and was measured end to end in Staging: a `Tooling` project with
   spaces off, the CLI deploying and running from the pipeline, a subscription read across accounts.
   Its price falls on what this item protects: one role per project, which members' sessions assume and
   AWS's managed policies define, shared by the project's applications, in place of D28's per-workflow
   role; the workflow outside Terraform's state; `datazone:*` carved out of `Workloads`, the account
   associated and the SMUS roles seated as its Lake Formation admins; a subscription that shares the
   producer's whole catalog through RAM and a Data Catalog resource policy; and residues a teardown
   leaves (the stage's 8.9 and log). Keeping the workflow in Terraform's state rests on INT-14 (Stage 10
   1.1), whose last fallback rung is the CLI's own API form (4.2).
3. **The CLI's place.** It deploys from the `dev` project to the `test` project and makes the bundle
   the pipeline promotes: `deploy --targets dev` from the laptop or a space while the application is
   engineered, `bundle` and `deploy --targets test` in the application's pipeline on the release
   tag, once its image is built and before the Staging leg (Stage 8 step 2.5), the identity of those
   jobs its decision 19. `bundle` builds nothing, so the tag pipeline first builds what the
   application needs built (a task's code package, a compiled extension) into the folders the
   manifest includes, `bundle` and the `test` deploy read them in one job, and once `test` passes
   the tag's GitLab release links to the bundle, stored where Stage 8 decision 20 says: the file
   Staging and Production receive (proposed by the user at 22:06 UTC the same day).
4. **The execution role in the CLI's stages.** The project role, as the CLI does: the model AWS
   documents for `dev` and `test`; a role per workflow there would need a field the CLI lacks.
5. **The production scheduler.** EventBridge Scheduler with one Step Functions Standard state
   machine per chain, above the workflows, in the `orchestration/` slice the pipeline applies: the
   machine starts each workflow (`StartWorkflowRun`) and waits for its run (`GetWorkflowRun`), the
   schedule starts the machine, and a workflow in a chain is created `manual_only`. Confirmed at
   15:43 UTC as the shape of `terraform-reference/`'s `modules/orchestration/`, whose GitLab pipeline
   creates per stage the state machines and the schedules. The dependencies between workflows
   follow: inside a chain the order is the machine's; between chains, or on an event, an inbox
   prefix in S3 and an EventBridge rule that starts the machine. Stage 10 steps 3.4 to 3.7 build
   it; its four choices, Stage 10 decisions 13 to 16, the user took the same day at 16:28 UTC, as
   recommended.
6. **The lab first.** The CLI was measured with `houseprice-etl` between the two Sandbox projects
   before the examples and `app-etl` change shape (below).
7. **The task's image.** The application image carries the dependencies alone, built from the lock,
   and the code is the job's input in every stage: copied by the CLI in `dev` and `test`, written
   by the release job under the release's prefix in Staging and Production and kept from overwrite
   there (Stage 10 decision 12). One form of task, the iteration in a space, and the image changes
   only with the lock. This is Stage 10 decision 7's alternative, taken over its recommendation
   (the image carrying the code), because the build runner serves protected refs only (Stage 7
   step 3.5), so an image per iteration in `dev` has no builder.
8. **The job's role in a project.** The project role, as 6i measured, to confirm at the first
   measurement; the alternative is the slice's job role with `iam:PassRole` from the project role.
9. **The Glue job's owner.** In Staging and Production the application slice declares the job and
   the workflow only runs it, so the workflow's role holds no `glue:CreateJob` there (Stage 10
   decision 12, D28 class 2c); in `dev` and `test` the operator creates and updates it, with
   `update_config: true` and the whole `Command` in `create_job_kwargs` (user, 2026-10-16: no stage
   variable controls `update_config`, which is not a template field), and `sandbox/workflows/` grants
   the `glue:GetJob` on a name not yet taken that the blueprint's policy refuses (user, 2026-10-16).
10. **The result file.** The last task is an S3 operator task (`S3CopyObjectOperator` or
    `S3CreateObjectOperator`), the operator of the inbox contract between applications; the Python
    task stays light.

The application `app-etl` takes the scope the user set at 05:39 UTC: its own image, and a workflow in
four tasks, a Glue job that reads an input file from S3, transforms it in Spark through Python code
and writes the result, a processing task on the application image with the code as the job's input,
a light Python task on the worker, and the S3 operator task that writes the result file.

## What the lab measured on 2026-10-15

The CLI, `aws-smus-cicd-cli` 1.0.9, from the user's laptop as `InfrastructureAccess` in Sandbox, with
the awsds-workflows example `houseprice-etl` rendered for the `dev` project; every output is in the
Claude project's library, `laboratorio/leituras/2026-10-15-cli-houseprice-etl-dev.md`.

- `list-connections` answers `InfrastructureAccess` in both projects, and `describe --connect` lists
  each project's connections. `EXC-17` records three refusals of that call to the same identity, as
  a non-member of the project. Read 2026-10-18: the identity has been a contributor of both projects
  since 06:15 UTC on 2026-10-15, before the lab ran, a group profile whose role is Sandbox's `InfrastructureAccess`, added
  through the portal (`CreateProjectMembership` by the domain execution role in the domain account's
  CloudTrail).
- `deploy` copies the manifest's content (`aws s3 sync`, no `--delete`) and creates no workflow; the
  workflow is born by the `bootstrap` action `workflow.create`, which every stage that must show it
  needs. The action resolves the YAML's `{proj.*}` variables, writes the resolved copy at the same
  S3 key and calls `CreateWorkflow` with the project role, the Tooling environment's subnets,
  security group and CMK, the log group `/aws/mwaa-serverless/<domain>-<project>/<name>` with no
  retention, no `TriggerMode` and six tags (`AmazonDataZoneProject`, `AmazonDataZoneDomain`,
  `Target`, `CreatedBy=SMUS-CICD`, `STAGE`, `Pipeline`), by which `monitor` and `logs` filter
  `ListWorkflows`. The name is `<application>_<project>_<workflow>` with every character outside
  `[A-Za-z0-9_]` replaced by `_`, and `run --workflow` composes it the same way: a state machine
  that starts a workflow by name in `dev` or `test` needs that.
- The CLI's pre-deployment validation, the `--dry-run` engine, calls `iam:SimulatePrincipalPolicy`
  with no context keys, so every conditioned SCP reads denied here: the Region control without
  `aws:RequestedRegion`, `DenyS3ObjectWriteOutsideOrganization` without `aws:ResourceOrgID`. The
  deploy of 15:46 UTC aborted on it with nothing written; the same simulation with the keys the real
  call carries answers `allowed` on every action, and the simulation never covers a bucket policy or
  a key policy. The deploy runs with `--skip-validation` (Lesson 30: the tool's failure is not a
  property of the estate), and `--no-events` keeps its `PutEvents` off the `default` bus. Its boto3
  reads no credential the `aws` CLI cached: a fresh SSO login, or `aws configure
  export-credentials`, precedes it.
- The deploy of 15:52 UTC (exit 0, 15:52:43 to 15:54:17) put two objects under the project's
  `shared/exemplos/houseprice-etl/` and created `houseprice_etl_eighth_experimentation_houseprice_etl`,
  `READY`, `CUSTOMER_MANAGED_KEY` with the project's key, `TriggerMode` `manual_only`, the resolved
  YAML identical to the `WorkflowDefinition` the service returns (`job_name:
  houseprice-etl-<project>`, the two Glue `NETWORK` connections it names existing), with the
  settings of the portal-made `demo-bash-operator`. The project holds five workflows since, 6i's
  four and this one.
- The portal, read at 16:49 UTC with no save: the project's Workflows list shows it beside 6i's
  four, `Manual only` with no run; the editor draws its `run_glue_job` node; the Definition tab is
  read-only with `Errors: 0`; the Tags tab shows the six tags under a notice that tags are defined
  in the definition file, where the CLI never wrote them (it tagged by `TagResource`), so a save
  from the portal would drop them, a reading no save has measured. After the tab closed the
  service returned the same `WorkflowVersion` and `ModifiedAt`, and `dev/workflows/` held no copy.
- Read in the lab on 2026-10-16: `bundle` and the deploy to `test`, whose 158 CloudTrail events
  gave the actions the CLI's identity needs beyond AWS's example policy, which lists no
  `airflow-serverless` action ([Stage 8](../stages/stage-08-cicd-pipelines.md) decision 19).
- Still owed: `run`, `monitor` and `logs` with the Sandbox up and the input file in place; a Python or Bash task's `Code` through the CLI; the
  project role's pull of the application image; and the chain layer's readings (Stage 10
  verifications xxii to xxvi).

## The chain layer, against `terraform-reference/`

The reference Terraform (`sa-east-1`, its prefix written `<prefix>`) carries the shape, and the lab
takes it in the `orchestration/` slice of each deployment account, with the names Stage 10 fixes:

| `terraform-reference/`: `modules/orchestration/` and `modules/security/` | The lab: `<env>/orchestration/` |
|---|---|
| `aws_scheduler_schedule_group` `controladoria-schedules` | the group `awsds-<env>-chains` |
| `aws_cloudwatch_log_group` `/aws/vendedlogs/states/<prefix>-pipelines`, 90 days, KMS | `/aws/vendedlogs/states/awsds-<env>-chains`, 90 days, the account's data CMK |
| the role `<prefix>-step-functions` (trust `states.amazonaws.com`): EMR Serverless, Glue crawlers, SageMaker jobs, `sns:Publish`, `iam:PassRole`, logs, X-Ray | `awsds-<env>-chain-exec`: `airflow-serverless:StartWorkflowRun` and `GetWorkflowRun` on the account's workflows, and the log delivery; nothing on jobs. The reference's state machine chains jobs; here the workflow chains jobs (D28) and the machine chains workflows |
| the role `<prefix>-eventbridge-scheduler` (trust `scheduler.amazonaws.com`): `states:StartExecution` on `stateMachine:<prefix>-*` | `awsds-<env>-chain-scheduler`, the same form on `awsds-<env>-chain-*` |
| the role `gitlab_cicd`: `states:*`, `scheduler:*`, `events:*`, no `airflow-serverless` | `awsds-deploy-<env>` (Stage 8), the named actions of Stage 10 step 1.5 inside the boundary |
| the module's input `eventbridge_role_arn`, given `<prefix>-eventbridge-scheduler`, trusted by `scheduler.amazonaws.com` alone, so a bridge rule needs a second trust on it or a second role | `awsds-<env>-chain-events`, trusted by `events.amazonaws.com`, the same `states:StartExecution`: a second role, so that CloudTrail tells a start on an inbox write from a scheduled one (Stage 10 step 3.6) |
| `sagemaker_provisioning_policy`: `SchedulerAccess` on `schedule-group/*` and `schedule/SageMakerUnifiedStudio-*/*` | nothing to build: a portal workflow's schedule is a Scheduler schedule in that family of names (inferred from the policy; unread in the lab) |
| the GitLab pipeline: validate, plan, manual apply | Stage 8's chain with its manual gate (3.5): the deploy job applies `staging/orchestration/`, then `production/orchestration/` |

Neither reference role holds an `airflow-serverless` action, so the single change request for the
reference carries two items, inferred from its code: `airflow-serverless:ListWorkflows`,
`StartWorkflowRun` and `GetWorkflowRun` on `<prefix>-step-functions`; and `CreateWorkflow`,
`UpdateWorkflow`, `GetWorkflow` and `ListWorkflows`, the `iam:PassRole` of the workflow's execution
role and the write on the application's prefix on the GitLab CI/CD role. The bridge between chains
adds the project bucket's notification to EventBridge and a role trusted by `events.amazonaws.com`.
`dev` and `test` are SMUS projects at both ends: the two Sandbox projects here, the domain's projects
there. Sandbox gets no machine and no schedule: `sandbox/workflows/` (rank 56) stays as it is.

## Consequences for the plan

- **D7** keeps "MWAA Serverless only" for what runs the tasks and gains the chain layer above them;
  design B leaves INT-14's ladder, whose terminal rung is the `CreateWorkflow` call from the release
  job (Stage 10 step 4.2), the CLI's form, at the cost of a workflow outside Terraform's state.
- **D26** keeps "a deployment target is never associated"; the CLI deploys between the projects,
  never into a target.
- **D28** gains class (4b), a chain's state machine and schedule, created by the pipeline with the
  workflow, and class (2d), a processing task's code under the release's prefix (item 7); the
  execution role writes its application's result and inbox prefixes (item 10); the lint runs on the
  rendered file, since the repository's YAML carries the CLI's variables; the CLI's manifest draws the
  same line between content and activation.
- **Stage 8** gains step 2.5 (`app-etl` as an application, the `test` deploy and the `bundle` in its
  pipeline, the GitLab release linking to the bundle), decision 19 (the identity those jobs run as)
  and decision 20 (where the release's bundle is stored); step 5.7 records the CLI as measured; step
  3.3 keeps Staging's integration tests, the application's run having been tested in `test`.
- **Stage 10** rewrites step 2 (the workflow is born in the repository and reaches the projects by
  the CLI, the pipeline deploying the bundle), adds steps 3.4 to 3.7 (the chain layer's base, a
  chain, the dependencies between workflows, the chain's failure rule), turns step 4.2 into the API
  rung, reads 6.1's proof from the schedule and the machine's history, takes decision 7 as the
  alternative, keeps decision 11's `states:` and `scheduler:` reads, takes decisions 13 to 16 as
  recommended (the user, 16:28 UTC) and adds verifications xxii to xxvi.
- **`conventions.md`** names the chain layer in the `orchestration/` comment and puts
  `manifest.yaml`, `workflows/` and `code/` in the application layout; **open question 26**'s
  mechanism half is answered; **INT-14**'s fallback column names the API rung; **`SMUS.md`** records
  what the CLI does; `aws/orchestration.py` gains `OR-9` when the layer is built.
- **awsds-workflows** reformats its examples as applications, and `app-etl` follows, after the
  measurements, each in its own repository.

## Cost

Measured rates, `us-west-2` (`docs/PRICING.md` §1.4): Step Functions Standard USD 0.000025 per state
transition, so a chain of three applications polled every 60 s for an hour makes about 550
transitions, USD 0.014 per execution, and a chain of one about 180, USD 0.005; EventBridge Scheduler
USD 1.00 per million invocations after 14 million free a month; the schedule group, the log group and
the roles meter nothing at rest. The reference's Region pays 0.0000375 per transition and 1.70
per million. The workflow's own cost is D7's, 0.088 per task-hour, unchanged.

## Revision trigger

A deployment target that gains a domain association and a project (item 2's alternative), which
would make the CLI the deployer of every stage: Stage 18 measured its price (2026-10-17 to 2026-10-22),
and what reopens it is `DenyDataZoneEntirely`'s trigger, Production publishing a data product of its own; a Step Functions integration with MWAA Serverless
that the console does not list, or a `GetWorkflowRun` loop the service's quotas refuse at the chains'
cadence (Stage 10 verification xxii); or the service gaining a dependency between workflows of its
own, which would retire the inbox and leave the machine as the scheduler alone.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
