# D10 — Identity Center administration

**Status:** Decided (2026-08-07): **delegated to a dedicated Identity account**

**In one line:** Identity Center administration delegated to a dedicated Identity account, so Terraform never holds Management credentials.

**Related decisions:** —

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 2](../stages/stage-02-terraform-foundation.md)

---

## Rationale and consequences

The Identity Center instance and its identity store are created in the Management account and cannot be moved; what is delegated is their *administration*. One member account is registered as delegated administrator (`sso.amazonaws.com`), and from there Terraform manages permission sets, groups and assignments — so Terraform never needs credentials in the Management account, which is what makes principle 1 real rather than aspirational. The role goes to a **dedicated Identity account** rather than to the Audit account: Audit stays the security guardian (GuardDuty, Security Hub, Macie findings) and Identity owns access management, so the two concerns do not share a blast radius. Costs one extra Control Tower-governed account, i.e. one more AWS Config recorder (~USD 0.50-1/month) — accepted in exchange for the separation. **Consequences:** (i) assignments whose *target* is the Management account cannot be managed from the delegated account and stay manual; (ii) the Identity account can grant administrative access to any account in the organization, so it is as sensitive as Management — the data scientist must never have access to it; (iii) Control Tower's own permission sets (`AWSAdministratorAccess` and friends) are left alone, since editing them causes landing-zone drift.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
