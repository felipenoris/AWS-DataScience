# Stage 16 — The sandbox lake

| | |
|---|---|
| **Status** | **PASSES 0, 1, 2 AND 3 APPLIED 2026-08-26 — the lake exists, is granted, and its key admits the vending role.** `sandbox/lake/` applied `12 added, 0 changed, 0 destroyed`, re-plan `No changes`, `./aws/sandboxlake.py` **11/11 `pass`, 0 FAILED**; `sandbox/data/` applied the key-policy statement and re-plans `No changes`, with the key reading back **three `Sid`s** live; `development/data/` re-plans **`No changes`** across both tag bumps — 2.2's proof, and the reading that attributes the finding below. **One finding, and it was not this stage's**: `sandbox/data/`'s first plan would have **stripped two Lake Formation administrators SageMaker Unified Studio created for itself** in Sandbox; the apply stopped, and the answer took two steps the same day — v0.4.0 adopted the seats, then the user's own question caught adoption freezing the list, and **`consumer-data-v0.5.0` is the standing answer: one create-time admin, `ignore_changes` over the list (measured: three live, one declared, plan `No changes`), and `./aws/datalake.py` `DL-13` as the list's defence** (§"What ran", the finding row and the one after it). **Still owed: 2.3** — its temporal window is gone, so it becomes the CONTRAST pair (direct access refused; another group's prefix refused), runnable as soon as the persona holds an SSO token and the tunnel is up — **and passes 4, 5 and 6**, which are where every documented claim about the S3 connection is converted or amended. **0.1 is DONE**: the user wrote the requirement into [`objectives.md`](../objectives.md) the same day, as a bullet in the SageMaker Unified Studio list, carrying the per-group contract and the SMUS mount (**not** permanence — see the 0.1 row). The reading with a consequence: the account data CMK carries **no delegate-to-IAM statement**, so 2.2 was never a formality. **Created 2026-08-26 at the user's request**; pre-instrumented the same day by `./aws/sandboxlake.py` (`SL-1`–`SL-5`), and the recurring procedure is drafted, **unexercised**, in [`runbooks/sandbox-lake.md`](../runbooks/sandbox-lake.md) — every command there is a design until passes 4-6 mark it measured, and the runbook earns its past tense from those readings, never from this file (Lesson 37) |
| **Prerequisites** | **None that block.** Stage 5's consumer side built this account's data CMK and its `DataLakeSettings` (`sandbox/data/`); Stage 6's create path is measured end to end, so a real project exists to wire; `s3-read-write` is merged (2026-08-24) and is pass 5's instrument **unchanged**; and the S3 Access Grants instance this stage grants against already exists in Sandbox — **SMUS-born 2026-08-22**, nothing here creates it (Lesson 17: read what the service made before adding to it). **Sandbox only, deliberately**: Development has no Access Grants instance until its first project is born, and nothing in this stage touches that account — extending the contract there is a later act, recorded here so it is not discovered as a gap |
| **Consumes** | [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D19](../decisions/D19-derived-zone.md), [D21](../decisions/D21-development-account.md), [D31](../decisions/D31-approver-read.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | — (no `INT-nn` row: every object lives in one account). What it does prove, and nothing before it has: the portal's **S3-connection surface**, measured for the first time — a path into S3 this estate has never exercised, beside the governed catalog path (D13) and the project path (`awsds-<env>-smus-projects`) |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules)
and [`docs/GOVERNANCE.md`](../../GOVERNANCE.md) — this stage builds the thing that file's derived-zone
contract exists to bound, on purpose, and the compensations below are argued against its clauses. The
recurring procedure is [`runbooks/sandbox-lake.md`](../runbooks/sandbox-lake.md); the mechanism sources are
the 2026-08-26 rows in [`docs/REFERENCES.md`](../../REFERENCES.md).*

---

**Objective:** a fourth Sandbox bucket, `awsds-sandbox-lake` — **permanent** artifacts, one prefix per SSO
group (`s3://awsds-sandbox-lake/<sso-group>/`, read-write for that group's members), each prefix mountable
into a SageMaker Unified Studio project through the portal's **S3 connection** feature, and readable and
writable from a laptop through `s3-read-write` with no project in the path — plus the runbook and the
instrument that let the infrastructure user wire and unwire projects as they appear.

## Why this bucket exists, and what its existence costs

The estate has three storage surfaces a data scientist can write, and none is a permanent, shareable home:
the **derived zone** sheds its contents at 30 days by contract (`GOVERNANCE.md` — "the lake keeps data,
this bucket sheds it"); the **project path** in `awsds-sandbox-smus-projects` is documented as "temporary
execution data and other project-related artifacts", is keyed by project id, and its access dies with the
project; a space's own work is an **EBS volume** that dies with the space. The governed lake is reached
through the catalog and is not a mount. So work that is maturing — a model, a dataset in progress, a
half-built pipeline — has nowhere to live between sessions and between projects until it is ready for the
promotion chain (D21), and the pressure that creates is exactly what Lesson 1 describes: copies land
somewhere regardless; the design's choice is only whether the destination is managed.

**What this stage accepts, with its eyes open: a permanent, ungoverned, group-writable store beside the
governed lake — a shadow lake.** The derived zone's own defence — "tolerable exactly because the contents
expire by design" — is precisely the clause this bucket abandons, so the compensations have to be
different, and they are these five, each owned by a step below:

- **It never leaves the account.** No sharing mechanism, no catalog registration, no cross-account
  principal, BPA and TLS-only from the house module — the data perimeter contains it exactly as D19
  argues for the derived copy (pass 1).
- **The key is the read control** (D31's idiom): the bucket encrypts under `alias/awsds-sandbox-data`,
  and the key policy — default-deny, hand-written — names who may read, which survives any forgotten
  prefix list (pass 2, the conventions' own KMS-over-enumeration rule).
- **Nothing reads or writes it under a standing identity statement.** Access is only by vended,
  prefix-scoped, expiring credentials — one Access Grant per (prefix × principal), each a registered,
  revocable object, so the entitlement is an enumerable register and **a grant nobody authorized is a
  finding** (the vending row's rule restated for this bucket; `SL-4` reads the shape and the orphans,
  and `AWS_STATE.md`'s register carries the authorized half).
- **Detection is scheduled where detection lives**: Stage 11's Macie job scope and its data-event trail
  map now name this bucket — written into that stage's file in this same sitting, not promised from here
  (Lesson 34). A permanent store outside the discovery scope would be the *un*-managed copy.
- **Permanence is not a serving path and not an archive of record**: what matures here leaves by the
  promotion chain — git for code, the governed lake's ingestion path for data (noting
  [open question 19](../open-questions.md): the drop-box catalogues nothing today) — and the
  classification norm follows copies in: the output of a query over `restricted` data is `restricted`,
  here as anywhere (decision 4, the runbook's §G).

**What it does not change:** the governed lake's rules. This bucket is D13's non-registered class — the
`scratch` class made permanent — plain IAM plus the key policy, no LF-Tag anywhere near it, and D13's
denies on registered prefixes are untouched. The institutional shape of the trade — an institution would
put permanent artifacts under lineage-aware governance rather than beside it — is a new row in
[`institutional-delta.md`](../institutional-delta.md), written with this file.

## What this stage builds, and in which accounts

| Where | What | Layer |
|---|---|---|
| Sandbox, `sandbox/lake/` (new slice) | the bucket `awsds-sandbox-lake` (house `s3-bucket` module, **no expiry**), the access role `awsds-sandbox-lake-access`, and — decision 3 — the Access Grants **location** plus one **grant per roster group** | `[P]` |
| Sandbox, `sandbox/data/` (amended) | one data-key-policy statement admitting the access role — `consumer-data` gains an `additional`-statements input, default empty, so Development's copy is byte-identical and unchanged | `[P]` |
| Sandbox, by hand, per project | one Access Grant per (project role × group prefix), created as projects appear and revoked when they die — [`runbooks/sandbox-lake.md`](../runbooks/sandbox-lake.md) §W / §R | — |
| the portal, per project | the S3 connection (documented as Create connection → Amazon S3): name, URI `s3://awsds-sandbox-lake/<sso-group>/`, Region, the access role | — |
| this repository | the runbook, `./aws/sandboxlake.py` (`SL-1`–`SL-5`), the slice README under the `POLICIES.md` discipline | — |

**Executor markers are Stage 4's** (`[Claude]` / `[Claude⚡]` / `[user]`), of which this stage uses two —
no step here is `[Claude⚡]`. Terraform applies and every
`s3control`/`datazone` write below are **[user]**-authorized per occurrence, as the infrastructure user —
account **Sandbox**, permission set **`InfrastructureAccess`**, profile `awsds-infra-sandbox-1`; the portal
acts and both tests are **[user]** as the data-scientist persona. Every reading is **[Claude]**.

## Step numbers are identifiers, not an order

| Pass | # | What | Slice · layer | Applied as / by |
|---|---|---|---|---|
| 0 | 0.1-0.4 | the spec note; the preflight readings | — | user (0.1); Claude reads |
| 1 | 1.1-1.3 | the bucket, and the slice around it | `sandbox/lake/` · `[P]` | Terraform, infrastructure user |
| 2 | 2.1-2.3 | the access role, and the key that must recognize it | `sandbox/lake/` + `sandbox/data/` · `[P]` | Terraform (a `consumer-data` tag bump) |
| 3 | 3.1-3.3 | the location and the per-group grants | decision 3's answer | infrastructure user |
| 4 | 4.1-4.4 | wire the first project; the in-project test | portal + by hand | user, with Claude reading |
| 5 | 5.1 | the out-of-project test | `s3-read-write`, unchanged | user, as the persona |
| 6 | 6.1-6.3 | revocation exercised; the paperwork | — | both |

## What ran on 2026-08-26, and what it measured

*The only place this stage's results are written. Everything here is a **reading** — no `terraform apply`,
no `s3control` write, no portal act. A row that says a thing exists says which command showed it.*

| # | What ran | What it measured |
|---|---|---|
| 0.1 | **[user]** — `objectives.md` edited | **DONE.** One line, in the user's own words, under the SageMaker Unified Studio bullet list this stage extends: *"connect to user's `sso-group` S3 bucket using SageMaker to read-write data to group's `sandbox-lake`"*. It is a **bullet in that list, not a dated note** — the user's choice of where the requirement belongs, and it puts the per-group contract and the SMUS mount into the spec. **Permanence is not in that sentence**, so the one thing this stage is measured against for the *durability* half is the stage file's own argument plus the [institutional-delta](../institutional-delta.md) row — recorded here rather than read into the line |
| 0.2 | `./aws/list-identities.py`, plus `iam list-roles` in Sandbox | **The roster is three, and it is derived.** `sso-group-data-scientists` → `DataScientistAccess`, `sso-group-deployment-managers` → `DeploymentManagerAccess`, `sso-group-dev-env-stewards` → `DevEnvStewardAccess` — one-to-one, and each one's `AWSReservedSSO_*` role is **provisioned in the account**, which is the assignment measured from the target's own side. `sso-group-infrastructure` is assigned too and takes **no prefix**: it is this bucket's operator, not a tenant — the distinction that makes `var.tenants` this slice's decision rather than a copy of `identity/sso/`'s table. The vending caveat holds: `awsds-org-project-storage-vending` is referenced by **`DataScientistAccess` only**, so two of the three rows have no laptop path until `identity/sso/` extends it |
| 0.3 (i) | `iam get-policy-version` on `awsds-sandbox-project-boundary` (v1) | **Nothing in the D13 boundary names this bucket** — confirmed, as the step predicted. The only S3 resources it names are `awsds-data-raw` / `awsds-data-curated` (deny) and `awsds-data-dropbox/incoming/*` (allow). **One thing the step did not predict:** its `DenyLakeDataKeyExceptThroughS3` names the **lake account's** key alone, so this account's own data CMK has **no `ViaService` clause in the boundary** — the pin over the new reader is the key policy's and the role's, both written in pass 2, and there is no third document behind them. The ceiling over the whole path is therefore just `CeilingIsEverythingTheIdentityPolicyGrants`, which narrows nothing |
| 0.3 (ii) | `kms get-key-policy` on `alias/awsds-sandbox-data` | **Two statements, and the absence between them is the finding.** `EnableKeyAdministrationInThisAccount` holds the administrative actions and **no cryptographic one**; `AllowDataScientistUseViaS3` holds the persona's three under a `ViaService` pin. There is **no delegate-to-IAM statement**, which is D31 working exactly as designed — and it means an identity policy in this account **cannot** grant `kms:Decrypt` on this key. So pass 2.2 is not paperwork: without it the access role's KMS statement grants nothing, and step 2.3's negative control should fail naming **KMS**, not S3 |
| 0.3 (iii) | `./aws/sandboxlake.py` — **first run ever** | Clean, exit 0. `SL-1`–`SL-4` `note` (bucket, role, location, grants: none). **`SL-5` `pass`** — no inline **or attached** `DataScientistAccess` document names `awsds-sandbox-lake`, so "vended-only" holds on the identity side **before** anything is built, which is the only time that claim is cheap to prove. The register shows the estate's existing Access Grants state: the **SMUS-born instance** (2026-08-22), one location scoped to a project's own path under `awsds-sandbox-smus-projects`, one grant to the persona role — the 2026-08-24 `s3-read-write` objects, untouched here. **The location's vending role there is the project role itself**; this stage's is a dedicated role, because a bucket shared across projects cannot vend through any one project's identity |
| 0.4 | — | **Still only documentation:** verifications (ii)–(vi). The whole per-project half of the access role's trust — the three `SmusProject*` statement shapes — comes from AWS's connection documentation read this day and from nothing else. `var.wired_projects` is **empty**, so none of it is applied; step 4.2 is what converts it, or amends it |
| 1.1 / 2.1 | authoring only — `terraform validate`, `fmt`, `tflint`, `checkov`, `make check` | `sandbox/lake/` on disk: the bucket (no `expiration_days`, no `additional_policy_statements`), `awsds-sandbox-lake-access`, the Access Grants **location**, three per-group grants, the slice README. **One provider gap measured rather than assumed, and it is not a version lag** — checked against the provider's docs tree on `main` (ahead of the v6.61.0 release, carrying the unreleased 6.62.0): `website/docs/r/` has all three `s3control_access_grants_*` **resources**, `website/docs/d/` has **none** of them, so no released *or* unreleased version removes the workaround. The managed resource is the one object this slice must not declare (SMUS-born, Lesson 17), so the trust's `aws:SourceArn` is **built** from partition + region + account — a form the 0.3 (iii) baseline printed verbatim. Revision trigger recorded in the code: a `d/` page appearing. `make check` **OK**, twenty-six slices |
| 1.2 / 3.1 / 3.2 | **APPLIED** — `terraform apply`, `awsds-infra-sandbox-1` | **`12 added, 0 changed, 0 destroyed`; re-plan `No changes`.** The bucket and its five configurations, `awsds-sandbox-lake-access` + its inline policy, the Access Grants **location** `3b7613eb-…` over `s3://awsds-sandbox-lake/`, and **three** standing grants. `./aws/sandboxlake.py` re-run: **11 rows, all `pass`, 0 FAILED** — `SL-1` reads *no expiry on current objects* (the requirement, measured), `SL-2` reads *the Access Grants service plus **0** enumerated project roles* (`wired_projects` still empty, as designed), `SL-3` and `SL-4` read the location and the three grants back by id. **Passes 1 and 3 are done in one act**; the pass table's split was a plan, not an order |
| 2.3 | **NOT TAKEN, AND THE WINDOW IS NOW GONE** | The temporal control needed the **persona**, and two things blocked it at the moment it was available: `awsds-scientist` had **no cached SSO token**, and the tunnel was **down** (public address = the operator's, not the VPN EIP). Off VPN the persona set's `DenyControlPlaneOffVpn` denies `*`, so the probe would have produced a denial attributable to the **wrong** control — the unattributable reading Lesson 24 says to separate by channel, never by a better guess. The apply then continued, so **both** temporal windows (before the grants, before the key policy) have closed. **2.3 becomes the CONTRAST pair, which holds principal, bucket and moment constant and varies only the grant**: as the persona, a **direct** `s3:GetObject`/`PutObject` must be refused (the vended-only claim), and a vend against **another group's** prefix must be refused (the grants are per-prefix and load-bearing). Owed, and unblocked the moment the persona holds a token and the tunnel is up |
| 2.2 | **APPLIED, after the finding below was settled** | `development/data/` re-planned **`No changes`** across the tag bump — 2.2's proof, and the empty plan that shows the default protected the other consumer. `sandbox/data/` did **not** apply on its first plan (`0 to add, **2 to change**, 0 to destroy`, and only one of the two was this stage's); after `consumer-data-v0.4.0` the plan reduced to the single resource `module.consumer_data.module.data_key.aws_kms_key.this` and was applied. **Read back live:** the key carries **three** `Sid`s — `EnableKeyAdministrationInThisAccount`, `AllowDataScientistUseViaS3`, **`AllowSandboxLakeAccessRoleViaS3`** — and `sandbox/data/` re-plans `No changes`. Both consumers were re-planned after **each** bump; Development read `No changes` **both times** |
| — | **THE FINDING (2026-08-26): SMUS made itself a Lake Formation administrator in Sandbox, and no gate here can see it** | `sandbox/data/`'s first plan would have **removed two `admins`** — `awsds-sandbox-smus-manage-access` and `awsds-sandbox-smus-provisioning`, the two Stage 6 service roles — and reset `allow_full_table_external_data_access` from **`true`** to unset. **Nothing in this stage touched `lakeformation.tf`**; the drift is pre-existing and its cause is attributable, because **`development/data/` re-plans `No changes`** and the one thing Sandbox has that Development has not is a **live SMUS project** (2026-08-22) — the service added its own principals when the first project was created ([Lesson 17](../lessons.md)). **`DL-5` reads `pass` in all three accounts** (`CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`, fresh 2026-08-26): the INT-11 hazard is intact and **was never the exposure here** — DL-5 measures `parameters` and **not `admins`**, so no gate in this repository would have reported it, and it surfaced only because a plan was run for an unrelated reason ([Lesson 31](../lessons.md)'s neighbour). **The user chose ADOPTION** (2026-08-26): `consumer-data-v0.4.0` carries `additional_data_lake_admin_role_arns` (default `[]`) and `allow_full_table_external_data_access` (default `null`), `sandbox/data/` declares both, and the LF administrators read back **three** after the apply. **Stripping them would have risked the create path Stage 6 measured *after* they existed, and removing them from the code would not remove them from AWS** — it would only make every future plan fight the service. **What adoption does not settle, and is a Stage 6 residue rather than this stage's:** whether a SMUS provisioning role *should* administer Lake Formation, when an administrator can grant itself anything in the local catalog — the resource links to the governed lake included |
| — | **THE SECOND ANSWER (same day, the user's question): `consumer-data-v0.5.0` replaces adoption with ownership** | The user asked whether v0.4.0 was pulling into Terraform something SMUS manages — and it was, one step removed: adoption froze the list as it stood, so a seat the service adds *tomorrow* is deleted by the next apply, the same failure one seat out. `v0.5.0` removes the two inputs, declares `admins = [the one create-time seat]`, and puts `ignore_changes = [admins, allow_full_table_external_data_access]` on the resource — the `catalog.tf` Iceberg-columns shape, Lesson 23: Terraform keeps the resource's existence, `parameters` and the cleared create-defaults; the admin list goes through the service. **The property is measured, not believed**: with Sandbox holding **three** administrators live and the config declaring **one**, `terraform plan` reads **`No changes`** — and Development reads `No changes` too, its third empty plan across three bumps. **The plan's defence is replaced, not dropped**: `./aws/datalake.py` **`DL-13`** (first run 2026-08-26: producer `pass`, Development `pass`, Sandbox `note` naming the two SMUS seats) fails on the required seat's absence, fails on any seat nobody granted, and notes the SMUS seats OQ 24 owns |
| 2.2 | authoring only | `consumer-data` gains `additional_data_key_policy_statements` (type `any`, default `[]`), `concat`ed after the two standing statements — **structure in the module, values in the slice**, the `vpc-egress-v0.3.0` split. `sandbox/data/` passes `AllowSandboxLakeAccessRoleViaS3`; `development/data/` bumps the ref and passes nothing. **The apply order is three acts over two slices** — `data` → `lake` → `data` — because KMS validates a key policy's principals and the role must exist first; it is written in `layers.py`'s `lake` rank comment, the slice README and here, because a rank cannot express it |

## To execute

### 0. Preflight — the spec, the roster, and what is only documentation

*Why: the mechanism this stage builds on was read from AWS's pages on 2026-08-26 (the S3 connection
registers an Access Grants location; the access role is the location's role; `GetConnection` vends
credentials), and an identifier or mechanism read out of prose is a claim, not a reading (Lesson 38). This
pass separates what the estate already knows by measurement from what pass 4 still owes.*

- **0.1 — [user] Write the requirement into [`objectives.md`](../objectives.md)** in the file's own
  convention — a dated *(added 2026-08-26)* bullet. What it must carry, in the user's words: permanent
  per-SSO-group artifact storage in the experimentation account, mountable into SMUS projects, with the
  shadow-lake risk accepted against the DLP requirement's discovery and detection halves. The existing
  bullet this extends: "use of S3 buckets for storage, built in SageMaker Unified Studio user interface".
- **0.2 — [Claude] The prefix roster is derived, not invented**: enumerate which `sso-group-*` groups hold
  a persona assignment in **this** account. The sso slice assigns **three** today —
  `sso-group-data-scientists`, `sso-group-deployment-managers`, `sso-group-dev-env-stewards`
  (`identity/sso/locals.tf`; `INV-04` — five groups exist, one member each) — and this step's reading
  confirms the roster against the deployed assignments, never against this sentence. A group with no
  principal in the account gets its prefix when it gains one, not before — a prefix with no possible
  reader is furniture. One consequence to record with the roster: **only `DataScientistAccess` carries
  the vending policy today** (`awsds-org-project-storage-vending`), so the other two groups' laptop path
  is inert until their sets gain the same by-name reference — an `identity/sso` act, taken when a second
  group's path is wanted, not silently here.
- **0.3 — [Claude] Three readings before anything is built** (Lesson 22 — read what cannot be attempted):
  the D13 boundary document's ceiling over this path (its `Allow *` and its lake-shaped statements — the
  exact statement set is this reading's *output*, not this sentence's; the claim to confirm is that
  nothing in it names this bucket, behaviourally re-proven at 4.4); the deployed data-key policy
  (`sandbox/data/` — the statement set pass 2 amends); and the Access Grants baseline — instance,
  locations, grants (`./aws/sandboxlake.py` first run: the bucket rows `note`, the register rows the
  SMUS-born state).
- **0.4 — [Claude] Say out loud what is still only documentation**: verifications (ii)-(vi) below are the
  documented-mechanism claims pass 4 converts into measurements. Nothing before pass 4 states them in the
  perfect tense.

### 1. The bucket — `sandbox/lake/`, a new `[P]` slice

- **1.1 — [Claude] Write the slice** ([`terraform-changes.md`](../runbooks/terraform-changes.md)
  Recipe C): the house `s3-bucket` module (current tag), `bucket_name = "awsds-${var.env}-lake"`,
  `kms_key_arn` = this account's data CMK (resolved by data source against `alias/awsds-sandbox-data` —
  no same-account remote-state read exists in the tree yet, and one is not needed to look up an alias),
  and **no `expiration_days`** — permanence is the point; the module's unconditional noncurrent-version
  expiry and multipart-abort stand. Add the slice's `layers.py` row (`[P]`, ranked after `data`) in the
  same commit — a slice without a row fails the sixth check.
- **1.2 — [user] Apply; re-plan `No changes`.**
- **1.3 — [Claude] The paperwork of the same sitting**: `terraform-live/README.md`'s count,
  `docs/AWS_STATE.md`'s new section-C row, and the slice README opened under the `POLICIES.md` discipline
  — one row per policy statement, per role, per grant the slice declares. (`docs/plan/conventions.md` §6
  already carries the `lake/` row — added at planning, marked not built.)

### 2. The access role, and the key that must recognize it

*Why: reach is an intersection (Lesson 28). A vended read of an SSE-KMS object needs the S3 grant AND the
key policy to answer, and the halves live in two slices — this pass writes both and then proves the
negative before any grant exists.*

- **2.1 — [Claude] The role** `awsds-sandbox-lake-access`, in `sandbox/lake/`. The trust starts as AWS's
  documented location-role statement — `access-grants.s3.amazonaws.com`, `sts:AssumeRole` +
  `sts:SetSourceIdentity`, `aws:SourceAccount` pinned, and the S3 guide's stricter `aws:SourceArn` (the
  instance ARN) adopted with it — **plus, per wired project, the documented project-role statement set**
  (an enumerated variable of role-ARN × project-id pairs, initially empty, appended by the runbook's §W):
  `sts:AssumeRole` under `sts:ExternalId` = the **project id**, `sts:SetSourceIdentity` matched to the
  caller's `datazone:userId` principal tag, and `sts:TagSession` for the
  `AmazonDataZoneProject`/`AmazonDataZoneDomain` request tags — carried whole, because a runtime assume
  that sends session tags or a source identity is *rejected* by a trust that merely names the role.
  **Never a wildcard principal** (`SL-2` fails on one). Permissions: object and list actions on the
  bucket and its prefixes; `kms:Decrypt`/`GenerateDataKey`/`DescribeKey` on the data CMK via S3.
  **Deliberately not carried, recorded as a deviation from the documented option-1 role**: the `S3AG*`
  location/grant-management statements and the `iam:PassRole` to the Access Grants service — they exist
  so a connection can register its *own* location, and here the location is pass 3's, pre-registered;
  **verification (ii) is the gate**, and if creation demands them they join this role as a measured
  amendment, never silently. This one role is both the location's vending role and the connection's
  access role — one principal to name in the key policy, one session identity in every trail row.
- **2.2 — [user] The key-policy statement, as a `consumer-data` tag bump** (Recipe B, two commits): the
  module gains `additional_data_key_policy_statements` (default `[]` — the structure stays in the module,
  each slice owns its values, the same shape `vpc-egress-v0.3.0` set), and `sandbox/data/` passes one
  statement admitting the access role. Development bumps the ref and its plan reads **`No changes`** —
  that empty plan is the proof the default protected it. Same sitting: the `consumer-data` README row.
- **2.3 — [Claude] The negative control, before any grant exists** (verification (i); Lesson 26's rule
  that a probe proves nothing without one): as the persona, attempt a direct read and a vend against the
  bucket — record the denial wording and attribute it. Everything pass 3 opens is measured against this
  baseline.

### 3. The location and the per-group grants

- **3.1 — [user] Register the location**: scope `s3://awsds-sandbox-lake/`, IAM role = the access role —
  by Terraform in the slice or by hand per decision 3's answer. **The instance is not touched**: it is
  SMUS-born, the service set it up and keeps writing to it, and it stays service-owned either way
  (Lesson 17's neighbourhood).
- **3.2 — [user] One grant per roster group**: prefix `<sso-group>/*`, permission `READWRITE`, grantee =
  the **reserved role of that group's permission set in this account** (decision 2 — the grain the
  2026-08-24 vending decision already accepted: membership-blind *within* the group, and the group is
  exactly the intended unit). The roster is 0.2's — three grants by today's assignments, with 0.2's
  vending-policy caveat standing beside the two whose laptop path is inert until `identity/sso` extends
  the reference.
- **3.3 — [Claude] Register every location and grant** in `docs/AWS_STATE.md` (the lake-bucket row and
  the vending row's discipline). The "a grant nobody authorized is a finding" rule has two halves:
  `SL-4` reads the **shape** — group folders, the two known grantee classes, orphans — and whether each
  well-shaped grant was *authorized* is a **human diff** of the grant list against the register, possible
  only while the register is current.

### 4. Wire the first project, and the in-project test

*Why: this pass is the stage's measurement instrument. The console form is the completeness spec
(Lessons 16 and 39): every field it demands is written down, and every documented claim about what
creation does — a location registered or reused, a grant cut or not, credentials vended as whom — is read
back from the APIs and the trail, not from the page.*

- **4.1 — [user] The project's grant** — the runbook's §W, executed for the first time: one
  `create-access-grant`, prefix `<sso-group>/*`, grantee = the experimentation project's
  `datazone_usr_role_*` — the role ARN **and the project id** (2.1's `ExternalId`) read from the
  project's **overview page**, where the documentation locates both; the user has also observed the ARN
  displayed in the connection form (2026-08-26), and which surfaces carry it is part of this step's
  reading. Then the pair's entry in the access-role trust variable, applied. Authorized per occurrence,
  like every hand write.
- **4.2 — [user] The connection**, in the portal, in the experimentation project. Two spellings of this
  act exist and 4.2's first reading is whether they are one form (Lesson 32): the user's observed
  surface is the Data area's *Add S3 location*; the documentation writes it as **Connections → Create
  connection → Amazon S3**. The documented fields, all four recorded: **Name**, S3 URI
  `s3://awsds-sandbox-lake/<sso-group>/`, Region `us-west-2`, and the access role — a **dropdown** of
  existing roles, from which `awsds-sandbox-lake-access` is picked. Any field the form demands beyond
  those four is recorded as a finding against this file.
- **4.3 — [Claude] Read back what creation actually did** (verifications (ii)-(iv)):
  `list-access-grants-locations` and `list-access-grants` before and after (a second location? a
  SMUS-cut grant?), `get-connection`'s environment read (does it carry the access role), and — after 4.4
  — the bucket's data events: **which principal** the browse, read and write arrived as. That last
  reading decides whether the key statement and the trust are naming the right identity, which no page
  settles (Lesson 42's arrived-vs-denied split is the diagnostic if rows are missing).
- **4.4 — [user] The test, from JupyterLab in the project**: write a file through the mounted location,
  list, read it back. Then the two refusals that make the pass mean something (Lesson 13): list **above**
  the prefix (verification (v)), and repeat the read from a project holding **no** grant (the contrast
  that proves the grant is the gate). Record all three outputs.

### 5. The out-of-project test

- **5.1 — [user] On the VPN, as a member of the roster group** (the persona profile, the same identity
  Stage 6's tests used): the `s3-read-write` sequence unchanged — `list_caller_grants` shows the group's
  grant beside the project-storage one (verification (ix): with two grants discoverable, the demo's
  first-grant convenience must not pick silently); vend against `s3://awsds-sandbox-lake/<sso-group>/*`;
  write, list, read back. Record the vended session's identity from its ARN — expected: a session of
  **the access role**, where the project-path vend was a session of the project role; the difference is
  worth one sentence in the log. Then verification (vii): the persona's **direct** `s3` call on the
  bucket still refuses — vended-only is a claim until its negative control runs.

### 6. Revoke, and the paperwork

- **6.1 — [user] Exercise §R once, against a sacrificial grant**: cut one extra grant on a probe prefix
  (`<sso-group>/probe/*`, same grantee), verify it vends, delete it, verify the vend refuses — and record
  how long the already-vended credentials keep working (verification (viii); the bearer residual, open
  question 14's shape). The working project mount is not the test article.
- **6.2 — [Claude] Close the record in the same sitting**: `docs/AWS_STATE.md` rows final; the runbook's
  unexercised markers replaced with the dates of 4.1-6.1; `./aws/sandboxlake.py` re-run all pass;
  the INDEX cells (stages, `GENERAL_PLAN.md`) brought to the file's state; `make check` clean.
- **6.3 — [user] The stage log** — `docs/log/log-stage-16-sandbox-lake.md`, including the connection
  form's exact field list and the CloudTrail principal reading, which are this stage's only measurements
  of what the feature *is* on the day it ran.

## Deliverables

- **The bucket, with its policies, read back**: `SL-1` pass — versioning, SSE-KMS under
  `alias/awsds-sandbox-data`, four-flag BPA, the TLS-only statement, **no expiry on current objects**.
- **The runbook, exercised**: §W and §R each executed at least once with their dates in the file; §T's
  two halves are deliverables 3 and 4.
- **The in-project proof**: a file written and read back through the S3 connection from JupyterLab, plus
  the two refusals (above-prefix, ungranted project) — written so the output differs between working and
  broken (Lesson 13).
- **The out-of-project proof**: the `s3-read-write` sequence end to end as a Sandbox SSO user in the
  roster group, the vended identity read from the session ARN.
- **The register, clean**: every location and grant on the Sandbox instance accounted for — `SL-4` pass
  (the shape and the orphans), plus the human diff of the grant list against `AWS_STATE.md`'s rows,
  which is the authorized-or-not half no instrument reads.

## Validation

1. Run `./aws/sandboxlake.py` — `SL-1`–`SL-5` pass, 0 FAILED.
2. `terraform plan` on `sandbox/lake/`, `sandbox/data/` and `development/data/` reads `No changes` after
   every by-hand act — the by-hand writes and the code describe the same world.
3. `make check` — the slice's layers row, the README index rows, no identifier leaks.
4. `./aws/datalake.py` unchanged, 0 FAILED — the governed lake's readings must not move because a
   neighbour appeared.

## Cost

Measured rows already in [`docs/PRICING.md`](../../PRICING.md) §5 (Lesson 6), nothing new to measure:
S3 Standard **USD 0.023/GB-month** in `us-west-2`, PUT-class requests 0.005/1 000, **S3 Access Grants
requests 0.03/1 000** (the Price List row of 2026-08-23 — the public pages say nothing). No new hourly
item, and under decision 1's recommendation no new CMK, so `cost-model.md`'s floor does not move — the S3
line grows with what users keep, which is by design unbounded here and is exactly the number Stage 12
reads against the real bill, under D12's ceiling. The tests' only metered item is the JupyterLab app
while it runs (USD 0.050/h).

## Decisions due while executing

**Blocking questions for the user: one — 0.1's spec note.** The alternative — anchoring this stage on the
existing "use of S3 buckets for storage, built in SageMaker Unified Studio user interface" bullet alone —
leaves permanence and the per-group contract measured against nothing; if the user prefers that, the
refusal is recorded here and the stage proceeds. Everything else is decided during the stage and written
into `docs/log/log-stage-16-sandbox-lake.md` (Lesson 16). Recommendations stated so the keyboard is not
the decision-maker.

1. **Which key encrypts the bucket** — due before pass 1. **(a) recommended: the account data CMK**
   (`alias/awsds-sandbox-data`), with the admitting statement arriving as a `consumer-data` input that
   defaults empty — `GOVERNANCE.md` §Encryption's rule holds unamended ("every data bucket encrypts under
   the data CMK of the account it lives in") and D31's key-as-read-control idiom extends to the new
   reader. **(b) the project CMK** (`alias/awsds-sandbox-project`) — rejected: that key is deliberately
   the SMUS project surface, and merging the two erases the boundary the split was made for. **(c) a
   third CMK** — rejected: Lesson 32 already priced this exact question for the derived zone ("a third
   CMK the cost model does not carry, or a key shared for no reason") and the answer has not changed.
2. **The grantee grain** — due before pass 3. **(a) recommended: IAM grain**, the reserved role of the
   group's permission set in this account — the grain the 2026-08-24 vending decision accepted,
   membership-blind within the group, and the group **is** the contract's unit (group ↔ permission set is
   one-to-one per account, so per-group separation is expressible without anything new). **(b) directory
   grantees** (`DIRECTORY_GROUP`) — would give per-human attribution, but requires
   `associate-access-grants-identity-center` on the SMUS-born instance, which
   [open question 13](../open-questions.md) says deserves its own decision and must not arrive as a side
   effect of this stage; and whether the plain-IAM `GetDataAccess` path both consumers use even matches a
   directory grant is unmeasured. If ever chosen: measured first, on a probe prefix.
3. **Where the durable Access Grants objects live** — due before pass 3. **(a) recommended: Terraform**,
   in `sandbox/lake/` — the location and the per-group grants are standing `[P]` objects and deserve a
   plan that defends them; they would be the tree's first `s3control` resources, and the **instance stays
   out of state either way** (SMUS set it up and keeps writing to it — Lesson 17's neighbourhood).
   **(b) by hand**, like the 2026-08-24 project
   grant — cheaper today, but a standing object defended only by a register row. **Per-project grants are
   hand-made under either answer** — they die with projects, and the runbook owns their lifecycle.
4. **The graduation norm** — due at close, recorded in the runbook's §G: what leaves this bucket and how
   (git for code; the governed ingestion path for data bound for the lake — which
   [open question 19](../open-questions.md) currently leaves without a demander), that nothing here is a
   serving path, and that the classification of a source follows its copies in. A norm, not a lifecycle
   rule — expiry is exactly what this bucket exists not to have, so the enforcement is Stage 11's
   detection plus Stage 12's bill, and saying so is the decision.

## Verifications to answer while executing

Record every answer, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | What exactly does the persona's attempt answer **before** any grant exists — the denial wording, attributed (the baseline every later success is measured against) | 2.3 |
| ii | Does connection creation **reuse** the pass-3 location or register a second one — and does an overlapping registration refuse, or silently coexist? | 4.3 |
| iii | Does connection creation cut any Access Grant of its own? The register rule ("a grant nobody authorized is a finding") needs to know whether SMUS-born grants are an expected class | 4.3 |
| iv | **Which principal do the bucket's data events name** for browse, read and write through the connection — a session of the access role, of the project role, or an Access-Grants-vended session? This decides whether the key statement and the trust name the right identity | 4.3, 4.4 |
| v | Does a connection whose URI is a prefix confine listing to that prefix, or is the prefix cosmetic? | 4.4 |
| vi | Does the D13 boundary let the project role through this path — read at 0.3, confirmed by 4.4 working (the claim: its lake-shaped statements name registered prefixes, the drop-box and the lake key, and none names this bucket — the full statement set is 0.3's output) | 0.3, 4.4 |
| vii | Is the persona's **direct** S3 call on the bucket still refused after every grant is in place — vended-only is a claim until its negative control runs | 5.1 |
| viii | What does deleting a grant actually cut, and how fast — including how long already-vended credentials keep working (the bearer residual, open question 14's shape) | 6.1 |
| ix | With two grants discoverable per caller (project storage and the lake), does `s3-read-write`'s first-grant convenience mislead, and does its README need a sentence? | 5.1 |

## Risks

- **The store grows without bound, by design.** No expiry, no quota — the compensations are detection
  (Stage 11's scope, amended in this sitting) and the bill (Stage 12). A day this bucket holds something
  `restricted` that Macie has not seen is the accepted window, stated rather than absorbed.
- **Membership-blind, bearer-shaped access** ([open question 14](../open-questions.md)): a grant admits
  the whole group's role, and vended credentials outlive a revocation for their remaining duration —
  measured, not assumed, at 6.1.
- **The name is a singleton** (D35): bucket names are global, so a second business unit's lake cannot be
  `awsds-sandbox-lake` — the ordinal question gains a token
  ([open question 10](../open-questions.md), amended in this sitting), decided with N=2 in hand.
- **The in-project test rides the browser**: the portal needs the Local Network Access grant on the
  tunnel (Lesson 43), so an in-project failure may be the browser and not the wiring — CloudTrail's
  arrived-vs-denied split (Lesson 42) is the first diagnostic, before any policy is touched.
- **Two authors write to one instance**: SMUS provisions project locations beside this stage's objects.
  `SL-4` classifies every grant rather than assuming a clean namespace, and an unclassifiable grant is a
  FAIL to attribute, never a row to tidy.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
