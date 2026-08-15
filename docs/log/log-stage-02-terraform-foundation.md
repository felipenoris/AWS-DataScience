# Log — Stage 2 — Terraform foundation

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`docs/plan/stages/stage-02-terraform-foundation.md`](../plan/stages/stage-02-terraform-foundation.md).*

---

- Starting at Step 5.0. Let's set delegation to Identity account.

*Three exceptions, recorded so the provenance is not guessed later. **The entry of 2026-08-15 below was
drafted by Claude at the user's explicit request**, from readings Claude took on the laptop in that same
session. And **on 2026-08-15 the user authorised Claude, once and explicitly, to merge four corrections
into this file directly** — the open-question-11 measurement entry, which had been lost when the
disposition entry replaced it rather than following it, plus three wording fixes marked below. **Later the
same day the user granted a second such one-off authorisation**, covering: the repair of the mispaired code
fences in the reading-3 transcript (the `update-policy` output was rendering as prose), three typing fixes
in the 5.1 entry, a lead-in line naming which entry that transcript belongs to, and the steps 1/6 entry at
the end — the last written by Claude from work done on the laptop, with no AWS call in it. Everything else
is the user's, as usual, and the rule is unchanged.*

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
  `docs/AWS_STATE.md` records: **6 documents on the root, 4 on an OU**.

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

- Login as AWS Control Tower Admin -> Management Account -> `AWSAdministratorAccess`. AWS Organizations -> Settings -> Delegated administrator for AWS Services. Used this JSON as the document:

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
  [`terraform-live/identity/org-policies/POLICIES.md`](../../terraform-live/identity/org-policies/POLICIES.md),
  in the one section `check-index.sh` cannot see; `docs/AWS_STATE.md` gained **`INV-15`**; `docs/ORGANIZATION.md`
  records the second widening of the Identity account's blast radius; step 5.0 of the stage file gained
  the mechanism for reading 3's content. `./check-index.sh` re-run: clean.

- **Next action: step 5.0 reading 3**, the deliberate write, from `awsds-infra-identity` —
  `organizations update-policy` on `p-95lyaycq7l` with the content read back from itself.

- **Executed on the local computer, under the infrastructure user's SSO session. This is reading 3's raw
  transcript, and the entry that reads it is the next one.**

```
➜  aws git:(main) ✗ aws organizations describe-policy --policy-id p-95lyaycq7l --profile awsds-infra-identity --query 'Policy.Content' --output text | tr -d '\n' > /tmp/awsds-tagpolicy-content.json

➜  aws git:(main) ✗ aws organizations update-policy --policy-id p-95lyaycq7l --content file:///tmp/awsds-tagpolicy-content.json --profile awsds-infra-identity
{
    "Policy": {
        "PolicySummary": {
            "Id": "p-95lyaycq7l",
            "Arn": "arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/tag_policy/p-95lyaycq7l",
            "Type": "TAG_POLICY",
            "AwsManaged": false
        },
        "Content": "{\"tags\":{\"environment\":{\"tag_key\":{\"@@assign\":\"Environment\"},\"tag_value\":{\"@@assign\":[\"sandbox\",\"development\",\"data\",\"staging\",\"production\",\"org\"]}},\"project\":{\"tag_key\":{\"@@assign\":\"Project\"},\"tag_value\":{\"@@assign\":[\"AWS-DataScience\"]}},\"managedby\":{\"tag_key\":{\"@@assign\":\"ManagedBy\"},\"tag_value\":{\"@@assign\":[\"terraform\",\"console\"]}},\"owner\":{\"tag_key\":{\"@@assign\":\"Owner\"}},\"costcenter\":{\"tag_key\":{\"@@assign\":\"CostCenter\"}}}}"
    }
}

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

- Repository: `docs/AWS_STATE.md` `INV-15` now records the grant as *exercised* rather than present, and names
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
  duplicate answers — the root one in the entry above, the wildcard one below — would be the same answer
  on success and on failure, and would mean nothing.

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

- Configured additional aws cli profiles:

```
cat >> ~/.aws/config <<'EOF'

[sso-session awsds-ctadmin]
sso_start_url = <START_URL>
sso_region = us-west-2
sso_registration_scopes = sso:account:access

[profile awsds-ctadmin-orgfull-identity]
sso_session = awsds-ctadmin
sso_account_id = <Identity Account>
sso_role_name = AWSOrganizationsFullAccess
region = us-west-2
output = json

[profile awsds-ctadmin-orgfull-dev]
sso_session = awsds-ctadmin
sso_account_id = <Development Account>
sso_role_name = AWSOrganizationsFullAccess
region = us-west-2
output = json
EOF
```

## 2026-08-15 — open question 11: what `AWSOrganizationsFullAccess` reaches from a vended account

*(Merged back by Claude under the one-time authorisation noted at the top of this file: this entry had
been replaced by the disposition entry below rather than followed by it, leaving five documents citing a
measurement the log no longer held.)*

Measured by hand as **`AWS Control Tower Admin`** through the permission set
**`AWSOrganizationsFullAccess`**, in two accounts, using the two profiles configured at the end of the
previous entry. Raw output in `/tmp/item11-leg{1,2}-*.txt`, not kept — it carries account e-mail
addresses.

**Why those profiles exist: the permission set has no shell.** CloudShell refused with *"no identity-based
policy allows the `cloudshell:CreateEnvironment` action"* — an implicit deny with no SCP involved,
consistent with the set carrying `organizations:*` and nothing else. The measurement therefore ran from the
laptop under a second `sso-session`, which makes the standing "`AWS Control Tower Admin` is console-only"
false from today.

### Leg 1 — `<Identity Account>`, role `AWSReservedSSO_AWSOrganizationsFullAccess_3e25cf051c1ea198`

Eleven reads, eleven `exit=0`: every account, the OU tree, every SCP with id and description, and the full
`Content` of `awsds-org-scp-baseline` (`p-1fp032g8`).

**The decisive call:** `attach-policy --policy-id p-95lyaycq7l --target-id r-zhj6`, against a pair re-read
as attached one line earlier → **`DuplicatePolicyAttachmentException`**. Authorization passed:
`AttachPolicy` authorizes against target **and** policy, so the `root/…/r-zhj6` entry and the
`policy/…/tag_policy/*` class both matched and `StringLikeIfExists` did not block. It is evidence rather
than coincidence only because of the canary's `AccessDeniedException` on the same call earlier the same day
(Lesson 26), which established that IAM authorization precedes the duplicate check.

Session bracketed — `get-caller-identity` identical before and after, so nothing expired mid-battery, which
is the failure the 1c battery already produced once.

### Leg 2 — `<Development Account>`, role `AWSReservedSSO_AWSOrganizationsFullAccess_ae101c6e565bd25b`

Same user, same permission set, same calls, same two pasted ids. **Two reads succeed and nothing else:**
`describe-organization`, and `describe-effective-policy` for its own account. `list-roots`,
`list-accounts`, `list-organizational-units-for-parent`, `list-policies` (both filters), `describe-policy`,
`list-targets-for-policy`, `list-parents` and `describe-account` all return `AccessDeniedException`.
**`attach-policy` returns `AccessDeniedException`.**

### What the pair settles

1. **The organization-wide read surface belongs to the account, not to the permission set.** It exists
   because `<Identity Account>` is the Identity Center delegated administrator (1b step 1), and every
   principal there holding `organizations:*` inherits it — including one nobody chose. In an ordinary
   vended account the reach is two calls. Item 11's feared residue is **negative** for vended accounts.
2. **The write is attributable to the 5.1 delegation**, whose `Principal` is
   `arn:aws:iam::<Identity Account>:root` — the whole account, not a role.
3. So **`AWS Control Tower Admin` can create, update, delete, attach and detach all four policy types over
   the root, any OU and any account** — Control Tower's own guardrails included — without ever signing in
   to `<Management Account>`. Nothing preventive sits above it: `awsds-org-scp-ou-identity` denies only
   user compute and `CT.MULTISERVICE.PV.1` keeps `organizations:*` in its `NotAction`, both re-read in leg
   1. And **1b step 8.3's alarm cannot see this path** — it fires on group-membership change, and this user
   is already a member. The residual control is the CloudTrail record alone.

### Four things worth carrying

- **The denial wording does not classify.** Organizations returns the same `AccessDeniedException: You
  don't have permissions to access this resource` whether a call is refused for being
  management-account-only or for lacking an allow. The discriminator was never the message — it was the
  controlled A/B between two accounts, which is why the run was designed as two legs with one variable.
- **`DuplicatePolicyAttachmentException` carries the wrong message**: *"A policy with the specified name
  and type already exists"*, which is `CreatePolicy` duplicate-name text. Bind the reading to the exception
  **type**; the message matches no search about attachment.
- **`describe-organization`'s `AvailablePolicyTypes` disagrees with `list-roots`** — it lists
  `SERVICE_CONTROL_POLICY` alone, while `list-roots` lists all four `ENABLED` and matches
  `org-policies.txt`. Read policy-type status from `ListRoots`. *(A deprecated field is the likely
  explanation; that was not read from AWS documentation here, so it is not recorded as one.)*
- **In the control leg the inline "re-read the pair before aiming at it" is impossible** —
  `list-targets-for-policy` is denied there. The safety rested on leg 1's reading minutes earlier, in the
  same sitting. Acceptable for that reason only, and stated rather than inherited.

Also observed: `describe-organization` returns `MasterAccountEmail` from any member account.

## 2026-08-15 — open question 11: the disposition, and what it changed in the repository

**No AWS call in this entry.** The measurement is the previous entry; this is what was decided from it.

- **Decision: the `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins` assignment on `Identity`
  stays.** The reason is the fact that reframes the whole finding: `AWS Control Tower Admin` holds
  `AWSAdministratorAccess` on **Management**, where Organizations is native — it could always rewrite
  every SCP, Control Tower's own guardrails included. The Identity path is a redundant door, not a new
  room. Removing the assignment would close an instance the same human walks around, and would buy a
  **standing** verification in exchange, since Control Tower re-creates landing-zone assignments — the
  shape 1b's verification (vi) is already watching for.

- **Decision: the delegation gets narrowed instead**, which closes the class rather than the instance.
  Written up as **step 5.1a**: an `ArnLike` condition on `aws:PrincipalArn`, over the two *write*
  statements only, scoping them to `…AWSReservedSSO_InfrastructureAccess_*` — decision 7's idiom and
  decision 7's wildcard, because the role suffix is minted per account, which this run observed directly
  (two different suffixes for the same user in two accounts). **Not applied yet.** Its one unknown is
  whether the document accepts a principal condition at all — it already rejects `NotAction`/`NotResource`
  — and a refusal is a safe failure that changes nothing. Verification (ix) is this session's A/B run
  again, and it needs **both** halves: `AccessDenied` from `awsds-ctadmin-orgfull-identity` *and* a still
  passing `awsds-infra-identity`. The first alone is indistinguishable from a delegation broken outright.

- **What neither decision touches, recorded so it is not mistaken for handled:** one human holding
  `AWSAdministratorAccess` on Management, Log Archive and Audit at once, able to delete the record of its
  own use. That belongs to `docs/plan/institutional-delta.md`, not to this finding.

- **The preflight both legs rested on**, from `awsds-infra-identity` before either session opened:
  `./aws/org-policies.sh` for the three ids, then `list-targets-for-policy --policy-id p-95lyaycq7l`
  returning a **single** target, `ROOT r-zhj6`. That is what kept the duplicate-attach inert — and it had
  to carry both legs, because in the control account the same read is denied, so that leg could not verify
  its own target and rested on this reading, taken minutes earlier in the same sitting.

- **Token hygiene, and this is the one thing this entry leaves unanswered:** whether `aws sso logout` was
  run after the two legs is **not recorded**. It matters past tidiness — the `awsds-ctadmin` token is the
  credential, not the profile, and while it lives any new profile under that `sso-session` reaches
  `AWSAdministratorAccess` on **Management**, which is the concentration the bullet above names. The two
  `awsds-ctadmin-orgfull-*` profiles themselves are scoped and were deliberately kept.

- **Repository, same sitting, no AWS call:** `docs/plan/open-questions.md` item 11 rewritten from question to
  closed finding plus the two decisions; step 5.1a and verification (ix) added to the stage file;
  `POLICIES.md`'s blast-radius paragraph corrected — it claimed 1b step 8.3's alarm as the control, and
  that alarm fires on group-membership *change* while this principal is already a member, so the residual
  is the CloudTrail record alone; `docs/AWS_STATE.md` A.1 no longer points at Stage 1c for the measurement;
  `CLAUDE.md` and `docs/log/INDEX.md` brought current.

## 2026-08-15 — steps 1 and 6: the repository skeleton and the hygiene gates

**No AWS call in this entry.** Everything below is local: the tree, the version pin, and the gates that run
before a commit.

- **Step 1 — the pin, recorded here because two of this stage's verifications are phrased "in the pinned
  provider version":** `required_version = "~> 1.15"` (Terraform 1.15.8 on this laptop) and
  `hashicorp/aws = "~> 6.60"`, resolving to **6.60.0** in the lock file.

- **The tree created is smaller than `docs/plan/conventions.md` §6, deliberately.** Five `bootstrap/` slices
  — `sandbox`, `development`, `data-governance`, `production`, `identity` — plus `terraform-modules/`. No
  `staging/` (unvended, step 3.2). The rest of §6 is not on disk: git does not track empty directories, so a
  full skeleton means ~35 `.gitkeep` files, which is a second copy of §6's listing in the form that drifts
  most quietly and that no reader consults. Each slice folder is created by the stage that first writes a
  `.tf` into it, and **§6 stays the one place the layout is written down**.

- **`versions.tf` is byte-identical in all five slices** (`md5`, one unique hash). Terraform has no
  repository-wide pin, so the constraint is repeated per root module; step 9's check is what keeps the copies
  together (Lesson 14).

- **Step 6.3 — the lock file was generated once and copied**, not generated five times: it is a function of
  the version constraint and the platform list only, and `versions.tf` is identical by construction, so five
  separate runs would download the provider fifteen times for the same bytes. Three `h1:` hashes present —
  `darwin_arm64` (this laptop), `linux_amd64` and `linux_arm64` (the Stage 7-8 runners, on Graviton per D8).
  `TF_PLUGIN_CACHE_DIR` exported first, since `terraform_validate` runs `init` per slice and would otherwise
  fetch its own copy of the provider each time.

- **Step 6.1 — the tooling, and it needed two different routes.** `pre-commit` **4.6.2** and `checkov`
  **3.3.11** are Python and went in with `uv tool install`, one command each. `tflint` is a Go binary and this
  laptop has no `brew`, `go`, `npm` or `docker`, so it came from a signed release download with a checksum
  check: **`tflint` v0.64.0**, in `~/local/bin`. All three are now in `CLAUDE.md`'s tool list.

- **The install is not the whole setup, and the difference costs a confusing failure.** `tflint`'s rulesets
  are **plugins downloaded on demand**, so with the binary on `PATH` the hook still failed until
  `tflint --init` was run against `.tflint.hcl` (it fetched `tflint-ruleset-aws` **0.48.0**, the pinned
  version). A fresh clone on another machine needs that second command too, which is why it is written at the
  top of `.tflint.hcl` rather than left to be rediscovered from an error message.

- **Step 6.2 — `.gitignore`**: the Terraform section added, including the **`*.tfstate`** the previous version
  of the step omitted — the local bootstrap state of 2.2, the one file this stage most insists must never be
  committed. Also `backend.hcl` unconditionally, and `*.tfvars`/`*.tfvars.json` wholesale. The lock file is
  protected by an explicit `!.terraform.lock.hcl`, and confirmed addable with `git add -n` rather than with
  `git check-ignore`, whose exit status also reports a negated match.

- **Steps 6.4 and 6.5 — `pre-commit install` run, and the chain demonstrated end to end** against the new
  `versions.tf` files:

```
fix end of files / trim trailing whitespace / check merge conflicts /
check added large files / detect private key ........................ Passed
Terraform fmt ....................................................... Passed
Terraform validate .................................................. Passed
Terraform validate with tflint ...................................... Passed
checkov (terraform) ................................................. Passed
```

  `detect-private-key` is in that list for D36's root CA. checkov is a `language: system` local hook, so it
  binds to the version recorded above instead of a second copy `pre-commit` would build at a version nobody
  chose.

- **Zero checkov suppressions taken, and this is the reason rather than a silence.** 6.5 asks that
  suppressions be recorded at the first run; the first run had no resource to judge — the slices hold only a
  version pin. The suppressions the step predicts (state-bucket access logging, cross-region replication)
  arrive with step 2 and will be recorded then.

- **`scripts/gen-backend-hcl.sh` written** — step 2.5's helper, needed before steps 2, 3 and 5 run `init`. It
  holds the region literal once for the whole tree, applies D36's separate PKI state key for
  `production/pki/`, and refuses both an unknown account folder and a slice directory that does not exist.
  Both refusals exercised. Its map exists because **folder, name token and `Environment` tag value are three
  different vocabularies**, not two — `development` / `dev` / `development` — and confusing the first with the
  second produces a bucket name nobody created.

- **One correction found by reading the hook's source rather than by recall:** `terraform_validate` takes
  **`--tf-init-args=`**, not `--init-args=`. The wrong spelling is accepted as an unknown argument and the
  init runs without it, so the failure would not have been an error message — it would have been a hook
  demanding AWS credentials on every commit.

- **Repository, same sitting:** the stage file's **Status** row now records steps 5.0, 5.1, 1 and 6 as closed
  and names step 9 as next; its tooling-absent finding is struck through; 6.1 carries the install and the
  `--init`. `CLAUDE.md` gained the steps 1/6 bullet, and two older bullets were compressed to keep the file
  under the 20 KB its own check enforces. `docs/REFERENCES.md` gained the four tool references. Link check
  after the documentation was consolidated under `docs/`: **1044 links resolve, none broken.**

## 2026-08-15 — step 9: the four checks, and the two surfaces that run them

**No AWS call in this entry.** Everything below is local. Step 9.3 is **written but not yet run**: it
needs an SSO session and is recorded as open at the end.

- **Four checks, two enforcement surfaces, the same scripts behind both** — so the commit gate and the
  `make` target cannot disagree, and Stage 8 step 6 adds a third caller rather than a rewrite:

  | Check | Script | Runs in |
  |---|---|---|
  | 9.1 | `scripts/check-tf-conventions.sh` | `make check` + `pre-commit` on any `*.tf` |
  | 9.2 | `scripts/check-iam-wildcards.sh` | `make check` + `pre-commit` on `terraform-live/identity/**` |
  | 9.3 | `scripts/check-ou-coverage.sh` | **`make check-ou` only** — needs a session |
  | 9.4 | `terraform-live/identity/org-policies/check-index.sh` | `make check` + `pre-commit` on `policies/` or `POLICIES.md` |

- **`Makefile` created** with `check`, `check-ou`, `check-docs`, `check-all`. It is the same file step 8
  will add `up`/`down`/`status` to.

- **The authored OU→document map is a file, and it is the file step 5 will read:**
  `terraform-live/identity/org-policies/attachments.json` — the root's six documents, the four OU pairs,
  and the three OUs that carry none with the reason each is empty. Names, never ids. One file, two
  consumers: 9.3's check and step 5's `for_each`.

- **`check-plan-refs.sh` was deliberately left out of `make check` and given `make check-docs`.** It is
  **red today**, on prose that predates this stage: `stage-01c`, `stage-01d` record dated measurements
  phrased as *"all six accounts with a profile"*, and the check cannot tell a historical measurement from
  a count that goes stale. Unresolved — it is either a check that needs a date-aware exemption or three
  sentences to rewrite, and it was not decided here.

- **Two defects found by testing the check rather than by reading it, both in 9.1 and both silent:**

  - **The first `perl` form did not compile.** It printed its error on stderr, matched nothing, and
    reported `none` over a fixture holding all three violations — the same output as a clean tree
    (Lesson 13). The scanner's exit status is now checked and a failed scan is a `FAIL`.
  - **`$.` counts cumulatively across the file list.** Without `close ARGV if eof`, a violation on line 2
    of the sixth file was reported as line 162 of a three-line file.

- **Demonstrated failing, which is the deliverable.** With a region literal and a wildcard-account ARN
  staged together, `pre-commit` exits 1 and three hooks go red — 9.1, 9.2, and 9.4 on the new document
  with no row in `POLICIES.md`. Each of 9.1's three rules was also fired separately against a fixture, as
  was the scanner-failure path. Fixtures deleted, index restored.

- **Green afterwards:** `make check` exit 0; the twelve-hook `pre-commit` chain passes `--all-files`;
  1045 links resolve.

- **Repository, same sitting:** stage file — status row, the step 9 record, 5.3 point 1 and 9.3 now name
  `attachments.json`, the deliverable marked met; `terraform-live/README.md` and
  `identity/org-policies/README.md`; `README.md` gained the `Makefile` and the checks; `CLAUDE.md`
  brought current and re-trimmed to stay under its 20 KB budget.

- **Open, and the next action:** run 9.3 against the organization, as the **infrastructure user** on
  **Identity** through **`InfrastructureAccess`** (`awsds-infra-identity`):

  ```
  aws sso login --sso-session awsds
  make check-ou
  ```

  Its section 4 compares what is attached against what `attachments.json` authors. A disagreement there
  means the map — written from today's snapshot — is wrong and must be corrected **before step 5 reads
  it**, not after.

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
