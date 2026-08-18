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

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
