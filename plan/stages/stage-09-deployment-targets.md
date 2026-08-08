# Stage 9 — Deployment target platforms, producer path

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3, 5, 8. |
| **Consumes** | [D14](../decisions/D14-supply-chain-account.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D20](../decisions/D20-staging-account.md), [D22](../decisions/D22-data-governance-account.md), [D25](../decisions/D25-drop-box-consumer.md), [D28](../decisions/D28-workflow-contract.md) |
| **Proves** | [INT-03](../integrations.md), [INT-04](../integrations.md), [INT-05](../integrations.md), [INT-06](../integrations.md), [INT-07](../integrations.md), [INT-10](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** what Staging and Production need in order to run promoted artifacts, and the governed
write path through which Production becomes the lake's producer (D22).

**Prerequisites:** Stages 3, 5, 8.

**Scope change (D14):** the Production *networking* moved to Stage 3 and the *registries* to Stage 7, both
because GitLab needed them earlier. What remains here is the data platform and the sharing model — which
is the interesting part anyway.

**Scope change (D17, D18):** this stage also builds the two things those decisions put in Production — the
SageMaker *runtime* (Model Registry and job execution roles, with no domain) and the data scientists'
compute-free access to this account. Both belong here rather than in Stage 10, because Stage 10 consumes
the registry and would otherwise have to create it in passing.

**Scope change (D20):** and the Staging data platform, which is what the promotion chain built in Stage 8
actually deploys against. Note the ordering this creates: Stage 8 builds the chain, Stage 9 gives it
somewhere real to run, and the end of this stage is where the first fully meaningful promotion happens.

**To execute:**

1. Apply the `production/data/` consumer slice, same module as the Stage 5 consumer side: application
   output buckets, the Production Athena workgroup, and LF resource links to the Data Governance share.
   The lake itself is not here (D22) — Production's `data/` holds what applications *produce locally*
   (logs, intermediates, outputs pending curation), not governed tables.
2. **The producer path (D22, INT-03).** Grant the Production job execution role the Lake Formation
   read **and governed-write** share from Data Governance: production ETL writes curated tables through
   LF-aware engines, cross-account, and this is the only path by which governed data is ever written.
   Prove it with a job that writes a curated table, and prove its converse — the same role cannot
   `PutObject` into the lake buckets directly.
   **The ingestion drop-box pickup runs here too (D25, INT-10)**, because it is the same producer
   path applied to a file a human dropped rather than to an upstream feed: a job under the Production
   execution role reads the dated prefixes in Data Governance, curates the contents into a governed table
   through the LF write, and deletes what it consumed. Data Governance cannot host this job — its OU SCP
   denies compute, Glue jobs included — so if it does not run in Production it does not run anywhere.
   Verify the KMS grant explicitly: an `AccessDenied` on the drop-box key surfaces as an S3 error.
3. **`production/sagemaker/` — the runtime half of D17, layer `[P]`.** Model package groups for the Model
   Registry (**`aws_sagemaker_model_package_group`**, one per application or model family — D28 item 6),
   and the execution role that pipeline-submitted training, processing and batch-transform jobs
   assume. No domain, no user profiles, no interactive anything. **Each package group carries a resource
   policy written here, not improvised in Stage 10:** the pipeline's Production role registers and
   approves versions; the Staging deploy role reads approved versions (INT-07); the Development side
   reads status and nothing else (INT-04). The registry lives here rather than in
   an Interactive account because it is the promotion boundary: a model version is *approved*, and the
   approval has to sit on the far side of the gate from the person who trained it. A model package group
   costs nothing at rest, which is why this is `[P]` and not part of the `[E]` orchestration slice.
4. **The Staging data platform (D20)** — `terraform-live/staging/data/`, from the same modules again, plus
   `terraform-live/staging/sagemaker/` holding job execution roles and nothing else (no domain, no Model
   Registry; the approved model version is read from Production's).
   Its catalog **mirrors the lake's schema** (D22) — same databases, same table definitions, same
   LF-Tags — held locally, with sampled or synthetic content, because a staging run that fails on a schema
   difference tests the staging environment rather than the application.
   Its **data is sampled or synthetic and is never a copy of the lake, and Staging is not on the Data
   Governance share (D20/D22)**. This is the part to hold the line on: Staging is a deployment target
   where the data scientists have read access (D18) and where automated tests run unattended, so a share
   or a copy would make the least-defended account the cheapest route to governed data. If a test
   genuinely needs production-shaped volume, generate it; if it needs production *values*, the test
   belongs in Production behind the approval gate, not in Staging.
   An earlier version of this plan put a `staging` Glue database inside the **Production** account as a
   stand-in for this. It is removed: it shared an account, an IAM surface and a blast radius with the very
   thing it was meant to de-risk, so it could catch a schema or logic error but never a permission one —
   which is the failure class a cross-account promotion actually produces.
5. **Apply the `DataScientistProdAccess` and `DataScientistStagingAccess` permission sets (D18)** created
   by hand in Stage 1b step 3, now from `terraform-live/identity/`, together with the Production Athena
   workgroup they depend on (`EnforceWorkGroupConfiguration = true`, scan limit, results to a
   per-principal prefix). The Staging set carries no write grant at all — confirm that in the plan output,
   not only in the intention.
6. **The production debugging escape hatch**, designed here rather than improvised later (D17): a
   time-boxed elevated role in Production, assumable only with an approval from `deployment-managers`, that grants
   read access to job inputs and outputs for a bounded window. CloudTrail alarm on every assumption of it.
   This exists because "nobody ever needs to look at production interactively" is not true, and an
   undesigned need becomes a permanent permission.
7. Cross-account IAM: the two deploy roles from Stage 8 step 3 (`awsds-deploy-staging` and
   `awsds-deploy-prod`, both assumed by the runner in Production), and the KMS key grants that let Staging
   decrypt what it pulls from the Production ECR.
8. **Verify the boundary rather than declare it.** Confirm, each as a test with its result recorded:
   - from a **Sandbox or Development** session — no deployment target's infrastructure can be changed; a
     lake table can be read through the share but not written (the governed write belongs to Production's
     job role alone, D22); a write to an S3 bucket outside the organization is denied (`plan/architecture.md` §4.2); the
     drop-box in Data Governance accepts a `PutObject` and refuses the matching `GetObject`;
   - from a **Production** session as the data scientist (D18) — no compute can be started
     (`sagemaker:CreateTrainingJob`, `glue:StartJobRun` both denied); Athena runs and its result lands in
     the per-principal prefix even when the client asks for somewhere else; and the reach does not extend
     to anything not enumerated in the permission set;
   - from a **Staging** session as the data scientist (D18, D20) — everything readable, nothing writable,
     including the buckets the pipeline writes to;
   - under the **Production job role** — a curated table written through the LF share succeeds, and a
     direct `PutObject` to the same bucket fails (step 2's pair);
   - and the two `plan/integrations.md` traps — that S3 access from a laptop over the VPN survives the `aws:SourceVpce`
     condition (INT-05), and what fraction of the S3 **console** survives it (INT-06).

**Deliverables:** the data scientist reads a lake table from Studio in both Interactive accounts and is
denied on write; the same user, signed in to Production, can inspect a failed job and query through Athena
but cannot start compute; a production job writes a curated table through the governed path and the pandas
test still fails everywhere; the promotion chain from Stage 8 runs end to end against a real catalog in
Staging and then in Production; and every verification in step 8 is written down with its outcome —
including the ones that fail.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
