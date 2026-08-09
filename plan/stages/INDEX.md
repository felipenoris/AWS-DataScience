# Stages — index

Dependency order, not importance. Open one stage file plus the decisions its `Consumes` row lists;
that is the whole reading list for executing it.

| Stage | What it builds | Status | Prerequisites |
|---|---|---|---|
| [Stage 0 — Baseline](stage-00-baseline.md) | Management account by hand, local tooling, the documentation set. | **DONE** | none |
| [Stage 1a — Landing zone, accounts and OUs](stage-01a-landing-zone.md) | Control Tower, the accounts and OUs, root secured, budget — the slow, hard-to-undo half. | **done except the `Staging` vend** ([log](../../log/stage-01a-landing-zone.md)) | none outstanding (D1 decided, every account e-mail registered) |
| [Stage 1b — Identity, policies, detective controls, org-wide enablement](stage-01b-identity-and-controls.md) | Identity Center, permission sets, SCP/RCP, the free detective controls, org-wide enablement — the fast, reversible half. | **next** | Stage 1a complete, bar the deferred `Staging` vend |
| [Stage 2 — Terraform foundation](stage-02-terraform-foundation.md) | State buckets, module skeletons, the SCP import, CI hygiene checks. | not started | Stage 1. |
| [Stage 3 — Networking](stage-03-networking.md) | One VPC per account that has one (Sandbox — one per business unit, D35 — Development, Staging, Production), split `foundation/` + `egress/`. | not started | Stage 2. |
| [Stage 4 — VPN access](stage-04-vpn.md) | WireGuard, the only entry point; peering to Production so the tunnel reaches GitLab. | not started | Stage 3. D4 is decided: self-managed WireGuard. |
| [Stage 5 — Data foundation](stage-05-data-foundation.md) | Lake buckets, Glue catalog, Iceberg, Lake Formation registrations and the three cross-account shares; EFS. | not started | Stage 3. |
| [Stage 6 — SageMaker Unified Studio](stage-06-unified-studio.md) | The DataZone V2 domain, project profiles, and the two egress designs compared. | not started | Stages 3, 4, 5, and the ECR/CodeArtifact repositories from Stage 7 step 5 — **pulled forward**, because under egress design B they are how packages arrive, so they cannot come after the thing that consumes them. **D5 is executed, not decided, in this stage**: both designs get built (`plan/architecture.md` §4.3). |
| [Stage 7 — GitLab, Runners and ECR](stage-07-gitlab-runners-ecr.md) | GitLab CE on EC2, runners, ECR, CodeArtifact, internal names and TLS from the internal CA (D15 as revised — no public domain here). | not started | Stages 3 (which now builds the Production VPC), 4; decisions D8, D14, D15. |
| [Stage 8 — CI/CD pipelines](stage-08-cicd-pipelines.md) | The three pipeline types and the promotion gate. | not started | Stage 7. |
| [Stage 9 — Deployment target platforms, producer path](stage-09-deployment-targets.md) | Staging and Production platforms, Model Registry, the producer path into the lake. | not started | Stages 3, 5, 8. |
| [Stage 10 — Workflow orchestration and promotion](stage-10-orchestration-promotion.md) | Both orchestrators (D7) built and compared, end-to-end promotion. | not started | Stages 8, 9. **D7 is settled — both implementations are built here** and compared against the same application, which is the only way the MWAA-versus-native trade stops being abstract. What remains to check at the start of this stage, not to decide: that `awscc_mwaaserverless_workflow` still applies cleanly under the CI deploy role (INT-14 — verified to *exist* on 2026-08-08, not yet verified to apply under a permission boundary). The metadata-database question from the earlier revision of this stage applies **only if the provisioned fallback is ever used** — Serverless has no environment to destroy, so its run history is not state inside an `[E]` resource. |
| [Stage 11 — Data protection and DLP](stage-11-dlp.md) | Macie, CloudTrail data events, LF column/row filters, GuardDuty's paid add-ons — data-specific detection on top of the perimeter. | not started | Stages 5, 6, 9; decision D6. |
| [Stage 12 — Observability, governance and FinOps](stage-12-observability-finops.md) | Dashboards, alarms, cost attribution against what the bill actually shows. | not started | any stage that created resources. |
| [Stage 13 — Public-facing web tier (experiment)](stage-13-public-web-tier.md) | The public-facing experiment: web tier in front of a private backend. **Also the only stage with public DNS** — domain registration, public hosted zone and public ACM live here and nowhere earlier (D15 phase 2). | not started | Stages 3, 9, **and the domain name from the user**. |
| [Stage 14 — Per-business-unit Sandbox vending](stage-14-sandbox-vending.md) | A business unit's `Sandbox` account from one name in a merge request (D35). | not started | Stages 2, 3, 4, 6. The first stage about **scale** rather than capability: it parameterises slices that already exist, and it is where the VPN topology question (one hub, a Transit Gateway, or per-unit endpoints) is finally answered — with N in hand. **The promotion chain is untouched**: only `Sandbox` multiplies. |

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · What was actually done by hand, per stage:
[log/INDEX.md](../../log/INDEX.md) — same file slugs as here*
