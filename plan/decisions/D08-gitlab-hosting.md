# D8 — GitLab hosting

**Status:** Decided: **self-managed on EC2 in the Production account, layer `[D]`**

**In one line:** GitLab CE self-managed on EC2 in Production, layer `[D]` — stopped between sessions, not destroyed.

**Related decisions:** [D14](D14-supply-chain-account.md)

**Referenced by stages:** [Stage 7](../stages/stage-07-gitlab-runners-ecr.md), [Stage 8](../stages/stage-08-cicd-pipelines.md)

---

## Rationale and consequences

Required by `CLAUDE.md`. GitLab CE Omnibus on a private-subnet EC2 instance, reached through the VPN, backed up to S3. Account placement per D14. Sizing: 8 GB RAM is the realistic minimum for GitLab + Pages — `t4g.large` (ARM) is ~20% cheaper than `t3.large` for the same memory and GitLab Omnibus ships arm64 packages. Stopped between sessions rather than destroyed (~USD 4/month of EBS), because rebuilding from backup on every session is the fragile path.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
