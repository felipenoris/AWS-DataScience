# D22 — The Data Governance account — state separated from compute

**Status:** Decided (2026-08-08): **the governed lake moves out of the environment accounts into a dedicated Data Governance account; every environment reaches it through Lake Formation cross-account shares**

**In one line:** The governed lake moves to a dedicated Data Governance account; every environment reaches it through Lake Formation shares.

**Related decisions:** [D13](D13-lake-formation-enforcement.md), [D18](D18-data-scientist-access.md), [D20](D20-staging-account.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 3](../stages/stage-03-networking.md), [Stage 5](../stages/stage-05-data-foundation.md), [Stage 9](../stages/stage-09-deployment-targets.md), [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

Environments (dev/staging/prod) sit on the *lifecycle* axis: how mature and protected a given copy of the application is. Data ownership sits on a different axis entirely: who produces a dataset, answers for its quality and sets its access policy. The lake outlives every application that reads it, so tying it to any environment account ties the data's life to a deployable thing's life — and forces a copy per environment. **What lives here:** the raw and curated S3 buckets (Iceberg), the Glue Data Catalog, Lake Formation with the LF-Tags and the D13 registrations, the classification scheme, the ingestion drop-box (D18), and Macie's primary scan scope (Stage 11). **What never lives here:** compute. No VPC in the first build — the data plane (S3, Glue, Athena, LF) is serverless, and consumers reach it through their *own* VPC endpoints; the SCP on the `Data` OU denies EC2 and SageMaker outright, and deletion protection is the policy set's whole personality (no `s3:DeleteBucket`, Object Lock where retention warrants it). **Who touches it:** nobody, interactively (D18). Sandbox and Development hold LF **read** shares; Production's job execution role holds LF read *and* the **governed write** — the producer path: production ETL writes curated tables through LF-aware engines, cross-account, and that is the only way governed data is ever written. Staging is deliberately not on the share (D20 — its data is sampled or synthetic, local to it). **What this closes and what it opens:** it closes the `plan/institutional-delta.md` row "the lab conflates environment with data domain", makes D13 cleaner (the execution roles in the environment accounts hold no S3 access at all to lake buckets — the accounts do not even contain them), and centralises what Macie scans. It opens more cross-account wiring: every row of `plan/integrations.md` that involved "Production's lake" now points at Data Governance, and the LF share count goes from one to three. One domain, one team still — but now the mechanism is exercised in the shape it scales in.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
