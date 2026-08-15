# D5 — SageMaker internet restriction mechanism

**Status:** Decided (2026-08-07): **build BOTH and compare, in Stage 6**

**In one line:** Two egress designs built behind a switch and compared: (A) NAT plus allowlist, (B) no NAT at all.

**Related decisions:** —

**Referenced by stages:** [Stage 3](../stages/stage-03-networking.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

Not one mechanism but two designs, implemented behind a switch and evaluated against each other — see `docs/plan/architecture.md` §4.3. **(A) Limited internet:** NAT plus an allowlist, using Route 53 Resolver DNS Firewall and/or a Squid proxy. **(B) No internet:** no NAT at all for the SageMaker subnets; packages arrive through CodeArtifact (upstream to the public repositories) and ECR pull-through cache, everything else through VPC endpoints. AWS Network Firewall (~USD 290/month) stays documented as the enterprise variant of (A) but is not built. The user's stated reservation about (B) is recorded in `docs/plan/architecture.md` §4.3: CodeArtifact does not cover every language this environment needs.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
