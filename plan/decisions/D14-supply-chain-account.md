# D14 — Where GitLab, Runners, ECR and CodeArtifact live

**Status:** Decided (2026-08-07): **the Production account**

**In one line:** GitLab, Runners, ECR and CodeArtifact live in Production, not next to the people the gate gates.

**Related decisions:** [D21](D21-development-account.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 3](../stages/stage-03-networking.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 9](../stages/stage-09-deployment-targets.md)

---

## Rationale and consequences

These four are the software supply chain. In the Sandbox account they would sit next to a `data-scientists` group with broad permissions, which means the runner holding the deploy credentials, and the registry Production pulls from, would both be modifiable by the people the approval gate is supposed to gate. Putting them in Production removes that path and costs no extra account. **Accepted trade-off:** build and runtime now share an account, so there is no blast-radius boundary between "the thing that builds" and "the thing that runs" — a compromise of GitLab is a compromise of Production. A large institution splits these into a Shared Services / Tooling account in an `Infrastructure` OU (`plan/institutional-delta.md`). **Consequences:** the Production VPC moves from Stage 9 to Stage 3; Sandbox↔Production VPC peering is needed so the VPN reaches GitLab (and, since D21, a second peering from Development); ECR and CodeArtifact are consumed cross-account from **both Interactive accounts**; and the data scientist needs a narrow, service-level (not infrastructure-level) reach into Production.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
