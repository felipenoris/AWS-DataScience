# SCPs — every statement in `policies/`, and what it is for

**The index of the `SERVICE_CONTROL_POLICY` documents in [`policies/`](policies/).** One section per file,
one row per `Sid`: what it denies, why the statement exists, and what it actually does once attached.
The documents themselves carry no comments — JSON has none — so this file is where their reasoning lives.

> ## Review this file at every SCP change — in the same sitting
>
> **A statement added, removed, renamed or re-conditioned in `policies/` is a change to this file**, and so
> is attaching a document to a new target or detaching it. The check is mechanical: **the rows in a section
> must be the `Sid`s in that file, in the same order, and nothing else.** It compares both sides and prints
> `OK` per document — a version that only listed the `Sid`s would leave the comparison to a reader who
> already believes the file is right. It needs no AWS session and changes nothing:
>
> ```bash
> ./terraform-live/identity/org-policies/check-index.sh
> ```
>
> It names both directions of the failure, and the second is the one that is easy to miss: a statement in
> the policy with no row here is a control nobody can explain a year from now, and a row here with no
> statement — which is what a **renamed** `Sid` leaves behind — describes a control that is not attached.
> **What it cannot check is whether a row's text is still *true*.** Nothing can; that is the reading this
> file asks for, and the script exists so that the reading is spent on the part that needs judgement.
>
> A statement whose reasoning is only in the sitting that wrote it is a statement the next reader either
> deletes or works around. **What is *not* here**: policy ids and attachment dates — those are in
> [`log/stage-01c-preventive-policies.md`](../../../log/stage-01c-preventive-policies.md), recorded as each
> document is attached, and duplicating them here would produce a second, staler answer.

**Scope:** SCPs only. The RCP, tag and declarative documents of
[step 7.8](../../../plan/stages/stage-01c-preventive-policies.md) are different policy *types* with
different evaluation rules and are not indexed here — except the **tag-forcing SCP**, which is an SCP and
gets a section of its own when decision 5 settles. The throwaway documents in [`canary/`](canary/) are
never attached to anything real and are described in [`README.md`](README.md).

**Reading the whole ceiling:** every account is governed by the root documents **plus** its OU's, and denies
only ever compose. A call that fails may be failing on a statement in a different file — the CloudTrail
`errorMessage` names the policy id, which is the only reliable way to tell them apart.

---

## `awsds-org-scp-baseline.json` → organization **root**

The statements that must reach every account, including the ones that do not exist yet.

| `Sid` | Effect |
|---|---|
| `DenyLeaveOrganization` | Denies `organizations:LeaveOrganization`. Every vended account carries `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins` (measured, `AWS_STATE.md` A.1), so this is one of the few Organizations calls a *member* account can really make — and one call drops every SCP and every Control Tower control for that account at once. **Effect:** no principal in any governed account can detach it from the organization. **Deliberately never probed:** its "allowed" outcome *is* the damage |
| `DenyIamUserCreation` | Denies `iam:CreateUser` and `iam:CreateAccessKey`. Principle 2 — *no IAM Users, no long-lived keys* — is otherwise a convention with nothing enforcing it. **Effect:** humans and machines can only obtain credentials by assuming a role. Break-glass (D16) is untouched: the Management account is exempt from SCPs by AWS's design |
| `DenyAccountBpaChangeExceptInfrastructure` | Denies `s3:PutAccountPublicAccessBlock` unless the principal ARN matches the `InfrastructureAccess` Identity Center role. **One action covers both directions** — the `DeletePublicAccessBlock` API is governed by the `Put` permission, so a `Delete…` action string would be a statement that silently does nothing. Protects the account-level Block Public Access set in step 7.4. **The carve-out is decision 7 and is the single wildcard-account ARN in this design**, because it must reach accounts that do not exist yet and whose role suffix is unknowable; Stage 2 step 9.2's check whitelists this `Sid` by name. **Effect, proven in both directions:** the canary (`AWSAdministratorAccess`) is denied, an `awsds-infra-*` profile still sets it |
| `DenySnapshotAndImageSharing` | Denies `ec2:ModifySnapshotAttribute`, `ec2:ModifyImageAttribute`, `rds:ModifyDBSnapshotAttribute`, `rds:ModifyDBClusterSnapshotAttribute`. **This is an exfiltration route that bypasses every other control here**: a Studio space's volume becomes an outside account's in two API calls with **no network path**, so NAT, the DNS firewall, endpoint policies and the `aws:ResourceOrgID` deny are all irrelevant to it — and no RCP reaches EC2 or RDS. Denied outright rather than conditioned on the destination: nothing in this design shares a snapshot at all. **It is half of the route and the other half is the row below** — this one is *granting someone else access to the image where it sits*; the sibling is *writing the image somewhere else*. **Effect:** the sharing route is closed for every principal, the builder included. The EC2 snapshot action is **attached but unexercised** — an invented snapshot id is rejected before authorization, `--dry-run` included — while its AMI sibling *was* denied; the RDS pair stays untested until an RDS exists |
| `DenyImageAndSnapshotExport` | Denies `ec2:CreateStoreImageTask`, `ec2:ExportImage`, `ec2:CreateInstanceExportTask` and `rds:StartExportTask`. **Added 2026-08-13, by re-reading the row above against AWS's action list rather than against its own claim.** That statement said it closed "the one exfiltration route that bypasses every other control", and it did not: sharing an attribute is one way an image leaves, and **writing it into a bucket is another** — `CreateStoreImageTask` stores an AMI into an S3 bucket that may belong to another account, `ExportImage`/`CreateInstanceExportTask` export a VM image, and `rds:StartExportTask` writes a DB snapshot out as Parquet. Both routes move the *same* bytes and neither needs a network path from the instance. **Why a separate `Sid` and not four more actions in the row above:** they are two different mechanisms, they will be exercised by different probes, and the log already records the original statement under its own name — a renamed `Sid` would make that entry describe something that no longer exists. **Effect:** unconditional, like its sibling; nothing in this design exports an image or a snapshot. **Revision trigger, and it is a plausible one:** exporting an RDS snapshot to S3 as Parquet is a real ingestion pattern, so the first time a relational source has to reach the lake, `rds:StartExportTask` is the action to reconsider — deliberately, with a named principal, not by deleting the statement |
| `DenyEcrPublicEntirely` | Denies `ecr-public:*`. Publishing to ECR Public is the case the perimeter document cannot reach: the repository is *inside* the organization, so `aws:ResourceOrgID` matches correctly and says nothing about the gallery being world-readable. The **whole namespace** rather than the publish actions, so it cannot fall one AWS release behind. **Effect:** no account can create or push to a public repository. **Anonymous pulls from `public.ecr.aws` are unaffected** — they involve no IAM action, so no SCP evaluates. Amendment trigger: an authenticated pull taken for the higher rate limit |
| `DenyGuardDutyTampering` | Denies `guardduty:DeleteDetector`, `UpdateDetector`, `DeleteMembers`, `DisassociateMembers`, `StopMonitoringMembers`, `DisassociateFromMasterAccount`, `DisassociateFromAdministratorAccount`, `DeletePublishingDestination` and `UpdatePublishingDestination`. Measured gap: **no Control Tower guardrail covers GuardDuty**, while Config already is covered (which is why no Config statement is written here). **Five of those nine were added 2026-08-13 and the reason is worth keeping: the statement had been written against the API's old vocabulary.** GuardDuty renamed master→administrator and **both spellings still exist as actions** — denying only `DisassociateFromMasterAccount` left the modern call open, which is a statement that reads as protection and is not (verified against the machine-readable list, where both names appear). `DisassociateMembers`/`StopMonitoringMembers` are the current member-detach pair, and the publishing-destination pair kills or redirects the export of findings without touching a detector at all. **Effect:** inert until Stage 4 turns GuardDuty on — and that is the correct order under principle 9, not an oversight. The battery probe is what says the statement is nonetheless live |
| `DenyDataZoneDomainOutsideDataOu` | Denies `datazone:CreateDomain` unless the principal's org path is the `Data` OU's. D26 says there is **one** unified domain; without this, a second domain anywhere reintroduces a second interactive entry point with its own blueprints and project roles. Three mechanics carry it and each fails toward a deny that never lifts: `aws:PrincipalOrgPaths` is multi-valued, so `ForAllValues:StringNotLike`; `ForAllValues` is vacuously true over an empty set, so `BoolIfExists: aws:PrincipalIsAWSService=false` is required; the path is the **full path with a trailing slash**. **`CreateDomain` alone, never `datazone:*` at the root** — Sandbox and Development need `PutEnvironmentBlueprintConfiguration`. **Effect: attached but unexercised** — DataZone validates the execution role before authorizing, so the probe measures nothing; it is [Stage 6 step 0](../../../plan/stages/stage-06-unified-studio.md), and the untested failure direction is the deny reaching `Data` too |

**Not in this document, and each absence is a decision:** no Config statement (Control Tower's guardrail
already denies the recorder, with the `AWSControlTowerExecution` carve-out that keeps the landing zone able
to update itself) and **no CloudTrail statement** (measured: nothing denies it anywhere — the trail is
organization-level and lives in Management, which is SCP-exempt, so a member-account deny would bind
nothing reachable. Revision trigger: the first trail this project creates in a member account).

**`guardduty:UpdateDetector` collides with [Stage 11 step 4](../../../plan/stages/stage-11-dlp.md), and the
collision is deliberate rather than unnoticed.** The deny is unconditional and this document sits on the
root, so it reaches **Audit** — the GuardDuty administrator — as hard as any member. Org-wide administration
is unaffected, because turning a feature on across the organization goes through
`UpdateOrganizationConfiguration` and `UpdateMemberDetectors`, neither of which is denied; what *is* denied
is changing **Audit's own detector**, which is exactly what enabling S3 Protection and Malware Protection
there will try to do. **The procedure is the same shape as the `s3:DeleteBucket` one in `Data`:** detach
`awsds-org-scp-baseline` from the root, make the change, re-attach, and re-run phases 1-3 of
[`scp-battery.md`](../../../plan/runbooks/scp-battery.md) before the sitting is called done. Carving out a
named administration role instead is the alternative, and it is a decision for Stage 4 — when that role
exists and can be named exactly, the way D27's is. **What is not acceptable is discovering this at the
console on the evening of Stage 11**, which is the only reason it is written here.

## `awsds-org-scp-perimeter.json` → organization **root**

The trusted-**resources** axis of the data perimeter. A separate document because it is the one most likely
to be amended — Stage 6 and Stage 9 both come back to it — and it is detached and re-attached on its own.

| `Sid` | Effect |
|---|---|
| `DenyS3ObjectWriteOutsideOrganization` | Denies the seven S3 object-write actions (`PutObject`, `PutObjectAcl`, `PutObjectTagging`, `PutObjectVersionAcl`, `PutObjectVersionTagging`, `PutObjectRetention`, `PutObjectLegalHold`) when `aws:ResourceOrgID` is not this organization, with `BoolIfExists: aws:PrincipalIsAWSService=false` beside it. **Writes only, deliberately** — a read-side deny of the same shape breaks `docker pull`, package installs and every legitimate read of an AWS-owned bucket. **The action list is enumerated and an action wildcard is forbidden**: `StringNotEqualsIfExists` evaluates **true when the key is absent**, so `s3:Put*` would reach the account-level `s3:PutAccountPublicAccessBlock` and deny, everywhere and for everyone, the exact call step 7.4 depends on. **Effect, proven by the inverted document:** `aws:ResourceOrgID` populates for S3 and the deny reaches an ordinary principal; in-org writes still succeed with it attached |
| `DenyEcrPushOutsideOrganization` | Denies `ecr:InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload` and `PutImage` under the same condition pair. **Four actions, not `PutImage` alone: the layers are the data** — by the time a manifest write is denied, the filesystem contents are already in the outside repository. `ecr:GetAuthorizationToken` is deliberately excluded (registry-scoped, so the key never populates and an `IfExists` deny would catch it unconditionally); authenticating against an outside registry is harmless, the write is the event. **No carve-out**: a pull-through cache writes into *your own* registry, so the deny never evaluates against it, and INT-01's replication is performed by ECR itself under the service carve-out. **Effect, proven separately from S3** — key population is a property of each service's authorization: the inverted probe denied `initiate-layer-upload`, and the real document leaves in-org pushes working |

## `awsds-org-scp-ou-workloads.json` → **`Workloads`** OU

Staging and Production: deployment targets, written by the pipeline, with no human control plane (D17, D20).

| `Sid` | Effect |
|---|---|
| `DenyInteractiveSageMakerSurface` | Denies `sagemaker:CreateDomain`, `CreateUserProfile`, `CreatePresignedDomainUrl`, `CreateSpace`, `CreateApp`, `StartSession`, `CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl`. Turns D17 from an intention into a control: *no interactive surface outside the Interactive OU* cannot be undone by anyone with a console and a good reason. **Enumerated, and `sagemaker:Create*` is forbidden here** — `CreateModel`, `CreateEndpoint`, `CreateEndpointConfig` and `CreateTrainingJob` are exactly what these accounts are for, so a prefix wildcard would deny the stage rather than the route. `CreateSpace`+`CreateApp` are the SMUS notebook (a space *plus* an app), and `StartSession` is the remote-IDE connection, which matches neither `Create*` nor `datazone:*`. **Effect:** a deployment target can serve models and cannot host a human |
| `DenyDataZoneEntirely` | Denies `datazone:*`. D26 says Staging and Production are never associated to the domain, and until this statement nothing enforced it. Three things it closes: a domain created locally, the account associating itself and configuring a blueprint (`PutEnvironmentBlueprintConfiguration` mints provisioning and manage-access roles with broad permissions *even when provisioning then fails*), and the non-ML blueprints, which provision buckets, Glue databases and Athena workgroups without ever passing through `sagemaker:*`. **The whole namespace on purpose**: this plan already paid for an enumerated deny once (D25's missing `glue:CreateJob`), and DataZone gains APIs. **Revision trigger:** the first time Production must publish a data product of its own |

## `awsds-org-scp-ou-data.json` → **`Data`** OU

Data Governance sits on the **ownership** axis (D22): it holds the lake and the domain, and nothing is
supposed to *run* there. This is the one OU where a `Create*` wildcard is the correct instrument.

| `Sid` | Effect |
|---|---|
| `DenyUserCompute` | Denies the four EC2 launch actions (`RunInstances`, `StartInstances`, `CreateFleet`, `RequestSpotInstances`, `RequestSpotFleet`), `sagemaker:Create*`, `sagemaker:StartSession`, `glue:CreateDevEndpoint`, `CreateJob`, `StartJobRun`, `CreateSession`, `RunStatement`, `CreateMLTransform`, `StartNotebook`, plus `lambda:CreateFunction` and the three ECS creation actions. The Glue list is D25's lesson applied twice over: its own gap was `CreateJob`/`StartJobRun` — *a perfectly legal way to run the whole ingestion in the account whose policy set says nothing runs there* — and `CreateSession`/`RunStatement`/`StartNotebook` are what "interactive sessions and notebooks" are actually called. **The EC2 list is that same lesson a third time:** `RunInstances` is one door of several, and `CreateFleet`/`RequestSpot*` launch instances without ever calling it, so a one-action deny would have carried the name of a control while being a convention (Lesson 5). **The `sagemaker:Create*` wildcard is safe here and is not in `Workloads`**, because nothing in this account deploys anything; verification (viii) confirmed the unified domain evaluates as `datazone:*`, so the wildcard does not reach it. **Effect:** the lake account can hold and govern data and cannot execute anyone's code — with the two exceptions below, which are stated rather than accidental |
| `DenyCatalogMaintenanceRunsExceptMaintenanceRole` | Denies `glue:StartCrawler`, `StartCrawlerSchedule`, `StartColumnStatisticsTaskRun` and `StartColumnStatisticsTaskRunSchedule` unless the principal is `arn:aws:iam::<Data Governance>:role/awsds-data-catalog-maintenance`, with `BoolIfExists: aws:PrincipalIsAWSService=false` beside it. D27's exception, made *narrow* rather than wide: a crawler samples object contents, so it **does** read data, and the honest statement is "no compute here **except** the bounded set that produces catalog metadata, under one role". **The deny is on the run and not on the creation** — creating a crawler is Terraform's work, i.e. `InfrastructureAccess`, i.e. an administrator of that account, so a deny there would have to exempt the very principal it binds (Lesson 18); the run is the event that reads. **The service guard is the same one the two root conditioned statements carry, and it is here for consistency rather than for a measured failure**: an `ArnNotEquals` carve-out can only name principals it can spell, so a run *initiated by Glue itself* — a standing schedule, which Stage 5 deliberately does not create — would fall on the deny side of a principal test it never meant to take (Lesson 14). **The role name is a contract with [Stage 5](../../../plan/stages/stage-05-data-foundation.md)**: created under another name, the crawlers simply never run. **Effect: the negative half is exercisable now, the positive half is untested until Stage 5** — the role does not exist yet |
| `DenyLakeDeletionAndDeregistration` | Denies `s3:DeleteBucket` and `lakeformation:DeregisterResource`. The lake buckets are `[P]` and are never destroyed, so the first is a deny nothing legitimate hits. The second is the quieter one: **deregistering a prefix returns it to plain IAM without deleting anything**, so D13's whole enforcement model disappears while every object stays exactly where it was. **Effect:** unconditional — it binds the builder as hard as anyone, which is what separates it from a convention. **It reaches every bucket in the account, not only the lake's**, so a `terraform destroy` of anything with a bucket in it stops here; the amendment procedure is [Stage 5](../../../plan/stages/stage-05-data-foundation.md)'s, and it is also why the `s3:DeleteBucket` half stays **untested** — exercising it means creating a bucket that cannot then be deleted |

**What `DenyUserCompute` does not cover here, both by decision:**

- **Athena.** `athena:StartQueryExecution` is allowed, because Stage 5's Iceberg maintenance — `OPTIMIZE`
  (compaction) and `VACUUM` (snapshot expiry) — runs through it. So a full-lake read path exists inside the
  account that "runs nothing", with results written to S3, and the perimeter document only stops that write
  when the destination is outside the organization. **That path is [Stage 11](../../../plan/stages/stage-11-dlp.md)'s
  to detect, and it is named here so it is not rediscovered as a surprise.**
- **EMR, EMR Serverless and AWS Batch.** Not denied, because nothing in this design uses them anywhere; an
  action nobody can explain is one nobody re-reads. **Revision trigger:** the first appearance of any of
  them in any account.

Also outside any SCP's reach: an Auto Scaling group launches through a **service-linked role**, which AWS
exempts from SCPs — so `autoscaling:CreateAutoScalingGroup` is the residual EC2 path, and it is governed by
the account having no reason to hold one rather than by this document.

## `awsds-org-scp-ou-interactive.json` → **`Interactive`** OU

Development plus the nested `Sandboxes`, which carries no set of its own and inherits this one (D23, D35) —
attaching it twice is how two copies diverge.

| `Sid` | Effect |
|---|---|
| `DenyClassicNotebookInstances` | Denies `sagemaker:CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl` — **decision 1**, settled 2026-08-13. The candidate had been left unadopted while "the data scientist must be able to create notebooks" and "deny creating notebook instances" looked contradictory. They are not: an SMUS notebook is a **space plus an app**, and the classic notebook instance is a different product this design uses nowhere. **Effect:** removes an ungoverned interactive surface that bypasses the domain, the VPC-only app configuration and the `dev-env` image gate in a single call, **without touching any feature `CLAUDE.md` asks for**. It needs **no carve-out at all**, which is what makes it a control rather than a convention. **Revision trigger:** any SMUS surface that turns out to provision a classic notebook instance on the user's behalf |

## `awsds-org-scp-ou-identity.json` → **`Identity`** OU

The identity plane is as sensitive as Management (D10) and holds no workload — only Terraform managing
Identity Center. The tier exists to make its blast radius smaller.

| `Sid` | Effect |
|---|---|
| `DenyUserCompute` | The same statement as the `Data` OU's first row, for the same reason and with none of its neighbours: there is nothing to run in this account, so the four EC2 launch actions, `sagemaker:Create*`/`StartSession`, the Glue compute list, `lambda:CreateFunction` and the ECS creation actions are all denied. **Deliberately not `Data`'s other two statements** — `s3:DeleteBucket` and `lakeformation:DeregisterResource` mean nothing in an account that holds neither, and an OU whose policy is *mostly* right is the kind nobody re-reads. **The two documents must stay identical in this statement**: they are one idea in two files, and the moment they drift, the next reader has to diff them to find out which is authoritative (Lesson 14 — the check at the top of this file compares `Sid`s, not action lists). **Effect:** a compromise of the identity plane cannot be turned into compute inside it. Athena, EMR and Batch are uncovered here too, for the same reasons as in `Data` — with the difference that this account has no lake to read, so the Athena hole is a shape without content |

---

## What is not in any of these documents

- **The Region restriction** — `CT.MULTISERVICE.PV.1`, a Control Tower **managed control** enabled per OU
  (decision 6, step 7.7). AWS maintains its `NotAction` exemption list, which already covers the global
  services this project calls from `us-east-1`; a hand-written version would have to keep that list
  complete and would break IAM the first time it fell behind.
- **`AWSControlTowerExecution` carve-outs.** None of the four per-OU documents exempts it. An unnecessary
  carve-out is a hole rather than a safety margin. **Revision trigger:** a landing-zone update, account
  update or re-enrollment that fails on a compute-creation call in `Data` or `Identity`.
- **Anything protecting the Management account.** SCPs do not apply to it, by AWS's design — which is the
  same asymmetry the break-glass path relies on (D16), and the reason a bad `Deny` here is recoverable.

## References — the AWS documentation for the actions named above

**Two sources per service, and they answer different questions.** The *Service Authorization Reference* page
describes what each action grants, its resource types and its condition keys; the **machine-readable service
reference** is the same list as JSON, which is what a script can diff — it is how verification (viii) was
answered, and it is the only source that says what an action is *called today*.

| Service | Actions used here | Reference | Machine-readable |
|---|---|---|---|
| Amazon S3 | `PutObject*`, `DeleteBucket`, `PutAccountPublicAccessBlock` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html> | `https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json` |
| Amazon ECR | `InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`, `PutImage` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerregistry.html> | `…/v1/ecr/ecr.json` |
| Amazon ECR Public | `ecr-public:*` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerregistrypublic.html> | `…/v1/ecr-public/ecr-public.json` |
| Amazon EC2 | `RunInstances`, `StartInstances`, `CreateFleet`, `RequestSpotInstances`, `RequestSpotFleet`, `ModifySnapshotAttribute`, `ModifyImageAttribute`, `CreateStoreImageTask`, `ExportImage`, `CreateInstanceExportTask` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonec2.html> | `…/v1/ec2/ec2.json` |
| Amazon RDS | `ModifyDBSnapshotAttribute`, `ModifyDBClusterSnapshotAttribute`, `StartExportTask` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonrds.html> | `…/v1/rds/rds.json` |
| AWS IAM | `CreateUser`, `CreateAccessKey` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_identityandaccessmanagement.html> | `…/v1/iam/iam.json` |
| AWS Organizations | `LeaveOrganization` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsorganizations.html> | `…/v1/organizations/organizations.json` |
| Amazon GuardDuty | `DeleteDetector`, `UpdateDetector`, `DeleteMembers`, `DisassociateMembers`, `StopMonitoringMembers`, `DisassociateFromMasterAccount` **and** `DisassociateFromAdministratorAccount` (both spellings exist), `DeletePublishingDestination`, `UpdatePublishingDestination` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonguardduty.html> | `…/v1/guardduty/guardduty.json` |
| Amazon DataZone (the SMUS control plane) | `CreateDomain`, and the whole namespace in `Workloads` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazondatazone.html> | `…/v1/datazone/datazone.json` |
| Amazon SageMaker | `CreateDomain`, `CreateUserProfile`, `CreatePresignedDomainUrl`, `CreateSpace`, `CreateApp`, `StartSession`, `CreateNotebookInstance`, `CreatePresignedNotebookInstanceUrl`, `Create*` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonsagemaker.html> | `…/v1/sagemaker/sagemaker.json` |
| AWS Glue | `CreateDevEndpoint`, `CreateJob`, `StartJobRun`, `CreateSession`, `RunStatement`, `CreateMLTransform`, `StartNotebook`, `StartCrawler`, `StartCrawlerSchedule`, `StartColumnStatisticsTaskRun(Schedule)` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsglue.html> | `…/v1/glue/glue.json` |
| AWS Lake Formation | `DeregisterResource` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awslakeformation.html> | `…/v1/lakeformation/lakeformation.json` |
| AWS Lambda | `CreateFunction` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awslambda.html> | `…/v1/lambda/lambda.json` |
| Amazon ECS | `RegisterTaskDefinition`, `RunTask`, `CreateService` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerservice.html> | `…/v1/ecs/ecs.json` |

**The condition keys these documents turn on** — `aws:PrincipalArn`, `aws:ResourceOrgID`,
`aws:PrincipalOrgPaths` and `aws:PrincipalIsAWSService`, plus the `…IfExists` and `ForAllValues:`
operators, each of which evaluates **true when its key is absent** and is therefore where these documents
fail silently:

- Global condition context keys: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html>
- Condition operators, including `…IfExists` and the set operators: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html>
- Service control policies — syntax, inheritance and evaluation: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html>
- Service reference information (the machine-readable index): <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_service-reference.html>

---

*Documents: [`README.md`](README.md) · Stage: [1c step 7](../../../plan/stages/stage-01c-preventive-policies.md) ·
Probes: [`plan/runbooks/scp-battery.md`](../../../plan/runbooks/scp-battery.md) · Policy ids and dates:
[`log/stage-01c-preventive-policies.md`](../../../log/stage-01c-preventive-policies.md)*
