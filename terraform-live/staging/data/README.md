# staging/data — Staging's data platform, layer `[P]`

Stage 9 step 4.1, applied 2026-10-22: [`production/data/`](../../production/data/README.md)'s
shape without the governed write. Staging reads the governed lake through the LF-Tag share Sandbox holds,
`DESCRIBE` and `SELECT` alone, writes only to its own catalog, buckets and key, and copies nothing
(decision 3). The rows below are the differences; every other row of Production's README holds here with
`staging` for `prod`.

## Before the apply

`data-governance/data/`'s Stage 9 change applied (pass 2, the read share) and `staging/sagemaker/`
applied, since Lake Formation refuses a grant to a role that does not exist. Then Recipe D, as in
Production. The module writes `CROSS_ACCOUNT_VERSION` 4, where Staging read 1 before the apply of 2026-10-22; the
version governs how an account shares, which Staging never does. The first apply read back the
`InfrastructureAccess` seat alone and both default lists `[]`.

## What differs from Production

| Object | Staging |
|---|---|
| the data key | no debug-role statement and no Redshift statement, and the deployment manager's run read as in Production; the persona's is `AllowTheDataScientistToDecryptViaS3`, `Decrypt` alone through S3, since `DataScientistStagingAccess` writes nothing |
| `awsds-staging-outputs`'s policy | the trusted endpoint is `staging/foundation/`'s gateway endpoint; `DenyThePersonaAnyWrite` holds the persona to reads, on the whole bucket (8.4: everything readable, nothing writable); no named-prefix statements and no debug role |
| Lake Formation grants | the job role's read alone: `job_link_describe`, `job_shared_databases`, `job_shared_tables`; no `job_curated_write`, since Staging received no write to regrant |
| `app_outputs` | the deploy creates the application's tables from the repository's schemas, after Stage 8's 3.2 and before its 3.3 (4.4) |
