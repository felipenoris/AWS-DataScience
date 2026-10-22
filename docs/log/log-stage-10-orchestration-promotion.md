# Log — Stage 10 — Workflow orchestration and promotion

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-10-orchestration-promotion.md`](../plan/stages/stage-10-orchestration-promotion.md).
Account ids are replaced by the account's name in angle brackets. The decisions this stage records as taken
before this file existed were taken in other sittings, and their logs carry them: Stage 8's for its
decisions 22 and 23, and [D41](../plan/decisions/D41-sagemaker-application.md) for decisions 13 to 18.*

---

## 2026-10-18 — pass 0 read, and step 4.3's deny applied

*Claude's hand, in the session "Execução local no Mac", as the infrastructure user (`InfrastructureAccess`).
The user's authorization, in that chat: "Você está autorizado a utilizar leituras com usuário sso infra e
realizar os applies necessários de terraform", and "Autorizo os applies de SCP em identity/org-policies das
Stages 9 e 10 e a bateria de SCP depois de cada um". The environment was down throughout.*

- **[Claude] 0.1.** `./aws/cicd.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`: every check
  passed, `CI-2` and `CI-3` on the four deploy roles. `./aws/deploytargets.py`, read after Stage 9's pass 1
  was applied the same afternoon: `DT-3`, `DT-4`, `DT-5`, `DT-7`, `DT-9`, `DT-10` and `DT-11` pass; `DT-1`,
  `DT-2`, `DT-6` and `DT-8` are notes Stage 9's pass 3 and later passes clear.
- **[Claude] 0.2.** `awscc_mwaaserverless_workflow` exists in `hashicorp/awscc` v1.106.0, the newest
  release, read from its schema in a scratch directory with no slice touched: `code` (`s3_location`),
  `definition_s3_location` (`bucket`, `object_key`, `version_id`, required), `network_configuration`
  (`security_group_ids`, `subnet_ids`), `logging_configuration` (`log_group_name`),
  `encryption_configuration` (`kms_key_id`, `type`), `trigger_mode`, `role_arn` (required),
  `schedule_configuration`. Both live locks still read 1.98.0, so 1.1's `code` needs a lock bump.
  The CLI half: `aws-cli/2.37.12` carries `mwaa-serverless create-workflow` with `--code`,
  `--network-configuration` and `--trigger-mode`.
- **[Claude] 0.3, the service-linked-role baseline.** `aws iam get-role --role-name
  AWSServiceRoleForAmazonMWAAServerless` answers `NoSuchEntity` in Production and in Staging, and no
  service role named for MWAA or Airflow exists in either. In `Sandbox Account 1` the role exists since
  2026-08-27T18:57:09Z. Staging's absence is recorded before Stage 18's first CLI deploy, which would
  create it there.
- **[Claude] 4.3 written.** `DenyProvisionedMwaa`, `airflow:CreateEnvironment` on `*`, joins
  `awsds-org-scp-baseline` as its thirteenth statement, with its `POLICIES.md` row and a `root` battery
  row run in Production (the call names two subnets, and `Policy Canary` has none). The document's
  description now also names 5b's two Redshift statements, which it omitted.
- **[Claude] 4.3 applied.** `identity/org-policies/` as `awsds-infra-identity`: plan 0 to add, 1 to change,
  0 to destroy, `aws_organizations_policy.this["awsds-org-scp-baseline"]` (`p-1fp032g8`) in place,
  content and description, `policy_document_bytes` 2944 → 3042. Apply 20:12:46-20:12:56 UTC, *"Apply
  complete! Resources: 0 added, 1 changed, 0 destroyed."*; re-plan *"No changes."*; `describe-policy` reads
  13 statements, the last `DenyProvisionedMwaa`. Every peer session was told before the apply.
- **[Claude] The battery after the apply**, `./aws/probes/scp-battery.py --phase root`, started 20:13:28 UTC
  (the driver stamps the laptop's clock), the new row verbatim with the phase's totals:

  ```
  SCP battery - 2026-10-18 17:13:28  (phase root)
    MARK PHASE    ACCOUNT   EXPECT OUTCOME       DETAIL                 PROBE
    ok   root     prod      deny   DENY-SCP      p-1fp032g8             airflow:CreateEnvironment (no such role, bucket or security group)
  25 as expected, 0 unexpected, 0 not measured
  ```

  The deny names the baseline, so the action authorizes before it validates the network configuration.
  The allowed side, the same call answered by validation with no deny, was not read before the apply.
- **[Claude] `OR-6`.** `./aws/orchestration.py`: *"none in 6 account(s) read"*. The other rows are the
  notes a stage that has not started reads: no workflow in Staging or Production, no approval rule yet.
- **[Claude] Left for later, by the plan's order.** 1.2's bump of `production/workloads/` and
  `staging/foundation/` to `vpc-v0.4.0` is pass 2's, and it would open the S3 gateway endpoint to the
  service's code bucket with no consumer yet. Pass 1 and pass 2 run with Stage 8's pass 4, after Stage 9
  (Stage 8 decision 23).

## 2026-10-18 — verification xxvii's first clause offline, and step 5.3 written and planned

*Claude's hand, in a task the orchestrating session ran on the laptop (branch
`claude/stages-09-10-18-readings`), with the environment down. The calls are reads and plans, as the
infrastructure user (`InfrastructureAccess`) through `awsds-infra-prod`, the plan also reading as
`awsds-infra-data` and `awsds-infra-sandbox-1`; nothing was applied. Times are UTC.*

- **[Claude] Verification xxvii, the first clause: `bundle` offline.** The CLI is the laptop's
  `aws-smus-cicd-cli` 1.0.9, a uv tool; nothing was downloaded. Over a copy of `examples/app-etl/` at
  `28f340c`, with `code/app-etl.zip` built as `build-task-code` builds it (`python3 -m zipfile`, 1,246
  bytes), no AWS credential (`AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` on missing paths, the
  proxy variables on a closed port) and fabricated values for the manifest's shell variables, `bundle
  --manifest manifest.yaml --targets test`, the call `test-deploy` makes, at 22:28:58: three `ERROR` lines on
  the domain lookup (*"Unable to locate credentials"*), each of the five storage items bundled *"from local
  files"*, and *"Bundle created: ./artifacts/app-etl.zip (6988 bytes)"*, seven files: `code/app-etl.zip`,
  `glue/transform.py`, `samples/trades.csv`, three under `src/app_etl/` and `workflows/app-etl.yaml`. The
  size is 20 bytes above Stage 8's offline run of 2026-10-16, before PR #156 added the `process` task's
  `VolumeKmsKeyId` line to the YAML [inferred].
- **[Claude] What the bundle carries.** Every file equals its source, and `workflows/app-etl.yaml` is
  byte-identical to the checkout's (sha256 `d367ab291ddc…`): its 25 CLI variables stand unresolved,
  `{proj.connection.default.s3_shared.s3Uri}` 9 times, `{proj.id}` 6, `{proj.iam_role_arn}` 2,
  `{env.SUBNET_AZ1}` 2, `{env.SUBNET_AZ2}` 2, and `{env.PROJECT_SG}`, `{env.PROJECT_KEY_ARN}`,
  `{env.JOB_IMAGE_URI}` and `{domain.region}` once each, beside the two Airflow templates; no fabricated
  value reached it, and no `{env.*}` became a `{{ params.* }}`, which `workflow.create` writes at deploy
  (2.2). The branch is `commands/bundle.py` line 201: a storage item that names a `connectionName` is
  downloaded from the stage's project, one that names none is copied from the manifest's folder (lines
  232-261), and `app-etl`'s `content.storage` items name none. The connection clause and `deploy`'s clause
  need a project and are unread.
- **[Claude] 5.3, read for what holds it.** The pass table puts step 5 in pass 3. The stage orders pass 1
  before pass 2 (the snapshot) and Stage 18's verdict before pass 2, and gives pass 3 no dependency of its
  own; the open decisions (1 to 5, 8, 9, 11 and 12) concern other steps. The rule needs
  `production/sagemaker/`, applied today (Stage 9 3.4), and `awsds-prod-alerts`, whose policy admits this
  account's EventBridge rules (`EventBridgeRulesOfThisAccount`). What it watches first appears at 5.2, and
  until then it costs nothing. So it was written ahead of its pass.
- **[Claude] 5.3 written.** `production/sagemaker/registry.tf` gains `awsds-prod-model-approval`, state
  `ENABLED` (`OR-4` fails any other), its pattern source `aws.sagemaker` and detail-type `SageMaker Model
  Package State Change` with no group named, tagged `CostCenter` `stage-10`; and its target `alerts-topic`,
  `awsds-prod-alerts` read from `foundation/`'s state as `debug.tf`'s targets are, through an input
  transformer naming the time, the group, the version, the two statuses, the package ARN and the event id,
  none of them free text a caller writes. The field names are the example event's on AWS's page, read again
  today (`docs/REFERENCES.md`). `conventions.md` §6 names the rule in the slice's row.
- **[Claude] 5.3 planned**, `-input=false`, as `awsds-infra-prod`. Before the edit, the baseline: *"No
  changes. Your infrastructure matches the configuration."* (22:34Z). After it, 22:35:10-22:35:22: *"Plan: 2
  to add, 0 to change, 0 to destroy."*, `aws_cloudwatch_event_rule.model_approval` and
  `aws_cloudwatch_event_target.model_approval`, nothing else, the plan saved outside the repository. The
  apply is the orchestrating session's; owed after it are the re-plan, `./aws/orchestration.py`'s `OR-4` on
  the rule, and `./aws/deploytargets.py`'s `DT-3` and `DT-5` (Validation 3).
- **[Claude] Verifications iii and xiii marked** with this file's 0.3 and 4.3 readings; no call was made for
  them.
- **[Claude] Three gaps of the pinned lint, given to this stage.** The orchestrating session relayed the
  Stage 8 task's reading of `awsds-workflows` at `3c1708e` (PR #186, open, whose Stage 8 5.6 table names an
  owner for each clause the template's line leaves off), and each was read again in that commit's code
  through `gh api`. `cli.py`'s `lint` hands `--instance-type` and `--image-repository` to a rendered file's
  checks only when given, so 2.3's promoted command passes the template's two options; `lint.py`'s
  processing and code-input checks return on any operator but `SageMakerProcessingOperator`, and its image
  rule reads `ImageUri` keys, so 5.1's training task is unchecked, and 1.3's "the lint checks each" now
  says a processing job's; and no rule compares a code input with the release's manifest, so 2.4's release
  job reads `src/` back against it.

## 2026-10-18 — step 5.3's rule applied

*Claude, the orchestrating session of 2026-10-18's third round, from the laptop as the infrastructure
user (`awsds-infra-prod`, `InfrastructureAccess` in `Production`), on the user's word in its chat ("Pode
rodar os applies necessários"). The same apply had been refused to this session by the auto-mode
classifier (*Production Deploy*) an hour earlier, before that word.*

- **[Claude] The apply**, of the plan saved by the previous entry from `production/sagemaker/` on the
  branch PR #188 merged: 23:19:10Z, `aws_cloudwatch_event_rule.model_approval` and
  `aws_cloudwatch_event_target.model_approval` created, *"Apply complete! Resources: 2 added, 0
  changed, 0 destroyed."*
- **[Claude] Read back**: the re-plan with `-detailed-exitcode` exits 0, *"No changes"*;
  `events describe-rule` reads `ENABLED` with the pattern `source = aws.sagemaker`, `detail-type =
  SageMaker Model Package State Change`; `list-targets-by-rule` names one target, `alerts-topic`, the
  topic `awsds-prod-alerts`.
- **[Claude] The instruments**: `./aws/orchestration.py` reads `OR-4` *"prod: rule
  awsds-prod-model-approval ENABLED"* `pass` and `OR-6` `pass`; `./aws/deploytargets.py` reads `DT-3`
  `pass` (the group policy, three statements) and `DT-5` `fail` on Production's create-defaults, Stage 9
  step 1.3's, as `AWS_STATE.md` section C records. Both exit 1 on calls alone: the `get-caller-identity`
  of the persona, deploy and Control Tower profiles, whose SSO sessions were not signed in.
- **[Claude] Not yet read**: a notification, since no model package exists in Production; Stage 12
  step 2.4's provocation is the first.

## 2026-10-19 — 1.2's bump of `staging/foundation/`, applied in Stage 18's window

- **[Claude] Written and planned in Stage 18's session**, because Stage 18's 4.4 runs a workflow with a
  Python task's `Code` in Staging ([Stage 18's log](log-stage-18-staging-deployment-project.md)):
  `staging/foundation/` pins `vpc-v0.4.0`, whose one functional change is the S3 gateway default list
  gaining `mwaa-serverless-code-files-*-<region>-prod`; the plan changed the gateway endpoint's policy
  alone. `production/workloads/` stays on `vpc-v0.3.1`.
- **[user] Applied** as `awsds-infra-staging` from the saved plan: *"Apply complete! Resources: 0
  added, 1 changed, 0 destroyed."* **[Claude]** The re-plan reads `No changes` (05:12:11Z); the
  endpoint's `AllowAwsOwnedServiceBuckets` holds the family's bucket and object ARNs, and `EG-4` reads
  `mwaa-code` in Sandbox and Staging since its pattern was added that day.

## 2026-10-20 — step 1.3's training operator, read in the provider's code

*Claude's hand, written in a task the orchestrating session started (branch
`claude/stage-10-log-reads-94955a`) for PR #210, merged the same day, which added no entry. That PR's
session made the reading from the Amazon provider's source on GitHub at the tag `providers-amazon/9.32.0`,
with no AWS call; this sitting read each clause again at the tag.*

- **[Claude] 1.3, `SageMakerTrainingOperator`**, in `operators/sagemaker.py`, `hooks/sagemaker.py` and
  `hooks/s3.py`: while `check_if_job_exists` is true, the default, `DescribeTrainingJob` runs on the
  config's `TrainingJobName` before `CreateTrainingJob`, and only a `ValidationException` counts as absent;
  `action_if_job_exists` takes `timestamp`, the default, or `fail`. Before the create, the hook heads each
  `S3DataSource` channel's bucket (`HeadBucket`), then its key (`HeadObject`) or prefix (`ListObjectsV2`);
  while `print_log` is true, the default, it reads `/aws/sagemaker/TrainingJobs` (`DescribeLogStreams`,
  `GetLogEvents`). 1.3's grant listed neither the S3 heads nor the log reads. No code in either SageMaker
  operator or in `SageMakerHook` stops a training or processing job. Step 1.3 carries the consequences.

## 2026-10-20 — verification iii: the service-linked role read in Staging and Production

*Claude's hand, in the same task, from the laptop as the infrastructure user (`InfrastructureAccess`)
through `awsds-infra-staging` and `awsds-infra-prod`, reads only, with the tunnel down (`NO_PROXY='*'`).
Times are UTC.*

- **[Claude] Staging, the role** (21:59:35Z): `iam get-role --role-name
  AWSServiceRoleForAmazonMWAAServerless` reads the path `/aws-service-role/airflow-serverless.amazonaws.com/`,
  `CreateDate` 2026-10-19T20:09:32Z, `RoleLastUsed` 2026-10-19T23:09:41Z in `us-west-2`, no boundary and no
  tags; the trust is one statement, `airflow-serverless.amazonaws.com` with `sts:AssumeRole` and no
  condition. `list-attached-role-policies` names `AmazonMWAAServerlessServiceRolePolicy` alone, and
  `list-role-policies` none.
- **[Claude] Staging, the policy**: `get-policy` reads `DefaultVersionId` `v1`, created and updated
  2025-11-15T20:34:07Z, `AttachmentCount` 1, and `list-policy-versions` holds `v1` alone. `get-policy-version`
  of `v1` is one `Allow` statement on `*` with no condition and no `Sid`, eleven actions, all `ec2:`:
  `AttachNetworkInterface`, `CreateNetworkInterface`, `CreateNetworkInterfacePermission`,
  `DeleteNetworkInterface`, `DeleteNetworkInterfacePermission`, `DescribeDhcpOptions`,
  `DescribeNetworkInterfaces`, `DescribeSecurityGroups`, `DescribeSubnets`, `DescribeVpcs`,
  `DetachNetworkInterface`.
- **[Claude] Staging, who created it**: `cloudtrail lookup-events` in `us-east-1` over the 90-day window
  holds one `CreateServiceLinkedRole` naming `airflow-serverless.amazonaws.com`, 2026-10-19T20:09:32Z,
  `invokedBy` `airflow-serverless.amazonaws.com` with the InfrastructureAccess session as its identity, and
  no `DeleteServiceLinkedRole`. In `us-west-2` the window's first `CreateWorkflow` is the same second's,
  `app_etl_deploy_staging_app_etl`, inside Stage 18's 4.2 deploy (20:07:34 to 20:09:33Z); the four after it,
  21:20:59Z to 21:59:48Z, the last two answered `ConflictException`, made no second
  `CreateServiceLinkedRole`.
- **[Claude] Production** (22:00:12Z): `get-role` *"An error occurred (NoSuchEntity) when calling the
  GetRole operation: The role with name AWSServiceRoleForAmazonMWAAServerless cannot be found."*;
  `list-roles` under the service's path is empty, the policy's `AttachmentCount` 0, `mwaa-serverless
  list-workflows` empty, and the trail's 90 days hold no `CreateWorkflow`.
- **[Claude] Production, the saver of 1.5**: `awsds-deploy-prod` carries one inline policy, `state`, no
  attached policy, and the boundary `awsds-prod-deploy-boundary` at `v1`. `iam simulate-principal-policy` for
  `iam:CreateServiceLinkedRole` on the service-linked role's ARN, with `iam:AWSServiceName`
  `airflow-serverless.amazonaws.com`, reads `implicitDeny`, allowed by the boundary and by Organizations,
  no statement matched; `airflow-serverless:CreateWorkflow` reads `implicitDeny` as well, a grant 1.5 adds.
- **[Claude] `./aws/orchestration.py awsds-infra-staging awsds-infra-prod`**, 22:04:58Z, exit 2: section 9
  reads Staging *"present, created 2026-10-19T20:09:32"* and Production absent; `OR-4` and `OR-6` pass;
  `OR-2` fails four times on Staging's three `/aws/mwaa-serverless/` log groups with no retention
  (`app_etl_deploy_staging_app_etl`, `dagid_copy_deploy_staging_app_etl`,
  `orchestration_demo_deploy_staging_demo_python_operator`), which Stage 18's deploys left, as its log
  records.
- **[Claude] Written into the stage file**: verification iii's Staging half, and in 1.5 what the trail
  means for Production: Staging's first save created the role in the saver's session, so Production's first
  apply needs `iam:CreateServiceLinkedRole` in `awsds-deploy-prod`'s policy unless the role exists by then.

## 2026-10-22 — the stage prepared with the environment down: readings, the module, both slices, two corrections

*Claude's hand, in the session "stage-10-prep" (branch `claude/stage-10-prep-91b561`), started by the
orchestrating session "Pendências estágios 7 e 8" on the user's request in that chat: "Revise o plano dos
estágios 8, 9 e 10 [...] Faça a preparação necessária para todas as etapas dos estágios 8, 9 e 10 que
forem possíveis de serem preparadas e que não precisam da minha intervenção ou decisão". AWS read as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`,
`awsds-infra-sandbox-1`), reads and plans only, with the tunnel down (`NO_PROXY='*'`); nothing was
applied. Times are UTC.*

- **[Claude] `./aws/orchestration.py awsds-infra-staging awsds-infra-prod awsds-infra-sandbox-1`**, before
  any edit: exit 0, *"all checks passed"*. `OR-1` notes no workflow in either account, `OR-4` passes on
  `awsds-prod-model-approval`, `OR-6` reads *"none in 3 account(s) read"*. `OR-2`'s four failures of
  2026-10-20 are gone: Stage 18's pass 8 deleted Staging's three `/aws/mwaa-serverless/` groups.
- **[Claude] The objects other stages create**, 04:53:34Z. Staging: `AWSServiceRoleForAmazonMWAAServerless`
  created 2026-10-19T20:09:32Z, last used 2026-10-22T00:32:11Z; no workflow; `awsds-staging-app-boundary`
  `NoSuchEntity`; `awsds-staging-deploy-boundary` at `v1`; `awsds-staging-job-exec` `NoSuchEntity`;
  `alias/awsds-staging-data` *"is not found"*; `awsds-staging-outputs` `404`. Production: the
  service-linked role `NoSuchEntity`; no workflow; `awsds-prod-app-boundary` `NoSuchEntity`;
  `awsds-prod-deploy-boundary` at `v1`; `awsds-prod-job-exec` created 2026-10-18T19:59:03Z with no boundary;
  `alias/awsds-prod-data` *"is not found"*, `alias/awsds-prod-registry` `Enabled`; `awsds-prod-outputs`
  `404`.
- **[Claude] The registry's `AWS::MWAAServerless::Workflow`** (`cloudformation describe-type`, created
  2025-11-28): create-only `Name` and `EncryptionConfiguration`; read-only `WorkflowArn`, `WorkflowVersion`,
  `ScheduleConfiguration`, `WorkflowStatus` and the times; `TriggerMode` a string of 1 to 255 characters.
  The create handler's permissions: `s3:GetObject`, `s3:GetObjectVersion`, `logs:CreateLogGroup`,
  `logs:DescribeLogGroups`, `iam:GetRole`, `iam:PassRole`, `airflow-serverless:CreateWorkflow`,
  `GetWorkflow`, `TagResource`, `iam:CreateServiceLinkedRole`, `kms:CreateGrant`, `kms:GenerateDataKey`;
  read: `GetWorkflow`, `ListTagsForResource`, `kms:Decrypt`; update: create's but `CreateWorkflow` and
  `CreateServiceLinkedRole`, with `UpdateWorkflow` and `UntagResource`; delete: `GetWorkflow`,
  `DeleteWorkflow`, `UntagResource`. 1.5's list lacked `s3:GetObjectVersion`, which a pinned version
  needs, and the read handler's `Decrypt`.
- **[Claude] The service's event names.** The schema registry `aws.events` holds no `aws.airflow-serverless`
  schema (the prefix `aws.airflow` lists provisioned MWAA's alone). EventBridge's reference page lists
  fifteen detail types, each prefixed: *"MWAA Serverless Workflow Run Failed"*, *"MWAA Serverless Workflow
  Run Timeout"* and thirteen more; an example event on a third-party page reads `"detail-type": "MWAA
  Serverless Workflow Run Succeeded"`, its detail carrying `accountId`, `workflowRunId`, `workflowArn`,
  `status` and `workflowId`. Step 3.1 named `Workflow Run Failed` and `Workflow Run Timeout`, which no event
  carries.
- **[Claude] The Cloud Control API's IAM prefix**, AWS's security page for it: *"You must prefix the action
  name with the lowercase string `cloudformation:`"*, and it supports no resource-level permission. Step 1.5
  said `cloudcontrol:*Resource*`.
- **[Claude] The API model** (botocore's `mwaa-serverless` 2024-07-26, read in the laptop's uv cache):
  `StartWorkflowRun` takes `WorkflowArn` (required), `ClientToken` (1 to 128 printable characters),
  `OverrideParameters` and `WorkflowVersion`, and returns `RunId`, `Status` and `StartedAt`; `GetWorkflowRun`
  returns `RunDetail.RunState`, one of `STARTING`, `QUEUED`, `RUNNING`, `SUCCESS`, `FAILED`, `TIMEOUT`,
  `STOPPING`, `STOPPED`. `hashicorp/awscc` v1.107.0 and `hashicorp/aws` 6.70.0 are the newest releases.
- **[Claude] Written**, in two commits: `e9f0c9a7`, the module `terraform-modules/orchestration/`; `7afbc554`,
  `staging/orchestration/` and `production/orchestration/` with `chains/app-etl.asl.json`, `release.tf` and
  their locks (three platforms), `RANKS["orchestration"]` 59 and two `[E]` rows in `layers.py`, the folder
  and zone ids in `backend.py`, `OR-9` and `OR-4`'s pattern check in `./aws/orchestration.py`, and the
  workers' group in `docs/NETWORK.md`. `make check` reads `check: OK`; checkov passes the module with
  fourteen skips, each with its reason.
- **[Claude] The slices planned**, `-input=false`, as `awsds-infra-prod` and `awsds-infra-staging`, the
  module by path. With no release, at 05:16:08Z, both *"No changes. Your infrastructure matches the
  configuration."* With a stand-in release (`v0.0.0`, version ids `stand-in`), each stops at its lookups:
  Production *"reading IAM Policy (arn:aws:iam::<Production>:policy/awsds-prod-app-boundary): couldn't find
  resource"* and *"reading KMS Alias (alias/awsds-prod-data): empty result"*; Staging the same two for its
  names and *"Unable to find remote state"*, `staging/sagemaker/`'s. Nothing was saved for an apply: the
  pipeline applies these slices with a real release.
- **[Claude] A scratch caller of the module**, planned with local state as `awsds-infra-staging`: Staging's
  VPC, subnets and alerts topic from its state, stand-ins for the ceiling, the key, the job role and the
  objects, three workflows (`app-etl`, decision 18's check, a training one), the chain and a bridge: *"Plan:
  35 to add, 0 to change, 0 to destroy."* Each execution role's policy is known at plan, with only the
  statements its entry asks for.
- **[Claude] The chain's definition validated**, 05:18:30Z, `stepfunctions validate-state-machine-definition
  --type STANDARD` as `awsds-infra-staging`, on `chains/app-etl.asl.json` rendered with a stand-in ARN:
  `"result": "OK"`, no diagnostic. Three negative controls, each `"FAIL"` with `SCHEMA_VALIDATION_FAILED`:
  `mwaaserverlessX` and `getWorkflowRunX`, *"The resource provided
  arn:aws:states:::aws-sdk:mwaaserverlessX:getWorkflowRun is not recognized. The value is not a valid
  resource ARN, or the resource is not available in this region."* and the same for the action; `RunId`
  removed, *"The field 'RunId' is required but was missing"*.
- **[Claude] The module's tag.** `git ls-remote --tags origin 'orchestration-*'` read nothing. The push of
  the branch with `orchestration-v0.1.0` was refused by the auto-mode classifier (*Out-of-Place
  Publication*), and the next command reading the local tags was refused the same way; no tag exists, local
  or on origin. The slices pin the module by path until the user authorizes the tag.
- **[Claude] `./aws/orchestration.py`** after the edits, 05:21:22Z: exit 0; `OR-9` notes *"nothing
  awsds-staging-chain\* exists - expected before pass 2"*, and the same for Production.
- **[Claude] Told the Stage 9 session**, which holds `production/workloads/`, both egress slices and the
  data slices: the `mwaa` group stays empty; the statements `production/data/` and `staging/data/` owe this
  stage, decision 12's deny exempting `InfrastructureAccess` beside the deploy role; and what
  `awsds-staging-job-exec` needs (Production's shape, its two outputs by the same names).
- **[Claude] The plan revised**: the status and prerequisites; 0.2, 1.1 to 1.5 (the grant enumerated for
  Stage 8), 2.3's and 5.1's lint rules and 2.4's comparison with the manifest, specified; 3.1's detail types,
  3.4 to 3.7; the decisions' state (1, 5, 8 and 12 awaiting confirmation, 2, 3, 4, 9 and 11 open), decisions
  19 and 20 written with their recommendations, and decision 6's render table; verifications iii, vi, xvi,
  xxii and xxv; a risk on the two accounts' endpoint sets.

## 2026-10-22 — the Stage 9 session's answer: Production's bump planned, the two endpoint sets equal

*Claude's hand, the same session, recording the Stage 9 session's message ("Stage 9 — revisão e
preparação", PR #245), with no AWS call of its own.*

- **[Claude] 1.2 item 4, as that session reported**: `production/workloads/` pins `vpc-v0.4.0` in its commit
  `502b6da6`, planned as `awsds-infra-prod`, *"Plan: 0 to add, 1 to change, 0 to destroy."*,
  `module.vpc.aws_vpc_endpoint.s3` in place with the `mwaa-serverless-code-files-*` family added and the
  endpoint's id unchanged; not applied.
- **[Claude] The endpoint sets, corrected**: this file's entry above read `staging/egress/` before Stage 9's
  4.3a re-cut. That re-cut gives Staging exactly `VPC-Workloads`' six endpoints on `vpc-egress-v0.17.0`
  (`sts`, `logs`, `kms`, `glue`, `sagemaker.api`, `secretsmanager`), planned 15 to add, so neither
  deployment target carries `ecr.*` once it applies, and the Staging leg is the first run to read whether a
  worker needs them. 1.2, verification xvi and the risk say so now.
- **[Claude] The data slices and the job role**: the statements `production/data/` and `staging/data/` owe
  this stage are in that session's report, with decision 12's deny and the principal branch exempting the
  deploy role and `InfrastructureAccess`; `awsds-staging-job-exec` is written in Production's shape with
  outputs `job_role_arn` and `job_role_name`, its Glue trust statement without `aws:SourceAccount`, as
  Production's, planned 8 to add.

## 2026-10-22 — decision 20's network rows follow Stage 9 decision 12 (a)

*Claude's hand, the same session, on the orchestrating session's message that the user took Stage 9
decision 12 as recommended, option (a), the same day (that stage's PR #245 records it). No AWS call; no
Stage 10 decision was taken.*

- **[Claude] Decision 20 (b) and (c) settled by it**: the Glue network connection and the job security
  group are `[P]` in `*/sagemaker/`, outputs `glue_connection_name` and `job_security_group_id`, so the
  application slice declares the Glue job on that connection and declares neither object, and the
  processing job's `{env.PROJECT_SG}` renders as that group. The stage file's earlier recommendation of
  the day, one connection per subnet in the application slice and the private-tier group for the
  processing job, is withdrawn; decision 6's render table follows. Decision 20 stays open for (a), (d) and
  the tool. The orchestration slices' `applications` locals name no network object and are unchanged.

## 2026-10-22 — decision 1 taken by the user, revised: the bundle's tree under `applications/<app>/<tag>/`

*Claude's hand, the same session. The user took the decision in a fork of the orchestrating session
("Pendências estágios 7 e 8", PR #244), whose message relayed it; this session read the user's words and
the revised recommendation they answered in that session's transcript before recording it. No AWS call.*

- **[user] The decision**, in that session: *"Sim, peço registrar esta recomendação revisada e acatar esta
  como sendo a decisão tomada."*, answering a recommendation that the bundle stay intact in
  `awsds-prod-releases/<app>/<tag>/`, each leg extract exactly its tree under a prefix of the account's
  outputs bucket named after the application rather than `workflows/`, the rendered YAML be the only
  difference from the bundle, and `MANIFEST.sha256` show it.
- **[Claude] Recorded**: decision 1 taken, revised, with its four points; the prefix
  `workflows/<app>/<tag>/` became `applications/<app>/<tag>/` in the stage file (the contracts, 1.1, 1.5's
  grant, 2.3, 2.4 with the manifest naming the bundle's SHA256 of each file, 3.6, decisions 6, 7 and 12,
  the render table, verification xxi), in the module's validation of the roles' prefixes, in both slices'
  keys and `release.tf`, in `./aws/orchestration.py`'s `OR-5` (`DEF_PREFIX`), and in the lines of
  `aws/INDEX.md` and `docs/GOVERNANCE.md` that named the old prefix. The orchestrating session and the Stage
  9 session were told, for Stage 8 3.2 and 4.1 and for the two data slices' statements.

## 2026-10-22 — the module tagged `orchestration-v0.1.0`, the slices pinned to it

*Claude's hand, the same session, on the user's word in its chat: "Autorizo criar a tag
orchestration-v0.1.0 no commit 26bfc15d, publicá-la no origin e trocar os dois slices para
?ref=orchestration-v0.1.0." Plans as the infrastructure user (`awsds-infra-prod`, `awsds-infra-staging`);
nothing applied. Times are UTC.*

- **[Claude] Before tagging**: `git ls-remote --tags origin 'orchestration-*'` read nothing, and the
  module's last commit was `26bfc15d`, decision 1's prefix.
- **[Claude] The tag**: `git tag orchestration-v0.1.0 26bfc15d`, pushed alone; origin reads
  `refs/tags/orchestration-v0.1.0` at `26bfc15dfd02…`. The push the auto-mode classifier refused earlier
  the same day was this tag's, then on `e9f0c9a7`; the module changed twice since, so that commit was never
  tagged.
- **[Claude] The slices**: both `main.tf` pin `?ref=orchestration-v0.1.0`; `terraform init` downloads the
  module from the tag, and at 18:22:59Z each plan with no release reads *"No changes. Your infrastructure
  matches the configuration."* With the stand-in release each still stops at its lookups, as at 05:16Z:
  the application ceiling and the data key in both accounts, and `staging/sagemaker/`'s state in Staging.

## 2026-10-22 — decisions 5, 8 and 12 taken by the user, as recommended

*Claude's hand, the same session; the user's words relayed from the orchestrating session ("Pendências
estágios 7 e 8"), whose chat they were written in, and read again in that session's transcript. No AWS
call.*

- **[user] The confirmation**, the user's sentence over the orchestrator's list, which the user pasted:
  *"Confirmo estes itens:"*, *"Stage 10, para confirmar (o código já segue a recomendação): \* 5: a slice de
  orquestração é `[E]`. \* 8: o passo de contêiner é um processing job do SageMaker, não uma task ECS. \*
  12: os scripts Glue ficam sob o prefixo da release, `applications/<app>/<tag>/glue/`, com uma regra que
  proíbe escrita em `applications/*` a todos menos o papel de release e o `InfrastructureAccess`."*
- **[Claude] Recorded**: decisions 5, 8 and 12 marked taken, as recommended, in the stage file, with the
  decisions' state and the status. The code written earlier the same day already follows them. Open: 2, 3,
  4, 9, 11 and 19, and 20's (a), (d) and tool.

## 2026-10-22 — decisions 2, 3, 4, 9, 11, 19 and 20 taken by the user: every decision of the stage taken

*Claude's hand, the same session; the user's words relayed from the orchestrating session ("Pendências
estágios 7 e 8"), whose chat they were written in, and read again in that session's transcript. No AWS
call.*

- **[user] The decision**: *"Aceito as recomendações das decisões 2, 3, 4, 9, 11, 19 e 20 (a, d, e) do
  Stage 10, com a 20(d) como exceção explícita do template. Registre-as."* The orchestrating session had
  shown the user that 20 (d)'s seeding of `inbox/app-etl/` from the bundle's `samples/` meets Stage 9
  decision 3's rule that Staging holds no seeded or synthetic content, and the exception it proposed: the
  samples are `app-etl`'s own test input, a template with no producer, and no stand-in for governed data,
  and a real application names its governed source in its release.
- **[Claude] Recorded**: each of the seven taken, as recommended, 20 (d) with that exception in those
  terms, in the stage file's decisions, their state and the status; every decision of the stage is taken.
- **[Claude] What decision 11's grant needs, read in `identity/sso/policies-approvers.tf`**:
  `DeploymentManagerAccess`'s `DenyDataReadPaths` denies `kms:Decrypt` on `*` with no condition, and under
  decision 2 the workflow service decrypts in the reader's session at each `GetWorkflowRun` (Stage 18 0.4),
  so the six `airflow-serverless:` reads alone would be refused by the set's own deny. Decision 11's text
  now names the three statements that make them work: `kms:Decrypt` allowed with the
  `aws:airflow-serverless:workflow-arn` encryption context, the deny narrowed to requests without it, and
  the data key's policy naming the set's role. Which other reads decrypt is 3.2's reading.

## 2026-10-22 — decision 11's decrypt carve-out approved by the user and written in `identity/sso/`

*Claude's hand, the same session; the user's words relayed from the orchestrating session ("Pendências
estágios 7 e 8"), whose chat they were written in, and read again in that session's transcript. No AWS
call of this session's.*

- **[user] The approval**: *"Pode aprovar a exceção, conforme a recomendação."*, answering the carve-out
  decision 11's text named: `kms:Decrypt` for `DeploymentManagerAccess` only with the
  `aws:airflow-serverless:workflow-arn` encryption context, D31's decrypt deny narrowed to requests without
  that key, and `kms:ViaService` added once a trail shows the calls carry it.
- **[Claude] What the orchestrating session reported writing** (PR #244, `b35aae36`): in `deployment_manager`
  of `identity/sso/policies-approvers.tf`, `ReadWorkflowRunStatus`, `DecryptWhatTheWorkflowServiceEncrypts`,
  `DenyDecryptOutsideTheWorkflowService`, and `DenyDataReadPaths` without `kms:Decrypt`; planned as
  `awsds-infra-identity`, *"0 to add, 1 to change, 0 to destroy"*, the set's inline policy from 7,289 to
  8,223 characters of 10,240; not applied, the apply a row of `waiting-on-the-user.md`. In 1.5's grant,
  `EncryptTheWorkflows` became the twins of Stage 9's key-policy statements (the workflow key's `Decrypt`
  and `GenerateDataKey` by the workflow's ARN as context, `CreateGrant` for an AWS resource,
  `DescribeKey`), and the release job's copy writes `inbox/*`, decision 20 (d)'s seed; the access policy
  measures 4,490 characters in Staging of 6,144.
- **[Claude] Recorded** in decision 11 and in 1.5's grant.

## 2026-10-22 — the application ceilings applied; the slices' plans read again

*Claude's hand, the same session, after the orchestrating session reported its applies of
`production/foundation/`, `staging/foundation/` and `identity/sso/` on the user's authorization in its chat
(each re-plan `No changes`, `./aws/cicd.py` 0 FAILED). Reads and plans as the infrastructure user
(`awsds-infra-prod`, `awsds-infra-staging`); nothing applied. Times UTC.*

- **[Claude] The ceilings**, 19:32:28Z: `iam get-policy` reads `awsds-prod-app-boundary` at `v1`, created
  2026-10-22T19:27:16Z, and `awsds-staging-app-boundary` at `v1`, created 19:27:35Z.
- **[Claude] The slices**, from the tag: with no release, each plan reads *"No changes. Your infrastructure
  matches the configuration."* With the stand-in release, the application ceiling's lookup now passes, and
  each plan stops at Stage 9's objects alone: Production *"reading KMS Alias (alias/awsds-prod-data): empty
  result"*; Staging *"Unable to find remote state"* (`staging/sagemaker/`) and *"reading KMS Alias
  (alias/awsds-staging-data): empty result"*. The Stage 9 session began its applies of those objects at
  the same time, so no plan was taken after this one.
- **[Claude] Recorded**: the stage file's status, prerequisites, 1.5's grant and decision 11 say what is
  applied.

## 2026-10-22 — steps of this sitting the entries above leave out: the PR, 1.3's ceiling, 6.1's minute, 1.5's two policies

*Claude's hand, the same session, recording commits of the day whose steps no entry above names. No AWS
call.*

- **[Claude] The branch and the PR**: after the classifier refused the tag's push (the first entry of the
  day), the branch alone was pushed and PR #246 opened against `main`; every later commit joined it, and
  its one check, `pre-commit and make check`, passed. The exact statements for Stage 8's `*/foundation/`
  (1.5's grant and the application ceiling) and the texts for the shared files were handed to the
  orchestrating session, which writes them in PR #244.
- **[Claude] 6.1** (`5d713ea3`): Production's chain fires at 06:30 UTC and a run needs
  `production/workloads-egress/`'s `[E]` endpoints, so the sitting that proves the unattended run spans
  that minute with them up, or a commit moves the cron into the sitting.
- **[Claude] 1.3's sentence on the deploy role's ceiling** (`f435d8d7`, `411dc2b3`), on the orchestrating
  session's reading: the ceiling refuses `CreateRole` and the five role-policy writes on a role without the
  application ceiling, the actions `iam:PermissionsBoundary` is evaluated for, where 1.3, the module's
  header and its variable's description said every policy change. Text only; that module commit moved the
  tag's target from `e9f0c9a7` to `f435d8d7`, before decision 1 moved it to `26bfc15d`.
- **[Claude] 1.5's grant as two managed policies** (`8dd5e2e9`), on the orchestrating session's
  measurement: the grant is 7,836 characters in Staging, white space not counted, above the 6,144 a managed
  policy holds, and inline it would take Staging's role to 12,483 of the 10,240 IAM allows; PR #244 splits
  it into `awsds-<env>-deploy-orchestration-resources` and `-access`, and an amendment keeps each under
  6,144. 1.5 no longer says the statements are in this log.
- **[Claude] Decision 11's carve-out put to the user** (`007ff267`), before the approval an entry above
  records: a row of `waiting-on-the-user.md`, with `identity/sso/` waiting on the answer.
