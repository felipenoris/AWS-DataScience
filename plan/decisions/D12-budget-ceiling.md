# D12 — Budget ceiling

**Status:** Decided (2026-08-07): **USD 50/month**

**In one line:** USD 50/month ceiling; it is what rules out always-on GitLab and forces stop/start.

**Related decisions:** [D20](D20-staging-account.md), [D21](D21-development-account.md), [D22](D22-data-governance-account.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md)

---

## Rationale and consequences

With the three-layer model the projection is a ~USD 21-27/month floor plus ~USD 0.28-0.40 per lab hour, so roughly **USD 29-31/month** at the expected usage — the figure in `plan/cost-model.md`, which this row now quotes instead of the pre-D20/D21/D22 estimate of "USD 26-27" it carried until 2026-08-08. This ceiling is what rules out always-on GitLab (~USD 60/month by itself) and confirms the stop/start approach.

**How the ceiling is enforced, amended 2026-08-09.** This decision used to say the Stage 1a budget alerts at 50/80/100% with Cost Anomaly Detection alongside it. **The user skipped both**, so the AWS Budget exists and notifies nobody: **USD 50 is a target, not a threshold anything reacts to.** The ceiling is enforced by the operating model instead — the `[E]` teardown of D11 and a manual look at Cost Explorer. That is a weaker enforcement of the same number, and it is deliberate: the alerts are free and can be added in minutes whenever the trade stops being acceptable.

**Revision trigger:** the first month the real bill exceeds the USD 29-43 projection, or the first forgotten `[E]` resource found by reading the bill rather than by noticing it — either one is evidence that the ceiling needed a notification and not a figure.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
