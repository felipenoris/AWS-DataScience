# Runbook — the `Policy Canary` battery

**Exercise a candidate SCP or RCP against a real principal before it reaches anything real** (D29). Written
for [Stage 1c step 7.3](../stages/stage-01c-preventive-policies.md), and **re-run whenever a policy is
amended** — Stage 6 and Stage 9 both come back to the perimeter document, and an amended policy that was
never exercised is an intention rather than a control (Lesson 5).

A policy that passed both halves is a control. One that was only attached is a hope.

> ## The probes are a script now — [`aws/probes/`](../../aws/probes/README.md)
>
> ```bash
> ./aws/probes/scp-battery.sh              # read-back, then every phase
> ./aws/probes/scp-battery.sh --phase ou   # root | ou | region
> ./aws/probes/scp-battery.sh --list       # what would run, and where
> ```
>
> **This file stayed, and the division of labour is the point.** The script executes and classifies; this
> runbook is *why each probe is shaped the way it is* and what each outcome means — which is the part that
> cannot be automated and the part a reader needs before trusting a green run. The probe list itself lives
> in `aws/probes/probes.sh`, so **amending the ceiling means editing that file**, and the tables below are what
> tell you what to write in it.
>
> Three things the script encodes because the hand-run version kept getting them wrong: a dead SSO session
> **aborts** instead of being recorded as a battery of denies; the outcome is read from the error *wording*
> and never from the exit code; and each probe declares the wording that proves *that action* reached
> authorization, so anything else is reported `UNTESTED` rather than assumed allowed. **What the script does
> not do is attach anything** — policy changes stay a deliberate act by a human on the Management console.

## The two identities, and why each one is the one it is

| Role in the battery | Identity | Why not the other one |
|---|---|---|
| The **subject** — the principal every probe runs as | `awsds-policy-canary`, which is Control Tower's `AWSAdministratorAccess` as a **direct** assignment (D32) | An SCP is a *ceiling*. A deny exercised by a principal that lacked the permission anyway proves nothing, so the subject has to be an administrator |
| The **attacher** — `create-policy`, `attach-policy`, `detach-policy` | **`AWS Control Tower Admin` on Management**, console or CloudShell | Management is exempt from SCPs by AWS's design (D16). It is the whole recovery path, which is why it is open *before* the first attach and not after |
| One probe only — the decision-7 carve-out, positive direction | `awsds-infra-dev` (`InfrastructureAccess`) | That probe asks whether the carve-out matches. The canary's principal is deliberately *outside* it |

`Policy Canary` is alone in the `Policy Test` OU, so a candidate attached to that OU reaches exactly one
account. **A document attached to the organization root reaches the canary too**, because `Policy Test`
hangs off the root like every other OU — which is what makes the root set testable here at all.

## Before the first attach

1. Management console open, signed in as `AWS Control Tower Admin`. **A precondition, not a precaution.**
2. The detach command written down with the id blank, and the id filled in **as each policy is attached**:

   ```bash
   aws organizations detach-policy --policy-id <POLICY_ID> --target-id <TARGET_ID>
   ```

3. `./terraform-live/identity/org-policies/render.sh` has been run, and **the paste comes from
   `aws/output/rendered-policies/`** — the tracked templates still hold placeholders.
4. Account-level BPA reads all four flags `true` in every account (7.4 step 1). The baseline document
   denies changing it; attached first, it would deny the call that sets it.

## How to read every outcome

**`AccessDenied` alone is not the evidence.** An SCP deny, a missing grant and someone else's bucket policy
are indistinguishable at the CLI. The discriminating string is in the error body:

| Wording | What denied it |
|---|---|
| *"with an explicit deny in a service control policy"* | an SCP — the answer these probes are looking for |
| *"with an explicit deny in a resource control policy"* | an RCP (7.8) |
| *"with an explicit deny in an identity-based policy"* | the permission set, **not** the ceiling — the probe is measuring the wrong thing |
| no explicit-deny clause at all | an implicit deny: nothing granted it. Same note — wrong thing measured |
| *"`ForbiddenException` … `GetRoleCredentials`: No access"*, on **every profile at once** | **not a probe result — the sign-in path itself is denied.** Indistinguishable from an expired token at the exit code, which is why the battery reads the wording: it prints `FAIL … NO-CREDENTIALS` per account, marks every probe behind it untested, and keeps going. The tell that it is the ceiling and not the token: **Management still answers and the member accounts do not**, because RCPs do not apply to the management account (Lesson 24) |

**A vended credential outlives the attach that should have broken it, and that is how a bad policy passes
its own probes.** An Identity Center role session is cached in `~/.aws/cli/cache` for **four hours**
(measured), so a document that denies the *sign-in* changes nothing until the next `GetRoleCredentials` —
the probes run straight after the attach are answered by a session minted before it existed. Before probing
anything that could reach STS, sign-in or federation, force a fresh vend:

```bash
rm -f ~/.aws/cli/cache/*.json && aws sts get-caller-identity --profile awsds-policy-canary
```

**The error body also names the policy, and this plan under-sold it until 2026-08-13.** An SCP denial ends
with `… with an explicit deny in a service control policy: arn:aws:organizations::…/service_control_policy/p-xxxxxxxx`
— **the policy id, in the CLI response itself**, no CloudTrail and no lag. That is what makes it survivable
to have several candidates parked on `Policy Test` at once. **Its one limit, and it decides whether a
document was really exercised:** when more than one attached policy denies the same call, AWS names **one**
of them, so a document can be attached and never be the deciding one — attached is not exercised. Isolate
it, or re-probe it after it reaches its own OU, where nothing else denies that action.

**Prefer a probe whose two outcomes are different errors over one whose outcomes are success and failure.**
`--dry-run`, a non-existent resource id, and a call that needs no resource all give that shape, and none of
them leaves anything behind in an account whose whole point is to stay empty.

## Phase 0 — the *must still succeed* half, before anything is attached

Run as `awsds-policy-canary`. This is the controlled comparison; without it, a failure later cannot be
attributed to the policy rather than to the account.

```bash
aws sts get-caller-identity --profile awsds-policy-canary
```

```bash
aws s3 ls --profile awsds-policy-canary
```

```bash
aws ec2 describe-vpcs --region us-west-2 --profile awsds-policy-canary --query 'Vpcs[].VpcId'
```

```bash
aws iam list-roles --profile awsds-policy-canary --query 'Roles[0].RoleName'
```

```bash
aws budgets describe-budgets --account-id <CANARY_ACCT> --region us-east-1 --profile awsds-policy-canary
```

`s3:ListAllMyBuckets` is `aws s3 ls` with no bucket named. **`s3:ListBucket` is a different action, about
the objects inside one bucket** — naming the wrong one is how a battery produces a false pass. The last two
answer in `us-east-1` and are here because 7.7's Region control must not break them.

### The throwaway resources, created once and deleted in the same sitting

The one exception to "nothing is ever created in `Policy Canary`" (`plan/conventions.md`) — the same
exception the battery already makes for `iam:CreateUser`. **Plan the cleanup before the call, not after it.**

```bash
BUCKET="awsds-canary-throwaway-$(date +%s)"; echo "$BUCKET"
```

```bash
aws s3 mb "s3://$BUCKET" --region us-west-2 --profile awsds-policy-canary
```

```bash
aws ecr create-repository --repository-name awsds-canary-throwaway --region us-west-2 --profile awsds-policy-canary
```

Both are written to *inside* this organization, so they are also the *must still succeed* target for
phase 3. Baseline them now, with nothing attached — both must work:

```bash
echo probe | aws s3 cp - "s3://$BUCKET/probe.txt" --profile awsds-policy-canary
```

```bash
aws ecr initiate-layer-upload --repository-name awsds-canary-throwaway --region us-west-2 --profile awsds-policy-canary
```

`initiate-layer-upload` returns an upload id and uploads nothing. It needs no image and no Docker.

## Phase 1 — the perimeter, tested by its complement, on `Policy Test` only

**The obvious test cannot be run and its evidence would not exist.** There is no bucket outside this
organization to write to, and `s3:PutObject` is a CloudTrail *data* event that the Control Tower trail does
not record — so the record would be missing in success and in failure alike (Lesson 13, in the verification
rather than in the control). What *can* be wrong is the condition, so the condition is what gets exercised.

Attach `canary/awsds-canary-scp-perimeter-inverted.json` — the real statement with one comparison flipped,
`StringEqualsIfExists` where production has `StringNotEqualsIfExists` — to the **`Policy Test` OU**, never
to the root.

```bash
aws organizations create-policy --name awsds-canary-scp-perimeter-inverted --type SERVICE_CONTROL_POLICY --description "THROWAWAY - Stage 1c step 7.3 battery. Detach and delete in the same sitting." --content file://aws/output/rendered-policies/awsds-canary-scp-perimeter-inverted.json
```

```bash
aws organizations attach-policy --policy-id <POLICY_ID> --target-id <OU_ID_POLICY_TEST>
```

Then re-run the two writes from phase 0. **Both must now fail, naming an explicit deny in a service control
policy**, and each proves something the other does not:

| Probe | Denied | Succeeded |
|---|---|---|
| `aws s3 cp - s3://$BUCKET/probe.txt` | the `IfExists` pair evaluates as written, and the deny reaches an ordinary principal | the condition never fired — read the rendered JSON before touching anything else |
| `aws ecr initiate-layer-upload` | `aws:ResourceOrgID` **populates on an ECR request** | it does not populate for ECR, and the production statement would be inert there |

**The ECR probe is not redundant.** Key population is a property of each service's authorization, not of the
policy, so the S3 run says nothing about it.

Then, in this order: detach, delete the policy, and **leave the bucket and repository in place for phase 3**.

```bash
aws organizations detach-policy --policy-id <POLICY_ID> --target-id <OU_ID_POLICY_TEST>
```

```bash
aws organizations delete-policy --policy-id <POLICY_ID>
```

**What this does not prove**, stated so nobody reads more into it: that a write to a genuinely external
bucket is denied. That rests on the production document being the complement of the tested one — a
one-character review — and it is the honest limit of a lab with a single organization.

## Phase 2 — `awsds-org-scp-baseline.json` on the organization root

Attach, then run every probe below. One policy at a time: a batch that breaks tells you something in the
batch is wrong, which is the least useful form of that information.

```bash
aws organizations attach-policy --policy-id <POLICY_ID> --target-id <ROOT_ID>
```

### Must now fail — as `awsds-policy-canary`, and none of these creates anything

| # | Probe | Statement | Denied vs allowed |
|---|---|---|---|
| 1 | `aws iam create-user --user-name awsds-canary-probe --profile awsds-policy-canary` | `DenyIamUserCreation` | **No dry-run exists.** If it succeeds, a user was created — `aws iam delete-user --user-name awsds-canary-probe` immediately |
| 2 | ~~`aws ec2 modify-snapshot-attribute --snapshot-id snap-…`~~ **— unrunnable with a fake id, measured 1c** | `DenySnapshotAndImageSharing` | EC2 rejects an invented snapshot id as `InvalidSnapshotID.Malformed` **before authorizing, `--dry-run` included**, so no fake-id probe reaches the SCP. It needs a *real* snapshot. Left untested in 1c on the argument that the statement carries **no condition** and probe 3 exercises the same statement — so the only untested thing is the spelling of one action string, which is a read. Create a volume and a snapshot if that argument is ever not enough |
| 3 | `aws ec2 modify-image-attribute --image-id ami-0000000000000000f --launch-permission "Add=[{UserId=000000000000}]" --region us-west-2 --profile awsds-policy-canary` | same statement, separate action — snapshot controls do not cover EBS-backed AMIs | `AccessDenied` vs `InvalidAMIID.NotFound` |
| 4 | `aws ecr-public describe-registries --region us-east-1 --profile awsds-policy-canary` | `DenyEcrPublicEntirely` | The deny is `ecr-public:*`, so even this read must fail. A registry list = the deny is not reaching the namespace |
| 5 | `aws guardduty delete-detector --detector-id 00000000000000000000000000000000 --region us-west-2 --profile awsds-policy-canary` | `DenyGuardDutyTampering` | `AccessDenied` vs `BadRequestException`. **Inert until Stage 4 turns GuardDuty on** — this probe is what says the statement is nonetheless live |
| 6 | `aws datazone create-domain --name awsds-canary-probe --domain-execution-role arn:aws:iam::<CANARY_ACCT>:role/nonexistent --region us-west-2 --profile awsds-policy-canary` | `DenyDataZoneDomainOutsideDataOu` | `AccessDenied` = denied. Any validation error about the role = allowed. The canary is **not** in the `Data` OU, so this is the negative direction |
| 7 | `aws s3control put-public-access-block --account-id <CANARY_ACCT> --profile awsds-policy-canary --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true` | `DenyAccountBpaChangeExceptInfrastructure`, **negative direction** | Must fail. If it succeeds it is harmless — the values are the ones already set — but the carve-out is matching a principal it should not |

### Must still succeed — the decision-7 carve-out, and it is the load-bearing probe of this phase

**As `awsds-infra-dev`, not as the canary.** Same call, same values, a principal *inside* the carve-out:

```bash
aws s3control put-public-access-block --account-id <DEV_ACCT> --profile awsds-infra-dev --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

**This is the one probe whose failure is silent in the expensive direction.** `aws:PrincipalArn` for an
assumed role resolves to the **IAM role ARN** — `arn:aws:iam::<acct>:role/aws-reserved/sso.amazonaws.com/<region>/AWSReservedSSO_…`
— **not** the `arn:aws:sts::<acct>:assumed-role/…` form that `sts:GetCallerIdentity` prints and that 1b's log
is full of. A carve-out written from that output matches nothing, and a carve-out that matches nothing means
**every future account is permanently without account-level BPA and no principal anywhere can set it**
(there is no cross-account API for it). If this probe is denied, detach the baseline document before doing
anything else.

Then re-run all of phase 0. Denies compose, so a *must still succeed* failure here is real regardless of
which policy caused it.

### Deliberately not tested: `organizations:LeaveOrganization`

**Do not probe it.** It is the one statement whose "allowed" outcome is the damage: a successful call
removes `Policy Canary` from the organization, dropping every SCP and every Control Tower control for it,
and the account comes back only through a re-invitation it has no billing profile to accept. The statement
is verified by review of the rendered JSON and by the fact that its neighbours in the same document
evaluate — which is weaker evidence, and is written down as weaker rather than quietly counted as a pass.

## Phase 3 — `awsds-org-scp-perimeter.json` on the organization root

The complement of phase 1, on the real document. Attach it, then run the two writes from phase 0 against
the surviving throwaway bucket and repository. **Both must succeed**: the resources are inside this
organization, so `aws:ResourceOrgID` matches and the deny must not fire.

A failure here is the production statement over-reaching — the direction phase 1 could not test, and the one
that would break `docker push` to your own registry and every module that writes to your own buckets.

Then clean up, in this order:

```bash
aws s3 rm "s3://$BUCKET" --recursive --profile awsds-policy-canary && aws s3 rb "s3://$BUCKET" --profile awsds-policy-canary
```

```bash
aws ecr delete-repository --repository-name awsds-canary-throwaway --force --region us-west-2 --profile awsds-policy-canary
```

## Phase 4 — the four per-OU documents (step 7.6), one at a time

**These are the first documents with a second, better place to exercise them**, and using only the canary
would waste it. A per-OU document is attached to an OU the canary is not in, so the canary can only test it
while it is parked on `Policy Test` — but each target OU already holds an account with a profile, and a
probe there measures the document *where it will actually live*, composed with everything above it:

| Document | Parked on `Policy Test` for | Then attached to | And re-probed as |
|---|---|---|---|
| `awsds-org-scp-ou-workloads` | the deny half | `Workloads` | `awsds-infra-prod` |
| `awsds-org-scp-ou-data` | the deny half | `Data` | `awsds-infra-data` |
| `awsds-org-scp-ou-interactive` | the deny half | `Interactive` | `awsds-infra-dev` **and** `awsds-infra-sandbox-1` — the second one is the nested-OU reading, and it is free here |
| `awsds-org-scp-ou-identity` | the deny half | `Identity` | `awsds-infra-identity` |

**It is one policy object, moved — not created twice.** `create-policy` once, `attach-policy` to
`Policy Test`, probe, `detach-policy` from `Policy Test`, then `attach-policy` to the real OU. The
throwaway-and-delete shape of phase 1 belongs to the *inverted* document, which must never reach anything
real; these four are the real documents and their id is the one recorded in the log. **Left attached to
both targets, a document governs an OU nobody meant to govern** — and `Policy Canary` would then be carrying
a tier written for someone else's OU into every later battery.

**Check the SSO token immediately before each block of probes.** It expired twice during sitting A, and
both times every probe came back as a non-answer that reads exactly like a deny.

### The probes, by document

Every one of them is shaped so that *both* outcomes are errors and nothing is created. Where the service
validates its input before authorizing — which 1c already met twice — the probe measures nothing, and the
honest record is *untested*, not *passed*.

| Document | Probe | Denied | Allowed |
|---|---|---|---|
| workloads | `aws datazone list-domains --region us-west-2` | `AccessDenied` naming an SCP | a list, empty or not — the namespace deny is not reaching reads |
| workloads | `aws sagemaker create-space --domain-id d-0000000000000 --space-name awsds-canary-probe --region us-west-2` | `AccessDenied` | `ValidationException` / `ResourceNotFound` = SageMaker validated first, so **untested** |
| workloads | `aws sagemaker start-session --resource-identifier arn:aws:sagemaker:us-west-2:<ACCT>:space/d-0000000000000/none` | `AccessDenied` | any validation error = untested |
| data, identity | `aws ec2 run-instances --dry-run --image-id <REAL AMI> --instance-type t3.micro --subnet-id <REAL SUBNET>` | `UnauthorizedOperation`, naming the policy | `DryRunOperation` = allowed |
| | **Both ids must be real, and that is the whole trick** (measured 2026-08-13): an invented AMI returns `InvalidAMIID.Malformed`, a well-formed but non-existent one `InvalidAMIID.NotFound`, and omitting the subnet `VPCIdNotSpecified` — **all three before authorization**, so the naive probe reports "untested" and reads like a pass. Take the AMI from the public SSM parameter and the subnet from the account itself; `--dry-run` still creates nothing: `aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text` and `aws ec2 describe-subnets --query 'Subnets[0].SubnetId' --output text` | |
| data, identity | `aws glue start-job-run --job-name awsds-canary-probe --region us-west-2` | `AccessDenied` | `EntityNotFoundException` |
| data | `aws glue start-crawler --name awsds-canary-probe --region us-west-2` | `AccessDenied` — **the negative half of the D27 carve-out** | `EntityNotFoundException` = the `ArnNotEquals` matched a principal it should not |
| data | `aws lakeformation deregister-resource --resource-arn arn:aws:s3:::awsds-canary-does-not-exist --region us-west-2` | `AccessDenied` | `EntityNotFoundException` |
| data | `aws s3api delete-bucket --bucket awsds-canary-does-not-exist-$(date +%s)` | `AccessDenied` | `NoSuchBucket` — **which is what it actually returns** (measured 2026-08-13): S3 checks existence before authorizing, so this probe measures nothing and `s3:DeleteBucket` is recorded **untested**. Its statement is not: `lakeformation:DeregisterResource` sits in the same `Sid` and *was* denied, so what is unverified is the spelling of one action string, which is a read. Testing it for real costs a bucket that cannot then be deleted until the policy moves — **name a bucket that cannot exist** rather than a real one |
| interactive | `aws sagemaker create-notebook-instance --notebook-instance-name awsds-canary-probe --instance-type ml.t3.medium --role-arn arn:aws:iam::<ACCT>:role/nonexistent --region us-west-2` | `AccessDenied` | a role/validation error. **The nonexistent role is deliberate**: it is what keeps an "allowed" outcome from billing a notebook instance |

**The positive half of the D27 carve-out cannot be run in this stage and is recorded as such.**
`awsds-data-catalog-maintenance` does not exist until [Stage 5](../stages/stage-05-data-foundation.md), so
"the maintenance role *can* start a crawler" is **untested until Stage 5**, where it is the first thing to
check after the role is created — before anything is wired to trigger it. A carve-out that silently matches
nothing is a job that will not run, and it does not announce itself.

**Then the *must still succeed* half, in the target account rather than in the canary.** After each real
attachment, from that OU's own profile: `aws sts get-caller-identity`, `aws s3 ls`, and
`aws ec2 describe-vpcs --region us-west-2`. Denies compose, so a failure here is real no matter which
document caused it — and this is the half the canary cannot give you for these four.

### Amending a **root** document is phases 1-3, not phase 4b

**The distinction is which targets the document reaches.** A per-OU document is attached to one OU the
canary is not in, so an amendment to it can only be measured in that OU's own account — phase 4b below.
The two root documents reach **`Policy Canary` as well**, which means the canary is available again and the
amendment goes back through the normal battery: probe the amended statements there, confirm the *must still
succeed* floor, and only then treat it as done. `update-policy` replaces the content in place and the id
does not change, so nothing is created, moved or detached.

**The 2026-08-13 amendment to `awsds-org-scp-baseline`** — five GuardDuty actions and the new
`DenyImageAndSnapshotExport` statement:

| Probe (from `awsds-policy-canary`) | Denied | Allowed |
|---|---|---|
| `aws guardduty disassociate-from-administrator-account --detector-id 00000000000000000000000000000000 --region us-west-2` | `AccessDenied` naming the policy — **this is the whole point of the amendment**, the modern spelling that used to be open | `BadRequestException` / detector-not-found = validated first, **untested** |
| `aws guardduty update-detector --detector-id 00000000000000000000000000000000 --no-enable --region us-west-2` | `AccessDenied` | validation error = untested. Regression only: it was already denied |
| `aws ec2 create-store-image-task --image-id <REAL public AMI> --bucket awsds-canary-does-not-exist --region us-west-2` | `UnauthorizedOperation` | an AMI validation error = untested. **The AMI must be real** — measured 2026-08-13: `ami-0123456789abcdef0` returns `InvalidAMIID.Malformed`, the public Amazon Linux AMI reaches authorization and is denied |
| `aws ec2 export-image --image-id ami-0123456789abcdef0 --disk-image-format VMDK --s3-export-location S3Bucket=awsds-canary-does-not-exist --region us-west-2` | `UnauthorizedOperation` | validation error = untested. **This one authorizes even with a malformed AMI**, which is the whole point of the rule below |
| `aws ec2 create-instance-export-task --instance-id i-1234abcd --target-environment vmware --export-to-s3-task '{"S3Bucket":"awsds-canary-does-not-exist","DiskImageFormat":"VMDK","ContainerFormat":"ova"}' --region us-west-2` | `UnauthorizedOperation` | validation error = untested |
| `aws rds start-export-task --export-task-identifier awsds-canary-probe --source-arn arn:aws:rds:us-west-2:<ACCT>:snapshot:nonexistent --s3-bucket-name awsds-canary-does-not-exist --iam-role-arn arn:aws:iam::<ACCT>:role/nonexistent --kms-key-id alias/aws/rds --region us-west-2` | `AccessDenied` | `DBSnapshotNotFound` = untested |

> ### Before recording *untested*, retry with a **real** resource id
>
> **The validation-before-authorization wall is per-action, not per-service, and this was measured rather
> than assumed (2026-08-13).** In the same account, in the same run: `ec2:ExportImage` and
> `ec2:CreateInstanceExportTask` authorized against a **malformed** id and came back denied, while
> `ec2:CreateStoreImageTask` rejected the same shape of id as malformed and only reached authorization once
> a **real public AMI** was passed. `ec2:StartInstances` never reached it at all — a 17-character id is
> rejected as `Malformed` and an 8-character one as `NotFound`, both before authorization.
>
> So "the service validates first" is a property of the API being probed, and **a first-try validation error
> is a reason to retry, not a result**. Reach for something that exists: the public Amazon Linux AMI from
> SSM, a subnet from `describe-subnets`, the account's own id in an ARN. Recording *untested* on the first
> error understates the ceiling — a statement that is in fact exercised gets carried in the notes as
> unproven, and the next reader spends an evening re-testing it.

### Phase 4b — re-probing an amended document, in place

**An amendment is not a smaller version of phase 4; it is the same phase with a shorter probe list.** Once a
document sits on its real OU, `update-policy` replaces its content in place and the id does not change — so
there is nothing to park on `Policy Test` and nothing to move. What must happen is that **every statement
the amendment touched is probed again in that OU's own account**, plus the *must still succeed* trio, before
the sitting is called done. A document amended and not re-probed is a document whose last measurement
describes a version that no longer exists.

**The 2026-08-13 amendment — the EC2 launch siblings in `awsds-org-scp-ou-data` and
`awsds-org-scp-ou-identity`, and the service guard on the D27 carve-out:**

| Where | Probe | Denied | Allowed |
|---|---|---|---|
| `awsds-infra-data`, `awsds-infra-identity` | `aws ec2 request-spot-instances --dry-run --instance-count 1 --launch-specification '{"ImageId":"<REAL AMI>","InstanceType":"t3.micro","SubnetId":"<REAL SUBNET>"}' --region us-west-2` | `UnauthorizedOperation`, naming the policy | `DryRunOperation`. **Same real-ids trick as `run-instances`** — an invented AMI or a missing subnet is rejected before authorization |
| `awsds-infra-data`, `awsds-infra-identity` | `aws ec2 start-instances --dry-run --instance-ids i-1234abcd --region us-west-2` | `UnauthorizedOperation` | `InvalidInstanceID.NotFound` = validated first, **untested** — which is what it returned on 2026-08-13, in both accounts and at both id lengths |
| `awsds-infra-data`, `awsds-infra-identity` | `aws ec2 create-fleet --dry-run --launch-template-configs '[{"LaunchTemplateSpecification":{"LaunchTemplateName":"awsds-canary-probe","Version":"1"}}]' --target-capacity-specification '{"TotalTargetCapacity":1,"DefaultTargetCapacityType":"on-demand"}' --region us-west-2` | `UnauthorizedOperation` on `…:fleet/*` | a launch-template error = untested. **This was predicted to be untestable and is not**: `--dry-run` authorizes *before* resolving the launch template, so a template name that does not exist still produces a real answer |
| `awsds-infra-data` | `aws glue start-crawler --name awsds-canary-probe --region us-west-2` | `AccessDenied` | `EntityNotFoundException` = the carve-out matched a principal it should not. **Re-run after the guard was added**: `BoolIfExists` evaluates *true* when the key is absent, so a human principal must still land on the deny side — if this one flips to allowed, the guard is inverted and the whole carve-out is open |

**The guard's own effect cannot be probed from a CLI session**, because `aws:PrincipalIsAWSService` is set by
AWS, not by the caller: there is no way to present as a service principal on purpose. What the re-run above
proves is the half that matters for regression — that adding the guard did not open the deny for people.

## Phase 5 — step 7.8's four documents, one attach at a time

**7.8 is the first sitting where the four documents are not all the same kind of thing**, and the ordering
below is not taste: each document is attached alone, measured, and only then is the next one touched. Two of
them break in ways the previous phases have no equivalent for.

| Order | Document | Attach to | Measure with | Undo |
|---|---|---|---|---|
| 1 | `awsds-org-scp-tag-enforcement` | root | `--phase tags` | detach |
| 2 | `awsds-org-tag-policy` | root | `./aws/org-policies.sh` — no probe exists | detach |
| 3 | `awsds-org-rcp-perimeter` | **`Policy Test` OU first**, root after | `--phase rcp` | detach |
| 4 | `awsds-org-declarative-ec2` | root | `--phase decl` **and** `./aws/declarative-ec2.sh` | detach **rolls state back** |

### 1 — the tag-enforcement SCP, and why the middle probe is the whole test

`--phase tags` is six rows and only the pattern is evidence. The **before** reading was taken 2026-08-13 in
`Development`: all four command forms returned `DryRunOperation`, so an untagged launch succeeded. After the
attach, the two untagged and the two single-tag rows must read `DENY-SCP` and the two fully tagged rows must
still read `DryRunOperation`.

**A run where every row denies is a failure, not a strict pass.** It is what an over-broad `Resource` element
produces: `aws:RequestTag` does not populate for the subnet, security group or volume that the same
`RunInstances` call references, so `Resource: "*"` denies every launch, tagged or not. The fully tagged row
is the only thing that separates the intended control from that.

### 2 — the tag policy, which has no probe and is not supposed to have one

It carries no `enforced_for`, so it **reports** and prevents nothing; there is no call it refuses and
therefore nothing for the battery to attempt. It is read, not probed:

```bash
aws organizations describe-effective-policy --policy-type TAG_POLICY --profile awsds-infra-dev --region us-east-1
```

Reading a compliance *report* needs the Resource Groups Tagging API and a resource population this project
does not have yet — Stage 2 is where that becomes meaningful. Until then the attach is verified by the
effective policy answering at all.

### 3 — the RCP, which is staged because the failure mode is a lockout

**Attach it to the `Policy Test` OU first and leave it there until `--phase rcp` is green.** The reason is
`EnforceOrgIdentitiesOnRoleAssumption`: for `sts:AssumeRoleWithSAML` and `sts:AssumeRoleWithWebIdentity` the
caller has **no AWS principal yet**, so `aws:PrincipalOrgID` cannot populate and the `StringNotEqualsIfExists`
form denies **unconditionally**.

**On 2026-08-14 that is exactly what happened, and this section used to end the paragraph above with the
sentence that caused it:** *"nothing federates that way today — Identity Center vends through
`sso:GetRoleCredentials`"*. It is false. **Identity Center *is* the external federation**: every account
holds a SAML provider `AWSSSO_<id>_DO_NOT_DELETE`, and the trust policy of `AWSReservedSSO_*` permits
**only** `sts:AssumeRoleWithSAML` + `sts:TagSession` from it — read it and see, it is two lines. The document
named both, so the root attach made every permission-set role in all six member accounts unreachable, by
CLI and by browser alike. The document is now scoped to `sts:AssumeRole` + `sts:SetContext`, matching AWS's
own `CT.STS.PV.1`, whose usage note is the authority on which STS actions may not appear here.

**So the rule that replaces the old claim: before adding any `sts:` action to an RCP, read the trust policy
of the role that action reaches.** A statement that names an action a *trust policy* depends on is not a
perimeter — it is a lockout, and it will not announce itself as one.

Between the two attaches, and this is the step that cannot be delegated to a script: **sign in to `Policy
Canary` through the access portal in a browser, as the infrastructure user** — not as `AWS Control Tower
Admin`, who has no assignment there at all. `Policy Canary` is reached by the infrastructure user's
**permanent direct assignment** of `AWSAdministratorAccess` (`ORGANIZATION.md`; Stage 1b step 3.8), which is
the same identity behind the `awsds-policy-canary` profile. The CLI path and the console path are not the
same path — 8.3's filter already showed the console emitting `sso.amazonaws.com` where the CLI emits
something else — and only the console login exercises the federation half.

If it locks the canary out: **detach from the Management account, which is exempt from RCPs.** That exemption
is the reason this staging is safe, and it is also the reason the root attach must never be the first one.
It is also the only reason the 2026-08-14 lockout was recoverable rather than terminal — **the recovery path
is the console as `AWS Control Tower Admin` on `Management`, and it works precisely because RCPs cannot
reach it.** Verify that identity still signs in *before* attaching an RCP that touches STS, not after.

**The staging only proves something if the canary's credentials are re-vended between the two attaches** —
see the cache rule under *How to read every outcome*. The first attempt at this section's procedure ran the
`Policy Test` probes on a session minted before the attach, they passed, and the document went to the root
on that evidence.

The `rcp` phase is **all floor and no deny**, which is a finding rather than an omission — see the block at
the top of that phase in `probes.sh`. Producing an out-of-organization principal needs an identity this
project does not have and will not create, so the deny half is Lesson 22: verified by `readback.py` and
`./aws/org-policies.sh`, never by attempting.

### 4 — the declarative policy, the only document that changes state

Three things separate it from every other document in `policies/`:

- **It is enforced in the service's control plane, not in authorization.** It names no policy id and emits no
  *"explicit deny"* wording. The attribution is the **exception message**, which is why the document sets a
  custom one — and the `decl` phase reports `custom-message` or `AWS-default-msg` precisely so that an
  `exception_message` lost in the upload is visible.
- **`--dry-run` measures the wrong layer.** It stops after authorization and returns `DryRunOperation`
  whether or not the policy is attached. The four probes therefore carry **no** `--dry-run` and are
  `creates`, canary-only; each has a one-command undo written beside it in `probes.sh`. **If any comes back
  `ALLOWED`, run its undo before doing anything else** — the canary has been left in the state the policy
  exists to prevent.
- **Attaching changes existing settings**, and detaching **rolls each attribute back** to what it was before.
  So "attached" and "in effect" are two facts. `./aws/declarative-ec2.sh` is what reads the second, and it is
  the authoritative check; the probes only show that the account is refused when it tries to change them.

**It is also the first root-attached document expected to reach the management account.** SCPs and RCPs skip
Management by design; AWS documents no such exemption for declarative policies, and control-plane enforcement
is not where that exemption lives. **This is unmeasured** — run `./aws/declarative-ec2.sh -` in CloudShell on
Management, as `AWS Control Tower Admin`, and record the answer. It is a reading nobody else will take.

### The canary cleanup gains four commands

The existing step empties `Policy Canary` after a battery. Add, and only if the corresponding `decl` row came
back `ALLOWED`:

```bash
aws ec2 enable-image-block-public-access --image-block-public-access-state block-new-sharing --region us-west-2 --profile awsds-policy-canary
```

The other three are in `probes.sh` next to their probes: `enable-snapshot-block-public-access`,
`disable-serial-console-access`, and `modify-instance-metadata-defaults --http-tokens required`.

## What this battery does not cover, and where each one goes

- **The Region restriction.** It is not written in 7.5 or 7.6 — it is a Control Tower managed control
  (`CT.MULTISERVICE.PV.1`, decision 6) enabled in **7.7**. Its probe is a pair, run afterwards:
  `aws ec2 run-instances --dry-run` in `us-east-1` must return **`UnauthorizedOperation`** and in
  `us-west-2` must return **`DryRunOperation`**. Under the loose construction this plan once described —
  adding `us-east-1` to the allowed list — the first call would succeed and look like a pass.
- **The `datazone` carve-out — *neither* direction, and this was measured rather than assumed.** DataZone
  validates `--domain-execution-role` **before** authorizing, so a call with a throwaway role returns
  `Cross-account pass role is not allowed` and never reaches the SCP. The same error comes back from the
  exempt account (`awsds-infra-data`), which is what proves the probe measures nothing — an authorization
  difference would have made the two accounts differ. It needs a role DataZone accepts, so it is
  **[Stage 6 step 0](../stages/stage-06-unified-studio.md)**, run before the domain is created rather than
  after. Note the direction of the risk: `ForAllValues:` over a key that does not populate evaluates
  **true**, so the untested failure is the deny applying to *everyone*, `Data` included.
- **The RCP's deny half.** Phase 5 covers 7.8, but the RCP is measured **only on its floor**: an
  out-of-organization principal is an identity this project cannot produce, so the deny is read and never
  attempted (Lesson 22, and the table below).
- **A tag policy's compliance report.** It enforces nothing and refuses no call, so there is nothing to
  probe; it needs a resource population that does not exist before Stage 2.
- **The positive half of the `Data` OU's catalog-maintenance carve-out** — phase 4 says why, and Stage 5 is
  where it is answered.

### The class the battery cannot reach at all — verified by *reading*, never by attempting

**A green run is silent about these, which is why they are listed by name** (Lesson 22). Every principal
this project can obtain is an Identity Center role, so any statement whose condition selects a principal of
a kind the harness cannot produce is invisible to a probe **in both directions** — the call is never made,
nothing is recorded, and an absent row reads exactly like a covered one. The discriminator when a new
statement is written: *can the harness produce a principal that satisfies this condition?* If not, the
verification is a document read, and the plan states the string that proves it.

| Statement | Why no probe reaches it | What to read instead |
|---|---|---|
| `GRRESTRICTROOTUSER` (Control Tower, per OU) | conditioned on `ArnLike aws:PrincipalArn = arn:*:iam::*:root`; no SSO role ever matches | `organizations describe-policy` on the OU's guardrail — **`aws:AssumedRoot` must appear** in the condition (the `ExemptAssumeRoot` parameter). Missing it denies `sts:AssumeRoot` into every account beneath, which is 1a step 6's only member-account recovery |
| positive half of D27's catalog-maintenance carve-out | the exempted role does not exist until Stage 5 | the `ArnNotEquals` value against the role Stage 5 creates |
| positive half of the `aws:PrincipalIsAWSService` guard | needs a service principal, which cannot be assumed | the `BoolIfExists` clause is present and spelled `false` |
| all four statements of `awsds-org-rcp-perimeter` | an RCP denies principals from **outside** the organization; there is no IAM user, no second organization and no external IdP here, so every principal the harness can produce carries the org id that makes the deny *not* fire | `readback.py` (four `Sid`s, correct action counts) and the org id in each `StringNotEqualsIfExists`. An anonymous request is denied for three other reasons and names no policy — it proves nothing (Lesson 20) |

**All three are checked mechanically by [`aws/org-policies.sh`](../../aws/org-policies.sh)**, which reads
the deployed documents and exits 2 if any of them stops saying what it must — run it after every attachment,
in the same sitting as the battery. It is a *different instrument*, not a phase of the battery, and that is
the whole point.

**This is the one place where "0 untested" in the driver's summary is not the whole answer** — the driver
counts probes that ran, and these were never probes. Re-read this table whenever a policy is amended.

## The canary's one permanent limitation

**Once the root set is attached, `Policy Canary` inherits it forever**, so every later candidate is tested
*on top of* the existing ceiling rather than in isolation. That is right for regression — it is the real
evaluation order — and wrong for answering "does *this policy* deny X", because denies only ever compose: a
call that fails may be failing on the root set. The half that stays clean is *must still succeed*, which
composition can only make stricter. For the deny half, read the CloudTrail `errorMessage`, which names the
policy id.

---

*Stage: [1c step 7.3](../stages/stage-01c-preventive-policies.md) · Decision:
[D29](../decisions/D29-policy-canary.md) · Documents:
[`terraform-live/identity/org-policies/`](../../terraform-live/identity/org-policies/README.md) · Record
every outcome in [`log/log-stage-01c-preventive-policies.md`](../../log/log-stage-01c-preventive-policies.md)*
