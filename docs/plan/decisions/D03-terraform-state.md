# D3 — Terraform state location

**Status:** Decided: **per-account S3 bucket, native S3 locking**

**In one line:** Terraform state in a per-account S3 bucket with native S3 locking; no DynamoDB, nothing in Management.

**Related decisions:** [D10](D10-identity-center-delegation.md)

**Referenced by stages:** [Stage 2](../stages/stage-02-terraform-foundation.md)

---

## Rationale and consequences

Terraform 1.15 supports `use_lockfile = true`, so no DynamoDB table is needed. Sandbox state lives in the Sandbox account, Production state in the Production account, and identity state in the Identity account (D10). This avoids putting state in the Management account (principle 1) and avoids cross-account state access.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
