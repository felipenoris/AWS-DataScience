# production/data — Production's data platform, layer `[P]`

Stage 9 steps 1 and 2.3, applied 2026-10-22. The `consumer-data` module's third caller
([its README](../../../terraform-modules/consumer-data/README.md) holds the module's own rows: the key's
administration statement, the settings, the links, the persona's re-grants); this file indexes what the
slice adds. The `.tf` comments carry the reasoning. `staging/data/` is the same shape without the
governed write ([its README](../../staging/data/README.md)).

## The apply is two steps

Recipe D ([`terraform-changes.md`](../../../docs/plan/runbooks/terraform-changes.md)): the settings alone
under `-target=module.consumer_data.aws_lakeformation_data_lake_settings.this`, read back (`DT-5`, and
`IAMAllowedPrincipals` revoked if it is still there), then the rest. Before it:
`data-governance/data/`'s Stage 9 change applied (pass 2), since the regrants below need the share. The
first apply, on 2026-10-22, read back the `InfrastructureAccess` seat alone and both default lists `[]`,
so nothing was revoked.

## The data key's added statements (`main.tf`)

Every role is the account root narrowed by `aws:PrincipalArn`, which KMS does not validate.

| `Sid` | Who | Actions and condition |
|---|---|---|
| `AllowTheJobRoleViaS3` | `awsds-prod-job-exec` | `Decrypt`, `GenerateDataKey` through S3 |
| `AllowTheDataScientistViaS3` | `DataScientistProdAccess` | `Decrypt`, `GenerateDataKey` through S3: the named outputs and Athena's results as the caller (5.1) |
| `AllowTheDebugRoleToDecryptViaS3` | `awsds-prod-debug` | `Decrypt` through S3 (6.1) |
| `AllowTheReleaseRolesViaS3` | `awsds-deploy-prod`, `InfrastructureAccess` | `Decrypt`, `GenerateDataKey` through S3: the release's tree and the inbox (Stage 10) |
| `AllowTheReleaseRolesForTheirWorkflows` | idem | `Decrypt`, `GenerateDataKey` with the workflow's ARN as encryption context (Stage 10 decision 2) |
| `AllowTheReleaseRolesToGrantTheWorkflowService` | idem | `CreateGrant` for an AWS resource; which context the service's grant carries is unread |
| `AllowTheReleaseRolesToDescribeTheKey` | idem | `DescribeKey` |
| `AllowTheChainRoleForItsWorkflows` | `awsds-prod-chain-exec` | `Decrypt`, `GenerateDataKey` with the workflow's ARN as context |
| `AllowTheDeploymentManagerToReadWorkflowRuns` | `DeploymentManagerAccess` | `Decrypt` with a workflow's ARN as encryption context alone: the service decrypts a run in the reader's session at each `GetWorkflowRun` (Stage 10 decisions 2, 11). No S3 object carries that context, so the approver still decrypts no output (D31) |
| `AllowTheWorkflowRolesViaS3` | `awsds-prod-wf-*` | `Decrypt`, `GenerateDataKey` through S3: the result file and the inbox markers |
| `AllowTheWorkflowRolesForTheirWorkflows` | `awsds-prod-wf-*` | `Decrypt` with the workflow's ARN as context |
| `AllowJobVolumeGrantsThroughSageMaker` | `awsds-prod-wf-*`, `awsds-deploy-prod` | `CreateGrant`, `DescribeKey` through SageMaker: a job's volume key, granted in the submitting session (6i) |
| `AllowCloudWatchLogsForTheJobAndWorkflowGroups` | `logs.<region>.amazonaws.com` | the key's use for the job groups (`/aws/sagemaker/*`, `/aws-glue/*`) and Stage 10's (`/awsds/prod/wf/*`, the chains' group), by `kms:EncryptionContext:aws:logs:arn` |
| `AllowRedshiftServerlessViaServiceInThisAccount` | this account, through Redshift Serverless | the governed warehouse's namespace (9.1); without it `CreateNamespace` fails and leaves an orphan secret (`EXC-12`) |

## `awsds-prod-outputs`'s policy (`buckets.tf`)

Beside the module's TLS-only and presigned-age denies.

| `Sid` | Denies |
|---|---|
| `DenyOutsideTheJobNetwork` | everything not through VPC-Workloads' gateway endpoint, not by or through a service, and not by `InfrastructureAccess`, the persona, the debug role or the deploy role (INT-05, D39) |
| `DenyThePersonaAndTheDebugRoleAnyWrite` | the persona and the debug role anything but `GetObject`, `GetObjectVersion`, `ListBucket`, `GetBucketLocation` |
| `DenyThePersonaReadsOutsideTheNamedPrefixes` | the persona's reads outside `var.persona_read_prefixes` (`app-etl/outbox/`) |
| `DenyThePersonaListingsOutsideTheNamedPrefixes` | the persona's listings outside the same prefixes |
| `DenyTheReleaseRoleAnythingButItsObjects` | the deploy role anything but `PutObject`, `GetObject`, `GetObjectVersion`, `ListBucket`, `GetBucketLocation` |
| `DenyTheReleaseRoleObjectsOutsideItsPrefixes` | the deploy role's object calls outside `applications/` and `inbox/` |
| `DenyTheReleaseRoleListingsOutsideItsPrefixes` | the deploy role's listings outside the same prefixes |
| `DenyWritesToApplicationsButTheReleaseRoles` | `PutObject`, `DeleteObject` under `applications/` to all but the deploy role and `InfrastructureAccess` (Stage 10 decision 12) |

`aws_s3_bucket_notification` sends the bucket's events to EventBridge (Stage 10 decision 16).
`awsds-prod-derived` carries the module's policy alone and expires after 30 days (decision 11).

## Lake Formation grants (`lakeformation.tf`)

| Grant | Principal | Resource | Permissions |
|---|---|---|---|
| `job_link_describe` (×2) | `awsds-prod-job-exec` | the links `raw`, `curated` | `DESCRIBE` |
| `job_shared_databases` | idem | the lake's databases, `layer ∈ {raw, curated}` | `DESCRIBE` |
| `job_shared_tables` | idem | the lake's tables, `layer ∈ {raw, curated}` and `classification ∈ {public, internal}` | `SELECT`, `DESCRIBE` |
| `job_curated_write` | idem | every table of the lake's `curated`, by name | `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DESCRIBE`: the governed write (2.3) |
| `release_app_outputs_database` | `awsds-deploy-prod` | database `app_outputs` | `CREATE_TABLE`, `DESCRIBE` |
| `release_app_outputs_tables` | idem | every table of `app_outputs` | `ALTER`, `DROP`, `DESCRIBE` |
| `job_app_outputs_database` · `_tables` | `awsds-prod-job-exec` | `app_outputs` and its tables | `DESCRIBE`; `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DESCRIBE` |
| `persona_app_outputs_database` · `_tables` | `DataScientistProdAccess` | idem | `DESCRIBE`; `SELECT`, `DESCRIBE` |

The workgroup `awsds-prod-athena` (`athena.tf`) is enforced: its results land under
`awsds-prod-derived/results/` under the data key, and a query past 10 GB is cancelled (decisions 2, 11).
