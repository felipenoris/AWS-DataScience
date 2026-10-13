# D28 — The production workflow contract: what must exist for a scientist-authored workflow to deploy

**Status:** Decided (2026-08-08): Production runs workflows headless — no domain, no portal, no blueprint ever touches a deployment target. The pipeline creates, from the application repository, exactly six artifact classes.

**Amended 2026-10-13:** classes (2b) and (2c) join the six, both code a task reads from S3 rather than from an image (below).

**In one line:** What crosses the gate into a headless deployment target: a closed list of artifact classes, carried by the repository.

**Related decisions:** [D7](D07-orchestration.md), [D14](D14-supply-chain-account.md), [D17](D17-interactive-vs-runtime.md), [D22](D22-data-governance-account.md), [D25](D25-drop-box-consumer.md), [D26](D26-unified-studio.md)

**Referenced by stages:** [Stage 6](../stages/stage-06a-unified-studio.md), [Stage 9](../stages/stage-09-deployment-targets.md), [Stage 10](../stages/stage-10-orchestration-promotion.md)

---

## Rationale and consequences

D26 forces the question: the workflow is authored in the unified domain (Development), Production has no domain (D17), so what crosses the gate? **The project's git repository is the promotion vehicle**, and the deployable set is: **(1)** the container image in Production ECR (D14); **(2)** the **workflow definition** — MWAA Serverless YAML — versioned in the repo, deployed by the pipeline to a versioned S3 prefix in Production; **(3)** a **per-workflow IAM execution role** built from `terraform-modules/iam-role`, which starts and observes the workflow's jobs and holds no data permission, the LF producer grants (D22/D25) being the job role's (Stage 10 step 1.3) — one role per workflow is the Serverless isolation model, and the least-privilege property a provisioned MWAA environment structurally cannot offer; **(4)** the orchestration resource itself: **`awscc_mwaaserverless_workflow`** (D7 alternative A), or **`aws_sfn_state_machine` + `aws_scheduler_schedule`** (alternative B) only if INT-14's ladder falls through to it; **(5)** an explicit **`aws_cloudwatch_log_group` per workflow** — named, retention set — wired into A's `LoggingConfiguration` and B's state-machine logging, so execution logs are a deliverable rather than an accumulation of default log groups nobody expires; **(6)** for ML, the **model package group** (`aws_sagemaker_model_package_group`, Stage 9) whose resource policy lets the pipeline register and approve versions, Staging read approved ones, and Development read status only (INT-04, 7). **Terraform support for (4) verified 2026-08-08:** `AWS::MWAAServerless::Workflow` exists in CloudFormation and the `awscc` provider exposes it as `awscc_mwaaserverless_workflow` — re-verify at Stage 10; fallbacks in order: `aws_cloudformation_stack` wrapping the CFN type, then design B, documented and not built (Stage 10 step 4). Provisioned MWAA (`aws_mwaa_environment`) is not a rung: D7's amendment of 2026-09-05 removed it, and Stage 10 step 4.3 denies `airflow:CreateEnvironment` on the root SCP. **What authoring must respect, enforced by a promotion lint in Stage 8's CI:** the workflow YAML references the container by ECR URI and tag, never by anything project-scoped, and no operator may reference a domain resource (project connections, portal-scoped IDs). A workflow that only runs where the portal exists is not a promotable artifact. INT-12, INT-13 and INT-14 carry the integration proofs.

**The classes added 2026-10-13.** **(2b)** the workflow's operator code package: the `Code` object a `PythonOperator` or `BashOperator` task runs on the worker, which the service copies at each save and versions with the definition, so it is pinned by its S3 `VersionId` like (2); Stage 8 step 5.6 builds and checks it, as 6d step 4.5 asked. **(2c)** a Glue job's script and every file its arguments name (`--extra-py-files`, a wheel in `--additional-python-modules`): Glue reads them from S3 when each run starts and takes no version, so no pin holds them and a job runs whatever the key holds then. The job is declared by the application's Terraform and names a script under the release's own prefix; how that prefix is kept from changing, against roles that can write its bucket, is Stage 10 decision 12. A Visual ETL flow reaches a deployment target only as (2c): its `.vetl` and its portal schedule stay in the project, and the script its editor generates is what graduates.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
