# Stage 10 — Workflow orchestration and promotion

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 8, 9. **D7 is settled — both implementations are built here** and compared against the same application, which is the only way the MWAA-versus-native trade stops being abstract. What remains to check at the start of this stage, not to decide: that `awscc_mwaaserverless_workflow` still applies cleanly under the CI deploy role (INT-14 — verified to *exist* on 2026-08-08, not yet verified to apply under a permission boundary). The metadata-database question from the earlier revision of this stage applies **only if the provisioned fallback is ever used** — Serverless has no environment to destroy, so its run history is not state inside an `[E]` resource. |
| **Consumes** | [D7](../decisions/D07-orchestration.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D28](../decisions/D28-workflow-contract.md) |
| **Proves** | [INT-14](../integrations.md) |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** take a workflow developed in SageMaker and run it in production on a schedule.

**Prerequisites:** Stages 8, 9. **D7 is settled — both implementations are built here** and compared
against the same application, which is the only way the MWAA-versus-native trade stops being abstract.
What remains to check at the start of this stage, not to decide: that `awscc_mwaaserverless_workflow`
still applies cleanly under the CI deploy role (INT-14 — verified to *exist* on 2026-08-08, not yet
verified to apply under a permission boundary). The metadata-database question from the earlier revision
of this stage applies **only if the provisioned fallback is ever used** — Serverless has no environment
to destroy, so its run history is not state inside an `[E]` resource.

**And one thing this stage stopped being separate from, 2026-08-13.** `CLAUDE.md` now names "SageMaker
workflows" as a data-scientist feature, and the Unified Studio *Workflows* tool **is Amazon MWAA** — in both
a serverless and a provisioned form, with existing environments connectable to a project. So the workflow a
data scientist authors in Stage 6 and the orchestrator compared here are the same product, not two that
happen to meet at D28's artifact contract. Two consequences: the D7 comparison should be run against a
workflow **authored in the Studio**, not a hand-written DAG, or it measures the wrong thing; and whatever
Stage 6 turns on for the Workflows capability is already the provisioned/serverless choice this stage
believes it is making — check what exists before building either
(`docs/plan/open-questions.md` item 15).

**To execute:**

1. Implement **both** orchestrators against the same workflow, behind a switch, in
   `production/orchestration/`, each producing the D28 artifact set:
   - **(A) MWAA Serverless** — the workflow YAML from the application repository, deployed by the
     pipeline to a versioned S3 prefix; one **`awscc_mwaaserverless_workflow`** per application, with its
     own execution role and its own log group (D28 items 2-5). Fallbacks in order (INT-14):
     `aws_cloudformation_stack` wrapping `AWS::MWAAServerless::Workflow`; then a `mw1.micro` environment
     (`aws_mwaa_environment`, `[E]`, metadata-database caveat back in force).
   - **(B) Native** — an **`aws_scheduler_schedule`** (EventBridge Scheduler) triggers an
     **`aws_sfn_state_machine`**; container steps run on ECS/Fargate or as SageMaker jobs, glue steps on
     **Lambda**; the state machine's logging configuration writes to the same explicit
     **`aws_cloudwatch_log_group`** discipline as A — named, retention set, per workflow.
   **One asymmetry the comparison must not hide:** A is defined in YAML (DAG-factory format — AWS ships
   a Python-to-YAML converter), B in ASL. The Airflow DAG a data scientist writes in the domain converts
   to A mechanically; to B it must be *ported*. That difference is a large part of what is being compared.
   The rest to write down: cost per run and per month, time to deploy a change, how a failed task is
   retried and observed — under A this means logs only, there is no Airflow UI in Serverless — and what
   each costs in Terraform code and operational surface. Cost model and per-unit rates: `docs/plan/cost-model.md`, `docs/PRICING.md`.
2. Define how a workflow authored in the unified domain becomes a deployable artifact — the D28 set: the
   container, the workflow YAML and the terraform/ folder, all versioned in the project repository that
   graduated into GitLab. **The container must be identical for both orchestrators**; if it is not, the
   comparison is measuring the packaging, not the orchestrator. **Add the D28 promotion lint to the
   Stage 8 CI here:** reject any workflow definition that references a domain resource (project
   connections, portal-scoped IDs) or names a container by anything other than ECR URI and tag — a
   workflow that only runs where the portal exists is not a promotable artifact.
3. Schedule, retry, alerting on failure to CloudWatch/SNS — alarms on the per-workflow log groups and on
   the workflow/state-machine failure metrics, in both implementations.
4. If — and only if — the provisioned fallback is used: **first, how the Airflow UI is reached at all.**
   A provisioned environment in *private* web-server mode is served by interface endpoints
   (`airflow.env`, `airflow.api`, `airflow.ops`) whose private DNS answers **only inside the VPC that owns
   them** — an AWS-managed zone that cannot be associated with another VPC (Stage 3 step 4). The laptop
   resolves through the *Sandbox* VPC, so `<env>.<region>.airflow.amazonaws.com` will not resolve to those
   ENIs by itself. The fix is internal and cheap, but it is work: a private hosted zone of our own with
   ALIAS records to the endpoint DNS name, associated with the Sandbox VPC, or a hosts-file entry on the
   laptop. Public web-server mode is not the alternative — it would put the Airflow UI on the internet,
   which `CLAUDE.md` rules out. **Under MWAA Serverless the question is empty: there is no web UI at all**,
   which is one more entry for the step 1 comparison, and the reason this whole item is conditional.
   Then: document how to create and destroy the MWAA environment on demand, and what is lost when it goes. DAG code lives in S3 and survives; run history
   and UI-defined connections/variables do not. Either export them before teardown or state explicitly
   that they are expendable — the `[E]` rule in `docs/plan/conventions.md` §5.1 does not allow leaving this implicit. Under
   Serverless this step is empty by construction, which is itself a point for the comparison in step 1.
5. **Close the notebook-to-production gap for models, not just for ETL.** The CI/CD in Stage 8 promotes a
   container; that covers the `app-etl` template in [`docs/plan/conventions.md`](../conventions.md) but not the other thing a data science
   environment produces, which is a trained model. The **SageMaker Model Registry** is the promotion
   boundary — a model version is *approved*, not a file copied — and D17 puts it in the Production account,
   built in Stage 9 step 3, so this stage consumes it rather than inventing it. What remains to define
   here: who registers a model version and under which role (the pipeline's, never the data scientist's),
   how an approved version is served (batch transform or an endpoint), and what is recorded alongside it —
   training data version, metrics, owner. Without this, "data science environment" means "notebooks with a
   nice network", and the whole promotion story only works for code.
   Where the *production* retraining job runs follows from D17 as well: in the Production account, on the
   execution role from `production/sagemaker/`, submitted by the orchestrator chosen at the top of this
   stage. Interactive-account training stays exploratory (Sandbox) or developmental (Development) and
   never produces a registered version directly — registration is the pipeline's act, after graduation
   through git (D21).
   **And the model follows the same chain as the code (D20):** an approved version is first served in
   Staging, against Staging's sampled data, and the promotion pipeline asserts that it loads and returns
   predictions of the expected shape before the Production deployment step runs. A model that only ever
   ran on the machine that trained it is not a promoted artifact — it is a file that changed accounts.

**Deliverables:** a workflow prototyped in Sandbox, engineered in Development and promoted through the
chain runs on schedule in production without manual steps, and a model reaches production through the
registry — exercised in Staging on the way — rather than by being copied.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
