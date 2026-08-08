# D12 — Budget ceiling

**Status:** Decided (2026-08-07): **USD 50/month**

**In one line:** USD 50/month ceiling; it is what rules out always-on GitLab and forces stop/start.

**Related decisions:** [D20](D20-staging-account.md), [D21](D21-development-account.md), [D22](D22-data-governance-account.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md)

---

## Rationale and consequences

With the three-layer model the projection is a ~USD 21-27/month floor plus ~USD 0.28-0.40 per lab hour, so roughly **USD 29-31/month** at the expected usage — the figure in `plan/cost-model.md`, which this row now quotes instead of the pre-D20/D21/D22 estimate of "USD 26-27" it carried until 2026-08-08. The AWS Budget created in Stage 1 alerts at 50/80/100% of USD 50, with Cost Anomaly Detection alongside it. This ceiling is what rules out always-on GitLab (~USD 60/month by itself) and confirms the stop/start approach.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
