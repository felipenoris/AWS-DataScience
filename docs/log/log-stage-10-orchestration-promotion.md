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
