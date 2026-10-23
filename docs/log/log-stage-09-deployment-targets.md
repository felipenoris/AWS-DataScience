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
