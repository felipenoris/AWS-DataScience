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
#     phase        root | ou | region        (--phase filters on this)
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
#                             Canary.** There are three in this file and each is argued.
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
probe region canary allow - ro "region floor: iam:ListRoles"           -- iam list-roles --max-items 1
probe region canary allow - ro "region floor: budgets:DescribeBudgets" -- budgets describe-budgets --account-id @ACCT@
probe region canary allow - ro "region floor: ce:GetCostAndUsage"      -- \
  ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-08-02 --granularity DAILY --metrics UnblendedCost
probe region canary allow - ro "region floor: organizations:DescribeOrganization" -- organizations describe-organization
