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

**Access Analyzer is the one that moved only halfway, and the distinction matters (2026-08-12).** What went
to 1b step 8.2 is the *organization-level external-access analyzer* — switched on early because it is free
and because it catches what Stages 2-3 create. **Its DLP role is not discharged by having been switched
on**: a service that emits findings nobody reads is Lesson 5 wearing a dashboard. D6 gives Access Analyzer
its place in the strategy; **step 2.1 below is where this stage collects on it**, and it also covers the
half 1b could not: an org-scoped external analyzer is silent by construction about access *inside* the
organization, which is exactly the movement this stage exists to control.

1. Amazon Macie for sensitive-data discovery — primary scope the **Data Governance** buckets (D22),
   plus the **derived zones in Sandbox and Development** (D19), which is where governed data re-surfaces
   outside the lake account and is the part a Data-Management-only scope would miss; findings to Security
   Hub; results mapped
   onto the classification scheme defined in Stage 5 step 2. **Scope it to a sampled prefix** — Macie bills
   per GB inspected and can dwarf every other line item in `plan/cost-model.md`.
2. Lake Formation column-level and row-level filters driven by the LF-Tags from Stage 5, enforceable
   because of D13.

   **Step 2.1 — collect on IAM Access Analyzer: the external findings as a stage input, the internal ones as
   a decision.** Numbered 2.1 rather than 3 so the steps after it keep their meaning — `plan/cost-model.md`
   refers to "Stage 11 step 4" by name.

   - **Read the external-access findings before writing the threat model, not after.** The analyzer has been
     running org-wide since 1b step 8.2 and by now has watched Stages 2-9 create every bucket, role, key,
     snapshot and file system in this environment. Every open finding is a row in the deliverable: answered,
     or explicitly accepted. **If a finding is intended, archive it with a rule and record why** — by design
     there should be none, since every cross-account share this project makes is *inside* the organization and
     invisible to an org-scoped analyzer, so a finding here is a genuine surprise and a list nobody triaged is
     indistinguishable from a list with nothing in it.
   - **The findings are load-bearing, not informational, for five resource types** — Lambda, SNS, EBS volume
     snapshots, RDS DB and DB-cluster snapshots, and EFS — because **no RCP covers them**
     (`plan/architecture.md` §4.2). The snapshots and D24's EFS are data-bearing, so for those the finding is
     not a check on the perimeter, it *is* the perimeter, and the threat model must say so rather than
     inheriting D19's "the perimeter contains it".
   - **Then decide on internal-access findings, which is the half that is actually about this stage.** They
     answer "which principals inside the organization can reach this resource" for **S3 buckets, RDS DB and
     DB-cluster snapshots, DynamoDB tables and streams** — which makes them the machine check of **D13**:
     that execution roles hold no direct S3 path to Lake Formation-registered prefixes, and therefore that the
     column and row filters in step 2 are not decoration. D13 is a claim about policies this project wrote,
     and until now nothing tested it (Lesson 18 — a policy never constrains the principal that authors it).
     Same for the **D19** derived zone: the CMK is asserted to be the read control, and this is what shows
     who can actually decrypt through it.
     - **It is paid, per resource monitored per analyzer-month**, so scope it the way Macie is scoped in step
       1 — the Data Governance registered buckets (D22) and the derived-zone buckets (D19), not every bucket
       in the organization. **Measure the price from the Price List API before enabling** (Lesson 6):
       `PRICING.md`'s Access Analyzer row currently prices only the per-check dimension, so it does not
       answer this question and must not be read as if it did.
     - **It does not cover EFS, and it does not see the Glue/Lake Formation catalog layer.** So it verifies
       the S3 path *underneath* the catalog — precisely the bypass D13 exists to close — and says nothing
       about entitlements expressed as LF-Tags. Two different questions; do not let a clean internal-access
       report be read as an answer about the catalog.
   - **Unused-access findings stay in Stage 12** and are not re-litigated here.
3. Egress hardening review of Stage 6, once D5 has been closed by the comparison in `plan/architecture.md` §4.3.
   **Correction:** the previous version of this plan listed "block SageMaker Studio file download /
   notebook export" as a control. Verify it exists before relying on it (Stage 6 flags the same doubt) —
   as far as this plan knows, Studio has no supported setting for that. If it does not, say so plainly in
   the threat model rather than leaving a control listed that nobody implemented.
   **And the browser is no longer the only surface to ask the question about (2026-08-13).** `CLAUDE.md`
   asks for the **remote IDE**: `sagemaker:StartSession` attaches a local VS Code to a running space, which
   is a file channel onto a laptop that no browser-side setting reaches. So a "yes, downloads are blocked"
   answer about the browser is not an answer about the environment. What exists is tag-scoping
   `StartSession` to a user's own private apps — a *scoping* control, not a *transfer* control. Whatever is
   left after it is an accepted risk, and this is the item most likely to end up in the deliverable's
   "accepted rather than controlled" column (`plan/open-questions.md` items 6 and 14).
4. Turn on GuardDuty's **S3 Protection and Malware Protection** — the base service has been running since
   Stage 4 step 10, and these two are billed separately and were deferred specifically so the decision
   could be made against a real bill (`plan/cost-model.md`).
   **This step is blocked by an SCP of this project's, on purpose, and the block is known in advance.**
   `DenyGuardDutyTampering` in `awsds-org-scp-baseline` denies `guardduty:UpdateDetector` unconditionally
   on the organization root, so it reaches Audit — the administrator account — as hard as any member.
   Enabling a feature **org-wide** is unaffected (`UpdateOrganizationConfiguration` and
   `UpdateMemberDetectors` are not denied); enabling it on **Audit's own detector** is the call that fails.
   Either detach the baseline document, make the change, re-attach and re-run phases 1-3 of
   [`plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md) — the re-attach is not done until the probes
   have run — or, if this recurs, carve out the named administration role in Stage 4, exactly the way D27's
   carve-out names one role. **The mistake to avoid is reading the `AccessDenied` as a broken policy and
   deleting the statement**: it is the statement that stops a compromised account from turning off its own
   detection.
5. CloudTrail data events on the sensitive buckets; CloudWatch alarms for exfiltration patterns: mass
   `GetObject`, unusual egress volume, `PutObject` to an unexpected destination.
   **Correction:** the previous version listed an alarm on "presigned URL creation". That is not
   detectable — signing a presigned URL is a local SigV4 operation against credentials already held, it
   makes no API call and appears nowhere in CloudTrail. What *is* detectable is the **use** of one, which
   shows up as a request whose authentication method differs from a normal SigV4 call. Alarm on that.
   **One read path is in scope specifically because no SCP covers it: Athena inside Data Governance.**
   The `Data` OU document denies user compute and deliberately leaves `athena:StartQueryExecution` alone,
   because Stage 5's Iceberg `OPTIMIZE`/`VACUUM` runs through it — so a principal in the lake account can
   query any table the catalog exposes and land the result in S3, with the perimeter SCP only stopping
   that write when the destination is outside the organization. **Preventively, that hole is deliberate
   and documented** ([`POLICIES.md`](../../terraform-live/identity/org-policies/POLICIES.md), `awsds-org-scp-ou-data`);
   detecting it is this step's. The signal is a query in the Data Governance account whose principal is
   not the catalog-maintenance role and whose statement is not a table-maintenance one — an inversion of
   the usual alarm, since in every *other* account Athena is the normal way to read.
6. Only then evaluate whether a third-party DLP agent adds anything the above does not cover.

**Deliverables:** a documented threat model with the control that addresses each item — and, for the items
where no control exists, an explicit statement that the risk is accepted rather than a control that was
never built; alarms that fire on a simulated exfiltration attempt. **The threat model carries a reachability
row per governed resource** — who outside the organization can reach it, and who inside can — answered by
Access Analyzer for the resource types it supports, and by **nothing at all for EFS** (D24), which is a
sentence to write down rather than a column to leave blank.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
