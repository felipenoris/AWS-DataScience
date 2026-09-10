# Organization policies — every statement in `policies/`, and what it is for

**The index of every document in [`policies/`](policies/), of all four policy types.** One section per file,
one row per `Sid` — or per tag key, or per declarative attribute: what it denies, why the statement exists,
and what it actually does once attached.
The documents themselves carry no comments — JSON has none — so this file is where their reasoning lives.

> ## Review this file at every policy change — in the same sitting
>
> **A statement added, removed, renamed or re-conditioned in `policies/` is a change to this file**, and so
> is attaching a document to a new target or detaching it. The check is mechanical: **the rows in a section
> must be the `Sid`s in that file, in the same order, and nothing else.** It compares both sides and prints
> `OK` per document — a version that only listed the `Sid`s would leave the comparison to a reader who
> already believes the file is right. It needs no AWS session and changes nothing:
>
> ```bash
> ./scripts/check-index.py
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
> [`docs/log/log-stage-01c-preventive-policies.md`](../../../docs/log/log-stage-01c-preventive-policies.md), recorded as each
> document is attached, and duplicating them here would produce a second, staler answer.

**Scope: every document in [`policies/`](policies/), of all four policy types — widened 2026-08-13 when
step 7.8 wrote the other three, and the file was renamed from `SCPs.md` on 2026-08-15 to stop the name
contradicting the scope.** The split the old name described was not worth keeping: a second index is a
second place to forget an amendment (Lesson 14), and "why does this statement exist" is the same question
whatever the type. **What differs is what plays the part of a `Sid`**, and
`check-index.py` knows all four: the `Sid` list for an SCP or an RCP, the **tag keys** for a tag policy, the
**attribute names** under `ec2_attributes` for a declarative policy. A document of a type it does not
recognise stops the run rather than being skipped.

**The four types do not compose the same way, and reading a row without knowing which type it is on will
mislead you.** An SCP bounds what a *principal in this organization* may do and never applies to the
management account. An **RCP** bounds who may reach a *resource in this organization* — including principals
outside it — and also never applies to the management account. A **tag policy** enforces nothing at all
unless `enforced_for` is set, which it is not here; it reports. A **declarative policy** is not a permission
boundary in either direction: it sets a service attribute that an account administrator then cannot change.

The throwaway documents in [`canary/`](canary/) are never attached to anything real and are described in
[`README.md`](README.md).

**Reading the whole ceiling:** every account is governed by the root documents **plus** its OU's, and denies
only ever compose. A call that fails may be failing on a statement in a different file — the CloudTrail
`errorMessage` names the policy id, which is the only reliable way to tell them apart.

---

## `awsds-org-scp-baseline.json` → organization **root**

The statements that must reach every account, including the ones that do not exist yet.

| `Sid` | Effect |
|---|---|
| `DenyLeaveOrganization` | Denies `organizations:LeaveOrganization`. Every vended account carries `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins` (measured, `docs/AWS_STATE.md` A.1), so this is one of the few Organizations calls a *member* account can really make — and one call drops every SCP and every Control Tower control for that account at once. **Effect:** no principal in any governed account can detach it from the organization. **Deliberately never probed:** its "allowed" outcome *is* the damage |
| `DenyIamUserCreation` | Denies `iam:CreateUser` and `iam:CreateAccessKey`. Principle 2 — *no IAM Users, no long-lived keys* — is otherwise a convention with nothing enforcing it. **Effect:** humans and machines can only obtain credentials by assuming a role. Break-glass (D16) is untouched: the Management account is exempt from SCPs by AWS's design |
| `DenyAccountBpaChangeExceptInfrastructure` | Denies `s3:PutAccountPublicAccessBlock` unless the principal ARN matches the `InfrastructureAccess` Identity Center role. **One action covers both directions** — the `DeletePublicAccessBlock` API is governed by the `Put` permission, so a `Delete…` action string would be a statement that silently does nothing. Protects the account-level Block Public Access set in step 7.4. **The carve-out is decision 7 and is the single wildcard-account ARN in this design**, because it must reach accounts that do not exist yet and whose role suffix is unknowable; Stage 2 step 9.2's check whitelists this `Sid` by name. **Effect, proven in both directions:** the canary (`AWSAdministratorAccess`) is denied, an `awsds-infra-*` profile still sets it |
| `DenySnapshotAndImageSharing` | Denies `ec2:ModifySnapshotAttribute`, `ec2:ModifyImageAttribute`, `rds:ModifyDBSnapshotAttribute`, `rds:ModifyDBClusterSnapshotAttribute`. **This is an exfiltration route that bypasses every other control here**: a Studio space's volume becomes an outside account's in two API calls with **no network path**, so NAT, the DNS firewall, endpoint policies and the `aws:ResourceOrgID` deny are all irrelevant to it — and no RCP reaches EC2 or RDS. Denied outright rather than conditioned on the destination: nothing in this design shares a snapshot at all. **It is half of the route and the other half is the row below** — this one is *granting someone else access to the image where it sits*; the sibling is *writing the image somewhere else*. **Effect:** the sharing route is closed for every principal, the builder included. The EC2 snapshot action is **attached but unexercised** — an invented snapshot id is rejected before authorization, `--dry-run` included — while its AMI sibling *was* denied; the RDS pair stays untested until an RDS exists |
| `DenyImageAndSnapshotExport` | Denies `ec2:CreateStoreImageTask`, `ec2:ExportImage`, `ec2:CreateInstanceExportTask` and `rds:StartExportTask`. **Added 2026-08-13, by re-reading the row above against AWS's action list rather than against its own claim.** That statement said it closed "the one exfiltration route that bypasses every other control", and it did not: sharing an attribute is one way an image leaves, and **writing it into a bucket is another** — `CreateStoreImageTask` stores an AMI into an S3 bucket that may belong to another account, `ExportImage`/`CreateInstanceExportTask` export a VM image, and `rds:StartExportTask` writes a DB snapshot out as Parquet. Both routes move the *same* bytes and neither needs a network path from the instance. **Why a separate `Sid` and not four more actions in the row above:** they are two different mechanisms, they will be exercised by different probes, and the log already records the original statement under its own name — a renamed `Sid` would make that entry describe something that no longer exists. **Effect:** unconditional, like its sibling; nothing in this design exports an image or a snapshot. **Revision trigger, and it is a plausible one:** exporting an RDS snapshot to S3 as Parquet is a real ingestion pattern, so the first time a relational source has to reach the lake, `rds:StartExportTask` is the action to reconsider — deliberately, with a named principal, not by deleting the statement |
| `DenyEcrPublicEntirely` | Denies `ecr-public:*`. Publishing to ECR Public is the case the perimeter document cannot reach: the repository is *inside* the organization, so `aws:ResourceOrgID` matches correctly and says nothing about the gallery being world-readable. The **whole namespace** rather than the publish actions, so it cannot fall one AWS release behind. **Effect:** no account can create or push to a public repository. **Anonymous pulls from `public.ecr.aws` are unaffected** — they involve no IAM action, so no SCP evaluates. Amendment trigger: an authenticated pull taken for the higher rate limit |
| `DenyGuardDutyTampering` | Denies `guardduty:DeleteDetector`, `UpdateDetector`, `DeleteMembers`, `DisassociateMembers`, `StopMonitoringMembers`, `DisassociateFromMasterAccount`, `DisassociateFromAdministratorAccount`, `DeletePublishingDestination` and `UpdatePublishingDestination`. Measured gap: **no Control Tower guardrail covers GuardDuty**, while Config already is covered (which is why no Config statement is written here). **Five of those nine were added 2026-08-13 and the reason is worth keeping: the statement had been written against the API's old vocabulary.** GuardDuty renamed master→administrator and **both spellings still exist as actions** — denying only `DisassociateFromMasterAccount` left the modern call open, which is a statement that reads as protection and is not (verified against the machine-readable list, where both names appear). `DisassociateMembers`/`StopMonitoringMembers` are the current member-detach pair, and the publishing-destination pair kills or redirects the export of findings without touching a detector at all. **Effect:** inert until Stage 15 turns GuardDuty on (Stage 4 until the 2026-08-18 split) — deliberately dormant, not an oversight. The battery probe is what says the statement is nonetheless live |
| `DenyDataZoneDomainOutsideDataOu` | Denies `datazone:CreateDomain` unless the principal's org path is the `Data` OU's. D26 says there is **one** unified domain; without this, a second domain anywhere reintroduces a second interactive entry point with its own blueprints and project roles. Three mechanics carry it and each fails toward a deny that never lifts: `aws:PrincipalOrgPaths` is multi-valued, so `ForAllValues:StringNotLike`; `ForAllValues` is vacuously true over an empty set, so `BoolIfExists: aws:PrincipalIsAWSService=false` is required; the path is the **full path with a trailing slash**. **`CreateDomain` alone, never `datazone:*` at the root** — Sandbox and Development need `PutEnvironmentBlueprintConfiguration`. **Effect: EXERCISED IN BOTH DIRECTIONS, 2026-08-21 — Stage 6 step 0.1a, and this row read *attached but unexercised* from 1c until that day.** *Positive:* `terraform apply` of `data-governance/governance/` created the domain (`awsds-studio`, V2) from the `Data` OU — the carve-out admits the account it was written for. *Negative:* the **identical request shape**, replayed as `awsds-policy-canary`, returned `AccessDeniedException … not authorized to perform: `datazone:CreateDomain` … **with an explicit deny in a service control policy**`, naming this document's policy id. So `aws:PrincipalOrgPaths` **does** populate for DataZone, the `ForAllValues` failure mode did not fire, and INT-12's forbidden one-domain-per-account fallback is **closed rather than merely intended**. **And the 2026-08-20 wall is explained, by measurement rather than by inference:** those four shapes passed `--domain-execution-role` and **no** `--service-role`; the replay passed both and reached authorization from the same CLI. `Cross-account pass role is not allowed` was DataZone complaining about the *missing service role* — a message that names neither the field nor the account, which is Lesson 24's shape and why the contrast was needed to see it. Both throwaway roles were deleted in the same sitting and the canary holds no domain and no `awsds-*` role |

**Not in this document, and each absence is a decision:** no Config statement (Control Tower's guardrail
already denies the recorder, with the `AWSControlTowerExecution` carve-out that keeps the landing zone able
to update itself) and **no CloudTrail statement** (measured: nothing denies it anywhere — the trail is
organization-level and lives in Management, which is SCP-exempt, so a member-account deny would bind
nothing reachable. Revision trigger: the first trail this project creates in a member account).

**`guardduty:UpdateDetector` collides with [Stage 15](../../../docs/plan/stages/stage-15-guardduty.md) first
and [Stage 11 step 4](../../../docs/plan/stages/stage-11-dlp.md) after it, and both collisions are deliberate
rather than unnoticed.** *(2026-08-18: the first is Stage 15's decision 1 — the protection plans arrive ON,
so the switch-OFF on Audit's own detector meets this deny before Stage 11's switch-on does.)* The deny is unconditional and this document sits on the
root, so it reaches **Audit** — the GuardDuty administrator — as hard as any member. Org-wide administration
is unaffected, because turning a feature on across the organization goes through
`UpdateOrganizationConfiguration` and `UpdateMemberDetectors`, neither of which is denied; what *is* denied
is changing **Audit's own detector**, which is exactly what enabling S3 Protection and Malware Protection
there will try to do. **The procedure is the same shape as the `s3:DeleteBucket` one in `Data`:** detach
`awsds-org-scp-baseline` from the root, make the change, re-attach, and re-run phases 1-3 of
[`scp-battery.md`](../../../docs/plan/runbooks/scp-battery.md) before the sitting is called done. Carving out a
named administration role instead is the alternative, and it is Stage 15's decision 1 — whose candidate
question that stage's step 5 settles: GuardDuty creates only the service-linked role, so the only nameable
principal is Audit's own administrator role, and the carve-out is option (c), recommended against.
**What is not acceptable is discovering this at the console on the evening of Stage 11**, which is the
only reason it is written here.

## `awsds-org-scp-perimeter.json` → organization **root**

The trusted-**resources** axis of the data perimeter. A separate document because it is the one most likely
to be amended (Stage 6 and Stage 9 both come back to it) and it is detached and re-attached on its own.

| `Sid` | Effect |
|---|---|
| `DenyS3ObjectWriteOutsideOrganization` | Denies the seven S3 object-write actions (`PutObject`, `PutObjectAcl`, `PutObjectTagging`, `PutObjectVersionAcl`, `PutObjectVersionTagging`, `PutObjectRetention`, `PutObjectLegalHold`) when `aws:ResourceOrgID` is not this organization, with `BoolIfExists: aws:PrincipalIsAWSService=false` beside it. Writes only: a read-side deny of the same shape breaks `docker pull`, package installs and every legitimate read of an AWS-owned bucket. The action list is enumerated and an action wildcard is forbidden: `StringNotEqualsIfExists` evaluates true when the key is absent, so `s3:Put*` would reach the account-level `s3:PutAccountPublicAccessBlock` and deny, everywhere and for everyone, the call step 7.4 depends on. **Effect, proven by the inverted document:** `aws:ResourceOrgID` populates for S3 and the deny reaches an ordinary principal; in-org writes still succeed with it attached |
| `DenyEcrPushOutsideOrganization` | Denies `ecr:InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload` and `PutImage` under the same condition pair. Four actions, not `PutImage` alone: the layers are the data, and by the time a manifest write is denied the filesystem contents are already in the outside repository. `ecr:GetAuthorizationToken` is excluded: it is registry-scoped, so the key never populates and an `IfExists` deny would catch it unconditionally; authenticating against an outside registry is harmless, the write is the event. No carve-out: a pull-through cache writes into *your own* registry, so the deny never evaluates against it, and INT-01's replication is performed by ECR itself under the service carve-out. **Effect, proven separately from S3** (key population is a property of each service's authorization): the inverted probe denied `initiate-layer-upload`, and the real document leaves in-org pushes working |

## `awsds-org-scp-ou-workloads.json` → **`Workloads`** OU

Staging and Production: deployment targets, written by the pipeline, with no human control plane (D17, D20).

| `Sid` | Effect |
|---|---|
| `DenyInteractiveSageMakerSurface` | Denies `sagemaker:CreateDomain`, `CreateUserProfile`, `CreatePresignedDomainUrl`, `CreateSpace`, `CreateApp`, `StartSession`, `CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl`. Turns D17, *no interactive surface outside the Interactive OU*, into a control. Enumerated, and `sagemaker:Create*` is forbidden here: `CreateModel`, `CreateEndpoint`, `CreateEndpointConfig` and `CreateTrainingJob` are what these accounts are for, so a prefix wildcard would deny the stage rather than the route. `CreateSpace`+`CreateApp` are the SMUS notebook (a space *plus* an app), and `StartSession` is the remote-IDE connection, which matches neither `Create*` nor `datazone:*`. **Effect:** a deployment target can serve models and cannot host a human |
| `DenyDataZoneEntirely` | Denies `datazone:*`. D26 says Staging and Production are never associated to the domain. It closes three things: a domain created locally; the account associating itself and configuring a blueprint (`PutEnvironmentBlueprintConfiguration` mints provisioning and manage-access roles with broad permissions *even when provisioning then fails*); and the non-ML blueprints, which provision buckets, Glue databases and Athena workgroups without ever passing through `sagemaker:*`. The whole namespace: this plan already paid for an enumerated deny once (D25's missing `glue:CreateJob`), and DataZone gains APIs. **Revision trigger:** the first time Production must publish a data product of its own |
| `DenyAthenaSparkStartSession` | Denies `athena:StartSession`, `athena:UpdateSession` and `athena:StartCalculationExecution` on `arn:aws:athena:*:*:workgroup/*`, copied verbatim from the `Interactive` document (Stage 6b step 3.8, 2026-09-06): the two OUs deny the same thing for the same reason, and a paraphrase would be a second spelling to keep in step (Lesson 33). A Workload account needs it because AWS's SMUS network-isolation guide states that *"Amazon Athena for Apache Spark does not currently support Amazon VPC"*, so a Spark session is an unproxied path out of the account, and the accounts under this OU hold deploy credentials. It denies Spark, not SQL: `StartQueryExecution` is untouched, so Stage 9's `awsds-prod-athena` workgroup is unaffected. Attached before the account it was written for arrived (the stage schedules this after the OU move), so the account never spent a moment in `Workloads` without the deny it had in `Interactive` |

## `awsds-org-scp-ou-data.json` → **`Data`** OU

Data Governance sits on the ownership axis (D22): it holds the lake and the domain, and nothing runs there.
This is the one OU where a `Create*` wildcard is the correct instrument.

| `Sid` | Effect |
|---|---|
| `DenyUserCompute` | Denies the five EC2 launch/start actions (`RunInstances`, `StartInstances`, `CreateFleet`, `RequestSpotInstances`, `RequestSpotFleet`), `sagemaker:Create*`, `sagemaker:StartSession`, `glue:CreateDevEndpoint`, `CreateJob`, `StartJobRun`, `CreateSession`, `RunStatement`, `CreateMLTransform`, `StartNotebook`, `athena:StartQueryExecution`, `lambda:CreateFunction` and the three ECS creation actions. The Glue list applies D25's lesson twice: its own gap was `CreateJob`/`StartJobRun`, a legal way to run the whole ingestion in the account whose policy set says nothing runs there, and `CreateSession`/`RunStatement`/`StartNotebook` are what "interactive sessions and notebooks" are called. The EC2 list is the same lesson a third time: `RunInstances` is one door of several, and `CreateFleet`/`RequestSpot*` launch instances without calling it, so a one-action deny would be a convention carrying the name of a control (Lesson 5). The `sagemaker:Create*` wildcard is safe here and not in `Workloads`, because nothing in this account deploys anything; verification (viii) confirmed the unified domain evaluates as `datazone:*`, so the wildcard does not reach it. **Effect:** the lake account can hold and govern data and cannot execute anyone's code, with the two exceptions listed below the table. The Athena half was exercised 2026-08-20 (Stage 5 pass 4e), with a caveat no earlier probe in this document needed: Athena's refusal names no policy. The error is a bare "You are not authorized to perform: `athena:StartQueryExecution` on the resource", which the battery's classifier reads as `DENY-NOT-SCP`, i.e. an IAM deny; it is not one, and no wording says so. The attribution rests on a contrast probe: the same call from `Sandbox 1`, in an OU this statement does not reach, gets past authorization and dies on the workgroup. That also settled Lesson 21's fork by measurement: Athena authorizes before it validates for this action |
| `DenyCatalogMaintenanceRunsExceptMaintenanceRole` | Denies `glue:StartCrawler`, `StartCrawlerSchedule`, `StartColumnStatisticsTaskRun` and `StartColumnStatisticsTaskRunSchedule` unless the principal is `arn:aws:iam::<Data Governance>:role/awsds-data-catalog-maintenance`, with `BoolIfExists: aws:PrincipalIsAWSService=false` beside it. D27's exception, made narrow: a crawler samples object contents, so it reads data, and the statement is "no compute here except the bounded set that produces catalog metadata, under one role". The deny is on the run, not the creation: creating a crawler is Terraform's work, i.e. `InfrastructureAccess`, an administrator of that account, so a deny there would have to exempt the very principal it binds (Lesson 18); the run is the event that reads. The service guard is the one the two root conditioned statements carry, here for consistency rather than for a measured failure: an `ArnNotEquals` carve-out can only name principals it can spell, so a run initiated by Glue itself (a standing schedule) would fall on the deny side of a principal test it never meant to take (Lesson 14). The role name is a contract with [Stage 5](../../../docs/plan/stages/stage-05-data-foundation.md): created under another name, the crawlers never run; pass 1 created it under exactly this name. **Effect:** the negative half was exercised in the canary on 2026-08-13 and fired against a principal that reaches it on 2026-08-19 (Stage 5 pass 4d): `InfrastructureAccess` in Data Governance, an account in the `Data` OU, was refused `glue:StartCrawler` *with an explicit deny in a service control policy*, naming this document. (The persona half measured in group A never reached here: the personas sit in `Interactive` and are refused earlier, by the absence of any `glue:Start*` allow.) The positive half is unreachable, not untested: the maintenance role's trust policy admits `glue.amazonaws.com` and nothing else, so no person and no other service's role can assume it, and both crawlers read `Schedule: null` with zero triggers. The scheduler path the service guard was written for is the only invocation path left, and Stage 5 creates no schedule; verified by reading (Lesson 22). A name is not a caller. Do not loosen this statement or that trust policy to make the run happen: the missing piece is the schedule, [open question 19](../../../docs/plan/open-questions.md) |
| `DenyLakeDeletionAndDeregistration` | Denies `s3:DeleteBucket` and `lakeformation:DeregisterResource`. The lake buckets are `[P]` and never destroyed, so the first is a deny nothing legitimate hits. The second is quieter: deregistering a prefix returns it to plain IAM without deleting anything, so D13's enforcement model disappears while every object stays where it was. **Effect:** unconditional; it binds the builder as hard as anyone. It reaches every bucket in the account, not only the lake's, so a `terraform destroy` of anything with a bucket in it stops here; the amendment procedure is [Stage 5](../../../docs/plan/stages/stage-05-data-foundation.md)'s. The `s3:DeleteBucket` half stays untested: exercising it means creating a bucket that cannot then be deleted |

**What `DenyUserCompute` does not cover here**, the first by decision, the second by omission:

- **EMR, EMR Serverless and AWS Batch.** Not denied: nothing in this design uses them anywhere, and an
  action nobody can explain is one nobody re-reads. **Revision trigger:** the first appearance of any of
  them in any account.
- **Glue table optimizers** (found 2026-08-19). No statement in this document names a table-optimizer
  action, although D27's mechanics line asked for them in the carve-out beside the column-statistics ones,
  so Iceberg auto-compaction is compute in the no-compute account that nothing reaches. Harmless today: the
  only optimizer configured, at Stage 5 pass 1, runs under the carve-out role itself; but the deny does no
  work, and any principal here could configure another. **Revision trigger and amendment shape:** verify
  the real action names against the machine-readable Glue action list, as 7.6a did for the EC2 siblings,
  and decide in writing whether they join `DenyUserCompute` behind the same `ArnNotEquals` carve-out.

Athena headed this list until 2026-08-20 (Stage 5 pass 4e). The allow existed for Stage 5's Iceberg
maintenance, expected to run `OPTIMIZE`/`VACUUM` through Athena, a reason decision 4 withdrew on 2026-08-18
by choosing Glue automatic compaction, which needs no Athena. The 12 sample rows were loaded by in-account
Athena `INSERT` on 2026-08-20 and the amendment went in the same day, in both documents. The cost: this was
the only in-account way to query the lake, so the `count(*)` that proved those 12 rows exist is no longer
reproducible from here; the equivalent runs from a consumer account over the share, which is D13 working
as designed and still a diagnostic given up. A reader debugging the lake meets this deny first. Stage 11's
`awsds-data-athena` rule was written conditional on which way this row read; it now reads *closed*.

Also outside any SCP's reach: an Auto Scaling group launches through a service-linked role, which AWS
exempts from SCPs, so `autoscaling:CreateAutoScalingGroup` is the residual EC2 path, governed by the
account having no reason to hold one rather than by this document.

## `awsds-org-scp-ou-interactive.json` → **`Interactive`** OU

Development plus the nested `Sandboxes`, which carries no set of its own and inherits this one (D23, D35);
attaching it twice is how two copies diverge.

| `Sid` | Effect |
|---|---|
| `DenyClassicNotebookInstances` | Denies `sagemaker:CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl` (decision 1, settled 2026-08-13). "The data scientist must be able to create notebooks" and "deny creating notebook instances" do not contradict: an SMUS notebook is a space plus an app, and the classic notebook instance is a different product this design uses nowhere. **Effect:** removes an ungoverned interactive surface that bypasses the domain, the VPC-only app configuration and the `dev-env` image gate in a single call, without touching any feature `CLAUDE.md` asks for, and needs no carve-out. **Revision trigger:** any SMUS surface that turns out to provision a classic notebook instance on the user's behalf |
| `DenyAthenaSparkStartSession` | Denies `athena:StartSession`, `athena:UpdateSession` and `athena:StartCalculationExecution` on `arn:aws:athena:*:*:workgroup/*` (Stage 6 decision 3, settled 2026-08-19 by the user, applied 2026-08-21). An SCP rather than the two controls AWS documents beside it: the Tooling blueprint's Athena flag removes Athena SQL with Spark, which is D13's whole query path, and is not retroactive (new projects only); the doc's third control is a grant-shaped edit to blueprint-authored IAM policies (Lesson 11, and INT-15's reconciliation risk). An OU SCP is preventive, retroactive and precise, and it reaches project roles, which is why the D13 permissions boundary in `terraform-modules/sagemaker-prereqs/` carries no Athena Spark clause (Lesson 20). Spark rather than Athena at all: an Athena Spark session has no `NetworkConfiguration` anywhere in its API, so the executor runs outside our VPC, outside every endpoint policy, every `aws:SourceVpce` condition and every flow log the data perimeter is built from. The 2026-04 PrivateLink release moved the client → session path only (Spark Connect, the Live UI, the History Server); a session URL minted inside the VPC stays reachable from the public internet by design. Athena SQL is untouched: it rides `StartQueryExecution` on the required `athena` API endpoint, and the three Spark session endpoints are separate surfaces this design does not create (a commented exclusion beside `extra_services` in both Interactive `egress/` slices). `athena:UpdateSession` was measured against the machine-readable action list on 2026-08-21 and there is no such operation in the Athena API model (`2017-05-18`): the pair comes from AWS's own sample statement, the better authority for a policy, so it ships as a hedge and the statement's real content is `StartSession` + `StartCalculationExecution`. The third action is there because `StartCalculationExecution` takes a `SessionId`, so a session obtained by any other route would still submit work. The `Resource` stays at AWS's wildcard: narrowing it to `us-west-2` would *permit* Spark everywhere else. No carve-out: nobody in this design legitimately opens a Spark session. **Revision trigger:** Athena Spark gaining an equivalent of `NetworkConfiguration`, executors in our subnets under our security group. *Not* "Athena Spark supports VPC", which the 2026-04 headline already says and which is about the control path |

## `awsds-org-scp-ou-identity.json` → **`Identity`** OU

The identity plane is as sensitive as Management (D10) and holds no workload, only Terraform managing
Identity Center. The tier exists to make its blast radius smaller.

| `Sid` | Effect |
|---|---|
| `DenyUserCompute` | The same statement as the `Data` OU's first row, for the same reason and with none of its neighbours: nothing runs in this account, so the five EC2 launch/start actions, `sagemaker:Create*`/`StartSession`, the Glue compute list, `athena:StartQueryExecution`, `lambda:CreateFunction` and the ECS creation actions are all denied. Not `Data`'s other two statements: `s3:DeleteBucket` and `lakeformation:DeregisterResource` mean nothing in an account that holds neither. The two documents must stay identical in this statement: they are one idea in two files, and `check-index.py` compares `Sid`s, not action lists, so drift is silent (Lesson 14). The Athena amendment landed 2026-08-20 (Stage 5 pass 4e) in both documents in the same sitting; the phase-4b re-probe ran from `awsds-infra-identity` as well as `awsds-infra-data`, both refused, and the attribution for both comes from a third probe rather than from either error message (Athena names no policy; the `Data` row says why). This account has no lake, so the Athena half here is a shape without content and will never be load-bearing. **Effect:** a compromise of the identity plane cannot be turned into compute inside it. EMR and Batch are uncovered here too, for the same reasons as in `Data` |

---

## `awsds-org-rcp-perimeter.json` → organization **root**  *(RESOURCE_CONTROL_POLICY)*

The trusted-*identities* axis (`docs/plan/architecture.md` §4.2), the mirror of the SCP perimeter above:
that one stops *our* principals writing *outside*, this one stops *outside* principals reaching *our*
resources. Seven services, because seven is what RCPs support: S3, STS, KMS, SQS, Secrets Manager, DynamoDB
and ECR (widened from five by the user, 2026-08-12). EC2, RDS and EFS are outside RCP reach entirely, which
is why the snapshot route is an SCP deny in `awsds-org-scp-baseline.json`; EFS stopped mattering on
2026-08-17, when the NFS requirement was withdrawn and D24's filesystem with it.

Two grammar differences from every other document here make it fail closed if forgotten: an RCP statement
requires a `Principal` element (`"*"`), and the budget is half, 5 policies per node and 5 120 characters
rather than the SCP's 10 and 10 240, because RCPs were not part of the May 2026 increase.

`BoolIfExists: aws:PrincipalIsAWSService=false` is on every statement. Service-*linked* roles are exempt
from RCPs by construction; service principals are not. Without the carve-out the first things denied are
CloudTrail and Config writing into the Log Archive bucket, in the account whose only job is to receive
them. The organization IAM Access Analyzer in Audit (1b step 8.2) reads resource policies across every
account under `access-analyzer.amazonaws.com` and depends on the same pair; confirm it after attaching by
checking that the analyzer still reports `ACTIVE` with a finding count
(`./aws/cloudshell/audit-iam-analyser.sh`), not by re-reading this JSON.

The document is split into four statements for future carve-outs: these services will not need the same
exemptions (ECR already has a service-fetch story that S3 does not), and one statement covering all seven
would force any future carve-out onto services that never needed it.

| `Sid` | Effect |
|---|---|
| `EnforceOrgIdentitiesOnDataStores` | Denies `s3:*`, `dynamodb:*` and `sqs:*` to any principal whose `aws:PrincipalOrgID` is not this organization. Whole namespaces, unlike the SCP perimeter: the SCP had to enumerate because `s3:Put*` would have caught the account-level `PutAccountPublicAccessBlock` that step 7.4 depends on, while an RCP is evaluated against *our* resources and a principal outside the organization has no legitimate call to make against any of them. `StringNotEqualsIfExists` also denies the anonymous request, where the key does not populate at all: the public-bucket case, and wanted. DynamoDB is inert on attachment and adopted anyway: this project has no table and no plan for one (D3 chose native S3 locking to avoid it), so the clause is in place before it is needed |
| `EnforceOrgIdentitiesOnSecretsAndKeys` | Denies `kms:*` and `secretsmanager:*` under the same condition pair. A KMS key policy that grants an outside account is overridden by this: the RCP is evaluated on the resource side, so it wins over a permissive resource policy. **Revision trigger:** the first legitimate cross-organization share, which this design does not have and D31's derived-zone CMK does not need |
| `EnforceOrgIdentitiesOnRegistry` | Denies `ecr:*` under the same pair. The load-bearing one, and the only one whose carve-out is exercised in normal operation. D14 puts the registry in Production and three integrations cross an account boundary to reach it: INT-01 (the Studio custom image pulled into the Sandbox and Development domains), INT-07 (Staging pulling the application image) and INT-01's replication fallback. All are inside the organization, so `aws:PrincipalOrgID` admits them, which is the reason to key on the organization rather than on an account list. The service half is different: ECR performs pull-through cache fetches and replication writes itself, under a service principal, so those depend on the `IsAWSService` carve-out. Test a pull-through cache fetch and a cross-account pull after attaching: the cross-account half proves the org key, the cache proves the carve-out, and neither proves the other |
| `EnforceOrgIdentitiesOnRoleAssumption` | Denies `sts:AssumeRole` and `sts:SetContext` to principals outside the organization, the third-party-access route closed at the resource. Scoped to exactly the two actions AWS's own `CT.STS.PV.1` names; the four it excludes (`AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity`, `SetSourceIdentity`, `TagSession`) locked every SSO user out of all six member accounts on 2026-08-14. Those operations carry no AWS credentials, so `aws:PrincipalOrgID` never populates, `IfExists` turns the absence into a match, and the deny fires. Identity Center *is* the external federation: each account holds a SAML provider `AWSSSO_<id>_DO_NOT_DELETE`, and the trust policy of `AWSReservedSSO_InfrastructureAccess_*` (read in Development) permits only `sts:AssumeRoleWithSAML` + `sts:TagSession` from it, so denying either makes the permission-set role unreachable by anyone. Three properties of that outage: it spares Management (RCPs do not apply there), so console access through CT Admin survives and the failure reads like a CLI problem; it is latent for the life of an already-vended session (4 h measured), because the deny lands on the next `GetRoleCredentials`, so probes passing right after an attach prove nothing; and it surfaces as `ForbiddenException … GetRoleCredentials: No access`, indistinguishable from an expired token unless the wording is read. **Revision trigger:** the first genuine external federation or third-party integration; re-read this row before adding *any* `sts:` action, because the excluded four are excluded by AWS for a reason that applies to every future one. `sts:SetContext` is adopted on AWS's authority, and its first in-org contact was Lake Formation cross-account version 4, not Stage 6 (INT-11 owns the detail): the metadata half travelled clean on 2026-08-19 (Stage 5 pass 3's shares applied with this statement attached), the credential-vending half is exercised at Stage 5 pass 4d's first persona query, and Stage 6's trusted identity propagation is a later, second contact to re-confirm |

## `awsds-org-scp-tag-enforcement.json` → organization **root**

Decision 5, settled 2026-08-13 by measurement. A tag policy cannot force a resource to be created with
tags (it constrains *tagging operations*), so the forcing function is an SCP with `aws:RequestTag`
conditions on the create actions. The question was which create actions, and the plan's instruction was to
verify the API before including one.

Measured from the machine-readable service reference: `s3:CreateBucket` maps `aws:RequestTag`/`aws:TagKeys`,
so the deciding question for S3 is whether Terraform's `aws` provider sends the tags on the create call or
still calls `PutBucketTagging` afterwards; if the latter, the condition is unsatisfiable by the tool this
project builds with and the first thing denied is Stage 2's own state bucket. That is answered at Stage 2,
free, by looking at what the provider sends. `rds:CreateDBInstance` maps it too and is inert: no RDS here
and none planned. So `ec2:RunInstances` is the only member of the scope that is both live (WireGuard,
GitLab, the runners) and answerable now.

Two mechanics decide whether this document works at all, and both fail silently in the same direction, a
deny that fires on everything:

- The `Resource` is `arn:aws:ec2:*:*:instance/*`, never `*`. `RunInstances` creates and references several
  resource types in one call (subnet, security group, image, volume, network interface) and
  `aws:RequestTag` only populates for the ones the request actually tags. With `Resource: "*"` the `Null`
  test is true for the untagged resource types and every launch is denied, tags or no tags.
- One statement per required key. Two keys inside a single `Null` block are ANDed, which would deny only
  when *both* tags are missing, the opposite of the requirement.

Volumes are out of scope: `TagSpecifications` for `volume` is optional on a launch, so including `volume/*`
would deny any launch that did not tag its root volume. Cost attribution for volumes rides on the instance.

| `Sid` | Effect |
|---|---|
| `DenyRunInstancesWithoutEnvironmentTag` | Denies `ec2:RunInstances` on `instance/*` when `aws:RequestTag/Environment` is absent, with the service carve-out beside it. `Environment` is the tag the cost model groups by, and its enumeration is fixed at `sandbox\|development\|data\|staging\|production\|org` with no ordinal at any N (user, 2026-08-13): a per-unit value would mean editing an organization policy at every vend, and forgetting is an `AccessDenied` on the first apply in a brand-new account |
| `DenyRunInstancesWithoutProjectTag` | The same for `aws:RequestTag/Project`. Two keys and no more: this is the one document in 7.5-7.8 that binds the builder exactly as hard as it binds anyone (Lesson 18), so the scope is the two keys whose absence costs something. `ManagedBy`, `Owner` and `CostCenter` are conventions, not controls; they are in the tag policy below, which reports and does not enforce |

Exercise both directions before trusting it: `ec2:RunInstances --dry-run` with and without
`--tag-specifications` in `Policy Canary`, the two-different-errors shape the battery prefers. It settles
from the authorization engine what the service reference could not say: that reference maps
`aws:RequestTag` to 0 of EC2's 793 actions while declaring the key at the service level, so its silence
about `RunInstances` is a gap in the instrument, not a fact about EC2 (Lesson 13).

## `awsds-org-tag-policy.json` → organization **root**  *(TAG_POLICY)*

This document reports; it does not enforce. A tag policy defines the canonical capitalisation of a tag key
and, optionally, the values that key may take, and then evaluates *tagging operations* against that
definition. Without an `enforced_for` list it prevents nothing: a non-compliant tag is flagged in the
Resource Groups console and applied anyway. `enforced_for` is not set here, because it covers only a subset
of resource types and would make the failure mode depend on which service you happened to be using.
Reading "we have a tag policy" as a control is the shape of Lesson 5; what forces tags is
`awsds-org-scp-tag-enforcement.json` above, on two keys, on one action.

**Revision trigger:** the first cost report that cannot answer a question because of a mistyped tag. At that
point `enforced_for` becomes worth its per-resource-type surprise.

| `Sid` | Effect |
|---|---|
| `Environment` | Fixes the capitalisation and enumerates `sandbox`, `development`, `data`, `staging`, `production`, `org`. `org` marks org-level and platform resources (the identity slice, `Policy Canary`); `data` marks Data Governance, which is not an environment but sits on the ownership axis, so cost reports can separate it. `shared` is reserved and unused: it names a Shared Services account if D14's revision trigger ever fires |
| `Project` | Fixes the capitalisation and pins the single value `AWS-DataScience`. One value is what makes a resource created outside this project visible in a cost report that filters on it |
| `ManagedBy` | Fixes the capitalisation and enumerates `terraform` and `console`. `console` is admitted for the six artefacts Stage 2 names as structurally outside Terraform (wrong account, Control Tower's object, or an SCP that would deny the apply); tagging those `terraform` would be false at the only moment anyone reads the tag, when working out where a resource's source of truth is |
| `Owner` | Fixes the capitalisation only, with no value enumeration: the value is one of the project's `sso-group-*` groups and that list grows per business unit at Stage 14, so enumerating it here would need an organization-policy edit at every vend, the failure this project already refused for `Environment` |
| `CostCenter` | Fixes the capitalisation only. The value is a stage, an open set by construction |

## `awsds-org-declarative-ec2.json` → organization **root**  *(DECLARATIVE_POLICY_EC2)*

Not a permission boundary in either direction. A declarative policy sets an EC2 *service attribute* for
every account in scope and then makes it unchangeable from inside those accounts
(`DisableSnapshotBlockPublicAccess` and friends stop working there). It is the right instrument for an
account-level, Regional setting: the only way to apply one across every account and every Region at once,
and it cannot be switched off locally afterwards.

AWS states that snapshot block public access **does not prevent private sharing**. It blocks the *public*
snapshot, the accident, and leaves sharing with a named outside account, the deliberate exfiltration, open.
That route is closed by `DenySnapshotAndImageSharing` in `awsds-org-scp-baseline.json`; the two are not
substitutes (Lesson 5).

| `Sid` | Effect |
|---|---|
| `exception_message` | The text a user sees when one of these attributes refuses their call. Says which policy did it and that the setting is organization-managed, because the default message reads like a broken console rather than a control working as intended |
| `snapshot_block_public_access` | `block_all_sharing`: blocks all public sharing of EBS snapshots and treats already-public snapshots as private. The stronger of the two blocking values, chosen because nothing is shared today, so there is nothing to grandfather |
| `image_block_public_access` | `block_new_sharing`. The asymmetry with the row above is AWS's, not a choice: the AMI attribute has no `block_all_sharing` value, so an AMI that is already public stays public. Nothing here is, and the SCP baseline denies `ec2:ModifyImageAttribute`, so the gap is closed from the other side. Recorded because "both are blocked" is the sentence someone will write later |
| `instance_metadata_defaults` | `http_tokens: required` (IMDSv2), `http_put_response_hop_limit: "2"` (AWS's own recommendation once tokens are required; 1 breaks containerised workloads reaching IMDS), `http_endpoint: enabled`, `instance_metadata_tags: no_preference`. `http_tokens_enforced` is deliberately not set: `http_tokens: required` sets the account *default*, which a launch may still override by asking for `optional`; `http_tokens_enforced: enabled` is what makes an IMDSv1 launch impossible. So this row is a default and not yet a ceiling (Lesson 5). **Revision trigger:** turn `http_tokens_enforced` on once Stage 4's WireGuard instance and Stage 7's GitLab and runners have launched successfully with IMDSv2, because AWS's warning is that enforcing while anything still asks for `optional` fails the launch |
| `serial_console_access` | `disabled`. Beyond what step 7.8 listed. The EC2 serial console is console-based access to an instance that traverses no network, so it is a path around `CLAUDE.md`'s first objective (all user access through the VPN) and around every security group and endpoint policy Stages 3, 4 and 9 write. It is off by default per account, which makes pinning it cheap and forgetting it easy. Drop this row if the trade is unwanted: the cost is that recovering a mis-networked instance then needs a rebuild rather than a serial session |

## The organization delegation policy

*Not a file in [`policies/`](policies/), not attached to a target, and not Terraform-managed. Applied by
hand on 2026-08-15 (Stage 2 step 5.1, INT-20); ids and dates are in
[`docs/log/log-stage-02-terraform-foundation.md`](../../../docs/log/log-stage-02-terraform-foundation.md).*

**1. What it is for.** Every other document indexed above is a ceiling on what accounts may do. This one is
a grant of who may edit those ceilings: a *resource-based delegation policy* on the organization itself
(`organizations:PutResourcePolicy`, one per organization), naming the **Identity** account as principal. By
AWS's default only the management account may create, update, delete, attach or detach any of the ten
documents above; without it this folder could hold JSON and never apply it. It is not
`register-delegated-administrator`, a different mechanism that does not cover policy management, and the
Identity Center delegation of 1b step 1 does not cover it either.

The scope was decided by measurement: the `Resource` list reaches the root, nested OUs (depth 2,
`Sandboxes` under `Interactive`) and accounts, and all four policy-type ARNs, so all ten documents are in
reach rather than only the four attached to an OU.

| `Sid` | Effect |
|---|---|
| `DelegateOrganizationNavigationToIdentity` | Sixteen read actions on `Resource: "*"`, no condition: walking the organization and refreshing what this folder manages. Two of them are load-bearing. `DescribePolicy` is what the provider calls on every refresh of an `aws_organizations_policy`: without it an import succeeds and the next `plan` fails. `DescribeResourcePolicy` is what [`aws/org-delegation.py`](../../../aws/org-delegation.py) reads to report on this document: deny it and `DEL-1` reports *denied* and every check below it goes vacuous. The rest was already answered from Identity before this policy existed, because a delegated administrator for any service may read the organization; it is written out so this folder's scope does not depend on a different delegation staying in place |
| `DelegatePolicyLifecycleToIdentity` | The five writes (`CreatePolicy`, `UpdatePolicy`, `DeletePolicy`, `AttachPolicy`, `DetachPolicy`) over seven ARNs in two classes, both required: the targets (`root/o-<org>/r-<root>`, the wildcard `ou/o-<org>/*`, the account wildcard) and the four `policy/o-<org>/<type>/*` ARNs. Create/Update/Delete authorize against the policy ARN and Attach/Detach against target and policy, so a target-only list denies every write on every document, which at the keyboard reads like *"the delegation cannot reach a root attachment"*, the thing step 5.0 measures. The wildcard OU form is required: AWS documents that naming a single OU *"excludes child OUs and accounts under child OUs"*, and this organization is two levels deep. The condition operator is `StringLikeIfExists`: with a bare `StringEquals`, any call that does not carry `organizations:PolicyType` in its request context fails the condition and is denied, producing the same false *"all refused"*. Confinement to the four types is carried by the ARN path. It also carries the `aws:PrincipalArn` condition of the row below |
| `DelegatePolicyTaggingToIdentity` | `TagResource` and `UntagResource`, policy ARNs only, with no `organizationsPolicyType` condition: the two actions do not accept that key, which is why AWS's own tagging example puts them in a separate statement. Nothing needs this today (all ten documents carry zero tags, measured), but the provider's `default_tags` tags an `aws_organizations_policy` at the first apply, and that denial would land on the import, long after step 5.0 had declared the delegation good. Not extended to account, OU or root ARNs: re-tagging the organization's structure is not something this folder needs. It carries the `aws:PrincipalArn` condition of the row below |
| **`aws:PrincipalArn`, on both write statements and on neither read** *(Stage 2 step 5.1a, applied 2026-08-16)* | `ArnLike` on `arn:…:iam::<any account>:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*`. A resource policy's `Principal` is an account and there is no narrower one to write: 5.1 names `arn:aws:iam::<Identity>:root`, which reaches every principal in Identity that also holds `organizations:*` on the identity side, and Control Tower had put a second one there that nobody chose (`AWSOrganizationsFullAccess` → `AWSControlTowerAdmins`, assigned into every vended account). The wildcard account and the trailing `*` are 1c decision 7's, for decision 7's reason: the SSO role suffix is minted per account, so an exact ARN breaks the first time Identity Center re-provisions the role. It is not on `DelegateOrganizationNavigationToIdentity`, which grants nothing the account does not already hold as a delegated administrator of another service. `DEL-10` in [`aws/org-delegation.py`](../../../aws/org-delegation.py) reads both write statements, fails if either lacks the condition, and reports the operator, so a `StringEquals`-shaped regression is visible |

Excluded on purpose: `EnablePolicyType` / `DisablePolicyType` (AWS supports delegating them; they act on
the root, disabling a type detaches every policy of that type at once, and nothing has needed them since
1c step 7.2); the AWS-managed policy ARN class (`arn:aws:organizations::aws:policy/…`) that AWS's CRUD
example carries (this project manages no AWS-managed policy); and `NotAction` / `NotResource`, which AWS
has rejected in delegation policies since 2026-06-30 as incompatible with the allowlist model, so an
exemption-shaped document of the kind used elsewhere in this folder is not available here.

**The blast radius.** AWS's note is that the delegation reaches policies *"created by any account in the
organization, including the management account"*, which includes Control Tower's own guardrail SCPs.
Scoping by policy ARN cannot fix it: this project's policies have no ARN until they are created. This is
the second widening of the Identity account's blast radius, after the group-membership path of 1b step 1,
and the control is not the same one (measured 2026-08-15): 1b step 8.3's alarm fires on a change of group
membership, while the principal this delegation newly reaches (`AWSOrganizationsFullAccess` →
`AWSControlTowerAdmins`, which Control Tower assigns into every vended account, this one included) is
already a member, so its use of the grant raises nothing. What is left is the CloudTrail record alone:
detection after the fact, with no alarm above it. The reach was measured from both sides and the reasoning
is in `docs/ORGANIZATION.md` under the Identity account.

**The narrowing of Stage 2 step 5.1a (applied 2026-08-16).** The document accepts a `Condition` on
`aws:PrincipalArn`, unlike `NotAction`/`NotResource`, which it rejects. The two write statements carry the
`ArnLike` of the row above, so the account-wide `Principal` reaches one role rather than every
administrator in Identity. Two readings measured it, because either alone proves nothing: the same
duplicate `AttachPolicy` against an already-attached pair, inert by construction and verified as attached
immediately before:

| From | Before 5.1a | After 5.1a |
|---|---|---|
| `awsds-ctadmin-orgfull-identity` — `AWS Control Tower Admin`, `AWSOrganizationsFullAccess` | `DuplicatePolicyAttachmentException` | **`AccessDeniedException`** |
| `awsds-infra-identity` — the infrastructure user, `InfrastructureAccess` | `DuplicatePolicyAttachmentException` | **`DuplicatePolicyAttachmentException`** |

The first row alone is indistinguishable from having broken the delegation outright, the failure this
narrowing is most likely to cause and the one that would read as success. The second makes it a narrowing
rather than a revocation. Both readings are evidence only because IAM authorization runs before the
service's duplicate check, proved by the negative control of step 5.0, where the same call from
`awsds-policy-canary` returns `AccessDeniedException`.

**What this does not close.** The account-wide `Principal` still reaches whatever else holds
`organizations:*` in Identity; the condition narrows it, and a condition is a second place a principal is
enumerated (Lesson 14). Anything that must ever write an organization policy (a Stage 8 pipeline role is
the candidate) has to be added to the `ArnLike` list here, and forgetting surfaces as an `AccessDenied` on
an apply, far from this file. The repair for a wrong condition is the Management console (D16).

**2. How it was created and associated with the organization.** Signed in as the **`AWS Control Tower
Admin`** user, permission set **`AWSAdministratorAccess`**, in the **Management** account, the only
Management action in Stage 2 and the only account from which this can be written. Then, in the AWS
Organizations console: **Settings** → the **Delegated administrator for AWS Organizations** section →
**Delegate** → the JSON editor → **Create policy**. The CLI equivalent, not used here, is
`aws organizations put-resource-policy --content file://<document>.json`; either path needs
`organizations:PutResourcePolicy` and `organizations:DescribeResourcePolicy`. AWS also requires the
delegated account's principals to hold the matching identity-based permissions, satisfied here because
`InfrastructureAccess` carries `AdministratorAccess`, so the grant is only ever the resource half. Verify
from the other side, as the infrastructure user through `awsds-infra-identity`:

```bash
./aws/org-delegation.py
```

**3. Why this one document stays outside Terraform.** Any one of three reasons decides it:

1. It lives in Management, and Management is bootstrap-only, "console only, never Terraform"
   (`docs/GENERAL_PLAN.md`, principle 1 and the account map). There is no state bucket, no profile and no
   slice for Management by design: the account whose root user is the break-glass credential (D16) gets no
   automation path.
2. It is this folder's own authorization. A slice that managed the grant it runs under can revoke it in a
   single apply and then be unable to restore it; the recovery would be the Management console, the manual
   step Terraform was meant to remove. It is also why step 5.0 tests this by writing, from the delegated
   account, rather than by reading the document back from the account that wrote it.
3. This is a decision, not a provider gap. `aws_organizations_resource_policy` exists (arguments `content`
   and `tags`, import id `rp-…`). Adopting it would require a Management slice, which reason 1 forbids. If
   principle 1 is ever revisited, that is the resource to use, and this section is the design that would
   move.

**Maintenance.** `check-index.py` iterates `policies/*.json`; this document is not a file there, so nothing
checks these rows against what is attached. They are maintained by reading, in the same sitting as any
change to the delegation, and `./aws/org-delegation.py` re-derives every claim above about actions,
`Resource` classes and the condition.

## What is not in any of these documents

- **The Region restriction** is `CT.MULTISERVICE.PV.1`, a Control Tower managed control enabled per OU
  (decision 6, step 7.7). AWS maintains its `NotAction` exemption list, which already covers the global
  services this project calls from `us-east-1`; a hand-written version would have to keep that list
  complete and would break IAM the first time it fell behind.
- **`AWSControlTowerExecution` carve-outs.** None of the four per-OU documents exempts it; an unnecessary
  carve-out is a hole. **Revision trigger:** a landing-zone update, account update or re-enrollment that
  fails on a compute-creation call in `Data` or `Identity`.
- **Anything protecting the Management account.** SCPs do not apply to it, the asymmetry the break-glass
  path relies on (D16) and the reason a bad `Deny` here is recoverable.

## The AWS documentation for the actions named here

Two sources per service answer different questions. The *Service Authorization Reference* page describes
what each action grants, its resource types and its condition keys; the machine-readable service reference
is the same list as JSON, which a script can diff (it answered verification (viii)) and the only source
that says what an action is called today.

| Service | Actions used here | Reference | Machine-readable |
|---|---|---|---|
| Amazon S3 | `PutObject*`, `DeleteBucket`, `PutAccountPublicAccessBlock` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html> | `https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json` |
| Amazon ECR | `InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`, `PutImage` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerregistry.html> | `…/v1/ecr/ecr.json` |
| Amazon ECR Public | `ecr-public:*` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerregistrypublic.html> | `…/v1/ecr-public/ecr-public.json` |
| Amazon EC2 | `RunInstances`, `StartInstances`, `CreateFleet`, `RequestSpotInstances`, `RequestSpotFleet`, `ModifySnapshotAttribute`, `ModifyImageAttribute`, `CreateStoreImageTask`, `ExportImage`, `CreateInstanceExportTask` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonec2.html> | `…/v1/ec2/ec2.json` |
| Amazon RDS | `ModifyDBSnapshotAttribute`, `ModifyDBClusterSnapshotAttribute`, `StartExportTask` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonrds.html> | `…/v1/rds/rds.json` |
| AWS IAM | `CreateUser`, `CreateAccessKey` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_identityandaccessmanagement.html> | `…/v1/iam/iam.json` |
| AWS Organizations | `LeaveOrganization` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsorganizations.html> | `…/v1/organizations/organizations.json` |
| Amazon GuardDuty | `DeleteDetector`, `UpdateDetector`, `DeleteMembers`, `DisassociateMembers`, `StopMonitoringMembers`, `DisassociateFromMasterAccount` and `DisassociateFromAdministratorAccount` (both spellings exist), `DeletePublishingDestination`, `UpdatePublishingDestination` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonguardduty.html> | `…/v1/guardduty/guardduty.json` |
| Amazon DataZone (the SMUS control plane) | `CreateDomain`, and the whole namespace in `Workloads` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazondatazone.html> | `…/v1/datazone/datazone.json` |
| Amazon SageMaker | `CreateDomain`, `CreateUserProfile`, `CreatePresignedDomainUrl`, `CreateSpace`, `CreateApp`, `StartSession`, `CreateNotebookInstance`, `CreatePresignedNotebookInstanceUrl`, `Create*` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonsagemaker.html> | `…/v1/sagemaker/sagemaker.json` |
| AWS Glue | `CreateDevEndpoint`, `CreateJob`, `StartJobRun`, `CreateSession`, `RunStatement`, `CreateMLTransform`, `StartNotebook`, `StartCrawler`, `StartCrawlerSchedule`, `StartColumnStatisticsTaskRun(Schedule)` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsglue.html> | `…/v1/glue/glue.json` |
| AWS Lake Formation | `DeregisterResource` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awslakeformation.html> | `…/v1/lakeformation/lakeformation.json` |
| AWS Lambda | `CreateFunction` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_awslambda.html> | `…/v1/lambda/lambda.json` |
| Amazon ECS | `RegisterTaskDefinition`, `RunTask`, `CreateService` | <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerservice.html> | `…/v1/ecs/ecs.json` |

The condition keys these documents turn on are `aws:PrincipalArn`, `aws:ResourceOrgID`,
`aws:PrincipalOrgPaths` and `aws:PrincipalIsAWSService`, with the `…IfExists` and `ForAllValues:`
operators. Each evaluates true when its key is absent, which is where these documents fail silently:

- Global condition context keys: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html>
- Condition operators, including `…IfExists` and the set operators: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html>
- Service control policies — syntax, inheritance and evaluation: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html>
- Service reference information (the machine-readable index): <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_service-reference.html>

---

*Documents: [`README.md`](README.md) · Stage: [1c step 7](../../../docs/plan/stages/stage-01c-preventive-policies.md) ·
Probes: [`docs/plan/runbooks/scp-battery.md`](../../../docs/plan/runbooks/scp-battery.md) · Policy ids and dates:
[`docs/log/log-stage-01c-preventive-policies.md`](../../../docs/log/log-stage-01c-preventive-policies.md)*
