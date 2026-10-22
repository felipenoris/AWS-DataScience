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
