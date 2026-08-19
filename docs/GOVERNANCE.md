# Data governance — the model

**The one copy of the lake's governance structure: the LF-Tag ontology, the classification rules, the
grant model, and the two designed copy destinations (drop-box in, derived zone out).** Decided by the
user on 2026-08-18 (Stage 5 decisions 1-3, recorded in
[`docs/log/log-stage-05-data-foundation.md`](log/log-stage-05-data-foundation.md)); authored here from
the user's draft, in English per the repository language rule. Two renames arrived with the decision:
the dimension the plan called `zone` is **`layer`**, and `domain` is **`businessunit`** — stage text
predating 2026-08-18 reads accordingly.

*Read with [`docs/plan/stages/stage-05-data-foundation.md`](plan/stages/stage-05-data-foundation.md)
(the build steps) and [`docs/plan/conventions.md`](plan/conventions.md) (naming). The applied grants are
registered in [`docs/AWS_STATE.md`](AWS_STATE.md) §"Lake Formation grant register".*

## Persistence — the buckets

All five live in the **Data Governance** account, encrypted SSE-KMS under the `zn-lab` CMK (see
`security-zone`), versioned, public access blocked — and **undeletable** while the `Data` OU SCP is
attached (`DenyLakeDeletionAndDeregistration`), so every name below is permanent.

| Bucket | What it holds | Who writes | Who reads |
|---|---|---|---|
| `awsds-data-dropbox` | `raw`-layer files published by users for pipeline consumption | Interactive-OU personas, `PutObject` only (§Drop-box) | the crawler (schema); the Production job, Stage 9 (read + delete) |
| `awsds-data-raw` | untreated bases — copies of legacy-system data | the governed producer path only (Stage 9's write share; nothing writes today) | consumers via LF (both layers are readable — data engineers develop the raw→curated ETL) |
| `awsds-data-curated` | transformed bases, built by ETL routines from `dropbox`+`raw` | the governed producer path only (Stage 9) | consumers via LF — the primary read surface |
| `awsds-data-artifacts` | non-tabular artifacts that must live under the lake's governance. **No writer is wired yet**: the bucket exists from Stage 5's four-bucket set; its first writer is named by the pipeline stage that needs it (8/9 — note Stage 9's *model* artifacts live in Production, not here) | — (none today) | — |
| `awsds-data-logs` | the Stage 11 CloudTrail **data-event trails**, delivered cross-account under `AWSLogs/<account>/` | CloudTrail (from Stage 11 on) | Stage 11's detection tooling |

`raw` and `curated` are **LF-registered** locations — access only through Lake Formation (D13).
`dropbox`, `artifacts` and `logs` are **not registered**: plain IAM/bucket-policy control (D13's
non-registered class).

## Catalog — AWS Glue Data Catalog

The technical catalog: a regional, per-account metadata store with the hierarchy **database → table
(schema, S3 location, format) → columns**. Everything that queries the lake — Athena, Glue, EMR — reads
schemas from it; the lake's tables are **Iceberg**, which is catalog-native (table state lives in the
catalog + metadata files, so no crawler ever points at one).

Its role in the plan: the single source of *what tabular data exists*, and the substrate every
Lake Formation permission attaches to. Databases today: `raw` and `curated`. Crawlers (under
`awsds-data-catalog-maintenance`, D27) infer schema **only where it arrives from outside** — the
drop-box and the raw zone. Stage 6 adds the *business* catalog (SageMaker Catalog/DataZone) as a storey
on top; this catalog remains the foundation.

## Lake Formation

What it provides, in the order this plan uses it:

1. **Registration** of S3 locations — turns "whoever holds `s3:GetObject` reads the files" into "the
   engine asks Lake Formation" (the mechanism behind D13);
2. **The permission layer** — grants at database/table/column grain (row filters arrive at Stage 11);
3. **LF-Tags** — the attribute system below, with inheritance and tag-based grants (LF-TBAC);
4. **Cross-account sharing** through RAM — how Sandbox and Development reach the lake at all (INT-03),
   with the version-4 parameters `DL-5` defends (INT-11).

Its role: the enforcement point. Execution roles hold **no S3 permission on registered prefixes**, so
every tabular read goes through an LF-aware engine and meets the grants — that is what makes the
fine-grained access objective a control rather than a decoration (D13).

## LF-Tags

An LF-Tag is a key-value pair used by Lake Formation to control data access by attribute. Instead of
permissioning each table or column in isolation, data is grouped and protected through these labels.

An LF-Tag is assigned to **databases, tables and columns** (the three catalog levels). Assignments
**inherit downward** — database → its tables → their columns — unless overridden at the lower level.
The Glue Data Catalog holds the objects; Lake Formation holds the tags, the inheritance and the grant
evaluation.

| Tag key | Description |
|---|---|
| `security-zone` | Divides the data into zones for **encryption-key (CMK) assignment** |
| `classification` | Information classification for **DLP** purposes |
| `layer` | Where in the data pipeline the dataset sits — its maturity degree |
| `businessunit` | The owning business unit — **reserved**, no values at N=1 |

**Assigning LF-Tags to datasets is the Governance Manager's responsibility.**

### `security-zone`

- `zn-lab` — the laboratory zone.

`security-zone=zn-lab` is the **default for every case, the drop-box included**. One zone means **one
lake CMK** — `alias/awsds-data-zn-lab` (the alias carries the value verbatim — the hyphen standard exists exactly so tag values and key aliases share one pattern) —
covering all five buckets. A second zone is a new value plus a new CMK; S3 Bucket Keys make re-keying a
bucket-level change, not a migration.

**What the single zone costs, named so it is a choice** (Stage 5 decision 3's deviation): INT-10's key
grants — the Production job role and the maintenance role need the drop-box's key — now land on the
**zone** key, so at the KMS layer those principals reach every bucket in the zone. The drop-box's
isolation therefore rests on the **S3 statements and Lake Formation alone**; the KMS layer separates
*zones*, not buckets. Revision trigger: the first dataset whose blast radius argues for its own zone.

**Scope: the dimension governs the zone wherever the zone's data lands — amended 2026-08-19, by the
user, at Stage 5 pass 4.** It used to stop at the Data Governance lake buckets, with the consumer
accounts' derived-zone CMKs declared outside it. That exception is withdrawn: a query result over a
`zn-lab` table is still `zn-lab` data (D19 practice v — classification inherits, and so does the zone),
so encryption granularity is this dimension's job in every account rather than a per-bucket decision
taken twice.

**One CMK per (zone × account), and the second half of that pair is not negotiable.** The lake's key is
`alias/awsds-data-zn-lab`; the same zone in Sandbox and Development is `alias/awsds-sandbox-zn-lab` and
`alias/awsds-dev-zn-lab`. Sharing the *lake's* key across the account line was considered and declined in
the same exchange, for a reason that is measured rather than aesthetic: `AllowProductionPickupDecryptViaS3`
on the lake key grants `kms:Decrypt` to `awsds-prod-job-exec` with **no bucket scoping** — only
`kms:ViaService=s3` and the role ARN — so a consumer's derived zone under that key would put Production's
job role over that account's materialised `restricted` copies, with S3 as the only remaining barrier.
Two further costs were named: a cross-account KMS dependency under a local working bucket, and an LF-Tag
governing a bucket no LF-Tag can be assigned to (the derived zone has no catalog object).

**D31 is unchanged and is what the per-account key still delivers**: the key policy in each consumer
account says who may read the copies — `DataScientistAccess` today, the project execution roles from
Stage 6 — and it delegates *administration* to the account root while withholding every cryptographic
action, so no IAM policy in the account can grant `Decrypt` behind it.

### `classification`

| Value | Meaning |
|---|---|
| `public` | public data — could be published without harm |
| `internal` | ordinary working data |
| `restricted` | leakage causes real damage |
| `personal` | contains identifiable-person data (LGPD scope) |

**The default-grant rule:** `public` and `internal` carry a **read-only grant for all users by
default**. Every other classification is **denied by default** — access exists only through an explicit,
enumerated grant (§Grants).

**`classification` says how sensitive a thing is; it does not say whether the thing is a thing people
read.** Those are different questions and this dimension only answers the first — which is why the
default grant carries a `layer` gate as well (§`layer`, §Grants). The drop-box is the case that proved
it: it carries `classification=internal` for the fail-open reason below, and a grant written on
`classification` alone would have shared the letterbox (found 2026-08-19, at the apply).

**Unclassified `raw` bases receive `classification=internal` by default** — mechanically, the `raw`
*database* carries the tag and new tables inherit it. This is the **fail-open** choice, made
deliberately (2026-08-18, against the fail-closed recommendation) so ETL development is not gated per
dataset; its consequence is named rather than hidden: an unclassified arrival is readable by every user
until someone reclassifies it, and the detective backstop (Macie) only arrives at Stage 11.

`curated` carries **no database default**: tables there are classified explicitly at creation. An
untagged curated table matches **no** TBAC expression and is therefore invisible to the default grants —
fail-closed by absence, the designed asymmetry between the two registered layers.

### `layer`

| Value | Meaning |
|---|---|
| `dropbox` | data supplied as unstructured user files |
| `raw` | untreated bases — legacy-system copies |
| `curated` | transformed bases, built by ETL from `dropbox`+`raw` |

`layer` states pipeline position. **It gates the default read at exactly one point, and the wording
before 2026-08-19 got this wrong:** the sentence used to read "Sandbox and Development read every layer
deliberately", which is true of `raw` and `curated` — the raw-zone deviation argued in
[`docs/plan/institutional-delta.md`](plan/institutional-delta.md) — and was never true of `dropbox`.
The drop-box is a letterbox, not a layer people read from (§Drop-box), so **the default consumer share
is gated on `layer ∈ {raw, curated}`** and `dropbox` is outside it. Which catalog database holds the
drop-box crawler's inferred tables is fixed at Stage 5 pass 1.

### `businessunit`

Reserved. No values while N=1; when the second business unit arrives (D35, Stage 14), its values join
the ontology and carry per-unit segregation — settled 2026-08-17: no separate `unit` key, and (since
2026-08-18) decoupled from encryption, which is `security-zone`'s job.

## Access control — LF-TBAC

LF-TBAC (Lake Formation Tag-Based Access Control) manages Data Lake permissions through the LF-Tags.
Instead of writing security rules per database, table or column, permissions are granted by matching
tags between the data and the principal's grant:

1. **Tag the data** — a resource receives an LF-Tag (e.g. a table gets `classification=restricted`);
2. **Tag the grant** — a principal is granted permissions over a tag *expression*
   (e.g. "may `SELECT` where `classification=restricted`");
3. **Lake Formation matches them** at query time: expression satisfied → access; otherwise denied.

TBAC is the **default method** here. Named-resource grants (per table/column) stay available for the
exceptions hybrid access mode covers (Stage 5 step 6.3) — used, they are recorded like every grant.

## Grants

**A grant is the triple `[principal, tag expression, permission list]`.**

The permission vocabulary (what the third element can contain):

| On | Permissions |
|---|---|
| tables | `SELECT`, `DESCRIBE`, `INSERT`, `DELETE`, `ALTER`, `DROP` |
| databases | `DESCRIBE`, `CREATE_TABLE`, `ALTER`, `DROP` |
| registered locations | `DATA_LOCATION_ACCESS` (create tables pointing into them) |

Any of them can carry the *grantable* option (permission to re-grant). **Corrected 2026-08-19, at the
apply that needed it: every *cross-account* grant carries it, not just Production's.** A cross-account
grant lands on the **account**; nothing inside that account can use the share until its own data lake
administrator passes it on to a local principal, and an administrator can only pass on what it received
with the option — AWS states it as an imperative (`docs/REFERENCES.md`). Without it the share applies
cleanly, appears in RAM, shows up in the consumer's catalog, and can never be granted to anybody. **It
is not a delegation of the share:** a resource shared *with* an account may be granted only to
principals *in* that account, never onward to another account or to an organization. Stage 9's
two-step (account-level grant, local regrant to the job role) is therefore the shape of **every** share
here, and what remains particular to Production is the governed *write* in its permission list.

**And the receiving account has a prerequisite of its own, which is not a grant and is easily mistaken
for a broken one** (measured 2026-08-19, both consumers at once): **an account with no data lake
administrator does not see a shared resource at all.** Its RAM holds the share, `ACTIVE`; its
`glue:GetDatabases` and `list-lf-tags` return nothing. So an empty consumer catalog has **two** possible
causes that look identical — the share never arrived, or the account is not yet a Lake Formation account
— and only the RAM side separates them. Every consumer account therefore carries its own
`aws_lakeformation_data_lake_settings`: an administrator, the `Parameters` map carried explicitly
(INT-11 — the resource replaces the whole structure), and the two `Create*DefaultPermissions` cleared
**before** its first local catalog object exists, because they act at creation time.

**The principals** (who the first element can be): the consumer **accounts** — `Sandbox Account 1` and
`Development` today, one more per business unit at N>1 (INT-03's N+2) — for the cross-account shares;
inside accounts, the persona permission-set roles; `awsds-data-catalog-maintenance` for catalog work;
from Stage 6, the project execution roles; from Stage 9, `awsds-prod-job-exec` (read + the governed
write). LF-Tags never gate the read/write direction — the **verbs** in the permission list do; the tags
say what the data *is*.

**The grain.** Entitlement follows the toolset's own practice: grants go to **roles and projects**,
assumed by people and services — the unit the whole chain (IAM, Lake Formation, SMUS projects) is built
around. **Per-user attribution is not a target of this design** (Stage 5 decision 6, 2026-08-18): where
a per-user option exists — TIP on the SQL engines, `${aws:userid}` prefix scoping in the derived zone —
it is mapped and priced at Stage 5 pass 2 as exploration, adopted only if it earns its place (TIP's
documented cost: remote access stops working). The objective's "who may read what" is met at the grain
of the assumable role/project, stated here rather than discovered.

**The map** (verification viii, written at pass 2 — three surfaces, and none of them is free):

| Surface | What it can express per *person* | What it costs | Status |
|---|---|---|---|
| **LF row/column filters** (data cells filters) | Nothing by itself. A filter attaches to a **principal**, and the principal Lake Formation sees is the role — so a filter on a role shared by four people applies to all four. It becomes per-user only when the surface below carries a user identity into the engine | — | **available, wrong grain alone**; Stage 11 narrows *within* the restricted grants using it |
| **Trusted identity propagation (TIP)** | The real lever: carries the Identity Center user into Athena, Redshift, Glue and EMR (since 2025-09), so LF sees the human and a filter becomes per-user. Enabled per project profile — `enableTrustedIdentityPropagationPermissions` | **Remote access stops working** (documented). JupyterLab and Visual ETL resolve through the project role either way, so it buys the SQL path only — a **two-grain** design, not a uniform one | **not adopted.** Stage 6 decision 2 records which yields; remote access favoured by default (open question 13) |
| **`${aws:userid}` prefix scoping** (derived zone, D19/9.2) | Real per-user separation, but of **copies**, not of source data: one person's materialised results are not a path around another's grants | An IAM condition per statement — cheap, and already the derived zone's shape | **adopted as design**, as containment rather than as entitlement |

Read together they say why the grain is the role: the only surface that makes Lake Formation see a
*person* is TIP, it reaches one of the two paths people actually use, and its price is an objective
this project holds. The derived zone's per-principal prefixes are what remains genuinely per-user, and
they govern the copy rather than the source — which is Lesson 1's shape, managed rather than forbidden.

**The default grants** — the standing expressions that implement the classification rule:

- `[each consumer account, layer ∈ {raw, curated}, DESCRIBE]` **on databases** — the container, metadata
  only;
- `[each consumer account, layer ∈ {raw, curated} AND classification ∈ {public, internal}, SELECT +
  DESCRIBE]` **on tables** — the rows, read-only, granted once per consumer;
- everything else (`restricted`, `personal`) travels **only** on explicit TBAC grants to enumerated
  principals, each recorded in the stage log **and** in the grant register.

**Why two expressions rather than the one this section used to print** (`classification ∈ {public,
internal}` alone, "both layers"), **corrected 2026-08-19 when it was first applied against a catalog
that actually carried tags:**

- **the `layer` gate keeps the drop-box out.** The drop-box database carries
  `classification=internal` — decision 1's fail-open rule for user-supplied arrivals — so the
  classification-only expression matched it, and the letterbox whose contract is *write, never read
  back* would have been shared read-only to both consumers. The rows would still not have arrived
  (the drop-box bucket is unregistered, so a query falls back to plain IAM and no consumer holds
  `s3:Get` on it), but the metadata would have, and a second control catching a first one's miss is
  not a reason to leave the first wrong. "Both layers" always meant `raw` and `curated`; the gate
  writes down what the sentence meant;
- **the database grant must *not* carry the classification gate.** `curated`'s database deliberately
  has no `classification` at all (fail-closed by absence), so an expression naming `classification`
  does not match it — and a database that does not match cannot be resource-linked, which is the whole
  consumer side. The classification gate belongs where the rows are.

The value lists in the applied grants are written **literally**, not read from the ontology: they are a
*subset*, and a new `layer` or `classification` value must not join a consumer share by inheritance.

**Every applied triple is registered in [`docs/AWS_STATE.md`](AWS_STATE.md) §"Lake Formation grant
register"** — one row per grant, written in the same sitting as the grant, the same discipline
`POLICIES.md` keeps for policy statements. It carries the catalog's own operational grants from Stage 5
pass 1; the **governance manager's** grants arrive at pass 2 and the first **consumer** grants — the
TBAC expressions above — at pass 3.

## Drop-box

The ingestion letterbox: **the only governed path for a file to enter the lake from the work accounts.**
The writer (a scientist in Sandbox/Development) may only `PutObject` into dated prefixes — no read-back,
no list, no delete. The crawler (maintenance role, D27) reads it to infer schema. The Production job
(Stage 9) reads **and deletes** — a letterbox nobody empties fills up.

Three principals, three statements, nobody holding two of the three — the asymmetry is what keeps the
drop-box from becoming a general-purpose exchange bucket (D18/D25). Own bucket `awsds-data-dropbox`,
under the `zn-lab` CMK (decision 3 — the KMS trade is §`security-zone`'s). Re-uploading a corrected
file is an ordinary overwrite (`PutObject` covers it; versioning keeps the prior copy internally); the
writer's confirmation is the API response, since read-back does not exist.

**The writer's permission is two-sided, because the write crosses the account line (2026-08-19,
Stage 5 pass 4c).** The three statements above are the *resource* half; cross-account evaluation also
requires an allow in the writer's own identity policy, so `DataScientistAccess` carries the mirror —
`PutObject` on the dated prefix, plus `GenerateDataKey`/`Decrypt` on the zone key via S3 — in
`identity/sso/`. Each half is scoped by the other: the bucket policy names the persona roles, the
permission set names the one prefix and the one key. The asymmetry is unchanged — the identity half
grants no read-back, no list, no delete.

**The catalog half of the asymmetry, written down 2026-08-19 because it was nearly lost.** The drop-box
has a catalog database and a crawler, so it has *metadata* that a grant can reach even though its bucket
holds nothing a consumer may read. Three things keep the letterbox shut on that side, and they are not
interchangeable:

| | What it does | What it does not do |
|---|---|---|
| **the `layer` gate** in the default share (§Grants) | keeps `layer=dropbox` out of every consumer grant — the control | — |
| **the unregistered location** — `awsds-data-dropbox` is deliberately **not** registered with Lake Formation | a query falls back to plain IAM, and no consumer persona holds `s3:Get` on the bucket, so no row is ever vended | it does **not** hide the metadata: table names, schema and S3 paths travel with a catalog grant |
| **`classification=internal`** on the database | states the sensitivity of user-supplied arrivals, fail-open (§`classification`) | it is **not** a statement that the drop-box may be read, and reading it as one is what produced the near-miss |

The near-miss is worth keeping: the default share was written on `classification` alone, and applied
literally it matched the drop-box database. Nothing would have leaked — the second row above holds —
but the metadata would have travelled, and a second control catching a first one's miss is not a reason
to leave the first wrong.

## Derived zone

Query results are the copy the design *manages* rather than forbids — saving results is the job
(Lesson 1). Each consumer account gets a designed destination — `awsds-<env>-derived`, applied at
Stage 5 pass 4 — with five controls:

- the Athena workgroup **forces** results there (`EnforceWorkGroupConfiguration = true` — the client
  cannot choose another destination);
- prefixes **per principal** (`…/derived/${aws:userid}/`) — one person's materialised result is not a
  path around another's grants;
- **lifecycle expiry** (30 days) — the shadow lake never silently becomes permanent;
- a **dedicated CMK** per consumer account whose key policy says who may read the copies (D31) —
  `alias/awsds-<env>-zn-lab`, the zone's key in that account (§`security-zone`);
- the prefixes are pre-declared **Macie + CloudTrail data-event scope** for Stage 11.

**Three prefix families in one bucket, and `scratch` is one of them rather than a bucket of its own**
(settled 2026-08-19, at the authoring). `results/` is the Athena workgroup's enforced output location —
per-persona, because an enforced workgroup has exactly one; `derived/${aws:userid}/` holds materialised
copies per principal; `scratch/` holds the notebook's working files. **The plan said "scratch bucket" in
three places and "scratch prefixes" in five, and the prefix reading is the origin**: D13's own sentence
is *"non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access"* — `scratch`
names the CLASS of everything Lake Formation does not govern, beside `artifacts` and `model outputs`,
and D19 (which the bucket wording credits) never mentions it at all. What makes the families real is the
`s3:PutObject` scoping on the permission set, not an S3 object, since a prefix exists only once
something is written under it.

**And one rule that is policy, not mechanism: the output of a query over `restricted` data is
`restricted`.** "Declared as policy" means: a written norm for people to follow — treat that file as
restricted, do not move it somewhere broader, do not share it — not something AWS executes. Nothing in
the system watches a query touch a restricted column and seal the output accordingly (that would be
lineage-based propagation, which does not exist as enforcement — §Data lineage). The perimeter contains
the copy either way: wherever it lands inside the organization, it cannot leave it.

## Data lineage

The AWS-native lineage feature arrives with Stage 6's domain: **SageMaker Catalog (the DataZone layer)**
provides data lineage — OpenLineage-compatible, capturing derivation events from instrumented engines
and drawing the table/column graph in the portal. Two limitations keep the rule above human:

1. **Lineage records the graph; it does not propagate classification.** It shows that a table derives
   from a restricted source — it does not tag, re-grant or deny the derivative. Auditing aid, not
   enforcement.
2. **Lineage is cooperative instrumentation, not passive observation.** Only event-emitting paths appear
   in the graph; a notebook writing a DataFrame with plain `boto3`/pandas emits nothing and is invisible
   to it.

So classification inheritance on derived data remains: the 9.4 rule (people), the derived zone's
containment (design), and Macie (detection, days later) — in that order.

---

*Stage: [stage-05-data-foundation.md](plan/stages/stage-05-data-foundation.md) · Grant register:
[AWS_STATE.md](AWS_STATE.md) · Plan core: [GENERAL_PLAN.md](GENERAL_PLAN.md)*
