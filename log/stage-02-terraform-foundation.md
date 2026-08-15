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

---

*Log index: [log/INDEX.md](INDEX.md) · Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md)*
