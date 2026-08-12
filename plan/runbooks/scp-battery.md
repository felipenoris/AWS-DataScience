# Runbook — the `Policy Canary` battery

**Exercise a candidate SCP or RCP against a real principal before it reaches anything real** (D29). Written
for [Stage 1c step 7.3](../stages/stage-01c-preventive-policies.md), and **re-run whenever a policy is
amended** — Stage 6 and Stage 9 both come back to the perimeter document, and an amended policy that was
never exercised is an intention rather than a control (Lesson 5).

A policy that passed both halves is a control. One that was only attached is a hope.

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
| 2 | `aws ec2 modify-snapshot-attribute --snapshot-id snap-0000000000000000f --attribute createVolumePermission --operation-type add --user-ids 000000000000 --region us-west-2 --profile awsds-policy-canary` | `DenySnapshotAndImageSharing` | `AccessDenied` = denied. **`InvalidSnapshot.NotFound` = allowed** — the call got past the ceiling and failed on the fake id |
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

## What this battery does not cover, and where each one goes

- **The Region restriction.** It is not written in 7.5 or 7.6 — it is a Control Tower managed control
  (`CT.MULTISERVICE.PV.1`, decision 6) enabled in **7.7**. Its probe is a pair, run afterwards:
  `aws ec2 run-instances --dry-run` in `us-east-1` must return **`UnauthorizedOperation`** and in
  `us-west-2` must return **`DryRunOperation`**. Under the loose construction this plan once described —
  adding `us-east-1` to the allowed list — the first call would succeed and look like a pass.
- **The `datazone` carve-out, positive direction.** It needs a principal in the `Data` OU and a real
  execution role; it is exercised at **Stage 6**, not here. Only the negative direction is provable today.
- **The RCP, tag and declarative policies.** 7.8, in sitting B, and the RCP's denial wording differs — see
  the table above.

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
every outcome in [`log/stage-01c-preventive-policies.md`](../../log/stage-01c-preventive-policies.md)*
