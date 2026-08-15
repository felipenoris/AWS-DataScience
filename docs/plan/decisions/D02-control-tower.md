# D2 — Control Tower vs. plain Organizations

**Status:** Decided: **Control Tower**

**In one line:** Control Tower rather than plain Organizations; AWS Config is the price of it.

**Related decisions:** —

**Referenced by stages:** —

---

## Rationale and consequences

Required by `CLAUDE.md`. It creates the Log Archive and Audit accounts, enables CloudTrail/Config org-wide and provides guardrails. Downside: AWS Config is the main recurring cost of the landing zone.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
