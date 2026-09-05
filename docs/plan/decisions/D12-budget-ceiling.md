# D12 — Budget ceiling

**Status:** Decided (2026-08-07): **USD 50/month**

**AMENDED 2026-09-05:** the ceiling is unchanged and is what rules the hub's shape — **zero NAT gateways** (a standing one is ≈ USD 36.50/month, three quarters of the ceiling) and Transit Gateway rejected with a number (USD 0.05 per attachment-hour). The floor moves by roughly +USD 4.65/month (a second Elastic IP and one or two private zones) and every session hour falls, since the two per-account NAT gateways are destroyed.

**In one line:** USD 50/month ceiling; it is what rules out always-on GitLab and forces stop/start.

**Related decisions:** [D20](D20-staging-account.md), [D21](D21-development-account.md), [D22](D22-data-governance-account.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1d](../stages/stage-01d-org-wide-enablement.md), [Stage 6](../stages/stage-06a-unified-studio.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md)

---

## Rationale and consequences

**The projection lives in [`docs/plan/cost-model.md`](../cost-model.md), and this decision deliberately carries no copy of it** (amended 2026-08-21). That file computes the monthly floor and the per-lab-hour metering, and its Floor row is the one that moves when a build adds a resource — twice already, both KMS: +USD 1.00 for the lake CMK on 2026-08-18 and +USD 3.00 for Stage 6's three on 2026-08-21. **The figures this paragraph carried until then — a "~USD 21-27/month floor" — were the pre-D29/D31 numbers `cost-model.md` retired on 2026-08-08 as understatements**, so a reader comparing the two files was comparing two eras of arithmetic, with the older one flattering the ceiling (Lesson 7: a rejected-on-cost option goes stale in the direction that flatters the rejection). The revision trigger below is written against the current projection, not against these. **What D12 owns is the choice of USD 50** — and that ceiling is what rules out always-on GitLab (~USD 60/month by itself) and confirms the stop/start approach.

**How the ceiling is enforced, amended 2026-08-09.** This decision used to say the Stage 1a budget alerts at 50/80/100% with Cost Anomaly Detection alongside it. **The user skipped both**, so the AWS Budget exists and notifies nobody: **USD 50 is a target, not a threshold anything reacts to.** The ceiling is enforced by the operating model instead — the `[E]` teardown of D11 and a manual look at Cost Explorer. That is a weaker enforcement of the same number, and it is deliberate: the alerts are free and can be added in minutes whenever the trade stops being acceptable.

**Revision trigger:** the first month the real bill exceeds the USD 29-43 projection, or the first forgotten `[E]` resource found by reading the bill rather than by noticing it — either one is evidence that the ceiling needed a notification and not a figure.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
