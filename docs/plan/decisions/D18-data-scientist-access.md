# D18 — Data scientist access outside the Interactive OU

**Status:** Decided (2026-08-07, restated 2026-08-08 for the nine-account layout): **data plane read, no compute, no control plane; writes only to enumerated prefixes**

**AMENDED 2026-09-05:** the Development row becomes the Staging row and is applied for the first time — `DataScientistStagingAccess` (read-only, no `athena:`), `DeploymentManagerAccess`, and **no** `DevEnvStewardAccess`. The lake share, the resource links, the re-grants and the vending policy the account inherited from its interactive life are all removed at [6b](../stages/stage-06b-development-becomes-staging.md) step 2.

**In one line:** Outside the Interactive OU the data scientist gets the data plane, no compute, no control plane; writes only to enumerated prefixes.

**Related decisions:** [D19](D19-derived-zone.md), [D22](D22-data-governance-account.md)

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 3](../stages/stage-03-networking.md), [Stage 5](../stages/stage-05-data-foundation.md), [Stage 9](../stages/stage-09-deployment-targets.md)

---

## Rationale and consequences

`docs/ORGANIZATION.md` gives the data scientist "read-only access to production environment data, and read-write access to sandbox and development environment". The full access matrix, per account: **Sandbox and Development** — read-write, interactive, the D19 derived zones; this is where the person works. **Staging — read-only, and nothing else.** No writes at all, not even a drop-box: Staging exists to be written by the pipeline and read by a human diagnosing why the pipeline failed, which is exactly what the `amazon-sagemaker-secure-mlops` reference grants in its staging account — a staging environment a human can write to stops being evidence of what the pipeline does. **Production — the data plane without compute:** CloudWatch logs of a failed job, Glue catalog metadata, SageMaker job/pipeline/registry status, named S3 prefixes (application outputs), and Athena on a dedicated workgroup with a scan limit. Denied explicitly: the control plane in full, plus `sagemaker:Create*Job`, `sagemaker:CreatePresignedDomainUrl`, `glue:StartJobRun` and `lakeformation:GrantPermissions`. **Data Governance — no sign-in at all.** The lake (D22) is read through the Lake Formation share from Sandbox and Development, which is the canonical analytical path — the tools are where the person is, so signing in to the account that stores the data accomplishes nothing. The one write the data scientist has toward the lake is the **ingestion drop-box** in Data Governance (`s3:PutObject` into a dated prefix — no `GetObject`, `DeleteObject` or `ListBucket`; a letterbox, not a shared folder), granted cross-account by bucket policy to the Interactive-OU roles **and by a matching statement in `DataScientistAccess` itself — both halves, INT-10 as amended (Lesson 28)** — rather than by a sign-in. **Deliberately not built:** any general-purpose exchange bucket between environments, which would be a promotion path running parallel to the Stage 8 approval gate. **One consequence to handle before it bites:** every `aws:SourceVpce` deny in a bucket policy (Stage 5, Stage 9) is evaluated against callers from *other* accounts — a data scientist at a laptop reaches S3 through the Sandbox or Development VPC endpoints or through the WireGuard Elastic IP — so the condition has to be a list that admits them (INT-05), or every call fails with an `AccessDenied` whose cause is invisible from the error.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
