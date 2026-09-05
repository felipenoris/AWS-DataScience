# Stage 9 — Deployment target platforms, producer path

| | |
|---|---|
| **Status** | not started — **re-scoped and re-reviewed 2026-09-05**. (1) **Staging is no longer a vend** — it is the renamed `Development` ([6b](stage-06b-development-becomes-staging.md)), so every "after 6b" gate in this file is unblocked and the account arrives with a VPC on **10.50.0.0/16**, its `[P]` S3 gateway endpoint intact, and a `[E]` endpoint set to build. (2) **It arrives carrying things D20 forbids** — a lake share, resource links, a read-write persona — and 6b removes them; `DT-8` is this stage's proof that the conversion was complete, and it is answerable for the first time. (3) **The Staging data CMK is created here, under its own name** (`alias/awsds-staging-data`); the account's old `dev`-named key is destroyed at 6b rather than renamed. (4) **Staging peers with `VPC-Networking` only** (D20 amended): no default route, an explicit-proxy client like every other spoke. (5) **The off-VPC job deny must move from the personas to the ROLES.**
`DenySageMakerJobsOffVpc` and its instance-type ceiling are attached to the six persona permission sets —
human sessions — and a pipeline-submitted job runs as a **job-execution role**, which carries neither. That
was survivable while every account had a NAT and a route; under [D38](../decisions/D38-single-egress-hub.md)
it is the one compute in the estate that could still reach the internet unproxied, in the accounts that hold
deploy credentials. So this stage attaches the same two statements as a **permissions boundary** on
`awsds-staging-job-exec` and `awsds-prod-job-exec` (and on the deploy roles that may pass them), and
`DT-*` reads the boundary back per role with `get-role` — never `list-roles`, which omits it by documented
contract. **Serverless inference has no VPC configuration at all**: it is either a named exception with its
own row, or `sagemaker:CreateEndpointConfig` is denied without one. (6) **The SageMaker runtime is the whole of its compute** — job execution roles, Pipelines, batch transform, the Model Registry consumer and, from Stage 10, a `staging/orchestration/` slice; no domain, no space, no interactive surface, and none of those APIs needs a domain object. — *earlier (2026-08-16 and twice on 2026-08-19, against the AWS documentation and what Stage 5 measured):* the deploy roles, the deploy runner and INT-07's image half are **Stage 8's**; a cross-account ECR pull **needs no KMS grant** (ECR decrypts through its own grants) while a cross-account model *deployment* needs three resource policies; an enforced workgroup has **one** result location, so the per-principal prefix was unbuildable and within-persona visibility is a recorded limit; the LF grant is the documented **two steps**; the `DataLakeSettings` apply is Recipe D's two steps in **both** consumer accounts and the `Parameters` hazard is **symmetric** (read each account's own map first); the re-grant is a **DESCRIBE-plus-target pair**, whose missing half shows as *no database visible at all*; and the LF half of `production/data/` is a **`consumer-data` call**, not a third authoring — with the outputs bucket written beside it |
| **Prerequisites** | Stage 3 — `production/foundation/` (VPC, the `[P]` gateway endpoint, KMS). Stage 5 — the lake, the LF settings under `DL-5`'s guard, the drop-box statements written against this stage's role name. **Stage 8 pass 1** — step 3's resource policies name `awsds-deploy-prod` and `awsds-deploy-staging`, and a resource policy naming a principal that does not exist fails at put time; the full chain only for pass 5's promotion. **6b** — the account is `Staging`, in `Workloads`, on 10.50.0.0/16, its tree at `terraform-live/staging/`. **6c** — Staging peers with `VPC-Networking` only, has no default route, and reaches AWS through its own endpoints. Nothing here waits on a quota; **passes 4-5 are gated by 6b, which runs long before this stage** |
| **Consumes** | [D13](../decisions/D13-lake-formation-enforcement.md), [D14](../decisions/D14-supply-chain-account.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D20](../decisions/D20-staging-account.md), [D22](../decisions/D22-data-governance-account.md), [D25](../decisions/D25-drop-box-consumer.md), [D28](../decisions/D28-workflow-contract.md), [D31](../decisions/D31-approver-read.md) |
| **Proves** | [INT-03](../integrations.md) **the write share** — the two read shares are Stage 5's; [INT-05](../integrations.md) (the Production and laptop branches); [INT-06](../integrations.md); [INT-07](../integrations.md) **in part** — the model-registry read half, **which absorbed INT-04 at 6b** (the image half is Stage 8 step 3.2's); [INT-10](../integrations.md) **the pickup half** — the writer and maintenance halves are Stage 5's |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** what Staging and Production need in order to run promoted artifacts, and the governed write
path through which Production becomes the lake's **only** producer (D22). Stage 8 built the promotion
*machinery* against an application that touches no data; this stage gives it something real to deploy
against, and its end is the first fully meaningful promotion. **Scope (D14):** Production's networking went
to Stage 3 and the registries to Stage 7; the deploy credential layer is Stage 8's. What remains here is
the data platform, the SageMaker runtime and the sharing model.

## What this stage builds, and in which accounts

| Where | What | Layer |
|---|---|---|
| `production/sagemaker/` (new) | Model Registry: package groups + **resource policies** (D28 item 6); `awsds-prod-job-exec`; the `awsds-prod-debug` escape hatch + its alarm | `[P]` |
| `data-governance/data/` (amended) | the Production share: LF read **+ governed write**, granted *with grant option* to the Production account (INT-03's last third) | `[P]` |
| `production/data/` (new) | the `consumer-data` call — LF resource links + local regrants, the account's LF settings, the account data CMK — plus the outputs bucket written beside it. **NOTE 2026-08-26: `consumer-data-v0.6.0` no longer provides a derived zone or a workgroup** (D19 revised — the Interactive zone re-homed onto the SMUS project path; Production has NO SMUS, D28). Where THIS account's query results land — a stage-authored results bucket + workgroup beside the call, or nothing — is **this stage's to re-decide at its revision**; `aws/deploytargets.py` carries the same dated note | `[P]` |
| `staging/data/`, `staging/sagemaker/` (new) | the catalog mirror with sampled/synthetic content; job execution roles and nothing else. **NOTE 2026-08-26, the same one the `production/data/` row carries**: Staging has no SMUS either (D17/D28 — the runtime without the domain), so the re-homed zone does not exist here, and step 4.2's enforced workgroup has had **no supplier and no named result location** since `consumer-data-v0.6.0`. One re-decision covers both deployment targets | `[P]` |
| `production/workloads-egress/` (amended), `staging/egress/` (amended) | the endpoints a job needs where there is no default route: `sagemaker.api`, `sagemaker.runtime`, `sts`, `logs`, `glue`, `athena`, `ecr.api`, `ecr.dkr`, `kms`, `secretsmanager` — **with the job subnets pinned to the endpoints' AZ** (6c step 5.4's `sagemaker.runtime` affinity) | `[E]` |
| `identity/sso/` (amended) | `DataScientistProdAccess`'s owed allows: the workgroup, the named prefixes, the debug-role assumption | `[P]` |
| `scripts/` | `backend.py`/`layers.py` rows for the four new slices (all `[P]` — `make up`/`down` never touch them) | — |

**Contracts this stage fixes, each read by `./aws/deploytargets.py` so a rename fails in a check rather
than in a later stage:** the job role **`awsds-prod-job-exec`** (the exact name Stage 5 step 1.4's
reader-deleter statement and drop-box KMS grant carry), the workgroup **`awsds-prod-athena`**, the buckets
**`awsds-prod-outputs`**/**`awsds-prod-derived`** (the module's derived zone — `results/` is a prefix family in it, never a bucket of its own), the package groups **`awsds-prod-model-<app>`**,
the debug role **`awsds-prod-debug`** with rule **`awsds-prod-debug-assume`**, and Staging's
**`awsds-staging-job-exec`**/**`awsds-staging-athena`**.

```mermaid
flowchart LR
    subgraph DG["Data Governance (D22)"]
        LAKE["curated · Iceberg"]
        BOX["drop-box (D25)"]
    end
    subgraph PRD["Production"]
        JOB["awsds-prod-job-exec [P]<br/>no S3 on lake prefixes (D13)"]
        REG["Model Registry [P]<br/>groups + resource policies"]
        WG["awsds-prod-athena [P]<br/>enforced · scan limit"]
        OUT["outputs + results [P]<br/>own CMK (D31)"]
        DBG["awsds-prod-debug [P]<br/>closed by default · alarmed"]
    end
    subgraph STG["Staging"]
        MIR["catalog mirror · sampled data<br/>awsds-staging-job-exec only"]
    end
    JOB ==>|"LF governed write · INT-03"| LAKE
    JOB ==>|"read + delete · INT-10"| BOX
    JOB --> OUT
    DS["data scientist (D18)"] -->|"Athena, read only"| WG
    DS -.->|"approved window only"| DBG
    SDR["awsds-deploy-staging (St.8)"] -.->|"read approved version<br/>INT-07's registry half"| REG
```

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits (Terraform, scripts) and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — only after the user authorizes that specific action in chat, with the SSO user/account/permission set stated first |
| **[user]** | behavioural proofs run from a laptop session, approvals, and every log entry |
| **[pipeline]** | Stage 8's chain re-run in pass 5 — triggered by the user's tag, credentialed by Stage 8 step 4 |

Hand applies run as the **infrastructure user**: `awsds-infra-data` (the grantor half),
`awsds-infra-prod` (both Production slices), `awsds-infra-staging`, `awsds-infra-identity`
(the `identity/sso/` amendment). The persona proofs of step 8 sign in as the **data-science user** through
the set under test — the one stage so far whose evidence is mostly *another* persona's sessions.

## Step numbers are identifiers, not an order

These numbers are **stable addresses cited from other files** — step 3 from Stage 10 step 5 and D28
item 6 (the registry Stage 10 consumes rather than invents); step 2 from Stage 5 step 1.4 and INT-10
(the pickup half); step 5 from `identity/sso/README.md`'s owed table; step 6 from D17 and
`docs/ORGANIZATION.md` (the deployment manager's approval). They do not change. The sequence to work in is
**six passes**:

| Pass | # | What | Slice · layer | Applied as |
|---|---|---|---|---|
| **0** | 7 | consume Stage 8's credential layer; the three preflight readings | readings, no build | — |
| **1** | 3, 6 | the runtime: registry + resource policies, the job role, the escape hatch | `production/sagemaker/` `[P]` | `awsds-infra-prod` |
| **2** | 2 | the share, grantor side — read + governed write to Production | `data-governance/data/` `[P]` | `awsds-infra-data` |
| **3** | 1, 2 | the consumer slice, then the producer proofs (the write pair, the pickup) | `production/data/` `[P]` | `awsds-infra-prod` |
| **4** | 5, 6, 8 | the persona layer and the boundary sweep | `identity/sso/` `[P]` + sessions | `awsds-infra-identity`; persona sessions |
| **5** | 4, 8 | the Staging platform, then the end-to-end promotion | `staging/data/`, `staging/sagemaker/` `[P]` | `awsds-infra-staging`; the pipeline |

Pass 1 precedes pass 2 because the grantor's regrant target and Stage 5's drop-box statements both name
the job role; pass 3 cannot precede pass 2 (a resource link to a share that does not exist resolves
nothing — Stage 5's rule, repeated for the third consumer). **Pass 5 waits on nothing but pass 4 and
Stage 8's chain**: 6b delivered the account several stages earlier.

**One consequence of that order, made explicit 2026-08-19 rather than met at the keyboard:** Production
becomes a Lake Formation account only at **pass 3** (1.3 names its first data lake administrator), so
**pass 2's post-grant reading is a RAM reading and not a catalog one** — the share is *held* before it is
*visible*, and the gap between the two is a pass wide. 2.2's callout carries the discriminator. Moving
1.3's settings into pass 1 would close the gap and is deliberately not done: it would split one slice
across two applies to buy nothing except an earlier confirmation.

---

## To execute

### 1. `production/data/` — the consumer slice, layer `[P]`

**Action:** give Production the data platform D18 and the producer path stand on — output buckets, the
enforced Athena workgroup, and the lake reached through resource links. **Why:** applications produce
locally (logs, intermediates, outputs pending curation) and humans read locally (D18); the lake itself is
never here (D22), so everything in this slice is either *local output* or a *pointer* to the share.
**Explanation:** same module family as Stage 5's consumer side, third instantiation — which is what makes
the sharing shape a pattern rather than an event. The LF settings in *this* account are written under the
same discipline `DL-5` imposes in Data Governance: a `DataLakeSettings` apply replaces the whole
structure, in every account that has one.

- **1.1 — [Claude] Write the outputs bucket beside the `consumer-data` call**: `awsds-prod-outputs`
  (application outputs; model artifacts under `models/<app>/` — step 3 points the registry here) from the
  `s3-bucket` module — versioning, `prevent_destroy`, BPA, SSE-KMS with **`alias/awsds-prod-data`**, the
  account data CMK the `consumer-data` call creates
  (decision 1; D31's argument: a key the Staging set and both approver sets cannot decrypt is what makes
  "read-only means read-only" expressible), **and its key policy written in the D31 shape pass 4 applied**
  — the account root keeps administration and holds no cryptographic action, so delegation to IAM is
  impossible and an enumerated statement has to name all three principals, conditioned
  `kms:ViaService = s3.<region>.amazonaws.com` — and **two of the three write**, so the statement is not
  `Decrypt` alone: `awsds-prod-job-exec` writes model artifacts (3.1) and `DataScientistProdAccess` stages
  Athena results as the caller (5.1), both needing `kms:GenerateDataKey` to write and `kms:Decrypt` to read
  back or to finish a multipart upload; only `awsds-prod-debug` is read-only.
  Without that statement the `kms:Decrypt` granted at 5.1 and 6.1 reaches nothing — Lesson 28's
  intersection, and the failure Stage 5 pass 4c paid for on the drop-box. **The module's single
  `data_scientist_role_arn` cannot express three readers**: the key statement above is a module change
  under Recipe B, applied to every consumer.
  **The results zone is deliberately not a bucket of its own**: it is the `results/` prefix family of
  `awsds-prod-derived`, which arrives with the `consumer-data` call — the shape passes 4a/4b applied
  twice, 30-day expiry included ([`docs/GOVERNANCE.md`](../../GOVERNANCE.md) §Derived zone owns it).
  Bucket policy on `awsds-prod-outputs`: the perimeter branches from Stage 5 step 1.3
  (`aws:SourceVpce` = the `[P]` gateway endpoint from `production/foundation/` outputs, `aws:SourceIp` =
  the WireGuard EIP list, the `aws:ViaAWSService` carve-out — Athena writes results as the caller).
- **1.2 — [Claude] The workgroup `awsds-prod-athena` arrives with the `consumer-data` call**:
  `enforce_workgroup_configuration = true` (the console's "override client-side settings" — documented
  to replace the client's result location, encryption and expected-bucket-owner with the workgroup's),
  result location `s3://awsds-prod-derived/results/`, SSE-KMS with the account data CMK,
  `bytes_scanned_cutoff_per_query` set by the module
  (decision 2). **One enforced location, not one per principal** — within-persona visibility of query
  results is a stated limit (risk 6), not a defect to hide.
- **1.3 — [Claude] Write the LF plumbing**: the account's `aws_lakeformation_data_lake_settings`
  (admins = this account's `InfrastructureAccess` role, create-default permissions emptied — Stage 5
  step 5.2's kill, repeated here — and **`parameters` carried explicitly from a read**, 1.5); **resource
  links** to the shared `raw` and `curated` databases; a local Glue database `app_outputs` for what
  applications write to 1.1. The **regrants** are 2.3's — they need the share first.

  > **THIS SLICE APPLIES IN TWO STEPS, AND THE PLAN CANNOT TELL YOU WHY — measured in Data Governance
  > on 2026-08-18 (Stage 5 pass 1) and inherited here unchanged.** Both `create_*_default_permissions`
  > blocks are **Computed**: omitting them plans as `after_unknown` and an explicitly empty list is not
  > expressible, so whether omission *clears* them or merely *leaves them alone* is a provider property
  > no plan states — while the difference is permanent, because those defaults act **at creation time**.
  > A resource link and `app_outputs` are both catalog objects created *in this apply*; if the defaults
  > still stand when they are created, they are born deferring to IAM and clearing the settings
  > afterwards does not reach them. **So: apply the settings alone under `-target`, read the account
  > back (`DT-5`, and `DL-6`'s reading applied to this account), revoke `IAMAllowedPrincipals` if it is
  > still there, and only then apply the rest.** Lesson 27; the procedure is **Recipe D** in
  > [`docs/plan/runbooks/terraform-changes.md`](../runbooks/terraform-changes.md), which exists because
  > of this exact case. **The same applies to `staging/data/` (4.1)** — to every account that gains this
  > resource, never just the one in front of you.
- **1.4 — [Claude] Write the machinery rows**: `backend.py`/`layers.py` gain `production/data/` and
  `production/sagemaker/` (both `[P]`, outside every `make up`/`down` path), and the slice reads the
  gateway-endpoint ID through `terraform_remote_state` from `production/foundation/` — never a pasted ID
  (Lesson 3). **`production` also joins `DATA_CONSUMERS`** so the slice receives its `lake` map — but
  **read what else that list feeds first (Stage 5 pass 4c)**: it is emitted a third time as
  `data_consumers` to `identity/sso/`, whose `locals.tf` folds every consumer's workgroup and
  derived-bucket ARN into **`DataScientistAccess`** — the Interactive persona. Production must not land in
  that policy, and step 5.1 grants those ARNs to `DataScientistProdAccess` separately. So **split the
  list** — a lake-consumer list for the `lake`/share emission, a narrower persona list for
  `identity/sso/` — before adding the row, and re-plan `identity/sso/` to confirm `No changes`.
- **1.5 — [Claude⚡] Apply as `awsds-infra-prod`, bracketing the LF settings with two readings**:
  `aws lakeformation get-data-lake-settings --profile awsds-infra-prod` before the first apply and again
  after — Production's `Parameters` map is defended nowhere until this slice exists, and this apply is
  exactly the operation that can silently reset it (INT-11's failure mode, third account).
  **The before-reading is not a formality and pass 4 is why (2026-08-19):** both Interactive accounts
  turned out to be carrying `CROSS_ACCOUNT_VERSION=4` / `SET_CONTEXT=TRUE` *already*, set by nobody in
  this repository and defended by nothing until the settings resource landed. The values that go into
  `parameters` are copied **from that account's own reading**, never from Data Governance's and never
  from this file. `DL-5` now reports per account, so the regression has somewhere to show up.
  `./aws/deploytargets.py` `DT-5` mechanises the reading from here on.

### 2. The producer path (D22, D25, INT-03, INT-10)

**Action:** grant Production the lake's read **and governed write**, then prove both directions — a
curated table written cross-account through Lake Formation, a direct `PutObject` to the same bucket
denied, and the drop-box pickup that empties the letterbox. **Why:** this is the only path by which
governed data is ever written (D22), and the write grant is INT-03's least-travelled variant — proven
with a job, never assumed. The pickup is the same producer path applied to a file a human dropped
(D25): Data Governance cannot host the job — its OU SCP denies compute — so if it does not run in
Production it runs nowhere. **Explanation:** the grant is the documented two-step. The grantor grants to
the **account** (with grant option); Production's LF admin then **regrants** to the job role locally.
The two-step is what lets Stage 10's per-workflow roles (D28 item 3) receive their own regrants later
without ever touching Data Governance again.

**And the local regrant is itself a PAIR — measured at pass 4, in two accounts, 2026-08-19.** A shared
database reaches a local principal through two permissions that are not interchangeable: `DESCRIBE` on
the **resource link**, which is an ordinary local database object, *and* the permission on the **target**,
addressed through the owner's `catalog_id`. The first is the one that gets forgotten, and its symptom is
the worst kind: the principal sees **no database at all**, holding every permission on the target. Write
both, and read `list-permissions` afterwards rather than the code (pass 4's four rows per account are the
shape).

> **A prerequisite this section silently owed was DELIVERED EARLY, 2026-08-20 (Stage 5, its log's
> entry of that date).** The registration role `awsds-data-lf-registration` — the session every
> LF-vended access to the registered locations runs as, 2.4's job included — shipped **read-only**,
> its `.tf` comment deferring the write half to "Stage 9, which amends this policy (its step 2)".
> **This file never carried that amendment**: the promise existed only at the promising end
> (Lesson 34), and 2.4's write proof would have failed inside the cross-account job with the share,
> the job role and the key all on the suspect list. Stage 5's sample-row load hit the wall first, in
> the one-account configuration, and the ceiling now exists: `registered-locations-write`
> (`s3:PutObject`+`s3:DeleteObject` on the two registered prefixes, `kms:GenerateDataKey`). **Nothing
> here needs to touch it** — 2.1's grants and 2.3's regrants are the per-principal gate under a
> ceiling that is already wide enough, and a 2.4 denial naming `kms:GenerateDataKey` or `s3:PutObject`
> for an `AWSLF-…` session would now mean the ceiling *regressed*, not that it was never built.

- **2.1 — [Claude] Amend `data-governance/data/` with the Production grant**: LF permissions
  `DESCRIBE, SELECT, INSERT, DELETE, ALTER` on the `curated` database and its tables (**`ALTER` is not
  optional** — an Iceberg commit rewrites table metadata, so a write without it fails at the commit, not
  at the first row), granted to the **Production account** with grant option, from the same authored
  share map Stage 5 built. Read side unchanged: `DESCRIBE`/`SELECT` on `raw` too, if the pickup curates
  from it. **Two shapes this inherits from Stage 5 pass 3, both found at that apply:**
  - **the grant option is not this stage's peculiarity.** Every cross-account grant carries it — the
    receiving account's own administrator can only pass on what it received with the option — so 2.3's
    regrant is the ordinary second half of *any* share here, and what stays particular to Production is
    the governed **write** in the permission list, not the option (`docs/GOVERNANCE.md` §Grants);
  - **if these are written as TBAC expressions rather than named resources, the `layer` gate is
    mandatory** (Lesson 29). Stage 5's decided form was `classification ∈ {public, internal}` alone and
    it matched the **drop-box**, whose entire contract is write-never-read-back. The write grant is more
    dangerous in the same direction — a `layer`-less write expression would reach whatever else ever
    carries a matching classification. **Recommended here: named-resource on `curated`**, which is what
    the text above already describes and what decision 5 reserves for enumerated exceptions — a
    single-database, single-account write is exactly that, and it is recorded in the register as one.
- **2.2 — [Claude⚡] Apply as `awsds-infra-data`, inside `DL-5`'s bracket**: read
  `DataLakeSettings.Parameters` before and after (Stage 5 step 5.4's three-reading discipline — this is
  the first `data-governance/data/` apply since the lake was built, and the reset it can cause is
  silent). Then, from Production with a **fresh** session (Lesson 24 — the four-hour CLI cache serves
  stale successes): **Production's RAM holds the new shares**, and **no pending invitation** (`DL-7`'s
  shape; a pending row is INT-11's fallback tax).

  > **WHAT THIS READING MUST *NOT* EXPECT, corrected 2026-08-19 against Stage 5 pass 3's measurement:
  > the shared databases will NOT be visible here, and that is the correct state rather than a failed
  > share.** A receiving account needs **at least one data lake administrator** before a shared resource
  > appears in its catalog at all — and Production has none until **1.3**, which is pass 3, one pass
  > *after* this one. Both Sandbox and Development read exactly this way on 2026-08-19: RAM holding two
  > `ACTIVE` shares each, `glue:GetDatabases` and `list-lf-tags` returning nothing. **The discriminator
  > is therefore the RAM side, not the catalog side** — a share the consumer's RAM does not hold is the
  > real INT-11 failure, an empty catalog before 1.3 is not. `DL-7` was rebuilt on 2026-08-19 to report
  > the two branches separately (it used to return one verdict for both — Lesson 13's family), and
  > `DT-5`'s twin reading inherits the distinction. The catalog-side confirmation belongs at **2.3**,
  > after 1.3 has made `awsds-infra-prod` an admin.
- **2.3 — [Claude⚡] Regrant locally and finish `production/data/`**: as `awsds-infra-prod` (an LF admin
  since 1.3), `aws_lakeformation_permissions` granting the job role `DESCRIBE` on the resource links and
  `SELECT, INSERT, DELETE, ALTER, DESCRIBE` on the shared tables through them.
- **2.4 — [user] Prove the write pair (INT-03)**: run a job under `awsds-prod-job-exec` (a Glue job —
  the engine the pickup and Stage 10's workflows use) that writes a curated Iceberg table through the LF
  share; then, from the same role, a direct `put-object` to the lake bucket — **denied**, because the
  role holds no S3 allow on lake prefixes (D13; the bucket's network branches admit the VPC, so the
  denial is the *identity* side, which is the point). Read both wordings; record both.
- **2.5 — [user] Prove the pickup (INT-10)**: drop a file into the dated prefix from a Sandbox session
  (Stage 5's writer half), run the pickup job under the job role — it reads the prefix, curates into a
  governed table through 2.4's write path, and **deletes what it consumed**. Verify the KMS half
  explicitly: an `AccessDenied` on the drop-box key surfaces as an S3 error naming the object, not the
  key (D25's forgotten half — the grant was written in Stage 5 against this stage's role name; this is
  where a typo in that contract fails).
- **2.6 — [user] Confirm the letterbox asymmetry now closes**: the same Sandbox session that wrote the
  file still cannot `GetObject` it back (Stage 5's deliverable, re-read with the consumer finally
  existing).

### 3. `production/sagemaker/` — the runtime half of D17, layer `[P]`

**Action:** the Model Registry and the execution role pipeline-submitted jobs assume — no domain, no user
profiles, no interactive anything. **Why:** the registry is the promotion boundary: a model version is
*approved*, and the approval must sit on the far side of the gate from the person who trained it — which
is why it lives here and not in an Interactive account, and why each package group carries a resource
policy **written now, not improvised in Stage 10** (D28 item 6). A model package group costs nothing at
rest, so this is `[P]`. **Explanation:** cross-account deployment is documented as three resource
policies — the model package group, the ECR repository of the inference image (Stage 8 step 3.0's grant
covers the repositories), and the S3/KMS of the model artifacts (1.1's bucket and CMK). The group policy
is `aws_sagemaker_model_package_group_policy` (`PutModelPackageGroupPolicy`, ≤ 20 480 bytes).

- **3.1 — [Claude] Write the job role `awsds-prod-job-exec`**: trust policy `sagemaker.amazonaws.com`
  and `glue.amazonaws.com` only — never assumable interactively (D27's shape). Permissions: Glue catalog
  read, `lakeformation:GetDataAccess` (the credential-vending call every LF-aware engine makes), CloudWatch
  Logs, read+write on 1.1's buckets, the drop-box read/delete and its KMS decrypt (the identity half of
  Stage 5's statements — the drop-box is its own bucket, Stage 5 decision 3, so it is the named
  exception), and **no `s3:*` on the four lake buckets** (D13 — 2.4 proves it).
  `iam:PassRole` to it is granted only in Stage 8's deploy roles, scoped by `iam:PassedToService`.
- **3.2 — [Claude] Write the package groups and their resource policies**: one group per application or
  model family — `awsds-prod-model-app-etl` first (D28 item 6). Policy, three statements: **register and
  approve** (`sagemaker:CreateModelPackage`, `UpdateModelPackage`) for `awsds-deploy-prod` alone;
  **read approved** (`DescribeModelPackage`, `ListModelPackages`) for `awsds-deploy-staging`; and
  **read status** for the human readers — principal the **Sandbox** account (INT-04 was merged into INT-07
  at 6b, and the account it named is now Staging, which reads through the deploy role above), conditioned
  on `aws:PrincipalArn` matching the data-science set's reserved-SSO pattern (decision 7's idiom: account
  enumerated, per-account suffix wildcarded; whitelist it in `make check` 9.2 rather than loosening the
  rule).
- **3.3 — [Claude] Write the escape hatch** (step 6's resources — same slice, same apply).
- **3.3a — [Claude] Complete `production/workloads-egress/`** with the same endpoint list 4.3a gives
  Staging — **`VPC-Workloads` is where Production's jobs run**, and 6c created that slice empty precisely so
  this stage could fill it. A job in a VPC with no default route and a missing endpoint fails as a proxy
  403 naming the host, which is readable; a job with **no** proxy either, which is the runtime case, simply
  cannot reach the service at all.
- **3.5 — [Claude] Move the off-VPC job deny from the personas to the ROLES, as a permissions boundary.**
  `DenySageMakerJobsOffVpc` and its instance-type ceiling are attached to the **six persona permission
  sets** — human sessions — and a pipeline-submitted job runs as a **job-execution role**, which carries
  neither. That was survivable while every account had a NAT and a route; under
  [D38](../decisions/D38-single-egress-hub.md) an unconstrained job role is the one compute in the estate
  that could still reach the internet unproxied, in the two accounts that hold deploy credentials. Write the
  same two statements as a managed policy **`awsds-job-exec-boundary`**, attach it as the
  `PermissionsBoundary` of `awsds-prod-job-exec` (3.1) and `awsds-staging-job-exec` (4.3), and add
  `iam:PermissionsBoundary` as a condition on the deploy roles' `iam:CreateRole`/`PassRole` so a pipeline
  cannot mint a job role without it. **`terraform-modules/sagemaker-denies/` already holds both statement
  bodies** — this is a second consumer of one source, not a second copy (Lesson 33).
- **3.6 — [Claude] Read the boundary back with `get-role`, never `list-roles`** — the API omits
  `PermissionsBoundary` from the list form by documented contract, which is the same trap `US-8` exists for
  on the D13 boundary. `./aws/deploytargets.py` gains **`DT-9`**: every role whose name ends `-job-exec`
  carries the boundary, read per role.
- **3.7 — [Claude reads, user decides] Settle serverless inference, which has no VPC configuration at
  all.** An endpoint configuration in serverless mode takes no `VpcConfig`, so the deny above cannot bind
  it and the boundary cannot save it. Two honest shapes, and the recommendation is the second: **(a)** a
  named exception with its own row in `docs/AWS_STATE.md` and a trigger to revisit; **(b)** deny
  `sagemaker:CreateEndpointConfig` **without** a `VpcConfig` in the `Workloads` OU SCP, so serverless
  inference simply does not exist in this estate until somebody argues for it. **Recommended: (b)** — a
  capability nobody has asked for is cheaper to refuse than to fence.
- **3.4 — [Claude⚡] Apply as `awsds-infra-prod`** (after 3.5-3.7 are written, so the boundary lands with
  the role rather than being added to a role that already ran without it), then **[user] prove the registry
  gate**: from a
  **Sandbox** session, `DescribeModelPackageGroup` answers while `CreateModelPackage` and
  `UpdateModelPackage` are denied; an approval succeeds under `awsds-deploy-prod` and under nothing else.
  Read the wordings — the denial must name the resource policy's absence of a grant, not a network
  condition.

### 4. The Staging data platform (D20) — layer `[P]`

**Action:** the environment the promotion chain actually deploys against — a catalog that mirrors the
lake's schema, holding sampled or synthetic content, and job execution roles. **Why:** a staging run that
fails on a schema difference tests the staging environment rather than the application; and **Staging is
not on the Data Governance share** (D20/D22) — it is the least-defended account with unattended tests and
data-scientist read access, so a share or a copy would make it the cheapest route to governed data. An
earlier stand-in (a `staging` database inside Production) is gone: it shared an IAM surface with what it
de-risked and could never catch a permission error (Lesson 2). **Explanation:** if a test genuinely needs
production-shaped volume, generate it; if it needs production *values*, the test belongs in Production
behind the approval gate.

- **4.0 — [Claude] Read what 6b and Stage 8 already delivered, and build only the gap**: 6b brought the
  bootstrap, `foundation/`, `egress/`, the tree and the SSO assignment; Stage 8 step 3.0 brought
  `awsds-deploy-staging` and the INT-07 image grant. **This stage owns two things nobody else does** — the
  account data CMK `alias/awsds-staging-data` (created here, under its own name; 6b destroyed the old
  `dev`-named key rather than renaming it) and the `staging/{data,sagemaker}/` slices below. Run
  `./aws/AZs.py` and `./aws/account-bpa.py` once as the standing post-conversion readings.
- **4.1 — [Claude] Write `staging/data/`**: local Glue databases mirroring the lake's — same database
  and table names, same Iceberg definitions, same LF-Tag keys and values (LF-Tags are account-local, so
  the mirror recreates the ontology) — **instantiated from the same versioned schema source as the
  lake's tables** (decision 3; two hand-typed copies drift, and the drift is the false test failure this
  account exists to prevent); content buckets `awsds-staging-data` under a Staging CMK; the LF settings
  under 1.3's discipline (parameters carried, defaults killed) — **including its two-step apply**, and
  this is the account where getting it wrong is least visible: the mirror's whole point is that its
  databases look like the lake's, so a mirror database born deferring to IAM would pass every shape
  comparison `DT-8` makes while enforcing nothing. **No resource link to Data Governance
  anywhere** — its absence is a control, and `DT-8` fails if one appears.
- **4.2 — [Claude] Write the workgroup `awsds-staging-athena`**: enforced, results local, scan limit —
  **for the integration tests and the deployed application, not for people**:
  `DataScientistStagingAccess` carries no Athena at all (Stage 2 wrote it that way — a query writes its
  result somewhere, and this set writes nothing). **"results local" names no bucket, and since
  2026-08-26 nothing supplies one** (`consumer-data-v0.6.0` removed the derived zone and the workgroup
  from the module — [D19 revised](../decisions/D19-derived-zone.md)). An enforced workgroup cannot exist
  without an output location, so **this step's destination is part of the same re-decision as the
  `production/data/` row's**, and it is the half that was never written down even before the removal.
- **4.3 — [Claude] Write `staging/sagemaker/`**: `awsds-staging-job-exec`, same trust shape as 3.1, **3.5's
  permissions boundary attached**, no registry, no domain — the approved model version is read from
  Production's registry. **`VpcConfig` is mandatory on every job this role can run**, which is what the
  boundary enforces; the subnets are Staging's private tier and the security group its own.
- **4.3a — [Claude] Complete Staging's `[E]` endpoint set in `staging/egress/`**, because with no default
  route a missing endpoint is the whole failure: `sagemaker.api`, `sagemaker.runtime`, `ecr.api`,
  `ecr.dkr`, `sts`, `logs`, `monitoring`, `kms`, `glue`, `athena` and `secretsmanager`, over the `[P]` S3
  and DynamoDB gateway endpoints 6b preserved. **Pin the job subnets to the endpoints' AZ** — 6c step 5.4
  settled that `sagemaker.runtime` *"must be activated in the Availability Zone of your client"* or the
  failure is a DNS error rather than a cross-AZ charge, and D9 keeps this estate single-AZ. The `NO_PROXY`
  the job containers carry is generated from **this list**, per 6c step 5.6, so a service with no endpoint
  fails as a proxy 403 naming the host rather than as a hang.
- **4.4 — [Claude] Write the sample-data seed**: a job in the `app-etl` repository generating the
  sampled/synthetic content into `awsds-staging-data` — owned by the repository so the pipeline can
  refresh it, never copied from the lake (D20's line to hold).
- **4.5 — [Claude⚡] Apply both slices as `awsds-infra-staging`**, machinery rows included.
- **4.6 — [Claude⚡] Amend step 3's resource policies with the Staging principals** (as
  `awsds-infra-prod`), and the artifact-bucket/CMK read for `awsds-deploy-staging` and
  `awsds-staging-job-exec` — the documented third leg of cross-account deployment (1.1's bucket, not
  ECR: ECR needs no KMS grant for pulls). **[user]** Prove INT-07's registry half: a
  `DescribeModelPackage` of an approved version from the Staging role answers.

### 5. The persona layer (D18) — `identity/sso/` amended

**Action:** deliver the allows `identity/sso/` records as owed by this stage, and read back what was
already built. **Why:** the sets were written narrow in Stage 2 with every object-scoped allow deferred
to the stage that creates the object (guessing an interface is what the slice refuses to do); this stage
creates the objects. **Explanation:** resource ARNs interpolate the account id from the organization
data source the slice already uses — never a literal id (`CLAUDE.md`), never a wildcard account
(conventions §6).

- **5.1 — [Claude] Amend `DataScientistProdAccess`**: `athena:StartQueryExecution`,
  `GetQueryExecution`, `GetQueryResults`, `StopQueryExecution` on the `awsds-prod-athena` workgroup ARN
  alone; `s3:GetObject` on the **enumerated** application-output prefixes; the derived-zone
  read/write Athena performs as the caller (`GetBucketLocation`, `ListBucket`, `PutObject`, `GetObject`
  on `awsds-prod-derived` — pass 4c's statement family, extended to the third consumer); `kms:Decrypt`
  on the account data CMK (1.1); `sts:AssumeRole` on exactly the
  `awsds-prod-debug` ARN (step 6). The `DenyProductionControlPlane` families are untouched — they
  deliberately do not name `athena:StartQueryExecution`.
- **5.2 — [Claude] Verify `DataScientistStagingAccess` by reading, not by trusting the intention**
  (Lesson 22): `DenyEveryWrite` present, no Athena statement anywhere, nothing this stage adds. **Its
  assignment already exists** — 6b assigned it in the same sitting that removed `DataScientistAccess` from
  the account.
- **5.3 — [Claude⚡] Apply as `awsds-infra-identity`**; `terraform output inline_policy_bytes` still
  under the ceiling.
- **5.4 — [user] Prove the workgroup boundary and the negatives**, signed in as the data-science user
  through `DataScientistProdAccess`: a query that asks for a different `OutputLocation` runs and its
  result lands under the enforced location anyway (the documented override — verification (vi)); a query
  over the scan limit is cancelled; `sagemaker:CreateTrainingJob` and `glue:StartJobRun` are denied
  naming the set's own deny; and nothing outside the enumerated prefixes answers.

### 6. The production debugging escape hatch (D17) — designed here, not improvised later

**Action:** a time-boxed elevated role in Production — `awsds-prod-debug` — that grants read access to
job inputs and outputs for a bounded window, assumable only while a window the **deployment manager**
approved is open, with an alarm on every assumption. **Why:** "nobody ever needs to look at production
interactively" is not true, and an undesigned need becomes a permanent permission. **Explanation:** its
shape is imposed rather than chosen — `DenyInteractiveSageMakerSurface` (`awsds-org-scp-ou-workloads`)
denies `CreateSpace`, `CreateApp`, `StartSession` and `CreatePresignedDomainUrl` with no principal
carve-out, so this role can only ever be read-by-API; the pressure toward "a notebook in Production,
just this once" has nowhere to go, and the correct response to that failure is to keep the shape, not to
amend the OU document. The builder is outside every claim here (Lesson 18): what watches the role is
detective — the alarm, and CloudTrail.

- **6.1 — [Claude] Write the role**: permissions — `s3:GetObject`/`ListBucket` on 1.1's buckets, logs
  read, `sagemaker:Describe*`/`List*`, `kms:Decrypt` on the 1.1 CMK; **no lake reach of any kind** (no
  `GetDataAccess`, no grant through 2.3). Trust — the `DataScientistProdAccess` reserved-SSO role
  (resolved in-account via `data.aws_iam_roles`, never a pasted suffix) **and**
  `Condition: DateLessThan aws:CurrentTime = var.debug_window_end`, whose default sits in the past: the
  role exists and is unassumable at rest. `max_session_duration` 1 hour.
- **6.2 — [Claude] Write the alarm**: an EventBridge rule `awsds-prod-debug-assume` on the CloudTrail
  `AssumeRole` event for this role — **every** assumption, not just misuse — to the Stage 1b SNS
  pattern.
- **6.3 — [user] Operate it as designed, once, to prove it**: the deployment manager approves in
  writing (the log), the window variable is set and applied (`[Claude⚡]` as `awsds-infra-prod`), the
  assumption succeeds and the alarm fires; after the window, the same assumption is denied; a
  `CreateSpace` under the role is denied naming the Workloads OU policy. Reverting the variable closes
  the window in the same sitting.

### 7. Consumed from Stage 8 — readings, not builds

**Action:** read what the credential layer already provides before building anything that overlaps it.
**Why:** this step used to *build* the deploy roles and "the KMS grants for Staging's ECR pulls" — the
first is Stage 8 pass 1's, and the second does not exist: ECR decrypts pulls through the grants it holds
on the repository key, and the puller needs no `kms:Decrypt` (the read that deleted the step is the kind
Lesson 7 asks for). **Explanation:** what Stage 9 *names* from Stage 8: `awsds-deploy-prod` and
`awsds-deploy-staging` in step 3's policies, the misuse alarms as the pattern step 6 copies, and the
INT-07 image grant as the model 4.6 follows.

- **7.1 — [Claude] Run `./aws/cicd.py`**: CI-2/CI-3 green (the two roles exist with boundary and
  single-principal trust) before pass 1 writes policies that name them.
- **7.2 — [Claude] Run `./aws/datalake.py`**: `DL-5` green (the INT-11 parameters intact) before pass 2
  touches the grantor account; the drop-box statement and key grant read back with the 3.1 role name.
- **7.3 — [Claude] Record the ECR non-grant**: one line in the log — cross-account pulls need the
  repository policy only, no key grant — so nobody "fixes" the absence later (Lesson 5's inverse: an
  absence that is correct, written down).

### 8. Verify the boundary rather than declare it

**Action:** the session matrix — each cell a test with its result recorded, including the ones that
fail. **Why:** the promotion crosses account boundaries this stage just finished wiring, and every cell
is a place where a resource policy can be missing (INT-05/06 are the two most likely to surface as an
`AccessDenied` nobody can diagnose from the error). **Explanation:** run each from the stated session;
read every denial by its wording, never its exit code.

- **8.1 — [user] From a Sandbox session**: no deployment target's infrastructure can be
  changed; a lake table reads through the share but will not write (the governed write is the job
  role's alone); a `PutObject` to an out-of-organization bucket is denied naming the perimeter
  (`docs/plan/architecture.md` §4.2 — exercised, not amended; an amendment would go through battery
  phase 4b); the drop-box accepts `PutObject` and refuses the matching `GetObject`.
- **8.2 — [user] From a Production session as the data scientist**: 5.4's proofs, plus INT-06 — how
  much of the S3 **console** survives the `aws:SourceVpce` condition, recorded as a fraction and written
  into `README.md` if the answer is "use the CLI over the tunnel".
- **8.3 — [user] From the laptop over the tunnel**: a lake-object read succeeds through the
  `aws:SourceIp` branch, and the same read with the tunnel down fails (INT-05's two halves).
- **8.4 — [user] From a Staging session as the data scientist** (`DataScientistStagingAccess`, which 6b assigned): everything readable,
  nothing writable — including the buckets the pipeline writes to; the wording names
  `DenyEveryWrite`.
- **8.5 — [pipeline] The end-to-end**: re-run Stage 8's promotion against the real
  catalogs — the integration tests now query `staging/data/`'s mirror, the artifact lands in
  Production, and the pandas test still fails everywhere it should. **This is the stage's closing
  proof and the first fully meaningful promotion.**

---

## Deliverables

Each is written so its output differs between working and broken (Lesson 13). **The mechanical half is
`./aws/deploytargets.py`** ([`aws/INDEX.md`](../../../aws/INDEX.md)): the buckets, CMK and workgroup
enforcement; the package groups with their policies; the job and debug roles with their trust shapes;
the LF settings in every account that has any (`DT-5` — `DL-5`'s twin); the share, links and regrants with no
pending invitation; the Staging mirror side by side with the lake's catalog, and the **absence** of any
Staging link to Data Governance; the alarm rule; the persona sets' owed allows read back. The
behavioural proofs are the stage's own (Lesson 20):

- **The producer pair (INT-03):** a curated Iceberg table written cross-account under
  `awsds-prod-job-exec` — and the same role's direct `PutObject` to the same bucket denied.
- **The pickup (INT-10):** the drop-box read, curated, and emptied by the job; the writer still cannot
  read back what it wrote.
- **The registry gate (INT-07):** approval only under `awsds-deploy-prod`; a Sandbox session reads status
  and nothing else; the Staging deploy role reads an approved version.
- **The workgroup boundary:** a client-requested result location is overridden into the enforced one;
  the scan limit cancels.
- **The escape hatch:** closed at rest, open only inside an approved window, alarmed on every
  assumption, and unable to become a notebook (the OU SCP names the denial).
- **The promotion (8.5):** Stage 8's chain against real catalogs, end to end.

## Validation

1. Run `./aws/deploytargets.py` — all `DT-*` pass; diff two runs across the stage (only timestamps may
   change).
2. Run `./aws/datalake.py` after every `data-governance/data/` apply — `DL-5` green (the three-account
   parameters discipline).
3. Run `./aws/egress.py` §6 at session end — this stage adds nothing metered, and the reading proves it.
4. Read every denial by its wording, never its exit code (standing rule since 1c).

## Cost

Measured (`docs/PRICING.md`, `docs/plan/cost-model.md`), us-west-2:

| Item | Cost | Layer |
|---|---|---|
| `alias/awsds-prod-data` + the Staging CMK | ~USD 1/key-month | `[P]` |
| Package groups, workgroups, LF grants, links, resource policies | free at rest | `[P]` |
| Outputs/results/mirror storage | cents at lab scale | `[P]` |
| Producer/pickup Glue runs | 0.44 USD/DPU-h, 10-min minimum, on-demand | metered per run |
| Athena queries | 5 USD/TB scanned — the workgroup limit is the guard | metered |
| Staging's own account overhead (Config recorder etc.) | ~USD 0.5-1/month, already being paid — the account exists | — |

## Decisions due while executing

**Blocking questions for the user: none.** Each is decided during the stage and written into
`docs/log/log-stage-09-deployment-targets.md` (Lesson 16). Recommendations stated so the keyboard is not
the decision-maker.

1. **The Production data CMK** (1.1) — **the alias is not open**: `docs/GOVERNANCE.md` §Encryption
   settles it (one data CMK per account — revised 2026-08-19, the `security-zone` dimension withdrawn),
   which gives `alias/awsds-prod-data`. What remains to decide here is only **dedicated versus reusing
   `foundation/`'s key**. Recommended: **dedicated** — D31's argument verbatim: the deny that matters
   ("Staging and the approvers cannot read outputs") is only expressible on a key nothing else uses.
2. **The scan limit** (1.2) — recommended: **10 GB per query** to start, revised against real queries at
   Stage 12 rather than set high and forgotten.
3. **The mirror mechanism** (4.1) — recommended: **both catalogs instantiated from one versioned schema
   source** in the repository (a module input, not a sync script); a hand-maintained second copy is
   Lesson 14 as a catalog.
4. **The debug window mechanics** (6.1) — recommended: the **`DateLessThan` trust condition from a
   tfvars value defaulting to the past** — approval is a recorded apply, closure is a revert, and no
   standing machinery exists to rot.

## Verifications to answer while executing

Record every answer, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | Do the parameter readings bracket every LF-settings apply unchanged — Data Governance (again), Production, Staging (`DT-5`, `DL-5`'s discipline)? | 1.5, 2.2, 4.5 |
| ii | Does the write share arrive with a **fresh** session and no pending RAM invitation — INT-11's org path holding for the third consumer? **Answered on the RAM side at 2.2 and on the catalog side at 2.3**, because Production has no data lake administrator in between (2.2's callout) | 2.2, 2.3 |
| iii | Does the write pair hold — the LF write succeeds **and** the direct `PutObject` is denied on the identity side (D13)? | 2.4 |
| iv | Does the pickup read, curate and delete — and does the drop-box KMS grant reach the exact 3.1 role name (the Stage 5 contract)? | 2.5 |
| v | Is the registry gate real — a Sandbox session reads status only, and an approval lands only under `awsds-deploy-prod` (INT-07)? | 3.4 |
| vi | Does the enforced workgroup override a client-requested result location, and does the scan limit cancel (the documented behaviour, observed)? | 5.4 |
| vii | Are the Production negatives denied naming the **set's** deny — `CreateTrainingJob`, `StartJobRun` (D18)? | 5.4 |
| viii | Does `DataScientistStagingAccess` read back with `DenyEveryWrite` and no Athena, and is its assignment the one 6b made (Lesson 22)? | 5.2 |
| ix | Does INT-05 hold from both directions — the VPC branch and the tunnel branch, and fail with the tunnel down? | 8.3 |
| x | What fraction of the S3 console survives the `aws:SourceVpce` condition (INT-06, open question 8) — and is `README.md` told? | 8.2 |
| xi | Is the escape hatch closed at rest, open only in the window, alarmed on every assumption — and does a `CreateSpace` under it die on the OU policy? | 6.3 |
| xii | Does the Staging role read an approved model version (INT-07's registry half)? | 4.6 |
| xiii | Does the end-to-end promotion pass against the real catalogs — and does a schema drift planted in the mirror fail the integration tests, not the deploy? | 8.5 |
| xv | Does every `-job-exec` role read back with `awsds-job-exec-boundary` attached, using `get-role` (3.6) — and does a job submitted without a `VpcConfig` fail? | 3.5, 3.6 |
| xvi | Which shape did serverless inference take (3.7) — a named exception, or the SCP deny — and is the choice written into `AWS_STATE.md` either way? | 3.7 |
| xvii | Does a Staging job resolve `sagemaker.runtime` from the subnet it actually landed in (the AZ affinity D9 collides with)? | 4.3a |
| xiv | In **each** of the two accounts this stage gives a `DataLakeSettings` (Production, then Staging): do `CreateDatabaseDefaultPermissions` and `CreateTableDefaultPermissions` read `[]` **before** the slice's first catalog object exists, and does no database in that account carry an `IAMAllowedPrincipals` grant afterwards? — the reading the two-step exists to produce, and the only moment it can be taken | 1.3, 1.5, 4.1 |

## Risks

- **The silent LF-settings reset now has three instances, not one** — every account with a
  `DataLakeSettings` resource can zero its own `Parameters` on any apply. `DT-5` extends `DL-5`'s
  reading to all three; run it after every apply, not at stage end. **And that resource carries a
  second, unrelated hazard on the same apply** (measured 2026-08-18, Stage 5 pass 1): the two
  `Create*DefaultPermissions` act at **creation time** and cannot be expressed empty in a plan, so a
  catalog object created in the same apply as the settings can be born deferring to IAM — permanently,
  and invisibly afterwards. Two hazards, one resource, opposite failure modes: one is *overwritten
  later*, the other is *not applied early enough*. Both are answered by the same two-step (1.3's
  callout, Recipe D).
- **"The share did not arrive" and "the account cannot see it yet" look identical from the consumer
  side** — and this stage reads the consumer side twice (2.2, 2.3) across the pass where the difference
  exists. A receiving account with no data lake administrator shows an empty catalog while its RAM holds
  the share, which is exactly what both Stage 5 consumers showed on 2026-08-19. Read RAM first, catalog
  second, and never treat an empty catalog before 1.3 as evidence about the grant.
- **The write share is INT-03's least-travelled variant** — an LF-aware cross-account Iceberg write can
  fail in engine-specific ways the read shares never exercised. The fallback is INT-03's row; the proof
  is 2.4, before anything depends on it.
- **Two contracts are spelled, not enforced**: `awsds-prod-job-exec` (Stage 5's statements name it) and
  the mirror's schema source (4.1). A typo fails closed later, with an error naming a policy rather
  than the typo (Lesson 14); `deploytargets.py` reads both sides.
- **The registry policy's Sandbox principal uses the reserved-SSO wildcard-suffix idiom** (decision
  7's shape) — `make check` 9.2 must whitelist that `Sid` by name; a second occurrence is a decision,
  not a precedent.
- **Staging's value rests on sampled data catching real failures** (open question 9) — record, for
  every production incident this environment ever has, whether the Staging run could have caught it;
  until then it is a belief, not a finding.
- **Query results are visible within the persona** — one enforced result location means any
  `DataScientistProdAccess` holder can read another's query output. Stated limit at lab scale (D31
  keeps it from the approvers and Staging); per-user isolation would need per-user workgroups, which
  the identity seam forbids as a resource-per-person.
- **The escape hatch is authored by the identity it cannot constrain** (Lesson 18) — the controls above
  it are detective: the alarm on every assumption, and a trail its user cannot edit.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
