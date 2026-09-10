# D1 — Region

**Status:** Decided (2026-08-07): **`us-west-2`**

**In one line:** `us-west-2`, and it stays there; region portability is Terraform hygiene, not planned work.

**Related decisions:** —

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md)

---

## Rationale and consequences

Oregon, chosen on cost — roughly half São Paulo's price on metered items. Data residency is not a concern: this is a test with no real data. The project mirrors something that would run in `sa-east-1` in practice, but that move is hypothetical and is not planned work; it implies only the Terraform hygiene in `docs/plan/architecture.md` §4.1. The availability question was answered there: nothing this plan uses is missing from São Paulo.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
