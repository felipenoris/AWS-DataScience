# Stage 11 — Data protection and DLP

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 5, 6, 9; decision D6. |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D6](../decisions/D06-dlp-approach.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D19](../decisions/D19-derived-zone.md), [D22](../decisions/D22-data-governance-account.md) |
| **Proves** | — |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the protection layer, built on top of a working environment rather than before it.

**Prerequisites:** Stages 5, 6, 9; decision D6.

**To execute:**

**What is no longer in this stage:** the data perimeter (`plan/architecture.md` §4.2) moved to Stage 1, and
the detective services moved to the stage that first gives each one something to observe (principle 9, as
amended): IAM Access Analyzer to Stage 1b step 8 because it is free, **GuardDuty to Stage 4 step 10** with
the first internet-facing resource, **Security Hub to Stage 5 step 13** with the first governed data. What
remains here is genuinely data-specific.

1. Amazon Macie for sensitive-data discovery — primary scope the **Data Governance** buckets (D22),
   plus the **derived zones in Sandbox and Development** (D19), which is where governed data re-surfaces
   outside the lake account and is the part a Data-Management-only scope would miss; findings to Security
   Hub; results mapped
   onto the classification scheme defined in Stage 5 step 2. **Scope it to a sampled prefix** — Macie bills
   per GB inspected and can dwarf every other line item in `plan/cost-model.md`.
2. Lake Formation column-level and row-level filters driven by the LF-Tags from Stage 5, enforceable
   because of D13.
3. Egress hardening review of Stage 6, once D5 has been closed by the comparison in `plan/architecture.md` §4.3.
   **Correction:** the previous version of this plan listed "block SageMaker Studio file download /
   notebook export" as a control. Verify it exists before relying on it (Stage 6 flags the same doubt) —
   as far as this plan knows, Studio has no supported setting for that. If it does not, say so plainly in
   the threat model rather than leaving a control listed that nobody implemented.
4. Turn on GuardDuty's **S3 Protection and Malware Protection** — the base service has been running since
   Stage 4 step 10, and these two are billed separately and were deferred specifically so the decision
   could be made against a real bill (`plan/cost-model.md`).
5. CloudTrail data events on the sensitive buckets; CloudWatch alarms for exfiltration patterns: mass
   `GetObject`, unusual egress volume, `PutObject` to an unexpected destination.
   **Correction:** the previous version listed an alarm on "presigned URL creation". That is not
   detectable — signing a presigned URL is a local SigV4 operation against credentials already held, it
   makes no API call and appears nowhere in CloudTrail. What *is* detectable is the **use** of one, which
   shows up as a request whose authentication method differs from a normal SigV4 call. Alarm on that.
6. Only then evaluate whether a third-party DLP agent adds anything the above does not cover.

**Deliverables:** a documented threat model with the control that addresses each item — and, for the items
where no control exists, an explicit statement that the risk is accepted rather than a control that was
never built; alarms that fire on a simulated exfiltration attempt.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
