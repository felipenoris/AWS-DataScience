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

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
