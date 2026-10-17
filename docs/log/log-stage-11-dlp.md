# Log — Stage 11 — Data protection and DLP

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is [`docs/plan/stages/stage-11-dlp.md`](../plan/stages/stage-11-dlp.md).
Account ids are replaced by the account's name. All times UTC.*

---

## 2026-10-17 — step 2.1.1, the organization analyzer read and triaged

- **[user] The Audit snapshot.** `aws/cloudshell/audit-iam-analyser.sh` ran in Audit's CloudShell at
  23:38:36Z under `AWSAdministratorAccess`, and its output was attached in the Claude project's thread
  "Esqueleto do threat model". The file carries account ids and stays out of git.
- **[Claude] Sections 2, 3, 5 and 6.** CHECK OK: one analyzer, `awsds-org-external-access`,
  `ORGANIZATION`, `ACTIVE`, created 2026-08-12T03:38:38Z, the five project tags, no archive rule, last
  resource analyzed at 23:10:48Z (`awsds-prod-tfstate`); no call failed. `INV-10` holds.
- **[Claude] Section 4 counts 49 findings, all `ExternalAccess`: 46 `ACTIVE`, 3 `RESOLVED`.** 45 of the
  active ones are `AWSReservedSSO_*` roles, one per assignment-backed permission set per account:

  | Account | Active role findings | Beyond A.1's class rows |
  |---|---|---|
  | Management | 5 | none |
  | Audit | 3 | none |
  | Log Archive | 3 | none |
  | Policy Canary | 4 | none |
  | Identity | 4 | none |
  | Data Governance | 5 | `GovernanceManagerAccess` |
  | Production | 7 | `DataScientistProdAccess`, `DeploymentManagerAccess`, `DevEnvStewardAccess` |
  | Sandbox Account 1 | 7 | `DataScientistAccess`, `DeploymentManagerAccess`, `DevEnvStewardAccess` |
  | Staging | 7 | `DataScientistStagingAccess`, `DeploymentManagerAccess`, and the direct `AWSAdministratorAccess` an account update re-created on 2026-09-06 |

  That is the 35 of 2026-08-15, the nine persona rows of `identity/sso`'s `local.assignments` and
  Staging's direct assignment: `INV-16`'s shape, restated in `docs/AWS_STATE.md`.
- **[Claude] The three `RESOLVED` findings are in Staging**: the `DevEnvStewardAccess` and
  `DataScientistAccess` roles whose assignments Stage 6b step 2.1 removed on 2026-09-06, and the KMS key
  `ef2e17cd-…`, which no document here names. That it is the Development project key 6b destroyed
  (`PendingDeletion` until 2026-10-06) is inferred.
- **[Claude] One `ACTIVE` finding has another shape: the KMS key `a81b1ef3-…` in Sandbox Account 1**,
  `alias/awsds-sandbox-project` (the id [`log-stage-06i`](log-stage-06i-sandbox-orchestration.md)
  records). Two statements of its policy, written by `terraform-modules/sagemaker-prereqs/kms.tf`,
  grant `Principal: {"AWS": "*"}` under conditions that bound neither the caller's account nor its
  organization: `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`. Which
  of them the finding carries is inferred, since the summary names neither. Outside the organization the
  RCP's `EnforceOrgIdentitiesOnSecretsAndKeys` denies `kms:*`, read and never attempted, and an external
  finding does not weigh an RCP (AWS's `ExternalAccessDetails` reference, read 2026-10-17), so the
  finding stands with the RCP in place. Recorded as `TM-21` in
  [`threat-model.md`](../plan/threat-model.md) and as `EXC-18`; the user chooses between narrowing the
  two statements and archiving the finding individually.
- **[Claude] No finding names an S3 bucket**: not the lake's five, not `awsds-sandbox-smus-projects`,
  not `awsds-sandbox-lake`. None names the lake's data CMK `alias/awsds-data-data`, Sandbox's
  `alias/awsds-sandbox-data`, a function, a topic, a snapshot or a file system. The threat model's
  outside column is filled from this reading.
