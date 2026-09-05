# D17 — Where the data scientist works, and what crosses the account boundary

**Status:** Decided (2026-08-07), revised (2026-08-08, D21): **interactive compute exists only in the Interactive OU (Sandbox and Development); the deployment targets carry the SageMaker runtime, but only pipelines submit to it**

**AMENDED 2026-09-05 (user):** sharpened to **humans run code in Sandbox and nowhere else**. With `Development` converted to `Staging` ([6b](../stages/stage-06b-development-becomes-staging.md)) the Interactive OU holds the Sandboxes alone; Staging and Production carry the SageMaker **runtime** only — jobs, Pipelines, batch transform, the Model Registry and endpoints, none of which needs a domain object — and the `Workloads` OU denies the interactive surface and `datazone:*` outright.

**In one line:** Interactive compute exists only in the Interactive OU; deployment targets carry the runtime, and only pipelines submit to it.

**Related decisions:** [D14](D14-supply-chain-account.md), [D20](D20-staging-account.md), [D21](D21-development-account.md)

**Referenced by stages:** [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 9](../stages/stage-09-deployment-targets.md), [Stage 10](../stages/stage-10-orchestration-promotion.md)

---

## Rationale and consequences

"SageMaker" is two things and the account boundary runs between them. The **interactive** half — Studio domains, user profiles, JupyterLab/Code Editor apps — exists in the Sandbox and Development accounts and nowhere else: a Studio domain in a deployment target would put unreviewed code back inside the account boundary, which is the one thing the split buys. (The original decision said "Sandbox-only"; D21 split the interactive world into two accounts, so the invariant is now stated against the OU, which is where the SCP enforcing it attaches anyway.) The **runtime** half — training and processing jobs, Pipelines, Model Registry, endpoints — exists in Staging and Production, because that is where artifacts are tested, retrained and served; what changes is that a pipeline submits to it, never a person. This is also what AWS's own multi-account MLOps references do: Studio lives in the development/data-science accounts, and staging and production are deployment targets with no domain of their own. **The promotion boundary is four artifacts**, all travelling Development → Staging → Production through the pipeline (D20, D21): the container image (ECR), the model version (Model Registry), the workflow definition and application code (a git tag), and the Terraform that instantiates them. Sandbox work enters that chain only by graduating into a Development repository through git (D21) — there is no Sandbox → Staging path. **The Model Registry lives in Production** — D14 already collapsed the reference architecture's Tooling account into Production, and a model package group costs nothing at rest; Staging reads the registry and runs the approved version, it does not keep one of its own. **Consequences:** `terraform-live/production/sagemaker/` is a `[P]` slice (model package groups, and the execution role that pipeline-submitted jobs assume), with a job-execution-role-only counterpart in `terraform-live/staging/sagemaker/`; Stage 8's shared base image remains load-bearing, because "promote only the code" is only true if the runtime is identical by construction; and debugging a failed production job is a time-boxed elevated role approved by the **deployment manager**, logged and alarmed — not a notebook (the release approver owns this, not the governance one: it is a lifecycle act).

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
