# AWS_SUPPLEMENT.md — what AWS and its tooling do that their documentation does not state

This file supplements the vendor's documentation. An entry is a behaviour of an AWS service, of
Terraform and its providers, or of a tool this estate runs against AWS, that the documentation does
not state, states incompletely or contradicts, and that this project learned by a measurement. The
lessons in [`plan/lessons.md`](plan/lessons.md) are habits; the entries here are facts about the
platform.

Read the section of a service before designing around a behaviour of it that nobody here has measured.
Search the file when an error names the wrong cause, a call answers against its page, or a plan
refuses to converge. Add an entry in the sitting that measures a new behaviour.

## Rules for an entry

- **What belongs.** A behaviour the documentation does not state, or states somewhere the person who
  needed it would not have been reading. A documented behaviour that was merely unread belongs in the
  file that owns it (`plan/conventions.md`, a runbook, a stage). Two candidates were excluded by that
  rule: `iam list-roles` omitting `PermissionsBoundary`, a documented contract, and ECR's
  `tagPatternList` accepting wildcards, which the page says. This project's own design is not an entry
  either; the platform behaviour that forced it is.
- **Evidence.** An entry says what was measured or read, when, and where the reading lives. A behaviour
  recorded without its evidence is indistinguishable from a belief (Lesson 37). "Measured" is a call
  that was made and answered; a reading of a trail, of a service model, of a console's code or of a
  vendor page says so.
- **Form.** `SUP-nnn`, then the behaviour as one bold sentence, subject first; how and when it was
  learned; the identifiers and the error text verbatim; what the vendor's page says or omits; the
  consequence; and `Where:`, the log, runbook or code that holds the reading.
- **Identifiers.** A `SUP-nnn` id is never reused and never renumbered, so other files cite an entry by
  it. A new entry takes the next free number and goes at the end of its section or subsection, whatever
  its date.
- **Corrections.** A later reading that extends or contradicts an entry is appended to it with its own
  date, and the title is brought to what is true now. An entry that turned out wrong is rewritten to
  say what was measured and what it was mistaken for; it is never removed in silence.
- **Placement.** An entry lives under the service whose behaviour it is. A Terraform or CLI behaviour
  that is one service's quirk stays under that service, and [Terraform](#terraform) points at it.
- **Candidates.** The signatures an entry leaves in a stage log: an error message naming the wrong
  cause, a call answering differently before and after another act, a field that writes and never
  reads, an object that survives its delete, a bill starting at a state nobody named.

## Searching this file

- **By service**: the sections below.
- **By API, resource type or error text**: entries keep them verbatim, so
  `grep -n -i 'PendingCheckout' docs/AWS_SUPPLEMENT.md` finds the entry.
- **Every title**: ``grep -n -A1 '^- `SUP-' docs/AWS_SUPPLEMENT.md``.

`./scripts/check-aws-supplement.py` holds the mechanical half: the ids are unique, every `SUP-nnn`
another file cites exists here, and the sections of this file are the ones `CLAUDE.md` indexes. Whether an
entry is still true is the reading.

## Sections

| Section | Its entries cover |
|---|---|
| [IAM and STS](#iam-and-sts) | The policy simulator's blind spots; validation before authorization, action by action; `sts:AssumeRole` refusals under an SCP; condition keys that do not populate; Access Analyzer's findings; revisions of AWS-managed policies |
| [IAM Identity Center](#iam-identity-center) | SSO tokens and the CLI's cache; `GetRoleCredentials` *No access*; the reserved roles' trust policy under an RCP; calls the delegated administrator answers |
| [Organizations and Control Tower](#organizations-and-control-tower) | Which SCP an error names; Control Tower's guardrail documents and its Region-deny control; delegation policies; declarative policies; reads from a member account; account updates and renames |
| [Security Hub and Config](#security-hub-and-config) | Central configuration and its pause; the delegated administrator's side effects; the CSPM meter; the configuration items an endpoint cycle records |
| [CloudTrail](#cloudtrail) | What an event names and omits; `lookup-events`' blind spots; the door a call took; cross-account and global-endpoint records; network activity events; CloudTrail Lake |
| [CloudWatch and Service Quotas](#cloudwatch-and-service-quotas) | Aggregates and their windows; `AWS/Usage`; log groups under a customer key; log groups the services create; quotas applied, raised and refused |
| [EventBridge](#eventbridge) | EventBridge Scheduler's context attributes under `jsonencode` |
| [EC2](#ec2) | Elastic IP transfers; descriptions EC2 refuses; instance type changes and first boot; an instance profile at boot; AL2023's zram and a first boot's dnf memory |
| [Systems Manager](#systems-manager) | State Manager associations; the agent's registration; Parameter Store's reserved and public names |
| [VPC and Route 53 Resolver](#vpc-and-route-53-resolver) | Interface endpoints' DNS names, private zones and readiness; gateway endpoints and S3's names; DNS Firewall's CNAME chains; the Resolver query log |
| [ECR](#ecr) | A pull through endpoints; the pull-through cache; ECR Public's redirect |
| [S3](#s3) | S3 Access Grants: the request charge, the lag of a delete, the instance and the plugin SageMaker Unified Studio brings; the wording of a refused read |
| [Glue](#glue) | Resource policies; crawlers under a security configuration; a job's sessions; lineage without an endpoint; federated databases |
| [Lake Formation](#lake-formation) | Data lake settings and who writes them; listings that omit grants; cross-account shares, vends and their flags; the creator's permissions; Athena writes through vended sessions; RAM |
| [Athena](#athena) | Workgroup deletion; SCP refusals that name no policy; Athena Spark's network; an Iceberg table's rename |
| [Redshift Serverless](#redshift-serverless) | Namespace, workgroup and usage limits; SQL, users and privileges; the Data API; datashares through Lake Formation; billing, metrics, the free trial and the audit export |
| [DataZone and SageMaker Unified Studio](#datazone-and-sagemaker-unified-studio) | The domain and its account association; blueprints, profiles and policy grants; environments, and what a project creates and leaves; the project role's managed policies; the portal; catalog, data sources and subscriptions; connections; the Bedrock IDE's knowledge bases, guardrails, evaluations, chat agents and flows |
| [SageMaker AI spaces and images](#sagemaker-ai-spaces-and-images) | Custom images and their versions; spaces, apps and their network identity; the Code Editor, the remote IDE, its clients and Amazon Q |
| [SageMaker AI jobs and models](#sagemaker-ai-jobs-and-models) | Processing jobs: status, mounts, keys and image pulls; condition keys on the job creates; models and model packages |
| [MWAA](#mwaa) | MWAA Serverless workflows, their API and KMS use; workers, templates, tasks and the Airflow operators; provisioned MWAA |
| [The SMUS CI/CD CLI](#the-smus-cicd-cli) | `aws-smus-cicd-cli` 1.0.9: manifests and their variables, bundles, workflow names, the pre-deployment validation, what `deploy` reads and creates |
| [Bedrock](#bedrock) | Inference profiles and their authorization; retention modes; agreements and the use-case form; CloudTrail and CloudWatch for invocations |
| [Terraform](#terraform) | `validate`, `init`, locks and credentials; the `aws` provider's read-backs, drift and replacements; `awscc` and Cloud Control; checkov |
| [The AWS CLI](#the-aws-cli) | `--query` under pagination; a global flag that shadows a parameter; a `file://` document in a list parameter |
| [Clients and the egress proxy](#clients-and-the-egress-proxy) | WireGuard on macOS and Linux; Chrome's Local Network Access; Squid's matching and refusals; VS Code and Open VSX behind a proxy |

## IAM and STS

- `SUP-001` **Whether an API validates its input before it authorizes is a property of the action, not of
  the service** (measured 2026-08-13 to 2026-10-26, Stage 1c 7.5a and later stages). Authorized first, so an
  invented id reaches the deny: `ec2:ExportImage` and `ec2:CreateInstanceExportTask` with a malformed AMI
  id, `ec2:ModifyImageAttribute`, `ec2:CreateFleet --dry-run` before resolving its launch template,
  GuardDuty's `DisassociateFromAdministratorAccount`, `UpdateDetector` and `StopMonitoringMembers` on an
  invented detector id, `glue:StartCrawler` (2026-08-19), `athena:StartQueryExecution` (2026-08-20) and
  `redshift-serverless:DeleteUsageLimit` (2026-09-20). Validated first, so the deny is never reached:
  `ec2:ModifySnapshotAttribute` (`InvalidSnapshotID.Malformed`, `--dry-run` included), `ec2:RunInstances
  --dry-run` (`InvalidAMIID.Malformed`, `InvalidAMIID.NotFound`, `VPCIdNotSpecified`),
  `ec2:CreateStoreImageTask` until given a real public AMI, `ec2:StartInstances` (`Malformed` at 17
  characters, `NotFound` at 8), S3 on a missing bucket (`NoSuchBucket`),
  `redshift-serverless:UpdateWorkgroup` (`ResourceNotFoundException`), `redshift-data:ExecuteStatement` with
  no workgroup (*"Redshift endpoint doesn't exist in this region"*, 2026-10-23), `datazone:CreateDomain`,
  and ARNs carrying a placeholder account: `airflow:CreateEnvironment` (*"Cross-account pass role is not
  allowed"*) and `sns:Publish` (*"Invalid namespace"*). A first validation error is a reason to retry with a
  resource that exists. Where: `log-stage-01c-preventive-policies.md`; `runbooks/scp-battery.md`;
  `log-stage-03-networking.md`, 2026-08-16; `log-stage-05a-data-foundation.md`, 2026-08-19;
  `log-stage-09-deployment-targets.md`, 2026-10-23 and 2026-10-26;
  `log-stage-10-orchestration-promotion.md`, 2026-10-23; `aws/probes/probes.py`; `POLICIES.md`. Readings of
  single actions: `SUP-279`, `SUP-243` and `SUP-298`.

- `SUP-002` **AWS's machine-readable service reference maps `aws:RequestTag` to none of EC2's 793 actions,
  though EC2 declares the key and `ec2:RunInstances` honours it on `instance/*`** (read 2026-08-13 in the
  service reference, measured 2026-08-14, Stage 1c 7.8). The same reference maps `aws:RequestTag` and
  `aws:TagKeys` to `s3:CreateBucket`, 1 of 11 S3 actions, and to `rds:CreateDBInstance`, so its silence on
  EC2 is a gap in the instrument, not a fact about EC2. The tag-enforcement SCP, one `Null` statement each
  on `aws:RequestTag/Environment` and `aws:RequestTag/Project` with `Resource` `arn:aws:ec2:*:*:instance/*`,
  passed the battery's six tag rows: untagged and single-tag `RunInstances --dry-run` denied, fully tagged
  left at `DryRunOperation`. With `Resource: "*"` every launch would be denied, because the key does not
  populate for the subnet, security group, image, volume or network interface the call references; that half
  is read, not measured. Where: `log-stage-01c-preventive-policies.md` 7.8, 2026-08-13 and 2026-08-14;
  `POLICIES.md` `awsds-org-scp-tag-enforcement`; `runbooks/scp-battery.md`.

- `SUP-003` **An organization-type IAM Access Analyzer reports every `AWSReservedSSO_*` role as
  `ExternalAccess`, one finding per assignment-backed permission set per account** (read 2026-08-15,
  2026-10-17 and 2026-10-21 in Audit's snapshot, Stage 1d and Stage 11 2.1.1). The count follows the
  assignments: 35 findings on 2026-08-15, 45 active on 2026-10-17 (Management 5, Audit 3, Log Archive 3,
  Policy Canary 4, Identity 4, Data Governance 5, Production 7, Sandbox 7, Staging 7) and 45 again on
  2026-10-21. The roles trust each account's Identity Center SAML provider, which the project infers the
  organization zone of trust counts as external. A removed assignment's finding turns `RESOLVED` and stays
  listed, as two Staging roles did after their assignments were removed on 2026-09-06. These findings are a
  baseline that moves with the assignments; a finding of another shape, or a count moving with no assignment
  change, is the signal. Where: `log-stage-11-dlp.md`, 2026-10-17 and 2026-10-21; `docs/AWS_STATE.md`
  `INV-10`, `INV-16`.

- `SUP-004` **A permission set's `aws:SourceIp` deny is evaluated at each service call, never when Identity
  Center vends the role credential** (measured 2026-08-17, Stage 4 step 8, verifications (iv) and (vi)).
  With a deny on `aws:SourceIp` in the persona permission sets, five roles across three accounts, off the
  allowed address, held a role credential: `sso:GetRoleCredentials` succeeded and the CLI printed the role
  ARN, and the call that followed was refused *"with an explicit deny in an identity-based policy"*. A
  credential minted inside the tunnel does not survive leaving it. Signing in to the access portal works off
  the allowed network, and the console loads and navigates; only the API calls behind each screen are
  denied. A stolen session off that network yields which accounts exist, which roles are held and which
  screens exist, and no call that returns data. Where: `log-stage-04-vpn.md`, 2026-08-17. The portal's half
  is `SUP-180`.

- `SUP-005` **AWS revises the SageMaker Unified Studio managed policies on project roles every few weeks,
  and nothing in the account announces it** (read 2026-08-23 to 2026-10-30 with `iam get-policy`, Stage 6a,
  Stage 17 0.1, open question 22). `SageMakerStudioProjectProvisioningRolePolicy` went from v81 (read
  2026-08-23) to v82 by 2026-08-26, `SMAppDelete` becoming `SMApp` with `sagemaker:CreateApp` and `AddTags`
  and its resource widened from four literal app-type ARNs to `arn:aws:sagemaker:*:*:app/*`, then to v84
  (2026-10-12). `SageMakerStudioProjectUserRolePolicy` moved v74, v75 (2026-08-27), v76 (2026-10-29);
  `SageMakerStudioProjectRoleMachineLearningPolicy` v42, v45 (2026-10-14), v47 (2026-10-29). The diffs of
  2026-08-26 and 2026-10-17 removed no permission. On 2026-10-17 IAM served v45 while AWS's reference page
  still showed v44 (edited 2026-09-14) and the admin guide's update table named no change after 2026-06-25.
  The project records no CloudTrail event for a revision (stated, not measured), so the instrument is
  pulling `DefaultVersionId` and `UpdateDate` and diffing `get-policy-version`. Read again 2026-11-14 in
  Sandbox with `iam list-policy-versions`: the user role policy v77 and the machine learning policy v48, both
  of 2026-11-13 20:47 UTC, the provisioning policy v85, of 20:07 UTC, and
  `SageMakerStudioDomainExecutionRolePolicy` v24 to v27, between 2026-11-04 and 2026-11-12; no action was
  dropped from any of them. AWS's reference pages, read at 20:02 UTC on 2026-11-13, showed v76, v47 and v84,
  and still did at 02:48 UTC on 2026-11-14, six hours after IAM listed the new versions. The admin guide's
  document history carried entries for v77 and v48 by then, dated 2026-11-13, and none for v85 nor for the
  domain execution policy's v24 and v26. Where: `open-questions.md`
  question 22; `log-stage-06a-unified-studio.md`, 2026-08-23; `log-stage-17-sandbox-machine-learning.md`,
  2026-10-17; `upstream-releases.md`, the SageMaker Unified Studio table.

- `SUP-006` **`iam simulate-custom-policy` refuses any input policy longer than 2,000 characters** (measured
  2026-09-11, Stage 6e step 3.1). Called with two SageMaker Unified Studio policy documents, 4,720 and
  54,912 bytes compacted, it answered *"Value at 'policyInputList' failed to satisfy constraint: Member must
  have length less than or equal to 2000"*. A project role's identity layer therefore cannot be simulated in
  isolation with this call; the same day `simulate-principal-policy` from the member account returned the
  organization's false `explicitDeny`, so the grant analysis was a reading of the documents statement by
  statement. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-09-11.

- `SUP-007` **IAM Access Analyzer reads a KMS key policy statement granting `Principal: {"AWS": "*"}` as
  public until it carries `aws:PrincipalOrgID`, whatever its tag, service and encryption-context
  conditions** (read 2026-10-17 and 2026-10-18 with `get-finding-v2`, resolved 2026-10-21, Stage 11 2.1.1).
  The Sandbox project key `alias/awsds-sandbox-project` held `GrantKMSPermissionsForAllProjectRoles`
  (`kms:GenerateDataKey`, `kms:Decrypt` through DataZone for a caller tagged `AmazonDataZoneDomain`) and
  `AllowCreateGrantForProjectRoles` (`kms:CreateGrant` under the domain's encryption context). The finding
  read their union of actions, `isPublic: true`, `condition: {}` and `resourceControlPolicyRestriction:
  APPLICABLE`; AWS's `ExternalAccessDetails` reference says an external finding does not weigh an RCP. After
  `aws:PrincipalOrgID` joined both statements' `StringEquals` (applied 2026-10-19), the Audit snapshot of
  2026-10-21 23:42:59Z read the finding `RESOLVED`. No AWS page read said how the analyzer weighs a key's
  conditions, and AWS's key permissions for the Tooling blueprint give both statements without an account or
  organization condition and do not mention the analyzer. Where: `log-stage-11-dlp.md`, 2026-10-17,
  2026-10-18 and 2026-10-21; `threat-model.md` `TM-21`.

- `SUP-008` **`iam simulate-principal-policy` reads the Control Tower Region ceiling as an explicit deny for
  every regional action unless the context names `aws:RequestedRegion`** (measured at Stage 11 pass 0,
  2026-10-18). Without the key, `sns:Publish` and `glue:GetDatabases` from a Sandbox project role return
  `explicitDeny` with `AllowedByOrganizations: false`, and `MissingContextValues` stays empty, since it
  lists the identity policies' keys and not the SCPs'. With `--context-entries
  ContextKeyName=aws:RequestedRegion,ContextKeyValues=us-west-2,ContextKeyType=string` the same calls read
  the identity layer. Stage 6e 3.1a recorded the first shape as the organization verdict being unusable from
  a member account. Where: `log-stage-11`, 2026-10-18. Two more readings of the same day: while the
  organization denies, the result names no identity statement, so the identity layer under an SCP deny is
  read by forcing the SCP's carve-out into the context; and the SCP evaluation reads `aws:PrincipalArn` as
  the role's own ARN when the context gives none, a key the simulator's page does not list among those it
  populates. Where: `log-stage-06h`, 2026-10-18. Read again on 2026-10-25 in Production, where
  `redshift-data:ExecuteStatement` and `sagemaker:DescribeModelPackage`, both working calls, read
  `explicitDeny` until the context named the Region (`log-stage-09`). The perimeter SCP's
  `DenyS3ObjectWriteOutsideOrganization` reads the same way while the context lacks `aws:ResourceOrgID`, its
  `StringNotEqualsIfExists` matching the absent key: Staging's deploy role read `explicitDeny` on
  `s3:PutObject` to its own orchestration state, which it writes at every leg, and with the organization's
  id in the context `allowed` there and `implicitDeny` on the egress state (`log-stage-08`, 2026-10-25).
  Read 2026-10-18 in Production (Stage 8 verification xxi): a bucket policy is evaluated only when passed as
  the resource policy with a simulated IAM user as the caller, `aws:PrincipalArn` then appears to come from
  the context rather than from that user (inferred from the `InfrastructureAccess` contrast), and no KMS key
  policy is evaluated (`log-stage-08`, 2026-10-18). On 2026-10-25 a role named as principal in Production's
  model-package group policy could not be evaluated at all, so that cross-account read was proved by a call
  (`log-stage-09`, 2026-10-25). On 2026-10-26 the debug role's `kms:Decrypt` read `implicitDeny` through
  `logs` and through S3 alike, the S3 condition false for want of `kms:ResourceAliases` in the simulated
  context, while the same role's read of a job log stream under that key succeeded the same day
  (`log-stage-09`, 2026-10-26). A role's own tags are not read as `aws:PrincipalTag/*` either (measured
  2026-11-11 on Production's project role, Stage 19): `s3:GetObject` and `PutObject` on the project's own
  prefix read `implicitDeny` until the context carried each tag of the role as `aws:PrincipalTag/<key>`,
  and `MissingContextValues` named none of them among the keys it listed. A policy written on principal
  tags, as AWS's project-role policies are, is simulated with the tags supplied or reads closed
  (`log-stage-19-smus-native-data-product.md`, 2026-11-11). The same day a boundary's next version was
  rehearsed before its apply by passing the planned document as
  `--permissions-boundary-policy-input-list`: 40 decisions as that role read the same under the planned
  document and, after the apply, under the attached boundary, the matched statement's
  `SourcePolicyId` being `PermissionsBoundaryPolicyInputList.1` in the first and the policy's name in
  the second. The simulator supplies no `kms:ResourceAliases`: that boundary's deny on every key whose
  aliases are not the excepted one, a `ForAllValues:StringNotLike`, read `explicitDeny` on the excepted
  key itself until the context carried the key's alias, the operator being true over an absent key.
  A resource named for an action can close a statement whose `Resource` is `*` (measured 2026-11-14 on
  Sandbox's bundle role, Stage 19): with `--resource-arns` naming the domain's ARN, `datazone:GetProject`,
  `ListConnections`, `Search` and `GetAsset` read `implicitDeny` under an allow on `*`, while
  `GetDomain`, whose statement names the domain, read `allowed`; with no resource named the same four
  read `allowed` by that statement (`log-stage-19-smus-native-data-product.md`, 2026-11-14). A statement
  naming a resource is never applied to an action the Service Reference gives no resource type (measured
  2026-11-17 on Production's deployment project role, Stage 19): with the domain's ARN, in the Data
  Governance account or rewritten to the caller's, `datazone:StartDataSourceRun`, `CreateDataProduct`,
  `CreateDataProductRevision` and `DeleteDataProduct` read `implicitDeny` naming no statement and carrying
  no organization or boundary detail, while `GetDomain` read `allowed`; with no resource named, the
  organization and the boundary read `true` and the four `implicitDeny`, a statement on the domain matching
  no `*`. `StartDataSourceRun` runs under the same form of statement (`SUP-346`), so a grant of such an
  action on the domain is read from its call (`log-stage-19-smus-native-data-product.md`, 2026-11-17).
  Read again 2026-11-20 on `eighth-experimentation`'s project role: `datazone:StartNotebookRun`,
  `ListNotebooks`, `GetNotebook` and `CreateNotebook` read `implicitDeny` with the domain's ARN in either
  account and `allowed` with no resource named, through `SageMakerStudioProjectRoleMachineLearningPolicy`'s
  `datazone:*Notebook*` (`log-stage-06d-unified-studio-remainder.md`, 2026-11-20). A key policy is evaluated
  once each statement's `Resource` is rewritten from `*` to the key's ARN, and refused as written (measured
  2026-11-21 in Sandbox, Stage 6a): passed as `--resource-policy` with `Resource` `*`, the call answered
  `InvalidInput`, *"ResourceNames are not in a valid ARN format: *."*; rewritten, a project role's
  `kms:GenerateDataKey` and `kms:Decrypt` through S3 read `allowed`, `ResourcePolicy` among the matched
  statements beside AWS's two project-role policies, the context carrying the Region, the organization,
  `kms:ViaService`, the encryption context and the role's `KmsKeyId` tag
  (`log-stage-06a-unified-studio.md`, 2026-11-21).

- `SUP-009` **`iam simulate-custom-policy` ignores `sagemaker:VolumeKmsKey` and `sagemaker:OutputKmsKey`
  when the resource is a job's ARN** (measured 2026-10-18, 6d step 1.3). A `Deny` on `Null` of either key
  matched a `CreateProcessingJob` or `CreateTrainingJob` that supplied the key against `processing-job/…` or
  `training-job/…`, and did not match against `*`; `sagemaker:VpcSubnets` was read both ways. The real call
  reads the key: 6i's four jobs carried `VolumeKmsKeyId` past the boundary's copy of the same deny. A
  simulation of a job's settings runs with the default resource `*`. Where: 6d step 1.3. Read again
  2026-10-24 for `CreateTransformJob` against `transform-job/…`, in `simulate-principal-policy` through the
  live `Workloads` document too (`log-stage-10`, 2026-10-24). Read again 2026-11-17 in Staging, an allow-all
  and one `Null` deny against `processing-job/…`, `training-job/…` and `transform-job/…`: a deny on
  `sagemaker:VolumeKmsKey` read `explicitDeny` whichever of the two keys the context carried, and one on
  `sagemaker:VolumeKmsKeyArn` read `allowed` with that key passed, so against a job's ARN the simulator
  honours the reference's name alone, while the service fills `VolumeKmsKey` (`SUP-239`;
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-17).

- `SUP-010` **An SCP's deny on `sts:AssumeRole` does not show behind the refusal of a role that does not
  exist** (measured 2026-10-27, Stage 8 decision 29, in `Policy Canary`). With
  `DenyDeployRoleAssumptionOutsideTheRegion` attached, an `AssumeRole` of `awsds-deploy-battery-probe`,
  which exists nowhere, through `sts.amazonaws.com` answered STS's plain *"not authorized to perform:
  sts:AssumeRole on resource"* for ten minutes, the wording of before the apply, and CloudTrail recorded
  that message in `us-east-1`, while the IAM simulator read the same call `explicitDeny`. A battery row
  built on a role that does not exist, the shape that measures most other denies here, cannot measure one on
  `sts:AssumeRole`; a caller the role trusts can. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-27.

- `SUP-011` **STS's refusal text does not always name the SCP behind an `sts:AssumeRole` deny; an
  authorization id can** (measured 2026-10-30, Stage 8 decision 29, in Production). An `AssumeRole` of `awsds-deploy-prod`,
  which exists and trusts the runner alone, through `sts.amazonaws.com` answered the plain *"not authorized
  to perform: sts:AssumeRole on resource"* and an authorization id, where AWS's page shows a denial naming
  the policy type and ARN in its text. `aws iam-toolbox get-request-authorization-details --region
  us-east-1` on the id named `DenyDeployRoleAssumptionOutsideTheRegion` as the matched deny,
  `EXPLICIT_DENY`. The same call through `sts.us-west-2.amazonaws.com`, refused by the trust alone, carried
  no id, nor did the 21 global refusals of a role that exists nowhere on 2026-10-27: whether a missing role,
  the deny's kind or the preview's rollout withholds the id, these readings do not separate. The details are
  kept 24 hours and read in the Region of the denial. Nor does every refusal carry one: the battery's same
  call 15 minutes later, at 06:25:03, carried none. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-30.
  Read again 2026-11-15 with the runner's role as the caller, which both deploy roles trust (`awsds/dev-env`
  pipeline #118): both global refusals read *"with an explicit deny in a service control policy:
  arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/p-1fp032g8"*,
  then a console link in `us-west-2` and an authorization id, in the job's output and in the `us-east-1`
  record's `errorMessage`, whose `requestParameters` is null. The text names the policy, never its
  statement; the two readings differ in caller and date, so they do not separate a trust that also refuses
  from a change in STS. Where: `log-stage-08-cicd-pipelines.md`, 2026-11-15.

## IAM Identity Center

- `SUP-012` **An `AWSReservedSSO_*` trust policy permits only `sts:AssumeRoleWithSAML` and
  `sts:TagSession`**, so an RCP denying those actions locks every SSO user out of every member account.
  Measured at Stage 1c step 7.8; AWS's own `CT.STS.PV.1` carries the exclusion note, which is why no `sts:`
  action is added to that document without reading it first. The mechanism, measured 2026-08-14 at Stage 1c
  7.8: the RCP statement `EnforceOrgIdentitiesOnRoleAssumption` denied `sts:AssumeRole`,
  `AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity`, `SetSourceIdentity` and `TagSession` under
  `StringNotEqualsIfExists` on `aws:PrincipalOrgID`; a SAML assertion carries no AWS credentials, so the key
  does not populate and `IfExists` turns the absence into a match. Every profile in all six member accounts
  failed at once with *"ForbiddenException ... GetRoleCredentials: No access"* while the console on
  Management, which RCPs do not reach, kept working, and detaching the document from the root restored
  access immediately. The lockout is latent: a vended role credential lives 4 h in `~/.aws/cli/cache`, so
  probes run right after the attach passed on a session minted before it; `rm -f ~/.aws/cli/cache/*.json`
  forces a fresh vend. Where: `log-stage-01c-preventive-policies.md` 7.8, 2026-08-14;
  `runbooks/scp-battery.md`; `POLICIES.md` `EnforceOrgIdentitiesOnRoleAssumption`.

- `SUP-013` **`ForbiddenException` on `GetRoleCredentials` with *"No access"* has two opposite causes, and
  only Identity Center's listing of the token's roles tells them apart** (measured 2026-08-14 and
  2026-08-20, Stage 1c 7.8 and Stage 5a). On 2026-08-14 an RCP denying the SAML flow's STS actions made
  every member-account profile fail with *"An error occurred (ForbiddenException) when calling the
  GetRoleCredentials operation: No access"* while Management still answered. On 2026-08-20 the same sentence
  came back with a token valid for another hour: the browser had re-approved the device authorization
  against another user's live portal session, so `aws sso login --sso-session awsds` reported success and
  that user's token held the session's slot. `sso:ListAccounts` and `sso:ListAccountRoles` with the cached
  token never traverse STS, so no SCP or RCP shapes them: a role assigned and refused is the policy, a role
  not assigned is the wrong identity, whose remedy is `aws sso logout`, not another login. The exit code
  separates neither from an expired token. Where: `log-stage-05a-data-foundation.md`, 2026-08-20;
  `log-stage-01c-preventive-policies.md` 7.8, 2026-08-14; `runbooks/scp-battery.md`; `aws/AWS-CLI.md`, "One
  session per person".

- `SUP-014` **A cached SSO token is keyed by the `sso-session` name, never by the user**, so signing in as a
  second identity silently reuses the first one's token. The remedy is `aws sso logout` plus a portal
  sign-out; the failure mode is a command that succeeds as the wrong person (`aws/INDEX.md`).

- `SUP-015` **`aws sso logout` invalidates every cached session's token, and a browser sign-out of the
  access portal invalidates none** (measured 2026-09-07/08). The infrastructure token died at
  `GetRoleCredentials … 401` right after the user's `aws sso logout`, while the CLI kept answering for
  profiles whose role credentials were already cached locally; Terraform, which exchanges the token itself,
  noticed first. The same night the Data Scientist's token survived the user signing out of the portal in
  the browser and signing in again as the infrastructure user. Two people's sessions coexist on one laptop
  as long as nobody types `aws sso logout`, and the browser's portal session decides whose token a login
  mints (the `ForbiddenException` at `GetRoleCredentials`). Where: `aws/AWS-CLI.md`.

- `SUP-016` **The portal's session ended twice right after another Identity Center user's CLI login** (seen
  2026-10-11, Stage 6i). Each time the user had just signed in to the CLI as the infrastructure user while
  Chrome held the Data Scientist User's portal session, and the next portal act landed on the sign-in page.
  The shared browser is the inferred cause, not an isolated one. Where: `aws/AWS-CLI.md`, "Signing in". The
  same shape reached the CLI on 2026-10-25: a minute after the Data Scientist User's CLI sign-in (19:45
  UTC), answered in the shared browser, the infrastructure user's token no longer loaded, *"Error loading
  SSO Token: Token for awsds does not exist"* (19:46:59), while the persona's token was untouched. On
  2026-10-26 the persona signed in with `--no-browser` and answered the code outside the shared browser, and
  the infrastructure user's token survived (`get-caller-identity` at 01:01:19). On 2026-10-24 a
  `--no-browser` sign-in whose answering browser the log does not name was followed by the same error, so
  the browser that answers the code is the variable, not the flag; each reading was seen once. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-24, 2026-10-25 and 2026-10-26.

- `SUP-017` **`sso-admin list-account-assignments-for-principal` answers from the Identity Center delegated
  administrator**, where its API reference says the action *"must be called from the management account"*
  (measured 2026-10-18 as `InfrastructureAccess` in Identity, Stage 14: the shared data-scientist group's
  three assignments). One call per principal replaces the walk over every permission set and account that
  `./aws/list-identities.py` makes, and `./aws/vending.py` `VN-6` rests on it: the day the page is enforced,
  that check fails on a refused call, never on an empty list. Where: `log-stage-14-sandbox-vending.md`,
  2026-10-18.

## Organizations and Control Tower

- `SUP-018` **An account that is a delegated administrator for any service answers Organizations reads over
  the whole organization, and the same permission set in an ordinary member account answers two calls**
  (measured 2026-08-12 and 2026-08-15, Stage 2 open question 11). In Identity, the IAM Identity Center
  delegated administrator, `AWSOrganizationsFullAccess` answered eleven reads with `exit=0`: every account,
  the OU tree, every SCP and the full `Content` of one; `describe-policy` had already answered there on
  2026-08-12, before any Organizations policy delegation existed. The same user and permission set in an
  ordinary vended account answered `describe-organization` and its own `describe-effective-policy`, while
  `list-roots`, `list-accounts`, `list-organizational-units-for-parent`, `list-policies`, `describe-policy`,
  `list-targets-for-policy`, `list-parents` and `describe-account` returned `AccessDeniedException`. The
  surface belongs to the account, so every principal there holding `organizations:*` inherits it, and a
  successful read from it proves nothing about a policy delegation. Where:
  `log-stage-02-terraform-foundation.md`, 2026-08-15; `aws/org-delegation.py` header; `aws/INDEX.md`.

- `SUP-019` **`describe-effective-policy` answers `{}` rather than raising when the policy type is `ENABLED`
  and nothing is attached** (measured at Stage 1c). A reader expects `EffectivePolicyNotFoundException`, and
  it does not arrive, so *"no policy in force"* and *"an empty policy in force"* are one reading. Any check
  written against this call needs a second signal.

- `SUP-020` **When several attached SCPs deny the same call, the error names one of them, so a document can
  be attached and never exercised** (measured 2026-08-13, Stage 1c steps 7.6 and 7.7). An SCP denial's CLI
  error ends with *"with an explicit deny in a service control policy:
  arn:aws:organizations::…/service_control_policy/p-…"*, readable with no CloudTrail lag. With four
  candidate documents on one account, `p-tgda7n58` decided no probe because other documents also denied its
  actions; moved to an OU where nothing else denied `CreateNotebookInstance`, it was proven in one call. In
  Sandbox Account 1 a Region deny named the parent OU's `p-umksvu5a` although `Sandboxes` then held its own
  copy, `p-h7lc62d0`, so attribution answers coverage, not registration. IAM names an SCP's explicit deny
  only to a principal whose identity policy allows the action: on 2026-10-23 a persona set with no
  `airflow:` allow was told *"no identity-based policy allows the airflow:CreateEnvironment action"* under a
  root SCP denying it. Where: `log-stage-01c-preventive-policies.md`, 2026-08-13 (7.6, 7.7);
  `log-stage-10-orchestration-promotion.md`, 2026-10-23; `runbooks/scp-battery.md`.

- `SUP-021` **Control Tower packs a control enablement into its `aws-guardrails-*` SCPs inconsistently
  across OUs, so a document's id does not say what it holds** (read 2026-08-13 and 2026-08-14 with
  `describe-policy`, Stage 1c step 7.7 and Stage 1d step 12). `AWS-GR_RESTRICT_ROOT_USER` and
  `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` were folded into the original guardrail on `Policy Test`
  (`p-kve97k0o`), `Workloads` (`p-xss3mf3w`) and `Interactive` (`p-o32xhs2d`), but into the
  `CT.MULTISERVICE.PV.1` document on `Identity` (`p-fw2pctqw`) and `Data` (`p-pk85fvr1`). On `Security`,
  `CT.MULTISERVICE.PV.1` went into a new document, `aws-guardrails-KAmzSQ` (`p-idgyiios`), and the root-user
  controls into the pre-existing `aws-guardrails-rFWRFL` (`p-2xyaqn66`), taking it from 11 statements to 13.
  Disabling `CT.MULTISERVICE.PV.1` on `Sandboxes`, where it had created `aws-guardrails-yvYgxw`
  (`p-h7lc62d0`), deleted that document. An enablement is per OU and not inherited, only its statements are,
  so an OU can show zero controls while governed by its parent's. The `Sid` list is the stable reading.
  Where: `log-stage-01c-preventive-policies.md`, 2026-08-13 (7.7); `log-stage-01d-org-wide-enablement.md`,
  2026-08-14 (step 12); `docs/AWS_STATE.md` `INV-11`.

- `SUP-022` **`AWS-GR_RESTRICT_ROOT_USER` enabled without `ExemptAssumeRoot` carries no `aws:AssumedRoot`
  exemption, and enabling it with the parameter edits the same SCP in place** (read 2026-08-13 with
  `describe-policy`, Stage 1c step 7.7). On `aws-guardrails-vldGRP` (`p-kve97k0o`), `GRRESTRICTROOTUSER` was
  `Deny *` on `ArnLike aws:PrincipalArn = arn:*:iam::*:root` with no second condition, and `aws:AssumedRoot`
  appeared in no policy of the organization, so the statement also denies `sts:AssumeRoot` sessions (read
  from the statement, not probed). After the control was enabled with `ExemptAssumeRoot`, the same policy id
  carried `"Null": {"aws:AssumedRoot": "true"}` ANDed with the root-ARN test: Control Tower edited the
  document rather than issuing a new one. `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` has no such parameter. No
  Identity Center role matches the root ARN, so reading the document is the only instrument for either
  state. Where: `log-stage-01c-preventive-policies.md`, 2026-08-13 (7.7).

- `SUP-023` **Control Tower calls from a member account either fail as if no landing zone existed or succeed
  with an empty answer, so their output says nothing about the landing zone** (measured 2026-08-13 and
  2026-08-16, Stage 1c step 7.0 and Stage 2 verification (iii)). From Identity, `controltower
  list-enabled-controls` failed on all seven OUs with `ResourceNotFoundException`: *"AWS Control Tower
  cannot complete the operation, because you must create a landing zone first."* From the same account
  `list-landing-zones` returned `None` and `list-landing-zone-operations` `[]`, neither an error, so a
  report run there states that the landing zone never ran, in output identical to a true answer. The
  Organizations account-cap quota reads `0.0` from a member account, and the Organizations quotas answer
  only in `us-east-1`, `NoSuchResourceException` elsewhere (read 2026-08-15 in Management, applied value
  10.0); no policy-size quota is published for `organizations`. Both are read in Management. Where:
  `log-stage-01c-preventive-policies.md`, 2026-08-13 (7.0); `log-stage-02-terraform-foundation.md`,
  2026-08-16 (verification (iii)); `log-stage-01a-landing-zone.md`, 2026-08-15. The control API's one
  account and the SCP it writes are `SUP-033`.

- `SUP-024` **`CT.MULTISERVICE.PV.1` lands as an ordinary SCP whose `NotAction` list exempts `iam`, `kms`,
  `organizations`, `config`, `access-analyzer` and `ecr-public` entirely, and not `ssm:GetParameter`,
  `cloudshell`, `servicequotas`, `guardduty`, `securityhub` or `macie2`** (read 2026-08-13 and 2026-08-14
  with `describe-policy`, Stage 1c step 7.7 and Stage 1d step 12). The `CTMULTISERVICEPV1` statement carries
  86 `NotAction` entries across 68 service prefixes, with `StringNotEquals aws:RequestedRegion = us-west-2`
  ANDed with `ArnNotLike aws:PrincipalARN` over four roles: `AWSControlTowerExecution`,
  `aws-controltower-ConfigRecorderRole`, `aws-controltower-ForwardSnsNotificationRole` and
  `AWSControlTower_VPCFlowLogsRole`. Of `cloudtrail:` only `LookupEvents` is exempt, and of `s3:` only the
  account-level and multi-region-access-point actions. `ecr-public:*` being exempt means the Region control
  never denies it, and a probe resolving its AMI with `ssm:GetParameter` in the denied Region was itself
  denied. The attached document answers `describe-policy` per OU, which the console's `Artifacts` tab does
  not replace. Where: `log-stage-01c-preventive-policies.md`, 2026-08-13 (7.7, verification (vii));
  `log-stage-01d-org-wide-enablement.md`, 2026-08-14.

- `SUP-025` **A successful read of a setting an EC2 declarative policy manages echoes the policy's custom
  message in `ManagedExceptionMessage`, so the message alone does not mark a refusal** (measured 2026-08-14,
  Stage 1c step 7.8). With `awsds-org-declarative-ec2` attached at the root, `ec2
  get-instance-metadata-defaults` returned `rc=0` with `"ManagedBy": "declarative-policy"` and
  `"ManagedExceptionMessage"` carrying the custom text. A refusal arrives as an API error carrying that
  message, with no policy id and no *"explicit deny"* wording, and AWS's default text in its place means the
  custom message was lost; the exit code separates the two. The document's vocabulary differs from the
  API's: `block_all_sharing` and `disabled` in the policy, `block-all-sharing` and `false` from EC2. That
  `--dry-run` answers `DryRunOperation` whether or not the policy is attached is reasoned from the
  enforcement layer, not measured, and whether a root attach reaches Management is unmeasured. Where:
  `log-stage-01c-preventive-policies.md`, 2026-08-14 (7.8); `aws/probes/scp-battery.py` `classify`;
  `aws/declarative-ec2.py`; `runbooks/scp-battery.md` §4.

- `SUP-026` **Control Tower's `CTS3PV8` and `CTS3PV7` guardrails deny configuration changes on the log
  buckets to everyone but `AWSControlTowerExecution` and leave `s3:DeleteObject` and
  `s3:DeleteObjectVersion` allowed** (read 2026-08-14 with `describe-policy` and measured the same day,
  Stage 1d step 9). On the `Security` OU's `aws-guardrails-rFWRFL` (`p-2xyaqn66`), `CTS3PV8` denies over
  `aws-controltower-access-logs-*`, `aws-controltower-cloudtrail-*` and `aws-controltower-logs-*`, and
  `CTS3PV7` over `aws-controltower-config-*`, with `ArnNotLike aws:PrincipalARN =
  arn:*:iam::*:role/AWSControlTowerExecution` and a `NotAction` list of `s3:Get*`, `s3:List*`,
  `s3:PutBucketTagging`, `s3:RestoreObject`, four delete actions and seven `s3:PutObject` family actions.
  `s3:PutBucketObjectLockConfiguration` and `s3:PutBucketVersioning` are absent, so the Log Archive
  account's administrator cannot enable Object Lock on the trail's bucket. A session assumed into
  `AWSControlTowerExecution` from Management matched the exemption, and `put-object-lock-configuration` with
  `COMPLIANCE`, 90 days, succeeded. The guardrail protects the buckets' configuration and leaves their
  contents deletable. Where: `log-stage-01d-org-wide-enablement.md`, 2026-08-14 (step 9).

- `SUP-027` **`AttachPolicy` on an already-attached pair is an inert authorization probe: authorization runs
  before the duplicate check, and the duplicate error carries `CreatePolicy`'s text** (measured 2026-08-15,
  Stage 2 step 5.0 reading 4). Re-attaching the tag policy `p-95lyaycq7l` to the root `r-zhj6` from an
  account the delegation reaches answered `DuplicatePolicyAttachmentException` with *"A policy with the
  specified name and type already exists."*, the duplicate-name text of `CreatePolicy`. The same call from a
  principal holding no delegation answered `AccessDeniedException`, so IAM authorization precedes the
  duplicate check. A per-OU pair answered the duplicate too, exercising an `ou/<org>/*` wildcard resource
  entry. Nothing is attached or detached, so the pair measures a delegation or its narrowing provided the
  negative control runs. Bind the reading to the exception type, never the message; a resource entry with no
  existing attachment to aim at cannot be probed this way. Where: `log-stage-02-terraform-foundation.md`,
  2026-08-15; `docs/plan/lessons.md` Lesson 26.

- `SUP-028` **Organizations answers the same `AccessDeniedException` text whether a call is
  management-account-only or merely lacks an allow** (measured 2026-08-15, Stage 2 open question 11). The
  same user and permission set, `AWSOrganizationsFullAccess`, in the IAM Identity Center
  delegated-administrator account and in an ordinary vended account received *"You don't have permissions to
  access this resource"* for every refused call, and the same text came back for an `attach-policy` refused
  for want of a delegation. The wording does not classify the refusal; only a comparison between two
  accounts with one variable apart separated the causes. Where: `log-stage-02-terraform-foundation.md`,
  2026-08-15.

- `SUP-029` **`describe-organization` lists only `SERVICE_CONTROL_POLICY` in `AvailablePolicyTypes` while
  `list-roots` lists every enabled type, and it returns `MasterAccountEmail` to any member account**
  (measured 2026-08-15, Stage 2 open question 11). With `SERVICE_CONTROL_POLICY`, `RESOURCE_CONTROL_POLICY`,
  `TAG_POLICY` and `DECLARATIVE_POLICY_EC2` enabled, `list-roots` reported all four `ENABLED` and
  `describe-organization` the first alone, so policy-type status is read from `ListRoots`. A deprecated
  field is the likely explanation; AWS's documentation was not read to confirm it. `describe-organization`
  answers in an ordinary member account and carries the management account's e-mail address in
  `MasterAccountEmail`, so any principal there allowed the call reads it. Where:
  `log-stage-02-terraform-foundation.md`, 2026-08-15.

- `SUP-030` **An Organizations resource-based delegation policy accepts a `Condition` on `aws:PrincipalArn`,
  which narrows its account-wide `Principal` to one role** (measured 2026-08-16, Stage 2 step 5.1a). The
  policy's `Principal` can only be an account, `arn:aws:iam::<account>:root`, reaching every principal there
  that holds `organizations:*`. `put-resource-policy` accepted an `ArnLike` on `aws:PrincipalArn` naming one
  SSO role, and the duplicate `AttachPolicy` probe moved from `DuplicatePolicyAttachmentException` to
  `AccessDeniedException` for another role while the named one stayed on
  `DuplicatePolicyAttachmentException`. Read, not measured: since 2026-06-30 AWS rejects `NotAction` and
  `NotResource` here; naming a single OU *"excludes child OUs and accounts under child OUs"*; `Create`,
  `Update` and `DeletePolicy` authorize against the policy ARN and `Attach` and `DetachPolicy` against
  target and policy too, so a target-only `Resource` list denies every write; a bare `StringEquals` on
  `organizations:PolicyType` denies calls not carrying the key, where `StringLikeIfExists` does not;
  `TagResource` and `UntagResource` take no such key. Where: `log-stage-02-terraform-foundation.md`,
  2026-08-15 and 2026-08-16; `terraform-live/identity/org-policies/POLICIES.md`.

- `SUP-031` **An out-of-band account rename propagates with no observable delay** (measured at Stage 6b step
  3.2, which had flagged the timing as undocumented): the console act and the `organizations list-accounts`
  read agreed in the same sitting. Recorded as a measured absence, so that nobody builds a wait into a
  procedure that does not need one.

- `SUP-032` **A Control Tower *Update account* renders `Display Name` and `Account Email` read-only**, so an
  account renamed out of band can never be made to match its provisioned product: permanent divergence, not
  drift (measured in Stage 6b). The same update re-asserts D32's direct `AWSAdministratorAccess` assignment,
  so its absence on other accounts is not a control.

- `SUP-033` **A Control Tower control is written from `Management` and read from anywhere** (measured
  2026-09-12). `controltower:` answers only in the management account — a member account is told to create a
  landing zone first — but the control writes an ordinary SCP, and `organizations describe-policy` returns
  its document from a delegated-admin account. So a console act on a control has a mechanical verification:
  the `NotAction` count, 86 in the `CT.MULTISERVICE.PV.1` template and 92 after six additions. This matters
  because the obvious verification is the opposite of an instrument — re-attempting the denied call returns
  the same refusal whether the form failed to propagate or something else in the chain is missing (Lesson
  24). Where: `claude-code-sagemaker.md` M5.

- `SUP-034` **`CT.MULTISERVICE.PV.1` is a template whose exempted actions and exempted principals are
  independent lists, so an added `NotAction` lifts the Region ceiling for every principal in the OU in every
  Region** (read 2026-09-12 in the Control Tower console and measured the same day, Stage 6e step 6; re-read
  2026-10-18). Updating the enabled control from Management shows the policy with `{{AllowedRegions}}`,
  `{{ExemptedActions}}` and `{{ExemptedPrincipalArns}}` slots; nothing expresses one action for one
  principal, and an action entry has no resource or Region dimension. Before its entry was added,
  `bedrock:PutAccountDataRetention` in `us-east-1` was refused *"with an explicit deny in a service control
  policy"* naming the control's `p-umksvu5a`. The SCP the control writes answers `organizations
  describe-policy` from a delegated account although the control API answers only in Management. On
  2026-10-18 the `Interactive` copy carried 92 `NotAction` entries after six `bedrock:` additions, each
  other OU's the stock 86. `Security` names its controls `controlcatalog:::control/<opaque>`, the others
  `controltower:<region>::control/AWS-GR_*`; `controlcatalog get-control` resolves either, `Aliases[0]`
  being the `AWS-GR_*` name. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-09-12; `docs/AWS_STATE.md`
  `INV-12`.

- `SUP-350` **An SCP's attach bound a DataZone read within ten seconds, and its detach kept refusing the
  same read for about a minute** (measured 2026-11-11 on `Policy Test`, Stage 19 step 4.1). A candidate
  document was attached at 04:31:41 UTC; the canary's `datazone list-domains`, which had answered an empty
  list a minute earlier, was refused at 04:31:51 *"with an explicit deny in a service control policy"*
  naming the candidate. The document was detached at 04:33:14 and deleted at 04:33:15; the same call was
  still refused, naming the deleted policy's id, at 04:33:33, 04:33:40 and 04:34:01, and answered at
  04:34:22, 68 s after the detach. One reading, on one service: a probe run right after a detach or an
  amendment can read the previous document, so the battery's rows for a changed statement are read a
  minute or more after the apply. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-11.

## Security Hub and Config

- `SUP-035` **AWS Config's continuous recorder records 120 to 290 configuration items for an
  interface-endpoint cycle whatever its length, a VPC that never changes among them** (measured 2026-10-14
  and re-read 2026-10-20 in Sandbox, Stage 12 step 6.1). From 2026-09-14 to 10-13 CloudWatch `AWS/Config`
  `ConfigurationItemsRecorded` read 1,816 items, 1,487 of them inside eight `sandbox/egress` cycles bounded
  by CloudTrail's `CreateVpcEndpoint` and `DeleteVpcEndpoints`; a day without a session recorded 0 to 4.
  `AWS::EC2::NetworkInterface` 510, `AWS::EC2::VPCEndpoint` 331, `AWS::EC2::SecurityGroup` 176,
  `AWS::EC2::Subnet` 157 and `AWS::EC2::VPC` 123 made 71%, beside `AWS::Config::ResourceCompliance` 279; the
  VPC's items are read as each ENI created or deleted changing its relationship list (inferred).
  `USW2-ConfigurationItemRecorded` was the only Config usage type and no rule evaluation billed: 0.36 to
  0.87 USD a cycle. ENI items can land 2 to 3 h after a destroy (17 in a Production cycle, read 2026-10-14).
  An empty account recorded about 90 items at enrollment, derived from a 2.20 USD day (read 2026-08-14).
  Where: `log-stage-12-observability-finops.md`, 2026-10-14 and 2026-10-20;
  `log-stage-01d-org-wide-enablement.md`, 2026-08-14; `docs/PRICING.md` §2 and §3.

- `SUP-036` **Designating a Security Hub CSPM delegated administrator also turns on trusted access for
  `securityhub.amazonaws.com`, and enables the hub in that account** (measured 2026-08-20, Stage 5a steps
  13.1 and 13.4). `enable-organization-admin-account` from Management answered only `AdminAccountId`. In
  Audit, `describe-hub` then read `SubscribedAt` `2026-08-20T23:07:11.384Z` although no enabling call was
  ever made there, which confirms AWS's page on the enabling. The organization's trusted-access listing then
  held `securityhub.amazonaws.com` among nine principals although nobody had enabled trusted access for it:
  the designation did. A trusted-access principal with no recorded enabling may be the side effect of a
  delegation. That GuardDuty and Macie behave the same is predicted, not measured. Where:
  `log-stage-05a-data-foundation.md`, 2026-08-20 (Pass 6, leg 1).

- `SUP-037` **A Security Hub CSPM configuration-policy association to a suspended account never reaches
  `SUCCESS`, and the root association stays `PENDING` with it** (measured 2026-08-20 and 2026-10-09, Stage
  5a step 13.1). A policy associated with the organization root walks the tree, so it reaches a suspended
  account attached directly to the root, which no policy attached to an OU reaches. On 2026-08-20, 16 of 18
  rows settled (all 7 OUs and all 9 live accounts), and the two left `PENDING` were the suspended account
  and the `ROOT` row; on 2026-10-09, before an update, the same filter still returned those two rows. That
  the root row aggregates its stuck descendant is the likeliest reading, not isolated. A check that every
  row reads `SUCCESS` fails permanently; every OU and live account `SUCCESS` is the usable invariant. Other
  associations take up to 24 h to settle, per AWS. Where: `log-stage-05a-data-foundation.md`, 2026-08-20 and
  2026-10-09; `docs/AWS_STATE.md` `EXC-01`.

- `SUP-038` **Security Hub CSPM bills each standard check as `USW2-PaidComplianceCheck` once the account's
  30-day window closes, 21 to 149 checks a day per account under FSBP** (measured 2026-10-09 in Cost
  Explorer, Stage 5a step 13). FSBP enabled on 2026-08-20 began billing on 2026-09-20 at 0.001 USD a check.
  Checks a day from 2026-10-05 to 2026-10-08 read Sandbox 75 to 120, Staging 22 to 58, Production 28 to 149,
  Data Governance 39 to 85 and Identity 21 to 42; Management's organization view read about 0.45 USD/day,
  about 13.5 USD a month. Finding ingestion, `USW2-SecurityHubProduct:FreeFindingsIngestion`, ran about 800
  a day per account, inside the free 10,000 a month, and Config beside it billed only
  `USW2-ConfigurationItemRecorded`. Cost Explorer lags about a day, so a change to the meter shows a day
  late. That removing the standard while keeping the hub stops the meter is the runbook's expectation; no
  dated zero reading is recorded. Where: `log-stage-05a-data-foundation.md`, 2026-10-09;
  `runbooks/security-hub.md` §S and §V3.

- `SUP-039` **`update-configuration-policy` accepts `ServiceEnabled: true` with an empty
  `EnabledStandardIdentifiers`, and the change reaches members while their associations read `PENDING`**
  (measured 2026-10-09, Stage 5a step 13 pause). The API reference says only `Required: No` for the list;
  the call was accepted in Audit, the delegated administrator, and minutes later `describe-hub` answered and
  `get-enabled-standards` was empty in five members. The update re-walks the tree: a listing seconds later
  showed 8 associations not `SUCCESS`, minutes later 16 (the root, all 7 OUs and 8 accounts, Audit among
  them), against 2 before. A `Description` not passed stayed unchanged. Read on AWS's pages, not measured:
  centrally managed accounts *"can't use"* the account-specific operations, `disable-security-hub` and
  `batch-disable-standards` among them, and *"Security Hub CSPM doesn't apply the policy to the delegated
  administrator account"* when it says `ServiceEnabled: false`. So a pause that reaches the delegated
  administrator keeps the service on with no standard. Where: `log-stage-05a-data-foundation.md`,
  2026-10-09; `runbooks/security-hub.md` §P.

- `SUP-040` **Removing a Security Hub CSPM standard deletes its `securityhub-*` Config rules in each account
  at that account's own pace** (measured 2026-10-09 and 2026-10-17, Stage 5a step 13 pause). After the
  policy update at 02:23 UTC, the rule counts at about 02:25 and at 02:29 read Sandbox 191 then 24, Staging
  309 then 205, Production 346 then 346, Data Governance 322 then 289 and Identity 193 then 71; on
  2026-10-17 none of the five held a Config rule of any name. `describe-config-rules` paginates, and a
  `length()` query under `--output text` prints one number per page. Read on AWS's page, not measured: a
  failed deletion is retried every 12 h, but *"if you disabled Security Hub CSPM or don't have any other
  standards enabled, Security Hub CSPM can't try again"*, so rules left after the last standard goes are
  orphans that AWS Support removes, and re-enabling the standard adopts them. Where:
  `log-stage-05a-data-foundation.md`, 2026-10-09; `docs/AWS_STATE.md` `EXC-14`; `runbooks/security-hub.md`
  §V and §F.

- `SUP-355` **AWS Config records no Glue database in an account whose Lake Formation create-defaults are
  empty: the recorder's `glue:GetDatabase` is refused** (read 2026-11-11 in Staging's and Production's
  trails and measured the same day in four accounts, Stage 19 step 4.6). Within three minutes of each
  database's creation by a deployment project's provisioning, `AWSServiceRoleForConfig`, invoked by
  `config.amazonaws.com`, called Cloud Control's `GetResource` for `AWS::Glue::Database` and
  `glue:GetDatabase` and was answered `AccessDenied`, *"An unknown error occurred"*: `app_etl` in both
  accounts, and Production's new `default`. `AWSConfigServiceRolePolicy` v97 allows `glue:GetDatabase`, so
  the refusal is not IAM's; the databases carry no `IAM_ALLOWED_PRINCIPALS` grant, both create-default
  lists being empty, and no Lake Formation grant names the role (inferred from the grants read: the
  trail's text names no layer). `configservice list-discovered-resources --resource-type
  AWS::Glue::Database` returned nothing in Sandbox, with nine databases, in Data Governance, with five,
  and in Staging and Production, with five each, under Control Tower's recorder, every supported type,
  continuous. Config's inventory and any rule over the type are blind to the catalog here, and each new
  database leaves a service role's `AccessDenied` in the trail that is no finding. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-11.

## CloudTrail

- `SUP-041` **Control Tower's organization trail carries the organization id as its `S3KeyPrefix`, so the id
  appears twice in every delivery path** (measured 2026-08-15 in Log Archive, Stage 1d step 9).
  `describe-trails` on `aws-controltower-BaselineCloudTrail` returned the organization id as `S3KeyPrefix`,
  the bucket root listed one `PRE <org-id>/`, and the day's deliveries sat under
  `<org-id>/AWSLogs/<org-id>/<account>/CloudTrail/us-west-2/2026/08/15/`. A key built from `AWSLogs/` alone
  lists empty, which reads as no deliveries rather than a wrong prefix, so the prefix is read from the trail
  before any key is built. Where: `log-stage-01d-org-wide-enablement.md`, step 9 under 2026-08-14.

- `SUP-042` **A persona's S3 and S3 Control calls through a gateway endpoint are recorded with a private
  source address and the `vpcEndpointId`, while its STS and Glue calls in the same session arrive from a
  public address with none** (measured 2026-08-19 in Sandbox, Stage 5a pass 4d, and 2026-09-07, Stage 6c 6.5
  verification 4). Over the WireGuard tunnel, `ListBuckets` was recorded from `10.20.160.254`, the host's
  ENI after NAT, with Sandbox's S3 gateway endpoint, and a refused Glue `StartCrawler` from the VPN's
  Elastic IP with no endpoint. Through the proxy, `GetCallerIdentity` came from the proxy's Elastic IP with
  no endpoint, and in the same second `ListCallerAccessGrants` and `GetDataAccess` from the proxy host's
  private address with the hub's gateway endpoint: `s3control` resolves inside the S3 prefix list. An
  identity-side `NotIpAddress aws:SourceIp` deny therefore refused every direct S3 call from inside the
  perimeter, and needs an `aws:SourceVpce` branch beside it. Where: `log-stage-05a-data-foundation.md`,
  2026-08-19; `log-stage-06c-networking-hub.md`, 2026-09-08.

- `SUP-043` **A CloudTrail `eventName` is not the IAM action that event authorizes, and a policy written
  from the event name grants nothing** (measured 2026-10-10, and it cost an apply cycle). The portal's
  refusals logged events `GetResources` and `ExecuteQuery`; the denial message on those same events named
  the action being checked, and it was `sqlworkbench:CreateConnection` — with `sqlworkbench:DriverExecute`
  behind a second `GetResources`. One event authorizes a differently-named action, and several events
  authorize the same one. A policy granting `sqlworkbench:GetResources` changed nothing and the next refusal
  was identical to the first, which is the dangerous part: the symptom does not say the grant missed. Read
  `errorMessage`, not `eventName` — `is not authorized to perform: <action>` is the only authoritative
  statement of what to grant, and it also distinguishes the policy type (*"no identity-based policy allows"*
  against an explicit deny). Two services in this same window gave neither: Glue answered `An unknown error
  occurred` for `GetCatalogs`, and Lake Formation answered *"Insufficient Lake Formation permission(s):
  Required Describe on raw"* — not an IAM failure at all, so the action was inferred from the event name
  there, by necessity rather than by choice. The corollary for managed policies:
  `AmazonRedshiftQueryEditorV2NoSharing` v9 does carry both real actions (`DriverExecute` unconditionally,
  `CreateConnection` under `aws:RequestTag/sqlworkbench-resource-owner`), and the earlier reading that it
  did not was this same confusion written down as a fact about AWS. Where: `log-stage-06h` (2026-10-10),
  `sandbox/warehouse/iam.tf`, `runbooks/log-debugging.md`.

- `SUP-044` **A refused `sts:AssumeRole` records no `roleArn` in CloudTrail** (measured 2026-10-10). Both
  denials carry `requestParameters.roleArn` absent and no `externalId`, while the successes in the same
  window carry the target in full. The trail says *denied*, not *denied for what*, so the role that was
  actually requested comes from the caller's own error text — read it before attributing a refusal from the
  trail alone. Where: `log-stage-06h` (2026-10-10), `runbooks/log-debugging.md`.

- `SUP-045` **`cloudtrail lookup-events` can answer "no events" for events it holds** (measured 2026-10-10).
  A lookup by `EventName=GetResources` returned nothing; a lookup by
  `EventSource=sqlworkbench.amazonaws.com` two minutes later returned six `GetResources` events in the same
  window. Indexing lag or an index that does not carry them — either way, an absence from a lookup run
  shortly after the fact is not evidence of absence (Lesson 62). Sweep by source before concluding that a
  call was never made. Where: `log-stage-06h` (2026-10-10).

- `SUP-046` **CloudTrail Lake refuses a new customer, and the network activity guide still offers it**
  (measured 2026-10-11, Stage 6i step 4.2a). `CreateEventDataStore` answered `InvalidParameterException:
  CloudTrail Lake is no longer accepting new customers. Existing customers can continue to use their event
  data stores.` An account that never created a store is a new customer. The guide's network activity page
  and the 2024 announcement both offer an event data store beside a trail. Where: `log-stage-06i`'s 4.2a
  entry, `PRICING.md`.

- `SUP-047` **Network activity events cover an S3 gateway endpoint, under a prefix of their own** (measured
  2026-10-11, Stage 6i step 4.2a). A trail's files arrive under
  `AWSLogs/<account>/CloudTrail-NetworkActivity/`, beside `CloudTrail/`. A refusal by the gateway endpoint's
  policy reads `errorCode` `VpceAccessDenied`, names the bucket for a path-style request as for a
  virtual-hosted one, and shows another owner's account as `HIDDEN_DUE_TO_SECURITY_REASONS`. The
  announcement names S3 and never says "gateway". Where: `log-stage-06i`'s 4.2a reading.

- `SUP-048` **A role's own account records a caller from another account with no ARN, and an absent field
  fails EventBridge's `anything-but`** (measured 2026-10-13, Stage 8 step 4.6). Staging's copy of the deploy
  runner's `AssumeRole` reads `userIdentity.type` `AWSAccount`, a `principalId` of `<role unique
  id>:<session name>`, the caller's `accountId` and a `sharedEventID`, and no `arn`; an SSO session's reads
  `AssumedRole`, still with no `arn`. `TestEventPattern` answered `false` for a pattern exempting the runner
  by `userIdentity.arn` on that record with another account's role in it, so the rule could never fire on a
  caller from outside. The operators page says `anything-but` matches *"anything except what's specified"*
  and speaks of absence only under `exists`. The role's account does deliver that copy to its event bus: a
  misuse from Production fired Staging's rule (verification xvi). A refused cross-account `AssumeRole` is
  recorded in the caller's account only, with `requestParameters` null and the role named in `errorMessage`
  alone. Where: `log-stage-08`'s 2026-10-13 entries, `deploy-role-v0.2.0`.

- `SUP-049` **The CloudTrail `AssumeRole` record that EventBridge delivers carries the new session's
  `accessKeyId` and `sessionToken` in `responseElements.credentials`, so an SNS target passing the whole
  event mails them** (measured 2026-10-13 in Production, Stage 8 verification xvi). The misuse rule's alert
  for a deliberate assumption of `awsds-deploy-prod` at 05:08:32Z was the whole event, `"readOnly":true`
  among its fields, and its `responseElements.credentials` held the session's key id and token, expiring
  06:08:32Z. The record carries no secret access key, so the pair cannot sign a request, but every alert
  puts a session token in a mailbox. An input transformer on the rule's target that names only the event's
  paths it needs (caller, role, time, source address) leaves them out. Where:
  `log-stage-08-cicd-pipelines.md`, 2026-10-13, verification xvi and `deploy-role-v0.3.0`.

- `SUP-050` **An `AssumeRole` event names its role by ARN, so a `ResourceName` lookup by the role's name
  finds none of them** (measured 2026-10-21 in Production). By ARN the lookup answered the same event ids as
  the `EventName=AssumeRole` history, 80,211 events since 2026-08-09: `awsds-deploy-prod` 12, Staging's
  `awsds-deploy-staging` 12, `awsds-prod-proxy` 476, and the Config service-linked role 627 on 2026-10-19.
  By name it answered no `AssumeRole`. The user guide's only `ResourceName` example is a role name. Where:
  `aws/deploytargets.py` §8 and `aws/cicd.py` `CI-8`, both by ARN. A role's own calls are not found by
  `ResourceName`, and a lookup by access key misses the calls a service makes in its session (read
  2026-10-18 and 2026-10-22 in Sandbox, Stage 8 verification xix). On 2026-10-18 the lookup by
  `awsds-deploy-sandbox-test`'s name or ARN returned nothing since 2026-10-16, while each session, looked up
  by its access key, showed its one `GetCallerIdentity`; on 2026-10-22 the lookup by ARN returned the role's
  17 `AssumeRole` events. The twelve `test-deploy` sessions' access keys, 2026-10-19 18:00 to 21:00,
  returned 1,335 events and none of the `kms:GenerateDataKey`, `logs:CreateLogGroup` and
  `logs:DescribeLogGroups` calls the service made in the role's session during `UpdateWorkflow`, which the
  trail showed on 2026-10-19. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-18, 2026-10-19 and
  2026-10-22.

- `SUP-051` **An `AssumeRole` through the global endpoint `sts.amazonaws.com` is recorded in `us-east-1`
  alone, in the role's account and in the caller's, so an EventBridge rule in `us-west-2` never sees it**
  (measured 2026-10-26, Stage 8 verification xxviii). The `sts-global-probe` job on Production's deploy
  runner assumed `awsds-deploy-prod` and Staging's `awsds-deploy-staging` through
  `sts.us-west-2.amazonaws.com` and through `sts.amazonaws.com`: of six records, each global call's sat in
  `us-east-1` alone and each regional call's in `us-west-2`, in both accounts, the caller's copy of the
  cross-account call included. AWS's page on STS endpoints, read 2026-10-16, says the global call is
  recorded in `us-east-1`. The call also evaluates as `us-east-1`: the IAM simulator read it `explicitDeny`
  under an SCP on `aws:RequestedRegion`, and a global `AssumeRole` of `awsds-deploy-prod` on 2026-10-30 was
  refused by that SCP. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-26;
  `terraform-live/identity/org-policies/POLICIES.md`, `DenyDeployRoleAssumptionOutsideTheRegion`.

## CloudWatch and Service Quotas

- `SUP-052` **The CloudWatch Logs Insights console reports a missing permission in its own wording, and
  calls `logs:DescribeFieldIndexes`, which AWS's list of console permissions omits** (measured 2026-08-17 in
  Sandbox, Stage 4). Field discovery failed with *"Failed to load discovered fields: Outdated permission.
  User with accountId: ... is not authorized to perform GetLogGroupFields on resources
  /aws/lambda/aws-controltower-NotificationForwarder"*, which carries neither *"with an explicit deny in an
  identity-based policy"* nor *"because no identity-based policy allows"*, so a probe attributed by its
  wording cannot use that action. With `logs:GetLogGroupFields`, `logs:GetLogRecord` and
  `logs:DescribeQueryDefinitions` granted from AWS's page of console permissions, the next call was refused
  in IAM's canonical wording on `logs:DescribeFieldIndexes`, which the page does not list. The managed
  policy `CloudWatchLogsReadOnlyAccess` (version 12) replaced the hand-written list. Where:
  `log-stage-04-vpn.md`, 2026-08-17; `terraform-live/identity/sso/permission-sets.tf`.

- `SUP-053` **A log group's `storedBytes` reads 0 while the group is receiving events, two days after its
  creation** (measured 2026-09-08 in Production and Sandbox, Stages 6c and 6d). The proxy access log's group
  in Production read 0 when two days old, while its `IncomingBytes` metric recorded 0.53 MB on 2026-09-06
  and 0.13 MB on 2026-09-07; `/awsds/sandbox/dns-firewall` read 0 while its streams were live and a
  half-hour window of it held 358 events. Older groups do carry a size (`/aws/sagemaker/studio` 13.6 MB on
  2026-09-12), so the field lags; the lag was not timed. An empty-looking group is read from its streams'
  `lastEventTimestamp` or from `IncomingBytes`, never from `storedBytes`. Where:
  `log-stage-06c-networking-hub.md` and `log-stage-06d-unified-studio-remainder.md`, 2026-09-08;
  `runbooks/log-debugging.md` §2.2.

- `SUP-054` **Services create their own log groups with a retention nobody chose: `datazone-<id>-dev` at 3,
  30 or 731 days, and the SageMaker and MWAA Serverless groups never expiring** (measured 2026-09-09 and
  2026-09-12 in Sandbox, Stage 6d 6.2, read again 2026-10-17). `describe-log-groups` found one
  `datazone-<id>-dev` group per DataZone project, at 3, 30 and 731 days in one account on one day. Studio
  apps write to `/aws/sagemaker/studio`, which has no retention, 13.6 MB on 2026-09-12 and 27.0 MB on
  2026-10-17, while `/awsds/sandbox/studio`, created with 30-day retention, held 0 bytes and no stream. The
  first processing job created `/aws/sagemaker/ProcessingJobs` with no retention and no CMK; each MWAA
  Serverless workflow gets `/aws/mwaa-serverless/<domain>-<project>/<workflow>` with none, and each
  project's `datazone-<project>-dev/error` and `/output` never expire: 14 such groups, 27.4 MB, on
  2026-10-17. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-09 and 2026-09-12;
  `docs/AWS_STATE.md` `EXC-10`.

- `SUP-055` **`RequestServiceQuotaIncrease` refuses a value below the default with a message asking for more
  than the default, and accepts a value equal to it** (measured 2026-09-13 in Sandbox, Stage 6d thirteenth
  sitting). On the three `datazone` quotas applied at 0 (`L-F63F402C`, `L-B3401D17`, `L-85C9EC5A`),
  `--desired-value 1` answered `IllegalArgumentException`, *"You must provide a quota value greater than the
  default quota value of 5.0"* (15.0 for the third). The same calls at 5, 5 and 15 were accepted: two
  `PENDING`, one `CASE_OPENED` seven seconds after its creation. The applied values stayed 0, and all three
  requests were `CASE_CLOSED` on 2026-09-24 without an increase. A quota applied below its default is
  requested at the default or above, whatever the refusal's wording says. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-12/13 and 2026-10-17.

- `SUP-056` **A CloudWatch aggregate answers a question about its window, not about now — and the CLI makes
  the aggregate easier to ask for than the current value** (three times in one stage, 2026-09-20). The same
  session read `ComputeSeconds` as 405, then 4,743, then 94,767 RPU-seconds for one workgroup, and
  `DataStorage` as 1,596 MB when the namespace held 130 — the storage figure was `max(Datapoints[].Maximum)`
  over a 24-hour window, six hours after a `DROP` had freed the space, and it was written into a plan as an
  owed `VACUUM`. `--statistics Sum` and `--statistics Maximum` with a wide `--start-time` are the shortest
  commands to type and the easiest to misread; the habit that catches all three is plot the series before
  quoting a number from it. Two consequences that cost real money and real work here: a cost figure taken
  while a query is still running is a partial sum, and a storage figure taken over a day is a peak. Where:
  `log-stage-05b`, the three amendments to 5.3 and the fourth on the storage.

- `SUP-057` **A SageMaker quota can be applied above the requested value while its request still reads
  `CASE_OPENED`, quotas never requested rise with it, and no trail records the raise** (measured 2026-10-17
  to 2026-10-18 in Sandbox, Stage 17 0.2, and 2026-10-24 in Production and Staging, Stage 9 3.5). Three
  requests for 1 on `L-CCE2AFA6`, `L-614B09FD` and `L-236AE59F`, made 2026-10-17 at 21:45Z and answered
  `PENDING`, read 20, 8 and 8 applied by 01:01Z the next day, and `L-0CE343FE`, never requested, rose from 4
  to 10. CloudTrail held only the three requests and reads under `servicequotas.amazonaws.com`, and no
  `support.amazonaws.com` event. In Production and Staging, four requests for 2 stayed `CASE_OPENED` while
  training read 20 and transform 8 for `ml.m5.large`, other types moved too, and
  `get-aws-default-service-quota` still read 0.0. What raised them is unread; the applied value is the
  reading. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-10-18;
  `log-stage-09-deployment-targets.md`, 2026-10-24.

- `SUP-058` **SageMaker's running apps and jobs are counted in `AWS/Usage`, not in an `AWS/SageMaker`
  namespace** (measured 2026-10-18, Stage 12 step 1.1). `ResourceCount` with `Service=SageMaker` carries one
  metric per app or job type, `studio/JupyterLab-ml.t3.medium` or `processing-job/ml.t3.medium`, with data
  while one runs; Service Quotas names it as the quota's usage metric, and `SERVICE_QUOTA()` divides it by
  the applied value. A reading that looked for a SageMaker namespace recorded "no running-app metric exists"
  (`EXC-10`, 2026-09-12), Lesson 62's wrong path. Where: `log-stage-12-observability-finops.md`, the
  2026-10-18 entry. Not every quota has a usage metric (read 2026-10-18 in five accounts, Stage 12).
  `list-service-quotas` for SageMaker returned 2,417 quotas in each account, 2,324 of them with a usage
  metric, and `L-0263D0A3` (Elastic IPs) and `L-1B52E74A` (gateway endpoints) carry none, so no
  `SERVICE_QUOTA()` alarm can be written on them. Beside SageMaker's types, `AWS/Usage` `ResourceCount`
  carries `InterfaceVPCEndpointsPerVPC` per VPC (Sandbox's at most 24) and `VPCsPerRegion` (Production 3
  every hour), and `SERVICE_QUOTA()` answered 30 %, 48 % and 60 % over them at their peaks. Where:
  `log-stage-12-observability-finops.md`, 2026-10-18; `terraform-live/production/observability/main.tf`, the
  quota alarm.

- `SUP-059` **A read of a log group under a customer key records a refused `Decrypt` by the reader and
  returns the events anyway** (measured 2026-10-26, Stage 9 3.1 and Stage 10 1.3). The infrastructure user,
  whom Production's data key admits through no `logs` path, read a job stream with `get-log-events`: the
  trail holds its `Decrypt` `invokedBy logs.amazonaws.com`, no encryption context, `AccessDenied`, and in
  the same second a `Decrypt` by `fas.s3.amazonaws.com` under CloudWatch Logs' chunk store's `aws:s3:arn`,
  which succeeded, and the events came back. The training operator's six refusals per run have the first
  shape while its task log carries the training job's lines, and `awsds-prod-debug`'s read in a window the
  same afternoon showed the same pair. A refusal of this shape is not a refused read. Where:
  `log-stage-10-orchestration-promotion.md` and `log-stage-09-deployment-targets.md`, 2026-10-26.

## EventBridge

- `SUP-060` **EventBridge Scheduler does not substitute a context attribute whose angle brackets arrive
  JSON-escaped** (measured 2026-10-25, Production's first scheduled execution, Stage 10 6.1). The
  orchestration module writes the target's input with Terraform's `jsonencode`, which escapes `<` and `>`:
  the schedule stored `{"chain":"app-etl","scheduledTime":"\u003caws.scheduler.scheduled-time\u003e"}` and
  the execution received the same text, which a JSON parser reads back as the unsubstituted
  `<aws.scheduler.scheduled-time>`. With the brackets literal in the stored input (`orchestration-v0.2.1`),
  the firing of 2026-10-26 00:42 UTC received `"scheduledTime":"2026-10-26T00:42:00Z"`. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-25 and 2026-10-26;
  `terraform-modules/orchestration/chains.tf`, the schedule's `input`. Terraform's plan showed the fix as
  whitespace (measured 2026-10-25, Stage 10): planned against `production/orchestration/`, `Plan: 0 to add,
  3 to change, 0 to destroy.`, each schedule's `input` rendered as `jsonencode( # whitespace changes`,
  though the stored bytes changed from `\u003c` and `\u003e` to literal angle brackets. The plan compares
  the decoded JSON, so a change a service matches byte for byte can be labelled whitespace, and the stored
  string is read back from the service's API after the apply. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-25; `runbooks/terraform-changes.md`.

## EC2

- `SUP-061` **Changing `instance_type` is a stop/modify/start, and user data does not re-run on it**, so a
  size change made because the build ran out of memory leaves the bigger host unbuilt. Only a replacement
  re-runs a first boot.

- `SUP-062` **The allocation id does not survive a transfer** (measured 2026-09-06, 6c step 4.5):
  `eipalloc-04397bfae0295333d` in the source became `eipalloc-07edec7a52dc0820a` in the destination. AWS
  documents it neither way. The address is preserved and the id is not, so an allocation id is a per-account
  fact about an address, and anything that pinned the old id points at nothing. This is why `[P]` ids are
  read through remote state instead of pasted, and why an `import` block's id is read after the accept.
  Reading: `log-stage-06c-networking-hub.md`, the 4.3-4.6 entry.

- `SUP-063` **Two of the four documented refusals fire at accept time, in the destination account.**
  `enable-address-transfer` succeeds on an address that is still associated, and on a destination at its
  Elastic IP quota; the failure arrives at `accept-address-transfer` as `InvalidTransfer.AddressAssociated`
  / `AddressLimitExceeded`, with the transfer already pending and a seven-day clock running that AWS
  notifies nobody about. The eligibility reading is therefore taken across both accounts before the first
  write, which is what `./aws/eip-transfer.py` does.

- `SUP-064` **An EC2 security group description refuses an apostrophe, and a rule description refuses `>`**
  (measured 2026-09-20 and 2026-09-21). One character set governs both: `a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*` —
  it includes `#`, `$`, `!`, `=` and `+`, and excludes `'` and `>`, so the ASCII arrow `->` that reads
  naturally in a rule description is refused while `to` passes. The wording differs by object (`Invalid
  security group description` against `Invalid rule description`) and both arrive at apply, after every
  other resource in the plan has been created and with `validate`, `fmt` and `tflint` all green. `validate`
  holds the set only on an inline `ingress`/`egress` block and on `aws_security_group_rule` (hashicorp/aws
  6.68.0, measured 2026-10-14); `./scripts/check-sg-descriptions.py` holds every description's literal text
  to it, in `make check` and the commit gate. Where: `log-stage-05b` 1.8, `log-stage-06h` 2.3,
  `log-stage-08` 2.4.

- `SUP-065` **A Data Lifecycle Manager policy description admits `[0-9A-Za-z _-]` and nothing else**
  (measured 2026-10-12, Stage 7 step 1.2): an apostrophe or a parenthesis fails the plan with `invalid value
  for description`, naming the CLI reference rather than the character. The Terraform provider validates it
  at plan time, which is the cheap place to meet it. Where: `terraform-live/production/tooling/main.tf`.

- `SUP-066` **An EC2 instance created in the same apply as its role and instance profile can meet
  `NoCredentials` on its first AWS call** (measured 2026-10-16, Stage 8). A GitLab test runner whose role
  and instance profile were created at 16:36:01-02 UTC in the same `make gitlab-up` stopped its boot at
  16:36:29, 28 s later, on `aws ssm get-parameter`: *"An error occurred (NoCredentials): Unable to locate
  credentials."*, with `cloud-final` `FAILED`. The apply had already reported success, and the runner never
  registered; the serial console showed it. A boot that depends on its own identity retries its first call
  with a deadline: this one doubles the wait up to 32 s for five minutes. Seen once; the propagation delay
  itself was not timed. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-16;
  `terraform-live/production/runners/test-user-data.sh.tftpl`; Lesson 68.

- `SUP-405` **AL2023 makes its zram swap only on a host with less than 800 MB of memory, so every EC2 size
  above a nano boots with no swap at all** (read 2026-11-21 on three hosts of
  `al2023-ami-2023.12.20261120.0-kernel-6.18-x86_64`, in the console and through SSM). The t3.nano's OOM
  report counted 415 MiB of memory and 415 MiB of zram swap, both spent when its `dnf` was killed
  (`SUP-406`). The t3.small's boot logged `zram_generator::config: zram0: system has too much memory
  (1909MB), limit is 800MB, ignoring.`, and the t3.medium read `MemTotal` 3835 MiB and no swap. A t3.micro
  read 913 MiB total on 2026-09-06 (Stage 6c's log), above the limit too. AWS gives the limit on the AL2023
  user guide's system-requirements page, where zram is on by default since AL2023.3 for instance types
  under 800 MB, the nano sizes named as examples. The page does not say that the step up loses the swap,
  and on the host the generator's console line is the only sign. The consequence: above a nano a size is
  chosen against `MemTotal` alone, with nothing to absorb a peak past it, so a t3.micro adds less headroom
  over a t3.nano than its memory suggests (inferred). Where: `log-stage-12-observability-finops.md`,
  2026-11-22; `terraform-live/production/proxy/variables.tf`.

- `SUP-406` **On AL2023 2023.12.20261120 a dnf with a cold cache peaks at about 620 MiB of resident
  memory, and update-motd runs a dnf of its own in the first minute of a boot** (measured 2026-11-21). The
  repository's metadata is 91 MB, downloaded at 74 MB/s in the t3.nano's console. On a t3.medium of the
  same image (`MemTotal` 3835 MiB, no swap, 257 MiB used at rest), through SSM with throwaway cache
  directories under `/var/tmp` and nothing installed, `dnf install --downloadonly squid jq
  amazon-cloudwatch-agent` exited 0 after 26 s at a `VmHWM` of 617 MiB, and `dnf check-update` exited 0
  after 25 s at 623 MiB. On the t3.nano, 415 MiB with 415 MiB of zram (`SUP-405`), the first boot's
  `dnf -y install wireguard-tools iptables-nft amazon-cloudwatch-agent` was killed 25 s into the user
  data, `Out of memory: Killed process 1962 (dnf)`, its `anon-rss` 165,736 kB with about 348 MB swapped and
  no other dnf running. systemd then stopped `cloud-final.service` (`Cloud-init 22.2.2 received SIGTERM,
  exiting`), and at 48 s update-motd's `70-available-updates` lost its own dnf to the same killer. The host
  came up with no WireGuard, no `wg0` and no CloudWatch agent while every describe-level check passed.
  AWS's system-requirements page says that a `dnf upgrade` between some releases can need more than
  512 MB, and nothing about an install or a check on a cold cache. Its page on package updates does not
  name update-motd; an issue on AWS's AL2023 tracker (441, opened 2023-09-09) has `update-motd.service`
  run at a reboot or once a day. The consequence: a first boot that installs packages needs about 620 MiB
  for its dnf above the system's own use, which a t3.micro's 913 MiB hold with little to spare, and about
  twice that if update-motd's dnf parses the cold cache at the same time (inferred: on the nano the two
  were killed 23 s apart, and did not run together - the first kill's task table lists one `dnf` and no
  update-motd, which appears with its own `dnf` only in the second, after cloud-init's SIGTERM). A host
  that lost its first boot is repaired by a replacement, not a resize (`SUP-061`). A 1 GiB swap file
  written before the first dnf, with update-motd masked, carries the install on a nano: on 2026-11-22 a
  t3.nano of the same image finished it in 65 s, `/swapfile` at priority -2 beside the zram at 100, and
  logged no OOM line (`wireguard-v0.8.1`). Where: `log-stage-12-observability-finops.md`, 2026-11-22;
  `terraform-modules/wireguard/main.tf`; `terraform-live/production/proxy/variables.tf`;
  `terraform-live/production/vpn/instance_type.auto.tfvars`.

## Systems Manager

- `SUP-067` **Parameter Store reserves every name beginning with `aws` or `ssm`, case-insensitively.**
  `PutParameter` answers `AccessDeniedException: No access to reserved parameter name`, a message that reads
  like a policy problem and is a naming one. Measured at Stage 2's Validation, 2026-08-16; the rule and this
  project's `/datascience/<env>/…` names live in `conventions.md`. The undocumented half is the error text.
  Read again 2026-11-16 (Stage 19 release F, pipeline #126's `staging-deploy`): `PutParameter` on
  `/awsds/staging/applications/app-etl/stage-variables` as `awsds-deploy-staging` answered the same text, the
  name quoted without its leading slash; release F's parameter moved to `/datascience/<env>/applications/`.

- `SUP-068` **`ApplyOnlyAtCronInterval` is rejected on `rate()` schedules**: `InvalidSchedule:
  ApplyOnlyAtCronInterval is not supported for Rate Schedule associations` (measured 2026-09-06, 6c step
  4.8). The flag is the only thing that stops a State Manager association firing at creation time, so an
  association that must not race a first boot has to be `cron(...)`.

- `SUP-069` **A State Manager association fires seconds after `RunInstances`** when
  `ApplyOnlyAtCronInterval` is absent, while the user data is still in `dnf install`. On a fresh host the
  immediate run is a guaranteed `exit 127`, and it leaves a `Failed` association on a working host.

- `SUP-070` **The SSM agent reports `Online` before the user data has finished**: the agent ships in the AMI
  and registers early. Agent registration is not a readiness signal; a check that treats it as one reads a
  half-built host as built (measured twice on 2026-09-06, on both hub hosts).

- `SUP-071` **A schedule-only State Manager association does not fire when an instance starts** (measured
  2026-09-19 on the proxy host). The association is `cron(0/30 * * * ? *)` and its `LastExecutionDate` was
  20:00:40Z; `make hub-up` started the host at 20:04:55Z; at 20:25Z the host was still serving the
  `squid.conf` of its previous session - 25 entries against the parameter's 32, missing both of that day's
  applies, one of which had been written while the host was stopped. The next scheduled run at 20:30:53Z
  reported `Success` with empty stdout, and `PX-3` read 32 against 32 immediately after. What it means here:
  starting the hub does not put the committed policy in force, and for up to one cron interval the proxy
  enforces the previous session's allow-list. A parameter written while the host is stopped is not rendered
  by the start either, so the lag is not bounded by how old the edit is. Where: `NETWORK.md` the proxy's
  filters, `log-stage-06d` the fifteenth sitting. Read again 2026-11-19 with the host stopped: the eight
  executions from 12:01:18Z to 15:30:41Z each reported `Success` with `ResourceCountByStatus` `{}`, so an
  execution's status says nothing about a render and its count does (`log-stage-06d`, 2026-11-19).

- `SUP-072` **A public AMI parameter answers only its current value** (measured 2026-10-16 as
  `InfrastructureAccess` in Production, Stage 8 decision 25). On
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`, `GetParameterHistory` is refused
  with `AccessDeniedException: Cannot access/update data for the restricted parameter`, and `GetParameter`
  with a version selector answers `ParameterVersionNotFound` for every version, the current one (194)
  included. A pin by parameter version is therefore unavailable, and which image the parameter named at a
  past moment is read from `describe-images` (owner `amazon`, name and `CreationDate`), never from Parameter
  Store. Neither the EC2 page that recommends the parameter nor Parameter Store's page on public parameters
  says so (both read the same day).

- `SUP-073` **The SSM Agent on a host started before its `ssm` interface endpoint exists hibernates, and the
  instance stays unregistered for twenty minutes** (measured 2026-10-26, Stage 7 8.1). In a private subnet
  with no NAT or internet gateway, the agent came up at 01:29:16 UTC, 40 s before the endpoint (01:29:56),
  resolved the public `ssm.us-west-2.amazonaws.com`, timed out and logged *"SSM Agent entering hibernation
  due to error"* at 01:31:26. `describe-instance-information` held no record until the hibernation's retry
  registered it `Online` at 01:51:26; meanwhile `start-session` answered *"An error occurred
  (TargetNotConnected) when calling the StartSession operation: ... is not connected"*. With the endpoints
  created first, the same host read `Online` 1 min 20 s after its start (03:15:09 to 03:16:29). The run
  started after the endpoints that still timed out once is `SUP-083`. Where:
  `log-stage-07-gitlab-runners-ecr.md`, 2026-10-26 (three entries); `runbooks/gitlab.md` §U;
  `scripts/tfhygiene/layers.py`.

## VPC and Route 53 Resolver

- `SUP-074` **A NAT never carried S3 or DynamoDB traffic here, even under design A**: a prefix-list route is
  more specific than `0.0.0.0/0`, so the gateway endpoint always won (`docs/NETWORK.md`, measured in Stage
  3). Removing the NAT therefore did not make that traffic cheaper; it was never paying. Design B saves on
  the traffic that did use the NAT, internet downloads at 0.045/GB of processing, which now cross an EC2
  proxy with no per-GB charge.

- `SUP-075` **DNS Firewall needs both `example.com` and `*.example.com` to cover a domain and its
  subdomains**: neither form implies the other. Harmless there, and fatal when the same list is transcribed
  into a system whose wildcard already covers the apex (Lesson 53).

- `SUP-076` **The Route 53 Resolver query log writes no `firewall_rule_action` for an allowed query, so an
  ALLOW is the absence of the field** (measured 2026-08-23 and re-read 2026-09-09, Stage 6 4.3 and 6d 8.2).
  In log version `1.100000`, 881 records held not one `ALLOW`: names that resolved carried no
  `firewall_rule_action`, and a filter looking for `ALLOW` finds nothing. A block arrives as
  `firewall_rule_action` `BLOCK` with `rcode` `NXDOMAIN` and the matched list's `firewall_domain_list_id`.
  `query_name` is an FQDN with a trailing dot. `srcids.instance` names an EC2 instance and nothing else, so
  a SageMaker app is a bare `srcaddr`, told apart only by the names it asks for. Clients report a block as a
  name error, `getaddrinfo ENOTFOUND`, and a MWAA Serverless worker as errno 16 (2026-10-11), with no `403`
  in any proxy log. Where: `log-stage-06a-unified-studio.md`, 2026-08-23;
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-09; `runbooks/log-debugging.md` §D.

- `SUP-077` **A DNS Firewall rule left at its default inspects every name in the CNAME chain, and the query
  log blames the queried name for a block caused by a target** (measured 2026-08-23, Stage 6 step 4.3).
  Under one rule and one wildcard depth, `blobs.duckdb.org` and `releases.astral.sh` (A records) resolved
  while `index.crates.io` (CNAME to Fastly) and `cloud.r-project.org` (CNAME to CloudFront) failed. The
  query log reported each failure as `BLOCK` against the queried name with the catch-all list's id, never
  printing the target, so `checkip.amazonaws.com` looked blocked under `*.amazonaws.com`. Of 21 hostnames
  four package ecosystems use, 14 were CNAMEs leaving any plausible list, and eight of nine external names
  resolved only because their authoritative side flattens the CDN behind an A record under the queried name.
  The field is `FirewallDomainRedirectionAction`, default `INSPECT_REDIRECTION_DOMAIN`; that
  `TRUST_REDIRECTION_DOMAIN` trusts the chain within one query only, so a target queried on its own is still
  blocked, is read, not measured. Where: `log-stage-06a-unified-studio.md`, 2026-08-23;
  `terraform-modules/vpc-egress/dns-firewall.tf`; `docs/AWS_STATE.md` `EXC-05`.

- `SUP-078` **An interface endpoint's private hosted zone is authoritative for the whole subtree of each
  name it serves, and answers NXDOMAIN for every subdomain that exists only in public DNS** (measured
  2026-08-24, Stage 6 4.2). With the `datazone` endpoint's private DNS on,
  `agent.datazone.<region>.api.aws`, a name the SMUS portal needs, returned NXDOMAIN to every client of the
  VPC resolver, a full-tunnel laptop included: the zone holds the apex and falls back to nothing. The answer
  is authoritative, so DNS Firewall never blocks it, and a literal `*` on the allow-list left the portal
  broken. With the endpoint removed (2026-08-25) the name resolved publicly through the same resolver
  (2026-08-26). `PrivateDnsEnabled` therefore claims every name under each name the endpoint serves, its
  `.api.aws` twin included, and each endpoint added shadows one more subtree for every client resolving
  through that VPC. Where: `lessons.md` Lesson 40; `docs/AWS_STATE.md` `EXC-06`;
  `terraform-live/sandbox/egress/main.tf`.

- `SUP-079` **The VPC resolver at `.2` answers only requests sourced from within the VPC's own address
  range**, so a forwarded packet carrying a tunnel address is not answered. This is why 6c step 4.7 exempts
  the hub's public subnets from the masquerade and never the VPC CIDR: the tidier rule takes the tunnel's
  DNS down, with a symptom pointing anywhere but at a masquerade rule.

- `SUP-080` **An interface endpoint answers for more DNS names than its service's `PrivateDnsName`, and
  neither set follows from the service token** (measured 2026-09-06 in `us-west-2` and 2026-09-09 in
  Sandbox, Stage 6c 5.6 and 6d 8.8). Of 29 services, eight have a canonical name no string rule derives:
  `ecr.api` is `api.ecr.<region>.amazonaws.com`, `sagemaker.studio` `*.studio.<region>.sagemaker.aws`,
  `emr-dashboard` `*.emrappui-prod.<region>.amazonaws.com`. `describe-vpc-endpoints` showed 16 of 18
  interface endpoints answering beyond it: twelve with an `.api.aws` twin, `logs` with
  `streaming-logs.<region>.amazonaws.com` and twins, `ecr.dkr` with `dkr-ecr.<region>.on.aws`,
  `sagemaker.studio` with four names across `sagemaker.aws` and `app.aws`; only `ec2messages` and
  `secretsmanager` had one. The plural `PrivateDnsNames` matched the endpoints' `DnsEntries` on seven
  services without an endpoint (2026-10-10); the singular field carries one name. `DnsEntries` adds `vpce-`
  names, `sagemaker.studio`'s ending in `.vpce.sagemaker.aws`. The S3 Gateway shape returns no private DNS
  name. A bypass list built from canonical names would let `streaming-logs.<region>.amazonaws.com` pass the
  proxy's `.amazonaws.com` entry as a public call, inferred, not observed. Where:
  `log-stage-06c-networking-hub.md`, 2026-09-06; `log-stage-06d-unified-studio-remainder.md`, 2026-09-09 and
  2026-10-10.

- `SUP-081` **`s3.dualstack.<region>.amazonaws.com` is not a subdomain of `s3.<region>.amazonaws.com`, and
  AL2023's repositories are reached by the dualstack name** (measured 2026-09-06 on a build host, Stage 6c
  5.8). The AL2023 repository bucket is addressed as
  `al2023-repos-<region>-xxxx.s3.dualstack.<region>.amazonaws.com`, which a `NO_PROXY` holding only
  `s3.<region>.amazonaws.com` does not match, so dnf sent it to the proxy and the first boot failed with
  *"Failed to download metadata for repo 'amazonlinux'"*. On the host the dualstack name returned 200 direct
  (16.15.35.255, through the S3 gateway endpoint) and 000 through the proxy; the plain name also returned
  200 direct. The gateway endpoint carries both spellings because its prefix-list route is keyed on the
  address and both resolve into S3's IPv4 ranges. `dnf.conf`'s `proxy=` has no exclusion setting, so the
  bypass has to come from the environment. Where: `log-stage-06c-networking-hub.md`, 2026-09-06;
  `terraform-modules/vpc-egress/no-proxy.tf`.

- `SUP-082` **The Amazon Q endpoint service `com.amazonaws.us-east-1.codewhisperer` exists in `us-east-1`
  alone and is absent from PrivateLink's cross-Region catalog read from `us-west-2`** (measured 2026-09-12
  in Sandbox's proxy log and `us-east-1`'s trail, read 2026-10-18 with `describe-vpc-endpoint-services`,
  Stage 6d 10.6). From `us-west-2` the call lists no `codewhisperer` service, the one Amazon Q name being
  `aws.api.us-west-2.qbusiness`; with `--service-regions us-east-1` it offers 92 `us-east-1` services,
  `sagemaker.api` and `sagemaker.runtime` among them, and no Amazon Q one. A `us-west-2` VPC has no private
  path for the Q extension: a space's `codewhisperer.us-east-1.amazonaws.com` and
  `aws-language-servers.us-east-1.amazonaws.com` calls left as `200 TCP_TUNNEL` through the proxy, and
  `q:SendMessage` reached CloudTrail in `us-east-1` from the proxy's Elastic IP with no `vpcEndpointId`. The
  SMUS admin guide's required list still pairs its `q` row with this service, *"available only in
  `us-east-1`"*. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-12 and 2026-10-18;
  `docs/NETWORK.md` §5. The refusal of the same calls by a Region ceiling is `SUP-236`.

- `SUP-083` **An interface endpoint can leave connections unanswered after the apply that created it
  returned** (measured 2026-10-26, Stage 7, `promotion.md` §N.7.1 step 2). `production/egress/`'s `ssm`
  endpoint was created at 21:17:53 UTC and `make gitlab-up` went on to start GitLab's host at 21:18:34; the
  host resolved `ssm.us-west-2.amazonaws.com` to the endpoint's address and its agent logged *"dial tcp
  10.30.4.117:443: i/o timeout"* at 21:20:53, registering 7 min 21 s after the start, where the run of 03:15
  the same day, in the same order and 39 s after the last endpoint, read `Online` in 1 min 20 s. The
  runners, started 20 to 30 s after the host, were `Online` by 21:21:31. An endpoint's existence is not its
  readiness, and the first caller meets the gap.

## ECR

- `SUP-084` **An ECR image pull is two paths, and the heavy one is free.** `ecr.api` and `ecr.dkr` carry the
  authentication and the manifest, kilobytes; the image layers are fetched from S3, which in this estate
  means the `[P]` gateway endpoint: no hourly charge and no per-GB charge. The two interface endpoints are
  billed for almost no traffic. This is also why AWS requires an S3 gateway endpoint beside the two ECR
  ones: without it the auth succeeds and the download hangs. Written down 2026-09-06 after a user question
  found it recorded nowhere in this repository.

- `SUP-085` **`public.ecr.aws` redirects blob downloads to a CloudFront distribution, so a hostname
  allow-list must name a second host that the client's error never mentions** (measured 2026-09-06, Stage 6c
  5.8). A `docker pull` through Squid failed with *"download failed after attempts=6: Forbidden"*, naming no
  host. The proxy's access log named it: `CONNECT d5l0dvt14r5h8.cloudfront.net:443 403 TCP_DENIED`. Squid
  matches the hostname each request names, and the redirect is a new request; a DNS firewall never meets it,
  a CNAME chain and an HTTP redirect being different mechanisms. With that one distribution allowed, `docker
  pull public.ecr.aws/docker/library/alpine:3.20` completed: token and manifest over the proxy, layers over
  the S3 gateway endpoint. The distribution name is a third party's and can change; the proxy log is where
  the next one is read. Where: `log-stage-06c-networking-hub.md`, 2026-09-06.

- `SUP-086` **An ECR pull-through cache whose repository creation template carries tags answers `not found`
  to every first pull when no custom creation role is set** (read 2026-10-12 in Production's trail, Stage 7
  6.4). BuildKit read `not found` on every `FROM` through the cache while the runner role's
  `GetAuthorizationToken` calls succeeded. CloudTrail held the runner's `BatchGetImage` calls answering
  `RepositoryNotFoundException` and ECR's four `CreateRepository` calls, made as
  `AWSServiceRoleForECRTemplate/ECRPullThroughCacheWithTemplate`, refused: *"is not authorized to perform:
  ecr:TagResource"*. That service-linked role carries `ECRTemplateServiceRolePolicy`, which grants
  `ecr:CreateRepository` and nothing else. The creation templates page says the creation role *"must be
  provided when using repository tags and/or KMS in the template, otherwise the repository creation will
  fail"*; the client's error names neither the template nor the role. With the tags removed from the
  templates, the next pull created the repositories. Where: `log-stage-07-gitlab-runners-ecr.md`,
  2026-10-12; `terraform-live/production/registry/cache.tf`; `runbooks/gitlab.md` §M.

- `SUP-087` **An ECR pull-through cache from a credential-free upstream completes its first pull with no
  route to the internet, and imports every platform of the upstream index** (measured 2026-10-12, Stage 7
  6.4 verification vii). In Production's private tier, with no NAT gateway, the first pull through each of
  three rules (`ecr-public`, `k8s`, `quay`) succeeded: ECR created the repositories from the creation
  templates and filled them as `AWSServiceRoleForECRPullThroughCache` (`InitiateLayerUpload` to `PutImage`),
  the `FROM` taking 1.3 s with the import. The repository records the page's wording that the first pull
  *"may require a route to the internet"*. The import takes the whole multi-architecture index, as the page
  says: `pause:3.10` stored five Linux images of 0.2 to 0.36 MB and two Windows images of 270 and 308 MB,
  `alpine:3.22` and `busybox:1.37` seventeen entries each, attestation manifests included. A large image
  whose other platforms are not wanted is pulled by its platform digest. Where:
  `log-stage-07-gitlab-runners-ecr.md`, 2026-10-12; `terraform-live/production/registry/cache.tf`;
  `AWS_STATE.md`.

- `SUP-437` **ECR's basic scanning has failed every image of this estate pushed since 2026-11-15 with
  *"Number of vulnerabilities for this image exceeds the maximum supported with Basic Scanning"*, where
  images of the same base pushed until 2026-10-26 completed with up to 1,365 findings** (read 2026-11-22,
  R1, `describe-image-scan-findings` as `awsds-infra-prod` on every image of Production's five scan-on-push
  repositories). The registry's scanning configuration is `BASIC` with no rule. `awsds-prod-ecr-app-etl`'s
  sixteen images pushed from 2026-10-12 to 2026-10-25 read `COMPLETE`, the 3.80 GB ones with 1,317 to 1,365
  findings (from `v0.3.0` on, 113 `CRITICAL`, 612 `HIGH`, 158 `MEDIUM`, 16 `LOW` and 466 `UNDEFINED`); its six
  pushed from 2026-11-15 20:25 to 2026-11-22 04:06 UTC, the same size, read `FAILED` with *"Number of
  vulnerabilities for this image exceeds the maximum supported with Basic Scanning. Please upgrade to
  Enhanced Scanning to cover all vulnerabilities in the image."*, no completion time and no finding.
  `awsds-prod-ecr-base` and `awsds-prod-ecr-dev-env` split the same way: `default-v0.10.0`, pushed on
  2026-10-26 at 21:51 and 22:02, `COMPLETE` with 1,337 findings each; `default-v0.10.1`, pushed on 2026-11-22
  at 04:09 and 04:20 with ten packages' findings fixed in its lock (#365), `FAILED` with the same text.
  `awsds-prod-ecr-deploy`'s three images of 0.21 to 0.26 GB, the last pushed 2026-10-25, read `COMPLETE` with
  18 to 24 findings. The status is `FAILED`, not the `LIMIT_EXCEEDED` the API also lists. None of the pages
  read on 2026-11-22 (basic scanning, scanning troubleshooting, image scanning, the `ImageScanStatus` and
  `DescribeImageScanFindings` references, the service quotas) names a maximum number of vulnerabilities, a
  scan failing on one, or this text; the quotas they give are 100,000 basic scans per registry per 24 hours
  and one scan per image per 24 hours. So the service changed between 2026-10-26 22:07 and 2026-11-15 20:25
  UTC. Whether an image with few findings pushed since completes is unread, no such image having been
  pushed. Consequence: the release pipelines' `scan-gate` (Stage 8 1.4, informative by decision 1) has read
  `FAILED` and no finding on every tag since `app-etl`'s `v0.4.7` of 2026-11-15, release G's pipeline #138 and
  dev-env's #139 among them, so the gate's OS half reports nothing on these images and `pip-audit` is the
  only scan that reads them; an earlier image's findings are no measure of a later one. The message's remedy
  is enhanced scanning (Inspector), a cost the user decides. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-15 (`v0.5.0`'s `scan-gate`) and 2026-11-22; `stages/stage-08-cicd-pipelines.md` 1.4.

## S3

- `SUP-088` **A denied `GetObject` on a key that does not exist names `s3:ListBucket` on the bucket in its
  error, not `s3:GetObject`** (measured 2026-08-19, Stage 5a pass 4d). `aws s3api get-object` on a missing
  key in `awsds-data-curated` answered *"not authorized to perform: s3:ListBucket on resource:
  "arn:aws:s3:::awsds-data-curated" with an explicit deny in a resource-based policy"* off the tunnel and
  *"because no resource-based policy allows the s3:ListBucket action"* on it. S3 chooses between `404
  NoSuchKey` and `403 AccessDenied` by evaluating `s3:ListBucket`, so a bucket-policy statement covering the
  bucket ARN meets the call there first; a `NoSuchKey` would mean the call was authorized. `aws s3 cp`
  issues a `HeadObject` first, which returns a bare `403 Forbidden` with no body, so the explicit and
  implicit wordings that locate the refusing layer appear only through `s3api get-object`. Where:
  `log-stage-05a-data-foundation.md`, 2026-08-19 (two entries).

- `SUP-089` **S3 Access Grants requests cost USD 0.03 per 1,000, a meter written only in the Price List
  offer file** (read 2026-08-23 in the Price List and AWS's pages, Stage 6). The `AmazonS3` offer prices
  `GetDataAccess`, `ListCallerAccessGrants` and every other non-delete Access Grants call at USD 0.03 per
  1,000 in both `us-west-2` and `sa-east-1`, and deletes at 0.00. The S3 pricing page, the user guide and
  the FAQ, all read the same day, mention no charge, so a reasoned answer of no separate charge is wrong.
  Where: `log-stage-06a-unified-studio.md`, 2026-08-23; `docs/PRICING.md` §5.

- `SUP-090` **SageMaker Unified Studio creates the account's S3 Access Grants instance `default` at the
  first project provisioning, with one location per project and no grants** (read 2026-08-23 and 2026-08-24
  in Sandbox, measured 2026-08-23, Stage 6). Each project has a location whose `LocationScope` is the
  project prefix and whose IAM role is the project role, and the `Tooling` environment carries
  `enableS3AccessGrantsForTools = true`; the instance's `CreatedAt` is 2026-08-22 and it has no Identity
  Center association, so `DIRECTORY_USER` and `DIRECTORY_GROUP` grantees are unavailable. Once a grant on a
  project's `shared/*` was made to a persona role, a laptop vended credentials that read back as
  `assumed-role/datazone_usr_role_<project>_…/access-grants-<uuid>`, and wrote, listed and read under the
  project CMK with no right of its own on the bucket or the key. The project role's trust admits no human
  principal, so this is a laptop's only path to that identity. Deleting a project removes its location and
  leaves the instance. Where: `log-stage-06a-unified-studio.md`, 2026-08-23; `docs/AWS_STATE.md`, the
  vending row; `docs/SMUS.md` §1a.

- `SUP-091` **S3 Access Grants' `GetDataAccess` rides the S3 gateway endpoint, because
  `s3-control.<region>.amazonaws.com` resolves inside the `pl-s3` prefix list's ranges** (read 2026-08-24 in
  Sandbox's trail, Stage 6). From a laptop on the tunnel, `GetDataAccess` (`eventSource` `s3.amazonaws.com`)
  carried the WireGuard host's private address `10.20.160.87` and the S3 gateway endpoint's `vpcEndpointId`,
  while `GetCallerIdentity` in the same session carried the same address and the STS interface endpoint's
  id; the same API off the tunnel carried no `vpcEndpointId`. A VPC with no `s3control` interface endpoint
  therefore does not send these calls to the internet gateway, and a policy on `aws:SourceVpce` must name
  the gateway endpoint for them. `GetDataAccess` is also an event name of `lakeformation.amazonaws.com`, so
  a trail lookup filters on `eventSource`. Where: `log-stage-06a-unified-studio.md`, 2026-08-24;
  `docs/AWS_STATE.md`, the persona vending row.
  **Read again 2026-11-21** (Stage 17 1.6, from a SageMaker Unified Studio space behind the egress proxy):
  the S3 Access Grants plugin's `GetAccessGrantsInstanceForPrefix` and `GetDataAccess` went to
  `<account>.s3-control.us-west-2.amazonaws.com` through the proxy, one tunnel (*"CONNECT
  <account>.s3-control.us-west-2.amazonaws.com:443 200 7313 6347 TCP_TUNNEL"*, 23:08:35Z), while the STS
  call and the `PutObject` that followed left with no proxy line. The account-prefixed host matches no
  `NO_PROXY` entry naming `s3.<region>.amazonaws.com`, so a proxied client reaches S3 Control through the
  proxy, the path `SUP-042` records with the hub's gateway endpoint, not the spoke's. Verification iii's ranged read on
  2026-11-22 showed the same tunnel at 00:12:57Z. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-11-21 and 2026-11-22.

- `SUP-092` **Deleting an S3 Access Grants grant leaves `GetDataAccess` answering for up to about 19
  seconds, and credentials already vended work until their own expiry** (measured 2026-08-26 in Sandbox,
  Stage 16 6.1, a single exercise). A sacrificial `READWRITE` grant was vended against at 20:14:07 (900 s,
  the minimum; expiry 20:29:08) and deleted at 20:16:54. A re-vend at +1 s answered, minting a fresh 900 s
  credential after the delete; at +19 s it was refused in the grant register's wording. The 20:14:07
  credentials, 40 s past the delete, listed, read through KMS and ran `DeleteObject`. Twelve seconds past
  their stated expiry they answered `ExpiredToken`, *"The provided token has expired."*, the only thing that
  stopped them. The exposure after a revocation is therefore the delete plus propagation plus the
  credential's duration, and a grantee holding a standing wider grant re-vends through it. Where:
  `log-stage-16-sandbox-lake.md`, 2026-08-26, sitting 4.

- `SUP-093` **The SMUS JupyterLab image ships `aws_s3_access_grants_boto3_plugin`, which vends through S3
  Access Grants under every boto3 S3 call, so a plain call from a notebook succeeds through a grant**
  (measured 2026-08-26 in Sandbox, Stage 16 4.4). A notebook probe meant as an un-vended read of a granted
  prefix returned 200 with the objects. The kernel's credentials method was `container-role`, `pip list`
  carried `aws_s3_access_grants_boto3_plugin 1.3.0`, and a plain `get_object` returned `b'hello'` decrypted
  under a key that delegates nothing to IAM, which only a vended session could do. CloudTrail held seven
  `GetDataAccess` events, six `OK` from the kernel's and the portal's sessions and one refused, matched one
  to one with service assumes. The plugin caches credentials, so most calls show no fresh vend. Outside the
  grant the error is the register's, *"You do not have READWRITE permissions to the requested S3 Prefix"*. A
  direct-refusal test runs only where no plugin sits. Where: `log-stage-16-sandbox-lake.md`, 2026-08-26,
  sitting 3; `runbooks/sandbox-lake.md`.
  **Read again 2026-11-21** (Stage 17 1.6, from `eighth-experimentation`'s space `jup` on the house image):
  before a `PutObject` under the project's `shared/` prefix, `GetAccessGrantsInstanceForPrefix` answered 200
  and `GetDataAccess` for `WRITE` 403, and the write then succeeded under the project role's own
  credentials, the plugin's fallback: the object `ml-demo-1-6.txt` exists, under the bucket's default key.
  Where the reading above surfaced the register's refusal, the notebook here saw a successful write, so a
  grant's refusal tested from a space is read in the trail's `GetDataAccess`, not in the call's result. The
  plugin's version and fallback setting in either
  interpreter were not read. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-21.

- `SUP-094` **An S3 gateway endpoint policy's refusal of another owner's bucket reaches the client as a bare
  `AccessDenied - Access Denied`, with no mention of the endpoint policy** (measured 2026-10-11 from a MWAA
  Serverless worker in Sandbox, Stage 6i 5.0 and 4.2a). Listing `sentinel-cogs`, a bucket of another owner,
  was refused in about 35 ms for both virtual-hosted and path-style addressing with only *"Access Denied"*;
  a probe expecting *"because no VPC endpoint policy allows"* failed on its own criterion. The requester's
  network activity trail recorded the same calls with `errorCode` `VpceAccessDenied`, `errorMessage` *"The
  request was denied due to a VPC endpoint policy"*, and the owner's account as
  `HIDDEN_DUE_TO_SECURITY_REASONS`. The log reads the longer wording as given only to a requester in the
  bucket owner's account; that half was not measured here. A probe against a foreign bucket counts the
  `AccessDenied` code, or reads the trail. Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-11. The
  network activity events themselves are `SUP-047`.

## Glue

- `SUP-095` **`CreateCrawler` with a Glue security configuration attached fails unless the crawler's role
  may call `glue:GetSecurityConfiguration`** (measured 2026-08-18, Stage 5a pass 1). The first apply
  answered `InvalidInputException`, *"The role … is not authorized to perform
  glue:GetSecurityConfiguration"*; both crawlers were created on the retry once the role carried
  `glue:GetSecurityConfiguration` and `glue:GetSecurityConfigurations` on `Resource: "*"`, since a security
  configuration has no ARN to scope to. The error names the missing action, not the encryption control that
  introduced it. The slice's comment also records that with a security configuration attached, Glue writes
  crawler logs to `/aws-glue/crawlers-role/<config>-<role>` instead of `/aws-glue/crawlers`, so the role's
  log statement covers `/aws-glue/*`. Where: `log-stage-05a-data-foundation.md`, 2026-08-18 (pass 1
  applied); `terraform-live/data-governance/data/maintenance.tf`.

- `SUP-096` **A Glue job's own role appears as session `GlueJobRunnerSession` both for Glue's pre-run calls,
  from AWS's addresses, and for the script's calls, through the job VPC's endpoints** (read 2026-10-19 in
  Staging's trail, Stage 18 4.2, and 2026-10-23 in Production's, Stage 9 2.4). In Staging, a Glue 6.0 job on
  two network connections showed `GlueJobRunnerSession` calling `glue:GetConnection` four times,
  `logs:CreateLogGroup` and the job's network-interface calls before the job ran, from AWS's own addresses
  through none of the account's endpoints; the job's role therefore needs `glue:GetConnection` on its
  connections and catalog. In Production, the script running as `…/GlueJobRunnerSession` made
  `glue:GetTable` through the `glue` endpoint, `lakeformation:GetDataAccess` through the `lakeformation`
  endpoint and `GetCallerIdentity` through the `sts` endpoint. One session name thus covers calls from two
  networks; the endpoint id in the event separates them. Where:
  `log-stage-18-staging-deployment-project.md`, 2026-10-19 (4.2 and 4.4);
  `log-stage-09-deployment-targets.md`, 2026-10-22 and 2026-10-23 (2.4).

- `SUP-097` **A Glue Spark job in a VPC with no DataZone endpoint posts no OpenLineage event, holds the
  listener about 33 s per attempt and still succeeds** (measured 2026-10-19 in Staging, Stage 18 7.1). With
  `spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener` and transport
  `amazon_datazone_api`, a Glue 6.0 job logged twice *"Failed to send lineage event to DataZone"*, caused by
  *"Unable to execute HTTP request: Network is unreachable (SDK Attempt Count: 4)"*, and `SUCCEEDED` in 118
  s; `list-lineage-events` read 0 and neither account's trail held a `PostLineageEvent`. With
  `com.amazonaws.us-west-2.datazone` and private DNS added, the same job posted 12 events (4 `START`, 4
  `RUNNING`, 4 `COMPLETE`) as `GlueJobRunnerSession` through the endpoint, under namespace `default` with
  the job name's `-` turned to `_`. AWS's page asks for the endpoint; the run status never shows its
  absence, only the driver's error stream does. Where: `log-stage-18-staging-deployment-project.md`,
  2026-10-19 (7.1).

- `SUP-098` **A Glue database with a `FederatedDatabase` refuses a `Description`**: *"Description and
  federation source cannot exist together in a database!"* (measured 2026-10-25, Data Governance's
  `governed_trades`). Where: `log-stage-09-deployment-targets.md`, 2026-10-25.

- `SUP-099` **`glue get-resource-policy` finds no policy on a catalog that holds per-resource policies; only
  `glue get-resource-policies` lists them** (measured 2026-10-26 in Data Governance, Stage 6f 11.9). A
  DataZone subscription fulfilment's publishing role made four `glue:PutResourcePolicy` calls, each with a
  `resourceArn` (`database/*` twice, `table/*/*` and `catalog`) and `enableHybrid` `TRUE`, all allowed.
  Afterwards the account-level read still answered *"Policy not found"*, while `glue get-resource-policies`
  listed the new statements: Sandbox's account root granted the Glue table and partition actions on
  `catalog`, `database/*` and `table/*/*` under `aws:PrincipalOrgID`, plus `AWSRAMPermissionLFTag`
  statements for the consumer accounts. Per-resource policies from an earlier named share already stood on
  `database/curated` and `table/curated/*`. A check that reads the catalog policy with `get-resource-policy`
  sees none of them. Where: `log-stage-06f-data-governance.md`, 2026-10-26 (11.8 and 11.9); `docs/SMUS.md`.

- `SUP-364` **`glue get-tables` and `glue get-table-versions` answer `IsRegisteredWithLakeFormation` false
  for a table `glue get-table` answers true** (measured 2026-11-14 in Sandbox, Stage 19, on
  `app_etl.trades_notional`, an Iceberg table at version 3 under a location registered with Lake
  Formation). The three reads, between 17:50 and 18:07 UTC, of one unchanged table: `get-tables
  --database-name app_etl` `False`, `get-table` `true`, `get-table-versions` `False` for version 3. Pass
  1's `get-table` of 2026-11-10 read `true` as well. The Glue API reference's `Table` page, read the same
  day, describes the field as whether the table is registered with Lake Formation; neither it nor the
  pages of `GetTable`, `GetTables` and `GetTableVersions` says which call fills it. A check that judges
  registration from a list call reads every table as unregistered; no instrument here reads the field. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-14.

- `SUP-368` **A Glue interactive session's `DPUSeconds` reads 0.0 when the session stops and is filled
  later, below the `ExecutionTime * MaxCapacity` its documentation gives as the formula, and is what the
  bill charges** (measured
  2026-11-14 and 2026-11-15 in Sandbox, Stage 19, on the session its Spark read opened through
  `project.spark.fineGrained` in `test-experimentation`: Glue 5.0, 10 `G.1X` workers, `MaxCapacity` 10.0,
  idle timeout 60). `get-session` at 23:07:41 UTC, 4 s after `STOPPED`: `ExecutionTime` 1151.921,
  `DPUSeconds` 0.0. `get-session` at 00:31:20 UTC on 2026-11-15: the same `ExecutionTime`, `DPUSeconds`
  3248.638 against the 11519.2 the formula gives, an average of 2.8 DPU, and `DefaultArguments` carrying
  `--enable-auto-scaling` `true` and `--enable-lakeformation-fine-grained-access` `true`. `list-sessions`
  a minute earlier answered the same `DPUSeconds` with `DefaultArguments` null, so the auto-scaling flag
  reads only from `get-session`. The formula is the service model's text for `GetSession` (`aws glue
  get-session help`, aws-cli 2.37.12). Which quantity the bill charges is not measured; the reading is
  Sandbox's `USW2-GlueInteractiveSession-DPU-Hour` line for 2026-11-14 once Cost Explorer holds the day:
  0.90 DPU-h if it counts `DPUSeconds`, 3.20 if it counts the formula. A session's consumption read at
  its stop reads nothing, and one priced from its size and its run reads three and a half times the
  field. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15. Read again 2026-11-17 at 01:12 UTC
  in Sandbox's Cost Explorer, the day held through its last hour: `USW2-GlueInteractiveSession-DPU-Hour`
  for 2026-11-14 reads 0.9025 DPU-h and 0.3971 USD at 0.44 USD/DPU-h, against the field's 0.9024
  (3248.638 DPU-s). Neither the formula's 3.1998 DPU-h (1.41 USD) nor the 3.3497 that 1205.9 s from
  `CreatedOn` to `CompletedOn` give at 10 DPU (1.47 USD) is billed. `list-sessions` at 22:37 UTC on
  2026-11-15 listed this session alone in Sandbox, so the line is its own. Where: the same log,
  2026-11-17.

- `SUP-453` **A resource link a subscription's fulfilment writes reads back from `glue get-tables` and
  `get-table` with `TableType` present and empty, `CreatedBy` empty and no `StorageDescriptor`,
  `Parameters` or `CreateTime`; `dbt-athena` 1.11.1 caches it as a table of its schema, and its
  `get_table_type` refuses it** (measured 2026-11-22 in Sandbox, Stage 20 5.1, on `app_dbt.trades_notional`,
  the link `app-dbt-dev`'s subscription to Production's `trades-notional` wrote at 14:05:20 UTC). DataZone's
  `CreateTable`, in Sandbox's trail as the project role's `AWSDataZone-Subscriptions` session, carried a
  `tableInput` of `name`, `retention` 0, `targetTable` and `isRowFilteringEnabled` `false`, no table type;
  `eighth-experimentation`'s link at 14:05:02, the same. At 14:54:57 `get-tables` answered the link with
  `"TableType": ""` beside the two Iceberg tables' `EXTERNAL_TABLE`. The service model's text (`aws glue
  get-table help`, aws-cli 2.37.12) gives `TableType` as the table's type, `EXTERNAL_TABLE` for what Glue
  creates, `CreatedBy` a minimum length of 1, and says nothing of a link's fields. In `dbt-athena` 1.11.1,
  read the same day from the lock's release: `list_relations_without_caching`, the cache `dbt build` fills
  from `GetTables`, skips only a table with no `TableType` key, so the link enters the cache as a table;
  `get_table_type` raises *"Table type cannot be None for table …"* on an empty type, and is called on a
  model's own relation during `app-dbt`'s build and on every table of a schema by `dbt docs generate`'s
  catalog. A
  build beside a link runs; `docs generate` over the schema fails while the link stands, and an adapter
  release whose cache classifies each table through `get_table_type` would fail the build as well. Where:
  `log-stage-20-dbt-lineage.md`, 2026-11-22 (5.1).

## Lake Formation

- `SUP-100` **`ram enable-sharing-with-aws-organization` both enables trusted access for `ram.amazonaws.com`
  and creates `AWSServiceRoleForResourceAccessManager`** (measured 2026-08-14, Stage 1d step 11). The call
  returned `true`; Organizations' trusted-access list went from seven principals to eight with
  `ram.amazonaws.com` at 18:47:22Z, and the service-linked role was created in Management at 18:47:23Z, one
  second later. That enabling trusted access from the Organizations side would give the same list and no
  role, with organization sharing still broken, is the source's inference, not measured; so `ram` in the
  list without the role is the reading to distrust. With the RAM call made, organization sharing held: four
  Lake Formation `LakeFormation-V4-*` shares arrived `ACTIVE` with no invitation (2026-08-19), and the
  DataZone domain association raised none (2026-08-21). Where: `log-stage-01d-org-wide-enablement.md`,
  2026-08-14 (step 11); `docs/AWS_STATE.md` `INV-09`; `scripts/tfhygiene/backend.py`.

- `SUP-101` **`CROSS_ACCOUNT_VERSION: 4` and `SET_CONTEXT: TRUE` are already set in accounts nobody
  configured**, consumers included, and `aws_lakeformation_data_lake_settings` replaces the whole
  `Parameters` structure in any account that gains the resource.

- `SUP-102` **A consumer account with no Lake Formation data lake administrator sees an empty catalog while
  RAM holds the share `ACTIVE`** (measured 2026-08-19 in Sandbox and Development, Stage 5a pass 3). After
  the producer's four `LakeFormation-V4-*` shares were created, each consumer's RAM held its two, `ACTIVE`,
  with no invitation anywhere, while `glue:GetDatabases` and `list-lf-tags` returned nothing in both
  accounts, whose settings read `DataLakeAdmins: []`. Once each account had its own data lake settings with
  one administrator (pass 4a/4b, the same day), the resource links were created over the shares. An empty
  consumer catalog therefore has two causes that look identical, the share never arrived or the account has
  no administrator, and only the RAM side and the administrator count separate them. Where:
  `log-stage-05a-data-foundation.md`, 2026-08-19 (pass 3 and pass 4a/4b); `docs/GOVERNANCE.md`;
  `aws/datalake.py` `DL-7`.

- `SUP-103` **Lake Formation gives a catalog object's permissions to its creator alone, so the data lake
  administrator who created a database holds no `DROP` on a table another principal created in it**
  (measured 2026-10-25 in Staging; read 2026-08-19 in Stage 5a pass 4). A Terraform destroy as
  `InfrastructureAccess`, the administrator that created `app_outputs`, was refused *"AccessDeniedException:
  Insufficient Lake Formation permission(s): Required Drop on trades_notional"*: the table's creator was the
  deploy role, through a pipeline. A by-name `DROP` grant to the administrator let `DeleteTable` pass, and
  the grant left with the table. In the other direction, the creator receives `ALL`, `DESCRIBE` and `DROP`
  with grant option on what it creates, resource links included, with no code asking and nothing revoking
  it. A teardown run by a different identity than the creator needs a grant nobody had to write for the
  creation. Where: `log-stage-09-deployment-targets.md`, 2026-10-25; `log-stage-05a-data-foundation.md`,
  2026-08-19 (pass 4a/4b).

- `SUP-104` **Cross-account LF-TBAC grants inside an organization travel with no Glue Data Catalog resource
  policy, against one of Lake Formation's pages** (measured 2026-08-19, Stage 5a pass 3). Lake Formation's
  considerations page states that cross-account LF-TBAC requires additions to the Data Catalog resource
  policy; its Prerequisites page scopes that to an account already sharing through a Glue resource policy.
  In Data Governance `glue:GetResourcePolicy` answered `EntityNotFoundException`, no policy written and
  nothing set to `EnableHybrid`, and the grants produced four `LakeFormation-V4-*` RAM shares, `ACTIVE`,
  held by both consumers with no invitation. The pages render only with JavaScript: an automated fetch
  returned no body, a browser read them. Where: `log-stage-05a-data-foundation.md`, 2026-08-19 (pass 3
  applied); `terraform-live/data-governance/data/README.md`.

- `SUP-105` **An Athena write to a Lake Formation registered location runs as a vended `AWSLF-00-AT-…`
  session of the registration role, and fails on that role's policy, not the caller's** (measured 2026-08-19
  in Data Governance, Stage 5a sample rows). A 12-row `INSERT INTO curated.sample_trades` by
  `InfrastructureAccess` through the `primary` workgroup failed in 1.3 s with *"PERMISSION_DENIED: User:
  …assumed-role/awsds-data-lf-registration/AWSLF-00-AT-<account>-yqjVkpVOQG is not authorized to perform:
  kms:GenerateDataKey … because no identity-based policy allows the kms:GenerateDataKey action (Service: S3,
  Status Code: 403 …)"*. The registration role held read actions alone; the key policy delegated to IAM.
  After `s3:PutObject`, `s3:DeleteObject` and `kms:GenerateDataKey` were added to that role, the same insert
  `SUCCEEDED` in 1,947 ms and `metadata_location` moved from `00000-…` to `00001-…`. The registration role
  is the ceiling for every governed read and write on its locations; the session name in the error is what
  points there. Where: `log-stage-05a-data-foundation.md`, 2026-08-20.

- `SUP-106` **SMUS appoints itself a Lake Formation administrator** when the first project is created: two
  service roles nobody chose, in an account whose `admins` list a later
  `aws_lakeformation_data_lake_settings` would silently reset. Found 2026-08-26 by an unrelated plan, not by
  a gate: `DL-5` measures `parameters`, not `admins`. The first project's provisioning also turns
  `AllowFullTableExternalDataAccess` on (read in CloudTrail 2026-10-21, Staging, Stage 18). In Staging the
  provisioning role's three `PutDataLakeSettings` at 2026-10-19 06:05:34Z set an admin list empty until then
  to itself and the manage-access role, and one of them carried `allowFullTableExternalDataAccess` `true`,
  the value the account then held; the infrastructure user's two earlier writes carried no such field.
  Sandbox's first project, 2026-08-22, left the flag `true` beside the two seats as well. A second
  environment provisioned in Staging on 2026-10-20 left the settings identical. The manage-access seat's
  only identity policy, `AmazonDataZoneSageMakerManageAccessRolePolicy` v4, carries no `lakeformation:`
  action, so its one call, `CreateLakeFormationOptIn`, was refused until
  `AmazonDataZoneGlueManageAccessRolePolicy` v18 was attached (2026-10-20). Where:
  `log-stage-18-staging-deployment-project.md`, 2026-10-20 and 2026-10-21; `docs/plan/open-questions.md`,
  question 24; `terraform-modules/consumer-data/README.md`.

- `SUP-107` **`lakeformation list-permissions` is not paginated by the CLI, returns empty pages that still
  carry a `NextToken`, and refuses a principal filter without a resource** (measured 2026-09-05, Stage 6b
  0.4, and 2026-10-21, Stage 6f). One CLI call answers the first page and a `NextToken`; read to the end,
  the listing took 6 pages for 29 grants in Sandbox and 5 for 28 in Data Governance, the last four of each
  empty. A check that stops at an empty page reads a partial catalog as complete. `--principal` without
  `--resource` answers *"Resource is mandatory if Principal is set in the input"*, read again 2026-10-26, so
  a per-principal reading lists every resource and filters client-side. The project's scripts also read
  `ListResources`, Athena `ListWorkGroups`, the three `s3control` listings and both S3 Access Grants
  listings page by page, the CLI having no paginator for them. Where:
  `log-stage-06b-development-becomes-staging.md`, step 0.4; `log-stage-06f-data-governance.md`, 2026-10-26
  (11.5); `aws/awslib/awscli.py`; `aws/INDEX.md`.

- `SUP-108` **`GetDataLakeSettings` returns the administrators in no fixed order** (read 2026-10-20 in
  Sandbox). Three consecutive reads gave two orders of the same three principals, and the trail holds no
  `PutDataLakeSettings` since 2026-10-15, so a change of order is no write. A reading compares the set.
  Where: `log-stage-06f-data-governance.md`, the entries of 2026-10-20.

- `SUP-109` **Lake Formation grants to an Identity Center principal are listed by neither `list-permissions`
  form** (measured 2026-10-20 and 2026-10-21 in Sandbox, Stage 6f). The SageMaker Unified Studio
  provisioning role grants `arn:aws:identitystore:::user/*` on a project's database and tables under the
  project's `context.datazone.projectId` condition, and CloudTrail's `BatchGrantPermissions` shows the
  grants succeeding. `ListPermissions` by resource omits them, and asked for that principal it answers
  `InvalidInputException`, *"LakeFormation Identity Center Configuration not configured for requested
  catalog"*. A grant to an Identity Center user is read in CloudTrail or not at all, so an audit built on
  `list-permissions` judges the role and `IAMPrincipals` grants alone. Where: `aws/catalog.py`, the header
  comment; `aws/INDEX.md`; the grants themselves in `log-stage-06f-data-governance.md` and
  `log-stage-18-staging-deployment-project.md`.

- `SUP-110` **`glue get-table` answers a missing table as it answers a hidden one** (measured 2026-10-22 in
  Staging, Stage 18 7.2). To a principal holding no Lake Formation grant, `trades` and a made-up name both
  answered *"Insufficient Lake Formation permission(s): Required Describe"*, where `get-database` answers
  `EntityNotFoundException` for a database that does not exist; a table's existence is read in CloudTrail's
  `CreateTable` or by a principal holding `DESCRIBE`. Where: `log-stage-18`'s 7.2 entry.

- `SUP-111` **A cross-account full-table-access vend reads the table owner's
  `AllowFullTableExternalDataAccess`, and the refusal names no account** (measured 2026-10-23, Stage 9 2.4).
  A Glue 6.0 Spark job in Production, the engine's own flag `true`, was refused at its first Iceberg write
  on a shared `curated` table with *"Insufficient Lake Formation permissions. Verify the data lake settings
  for account"*, the sentence ending there; the same job committed 99 s after the lake's flag went on. AWS's
  page names the flag as the mode's first step and says nothing about which account's. The vend is logged as
  `GetDataAccess` in two legs, the driver's own call and Glue's on its behalf, and only the second reaches
  the owner's trail, as a shared event; `GetTemporaryGlueTableCredentials` never appears as an event name.
  Where: `log-stage-09-deployment-targets.md`, the 2026-10-23 entries; Stage 9 decision 13. The engine
  account's own flag plays no part (measured 2026-10-23 and 2026-10-24, Stage 9 2.4 and verification
  xxviii). The second run on 2026-10-23, both flags on, committed with the job role holding `INSERT`,
  `DELETE` and `ALTER` and no `ALL`, which AWS's page says a write requires. On 2026-10-24, with the lake's
  flag on and Production's removed in the console at 22:23:32, the same job `SUCCEEDED`: the insert
  committed at 22:26:46 and the table read 30 rows through the share, eight `GetDataAccess` answered in
  pairs, the driver's and Glue's, through the `lakeformation` endpoint. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-23 (the second run) and 2026-10-24 (the third run).

- `SUP-112` **`GetDataLakeSettings` returns `AllowFullTableExternalDataAccess` `false` as an absent key,
  and the console's switch-on writes `AuthorizedSessionTagValueList` as an empty list** (measured 2026-10-23,
  2026-10-24 and 2026-10-25 in Production, Stage 9 decision 13). Switching on *Allow external engines to
  access data in Amazon S3 locations with full table access* left `get-data-lake-settings` with the flag
  `true` and `AuthorizedSessionTagValueList` an empty list, where the API had returned it absent. Switching
  it off, twice, left the key absent rather than `false`. A comparison of settings by shape sees the
  console's writes as changes. Where: `log-stage-09-deployment-targets.md`, 2026-10-23 (decision 13's act),
  2026-10-24 (the third run) and 2026-10-25. The absence is the API's reading of `false`, not the
  console's removal of a key (read 2026-11-11 and measured 2026-11-12, Stage 19 step 4.7). Production's
  trail holds the console's switch-off of 2026-10-25 as one `PutDataLakeSettings` at 17:44:31 UTC
  carrying the whole structure with `allowFullTableExternalDataAccess` `false`. On 2026-11-12 the CLI's
  `put-data-lake-settings` wrote the settings `get-data-lake-settings` had returned with the flag `false`,
  in Production at 01:50:08 UTC and in Staging at 01:50:16, and three minutes later each account's
  settings held no such key, the administrators, the parameters and the create-default lists as before.
  A reader takes an absent key as `false`, and cannot tell a flag turned off from one never set. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-11 (the classifier's refusals) and 2026-11-12.

- `SUP-113` **A Lake Formation refusal reaches CloudTrail without the permission it lacked** (measured
  2026-10-25, Staging's `make down`). The client read *"Insufficient Lake Formation permission(s): Required
  Drop on trades_notional"*, while the trail's two `DeleteTable` events read `AccessDenied`, *"An unknown
  error occurred"*. Which grant is missing comes from the client's output or from `list-permissions`, never
  from the trail. Where: `log-stage-09-deployment-targets.md`, 2026-10-25.

- `SUP-114` **`lakeformation list-permissions` filtered by principal returns nothing on a resource another
  account's catalog holds** (measured 2026-10-25 in Sandbox, on Data Governance's `governed_trades`). For
  the project's access role, whose grant serves every read of the governed table, and for the project role
  alike, the principal-filtered listing of the database and of the table came back empty; listed by resource
  alone, the same calls returned both roles' `DESCRIBE` and `SELECT`, the latter as `TableWithColumns`. A
  read-back after a grant or a revoke on a shared resource lists by resource. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-25. A `SELECT` granted by name on a table is stored as
  `TableWithColumns` with the column wildcard, so a `list-permissions` filtered by principal and a `Table`
  resource does not return it, while the `DESCRIBE` granted in the same call reads back as `Table` (measured
  2026-10-25 in Sandbox, Stage 9 9.5 step 4, on `governed_trades`' table `trades.trades_notional`). Where:
  `log-stage-09-deployment-targets.md`, 2026-10-25 (9.5's steps 4 and 5).

- `SUP-115` **A Redshift datashare registered with Lake Formation is read by `describe-resource` and omitted
  by `list-resources`** (measured 2026-10-25 in Data Governance, Stage 9 9.5). `register-resource` on the
  datashare's ARN at 01:52:38 UTC, no role, `HybridAccessEnabled` and `WithPrivilegedAccess` false, left a
  registration `describe-resource` reads back as `NOT_VERIFIED`, while `list-resources` returns the two S3
  registrations alone. An inventory of registrations built on `list-resources` misses every datashare. The
  registration also cannot be adopted into Terraform: `aws_lakeformation_resource` has no importer in the
  provider's source at v6.60.0, and the slice's README records a second registration of the same ARN as a
  conflict. Where: `log-stage-09-deployment-targets.md`, 2026-10-25 (9.5's first steps, and the adoption
  written with the environment down); `terraform-live/data-governance/data/README.md`.

- `SUP-116` **An Athena `INSERT` on a Lake Formation table the caller holds `SELECT` on is vended `SELECT`
  first, then refused `INSERT` and `DELETE`, and the error's manifest warning points at no file** (measured
  2026-10-30 in Sandbox and Data Governance, Stage 9 8.1, seen once). From the portal's query editor on
  Athena, through a subscription's resource link to `curated.trades`, the insert failed with `AthenaError`
  category 2, type 1500, *"Principal does not have any privilege on specified resource (Service:
  AWSLakeFormation; Status Code: 400; Error Code: AccessDeniedException…)"*. The trail shows `GetDataAccess`
  granting `SELECT` at 03:46:59, then refusing `INSERT` at 03:47:00 and `DELETE` at 03:47:00 and 03:47:01,
  on the link and on the lake's table, in both accounts. No `UpdateTable`, no `GenerateDataKey` and no
  manifest object existed, although the console message said one may need cleaning. The editor appended `
  LIMIT 100` to every statement, the insert included. Where: `log-stage-09-deployment-targets.md`,
  2026-10-30. A statement carrying its own limit gains none (read 2026-11-22, Stage 6g 2.4): `SELECT * FROM
  "glue_db_blerpkhn9nj7o0"."trades" LIMIT 10;` ran as `… LIMIT 10`, with no semicolon. The statement is
  read with `athena get-query-execution`, since the trail's `StartQueryExecution` shows `queryString` as
  `***OMITTED***`. Where: `log-stage-06g-access-by-identity.md`, 2026-11-22.

- `SUP-416` **A cross-account Athena read through Lake Formation leaves `Decrypt` events in the owner's
  trail by the registration role, invoked by `glue.amazonaws.com`, and names the query only in the
  consumer's `GetDataAccess` on the resource link** (read 2026-11-22 in Sandbox's and Data Governance's
  trails, Stage 6g 2.4). The project role's query `c9f604ea-50f8-47b3-b171-caf3985b6692`, from the portal's
  query editor through the link `glue_db_blerpkhn9nj7o0.trades` to `curated.trades`, left two
  `GetDataAccess` in Sandbox at 02:15:34Z. The one invoked by `athena.amazonaws.com` on the link carries
  `requestParameters.auditContext.additionalAuditContext` `{queryId: c9f604ea-50f8-47b3-b171-caf3985b6692}`,
  a string rather than JSON, and the project role's ARN as `lakeFormationPrincipal`. The one invoked by
  `glue.amazonaws.com` on the lake's table carries `callType` `EXTERNAL` and no audit context. Both carry
  `requesterService` `ATHENA` and one `lakeFormationRoleSessionName`,
  `AWSLF-00-AT-<Sandbox account id>-CRWz3tDXZ4`. Data Governance received the second alone, as a shared
  event of type `AWSAccount` whose `principalId` is the project role's unique id and its session,
  `<Identity Center user id>@<environment id>`. The nine `Decrypt` in Data Governance at 02:15:35Z name
  `assumed-role/awsds-data-lf-registration/AWSLF-00-AT-<Sandbox account id>-CRWz3tDXZ4`, a session created
  at 02:15:34Z, with `invokedBy`, `sourceIPAddress` and `userAgent` `glue.amazonaws.com`, encryption context
  `aws:s3:arn` the bucket's ARN, no source identity and no VPC endpoint. AWS's *Cross-account CloudTrail
  logging* page gives the session name's format, `AT` for Athena and the account id of the account that
  requested the credentials, with a Glue job's S3 event as its example; neither it nor the service's
  CloudTrail page mentions KMS events, an Athena read's `invokedBy` or the audit context (read 2026-11-22).
  In the owner's account the `Decrypt` events read as Glue's, and the shared `GetDataAccess` names Athena,
  the consumer account and the role's session, never the query. The query comes from the consumer's trail:
  the session name finds the `GetDataAccess` on the link, its audit context names the query, and the
  query's `StartQueryExecution` carries the source identity. Whether the consumer's opt-in, *Resource
  owners* under *Default permissions for AWS CloudTrail*, adds the principal's ARN to the owner's copy was
  not measured. Where: `log-stage-06g-access-by-identity.md`, 2026-11-22 (2.4's Athena read, and the
  attribution read after it). Read again 2026-11-22 in Production, on a data product's cross-account read
  (Stage 19 4.12, verification xxiv): the query `cb03150a-…` from `eighth-experimentation`'s query editor
  through the link `glue_db_blerpkhn9nj7o0.trades_notional` left the same pair of `GetDataAccess` in Sandbox,
  and Production received the shared one as `AWSAccount` with the same kind of `principalId`. Production
  also received the consumer's `glue:GetTable` and `BatchGetTable` with that identity, two of them carrying
  the audit context with the query's id, so the owner's trail names the query in Glue's events. The vend's
  `sts:AssumeRole` reads `AWSService` `glue.amazonaws.com` on the role the location is registered with, here
  the deployment project's role SMUS registered, into the session `AWSLF-00-AT-<Sandbox account id>-…`,
  under a session policy of `s3:GetObject` and `s3:ListBucket` on the table's prefix and `kms:Decrypt`
  through S3; three `Decrypt` follow in that session. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-22 (4.12's consumer read).

## Athena

- `SUP-117` **Athena Spark's PrivateLink release moves only the client's path to a session, and the session
  still runs outside every VPC** (read on AWS's pages, 2026-08-19, not measured; Stage 6 decision 3). The
  release of 2026-04-21 adds three interface endpoints on Spark 3.5 workgroups, for Spark Connect, the Live
  UI and the Spark History Server. The Athena Spark API has no `NetworkConfiguration`, subnet or security
  group anywhere, and the SageMaker Unified Studio network-isolation page, current after the release, still
  answers VPC connectivity with *"use Amazon EMR or AWS Glue instead"*. The feature's page says the three
  session endpoints take no VPC endpoint policy, its workaround policing `GetSessionEndpoint` and
  `GetResourceDashboard` on the `athena` API endpoint, and that a session URL minted inside the VPC is
  reachable from the public internet. An executor outside the VPC is outside endpoint policies, flow logs
  and `aws:SourceVpce` conditions; Athena SQL rides `StartQueryExecution` on the `athena` endpoint and is
  unaffected. Where: `log-stage-06a-unified-studio.md`, 2026-08-19; `docs/plan/open-questions.md`, question 12.

- `SUP-118` **An SCP deny on `athena:StartQueryExecution` or `athena:StartSession` reaches the caller with
  no policy named, and both actions authorize before they validate the workgroup** (measured 2026-08-20,
  Stage 5a pass 4e, and 2026-08-21, Stage 6 battery phase 4b). With `athena:StartQueryExecution` added to
  the `Data` and `Identity` OU documents, the call against a workgroup that does not exist answered
  `AccessDeniedException`, *"You are not authorized to perform: athena:StartQueryExecution on the
  resource"*, in Data Governance and in Identity, with no *"explicit deny in a service control policy"* and
  no policy id; the same call from Sandbox, in an OU the statement does not reach, answered
  `InvalidRequestException: WorkGroup is not found`. `StartSession` under the `Interactive` document read
  the same shape the next day. A classifier that files a policy-less refusal as an IAM deny misfiles these,
  so attribution needs a contrast call from an account the statement does not reach. Where:
  `log-stage-05a-data-foundation.md`, 2026-08-20 (4e); `log-stage-06a-unified-studio.md`, 2026-08-21;
  `aws/probes/probes.py`. The portal's query editor shows the same text (read 2026-11-22, Stage 6f 4.3):
  `governed-lake`'s editor in Data Governance, as the project role in the Governance Manager's session,
  answered *"…on the resource. After your AWS administrator or you have updated your permissions, please
  try again. (Service: Athena, Status Code: 400, …)"*, CloudTrail's `errorCode` `AccessDenied`, the
  workgroup existing and its `GetWorkGroup` answered 3 s earlier (`log-stage-06f-data-governance.md`,
  2026-11-22).

- `SUP-119` **`athena:UpdateSession`, which AWS's sample statement for disabling Athena Spark denies, is in
  no Athena API model** (read 2026-08-21 in the CLI's service model, Stage 6 step 1.6). AWS's SageMaker
  Unified Studio network-isolation page ships the statement `DenyAthenaSparkStartSession` with
  `athena:StartSession` and `athena:UpdateSession` on `arn:aws:athena:*:*:workgroup/*`. The botocore model
  of the installed CLI, `athena/2017-05-18`, carries `StartSession`, `TerminateSession`, `GetSession`,
  `GetSessionStatus`, `GetSessionEndpoint`, `ListSessions`, `ListNotebookSessions` and
  `StartCalculationExecution`, and no `UpdateSession`, so that half of the sample denies nothing.
  `StartCalculationExecution` takes a `SessionId`, so a Spark deny that should hold against a session
  obtained by another route names it beside `StartSession`. Where: `log-stage-06a-unified-studio.md`,
  2026-08-19 and 2026-08-21; `terraform-live/identity/org-policies/POLICIES.md`,
  `DenyAthenaSparkStartSession`.

- `SUP-120` **`DeleteWorkGroup` counts query history as contents, and no API deletes a query execution.** A
  workgroup with zero named queries and zero prepared statements still refuses to delete while old
  executions remain, and those age out on Athena's own 45-day clock. The only door is
  `RecursiveDeleteOption`. The Terraform corollary: that door is a configuration argument (`force_destroy`)
  and a destroy runs from the attributes in state, so the flag has to be set in the configuration before the
  resource is removed from it. Deleting the block and the flag in one version leaves the destroy unarmed,
  which surfaces only at destroy time.

- `SUP-400` **Athena renames an Iceberg table in the Glue Data Catalog by a create and a delete, after the
  Glue Iceberg REST endpoint refuses `renameTable`** (measured 2026-11-21 in Sandbox, Stage 20 2.5).
  dbt-athena's table swap on `notional_by_desk`, every statement `SUCCEEDED`. For each of its two
  `alter table … rename to …` (05:02:56 and 05:02:57 UTC) the trail holds first an `UpdateTable` refused
  `UnsupportedOperationResponse`, *"RenameTable endpoint is not supported for Glue Catalog."*,
  `additionalEventData` `{"IcebergRestOperation":"renameTable"}`, with the prefix `catalogs/<account id>`
  and both names, then a `CreateTable` of the new name and a `DeleteTable` of the old, all as the caller's
  session invoked by `athena.amazonaws.com`. The table under the new name is a new Glue object, created at
  the rename at `VersionId` 1. Each rename therefore leaves a refused call in the trail beside a statement
  that succeeded, and exercises `glue:CreateTable` and `glue:DeleteTable` rather than the update its
  statement names. Glue's Iceberg REST connection page lists the endpoint's operations without
  `RenameTable`, and Athena's *ALTER TABLE RENAME* page names no permission; neither says how a rename is
  carried out (read 2026-11-21). Where: `log-stage-20-dbt-lineage.md`, 2026-11-21, 2.5's run half.

## Redshift Serverless

### Namespace, workgroup and limits

- `SUP-121` **A failed `CreateNamespace` rolls the namespace back and leaves its managed secret behind**
  (measured 2026-09-20). Redshift Serverless creates the admin credential in Secrets Manager, then the
  namespace; when the namespace creation failed on an inaccessible KMS key, the namespace was rolled back
  and the secret was not. It survives as `redshift!<namespace>-<username>`, `OwningService: redshift`,
  rotation enabled, tagged with a namespace ARN that no longer resolves — and the next attempt fails with a
  *different* message, *"Unable to create secret for the dbInstance because a secret with a matching name
  exists"*, which reads like a name collision rather than the residue of the previous attempt. The name is
  derived from the namespace and the admin username, so changing either gets past it and leaves the orphan.
  Where: `AWS_STATE.md` `EXC-12`, `log-stage-05b` the first sitting. A Redshift-owned secret is deletable by
  an ordinary call (measured 2026-09-20, Stage 5b). `delete-secret --recovery-window-in-days 7` on the
  orphan `redshift!awsds-sandbox-warehouse-whadmin`, `OwningService: redshift`, was accepted with a deletion
  date of 2026-09-27. Its `aws:redshift-serverless:namespaceArn` tag named `namespace/bf04abe5-…` while the
  only live namespace was `8a6117fd-…`, which is how the orphan is told from the live
  `redshift!awsds-sandbox-warehouse-dbadmin`, left untouched. Where: `AWS_STATE.md` `EXC-12`;
  `log-stage-05b-redshift-serverless.md`, 2026-09-20 (the orphan secret removed).

- `SUP-122` **A Redshift Serverless workgroup's endpoint host survives a delete and re-create; its id does
  not** (measured 2026-09-20). Destroy and re-create under the same name and `endpoint.address` is
  byte-identical — it is derived from the name, the account and the Region — while `workgroupId` changes
  (`75b926c8-…` → `4b0577a2-…`), the usage limit's id changes, and the workgroup's VPC endpoint and both its
  ENIs are replaced with new private addresses. The ARN carries the id, so any IAM or SCP statement scoped
  to a workgroup's exact ARN stops matching after the first teardown, silently, presenting as a principal
  whose queries stopped authenticating with no diff anywhere. Two ENIs also linger in `available` state for
  under two minutes after the destroy, still referencing the security group, which would fail a teardown of
  the slice that owns it inside that window. Where: `log-stage-05b` 1.9, and the comments on
  `sandbox/warehouse/iam.tf` and `DenyRedshiftCostGuardTamperingExceptInfrastructure`.

- `SUP-123` **A breached `deactivate` usage limit does not show in the workgroup's status, and refuses only
  the compute** (measured 2026-09-20). With the limit breached, `get-workgroup` still reads `status:
  AVAILABLE` and nothing in the workgroup's record mentions it; `UsageLimitAvailable` reports a stale figure
  against the previous amount; and the client sees six words with no policy, no limit id and no amount:
  `ERROR: Query reached usage limit`. Leader-node queries keep answering — `select 1`, `select count(*) from
  pg_attribute`, `svv_all_schemas` — while a `CREATE TABLE` is refused, so *"connect and `select 1`"* passes
  on a warehouse that cannot run a real query. Recovery is immediate on raising the amount, with no wait for
  the period to roll over, which no vendor page states. Also: a second `deactivate` limit is refused
  outright (*"Only one DISABLE usage limit allowed per feature"*) and a second, looser `log` limit is
  permitted, which is the hole `WH-3` exists for. Where: `log-stage-05b` pass 3. The counter belongs to the
  usage-limit object (measured 2026-09-20, Stage 5b). `UsageLimitConsumed` is dimensioned `{UsageLimitId,
  UsageType, Workgroup}`: the limit destroyed at step 1.9 read 0.0 although 178 RPU-seconds ran while it
  existed, and its successor read 28.0. After the amount was lowered to 10 RPU-hours in a month that had
  used 26.3, the limit created by the next `make up` did not deactivate the workgroup: a `CREATE TABLE` and
  its `DROP` finished on the first attempt. So a replacement limit starts near zero whatever the month has
  consumed. The limit is evaluated in whole RPU-hours: `UsageLimitConsumed` read 1.0 against an amount of 1
  and fired while real usage settled at 1.3175 RPU-hours, so a limit of N bites between N-1 and N. Where:
  `log-stage-05b-redshift-serverless.md`, 2026-09-20 (the limit lowered to 10; the environment raised);
  `docs/PRICING.md` §5.

- `SUP-124` **A Redshift Serverless workgroup reads back with six `config_parameter` entries nobody set, and
  a Terraform provider older than 6.66.0 plans to remove them forever** (measured 2026-09-20).
  `config_parameter` is a set the provider owns whole: a workgroup created with three parameters returns
  nine, because the service fills `auto_mv`, `datestyle`, `enable_case_sensitive_identifier`, `query_group`,
  `search_path` and `use_fips_ssl`, and every subsequent plan is `1 to change` that never converges. The fix
  is to declare them at their read-back values, which also discloses what a query actually runs under —
  including that `auto_mv` is on by default, so the service builds and refreshes materialized views on a
  1.44 USD/hour meter unasked. Where: `log-stage-05b` pass 3, `sandbox/warehouse-compute/main.tf`. The
  read-back depends on the provider version (read 2026-10-11 and 2026-10-18, Stage 5b; the version
  boundaries from the provider's issues, not measured here). Before 6.66.0 the provider validates
  `parameter_key` against an allow-list and keeps every returned key, so a key the service adds plans a
  removal forever and `UpdateWorkgroup` answers *"ValidationException: You didn't specify any changes to the
  configuration parameters"*; 6.66.0 keeps only the declared keys and drops the allow-list; 6.68.0 reads the
  whole list again when no `config_parameter` block is declared. An AWS Health notice re-introduced
  `enable_large_strings_opt_in` on 2026-10-13: Sandbox's `CreateWorkgroup` responses of 2026-10-16 on 6.68.0
  carry ten `configParameters`, the tenth that key with value `""`, where those of 2026-10-10 and 2026-10-11
  on 6.64.0 carry nine. A plan on 6.68.0 read `No changes` on 2026-10-11 against a workgroup without the
  key; the re-plan against one carrying it is unread. Where: `log-stage-05b-redshift-serverless.md`,
  2026-10-11 and 2026-10-18; `terraform-live/sandbox/warehouse-compute/versions.tf`;
  `docs/plan/upstream-releases.md`.

- `SUP-125` **`db_name` on a Redshift Serverless namespace adds a database, it does not replace `dev`**
  (measured 2026-09-20). A namespace created with `db_name = "warehouse"` carries both `warehouse` and `dev`
  as local databases, and both are born with `USAGE, CREATE` to the group `PUBLIC` on their `public` schema.
  So the `REVOKE` that closes that hole is owed per database, and a check that looks for "exactly one class
  container" has to know about two inert ones. Also in the same namespace: `awsdatacatalog` exists but
  cannot be connected to at all — *"FATAL: Cannot connect to shared database … use cross-database query
  notation"* — which is a stronger form of the documented read-only direction. Where: `log-stage-05b` 1.6
  and 2.4.

- `SUP-126` **A Redshift Serverless workgroup accepts two subnets in two Availability Zones, against the
  Terraform provider's page** (measured 2026-09-20, Stage 5b 0.1). The `aws_redshiftserverless_workgroup`
  page says `subnet_ids` *"must contain at least three subnets spanning three Availability Zones"*; the
  provider's code carries no validator, and AWS's own considerations page disagreed with it. The apply sided
  with AWS's page: Sandbox's workgroup was created with two subnets, in `us-west-2b` (`usw2-az1`) and
  `us-west-2a` (`usw2-az2`), and `enhancedVpcRouting: false`. A VPC built on two Availability Zones needs no
  third subnet for the warehouse. Where: `log-stage-05b-redshift-serverless.md`, 2026-09-20 (0.1).

- `SUP-127` **`CreateNamespace` refused by a customer-managed key's policy fails first on the admin secret's
  key, and neither error names the key policy** (measured 2026-09-20, Stage 5b 1.8). With Sandbox's data
  key, whose policy grants the root the administrative actions and no cryptographic one, `CreateNamespace`
  failed with *"ConflictException: Unable to create namespace credential secret: The KMS key used to encrypt
  the secret is not accessible"*; with the secret's key dropped, with *"ValidationException: Unable to
  create namespace. The key '…' is inaccessible."* A direct `GenerateDataKey` by the same identity named the
  layer: *"…because no resource-based policy allows the kms:GenerateDataKey action"*. The statement that
  admitted the namespace grants the root `Encrypt`, `Decrypt`, `ReEncrypt*`, `GenerateDataKey*`,
  `CreateGrant` and `DescribeKey` under `kms:ViaService = redshift-serverless.us-west-2.amazonaws.com`;
  AWS's note says the service supports no encryption context or confused-deputy headers. `list-grants` read
  `[]` before the create, and the service creates its own grant. Where:
  `log-stage-05b-redshift-serverless.md`, 2026-09-20 (1.8); `terraform-live/sandbox/data/main.tf`,
  `AllowRedshiftServerlessViaServiceInThisAccount`.

- `SUP-128` **A Redshift Serverless workgroup's host name resolves inside the VPC to the ENIs of the
  workgroup's own managed VPC endpoint, not to the `redshift-serverless` interface endpoint** (measured
  2026-10-10, Stage 6h 3.3). From a SageMaker space,
  `<workgroup>.<account>.us-west-2.redshift-serverless.amazonaws.com` resolved to `10.20.116.172` and
  `10.20.49.135`, the ENIs of `vpce-0f9698ecbcece5437`, which carry the warehouse's security group. The
  `redshift-serverless` interface endpoint that serves `GetCredentials` had one ENI, `10.20.7.52`, with
  private DNS on, and its private zone did not capture the data host name. After the workgroup was destroyed
  and rebuilt the name resolved to new addresses, `10.20.53.13` and `10.20.65.84`. DNS and port 5439
  therefore belong to the workgroup's endpoint and `GetCredentials` to the interface endpoint, and each
  fails apart. The TCP source seen from the space was `169.255.254.1`, later `169.255.254.3`, the
  container's NAT and not a VPC address. Where: `log-stage-06h-redshift-connection.md`, 2026-10-10 (3.3
  attempted) and the entry headed 2026-10-11; `runbooks/redshift-connection.md` §V.

- `SUP-129` **Redshift Serverless rotates a managed admin secret with no workgroup, and the database follows**
  (measured 2026-10-20, Stage 5b; read again in Production 2026-11-22). AWS's page *Managing Amazon Redshift admin passwords using AWS Secrets Manager* says such a
  rotation fails and is never retried. Sandbox's first scheduled rotation ran on 2026-10-20 with no
  workgroup since 2026-10-16: Redshift's service-linked role wrote and promoted the new version, and
  `CompleteRotation` reported `Succeeded`. Whether the database followed is unread; the next
  `./aws/warehouse.py --sql` authenticates with the rotated secret. Where: `AWS_STATE.md` `EXC-13`,
  `log-stage-05b` (2026-10-20). The database follows the rotation (read 2026-10-25, Stage 9). With Sandbox's
  workgroup up, the Data API authenticated as `dbadmin` through the secret at 02:38 (`CREATE DATABASE
  governed_trades`) and at 06:04 (`GRANT TEMP`), a password user on the password the rotation of 2026-10-20
  wrote, and again twice on 2026-10-26. Where: `AWS_STATE.md` `EXC-13`;
  `log-stage-09-deployment-targets.md`, 2026-10-25 and 2026-10-26. **Read again 2026-11-22 in Production**
  (R1): `redshift!awsds-prod-warehouse-dbadmin`'s first scheduled rotation, with no workgroup since
  2026-11-16 05:33 UTC, started at 01:11:55 and succeeded at 01:17:08, Redshift's service-linked role
  writing `AWSPENDING` at 01:13:08 and promoting it to `AWSCURRENT` at 01:17:08; it started 48 minutes
  before the `NextRotationDate` it replaced, 01:59:59. With a workgroup up from 05:41:41,
  `./aws/warehouse.py awsds-infra-prod --sql` authenticated as `dbadmin` through the rotated secret eight
  times from 05:42:19 to 05:42:43, no error. Where: `AWS_STATE.md` `EXC-13`;
  `log-stage-19-smus-native-data-product.md`, 2026-11-22.

- `SUP-130` **`DeleteWorkgroup` answers `ConflictException` for up to seventeen seconds after the workgroup's
  usage limit is deleted, and the Terraform provider retries through it** (read 2026-10-26 in Production's and Sandbox's trails, Stage 9).
  On three teardowns that day the trail shows `DeleteWorkgroup` refused four or five times with *"There is
  an operation running on the workgroup. Try to delete it later."*: in Production from 01:10:38 to 01:10:47,
  accepted at 01:10:55; in Sandbox from 01:37:26 to 01:37:30, accepted at 01:37:34, and from 22:10:35 to
  22:10:44, accepted at 22:10:52. Terraform 1.16.6's provider retried each time and the destroy completed. A
  trail read after a successful teardown therefore carries these refusals; the source does not identify the
  running operation. Where: `log-stage-09-deployment-targets.md`, 2026-10-26 (three entries). **Read again
  2026-11-22** (R1, Production's and Sandbox's trails) with the two teardowns since, in Production: refused
  at 05:33:18 and 05:33:19 and accepted at 05:33:20 on 2026-11-16, refused from 05:47:52 to 05:47:56 and
  accepted at 05:48:01 on 2026-11-22, with the same message (Terraform 1.17.2; provider 6.68.0 in all five).
  In each of the five, an accepted `DeleteUsageLimit` on the workgroup's limit came in the same second as
  the first refusal or in the second before it, the provider destroying the limit first as the workgroup's
  dependent, and `DeleteWorkgroup` was accepted 3 to 17 seconds after it. The running operation is
  therefore probably the limit's deletion; the teardown of a workgroup with no usage limit, which would
  settle it, has not been read. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-22.

### SQL, users and privileges

- `SUP-131` **`SVV_SCHEMA_QUOTA_STATE` is refused to a superuser on Redshift Serverless** (measured
  2026-09-20). Both it and `STV_SCHEMA_QUOTA_STATE` answer `permission denied for relation` for the
  namespace admin, who reads `usesuper = true` in `pg_user`, and no other catalog view carries a schema's
  quota — `svv_redshift_schemas.schema_option` is empty for a schema that has one. So a quota is authored
  and proven by breach, never read back: the check named for it in Stage 5b's deliverables can only ever be
  a note. The breach itself is legible and carries three facts: the refusal is at commit, the usage exceeds
  the quota inside the transaction before the abort (2458 MB against a 2048 MB quota), and 1,024,000
  incompressible 1 KB rows read as 2458 MB — a quota bounds disk blocks, not logical bytes. The floor and
  ceiling are also undocumented: *"Schema quota must be between 2048 and 524288000 MB"*. Where:
  `log-stage-06h`, `runbooks/redshift-connection.md` §S.

- `SUP-132` **`CREATE SCHEMA … AUTHORIZATION` takes a database user, not a role** (measured 2026-09-20).
  Redshift has RBAC roles and they cannot own a schema: given a role the statement answers `ERROR: user
  "<name>" does not exist`, which reads as a missing object rather than a wrong kind of object. A shared
  schema therefore has a non-login user as owner and its grants on a role, which is the shape that keeps a
  schema × project relation many-to-many. Where: `log-stage-06h` 1.3, `runbooks/redshift-connection.md` §S.

- `SUP-133` **`DROP` frees Redshift Managed Storage at once; the `VACUUM` caveat is about `DELETE`**
  (measured 2026-09-20). *"A DELETE statement deletes data from a table and disk space is freed up only when
  `VACUUM` runs"* is about rows removed from a table that still exists. `DROP SCHEMA … CASCADE` over a 1.5
  GB table took `DataStorage` from 1,596 MB to 129 MB in the next 30-minute datapoint, with no `VACUUM`
  anywhere. Reading the caveat as covering both is how a session ends up planning to raise an `[E]` compute
  at 1.44 USD/hour to reclaim zero bytes. Where: `log-stage-05b`, the fourth amendment, and
  `runbooks/redshift-connection.md` §S.

- `SUP-134` **The database user Redshift Serverless creates for the `InfrastructureAccess` reserved SSO role
  is a superuser** (read in `pg_user` on 2026-09-20 in Sandbox and on 2026-10-24 in Production, Stage 6h 0.3
  and Stage 9 9.3). Both namespaces list `IAMR:AWSReservedSSO_InfrastructureAccess_<suffix>` with `usesuper`
  and `usecreatedb` true, a user nobody created: in Production it appeared with the role's first
  IAM-authenticated session (`./aws/warehouse.py` or the compute's apply), before any `CREATE USER`. In
  Sandbox the project role's user, made by `CREATE USER`, reads false on both. An `InfrastructureAccess`
  session that reaches the database by IAM authentication is therefore a superuser session, bounded by the
  permission set and by nothing inside Redshift. Which IAM grant earns the superuser status is not isolated.
  The name also shows how a role-derived user is spelled: `IAMR:<role name>`. Where:
  `log-stage-06h-redshift-connection.md`, 2026-09-20 (0.3) and its `pg_user` table;
  `log-stage-09-deployment-targets.md`, 2026-10-24; `AWS_STATE.md`'s Redshift register.

- `SUP-135` **A Redshift schema shared by a role shares nothing in it, and `pg_default_acl` cannot tell
  you** (measured 2026-10-10, on the first table a project ever wrote). A role holding `USAGE, CREATE ON
  SCHEMA` lets every admitted project create its own tables and carries nothing at table level: the new
  table's `relacl` was null, so a second project granted the same role would have had `CREATE` and read none
  of the first's data — not reduced access, none. The fix is `ALTER DEFAULT PRIVILEGES`, set per creating
  user, so a shared schema owes one statement per admitted project (Lesson 14) plus one `GRANT` per table
  that already exists. And the verification is not where PostgreSQL keeps it: `pg_default_acl` returns zero
  rows after a successful `ALTER DEFAULT PRIVILEGES`, and the privilege lives in `svv_default_privileges`
  alone — the mirror of the schema trap, where `nspacl` is the authority and the `SVV_` view shows only
  RBAC. A statement that reports `FINISHED` and a catalog that reports nothing is Lesson 54's shape, and the
  cheap resolution is to look for the platform's own view before believing either. Where: `log-stage-06h`
  (2026-10-10), `runbooks/redshift-connection.md` §T, `WH-14`.

### The Data API

- `SUP-136` **The Redshift Data API reaches a private workgroup from outside every VPC** (measured
  2026-09-20). `redshift-data execute-statement --workgroup-name … --secret-arn …` runs SQL on a workgroup
  that is `publiclyAccessible: false`, in a private subnet with no default route, from a laptop with no VPN
  — because the Data API is an AWS endpoint and not a database connection. No security group sees it and the
  5439 door is irrelevant to it. Convenient (it is how this repository's instruments read `SVV_*`) and
  load-bearing: a principal holding `redshift-data:ExecuteStatement` has a query path from anywhere, which
  is why `identity/sso` denies the family rather than merely not granting it. It is also asynchronous with
  no waiter, so a poll without a delay reports an empty result for a warehouse that is answering. Where:
  `log-stage-06h`, `runbooks/redshift-connection.md` §V.

- `SUP-137` **The Redshift Data API does not cancel a statement when its client stops polling, and
  `max_query_execution_time` did not stop it either** (measured 2026-09-20, and it cost 9.44 USD). A
  `count(*)` over a triple cross join was submitted through `redshift-data execute-statement`; the client
  gave up polling after 242 s and exited; the statement ran for 23,601 seconds — 6 h 33 min — at base
  capacity, and `ComputeSeconds` reported a flat 7,230 RPU-seconds per 30-minute interval throughout, which
  is 4.017 RPU sustained. The workgroup's `max_query_execution_time` was 1800. Why it did not bite is
  unresolved, and the obvious explanation lost its support within the hour. The first hypothesis was the
  superuser queue — `pg_user` reports `usesuper = true` for the namespace admin, and Redshift exempts that
  queue from WLM and QMR. But AWS's serverless query-queues page says *"Query monitoring rules (QMR) apply
  only at the Redshift Serverless workgroup level, affecting all queries run in this workgroup uniformly"*,
  and its example exempts an admin by giving them a queue with no rules — implying that without queues (none
  here; enabling them is permanent) the rule reaches everyone. So the live candidates are the exemption
  *after all*, or that `max_query_execution_time` as a standalone `config_parameter` is not enforced at all
  and a per-query ceiling exists only through `wlm_json_configuration` — Lesson 56 in its purest form. A
  third: the statement read only catalog tables, which AWS runs *"exclusively on the leader node"*, so it
  may sit outside what both guards govern. The test that separates the three is a long query over a user
  table, as a non-superuser and as the admin. Until then the parameter is possibly inert. The unit is not in
  doubt: seconds, from the 86,399-second service maximum and the QMR examples' own wording;
  `statement_timeout` is the millisecond parameter and is not in the Serverless list. What stopped it:
  `pg_terminate_backend(<session_id>)`, then destroying the workgroup. The `serverless-compute` usage limit
  did not: the statement kept running through the two minutes 5.1 held it breached, while that breach
  refused every query needing the compute. Where: `log-stage-05b` the third amendment and the entry of
  2026-10-18, and the comments on `sandbox/warehouse-compute/main.tf`'s `max_query_execution_time` and
  `layers.py`'s `sandbox/warehouse-compute` row.

- `SUP-138` **The Data API authorizes following, reading and cancelling a statement on no resource**
  (measured 2026-10-25, `production-warehouse-ddl`). `DescribeStatement`, `GetStatementResult` and
  `CancelStatement` granted on `workgroup/*` matched nothing, *"no identity-based policy allows"*, while
  `ExecuteStatement` on the same ARN passed; the three take `"*"` and the condition key
  `redshift-data:statement-owner-iam-userid`. The CLI on the deploy runner keeps one role session across a
  job, so `aws:userid` matches between the two calls. Where: `log-stage-09-deployment-targets.md`,
  2026-10-25; `production/foundation/deploy-anchors.tf`, `FollowItsOwnStatements`. A statement is visible
  only to the identity that ran it (measured 2026-10-26, Stage 9 9.4). `describe-statement` on the two
  statement ids of `awsds-deploy-prod`'s pipeline job, called as the infrastructure user with
  `InfrastructureAccess`, answered *"ResourceNotFoundException … Query does not exist"*, and those two
  `DescribeStatement` calls carry no `errorCode` in Production's trail. A statement's record outside the
  session that ran it is the caller's own output and the trail's `ExecuteStatement` events. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-26.

### Datashares through Lake Formation

- `SUP-139` **A Redshift consumer of a Lake Formation-managed datashare calls Glue and Lake Formation as the
  session's IAM principal, needs `TEMP` on the session's database, and reads with the producer's workgroup
  gone** (measured 2026-10-25, Stage 9 9.7). A SageMaker project's portal session assumes its access role,
  whose `RedshiftDbUser` tag names the database user `IAMR:datazone_usr_role_…`: the refusal named the
  access role (`glue:GetTable`), so the catalog read and the Lake Formation grant belong to the access role,
  never to the role the user is named after. A password user is refused, *"Current user is not authenticated
  with IAM credentials"*; the share's table is an external table, and the query needs `TEMP` on the database
  the session is in, *"permission denied to create temporary tables"*; and a Serverless producer whose
  workgroup was destroyed keeps serving the share from its namespace. The consumer account's Lake Formation
  administrator reads under the account's grant with no grant of its own. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-25; `sandbox/warehouse/iam.tf`,
  `ReadTheGovernedShareCatalog`.

- `SUP-140` **A producer's `REVOKE` on a Lake Formation-managed datashare takes the share out of both
  accounts' control plane and keeps every Lake Formation object** (measured 2026-10-26, Stage 9 xxiv). After
  `REVOKE USAGE ON DATASHARE … FROM ACCOUNT … VIA DATA CATALOG`, `describe-data-shares` by ARN answered
  `InvalidDataShareFault`, *"the ARN doesn't exist"*, to the producer too. The authorization and the
  consumer's association with its catalog were gone, and the federated table read *"No glue catalog
  datashare is found"*. The registration, the federated database, its grants and its LF-Tag, and another
  account's named grants on the table all stayed. A `GRANT` alone brings the consumer back as
  `PENDING_AUTHORIZATION`, invisible to the Lake Formation account. The authorization and a new association
  are owed, after which the table and its tag assignment return by name. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-26.

- `SUP-141` **A datashare granted to a Lake Formation consumer makes Redshift create a `ds:` user and a
  `ds:` role in the producer database, absent from `pg_user`** (measured 2026-10-26, Stage 9 9.5 and xxiv).
  After `GRANT USAGE ON DATASHARE trades_lf TO ACCOUNT '<Data Governance>' VIA DATA CATALOG`, Production's
  user-role grants counted three where two were written: the third is the user `ds:trades_lf_acc_DC_<Data
  Governance>` holding the role `ds:trades_lf`, created by Redshift for the consumer `DC:<Data Governance>`.
  Neither is among the six users `pg_user` lists. After `REVOKE USAGE` the count read two, and after the
  re-grant three again. `sys_datashare_change_log`'s `consumer_account` column cuts the consumer's id at
  twelve characters (read once). A check that compares grants against a register meets this pair as an
  unregistered grantee owned by the platform. Where: `log-stage-09-deployment-targets.md`, 2026-10-26;
  `AWS_STATE.md`'s Redshift register.

### Billing, metrics and the audit export

- `SUP-142` **`ComputeSeconds` lands per half-hour interval, so a Redshift cost read right after an
  expensive query under-reads it** (measured 2026-09-20). The same metric answered 405, then 4,743, then
  94,767 RPU-seconds for the same workgroup within a few hours — the first two while a query was still
  running, and each was written into four tracked files as *the measured cost*. Cost Explorer cannot be used
  as the cross-check on the same day: it returned 0 for every service with zero groups for that date, while
  a negative control three days earlier returned real figures, so its zero means *no data yet* and nothing
  else. Two rules, and neither is about Redshift: a meter that is still accruing has not answered, and *"I
  stopped watching"* is not *"it stopped"*. Where: `docs/PRICING.md` §5, `log-stage-05b`'s three amendments
  to 5.3. The free-trial balance shows what `ComputeSeconds` misses, and keeps moving after the workgroup is
  gone (measured 2026-10-26 and 2026-10-30 in Production's console, Stage 9). The sitting of early
  2026-10-26 read 79 RPU-seconds (0.0079 USD) while the balance fell 0.05 USD, 0.03 of it landing after the
  reading at about 01:50 with no workgroup up. Stage 9 xxiv's sitting that evening read 78 RPU-seconds
  (0.0078 USD) over four statement windows; the balance fell from 299.66 to 299.54, 0.12 USD or 300 seconds
  at 4 RPU, 38 minutes after the workgroup went, and stood at 299.50 on 2026-10-30, 0.16 USD in all. The
  balance bills each query at its 60-second minimum, so the metric under-reads a sitting of short statements
  by an order of magnitude, and a reading within the hour missed a quarter of the bill. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-26 (two entries) and 2026-10-30; `docs/PRICING.md` §5.
  Cost Explorer's lag runs past a day, and a day it holds in part reads cheaper, not absent (read
  2026-11-15 to 2026-11-17 in Sandbox, Stage 19, each a daily `get-cost-and-usage` by service and usage
  type). At 05:05:57 UTC on 2026-11-15, 2026-11-14 and 2026-11-15 held no line, and 2026-11-13, 29 hours
  past its end, held *"3 to 6 hours of its whole-day lines (the alarms 0.1000 against 0.4000 on 2026-11-10
  to 12, the dashboard 0.0083 against 0.0333, the secret 0.0069 against 0.0333, Unified Studio's volumes
  0.1111 against 0.5333 GB-month)"*. At 00:02:33 UTC on 2026-11-16, *"2026-11-14 and 2026-11-15 still held
  none"*, 2026-11-14 a whole day past its end. At 01:12:48 UTC on 2026-11-17, 2026-11-14 held 47 lines,
  *"its last hour in"*, and 2026-11-15, 25 hours past its end, held 44 lines and 9 endpoint hours, *"where
  the 2026-11-14 sitting's hour after midnight alone bills 19"*. Read less than two days after it ends, a
  day can be absent or partial, and a whole-day line below its usual value is the tell. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-17, the entry on `SUP-368`'s line.

- `SUP-143` **Redshift Serverless publishes a `ChargedSeconds` metric beside `ComputeSeconds`, and the two
  diverge for a session held open** (read 2026-10-18 in CloudWatch, Stage 5b). AWS's metric list does not
  name `ChargedSeconds`. For the 18:00Z hour of 2026-10-10 it read 480 against `ComputeSeconds`' 13,733,
  inside a 60-minute plateau at 4 RPU (17:57 to 18:56Z) in which no query of ten seconds or more completed
  and which ended on no call, 3,600 s being the idle-session timeout; the hours of a running 23,601-second
  query read 14,400 on both. That the plateau is a notebook session held open is an inference:
  `redshift_connector` sends `begin transaction` before the first statement. Summed since 2026-09-19,
  `ChargedSeconds` is 122,928 RPU-seconds (12.2928 USD) and `ComputeSeconds` 119,138 (11.9138 USD), with the
  console's 12.10 USD consumed between them; which meter the free trial draws on is not settled. Where:
  `log-stage-05b-redshift-serverless.md`, 2026-10-18; `log-stage-06h-redshift-connection.md`, 2026-10-10
  (3.3 attempted); `runbooks/redshift-connection.md` §J.
  Read again 2026-11-22 in Production against the console's free-trial balance (Stage 9's log, the balance
  after R1): `ChargedSeconds` follows the balance within its cent in three sittings, release F's of
  2026-11-16 (3,120 RPU-seconds, 0.312 USD, against 0.32), xxiv's of 2026-10-26 (1,680, 0.168, against 0.16)
  and R1's of 2026-11-22 (240, 0.024, against 0.02), and over-reads the early 2026-10-26 sitting (720, 0.072,
  against 0.05). `ComputeSeconds` read 139, 78, 0 and 79. `ChargedSeconds` is the closer meter, and which one
  the trial draws on is still not settled.

- `SUP-144` **Sandbox's Redshift Serverless audit export carried nothing while a workgroup existed, and
  Production's carried its first session** (measured 2026-10-17 over the groups' 30-day retention).
  Configuration is not the explanation: the namespace exports all three groups, unchanged since its
  creation. After the first day no record of any kind arrived during any of seven workgroup lifetimes, and
  the namespace's own `rdsdb` sessions arrive in a `default` stream, about 29,000 a day, only while no
  workgroup exists, from about a day after a delete until two minutes after the next create. The one window
  of user activity is the admin's Data API sessions of 2026-09-21, 23 minutes long: 36 of the 268 Data API
  calls CloudTrail holds for those two days, and no session through any other door. The reading of
  2026-10-10 was a sampler's (inference): 155 records at a ~2h25m cadence fit one record per 1 MB
  `FilterLogEvents` page over the 444,502 records the group held, so the *heartbeat* was the pager's, and
  the *stop* at 03:09:06 was that day's first create silencing the stream. The reading to carry: before an
  absence or a cadence in a log group is evidence, count it with an aggregate (Logs Insights `stats count(*)
  by bin(1h)`), not by paging events (Lesson 62's wrong path). Stage 11 must not rest a DLP feed on these
  groups. Where: `log-stage-06h` (2026-10-10, 2026-10-17), `log-stage-05b`, Stage 11. The silence is
  Sandbox's, not the service's (read 2026-10-24, Stage 9 9.3). In Production the three groups under
  `/aws/redshift/awsds-prod-warehouse/` carried the namespace's first session while its workgroup existed:
  `connectionlog` the admin's Data API connection (*"authenticated | 00:26:52 | 127.0.0.1 | warehouse |
  dbadmin | password | TLSv1.3"*), `useractivitylog` its statements, and `userlog` the three `create` events
  of 00:28:31, 00:29:01 and 00:29:06. The Sandbox reading of 2026-10-17 stands for that namespace, and its
  mechanism is unknown. Where: `log-stage-09-deployment-targets.md`, 2026-10-24; `AWS_STATE.md` `EXC-16`.

- `SUP-145` **The Redshift Serverless free trial's 90 days run from the namespace's creation, not from the
  first workgroup** (read 2026-10-25 in the console, Stage 9 9.1; inferred from two accounts' dates). AWS's
  page offers *"$300 credit, which can be used within 90 days of sign-up"* and does not settle when the
  clock starts. Production's console read *"Free trial expiration January 21, 2027"*, 90 days after its
  namespace was created on 2026-10-23 22:07 UTC, while its first workgroup came on 2026-10-24; Sandbox's
  December 19, 2026 is 90 days after 2026-09-20, when its namespace and first workgroup were both created.
  The balance shows only in the Redshift Serverless console: the Management credits page showed no credit on
  2026-09-20, and Cost Explorer carried no Redshift line for Sandbox through 2026-10-17, as AWS writes for
  trial usage. A namespace created ahead of use spends the window. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-25; `log-stage-05b-redshift-serverless.md`, 2026-10-17;
  `docs/PRICING.md` §5.

- `SUP-455` **A Redshift Serverless workgroup's own VPC endpoint adds no hours to the account's
  `USW2-VpcEndpoint-Hours`** (measured 2026-11-22 in Sandbox from Cost Explorer and CloudTrail, Stage 12).
  Each `CreateWorkgroup` is followed within 18 s by a `CreateVpcEndpoint` that `redshift.amazonaws.com`
  invokes: a requester-managed interface endpoint in two subnets, which the same service deletes with the
  workgroup. CloudTrail holds 15 since 2026-09-20. Cost Explorer's daily `USW2-VpcEndpoint-Hours` from
  2026-09-20 to 11-21 fits the CloudTrail lifetimes of the user-made endpoints alone with an absolute
  error of 207 h, and of 315 h once the managed endpoints' two AZs are added. On the ten days with a
  workgroup, Cost Explorer reads a mean of 12.2 h below the user-made hours, where billing the managed
  endpoint would add 12.1. On 2026-09-20 it billed 273 h, against 273.3 user-made and 305.7 with the
  managed endpoints. Sandbox shows no other VPC usage type in October and November, and no Redshift line
  during the free trial (`SUP-145`), so a charge billed under Redshift is not visible before 2026-12-19.
  AWS's page on Redshift-managed VPC endpoints sends their pricing to PrivateLink's, and the Serverless
  connection and pricing pages say nothing of the workgroup's own endpoint. Over the 63 days the bill
  reads 1761 h against 1901 user-made, and a day's residual reaches 35 h, both unexplained. Where:
  `log-stage-12-observability-finops.md`, 2026-11-22; `docs/PRICING.md` §5; `SUP-128`.

## DataZone and SageMaker Unified Studio

### Domain, account association, blueprints and profiles

- `SUP-146` **`datazone create-domain` without `--service-role` answers "Cross-account pass role is not
  allowed" in the caller's own account, naming neither the missing field nor an account** (measured
  2026-08-20 and 2026-08-21, Stage 6 step 0 and verification i). Every variant of 2026-08-20, in Data
  Governance and in Policy Canary, V2 and V1, the execution role's trust with and without
  `aws:SourceAccount`, the conventional name `AmazonDataZoneDomainExecutionRole` included, passed
  `--domain-execution-role` alone and returned the byte-identical `AccessDeniedException` *"Cross-account
  pass role is not allowed."*, though caller and role were in one account and the caller held
  `AdministratorAccess`. On 2026-08-21 the same CLI passing both roles (V2) reached authorization and
  returned the SCP's explicit deny naming the policy. The message is DataZone objecting to the absent
  service role before authorization, so it reads the same from an account an SCP exempts and one it denies,
  and a probe built on it measures no SCP. The V1 variant was not replayed with a service role. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-20 and 2026-08-21; `log-stage-01c-preventive-policies.md`.

- `SUP-147` **A DataZone domain's account association is an organization-scoped RAM share that auto-accepts,
  under `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, a permission the V1 user guide does
  not name** (measured 2026-08-21, Stage 6 1.3). The console's *AWS Organization-only RAM share* and *IAM
  users can access APIs only* choices created `DataZone-EXTENDED_ACCESS-<domain>-ORG-ONLY`; `ram
  get-resource-share-invitations` returned an empty list in both member accounts, so there is no accept step
  and the V1 guide's 7-day expiry never starts. `ram list-permissions --resource-type datazone:Domain`
  publishes six permissions, and the guide's `AWSRAMPermissionDataZoneDefault` and
  `AWSRAMPermissionDataZonePortalReadWrite` are not among them. The attached permission, version 10, carries
  152 actions against the default `AWSRAMDefaultPermissionAmazonDataZoneDomain`'s 111, a strict superset
  whose 41 extras are the V2 workbench surface (notebooks, cells, `StartCompute`/`StopCompute`, connections,
  `GetDomainExecutionRoleCredentials`, `StartAccountBootstrapAction`). `--permission-type CUSTOMER_MANAGED`
  returns empty, so nothing narrower can be had. The association had no public API (read 2026-08-16). The
  designations guide, read 2026-11-13, gives minimum versions of the domain's RAM permissions for enabling or
  authorizing a blueprint from an associated account, v11 for this one. Measured 2026-11-14: the share still
  carries version 10, and what that withholds from an associated account is `SUP-360`. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-21; `open-questions.md` 21; `upstream-releases.md`, the
  designations row. Read again 2026-11-19 (Stage 19): the share moved to version 13 that day, the only
  version RAM would attach (`SUP-360`). Where: `log-stage-19-smus-native-data-product.md`, 2026-11-19.

- `SUP-148` **`CreateProjectProfile` refuses `ToolingLite` as an on-demand element of a project profile**
  (measured 2026-08-21, Stage 6 1.5). Both profile creates failed with DataZone 400, *"ToolingLite
  environment blueprint configuration must have deployment mode ON_CREATE"*, and nothing was created. The
  domain's descriptions read `ToolingLite` (*"Create basic resources for SageMaker Unified Studio
  project."*) as a second base beside `Tooling`, not a capability, so it cannot ride a `Tooling` profile as
  an extra, and two bases would provision every project twice; the service states no reason (inferred from
  the descriptions). The console's Blueprints page never offers `ToolingLite`; its description comes from
  `get-environment-blueprint`. Where: `log-stage-06a-unified-studio.md`, 2026-08-21; `docs/SMUS.md`
  §Blueprints.

- `SUP-149` **DataZone's managed blueprint roster and the console's Blueprints page disagree, and blueprint
  names taken from documentation prose do not resolve in the API** (measured 2026-08-21 on the live domain,
  Stage 6 1.4; re-read 2026-10-18 and 2026-10-30). `datazone list-environment-blueprints --managed` returned
  23 names against the console's 13 (24 on 2026-10-30, `SageMakerAIDomain` added).
  `AmazonBedrockGenerativeAI` is a console grouping with no API identifier: the API returns its seven
  `AmazonBedrock*` blueprints and no aggregate. `LakeHouseDatabase` in the console is `DataLake` in the API.
  `LakehouseAdmin`, `S3Bucket`, `S3TableCatalog` and `ToolingLite` are returned by the API and never offered
  by the console. `EMRServerless` is `EmrServerless`, `EMRonEC2` is `EmrOnEc2` and `Quicksight` is
  `QuickSight`; a Terraform plan failed on the prose names before anything was applied. The API, and so
  Terraform, takes only the API name. Where: `docs/SMUS.md` §Blueprints;
  `terraform-live/data-governance/governance/locals.tf`; `terraform-modules/sagemaker-prereqs/variables.tf`.

- `SUP-150` **`EnvironmentRolePermissionBoundary` is write-only on a blueprint configuration**: the schema
  accepts it and no read returns it (Stage 6a, 2026-08-22). Boundary drift can never appear in a `terraform
  plan`; the only door is `iam get-role` per role, since `list-roles` omits `PermissionsBoundary` by
  documented contract. A control that cannot be read back needs a sentinel, which is `US-8`. Read again
  2026-10-19 (Stage 18 2.5): DataZone's own `get-` and `list-environment-blueprint-configurations` return
  `environmentRolePermissionBoundary`, in Sandbox and in Staging; Cloud Control's `get-resource`, the read
  `awscc` makes, omits it. So drift still never appears in a plan, the configuration's value is a DataZone
  read away, and a role's own boundary is still `get-role`'s. The service injects the field into the
  environment's stack template as the `PermissionsBoundary` of `ToolingUserRole` and of the two conditional
  Bedrock roles; the template's two conditional EMR roles (`createEmrResourceInTooling`) declare none, so
  enabling EMR in `Tooling` creates two unbounded roles (read 2026-08-22 in the stack's template, Stage 6
  verification v). A reconciliation's `UpdateStack` by the provisioning role, `invokedBy` DataZone, re-sent
  `permissionsBoundaryArn` with the other parameters on 2026-10-11 at 22:05:48Z, and the project role still
  carried the boundary on 2026-10-17. The three roles a stack creates carry the tag `AmazonDataZoneDomain`,
  which finds them where a name match on `datazone` finds one. Where: `log-stage-06a-unified-studio.md`,
  2026-08-22 and 2026-08-26; `log-stage-06d-unified-studio-remainder.md`, 2026-10-17.

- `SUP-151` **An associated DataZone domain lists from every member account, with an ARN naming the owning
  account.** A check that counts domains per account therefore reports the association working as a finding.
  Measured when `./aws/studio.py` failed because the step succeeded (Lesson 31).

- `SUP-152` **`list-environment-blueprint-configurations` cannot succeed from a member account until the
  association exists**; after it, the same call returns `{"items": []}`. The empty list is the success
  signal, indistinguishable from an absence to anything that only checks the contents. Disassociation
  reverses it (measured 2026-09-06, Stage 6b 1.4 and 1.5, and 2026-10-22 in Staging, Stage 18 8.5): the same
  call from the member account raises *"UnauthorizedException: Unauthorized"*, naming no policy, where one
  step earlier it had returned 0 items, and the `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` share leaves `ram
  get-resource-shares --resource-owner OTHER-ACCOUNTS`. Where:
  `log-stage-06b-development-becomes-staging.md`, 2026-09-06; `log-stage-18-staging-deployment-project.md`,
  2026-10-22.

- `SUP-153` **A blueprint configuration is applied from the member account**, an existing one is immutable
  through `awscc`, and an incomplete one pins its projects in both directions: they can neither deploy nor
  be torn down. None of the three is on the authoring API's page; each cost a sitting. The incomplete
  configuration's errors (measured 2026-08-22, Stage 6 pass 3): with `Tooling`'s manage-access role null,
  *"Manage Access Role Arn for environment blueprint id 4k186sfh08eqxc not defined"*, on deploy and on the
  stuck project's delete, the project `ACTIVE` and its environment failed before any stack existed; without
  `S3Location`, *"Invalid S3 path provided null"* in both directions; without `KmsKeyArn`, the AWS managed
  key and no error. `PutEnvironmentBlueprintConfiguration` accepted all three missing, while the console's
  Enable-Tooling wizard always asks for them. Adding the fields through `awscc` met `NotUpdatableException`;
  a full-object `put-environment-blueprint-configuration` per member account completed them, and the stuck
  projects then deleted. Where: `log-stage-06a-unified-studio.md`, 2026-08-22;
  `terraform-modules/sagemaker-prereqs/blueprints.tf`.

- `SUP-154` **`PutEnvironmentBlueprintConfiguration` enables a blueprint without its
  `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant, whose entity identifier is `<account-id>:<blueprint-id>`**
  (measured 2026-08-22, Stage 6 pass 3). With the profile grants in place, `CreateProject` succeeded and the
  project died in deployment, *"Caller is not authorized to create environment using blueprintId
  4k186sfh08eqxc"*, rolled back with no stack in the member account. `list-policy-grants` read zero such
  grants on all 22 configurations, 11 per member account; the console's enable-blueprint flow fills
  *Authorized domain units*, which emits the grant, and the API call does not. The entity identifier joins
  the configuration owner's account, the member's, to the blueprint id: the bare id, `domain|id` and the ARN
  are rejected, *"Format of EnvironmentBlueprintConfigurationId is invalid"*, the domain account's id
  answers *"does not exist in account"*, and the API reference gives no format. AWS's sample
  `aws-samples/sample-automate-sagemaker-unified-studio-using-iac` uses the same form. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-22; `terraform-modules/sagemaker-prereqs/grants.tf`;
  `docs/SMUS.md`.

- `SUP-155` **`CreateProjectProfile` validates no parameter against the blueprint templates, and
  `UpdateProjectProfile` validates what it skipped** (measured 2026-08-22, Stage 6 pass 3, attempt 4). A
  profile locking `Tooling`'s `lifecycleManagement` to `"true"`, against the template's
  `ENABLED`/`DISABLED`, was created on 2026-08-21 and failed only at the first project's stack: *"Stack
  creation failed with Parameter 'lifecycleManagement' must be one of AllowedValues"* (CloudFormation 400).
  The fix through `UpdateProjectProfile` then met *"Missing required Blueprint parameter(s): bucketName"*:
  the update requires every blueprint parameter without a default, `S3Bucket.bucketName` and
  `S3TableCatalog.catalogName` across eleven blueprints, which the create had accepted absent. A profile
  that creates cleanly can be impossible to update, and a bad locked value surfaces at the first deploy; the
  downloaded templates' `AllowedValues` are the check before an apply. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-22; `terraform-live/data-governance/governance/locals.tf`.

- `SUP-156` **A project profile can be listed by anyone and instantiated by nobody until a
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` policy grant names the caller** (measured 2026-08-22 on a domain
  created through the API, Stage 6 1.7). The portal offered both profiles and *Create project* answered
  *"User is not permitted to perform operation: CreateProject"*, identical with the VPN tunnel up and down.
  `list-policy-grants` on the root domain unit returned an empty list for `CREATE_PROJECT` and
  `CREATE_PROJECT_FROM_PROJECT_PROFILE`, and `list-entity-owners` one owner, the group profile of the role
  that created the domain, the only principal able to create a project. `AWS::DataZone::PolicyGrant` takes a
  `Group` principal and a `ProjectProfiles` list, and the service accepted an Identity Center group id with
  no DataZone group profile behind it. Every field of the grant is `createOnly` in the CloudFormation
  schema, so moving it to another group replaces it. Where: `log-stage-06a-unified-studio.md`, 2026-08-22;
  `terraform-live/data-governance/governance/grants.tf`.

- `SUP-157` **DataZone refuses connection operations to an identity that is not a project member, in its own
  authorization layer rather than in IAM** (measured 2026-09-21). `datazone list-connections` as the
  account's `InfrastructureAccess` role: *"User is not permitted to perform operation: ListConnections"* —
  no IAM policy is involved and none can fix it. So the account's administrator cannot read, let alone
  create, a project's connections; the act belongs to a project member in the portal. Lesson 28's
  intersection, with the second permission system being the product's own. Where: `log-stage-06h`
  (2026-09-21). The same layer refuses `CreateEnvironment` to an identity holding no designation on the
  project, *"User is not permitted to perform operation: CreateEnvironment DesignationPolicy does not allow
  access"* (measured 2026-10-30, the infrastructure user in Sandbox, Stage 6d 2.6 item 3), and refuses
  `GetAsset`, `GetDataProduct` and `ListPolicyGrants` for `CREATE_ENVIRONMENT` and `USE_ASSET_TYPE` to Data
  Governance's `InfrastructureAccess` (measured 2026-09-13 and 2026-10-18), so an asset behind a listing is
  read through `GetListing`. A membership flips the answers: Sandbox's `InfrastructureAccess` role, made
  `PROJECT_CONTRIBUTOR` through a group profile in the portal on 2026-10-15 at 06:15Z, is answered
  `ListConnections` and `GetAsset`, while Data Governance's session stays refused (read 2026-10-18). A
  member account's `GetProjectProfile` and `GetGroupProfile` fail differently, on the domain's resource
  policy: *"no resource-based policy allows the datazone:GetProjectProfile action"*. What the layer
  answers to a non-member is a project's existence and shape (measured 2026-11-11, Stage 19 step 4.5):
  Production's `InfrastructureAccess`, a member of no project, read `ListProjects`, every project of the
  domain, and on `governed-lake`, a project of another account, `GetProject`, `ListProjectMemberships` and
  `ListEnvironments`, and was refused `ListConnections`; Data Governance's read the member lists of all six
  projects the same day, and `ListDataSources` and `GetDataSource` of the two deployment projects it is no
  member of. Membership confines a project's connections and catalog, not its name, its members, its
  environments or its data sources. A member's designation bounds its writes in the same layer (measured
  2026-11-14, Stage 19): Sandbox's `InfrastructureAccess`, a `PROJECT_CONTRIBUTOR` of
  `test-experimentation`, was refused `DeleteProjectMembership` there, *"User is not permitted to perform
  operation: DeleteProjectMembership DesignationPolicy does not allow access."*; member management is
  `PROJECT_OWNER`'s by that designation's own description (`upstream-releases.md`, read 2026-10-30). A member
  account's resource-policy refusals follow the version of the permission on the domain's RAM share
  (`SUP-360`, measured 2026-11-14): version 12 names `GetGroupProfile`, and no version names
  `GetProjectProfile`. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-10-30;
  `log-stage-06f-data-governance.md`, 2026-09-18, 2026-10-18 and 2026-10-26;
  `log-stage-19-smus-native-data-product.md`, 2026-11-11; `aws/catalog.py`. Read again 2026-11-16 (Stage
  19 release F): Data Governance's `InfrastructureAccess`, no member of `deploy-staging`, read its source's
  runs and their activities (`ListDataSourceRuns`, `ListDataSourceRunActivities`), each run's `added` count
  among them, and was refused a `Search` of the assets the project owns, *"User is not permitted to perform
  operation: Search"*. A non-member reads whether a project's source has added an asset, never the asset.
  Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15. Read again 2026-11-18 (Stage 6d 2.7 step
  1, reading (iii)): the same contributor of `test-experimentation` was refused `UpdateProject` there, with
  `projectProfileVersion` `latest` and the project's own user parameters, *"User is not permitted to perform
  operation: UpdateProject DesignationPolicy does not allow access."*, the project unchanged and both
  accounts' trails reading `AccessDenied` with no `errorMessage` (`SUP-162`). The project's creator, its
  owner, was accepted the same update from the portal on 2026-10-11 (`SUP-168`), so a project's update is
  its owner's, never an operator's call as a contributor. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-11-18. Read again 2026-11-19 (Stage 6h decision 3): the
  same role, a `PROJECT_CONTRIBUTOR` of `eighth-experimentation`, was accepted `UpdateConnection` on the
  Redshift connection the project's owner made in the portal, its database and its `lineageSync` changed,
  both accounts' trails reading the call with no `errorCode`. A connection's update is a contributor's where
  a project's update is its owner's; the managed designations' descriptions name neither action, so a
  contributor's writes are read by attempt. Where: `log-stage-06h-redshift-connection.md`, 2026-11-19. Read
  again 2026-11-19 (Stage 19), after the share's move to version 13 (`SUP-360`): `GetGroupProfile` answered
  from Sandbox, Staging and Production as each account's `InfrastructureAccess`, and `GetProjectProfile` was
  refused in all three, *"because no resource-based policy allows the datazone:GetProjectProfile action"*.
  Where: `log-stage-19-smus-native-data-product.md`, 2026-11-19. Read again 2026-11-21 (Stage 6a): the layer
  confines `GetEnvironment` where it lists environments to anyone. Production's `InfrastructureAccess`, no
  member of `test-experimentation`, read its five environments with `ListEnvironments` and was answered
  `GetEnvironment` on one of them, `ACTIVE` in that listing, *"ResourceNotFoundException ... Environment not
  found"*; Sandbox's, no member of `deploy-production`, read that project's pair the same way. A deleted
  environment and an id that never existed receive the same wording (read the same hour), so a non-member
  cannot tell a deleted environment from one it may not read; `./aws/studio.py` `US-15` reads the
  environment's stack in the resource's account instead. Version 14 of the share's permission names
  `GetProjectProfile`, which answers from the three member accounts since the share's move to it that day
  (`SUP-360`). Where: `log-stage-06a-unified-studio.md`, 2026-11-21.

- `SUP-158` **An IAM role in a DataZone domain is a group and one user profile per session name, and a
  policy grant takes the group.** Its ARN resolves as a user identifier to one session's user profile, and
  as a group identifier to the role's `IAM_ROLE_SESSION_GROUP` profile, which every session belongs to.
  `CreatePolicyGrant` with the ARN as a user is refused, *"Group profile already exists for the given User
  profile"*, though the service model's pattern admits it; the grant goes to the group by its profile id,
  which Cloud Control's `GetResource` for `AWS::DataZone::GroupProfile` resolves from `<domain>|<role ARN>`
  (Stage 18 2.7, 2026-10-19). The domain keeps a user profile for every session name a role has called
  under (read 2026-11-11, `search-user-profiles --user-type DATAZONE_IAM_USER`, Stage 19): of 50 such
  profiles, 30 were `awsds-deploy-sandbox-test`'s and 6 `awsds-deploy-staging`'s, each with its own
  `sessionName` of the form `botocore-session-<digits>`, the SDK's name for a role assumed through a
  profile that sets no `role_session_name`, so every pipeline job adds one; the four accounts'
  `InfrastructureAccess` roles held one each, named for the person; ten were project roles', with no
  session name, five of them of projects deleted since (`SUP-165`). Each carries `groupProfileId`, the
  role's group. A project role's profile is a member of its own project: `list-project-memberships` reads
  it as `PROJECT_CONTRIBUTOR` in each of the five projects that hold a `Tooling` environment, the two
  created that day included. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-11.

- `SUP-159` **A role's `IAM_ROLE_SESSION_GROUP` profile exists only after the role's first DataZone call,
  and until a person makes it a project member the CI/CD CLI's deploy stops on `ListConnections`** (measured
  2026-10-19 in Sandbox, Stage 8, and 2026-10-21 in Staging, Stage 18 4.3). Before the first run, Cloud
  Control's `<domain>|<role ARN>` read answers `NotFound`, and `search-group-profiles --group-type
  IAM_ROLE_SESSION_GROUP` lists SSO groups among its six profiles while `--search-text` with the role's name
  answers nothing; a role's profile is found by its `rolePrincipalArn`. The first run creates the profile
  (`ASSIGNED`) and a session-bound user profile, and fails as a non-member: *"User is not permitted to
  perform operation: ListConnections"*, then *"No S3 URI found for connection unknown"* for each storage
  item. A membership by `userIdentifier` with the role's ARN is refused, *"Group profile already exists for
  the given User profile"*; `create-project-membership` with `groupIdentifier=<profile id>` works, and the
  retried job succeeded. No IAM grant replaces the membership. The call that creates the profile is a
  read of a project, not any call (measured 2026-11-11 on Production's `InfrastructureAccess`, Stage 19
  step 4.5): `ListDomains`, `ListEnvironmentBlueprintConfigurations`, `ListProjects` and `GetDomain` were
  each answered and left the role's group profile `NotFound`; four seconds after the role's first
  `GetProject` it read `ASSIGNED`. A role that has only listed cannot be named in a policy grant. Where:
  `log-stage-08-cicd-pipelines.md`, 2026-10-19; `log-stage-18-staging-deployment-project.md`, 2026-10-20
  and 2026-10-21; `log-stage-19-smus-native-data-product.md`, 2026-11-11.

- `SUP-160` **A project profile's override of a blueprint parameter marked `isEditable` false reaches the
  deploy, and `Tooling` creates a SageMaker AI domain only when `enableSpaces` is `"true"`** (read
  2026-10-19 in the blueprint and its templates, and measured the same day in Staging, Stage 18 2.6 and
  3.2). The live blueprint marks `enableSpaces` and `maxIdleTimeoutInMinutes` not editable; a profile
  overriding `maxIdleTimeoutInMinutes` to 120 deploys, and a profile locking `enableSpaces` `false` produced
  a stack with `enableSpaces` `false`. In `Tooling` (65 template parameters) `SageMakerSpacesDefaultDomain`
  carries `sageMakerDomainRequired`, `isDefaultTooling` and `enableSpaces == "true"`; `ToolingLite` creates
  its `AWS::SageMaker::Domain` with no condition. The Staging stack held thirteen resources and no SageMaker
  AI domain, and the portal's Workflows tool refused: *"This tool is not available for this project: Spaces
  are not enabled in this project profile. Please contact your admin."* Where:
  `log-stage-18-staging-deployment-project.md`, 2026-10-19 and 2026-10-20.
  **Read again 2026-11-18** (Stage 6d 2.7 step 5): `experimentation` locks `enableSpaces` `false` and
  deploys the `SageMakerAIDomain` blueprint `ON_CREATE` beside it. Its project `throwaway-6d` got the same
  thirteen `Tooling` resources with no domain, the blueprint's domain beside them, and the Workflows tool
  opened: `ListWorkflows` and `ListWorkflowRuns` answered to the project role from 21:48:11 to 21:48:58
  UTC. A project with no SageMaker AI domain is refused; one whose only domain is the blueprint's is not.
  Where: `log-stage-06d-unified-studio-remainder.md`, 2026-11-18.

- `SUP-161` **A V2 domain refuses the three catalog designations the DataZone API lists** (measured
  2026-10-20, Stage 18 6.1). `create-project-membership` with `PROJECT_CATALOG_VIEWER`,
  `PROJECT_CATALOG_CONSUMER` or `PROJECT_CATALOG_STEWARD` answers `ValidationException` *"Project member
  with designation <it> cannot be added to project in V2 domain"*, and `PROJECT_CONTRIBUTOR` is admitted.
  The CLI's model (`datazone/2018-05-10`) lists all five, while SageMaker Unified Studio's user guide names
  two project roles, Contributor and Owner, both working on the project's credentials: no designation gives
  a person a view with no write. Where: the Stage 18 log, 2026-10-20.

- `SUP-162` **DataZone refuses `ListDomains` to a project's role that IAM allows** (measured 2026-10-26,
  Stage 10 2.1). The role's managed policy grants `datazone:List*` on `*` and nothing denies it, yet the
  call reads *"User is not permitted to perform operation: ListDomains"*, CloudTrail `AccessDenied` with no
  `errorMessage`. The CI/CD CLI 1.0.9 makes the call on every deploy with bootstrap actions, the manifest's
  domain id unused, so a deploy from a space stops there; reported upstream as [issue
  413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413). Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-26.
  Read 2026-11-15 on `bundle --targets dev` from the laptop as Sandbox's `InfrastructureAccess` (Stage 19
  step 17's rehearsal): `bundle` makes the call too, one second after `DescribeStacks` refused *"Stack with
  id cicd-test-domain-stack does not exist"*, its configuration carrying the target's region alone
  (`commands/bundle.py`). The call answered, and the bundle took the one domain listed; the code
  (`helpers/datazone.py`) raises on two. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15.

- `SUP-349` **The console's account association is one public RAM call, `AssociateResourceShare` on the
  domain's share, after which RAM writes the domain's sharing policy in the caller's session** (read
  2026-11-11 in Data Governance's trail of the console act of 2026-10-19, then measured the same day,
  Stage 19 step 4.2). The console called `ram:GetResourceShares` filtered by the permission
  `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, then `ram:AssociateResourceShare` with the
  account id as the one principal, on the share `DataZone-EXTENDED_ACCESS-<domain id>-ORG-ONLY`; one second
  later `datazone:PutDomainSharingPolicy` followed, `invokedBy` and user agent `ram.amazonaws.com`, under
  the same session, its policy naming every associated account. No other write appears between the page's
  load and its refresh. `aws ram associate-resource-share --resource-share-arn <the share> --principals
  <account> <account>` as the domain account's InfrastructureAccess associated Staging and Production at
  04:37:18 UTC: both read `ASSOCIATED` at 04:37:19, `PutDomainSharingPolicy` followed twice (04:37:20 and
  04:37:21, three principals in each policy), no invitation was raised under organization-wide sharing,
  and each account read the share `ACTIVE` as `OTHER-ACCOUNTS`. AWS documents the association as a console
  act and the DataZone API carries no call for it, which this project recorded as "no public API" from
  2026-08-21. The caller needs `datazone:PutDomainSharingPolicy` beside the RAM action. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-11.

- `SUP-353` **Two policy grants of one type on one domain unit, created at once, leave one of them
  refused with `ResourceConflict`** (measured 2026-11-11 in Data Governance, Stage 19 step 4.5). One
  apply created two `CREATE_PROJECT_FROM_PROJECT_PROFILE` grants on the root domain unit in parallel,
  through `awscc_datazone_policy_grant`: one was created in 6 s and the other failed, *"Waiting for Cloud
  Control API service CreateResource operation completion returned: waiter state transitioned to FAILED.
  StatusMessage: failed conditions: VERSION EQ [S] (Service: DataZone, Status Code: 409 ...). ErrorCode:
  ResourceConflict"*. `list-policy-grants` read three grants of the type, the refused one absent; the
  re-plan read 1 to add and its apply created it in 8 s. The wording reads as a conditional write on a
  version the first grant had just moved (inferred), so the grants of one type on one unit behave as one
  record. Two grants on two different entities, each target's two blueprint grants in the same sitting,
  were created in parallel with no refusal. An apply that adds several grants to one unit runs with
  `-parallelism=1`, or is applied twice: run that way the same day, six grants of three types on the
  same unit were created in 72 s with no refusal. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-11.

- `SUP-360` **A DataZone domain's RAM share keeps the version of its managed permission it was created
  with, so an action AWS adds to the permission later reaches an associated account only once the share is
  moved to the default version, the one version RAM attaches** (measured
  2026-11-14 in Data Governance and Sandbox, `upstream-releases.md`'s re-read). `ram
  list-resource-share-permissions` on `DataZone-EXTENDED_ACCESS-<domain id>-ORG-ONLY`, created 2026-08-21 with a
  `lastUpdatedTime` of that same second, read `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`
  at version 10, `defaultVersion` false; `ram list-permission-versions` read version 11, of 2026-10-26, and
  version 12, of 2026-11-03, the default. Read with `ram get-permission`: version 11 adds
  `datazone:GetDesignation` and `ListDesignations` to version 10's 152 actions, and version 12 adds
  `GetGroupProfile`, `ListDeployableEnvironmentBlueprints`, `UpdateAssetOwner` and six `DataApp` actions, 163
  in all. From Sandbox, as InfrastructureAccess, `ListDesignations` on the domain answered *"is not
  authorized to perform: datazone:ListDesignations on resource:
  arn:aws:datazone:us-west-2:<account>:domain/<domain id> because no resource-based policy allows the
  datazone:ListDesignations action"*, while `GetDomain` from the same session answered and `ListDesignations`
  from Data Governance returned the two managed designations. The designations guide gives minimum versions
  of the permission, v11 for this one, and does not say that a share stays at the version it was created
  with. Version 10 names `GetUserProfile` alone of the profile reads, which accounts for the
  `GetGroupProfile` refusal the CLI's deploys from a member account have logged since 2026-10-19, in the same
  wording (`SUP-157`); the share has not been moved to confirm it. Moving it to the default version is a RAM
  write in the domain's account. Where: `upstream-releases.md`, the designations row;
  `waiting-on-the-user.md`. Read again 2026-11-19 (Stage 19, before 4.12): `list-permission-versions` read
  version 13, created 2026-11-16T21:08:23Z, as the default and the only `ATTACHABLE` version, versions 1 to
  12 `UNATTACHABLE`; version 13 adds `datazone:GetSystemTableExportConfiguration` to version 12's 163
  actions. Version 12, which the user had chosen on 2026-11-17, could no longer be attached:
  `AssociateResourceSharePermission` takes only a permission's default version, by its API reference. The
  share moved from version 10 to 13 at 02:20:31 UTC on the user's word, `associate-resource-share-permission
  --permission-version 13 --replace` answering `{"returnValue": true}`. The association read
  `lastUpdatedTime` 02:20:33 and the share's own `lastUpdatedTime` stayed at 2026-08-21. At 02:21:01 `ram
  get-resource-policies` on the domain read version 13's 164 actions in the same statement, principals and
  `aws:PrincipalOrgID` condition. From Sandbox, Staging and Production as `InfrastructureAccess`,
  `GetGroupProfile`, `ListDesignations` and `GetDesignation` then answered, and `GetProjectProfile` was still
  refused in the same wording: version 10's missing `GetGroupProfile` was the cause of the deploys'
  refusals, though no deploy has run since. RAM's user guide states what this entry measured, where a
  DataZone reader does not look: a share is never moved to a new version by itself, and an AWS managed
  permission's move cannot be reverted once saved. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-19. Read again 2026-11-21 (Stage 6a): version 14 is the default and the only `ATTACHABLE` version,
  versions 12 and 13 `UNATTACHABLE`, and the share still holds 13, `ASSOCIATED`. `list-permission-versions`
  dates version 14 2026-11-18T20:03:32Z, earlier than the move of 2026-11-19 at 02:20:31Z that took version
  13 as the default; `get-permission` answers `creationTime` and `lastUpdatedTime` as the moment of each
  call, for every version, so a version's date is read from the listing. Version 14 adds nine actions to
  version 13's 164 in an otherwise identical statement: `GetProjectProfile`, `ListProjectProfiles`,
  `ListGroupsForUser`, `GetAssetType`, `GetSubscriptionEligibility`, `GetUpdateEligibility`,
  `StartMetadataGenerationRun`, `GetAccountPool` and `ListAccountsInAccountPool`. Neither version names
  `ListEntityOwners`: Sandbox's `InfrastructureAccess` was refused it on the root domain unit, *"because no
  resource-based policy allows the datazone:ListEntityOwners action"*, and Data Governance's read the unit's
  one owner. The share moved to version 14 at 05:45:59Z on the user's word, `associate-resource-share-permission
  --permission-version 14 --replace` answering `{"returnValue": true}`; the association read
  `lastUpdatedTime` 05:46:02Z and the share's own stayed at 2026-08-21. At 05:46:17Z the domain's
  org-principals statement held version 14's 173 actions and no other, beside the unchanged statement of 20
  actions for `sagemaker.amazonaws.com`. At 05:46:23Z `GetProjectProfile` answered from Sandbox, Staging and
  Production as `InfrastructureAccess`, refused at 05:45:20Z *"because no resource-based policy allows the
  datazone:GetProjectProfile action"*, and `ListEntityOwners` stayed refused in all three. Where:
  `log-stage-06a-unified-studio.md`, 2026-11-21. Read again the same day (Stage 20 8.6), on version 14: the
  CI/CD CLI's `bundle` from Sandbox as `InfrastructureAccess` made two `GetGroupProfile` calls at 20:27Z,
  both answered, where Stage 19 step 17's run of 2026-11-15, on version 10, read both refused. Where:
  `log-stage-20-dbt-lineage.md`, 2026-11-21.

- `SUP-361` **`list-environment-blueprints` and `get-environment-blueprint` date one managed blueprint
  differently** (measured 2026-11-14 on `awsds-studio`, `upstream-releases.md`'s re-read). `datazone
  list-environment-blueprints --managed` read `SageMakerAIDomain` with `createdAt` and `updatedAt` both
  2026-08-19T22:44:32Z, from Data Governance and from Sandbox alike. `get-environment-blueprint` on the same
  identifier read `createdAt` 2026-08-21T00:49:55Z and `updatedAt` 2026-10-22T22:46:51Z, the dates the reading
  of 2026-10-30 recorded, with the template `DataZone-SageMakerAIDomain-prod-20260905` and its 17 user
  parameters. A roster listing does not show that a blueprint's template moved; the get does. Where:
  `upstream-releases.md`, the `SageMakerAIDomain` row. Read again 2026-11-22 on `RedshiftServerless`
  (Stage 21): the get reads `createdAt` and `updatedAt` both 2026-05-13T21:31:31Z, while the template object
  behind its `templateUrl` read `LastModified` 2026-11-13T19:43:40Z on 2026-11-18 (`SUP-378`) and
  2026-11-21T01:19:23Z on 2026-11-22, 10,532 bytes both times. The object is rewritten in place with no
  change to the blueprint's dates, so its `LastModified` dates a rewrite, not a release; a change of content
  under the same name is read from the object's `ETag` (`"d516acd3183d361cf3b92a12ec19dd95"` on 2026-11-22).
  Where: `log-stage-21-redshift-s3-data-products.md`, 2026-11-22.

- `SUP-378` **The `RedshiftServerless` blueprint's template treats a base capacity of 128 and a maximum of 0 as
  sentinels, and the blueprint's user parameters default the maximum to 512 RPU** (read 2026-11-18, Stage 21
  1.3, the template `DataZone-Amazon-SageMaker-RedshiftServerlessDefault-prod-20250515.template.json`,
  `LastModified` 2026-11-13T19:43:40Z, through the blueprint's `templateUrl`). `redshiftBaseCapacity` and
  `redshiftMaxCapacity` are `Number`s with no `AllowedValues`, defaults 128 and 0. The workgroup gets
  `BaseCapacity` only when the base is not 128, `MaxCapacity` only when the maximum is not 0, and
  `PricePerformanceTarget` `{Level: 50, Status: ENABLED}` only when the base is 128. The blueprint's own
  user parameters differ from the template's defaults: `redshiftMaxCapacity` `"512"` (template 0),
  `provisionManagedSecret` `"true"` (false), and the names `redshift-serverless-workgroup` and
  `redshift-serverless-namespace` (`datazone-workgroup`, `datazone-namespace`). An unconfigured create
  therefore gives a workgroup on a price-performance target with no base and a 512-RPU maximum; a locked
  override of the base holds a floor. No AWS page states the sentinels or `MaxCapacity`'s range. Where:
  `log-stage-21-redshift-s3-data-products.md`, 2026-11-18; `data-governance/governance/locals.tf`.

- `SUP-382` **`ram get-permission` on an AWS-managed permission answers the time of the call as its
  `creationTime` and `lastUpdatedTime`** (measured 2026-11-19 in Data Governance, Stage 17 3.3). Two calls
  on `AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain`, version 3, made at 02:21:16.69 and
  02:21:18.59 UTC, answered `02:21:18.543Z` and `02:21:19.740Z` in both fields, and a call at 02:11:47 had
  answered `02:11:49.944Z`. `ram list-permission-versions` dates each version with a fixed past time
  (`AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`: version 12 2026-11-03, version 13
  2026-11-16). The CLI's reference describes the two fields as *"The date and time when the permission was
  created"* and *"last updated"*. A permission's age is read from `list-permission-versions`, never from
  `get-permission`. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-19. Read again 2026-11-19
  (Stage 19): `get-permission` on `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, versions 10 to
  13, called from 02:09:50 to 02:10:14 UTC, dated each version at the second of its own call. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-19.

- `SUP-383` **RAM shares a DataZone domain with the service principal `sagemaker.amazonaws.com`, which its
  table of shareable resources says it cannot** (measured 2026-11-19 in Data Governance, Stage 17 3.3).
  RAM's *Shareable AWS resources* page marks `datazone:Domain` *"Can share with service principals: No"*,
  against AWS's page on a SageMaker data source and the managed permission
  `AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain`, whose resource type is
  `datazone:Domain`. `awscc_ram_resource_share` (awscc 1.106.0, CloudFormation's
  `AWS::RAM::ResourceShare`) created `DataZone-dzd-d8yrvx1ko7im6o-SageMaker` in 7 seconds at 03:02:35 UTC,
  with the domain, that principal, that permission and four source accounts in `sources`. Read at 03:03:
  the share `ACTIVE`, the principal and the domain `ASSOCIATED`, the permission at version 3 `ASSOCIATED`,
  and each source association `ASSOCIATED`. The apply's wording is the reading where the table and the
  service disagree; whether a data source then runs is `EXC-11`'s. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-19. Read 2026-11-19 and 2026-11-20: the `Tooling`
  data source of each of three projects in Sandbox, an account associated with the domain, ended its first
  run after the share `SUCCESS`, where AWS's page describes the domain's own account alone; `EXC-11`
  closed 2026-11-20. Where: the same log, both days.

### Environments and projects

- `SUP-163` **The `Workflows` blueprint has three states and the bill starts at the third.** Enabling it
  provides the CloudFormation template; the fee-bearing MWAA environment is born when a project first uses
  the blueprint. Neither *"enabled"* nor *"a project exists"* means billing.

- `SUP-164` **A SMUS project's deploy errors for a key-policy or service-role trust defect name neither
  cause, and leave no DataZone event in either account's trail** (measured 2026-08-22, Stage 6 pass 3,
  attempt 3′). One attempt reported *"Failed to remove EMR EKS IAM roles (System Namespace, Query Engine)"*
  and *"Could not resolve KMS key arn:aws:kms:us-west-2:<member-account>:key/… to its canonical ARN"*. The
  causes were two: both service-role trusts were pinned to the member account where the documented guard is
  `aws:SourceAccount` equal to the domain account, and the project key handed to `Tooling` carried the
  delegate-to-IAM default policy, which reaches neither the `datazone` service principal nor the domain
  execution role in the domain account. CloudTrail in the domain account and in the member account held no
  `datazone` event, so the attribution came from AWS's key-permissions page; after both fixes the failure
  moved into the member account's CloudFormation and the stuck projects deleted. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-22; `terraform-modules/sagemaker-prereqs/kms.tf`.

- `SUP-165` **`delete-project` removes a SMUS project's environment stacks and leaves its projects-bucket
  prefix, its log group, its Glue databases, account-level objects and domain-side records** (read
  2026-08-26 and 2026-10-17 in Sandbox, Stage 6 2.4; measured 2026-10-22 in Staging, Stage 18 8.1).
  Sandbox's projects bucket held five prefixes against one live project, one orphan with a complete `.git`
  tree, and six against two on 2026-10-17. In Staging `delete-project --skip-deletion-check` at 01:09:39Z
  deleted both `DataZone-Env-*` stacks by 01:12:25Z, with the project role, the security group, two Glue
  connections, two Athena workgroups, the schedule group and the Access Grants location. It left the log
  group `datazone-<project>-dev` (731 days), both Glue databases, dropped only after `InfrastructureAccess`
  joined the Lake Formation administrators and granted itself `DROP`; the Access Grants instance `default`;
  `AWSServiceRoleForAmazonAthena`; the workflows' and processing jobs' log groups, with no retention; and
  the domain's `IAM` user profiles of the deleted project role and the deploy role, the deploy role's group
  profile and 44 lineage events, which no delete API reached. Where: `log-stage-06a-unified-studio.md`,
  2026-08-26; `log-stage-18-staging-deployment-project.md`, 2026-10-22.
  **Read again 2026-11-18** (Stage 6d 2.7 step 5), on a project holding the `SageMakerAIDomain`
  blueprint's environment beside a `Tooling` with spaces off. The portal's `DeleteProject`
  (`skipDeletionCheck` `true`) at 22:57:05 UTC was followed by the provisioning role's `DeleteStack` on
  the blueprint's stack at 22:58:34, its `DeleteUserProfile` (the profile the space's creation made) and
  `DeleteDomain` at 22:58:37, the project role's `DeleteAccessGrantsLocation` at 22:59:30, and
  `DeleteStack` on the `Tooling`'s at 22:59:45. Left: the prefix's five objects written at the project's
  creation (87,233 bytes), the log group (`SUP-174`), the domain's streams in `/aws/sagemaker/studio`
  (`EXC-10`) and the `IAM` user profile of the deleted project role. No EFS file system, NFS security
  group or Lake Formation permission was left. Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-11-18.

- `SUP-166` **SMUS registers each project's `dev/` prefix with Lake Formation under the project role and
  grants on it to a project condition, not to a role** (read 2026-09-12 in Sandbox's trail since 2026-08-20,
  Stage 6f). At project creation the provisioning role, session `AmazonDataZoneEnvironmentDeployer-*` via
  `datazone.amazonaws.com`, calls `RegisterResource` on `…/<project-id>/dev/` with the project role as
  registration role, `HybridAccessEnabled` false and `WithFederation` false; `shared/` is not registered. It
  then runs `BatchGrantPermissions` to `<account-id>:IAMPrincipals` and `arn:aws:identitystore:::user/*`,
  each under `context has datazone && context.datazone has projectId &&
  context.datazone.projectId=="<project-id>"`, granting `DATA_LOCATION_ACCESS` on `dev/` and `DESCRIBE` on
  `default`. Deleting the project calls `DeregisterResource` and `BatchRevokePermissions` and leaves the
  prefix; the `Tooling` template's `LakeFormationResourceToRegisterProjectsS3Location` carries no
  `DeletionPolicy` (read 2026-10-26). Sandbox's trail held five registrations and four deregistrations. Lake
  Formation's ABAC page does not describe `context.datazone`. Where: `log-stage-06f-data-governance.md`,
  2026-09-12/13; `docs/SMUS.md` §S3 item 1b.

- `SUP-167` **A `Tooling` environment creates a daily DataZone data source nobody configured, every run
  fails, and the source's `status` reads `RUNNING` throughout** (measured 2026-09-19 and 2026-10-18 in the
  domain, Stage 6f). `Tooling-default-sagemaker-modelpackagegroup-datasource` tracks
  `SageMakerModelPackageGroupAssetType` over an empty list on a cron the environment picks (`cron(32 17 * *
  ? *)` for one project, `cron(6 6 * * ? *)` for another). Each run ends `VALIDATION_EXCEPTION`, *"Failed to
  run the data source. Please check if RAM share is correctly configured between Amazon SageMaker and Amazon
  DataZone"*: 25 `FAILED` on 2026-09-19, the oldest the day after creation, and 57 across two projects on
  2026-10-18, `lastRunAssetCount` 0. A run's `stoppedAt` equals its successor's `startedAt`, so a daily
  source always shows one `RUNNING` run, and only `list-data-source-runs` shows the failures. A Staging
  project whose `Tooling` had `enableSpaces` false held none (2026-10-19, cause not isolated). Where:
  `log-stage-06f-data-governance.md`, 2026-09-19 and 2026-10-18;
  `log-stage-18-staging-deployment-project.md`, 2026-10-19. AWS's page on a SageMaker data source (read
  2026-11-17) documents the share the error asks for: the domain shared through RAM to the service
  principal `sagemaker.amazonaws.com` with the managed permission
  `AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain`, a share never created here. The page
  describes a source someone creates in the domain's own account; it says nothing of the source a `Tooling`
  environment creates by itself, and an associated account's case is unread. The cause is documented; the
  source, its failures and its `status` are not (`EXC-11`; `log-stage-06d-unified-studio-remainder.md`,
  2026-11-17).

- `SUP-168` **A project update in the portal reconciles the environment's stack, and the stack writes only
  what its template changed** (measured 2026-10-18, 6d step 2.4). An `UpdateProject` with
  `projectProfileVersion: latest` and the parameters unchanged, made by a person in the portal, was followed
  28 s later by an `UpdateStack` by the provisioning role. The new template added
  `elasticmapreduce.amazonaws.com` to the project role's trust policy, the one IAM write besides a `TagRole`
  of a value the role already carried; the SageMaker domain resource read `UPDATE_COMPLETE` with no
  `UPDATE_IN_PROGRESS` and no `UpdateDomain`, so an attachment made by hand outside the template survives a
  reconciliation that leaves the domain's properties alone. Where: 6d step 2.4, INT-15, INT-17.
  **Read again 2026-11-22** (Stage 6d, the idle range, read by the session that applied it): a reconciliation
  that changes the domain's properties leaves the hand-set ones as well. `app-etl-dev`'s *Update project*
  (`UpdateProject` 19:19:49Z) re-deployed its `Tooling` environment, whose stack sent `UpdateDomain` on the
  project's `Tooling` domain at 19:20:23Z through the provisioning role. The request carried the template's
  declared `DefaultUserSettings`, JupyterLab's and Code Editor's `AppLifecycleManagement` among them with
  `MaxIdleTimeoutInMinutes` 525600, and neither `CustomImages` nor `StudioWebPortalSettings`, which the
  template does not declare. Against its 19:01Z snapshot the domain changed in the three
  `MaxIdleTimeoutInMinutes` leaves alone: the `CustomImages` entries attached by hand, which name no
  `ImageVersionNumber`, and `ExecutionRoleSessionNameMode` `USER_IDENTITY` stood, the omitted keys read as
  unchanged (`SUP-212`). Where: `log-stage-06d-unified-studio-remainder.md`, 2026-11-22.

- `SUP-169` **The `AmazonBedrockKnowledgeBase` blueprint's template creates its OpenSearch Serverless
  collection, Lambdas and roles only for an OpenSearch Serverless store, behind a network policy with
  `AllowFromPublic` true and no encryption policy** (read 2026-10-19 in Sandbox, Stage 17 7.0a, from
  `DataZone-AmazonBedrockKnowledgeBase-prod-20260316` and from the console's code). Of the template's 22
  resources, the collection with its `network` and `data` policies and the two Lambdas with their log groups
  exist only under `IsAOSSVectorStoreKB`; with S3 Vectors or Neptune Analytics the stack holds its wait
  handles alone, while AWS's blueprint page lists the Lambdas with no condition. Its two roles exist only
  when DataZone passes none, under AWS's `SageMakerStudioProjectUserRolePermissionsBoundary`, never the
  configuration's boundary. The template declares 62 parameters and the blueprint (`48ls9aowlj9zv4`) 61 user
  parameters: fourteen template parameters are not user parameters and thirteen user parameters are not in
  the template. The console's *Set up generative AI* Submit writes an OpenSearch Serverless encryption
  policy over `collection/bedrock-ide-*` that the template does not. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-10-19 and 2026-10-21.

- `SUP-170` **The first SMUS project in an account creates account-level objects outside its environment's
  stack: Lake Formation administrators and settings, an S3 Access Grants instance and
  `AWSServiceRoleForAmazonAthena`** (read 2026-10-19 and 2026-10-20 in Staging's trail, Stage 18 3.3). The
  provisioning role's three `PutDataLakeSettings` at 06:05:34Z, a full replace, seated itself and the
  manage-access role as the account's only Lake Formation administrators, `CROSS_ACCOUNT_VERSION` 1, and set
  `AllowFullTableExternalDataAccess` true. It created `AWSServiceRoleForAmazonAthena`
  (`ops.athena.amazonaws.com`, `invokedBy` `datazone.amazonaws.com`) at 06:06:23Z, never used afterwards.
  The project role's `CreateAccessGrantsLocation` was refused at 06:06:48Z for want of an instance, the
  provisioning role's `CreateAccessGrantsInstance` made `default` at 06:06:50Z, and the retry at 06:06:51Z
  created the location for the project's prefix, which the `project.s3_default_folder` connection names. The
  CLI's first `CreateWorkflow` (20:09:32Z) created `AWSServiceRoleForAmazonMWAAServerless`. No configuration
  names any of them, and `delete-project` leaves every one. Where:
  `log-stage-18-staging-deployment-project.md`, 2026-10-19 (3.2 and 3.3) and 2026-10-20; `docs/SMUS.md`, the
  deployment project. The Access Grants instance is `SUP-090` and the Lake Formation seats `SUP-106`.
  With an administrator already seated the three writes add to the list (measured 2026-11-11 in Staging
  and in Production, Stage 19 step 4.6): each account held `InfrastructureAccess` alone,
  `CROSS_ACCOUNT_VERSION` 4 and `SET_CONTEXT` `TRUE`, and after the provisioning role's three
  `PutDataLakeSettings` it held the two SMUS roles beside it, the same parameters, both create-default
  lists still empty and the flag `true`; `<env>/data/` planned `No changes` after it. The same
  provisioning leaves a `default` Glue database carrying its own `ALL` and a `DESCRIBE` for
  `IAMPrincipals` conditioned on the project: Production had none and holds one since, and Staging's,
  which existed, gained the two grants. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-11.

- `SUP-171` **An `MLflowApp` environment's stack holds only a `WaitConditionHandle`: DataZone's deployer
  creates the MLflow App beside the stack, and the environment reads `ACTIVE` minutes before the app is
  ready** (measured 2026-10-19 in Sandbox, Stage 17 1.5). `create-environment` on the blueprint produced
  `DataZone-Env-<id>` with one resource, `WaitHandle`. Sandbox's trail shows `CreateMlflowApp` by the
  provisioning role in session `AmazonDataZoneEnvironmentDeployer-<account>`, `invokedBy`
  `datazone.amazonaws.com`, with the project role as `roleArn`, the store under the project's
  `dev/data/ml/mlflow` and the three DataZone tags; no `KmsKeyId` travels and `describe-mlflow-app` returns
  none. The environment read `ACTIVE` at 06:40:03 UTC; the app read `Created` with `LastModifiedTime`
  06:44:15, about four minutes twenty seconds after `CreateMlflowApp` (a 30-second poll). The portal's
  *Open* calls `CreatePresignedMlflowAppUrl` as the project role from the laptop's browser, on the public
  SageMaker API with no `vpcEndpointId`. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-10-19.

- `SUP-172` **A `DataLake` environment that fails keeps the Glue database its add-on created, and deleting
  the environment keeps it too** (read 2026-10-20 in both trails, 6f decision due 6). The template,
  `DataLakeDefault-prod-20250618`, declares the `AWS::Glue::Database` with `DeletionPolicy: Retain`: at the
  failure DataZone deletes the stack and no `DeleteDatabase` follows, and a later `DeleteEnvironment`
  deletes the stack again and calls none either (Staging's `glue_db_c2ej62w956q2a8`, Sandbox's
  `mydatabase`). An `ACTIVE` environment's deletion follows the same template and left its database too
  (Staging's `glue_db_d6ogysnx78dguo`, 2026-10-22, Stage 18 8.1). The portal's *Create database* deleted its
  database after one such failure (`test`, 2026-10-15, as the project role) and not after the other. Lake
  Formation leaves the database out of a non-administrator's `get-databases`, so the listing reads it as
  gone; `get-database` by name answers *"Insufficient Lake Formation permission(s): Required Describe"*
  while it exists and `EntityNotFoundException` once it does not. Where: `log-stage-06f-data-governance.md`,
  the entry of 2026-10-20. The same template declares an Athena workgroup beside the database, both with
  `DeletionPolicy` and `UpdateReplacePolicy` `Retain` (read 2026-10-20 in Sandbox). A failed record does not
  block a new environment from the same configuration: on 2026-10-26 `create-environment` beside the
  `CREATE_FAILED` `4lrapnc3syxd74` went `ACTIVE` in 36 s (37 s on 2026-10-20, after the failed record's
  deletion). In both, the manage-access role's `RevokePermissions` of `ALL` from `IAM_ALLOWED_PRINCIPALS`
  answered *"InvalidInputException"* under empty create defaults, nothing to revoke, and the environment
  still deployed. Where: `log-stage-06f-data-governance.md`, 2026-10-20 and 2026-10-26.

- `SUP-173` **A `DataLake` environment needs `AmazonDataZoneGlueManageAccessRolePolicy` on the manage-access
  role** (measured 2026-10-20, Stage 18 7.2). The add-on has the manage-access role call
  `lakeformation:CreateLakeFormationOptIn` on the new database, which
  `AmazonDataZoneSageMakerManageAccessRolePolicy` v4 does not carry and the Glue policy v18 does; with the
  SageMaker policy alone the environment fails and its stack rolls back, which is why every Sandbox
  `DataLake` environment has been `CREATE_FAILED` since 2026-09-13. The Glue policy's ARN carries the
  `service-role/` path, which the SageMaker one does not. The module attaches it since
  `sagemaker-prereqs-v0.8.0` (PR #207), and Staging's `staging/studio/manage-access.tf` until that slice
  leaves v0.6.0. Where: `log-stage-18-staging-deployment-project.md`, the 7.2 entries of 2026-10-20.

- `SUP-174` **Deleting a `Tooling` environment leaves its log group** (measured 2026-10-22, Stage 18 8.1):
  the stack reached `DELETE_COMPLETE` and `datazone-<project>-dev`, at 731 days, stayed. Read again
  2026-11-21 in Sandbox (Stage 6a): five such groups of five deleted projects, four created on 2026-08-22
  and 23 and one on 2026-11-18, 0 bytes each at 3, 30 or 731 days, keep their environment's
  `AmazonDataZone*` tags and CloudFormation's three, `aws:cloudformation:stack-id` naming a stack
  `describe-stacks` no longer finds by that id; an `S3Bucket` bucket loses CloudFormation's (`SUP-394`). The
  tagging API lists them by `AmazonDataZoneEnvironment` while no live stack carries their environment, which
  is how `./aws/studio.py` `US-15` notes them. Where: `log-stage-06a-unified-studio.md`, 2026-11-21.

- `SUP-175` **DataZone takes the `SageMakerAIDomain` blueprint's `customImages*` as JSON and reports nothing
  when they are not** (measured 2026-10-30). The template declares the parameter as comma-separated
  `imageName;appImageConfigName;versionNumber` triples and splits it so; the portal's *Configure* panel and
  the profile take `[{"ImageName","AppImageConfigName","ImageVersionNumber"}]`, and the service writes the
  triple into the stack (the environment's resolved parameter carries the JSON, the stack's parameter the
  triple, 22:11 UTC). A profile override in the triple form ends every environment `VALIDATION_FAILED` with
  `failureReason` `{code: "1", message: "[]"}` 11 to 13 s after `CreateEnvironment`, no call into the member
  account, the portal's banner reading *"Setting up your SageMaker AI domain"* first; the template's
  defaults alone deploy, and so does the JSON through an update of the living environment. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-10-30. A `VALIDATION_FAILED` environment is reachable
  only through the API (read 2026-10-30): the portal's *Project details* has no environment list and *Code
  spaces* reads *"You don't have any code spaces"*, yet the record holds the name `SageMakerAIDomain`, so
  each later press is a `ConflictException` and the wizard answers *"An environment named SageMakerAIDomain
  already exists within this project"* until `delete-environment` removes it. Data Governance's trail of a
  failure holds `CreateEnvironment`, `GetEnvironmentBlueprint`, `GetEnvironment` and `AssumeRole`s by
  `datazone.amazonaws.com` into the domain execution role, and no call to another service. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-10-30.

- `SUP-359` **A project's `Tooling` environment answers, as `provisionedResources`, the values a stage of
  a CI/CD manifest reads: its subnets, its security group, its key and its shared prefix** (read
  2026-11-12 in `deploy-staging` and `deploy-production`, Stage 19 step 4.9). `GetEnvironment` on the
  environment whose `isDefaultToolingEnvironment` is `true` lists them by name, each a string:
  `privateSubnets` (the two subnet ids, comma-separated), `securityGroup`, `kmsKeyArn`, `userRoleArn`,
  `vpcId`, `nonGitProjectRepositoryLocation` (`s3://<projects bucket>/<domain>/<project>/shared`, the
  `default.s3_shared` connection's prefix without its slash), `glueNetworkConnection0` and `1`
  (`datazone-glue-network-connection-<subnet id>-<project>-dev`, one per subnet in the order of
  `privateSubnets`), `athenaWorkGroupName` and `logGroupName`. The names are the blueprint's, read from
  the answer; no page of AWS's was read for them, and the CLI 1.0.9 reads the same environment for a
  workflow's network and key (its *"Resolved Tooling config"* line). A member of the project reads
  them, so a deploy leg fills a stage's variables from the project itself and no pipeline variable or
  Terraform state holds them. The project's
  security group, `datazone-<project>-dev`, admits itself inbound and every destination outbound in
  both targets. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-12;
  `scripts/tfhygiene/projects.py`.

- `SUP-379` **A `SageMakerAIDomain` blueprint domain names the projects bucket's root `shared/` as its
  `ProjectS3Path`, a prefix the project role lists and can neither read nor write** (read 2026-10-30 on two
  domains in Sandbox, and the bucket and the role's policies on 2026-11-18; Stage 6d steps 2.6 and 2.7).
  `describe-domain` read `UnifiedStudioSettings.ProjectS3Path` `s3://awsds-sandbox-smus-projects/shared/`
  on `d-tqvlxk2hftsv`, born from the template's defaults, and on `d-odhynkcev3yw`, born from
  `experimentation`'s fourteen overrides: the bucket's root, without the `<domain>/<project>/` prefix, where
  the two projects' `Tooling` domains carry `<domain>/<project>/dev`. On 2026-11-18 the bucket held the
  prefix `dzd-d8yrvx1ko7im6o/` alone, no object and no version under `shared/` (versioning `Enabled`,
  noncurrent versions kept 90 days), and its policy was `DenyInsecureTransport` alone. The project role's
  object grant reaches `<bucket>/<domain>/<project>/*` only (`SageMakerStudioProjectUserRolePolicy` v77,
  `DomainS3BucketPermissions`), its whole-bucket list comes from `AirflowListDomainS3Permissions`
  (`SUP-367`, `TM-31`), and the ML policy v48's `S3AG` statements act through the access-grants instance
  `default` alone. No AWS page read for this project gives the value: the blueprint's admin guide page,
  read again 2026-11-18, names no S3 path, prefix or `ProjectS3Path`. Nothing has been written under the
  prefix, so what the service puts there is unread. Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-10-30 (two entries) and 2026-11-18; `REFERENCES.md`, SageMaker Unified Studio's October 2026
  releases.
  Read again 2026-11-18 on three more domains, `d-m8m0uefej9kb`, `d-jaid1tvg20jv` and `d-kr8cbbohordz`
  (Stage 6d 2.7 step 2): the same root. The stack's template holds one resource, `AWS::SageMaker::Domain`,
  sets no `UnifiedStudioSettings`, and writes the tag `ProjectS3Path` as `s3://`, the bucket's name split
  from the parameter `sageMakerUnifiedStudioToolingS3BucketArn`, and `/shared/`; `describe-domain` answers
  the tag's value. The project's prefix arrives as `sageMakerUnifiedStudioProjectRepositoryLocation`
  (`s3://<bucket>/<domain>/<project>/shared`, the value of `SUP-359`'s `nonGitProjectRepositoryLocation`)
  and becomes `DefaultUserSettings.CustomFileSystemConfigs`, an S3 mount at `shared`, the URI the project's
  `Tooling` domain mounts. A space's `shared` mount is therefore inside the project role's object grant;
  only the tag names the root. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-11-18.

- `SUP-380` **An *Update project* did not carry a profile's new override of `enableSpaces` into an environment
  created before the override, and carried changed overrides of the image pin and the idle ceiling into the
  environments created with them**
  (measured 2026-11-18 in Sandbox, Stage 6d 2.7 step 4). `test-experimentation`'s `Tooling` environment
  `bi356s1sacz0cw`, created 2026-10-15 when `experimentation` overrode no `enableSpaces`, stores it in its
  `userParameters` as `defaultValue` `"true"`, `isEditable` false. At 18:45:34 the profile locked
  `enableSpaces` `"false"`, and `get-project-profile` read it in both `parameterOverrides` and
  `resolvedParameters`. The user's *Update project* sent `UpdateProject` at 19:14:47 with
  `projectProfileVersion` `latest` and, for that environment, its ten editable parameters, `enableSpaces`
  not among them. The provisioning role's `UpdateStack` followed at 19:15:16 with 57 parameters, whose
  values CloudTrail does not record. The stack read `UPDATE_COMPLETE` at 19:15:29 with no resource event
  and `enableSpaces` `true`; the deployment read `UPDATE` `SUCCESSFUL`, and the domain `d-lfgbdrjncmsu`
  stood. A profile's locked change therefore reaches the projects created after it, and a living project
  keeps its copy. Only `enableSpaces` was measured: whether a locked override in another element, the
  `SageMakerAIDomain` image pin among them, stops at the same copy is unmeasured. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-11-18.
  **Read again 2026-11-22** (Stage 6d 2.7 step 8, read by the coordinating session): the image pin moved in
  every environment. `experimentation` has overridden the pin since 2026-10-30 (#277), and Sandbox's six
  `SageMakerAIDomain` environments were created after it, from 2026-11-18 18:16:05Z to 2026-11-19 00:19:40Z, each
  storing `/11` in its `userParameters`, `isEditable` false. The profile's pin went to 12 at 05:07Z. The owner's
  *Update project* on the six projects, `UpdateProject` from 05:14:42Z to 05:21:06Z with `projectProfileVersion`
  `latest`, re-deployed each through the provisioning role: `Tooling`'s `UpdateStack`, 57 parameters, with no
  resource event, and `SageMakerAIDomain`'s, 29 parameters, passing `SageMakerDomain` through an update whose
  `UpdateDomain` (05:16:14Z to 05:28:53Z) rewrote the whole `DefaultUserSettings`. Each environment then stored
  `/12`, and each domain read JupyterLab and Code Editor at version 12, custom images and default alike: the
  parameters the profile overrode at creation were re-resolved from its latest version. The readings differ in
  the parameter as well as in the creation condition, and no living environment holds the image pin from the
  blueprint's default, so which of the two decides is unmeasured. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-11-22.
  **Read again 2026-11-22** (Stage 6d, the idle range, read by the session that applied it): one environment
  held both outcomes. `app-etl-dev`'s `Tooling` environment `6kvndq6t2757rk`, created 2026-11-14, before the
  `enableSpaces` override, stored `enableSpaces` `"true"` and `maxIdleTimeoutInMinutes` `"120"`, both
  `isEditable` false; every profile has locked the second since Stage 6a step 8.1. The profiles took `525600`
  at 19:00:22Z. After the owner's *Update project* (`UpdateProject` 19:19:49Z, the deployment `UPDATE`
  `SUCCESSFUL` at 19:20:54Z), the environment stored `"525600"` beside `enableSpaces` `"true"`, and its domain
  read 525600. The element, the environment and the update are now the same, and only the parameter differs:
  `enableSpaces` remains the one override measured arriving after an environment's creation. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-11-22.

- `SUP-381` **The `SageMakerAIDomain` blueprint's deployer calls `sagemaker:ListTags` on the domain it has
  just created, which the provisioning role's managed policy does not grant, and the environment goes
  `ACTIVE` regardless** (measured 2026-11-18 in Sandbox, Stage 6d 2.7 steps 2 and 5). On each of four
  creations `awsds-sandbox-smus-provisioning`, through DataZone, was refused `sagemaker:ListTags` on the new
  domain 12 to 13 s after its `CreateDomain`: at 18:16:36, 18:20:53, 18:24:08 and 21:45:58 UTC, *"no
  identity-based policy allows the sagemaker:ListTags action"*. The role's one policy,
  `SageMakerStudioProjectProvisioningRolePolicy` v86, carries no `sagemaker:ListTags`. The four environments
  read `ACTIVE`, their `CREATE` deployments `SUCCESSFUL`, so this refusal in the trail is no deployment's
  cause. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-11-18.

- `SUP-384` **A custom designation's Cedar policy names action groups, never individual actions, and no AWS
  page gives the groups' identifiers** (measured 2026-11-19 in Data Governance, Stage 19 decision 15 (d)).
  `datazone create-designation` on `awsds-studio`, its policy three `permit`s over individual actions in
  the managed designations' form (`Subscriptions::Action::"AcceptSubscriptionRequest"` and the other four
  approvals, nine `Catalog` reads, the 17 `DataAgent` actions `PROJECT_CONTRIBUTOR` stores), was refused at
  02:33:30 UTC with a `ValidationException`: *"Invalid designation policy: Designation policy validation
  error: the specified action is not a valid action group"*. Nothing was created. The same call with one
  group per statement, `Subscriptions::Action::"ManageSubscriptionApprovals"`,
  `Catalog::Action::"ReadOnlyActions"` and `DataAgent::Action::"AllActions"`, created `subscription-approver`
  at 02:46:46, `USER_CREATED` with deletion protection on, and `get-designation` returns the policy byte for
  byte, its groups unexpanded. `CreateDesignation`'s reference describes `policy` as a Cedar permit policy
  and shows no syntax. The designation permissions page names each category's choices by label (*Manage
  subscription approvals*, *Read-only actions*) with their API lists, never by identifier, and prints the
  managed designations with individual actions (`SUP-385`). `ReadOnlyActions`, `UseConnection` and
  `AllActions` come from a designation made in the portal (Classmethod, 2026-11-02);
  `ManageSubscriptionApprovals` was inferred from its label and accepted. The validation accepted a policy
  without the Connections groups, which the portal pre-selects and does not let a user clear (the same
  article). Whether it refuses a policy without the Data Agent group, which the guide requires, was not
  tried. What a group grants is read from the permissions page, not from the API. The CLI 2.37.12 has no
  designation operations; botocore 1.44.5's model in `AWS_DATA_PATH` ran them. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-19; Stage 19 decision 15.

- `SUP-385` **The managed designations' stored policies differ from the text the admin guide prints for
  them** (read 2026-11-19 in Data Governance and on the designation permissions page, Stage 19 decision 15
  (d)). `get-designation` returned `PROJECT_OWNER` and `PROJECT_CONTRIBUTOR` as 23 and 18 `permit`
  statements over 158 and 150 unique actions; the page prints 21 and 17 statements over 150 and 143. Both
  stored policies hold seven Data Agent actions the page lacks, `PutAgentApprovalPolicy`,
  `GetAgentApprovalPolicy`, `DeleteAgentApprovalPolicy`, `RegisterAgentArtifact`, `DeregisterAgentArtifact`,
  `ListAgentArtifacts` and `ListAgentSessionRecords`, and lack the page's four agent-context actions,
  `AssociateAgentContext`, `DisassociateAgentContext`, `UpdateAgentContext` and `ListAgentContexts`, which
  the page's table also lists under the Data Agent's *All actions*. Both add the `Project` actions
  `ListDeployableEnvironmentBlueprints`, `StartCompute`, `GetCompute` and `StopCompute`, the last three in the
  page's table under *Manage user compute* but in neither printed policy, and the owner's adds `Catalog`'s
  `UpdateAssetOwner`. Which actions `DataAgent::Action::"AllActions"` grants in a custom designation
  (`SUP-384`) is therefore unread: the page lists 14, the managed designations hold 17. A managed
  designation's reach is read from `get-designation`, never from the page. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-19.

- `SUP-392` **DataZone passes a project's `Tooling` outputs to an `S3Bucket` environment, so its bucket
  encrypts under the project CMK though neither the blueprint configuration nor the profile names a key**
  (measured 2026-11-21 in Sandbox, Stage 6a). `create-environment` in `test-experimentation`, with the
  `experimentation` profile's `S3Bucket` configuration and one user parameter, `bucketName`, made a stack with
  six parameters: `bucketName`, `datazoneEnvironmentEnvironmentId`, `datazoneEnvironmentProjectId`,
  `datazoneScopeName` `dev`, `executionRoleArn` and `kmsKeyArn`. The last two equal the values the project's
  `Tooling` environment answers as `userRoleArn` and `kmsKeyArn` (`SUP-359`): the project's user role and the
  key `alias/awsds-sandbox-project` names. The `S3Bucket` configuration's regional parameters are `VpcId`,
  `Subnets` and `AZs`, and the profile overrides `bucketName` alone. The template
  (`DataZone-Amazon-SageMaker-S3Bucket-prod-20250923`) describes the key as *"optional. If not provided,
  uses S3 managed encryption"*, and no page read for `docs/SMUS.md` §Resource blueprints names where the value
  comes from. The bucket read SSE-KMS under that key, `BucketKeyEnabled` false and `SSE-C` blocked, and
  carried the stack's tags `AmazonDataZoneDomain`, `AmazonDataZoneProject`, `AmazonDataZoneEnvironment` and
  `AmazonDataZoneBlueprint`. Which key such a bucket uses is AWS's composition, not a parameter this
  repository writes. Where: `log-stage-06a-unified-studio.md`, 2026-11-21.

- `SUP-394` **Deleting an `S3Bucket` environment deletes the bucket's policy and keeps the bucket, which no
  project role then reaches** (measured 2026-11-21 in `test-experimentation`, Sandbox, Stage 6a).
  `delete-environment` ran at 04:58:36 UTC. The stack read `DELETE_COMPLETE` at 04:58:55, `ProjectBucketPolicy`
  `DELETE_COMPLETE` and `ProjectBucket` `DELETE_SKIPPED` under the template's `DeletionPolicy: Retain`, and the
  environment answered *"Environment not found"* by 04:59:15. The bucket kept its default encryption under the
  project CMK and the four `AmazonDataZone*` tags, lost CloudFormation's three, and `get-bucket-policy`
  answered `NoSuchBucketPolicy`. The simulator gave `s3:GetObject`, `s3:PutObject` and `s3:ListBucket`
  `implicitDeny` to the owning project's user role and to another project's. The provisioning role cannot
  delete the bucket: `SageMakerStudioProjectProvisioningRolePolicy` v86 grants `DeleteBucketPolicy` on
  `sagemaker-*` in Sid `S3Create` and no `DeleteBucket`. A bucket therefore outlives its environment with
  whatever the project wrote in it, reachable only by an identity whose own IAM policy covers it; the probe's
  empty bucket was deleted by hand at 05:00:15 UTC. Where: `log-stage-06a-unified-studio.md`, 2026-11-21.

### The managed policies of a project role

- `SUP-176` **`SageMakerStudioProjectRoleMachineLearningPolicy` grants every SMUS project role `datazone:`
  actions on `*` with no domain scope and, since v47, Bedrock AgentCore's managed browser and code
  interpreter, joined in v48 by its web search and the Agent Registry** (read in Sandbox's policy documents
  on 2026-08-26, 2026-10-30, 2026-11-08 and 2026-11-22; not exercised). Read 2026-08-26: `datazone:*Compute*`, `CreateAsset*`, `List*` and `Search*` on `Resource:
  "*"`, where the user-role policy beside it is scoped to the role's domain, and S3 reach keyed on principal
  tags,
  `${aws:PrincipalTag/DomainBucketName}/${aws:PrincipalTag/AmazonDataZoneDomain}/${aws:PrincipalTag/AmazonDataZoneProject}/*`.
  v47 (2026-10-29 22:27 UTC) adds `ACManagedBuiltInTools`, `bedrock-agentcore:*CodeInterpreterSession`,
  `InvokeCodeInterpreter`, `*BrowserSession` and `ConnectBrowserAutomationStream` on AWS's built-in
  `code-interpreter/*` and `browser/*`, tools that run on AWS's side, and `ACProjectResources` on
  project-tagged AgentCore resources; no release note announced them. v47 also grants `datazone:Get*`,
  `List*`, `Search*`, `CreateAsset*`, `CreateListingChangeSet`, `CreateSubscriptionRequest` and
  `RevokeSubscription` on `*`, and no managed policy on the role grants `StartDataSourceRun` (2026-11-08).
  Where: `log-stage-06a-unified-studio.md`, 2026-08-26; `upstream-releases.md`, the project role's managed
  policies; `threat-model.md` `TM-28`; `log-stage-19-smus-native-data-product.md`, 2026-11-08.
  v48 (2026-11-13 20:47:08 UTC, the default version) was read 2026-11-22 in Sandbox by the infrastructure
  user (`InfrastructureAccess`) against v47: 96 statements where v47 held 90, 339 distinct actions where it
  held 312, nothing removed. Six statements are new. `ACApiKeySecret` allows `secretsmanager:CreateSecret`,
  `PutSecretValue`, `DeleteSecret` and `GetSecretValue` on `secret:bedrock-agentcore-identity!*` when
  `aws:CalledVia` names `bedrock-agentcore.amazonaws.com`. `ARConsumerPublisher` allows the Agent Registry's
  `agent-registry:List*`, `GetRegistry`, `GetRegistryRecord`, `GetDiscoverableRegistryRecord` and
  `SearchDiscoverableRegistryRecords` on `*` with no condition; `ARCreate` allows `CreateRegistryRecord`
  under the request's `AmazonDataZoneProject` tag; `ARPublisher` allows `UpdateRegistryRecord`,
  `UpdateRegistryRecordStatus`, `DeleteRegistryRecord`, `SubmitRegistryRecordForApproval` and
  `TagResource` on records carrying the role's project tag. `IdCKmsDecrypt` and `IdCKmsDescribe` allow
  `kms:Decrypt` and `DescribeKey` through `sso` and `identitystore`. Seven statements gain actions:
  `ACManagedBuiltInTools` `bedrock-agentcore:InvokeWebSearch` on AWS's `tool/web-search.v1`, with no
  condition; `ACProjectResources` `*ApiKeyCredentialProvider` and `GetResourceApiKey` on project-tagged
  resources; `ACIdentityDirectory` the same two, `*TokenVault` and `ListTagsForResource` on the account's
  `token-vault/default`; `ACUnscopedMetadata` `ListApiKeyCredentialProviders`; `DataZoneUserPermissions`
  `datazone:UpdateAssetOwner` on `*`; `SSOReadOnlyPermissions` `identitystore:GetUserId`, `GetGroupId`,
  `sso-directory:DescribeUser`, `DescribeGroup` and `sso:ListInstances` under `aws:ViaAWSService`;
  `CreateSLR` the Agent Registry's service-linked role. No statement grants `agent-registry:CreateRegistry`
  or `InvokeRegistryMcp`. Simulated the same day as `eighth-experimentation`'s project role, with the
  Region, the project tag and the account in the context (`SUP-008`): `InvokeWebSearch`, a browser and a
  code interpreter session, the registry's search, create, submit and status calls,
  `CreateApiKeyCredentialProvider`, `GetResourceApiKey` and `UpdateAssetOwner` each `allowed` by this
  policy, `AllowedByOrganizations` and `AllowedByPermissionsBoundary` true; the secret's create `allowed`
  through AgentCore and `implicitDeny` without `aws:CalledVia`. The negative controls: `athena:StartSession`
  `explicitDeny` by the organization, `s3:GetObject` on `awsds-data-curated` `explicitDeny` by the boundary.
  As Staging's and Production's deployment project roles the same day, `InvokeWebSearch`, a browser session
  and `CreateApiKeyCredentialProvider` read `explicitDeny` by the boundary's
  `DenyServicesNoProjectUsesHere`, and the registry's search, create, submit and status calls and
  `UpdateAssetOwner` read `allowed`: `agent-registry` is a service prefix of its own, which the fence does
  not name. Where: `upstream-releases.md`, the project role's managed policies; `threat-model.md` `TM-28`.

- `SUP-177` **`SageMakerStudioProjectUserRolePolicy` lets every SMUS project role send to other accounts'
  queues, invoke other accounts' functions, regrant Lake Formation permissions with no condition and, since
  v76, invoke any Bedrock model in any Region** (read in Sandbox's policy documents: v74 2026-08-26, v75
  2026-10-18 and 2026-10-27, v76 2026-10-30; nothing exercised). v74's `DataZoneUserPermissions` grants
  `datazone:GetDomainExecutionRoleCredentials` on the domain named by the role's `AmazonDataZoneDomain` tag,
  so a blanket deny breaks every project. v75's `AirflowSqsActions` allows `sqs:SendMessage` on
  `arn:aws:sqs:*:*:airflow-celery-*` only where `aws:ResourceAccount` is not the caller's, simulated
  `allowed` for an outside account; `InvokeFunctionForAmazonBedrockIDE` and `LambdaInvokeFunctionViaBedrock`
  allow `lambda:InvokeFunction` on any account's `amazon-bedrock*` function under `aws:CalledViaFirst`
  `bedrock.amazonaws.com` and the project tag; `LFResourceSharingPermissions` allows
  `lakeformation:BatchGrantPermissions` on `*` with no condition, so a publishing project's role regrants
  what it holds with the grant option in any session. v76 (2026-10-29 22:37 UTC) adds `ACInvoke`:
  `bedrock:InvokeModel` and `InvokeModelWithResponseStream` on every foundation model and inference profile
  in every Region for a role tagged `EnableAmazonBedrockPermissions` `true`. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-26; `log-stage-11-dlp.md`, 2026-10-18; `threat-model.md`
  `TM-17`, `TM-27`; `upstream-releases.md`.

- `SUP-178` **`SageMakerStudioDomainExecutionRolePolicy` v23 lets the domain execution role run the whole
  subscription approval cycle, change the domain's policy grants and pass requests to Amazon Q** (read
  2026-09-18 on `awsds-data-studio-domain-execution` in Data Governance, Stage 6f 1.2; still v23 on
  2026-10-30). The role holds this one AWS-managed policy, no inline policy and no permissions boundary, and
  trusts `datazone.amazonaws.com`. `DataZonePermissions` grants `AcceptSubscriptionRequest`,
  `RejectSubscriptionRequest`, `CreateSubscriptionGrant`, `DeleteSubscriptionGrant`, `RevokeSubscription`,
  `AddPolicyGrant`, `RemovePolicyGrant` and `datazone:GetEnvironmentCredentials`;
  `AmazonQPermissionsStatement` grants `q:PassRequest`; `AllowSetTrustedIdentity` grants `sts:SetContext`. A
  person's portal acts run as this role with the person's session name (`CreateProjectMembership`,
  2026-10-15, read 2026-10-18 in Data Governance's trail). The project role's managed policy does not grant
  `q:PassRequest`, this one does, so a deny written on the first fact is not redundant. Where:
  `log-stage-06f-data-governance.md`, 2026-09-18 and 2026-10-18.

- `SUP-179` **`SageMakerStudioProjectUserRolePolicy` v75 grants every SMUS project role Redshift
  credentials, the Data API and secret writes through resource tags, and `GetCredentials` on any workgroup
  through `sqlworkbench`** (read and simulated 2026-10-18 on both Sandbox project roles, Stage 6h 5.3).
  `ComputeCredentials` and `RedshiftDataActions` grant `redshift-serverless:GetCredentials`,
  `redshift-data:ExecuteStatement`, `BatchExecuteStatement` and the listing calls on `*` where the
  resource's `AmazonDataZoneProject` equals the caller's. `RssCreds` grants `GetCredentials` on any
  workgroup in any account when `aws:CalledVia` names `redshift-data.amazonaws.com` or
  `sqlworkbench.amazonaws.com`. `ExistingRedshiftCompute` grants credentials and the Data API on anything
  tagged `for-use-with-all-datazone-projects=true` and carrying no `AmazonDataZoneEnvironment` tag.
  `AllowGetSecretForRedShift` grants `secretsmanager:GetSecretValue` and `PutSecretValue` on a same-account
  secret tagged with the caller's project, `DataConnectionAllProjectResources` the same on any secret with
  the wide tag. `SQLWorkBench` grants thirteen query-editor actions on `*` with no condition. A tag on a
  workgroup or a secret is therefore the grant, and leaving `redshift-data:` out of one's own policies
  removes nothing. Where: `log-stage-06h-redshift-connection.md`, 2026-10-18; `AWS_STATE.md` `INV-20`.

- `SUP-358` **AWS's policies allow a project role `sts:AssumeRole` on every role, `kms` through S3 on every
  key and `glue` database writes on the whole catalog: what confines the role to its project is, for these,
  each resource's own policy** (read 2026-11-11 in `SageMakerStudioProjectUserRolePolicy` v76 and
  `SageMakerStudioProjectRoleMachineLearningPolicy` v47, and simulated the same day as Production's project
  role, Stage 19 step 4.6). With `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9 the role carries
  265 statements; of the 179 that allow a write, 98 name the project through `${aws:PrincipalTag/...}` and
  81 do not. Among the 81: `AllowAssumeAccessRole`, `sts:AssumeRole` on `*` on the one condition that the
  role's project tag is not empty, so a role is closed to a project by its trust policy alone;
  `S3AGKMSPermissions`, `kms:Decrypt` and `GenerateDataKey` on `*` when called through S3 with an
  `aws:s3:arn` encryption context, in any account, so a key whose policy delegates to its account's IAM
  gives the role nothing only while S3 refuses the object; `GlueCatalogDb`, `glue:CreateDatabase` and
  `DeleteDatabase` on every database with no condition, and `GlueDatalakePermissions`, the table writes on
  `*` where `glue:LakeFormationPermissions` is `Enabled`, so Lake Formation alone decides, and a catalog on
  which `IAM_ALLOWED_PRINCIPALS` holds `CREATE_DATABASE`, AWS's default, takes a database from the role;
  `LFResourceSharingPermissions`, `lakeformation:BatchGrantPermissions` and the data cells filter writes
  on `*`; `SageMakerECRPermissions`, the pull actions on every repository; `RssCreds`,
  `redshift-serverless:GetCredentials` on every workgroup when called through `sqlworkbench` or the Data
  API. The S3 Access Grants statements allow object reads and writes on `*` in the role's account for a
  request carrying the `default` instance's credentials, while a location and a grant can be created for
  the project's own prefix alone, so that reach is the instance's locations. Simulated with the Region and
  the role's tags in the context (`SUP-008`): the assumption of the deploy role, the runner's role and the
  job role `allowed`, `kms:Decrypt` through S3 on the keys of GitLab and of the Terraform state `allowed`,
  `glue:DeleteDatabase` on `curated` `allowed`; a secret, a host, a bucket read directly, a chain, a
  schedule and an IAM write `implicitDeny`. In Production no role trusts the account's root, no bucket
  policy allows the account broadly and no Lake Formation grant names every IAM principal on the lake's
  databases, which is what the three allows meet. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-11; `threat-model.md` `TM-30`; `./aws/studio.py` `US-12`, `./aws/deploytargets.py` `DT-14`.

- `SUP-367` **`SageMakerStudioProjectUserRolePolicy` lets every project role list the whole domain bucket,
  every other project's keys included** (measured 2026-11-14 in Sandbox, Stage 19 verification xi; the
  policy read the same day at v77). From a space in `test-experimentation`, its project role's `s3api
  list-objects-v2` on `awsds-sandbox-smus-projects` with the prefix of `eighth-experimentation`'s table,
  `dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/catalogs/trades_notional/`, answered a key,
  `…/data/00000-9-41aaf172-…-00001.parquet`, before and after the subscription's revocation, while
  `head-object` on the table's metadata file answered `403 Forbidden`. The statement
  `ListDomainS3BucketPermissions` grants `s3:ListBucket` and `s3:ListBucketVersions` on
  `${aws:PrincipalTag/DomainBucketName}` under `s3:prefix` values naming
  `${aws:PrincipalTag/AmazonDataZoneDomain}/${aws:PrincipalTag/AmazonDataZoneProject}`; the statement
  `AirflowListDomainS3Permissions` grants `s3:ListBucket` on the same bucket under the resource account's
  condition alone, with no `s3:prefix` condition. The bucket's policy holds `DenyInsecureTransport` alone.
  The reach follows from the policy's text, and no page this project has read states it. A key carries a
  partitioned table's partition values, so the listing is a metadata channel between the projects that
  share a domain bucket (`threat-model.md` `TM-31`). Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-14.

### The portal

- `SUP-180` **An `aws:SourceIp` deny on a permission set does not reach the SageMaker Unified Studio portal,
  whose DataZone calls run as the domain execution role and carry the browser's address** (measured
  2026-08-22, Stage 6 step 1.7). With the tunnel down, a Data Scientist whose permission sets carry
  `DenyControlPlaneOffVpn` (`Deny *` on `*` off the VPN) signed in, listed the project profiles, created a
  project, started its space and worked in JupyterLab, as with the tunnel up, while the console's
  `logs:DescribeLogGroups` was refused *"with an explicit deny in an identity-based policy"*. `VpcOnly`
  governs the app's interfaces and egress, not the user's path through the Studio front end. Data
  Governance's trail held 770 `datazone.amazonaws.com` events under the domain execution role with three
  `sourceIPAddress` values, the VPN's Elastic IP (390) and two carrier addresses (246, 134), split by hour
  as the sittings were, every session `user-<uuid>`. A network condition therefore belongs on that role;
  that `aws:SourceIp` matches `sourceIPAddress` there is identified, not measured by an applied policy.
  Where: `log-stage-06a-unified-studio.md`, both 2026-08-22 entries; `docs/plan/integrations.md` `INT-16`.
  The console and CLI half is `SUP-004`.

- `SUP-181` **No VPC endpoint service serves the SageMaker Unified Studio portal's browser surfaces, and the
  `datazone` endpoint's private zone shadows one of them** (read 2026-08-24 in the Region's endpoint-service
  catalog and on AWS's network-isolation page, Stage 6 `NT-9` and `NT-10`). Among `us-west-2`'s about 569
  endpoint services, none serves the `on.aws` portal, its CloudFront assets,
  `agent.datazone.<region>.api.aws` or `sagemaker-unified-studio.<region>.api.aws`: the `datazone` family
  holds `datazone` and `datazone-fips`, the `sagemaker-unified-studio` family `sagemaker-unified-studio-mcp`
  alone. AWS's SMUS network-isolation page instructs the `datazone` endpoint in a required table scoped to
  its own isolation, *"access to the public internet is denied from the Amazon VPC"*, and lists
  `agent.datazone.<region>.api.aws` under public internet access in a third table. With the endpoint's
  private DNS on, its zone answered NXDOMAIN for that name to every client of the VPC resolver, the
  full-tunnel laptop included, and the portal broke on the VPN (measured 2026-08-23/24). The portal needs
  public egress from the client's network. Where: `aws/networking.py` `NT-9` and `NT-10`;
  `docs/plan/lessons.md`, Lessons 40 and 41. The private zone's reach over a subtree is `SUP-078`.

- `SUP-182` **The Query Editor's querybook compute was refused with status 402 while the `datazone`
  querybook quotas applied at 0 against non-zero defaults, and AWS later raised them with no request** (measured 2026-09-13 in Sandbox, Stage 6d
  thirteenth sitting, and 2026-10-21 in Staging, Stage 18 6.1). Six `datazone:StartNotebookCompute` calls
  answered `ServiceQuotaExceededException`, shown as *"Status code: 402 - The account-level service limit
  'SageMaker Unified Studio Querybooks running on sc.t3.medium instances' is 0 Querybooks"*. In the
  `datazone` service code `L-F63F402C` read 0 against a default of 5, `L-B3401D17` (*Querybook Runs*) 0
  against 5 and `L-85C9EC5A` (*concurrent notebook runs per account*) 0 against 15; 79 of the 81 `sc.*`
  quotas with a default above zero read 0. Requests at the defaults closed on 2026-09-24 with no increase;
  the first two read 0 in Sandbox and Staging on 2026-10-21. The editor's SQL path, `sqlworkbench` to Athena
  with no compute, returned 10 rows. In Staging the 402 came with *"Kernel Error"*, and the typed `SELECT 1`
  was saved as the querybook's description (`UpdateNotebook`). Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-12/13 and 2026-10-17;
  `log-stage-18-staging-deployment-project.md`, 2026-10-21. Read again 2026-11-19 in Sandbox, Staging and
  Production: `L-F63F402C` 10, `L-B3401D17` 5 and `L-85C9EC5A` 15, none of the 81 `sc.*` quotas with a
  default above zero at 0 and 36 above their default, with no request on record but Sandbox's three closed
  on 2026-09-24 (`log-stage-06d-unified-studio-remainder.md`, 2026-11-19).

- `SUP-183` **The portal's file upload creates a Glue table whose location is a folder named after the
  upload time in milliseconds, not under the database's `LocationUri`** (read 2026-09-13 in Sandbox's trail,
  Stage 6f first sitting). Uploading a Parquet file into `mydatabase` left it at
  `dev/local-uploads/1789265679189/house-price.parquet` in the project's bucket. `glue:CreateTable` at
  02:14:48Z, by the project role from the browser, made an `EXTERNAL_TABLE` (`ParquetHiveSerDe`,
  `IsRegisteredWithLakeFormation: true`) located at `…/dev/local-uploads/1789265679189/`. The folder name is
  the upload's time in milliseconds (02:14:39Z), and the database's `LocationUri`, `…/dev/data/catalogs/`,
  was not used. The 9,249-byte file is the only copy of the data the table reads. Where:
  `log-stage-06f-data-governance.md`, 2026-09-12/13; `docs/SMUS.md`, the upload item.

- `SUP-184` **The portal's *Create database* deploys one `DataLake` environment per database, whose Glue
  database the provisioning role writes with no default table permissions** (read 2026-09-13 in Sandbox's
  trail and 2026-10-28, Stage 6f first sitting and Stage 19). `glue:CreateDatabase` came from
  `awsds-sandbox-smus-provisioning` through `datazone.amazonaws.com`, description *"Created by DataZone for
  project eighth-experimentation"*, `LocationUri` the project's `dev/data/catalogs/`,
  `CreateTableDefaultPermissions: []`, and wrote no object; Lake Formation grants to the project-conditioned
  principals and to the manage-access role followed within eight seconds. The environment is named
  `create-datalake-database-env-<name>-<epoch ms>`; the one of 2026-10-28, for `new_database`, reached
  `ACTIVE` with its own Glue data source on `cron(22 6 * * ? *)`, the minute of its creation, which had 11
  `SUCCESS` runs by 2026-11-08. Every database created this way shares the same location prefix. The
  portal's environment carries one user parameter, `glueDbName`, and no subscription target; the same
  environment created through the API, `create-environment` with the profile's `DataLake` configuration,
  the blueprint and `--user-parameters name=glueDbName,value=<name>`, creates the same database, grants
  and daily source, its stack holding the database alone, and carries a target,
  `<environment name>-default-target`, for `GlueTableAssetType`
  and `GlueViewAssetType` over that database (measured 2026-11-11 in Staging and in Production, Stage 19
  step 4.6; the portal's `app_etl` environment in Sandbox read with none the same day). Read 2026-11-14 on
  that environment, `chz5jdb80ohocw`, no write: its daily source names no environment (`environmentId`
  null) and hangs from the project's `project.default_lakehouse` connection, the `Tooling` environment's,
  its filter naming the database; the stack's template gives `GlueDatabase`, and an Athena workgroup the
  stack did not create, `DeletionPolicy` and `UpdateReplacePolicy` `Retain`, so the stack's deletion leaves
  the database. What the environment's delete does to the source is unread. Read 2026-11-19 across four
  projects (Stage 20 8.3): the target follows an environment's rank in its project, not the path that
  created it. A project's first `ACTIVE` `DataLake` environment carries one and a later one none:
  `eighth-experimentation-lakehouse` (2026-10-26) and `test-experimentation-lakehouse` (2026-10-20) carry
  one, the portal's `new_database` (2026-10-28) and `test_project_database` (2026-11-09) environments none,
  `app-etl-dev`'s portal `app_etl` environment (2026-11-14), its project's first, one, and the API's
  `deploy-staging-app-dbt` and `deploy-production-app-dbt`, each its project's second, none. The contrast
  of 2026-11-11 set a first environment created through the API beside `chz5jdb80ohocw`, a later one of
  `eighth-experimentation`. No trail holds a `CreateSubscriptionTarget` for the target `SYSTEM` created on
  2026-11-11. In `deploy-staging` and `deploy-production` the second environment adds no connection, the
  nine staying the `Tooling` environment's, and provisions that environment's `userRoleArn`. Where:
  `log-stage-06f-data-governance.md`, 2026-09-12/13; `log-stage-19-smus-native-data-product.md`, 2026-10-28,
  2026-11-08, 2026-11-11 and 2026-11-14; `log-stage-20-dbt-lineage.md`, 2026-11-19; `docs/SMUS.md`, the
  *Create database* item. A name the account's catalog already holds is refused before any stack: the
  portal's `mydatabase` in `test-experimentation` (`60j5234reuos9c`, created 2026-11-09 19:53:53Z by the
  Data Scientist User, `eighth-experimentation`'s `mydatabase` existing) read `VALIDATION_FAILED` 11 s
  later, `failureReason` *"Failed to validate environment 60j5234reuos9c: Glue database with name
  mydatabase already exists"*, `provisionedResources` null, and the record stays in the project (read
  2026-11-22, `log-stage-06f-data-governance.md`).

- `SUP-185` **The portal's MLflow entries look their blueprint up in the domain account, so a domain whose
  configurations live in associated accounts greys them out whatever the profile carries** (read 2026-10-19,
  Stage 17 1.5). *Create MLflow App* and *Create MLflow Tracking Server* resolve the blueprint's id by name
  from `ListEnvironmentBlueprintConfigurations`, called with the domain id alone as the domain execution
  role. DataZone answers with the domain account's configurations, none here (D22), the page's query fails
  with *"No environment blueprint configurations found"*, and the tooltip says *"The MLflowApp blueprint is
  not enabled for this project"*. Neither the profile, *Update project* (`UPDATE_NOT_AVAILABLE`) nor the
  project's age plays a part. A `CreateEnvironment` with the profile's configuration id, made through the
  API by a project contributor, creates the app the entry would have. Where:
  `log-stage-17-sandbox-machine-learning.md`, the 1.5 entries of 2026-10-19.

- `SUP-186` **The portal's Generative AI menu opens only with all seven Bedrock blueprints in the profile**
  (read 2026-10-19, Stage 17 1.5). Its module maps the profile's configurations to `ChatApp`, `Evaluation`,
  `FlowApp`, `Function`, `Guardrail`, `KnowledgeBase` and `Prompt`, and answers the Playground and *AI apps*
  with *"This tool is not available for this project"* when one is missing, so a profile carrying six, the
  knowledge base left out on cost, opens none of them. Where: `log-stage-17-sandbox-machine-learning.md`,
  the 1.5 entries of 2026-10-19.

- `SUP-187` **An associated account's Bedrock models tab enables no model until the domain holds a project
  named `GenerativeAIModelGovernanceProject`, and only the domain account's setup creates one** (read
  2026-10-19, Stage 17 decision 13). In `Sandbox Account 1` the *Amazon Bedrock models* tab greys out
  *Manage* with *"Model governance project does not exist"* (measured 19:51 UTC). The console's code creates
  the project, on a profile *Generative AI model governance* with no environment configuration, only in the
  domain account's setup, the run that also configures the Bedrock blueprints and `Tooling` in the domain
  account, where D22 configures none; an associated account's *Set up generative AI* creates neither. The
  console finds the project through `ListProjects`, by id or by that name: one written by Terraform, with
  the account's `InfrastructureAccess` session group as a contributor, opened *Manage* (20:33), and the
  Submit created the models' environments and assets in it (20:52). AWS's page says the service creates the
  project, owned by whoever configures Bedrock for the domain, and that an associated account's identity
  must join it; it says neither which setup creates it nor what an associated account sees without it.
  Where: `log-stage-17-sandbox-machine-learning.md`, decision 13's entries of 2026-10-19, and
  `terraform-live/data-governance/governance/model-governance.tf`. The Submit's writes, read in the
  console's code and measured on 2026-10-19 at 20:52 UTC for five models in Sandbox (Stage 17 decision 13):
  per model enabled in projects, `CreateEnvironment` from `AwsServiceBlueprint` in the governance project
  (`amazon.datazone.BedrockModelEnvironmentType_<12 characters>`), `AssociateEnvironmentRole` with the
  provisioning role as `SYSTEM_ROLE`, `CreateAsset` of `amazon.datazone.BedrockModelAssetType` and
  `CreateListingChangeSet` `PUBLISH`; per model enabled in the playground, `bedrock:CreateInferenceProfile`
  as the person pressing Submit, named after the domain id, then an environment of
  `BedrockInferenceOnlyEnvironmentType` and an asset of `BedrockInferenceOnlyAssetType`. Sandbox's trail
  held 2 `CreateInferenceProfile` and 6 of each DataZone write from 20:52:15 to 20:52:47; six environments
  `ACTIVE`, six assets published, two application inference profiles named `dzd-d8yrvx1ko7im6o`, and no IAM
  role or customer-managed policy created. After a reload the five rows read *Enabled* while the heading
  still read *"Models enabled for the selected account and region (0)"*, and a *Manage roles* dialog's *Save
  and submit* for a model not yet enabled wrote nothing. Where: `log-stage-17-sandbox-machine-learning.md`,
  decision 13's entries of 2026-10-19.

- `SUP-188` **The Bedrock models tab adopts a provisioning role by a name no AWS page gives** (read
  2026-10-19, Stage 17 decision 13). Its Submit takes the account's role whose name contains
  `AmazonSageMakerBedrockModelManagementRole-<domain account id>`, else the role chosen in the setup wizard,
  and creates one at `/service-role/` with AWS's policy only when neither exists, all before it reads the
  role chosen per model (the console's code). A model's *Manage roles* dialog preselects that name as an
  existing role whether or not one exists (measured 19:52 UTC, with none). The role `sandbox/model-access/`
  writes under that name, at `/` under the project boundary with a policy of its own, served the Submit,
  which created no principal (20:52). The consumption dialog preselects
  `AmazonSageMakerBedrockModelConsumptionRole-<hash>` the same way, a role that did not exist. AWS's role
  page calls the role `AmazonDataZoneBedrockModelManagementRole` and its post of 2025-07-09
  `AmazonSageMakerBedrockModelManagementRole`; both say only that the service creates a role or takes a
  custom one. Where: `log-stage-17-sandbox-machine-learning.md`, decision 13's entries of 2026-10-19, and
  `terraform-live/sandbox/model-access/`.

- `SUP-189` **The portal calls DataZone for a signed-in person as the domain account's execution role, in a
  session named `user-<DataZone user profile id>`** (read 2026-10-19 and 2026-10-21 in Data Governance's
  trail, Stage 17 7.2 and Stage 18 6.1). One tab's browsing by the Data Scientist User left 327 events in
  seven minutes under `awsds-data-studio-domain-execution/user-28f1b390-…`, an id `get-user-profile`
  resolves to that SSO user, and two `UserProfileAutoCreated` by DataZone. The portal's `CreateEnvironment`
  calls for the `DataLake` environments (2026-09-13, 2026-10-15) came from the same role. A *Create project*
  the domain unit's grant refused was `CreateProject` `AccessDenied` by that role, the portal showing
  *"Failed to create project - User is not permitted to perform operation: CreateProject"*. The same
  person's writes to project storage and querybooks ran as the project role in the member account, in a
  session named `<profile id>@<environment id>` that DataZone assumed. A portal refusal is read in the
  domain account's trail. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-10-19 (1.5 and 7.2);
  `log-stage-18-staging-deployment-project.md`, 2026-10-21 (6.1 and the session name's correction).

- `SUP-190` **The SageMaker Data Agent calls DataZone from the browser as the project role, and its Bedrock
  inference leaves no event in either account's trail** (read 2026-10-30 in Sandbox's and Data Governance's
  trails, Stage 11 `TM-23`). After the Query Editor's assistant was used in `eighth-experimentation`,
  Sandbox's trail in `us-west-2` held `StartConversation` (4), `SendMessage` (2, each carrying the
  317-character prompt and answering an event stream), `GetConversation` (8) and `ListConversations` (7) as
  the project role, the person's Identity Center id as `sourceIdentity`, sent from the browser to
  `agent.datazone.us-west-2.api.aws` with no VPC endpoint, and no `GenerateCode`; their `resourceContext`
  was a `QUERY_EDITOR` notebook of `sqlworkbench`. Data Governance's trail held none of them, and no
  `bedrock` or `bedrock-runtime` event in `us-west-2`, `us-east-1` or `us-east-2`, in either account, was
  the agent's. `get-domain` carries no field for the agent's switch. The inference is AWS's: neither a proxy
  nor a Bedrock SCP's model list is on its path. Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-10-30; `docs/plan/threat-model.md` `TM-23`.

- `SUP-393` **The portal's *S3 Bucket* form prefills the prefix `amazon-sagemaker-`, and the managed
  provisioning policy creates only `sagemaker-*` buckets, so a deployment that keeps the prefix fails on
  `s3:CreateBucket`** (read 2026-11-21 in `app-ml-dev`'s gallery and measured the same day in
  `test-experimentation`, Sandbox, Stage 6a). The form's one field, *Bucket name*, an editable text box,
  opens holding `amazon-sagemaker-` over the hint *"Prefilled with the recommended prefix amazon-sagemaker.
  Must be 3 to 33 characters."*; the profile's default for the parameter, `changeme-project-bucket`, is not
  shown. `create-environment` with the same configuration and the name `amazon-sagemaker-probe-<suffix>` read
  `CREATE_FAILED` 33 seconds later: *"User: arn:aws:sts::<account>:assumed-role/awsds-sandbox-smus-provisioning/AmazonDataZoneEnvironmentDeployer-<account>
  is not authorized to perform: s3:CreateBucket on resource: "arn:aws:s3:::amazon-sagemaker-probe-<suffix>"
  because no identity-based policy allows the s3:CreateBucket action"*, and no stack remained.
  `SageMakerStudioProjectProvisioningRolePolicy` v86 (2026-11-17), the provisioning role's one policy, grants
  `CreateBucket` and the bucket's configuration calls in Sid `S3Create` on `arn:aws:s3:::sagemaker-*` alone;
  with the name `sagemaker-awsds-probe-<suffix>` the environment was `ACTIVE` in about 70 seconds. A member
  replaces the prefix with `sagemaker-`, and the refusal names a permission where the cause is the name.
  Where: `log-stage-06a-unified-studio.md`, 2026-11-21; `docs/SMUS.md` §Resource blueprints.

- `SUP-456` **Saving a space's idle timeout in the portal deletes the space's app, updates the space and
  creates the app again, so the save lasts a whole app start** (measured 2026-11-22 in Sandbox, Stage 6d's
  idle range). The space `jup8h` (JupyterLab, `ml.t3.medium`, `awsds-sandbox-dev-env` version 12) was created
  in `app-etl-dev` at 19:26:15Z with an idle timeout of 480 minutes. Its owner saved 1440, and the browser
  sent, through the project's user role, `DeleteApp` at 19:43:45Z (the server took `SIGTERM` at 19:43:46Z),
  `UpdateSpace` at 19:43:50Z carrying the whole `SpaceSettings` with `IdleTimeoutInMinutes` 1440, and
  `CreateApp` at 19:43:55Z. The portal polled `DescribeApp` every 3 s until 19:53:58Z, when it sent
  `CreatePresignedDomainUrl` for the space: the save lasted 10 min 13 s. The six JupyterLab apps created in
  Sandbox that day, all on the house image and `ml.t3.medium`, logged their first line 8 min 41 s to 9 min
  10 s after their `CreateApp`. `describe-app` kept the first app's `CreationTime`, 19:26:20Z, through the
  delete and the re-create, and its `LastHealthCheckTimestamp` read that instant while `Pending` and the
  instant of each call once `InService`, so an app's start is timed from CloudTrail's `CreateApp`. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-11-22.

### Catalog, data sources and subscriptions

- `SUP-191` **The portal's *Publish to Catalog* on a Glue table writes a data source with business-name
  generation on, an asset, a listing and two lineage nodes, and no Lake Formation grant** (read 2026-09-13
  and 2026-10-26 in Data Governance's trail, Stage 6f first sitting and 11.6). Both publishes ran as the
  domain execution role in the person's session: `CreateDataSource` (`GLUE`, `INCLUDE *`, `publishOnImport`
  false, no schedule, `enableBusinessNameGeneration` true), `CreateAsset` (`GlueTableAssetType`),
  `CreateListingChangeSet` `PUBLISH`, then two `CreateLineageNode` by `datazone.amazonaws.com`,
  `requestParameters` null and the node ids only in `additionalEventData`. No Glue or Lake Formation write
  followed. The lineage links the asset to its listing column by column (`ColumnLineageForm`) and nothing
  outside the catalog, and `list-lineage-events` returns `items: []`. The Service Authorization Reference
  (read 2026-10-18) names `datazone:domainId`, `datazone:projectId` and `datazone:userId` against no action,
  and `CreateDataSource` and `UpdateDataSource` take no resource type, so IAM reaches the generation only by
  denying a whole action. Where: `log-stage-06f-data-governance.md`, 2026-09-13, 2026-10-18 and 2026-10-26;
  `aws/catalog.py` `CT-5`.

- `SUP-192` **A published Glue asset and its listing carry no LF-Tag, and `lakeFormationDetails` reads
  empty** (read 2026-09-18 and 2026-10-26, Stage 6f verification vi). The asset `trades`, published from
  `curated` where the table carries `classification=internal`, holds `GlueTableForm`,
  `DataSourceReferenceForm`, `SubscriptionTermsForm` and `CommonDetails`, with `lakeFormationDetails` empty
  and nothing naming `classification` or an LF-Tag. The listing `house-price` read `lakeFormationDetails:
  {}` on 2026-09-18, when its table had no tag to show. The fulfilment grants `SELECT` on the table by name,
  so a subscription to `curated.sample_trades`, tagged `restricted` on `counterparty`, would hand the column
  over whole: inferred from the mechanism, not run. Where: `log-stage-06f-data-governance.md`, 2026-09-18,
  2026-10-26 and 2026-10-27.

- `SUP-193` **A Glue table's subscription target is the subscriber's `DataLake` environment, never its
  `Tooling` environment, so a project without an `ACTIVE` `DataLake` environment cannot receive one** (read
  2026-10-20 with `list-subscription-targets`, Stage 6f 2.0). Each `Tooling` environment, in both Sandbox
  projects and in Staging's `deploy-staging`, carried two targets: one for `BedrockModelAssetType`, and
  `Tooling-default-target` for `SageMakerFeatureGroupAssetType` and `SageMakerModelPackageGroupAssetType`.
  Only an `ACTIVE` `DataLake` environment carried a target for `GlueTableAssetType` and `GlueViewAssetType`,
  named `<environment>-lakehouse-default-target`, its `manageAccessRole` the project role. With every
  Sandbox `DataLake` environment `CREATE_FAILED`, no Sandbox project could receive a Glue subscription until
  `test-experimentation`'s environment reached `ACTIVE` later that day. Where:
  `log-stage-06f-data-governance.md`, 2026-10-20; `docs/plan/integrations.md` `INT-23`.
  Read again 2026-11-18 (Stage 21 1.3): `list-subscription-targets` returns `type: null` for every target and
  `get-subscription-target` gives it, `GlueSubscriptionTargetType` on the lakehouse environment's target,
  `BedrockModelSubscriptionTargetType` and `BaseSubscriptionTargetType` on `Tooling`'s; the Glue target is
  authorized to `abac:CURRENT_PROJECT`. Where: `log-stage-21-redshift-s3-data-products.md`, 2026-11-18.

- `SUP-194` **DataZone sets `aws:SourceIdentity` on the project-role sessions it opens for a member or as
  `SYSTEM`, and on none it opens to fulfil a subscription** (measured 2026-10-21 and 2026-10-22, Stage 18
  6.2 and 7.2). A person's, an IAM principal's and a data source's `SYSTEM` sessions carried the caller's
  profile id or `SYSTEM`; the workers' (MWAA Serverless, Glue, SageMaker) and the
  `AWSDataZone-Subscriptions` sessions carried none, so a deny conditioned on the key binds the first and
  spares the second, the fulfilment's `glue:PutResourcePolicy` included. Where: `log-stage-18`'s 6.2, 4.3
  and 7.2 entries.

- `SUP-195` **A subscription's fulfilment shares the producer's whole catalog** (measured 2026-10-22, Stage
  18 7.2). With Staging's `CROSS_ACCOUNT_VERSION` at 1, the grant DataZone wrote carried
  `CROSS_ACCOUNT_VERSION` 5 in its own parameters; the RAM share it created named Staging's `catalog`,
  `database/*` and `table/*/*` with the three ReadWrite Glue permissions, and three `glue:PutResourcePolicy`
  calls put per-resource policies naming the consumer account on the same three resources, which the stage
  log took for Staging's Data Catalog resource policy. Lake Formation's `SELECT` under the subscribing
  project's context is what scopes the read, and the revocation removed all of it. Where: `log-stage-18`'s
  7.2 and C1 entries. A lake table shared to Sandbox (measured 2026-10-26, Stage 6f 11.9)
  reached grant `COMPLETED` and asset `GRANTED` 63 s after the approval (21:36:15Z to 21:37:18Z). The
  producer's project role, in `AWSDataZone-Subscriptions` sessions with no source identity, called
  `BatchGrantPermissions` (`SELECT` on `curated.trades`, no grant option) and `ram:CreateResourceShare`
  (`LakeFormation-V5-ZKUYXYESG4`, `allowExternalPrincipals` false), then four `glue:PutResourcePolicy` on
  `database/*` (twice), `table/*/*` and `catalog`, each with `enableHybrid` `TRUE`. Those policies are per
  resource, under `aws:PrincipalOrgID`: `glue get-resource-policy` still answered *"Policy not found"*, and
  `glue get-resource-policies` listed them. In Sandbox the subscribing project's role created the resource
  link in its `DataLake` database and granted `DESCRIBE` on it under the project's condition; Glue reports
  the link's `CreateTime` as the target table's. Where: `log-stage-06f-data-governance.md`, 2026-10-26;
  `docs/AWS_STATE.md`'s grant register. Inside one account (measured 2026-11-14, Stage 19 pass 2, a
  Sandbox project's product shared to another Sandbox project) the fulfilment writes no RAM share and
  no catalog policy: the producer's project role granted `SELECT` on the table to the account's
  `IAMPrincipals` under the consumer's project condition 45 s after the request, the consumer's
  project role created the link 10 s later and granted `DESCRIBE` on it to `IAMPrincipals` and to
  `arn:aws:identitystore:::user/*` under the same condition, each in an `AWSDataZone-Subscriptions`
  session, and the grant read `COMPLETED` 65 s after the request. `glue get-table` on the link
  answered the target's `CreateTime` and `CreatedBy` again, the link's own creation being the
  trail's `CreateTable` (`log-stage-19-smus-native-data-product.md`, 2026-11-14). Read again 2026-11-17
  in Staging's trail (Stage 18 7.2): the three `PutResourcePolicy` at 2026-10-22T00:42:23Z each carried a
  `resourceArn` (`catalog`, `database/*`, `table/*/*`), one statement and `enableHybrid` `TRUE`, from the
  producer's project role in an `AWSDataZone-Subscriptions` session through `datazone.amazonaws.com`; the
  revocation made three `glue:DeleteResourcePolicy` on the same ARNs, from the same role in the same kind of
  session, at 01:07:09Z, 39 s after `revoke-subscription`. The *"Policy not found"* Stage 18 read after the
  revocation came from `glue get-resource-policy`, which lists none of these (`SUP-099`): the trail's three
  deletes are what show them gone, and `glue get-resource-policies` read an empty list on 2026-11-17
  (`log-stage-18-staging-deployment-project.md`, 2026-11-17). A second subscriber project in an account
  the producer already shares to (measured 2026-11-22, Stage 6f 4.3, `test-experimentation` on
  `curated.trades` beside `eighth-experimentation`) costs one grant: the producer's role made one
  `BatchGrantPermissions` (`SELECT` to Sandbox's `IAMPrincipals` under the new project's condition,
  `CROSS_ACCOUNT_VERSION` 5) 5 s after the approval and no RAM or Glue policy call, the share
  `LakeFormation-V5-ZKUYXYESG4` and the five per-resource policies keeping their update times and hashes, and
  the grant read `COMPLETED` 16 s after the approval, against 63 s for the first. The same night inside one
  account (`house-price` into `test-experimentation`): the owner's grant 32 s after the request, the link 11 s
  later, `COMPLETED` at 54 s (`log-stage-06f-data-governance.md`, 2026-11-22). Read in Production the same
  day (Stage 19 4.12 and Stage 20 5.0, a deployment project's product to two Sandbox projects, Production's
  `CROSS_ACCOUNT_VERSION` at 4): the first fulfilment wrote the share `LakeFormation-V5-2Y5MBO5ADP` at
  14:04:45Z, the grant with `CROSS_ACCOUNT_VERSION` 5 and three per-resource policies at 14:04:46Z, each
  from `deploy-production`'s project role, and read `COMPLETED` 61 s after the grant's creation; the second,
  on the same listing, one `BatchGrantPermissions` and no RAM or Glue call, `COMPLETED` 4.5 s after its
  grant's creation (`log-stage-19-smus-native-data-product.md` and `log-stage-20-dbt-lineage.md`,
  2026-11-22).

- `SUP-196` **`UpdateDataSource` refuses the `dataAccessRole` that `GetDataSource` reports for a Glue source
  on a connection** (measured 2026-10-26 in Data Governance, Stage 6f 11.6). A configuration built from the
  saved `get-data-source` output, with only the filter changed, was refused at 21:53:31Z, *"For Glue
  dataSources that use Connection, dataAccessRole must be null"*, and nothing changed. The same call without
  the role succeeded (`UPDATING`, then `READY` within ten seconds), and the source still reported the
  project role afterwards, read from the connection. A read-modify-write of a connection-backed source drops
  that field. The trail held the two calls as `InfrastructureAccess` and a third `UpdateDataSource` one
  second after the second with no session issuer. Where: `log-stage-06f-data-governance.md`, 2026-10-26.

- `SUP-197` **A DataZone Glue data source over a subscriber's `DataLake` database imports the subscription's
  resource link as an inventory asset** (read 2026-10-28, Stage 19 readings of the domain). The fulfilment
  of the `trades` subscription had created the resource link `trades` in `eighth-experimentation`'s
  `glue_db_blerpkhn9nj7o0` on 2026-10-26. That database's data source, `publishOnImport` false, then ran
  `SCHEDULED` at 2026-10-27T21:32:10Z (`SUCCESS`, 2 s, `added: 1`), and the project's inventory held a
  `GlueTableAssetType` asset `trades`, external identifier the link `glue_db_blerpkhn9nj7o0/trades`, created
  21:32:12Z, with no listing, beside its own `house-price`. The subscriber thus owns an unpublished asset
  for data it holds only by subscription, and a check that reads listings and not inventories misses it.
  Seen once by 2026-10-28. Read again 2026-11-10 with `search --search-scope ASSET`: the asset `cm329mc3bqu39s`'s
  external identifier is `arn:aws:glue:us-west-2:<Sandbox Account 1>:table/glue_db_blerpkhn9nj7o0/trades.avhvbqn37ty7m8`;
  the 2026-10-28 text named the link, not the field (`SUP-343`). Where: `log-stage-19-smus-native-data-product.md`,
  2026-10-28 and 2026-11-10.
  Seen again 2026-11-14 in `test-experimentation` (Stage 19 verification x): a run started from the portal,
  type `PRIORITIZED`, `added: 1`, imported the link `glue_db_4zojr4rr6bmnww.trades_notional` as the
  unlisted asset `b5r73n41qe7jf4`; after the revocation deleted the link (`SUP-365`) the asset stayed in the
  inventory with no table behind it. Where: the same log, 2026-11-14.
  Read again 2026-11-15 on the source's scheduled run at 02:51 UTC, the first after the revocation:
  `4etghy8jms5o5s`, `SUCCESS` in 1.3 s, `added`, `updated`, `unchanged` and `failed` all 0, no activity, the
  source's `lastRunAssetCount` 0, and the asset at revision 1, unlisted. A run over a database whose table is
  gone neither removes, nor reports, nor counts the asset it imported. Where: the same log, 2026-11-15.

- `SUP-198` **A listing's `DataSourceReferenceForm` keeps the data source's configuration as published, and
  disagrees with the source after an update** (read 2026-10-27 in Data Governance, Stage 6f decisions 2 to
  5). `update-data-source` turned `enableBusinessNameGeneration` off on the source `aus07vzuom8ntc` at
  21:53:45Z on 2026-10-26. On 2026-10-27 the listing `b3bagfgnvev3tc`, at revision 2, still carried
  generation `true` in its `DataSourceReferenceForm`, while `get-data-source` read `false`. `get-listing`
  returns the forms as a JSON string, beside `SubscriptionTermsForm.approvalRequired` (`YES`). A check of a
  source's settings reads the source, never the listing's copy. Where: `log-stage-06f-data-governance.md`,
  2026-10-26 and 2026-10-27; `docs/SMUS.md`, the listing item.

- `SUP-343` **A Glue table asset's external identifier is the table's ARN with the owning project's id
  suffixed to its last segment** (read 2026-11-10 with `search --search-scope ASSET` as Sandbox's
  `InfrastructureAccess`, Stage 19 pass 1). All three assets of `eighth-experimentation` carry the shape
  `arn:aws:glue:us-west-2:<Sandbox Account 1>:table/<database>/<table>.avhvbqn37ty7m8`, whichever act made
  them: `house-price`, the user's portal publish of 2026-09-13; `trades`, the subscriber's source import of
  2026-10-27 (`SUP-197`); `trades_notional`, the project's source started by the workflow's `publish` task
  on 2026-11-10 (`createdBy` `SYSTEM`). The search's item carries no revision. No page this project read
  gives the shape. Code that matches an asset on `<database>/<table>` finds none: Stage 19's run 1 failed
  on it (*"0 asset(s) for app_etl/trades_notional in the project, one expected"*). Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-10; `examples/app-etl/code/app_etl_tasks.py`,
  `names_table`.

- `SUP-344` **Each save of a metadata form type is a `CreateFormType` that answers a new revision, and
  `GetFormType`'s `createdAt` is the newest revision's** (read 2026-11-10 in Data Governance's trail and with
  `get-form-type`, Stage 19 decision 4). The portal's two saves of `classification`, the form and then its
  field, were two `CreateFormType` calls through `awsds-data-studio-domain-execution` in the person's
  session, at 00:41:53 and 00:44:24 UTC, answered revisions 1 and 2. `get-form-type` answers revision 2 with
  `createdAt` 00:44:24 UTC, so the form's first creation is in the trail alone, which redacts the model
  (`"***"`). `GetFormType` answers Data Governance's `InfrastructureAccess`, no member of the owning project,
  where `GetAsset` refuses it. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-10.

- `SUP-345` **`CreateListingChangeSet` answers a listing revision that stays `CREATING` while the service
  writes the next revision `ACTIVE`** (read 2026-11-10 with `get-listing` and Sandbox's trail, Stage 19
  pass 1). The project role's `PUBLISH` of asset `4j6p77v7dm2840` at 02:44:45 UTC, its first listing, was
  answered `{"listingRevision": "1", "listingId": "ct5d0innrgw3v4"}`. Revision 1 still answered `CREATING`
  six minutes on, its `updatedAt` its `createdAt`; revision 2 answered `ACTIVE`, updated 0.8 s after the
  creation, carrying the asset's revision; `get-listing` without a revision answers revision 2, and
  `get-asset` the listing `ACTIVE`. Code that waits for the answered revision waits forever: Stage 19's
  rerun failed on it (*"listing ct5d0innrgw3v4 revision 1 not ACTIVE after 120 s"*) with the product
  listed. Read the latest revision, one at or past the answered one. A republication of a listed asset is
  unmeasured. Read again at a republication, 2026-11-10 03:23 UTC (run `hiErIl5sGJSyRFx`): the change set
  answered revision 3 through the `datazone` interface endpoint; revision 3 read `UPDATING` by the task,
  then `ACTIVE` at 03:23:00.426 UTC still carrying the previous asset revision 2, and revision 4 `ACTIVE`
  0.9 s later carrying asset revision 6, the source run's. `UPDATING` is absent from the API's model
  (`ListingStatus`: `CREATING`, `ACTIVE`, `INACTIVE`; aws-cli 2.37.12). The publication is the revision
  past the answered one in both readings, and a wait at or past it takes revision 3's previous content.
  Read a third time at 03:56 UTC (run `MmFs38SsxUFQ2xM`): answered revision 5, revision 5 `ACTIVE` at
  03:56:05.061 UTC carrying asset revision 6 and revision 6 `ACTIVE` at 03:56:06.592 UTC carrying asset
  revision 7, which the task, waiting past the answered revision, took for the publication.
  Where: `log-stage-19-smus-native-data-product.md`, 2026-11-10;
  `examples/app-etl/code/app_etl_tasks.py`, `publish_asset`.

- `SUP-346` **DataZone admits `StartDataSourceRun` on a project's data source from a principal that is no
  member of that project** (read 2026-11-10 in Sandbox's and Data Governance's trails, Stage 19
  verification ii). `eighth-experimentation`'s project role, whose DataZone profile is a
  `PROJECT_CONTRIBUTOR` of that project alone, started `test-experimentation`'s source `3zp6fog9jep1qo`
  from a space at 03:56:35 UTC: no error, answered `REQUESTED`, the run `SUCCESS` with every statistic 0.
  The role's IAM grant is `datazone:StartDataSourceRun` on the domain's ARN. A design that relies on
  DataZone's project membership to keep one project from running another's source has no such control:
  the IAM statement is the one boundary. Read again the same day, the boundary's reach: the Service
  Reference's DataZone JSON (`v1.5`) gives `StartDataSourceRun` no resource type and no condition key and
  maps `datazone:domainId`, `datazone:projectId` and `datazone:userId` to no action, while DataZone
  authorizes against the domain's ARN (run 1's `GetGroupProfile` refusals name it as the resource, and
  `awsds-sandbox-workflows` `v4`'s statement on it is the role's one grant of the action). IAM narrows the
  start to the domain, every project in every associated account. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-10.

- `SUP-347` **`GetLineageNode` answers `ResourceNotFoundException` to a Glue table node's
  `sourceIdentifier`, which its API page says the identifier accepts** (read 2026-11-10 in the domain,
  Stage 19 verification v). The node `d0m1zl6r8q3uvk`, created by `datazone.amazonaws.com` from the Glue
  job's OpenLineage events, has the table's ARN, `arn:aws:glue:us-west-2:<Sandbox>:table/app_etl/trades_notional`,
  as its `sourceIdentifier`. It answered to its id and refused that ARN, character for character the
  value `CreateLineageNode`'s `additionalEventData` recorded, from both accounts' infrastructure sessions.
  The asset's node answered to `amazon.datazone.asset/4j6p77v7dm2840` and a job's node to
  `default.app_etl_avhvbqn37ty7m8`, so the lookup by `sourceIdentifier` works for those forms. An asset's
  own id is no node identifier either. The ids are in Data Governance's trail, each `CreateLineageNode`
  carrying a node's id and `sourceIdentifier` in `additionalEventData`. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-10.

- `SUP-354` **`CreateSubscriptionRequest` naming a domain, a listing and a project that do not exist is
  refused, never answered not-found** (measured 2026-11-11, Stage 19 step 4.1). `aws datazone
  create-subscription-request --domain-identifier dzd_canaryprobe0000 --subscribed-listings
  identifier=canaryprobe0000 --subscribed-principals project={identifier=canaryprobe0000}`, ids that pass
  the model's patterns and name nothing: as `Policy Canary`'s administrator with no deny in the way,
  DataZone's own layer answered `AccessDeniedException`, *"User is not permitted to perform operation:
  CreateSubscriptionRequest"*; under a service control policy denying the action the same call read
  *"with an explicit deny in a service control policy"* naming the policy, on the canary under a candidate
  and as `InfrastructureAccess` in Staging and in Production under `awsds-org-scp-ou-workloads`. IAM and
  the organization's policies answer before DataZone looks the identifiers up, and DataZone's own answer
  for ids that name nothing is a refusal; whether it authorizes first or masks a not-found was not
  separated. A deny on the action is therefore probed with made-up ids, the probe creating nothing
  whatever the answer, and the two wordings separate the layers (Lesson 21).
  `ListEnvironmentBlueprints` on the same made-up domain read the policy's deny under the candidate; its
  answer with nothing denying it was not read. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-11; `aws/probes/probes.py`; `runbooks/scp-battery.md`.
- `SUP-362` **The portal's *Share* on a listing is a `CreateSubscriptionRequest` the owner makes for
  the consumer project, accepted at creation** (measured 2026-11-14, Stage 19 pass 2). As the owner of
  the producing project, on the catalog's page, *Share* in the menu of a data product's listing, the
  dialog *Create subscription* with a project chosen: the domain account's trail holds one
  `CreateSubscriptionRequest` in that user's portal session, naming the listing and the consumer
  project, and no `AcceptSubscriptionRequest`. The request reads `ACCEPTED`, its `createdAt` equal to
  its `updatedAt`, with no `reviewerId` and an empty `requestReason`; the subscription reads
  `APPROVED` and carries that request's id. `list-subscription-requests` with the approver's project
  and no status answers none of it: the request is read by its id. The fulfilment is a
  subscription's (`SUP-195`). A Share on a Glue-table listing is therefore told from a consumer's
  request by its creator, a member of the owning project, and by the absent reviewer, the record
  `catalog.py` `CT-11` fails on for a lake listing. A consumer's own request by a member of the
  owning project, which AWS's approval page approves at creation, was not made, so whether it leaves
  the same record is unread. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-14, whose
  entries on pass 2 cite it as `SUP-360`.
- `SUP-363` **A subscription to a data product is listed under each asset listing the product
  carries, and its grant under the asset listing alone** (measured 2026-11-14, Stage 19 step
  6.1). The data product `trades-notional` carries one asset listing, `trades_notional`, and holds
  one subscription. `list-subscriptions` and `list-subscription-requests` with
  `--subscribed-listing-id` return that subscription and its request under the product listing's
  id and under the asset listing's alike, each naming the product listing as its subscribed
  listing with the asset listings it carries. `list-subscription-grants` returns the grant under
  the asset listing's id, which its `grantedEntity` names, and nothing under the product
  listing's. A join of Lake Formation's grants to subscriptions therefore asks under both ids and
  keys the grant by the asset listing, as `catalog.py` `CT-17` does. `list-subscriptions
  --owning-project-id` selects by the subscribing project and answers a session that is no member
  of it: Data Governance's `InfrastructureAccess`, a member of none of the four, read
  `test-experimentation`'s one subscription, `eighth-experimentation`'s two and each deployment
  project's none. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-14; `aws/catalog.py`.

- `SUP-365` **A subscription's revocation removes the fulfilment asynchronously, and a session reading
  through the resource link reads until the link's delete, then answers that the table does not exist**
  (measured 2026-11-14 in Sandbox, Stage 19 verification ix, inside one account). `RevokeSubscription` on
  `d21t6zwyzrcas0` from the portal at 23:00:00 UTC, no `retainPermissions` in the request (Data
  Governance's trail); `BatchRevokePermissions`, one entry, by the producer's project role at 23:00:52 and
  `DeleteTable` on the consumer's link by the consumer's project role at 23:01:02, each in an
  `AWSDataZone-Subscriptions` session (Sandbox's trail). A Glue interactive session on
  `project.spark.fineGrained`, opened at 22:47 UTC, counted the table through the link once after the
  revocation and failed at 23:01:21 with *"[TABLE_OR_VIEW_NOT_FOUND] The table or view
  `glue_db_4zojr4rr6bmnww.trades_notional` cannot be found"*. The subscription then read `REVOKED`,
  `get-subscription-grant` `ResourceNotFoundException`, the link `EntityNotFoundException`, and the asset
  the consumer's source had imported from the link stayed in its inventory (`SUP-197`). The refusal names a
  missing object, not a revoked access. Whether a session reading by the target's name keeps reading past
  `BatchRevokePermissions` was not measured. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-14.

- `SUP-366` **`DeleteDataSource` is refused with an empty `ValidationException` while an asset the source
  imported exists** (read 2026-11-14 from Data Governance's trail, Stage 19 item 20; the cause inferred from
  the order). `DeleteDataSource` on `budryu9mt9y5u8`, by the domain execution role in the data scientist's
  portal session at 23:11:14 UTC, carried `errorCode` `ValidationException` and no `errorMessage`;
  `CreateListingChangeSet` `UNPUBLISH` and `DeleteAsset` on the source's asset `4j6p77v7dm2840` followed at
  23:11:38, and `DeleteDataSource` on the same source was accepted at 23:11:51. A retirement deletes the
  asset first and the source right after, before the source's next scheduled run imports the table again.
  Where: `log-stage-19-smus-native-data-product.md`, 2026-11-14; Stage 19's sitting step 8.

- `SUP-371` **`Search` refuses the `DATA_PRODUCT` scope without an owning project, so no identity reads a
  data product's name across a domain** (measured 2026-11-16, Stage 19 release G step 1). `aws datazone
  search --search-scope DATA_PRODUCT --search-text trades-notional` answered `ValidationException`,
  *"OwningProjectId is mandatory for SearchScope - DATA_PRODUCT"*, while the service model the CLI 2.37.12
  carries marks `--owning-project-identifier` optional. With a project, a non-member's search is
  `AccessDeniedException`: the infrastructure profiles of Sandbox, Staging and Production each read only the
  projects their sessions belong to. A data product's name is the domain's (`SUP-369`), so the
  domain-wide answer to "is this name free" is the create's conflict, and a reading per project covers only
  the projects the reader is a member of. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-16;
  `runbooks/promotion.md` §N.8.5 step 1.

- `SUP-377` **DataZone refuses `GetAssetType` to a member account's caller that `SearchTypes` answers with the
  same types** (measured 2026-11-18 at 00:40 UTC, Stage 21 1.3). Sandbox's `InfrastructureAccess` session, a
  contributor of both Sandbox projects, listed the 24 managed asset types and their forms with `search-types
  --managed --search-scope ASSET_TYPE`, and `get-asset-type` answered *"is not authorized to perform:
  datazone:GetAssetType on resource: arn:aws:datazone:us-west-2:<Data Governance Account>:domain/dzd-d8yrvx1ko7im6o
  because no resource-based policy allows the datazone:GetAssetType action"*. The same call answered as
  `awsds-infra-data` in Data Governance. The wording names a resource policy no API of the domain manages, so a
  type's revisions and required forms are read from the domain's account. Where:
  `log-stage-21-redshift-s3-data-products.md`, 2026-11-18.

- `SUP-391` **A dataset's `symlinks` facet naming a Glue table makes its lineage node the table's ARN in an
  event with no Glue environment properties, which the `sourceIdentifier` page reserves to Glue's events**
  (measured 2026-11-21, Stage 20 2.4). dbt 1.11.16's events, built by OpenLineage's dbt wrapper 1.55.0 and
  posted with `PostLineageEvent` as `app-dbt-dev`'s role, name each dataset
  `awsathena://athena.us-west-2.amazonaws.com` `awsdatacatalog.app_dbt.<table>` with one `symlinks`
  identifier, namespace `arn:aws:glue:us-west-2:<Sandbox>`, name `table/app_dbt/<table>`, type `TABLE`; their
  run facets are `dbt_run`, `dbt_version`, `parent`, `processing_engine` and `tags`, with no
  `environment-properties`. The domain created the output's node `6w7hp2vvi8kscw` with the `sourceIdentifier`
  `arn:aws:glue:us-west-2:<Sandbox>:table/app_dbt/notional_by_desk`, and the input took `3s0gk0eg2o68pc`, the
  node the Glue job's events had created for `trades`: Data Governance's trail holds no `CreateLineageNode`
  with an `awsathena://` identifier. Each node's `DatasetForm` keeps both names as `alternateIdentifiers`, the
  Athena one and the symlink joined by a slash (`arn:aws:glue:us-west-2:<Sandbox>/table/app_dbt/trades`), and
  the `ColumnLineageForm` names its source table by the Athena name. The page reads the symlink for an event
  whose `environment-properties` carries `GLUE_VERSION`, and *"In all other cases, dataset nodes'
  sourceIdentifier is populated using <namespace>/<name>"*, which would have made the node
  `awsathena://athena.us-west-2.amazonaws.com/awsdatacatalog.app_dbt.notional_by_desk`, apart from its asset.
  A dbt project's events join the Glue assets' graph as the wrapper builds them, with no transformer in the
  client (Stage 20 decision 3). Where: `log-stage-20-dbt-lineage.md`, 2026-11-21.

- `SUP-401` **`DeleteLineageEvent` is refused to a member account by the domain's resource share, whose
  managed permission carries `PostLineageEvent` and not the delete, and to the domain's own account by
  DataZone itself** (measured 2026-11-21, Stage 20 3.4). `delete-lineage-event` on one posted event as
  `InfrastructureAccess`, aws-cli 2.37.12. From Sandbox at 05:50:51 UTC: *"… is not authorized to perform:
  datazone:DeleteLineageEvent on resource: …:domain/dzd-… because no resource-based policy allows the
  datazone:DeleteLineageEvent action"*. From Data Governance, the domain's account, at 05:50:54: *"User is
  not permitted to perform operation: DeleteLineageEvent"*, DataZone's own wording after IAM let the call
  through. `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, versions 13 and 14, carries
  `PostLineageEvent` and the lineage reads and no `DeleteLineageEvent`; the root domain unit's one owner is
  an Identity Center group, with no IAM principal. AWS's lineage authorization and API pages name neither
  who may call the delete nor what it removes (read 2026-11-21). A posted event stays in the graph until an
  identity the domain admits deletes it; the infrastructure user is none in either account, and the posting
  role was not tried. Where: `log-stage-20-dbt-lineage.md`, 2026-11-21 (3.4).

- `SUP-402` **The domain adds a posted lineage event about any project's dataset to that dataset's node,
  whoever posts it, and names as its creator the person a session carries, else the role** (measured
  2026-11-21, Stage 20 2.6 and 3.4). From a space of `test-experimentation` as that project's role, an
  event whose output named `app-dbt-dev`'s table by its Glue ARN answered `processingStatus` `SUCCESS`: the
  table's node took a version at the event's time with the foreign job's run upstream, and the portal drew
  that job on `app-dbt-dev`'s asset's *Lineage* tab, naming the node by its latest version's dataset name.
  Posts from a space, the role's session `SageMaker` whose `sourceIdentity` is the user, name as creator of
  the events and of the nodes they add the person's profile (type `SSO`); a workflow's posts, the session
  `AmazonMWAAServerless` with no `sourceIdentity`, name the role's profile (type `IAM`). Data Governance's
  trail records both as `AWSAccount`, so the domain's account cannot tell them apart. The pages read for
  this project say posting needs `datazone:PostLineageEvent` and name no check against the dataset's
  owning project. A role holding `PostLineageEvent` writes into every project's graph, and a node's history
  is the instrument that shows who did. Where: `log-stage-20-dbt-lineage.md`, 2026-11-21 (2.6, 3.4).

- `SUP-415` **A subscription's fulfilment writes a lineage node for the subscriber's resource link, keyed by
  the link's Glue ARN, and a later link of the same name inherits that node with every upstream it had**
  (measured 2026-11-22, Stage 6f 2.2 and 4.3). After each grant read `COMPLETED`, Data Governance's trail
  holds `datazone.amazonaws.com` writing a `DatasetLineageNodeType` node whose `sourceIdentifier` is the
  link's ARN (`arn:aws:glue:us-west-2:<Sandbox>:table/glue_db_4zojr4rr6bmnww/<table>`), named after the
  subscription target and carrying `SubscriptionTargetLineageForm`, `DatasetSchemaForm`, `DatasetForm` and
  `ColumnLineageForm`, with the listing's node as its upstream and both versions dated at the grant's
  completion: `house-price`'s link a new node 6 s after its grant completed, `trades`' link a new version
  14 s after. That `trades` node, `3juvtmem73n1g0`, dates from 2026-10-22, when Stage 18 7.2's subscription
  to Staging's `trades` created a link of the same name; its revocation added a version and kept the edge.
  The node now lists two upstreams, the lake listing's node and that of Staging's listing
  `bx8v3rafykv3ww`, which `get-listing` answers `ResourceNotFoundException`. A subscriber's graph keeps a
  revoked producer as an input of every link that reuses the name. Where:
  `log-stage-06f-data-governance.md`, 2026-11-22.

### Connections

- `SUP-199` **A portal S3 connection over an already registered Access Grants location needs none of the
  `S3AG*` statements or the `iam:PassRole` of AWS's documented location role** (measured 2026-08-26 in
  Sandbox, Stage 16 4.2 to 4.4). The access role `awsds-sandbox-lake-access` carried object and list actions
  and the data key's use, and none of the location- and grant-management statements or the `iam:PassRole` to
  Access Grants that AWS's documented "option 1" role carries. The form asked for four fields, name, S3 URI,
  Region and the access role from a dropdown; creation succeeded with no complaint and reused the location
  registered beforehand. CloudTrail showed both paths in use: direct `sts:AssumeRole` of the access role by
  the project role (`externalId` the project id, session tags `AmazonDataZoneProject` and
  `AmazonDataZoneDomain`, a scoping session policy, 1800 s), and `GetDataAccess` vends answered by assumes
  `invokedBy` `access-grants.s3.amazonaws.com`, which a `ResourceName` lookup misses, so the full events
  were read. Where: `log-stage-16-sandbox-lake.md`, 2026-08-26 sitting 3; `stage-16-sandbox-lake.md`
  verification ii; `terraform-live/sandbox/lake/iam.tf`.

- `SUP-200` **`AmazonDataZoneProject` is a single-valued tag key, so a Redshift compute admits one SageMaker
  project** (read 2026-09-20). AWS's instruction is to add *"1 of the following tags"* to the workgroup and
  its namespace: either `AmazonDataZoneProject={{projectID}}`, which names one project, or
  `for-use-with-all-datazone-projects=true`, which names every project in the account. There is no
  per-project list, because a tag key holds one value — on both objects. A plan that says *"one tag per
  admitted project"* is therefore not implementable, and a second map entry would silently overwrite the
  first project's tag and break its connection with nothing in the plan output to say which project lost
  access. Where: `log-stage-06h`, `terraform-live/sandbox/warehouse/variables.tf`'s `projects` validation.

- `SUP-201` **The SageMaker Unified Studio portal requires an access role on a same-account Redshift
  connection, and both AWS's procedure and the field's own help say it does not** (measured 2026-09-21, by
  the user, in the form). *"Gaining access to Amazon Redshift resources"* splits in two: the same-account
  procedure is three steps and names no role — the admin tags the workgroup and its namespace and *"then
  must send you a username and password for a database user"* — while the access role, its trust policy and
  the `RedshiftDbUser` tag live entirely under *"resources in a different account"*. The form's help says
  *"Access role ARN is optional. Required when connecting to resources in a different AWS account."* The
  form then refuses to submit without it, same account, same VPC, while marking `AWS Secret` optional beside
  it. Lesson 41 with the polarity reversed: a vendor optional the implementation makes mandatory, so the
  premise that travelled was the wrong one in both directions. Where: `log-stage-06h` (2026-09-21),
  `sandbox/warehouse/iam.tf`.

- `SUP-202` **"IAM credentials" is not a credential type in the DataZone API at all** (read 2026-09-21 from
  `aws datazone create-connection`'s own model). `redshiftProperties.credentials` is a tagged union with
  exactly two variants, `secretArn` and `usernamePassword`. The portal's third option is
  `awsLocation.accessRole` plus the role's `RedshiftDbUser` tag, which *"determines the federated database
  user"* — a shape that carries no standing credential, which is why the portal's requirement of an access
  role (`SUP-201`) turned out to be the better outcome and why the purpose-made secret held in reserve was
  never built. Two things the pages do not say: whether `RedshiftDbUser` is used verbatim or prefixed the
  way an IAM-derived user is spelled (`IAMR:<role>`), and — from the serverless side — that a database user
  is created on first sign-in, so the grant can be pre-made or not at all. `RedshiftDbRoles` maps roles at
  that first sign-in, and *"in a case where you pass a role name that doesn't exist in the database, it's
  ignored"*: a silent nothing, which is why it was refused. Where: `log-stage-06h` (2026-09-21).

- `SUP-203` **The database identity of a SMUS Redshift connection is the access role, not the project role
  and not the person** (measured 2026-10-10, from the account's own trail).
  `redshift-serverless:GetCredentials` is called by the assumed access role; the project role's own calls
  are `ListWorkgroups`, which fills the compute dropdown, and the `sts:AssumeRole` that gets there. So the
  `RedshiftDbUser` tag belongs on the access role, layer 2's reach has to be attached to both roles for
  different reasons, and *whose identity reaches the database* is a third answer again after Stage 6d step
  7's `StartSession`. Creating the connection mints no database session: the compute reads `Available` with
  `pg_user` unchanged, because a database user is created when credentials are used rather than when they
  are minted. Where: `log-stage-06h` (2026-10-10).

- `SUP-204` **Two sessions on the same role carry different session tags, and the session name is the only
  thing that tells them apart** (measured 2026-10-10, after reading one for the other). SMUS assumes one
  project role from two places: the portal's session, named `<Identity Center user id>@<environment id>`,
  carries `RedshiftDbUser` and `RedshiftDbRoles`; the space's session, named `SageMaker`, carries
  `RedshiftDbUser` and not `RedshiftDbRoles`. Both appear in one `lookup-events` output, identical but for
  `roleSessionName` and the tag list — and a capability read off the wrong one becomes a mechanism you then
  cannot make work, with nothing broken to find. `transitiveTagKeys` was `None` on both, so no tag survives
  a further chain. Read `roleSessionName` before attributing a session tag, and treat "the role carries X"
  and "this session carries X" as different claims — a role tag is overridden by a session tag of the same
  key, so the role's value can be live and irrelevant at once. Where: `log-stage-06h` (2026-10-10), 6h
  decision 8a.

- `SUP-205` **The door into one database decides the database user, one per project or one per person**
  (measured 2026-10-10). The same warehouse, the same schema, the same project: through the
  portal's Data page the grantee is `IAMR:<the project role's name>`, set by the access role's
  `RedshiftDbUser` tag; through JupyterLab, where the project role reaches `5439` directly, Redshift
  auto-creates `IAMR:user-<Identity Center user id>@<project id>` holding nothing. So a `GRANT` written for
  one door leaves the other with a session that authenticates and can read nothing — and this grantee cannot
  be pre-made, because it does not exist until that person first connects. Asking "is the database user per
  project or per person" has no answer: it is a property of the path, not of the design. The per-person
  `GRANT` is the trap — it is the identity seam, one statement per person per schema; the mechanism that
  fits is `RedshiftDbRoles` on the role the user signs in with, which maps roles at first sign-in. Where:
  `log-stage-06h` (2026-10-10), `runbooks/redshift-connection.md` §T, `docs/AWS_STATE.md`'s Redshift
  register. A notebook that assumes the access role before connecting lands on the access role's per-project
  user (measured 2026-10-10, Stage 6h decision 8a; the log heads these entries 2026-10-11 and a later entry
  dates them 2026-10-10). In one run the chained session resolved to
  `IAMR:datazone_usr_role_<project>_<environment>`, which already held `sbx_lab_rw`, wrote a table, and the
  schema's default privilege fired on it (`sbx_lab_rw`, `SELECT`); the direct session in the same run stayed
  per person with no role and failed *"permission denied for schema lab"*. `transitiveTagKeys` read `None`
  on both assumes, so the space's per-person `RedshiftDbUser` session tag does not follow the chain and the
  access role's own tag decides the user. Where: `log-stage-06h-redshift-connection.md`, 2026-10-11 entries;
  `AWS_STATE.md`'s Redshift register. A third door, read 2026-11-16 in Production (Stage 19 step 9): a Glue
  job running as a deployment project's role, whose `GlueJobRunnerSession` carries no session tag,
  connected as `IAMR:user-project@<project id>`, the value of the `RedshiftDbUser` tag DataZone writes on
  the project role. Redshift auto-created that user holding nothing, and the job's `DELETE` failed
  *"permission denied for schema trades"*, while the user granted under the role's name,
  `IAMR:datazone_usr_role_<project>_<environment>`, saw no session; with `gov_trades_rw` granted to the
  auto-created user the next run deleted 30 rows and inserted 10. That name is per project and known
  before the first connection, so it can be created ahead. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-16.

- `SUP-206` **`RedshiftDbUser` decides the database user, and Redshift prefixes its value with `IAMR:`**
  (measured 2026-10-10). The tag on the access role carried the project role's *name*, and the session ran
  as `IAMR:<that name>` — 142 queries attributed to it. The discriminator is that an ignored tag would have
  produced `IAMR:<the access role's own name>`, and it did not. So the documented `IAMR:<role>` spelling
  applies to the tag value, which is not a role at all, and a grant written for the unprefixed value reaches
  nobody. Where: `log-stage-06h` (2026-10-10), `runbooks/redshift-connection.md` §P.

- `SUP-207` **A Redshift connection made in the portal carries `lineageSync` enabled, and the form shows no
  toggle** (read 2026-10-18, Stage 6h). The same-account form of 2026-09-21 offered no lineage field;
  `get-connection` on the connection it wrote reads `lineageSync.enabled: true` on `cron(43 3 * * ? *)` with
  a lineage job of its own, which ran daily from 2026-10-11 and failed eight times. A run that succeeds is a
  scheduled query on the warehouse's meter. Where: `log-stage-06h`, 2026-10-18, and `./aws/warehouse.py`
  `WH-9`. The Glue side carries the sync too (read 2026-10-18, Stage 6f 6.2): `ListConnections` in both
  Sandbox projects returns `project.default_lakehouse` (`LAKEHOUSE`) and `project.iam` (`IAM`) with
  `glueLineageSyncEnabled: true` and no `UpdateConnection` in 90 days of either trail, so the value is the
  creation default, and the `DataLake` blueprint configuration carries no lineage field. The Redshift job's
  runs carry no error text in `list-job-runs`; `get-job-run` first answered `ResourceNotFoundException` for
  every run id, and a second reading the same day returned zero queries processed and a `RedshiftData`
  status 400, *"Redshift endpoint doesn't exist in this region."*, the workgroup being down. CloudTrail
  holds no `GetCredentials` at the run times, so the failed runs opened no database session. Where:
  `log-stage-06f-data-governance.md` and `log-stage-06h-redshift-connection.md`, 2026-10-18. Read again
  2026-11-19 (6h decision 3): `UpdateConnection` with `lineageSync` `enabled: false` and the same schedule
  switched the sync off, the schedule and the `lineageJobId` kept on the object, and `list-job-runs` kept
  the job's 39 runs, one a day from 2026-10-11 to 2026-11-18, each `FAILED`. Where:
  `log-stage-06h-redshift-connection.md`, 2026-11-19. Read again 2026-11-19 at 03:50 UTC: the job created
  no run at the schedule's time, where it had created one at 03:44:44 on each of the 39 days before, so
  `enabled: false` stops the runs while the schedule stays on the object. Where:
  `log-stage-06h-redshift-connection.md`, 2026-11-19.

- `SUP-208` **The SageMaker Unified Studio Query editor opens each session on the Redshift connection's
  database, not on the database selected in an earlier session** (measured 2026-10-26, Stage 9 xxiv). The
  project's connection `redshift-serverless.redshift` names `dev`, the database the portal's compute
  dropdown offered when the connection was made, and keeps it. Sittings of 2026-10-25 and 2026-10-26 had
  `sandbox` selected; the next session sat in `dev` as `IAMR:datazone_usr_role_<project>_<environment>` from
  its first query, and the trail's `GetCredentials` carried `dbName` `dev`. A read of a datashare's table
  through the Data Catalog was then refused: *"Failed to incorporate external table
  "trades"."trades_notional" into local catalog. Error=permission denied to create temporary tables in
  database "dev""*, because the session's database holds the query's temporary objects and the user held
  `TEMP` on `sandbox` alone. Selecting `sandbox` returned the row. Where: `log-stage-09-deployment-targets.md`,
  2026-10-26; `runbooks/redshift-connection.md` §G. Read again 2026-11-19 (6h decision 3): a contributor's
  `UpdateConnection` changed the stored database from `dev` to `sandbox` (`SUP-157`), `jdbcUrl` and
  `jdbcIamUrl` following it and `redshiftTempDir`, whose `dev` segment is the environment's stage, unchanged.
  A session opened on the new database needs the workgroup and is unread. Where:
  `log-stage-06h-redshift-connection.md`, 2026-11-19.

- `SUP-387` **`UpdateConnection` on a Redshift Serverless connection does not check the workgroup it
  names** (measured 2026-11-19, Stage 6h decision 3). The call was accepted at 02:22:20 UTC on
  `redshift-serverless.redshift` with the workgroup `awsds-sandbox-warehouse` destroyed, `GetWorkgroup`
  having answered *"Serverless workgroup awsds-sandbox-warehouse not found."* at 02:11:51, and the object
  read back `READY`, its workgroup and host unchanged and its database `sandbox`. The service model documents
  the call as *"Updates a connection"* and says nothing of validation. A connection's database and lineage
  sync are changed with no warehouse up, and `READY` says nothing about the compute. Where:
  `log-stage-06h-redshift-connection.md`, 2026-11-19; `runbooks/redshift-connection.md` §P step 4a.

- `SUP-390` **The portal's *Create database* refusal names a project-profile setting the profile
  carries** (measured 2026-11-21, Stage 20 2.1). In `app-genai-dev` the portal answered *"Insufficient
  permissions to create a new database. Please add a LakeHouseDatabase blueprint deployment setting with
  On Demand mode to the project profile."* The profile `experimentation` carried `DataLake`, the console's
  `LakeHouseDatabase`, as `ON_DEMAND`; the domain's `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant on it named
  the contributor projects of the project's domain unit; the user owned the project. No call failed: the
  trail holds `GetProjectProfile` and `ListDeployableEnvironmentBlueprints`, a call the CLI does not
  offer, on `app-genai-dev` at each attempt, each answered. The same act then created the database in
  `app-dbt-dev`, with the same profile, unit, environments and owner, after the page was opened on it.
  The page and the project changed together, so the refusal is unattributed, and the message is no
  evidence about the profile: the trail's `projectIdentifier` says which project the portal had open.
  Where: `log-stage-20-dbt-lineage.md`, 2026-11-21.

- `SUP-396` **A native notebook run accepts and records `networkAccessType` `PUBLIC_INTERNET_ONLY`, and its
  compute runs in the domain's VPC regardless** (measured 2026-11-21 in Sandbox, Stage 6d 4.7). From a
  space's terminal as `eighth-experimentation`'s project role, `datazone:StartNotebookRun` with
  `--network-configuration networkAccessType=PUBLIC_INTERNET_ONLY` and no compute answered `QUEUED`; the
  request, the response and every later `GetNotebookRun` carried `PUBLIC_INTERNET_ONLY`. Seventeen seconds
  after the call, `AWSServiceRoleForAmazonSageMakerNotebooks` created the compute's interface through
  `global.workflows.looseleaf.im.amazonaws.com` in the project's private subnet, with its
  `datazone-<project>-dev` group. The kernel called DataZone through the VPC's interface endpoint, and a
  cell opening `https://checkip.amazonaws.com` with no proxy timed out on each of its 8 addresses: `FAILED`,
  *"URLError: <urlopen error timed out>"*. Three runs sent the same day with no network, from the portal's
  *Run in background*, a schedule and a workflow's `SageMakerUnifiedStudioNotebookOperator`, took the same
  subnets and group, and the portal sent the editor's own compute `VPC_ONLY`. The VPC, its subnets and its
  zones are the domain's blueprint configuration's (`sandbox/sagemaker/`). No AWS page read for this
  project states a run's default network or that the domain's VPC overrides the request, so a run's record
  is no evidence of where it ran; its interface is. Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-11-21 (two entries); `threat-model.md`, `TM-34`.

### The Bedrock IDE

- `SUP-410` **The Bedrock IDE creates a knowledge base's S3 Vectors bucket under the project key the Tooling
  configuration carries, and the index is refused unless that key grants `indexing.s3vectors.amazonaws.com`
  `kms:Decrypt`, a statement SMUS's key-permissions page does not name** (measured 2026-11-22 in Sandbox,
  Stage 17 7.4a). The knowledge base was created from the portal's *My components* with Titan Text Embeddings
  V2 at 1024 dimensions and Amazon S3 Vectors. At 01:03:10Z the provisioning role, from
  `datazone.amazonaws.com`, called `CreateVectorBucket` `amazon-bedrock-ide-<project id>-<environment id>`
  with `sseType` `aws:kms` and the key the Tooling configuration alone carries as `KmsKeyArn`; the
  knowledge-base configuration carries no key parameter. The bucket was admitted. `CreateIndex`
  `amazon-bedrock-ide` (1024, `float32`, `euclidean`) was refused: *"AccessDeniedException: Insufficient
  access to perform asynchronous indexing. Ensure that the key used to encrypt the index still exists, is
  active, and has a resource policy granting access to the S3 service principal
  'indexing.s3vectors.amazonaws.com'."* The portal showed it inside *"Amazon Bedrock couldn't deploy the
  Knowledge Base. Delete this component, and then create a new one."* The environment's stack, holding its
  wait handles alone (`SUP-169`), was created and deleted within 35 s. The vector bucket stayed, empty, with
  no index and no tag. Before the stack, `AmazonSageMakerBedrockModelManagementRole` had created an
  application inference profile copied from the embeddings model, which stayed too. The S3 Vectors encryption
  page documents the indexing principal's statement: `kms:Decrypt` under `aws:SourceArn`,
  `aws:SourceAccount` and `kms:EncryptionContextKeys` (`aws:s3vectors:arn`, `aws:s3vectors:resource-id`).
  SMUS's key-permissions page lists ten statements and none for S3 Vectors, a knowledge base or OpenSearch
  Serverless. Bedrock's knowledge-base setup page names no key policy. All three pages were read 2026-11-22.
  A project key written to SMUS's page therefore refuses every IDE knowledge base on S3 Vectors. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-22; `terraform-modules/sagemaker-prereqs/kms.tf`.
  A later reading (2026-11-22, 01:33Z): with the statement in the key's policy (`sagemaker-prereqs-v0.13.0`),
  the second create's `CreateIndex` was admitted. The failed component's row in *My components* carried an
  error icon and no menu; once its blueprint deployment was deleted from *Resource blueprints*, the row
  offered *Delete*. The first vector bucket survived both deletes, empty.

- `SUP-411` **The Bedrock IDE's S3 Vectors index declares `AMAZON_BEDROCK_TEXT` alone non-filterable, where
  Bedrock's pages add `AMAZON_BEDROCK_METADATA`, and ingestion then fails on S3 Vectors' 2 KB cap on a
  filterable string with a per-document reason that names no metadata** (measured 2026-11-22 in Sandbox,
  Stage 17 7.4a). The index `amazon-bedrock-ide` the provisioning role created at 01:33:17Z read
  `nonFilterableMetadataKeys` `AMAZON_BEDROCK_TEXT` and `indexMode` `ENHANCED`; the knowledge-base form
  exposes no index setting. Bedrock's knowledge-base setup page (its S3 Vectors tab) and its chunking page
  say to add `AMAZON_BEDROCK_TEXT` and `AMAZON_BEDROCK_METADATA` as non-filterable keys. S3 Vectors' limits
  page caps each filterable string value at 2 KB, and its metadata-filtering page says non-filterable keys
  are configured when the index is created. Over 20 Markdown runbooks with the form's default chunking
  (fixed size, 300 tokens, 15 % overlap), the sync the create started indexed 2 and failed 18. A second
  sync scanned 20, indexed none and failed 18, counting the other 2 in no statistic. Both jobs' reason
  read *"Invalid record for key '<uuid>': Metadata value is invalid: exceeds 2048 byte string limit
  (Service: S3Vectors, Status Code: 400 …)"*, and each failed document's `statusReason` read *"The document
  was not indexed. No content could be extracted from it, or processing ended before it completed."*
  Neither reading names the key that exceeded. The two indexed runbooks hold one Markdown table each and
  the 18 others two or more, a correlation read from the files, not a cause. A knowledge base the IDE
  creates on S3 Vectors keeps this index for its life. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-11-22.

- `SUP-417` **The Bedrock IDE's guardrail is created by DataZone as the provisioning role under the project
  key, and Bedrock refuses it unless that role may `kms:CreateGrant` on the key, which SMUS's key-permissions
  page does not name** (measured 2026-11-22 in Sandbox, Stage 17 7.4). The guardrail was created from the
  portal's *My components* → *Create component* → *Guardrail* with one denied topic. At 01:56:24Z
  `CreateGuardrail`, called from `datazone.amazonaws.com` as `awsds-sandbox-smus-provisioning` (session
  `AmazonDataZoneEnvironmentDeployer-<account>`), was refused with *"You don't have sufficient permissions
  for this KMS key."*, and in the same second `kms:CreateGrant` on the project key was refused: *"… is not
  authorized to perform: kms:CreateGrant on resource: arn:aws:kms:us-west-2:<account>:key/<project key> because
  no identity-based policy allows the kms:CreateGrant action"*. Both events carry `datazone.amazonaws.com` as
  source and user agent, and the grant's event no request parameters. The role's managed policy allows
  `kms:CreateGrant` through `airflow`, `neptune-graph` and `s3vectors` alone, and the key's policy allowed it
  to the role through `redshift-serverless` alone. The environment's stack, created at 01:56:20Z, was rolled
  back to `DELETE_COMPLETE`, and the environment read `CREATE_FAILED` with *"Access denied for operation
  'AWS::Bedrock::Guardrail'."* (`HandlerErrorCode: AccessDenied`): CloudFormation's handler made the call, and
  the trail attributes it to DataZone. Bedrock's guardrail encryption page lists, for the creating identity,
  `kms:Decrypt`, `kms:GenerateDataKey`, `kms:DescribeKey` and `kms:CreateGrant` with no condition (read
  2026-11-22); SMUS's key-permissions page names no guardrail statement. A project key written to SMUS's page
  therefore refuses every IDE guardrail. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22;
  `terraform-modules/sagemaker-prereqs/kms.tf`.
  A later reading (2026-11-22, 02:45Z): with the statement in the key's policy (`sagemaker-prereqs-v0.14.0`),
  `CreateGuardrail` was admitted as the same role, and in the same second three `kms:CreateGrant` on the key,
  each naming `bedrock.us-west-2.amazonaws.com` as grantee and retiring principal. Two are bound to the
  encryption context `aws:bedrock:guardrail-id`; the third carries no constraint and allows `Decrypt`,
  `Encrypt`, `GenerateDataKey`, `CreateGrant`, `RetireGrant` and `DescribeKey`. The guardrail therefore left on
  the project key a grant to Bedrock that no guardrail id bounds.

- `SUP-418` **The Bedrock IDE's evaluation form sends `temperature` and `top_p` together, which Claude Haiku
  4.5 refuses, so the IDE did not evaluate it; the portal reports an unknown error** (measured 2026-11-22 in
  Sandbox, Stage 17 7.4). The form's *Inference configurations* panel holds Max tokens 500, Temperature 0.5,
  Top P 0.5 and Top K 50 by default, and a cleared Top P returns to 0.5. Its model list offered Nova Lite,
  Claude Haiku 4.5, Claude Opus 4.5 and Claude Sonnet 4.5; Opus 4.5 and Sonnet 4.5 were not submitted. With
  Haiku 4.5, Question and answer and Toxicity over a 20-line custom dataset, DataZone created the evaluation
  environment, whose stack holds an output and no resource. At 02:07:54Z Bedrock's pre-flight `Converse`, as
  the project's `AmazonBedrockServiceRole-*` on the application inference profile, was refused: *"The model
  returned the following errors: `temperature` and `top_p` cannot both be specified for this model. Please use
  only one."*, and `CreateEvaluationJob`, as the project role, with *"There was a validation exception when
  running inference for model identifier
  arn:aws:bedrock:us-west-2:<account>:application-inference-profile/<id>. Please review the error and retry:
  …"* and the same reason. The trail's `Converse` event shows `inferenceConfig` holding `maxTokens` 1 alone,
  and the job's `inferenceParams` read `HIDDEN_DUE_TO_SECURITY_REASONS`. The portal read *"An error occurred
  while creating the evaluation job: Unknown error. Potentially invalid input"*, and no evaluation job exists.
  The environment stayed `ACTIVE`.
  The prompt editor drops Top P instead: its form at Temperature 1 and Top P 0 stored, in both versions of the
  prompt, `inferenceConfiguration` `temperature` 1.0, `maxTokens` 4096 and `stopSequences` `Human:`, with no
  `topP`, and its test of Haiku 4.5 was admitted (`ConverseStream` at 01:48:24Z as the project role). The trail
  shows `maxTokens` alone for every call, so the stored prompt is what tells the two forms apart. SMUS's
  job-creation page says *"You can change Max tokens, temperature, and Top P inference parameters"* and names
  no model they exclude (read 2026-11-22). Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.
  A later reading (2026-11-22, 02:52Z): with Nova Lite and the same task, metric and dataset,
  `CreateEvaluationJob` was admitted. Nova Lite's panel held Max tokens 500, Temperature 0.5 and Top P 0.5,
  with no Top K, and was closed with no change. `GetEvaluationJob` reads the job's `inferenceParams` as
  `maxTokens` 2048, `temperature` 0, `topP` 0 and no stop sequence: the form's *Default* sends values its panel
  does not show, both sampling parameters among them, and `GetEvaluationJob` shows what the trail hides.

- `SUP-419` **The Bedrock IDE's evaluation form refuses a custom dataset for Accuracy and Robustness under
  Question and answer, where SMUS's pages say every metric takes one** (measured 2026-11-22 in Sandbox, Stage 17
  7.4). With the task *Question and answer* and the metric Accuracy or Robustness, the form greys out *Upload a
  dataset to S3* and *Choose a dataset from S3*, reads *"Custom datasets are not supported for Q&A task type with
  robustness or accuracy metrics"*, and leaves the built-in BoolQ, Natural Questions and Trivia QA checked.
  Toxicity takes the upload. SMUS's custom-dataset page says *"you can use a custom prompt dataset for each
  metric you select in the model evaluation job"* and requires `referenceResponse` *"for all accuracy, and
  robustness evaluations"*; its job-creation page offers, *"For each metric"*, the built-in or an S3 dataset
  (both read 2026-11-22). A question-and-answer dataset of one's own is therefore scored for toxicity alone.
  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-445` **The Bedrock IDE keeps a component's portal name in its DataZone environment's description, and
  names the environment and the Bedrock resource after ids** (read 2026-11-22 in Sandbox, Stage 17 7.4). Each
  component is an environment whose description is JSON, `{"resourceId":"<component uuid>","resourceName":"<the
  portal's name>","resourceDescription":"<the form's description>"}`, and whose name is `<component uuid>-dev`;
  the portal's URL carries the uuid (`/bedrock/prompts/<uuid>`, `/bedrock/promptFlows/<uuid>`). The Bedrock
  resource's name is `Bedrock-Prompt-<environment id>` or `Bedrock-Flow-<environment id>`, its description names
  the project and the domain, and the flow carries the tags `AmazonDataZoneProject`, `AmazonDataZoneEnvironment`,
  `AmazonDataZoneBlueprint`, `AmazonDataZoneDomain` and `AmazonBedrockManaged`. A knowledge base is named
  `<project id>-<portal name>`. An evaluation's environment and job are both named `<project id><portal name>`,
  with no separator and no description. No SMUS page describes the mapping, so a reader that lists Bedrock's
  objects finds none under the name the portal shows. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-11-22.
  A later reading (2026-11-22, 02:45Z to 02:52Z): the guardrail is named after its environment,
  `<component uuid>-dev`, and carries the flow's five tags, `AmazonDataZoneBlueprint` reading
  `AmazonBedrockGuardrail`. The project holds one application inference profile per model its components
  used, each created by `AmazonSageMakerBedrockModelManagementRole-<account>` at the model's first use and
  named `<domain id> <project id>`: its four, for an embeddings model, Claude Opus 4.5, Claude Haiku 4.5 and
  Nova Lite, share that name, and the domain's two from the playground share `<domain id>` (`SUP-187`). Nova
  Lite's was created at the evaluation's submit, 4 s before its environment.
  A later reading (2026-11-22, 08:21Z to 08:25Z, `app-genai-dev`): a project's first use of a model is its
  subscription to the model's listing. A playground call went through the domain's profile and wrote nothing
  in the project; an unsaved *Run* in the prompt builder sent `CreateSubscriptionRequest` as the domain
  execution role, accepted at creation, and the role above created the project's profile 4 s later in an
  `AWSDataZone-Subscriptions` session, with no environment. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-11-22.

- `SUP-446` **The Bedrock IDE's chat agent app is an Agents Classic agent: its preview calls `InvokeInlineAgent`
  and its deploy `CreateAgent`, both refused for an account with no prior agent use, and the portal shows
  neither refusal's wording** (measured 2026-11-22 in Sandbox, Stage 17 7.4b). *Save* writes the app's
  definition to the project's bucket, `amazon-bedrock/builder/apps/chatApp/<uuid>-definition.json`, and creates
  no environment and no agent. The definition names the model by a catalog listing revision, `<listing id>:2`,
  whose `BedrockModelAssetType` asset has the `us.` system profile as its base, names the knowledge base and the
  guardrail by component uuid, and holds `temperature`, `topK` and `maxTokens` with no `topP`. Each *Preview*
  message sent `POST bedrock-agent-runtime.us-west-2.amazonaws.com/agents/<session id>` from the browser,
  answered 403 with *"Bedrock Agents is in Maintenance Mode. New agent creation is not available for accounts
  without prior service usage."*; the portal read *"Failed to run application Amazon Bedrock encountered an
  error when invoking the Bedrock runtime API. Try again later."* and *"Something went wrong."*. *Deploy*
  created a DataZone environment `<uuid>-shared` of the `AmazonBedrockChatAgent` blueprint, and its stack's
  `CreateAgent`, as the provisioning role from `datazone.amazonaws.com`, on the project's application inference
  profile with the project key and the guardrail's `DRAFT`, was refused `AccessDenied` with no error message
  in the trail and no KMS call; the environment read `CREATE_FAILED` with *"Access denied for operation
  'AWS::Bedrock::Agent'."*. The IAM simulator, with resource `*`, reads `bedrock:CreateAgent` allowed for that
  role by `SageMakerStudioProjectProvisioningRolePolicy` and the SCPs under the request's tags, so the refusal
  is Bedrock's own, and its wording reaches the browser on `InvokeInlineAgent` alone. The builder's banner
  dates Agents Classic's closing to new customers, July 30, 2026, and names no refusal of its own calls.
  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-447` **The Bedrock IDE's flow environment always creates a role of its own, and creates it with no
  permissions boundary: the blueprint configuration's `environmentRolePermissionBoundary` does not reach it,
  and the flow runs as the project's service role instead** (read 2026-11-22 in Sandbox, Stage 17 7.5). The
  stack of a flow app's environment declares `AWS::IAM::Role` with no condition, named
  `AmazonBedrockFlowServiceRole-<environment id>`. The environment passed the stack parameter
  `useAwsManagedPoliciesWithoutBoundary` `true`, which gives the role AWS's
  `SageMakerStudioBedrockFlowServiceRolePolicy` and no boundary; `false` gives it inline policies under AWS's
  `SageMakerStudioProjectUserRolePermissionsBoundary`. Neither branch reads the boundary the
  `AmazonBedrockFlow` blueprint configuration names, `awsds-sandbox-project-boundary` here, and the template
  takes no parameter for it. The provisioning role's `CreateRole`, from `datazone.amazonaws.com`, named no
  `permissionsBoundary`. The flow's `ExecutionRoleArn` is the new role only when `bedrockServiceRoleArn` is
  empty; the environment passed the project's `AmazonBedrockServiceRole-*`, so the flow ran as that bounded
  role and the new one reads no `RoleLastUsed`. Its trust admits `bedrock.amazonaws.com` for this account's
  flows alone, its policy names only the project's Bedrock objects by tag, models through an inference
  profile, `RetrieveAndGenerate` on `*` and the project key through Bedrock, and the project role may not pass
  it (`iam:PassRole` `implicitDeny` in the simulator). No SMUS page read for this project describes the role,
  the flow app pages read on 2026-11-22 included. A check that every blueprint-authored role carries the
  boundary fails on each flow app's environment. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-11-22.

- `SUP-448` **The Bedrock IDE's flow builder deploys a flow on each test message and never on *Save*, and
  offers a flow app no *Share*** (measured 2026-11-22 in Sandbox, Stage 17 7.4b). `ml-demo-flow` was edited to
  carry a knowledge base node. *Save* read *"Saved"* and wrote the four-node definition to the project's
  bucket, `amazon-bedrock/builder/apps/flowApp/<uuid>-definition.json`, and `GetFlow` still read the two-node
  flow prepared two hours before. The first test message ran a PUT of the asset `genAI/assets/flows/<uuid>`,
  DataZone's `UpdateEnvironment`, a PUT of the environment's `definition.json` and the update of the stack
  `DataZone-Env-<environment id>` (04:25:26Z to 04:25:36Z), whose `UpdateFlow` and `PrepareFlow` ran as the
  provisioning role from `datazone.amazonaws.com`, before the browser's `InvokeFlow` on `TSTALIASID`
  (04:25:49Z). Each of the three later messages, with no edit between them, updated the stack again (the stack
  from 04:26:50Z to 04:27:01Z, then `UpdateFlow` at 04:28:33Z and at 04:30:29Z), and a message took 70 to
  80 s from the send to the answer. The
  stack updated `BedrockFlow` alone. *My apps* lists the flow *"Not shared"*, with a delete icon alone. AWS's
  flow app pages say *Save* saves the app and the run button tests it, and its share page describes chat agent
  apps alone (`build-flow.html`, `app-share.html`, read 2026-11-22). A flow saved and never tested therefore
  runs its previous definition, a `GetFlow` after *Save* reads the edit as lost, and every test is a stack
  update as the provisioning role. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22;
  `runbooks/bedrock-generative-ai.md` §B.

- `SUP-452` **Opening the portal's domain-level *Playground* subscribes the signed-in user to its default
  model's inference-only listing, twice, with no approval** (measured 2026-11-22 in Data Governance, Stage
  19 xxvi). The Governance Manager User, a member of `deploy-production` under a custom designation that
  withholds `CreateSubscriptionRequest`, opened *Playground* (`/bedrock/playground/explorer`) from the side
  menu and clicked nothing else. At 13:44:38.941Z and 13:44:39.531Z the portal sent two
  `CreateSubscriptionRequest` as the domain execution role in the user's session, the user the subscribed
  principal, on Claude Haiku 4.5's listing of `BedrockInferenceOnlyAssetType`, owned by
  `GenerativeAIModelGovernanceProject`. Both requests read `ACCEPTED` at creation with no reviewer, each made
  an `APPROVED` subscription, and the two share one grant, `COMPLETED` 0.8 s after its creation, with no
  subscription target. No model was invoked and no Bedrock or IAM write followed. The project's designation
  did not apply, the principal being the user rather than a project. The Data Scientist User holds the same
  pair on that listing since 2026-10-19 at 21:12:18Z, the day of Stage 17 7.3's first playground calls
  (`SUP-300`). A model listing's subscribers therefore name every person who has opened the playground.
  AWS's pages were not read for this behaviour. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-22.

## SageMaker AI spaces and images

### Custom images and their versions

- `SUP-209` **An app image configuration's environment caps each value at 256 characters, and no BYOI page
  says so** (measured 2026-09-10, 6d step 2.2). `CreateAppImageConfig` refused this estate's six proxy
  variables with `ValidationException … Member must have length less than or equal to 256`; the cap is in
  the `ContainerConfig` API reference (25 entries, 256 per key and per value) and nowhere on the pages that
  recommend `ContainerEnvironmentVariables` as the way to configure a custom image. A generated `NO_PROXY` —
  50 endpoint names, 1,442 characters — does not fit, so the documented mechanism cannot deliver the
  estate's own proxy contract. Where: `runbooks/dev-env.md` §E, and 6d decision due 8.

- `SUP-210` **`CreateImageVersion` uses the image's `RoleArn` to read the repository, and resolves the tag
  to a digest once** (measured 2026-09-10, 6d step 2.1). The role is documented as *"a role that enables
  SageMaker to perform tasks on your behalf"* with a console hint to attach `AmazonSageMakerFullAccess`, and
  what it actually does is `BatchGetImage` + `GetDownloadUrlForLayer` in the registry account — visible in
  that account's CloudTrail as `userIdentity.type AWSAccount`, principal `<role-id>:SageMaker`, from an
  AWS-internal address. Four ECR read actions are enough. The version's `ContainerImage` then names a
  `sha256:` digest, so a registered version is pinned to bytes rather than to a tag, and re-tagging upstream
  would not move it. Where: `runbooks/dev-env.md` §C5.

- `SUP-211` **A SageMaker Unified Studio space takes its custom image from the domain's
  `DefaultUserSettings`, and `DefaultSpaceSettings` needs no `CustomImages`** (measured 2026-09-10, Stage 6d
  2.3). After `update-domain` put version 1 into `JupyterLabAppSettings.CustomImages` and
  `CodeEditorAppSettings.CustomImages` of `DefaultUserSettings`, with `DefaultSpaceSettings` read in the
  same minute holding no `CustomImages` and no `CodeEditorAppSettings`, a JupyterLab space and a Code Editor
  space created from the portal both started on the image. A space's own
  `SpaceSettings.CodeEditorAppSettings` has neither `CustomImages` nor `LifecycleConfigArns`, so the
  picker's offer is decided on the domain alone. An entry with no `ImageVersionNumber` offers every version,
  newest first, and a version created later appears with no domain write (2026-10-15). One image served both
  app types here, a reading about this image rather than about every custom image. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-10/11; `log-stage-08-cicd-pipelines.md`, 2026-10-15;
  `runbooks/dev-env.md`.

- `SUP-212` **`UpdateDomain` does not clear a list you leave out; it clears one you send empty** (measured
  2026-09-11, 6d step 2's first version bump). The API is treated as a full replace of `DefaultUserSettings`
  — and a block sent without `JupyterLabAppSettings.CustomImages` left both attachments exactly as they
  were, so "omitted" read as "unchanged" rather than as "deleted". The vendor says the form in the detach
  page and nowhere near the attach page: *"you will need to leave `CustomImages` blank, such that
  `"CustomImages": []`"*. What survives of Lesson 60 here is the discipline, not the mechanism: send the
  block back as read, and clear a list explicitly. Where: `runbooks/dev-env.md` §C6 and §X step 1.

- `SUP-213` **A SageMaker space keeps its own copy of the custom image version number**, in
  `SpaceSettings.<app>AppSettings.DefaultResourceSpec`, written when the space is created — and it overrides
  the domain's `DefaultUserSettings`. Measured 2026-09-12: with version 4 attached to the domain, an
  existing space still named version 3, which the same apply had destroyed (`aws_sagemaker_image_version` is
  force-new on `base_image`). AWS's own images are referenced by a mutable alias instead, which survives a
  bump. An app started against the destroyed version fails to start rather than falling back (measured the
  same evening). Where: `dev-env.md` §B, *Moving a space*, `AWS_STATE.md` `EXC-09`, Lesson 63. Measured
  2026-10-15 on a probe image: `delete-image-version` of a version that a space's spec named while its app
  ran was accepted and the version was gone within 5 s, the domain `InService` with no `FailureReason`; the
  app stayed `InService` on the deleted version, so the stranding shows only at the space's next start. An
  `ARCHIVED` version still starts the space that names it and stays in the portal's picker, which a deleted
  version leaves. A space whose spec names an alias follows the alias to its new version at its next start.
  Moving a space with `update-space` and the live `SpaceSettings` kept the idle settings, the volume,
  `RemoteAccess` and the S3 mount, and dropped `SpaceManagedResources: ENABLED`, sent with the block, from
  the read (once, on a probe space); the portal's route kept `RemoteAccess`, the EBS size and the S3
  connection (2026-09-12). Where: `log-stage-08-cicd-pipelines.md`, 2026-10-15; `AWS_STATE.md` `EXC-09`.

- `SUP-214` **`describe-app` still returns the `ResourceSpec` of an app that has been deleted** (measured
  2026-09-12), so the image a removed space ran can be attributed after the fact. A space deleted within the
  hour read `sagemaker-distribution-cpu`, alias `4.3`, with `Status: Deleted` — the evidence that it had
  been created on AWS's image rather than this estate's, which is what its missing proxy variables had
  looked like a defect of. Where: `dev-env.md` §C7.

- `SUP-215` **`UpdateDomain` changes `CustomImages` with apps running, whatever the vendor's page says**
  (measured 2026-10-15 on a probe image, Stage 8 decision 7). The detach page reads *"Before you can update
  the custom images, you must delete all of the applications in your domain"*, and four `update-domain`
  calls changing the list were accepted with apps `InService`, one removing an entry while two apps ran on
  that image. Each read back identical, and the running apps were untouched. Where: `dev-env.md` §C6.

- `SUP-216` **A `CustomImage` with no `ImageVersionNumber` offers every version of the image** (measured
  2026-10-15). The portal's picker listed each version, newest first, as `<display name> v<n>`, including
  one created after the attach and one no space named, and the portal's `CreateSpace` pinned the chosen
  version's ARN into the new space. The API reference says only that the field is optional. Where:
  `dev-env.md` §C6 and §B.

- `SUP-217` **`VendorGuidance ARCHIVED` hides nothing from the portal, and an archived version still
  starts** (measured 2026-10-15). With a version `TO_BE_ARCHIVED` and then `ARCHIVED`, the picker kept
  offering it under the same label, `list-image-versions` kept listing it, and a space pinned to it started
  and pulled it by digest. Deleting it is what took it out of the picker. Where: `dev-env.md` §B, *The
  retirement*.

- `SUP-218` **A custom image's alias works in a space's spec, and the portal reads it as the SageMaker
  Distribution's** (measured 2026-10-15). `update-space` accepted `SageMakerImageVersionAlias` with the
  version ARN cleared by `"None"`; the app resolved the alias at each start and followed it to another
  version; and the portal then bannered the space as running an *outdated SageMaker Distribution image*. The
  same `update-space`, sent the whole live block, left `SpaceManagedResources: ENABLED` out of the read
  afterwards. Where: `dev-env.md` §B, *Moving a space*.

### Spaces and apps

- `SUP-219` **A `VpcOnly` space started with no interface endpoints does not fail; it hangs, with a working
  terminal** (measured 2026-09-07, 6c step 6.2, the first space under design B). JupyterLab loaded, the
  terminal answered, the banner *"IDE configuration in progress"* never cleared and a Python kernel never
  returned: the app's DataZone and SageMaker calls had no route and no endpoint, so they got silence rather
  than a denial (Lesson 42), and nothing in the UI said network. The vendor's pages list the endpoints as
  required and say nothing about what their absence looks like. `make up ENV=sandbox` plus a stop/start of
  the space cleared it. The discriminator from inside the space is `getent hosts
  sts.us-west-2.amazonaws.com` (`10.20.x.x` with the endpoints, public without) and `curl` to the same name
  (`302` against a timeout). Where: `docs/SMUS.md` §`VpcOnly`, the client runbook §1, the 6c log.

- `SUP-220` **Inside a SageMaker space the container reports a link-local address, while the network sees
  the app's ENI address, which changes when the app restarts** (measured 2026-09-08, 2026-09-19 and
  2026-10-11, Stage 6d and Stage 6h 3.3). `hostname -I` in a space printed `169.255.255.2` while the proxy
  logged every one of its requests from `10.20.126.1`. A connection to the Redshift Serverless workgroup
  read `169.255.254.3 -> 10.20.53.13:5439`, and the workgroup's security group rule naming the project's own
  group admitted it, so the packet arrives as the ENI carrying that group. A restart of one space moved its
  proxy-log address from `10.20.102.237` to `10.20.79.130`. A space is matched to a proxy or flow log line
  by time window, never by the address it reports. Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-09-08 and 2026-09-19; `log-stage-06h-redshift-connection.md`, 2026-10-11;
  `runbooks/log-debugging.md`.

- `SUP-221` **SageMaker idle shutdown appears in CloudTrail as `DeleteApp` by
  `AWSServiceRoleForAmazonSageMakerNotebooks`, through `global.workflows.looseleaf.im.amazonaws.com`** (read
  2026-09-09 and 2026-10-17 in Sandbox's trail, Stage 6d 5.1). On 2026-09-09 that role deleted a JupyterLab
  app at 20:40:30 and a Code Editor app at 20:47:20, `FailureReason` null, the Code Editor app having run 63
  minutes. From 2026-09-12 to 2026-10-17 it deleted 23 apps; on 2026-10-16 it accounted for 7 of the 12 apps
  deleted, the project roles from the portal for 3 and the teardown script for 2. The same call from a
  browser `userAgent` under the project role is a person. A deletion time is not the length of the idle
  interval, so the threshold stays unmeasured. Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-09-09, 2026-10-17 and 2026-10-18; `runbooks/log-debugging.md`.

- `SUP-222` **A space's `~/shared/` writes a zero-byte folder marker for every directory** (measured
  2026-10-11, Stage 6i step 3.6). A `cp -r` of a 176-file folder left 192 objects, 16 of them `…/` keys, and
  a `mkdir` leaves `inbox/`, which a sensor's `inbox/*` matches before any file lands. A processing input
  downloads such a prefix without complaint. Where: `runbooks/serverless-workflows.md` §A and §J1.

- `SUP-223` **Opening a project's *Spaces* page in the portal starts its default space** (read 2026-10-15).
  CloudTrail recorded a `CreateApp` on the default space, by the project role in the data scientist's portal
  session and on AWS's distribution by alias, as the page loaded, and the app ran until its idle shutdown.
  Where: `dev-env.md` §C7.

- `SUP-224` **When a space is created, SageMaker starts its first app itself with an empty `resourceSpec`,
  so `sagemaker:ImageArns` can be absent at `CreateApp`** (read 2026-10-17 in Sandbox's trail, Stage 6d
  decision 13). Of 113 `CreateApp` events since 2026-09-12, 26 carried `invokedBy: sagemaker.amazonaws.com`
  and `resourceSpec` `{}`, and the space's own spec applied. The other 87 were a person's start through the
  portal or the Toolkit: 56 on AWS's `sagemaker-distribution-cpu` named by an alias (`4.3`, later `4.5`),
  never by a version ARN, and 31 on a custom image, mostly by version ARN. A deny keyed on
  `sagemaker:ImageArns` at `CreateApp` meets an absent key on one start in four and needs a `Null` case;
  whether the key is published at request time was not measured. The shape recurred on 2026-10-15 and
  2026-10-30. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-10-17 and 2026-10-30;
  `log-stage-08-cicd-pipelines.md`, 2026-10-15; `threat-model.md` `TM-10`.

- `SUP-225` **SMUS's Query editor creates the project space's JupyterLab app on opening, beside its own
  `sqlworkbench` session, and the app sits in `PendingCheckout`, a state `DeleteApp` cannot take to
  `Deleting`** (measured 2026-10-26, 01:26 to 01:37 UTC, the Stage 9 session's warehouse sitting). The query
  ran without the app; `make down ENV=sandbox` minutes later met the app in `PendingCheckout`
  (`ValidationException`) and the Studio-apps hook stopped the down twice, until the user closed the editor,
  the portal stopped polling at 01:36:20 and `DeleteApp` went through at 01:37:03. Where:
  `log-stage-09-deployment-targets.md`, 2026-10-26.

- `SUP-226` **A space's home `.gitconfig` names the CodeCommit credential helper for every host** (measured
  2026-10-26, Stage 7 xi). `credential.helper !aws codecommit credential-helper --ignore-host-check $@` with
  `credential.usehttppath true` sits in `/home/sagemaker-user/.gitconfig`: a clone of any HTTPS remote sends
  that helper's credential, GitLab answers *"HTTP Basic: Access denied"*, and git never prompts for a token.
  `-c credential.helper=` resets the list for one command. Where: `log-stage-07-gitlab-runners-ecr.md`,
  2026-10-26.

- `SUP-227` **The SageMaker Distribution's own `aws-smus-cicd-cli` comes first on a space's `PATH`**
  (measured 2026-10-26, Stage 10 2.1). In a house-image space, `type -a` reads
  `/opt/conda/bin/aws-smus-cicd-cli`, 1.0.8, ahead of the house environment's 1.0.9; the 1.0.8 refuses a
  manifest whose `content.workflows[]` carries `code`. Where: `log-stage-10-orchestration-promotion.md`,
  2026-10-26.

- `SUP-228` **A space's `PATH` is the base environment's activation, not the image's `ENV`** (read
  2026-10-26 in the SageMaker Distribution 4.5.2's start scripts and libmamba's activation, not measured in
  a space). `entrypoint-sagemaker-ui-jupyter-server`, `start-sagemaker-ui-jupyter-server` and the Code
  Editor's pair each run `micromamba activate base` before their server, and libmamba puts the environment's
  `bin` first on activation and on reactivation removes it from wherever it was and puts it first again; the
  server's terminal (`shell_command: ["/bin/bash"]`) inherits that `PATH`. A directory an image places ahead
  of `/opt/conda/bin` reaches only what runs without the activation: a descendant's Dockerfile `RUN`, which
  `_dockerfile_shell.sh` runs unactivated, and a job's `ContainerEntrypoint`. The base environment's
  `etc/conda/activate.d/*.sh` run after the activation exports `PATH`. Where:
  `log-stage-08-cicd-pipelines.md`, 2026-10-26.

- `SUP-229` **An app's `CreationTime` is the first `CreateApp` under its name, kept across a restart and
  across its space deleted and made again under the same name** (measured 2026-10-26 and 2026-11-21).
  Both `default` spaces' apps read `CreationTime` 2026-10-25 05:40 UTC while CloudTrail's `CreateApp`
  started them at 04:45 and 05:31 UTC on 2026-10-26: an app's age is read from `CreateApp`. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-26. **2026-11-21**: `code` in `d-m8m0uefej9kb` was
  created at 03:54:10, shut down idle at 05:04:31, its space deleted at 18:34:05 and made again at 20:08:41,
  and its `CreateApp` ran at 20:08:46; `describe-app` and `list-apps` still read 03:54:10. Three restarts
  inside one space read their first `CreateApp` too. The DescribeApp reference states the rule on
  `CreationTime` (an application restarted within 24 hours of its last shutdown is an update and keeps its
  metadata); ListApps's `AppDetails`, the shape of each app `list-apps` returns, says only *"The creation time."*, and
  neither page names a space made again. `scripts/slices.py status` billed `code` *"about 1.74 USD so far
  since 2026-11-21 03:54 UTC"* for a run of about 0.12 USD; it now bills from the later of the app's and
  the space's `CreationTime` and prints an upper bound, since a restart inside one space keeps the first
  time. Where: `log-stage-12-observability-finops.md`, 2026-11-21.

- `SUP-230` **An open portal page starts its project's space app again after `make down` deleted it**
  (measured 2026-10-26). The Studio-apps hook deleted both projects' apps at 06:10 UTC; the persona's open
  portal tabs created them again at 06:13 (`CreateApp`, a browser `userAgent`, each project's role), and
  `DeleteApp` refused the one still starting eight times from 06:21:58 to 06:25:04, *"State transition from
  [PendingCheckout] to [Deleting] is not allowed."*, until it went through at 06:26:12 with every tab
  closed. The Query editor's case is `SUP-225`. Where: `log-stage-07-gitlab-runners-ecr.md`, 2026-10-26.

- `SUP-231` **The portal deletes a project's default JupyterLab space** (measured 2026-10-30). Sandbox's
  trail holds `DeleteSpace` of `default-<user profile id>` in `eighth-experimentation`'s domain at 03:49:33
  UTC, by the project role from a browser, with no error, while the code spaces page read the same day says
  *"You cannot delete the default JupyterLab space"*. Opening that project's *Code spaces* page recreated
  the space (`CreateSpace` by the project role from a browser, 06:44:45 UTC) and the service started its
  app. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-10-30.

- `SUP-450` **A SageMaker Unified Studio JupyterLab app calls `cognito-identity.us-east-1.amazonaws.com`
  and `client-telemetry.us-east-1.amazonaws.com` every few seconds while it runs, and the idle shutdown does
  not count the calls as activity** (measured 2026-11-21 in Sandbox's proxy log, Stage 17 sitting B). From
  the space `jup`, JupyterLab on `ml.t3.medium`, the proxy logged a pair of tunnels every 2.5 to 2.6 s, each
  pair the same sizes: *"CONNECT cognito-identity.us-east-1.amazonaws.com:443 200 8072 2932 TCP_TUNNEL"* and
  *"CONNECT client-telemetry.us-east-1.amazonaws.com:443 200 5605 3637 TCP_TUNNEL"*. The app's address sent
  1,529 pairs from 20:17:53Z to 21:23:15Z, from its UI's first minutes to its idle delete at 21:23:14Z
  (`SUP-221`, the domain's `IdleTimeoutInMinutes` 60), and the restarted app's new address sent them again
  from 23:07:53Z. About 6.6 KB leave per pair, 9.2 MB an hour per running JupyterLab app, and 19 MB arrive.
  The pair passes the compute plane's `.amazonaws.com` allowance. A Code Editor space sent it once per app
  start (6d's log; `SUP-233`), and `app-etl-dev`'s JupyterLab space `default` about 300 of each in 20
  minutes on 2026-11-15. The sending component was not identified. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-21; `log-stage-12-observability-finops.md`,
  2026-11-21; `log-stage-19-smus-native-data-product.md`, 2026-11-15.

### The Code Editor and the remote IDE

- `SUP-232` **The SageMaker Code Editor's extension gallery client reads `http_proxy`/`https_proxy` from the
  server's environment and ignores the `http.proxy` setting, which the rest of the IDE honours** (measured
  2026-09-08 and 2026-09-09, Stage 6d 8.4). With the setting in User Settings, a restart moved
  `idetoolkits.amazonwebservices.com`, `api.github.com` and `raw.githubusercontent.com` from DNS blocks to
  proxy answers and `pypi.org` to `200` (98 proxied requests, 96 MiB), while `open-vsx.org` stayed at 24 DNS
  blocks with no proxy-log line. `code-editor-server --install-extension`, run with the proxy variables
  exported and `VSCODE_IPC_HOOK_CLI` unset, connected and got the proxy's HTTP `403`; with that variable
  set, the call is forwarded into the running server and measures its environment. The terminal reads
  `SUPERVISOR_PROCESS_NAME=codeeditorserver`: the server is a supervisord program, so a variable has to
  reach that program, not a login shell. `open-vsx.org` serves the API and `openvsx.eclipsecontent.org` the
  `.vsix` bytes. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-08 and 2026-09-09;
  `runbooks/sg-proxy.md`.

- `SUP-233` **The Code Editor's AWS Toolkit calls hosts outside `amazonaws.com` and hosts with no VPC
  endpoint at every start** (measured 2026-09-08, 2026-09-09 and 2026-09-11, Stage 6d 8.2 and 8.6). A space
  with no internet path logged 20 DNS blocks for `idetoolkits.amazonwebservices.com` while its sibling
  `idetoolkits-hostedfiles.amazonaws.com` was allowed: one feature, two registrable domains, and a
  `.amazonaws.com` allowance covers one. Behind the proxy the IDE also reached
  `ide-toolkits.app-composer.aws.dev` and `sagemaker-unified-studio-mcp.us-west-2.api.aws`, none of the
  three with a VPC endpoint, and `aws-language-servers.us-east-1.amazonaws.com` (52.4 MiB in two requests
  per app start), `cognito-identity.us-east-1.amazonaws.com` and `idetoolkits-hostedfiles.amazonaws.com`,
  public calls through a `.amazonaws.com` entry. VS Code telemetry to `mobile.events.data.microsoft.com` and
  `*.in.applicationinsights.azure.com` is requested as well. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-08, 2026-09-09 and 2026-09-11.

- `SUP-234` **A remote IDE session's `sagemaker:StartSession` is made from the laptop as the SageMaker
  Unified Studio project role, not as the person's permission set** (read 2026-09-11 in Sandbox's trail,
  Stage 6d 7.2). Two calls at 16:02:15Z and 16:02:28Z carried the principal
  `datazone_usr_role_<project>_<env>`, session name and `sourceIdentity` `<idc-user-id>@<env-id>`, the
  laptop's own public address, `userAgent` `aws-sdk-js/1.0.0 … os/win32 … lang/js md/nodejs`, and a
  `streamUrl` to `wss://ssmmessages.us-west-2.amazonaws.com`. The portal's deep link was the same role from
  a Chrome user agent, refused with *"ValidationException … does not have remote access enabled"* on a space
  with the flag off (2026-09-10). Denies on persona permission sets never evaluate on the call. The role's
  only `StartSession` grant was AWS's `AllowStartSessionForSpaceRemoteConnection` in
  `SageMakerStudioProjectRoleMachineLearningPolicy` v43, conditioned on the project and user tags
  (2026-09-12); the principal tags it reads are not in CloudTrail. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-11 and 2026-09-12; `runbooks/remote-ide.md` §I;
  `aws/remote-ide.py`.

- `SUP-235` **A SageMaker space with a remote IDE session runs two IDE servers in one container, each with
  its own gallery, extension directory and settings** (measured 2026-09-11, Stage 6d 7.3 to 7.5). `ps`
  showed AWS's Code Editor (`/opt/conda/share/sagemaker-code-editor`, Code-OSS 1.119.1, gallery
  `open-vsx.org`, extensions in `~/sagemaker-code-editor-server-data/extensions`) beside the remote
  session's VS Code Server (`~/.vscode-server/cli/servers/Stable-<commit>/`, the client's own 1.127.0,
  gallery `marketplace.visualstudio.com`, extensions in `~/.vscode-server/extensions`), both on the space's
  EBS volume. The AWS Toolkit was 3.101.0 in one and 4.15.0 in the other, and a setting written in one
  surface does not reach the other. `~/.sagemaker_remoteAccess_do_not_delete/sagemaker-remote-access-server`
  (6.87 MB, `mtime` 2026-09-04) appeared between the credential vend and `StartSession` and is in no proxy
  log, so the service delivers it. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-11;
  `runbooks/remote-ide.md` §O and §E.

- `SUP-236` **Amazon Q in a SageMaker Unified Studio space calls `us-east-1`, so a Region-ceiling SCP
  refuses it while the project role's managed policy grants it** (read 2026-09-12 in the `us-east-1` trail,
  Stage 6d; re-read 2026-10-17 and 2026-10-18). From a `us-west-2` space, `q:SendMessage` by the project
  role (`userAgent` `api/qdeveloperstreaming`) was refused *"explicit deny in a service control policy"*,
  naming none; only Control Tower's `CTMULTISERVICEPV1` matched, its 92 `NotAction` entries holding no `q:`
  or `codewhisperer:` action. `SageMakerStudioProjectUserRolePolicy` v75 grants `q:StartConversation`,
  `q:SendMessage` and `codewhisperer:GenerateRecommendations` on `*` unconditionally, not `q:PassRequest`,
  which `SageMakerStudioDomainExecutionRolePolicy` v23 grants. `describe-vpc-endpoint-services` in
  `us-west-2` lists no `codewhisperer` service, only `aws.api.us-west-2.qbusiness`, and no Amazon Q service
  from `us-east-1`; Unified Studio's endpoint page lists `com.amazonaws.us-east-1.codewhisperer` as
  *available only in `us-east-1`*. `/amazon/datazone/q/<domain-id>` and `.../q-enabled` answer
  `ParameterNotFound`. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-12, 2026-09-18,
  2026-10-17 and 2026-10-18; `docs/SMUS.md`.

- `SUP-397` **`sagemaker:StartSession` on a space of a domain SageMaker Unified Studio created refuses any
  client but the AWS Toolkit and the Unified Studio web IDEs, and checks the client only after IAM allows
  the call** (measured 2026-11-21 in Sandbox, Stage 6d 7.6). From a space's terminal as
  `eighth-experimentation`'s project role, `aws-cli/2.37.0` through the `sagemaker.api` interface endpoint,
  three calls a second apart: the caller's own space in the blueprint's domain answered
  `ValidationException`, *"StartSession for SageMaker Unified Studio Domain is supported only from Unified
  Studio clients - AWS Toolkit and SageMaker Unified Studio Web IDEs. Retry your request from a supported
  client."*; another project's space and another user's space answered `AccessDenied`, *"… because no
  identity-based policy allows the sagemaker:StartSession action"*. The portal's deep link on the caller's
  own space, 9 minutes earlier, was answered. A call IAM refuses reads the refusal, and only an allowed call
  meets the client check. Which mark of the request the service reads is unread; the user agent is the
  visible difference. The SageMaker AI guide's third connection method runs `aws sagemaker start-session`
  in a `ProxyCommand` script, and neither its pages nor the Unified Studio admin guide's *Local IDE
  support*, read 2026-11-21, state the restriction: that method cannot reach a Unified Studio space, and a
  CLI `start-session` measures the identity half only on a space the caller holds no Allow for. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-11-21; `runbooks/remote-ide.md` §I and §F.

- `SUP-398` **The AWS Toolkit lists a Unified Studio project's spaces from the domain its `Tooling`
  environment names, so a space in the project's `SageMakerAIDomain` blueprint domain is invisible to it**
  (measured 2026-11-21 in Sandbox, Stage 6d 7.6; read from the Toolkit 4.20.0 bundle the same day). Signed
  in to the domain with `eighth-experimentation` open, the Toolkit listed no space. Its six `ListSpaces`
  and `ListApps` pairs from 07:23:08 to 07:31:27 UTC, `aws-sdk-js` from the laptop's address as the
  project role, each named `domainIdEquals` the `Tooling` domain alone, empty since 6d 2.7 moved the spaces;
  the portal's listings in the same minutes named the blueprint's domain as well, where the owner's space
  ran. The bundle (`dist/src/extensionNode.js`) takes the domain id from the `Tooling` environment's
  provisioned resource `sageMakerDomainId` and filters the spaces to the signed-in user's profile; a
  project whose environment has no such resource, as one created since 2026-11-18 under the profile, reads
  *"Spaces are unavailable — this project's tooling environment has no SageMaker domain"* (the code, not
  run). No AWS page read 2026-11-21 (*Local IDE support*, *Set up Remote IDE*, *Connect your Remote IDE*)
  says which domain the Toolkit reads. A space in the blueprint's domain is reached by the portal's deep
  link alone. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-11-21; `runbooks/remote-ide.md` §W.

- `SUP-399` **A portal deep link hands the Toolkit one session, and every later SSH connection to the space
  waits on the browser for another, for 40 seconds** (measured 2026-11-21 on macOS, Stage 6d 7.6; read
  from the Toolkit 4.20.0 bundle the same day). The link's session, from the portal's `StartSession`, is
  stored in `~/.aws/.sagemaker-space-profiles` as the request `initial-connection`. The connect script asks
  the Toolkit's local server (`/get_session_async`) for a session per SSH connection, and the server hands
  `initial-connection` to the first and marks it `consumed`. For a later connection it opens the portal's
  refresh URL in the default browser, with `remote_access_token_refresh=true` and a callback to its own
  `localhost` port, answers 202 and marks the request `pending`, then answers 204 until the callback
  delivers a session; the script polls 8 times at 5 seconds and gives up. Remote-SSH's
  `remote.SSH.localServerDownload` `always` copies the VS Code Server with `scp`, a second connection: it
  read 202 once and 204 seven times from 07:33:37 UTC and failed at 07:34:18 with *"Error: Timed out after
  8 attempts waiting for session to be ready."*, and the trail holds no second `StartSession`. No AWS page
  read 2026-11-21 mentions the refresh or its limit. A first connection to a space that does not hold the
  server yet, and every reconnection, needs the browser to finish the portal's refresh, signed in as the
  space's owner, within 40 seconds. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-11-21;
  `runbooks/remote-ide.md` §W.

## SageMaker AI jobs and models

- `SUP-237` **A processing job reads `Completed` minutes after it ends, and the operator bills the wait**
  (measured 2026-10-11, Stage 6i step 3.8). `ProcessingEndTime` was 23:16:26Z, the outputs had landed at
  23:16:21Z, and `describe-processing-job` still read `InProgress` at 23:18:33Z and `Completed` at
  23:18:54Z. `SageMakerProcessingOperator` waits on that status, so its task held a worker 791 s for a
  one-second command: about 3 minutes of provisioning before `ProcessingStartTime`, 7 of image pull, and
  this tail. Where: `runbooks/serverless-workflows.md` §J.

- `SUP-238` **An extension module imports from a processing input** (measured 2026-10-11, Stage 6i
  verification xvi). `msgspec`'s `_core.cpython-313-x86_64-linux-gnu.so` loaded from
  `/opt/ml/processing/code`, which SageMaker had downloaded from S3 with the prefix's folder markers. No
  page says whether the input volume admits executable mappings. Where: `runbooks/serverless-workflows.md`
  §J1.

- `SUP-239` **`sagemaker:VolumeKmsKey` still populates on `CreateProcessingJob`, although the Service
  Authorization Reference lists `sagemaker:VolumeKmsKeyArn` for the job creates** (measured 2026-10-11 and
  2026-10-18, Stage 9 3.5). The reference read on 2026-10-16 names `sagemaker:VolumeKmsKeyArn`. A deny keyed
  on the older `sagemaker:VolumeKmsKey` admitted a processing job naming its `VolumeKmsKeyId` under
  Sandbox's permissions boundary on 2026-10-11, and in Production's SCP battery of 2026-10-18 the job with
  no `VolumeKmsKeyId` answered `DENY-SCP` while the compliant job reached authorization
  (`ResourceLimitExceeded`). Whether `VolumeKmsKeyArn` also populates was not read. A compliant job turning
  into a deny is the sign that the old name stopped populating. Where: `log-stage-09-deployment-targets.md`,
  2026-10-16 and 2026-10-18; `runbooks/scp-battery.md`.

- `SUP-240` **A SageMaker processing job creates every mount under `/opt/ml/processing` owned by root with
  mode 755, so a container running as a non-root user cannot write its output** (measured 2026-10-11 in
  Sandbox, Stage 6i 2.5). In the house image, which runs as `uid=1000(sagemaker-user)`, `code`, `inbox` and
  `outbox` listed as `drwxr-xr-x. 0 0`, and `touch /opt/ml/processing/outbox/probe` failed with `Permission
  denied`. The job ended `Failed` with *"AlgorithmError: , exit code: 1"*, which names neither the mount nor
  the permission; the cause is in the container's stream in `/aws/sagemaker/ProcessingJobs`. In the next run
  `sudo -n chown "$(id -u)" /opt/ml/processing/outbox` succeeded and the write passed, `sudo` being the
  image's. Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-11; `runbooks/serverless-workflows.md`
  §J.

- `SUP-241` **A SageMaker processing job's image is pulled by the platform outside the job's VPC, as the
  execution role's id with session name `SageMaker`** (read 2026-10-11 in Production's CloudTrail, Stage 6i
  pass 2). For a network-isolated job in Sandbox on an image in Production's registry, Production's trail
  held three `BatchGetImage` by digest, each `userIdentity.type` `AWSAccount`, principal `<role
  id>:SageMaker`, none with a `vpcEndpointId`; the one at the job's start was invoked by
  `ecr.amazonaws.com`. The job session's `GetAuthorizationToken` and 42 `GetDownloadUrlForLayer` followed,
  and one more `BatchGetImage` was refused with `InvalidParameterException` on its `repositoryName` while
  the pull succeeded, again in Staging on 2026-10-19. An isolated job therefore needs no ECR endpoint. The
  create itself came through Sandbox's `sagemaker.api` endpoint as session `AmazonMWAAServerless`. Where:
  `log-stage-06i-sandbox-orchestration.md`, 2026-10-11.

- `SUP-242` **A `CreateProcessingJob` with a volume key makes a direct `kms:CreateGrant` as the execution
  role in session `SageMaker`, and the job goes on when it is refused** (read 2026-10-11 in Sandbox's
  CloudTrail, Stage 6i pass 2; again 2026-10-19 in Staging). At each create the project role, session
  `SageMaker`, called `kms:CreateGrant` on the project key from an AWS address (the Java SDK in Lambda) and
  was refused, *"no identity-based policy allows the kms:CreateGrant action"*, because AWS's
  `SageMakerKmsPermissions` allows the action only with `kms:ViaService` `sagemaker.*.amazonaws.com`. In the
  same second the operator's session, invoked by `sagemaker.amazonaws.com`, created a grant for
  `sagemaker.us-west-2.amazonaws.com`, and `ec2-frontend-api.amazonaws.com` derived a `Decrypt` grant from
  it. Each job completed with its output under the project key, so the refusal in a trail is not a failure's
  cause. Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-11;
  `log-stage-18-staging-deployment-project.md`, 2026-10-19.

- `SUP-243` **`CreateProcessingJob` checks the instance quota after authorization and before the role**
  (measured 2026-10-17 and read in CloudTrail on 2026-10-18, Stage 9). In Production, where the processing
  quotas of `ml.m5.large` and `ml.m5.2xlarge` read 0, six calls naming a role that does not exist answered
  `ResourceLimitExceeded`, never `ValidationException`; after the `Workloads` document's apply the same
  calls answered the SCP's deny. So a quota of 0 hides the validation a probe relies on, and reads as
  authorized. Where: the Stage 9 log, `aws/probes/probes.py` `_JOB_AUTHORIZED`.

- `SUP-244` **An SCP denies serverless inference with `sagemaker:ServerlessMemorySize`, since
  `CreateEndpointConfig` has no VPC field and no VPC condition key** (measured 2026-10-17 and 2026-10-18 in
  Production, Stage 9 3.7). The Service Authorization Reference lists no VPC condition key for
  `CreateEndpointConfig` (read 2026-10-16), and an endpoint configuration carries no VPC field. A statement
  denying the action when `sagemaker:ServerlessMemorySize` is present (`Null` = `false`) works: before it
  was attached a `create-endpoint-config` with a `ServerlessConfig` reached authorization, and after it the
  same call answered `DENY-SCP` naming the `Workloads` document, while an instance-backed configuration
  stayed authorized. `MemorySizeInMB` is required in a `ServerlessConfig`, so every serverless variant
  should carry the key (one variant measured). Where: `log-stage-09-deployment-targets.md`, 2026-10-17 and
  2026-10-18.

- `SUP-245` **SageMaker fills `sagemaker:InstanceTypes` from every entry of a job's `InstancePreferences`
  list, so an instance-type SCP reads a preference list** (measured 2026-10-22 in Production, Stage 9 3.5
  run at Stage 18 8.7). With a preference list in place of `InstanceType`,
  `ProcessingResources.ClusterConfig.InstancePreferences` for `CreateProcessingJob` and
  `ResourceConfig.InstancePreferences` for `CreateTrainingJob`, `DenySageMakerInstanceCeiling`
  (`ForAnyValue:StringNotEquals` on the key) answered `DENY-SCP` for a list naming `ml.m5.2xlarge` and for
  one naming `ml.m5.large` then `ml.m5.2xlarge`, for both actions; a list naming `ml.m5.large` alone reached
  authorization. The policy generator's catalogue lists no new key for the lists. AWS's page says SageMaker
  checks the quota of every listed type, so a listed type at quota 0 still refuses the request (read, not
  isolated). Where: `runbooks/scp-battery.md`, phase 4b; `upstream-releases.md`;
  `log-stage-18-staging-deployment-project.md`, 2026-10-22.

- `SUP-246` **A cross-account `sagemaker:CreateModelPackage` refused by the group's resource policy names
  the resource `model-package/<group>/new`, and is logged in the caller's account alone** (measured
  2026-10-23 and 2026-10-26, Sandbox to Production, Stage 9 3.4). From a Sandbox SSO persona and then from a
  project role in a space, `create-model-package` on Production's group ARN answered *"is not authorized to
  perform: sagemaker:CreateModelPackage on resource:
  arn:aws:sagemaker:us-west-2:<Production>:model-package/awsds-prod-model-app-etl/new because no
  resource-based policy allows the sagemaker:CreateModelPackage action"*. The resource ends in `/new`, not a
  version number. The wording names the resource policy, so the identity side had allowed the call. The
  refused `CreateModelPackage` was in Sandbox's trail only, while `DescribeModelPackageGroup` by ARN,
  admitted by the group policy, was in both accounts' trails, Production's record carrying no caller ARN.
  Where: `log-stage-09-deployment-targets.md`, 2026-10-23 and 2026-10-26.

- `SUP-247` **`CreateModel` from a model package describes the package as the model's execution role, and
  goes on when refused** (measured 2026-10-25, Stage 10 5.4 in Production). At 01:29:33 the deploy role's
  `CreateModel` on `awsds-prod-model-app-etl/1` was followed by a `DescribeModelPackage` as
  `awsds-prod-job-exec`, session `sagemaker-inference`, refused *"is not authorized to perform:
  sagemaker:DescribeModelPackage"*; the model was created and the batch transform completed. A trail reader
  meets an `AccessDenied` on a run that succeeded. Where: `log-stage-10-orchestration-promotion.md`,
  2026-10-25.

- `SUP-248` **A SageMaker processing job whose `ProcessingOutputConfig` names no `KmsKeyId` uploads its
  outputs under the AWS managed key `aws/s3`, over the bucket's default encryption** (read 2026-10-25 in
  Production, Stage 10, `EXC-22`). The job named the account's data key as `VolumeKmsKeyId`; its
  `app-etl/work/job/trades.summary.json` (06:38:54) on the outputs bucket read SSE-KMS under `aws/s3` with
  `head-object`, while `app-etl/outbox/report.json` (06:43:01), written by a later task, was under the data
  key. No bucket statement refused the key, so any principal the bucket policy admits reads such an object
  without the data key's grant. With `ProcessingOutputConfig.KmsKeyId` set, the same object read under the
  account data key in Staging (2026-10-25 23:37 UTC) and Production (2026-10-26 00:27:20 UTC). Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-25; `AWS_STATE.md` `EXC-22`.

- `SUP-408` **A `CreateTrainingJob` sent with no tags from a notebook in a SageMaker Unified Studio space
  is recorded with the space's `sagemaker:*-arn` and `AmazonDataZone*` tags and admitted without the
  caller's `sagemaker:AddTags`, while the same request naming `AmazonDataZoneProject` is refused as
  `sagemaker:AddTags`** (measured 2026-11-21 in Sandbox, Stage
  17 2.2). `train.py untagged` deleted `Tags` from its boto3 request; CloudTrail's event at 23:19:36 recorded
  `requestParameters.tags` with `sagemaker:user-profile-arn`, `sagemaker:domain-arn`, `sagemaker:space-arn`,
  `AmazonDataZoneProject`, `AmazonDataZoneScopeName`, `AmazonDataZoneUser` and `AmazonDataZoneDomain`, and
  the job `ml-demo-xgb-untagged-20261121-231933` carried the same seven, though no policy on the project
  role allowed `AddTags`. Eight seconds later the request whose `Tags` named `AmazonDataZoneProject` read
  *"not authorized to perform: sagemaker:AddTags ... because no identity-based policy allows the
  sagemaker:AddTags action"* (`SUP-267`'s exclusion). The composer of the seven is not read: the space's
  `BOTOCORE_EXPERIMENTAL__PLUGINS` names the S3 Access Grants plugin alone, the blueprint domain's
  `TagPropagation` reads `None`, and the four `AmazonDataZone*` keys are four of the nine the space and its
  user profile carry. A notebook in a space creates a training job without the training pair by naming no
  tag; a workflow's operator names it and needs the pair (`sandbox/workflows/`). Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-21.
  **Read again 2026-11-22** (Stage 17 3.2): `CreateModelPackageGroup` from the same space, its `Tags`
  naming `AmazonDataZoneProject` alone, was recorded at 00:18:45 with the same seven keys and admitted
  through `sandbox/ml/`'s statement, whose `aws:TagKeys` condition admits that key alone, so the six others
  were not in the authorization. A versioned `CreateModelPackage` with no tag argument was recorded at
  00:34:10 with no `tags` key (`SUP-409`). Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-409` **A model package version takes no tag: a versioned `CreateModelPackage` that names `Tags` is
  refused as `sagemaker:AddTags` on `model-package/<group>/new`, and the same request with no tag argument
  is authorized against the group's tags** (measured 2026-11-22 in Sandbox, Stage 17 3.2, as
  `eighth-experimentation`'s role from a space). CreateModelPackage's API reference says a package created
  in a group uses the group's tags and *"you cannot supply a tag argument"*. With `Tags` naming
  `AmazonDataZoneProject`, the request at 00:18:46 read *"not authorized to perform: sagemaker:AddTags on
  resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:model-package/ml-demo-xgboost/new because no
  identity-based policy allows the sagemaker:AddTags action"*, `requestParameters` null: the authorization
  answers before any validation of the tag argument, and names a permission. Without
  `Tags`, the request at 00:34:10 created version 1, `PendingManualApproval`, recorded with no `tags` key.
  The one statement on the role allowing `CreateModelPackage` on that resource is the blueprint's
  `SageMakerCreatePermissions` (`SageMakerStudioProjectRoleMachineLearningPolicy` v48), conditioned on
  `aws:ResourceTag/AmazonDataZoneProject` equal to the caller's principal tag, so the version's resource tag
  at the create is its group's. `ListTags` on the version answers *"ValidationException: Tag operations are
  supported only on ModelPackage Group not on ModelPackage Versions."* An `AddTags` grant on `model-package/*`
  would authorize a request the API reference excludes; a registration names no tag, into a group tagged
  with the project.
  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-458` **`CreateModelPackage` refuses a `ModelDataETag` that its caller sends, even the object's
  own ETag, and sets the field itself from the object the version names** (measured 2026-11-22 in
  Sandbox, Stage 17 9.6, as `app-ml-dev`'s project role from an MWAA Serverless worker, through the
  `sagemaker` API endpoint).
  - The documentation: `ModelPackageContainerDefinition` describes the field as *"The ETag associated with
    Model Data URL"* and says nothing of who sets it. CreateModelPackage lists it in its request syntax
    with no prose.
  - The refusal: a versioned `CreateModelPackage` at 19:39:35 named `ModelDataETag`
    `b5a42cff73d4153ba6731750a1831ebc`, the ETag `head-object` read on its `ModelDataUrl` without the
    quotes. It was refused: *"An error occurred (ValidationException) when calling the CreateModelPackage
    operation: The ETag request value isn't permissible."*
  - The service sets it: the same request with no `ModelDataETag`, at 20:00:18, created `app-ml-dev/1`,
    whose `ModelDataETag` reads `1792fa2976e38b9a5bec44860076416d`, the object's ETag at that moment.
    `ml-demo-xgboost/1`, created at 00:34:10 by a request with none, reads
    `f8783f02a8dc0bb2867b2e67b030ea30`, its own object's ETag.
  - The service also fills `ImageDigest` and sets `IsCheckpoint` to `false`.
  - Under the bucket's SSE-KMS encryption the ETag is no digest of the bytes. The same 9,930 bytes
    (SHA-256 `852032c5…`) read `b5a42cff…` after the PUT at 19:39 and `1792fa29…` after the PUT at 20:00.
    The candidate they were copied from reads `fad76c8d…`.
  - So a version's `ModelDataETag` names one PUT of its object, and rewriting identical bytes changes the
    object's ETag. Whether `CreateModel` from the version compares the two is verification lix.

  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22; `examples/app-ml/code/app_ml_tasks/registry.py`.

- `SUP-460` **AWS republishes the SageMaker XGBoost algorithm image under its short tag: `sagemaker-xgboost:3.0-5`
  named a new image from 2026-11-17, and the image it named before keeps its long tag alone** (read
  2026-11-22 in AWS's `us-west-2` algorithm registry with `ecr describe-images`, Stage 17 9.6, as the
  infrastructure user).
  - The reading, at about 19:11 UTC: `3.0-5` names
    `sha256:5a82a2d0f00fa1baa41aba8a95f8145b8214bc65c4c16ce12d723a30e8cc34dd`, with `3.0-5-1.0.67.0` and
    `3.0-5-cpu-py3`, pushed 2026-11-17 19:42:09. The digest both targets' `training-image.tf` pin,
    `sha256:0b5d9341baa09ab2432fc9efbc329425e69325ba33562b1e2a015fd6f16e3a78`, carries `3.0-5-1.0.64.0` alone,
    pushed 2026-10-11 05:39:43.
  - No page read for this project says the short tag moves. The image table of `sagemaker-core` 2.21.0, read for
    pass 0 on 2026-10-17, names the image by `3.0-5`.
  - A training job created with the tag at 18:59:16 ran on the republished image. `app-ml`'s `publish` then
    refused its candidate before any write, the training image naming no digest. The job created at 19:30:09
    with the pinned digest ran on the pin.
  - So `3.0-5` is a release, as Lesson 68 says of what a host reads unpinned. An image named by the short tag
    today is not the one the targets serve.

  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22; `terraform-live/*/ml/training-image.tf`.

## MWAA

### MWAA Serverless: workflows and the API

- `SUP-249` **A workflow authored in the SageMaker Unified Studio portal runs as the project's role with the
  session name `AmazonMWAAServerless`, and needs no `Workflows` blueprint** (read 2026-09-09 on the workflow
  and its run of 2026-08-27, Stage 6d 4.1, 4.4 and 4.6). Sandbox's only workflow, created in the portal on
  2026-08-27, ran its task as `datazone_usr_role_<project>_<environment>`, so the project's permissions
  boundary applied to it; the SMUS page's *"its own execution role and worker"* does not hold for the role.
  Its `NetworkConfiguration` held the account's two private subnets in two AZs and one security group, its
  encryption `CUSTOMER_MANAGED_KEY` on the project key, and its definition was readable inline and at
  `DefinitionS3Location` in the projects bucket, written twice at creation, 18 s apart. The surface existed
  with the eleven blueprint configurations unchanged and no `Workflows` blueprint. A workflow created
  through Cloud Control with its own role ran as that role (`awsds-staging-wf-app-etl`, 2026-10-23). Where:
  `log-stage-06d-unified-studio-remainder.md`, the seventh sitting (2026-09-09) and 2026-09-10;
  `log-stage-10-orchestration-promotion.md`, 2026-10-23.

- `SUP-250` **`mwaa-serverless update-workflow` replaces the workflow whole: a field not passed is dropped,
  and the domain and project the portal injected are lost with no field to restore them** (measured
  2026-09-10 in Sandbox, Stage 6d step 4). An update passing `--workflow-arn`, `--definition-s3-location`
  and `--role-arn` set `NetworkConfiguration` to null, removing two subnets and a security group, and
  replaced `LoggingConfiguration` with a service default, creating
  `/aws/mwaa-serverless/<workflow-arn-suffix>/`, so the run's logs were missing from the workflow's group.
  The next run's task failed in 7 s with no AWS call in CloudTrail. Re-passing every field restored the
  network; the next run failed on *"ValueError: Project ID not found in environment"*, the portal-injected
  binding gone. The `AmazonDataZoneProject` tag survived and nothing carried the domain; `domain_id`,
  `project_id` and `domain_region` written into the definition repaired it. The registry's
  `AWS::MWAAServerless::Workflow` marks `Name` and `EncryptionConfiguration` create-only (read 2026-10-18
  and 2026-10-22), so a new key is a new workflow. `Environment`, a workflow's environment variables (API of
  2026-11-04), is one more field an update drops: the API reference says an `UpdateWorkflow` that omits it
  leaves the workflow with none (read 2026-11-13 in botocore 1.44.2's model and the user guide, not
  measured). Where: `log-stage-06d-unified-studio-remainder.md`,
  2026-09-10; `log-stage-10-orchestration-promotion.md`, 2026-10-22; `docs/SMUS.md`; `upstream-releases.md`,
  the MWAA Serverless table.

- `SUP-251` **`list-workflow-runs` returned `RunType` null for every run on 2026-10-10 and carried it on
  2026-11-22; `get-workflow-run` carries it** (measured 2026-10-10, on Sandbox's two portal-authored
  workflows). The service model declares `RunType` (`ON_DEMAND` | `SCHEDULED`) in `WorkflowRunSummary`; all
  six listed runs read `null`, and each read `ON_DEMAND` one at a time. A check that takes the type from the
  list sees no `SCHEDULED` run whether one fired or not, and that is Stage 10 verification (v)'s evidence.
  Where: `aws/orchestration.py` section 7, `log-stage-06d`'s sixteenth sitting.
  **Read again 2026-11-22** (R1): the list carried `RunType` on every run, 36 runs of 15 workflows in
  Sandbox, Staging and Production, each `ON_DEMAND`, the portal-created `wfk-notebook`'s run among them.
  `simple-s3-copy`, one of the workflows read on 2026-10-10, is no longer listed, so whether the service
  changed or those runs differed is unread, and no `SCHEDULED` run was listed to show the list carries that
  value. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-22.

- `SUP-252` **The portal's save sends a code location the editor pre-fills, and an import cannot replace a
  saved workflow** (measured 2026-10-10/11, Stage 6i). A new workflow's *Settings → Storage* carries
  `dev/operatorFiles/<workflow>.zip`, a processing-only workflow's included; saved with no file there, the
  service answers `ValidationException: Code not found in specified S3 location`. An import into a saved
  workflow's editor makes a new workflow under the bare name, whose save is refused with
  `ConflictException`. Where: `runbooks/serverless-workflows.md` §A.

- `SUP-253` **MWAA Serverless checks a workflow's name at creation, yet two `CreateWorkflow` calls 2 s apart
  both succeeded with one name, and a recreated workflow gets a new ARN suffix** (measured 2026-10-10 in
  Sandbox, Stage 6i pass 2). One portal save made `CreateWorkflow` at 01:00:57Z and 01:00:59Z, and the
  account held `demo-devenv-job-W6HvorwGu9` and `demo-devenv-job-1N0Y70z8Jr`, each `READY` with one version.
  A later create by an existing name was refused, *"Workflow with given name already exists"*, so the twins
  raced past the check. Each delete and create of one name gave a new suffix (`It0FUChSnC`, `ODN4LiixCM`,
  `j39HQ6kTxG`) and restarted the run and version history, while the log group, named after the workflow,
  kept every run's logs. A script reading `list-workflows` by name has to expect several entries and choose
  one, the newest by `CreatedAt` here. Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-10;
  `aws/sandbox-orchestration.py`.

- `SUP-254` **MWAA Serverless creates a workflow's log group,
  `/aws/mwaa-serverless/<domain>-<project>/<workflow>`, at `CreateWorkflow` with no retention, and the
  group outlives the workflow** (measured 2026-10-10 in Sandbox, Stage 6i, 2026-10-20 in Staging, Stage 18,
  and 2026-11-16 in Production, Stage 19). Each workflow the CI/CD CLI 1.0.9 deployed in Staging got such a
  group with no retention: `app_etl_deploy_staging_app_etl`, `dagid_copy_deploy_staging_app_etl` and
  `orchestration_demo_deploy_staging_demo_python_operator`, read by `describe-log-groups` at 22:19:18Z, the
  last two after their workflows were deleted. That reading took the name for the service's default and
  recorded that the CLI passes no `LogGroupName`; the CLI passes it (below). In Sandbox, deleting four
  portal workflows on 2026-10-10 took their run history with them and left their log groups, `MyWorkflow`'s
  holding 21,448 bytes. A deleted workflow's run evidence lives only in its group, and a retention rule has
  to reach the group itself. Read again 2026-11-16 in Production: for an IAM Identity Center domain the CLI
  composes the name (`build_idc_log_group_name`) and passes it in `CreateWorkflow` and `UpdateWorkflow`.
  The trail shows `CreateLogGroup` on each group in the deploy role's session, `invokedBy
  airflow-serverless.amazonaws.com`, with the project key and no retention (02:31:49 to 02:32:13 UTC), and
  the `UpdateWorkflow` calls of 02:50:53 to 02:51:20 naming the existing groups succeeded. The project's
  `datazone-<project>-dev/error` and `/output` groups are created by the project role itself, with no key
  and no retention. Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-10;
  `log-stage-18-staging-deployment-project.md`, 2026-10-20; `log-stage-19-smus-native-data-product.md`,
  2026-11-15; `docs/AWS_STATE.md` `EXC-21`, `EXC-25`.

- `SUP-255` **The portal's workflow editor demands `ContainerArguments` on a SageMaker Processing task,
  which `CreateProcessingJob` does not, and its form has no field for the job's network, keys or tags**
  (observed 2026-10-10 in the portal and read in the saved workflow, Stage 6i pass 2). An imported
  definition whose processing task carried its command whole passed the import and failed the editor's
  validation, *"ContainerArguments: Container argument is required."*; splitting the command into
  `ContainerEntrypoint` and `ContainerArguments` cleared it. The form shows task name, job name, inputs,
  outputs, image URI, entrypoint, arguments, instance type and count, volume and role, and nothing for
  `NetworkConfig`, either KMS key or tags; an import carried all of them, `StoppingCondition` included,
  through the save. Each save adds `is_paused_upon_creation: false` and keeps the editor's layout as a JSON
  comment on the first line. A failed run's banner reads *"Workflow execution failed, please check the task
  execution logs for more details"* and names no cause. Where: `log-stage-06i-sandbox-orchestration.md`,
  2026-10-10; `runbooks/serverless-workflows.md` §A and §J.

- `SUP-256` **Every save takes a new code snapshot, and the portal uploads the code again at every save**
  (measured 2026-10-11, Stage 6i verification vii). A description-only edit made a new workflow version and
  moved `CodeSnapshottedAt` with the code unchanged, and a refused save uploaded the file all the same.
  Where: `runbooks/serverless-workflows.md` §C5.

- `SUP-257` **MWAA Serverless's `UpdateWorkflow` calls `logs:DescribeLogGroups` in the caller's session, and
  a caller without it gets a refusal that names neither the action nor the resource** (measured 2026-10-19
  in Sandbox's trail, Stage 8 `v0.2.1`, pipeline #55). The CI/CD CLI found
  `app_etl_test_experimentation_app_etl` existing, `CreateWorkflow` answering `ConflictException`, and
  updated it; `UpdateWorkflow` answered *"Access denied to logGroup or KmsKey"*. In the deploy role's
  session the service had called `kms:GenerateDataKey` (allowed), `logs:CreateLogGroup`
  (`ResourceAlreadyExistsException`) and `logs:DescribeLogGroups`, refused on the account's
  `log-group::log-stream:`, a listing no single-group grant covers; the grant on `log-group:*` let the retry
  pass. At creation the log group is created in the caller's session and the service creates two grants on
  the workflow's key for `airflow-serverless.us-west-2.amazonaws.com` (2026-10-16 and 2026-10-19), and the
  first release's create made no such call as the update's. Where: `log-stage-08-cicd-pipelines.md`,
  2026-10-19; `log-stage-18-staging-deployment-project.md`, 2026-10-19 (4.2);
  `terraform-live/sandbox/workflows/deploy-role.tf`, `DescribeTheLogGroupsOnUpdate`.

- `SUP-258` **MWAA Serverless authorizes listing, reading and starting a SageMaker Unified Studio project's
  workflow by IAM alone, and the start decrypts with the workflow's key in the starter's session** (measured
  2026-10-19 in Sandbox, Stage 18 0.4). `InfrastructureAccess`, no member of `test-experimentation`, found
  the CI/CD CLI's workflow with `list-workflows` and `get-workflow` and started it with
  `start-workflow-run`, `SUBNET_AZ1` and `SUBNET_AZ2` as overrides; the run read `SUCCESS`, `Duration` 136,
  task attempt 1. The trail held `StartWorkflowRun` with no error and no DataZone call on the start path; in
  the same second `airflow-serverless.amazonaws.com` called KMS `GenerateDataKey` and `Decrypt` on the
  project key under the starter's session, the workflow's ARN as encryption context, and one `Decrypt` for
  each later `get-workflow-run`. A starter needs the IAM action and its own KMS permission on the workflow's
  key, and project membership is not checked. The polled state lagged the work by about two minutes. Where:
  `log-stage-18-staging-deployment-project.md`, 2026-10-19 (0.4). The decrypt behind each read of a run is
  `SUP-264`.

- `SUP-259` **MWAA Serverless's EventBridge detail types all begin `MWAA Serverless Workflow Run`, and the
  `aws.events` schema registry holds no schema for the service** (read 2026-10-22 on EventBridge's reference
  page and in the registry; measured 2026-10-23 in Staging, Stage 10 3.1 and 3.4). The registry `aws.events`
  holds no `aws.airflow-serverless` schema, and its prefix `aws.airflow` lists provisioned MWAA's alone.
  EventBridge's reference page lists fifteen detail types, each prefixed, among them `MWAA Serverless
  Workflow Run Failed` and `MWAA Serverless Workflow Run Timeout`, so a rule on `Workflow Run Failed`
  matches no event. A Staging run that ended at 22:50:17 had its `FAILED` event emitted at 22:51:29, 72 s
  later (the run's `ModifiedAt` 22:51:28), and a rule on the prefixed name delivered it through SNS in the
  same minute. An alert on the event trails the failure by about a minute (seen once). Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-22 and 2026-10-23.

- `SUP-260` **MWAA Serverless calls `iam:CreateServiceLinkedRole` in the saver's session on a workflow
  created through Cloud Control, with its service-linked role already in the account** (read 2026-10-24 in
  Staging's trail of 2026-10-23). At Stage 8 3.8's apply the call came at 22:47:51, invoked by
  `airflow-serverless.amazonaws.com`, answered `InvalidInputException`, and the creation went on; Stage 18's
  later CLI creations of 2026-10-19 made no such call. Under a role without the grant the call is refused
  before IAM reads whether the role exists, and how the service takes that refusal is unmeasured, so a grant
  written "until the role exists" is written for both accounts. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-24; Staging's `deploy-role.tf` and Production's
  `deploy-anchors.tf`, `CreateTheWorkflowServiceLinkedRole`. Read again 2026-11-17 in both deployment
  targets' trails (Stage 19): the call is not Cloud Control's. In Staging it came at 20:46:18 UTC on
  2026-11-15 in `awsds-deploy-staging`'s Cloud Control session, a second before release T's first
  `CreateWorkflow`, and at 23:21:03 in the CLI's boto3 session, a second before release F's first, both
  invoked by `airflow-serverless.amazonaws.com` and answered `InvalidInputException`; each session's second
  creation (20:46:27, 23:21:16) drew none. In Production the CLI's three creations by `awsds-deploy-prod`,
  at 02:31:50, 02:32:02 and 02:32:14 UTC on 2026-11-16, drew none. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-17; both targets' `deploy-project.tf`,
  `CreateTheWorkflowServiceLinkedRole`, since Stage 19 item 31.

- `SUP-261` **MWAA Serverless authorizes the tags a `CreateWorkflow` carries as
  `airflow-serverless:TagResource` on `workflow/*`, and no trail shows that check** (measured 2026-10-24,
  pipeline #68 in Staging). A workflow's ARN ends in a suffix the service generates
  (`awsds-staging-wf-app-etl-hHNGu2YFTv`), so `TagResource` granted on the name pattern
  `workflow/awsds-<env>-wf-*` misses the creation: Cloud Control's handler failed with
  `UnauthorizedTaggingOperation`, *"not authorized to perform: airflow-serverless:TagResource on resource:
  …workflow/*"*. The check runs inside `CreateWorkflow` and leaves no CloudTrail event of its own, so a
  trail replayed through the policy simulator cannot show it, and a by-hand apply under a broad permission
  set passes it unseen. The service's condition keys are `aws:RequestTag/*`, `aws:ResourceTag/*` and
  `aws:TagKeys`; held to `aws:RequestTag/Name`, the retried apply created the workflow in 5 s. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-24; both `foundation/apply-orchestration.tf`,
  `TagTheWorkflowsAtCreation`.

- `SUP-262` **MWAA Serverless publishes no CloudWatch metric namespace, so a workflow's logs and EventBridge
  events are its whole signal** (read 2026-10-25 with `list-metrics` in Sandbox, Staging and Production,
  Stage 10 verification xvi). Over `list-metrics`' 14 days no MWAA Serverless or Airflow namespace existed
  in any of the three accounts, after app-etl and train runs in each target, while the logs arrived:
  `IncomingLogEvents` read 105, 142 and 104 on `/awsds/prod/wf/app-etl` in the 21:00, 01:00 and 06:00 hours.
  A `monitoring` interface endpoint in the workers' VPC would turn nothing into a reading, and an alarm on a
  run's outcome is built on the service's EventBridge events. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-25.

- `SUP-263` **The API has no `.amazonaws.com` name, and botocore reports a proxy's refusal as a connection
  failure** (measured 2026-10-26, Stage 10 2.1). `airflow-serverless.<region>.api.aws` is the endpoint
  service's only private name and the only public one that resolves; a compute plane that refuses `.api.aws`
  at its proxy leaves an interface endpoint as the one path. The proxy's `403` to `CONNECT` reached the CLI
  as *"Failed to connect to proxy URL"*; the proxy log names the host. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-26.

- `SUP-264` **`GetWorkflowRun` makes MWAA Serverless decrypt with the workflow's key in the reader's
  session, while `GetWorkflow` and `ListWorkflowRuns` do not** (read 2026-10-26 in Staging's and
  Production's trails, Stage 10 decision 11). In Staging each `GetWorkflowRun` poll by the chain role paired
  with a `Decrypt` in the same second, `invokedBy` `airflow-serverless.amazonaws.com`, under the encryption
  context `aws:airflow-serverless:workflow-arn` beside an `aws-crypto-public-key` entry; `GetWorkflow`,
  `ListTagsForResource`, `ListWorkflowRuns`, `ListWorkflowVersions` and `ListWorkflows` paired with none. In
  Production a Deployment Manager session's `GetWorkflowRun` answered `SUCCESS` under a decrypt allow
  narrowed with `kms:ViaService` `airflow-serverless.us-west-2.amazonaws.com`, the service's `Decrypt` in
  that session at 20:01:18 with no error. A reader of run state needs `kms:Decrypt` on the workflow's key,
  and that `kms:ViaService` value admits it. `GetTaskInstance` was not called in the window. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-26.

- `SUP-436` **`list-workflow-runs` fills each page with the newest runs not yet listed and orders the runs
  inside a page by no time, so only a page of one run is ordered** (measured 2026-11-22, R1, as
  `awsds-infra-prod` and `awsds-infra-sandbox-1`, aws-cli 2.37.12). Production's
  `app_etl_deploy_production_app_etl` holds three runs of 2026-11-16, created 02:32:15, 02:51:21 and 03:19:11
  UTC. One page listed them 02:32:15, 03:19:11, 02:51:21, the same on two calls; pages of one run answered
  03:19:11, 02:51:21 and 02:32:15, in that order; a page of two answered 03:19:11, 02:51:21. Sandbox's
  `houseprice_etl_eighth_experimentation_houseprice_etl` holds seven runs of 2026-10-16: one page listed
  02:13:11, 02:03:59, 15:21:53, 15:18:35, 03:28:31, 03:11:05, 02:25:55; pages of three answered the three
  newest, then 02:13:11, 03:11:05, 02:25:55, then 02:03:59; pages of one answered all seven newest first. Of
  the 15 workflows with runs in Sandbox, Staging and Production, a full list read in descending order for
  six, ascending for one and in neither for three; five hold one run. The CLI's reference page says only
  that the call lists all runs for a workflow, with optional pagination and filtering. Consequence:
  `WorkflowRuns[0]` of a page holding more than one run is not the newest run, and `--max-results 1
  --no-paginate --query 'WorkflowRuns[0].RunId'`, the runbooks' form, is. A reader of several runs sorts by
  `RunDetailSummary.CreatedOn`, as `aws/sandbox-orchestration.py` does; `aws/orchestration.py`'s
  `--max-results` returns the newest runs in no order. Where: `log-stage-19-smus-native-data-product.md`,
  2026-11-22.

### MWAA Serverless: workers, tasks and operators

- `SUP-265` **The portal workflow's notebook task runs as a SageMaker training job, and
  `SageMakerNotebookOperator` takes no network, isolation or key parameter** (measured on the runs of
  2026-08-27 and 2026-09-10 in Sandbox, the operator read in its code, Stage 6d step 4). The first portal
  workflow's run failed on `sagemaker:CreateTrainingJob` for `training-job/Notebook-task-…` *"with an
  explicit deny in a permissions boundary"*, as the project role's session `AmazonMWAAServerless`, with no
  `VpcConfig`. The operator delegates to `SageMakerNotebookHook.start_notebook_execution()`, whose
  parameters are `domain_id`, `project_id`, `domain_region`, `input_config`, `output_config`, `compute`,
  `termination_condition`, `tags`, `execution_name` and `waiter_*`: no `VpcConfig`, `NetworkIsolation`,
  `VolumeKmsKey` or `InterContainerTrafficEncryption`. The portal emits `compute: {}`; filling
  `instance_type`, `volume_size_in_gb` and `image_details` brought the third run to the same refusal. A
  control requiring job-level networking on training jobs refuses every notebook task, while a portal
  `S3CopyObjectOperator` task ran `SUCCESS` as the same role. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-09 and 2026-09-10; `docs/SMUS.md`.

- `SUP-266` **An MWAA Serverless task with no `retries` key is retried once on failure, and every update of
  a workflow spends one of its 50 versions** (measured 2026-09-10 to 2026-10-26, Stage 6d and Stage 8 xxiii;
  quotas read 2026-10-19, Stage 18 5.4). Four failed runs of a portal workflow with no `retries` key each
  listed two task instances, `UP_FOR_RETRY` then `FAILED`, so a 7-second task sat inside a 6-minute run; a
  successful run listed one (2026-10-10). Each `update-workflow` and each CI/CD CLI deploy minted a new
  `WorkflowVersion`, keeping the run history: 2 versions for 2 deploys (2026-10-16), `app-etl` at 12
  (2026-10-26). Service Quotas reads AWS's defaults in Staging and Sandbox: 100 workflows per account, 50
  versions per workflow, 100 concurrent runs, 76,800 MB of code, 50 KB per definition, 100 KB of XCom, and a
  task timeout of 60 with no unit. A deploy past the 50th version is unread; the runbooks' caps of 3 retries
  and 3,600 s per task are not measured here. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-10
  and 2026-10-10; `log-stage-18-staging-deployment-project.md`, 2026-10-19; Stage 8's verification xxiii.

- `SUP-267` **The blueprint's project-role policies refuse a workflow's first SageMaker processing or
  training job and its first Glue job, because the read before each create is scoped to a project tag that a
  free name cannot carry** (measured 2026-10-10 and 2026-10-16 in Sandbox, Stage 6i; 2026-10-19 in Staging,
  Stage 18 4.4; the training job 2026-11-16 in Staging, Stage 19).
  `SageMakerStudioProjectRoleMachineLearningPolicy` grants `DescribeProcessingJob` only when
  `aws:ResourceTag/AmazonDataZoneProject` equals the caller's tag, so run `Pzs3TlvfHhqOK6M` failed on
  `DescribeProcessingJob`, *"no identity-based policy allows"*, before any job existed. With that read
  granted, run `FVyFira1LY3BuGi` failed on `CreateProcessingJob` as `sagemaker:AddTags`:
  `SageMakerTagPermissions` excludes every `AmazonDataZone*` key while `SageMakerCreatePermissions` requires
  the job to carry `AmazonDataZoneProject`, so the blueprint's policies alone cannot create a processing
  job. The blueprint grants `glue:GetJob` only on a job tagged with the caller's project; the CI/CD CLI's
  run `u4AFogXA74olkqo` stopped there, and so did Staging's `7MMhwSySe5SOWd1`. With `GetJob` granted,
  `CreateJob` with the tag passed under `GlueCreateAndTagPermissions` alone. Where:
  `log-stage-06i-sandbox-orchestration.md`, 2026-10-10 and 2026-10-16; `runbooks/serverless-workflows.md`
  §G; `terraform-live/sandbox/workflows/main.tf`. What the operators call, and in which order, is `SUP-268`.
  Read again 2026-11-16 in Staging (Stage 19 release F, pipeline #126's `staging-test`): the first run of
  `app-etl-train` under a project role, `W373uHP9ZB5EvsW` in `deploy-staging`, failed on
  `DescribeTrainingJob` of a free name, *"no identity-based policy allows"*; v48 scopes
  `DescribeTrainingJob` to the caller's project tag as it scopes `DescribeProcessingJob`. The deployment
  projects' grant holds the same pair for training jobs (`<env>/studio/workflows.tf`). With it applied,
  `v0.5.2`'s run created `app-etl-train-20261116T020100`, `Completed` (pipeline #129's `staging-test`);
  the pair grants `AddTags` too, so the pass does not separate whether `CreateTrainingJob` with its tag
  is authorized as `AddTags`, as the processing job's create is. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-15.

- `SUP-268` **The Amazon provider 9.32.0's SageMaker and Glue operators read the job name before they create
  the job, and count only one error code as absent** (read in the provider's code at
  `providers-amazon/9.32.0` and measured 2026-10-10 and 2026-10-16, Stage 6i; the training operator read
  2026-10-20, Stage 10 1.3). `SageMakerProcessingOperator.execute()` always calls `_get_unique_job_name`:
  `DescribeProcessingJob` on the proposed name, a `ValidationException` the only absence, anything else
  re-raised; `action_if_job_exists` takes `timestamp` or `fail`, and both check. `SageMakerTrainingOperator`
  calls `DescribeTrainingJob` the same way while `check_if_job_exists` is true, the default, then heads each
  `S3DataSource` channel's bucket (`HeadBucket`) and its key (`HeadObject`) or prefix (`ListObjectsV2`), and
  with `print_log` true reads `/aws/sagemaker/TrainingJobs`. `GlueJobOperator` calls `glue:GetJob` and
  counts only `EntityNotFoundException` as absent; its log reads *"Checking if job already exists"*, then
  *"Creating job"*, and a refused `GetJob` ends the task with no `CreateJob`. A grant on the create alone is
  never reached; each read needs its own. The guide's custom code page lists the provider at 9.38.0 on the
  worker on 2026-11-13, where it listed 9.32.0 on 2026-10-10. Read the same day between the provider's two
  tags, not measured on a worker: `hooks/glue.py` and `hooks/sagemaker.py` are byte-identical and
  `_get_unique_job_name` is untouched, so the reads above hold at 9.38.0, and `GlueJobOperator` there raises
  `GlueJobRunStoppedError` when a run ends in any state but `SUCCEEDED`, where 9.32.0 returned on `STOPPED`.
  Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-10 and
  2026-10-16; `log-stage-10-orchestration-promotion.md`, 2026-10-20;
  `terraform-live/sandbox/workflows/main.tf`; `upstream-releases.md`, the MWAA Serverless table. What the
  blueprint's project-role policies refuse on a first run is `SUP-267`.

- `SUP-269` **MWAA Serverless renders a workflow's Jinja templates when it creates a run, in a short context
  and a sandbox stricter than Jinja's, and a render failure ends the run before any task** (measured
  2026-10-10, 2026-10-16 and 2026-10-26, Stage 6i pass 2 and Stage 10 xxix). Each failed run read
  `StartedOn` and `Duration` null and no task instance. `{{ dag_run... }}` failed with *"'dag_run' is
  undefined"*: `dag_run`, `run_id` and `logical_date` are absent, while the guide's page names `macros`,
  `ti`/`task_instance`, `params`, `ds`, `ds_nodash`, `ts`, `ts_nodash` and a list of macros.
  `macros.datetime.utcnow().strftime(...)` failed with *"access to attribute 'strftime' of 'datetime' object
  is unsafe"*, which Jinja's standard sandbox allows; `{{ macros.time.strftime('%Y%m%dT%H%M%S',
  macros.time.gmtime()) }}` passed. A referenced parameter the run does not pass fails the render, *"'dict
  object' has no attribute 'GLUE_UPDATE_CONFIG'"*, rather than rendering empty, and a portal run, whose
  `OverrideParameters` hold only `mwaa_serverless_workflow_id`, failed so on `SUBNET_AZ1`. A manual run's
  `{{ ts_nodash }}` is the day's midnight. The guide's connections page, read 2026-11-13, says a
  definition's templates also read `{{ conn.<id> }}`, `{{ var.value.<key> }}` and `{{ var.json.<key> }}`, an
  Airflow variable being definable as the workflow environment variable `AIRFLOW_VAR_<KEY>` (`SUP-250`);
  whether the render at run creation resolves them is not measured. Where:
  `log-stage-06i-sandbox-orchestration.md`, 2026-10-10 and
  2026-10-16; `log-stage-10-orchestration-promotion.md`, 2026-10-26; `upstream-releases.md`, the MWAA
  Serverless table.

- `SUP-270` **A worker fetches its `Code` snapshot as the service principal, through the customer's S3
  gateway endpoint** (measured 2026-10-11, Stage 6i decision 7). At each save the service copies the code
  object to `mwaa-serverless-code-files-<AWS-owned account>-<region>-prod`, keyed by account, workflow,
  version and the upload's key. Each task's environment preparation then has
  `airflow-serverless.amazonaws.com` `GetObject` it through the workers' VPC, so the gateway endpoint's
  policy must admit a bucket the customer neither owns nor names. A refusal surfaces only as "Execution
  environment preparation failed due to an internal server error". The guide names neither the bucket nor
  the path. Where: `runbooks/serverless-workflows.md` §O and §C, `log-stage-06i`'s 4.2a entries.

- `SUP-271` **A Bash task's script is rendered as a Jinja template, and its `PYTHONPATH` carries the code
  folder** (measured 2026-10-11, Stage 6i pass 5). `bash_command: reach_pypi.sh` ran as `bash <tmp>.sh`, the
  archive's file rendered into a temporary file; an inline command needs no archive; `PYTHONPATH` starts
  with `/usr/local/airflow/dags`. Where: `runbooks/serverless-workflows.md` §C4. An inline `bash_command`
  runs in a temporary folder, `cwd` `/var/tmp/airflowtmp…`, not in `/usr/local/airflow/dags`, the working
  directory the guide gives a script from the archive (measured 2026-10-11 in two runs, Stage 6i 5.0 and
  5.3; a script called by its full path also ran in the temporary folder on 2026-10-12, outside the lab). A
  command that relies on relative paths into the archive changes to `/usr/local/airflow/dags` first. Where:
  `log-stage-06i-sandbox-orchestration.md`, 2026-10-11; `runbooks/serverless-workflows.md` §C4.

- `SUP-272` **The worker's resolver reports a DNS Firewall block as errno 16** (measured 2026-10-11, Stage
  6i step 5.0). `pypi.org` answered `NXDOMAIN` with `firewall_rule_action` `BLOCK`, and Python read
  `OSError(16, 'Device or resource busy')`, pip `[Errno 16]`, rather than a name error. A worker failing at
  resolution with "Device or resource busy" is a blocked name. Where: `runbooks/serverless-workflows.md` §O.

- `SUP-273` **A run's state and its task instances lag the work they report, and the workflow's log group
  exists from its first save** (measured 2026-10-11, Stage 6i step 3.8). `get-workflow-run` read `QUEUED` until 23:06:16Z while
  the sensor had finished at 23:05:23Z, and `/aws/mwaa-serverless/<domain>-<project>/<workflow>` existed,
  empty and with no retention, before any run. Where: `runbooks/serverless-workflows.md` §V and §O.
  Read again 2026-11-16 in Staging through the chain machines' `getWorkflowRun`, one poll a minute (Stage
  19 release F). `app-etl`'s run read `QUEUED` with no `StartedOn` at 00:43:52 and 00:44:52, then
  `RUNNING` with a `StartedOn` of 00:43:14; it still read `RUNNING` at 00:56:55, after a `CompletedOn` of
  00:56:49, and `SUCCESS` at 00:57:55. `app-etl-train`'s run, started 00:58:24 and completed 00:59:22, read
  `QUEUED` at 00:59:15 and 01:00:15 and `FAILED` at 01:01:16, with a `ModifiedAt` of 01:00:23; it never read
  `RUNNING`. A run shorter than the lag goes from `QUEUED` to its end, and the end is written about a
  minute after `CompletedOn`. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15.
  Read again 2026-11-21 in Sandbox, polled every 22 seconds (Stage 20 2.5). `get-workflow-run` read `QUEUED`
  and `list-task-instances` listed nothing through 04:59:28, `load` first at 04:59:50, while
  `list-workflow-runs` read `RUNNING` from 04:57:30 and the task's Glue job had started at 04:58:18. At the
  end `transform` and the run read `RUNNING` through 05:05:22 and `SUCCESS` at 05:05:44, dbt's log having
  ended at 05:03:11. The task instances lag as the run does, about two and a half minutes at each end, and
  `list-workflow-runs` reads the start first. Where: `log-stage-20-dbt-lineage.md`, 2026-11-21.

- `SUP-274` **On an MWAA Serverless worker a Python task imports a pre-installed package before the code
  archive's copy, while a Bash task's `python3` imports the archive's copy first** (measured 2026-10-11,
  Stage 6i verification viii; the Bash half 2026-10-12, outside the lab). The worker extracts the archive to
  `/usr/local/airflow/dags`. In a Python task `petl`, absent from the worker, imported from the archive, and
  the archive's PyYAML 6.0.1 lost to the worker's 6.0.2 from
  `/opt/mwaa-serverless-venv/lib64/python3.12/site-packages`. A Bash task's `PYTHONPATH` starts with
  `/usr/local/airflow/dags`, so its `python3` imported the archive's `six` 1.16.0 over the one Airflow
  requires. A version pinned in the archive is replaced without notice in a Python task whenever the worker
  carries the package (Python 3.12.14, boto3 1.43.1, Amazon provider 9.32.0). The guide's custom code page,
  read 2026-11-13, lists the pre-installed set as `apache-airflow` 3.0.6, `apache-airflow-providers-amazon`
  9.38.0, `apache-airflow-providers-duckdb` 0.2.1, `duckdb` 2.0.0, `boto3` and `botocore` 1.43.1,
  `dag-factory` 1.0.0 and `lz4` 4.4.4, where it listed the Amazon provider at 9.32.0 on 2026-10-10; not
  measured on a worker since 2026-10-11. Read 2026-11-16: the page's address is now
  `custom-code-operators.html`, titled "Running custom code with Python, Bash, and custom operators", and
  the old address, `operators-python-bash-detail.html`, serves it; the old address's `.md` rendition
  serves a page titled "Using Python and Bash operators", with the provider at 9.32.0, the version the
  page listed on 2026-10-10, no DuckDB row and five AWS encryption packages. Neither rendition carries a
  date, so a `.md` rendition of a page that moved is read against its `.html`. Where:
  `log-stage-06i-sandbox-orchestration.md`, 2026-10-11 (4.3's re-run); `runbooks/serverless-workflows.md`
  §C1; `upstream-releases.md`, the MWAA Serverless table; `log-stage-17-sandbox-machine-learning.md`,
  2026-11-16.

- `SUP-275` **A sensor that soft-fails ends an MWAA Serverless run `SUCCESS`, and the API reports its status
  as `NONE` with no task instance for the tasks after it** (measured 2026-10-11, Stage 6i 3.4). Run
  `2T6nhkziKgM3GA2`, an `S3KeySensor` with `soft_fail: true` and `timeout: 600` over an empty prefix, ended
  `SUCCESS` after 647 s. `RunDetail.TaskInstances` held only `wait_for_file`, which `get-task-instance` read
  as `Status` `NONE`, not `SKIPPED`, with `DurationInSeconds` 611; the two downstream tasks had no task
  instance at all. Only the task log says `Skipping task.` The API alone cannot tell a skipped task from one
  never scheduled, a rule on a failed run hears nothing, and the wait bills its 611 s, about 0.015 USD.
  Where: `log-stage-06i-sandbox-orchestration.md`, 2026-10-11; `runbooks/serverless-workflows.md` §A.

- `SUP-276` **A worker encrypts every XCom a task pushes with its own `kms:GenerateDataKey` on the
  workflow's key, after the task's work is done** (measured 2026-10-23, Stage 8 3.8's by-hand leg in
  Staging). The data key admitted the execution role's `Decrypt` with the workflow's ARN as encryption
  context, the call Stage 18 had read, and the first chain failed at its first task: `GlueJobOperator`
  started the Glue job, the job ran to `SUCCEEDED` in 98 s, and the task ended `FAILED` on *"Failed to
  encrypt XCom value"*, the `GenerateDataKey` refused *"because no resource-based policy allows"*; the three
  tasks behind it `UPSTREAM_FAILED`. A key policy read against the service's documented calls misses the
  XCom backend's, and a run on a key the role already held `kms:*` on (Stage 18's project key) could not
  show it. The role's own policy mirrored the key's, `Decrypt` alone, so the second run moved the wording
  from *"no resource-based policy allows"* to *"no identity-based policy allows"*: one intent in two
  documents (Lesson 33), each needing the action. Where: `log-stage-10-orchestration-promotion.md`, the
  2026-10-23 entries; `staging/data/main.tf`'s `AllowTheWorkflowRolesForTheirWorkflows` and the
  orchestration module's `UseTheKeyForItsWorkflow`.

- `SUP-277` **The MWAA Serverless worker renders an XCom into a template as the JSON of its value**
  (measured 2026-10-25, `v0.4.1`'s train chain in Staging). `{{ ti.xcom_pull(task_ids='train')['Training']
  }}` failed with *"'str object' has no attribute 'Training'"*: the training operator's dict reached Jinja
  as text, and `report.json`, written from `{{ ti.xcom_pull(task_ids='summarize') }}`, holds the JSON text
  of the report's string. A template indexes nothing; the callable decodes. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-24; `examples/app-etl/code/app_etl_tasks.py`,
  `training_job_name`.

- `SUP-278` **A workflow created without `NetworkConfiguration` runs its worker in the service's own
  network, and a borrowed execution role fails it at environment preparation with a log line that names no
  refusal** (measured 2026-10-26, Stage 10 1.2 in Staging). The worker's first calls came from `10.1.11.134`
  with `vpcEndpointId` `airflow-serverless.amazonaws.com` (`exec-env/AWS_ECS_FARGATE`), outside every
  endpoint of the estate, where a configured run's workers call from `10.50.x` through `vpce-…`. Its
  `kms:Decrypt` was refused because the role's statement binds the key to its own workflow's ARN through
  `kms:EncryptionContext:aws:airflow-serverless:workflow-arn`, and the task log said only *"Execution
  environment preparation failed due to an internal server error."*; the trail carried the `AccessDenied`.
  Where: `log-stage-10-orchestration-promotion.md`, 2026-10-26.

- `SUP-372` **The Amazon provider's `SageMakerTransformOperator` reads the transform job's name before
  it creates the job and calls the model APIs only when its `config` carries a `Model` key, and
  `SageMakerRegisterModelVersionOperator` creates the model package group before the package** (read in
  the provider's code at `providers-amazon/9.32.0` and `9.38.0` on 2026-11-16, Stage 17 pass 9; not
  measured on a worker). `SageMakerTransformOperator.execute()`, with `check_if_job_exists` true, the
  default: `DescribeTransformJob` on the proposed name, a `ValidationException` the only absence and
  anything else re-raised; `action_if_job_exists` takes `timestamp` or `fail`, and `fail` raises *"A
  SageMaker job with name … already exists."*. With a `Model` key in the `config` it calls
  `DescribeModel` on the model's name and then `CreateModel`; with none it makes no model call before
  the job. The hook then checks the input (`HeadBucket`, then `HeadObject` on the key or a list of the
  prefix), calls `CreateTransformJob` and polls, and the operator returns `DescribeTransformJob` and
  `DescribeModel`. Its OpenLineage method, where a listener calls it, reads `DescribeModelPackage` for a
  model whose `PrimaryContainer` names a package. `SageMakerModelOperator` calls `CreateModel` and
  `DescribeModel` with no check of the name, and `SageMakerDeleteModelOperator` calls `DeleteModel`
  alone. `SageMakerEndpointOperator` calls `CreateModel` and `CreateEndpointConfig` when its `config`
  carries them, with no check, then `CreateEndpoint`; when the error's message starts *"Cannot create
  already existing endpoint"* it calls `UpdateEndpoint`, dropping the tags; then it waits for
  `InService`. `SageMakerRegisterModelVersionOperator` calls `CreateModelPackageGroup` first, with the
  package's description as the group's, and counts as "already there" only a `ValidationException` whose
  message starts *"Model Package Group already exists"*; it then calls `CreateModelPackage`, and deletes
  a group it created when the package fails. `SageMakerStartPipelineOperator` calls
  `StartPipelineExecution` and returns the execution's ARN; it polls the execution only with
  `wait_for_completion`, false by default. `BedrockInvokeModelOperator` calls `InvokeModel`. Between the
  two tags `operators/sagemaker.py` differs in the triggers' arguments, in where the
  `output_files_to_xcom` check sits and in a notebook instance's tags, and in none of these calls. Not
  read: `SageMakerEndpointConfigOperator` and the tuning and AutoML operators. The consequences: a role
  that runs a transform task needs the read of a free transform-job name, the read `SUP-267` names for
  processing and training jobs; a transform task with no `Model` key needs no model call of its own
  before the job; and the register operator, on a group Terraform declares, needs
  `sagemaker:CreateModelPackageGroup` allowed to reach the "already exists" answer, since a refusal ends
  the task before `CreateModelPackage`. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-16;
  Stage 17 step 9 and decision 16; `runbooks/sagemaker-ai-ml.md` §W.

- `SUP-373` **The Amazon provider's `BedrockInvokeModelOperator` sends `InvokeModel` with no guardrail
  and writes the prompt and the response to the task log, and its retrieval operators log their text
  too** (read in the provider's code at `providers-amazon/9.32.0` and `9.38.0` on 2026-11-16, Stage 17
  pass 10; not measured on a worker). `BedrockInvokeModelOperator.execute()` calls `invoke_model` with
  `body`, the JSON of `input_data`, with `modelId` and, when set, with `contentType` and `accept`. The
  operator has no parameter for `guardrailIdentifier`, `guardrailVersion` or `trace`, and it never calls
  `Converse`. It then logs *"Bedrock %s prompt: %s"* with the model and the input, logs *"Bedrock model
  response: %s"* with the decoded body, and returns that body, which becomes the task's XCom. The class
  is identical at the two tags. `BedrockRaGOperator` calls `retrieve_and_generate` and logs *"Prompt:
  %s"*, *"Response: %s"* and *"Citations: %s"*; `BedrockRetrieveOperator` calls `retrieve` and logs
  *"Query: %s"* and *"Retrieved: %s"*; each returns the service's whole answer.
  `BedrockIngestDataOperator` calls `start_ingestion_job`, repeats it after a `ValidationException`
  whose message it knows as an index not ready, and waits on the job with the hook's
  `ingestion_job_complete` waiter. `BedrockCreateGuardrailOperator` calls `create_guardrail` with the
  name, the two blocked messages, the description, the five policy configurations, `kmsKeyId` and
  `tags`; with `if_exists` `skip`, the default, a `ConflictException` is answered by the hook's
  `get_guardrail_id_by_name`, and the task returns the id it found.
  `BedrockCreateGuardrailVersionOperator` calls `create_guardrail_version`,
  `BedrockDeleteGuardrailOperator` `delete_guardrail` and `BedrockUpdateGuardrailOperator`
  `update_guardrail`, and the four guardrail classes are identical at the two tags.
  `operators/bedrock.py` holds seventeen operator classes at both tags. The service's operators page
  (read 2026-11-16) lists eleven of them with four sensors, and does not list
  `BedrockBatchInferenceOperator`, `BedrockUpdateGuardrailOperator`,
  `BedrockCreateEvaluationJobOperator` and the three AgentCore runtime operators. Not read: the hook's
  methods, and the knowledge base, data source, customization, provisioned throughput, batch inference,
  evaluation and AgentCore operators past their first call. The consequences: a call that must name a
  guardrail is a Python task's, with boto3; a deny over an absent `bedrock:GuardrailIdentifier` refuses
  the invoke operator whatever its input; a workflow on the invoke or the retrieval operators leaves
  what it sent and what came back in the task's log group and in XCom, for whoever reads either; a
  guardrail an account's Terraform declares, as each target's own is (Stage 17 decision 27 (a)), needs
  none of the guardrail operators; and none of them keeps a guardrail in step with a definition, since
  the create operator leaves an existing guardrail as it is, the update operator is off the service's
  list and the version operator publishes a version at every run, so a task that keeps one calls boto3
  (decision 24 (b)). Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-16; Stage 17 step 10 and
  decisions 24 to 27; `runbooks/sagemaker-ai-ml.md` §W and §G.
  **Measured on a worker 2026-11-22** (Stage 17 10.4 step 3): `probes/operator.yaml`, imported in the portal's
  editor, ran as `app-genai-dev`'s project role. Its one `InvokeModel`, at 19:43:02, named the application
  inference profile alone, with no guardrail, and its user agent `Caller/BedrockInvokeModelOperator`. The task
  log held the prompt and the response in full: *"Bedrock <profile ARN> prompt: {…}"* and *"Bedrock model
  response: {…}"*. With `SUP-459`'s deny applied, both later runs failed on that call's `AccessDeniedException`.
  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

### Provisioned MWAA

- `SUP-279` **`airflow:CreateEnvironment` authorizes before it validates the network configuration**
  (measured 2026-10-18, Stage 10 4.3). A call naming two subnets of Production, a security group, a role and
  a bucket that do not exist read the root baseline's `DenyProvisionedMwaa` with the policy id, so the deny
  is attributable without a valid environment. Where: the Stage 10 log.

## The SMUS CI/CD CLI

- `SUP-280` **`aws-smus-cicd-cli` 1.0.9's pre-deployment validation simulates the caller's policies with no
  context keys, so every conditioned SCP reads as a deny** (measured 2026-10-15 in Sandbox, D41's lab). The
  validation, the `--dry-run` engine, calls `iam:SimulatePrincipalPolicy` without context entries: the
  Control Tower Region control without `aws:RequestedRegion` and `DenyS3ObjectWriteOutsideOrganization`
  without `aws:ResourceOrgID` both read denied, and the deploy of 15:46 UTC aborted with nothing written.
  The same simulation with the keys the real call carries answered `allowed` on every action, and the
  simulation never covers a bucket policy or a key policy. A deploy under conditioned SCPs therefore runs
  with `--skip-validation`. In the same lab `--no-events` kept the CLI's `PutEvents` off the `default` bus,
  and the CLI's boto3 read no credential the `aws` CLI's SSO login had cached. Where:
  `decisions/D41-sagemaker-application.md`; `docs/SMUS.md`, the CI/CD tool section;
  `runbooks/sagemaker-application.md` §D.

- `SUP-281` **`aws-smus-cicd-cli` 1.0.9 names a workflow by mapping every character outside `[A-Za-z0-9_]`
  to `_` at creation, while `run` and `destroy` map only `-`** (read 2026-10-18 in the CLI's code, Stage 18
  0.1). A workflow is created as `<application>_<project>_<workflow>` (`commands/deploy.py:2165-2189`);
  `run` (`commands/run.py:557-563`) and `destroy` (`helpers/destroy_validator.py:437`) derive the name by
  replacing `-` alone, so a manifest name holding a dot or another character is created under one name and
  found by neither command (inferred from the code; only hyphenated names were run). The workflow is created
  with no `TriggerMode`, so `manual_only`, and the tags `Pipeline` (the application), `Target` (the
  project), `STAGE`, `CreatedBy=SMUS-CICD`, `AmazonDataZoneDomain` and `AmazonDataZoneProject` (measured
  2026-10-15); two applications in one project differ by `Pipeline` alone, which `monitor` filters on.
  Where: `log-stage-18-staging-deployment-project.md`, 2026-10-18; `runbooks/sagemaker-application.md` §R.

- `SUP-282` **`aws-smus-cicd-cli` 1.0.9 refuses every command while any `${VAR}` of the manifest is unset,
  and writes each `{env.VAR}` into the workflow as `{{ params.VAR }}` with no default** (read in the CLI's
  code 2026-10-15 and 2026-10-26; measured 2026-10-26, Stage 10 2.1 and xxix). `find_missing_env_vars` tests
  `not os.getenv` over the whole manifest, other stages' variables included, so a `dev` deploy sets every
  stage's names. The deployed definition holds no value; only `run` fills the parameters, as
  `OverrideParameters` from the stage's `environment_variables`. A run of such a workflow started from the
  portal carried the service's own `mwaa_serverless_workflow_id` alone and failed before any task: *"User
  template error: DAG template rendering failed: 'dict object' has no attribute 'SUBNET_AZ1'"*. A
  `start-workflow-run` passing the parameters as `OverrideParameters` succeeded on 2026-10-19 with no
  DataZone call, the service calling `kms:GenerateDataKey` and `kms:Decrypt` on the project key under the
  starter's session. Where: `log-stage-10-orchestration-promotion.md`, 2026-10-26;
  `log-stage-18-staging-deployment-project.md`, 2026-10-19.
  **Read again 2026-11-22** (Stage 17 9.6 and 10.4): a value changed in the working copy reaches the next
  `run` with no deploy. `TRAINING_IMAGE_URI` corrected to the pinned digest in the sourced `.env` made the next
  `app-ml-train` job run on the digest, and `EXPECT_UNGUARDED` set to `refused` on the manifest's `dev` stage
  made `app-genai-probe` expect the refusal. The files a deploy wrote stay as deployed: the guardrail definition
  restored in the working copy alone left the deployed one in force. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-283` **`aws-smus-cicd-cli` 1.0.9's `bundle` reads an `include` entry as a file or folder, never a
  glob, and exits 0 when it matches nothing** (measured 2026-10-16 offline, Stage 8 2.5). With the
  manifest's `code` item as `include: ["code/*.zip"]` and the zip present, `bundle` printed `Warning:
  Pattern not found: code/*.zip` on stderr and `Bundled 0 files for 'code'`, exited 0 and wrote a 5,609-byte
  bundle without the zip. In `commands/bundle.py` an include is tested with `os.path.isfile` or
  `os.path.isdir`, while `commands/deploy.py` expands the same entry with `glob.glob`, so a manifest that
  deploys correctly can bundle incompletely. With `include: [code/app-etl.zip]` the bundle held the zip
  (6,968 bytes). With no credentials the domain lookup logged three `ERROR` lines (`Unable to locate
  credentials`) and the bundle went on. A pipeline that trusts the exit code ships a bundle missing files.
  Where: `log-stage-08-cicd-pipelines.md`, 2026-10-16.

- `SUP-284` **`aws-smus-cicd-cli` 1.0.9 creates a SageMaker Unified Studio project when a stage says
  `project.create: true`, and its `destroy` deletes it** (read 2026-10-17 and 2026-10-18 in the CLI's code,
  Stage 18 0.1). AWS's guide says the CLI deploys only into projects that already exist. With `create:
  false` a missing project stops the deploy, *"Project '…' not found, make sure the SMUS project is
  pre-created manually before using the SMUS CLI"*; with `create: true` it calls `CreateProject`
  (`helpers/project_manager.py`), and `destroy` deletes the project (`helpers/destroy_executor.py`). A
  profile name the domain does not list falls back to the first profile listed, with a printed warning, and
  the deploy goes on. `destroy` deletes no IAM role, and no call enables a blueprint. The sdist was read,
  nothing executed. Where: `log-stage-18-staging-deployment-project.md`, 2026-10-18; `docs/SMUS.md`, the
  CI/CD tool section.

- `SUP-285` **`aws-smus-cicd-cli` 1.0.9's `workflow.create` creates a workflow with no
  `NetworkConfiguration` and no `EncryptionConfiguration` when its identity cannot read the project's
  network and key** (read 2026-10-18 in the CLI's code, Stage 18 0.1). The action takes the subnets,
  security group and key from a domain-scoped VPC connection or from the `Tooling` environment's
  `privateSubnets`, `securityGroup` and `kmsKeyArn`; when neither can be read it prints one line and creates
  the workflow in MWAA Serverless's default worker network under a service-managed key
  (`helpers/datazone.py`, `bootstrap/handlers/workflow_create_handler.py`, `helpers/airflow_serverless.py`).
  Upstream issue 318 shows it on a deploy role refused `ListEnvironmentBlueprints`. The key is fixed at
  creation, and MWAA Serverless's IAM carries only tag condition keys, so no SCP can require a network on
  `CreateWorkflow`. A deploy role that was not a project member, measured in Staging on 2026-10-21, never
  reached the fallback: each storage item stopped on a refused `ListConnections`, before `workflow.create`.
  Read 2026-11-13 on the repository's `main` (`cdb8e3c18f`), whose `src/` tree is 1.0.9's, nothing executed:
  unchanged. The handler prints a line for each half, *"No custom VPC config on Tooling blueprint; using
  default worker VPC"* and *"No custom CMK on Tooling blueprint; using default encryption key"*, and
  *"Workflows will use Tooling VPC config"* only when it read both the subnets and a security group. It seeks
  the Tooling environment through the managed blueprints named `Tooling.GA` and `Tooling.Lightning`, then
  through the project's IAM connection (`ListConnections`, type `IAM`).
  Where: `upstream-releases.md`, the CI/CD CLI table; `log-stage-18-staging-deployment-project.md`,
  2026-10-21.

- `SUP-286` **`deploy` reads a manifest's local content from the manifest's folder, whatever
  `--bundle-archive-path` names, and the catalog from that archive alone** (the first measured 2026-10-19,
  Stage 18 4.2, `aws-smus-cicd-cli` 1.0.9; the second read 2026-11-11 in its `commands/deploy.py`, no call
  made). A `content.storage` item that names no connection is copied from the folder the manifest sits in;
  run from a checkout with a release's bundle, the deploy wrote the checkout's files and none of the
  bundle's. A promotion that deploys a stored bundle extracts it and puts the stage's manifest beside it.
  The catalog import takes the other road: `_import_catalog_from_bundle` opens the zip the option names, or
  the one found under `./artifacts` when the manifest has bundle items, and reads
  `catalog/catalog_export.json` inside it. With no archive, with no such member, or with the stage's
  `deployment_configuration.catalog.disable` true, it imports nothing and returns success. A leg that
  promotes files and catalog gives the CLI both: the extracted files beside the manifest and the archive's
  path. Where: `log-stage-18`'s 4.2 entries; `log-stage-19-smus-native-data-product.md`, 2026-11-11.

- `SUP-287` **`workflow.create` and the operator-code lookup scan the project's whole shared root, whatever
  `targetDirectory` says** (measured 2026-10-19, Stage 18 5.2, the same version). The scan's prefixes come
  from `target_directory`, a name the manifest's `StorageConfig` does not carry, so they fall back to the
  root, and the first file in S3's listing order wins each workflow name or DAG id. An application whose
  workflow reused `app-etl`'s name and DAG id read and rewrote `app-etl`'s YAML, was created from
  `app-etl`'s definition, and its `destroy` plan then held `app-etl`'s Glue job, since `destroy` reads the
  Glue jobs from the workflow's definition as the service holds it. The open upstream PR #369, read
  2026-11-13 at `ac3ba5556d`, rewrites `_derive_workflow_search_prefixes` to read `targetDirectory` on the
  stage's storage and git items: the scans would read each of those directories in the stage's order and the
  shared root last. Unmerged, and `main`'s code is 1.0.9's. Where: `log-stage-18`'s pass 5 entry;
  `upstream-releases.md`, the CI/CD CLI table.

- `SUP-348` **`deploy` uploads an application's files to the project's shared root and deletes none the
  new bundle lacks** (measured 2026-11-10 in Sandbox, Stage 19 pass 1, the same version). Run 1's
  package carried ten AppleDouble files (`._*`, 163 bytes each), which macOS's `tar` wrote and its `tar -t`
  does not list; the deploy at 01:57 UTC uploaded them with the 11 real files (*"Total files deployed:
  21"*). Three later deploys, at 02:29, 03:07 and 03:40 UTC, carried 11 files each, and after them the ten
  objects were still under `shared/app-etl/`, in `glue/`, `inbox/`, `src/` and `workflows/`. Since the
  workflow scan reads the whole shared root (`SUP-287`), a file an application drops stays in the scan
  until it is deleted by hand. Spark's listing skipped `inbox/._trades.csv`: each Glue run read the
  sample's 10 rows. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-10.

- `SUP-351` **`deploy`'s catalog import first checks the target project's domain unit for a
  `CREATE_GLOSSARY`, a `CREATE_FORM_TYPE` and a `CREATE_ASSET_TYPE` grant, adds the missing ones as the
  identity that deploys, and aborts the import when it cannot** (read 2026-11-11 in the CLI 1.0.9's
  `helpers/catalog_import.py`, `_ensure_import_permissions`; no call made). For each of the three types it
  calls `ListPolicyGrants` on the unit and takes a non-empty `grantList` as granted, whoever the grant
  names; an `AccessDeniedException` on the listing reads as not granted. For a missing type it calls
  `AddPolicyGrant` with the target project's `OWNER` designation as principal, and a failure there raises
  *"Catalog import aborted — could not add required policy grants"* before any asset is read. The bundle's
  content does not enter the check: a bundle with one asset and no glossary takes the same path. On
  2026-11-11 this domain's root unit held one `CREATE_FORM_TYPE` grant and none of the other two
  (`list-policy-grants`, measured), so a first import by a deploy role, which holds no `AddPolicyGrant`
  and owns no domain unit, would abort. The catalog guide says the import creates what the target lacks
  and does not name the grants. `data-governance/governance/`'s `catalog_import_projects` declares the
  three per deployment project. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-11;
  `terraform-live/data-governance/governance/grants.tf`.

- `SUP-352` **`bundle` exits 0 and writes the bundle when its caller cannot read the stage's project,
  and when the catalog export fails** (the first measured 2026-11-11, the second read the same day in
  the CLI 1.0.9's `commands/bundle.py` and `helpers/utils.py`, no call made). Run on the laptop as
  Sandbox's InfrastructureAccess with the `dev` stage naming `governed-lake`, a project that identity
  is no member of: `ListConnections` was refused *"User is not permitted to perform operation:
  ListConnections"*, the CLI logged *"ERROR - Failed to get project connections for governed-lake"*,
  and the archive was written with the same 11 files as the run that named a project the caller
  belongs to, whose log carries no such line. `get_datazone_project_info` catches every exception and
  returns an error record the command never reads. The catalog export runs inside a `try` whose handler
  prints *"Error exporting catalog resources: <error>"* and continues, and a domain or project id it
  cannot resolve prints a warning the same way; neither changes the exit status. A bundle made by an
  identity that lacks a catalog read, or that is no member of the source project, therefore carries
  the files and no `catalog/catalog_export.json`, and the target's import finds nothing to import. A
  pipeline that depends on the project's read or on the export checks the log and the archive. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-11; `examples/app-etl/.gitlab-ci.yml`, the job
  `bundle`.

- `SUP-357` **`deploy` reports a catalog import as failed only when every item it attempted failed**
  (read 2026-11-11 in the CLI 1.0.9's `commands/deploy.py`, `_import_catalog_from_bundle`; no call made).
  After the import it prints *"Catalog import completed"* with five counts, `Created`, `Updated`,
  `Skipped (extra in target)`, `Failed` and `Published`, and returns failure only if the sum of created,
  updated and failed is above zero and equals the failed count, printing *"All catalog imports failed"*.
  Any other mix returns success and the deploy's exit status with it: one asset created and the rest
  failed is a successful deploy. A leg that promotes a catalog reads the `Failed:` count from the log, or
  the target project's assets afterwards. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-11.

- `SUP-369` **A catalog import creates neither the asset nor the data product in a second project of the
  domain: `CreateAsset` with the source's `externalIdentifier` and `CreateDataProduct` with the source's
  name are each a `ConflictException`, which the CLI 1.0.9 counts as an update** (measured 2026-11-15,
  Stage 19 release F, pipeline #123's `staging-deploy`; the data product 2026-11-16, pipeline #129's
  `staging-catalog`).
  The import of `app-etl-dev`'s `trades_notional` into `deploy-staging` called `CreateAsset` with the
  source's `externalIdentifier` unchanged, `arn:aws:glue:us-west-2:<Sandbox>:table/app_etl/trades_notional.<app-etl-dev's
  project id>`, and DataZone answered `ConflictException`, CloudTrail carrying no `errorMessage`.
  `deploy-staging` held no asset: that call is the only `CreateAsset` into it in CloudTrail since
  2026-11-09, and its source's runs had added 0. Two projects already held an asset named
  `trades_notional`, so the conflict is the identifier, not the name. `_import_resource` logs *"Resource
  trades_notional already exists (ConflictException), treating as update"* and returns success with no
  target id recorded, so the data product's item keeps the source asset's id and `CreateDataProduct`
  answers *"ValidationException: Resource asset provided is not from same project"*. The summary reads
  *"0 created, 1 updated, 0 skipped (extra in target), 1 failed, 0 published"* and the CLI exits 0
  (`SUP-357`). A target's asset can therefore come only from its own source; a later import maps the
  source's asset to it by name, `_build_identifier_map`'s fallback (read in the code, not measured).
  Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15.
  Read again 2026-11-16 (pipeline #129's `staging-catalog`, `v0.5.2`'s `--catalog-follow-up`): the
  target's source, started by the deploy role at 02:07:53 UTC, imported `trades_notional` (run
  `cntcrgrt3c22og`, `added: 1`), and the second import remapped the `DataSourceReferenceForm` to that
  source and revised the target's asset `as6m73yp8shr80` by name, `CreateAssetRevision` to revision 2,
  with no `CreateAsset`. The data product failed on its name: `CreateDataProduct` in `deploy-staging` over
  `as6m73yp8shr80` answered `ConflictException`, *"Conflict with dataProduct 5070mjwdvjwp3k"*,
  `app-etl-dev`'s product of the same name; `CreateDataProduct`'s prerequisites state a data product's
  name unique within the domain. The CLI logged *"Resource trades-notional already exists
  (ConflictException), treating as update"*, the summary read *"0 created, 2 updated, 0 skipped (extra in
  target), 0 failed, 0 published"*, and `deploy-application.py` passed. A data product the CLI promotes
  between projects of one domain reaches no target while the source holds it, and the summary counts the
  miss as an update. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15; Stage 19 decision 26.

- `SUP-374` **`bundle` reads a storage item that names a connection from the stage's project, with its
  caller's credentials through the `aws` CLI, and neither `bundle` nor `deploy` fails where that item is
  missing** (read 2026-11-17 in the released wheel of `aws-smus-cicd-cli` 1.0.9,
  `aws_smus_cicd_cli-1.0.9-py3-none-any.whl`, whose SHA-256 `bd7258c0…4903` is the one the house image's
  lock and the deploy image's requirements hold; no call made, Stage 17 pass 9). In
  `commands/bundle.py`, an item whose `connectionName` is not among the stage's connections prints
  *"Warning: Connection '<name>' not found for storage item '<item>'"*, and one whose connection carries
  no `s3Uri` prints *"Warning: No S3 URI found for connection '<name>'"*; each skips the item. Otherwise
  `list_s3_contents` (`helpers/deployment.py`) pages `ListObjectsV2` over the connection's whole
  location and prints every key as a tree, and a `ClientError` there prints *"❌ Error accessing S3:
  <error>"* and the command goes on. Then `download_s3_files` runs the `aws` CLI as a subprocess for
  each `include`: `aws s3 cp` for an entry whose last segment holds a dot, otherwise
  `aws s3 sync s3://<bucket>/<location><include>/` into the bundle's folder of the item's name, with
  `*.pyc`, `__pycache__/*` and `.ipynb_checkpoints/*` excluded; an entry that is `*`, or an item with no
  `include`, syncs the whole location. The location and the include are joined with no separator of
  their own, and the files land under the item's name without the include's path. A call that returns
  non-zero prints *"Error copying file: <stderr>"* or *"Error syncing <include>: <stderr>"*, and the
  item counts no file. The zip is written from the files alone, so an item that read nothing leaves no
  member, and `bundle` exits 1 only where the whole bundle holds no file (*"❌ No files found"*). In
  `commands/deploy.py`, `manifest_requires_bundle` (`helpers/bundle_storage.py`) is true where a storage
  item names a connection or the manifest has a `git` item, and a deploy that finds no bundle then stops
  with *"No bundle file found in ./artifacts directory"*. `_deploy_named_item_from_bundle` prints *"No
  files found for '<item>' in bundle"* where the zip lacks the item's folder and returns an empty list,
  which `storage_success` counts as success. An item that names no connection takes the other road, the
  manifest's folder (`SUP-286`). The consequences: what such an item puts in a release comes from a
  project and not from the tag, and is whatever the prefix holds when `bundle` runs, read as `bundle`'s
  caller; the exit status of either command says nothing of it, as `SUP-352` found for the project's
  read and the catalog's export, so a pipeline that promotes such an item checks the archive; the
  `bundle` job's log holds a listing of the connection's whole location unless its caller is refused the
  listing; and a manifest with such an item needs a bundle before every `deploy`, `dev`'s included. Not
  read: `upload_bundle`, `display_bundle_tree` and what `deployment.deploy_files` sends for the item in
  a target. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-17; Stage 17 pass 9, "The model
  in the bundle, and what the CLI does with it", and verification lxii; `runbooks/sagemaker-ai-ml.md`
  §B.
  **Read again 2026-11-22** (Stage 17 9.6, `bundle --targets dev` from a space as `app-ml-dev`'s project
  role through `scripts/dev-cli.sh`):
  - `bundle` never reads the connection. It copies the stage's domain `region`, `name` and `tags` into its
    configuration, not its `id`.
  - `get_datazone_project_info` then resolves the domain through `datazone.resolve_domain_id`, a
    `ListDomains` that DataZone refuses to a project role: *"User is not permitted to perform operation:
    ListDomains"*, logged three times as `ERROR`.
  - The project's connections come back empty. The `model` item, which names `default.s3_shared`, is
    skipped with the warning above. This happened before the training run (18:45:20) and after it
    (19:57:48), with `latest/` present in the prefix.
  - The archive held the 10 files of the items read from the manifest's folders (15,592,181 and 15,592,095
    bytes), and the command exited 0.
  - `scripts/dev-cli.sh` answers `get_domain_id_by_name`, which this path does not call. The bundle role
    holds `datazone:ListDomains`.
  - `deploy` with no archive in `./artifacts`, as the same role at about 20:41, read the project and its
    connections, printed the storage items and stopped with *"❌ Error: No bundle file found in ./artifacts
    directory"* and *"❌ Error: Deployment failed: 1"*, exit 1. The trail holds no management write from it.
  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-375` **`aws-smus-cicd-cli` 1.0.9's `deploy` adds a stage's `owners` and `contributors` to an
  existing project at every run and removes no member, and acts on the project role only under
  `project.create: true`** (read 2026-11-17 in the released wheel, SHA-256 `bd7258c0…4903`, whose
  `helpers/project_manager.py` and `helpers/context_resolver.py` are byte-identical to `main` at
  `cdb8e3c18f`; nothing executed, Stage 19). Every `deploy` calls `ensure_project_exists`
  (`commands/deploy.py`), and for a project that exists `_update_existing_project` runs. It lists the
  project's members and calls `CreateProjectMembership` for each `owners` or `contributors` entry absent,
  as `PROJECT_OWNER` or `PROJECT_CONTRIBUTOR`: an entry starting `arn:aws:iam::` resolves to the role's
  group and any other to a user by name, a `:*:` account in an ARN becomes the caller's, and a member
  present with the other designation is left as it is, with *"⚠️ <member> exists with different role:
  <designation>"*. No call removes a member, and a refused call prints *"❌ Failed to add owner <member>:
  <error>"* while the deploy goes on. `project.create` is false by default
  (`application/application_manifest.py`). Under `create: true` the same function then acts on the role:
  with `role.arn` and at least one `role.policies` ARN it attaches each policy not yet attached and writes
  the inline policy `SelfPassRolePolicy`, `iam:PassRole` and `iam:GetRole` on the role itself, at every
  deploy, detaching nothing; with `role.arn` alone it does nothing; with no `role.arn` it creates
  `role.name`, by default `smus-<project>-role`, with a trust policy for ten service principals under
  `aws:SourceAccount` and the tag `CreatedBy=SMUS-CICD`, then waits 90 s, or updates a role of that name
  that carries the tag. That role is not attached to the existing project: the CLI passes `role.arn` only
  when it creates the project, as `customerProvidedRoleConfigs` with designation `PROJECT_OWNER`. The
  manifest schema page shows `role.arn` and `role.policies` with no condition on `create`, and the
  README's examples carry `owners` and `role.arn` on stages that set no `create`. The consequences:
  `owners` and `contributors` in a manifest are a membership grant the deploying role makes at every
  deploy, made again after a removal by hand, and that role needs `datazone:CreateProjectMembership` for
  it; a `role` under a stage whose `create` is false does nothing; and `create: true` makes every deploy an
  IAM write in the target account. `app-etl`'s manifest names no `owners`, `contributors`, `role` or
  `create`, so its `deploy` makes no membership or IAM call, and the project roles' policies stay
  Terraform's (open question 27). Where: `log-stage-19-smus-native-data-product.md`, 2026-11-17; Stage 19
  decision 15.

- `SUP-389` **`aws-smus-cicd-cli` 1.0.9's catalog import points an asset at the target project's source
  whose filter names the asset's database, and falls back to a source by position when none does or the
  asset carries no `GlueTableForm`** (read 2026-11-19 in the released wheel unpacked in the laptop's `uv`
  cache, `helpers/catalog_import.py` matching the wheel's `RECORD`, `sha256=NPf0CALj…Ihk`; nothing
  executed, Stage 20 8.3). For an asset's `amazon.datazone.DataSourceReferenceFormType`,
  `_resolve_target_data_source` lists the target project's sources in one `ListDataSources` call of
  `maxResults=25`, reading no next page, and keeps those of the form's `dataSourceType` (`GLUE` by
  default) that are `READY` or `RUNNING`. It returns the first whose `relationalFilterConfigurations` name
  the asset's `databaseName`, else the last whose filter is `*`, else `candidates[0]`; a source whose
  `GetDataSource` fails is skipped. The database comes from the asset's `GlueTableFormType` form alone, so
  an asset with none, a view's `GlueViewFormType` among them, takes `candidates[0]` directly. The form then
  names that source, and its latest run when that run is `SUCCESS`. With no candidate the form is
  stripped: *"No matching <type> data source in target project (db=<database>), stripping
  DataSourceReferenceForm"*. The order `ListDataSources` returns is undocumented, and the CLI's pages do
  not describe the remap. The consequences: in a deployment project holding several applications'
  sources, a table asset reaches its own database's source, since each source `create-environment` makes
  filters on its database alone; a view, an asset of another form, or a project past 25 sources takes a
  source by position (Lesson 73). Release F's import of 2026-11-15 logged its remap to `52f18khk7kdi4w`,
  the source over `app_etl`, the project's only one. Where: `log-stage-20-dbt-lineage.md`, 2026-11-19;
  `log-stage-19-smus-native-data-product.md`, 2026-11-15.

- `SUP-454` **`aws-smus-cicd-cli` 1.0.9's catalog import writes the source project's table into the target's
  asset, and the target's own data source writes the target's table back at its next run** (read 2026-11-22
  in Staging and Production, Stage 19 step 8 of the order). Each `deploy`'s import revises the target's
  asset by name with the bundle's `GlueTableForm` and `AssetCommonDetailsForm` `sourceIdentifier`:
  `app-etl-dev`'s table, Sandbox's catalog id and table ARN, its S3 location and its `updateTime`, while the
  asset's `externalIdentifier` stays the target's table. Measured on both releases that imported:
  `deploy-staging`'s revisions 2 (2026-11-16) and 4 (2026-11-22, 04:12:01 UTC) by `awsds-deploy-staging`,
  `deploy-production`'s 2 and 5 (04:47:12 UTC) by `awsds-deploy-prod`. The target's source, with
  `publishOnImport` false, rewrote those forms with its own table at its next run and kept the description,
  the `classification` form and the subscription terms the import wrote: a scheduled run (Staging, 15:37:24
  UTC, `updated: 1`) or the `publish` task's run (Production, 05:03:20 UTC, four seconds before its
  listing). So the first scheduled run after an import reads `updated: 1` where nothing ran the source
  since, and `unchanged: 1` every other day. Between an import and the source's next run the asset names
  another account's table, and a listing made in that window publishes that table's location and ARN.
  Where: `log-stage-19-smus-native-data-product.md`, 2026-11-22.

## Bedrock

The Bedrock IDE, SageMaker Unified Studio's builder of Bedrock components, is recorded under
[DataZone and SageMaker Unified Studio](#datazone-and-sagemaker-unified-studio), *The Bedrock IDE*: `SUP-410`
and `SUP-411` (a knowledge base on S3 Vectors: the key statement its index needs, and the index's filterable
metadata), `SUP-417` (a guardrail: `kms:CreateGrant` on the project key), `SUP-418` and `SUP-419` (an
evaluation: the sampling parameters Claude Haiku 4.5 refuses, and its datasets), `SUP-445` (the names),
`SUP-446` (the chat agent on Agents Classic), `SUP-447` (a flow's role with no boundary) and `SUP-448` (a flow
deployed by each test). `SUP-426`, below, is the endpoint id its knowledge base's calls carry.

- `SUP-288` **The Bedrock use-case form is stored as double base64 over a flat JSON object, and one
  submission covers every model** (measured 2026-09-11, Stage 6e M2). `PutUseCaseForModelAccess` and
  `GetUseCaseForModelAccess` declare `formData` an opaque blob, and the CLI prints its outer layer; `base64
  -d | base64 -d` gives six fields, `companyName`, `companyWebsite`, `intendedUsers`, `industryOption`,
  `otherIndustryOption` and `useCases`. The console's submission left `useCases` starting with `. ` while
  `otherIndustryOption` was empty, consistent with the two sharing one input (seen once, inferred). Neither
  call takes a `modelId`, in the path or the body, so the form is account-level. Before a submission the
  read answers *"ResourceNotFoundException: You have not filled out the request form."*
  `aws_bedrock_use_case_for_model_access` has one required attribute, `form_data`. Where:
  `log-stage-06e-claude-code-bedrock.md`, 2026-09-11; `runbooks/claude-code-sagemaker.md` M2.

- `SUP-289` **No Bedrock API exposes which data retention modes a model permits (`allowed_modes`)** (read
  2026-09-11 in the service models of AWS CLI 2.36.18, Stage 6e 7.2). No shape or member matching `allowed`
  exists in any of the eight `bedrock*` service models, and `get-foundation-model`,
  `list-foundation-models`, `get-foundation-model-availability` and the agreement offer's `termDetails`
  carry nothing about retention. The account-level enum read `default`, `none`, `provider_data_share` and
  `inherit` (*"no data retention mode is set at this scope"*); the model shipped with CLI 2.37.12 adds
  `aws_review`. A Region never set reads `mode: inherit` with no `updatedAt`. With the mode at `none`,
  `get-foundation-model-availability` read `AUTHORIZED / AVAILABLE / AVAILABLE` for all thirteen Anthropic
  models, the two the vendor names as retaining included, as before. Only an invocation can show a model the
  mode makes unavailable. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-09-11; `aws/bedrock.py`;
  `upstream-releases.md`.

- `SUP-290` **A SageMaker Unified Studio project role's managed policies allow `bedrock:InvokeModel*` on
  foundation models only when the request names an inference profile, and on no system-defined profile**
  (read 2026-09-11, refusal measured 2026-09-12 from a space, Stage 6e 3.1). Of the three AWS-managed
  policies on the role, the one matching allow, `BedrockModelInvocationPermission` in
  `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy`, covers `foundation-model/*` under `Null:
  {bedrock:InferenceProfileArn: false}`; `BedrockInvokeModelPermissions` requires an application inference
  profile, `InvokeBRModel` the role tag `EnableAmazonBedrockIDEPermissions`, and `ListInferenceProfiles` is
  granted nowhere. `InvokeModel` on the bare `amazon.nova-lite-v1:0` was refused: *"no identity-based policy
  allows the bedrock:InvokeModel action"*. A project reaches a model through a system profile such as
  `us.anthropic.*` only with a grant on the profile ARN beside the managed policies. Where:
  `log-stage-06e-claude-code-bedrock.md`, 2026-09-11 and 2026-09-12; `runbooks/claude-code-sagemaker.md`,
  the grant.

- `SUP-291` **A cross-Region inference profile is authorized once per destination Region, and
  `aws:RequestedRegion` in that evaluation is the destination, not the caller's** (measured 2026-09-12,
  Stage 6e step 6). A call made with `--region us-west-2` and logged by CloudTrail with `awsRegion:
  us-west-2` was denied against `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-5` by
  Control Tower's `CT.MULTISERVICE.PV.1`, whose only condition is `aws:RequestedRegion != us-west-2`. No
  vendor page connects the two, and the consequence is that a Region ceiling refuses every cross-Region
  profile in the organization until the invoke actions are exempted. Where: `claude-code-sagemaker.md` M5.

- `SUP-292` **Bedrock's data retention mode is per account and per Region** (measured 2026-09-12). The
  account read `none` in `us-west-2` and `inherit` in the two Regions its own profiles route to;
  `get-account-data-retention` answers independently in each. A mode declared once is a claim about one
  Region, and whether cross-Region inference obeys the source Region's mode or the destination's is in no
  API and on no page. Where: `claude-code-sagemaker.md` M1, `AWS_STATE.md` `EXC-07`.

- `SUP-293` **The Bedrock use-case form does not enable a model; the agreement does** (measured 2026-09-12).
  With the form submitted and readable in all three Regions, `create-foundation-model-agreement` against an
  offer token was still required per model — the act the console calls *Enable specific models*.
  `agreementAvailability.status: NOT_AVAILABLE` means no agreement has been created, not *no agreement is
  needed*, and reading it the second way is what hid the omission through three separate readings. The
  agreement is account-wide: created in one Region it reads `AVAILABLE` in the others before the creating
  Region leaves `PENDING`. Amazon's own models need none. Where: `claude-code-sagemaker.md` M4. Read again
  2026-11-22 (Stage 6e decision 17): the agreements for Opus, Sonnet and Haiku 5.5, created through
  `us-west-2`, read one status in all three routed Regions at each reading. Opus 5.5 read `AVAILABLE`
  everywhere at the first reading, 02:13:31, 49 seconds after its CloudTrail event; Sonnet and Haiku 5.5 read
  `PENDING` everywhere at 02:13:31 and `AVAILABLE` everywhere by 02:14:13. The other Regions leading the
  creating one did not recur, so the order of the Regions is not a property. Where:
  `log-stage-06e-claude-code-bedrock.md`, 2026-11-22.

- `SUP-294` **A Bedrock model can be gated commercially with every readable instrument reporting it
  available** (measured 2026-09-12). `anthropic.claude-sonnet-5`: agreement `AVAILABLE`,
  `authorizationStatus AUTHORIZED`, `entitlementAvailability AVAILABLE`, `regionAvailability AVAILABLE`,
  `modelLifecycle ACTIVE`, form present — and `AccessDeniedException … not available for this account …
  contact AWS Sales` for every principal including `AdministratorAccess`, while the previous generation
  answered. The invocation is the only instrument that answers whether a model can be used, which is Lesson
  13 at account scale. Where: `AWS_STATE.md` `EXC-08`. The gate follows the shape of the model id (measured
  2026-09-12, Stage 6e step 6): dated ids (`…-2025xxxx-v1:0`) invoked once their agreement was accepted, and
  clean ids (`claude-sonnet-5`, `claude-opus-5`, `claude-opus-4-6/4-7/4-8`, `claude-sonnet-4-6`,
  `claude-fable-5`, `claude-fable-5-1`) did not. `agreementAvailability: NOT_AVAILABLE` means no agreement
  has been created, not that none is needed: a live offer existed for each model. An agreement is per model
  and account-wide: Sonnet 5's went `PENDING` to `AVAILABLE` within seconds, `us-east-1` and `us-east-2`
  reading `AVAILABLE` before the creating Region left `PENDING` (not repeated on 2026-11-22, `SUP-293`),
  while Sonnet 4.5's took minutes;
  `amazon.nova-lite-v1:0` needed none. The grant, the endpoint policy, the SCP and the use-case form were
  each eliminated by measurement. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-09-12. Read again
  2026-11-22 (Stage 6e decision 17): Opus, Sonnet and Haiku 5.5, ids without a date, were refused to the
  infrastructure user at 02:37:50 to 02:37:52 and again at 02:44:04 to 02:44:06 with the same
  `AccessDeniedException`, *"anthropic.claude-opus-5-5 is not available for this account …"*, the
  agreements `AVAILABLE` in all three routed Regions since 02:14 and the SCP naming the ids since 02:37:30.
  Haiku 4.5 answered the same night. The shape rule holds for a third generation. Where:
  `log-stage-06e-claude-code-bedrock.md`, 2026-11-22.

- `SUP-295` **A streaming Bedrock invocation writes two CloudTrail events; a non-streaming one writes one**
  (measured 2026-09-12). `InvokeModelWithResponseStream` records one event carrying
  `requestParameters.modelId` and a sibling carrying `requestParameters: {}` — 9 and 9 in one hour — while
  `InvokeModel` records a single event, 4 with a `modelId` and none without in the same hour. Counting
  events doubles a streaming client's calls; counting events that name a `modelId` and carry no `errorCode`
  counts each invocation once, and it equals CloudWatch's per-model `Invocations` exactly (22/20/3 over one
  evening). `responseElements` is `null` on both, which is the attribution-without-content property Stage 6e
  4.6 claims, measured. A denied call reaches CloudTrail with no `modelId` at all, so refusals cannot be
  attributed to a model there — and they do not reconcile with CloudWatch either: one hour held 18
  `AccessDenied` events against 6 `InvocationClientErrors`, a metric AWS publishes only without a `ModelId`.
  A portal-playground call through an application inference profile writes an `AwsApiCall` and an
  `AwsServiceEvent` of the same name in the same second (read 2026-10-19 in Sandbox's trail, Stage 17 7.3).
  Haiku 4.5's `ConverseStream` at 22:08:48 carried as `modelId` the profile's ARN,
  `application-inference-profile/cp0gmvjv1h8q`, with `inferenceRegion` `us-east-2`, resource
  `foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0` and host
  `bedrock-runtime.us-west-2.amazonaws.com`; the service event named the same model. A count keyed on
  `modelId` sees a profile ARN there, not a model id. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-10-19. Read again 2026-11-22 (Stage 6e decision 17): `InvocationClientErrors` carries a `ModelId`
  series for an application inference profile, `ljl42zoh6e4v`, beside the dimensionless one, with one error
  at 02:07 in both; a refusal by the commercial gate writes neither an event nor a datapoint (`SUP-427`).

- `SUP-296` **CloudWatch carries a cross-region profile's tokens in the source Region, with invocation
  logging off** (measured 2026-09-12). `AWS/Bedrock` publishes `Invocations` and four token counts per
  `ModelId` — the `us.` profile id — in `us-west-2`, whichever Region processed the prompt; the
  dimensionless series equals the per-model sum for all four token metrics. The Control Tower Region ceiling
  refuses `cloudwatch:ListMetrics` in `us-east-1` and `us-east-2`, so nothing else could have been read. And
  `ListMetrics` names only series with data in the last two weeks. Where: `aws/bedrock-usage.py`. The
  dimensionless `Invocations` series equals the per-model sum plus `InvocationClientErrors`, which has no
  `ModelId` series: 66 = 60 + 6 (measured 2026-09-12). CloudWatch does not separate a 5-minute cache write
  from a 1-hour one, whose rate is higher (Opus 4.5: 11.00 against 6.875 USD per million tokens); Cost
  Explorer's usage types separate them, a day late. Where: `aws/bedrock-usage.py`, `BU-3`;
  `runbooks/claude-code-sagemaker.md` §V.

- `SUP-297` **`PutAccountDataRetention` publishes `bedrock:DataRetentionMode` at request time** (measured
  2026-09-12 in `Policy Canary`), so a `StringNotEquals` deny on it is a mode ceiling and not a blanket deny
  on the action. A condition key being in a service's catalogue and a key being published by a given action
  are two claims, and `accessanalyzer validate-policy` answers only the first: it accepts a statement
  conditioned on a catalogued key whatever action it is written against. The second is a call, and the
  vendor documents neither. The mode enum is also four values — `default`, `none`, `provider_data_share`,
  `inherit` — where this plan had discussed two. Where: `claude-code-sagemaker.md` M3.

- `SUP-298` **`InvokeModel` refuses an application inference profile id that does not exist before it
  authorizes** (measured 2026-10-19, Stage 17 decision 11). As `InfrastructureAccess` in `Sandbox Account
  1`, with `DenyBedrockInvocationOutsideTheScopedModels` naming no `application-inference-profile`, the call
  answered `ValidationException`, *"The provided model identifier is invalid"* (21:33 UTC), and the
  battery's row had read that call as `ALLOWED`, `reached-authorization`. A profile the console minted was
  refused by that statement at 21:13, `InvokeModelWithResponseStream` as the playground's consumption role
  (7.3's first chat). The API reference and the troubleshooting page name both errors and neither the
  message nor the order. A probe of a statement on application inference profiles therefore needs an id the
  service minted (Lesson 21), and the battery carries no such row. Where:
  `log-stage-17-sandbox-machine-learning.md`, decision 11's entries of 2026-10-19, and the note on decision
  11 in `aws/probes/probes.py`.

- `SUP-299` **`ListInferenceProfiles` with no `typeEquals` returns the system-defined profiles alone**
  (measured 2026-10-19). In `Sandbox Account 1`, which held two application inference profiles, the call
  with no type returned 96 profiles, every one `SYSTEM_DEFINED`, and `--type-equals APPLICATION` returned
  the two. The API reference names both values and no default. Where: `aws/awslib/inferenceprofiles.py` asks
  for each type by name, for `aws/bedrock-usage.py` to rate a series published under an application
  profile's id, for `aws/bedrock.py` section 5 to list both types and for `aws/bedrock-scope.py`'s `BS-2` to
  read the declared `us.` profiles, which are `SYSTEM_DEFINED`.

- `SUP-300` **A Bedrock call through an application inference profile is authorized on the profile's ARN and
  then on the foundation model's, and the SCP denial names the pass that failed** (measured 2026-10-19 in
  Sandbox's portal playground, Stage 17 7.3). The playground's calls go through an application inference
  profile the console creates. With an SCP whose `NotResource` listed the system profiles and foundation
  models but no `application-inference-profile`, both models were refused
  `bedrock:InvokeModelWithResponseStream` on `application-inference-profile/<id>`. With
  `application-inference-profile/*` admitted, Claude Haiku 4.5 answered and Nova Lite, outside the scoped
  set, was refused on `arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-lite-v1:0` by the same
  policy. A ceiling that refuses the profile pass therefore hides whether the model pass holds. The browser
  called `bedrock-runtime` directly, with no `vpcEndpointId`, as the consumption role in a session named
  `<DataZone user>@<environment>`. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-10-19;
  `POLICIES.md`, `DenyBedrockInvocationOutsideTheScopedModels`. Read again over 2026-10-17 21:07 to
  2026-11-22 01:56 in Sandbox's trail (Stage 6e decision 13): the portal's Bedrock pages call the control
  plane from the browser too, as the project role from a public address with no `vpcEndpointId`:
  `ListPrompts` 11, `GetPrompt` 3, `CreatePromptVersion` 2, `ListIngestionJobs` 4, `GetIngestionJob` 11,
  `StartIngestionJob` 1, `ListEvaluationJobs` 3 and `ConverseStream` 2, every one answered. The consumption
  role's 15 `ListFoundationModels` came the same way. Where: `log-stage-06e-claude-code-bedrock.md`,
  2026-11-22. Read again 2026-11-22 (Stage 17 10.4 reading 5): with `awsds-sandbox-bedrock-application`'s
  deny on `app-genai-dev`'s project role, a chat on Nova Lite in that project's playground answered
  *"Ready."*. Its `ConverseStream` at 20:52:48 ran as the consumption role, from the browser, through the
  domain's profile `csu817ovl4kz` (tagged with the domain alone), with no `guardrailConfig`. An identity
  deny on a project role does not reach the playground. Where: `log-stage-17-sandbox-machine-learning.md`,
  2026-11-22.

- `SUP-301` **CloudWatch publishes a Bedrock call through an application inference profile under the
  profile's id, which names no model** (measured 2026-10-19 in Sandbox, Stage 17 7.3). Haiku 4.5's
  playground call appeared in `AWS/Bedrock` as `cp0gmvjv1h8q` (1 invocation, 13 tokens in, 4 out), and
  CloudTrail named it by the profile's ARN. The console's enable creates the profile
  (`bedrock:CreateInferenceProfile` as the person submitting, named after the domain id), copying the system
  profile (`cp0gmvjv1h8q`, three Regions) or the model (`csu817ovl4kz`, `us-west-2` alone); the profile
  lists the model ARNs it reaches but not what it copied. `ListInferenceProfiles` with no `--type-equals`
  returned 96 profiles, all `SYSTEM_DEFINED`. In the console's code a playground disable deletes the
  profile, so a later enable gives a new id and an old series no longer resolves to a model. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-10-19; `aws/bedrock-usage.py`.

- `SUP-426` **A knowledge base's model calls, at ingestion and from a flow's knowledge base node, are recorded
  with the `vpcEndpointId` of an endpoint this account does not own, and with no `vpcEndpointAccountId`** (read 2026-11-22 in Sandbox's
  trail, Stage 6e decision 13). A SageMaker Unified Studio knowledge base, created at 01:33:19 on 2026-11-22
  by `awsds-sandbox-smus-provisioning` from `datazone.amazonaws.com`, ran two ingestion jobs. Its 2,939
  `InvokeModel` calls on the application inference profile `p391nstyc81c`, 01:33:18 to 01:34:37, are the
  only Bedrock events from 2026-10-17 21:07 to 2026-11-22 01:56 that carry a `vpcEndpointId`. Each is
  recorded in the project role's session, with `invokedBy`, `sourceIPAddress` and `userAgent`
  `bedrock.amazonaws.com`. Each ingestion job's calls came in one session named `EmbeddingTask-<id>` through
  one endpoint id: 1,479 through `vpce-0d75040e827258f9d` and 1,457 through `vpce-046f1b5f53e3e98c7`. One
  call at the knowledge base's creation and one at each `StartIngestionJob`, in sessions named
  `BKB-CP-<knowledge base id>-<suffix>`, came through a third, `vpce-021c8cd79f64c2f84`.
  `describe-vpc-endpoints` finds none of the three in the account, whose four Bedrock endpoints carried no
  event. CloudTrail's record reference, at eventVersion 1.11, says that for events AWS originates through a
  service's VPC the field is *"usually `AWS Internal` or the service name"*, and it defines
  `vpcEndpointAccountId` (since 1.09) as the endpoint owner's account. These 1.11 records carried a `vpce-`
  id and no owner, as did every other event of the window. A count of calls through the account's endpoints
  therefore matches its own endpoint ids, never a non-null `vpcEndpointId`. With the portal's calls from the
  browser (`SUP-300`) and the blueprint's creates from `datazone.amazonaws.com`, no Unified Studio Bedrock
  feature reached Bedrock through this account's endpoints in those ten weeks, and an endpoint policy binds
  none of them. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-11-22; Stage 6e decision 13.
  **Read again 2026-11-22** (Stage 17 7.4b, Sandbox's trail): inside a flow whose knowledge base node
  answers from the same knowledge base, each question wrote `InvokeModel` on `p391nstyc81c` as the project
  role, the knowledge base's role, and `Converse` on the response model's application inference profile as
  the flow's execution role, the project's `AmazonBedrockServiceRole-*`, both invoked by
  `bedrock.amazonaws.com` through `vpce-0cf920938fc4d8fc6`, a fourth id the account does not hold
  (*"The Vpc Endpoint Id 'vpce-0cf920938fc4d8fc6' does not exist"*, `InvalidVpcEndpointId.NotFound`). The
  flow's prompt node, calling `Converse` as the same role on the same profile, carried no `vpcEndpointId`.
  `InvokeFlow`, `Retrieve` and `RetrieveAndGenerate` are data events, as Bedrock's CloudTrail page says, and
  `lookup-events` returns none. Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22.

- `SUP-427` **A Bedrock invocation refused by the commercial gate writes no CloudTrail event and no
  CloudWatch datapoint** (read 2026-11-22 in Sandbox, Stage 6e decision 17). The infrastructure user's six
  `InvokeModel` calls on `us.anthropic.claude-opus-5-5`, `-sonnet-5-5` and `-haiku-5-5`, at 02:37:50 to
  02:37:52 and 02:44:04 to 02:44:06, each answered `AccessDeniedException`, *"… is not available for this
  account …"* (`SUP-294`). Read at 03:25, event history held no `InvokeModel` between 02:30 and 03:00 in
  `us-west-2`, `us-east-1` or `us-east-2`, while it held Bedrock's `ListIngestionJobs` and `GetIngestionJob`
  of 02:42:07 and 02:42:08.
  `AWS/Bedrock` `InvocationClientErrors` in `us-west-2` held one datapoint from 2026-11-08 to 04:00, one
  error at 02:07 on the application inference profile `ljl42zoh6e4v`, and no series names a 5.5 id. The
  trail of 2026-09-12 agrees: the infrastructure user's Nova Lite at 06:32:23 and Sonnet 4.5 at 06:35:57
  are recorded, and the gate's refusal of `us.anthropic.claude-sonnet-5` in the same sitting is not. That
  day's 42 `AccessDenied` events on the two invocation APIs are 18 IAM refusals (*"no identity-based policy
  allows"*) and 24 SCP refusals (*"explicit deny in a service control policy"*), none of them the gate's,
  which the project role met twice from a space. Bedrock's CloudTrail page says CloudTrail *"captures all
  API calls for Amazon Bedrock as events"* and says nothing of a refused call. The client's error is the
  only record of the gate's refusal, so an absence of refusals in the trail or the metric does not show
  that nobody tried a gated model. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-11-22.

- `SUP-451` **AWS's service reference and the project role's managed policy disagree on the resources of
  two AgentCore tool actions, and the AWS CLI 2.37.12 carries no web search call** (read 2026-11-22,
  `TM-28`). The service reference (`bedrock-agentcore.json`, version `v1.5`) writes the web search's
  resource as `arn:${Partition}:bedrock-agentcore:${Region}:${Account}:tool/web-search.v1`, the caller's
  account, where `SageMakerStudioProjectRoleMachineLearningPolicy` v48 grants `InvokeWebSearch` on
  `arn:*:bedrock-agentcore:*:aws:tool/web-search.v1` and the Web Search API's guide gives the `aws`
  spelling too ([`REFERENCES.md`](REFERENCES.md), 2026-11-22). It lists `ConnectBrowserAutomationStream` with no
  resource type, which IAM authorizes on `*`, where the policy grants it on `arn:*:bedrock-agentcore:*:aws:browser/*`.
  Simulated as `eighth-experimentation`'s project role, with the Region and the project tag in the context
  (`SUP-008`): `InvokeWebSearch` `allowed` on the `aws` spelling and `implicitDeny` on the account's;
  `ConnectBrowserAutomationStream` `implicitDeny` on `*`, and on the browser's ARN the simulator returns no
  organizations or boundary verdict at all. Which ARN the service builds is unmeasured: the CLI has no call,
  and a call would run a search. So whether a project role can search today turns on an ARN no page
  settles, and a deny written on the grant's ARNs could match nothing; `DenyAgentCoreBuiltInTools` is on
  `*` for that reason. The CLI 2.37.12 (botocore model `2024-02-28`, 67 operations) has no
  `invoke-web-search` and no `invoke-web-answer`, and drops `invoke-code-interpreter`, an event stream, so
  the SCP battery cannot attempt those three. Where: `log-stage-11-dlp.md`, 2026-11-22; `scp-battery.md`,
  the `TM-28` amendment.

- `SUP-459` **A guarded `Converse` through an application inference profile carries `bedrock:GuardrailIdentifier`
  on both of its authorization passes, so an `ArnNotLike` deny over the key admits it and refuses a call that
  names no guardrail on the profile's pass** (measured 2026-11-22 in Sandbox, Stage 17 10.4 step 4,
  verification xxxvii, as `app-genai-dev`'s project role from MWAA Serverless workers, through the
  `bedrock-runtime` endpoint).
  - The documentation: Bedrock's page on enforcing a guardrail gives the condition key for `InvokeModel` and
    `Converse`. It does not say whether a call through an inference profile carries the key on the profile's
    pass, on the foundation model's pass, or on both (`SUP-300`'s two passes).
  - The deny: `DenyAnInvocationWithNoPublishedGuardrailOfTheAccount` on `bedrock:InvokeModel` and
    `bedrock:InvokeModelWithResponseStream`, resource `*`, `ArnNotLike` `bedrock:GuardrailIdentifier`
    `arn:aws:bedrock:us-west-2:<account>:guardrail/*:*`, in `awsds-sandbox-bedrock-application`, applied at
    19:56:00.
  - Admitted: the 40 `Converse` of `app-genai-triage` from 20:12:04, each with a `guardrailConfig` that names
    the application's guardrail by its unversioned ARN with `guardrailVersion` `2`. A negated operator matches
    an absent key and the deny's resource is `*`, so the key was present on both passes.
  - Refused, each `AccessDenied`: a `Converse` with no `guardrailConfig` at 20:11:15, and
    `BedrockInvokeModelOperator`'s `InvokeModel` at 20:09:14 and 20:11:41. Each reads *"… is not authorized to
    perform: bedrock:InvokeModel on resource: arn:aws:bedrock:us-west-2:<account>:application-inference-profile/ciceumyodl7y
    with an explicit deny in an identity-based policy: arn:aws:iam::<account>:policy/awsds-sandbox-bedrock-application"*.
    The refusal names the profile, the first pass.
  - A refused call's event carries `requestParameters` null, so the trail does not show what a refused request
    named.

  Where: `log-stage-17-sandbox-machine-learning.md`, 2026-11-22; `terraform-live/sandbox/bedrock/application.tf`;
  Stage 17 decision 24.

## Terraform

A Terraform behaviour that is one service's quirk is recorded under that service: `SUP-124` (a Redshift
Serverless workgroup's `config_parameter`), `SUP-120` (an Athena workgroup's `force_destroy`), `SUP-106` and
`SUP-101` (`aws_lakeformation_data_lake_settings` and the settings it replaces), `SUP-150` and `SUP-153`
(DataZone blueprint configurations through `awscc`), `SUP-353` (DataZone policy grants created at once, and
`-parallelism=1`), `SUP-064` (security group descriptions at `validate`),
`SUP-065` (a Data Lifecycle Manager description at plan time), `SUP-060` (`jsonencode` and an EventBridge
Scheduler placeholder), `SUP-061` (`instance_type` and user data), `SUP-213` (`aws_sagemaker_image_version`
and a space's own copy of the version) and `SUP-062` (an Elastic IP's allocation id after a transfer).

### Terraform core and its command line

- `SUP-302` **`terraform init -backend=false` on an initialised slice still reads the backend recorded in
  `.terraform/` and looks for credentials** (measured 2026-08-18, Stage 4). On a slice already initialised,
  `init -backend=false`, run while committing a caller's module bump, failed with *"No valid credential
  sources"* or an IMDS timeout: with no profile in the environment, the credential lookup fell through to
  the EC2 instance metadata service of a laptop. The flag skips configuring a backend, not reading the one
  already recorded. A real `init` with the slice's profile and `-backend-config=backend.hcl` clears it, and
  an IMDS timeout in this position means a missing profile, not a broken backend. Where:
  `log-stage-04-vpn.md`, 2026-08-18; `runbooks/terraform-changes.md` §7.

- `SUP-303` **A `.terraform.lock.hcl` missing a platform's `h1:` hash fails `terraform init` under
  `TF_PLUGIN_CACHE_DIR`, and is silently rewritten without the cache** (measured 2026-08-21, Stage 6 plan
  review, `hashicorp/aws` 6.60.0). Three slices carried one `h1:` hash each where every other slice carried
  three. With the plugin cache set, Terraform holds an unpacked directory rather than the provider's zip, so
  it can compute only an `h1:`; on a platform whose `h1:` the lock lacks, `init` fails with a checksum error
  that reads like a supply-chain attack. Without the cache, `init` verifies against the 16 `zh:` hashes the
  registry signs, appends the missing `h1:` and rewrites the committed file, which in CI shows as a dirty
  worktree or a later `git diff --exit-code` failure naming the wrong cause. `terraform providers lock`
  re-resolves the version constraint, here `~> 6.60`, and would have moved applied slices to 6.61.0. Where:
  `log-stage-06a-unified-studio.md`, 2026-08-21; `scripts/check-provider-locks.py`.

- `SUP-304` **A `terraform plan` run with no terminal and a variable missing waits on its prompt
  indefinitely, and a 3h33m wait held no state lock** (measured 2026-09-06, Stage 6c pass 3). A backgrounded
  plan whose `peerings` variable was missing from the tfvars sat for eleven minutes while other commands
  failed with *"Error acquiring the state lock"*; two locks were force-unlocked after no `terraform` process
  was found holding them. Later the same day a plan looping over two spokes stopped at a prompt in its
  second half and sat 3h33m with `fd 0` on the harness pipe; every `.tflock` object in the three state
  buckets was listed and none existed, the process having blocked during variable evaluation, before the
  lock is taken. A hang and a lock error are therefore separate readings: list the lock objects and look for
  a live process before `force-unlock`. `-input=false` turns the prompt into an immediate error. Where:
  `log-stage-06c-networking-hub.md`, 2026-09-06 (two entries); `runbooks/terraform-changes.md` Recipe A;
  `lessons.md` Lesson 47.

- `SUP-305` **`terraform validate` answers `Success!` on a conditional whose branches disagree in type when
  its values come from a `for` whose keys are unknown until plan** (measured 2026-09-12, Stage 6e step 4.2).
  `vpc-egress` v0.12.0 to v0.14.0 built each endpoint policy with `scope == null ? st : merge(st, { Action =
  scope })`, one branch carrying `Action` as the string `"*"` and the other as a list of strings. `validate`
  passed in the module directory and in `sandbox/egress` fully initialised at each tag; the log gives the
  reason as `local.service_names` being a `for` over `distinct(concat(...))` whose keys are unknown until
  plan, so the statement's type stays dynamic (inferred, not isolated). The first plan, at `make up`, failed
  with twenty *"Inconsistent conditional result types"*, one per endpoint. Only a plan of a caller exercises
  a module change of this kind. Where: `log-stage-06e-claude-code-bedrock.md`, 2026-09-12; `lessons.md`
  Lesson 54.

- `SUP-306` **Terraform's S3 backend refuses an AWS profile that sets `credential_source` without
  `role_arn`, a profile the AWS CLI accepts by ignoring the key** (measured 2026-10-15, Stage 8 decision 14,
  Terraform 1.15.8). A runner profile written with `credential_source = Ec2InstanceMetadata` and no
  `role_arn` served the AWS CLI at the runner's boot; read through the S3 backend of a
  `terraform_remote_state` on the laptop, it failed with *"Error: credential type credential_source requires
  role_arn"*. A profile with a `role_arn`, and one with a region alone, both passed that check and stopped
  later at the instance metadata the laptop lacks. A profile proven by the CLI is therefore not proven for
  Terraform; a profile carrying no credential setting reaches the instance metadata through both tools'
  default chain. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-15;
  `terraform-live/production/runners/deploy-runner.tf`.

- `SUP-356` **A resource planned as an in-place update because one argument is known after apply is not
  counted by the apply when the value comes out the same** (measured 2026-11-11 in `staging/studio/` and
  `production/studio/`, Stage 19 step 4.4, Terraform 1.16.6). Each plan read *"5 to add, 2 to change, 0 to
  destroy"* and each apply *"5 added, 1 changed, 0 destroyed"*. The second planned change was an
  `aws_iam_policy` whose document reads a data source carrying `depends_on` on a module with pending
  changes: Terraform defers such a read to the apply, which its page on data sources states, so the
  document was planned as `(known after apply)` and the policy as updated in place; at apply the document
  rendered identical and no update was made. A plan and an apply whose counts differ by such a resource
  are both right, and the re-plan reads `No changes`. Where:
  `log-stage-19-smus-native-data-product.md`, 2026-11-11; `terraform-live/staging/studio/person-session.tf`.
  Read again the same day on the same policy, at the module's next tag: each plan *"0 to add, 2 to
  change"*, each apply *"0 added, 1 changed"*, each re-plan `No changes`.
  The complement, 2026-11-12, release F's applies in the same two slices: the same policy planned the
  same way with a document that did change, each plan *"2 to add, 2 to change"* and each apply *"2
  added, 2 changed"*.
  Read again 2026-11-22 in `sandbox/warehouse/` (Stage 6h decision 8 (a)'s standing change, Terraform
  1.17.2), with no `depends_on`: `data.aws_iam_policy_document.project_warehouse["avhvbqn37ty7m8"]`
  references `aws_iam_role.project_access[each.key]`, its own instance unchanged, and was planned *"will be
  read during apply"*, *"(depends on a resource or a module with changes pending)"*, because the resource
  gains the instance `4gqfau9xuo6e4w`. The plan read *"7 to add, 2 to change"*, the existing project's
  policy the second change: the deferral follows the resource, not the instance. The apply half is read at
  the Sandbox warehouse sitting. Where: `log-stage-06h-redshift-connection.md`, 2026-11-22.

- `SUP-403` **A saved plan file is refused by every Terraform version but the one that wrote it** (measured
  2026-11-21, the laptop's move to 1.17.2). `sandbox/workflows/`'s training-pair plan, saved by 1.16.6 on
  2026-11-20, read with `terraform show` under 1.17.2: exit 1, *"Plan read error: plan file was created by
  Terraform 1.16.6, but this is 1.17.2; plan files cannot be transferred between different Terraform
  versions"*. The pages of `plan` and `apply` (read 2026-11-21) call `-out`'s file opaque and name no
  version. A plan saved for a later sitting does not survive a binary change, and the sitting plans again.
  `state pull` is the documented opposite: its output carries the running binary's version, 1.17.2 against
  the 1.15.8 the S3 object of `sandbox/foundation` holds (serial 18 in both). Where:
  `log-stage-08-cicd-pipelines.md`, 2026-11-21; `runbooks/promotion.md` §N.12.3.

- `SUP-457` **`terraform show -json` prints `{"format_version":"1.0"}`, exit 0, both for a state that holds
  no resource and for an S3 backend key that holds no object** (measured 2026-11-22 under 1.17.2). The
  destroyed `production/egress/`, whose object reads format 4, serial 226 and `"resources": []`, printed that
  line; so did a scratch configuration whose backend named `production/no-such-slice/terraform.tfstate`, a
  key `head-object` answers 404 for, after an `init` that exited 0. The human `show` of the second printed
  *"The state file is empty. No resources are represented."*, exit 0. The pages of `terraform show`, the
  JSON output format and the S3 backend (read 2026-11-22, the last two in part) state no output for an
  empty or absent state and nothing about a key with no object. Until 2026-11-22 `make status` read every
  `[E]` slice through `show`, so a moved key or a slice never applied read `down` at 0 USD/h; it reads the
  object since, and a key with no object reads UNREADABLE. Where: `scripts/slices.py`, `state_tree()`;
  `log-stage-12-observability-finops.md`, 2026-11-22.

### The `aws` provider

- `SUP-307` **`aws_organizations_policy` compares `content` as decoded JSON values, so a one-element
  `Action` array and the same action as a string differ to the plan while they mean the same to IAM**
  (measured 2026-08-16, Stage 2 step 5.5, `hashicorp/aws` 6.60.0). Organizations minifies a policy but keeps
  the key order it was given, while `jsonencode` sorts keys; the byte strings differ and the plan stays
  empty, because the provider's `verify.SuppressEquivalentJSONDiffs` runs a `reflect.DeepEqual` on the
  decoded values. That comparison knows nothing of IAM: Organizations held `"ecr:*"` where a tracked
  document wrote `["ecr:*"]`, and of ten documents that one alone would have stayed dirty after import. Once
  it wrote the scalar, twenty objects imported and the full plan carried no `content` or `type` diff. Where:
  `log-stage-02-terraform-foundation.md`, the two step 5.5 entries of 2026-08-16;
  `terraform-live/identity/org-policies/locals.tf`.

- `SUP-308` **`aws_instance` applies a changed `user_data` in place by default, and with
  `user_data_replace_on_change = true` every byte of a rendered template, comments included, replaces the
  host** (read 2026-08-16 in a plan, Stage 3 probes; measured 2026-09-17, Stage 6g decision 1). Without the
  flag, a rewritten probe script planned as an in-place update of the attribute, and user data runs at first
  boot only, so the corrected instrument would have been measured on a host still running the old one. With
  the flag set, a two-argument change to `production/proxy/main.tf` planned `1 to add, 2 to change, 2 to
  destroy`: the SSM-resolved `ami` had moved, and a comment edited in `user-data.sh.tftpl` and never applied
  made `user_data` differ from what the running host carried. A plan can therefore propose a replacement for
  a template edit made long before the change being applied; `aws ec2 describe-instance-attribute
  --attribute userData` reads what the host carries. Where: `log-stage-03-networking.md`, 2026-08-16;
  `log-stage-06g-access-by-identity.md`, 2026-09-17; `lessons.md` Lesson 64.

- `SUP-309` **`associate_public_ip_address` read-back fights an `aws_eip_association` forever.** With an
  Elastic IP attached, the refresh reports the attribute from the instance's current public address, so the
  next plan wants to destroy and recreate the instance on a ForceNew diff that nothing changed. Measured on
  the first VPN apply, 2026-08-17; the fix is `ignore_changes` on the read-back, while the argument stays
  load-bearing at launch.

- `SUP-310` **`hashicorp/aws` 6.60.0 stores an `aws_instance`'s rendered `user_data` in the state in full,
  in plaintext, not as a SHA-1** (measured 2026-08-17, Stage 4 step 1.4). `terraform state pull` after the
  WireGuard host's first apply showed the whole rendered script where the stage, its runbook and the slice
  README had predicted 40 hex characters; the hash is pre-5.0 behaviour. Anything a template renders into
  user data is readable by whoever reads the state. A secret stays out of the state only when the script
  holds a pointer, here a Secrets Manager ARN and a shell variable filled on the host at boot. Where:
  `log-stage-04-vpn.md`, 2026-08-17; `runbooks/vpn.md` §K0.

- `SUP-311` **`aws_lakeformation_data_lake_settings` cannot write its default-permission blocks empty, and
  its plan states nothing about what omitting them will do** (measured 2026-08-18 in Data Governance and
  2026-08-19 in Sandbox and Development, Stage 5a pass 1 and pass 4a/4b, `hashicorp/aws` ~> 6.60).
  `create_database_default_permissions = []` is refused with *"An argument named … is not expected here. Did
  you mean to define a block?"*; a `{}` block declares one entry with computed fields; omitting both blocks
  plans as `after_unknown: true` for each. The schema shows `nesting_mode: list` blocks with `max_items: 3`
  and marks `computed` on attributes, never on `block_types`, so a create or update plan's `after_unknown`
  is the only reading (a no-op plan answers `{}`). Applied alone under `-target`, omission cleared both
  lists: `DbDefaults: []`, `TableDefaults: []`, and no `IAMAllowedPrincipals` grant on any new database. The
  plan renders the same whether the apply clears or keeps them, and the defaults act at creation, so the
  settings are read back before the first database exists. Where: `log-stage-05a-data-foundation.md`,
  2026-08-18 and 2026-08-19; `runbooks/terraform-changes.md` Recipe D.

- `SUP-312` **An `aws_instance` whose `ami` is read from a public AMI parameter in SSM shows a forced
  replacement as `ami = (sensitive value) # forces replacement`, hiding both image ids** (measured
  2026-08-18, Stage 4, the WireGuard host's MTU change). The plan of a `user_data` edit named two causes of
  replacement, and the second was the AMI, resolved from `/aws/service/ami-amazon-latest/…`, with both ids
  masked. Read from the parameter and from `describe-instances`, the instance ran `ami-098176c88d53db397`
  and the parameter had moved to `ami-0c9da9b2b7758f931` the previous evening. Any change to such an
  instance also replaces it whenever the parameter has moved since the last apply, and a boot failure after
  it has two candidate causes, which only the two ids separate. Where: `log-stage-04-vpn.md`, 2026-08-18;
  `terraform-live/production/tooling/data.tf`.

- `SUP-313` **The first Iceberg commit stamps `iceberg.field.id`, `iceberg.field.current` and
  `iceberg.field.optional` onto every column of the Glue table, so an `aws_glue_catalog_table` declaring
  bare columns plans a change forever** (measured 2026-08-20, Stage 5a, Data Governance's
  `curated.sample_trades`). After a 12-row Athena `INSERT INTO curated.sample_trades`, the next plan of the
  lake slice read `1 to change` on the table: Terraform wanted to strip parameters the engine re-stamps at
  each commit, so an apply would be undone by the next commit. With `lifecycle { ignore_changes =
  [storage_descriptor[0].columns] }` the slice plans `No changes`; Terraform then holds the table's
  existence, location and format, and schema evolution goes through the engine. Where:
  `log-stage-05a-data-foundation.md`, 2026-08-20; `terraform-live/data-governance/data/catalog.tf`.

- `SUP-314` **`aws_instance` plans a decrease of `root_block_device.volume_size`, and `aws_ebs_volume` one of
  `size`, as an in-place change that EBS refuses at apply** (measured 2026-08-21, the WireGuard host). An apply taking the host from
  `t3.medium` on 64 GiB back to `t3.nano` on 8 GiB changed the type by a stop, a modify and a start, and its
  disk half failed at `ModifyVolume` with *"InvalidParameterValue: New size cannot be smaller than existing
  size"*, leaving `~ volume_size 64 -> 8` in the slice's plan. No flag, re-run or `force` completes it. The
  way down was an explicit `-replace` of the instance, `2 to add, 1 to change, 2 to destroy`, which deleted
  the 64 GiB volume with the old instance and left no `available` volume. A grow is issued as `ModifyVolume`
  without a stop, and the filesystem takes the extra GiB only when `growpart` runs at boot (read in the
  slice's variable description, not measured). Where: `docs/AWS_STATE.md`, the WireGuard host row;
  `terraform-live/production/vpn/variables.tf`, `root_volume_size`; `runbooks/vpn.md` §S6.
  Read 2026-11-09 on GitLab's data volume, a standalone `aws_ebs_volume`: with `-var data_volume_size=20`
  the plan reads `aws_ebs_volume.data will be updated in-place`, `size = 50 -> 20`, `Plan: 0 to add, 1 to
  change, 0 to destroy.` (provider `hashicorp/aws` 6.68.0), never applied. The smaller volume landed on
  2026-11-10 through the slice's destroy, re-apply and a GitLab restore. Where:
  `log-stage-12-observability-finops.md`, 2026-11-09 and 2026-11-10; `runbooks/gitlab.md` §B.

- `SUP-315` **Route 53 Resolver returns every firewall domain-list entry with a trailing dot, so an
  `aws_route53_resolver_firewall_domain_list` written with bare names plans a change after every apply**
  (found 2026-08-22, Stage 6a; measured 2026-09-06 in Sandbox, Stage 6c, `EXC-04`). `list-firewall-domains`
  returns `pypi.org.`, `*.amazonaws.com.` and `*.` for entries written without the dot; the provider
  compares the two spellings, re-issues `UpdateFirewallDomains` at each apply, and the re-plan read `0 to
  add, 2 to change` immediately after a successful apply, with ten entries as with sixty-three. With the ten
  entries dotted and the catch-all bare the plan read `1 to change`; with both dotted, `No changes`, also
  after a forced re-create of both lists. Endpoint `PrivateDnsName` values and
  `describe-vpc-endpoint-services` names come back without the dot, so a comparison with them strips it. The
  provider version is not recorded. Where: `log-stage-06c-networking-hub.md`, 2026-09-06;
  `log-stage-06a-unified-studio.md`, 2026-08-22; `terraform-modules/vpc-egress/dns-firewall.tf`.

- `SUP-316` **A destroy of `aws_lakeformation_data_lake_settings` resets the account to AWS's defaults,
  `CROSS_ACCOUNT_VERSION=1` and an empty administrator list, and brings back no create-time default**
  (measured 2026-09-06 in the account then named Development, now Staging, Stage 6b step 2.4). The slice's
  teardown read `0 added, 0 changed, 5 destroyed`, the settings among the five, and the account then read
  version 1 with no administrator. No `IAMAllowedPrincipals` database or table default came back. A check
  written for a consumer's settings reads this resting state as failed, though the account holds no share,
  resource link or catalog object. Where: `log-stage-06b-development-becomes-staging.md`, 2026-09-06.

- `SUP-317` **No resource of `hashicorp/aws` 6.60.0 and no CloudFormation type wraps Bedrock's
  `PutAccountDataRetention`, so the account's retention mode stays outside Terraform** (read 2026-09-11 in
  the provider and the CloudFormation registry, Stage 6e 7.2). The provider declares nine `aws_bedrock_*`
  resources and eight data sources, none matching `retention`. Its binary carries
  `bedrock.GetAccountDataRetentionInput` and `PutAccountDataRetentionInput`, which belong to the bundled Go
  SDK and are no provider surface, so a `strings` grep over the binary misleads. `list-types --visibility
  PUBLIC --filters TypeNamePrefix=AWS::Bedrock` returns 29 `AWS::Bedrock::*` types, none an account setting,
  so `hashicorp/awscc` has nothing either. The use-case form is a resource,
  `aws_bedrock_use_case_for_model_access`, whose whole schema is `form_data`, a string over the API's blob.
  Where: `log-stage-06e-claude-code-bedrock.md`, 2026-09-11; `runbooks/claude-code-sagemaker.md` §M1.

- `SUP-318` **`aws_sagemaker_image_version` calls `sagemaker:ListAliases` on every refresh and again on a
  replace** (read 2026-10-15 in Sandbox's trail of a replace on 2026-10-12, Stage 8 pass 3). CloudTrail of
  the replace of image version 5 lists the provider's calls: on refresh `DescribeImage`,
  `DescribeImageVersion`, `ListAliases`, `ListTags`, `DescribeAppImageConfig`; on the replace
  `DeleteImageVersion`, `CreateImageVersion` and `ListAliases` again. A deploy role whose policy granted the
  image-version actions without `ListAliases` read `implicitDeny` on the image and the version in the policy
  simulator, so its first plan of the slice would have been refused (inferred from the simulator, not run).
  `hashicorp/aws` 6.64.0, read in its references, keys the resource by name and number, reads aliases with
  `ListAliases`, updates aliases and `VendorGuidance` in place and forces a new version only on `base_image`
  and `image_name`. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-15 (two entries).

- `SUP-319` **The DataZone and MLflow resources of `hashicorp/aws` 6.69.1 and `hashicorp/awscc` 1.106.0
  cannot write a custom blueprint, a VPC or Git connection, a domain's cascading delete or an MLflow App's
  key** (read 2026-10-18 in the CloudFormation registry, the provider schemas and botocore's models). The
  registry holds no `AWS::DataZone::EnvironmentBlueprint` type, so a custom Tooling blueprint is a hand
  object. `AWS::DataZone::Connection` and `awscc_datazone_connection` carry neither a VPC nor a Git
  connection, though the model's connection types include `VPC` and `GIT`. `aws_datazone_domain` has no
  argument for the `cascadeDelete` that `DeleteDomain` takes since botocore 1.43.82.
  `AWS::SageMaker::MlflowApp`, `aws_sagemaker_mlflow_app` and `awscc_sagemaker_mlflow_app` carry no key
  field although `CreateMlflowApp` takes `KmsKeyId`, so an app made through them has no customer-managed
  key. A domain's account association has no public API at all (read 2026-08-16). Where:
  `docs/plan/upstream-releases.md`, the SageMaker Unified Studio table; `docs/SMUS.md`, "Domain".

- `SUP-320` **`aws_sfn_state_machine` calls `states:ValidateStateMachineDefinition` while it plans a new or
  changed definition, and the action takes no resource** (read 2026-10-24 in the provider's source,
  Staging's trail and the policy simulator, Stage 10 3.8 replay, `hashicorp/aws` v6.70.0, Terraform 1.15.8).
  The provider's `stateMachineDefinitionValidate` runs in `CustomizeDiff` when the definition is new or
  changed, so at plan and again at apply, and returns any error from the call. Staging's trail holds the
  call at 22:47:58 on 2026-10-23, beside `CreateStateMachine`. `iam simulate-principal-policy` read
  `implicitDeny` for both deploy roles, which held the state-machine writes on their machines' ARNs; given a
  state machine's ARN the simulator applied no statement, so only `Resource "*"` grants it. A role scoped to
  its state machines would stop at the plan of any definition change: inferred from the source and the
  simulator, not seen as a failed run. Where: `log-stage-10-orchestration-promotion.md`, 2026-10-24;
  `terraform-live/production/foundation/apply-orchestration.tf`.

- `SUP-321` **`aws_lakeformation_resource` declares no importer, so a Lake Formation registration made
  outside Terraform cannot be adopted** (read 2026-10-25 in the provider's documentation and source, Stage 9
  9.5, `hashicorp/aws` 6.60.0). Its Create sends `UseServiceLinkedRole: true` when no role is given, and its
  Read never sets that attribute. `aws_lakeformation_resource_lf_tags` documents no import either. Data
  Governance's registration of a Redshift datashare and its LF-Tags therefore stayed hand objects while the
  datashare authorization, the consumer association and the federated Glue database beside them were
  imported on 2026-10-25. Read, not exercised. Where: `log-stage-09-deployment-targets.md`, 2026-10-25.

- `SUP-322` **`aws_redshift_data_share_authorization` plans a replacement when `allow_writes = false` is
  declared, and leaves the state whenever the consumer is not `AUTHORIZED`** (measured 2026-10-25 and
  2026-10-26, Stage 9 9.5 and verification xxiv, `hashicorp/aws` 6.68.0). Importing a hand-made
  authorization with `allow_writes = false` declared planned `1 to import, 1 to add, 1 to destroy`, the
  attribute *"forces replacement"* because the provider reads it back as unset; left undeclared, the plan
  read `1 to import, 0 to add, 0 to change, 0 to destroy`. After the producer's `REVOKE`, the refresh warned
  *"AWS resource not found during refresh"*, *"Original error: couldn't find resource"* and planned `1 to
  add`. After the re-grant left the consumer `PENDING_AUTHORIZATION`, the plan again read `1 to add`, after
  *"Original error: empty result"*, and its apply brought the consumer to `AUTHORIZED`. A pending consumer
  is therefore a resource Terraform creates, not one it adopts. Where: `log-stage-09-deployment-targets.md`,
  2026-10-25 and 2026-10-26; `terraform-live/production/warehouse/datashare.tf`.

- `SUP-323` **`data.aws_redshift_data_shares` returns null, not an empty list, when the account sees no
  datashare** (measured 2026-10-26, Stage 9 verification xxiv, `hashicorp/aws` 6.60.0). With Production's
  share `trades_lf` revoked, Data Governance's slice failed to plan: *"Planning failed"*, *"Error: Iteration
  over null value"*, *"data.aws_redshift_data_shares.visible.data_shares is null"*, at a `for` expression
  over the list. While a share was visible the same data source returned a list. A slice that iterates it
  can plan no change at all while no share is visible; it planned again once the producer had re-granted the
  share and its authorization read `AUTHORIZED`. Where: `log-stage-09-deployment-targets.md`, 2026-10-26;
  `terraform-live/data-governance/data/warehouse-share.tf`; `runbooks/promotion.md` §N.4a.

- `SUP-407` **`aws_instance` refuses a `user_data` over 16,384 bytes at plan, counts bytes rather than
  characters, and prints the whole value in its error** (measured 2026-11-22, `hashicorp/aws` 6.60.0).
  The schema check reads *"expected length of user_data to be in the range (0 - 16384), got "* followed
  by the user data itself: `production/proxy/` padded to 16,385 bytes printed 303 lines, 17,975 bytes of
  plan output. Offline, a literal of 8,193 characters and 16,385 bytes failed `terraform validate`, and
  one of 16,384 ASCII bytes passed. `validate` runs the check only on a value it knows: a user data
  rendered from a variable or a data source is unknown there and passes, and the same value fails at
  plan. An over-limit user data therefore stops a replacement at plan, before the destroy. A `lifecycle`
  precondition on the instance is evaluated before the check: with one, the padded plan stopped on
  *"Resource precondition failed"* alone. The provider's page for `aws_instance` states no limit on
  `user_data`; EC2's page states 16 KB before base64. The same refusal stopped `wireguard-v0.8.0`'s plan
  at about 16,432 bytes that day. Where: `log-stage-06c-networking-hub.md` and
  `log-stage-12-observability-finops.md`, 2026-11-22; `terraform-live/production/proxy/main.tf`;
  `terraform-modules/wireguard/main.tf`.

### The `awscc` provider and Cloud Control

- `SUP-324` **`awscc_datazone_environment_blueprint_configuration` takes the blueprint's name in
  `environment_blueprint_identifier`, and an id fails as a blueprint that does not exist** (measured
  2026-08-21, Stage 6 step 1.4). Fed blueprint ids, all twelve configurations failed at apply with *"waiter
  state transitioned to FAILED. StatusMessage: Managed Environment Blueprint with `<id>` doesn't exist..
  ErrorCode: InvalidRequest"*, while `get-environment-blueprint` from the same profile, domain and Region
  answered for those ids; nothing was created. A Cloud Control `create-resource` with the name `Tooling`
  returned `SUCCESS` with an identifier `<domain id>|<blueprint id>`, and a plain-CLI
  `put-environment-blueprint-configuration` with the id succeeded. The `aws` provider's equivalent resource
  takes the id. The type schema marks the identifier createOnly and writeOnly, so the read never returns it
  and Terraform keeps what was sent. The CloudFormation page documents the identifier against the names
  `DefaultDataLake` and `DefaultDataWarehouse` alone. Where: `log-stage-06a-unified-studio.md`, 2026-08-21;
  `terraform-modules/sagemaker-prereqs/blueprints.tf`.

- `SUP-325` **An `awscc_datazone_project_profile` environment configuration with `parameter_overrides = []`
  plans `1 to change` on every run** (measured 2026-10-30, Stage 6d 2.6 item 3, `awscc` 1.98.0). DataZone
  stores no `parameterOverrides` for an empty list, so the configuration sent and the one read back never
  match. Taking the `SageMakerAIDomain` element's key out of the overrides map, which leaves its
  `configuration_parameters` null, made the re-plan read `No changes`, and `get-project-profile` then showed
  the element with no override and seventeen resolved parameters at the template's defaults. A blueprint
  with no overrides is written by omitting `configuration_parameters`, never with an empty list. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-10-30;
  `terraform-live/data-governance/governance/locals.tf` and `profiles.tf`.

### The gates around a plan

- `SUP-326` **checkov ignores a `# checkov:skip=` comment written above the resource block, and reports
  nothing about it** (measured 2026-08-15, Stage 2 step 2). The bootstrap slice's first run read 30 passed
  and 3 failed (`CKV_AWS_18`, `CKV_AWS_144`, `CKV2_AWS_62`); a suppression on the line above a resource
  block was read as an ordinary comment and the check failed anyway. The suppression takes effect only
  inside the block, in its first lines, as `# checkov:skip=CKV_xxx:reason`. No output marks a misplaced
  suppression, so a skip that does not apply reads like no skip at all until the check fails. Where:
  `log-stage-02-terraform-foundation.md`, step 2, 2026-08-15; `runbooks/terraform-changes.md` §7.

## The AWS CLI

- `SUP-327` **The AWS CLI prints a `--query` result once per page of a paginated call under `--output
  text`** (measured 2026-10-09, Stage 5a pass 6, and 2026-10-14, Stage 8). `describe-config-rules` with a
  `length()` query printed one number per page, so the counts were page sums; `--output json | jq length`
  gave the total. `ecr describe-image-scan-findings --query imageScanStatus.status --output text` on an
  image with 1,317 findings printed `COMPLETE` and then `None` for every later page, so a shell loop waiting
  for the output to equal `COMPLETE` never exited; `jq` over the merged JSON was not affected. With
  `--max-items 1`, `mwaa-serverless list-workflow-runs` printed the CLI's `None` pagination token after the
  run id, and `get-workflow-run` refused the result as a run id (2026-10-26); `--max-results 1
  --no-paginate` returns the id alone. Against a local stand-in for Athena holding ten ids, with no AWS
  call (2026-11-17, aws-cli 1.46.3, Stage 20's review),
  `athena list-query-executions --max-items 4 --query QueryExecutionIds --output text` sent one request
  with no `MaxResults` and printed four ids and a line `None`, which a command substitution handed to
  `batch-get-query-execution` as a fifth id; `--max-results 4 --no-paginate` sent `MaxResults` 4 and
  printed the four ids alone. Where: `log-stage-05a-data-foundation.md`, 2026-10-09;
  `log-stage-08-cicd-pipelines.md`, 2026-10-14; `log-stage-10-orchestration-promotion.md`, 2026-10-26;
  `log-stage-20-dbt-lineage.md`, 2026-11-17; `runbooks/security-hub.md`.

- `SUP-328` **`aws sagemaker describe-image-version --version 6` prints the CLI's own version and exits 0
  without calling SageMaker** (measured 2026-10-12, Stage 8 pass 0). The operation's parameter is
  `--version-number`; `--version` behaves as the CLI's global flag. A script that passes it receives a
  version string and a success code, and no image version, so a check built on it can neither pass nor fail
  on the image. Where: `log-stage-08-cicd-pipelines.md`, 2026-10-12.

- `SUP-370` **The AWS CLI passes a `file://` document to `--policy-input-list` as one member per character**
  (measured 2026-11-16 with aws-cli 2.37.12, Stage 19). `iam simulate-principal-policy --policy-input-list
  file://<document>` was refused *"1 validation error detected: Value '[{, ", V, e, r, s, i, …]' at
  'policyInputList' failed to satisfy constraint: Member must have length less than or equal to 10"*,
  whether the document held one line or several. The same document passed as the argument's text,
  `"$(cat <document>)"`, was read as one policy, the matched statement's `SourcePolicyId` being
  `PolicyInputList.1`. The parameter is a list of strings, and the file's content reaches it as one string
  the CLI iterates (inferred from the error). Where: `log-stage-19-smus-native-data-product.md`, 2026-11-15.

- `SUP-435` **The AWS CLI v2 prints a JSON-protocol service's timestamps in the machine's time zone and EC2's
  in UTC, so a date read from its output is not always a UTC date** (measured 2026-11-22 with aws-cli 2.37.12
  on a laptop at UTC-3, default configuration, R1). `aws secretsmanager describe-secret --query
  LastRotatedDate --output text` printed `2026-11-21T22:17:08.980000-03:00`, and with `TZ=UTC` on the command
  `2026-11-22T01:17:08.980000+00:00`; `cloudtrail lookup-events` printed every `EventTime` at `-03:00`; `ec2
  describe-instances --query 'Reservations[0].Instances[0].LaunchTime'` printed `2026-11-22T01:15:54+00:00`
  with and without `TZ=UTC`. The CLI's service models name the protocols: `json` for Secrets Manager and
  CloudTrail, whose timestamps travel as epoch seconds, and `ec2` for EC2, which sends ISO 8601 text.
  botocore's `parse_timestamp` turns a number into a `datetime` with `tzlocal()` and keeps a text's own offset
  (read in botocore 1.43.114; the CLI v2's own copy is frozen into its binary and was not read). AWS's
  configuration page gives `iso8601`'s form as `YYYY-MM-DDThh:mm:ssZ`, "including a `Z` after the time", and
  names no zone; the v2 migration guide names none either; neither output carried a `Z`. Consequence: R1's
  poll waiting for the warehouse admin secret's `LastRotatedDate` to contain `2026-11-22` read six times from
  02:00:15Z to 02:05:27Z and never matched a rotation that had finished at 01:17:08Z, and `NextRotationDate`
  read `2026-12-21T22:59:59-03:00`, a date one day before UTC's. A date that is compared or written down is
  read with `TZ=UTC` on the command. Where: `log-stage-19-smus-native-data-product.md`, 2026-11-22;
  `runbooks/promotion.md` §N.8.3.

## Clients and the egress proxy

- `SUP-329` **`wg-quick` with no `MTU` line takes the uplink's MTU minus 80, so a WireGuard host on a
  9001-byte ENA interface brings `wg0` up at 8921** (measured 2026-08-17 and 2026-08-18, Stage 4 pass 2). On
  the host `ens5` read `mtu 9001` and `wg0` `mtu 8921` before the module pinned it. On a laptop tethered to
  a phone the uplink presented 1500, the tunnel came up at 1420, and since WireGuard sets DF on its outer
  packets the oversized ones were dropped with no error at either end: the 148-byte handshake and DNS
  succeeded, a TLS exchange with a full-MSS certificate chain timed out. `MTU = 1280` on both ends fixed it;
  `ping -M do -s 1253` then failed locally with *"message too long, mtu=1280"* and `-s 1252` passed. Editing
  the file while the interface is up does not change its MTU; the tunnel has to go down and up. Where:
  `log-stage-04-vpn.md`, 2026-08-17 and 2026-08-18; `runbooks/vpn.md` §C4.

- `SUP-330` **Chrome's Local Network Access gates the SMUS portal's requests when the laptop resolves
  through a VPC whose interface endpoints answer the portal's names with private addresses** (measured
  2026-08-26 and 2026-09-07, Stage 6 4.2 and 6c 6.2). On the tunnel, resolving at Sandbox's resolver, the
  portal's catalog tab and a JupyterLab launch failed with *"TypeError: Failed to fetch"* until a per-origin
  grant was given, while the `glue`, `lakeformation`, `athena` and `*.studio.<region>.sagemaker.aws` zones
  answered `10.20.x.x` and `curl` from the same laptop reached every address. CloudTrail held zero arrivals
  for about 25 minutes; the first minute after the grant showed Glue at the `glue` endpoint and SageMaker at
  `sagemaker.api`. Resolving instead at a VPC with no endpoint holding private DNS,
  `agent.datazone.us-west-2.api.aws` answered three public addresses, and the portal, a project, its catalog
  tab and a space opened with no prompt. A DNS Firewall block produces the same words; `dig` separates them.
  Where: `log-stage-06c-networking-hub.md`, 2026-09-07; `lessons.md` Lesson 43; `docs/NETWORK.md` §4.

- `SUP-331` **Squid's `dstdomain` treats `.example.com` as the domain and every subdomain and a bare
  `example.com` as that host alone, and an acl listing both refuses to load** (measured 2026-09-06, Stage 6c
  4.8, and 2026-09-08). `squid -k parse` on the hub proxy's first list printed *"ERROR:
  '.signin.aws.amazon.com' is a subdomain of 'signin.aws.amazon.com'"* then *"FATAL: Bungled ... line 10"*,
  and the proxy came up with an empty list; a deeper name under a wildcard (`d35uxhjf90umnp.cloudfront.net`
  beside `.cloudfront.net`) is only a warning, measured in isolation. Squid matches the name the client
  requested, the `Host:` header or the `CONNECT` target, and never a DNS answer: a CNAME chain is invisible,
  while an HTTP redirect to another host is a new request that needs its own entry. `github.com` covered
  neither `api.github.com` nor `codeload.github.com`, and the latter was refused `403 TCP_DENIED` in the
  same second the first tunnelled. Where: `log-stage-06c-networking-hub.md`, 2026-09-06; `runbooks/vpn.md`;
  `runbooks/log-debugging.md` §P. A later reading, 2026-11-21 (Stage 11, `TM-01`): a `CONNECT` target that
  is an IP address is matched by the name its reverse lookup returns, as Squid's `acl` page states for a
  `dstdomain` without `-n`; `SUP-404` holds the reading.

- `SUP-332` **`AllowedIPs` is inert for an address family the interface has no address in** (measured
  2026-09-07, macOS, App Store client). `wg-quick` installs routes only for the families present on
  `[Interface] Address`, so `AllowedIPs = 0.0.0.0/0, ::/0` beside an IPv4-only address installs no IPv6
  route; the config parses, the tunnel comes up and `wg show` reports nothing unusual. The reading is
  `netstat -rn -f inet6`: the tunnel interface is not among the default routes. WireGuard's documentation
  does not say the two lines are coupled. Where: `docs/plan/runbooks/vpn.md` §C6.

- `SUP-333` **macOS keeps the physical default route as an interface-scoped entry while a tunnel is
  primary** (measured 2026-09-07, macOS, App Store client). `netstat -rn` shows two defaults; the physical
  one carries the `I` flag, and traffic already associated with that interface keeps using it. A socket
  established before the tunnel came up survives it, so "the tunnel is up" does not mean everything goes
  through the tunnel: a new connection to the same host fails while the old one works.

- `SUP-334` **macOS does not consult the system proxy while a NetworkExtension tunnel is primary** (measured
  2026-09-07). `networksetup -getsecurewebproxy "Wi-Fi"` reports the proxy configured and enabled; `scutil
  --proxy`, which is what applications read, returns an empty dictionary. Safari, Chrome by default and
  every native application reading the system configuration behave as if no proxy existed. Per-application
  configuration works (Chrome's `--proxy-server` flag, Firefox's own settings, `https_proxy` for shell
  tools). With the tunnel down the same setting is consulted again, points at a host only the tunnel can
  reach, and breaks the `aws` CLI, which falls back to the system configuration: an empty `https_proxy` does
  not override it and `NO_PROXY='*'` does. Tracked as [issue #67](https://github.com/felipenoris/AWS-DataScience/issues/67).

- `SUP-335` **Linux rate-limits the ICMP errors a `REJECT` rule promises, per destination, and the rule's
  own counter does not say so** (measured 2026-09-07, 6c step 6.4). `iptables -L FORWARD -v` counted 27681
  rejected packets; `/proc/net/snmp`'s `Icmp` line said 4366 `OutDestUnreachs` and 23318 `OutRateLimitHost`,
  under `net.ipv4.icmp_ratelimit = 1000` (ms, per destination) and `icmp_ratemask = 6168`
  (destination-unreachable included). A client whose background traffic is refused a few times a second sees
  a timeout for the packet it is watching, and a fast refusal when a token happens to be free; both were
  measured with the same command, minutes apart. The `REJECT` counter proves the rule is hit; only the
  `Icmp` line says whether the refusal was spoken. `./aws/vpn.py --on-host` reads both. Where:
  `docs/plan/runbooks/vpn.md` §S2, `docs/NETWORK.md` §7.

- `SUP-336` **The App Store WireGuard client applies a `DNS` line to every query, whatever `AllowedIPs`
  says** (read from its source on 2026-09-08, `matchDomains = [""]` in
  `PacketTunnelSettingsGenerator.swift`, and measured the same night, 6c step 8.3). Under a split
  `AllowedIPs` the tunnel's resolver is still `scutil --dns`'s resolver #1, with no domain restriction and
  ordered ahead of the physical interface's; `/etc/resolv.conf` names it, and `dig` resolves a private name
  through it. A split tunnel does not give the laptop its own DNS back: every name crosses the tunnel, only
  the traffic does not. The `wg-quick` path does the same by writing the server on every network service.
  Where: `docs/plan/runbooks/vpn.md` §C7.

- `SUP-337` **The App Store WireGuard client installs an interface-scoped default route on the tunnel in
  both families, even when `AllowedIPs` names no default** (measured 2026-09-08, 6c step 8.3). `netstat -rn`
  shows a `default … utun4` carrying the `I` flag beside the physical `default … en0` without it, and the
  scoped entry is inert for any socket not bound to the tunnel. The reading that separates the two profiles
  is the flag, not the presence of the line: under the monitored profile the tunnel's default has no `I` and
  is primary. A step written as *"no default via the tunnel"* was one flag short; the host's `REJECT`
  counter, flat across a burst, proved the route inert. Observed the same night by the user: the app's
  tunnel is a Network Extension that `wg show` does not list, so the app's window is check 1's reading.

- `SUP-338` **A host with no IPv6 route answers a tunnelled IPv6 packet with ICMPv6 *no route* before the
  `FORWARD` chain sees it** (measured 2026-09-08, 6c step 8.3). The `ip6tables` `REJECT` written on
  2026-09-07 to make the refusal counted stood at 0 while `Icmp6OutDestUnreachs` read 191: the refusal is
  real and counted in `/proc/net/snmp6`, and the rule is a backstop that has never fired. The routing table
  is the control (Lesson 56). Where: `runbooks/vpn.md` §C6.

- `SUP-339` **A Squid refusal of an HTTPS `CONNECT` reads `000` at `curl`, and a `403` at the client can be
  the origin's inside a tunnel Squid admitted** (measured 2026-09-08 and 2026-09-20, Stage 6d). Over `https`
  the proxy's refusal is a `CONNECT` refusal: `curl` prints *"CONNECT tunnel failed, response 403"* and
  `%{http_code}` reads `000`, while the proxy log holds a named `403 TCP_DENIED`. In a probe of nine GitHub
  names from a space on 2026-09-20, `github-cloud.githubusercontent.com` read `403` at the client and `200
  TCP_TUNNEL` in the proxy log: Squid admitted the `CONNECT` and the origin answered `403` inside it, where
  Squid cannot see. `ssh.github.com`, `example.com` and `repo.anaconda.com` read `000` at the client and
  `403 TCP_DENIED` at the proxy. The client tells refused from admitted; only the proxy log says which side
  refused. A probe meant to be legible runs over `http://`. Where:
  `log-stage-06d-unified-studio-remainder.md`, 2026-09-08 and 2026-09-19; `runbooks/log-debugging.md` §P.

- `SUP-340` **The SageMaker Code Editor's extension gallery needs two hosts, `open-vsx.org` for the API and
  `openvsx.eclipsecontent.org` for the `.vsix` bytes, and its client ignores the `http.proxy` setting**
  (measured 2026-09-09, Stage 6d 8.5 and 8.6). `code-editor-server --install-extension`, run with the proxy
  variables exported and `VSCODE_IPC_HOOK_CLI` unset, reached the proxy and answered *"Server returned
  403"*; earlier attempts relying on `http.proxy` died at name resolution. The proxy log showed `CONNECT
  open-vsx.org:443` `200` and, at the same second, `CONNECT openvsx.eclipsecontent.org:443` `403`: the
  install is redirected to the second host, and an allow-list naming only the first admits the request and
  refuses the download. With both listed the install printed *"successfully installed"*, 96.32 MiB through
  `openvsx.eclipsecontent.org`. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-09;
  `runbooks/sg-proxy.md`. The gallery client's proxy handling is `SUP-232`, and the hosts the IDE calls at
  start are `SUP-233`.

- `SUP-341` **R's `install.packages` reports a proxy refusal as *"package 'X' is not available for this
  version of R"*, naming no refusal** (measured 2026-09-11 from a SageMaker space on `default-v0.2.0`, Stage
  6d decision 6). With the compute plane refusing `cloud.r-project.org`, R printed *"cannot open URL
  'https://cloud.r-project.org/src/contrib/PACKAGES'"* and *"package 'R6' is not available for this version
  of R"*, while the proxy log held `CONNECT cloud.r-project.org:443 403 TCP_DENIED` three times in one
  second, R trying more than one index candidate. R needed no proxy setting: `capabilities("libcurl")` was
  `TRUE` with `download.file.method` unset, and a positive control through the same process succeeded. Two
  local failures read like network ones: a missing personal library fails as *"'lib = …' is not writable"*
  before any request, and the image's conda-forge `r-base` without `repos=` fails as *"trying to use CRAN
  without setting a mirror"*. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-11;
  `runbooks/sg-proxy.md`.

- `SUP-342` **VS Code attached to a SageMaker space still asks the space to fetch
  `update.code.visualstudio.com` and `marketplace.visualstudio.com`, and the client settings that copy from
  the laptop reduce those calls without removing them** (measured 2026-09-11, Stage 6d step 7). With both
  names refused (`403 TCP_DENIED`), the session worked: Remote - SSH copied the server from the laptop with
  `scp`, and extensions came over the session. One container with no client settings asked `update.code` 3
  times and `marketplace` 15 times over four minutes; with `remote.SSH.localServerDownload: always` and
  `remote.downloadExtensionsLocally: true`, the next asked once and three times, and the extension installed
  and ran. Every line is a 3.4 KB Squid error page. The proxy log cannot tell a download attempt from a
  version probe by the CLI under `~/.vscode-server/cli`, and the server lives in
  `~/.vscode-server/cli/servers/Stable-<commit>/`, not `~/.vscode-server/bin`. A `403` on either name during
  a working session is expected. Where: `log-stage-06d-unified-studio-remainder.md`, 2026-09-11;
  `runbooks/remote-ide.md` §N.

- `SUP-376` **botocore's request validation, which `Stubber` runs, refuses a missing required member and
  leaves a shape's maximum length, pattern and enum unchecked** (measured 2026-11-17 with botocore 1.43.1 on
  the laptop, Stage 17 10.2, no call made). On `CreateGuardrail` under `Stubber`, a 60-character name, where
  the model's maximum is 50, a name off the model's pattern and the enum value `NOT_A_TYPE` were each
  admitted, and a request missing a required member was refused. boto3's pages do not say which of a shape's
  constraints the client checks. A test over `Stubber` therefore passes a request the service refuses, so
  `examples/app-genai/tests/test_definition.py` walks the model's constraints itself. Where:
  `log-stage-17-sandbox-machine-learning.md`, 2026-11-17.

- `SUP-395` **botocore decides a client's proxy against the host it composes from the service's endpoint
  prefix, not the host the endpoint ruleset resolves, so a `NO_PROXY` naming only
  `airflow-serverless.<region>.api.aws` sends MWAA Serverless's calls to the proxy** (measured 2026-11-21 in
  a space on `awsds-sandbox-dev-env` version 11 and on the laptop with aws-cli 2.37.12, Stage 20 3.3). In
  `app-dbt-dev`'s space, `boto3.client("mwaa-serverless", region_name="us-west-2")` failed `GetWorkflowRun`
  with `ProxyConnectionError`, *"Tunnel connection failed: 403 Forbidden"*, and the proxy logged five
  `CONNECT airflow-serverless.us-west-2.api.aws:443 403 … TCP_DENIED` from the space, both `NO_PROXY`
  variables carrying that host. On the laptop, with `HTTPS_PROXY=http://127.0.0.1:9` standing for a proxy
  that refuses every connection, `aws mwaa-serverless list-workflows` with `NO_PROXY` naming the `.api.aws`
  host logged *"Endpoint provider result: https://airflow-serverless.us-west-2.api.aws"*, then
  `ProxyConnectionError: Failed to connect to proxy URL: "http://127.0.0.1:9"`. The call answered with
  `NO_PROXY` naming `airflow-serverless.us-west-2.amazonaws.com`, a host that does not resolve (the `mwaa`
  group in `terraform-modules/vpc-egress/endpoints.tf`), and with `--endpoint-url
  https://airflow-serverless.us-west-2.api.aws` beside the `.api.aws` host in `NO_PROXY`; `sts
  get-caller-identity` with `NO_PROXY` naming `sts.us-west-2.amazonaws.com` answered, the control. The
  service's `endpointPrefix` is `airflow-serverless`. The proxy is chosen once, for
  `<endpointPrefix>.<region>.amazonaws.com`, when the client is created, and each request then goes to the
  ruleset's host (inferred from the readings). Every other `.api.aws` host in version 11's list has its
  composed twin beside it, ECR's being `api.ecr.us-west-2.amazonaws.com`, so MWAA Serverless is the one
  service in that list the rule reaches. A client in a space reaches the service with the composed host
  added to `NO_PROXY` or with an explicit endpoint URL. The CI/CD CLI's `run`, from the same terminal, left
  no `airflow-serverless` line in the proxy's log (cause unmeasured). Where: `log-stage-20-dbt-lineage.md`,
  2026-11-21; `runbooks/sagemaker-application.md` §D.

- `SUP-404` **An AWS service endpoint named under `.api.aws` can answer a reverse lookup with an EC2
  hostname under `.amazonaws.com`, so a proxy that matches reverse names admits by address a service it
  refuses by name** (measured 2026-11-21, Stage 11 `TM-01`). Read with `dig -x` from the laptop:
  the four addresses of `airflow-serverless.us-west-2.api.aws` and the three of
  `sagemaker-unified-studio-mcp.us-west-2.api.aws` answered `ec2-<a>-<b>-<c>-<d>.us-west-2.compute.amazonaws.com`,
  the form of the public hostname EC2 documents for an instance, and so did the front-ends of `sts`, `ec2`,
  `ssm`, `logs`, `sqs`, `sns`, `kms`, `monitoring`, `glue` and `athena` in `us-west-2`; S3's answered
  `s3-us-west-2.amazonaws.com` and DynamoDB's `dynamodb.us-west-2.amazonaws.com`. Names CloudFront serves
  answered `server-<ip>.<pop>.r.cloudfront.net` (`datazone.us-west-2.api.aws`,
  `idetoolkits.amazonwebservices.com`), and `public.ecr.aws`, on Global Accelerator,
  `<id>.awsglobalaccelerator.com`. No page this project read gives a service endpoint's reverse record.
  Squid's `dstdomain` without `-n` matches an address by that name (`SUP-331`): from a Sandbox space at
  20:29:25Z, `CONNECT 54.213.164.60:443`, an `airflow-serverless` address, read `200 TCP_TUNNEL` through the
  compute plane's `.amazonaws.com` entry, the plane refusing that host by name the same day (`SUP-395`),
  and `CONNECT 108.158.137.46:443`, a `datazone` address, read `403 TCP_DENIED`. Where:
  `log-stage-11-dlp.md`, 2026-11-21; `threat-model.md` `TM-01`.
