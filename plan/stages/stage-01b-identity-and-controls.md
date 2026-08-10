# Stage 1b — Identity Center, permission sets, and the alarm above them

| | |
|---|---|
| **Status** | **next** — not started |
| **Prerequisites** | Stage 1a complete, bar the deferred `Staging` vend. **Steps 3 and 5 must skip their `Staging` items** (`DataScientistStagingAccess`, `DeploymentManagerAccess` on Staging, the `awsds-infra-staging` profile) and pick them up when the account is vended |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D14](../decisions/D14-supply-chain-account.md), [D16](../decisions/D16-break-glass.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D29](../decisions/D29-policy-canary.md), [D30](../decisions/D30-scp-recovery.md), [D31](../decisions/D31-approver-read.md), [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | Nothing cross-account; this stage is what makes every later stage reachable. Step 5's profiles are the precondition for **Stage 1c**, **Stage 1d** and everything from Stage 2 onwards |
| **Log** | [`log/stage-01b-identity-and-controls.md`](../../log/stage-01b-identity-and-controls.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

**Was "do not lose it", now settled: 1a step 2's budget alert thresholds (50/80/100%) and Cost Anomaly
Detection are deliberately skipped** (user, 2026-08-09). They are not pending work and are not to be picked
up in passing here, or in 1c or 1d. **The USD 50 budget therefore notifies nobody**: the ceiling is a number
read from the console, so the cost control of D12 is now the operator's own habit of looking — which is an
intention, not a control (Lesson 5). `plan/cost-model.md` names the exposure this leaves standing (a
forgotten `egress/` day at ~USD 4.08), and D12 carries the revision trigger.

---

**Step numbers are identifiers, not an order — and they run 1-6 and 8 here.** The landing zone's second
half was one stage until 2026-08-09 and is now three (1b, 1c, 1d), split along the sessions it already
described. **The step numbers did not change in the split**, so `Stage 1c step 7` and `Stage 1d step 9` are
the same steps every other file already references; only the stage prefix moved. Step 7 is
[Stage 1c](stage-01c-preventive-policies.md); steps 9, 10 and 11 are
[Stage 1d](stage-01d-org-wide-enablement.md).

Everything here is fast, reversible and iterative. **Nothing in this stage is irreversible** — that
property belongs to Stage 1c's step 7 and Stage 1d's step 9, which is the reason they are separate stages
rather than the tail of this one.

## The stage at a glance

Seven steps, and the order is a dependency chain rather than a listing. Read this table to plan a session;
read the step for how to do it. **The `Consumes` column is per step** — executing step 5 does not require
reading sixteen decision files.

| # | What | Identity | Consumes | Why it is here and not later |
|---|---|---|---|---|
| 1 | Delegate Identity Center to the Identity account | CT Admin @ Management | D10, D33 | Everything in 2-4 is done *from* Identity |
| 2 | Users and groups, beside Control Tower's | Infra user @ Identity | D32, D33, D34, D35 | — |
| 3 | Permission sets and assignments | Infra user @ Identity | D14, D16, D18, D19, D20, D21, D22, D29, D30, D31, D32 | — |
| 4 | Confirm no persona reaches Management | Infra user @ Identity | D34 | Closes the assignment path that step 8 then watches |
| 5 | Local `aws configure sso` profiles | Infra user, laptop | D29 | **Stages 1c and 1d cannot start without a member-account profile** |
| 6 | AZ name→ID mapping per account | Infra user, laptop | D14, D20, D21 | Stage 3 anchors subnets on the answer |
| 8 | Access Analyzer + the group-membership alarm | CT Admin @ Management / Audit | D33, D34 | The alarm is the only control over step 1's blast radius |

**Sessions.** Steps 1-6 are one sitting and are the bootstrap: nothing in this stage or the two that follow
is reachable without a profile. **Keep step 1 and step 8 in the same session** — step 1 widens the Identity
account's blast radius and step 8 is the only thing watching it. That constraint is why step 8 stayed here
rather than moving to Stage 1d with the rest of the org-wide work.

## Who executes what

**Every manual step names the identity that performs it, not only what it does** (Lesson 17). **Two
identities do all seven steps, through three sign-in paths** — and it is the *path* that is easy to get
wrong, which is how a step stalls on an `AccessDenied` that looks like a policy bug.

| Steps | Identity | Sign-in path |
|---|---|---|
| 1, 8.1 (delegations) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 8.2 (creating the analyzer *in Audit*) | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Audit** — the infrastructure user has *no* assignment there (`ORGANIZATION.md`) |
| 2, 3, 4 | **Infrastructure user** | access portal → `AWSAdministratorAccess` on **Identity** (the direct Account Factory assignment from 1a step 4 — this is what bootstraps the whole stage) |
| 5, 6 | **Infrastructure user**, from the laptop | the `awsds-infra-*` and `awsds-policy-canary` profiles created in step 5 |

**Nothing in this stage is performed by root**, and nothing is performed by a project persona other than
the infrastructure user. The *directory* holds six identities after step 2 (five personas plus
`AWS Control Tower Admin`); only these two ever execute anything here.

## What this stage costs

Principle 6 wants the number per stage, and this one is almost free:

- **Free:** Identity Center, groups, permission sets, IAM Access Analyzer **external-access** findings.
- **Added here:** one CloudWatch alarm (USD 0.10/alarm-month) and, if step 8's alarm is built as a metric
  filter, one custom metric (USD 0.30/metric-month, metered only in the hours it publishes — same trick as
  1a step 5).
- **Deliberately not added:** GuardDuty, Security Hub and Macie — including their **delegation**, which
  step 8 now moves with them, because delegating them turns them on.

The landing zone's one significant recurring line, AWS Config, is decided in **Stage 1d step 10**.

---

## To execute

### Step 1 — Register the Identity account as delegated administrator of IAM Identity Center (D10)

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
  SCPs, RCPs and tag policies written in **Stage 1c** are AWS Organizations objects and stay console-managed
  until **Stage 2 step 5.1 (INT-20)** adds a *second*, different delegation — a resource-based policy on
  the organization — after which the Identity account can also edit organization policy, Control Tower's
  guardrails included. Nothing to do about it here; the point is that step 8's alarm is the control above
  both delegations, so it is worth building well rather than quickly.
- **Verify while executing (i):** that the delegation coexists with the landing zone without raising
  Control Tower drift. Control Tower's handling of Identity Center has changed more than once. Record
  the answer in `log/stage-01b-identity-and-controls.md`.


### Step 2 — Create this project's users and groups in IAM Identity Center — beside Control Tower's, never inside them

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


### Step 3 — Create the permission sets and make the assignments

#### 3.1 — The seven sets, stated up front rather than discovered paragraph by paragraph

An earlier
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
or Stage 1c measures the wrong thing: an SCP is a *ceiling*, so a deny that a restricted principal could
not have exercised anyway proves nothing about it.

#### 3.2 — Settle the name collision before creating anything, because its failure mode is silent
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

#### 3.3 — One permission set object is one policy, however many accounts it is assigned to

This is the
mechanical fact behind two rows of the table and is worth stating once: `DataScientistAccess` is one set
assigned on Sandbox *and* Development (the two accounts are policy-identical at this level — that is what
putting them in one OU asserts, and what differs between them is the work, not the permission shape), and
`DevEnvStewardAccess` is one set assigned on Production, Sandbox and Development. So **scope by resource
ARN and by condition, never by "this account will not have that resource"**: a grant that is harmless in
one account because nothing matches it is a grant that appears the day something does.

#### 3.4 — `DataScientistAccess` does not start as `PowerUserAccess`

An earlier version of this plan gave
it `PowerUserAccess` "until Stage 6", which contradicts `ORGANIZATION.md` ("no permissions to perform
infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let the data
scientist create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the whole
design — for five stages. `AmazonSageMakerFullAccess` is *not* a safe starting point either: it grants
`s3:*` on any bucket with "sagemaker" in the name plus a broad `iam:PassRole`. It starts as: SageMaker
Studio use, read/write on the account's scratch and derived prefixes, Athena, ECR pull, and nothing else,
with a **permissions boundary** and `PassRole` scoped per the IAM rules in `plan/conventions.md` §6.

#### 3.5 — The three sets whose *denials* are the point of them

All three are approvers, and an approver
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

#### 3.6 — The two remaining data scientist sets (D18, D20)

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

#### 3.7 — What nobody gets, which is as much of the design as what they do

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

#### 3.8 — The direct assignments Account Factory left behind, and the ordering that is the whole of it (D32)

Every vended account carries a *direct* assignment of Control Tower's administrator set to the
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

#### 3.9 — Why this is by hand

Terraform cannot run before SSO login works. Stage 2 moves all of it into
`terraform-live/identity/sso/` and imports it.


### Step 4 — No project persona holds an assignment on the Management account — the infrastructure user included

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


### Step 5 — Configure the local SSO profiles now, not at the end of the stage

- **Do:** `aws configure sso` for `awsds-infra-sandbox`, `awsds-infra-dev`, `awsds-infra-prod`,
  `awsds-infra-data` and `awsds-infra-identity` — plus one more that is deliberately named differently,
  **`awsds-policy-canary`** (D29). `awsds-infra-staging` waits for the vend.
- **Why the canary profile is not an `awsds-infra-*`:** `Policy Canary` is not a Terraform-managed
  account and nothing is ever applied into it. The profile exists only to run Stage 1c's test battery, and
  the naming keeps that visible in shell history.
- **Verify:** `aws sts get-caller-identity --profile <each>` returns the expected account ID. This is the
  first real proof that steps 1-4 worked, and it is the precondition step 3.8 names before any direct
  assignment is removed.
- **This used to be the second-to-last step and that was an ordering bug.** Every step below this one,
  and everything in Stages 1c and 1d, does CLI or console work *inside a member account* — the
  `Policy Canary` battery, restricting the Config recorder, enabling Object Lock on the Log Archive
  bucket, raising the Lake Formation cross-account version in Data Governance, reading AZ IDs per
  account — and none of it is reachable without a profile.


### Step 6 — Check the AZ name-to-ID mapping

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


### Step 8 — Security delegation, the free detective control, and the alarm that has no preventive control above it

Principle 9, as amended 2026-08-08.

This step used to enable Security Hub, GuardDuty and Access Analyzer here, all at once, citing principle
9. That was a misreading of it: the principle argues that **prevention has precedence and that the
preventive half belongs in the landing zone because it is free** — it says nothing in favour of paying
for detection over empty accounts. Between this stage and Stage 5 there is no governed data to exfiltrate
and no workload to attack; what exists is empty accounts, VPCs and state buckets, while Stages 2-3 are
the heaviest `terraform apply` period the project will ever have.

#### 8.1 — Delegation is not free of consequence, which changes what belongs in this step

The plan used
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

#### 8.2 — Do here: IAM Access Analyzer, external-access findings, org-wide from the Audit account

- Register `access-analyzer.amazonaws.com` with the Audit account as delegated administrator from
  Management, then create the **organization-level external-access analyzer** in Audit, in `us-west-2`.
- **These findings are free**, so they follow the preventive rule rather than the detective one — and
  they catch exactly the class of mistake Stages 2 and 3 create: a bucket policy or a role trust policy
  that grants to a principal outside the organization. AWS also names them as the thing to read *before*
  attaching RCPs, which is a second reason they come before Stage 1c is repeated in code at Stage 2.
- **Unused-access findings are the paid half and stay in Stage 12.**

#### 8.3 — Do here: an alarm on membership changes to Control Tower's own groups (D33), which D34 promotes from prudent to load-bearing

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

#### 8.4 — Deliberately not here

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


---

## Deliverables of 1b

Each one is written so that its output differs between working and broken (Lesson 13):

- **SSO login works and the group path is real:** `aws sts get-caller-identity --profile awsds-infra-sandbox`
  returns the Sandbox account ID, and the same for every other profile from step 5.
- **The delegation took effect:** `aws sso-admin list-instances --profile awsds-infra-identity` returns the
  Identity Center instance — from the *Identity* account, which is what makes it evidence about the
  delegation rather than about Identity Center existing.
- **The membership alarm is a control and not a hypothesis:** it fired once, on both channels, on a
  deliberate add-and-remove.

## Decisions due while executing

**Blocking questions for the user: none.** One decision is *made* during this stage, and it has to be
written into `log/stage-01b-identity-and-controls.md` rather than left to whoever is at the keyboard
(Lesson 16):

| # | Decision | Step | Reversible? |
|---|---|---|---|
| 2 | The name of this project's administrator permission set — `AdministratorAccess` as `ORGANIZATION.md` states, or a rename propagated in the same session | 3.2 | Yes, but it touches three other files |

*The numbering is the landing zone's, not this file's: decisions 1, 5 and 6 are made in
[Stage 1c](stage-01c-preventive-policies.md), and 3 and 4 in
[Stage 1d](stage-01d-org-wide-enablement.md).*

## Risks

- **Step 1's delegation widens the Identity account's blast radius before step 8's alarm exists.** Keep the
  two in the same session. This is the constraint that decided the split: step 8 belongs with step 1, not
  with the org-wide work it otherwise resembles.
- **Nothing here is torn down between sessions** — everything 1b creates is `[P]` (D11). Account e-mails
  cannot be reused after an account is closed (a closed account holds its e-mail for 90 days), which is
  exactly why D11 keeps accounts in the persistent layer. The same is true of 1c and 1d.

## Verifications to answer while executing

Each is stated in its step; the list is the index, not a second copy. Record every answer in
`log/stage-01b-identity-and-controls.md`, including the ones that come out fine. **The numerals are the
landing zone's** — iii, iv, v, vii and viii are asked in Stages 1c and 1d.

| # | Question | Step |
|---|---|---|
| i | Does the Identity Center delegation coexist with the landing zone without raising drift? | 1 |
| ii | Are Management-targeted assignments the *only* thing the delegated administrator cannot manage? | 4 |
| vi | Does removing an Account Factory direct assignment stick, or is it re-created? | 3.8 |
| ix | Are Identity Center membership events recorded in Management's org-trail log group after the delegation, and under which of the three event sources? | 8.3 |

**Was (ix), and it does not belong to this stage:** *"does Macie's delegation enable Macie, as GuardDuty's
and Security Hub's do?"* — 8.1 defers Macie's delegation to **Stage 11**, so nothing here can answer it.
It is recorded in 8.1's table as the thing to check *there*.

---

*Stage index: [plan/stages/INDEX.md](INDEX.md) · Next: [Stage 1c](stage-01c-preventive-policies.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
