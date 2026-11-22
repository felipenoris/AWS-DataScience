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

## 2026-10-21 — decision 12's RLS policies and the mechanisms of `TM-22`..`TM-24`, read on 2026-10-20 (PR #218), recorded

*Claude's sitting, no AWS call: the offline task of the orchestrating session "Stage 18 checklist" that
opened PR #218 (merged 2026-10-20T21:52:33Z) read AWS's documentation pages, botocore's models and both
providers' changelogs, recorded in [`REFERENCES.md`](../REFERENCES.md) the same sitting. It wrote no
entry, under the rule of that day; this one is written on 2026-10-21 from the PR's body and diff, with no
AWS call either.*

- **[Claude] Decision 12 gains Lake Formation's row-level security policies.** A data cells filter's row
  predicate still yields to an all-rows grant, while an RLS attachment scopes down any `SELECT` but `ALL`
  or `SUPER_USER`; no provider resource and no CloudFormation type carries one. The recommendation keeps
  the written filter for the row half while the project role holds no other `SELECT` on the table, and
  adds an RLS policy once 6f's (c) regrants it. The decision stays the user's.
- **[Claude] `threat-model.md`'s `TM-22`..`TM-24` carry their mechanisms, the measurements still owed.**
  The ODBC and JDBC drivers query as the project role, through `GetEnvironmentCredentials`; the Data
  Agent's five DataZone actions are the project role's, and AWS names a deny and a domain switch that stop
  it; no IAM condition key reaches a connection's type.
- **[Claude] The knowledge base's Lambdas**, in 3.7, `TM-12` and the Lambda row of the resource types no
  RCP reaches, depend on Stage 17's decision 12, from Stage 17's template reading of 2026-10-19.
- **[Claude] `awsds-staging-smus-projects`**, Stage 18's projects bucket in Staging, gains the halves its
  code and Stage 18's log answer; its outside column waits on an Audit snapshot taken since 2026-10-19,
  the user's.

## 2026-10-21 — step 4.3's sentence on GuardDuty's roles, corrected on 2026-10-20 (PR #227), recorded

*Claude's sitting, no AWS call: the task of the orchestrating session that opened PR #227 (merged
2026-10-20T22:54:07Z) corrected Stage 15's text on GuardDuty's service-linked roles from AWS's pages,
recorded in [Stage 15's log](log-stage-15-guardduty.md), and the same sentence here. It wrote no entry,
under the rule of that day; this one is written on 2026-10-21 from the PR's body and diff, with no AWS
call either.*

- **[Claude] 4.3 says GuardDuty creates only service-linked roles**, where it said only the
  service-linked role: Malware Protection for EC2 creates a second, and neither role's managed policy
  holds a `guardduty:` action, so the step's "no administration role to name" holds.

## 2026-10-21 — 2.1.1's snapshot taken again, before Stage 18's 8.6

*The user ran `aws/cloudshell/audit-iam-analyser.sh` in Audit's CloudShell as AWS Control Tower Admin with
`AWSAdministratorAccess` and saved the report in the project folder's `aws/output/cloudshell/`; Claude read
it and compared it with the report of 2026-10-17. Written by the Stage 18 session, no other Claude session
running on the laptop at the time.*

- **[user] The snapshot**: generated 2026-10-21T23:42:59Z, `Audit Account` `[OK]`, `us-west-2`; section 5
  *"CHECK OK: exactly one analyzer, ORGANIZATION zone of trust, ACTIVE"*, its last resource analyzed at
  23:30:17Z; section 6 *"None. Every call in this report returned successfully."*
- **[Claude] The findings**: 49, 45 `ACTIVE` and 4 `RESOLVED`. Against 2026-10-17's report (46 and 3) the one
  change is the key `a81b1ef3-…`, `alias/awsds-sandbox-project` in `Sandbox Account 1` (read with
  `describe-key`), from `ACTIVE` to `RESOLVED`: `TM-21` is controlled and `EXC-18` closed. Every `ACTIVE`
  finding is `ExternalAccess` on an `AWSReservedSSO_*` role, `INV-16`'s shape, at 45. No finding names
  Stage 18's projects bucket `awsds-staging-smus-projects` or Staging's project key (`62942eb7-…`), both
  created 2026-10-19. The other `RESOLVED` rows are 2026-10-17's: the key `ef2e17cd-…` and 6b step 2.1's two
  roles.
- **[Claude] Carried into** `threat-model.md` (`TM-21`, the Staging bucket's row, what the file waits on),
  `AWS_STATE.md` (`EXC-18`, `INV-16`), this stage's 2.1.1 and the waiting list.

## 2026-10-22 — Production's release bucket, the PKI state and the PKI key's alarm in 5.1 and 5.2

*Claude, in the session `stages-7-8-pending` (branch `claude/stages-7-8-pending-03936d`), no AWS call:
the plan revised from a review of Stages 7 and 8, on the user's request to correct what the review found.*

- **[Claude] 5.1's map gains Production**: `awsds-prod-releases`, whose downloads Stage 8 decision 20
  leaves to this step, and the `pki/` prefix of the state bucket, D36 §5's first control. No stage file
  carried either, and both wait on `production/data/` with the rest of Production's trail.
- **[Claude] 5.2 gains `awsds-prod-pki-key-use`**, D36 §5's second control: `kms:Decrypt` on the key behind
  `alias/awsds-prod-tfstate-pki` by anyone but the infrastructure role, and `kms:ScheduleKeyDeletion` on it.

## 2026-11-17 — `TM-01`'s order taken on a card, with no AWS call

*Claude's sitting in a cloud session of the user's Claude project, no AWS call: the review of the plan's
open decisions the user asked for at 22:01 UTC, one card per decision under the user's default of
21:50 UTC (the path AWS suggests), recorded by pull request #317. Times are UTC.*

- **[user] `TM-01`**, at 22:55, on the card *"Pôr -n nas listas de permissão do proxy, para um IP cru não
  casar com nome?"*: *"Medir antes com uma sonda"*, against the flag recommended. **[Claude]** The probe
  runs in a Sandbox sitting with a space up: a `CONNECT` to an address whose reverse record, read with
  `dig -x` first, ends in an allowed suffix, beside one whose record names no allowed host as the
  negative control, read in `/awsds/prod/proxy`; the flag is decided on its reading.

## 2026-11-21 — `TM-01`'s probe: a raw address admitted by its reverse record, and `-n` decided

*Claude, in the session started by §N.9 day 2's orchestrating session on branch
`claude/stage11-tm01-sonda-d80762`; the probe by the user's hand in a JupyterLab terminal of the day-2
space in `eighth-experimentation`. AWS calls: CloudWatch Logs reads in Production as the infrastructure
user (`awsds-infra-prod`, `InfrastructureAccess`), no write. Times are UTC.*

- **[Claude] The plane**, read from `main` at `b3b900b4`: a space leaves from `sandbox-foundation`
  (`10.20.0.0/16`), an `allowlist` plane whose 42 names open with `.amazonaws.com`, rendered as
  `acl dst_sandbox_foundation dstdomain <names>` with no `-n`.
- **[Claude] The two addresses**, read with `dig` from the laptop at 20:23:11 and again at 20:30:18,
  unchanged: `54.213.164.60`, one of the four addresses of `airflow-serverless.us-west-2.api.aws`, reverse
  `ec2-54-213-164-60.us-west-2.compute.amazonaws.com.`; `108.158.137.46`, one of the four of
  `datazone.us-west-2.api.aws`, reverse `server-108-158-137-46.gig51.r.cloudfront.net.`. The plane
  refuses both names. The same reading over other AWS front-ends is `SUP-404`.
- **[Claude] The log's history**, `filter-log-events` over the group's whole life, its first match
  2026-09-07T00:41:17: `%CONNECT [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:%` and `%CONNECT \[%` returned no event;
  `%http://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+[:/]%` returned 94, every one `403 TCP_DENIED` to a private or
  link-local address (`10.31.0.1`, `10.32.0.10`, `169.254.170.2`, `169.254.169.254`). A pattern holding
  `(` is refused: *"Invalid character(s) in term '%('"*. The first pattern over the hour after the probe
  returned the probe's two lines and no other, its positive control.
- **[user] The probe**, pasted from the space's terminal:

  ```
  sagemaker-user@default:~$ date -u +%FT%TZ; curl -sS -o /dev/null --max-time 10 --proxy http://proxy.awsds.internal:3128 --noproxy '' -w 'positivo 54.213.164.60 CONNECT=%{http_connect}\n' https://54.213.164.60/; echo "exit=$?"
  date -u +%FT%TZ; curl -sS -o /dev/null --max-time 10 --proxy http://proxy.awsds.internal:3128 --noproxy '' -w 'negativo 108.158.137.46 CONNECT=%{http_connect}\n' https://108.158.137.46/; echo "exit=$?"
  2026-11-21T20:29:25Z
  curl: (60) SSL: no alternative certificate subject name matches target host name '54.213.164.60'
  More details here: https://curl.se/docs/sslcerts.html

  curl failed to verify the legitimacy of the server and therefore could not
  establish a secure connection to it. To learn more about this situation and
  how to fix it, please visit the web page mentioned above.
  positivo 54.213.164.60 CONNECT=200
  exit=60
  2026-11-21T20:29:25Z
  curl: (56) CONNECT tunnel failed, response 403
  negativo 108.158.137.46 CONNECT=403
  exit=56
  ```

- **[Claude] `/awsds/prod/proxy`**, read at 20:29:50, the window's newest line stamped 20:29:48:

  ```
  2026-11-21T20:29:25+0000 10.20.38.182 CONNECT 54.213.164.60:443 200 4701 722 TCP_TUNNEL
  2026-11-21T20:29:25+0000 10.20.38.182 CONNECT 108.158.137.46:443 403 3406 119 TCP_DENIED
  ```

  `10.20.38.182` is the day-2 space, 568 lines from 20:17:02 to 20:29:51. The verdict: the proxy admits
  a raw public address whose reverse record ends in an allowed suffix and refuses one whose record names
  no allowed host, from one source in one second.
- **[user] `-n`**, on a question of this session answered by 20:33: *"Aplicar o -n (Recomendado)"*, on
  every `dstdomain` of the allow-list planes, never on a deny list. The code is the session's that
  prepares the hub sitting's `production/proxy/` apply.

## 2026-11-21 — `TM-01`'s `-n` written, and `production/proxy/` planned against the live hub

*Claude, in the same session and branch, at the request of the session coordinating the hub sitting,
which relayed the user's words of 21:00 in its chat; the applies are that session's, from `main` after
PR #351's merge. AWS calls: an SSM `GetParameter`, EC2 and SSM Inventory reads and a `terraform plan`
in Production as the infrastructure user (`awsds-infra-prod`, `InfrastructureAccess`), no write. Times
are UTC.*

- **[Claude] The template**: `render-squid.sh.tftpl`'s `allowlist` branch renders
  `acl dst_<plane> dstdomain -n <names>`. The `open` branch's `acl dstdeny_<plane>` stays without the
  flag, which would admit an address whose reverse name is denied. Squid's `acl` pages for 6.9 and 5.10,
  read the same day, give `acl aclname dstdomain [-n] .foo.com ...`, the flag before the names.
- **[Claude] The host's Squid version is read nowhere**: SSM Inventory holds no `AWS:Application` entry
  for `awsds-prod-proxy`, only `access.log` reaches CloudWatch, and the image is
  `al2023-ami-2023.12.20260917.1`, whose release notes name no Squid update. The new host's
  `squid -k parse` is the flag's first reading, and a refusal at first boot leaves the allow-list empty,
  every Sandbox request `TCP_DENIED`, the failure `hub-anchors.tf` records for 2026-09-06.
- **[Claude] The render rehearsed** on the laptop: the template's jq program over
  `/datascience/prod/proxy/allowlist` at version 12 (`sandbox-foundation` an `allowlist` of 42 names,
  `production-workloads` and `staging-foundation` empty, `tunnel` and `production-foundation` `open`
  with empty deny lists) differs from the applied template's output in one line,
  `acl dst_sandbox_foundation dstdomain -n .amazonaws.com ...`.
- **[Claude] `./aws/proxy.py`**: `acl_values` reads the tokens before the first name that start with `-`
  as flags, `--` ending them, so `running_allowlist` returns the same 42 names over both renders and
  PX-3 compares equal with and without `-n`. Read as a name, `-n` would be an entry only the host has.
  The running table gains a FLAGS column (`running_flags`) that no check judges, so PX-3 does not fail
  on the host before the apply.
- **[Claude] `production/proxy/` planned** from the branch at 21:23:38, `-input=false`, Terraform
  1.17.2: `1 to add, 2 to change, 1 to destroy`, the counts of Stage 12's plan of 20:21:09.
  `aws_instance.this` is replaced on `ami`, masked, and on `user_data`, whose differences are the
  render's, two lines out and five in, and 6g decision 1's first-render comment, three out and two in.
  The alarm and `proxy.awsds.internal` change in place; the association does not change. A first plan
  at 21:21:28, with longer comments, read the same counts.
- **[Claude] The user data's size**: `length(local.user_data)` in `terraform console` reads 15,148, and
  the three templates hold no non-ASCII character, so 15,148 bytes against EC2's limit of *"16 KB, in
  raw form, before it is base64-encoded"*, about 1.2 KB of room. The render's change spent 262 bytes,
  and nothing in the slice checks the limit at plan time.
- **[Claude] Records**: `TM-01`'s row reads written and not applied, its revision trigger read in the
  FLAGS column of `./aws/proxy.py --on-host`; the Stage 11 `Status` row; `NETWORK.md` §5's paragraph
  says the flag is written, and it leaves with the apply.

## 2026-11-22 — `TM-01` controlled: `-n` applied with the proxy's replacement, and the re-probe

*Claude, in the same session and branch, at the request of the session coordinating the hub sitting,
from about 00:30 UTC. The apply and `./aws/proxy.py --on-host` are that session's, relayed, `--on-host` on
the user's word; the re-probe is the user's, from a space, relayed with its log lines. AWS calls by this
session: EC2, Route 53 and CloudWatch reads in Production as the infrastructure user (`awsds-infra-prod`,
`InfrastructureAccess`), no write. Times are UTC.*

- **[The coordinating session, relayed] The apply**: `production/proxy/` from `main` at `65254241`,
  which carries #351's `-n` and #354's `t3.small`, 2026-11-21 23:51:42 to 23:53:26, `1 added, 2 changed,
  1 destroyed`, re-plan `No changes`. The new host `i-071bcc561f75b51d7`, `10.31.160.128`, printed the
  render's steps (2) to (4) with no `FAILED` line, started Squid and printed `done - the proxy is up`
  (Stage 12's log of 2026-11-22).
- **[The coordinating session, on the user's word, relayed] `./aws/proxy.py --on-host`**, about 00:20:
  exit 0, `PX-1`, `PX-2` and `PX-3` pass, FLAGS reading `sandbox_foundation allowlist -n 42`.
- **[Relayed by the coordinating session]** The reverse record of `54.213.164.60` at 23:58:19:
  `ec2-54-213-164-60.us-west-2.compute.amazonaws.com.`, the record that passed on 2026-11-21.
- **[The user, relayed] The re-probe** at 00:20:41 from `jup` (`10.20.54.175`; `10.20.38.182` on
  2026-11-21): the two `curl`s of 2026-11-21 and Stage 12 2.2 step 5's positive control.
  `54.213.164.60` printed `CONNECT=403` and exit 56, `108.158.137.46` `CONNECT=403` and exit 56, and
  `pypi.org` `CONNECT=200 HTTP=200` and exit 0. The new instance's stream in `/awsds/prod/proxy`:
  - `00:20:41 ... CONNECT 54.213.164.60:443 403 3404 117 TCP_DENIED`
  - `00:20:41 ... CONNECT 108.158.137.46:443 403 3406 119 TCP_DENIED`
  - `00:20:42 ... CONNECT pypi.org:443 200 49005475 1208 TCP_TUNNEL`
- **[Claude] What the reading says**: the address that passed by its reverse record on 2026-11-21 is
  refused with the record unchanged, while one of the 42 names tunnels from the same space a second
  later, so the list is loaded and the address falls to `deny all`. `108.158.137.46` reads `403` as it
  did, its record being under `cloudfront.net`. `TM-01` is controlled. What reopens it is an allow-list
  plane read without `-n` under FLAGS, or a raw public address read `200` in the access log.
- **[Claude] Read back** from 00:39:49 to 00:40:14: `proxy.awsds.internal` an `A` record at
  `10.31.160.128`, TTL 60, and `awsds-prod-proxy` a running `t3.small` at that address, launched 23:52:54.
- **[Claude] Records**: `threat-model.md`'s `TM-01` row and its channel row read controlled, and the
  paragraph naming the plane edits no longer lists it; `NETWORK.md` §5's paragraph says the flag is
  applied; the Stage 11 `Status` row.

## 2026-11-22 — `TM-28`'s controls written and planned: the `Interactive` OU's SCP and the targets' fence

*Claude, in a session of its own on the branch `claude/tm28-agentcore-controls-6e013a`, at the request of
the session coordinating 2026-11-22's batch, from about 06:30 UTC. The layer of the Sandbox deny is the
user's, answered on a card in this session. AWS calls by this session, all reads: IAM, Access Analyzer's
`validate-policy`, `simulate-principal-policy` and AgentCore reads in Sandbox Account 1
(`awsds-infra-sandbox-1`); IAM reads and the plans in Staging and Production; the plan in Identity. Each
ran as the infrastructure user (`InfrastructureAccess`). No apply. Times are UTC.*

- **[The user] The layer**: *"SCP da OU Interactive"*. The deny goes in `awsds-org-scp-ou-interactive`,
  which binds every principal of the `Interactive` accounts, rather than in Sandbox's project boundary.
- **[Claude] The service reference**, read 06:39, `bedrock-agentcore` and `agent-registry` at `v1.5`:
  `*CodeInterpreterSession` matches Start, Get and Stop, and `*BrowserSession` the same three.
  `InvokeWebAnswer` acts on `tool/web-answer.v1`, which v48 does not grant; the statement names it too.
  The reference and v48 disagree on the resources of `InvokeWebSearch` and
  `ConnectBrowserAutomationStream` (`SUP-451`), so the statement is on `Resource: "*"`. `agent-registry` is
  a prefix of its own, 32 actions on `publisher`, `registry` and `registry-record`, which
  `bedrock-agentcore:*` does not cover.
- **[Claude] The validation**, 06:46: `validate-policy --policy-type SERVICE_CONTROL_POLICY` returned no
  finding on the statement, its mid-action wildcards included. The negative control,
  `InvokeWebSearchNoSuchAction` and `*NoSuchSessionKind`, returned `ERROR INVALID_ACTION` each. The amended
  document returns one finding, `athena:UpdateSession does not exist`, the hedge `POLICIES.md` records.
- **[Claude] The allowed answers**, Sandbox Account 1, about 06:43, with no deny in place: a get on a
  session that does not exist answered `ResourceNotFoundException` *"Session not found"* on both managed
  tools, a get on a tool that does not exist *"Code Interpreter not found"* and *"Browser not found"*, and
  `get-agent-runtime` `ResourceNotFoundException`; `list-agent-runtimes` listed no runtime.
- **[Claude] The simulation**, 06:52, as `eighth-experimentation`'s project role under its boundary
  `awsds-sandbox-project-boundary` v3, with `aws:RequestedRegion` `us-west-2` and the project tag in the
  context (`SUP-008`):
  - Run A, today: the code interpreter's Start, Get, Stop and Invoke and the browser's Start, Get and Stop
    read `allowed`, each by `SageMakerStudioProjectRoleMachineLearningPolicy`. `InvokeWebSearch` reads
    `allowed` on the grant's `aws:tool/web-search.v1` and `implicitDeny` on the reference's spelling with
    the account. `InvokeWebAnswer` reads `implicitDeny`. `ConnectBrowserAutomationStream` reads
    `implicitDeny` on `*`, Organizations and the boundary allowing, and on `aws:browser/*`, where the
    simulator returns neither verdict. The eight runtime actions read `allowed`.
  - Run B, the boundary's v3 document with the statement appended, passed as
    `--permissions-boundary-policy-input-list` in the SCP's place: `explicitDeny` on every tool action,
    both web search spellings and the stream on `*` included (on `aws:browser/*` the simulator still
    returns no verdict), and `allowed` on the eight runtime actions.
- **[Claude] The plans**, from this branch at `main`'s `82edff32` with the edits, Terraform 1.17.2,
  `-input=false -detailed-exitcode`, exit 2 each:
  - `identity/org-policies/`, ended 06:55:49: `0 to add, 1 to change, 0 to destroy`,
    `aws_organizations_policy.this["awsds-org-scp-ou-interactive"]`, its content gaining
    `DenyAgentCoreBuiltInTools` and its description the `TM-28` sentence.
  - `staging/studio/` and `production/studio/`, ended 06:56:33: `0 to add, 2 to change, 0 to destroy`
    each. `module.sagemaker_prereqs.aws_iam_policy.project_boundary` gains `"agent-registry:*"` in
    `DenyServicesNoProjectUsesHere`, 6d decision 17's fence, and `aws_iam_policy.person_session` reads its
    document `(known after apply)` (`SUP-356`), so each apply is expected to read `0 added, 1 changed` and
    its re-plan `No changes`. Both boundaries read `v4` today.
- **[Claude] The plans again**, after `main` at `65401691` (#370) was merged into this branch, a merge that
  touches none of the three slices: the same actions line for line, exit 2 each, `identity/org-policies/`
  ended 07:09:04, `production/studio/` 07:09:10 and `staging/studio/` 07:09:15.
- **[Claude] The sizes**: the amended document is 1874 characters minified, five statements, under the
  5120 its precondition enforces; the description is 508 characters, under Organizations' 512, which no
  plan reads.
- **[Claude] The battery's rows**, eight in `aws/probes/probes.py`'s `ou` phase, 67 rows from 59: four
  denies in Sandbox Account 1 (the two gets `ro`, the two starts `blocked`), the two starts in
  `Policy Canary` as the contrast, and two runtime allows in Sandbox Account 1 (`get-agent-runtime` `ro`,
  `invoke-agent-runtime` `blocked`). Each argv parsed against a closed local port; none reached AWS.
  `InvokeCodeInterpreter`, `InvokeWebSearch`, `InvokeWebAnswer` and `ConnectBrowserAutomationStream` have
  no row (`SUP-451`); the simulation in `scp-battery.md`'s `TM-28` amendment reads them after the apply.
- **[Claude] Records**: `POLICIES.md`'s row; `threat-model.md`'s `TM-28` row and its channel row;
  `AWS_STATE.md` §C; `scp-battery.md`'s `TM-28` amendment under phase 4b; `SUP-451`; `REFERENCES.md`;
  Stage 17's 10.5 and its AgentCore paragraph; the comment in `aws/deploytargets.py`; the Stage 11
  `Status` row.
- **[Claude] Owed**, each apply on the user's word naming it: `identity/org-policies/`, `staging/studio/`
  and `production/studio/`; then the battery's `--phase ou` and the simulation, and `agent-registry` in
  `deploytargets.py`'s `FENCED_SERVICES` in the commit after the two studio applies (Lesson 50).
