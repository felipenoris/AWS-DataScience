# Log — index

**What was actually done in AWS, by hand, one file per stage.** The stage files are written by the user,
**never** by Claude — Claude reads them, and records plan narrative in
[`plan/history.md`](../plan/history.md) instead.

**This index is the exception: Claude maintains it.** After reading a stage log, Claude brings that stage's
`Records` cell to what the file now holds. Nothing else under `log/` is Claude's to edit.

One log file mirrors one stage file: `log/stage-NN-*.md` ↔
[`plan/stages/stage-NN-*.md`](../plan/stages/INDEX.md). **Open the one row you need** — the `Records`
column below exists so that no stage ever requires reading another stage's log.

| Stage | Log | Records |
|---|---|---|
| Stage 0 — Baseline | [stage-00-baseline.md](stage-00-baseline.md) | Management account created by hand; `aws` CLI and `terraform` installed; the pre-existing `SUSPENDED` `Sandbox` account attached to the root, which predates the project and is left alone (`EXC-01`). |
| Stage 1a — Landing zone, accounts and OUs | [stage-01a-landing-zone.md](stage-01a-landing-zone.md) | Account-quota ticket (15); root MFA; the USD 50 budget; Control Tower enabled in `us-west-2`; every OU and account vend, **including the refused `Identity` vend under `Security`** that produced the `Identity` OU; the access portal; the `AWS Control Tower Admin` and `Infrastructure User` SSO users; the **break-glass chain** (`awsds-org-break-glass-alerts`, the `awsds-org-root-activity` metric filter, the `AWS Break Glass Alert` alarm) and its **2026-08-09 two-channel test**; centralized root access enabled and the per-account `Delete root credentials` check. |
| Stage 1b — Identity, policies, detective controls | [stage-01b-identity-and-controls.md](stage-01b-identity-and-controls.md) | **In progress — step 6 done, only 8.2 left.** Step 8.3's metric filter and its alarm; the Identity account registered as Identity Center delegated administrator (step 1); the five `sso-group-*` groups and their members (step 2); the `InfrastructureAccess` permission set, its tags and its assignments (step 3); the probe showing the delegated administrator reads everything but cannot change Management-targeted assignments (step 4); the six SSO profiles and the assumed-role ARN each one returns (step 5); the first `aws/list-identities.sh` snapshot and what it settles — step 3's owed tag check, step 4's read boundary across the whole read surface, and the root's enabled policy types; 5.1's retirement of the Account Factory direct assignments, including the second delegated-administrator boundary it uncovered — a permission set provisioned into Management cannot be altered from Identity, so the removals ran as CT Admin on Management, and verification (vi) left open by construction; and step 6's AZ name→ID table, identical across every account that has a profile, with the names not in ID order. |
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

**Adding a stage log:** the user creates `log/stage-NN-<same-slug-as-the-stage-file>.md` and copies the
two-line header from an existing one; Claude replaces that stage's `—` above with the link plus a one-line
`Records` summary, and keeps it current as the file grows. A row whose `Records` cell does not say what is
inside the file defeats the point of the index — *"stage not started"* against a file with five hundred
lines in it is the failure this rule exists to prevent, and it had already happened once.

**Not in these files:** break-glass *use* is also recorded here (date, reason, actions), but the procedure
itself is [`plan/runbooks/break-glass.md`](../plan/runbooks/break-glass.md); why the plan changed is
[`plan/history.md`](../plan/history.md).

---

*Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md) · Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md)*
