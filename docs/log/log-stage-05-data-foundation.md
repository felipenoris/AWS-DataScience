# Log — Stage 5 — Data foundation

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-05-data-foundation.md`](../plan/stages/stage-05-data-foundation.md).*

*Provenance is named by SUBJECT rather than by ordinal — the convention
[Stage 3's log](log-stage-03-networking.md) adopted and Stage 4 kept. Identifiers are redacted as
`scripts/check-identifiers.py` requires — an account id becomes the account's name, an e-mail inside an
ARN becomes that user's role — with the substitutions declared once per entry.*

*File initialized 2026-08-18 on the user's request, before the stage's first act.*

---

## 2026-08-18 — The stage opened: the INT-11 before-reading, and what the same call says about the order of the first apply

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting, and it is
readings and repository edits only — **no AWS write, and nothing applied**. Every measurement below comes
from a read-only run of `./aws/datalake.py` (snapshot `2026-08-18T12:43:28Z`) or from `make status`; the
analysis around them is marked where it is analysis. Redactions per `scripts/check-identifiers.py`:
accounts are named, never numbered.*

**No AWS call in this entry changes anything.** The stage has not started building; what it has done is
take the reading that must exist *before* the first apply, while there is still nothing to overwrite.

### Stage 4 was read as closed before this file was opened

`./aws/vpn.py`: **all `VP-*` pass**, including `VP-7` in its inverted direction (the seventh set carrying
no `DenyControlPlaneOffVpn` is the *pass*, open question 17 option a). The stage file's Status row records
the 2026-08-18 close by the GuardDuty split. **Two residuals, neither blocking this stage and neither
this file's to fix:** the WireGuard host was left `running` by the MTU rebuild, and Stage 4's close-out log
entry — the user's — is still owed.

### The three-reading bracket has its first reading (step 5.4-pre, pass 0)

`DL-5`, from `awsds-infra-data`:

```
Parameters       : {"CROSS_ACCOUNT_VERSION": "4", "SET_CONTEXT": "TRUE"}
```

**This is the "before" of INT-11's bracket**, taken while `data-governance/` still holds only `bootstrap/`
— so it is a reading of a value no Terraform of ours has ever touched. It confirms for the **third** time
what `docs/AWS_STATE.md` §C recorded on 2026-08-14 and again on 2026-08-17. The remaining two readings are
owed after 5.4's apply and after the first share.

### The same call carries the finding that decides the ORDER of the first apply

The rest of section 6 is not a footnote to the line above — it is the reason step 5.2 has to happen in one
particular order, and it is measured rather than assumed:

```
DataLakeAdmins   : (none)
DB defaults      : [{"Principal": {"DataLakePrincipalIdentifier": "IAM_ALLOWED_PRINCIPALS"}, "Permissions": ["ALL"]}]
Table defaults   : [{"Principal": {"DataLakePrincipalIdentifier": "IAM_ALLOWED_PRINCIPALS"}, "Permissions": ["ALL"]}]
Registered locations: (none)
LF-Tags: (none)
```

**Lake Formation in Data Governance is not enforcing anything today, and nobody can change that yet** —
the admin list is empty. *Analysis:* the two `ALL`-to-`IAM_ALLOWED_PRINCIPALS` defaults act **at creation
time**, so clearing them after a database exists does not reach what already exists. Combined with the
`Parameters` map that `aws_lakeformation_data_lake_settings` **replaces wholesale**, the first apply of
`data-governance/data/` owes three things in one order, all in the same resource: name the admins,
carry `parameters` explicitly written from the reading above, and empty both default-permission blocks —
**before any database is created**. Getting the third one late is D13 reduced to decoration with no error
anywhere; getting the second one wrong is INT-11's silent share failure.

### The rest of the baseline, so a later reading has a "before" to differ from

| Check | Reading | Why it is a note and not a failure |
|---|---|---|
| `DL-1` | no `awsds-data-*` bucket | expected before pass 1 |
| `DL-4` | `awsds-data-catalog-maintenance` **absent** | expected before step 3 — the name is an SCP contract |
| `DL-8` | no `awsds-*` Athena workgroup in either consumer | expected before step 8 |
| `DL-11` | **Security Hub not enabled in any measured account** | expected before step 13; this is verification (ix)'s "before" |
| `DL-10` | no EFS in the VPN home | a **pass**: the withdrawn NFS requirement staying withdrawn |
| — | RAM: no share owned by Data Governance | expected before step 7 |

`0 check(s) FAILED`. **The banner reads `some calls FAILED` and it is not the verdict** — the failures are
seven profiles across six SSO sessions with no token (`awsds-ctadmin`, `awsds-deploy`, `awsds-devenv`,
`awsds-governance`, `awsds-scientist`), which is the same footprint Stage 4's entry ten named. Read the
check table, never the banner.

### Does this stage need the Sandbox environment up? — asked by the user, answered by reading

*Analysis, not a measurement.* **`make down ENV=sandbox` does not stand in this stage's way**, and the
reason is the `[P]`/`[D]`/`[E]` split doing exactly what it was built for:

- **Passes 0-3 touch Sandbox not at all.** They run in Data Governance as `awsds-infra-data`. The one
  Sandbox input they consume — the `s3_gateway_endpoint_id` output of `sandbox/foundation/` for step 1.3's
  `aws:SourceVpce` branch, plus the WireGuard Elastic IP for the `aws:SourceIp` branch — are both `[P]`,
  which `make down` never reaches. **That is INT-05's rule arriving as a consequence rather than as a
  warning:** the branch was written against gateway endpoints in `foundation/` *because* the `[E]`
  interface endpoints in `egress/` change ID on every cycle, and this is the first stage where that choice
  pays.
- **Pass 4's applies do not need the tunnel either.** `sandbox/data/` is `[P]`, applied as
  `awsds-infra-sandbox-1` — `InfrastructureAccess`, the one set deliberately left off-VPN (open question
  17, option a).
- **What does need the host back is the behavioural half**: the pandas pair, the classification pair, the
  workgroup boundary and the drop-box asymmetry are all run as **persona** sessions, and every persona set
  carries `DenyControlPlaneOffVpn`. Those need `make up ENV=sandbox` first, in the same sitting.

**One cost consequence, named now rather than met later:** `scripts/slices.py` takes `--env` and no slice
target, so `make up ENV=sandbox` also applies `egress/` and `probes/` — **~USD 0.17/h against the
~USD 0.0042/h the tunnel alone costs**. For a session that only needs the tunnel, that is a fortyfold
difference and it is worth a decision at the time, not a shrug.

### Estate state at the time of these readings

`make status`: **only `sandbox/vpn` is up** — one instance, `0.0042 USD/h`; `sandbox/egress`,
`sandbox/probes`, `development/probes`, `production/egress` and `production/probes` all down. Total
estimated burn `USD 0.0042/h`.

### Repository, in the same sitting

- This file created, in the standard header shape.
- `docs/log/INDEX.md`: the Stage 5 row pointed here; **the Stage 4 row corrected in two places** — its cell
  opened "Ten entries" while its own text went on to describe the eleventh, twelfth and thirteenth, and it
  did not say that the 2026-08-18 close has no log entry of its own yet.
- `CLAUDE.md` → Claude LOG: the Stage 5 opening bullet.
- `make check`: OK.

## 2026-08-18 — Decision 4 taken: Iceberg maintenance is Glue automatic compaction, and the Athena closure it unlocks is now owed

*Provenance: **the decision is the user's**, taken in chat before pass 1; the entry and the propagation
are Claude's, written on the user's request in the same sitting. **No AWS call** — the SCP amendment this
decision unlocks is NOT applied here; it is owed to battery phase 4b during this stage.*

- **The path**: Glue automatic compaction — the table-optimizer runs the D27 carve-out already names —
  under `awsds-data-catalog-maintenance`. Athena scheduled `OPTIMIZE`/`VACUUM` declined: it would keep a
  scheduler and a standing query path alive in the one account whose policy set says nothing runs there.
  Cost row added to the stage table: USD 0.44/DPU-h, measured (`docs/PRICING.md` §5); config free at rest.
- **The consequence, accepted with the choice (4.3)**: `athena:StartQueryExecution` loses its reason to
  stay out of `DenyUserCompute`, so the amendment is owed — through battery phase 4b, never straight to
  the OU — **sequenced late in the stage**: the amendment binds every principal in the account,
  `InfrastructureAccess` included, so if the 4.1 sample table is created or loaded through Athena in this
  account, that comes first. Until it lands, the full-lake read path stays open and stays declared.
- **Propagated, four files**: the stage file (decision row 4, steps 4.2/4.3 marked decided, the cost
  row); `POLICIES.md`'s "not covered" Athena bullet (the allowance stands in the attached document today,
  its justification withdrawn — rewritten again when the amendment lands); Stage 1c's twin bullet
  (annotated, not rewritten — it records why the absence was deliberate at attachment);
  `institutional-delta.md`'s Iceberg-operations row (the lab column now names the chosen path).
  **[Stage 11](../plan/stages/stage-11-dlp.md) needed nothing**: its `awsds-data-athena` rule was already
  written conditional on this decision's outcome, reading `POLICIES.md` for which way it went.

## 2026-08-18 — Decisions 1-3 taken: the ontology renamed and extended, and `docs/GOVERNANCE.md` created as its one copy

*Provenance: **the decisions and the governance model are the user's**, given in chat as rules plus a
drafted `GOVERNANCE.md`; Claude authored the file from that draft on request — translated to English per
the repository language rule — filled its gaps from the plan, and propagated. **No AWS call.***

- **Decision 1 — the classification scheme**: values `public / internal / restricted / personal`; owner
  the governance manager; the default grant is read-only over `classification ∈ {public, internal}`,
  everything else by explicit enumerated grant. **The `raw` database default is `internal` — fail-open,
  the user's call against the fail-closed recommendation**, so ETL development is not gated per dataset;
  the consequence is named in `GOVERNANCE.md` (an unclassified arrival is readable until reclassified;
  Macie is the Stage 11 backstop). `curated` carries no database default — an untagged table there
  matches no TBAC expression: fail-closed by absence.
- **Decision 2 — reframed by the user**: CMK granularity belongs to a new **`security-zone`** dimension,
  decoupled from business segregation. One zone, `zn-lab`, the default everywhere **including the
  drop-box** → one lake CMK, `alias/awsds-data-zn-lab`. The renames arrived with it: `zone` →
  **`layer`** (gaining a `dropbox` value), `domain` → **`businessunit`** (reserved at N=1).
- **Decision 3 — the drop-box container**: own bucket `awsds-data-dropbox`, **sharing the `zn-lab`
  CMK** — the deviation from the own-CMK recommendation follows from the one-zone model. Its cost is
  named in `GOVERNANCE.md` §`security-zone`: INT-10's key grants land on the zone key, so the KMS layer
  separates zones, not buckets — the drop-box's isolation rests on the S3 statements and LF alone.
  Revision trigger: the first dataset whose blast radius argues for its own zone.
- **Repository, in the same sitting**: `docs/GOVERNANCE.md` created — the persistence table's two gaps
  answered from the plan (`awsds-data-logs` receives Stage 11's data-event trails; `awsds-data-artifacts`
  has **no writer wired yet** — its first writer is named by Stage 8/9, and Stage 9's *model* artifacts
  live in Production, not there). `docs/AWS_STATE.md` gained the **Lake Formation grant register**,
  empty, one row per applied triple, written in the same sitting as the grant. Stage file decision rows
  1-3 marked DECIDED with pointers; step 2 and 6.1 point at the ontology's one copy; the KMS cost row
  settled at 3 CMKs (~USD 3/month). `CLAUDE.md` gained the routing row. `make check` OK.

*Amended in the same sitting, by the user: **hyphens replace underscores in every LF-Tag key and
value** — `security-zone`, `zn-lab` — so tag values and key aliases share one pattern
(`alias/awsds-data-zn-lab` now carries the value verbatim). Applied across the five files this entry
touched; the names above already read in the amended form.*

## 2026-08-18 — Decision 5 taken: the recommendation adopted whole — admins, account grants, TBAC

*Provenance: **the decision is the user's** — the recommendation accepted as stated, in chat; the entry
is Claude's on request. **No AWS call.***

- **Admins (5.3): `InfrastructureAccess` only.** The governance manager is never an admin — an approver
  who can already grant everything exercises no control (Lesson 9, D31's argument) — and receives
  **specific grants** instead (LF-Tag association, per `GOVERNANCE.md`), each row in the grant register.
  Named revision trigger: Stage 6, when the DataZone fulfilment principal joins the permission plane
  (D26).
- **Consumers (7.2): the two named accounts** — `Sandbox Account 1` and `Development`. The OU grant buys
  nothing at N=1 and is revisited at Stage 14; per-account is INT-11's fallback shape anyway, and the
  enumerated form is what the register records.
- **Method (6.1): LF-TBAC as the default**, exactly as `GOVERNANCE.md` writes it — the
  `classification ∈ {public, internal}` read-only default expression; `restricted`/`personal` only as
  enumerated TBAC grants — with **7.1's prerequisite read before the first grant** (the Data Catalog
  resource-policy additions, whose absence fails exactly like a working share that never arrives), and
  named-resource reserved for recorded hybrid-mode exceptions (6.3).

## 2026-08-18 — Decision 6 taken: the grain reframed to roles and projects — and pass 0 closes

*Provenance: **the decision is the user's**, in chat; the entry is Claude's on request. **No AWS
call.***

- **The user's framing, kept close to verbatim:** traditionally access is granted to **roles**, assumed
  by users and services, the way IAM works; this project holds **no strong restriction on per-user
  attribution**; the aim is to **experiment with what the tools allow** (Lake Formation + SageMaker +
  S3 + the rest) — understanding the AWS good practice matters more than hitting a per-user target.
- **What it settles:** the objective's grain is the **assumable role/project** — the outcome 6.4
  pre-contemplated, now chosen rather than discovered, which closes the stage risk row's failure mode
  (an objective invalidated by discovery). Stated in `docs/GOVERNANCE.md` §"The grain".
- **What survives into pass 2:** verification (viii) becomes a **mapping** — which per-user expressions
  exist (SQL-path LF filters; TIP, priced against its documented remote-access cost, open question 13;
  9.2's `${aws:userid}` `GetObject` scoping) and what each costs. The written map is the deliverable;
  the per-user `GetObject` scoping moves from conditional obligation to mapped option; step 8's `min()`
  ceiling stays as recorded fact.
- **Pass 0 closes with this entry — all six decisions taken, all on 2026-08-18.** Propagated: decision
  row 6 and step 6.4 marked; `GOVERNANCE.md` gained §"The grain"; open question 13's Stage 5 half
  answered in place, its Stage 6 half (TIP versus remote access) now weighed against a mapped option
  with remote access favoured by default.

## 2026-08-18 — Pass 1 authored: `data-governance/data/`, `58 to add` — and the one obligation the plan cannot state

*Provenance: **this entry is Claude's**, written on the user's request. **NOTHING IS APPLIED** — the
work is repository authoring plus read-only Terraform (`init`, `validate`, `fmt`, `plan`, `console`,
`providers schema`) against the Data Governance account as `awsds-infra-data`. The plan file was written
to the session scratchpad, never into the repository (it carries account ids).*

### What was authored

`terraform-live/data-governance/data/` — eleven files, the slice registered in the D11 machinery in the
same authoring (`./scripts/slices.py check`: **18 declared, 18 on disk**). `plan`: **58 to add, 0 to
change, 0 to destroy** — one CMK + alias, five buckets with their six per-bucket resources, the LF
settings, two registrations, three LF-Tags, three databases, five tag assignments, the sample Iceberg
table, its optimizer, two IAM roles with their policies, four LF permissions, two crawlers.

Two things the plan proves incidentally, both firsts: **the cross-account remote-state reads resolved** —
each consumer's `foundation/` for its `[P]` S3 gateway-endpoint id (INT-05's anchor, never the `[E]`
interface endpoints) and the VPN home's for the Elastic IP — and the **data lake administrator resolved
by pattern**, `one()` over the `AWSReservedSSO_InfrastructureAccess_*` roles, so the per-account suffix
is never written down.

### The finding, and it changed how the stage is applied

**The 5.2 obligation — empty both `IAM_ALLOWED_PRINCIPALS` default blocks before any database exists —
cannot be stated in the plan at all**, measured in the pinned provider (`aws ~> 6.60`) rather than
assumed:

| What was tried | What came back |
|---|---|
| omitting both blocks | `after_unknown: true` for each — **Terraform states no intention about them** |
| `create_database_default_permissions = []` | refused: *"An argument named … is not expected here. Did you mean to define a block?"* |
| a `{}` block | would declare **one** entry with computed fields, which is not zero |
| the provider schema | both are `nesting_mode: list` **blocks**, `max_items: 3` — *and that is all it says*. **Amended in the eighth entry**, where it was checked: the JSON schema marks `computed` on attributes and **never on `block_types`**, so "the provider decides this" is carried by the `after_unknown` reading above, not by the schema |

So omission is the only expressible form, and whether it **clears** or merely **leaves alone** is a
provider property the plan does not state. The consequence is the expensive, silent one: a database
created while the defaults still stand is born deferring to IAM — D13 as decoration — and clearing them
afterwards does not reach it.

**The apply therefore became two steps** (written into the stage file's 5.2 as a callout, into the
slice's `README.md`, and beside the resource in `lakeformation.tf`): apply
`aws_lakeformation_data_lake_settings` **alone** with `-target`; read `./aws/datalake.py` (`DL-5`
parameters, `DL-6` defaults); revoke and re-read if `IAM_ALLOWED_PRINCIPALS` is still named; only then
apply the rest, which is where the first database is created. The graph orders the two correctly —
every database `depends_on` the settings — but a graph cannot pause to be read (Lesson 13).

### One module change, so the two-commit order applies

`terraform-modules/s3-bucket`'s `additional_policy_statements` was `list(any)`, which **cannot hold this
stage's statements**: `list(any)` unifies to a single element type, and a Deny carrying three condition
operators does not unify with an Allow carrying one (`validate` refused the conditional that mixed
them). Changed to `any` — the module only `concat()`s and `jsonencode()`s them — and the caller pins
**`s3-bucket-v0.2.0`**. Per the terraform-changes runbook §3 this is Recipe B: **the module commit and
its pushed tag must land before the caller's commit**, or the commit hook's `init` fails on `invalid
ref`. The tag does not exist yet; the plan above was produced against a temporary local module path,
which was reverted to the pinned ref before `make check` (OK).

### Decisions rendered, so the code and `GOVERNANCE.md` can be read against each other

The ontology is the file's rendering, value for value: `classification` (4 values), `layer`
(`dropbox`/`raw`/`curated`), `security-zone` (`zn-lab`); `businessunit` is **absent on purpose** — an
LF-Tag needs at least one value and the dimension has none at N=1. Decision 1's asymmetry is in the tag
assignments: `raw` and `dropbox` databases carry `classification=internal` (fail-open, the user's call),
`curated` carries **none** — an untagged table there matches no TBAC expression, fail-closed by absence.
One thing `GOVERNANCE.md` left open was fixed here as pass 1 said it would be: the drop-box crawler
writes into **its own `dropbox` database**, so inferred tables inherit `layer=dropbox` instead of
wearing raw's value wrongly.

Two shapes worth naming because they are not obvious: **a bucket policy validates its `Principal`**, so
statements for roles that do not exist yet (`awsds-prod-job-exec` — Stage 9's contract — and the Stage 6
project execution roles) name the **account root** as Principal and narrow with an `ArnLike` condition;
and the perimeter deny's third branch is `aws:PrincipalAccount` = this account rather than the
maintenance role alone — the stage's own "looser and easier to get right" option, taken deliberately,
because a role-only branch would lock out both the crawler (no VPC, no tunnel) and the infrastructure
user working off-VPN by decision (open question 17).

### Not done

- **Nothing is applied.** The two-step apply, both readings, and the SCP amendment of 4.3 are all still owed.
- **`checkov` and `tflint` were not run** over the new slice — they run in the commit hooks, which cannot
  pass until the module tag is pushed.
- The plan could not render the bucket policies (`known after apply` — the module's TLS statement uses
  the bucket's own computed ARN), so **the perimeter conditions were read structurally, not by value**.

## 2026-08-18 — Pass 1 APPLIED: the lake exists, and the two-step apply earned its keep

*Provenance: **Claude's**, on the user's explicit authorisation of the commit procedure and the apply.
Applied as the **infrastructure user**, account **Data Governance**, permission set
**`InfrastructureAccess`**, profile `awsds-infra-data`. Every plan was written to the session scratchpad
and applied from the saved file (Recipe A step 6). Redactions as this file's header states.*

### The commit procedure ran first, and the tag order is not ceremony

Recipe B, in order: commit 1 the module alone (`s3-bucket` `list(any)` → `any`), tag **`s3-bucket-v0.2.0`**,
push branch and tags, and **ask origin for the tag** — `9dd35db…  refs/tags/s3-bucket-v0.2.0`, the same
hash as the local tag. Then commit 2, the callers. **The order proved itself twice**: commit 1 was
blocked by `checkov` (below), and commit 2 was blocked by `terraform_validate` with **`Module source has
changed`** — the working `.terraform/` still recorded the temporary local path used for the authoring
plan. A re-init pulled the module from the pushed tag and the commit passed. That is the runbook's
`invalid ref` hazard arriving in its other form: not a missing tag, but a stale local install.

### Two gate findings, and one of them is a real control the stage text did not have

- **`CKV_TF_1`** (module pinned by tag, not commit hash) — the repository's established answer: a
  `checkov:skip` naming the convention, added to all four module calls.
- **`CKV_AWS_195`: the crawlers had no Glue security configuration** — and this one is not a default
  worth skipping. D27's own honest sentence is that a crawler **samples object contents** to infer
  schema, so what it writes to CloudWatch is closer to data than to metadata, and everything else here
  encrypts under the zone CMK. So `awsds-data-catalog-maintenance` (a security configuration of the
  same name) was added and attached to both crawlers, with a fourth statement on the zn-lab key policy
  for `logs.us-west-2.amazonaws.com`, scoped by the log-group encryption context. **A second gate
  finding corrected the first fix**: the draft declared `s3_encryption` and `job_bookmarks_encryption`
  `DISABLED` (a crawler writes neither), and `CKV_AWS_99` refused it — rightly, because a configuration
  naming the key for one mode and "off" for two is a statement about what happens to exist rather than
  about this lake. All three modes now name the key.

### The apply, in the two steps the plan could not state

| Step | What | Result |
|---|---|---|
| 1 | `aws_lakeformation_data_lake_settings` **alone**, `-target` | `1 added` |
| — | **the reading** — `get-data-lake-settings` | see below |
| 2 | the remainder | `56 added`, then failed on the crawlers |
| 3 | the crawler fix | `2 added, 1 changed` |
| — | re-plan | **`No changes`, `-detailed-exitcode 0`** |

**And the reading between steps 1 and 2 is the whole reason the split existed — it came back the good
way, which is a measurement and not a relief:**

```
Parameters    : {"CROSS_ACCOUNT_VERSION": "4", "SET_CONTEXT": "TRUE"}
Admins        : [ ...AWSReservedSSO_InfrastructureAccess_... ]
DbDefaults    : []
TableDefaults : []
```

**Omission clears.** The provider sends the empty structure and `PutDataLakeSettings` replaces
server-side — so the behaviour the plan refused to state is now measured for this provider version. Two
things follow: the split can, in principle, collapse back to one apply at pass 2 and beyond — and it
**should not**, because what was measured is a provider behaviour that the plan still does not state,
so the next version could change it silently. The read-back stays (`DL-6`), which is the cheap half.

**The claim that actually matters was then verified per database**, not inferred from the settings:
`list-permissions` on `raw`, `curated` and `dropbox` returns **no `IAMAllowedPrincipals` grant at all** —
only the maintenance role's operational grants and `InfrastructureAccess` as creator. The databases were
born governed. Had the order been one apply, this reading would have been the discovery that D13 was
decoration, days later and with the tables already created.

### The one failure, and it was caused by the fix rather than by the design

`CreateCrawler` returned `InvalidInputException: The role … is not authorized to perform
glue:GetSecurityConfiguration` — **a role must be able to READ the security configuration it runs
under**, which nothing in the stage text or the checkov guidance says. Added as its own statement
(`Resource: "*"` — Glue security configurations have no ARN to scope to). Both crawlers created on the
retry. Worth keeping in mind as a shape: adding an encryption control added an IAM requirement to a
principal that was already written, and the error named the missing action rather than the control.

### What exists now

Five buckets under one CMK (`alias/awsds-data-zn-lab`), each versioned, SSE-KMS, Bucket Key on, carrying
the three-branch perimeter deny plus the signature-age cap — `DL-1` and `DL-2` pass on all five. `raw`
and `curated` registered through `awsds-data-lf-registration`; the three LF-Tag keys with
`GOVERNANCE.md`'s values; three databases with decision 1's asymmetry applied (`raw` and `dropbox`
tagged `classification=internal`, `curated` deliberately untagged at the database); the Iceberg table
`curated.sample_trades` with its `restricted` column and its compaction optimizer;
`awsds-data-catalog-maintenance` trusting `glue.amazonaws.com` alone, with two **unscheduled** crawlers.
`./aws/datalake.py`: **`DL-1` through `DL-6` and `DL-10` all pass**; `DL-7`, `DL-8` and `DL-11` are the
expected pre-pass notes.

### Not done

- **Passes 2, 3, 4 and 6 are untouched**, and so is 4.3's SCP amendment (battery phase 4b).
- **Nothing behavioural was proven.** Every claim above is a describe call or a policy read; the pandas
  pair, the classification pair, the drop-box asymmetry and the crawler pair are the stage's own probes
  and need the tunnel and the consumer side.
- **The crawlers have never run.** `DL-3` reads their shape, not a run — verification (iii)'s positive
  half (the SCP carve-out actually matching) is still owed, and it is the first thing that will exercise
  the security configuration added here.

## 2026-08-18 — Pass 1 merged and synchronised, and what the session was worth keeping

*Provenance: **the merge is the user's** (PR #18). The synchronisation, the post-merge reading and the
documentation work are Claude's, on the user's request in the same sitting. **No AWS write** — the one
AWS call is a `plan`, which is read-only, run as the **infrastructure user**, account **Data
Governance**, permission set **`InfrastructureAccess`** (`awsds-infra-data`). The plan file was written
to the session scratchpad, never into the repository.*

### The synchronisation, and the one reading that makes it more than bookkeeping

`main` at `96639df`; the merged branch deleted locally and two stale remote branches pruned;
`s3-bucket-v0.2.0` re-confirmed on origin at `9dd35db…`, the hash it was pushed with.

Then the check that a fast-forward alone does not give: **`terraform plan` on
`data-governance/data/` from the merged `main` returns `No changes`.** The merge preserved what was
applied — worth one command, because the branch that was applied and the branch that was merged are
only the same object until somebody rebases or squashes one of them.

### A lesson: 27, the plan's silence

**Added to [`docs/plan/lessons.md`](../plan/lessons.md)**, and it is pass 1's finding generalised rather
than restated: *a declarative plan is silent about the values the provider owns — so the setting that
has to be right before anything else exists is precisely the one Terraform will not promise.* What
earns it a place is the shape rather than the incident: the plan **renders identically** whether the
apply will clear the defaults or leave them standing, which is Lesson 13's failure moved out of the
verification and into the artifact that *authorises* the apply. It carries the recognisable class —
the account-level settings singletons, which create nothing and overwrite state AWS initialised
(`aws_s3_account_public_access_block`, `aws_ebs_encryption_by_default`, anything `*_default_*`) — and
the warning against relief: omission clearing is a fact about one provider version, so the read-back
stays.

**Writing it corrected the discriminator.** The natural instrument is the provider schema, and it does
not work: `terraform providers schema -json` marks `computed` on **attributes and never on
`block_types`**, checked here against the pinned provider — so for a block it reports `nesting_mode`
and `max_items` and nothing about who decides the value. The instrument is the plan:
`terraform show -json … | jq '… .change.after_unknown'`, and it is meaningful only on a create-or-update
plan (a `no-op` returns `{}`, everything being known from state — also verified here, against the
post-merge plan above). **This is the second time in this stage that the obvious place to look did not
hold the answer**, and both times the plan JSON did.

### The runbook gained the recipe this stage invented

[`terraform-changes.md`](../plan/runbooks/terraform-changes.md), four changes:

- **A new Recipe D — the staged apply**, `-target` as a *measurement* rather than a shortcut: the two
  preconditions, the `after_unknown` check, and five steps of which step 1 is "write down what reading
  would make you stop" and step 4 is acting on it. It states what the recipe is **not** — never a way
  around a dependency the graph should express, since `depends_on` already orders the halves; what it
  buys is **a pause the graph cannot give you**.
- **§8's prohibition reworded rather than contradicted.** It read "never `-target`", which this stage
  deliberately did; it now forbids `-target` *as a convenience* and names Recipe D as its only
  sanctioned use, so the two pages stop disagreeing.
- **Recipe B gained the step that plants the landmine**: how to plan a caller against a module version
  whose tag does not exist yet (point `source` at the local path), and that the revert is **two halves**
  — revert *and* re-init, because only the second touches `.terraform/modules`. The blocked-commit table
  gained the matching row, distinct from the one already there: same message, different cause.
- **The `checkov` row strengthened** from "fix it or suppress it" to what pass 1 actually cost: an
  accepted finding can pull in whole resources the stage text never had, each with its own requirements
  — `CKV_AWS_195` cost a security configuration, a key-policy statement **and** a
  `glue:GetSecurityConfiguration` that surfaced only at apply. **An accepted gate finding re-enters the
  recipe.**

Section numbers 5-7 shifted to 6-8 by the insertion; internal references updated. Per `CLAUDE.md` the
`§` numbers are historical anchors, so the stable references are the recipe letters.

### Two findings deliberately NOT promoted, and the criterion

The lessons file admits only what would otherwise be relearned the hard way, so applying it means saying
no twice here:

- **`glue:GetSecurityConfiguration`** — a role must read the security configuration it runs under. Real,
  and it cost an apply failure, but the error **names the missing action**; it is self-announcing and
  costs one retry. It lives in the runbook's checkov row, where somebody about to accept a gate finding
  will meet it.
- **A bucket policy validates its `Principal`**, so a statement for a role a later stage will create
  names the account root and narrows with `ArnLike`. This was **anticipated in authoring, not learned by
  failing** — it was written that way the first time. Recorded in pass 1's entry; not a lesson.

### Not done

- **The stage itself did not advance.** Passes 2, 3, 4 and 6 are untouched, 4.3's SCP amendment is still
  owed via battery phase 4b, and **the crawlers still have never run** — nothing behavioural is proven
  that was not proven before this entry.
- Stage 4's two residuals are unchanged and are not this stage's: the host left `running`, and the
  close-out log entry, which is the user's.

## 2026-08-19 — Pass 2 authored: the governance manager's own grants, `9 to add` — and the reading that found a persona holding nothing

*Provenance: **this entry is Claude's**, written on the user's request. **NOTHING IS APPLIED.** The AWS
calls are all reads — `iam list-roles`, `terraform plan`, `providers schema` — as the **infrastructure
user**, account **Data Governance**, permission set **`InfrastructureAccess`** (`awsds-infra-data`). Plan
files were written to the session scratchpad, never into the repository. Redactions as this file's header
states; the SSO role suffix is truncated wherever it appears.*

### What was authored

`governance.tf` — the first grants this project makes to a **human persona**, and the delivery of
decision 5's second half ("the governance manager is never an admin … and receives specific grants
instead"). `plan`: **9 to add, 0 to change, 0 to destroy** — nothing of pass 1 is touched.

| Grant | Permission | Why |
|---|---|---|
| the three LF-Tag keys | `ASSOCIATE` | assigning tags to datasets — the job `GOVERNANCE.md` gives the persona. Values read **from the tag resources**, so an ontology value cannot go missing here (Lesson 14) |
| the three databases | `DESCRIBE` | without it the persona sees an **empty catalog** |
| their tables, `wildcard` | `DESCRIBE` | covers the tables the crawlers have not inferred yet |

**No `SELECT` and no grant option anywhere in the file.** The set implements the permission set's own
one-line description, written back in Stage 2 and unread since: *"The catalog, never the rows."* The
principal is resolved **by pattern** like the admin before it, and the role was confirmed to exist first
(`AWSReservedSSO_GovernanceManagerAccess_…` is provisioned in this account by `identity/sso/`'s
`governance-manager@data-governance` assignment — the only account that assignment names).

### 6.2's reading, and it comes back in the strongest form the question has

The step asks whether any of the six persona sets carries an S3 grant reaching this account's buckets.
**Every single `s3:` mention across the four policy files is inside a `Deny`** — there is no `s3:Get*`
**Allow** anywhere in the six sets, not scoped, not wildcarded, not on another account's buckets. The
four are `DenyTerraformStateAccess` (`s3:*` on `awsds-*-tfstate` — the wildcard read in the closing
direction), `DenyMakingStorageOrImagesPublic`, the scientists' `DenyEveryWrite`, and the approvers'
`DenyReadingTheRows` (`s3:Get*` whole).

*Analysis:* **D13's premise therefore holds by absence rather than by exclusion.** 6.1's "no S3
permission of any kind on Data Governance buckets" needed no carve-out written anywhere, because there
was never a grant to carve out of — which is what D22's account split bought and what the old
same-account layout would have made a per-prefix exclusion problem. The drop-box `PutObject` exception
6.1 names is granted by **bucket policy** to the Interactive-OU roles, so its absence from the permission
sets is correct rather than missing.

### The finding, and it is a persona that held nothing while a file said otherwise

Writing the grants surfaced what the reading above cannot show on its own: **the IAM half already existed
and grants the persona nothing.** `policies-approvers.tf` carries `AdministerLakeFormation` —
`AddLFTagsToResource`, `GrantPermissions`, `CreateLFTag` — which reads like the whole answer. Lake
Formation authorizes **separately**: the IAM action permits the API *call*, an LF permission (`ASSOCIATE`)
decides whether it *succeeds*. The two halves sit in different accounts, different slices and different
stages, and the unit anyone opens is a slice.

What makes it expensive is the failure shape: before this pass the persona could not tag a single
dataset, and with Lake Formation enforcing, a missing grant makes `glue:GetDatabases` return an **empty
list** rather than an error — so the wrong conclusion is drawn from a file that is accurate, and the
symptom is an absence. The reverse direction has no symptom at all: revoke the LF grant and the IAM
policy still describes the capability.

**Promoted to [Lesson 28](../plan/lessons.md)**, with the mitigation shipped beside it rather than left
to memory: a comment at **each** end pointing at the other — in `policies-approvers.tf` beside the
statement, and in the slice README's §"A permission here is the intersection of two systems".

### Verification (viii) answered as a map, per decision 6

The grain question stops being an objective and becomes the written map decision 6 asked for, now in
`docs/GOVERNANCE.md` §"The grain": **LF row/column filters** attach to a *role*, so per-user is not
theirs to give; **TIP** is the only surface that makes Lake Formation see a person, reaches the SQL path
and not JupyterLab, and costs remote access — reachable, **not adopted**; **`${aws:userid}` prefixes**
are genuinely per-user but govern *copies*. Read together they are why the grain is the role.
*Expressed* is answered; *observed* is not claimed — nothing was run.

### What was NOT established, and is deliberately unasserted

**What a non-administrator must hold in order to *grant* data permissions through an LF-Tag expression.**
`ASSOCIATE`'s own semantics were confirmed (it permits assigning the tag to a catalog resource and
implicitly grants `DESCRIBE`), but the complementary question was not: the Lake Formation pages are
JavaScript-rendered and **returned no body to an automated fetch** — the first attempt answered from the
model's own memory while admitting it had seen no content, and was discarded. What is recorded came from
AWS's indexed text via search, and `docs/REFERENCES.md` carries that provenance explicitly so the row
cannot be leaned on further than it earns.

It is **Stage 6's to settle by measurement**, with a real governance-manager session, when the persona
first has to grant rather than tag — decision 5's named revision trigger arriving on schedule. *Analysis,
worth stating before it is met:* if granting does require holding the permission with the grant option,
then the separation D31 asks for cannot live in Lake Formation and lives in the **IAM** deny
(`DenyReadingTheRows`) instead — the approver would hold `SELECT` in the permission layer and still have
no path to a row.

### Repository, in the same sitting

- **The slice README rewritten into an index of controls**, in `POLICIES.md`'s discipline and at the
  user's direction: one row per `Sid`, per tag assignment, per grant — the LF settings and ontology, the
  four key-policy statements, the perimeter's two `Sid`s with their three branches and two carve-outs, the
  drop-box's four, both service roles, and pass 2's grants. It says what the **code** declares;
  `docs/AWS_STATE.md` keeps what is **deployed**, and the file names that split so a second staler answer
  cannot grow.
- `docs/REFERENCES.md`: the LF-Tag permissions row, with the provenance caveat above.
- The stage file: 6.2 answered inline, verification (viii) answered, the pass table annotated.
- `GOVERNANCE.md`: §"The grain" gained the map; §Grants' "empty until pass 2" line corrected — pass 1's
  operational rows had already landed.
- `make check`: OK.

### Not done

- **Nothing is applied**, and the grant register in `docs/AWS_STATE.md` is therefore **unchanged** — its
  rows are written in the same sitting as the grant, not in the sitting that authors it.
- **No behavioural proof.** Whether the persona can in fact tag a dataset is a claim about the pair, and
  measuring it needs a governance-manager session — which carries `DenyControlPlaneOffVpn`, so it needs
  the tunnel up. It joins the stage's other owed proofs rather than forming a new class.
- Pass 3, 4 and 6 untouched; 4.3's SCP amendment still owed via battery phase 4b; **the crawlers still
  have never run**.

## 2026-08-19 — Pass 2 APPLIED: the persona now holds something, and the register says what

*Provenance: **Claude's**, on the user's explicit authorisation to proceed. **The commit is the
user's** — `6440c6a "stage 5 review"`, made on `main` before this apply, so there was nothing for Claude
to commit and the branch it had opened was deleted unused. Applied as the **infrastructure user**,
account **Data Governance**, permission set **`InfrastructureAccess`** (`awsds-infra-data`), from a plan
read and then applied from the saved file (Recipe A steps 5-6). Redactions as this file's header states.*

### The apply

| Step | Result |
|---|---|
| `apply` the read plan | **9 added, 0 changed, 0 destroyed** |
| re-plan | **`No changes`**, `-detailed-exitcode 0` |
| `./aws/datalake.py` | **`0 check(s) FAILED`** |

A second `apply` of the same file was refused — *"Saved plan is stale"* — which is the runbook's own
guard working rather than a problem: the first apply had moved the state serial, so the plan could not
be replayed.

**`DL-5` re-read after this apply and the bracket holds**: `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE`.
That is not ceremony — this pass applied into the *same slice* that owns
`aws_lakeformation_data_lake_settings`, and INT-11's failure mode is precisely a parameter reset that
nothing reports. `DL-6` still reads no `IAMAllowedPrincipals` default.

### The claim verified against the API, not against the code

`list-permissions`, filtered on the governance-manager principal, returns **exactly nine rows and
nothing else**:

```
DESCRIBE  | grant_option=NONE | Database  curated / raw / dropbox
DESCRIBE  | grant_option=NONE | Table     ALL_TABLES (TableWildcard) in each of the three
ASSOCIATE | grant_option=NONE | LFTag     classification(4) / layer(3) / security-zone(1)
```

Two things are established by that listing rather than asserted from the source: **`grant_option` is
`NONE` on every one of the nine**, and the persona holds **no `SELECT` anywhere** — established by
exhaustion, since the filter returns the principal's complete set. The permission set's own one-line
description from Stage 2 — *"The catalog, never the rows"* — is now true of the Lake Formation half as
well as the IAM half.

### Records, in the same sitting

The **grant register** in `docs/AWS_STATE.md` gained three rows covering **nine triples** (three
resources each), with the no-`SELECT`/no-grant-option finding stated as *verified against the API*. The
register's note was corrected while there: it said the first consumer grants arrive at pass 2, and they
arrive at **pass 3**, with the shares they ride on.

### Not done — and one of these is the point

- **Nothing behavioural is proven, and it cannot be from here.** Whether the persona can in fact tag a
  dataset is a claim about the *pair* (Lesson 28), and only a governance-manager session answers it. The
  instrument run in this same sitting shows why the gap is structural rather than an oversight:
  `awsds-governance-data` is one of the seven profiles reading `FAILED` for want of an SSO token, and the
  set carries `DenyControlPlaneOffVpn` — so the proof needs the tunnel up **and** a sign-in as that
  persona. It joins the stage's owed proofs.
- **Passes 3, 4 and 6 untouched**; 4.3's SCP amendment still owed via battery phase 4b; **the crawlers
  still have never run**.

## 2026-08-19 — Pass 3 APPLIED: the lake is shared, and two things about the decided form were wrong

*Provenance: **Claude's**, on the user's explicit authorisation to apply and to revise the project's
artifacts against this session's findings. Applied as the **infrastructure user**, account **Data
Governance**, permission set **`InfrastructureAccess`** (`awsds-infra-data`), from a plan read and then
applied from the saved file (Recipe A steps 5-6). Redactions as this file's header states.*

### The sitting opened by closing the previous one

**PR #19 — pass 2's records — is the user's merge**, and the local repository was synchronised onto it:
`main` fast-forwarded `6440c6a` → `7814c75`, the merged branch deleted. Unlike PR #18 (entry eight)
this one carried **no `.tf` file**, only records, so no post-merge re-plan was owed and none was run —
the deployed state and `main` had not been able to diverge.

### The method changed first, and that is why the rest of the entry exists

The previous entry recorded that AWS's Lake Formation pages "did not return a body to an automated
fetch" and deferred a question because of it. **They read normally through a browser that renders
JavaScript.** The limit was the fetcher's, not the pages'. Everything below comes from reading the
rendered pages, and two things fell out immediately:

- **the question pass 2 deliberately left unasserted is answered**, and in the design's favour: *"You
  need to have `Grant with LF-Tag expressions` permission to grant data permissions… The data lake
  administrator and the LF-Tag creator implicitly receive this permission."* The governance manager,
  holding `ASSOCIATE` and `DESCRIBE` and no admin seat, **tags and does not grant** — decision 5's
  intent, now established. **One ambiguity survives and stays Stage 6's:** the same sentence extends the
  implicit permission to the *LF-Tag creator*, and the persona's IAM half carries `CreateLFTag`;
- **the 7.1 prerequisite is conditional.** The considerations page states flatly that cross-account
  LF-TBAC "requires additions to the Data Catalog resource policy"; the Prerequisites page scopes it to
  an account **already** sharing through a Glue resource policy. Measured here: `glue:GetResourcePolicy`
  → `EntityNotFoundException`. No policy written, nothing set to `EnableHybrid`.

This became **Lesson 30** — a tool's failure recorded as a property of the world.

### The two corrections to the decided form, both found before applying

| What `GOVERNANCE.md` said | What it had to become | Why |
|---|---|---|
| the grant option is "used only on the cross-account share to Production" | **every** cross-account grant carries it | the share lands on the *account*; its own data lake administrator must pass it on, and can only pass on what it received with the option. AWS states it as an imperative. Omitting it fails **mutely and late** — the apply succeeds, RAM shows the share, and every later grant to a person fails in another account |
| the default expression is `classification ∈ {public, internal}` alone, "both layers" | a `layer` gate on **both** grants | applied against the catalog *as tagged*, the classification-only form matched the **drop-box** database, which carries `classification=internal` for decision 1's fail-open reason. The letterbox whose contract is *write, never read back* would have been shared read-only to both consumers |

No row would have travelled from that near-miss — the drop-box bucket is unregistered, so a query falls
back to plain IAM and no consumer holds `s3:Get` on it — but the **metadata** would have, and a second
control catching a first one's miss is not a reason to leave the first wrong. It became **Lesson 29**.

The applied form is deliberately two different expressions: `DESCRIBE` on databases matching
`layer ∈ {raw, curated}`, and `SELECT`+`DESCRIBE` on tables matching that **AND**
`classification ∈ {public, internal}`. The database grant may not carry the classification gate, because
`curated`'s database has none by design and a database that does not match cannot be resource-linked.

### The apply

| Step | Result |
|---|---|
| `plan` | **4 to add, 0 to change, 0 to destroy** — the settings resource a no-op, which is the INT-11 guard |
| `apply` the saved plan | **4 added** |
| re-plan | **`No changes`**, `-detailed-exitcode 0` |
| `list-permissions` | four rows, both accounts, **grant option on every one**, the `AND` present on the table rows — verified against the API, not the code |
| `./aws/datalake.py` | **`0 check(s) FAILED`** |

### The three readings of 7.3, and the third one changed the instrument

- **the parameters bracket holds**: `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE` after the shares exist
  — the third of the three readings verification (i) asks for, so **(i) is answered**;
- **the shares travelled**: four `LakeFormation-V4-*` shares owned here, all `ACTIVE`, each consumer's
  own RAM holding its two, **zero invitations anywhere**. INT-11's fallback tax is not being paid, and
  the row is closed. This is also the falsifier for the conditional reading above **not** firing;
- **the consumer catalogs are empty, and that is correct.** `glue:GetDatabases` and `list-lf-tags` return
  nothing in either account because **neither has a data lake administrator** (`DataLakeAdmins: []`), and
  AWS requires one before a shared resource is visible there at all.

**1d step 11.4's two owed items resolved without adding anything**, which is worth saying because both
were on this step's list: the grantor needs `AWSLakeFormationCrossAccountManager`, and it is
`InfrastructureAccess` — i.e. `AdministratorAccess` — so the managed policy is a strict subset of what
the principal already holds and attaching it would be decoration; and `ram:AcceptResourceShareInvitation`
on the consumer roles was the *only-if-the-org-path-fails* half, and there was no invitation to accept.

That last reading exposed a defect in this stage's own instrument: **`DL-7` reported one verdict for two
opposite causes** — "step 8 has not run" and "the share never arrived" — which is Lesson 13's family.
The discriminator is now measured: `./aws/datalake.py` reads each consumer's **held** shares and its
**data lake admin count**, and `DL-7` reports the branches separately. It currently reads a *note*: the
share travelled, no link yet, admins `[dev:0, sandbox-1:0]` — the expected state between passes 3 and 4.

### What that means for pass 4, written down before it is forgotten

Step 8 now opens with a prerequisite it did not have: **each consumer account needs its own
`DataLakeSettings`**, carrying both hazards the producer side already met — `Parameters` replaced
wholesale (INT-11), and `Create*DefaultPermissions` cleared **before** the first local database, which
there is the first resource link (Lesson 27, Recipe D).

### Records

**Code:** `shares.tf` (new — the four grants and the reasoning beside them) and `locals.tf`
(`consumer_accounts`, resolved from the aliased providers so no account id enters a tracked file);
`aws/datalake.py` (the consumer-side receipt read, and `DL-7` split into its two branches).

**Records:** `GOVERNANCE.md` (§Grants' default expressions and the grant-option rule, §`classification`,
§`layer`'s wrong sentence, §Drop-box's new three-control table), the stage file (7.1, 7.2, 7.3, step 8,
verifications i / ii / v, and 6.1's decided form marked superseded), `AWS_STATE.md` (the register at
**nine rows / 17 triples**, §C's Lake Formation row), `integrations.md` (INT-03 applied, INT-11 closed),
`REFERENCES.md` (the rendered pages and the superseded provenance note), the slice `README.md` (a
`shares.tf` section), `lessons.md` (**29** and **30**), `open-questions.md` (**item 18** — the LF-Tag
creator ambiguity, with its settling mechanism), `CLAUDE.md` and this file's `INDEX.md`.

**Not committed by Claude.** The working tree also carries the user's own uncommitted edits to
[Stage 6's file](../plan/stages/stage-06-unified-studio.md) — the two 2026-08-19 decisions about the
permissions boundary and about not pulling the Athena Spark amendment into Stage 5's phase-4b sitting —
so **the commit is the user's**, and this line is what a later reader needs to know that the mixture was
deliberate rather than accidental.

### Not done

- **`sts:SetContext` is half-tested.** The metadata path travelled with the RCP in place; version 4 vends
  *data* credentials through that action and nothing has read a row yet, so verification (ii) closes at
  pass 4's first query.
- **Pass 2's behavioural half is still owed** (can the persona actually tag — needs the tunnel and a
  governance-manager sign-in), **the crawlers have still never run**, and 4.3's SCP amendment is still
  owed via battery phase 4b.

## 2026-08-19 — Passes 0-3 propagated: what the findings cost the stages that had not run yet

*Provenance: **Claude's**, on the user's request to review the project's files and propagate the side
effects of this stage's findings into the rest of the plan. **No AWS call was made in this sitting** —
no profile was used, no `aws` command was run, and `./aws/datalake.py` was not re-run. Everything below
is a reading of the repository plus the local offline gates. It is logged here, in the stage whose
findings travelled, because there is no other file that records what a finding did after it was found.*

### Why a sitting with no apply has an entry

Passes 1-3 produced four findings, and each was written down where it was found. **That is not the same
as the plan having absorbed them.** A finding recorded only in the stage that produced it is a finding
the next stage meets again at the keyboard — which is the shape this project keeps calling Lesson 14.
The sitting went looking for where each one lands, and two of the landings were defects rather than
additions.

### The two defects, both in stages that have not started

| Where | What was wrong | What it would have cost |
|---|---|---|
| **[Stage 9](../plan/stages/stage-09-deployment-targets.md) step 2.2** | it instructed a post-grant reading of "the shared databases visible" from Production — but Production gets its first data lake administrator at **1.3**, which is a *later pass* | the reading would have come back empty and been diagnosed as INT-11 failing. The same empty catalog both Stage 5 consumers show today, met without the discriminator that explains it. 2.2 now reads the **RAM** side; the catalog confirmation moved to 2.3 |
| **This stage's own pass table** | three owed acts had **no owning pass** — the crawler pair of 3.3 (verification (iii)), the drop-box asymmetry halves, and 4.3's `athena:StartQueryExecution` amendment | an act with no pass is an act that does not happen. Pass 4's row now carries a numbered debt list, with 4.3's amendment **last** — it binds every principal in this account, and nothing in pass 4 that runs *here* may follow it |

### The finding that was in the applied state all along, unread

`curated.sample_trades` was created through the Glue API's Iceberg path — deliberately, so no Athena DDL
would exist in this account and 4.3's amendment could sequence freely. **The table therefore has no
rows**, and nothing had said what that costs:

- **verification (x) survives** — it reads the *column list*, which distinguishes all three states
  (`counterparty` absent, present, or the table not resolving). The stage text said "absent from the
  result and from the column list"; the result half was always going to be empty and said nothing;
- **[Stage 11](../plan/stages/stage-11-dlp.md)'s row-filter proof does not survive.** A row filter over
  an empty table returns nothing whether it works or is absent — Lesson 13 exactly. That proof now has a
  written dependency on **Stage 9's producer path having written real rows**, which is the designed way
  data enters `curated` at all (D22). The alternative — loading rows by hand through Athena here, before
  the amendment closes that door — is recorded at 4.1 and **not recommended**: it would use the one write
  path the design does not have.

### The instrument gap, which is the most dangerous item on this list

**`DL-6` is scoped to Data Governance alone** (`DATA_PROFILE`) — it was written when one account had a
`DataLakeSettings`. It is the check that decides whether the create-defaults were cleared, and those
defaults act at **creation time**, so there is no second reading later. Pass 4 gives Sandbox and
Development that resource and **nothing would be reading it there**. Recorded at step 8 and in
[`aws/INDEX.md`](../../aws/INDEX.md), to be extended in the same sitting that writes those settings.
No code was changed here.

### Where the four findings landed

| Finding | Propagated to |
|---|---|
| the create-defaults are not expressible in a plan and act at creation time (**Lesson 27**) | Stage 9's 1.3 (a two-step callout) and 4.1; Stage 6 (blueprint-created catalog objects); Stage 14 (the vend); Recipe D gained the four accounts it is already scheduled to run in |
| the grant option is mandatory on **every** cross-account grant | Stage 9's 2.1 — it stopped being that stage's peculiarity; `GLOSSARY.md` gained the *data lake administrator* entry that explains why |
| a TBAC expression on `classification` alone reaches the drop-box (**Lesson 29**) | Stage 9's 2.1 (with a recommendation: named-resource for the write, which decision 5 reserves for enumerated exceptions); Stage 6's new verification (xvi), for grants **DataZone** writes rather than this repository |
| a receiving account with no administrator shows an empty catalog while holding the share | Stage 9's 2.2 and its risks; Stage 6 (pass 4 became a **hard predecessor**); Stage 14 item 5, split into *plumbing* (the module's) and *entitlement* (the governance manager's); `GOVERNANCE.md` §Grants |

### One correction made to my own text, after the fact

The Stage 6 callout was written while the user was editing the same file with decisions 4 and 5. It said
"the Lakehouse blueprints", plural, which decision 4 then made wrong: **only `LakeHouseDatabase`
(`DataLake`) is enabled**, and it is precisely the Glue/Athena form whose output is per-project Glue
databases and Lake Formation permissions. The callout now names it — which made the point stronger, not
merely accurate: that blueprint does not touch this stage's surface, it writes on it. `LakehouseCatalog`,
disabled, provisions on Redshift-managed storage and none of this reaches it.

### Records

**No code.** No `.tf` file, no script, no AWS resource.

**Records:** [Stage 5](../plan/stages/stage-05-data-foundation.md) (the pass-4 debt list, 4.1's
empty-table callout, step 8's instrument note, verifications iii / x, the classification-pair
deliverable), [Stage 6](../plan/stages/stage-06-unified-studio.md) (1.4's callout, prerequisites,
verifications xiv-xvi), [Stage 9](../plan/stages/stage-09-deployment-targets.md) (status, pass ordering,
1.3, 2.1, 2.2, 4.1, risks, verifications ii / xiv), [Stage 11](../plan/stages/stage-11-dlp.md)
(prerequisites, 2.3, verification iii), [Stage 14](../plan/stages/stage-14-sandbox-vending.md) (item 5),
[stages/INDEX.md](../plan/stages/INDEX.md) (the Stage 5 row still read *not started*),
[`GOVERNANCE.md`](../GOVERNANCE.md), [`GLOSSARY.md`](../GLOSSARY.md),
[`cost-model.md`](../plan/cost-model.md) (the KMS row's open half settled by decision 2 — one lake CMK,
so the count moved 9 → 10), [the terraform-changes runbook](../plan/runbooks/terraform-changes.md)
(Recipe D's forward schedule), [`terraform-live/README.md`](../../terraform-live/README.md) (the lake
slice, absent from a file whose rule is to carry account-folder changes), [`aws/INDEX.md`](../../aws/INDEX.md)
and `CLAUDE.md`.

**Gates:** `make check` **OK** — 19048 relative links resolve, no broken `D`/`INT` reference, no
identifier. `make check-docs` stays red on its two pre-existing counts: hard-coded account numbers in
pre-Stage-2 prose, and `CLAUDE.md` over the 20 KB budget (it was already over before this sitting).

**Not committed by Claude**, and the tree is mixed on purpose: it also carries the user's own work on
[`docs/SMUS.md`](../SMUS.md) and on Stage 6's decisions 4 and 5, written during this sitting.

### Not done

- **Nothing was measured.** Every claim here is a reading of the repository or of a prior entry; the
  three questions this sitting *raised* — Stage 6's (xiv), (xv), (xvi) — are all settled by a session
  nobody has run yet.
- **`DL-6` was not extended**, only the debt written down. It belongs to the sitting that writes the
  consumer settings, so that the check and the resource arrive together (Lesson 14's good direction).
- The debts the previous entry left are unchanged: the crawlers have still never run, the persona-tagging
  proof still needs a governance-manager sign-in with the tunnel up, and 4.3's amendment is still owed.

## 2026-08-19 — Pass 4a/4b APPLIED: the consumer side exists, and the check that was passing was reading the wrong account

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting, and unlike
every entry since pass 3 it **does change AWS**: two `terraform apply` runs per consumer account, on the
user's explicit authorization given mid-sitting. Every measurement below is a read-only call made after
the write it reports on. Redactions per `scripts/check-identifiers.py`: accounts are named, never
numbered.*

### What the sitting was asked for, and what it turned into

It opened as *prepare the next step*. The preparation itself produced the finding, before a line of
Terraform was written — which is the whole argument for taking the before-reading first.

### The before-reading, and the reason it stopped being a formality

`get-data-lake-settings` in **both** consumer accounts, taken before authoring:

| | Sandbox | Development |
|---|---|---|
| `DataLakeAdmins` | `[]` | `[]` |
| `Parameters` | `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE` | idem |
| `Create{Database,Table}DefaultPermissions` | `IAM_ALLOWED_PRINCIPALS: ALL` | idem |

**Both hazards are symmetric, and nothing in the plan said so.** INT-11 was written about the producer:
an apply that names admins and omits `parameters` resets `CROSS_ACCOUNT_VERSION` to 1 and every share
fails silently afterwards. The consumer accounts turn out to carry the same two values — set by nobody in
this repository, defended by nobody until this pass — so the same resource in the same stage would have
reset them one account further from where anyone looks. And Lesson 27's create-defaults are live in both,
with the first local catalog object being the **resource link** rather than a database somebody notices.

### The instrument gap was worse than "not extended yet"

`DL-6` was reporting **`pass`** while two accounts sat in exactly the state it exists to fail. It was
scoped to `DATA_PROFILE` because Data Governance was the only account with a `DataLakeSettings` when it
was written; pass 3 wrote the debt down precisely so it would be paid in the sitting that writes the
consumer settings, and this is that sitting. Extended both checks per account. **In a consumer, `DL-6`
deliberately carries no *databases exist* guard** — the producer-side version has one — because the
defaults act at creation time and the reading is only actionable *before* the first link, which is
exactly when a guard would silence it.

`DL-5` was extended the same way, for the symmetry above. The report's admin table now carries
`Parameters` and both default blocks per consumer, so the discriminator is visible and not only checked.

### What was built

`terraform-modules/consumer-data/` (**v0.1.0**, new) and two thin slices calling it —
`terraform-live/sandbox/data/` and `terraform-live/development/data/`, both `[P]`, registered at rank
`data`. `s3-bucket` went to **v0.3.0** for one reason: it could expire only *noncurrent* versions, which
reaches nothing that was never overwritten, and `DL-9` fails a `*-derived` bucket with no `Expiration`
rule. Recipe B ran as a **chain of three commits** — `s3-bucket` tagged and pushed before
`consumer-data` could even `init`, then `consumer-data` tagged and pushed before the slices could.

**The module nests another module by tag, which this repository had not done before.** It resolves
exactly as the flat case does; the note is in the module rather than in a lesson, because the only new
fact is that the tag order has one more link in it.

### Three design points settled in the authoring, one of them by the user

**1. `scratch` is a prefix, not a bucket** — and the plan says both. `D13` is the origin and it is
unambiguous: *"non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access"* —
`scratch` there is the CLASS of everything Lake Formation does not govern, listed beside `artifacts` and
`model outputs`. Every line on the **IAM** side says *prefixes* (`identity/sso/`'s owed-grants note,
1b step 3.4, the set's own description); the three lines calling it a **bucket** are all on the topology
side (`architecture.md`, `conventions.md` §6, this stage's own table) and all credit **D19**, which does
not mention `scratch` anywhere. Both spellings entered in the same commit, so it is original ambiguity
rather than drift. The derived bucket carries three prefix families instead — `results/`,
`derived/${aws:userid}/`, `scratch/` — which is what the IAM side always described.

**2. The CMK is per (zone × account)** — **the user's call, and it changed the shape.** The question
reached the user as *scratch needs a key and only one is budgeted*; the answer reframed it: encryption
granularity is the `security-zone` dimension's job everywhere, not only inside the lake, so the consumer
key is `alias/awsds-<env>-zn-lab` rather than `alias/awsds-<env>-derived`. Same zone, different account.

The variant considered and declined in the same exchange was **the lake's own key**, and the reason it
was declined is a measurement rather than a preference: `AllowProductionPickupDecryptViaS3` on
`alias/awsds-data-zn-lab` grants `kms:Decrypt` to `awsds-prod-job-exec` with **no bucket scoping** — only
`kms:ViaService=s3` and the role ARN. Encrypting a consumer's derived zone with that key would put
Production's job role over this account's materialised `restricted` copies with the S3 layer as the only
thing left standing, which is the state D31 exists to prevent. Two further consequences were named: a
cross-account KMS dependency under a local working bucket, and a `security-zone` LF-Tag governing a bucket
no LF-Tag can be assigned to.

**3. The key policy delegates administration to root and no cryptographic action.** The module's default
policy — and the lake key's first statement — grants the account root `kms:*`, which means *the account's
IAM decides who may use this key*. Here that would undo D31 outright: any IAM policy in the account could
then grant `kms:Decrypt`, which is how D31 was created in the first place. So root keeps every
administrative action (the anti-lockout guarantee is intact, Terraform can re-policy and delete) and holds
no `Encrypt`, `Decrypt`, `GenerateDataKey*` or `ReEncrypt*`. **What it does not close is stated in the
file**: the administrator can call `kms:PutKeyPolicy` and rewrite the statement (Lesson 18). What the
shape buys is that widening it is an edit with a diff, not a side effect of some other grant.

### The apply, in Recipe D's two steps, per account

**The precondition was re-measured rather than assumed**, on the create plan:
`create_database_default_permissions` and `create_table_default_permissions` both come back
`after_unknown: true` — the plan states no intention about either, exactly as at pass 1 and in the same
pinned provider. Lesson 27 says a good reading does not retire the split, and it did not.

| | Sandbox | Development |
|---|---|---|
| step 1, settings alone under `-target` | `1 added` | `1 added` |
| the reading between | `DL-6` **pass** — omission clears | `DL-6` **pass** |
| step 3, the remainder | `15 added` | `15 added` |
| re-plan | `No changes` | `No changes` |

**The reading between the halves did something a green check usually does not: it failed, correctly.**
After Sandbox's step 1 and before Development's, the run reported `DL-6` **FAILED** for
`awsds-infra-dev` — the pre-apply state, in the account whose turn had not come. That is the extended
check working on its first outing, and it is the reading the old single-account version could not have
produced.

### What exists now, measured after the fact

Per consumer account: the zone CMK, `awsds-<env>-derived` under it with a 30-day expiry, the Athena
workgroup `awsds-<env>-athena` **enforcing** its configuration into `s3://awsds-<env>-derived/results/`
with a 10 GiB per-query scan cap, a `DataLakeSettings` naming `InfrastructureAccess`, two resource links
(`raw`, `curated`) and four grants to `DataScientistAccess`.

`./aws/datalake.py`: **0 check(s) FAILED**, and `DL-7` moved off its between-passes note to
*"4 share(s) out, 4 resource link(s) on the consumer side, no pending invitation"* — **verification (v)
is now answered in both halves**.

**The grants verified against the API rather than the code**, `list-permissions` in each account, four
rows for the persona and nothing else:

| Resource | Expression | Permissions | Grant option |
|---|---|---|---|
| `Database` (the `raw` link) | — | `DESCRIBE` | none |
| `Database` (the `curated` link) | — | `DESCRIBE` | none |
| `LFTagPolicy` DATABASE | `layer ∈ {raw, curated}` | `DESCRIBE` | none |
| `LFTagPolicy` TABLE | `layer ∈ {raw, curated}` AND `classification ∈ {public, internal}` | `SELECT`, `DESCRIBE` | none |

No grant option anywhere on the persona, which is 1b step 3.7 holding: the reader is never the grantor.

**One applied triple nobody wrote**, and it belongs in the register for exactly that reason: the
resource links carry `ALL, DESCRIBE, DROP` **with grant option** for `InfrastructureAccess` in each
account. Lake Formation gives the creator of a catalog object full permission on it; the code granted
none of it. Expected, undeclared, and now recorded.

### Verification (x), answered earlier in the chain than the plan expected

The plan frames the classification pair as a persona-session test. It is enforced one layer sooner, and
the column list says so with a negative control in the same reading:

| Read as `InfrastructureAccess` in | `sample_trades` columns |
|---|---|
| Data Governance (the owner) | `trade_id, trade_date, instrument, quantity, price, **counterparty**` |
| Sandbox, through the link | `trade_id, trade_date, instrument, quantity, price` |
| Development, through the link | `trade_id, trade_date, instrument, quantity, price` |

**The `restricted` column never crossed the account line.** The consumer's own data lake administrator
cannot see it either — an account may pass on only what it received, and `classification=restricted` was
never in the received expression. The share is doing column-level work before any persona exists, which
is a stronger result than the deliverable asked for and a different claim from the one still owed: what a
**persona** session sees is 4d's, and it needs the tunnel.

### Records

**Code:** `terraform-modules/s3-bucket/` (v0.3.0), `terraform-modules/consumer-data/` (v0.1.0, new),
`terraform-live/{sandbox,development}/data/` (new, 7 files each), `scripts/tfhygiene/backend.py`
(the `DATA_LAKE` emission), `scripts/tfhygiene/layers.py` (two rows), `aws/datalake.py` (`DL-5`/`DL-6`
per account), `aws/INDEX.md`.

**AWS:** 32 resources created across two accounts. Nothing destroyed, nothing changed.

**Gates:** `make check` **OK**. `pre-commit` green on all three commits; one commit rejected first by
tflint for two unused data sources in the slices, which were removed rather than suppressed.

**Branch `claude/stage-05-pass-4`, four commits, pushed with both tags. [PR #20](https://github.com/felipenoris/AWS-DataScience/pull/20)
opened on the user's authorization** — and its body says in the first line that the branch was **applied
before it was merged**, which is this repository's normal order for a `[P]` slice but is not the order a
reviewer assumes. The post-merge `plan` from the merge commit is owed, for the reason pass 1 recorded: a
fast-forward proves the two branches are the same object only until somebody rebases one.

### The merge, and the thing the rebase did to the tags

**Merged and synchronised (the merge is the user's).** The re-plan owed above was run from the merge
commit and comes back **`No changes` in all three slices** — both consumer slices and
`data-governance/data/`, the last included because a merge that touched the modules could have moved the
lake too. `./aws/datalake.py`: **all checks passed**. Local branch deleted, remote pruned.

**And the sentence that predicted this is the one that mattered: it was a REBASE merge, not a
fast-forward.** Every commit hash was rewritten, so both tags — `s3-bucket-v0.3.0`,
`consumer-data-v0.1.0` — still point at the pre-rebase commits, which are **no longer ancestors of
`main`**:

```
git merge-base --is-ancestor s3-bucket-v0.3.0 main   ->  orphaned
```

**Nothing is broken, and doing nothing is the correct response** — but that is a conclusion, not an
assumption, so it was measured: the *tree hash* of each module at its tag is **byte-identical** to the
same path on `main` (`87a1b29…` for `s3-bucket`, `ef07de3…` for `consumer-data`). `terraform init`
resolves a tag's **content**, not its position in a history, and the tagged commits survive garbage
collection because a tag ref pins them. Re-tagging is forbidden by the runbook's own §8, and cutting a
`v0.3.1` at the merge commit would mean a version bump on every merge for a diff of zero.

**Recipe B gained the check**, because this recurs on every merge from now on and the reflex it needs is
counter-intuitive: *expect `orphaned`, and verify the tree hash instead.* Two different tree hashes would
be the real fault — deployed callers pinned to code the repository no longer has — and that one is fixed
with a new version plus a caller bump, never with a moved tag.

### A second review pass, after the first propagation — seven things it had missed

The first pass propagated the findings into the stage files. Re-reading against the question *which file
OWNS each claim that changed* found that two of them had been updated everywhere except in the row that
asserts them:

| Where | What was still wrong |
|---|---|
| **INT-11** | the row describes the `Parameters` reset as a property of **Data Governance** throughout — it is the row that owns the claim, and the symmetry finding had gone into Stage 9 and the checks but not into it |
| **INT-03** | still read *"both consumers read `DataLakeAdmins: []` today … Stage 5 step 8 fixes it"*, of a thing done hours earlier; and it never said the re-grant is a **pair** |
| `aws/INDEX.md` | the `DL-6` row was corrected in the first pass and the **`DL-5`** row beside it still said *"read it after every apply in `data-governance/data/`"* — the exact scoping the session had just proven wrong |
| **Recipe D** | its forward schedule still listed all four accounts as pending. It is a live procedure; two of them ran, and *how* they ran (the precondition re-measured, the reading failing correctly once, the second value the split protected) is the part worth keeping |
| **`GLOSSARY.md`** | no entry for **resource link**, a term this session made load-bearing twice — it needs its own `DESCRIBE`, and it is the first local catalog object a consumer account creates |
| **D19** | the decision file records its own revisions inline (2026-08-08, 2026-08-12) and had none for the key's renaming or for `scratch` |
| **`terraform-modules/README.md`** | opened with **"Empty on purpose today"** while seven modules sat beside it — stale since Stage 3, and the natural home for the nesting rule this session created |

**Two lessons came out of the re-reading rather than out of the apply**, and both are about the record
rather than about AWS:

- **[Lesson 31](../plan/lessons.md)** — a check inherits the scope of the account it was written in and
  keeps reporting `pass` about that one. Deliberately *not* filed under Lesson 13: this check
  discriminates perfectly and is pointed at the wrong set, which is worse, because Lesson 13's failure
  looks empty and invites suspicion while this one looks like evidence. The cheap fix is printing the
  scope in the line, and the trigger to re-read every instrument is a **topology** change, not a code one;
- **[Lesson 32](../plan/lessons.md)** — two spellings of one object survive while nothing has to build it,
  and the side that has to build it is right. The tie-break that worked is *follow the citation*: all
  three "scratch bucket" lines credited D19, which never mentions it.

**Second-pass records:** [`integrations.md`](../plan/integrations.md) (INT-03, INT-11),
[`aws/INDEX.md`](../../aws/INDEX.md) (`DL-5`), [the terraform-changes runbook](../plan/runbooks/terraform-changes.md)
(Recipe D's schedule, now *where it has run* and *where it runs next*), [`GLOSSARY.md`](../GLOSSARY.md),
[D19](../plan/decisions/D19-derived-zone.md), [`terraform-modules/README.md`](../../terraform-modules/README.md),
[`lessons.md`](../plan/lessons.md) (31, 32) with their recognition keys in `CLAUDE.md`, and this stage's
**Deliverables** — the share pair's metadata half landed, the classification pair's absent half answered.

### Not done, and owed by name

- **4c — the persona grants in `identity/sso/`.** Deliberately *after* this apply rather than with it:
  the document is one object provisioned into many accounts, so the derived-bucket and workgroup ARNs
  would have had to be wildcards; now they can be read from these two slices' state and enumerated
  exactly. Without it the persona holds Lake Formation permission and no `athena:StartQueryExecution` and
  no `s3:PutObject`, so nothing can be queried yet.
- **4d — every behavioural proof**, which is all of them: the pandas pair, the persona half of the
  classification pair, the workgroup boundary, the crawler pair, the drop-box asymmetry. All need a
  persona sign-in with the tunnel up.
- **4e — 4.3's `athena:StartQueryExecution` amendment**, still last and still through battery phase 4b.
- Pass 6 (Security Hub) untouched; `DL-11` still notes it enabled nowhere.

---

## 2026-08-19 — Pass 4c APPLIED: the persona can query, and the drop-box write turned out to have only half a permission

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting. It **does
change AWS**: one `terraform apply` in the Identity account, on the user's explicit authorization
("pode rodar o plan e o apply"). Every measurement below is a read-only call made after the write it
reports on. Redactions per `scripts/check-identifiers.py`: accounts are named, never numbered.*

### Identity, stated before the calls

Applied as the **infrastructure user** on the **Identity** account through **`InfrastructureAccess`**
(profile `awsds-infra-identity`). The plan additionally *reads* state in **Sandbox Account 1**,
**Development** and **Data Governance**, each through that account's `InfrastructureAccess` — one
sign-in covers all four, since every profile sits on the `awsds` sso-session. `aws sts
get-caller-identity` was checked before the first call, as the rule requires.

### The finding, which arrived while authoring rather than while applying

4c was scoped as *Athena + the derived zone*. Reading the drop-box's applied form to write the S3
statements produced a third one, and it is a defect rather than an addition:

**The drop-box write is cross-account, so the bucket policy alone was never a working permission.** The
persona's role lives in Sandbox or Development; `awsds-data-dropbox` lives in Data Governance. Access
across an account line requires an allow in **both** the resource policy and the identity policy — and
the persona sets carried no S3 allow at all. A 4d attempt would have returned `AccessDenied` with
`AllowInteractiveWriterPutOnly` and `AllowDropBoxWritersViaS3` both correct, which is the expensive
shape: the error points at the half that is right.

**And the plan asserted the opposite in writing.** Step 6.2's reading, made on 2026-08-19 during pass 2,
ends: *"The drop-box `PutObject` exception 6.1 names is granted by **bucket policy** … so it does not
appear here, and that is correct rather than missing."* The reading itself was accurate — the sets held
no S3 allow — but the conclusion drawn from it was wrong. What made it plausible is same-account
intuition: within one account a bucket policy naming a role *is* sufficient, and the sentence was
written by someone (me) reading a bucket policy that names roles.

It is **Lesson 28's shape** — reach is an intersection and the two halves sit in different slices — on
plain S3 rather than on Lake Formation. Lesson 28 was written about a service *with its own permission
layer*, which is why it did not fire here; the lesson has been generalised rather than duplicated (below).

### What was applied

Seven statements added to **`DataScientistAccess`** — one document, provisioned into Sandbox and
Development:

| Sid | What it grants | The scoping that is the point |
|---|---|---|
| `RunQueriesInTheEnforcedWorkgroups` | the Athena run family (8 actions) | **the two workgroup ARNs, enumerated from the consumer slices' state** — `primary` is absent, and that absence is what denies it |
| `UseDerivedZoneBuckets` | `ListBucket`, `GetBucketLocation`, multipart list | the two derived buckets |
| `ReadDerivedZoneObjects` | `GetObject` | `results/`, `derived/`, `scratch/` — read at decision 6's **persona** grain |
| `WriteDerivedZonePrefixes` | `PutObject` + the multipart pair | `results/`, **`derived/${aws:userid}/`** (per principal), `scratch/` |
| `DeleteScratchObjects` | `DeleteObject` | **`scratch/` only** — `results/` and `derived/` are deleted by the 30-day lifecycle and by nothing else; `DeleteObjectVersion` is not granted anywhere |
| `WriteIngestionDropBox` | `s3:PutObject` | `awsds-data-dropbox/incoming/*` — the identity half above, mirroring the bucket policy's asymmetry exactly: no read-back, no list, no delete |
| `UseLakeZoneKeyViaS3` | `GenerateDataKey`, `Decrypt` | the lake's `zn-lab` CMK, `kms:ViaService = s3` — the same condition the key policy carries, each side scoping the other |

**Why `results/` is writable by a human who never chooses to write there:** Athena stages query results
**with the caller's credentials** into the workgroup's enforced location. No `PutObject` on `results/`
means no output means no query — the grant is the engine's contract, not a convenience.

**No KMS statement for the derived zone**, and its absence is deliberate: those keys are same-account, so
the key policy — which names this role and nobody else — decides alone. That is D31 working as designed.

### One ledger line corrected rather than delivered

`policies-data-scientists.tf` has carried a `STILL OWED` ledger since Stage 2. One of its Stage 5 lines
was *"s3:GetObject on the governed lake through the Lake Formation share"*. **No such grant will ever
arrive.** Vended access hands the engine credentials through `lakeformation:GetDataAccess`, which the set
already holds; a direct `s3:GetObject` on a registered prefix is precisely the bypass D13 exists to
exclude. That line was Stage 2 guessing at Stage 5's interface — the exact failure the file's own opening
comment warns against, caught by delivery rather than by review.

### The plumbing, in one paragraph

`backend.py` emits two new maps to `identity/sso` — `data_consumers` and `lake` — so the slice gained its
**fifth and sixth** cross-account lookups, both `terraform_remote_state` reads with a profile, exactly
like `vpn_home`. The workgroup and bucket ARNs come from the consumer slices' outputs; the drop-box ARN,
its prefix and the key ARN from the lake's. **The key ARN carries the lake's account id**, which is why
it is read from state and never written down — the same rule `aws/INDEX.md` rule 1 states for every
identifier. `data_consumers` validates non-empty with the *opposite* polarity from `vpn_homes`, noted in
the variable: an empty map there denies everything, here it renders three allows with no resource and
fails at provisioning, per account.

### The apply, and the reading that proves it landed

```
Plan: 0 to add, 1 to change, 0 to destroy.
inline_policy_bytes: data_scientist 4285 -> 7036
```

Applied; **re-plan `No changes`**. The 7036 is against the plan-time ceiling of 10240 — the precondition
Stage 2 built for exactly this moment, and the first time it has had a real increase to measure.

**Then the reading that matters, because a permission set is not where the permission lives.** A set
becomes an IAM role in every account it is provisioned into, so `1 changed` in Identity proves nothing
about Sandbox and Development. `get-role-policy` on `AWSReservedSSO_DataScientistAccess_*` in **both**
accounts returns **all 18 statements**, the seven new ones included — so the reprovisioning happened
rather than being assumed. And in the same reading, `WriteDerivedZonePrefixes` comes back carrying
`.../derived/${aws:userid}/*` **as a literal policy variable**, not expanded and not mangled by the
round trip through Terraform's `$${...}` escape.

### The instrument gained the check that would have caught it — `DL-12`

The defect got past a review, a plan, a commit gate and three passes. What none of them had is a
question that can be *asked mechanically*, so one was added: **`DL-12` reads the drop-box's identity
half off the PROVISIONED role in each consumer account** — `WriteIngestionDropBox` and
`UseLakeZoneKeyViaS3` present, or a `fail` naming what is missing. `DL-2` has always measured the
resource half; the pair is now what "the drop-box write works" means to the instrument, which is the
AND the evaluation rule actually is.

**It reads the role and not the permission set, deliberately.** A set lives in Identity and *becomes* a
role in every account it reaches; the role is where the permission is, and it is also the object a
half-finished reprovisioning would leave stale. `./aws/datalake.py`: **`DL-12` pass in both consumer
accounts, 0 FAILED overall.** Its negative control is not hypothetical — the plan diff for this apply
showed both statements as additions, so the check would have failed against the state that existed this
morning.

### Records

**Code:** `terraform-live/identity/sso/` (`variables.tf`, `data.tf`, `locals.tf`,
`policies-data-scientists.tf`), `scripts/tfhygiene/backend.py`, `aws/datalake.py` (`DL-12`, new).

**Docs:** the stage file (status row, pass table, the 4c paragraph, **6.2's correction**),
`docs/GOVERNANCE.md` (§Drop-box: the writer's permission is two-sided),
`terraform-live/data-governance/data/README.md` (the `AllowInteractiveWriterPutOnly` row says which half
it is), **`docs/plan/integrations.md` (INT-10 amended — it described only the resource half)**,
`docs/plan/lessons.md` (**Lesson 28 amended**, not duplicated), `CLAUDE.md` (the Stage 5 bullets
consolidated in the same sitting — the section's own budget rule, and my additions had been growing it).

**The propagation sweep, and it came back closed.** Every resource policy in the applied estate that
names a **foreign** principal was enumerated: four statements, all in the lake — the two writer ones
(Sandbox + Development, on the bucket and on the key) and the two Production pickup ones. The writer's
identity half is what this sitting applied; **the pickup's was already correctly specified**, in Stage 9
step 3.1, which says in those words *"the identity half of Stage 5's statements"*. So the plan was right
where the role is authored beside its grant and wrong only where the two halves sat five stages and two
slices apart — the defect correlates with **distance**, not with the concept, and that is the useful
half of the finding.

**Two files were missed on the first pass and found by the user asking whether everything had been
edited — both of them owners of the changed claim, which is Lessons 31-32 again.**
`identity/sso/README.md` carries an **owed table**, one row per stage, and its Stage 5 row still
promised the work this sitting delivered *and* repeated the corrected line (*"lake read through the
Lake Formation share"*). `aws/INDEX.md`'s question table had a row for every `DL-` check except the new
one. Neither is prose: the first is what a reader opens to learn what a persona is still missing, the
second is how a check is found by the question it answers. The pattern to carry: **a delivery has to
sweep the files that say the thing is still owed**, and an index of checks is one of them.

**AWS:** 1 resource changed, in the Identity account. Nothing created, nothing destroyed. The two
provisioned roles were re-written by Identity Center as a consequence, which is the change that matters
and is not what Terraform counted.

**Gates:** `make check` **OK**; `pre-commit` green on the five changed files, including tflint, checkov
and the 9.2 wildcard-account check — the last one is the one that would have fired had 4c been written
before the consumer slices existed.

### Not done, and owed by name

- **4d — every behavioural proof**, unchanged in scope but no longer blocked by entitlement: the pandas
  pair, the persona half of the classification pair, the workgroup boundary, the crawler pair, the
  drop-box asymmetry. All need a persona sign-in with the tunnel up. **The drop-box half is now worth
  more than it was**: it is the first exercise of a permission that was measured wrong on paper.
- **4e — 4.3's `athena:StartQueryExecution` amendment**, still last and still through battery phase 4b.
  Note it binds Data Governance only; nothing applied today runs there.
- Pass 6 (Security Hub) untouched; `DL-11` still notes it enabled nowhere.
- **Not committed** — the working tree carries all nine files; the branch is the user's call.

## 2026-08-19 — The `security-zone` dimension is WITHDRAWN and APPLIED away: one data CMK per account

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting. **The
decision is the user's**, and so is the authorization to apply ("pode fazer apply do terraform qdo
concluir"). It **changes AWS**: four `terraform apply` runs in four accounts, one of them destroying an
LF-Tag and a grant. Every measurement below is a read-only call made after the write it reports on.
Redactions per `scripts/check-identifiers.py`: accounts are named, never numbered.*

### How the decision arrived, which is the part worth keeping

**It came out of a conversation, not a review.** The user opened a discussion of the bucket layout, the
CMK and the SMUS intersection, and worked through it as a series of verification questions — are LF-Tags
attached to buckets, which CMK encrypts each bucket, how did you conclude `dropbox`/`artifacts`/`logs`
sit under the `zn-lab` key when those buckets carry no `security-zone` assignment. That last question is
the one that broke the model open, and the honest answer was that the conclusion came from
`buckets.tf` — a single `kms_key_arn` on the `for_each` — and **not from any tag**.

The user then named it themselves, in one sentence: *"eu decidi errado: achei que a chave CMK estava
associada a uma LF tag."* The mechanism does not exist. An LF-Tag attaches to a database, table or column
and is read by Lake Formation when it evaluates a TBAC expression; a CMK is bound to a bucket by that
bucket's default-encryption configuration, written by Terraform. **Nothing in AWS connects the two.**
What connected them here was the shared spelling `zn-lab` in a tag value and a key alias, plus a review
habit — and the tag appeared in **no TBAC expression at all**, so the dimension was carrying nothing.

So the dimension is withdrawn, one day after it was applied, and the rule that replaces it is simpler and
is what the code already did: **one data CMK per account**, `alias/awsds-<env>-data`.
[`docs/GOVERNANCE.md`](../GOVERNANCE.md) §Encryption is its one copy and carries the withdrawal note, so
the correction is readable where the model is rather than only here.

**What survived the wrong premise, checked rather than assumed.** The (zone × account) decision of pass
4a/4b rested on *two* arguments, and only the first was the premise that fell:

- the framing — *a derived copy of a `zn-lab` table is still `zn-lab` data* — **is gone with the
  dimension**;
- the refusal to share the **lake's** key across the account line is a **measurement**, not a framing:
  `AllowProductionPickupDecryptViaS3` grants `kms:Decrypt` to `awsds-prod-job-exec` with no bucket
  scoping, so a consumer's derived zone under that key would put Production's job role over that
  account's materialised `restricted` copies. **That stands verbatim**, and it is why the outcome — a
  dedicated key per consumer account — did not move even though the reason for its *name* did. D31 is
  untouched for the same reason: its control is the key policy's contents, never the alias.

### Identity, stated before the calls

Four accounts, four profiles, all the infrastructure user through `InfrastructureAccess`, one sign-in
(every profile sits on the `awsds` sso-session): **Data Governance** (`awsds-infra-data`), **Sandbox
Account 1** (`awsds-infra-sandbox-1`), **Development** (`awsds-infra-dev`), **Identity**
(`awsds-infra-identity`). `aws sts get-caller-identity` was checked before the first call — it came back
`NoCredentials`, which is why the sitting opens with an `aws sso login` rather than with a plan.

### The mechanic that made this cheap, and it was chosen rather than discovered

**A CMK rename is an alias operation, and the alias is not the key.** The user chose *rename in place*
over *new key*, so the three key objects never move and **no object is ever re-encrypted**: every S3
object keeps pointing at the same key id, and the aliases that name it change. In Terraform that is a
`moved {}` block per module address (`zn_lab_key` → `data_key`, `zone_key` → `data_key`) plus a new
`alias_name`, and **the plan is the proof it worked**:

```
module.data_key.aws_kms_alias.this must be replaced
module.data_key.aws_kms_key.this   will be updated in-place
```

The **key** is `updated in-place` — not replaced, not destroyed, not re-created under a new id. Had the
`moved` blocks been absent, the same rename would have read `destroy` + `create` on the key itself, which
is a 7-day deletion window and an unreadable lake. The blocks are annotated as removable once every
caller has applied, which they now have.

### The four applies, in dependency order

| Slice | Account | Plan | Result | Re-plan |
|---|---|---|---|---|
| `data-governance/data/` | Data Governance | `4 to add, 3 to change, 6 to destroy` | applied | **`No changes`** |
| `sandbox/data/` | Sandbox Account 1 | `1 to add, 1 to change, 1 to destroy` | applied | **`No changes`** |
| `development/data/` | Development | `1 to add, 1 to change, 1 to destroy` | applied | **`No changes`** |
| `identity/sso/` | Identity | `0 to add, 1 to change, 0 to destroy` | applied | **`No changes`** |

**The producer's six destructions, named because one of them is a governance object and not a rename:**
`aws_lakeformation_lf_tag.security_zone` (the dimension itself),
`aws_lakeformation_permissions.gm_associate_security_zone` (the governance manager's `ASSOCIATE` on it),
the three `aws_lakeformation_resource_lf_tags` assignments **replaced** to drop their `security-zone`
block, and the alias. The three changes are in-place: the key's description, and the two service roles'
inline policies where the Sids were renamed (`UseZnLabKey` → `UseDataKey`, `KmsDecryptZnLab` →
`KmsDecryptDataKey`).

**Recipe D was not used here and that is deliberate**: the two-step apply exists to read
`Create*DefaultPermissions` before a database is created, and nothing in these plans touches
`aws_lakeformation_data_lake_settings` or creates a catalog object. `DL-5`/`DL-6` still bracket the
sitting, per the standing rule, and both read clean before and after in all three Lake Formation
accounts.

**Recipe B ran and its documented failure fired once.** `consumer-data-v0.2.0` was tagged and pushed
before either slice could resolve it, and the second commit was **blocked** by `Module source has
changed` — the stale local module install, exactly the trap pass 1 recorded and the recipe warns about.
`terraform get -update` in both slices cleared it. Worth noting the shape: the block came from the
**commit gate**, not from an apply, which is the gate doing its job a step earlier than the runbook
describes it.

### What the estate reads now

- **LF-Tags: `classification` (4 values), `layer` (3).** `security-zone` is gone from
  `list-lf-tags` — the ontology is two keys plus the reserved `businessunit`;
- **aliases: `alias/awsds-data-data`, `alias/awsds-sandbox-data`, `alias/awsds-dev-data`** — one data CMK
  per account, and each account's `awsds-<env>-tfstate` key sits beside it untouched, which is the
  distinction §Encryption insists on (one key per account **for data**, not one key per account);
- **`DL-5`: `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE`** in Data Governance, Sandbox and Development,
  before and after;
- **`DL-6`: no `IAMAllowedPrincipals` create-default** in all three;
- **`DL-7`: 4 shares out, 4 resource links, no pending invitation** — the shares are indifferent to the
  key rename, as they should be;
- **`0 check(s) FAILED`** overall.

### `DL-12` failed correctly in the before-reading, and that is a feature

The pre-apply run reported **`DL-12` FAILED in both consumer accounts**, naming
`UseLakeDataKeyViaS3 (GenerateDataKey/Decrypt via S3)` as missing. It was: the instrument had already
been edited to look for the new Sid, and the provisioned roles still carried the old one. **The check was
describing the estate accurately** — the identity half under its new name genuinely did not exist yet —
and it went `pass` in both accounts after the fourth apply.

This is the same shape as pass 4a/4b's `DL-6` reading FAILED for Development while its turn had not come,
and it is worth writing down twice: **an instrument edited ahead of the apply it measures reports the
truth about a state that is about to stop existing.** The failure mode to guard against is the opposite
one — reading that red as a defect and "fixing" it — which is why the plan diff is the negative control
in both cases.

### The grant register loses a row's worth of triples — its first removal

`docs/AWS_STATE.md`'s Lake Formation grant register goes **25 → 24 applied triples**. The governance
manager's `ASSOCIATE` row covered three tags and now covers two. **The row was annotated rather than
rewritten**: it names the revoked `security-zone` triple and its date, because a register whose past
silently matches its present cannot show that something was withdrawn. That is the same discipline
`POLICIES.md` keeps, applied to the first grant this project has ever taken away.

### The second review pass, and it found the rows that own the claim — again

After the propagation was written, a **four-lens adversarial review** ran over the diff (stale
current-state claims; `GOVERNANCE.md` self-consistency; the two per-`Sid` READMEs against their `.tf`;
forward-looking plan files), each finding then handed to a verifier prompted to **refute** it. Thirteen
agents, nine confirmed findings, **six distinct fixes** — and the pattern is pass 4's, for the third
time:

| What was missed | Why it matters |
|---|---|
| **`CLAUDE.md`'s routing table** still enumerated `security-zone` in the ontology **and** called the consumer key "zone CMK" | The two rows whose whole job is to say where the model lives — contradicting a bullet I had written into the same file minutes earlier |
| **`AWS_STATE.md`** said the account holds the GM's **"nine grants"** | Its own register two screens below already counted eight |
| **INT-10** pointed the Stage 9 executor at Sid **`UseLakeZoneKeyViaS3`** | The row that exists to name where the two halves are, naming a Sid that no longer exists. **This one no grep of mine would have caught** — it contains neither `zn-lab` nor `security-zone` |
| **`GOVERNANCE.md` §Encryption** argued against a key "that also served state and **logs**" | The lake's own `awsds-data-logs` sits under the data key, so the new section's rationale indicted the applied design. Narrowed to Terraform state, with `logs` named as data |
| **Stage 6** called the consumer CMK "the derived-zone key" in three forward-looking spots | The object a Stage 6 executor must edit is `alias/awsds-<env>-data` |
| The lf-registration role's trust Sid **`LakeFormationService`** had no README row | Pre-existing gap in the one-row-per-`Sid` discipline, found in passing |

**The transferable half is the search method, not the findings.** A textual sweep finds the *word* that
changed; it cannot find a claim that was made in the old model's vocabulary without using its terms — a
count ("nine grants"), a renamed `Sid`, an argument whose example is now wrong. Those need a reader with
the new model in hand, which is what the lenses were.

### Records

**Code:** `terraform-live/data-governance/data/` (`kms.tf`, `lakeformation.tf`, `catalog.tf`,
`governance.tf`, `buckets.tf`, `maintenance.tf`, `outputs.tf`, `providers.tf`),
`terraform-modules/consumer-data/` (`kms.tf`, `buckets.tf`, `athena.tf`, `outputs.tf`, README) at
**v0.2.0**, `terraform-live/{sandbox,development}/data/` (`main.tf` pin, `outputs.tf`),
`terraform-live/identity/sso/` (`data.tf`, `locals.tf`, `variables.tf`,
`policies-data-scientists.tf`), `aws/datalake.py` (`DL-12`'s Sid), `aws/deploytargets.py`
(`PROD_CMK_ALIAS` → `alias/awsds-prod-data`), `scripts/tfhygiene/{layers,backend}.py` (descriptions).

**Docs:** [`docs/GOVERNANCE.md`](../GOVERNANCE.md) — **§`security-zone` deleted, §Encryption written** as
the one copy, plus the LF-Tags table, §Drop-box, §Derived zone and §Persistence;
[`docs/AWS_STATE.md`](../AWS_STATE.md) (the state row, the register preamble and its GM row);
[`D19`](../plan/decisions/D19-derived-zone.md) (a second revision note — the zone framing kept as
history); the stage file (build table, decisions 1/2/3, steps 1.4, 2, 6.2, 9.2, cost row); stage files
**6, 9, 10, 14**; both lake READMEs; [`docs/plan/integrations.md`](../plan/integrations.md) (INT-10);
`cost-model.md`, `architecture.md`, `conventions.md`, `SMUS.md`, `terraform-live/README.md`;
[`docs/plan/history.md`](../plan/history.md) (the withdrawal, since provisioned objects changed);
`CLAUDE.md` (routing table + a Current-position bullet).

**AWS:** 6 added, 6 changed, 8 destroyed across four accounts — of which **exactly two destructions are
governance objects** (the LF-Tag and its grant); everything else is an alias replacement or an in-place
policy edit. **No key was created, none was deleted, no object was re-encrypted, and the monthly KMS cost
is unchanged** at three data keys.

**Gates:** `make check` **OK** (twice — before the applies and after the review pass); `pre-commit` green
on every commit, tflint/checkov/ruff included; `terraform validate` clean in all four slices.

### Not done, and owed by name

- **4d — every behavioural proof**, unchanged and still the real debt: the pandas pair, the classification
  pair's persona half, the workgroup boundary, the crawler pair, the drop-box asymmetry. All need a
  persona sign-in with the tunnel up. **This sitting added nothing to that list and removed nothing from
  it** — a rename is invisible to every one of those proofs, which is the point of renaming rather than
  re-keying.
- **4e — 4.3's `athena:StartQueryExecution` amendment**, still last, still through battery phase 4b.
- Pass 6 (Security Hub) untouched; `DL-11` still notes it enabled nowhere.
- **The two `moved {}` blocks are now removable** — every caller has applied — but they were left in
  place deliberately this sitting: removing them is a separate diff with nothing else in it, which is how
  a state-address change should be reviewed.

## 2026-08-19 — Pass 4d opened: the host's first start met a capacity wall, the topology was read, and the VPN runbooks were unified

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting. **The one
AWS write is the user's hand** — two `ec2:StartInstances` attempts, as the infrastructure user in
`Sandbox` (`InfrastructureAccess`); everything else below is a read-only call. The error message is
the user's paste, verbatim. No apply, no policy change, no grant.*

### The sitting's decision: start the host, not the account

Pass 4d's proofs all ride the tunnel, and the session opened with the question *"tenho que rodar o
make up para sandbox?"*. The answer, measured against `scripts/tfhygiene/layers.py` and both
dry-runs: **no** — `make up ENV=sandbox` would also apply the two `[E]` slices (`egress/` at
USD 0.160/h, `probes/` at 0.0084/h) against the tunnel's own 0.0042/h, and **no 4d proof runs inside
a VPC**: everything leaves the laptop, transits the host's masquerade and exits through the Elastic
IP or the `[P]` gateway endpoints. The NAT and the interface endpoints serve the *private* subnets
(their route is installed only in the private route tables), which nothing occupies until Stage 6.
So the sitting used the host-only start — now §S5 of the unified runbook — and the `[E]` slices
stayed down.

### The start, and the first `InsufficientInstanceCapacity` this project has met

The user's first attempt returned, verbatim:

```
aws: [ERROR]: An error occurred (InsufficientInstanceCapacity) when calling the StartInstances operation (reached max retries: 2): Insufficient capacity.
```

The discriminating reads (Claude, read-only): the instance was left cleanly `stopped` — a failed
start has no intermediate state to undo — and `describe-instance-type-offerings` shows **`t4g.nano`
IS offered in the host's AZ**, so this was transient pool exhaustion, not a configuration defect. A
stopped `[D]` instance holds no hardware; every start re-contests capacity like a fresh launch, and
a one-AZ Graviton nano is where the pool runs dry first — the hidden price of D11's "pay nothing
while idle", now measured rather than assumed. **The user's retry succeeded minutes later**:
`running`, same type, same AZ, launch 23:04:41Z. `./aws/vpn.py` read **0 FAILED** with `VP-2`
confirming the Elastic IP reassociated to the host — every client config untouched, which is what
that `[P]` allocation exists to guarantee. The remediation ladder (retry; then `t4g.micro` by
deliberate apply; never an AZ move) is written into §S5 rather than left here.

### The topology, read rather than believed — and one 4d probe corrected by it

Three readings taken while answering *"o egress não é necessário para a VPN?"*, all now §S2/§S3 of
the runbook:

- the host sits in the **public** subnet; its route table sends `0.0.0.0/0` to the **IGW** — no NAT
  anywhere on the path;
- the same route table carries the **two `[P]` gateway endpoints** (S3, DynamoDB), so tunnel traffic
  **splits by destination**: S3 arrives at a bucket as `aws:SourceVpce`, every other API as
  `aws:SourceIp` = the Elastic IP. The drop-box bucket policy, read back, mirrors the split exactly —
  its `DenyOutsideTrustedNetworks` names that gateway endpoint id and that `/32`, INT-05 restated as
  policy;
- `source_dest_check` is **on**, deliberately, over a forwarding host — everything is masqueraded, so
  the check stays as anti-spoofing and a broken masquerade fails visibly at the host.

**The finding that changes a 4d probe:** the same bucket-policy condition carries an
`aws:PrincipalAccount` branch admitting the lake account's own principals **from any network** — so
the carve-out pair's negative half ("a caller satisfying no branch is denied") proves nothing if run
as that account's `InfrastructureAccess`. It must run as a principal from a **different** account,
off-tunnel; the on-tunnel persona pandas probe then fails by *implicit* deny (D13, no S3 grant
anywhere), and the two denials carry different wording — the pair Lesson 13 asks for.

### The repository work, at the user's request

`vpn-keys.md` and `vpn-client.md` **unified into [`runbooks/vpn.md`](../plan/runbooks/vpn.md)** —
their content kept whole as Parts K and C (procedures keep their letters, sections gained `K`/`C`
prefixes), plus a new **Part S** written from this sitting's readings: the components table, the
measured topology, the VPN-vs-`egress/` split, why persona work needs the tunnel, and **§S5 —
start/stop** with the Name-tag lookup (the id is never written down: a roster change replaces the
host), the guarded one-liner (Lesson 25's empty-id trap named), and the capacity note above.
References updated in `CLAUDE.md` (two routing rows merged into one), `README.md`,
`docs/GENERAL_PLAN.md`, `docs/ORGANIZATION.md`, `stage-04-vpn.md` (historical mention annotated, not
rewritten), `scripts/check-tfvars-shape.py` (two error strings), and one link target in the Stage 4
log (text kept, href only). One gap written down for the next sitting: **no `awsds-scientist-dev`
profile exists** in the local CLI config — the Development-side persona proofs need it, a local
config edit, no AWS change.

### Not done, and owed by name

Every 4d proof is still owed — the tunnel was not yet up when this entry was written; the host is
`running` and waiting. Then 4e (the SCP amendment, last, through battery phase 4b) and pass 6
(Security Hub). The stage's debt list is unchanged by this sitting except in one respect: the
carve-out pair's negative half now has its correct principal written down.

## 2026-08-19 — Pass 4d's first proof: the perimeter fires off the tunnel and stands down on it, in two different wordings

*Provenance. **The `~/.aws/config` edit and every command below are the user's**, run from the laptop
and pasted verbatim, with **one mechanical substitution, named here and made nowhere else: account ids
→ the account's name**. Nothing else in the outputs is touched — the `AWSReservedSSO_*` suffix, the
resource ARNs, the shell prompts and the error wording arrived as they read. **Claude wrote the
analysis around them and nothing else**, and made no AWS call in this sitting.*

### The prerequisite the previous entry left owed

`awsds-scientist-dev`, added to `~/.aws/config` — a local file, no AWS change. It reaches
`<Development Account>` through the **same `awsds-scientist` sso-session** as the Sandbox persona
profile and the **same `DataScientistAccess` permission set**: person and role coincide, so the name
carries no role segment (`aws/AWS-CLI.md`'s rule), and one sign-in covers both accounts.

```
[profile awsds-scientist-dev]
sso_session = awsds-scientist
sso_account_id = <Development Account>
sso_role_name = DataScientistAccess
region = us-west-2
```

### The pair — one command, two networks, two wordings

**Tunnel DOWN**, as the infrastructure user in `<Sandbox Account 1>` — a principal from an account
**other** than the lake's, which is the correction the previous entry wrote down. `/dev/null` is the
`OUTFILE` positional `get-object` requires; a denial is what the command is for, so nothing is written:

```
~ aws s3api get-object --bucket awsds-data-curated --key qualquer-coisa /dev/null --profile awsds-infra-sandbox-1

aws: [ERROR]: An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_InfrastructureAccess_59e5b26af457128d/<the infrastructure user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-data-curated" with an explicit deny in a resource-based policy
```

**Tunnel UP**, credential cache cleared first so that no session minted off the tunnel could be
replayed and turn a network reading into an identity one (Lesson 25), then the identical command:

```
~ rm -f ~/.aws/cli/cache/*.json
➜  ~ aws s3api get-object --bucket awsds-data-curated --key qualquer-coisa /dev/null --profile awsds-infra-sandbox-1

aws: [ERROR]: An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_InfrastructureAccess_59e5b26af457128d/<the infrastructure user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-data-curated" because no resource-based policy allows the s3:ListBucket action
```

### What the two wordings prove

**The statement that fired is `DenyOutsideTrustedNetworks`** (`data-governance/data/buckets.tf`), read
from the code rather than inferred from the message — IAM names neither the policy nor the `Sid` in a
resource-policy denial. Its condition block is five tests ANDed, and off the tunnel every one of them
held: no `aws:SourceVpce` key at all (a request over the public internet has none, and a *negated*
operator on an absent key evaluates **true** — the mechanism the whole branch rests on), an
`aws:PrincipalAccount` that is Sandbox rather than the lake, a source address outside both Elastic-IP
`/32`s, and neither `aws:ViaAWSService` nor `aws:PrincipalIsAWSService` set.

**`s3:ListBucket` in place of `s3:GetObject` is not a mismatch.** The key does not exist, and S3 decides
between `404 NoSuchKey` and `403 AccessDenied` by evaluating `s3:ListBucket` on the *bucket*; that
evaluation hit the deny first. The statement covers `[arn, arn/*]`, so it is the same statement either
way — and a `NoSuchKey` here would have been the bad reading, since it would mean the call was
authorized.

**On the tunnel the wording changes to the implicit-deny form**, which is the half that makes this a
verification rather than a single denial (Lesson 13): *"because no resource-based policy allows"* is
what IAM says when **no explicit deny matched**. So the perimeter stood down — the request satisfied a
trusted branch — and what refuses the call is now the absence of a grant. That absence is Lesson 28's
shape from the far side: a cross-account read needs an allow in **both** the caller's identity policy
and the bucket's resource policy, and the lake's policy grants this account nothing on `curated`.

**One thing the pair does not settle, and it is worth not over-claiming.** The on-tunnel reading proves
*a* trusted branch matched; it cannot say **which**, because `aws:SourceVpce` (the consumer gateway
endpoint) and `aws:SourceIp` (the Elastic IP) are both trusted and the message names neither. What
discriminates them is the route-table reading in the previous entry — the public subnet carries the two
`[P]` gateway endpoints, and a prefix-list route is more specific than `0.0.0.0/0` — not this message.
A future claim that "the `aws:SourceVpce` branch is proven end to end" needs the flow log or an S3 data
event carrying `vpcEndpointId`, and neither was read here.

### The tunnel, in two readings

```
~ curl -s https://checkip.amazonaws.com
52.89.212.1

~ dig +short SOA sandbox.internal
ns-1536.awsdns-00.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
```

The address is the `[P]` Elastic IP of `sandbox/foundation/`, unchanged across every host stop, start
and replacement since 2026-08-17 — so the **full** tunnel is real and the laptop's non-S3 traffic
leaves through the host's masquerade. The SOA answer is the second, different claim: `sandbox.internal`
is a **private** hosted zone associated with the Sandbox VPC alone, so it NXDOMAINs from any public
resolver — an answer means the VPC resolver was reached, i.e. DNS is inside the tunnel too. §C2's third
check, the handshake, is not in this record; the two above carry the claim on their own, since neither
can succeed without a live tunnel.

### Not done, and owed by name

Every **persona** proof of 4d is still owed, and none of them has run: the Athena query through the
resource link, the five-column read with `counterparty` absent, the pandas/S3 implicit-deny pair, the
workgroup boundary, the drop-box asymmetry (`PutObject` yes, `GetObject` no) and the crawler pair — in
**both** Sandbox and Development, which is what the new profile exists for. Then the explicit
`restricted` grant and its revert, then **4e** (the `athena:StartQueryExecution` amendment, last,
through battery phase 4b) and pass 6 (Security Hub). What this sitting closed is the carve-out pair
alone — the one 4d proof that needed no persona.

## 2026-08-19 — Pass 4d, group A in Sandbox: five proofs land, and the drop-box write is broken by a deny nobody connected to the gateway endpoint

*Provenance. **Every command and every output below is the user's**, run from the laptop with the
tunnel up and pasted verbatim, with **one mechanical substitution, named here and made nowhere else:
account ids → the account's name, and the persona's e-mail inside an ARN → that user's role**. Nothing
else is touched — the `AWSReservedSSO_*` suffix, the query-execution ids, the shell prompt fragments
and the error wording arrived as they read. **Claude wrote the analysis around them and nothing else**,
and made no AWS call in this sitting. The two writes below are the user's hand: one Athena query and
one attempted `PutObject`.*

### A1-A3 — the identity, the column list, and the first persona query

```
aws sso login --sso-session awsds-scientist

# checking profile

AWS_PROFILE=awsds-scientist-sandbox aws sts get-caller-identity --query Arn --output text

arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user>

AWS_PROFILE=awsds-scientist-sandbox aws glue get-tables --database-name curated --query 'TableList[].Name' --output text

sample_trades

AWS_PROFILE=awsds-scientist-sandbox aws glue get-table --database-name curated --name sample_trades --query 'Table.StorageDescriptor.Columns[].Name' --output text

trade_id        trade_date      instrument      quantity        price

AWS_PROFILE=awsds-scientist-sandbox aws athena start-query-execution --work-group awsds-sandbox-athena --query-string "SELECT * FROM curated.sample_trades LIMIT 10" --query QueryExecutionId --output text

19893d80-17d4-45dd-b5b7-398e8de15032

AWS_PROFILE=awsds-scientist-sandbox aws athena get-query-execution --query-execution-id 19893d80-17d4-45dd-b5b7-398e8de15032 --query 'QueryExecution.{State:Status.State,Reason:Status.StateChangeReason,Out:ResultConfiguration.OutputLocation,Scanned:Statistics.DataScannedInBytes}'

{
    "State": "SUCCEEDED",
    "Reason": null,
    "Out": "s3://awsds-sandbox-derived/results/19893d80-17d4-45dd-b5b7-398e8de15032.csv",
    "Scanned": 0
}

AWS_PROFILE=awsds-scientist-sandbox aws athena get-query-results --query-execution-id 19893d80-17d4-45dd-b5b7-398e8de15032 --query 'ResultSet.ResultSetMetadata.ColumnInfo[].Name' --output text

trade_id        trade_date      instrument      quantity        price
```

**Four readings, and each closes something different.** The identity is the control the rest depend
on — `DataScientistAccess`, not an infrastructure role. `glue:GetTable` through the **resource link**
returns **five** columns against the lake's six: **verification (x)'s persona half is answered**, and
it agrees with the account-level reading taken as `InfrastructureAccess` on 2026-08-19 — the
`classification` gate filters `counterparty` at the account boundary and the persona inherits that,
rather than being filtered a second time.

**The query is the entry that matters.** `SUCCEEDED`, `Reason: null`, `Scanned: 0` (the table is
empty, as applied), and `ResultSetMetadata.ColumnInfo` carries the **same five names** — so the
column filter holds at the **engine**, not only in the catalog, which the metadata read alone could
not say. This is **verification (ii) closed in full**: version-4 cross-account credential vending
through `sts:SetContext` works, and **INT-11's vending half — untested since the RCP was written —
is exercised for the first time**. The output landed at
`s3://awsds-sandbox-derived/results/<id>.csv`: D19 practice (i) holding, the result inside the zone
that carries the account's CMK, the 30-day lifecycle and Stage 11's future Macie scope.

**And the shape of it is the D13 argument made visible**: the persona read a governed table while
holding no `s3:GetObject` anywhere on the lake — A5 below is the same session failing to reach the
bytes.

### A4 — the workgroup boundary, and the stage file predicted the wrong half

```
AWS_PROFILE=awsds-scientist-sandbox aws athena start-query-execution --work-group awsds-sandbox-athena --query-string "SELECT 1" --result-configuration OutputLocation=s3://awsds-sandbox-derived/scratch/hijack/ --query QueryExecutionId --output text

021ea6de-160c-4bf8-b52a-1d43a98092a4

AWS_PROFILE=awsds-scientist-sandbox aws athena get-query-execution --query-execution-id 021ea6de-160c-4bf8-b52a-1d43a98092a4 --query 'QueryExecution.ResultConfiguration.OutputLocation' --output text

s3://awsds-sandbox-derived/results/021ea6de-160c-4bf8-b52a-1d43a98092a4.csv
```

**The client asked for `scratch/hijack/` and got `results/`.** `EnforceWorkGroupConfiguration`
**overrides** the client's result location rather than refusing the query — so the deliverable's own
wording, *"a query whose client asks for a result location outside the derived prefix **fails**"*, is
**wrong about the mechanism and right about the control**, and is corrected in the stage file in this
sitting. The discriminating reading is the `OutputLocation` of the resulting execution, never an error
code (Lesson 13 again): the hijack target was chosen inside a prefix the persona **can** write, so a
failure of enforcement would have shown up as a successful write in the wrong place rather than as a
permission error that two causes could explain.

**The second half — the unenforced `primary` workgroup, which the design leaves alone deliberately
(`athena.tf`, Lesson 5) and denies from the identity plane instead:**

```
✗ AWS_PROFILE=awsds-scientist-sandbox aws athena start-query-execution --work-group primary --query-string "SELECT 1" --result-configuration OutputLocation=s3://awsds-sandbox-derived/scratch/

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the StartQueryExecution operation: You are not authorized to perform: athena:StartQueryExecution on the resource. After your AWS administrator or you have updated your permissions, please try again.
```

**Athena's own message names no policy and no mechanism** — *"You are not authorized to perform:
athena:StartQueryExecution on the resource"* — so this reading proves the denial and **not** what
produced it. What produces it is written in the policy rather than in the message: the run family is
scoped to an enumeration of two workgroup ARNs, `primary` is absent from it, and the absence is the
control (`athena.tf`'s own note). Recorded as a **weaker reading than the S3 ones below**, which do
distinguish their mechanism, rather than written up as if the two were the same kind of evidence.

### A5 — the D13 bypass is refused, but not by the deny the plan expected

```
✗ AWS_PROFILE=awsds-scientist-sandbox aws s3 ls s3://awsds-data-curated/

aws: [ERROR]: An error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-data-curated" with an explicit deny in an identity-based policy

✗ AWS_PROFILE=awsds-scientist-sandbox aws s3api get-object --bucket awsds-data-curated --key qualquer-coisa /dev/null

aws: [ERROR]: An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-data-curated" with an explicit deny in an identity-based policy
```

**The bypass is closed — and the wording says it was closed by something nobody predicted.** The
prediction, written into this sitting's plan, was the *implicit* deny of D13: the persona holds no
`s3:GetObject` on the lake and never will, so *"no resource-based policy allows"* was the expected
sentence. What came back is **`with an explicit deny in an identity-based policy`**, which means a
`Deny` statement inside `DataScientistAccess` itself matched. The next block says which one, and why
it matters far more than this proof does.

### A6 — the drop-box write, which is supposed to work, does not

```
✗ AWS_PROFILE=awsds-scientist-sandbox aws s3api put-object --bucket awsds-data-dropbox --key incoming/2026/08/19/probe-sandbox.txt --body /tmp/dropbox-probe.txt

aws: [ERROR]: An error occurred (AccessDenied) when calling the PutObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::awsds-data-dropbox/incoming/2026/08/19/probe-sandbox.txt" with an explicit deny in an identity-based policy

✗ AWS_PROFILE=awsds-scientist-sandbox aws s3api get-object --bucket awsds-data-dropbox --key incoming/2026/08/19/probe-sandbox.txt /dev/null

aws: [ERROR]: An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-data-dropbox" with an explicit deny in an identity-based policy

➜  AWS-DataScience git:(main) ✗ AWS_PROFILE=awsds-scientist-sandbox aws s3api list-objects-v2 --bucket awsds-data-dropbox --prefix incoming/

aws: [ERROR]: An error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-data-dropbox" with an explicit deny in an identity-based policy
```

**`PutObject` was DENIED, and it is the one call in this sitting that was supposed to succeed.** The
drop-box write is pass 4c's own deliverable — the identity half whose absence 6.2's correction
explains, applied on 2026-08-19 as `WriteIngestionDropBox`. It is present, it is correct, and it is
**overridden by an explicit `Deny` in the same document**, because an explicit deny beats every allow.
The read-back and the list are denied too, which is the designed asymmetry — but the asymmetry is not
what this measured, since all three verbs failed for the same reason.

### The diagnosis: `DenyControlPlaneOffVpn` fires on S3 *because* the tunnel works as designed

`DataScientistAccess` composes exactly five `Deny` statements, and four of them cannot match these
calls: `DenyIamPrincipalMutation` (iam only), `DenyMakingStorageOrImagesPublic` (no `PutObject`, no
`ListBucket`), `DenyInternetFacingCompute` (ec2 only), and `DenyTerraformStateAccess`, whose ARNs are
`awsds-*-tfstate` and `awsds-*-tfstate/*` — a pattern neither `awsds-data-curated` nor
`awsds-data-dropbox` matches, since the wildcard still requires the name to *end* in `-tfstate`. **The
fifth is `DenyControlPlaneOffVpn`: `Action *` on `Resource *`, denying whenever
`NotIpAddress aws:SourceIp` ∉ the VPN Elastic IPs AND `aws:ViaAWSService` is false.**

**The condition is met by S3 and not by Glue or Athena, and the reason is the split this project
already measured and wrote down one entry ago.** The public subnet's route table carries the two `[P]`
gateway endpoints, so tunnel traffic **splits by destination**: an S3 call leaves through the gateway
endpoint, every other API through the internet gateway wearing the Elastic IP. A request arriving at
S3 through a VPC endpoint does not present the Elastic IP in `aws:SourceIp` — the key is either absent
or carries a private address, and **either way a negated operator makes the deny fire**. *(Measured
later the same day: it is the second — present, carrying the host's private address. The controls
entry below.)* Glue and
Athena, on the same session and in the same minutes, arrive as `aws:SourceIp` = the Elastic IP and the
deny stays quiet. A2, A3 and A7 are therefore not just other proofs: **they are the control that
isolates this one to the S3 path** rather than to a broken session, an expired token or a lost tunnel.

**Why A3 wrote to `results/` anyway**, and it is the second half of the same mechanism: Athena stages
the result with the caller's credentials through a **forward access session**, where
`aws:ViaAWSService` is `true` — so the statement's own carve-out excludes it. Service-mediated S3
works; the persona's *own* S3 call does not.

**This is the two halves of the design disagreeing about a split only one of them knows about.** The
bucket policy's `DenyOutsideTrustedNetworks` carries **three** branches — `aws:SourceVpce`,
`aws:SourceIp`, `aws:PrincipalAccount` — precisely because traffic can arrive either way. The identity
policy's twin carries **one**, `aws:SourceIp`, and the comment above it argues the split-tunnel case
(step 5's `0.0.0.0/0` route) without ever reaching the gateway-endpoint case. The resource half was
written against the measured topology; the identity half was written against the intended one.

**What it costs, stated at its real width rather than at the width of the failing command.** Every
direct S3 call a persona makes from the tunnel is explicitly denied, which reaches past the drop-box:
the derived zone's own three prefix families — `results/`, `derived/$${aws:userid}/`, `scratch/` — are
granted by four statements of `DataScientistAccess` applied at 4c, and **a person cannot download
their own query result with `aws s3 cp`** under the same mechanism. That prediction is untested and is
the first thing group B should measure, because it separates "the deny is about the lake" from "the
deny is about S3".

**It is a real defect and it is not a hole in the perimeter** — the failure is closed, not open, and
nothing reached data it should not. What it breaks is a designed path (D18/D25's ingestion) and,
probably, the usability of the derived zone. **The fix is not this sitting's**: the shape is a third
condition on `DenyControlPlaneOffVpn` mirroring the bucket policy's `aws:SourceVpce` branch, and
`identity/sso/` already reads the consumer states that hold those endpoint ids — ***and the consumer
states are the wrong ones**: the controls entry below measures that every tunnel call, in either
consumer, leaves through the **VPN home's** endpoint. Read that before implementing this sentence* —
but amending a
statement that binds **six** permission sets in every governed account is a deliberate change with its
own review, and Stage 4's own warning about it (getting this wrong on a persona costs a session) is
the reason it is written down here rather than applied.

### A7 — the crawler's negative half, and the second thing the plan predicted wrongly

```
✗ AWS_PROFILE=awsds-scientist-sandbox aws glue start-crawler --name awsds-data-raw

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the StartCrawler operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: glue:StartCrawler on resource: arn:aws:glue:us-west-2:<Sandbox Account 1>:crawler/awsds-data-raw because no identity-based policy allows the glue:StartCrawler action
```

**The deliverable says this call is "denied naming the OU policy". It is not, and could not be.** The
`glue:StartCrawler` deny is `DenyCatalogMaintenanceRunsExceptMaintenanceRole` in
`awsds-org-scp-ou-data`, attached to the **Data** OU; Sandbox and Development sit under
**`Interactive`**, whose only statement is `DenyClassicNotebookInstances`. So no SCP is in the path at
all, and what refuses the call is the **absence of any `glue:Start*` allow** in the persona's own
document — *"because no identity-based policy allows"*, the implicit form. Corrected in the stage file
in this sitting. The D27 carve-out remains **unexercised in both directions** by this reading: it was
never the mechanism here.

**Two things fall out of it that are worth more than the proof itself.** The resource ARN in the
message is `arn:aws:glue:us-west-2:<Sandbox Account 1>:crawler/awsds-data-raw` — a crawler that does
**not exist**, since both crawlers live in Data Governance — and IAM still answered with an
authorization decision rather than `EntityNotFoundException`. That is **Lesson 21's fork resolved in
the good direction for this action**: `glue:StartCrawler` authorizes before it validates, so the
reading is real and not an artefact. And the *wording* is the control for the diagnosis above: the
same session, the same minute, produces an **implicit** deny from Glue and an **explicit identity**
deny from S3. Only the network path differs.

### Not done, and owed by name

**Group B — every proof above repeated in Development** — is untouched, and Lesson 31 is exactly why
it is not optional: the two consumers have their own `DataLakeSettings`, their own CMK, their own
derived bucket and their own re-grants, and a check written in one account keeps reporting `pass`
about that one. It gains one probe this sitting did not have: **the persona reading its own derived
bucket**, which decides how wide the `DenyControlPlaneOffVpn` finding is.

Then the three acts that need authorization and were deliberately not run: the maintenance pair's
**positive** half (`StartCrawler` as `awsds-data-catalog-maintenance`, still never run since pass 1),
the **explicit `restricted` grant and its revert** (four writes across two accounts), and **4e** — the
`athena:StartQueryExecution` amendment, last, through battery phase 4b. One decision is now sequenced
rather than open: **whether `sample_trades` ever gets rows**, since after 4e nothing in Data Governance
can run a query, and every verification of this stage reads column lists rather than rows.

---

## 2026-08-19 — Group A re-run by Claude's hand: every reading reproduces, and the finding's width is settled — the persona cannot read its own derived zone

*Provenance. **This entry is Claude's, and so are the commands in it** — run at the user's request in
this sitting, from the same laptop and the same tunnel, to re-validate the entry above. **The
read-only calls were run under the standing rule; the five write calls were run only after the user
authorized them explicitly, by name, in this sitting** — three of them are denied and create nothing,
which is the probe battery's shape (`aws/probes/`), and two create an Athena execution and a CSV.
**The redaction is mechanically different here and it is worth knowing which**: the account id and the
persona's e-mail were masked **at capture**, by a filter on the command's own output, so — unlike the
user's pastes above, which are redacted after the fact — the raw values never entered a file at all.
Everything else is verbatim.*

### The session it was measured in

`curl` returned the `[P]` Elastic IP and the `sandbox.internal` SOA answered, so the tunnel was the
same one; `sts:GetCallerIdentity` returned `AWSReservedSSO_DataScientistAccess_37932702010107f8`, the
same provisioned role. Neither is decoration: without both, every denial below has two explanations.

### Nine read-only readings, all identical to the entry above

`glue:GetTables` through the link (`sample_trades`), the five-column list, `s3 ls` and `get-object` on
`awsds-data-curated`, `get-object` and `list-objects-v2` on `awsds-data-dropbox` — same wording, down
to which action the message names. And **A3's and A4's original execution ids still answer**, so those
two were re-read rather than re-derived: `SUCCEEDED`, `Reason: null`, `Scanned: 0`, output at
`results/19893d80-….csv`, `ColumnInfo` five long, and the hijacked query still recorded as having
written to `results/021ea6de-….csv`.

### The measurement that was missing, and it settles the width

```
B0.1  the PERSONA lists its OWN derived bucket

aws: [ERROR]: An error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-sandbox-derived" with an explicit deny in an identity-based policy

B0.2  the PERSONA downloads its own query result

download failed: s3://awsds-sandbox-derived/results/19893d80-17d4-45dd-b5b7-398e8de15032.csv to - An error occurred (403) when calling the HeadObject operation: Forbidden
```

**The prediction the entry above left untested is now measured, and it holds.** `awsds-sandbox-derived`
carries no network perimeter of its own — only `DenyStalePresignedUrls` beside the module's TLS deny —
and `UseDerivedZoneBuckets` grants this persona `s3:ListBucket` on exactly that ARN. **So a `Deny` is
overriding an explicit `Allow`, and the only statement in the document able to do that is
`DenyControlPlaneOffVpn`.** The finding is therefore **not about the lake's buckets: it is about the S3
path**, and its cost has a shape a user would feel — *the scientist runs the query and cannot fetch the
CSV*. Athena writes the result (forward access session, `aws:ViaAWSService` true, the statement's own
carve-out); the person reading it does not.

**B0.2's `403 Forbidden` is the weaker of the two and is recorded as such**: `aws s3 cp` issues a
`HeadObject` first, and HeadObject returns no body, so the mechanism is invisible in it. The wording
that carries the finding is B0.1's.

### The five writes, re-run on explicit authorization

The three that create nothing came back **word for word** as the entry above: Athena's unnamed refusal
on `primary`, `s3:PutObject` on the drop-box key *with an explicit deny in an identity-based policy*,
and `glue:StartCrawler` *because no identity-based policy allows* — the latter again naming a crawler
ARN in an account that has none, `glue:StartCrawler` authorizing before it validates.

The two that create something were re-run as **fresh executions rather than re-reads**, which is the
point of running them at all:

| | |
|---|---|
| `ca9c2014-c92c-48f2-8973-5ea81ab323f5` | `SUCCEEDED`, `Reason: null`, `Scanned: 0`, `results/ca9c2014-….csv`, `ColumnInfo` = the same five names |
| `63d8b373-24c3-4a84-bc83-f30b59ce863f` | asked for `scratch/hijack/`, **wrote to `results/63d8b373-….csv`** |

So `EnforceWorkGroupConfiguration` overrode the client's location a **second** time, in an execution
that shares nothing with the first. Cost of the re-run: two more CSVs under the derived zone's 30-day
lifecycle. The drop-box gained nothing — the `PutObject` was denied — so there is no probe object
anywhere to clean up, in either account.

### The two controls that were NOT taken, and what they need

- **`InfrastructureAccess` listing the same bucket through the same endpoint.** This is the clean
  control: step 8.3 applied `DenyControlPlaneOffVpn` to the six personas **only**, so if that role
  succeeds where the persona fails, the deny is isolated to the persona fragment rather than to the
  bucket, the endpoint or the network. It was attempted and returned
  `Error loading SSO Token: Token for awsds does not exist` — the browser is signed into the access
  portal as the persona, which is Stage 4's own finding about consecutive sign-ins.
- **CloudTrail's `vpcEndpointId` and `sourceIPAddress`, on a denied S3 management event beside the
  Glue one.** That would measure the split directly instead of inferring it. Same blocker: the persona
  holds no `cloudtrail:LookupEvents`.

**So the diagnosis today rests on three measurements and one reading** — the Glue-implicit /
S3-explicit pair in one session, the derived-bucket denial over an explicit allow, and the
reproduction above, against an elimination over the document's five `Deny` statements. That is enough
to act on and not enough to call it measured; the two controls above are what would close the gap, and
both are one `aws sso login --sso-session awsds` away.

---

## 2026-08-19 — Pass 4d group B, in Development: every reading mirrors Sandbox, and the second role is what makes the finding a property of the DOCUMENT

*Provenance. **This entry is Claude's, and so are the commands** — run at the user's request, from the
same laptop and the same tunnel, immediately after the group-A re-run above. The read-only calls ran
under the standing rule; **the five write calls ran because the user authorized group B by name in
this sitting, with those five enumerated in the handover that preceded it** — three are denied and
create nothing, two create an Athena execution and a CSV. Identifiers were **masked at capture**, as
in the entry above, so no raw value entered a file. Everything else is verbatim.*

### Why this was repeated rather than assumed

Lesson 31, and it is not a formality here: the two consumers hold **their own** `DataLakeSettings`,
their own account CMK, their own derived bucket, their own resource links and their own four
re-grants. Nothing measured in Sandbox is evidence about Development, and this project has already
been bitten once by a check that kept reporting `pass` about the account it was written in.

### The ten readings

| | Development | against Sandbox |
|---|---|---|
| identity | `AWSReservedSSO_DataScientistAccess_93e51218b5f8bf66` | **a different role** |
| `glue:GetTables` through the link | `sample_trades` | same |
| column list | `trade_id trade_date instrument quantity price` | same — five, `counterparty` absent |
| the query `cbc25fa7-c41c-4ce6-92cd-2aa6a4767bc6` | `SUCCEEDED`, `Reason: null`, `Scanned: 0`, `s3://awsds-dev-derived/results/cbc25fa7-….csv`, `ColumnInfo` five long | same |
| the hijack `a0f29aae-d2d9-484f-be7f-98f8b37515aa` | asked `scratch/hijack/`, wrote `results/a0f29aae-….csv` | same |
| `primary` | `AccessDeniedException`, naming no policy | same |
| `s3 ls` on `awsds-data-curated` | *explicit deny in an identity-based policy* | same |
| **`s3 ls` on `awsds-dev-derived`** | *explicit deny in an identity-based policy* | same |
| `PutObject` on the drop-box | *explicit deny in an identity-based policy* | same |
| `glue:StartCrawler` | *because no identity-based policy allows*, naming a crawler ARN in an account that has none | same |

### What the repetition bought, and it is one line of the table

**The provisioned role is a different one** — `93e51218b5f8bf66` here against `37932702010107f8` in
Sandbox. One permission set, two accounts, **two distinct IAM roles**, and both fail identically. That
moves `DenyControlPlaneOffVpn`'s defect from *"something is wrong in Sandbox"* to **a property of the
document**: it reaches every account the set is provisioned into, and it will reach `Staging` at its
vend and every Sandbox unit D35 adds, with nobody having done anything. The same is true of the two
proofs that *worked*: the workgroup enforcement and the column filter hold in both, from two different
roles, which is what the pass needed and could not get from one account.

**`s3 ls` on `awsds-dev-derived` is the row that matters most.** The derived-zone consequence measured
in Sandbox reproduces here: the persona cannot list its own zone, in either consumer. The finding is
systemic across the consumer side rather than an accident of one account.

### Two verification rows close

- **(ii)** — version-4 cross-account credential vending through `sts:SetContext` now answered **in both
  consumers**, each with its own `DataLakeSettings` and its own re-grants. The RCP leaves it untouched.
- **(x)**'s exclusion half — the column filter holds at the **engine** in both accounts, read from
  `ResultSetMetadata.ColumnInfo` rather than from the catalog alone. **The explicit-grant half is still
  owed** and is one of the two authorized acts below.

### Cost, and what was left behind

Two more CSVs under `s3://awsds-dev-derived/results/`, on the zone's 30-day lifecycle. **The drop-box
gained no object in either account** — the write is denied on both sides — so there is nothing to
clean up anywhere, and `incoming/2026/08/19/` does not exist.

### Not done, and owed by name

**4d's two authorized acts remain, and both need an identity this sitting did not use**: the
maintenance pair's positive half (`StartCrawler` as `awsds-data-catalog-maintenance`, still never run
since pass 1) and the **explicit `restricted` grant with its revert** (four writes across two
accounts). Then **4e**, last, through battery phase 4b. And the two controls the entry above names as
not taken — `InfrastructureAccess` on the derived bucket, and CloudTrail's `vpcEndpointId` — which are
what would turn the `DenyControlPlaneOffVpn` diagnosis from deduced into measured. **The persona
session has now done everything it can do**, so the identity switch those controls need costs nothing
that was still needed.

---

## 2026-08-19 — The two controls, taken as the infrastructure user: the split is measured, and the proposed fix was aimed at the wrong endpoint list

*Provenance. **This entry is Claude's, and so are the commands.** Every call is read-only and ran under
the standing rule — including the two `s3api` calls fired **deliberately, so that CloudTrail would have
something to show**: the persona's denied call is an S3 *data* event and the trail carries management
events only, so the path had to be re-created by a call of the right kind rather than looked up.
Identifiers were masked at capture. Everything else is verbatim.*

### Why the identity changed, and what the change cost

Nothing that was still needed. The entry above closed with the persona session having done everything
it could do, and both controls need either `cloudtrail:LookupEvents` or a role the deny does not bind.
The user signed in as **the infrastructure user, `InfrastructureAccess`, in `Sandbox 1` and
`Development`**.

**The tunnel was confirmed up before anything else ran** — `curl checkip` returned `52.89.212.1`.
Without that check the control would have varied identity **and** route at once, and a success would
have proven nothing about which of the two mattered.

### Control 1 — the isolation holds, and the listing costs the finding its abstraction

`aws s3 ls` on `s3://awsds-sandbox-derived/` and on `s3://awsds-dev-derived/`, same tunnel, same
endpoint, `InfrastructureAccess`: **both list without error.** The bucket policy, the account CMK, the
gateway endpoint and the network are exonerated in one reading, and step 8.3 is why — it applied
`DenyControlPlaneOffVpn` to the six personas **only**.

**What the listing returned matters more than that it returned.** The objects are there:

| bucket | contents | written by |
|---|---|---|
| `awsds-sandbox-derived/results/` | 4 CSVs + 4 `.metadata` | group A (21:42, 21:45) and the re-run (22:20), local time |
| `awsds-dev-derived/results/` | 2 CSVs + 2 `.metadata` | group B (22:38) |

Every one is the output of a query **the persona itself ran**. The scientist submits the query, Athena
writes the answer into the scientist's own bucket, and the scientist cannot fetch it. That is the
defect stated the way a person meets it, rather than as a denied API call.

### Control 2 — the instrument had to change before it could answer

`cloudtrail lookup-events` over the persona's window returned the two denied `StartCrawler` calls and
**no denied S3 call at all**. That is not a gap in the trail: `aws s3 ls s3://bucket/` issues
`ListObjectsV2`, an S3 **data** event, and the Control Tower trail records management events only. The
control as the entry above named it — *"a denied S3 management event beside the Glue one"* — could not
be taken, **because the persona never made one**. The instrument was fine; the event did not exist.

So the path was measured with a call of the right kind, over the same tunnel:

| call | `sourceIPAddress` | `vpcEndpointId` |
|---|---|---|
| `ListBuckets` — S3, over the tunnel | **`10.20.160.254`** | **`vpce-0cc3e139c1167ca83`** |
| `StartCrawler` — Glue, denied, persona session | **`52.89.212.1`** | *absent* |
| `GetBucketLocation` — Athena staging a result, persona's own `sessionIssuer` | `athena.amazonaws.com` | *absent* |

`10.20.160.254` sits inside `10.20.0.0/16`, the Sandbox VPC, and is the WireGuard host's own ENI after
its NAT. `vpce-0cc3e139c1167ca83` is **Sandbox's** S3 gateway endpoint, read back from
`describe-vpc-endpoints`. And `local.vpn_egress_cidrs` is built from one thing only: one `/32` per VPN
home, from that home's `wireguard_eip_public_ip`.

**Three rows, three different claims closed.** An S3 call from the tunnel presents a private address
and an endpoint id, so `NotIpAddress aws:SourceIp` is **true** and the deny fires. The same session's
Glue call presents the Elastic IP, so the deny stays quiet and what was seen was the implicit deny —
the two are minutes apart on one tunnel and differ only in destination. And Athena's staging write is
recorded with the **service** as its origin under the persona's `sessionIssuer`, which is
`aws:ViaAWSService` being true, measured rather than argued.

### What this changes in the diagnosis above

**The mechanism is precise where it was a disjunction.** The entry above said the key "is either
absent or carries a private address, and either way a negated operator makes the deny fire". It is the
second. The conclusion was right and half the reasoning covered a case that does not occur.

**The elimination was re-done rather than carried forward**, by reading the documents instead of the
earlier entry: of the six `Deny` statements `DataScientistAccess` composes,
`DenyTerraformStateAccess` requires a name *ending* in `-tfstate`, `DenyMakingStorageOrImagesPublic`
carries a closed action list holding neither `ListBucket` nor `GetObject`, and
`DenyIamPrincipalMutation`, `DenyInternetFacingCompute` and `DenyLakeFormationAdministration` are
other services. Only `DenyControlPlaneOffVpn` — `Action *` on `Resource *` — can reach the call.
**Proved by exhaustion over the file, not remembered from the entry that first proposed it.**

**The sharpest evidence in this pass is not a measurement.** `permission-sets.tf` already carries a
`precondition` over `vpn_egress_cidrs` whose error message predicts this pass's exact symptom —
*"DenyControlPlaneOffVpn would apply cleanly and deny every call from every network for all six
personas"*. It was written against the list coming back **malformed**. Nothing in it considers the
list being well-formed and the key being irrelevant on the route the traffic takes. **The failure was
foreseen; the way it would arrive was not**, and a guard was built for the half that did not happen.

### The second finding: the fix was aimed at the wrong list

The entry above proposed the amendment and said `identity/sso/` "already reads the consumer states
that hold those endpoint ids". **The consumer endpoints are the wrong ones.**

`vpn_homes` holds exactly one row, `sandbox`. Every persona call over the tunnel — in *either*
consumer — leaves through **Sandbox's** endpoint, because that is where the host is. Development's own
`vpce-0a222aef0c577abbb` is not on that path and will not be until Stage 6 puts compute inside
Development's VPC.

**The same axis error is already in the lake's bucket policy, and there it is working by luck.**
`local.consumer_vpce_ids` is built as *each consumer's own* endpoint. The branch that actually carries
a Development persona's reach to `awsds-data-curated` is Sandbox's endpoint id — **in that list
because Sandbox is a consumer, not because it is the VPN home**. The right value is in the right list
for the wrong reason, and it stops being true the day the host moves, a second home is added, or a
consumer appears that is not a VPN home.

Lesson 10's axis question and Lesson 29's *describe-becomes-select*, arriving together: a list built
along "who consumes the lake" is being asked "what is on the network path", and today the two
intersect.

### The fix, now shaped by measurement rather than by symmetry with the bucket policy

A third condition on `DenyControlPlaneOffVpn`, its values from the **VPN homes'**
`s3_gateway_endpoint_id` — an output every `foundation/` already exports, out of the `vpn_home` remote
state `identity/sso/` already reads, so no new output and no new state read:

```hcl
condition {
  test     = "StringNotEqualsIfExists"
  variable = "aws:SourceVpce"
  values   = local.vpn_egress_vpce_ids
}
```

**`IfExists` is what holds the polarity.** On the internet-gateway path the key is absent, the
condition passes, and the deny still closes every off-VPN call — which is the statement's whole
purpose. On the endpoint path with a matching id the condition is false and the deny stands down.

**Two consequences stated rather than discovered.** It widens the carve-out to anything able to reach
Sandbox's S3 gateway endpoint — the host today, Sandbox compute after Stage 6. That is inside the
perimeter and it is still a choice. And **it covers S3 and nothing else**: the DynamoDB gateway
endpoint has the identical property and any interface endpoint presents `aws:SourceVpce` too, so the
local is plural by design rather than by accident.

**It is still not this sitting's change.** The statement binds six permission sets in every governed
account, and nothing measured here softens Stage 4's warning that getting it wrong costs a session.

### What the amendment does not promise, and this is the part to carry forward

**That the drop-box write starts working.** The explicit deny masked whatever sits under it, and by
Lesson 28 reach is an intersection: `AllowInteractiveWriterPutOnly` on the drop-box bucket is the
other half, and no call has yet got past the identity half to exercise it.

**And D13's own mechanism stays unmeasured.** The argument is that an execution role holds *no* S3
grant on a registered prefix — an **implicit** deny — and every attempt so far has been intercepted by
an explicit one. Both become measurable only after the amendment lands. **This is the pass's one
genuine regression in evidence**: a proof the stage counted on is not merely deferred, it was
overwritten by a louder failure.

### Still owed, unchanged by this sitting

4d's two authorized acts — the maintenance pair's positive half (`StartCrawler` as
`awsds-data-catalog-maintenance`, still never run since pass 1) and the explicit `restricted` grant
with its revert — then **4e**, last, through battery phase 4b.

---

## 2026-08-19 — 4d's two authorized acts: the maintenance pair's positive half has no principal at all, and the restricted grant closes its half with a control beside it

*Provenance. **This entry is Claude's, and so are the commands.** The readings ran under the standing
rule; **the three write calls — one `StartCrawler` that was denied, one `grant-permissions` and its
`revoke-permissions` — ran because the user authorized "the two authorized acts of 4d" by name in this
sitting**, and the stage file names both. Identifiers were masked at capture. Everything else is
verbatim.*

### The reconnaissance came first, and it is what turned act 1 into a finding

Neither act was attempted before its baseline was read, and in act 1's case the baseline is the whole
result. Four readings, all before any write: the maintenance role's **trust policy**, the two
crawlers' configuration, the SCP statement the stage names, and the blast radius of a crawl that might
succeed (`s3://awsds-data-raw` empty, `raw` holding zero tables — so a run would have catalogued
nothing).

### Act 1, the negative half — and D27's carve-out is exercised for the first time

`glue:StartCrawler` on `awsds-data-raw`, as **`InfrastructureAccess` in `Data Governance`**, an account
in the **`Data`** OU:

```
An error occurred (AccessDeniedException) when calling the StartCrawler operation:
User: arn:aws:sts::<Data Governance Account>:assumed-role/AWSReservedSSO_InfrastructureAccess_ba1899ccb658ab35/<the infrastructure user>
is not authorized to perform: glue:StartCrawler on resource:
arn:aws:glue:us-west-2:<Data Governance Account>:crawler/awsds-data-raw
with an explicit deny in a service control policy: <the awsds-org-scp-ou-data policy ARN>
```

`get-crawler` in the same session returned `READY`, so the session was alive and Glue reachable — the
control that separates a deny from a broken session.

**This is the first time `DenyCatalogMaintenanceRunsExceptMaintenanceRole` has ever fired.** Stage 1c
recorded it among the statements *attached but unexercised*; group A then found that the **persona**
half could not exercise it either, because the personas sit in `Interactive` and are refused earlier by
the absence of any `glue:Start*` allow. `InfrastructureAccess` in the `Data` OU is the principal that
reaches the statement, and the wording — *service control policy*, not identity-based — is what proves
which layer answered.

### Act 1's real result: the positive half cannot be produced by any principal that exists

The stage asks for "the raw crawler runs as `awsds-data-catalog-maintenance`". **It cannot, and the
reason is three readings that close on each other:**

| reading | what it says |
|---|---|
| the SCP's condition | `ArnNotEquals aws:PrincipalArn` = the maintenance role, `BoolIfExists aws:PrincipalIsAWSService false` — so **only** that role, or a service principal, may call `StartCrawler` |
| the role's trust policy | one statement, `GlueServiceOnly`: `Principal.Service = glue.amazonaws.com`, conditioned on `aws:SourceAccount`. **No human, and no other service's role, can assume it** |
| the crawlers | `Schedule: null` on both; `list-triggers` and `list-workflows` both return `[]` |

So the role is an **execution** role, never an identity anyone becomes: Glue assumes it to *perform* a
crawl, after `StartCrawler` has already been authorized against somebody else. And the only caller the
SCP would accept is Glue's own scheduler, reaching the API as a service principal — which needs a
`Schedule`, and neither crawler has one.

**Nothing in this estate can start these crawlers.** That is **Lesson 22** in its exact shape — a
control whose principal the harness cannot produce is verified by reading rather than by attempting —
and the positive half is therefore closed by the table above, not by a run.

### What that costs, and it is not confined to a deliverable

**D18/D25's ingestion path is `persona PutObject → crawler catalogues → data appears`, and both halves
are now broken, for unrelated reasons.** The write is refused by `DenyControlPlaneOffVpn` (the entries
above); the catalogue step has no invocation path at all. **The two are independent: amending the VPN
statement does not make a crawler run**, and adding a schedule does not make the drop-box writable.
Anyone reading only one of these entries would fix half of a path and believe it whole.

### It is not a defect in the SCP or in the trust policy — it is a decision nobody took

Both documents are coherent with a design in which crawlers run **on a schedule** and no person ever
triggers one; that is a reasonable reading of D27, and it is arguably the stronger control. What is
missing is the schedule itself. Pass 1 created the two crawlers deliberately **never-run**, and nothing
since has said when they should run — so **`Schedule` is an open design decision surfaced by this
attempt**: whether it exists at all, at what frequency, and whether the drop-box's cadence differs from
`raw`'s, given that the drop-box is an ingestion path and `raw` is a zone. Recorded here rather than
answered, because it is the stage's call and not this sitting's. *(Refined in the review entry below:
half of it **was** decided — `maintenance.tf` rejects a standing schedule on cost, `DL-3` checks the
rejection, and the chosen trigger was "on-demand". The untaken half is the DEMANDER.)*

### Act 2 — the explicit `restricted` grant, with a live control beside it

Granted in Data Governance, mirroring the shape of the four grants already there — `LFTagPolicy`,
`ResourceType: TABLE`, expression `classification=restricted AND layer IN (curated, raw)`,
`DESCRIBE, SELECT` with the grant option — **to the Sandbox account only**:

| reading of `curated.sample_trades` | Sandbox | Development | Data Governance |
|---|---|---|---|
| before | 5 columns | 5 columns | **6** |
| **after the grant** | **6 — `counterparty` present** | **5** | 6 |
| after the revoke | 5 | 5 | 6 |

**Granting in one account rather than two is what makes this a measurement instead of an
observation.** Development was read in the same minute, through the same tunnel, as the same kind of
principal, and did not move. Time, catalog caching, a stale session and a coincidental propagation are
all excluded by that column — none of which a two-account grant could have excluded. The stage
budgeted four writes here; two were enough, and the two that were dropped were the ones that would have
destroyed the control.

**This closes the classification pair's second half and verification (x)'s explicit-grant half.** The
absent half was measured at the **account/administrator** grain (the share's `classification` gate
filtering `counterparty` at the boundary), and this is measured at the same grain, so the pair is
symmetric.

**The limit, stated rather than left implicit:** this is not measured at the **persona** grain. A
persona seeing `counterparty` would need a second grant, inside the consumer account, from that
account's own administrator to the persona — `consumer-data`'s re-grants scope the persona to
`classification IN (public, internal)` and were not touched. What is proven is that the boundary gate
opens and closes on the explicit grant; what is not proven is the consumer-side re-grant on top of it.

### The state left behind: none

The revoke was verified three ways rather than assumed: the two column lists back at five, the
`LFTagPolicy` grant count back at **4** (2 `DATABASE`, 2 `TABLE`), and **zero** permissions anywhere
carrying `restricted` in an expression. `./aws/datalake.py` then read **0 check(s) FAILED**. The
`FAILED` lines against persona profiles in its header are absent SSO sessions, not lake findings —
Lesson 25's neighbourhood, and worth naming so a later reader does not chase them.

**The grant register in `docs/AWS_STATE.md` is unchanged and correctly so**: 13 rows / 24 triples
describe the applied state, and the applied state is what it was before this entry.

### What 4d still owes

**4e** — `athena:StartQueryExecution` added to `DenyUserCompute` in `awsds-org-scp-ou-data`, last,
through battery phase 4b. Everything else in 4d is now either measured or recorded as unmeasurable
with its reason.

---

## 2026-08-20 — The sample rows: the one-way door was walled shut all along, and unbricking it delivers Stage 9's write ceiling early

*Provenance. **This entry is Claude's, and so are the commands.** The readings ran under the standing
rule. The writes ran on two authorizations, each given by name in this sitting: the **INSERT** by the
user's answer to the sample-row question — the first option, rows before 4e, chosen against the
recommendation with both stated costs in view — and the **Terraform apply** by the user's explicit
"autorizo o apply das mudanças", given after the finding was reported and with the diff described.
Identifiers were masked at capture. Everything else is verbatim.*

### The decision, and what neither branch knew

The stage's 4.1 callout posed the one-way door: load rows through Athena in this account *before*
4.3's amendment closes that path, or leave the table empty and let Stage 9's producer write the first
real rows. The recommendation was the second; the user took the first. **Both options, as posed,
described a door that was not there** — and that is the finding, not a detail of it.

### The attempt (2026-08-19, 23:35 local): DENIED, and the principal in the error is nobody at the keyboard

A 12-row `INSERT INTO curated.sample_trades` through the `primary` workgroup, as
`InfrastructureAccess` in `Data Governance`. Athena accepted it and failed it in 1.3 s:

```
PERMISSION_DENIED: User: arn:aws:sts::<Data Governance Account>:assumed-role/awsds-data-lf-registration/AWSLF-00-AT-<Data Governance Account>-yqjVkpVOQG
is not authorized to perform: kms:GenerateDataKey on resource: <the account data CMK>
because no identity-based policy allows the kms:GenerateDataKey action (Service: S3, Status Code: 403 …)
```

The denied principal is a **vended session of `awsds-data-lf-registration`** — the `AWSLF-…-AT-…`
session Lake Formation mints for Athena to touch a registered location. The caller's own permissions
never entered into it: the write died at the vending ceiling.

**Nothing was left behind, verified rather than assumed**: the table's `metadata_location` still read
the original `00000-…` (no Iceberg commit), the table prefix held only the creation-time metadata
JSON, and `athena-results/` in the artifacts bucket was empty.

### The reconnaissance: three files, three spellings, and the mechanism side was right again

| where | what it said |
|---|---|
| the role's live policy | **one** inline policy, `registered-locations-read`: `s3:GetObject`+`ListBucket` on the two registered locations, `kms:Decrypt`. No write action of any kind |
| the slice's `.tf` comment | *"READ-side only today: the governed WRITE arrives at Stage 9, which amends this policy in the same slice (its step 2)"* — deliberate, documented |
| Stage 9's file | **silent** — steps 2.1–2.4 grant, regrant and prove, and none of them amends this policy. The promise existed only at the promising end |
| Stage 5's file (item 3, 4.1) | *"the only way to put rows in it from inside this account is Athena, which is exactly what the next item closes"* — a door asserted open that was never built |

The key policy was checked and exonerated: `EnableIamPolicyDelegationInThisAccount` gives the account
root `kms:*`, so IAM delegation works inside Data Governance and the missing half was **IAM-side
only** — one statement, one file, one account.

**This is Lesson 34, and the user's choice is what made it cheap.** Nothing had ever exercised the
governed write, so all three spellings survived (Lesson 20's mirror — an unexercised allow-path is
exactly as unmeasured as an unexercised deny). Left alone, the wall stood until Stage 9's 2.4 — a
cross-account Glue job, with the share, the job role and two keys all on the suspect list when it
failed. The rows-now decision hit it with one account, one role, one key.

### The fix: a second inline policy, because the ceiling is not a grant

Authored in `data-governance/data/lakeformation.tf` as **pure addition** —
`registered-locations-write`, beside the read policy rather than inside it, so the diff adds, the
revert deletes one thing, and each policy's name stays true:

- `S3WriteRegisteredLocations` — `s3:PutObject`, `s3:DeleteObject`, **object ARNs only**, on the two
  registered prefixes;
- `KmsGenerateDataKey` — the exact action the denial named.

`s3:DeleteObject` is the one action **reasoned rather than measured**, and the code says so: engine
failure-path cleanup and Iceberg maintenance delete data files, and a put-only ceiling strands every
failed commit where no engine can remove it. The role's description now says "reads and writes". The
comment carries the history and the frame that matters: **this policy is the vending ceiling for every
governed access to the two locations, from any account** — widening it widens a ceiling, and the LF
grants stay the per-principal gate underneath. The slice README gained the two Sid rows in the same
sitting, and the read row's "write arrives at Stage 9" sentence is preserved struck-through with its
correction.

### The apply, inside the standing discipline

`terraform plan`: **`1 to add, 1 to change, 0 to destroy`** — the add the new policy, the change read
in full and confirmed to be the role's **description string alone**. Applied from the saved plan file;
re-plan **`No changes`**. Then the read-backs the slice's own rule demands after any apply:
`GetDataLakeSettings` returned one admin, `CROSS_ACCOUNT_VERSION: 4`, `SET_CONTEXT: TRUE`, both
default-permission lists `[]` — **the DL-5/INT-11 hazard did not fire** — and the role listed both
policies with the write statements exactly as authored.

### The load, and its verification chain

The identical 12-row INSERT, re-run: **`SUCCEEDED`, 1 947 ms.** Then, each reading a different claim:

| reading | result |
|---|---|
| `SELECT count(*), count(DISTINCT counterparty)` | **12** rows, **4** counterparties |
| `metadata_location` | moved `00000-…` → `00001-…` — a real Iceberg commit, not a file drop |
| the table prefix | one parquet data file (1 416 B) + manifest, manifest-list and snapshot avros |
| `./aws/datalake.py` | **0 check(s) FAILED** |

The rows are synthetic and obviously fictitious — four invented counterparties over five instruments
and six trade dates in 2026-08 — with enough variety that Stage 11's row filters have something real
to discriminate on.

### What this settles, and where it was written

- **Stage 5 item 3 / 4.1**: corrected in place — the premise was false, the decision and outcome are
  recorded, and the one-way door **now exists for real**: 4e closes in-account Athena while the write
  ceiling stays, because Stage 9's engine sits in Production and never calls Athena here.
- **Stage 9 §2**: a dated callout where the amendment would have been owed — 2.4 rides this same role,
  nothing there needs to touch the policy now, and a future `AWSLF` denial on these actions means the
  ceiling *regressed*, not that it was never built.
- **Stage 11**: the row-proof's dependency on Stage 9 is **lifted**, with the surviving caveat named —
  twelve synthetic rows prove the filter, not production shape or volume.
- **Lesson 34** (`lessons.md`), the `AWS_STATE.md` lake row, and the slice README — one copy each.

### What was left behind

12 synthetic rows in `curated.sample_trades`; **three objects** under
`awsds-data-artifacts/athena-results/` — the count query's CSV with its `.metadata`, and the
successful INSERT's own `.metadata` *(corrected by listing in the review entry below; this line first
said "the count query's CSV")*; the failed execution id and the two successful ones, in Athena's
45-day history. No object anywhere else.

### Still owed

**4e**, unchanged and now honest — there is finally an in-account Athena door to close — then pass 6.

---

## 2026-08-20 — The sitting reviewed: three log corrections, a drift the INSERT left behind, the 4d amendments authored but not applied, and the session's command reference

*Provenance. **This entry is Claude's, at the user's request** — a review sitting. **No AWS write ran**:
every `aws` call was a read, and the Terraform work is AUTHORING plus read-only `plan`s — nothing was
applied. One tooling note so the record reads honestly (Lesson 30's spirit): several commands in this
sitting and the previous one were re-issued after a local harness permission-classifier returned
transient errors of its own; no AWS call was affected, and a repeated invocation in this record is that,
not a retry against AWS.*

### The audit: the log against the session, three corrections

- **"The eight readings" → "The ten readings"** (group B's section header). The table under it has ten
  rows and the index already said ten; the header was the copy that drifted.
- **Entry 23's leftover line said "the count query's CSV"; the listing says three objects** — the count
  query's CSV *and its `.metadata`*, plus the successful INSERT's own `.metadata`. Corrected in place
  with the correction marked. The miss is the usual one: the line was written from intent, the listing
  was taken afterwards.
- **Entry 22's "a decision nobody took" was half wrong, and the code knew better.** `maintenance.tf`'s
  own comment — re-read this sitting — rejects a standing schedule **on cost** (DPU-hour, 10-minute
  billed minimum, cron-always out-costing the storage it catalogs), has `DL-3` check that rejection,
  and names the chosen trigger: *"on-demand, before a pickup"*. What 4d actually measured is narrower
  and sharper: **on-demand has no demander.** Entry 22 carries a pointer; open question 19, the stage
  bullet and `AWS_STATE.md` are refined — and the question's live candidate was **already in the
  stage** as verification (iv)'s event shape (S3 → EventBridge → Glue workflow), now to be measured
  against the SCP's service guard rather than assumed past it.

### A finding the review itself produced: the INSERT left Terraform drift on the sample table

The first lake-slice `plan` of this sitting read `1 to change` — **not** the authored change:
`aws_glue_catalog_table.sample_trades`. The first Iceberg commit stamped
`iceberg.field.{id,current,optional}` onto every column of the **live** table — the Glue columns are
the engine's mirror of its own metadata, re-stamped at each commit — and Terraform, whose config
declares bare columns, wanted to **strip them**: permanent drift, dirtying every future plan, and an
apply the next commit would undo. **Lesson 23 exactly** (a managed service owns its artifacts'
packing). Authored: `lifecycle { ignore_changes = [storage_descriptor[0].columns] }` with the argument
in the comment — Terraform keeps the table's existence, location and format; schema *evolution* goes
through the engine, which is how an Iceberg table changes anyway. The slice then plans **`No
changes`**.

### The 4d amendments: AUTHORED, planned, and deliberately not applied

**`identity/sso/` — the third condition on `DenyControlPlaneOffVpn`** (`policies-shared.tf`, values in
`locals.tf`): `StringNotEqualsIfExists aws:SourceVpce` over the **VPN homes'** gateway endpoints — both
of each home's, S3 and DynamoDB, one mechanism (any service with a gateway endpoint on the home's route
table takes that path). `IfExists` holds the polarity: off-VPN traffic carries no vpce key, the test
passes, the deny still fires. The comment block now argues **three** ANDed conditions and carries the
measured history. Beside it, **a second plan-time guard** in `permission-sets.tf` — the existing one
predicted the right symptom for the wrong cause (a malformed address list), and the new one guards the
measured cause, naming its own asymmetry: a bad vpce entry is not a lockout but a silent **regression**
to the 4d defect.

The plan, read in full before being left unapplied: **`0 to add, 6 to change, 0 to destroy`** — the six
persona inline policies and nothing else, each gaining exactly the one condition with the two Sandbox
endpoint ids; both preconditions passed; the saved plan file sits in the session scratchpad.

**`data-governance/data/` — the trusted list rebuilt on the right axis**: `trusted_vpce_ids =
sort(distinct(consumer ∪ vpn_home))`, consumed by `DenyOutsideTrustedNetworks`. **It renders
identically today** — the slice plans `No changes` — because the single home is also a consumer; the
line exists so that stops being load-bearing (Lesson 33's second finding). And `maintenance.tf`'s
crawler comment now carries the demander finding beside its own cost argument.

**Why not applied, said plainly**: the statement binds six permission sets in every governed account,
and this sitting's authorization was for review and propagation. **The apply is its own sitting**, and
its sequence is already written into the stage: apply → `VP-7` read-back → the two unblocked proofs
(the drop-box `PutObject`, which should now meet `AllowInteractiveWriterPutOnly`; the pandas negative,
which should finally return D13's **implicit** deny) → then 4e, still last. **For the crawler demander,
no Terraform was authored, deliberately**: open question 19 is an undecided design input, and authoring
a `Schedule` or an event pipe would be inventing the decision it asks for.

### The session's AWS CLI, as a debugging reference

Every command family this session used, with what it was *for* and what it *does* — the readings live
verbatim in the entries above; this is the map. All reads unless marked.

| Command | Why it was run | What it does, and what to read |
|---|---|---|
| `aws sts get-caller-identity` | First call of every episode: which principal, which account | STS echoes `Account`/`Arn`/`UserId` of the active credentials. Every later error is relative to this answer |
| `curl https://checkip.amazonaws.com` | Vary identity, not route: prove the tunnel before any control | Returns the public IP the world sees. The `[P]` Elastic IP = full tunnel up; anything else = down or split. No AWS auth involved |
| `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=<svc>.amazonaws.com --start-time …` | Measure which network path a call took, after the fact | Reads 90 days of **management** events. `CloudTrailEvent` is a JSON string — `jq 'fromjson'` — holding `sourceIPAddress` and `vpcEndpointId`. **Data events (`GetObject`, `ListObjectsV2`) are NOT here**: a missing event is instrument scope, not proof the call never happened |
| `aws s3api list-buckets` / `get-bucket-location` | Re-create a denied data call's path with a call the trail records | S3 **management** calls — same wire, same endpoint split, but CloudTrail-visible. The pair that measured `10.20.160.254` + the vpce id |
| `aws ec2 describe-vpc-endpoints --filters Name=vpc-endpoint-type,Values=Gateway` | Turn a `vpce-…` id from CloudTrail into a name | Lists endpoints with `ServiceName`/`State`. What said `vpce-0cc3…` is Sandbox's S3 gateway |
| `aws ec2 describe-vpcs` | Place a private source address | The VPC CIDRs; `10.20.160.254 ∈ 10.20.0.0/16` is what identified the WireGuard host's ENI behind the NAT |
| `aws iam get-role --role-name X` | Who can *become* the role — act 1's decisive read | Returns the **trust policy** (`AssumeRolePolicyDocument`). `GlueServiceOnly` here is what closed the positive half by reading (Lesson 22) |
| `aws iam list-role-policies` / `get-role-policy` | The identity half of a permission (Lesson 28) | Inline policy names, then the document. What proved the vending ceiling read-only — and, after the fix, read back the write half verbatim |
| `aws kms get-key-policy --key-id … --policy-name default` | The resource half of the same permission | The key policy's statements. `EnableIamPolicyDelegationInThisAccount` (root, `kms:*`) is what proved the fix needed one side only |
| `aws glue get-crawler --name X` | Can anything run it, has anything ever | `State`, `Schedule`, `LastCrawl`. `Schedule: null` + `LastCrawl: null` is "never, and the scheduler never will" |
| `aws glue list-triggers` / `list-workflows` | The invocation paths that are not the scheduler | Both `[]` = the crawler has no demander at all |
| `aws glue start-crawler --name X` *(write — denied)* | The probe whose **denial wording names the layer** | *"explicit deny in a **service control policy**"* vs *"…identity-based policy"* vs implicit. Lesson 21: Glue authorizes before validating, so the denial arrives even for a crawler that does not exist |
| `aws glue get-table --query 'Table.StorageDescriptor.Columns[].Name'` | The classification boundary, read at the engine's input | The LF-filtered column list. Three distinguishable states: 5 columns (gate holding), 6 (gate open), error (share broken) — Lesson 13's requirement |
| `aws glue get-table --query 'Table.Parameters.metadata_location'` | Did Iceberg **commit**, or only stage files | The pointer moves (`00000→00001`) only on a successful commit. Distinguishes a real write from debris |
| `aws lakeformation get-data-lake-settings` | The DL-5 bracket — after **every** apply of the owning slice | `DataLakeAdmins`, `Parameters` (`CROSS_ACCOUNT_VERSION`/`SET_CONTEXT`), both `Create*DefaultPermissions` — the reset is silent, so it is read, never assumed |
| `aws lakeformation list-permissions` | The applied grants, from the API rather than the code | Ground truth for the register: principal, resource kind, `Expression`, `Permissions`, `PermissionsWithGrantOption`. Also the source the grant's own shape was mirrored from |
| `aws lakeformation grant-permissions` / `revoke-permissions` *(writes — authorized)* | The explicit `restricted` grant and its revert | `--principal DataLakePrincipalIdentifier=<account>` + `--resource '{"LFTagPolicy":{"CatalogId","ResourceType","Expression"}}'` + the two permission lists. **Mirror the shape `list-permissions` returns; never compose from memory** |
| `aws athena list-work-groups` / `get-work-group` | Where results go, and who decides | `EnforceWorkGroupConfiguration` + `ResultConfiguration.OutputLocation`. `primary` enforces nothing, so the client must supply the location |
| `aws athena start-query-execution --work-group … --query-execution-context … --result-configuration OutputLocation=…` *(write — authorized)* | Run the INSERT / the count | Returns only the execution id. Nothing about success |
| `aws athena get-query-execution` | **The debugging read of the session** | `Status.State` and `Status.StateChangeReason` — the reason carries the denied **principal** and **action** verbatim. The `AWSLF-00-AT-…` session name in it is what moved the diagnosis from "my permissions" to "the vending ceiling" |
| `aws athena get-query-results` | The rows themselves | `ResultSet.Rows[].Data[].VarCharValue`, header row first. The `count(*) = 12` proof |
| `aws s3 ls s3://… [--recursive]` | Footprint, orphans, and the isolation control | Issues `ListBucket`/`ListObjectsV2` — a **data** event. On a denial, the wording (which policy kind, explicit vs implicit) is the evidence |
| `terraform plan -detailed-exitcode -out=<file>` → `show <file>` → `apply <file>` → `plan` | The change discipline, end to end | Plan once and save; **read the `~` in full** (the description-only change was confirmed at `show`); apply exactly the reviewed file; re-plan to `No changes` as the closing bracket |
| `./aws/datalake.py` | The lake battery, after anything touches the lake | `0 check(s) FAILED` is the line; per-profile `FAILED` headers are absent SSO sessions, not findings |

### Where this sitting wrote

The stage file (debt items 1-2, the Status row, the pass-4 row), open questions **19** (refined) and
**8** (informed, not closed), `AWS_STATE.md` (both §C rows), `GOVERNANCE.md` (the artifacts bucket's
incidental writer), `maintenance.tf` + `catalog.tf` + the four amendment files, and the three log
corrections above. `terraform fmt` clean on every touched file; the identifier gate reads 385 files,
none.

### Still owed, in order

1. **The amendment apply** (`identity/sso`, `0/6/0`) — its own sitting, then the two unblocked proofs;
2. **4e**, last, through battery phase 4b;
3. **pass 6** (Security Hub);
4. open question **19** — the demander — decided by the user, with verification (iv) as the live
   candidate.

## 2026-08-20 — The amendment applied, and the four proofs it was blocking: the deny stands down, D13's mechanism is finally its own reason, and the drop-box is put-only in three directions

*Provenance. **This entry is Claude's, and so are the commands.** **Three writes ran, each authorized in
its own sitting**: the `terraform apply` of the amendment ("pode aplicar a emenda"), and the drop-box
`PutObject` and `DeleteObject` probes ("pode executar"). Everything else is a read. Identifiers are
masked in the usual shape — an account id by the account's **name** in angle brackets, the e-mail inside
a role ARN by **the persona's role**; the readings are otherwise verbatim.*

### The apply, and the guard that fired on the second try

The saved plan from the review sitting (`0 to add, 6 to change, 0 to destroy`) was applied from
`terraform-live/identity/sso` as the **infrastructure user**, `InfrastructureAccess`, in `Management`.
It succeeded. A second invocation of the same file was **refused — "Saved plan is stale"** — which is
Recipe D's guard doing exactly its job: a saved plan is spent once, and the refusal is the mechanism
that stops a re-run from applying a world that has moved. Re-plan: **`No changes`**.

**The read-back was taken on both provisioned roles, not on the document.** The defect was a property of
the shared fragment, so the fix is only proven where the fragment lands — `AWSReservedSSO_DataScientistAccess_…07f8` in
`Sandbox 1` and `…bf66` in `Development`, the same two roles that had failed identically in groups A and
B. Both now carry three conditions:

```json
{ "BoolIfExists":            { "aws:ViaAWSService": "false" },
  "NotIpAddress":            { "aws:SourceIp": "52.89.212.1/32" },
  "StringNotEqualsIfExists": { "aws:SourceVpce": ["vpce-0a215b90df70b23c3", "vpce-0cc3e139c1167ca83"] } }
```

`./aws/vpn.py` → **all checks passed**. **`VP-7` passes in both directions** — the fragment is on all six
persona sets, and **absent from `InfrastructureAccess`** — which is the half that keeps the recovery
path open and would have been the expensive thing to get wrong.

### The proofs, taken as the persona

The user signed in as the **data-scientist persona**, `DataScientistAccess`, in `Sandbox 1` and
`Development`. `curl checkip` → `52.89.212.1` first, so identity varied and route did not.

**The before/after, on the one call that diagnosed the defect.** `s3api list-buckets` is what the
previous sitting caught in CloudTrail arriving with `aws:SourceVpce` and a private address. Re-run now:

```
not authorized to perform: s3:ListAllMyBuckets
because no identity-based policy allows the s3:ListAllMyBuckets action
```

**Explicit deny in an identity-based policy → implicit.** Same call, same role, same tunnel, one
variable changed. Nothing else in this stage measures the fix that directly.

**The contrast pair — one action, two buckets, one session.** This is what separates *"S3 is blocked"*
from *"this bucket is not granted"*, and the two were indistinguishable while the deny sat on top:

| `s3api get-bucket-location` on | `Sandbox 1` | `Development` |
|---|---|---|
| `awsds-<env>-derived` | **`us-west-2`** | **`us-west-2`** |
| `awsds-data-curated` | implicit deny | implicit deny |

`GetBucketLocation` was chosen over `ListObjectsV2` for the same reason as last sitting: it is a
**management** event, so the trail will carry it. The instrument's scope is a standing constraint here,
not a one-off.

**D13's mechanism, closed.** The direct S3 path to a registered location is refused **because nothing
grants it** — not because an unrelated rule intervened:

```
s3:ListBucket on "arn:aws:s3:::awsds-data-curated"
because no identity-based policy allows the s3:ListBucket action
```

Both accounts, identical wording, so the property belongs to the design and not to an accident of one
account. While the explicit deny was in the way, this reading and a broken-share reading produced the
same output — **Lesson 13 in its live form**, and the reason the amendment had to land before the claim
could be made at all.

### The drop-box: `PutObject` lands, and the success response carries the third half

`s3api put-object` on `awsds-data-dropbox/incoming/2026/08/20/probe-4d-sandbox.txt`, 38 bytes, fixed
size **deliberately** — a stdin stream of unknown length would have gone multipart, and the identity
half grants `s3:PutObject` with no multipart companion, so the probe would have failed for a reason that
was not the one under test. It succeeded, and returned:

```
ServerSideEncryption: aws:kms
SSEKMSKeyId:          arn:aws:kms:us-west-2:<the lake account>:key/31e29a7d-…
BucketKeyEnabled:     true
VersionId:            FdI4Gv5zaoOYBH_SaVIpCdD7Pv37GfNm
```

**`AllowInteractiveWriterPutOnly` moves from attached to exercised** — Lesson 20 discharged for that
statement, and the identity half authored in 4c delivered.

**The finding: on an encrypted write path, Lesson 28's intersection has three terms, not two.** Three
policies in two accounts had to agree at once — the identity half (`WriteIngestionDropBox`), the
resource half (`AllowInteractiveWriterPutOnly`, `ArnLike` over both consumer accounts' reserved-SSO
pattern), and **the key policy** of the lake CMK meeting `UseLakeDataKeyViaS3`, each side carrying the
`ViaService = s3` scope that bounds the other. The third term is invisible in the failure taxonomy the
stage has been using — a missing key policy surfaces as a **KMS** error, which is precisely the shape
yesterday's INSERT failure took. It is visible here only because a *successful* `PutObject` echoes
`SSEKMSKeyId`. **Lesson 28's wording is owed an amendment**: two halves is the identity/resource case;
encryption adds a third, and the success response is where you read it.

**Put-only, measured in three directions.** All three refusals are implicit — absence of grant, the same
reason as D13's:

| the persona attempts | result |
|---|---|
| `PutObject` | **succeeds** |
| `GetObject` on the object it just wrote | implicit deny |
| `ListObjectsV2` on `incoming/` | implicit deny |
| `DeleteObject` on its own object | implicit deny |

Write and lose sight of it. **D18's refusal of an exchange bucket is now a construction, not a
convention** — and the delete probe is what makes that claim complete, since a writer that can retract
is a writer that can launder.

The `Development` leg was **not** run, deliberately: the resource half is an `ArnLike` pattern covering
both accounts and both provisioned roles were already read back above, so a second uncollectable object
would have bought weaker evidence than what the read-back already gives.

### The residue, declared rather than discovered later

**The probe object stays.** Versioned, under the lake CMK, and **no principal in the current design can
collect it**: the pickup is `awsds-prod-job-exec`, a Stage 9 object that does not exist. This is the
expected consequence of the drop-box being complete before its consumer, not stray debris — but
undeclared it becomes a phantom finding in some later snapshot, so `AWS_STATE.md` is owed an `EXC` row
naming the object and the stage that removes it.

### New to the session's command reference

The families below join the table in the entry above; the rest were already there.

| Command | Why it was run | What it does, and what to read |
|---|---|---|
| `aws s3api put-object --body <file>` *(write — authorized)* | The 4c deliverable, unexercised until now | Single `PutObject`; **use a fixed-size file, never stdin**, or the CLI goes multipart and fails on a permission that is not under test. On success read `SSEKMSKeyId` — it is the only place the **key** half of the intersection is visible |
| `aws s3api get-object` / `delete-object` *(delete is a write — authorized)* | The put-only asymmetry, all three directions | Each returns the denial wording that names the layer. A probe expected to be **denied** is still a write API and is authorized as one |
| `aws s3api get-bucket-location` on a granted **and** a non-granted bucket | Isolate "the network is blocked" from "this bucket is not granted" | One action, two resources, one session. The contrast is the control; either reading alone is ambiguous |
| `aws iam get-role-policy` on the **provisioned** role, not the permission set | Prove a shared fragment where it actually lands | A permission set is a template; the role in each account is the enforced object. Two accounts failed identically, so two read-backs are what closes it |

### What this closes, and what is left

Closed: the Lesson 33 fix, **proven** rather than authored; `VP-7` both halves; **D13's mechanism**;
`AllowInteractiveWriterPutOnly`; the drop-box asymmetry. Still owed, in order: **4e** (the SCP
amendment, last, through battery phase 4b — the in-account Athena door now genuinely exists to close),
**pass 6** (Security Hub), and open question **19**, the crawler demander, which is the user's decision.

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
