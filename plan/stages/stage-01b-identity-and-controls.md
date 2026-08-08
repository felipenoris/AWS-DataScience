# Stage 1b — Identity, policies, detective controls, org-wide enablement

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 1a complete |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D29](../decisions/D29-policy-canary.md), [D30](../decisions/D30-scp-recovery.md), [D31](../decisions/D31-approver-read.md) |
| **Proves** | [INT-11](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

Everything in 1b is fast, reversible and iterative — which is exactly why it is separated from the half
that is not.

1. **Register the Identity account as delegated administrator of IAM Identity Center (D10).** From the
   Management account:
   `aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com`.
   This is reversible (`deregister-delegated-administrator`), so it is a cheap step to get wrong.
   Everything in steps 2 and 3 is then done **from the Identity account**, not from Management.
2. In IAM Identity Center, create the **four** users from `ACCOUNTS_AND_USERS.md` (e-mails in
   `secrets/emails.md`) and the groups `infrastructure`, `data-scientists`, **`deployment-managers`** and
   **`governance-managers`**. Enforce MFA. The two manager groups were one group (`managers`) until
   2026-08-08; they were split because the two approvals they carry sit on different axes and, more to the
   point, because one persona holding both means a single human can write a job that reads restricted
   data, approve its release *and* approve its access to that data — three acts, one signature.
   **Never put the same person in both groups**, even while there is only one human: the moment that
   happens the split is notation again, and nothing in AWS will warn you.
3. Create permission sets: `AdministratorAccess` (infrastructure), `DataScientistAccess` (the Interactive
   OU), `DeploymentManagerAccess` (deployment-managers). An earlier draft also created a `DeployApprover`
   permission set; it was
   dropped — the deploy approval gate lives in GitLab (Stage 8), driven by GitLab group membership, and
   consumes no AWS-side permission. Create such a permission set only when something actually consumes it.
   **Note that `DeploymentManagerAccess` is not that set coming back:** the *approval* still consumes no AWS
   permission; this set exists for the other half of the job, which is **diagnosis** — reading why a
   promotion failed before deciding whether to release it.
   **The two approver permission sets are the ones whose *denials* are the point of them, and until
   2026-08-08 only one of them was written that way.**
   **`GovernanceManagerAccess`.** The governance manager approves who may read data, so their own reach must
   stop at the *catalog*, not the
   rows: Glue catalog metadata read, Lake Formation LF-Tag and permission administration, DataZone domain
   ownership, Macie findings read — and **no `s3:GetObject` on lake prefixes and no Athena workgroup**. An
   approver who can already read everything is not exercising a control when they approve a subscription.
   **`DeploymentManagerAccess` (D31), which used to be the AWS-managed `ReadOnlyAccess` and should not have
   been.** The argument above is symmetric and the plan applied it to one approver only. `ReadOnlyAccess` on
   four accounts reaches the D19 derived zones — where the output of a query over `restricted` data lives
   and, by D19's own classification rule, *is* `restricted` — and reaches `athena:GetQueryResults`, which
   returns other people's query output. So it is replaced by a set in the same shape as
   `DataScientistProdAccess` (D18): CloudWatch Logs read including Logs Insights (diagnosing a failed
   promotion is the job), SageMaker job/pipeline/Model Registry **status**, Glue catalog metadata, ECR image
   metadata and scan findings, Step Functions and EventBridge Scheduler execution status, and
   `s3:GetObject` on **enumerated** prefixes only — build artifacts and test reports, never a bucket
   wildcard. Denied explicitly rather than by omission: **`athena:*`** (both starting a query and reading
   someone else's results), **`kms:Decrypt`**, `secretsmanager:GetSecretValue`, `ssm:GetParameter*`, the
   Terraform state buckets, and the control plane in full.
   One precision worth carrying, because it is why the old arrangement looked harmless: `ReadOnlyAccess`
   grants no `athena:StartQueryExecution` and no `kms:Decrypt`, so it could never *originate* a read of the
   lake and could not decrypt an SSE-KMS object at all. The exposure was being prevented by encryption
   rather than by design — which stops being true the first time a bucket is created without a CMK.
   **`DataScientistAccess` does not start as `PowerUserAccess`.** An earlier version of this plan gave it
   `PowerUserAccess` "until Stage 6", which contradicts `ACCOUNTS_AND_USERS.md` ("no permissions to
   perform infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let
   the data scientist create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the
   whole design — for five stages. It starts as: SageMaker Studio use, read/write on the account's scratch
   and derived prefixes, Athena, ECR pull, and nothing else. `AmazonSageMakerFullAccess` is *not* a safe
   starting point either: it grants `s3:*` on any bucket with "sagemaker" in the name plus a broad
   `iam:PassRole`. Attach a permissions boundary and scope `PassRole` per the IAM rules in `plan/conventions.md` §6.
   **One set, two targets (D21):** `DataScientistAccess` is assigned on Sandbox *and* Development — the
   two accounts are policy-identical at this level (that is what putting them in one OU asserts), and what
   differs between them is the work, not the permission shape.
   **A second permission set targeting Production (D18)** —
   `DataScientistProdAccess`, and it is a different shape, not a weaker copy: **data plane read, no
   compute, no control plane.** It grants CloudWatch Logs read, Glue catalog metadata read, SageMaker
   job/pipeline/Model Registry *status* read, `s3:GetObject` on named application-output prefixes, and
   Athena on the dedicated workgroup from Stage 9, and nothing else. It denies, explicitly rather than by
   omission: the control plane, `sagemaker:Create*Job`, `sagemaker:CreatePresignedDomainUrl`,
   `glue:StartJobRun` and `lakeformation:GrantPermissions`. GitLab and ECR access (D14) folds into this
   set rather than living as a separate grant. (The ingestion drop-box moved with the lake to Data
   Governance, D22 — it is granted by bucket policy to the Interactive-OU roles, not by this set.)
   **And a third, `DataScientistStagingAccess` (D20)** — read-only, with no write of any kind, not even a
   drop-box. Staging exists to be written by the pipeline and read by a human working out why the pipeline
   failed; a staging environment a person can write to stops being evidence of what the pipeline actually
   does. Same denies as the Production set, minus every write grant.
   Assign them: infrastructure → the six Terraform-managed accounts (Sandbox, Development, Data
   Governance, Staging, Production, Identity) **plus `AdministratorAccess` on `Policy Canary` (D29)** —
   which is not a seventh Terraform-managed account but the test principal for step 7, and it has to be an
   administrator or the test measures the wrong thing: an SCP is a ceiling, so a deny that a restricted
   principal could not have exercised anyway proves nothing about the ceiling; data-scientists →
   `DataScientistAccess` on Sandbox and Development, `DataScientistStagingAccess` on Staging,
   `DataScientistProdAccess` on Production, **no assignment of any kind on Data Governance** (D18/D22);
   deployment-managers → `DeploymentManagerAccess` on Sandbox, Development, Staging and Production (the
   approval itself happens in GitLab; this set is for diagnosis, D31), and **nothing on Data Governance** —
   a release approver has no business in the account that grants data access; governance-managers → `GovernanceManagerAccess` on **Data
   Governance only**, which is the mirror image: the one account the deployment manager cannot enter is the
   only one the governance manager can.
   The data scientist gets no access to Identity, Audit, Log Archive or Policy Canary — the last one
   matters less than it looks, since the account is empty, but an account whose whole purpose is to have
   broken permissions is not somewhere a second persona should be able to sign in and draw conclusions.
   Leave Control Tower's own permission sets untouched — editing them causes landing-zone drift.
   These are created by hand here only because Terraform cannot run before SSO login works; Stage 2 moves
   them into `terraform-live/identity/` and imports them.
4. The infrastructure user's assignment **on the Management account itself** has to be created from the
   Management account — the delegated administrator cannot manage assignments targeting Management.
   This is the one identity task that stays there permanently.
5. **Configure the local SSO profiles now, not at the end of the stage.** `aws configure sso` for
   `awsds-infra-sandbox`, `awsds-infra-dev`, `awsds-infra-staging`, `awsds-infra-prod`, `awsds-infra-data`
   and `awsds-infra-identity` — plus one more that is deliberately named differently,
   **`awsds-policy-canary`** (D29). It is not an `awsds-infra-*` profile because `Policy Canary` is not a
   Terraform-managed account and nothing is ever applied into it; the profile exists only to run step 7's
   test battery, and the naming keeps that visible in shell history. **This used to be step 10 and that was
   an ordering bug:** every step below
   this one does CLI or console work *inside a member account* — restricting the Config recorder, enabling
   Object Lock on the Log Archive bucket, raising the Lake Formation cross-account version in Data
   Governance, reading AZ IDs per account — and none of it is reachable without a profile. Doing it here
   also gives the first real proof that steps 1-4 worked.
6. **Check the AZ name-to-ID mapping** across the Sandbox, Development and Production accounts
   (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
   profile). D14 and D21 make this matter for real: both peerings into Production are free within an AZ
   and USD 0.01/GB each way across AZs, so a mismatch has a bill attached. See `plan/open-questions.md` item 3. Cheap to do here,
   and Stage 3 needs the answer before it writes a subnet.
7. **Preventive policies.** Attach to the OUs, in this order. They come in tiers, one per OU policy set
    (D23), on top of an organization-root set that applies everywhere.

    **Every `Deny` statement written below carries the D30 recovery carve-out, and getting its shape right
    matters more than any individual policy.** The condition excludes the `awsds-scp-recovery` role so that
    a mistaken policy can be repaired from inside the affected account. Two things about how it is written:

    - **`ArnNotEquals` with an enumerated list of role ARNs, never `ArnNotLike` with a wildcard account.**
      `arn:aws:iam::*:role/awsds-scp-recovery` would exempt a role of that name in *any* account — which
      means anyone able to create a role anywhere in the organization can name their way out of every deny
      you ever write. List the ARNs explicitly, one per governed account.
    - **A companion deny in the same set**, on `iam:CreateRole`, `iam:PutRolePolicy`, `iam:AttachRolePolicy`
      and `iam:UpdateAssumeRolePolicy` for that role name, so the exemption cannot be minted or widened
      from inside a governed account. Without it the enumerated list buys less than it looks like.

    The role itself does not exist yet — it is `[P]` and is created in each account's `foundation/` slice in
    Stage 3. **Order this deliberately:** either write the policies now with the carve-out condition
    referring to ARNs that do not yet resolve (which is legal — IAM conditions on non-existent principals
    simply never match, so the deny applies to everyone until Stage 3, i.e. the safe direction), or attach
    the policies without the carve-out and add it in Stage 3. The first is preferable because it means the
    policy text never changes shape later; record which you did.
    - **`Workloads` OU** (D20): deny `sagemaker:CreateDomain`, `sagemaker:CreateUserProfile` and
      `sagemaker:CreatePresignedDomainUrl` — this is what turns D17 from an intention into a control:
      "no Studio outside the Interactive OU" cannot be undone by anyone with a console and a good reason.
    - **`Data` OU** (D22): deny compute creation outright (`ec2:RunInstances`, `sagemaker:Create*`,
      `glue:CreateDevEndpoint`, **`glue:CreateJob` and `glue:StartJobRun`** — added by D25, because the
      original list left a Glue ETL job as a perfectly legal way to run the whole ingestion in the account
      whose entire policy set says nothing runs there — and ECS/Lambda creation), deny `s3:DeleteBucket`
      and `lakeformation:DeregisterResource`. The lake account's SCP is about what can never happen there,
      because nothing is supposed to *run* there at all.
    - **`Interactive` OU** (D21): no extra SageMaker denies — Studio is the point — but the same
      no-infrastructure guardrails as everywhere else. The differences between Sandbox and Development
      are differences of content, not of policy, which is why they share the OU.
    - **SCPs:** deny leaving the organization, deny disabling CloudTrail/Config/GuardDuty, restrict usable
      regions to `us-west-2` — the region SCP must still allow `us-east-1`, because IAM, Organizations,
      Route 53, CloudFront and Support only have endpoints there — and **deny writes to S3 resources
      outside this organization** (`aws:ResourceOrgID`), which is the trusted-resources axis of `plan/architecture.md` §4.2 and
      closes the most direct exfiltration route a notebook has. Two more, cheap and load-bearing:
      **deny `iam:CreateUser` and `iam:CreateAccessKey`** — principle 2 ("no IAM Users") is otherwise a
      convention with no enforcement, and break-glass (D16) is unaffected because the Management account
      is exempt from SCPs — and **deny `s3:PutAccountPublicAccessBlock`**, which protects the
      account-level setting enabled below.
    - **RCPs:** deny access to S3, STS, KMS, SQS and Secrets Manager from principals outside the
      organization (`aws:PrincipalOrgID`) — the trusted-identities axis of `plan/architecture.md` §4.2.
    - **Tag policies:** standardize the mandatory tags from `plan/conventions.md` §6 — with a precision the previous version of
      this plan got wrong: tag policies constrain *tagging operations*, they cannot force a resource to be
      created with tags at all. The forcing function is an SCP with `aws:RequestTag`/`aws:TagKeys`
      conditions on the create actions that matter (EC2, S3, SageMaker). One or the other, or the tags are
      a convention — and conventions do not survive contact with a `terraform apply` at 23:00.
    - **Account-level S3 Block Public Access** in every member account. The module-level block from
      Stage 2 only covers buckets the module creates; the account-level setting is the blanket that also
      covers the bucket someone creates outside it. Protected by the SCP above.
    - **Declarative policies:** enforce IMDSv2 and EC2 public-access defaults org-wide.
    **Every one of these is attached to the `Policy Test` OU first and exercised from `Policy Canary`
    before it goes anywhere real (D29).** An SCP mistake is the fastest way to lock yourself out of your
    own organization — recoverable, because the Management account is exempt from SCPs and the break-glass
    path from 1a step 5 exists, but recoverable is not the same as cheap. The procedure, and it is a
    procedure rather than a gesture:

    - **One policy at a time.** Attach, test, record, then move on. A batch that breaks tells you that
      something in the batch is wrong, which is the least useful form of that information.
    - **Test in both directions, because the two failure modes are opposites.** *Too tight* — run the calls
      that must still **succeed** (an `sts:GetCallerIdentity`, a `s3:ListBuckets`, an `ec2:DescribeVpcs` in
      `us-west-2`, and for the region SCP specifically an `iam:ListRoles`, which only lives in `us-east-1`).
      *Too loose* — run the calls that must now **fail**: a `PutObject` to a bucket outside the
      organization, an `iam:CreateUser`, an `ec2:RunInstances` in a denied region. A policy that denies
      nothing fails silently and leaves you believing you have a control (Lessons 5 and 13 in `CLAUDE.md`),
      and only this half of the battery catches it.
    - **From an administrator principal**, which is why 1b step 3 assigns `AdministratorAccess` here. An
      SCP is a ceiling; a deny exercised by a principal that lacked the permission anyway proves nothing.
    - **And, from Stage 3 onwards, a third direction: the D30 carve-out itself.** Assume
      `awsds-scp-recovery` in `Policy Canary` and confirm it *can* do the denied thing, then confirm a
      plain administrator *cannot*. A carve-out that silently fails to match is a recovery path you find
      out you do not have on the night you need it — and that is precisely the class of failure `Policy
      Canary` exists to catch.
    - **With the detach command written down and the Management account already open** before the first
      attach. Verify you can reach it *now*, not in theory.
    - Then move the attachment to its real target — the OU named in each bullet above, or the organization
      root for the org-wide set. Note that the root-level policies can be exercised here exactly as they
      will behave in production, because `Policy Test` sits under the root and inherits from it like every
      other OU.

    Record each outcome. A policy that passed both halves of the battery is a control; one that was only
    attached is a hope.
8. **Detective controls** (principle 9 — these belong to the landing zone, not to Stage 11). The
    *delegation* of each service to the Audit account runs **from the Management account**
    (`enable-organization-admin-account` / `register-delegated-administrator`, one manual console action
    per service — consistent with principle 1); everything after that is done from the Audit account:
    enable org-wide **Security Hub**, **IAM Access Analyzer** (external access, and unused access for
    Stage 12) and **GuardDuty**. Watch the cost of GuardDuty's S3 Protection and Malware
    Protection against D12 — enable the base service now and decide on those two with a real bill in hand.
9. **Make the audit trail tamper-evident:** enable **S3 Object Lock** on the Control Tower Log Archive
    bucket and **CloudTrail log file validation**. An audit log that the compromised party can edit is not
    an audit log. Do this before there is anything worth hiding in it.
10. **Restrict the AWS Config recorder** to the resource types this project actually uses. Config is the
    main recurring cost of the landing zone (`plan/cost-model.md`) and the default records everything, in eight accounts.
11. **Enable organization-wide resource sharing, so the Lake Formation shares of Stage 5 can exist**
    (D22, INT-11). Three separate settings, **in three different accounts** — which is half of why
    this step is easy to get wrong — and none of which announces its absence:
    - **`ram:EnableSharingWithAwsOrganization`, called from the *Management* account.** It enables trusted
      access for RAM across the organization; it is not a Data Governance setting and cannot be done from
      there. Without it, a Lake Formation grant to another account produces an AWS RAM *invitation* that
      somebody has to accept by hand, and it reappears every time the share is recreated. With it, accounts
      inside the organization receive shares directly.
    - **Lake Formation cross-account version 3 or above**, set **in the Data Governance account**. Versions
      below 3 cannot grant to an Organization or an OU at all, only to an explicit list of account IDs —
      and this project has three consumers with more implied by every `plan/institutional-delta.md` row about scale.
    - The **`AWSLakeFormationCrossAccountManager`** managed policy on the grantor (Data Governance), and
      `ram:AcceptResourceShareInvitation` on the data lake administrator role **in each consumer account**,
      which is the fallback path if the two settings above are ever unavailable.

    **How to verify it, because the obvious command does not.** `aws ram get-resource-share-associations`
    requires an `--association-type` and lists the associations of shares that already exist — with no
    share yet created it returns an empty list, which is indistinguishable from the failure it is supposed
    to detect. The check that actually answers the question is
    `aws organizations list-aws-service-access-for-organization` from the Management account, looking for
    `ram.amazonaws.com`; and, for the second setting,
    `aws lakeformation get-data-lake-settings --profile awsds-infra-data`, reading the cross-account
    version back. Confirming a silent-failure mode with a command that is itself silent is how INT-11
    stays open for a month.

    This step is here rather than in Stage 5 because it is organization-level and manual, like everything
    else in this stage. Stage 5 step 7 assumes it and will fail confusingly without it: the grant appears
    to succeed on the producer side and the resource simply never shows up on the consumer side.

**Deliverables of 1b:** SSO login working; `aws sts get-caller-identity --profile awsds-infra-sandbox`
returns the Sandbox account ID; `aws sso-admin list-instances --profile awsds-infra-identity` returns the
Identity Center instance, which is the proof that the delegation took effect; an attempt to write to an S3
bucket outside the organization is denied, which is the proof that the perimeter is real; and
`aws organizations list-aws-service-access-for-organization` (from Management) lists `ram.amazonaws.com`
while `aws lakeformation get-data-lake-settings --profile awsds-infra-data` reports a cross-account
version of 3 or above — together, the proof that Stage 5's shares have somewhere to land. Note what this
deliverable used to say: `aws ram get-resource-share-associations` from the Data Governance profile, which
returns an empty list both when sharing is enabled and when it is not.

**Blocking questions for the user:** the domain name to register (D15). Not needed to start the stage, but
needed before Stage 7.

**Risks:** Control Tower landing zone deployment takes ~60 minutes and is awkward to undo. Account e-mails
cannot be reused after an account is closed (a closed account holds its e-mail for 90 days) — which is
exactly why D11 keeps accounts in the persistent layer. Everything created in this stage is persistent;
nothing here is torn down between sessions.

**To verify while executing this stage**, because Control Tower's handling of Identity Center has changed
more than once and the plan should not assume: (i) that the delegation coexists with the landing zone
without raising drift; (ii) that the restriction in 1b step 4 is exactly as described — that assignments
targeting the Management account are the *only* thing the delegated administrator cannot manage; and
(iii) that the RCPs and SCPs in 1b step 5 do not conflict with the SCPs Control Tower manages itself, which
is the usual source of "the guardrail I wrote silently does nothing"; (iv) that enabling S3 Object
Lock on the Control Tower-managed Log Archive bucket (1b step 7) does not raise landing-zone drift; and
(v) that the Lake Formation cross-account version can be raised to 3+ in an account that has no lake in it
yet (1b step 9) — if it cannot, that setting moves into Stage 5 and the rest of the step stays here.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
