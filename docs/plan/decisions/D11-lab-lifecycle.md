# D11 — Lifecycle of the lab

**Status:** Decided (2026-08-07): **resources are ephemeral, accounts are not**

**AMENDED 2026-09-05:** the three layers are unchanged; the hub adds a **cross-account** bring-up dependency the per-ENV `make up`/`down` cannot express. `production/networking/` is `[P]` (nothing to start), the WireGuard and Squid hosts are `[D]` with their own `make hub-up`/`hub-down` target, and a spoke's `make up` refuses while either is stopped — turning what would be a blackhole into an error ([Stage 6c](../stages/stage-06c-networking-hub.md) pass 7).

**In one line:** Resources are ephemeral, accounts are not: pay nothing while idle, in three layers.

**Related decisions:** —

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 2](../stages/stage-02-terraform-foundation.md)

---

## Rationale and consequences

The environment runs for a few hours per session and is shut down in between. Accounts, the Organization, Control Tower and Identity Center are never destroyed. Within the accounts the rule is not "destroy everything" but **"pay nothing while idle"**: resources that cost nothing at rest are simply left in place, resources that meter are destroyed, and stateful services that are awkward to rebuild are stopped rather than destroyed. Three layers, defined in `docs/plan/conventions.md` §5.1.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
