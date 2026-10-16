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
