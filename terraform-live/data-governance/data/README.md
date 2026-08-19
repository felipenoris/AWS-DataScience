# data-governance/data — the governed lake, layer `[P]`

The Stage 5 slice ([stage file](../../../docs/plan/stages/stage-05-data-foundation.md); the
governance model's one copy is [`docs/GOVERNANCE.md`](../../../docs/GOVERNANCE.md)). Applied as
`awsds-infra-data`. **`./aws/datalake.py` `DL-5` brackets every apply of this slice** — read it
before and after; a reset `CROSS_ACCOUNT_VERSION` fails every share silently, days later (INT-11).

What lands here by pass:

| Pass | Content |
|---|---|
| 1 | the account data CMK (`alias/awsds-data-data`; named `zn-lab` until the 2026-08-19 revision); the five buckets with the perimeter and drop-box statements; the settings trio (admins + parameters + emptied defaults, **before any database**); registrations + the LF-Tag ontology; databases `raw`/`curated`/`dropbox`; the sample Iceberg table with its `restricted` column; the maintenance role, its LF grants, two on-demand crawlers, the compaction optimizer |
| 2 | step 6 — the governance manager's own grants (`governance.tf`); the consumer TBAC grants are pass 3's, with the shares they ride on |
| 3 | step 7 — the two cross-account shares (`shares.tf`) + the INT-11 after-reading |

## The first apply is two steps, and that is not a preference

`aws_lakeformation_data_lake_settings` must clear the two `IAM_ALLOWED_PRINCIPALS` defaults **before any
database exists** — they act at creation time — and **the plan cannot prove it does** (both blocks are
Computed; an explicitly empty list is not expressible in `aws ~> 6.60`). So:

```bash
AWS_PROFILE=awsds-infra-data terraform -chdir=terraform-live/data-governance/data apply -target=aws_lakeformation_data_lake_settings.this
```

then `./aws/datalake.py` (`DL-5` parameters, `DL-6` defaults) — and only then the full apply. If `DL-6`
still names `IAM_ALLOWED_PRINCIPALS`, revoke and re-read first. The reasoning is in `lakeformation.tf`
beside the resource and in the stage file's 5.2 callout. **Measured 2026-08-18: omission clears** — and
the read-back stays anyway, because that is provider behaviour the plan still does not state
([Lesson 27](../../../docs/plan/lessons.md); the procedure is the terraform-changes runbook's
**Recipe D**).

Every bucket here is **undeletable** while the Data OU SCP is attached — names are permanent.

---

# The controls, one row each

**The same discipline [`org-policies/POLICIES.md`](../../identity/org-policies/POLICIES.md) keeps for
organization policies, applied to this slice**: a statement, a tag assignment or a grant that is added,
removed, renamed or re-conditioned in the `.tf` files **is a change to this file, in the same sitting**.
The `.tf` files carry the *reasoning* in comments beside each resource; this file is the **index** — what
exists, and what it does once applied — so that "what governs this lake" can be answered without reading
six files.

**What is not here**: applied grant triples with their dates, which live in
[`docs/AWS_STATE.md`](../../../docs/AWS_STATE.md) §"Lake Formation grant register" — duplicating them
would produce a second, staler answer. This file describes what the **code** declares; that one records
what is **deployed**.

## A permission here is the intersection of two systems, never one of them

**The single most misleading thing about this slice, and it is worth reading before any row below.**
Lake Formation runs its own authorization layer *on top of* IAM. For a principal to do anything with the
catalog, two independent grants must both exist:

| Half | Where it lives | What it decides |
|---|---|---|
| the **IAM** action | `identity/sso/` for personas; `maintenance.tf` / `lakeformation.tf` for service roles | whether the API **call** is permitted |
| the **Lake Formation** permission | this slice — `governance.tf`, `maintenance.tf` | what the call **returns**, or whether it succeeds at all |

The trap is that the natural unit to read is a *slice*, and the slice is never the authorization unit —
the two halves sit in different accounts, different slices and different stages. A reading of
`identity/sso/policies-approvers.tf` alone says the governance manager may tag datasets; before pass 2
that was false, and the failure mode was an **empty catalog listing**, not an error. It runs in reverse
too: revoke an LF grant and the IAM policy still describes the capability. **Verify the pair.**

The second, quieter half of the same fact: with Lake Formation enforcing, `glue:GetDatabases` and
`glue:GetTables` return **only what the caller holds LF permissions on**. A missing grant therefore looks
like an empty list rather than an access denial — [Lesson 13](../../../docs/plan/lessons.md)'s shape, so
never read an empty catalog as "nothing exists".

## `lakeformation.tf` — the settings, the registrations, the ontology

| Resource / attribute | What it does once applied |
|---|---|
| `aws_lakeformation_data_lake_settings` · `admins` | `InfrastructureAccess` **alone** (decision 5). The governance manager is deliberately absent — an approver who can already grant everything exercises no control (Lesson 9, D31). Stage 6's DataZone fulfilment principal is the named revision trigger |
| — · `parameters` | `CROSS_ACCOUNT_VERSION = 4`, `SET_CONTEXT = TRUE`, written **from the reading** and never from memory. This resource **replaces the whole structure**: naming admins while omitting parameters resets the version to 1, after which every share appears to succeed and never arrives (INT-11, the silent failure `DL-5` brackets) |
| — · the two default-permission blocks | **Omitted**, which clears them (measured). Their applied state grants `ALL` to `IAM_ALLOWED_PRINCIPALS` *at creation time*, so a database created before this lands is born deferring to plain IAM — D13 as decoration, with no error anywhere |
| `aws_lakeformation_resource.raw` / `.curated` | Registers the two prefixes: reads stop being "whoever holds `s3:GetObject`" and become "the engine asks Lake Formation". **`dropbox`, `artifacts` and `logs` stay unregistered by design** — D13's non-registered class, plain IAM/bucket-policy control. Deregistration is denied by the Data OU SCP |
| `aws_lakeformation_lf_tag.classification` | `public` / `internal` / `restricted` / `personal` — the DLP dimension. The default grant reaches the first two read-only; the other two travel only on enumerated grants |
| `aws_lakeformation_lf_tag.layer` | `dropbox` / `raw` / `curated` — pipeline position. **Does not gate the default read**: both registered layers are readable by consumers, the deviation argued in `institutional-delta.md` |
| — (absent) `businessunit` | **Reserved, deliberately not created**: an LF-Tag requires at least one value and the dimension has none at N=1 (D35) |
| — (removed) `security-zone` | Existed 2026-08-18/19 (`zn-lab` only) and was **withdrawn by the user's revision**: no TBAC expression ever used it, and no AWS mechanism ties an LF-Tag to a CMK — encryption is per account (`GOVERNANCE.md` §Encryption) |

## `catalog.tf` — the tag assignments, and the asymmetry that is the whole design

Tags **inherit downward** — database → tables → columns — unless overridden at the lower level, so what
a database carries is what every future table there starts with.

| Assignment | Applied tags | Why this shape |
|---|---|---|
| database `raw` | `layer=raw`, `classification=internal` | **Fail-open, the user's decision** (decision 1, against the recommendation): ETL development is not gated per dataset. The named consequence — an unclassified arrival is readable by every user until reclassified; Macie is the Stage 11 backstop |
| database `dropbox` | `layer=dropbox`, `classification=internal` | Same rationale — user-supplied arrivals. Its own database so crawler-inferred tables do not wear `raw`'s value wrongly |
| database `curated` | `layer=curated` — **no `classification`** | **Fail-closed by absence**, and this is the designed asymmetry: an untagged curated table matches **no** TBAC expression and is therefore invisible to the default grants. Tables here are classified explicitly at creation |
| table `curated.sample_trades` | `classification=internal` | Declares its own, since the database carries none |
| column `sample_trades.counterparty` | `classification=restricted` | **Most-specific wins.** This is the column the classification pair proves against: absent from a default session's result *and* from its column list, present after the explicit grant |

## `kms.tf` — the account data key policy

One key for the whole lake, drop-box included (decision 2 as revised 2026-08-19: one data CMK per
account, and this account holds the five lake buckets). The policy is **passed, not defaulted**, because
two cross-account statements must ride on the key object itself.

| `Sid` | What it allows, and to whom |
|---|---|
| `EnableIamPolicyDelegationInThisAccount` | The account root — the standard delegation that lets IAM policies in this account govern the key. Without it the key is only governed by its own policy |
| `AllowDropBoxWritersViaS3` | The Sandbox and Development roots, narrowed by `ArnLike aws:PrincipalArn` to the writer roles: `GenerateDataKey` **and** `Decrypt`. Both are needed — SSE-KMS `PutObject` needs the first, a **multipart upload** needs the second, and the error otherwise names S3 rather than KMS. Scoped `kms:ViaService = s3`, so the persona cannot use the key outside an S3 call. **This is the resource HALF of a cross-account permission** — the identity half (`UseLakeDataKeyViaS3` in `DataScientistAccess`, the same two actions under the same `kms:ViaService = s3` condition) lives in `identity/sso/`, Stage 5 pass 4c; neither half works alone (Lesson 28, amended) |
| `AllowCloudWatchLogsEncryptionForGlue` | The **service principal** `logs.<region>.amazonaws.com`, scoped by the log-group encryption context to `/aws-glue/*` in this account. CloudWatch Logs encrypts with the key *itself*, so the crawler role's own KMS grant does not cover it — this exists because a crawler samples object contents and its logs therefore take the lake key |
| `AllowProductionPickupDecryptViaS3` | The Production root narrowed to `awsds-prod-job-exec`: `Decrypt`, for the drop-box pickup (INT-10, D25). **The role arrives at Stage 9** — until then the `ArnLike` matches nothing, which is the recorded "pickup half unexercised" state, not a defect |

**What the single key costs, and it is a choice rather than an oversight** (decision 3's deviation):
these grants land on the **account** key, so at the KMS layer the matched principals reach every lake
bucket. The drop-box's isolation rests on the S3 statements and Lake Formation **alone**. Revision
trigger: the first dataset whose blast radius argues for a key of its own.

## `buckets.tf` — the S3 permission controls

### The perimeter — on **every** one of the five buckets

| `Sid` | What it denies |
|---|---|
| `DenyOutsideTrustedNetworks` | `s3:*` to every principal **unless** one of three branches matches. It is a `Deny` with negated conditions, so a caller matching *no* branch is refused |
| `DenyStalePresignedUrls` | `s3:*` where `s3:signatureAge > 900000` ms. A presigned link is a **bearer credential**; 15 minutes bounds how long a leaked one works. The preventive counterpart of Stage 11's presigned-URL detection |

The three branches of `DenyOutsideTrustedNetworks`, and why each is written the way it is:

| Branch | Condition | The rule behind it |
|---|---|---|
| 1 | `aws:SourceVpce` ∈ the consumers' **gateway** endpoint ids | **Never the `[E]` interface endpoints** ([Lesson 3](../../../docs/plan/lessons.md), INT-05): those change id on every `make up` and live in accounts this policy could never repair itself against. Anchored on `[P]` state, read live, never pasted |
| 2 | `aws:SourceIp` ∈ the WireGuard Elastic IPs | D18's laptop path. A **list**, per D35 — one entry per VPN home |
| 3 | `aws:PrincipalAccount` = this account | The stage's own "looser and easier to get right" option, **taken deliberately** over naming the maintenance role alone: the crawler runs in Glue with no VPC and no tunnel (D27's collision), and the infrastructure user works off-VPN by decision (open question 17a). A role-only branch would lock the account's own administrator out of its own lake |

And two carve-outs the deny **must** carry or it breaks the design it protects:

| Carve-out | Without it |
|---|---|
| `aws:ViaAWSService` (`BoolIfExists`, false) | D13 forces every tabular read through Lake-Formation-vended access, which arrives as a service-on-behalf call — a bare `SourceVpce` deny makes step 6 unusable |
| `aws:PrincipalIsAWSService` (`BoolIfExists`, false) | A service principal presents no VPC, no IP and no account. CloudTrail delivering Stage 11's data-event trails into `awsds-data-logs` would be eaten by the deny |

### The drop-box — three principals, three statements, nobody holding two of the three

This asymmetry **is** the design (D18, D25, D27): it is what keeps the drop-box from becoming the
general-purpose exchange bucket D18 refuses to build.

| `Sid` | Principal | Grants | The asymmetry |
|---|---|---|---|
| `AllowInteractiveWriterPutOnly` | Sandbox + Development roots, `ArnLike` to the writer roles | `s3:PutObject` on the dated prefix | **No read-back, no list, no delete.** Confirmation is the `PutObject` response; re-uploading a corrected file is an ordinary overwrite and versioning keeps the prior copy internally. **This is the resource HALF of a cross-account permission** — the identity half (`WriteIngestionDropBox` + the KMS pair, mirrored scoping) lives in `identity/sso/`, Stage 5 pass 4c |
| `AllowProductionPickupReadDelete` | Production root, `ArnLike` to `awsds-prod-job-exec` | `GetObject` + `DeleteObject` | Reads **and** empties — a letterbox nobody empties fills up. Stage 9's half |
| `AllowProductionPickupList` | idem | `ListBucket`, `s3:prefix` scoped | Listing is separate because it is a **bucket** action, not an object one |
| `AllowMaintenanceSchemaRead` | the maintenance role | `GetObject` + `ListBucket` | Reads to infer schema, **cannot delete**. Same-account IAM would suffice (its inline policy carries the read) — the statement is here so the whole asymmetry is readable in **one place** |

**A bucket policy validates its `Principal`**, so statements naming roles that do not exist yet
(`awsds-prod-job-exec`, the Stage 6 project roles) name the **account root** and narrow with an `ArnLike`
condition. That is why the principals above read as roots.

## `maintenance.tf` and `lakeformation.tf` — the two service roles

| Role | `Sid` | What it is for |
|---|---|---|
| `awsds-data-catalog-maintenance` | `GlueServiceOnly` (trust) | Trusts `glue.amazonaws.com` **alone** — the name is an SCP contract (D27's carve-out names it), so a typo fails closed, later |
| | `CrawlRawAndDropBox` | `GetObject`/`ListBucket` on the two crawled prefixes |
| | `CompactCuratedWarehouse` | Read **and write** on curated — compaction rewrites files (decision 4) |
| | `UseDataKey` | The account data CMK: everything above is SSE-KMS |
| | `CatalogReadWrite` | The Glue catalog calls a crawler and an optimizer make |
| | `ReadOwnSecurityConfiguration` | **A role must be able to READ the security configuration it runs under.** `Resource = "*"` because Glue security configurations have no ARN to scope to. Nothing in the stage text said so — the first `CreateCrawler` failed on it |
| | `VendedDataAccess` | `lakeformation:GetDataAccess` — the registered-location read path |
| | `CrawlerLogs` | `/aws-glue/*` only, encrypted by the key-policy statement above |
| `awsds-data-lf-registration` | `S3ReadRegisteredLocations` | How Lake Formation **vends** governed reads of `raw` and `curated`. Read-side only — the governed write arrives at Stage 9, amending this policy in this slice |
| | `KmsDecryptDataKey` | The SSE-KMS half of the same path. The service-linked role cannot be granted the CMK cleanly, which is why this is a custom role |

### The maintenance role's own Lake Formation grants (`maintenance.tf`)

The IAM `Sid`s above are only one half (see §"A permission here is the intersection of two systems"):
with the IAM-fallback defaults emptied, catalog writes are governed by Lake Formation, so the role needs
grants of its own. All four are **operational**: same-account, **named-resource, deliberately not TBAC** —
tag-based access is the *consumer* method, and this is machinery.

| Grant | Resource | Permission | What it buys |
|---|---|---|---|
| `maintenance_create_raw` | database `raw` | `CREATE_TABLE`, `DESCRIBE` | The whole crawler need: a crawler-created table grants its creator `ALL` automatically, so nothing has to be granted per table |
| `maintenance_create_dropbox` | database `dropbox` | `CREATE_TABLE`, `DESCRIBE` | Idem, for the drop-box crawler |
| `maintenance_raw_location` | the registered `raw` prefix | `DATA_LOCATION_ACCESS` | Creating tables that point **into** a registered location. `dropbox` is unregistered by design, so no location grant exists to need |
| `maintenance_compact_sample` | table `curated.sample_trades` | `SELECT`, `INSERT`, `ALTER`, `DESCRIBE` | The four verbs compaction rewrites files with (decision 4) |

Applied triples with their dates stay in [`docs/AWS_STATE.md`](../../../docs/AWS_STATE.md)'s grant
register, which already carries all four; these rows say what the **code** declares.

## `governance.tf` — the governance manager's grants (pass 2, step 6)

The first grants made to a **human persona**, and the delivery of decision 5's second half: the
governance manager is never an admin and receives *specific grants* instead. The set implements the
permission set's own one-line description — *"The catalog, never the rows."*

| Grant | Principal | Permission | What it buys |
|---|---|---|---|
| `gm_associate_*` (×2 — a third, on `security-zone`, left with the tag in the 2026-08-19 revision) | `AWSReservedSSO_GovernanceManagerAccess_*`, resolved **by pattern** | `ASSOCIATE` on each LF-Tag key | Assigning tags to datasets — the job `GOVERNANCE.md` gives the persona. Granting `ASSOCIATE` implicitly grants `DESCRIBE` on the tag. Values are read from the tag resources, so a value added to the ontology cannot be silently missing here |
| `gm_describe_database` (×3) | idem | `DESCRIBE` on `raw`/`curated`/`dropbox` | Without it the persona sees an **empty catalog** — the IAM half grants the call, Lake Formation decides what it returns |
| `gm_describe_tables` (×3) | idem | `DESCRIBE`, `wildcard = true` | Tables it has to tag, **including ones that do not exist yet** — crawler-inferred tables arrive without anybody re-granting |

**No `SELECT`, and no `permissions_with_grant_option`, anywhere in this file.** `DESCRIBE` returns the
name, the schema and the location — never a row — which is what keeps this inside D31 rather than
against it; the three routes from the catalog to the rows stay closed by the persona's own IAM deny
(`DenyReadingTheRows`: `athena:*`, `lakeformation:GetDataAccess`, `s3:Get*`). The grant option is absent
because re-granting is a **delegation plane** nobody has decided; decision 5 named the persona's own
grants and no more.

**Answered 2026-08-19, one pass after it was posed** — the question of what a non-administrator must
hold in order to **grant data permissions** through an LF-Tag expression. AWS: *"You need to have `Grant
with LF-Tag expressions` permission to grant data permissions on Data Catalog resources by using the
LF-TBAC method. The data lake administrator and the LF-Tag creator implicitly receive this permission."*
So this persona, holding `ASSOCIATE` and `DESCRIBE` and no admin seat, **tags and does not grant** —
which is what decision 5 intended, now established rather than assumed. **One ambiguity survives, and it
is still Stage 6's to settle by measurement:** the same sentence extends the implicit permission to the
*LF-Tag creator*, and this persona's IAM half carries `lakeformation:CreateLFTag` — whether that makes
it a "creator" for tags it did **not** create is stated nowhere. Only a real governance-manager session
answers it (the pages, and how they were read, are in
[`docs/REFERENCES.md`](../../../docs/REFERENCES.md)).

## `shares.tf` — the cross-account shares (pass 3, step 7)

Four grants: two consumer accounts × two resource types. The principal is an **account**, resolved from
the aliased providers so no account id enters a tracked file. Production is absent by design — its share
carries the governed write and arrives with Stage 9.

| Grant | Expression | Permission | Why that shape |
|---|---|---|---|
| `share_databases` (×2) | `layer ∈ {raw, curated}` | `DESCRIBE` **+ grant option** | The container, metadata only. It may **not** carry the classification gate: `curated`'s database deliberately has no `classification`, so an expression naming it would not match — and a database that does not match cannot be resource-linked, which is the whole consumer side |
| `share_tables` (×2) | `layer ∈ {raw, curated}` **AND** `classification ∈ {public, internal}` | `SELECT`, `DESCRIBE` **+ grant option** | The rows. Two `expression` blocks in one grant is an **AND**; two separate grants would be an OR and would share the drop-box back |

**The grant option is not a style choice.** A cross-account grant lands on the *account*; nothing inside
it can use the share until that account's own data lake administrator passes it on, and an administrator
can only pass on what it received with the option — AWS states it as an imperative. Omitting it fails
mutely: the apply succeeds, the RAM share appears, the resource shows in the consumer catalog, and every
grant to a person fails afterwards. It is **not** a delegation of the share: a resource shared *with* an
account may be granted only to principals *in* that account, never onward.

**Why `layer` is in both expressions** — the drop-box database carries `classification=internal`
(fail-open, for arrivals), so a classification-only grant matched the letterbox. Nothing would have
leaked, because the drop-box bucket is unregistered and no consumer holds `s3:Get` on it, but the
metadata would have travelled. The full three-control account is in
[`docs/GOVERNANCE.md`](../../../docs/GOVERNANCE.md) §Drop-box.

**The value lists are written literally, and that is the opposite of `governance.tf` on purpose.** There
the lists are read from the tag resources so an ontology value cannot go missing; here they are a
**subset**, and a new `layer` or `classification` value joining every consumer share by inheritance is
the widening nobody decided.

**No Data Catalog resource policy is written by this slice.** The 7.1 prerequisite is conditional: the
`glue:ShareResource` statement is required of an account already sharing through an AWS Glue Data Catalog
resource policy (the version 1/2 path). Measured 2026-08-19 — `glue:GetResourcePolicy` →
`EntityNotFoundException` — and the grants then produced four **ACTIVE** RAM shares, held by both
consumers with no invitation, which is the falsifier not firing.
