# Log — Stage 2 — Terraform foundation

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`plan/stages/stage-02-terraform-foundation.md`](../plan/stages/stage-02-terraform-foundation.md).*

---

- Starting at Step 5.0. Let's set delegation to Identity account.

*One exception, recorded so the provenance is not guessed later: **the entry of 2026-08-15 below was
drafted by Claude at the user's explicit request**, from readings Claude took on the laptop in that same
session. Everything after it is the user's, as usual.*

---

## 2026-08-15 — step 5.0 reading 1, and the 5.1 document authored

**Nothing has been created, attached or changed in AWS as of this entry.** The delegation below is
written but **not applied**.

- **Step 5.0, reading 1 — `./aws/org-delegation.sh`**, as the **infrastructure user** through
  `awsds-infra-identity`. Exit 0, `0 check(s) FAILED`, `DEL-1` = **ABSENT**:

```
aws: [ERROR]: An error occurred (ResourcePolicyNotFoundException) when calling the
DescribeResourcePolicy operation: No resource-based policy found.
```

  This is the expected pre-5.1 answer and it is an *answer*, not a denial — the call was authorized and
  reported that no such policy exists. The target census in the same run reproduces the shape
  `AWS_STATE.md` records: **6 documents on the root, 4 on an OU**.

- **Three measurements taken to write the document, none of which survives in `aws/output/`:**

  - **`InfrastructureAccess` carries `arn:aws:iam::aws:policy/AdministratorAccess` and nothing else** —
    no inline policy, no customer-managed reference, no permissions boundary. So the identity-side
    already permits `organizations:*`, and the resource-based delegation is the only missing piece.
  - **The four policy-ARN type segments, read rather than deduced** — `describe-policy` on one document
    of each type returns `service_control_policy`, `resource_control_policy`, `tag_policy`,
    `declarative_policy_ec2` under `arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/`.
  - **All ten attached documents carry zero tags** (`list-tags-for-resource`, empty for each).

  It departs from the step's earlier wording in three places and excludes two things by intent; the
  reasoning for all five is now in the stage file, step 5.1, and is not repeated here. Checked against
  the nine `DEL-*` checks by reading `aws/org-delegation.sh` before applying: all nine are satisfied,
  and **`DEL-8` cannot see the operator** — it passes a `StringEquals` document that would fail every
  write.

- **Two repository corrections made in the same sitting, before the apply:** step 5.1 of the stage file
  gained the operator, the six extra reads and the tagging statement; `aws/org-delegation.sh`'s `READ`
  list was extended to match, so `DEL-4` covers what 5.1 now names.

- Login as AWS Control Tower Admin -> Management Account -> AWSAdministrator Access. AWS Oraganizations -> Settings -> Delegated administrator fow AWS Services. Used this JSON as the document:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DelegateOrganizationNavigationToIdentity",
            "Effect": "Allow",
            "Principal": { "AWS": "arn:aws:iam::<Identity Account>:root" },
            "Action": [
                "organizations:DescribeOrganization",
                "organizations:DescribeOrganizationalUnit",
                "organizations:DescribeAccount",
                "organizations:DescribePolicy",
                "organizations:DescribeEffectivePolicy",
                "organizations:DescribeResourcePolicy",
                "organizations:ListRoots",
                "organizations:ListOrganizationalUnitsForParent",
                "organizations:ListParents",
                "organizations:ListChildren",
                "organizations:ListAccounts",
                "organizations:ListAccountsForParent",
                "organizations:ListPolicies",
                "organizations:ListPoliciesForTarget",
                "organizations:ListTargetsForPolicy",
                "organizations:ListTagsForResource"
            ],
            "Resource": "*"
        },
        {
            "Sid": "DelegatePolicyLifecycleToIdentity",
            "Effect": "Allow",
            "Principal": { "AWS": "arn:aws:iam::<Identity Account>:root" },
            "Action": [
                "organizations:CreatePolicy",
                "organizations:UpdatePolicy",
                "organizations:DeletePolicy",
                "organizations:AttachPolicy",
                "organizations:DetachPolicy"
            ],
            "Resource": [
                "arn:aws:organizations::<Management Account>:root/o-4z1leiit0c/r-zhj6",
                "arn:aws:organizations::<Management Account>:ou/o-4z1leiit0c/*",
                "arn:aws:organizations::<Management Account>:account/o-4z1leiit0c/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/resource_control_policy/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/tag_policy/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/declarative_policy_ec2/*"
            ],
            "Condition": {
                "StringLikeIfExists": {
                    "organizations:PolicyType": [
                        "SERVICE_CONTROL_POLICY",
                        "RESOURCE_CONTROL_POLICY",
                        "TAG_POLICY",
                        "DECLARATIVE_POLICY_EC2"
                    ]
                }
            }
        },
        {
            "Sid": "DelegatePolicyTaggingToIdentity",
            "Effect": "Allow",
            "Principal": { "AWS": "arn:aws:iam::<Identity Account>:root" },
            "Action": [
                "organizations:TagResource",
                "organizations:UntagResource"
            ],
            "Resource": [
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/resource_control_policy/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/tag_policy/*",
                "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/declarative_policy_ec2/*"
            ]
        }
    ]
}
```

## 2026-08-15 — the delegation verified from Identity, and step 5.0 reading 2

- **The applied document is byte-for-byte the one authored above** — read back from
  `awsds-infra-identity` and compared against the source. No console reformatting, no dropped statement.

- **`./aws/org-delegation.sh`**, as the **infrastructure user** through `awsds-infra-identity`:
  `STATE: PRESENT`, exit 0, **all nine `DEL-*` checks pass**. Report in `aws/output/org-delegation.txt`.

  **`DEL-6` is the one that decided the stage's size:** the `Resource` list reaches the organization
  **root**, so `terraform-live/identity/org-policies/` is scoped to **all ten documents**, not the four
  per-OU fallback 5.0 was written to fall back to.

- **Step 5.0, reading 2 —** `organizations describe-policy` from `awsds-infra-identity` on two
  root-attached documents (`p-1fp032g8`, `p-95lyaycq7l`) and one OU-attached one (`p-gl01bcdm`):
  all three return. No read is refused at either attachment depth.

  This does **not** settle the question. The stage says only a write is evidence, and reading 3 is open.

- **One AWS constraint found by reading the procedure page, not by paraphrase:** since **2026-06-30** AWS
  rejects `NotAction` and `NotResource` in an organization delegation policy. The exemption idiom used
  freely across `policies/` is unavailable in *this* document — a document written that way fails at
  creation, not in use. The delegable actions are a published closed list, which is the first thing to
  check before any later stage widens the grant.

- **Repository work in the same sitting, no AWS call:** the three `Sid`s and the reasons this document
  stays outside Terraform are now indexed in
  [`terraform-live/identity/org-policies/POLICIES.md`](../terraform-live/identity/org-policies/POLICIES.md),
  in the one section `check-index.sh` cannot see; `AWS_STATE.md` gained **`INV-15`**; `ORGANIZATION.md`
  records the second widening of the Identity account's blast radius; step 5.0 of the stage file gained
  the mechanism for reading 3's content. `./check-index.sh` re-run: clean.

- **Next action: step 5.0 reading 3**, the deliberate write, from `awsds-infra-identity` —
  `organizations update-policy` on `p-95lyaycq7l` with the content read back from itself.

- Executed on local computer, with infrastructure user sso.

```
➜  aws git:(main) ✗ aws organizations describe-policy --policy-id p-95lyaycq7l --profile awsds-infra-identity --query 'Policy.Content' --output text | tr -d '\n' > /tmp/awsds-tagpolicy-content.json

➜  aws git:(main) ✗ aws organizations update-policy --policy-id p-95lyaycq7l --content file:///tmp/awsds-tagpolicy-content.json --profile awsds-infra-identity

```
{
    "Policy": {
        "PolicySummary": {
            "Id": "p-95lyaycq7l",
            "Arn": "arn:aws:organizations::885931358757:policy/o-4z1leiit0c/tag_policy/p-95lyaycq7l",
            "Type": "TAG_POLICY",
            "AwsManaged": false
        },
        "Content": "{\"tags\":{\"environment\":{\"tag_key\":{\"@@assign\":\"Environment\"},\"tag_value\":{\"@@assign\":[\"sandbox\",\"development\",\"data\",\"staging\",\"production\",\"org\"]}},\"project\":{\"tag_key\":{\"@@assign\":\"Project\"},\"tag_value\":{\"@@assign\":[\"AWS-DataScience\"]}},\"managedby\":{\"tag_key\":{\"@@assign\":\"ManagedBy\"},\"tag_value\":{\"@@assign\":[\"terraform\",\"console\"]}},\"owner\":{\"tag_key\":{\"@@assign\":\"Owner\"}},\"costcenter\":{\"tag_key\":{\"@@assign\":\"CostCenter\"}}}}"
    }
}
```

➜  aws git:(main) ✗ aws organizations describe-policy --policy-id p-95lyaycq7l --profile awsds-infra-identity --query 'Policy.Content' --output text | tr -d '\n' | diff -q - /tmp/awsds-tagpolicy-content.json && echo IDENTICAL
IDENTICAL
```
## 2026-08-15 — step 5.0 reading 3: the deliberate write. INT-20 answered

- **Step 5.0, reading 3** — from `awsds-infra-identity`, the content read back from the document itself
  and fed straight to the write, so the test measures the delegation and edits nothing:

```
aws organizations describe-policy --policy-id p-95lyaycq7l \
  --query 'Policy.Content' --output text | tr -d '\n' > /tmp/awsds-tagpolicy-content.json
aws organizations update-policy --policy-id p-95lyaycq7l \
  --content file:///tmp/awsds-tagpolicy-content.json
```

  **It succeeded.** `awsds-org-tag-policy` is a **root-attached** document, so INT-20's predicted
  failure — "the delegation works and still cannot touch a root attachment" — did not occur.
  **`terraform-live/identity/org-policies/` is scoped to all ten documents.** Step 5.0 is closed.

- **One thing the write did not settle, recorded so it is not mistaken for settled later:**
  `UpdatePolicy` authorizes against the **policy** ARN alone; `Attach`/`DetachPolicy` authorize against
  the **target** as well. The `root/` and `ou/` entries of the delegation are therefore still supported
  only by reading them, and step 5.5 imports existing attachments rather than creating them, so nothing
  in this stage will exercise that half either. Step 5.0 gained a **reading 4** to close it without
  mutating anything — **not yet run**.

- **`aws/org-delegation.sh` — `DEL-8`'s blind spot closed.** The check read the condition's *values* and
  discarded the *operator*, so a `StringEquals` document passed while denying every write. It now reports
  the operator and **fails** on any form without an `IfExists` suffix. Demonstrated against the live
  document with the operator name as the only edit: `StringLikeIfExists` → pass, `StringEquals` → FAIL.
  Re-run against the real delegation afterwards: **9/9, exit 0**.

- Repository: `AWS_STATE.md` `INV-15` now records the grant as *exercised* rather than present, and names
  the unexercised target half; `aws/INDEX.md` gained the operator question; the stage file carries the
  outcome, reading 4, and the corrected `DEL-8` note.

## 2026-08-15 — step 5.0 reading 4: the target half

- **Step 5.0, reading 4** — the non-mutating close on the `Resource` list's target entries, from
  `awsds-infra-identity`, against a pair read out of `aws/output/org-delegation.txt` §5 immediately before. Probing duplicate policy attachment. Executed on local aws client:

```
➜  AWS-DataScience git:(main) ✗ grep -A 20 "CLASS" aws/output/org-delegation.txt | grep "ROOT.*p-95lyaycq7l"
ROOT   Root         r-zhj6            TAG_POLICY               p-95lyaycq7l  awsds-org-tag-policy
➜  AWS-DataScience git:(main) ✗ aws organizations attach-policy --policy-id p-95lyaycq7l --target-id r-zhj6 --profile awsds-infra-identity

aws: [ERROR]: An error occurred (DuplicatePolicyAttachmentException) when calling the AttachPolicy operation: A policy with the specified name and type already exists.
```

  **`DuplicatePolicyAttachmentException`** — authorization passed and the service then refused the
  duplicate. `AttachPolicy` authorizes against target **and** policy, so `root/<org>/r-zhj6` matched a real
  call rather than a reading. Nothing was attached, detached or changed.

- **Two threads this leaves open, recorded because neither will announce itself later:**

  - **The negative control.** The duplicate answer is evidence only if IAM authorization runs *before* the
    service's duplicate check. The same call from `awsds-policy-canary` — no delegation at all — settles
    it: `AccessDenied` there makes the reading above proof, the same exception voids it.
  - **The `ou/<org>/*` entry has still never been matched by a call.** The root entry is an exact ARN;
    this one is a wildcard, and `DEL-7` reads it rather than exercising it. The same duplicate-attach
    against an already-attached per-OU pair closes it.

## 2026-08-15 — step 5.0 reading 4 completed, with its negative control. Step 5.0 CLOSED

- **The negative control, run first in reading order even though it was run second** — the same
  duplicate-attach from `awsds-policy-canary`, a principal holding no delegation at all:

```
aws organizations attach-policy --policy-id p-95lyaycq7l --target-id r-zhj6 --profile awsds-policy-canary
-> AccessDeniedException: You don't have permissions to access this resource.
```

  IAM authorization therefore runs **before** the service's duplicate check. Without this answer the two
  conflicts below would be the same answer on success and on failure, and would mean nothing.

- **The `ou/<org>/*` wildcard, the last unexercised entry that could be reached inertly** — from
  `awsds-infra-identity`, against a per-OU pair read out of `aws/output/org-delegation.txt` §5:

```
aws organizations attach-policy --policy-id p-mmfc17ac --target-id ou-zhj6-hrcu9hog
-> DuplicatePolicyAttachmentException
```

  The wildcard matches a real call. Nothing was attached, detached or changed by either command.

- **Step 5.0 is closed.** All four readings ran: the pre-delegation `describe-resource-policy`, the two
  reads, the `update-policy` write, and the target-side duplicate-attach with its control.
  `terraform-live/identity/org-policies/` is scoped to **all ten documents**.

- **What remains a reading, and cannot stop being one here:** the delegation's `account/<org>/*` entry.
  Nothing in this design is attached to an account — the census is 6 root + 4 OU — so there is no existing
  pair to aim an inert call at, and the only call that would exercise it is one that really attaches. An
  unexercised over-grant, not a gap; narrowing it later removes reach nobody uses.

- **Recorded as [Lesson 26](../plan/lessons.md)**, since the technique outlives this step: an
  "already exists" error is a free authorization probe, and it is only a measurement when paired with the
  same call from a principal known to hold nothing.


---

*Log index: [log/INDEX.md](INDEX.md) · Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md)*
