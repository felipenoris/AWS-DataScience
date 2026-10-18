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
