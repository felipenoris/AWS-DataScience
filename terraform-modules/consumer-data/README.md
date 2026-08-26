# `consumer-data` — the lake's consumer side, one module applied twice

The Stage 5 pass 4 module ([stage file](../../docs/plan/stages/stage-05-data-foundation.md); the governance
model's one copy is [`docs/GOVERNANCE.md`](../../docs/GOVERNANCE.md)). Called by
[`terraform-live/sandbox/data/`](../../terraform-live/sandbox/data/) and
[`terraform-live/development/data/`](../../terraform-live/development/data/) — both thin, both `[P]`, both
pinning `consumer-data-v0.2.0` **by git tag** — and by every further business unit's Sandbox once D35's N
passes 1. **The design lives here once; a slice says which account, never what.** That is also why this
index is in the module and not in the slices: two copies of one design drift on the first divergence.

What lands in **each** consumer account when this module applies:

| Object | Name |
|---|---|
| the account's data CMK | `alias/awsds-<env>-data` |
| the derived zone | `awsds-<env>-derived`, 30-day expiry, three prefix families |
| the enforced query path | workgroup `awsds-<env>-athena`, 10 GiB scan cap, output into `results/` |
| the account's own Lake Formation seat | `aws_lakeformation_data_lake_settings` — admins, `parameters`, the cleared create-defaults |
| the shared lake, made addressable | 2 resource links (`raw`, `curated`) + 4 re-grants |

## The apply is two steps here as well, per account

`aws_lakeformation_data_lake_settings` owns values Terraform cannot state an intention about — the two
`Create*DefaultPermissions` blocks act at **creation** time, and **the first local catalog object in this
module is the resource link**. A link born while the defaults still stand defers to plain IAM, and clearing
them afterwards does not reach it. So, per consumer:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/data \
  apply -target=module.consumer_data.aws_lakeformation_data_lake_settings.this
```

then `./aws/datalake.py` — `DL-6` **for that account**, `DL-5` for the parameters — and only then the full
apply. If `DL-6` still names `IAM_ALLOWED_PRINCIPALS`, revoke before continuing. That is
[Lesson 27](../../docs/plan/lessons.md) and **Recipe D** in
[`docs/plan/runbooks/terraform-changes.md`](../../docs/plan/runbooks/terraform-changes.md), unchanged from
the producer side; the reasoning sits in `lakeformation.tf` beside the resource.

---

# The controls, one row each

**The same discipline
[`data-governance/data/README.md`](../../terraform-live/data-governance/data/README.md) keeps for the lake,
applied to its consumer half**: a key-policy statement, a bucket-policy statement, a settings attribute, a
workgroup setting or a re-grant that is added, removed, renamed or re-conditioned in the `.tf` files **is a
change to this file, in the same sitting**. The `.tf` files carry the *reasoning* in comments beside each
resource; this file is the **index** — what exists, and what it does once applied.

**What is not here**: applied grant triples with their dates, which live in
[`docs/AWS_STATE.md`](../../docs/AWS_STATE.md) §"Lake Formation grant register". This file describes what the
**code** declares; that one records what is **deployed**, in which account, on which date.

## A permission here is the intersection of three documents in three accounts

The lake README's warning, one account further out. Lake Formation runs its own authorization layer on top
of IAM, so no single file answers "what can this persona do":

| Half | Where it lives | What it decides |
|---|---|---|
| the **IAM** action | `terraform-live/identity/sso/` — one permission set, provisioned into every account | whether the API **call** is permitted at all |
| the **Lake Formation** permission | the producer's `shares.tf` (to the account) **and** this module's re-grants (to the principal) | what the call **returns** |
| the **resource** policy | this module's key and bucket policies, and — for the drop-box — the lake's, in a third account | whether the object may be read or written |

Since pass 4c the trap has a second edge, and the seven identity-side statements split by *which* state they
read. Five name **this** module's objects — `RunQueriesInTheEnforcedWorkgroups`, `UseDerivedZoneBuckets`,
`ReadDerivedZoneObjects`, `WriteDerivedZonePrefixes`, `DeleteScratchObjects` — enumerated from this slice's
outputs rather than wildcarded, so an object renamed here silently narrows a policy written in Identity. The
other two, `WriteIngestionDropBox` and `UseLakeDataKeyViaS3`, name the **lake's** drop-box prefix and
data key, read from `data-governance/data/`'s state — which is why the trap spans three accounts rather
than two. [Lesson 28](../../docs/plan/lessons.md), as amended by 4c: **verify the pair, and remember the
two halves are in different accounts.** `./aws/datalake.py` measures both sides — `DL-12` the identity half
of the drop-box write, `DL-5`/`DL-6`/`DL-7` the Lake Formation half, `DL-8`/`DL-9` the workgroup and the
derived zone.

**Measured 2026-08-20, and the table above is now confirmed *and* undercounted.** The drop-box
`PutObject` ran for the first time and needed all three rows at once — the identity statement here, the
lake's bucket policy, and the lake CMK's key policy — three documents in **two** accounts on a single
call. What the reading adds: the **resource** row splits into a bucket half and a *key* half whenever the
target is encrypted, and only the key half is invisible on failure. A missing key grant returns a **KMS**
error naming an action that appears in neither the bucket policy nor the statement being debugged; a
successful write is where it becomes readable, in `SSEKMSKeyId`. **So the review habit for anything in
this module that writes: read the success response's key ARN, not the exit code.** The same pass measured
the drop-box's asymmetry from the persona — `PutObject` allowed, `GetObject` / `ListObjectsV2` /
`DeleteObject` each denied *implicitly* — so `WriteIngestionDropBox` is exercised rather than merely
declared.

## `kms.tf` — the account's data-key policy

One data CMK per **account** (revised 2026-08-19 — the `security-zone` dimension withdrawn:
`GOVERNANCE.md` §Encryption), and the alias carries the account pattern rather than the word *derived*:
`alias/awsds-<env>-data`, uniform with the lake's. It is deliberately **not** the lake's key —
the reasons are in the file, and the load-bearing one is that the lake key's
`AllowProductionPickupDecryptViaS3` grants `Decrypt` with **no bucket scoping**, so these buckets under that
key would put Production's job role over this account's materialised `restricted` results.

| `Sid` | What it allows, and to whom |
|---|---|
| `EnableKeyAdministrationInThisAccount` | The account root, **administration only** — `Create*`, `Delete*`, `Put*`, `Describe*`, `Get*`, `List*`, `Enable*`/`Disable*`, `Revoke*`, `Tag`/`Untag`, `ScheduleKeyDeletion`, `CancelKeyDeletion`, `Update*` — and **no cryptographic action**: no `Encrypt`, `Decrypt`, `GenerateDataKey*`, `ReEncrypt*`. This is the difference between D31 being a control and being a comment: the module's default (and the lake key's first statement) grants root `kms:*`, which delegates *use* to whatever IAM policy happens to exist. The anti-lockout guarantee is intact and Terraform can still create, tag, re-policy and schedule deletion. What it does not close, stated rather than implied ([Lesson 18](../../docs/plan/lessons.md)): the administrator can call `kms:PutKeyPolicy` — the point is that widening becomes an **edit with a diff**, not a side effect of some other grant |
| `AllowDataScientistUseViaS3` | `DataScientistAccess` (resolved **by pattern** in the caller — the `AWSReservedSSO_*` suffix is minted per account): `Decrypt`, `GenerateDataKey`, `DescribeKey`, scoped `kms:ViaService = s3.<region>.amazonaws.com`. SSE-KMS needs `GenerateDataKey` to write and `Decrypt` to read, and Athena needs both under the **caller's own** identity — it writes results through a forward access session, so there is no separate service grant to make. **Deliberately absent and named so** ([Lesson 5](../../docs/plan/lessons.md)): `DeploymentManagerAccess` and `GovernanceManagerAccess`, because an approver does not read the data it approves on (D31); Stage 6's project execution roles, which do not exist yet (INT-15) and join as a **second element of `Principal`** — the extension point step 9.3 asks for |
| *(caller-supplied)* `var.additional_data_key_policy_statements` | **`v0.3.0`, 2026-08-26 — the extension point above, delivered by the first caller that needed one.** KMS holds **one** policy per key, so a second reader can only arrive through the module; the input is `any`, defaults **empty**, and is `concat`ed after the two statements above. **Structure in the module, values in the slice** — the split `vpc-egress-v0.3.0` made for the DNS allow-list. The shape that arrived is a second **statement**, not the predicted second `Principal` element, because the new reader is not a human persona. **Anything passed here is a widening of D31 and belongs in the calling slice's own row.** Today exactly one caller passes anything: `sandbox/data/` adds `AllowSandboxLakeAccessRoleViaS3` — `awsds-sandbox-lake-access` with `Decrypt`/`GenerateDataKey`/`DescribeKey` under the same `kms:ViaService` pin, for [Stage 16](../../docs/plan/stages/stage-16-sandbox-lake.md)'s bucket. `development/data/` passes nothing and its plan across the bump must read **`No changes`** — that empty plan is the proof the default protected it |

## `buckets.tf` — the derived zone, `awsds-<env>-derived`

One designed destination per consumer account, **not two**: D13's own wording makes `scratch` a *class* of
non-registered prefix rather than a named bucket, and a second bucket would need either a third CMK the cost
model does not carry or a key shared for no reason (settled 2026-08-19, with the user).

| `Sid` | What it denies |
|---|---|
| `DenyInsecureTransport` | `s3:*` where `aws:SecureTransport = false`. The `s3-bucket` module's own statement, on every bucket in both trees — S3 holds exactly **one** policy per bucket, so the caller's statements are appended through `additional_policy_statements` rather than attached as a second policy |
| `DenyStalePresignedUrls` | `s3:*` where `s3:signatureAge > 900000` ms. The one branch of the lake's perimeter worth copying onto a bucket holding **copies**: a presigned link is a bearer credential and 15 minutes bounds how long a leaked one works. The preventive counterpart of Stage 11's presigned-URL detection |

The bucket's other properties come from `s3-bucket` v0.3.0 and are not restated here: all four public-access
blocks on, versioning, SSE-KMS under the account data key with Bucket Keys, abort-incomplete-multipart at 7 days,
noncurrent-version expiry — plus `expiration_days = 30`, which is **v0.3.0's reason for existing**: expiring
noncurrent versions reaches nothing that was never overwritten, and D19 practice (iii) is about the current
object. `DL-9` checks the rule exists, never the number.

### The three prefix families — three different contracts

**The prefixes are not created here, and that is not an omission**: S3 has no directories, so a prefix exists
when an object is written under it. What makes them real is the identity-side statement in `identity/sso/`
that scopes `s3:PutObject` to them and to nothing else — which is why these names are a **contract between
two slices in two accounts**, written out in one place a human reads.

| Prefix | Grain, and what enforces it |
|---|---|
| `results/` | The workgroup's **enforced** output location. **Per-persona, not per-person** — an enforced workgroup has exactly one result location, and that is the ceiling on the whole design ([`docs/GOVERNANCE.md`](../../docs/GOVERNANCE.md), "The grain"): the system's real grain is min(SQL grain, derived-zone grain) |
| `derived/${aws:userid}/` | **Per principal on the WRITE** (D19 practice ii) — the one genuinely per-user control in the design, and it governs the **copy** rather than the source ([Lesson 1](../../docs/plan/lessons.md)'s shape). **The read is persona-wide** since pass 4c: `ReadDerivedZoneObjects` names `derived/*` with no `${aws:userid}` segment, so the per-principal split is on the write alone — what keeps *another persona* out of a materialised result is the account data CMK above (D31), never the prefix |
| `scratch/` | The notebook's working files — a downloaded CSV, an intermediate feature, a checkpoint. Non-registered by definition, so plain IAM, which is exactly what D13 says about this class. **The only prefix where the persona may delete** (`DeleteScratchObjects`) |

**Stage 11 scope, declared here because Stage 11 cannot discover it**: this bucket is in Macie's scan scope
and carries CloudTrail data events (D19 practice iv). It is where sensitive data actually accumulates, and it
sits **outside** the account Macie primarily watches.

## `athena.tf` — the enforced workgroup, `awsds-<env>-athena`

| Setting | What it does once applied |
|---|---|
| `enforce_workgroup_configuration = true` | **The control, and everything else on this resource is ordinary.** The console calls it "override client-side settings"; without it the result location is whatever the client asks for, which makes the derived zone a suggestion and D19 practice (i) a comment |
| `result_configuration.output_location` | `s3://awsds-<env>-derived/results/` — **into the derived zone**, not into a results bucket of its own: query output lands under the lifecycle, the CMK and the Macie scope designed for it, instead of in a second, undesigned copy zone |
| `result_configuration.encryption_configuration` | `SSE_KMS` under the account's data key, **stated rather than inherited** from the bucket default: the workgroup writes the object, so the encryption choice is visible where somebody reads it. Same key, so the two cannot disagree |
| `bytes_scanned_cutoff_per_query` | 10 GiB by default. Athena bills USD 5/TB ([`docs/PRICING.md`](../../docs/PRICING.md)), so this is the guard on a query nobody meant to run: over the limit the query is **cancelled**, which bounds what a runaway can bill rather than zeroing it — the bytes scanned up to the cancellation are billed — and raising it is a deliberate act with a number attached |
| `publish_cloudwatch_metrics_enabled = false` | Workgroup metrics are CloudWatch **custom** metrics and billed as such; nothing reads them yet. Stage 12 turns this on with a consumer in hand |
| `state = "ENABLED"`, no `force_destroy` | `[P]` by D11: a workgroup costs nothing at rest, and destroying it would orphan the query history that explains what was run |
| — (absent) the `primary` workgroup | **Deliberately left alone** ([Lesson 5](../../docs/plan/lessons.md)). Athena creates it in every account and it enforces nothing; what keeps a persona out of it is not a setting there but `RunQueriesInTheEnforcedWorkgroups` in `identity/sso/`, which scopes `athena:StartQueryExecution` to **this** workgroup's ARN and to no other. Adopting an object this module did not create, in every account, for a defence the identity plane already provides, is the trade declined |

`DL-8` reads the enforcement flag, the limit and the output location per account.

## `lakeformation.tf` — the settings, the links, the re-grants

### The settings — the account joins Lake Formation at all

| Attribute | What it does once applied |
|---|---|
| `admins` — *and `var.additional_data_lake_admin_role_arns`, `v0.4.0`* | **`v0.4.0`, 2026-08-26: no longer "alone" in every account, and the change is an ADOPTION.** `admins` is a list this resource replaces **wholesale**, exactly like `parameters` — and SageMaker Unified Studio **adds itself to it**: the first project created in Sandbox (2026-08-22) left `awsds-sandbox-smus-manage-access` and `awsds-sandbox-smus-provisioning` standing as data lake administrators. Nobody in this repository asked for them ([Lesson 17](../../docs/plan/lessons.md)) and **no gate here could see it** — `DL-5` reads `parameters`, not `admins` — so it surfaced only when [Stage 16](../../docs/plan/stages/stage-16-sandbox-lake.md) ran a plan for an unrelated reason. **`development/data/` re-plans `No changes`, which is what attributes the cause**: it has no project. The list input is empty by default and `sandbox/data/` passes the two; applying the narrow list instead would have stripped live administrators from the service whose create path Stage 6 measured *after* they existed. **What adoption does not settle:** whether a SMUS provisioning role *should* administer Lake Formation — an administrator can grant itself anything in the local catalog, the resource links included. That is a Stage 6 residue, not a property of this variable |
| `allow_full_table_external_data_access` — *`var.…`, `v0.4.0`* | **`null` by default (undeclared), which is what a consumer with no SMUS project wants.** Sandbox reads back **`true`**, set by the service beside the two administrators above; `sandbox/data/` declares it so the plan stops proposing to reset it. **Read from the account, not chosen here** — the same discipline `parameters` has carried since pass 4 |
| `admins` — *the original row* | `InfrastructureAccess` **alone** (decision 5), resolved by pattern in the caller. AWS requires at least one data lake administrator in the **receiving** account before a shared resource is visible there: measured `[]` on both consumers 2026-08-19, while both already held their shares `ACTIVE` and `glue:GetDatabases` returned nothing — an empty consumer catalog has two causes that look identical, and only the RAM side separates them (`DL-7` reports the branches apart since pass 3) |
| `parameters` | `CROSS_ACCOUNT_VERSION = 4`, `SET_CONTEXT = TRUE`, written **from the reading** and never from memory. This resource replaces the whole `DataLakeSettings` structure: naming admins while omitting parameters resets the version to 1, after which every share appears to succeed and never arrives. **INT-11's hazard is symmetric** — it was written about the producer, and both consumers turned out to carry 4/TRUE already, set by nobody in this repository and defended by nobody until pass 4 |
| the two `Create*DefaultPermissions` blocks | **Omitted, which clears them.** Omission is the only expressible form (`= []` is refused because they are blocks, and `{}` declares one entry rather than zero), and they act at **creation** time — so a resource link created before they clear is born deferring to plain IAM, with no error anywhere. Hence the two-step apply above, per account |

### The resource links — two, and `dropbox` is absent by design

A resource link is a **local catalog database** pointing at a shared one; it is what makes the lake's `raw`
and `curated` addressable from an Athena query in this account. Without it the share is held and unusable.

| Link | Shape |
|---|---|
| `link["raw"]`, `link["curated"]` | Local name **= target name**, deliberately: a query written in Sandbox, in Development, or against the lake itself then reads identically — a prefixed local name would give one table three spellings. The target is addressed through the producer's catalog id, resolved live by the caller's aliased provider |
| — (absent) `dropbox` | Filtered out of `var.lake_databases`, and **its absence is the design working** ([Lesson 29](../../docs/plan/lessons.md)): the producer's share is gated on `layer ∈ {raw, curated}`, so the letterbox never travelled. The map comes from the lake slice's own output, so a `dropbox` key appearing in it means the gate changed on the producer side — a **finding**, not a convenience |

### The four re-grants — why a re-grant exists at all

A cross-account grant lands on the **account**, never on a principal inside it. Nothing here can read a row
until this account's own data lake administrator passes the permission on to a local principal — which is why
every producer-side grant carries the grant option, and why an administrator may pass on only what it
received with it. **Two grants per shared object, and they are not interchangeable**; the half people miss is
the first.

| Grant | Principal | Permission | What it buys |
|---|---|---|---|
| `link_describe` (×2) | `DataScientistAccess` | `DESCRIBE` on each **link** | Makes the local link **visible** in the catalog. Without it the persona sees no database at all, even holding every permission on the target |
| `shared_databases` | idem | `DESCRIBE` over `layer ∈ {raw, curated}`, on the **producer's** catalog id | The container, metadata only. **No `classification` gate, deliberately**: `curated`'s database carries no classification (fail-closed by absence, decision 1), so an expression naming it would not match — and a database that does not match cannot be read through its link |
| `shared_tables` | idem | `SELECT` + `DESCRIBE` over `layer ∈ {raw, curated}` **AND** `classification ∈ {public, internal}` | The rows. Two `expression` blocks in one grant is an **AND**; two grants would be an OR and would hand back the drop-box the `layer` gate excludes. `restricted` and `personal` are absent **by enumeration**, which is what makes this also the column proof: `curated.sample_trades.counterparty` is expected to be missing from this persona's **column list** (verification x — read as a column list, the table having been applied empty) |

Two properties hold across all four. **The value lists are literal**, exactly as on the producer side and for
the same reason: they are a **subset**, and a `layer` or `classification` value added to the ontology tomorrow
must not join a persona's reach by inheritance. And **no `permissions_with_grant_option` anywhere** — the
account received the option so that its administrator could pass the permission on, and these four *are* that
passing on; a resource shared with an account may be granted only to principals **in** it, never onward.

## What the caller supplies, and what it republishes

Everything that differs between the two callers is in `variables.tf` and nothing else is (Lesson 14) — the
descriptions there are the one copy. What matters to a reader outside this module is the other direction:
`outputs.tf` republishes the derived bucket's name and ARN, the data key's ARN and alias, the workgroup's name
and ARN, and the resource-link names — and **`terraform-live/identity/sso/` reads them through
`terraform_remote_state` at pass 4c**, which is why the persona statements name resources exactly instead of
wildcarding, and why `identity/sso/` applies *after* both `data/` slices.

---

## Pointers

| Question | File |
|---|---|
| The governance model — the LF-Tag ontology, the grant rules, the grain | [`docs/GOVERNANCE.md`](../../docs/GOVERNANCE.md) |
| **What governs the lake itself** — its perimeter, the drop-box asymmetry, the tag assignments, the shares | [`terraform-live/data-governance/data/README.md`](../../terraform-live/data-governance/data/README.md) |
| **The identity half of every row above** | [`terraform-live/identity/sso/README.md`](../../terraform-live/identity/sso/README.md) — the persona's own statements; `./aws/datalake.py` `DL-12` measures the drop-box write's |
| Which triples are **applied**, in which account, on which date | [`docs/AWS_STATE.md`](../../docs/AWS_STATE.md) §"Lake Formation grant register" |
| The two-step apply, and the tag order a module change needs | [`docs/plan/runbooks/terraform-changes.md`](../../docs/plan/runbooks/terraform-changes.md) — Recipes D and B |
| Why a module is consumed by tag, and the rung order when a module calls a module | [`terraform-modules/README.md`](../README.md) |
