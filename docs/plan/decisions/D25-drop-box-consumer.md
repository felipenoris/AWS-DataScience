# D25 — Who consumes the ingestion drop-box

**Status:** Decided (2026-08-08): **the Production job execution role, on the producer path; the `Data` OU SCP is tightened so no compute can run in Data Governance at all**

**In one line:** The Production job role consumes the ingestion drop-box, and the `Data` OU SCP is tightened to deny Glue jobs.

**Related decisions:** [D18](D18-data-scientist-access.md), [D22](D22-data-governance-account.md), [D26](D26-unified-studio.md), [D27](D27-catalog-maintenance.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 5](../stages/stage-05-data-foundation.md), [Stage 9](../stages/stage-09-deployment-targets.md)

---

## Rationale and consequences

D18 put an ingestion drop-box in the Data Governance account (`s3:PutObject` from the Interactive-OU roles into a dated prefix, no read, no list, no delete) and said "a pipeline picks up from it" — without naming the account that pipeline runs in. There is only one answer consistent with D22: **Production**, because Production's job role already holds the Lake Formation governed write, and ingestion is exactly the producer path applied to a file a human dropped rather than to an upstream feed. Data Governance cannot host it — the `Data` OU exists to make "nothing runs here" structural. **Two consequences to build rather than assume.** (i) The drop-box bucket policy needs a *second* statement, granting the Production job role `GetObject`, `ListBucket` on the dated prefixes and `DeleteObject` (the pickup has to consume what it read, or the letterbox never empties) — plus a grant on the drop-box KMS key, which is the half that is forgotten until the `AccessDenied` arrives. INT-10 carries it. (ii) The `Data` OU SCP as drafted in Stage 1 denies `ec2:RunInstances`, `sagemaker:Create*`, `glue:CreateDevEndpoint` and ECS/Lambda creation, but **not `glue:CreateJob`/`StartJobRun`** — a gap wide enough to run the whole ingestion in the wrong account by accident. Add Glue job creation and execution to the deny, so the SCP means what the OU's name promises. **The asymmetry is deliberate and worth stating:** the data scientist can put a file into the lake account but cannot read it back, and the thing that reads it runs behind the approval gate. That is what keeps the drop-box from becoming the general-purpose exchange bucket D18 refuses to build. **Revised 2026-08-08 (D26, D27):** "no compute at all" is now "no *user* compute". Two carve-outs were added by name, and the distinction between them is the useful part — `datazone:*` because a governance control plane is not compute (D26), and the crawler/optimizer actions under the catalog-maintenance role because they *are* compute and therefore need a bounded principal, an event trigger and an alarm (D27). The deny list in this decision is otherwise unchanged, Glue jobs included.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
