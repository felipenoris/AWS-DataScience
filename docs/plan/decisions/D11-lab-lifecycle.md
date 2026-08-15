# D11 — Lifecycle of the lab

**Status:** Decided (2026-08-07): **resources are ephemeral, accounts are not**

**In one line:** Resources are ephemeral, accounts are not: pay nothing while idle, in three layers.

**Related decisions:** —

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 2](../stages/stage-02-terraform-foundation.md)

---

## Rationale and consequences

The environment runs for a few hours per session and is shut down in between. Accounts, the Organization, Control Tower and Identity Center are never destroyed. Within the accounts the rule is not "destroy everything" but **"pay nothing while idle"**: resources that cost nothing at rest are simply left in place, resources that meter are destroyed, and stateful services that are awkward to rebuild are stopped rather than destroyed. Three layers, defined in `docs/plan/conventions.md` §5.1.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
