# Log — Stage 9 — Deployment target platforms

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-09-deployment-targets.md`](../plan/stages/stage-09-deployment-targets.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-16 — pass 1 written in a cloud session, nothing applied

- **[user] The pass is written from a cloud session.** In the Claude project's thread "Plano do
  AWS-DataScience em paralelo", at 05:56 UTC, the user answered the card *"Avançar a etapa 9 escrevendo o
  código aqui ou numa sessão no seu Mac?"* with *"Código aqui"*: Claude writes pass 1 in a pull request
  (PR #144), and a session on the laptop reads, plans, runs the battery and applies with the user's
  authorization. The card's context, in Claude's words, said that no decision of the stage blocks the
  pass, that the recommended options would be followed, and that 3.7 would refuse serverless inference
  without waiting for Stage 17's reading. The cloud session holds no AWS credential: no `aws` call, plan
  or battery ran in it, so nothing below is a measurement of AWS, and pass 0's readings come first on the
  laptop.
- **[Claude] Decisions taken as recommended, under that answer.** Decision 4: the window is
  `var.debug_window_end`, a `DateLessThan` on `aws:CurrentTime` whose default, `2026-01-01T00:00:00Z`,
  sits in the past; opening it is one apply with `-var debug_window_end=<the approved end>`, and a
  `check` block warns on every plan while it is open. Decision 9: shape (a), the `Workloads` OU document.
  Decision 10: both Sandbox readers, matched by `aws:PrincipalArn`. Step 3.7: shape (b), a deny in the
  same document. The roles name `awsds-prod-outputs`, `awsds-prod-derived` and `alias/awsds-prod-data`,
  the contracts `./aws/deploytargets.py` reads (`OUT_BUCKET`, `RESULTS_BUCKET`, `PROD_CMK_ALIAS`), so pass
  3 creates them under those names; decisions 1, 2 and 11 stay pass 3's. Which role an application's
  job runs as in Staging and Production, among the three names Stage 8 step 2.5 lists, stays that
  step's question; this pass creates Stage 9's `awsds-prod-job-exec`, the name Stage 5a step 1.4's
  drop-box statements carry.
- **[Claude] 7.3, the ECR non-grant.** A cross-account pull of the application image needs the
  repository policy only, no key grant: ECR decrypts a pull through the grants it holds on the
  repository key, so the puller needs no `kms:Decrypt`, and no statement of this pass grants one.
- **[Claude] `production/sagemaker/`, rank 46, `[P]`** (steps 3.1, 3.2, 6.1, 6.2):
  - `awsds-prod-job-exec` trusts `sagemaker.amazonaws.com` under `aws:SourceAccount` and
    `glue.amazonaws.com` with no condition. It holds the catalog reads and
    `lakeformation:GetDataAccess`; read and write on the outputs and derived buckets; the account data
    key through S3, matched by its alias; the drop-box pickup under Stage 5a's prefix, with the lake key
    through S3; the `app-etl` image pull; the writes to the six job log groups it declares;
    `cloudwatch:PutMetricData` held to the job namespaces; and the network interfaces a job in a VPC
    needs, with Glue's tag on them. No S3 on a lake bucket.
  - The job log groups `/aws/sagemaker/ProcessingJobs`, `/aws/sagemaker/TrainingJobs`,
    `/aws/sagemaker/TransformJobs`, `/aws-glue/jobs/output`, `/aws-glue/jobs/error` and
    `/aws-glue/jobs/logs-v2`, at 30 days, under the AWS-owned key until pass 3's CMK and the CloudWatch
    Logs statement step 1.1 lists.
  - `awsds-prod-model-app-etl` and its policy: register and approve for `awsds-deploy-prod` alone, read
    the versions for `awsds-deploy-staging`, read the status for the Sandbox account's persona role and
    project role by `aws:PrincipalArn`. Each reader's own half exists already: the persona's is
    `DataScientistAccess`'s `ReadSageMakerStatus` (`Describe*`, `List*` on `*`), the project role's is
    AWS's `SageMakerStudioProjectRoleMachineLearningPolicy`, whose `SageMakerCrossAccountPermissions`
    (v44, read on AWS's page) admits `DescribeModelPackage`, `DescribeModelPackageGroup` and
    `ListModelPackages` on another account's resources. So no Sandbox policy is written, and 3.4 measures
    both halves.
  - `awsds-prod-debug` trusts the production persona's reserved role (one match by pattern, or the plan
    fails) while the window is open and only through this region's STS endpoint (`aws:RequestedRegion`):
    a call to the global endpoint is logged in `us-east-1`, where no rule watches (AWS's page on STS
    endpoints). It reads the outputs bucket, decrypts through S3 with the account data key, reads the six
    job log groups, and holds SageMaker `Describe*` and `List*`; no lake reach and no write.
  - The alarm is two rules, `awsds-prod-debug-assume` on STS `AssumeRole` and
    `awsds-prod-debug-assume-console` on the sign-in service's `SwitchRole`, both in state
    `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`, to the account's alerts topic, with a message that
    names the event and carries no credential. That a console switch records `SwitchRole` with the role
    in `additionalEventData.SwitchTo` is inferred from published examples, not read here; 6.3 reads which
    rule fires, or whether the trust's region condition refuses the console switch.
- **[Claude] The `Workloads` OU document (3.5, 3.7).** Nine statements, 2,499 characters minified of the
  5,120 the slice enforces: sagemaker-denies v0.2.0's five, copied into
  `awsds-org-scp-ou-workloads.json`, and `DenySageMakerServerlessInference`. `job-denies.tf` instantiates
  the module at its tag, and a precondition in `policies.tf` compares the copy with the module's
  rendering on every plan and names the Sid that drifted. The battery gains eight `ou` rows for
  Production, run in phase 4b after the apply (`scp-battery.md`): each deny row breaks one setting and
  keeps the other four, because AWS names the policy and never the statement, and the two allow rows are
  the same calls with nothing broken. Every call names a role, an image, a security group, a key or a
  model that does not exist, so an authorized call creates nothing. `readback.py` counts `NotAction`
  beside `Action`, which `DenySageMakerInstanceCeiling` uses.
- **[Claude] The 3.7 deny keys on the memory size, not on `VpcConfig`.** The plan's wording, a deny of
  `CreateEndpointConfig` without a `VpcConfig`, cannot be written: an endpoint configuration carries no
  VPC field, and the Service Authorization Reference lists no VPC condition key for the action (read
  2026-10-16). The statement denies `sagemaker:CreateEndpointConfig` when `sagemaker:ServerlessMemorySize`
  is present (`Null` = `false`). `MemorySizeInMB` is required in a `ServerlessConfig`, so every serverless
  variant should populate the key; the battery's serverless row is what proves it. Stage 17 4.4's reading
  keeps its use: it says whether the service refuses a serverless configuration over a VPC-bound model on
  its own.
- **[Claude] `sagemaker:VolumeKmsKey` against the reference's `sagemaker:VolumeKmsKeyArn`.** The module's
  volume deny names `sagemaker:VolumeKmsKey`, which 6i populated (a processing job naming its
  `VolumeKmsKeyId` was accepted under the D13 boundary, 2026-10-11). The Service Authorization Reference
  lists `sagemaker:VolumeKmsKeyArn` for the job creates (read 2026-10-16). The battery's compliant row
  reads it again: a compliant job refused means the old name stopped populating.
- **[Claude] `production/workloads-egress/` (3.3a).** From `vpc-egress-v0.11.1` to `v0.17.0`, with six
  endpoints, `sts`, `logs`, `kms`, `glue`, `sagemaker.api` and `secretsmanager` (0.060/h), and the DNS
  Firewall on, its allow-list AWS's namespaces only (`amazonaws.com.`, `*.amazonaws.com.`, `api.aws.`,
  `*.api.aws.`) under `TRUST_REDIRECTION_DOMAIN`. `ecr.api`, `ecr.dkr` and `athena` leave the module's
  core: a SageMaker job pulls its image as its role through the service. While the slice is up,
  `gitlab.awsds.internal`, `proxy.awsds.internal` and every `prod.awsds.internal` name answer NXDOMAIN
  in `VPC-Workloads`; nothing there reaches either host today (no peering to `VPC-SharedServices`, and a
  proxy plane that refuses everything). A Production `make up` raises the slice; `make gitlab-up` does
  not (`--only tooling,egress,runners`). Validated against a local copy of the tag, the lock unchanged;
  no plan ran.
- **[Claude] What step 2.4's choice of the job's network changes here.** A Glue job given a network
  connection runs in `VPC-Workloads` and calls Lake Formation from it, so that choice puts
  `lakeformation` in the slice before the job runs, and the job's `vpcEndpointId` reading decides whether
  it stays (Stage 10 step 0.5). Two more questions ride on the same choice and are unread: whether the
  job publishes metrics through the VPC, which would need `monitoring` [inferred]; and whether its Spark
  driver and executors resolve this VPC's host names or their reverse lookups, which the firewall's list
  refuses [uncertain]. 2.4's first run reads both.
- **[Claude] `./aws/deploytargets.py`** (3.6, 6). `DT-11` reads the `Workloads` OU through Organizations as
  the delegated administrator, the attached `awsds-org-scp-ou-workloads` and its six job Sids: a missing
  Sid is a note before the apply and a failure after it, a detached document a failure. `DT-9` now fails
  a debug window that does not pin `aws:RequestedRegion`, and reads each rule's state: `ENABLED` fails,
  because it receives no `AssumeRole`. Run against a stand-in `aws` on `PATH`, not against AWS.
- **[Claude] Two findings outside the pass, recorded and not acted on.** AWS Support's answer quoted in
  prowler issue 2810 says Glue sends no `aws:SourceAccount` when it assumes a role, which is why the job
  role's Glue statement carries no condition, and step 2.4's first Glue run reads it. If the answer
  holds, `awsds-data-catalog-maintenance`'s trust (`GlueServiceOnly`, under `aws:SourceAccount`) refuses
  Glue too, a second reason no crawler can run, behind open question 19 [inferred, not measured]. And
  Stage 8's misuse rules on the deploy roles share the global-endpoint blind spot that `DT-9`'s new check
  closes for the debug role [inferred].
- **[Claude] Corrections outside the ask.** `docs/PRICING.md` §3 counted `VPC-SharedServices` at 13
  endpoints and `docs/plan/conventions.md` at 14; both now say 12, Stage 7's count. `docs/AWS_STATE.md`
  gave the estate's fixed rate as 0.390/h; it is 0.410/h, §3's sum for 41 endpoints.
- **[Claude] What the laptop session runs, in order, as the infrastructure user** (one login on the
  `awsds` session covers every profile below):
  1. Pass 0: 7.1 `./aws/cicd.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`, `CI-2` and
     `CI-3` green; 7.2 `./aws/datalake.py`, `DL-5` green and the drop-box statements naming
     `awsds-prod-job-exec`.
  2. `identity/org-policies/` in the Identity account as `InfrastructureAccess` (`awsds-infra-identity`),
     Recipe A: the plan changes one document's `content` and `description` and nothing else, and the apply
     needs the user's word.
  3. The battery's Stage 9 rows in Production as `InfrastructureAccess` (`awsds-infra-prod`),
     `./aws/probes/scp-battery.py --phase ou`, then the *must still succeed* trio.
  4. Before `production/sagemaker/`, in Production as `awsds-infra-prod`: `aws logs describe-log-groups
     --log-group-name-prefix /aws/sagemaker/` and `--log-group-name-prefix /aws-glue/` read none of the six
     groups (one that exists is imported, or the apply fails), and the `DataScientistProdAccess` reserved
     role exists. Then `./scripts/gen-backend-hcl.py production sagemaker`,
     `./scripts/gen-tfvars.py production sagemaker`, `init`, plan, and the apply on the user's word (3.4),
     whose plan also reads the lake's state as `awsds-infra-data` and the Sandbox identity as
     `awsds-infra-sandbox-1`.
  5. `production/workloads-egress/` at the next Production `make up`, which plans it like any `[E]` slice.
  6. 3.4's registry proof and 6.3's window, by the user; `./aws/deploytargets.py` after each.

## 2026-10-17 — the battery's Stage 9 rows, read before the apply

*The run is the user's, on the laptop: `./aws/probes/scp-battery.py --phase ou`, for Stage 6e's rows
([its log](log-stage-06e-claude-code-bedrock.md)), so the phase's Stage 9 rows ran too, in Production as
`InfrastructureAccess` (`awsds-infra-prod`). The driver stamps the laptop's clock, about 23:21 UTC. Below
are those rows, copied verbatim from the user's paste with the phase's stamp and totals, and one Workloads
row of Stage 6b's for the policy id.*

- **[user] The rows**, excerpt:

  ```
  SCP battery - 2026-10-17 20:21:03  (phase ou)
    MARK PHASE    ACCOUNT   EXPECT OUTCOME       DETAIL                 PROBE
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: datazone:ListDomains
    note ou       prod      allow  UNTESTED                             workloads: compliant sagemaker:CreateProcessingJob still authorized (3.5 contrast)
    note ou       prod      deny   UNTESTED                             workloads: CreateProcessingJob with no VpcConfig (DenySageMakerJobsOffVpc)
    note ou       prod      deny   UNTESTED                             workloads: CreateProcessingJob on ml.m5.2xlarge (DenySageMakerInstanceCeiling)
    note ou       prod      deny   UNTESTED                             workloads: CreateProcessingJob not isolated (DenySageMakerJobsWithoutNetworkIsolation)
    note ou       prod      deny   UNTESTED                             workloads: CreateProcessingJob unencrypted between containers (DenySageMakerJobsWithoutInterContainerEncryption)
    note ou       prod      deny   UNTESTED                             workloads: CreateProcessingJob, no VolumeKmsKeyId (DenySageMakerJobsWithoutVolumeEncryption)
    FAIL ou       prod      deny   ALLOWED       reached-authorization  workloads: serverless CreateEndpointConfig (DenySageMakerServerlessInference, 3.7)
    ok   ou       prod      allow  ALLOWED       reached-authorization  workloads: instance-backed CreateEndpointConfig still authorized (3.7 contrast)
  32 as expected, 1 unexpected, 13 not measured
  ```

- **[Claude] The rows ran before the apply.** The order of 2026-10-16 runs them at step 3, after
  `identity/org-policies/` at step 2, which has not run: the `Workloads` document attached in Production
  still carries its three statements (`AWS_STATE.md`), so this is each row's before half.

- **[Claude] The serverless row is its statement's negative control.** A `create-endpoint-config` with a
  `ServerlessConfig` reached authorization in Production: serverless inference is refused nowhere, as
  `AWS_STATE.md` says, and the `FAIL` is that state. After the apply the row must read `DENY-SCP` naming
  `p-83t232f4`, the id the `Workloads` rows already name. The instance-backed contrast reached
  authorization, as it must on both sides of the apply.

- **[Claude] The six processing-job rows did not reach their wording.** Each read `UNTESTED`:
  `create-processing-job` answered neither `ValidationException` nor a deny, the compliant contrast
  included. With no statement attached, a deny row that reached the validation would read `ALLOWED`, a
  `FAIL` like the serverless row's, and none did. The compliant row is meant to read `ALLOWED` on both
  sides of the apply, since it attributes the five denies and reads `sagemaker:VolumeKmsKey`, and it did
  not. The report keeps only the table, so the reply is unread.
  [inference] One cause would fit all six rows and spare both endpoint-configuration rows: a refusal after
  authorization that a configuration call never meets, such as an instance quota of 0 for processing jobs
  in Production. Reading that reply is owed before step 3 relies on the row.

## 2026-10-18 — pass 0 read and pass 1 applied, from the laptop

*Claude's hand, in the session "Execução local no Mac", as the infrastructure user (`InfrastructureAccess`).
The user's authorization, in that chat: "Você está autorizado a utilizar leituras com usuário sso infra e
realizar os applies necessários de terraform", and, for this pass's document, "Autorizo os applies de SCP em
identity/org-policies das Stages 9 e 10 e a bateria de SCP depois de cada um". The app refused to hand the
SCP apply to a parallel session, so it ran here.*

- **[Claude] 7.1.** `./aws/cicd.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`: every check
  passed. `CI-2` reads a boundary on each of the four deploy roles and `CI-3` every trust naming
  `awsds-prod-runner-deploy` with `sts:AssumeRole` only.
- **[Claude] 7.2.** `./aws/datalake.py`: 0 checks failed. `DL-5` reads `CROSS_ACCOUNT_VERSION=4`,
  `SET_CONTEXT=TRUE`, and the drop-box policy names `awsds-prod-job-exec` in
  `AllowProductionPickupReadDelete` and `AllowProductionPickupList`.
- **[Claude] The six `UNTESTED` replies of 2026-10-17 are quota refusals.** CloudTrail in Production holds
  six `CreateProcessingJob` events between 23:21:12 and 23:21:18 UTC, each `ResourceLimitExceeded`: *"The
  account-level service limit 'ml.m5.large for processing job usage' is 0 Instances"*, and
  `ml.m5.2xlarge` for the ceiling row. The inference of 2026-10-17 holds: the service checks the quota after
  authorization and before the role. Production and Staging both read 0 for `ml.m5.large` (`L-8541302D`),
  `ml.m5.xlarge` (`L-0307F515`) and `ml.m5.2xlarge` (`L-1D84B9D2`) for processing job usage, so no
  processing job runs in either account until a quota request is granted. `aws/probes/probes.py` now reads
  `ResourceLimitExceeded` as authorized on the six rows (`_JOB_AUTHORIZED`), and the runbook's compliant row
  says so.
- **[Claude] 3.5 and 3.7 applied.** `identity/org-policies/` as `awsds-infra-identity`: plan 0 to add,
  1 to change, 0 to destroy, `aws_organizations_policy.this["awsds-org-scp-ou-workloads"]` (`p-83t232f4`)
  in place, content and description, `policy_document_bytes` 640 → 2499. Apply 19:54:06-19:54:15 UTC,
  *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*; re-plan *"No changes."*;
  `describe-policy` reads nine statements, `DenyInteractiveSageMakerSurface`, `DenyDataZoneEntirely`,
  `DenyAthenaSparkStartSession`, `DenySageMakerJobsOffVpc`, `DenySageMakerInstanceCeiling`,
  `DenySageMakerJobsWithoutNetworkIsolation`, `DenySageMakerJobsWithoutInterContainerEncryption`,
  `DenySageMakerJobsWithoutVolumeEncryption`, `DenySageMakerServerlessInference`. Every peer session was
  told before the apply, and the session holding PR #108 confirmed its branch carries the same document.
- **[Claude] The battery's after-half**, `./aws/probes/scp-battery.py --phase ou`, started 19:55:13 UTC (the
  driver stamps the laptop's clock), the Stage 9 rows verbatim with the phase's totals:

  ```
  SCP battery - 2026-10-18 16:55:13  (phase ou)
    MARK PHASE    ACCOUNT   EXPECT OUTCOME       DETAIL                 PROBE
    ok   ou       prod      allow  ALLOWED       reached-authorization  workloads: compliant sagemaker:CreateProcessingJob still authorized (3.5 contrast)
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: CreateProcessingJob with no VpcConfig (DenySageMakerJobsOffVpc)
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: CreateProcessingJob on ml.m5.2xlarge (DenySageMakerInstanceCeiling)
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: CreateProcessingJob not isolated (DenySageMakerJobsWithoutNetworkIsolation)
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: CreateProcessingJob unencrypted between containers (DenySageMakerJobsWithoutInterContainerEncryption)
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: CreateProcessingJob, no VolumeKmsKeyId (DenySageMakerJobsWithoutVolumeEncryption)
    ok   ou       prod      deny   DENY-SCP      p-83t232f4             workloads: serverless CreateEndpointConfig (DenySageMakerServerlessInference, 3.7)
    ok   ou       prod      allow  ALLOWED       reached-authorization  workloads: instance-backed CreateEndpointConfig still authorized (3.7 contrast)
  39 as expected, 0 unexpected, 7 not measured
  ```

  Each Stage 9 row is as expected, and both halves of each statement are now read: the 2026-10-17 run is
  the before half. The seven not measured are the phase's standing notes (Athena's denies name no policy;
  Data Governance and Identity hold no subnet). The *must still succeed* trio in Production answered:
  `sts get-caller-identity`, `s3 ls` and `ec2 describe-vpcs` (three VPCs).
- **[Claude] 3.6.** `./aws/deploytargets.py`: `DT-11` passes, *"attached, the 6 job Sids present"*.
- **[Claude] 3.4 applied.** The pre-reads: no log group under `/aws/sagemaker/` or `/aws-glue/` in
  Production, so nothing to import, and one `AWSReservedSSO_DataScientistProdAccess_*` role.
  `production/sagemaker/` as `awsds-infra-prod`: plan 16 to add, 0 to change, 0 to destroy (the two roles
  and their inline policies, the package group and its policy, the two rules and their targets, the six job
  log groups). Apply 19:58:55-19:59:07 UTC, *"Apply complete! Resources: 16 added, 0 changed, 0 destroyed."*;
  re-plan *"No changes."*. `./aws/deploytargets.py` after it: `DT-3` (the group's policy, 3 statements),
  `DT-4` (glue and sagemaker service principals only; no S3 allow reaches a lake bucket, the drop-box
  excepted), `DT-7`, `DT-9` (the window closed, ending 2026-01-01T00:00:00Z; both rules
  `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`) and `DT-11` pass; `DT-1` notes `alias/awsds-prod-data`
  absent, pass 3's.
- **[Claude] 3.3a planned, read-only.** `production/workloads-egress/`'s first plan: 15 to add, the six
  endpoints (`sts`, `logs`, `kms`, `glue`, `sagemaker.api`, `secretsmanager`) and the DNS Firewall's nine
  pieces. Nothing applied: the slice is `[E]`, and the next Production `make up` raises it.
- **[Claude] 4.0 and 5.2.** `./aws/AZs.py`: six accounts, mappings identical. `./aws/account-bpa.py`: all four
  flags `true` in the six measured accounts, Staging included. `DT-10` reads `DataScientistStagingAccess`
  with `DenyEveryWrite` and no Athena allow (verification viii, the policy half).
- **[Claude] Owed after this pass.** 3.4's registry proof and 6.3's window are the user's; pass 2 waits on
  decision 3; the processing-job quotas in Production and Staging are a quota request, the user's, before any
  job runs there (Stage 10's processing step included).

## 2026-10-18 — verification viii's assignment half, and text the stage had overtaken

*Claude's hand, in a task the orchestrating session ran on the laptop (branch
`claude/stages-09-10-18-readings`), with the environment down. Every call is a read, as the infrastructure
user (`InfrastructureAccess`) through `awsds-infra-identity`; nothing was applied.*

- **[Claude] Verification viii, the assignment half.** `./aws/list-identities.py`, report stamped
  2026-10-18T22:20:57Z, section 6 empty: `Staging Account` carries seven assignments, the seven of 6b's
  last reading ([its log](log-stage-06b-development-becomes-staging.md), 2026-09-06):
  `AWSAdministratorAccess` to the infrastructure user (`USER`, re-asserted by the Control Tower account
  update of 6b step 3.5, D32), the landing zone's `AWSOrganizationsFullAccess`, `AWSPowerUserAccess` and
  `AWSReadOnlyAccess` to their groups, `DataScientistStagingAccess` to `sso-group-data-scientists`,
  `DeploymentManagerAccess` to `sso-group-deployment-managers` and `InfrastructureAccess` to
  `sso-group-infrastructure`. `DataScientistStagingAccess` is assigned in no other account.
- **[Claude] The assignment's provenance, from CloudTrail.** `lookup-events` in the Identity account,
  `us-west-2`, since 2026-08-20: one `CreateAccountAssignment`, at 2026-09-06T04:35:35Z, by
  `InfrastructureAccess`, no error code, permission set `DataScientistStagingAccess`, principal type
  `GROUP` with the id of `sso-group-data-scientists`, target `Staging Account`; and two
  `DeleteAccountAssignment` in the same account at 04:35:25Z, `DataScientistAccess` and
  `DevEnvStewardAccess`. Those three are 6b step 2.1's apply, *"1 added, 0 changed, 2 destroyed"*, and no
  call has touched the assignment since. With `DT-10`'s reading of the policy, verification viii is
  answered: yes to both halves.
- **[Claude] 7.3 carried no marker** though this file's first entry records it (2026-10-16); the step now
  says so.
- **[Claude] Two sentences the estate had overtaken.** The Prerequisites said Stage 18 adds Staging to the
  `readers` of `production/sagemaker/`: `readers` is `SMUS_MEMBERS` (`scripts/tfhygiene/backend.py`), and
  Stage 18 step 2.3 (PR #174) gave a deployment account a list of its own, `SMUS_DEPLOYMENT_MEMBERS`,
  which `readers` does not read. And 9.1's alarms bullet said neither alarm notifies anyone: Sandbox's two
  publish to `awsds-sandbox-alerts` since 21:19Z today (PR #181, [the 5b log](log-stage-05b-redshift-serverless.md)),
  and `awsds-prod-alerts` admits CloudWatch since PR #179 (`CloudWatchAlarmsOfThisAccount`,
  [the Stage 12 log](log-stage-12-observability-finops.md)), so the copies publish there.

## 2026-10-20 — the instance-preference rows and decision 1's scoping written; Production's quotas and Bucket Keys read

*Claude's hand. The first two entries record PR #216, written offline in a task session on 2026-10-20
and merged at 21:52Z: no AWS call, plan or battery ran in it. The readings after them were taken in a
later task session as the infrastructure user (`InfrastructureAccess`) through `awsds-infra-prod`, in
Production, with the tunnel down (`NO_PROXY='*'`). Every call is a read; nothing was applied.*

- **[Claude] 3.5's instance-preference rows, written and not run** (PR #216). `aws/probes/probes.py`'s `ou`
  phase gains seven rows in Production, each `blocked`, for a job naming its types in
  `InstancePreferences`: for `CreateProcessingJob` and for `CreateTrainingJob`, a list naming
  `ml.m5.2xlarge` and a list naming `ml.m5.large` then `ml.m5.2xlarge`, each expected `DENY-SCP`, beside a
  list naming `ml.m5.large`, expected authorized; and for training, `ml.m5.2xlarge` as `InstanceType`, the
  control. Each argv was checked offline against the installed CLI's SageMaker model, and `scp-battery.md`
  moves the entry from its uncovered list to phase 4b. No `scp-battery-*` report in any checkout on the
  laptop is dated after 2026-10-19. The run is owed: the infrastructure user, account Production,
  permission set `InfrastructureAccess` (`awsds-infra-prod`), `./aws/probes/scp-battery.py --phase ou`,
  before Stage 10's processing step and Stage 17 pass 2's training job.
- **[Claude] Decision 1's scoping, written as a recommendation** (PR #216): Staging reads
  `awsds-prod-outputs/models/*/model.tar.gz`, `s3:GetObject` with no `s3:ListBucket`, as
  `awsds-staging-job-exec` and `awsds-deploy-staging`; the bucket policy alone holds them to the archives,
  because with S3 Bucket Keys the KMS encryption context is the bucket's ARN (AWS's S3 guide). The
  decision, and Stage 10 decision 6's sentence with it, stay the user's.
- **[Claude] The Bucket Keys on Production's buckets**, `s3api get-bucket-encryption` at 22:00:16Z:
  `awsds-prod-outputs` answered *"An error occurred (NoSuchBucket) when calling the GetBucketEncryption
  operation: The specified bucket does not exist"*; 1.1 creates it in pass 3, from the module. The three
  buckets `terraform-modules/s3-bucket` created in Production, `awsds-prod-releases` (`s3-bucket-v0.4.0`),
  `awsds-prod-gitlab-objects` and `awsds-prod-gitlab-backup` (`v0.3.0`), each read `aws:kms` with
  `BucketKeyEnabled: true`, as does `awsds-prod-tfstate`, the bootstrap's. Every module tag, `v0.1.0` to
  `v0.4.0`, sets `bucket_key_enabled = true` with no variable, so decision 1's finding holds for the bucket
  1.1 creates, and D31 records its zero-cost variant as unavailable on the module's buckets.
- **[Claude] Production's processing quotas**, `service-quotas list-service-quotas --service-code
  sagemaker` at 22:00:35Z: `ml.t3.medium for processing job usage` (`L-0CE343FE`) 4.0, adjustable, AWS's
  default (`get-aws-default-service-quota` 4.0); `ml.m5.large` (`L-8541302D`), `ml.m5.xlarge`
  (`L-0307F515`) and `ml.m5.2xlarge` (`L-1D84B9D2`) 0.0. The SageMaker request history is empty. Stage 12's
  reading of 2026-10-18 gave Production the same 4 ([its log](log-stage-12-observability-finops.md)). A
  Production job on `ml.t3.medium`, the type `app-etl`'s `process` task names, passes the quota, and the
  processing rows' reading of `ResourceLimitExceeded` as authorized still holds for the three `ml.m5`
  types.

## 2026-10-20 — Production's training quotas read

*Claude's hand. The first reading is the orchestrating session's; the task session it started to carry
the reading into the plan re-read it and added AWS's defaults and the ceiling's other types. Both as the
infrastructure user (`InfrastructureAccess`) through `awsds-infra-prod`, in Production, with the tunnel
down (`NO_PROXY='*'`). Every call is a read; nothing was applied.*

- **[Claude] The three `ml.m5` training quotas**, `service-quotas list-service-quotas --service-code
  sagemaker`, read by the orchestrating session at 22:22:36Z: `ml.m5.large for training job usage`
  (`L-611FA074`), `ml.m5.xlarge` (`L-CCE2AFA6`) and `ml.m5.2xlarge` (`L-AD0A282D`) 0.0. The task
  session's re-read at 22:34Z gave the same three 0.0, `get-aws-default-service-quota` 0.0 for each, and
  an empty SageMaker request history.
- **[Claude] The ceiling's other types, from the same listing**: `ml.t3.large` (`L-B95AAE44`),
  `ml.t3.xlarge` (`L-823DAB46`) and `ml.c5.xlarge` (`L-E2BB44FE`) for training 0.0, AWS's default 0.0
  each (22:36Z); `ml.t3.medium` and `ml.c5.large` have no training quota. No type inside the ceiling can
  train in Production without an increase, so Stage 10 5.1's training job waits on one.

## 2026-10-21 — the stage's text brought to `EXC-13`'s rotation and the training quotas on 2026-10-20 (PR #230), recorded

*Claude's sitting, no AWS call: the task session the orchestrating session "Stage 18 checklist" started
opened PR #230 (merged 2026-10-20T22:55:05Z), which carried two readings into the plan: `EXC-13`'s first
rotation ([the 5b log](log-stage-05b-redshift-serverless.md), 2026-10-20) and Production's training
quotas (this log's entry "Production's training quotas read", the PR's one AWS reading). It logged the
reading and not the text it changed; this entry is written on 2026-10-21 by the orchestrating session
from the PR's body and diff, with no AWS call.*

- **[Claude] 9.1, "The admin secret"**: the claim that the rotation "fails permanently" with no workgroup
  gives way to Sandbox's reading, the first rotation succeeding on 2026-10-20. `EXC-13` still gains a
  Production row: the Production secret rotates on the same schedule.
- **[Claude] The training quotas in the stage file**: the Status row, 3.5 and the instance-preference
  risk say that no type inside the ceiling can train in Production without an increase, so Stage 10 5.1's
  training job waits on one.
- **[Claude] The battery's training rows**: [`scp-battery.md`](../plan/runbooks/scp-battery.md) phase 4b
  and the comment over the rows in `aws/probes/probes.py` no longer call the quotas unread; whether
  `CreateTrainingJob` checks them after authorization still is. No probe changed.
- **[Claude] "Who executes"**: the `[user]` row reads "the log entries the user writes", as PR #228 has it
  in the other stage files.

## 2026-10-22 — the stage reviewed and prepared with the environment down

*Claude's hand, in the session "Stage 9 — revisão e preparação", one of three the orchestrating session
started on the user's request of that day to review and prepare Stages 8, 9 and 10. Every AWS call is a
read, as the infrastructure user (`InfrastructureAccess`) through `awsds-infra-prod`,
`awsds-infra-staging`, `awsds-infra-data`, `awsds-infra-identity` and `awsds-infra-sandbox-1`, with the
tunnel down (`NO_PROXY='*'`); the plans ran on Terraform 1.15.8 and were saved under `$HOME/tmp/stage-09/`.
Nothing was applied. Times UTC.*

- **[user] The request**, to the orchestrating session: *"Revise o plano dos estágios 8, 9 e 10,
  considerando o andamento atual do plano, em especial as decisões registradas na sessão atual, bem como o
  aprendizado com a conclusão do stage 18. Faça todas as leituras que não dependam do ambiente no ar.
  [...] Faça a preparação necessária para todas as etapas dos estágios 8, 9 e 10 que forem possíveis de
  serem preparadas e que não precisam da minha intervenção ou decisão."*
- **[Claude] What Stage 8's decisions of the day change here.** Its 2.5 makes this stage's
  `awsds-<env>-job-exec` the job role in Staging and Production, with Staging's twin arriving by 4.3 before
  Stage 8's pass 4 (decision 23), so 4.3 moves ahead of the rest of pass 5. Its decision 2 (`awsds/infrastructure`
  kept as pass 4's reader), 3.9 (no S3 grant to `DeploymentManagerAccess`) and decision 20 (no
  `If-None-Match` deny) leave this stage's text as it was.
- **[Claude] Lake Formation, before 1.5 and 4.1**, `get-data-lake-settings` at 04:55:27Z. Staging: no
  administrator, both default lists empty, `CROSS_ACCOUNT_VERSION` `1`, `SET_CONTEXT` `TRUE`, as Stage 18's
  pass 8 left them. Production: no administrator, both default lists
  `IAM_ALLOWED_PRINCIPALS` with `ALL`, `CROSS_ACCOUNT_VERSION` `4`, `SET_CONTEXT` `TRUE`.
- **[Claude] The job log groups**, `describe-log-groups` at 04:55:40Z: none under `/aws/sagemaker/` or
  `/aws-glue/` in Staging, whose whole list is the Control Tower forwarder's group and
  `awsds-staging-vpc-flow-logs`; Production's six at 30 days with no CMK, as 3.4 created them.
- **[Claude] The SageMaker quotas**, `service-quotas list-service-quotas` at 04:56:01Z, identical in
  Staging and Production: processing `ml.t3.medium` 4, `ml.t3.large` 4, `ml.t3.xlarge` 2, and 0 for
  `ml.m5.large`, `ml.m5.xlarge` and `ml.c5.xlarge`; training 0 for `ml.t3.large`, `ml.t3.xlarge`,
  `ml.m5.large`, `ml.m5.xlarge` and `ml.c5.xlarge`; transform 0 for `ml.m5.large` (`L-236AE59F`),
  `ml.m5.xlarge` (`L-7939E4EC`) and `ml.c5.xlarge` (`L-09C9B23C`). `ml.t3.*` and `ml.c5.large` have no
  transform quota, and `ml.c5.large` none for processing or training either. Both accounts' SageMaker
  request history is empty. So Staging's training quotas are Production's, and Stage 10 5.4's batch
  transform waits on an increase in both accounts.
- **[Claude] The instruments.** `./aws/datalake.py`: *"0 check(s) FAILED."*, `DL-5`
  `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE - the 5.4 bracket holds`. `./aws/deploytargets.py` as it stood:
  *"7 check(s) FAILED."*, every one an object of a pass not yet applied (the two buckets and the workgroup,
  Production's create-defaults, the write share, the `curated` mirror, the persona's owed allows), since
  its `built` flag turned every absence into a failure once pass 1 stood (Lesson 50).
- **[Claude] `./aws/deploytargets.py` amended.** Each check reads the pass that creates its object from that
  pass's own objects: pass 1 the job role, a package group or the debug role; pass 3 a bucket, the
  workgroup or the CMK, and Production's seated administrator for `DT-5` and `DT-6`; pass 4 one of 5.1's
  statements; pass 5 a mirror database, Staging's workgroup or CMK. `DT-4` reads `awsds-staging-job-exec`
  with no lake exception, `DT-5` reads every account's parameters (`SET_CONTEXT` everywhere,
  `CROSS_ACCOUNT_VERSION` 4 in Data Governance and Production, the value 1.5 copies), and `DT-12` reads the
  six job log groups in both accounts. Live, as the five infrastructure profiles: *"0 check(s) FAILED."*,
  16 passes and 8 notes. Against a stand-in `aws` on `PATH` serving a half-applied world, with no AWS call:
  *"11 check(s) FAILED."*, each planted defect named (a bucket without its sibling, the workgroup missing
  beside it, a Staging role reaching `awsds-data-dropbox`, Production's defaults granting with an
  administrator seated, Staging's parameters emptied, the share missing after pass 3 began, a partial
  5.3, a missing job group in each account), and `DT-11` failing on the document the stand-in did not
  serve. `aws/INDEX.md` follows.
- **[Claude] 4.3, `staging/sagemaker/`.** `awsds-staging-job-exec` with 3.1's trust and permissions, without
  the drop-box pickup, with S3 on `awsds-staging-outputs` (Stage 10 decision 17, taken 2026-10-15) and
  `awsds-staging-derived` (decision 11's name) and none on `awsds-staging-data`, the mirror's content,
  which 4.1 registers with Lake Formation; the image from Production's `awsds-prod-ecr-app-etl`, the
  repository's ARN read from `production/registry/`'s state cross-account; the six job log groups at 30
  days. `backend.py` gains `DATA_MIRRORS = ["staging"]` and the slice's registry map, `layers.py` its `[P]`
  row. Plan as `awsds-infra-staging`: *"Plan: 8 to add, 0 to change, 0 to destroy."* The inline policy is
  known after apply, since it names the groups' ARNs, as Production's was.
- **[Claude] `glue:GetConnection` on both job roles.** Stage 18's CloudTrail of 2026-10-19 shows Glue's
  `GlueJobRunnerSession`, a session of that job's role, calling `glue:GetConnection` four times before the
  job ran; `awsds-prod-job-exec` had no such action. `ReadTheJobsConnection` grants it on the account's
  connections and catalog. `production/sagemaker/` plan as `awsds-infra-prod`: *"Plan: 0 to add, 1 to
  change, 0 to destroy."*, the job role's inline policy alone, no other drift.
- **[Claude] 4.3a, `staging/egress/`.** Re-cut to `VPC-Workloads`' six (`sts`, `logs`, `kms`, `glue`,
  `sagemaker.api`, `secretsmanager`) on `vpc-egress-v0.17.0`, the firewall's list AWS's namespaces alone,
  from Stage 18's reading of this account's run of 2026-10-19: the worker called `glue` 30 times,
  `sagemaker.api` 19, `kms` 11 and `logs` 4 through the endpoints, and the job's image pull and Glue's
  job runner called from AWS's own addresses. `staging.awsds.internal` holds its NS and SOA records alone
  (read 2026-10-22), so blocking its names costs nothing. The two module versions declare the same
  resource types, so the deploy role that raises the slice in the promotion leg meets nothing new. Plan as
  `awsds-infra-staging`: *"Plan: 15 to add, 0 to change, 0 to destroy."*, the six endpoints and the
  firewall's nine pieces, the coverage precondition passing; the next `make up ENV=staging` applies it.
  `layers.py` 0.110 → 0.060/h; `docs/NETWORK.md` §10 and conventions §6 follow, `check-network-doc.py`
  clean.
- **[Claude] Two readings behind decision 12.** The lake's `DenyOutsideTrustedNetworks` admits a call made
  through a trusted gateway endpoint, by a Data Governance principal or by a service, so a Glue job's
  vended reads and writes, made as the registration role, pass from any network, while the pickup's
  direct `GetObject` and `DeleteObject` as `awsds-prod-job-exec` pass only through `VPC-Workloads`'
  gateway endpoint; and that endpoint's policy admits every bucket of the organization
  (`AllowWithinOrganization`). The deploy roles' ceiling is `CeilingIsEverythingTheIdentityPolicyGrants`
  (`Allow *`) beside the module's denies, so 9.4's grant needs no line in it.
- **[Claude] The plan corrected.** The Status row; the build table's Staging and egress rows; the contracts
  gain `awsds-staging-outputs` and a paragraph of the outputs other slices read by state key; 1.3 carries
  `datalake.py`'s `DL-8` and `DL-9`, which would fail Production's derived bucket and workgroup once
  Production joins its consumers; 1.5 the Production reading; 2.4 decision 12; 3.1 the connection read;
  3.2 `awsds-deploy-staging`'s own registry allow; 3.4's proof in two halves, the approval as a pipeline
  job on the deploy runner; 4.1, 4.3, 4.3a, 4.4's timing in the Staging leg and 4.6; 6.3's prerequisite,
  marked as an inference; 9.4 without "and its boundary"; verification xvii without a subject; the
  quota risk; the endpoint cost; and the Decisions-due header, which said no question blocks on the user.
- **[Claude] Owed, by the user or an authorized apply**: the applies of `staging/sagemaker/` (as
  `awsds-infra-staging`) and `production/sagemaker/` (as `awsds-infra-prod`) from their saved plans or a
  fresh re-plan; decision 12 and the decisions the waiting list holds; the transform and training quota
  requests before Stage 10 5.4 and 5.1.

## 2026-10-22 — `production/workloads/` on `vpc-v0.4.0` for Stage 10, and Stage 10's requirements

*Claude's hand, the same session, after the session "Stage 10 — revisão e preparação" answered the
ownership message of the morning. Its message is information, not authorization; nothing was applied.*

- **[Claude] The slices between the two stages.** This stage holds `production/workloads/`,
  `production/workloads-egress/`, `staging/egress/` and the two `data/` slices; Stage 10's 1.2 and its
  `data/` statements land in them, written by this stage alone. Stage 10 keeps `vpc-egress`'s `mwaa` group
  empty, `monitoring` joining both VPCs only when its verification xvi reads the workers' metrics refused,
  so no module release and no `GROUPS=` follow.
- **[Claude] `production/workloads/` pins `vpc-v0.4.0`** (Stage 10 1.2 item 4, the
  `mwaa-serverless-code-files-*` family `staging/foundation/` took on 2026-10-19). The module's interface
  moved by descriptions alone between the two tags. Plan as `awsds-infra-prod`: *"Plan: 0 to add, 1 to
  change, 0 to destroy."*, `module.vpc.aws_vpc_endpoint.s3` updated in place, its policy gaining
  `arn:aws:s3:::mwaa-serverless-code-files-*-us-west-2-prod` and its objects; the endpoint's id, INT-05's
  anchor, stays. `docs/NETWORK.md` §8 follows.
- **[Claude] Parity on `ecr.*`.** The Stage 10 session noted that every worker run so far had `ecr.api` and
  `ecr.dkr` present, so whether a worker needs them is unmeasured. 4.3a removes them from Staging as
  `VPC-Workloads` lacks them, so the Staging leg is where a worker that needs them fails first.
- **[Claude] Stage 10's requirements on `awsds-<env>-outputs` and `alias/awsds-<env>-data`**, written into its
  own file as the exact list and pointed to from 1.1: its decision 12's deny on `workflows/*`, which
  exempts the release job's deploy role and the account's `InfrastructureAccess` role (Stage 8 3.8's by-hand
  parity), the same pair admitted to `workflows/*` from outside `VPC-Workloads`' endpoint, the EventBridge
  notification, and the key's statements for the deploy role, the chain role, the `awsds-<env>-wf-*` roles
  and CloudWatch Logs. `awsds-staging-job-exec` already matches what it reads: Production's shape, the two
  outputs `job_role_arn` and `job_role_name`, read on the whole of `awsds-staging-outputs`, and no
  `iam:PassRole` of its own.

## 2026-10-22 — decisions 1 and 3 carry a revised recommendation

*Claude's hand, the same session, on a message from the orchestrating session "Pendências estágios 7 e 8"
relaying the user's words in that chat. No AWS call; the decisions stay the user's.*

- **[user] The instruction**, relayed verbatim from the orchestrating session's chat: *"Sim, aplique esta
  recomendação revisada na sessão do Stage 9."* The revision rests on the user's reasoning on environment
  isolation: in data science code and artifacts are promoted and data is not, and the governed lake is the
  one source of truth.
- **[Claude] Decision 3**, rewritten as "whether Staging keeps a mirror of the lake". Recommended: no
  mirror; Staging reads the governed lake read-only through Lake Formation, by the LF-Tag share Sandbox
  holds, writes only to its own catalog, buckets and key, creates the application's schemas from the
  repository at each deploy, and pins an Iceberg snapshot or reads by time travel for a reproducible
  test. Controls: no write grant outside Production on the governed catalog, the read scoped by
  `classification` with `restricted` excluded or filtered (Stage 11 decision 12), Stage 11's data events
  on every read from outside Production, and the residual accepted in `threat-model.md`. The mirror stays
  listed as the alternative. Taken, it amends D20's off-the-share and sampled-data sentences and reverses
  6b 2.3's revocation.
- **[Claude] Decision 1**, rewritten to cover what Staging reads of Production's outputs. Recommended: a
  dedicated key, and Staging reads nothing of Production's outputs, model archives included, so Stage 10
  decision 6 holds as written; a model crosses environments as a release artifact or is retrained in
  Staging from governed data, its archive carrying its data's classification. The archive read of the
  2026-10-20 entry is now option (a); the Bucket Keys finding stays.
- **[Claude] Steps 4.1, 4.4 and 4.6** point at the two recommendations and stand as written until the user
  decides; no code changed. `staging/sagemaker/`'s role serves either design: it reads through
  `lakeformation:GetDataAccess` and holds S3 on no lake bucket.

## 2026-10-22 — decisions 2, 5, 6, 7, 8, 11 and 12 taken by the user, as recommended

*Claude's hand, the same session. The user's words were relayed from the orchestrating session "Pendências
estágios 7 e 8", where the user took the decisions after the orchestrator showed them the options and
recommendations of this stage's file. No AWS call, and no preparation beyond the record.*

- **[user] The words, verbatim**, relayed from the orchestrating session: *"Pode registrar como aceitas as
  recomendações de decisão em relação aos seguintes itens: # Stage 9 * #2 Limite de dados por query no
  athena. * #11 onde ficam os resultados de query em Staging e Produção * #12 a rede do job glue * #5 como
  um projeto do sandbox lê uma tabela governada no redshift * #6 Quem cria as tabelas do warehouse
  governado * #7 Os limites de custo do warehouse * #8 os logs de auditoria do warehouse"*
- **[Claude] What each acceptance takes**, recorded in the Decisions-due table:
  - 2: 10 GB per query.
  - 11: each data slice authors `awsds-<env>-derived`, `results/` at 30 days, and `awsds-<env>-athena`.
  - 12: option (a), the Glue connection and the job security group `[P]` in `*/sagemaker/`. The
    application slice references them through `*/sagemaker/`'s outputs (Stage 10 decision 20 (b)).
  - 5: the Lake Formation-managed datashare, after 9.5a's reading.
  - 6: the DDL and the load job in the repository, the deployer's database user the only creator.
  - 7: 10 RPU-hours and `auto_mv` off.
  - 8: 30 days and the account data CMK.
- **[Claude] Still open**: decisions 3 (whether Staging keeps a mirror) and 1 (the Production data key and
  what Staging reads of Production's outputs), which hold pass 2 onward.

## 2026-10-22 — decisions 3 and 1 taken by the user, as recommended

*Claude's hand, the same session. The user's words were relayed from the orchestrating session "Pendências
estágios 7 e 8", which reads them as the two decisions taken on 2026-10-22 as revised and recommended. No
AWS call; the saved plan of `staging/sagemaker/` was refreshed.*

- **[user] The words, verbatim**, relayed from the orchestrating session: *"Avise às sessões que irei
  acatar as recomendações em relação às decisões 3 e 1, conforme conversamos nesta sessão."*
- **[Claude] Decision 3**: no mirror. Staging reads the governed lake read-only through the LF-Tag share
  Sandbox holds, writes only to its own catalog, buckets and key, and creates the application's schemas
  from the repository at each deploy. **Decision 1**: a dedicated Production data key, and Staging reads
  nothing of Production's outputs, model archives included, so Stage 10 decision 6 holds as written. Every
  decision of the stage is now taken, and none holds a pass.
- **[Claude] The stage file brought to the two decisions**: the Status row and the Decisions-due table;
  the build table's `data-governance/data/` and `staging/data/` rows; the outputs paragraph, where
  `staging/data/` gives `production/data/`'s names; the diagram's Staging node; 1.4 and 2.1 (Staging joins
  `DATA_CONSUMERS`, the share map gains its `DESCRIBE` and `SELECT`); section 4's Action and Why; 4.1 as
  1.1-1.3's shape without the write; 4.4 withdrawn; 4.6 without the archive read; 8.5, the Deliverables,
  verification xiii, two risks, the cost table and decision 6's sentence on the schema's source.
- **[Claude] The code made true to them, behaviour unchanged**: `DATA_MIRRORS` is `READ_ONLY_TARGETS` in
  `backend.py`; `staging/sagemaker/`'s comments and role description name the lake read through Lake
  Formation, and its Sid `VendTheMirrorCredentials` is `VendTheLakeCredentials`. Re-plan as
  `awsds-infra-staging`: *"Plan: 8 to add, 0 to change, 0 to destroy."*, saved over the earlier plan.
  `deploytargets.py`'s `DT-4` cites D13 for Staging's role; `./aws/deploytargets.py` *"0 check(s)
  FAILED."*
- **[Claude] Owed before 4.5's apply**: `DT-8` still reads the superseded design, an isolation check that
  fails on a link to Data Governance and a table-by-table comparison with a mirror; it is rewritten with
  pass 5's preparation to read that every Staging grant on the lake is `DESCRIBE` or `SELECT`. Passes 2,
  3 and 5 can now be prepared: no decision blocks them.

## 2026-10-22 — 4.4 aligned with Stage 8 3.3

*Claude's hand, the same session, on the orchestrating session's message that it applied decisions 3
and 1 to the shared files in PR #244. No AWS call.*

- **[Claude] What the message asked was already on this branch**: decisions 2, 5, 6, 7, 8, 11 and 12
  (commit `f96db8bf`) and 3 and 1 (`29302c94`) recorded, and 4.1, 4.4 and 4.6 rewritten to them.
- **[Claude] 4.4 names where the application's tables come from**, the shape Stage 8 3.3 now assumes: in
  the Staging leg the deploy creates them from the repository's schemas, after Stage 8's 3.2 and before
  its 3.3, in 4.1's local database, and the tests read them beside the governed tables through the share.

## 2026-10-22 — Stage 10's definitions home renamed to `applications/`

*Claude's hand, the same session, on a message from the session "Stage 10 — revisão e preparação". No AWS
call.*

- **[Claude] 1.1's pointer to Stage 10's statements** names `applications/*` where it named `workflows/*`:
  the user took Stage 10 decision 1, revised, on 2026-10-22, and the definitions home's prefix moved with
  it. Each leg extracts the release bundle's tree there (`workflows/<name>.yaml`, `code/`, `src/`,
  `glue/`); the deny's two exemptions and the principal branch's pair are unchanged, and Stage 10's file
  carries the list as of its commit `f2bd47a7` on PR #246.

## 2026-10-22 — passes 2, 3 and 5 and decision 12 (a) prepared, `DT-8` rewritten

*Claude's hand, the same session, on the user's words relayed from the orchestrating session. Every AWS
call is a read, as the infrastructure user (`InfrastructureAccess`) through `awsds-infra-data`,
`awsds-infra-prod`, `awsds-infra-staging` and `awsds-infra-identity`, with the tunnel down; the plans ran
on Terraform 1.15.8 and were saved under `$HOME/tmp/stage-09/`. Nothing was applied.*

- **[user] The words, verbatim**, relayed from the orchestrating session's chat: *"Peça à sessão do Stage 9
  para preparar os passes 2, 3 e 5 e reescrever o DT-8, sem aplicar nada."*
- **[Claude] `backend.py`.** `DATA_CONSUMERS` holds Sandbox, Staging and Production; `DATA_CONSUMER_VPC_SLICE`
  sends the lake's read of Production's gateway endpoint to `production/workloads/` (1.4), and the
  generated `consumers` map carries it as `vpc_slice`; a deployment target's `data/` slice receives its
  account folder, VPC slice and deploy role's name; the two `sagemaker/` slices their zone ids and, in
  Staging, the account folder. `layers.py` gains `production/data/` and `staging/data/` (`[P]`).
- **[Claude] Pass 2, `data-governance/data/`.** An aliased provider and identity read for Staging; the
  consumers' endpoint read from each one's VPC slice; the read shares (`share_databases`, `share_tables`)
  for Staging and Production beside Sandbox's; `production_write_database` and `production_write_tables`,
  named on `curated` with the grant option; the table `curated.trades` (Iceberg, the columns of
  `app-etl`'s input: `trade_date`, `desk`, `instrument`, `quantity`, `price`) and its
  `classification=internal`, the Governance Manager's to approve; the output `producer_table_name`.
  `DL-5`'s bracket: `get-data-lake-settings` at 18:44:47Z read `CROSS_ACCOUNT_VERSION` `4` and
  `SET_CONTEXT` `TRUE`, and the plan touches no settings. Plan: *"Plan: 8 to add, 5 to change, 0 to
  destroy."*; each of the five lake bucket policies gains two `aws:SourceVpce` ids, the Production one
  read from `production/workloads/terraform.tfstate`.
- **[Claude] Pass 3, `production/data/`.** The `consumer-data-v0.6.0` call with fourteen added key
  statements (the job role, the persona, the debug role, the release roles and their workflows, the chain
  role, the workflow roles, the jobs' volume grants, CloudWatch Logs for the job and workflow groups,
  Redshift Serverless); `awsds-prod-outputs` with eight statements (the network deny with its named
  exemptions, the persona's and debug role's reads, the release role's prefixes `applications/` and
  `inbox/`, Stage 10 decision 12's deny on `applications/*` exempting the deploy role and
  `InfrastructureAccess`) and its EventBridge notification; `awsds-prod-derived` at 30 days;
  `awsds-prod-athena`, enforced, 10 GB per query; `app_outputs` and its grants; 2.3's regrants to the job
  role, the read by expression and the write on `curated` by name. Plan: *"Plan: 35 to add, 0 to change, 0
  to destroy."*; Recipe D's first step, `-target` on the settings: *"Plan: 1 to add, 0 to change, 0 to
  destroy."*, `CROSS_ACCOUNT_VERSION` `4`, `SET_CONTEXT` `TRUE`, the create-time defaults known after
  apply.
- **[Claude] Pass 5, `staging/data/`.** The same shape without the write, the debug role and the Redshift
  statement; the persona held to reads on the whole bucket. Plan: *"Plan: 34 to add, 0 to change, 0 to
  destroy."*; the first step *"Plan: 1 to add"*. The module writes `CROSS_ACCOUNT_VERSION` 4 where Staging
  read 1.
- **[Claude] Decision 12 (a).** `network.tf` in both `sagemaker/` slices: `awsds-<env>-jobs`, a
  self-referencing rule for every TCP port in and out, TCP/443 to the endpoints' group and to the S3
  prefix list, and the `NETWORK` Glue connection on the first zone's private subnet; outputs
  `job_security_group_id` and `glue_connection_name`. EC2 refuses an apostrophe in a description, which
  `check-sg-descriptions.py` caught before a plan. Plans: `production/sagemaker/` *"Plan: 6 to add, 1 to
  change, 0 to destroy."* (the change is `glue:GetConnection`), `staging/sagemaker/` *"Plan: 14 to add, 0
  to change, 0 to destroy."*. `lakeformation` joins both egress slices: *"Plan: 16 to add"* each.
- **[Claude] `DT-8` rewritten.** It reads every grant of the lake to Staging's account (fail on anything
  beyond `DESCRIBE` and `SELECT`), Staging's resource links into Data Governance (a failure once
  `staging/data/` stands without them) and Staging's local tables against the lake's names (a failure on
  a copy). Live, the five infrastructure profiles: *"0 check(s) FAILED."*, `DT-8` two notes (no grant, no
  link yet) and one pass. Against a stand-in `aws`: a planted `INSERT`, a missing link with the Staging key
  present and a local `app_outputs.trades` each fail by name; a world with `DESCRIBE`/`SELECT` grants,
  both links and no copy reads three passes.
- **[Claude] What the plans do not stop on, and what they wait for.** No plan reads an object another
  stage creates: the policies name Stage 10's roles by `aws:PrincipalArn`. The applies have an order:
  pass 2 before `production/data/` and `staging/data/` (the regrants need the share);
  `staging/sagemaker/` before `staging/data/` (Lake Formation refuses a grant to a role that does not
  exist); Recipe D's two steps in each data slice. Once merged, `data-governance/data/`'s change sits on
  `main` unapplied, and any later apply of that slice carries it (Lesson 69).
- **[Claude] Documents.** `docs/NETWORK.md` §2.1 and §9 name the jobs' groups and §10 the seven
  endpoints; the producer README gains the write grants, the trusted endpoints' sources and `curated.trades`;
  `production/data/` and `staging/data/` carry READMEs indexing every added `Sid` and grant; conventions §6,
  `docs/PRICING.md` §3, `docs/plan/cost-model.md` and `aws/INDEX.md` follow. `check-network-doc.py`,
  `check-sg-descriptions.py`, `check-plan-refs.py`, `check-index.py` and `slices.py check` (41 slices) are
  clean.

## 2026-10-22 — 4.4 carries Stage 10 decision 20 (d)'s exception

*Claude's hand, the same session, on the orchestrating session's message that the user took Stage 10
decision 20 (d) in its chat. No AWS call.*

- **[Claude] 4.4** keeps Staging free of any seeded stand-in for governed data, with one exception named:
  the release job seeds `inbox/app-etl/` of the account's outputs bucket from the bundle's `samples/`, in
  Staging and Production alike, because `app-etl` is a template with no producer and the samples are its
  own test input; a real application names its governed source in its release. `production/data/` and
  `staging/data/` already admit the release role to `inbox/`, and Stage 10 decision 2, taken the same day,
  confirms the workflow statements their data keys carry.

## 2026-10-22 — the deployment manager's run read on both data keys; Stage 8's halves in PR #244

*Claude's hand, the same session, on messages from the sessions "Stage 10 — revisão e preparação" and
"Pendências estágios 7 e 8". No AWS call beyond the re-plans; nothing applied.*

- **[Claude] `AllowTheDeploymentManagerToReadWorkflowRuns`** joins the data keys of `production/data/` and
  `staging/data/`: the user took Stage 10 decision 11 that day, so `DeploymentManagerAccess` reads
  workflow runs, and under decision 2 the service decrypts a run in the reader's session at each
  `GetWorkflowRun`. `kms:Decrypt`, the reserved role matched by pattern, and the encryption context
  `aws:airflow-serverless:workflow-arn` matched to `awsds-<env>-wf-*`, narrower than the context's
  presence the request named. No S3 object carries that context, so the approver still decrypts no
  output (D31). Re-plans: *"Plan: 35 to add, 0 to change, 0 to destroy."* and *"Plan: 34 to add, 0 to
  change, 0 to destroy."*, the full plans saved again; Recipe D's first-step plans are unchanged, since the
  settings carry no key statement.
- **[Claude] Stage 8's halves, in PR #244 and unapplied**: `awsds-<env>-app-boundary` in both
  `foundation/` slices (4.0 now says so), `PassTheJobRole` on both deploy roles, and on
  `awsds-deploy-staging` `ReadTheApprovedModelVersions` and `ListTheModelVersions`, the two actions
  `production/sagemaker/`'s group policy grants that role.

## 2026-10-22 — passes 2, 3 and 5, decision 12 (a) and `production/workloads/` applied

*Claude's hand, the same session, as the infrastructure user, on the user's "Autorizado" in this
session's chat: the applies in the report's order, `curated.trades`' classification with pass 2. The
session told "Pendências estágios 7 e 8", "Stage 10 — revisão e preparação" and "Chat lateral" before
the first write, and started after the orchestrating session reported its `foundation/` and
`identity/sso/` applies done. Every plan was made afresh with `-input=false`, and its changes in
`terraform show -json` compared with the reviewed plan's: identical each time.*

- **[Claude] Pass 2, `data-governance/data/`** (Data Governance, `InfrastructureAccess`,
  `awsds-infra-data`), 19:35:58-19:36:25Z: *"Apply complete! Resources: 8 added, 5 changed, 0
  destroyed."*, re-planned `No changes`. `DL-5` read `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE` before
  (19:35:09Z) and after (19:39:12Z), and `DL-7` 9 shares out where it read 3, no invitation pending.
  `DT-6` passes (an `INSERT` grant names Production's account) and `DT-8` reads 2 grants to Staging,
  `DESCRIBE` and `SELECT` alone (19:45:20Z); `DT-5` read Production's two default lists holding one
  `IAMAllowedPrincipals` entry each.
- **[Claude] `production/workloads/` and `production/sagemaker/`** (Production, `awsds-infra-prod`) and
  **`staging/sagemaker/`** (Staging, `awsds-infra-staging`): 19:46:42-19:47:00Z, 1 changed, the S3 gateway
  endpoint's policy on `vpc-v0.4.0`; 19:47:00-19:47:22Z, 6 added and 1 changed, decision 12 (a)'s group,
  rules and Glue connection and `ReadTheJobsConnection`; 19:47:23-19:47:54Z, 14 added. Each re-planned
  `No changes`.
- **[Claude] `production/data/` by Recipe D**: the settings alone, 19:51:00-19:52:37Z, 1 added;
  `get-data-lake-settings` read the `InfrastructureAccess` seat alone, both default lists `[]`,
  `CROSS_ACCOUNT_VERSION=4` and `SET_CONTEXT=TRUE`, so nothing was revoked, and `DT-5` read the lists
  emptied (19:54:38Z). Then the rest, 19:55:07-19:56:36Z, *"Apply complete! Resources: 34 added, 0 changed,
  0 destroyed."*, re-planned `No changes`.
- **[Claude] `staging/data/` by Recipe D**: the settings alone, 19:57:27-19:57:36Z, 1 added, read back
  with the `InfrastructureAccess` seat alone, both lists `[]`, `SET_CONTEXT=TRUE` and
  `CROSS_ACCOUNT_VERSION` 4 where it read 1. Then the rest, 19:58:08-19:59:30Z, *"Apply complete!
  Resources: 33 added, 0 changed, 0 destroyed."*, re-planned `No changes`.

## 2026-10-22 — the readings after the applies

*Claude's hand, the same session, read-only. Both instruments exit 1 for the persona profiles that were
not signed in (their "Calls that failed" section), with 0 checks failed.*

- **[Claude] `./aws/deploytargets.py`**, 20:01:24Z: 0 failed, one note, `DT-10`'s `DataScientistProdAccess`
  allows, owed by 5.1. `DT-1` reads `awsds-prod-outputs` under `aws:kms` with its vpce, via and principal
  branches and `awsds-prod-derived` expiring at 30 days; `DT-2` the workgroup enforced, its results in
  `awsds-prod-derived`, cutoff 10737418240, `SSE_KMS`; `DT-4` both job roles' trust and D13; `DT-5` every
  account's parameters and both consumers' lists emptied; `DT-8` the share, the links `curated` and `raw`
  resolving into Data Governance, and no copy; `DT-12` six job log groups at 30 days in each account.
- **[Claude] `./aws/datalake.py`**, 20:03:39Z: 0 failed, `DL-5` 4 / TRUE, `DL-7` 9 shares out.
- **[Claude] Verification xiv**: no grant names `IAM_ALLOWED_PRINCIPALS` in Production (21 grants: 9 to
  `awsds-prod-job-exec`, 7 to `DataScientistProdAccess`, 3 to `InfrastructureAccess`, 2 to
  `awsds-deploy-prod`) or in Staging (22). Production's RAM holds four `LakeFormation-V4-*` shares and
  Staging's two, each `ACTIVE`, with no invitation pending; through the links, `curated` lists
  `sample_trades` and `trades` in both accounts and `raw` lists none.
- **[Claude] The jobs' network**: `awsds-prod-jobs` and `awsds-staging-jobs` each read ingress TCP
  0-65535 from itself, and egress TCP 0-65535 to itself, 443 to the endpoints group and 443 to the S3
  prefix list. The Glue connections of the same names are `NETWORK`, on that group, in `us-west-2b`.
  `./aws/egress.py`'s `EG-4` matches `mwaa-code` on VPC-Workloads' gateway endpoint and on neither of
  Production's other two, 0 failed.
- **[Claude] Stage 8's ceilings**: `awsds-prod-app-boundary` and `awsds-staging-app-boundary` read at
  `v1`, created 19:27:16Z and 19:27:35Z, attached to nothing.
- **[Claude] The branch on `main`**: the user asked to rebase on `main`; the branch is pushed, so the
  app's sync merged `origin/main` (PR #246) per `CLAUDE.md`'s rule, one conflict in `docs/NETWORK.md` §9
  where both stages added a row, both kept. The six applied slices re-planned on the merged code read
  `No changes`.

## 2026-10-22 — the job log groups under the data key, written and planned

*Claude's hand, the same session, on the user's "Sim, prepare a migração dos seis grupos de log dos jobs
para a chave de dados em production/sagemaker e staging/sagemaker, só até o plano, sem aplicar." AWS
reads only; nothing applied.*

- **[Claude] The association**: each `*/sagemaker/` slice reads the account data key's ARN from
  `*/data/`'s state, with a null default so a first build still applies the job role before `data/`
  (whose Lake Formation grants name it), and sets `kms_key_id` on its six job log groups. CloudWatch Logs
  uses the key as its own principal under the data key's `AllowCloudWatchLogsForTheJobAndWorkflowGroups`;
  no role holds a grant on it. The `CKV_AWS_158` skips are gone.
- **[Claude] The policies name the groups by ARNs built from their names**: a first plan listed the job
  role's and the debug role's inline policies as updates, their documents read only at the apply because
  they referenced the group resources. With the ARNs built from `local.job_log_groups` the documents are
  identical and plan as no change.
- **[Claude] Plans** as `awsds-infra-prod` and `awsds-infra-staging`, each *"Plan: 0 to add, 6 to change,
  0 to destroy."*, `kms_key_id` the only attribute that moves, no data source deferred to the apply; saved
  as `production-sagemaker-logkey.tfplan` and `staging-sagemaker-logkey.tfplan` outside the repository.
- **[Claude] `DT-12`** reads each group's key: live, a note in both accounts (all twelve groups under the
  AWS-owned key), 0 failed. Against a stand-in `aws`: all six under the data key passes, three of six
  fails as a partial apply, another key fails, none is the note.
- **[Claude] Lesson 69**: once PR #245 merges, both `sagemaker/` slices carry this change on `main`
  unapplied, and any later plan of either shows the six associations.

## 2026-10-22 — the job log groups under the data key, applied

*Claude's hand, the same session, as the infrastructure user, on the user's "Sim, aplique a associação
dos grupos de log à chave de dados em production/sagemaker (awsds-infra-prod) e staging/sagemaker
(awsds-infra-staging), a partir de planos novos." The session told "Pendências estágios 7 e 8" and
"Chat lateral" before the write.*

- **[Claude] Fresh plans**, each *"Plan: 0 to add, 6 to change, 0 to destroy."*, their changes in
  `terraform show -json` identical to the reviewed plans', no data source deferred to the apply.
- **[Claude] `production/sagemaker/`** (Production, `awsds-infra-prod`), 20:51:10-20:51:22Z, and
  **`staging/sagemaker/`** (Staging, `awsds-infra-staging`), 21:00:02-21:00:15Z: *"Apply complete!
  Resources: 0 added, 6 changed, 0 destroyed."* each. Staging re-planned `No changes`. Production's first
  re-plan failed on the laptop's DNS (`lookup ec2.us-west-2.amazonaws.com: no such host`; the
  orchestrating session reported the same drop interrupting its `identity/sso/` apply), and the second, at
  21:00:44Z, read `No changes`.
- **[Claude] `DT-12`**, 21:03:22Z: *"6 under the account data key"* in both accounts, 0 failed; the
  CLI reads each of the twelve groups' `kmsKeyId` as its account's data key. Its branch for the AWS-owned
  key turned from a note into a fail, exercised against the stand-in.
- **[Claude] Owed**: the first job in each account shows whether its logs land and whether the debug role
  reads them, neither role holding a grant on the key.

## 2026-10-22 — the documents brought to the applied state

*Claude's hand, the same session, in commit `d3610844` with the applies of passes 2, 3 and 5. No AWS call
beyond the readings recorded above.*

- **[Claude] The stage file**: the Status, steps 1, 1.5, 2.1-2.3, 3.1's `glue:GetConnection` note, 4.0's
  ceiling, 4.1, 4.3, 4.5, 7.2 and verification xiv carry the applies and their readings where they said
  planned and unapplied.
- **[Claude] The indexes**: the rows of `production/data/`'s, `staging/data/`'s and the producer's READMEs
  read applied; `consumer-data`'s README names its three callers; conventions §6 counts seven endpoints in
  both egress slices, `lakeformation` among them; `docs/NETWORK.md` marks the jobs' groups and
  VPC-Workloads' `vpc-v0.4.0` applied.
- **[Claude] `docs/PRICING.md`**: the KMS row counts 17 keys with the two deploy targets' data keys, and
  the monthly floor rises by 2 USD in both Regions (`sa-east-1` ~USD 32-45, central ~38; `us-west-2`
  ~USD 27-36, central ~32), in §2 and in the regional comparison.

## 2026-10-22 — the third sitting with the environment down: 5.1 as a managed policy, the warehouse pair written, 2.4 has no job

*Claude's hand, in the session `stages-8-9-10-review`, on the user's request quoted in Stage 8's entry of
the same sitting. AWS read as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`,
`awsds-infra-staging`, `awsds-infra-data`, `awsds-infra-identity`, `awsds-infra-sandbox-1`), reads and
plans only, the tunnel down (`NO_PROXY='*'`); the plans saved outside the repository. Nothing applied.
Times UTC.*

- **[Claude] The instruments, between 22:00 and 22:10**: `./aws/deploytargets.py` 0 FAILED, `DT-10` a
  note (`DataScientistProdAccess`: the three markers `no`, owed by 5.1); `./aws/datalake.py` 0 FAILED,
  `DL-5` 4 / TRUE.
- **[Claude] 5.1, first as inline statements**: the six allows and the two Redshift denies, with the
  ARNs read from `production/data/` and `production/sagemaker/`'s states through a `deployment_target`
  map. The plan as `awsds-infra-identity` at 22:14:09 failed the slice's own precondition:
  *"Inline policy for DataScientistProdAccess is 10550 characters, over the 10240 the plan allows. See
  step 5.2: the way out is a customer-managed policy, not a larger threshold."* The set read 7,098
  before. The set also lacked `lakeformation:GetDataAccess` (read in the document), without which 2.3's
  regrants reach nothing.
- **[Claude] 5.1 as written**: `production/data/persona.tf`, the `aws_iam_policy`
  `awsds-prod-data-scientist` (`backend.py`'s `PERSONA_PRODUCTION_POLICY_NAME`, generated into both
  slices) with seven statements on the slice's own objects: the six Athena query and history actions on
  `awsds-prod-athena`, `GetObject` and `GetObjectVersion` under `PERSONA_READ_PREFIXES`
  (`app-etl/outbox/`, one list in `backend.py`, generated into `production/data/` for the bucket policy
  and the policy alike), `ListBucket` held to those prefixes, the results' read and write under
  `results/` of `awsds-prod-derived`, `Decrypt` and `GenerateDataKey` on the data key through S3, and
  `sts:AssumeRole` on `awsds-prod-debug`; `identity/sso/` attaches it to `data_scientist_prod` by name,
  keeps `ReadThroughLakeFormation` inline, and composes the two Redshift denies from the new fragment
  `redshift_denies`, which both data-science sets read. `production/data/`'s key policy admits
  `/aws/redshift/*` for 9.1's audit groups. Plans: `production/data/` as `awsds-infra-prod` at 22:22:18
  *"Plan: 1 to add, 1 to change, 0 to destroy."* (the policy; the key policy's CloudWatch statement);
  `identity/sso/` as `awsds-infra-identity` at 22:22:31 *"Plan: 1 to add, 1 to change, 0 to destroy."*
  (the attachment; `DataScientistProdAccess` 7,098 to 8,438), `DataScientistAccess` unchanged.
- **[Claude] `DT-10` amended**: it reads the set's customer-managed policy references and, when
  `awsds-prod-data-scientist` is among them, the policy's default version in Production, and searches
  the markers in both documents; live at 22:28: a note, the markers `no` and the policy `not attached`,
  0 failed.
- **[Claude] 9.1, written by a fork of this session**: `terraform-live/production/warehouse/` and
  `production/warehouse-compute/` from the Sandbox slices with the step's differences; the four states'
  outputs read at 22:08:20; the namespace planned as `awsds-infra-prod` at 22:13:52 to 22:14:12,
  *"Plan: 9 to add, 0 to change, 0 to destroy."* (three log groups, two alarms, the role, the namespace,
  the security group, the ingress rule); the compute's plan at 22:14:16 to 22:14:26 *"Error: Unable to
  find remote state … No stored state was found"* for `production/warehouse/`, the expected reading;
  `awsds-prod-tfstate` holds no object under `production/warehouse` (22:14:51). `layers.py` gains the
  two rows and refusal 9, `HELD_FROM_UP`, keyed `("production", "warehouse-compute")`: `make up
  ENV=production DRY=1` prints the refusal and raises nothing of it. `docs/NETWORK.md` gains the pair's
  rows in §2, §2.1 and §9; `check-network-doc.py` clean.
- **[Claude] 2.4 read against the code**: no job writes `curated.trades`. The pipeline's Glue job runs
  `glue/transform.py` (inbox to one CSV), and the template carries no schema, so 2.4 to 2.6 have no job
  to run; the step now specifies the proof job (`awsds-prod-producer-proof`, `[P]` in
  `production/sagemaker/`, its scripts under `applications/stage-09-proofs/v0/glue/`), unwritten.
- **[Claude] The plan**: the Status row, the build table, 2.4, 4.6, 5.1, 5.3 and 9.1.

## 2026-10-22 — 5.1 applied: the persona's managed policy in Production, its attachment in Identity

*Claude's hand, the same session, as the infrastructure user (`awsds-infra-prod`, `awsds-infra-identity`,
each `InfrastructureAccess`), on the user's authorization in this chat. Every plan was made afresh and
applied only after its summary line read what the reviewed plan had read. Times UTC.*

- **[user] The authorization**: *"Autorizo aplicar production/data como awsds-infra-prod e depois
  identity/sso como awsds-infra-identity, cada um a partir de um plano novo, avisando as outras sessões
  antes."*
- **[Claude] Before**: the app's session list read at 22:49, no session running, so none to warn; both
  profiles answered `get-caller-identity`; the worktree clean at `c9800c78`.
- **[Claude] `production/data/`** (Production, `awsds-infra-prod`): the fresh plan at 22:50:22 to 22:50:56
  read *"Plan: 1 to add, 1 to change, 0 to destroy."* (`aws_iam_policy.persona`; the data key's policy);
  the apply, 22:50:56 to 22:51:16, *"Apply complete! Resources: 1 added, 1 changed, 0 destroyed."*, the
  key modified in 8 s and the policy created in 1 s; the re-plan at 22:52:31 *"No changes."*
- **[Claude] `identity/sso/`** (Identity, `awsds-infra-identity`): the fresh plan at 22:51:39 to 22:51:53
  read *"Plan: 1 to add, 1 to change, 0 to destroy."* with `data_scientist_prod` 7098 → 8438; the apply,
  22:51:53 to 22:52:13, *"Apply complete! Resources: 1 added, 1 changed, 0 destroyed."*, the attachment
  created in 7 s and the inline policy modified in 9 s, `inline_policy_bytes` reading 8438 for the set;
  the re-plan at 22:53:50 *"No changes."*
- **[Claude] Read back**, 22:54 to 22:56: `awsds-prod-data-scientist` at `v1`, created 22:51:13, attachment
  count 1, its seven `Sid`s the ones `persona.tf` writes; the set's customer-managed policy references name
  it at path `/`, provisioned in one account; Production's `AWSReservedSSO_DataScientistProdAccess_*` role
  carries `CloudWatchLogsReadOnlyAccess` and `awsds-prod-data-scientist` attached, and its inline policy
  `DenyMintingARedshiftDatabaseSession`, `DenyRedshiftCostGuardAndCompute` and `ReadThroughLakeFormation`;
  the data key's `AllowCloudWatchLogsForTheJobAndWorkflowGroups` lists `/aws/redshift/*` between
  `/aws-glue/*` and `/awsds/prod/wf/*`. `./aws/deploytargets.py` on the five infrastructure profiles at
  22:55:43: *"0 check(s) FAILED."*, `DT-10` passing for `DataScientistProdAccess` (the three markers `yes`,
  the policy `attached`) and for `DataScientistStagingAccess`.
- **[Claude] The records**: the stage file (the Status, 5.1, 5.3), both slices' READMEs, the waiting
  list, `CLAUDE.md`, the plan core and both indexes; `docs/AWS_STATE.md`'s row on `deploytargets.py`,
  which still described the seven fails of 2026-10-18, brought to the 0-failed reading with `DT-10`
  passing.
- **[Claude] What follows**: 5.4 and 8.1 to 8.4 are the user's, in the data-science persona's sessions;
  6.3 may run now, the persona holding the debug role's assumption.

## 2026-10-22 — 6.3: the deployment manager's approval of a debugging window, and the apply planned

*Claude's hand, the same session. The approval is the user's, in this chat; the plan a read as the
infrastructure user (`awsds-infra-prod`); nothing applied in this entry. Times UTC.*

- **[user] The approval**, as the deployment manager, 23:0x: *"Sim: registre minha aprovação como
  deployment manager, planeje o apply da variável debug_window_end em production/sagemaker e me diga
  o que eu faço na sessão da persona."* It answers this session's question of the same minute,
  *"Quer abrir agora a janela do escape hatch (6.3), com sua aprovação escrita e o apply da
  variável?"*. The window proposed: until 2026-10-23T01:00:00Z, about two hours from the approval, long
  enough for the persona's sign-in, one assumption inside it and the refused one after it.
- **[Claude] The plan**, `production/sagemaker/` as `awsds-infra-prod` with `-var
  debug_window_end=2026-10-23T01:00:00Z`, 23:07:28 to 23:07:44: *"Plan: 0 to add, 1 to change, 0 to
  destroy."*, the debug role's trust alone (`DateLessThan` moving from the default to the window), and
  the slice's own check printing *"The debug window on awsds-prod-debug is open until
  2026-10-23T01:00:00Z: close it in the same sitting with an apply without -var debug_window_end"*, the
  reminder 6.3 relies on. The apply waits on the user's word; the persona's sequence is the step's.

## 2026-10-22 — 6.3: the window opened

*Claude's hand, the same session, as the infrastructure user (`awsds-infra-prod`), on the user's
authorization in this chat: "Autorizo o apply de production/sagemaker como awsds-infra-prod a partir do
plano salvo, abrindo a janela do awsds-prod-debug até 2026-10-23T01:00:00Z." Times UTC.*

- **[Claude] Before**: the app's session list read at 23:09, no session running.
- **[Claude] The apply**, from the plan saved at 23:07 (`production/sagemaker/`, Production): 23:09:43 to
  23:09:55, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*, the role modified in 1 s,
  the check warning *"The debug window on awsds-prod-debug is open until 2026-10-23T01:00:00Z"* printed
  with it.
- **[Claude] Read back**: `get-role` at 23:10:19 shows the trust's `DateLessThan aws:CurrentTime
  2026-10-23T01:00:00Z` beside `aws:RequestedRegion us-west-2`, the session ceiling 3600 s;
  `./aws/deploytargets.py awsds-infra-prod` at 23:10:50 *"0 check(s) FAILED."*, `DT-9` a note, *"OPEN
  until 2026-10-23T01:00:00Z - close it in the same sitting (6.3)"*, both assumption rules
  `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`; the re-plan with the flag at 23:11:04 *"No changes."*
  with the same warning.
- **[Claude] What follows**: the persona's sequence (6.3), the user's; then the refused assumption after
  01:00Z read in the trail, and the closing apply without the flag.

## 2026-10-22 — 6.3: the persona's assumption inside the window, the alarm heard on the receiving side

*The user's hand for the persona's commands, pasted into this chat and copied here with the account id
and the sign-in address replaced by placeholders; Claude's hand for the readings, as the infrastructure
user (`awsds-infra-prod`), after the user signed in again as that user (the persona's login had emptied
the `awsds` token: *"Token for awsds does not exist"* at 23:22). Times UTC.*

- **[user] A first attempt with the placeholder left in the ARN**, three calls refused the same way:
  *"An error occurred (AccessDenied) when calling the AssumeRole operation: User:
  arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the
  data-science user> is not authorized to perform: sts:AssumeRole on resource:
  arn:aws:iam::<Production>:role/awsds-prod-debug"*, the resource string carrying the literal
  `<Production>` of the step's text. The trail records them in Production as `AccessDenied` on
  `AssumeRole` with `requestParameters` null (4 events, 23:18:16, 23:18:27, 23:18:36, 23:20:51), the shape Stage 8 4.6 read
  for a refused assumption. The step's command now reads the account id from the persona's own profile.
- **[user] The assumption inside the window**, the step's command with the real ARN:
  *"arn:aws:sts::<Production>:assumed-role/awsds-prod-debug/debug-window-proof"*.
- **[user] The reads through the assuming profile**: `aws s3 ls s3://awsds-prod-outputs/` answered
  nothing and refused nothing (the bucket holds no object yet, so the listing is the reading and
  `GetObject` stays unexercised); `describe-log-groups` under `/aws/sagemaker/` listed
  `/aws/sagemaker/ProcessingJobs`, `/aws/sagemaker/TrainingJobs` and `/aws/sagemaker/TransformJobs`.
- **[Claude] The receiving side**, 23:25:44: the rule `awsds-prod-debug-assume` read `TriggeredRules` 2 in
  the 23:21 minute and `Invocations` 1 at 23:21 and 1 at 23:22; the topic `awsds-prod-alerts`
  `NumberOfMessagesPublished` 1 and 1 in the same minutes, its one subscription an e-mail, `confirmed`
  (23:26:17). The trail, read at 23:26: two `AssumeRole` events naming the role, both by the persona's
  reserved role in `us-west-2` with no error: 23:21:29 session `debug-window-proof` (event
  `14013946-3962-41c9-8391-7cc6cc1db228`) and 23:22:00 session `botocore-session-1792711318` (event
  `2acc588b-f660-4c47-9abc-ea3c7ff286e4`), the second the assuming profile's own call at the first read.
  So one proof assumption produced two alarms, the direct call's and the profile's, each a message.
- **[Claude] What follows**: the two negatives and, after 01:00Z, the refused assumption, then the closing
  apply.
- **[Claude] A correction to the entry above**: the trail holds four refused attempts with the
  placeholder, not three: 23:18:16, 23:18:27, 23:18:36 and 23:20:51, each `AccessDenied` with
  `requestParameters` null.

## 2026-10-22 — 6.3: the two negatives under the debug role, each refused one layer before the one the step named

*The user's hand, the commands run as the Data Scientist User through the assuming profile, pasted into
this chat and copied here with the account id replaced by its placeholder; Claude's reading of them.*

- **[user] The write**: *"upload failed: - to s3://awsds-prod-outputs/app-etl/outbox/probe.txt An error
  occurred (AccessDenied) when calling the PutObject operation: User:
  arn:aws:sts::<Production>:assumed-role/awsds-prod-debug/botocore-session-1792711318 is not authorized to
  perform: kms:GenerateDataKey on resource:
  arn:aws:kms:us-west-2:<Production>:key/0415a6f0-9b15-4049-841d-d51e7a65d09c because no resource-based
  policy allows the kms:GenerateDataKey action"*.
- **[user] The `CreateSpace`**: *"An error occurred (AccessDeniedException) when calling the CreateSpace
  operation: User: arn:aws:sts::<Production>:assumed-role/awsds-prod-debug/botocore-session-1792711318 is
  not authorized to perform: sagemaker:CreateSpace on resource:
  arn:aws:sagemaker:us-west-2:<Production>:space/d-0000000000000/awsds-canary-probe because no
  identity-based policy allows the sagemaker:CreateSpace action"*.
- **[Claude] The reading** (Lesson 20): both refused, neither by the policy the step named. The write
  met the data key before the bucket: the key policy's `AllowTheDebugRoleToDecryptViaS3` grants the role
  `Decrypt` alone, and a `PutObject` under SSE-KMS needs `GenerateDataKey`, so the key refused and the
  bucket's `DenyThePersonaAndTheDebugRoleAnyWrite` stays attached and unexercised for this principal. The
  `CreateSpace` met the role's own identity policy, `Describe*` and `List*`, an implicit deny; the
  `Workloads` document's `DenyInteractiveSageMakerSurface` names itself only to a principal whose
  identity policy allows the action, the battery's infrastructure user, so for the debug role the SCP
  stays attached and unexercised, as the inline policy's absence of the action already refuses it. The
  role is read-by-API by two layers in each direction, and one of each pair is proven. The step's
  expectation is corrected to the measured wording.

## 2026-10-22 — 6.3: the alarm's messages received, and a third assumption inside the window

*The user's hand for the messages and the command, pasted into this chat and copied here with the
account id, the sign-in address and the laptop's address replaced by placeholders; Claude's reading as
the infrastructure user (`awsds-infra-prod`). Times UTC.*

- **[user] The alerts**: *"Sim, recebi dois emails de alerta"*, one per assumption; the second's body,
  verbatim but for the placeholders, the input transformer's eight lines:
  *"awsds-prod-debug-assume: the production debug role was assumed." / "When: 2026-10-22T23:22:00Z" /
  "Role: arn:aws:iam::<Production>:role/awsds-prod-debug" / "Caller: AROAW6L3NRTR5S22T5TS5:<the
  data-science user>" / "Session name: botocore-session-1792711318" / "Source address: <the laptop>" /
  "CloudTrail event id: 2acc588b-f660-4c47-9abc-ea3c7ff286e4"*. No credential in it, as 6.2 wrote the
  transformer; the caller is the reserved role's unique id and the sign-in name.
- **[user] The after-window command, run before the window's end**: the step's `assume-role` with the
  session name `debug-window-after` answered
  *"arn:aws:sts::<Production>:assumed-role/awsds-prod-debug/debug-window-after"*, a third successful
  assumption, since the window is open until 01:00Z. The refusal is the next reading, after the window
  closes, by the clock or by the closing apply.

## 2026-10-22 — 6.3: the window closed by the apply, read back

*Claude's hand, as the infrastructure user (`awsds-infra-prod`), on the user's authorization in this
chat: "Autorizo o apply de production/sagemaker sem a flag, como awsds-infra-prod, a partir de um plano
novo, para fechar a janela agora; depois eu rodo o assume-role e colo a recusa." Times UTC.*

- **[Claude] Before**: no session running (the app's list at 23:34); the trail read at 23:34:29 holds
  three successful `AssumeRole` events on the role, all by the persona's reserved role in `us-west-2`:
  23:21:29 `debug-window-proof`, 23:22:00 `botocore-session-1792711318`, 23:32:07 `debug-window-after`
  (event `371cc413-9835-40b0-aec1-86ef80c0b962`).
- **[Claude] The closing apply** (`production/sagemaker/`, Production): the fresh plan without the flag,
  23:34:42 to 23:34:58, *"Plan: 0 to add, 1 to change, 0 to destroy."*, `aws:CurrentTime` moving from
  `2026-10-23T01:00:00Z` back to `2026-01-01T00:00:00Z`, no check warning; the apply, 23:34:58 to
  23:35:09, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*, the role modified in 1 s.
- **[Claude] Read back**: the re-plan at 23:35:36 *"No changes."* with no warning; `get-role` at 23:35:38
  shows `DateLessThan aws:CurrentTime 2026-01-01T00:00:00Z` beside `aws:RequestedRegion us-west-2`;
  `./aws/deploytargets.py awsds-infra-prod` at 23:36:06 *"0 check(s) FAILED."*, `DT-9` passing, *"window
  on awsds-prod-debug closed (ends 2026-01-01T00:00:00Z)"*, both rules
  `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`. The window was open 25 minutes, 23:09:55 to 23:35:09.
- **[Claude] What follows**: the persona's `assume-role` against the closed trust, the refusal pasted
  here and read in the trail by `errorCode`, which closes 6.3 and verification xi.

## 2026-10-23 — 6.3: the assumption refused against the closed trust

*The user's hand, the command run as the Data Scientist User after the closing apply of 2026-10-22
23:35 UTC and pasted into this chat on 2026-10-23, copied here with the account id and the sign-in
address replaced by placeholders; Claude's reading. The infrastructure user's token had expired by
the time of the reading (15:25 UTC), so the trail's `errorCode` for this attempt is owed to the next
sign-in.*

- **[user] The refusal**, the step's command with the session name `debug-window-closed`: *"An error
  occurred (AccessDenied) when calling the AssumeRole operation: User:
  arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the
  data-science user> is not authorized to perform: sts:AssumeRole on resource:
  arn:aws:iam::<Production>:role/awsds-prod-debug"*.
- **[Claude] The reading**: the same wording as the four refusals of the malformed ARN, now on the real
  ARN, from the trust's `DateLessThan` with the default in the past: STS names no condition in its
  message, so the trail's record is what attributes it, a refused `AssumeRole` with `requestParameters`
  null and `errorCode` `AccessDenied` by the persona's reserved role, the shape Stage 8 4.6 read. The
  escape hatch is closed at rest, open in an approved window alone, alarmed on each assumption, and
  cannot become a notebook: 6.3 is done, verification xi answered but for the OU wording, which the
  role's own policy pre-empts (Lesson 20).

## 2026-10-23 — 6.3: the refusal's record read in the trail

*Claude's hand, as the infrastructure user (`awsds-infra-prod`), after the user signed in again on
request. Read-only. Times UTC.*

- **[Claude] The trail**, every `AssumeRole` in Production from 2026-10-22 23:30 to 2026-10-23 15:28,
  paginated whole (471 events, none truncated), two by the persona's reserved role: the third assumption
  inside the window, 2026-10-22 23:32:07, session `debug-window-after`, no error; and the refusal,
  **2026-10-23 15:25:28, `errorCode` `AccessDenied`, `requestParameters` null**, `us-west-2`, event
  `47e12fbc-5061-4a34-bc1f-e73217fbf313`, its `errorMessage` the text the user pasted, both from the
  laptop's address. The refused call records no session name and no role ARN, the shape Stage 8 4.6
  read; the window had been closed for 15 h 50 min. 6.3 and verification xi are closed.

## 2026-10-23 — the fourth sitting with the environment down: 2.4's proof job, decision 13, pass 6's grants, the persona sequences

*Claude's hand, in the session `stages-8-9-10-prep-2` (the branch `claude/stages-8-9-10-prep-2`, cut from
`main` after PR #247's merge retired the previous branch), on the user's request: "Em relação aos
estágios 8, 9 e 10, peço fazer o seguinte: verifique o status atual de cada estágio. revise o plano
destes estágios considerando o andamento atual, o resultado com as leituras e preparações prévias
realizadas para execução destes estágios. Faça a preparação necessária para a execução destes
estágios com tudo o que pode ser feito sem que seja necessário subir o ambiente. Prepare tudo que for
necessário para executarmos de forma mais célere estas etapas uma vez que eu consiga subir o
ambiente. Usuário infra sso logado para as leituras." AWS read as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`,
`awsds-infra-data`, `awsds-infra-identity`), reads and plans only, the tunnel down (`NO_PROXY='*'`); the
plans saved outside the repository. Nothing applied. Times UTC.*

- **[Claude] The instruments**, 16:05 to 16:16 over every `awsds-*` profile, where the six persona
  profiles' identity calls failed with no session (not a check); again 16:19 to 16:23 on the five
  infrastructure profiles alone: `cicd.py`, `deploytargets.py`, `orchestration.py`, `datalake.py` and
  `egress.py` each *"all checks passed"*, `DT-10` passing on the managed policy, `DT-12` six groups at
  30 days in both accounts, `DL-5` `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE`, `OR-9` a note (nothing of
  the layer exists), the burn 0.000 USD/h in the five accounts, no interface endpoint and no NAT
  gateway; `warehouse.py` exit 0. `make check` OK at 16:17.
- **[Claude] 2.4 read against AWS's pages** ("Using AWS Glue with AWS Lake Formation for Full Table
  Access", "Application integration for full table access", both in `REFERENCES.md`): a Glue Spark job
  writes a Lake Formation table in the full-table-access mode alone, which asks first for
  `AllowFullTableExternalDataAccess`, says a write needs `ALL`, and ends an Iceberg commit in
  `glue:UpdateTable`. Read live at 16:00: the flag unset in Production and in the lake, both reading one
  administrator, `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`, `AllowExternalDataFiltering` false.
- **[Claude] 2.4 written**: `terraform-live/production/sagemaker/producer-proof.tf`, the `[P]` Glue 6.0 job
  `awsds-prod-producer-proof` on `awsds-prod-jobs` as the job role, its script
  `proofs/producer_proof.py` at `applications/stage-09-proofs/v0/glue/` of the outputs bucket, the Iceberg
  catalog `lake` over the lake account's catalog (its id read from the lake state's key ARN) with Lake
  Formation vending on, one run per `--MODE`: `producer` (the ten sample rows inserted, read back, the
  direct put attempted and the run failed if it lands) and `pickup` (every `.csv` under `incoming/`
  read as the role, curated, deleted and read gone; a run with nothing to pick fails). The job role
  gains `CommitTheIcebergWrites`, `glue:UpdateTable` on the lake's `curated` tables and this account's
  `app_outputs` tables. Plan as `awsds-infra-prod` at 16:23:43 to 16:24:07: *"Plan: 1 to add, 1 to
  change, 0 to destroy."*, the job and the role's inline policy. The script compiles and passes `ruff`;
  it has run nowhere (Lesson 54): the first run's readings are verification xxviii.
- **[Claude] Decision 13 opened** (the stage file): the flag, where and by which hand, (a) Production's by
  the console recommended, its cost in the threat model named, (b) and (c) weighed.
- **[Claude] Pass 6's owed code**: `production/foundation/deploy-anchors.tf`'s
  `apply_application_in_this_account` gains `RunTheGovernedWarehouseDdl` (9.4), planned as
  `awsds-infra-prod` with the alerts var-file at 16:24:29 to 16:24:55, *"Plan: 0 to add, 1 to change, 0
  to destroy."*, the inline `apply-application`; `production/workloads-egress/` gains
  `optional_service_groups` and its wiring, so `make up ENV=production GROUPS=redshift` raises the
  warehouse's endpoint (9.1), its plan unchanged at 16:24:07 to 16:24:29, *"Plan: 16 to add, 0 to
  change, 0 to destroy."*; `aws/warehouse.py` `WH-15` names each account's own `make down` (9.8);
  9.3's statements prepared in the step, the theme `trades` and 1 TB proposed; `docs/NETWORK.md`'s
  firewall paragraph carries the group.
- **[Claude] The quotas**, read in both accounts with `list-service-quotas` (16:10 to 16:45, the
  Staging read slow enough to move to the background): every training and transform code of the
  ceiling's types at 0 in Staging as in Production, `ml.t3.medium`, `ml.t3.large` and `ml.t3.xlarge`
  processing at 4, 4 and 2 in both; `list-requested-service-quota-change-history` empty in both, so no
  request was ever made in either account. The codes and the request commands are in 3.5.
- **[Claude] The persona sequences written**, each runnable with nothing up (D39): 3.4's laptop half,
  5.4, 8.1's laptop half, 8.2, 8.3, 8.4 (no laptop profile reaches `DataScientistStagingAccess`; the
  block to add is in the step) and 2.5's drop, 2.6's read-back; Stage 10 6.2's in its file.
- **[Claude] The sittings in order**: [`runbooks/promotion.md`](../plan/runbooks/promotion.md), §0 to §R,
  one section per sitting, the command and the reading of each step; `waiting-on-the-user.md`'s
  Production and GitLab rows, its decision and act rows, and the three stage files point at it.
- **[Claude] The plan**: the Status row, the build table, 2.4, 2.5, 2.6, 3.1, 3.4, 3.5, 5.4, 8.1-8.4,
  9.1, 9.3, 9.4, 9.8, decision 13 and verification xxviii.

## 2026-10-23 — decision 13 taken by the user, as recommended: (a)

*Claude's hand, the same session; no AWS call.*

- **[user]** Asked for the decision's context, its options and the recommendation, read them, and took
  it: *"Ok com a recomendação (a)."* `AllowFullTableExternalDataAccess` goes on in Production by the
  console's Application integration settings, the user's act as the infrastructure user, between two
  `DT-5` readings of Claude's, with nothing up; the lake's half waits for the proof job's first wording.
- **[Claude]** The decision recorded in the stage file (decision 13, the Status row), the act in
  `waiting-on-the-user.md`'s acts and in `runbooks/promotion.md` §0.3 with its three steps, the indexes
  and `CLAUDE.md` following. Stage 11's threat-model row and `AWS_STATE.md`'s word on the flag are
  written when the flag reads on.

## 2026-10-23 — decision 13's act: the full-table-access flag turned on in Production, read before and after

*Claude's hand, the same session; the readings as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`, `awsds-infra-data`, `awsds-infra-staging`, `awsds-infra-sandbox-1`), reads only;
the write the user's, in the console. Times UTC.*

- **[Claude] The before-reading**, 19:29:52, `get-data-lake-settings` in Production: one administrator,
  `InfrastructureAccess`; `ReadOnlyAdmins` empty; both create-default lists empty;
  `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`; `AllowExternalDataFiltering` false;
  `AllowFullTableExternalDataAccess` absent; the allow list empty; `AuthorizedSessionTagValueList`
  absent. `DT-5` passing (parameters and create-defaults).
- **[user]** The console refused the settings page first, pasted (the account ids and the address
  masked): *"Unable to load settings. User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_InfrastructureAccess_c2bcabf74c885115/<the infrastructure user> is not authorized to perform: lakeformation:GetDataLakeSettings on resource: arn:aws:lakeformation:us-east-2:<Production>:catalog:<Production> with an explicit deny in a service control policy: arn:aws:organizations::<Management>:policy/<organization>/service_control_policy/p-i0ney7mx"*.
- **[Claude]** `p-i0ney7mx` read as `awsds-infra-identity`: `aws-guardrails-nYsweH`, Control Tower's
  `CTMULTISERVICEPV1`, `StringNotEquals aws:RequestedRegion us-west-2`: the console had opened in Ohio,
  and the Region ceiling refused the page to the account's own Lake Formation administrator, the first
  console-side reading of that control in Production (INV-12's hand-probe was a CLI call in CloudShell).
- **[user]** The console switched to `us-west-2`; *Administration → Application integration settings →
  Allow external engines to access data in Amazon S3 locations with full table access* marked and saved:
  *"Pronto"*.
- **[Claude] The after-reading**, 19:49:19: `AllowFullTableExternalDataAccess` `true`; the administrator,
  both lists, the parameters, `AllowExternalDataFiltering` and the allow list as before;
  `AuthorizedSessionTagValueList` now an empty list, which the console wrote and the API had returned
  absent. `DT-5` passing at 19:49:30, 0 failed. The other accounts the same minute: the lake absent,
  Staging absent, Sandbox `true` with its three administrators.
- **[Claude]** `TM-26` written in the threat model's ledger, the flag per account in `AWS_STATE.md` §C,
  decision 13 and the Status row brought to the act, the act's rows out of `waiting-on-the-user.md`,
  `runbooks/promotion.md` §0.3 marked done with the Region note.

## 2026-10-23 — 3.5: the `ml.m5.large` quota pair requested in both accounts

*Claude's hand, the same session; the requests the user's, from the laptop as the infrastructure user
(`awsds-infra-prod`, `awsds-infra-staging`); the reading Claude's. Times as printed, then UTC.*

- **[user]** Ran 3.5's two commands, training `L-611FA074` and transform `L-236AE59F` of `ml.m5.large`
  at 2 in each account, and pasted the history read in both:

  ```
  -----------------------------------------------------------------------------------------------
  |                           ListRequestedServiceQuotaChangeHistory                            |
  +--------------------------------------+------+----------+------------------------------------+
  |  ml.m5.large for transform job usage |  2.0 |  PENDING |  2026-10-23T17:00:45.330000-03:00  |
  |  ml.m5.large for training job usage  |  2.0 |  PENDING |  2026-10-23T17:00:42.296000-03:00  |
  +--------------------------------------+------+----------+------------------------------------+

  -----------------------------------------------------------------------------------------------
  |                           ListRequestedServiceQuotaChangeHistory                            |
  +--------------------------------------+------+----------+------------------------------------+
  |  ml.m5.large for transform job usage |  2.0 |  PENDING |  2026-10-23T17:00:54.511000-03:00  |
  |  ml.m5.large for training job usage  |  2.0 |  PENDING |  2026-10-23T17:00:52.318000-03:00  |
  +--------------------------------------+------+----------+------------------------------------+
  ```

- **[Claude]** Read again at 20:02:06 UTC in Production and 20:02:07 in Staging: the four requests
  `PENDING`, created 20:00:42 to 20:00:54 UTC, no case id yet. Stage 17's requests of 2026-10-17 moved
  to `CASE_OPENED` and stayed there for days, so the next reading is the sitting's. The stage's 3.5,
  `waiting-on-the-user.md`, `runbooks/promotion.md` §0.2 and `CLAUDE.md` carry the state.

## 2026-10-23 — 5.4 and 8.3 run by the user from the laptop: the workgroup's override, the Production negatives, the prefixes

*The commands the user's, from the laptop signed in as the Data Scientist User through
`DataScientistProdAccess` (`awsds-scientist-prod`), the tunnel down; the paste the user's, the account id
and the address masked; the readings Claude's. The user's hand ran every command; Claude's hand wrote
this entry. Times: the paste carries none; the block ran about 20:20 to 20:35 UTC.*

- **[user] Block A, pasted:**

  ```
  aws athena start-query-execution --work-group awsds-prod-athena --query-string 'SELECT count(*) AS n FROM curated.trades' --query-execution-context Database=curated --result-configuration OutputLocation=s3://awsds-prod-outputs/not-enforced/ --profile awsds-scientist-prod --region us-west-2

  {
      "QueryExecutionId": "74895f10-caf8-460d-9186-654049b0820d"
  }

  aws athena get-query-execution --query-execution-id "74895f10-caf8-460d-9186-654049b0820d" --query 'QueryExecution.[Status.State,ResultConfiguration.OutputLocation,Statistics.DataScannedInBytes]' --output text --profile awsds-scientist-prod --region us-west-2

  SUCCEEDED       s3://awsds-prod-derived/results/74895f10-caf8-460d-9186-654049b0820d.csv        0

  aws athena get-query-results --query-execution-id "74895f10-caf8-460d-9186-654049b0820d" --query 'ResultSet.Rows[*].Data[*].VarCharValue' --output text --profile awsds-scientist-prod --region us-west-2

  n
  0

  aws athena get-work-group --work-group awsds-prod-athena --query 'WorkGroup.Configuration.[EnforceWorkGroupConfiguration,BytesScannedCutoffPerQuery]' --output text --profile awsds-scientist-prod --region us-west-2

  True    10737418240

  ➜  AWS-DataScience git:(main) aws sagemaker create-model-package-group --model-package-group-name awsds-canary-probe --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the CreateModelPackageGroup operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: sagemaker:CreateModelPackageGroup on resource: arn:aws:sagemaker:us-west-2:<Production>:model-package-group/awsds-canary-probe with an explicit deny in an identity-based policy
  ➜  AWS-DataScience git:(main) aws glue start-job-run --job-name awsds-prod-producer-proof --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the StartJobRun operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: glue:StartJobRun on resource: arn:aws:glue:us-west-2:<Production>:job/awsds-prod-producer-proof with an explicit deny in an identity-based policy
  ➜  AWS-DataScience git:(main) aws redshift-data execute-statement --workgroup-name awsds-prod-warehouse --database warehouse --sql 'select 1' --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (ValidationException) when calling the ExecuteStatement operation: Redshift endpoint doesn't exist in this region.
  ➜  AWS-DataScience git:(main)

  ➜  AWS-DataScience git:(main) aws s3 ls s3://awsds-prod-outputs/app-etl/outbox/ --profile awsds-scientist-prod --region us-west-2
  ➜  AWS-DataScience git:(main) aws s3 ls s3://awsds-prod-outputs/ --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-prod-outputs" with an explicit deny in a resource-based policy
  ➜  AWS-DataScience git:(main) aws s3 cp s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py - --profile awsds-scientist-prod --region us-west-2
  download failed: s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py to - An error occurred (403) when calling the HeadObject operation: Forbidden
  ```

- **[Claude] The readings.** The override, verification vi's first half: the query asked for
  `s3://awsds-prod-outputs/not-enforced/` and its result landed under `s3://awsds-prod-derived/results/`,
  the enforced location, `SUCCEEDED`, 0 bytes scanned, the count 0 (the table empty until 2.4's job);
  the workgroup reads `EnforceWorkGroupConfiguration` true and the cutoff 10,737,418,240 bytes, decision
  2's 10 GB. The two negatives of the set: `CreateModelPackageGroup` and `StartJobRun` refused *"with an
  explicit deny in an identity-based policy"*, `DenyProductionControlPlane`'s families (`sagemaker:Create*`,
  `glue:Start*`), the one layer that answers a control-plane action the `Workloads` document does not name.
  **`redshift-data:ExecuteStatement` validated before it authorized** (Lesson 21): with no workgroup in
  Production, the Data API answered *"Redshift endpoint doesn't exist in this region"*, a
  `ValidationException` and no authorization at all, so `DenyMintingARedshiftDatabaseSession` stays
  attached and unexercised for this set; the same command is run again at pass 6, with the workgroup up.
  The prefixes, 8.3's reading too, the tunnel down: `app-etl/outbox/` answered, empty; the bucket's root
  refused *"with an explicit deny in a resource-based policy"*, the bucket's
  `DenyThePersonaListingsOutsideTheNamedPrefixes`; the release's tree refused as a bare `403` on
  `HeadObject`, which carries no wording, so that refusal is attributed by a `get-object` instead, whose
  error body names the policy (the next command).

## 2026-10-23 — 5.4's read outside the prefixes, attributed by `get-object`

*The command the user's, as the Data Scientist User through `DataScientistProdAccess`; the paste the
user's, the account id and the address masked; the reading Claude's.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws s3api get-object --bucket awsds-prod-outputs --key applications/stage-09-proofs/v0/glue/producer_proof.py /dev/null --profile awsds-scientist-prod --region us-west-2

  aws: [ERROR]: An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<the data scientist user> is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-prod-outputs" with an explicit deny in a resource-based policy
  ```

- **[Claude]** The object does not exist yet (the script is uploaded at the Production sitting), so S3
  evaluated `s3:ListBucket` to choose between a 403 and a 404, and the bucket's
  `DenyThePersonaListingsOutsideTheNamedPrefixes` answered. The read deny,
  `DenyThePersonaReadsOutsideTheNamedPrefixes`, is attached and still unexercised for this principal: the
  same `get-object` after the upload is the reading that names it (Lesson 20).

## 2026-10-23 — 3.4's laptop half, the read: the persona from Sandbox reads the group

*The command the user's, from the laptop signed in as the Data Scientist User through
`DataScientistAccess` (`awsds-scientist-sandbox`); the paste the user's, the account id, the addresses
and the principal's unique id masked; the reading Claude's.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws sagemaker describe-model-package-group --model-package-group-name "arn:aws:sagemaker:us-west-2:<Production>:model-package-group/awsds-prod-model-app-etl" --profile awsds-scientist-sandbox --region us-west-2


  {
      "ModelPackageGroupName": "awsds-prod-model-app-etl",
      "ModelPackageGroupArn": "arn:aws:sagemaker:us-west-2:<Production>:model-package-group/awsds-prod-model-app-etl",
      "ModelPackageGroupDescription": "app-etl's model versions: registered and approved by the Production deploy role alone (Stage 9 step 3.2, D28 item 6)",
      "CreationTime": "2026-10-18T16:59:03.981000-03:00",
      "CreatedBy": {
          "IamIdentity": {
              "Arn": "arn:aws:sts::<Production>:assumed-role/AWSReservedSSO_InfrastructureAccess_c2bcabf74c885115/<the infrastructure user>",
              "PrincipalId": "<unique id>:<the infrastructure user>"
          }
      },
      "ModelPackageGroupStatus": "Completed"
  }
  ```

- **[Claude]** The read-status half of verification v, the persona's side: the group's record came back
  across the account boundary, through the group policy's read-status statement (3.2, decision 10) and
  the set's `ReadSageMakerStatus`, both halves of Lesson 28's intersection exercised by one call. The
  write half is the next command, `create-model-package`.

## 2026-10-23 — 3.4's write half, 8.1's laptop half, 2.5's drop and 2.6's read-back, from Sandbox

*The commands the user's, from the laptop signed in as the Data Scientist User through
`DataScientistAccess` (`awsds-scientist-sandbox`), the Production account id in a shell variable; the
paste the user's, the account ids and the address masked; the readings Claude's.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws sagemaker create-model-package --model-package-group-name "arn:aws:sagemaker:us-west-2:${PROD}:model-package-group/awsds-prod-model-app-etl" --model-package-description probe --inference-specification "{\"Containers\":[{\"Image\":\"${PROD}.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-app-etl:v0.2.1\"}],\"SupportedContentTypes\":[\"text/csv\"],\"SupportedResponseMIMETypes\":[\"text/csv\"]}" --profile awsds-scientist-sandbox --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the CreateModelPackage operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<the data scientist user> is not authorized to perform: sagemaker:CreateModelPackage on resource: arn:aws:sagemaker:us-west-2:<Production>:model-package/awsds-prod-model-app-etl/new because no resource-based policy allows the sagemaker:CreateModelPackage action
  ➜  AWS-DataScience git:(main) echo probe | aws s3 cp - s3://awsds-data-curated/warehouse/trades/probe.txt --profile awsds-scientist-sandbox --region us-west-2
  upload failed: - to s3://awsds-data-curated/warehouse/trades/probe.txt An error occurred (AccessDenied) when calling the PutObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<the data scientist user> is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::awsds-data-curated/warehouse/trades/probe.txt" because no identity-based policy allows the s3:PutObject action
  ➜  AWS-DataScience git:(main) aws sts assume-role --role-arn "arn:aws:iam::${PROD}:role/awsds-prod-debug" --role-session-name probe --profile awsds-scientist-sandbox --region us-west-2

  aws: [ERROR]: An error occurred (AccessDenied) when calling the AssumeRole operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<the data scientist user> is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::<Production>:role/awsds-prod-debug
  ➜  AWS-DataScience git:(main) echo probe | aws s3 cp - s3://noaa-ghcn-pds/awsds-probe.txt --profile awsds-scientist-sandbox --region us-west-2
  upload failed: - to s3://noaa-ghcn-pds/awsds-probe.txt An error occurred (AccessDenied) when calling the PutObject operation: Access Denied
  ➜  AWS-DataScience git:(main) aws s3 cp examples/app-etl/samples/trades.csv "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" --profile awsds-scientist-sandbox --region us-west-2
  upload: examples/app-etl/samples/trades.csv to s3://awsds-data-dropbox/incoming/2026/10/23/trades.csv
  ➜  AWS-DataScience git:(main) aws s3 cp "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" - --profile awsds-scientist-sandbox --region us-west-2
  download failed: s3://awsds-data-dropbox/incoming/2026/10/23/trades.csv to - An error occurred (403) when calling the HeadObject operation: Forbidden
  ```

- **[Claude] The readings.** **The registry gate (3.4, verification v's Sandbox half)**: the write was
  refused *"because no resource-based policy allows the sagemaker:CreateModelPackage action"*, the
  group policy's absence of a grant and no network condition, the wording the step asked for; the
  identity side had allowed it, or IAM would have named the identity policy first, so the gate is the
  resource policy alone (3.2). **8.1**: the direct put into the lake's own bucket refused by the set's
  implicit deny, *"no identity-based policy allows the s3:PutObject action"*, which keeps the bucket's
  branches unreached from this principal; the debug role refused at the trust, *"not authorized to
  perform: sts:AssumeRole"*, which STS never attributes; **the perimeter put answered a bare `Access
  Denied`**, S3's form for a bucket another account owns, which names no policy, and the set holds no
  `s3:PutObject` on that bucket anyway, so the implicit deny would answer before the perimeter document
  even in the attributed form (Lesson 20): `DenyS3ObjectWriteOutsideOrganization`'s exercise stays 1c's
  inverted document, and no laptop persona can exercise it. **2.5's drop** landed at
  `s3://awsds-data-dropbox/incoming/2026/10/23/trades.csv`, the writer's put by principal, waiting for the
  pickup run; **2.6's read-back** was refused as a bare `403` on `HeadObject`, the asymmetry holding,
  its wording owed to a `get-object` (the next command), as 5.4's was.

## 2026-10-23 — 8.4 run by the user from the laptop: Staging readable, the writes refused

*The commands the user's, from the laptop signed in as the Data Scientist User through
`DataScientistStagingAccess`, on the profile `awsds-scientist-staging` the user added to the laptop's
config this evening (8.4's block); the paste the user's, the account id and the address masked; the
readings Claude's.*

- **[user]**

  ```
  aws glue get-tables --database-name app_outputs --profile awsds-scientist-staging --region us-west-2

  {
      "TableList": []
  }

  ➜  AWS-DataScience git:(main) echo probe | aws s3 cp - s3://awsds-staging-outputs/probe.txt --profile awsds-scientist-staging --region us-west-2
  upload failed: - to s3://awsds-staging-outputs/probe.txt An error occurred (AccessDenied) when calling the PutObject operation: User: arn:aws:sts::<Staging>:assumed-role/AWSReservedSSO_DataScientistStagingAccess_c242dbe2f89a1229/<the data scientist user> is not authorized to perform: kms:GenerateDataKey on resource: arn:aws:kms:us-west-2:<Staging>:key/74f5ebbc-41bb-4165-9047-f84a952a833f because no resource-based policy allows the kms:GenerateDataKey action
  ➜  AWS-DataScience git:(main) aws glue start-job-run --job-name awsds-staging-app-etl --profile awsds-scientist-staging --region us-west-2

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the StartJobRun operation: User: arn:aws:sts::<Staging>:assumed-role/AWSReservedSSO_DataScientistStagingAccess_c242dbe2f89a1229/<the data scientist user> is not authorized to perform: glue:StartJobRun on resource: arn:aws:glue:us-west-2:<Staging>:job/awsds-staging-app-etl with an explicit deny in an identity-based policy
  ```

- **[Claude] The readings.** The catalog read answered, an empty list: no deploy has created a table in
  `app_outputs` yet, and an empty list is also what Lake Formation shows a principal with no grant, so
  the read is "answered", not "sees tables" (Lesson 13). The Glue write refused *"with an explicit deny
  in an identity-based policy"*, `DenyEveryWrite`'s `glue:Start*`. **The S3 write was refused by the
  data key's policy first**, *"kms:GenerateDataKey … because no resource-based policy allows"*: the
  bucket encrypts under `alias/awsds-staging-data`, which names no persona for `GenerateDataKey`, and
  S3 asked the key before it decided the put, so `DenyEveryWrite`'s `s3:Put*` and the bucket's
  `DenyThePersonaAnyWrite` stay attached and unexercised by this call (Lesson 20), the same order 6.3
  read on Production's data key. A write that takes no key, a delete, exercises the set's own deny; the
  next command.

## 2026-10-23 — 2.6's read-back and 8.4's delete, attributed

*The commands the user's, as the Data Scientist User through `DataScientistAccess`
(`awsds-scientist-sandbox`) and `DataScientistStagingAccess` (`awsds-scientist-staging`); the paste the
user's, the account ids and the address masked; the readings Claude's.*

- **[user]**

  ```
  ➜  AWS-DataScience git:(main) aws s3api get-object --bucket awsds-data-dropbox --key incoming/2026/10/23/trades.csv /dev/null --profile awsds-scientist-sandbox --region us-west-2

  aws: [ERROR]: An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<the data scientist user> is not authorized to perform: s3:GetObject on resource: "arn:aws:s3:::awsds-data-dropbox/incoming/2026/10/23/trades.csv" because no identity-based policy allows the s3:GetObject action
  ➜  AWS-DataScience git:(main) aws s3api delete-object --bucket awsds-staging-outputs --key probe.txt --profile awsds-scientist-staging --region us-west-2

  aws: [ERROR]: An error occurred (AccessDenied) when calling the DeleteObject operation: User: arn:aws:sts::<Staging>:assumed-role/AWSReservedSSO_DataScientistStagingAccess_c242dbe2f89a1229/<the data scientist user> is not authorized to perform: s3:DeleteObject on resource: "arn:aws:s3:::awsds-staging-outputs/probe.txt" with an explicit deny in a resource-based policy
  ```

- **[Claude] The readings.** **2.6 is closed**: the writer's read of what it wrote is refused by the
  set's implicit deny, *"no identity-based policy allows the s3:GetObject action"*, the wording Stage 5a
  pass 4d read; the letterbox asymmetry holds with the consumer now existing. **8.4's delete** was
  refused *"with an explicit deny in a resource-based policy"*, the bucket's `DenyThePersonaAnyWrite`,
  which IAM named ahead of the set's `DenyEveryWrite` (`s3:Delete*`), two explicit denies of which one is
  reported (Lesson 20): the set's deny is proven on Glue (`StartJobRun`), the bucket's on S3, and the
  set's S3 half stays attached and unexercised. The Staging persona writes nothing of the outputs bucket
  through three layers, the key, the bucket and the set, each read once.

## 2026-10-23 — 8.2: the S3 console under the principal branch, read in the user's browser session

*Claude's hand, reading the AWS console in the user's Chrome session, signed in by the user as the
Data Scientist User in Production through `DataScientistProdAccess`, `us-west-2`; five pages read,
nothing clicked but the navigation; the console's messages quoted as shown. About 21:00 UTC.*

- **The bucket list** (`S3 → General purpose buckets`): *"You don't have permissions to list
  buckets"*, naming `s3:ListAllMyBuckets`, the list empty. The persona reaches a bucket by its URL alone.
- **`awsds-prod-outputs`, Objects at the root**: *"Insufficient permissions to list objects"*, naming
  `s3:ListBucket`, the bucket's listing deny outside the named prefixes.
- **`awsds-prod-outputs`, Objects at `app-etl/outbox/`** (the URL with `prefix=app-etl/outbox/`): the
  listing opens, *"Objects (0)"*, *"You don't have any objects in this folder"*; the one page that works.
  A download from it is the `s3:GetObject` the policy allows and waits for an object.
- **Properties**: *"Insufficient permissions"* on the overview, and every panel refused by name:
  versioning, ABAC, tags, default encryption, archive tiers, server access logging, event
  notifications, transfer acceleration, Object Lock, requester pays.
- **Permissions**: the bucket policy, Object ownership, the ACL and CORS refused; Block Public Access
  shows the API response, `s3:GetBucketPublicAccessBlock` refused *"with an explicit deny in a
  resource-based policy"*, the bucket's deny on the persona's reads outside the named prefixes; the
  Access Analyzer panel *"could not load the content for the page"*.
- **The fraction, INT-06's answer**: one page of the console works for the persona, the object listing
  under a named prefix reached by URL, with its downloads; the bucket list, the root listing and every
  bucket-level tab refuse. The console is a URL-and-prefix tool for this persona, and `README.md` says
  so; open question 8 is closed, and the CLI is the whole surface beyond that page.

## 2026-10-23 — the session's branch and its PR

*Claude, the same session; no AWS call.*

- **[Claude] The PR**: the session's first commit opened PR #248 against `main` on 2026-10-23 at
  16:38 UTC, from the branch `claude/stages-8-9-10-prep-2` cut from `main` after PR #247's merge retired
  the previous branch, and every later commit of the session joined it: decision 13 taken and done, the
  quota requests, the persona proofs block by block, and the records. The description follows the branch.

## 2026-10-23 — 2.4's job and 9.4's grant applied, the script uploaded, with the environment down

*Claude's hand, on the user's authorization in chat (*"Autorizo as aplicações 1 a 3 do §0.4 … e o upload
do script, cada uma de um plano fresco"*), as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`), the tunnel down, after the user's fresh `./aws/login.py`; no other session running
on the machine (`list_sessions`, every row idle). Each apply from a saved plan read first (Recipe A), the
plans outside the repository. Times UTC.*

- **[Claude] `production/sagemaker/`**: the fresh plan at 21:17:03 to 21:17:19, *"Plan: 1 to add, 1 to
  change, 0 to destroy."*, the job `awsds-prod-producer-proof` and the role's inline `job` policy;
  applied 21:18:32 to 21:18:42, *"Apply complete! Resources: 1 added, 1 changed, 0 destroyed."* (the
  policy modified in 1 s, the job created in 2 s); re-planned `No changes` at 21:18:54.
- **[Claude] `production/workloads/`**: the fresh plan at 21:17:31 to 21:17:49 read **`No changes`**:
  the `vpc-v0.4.0` bump had been applied in the evening of 2026-10-22 with Stage 9's passes (this log's
  entry of that evening), and Stage 10's 1.2 and `runbooks/promotion.md` §0.4 still called it unapplied;
  both are corrected. Nothing applied.
- **[Claude] `production/foundation/`**, with `-var-file=<project folder>/secrets/alerts.auto.tfvars`:
  the fresh plan at 21:17:49 to 21:18:12, *"Plan: 0 to add, 1 to change, 0 to destroy."*, the deploy
  role's inline `apply-application` gaining `RunTheGovernedWarehouseDdl` (9.4); applied 21:19:16 to
  21:19:26, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*; re-planned `No changes`
  with the var-file. `./aws/deploytargets.py awsds-infra-prod` at 21:19:42: all checks passed.
- **[Claude] The script**: `aws s3 cp` of `proofs/producer_proof.py` (7,318 bytes) to
  `s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py` at 21:20:09, the
  write the bucket's principal branch and the data key admit `InfrastructureAccess` to; `head-object`
  reads 7,318 bytes, `aws:kms` under the data key with the bucket key on, version
  `LhV4dvLqaXJCFqSJm.Z0tpmqShZjHM95`. `get-job` reads the job as declared: Glue 6.0, two `G.1X`, 20
  minutes, the connection `awsds-prod-jobs`, the script's location, `--MODE producer`,
  `--datalake-formats iceberg`, `curated`, `trades`, `incoming`.
- **[Claude] What this leaves for the Production sitting**: `make hub-up`, `make up ENV=production
  ONLY=workloads-egress`, the two runs and their readings (`runbooks/promotion.md` §P). With the script
  in place, 5.4's `get-object` from the persona now meets the read deny rather than the listing deny, a
  one-command reading the user may take at any time.

## 2026-10-23 — 2.4's producer run: the write refused at the vend, naming the data lake settings; the lake's flag planned

*Claude's hand, on the user's authorization in chat (*"Autorizo a execução producer do job
awsds-prod-producer-proof agora, como usuário de infraestrutura em Production, e a leitura dos
resultados."*), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod` for the run
and its trail, `awsds-infra-data` for the lake's readings and the plan); the hub and
`production/workloads-egress/` up, raised by the user (`make status`: seven endpoints available). Times UTC.*

- **[Claude] The run**: `start-job-run` at 21:43:25, run
  `jr_3a45dc0e7e994943f6e4eca20664083ca0437fef7b1a2302ae8bd03ca79a287f`, started 21:43:26, **`FAILED`** at
  21:44:42 after 56 s of execution, 113 DPU-seconds. The script's lines in `/aws-glue/jobs/output`:
  *"running as arn:aws:sts::<Production>:assumed-role/awsds-prod-job-exec/GlueJobRunnerSession, mode
  producer"* at 21:44:08 and *"producer: inserting 10 sample rows into lake.curated.trades"* at 21:44:25;
  the first SQL failed with *"Failed to retrieve AWS Lake Formation temporary credentials for table
  arn:aws:glue:us-west-2:<Data Governance>:table/curated/trades with permission SELECT. Error:
  Insufficient Lake Formation permissions. Verify the data lake settings for account (Service:
  LakeFormation, Status Code: 400, Request ID: 1230a16c-812b-4c80-bf11-bfa9d4401d19)"*, the sentence
  naming no account. The error stream's last cause, *"Connection refused: /10.32.58.144:35175"*, is the
  executor losing the driver after its exit, an address in `VPC-Workloads`' private range.
- **[Claude] Production's trail** (`lookup-events` at 21:46 and 21:57): six `glue:GetTable` at 21:44:29
  answered through `vpce-0925d883174fd23c1`, the `glue` endpoint; four `lakeformation:GetDataAccess` at
  21:44:30 through `vpce-0431cce5692733205`, the `lakeformation` endpoint, each `AccessDenied` with the
  wording above, two from the driver's SDK (`aws-sdk-java/2.44.6`) naming the lake's table and the job
  in `auditContext`, two invoked by `glue.amazonaws.com` with no request parameters logged; one
  `glue:GetConfig` at 21:44:30 through the Glue endpoint, `ForbiddenResponse`; the session's
  `GetCallerIdentity` at 21:44:08 through `vpce-004b999946b362a5e`, the `sts` endpoint. No
  `GetTemporaryGlueTableCredentials` event in three hours: the vend is logged as `GetDataAccess`.
  **Stage 10 0.5 is answered**: the job's Lake Formation call carries the `lakeformation` endpoint's id,
  the endpoint decision 12 (a) raised.
- **[Claude] The lake's trail**: no Lake Formation event in the run's window. A cross-account vend the
  lake answers is logged there too, with a `sharedEventID` and no user name: 5.4's Athena read of
  `curated.trades` by the Data Scientist User in Production at 20:29:09 left its pair, `GetDataAccess`
  invoked by `athena.amazonaws.com` on Production's resource link and by `glue.amazonaws.com` on the
  lake's table, answered in both trails. The run's vend was refused in Production before any event
  reached the lake.
- **[Claude] The readings and the fallback**: Production's settings re-read at 21:53, the flag `true`,
  one administrator, both lists empty, `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`; the lake's at
  21:53, the flag unset and the rest the same; `./aws/datalake.py awsds-infra-data` at 21:46 all checks
  passed, `DL-5` 4/TRUE, `DL-6` and `DL-13` passing. The wording names the data lake settings with
  Production's flag on, which is decision 13's fallback: `data-governance/data/lakeformation.tf` gains
  `allow_full_table_external_data_access = true` and its README the row; the slice initialised in the
  worktree (`gen-tfvars.py`, `gen-backend-hcl.py`, `init`) and planned as `awsds-infra-data` at 21:55:41
  to 21:56:00, *"Plan: 0 to add, 1 to change, 0 to destroy."*, the flag `false -> true` and eight
  attributes unchanged, the plan saved outside the repository. The apply waits on the user's
  authorization, then `DL-5` after it and the second run.

## 2026-10-23 — decision 13's lake half applied: the flag on in Data Governance

*Claude's hand, on the user's authorization in chat (*"Pode prosseguir com os applies e todas as etapas
que você conseguir executar sem q minha intervenção."*), as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-data`); no other session running on the machine (`list_sessions`,
every row idle). Recipe A, the plan outside the repository, `DL-5` before and after. Times UTC.*

- **[Claude] Before**: `./aws/datalake.py awsds-infra-data` at 22:01:58, all checks passed, `DL-5`
  `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`, `DL-6` and `DL-13` passing. The fresh plan at 22:02:36
  to 22:02:55, *"Plan: 0 to add, 1 to change, 0 to destroy."*, one resource,
  `allow_full_table_external_data_access = false -> true`.
- **[Claude] The apply** at 22:02:55 to 22:03:05, *"aws_lakeformation_data_lake_settings.this:
  Modifications complete after 1s"*, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*;
  the resource's id moved from `4042482338` to `1412964709`, a hash of the settings.
- **[Claude] After**: `get-data-lake-settings` at 22:03:49 reads the flag `true`, one administrator,
  both create-default lists empty, the parameters `4` / `TRUE`, `ExternalDataFilteringAllowList` `[]`,
  `AuthorizedSessionTagValueList` and `TrustedResourceOwners` absent; `./aws/datalake.py` at 22:03:50
  all checks passed, the two standing notes (`DL-7`, `DL-11`); the re-plan at 22:04:42 **`No changes`**.
  The flag now reads `true` in Production, Sandbox and Data Governance, unset in Staging.

## 2026-10-23 — 2.4's producer run again, with both flags on: the governed write committed

*Claude's hand, the same authorization and identity (`awsds-infra-prod`), the hub and
`production/workloads-egress/` up. Times UTC.*

- **[Claude] The run**: `start-job-run` at 22:04:44, run
  `jr_954bd067091522ca86a459b9887e4ab3d0d3055fae0130aa845965de4f8e2b09`, **`SUCCEEDED`** at 22:06:27
  after 79 s of execution, 158 DPU-seconds, 99 s after the lake's flag went on. The script's lines:
  *"running as …awsds-prod-job-exec/GlueJobRunnerSession, mode producer"* 22:05:33; *"inserting 10
  sample rows into lake.curated.trades"* 22:05:42; *"the insert committed"* 22:06:11;
  *"lake.curated.trades holds 10 row(s) through the share"* 22:06:14, the ten rows printed, dated
  2026-10-01 to 2026-10-05; *"the direct put was refused: AccessDenied: User:
  …awsds-prod-job-exec/GlueJobRunnerSession is not authorized to perform: kms:GenerateDataKey on this
  resource because the resource does not exist in this Region, no resource-based policies allow access,
  or a resource-based policy explicitly denies access"* 22:06:16; *"done"*. The refusal came from the
  lake's data key, one layer before the S3 identity-policy wording 2.4 expected, the same order 8.4
  read for the Staging persona: the job role's missing `s3:PutObject` stays attached and unexercised
  (Lesson 20). The error log group carries Spark's executor noise (*"SparkContext should only be created
  and accessed on the driver"*, *"A master URL must be set"*) and no failure.
- **[Claude] The vends in both trails**: eight `GetDataAccess` in Production between 22:05:45 and
  22:06:15, every one answered through `vpce-0431cce5692733205`, in pairs: one from the driver's SDK
  naming the lake's table, one invoked by `glue.amazonaws.com` whose `sharedEventID` is also in the
  lake's trail (four events there, the role's session as the principal, `invokedBy`
  `glue.amazonaws.com`). The first run's refused vends had reached neither leg of that pair in the lake.
- **The readings 2.4 owed**: the mode admits a writer holding `INSERT`, `DELETE` and `ALTER` without
  `ALL`, so the `ALL` fallback is not taken; the commit went through with `glue:UpdateTable` in the
  role, which the next run without it would measure, and is not measured; the flag is needed in the
  owner's account, and whether Production's is also needed is the third run's measurement, the
  user's hand.

## 2026-10-23 — 9.1's `production/warehouse/` applied: the governed namespace

*Claude's hand, the same authorization (*"Pode prosseguir com os applies…"*), as the infrastructure user
with `InfrastructureAccess` (`awsds-infra-prod`); `runbooks/promotion.md` §W step 2. Recipe A, the
plan outside the repository. Times UTC.*

- **[Claude] The plan**, the slice initialised in the worktree, at 22:06:09 to 22:06:18: *"Plan: 9 to
  add, 0 to change, 0 to destroy."*, the count 9.1 planned on 2026-10-22: the three audit log groups
  (`connectionlog`, `userlog`, `useractivitylog` under `/aws/redshift/awsds-prod-warehouse/`), the
  alarms `awsds-prod-warehouse-compute-capacity` and `-data-storage`, the role
  `awsds-prod-warehouse-exec`, the namespace, the security group and its 5439 ingress rule.
- **[Claude] The apply** at 22:07:07 to 22:07:20, *"Apply complete! Resources: 9 added, 0 changed, 0
  destroyed."*, the namespace `awsds-prod-warehouse` created in 2 s, the security group
  `sg-0f018ef6c4848a9a3`; the re-plan at 22:07:32 **`No changes`**. The outputs: the admin secret
  `redshift!awsds-prod-warehouse-dbadmin-…`, Redshift-managed; capacity base 4, max 8, the usage
  limit 10 RPU-hours monthly, `max_query_execution_time` 120; the namespace ARN. No workgroup exists:
  `production/warehouse-compute/` is `[E]`, raised by `make up … ONLY=warehouse-compute GROUPS=redshift`
  once `layers.py`'s refusal 9 is lifted, and 9.3's SQL waits on the user's schema theme and quota
  (`waiting-on-the-user.md`).

## 2026-10-23 — 2.5's pickup run: the drop consumed, curated through the write path, deleted

*Claude's hand, the same authorization and identity (`awsds-infra-prod`), the hub and
`production/workloads-egress/` up; the drop `incoming/2026/10/23/trades.csv` (362 bytes) made by the
user as the Data Scientist User in Sandbox at 20:47 UTC. Times UTC.*

- **[Claude] The run**: `start-job-run` at 22:09:38, run
  `jr_4039ad141615c4ac81136dccb766dff822ff964b27ac84ee5db7a88ea8153683`, **`SUCCEEDED`** at 22:11:33
  after 97 s of execution, 194 DPU-seconds. The script's lines: *"pickup: 1 CSV object(s) under
  s3://awsds-data-dropbox/incoming/: incoming/2026/10/23/trades.csv"* 22:10:34, the three `.txt`
  objects of `EXC-02` passed over; *"pickup: 10 row(s) read as the job role, under the lake data key
  (the KMS half)"* 22:11:09; *"pickup: 10 row(s) curated into lake.curated.trades"* 22:11:19;
  *"lake.curated.trades holds 20 row(s) through the share"* 22:11:20, the sample rows and the CSV's
  carrying the same ten trades, so each prints twice; *"pickup: deleted
  s3://awsds-data-dropbox/incoming/2026/10/23/trades.csv; a read after the delete answers 404: Not
  Found"* 22:11:21; *"the letterbox is empty"*; *"done"*.
- **[Claude] The drop-box after**: the listing at 22:13 holds the three `.txt` objects alone. The
  bucket is versioned, so the delete is a **delete marker** (`YoD2rVa6…`, 22:11:22) over the object's
  version (`.UmZxqIbd…`, 362 bytes), which stays until the bucket's lifecycle expires it.
- **[Claude] Production's trail** (22:11): the drop-box read's `kms:Decrypt` at 22:11:08 invoked by
  `fas.s3.amazonaws.com` as the job role's session, the KMS half of INT-10 answered by the lake's data
  key; the vends in pairs through the `lakeformation` endpoint at 22:11:12, 22:11:18 and 22:11:21, the
  `GetTable`s through the `glue` endpoint, and one `glue:UpdateTable` at 22:11:19 invoked by
  `glue.amazonaws.com`, the Iceberg commit. The lake's trail had not yet shown the decrypt at 22:13.
- **[Claude] The lake's trail at 22:26**, after the log's lag: the drop-box read's `kms:Decrypt` at 22:11:08
  as the job role's session, the cross-account principal (`sharedEventID` with Production's event); then,
  from 22:11:12 to 22:11:21, every `Decrypt` on the curated data is the registration role's
  (`awsds-data-lf-registration`, sessions `AWSLF-00-NA-…`), the credentials Lake Formation vended: the
  job role's own session touched no `curated` object, which is D13 read in the trail.

## 2026-10-23 — 4.3a's first apply of the re-cut `staging/egress/`, read back

*The apply the user's, `make up ENV=staging ONLY=egress` from the project folder as the infrastructure
user with `InfrastructureAccess` (`awsds-infra-staging`), the hub up (the user's words: "staging está
no ar"); Claude's hand reading. Times UTC.*

- **[user] The apply**, the slice's first since 4.3a re-cut it to `VPC-Workloads`' endpoint set (16 to
  add). **[Claude] Read at 22:44**: `./aws/egress.py awsds-infra-staging` all checks passed, `EG-1` and
  `EG-2` on each endpoint, `EG-5` ~0.070 USD/h; the seven interface endpoints `available`, `glue`,
  `kms`, `lakeformation`, `logs`, `sagemaker.api`, `secretsmanager` and `sts`, each single-AZ in
  `usw2-az1`, no `ecr.*` among them (Stage 10 verification xvi's premise); the DNS Firewall rule group
  `awsds-staging-egress`.

## 2026-10-23 — the Production sitting's end: `workloads-egress/` down, zero burn

*The teardown the user's, `make down ENV=production` from the project folder as the infrastructure user
with `InfrastructureAccess` (the user's words: "production está sendo destruído"); Claude's hand
reading. Times UTC.*

- **[Claude] The reading**: Production's interface endpoints gone at 22:48; `./aws/egress.py
  awsds-infra-prod` at 22:49:56 reads 0 interface endpoints, 0 NAT gateways, 0.000 USD/h, `EG-5`
  *"none - the correct between-sessions state (D11)"*. The hub stays up for the Staging leg (Stage 8's
  log). The sitting's balance in Production: the proof job's three runs (one refused, two
  `SUCCEEDED`), `curated.trades` at twenty rows, the lake's flag on, the governed namespace applied.

## 2026-10-23 — the sitting's end: the hub down

*Claude's hand, on the user's authorization in chat (*"Autorizo make hub-down agora, com a leitura do
make status depois."*), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`); no
other session running on the machine. Times UTC, past midnight into 2026-10-24.*

- **[Claude] `make hub-down`** at 00:06:39 to 00:06:49: the dormant hook stopped `awsds-prod-vpn`
  (`i-011ffd7b…`) and `awsds-prod-proxy` (`i-0d42d039…`), every other slice refused as always. A
  `make status` in the same minute still read the proxy `UP` while it was stopping; at 00:09 both
  hosts read `stopped` (`t3.nano`, `t3.micro`), and `make status` at 00:10 reads every `[E]` slice down
  with 0 resources, the three `[D]` hosts stopped, the burn **0.0000 USD/h**. The evening's balance:
  Stage 9 2.4-2.6 and 9.1, Stage 10 0.5 and the Staging half of passes 1-2 by hand (Stage 8 3.8), two
  policy fixes, one module release, the estate at zero burn.

## 2026-10-23 — 9.3's theme and quota, the user's decision

*The user's hand, in chat (00:15 UTC on 2026-10-24); Claude recording.*

- **[user]** *"Confirmo o tema trades e a cota de 1 TB para o primeiro schema governado (Stage 9 9.3)."*
  The proposal of 2026-10-23 stands as the decision: the schema `trades` in the database `governed`, owner
  `gov_trades_owner`, `QUOTA 1 TB`, the roles `gov_trades_rw` and `gov_trades_ddl`, the statements as 9.3
  carries them. The waiting list's row leaves; §W runs them at the next Production sitting, the compute
  raised with `GROUPS=redshift`.

## 2026-10-24 — 9.3's governed schema: the statements run through the Data API

*Claude's hand, on the user's authorization in chat (*"rodei make hub-up e make up ENV=production
ONLY=workloads-egress,warehouse-compute GROUPS=redshift. Pode prosseguir. Autorizo os applies
necessários."*), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), through
`redshift-data` with the namespace's admin secret (`redshift!awsds-prod-warehouse-dbadmin-…`), one
`execute-statement` per statement. The workgroup `awsds-prod-warehouse` `AVAILABLE` since 00:23:05, base 4
and max 8 RPU, the usage limit 10 RPU-hours monthly `deactivate`, the `redshift-serverless` endpoint among
the nine of `VPC-Workloads`. Times UTC.*

- **[Claude] The readings first** (00:26:52 to 00:27:05): the secret authenticated at the first call, so
  `EXC-13`'s database half reads true for a namespace no rotation has touched; `public`'s ACL in
  `warehouse` and in `dev` `{rdsdb=UCDA/rdsdb,=UC/rdsdb}`, so `PUBLIC` held `USAGE` and `CREATE` on both,
  the `CREATE` owed a revoke; both databases' `datacl` null, the defaults.
- **[Claude] The statements** (00:27:50 to 00:29:21, each `FINISHED`, none above 0.6 s): in `warehouse`,
  `REVOKE CREATE ON SCHEMA public FROM PUBLIC`, `REVOKE ALL ON DATABASE warehouse FROM PUBLIC`,
  `CREATE DATABASE governed`; in `dev`, the same two revokes; in `governed`, `public`'s ACL read the same
  `=UC/rdsdb` and the two revokes ran, then `CREATE USER gov_trades_owner PASSWORD DISABLE NOCREATEDB
  NOCREATEUSER`, `CREATE SCHEMA trades AUTHORIZATION gov_trades_owner QUOTA 1 TB`, `CREATE ROLE
  gov_trades_rw`, `GRANT USAGE ON SCHEMA trades TO ROLE gov_trades_rw`, `CREATE ROLE gov_trades_ddl`,
  `GRANT USAGE, CREATE ON SCHEMA trades TO ROLE gov_trades_ddl`, `CREATE USER "IAMR:awsds-prod-job-exec"`
  and `CREATE USER "IAMR:awsds-deploy-prod"` (both `PASSWORD DISABLE NOCREATEDB NOCREATEUSER`), `GRANT
  ROLE gov_trades_rw TO "IAMR:awsds-prod-job-exec"`, `GRANT ROLE gov_trades_ddl TO "IAMR:awsds-deploy-prod"`,
  `ALTER DEFAULT PRIVILEGES FOR USER "IAMR:awsds-deploy-prod" IN SCHEMA trades GRANT SELECT, INSERT,
  DELETE ON TABLES TO ROLE gov_trades_rw`. The theme and the quota are the user's decision of 00:15.
- **[Claude] Read back** (00:30:33 to 00:31:15, the Data API as the admin): `pg_user` holds six users:
  `rdsdb`, `dbadmin`, `gov_trades_owner`, `IAMR:awsds-prod-job-exec`, `IAMR:awsds-deploy-prod` and
  **`IAMR:AWSReservedSSO_InfrastructureAccess_c2bcabf74c885115`, superuser**, the user 9.8 predicted
  nobody would create, born of the first IAM-authenticated session (`./aws/warehouse.py` or the compute's
  apply) and not of this sitting's statements; `svv_roles` the two roles, owner `dbadmin`;
  `svv_user_grants` `IAMR:awsds-deploy-prod` → `gov_trades_ddl` and `IAMR:awsds-prod-job-exec` →
  `gov_trades_rw`; `pg_namespace` `trades` owned by `gov_trades_owner`; `svv_default_privileges` three
  rows for `trades`, `RELATION`, owner `IAMR:awsds-deploy-prod`, `SELECT`, `INSERT` and `DELETE` to the
  role `gov_trades_rw`; the databases' ACLs `{dbadmin=CTA/dbadmin}` for `warehouse` and `governed`,
  `{rdsdb=CTA/rdsdb}` for `dev`, `PUBLIC` gone from all three; `public`'s ACL `=U/rdsdb` in each, the
  `CREATE` revoked. `./aws/warehouse.py awsds-infra-prod --sql` at 00:31:19: OK, `WH-6` *"`governed` plus
  the inert ['dev', 'warehouse']"*, `WH-12` one themed schema, `WH-15` idle at 8 RPU-seconds, `WH-14` a note
  until a table exists, `WH-13` the quota unreadable.
- **[Claude] The audit groups** (read 00:35, Lesson 62): `connectionlog` carries the admin's Data API
  session (*"authenticated | 00:26:52 | 127.0.0.1 | warehouse | dbadmin | password | TLSv1.3"*),
  `useractivitylog` its statements (*"db=governed user=dbadmin … LOG: CREATE SCHEMA trades AUTHORIZATION
  gov_trades_owner QUOTA 1 TB"*), `userlog` the three `create` events of 00:28:31, 00:29:01 and 00:29:06;
  Production's export carries what Sandbox's never did (`EXC-16`).
- **[Claude] `make down ENV=production`** (`AUTO=1`, to 00:47:16): `warehouse-compute/` *"2 destroyed"*,
  the workgroup and its usage limit, `workloads-egress/` *"17 destroyed"*, the seven endpoints with the
  `redshift-serverless` one `GROUPS=redshift` added and the firewall, every other `[E]` slice 0; the
  namespace `AVAILABLE` with `governed` and its schema, `[P]`. `./aws/egress.py awsds-infra-prod` at 00:47:34
  reads no interface endpoint and no NAT; `make status` at 00:48 reads every `[E]` slice down and the burn
  0.0156 USD/h, the hub's two hosts, whose `make hub-down` is the user's. 9.5's datashare (both sides),
  9.6 and 9.7 are the sitting that follows.
- **[Claude] `make hub-down`** (00:52:15 to 00:52:20, on the user's authorization in chat, *"Autorizo make
  hub-down agora, com a leitura do make status depois."*): the dormant hook stopped `awsds-prod-vpn` and
  `awsds-prod-proxy`, both `stopped` a minute later; `make status` at 00:53 reads the three `[D]` hosts
  stopped, every `[E]` slice down and the burn **0.0000 USD/h**. No other session running on the machine.

## 2026-10-24 — the fifth sitting with the environment down: the readings, 9.5 as commands, decision 14

*Claude's hand, in the session `stages-8-9-10-prep-f13bc2` (the branch `claude/stages-8-9-10-prep-f13bc2`,
cut from `main` at PR #250's merge), on the user's request. AWS read as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`,
`awsds-infra-data`, `awsds-infra-identity`), reads only, the tunnel down; no other session running on the
machine. Nothing applied. Times UTC.*

- **[user] The request**: *"Em relação aos estágios 8, 9 e 10, peço fazer o seguinte: verifique o status
  atual de cada estágio. revise o plano destes estágios considerando o andamento atual, o resultado com as
  leituras e preparações prévias realizadas para execução destes estágios. Faça a preparação necessária
  para a execução destes estágios com tudo o que pode ser feito sem que seja necessário subir o ambiente.
  Prepare tudo que for necessário para executarmos de forma mais célere estas etapas uma vez que eu consiga
  subir o ambiente. Verifique o andamento recente e os últimos commits. Propague as correções e alterações
  necessárias aos passos restantes do plano considerando isso. Usuário infra sso logado para as
  leituras."*
- **[Claude] The quota requests**, 01:58: the four `ml.m5.large` requests of 2026-10-23 (training
  `L-611FA074` and transform `L-236AE59F`, 2 each, Production and Staging) read `CASE_OPENED`, each with a
  support case id, last updated between 20:03 and 21:00 on 2026-10-23.
- **[Claude] The instruments**, 01:59 to 02:07: `./aws/egress.py` on the three compute profiles all checks
  passed, `EG-5` *"none - the correct between-sessions state"*; `./aws/warehouse.py awsds-infra-prod` and
  `./aws/datalake.py awsds-infra-data` OK; `./aws/deploytargets.py` on the five infrastructure profiles
  all checks passed. A first run of it on Production and Staging alone failed `DT-8` (*"none while
  staging/data/ stands"*) while its section 5 listed Staging's two resource links to the lake: without
  `awsds-infra-data` the check cannot resolve the lake's account, so the failure was the invocation's
  (Lesson 62). `make status`, 02:08 to 02:22: every `[E]` slice down with 0 resources, the estimated
  burn 0.0000 USD/h. `terraform version` reads 1.15.8, so the 1.16.6 pins still wait on the user's install.
- **[Claude] 9.5 read on AWS's step pages**, by a research agent of this session: the Redshift guide's
  Lake Formation producer, consumer and considerations pages, `CREATE DATASHARE`, `ALTER DATASHARE`,
  `GRANT`, `CREATE DATABASE`, the Lake Formation guide's prerequisites, permissions, notes, LF-Tag and
  cross-account pages, the API references and two AWS blogs (`docs/REFERENCES.md`). 9.5 now carries shape
  (ii) as five steps across Production, the Lake Formation account and Sandbox, and what the pages leave
  unsaid: a read with Production's workgroup gone, a cross-account LF-Tag grant on a federated database,
  the principal behind a `RedshiftDbUser` tag, an empty share's registration, and the `CREATE USER`
  contradiction between one page and both blogs. Two rules open **decision 14**, the account that
  registers and grants: an LF-Tag cannot be put on a resource shared from another account, and a
  receiving account cannot pass a share on. Recommended: Data Governance, whose registration
  `DenyLakeDeletionAndDeregistration` makes permanent. 9.5a is settled by decision 5 (no switch).
- **[Claude] What 9.6 and 9.7 still need**: a table in `trades`. 9.4's DDL and load job, which decision 6
  puts in the application repository and the pipeline runs, are unwritten; they ride a release after
  `v0.3.0`'s first promotion.
- **[Claude] The texts**: 3.5 (the requests' state), 9.5, 9.5a, decision 14 and the decisions' preamble,
  the Status row (two sentences joined without a stop since PRs #248 and #250, separated);
  `runbooks/promotion.md` (where it stands, §0.5, §W step 5, §T's prerequisite); `waiting-on-the-user.md`
  (the quota row, decision 14, 6d decision due 11, the persona's Athena read moved out of the Production
  sitting, since 5.4's sequence needs nothing up).

## 2026-10-24 — `EXC-02`'s cleanup refused to Claude by the auto-mode classifier; 9.8's network and README rows

*Claude's hand, on the user's word in chat (*"Pode prosseguir com as etapas que não dependem do ambiente no
ar"*), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-data`, `awsds-infra-prod`).
Times UTC.*

- **[Claude] `EXC-02`'s before-reading**, 03:04:20: the three `.txt` objects the row names are the current
  versions under `incoming/` (38, 213 and 213 bytes), `trades.csv` behind its delete marker of 22:11:22;
  the bucket policy holds no deny on `s3:DeleteObject`, so `InfrastructureAccess` in its own account may
  delete. The three `delete-object` calls were refused before running by Claude Code's auto-mode
  classifier (*"judged this action dangerous"*); nothing was deleted, and a listing at 03:04:48 reads the
  three objects in place. The cleanup is the user's from the project folder, the command in
  `runbooks/promotion.md` §0.5; the row retires after Claude's read-back.
- **[Claude] 9.8's paperwork for what 9.3's sitting raised**: `docs/NETWORK.md`'s two rows and
  `terraform-live/README.md` still called the governed workgroup unapplied; they now carry its first raise,
  2026-10-24 00:23 to 00:47. `AWS_STATE.md` already held the two database users nobody created (PR #250),
  so it is unchanged. `INT-24` carries the step pages' reading and decision 14.

## 2026-10-24 — `EXC-02`'s cleanup by the user, read back; 5.4's read of the twenty rows as the persona

*The user's hand for the delete and the query, Claude's for the read-back and the record. The delete as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-data`), from the project folder, with
`runbooks/promotion.md` §0.5's command; the query as the Data Scientist User with
`DataScientistProdAccess` (`awsds-scientist-prod`), signed in with `aws sso login --sso-session
awsds-scientist --no-browser`, the tunnel down. Times UTC.*

- **[user] `EXC-02`'s three `.txt` objects deleted** from `awsds-data-dropbox`, the auto-mode classifier
  having refused Claude's delete. **[Claude] Read back at 03:12:47** as `awsds-infra-data`: `incoming/`
  holds no current object; each `.txt` is a delete marker, `probe-4d-sandbox.txt` at 03:12:22,
  `awsds-6g-24-probe.txt` at 03:12:28 and `awsds-6g-24-probe-tunnel.txt` at 03:12:32, over its version
  (38, 213 and 213 bytes), which the bucket's 90-day noncurrent rule expires; `trades.csv` behind its
  marker of 2026-10-23. `AWS_STATE.md`'s row is closed, and `GOVERNANCE.md`, open question 19, the lake's
  README, `buckets.tf`'s comment and 2.5's text say the collector exists.
- **[user] 5.4's first query**, the output pasted in chat, verbatim:

  ```
  aws athena start-query-execution --work-group awsds-prod-athena --query-string 'SELECT count(*) AS n FROM curated.trades' --query-execution-context Database=curated --result-configuration OutputLocation=s3://awsds-prod-outputs/not-enforced/ --profile awsds-scientist-prod --region us-west-2

  {
      "QueryExecutionId": "d78c3939-168a-4c28-8313-246620114d06"
  }

  aws athena get-query-execution --query-execution-id "d78c3939-168a-4c28-8313-246620114d06" --query 'QueryExecution.[Status.State,ResultConfiguration.OutputLocation,Statistics.DataScannedInBytes]' --output text --profile awsds-scientist-prod --region us-west-2

  SUCCEEDED       s3://awsds-prod-derived/results/d78c3939-168a-4c28-8313-246620114d06.csv        0

  aws athena get-query-results --query-execution-id "d78c3939-168a-4c28-8313-246620114d06" --query 'ResultSet.Rows[].Data[].VarCharValue' --output text --profile awsds-scientist-prod --region us-west-2

  n       20
  ```

- **[Claude] The reading**: the persona reads `curated.trades` through Production's resource link, the
  share's `SELECT` and `awsds-prod-athena`, the count 20 the producer's ten and the pickup's ten; the
  workgroup's enforced location overrode the request's `not-enforced/`, the override 5.4 asks about;
  0 bytes scanned, a `count(*)` Athena can answer from the Iceberg table's metadata, so the scan limit
  was not approached. A read-back of the query as `awsds-infra-prod` found no SSO token for the `awsds`
  session after the persona's sign-in (*"Error loading SSO Token: Token for awsds does not exist"*); it was
  not retried, the pasted output being the measurement.

## 2026-10-24 — 5.4's query read back from the account and its trail

*Claude's hand, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), reads only,
after the user signed the `awsds` session in again. Times UTC.*

- **[Claude] The query** `d78c3939-168a-4c28-8313-246620114d06`, read at 03:31:52: workgroup
  `awsds-prod-athena`, database `curated`, `SUCCEEDED`, submitted 03:21:58.720 and completed 03:22:01.049
  (2,329 ms), Athena engine version 3, 0 bytes scanned, the result at
  `s3://awsds-prod-derived/results/d78c3939-168a-4c28-8313-246620114d06.csv` under `SSE_KMS`.
- **[Claude] Production's trail**: `StartQueryExecution` at 03:21:58 in a `DataScientistProdAccess`
  session, from a public address (the laptop off the VPN, D39), naming the workgroup and returning that
  id; then the vend pair at 03:21:59, `lakeformation:GetDataAccess` in the same session invoked by
  `glue.amazonaws.com` and by `athena.amazonaws.com`, both answered. The persona's read of the governed
  table is attributed by its own session, not by the profile's name.

## 2026-10-24 — decision 14 taken by the user, as recommended: Data Governance

*The user's hand, in chat; Claude recording.*

- **[user]** *"Aceito as duas recomendações: Stage 9 decisão 14 como (a), Data Governance registra e
  concede o datashare; e 6d decisão 11, manter o endpoint lakeformation do Sandbox. Registre as
  decisões."*
- **[Claude] What it fixes**: 9.5's `<LF>` is Data Governance. Production grants the datashare `VIA DATA
  CATALOG` to it and authorizes `DataCatalog/<Data Governance>`; the lake's administrator associates,
  registers, creates the federated database and grants Sandbox, with the lake's own LF-Tags; Sandbox's
  administrator grants the project's role. The Lake Formation grants keep one grantor, so the step's
  callout, 9.8, the risk on the register, D40's compensation paragraph and `GOVERNANCE.md` no longer
  speak of a second grantor account; the `GRANT`s inside `governed` stay Production's, in the register's
  Redshift half. The registration is permanent under `DenyLakeDeletionAndDeregistration`. The waiting
  list's row leaves; 6d decision due 11 is that stage's log.

## 2026-10-24 — the sixth sitting with the environment down: the quotas raised, 9.4 written, decision 15

*Claude's hand, in the session `planejamento-estagios-8-9-10-847863` (the branch
`claude/planejamento-estagios-8-9-10-847863`, cut from `main` at PR #252's merge and fast-forwarded to
PR #253's at the user's word), on the user's request. AWS read as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`), reads and
plans only, the tunnel down; the one other session on the machine, the runbooks review (PR #253), was
told which stage-file forms this session takes. Nothing applied. Times UTC.*

- **[user] The request**: *"Planeje as próximas atividades para concluirmos os estágios 8, 9 e 10.
  Antecipe todas as etapas que podem ser feitas neste momento sem o ambiente no ar. Em seguida, planeje
  a execução destas etapas e me avise para subir o ambiente e prosseguirmos com a implementação do
  plano."* Later in the sitting: *"Peço sincronizar o repositório em relação à main. houve revisão dos
  runbooks."*
- **[Claude] 3.5's quotas**, 03:47 to 03:48: the four `ml.m5.large` requests still read `CASE_OPENED`,
  last updated 2026-10-23 between 20:03 and 21:00, and the applied values `list-service-quotas` returns
  are no longer 0. In Production and Staging alike: training 20 for `ml.m5.large`, `ml.m5.xlarge`,
  `ml.c5.xlarge` and `ml.m5.2xlarge`, 1 for `ml.t3.large` and `ml.t3.xlarge`; transform 8, 4, 8 and 2 for
  the first four; processing 8 for `ml.m5.large`, `ml.m5.xlarge` and `ml.c5.xlarge`, 4 for
  `ml.m5.2xlarge`, 10 for `ml.t3.medium` (4 before) and `ml.t3.large`, 5 for `ml.t3.xlarge`. Sandbox
  reads the same values. `get-aws-default-service-quota` still reads 0.0 for `L-611FA074`, so these are
  the two accounts' applied quotas, raised past the requests' 2. Stage 10's pass 3 waits on no quota.
- **[user] Decision 15**, the warehouse load's trigger, answered in the session's question: *"Workflow
  só de Produção"*, against the recommendation of a manual job in the Production leg. The load is a
  task of its own workflow with its own chain, Production's alone, and fails whenever the compute is
  down.
- **[Claude] 9.4 written** in the template (`examples/app-etl/`) and its slices: `warehouse/trades.sql`
  (`CREATE TABLE IF NOT EXISTS trades.trades_notional`, the deployer's user its owner); the pipeline's
  manual job `production-warehouse-ddl` (the Data API as `awsds-deploy-prod`, a read every 5 s, cancelled
  past 300 s and read back, verifications xxii and xxvii); `glue/load_warehouse.py` (`GetCredentials` and
  `GetWorkgroup`, then JDBC on the workgroup's port as `IAMR:awsds-prod-job-exec`, delete and insert in
  one transaction, the count read back); the job `awsds-prod-app-etl-load`, Production's alone in the
  shared application slice; the workflow `app-etl-warehouse` and its chain at `cron(30 7 * * ? *)`; the
  job role's `ConnectToTheGovernedWarehouse`. AWS's JDBC page names `redshift-jdbc42-2.1.0.29` for Glue
  5.0 and 5.1 and says Glue provides the drivers to its Spark jobs; Glue 6.0's row is not in its table,
  so the first run reads whether the driver loads.
- **[Claude] 8.5's half**: the template's Glue job reads `curated.trades` through the share when the
  application slice gives it `--SOURCE_TABLE` (2.4's catalog settings), writes
  `app_outputs.trades_notional` and reads it back against the rows read; `staging-test` reads the table
  by `get-table` as the deploy role. A planted drift, `GOVERNED_COLUMNS` naming a column `curated.trades`
  lacks, fails Staging's leg and passes `test` (verification xiii, Stage 8's ix).
- **[Claude] The plans**, 17:17 to 17:21, each outside the repository: `production/data/` and
  `staging/data/` *"Plan: 0 to add, 1 to change, 0 to destroy."*, the outputs bucket's policy with
  `models/` among the deploy role's prefixes, and four outputs (`lake_catalog_id`, `curated_database`,
  `curated_table`, `curated_bucket_name`); `production/sagemaker/` the same counts, the job role's inline
  policy, and `training_image_uri`; `staging/sagemaker/` the output alone. The applies wait for the user.
- **[Claude] What the Staging leg of v0.4.0 depends on**: Staging's `AllowFullTableExternalDataAccess`
  is unset, and whether an engine's flag is needed beside the lake's is verification xxviii's third
  clause. The third producer run, Production's flag off, comes before that leg; if it is refused, the
  user turns Staging's flag on in its console as Production's was.

## 2026-10-24 — v0.4.0's data and sagemaker slices applied, read before and after

*Claude's hand, on the user's authorization in chat (*"Autorizo os seis applies do §0.6 (production/data,
staging/data, production/sagemaker, staging/sagemaker, production/foundation, staging/foundation) como
usuário de infraestrutura com InfrastructureAccess, cada um de um plano fresco, com o var-file de alertas
nos foundation, e as leituras depois."*), as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`, `awsds-infra-staging`, the identity read at 17:48:39); Recipe A, each plan outside
the repository, from the branch at `be2fdf17`. The six other sessions on the machine, all idle, were told
before the first write; one answered that PR #248's changes, live in four of the slices, must be in the
tree, which the plans confirmed by showing only this branch's additions. Times UTC.*

- **[Claude] Before**, 17:49:09: `./aws/deploytargets.py` on the five infrastructure profiles, all checks
  passed; `DT-5` reads `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`, the create-defaults emptied and one
  administrator in Data Governance, Production and Staging.
- **[Claude] `production/data/`**: the fresh plan at 17:51:01, *"Plan: 0 to add, 1 to change, 0 to
  destroy."*, the outputs bucket's policy; applied 17:51:16, *"Modifications complete after 1s
  [id=awsds-prod-outputs]"*, *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*, the four
  outputs written; re-planned `No changes` at 17:51:26.
- **[Claude] `staging/data/`**: plan 17:51:46, the same counts; applied 17:52:02 on
  `awsds-staging-outputs`, *"0 added, 1 changed, 0 destroyed"*; re-planned `No changes` at 17:52:11.
- **[Claude] `production/sagemaker/`**: plan 17:52:51, *"Plan: 0 to add, 1 to change, 0 to destroy."*, the
  job role's inline policy; applied 17:53:04, *"Modifications complete after 1s
  [id=awsds-prod-job-exec:job]"*; re-planned `No changes` at 17:53:13; the output `training_image_uri`
  names `sagemaker-xgboost@sha256:0b5d9341…3a78`.
- **[Claude] `staging/sagemaker/`**: plan 17:53:30, the output alone; applied 17:53:41, *"Apply complete!
  Resources: 0 added, 0 changed, 0 destroyed."*; re-planned `No changes` at 17:53:49.
- **[Claude] After**, 17:56:04: `./aws/deploytargets.py` on the five profiles, all checks passed, `DT-5`
  as before; `./scripts/check-copies.py` OK. `production/data/`'s outputs read back: `curated_database`
  `curated`, `curated_table` `trades`, `curated_bucket_name` `awsds-data-curated`, `lake_catalog_id` the
  lake account's. The simulator, `aws:RequestedRegion` in the context: `redshift-serverless:GetCredentials`
  and `GetWorkgroup` on a `workgroup/…` ARN `allowed` for `awsds-prod-job-exec`, matched by its inline
  `job` policy.

## 2026-10-24 — the first promotion's Production run: the job role's jobs in `VPC-Workloads`

*Claude's hand, as the infrastructure user with `InfrastructureAccess` (the run is Stage 10's, its entry of
this date). Times UTC.*

- **[Claude]** The release's Glue job `awsds-prod-app-etl`, declared by `production/app/app-etl/` at
  `v0.3.3`, ran as `awsds-prod-job-exec` on the `[P]` connection `awsds-prod-jobs` (decision 12):
  `jr_56c29738…e022`, `SUCCEEDED` from 21:42:08 to 21:44:01, 93 s. The processing job
  `app-etl-20261024T214447` ran as the same role on `ml.t3.medium` with network isolation, inter-container
  encryption and two subnets (decision 9's settings, submitted by the workflow's execution role), on the
  release's image `awsds-prod-ecr-app-etl@sha256:89d0ea21…2aac`, `Completed` from 21:45:36 to 21:50:11.
  The job role wrote `app-etl/work/` and `app-etl/outbox/` of `awsds-prod-outputs` (four objects,
  21:43:51 to 21:54:12) and touched no lake prefix: v0.3.3 reads the inbox, and the governed read is
  v0.4.0's (8.5).

## 2026-10-24 — 2.4's third producer run, Production's flag off: the commit needs the owner's flag alone

*The user's hand for the two console acts; Claude's for the readings and the run, on the user's
authorization in chat (*"Autorizo a execução --MODE producer do job awsds-prod-producer-proof agora, como
usuário de infraestrutura com InfrastructureAccess em Production (awsds-infra-prod), e as leituras dos
resultados."*), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), in the session
of `runbooks/promotion.md` §V (the branch `claude/eloquent-ishizaka-04f598`); §V step 1, the hub and
`production/workloads-egress/` up. The seven other sessions on the machine were told before the run.
Times UTC.*

- **[Claude] Before**, 22:14:40: `get-data-lake-settings` reads `AllowFullTableExternalDataAccess` `true`,
  one administrator, both create-default lists empty, `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`;
  `./aws/deploytargets.py awsds-infra-prod` all checks passed (`DT-5`).
- **[user]** *"Desliguei a flag de full-table access de Production no console do Lake Formation
  (us-west-2)."* The trail holds the console's `PutDataLakeSettings` at 22:23:32. **[Claude] read back** at
  22:23:53: the flag absent from the settings, which the console removes rather than writing `false`, the
  rest as before; `DT-5` passing.
- **[Claude] The run**: `start-job-run` at 22:24:58, run
  `jr_39e590285fd3b47097708bb1a6c133c1e3080fde2415a21c9b36002ef264064d`, **`SUCCEEDED`** at 22:27:01 after
  102 s of execution, 204 DPU-seconds. The script's lines: *"running as
  …awsds-prod-job-exec/GlueJobRunnerSession, mode producer"* 22:26:07; *"inserting 10 sample rows into
  lake.curated.trades"* 22:26:22; *"the insert committed"* 22:26:46; *"lake.curated.trades holds 30 row(s)
  through the share"* 22:26:48; the direct put refused by the lake's data key, *"not authorized to perform:
  kms:GenerateDataKey on this resource because the resource does not exist in this Region, no
  resource-based policies allow access, or a resource-based policy explicitly denies access"*, 22:26:50, as
  on 2026-10-23; *"done"*.
- **[Claude] Production's trail**: eight `GetDataAccess` on the lake's `table/curated/trades` between
  22:26:27 and 22:26:49, in pairs, one from the driver's SDK and one invoked by `glue.amazonaws.com`, every
  one answered, each carrying a `sharedEventID`, all through `vpce-05f87e3d8b6ce302d`, the `lakeformation`
  endpoint `workloads-egress/` raised at 18:58.
- **[user]** *"Religuei a flag de full-table access de Production no console do Lake Formation
  (us-west-2)."* **[Claude] read back** at 22:29:42: the flag `true`, the rest as before, `DT-5` passing.
- **Verification xxviii's third clause**: with the lake's flag on and Production's off, the write
  commits, so the engine account's flag is not needed. Staging's leg reads through the lake's flag alone,
  and Staging's stays unset. Production's flag is back on, as decision 13 (a) left it; whether it stays is
  the user's to decide against `TM-26`. `curated.trades` holds 30 rows.

## 2026-10-25 — §V step 8: the DDL, the load (9.6, xxv), two grants found missing, 9.5's first three steps

*The user's hand for `make up ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift` and
the pipeline's manual job; Claude's for the readings, the applies, the chain's runs and the datashare's
commands, on the user's authorizations in chat (*"Autorizo o apply de production/foundation (plano salvo,
0/1/0) como awsds-infra-prod, a chain awsds-prod-chain-app-etl-warehouse e os passos 1 a 3 do 9.5 (SQL do
datashare em Production, authorize-data-share e o lado de Data Governance)."* and *"Autorizo o apply de
production/warehouse (plano salvo, 1 to add: o egress 5439 do awsds-prod-jobs para o awsds-prod-warehouse)
como awsds-infra-prod e rodar de novo a chain awsds-prod-chain-app-etl-warehouse."*), as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-data`,
`awsds-infra-sandbox-1`); the planning session told before each apply. Times UTC.*

- **[user] The compute**: the `redshift-serverless` endpoint `available` at 01:37:44, the workgroup
  `awsds-prod-warehouse` created at 01:38:36 and `AVAILABLE` at 01:40:41, base 4 and max 8 RPU, not public,
  the usage limit 10 RPU-hours monthly `deactivate`.
- **[user] `production-warehouse-ddl`** (pipeline #80, job 449), about 01:42: **[Claude]** the trail holds
  `ExecuteStatement` at 01:42:23 as `awsds-deploy-prod`, no error, and `DescribeStatement` at 01:42:30 in the
  same role session, `AccessDenied`; the job stopped on *"is not authorized to perform:
  redshift-data:DescribeStatement because no identity-based policy allows the redshift-data:DescribeStatement
  action"*, exit 254. The statement had run: `./aws/warehouse.py awsds-infra-prod --sql` read `WH-14`
  *"1 relation(s), each reachable by a role through a grant or a default privilege"*. The Data API
  authorizes `DescribeStatement`, `GetStatementResult` and `CancelStatement` on no resource, so the grant
  under `workgroup/*` matched nothing.
- **[Claude] The deploy role's fix**: `FollowItsOwnStatements` in `production/foundation/deploy-anchors.tf`,
  the three actions on `"*"` with `redshift-data:statement-owner-iam-userid` equal to `aws:userid`; planned
  at 01:46:09 with the alerts var-file, *"Plan: 0 to add, 1 to change, 0 to destroy."*, the inline policies
  at about 3,803 of 10,240 characters after; applied at 01:47:41, *"Modifications complete after 1s
  [id=awsds-deploy-prod:apply-application]"*; re-planned `No changes`. The simulator, with
  `aws:RequestedRegion` in the context, reads the three `allowed` on the role's own statement and
  `implicitDeny` on another owner's; without that key it reads every action `explicitDeny`, the Region
  ceiling's SCP, even `ExecuteStatement` and `sagemaker:DescribeModelPackage`, which work.
- **[Claude] The warehouse chain, first run**, `v0-4-2-by-hand-2026-10-25-app-etl-warehouse`, 01:49:52 to
  01:54:55, `FAILED`: the load job `jr_190a5fd2…0337` (01:50:40 to 01:52:37) *"read 30 row(s) from
  s3://awsds-prod-outputs/app-etl/tables/trades_notional/"*, *"connecting to
  jdbc:redshift://awsds-prod-warehouse.<Production>.us-west-2.redshift-serverless.amazonaws.com:5439/governed as
  IAMR:awsds-prod-job-exec"*, then *"java.net.SocketTimeoutException: Connect timed out"*. The name resolved;
  the job group `awsds-prod-jobs` (`sg-0b8b0b803f6fed9cc`) held egress to the interface endpoints, the S3
  prefix list and itself, and none to the warehouse's group `sg-0f018ef6c4848a9a3`, whose ingress from it
  9.1 had written. The workgroup's ENIs `10.32.85.148` and `10.32.42.6`, in the connection's subnet among
  them.
- **[Claude] The egress fix**: `jobs_to_warehouse_5439` in `production/warehouse/security-group.tf`,
  planned at 01:57:14, *"Plan: 1 to add"*; applied at 01:59:33, *"Creation complete after 2s
  [id=sgr-0c9aea27065a1d2b0]"*; re-planned `No changes`.
- **[Claude] 9.6, the second run**, `v0-4-2-by-hand-2026-10-25-app-etl-warehouse-2`, 01:59:59 to 02:05:12,
  `SUCCEEDED`: the load job `jr_453d7bb9…2870` (02:00:53 to 02:03:15) *"trades.trades_notional: 0 row(s)
  deleted, 30 inserted, 30 counted for the load's dates, as IAMR:awsds-prod-job-exec"*. **Verification xxv**,
  read at 02:05:55 through the Data API as the admin: `pg_user` holds `IAMR:awsds-prod-job-exec` and
  `IAMR:awsds-deploy-prod`, neither a superuser, beside `dbadmin`, `rdsdb`, `gov_trades_owner` and the
  infrastructure user's `IAMR:` user; `trades.trades_notional`'s owner is `IAMR:awsds-deploy-prod`, and it
  holds 30 rows dated 2026-10-01 to 2026-10-05, written by the job role.
- **[Claude] 9.5's step 1**, in `governed` as the admin, 01:51:05 to 01:51:22, each `FINISHED`: `CREATE
  DATASHARE trades_lf`, `ALTER DATASHARE trades_lf ADD SCHEMA trades`, `ADD ALL TABLES IN SCHEMA trades`,
  `SET INCLUDENEW = TRUE FOR SCHEMA trades`, `GRANT USAGE ON DATASHARE trades_lf TO ACCOUNT '<Data
  Governance>' VIA DATA CATALOG`; `svv_datashare_objects` the schema `trades` and the table
  `trades.trades_notional`, `svv_datashare_consumers` `DC:<Data Governance>`.
- **[Claude] Step 2**, as `awsds-infra-prod`: `authorize-data-share` for `DataCatalog/<Data Governance>`,
  `AUTHORIZED` at 01:52:05, `ProducerAllowedWrites` false, no publicly accessible consumer.
- **[Claude] Step 3**, as `awsds-infra-data`: the share `AVAILABLE` to the consumer; `associate-data-share-consumer`
  on the lake's catalog `ACTIVE` at 01:52:29; `register-resource` on the datashare's ARN at 01:52:38, no role,
  `HybridAccessEnabled` and `WithPrivilegedAccess` false, `NOT_VERIFIED`; the create-defaults read empty
  first. `glue create-database` with a description was refused, *"Description and federation source cannot
  exist together in a database!"*; without it `governed_trades` was created at 01:53:16, its
  `FederatedDatabase` the datashare's ARN on `aws:redshift`, `CreateTableDefaultPermissions` `[]`, its only
  permission the creator's (`InfrastructureAccess`, `ALL` with grant option), none to
  `IAM_ALLOWED_PRINCIPALS`; its table `trades.trades_notional`. LF-Tags at 01:54:06, `layer=curated` on the
  database and `classification=internal` on the table, no failure.
- **[Claude] The tag grant reaches the federated database**: Sandbox's account holds the lake's TBAC grants
  (`DESCRIBE` on databases with `layer` in `curated`, `raw`; `DESCRIBE` and `SELECT` on tables with
  `classification` in `internal`, `public` and `layer` in `curated`, `raw`, both grantable), and from Sandbox
  `glue get-database` and `get-table` on `<Data Governance>`'s catalog answered for `governed_trades` and
  `trades.trades_notional` (six columns, `notional` among them), with no RAM invitation pending: no named
  grant was needed for the account. In Sandbox the tag re-grants name the Data Scientist User's set, not a
  project role, so step 4's grant to the project role is still owed, with steps 5 and 9.7.

## 2026-10-25 — 9.5's steps 4 and 5 in Sandbox: the project role's grant, the consumer database; the administrator reads it

*Claude's hand, on the user's authorization in chat (*"Autorizo os applies dos planos salvos de
production/foundation (0/3/0, awsds-infra-prod) e staging/foundation (0/3/1, awsds-infra-staging) e os
passos 4 e 5 do 9.5 no Sandbox (awsds-infra-sandbox-1)."*), as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-sandbox-1`, Sandbox's Lake Formation administrator), in the session's
second branch (`claude/eloquent-ishizaka-04f598-2`, cut from `main` after PRs #255 and #256); the user raised
`sandbox/warehouse-compute/` (the workgroup `AVAILABLE`, created 02:11:54). Times UTC.*

- **[Claude] Step 4**, at 02:37:27 and 02:37:28: `grant-permissions` to
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` (`eighth-experimentation`, the project the warehouse
  admits), `DESCRIBE` on `<Data Governance>`'s `governed_trades` and `SELECT`, `DESCRIBE` on its table
  `trades.trades_notional`, by name, so the project reaches this table alone and not every `curated` /
  `internal` table the account's tag grant covers. Read back: `DESCRIBE` on the database and the table and
  `SELECT` as `TableWithColumns` with the column wildcard, which a `list-permissions` filtered by principal and
  `Table` resource does not return.
- **[Claude] Step 5**, the Data API as the namespace's admin in `warehouse`: `CREATE DATABASE governed_trades
  FROM ARN 'arn:aws:glue:us-west-2:<Data Governance>:database/governed_trades' WITH DATA CATALOG SCHEMA
  governed_trades` `FINISHED` at 02:38:48, and `GRANT USAGE ON DATABASE governed_trades TO
  "IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"` at 02:38:52, the user in `pg_user` since 6h.
  `svv_redshift_databases` reads it `shared via data catalog`, `{"datacatalog_schema":"governed_trades"}`.
- **[Claude] What the pages left open, read**: as `dbadmin`, a password user, `svv_all_tables` lists nothing in
  `governed_trades` and a `SELECT` is refused, *"ERROR: Current user is not authenticated with IAM
  credentials."*: a share registered with Lake Formation is read by an IAM-derived user alone. Through the Data
  API with IAM authentication, as `IAMR:AWSReservedSSO_InfrastructureAccess_59e5b26af457128d`, the table is
  `governed_trades.trades.trades_notional`, an `EXTERNAL TABLE` under the producer's schema name `trades`, not
  the Glue database's; and `SELECT count(*)` read **30**, at 02:40, with no grant to that role: the account's
  Lake Formation administrator reads under the grant the account holds from the lake, as it reads the lake's
  `curated` tables. The project role's read is 9.7's, the user's.
- **[Claude] 9.6's namespace half**: `awsds-prod-warehouse-exec` holds no inline and no attached policy (read
  02:41), so the namespace role reaches no lake prefix (9.2).

## 2026-10-25 — 9.7: a Sandbox project reads the governed table, after three grants the pages did not name

*The user's hand for the queries, from the project `eighth-experimentation`'s Query editor in the portal;
Claude's for the grants and the applies, on the user's authorizations in chat (*"Autorizo, como
awsds-infra-sandbox-1: o apply de sandbox/data (só a saída lake_catalog_id), o apply de sandbox/warehouse se
o plano mostrar só a política do papel de acesso, e o grant DESCRIBE/SELECT em governed_trades ao
awsds-sandbox-warehouse-access-avhvbqn37ty7m8."* and *"Autorizo, como awsds-infra-sandbox-1 pela Data API com
o segredo do admin: GRANT TEMP ON DATABASE sandbox TO "IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"."*),
as the infrastructure user with `InfrastructureAccess` (`awsds-infra-sandbox-1`); the planning session told
before the writes. In the user's pasted output the account id is replaced by `<Sandbox Account 1>`. Times
UTC.*

- **[user] The first attempt**, refused: *"ERROR: AwsClientException: AccessDeniedException from glue - User:
  arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-warehouse-access-avhvbqn37ty7m8/28f1b390-…@5hkjdsy3umpi1c
  is not authorized to perform: glue:GetTable on resource: ar…"*. **The principal the consumer evaluates is
  the session's**, the project's access role, which the portal's connection assumes; the database user
  `IAMR:datazone_usr_role_…` is a name the access role's `RedshiftDbUser` tag gives, and neither Glue nor
  Lake Formation sees that role. Step 4's grant to the project role is unused by this door.
- **[Claude] The access role's two layers**: `sandbox/data/` gained the output `lake_catalog_id` (planned
  05:56:20, *"Changes to Outputs: + lake_catalog_id"*, applied 05:57:35, *"0 added, 0 changed, 0 destroyed"*,
  re-planned `No changes`); `sandbox/warehouse/` gained `ReadTheGovernedShareCatalog` on the access role's
  portal policy, `glue:GetDatabase`, `GetDatabases`, `GetTable` and `GetTables` on the lake's catalog,
  `database/governed_trades` and `table/governed_trades/*` (planned 05:58:05, *"Plan: 0 to add, 1 to change, 0
  to destroy."*, `aws_iam_policy.project_access_portal["avhvbqn37ty7m8"]` alone; applied 05:58:34; re-planned
  `No changes`); Lake Formation at 05:59:03, `DESCRIBE` on `governed_trades` and `SELECT`, `DESCRIBE` on its
  table to `awsds-sandbox-warehouse-access-avhvbqn37ty7m8`, read back beside step 4's grant to the project role.
- **[user] The second attempt**, refused by Redshift: *"ERROR: Failed to incorporate external table
  "trades"."trades_notional" into local catalog. Error=permission denied to create temporary tables in database
  "sandbox""*. The share's table is an external table, and the session's database holds the temporary objects a
  query on one needs; 5b and 6h revoked every database privilege from `PUBLIC`, `TEMP` with it.
- **[Claude] The third layer**: in `sandbox` as the admin, `GRANT TEMP ON DATABASE sandbox TO
  "IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"` at 06:04:42, the ACL from `{dbadmin=CTA/dbadmin}` to
  `{dbadmin=CTA/dbadmin,"IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"=T/dbadmin}`.
- **[user] The third attempt**, `SELECT current_user, count(*), min(trade_date), max(trade_date) FROM
  governed_trades.trades.trades_notional;`: *"current_user = IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c,
  count = 30, min 2026-10-01, max = 2026-10-05"*. **INT-24 holds**: a Sandbox project reads a governed table
  of Production's warehouse through Lake Formation, the lake's tag grant reaching the federated database,
  with no network path between the accounts. The door needs, per project, the access role's catalog read
  (IAM), its Lake Formation grant, `USAGE` on the consumer database and `TEMP` on the session's database.

## 2026-10-25 — 9.7 with Production's workgroup gone: the share still reads

*The user's hand for `make down ENV=production ONLY=warehouse-compute` and the query; Claude's for the
readings, as the infrastructure user with `InfrastructureAccess`. Times UTC.*

- **[user]** `make down ENV=production ONLY=warehouse-compute`; **[Claude] read back** at 06:13:30: no workgroup
  in Production, `DeleteWorkgroup` in its trail from 06:11:56 to 06:12:01, the namespace `awsds-prod-warehouse`
  `AVAILABLE`; Sandbox's workgroup `AVAILABLE`.
- **[user]** The same query from `eighth-experimentation` ran successfully with the producer's workgroup gone.
  9.5's open measurement is answered: a Serverless producer with no workgroup keeps serving a Lake
  Formation-managed datashare from its namespace, so a Sandbox read costs Sandbox's compute alone, never both
  workgroups at once.

## 2026-10-25 — Staging's `make down` refused the application table's delete; the infrastructure user's grant on `app_outputs`

*The user's hand for `make down ENV=staging` and the grant that unblocked it; the forked session's for the
reading of Staging after the down; Claude's for the trail's reading and the code, as the infrastructure user
with `InfrastructureAccess` (`awsds-infra-staging`, `awsds-infra-prod`). Times UTC.*

- **[user] `make down ENV=staging`**, as the infrastructure user: the application slice's Glue job destroyed,
  the table refused, *"AccessDeniedException: Insufficient Lake Formation permission(s): Required Drop on
  trades_notional"* (the forked session's quote of the output). **[Claude] Staging's trail**: `DeleteTable` on
  `app_outputs.trades_notional` refused at 06:30:24 and 06:31:52, Terraform 1.15.8, the trail reading
  `AccessDenied`, *"An unknown error occurred"*. The table's creator was `awsds-deploy-staging`, through
  pipeline #87's `staging-deploy`, and Lake Formation gives a table's creator its permissions and no one else:
  the account's administrator, who created `app_outputs`, holds no `DROP` on a table another principal created
  in it.
- **[user] The unblock**, `aws lakeformation grant-permissions` from the CLI at 06:34:37: `DROP` on
  `app_outputs.trades_notional`, by name, to `InfrastructureAccess`; `DeleteTable` passed at 06:36:00 and the
  down completed. **[forked session]** Staging read at zero at about 06:47: `./aws/egress.py awsds-infra-staging`
  0 interface endpoints, 0 NAT, 0.000 USD/h; no workflow; the Glue job and the table gone. **[Claude] read at
  06:49**: `app_outputs` holds no table, and the grants on its tables list the job role, the persona and the
  deploy role; the by-name grant left with its table.
- **[Claude] The fix**, at the forked session's request on the user's behalf: since Stage 8's decision 27 the
  pipeline applies an application slice and the user destroys it, so every release's table meets this refusal
  at the next down. `infrastructure_app_outputs_tables` in `staging/data/` and `production/data/` gives
  `InfrastructureAccess` the deploy role's catalog operations on every table of `app_outputs`, `ALTER`, `DROP`
  and `DESCRIBE`, no data permission; planned at 06:44 in each slice, *"Plan: 1 to add, 0 to change, 0 to
  destroy."*, the plans saved, the applies waiting for the user's authorization.

## 2026-10-25 — `infrastructure_app_outputs_tables` applied in both data slices

*Claude's hand, on the user's authorization in chat (*"Autorizo os applies dos planos salvos de staging/data
(1 to add, awsds-infra-staging) e production/data (1 to add, awsds-infra-prod), como usuário de infraestrutura
com InfrastructureAccess."*), as the infrastructure user with `InfrastructureAccess`; the forked session told
before the writes. Times UTC.*

- **[Claude] The applies** of the saved plans: `staging/data/` at 06:52:58 and `production/data/` at 06:53:17,
  each *"Apply complete! Resources: 1 added, 0 changed, 0 destroyed."*; both re-planned `No changes`.
- **[Claude] Read back** at 06:54 with `list-permissions` on every table of `app_outputs`: in each account
  `InfrastructureAccess` holds `ALTER`, `DESCRIBE`, `DROP`, beside the deploy role's same three, the job role's
  `ALTER`, `DELETE`, `DESCRIBE`, `INSERT`, `SELECT` and the persona's `DESCRIBE`, `SELECT`. The next
  `make down ENV=staging` after a release is the grant's measurement.

## 2026-10-25 — the warehouse instrument after the downs

*Claude's hand, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-sandbox-1`, `awsds-infra-prod`).
Times UTC.*

- **[Claude] `./aws/warehouse.py`** at 07:15: in each account `WH-8` *"1 namespace(s), 0 workgroup(s), all
  expected"*, and `WH-4`, `WH-4b`, `WH-5`, `WH-7` and `WH-1b` pass; run without `--sql`, since both workgroups
  are gone, so the database readings (`WH-6`, `WH-12`, `WH-14`) and `EXC-13`'s password wait for the next
  warehouse sitting. `WH-9` reads the Sandbox connection's `lineageSync` `ENABLED` on `cron(43 3 * * ? *)`, 15
  runs, none completed (`EXC-17`).
