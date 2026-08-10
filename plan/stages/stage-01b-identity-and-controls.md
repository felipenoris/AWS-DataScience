# Stage 1b — Identity, policies, detective controls, org-wide enablement

| | |
|---|---|
| **Status** | **next** — not started |
| **Prerequisites** | Stage 1a complete, bar the deferred `Staging` vend. **Steps 3 and 5 must skip their `Staging` items** (`DataScientistStagingAccess`, `DeploymentManagerAccess` on Staging, the `awsds-infra-staging` profile) and pick them up when the account is vended |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D29](../decisions/D29-policy-canary.md), [D31](../decisions/D31-approver-read.md), [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | **The two organization-level halves of [INT-11](../integrations.md)** — org-wide RAM sharing and Lake Formation cross-account v3. The third (`AWSLakeFormationCrossAccountManager` on the grantor) is Stage 5 step 7, because the role does not exist yet (11.4). Also **constrains** [INT-12](../integrations.md), whose fallback step 7 forbids until the policy is amended |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

**Was "do not lose it", now settled: 1a step 2's budget alert thresholds (50/80/100%) and Cost Anomaly
Detection are deliberately skipped** (user, 2026-08-09). They are not pending work and are not to be picked
up in passing here. **The USD 50 budget therefore notifies nobody**: the ceiling is a number read from the
console, so the cost control of D12 is now the operator's own habit of looking — which is an intention, not
a control (Lesson 5). `plan/cost-model.md` names the exposure this leaves standing (a forgotten `egress/`
day at ~USD 4.08), and D12 carries the revision trigger.

---

Everything in 1b is fast, reversible and iterative — which is exactly why it is separated from the half
that is not. **Two exceptions, and knowing which is which is the whole of the risk budget:** step 7 is
neither fast nor freely reversible from inside a governed account and carries its own recovery procedure;
step 9's Object Lock retention, once set in compliance mode, is permanent.

## The stage at a glance

Eleven steps, and the order is a dependency chain rather than a listing. Read this table to plan a session;
read the step for how to do it.

| # | What | Identity | Why it is here and not later |
|---|---|---|---|
| 1 | Delegate Identity Center to the Identity account | CT Admin @ Management | Everything in 2-4 is done *from* Identity |
| 2 | Users and groups, beside Control Tower's | Infra user @ Identity | — |
| 3 | Permission sets and assignments | Infra user @ Identity | — |
| 4 | Confirm no persona reaches Management | Infra user @ Identity | Closes the assignment path that step 8 then watches |
| 5 | Local `aws configure sso` profiles | Infra user, laptop | **Every step below needs a member-account profile** |
| 6 | AZ name→ID mapping per account | Infra user, laptop | Stage 3 anchors subnets on the answer |
| 7 | Preventive policies (SCP/RCP/tag/declarative + managed controls) | mixed — see 7.4 | Prevention before detection (principle 9) |
| 8 | Access Analyzer + the group-membership alarm | CT Admin @ Management / Audit | The alarm is the only control over step 1's blast radius |
| 9 | Object Lock, compliance mode, on the log bucket | CT Admin @ Log Archive | Before there is anything worth hiding in the trail |
| 10 | Measure AWS Config, then decide | CT Admin @ Management + Audit | The landing zone's largest recurring line |
| 11 | Org-wide RAM sharing + LF cross-account v3 | CT Admin @ Management / Infra user @ Data | Stage 5 fails **silently** without it |

**Sessions.** Steps 1-6 are one sitting and are the bootstrap: nothing below them is reachable without a
profile. Step 7 wants its own sitting with the Management console already open. Steps 8-11 are independent
of each other. **Keep step 1 and step 8 in the same session** — step 1 widens the Identity account's blast
radius and step 8 is the only thing watching it.

## Who executes what

**Every manual step names the identity that performs it, not only what it does** (Lesson 17). **Two
identities do all eleven steps, through four sign-in paths** — and it is the *path* that is easy to get
wrong, which is how a step stalls on an `AccessDenied` that looks like a policy bug.

| Steps | Identity | Sign-in path |
|---|---|---|
| 1, 7 (policy-type enablement, org-root attachments, managed controls), 8.1 (delegations), 10 (Cost Explorer), 11.1 (RAM) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 7.4 step 1 (account-level BPA on Log Archive and Audit), 8.2 (creating the analyzer *in Audit*), 9 (Object Lock, *in Log Archive*), 10 (the Config aggregator lives in Audit) | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Log Archive** / **Audit** — the infrastructure user has *no* assignment in either (`ORGANIZATION.md`) |
| 2, 3, 4 | **Infrastructure user** | access portal → `AWSAdministratorAccess` on **Identity** (the direct Account Factory assignment from 1a step 4 — this is what bootstraps the whole stage) |
| 5, 6, 7.3 (the `Policy Canary` battery), 7.4 step 1 (BPA in the other member accounts), 11.2 (Lake Formation) | **Infrastructure user**, from the laptop | the `awsds-infra-*` and `awsds-policy-canary` profiles created in step 5 |

**Nothing in this stage is performed by root**, and nothing is performed by a project persona other than
the infrastructure user. The *directory* holds six identities after step 2 (five personas plus
`AWS Control Tower Admin`); only these two ever execute anything here.

## What this stage costs

Principle 6 wants the number per stage. 1b is close to free and is the stage that decides the largest
recurring line in the whole landing zone:

- **Free:** Identity Center, groups, permission sets, SCPs/RCPs/tag policies/declarative policies, Control
  Tower controls, IAM Access Analyzer **external-access** findings, S3 Object Lock (the lock itself; the
  storage it prevents from expiring is not), organization-wide RAM sharing.
- **Added here:** one CloudWatch alarm (USD 0.10/alarm-month) and, if step 8's alarm is built as a metric
  filter, one custom metric (USD 0.30/metric-month, metered only in the hours it publishes — same trick as
  1a step 5).
- **Decided here, not added:** AWS Config is the landing zone's main recurring cost — USD 0.003 per
  configuration item, USD 2.50-5.00/month at this account count (`PRICING.md` §2). Step 10 is about that
  number and, read honestly, is mostly about *measuring* it.
- **Deliberately not added:** GuardDuty, Security Hub and Macie — including their **delegation**, which
  step 8 now moves with them, because delegating them turns them on.

---

## To execute

1. **Register the Identity account as delegated administrator of IAM Identity Center (D10).**

   - **Do**, from the Management account:
     `aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com`.
   - **Verify:** `aws organizations list-delegated-administrators --service-principal sso.amazonaws.com`
     returns the Identity account, and — after step 5 —
     `aws sso-admin list-instances --profile awsds-infra-identity` returns the Identity Center instance.
     That second command is the one that proves the delegation *took effect* rather than merely being
     recorded.
   - **Reversible** (`deregister-delegated-administrator`), which is what makes this a cheap step to get
     wrong. Everything in steps 2, 3 and 4 is then done **from the Identity account**, not from Management.
   - **The blast radius this creates, which is easy to miss and is load-bearing.** An Identity Center
     delegated administrator can manage **groups assigned to the Management account** — including Control
     Tower's `AWSControlTowerAdmins`. So whoever administers the Identity account can grant themselves
     Management administrator by editing a group membership. That is the same blast radius
     `ORGANIZATION.md` already ascribes to this account; it is recorded here because D33's groups make it
     concrete rather than theoretical, and because **step 8's alarm is the only control over it**.
     **And it widens once more, one stage from here:** this delegation reaches Identity Center only. The
     SCPs, RCPs and tag policies written in step 7 are AWS Organizations objects and stay console-managed
     until **Stage 2 step 5.1 (INT-20)** adds a *second*, different delegation — a resource-based policy on
     the organization — after which the Identity account can also edit organization policy, Control Tower's
     guardrails included. Nothing to do about it here; the point is that step 8's alarm is the control above
     both delegations, so it is worth building well rather than quickly.
   - **Verify while executing (i):** that the delegation coexists with the landing zone without raising
     Control Tower drift. Control Tower's handling of Identity Center has changed more than once. Record
     the answer in `log/stage-01b-identity-and-controls.md`.

2. **Create this project's users and groups in IAM Identity Center — beside Control Tower's, never inside
   them.**

   - **Pre-flight:** `secrets/emails.md` must carry an address for every user created here. Verified on
     2026-08-08 — it does, including the **Dev Env Steward**, which was missing when this step was first
     written. An Identity Center user cannot be created without one, so re-check *before* starting rather
     than half-way through.
   - **Enumerate before creating anything. This step does not start from an empty directory, and it was
     written as if it did.** Enabling Control Tower in 1a step 3 created the Identity Center directory *and
     populated it*: Control Tower's own groups (`AWSAccountFactory`, `AWSControlTowerAdmins`, the auditor
     and per-account administrator groups), its own permission sets, and a first administrator. List what is
     there, then treat the two sets as separate — Control Tower owns its objects and may re-create them;
     this stage owns the five groups below.
   - **Create four users, not five (D32).** The infrastructure user already exists: Account Factory created
     it in 1a step 4 from the `SSOUserEmail` field, and it already holds a direct administrator assignment
     on every vended account. The only thing to do about it here is **put it in the `infrastructure`
     group**. Re-creating it under a second address gives one human two administrators, one of which nobody
     is watching.
   - **Create five groups:** `infrastructure`, `data-scientists`, `deployment-managers`,
     `governance-managers`, `dev-env-stewards`.
   - **One group per business unit is deferred, deliberately (D35).** `Sandbox` is one account per business
     unit and N is 1, so **create `data-scientists` and no per-unit group today**. What this step fixes now
     is that the *assignment list* in step 3 keeps the Sandbox row separable from the Development row, so
     the second unit is an addition (`data-scientists-<bu>` covering that unit's Sandbox alone) and not a
     refactor. [Stage 14](stage-14-sandbox-vending.md) owns the naming; do not invent it here.
   - **Enforce MFA** in Identity Center settings — required at every sign-in, and required at registration.
     This applies to `AWS Control Tower Admin` too, whose MFA (1a step 3) is a **standing control**, not a
     stopgap for a few days.
   - **Do not add a project persona to a Control Tower group, and do not repurpose one.** Those groups
     arrive with their assignments already made, so a membership edit is an organization-wide grant:
     `AWSControlTowerAdmins` is administrator on Management, Log Archive *and* Audit, and
     `AWSSecurityAuditPowerUsers` is `AWSPowerUserAccess` on every account. All but the first are empty
     today, and **empty is not the same as harmless**.
   - **The sixth identity is `AWS Control Tower Admin` (D33), and it stays (D34).** Created with the
     Management root's e-mail, it is not a *persona* of this plan — no project group, not the infrastructure
     user — but it holds one standing duty: it owns Control Tower administration, creating OUs and vending
     accounts from the console. **Do not disable it.** An earlier version of this step retired it here, on
     the premise that vending ends inside Stage 1a; the account list is not static, so what it needed was an
     owner and not an end date. Two consequences beyond the MFA above:
     - **Do not add it to any project group and do not give it a project permission set.** Its whole
       footprint stays the two Control Tower groups it arrived with.
     - **The narrow alternative stays documented and unused**, so nobody rediscovers it as a fault:
       `AWSAccountFactory` alone reaches the Account Factory product through the **Service Catalog**
       console, which is enough to *vend into an existing OU* but not to reach the **Control Tower
       console** — where OUs are created and accounts enrolled — which AWS documents as reachable only by
       `AWSControlTowerAdmins` members. Creating OUs is part of the job, which is what decided D34.
   - **Never put the same person in more than one approver group, or in one of them plus
     `data-scientists`** — or plus `infrastructure`, which is the instance that matters most and the one the
     tables hide. The approver groups were a single `managers` group until 2026-08-08 and have been split
     twice since, each time along a different axis: release (lifecycle), data access (ownership), runtime
     image (supply chain). The reason is cumulative and it is the whole point: one persona holding all of
     them means a single human can write a job that reads restricted data, approve its release, approve its
     access to that data, **and** approve the runtime image the job was written on — four acts, one
     signature. Nothing in AWS will warn you.

3. **Create the permission sets and make the assignments.**

   **3.1 — The seven sets, stated up front rather than discovered paragraph by paragraph.** An earlier
   version of this step named three in its first line and introduced four more further down, which is how a
   set gets missed.

   | Permission set | Group | Assigned on | Shape |
   |---|---|---|---|
   | `AdministratorAccess` | `infrastructure` | Sandbox, Development, Data Governance, Staging*, Production, Identity | The builder. The one named exception to "nothing gets `AdministratorAccess`" (`plan/conventions.md`) |
   | `DataScientistAccess` | `data-scientists` | Sandbox **and** Development (D21) | Studio use, scratch/derived read-write, Athena, ECR pull. **Not** `PowerUserAccess`, **not** `AmazonSageMakerFullAccess` |
   | `DataScientistStagingAccess` | `data-scientists` | Staging* (D20) | Read-only, no write of any kind, not even a drop-box |
   | `DataScientistProdAccess` | `data-scientists` | Production (D18) | Data plane read, no compute, no control plane |
   | `DeploymentManagerAccess` | `deployment-managers` | Sandbox, Development, Staging*, Production (D31) | Diagnosis, not reading. **Nothing on Data Governance** |
   | `GovernanceManagerAccess` | `governance-managers` | **Data Governance only** | The catalog, never the rows |
   | `DevEnvStewardAccess` | `dev-env-stewards` | Production + read-only on Sandbox and Development | The artifact, never the data |

   \* **Skip every `Staging` cell until the account is vended** (the prerequisites row). Nothing before
   Stage 8 needs it.

   Plus one account reached with no group behind it: **`Policy Canary` (D29)**, which since D32 is a
   **confirmation rather than a task**. Vending it in 1a step 4 with the infrastructure user's
   `SSOUserEmail` already left a **direct assignment of Control Tower's `AWSAdministratorAccess`** there —
   *that* set, not this project's, and saying so is 3.2's rule being applied rather than restated. So the
   task here is to **confirm it, not to create anything**: `aws sso-admin list-account-assignments` for the
   Policy Canary account must return the infrastructure user with an administrator set. A direct assignment
   is also the right *shape* there — the account is deliberately outside the Terraform-managed set, has no
   `awsds-infra-*` profile, and is reached only through `awsds-policy-canary`. It must be an administrator
   or step 7 measures the wrong thing: an SCP is a *ceiling*, so a deny that a restricted principal could
   not have exercised anyway proves nothing about it.

   **3.2 — Settle the name collision before creating anything, because its failure mode is silent.**
   Control Tower already created a permission set called **`AWSAdministratorAccess`**; this step creates one
   called **`AdministratorAccess`** — two objects four characters apart, both granting administrator, one
   owned by Control Tower and one by this project. An assignment made against the wrong one still works, so
   nothing reports it.

   - **The name is `AdministratorAccess`**, and the disambiguation rule is the one `ORGANIZATION.md` already
     states: *anywhere this repository says "the administrator permission set" without naming Control Tower,
     it means this project's*. That is the choice, not an option — an earlier draft left "either rename it
     or write the rule down" open at execution time, and an unanswered naming question gets answered by
     whoever is at the keyboard (Lesson 16).
   - **If you would rather rename it** (`InfrastructureAccess` is the honest name — it is the
     `infrastructure` group's set), that is a decision that has to be made *here* and propagated in the same
     session to `ORGANIZATION.md`, `plan/conventions.md` and D32. Record which way it went.
   - **Never edit or reuse Control Tower's set.** It is theirs, and a landing-zone update may reset it.

   **3.3 — One permission set object is one policy, however many accounts it is assigned to.** This is the
   mechanical fact behind two rows of the table and is worth stating once: `DataScientistAccess` is one set
   assigned on Sandbox *and* Development (the two accounts are policy-identical at this level — that is what
   putting them in one OU asserts, and what differs between them is the work, not the permission shape), and
   `DevEnvStewardAccess` is one set assigned on Production, Sandbox and Development. So **scope by resource
   ARN and by condition, never by "this account will not have that resource"**: a grant that is harmless in
   one account because nothing matches it is a grant that appears the day something does.

   **3.4 — `DataScientistAccess` does not start as `PowerUserAccess`.** An earlier version of this plan gave
   it `PowerUserAccess` "until Stage 6", which contradicts `ORGANIZATION.md` ("no permissions to perform
   infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let the data
   scientist create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the whole
   design — for five stages. `AmazonSageMakerFullAccess` is *not* a safe starting point either: it grants
   `s3:*` on any bucket with "sagemaker" in the name plus a broad `iam:PassRole`. It starts as: SageMaker
   Studio use, read/write on the account's scratch and derived prefixes, Athena, ECR pull, and nothing else,
   with a **permissions boundary** and `PassRole` scoped per the IAM rules in `plan/conventions.md` §6.

   **3.5 — The three sets whose *denials* are the point of them.** All three are approvers, and an approver
   who can already read everything is not exercising a control when they approve.

   - **`DeploymentManagerAccess` (D31), which used to be the AWS-managed `ReadOnlyAccess` and should not
     have been.** `ReadOnlyAccess` on the lifecycle accounts reaches the D19 derived zones — where the
     output of a query over `restricted` data lives and, by D19's own classification rule, *is*
     `restricted` — and reaches `athena:GetQueryResults`, which returns other people's query output. It is
     replaced by a set in the same shape as `DataScientistProdAccess`: CloudWatch Logs read including Logs
     Insights (diagnosing a failed promotion is the job), SageMaker job/pipeline/Model Registry **status**,
     Glue catalog metadata, ECR image metadata and scan findings, Step Functions and EventBridge Scheduler
     execution status, and `s3:GetObject` on **enumerated** prefixes only — build artifacts and test
     reports, never a bucket wildcard.
     **Denied explicitly rather than by omission:** `athena:*` (both starting a query and reading someone
     else's results), `kms:Decrypt`, `secretsmanager:GetSecretValue`, `ssm:GetParameter*`, the Terraform
     state buckets, and the control plane in full.
     *One precision worth carrying, because it is why the old arrangement looked harmless:*
     `ReadOnlyAccess` grants no `athena:StartQueryExecution` and no `kms:Decrypt`, so it could never
     *originate* a read of the lake and could not decrypt an SSE-KMS object at all. The exposure was being
     prevented by encryption rather than by design — which stops being true the first time a bucket is
     created without a CMK.
     **Note also what this set is *not*:** an earlier draft created a `DeployApprover` permission set and it
     was dropped, because the deploy approval gate lives in GitLab (Stage 8), driven by GitLab group
     membership, and consumes no AWS permission. That is still true. This set exists for the other half of
     the job, which is **diagnosis** — reading why a promotion failed before deciding whether to release it.
   - **`GovernanceManagerAccess`.** The governance manager approves who may read data, so their own reach
     must stop at the *catalog*, not the rows: Glue catalog metadata read, Lake Formation LF-Tag and
     permission administration, DataZone domain ownership, Macie findings read — and **no `s3:GetObject` on
     lake prefixes and no Athena workgroup**.
   - **`DevEnvStewardAccess`.** The steward approves the `dev-env` image — the runtime every notebook and
     every project app runs on — and the approval itself happens in GitLab, consuming no AWS permission.
     What the set is for is judging the artifact: ECR image metadata and **enhanced-scanning findings**, the
     build pipeline's CloudWatch Logs, and read access to the `aws_sagemaker_image` / `app_image_config`
     resources in Sandbox and Development so they can confirm what is actually registered.
     **Denied explicitly, because these are what would turn the gate into theatre:** `ecr:PutImage`,
     `ecr:BatchDeleteImage`, `sagemaker:CreateImage`, `sagemaker:CreateImageVersion` and
     `sagemaker:UpdateAppImageConfig` — the pipeline holds those and runs only after the approval, so a
     steward who also holds them can ship an image nobody reviewed, including their own. Also denied:
     `athena:*`, `kms:Decrypt`, and `s3:GetObject` on lake or derived prefixes. Approving a *runtime* never
     requires reading data.

   **3.6 — The two remaining data scientist sets (D18, D20).**

   - **`DataScientistProdAccess`** is a different shape, not a weaker copy: **data plane read, no compute,
     no control plane.** CloudWatch Logs read, Glue catalog metadata read, SageMaker job/pipeline/Model
     Registry *status* read, `s3:GetObject` on named application-output prefixes, and Athena on the
     dedicated workgroup from Stage 9. It denies, explicitly rather than by omission: the control plane,
     `sagemaker:Create*Job`, `sagemaker:CreatePresignedDomainUrl`, `glue:StartJobRun` and
     `lakeformation:GrantPermissions`. GitLab and ECR access (D14) folds into this set rather than living as
     a separate grant. *(The ingestion drop-box moved with the lake to Data Governance, D22 — it is granted
     by bucket policy to the Interactive-OU roles, not by this set.)*
   - **`DataScientistStagingAccess`** — read-only, with no write of any kind, not even a drop-box. Staging
     exists to be written by the pipeline and read by a human working out why the pipeline failed; a staging
     environment a person can write to stops being evidence of what the pipeline actually does. Same denies
     as the Production set, minus every write grant.

   **3.7 — What nobody gets, which is as much of the design as what they do.**

   - **`data-scientists` has no assignment of any kind on Data Governance** (D18/D22). The lake is read from
     Sandbox and Development through the Lake Formation share.
   - **`deployment-managers` has nothing on Data Governance** — a release approver has no business in the
     account that grants data access. `governance-managers` is the mirror image: the one account the
     deployment manager cannot enter is the only one they can.
   - **`dev-env-stewards` has nothing on Staging, Data Governance, Identity, Audit, Log Archive or Policy
     Canary** — the narrowest of the three, because the artifact it judges is a container image and not an
     environment.
   - **No project persona has anything on Identity, Audit, Log Archive or Policy Canary** except the
     infrastructure user on Identity. The last one matters less than it looks, since the account is empty,
     but an account whose whole purpose is to have broken permissions is not somewhere a second persona
     should be able to sign in and draw conclusions.
   - **Control Tower's own permission sets stay untouched** — editing them causes landing-zone drift.

   **3.8 — The direct assignments Account Factory left behind, and the ordering that is the whole of it
   (D32).** Every vended account carries a *direct* assignment of Control Tower's administrator set to the
   infrastructure user, created in 1a step 4 and sitting outside the group model built here.

   - **Remove none of them until the group path is proven end to end** — `infrastructure` →
     `AdministratorAccess` → an actual `aws sts get-caller-identity` under each profile in step 5. Removing
     them first is the cheapest way to lock the only administrator out of an account whose sole remaining
     recovery path is the Management root (D16; D30 reverted). **So the removal happens after step 5, not
     inside step 3** — it is listed here because this is where the assignments are described.
   - **`Policy Canary` is the exception and it is permanent.** Its direct assignment is not a leftover to be
     cleaned up: there is no group and no `awsds-infra-*` profile behind it (3.1), so removing it removes the
     only way into the account, and with it D29's whole battery. Whatever the answer to (vi) below, this one
     stays.
   - **The Identity account's direct assignment is the bootstrap for this entire stage** — it is what lets
     steps 2, 3 and 4 happen at all. It is the last one to touch, if any of them is touched.
   - **Verify while executing (vi):** whether removing one sticks, or Control Tower re-creates it on a
     landing-zone update, an account update or a re-enrollment. If it returns, the honest outcome is to
     record the direct assignment as a **permanent property of Account Factory-vended accounts** rather
     than to keep deleting something that keeps coming back. D32 is amended either way.

   **3.9 — Why this is by hand.** Terraform cannot run before SSO login works. Stage 2 moves all of it into
   `terraform-live/identity/sso/` and imports it.

4. **No project persona holds an assignment on the Management account — the infrastructure user included.**

   - **This step used to create one**, and it contradicted the reason `AWS Control Tower Admin` is kept
     standing at all: the Management-account work is *its* job, and what D34 buys is precisely that the
     infrastructure user gains no standing reach there. Principle 1 says the same from the other side —
     Management is bootstrap-only and console-only, Terraform never runs against it, so there is nothing for
     an `awsds-infra-*` profile to do. Step 3's assignment list already omits it; this step now says so
     deliberately rather than by omission, which is the difference between a decision and an oversight.
   - **Keep the mechanical fact the old step carried, because it is true and it bites at step 8:** the
     delegated administrator **cannot manage assignments targeting the Management account** — those can only
     be created from Management itself. That is a constraint on *creating an assignment*, and it is **not** a
     constraint on group membership: `AWSControlTowerAdmins` already carries `AWSAdministratorAccess` on
     Management, created by the landing zone, and step 1 records that the delegated administrator can edit
     who is in it. **So the preventive path into Management is closed and the membership path is not** —
     which is why step 8's alarm is the control rather than a nicety.
   - **Verify while executing (ii):** that the restriction is exactly as described — that assignments
     targeting the Management account are the *only* thing the delegated administrator cannot manage.

5. **Configure the local SSO profiles now, not at the end of the stage.**

   - **Do:** `aws configure sso` for `awsds-infra-sandbox`, `awsds-infra-dev`, `awsds-infra-prod`,
     `awsds-infra-data` and `awsds-infra-identity` — plus one more that is deliberately named differently,
     **`awsds-policy-canary`** (D29). `awsds-infra-staging` waits for the vend.
   - **Why the canary profile is not an `awsds-infra-*`:** `Policy Canary` is not a Terraform-managed
     account and nothing is ever applied into it. The profile exists only to run step 7's test battery, and
     the naming keeps that visible in shell history.
   - **Verify:** `aws sts get-caller-identity --profile <each>` returns the expected account ID. This is the
     first real proof that steps 1-4 worked, and it is the precondition step 3.8 names before any direct
     assignment is removed.
   - **This used to be step 10 and that was an ordering bug.** Every step below this one does CLI or console
     work *inside a member account* — restricting the Config recorder, enabling Object Lock on the Log
     Archive bucket, raising the Lake Formation cross-account version in Data Governance, reading AZ IDs per
     account — and none of it is reachable without a profile.

6. **Check the AZ name-to-ID mapping.**

   - **Do**, under each of `awsds-infra-sandbox`, `awsds-infra-dev` and `awsds-infra-prod`:
     `aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'`.
   - **Why it has a bill attached.** AWS maps AZ names to physical datacenters independently per account, so
     `data.aws_availability_zones` indexed by position can place "the same" AZ in different datacenters.
     D14 and D21 make this concrete: both peerings into Production are free within an AZ and USD 0.01/GB
     each way across AZs, and the VPN, SageMaker and GitLab talk across them constantly.
   - **Staging and every future Sandbox get the same check when they are vended** — the *cost* argument does
     not apply to Staging (D20 leaves it unpeered), but Stage 3 anchors its subnets the same way, so the
     mapping has to be on record before it writes one.
   - **Record the full table in `log/stage-01b-identity-and-controls.md`.** If the mappings differ, Stage 3
     anchors subnets on `zone_ids` (`usw2-az1`, passed per environment in `.tfvars`) instead of on list
     position, and `plan/architecture.md` §4.1 is updated. See `plan/open-questions.md` item 3.

7. **Preventive policies.** The one step in 1b that is neither fast nor freely reversible from inside a
   governed account. Read all of 7.1 before attaching anything.

   **7.1 — What makes this step different, and the two rules that survive from D30.**

   - **No `Deny` written below carries a blanket exemption for any principal (D30, reverted).** A standing
     role exempt from every custom deny was proposed and removed; the only carve-outs in this design are
     per-function and per-statement — the catalog-maintenance role against the `Data` OU's Glue deny (D27),
     the `datazone:*` control plane (D26), and a deploy role against a specific deny where automation would
     otherwise stall.
   - **The practical consequence, and it is why 7.3's battery is not optional: a policy attached here has no
     in-account repair.** A mistake is undone by detaching the policy from the Management account, which is
     exempt from SCPs by design (D16) — so the battery *is* the control, and having the Management console
     already open is a precondition rather than a precaution.
   - **A condition that has to appear in several policies is generated, not typed** — which is why these
     policies live in `terraform-live/identity/org-policies/` from Stage 2 rather than in the console
     (Lesson 14).
   - **Any ARN condition uses an enumerated list, never a wildcard account.** `arn:aws:iam::*:role/x` means
     "anyone who can create a role named `x`, anywhere".
   - **There is a size budget, and it is small enough to hit.** AWS Organizations caps how many policies
     attach to one node and how large each is — **10 SCPs per node and 10 240 characters** since the May 2026
     increase, but **RCPs are still 5 per node and 5 120 characters**, and Control Tower's own guardrails
     consume part of the SCP allowance at every OU it registers. The organization root here is asked to carry
     the 7.5 set *and* the tag-forcing SCP of 7.8, and 7.8's RCP covers five services in one document.
     **Count before writing, and prefer one well-`Sid`-ed policy per node to several thin ones** — a policy
     that will not attach is discovered at the end of the work rather than at the start.
   - **A third rule arrives with D34, and it is the one that survives an account being added later.** OUs
     and accounts are created from the console, outside every Terraform state — which cannot cause drift,
     because nothing here declares them, but *can* leave a new OU with no policy attached and a new account
     outside every enumerated condition, with `terraform plan` reporting "No changes" either way. So when
     these policies move into `terraform-live/identity/org-policies/` at Stage 2: **the floor is discovered
     and the
     grants are enumerated** — attachments and org-wide sets driven by `for_each` over the Organizations
     data sources, permission set assignments written out one by one.

   **7.2 — Preconditions, in this order. Two of them are the reason a first attempt fails.**

   1. **Enable the policy types that are not already on.** Control Tower enables `SERVICE_CONTROL_POLICY`;
      **`RESOURCE_CONTROL_POLICY`, `TAG_POLICY` and `DECLARATIVE_POLICY_EC2` are not enabled by default**
      and cannot be attached until they are. RCPs additionally require an organization with **all features**
      enabled — Control Tower requires that too, so it is expected to be on; confirm it rather than assume
      it. Nothing below works without this and the error does not say so clearly.

      ```bash
      aws organizations describe-organization --query 'Organization.FeatureSet'   # must be ALL
      aws organizations list-roots --query 'Roots[0].[Id,PolicyTypes]'            # note the root id r-xxxx
      aws organizations enable-policy-type --root-id <r-xxxx> --policy-type RESOURCE_CONTROL_POLICY
      aws organizations enable-policy-type --root-id <r-xxxx> --policy-type TAG_POLICY
      aws organizations enable-policy-type --root-id <r-xxxx> --policy-type DECLARATIVE_POLICY_EC2
      ```

      Re-run `list-roots` afterwards: each type must read `ENABLED`, not `PENDING_ENABLE`.
   2. **Confirm the `Policy Canary` account is reachable** under `awsds-policy-canary` and holds an
      administrator (step 3.1).
   3. **Write the detach command down, and reach the Management console *now*, not in theory.** This is the
      whole recovery path, not a backup to one. The command is
      `aws organizations detach-policy --policy-id <p-xxxx> --target-id <root-or-ou-id>`, run from
      Management — have the policy id in the same note, because it is not guessable at 23:00.
   4. **Enable account-level S3 Block Public Access before the SCP that denies changing it** — see 7.4,
      where the ordering is stated as an instruction rather than implied.

   **7.3 — The battery, run against `Policy Canary` before anything reaches a real OU (D29).** An SCP
   mistake is the fastest way to lock yourself out of your own organization — recoverable, because the
   Management account is exempt from SCPs and 1a step 5's break-glass path exists, but recoverable is not
   the same as cheap. Since D30 was reverted this is the only thing standing between a mistake and that
   recovery. It is a procedure, not a gesture:

   - **One policy at a time.** Attach, test, record, move on. A batch that breaks tells you that something
     in the batch is wrong, which is the least useful form of that information.
   - **From an administrator principal.** An SCP is a ceiling; a deny exercised by a principal that lacked
     the permission anyway proves nothing. That is what step 3.1's assignment on this account is for.
   - **Test in both directions, because the two failure modes are opposites.**
     - *Too tight* — the calls that must still **succeed**: `sts:GetCallerIdentity`,
       `s3:ListAllMyBuckets` (`aws s3 ls` — **not** `s3:ListBucket`, which is a different action about the
       objects *inside* one bucket, and naming the wrong one is how a battery produces a false pass),
       `ec2:DescribeVpcs` in `us-west-2`, and — once the region restriction is on — `iam:ListRoles`,
       `budgets:DescribeBudgets` and `ce:GetCostAndUsage`, all of which answer in `us-east-1` and must keep
       working.
     - *Too loose* — the calls that must now **fail**: a `PutObject` to a bucket outside the organization,
       and an `iam:CreateUser`.
     - **The region test belongs to 7.7, not to this battery, and the sequencing matters.** The
       discriminating check is `ec2:RunInstances --dry-run` in **`us-east-1` specifically** — under the
       correct construction `us-east-1` is *not* an allowed region and the call must fail, while under the
       loose construction this plan used to describe (adding `us-east-1` to the allowed list) it would
       succeed and look like a pass. But no policy written in 7.5 or 7.6 implements the region restriction:
       it comes from a **Control Tower managed control**, enabled at 7.4 step 4. So run this pair —
       `us-east-1` must return `UnauthorizedOperation`, `us-west-2` must return `DryRunOperation` — from
       `awsds-policy-canary` **after** 7.7, as the check that the managed control took effect.
   - **Use `--dry-run` for the "must fail" half wherever the API supports it, because a passing test that is
     not dry-run is a resource you now own.** `ec2:RunInstances --dry-run` returns `DryRunOperation` when
     the call *would* have been allowed and `UnauthorizedOperation` when it is denied — two distinguishable
     outcomes and no instance, in an account whose whole point is to stay empty. Where there is no dry-run
     (`iam:CreateUser`), plan the cleanup before the call, not after it.
   - **Read the denial, do not just observe it (Lesson 13).** `AccessDenied` from an SCP and `AccessDenied`
     from a missing grant or someone else's bucket policy look identical at the CLI. The
     discriminating evidence is the CloudTrail record's `errorMessage`, which names an explicit deny in a
     service control policy. This matters most for the cross-organization `PutObject` test, where a bucket
     you do not own would have refused you anyway.
   - **Test each per-function carve-out the same way, in both directions.** For D27's catalog-maintenance
     role and D26's `datazone:*` control plane: confirm the exempt principal *can* do the thing, and that a
     principal outside the carve-out *cannot*. A carve-out that silently fails to match is either a control
     you do not have or a job that will not run, and neither announces itself.
   - **Then move the attachment to its real target** — the OU named in 7.4/7.5, or the organization root for
     the org-wide set. The root-level policies can be exercised here exactly as they will behave in
     production, because `Policy Test` sits under the root and inherits from it like every other OU.
     **And that is also the canary's one permanent limitation, worth knowing before you rely on it a second
     time:** once the root set is attached, `Policy Canary` inherits it forever, so every later candidate is
     tested *on top of* the existing ceiling rather than in isolation. That is the right thing for
     regression — it is the real evaluation order — and the wrong thing for answering "does *this policy*
     deny X", because denies only ever compose: a call that fails may be failing on the root set. The half
     that stays clean is the *must still succeed* half, which composition can only make stricter — so a
     success there is still evidence about the candidate. For the deny half, read the CloudTrail
     `errorMessage`, which names the policy id.
   - **Record each outcome.** A policy that passed both halves is a control; one that was only attached is a
     hope.
   - **Two verifications ride along** (`plan/open-questions.md` item 10): whether the **IAM Policy
     Simulator** evaluates SCPs for member-account principals — if it does, it is a cheaper first pass than
     any OU — and whether the OU has to be **registered with Control Tower** for the test to run against the
     real control baseline (D29 assumes it; 1a step 4 instructs it).
   - **Verify while executing (iii):** that the RCPs and SCPs written here do not conflict with the SCPs
     Control Tower manages itself, which is the usual source of "the guardrail I wrote silently does
     nothing".

   **7.4 — The order of attachment. This is an instruction, not a listing order.** Two pairs interlock, and
   following the old "attach to the OUs, in this order" literally breaks one of them.

   1. **Account-level S3 Block Public Access in every account, enumerated rather than implied.** The
      module-level block from Stage 2 only covers buckets the module creates; the account-level setting is
      the blanket that also covers the bucket someone creates outside it — so "every member account" has to
      be a list, or the one account nobody had a profile for is the one that keeps the hole.
      - `AWS Control Tower Admin`, from the console: **Management**, **Log Archive**, **Audit**.
      - `awsds-infra-sandbox`, `-dev`, `-prod`, `-data`, `-identity` (`aws s3control put-public-access-block`).
      - **`awsds-policy-canary`** — the easiest one to forget, because the account is supposed to stay empty
        and has no `awsds-infra-*` profile. It is still an account with an S3 API.
      - **`Staging` gets it at the vend**, with everything else deferred there.
      - **Management is on the list even though the deny below never reaches it** (SCPs do not apply to the
        management account, D16). The ordering interlock in step 2 is therefore about the *members*; doing
        Management first is simply doing it in the same sitting.
   2. **Then** the organization-root SCP set (7.5), which includes the deny on
      `s3:PutAccountPublicAccessBlock`. **In the other order the deny blocks the very call that enables the
      setting it protects**, in every account at once, and the repair is a detach from Management.
   3. **Then** the per-OU sets: `Workloads`, `Data`, `Identity`, and `Interactive` if 7.6 decides it gets
      one.
   4. **Then** the managed Control Tower controls (7.7) — region deny and the two root-user controls.
   5. **Then** RCPs, tag policies and declarative policies (7.8).

   The same interlock appears once more inside 7.7: the region-deny exemption list has to contain
   `s3:PutAccountPublicAccessBlock` and `s3:ListAllMyBuckets`, which are account-level calls evaluated
   outside any region.

   **7.5 — The organization-root SCP set** (hand-written; moves to `terraform-live/identity/org-policies/`
   at Stage 2).

   - **Deny `organizations:LeaveOrganization` — not hygiene: a real principal can call it.** Control Tower's
     `AWSControlTowerAdmins` group carries `AWSOrganizationsFullAccess` on every member account (D33), and
     this is one of the few Organizations calls a *member* account can make. One call drops every SCP and
     every Control Tower control for that account.
   - **Deny disabling CloudTrail, Config and GuardDuty.**
   - **Deny writes to S3 resources outside this organization** (`aws:ResourceOrgID`) — the trusted-resources
     axis of `plan/architecture.md` §4.2, and the most direct exfiltration route a notebook has. **Writes
     only, deliberately:** a read-side deny of the same shape breaks `docker pull`, package installs and
     every other legitimate read of an AWS-owned bucket.
     **Write the condition the way 7.8 writes the RCP's, because it is the same trap and this plan only
     spelled it out on one of the two sides:**
     `"StringNotEqualsIfExists": {"aws:ResourceOrgID": "<o-xxxx>"}` beside
     `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}`. A plain `StringNotEquals` evaluates **true
     when the key is absent**, so every call that does not populate `aws:ResourceOrgID` is denied — and the
     `BoolIfExists` pair is what stops the deny reaching calls an AWS service makes on your behalf. Both
     halves are invisible in the JSON review and obvious in the canary, which is what 7.3 is for.
   - **Deny `iam:CreateUser` and `iam:CreateAccessKey`.** Principle 2 ("no IAM Users") is otherwise a
     convention with no enforcement. Break-glass (D16) is unaffected: the Management account is exempt from
     SCPs.
   - **Deny `s3:PutAccountPublicAccessBlock`**, protecting the setting enabled in 7.4 step 1.
   - **Deny `datazone:CreateDomain`, with a carve-out for the `Data` OU** (added 2026-08-08). D26 says there
     is one unified domain and it is registered in Data Governance; until now that was a sentence rather
     than a control, and a second domain anywhere would quietly reintroduce the thing the account split
     exists to prevent — a second interactive entry point with its own blueprints and its own project roles.
     Three precisions:
     - **The carve-out is the OU, not a role:** `aws:PrincipalOrgPaths` admitting the `Data` OU and nothing
       else. SCPs are ceilings and an explicit `Deny` wins wherever it appears, so the exception is a
       **condition on the root deny**, never an `Allow` in the `Data` OU's own set.
       **Two mechanics decide whether it works at all, and both fail in the direction of a deny that never
       lifts:**
       - `aws:PrincipalOrgPaths` is a **multi-valued** key, so the deny's condition is
         `"ForAllValues:StringNotLike"`, never a bare `"StringNotLike"` — a set operator is required and a
         missing one is a policy that does not evaluate the way it reads.
       - The value is the **full path with a trailing slash**: `<o-xxxx>/r-xxxx/<ou-id-of-Data>/`. `Data`
         sits directly under the root, so that is the whole path; append `*` instead of the final `/` only
         if the carve-out is ever meant to reach nested OUs.

       Get either wrong and Data Governance cannot create the domain the whole of Stage 6 depends on, with
       an `AccessDenied` that names the root policy and not the condition. Exercise **both** directions in
       7.3 — from an administrator in `Policy Canary` (must fail) and, once the OU ids are known, confirm
       the path string against `aws organizations list-parents` rather than against a screenshot.
     - **It must be `CreateDomain` alone and not `datazone:*` at the root.** Sandbox and Development need
       `datazone:PutEnvironmentBlueprintConfiguration` for the blueprints to provision into them at all, so
       a root-wide namespace deny would break Stage 6 rather than protect it. The `Workloads` OU tightens to
       the full namespace on top of this (7.6).
     - **Read this against INT-12 before attaching it, because the two collide.** INT-12's stated fallback,
       if the domain's account associations do not work, is *one V2 domain per Interactive account* — which
       this deny makes impossible. That is acceptable only because it is now explicit: if Stage 6 has to
       fall back, this policy is amended first (carve the `Interactive` OU in, or drop the root deny to the
       `Workloads` OU only), deliberately and with the reason recorded. A fallback silently forbidden by a
       policy written five stages earlier is the worst version of this.

   **7.6 — The per-OU sets.** One tier per OU policy set (D23), on top of the root set above.

   - **`Workloads` OU** (D20) — deny `sagemaker:CreateDomain`, `sagemaker:CreateUserProfile` and
     `sagemaker:CreatePresignedDomainUrl`. This is what turns D17 from an intention into a control: "no
     Studio outside the Interactive OU" cannot be undone by anyone with a console and a good reason.
     **And deny `datazone:*` outright, which the SageMaker list does not cover (corrected 2026-08-08).**
     Those three actions were the whole control when the interactive surface was the classic Studio; since
     D26 it is a DataZone V2 domain, and D26's "Staging and Production are never associated" had no policy
     line behind it. Three things were reachable and are now not:
     - **A DataZone domain created locally** in Staging or Production.
     - **The account associating itself to a domain and configuring a blueprint**
       (`datazone:PutEnvironmentBlueprintConfiguration`), which mints provisioning and manage-access roles
       with broad permissions in the account — even where the provisioning then fails.
     - **The blueprints that are not the ML one.** Tooling and Lakehouse provision a project bucket, a Glue
       database and an Athena workgroup; none of that passes through `sagemaker:*`, so none of it was
       denied.

     **Why the whole namespace rather than a list of actions.** This plan has already paid for an enumerated
     deny once: the `Data` OU list below omitted `glue:CreateJob` and left the whole ingestion runnable in
     the wrong account until D25 caught it. DataZone gains APIs, and a list written today goes stale in the
     direction of the false negative. Nothing legitimate in this design calls DataZone from a deployment
     target: what crosses the gate is the D28 artifact set, and Production's governed write resolves through
     Lake Formation, not through DataZone. **Revision trigger:** the first time Production needs to publish
     a data product of its own.
     **What is *not* the gate, and it is worth knowing before debugging this.** The account association is
     not held back by anyone declining a RAM invitation: `ram:EnableSharingWithAwsOrganization` (step 11)
     makes shares inside the organization arrive without an invitation to accept. The gate is the target
     account being unable to configure a blueprint.
     **To verify while attaching, because the product surface moves:** confirm in the `Policy Canary`
     battery which namespace each Unified Studio action actually evaluates under — some of the portal's
     surface is `datazone:*` and some is `sagemaker:*` — and widen the deny rather than assuming the prefix
     covers it.

   - **`Data` OU** (D22) — deny compute creation outright (`ec2:RunInstances`, `sagemaker:Create*`,
     `glue:CreateDevEndpoint`, **`glue:CreateJob` and `glue:StartJobRun`** — added by D25, because the
     original list left a Glue ETL job as a perfectly legal way to run the whole ingestion in the account
     whose entire policy set says nothing runs there — and ECS/Lambda creation), deny `s3:DeleteBucket` and
     `lakeformation:DeregisterResource`. The lake account's SCP is about what can never happen there,
     because nothing is supposed to *run* there at all. Two named carve-outs, and they are per-statement:
     `datazone:*` as a governance control plane (D26), and `glue:CreateCrawler`/`StartCrawler` plus the
     table-optimizer and column-statistics actions **only when the principal is the catalog-maintenance
     role** (D27).
     **The `sagemaker:Create*` line is the one to re-read before attaching, because this list predates D26.**
     It was written when the only thing that could run in Data Governance was a job somebody started by
     hand; since D26 the account also holds the **unified domain**, whose creation and whose Tooling
     blueprint provision resources into this very account. If any part of that surface evaluates under
     `sagemaker:*` rather than `datazone:*` — which is exactly what verification (viii) asks — then a
     `datazone:*`-only carve-out leaves the `Data` OU denying the creation of the domain the whole of
     Stage 6 depends on, five stages before anyone tries it. **So answer (viii) against the `Data` OU as
     well as against `Workloads`**, and if the answer is mixed, widen this carve-out to the specific
     `sagemaker:*` actions the domain needs rather than dropping the deny. The distinction the deny is
     protecting is *user compute*, not *the control plane that happens to share a prefix with it*.

   - **`Interactive` OU** (D21) — **read this before writing anything here, because the phrase the plan used
     to carry did not describe a policy.** "Human infrastructure changes denied" appeared across six files as
     a property of this OU's SCP set, and no SCP implements it. What actually stops the data scientist from
     creating a VPC is `DataScientistAccess` and its permissions boundary — an **identity** policy,
     enumerated by hand, which is exactly the sort of thing an SCP is supposed to back up rather than the
     thing an SCP *is* (Lesson 5). Corrected across those files on 2026-08-09. The honest statement of what
     this OU carries today is **nothing of its own**: interactive compute is allowed here because, unlike
     `Workloads` and `Data`, nothing denies it, and the organization-root set is the whole ceiling.
     - **Why the literal SCP was not simply written.** A deny of "infrastructure changes" in these accounts
       would have to exempt the identity that *builds* the infrastructure in them — Terraform applies the
       VPC, the buckets, the roles and the keys here under `AdministratorAccess`. A standing exemption for
       the builder from every infrastructure deny is the exact shape D30 proposed and had reverted. A second
       exemption would follow it: D26's blueprints provision project buckets, execution roles and apps into
       these accounts under DataZone's own provisioning roles — principals that do not exist until Stage 6
       (Lesson 17), and whose absence from a carve-out surfaces as a failed project creation rather than as
       a policy error.
     - **So there is a choice to make while attaching, rather than a sentence to inherit.** Either leave
       this OU with no set of its own — and say so in one place instead of implying a control — or give it
       denies that are *interactive-specific and need no exemption at all*.
     - **The candidate worth pricing** is the ungoverned interactive surface:
       **`sagemaker:CreateNotebookInstance` and `sagemaker:CreatePresignedNotebookInstanceUrl`**. Nothing in
       this design uses a classic notebook instance; it bypasses the VPC-only app configuration and the
       `dev-env` image gate in one step; and denying it binds the builder too, which is what would make it a
       control rather than a carve-out. It is named here as a candidate and **deliberately not adopted** —
       adopting it is a decision, and it belongs to whoever runs this step against the battery. **Record
       which way it went.**
     - **If this OU does gain a set, attach it here and not to the nested `Sandboxes` OU** (D23, D35).
       `Sandboxes` groups the accounts that multiply and carries no set of its own; inheritance is what makes
       a unit vended next year governed on arrival, and a set attached twice is a set that will diverge in
       one of the two places. **Until it gains one, that instruction is about the root set** — which reaches
       a newly vended Sandbox whatever the nesting, so "governed on arrival" is true today for a reason that
       has nothing to do with where the attachment goes.
     - The differences between Sandbox and Development are differences of content, not of policy, which is
       why they share the OU.

   - **`Identity` OU** (D10, D23 as revised 2026-08-09) — **the tier this plan did not have, because the
     account was supposed to be in `Security`.** It is not: Control Tower refused the vend into a
     foundational OU, so the account sits in a sibling OU created from the console — and **a console-created
     OU carries no policy set until code attaches one** (D34). Two things, in this order:
     - **Establish the baseline before writing anything.** List the Control Tower controls enabled on
       `Security` and on `Identity` and diff them; whatever `Security` got by being foundational and
       `Identity` did not is the gap. Enable the equivalent elective controls on `Identity` where they
       exist. **Record the diff in `log/stage-01b-identity-and-controls.md`** — "it used to inherit that" is
       not a control (Lesson 5).
     - **Then the hand-written set.** The root SCPs and RCPs already reach this account by inheritance, so
       what belongs *here* is what makes the identity plane's own blast radius smaller: deny deletion or
       disabling of the CloudTrail this account is recorded in, and deny the account creating compute at all
       — there is no workload here, only Terraform managing Identity Center, so `ec2:RunInstances`,
       `sagemaker:Create*` and the rest of the D22 compute list apply for exactly the same reason they apply
       to `Data`.
     - **Do not put the Identity account under the `Data` OU's set to save writing one**, tempting as the
       overlap looks: `Data`'s set denies `s3:DeleteBucket` and `lakeformation:DeregisterResource` and carves
       out `datazone:*` and the catalog-maintenance role, none of which means anything here, and an OU whose
       policy is *mostly* right is the kind of thing nobody re-reads.

   **7.7 — The Control Tower managed controls: use theirs, do not hand-roll these two.**

   - **Region restriction** (revised 2026-08-08; **corrected 2026-08-09 — there are two of these controls,
     and the plan knew only the one that cannot be canary-tested**). Goal unchanged: **`us-west-2` as the
     only allowed region**. Three reasons it is not in the hand-written set:
     - **Global services resolve to `us-east-1`.** `iam:CreateRole` goes to `iam.amazonaws.com`, which
       answers in `us-east-1`, so `aws:RequestedRegion` is `us-east-1` and a naive deny breaks IAM outright.
       The correct exemption is **`NotAction` on the global service prefixes**, never adding `us-east-1` to
       the allowed regions — the second is what an earlier version of this plan described, and it is much
       looser: it would permit `ec2:RunInstances` in a region with no Config recorder, no GuardDuty and no
       endpoints, which is precisely the blind spot the control exists to remove.
     - **That exemption list has to stay complete as AWS ships services, and AWS maintains theirs.** This is
       Lesson 14 applied to a list rather than to a condition — and the useful finding is that **AWS's
       default `NotAction` already contains every prefix this project was worried about**: `iam:*`,
       `organizations:*`, `sts:*`, `kms:*`, `sso:*`, `config:*`, `access-analyzer:*`, `route53:*`,
       **`route53domains:*`** (a separate prefix, and the one that registers the D15 domain at Stage 13),
       `acm:*`, `cloudfront:*`, `shield:*`, `waf:*`/`wafv2:*`, the whole billing family
       (`billing:*`, `budgets:*`, `ce:*`, `cur:*`, `pricing:*`, `tax:*`), and **`s3:PutAccountPublicAccessBlock`
       plus `s3:ListAllMyBuckets`** — the pair that interlocks with 7.4. **So do not maintain a list: read
       the current one off the control's `Artifacts` tab in the Control Tower console and diff it against
       what this project calls** (**verify while executing (vii)**), then add only what is genuinely
       missing, through `ExemptedActions`.
     - **It also needs principal exemptions, not just service ones.** AWS's default already exempts
       `AWSControlTowerExecution`, `aws-controltower-ConfigRecorderRole`,
       `aws-controltower-ForwardSnsNotificationRole` and `AWSControlTower_VPCFlowLogsRole`, or the landing
       zone's own machinery breaks. A hand-written control has to remember them; this is the third reason
       not to write one.

     **Which of the two controls to enable, and this is the part that changed.** AWS ships a
     landing-zone-wide Region deny **and** an OU-scoped one, and only the second can be exercised the way
     D29 requires:

     | | `GRREGIONDENY` | `CT.MULTISERVICE.PV.1` |
     |---|---|---|
     | Scope | The **whole landing zone**; applies to every registered OU at once | **Per OU**, chosen at enable time |
     | How | Landing zone settings → **Modify settings** — i.e. a landing-zone update, not a checkbox | Controls library → **Enable control** → pick the OU, or `aws controltower enable-control` |
     | Parameters | Region list only | `AllowedRegions` (mandatory), `ExemptedActions`, `ExemptedPrincipalARNs` |
     | Canary-testable (D29) | **No** | **Yes — attach it to `Policy Test` first** |

     **Do it in this order.** Enable `CT.MULTISERVICE.PV.1` on **`Policy Test`** with
     `AllowedRegions=["us-west-2"]`, run the region pair from 7.3 under `awsds-policy-canary` (`us-east-1`
     → `UnauthorizedOperation`, `us-west-2` → `DryRunOperation`), and confirm the *must still succeed* list —
     `iam:ListRoles`, `budgets:DescribeBudgets`, `ce:GetCostAndUsage`. Only then enable it on the real OUs
     (`Interactive`, `Workloads`, `Data`, `Identity`) **or** turn on the landing-zone-wide one, which is the
     simpler operation once the parameters are known to be right. **Enabling both is possible and the
     interaction is hard to predict** — AWS says so in the control's own documentation — so pick one and
     record which, in `log/stage-01b-identity-and-controls.md`.

     **Two facts to have before you start.** The home region cannot be denied, and *nothing must already
     exist in the regions being denied* — trivially true here, and it is the reason to do this now rather
     than at Stage 12. Both controls are reversible from the Control Tower console, which is the
     compensating fact if the landing-zone-wide one is chosen; the landing-zone route also costs a
     landing-zone update, so **budget it as an hour, not a click**.

   - **The two root-user controls, and the one parameter that decides whether they break 1a step 6.**
     `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` and `AWS-GR_RESTRICT_ROOT_USER` are *strongly recommended*
     controls — **not enabled by default**, so today the organization has neither.
     - The access-key one is free of consequences and matches the invariant D16 already states.
     - The other denies `*` wherever `aws:PrincipalArn` matches `arn:*:iam::*:root`, and **that reaches the
       privileged root sessions 1a step 6 depends on**: in a member account an `sts:AssumeRoot` session *is*
       that principal, so the control would deny the very action that restores a root credential or unlocks
       a self-denied S3 bucket policy. Enable it **with the `ExemptAssumeRoot` parameter**, which carves the
       centralized path back out by exempting requests carrying `aws:AssumedRoot`.
       **Three mechanics, confirmed against the control's documentation, because each is a way to get it
       wrong:** the parameter exists **only** on `AWS-GR_RESTRICT_ROOT_USER`; it is set **per OU**, at enable
       time, so every OU this control is enabled on needs it — miss one and 1a step 6's recovery path is
       closed in exactly that OU; and **it does not accept `false`** — presence means exempt, absence means
       not exempt, so "set it to false" is not a thing you can do or read back.
     - Both controls also take `ExemptedPrincipalArns`; neither exemption should be a wildcard account.
     - **The asymmetry that makes this safe to enable at all:** the controls attach to OUs, and the
       Management account is exempt from SCPs, so the break-glass root is untouched either way (D16).
       Enabled from the Control Tower console, so this one is reversible without a detach.

   **7.8 — RCPs, tag policies, declarative policies.**

   - **RCPs** — deny access to S3, STS, KMS, SQS and Secrets Manager from principals outside the
     organization (`aws:PrincipalOrgID`): the trusted-identities axis of `plan/architecture.md` §4.2. Three
     things that are not optional:
     - **The policy type must be enabled first** (7.2), and the organization must have all features on.
     - **The condition needs `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}` beside the
       `aws:PrincipalOrgID` test.** Without it the RCP denies AWS's own service principals reaching your
       resources — CloudTrail and Config writing to the Log Archive bucket being the two that break first,
       in the account whose whole job is to receive them. Service-*linked* roles are exempt from RCPs by
       construction; service principals are not, and that distinction is the entire bug.
     - **RCPs do not apply to the Management account at all**, so nothing here protects it and nothing here
       can lock it out. That is the same asymmetry D16 relies on.
   - **Tag policies** — standardize the mandatory tags from `plan/conventions.md` §6, with a precision the
     previous version of this plan got wrong: tag policies constrain *tagging operations*, they cannot force
     a resource to be created with tags at all. **The forcing function is an SCP with
     `aws:RequestTag`/`aws:TagKeys` conditions on the create actions that matter** (EC2, S3, SageMaker). One
     or the other, or the tags are a convention — and conventions do not survive contact with a
     `terraform apply` at 23:00.
     **That forcing SCP is a decision, not a formality, and it is the one policy in 7.5-7.8 that binds the
     builder as hard as it binds anyone** (Lesson 18 read forwards for once). Three things it breaks if it
     is written broadly:
     - **Resources whose create API takes no tags.** `aws:RequestTag` can only be satisfied by a call that
       carries tags; where the API does not accept them, a `Deny` on the create action is a deny full stop.
     - **Resources this project does not create.** D26's blueprints provision project buckets, Glue
       databases, Athena workgroups and execution roles into Sandbox and Development under DataZone's own
       provisioning roles — they will not carry `CostCenter=<stage>`, and the failure surfaces at Stage 6 as
       a project that will not create.
     - **The landing zone's own machinery**, which creates resources in every enrolled account.
     **So adopt it narrowly or not at all**, and adopt it *here*, in writing: the defensible scope is the
     handful of create actions whose cost this project actually attributes — `ec2:RunInstances`,
     `s3:CreateBucket`, `rds:CreateDBInstance` — with `Environment` and `Project` as the required keys and
     nothing else, exempting the blueprint and Control Tower principals per 7.1's enumerated-ARN rule. It is
     the fifth decision due while executing, and it is the one whose cost lands on a stage nobody is looking
     at yet.
     **Write both enumerations so a per-unit token is admissible before it is needed (D35).** The `<env>`
     list and the tag policy's allowed values both enumerate `sandbox`; an enumeration that does not admit a
     per-unit value turns the first apply in a freshly vended account into an `AccessDenied`, discovered by
     whoever is standing that account up. `plan/conventions.md` points at this step for exactly this reason.
   - **Declarative policies** — enforce IMDSv2 and EC2 public-access defaults org-wide. Policy type enabled
     in 7.2.

8. **Security delegation, the free detective control, and the alarm that has no preventive control above
   it** (principle 9, as amended 2026-08-08).

   This step used to enable Security Hub, GuardDuty and Access Analyzer here, all at once, citing principle
   9. That was a misreading of it: the principle argues that **prevention has precedence and that the
   preventive half belongs in the landing zone because it is free** — it says nothing in favour of paying
   for detection over empty accounts. Between this stage and Stage 5 there is no governed data to exfiltrate
   and no workload to attack; what exists is empty accounts, VPCs and state buckets, while Stages 2-3 are
   the heaviest `terraform apply` period the project will ever have.

   **8.1 — Delegation is not free of consequence, which changes what belongs in this step.** The plan used
   to delegate every security service to the Audit account here and enable each service later, on the
   premise that delegation is a free organization-level act. **Checked against the documentation, that
   premise holds for one of the four:**

   | Service | Does delegation enable it? | Where the delegation now happens |
   |---|---|---|
   | **IAM Access Analyzer** | No — registering the delegated administrator creates no analyzer | **Here**, 8.2 |
   | **GuardDuty** | **Yes** — "GuardDuty gets enabled automatically … in the current AWS Region" for the administrator account | **Stage 4 step 10**, with the enablement |
   | **Security Hub** | **Yes** — designating the administrator "enables Security Hub CSPM in the current AWS Region for the delegated administrator account" | **Stage 5 step 13**, with the enablement |
   | **Macie** | Expect the same; **verify — at Stage 11, not here, since nothing in 1b touches Macie** | **Stage 11**, with the enablement |

   **What this costs, stated rather than discovered:** three later stages each need one visit to the
   Management console, which this stage was trying to spare them. That is the smaller price. Delegating
   GuardDuty here would start both its meter and its **30-day free trial** over eight empty accounts — the
   one window in which its real cost for this environment could have been measured (Lesson 7 in reverse:
   a service enabled early goes stale in the direction that flatters the estimate).

   **8.2 — Do here: IAM Access Analyzer, external-access findings, org-wide from the Audit account.**

   - Register `access-analyzer.amazonaws.com` with the Audit account as delegated administrator from
     Management, then create the **organization-level external-access analyzer** in Audit, in `us-west-2`.
   - **These findings are free**, so they follow the preventive rule rather than the detective one — and
     they catch exactly the class of mistake Stages 2 and 3 create: a bucket policy or a role trust policy
     that grants to a principal outside the organization. AWS also names them as the thing to read *before*
     attaching RCPs, which is a second reason they come before step 7 is repeated in code at Stage 2.
   - **Unused-access findings are the paid half and stay in Stage 12.**

   **8.3 — Do here: an alarm on membership changes to Control Tower's own groups (D33), which D34 promotes
   from prudent to load-bearing.**

   - **Why it has to exist.** Those groups are pre-wired: one membership edit puts a person into
     `AWSAdministratorAccess` on Management, Log Archive and Audit, or `AWSPowerUserAccess` on every
     account, with nothing to review and no approval anywhere. **`AWSControlTowerAdmins` is no longer
     empty** — it permanently holds the vending owner — so this alarm is the only thing that distinguishes
     "the expected member" from "a second one somebody added".
   - **There is no preventive control above it.** The Identity Center administrator is the top of the
     identity plane, and after step 1 that is the delegated administrator in the Identity account, who can
     place themselves in `AWSControlTowerAdmins`. Step 4 closes the *assignment* path into Management and
     leaves the *membership* path open by construction. So the control is detective, and it is also what
     `ORGANIZATION.md` names as one of the three things containing the infrastructure user itself
     (Lesson 18).
   - **Build it as a metric filter on the organization trail's log group, not as a local EventBridge
     rule** — this is a correction, and the reason is step 1. Identity Center group-membership calls are
     made **from the account administering the directory**, which after the delegation is the Identity
     account, not Management. An EventBridge rule in Management would watch an account the calls have just
     stopped being made in, and would report nothing while looking healthy (Lesson 13). The organization
     trail already collects member-account events into
     **`aws-controltower/CloudTrailLogs-*` in the Management account** — 1a step 5 established exactly this
     property and used it for the same reason — so:
     - Metric filter on that log group matching the events that change group membership and account
       assignments. **There are three event sources, not one, and an earlier version of this step named only
       the console pair** — AWS's own documentation says to consider both the public and the console API
       when detecting "adding a member to a group":

       | Event source | Events | Emitted by |
       |---|---|---|
       | `sso-directory.amazonaws.com` | `AddMemberToGroup`, `RemoveMemberFromGroup` | The Identity Center **console** |
       | `identitystore.amazonaws.com` | `CreateGroupMembership`, `DeleteGroupMembership` | The **API/CLI/Terraform** path |
       | `sso.amazonaws.com` | `CreateAccountAssignment`, `DeleteAccountAssignment` | Either |

       **Matching only the console pair is the failure mode this project walks into by design**, because
       Stage 2 moves identity into `terraform-live/identity/sso/` — from then on every membership change this
       alarm exists to catch arrives through `identitystore`, and a filter that misses it reports nothing
       while looking healthy (Lesson 13).
     - **Filter on group *IDs*, resolved first — not on names.** These events carry the group's `groupId`
       (a GUID), and CloudTrail's Identity Center payloads changed in January 2025 in exactly the fields a
       name-based filter would key on (`userName`, `principalId`, `displayName`). So resolve them once —
       `aws sso-admin list-instances` for the `IdentityStoreId`, then
       `aws identitystore list-groups --identity-store-id <d-xxxx>` — record the IDs of
       `AWSControlTowerAdmins`, `AWSAccountFactory` and the rest of the pre-wired set in
       `log/stage-01b-identity-and-controls.md`, and put those in the pattern. **If that proves awkward,
       take the cheaper and stricter option: do not filter by group at all.** Membership changes across
       this whole directory are a handful of events a year; a slightly noisy alarm that fires is worth more
       than a precise one that cannot.
     - Namespace `AWSDS/Security`, its own metric name, metric value `1`, **`Default value` left empty** —
       a custom metric is USD 0.30/metric-month and is metered only in the hours it publishes.
     - Alarm: Sum, 1 minute, `≥ 1`, **missing data `notBreaching`** (the price of the empty default value),
       delivering to `awsds-org-break-glass-alerts` — the same SNS topic as the break-glass alarm, which is
       already confirmed on both channels.
     - **Verify while executing (ix):** which account the events land in, and under which of the three event
       sources above, before trusting the filter. If they turn
       out to be recorded only in the Identity account, keep the filter there instead and point it at the
       same topic cross-account. Record which it was.
     - **Expect the alarm to fire minutes late, and do not treat that as a failure.** The path is
       CloudTrail → S3 → CloudWatch Logs → metric filter → alarm, so single-digit minutes of delay is normal
       for a detective control of this shape. It is why 1a's break-glass alarm is built the same way.
   - **Fire it once**, by adding and removing a member deliberately. An untested alarm is a hypothesis —
     1a step 5 makes the same point about the same topic.

   **8.4 — Deliberately not here.**

   - **GuardDuty → Stage 4 step 10**, with the WireGuard instance: the first internet-facing resource in the
     project, and the one whose compromise GuardDuty actually detects. Its **delegation goes with it** (8.1).
   - **Security Hub → Stage 5 step 13**, with the first governed data — its standards checks report on
     resources, and before Stage 5 there are almost none to report on. Note the compounding this avoids:
     Security Hub's checks are implemented as **AWS Config rules**, so enabling it adds rule evaluations on
     top of the configuration items Control Tower is already recording, precisely during the stages that
     create and destroy the most resources. Its **delegation goes with it** (8.1).
   - **Macie → Stage 11**, unchanged, delegation included.
   - **What an institution does instead:** enables all of it on day one, because the money is noise and "we
     will turn it on later" is how detective controls never get turned on
     (`plan/institutional-delta.md` carries the row). The mitigation here is that each service names the
     *step* that enables it and carries a deliverable there, rather than being deferred to a vague later.

9. **Make the audit trail tamper-evident.** An audit log that the compromised party can edit is not an audit
   log. Do this before there is anything worth hiding in it.

   **9.1 — Identify the right bucket first, because there are at least two and one of them must not be
   touched.**

   - **Object Lock goes on the CloudTrail log bucket, `aws-controltower-logs-*`, in the Log Archive
     account.**
   - **It must never go on `aws-controltower-s3-access-logs-*`.** That bucket is the destination for S3
     server access logging, and **S3 buckets with Object Lock cannot be used as a server access log
     destination** — locking it silently stops access logging for the bucket beside it.
   - **Check the landing zone version while you are here.** From landing zone 4.0 the *Config* logs move to
     `aws-controltower-config-logs-*` in the Config integration (Audit) account, while the CloudTrail logs
     stay in Log Archive. The target of this step is the CloudTrail bucket either way; knowing the version
     tells you whether a second bucket exists that this step deliberately does not cover.

   **9.2 — Use compliance mode, and this is the step that limits D33.** The earlier wording left this
   unsaid, so it was an intention rather than a control (Lesson 5). `AWSControlTowerAdmins` is administrator
   *of the Log Archive account*, so the principal this step defends against holds
   `s3:BypassGovernanceRetention`: **in governance mode it walks straight through.** In compliance mode a
   locked object version cannot be deleted or overwritten by anyone, including that account's root. **Since
   D34 that principal is permanent**, so this is not a control covering a two-week bootstrap window — it is
   what keeps the audit trail surviving its own administrator for as long as the organization exists.
   Getting the mode wrong here is a permanent hole, not a temporary one.

   **9.3 — Three practical constraints, all of which bite later if ignored.**

   - **Compliance mode is not reversible and not shortenable**, and Object Lock itself cannot be disabled
     once enabled on a bucket. The retention period is a commitment, so keep it **short** — long enough that
     tampering is detectable, not long enough to become an archive. This is a detection control, not a
     retention policy.
   - **Keep the retention shorter than Control Tower's own log lifecycle expiration**, or the landing zone's
     lifecycle deletions start failing against locked objects. **Read the bucket's existing lifecycle rule
     first** and set the lock inside it.
   - **The bucket already exists**, which used to make this step impossible; Object Lock can now be enabled
     in place on an existing bucket (console: Properties → Object Lock → Edit → Enable; CLI:
     `put-object-lock-configuration`), and doing so requires versioning, which S3 turns on and which can no
     longer be suspended. **Existing objects are not locked retroactively** — the default retention applies
     to objects written *after* it, which is fine here and is the reason for "before there is anything worth
     hiding".

   **9.4 — CloudTrail log file validation.** Control Tower's `aws-controltower-BaselineCloudTrail` is
   expected to have it on already; **verify rather than enable**, because editing the trail is landing-zone
   drift (1a step 5 makes the same distinction: adding a metric filter to the log group is not an edit to
   the trail). `aws cloudtrail get-trail --name aws-controltower-BaselineCloudTrail` reports
   `LogFileValidationEnabled`.

   **9.5 — Verify while executing (iv):** that enabling Object Lock on the Control Tower-managed bucket does
   not raise landing-zone drift. Record the answer.

10. **Decide what the AWS Config recorder records — starting by measuring it.**

    **10.1 — Why this step exists.** Config is the main recurring cost of the landing zone
    (`plan/cost-model.md`): USD 0.003 per configuration item, recorded in **every governed account**, so
    the cost scales with the account count and with how busy `terraform apply` is — exactly the shape that
    surprises people during the build-out stages.

    **10.2 — There is no console switch, and this is the correction.** The step used to read "restrict the
    AWS Config recorder to the resource types this project actually uses", which is one line describing
    something Control Tower does not offer:

    - Control Tower **enables and owns** the recorder in every enrolled account. From landing zone 3.0 it
      already limits *global* resources to the home region, which is the one restriction you get for free.
    - **Editing the recorder by hand in a governed account is drift** and is liable to be reset by a
      landing-zone update, an account update or a re-enrollment — the same class of behaviour step 3.8
      warns about for direct assignments.
    - The documented path is a **deployed solution**: a Lambda driven by Control Tower lifecycle events
      (`UpdateLandingZone`, `CreateManagedAccount`, `UpdateManagedAccount`) that re-applies a chosen
      resource-type list through each account's `AWSControlTowerExecution` role. That is a real piece of
      infrastructure with its own failure modes, not a checkbox.

    **10.3 — So do this instead, in this order.**

    1. **Measure — and note that this takes two sign-ins, which the step used to hide.**
       - **Spend**, from **Management**: Cost Explorer filtered to `AWS Config`, grouped by **usage type**
         and by **linked account**, for the last full month. The usage-type breakdown is what separates
         configuration items from rule evaluations, and only one of those is what step 10 is about.
       - **Volume**, from **Audit**: 1a made Audit the **Config aggregator** account, so the item counts for
         every enrolled account are readable there in one place —
         `aws configservice describe-configuration-aggregators` to find it, then the Config console's
         aggregated view. Going account by account under the `awsds-infra-*` profiles gives the same answer
         for more work, and misses Log Archive and Audit, where the infrastructure user has no assignment.
       Record both numbers in `log/stage-01b-identity-and-controls.md`. Prices are measured, not reasoned
       (Lesson 6), and the same rule applies to volumes.
       **One caveat on the number you will get:** the accounts are days old and nearly empty, so this
       measures the recorder's floor, not its cost during Stages 2-3. That is the honest reason step 10.3
       point 2 defers the decision to Stage 12 rather than the reason it is written as if the number were
       final.
    2. **Decide against the measured number, not the estimate.** If the item count sits inside the
       USD 2.50-5.00/month band `PRICING.md` projects, the honest answer is to leave the recorder alone and
       revisit at **Stage 12 step 5**, when there is a real bill and Stage 2-3's apply storm is over.
    3. **Only if it does not**, deploy the lifecycle-event solution — and note that it must exclude nothing
       Control Tower's own controls and Security Hub's checks depend on, since both consume Config.
    4. **Do not unenroll an account to cut the bill.** It is the documented lever and it is the wrong one
       here: `Policy Canary` is the tempting candidate and unenrolling it removes the Control Tower control
       baseline that makes D29's battery a valid test rather than a false pass.

11. **Enable organization-wide resource sharing, so the Lake Formation shares of Stage 5 can exist**
    (D22, INT-11).

    Two settings to make now, **in two different accounts** — which is half of why this step is easy to get
    wrong — and neither of which announces its absence.

    **11.1 — `ram:EnableSharingWithAwsOrganization`, called from the *Management* account.** It enables
    trusted access for RAM across the organization; it is not a Data Governance setting and cannot be done
    from there. Without it, a Lake Formation grant to another account produces an AWS RAM *invitation* that
    somebody has to accept by hand, and it reappears every time the share is recreated. With it, accounts
    inside the organization receive shares directly.

    **11.2 — Lake Formation cross-account version 3 or above, set in the Data Governance account**
    (`awsds-infra-data`). Versions below 3 cannot grant to an Organization or an OU at all, only to an
    explicit list of account IDs — and this project has three consumers at N=1, one more per business unit
    (D35), with more implied by every `plan/institutional-delta.md` row about scale.

    **Prefer the console for this one, and if you use the CLI, read this first.** The version lives inside
    `DataLakeSettings`, and **`put-data-lake-settings` replaces that whole structure rather than patching
    it** — call it with only `Parameters` set and you have just cleared `DataLakeAdmins`,
    `CreateDatabaseDefaultPermissions` and `CreateTableDefaultPermissions` in the same call. The safe shape
    is get-modify-put:

    ```bash
    aws lakeformation get-data-lake-settings --profile awsds-infra-data > /tmp/lf.json
    # edit DataLakeSettings.Parameters.CROSS_ACCOUNT_VERSION to "3", keep every other key
    aws lakeformation put-data-lake-settings --profile awsds-infra-data --cli-input-json file:///tmp/lf.json
    ```

    Today the structure is nearly empty, which is exactly why this is cheap to do now and expensive to do
    after Stage 5 has registered a lake and named its administrators. Note also that changing these settings
    requires being a Lake Formation **data lake administrator** or holding
    `lakeformation:PutDataLakeSettings` outright — the infrastructure user has the latter through
    `AdministratorAccess`, so no administrator has to be registered first; Stage 5 still creates the real
    one.

    **11.3 — How to verify it, because the obvious command does not.**
    `aws ram get-resource-share-associations` requires an `--association-type` and lists the associations of
    shares that already exist — with no share yet created it returns an empty list, which is
    indistinguishable from the failure it is supposed to detect (Lesson 13). The two checks that actually
    answer the question:

    ```bash
    aws organizations list-aws-service-access-for-organization --query "EnabledServicePrincipals[?ServicePrincipal=='ram.amazonaws.com']"
    ```

    ```bash
    aws lakeformation get-data-lake-settings --profile awsds-infra-data --query 'DataLakeSettings.Parameters'
    ```

    The first is run from Management and must return `ram.amazonaws.com`; the second must read a
    cross-account version of 3 or above back. Confirming a silent-failure mode with a command that is itself
    silent is how INT-11 stays open for a month.

    **11.4 — Not here, and deliberately: the third INT-11 item.** The
    **`AWSLakeFormationCrossAccountManager`** managed policy on the grantor and
    `ram:AcceptResourceShareInvitation` on the data lake administrator role **in each consumer account** are
    the fallback path if 11.1 or 11.2 is ever unavailable — and **neither role exists yet**: the data lake
    administrator is created in Stage 5, the consumer-side roles in Stage 5 and Stage 9. Attempting it here
    is attaching a policy to a principal that has not been written. It is recorded here because INT-11 is
    settled here; it is *executed* in Stage 5 step 7.

    **11.5 — Why this step is in 1b at all.** It is organization-level and manual, like everything else in
    this stage. Stage 5 step 7 assumes it and will fail confusingly without it: the grant appears to succeed
    on the producer side and the resource simply never shows up on the consumer side.

    **11.6 — Verify while executing (v):** that the Lake Formation cross-account version can be raised to 3+
    in an account that has no lake in it yet. If it cannot, that setting moves into Stage 5 and the rest of
    this step stays here.

---

## Deliverables of 1b

Each one is written so that its output differs between working and broken (Lesson 13):

- **SSO login works and the group path is real:** `aws sts get-caller-identity --profile awsds-infra-sandbox`
  returns the Sandbox account ID, and the same for every other profile from step 5.
- **The delegation took effect:** `aws sso-admin list-instances --profile awsds-infra-identity` returns the
  Identity Center instance — from the *Identity* account, which is what makes it evidence about the
  delegation rather than about Identity Center existing.
- **The perimeter is real:** an attempt to write to an S3 bucket outside the organization is denied, **and
  the CloudTrail record for that call names an explicit deny in a service control policy.** The denial alone
  is not the deliverable; a bucket you do not own would have refused you anyway.
- **The ceiling is real in the other direction too:** `ec2:RunInstances --dry-run` in `us-east-1` returns
  `UnauthorizedOperation`, while the same call in `us-west-2` returns `DryRunOperation`.
- **The audit trail survives its own administrator:** resolve the real bucket name first — the `*` in
  `aws-controltower-logs-*` is this document's shorthand, not a glob the CLI expands, and pasting it returns
  a bucket-not-found that reads like a failed lock:

  ```bash
  BUCKET=$(aws s3api list-buckets --query "Buckets[?starts_with(Name,'aws-controltower-logs-')].Name | [0]" --output text)
  aws s3api get-object-lock-configuration --bucket "$BUCKET"
  ```

  Run it **inside Log Archive** — CloudShell under `AWS Control Tower Admin` → `AWSAdministratorAccess`, per
  "Who executes what"; the infrastructure user has no assignment there and no profile to pass. It must
  report `COMPLIANCE`, with a retention shorter than the bucket's lifecycle expiration
  (`aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET"`).
- **The membership alarm is a control and not a hypothesis:** it fired once, on both channels, on a
  deliberate add-and-remove.
- **Stage 5's shares have somewhere to land:**
  `aws organizations list-aws-service-access-for-organization` (from Management) lists `ram.amazonaws.com`,
  and `aws lakeformation get-data-lake-settings --profile awsds-infra-data` reports a cross-account version
  of 3 or above. *(Note what this deliverable used to say:
  `aws ram get-resource-share-associations` from the Data Governance profile, which returns an empty list
  both when sharing is enabled and when it is not.)*

## Decisions due while executing

**Blocking questions for the user: none** — nothing here waits on an input before the stage can start. But
six decisions are *made* during it, and each has to be written into
`log/stage-01b-identity-and-controls.md` rather than left to whoever is at the keyboard (Lesson 16). Two of
them are permanent:

| # | Decision | Step | Reversible? |
|---|---|---|---|
| 1 | Whether the `Interactive` OU gets a policy set of its own, and whether the `sagemaker:CreateNotebookInstance` candidate is adopted | 7.6 | Yes |
| 2 | The name of this project's administrator permission set — `AdministratorAccess` as `ORGANIZATION.md` states, or a rename propagated in the same session | 3.2 | Yes, but it touches three other files |
| 3 | **The Object Lock retention period** | 9.3 | **No — compliance mode cannot be shortened and Object Lock cannot be disabled** |
| 4 | Whether the Config recorder is left alone after the measurement | 10.3 | Yes |
| 5 | Whether the tag-forcing SCP is adopted, and over which create actions | 7.8 | Yes, but its cost lands at Stage 6 |
| 6 | Which Region deny control is used — `CT.MULTISERVICE.PV.1` per OU, or landing-zone-wide `GRREGIONDENY` | 7.7 | Yes; enabling **both** is what is hard to undo, because the interaction is not predictable |

The domain name (D15) used to be listed here as "needed before Stage 7"; the 2026-08-09 revision moved it
to **Stage 13**, which is now the only stage that registers anything public. Nothing between here and there
depends on a name we do not already own.

## Risks

- **Step 7 is the only irreversible-from-inside step in the stage.** A bad `Deny` has no in-account repair
  and the recovery path is a detach from the Management account (D16; D30 reverted). The `Policy Canary`
  battery and an already-open Management console are the mitigations, and both are procedures rather than
  properties — they only work if they are actually done.
- **Step 9's compliance-mode retention cannot be shortened, and Object Lock cannot be disabled.** A
  retention chosen too long makes the Log Archive bucket an archive nobody chose to pay for; one longer than
  the lifecycle expiration makes the landing zone's own deletions fail.
- **Step 1's delegation widens the Identity account's blast radius before step 8's alarm exists.** Keep the
  two in the same session.
- **Nothing here is torn down between sessions** — everything 1b creates is `[P]` (D11). Account e-mails
  cannot be reused after an account is closed (a closed account holds its e-mail for 90 days), which is
  exactly why D11 keeps accounts in the persistent layer.
- **Not a risk of this stage, though it was listed as one:** "Control Tower landing zone deployment takes
  ~60 minutes and is awkward to undo" belongs to 1a, which is done. It was copied across in the split.

## Verifications to answer while executing

Each is stated in its step; the list is the index, not a second copy. Record every answer in
`log/stage-01b-identity-and-controls.md`, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | Does the Identity Center delegation coexist with the landing zone without raising drift? | 1 |
| ii | Are Management-targeted assignments the *only* thing the delegated administrator cannot manage? | 4 |
| iii | Do the hand-written SCPs/RCPs conflict with the SCPs Control Tower manages itself? | 7.3 |
| iv | Does enabling Object Lock on the Control Tower-managed bucket raise landing-zone drift? | 9.5 |
| v | Can the Lake Formation cross-account version be raised to 3+ with no lake in the account? | 11.6 |
| vi | Does removing an Account Factory direct assignment stick, or is it re-created? | 3.8 |
| vii | Does `CT.MULTISERVICE.PV.1`'s current default `NotAction` still cover everything this project calls from `us-east-1`? Read it off the control's `Artifacts` tab and diff | 7.7 |
| viii | Which namespace does each Unified Studio action actually evaluate under — `datazone:*` or `sagemaker:*`? **Ask it of the `Data` OU as well as of `Workloads`** | 7.6 |
| ix | Are Identity Center membership events recorded in Management's org-trail log group after the delegation, and under which of the three event sources? | 8.3 |

**Was (vii), now answered from the documentation rather than by execution:** *"is Region deny
landing-zone-wide, i.e. untestable against `Policy Test` first?"* — **the landing-zone control
`GRREGIONDENY` is; the OU-scoped `CT.MULTISERVICE.PV.1` is not, and can be canary-tested.** 7.7 carries the
choice that replaces the question.

**Was (ix), and it does not belong to this stage:** *"does Macie's delegation enable Macie, as GuardDuty's
and Security Hub's do?"* — 8.1 defers Macie's delegation to **Stage 11**, so nothing in 1b can answer it.
It is recorded in 8.1's table as the thing to check *there*, and dropped from this list, which is about
what is answered while executing 1b.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
