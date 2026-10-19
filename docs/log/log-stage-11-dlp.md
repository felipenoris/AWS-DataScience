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

## 2026-10-18 — `TM-21`: the Sandbox project key's narrowing chosen

Written by Claude in the cloud session of the project thread, with no AWS identity, in PR #164; nothing
changed in AWS.

- **[user] The choice** (00:02:46, on a card): narrow the project key policy's two
  `Principal: {"AWS": "*"}` statements to this organization's principals, rather than archive the
  finding individually.
- **[Claude] What the change waits on.** The statement the finding carries, which `get-finding-v2` in
  Audit names, asked of the user at 00:03:35. And Stage 17's pass 1 (PR #157), which moves the same
  module, `terraform-modules/sagemaker-prereqs/`, to `v0.5.0`, a tag not yet on origin: the narrowing
  is the module's next tag after it, read from `git ls-remote --tags origin` when it is tagged, and its
  `sandbox/sagemaker/` apply runs from the laptop. `TM-21` and `EXC-18` stay open until a snapshot
  reads the finding `RESOLVED`.

## 2026-10-18 — `TM-21`: the finding read by `get-finding-v2`

- **[user] The finding's detail**, read in Audit's CloudShell with the commands asked at 00:03:35 and
  pasted in the thread at 00:18:51:

  ```bash
  ANALYZER=$(aws accessanalyzer list-analyzers --region us-west-2 --query "analyzers[?name=='awsds-org-external-access'].arn" --output text)
  ID=$(aws accessanalyzer list-findings-v2 --region us-west-2 --analyzer-arn "$ANALYZER" --filter '{"resourceType":{"eq":["AWS::KMS::Key"]},"status":{"eq":["ACTIVE"]}}' --query 'findings[0].id' --output text)
  aws accessanalyzer get-finding-v2 --region us-west-2 --analyzer-arn "$ANALYZER" --id "$ID" --query '[resource, findingDetails]' --output json
  ```

  The output, with the account id replaced by the account's name:

  ```json
  [
      "arn:aws:kms:us-west-2:<Sandbox Account 1>:key/a81b1ef3-716f-4105-bb42-14184a6e2174",
      [
          {
              "externalAccessDetails": {
                  "action": [
                      "kms:CreateGrant",
                      "kms:Decrypt",
                      "kms:GenerateDataKey"
                  ],
                  "condition": {},
                  "isPublic": true,
                  "principal": {
                      "AWS": "*"
                  },
                  "resourceControlPolicyRestriction": "APPLICABLE"
              }
          }
      ]
  ]
  ```

- **[Claude] Both statements carry the finding.** Its three actions are the union of
  `GrantKMSPermissionsForAllProjectRoles` (`kms:GenerateDataKey`, `kms:Decrypt`) and
  `AllowCreateGrantForProjectRoles` (`kms:CreateGrant`), and its principal is theirs. The analyzer
  reads the key as public (`isPublic: true`) and weighs neither statement's conditions as bounding
  (`condition: {}`); `APPLICABLE` is the RCP present and left out of the evaluation. That an
  `aws:PrincipalOrgID` condition on both statements resolves the finding is inferred: no AWS page read
  here says how the analyzer weighs it on a key, and the snapshot after the apply decides it. AWS's key
  permissions for the Tooling blueprint, the contract `kms.tf` adapts, give both statements without an
  account or organization condition and do not mention Access Analyzer (read 2026-10-18). The change
  now waits only on Stage 17's pass 1 (PR #157).

## 2026-10-18 — `TM-21`: the narrowing tagged `sagemaker-prereqs-v0.6.0`

Written by Claude in the cloud session of the project thread, with no AWS identity, in PR #166; nothing
changed in AWS.

- **[Claude] The module change** (`0dc159f`, on `main` after PR #157 merged as `e6dfc6a`):
  `aws:PrincipalOrgID` in the `StringEquals` of `GrantKMSPermissionsForAllProjectRoles` and of
  `AllowCreateGrantForProjectRoles`, the id read from the data source
  `aws_organizations_organization.current` as `vpc` and `vpc-egress` read it. Checked in the cloud
  session: `terraform fmt -check`; `init -backend=false` and `validate` with the providers
  `sandbox/sagemaker/`'s lock file pins (aws 6.61.0, awscc 1.98.0); a scratch `terraform test` with
  mocked providers, in which both statements rendered with the organization id when `domain_id` is set
  and neither rendered without it; `make check` OK; the offline gates green on the commit.
- **[user] The tag**, pushed from the laptop because the cloud session's tag pushes are refused, and
  pasted in the thread at 06:10:04:

  ```text
  git fetch origin claude/project-thread-yrm4u1
  git log --oneline -1 0dc159f
  git tag sagemaker-prereqs-v0.6.0 0dc159f
  git push origin sagemaker-prereqs-v0.6.0
  git ls-remote --tags origin sagemaker-prereqs-v0.6.0
  From github.com:felipenoris/AWS-DataScience
   * branch            claude/project-thread-yrm4u1 -> FETCH_HEAD
  Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
  To github.com:felipenoris/AWS-DataScience.git
   * [new tag]         sagemaker-prereqs-v0.6.0 -> sagemaker-prereqs-v0.6.0
  0dc159f5a6a034b3ac80d39ee4fbbc981b840866	refs/tags/sagemaker-prereqs-v0.6.0
  ```

- **[Claude] The caller.** `terraform-live/sandbox/sagemaker/` points at `sagemaker-prereqs-v0.6.0`,
  not planned and not applied. The slice also carries Stage 17's pass 1 (`v0.5.0`, `MLflowApp`), not
  applied either, whose step 1.2 reads the slice's plan as one configuration and one grant added. With
  its step 1.3 applied first, this version's plan should change only the key's policy, in place
  (inferred: no plan has run). `TM-21` and `EXC-18` stay open until a snapshot reads the finding
  `RESOLVED`.

## 2026-10-18 — `TM-21`: `sandbox/sagemaker/` planned, not applied

Written by Claude, session "Stage 11: pass 0 readings and the data cells filters", as the
infrastructure user (`InfrastructureAccess`, profile `awsds-infra-sandbox-1`), between 19:45 and 20:40Z.
Account ids are replaced by the account's name.

- **[Claude] The plan**, `-input=false`, to a file outside the repository: `Plan: 2 to add, 1 to change,
  0 to destroy.` The change is the project key's policy in place, `aws:PrincipalOrgID` added to the
  `StringEquals` of `GrantKMSPermissionsForAllProjectRoles` and of `AllowCreateGrantForProjectRoles`,
  six statements unchanged. The adds are Stage 17's: the `MLflowApp` blueprint configuration and its
  `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant.
- **[Claude] Not applied.** The same apply would create `MLflowApp` before Stage 17's step 1.1 reads the
  portal without it. The apply waits on that reading, or on the user accepting its loss.

## 2026-10-18 — pass 0's readings

Written by Claude, same session and identity, profiles `awsds-infra-data`, `awsds-infra-sandbox-1`,
`awsds-infra-prod`, `awsds-infra-staging` and `awsds-infra-identity`.

- **[Claude] 2.1.5's key half, `alias/awsds-data-data`**: four statements, no grant.
  `EnableIamPolicyDelegationInThisAccount` (the `<Data Governance Account>` root, `kms:*`);
  `AllowDropBoxWritersViaS3` (the `<Sandbox Account 1>` root narrowed to `DataScientistAccess`,
  `GenerateDataKey` and `Decrypt` through S3); `AllowCloudWatchLogsEncryptionForGlue` (the logs service,
  `/aws-glue/*`); `AllowProductionPickupDecryptViaS3` (the `<Production Account>` root narrowed to
  `awsds-prod-job-exec`, `Decrypt` through S3). `simulate-principal-policy` over every Data Governance role
  that is not service-linked: `kms:Decrypt` allowed to `InfrastructureAccess`, `AWSPowerUserAccess`,
  `AWSControlTowerExecution`, `aws-controltower-AdministratorExecutionRole`,
  `awsds-data-catalog-maintenance` and `awsds-data-lf-registration`; implicit deny for
  `GovernanceManagerAccess`, `AWSReadOnlyAccess`, `AWSOrganizationsFullAccess`, the two domain roles and
  the other Control Tower roles. `awsds-prod-job-exec` exists since 2026-10-18T19:59:03Z (read at
  20:36:57Z), created by Stage 9's `production/sagemaker` apply.
- **[Claude] RAM on the lake shares**: `LakeFormation-V4-AZCTDXPPCJ`, `LakeFormation-V4-1KCIGTUIUW` and
  `DataZone-EXTENDED_ACCESS-<domain>-ORG-ONLY` are `ACTIVE`, `allowExternalPrincipals: False`, each with one
  principal, `<Sandbox Account 1>`, `external: False`.
- **[Claude] `TM-17`'s identity half.** The first simulation of every Sandbox role returned `explicitDeny`,
  `AllowedByOrganizations: false`, for `sns:Publish` to an outside account and to this one alike; with
  `aws:RequestedRegion=us-west-2` in the context both read the identity layer, and `glue:GetDatabases`
  moved from `explicitDeny` to `implicitDeny` the same way. The Control Tower Region ceiling,
  `CT.MULTISERVICE.PV.1`, is the only SCP on the path conditioned on that key over every action. With
  the key, against resources in `<an account outside the organization>`, AWS's documentation example: `sns:Publish`,
  `sqs:SendMessage`, `events:PutEvents`, `lambda:InvokeFunction`, `kinesis:PutRecord` and
  `firehose:PutRecord` are implicit deny for every Sandbox role but `InfrastructureAccess`,
  `AWSPowerUserAccess`, `AWSControlTowerExecution` and `aws-controltower-AdministratorExecutionRole`.
  Reading the policies of both project roles found what the generic names missed:
  `SageMakerStudioProjectUserRolePolicy` v75's `AirflowSqsActions` allows `sqs:SendMessage` on
  `arn:aws:sqs:*:*:airflow-celery-*` under `StringNotEquals aws:ResourceAccount ${aws:PrincipalAccount}`,
  simulated `allowed` for a queue of that name in that outside account (SCP and boundary allowing) and
  `implicitDeny` for the same name in this account; and `InvokeFunctionForAmazonBedrockIDE` and
  `LambdaInvokeFunctionViaBedrock` allow `lambda:InvokeFunction` on any account's `amazon-bedrock*`
  functions under `aws:CalledViaFirst = bedrock.amazonaws.com` and the project tag. No persona set in
  Sandbox, `Production`, `Staging` or `Data Governance` carries an Allow for any of these actions, and
  every other Sandbox role's Lambda statement is bound to its own account. Sandbox holds no endpoint but
  the S3 and DynamoDB gateways while the environment is down, and `vpc-egress` names no SQS group.
  `DenyProvisionedMwaa` is in the root baseline (read 20:36:57Z).
- **[Claude] The Stage 5a and 6 outcomes step 11 consumes**, collected: the classification scheme and the
  live LF-Tags, `classification` (`public`, `internal`, `restricted`, `personal`) and `layer` (`raw`,
  `curated`, `dropbox`), `businessunit` absent; the derived zone is `awsds-sandbox-smus-projects`, and
  Sandbox holds three buckets, `awsds-sandbox-lake`, `awsds-sandbox-smus-projects` and
  `awsds-sandbox-tfstate`; Stage 5a decision 4's Athena outcome is the closed hole, `DenyUserCompute` on
  the `Data` OU naming `athena:StartQueryExecution`; `sample_trades` carries its 12 rows of 2026-08-20,
  whose values are recorded nowhere; D5's comparison is withdrawn by D38, the raw-address row closed by
  route and its proxy half `TM-01`; the grain is decision 6's, roles and projects; the remote-access
  residual is `TM-08`. Stage 9's producer path is not built: no `production/data/`, and decision 3's map
  has no `Production` row.
- **[Claude] The lake's Lake Formation grants**, read for step 2: 28 permission rows in Data Governance, of
  which the `<Sandbox Account 1>` account holds the two TBAC rows of the register and nothing more; no
  data cells filter exists; in Sandbox only `DataScientistAccess` holds lake regrants (the two links, the
  two TBAC expressions), and no project role holds any. `DataLakeSettings`: `CROSS_ACCOUNT_VERSION 4` and
  `SET_CONTEXT TRUE` in both accounts; Sandbox's administrators are `InfrastructureAccess`,
  `awsds-sandbox-smus-manage-access` and `awsds-sandbox-smus-provisioning`.
- **[Claude] Validation 1's before-run, `./aws/dlp.py`** on the six infrastructure profiles,
  2026-10-18T20:12:34Z, exit 0: `DP-1`, `DP-2`, `DP-3`, `DP-5`, `DP-6` and `DP-7` notes, no failure, `DP-4`
  not emitted (no trail). Macie disabled in both members and no delegated administrator; no detector in
  any of the six accounts; `DenyCloudTrailKill` absent. The run over every profile exits 1 only because
  seven persona and Control Tower profiles hold no SSO token, none of them DLP-scoped.

## 2026-10-18 — 5.6's instrument, `DP-8`

Written by Claude, same session and identity.

- **[Claude] `get-model-invocation-logging-configuration`**, by hand first: an empty answer in `us-west-2`,
  and in `us-east-1`, `us-east-2` and `eu-west-1` `AccessDeniedException ... with an explicit deny in a
  service control policy`. The Region ceiling's 92 `NotAction` entries include six Bedrock actions, and
  neither logging-configuration action is among them.
- **[Claude] `./aws/dlp.py` with `DP-8`**, 2026-10-18T20:16:10Z, exit 0: `DP-8 pass`, no configuration in
  `us-west-2` in any of the six accounts, `us-east-1` and `us-east-2` denied by the ceiling in each.

## 2026-10-18 — pass 1 written, stopped before the apply

Written by Claude, same session and identity.

- **[Claude] `data-governance/data/`**, plan with the filters and grants written and `filter_shares`
  empty: `No changes.` The same plan with Sandbox named for both filters, saved outside the repository and
  discarded: `Plan: 4 to add, 0 to change, 0 to destroy.`, the two filters and two `SELECT` grants with the
  grant option to `<Sandbox Account 1>`.
- **[Claude] `sandbox/data/` against the local module**, `data_cells_filter_grants` empty: `No changes.`
  With a project role and the persona as sample readers: `Plan: 3 to add`, `DESCRIBE` on the `curated`
  link for the project role alone. The pin was reverted to `consumer-data-v0.6.0` and the slice
  re-initialised.
- **[Claude] Nothing applied.** No principal the plan names can be filtered without a choice the stage file
  does not settle, so the apply, the module tag and the caller's pin wait on Stage 11 decision 12.

## 2026-10-19 — `TM-21`: applied with Stage 17's 1.3

Written by Claude, session "Stage 17 1.1 and 1.3: MLflow reading and the applies", as the infrastructure
user (`InfrastructureAccess`, profile `awsds-infra-sandbox-1`). The apply and its full record are in
[Stage 17's log](log-stage-17-sandbox-machine-learning.md), entry of the same day.

- **[user] The apply**, of a plan Claude saved at `v0.6.0` after Stage 17's 1.1 had read the portal:
  `aws_kms_key.this: Modifications complete after 6s`, in the same `Apply complete! Resources: 2 added, 1
  changed, 0 destroyed.` as Stage 17's `MLflowApp` configuration and grant. Sandbox's trail reads
  `PutKeyPolicy` at 05:11:46 UTC as `InfrastructureAccess`.
- **[Claude] Read back** at 05:14 UTC: the slice re-plans `No changes`; the live policy's two
  `Principal *` statements, `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`,
  carry `aws:PrincipalOrgID` in their `StringEquals`, and the other seven statements read as before.
- **[Claude] Still open.** `TM-21` and `EXC-18` close when a snapshot in Audit reads the finding
  `RESOLVED`; no CLI profile reaches Audit, so that read is the user's, in Audit's CloudShell with the
  block of this log's entry "`TM-21`: the finding read by `get-finding-v2`", its status filter set to
  `RESOLVED`.
