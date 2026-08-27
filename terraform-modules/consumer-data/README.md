# `consumer-data` — the lake's consumer side, one module applied twice

The Stage 5 pass 4 module ([stage file](../../docs/plan/stages/stage-05-data-foundation.md); the governance
model's one copy is [`docs/GOVERNANCE.md`](../../docs/GOVERNANCE.md)). Called by
[`terraform-live/sandbox/data/`](../../terraform-live/sandbox/data/) and
[`terraform-live/development/data/`](../../terraform-live/development/data/) — both thin, both `[P]`, both
pinning the module **by git tag** — and by every further business unit's Sandbox once D35's N
passes 1. **The design lives here once; a slice says which account, never what.** That is also why this
index is in the module and not in the slices: two copies of one design drift on the first divergence.

> **`v0.6.0` (2026-08-26) REMOVED the derived zone and the enforced workgroup** —
> [D19 revised](../../docs/plan/decisions/D19-derived-zone.md): the zone is re-homed onto the SMUS
> project path (`awsds-<env>-smus-projects`, `terraform-modules/sagemaker-prereqs/`'s bucket), and the
> persona's direct Athena path left `identity/sso/` in the same revision. The struck sections below are
> kept as the record of what the module built from v0.1.0 to v0.5.0; `git log` and the tags carry the
> code. `DL-8`/`DL-9` now measure the ABSENCE of what they used to verify.

What lands in **each** consumer account when this module applies:

| Object | Name |
|---|---|
| the account's data CMK | `alias/awsds-<env>-data` — since v0.6.0 with **no persona statement**: its consumers arrive only through `additional_data_key_policy_statements` (today: the sandbox lake's access role, in Sandbox alone; Development's key is held empty, dated) |
| the account's own Lake Formation seat | `aws_lakeformation_data_lake_settings` — admins, `parameters`, the cleared create-defaults |
| the shared lake, made addressable | 2 resource links (`raw`, `curated`) + 4 re-grants |
| ~~the derived zone~~ | ~~`awsds-<env>-derived`~~ — **removed at v0.6.0** |
| ~~the enforced query path~~ | ~~workgroup `awsds-<env>-athena`~~ — **removed at v0.6.0**; the query surface is the SMUS project workgroup |

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

Since pass 4c the trap had a second edge: seven identity-side statements split by *which* state they
read. **Five of the seven left on 2026-08-26 with the derived zone** (`RunQueriesInTheEnforcedWorkgroups`,
`UseDerivedZoneBuckets`, `ReadDerivedZoneObjects`, `WriteDerivedZonePrefixes`, `DeleteScratchObjects` —
they enumerated this module's removed objects, and `identity/sso/` stopped reading this state with them).
The two that stand, `WriteIngestionDropBox` and `UseLakeDataKeyViaS3`, name the **lake's** drop-box
prefix and data key, read from `data-governance/data/`'s state — the ingestion path, untouched by the
revision. [Lesson 28](../../docs/plan/lessons.md): **verify the pair, and remember the two halves are in
different accounts.** `./aws/datalake.py` measures both sides — `DL-12` the identity half of the drop-box
write, `DL-5`/`DL-6`/`DL-7` the Lake Formation half, `DL-8`/`DL-9` the **absence** of the workgroup and
the derived bucket.

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
| ~~`AllowDataScientistUseViaS3`~~ | **Removed at `v0.6.0` (2026-08-26), and the removal is a TIGHTENING**: the statement granted the persona `Decrypt`/`GenerateDataKey` via S3 because the derived zone encrypted here and the persona read it (D31). With the zone re-homed onto the SMUS project path, the only bucket left under this key is the sandbox lake — reached **only** through vended, prefix-scoped access-role credentials — and keeping the persona statement would have granted a KMS-layer path around that vending door. Stage 5 step 9.3's "second element of `Principal`" extension point died unconsumed with it: a project role never needed this key |
| *(caller-supplied)* `var.additional_data_key_policy_statements` | **`v0.3.0`, 2026-08-26 — the extension point above, delivered by the first caller that needed one.** KMS holds **one** policy per key, so a second reader can only arrive through the module; the input is `any`, defaults **empty**, and is `concat`ed after the two statements above. **Structure in the module, values in the slice** — the split `vpc-egress-v0.3.0` made for the DNS allow-list. The shape that arrived is a second **statement**, not the predicted second `Principal` element, because the new reader is not a human persona. **Anything passed here is a widening of D31 and belongs in the calling slice's own row.** Today exactly one caller passes anything: `sandbox/data/` adds `AllowSandboxLakeAccessRoleViaS3` — `awsds-sandbox-lake-access` with `Decrypt`/`GenerateDataKey`/`DescribeKey` under the same `kms:ViaService` pin, for [Stage 16](../../docs/plan/stages/stage-16-sandbox-lake.md)'s bucket. `development/data/` passes nothing and its plan across the bump must read **`No changes`** — that empty plan is the proof the default protected it |

## ~~`buckets.tf` — the derived zone~~ · ~~`athena.tf` — the enforced workgroup~~ — REMOVED at `v0.6.0`

**Both files left the module on 2026-08-26** ([D19 revised](../../docs/plan/decisions/D19-derived-zone.md)
— the user's decision, on the same day Stage 6 step 2.4 measured the Tooling blueprint already building
an enforced results location and a mounted working folder **per project**). What they built, for the
record — `awsds-<env>-derived` (one bucket, three prefix families: `results/` enforced output,
`derived/${aws:userid}/` per-principal write, `scratch/` the one delete), 30-day expiry, the
`DenyStalePresignedUrls` branch, and `awsds-<env>-athena` with `EnforceWorkGroupConfiguration = true`
and a 10 GiB scan cap — is in the tags up to `consumer-data-v0.5.0` and in D19's history; the surviving
zone's contracts are [`docs/GOVERNANCE.md`](../../docs/GOVERNANCE.md) §"Derived zone".

Two absences that were design remain worth knowing after the removal: the **`primary` workgroup was
never adopted** (Lesson 5 — what kept a persona out of it was the identity-side scoping, which left with
the run family), and the presigned-URL cap now exists only on the lake's own buckets — the projects
bucket's equivalent is `sagemaker-prereqs`' to decide, not this module's.

## `lakeformation.tf` — the settings, the links, the re-grants

### The settings — the account joins Lake Formation at all

| Attribute | What it does once applied |
|---|---|
| `admins` — *and the `lifecycle` block, `v0.5.0`* | **`v0.5.0`, 2026-08-26: the list is the service's; Terraform keeps one create-time seat.** `admins` is replaced **wholesale**, like `parameters` — and SageMaker Unified Studio **adds itself to it**: the first project created in Sandbox (2026-08-22) left `awsds-sandbox-smus-manage-access` and `awsds-sandbox-smus-provisioning` standing as data lake administrators, with `allow_full_table_external_data_access = true` beside them. Nobody here asked for them ([Lesson 17](../../docs/plan/lessons.md)) and **no gate could see it** — `DL-5` reads `parameters`, not `admins` — so it surfaced only when [Stage 16](../../docs/plan/stages/stage-16-sandbox-lake.md) ran a plan for an unrelated reason; `development/data/`, with no project, re-planned `No changes`, which attributed the cause. **`v0.4.0` adopted the two seats as inputs and was wrong in the way that matters**: it froze the list, so a seat the service adds *tomorrow* would be deleted by the next apply — the same failure one seat out. `v0.5.0` removes the inputs and declares ownership instead: `admins = [var.data_lake_admin_role_arn]` at create, `ignore_changes = [admins, allow_full_table_external_data_access]` after — the [`catalog.tf` Iceberg-columns shape](../../terraform-live/data-governance/data/catalog.tf), Lesson 23. **Measured, not believed**: with Sandbox holding **three** administrators live and the config declaring **one**, the plan reads `No changes`. **The plan's defence is replaced, not dropped**: `./aws/datalake.py` **`DL-13`** reads the list per account, fails on the required seat's absence, and reports every extra seat — because the load-bearing seat's *loss* would otherwise go unnoticed (an account with no administrator sees an **empty catalog**, measured 2026-08-19). Whether SMUS *should* hold the seats is [open question 24](../../docs/plan/open-questions.md) |
| `admins` | `InfrastructureAccess` **alone** (decision 5), resolved by pattern in the caller. AWS requires at least one data lake administrator in the **receiving** account before a shared resource is visible there: measured `[]` on both consumers 2026-08-19, while both already held their shares `ACTIVE` and `glue:GetDatabases` returned nothing — an empty consumer catalog has two causes that look identical, and only the RAM side separates them (`DL-7` reports the branches apart since pass 3) |
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
`outputs.tf` republishes the data key's ARN and alias and the resource-link names. **Nothing reads them
through remote state any more**: `identity/sso/`'s pass-4c lookup left on 2026-08-26 with the statements
that consumed it, so the old apply-ordering constraint (sso after both `data/` slices) survives only in
reverse — the REMOVAL applies sso first, then the slices (Stage 6 step 2.6's choreography).

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
