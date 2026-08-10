# D21 — The Development account, and where experimentation ends

**Status:** Decided (2026-08-08): **a dedicated Development account; Sandbox becomes pure experimentation; the promotion chain starts in Development**

**In one line:** A Development account: Sandbox becomes pure experimentation and the promotion chain starts in Development.

**Related decisions:** [D19](D19-derived-zone.md), [D22](D22-data-governance-account.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 3](../stages/stage-03-networking.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 10](../stages/stage-10-orchestration-promotion.md)

---

## Rationale and consequences

The distinction the AWS MLOps roadmap draws and the previous revision collapsed "because there is one user": **Experimentation (Sandbox)** is where the unit of work is a *notebook* — no versioning expectation, nothing survives, cost is spasmodic and human-driven. **Development** is where the unit of work is a *pipeline* — a repository with tests, a SageMaker Pipeline, git, CI, the expectation that running it again on Tuesday gives the same answer. The user chose to build the boundary anyway, and it buys three real things even single-operator: (i) **the promotion chain gets an honest origin** — what enters CI from Development is already repository-shaped, so the pipeline never has to pretend a notebook is an artifact; (ii) **the graduation step becomes visible** — moving work from Sandbox to Development is a deliberate act (a git commit into a Development repository), not a gradual blurring inside one account; (iii) **cost attribution separates exploration from engineering**, which is the split a real budget conversation needs. **What Development is:** a second Interactive-OU account — Studio domain (VPC-only, same module as Sandbox), derived zone (D19), LF read share from the lake (D22), peering to Production for GitLab, and the place SageMaker Pipelines are *authored and test-run* before the pipeline promotes them. **What it is not:** a deployment target (humans work here interactively) and not a staging area (its runs prove the pipeline works, not that the artifact deploys). **Graduation Sandbox → Development is git, not a pipeline:** a notebook's logic is rewritten into the repository, reviewed, and committed — there is deliberately no automated path that lifts a notebook out of Sandbox, because the rewrite *is* the quality gate. Promotion is Development → Staging → Production and never starts in Sandbox.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
