# D19 — The derived zone — what Lake Formation does *not* do (extends D13)

**Status:** Decided (2026-08-07): **the copy is not prevented; the destination is managed and the perimeter contains it**

**In one line:** The derived copy is not prevented; the destination is managed and the perimeter contains it. Its CMK is the read control (D31).

**Related decisions:** [D5](D05-sagemaker-egress.md), [D13](D13-lake-formation-enforcement.md), [D18](D18-data-scientist-access.md), [D31](D31-approver-read.md)

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 5](../stages/stage-05-data-foundation.md), [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

Running a `SELECT` against the lake and storing the result is what a data science environment is *for*. Any principal that can read tabular data can materialise it outside the governed prefixes, and no configuration changes that. This is not a hole introduced by D18 — it has been true of the Sandbox since Stage 5, and of every SageMaker installation ever built. What it actually means is worth stating plainly: **Lake Formation's column and row filters are an entitlement mechanism, not a containment mechanism.** They decide what a principal may see at the moment of read; they say nothing about where the bytes go next. D13 makes the entitlement real; this decision covers everything after it. The practice: (i) **the output location is not the user's choice** — the Athena workgroup sets `EnforceWorkGroupConfiguration = true`, so a client cannot override the result location, and `s3:PutObject` on execution roles and permission sets is scoped to enumerated prefixes, never `*`; (ii) derived prefixes are **per principal** (`…/derived/${aws:userid}/`), so one person's copy is not a way around another person's grants; (iii) they carry a **lifecycle expiry**, so the shadow lake does not become permanent by accident; (iv) they sit **inside Macie's scan scope and carry CloudTrail data events** (Stage 11), because this is where sensitive data actually accumulates; (v) classification **inherits** — the output of a query over `restricted` data is `restricted` — stated as policy, because nothing enforces it automatically at this scale (`plan/institutional-delta.md`: this is exactly where a catalog with lineage earns its price). **And the containment itself comes from somewhere else entirely:** the copy is tolerable because the data perimeter (`plan/architecture.md` §4.2) stops it leaving the organization and D5 stops it leaving the network. Preventing the copy was never the control. The perimeter is. **Revised 2026-08-08 (D31): a sixth practice, and it is the only one on this list that is default-deny.** The five above answer *where the copy lands*, *how long it lives* and *who is told about it*; none of them answers **who may read it**, which was left to whatever IAM policies happened to exist — and that turned out to be how a release approver acquired read access to materialised `restricted` data without anyone deciding it. So the derived zone gets **its own KMS CMK**, separate from the account's general-purpose key, and the key policy carries the answer: `kms:Decrypt` to the project execution roles and `DataScientistAccess`, and to nobody else. It survives forgetfulness in a way a prefix deny-list does not — a new derived prefix under the same key is covered without anyone updating anything.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
