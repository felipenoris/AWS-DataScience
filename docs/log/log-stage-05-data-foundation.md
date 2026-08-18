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

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
