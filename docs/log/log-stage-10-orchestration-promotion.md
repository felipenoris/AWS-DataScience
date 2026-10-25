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

## 2026-10-22 — the third sitting with the environment down: 2.3's lint wired into the legs, pass 3 placed behind the quotas

*Claude's hand, in the session `stages-8-9-10-review`, on the user's request quoted in Stage 8's entry of
the same sitting. AWS read as the infrastructure user (`awsds-infra-staging`, `awsds-infra-prod`,
`awsds-infra-sandbox-1`), reads only, the tunnel down. Nothing applied. Times UTC.*

- **[Claude] `./aws/orchestration.py`**, between 22:00 and 22:10: 0 FAILED; `OR-9` a note, nothing of
  the layer existing in either account.
- **[Claude] 2.3 wired**: Stage 8's release job runs the promoted lint on each rendered copy
  (`release-application.py --lint`, its entry in Stage 8's log), read offline on `v0.2.1`'s bundle
  against Staging's live state: the rendered copy `ok`, a `dev-env` image refused by the lint's image
  rule, an empty `LINT_INSTANCE_TYPES` refused by the script. The three rules this stage owns in
  `awsds-workflows` stay specified and unwritten.
- **[Claude] Pass 3's placement**: every type inside the ceiling has a training quota of 0 in Staging
  and Production (Stage 9's reading of 2026-10-22) and Sandbox's is 20, so a training task in `app-etl`'s
  workflow would pass `test` and fail the Staging leg; 5.1 now puts it in a second workflow with its own
  chain, written after the quota increase, and pass 3 waits on that increase.
- **[Claude] The plan**: the Status row, 2.3 and 5.1.

## 2026-10-23 — the fourth sitting with the environment down: 6.2's commands, 0.5's instrument, the sittings in order

*Claude's hand, in the session `stages-8-9-10-prep-2`, on the user's request quoted in Stage 9's entry of
the same sitting. AWS read as the infrastructure user (`awsds-infra-prod`, `awsds-infra-staging`,
`awsds-infra-sandbox-1`, `awsds-infra-data`, `awsds-infra-identity`), reads only, the tunnel down. Nothing
applied. Times UTC.*

- **[Claude] `./aws/orchestration.py`**, 16:21: *"all checks passed"* on the five infrastructure profiles,
  `OR-9` a note in both accounts, nothing of the chain layer existing.
- **[Claude] 6.2's negatives written as commands** in the step, runnable from a `DataScientistProdAccess`
  session with the environment down: the four `airflow-serverless`, `states` and `scheduler` calls (the
  set's implicit deny), `mwaa create-environment` (`DenyProvisionedMwaa`, exercised from a persona
  session) and `sns publish`.
- **[Claude] 0.5's instrument**: Stage 9 2.4's proof job, written this sitting, vends Lake Formation
  credentials from inside `VPC-Workloads`; its runs' `GetTemporaryGlue*Credentials` events in Production's
  CloudTrail are the `vpcEndpointId` reading, the command in Stage 9's step.
- **[Claude] The sittings**: pass 1's `deploy --targets dev` in the Sandbox sitting, passes 1 and 2 in the
  tag's, pass 3 after the quotas, each in [`runbooks/promotion.md`](../plan/runbooks/promotion.md) (§T, §Q).
- **[Claude] The plan**: the Status row, 0.5 and 6.2.

## 2026-10-23 — 6.2 begun by the user from the laptop: the workflow calls refused

*The commands the user's, from the laptop signed in as the Data Scientist User through
`DataScientistProdAccess` (`awsds-scientist-prod`), the tunnel down; the paste the user's, the account id
and the address masked; the reading Claude's. The first form of the two commands, `aws
airflow-serverless …`, was refused by the CLI (*"Found invalid choice 'airflow-serverless'"*): the command
is `mwaa-serverless`, corrected in the step.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws mwaa-serverless start-workflow-run --workflow-arn "arn:aws:airflow-serverless:us-west-2:<Production>:workflow/awsds-prod-wf-app-etl-0000000000" --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the StartWorkflowRun operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: airflow-serverless:StartWorkflowRun on resource: arn:aws:airflow-serverless:us-west-2:<Production>:workflow/awsds-prod-wf-app-etl-0000000000 because no identity-based policy allows the airflow-serverless:StartWorkflowRun action
  ➜  AWS-DataScience git:(main) aws mwaa-serverless list-workflows --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the ListWorkflows operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: airflow-serverless:ListWorkflows on resource: * because no identity-based policy allows the airflow-serverless:ListWorkflows action
  ```

- **[Claude]** Both the implicit deny the step expects, *"no identity-based policy allows"*: the set
  names no `airflow-serverless:` action, and decision 11 gave the reads to the approver's set alone. The
  service authorized a workflow ARN that does not exist, so the reading needed no workflow. The chain
  layer's two calls, the provisioned environment and the topic are the block's next four.

## 2026-10-23 — 6.2's chain-layer calls, the provisioned environment and the topic

*The commands the user's, the same session and profile; the paste the user's, the account id and the
addresses masked; the reading Claude's. Two commands were first run with the `<Production>` placeholder
left in, which the service refused as a malformed input, and one of them was re-run.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws stepfunctions start-execution --state-machine-arn "arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-app-etl" --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the StartExecution operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: states:StartExecution on resource: arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-app-etl because no identity-based policy allows the states:StartExecution action
  ➜  AWS-DataScience git:(main) aws scheduler create-schedule --name awsds-canary-probe --schedule-expression 'rate(1 day)' --flexible-time-window Mode=OFF --target '{"Arn":"arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-app-etl","RoleArn":"arn:aws:iam::<Production>:role/awsds-prod-chain-scheduler"}' --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the CreateSchedule operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: scheduler:CreateSchedule on resource: arn:aws:scheduler:us-west-2:<Production>:schedule/default/awsds-canary-probe because no identity-based policy allows the scheduler:CreateSchedule action
  ➜  AWS-DataScience git:(main) aws mwaa create-environment --name awsds-canary-probe --dag-s3-path dags --execution-role-arn "arn:aws:iam::<Production>:role/awsds-prod-job-exec" --source-bucket-arn arn:aws:s3:::awsds-prod-outputs --network-configuration SecurityGroupIds=sg-00000000000000000,SubnetIds=subnet-00000000000000000,subnet-00000000000000001 --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the CreateEnvironment operation: Cross-account pass role is not allowed.
  ➜  AWS-DataScience git:(main) aws mwaa create-environment --name awsds-canary-probe --dag-s3-path dags --execution-role-arn "arn:aws:iam::<Production>:role/awsds-prod-job-exec" --source-bucket-arn arn:aws:s3:::awsds-prod-outputs --network-configuration SecurityGroupIds=sg-00000000000000000,SubnetIds=subnet-00000000000000000,subnet-00000000000000001 --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the CreateEnvironment operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: airflow:CreateEnvironment on resource: arn:aws:airflow:us-west-2:<Production>:environment/awsds-canary-probe because no identity-based policy allows the airflow:CreateEnvironment action
  ➜  AWS-DataScience git:(main) aws sns publish --topic-arn "arn:aws:sns:us-west-2:<Production>:awsds-prod-alerts" --message probe --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (InvalidParameter) when calling the Publish operation: Invalid parameter: TopicArn Reason: Invalid namespace: <Production>
  ```

  The first `create-environment` carried the literal placeholder in the role ARN, which the service read
  as another account's role, *"Cross-account pass role is not allowed"*; the second carried the account's
  id. The `publish` carried the placeholder in the topic ARN and was refused as a malformed parameter,
  never authorized; it is run again with the id.
- **[Claude] The readings.** `states:StartExecution` and `scheduler:CreateSchedule`: the implicit deny,
  *"no identity-based policy allows"*, as the step expects. **`airflow:CreateEnvironment` was refused by
  the set's own implicit deny**, *"no identity-based policy allows the airflow:CreateEnvironment action"*,
  one layer before the root baseline's `DenyProvisionedMwaa` (Lesson 20): IAM names the explicit deny of
  a service control policy only to a principal whose identity policy allows the action, and no persona
  set holds an `airflow:` allow. So that statement is exercised from a persona session by nobody, and its
  proof stays the battery's `root` row as the infrastructure user (2026-10-18, `DENY-SCP`), the same shape
  Stage 9 6.3 read for `CreateSpace` under the debug role. The step's expectation is corrected.

## 2026-10-23 — 6.2's topic, run again with the account id

*The command the user's, the same session and profile; the paste the user's, the account id and the
address masked; the reading Claude's.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws sns publish --topic-arn "arn:aws:sns:us-west-2:${PROD}:awsds-prod-alerts" --message probe --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AuthorizationError) when calling the Publish operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: SNS:Publish on resource: arn:aws:sns:us-west-2:<Production>:awsds-prod-alerts because no identity-based policy allows the SNS:Publish action
  ```

- **[Claude]** The implicit deny, the set naming no `sns:` write; 6.2's six calls are read, every one
  refused by the set's own policy, and the provisioned deny's exercise stays the battery's.

## 2026-10-23 — 0.5's reading: the Lake Formation call carries the endpoint's id

*Claude's hand, reading Production's CloudTrail after Stage 9 2.4's runs, which that stage's log carries;
no write. Times UTC.*

- **[Claude] The reading**: the proof job's `GetDataAccess` events of 21:44, 22:05-22:06 and 22:11 each
  carry `vpcEndpointId` `vpce-0431cce5692733205`, the `lakeformation` interface endpoint
  `production/workloads-egress/` raises in `VPC-Workloads`; its `GetTable`s carry the `glue` endpoint's,
  `vpce-0925d883174fd23c1`. The event name is `GetDataAccess`, never `GetTemporaryGlueTableCredentials`,
  and the vend comes in two legs, the driver's own call and Glue's on its behalf. The Sandbox endpoint
  question 6d left in this step is answerable from this reading.

## 2026-10-23 — the orchestration slice's first apply with a release, in Staging, by hand

*Claude's hand, on the user's authorization in chat (*"pode prosseguir com o plano"*), as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-staging`), Stage 8 3.8's by-hand leg (that
stage's log carries the release and the applies). Times UTC.*

- **[Claude] `staging/orchestration/` with `v0.2.1`**: *"Plan: 21 to add, 0 to change, 0 to destroy."*,
  applied 22:47:39 to 22:48:02, re-planned `No changes`; `awscc_mwaaserverless_workflow.this["app-etl"]`
  created in 7 s as `awsds-staging-wf-app-etl-hHNGu2YFTv`, with the service-linked role Stage 18's first
  `CreateWorkflow` had left in the account (1.5's premise holds here; Production's first apply still owes
  `iam:CreateServiceLinkedRole`). Verification ii's deploy-role half is not answered by this apply, made
  under `InfrastructureAccess`; the pipeline's leg answers it.
- **[Claude] The key's calls in Staging's trail** (read 22:56, the key `74f5ebbc-…` the workflow names,
  the account data CMK): at the `CreateWorkflow` of 22:47:51, two `CreateGrant` and three
  `GenerateDataKey` invoked by `airflow-serverless.amazonaws.com` in the saver's session
  (`InfrastructureAccess`), each `GenerateDataKey` carrying the encryption context
  `aws:airflow-serverless:workflow-arn` = the workflow's ARN beside `aws-crypto-public-key`; at the
  chain's start, 22:49:25, `GenerateDataKey` and `Decrypt` in `awsds-staging-chain-exec`'s session with
  the same context; at 22:50:06 a `Decrypt` by the worker itself, the session
  `awsds-staging-wf-app-etl/AmazonMWAAServerless`, no `invokedBy`, the same context; the log groups'
  calls carry `aws:logs:arn` and the bucket's `aws:s3:arn`. Decision 2's premise reads true: the
  worker's and the saver's calls carry the workflow's ARN as encryption context.
- **[Claude] The chain's first execution, `v0-2-1-byhand-224923`**, started by `start-execution` as the
  infrastructure user at 22:49:24 (decision 19's shape, the leg's own command): the machine started the
  workflow run `7sLvJ2334shWqn5` (`ON_DEMAND`), polled it (`QUEUED` at 22:50:25 and 22:51:25), read it
  `FAILED` at 22:52:25 and ended **`FAILED`** with its own error `WorkflowRunNotSucceeded`, *"The run of
  awsds-staging-wf-app-etl ended FAILED, TIMEOUT or STOPPED: its task instances name the task (Stage 10
  step 3.2)"*: the chain layer's diagnosis path, exercised before 3.2 broke anything on purpose.
- **[Claude] The run**: 48 s, started 22:49:29, ended 22:50:17; `transform` (`GlueJobOperator`) **`FAILED`**
  after 11 s, `process`, `summarize` and `write_result` `UPSTREAM_FAILED`. The task's log
  (`/awsds/staging/wf/app-etl`, one stream, `task_id=transform/attempt=1`): *"Error encrypting:
  ClientError('An error occurred (AccessDeniedException) when calling the GenerateDataKey operation: User:
  arn:aws:sts::<Staging>:assumed-role/awsds-staging-wf-app-etl/AmazonMWAAServerless is not authorized to
  perform: kms:GenerateDataKey on resource: arn:aws:kms:us-west-2:<Staging>:key/74f5ebbc-… because no
  resource-based policy allows the kms:GenerateDataKey action')"*, then *"Failed to encrypt XCom value"*
  and *"XCom with key='glue_job_run_details' … not found"*. The trail: the worker's `GenerateDataKey`
  at 22:50:11 through the `kms` endpoint `vpce-07b2884c5d3d77925`, `AccessDenied`, its context not
  logged. **The Glue job the task had started ran to the end**: `awsds-staging-app-etl` run `jr_2273904b…`
  `SUCCEEDED`, 22:50:10 to 22:52:08, 98 s, 196 DPU-seconds, `--SOURCE_PATH s3://awsds-staging-outputs/inbox/app-etl/`,
  `--TARGET_PATH …/app-etl/work/glue/trades.csv`, two `G.1X`, Glue 6.0; the task failed pushing the
  run's details as an XCom, not at the job.
- **[Claude] The reading**: the data key's `AllowTheWorkflowRolesForTheirWorkflows` admits the pattern
  `awsds-staging-wf-*` to `kms:Decrypt` with the workflow's ARN as context, and the worker encrypts each
  XCom with its own `GenerateDataKey` under the workflow key, a call no page names and Stage 18's run on
  a project key (where the role held `kms:*` through the project) could not show. The fix is one action
  on that statement in `staging/data/` and `production/data/`, planned next; no processing job started,
  so verification xvi's worker-preparation clause is still open.

## 2026-10-23 — the failure rules heard: the alert e-mails of the first chain

*The user's hand (the e-mails received and pasted in chat), Claude recording; the account id masked.*

- **[user] Two e-mails received at 19:51 local time (22:51 UTC)** from Staging's alerts topic, the
  workflow's and the chain's failure rules of 3.4 (`OR-4` had read both `ENABLED` at 22:49). The one
  pasted, verbatim:

  ```
  awsds-staging-wf-app-etl-failed: a workflow run ended FAILED."
  "When: 2026-10-23T22:51:29Z"
  "Event: MWAA Serverless Workflow Run Failed"
  "Workflow: arn:aws:airflow-serverless:us-west-2:<Staging>:workflow/awsds-staging-wf-app-etl-hHNGu2YFTv"
  "Run: 7sLvJ2334shWqn5"
  "Diagnose with mwaa-serverless list-task-instances and get-task-instance (Stage 10 step 3.2)."
  "EventBridge event id: 413d9e05-1762-6379-3ab5-5e12b1e7d492"
  ```

- **[Claude] The reading**: the service emitted the run's `FAILED` event at 22:51:29, 72 s after the run
  ended (its `ModifiedAt` 22:51:28), and the rule's input transformer, the topic and the subscription
  delivered it in the same minute; the second e-mail is the chain's own rule on the execution's `FAILED`
  of 22:52:25. The failure rule 6.1 expects to hear is heard here, on a failure nobody staged, and its
  text names the diagnosis commands that found the task (the entry above).

## 2026-10-23 — the data keys' workflow-role statement gains `kms:GenerateDataKey`, both targets

*Claude's hand, on the user's authorization in chat (*"autorizado o apply"*, after the box named both
slices), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-staging`, then
`awsds-infra-prod`); Recipe A, each plan outside the repository, no other session running on the machine.
Times UTC.*

- **[Claude] The change**: `AllowTheWorkflowRolesForTheirWorkflows` in `staging/data/main.tf` and
  `production/data/main.tf` admits the pattern `awsds-<env>-wf-*` to `kms:Decrypt` **and
  `kms:GenerateDataKey`** with the workflow's ARN as encryption context; the comment names the XCom
  encryption and the date it was read; `production/data/README.md`'s row follows. The planned diff in
  each account: one resource, `module.consumer_data.module.data_key.aws_kms_key.this` updated in place,
  `+ "kms:GenerateDataKey"` in that statement's `Action`.
- **[Claude] Staging**: the fresh plan at 23:07:25 to 23:07:42, *"Plan: 0 to add, 1 to change, 0 to
  destroy."*; applied 23:07:42 to 23:07:58, *"Modifications complete after 6s"* on the key
  `74f5ebbc-…`; re-planned `No changes`.
- **[Claude] Production**: the fresh plan at 23:08:14 to 23:08:30, the same counts; applied 23:08:30 to
  23:08:45, *"Modifications complete after 6s"* on the key `0415a6f0-…`; re-planned `No changes`. The
  two slices' key policies stay identical in this statement.
- **[Claude] The chain's second execution, `v0-2-1-byhand-230927`** (23:09:28, after the key policies):
  **`FAILED`** again at 23:12:29 on the same `WorkflowRunNotSucceeded`; the run `ojUePHoPNgNdm0v` 51 s,
  `transform` `FAILED` after 14 s, the three others `UPSTREAM_FAILED`, the Glue job `jr_dfb8a65d…`
  `SUCCEEDED` again (23:10:20 to 23:12:18, 98 s, 196 DPU-seconds). The task log's wording moved one
  layer: *"not authorized to perform: kms:GenerateDataKey … because no identity-based policy allows
  the kms:GenerateDataKey action"* (23:10:21, the worker's own call through the `kms` endpoint), where
  the first run read *"no resource-based policy"*: the key policy now admits the call and the
  execution role's own policy, `orchestration-v0.1.0`'s `orchestrate` document, does not. The worker's
  `Decrypt` of 23:10:14 with the workflow's ARN as context was answered. The failure rules mailed
  again (the user's inbox, 20:11 local time).

## 2026-10-23 — `orchestration-v0.2.0`: the execution role's `GenerateDataKey`, applied in Staging

*Claude's hand, the same authorization; Recipe B. Times UTC.*

- **[Claude] The module**: `workflows.tf`'s statement `DecryptItsWorkflow` becomes `UseTheKeyForItsWorkflow`,
  `kms:Decrypt` and `kms:GenerateDataKey` on the data key with the workflow's ARN as encryption context;
  `validate` passes alone, and `staging/orchestration/` planned against the local path reads *"0 to add,
  1 to change, 0 to destroy"*, the inline `orchestrate` policy alone, the source reverted and re-initialised.
  Commit `f5429253` carries the module alone; origin's tags read `orchestration-v0.1.0` alone at the moment
  of tagging; the tag `orchestration-v0.2.0` on `f5429253`, pushed with the branch and read back from origin.
- **[Claude] The callers**: both slices pin `orchestration-v0.2.0`. `staging/orchestration/` re-initialised
  on the tag, planned *"0 to add, 1 to change, 0 to destroy"* and applied at 23:20:27, *"Modifications complete
  after 0s"* on `awsds-staging-wf-app-etl:orchestrate`, re-planned `No changes`; `production/orchestration/`
  re-initialised on the tag and planned `No changes` (no release). The callers' commit failed its hook once,
  the slices not yet initialised on the new tag, and landed after the applies.
- **[Claude] The chain's third execution, `v0-2-1-byhand-232145`** (23:21:47, after the role's policy):
  **`SUCCEEDED`** at 23:36:51, output `{"runId":"2gSJPosjsAlFvxB","runState":"SUCCESS"}`; the run 767 s,
  23:21:54 to 23:34:42, four tasks `SUCCESS`: `transform` 106 s (the Glue job `jr_f8abc018…`, 76 s, 153
  DPU-seconds, `work/glue/trades.csv` 436 bytes), `process` 491 s (the processing job
  `app-etl-20261023T232509`, `Completed`, 23:26:04 to 23:30:28 on `ml.t3.medium`, network isolation on,
  the two private subnets, the jobs' group, the image `awsds-prod-ecr-app-etl@sha256:247ec6b6…` pulled
  across the account boundary, the volume under the data key; `work/job/trades.parquet` 2,126 bytes and
  `trades.summary.json` 511), `summarize` 7 s (*"1 table(s), 10 rows, under
  s3://awsds-staging-outputs/app-etl/work/job/"*), `write_result` 6 s (`app-etl/outbox/report.json`, 332
  bytes: 10 rows, `notional` 49850.5, `quantity` 1530, the input's SHA256). `./aws/orchestration.py` all
  checks passed after the run.
- **[Claude] The worker's calls in the trail**: `glue:GetJob`, `StartJobRun` and seventeen `GetJobRun`
  through `vpce-029bcdb3b71c415e6` (`glue`); `sagemaker:CreateProcessingJob` and eighteen
  `DescribeProcessingJob` through `vpce-04b5fe9741bc3c295` (`sagemaker.api`), the first `Describe` a
  `ValidationException` before the job existed; the key's `GenerateDataKey` and `Decrypt` through
  `vpce-07b2884c5d3d77925` (`kms`), `logs:CreateLogStream` through `vpce-0813d1026921373f2`; one
  `ec2:CreateNetworkInterface` in the worker's session at 23:25:12, `Client.UnauthorizedOperation`, the job
  unaffected. The two tasks' hosts, `ip-10-50-110-196` (`process`) and `ip-10-50-50-227` (`summarize`),
  sit one in each private subnet, so the single-AZ endpoints were reached from both AZs (verification xvi).

## 2026-10-24 — 2.3's rules (2c) and (6) written in `awsds-workflows`, read on both application slices

*Claude's hand, the session and authorisation of Stage 8's entry of the same date: plans and reads as
the infrastructure user (`awsds-infra-staging`, `awsds-infra-prod`, `InfrastructureAccess`), the plans
under `$TMPDIR`, nothing applied. Times UTC.*

- **[Claude] The rules**: `awsds-workflows` PR #23, merged 2026-10-24 at 00:38:02 as `ff25eae`, writes
  (2c), the command `lint-plan <plan.json> --prefix <s3://…>` over `terraform show -json` on a saved plan,
  and (6), the promoted mode's refusal of a Glue task keeping `create_job_kwargs`, `script_location`,
  `iam_role_arn`, `update_config` or `job_desc`; read in its code at that commit. 5.1's training rule stays
  specified: the pin's `job` rule reads a `SageMakerProcessingOperator` alone and its image rule `ImageUri`
  keys, no rule names a training job. The template pins `ff25eae`, and the legs run (2c) through
  `scripts/lint-plan.py` (Stage 8's entry).
- **[Claude] (2c) on Staging's application slice**, `v0.2.1` as the stand-in release (the tag, the
  digest `sha256:247ec6b6…ce0c` and the bundle's `7fb374d1…5fff`, as on 2026-10-22): planned at 01:15:36,
  *"Plan: 1 to add, 0 to change, 0 to destroy."*, the job `awsds-staging-app-etl` on
  `awsds-staging-job-exec` and `awsds-staging-jobs`, its script
  `s3://awsds-staging-outputs/applications/app-etl/v0.2.1/glue/transform.py`. `lint-plan.py staging …
  --tag v0.2.1` at 01:15:57: *"ok: 1 job(s) do Glue: aws_glue_job.this[0]"*, exit 0; `--tag v9.9.9`:
  *"glue: aws_glue_job.this[0]: o script
  s3://awsds-staging-outputs/applications/app-etl/v0.2.1/glue/transform.py está fora de
  s3://awsds-staging-outputs/applications/app-etl/v9.9.9/glue/"*, exit 1; the tool called directly with the
  two prefixes printed the same, exits 0 and 1.
- **[Claude] (2c) on Production's**, the same release: planned at 01:16:25, *"Plan: 1 to add"*, the job
  `awsds-prod-app-etl` on `awsds-prod-job-exec` and `awsds-prod-jobs`, its script under
  `s3://awsds-prod-outputs/applications/app-etl/v0.2.1/glue/`. `lint-plan.py production … --tag v0.2.1` at
  01:16:35: *"ok: 1 job(s) do Glue: aws_glue_job.this[0]"*, exit 0; `--tag v9.9.9`: the script refused under
  `glue`, exit 1.
- **[Claude] Staging's slice with no release**, 01:17:02: `No changes`; the tool printed *"ok: 0 job(s) do
  Glue: -"* and `lint-plan.py` exited 1, *"no aws_glue_job is left by the apply, so none was read"*.
- **[Claude] (6)** is read on Staging's rendered copy, each key refused: Stage 8's entry, verification xiv.
- **[Claude] The plan**: 2.3 (the rules written, where the legs call `lint-plan`, the readings), 5.1's
  sentence at the new pin, the Status row.

## 2026-10-24 — 3.8's calls replayed as the deploy roles: `ValidateStateMachineDefinition` missing from both

*Claude's hand, in the session `stages-8-9-10-prep-f13bc2`, on the user's request to check the state of
Stages 8, 9 and 10, review their plans against the recent work and prepare everything that needs no
environment (the request is quoted in Stage 9's entry of this date). AWS read as the infrastructure user
with `InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`,
`awsds-infra-data`, `awsds-infra-identity`), reads, simulations and plans only, the tunnel down. Nothing
applied. Times UTC.*

- **[Claude] The trail**: Staging's management events of 2026-10-23 22:25 to 23:55, us-west-2 (2,671
  events, 1,369 in the infrastructure user's session) and us-east-1 for IAM and Organizations, kept outside
  the repository. Terraform's calls (user agent `APN/1.0 … Terraform/1.15.8`) and the services' calls in
  that session (`userIdentity.invokedBy`) were taken from four windows: `make up ENV=staging ONLY=egress`
  (22:39 to 22:44), the two applies (22:46:30 to 22:48:30), the orchestration update (23:19:30 to 23:21)
  and `make down ENV=staging` (23:41 to 23:51).
- **[Claude] The replay**, 02:22 to 02:40: each distinct call put through `iam simulate-principal-policy`
  as `awsds-deploy-staging`, with `aws:RequestedRegion`, the organization and account keys, and the
  condition keys each statement reads (`iam:PermissionsBoundary`, `iam:PassedToService`,
  `kms:ResourceAliases`, `kms:ViaService`, the workflow's encryption context, `kms:GrantIsForAWSResource`,
  the workers' group's `Name` tag); then renamed for Production as `awsds-deploy-prod`, the egress slice
  left out (the user raises `workloads-egress/`). Added by hand, since no management event shows them: the
  five `iam:PassRole`s (the workflow, chain, scheduler and bridge roles, the Glue job role), the release's
  S3 objects and the data key through S3, the state objects, and Production's
  `iam:CreateServiceLinkedRole`. 161 simulations in Staging, 129 in Production.
- **[Claude] The readings**: every call `allowed` but two. `states:ValidateStateMachineDefinition` reads
  `implicitDeny` for both roles, the boundary and the organization's policies allowing it; with a state
  machine's ARN the simulator applies no statement, so the action takes no resource. Called once in the
  by-hand leg, at 22:47:58 beside `CreateStateMachine`; the aws provider's `stateMachineDefinitionValidate`
  (v6.70.0, read in its source) runs in `CustomizeDiff` when the definition is new or changed and returns
  any error, so both legs would have stopped at the orchestration apply. `iam:CreateServiceLinkedRole`
  reads `implicitDeny` for `awsds-deploy-staging`: the trail holds it at 22:47:51, invoked by
  `airflow-serverless.amazonaws.com` in the saver's session during the Cloud Control creation, answered
  `InvalidInputException` because the role exists; under a role without the grant the call is refused
  first, and how the service takes the refusal is unmeasured. The other first-pass refusals were the
  replay's ARNs, re-read with resources of each action's type (the Route 53 Resolver set, `DescribeLogGroups`
  and `CreateWorkflow` on `*`), all `allowed`. Both data keys' policies were read the same night: the
  deploy role and `InfrastructureAccess` named for `CreateGrant`, `DescribeKey`, and `Decrypt` and
  `GenerateDataKey` under the workflow's encryption context.
- **[Claude] The fix**: `apply-orchestration.tf`, the same file in both `foundation/` slices, gains
  `ValidateTheChainDefinitions`; Staging's `deploy-role.tf` gains Production's
  `CreateTheWorkflowServiceLinkedRole`, and Production's comment no longer removes it once the role
  exists. `staging/foundation/` planned as `awsds-infra-staging` at 02:33:42 to 02:33:59 and
  `production/foundation/` as `awsds-infra-prod` at 02:34:59 to 02:35:16, each with the alerts var-file:
  *"Plan: 0 to add, 1 to change, 0 to destroy."*, `aws_iam_policy.orchestration["resources"]` updated in
  place, the two statements in Staging and the one in Production, the plans outside the repository. The
  managed policies measured 4,063 and 4,490 characters before the change, under the 6,144 a managed policy
  holds. The applies wait for the user's authorization (`runbooks/promotion.md` §0.5).
- **[Claude] `./aws/orchestration.py`** on the five infrastructure profiles at 02:07: all checks passed,
  `OR-1` and `OR-9` notes in both accounts (no workflow, no chain, `[E]` between sessions). A first run
  with no profile named tried every profile in the config and failed on the persona profiles with no
  session; it measured nothing.
- **[Claude] 0.5's consequence for 6d decision due 11**, written in the step: keep Sandbox's
  `lakeformation` endpoint, recommended, the decision the user's.
- **[Claude] The plan**: 1.5's grant list and its replay, verification ii's simulator half, 0.5 and the
  Status row.

## 2026-10-24 — the two statements applied in both `foundation/` slices, read back by the simulator

*Claude's hand, on the user's authorization in chat (*"Autorizo os applies de staging/foundation/
(awsds-infra-staging) e production/foundation/ (awsds-infra-prod), como usuário de infraestrutura com
InfrastructureAccess, cada um de um plano fresco com o var-file de alertas, e a leitura do simulador
depois."*), as the infrastructure user with `InfrastructureAccess`; Recipe A, each plan outside the
repository, with `-var-file=<project folder>/secrets/alerts.auto.tfvars`, from the branch at `c5a479db`.
The one other session on the machine, idle, was told before the first write and answered that the
applies touch nothing it reads. Times UTC.*

- **[Claude] `staging/foundation/`** as `awsds-infra-staging`: the fresh plan at 02:51:53 to 02:52:08,
  *"Plan: 0 to add, 1 to change, 0 to destroy."*, `aws_iam_policy.orchestration["resources"]` gaining
  `CreateTheWorkflowServiceLinkedRole` and `ValidateTheChainDefinitions`; applied 02:52:20 to 02:52:30,
  *"Modifications complete after 1s"* on `awsds-staging-deploy-orchestration-resources`, *"Apply
  complete! Resources: 0 added, 1 changed, 0 destroyed."*; re-planned `No changes` at 02:52:44.
- **[Claude] `production/foundation/`** as `awsds-infra-prod`: the fresh plan at 02:52:53 to 02:53:11, the
  same counts, `ValidateTheChainDefinitions` alone; applied 02:53:24 to 02:53:36, *"Modifications
  complete after 1s"* on `awsds-prod-deploy-orchestration-resources`, *"Apply complete! Resources: 0
  added, 1 changed, 0 destroyed."*; re-planned `No changes` at 02:53:56.
- **[Claude] The simulator**, 02:54:08 to 02:54:14: `states:ValidateStateMachineDefinition` on `*` and
  `iam:CreateServiceLinkedRole` on the MWAA Serverless service-linked role (`iam:AWSServiceName`
  `airflow-serverless.amazonaws.com`) read `allowed` for `awsds-deploy-staging` and `awsds-deploy-prod`,
  each matched by its account's `awsds-<env>-deploy-orchestration-resources`, the boundary and the
  organization's policies allowing. The legs' orchestration applies no longer stop at the plan; whether
  the service's own calls then succeed is the leg's reading (verification ii).

## 2026-10-24 — the `staging-test` leg's calls read by the simulator

*Claude's hand, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-staging`), reads only.
Times UTC.*

- **[Claude] The calls the first replay left out**, made by the CLI rather than Terraform: the leg's
  `states:StartExecution` on `stateMachine:awsds-staging-chain-app-etl`, and `states:DescribeExecution`
  and `states:GetExecutionHistory` on one of its executions, read `allowed` for `awsds-deploy-staging` at
  03:05, each matched by `awsds-staging-deploy-orchestration-resources` (decision 19's start of the chain).

## 2026-10-24 — pass 3 written, the quotas raised: decisions 21 and 22, the training rule

*Claude's hand, in the session `planejamento-estagios-8-9-10-847863` (Stage 9's entry of this date quotes
the request), as the infrastructure user with `InfrastructureAccess`, reads and plans only. Nothing
applied. Times UTC.*

- **[user] The decisions**, answered in the session's question: *"Tudo agora (Recomendado)"* for when
  v0.4.0 is written, its tag after v0.3.0 has passed; decision 21, the model, *"XGBoost da AWS
  (Recomendado)"*; decision 22, how Staging tests a model it cannot read from Production, *"Retreina em
  Staging (Recomendado)"*.
- **[Claude] The image**: `aws ecr describe-images` on AWS's `sagemaker-xgboost` repository, tag `3.0-5`,
  as `awsds-infra-prod`: `sha256:0b5d9341baa09ab2432fc9efbc329425e69325ba33562b1e2a015fd6f16e3a78`,
  pushed 2026-10-11, tags `3.0-5`, `3.0-5-cpu-py3` and `3.0-5-1.0.64.0`. `*/sagemaker/training-image.tf`
  composes the URI from the provider's table of prebuilt images and that digest, so no account id is in
  the repository.
- **[Claude] 5.1 written**: the workflow `app-etl-train`, `train` (`SageMakerTrainingOperator`,
  `ml.m5.large`, the job subnets, network isolation, the data key on the volume and the model,
  `action_if_job_exists: fail`) and `evaluate` (the training job's `validation:rmse` as SageMaker's
  model-quality statistics beside the model, with the batch's row count). The job's name reaches
  `evaluate` through `train`'s XCom, since `{{ ts_nodash }}` is midnight in a manual run. The lint's
  rule `treino` and the `TrainingImage` half of `imagem` are `awsds-workflows` `d60e1ad` (branch
  `treino-e-repositorio-de-algoritmo`, its merge the user's): 135 lint tests pass, and the 7 of
  `prepare_offline` that fail on Darwin arm64 fail the same at `ff25eae`. The template's lint and the
  release's promoted lint pass `--algorithm-repository sagemaker-xgboost` (`LINT_ALGORITHM_REPOSITORIES`);
  each rendered copy, stand-in values, reads `ok`.
- **[Claude] 5.2 and 5.4 written**: `scripts/model-chain.py` (`register`, `approve`, `transform`, and
  `--check` in `make check`) and the template's jobs `staging-model`, `production-register` and
  `production-approve` (manual) and `production-transform`. 5.4's Staging half now serves Staging's own
  retrained model, as Stage 9 decision 1 requires. The deploy roles' grants planned 17:20 to 17:21 with
  the alerts var-file: *"Plan: 0 to add, 1 to change, 0 to destroy."* in each `foundation/`, the
  inline totals 3,637 (Production) and 6,183 (Staging) characters of 10,240.
- **[Claude] The orchestration slices**: `app-etl-train` and its chain in both (`DISABLED` in Staging,
  `cron(0 7 * * ? *)` in Production), `app-etl-warehouse` and its chain in Production; a chain whose
  workflows a release lacks is not created, so v0.3.0's `release.tf` creates neither. Both slices
  validate; `orchestration-v0.2.0` already carries `training_job_prefix`.

## 2026-10-24 — the deploy roles' model-chain grants applied in both `foundation/` slices, read by the simulator

*Claude's hand, on the user's authorization quoted in Stage 9's entry of this date, as the infrastructure
user with `InfrastructureAccess`; Recipe A with `-var-file=<project folder>/secrets/alerts.auto.tfvars`.
Times UTC.*

- **[Claude] `production/foundation/`** as `awsds-infra-prod`: plan 17:54:19, *"Plan: 0 to add, 1 to
  change, 0 to destroy."*, `aws_iam_role_policy.inline["apply-application"]` in place; applied 17:54:37,
  *"Modifications complete after 1s [id=awsds-deploy-prod:apply-application]"*; re-planned `No changes`
  at 17:54:48.
- **[Claude] `staging/foundation/`** as `awsds-infra-staging`: plan 17:55:10, the same counts; applied
  17:55:24 on `awsds-deploy-staging:apply-application`; re-planned `No changes` at 17:55:34.
- **[Claude] The simulator**, 17:58 to 18:05, `aws:RequestedRegion` in every context (without it the
  Control Tower ceiling denies everything, the shape `lessons.md` records). `allowed`, matched by each
  role's `apply-application`: `DescribeModel`, `DeleteModel`, `DescribeTransformJob`,
  `StopTransformJob`, `DescribeTrainingJob` on `app-etl-train-*`, `ListTrainingJobs`, `s3:GetObject` on
  `models/…` of the account's outputs bucket and `glue:CreateJob` on `awsds-<env>-app-etl-load`, for both
  roles; `CreateModelPackage` on a version of `awsds-prod-model-app-etl`, `UpdateModelPackage`,
  `DescribeModelPackage` and `DescribeModelPackageGroup` for `awsds-deploy-prod`, and `CreateModelPackage`
  `implicitDeny` for `awsds-deploy-staging`, the negative control. `CreateModel` on `model/app-etl-…`
  reads `allowed` with `sagemaker:VpcSubnets`, `VpcSecurityGroupIds` and `NetworkIsolation` in the
  context and `explicitDeny` from the organization without them, so the `Workloads` document's job
  settings bind each deploy role (Stage 9 verification xv's deploy-role half, by simulation).
  `CreateTransformJob` on a `transform-job/…` ARN reads `explicitDeny` with the volume key given: the
  simulator drops `sagemaker:VolumeKmsKey` against a job's ARN, `CreateTrainingJob` alike (the entry
  `lessons.md` holds since 6d, extended to the transform). Against `*` the same request reads
  `implicitDeny`, the organization no longer denying and the identity statement scoped to
  `transform-job/app-etl-*`, and without the key `explicitDeny` from the organization. The first real
  call is v0.4.0's `staging-model`.

## 2026-10-24 — pipeline #68: the deploy role refused the workflow's tag-on-create, then applied the orchestration slice in Staging

*Claude's hand for the reading (the job traces through the user's Chrome session, AWS as the
infrastructure user with `InfrastructureAccess`), the fix and the applies, on the user's authorization
quoted below; the user's for the retry. Times UTC.*

- **[Claude] The refusal**, `staging-deploy` (Stage 8's log), by 20:09:57: `staging/orchestration/` planned
  21 to add and stopped at `awscc_mwaaserverless_workflow.this["app-etl"]`: *"Waiting for Cloud Control
  API service CreateResource operation completion returned: waiter state transitioned to FAILED.
  StatusMessage: User: arn:aws:sts::<account>:assumed-role/awsds-deploy-staging/aws-go-sdk-… is not
  authorized to perform: airflow-serverless:TagResource on resource:
  arn:aws:airflow-serverless:us-west-2:<account>:workflow/* because no identity-based policy allows the
  airflow-serverless:TagResource action … ErrorCode: UnauthorizedTaggingOperation"*. A workflow's ARN ends
  in a suffix the service generates (`awsds-staging-wf-app-etl-hHNGu2YFTv` on 2026-10-23), so
  `CreateWorkflow` authorizes the tags it carries on `workflow/*`; `ManageTheWorkflows` named
  `workflow/awsds-<env>-wf-*` alone. Read at 20:20 as `awsds-infra-staging`: `list-workflows` empty; the
  roles `awsds-staging-wf-app-etl`, `-chain-events`, `-chain-exec` and `-chain-scheduler`, the workers'
  group, the log groups `/awsds/staging/wf/app-etl` and `/aws/vendedlogs/states/awsds-staging-chains`; no
  state machine.
- **[Claude] Why 2026-10-24's replay missed it** (1.5, verification ii's simulator half; the reading of
  the peer session *Estágios 8, 9 e 10 — preparação e revisão*): the tag-on-create check runs inside
  `CreateWorkflow` and leaves no CloudTrail event of its own, and 3.8's by-hand leg ran as
  `InfrastructureAccess`, so no trail held the call to replay. The legs' other tag-on-create checks are on
  ARNs the caller names: `states`, `scheduler`, `events`, `logs`, `iam`, and `ec2:CreateTags` under
  `ec2:CreateAction`.
- **[Claude] The fix, `c60ad8d6`**: `TagTheWorkflowsAtCreation` in both `foundation/apply-orchestration.tf`
  copies, `airflow-serverless:TagResource` on `workflow/*` for a request whose `aws:RequestTag/Name` is
  `awsds-<env>-wf-*`, the tag the module writes; the service's condition keys are `aws:RequestTag/*`,
  `aws:ResourceTag/*` and `aws:TagKeys` (the policy generator's table, read the same evening). Plans
  *"0 to add, 1 to change, 0 to destroy"* each, `aws_iam_policy.orchestration["resources"]` in place,
  4,743 and 4,343 compact characters of 6,144.
- **[user]** *"Autorizo os applies dos planos salvos de staging/foundation e production/foundation, como
  usuário de infraestrutura com InfrastructureAccess (awsds-infra-staging e awsds-infra-prod), e as
  leituras depois."* **[Claude]** The five peer sessions told first. Staging applied 20:28:51 to 20:29:02,
  Production 20:29:10 to 20:29:21, each *"Modifications complete after 2s"*, both policies at `v3`;
  re-planned `No changes`. The simulator, `aws:RequestedRegion` in the context: `TagResource` on
  `workflow/*` reads `allowed` for `awsds-deploy-staging` and `awsds-deploy-prod` with
  `Name=awsds-<env>-wf-app-etl`, matched by `awsds-<env>-deploy-orchestration-resources`, and
  `implicitDeny` with `Name=other-workflow`.
- **[user]** The retry. **[Claude] Job 330** as `awsds-deploy-staging`: *"Plan: 7 to add, 0 to change, 0
  to destroy."*, the workflow *"Creation complete after 5s"* at 20:34:57, then the failure rule and its
  target, the chain's state machine, its schedule and the chain's failure rule and target, *"Apply
  complete! Resources: 7 added, 0 changed, 0 destroyed."* at 20:34:59; the workflow and the machine read
  in Staging at 20:35:00. INT-14 is answered in Staging: `awscc_mwaaserverless_workflow` applies under the
  deploy role's boundary (verification ii's deploy-role half), and so do `aws_sfn_state_machine` and
  `aws_scheduler_schedule` beside it (verification xxvi's Staging half). The chain was not started:
  `staging-test` stopped at its clone (Stage 8's log).

## 2026-10-24 — Production's half of passes 1 and 2 through pipeline #71, and the chain's first run there

*Claude's hand for the readings (the job traces through the user's Chrome session, AWS as the
infrastructure user with `InfrastructureAccess`) and for the run, on the user's authorization quoted
below; the user's for the gate. Times UTC.*

- **[Claude] `production-deploy`** (Stage 8's log), as `awsds-deploy-prod`: `production/orchestration/`
  *"Plan: 21 to add"*, the workflow *"Creation complete after 5s"* at 21:34:01, the chain's machine at
  21:34:03, its schedule at 21:34:03, *"Apply complete! Resources: 21 added, 0 changed, 0 destroyed."* at
  21:34:04. INT-14 holds in Production (verification ii). CloudTrail, `us-east-1`: `CreateServiceLinkedRole`
  at 21:33:58, session issuer `awsds-deploy-prod`, invoked by `airflow-serverless.amazonaws.com`, no error;
  `AWSServiceRoleForAmazonMWAAServerless` created 21:33:58 (verification iii's Production half, 1.5's
  statement `CreateTheWorkflowServiceLinkedRole` exercised). Read at 21:38: `awsds-prod-wf-app-etl`
  `READY`, `manual_only`, its definition `jU1vr4IL…eHZX` and code `K.apAb_C…eBtxN`; the schedule
  `awsds-prod-chain-app-etl` `ENABLED` on `cron(30 6 * * ? *)` UTC; no execution.
- **[user]** *"Autorizo disparar a chain awsds-prod-chain-app-etl agora, à mão, como usuário de
  infraestrutura com InfrastructureAccess (awsds-infra-prod), e acompanhar até o fim. O workloads-egress
  fica no ar até o schedule das 06:30 UTC."* **[Claude]** The five peer sessions told first;
  `start-execution` as `awsds-infra-prod` at 21:41:17, the execution `v0-3-3-by-hand-2026-10-24` started
  21:41:19 and `SUCCEEDED` at 21:56:23 (15 min 4 s). The workflow run `TjivGiTkS0VAZOV`, `RunType`
  `ON_DEMAND`, `SUCCESS` from 21:41:24 to 21:54:12, its four tasks `SUCCESS`: the Glue job
  `awsds-prod-app-etl`, run `jr_56c29738…e022`, `SUCCEEDED` from 21:42:08 to 21:44:01 (93 s, Glue 6.0, two
  `G.1X`); the processing job `app-etl-20261024T214447` `Completed` from 21:45:36 to 21:50:11; then the
  summary and the report. The outputs, under `s3://awsds-prod-outputs/app-etl/`: `work/glue/trades.csv`
  (436 bytes, 21:43:51), `work/job/trades.parquet` (2,126) and `trades.summary.json` (511) at 21:50:07,
  `outbox/report.json` (332) at 21:54:12.
- **[Claude] 6.1**: `workloads-egress/` stays up, by the user's decision, so the schedule's first firing
  at 06:30 UTC on 2026-10-25 runs unattended (verification xxiv); its reading and 6.3's sentence come
  before the first `make down ENV=production`.
- **[Claude] The instruments**, on the five infrastructure profiles: `./aws/orchestration.py` 13 passes and
  two notes, Staging's workflows and chains absent after the user's `make down`: `OR-1` `READY`, `OR-3`
  bounded with no lake reach and two subnets in two AZs with no default route, `OR-5` the definition at
  `v0.3.3`'s version, `OR-6` none in 6 accounts, `OR-7` 1/50, `OR-9` the three chain roles on
  `awsds-prod-app-boundary` and the chain's schedule and failure rule `ENABLED` (verification xxvi's
  `OR-9` half). The persona profiles hold no session, so the script exits 1 on section 1 alone.

## 2026-10-24 — 1.6's record in Production and 6.3's run-history disposition, read on Staging's teardown

*Claude's hand, as the infrastructure user with `InfrastructureAccess`. Times UTC.*

- **[Claude] 1.6, Production**: the first `CreateWorkflow` created `workflow/awsds-prod-wf-app-etl-DHhc8FiTZC`,
  version 1 of 50 (`OR-7`). `AWSServiceRoleForAmazonMWAAServerless` sits at
  `/aws-service-role/airflow-serverless.amazonaws.com/`, created 21:33:58, its trust
  `airflow-serverless.amazonaws.com`, no boundary, no inline policy, one attached policy,
  `AmazonMWAAServerlessServiceRolePolicy` at `v1`: Staging's shape of 2026-10-20 (verification iii).
- **[Claude] 6.3, the disposition, measured on Staging after the user's `make down ENV=staging`** (read
  about 22:00): the destroy of `staging/orchestration/` deleted the workflow with its two versions and its runs,
  the chain's machine with its executions (`v0-3-3-71` among them), and both log groups the module creates,
  `/awsds/staging/wf/app-etl` and `/aws/vendedlogs/states/awsds-staging-chains`. The step's sentence that
  the log group is `[P]`-adjacent does not hold for these two: they live in the `[E]` slice and die with
  it. What survives a teardown: the Glue and processing jobs' logs in `/aws-glue/jobs/*` and
  `/aws/sagemaker/ProcessingJobs`, `[P]` groups of `sagemaker/` at 30 days; the leg's artifacts
  `execution.json` and `history.json`, kept a year; the objects under the outputs bucket. In Production
  the same holds for `/awsds/prod/wf/app-etl` and `/aws/vendedlogs/states/awsds-prod-chains` (90 days) on
  a destroy of `production/orchestration/`, which `make down ENV=production ONLY=workloads-egress` never
  runs: Production's run history and chain logs persist between sessions while the slice stands.

## 2026-10-24 — `v0.4.1`'s Staging leg: the train chain's first run, `evaluate` failing at its template, the diagnosis from the service's APIs

*Claude's hand for the readings, as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-staging`), reads only; the run was the pipeline's (Stage 8's log, pipeline #77), in the
session of `runbooks/promotion.md` §V (the branch `claude/eloquent-ishizaka-04f598`). Times UTC.*

- **[Claude] The orchestration slice in Staging**: `staging-deploy` applied *"31 added"*, the workflows
  `awsds-staging-wf-app-etl` and `awsds-staging-wf-app-etl-train` and their two chains, `DISABLED`
  (decision 19); the warehouse workflow's definition was rendered and written but no workflow made, as
  decision 15 has it. The release file's `VersionId`s: `app-etl` definition `PE1nwZT0…R1D7`, code
  `o_PmDbA1…idKy`; `app-etl-train` definition `enBzmuTu…fOdQo`, code `G7qnbCvy…03UJyYL`; `app-etl-warehouse`
  definition `uAsosO2S…8bc3Xin`.
- **[Claude] The app-etl chain**: `v0-4-1-77-app-etl` `SUCCEEDED`, 23:20:23 to 23:33:26.
- **[Claude] The train chain's first run anywhere** (5.1; `test-deploy` creates the workflow in the
  `test` project and never runs it): `v0-4-1-77-app-etl-train`, 23:33:46 to 23:40:48, `FAILED` with
  *"WorkflowRunNotSucceeded"*. The run `yCiuDo0tu6ofGpx`, 23:34:01 to 23:38:53: `train` `SUCCESS` in 219 s,
  the training job `app-etl-train-20261024T233434` on `ml.m5.large` as `awsds-staging-job-exec`, AWS's
  XGBoost by digest, the data key on the volume and the model, network isolation and inter-container
  encryption, two subnets, `MaxRuntimeInSeconds` 1800, training from 23:35:32 to 23:37:26 (114 billable
  seconds), `validation:rmse` 1016.31; `evaluate` `FAILED` in 10 s.
- **[Claude] The diagnosis, from the service's APIs alone** (3.2's path): the machine's `cause` names the
  workflow; `get-workflow-run` reads *"Workflow execution failed, please check the task execution logs for
  more details"* and `RunType` null; `list-task-instances` names `evaluate` `FAILED`; `get-task-instance`
  gives its `LogStream`, `workflow_id=awsds-staging-wf-app-etl-train-wjwLbosH4U/run_id=yCiuDo0tu6ofGpx/task_id=evaluate/attempt=1.log`;
  the stream in `/awsds/staging/wf/app-etl-train`, read at about 23:43, before `staging-down` destroyed
  the group: *"Exception rendering Jinja template for task 'evaluate', field 'op_kwargs'"* on
  `ti.xcom_pull(task_ids='train')['Training']['TrainingJobName']`, *"UndefinedError … 'str object' has no
  attribute 'Training'"*. The worker renders an XCom as the JSON of its value: Staging's
  `app-etl/outbox/report.json` (336 bytes, 23:30:31) holds the JSON text of the report's string, the same
  rendering one task earlier. The code package imported (*"Successfully generated DAGs"*), and no call
  of the task's reached AWS.
- **[Claude] The failure rules** (verification vi): `awsds-staging-wf-app-etl-train-failed` triggered and
  invoked once at 23:39, `awsds-staging-chain-app-etl-train-failed` at 23:40, and `awsds-staging-alerts`
  published and delivered two notifications at 23:40 (`AWS/Events` and `AWS/SNS`, read after the
  teardown, since the rules die with the slice).
- **[Claude] The fix**, in the template: `evaluate` takes the whole XCom and `training_job_name` decodes
  it; 31 tests and the workflow lint pass. The release is `v0.4.2` (Stage 8's log). 6.3's sentence holds
  on a failure: the task's log group went with the slice, and the reading survives only because it was
  taken before `staging-down`.

## 2026-10-25 — `v0.4.2`'s Staging leg: the train chain, Staging's first batch transform (5.4's Staging half), Production's three chains

*Claude's hand for the readings, as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-staging`, `awsds-infra-prod`); the runs were the pipeline's (Stage 8's log, pipeline #80).
Times UTC.*

- **[Claude] The train chain in Staging**, with `evaluate`'s fix: the app-etl chain `SUCCEEDED` (about
  00:17 to 00:32), then the train chain `SUCCEEDED` (about 00:32 to 00:40): the training job
  `app-etl-train-20261025T003320` `Completed` with the settings #77's job carried, and `evaluate` wrote
  `models/app-etl/app-etl-train-20261025T003320/evaluation.json` on `awsds-staging-outputs`, `rmse`
  1016.31 and `batch_rows` 30, the job and its model named in the file's `awsds` block.
- **[Claude] 5.4's Staging half**, `staging-model` (`scripts/model-chain.py transform staging`): the
  model `app-etl-v0-4-2-20261025T004019` as `awsds-staging-job-exec`, network-isolated in the two job
  subnets, AWS's XGBoost by digest over `app-etl-train-20261025T003320`'s artifact; the transform job of the
  same name on one `ml.m5.large`, the data key on its volume and its output, the input
  `app-etl/work/train/batch/` split by line, the output under `models/app-etl/transform/<job>/`;
  `Completed` at 00:45:41, *"30 prediction(s), one per input row"*, the model deleted after. Staging served
  its own model before Production's deploy ran (decision 22, verification x's order).
- **[Claude] Production's orchestration apply** (`production-deploy`, 00:54:37 to 00:57:51, as
  `awsds-deploy-prod`): *"20 added, 1 changed"*, the app-etl workflow updated to `v0.4.2` and
  `awsds-prod-wf-app-etl-train` and `awsds-prod-wf-app-etl-warehouse` created, each with its chain and its
  schedule `ENABLED` (06:30, 07:00 and 07:30 UTC), so the schedules fire `v0.4.2`'s chains from 2026-10-25.

## 2026-10-25 — Production's runs by hand, the model's registration and approval, the first batch transform there, 5.5 from Sandbox

*Claude's hand for the runs, on the user's authorization in chat (*"Autorizo iniciar, depois do
production-deploy da v0.4.0, as chains awsds-prod-chain-app-etl e em seguida
awsds-prod-chain-app-etl-train em Production, como usuário de infraestrutura com InfrastructureAccess
(awsds-infra-prod), e acompanhar cada uma até o fim."*), and for the readings, as the infrastructure user
with `InfrastructureAccess`; the user's for the pipeline's manual jobs and for 5.5, signed in as the Data
Scientist User. In the user's pasted output the account ids are replaced by `<Production>`, `<Sandbox
Account 1>` and `<AWS registry>` and the e-mail by `<data scientist user>`. Times UTC.*

- **[Claude] The app-etl chain**, `v0-4-2-by-hand-2026-10-25-app-etl`, started at 00:58:42, `SUCCEEDED` at
  01:17:47: the Glue job `jr_45a3c84d…f19c` (00:59:28 to 01:05:04) *"reading SELECT trade_date, desk,
  instrument, quantity, price FROM lake.curated.trades"*, *"read 30 row(s)"*, the table and the training
  sets written (24, 6 and 30 lines); the processing job `app-etl-20261025T010552` `Completed`.
- **[Claude] The train chain**, `v0-4-2-by-hand-2026-10-25-app-etl-train`, 01:18:16 to 01:25:18,
  `SUCCEEDED`: Production's first training job `app-etl-train-20261025T011858` as `awsds-prod-job-exec`
  on `ml.m5.large`, Production's data key on its volume and its output (`OutputDataConfig.KmsKeyId`,
  verification x), network isolation and inter-container encryption, training 01:19:45 to 01:21:49 (124
  billable seconds), `validation:rmse` 1016.31; `evaluate` wrote its `evaluation.json`, 30 batch rows.
- **[user] 5.2's jobs**: `production-register` (job 450, 01:28:13 to 01:28:39), *"registered
  …model-package/awsds-prod-model-app-etl/1 from app-etl-train-20261025T011858, PendingManualApproval"*;
  `production-approve` (451, 01:29:00 to 01:29:13), *"…/awsds-prod-model-app-etl/1: Approved"*.
  **[Claude] read back**: version 1 `Completed` and `Approved`, `ApprovalDescription` *"approved by felipenoris
  at the promotion pipeline's manual job"*, `CustomerMetadataProperties` `git_tag` `v0.4.2`, the training
  job and its `validation_rmse`, `ModelMetrics.ModelQuality` the `evaluation.json`; CloudTrail:
  `CreateModelPackage` at 01:28:36 and `UpdateModelPackage` at 01:29:10, both `awsds-deploy-prod`, no
  error (verification x's registration clause).
- **[Claude] 5.3's rule fired for the first time**: `awsds-prod-model-approval` triggered at 01:28 and at
  01:29, and `awsds-prod-alerts` delivered one notification each minute.
- **[pipeline] 5.4's Production half**, `production-transform` (452, 01:29:16 to 01:35:30): CloudTrail
  `CreateModel` at 01:29:33 as `awsds-deploy-prod` with `Containers` `[{"modelPackageName":
  "…/awsds-prod-model-app-etl/1"}]`, the execution role `awsds-prod-job-exec`, network isolation and the
  job subnets; the transform `app-etl-v0-4-2-20261025T012931` on `ml.m5.large`, the data key on its volume
  and its output, 01:33:24 to 01:35:03, *"30 prediction(s), one per input row"*; `DeleteModel` at
  01:35:28. Pipeline #80 ended `success`, `production-warehouse-ddl` left manual.
- **[user] 5.5 from Sandbox**, as the Data Scientist User through `awsds-scientist-sandbox`: `aws
  sagemaker describe-model-package --model-package-name
  "arn:aws:sagemaker:us-west-2:<Production>:model-package/awsds-prod-model-app-etl/1"` answered with the
  whole record, `ModelApprovalStatus` `Approved`, `CreatedBy` and `LastModifiedBy`
  `arn:aws:sts::<Production>:assumed-role/awsds-deploy-prod/botocore-session-…`, the image
  `<AWS registry>.dkr.ecr.us-west-2.amazonaws.com/sagemaker-xgboost@sha256:0b5d9341…3a78`; `aws sagemaker
  update-model-package … --model-approval-status Approved` was refused: *"An error occurred
  (AccessDeniedException) when calling the UpdateModelPackage operation: User: arn:aws:sts::<Sandbox Account
  1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not
  authorized to perform: sagemaker:UpdateModelPackage on resource:
  arn:aws:sagemaker:us-west-2:<Production>:model-package/awsds-prod-model-app-etl/1 because no
  resource-based policy allows the sagemaker:UpdateModelPackage action"*. The gate holds from the far side,
  the refusal the group policy's absence of a grant.

## 2026-10-25 — 6.1: the schedules start both chains unattended, and the paused one does not fire

*Claude's hand, on the user's authorization in chat for the pause (*"Sim: pause o schedule
awsds-prod-chain-app-etl-warehouse (DISABLED) pelo slice production/orchestration, com um commit no PR e o apply
manual como usuário de infraestrutura (awsds-infra-prod); app-etl (06:30) e treino (07:00) disparam sozinhos
amanhã."*), and for the readings, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`);
nobody at the keyboard for the runs, `production/workloads-egress/` up since the warehouse sitting. Times UTC.*

- **[Claude] The lever, through the slice**: the warehouse chain's `schedule_enabled = false` in
  `production/orchestration/` (Stage 9 decision 15: the load fails whenever the warehouse compute is down),
  planned at 01:15, *"Plan: 0 to add, 1 to change, 0 to destroy."*, the schedule's `state` `ENABLED` →
  `DISABLED` alone; applied at 01:15:54, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*,
  re-planned `No changes`; the app-etl and train schedules left `ENABLED`.
- **[Claude] 06:30, the app-etl chain**: CloudTrail's `AssumeRole` at 06:30:17 by `scheduler.amazonaws.com` on
  `awsds-prod-chain-scheduler`, and `StartExecution` by that session in the same second; the execution
  `226adda1-…-841c0c8b1529`, the machine's third (the first two by hand), `SUCCEEDED` at 06:45:20. Its
  `startWorkflowRun` started `wisIec9vNuC4No1` with the `ClientToken` `<execution name>-app-etl`, and
  `get-workflow-run` reads **`RunType` `ON_DEMAND`**, `SUCCESS` from 06:30:22 to 06:43:01 (758 s): `transform`
  118 s, `process` 487 s, `summarize` 6 s, `write_result` 5 s. The Glue job `jr_6c8d2e06…e99a` (06:31:09 to
  06:32:58): *"reading SELECT trade_date, desk, instrument, quantity, price FROM lake.curated.trades"*, *"read 30
  row(s)"*, *"wrote 30 row(s) to the table at s3://awsds-prod-outputs/app-etl/tables/trades_notional/"*, the
  training sets at 24, 6 and 30 lines; four `GetDataAccess` at 06:32:12 and 06:32:39 to `awsds-prod-job-exec` on
  the lake's `curated.trades`, through `vpce-05f87e3d8b6ce302d`, INT-03's read under the job role; the processing
  job `app-etl-20261025T063334` `Completed` (06:33:35 to 06:38:58).
- **[Claude] 07:00, the train chain**: `StartExecution` at 07:00:36 by the same Scheduler session; the execution
  `906adda8-…-0739f9833f3e` `SUCCEEDED` at 07:07:38; the run `ouuzAXNpOfPrTV4` `ON_DEMAND`, `SUCCESS` in 296 s
  (`train` 219 s, `evaluate` 5 s); the training job `app-etl-train-20261025T070126` `Completed` (07:02:35 to
  07:04:29, 114 billable seconds) as `awsds-prod-job-exec`, with network isolation, inter-container encryption
  and the data key on its volume and its output, `validation:rmse` 1016.31; `evaluation.json` at 07:05:42.
- **[Claude] The failure rules stayed quiet**: `AWS/Events` `TriggeredRules` holds no datapoint for the four rules
  of the two chains over each run's window, the instrument that read `awsds-prod-model-approval`'s triggers at
  01:28 and 01:29.
- **[Claude] The schedule's date never reached a chain**: both executions' input reads
  `"scheduledTime":"<aws.scheduler.scheduled-time>"`, the schedule's stored `Target.Input` the same
  text. The module's `jsonencode` escapes the angle brackets, and the Scheduler substitutes none of it; no chain
  forwards the field (3.5).
- **[Claude] 07:30, the paused chain** (verification xxiv's third clause), read at 07:32:01: the warehouse
  schedule `DISABLED` on `cron(30 7 * * ? *)` UTC, and the machine's executions the two by hand of 01:49:52
  (`FAILED`) and 01:59:59 (`SUCCEEDED`) alone, while the two `ENABLED` schedules had fired at theirs. The lever
  holds.
- **[Claude] `./aws/orchestration.py`** at 07:16, `workloads-egress/` already down: every Production check passes,
  the three workflows `READY` with `TriggerMode` `manual_only` and their definitions at `v0.4.2`'s `VersionId`s,
  `OR-8` *"2 event(s), every caller is awsds-deploy-prod"*, `OR-9` on the three chains (the warehouse's schedule
  `DISABLED`); Staging's workflows and chains absent, a note. The failed calls of its section 14 are the profiles
  of identities with no SSO session.

## 2026-10-25 — `orchestration-v0.2.1`: the schedule's input carries the placeholder literally

*Claude's hand, at the user's request to prepare what needs no environment (*"Aproveite para adiantar e preparar
qualquer passo pendente do plano que não dependa do ambiente no ar."*), as the infrastructure user with
`InfrastructureAccess`, plans only. Times UTC.*

- **[Claude] The module**: `chains.tf` writes the schedule's input as a template with the chain's key alone
  encoded, `{"chain":<key>,"scheduledTime":"<aws.scheduler.scheduled-time>"}`; a scratch configuration printed the
  rendered string with literal angle brackets. Planned against `production/orchestration/` from the local path
  (Recipe B's first step): *"Plan: 0 to add, 3 to change, 0 to destroy."*, each schedule's `input`, which the plan
  renders as `jsonencode( # whitespace changes`; the caller back on its pin, re-initialised, `No changes`.
- **[Claude] The tag**: read from origin at the moment of tagging, `orchestration-v0.2.0` the last; the commit
  `8f3cfba8`, the tag `orchestration-v0.2.1` on it, pushed alone with the branch and read back by `git ls-remote`.
- **[Claude] The callers**: both slices pin `orchestration-v0.2.1` (`4c9c7fa0`). Production plans *"0 to add, 3
  to change, 0 to destroy."*, the three inputs; Staging's slice is down and plans its 21 resources from the
  defaulted release, which the pipeline's Staging leg applies.
- **[Claude] The pause, prepared**: between sittings `workloads-egress/` is down and a scheduled run fails on the
  absent endpoints, so the app-etl and train chains' `schedule_enabled = false` is written in
  `production/orchestration/` beside the warehouse chain's and saved as a plan, *"Plan: 0 to add, 3 to change, 0
  to destroy."*: the three inputs and the two states `ENABLED` → `DISABLED`. The apply waits for the user's
  decision (the waiting list).

## 2026-10-25 — with the environment down: verification xiv read from the network ACLs

*Claude's hand, at the user's request to prepare what needs no environment, as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`), reads only. Times UTC.*

- **[Claude] xiv**: `describe-network-acls` on `VPC-Workloads` and on Staging's VPC reads one ACL each, the
  default, over six subnets, rule 100 allowing all traffic in and out before the final deny; the `vpc` module
  declares no network ACL (`main.tf`, *"NACLs stay at the default allow, by decision (step 2.3)"*). The guide's
  outbound deny-all was never applied, and the workers reached the endpoints through the default ACL in every
  run from 2026-10-23 to 2026-10-25.

## 2026-10-25 — with the environment down: xvi, xvii, xxi, xxiii and xxviii from the trail and the simulator; the processing output under `aws/s3`

*A read-only agent of this session took the readings as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`), at the user's request to prepare what needs
no environment; Claude's hand for the spot checks and the template's change. The simulator ran with
`aws:RequestedRegion` and `aws:ResourceOrgID` in its context. Times UTC.*

- **[agent] xvii**: at each save, `awsds-deploy-prod` made the key calls `airflow-serverless.amazonaws.com` invoked
  on `alias/awsds-prod-data` under the workflow's ARN, `GenerateDataKey`, `Decrypt` and a `CreateGrant` naming
  `airflow-serverless.us-west-2.amazonaws.com` as grantee and retiring principal (00:57:35 to 00:57:40 on
  2026-10-25), and an S3-forwarded `Decrypt` in the same session; `awsds-deploy-staging` the same in Staging. At run
  time the execution role made no S3-forwarded `Decrypt`: one `GenerateDataKey` per app-etl run, the result write;
  its `s3:GetObject` on the release's YAML and code reads `implicitDeny`, `awsds-deploy-prod`'s `allowed`. The
  service reads the definition and the code under the save's grant.
- **[agent] xxviii**: `app-etl/outbox/report.json` at 06:43:01 under the data key, after the execution role's
  S3-forwarded `GenerateDataKey` at 06:43:00; the simulator matches the key policy's `AllowTheWorkflowRolesViaS3`
  and the role's `UseTheDataKeyThroughS3`. `v0.4.2`'s workflow writes no inbox marker, so that clause is
  unexercised. The lake read is refused: `GetObject` on `awsds-data-curated`, `-raw` and `-dropbox`, `ListBucket`
  and `GetDataAccess` read `implicitDeny` for the three execution roles, by their policy and their boundary.
- **[agent] xxi**: with the live bucket policy as resource policy, `PutObject` and `DeleteObject` on
  `applications/app-etl/` read `explicitDeny` for `awsds-prod-job-exec`, matched by
  `DenyWritesToApplicationsButTheReleaseRoles` alone; `allowed` on `app-etl/work/job/` for it and on
  `applications/` for `awsds-deploy-prod`; the release copy is twelve objects under `applications/app-etl/v0.4.2/`,
  00:55:13 to 00:55:31, `MANIFEST.sha256` last. **[Claude]** read the policy's nine `Deny` statements back, that one
  among them.
- **[agent] xxiii's image half**: Sandbox's trail names `test-experimentation`'s project role, session `SageMaker`,
  pulling `awsds-prod-ecr-app-etl` in the same second as each of nine `CreateProcessingJob` calls by that role
  (2026-10-24 19:08:22 to 2026-10-25 05:40:10), the image by digest; Production's trail holds the same pulls by
  account.
- **[agent] xvi**: the workers' addresses fell in both AZs' subnets in every app-etl and train run, the endpoints
  single-AZ in `private-usw2-az1`, no `ecr.*` and no `monitoring` endpoint; the logs arrive, `IncomingLogEvents` 105,
  142 and 104 on `/awsds/prod/wf/app-etl` in the 21:00, 01:00 and 06:00 hours; no MWAA Serverless or Airflow metric
  namespace exists in the three accounts over `list-metrics`' 14 days, which a `monitoring` endpoint would turn into
  a reading.
- **[agent, Claude] The processing output under `aws/s3`** (`EXC-22`): `app-etl/work/job/trades.summary.json`,
  written at 06:38:54 by the processing job, is SSE-KMS under the AWS managed key `aws/s3`, read back by Claude
  with `head-object` against both keys' ids; `report.json` is under the data key. The job's
  `ProcessingOutputConfig` names no `KmsKeyId` while its volume carries the data key. **[Claude] The template**:
  `examples/app-etl/workflows/app-etl.yaml` gains `ProcessingOutputConfig.KmsKeyId: "{env.PROJECT_KEY_ARN}"`, which
  the render resolves to each account's data key and the manifest to the Sandbox project's key; the render check and
  the template's 31 tests pass. The GitLab MR and its tag are the user's.
- **[agent, Claude] A refusal during 5.4's `CreateModel`**: at 01:29:33 `awsds-prod-job-exec`, session
  `sagemaker-inference`, was refused `sagemaker:DescribeModelPackage` on version 1, *"is not authorized to
  perform: sagemaker:DescribeModelPackage"*, read back by Claude; the model and the transform completed. SageMaker
  describes the package as the model's role and goes on without it today.

## 2026-10-25 — `production/orchestration/` on `orchestration-v0.2.1`, the schedules paused between sittings

*Claude's hand, on the user's authorization in chat (*"Autorizo o apply do plano salvo de production/orchestration
(0 to add, 3 to change: as três entradas corrigidas e os agendamentos app-etl e treino para DISABLED), como usuário
de infraestrutura com InfrastructureAccess (awsds-infra-prod)."*), as the infrastructure user with
`InfrastructureAccess`; the forked session told before the write. Times UTC.*

- **[Claude] The apply** of the plan saved at 07:27: at 14:39:24, *"Apply complete! Resources: 0 added, 3 changed, 0
  destroyed."*, the three schedules modified in place; re-planned `No changes`.
- **[Claude] Read back** at 14:39:56 with `get-schedule`: `awsds-prod-chain-app-etl`, `-app-etl-train` and
  `-app-etl-warehouse` `DISABLED` on `cron(30 6 * * ? *)`, `cron(0 7 * * ? *)` and `cron(30 7 * * ? *)`, each
  `Target.Input` now `{"chain":"<key>","scheduledTime":"<aws.scheduler.scheduled-time>"}` with the angle brackets
  literal. Whether the Scheduler substitutes the literal form is read at the next firing, when a sitting turns a
  schedule on by a commit.

## 2026-10-25 — the plan read for what is left; the next release's sitting written

*Claude's hand, with two editing agents of this session, at the user's request to review the documentation, the
runbooks and the Terraform comments against the session's learnings, to prepare what can be anticipated and to
review what is left; no AWS write.*

- **[Claude]** The stage file's status cell ends with what is left on 2026-10-25, its stale clauses corrected
  against this log; `runbooks/promotion.md` §N orders every step left in Stages 8, 9 and 10 by the sitting that
  runs it (nothing up, the release through Staging and Production, the warehouses, a Sandbox space, the
  deliberate exercises, what waits on something else). The next tag needs PR #258 merged and `main` pushed to the
  GitLab mirror first, since the mirror at `79651026` holds `production/orchestration/` on `orchestration-v0.2.0`
  with the app-etl and train schedules `ENABLED` (the waiting list).
- **[Claude]** The documentation, runbooks and Terraform comments read against the learnings: Staging's release
  stays until the user's `make down` (decision 27), the governed warehouse is a Lake Formation-managed datashare,
  `EXC-22` in `GOVERNANCE.md`'s encryption rule and the threat model, the save's KMS grant behind every workflow
  run, the plan's `# whitespace changes` on a JSON string in `terraform-changes.md`, the principal-filtered
  `list-permissions` in `log-debugging.md`, and `aws/orchestration.py`'s report texts.
