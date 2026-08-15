#!/usr/bin/env bash
#
# probes.sh - THE BATTERY, as data. Sourced by scp-battery.sh; never run on its own.
#
# Amending the ceiling means editing this file and nothing else: add the probe next to its
# statement's siblings, run ./aws/probes/scp-battery.sh, and the report says whether the
# amendment did what it was written to do.
#
#   probe <phase> <account> <expect> <allowed-regex|-> <safety> <label> -- <aws args...>
#
#     phase        root | ou | region | rcp | tags | decl     (--phase filters on this)
#
#                  The last three are step 7.8's, one per document, because 7.8 is attached
#                  one document at a time and each phase is the measurement for the attach
#                  that just happened. `rcp` in particular is run BEFORE widening the RCP
#                  from Policy Test to the root - see docs/plan/runbooks/scp-battery.md.
#     account      canary data identity dev sandbox1 prod
#     expect       deny   the ceiling must stop it
#                  allow  it must still work - a cross-check, or the floor
#     allowed-re   the wording that proves THIS action reached authorization. Lesson 21:
#                  that is a property of the action, not of the service, so it is declared
#                  per probe. Anything not matching it and not a deny is UNTESTED, never
#                  silently "allowed".
#
#     safety       MANDATORY, and it is the field that answers "does this create anything?"
#                  in the file rather than in someone's head. The driver rejects any probe
#                  whose safety is not one of:
#
#                    ro       read-only. The call changes nothing even if fully allowed.
#                    dryrun   carries --dry-run, so the service refuses to perform it.
#                    blocked  mutating, but it CANNOT succeed: a prerequisite named in the
#                             command does not exist (a domain, a role, an instance, a
#                             snapshot, a bucket). Remove the deny and the call still fails,
#                             one step later. The reason is written next to it.
#                    creates  mutating AND it would really do something if the deny were
#                             absent. **The driver refuses to run these outside Policy
#                             Canary.** There are seven in this file and each is argued:
#                             three in `root`, four in `decl`.
#
#     @AMI@ @SUBNET@ @ACCT@ are substituted with real ids from the probed account.
#
# The --profile flag is added by the driver. Do not write one here.

# ==========================================================================
# phase: root - the two documents on the organization root, measured on the
# canary, which is the one account they reach that can be probed freely (D29).
# ==========================================================================

# --- DenyGuardDutyTampering. GuardDuty authorizes BEFORE validating the detector id, which
#     is what lets this statement be proven while the service is still off everywhere - and
#     the same property is what makes these three `blocked`: no such detector exists.
probe root canary deny - blocked "guardduty:DisassociateFromAdministratorAccount (the spelling 7.5a added)" -- \
  guardduty disassociate-from-administrator-account \
  --detector-id 00000000000000000000000000000000 --region us-west-2

probe root canary deny - blocked "guardduty:UpdateDetector" -- \
  guardduty update-detector --detector-id 00000000000000000000000000000000 --no-enable --region us-west-2

probe root canary deny - blocked "guardduty:StopMonitoringMembers" -- \
  guardduty stop-monitoring-members --detector-id 00000000000000000000000000000000 \
  --account-ids 000000000000 --region us-west-2

# --- DenySnapshotAndImageSharing. The AMI id is deliberately one that does not exist:
#     measured 2026-08-13, ModifyImageAttribute authorizes first, so the probe reaches the
#     deny without ever naming a real image. An earlier version passed the public Amazon
#     Linux AMI, which asked to make a real image public and gained nothing by it.
probe root canary deny - blocked "ec2:ModifyImageAttribute (no such image)" -- \
  ec2 modify-image-attribute --image-id ami-0123456789abcdef0 \
  --launch-permission 'Add=[{Group=all}]' --region us-west-2

# --- DenyImageAndSnapshotExport (7.5a). All four are `blocked`: the image, instance,
#     snapshot and destination bucket named here exist nowhere.
probe root canary deny - blocked "ec2:ExportImage" -- \
  ec2 export-image --image-id ami-0123456789abcdef0 --disk-image-format VMDK \
  --s3-export-location S3Bucket=awsds-canary-does-not-exist --region us-west-2

probe root canary deny - blocked "ec2:CreateInstanceExportTask" -- \
  ec2 create-instance-export-task --instance-id i-1234abcd --target-environment vmware \
  --export-to-s3-task '{"S3Bucket":"awsds-canary-does-not-exist","DiskImageFormat":"VMDK","ContainerFormat":"ova"}' \
  --region us-west-2

# The one that needs a REAL ami to reach authorization (Lesson 21) - and is still blocked,
# by the destination bucket, which does not exist.
probe root canary deny - blocked "ec2:CreateStoreImageTask (real AMI, bucket that does not exist)" -- \
  ec2 create-store-image-task --image-id @AMI@ --bucket awsds-canary-does-not-exist --region us-west-2

probe root canary deny - blocked "rds:StartExportTask" -- \
  rds start-export-task --export-task-identifier awsds-canary-probe \
  --source-arn arn:aws:rds:us-west-2:@ACCT@:snapshot:awsds-canary-nonexistent \
  --s3-bucket-name awsds-canary-does-not-exist \
  --iam-role-arn arn:aws:iam::@ACCT@:role/awsds-canary-nonexistent \
  --kms-key-id alias/aws/rds --region us-west-2

# --- CREATES #1. DenyAccountBpaChangeExceptInfrastructure: the canary is on the denied side
#     of decision 7. This one really writes if the deny lifts - so the four values sent are
#     the four already set (INV: all true in all nine accounts), which makes the write a
#     no-op. A probe that cannot be blocked by a missing prerequisite is made harmless by
#     asking for the state that already exists.
probe root canary deny - creates "s3:PutAccountPublicAccessBlock (canary is NOT exempt)" -- \
  s3control put-public-access-block --account-id @ACCT@ \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# --- CREATES #2. DenyIamUserCreation. Nothing can block this one: creating a user needs no
#     prerequisite. If the deny lifts, an IAM user called awsds-canary-probe appears in
#     Policy Canary - which is why it may run nowhere else, and why the canary is emptied at
#     the end of every battery.
probe root canary deny - creates "iam:CreateUser" -- \
  iam create-user --user-name awsds-canary-probe

# --- CREATES #3. DenyEcrPublicEntirely. Same shape, and the resource it would create is
#     world-readable, which is exactly what the statement exists to prevent. Canary only.
#     NOTE the interlock: ecr-public is a us-east-1-only API, so once CT.MULTISERVICE.PV.1
#     is enabled the region control may deny it first. The policy id in the outcome column
#     is what tells the two apart (Lesson 20).
probe root canary deny - creates "ecr-public:CreateRepository" -- \
  ecr-public create-repository --repository-name awsds-canary-probe --region us-east-1

# --- the floor, on the canary
probe root canary allow - ro "floor: sts:GetCallerIdentity" -- sts get-caller-identity
probe root canary allow - ro "floor: s3:ListAllMyBuckets"   -- s3api list-buckets
probe root canary allow - ro "floor: ec2:DescribeVpcs"      -- ec2 describe-vpcs --region us-west-2
probe root canary allow - ro "floor: iam:ListRoles (global, us-east-1)" -- iam list-roles --max-items 1

# ==========================================================================
# phase: ou - the four per-OU documents, each in its own OU's account. The
# canary cannot reach these OUs, so this is the only place they can be
# measured, and the cross-checks below are what prove nothing leaks between
# them or down from the root (Lesson 20).
#
# EVERY probe here is ro, dryrun or blocked. Nothing in this phase can create
# anything in a real account even with the whole ceiling removed - which is
# the property that makes it safe to re-run at any time.
# ==========================================================================

# --- Workloads: no interactive surface, no DataZone at all
probe ou prod deny - ro "workloads: datazone:ListDomains" -- datazone list-domains --region us-west-2
probe ou prod deny 'ValidationException|ResourceNotFound|does not exist' blocked "workloads: sagemaker:CreateSpace (no such domain)" -- \
  sagemaker create-space --domain-id d-0000000000000 --space-name awsds-canary-probe --region us-west-2
probe ou prod deny 'ValidationException|does not exist' blocked "workloads: sagemaker:CreateNotebookInstance (no such role)" -- \
  sagemaker create-notebook-instance --notebook-instance-name awsds-canary-probe \
  --instance-type ml.t3.medium --role-arn arn:aws:iam::@ACCT@:role/awsds-canary-nonexistent --region us-west-2

# --- Interactive: decision 1 costs no feature, and that is the point of the two allows.
#     The nonexistent role is what keeps an "allowed" outcome from billing a notebook.
probe ou dev deny 'ValidationException|does not exist' blocked "interactive: sagemaker:CreateNotebookInstance (no such role)" -- \
  sagemaker create-notebook-instance --notebook-instance-name awsds-canary-probe \
  --instance-type ml.t3.medium --role-arn arn:aws:iam::@ACCT@:role/awsds-canary-nonexistent --region us-west-2
probe ou dev allow 'ValidationException|ResourceNotFound|does not exist' blocked "interactive: sagemaker:CreateSpace still works" -- \
  sagemaker create-space --domain-id d-0000000000000 --space-name awsds-canary-probe --region us-west-2
probe ou dev allow - ro "interactive: datazone:ListDomains still works" -- datazone list-domains --region us-west-2

# --- Sandboxes is governed by INHERITANCE and carries no policy of its own. This probe is
#     the whole evidence for that, and it is why sandbox1 appears here at all.
probe ou sandbox1 deny 'ValidationException|does not exist' blocked "sandboxes: inherits Interactive's deny" -- \
  sagemaker create-notebook-instance --notebook-instance-name awsds-canary-probe \
  --instance-type ml.t3.medium --role-arn arn:aws:iam::@ACCT@:role/awsds-canary-nonexistent --region us-west-2

# --- Data: nothing runs in the lake account
probe ou data deny - dryrun "data: ec2:RunInstances" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro --subnet-id @SUBNET@ --region us-west-2
probe ou data deny - dryrun "data: ec2:CreateFleet (7.6a)" -- \
  ec2 create-fleet --dry-run \
  --launch-template-configs '[{"LaunchTemplateSpecification":{"LaunchTemplateName":"awsds-canary-probe","Version":"1"}}]' \
  --target-capacity-specification '{"TotalTargetCapacity":1,"DefaultTargetCapacityType":"on-demand"}' --region us-west-2
probe ou data deny - dryrun "data: ec2:RequestSpotInstances (7.6a)" -- \
  ec2 request-spot-instances --dry-run --instance-count 1 \
  --launch-specification '{"ImageId":"@AMI@","InstanceType":"t3.micro","SubnetId":"@SUBNET@"}' --region us-west-2
probe ou data deny 'EntityNotFoundException' blocked "data: glue:StartJobRun (no such job)" -- \
  glue start-job-run --job-name awsds-canary-probe --region us-west-2
probe ou data deny 'EntityNotFoundException' blocked "data: glue:StartCrawler (D27 negative half)" -- \
  glue start-crawler --name awsds-canary-probe --region us-west-2
probe ou data deny 'ValidationException|ResourceNotFound|does not exist' blocked "data: sagemaker:CreateSpace (no such domain)" -- \
  sagemaker create-space --domain-id d-0000000000000 --space-name awsds-canary-probe --region us-west-2
probe ou data deny 'EntityNotFoundException' blocked "data: lakeformation:DeregisterResource (no such resource)" -- \
  lakeformation deregister-resource --resource-arn arn:aws:s3:::awsds-canary-does-not-exist --region us-west-2

# --- Identity: the same DenyUserCompute and NONE of Data's neighbours. The last two are the
#     cross-check: denied in Data, allowed here, which is what says nothing leaks from the
#     root set and the two documents differ exactly where they were written to differ.
probe ou identity deny - dryrun "identity: ec2:RunInstances" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro --subnet-id @SUBNET@ --region us-west-2
probe ou identity deny - dryrun "identity: ec2:CreateFleet (7.6a)" -- \
  ec2 create-fleet --dry-run \
  --launch-template-configs '[{"LaunchTemplateSpecification":{"LaunchTemplateName":"awsds-canary-probe","Version":"1"}}]' \
  --target-capacity-specification '{"TotalTargetCapacity":1,"DefaultTargetCapacityType":"on-demand"}' --region us-west-2
probe ou identity deny 'EntityNotFoundException' blocked "identity: glue:StartJobRun (no such job)" -- \
  glue start-job-run --job-name awsds-canary-probe --region us-west-2
probe ou identity allow 'EntityNotFoundException' blocked "identity: glue:StartCrawler is ALLOWED here" -- \
  glue start-crawler --name awsds-canary-probe --region us-west-2
probe ou identity allow 'EntityNotFoundException' blocked "identity: lakeformation:DeregisterResource is ALLOWED here" -- \
  lakeformation deregister-resource --resource-arn arn:aws:s3:::awsds-canary-does-not-exist --region us-west-2

# --- the floor, in each OU's own account
probe ou data     allow - ro "floor: s3:ListAllMyBuckets" -- s3api list-buckets
probe ou data     allow - ro "floor: glue:GetDatabases"   -- glue get-databases --region us-west-2
probe ou identity allow - ro "floor: s3:ListAllMyBuckets" -- s3api list-buckets
probe ou identity allow - ro "floor: ec2:DescribeVpcs"    -- ec2 describe-vpcs --region us-west-2
probe ou dev      allow - ro "floor: ec2:DescribeVpcs"    -- ec2 describe-vpcs --region us-west-2
probe ou prod     allow - ro "floor: ec2:DescribeVpcs"    -- ec2 describe-vpcs --region us-west-2

# ==========================================================================
# phase: region - CT.MULTISERVICE.PV.1 (step 7.7, decision 6). Meaningless
# until the control is enabled on the probed OU; until then the us-east-1 row
# reads "deny expected, ALLOWED" and that FAIL is the before-reading, not a
# bug.
#
# The pair is the point: a deny in us-east-1 alone is also what the loose
# construction (adding us-east-1 to the allowed list) would produce, so the
# us-west-2 half is what distinguishes the intended control from it.
# ==========================================================================

# The probed action needs NO resource id, and that is not a convenience - it is what keeps
# the probe working after the control starts working. The first version launched an instance
# with @AMI@, which meant resolving a public AMI **through ssm:GetParameter in the region
# being denied**: the moment the control took effect, the resolution itself was denied, the
# id came back empty, and the probe degraded to UNTESTED - reporting "not measured" at
# exactly the moment it finally had something to measure. Measured 2026-08-13, on the run
# that found the control already enabled. `create-key-pair --dry-run` authorizes with
# nothing but a name.
probe region canary deny - dryrun "region: ec2 in us-east-1 must be denied" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-east-1
probe region canary allow - dryrun "region: ec2 in us-west-2 must still work" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-west-2

# The global services that resolve in us-east-1 and must survive the control. AWS's own
# NotAction list covers these; the probes are what say so rather than assume it.
# The control is enabled per OU, so it is measured per OU. The canary above proves the
# control works; these prove it was enabled where it was meant to be - which is a different
# claim, and the one an enable-per-OU design can get wrong five times.
#
# `sandbox1` is not a repetition of `dev`: it is verification (xi)'s second half. The SCP an
# enabled control attaches is *inherited* by a nested OU whether or not that OU is itself a
# registered target, so a deny in Sandbox Account 1 says the accounts are covered and says
# nothing about which OU covers them. What distinguishes the two readings is whether the
# enablement on `Sandboxes` was *accepted*, and that is read from the OU's attached policies.
probe region data     deny  - dryrun "region: us-east-1 denied in Data Governance" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-east-1
probe region identity deny  - dryrun "region: us-east-1 denied in Identity" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-east-1
probe region dev      deny  - dryrun "region: us-east-1 denied in Development" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-east-1
probe region sandbox1 deny  - dryrun "region: us-east-1 denied in Sandbox 1 (nested OU)" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-east-1
probe region prod     deny  - dryrun "region: us-east-1 denied in Production" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-east-1

probe region data     allow - dryrun "region: us-west-2 still works in Data Governance" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-west-2
probe region identity allow - dryrun "region: us-west-2 still works in Identity" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-west-2
probe region dev      allow - dryrun "region: us-west-2 still works in Development" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-west-2
probe region sandbox1 allow - dryrun "region: us-west-2 still works in Sandbox 1" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-west-2
probe region prod     allow - dryrun "region: us-west-2 still works in Production" -- \
  ec2 create-key-pair --key-name awsds-canary-probe --dry-run --region us-west-2

# IAM answers in us-east-1 and is on AWS's NotAction list. One per account, because a region
# deny that breaks IAM breaks the account outright and the symptom is not obviously regional.
probe region data     allow - ro "region floor: iam:ListRoles in Data Governance" -- iam list-roles --max-items 1
probe region identity allow - ro "region floor: iam:ListRoles in Identity"        -- iam list-roles --max-items 1
probe region dev      allow - ro "region floor: iam:ListRoles in Development"     -- iam list-roles --max-items 1
probe region sandbox1 allow - ro "region floor: iam:ListRoles in Sandbox 1"       -- iam list-roles --max-items 1
probe region prod     allow - ro "region floor: iam:ListRoles in Production"      -- iam list-roles --max-items 1

probe region canary allow - ro "region floor: iam:ListRoles"           -- iam list-roles --max-items 1
probe region canary allow - ro "region floor: budgets:DescribeBudgets" -- budgets describe-budgets --account-id @ACCT@
probe region canary allow - ro "region floor: ce:GetCostAndUsage"      -- \
  ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-08-02 --granularity DAILY --metrics UnblendedCost
probe region canary allow - ro "region floor: organizations:DescribeOrganization" -- organizations describe-organization

# ==========================================================================
# phase: rcp - awsds-org-rcp-perimeter (step 7.8). ALL FLOOR, ON PURPOSE, and
# the absence of a deny probe here is the finding rather than an omission.
#
# WHY THERE IS NO DENY PROBE. An RCP denies principals from OUTSIDE the
# organization. Producing one needs an identity this project does not have and
# will not create: there are no IAM users (guiding principle), no second
# organization, and no external IdP. Every principal the harness can produce
# carries aws:PrincipalOrgID = our org, which is exactly the value that makes
# the deny NOT fire. That is Lesson 22 - a control whose principal the harness
# cannot produce is verified by READING, not by attempting - and the reading is
# readback.py plus ./aws/org-policies.sh, which run anyway.
#
# An anonymous request was considered and rejected as evidence: it IS denied
# (aws:PrincipalOrgID does not populate, StringNotEqualsIfExists is therefore
# true), but a public request to any bucket here is already denied by account
# BPA and by the absence of a bucket policy, and the answer names no policy. A
# probe that passes for three reasons proves none of them (Lesson 20).
#
# WHAT IS MEASURABLE IS THE HALF THAT ACTUALLY BREAKS THINGS. This RCP names
# s3, dynamodb, sqs, kms, secretsmanager, ecr and five sts actions with a
# condition keyed on a value that is ABSENT for whole classes of caller. A
# mistake does not show up as a hole; it shows up as the organization losing
# access to its own data stores, which is what the rows below detect.
# ==========================================================================

# The sts half, and it is the reason the RCP is attached to Policy Test before the root.
# EnforceOrgIdentitiesOnRoleAssumption covers AssumeRoleWithSAML and AssumeRoleWithWebIdentity,
# where the caller has NO AWS principal yet, so aws:PrincipalOrgID cannot populate and the
# IfExists form denies unconditionally. Nothing here federates that way today - Identity
# Center vends through sso:GetRoleCredentials - but "today" is the whole claim being tested,
# and the instrument is simply whether a session can still be obtained per account.
# ensure_session runs before each probe below and ABORTS the battery (exit 2) if it cannot,
# so these six rows are the AssumeRole floor even though the call they make is trivial.
probe rcp canary   allow - ro "rcp floor: credentials still vend in Policy Canary"  -- sts get-caller-identity
probe rcp dev      allow - ro "rcp floor: credentials still vend in Development"    -- sts get-caller-identity
probe rcp data     allow - ro "rcp floor: credentials still vend in Data Governance" -- sts get-caller-identity
probe rcp identity allow - ro "rcp floor: credentials still vend in Identity"       -- sts get-caller-identity
probe rcp sandbox1 allow - ro "rcp floor: credentials still vend in Sandbox 1"      -- sts get-caller-identity
probe rcp prod     allow - ro "rcp floor: credentials still vend in Production"     -- sts get-caller-identity

# One read per SERVICE named in the document. An empty result is a pass: the question is
# whether the call is authorized, not whether anything exists to return. These are the rows
# that would fail if a condition key were mistyped - a typo in `aws:PrincipalOrgID` denies
# EVERYONE, and the failure is not subtle once it is being looked for.
probe rcp canary allow - ro "rcp floor: s3 reachable"             -- s3api list-buckets
probe rcp canary allow - ro "rcp floor: dynamodb reachable"       -- dynamodb list-tables --region us-west-2
probe rcp canary allow - ro "rcp floor: sqs reachable"            -- sqs list-queues --region us-west-2
probe rcp canary allow - ro "rcp floor: kms reachable"            -- kms list-aliases --limit 1 --region us-west-2
probe rcp canary allow - ro "rcp floor: secretsmanager reachable" -- secretsmanager list-secrets --max-results 1 --region us-west-2
probe rcp canary allow - ro "rcp floor: ecr reachable"            -- ecr describe-repositories --max-results 1 --region us-west-2

# Repeated in Data Governance, which is where the buckets and the catalog will actually live
# (Stage 5) and therefore where an RCP mistake costs something. The canary is empty by design,
# so a canary-only floor measures the policy against nothing.
probe rcp data allow - ro "rcp floor: s3 reachable in Data Governance"   -- s3api list-buckets
probe rcp data allow - ro "rcp floor: kms reachable in Data Governance"  -- kms list-aliases --limit 1 --region us-west-2
probe rcp data allow - ro "rcp floor: ecr reachable in Data Governance"  -- ecr describe-repositories --max-results 1 --region us-west-2
probe rcp data allow - ro "rcp floor: glue still reads the catalog"      -- glue get-databases --region us-west-2

# ==========================================================================
# phase: tags - awsds-org-scp-tag-enforcement (step 7.8, decision 5).
#
# THE TRIPLE IS THE MEASUREMENT, not any single row. The document is two
# statements, one per required key, because two keys in ONE Null block are
# ANDed and would deny only when BOTH were missing - the opposite of the
# requirement. No denial message can name a Sid, so the two statements cannot
# be told apart by attribution; what tells them apart is the middle row, which
# supplies ONE tag and must STILL be denied. Drop it and the AND bug passes.
#
# WHERE THESE MAY NOT RUN: Data Governance and Identity, whose per-OU documents
# deny ec2:RunInstances outright (7.6a). A deny there proves nothing about this
# document and AWS names only one policy (Lesson 20). Development is the account
# where a launch is legitimate, which is what makes the third row meaningful.
# ==========================================================================

probe tags canary deny - dryrun "tags: RunInstances with NO tags" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2

# `Environment=org` is the enumerated value for every account that is not a workload
# environment - Management, Log Archive, Audit, Identity and this one. The SCP tests presence
# and not value, so this row would pass with any string; using the tag policy's own value
# keeps the two documents from drifting into disagreement about what a legal tag looks like.
probe tags canary deny - dryrun "tags: RunInstances with Environment ONLY (catches the AND bug)" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Environment,Value=org}]'

probe tags canary allow - dryrun "tags: RunInstances with BOTH tags must still work" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Environment,Value=org},{Key=Project,Value=AWS-DataScience}]'

# The same triple in Development. This is the half that says the document constrains rather
# than forbids: Stage 4's VPN endpoint and Stage 7's GitLab both launch instances here, and
# an over-broad Resource element (`*` instead of `instance/*`) denies EVERY launch, tagged or
# not, because aws:RequestTag does not populate for the subnet and security group the same
# call also references. The third row is the only thing that distinguishes the two.
probe tags dev deny - dryrun "tags: RunInstances with NO tags (Development)" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2

probe tags dev deny - dryrun "tags: RunInstances with Project ONLY (Development)" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Project,Value=AWS-DataScience}]'

probe tags dev allow - dryrun "tags: a properly tagged launch still works (Development)" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Environment,Value=development},{Key=Project,Value=AWS-DataScience}]'

# ==========================================================================
# phase: decl - awsds-org-declarative-ec2 (step 7.8).
#
# WHY THESE FOUR CARRY NO --dry-run, WHICH IS THE OPPOSITE OF EVERY OTHER EC2
# PROBE IN THIS FILE. A declarative policy is enforced in the SERVICE's control
# plane, not in authorization (AWS Organizations user guide, "How declarative
# policies work"). `--dry-run` stops after authorization and returns
# DryRunOperation, so a dry-run form would come back ALLOWED whether the policy
# is attached or not - a row that reads as a hole in the ceiling and is not one,
# every single run. Measuring the wrong layer and reporting it as evidence is
# worse than not measuring: it is Lesson 5 with a green tick on it.
#
# WHAT THEY RISK, WHICH IS WHY THEY ARE canary-ONLY. Each flips one account
# setting IF AND ONLY IF the declarative policy is not doing its job. The canary
# holds no AMI, no snapshot and no instance, so all four are inert there even
# when they succeed - and each has a one-command undo, written next to it and
# repeated in the runbook's cleanup step. If any of these comes back ALLOWED,
# run the undo before anything else.
#
# WHAT THEY PROVE THAT A READ CANNOT. ./aws/declarative-ec2.sh reads the four
# resulting VALUES, which is the authoritative check. These rows answer a
# different question: that the account is refused when it tries to change them,
# and that the caller receives OUR exception message rather than AWS's default.
# The outcome column carries `custom-message` or `AWS-default-msg`, and the
# second means the exception_message did not survive the upload.
# ==========================================================================

# undo: aws ec2 enable-image-block-public-access --image-block-public-access-state block-new-sharing
probe decl canary deny - creates "decl: ec2:DisableImageBlockPublicAccess" -- \
  ec2 disable-image-block-public-access --region us-west-2

# undo: aws ec2 enable-snapshot-block-public-access --state block-all-sharing
probe decl canary deny - creates "decl: ec2:DisableSnapshotBlockPublicAccess" -- \
  ec2 disable-snapshot-block-public-access --region us-west-2

# The one probe that ENABLES rather than disables: the policy asserts the console is off, so
# the change it must refuse is turning it on.
# undo: aws ec2 disable-serial-console-access --region us-west-2
probe decl canary deny - creates "decl: ec2:EnableSerialConsoleAccess" -- \
  ec2 enable-serial-console-access --region us-west-2

# IMDSv1 is what this asks for, and it is the one setting the document deliberately leaves as
# a DEFAULT rather than a ceiling: http_tokens_enforced is not set (7.8), so a per-launch
# override is still legal. This row is about the ACCOUNT default, which the policy does own.
# undo: aws ec2 modify-instance-metadata-defaults --http-tokens required --region us-west-2
probe decl canary deny - creates "decl: ec2:ModifyInstanceMetadataDefaults to optional" -- \
  ec2 modify-instance-metadata-defaults --http-tokens optional --region us-west-2

# The floor: reading the settings must keep working everywhere, in every account, because
# ./aws/declarative-ec2.sh depends on exactly these four calls and a policy that broke them
# would leave the project with no instrument at all.
probe decl canary allow - ro "decl floor: read image BPA state"       -- ec2 get-image-block-public-access-state --region us-west-2
probe decl canary allow - ro "decl floor: read snapshot BPA state"    -- ec2 get-snapshot-block-public-access-state --region us-west-2
probe decl canary allow - ro "decl floor: read serial console status" -- ec2 get-serial-console-access-status --region us-west-2
probe decl canary allow - ro "decl floor: read IMDS defaults"         -- ec2 get-instance-metadata-defaults --region us-west-2
probe decl dev    allow - ro "decl floor: read IMDS defaults (Development)" -- ec2 get-instance-metadata-defaults --region us-west-2

# Launching with IMDSv1 explicitly requested. This is NOT expected to be denied and the row
# says so: without http_tokens_enforced the account default is a default, and a launch may
# override it. The row exists so that the day 7.8's follow-up sets http_tokens_enforced, the
# expectation flips to `deny` and the battery measures the change instead of assuming it.
probe decl dev allow - dryrun "decl: a launch may still ask for IMDSv1 (no http_tokens_enforced yet)" -- \
  ec2 run-instances --dry-run --image-id @AMI@ --instance-type t3.micro \
  --subnet-id @SUBNET@ --region us-west-2 --metadata-options 'HttpTokens=optional' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Environment,Value=development},{Key=Project,Value=AWS-DataScience}]'
