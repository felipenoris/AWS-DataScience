# Log — index

**What was actually done in AWS, by hand, one file per stage.** Written by the user, **never** by Claude —
Claude reads these files, and records plan narrative in [`plan/history.md`](../plan/history.md) instead.

One log file mirrors one stage file: `log/stage-NN-*.md` ↔
[`plan/stages/stage-NN-*.md`](../plan/stages/INDEX.md). **Open the one row you need** — the `Records`
column below exists so that no stage ever requires reading another stage's log.

| Stage | Log | Records |
|---|---|---|
| Stage 0 — Baseline | [stage-00-baseline.md](stage-00-baseline.md) | Management account created by hand; `aws` CLI and `terraform` installed. |
| Stage 1a — Landing zone, accounts and OUs | [stage-01a-landing-zone.md](stage-01a-landing-zone.md) | Account-quota ticket (15); root MFA; the USD 50 budget; Control Tower enabled in `us-west-2`; every OU and account vend, **including the refused `Identity` vend under `Security`** that produced the `Identity` OU; the access portal; the `AWS Control Tower Admin` and `Infrastructure User` SSO users; the **break-glass chain** (`awsds-org-break-glass-alerts`, the `awsds-org-root-activity` metric filter, the `AWS Break Glass Alert` alarm) and its **2026-08-09 two-channel test**; centralized root access enabled and the per-account `Delete root credentials` check. |
| Stage 1b — Identity, policies, detective controls | [stage-01b-identity-and-controls.md](stage-01b-identity-and-controls.md) | *(stage not started — file exists, empty)* |
| Stage 2 — Terraform foundation | — | *no entries yet* |
| Stage 3 — Networking | — | *no entries yet* |
| Stage 4 — VPN access | — | *no entries yet* |
| Stage 5 — Data foundation | — | *no entries yet* |
| Stage 6 — SageMaker Unified Studio | — | *no entries yet* |
| Stage 7 — GitLab, Runners and ECR | — | *no entries yet* — will carry the **internal CA fingerprint** (D36) |
| Stage 8 — CI/CD pipelines | — | *no entries yet* |
| Stage 9 — Deployment target platforms | — | *no entries yet* |
| Stage 10 — Workflow orchestration and promotion | — | *no entries yet* |
| Stage 11 — Data protection and DLP | — | *no entries yet* |
| Stage 12 — Observability, governance and FinOps | — | *no entries yet* |
| Stage 13 — Public-facing web tier | — | *no entries yet* |
| Stage 14 — Per-business-unit Sandbox vending | — | *no entries yet* |

**Adding a stage log:** create `log/stage-NN-<same-slug-as-the-stage-file>.md`, copy the two-line header from
an existing one, and replace that stage's `—` above with the link plus a one-line `Records` summary. A row
whose `Records` cell does not say what is inside the file defeats the point of the index.

**Not in these files:** break-glass *use* is also recorded here (date, reason, actions), but the procedure
itself is [`plan/runbooks/break-glass.md`](../plan/runbooks/break-glass.md); why the plan changed is
[`plan/history.md`](../plan/history.md).

---

*Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md) · Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md)*
