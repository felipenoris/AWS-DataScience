# D23 — OU structure — the account is the isolation boundary, the OU is the policy boundary

**Status:** Decided (2026-08-08): **four OUs, each defined by the policy set it carries: Security, Interactive, Data, Workloads. Revised the same day by D29: a fifth, `Policy Test`, holding the throwaway `Policy Canary` account**

**In one line:** Five OUs, each named for the policy set it carries; the account isolates, the OU attaches policy.

**Related decisions:** [D20](D20-staging-account.md), [D26](D26-unified-studio.md), [D27](D27-catalog-maintenance.md), [D29](D29-policy-canary.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md)

---

## Rationale and consequences

Segregating "by OU" versus "by account" is a false choice — accounts isolate (blast radius, quotas, billing, credentials), OUs attach policy once so it is inherited rather than remembered. An OU therefore earns its existence exactly when two or more accounts need the same policy set, and the OUs here are named for their policy, not for their contents: **Security** (Log Archive, Audit, Identity — Control Tower's guardrails plus delegated administration), **Interactive** (Sandbox, Development — interactive compute *allowed*, human infrastructure changes denied), **Data** (Data Governance — no *user* compute, with the two named carve-outs D26 and D27 add, deletion denied), **Workloads** (Staging, Production — no interactive compute, no human control plane; the D20 SCP set unchanged). A per-environment OU tree (one OU per account) was considered and rejected: an OU holding exactly one account forever is a folder with one file — policy might as well attach to the account. The revision triggers are recorded here so the structure is revisited deliberately: a second production-like account → nest `Workloads` into `NonProd`/`Prod`; the first time Staging and Production need genuinely different policy → the same; a second data domain → the `Data` OU stops being a single-account OU by itself. **The OU this row used to list as notably absent — a policy staging OU for testing SCPs before they attach to anything real — was built the same day as D29**, under the names `Policy Test` (OU) and `Policy Canary` (account), chosen precisely to avoid the collision with the Staging *account* that this row spent a sentence warning about. It is the one single-account OU that passes the test above rather than failing it: its purpose *is* to contain a disposable account, so the account and the OU are the same decision.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
