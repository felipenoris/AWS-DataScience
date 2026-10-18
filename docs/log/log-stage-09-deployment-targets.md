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
