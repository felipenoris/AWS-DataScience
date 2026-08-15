# D28 — The production workflow contract: what must exist for a scientist-authored workflow to deploy

**Status:** Decided (2026-08-08): **Production runs workflows headless — no domain, no portal, no blueprint ever touches a deployment target. The pipeline creates, from the application repository, exactly six artifact classes**

**In one line:** What crosses the gate into a headless deployment target: exactly six artifact classes, carried by the repository.

**Related decisions:** [D7](D07-orchestration.md), [D14](D14-supply-chain-account.md), [D17](D17-interactive-vs-runtime.md), [D22](D22-data-governance-account.md), [D25](D25-drop-box-consumer.md), [D26](D26-unified-studio.md)

**Referenced by stages:** [Stage 6](../stages/stage-06-unified-studio.md), [Stage 9](../stages/stage-09-deployment-targets.md), [Stage 10](../stages/stage-10-orchestration-promotion.md)

---

## Rationale and consequences

The question D26 forces: the workflow is authored in the unified domain (Development), Production has no domain (D17) — so what crosses the gate? **The project's git repository is the promotion vehicle**, and the deployable set is: **(1)** the container image in Production ECR (D14); **(2)** the **workflow definition** — MWAA Serverless YAML — versioned in the repo, deployed by the pipeline to a versioned S3 prefix in Production; **(3)** a **per-workflow IAM execution role** built from `terraform-modules/iam-role`, holding the LF producer grants it needs (D22/D25) and nothing else — one role per workflow is the Serverless isolation model, and the least-privilege property a provisioned MWAA environment structurally cannot offer; **(4)** the orchestration resource itself: **`awscc_mwaaserverless_workflow`** (D7 alternative A) and/or **`aws_sfn_state_machine` + `aws_scheduler_schedule`** (alternative B); **(5)** an explicit **`aws_cloudwatch_log_group` per workflow** — named, retention set — wired into A's `LoggingConfiguration` and B's state-machine logging, so execution logs are a deliverable rather than an accumulation of default log groups nobody expires; **(6)** for ML, the **model package group** (`aws_sagemaker_model_package_group`, Stage 9) whose resource policy lets the pipeline register and approve versions, Staging read approved ones, and Development read status only (INT-04, 7). **Terraform support for (4) verified 2026-08-08:** `AWS::MWAAServerless::Workflow` exists in CloudFormation and the `awscc` provider exposes it as `awscc_mwaaserverless_workflow` — re-verify at Stage 10; fallbacks in order: `aws_cloudformation_stack` wrapping the CFN type, then provisioned MWAA (`aws_mwaa_environment`, `[E]`, with the metadata-database caveat back in force). **What authoring must respect, enforced by a promotion lint in Stage 8's CI:** the workflow YAML references the container by ECR URI and tag, never by anything project-scoped, and no operator may reference a domain resource (project connections, portal-scoped IDs) — a workflow that only runs where the portal exists is not a promotable artifact. INT-12, INT-13 and INT-14 carry the integration proofs.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
