# data-governance/data — the governed lake, layer `[P]`

The Stage 5 slice ([stage file](../../../docs/plan/stages/stage-05-data-foundation.md); the
governance model's one copy is [`docs/GOVERNANCE.md`](../../../docs/GOVERNANCE.md)). Applied as
`awsds-infra-data`. **`./aws/datalake.py` `DL-5` brackets every apply of this slice** — read it
before and after; a reset `CROSS_ACCOUNT_VERSION` fails every share silently, days later (INT-11).

What lands here by pass:

| Pass | Content |
|---|---|
| 1 (this authoring) | the `zn-lab` CMK; the five buckets with the perimeter and drop-box statements; the settings trio (admins + parameters + emptied defaults, **before any database**); registrations + the LF-Tag ontology; databases `raw`/`curated`/`dropbox`; the sample Iceberg table with its `restricted` column; the maintenance role, its LF grants, two on-demand crawlers, the compaction optimizer |
| 2 | step 6 — the consumer TBAC grants (D13 made real) |
| 3 | step 7 — the two cross-account shares + the INT-11 after-reading |

## The first apply is two steps, and that is not a preference

`aws_lakeformation_data_lake_settings` must clear the two `IAM_ALLOWED_PRINCIPALS` defaults **before any
database exists** — they act at creation time — and **the plan cannot prove it does** (both blocks are
Computed; an explicitly empty list is not expressible in `aws ~> 6.60`). So:

```bash
AWS_PROFILE=awsds-infra-data terraform -chdir=terraform-live/data-governance/data apply -target=aws_lakeformation_data_lake_settings.this
```

then `./aws/datalake.py` (`DL-5` parameters, `DL-6` defaults) — and only then the full apply. If `DL-6`
still names `IAM_ALLOWED_PRINCIPALS`, revoke and re-read first. The reasoning is in `lakeformation.tf`
beside the resource and in the stage file's 5.2 callout.

Every bucket here is **undeletable** while the Data OU SCP is attached — names are permanent.
Grants applied from this slice are registered in `docs/AWS_STATE.md` §"Lake Formation grant
register", one row per triple, in the same sitting.
