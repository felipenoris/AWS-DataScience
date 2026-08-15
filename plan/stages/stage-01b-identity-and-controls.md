# Stage 1b — Identity Center, permission sets, and the alarm above them

| | |
|---|---|
| **Status** | **DONE** — closed 2026-08-12 (8.3, 1, 2, 3, 4, 5, 5.1, 6, 8.2). Verifications (i), (ii), (a) and (ix) answered; **(vi) is open by construction** and is re-checked at the next landing-zone update, account update or Account Factory re-enrollment, not on a schedule |
| **Prerequisites** | Stage 1a complete, bar the deferred `Staging` vend. **Steps 3, 5 and 6 skip their `Staging` items**; the full list of what the deferral owes, across every stage, is in [Stage 1a](stage-01a-landing-zone.md) ("What the deferral leaves owed") and is worked at the vend rather than remembered here |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D14](../decisions/D14-supply-chain-account.md), [D16](../decisions/D16-break-glass.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D29](../decisions/D29-policy-canary.md), [D30](../decisions/D30-scp-recovery.md), [D31](../decisions/D31-approver-read.md), [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | Nothing cross-account; this stage is what makes every later stage reachable. Step 5's profiles are the precondition for **Stage 1c**, **Stage 1d** and everything from Stage 2 onwards |
| **Log** | [`log/log-stage-01b-identity-and-controls.md`](../../log/log-stage-01b-identity-and-controls.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

**Was "do not lose it", now settled: 1a step 2's budget alert thresholds (50/80/100%) and Cost Anomaly
Detection are deliberately skipped** (user, 2026-08-09). They are not pending work and are not to be picked
up in passing here, or in 1c or 1d. **The USD 50 budget therefore notifies nobody**: the ceiling is a number
read from the console, so the cost control of D12 is now the operator's own habit of looking — which is an
intention, not a control (Lesson 5). `plan/cost-model.md` names the exposure this leaves standing (a
forgotten `egress/` day at ~USD 4.08), and D12 carries the revision trigger.

---

**Step numbers are identifiers, not an order — and they run 1-6 and 8 here, plus 5.1.** The landing zone's
second half was one stage until 2026-08-09 and is now three (1b, 1c, 1d), split along the sessions it
already described. **The step numbers did not change in the split**, so `Stage 1c step 7` and
`Stage 1d step 9` are the same steps every other file already references; only the stage prefix moved.
**5.1 is the one number added since** — an action step 3.8 already described but no step performed. Step 7 is
[Stage 1c](stage-01c-preventive-policies.md); steps 9, 10 and 11 are
[Stage 1d](stage-01d-org-wide-enablement.md).

Everything here is fast, reversible and iterative. **Nothing in this stage is irreversible** — that
property belongs to Stage 1c's step 7 and Stage 1d's step 9, which is the reason they are separate stages
rather than the tail of this one.

## The stage at a glance

**The step numbers are identifiers and the `Order` column is the sequence.** They differ in two places, and
both differences are the point rather than an accident: 8.3 runs *first* and 5.1 is an action step 3
describes but does not perform. Read this table to plan a session; read the step for how to do it.
**The `Consumes` column is per step** — executing step 5 does not require reading sixteen decision files.

| Order | # | What | Identity | Consumes | Why it is where it is |
|---|---|---|---|---|---|
| 1 | **8.3** | The alarm on Identity Center membership and assignment changes — unfiltered | CT Admin @ Management | D33, D34 | **Before step 1, not beside it.** It is the only control over the blast radius step 1 creates, and it depends on nothing in this stage — the groups it watches are Control Tower's and exist since 1a |
| 2 | 1 | Delegate Identity Center to the Identity account | CT Admin @ Management | D10, D33 | Everything in 2-4 is done *from* Identity |
| 3 | 2 | Users and groups, beside Control Tower's | Infra user @ Identity | D32, D33, D34, D35 | Its first membership edit is what fires the alarm built in 8.3 |
| 4 | 3 | **One** permission set — the administrator — and its assignments | Infra user @ Identity | to execute: D16, D29, D32 · to *specify* the other six (3.4-3.7): D14, D18, D19, D20, D21, D22, D31 | The other six are specified here and **created in Stage 2 step 5**, in code (3.9) |
| 5 | 4 | Confirm no persona reaches Management | Infra user @ Identity | D34 | Closes the assignment path 8.3 then watches |
| 6 | 5 | Local `aws configure sso` profiles | Infra user, laptop | D29 | **Stages 1c, 1d and 2 cannot start without a member-account profile.** It depends on nothing above it — see the note in step 5 |
| 7 | **5.1** | Retire the Account Factory direct assignments, or record that they cannot be | **CT Admin @ Management** + Infra user's laptop | D32 | Described in 3.8, performed here, because it is only safe once the group path is proven **and** it invalidates the profiles step 5 just wrote. **Not executable from Identity** — measured 2026-08-12, see the step |
| 8 | 6 | AZ name→ID mapping per account | Infra user, laptop | D14, D20, D21 | Stage 3 anchors subnets on the answer |
| 9 | 8.2 | IAM Access Analyzer, org-wide from Audit | CT Admin @ Management / Audit | D33, D34 | Free, and it catches what Stages 2-3 create. Nothing else waits on it |

**Sessions.** Orders 1-7 are one sitting and are the bootstrap: nothing in this stage or the three that
follow is reachable without a profile. Orders 8 and 9 are independent of everything else and of each other.

**Why 8.3 moved to the front, since the previous version of this file solved the same problem differently.**
It used to say "keep step 1 and step 8 in the same session", which is an intention rather than a control
(Lesson 5) — the window between them is exactly the interval in which the widened blast radius is
unobserved, and nothing enforces its length. 8.3 has no dependency on steps 1-6: the groups it watches were
created by Control Tower in 1a, and the metric filter goes on the Management account's org-trail log group,
which 1a step 5 already used. Building it first closes the window by construction instead of by discipline,
and it makes step 2 the alarm's test rather than requiring a deliberate edit to `AWSControlTowerAdmins`.

## Who executes what

**Every manual step names the identity that performs it, not only what it does** (Lesson 17). **Two
identities do all of it, through four sign-in paths** — and it is the *path* that is easy to get
wrong, which is how a step stalls on an `AccessDenied` that looks like a policy bug. 5.1 is the step that
proved the point: it was written against the wrong path and stalled on exactly that `AccessDenied`.

| Steps | Identity | Sign-in path |
|---|---|---|
| 8.3 (the metric filter and the alarm), 1 and 8.1 (delegations) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 8.2 (creating the analyzer *in Audit*) | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Audit** — the infrastructure user has *no* assignment there (`ORGANIZATION.md`) |
| **5.1's removals** | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Management**. **This row is a correction**, measured 2026-08-12: the removals are *not* performable from Identity by any principal there — see 5.1 |
| 2, 3, 4 | **Infrastructure user** | access portal → `AWSAdministratorAccess` on **Identity** (the direct Account Factory assignment from 1a step 4 — this is what bootstraps the whole stage) |
| 5, 5.1's re-check, 6 | **Infrastructure user**, from the laptop | the `awsds-infra-*` and `awsds-policy-canary` profiles created in step 5 |

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

**Do not start this step until 8.3's alarm exists and has been seen to work.** That is the ordering in the
table above, and it is the whole reason the alarm is in this stage rather than in Stage 1d.

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
  concrete rather than theoretical, and because **8.3's alarm — already built, one step earlier — is the
  only control over it**.
  **And it widens once more, one stage from here:** this delegation reaches Identity Center only. The
  SCPs, RCPs and tag policies written in **Stage 1c** are AWS Organizations objects and stay console-managed
  until **Stage 2 step 5.1 (INT-20)** adds a *second*, different delegation — a resource-based policy on
  the organization — after which the Identity account can also edit organization policy, Control Tower's
  guardrails included. Nothing to do about it here; the point is that 8.3's alarm is the control above
  both delegations, so it is worth building well rather than quickly.
- **Verify while executing (i):** that the delegation coexists with the landing zone without raising
  Control Tower drift. Control Tower's handling of Identity Center has changed more than once. Record
  the answer in `log/log-stage-01b-identity-and-controls.md`.


### Step 2 — Create this project's users and groups in IAM Identity Center — beside Control Tower's, never inside them

- **Pre-flight:** `secrets/emails.md` must carry an address for every user created here. An Identity Center user cannot be created without one, so re-check *before* starting rather
  than half-way through.
- **Enumerate before creating anything. This step does not start from an empty directory, and it was
  written as if it did.** Enabling Control Tower in 1a step 3 created the Identity Center directory *and
  populated it*: Control Tower's own groups (`AWSAccountFactory`, `AWSControlTowerAdmins`, the auditor
  and per-account administrator groups), its own permission sets, and a first administrator. List what is
  there, then treat the two sets as separate — Control Tower owns its objects and may re-create them;
  this stage owns the five groups below.
- **Create four users, not five (D32).** The infrastructure user already exists: Account Factory created
  it in 1a step 4 from the `SSOUserEmail` field, and it already holds a direct administrator assignment
  on every vended account. The only thing to do about it here is **put it in the `sso-group-infrastructure`
  group**. Re-creating it under a second address gives one human two administrators, one of which nobody
  is watching.
- **Create five groups:** `sso-group-infrastructure`, `sso-group-data-scientists`, `sso-group-deployment-managers`,
  `sso-group-governance-managers`, `sso-group-dev-env-stewards`.
- **One group per business unit is deferred, deliberately (D35).** `Sandbox` is one account per business
  unit and N is 1, so **create `sso-group-data-scientists` and no per-unit group today**. What this step fixes now
  is that the *assignment list* in step 3 keeps the Sandbox row separable from the Development row, so
  the second unit is an addition (`sso-group-data-scientists-<bu>` covering that unit's Sandbox alone) and not a
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
  `sso-group-data-scientists`** — or plus `sso-group-infrastructure`, which is the instance that matters most and the one the
  tables hide. The approver groups were a single `managers` group until 2026-08-08 and have been split
  twice since, each time along a different axis: release (lifecycle), data access (ownership), runtime
  image (supply chain). The reason is cumulative and it is the whole point: one persona holding all of
  them means a single human can write a job that reads restricted data, approve its release, approve its
  access to that data, **and** approve the runtime image the job was written on — four acts, one
  signature. Nothing in AWS will warn you.


### Step 3 — Create the administrator permission set, and specify the other six

**This step creates one permission set and specifies seven.** The six that are not the administrator are
**written in code, in Stage 2 step 5**, and are never typed into a console — 3.9 carries the reasoning and
it is the substantive change of the 2026-08-09 revision. What stays here is the *design*: 3.1 to 3.7 are
the design of record for all seven sets, and Stage 2 step 5.2 points back at this section rather than
restating it.

#### 3.1 — The seven sets, stated up front rather than discovered paragraph by paragraph

An earlier
version of this step named three in its first line and introduced four more further down, which is how a
set gets missed.

| Permission set | Group | Assigned on | Created | Shape |
|---|---|---|---|---|
| `InfrastructureAccess` | `sso-group-infrastructure` | Sandbox, Development, Data Governance, Staging*, Production, Identity | **Here, by hand** | The builder. The one named exception to "nothing gets `AdministratorAccess`" (`plan/conventions.md`) — it is the one set that attaches it |
| `DataScientistAccess` | `sso-group-data-scientists` | Sandbox **and** Development (D21) | Stage 2 step 5 | Studio use, scratch/derived read-write, Athena, ECR pull. **Not** `PowerUserAccess`, **not** `AmazonSageMakerFullAccess` |
| `DataScientistStagingAccess` | `sso-group-data-scientists` | Staging* (D20) | Stage 2 step 5 | Read-only, no write of any kind, not even a drop-box |
| `DataScientistProdAccess` | `sso-group-data-scientists` | Production (D18) | Stage 2 step 5 | Data plane read, no compute, no control plane |
| `DeploymentManagerAccess` | `sso-group-deployment-managers` | Sandbox, Development, Staging*, Production (D31) | Stage 2 step 5 | Diagnosis, not reading. **Nothing on Data Governance** |
| `GovernanceManagerAccess` | `sso-group-governance-managers` | **Data Governance only** | Stage 2 step 5 | The catalog, never the rows |
| `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | Production + read-only on Sandbox and Development | Stage 2 step 5 | The artifact, never the data |

\* **Skip every `Staging` cell until the account is vended** (the prerequisites row). Nothing before
Stage 8 needs it.

**The five groups are still created here, in step 2, and that is not an inconsistency — it is the seam.**
A group and a group membership are *person-shaped*: in a real environment they arrive from the corporate
IdP over SCIM, and the number of them grows with the number of people. A permission set and its assignment
are *entitlement-shaped*: their number is fixed by the design, not by headcount. So the directory objects
stay outside Terraform and the entitlements go into it, with the assignment resolving its group **by
display name** rather than by GUID (`plan/conventions.md`, "The identity seam"). Nothing here changes if
the directory is later replaced.

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

#### 3.2 — The name collision, settled before creating anything, because its failure mode is silent

**The name is `InfrastructureAccess`** — decided 2026-08-10, before execution, and already propagated. It is
not a choice left at the keyboard (Lesson 16); it is recorded here because the *reason* is what the step has
to carry into the console.

Control Tower already created a permission set called **`AWSAdministratorAccess`**. The set created here was
going to be called `AdministratorAccess` — two objects four characters apart, both granting administrator,
one owned by Control Tower and one by this project. **An assignment made against the wrong one still works,
so nothing reports it.** Three things decided the rename:

- **It degrades the one check standing in front of the only dangerous act in this stage.** Step 5's evidence
  and step 5.1's precondition are both "read the ARN and tell which set it is".
  `AWSReservedSSO_InfrastructureAccess_*` next to `AWSReservedSSO_AWSAdministratorAccess_*` is a difference
  you cannot miss; `AWSReservedSSO_AdministratorAccess_*` next to it is a prefix nobody reads carefully, at
  the moment they are about to remove the assignment that is known to work (Lesson 13).
- **It restores the shape the other six sets already follow** — `<Persona>Access` — so the administrator set
  stops being the only one named after a *permission level* rather than a group. `plan/conventions.md` asks
  for its exception to be read narrowly, covering one group; a name that says `Administrator` invites the
  opposite reading.
- **The collision had already produced drift in prose, before the object existed.** `ORGANIZATION.md`'s
  access table and D29 both said this project's set was the one on `Policy Canary`, where 3.1, step 5 and
  D32 say it is Control Tower's. Both were corrected in the same pass.

Two rules survive the rename and are the reason it was cheap now and would not have been later:

- **Never edit or reuse Control Tower's set.** It is theirs, and a landing-zone update may reset it.
- **`AWSAdministratorAccess` is still what every Account Factory direct assignment points at** (D32), and
  what `awsds-policy-canary` is bound to permanently (3.1). The rename removes the ambiguity, not the second
  set — both exist throughout this stage, and the whole of 5.1 is about telling them apart.

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

**The boundary carries a mechanical constraint that decides where it can be declared**, and it is the one
thing in this section that cannot be settled by writing a policy document. A boundary attached to a
permission set (`aws_ssoadmin_permissions_boundary_attachment`) is either an AWS-managed policy or a
**customer-managed** one referenced *by name* — and a customer-managed reference requires an IAM policy
with that name and path to exist **in every account the permission set is provisioned into**. Miss one and
provisioning fails there, in an account nobody is looking at. Those `aws_iam_policy` objects belong to each
account's own `foundation/` slice: a different state, a different profile, a different apply — and one more
copy per business unit (D35). So it is a cross-slice ordering dependency, not a policy choice, and
**Stage 2 step 5 carries it as a decision row** rather than leaving it to be discovered by a failed
provisioning.

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

- **`sso-group-data-scientists` has no assignment of any kind on Data Governance** (D18/D22). The lake is read from
  Sandbox and Development through the Lake Formation share.
- **`sso-group-deployment-managers` has nothing on Data Governance** — a release approver has no business in the
  account that grants data access. `sso-group-governance-managers` is the mirror image: the one account the
  deployment manager cannot enter is the only one they can.
- **`sso-group-dev-env-stewards` has nothing on Staging, Data Governance, Identity, Audit, Log Archive or Policy
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

- **Remove none of them until the group path is proven end to end** — `sso-group-infrastructure` →
  `InfrastructureAccess` → an actual `aws sts get-caller-identity` under each profile in step 5. Removing
  them first is the cheapest way to lock the only administrator out of an account whose sole remaining
  recovery path is the Management root (D16; D30 reverted). **So the removal is not performed here: it is
  [step 5.1](#step-51--retire-the-account-factory-direct-assignments-or-record-that-they-cannot-be),
  and it has a step number for a reason.** An earlier version of this file described the removal in this
  subsection and told the reader to do it "after step 5" — an action with no step, no identity and no place
  in any table, which is the shape of something that gets done at the wrong moment or not at all.
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

#### 3.9 — Why *one* set is by hand, and the other six are not

The old version of this
subsection read: *"Terraform cannot run before SSO login works. Stage 2 moves all of it into
`terraform-live/identity/sso/` and imports it."* Both sentences are true and the conclusion does not
follow from them. Terraform cannot run before **an administrator can sign in**; that justifies one group
and one permission set, not seven — and the other six then get typed into a console and immediately
re-expressed in code, with Stage 2 step 5.5 demanding that the second expression match the first byte for
byte. That is the same work done twice with a gate in the middle designed to fail on JSON whitespace.

- **Nothing between here and Stage 5 needs the other six.** The "Who executes what" table of this stage and
  of 1c, 1d and 2 contains exactly two identities — `AWS Control Tower Admin` and the infrastructure user.
  The data scientist's first sign-in is Stage 6, the governance manager's is Stage 6, and the two GitLab
  approvers consume no AWS permission at all until they diagnose something (Stage 8).
- **So they are authored in `terraform-live/identity/sso/` at Stage 2 step 5, created rather than
  imported.** The design of record is 3.1-3.7 above; Stage 2 references it and does not restate it.
- **What is still imported is small and deliberate:** the `InfrastructureAccess` set created here and its
  assignments. That keeps the whole entitlement plane in code — an artefact nobody owns is worse than an
  artefact somebody owns badly (Lesson 5) — and it exercises the import mechanism on objects whose worst
  failure is that a person cannot sign in, which is exactly the argument Stage 2 step 5.5 already makes for
  doing `sso/` before `org-policies/`.
- **Why the administrator set is not authored in code with the rest, which is the mirror-image question.**
  It is the credential the code applies *as*. A permission set whose only source is the state file that
  needs it to be applied is a cycle, and the Account Factory direct assignments (3.8) are the only thing
  standing behind it until 5.1 proves otherwise. Author it by hand, import it, keep the direct assignments
  until 5.1 says they can go.


### Step 4 — No project persona holds an assignment on the Management account — the infrastructure user included

- **This step used to create one**, and it contradicted the reason `AWS Control Tower Admin` is kept
  standing at all: the Management-account work is *its* job, and what D34 buys is precisely that the
  infrastructure user gains no standing reach there. Principle 1 says the same from the other side —
  Management is bootstrap-only and console-only, Terraform never runs against it, so there is nothing for
  an `awsds-infra-*` profile to do. Step 3's assignment list already omits it; this step now says so
  deliberately rather than by omission, which is the difference between a decision and an oversight.
- **Keep the mechanical fact the old step carried, because it is true and it bites at 8.3:** the
  delegated administrator **cannot manage assignments targeting the Management account** — those can only
  be created from Management itself. That is a constraint on *creating an assignment*, and it is **not** a
  constraint on group membership: `AWSControlTowerAdmins` already carries `AWSAdministratorAccess` on
  Management, created by the landing zone, and step 1 records that the delegated administrator can edit
  who is in it. **So the preventive path into Management is closed and the membership path is not** —
  which is why 8.3's alarm — built before any of this — is the control rather than a nicety.
- **Verify while executing (ii):** that the restriction is exactly as described — that assignments
  targeting the Management account are the *only* thing the delegated administrator cannot manage.


### Step 5 — Configure the local SSO profiles now, not at the end of the stage

- **Do:** `aws configure sso` for `awsds-infra-sandbox-1`, `awsds-infra-dev`, `awsds-infra-prod`,
  `awsds-infra-data` and `awsds-infra-identity` — plus one more that is deliberately named differently,
  **`awsds-policy-canary`** (D29). `awsds-infra-staging` waits for the vend.
  **The sandbox profile carries an ordinal and the other four do not** (`plan/conventions.md`, settled
  2026-08-11): `Sandbox` is the one account that multiplies (D35), `-1` names the account AWS already calls
  `Sandbox Account 1`, and the second business unit gets `awsds-infra-sandbox-2`.
- **Name the permission set each profile is bound to, and write it in the log.** `aws configure sso` stores
  a `sso_role_name` in `~/.aws/config`, so a profile is bound to *one* named set, not to "whatever
  administrator access this user has". There are two administrator sets four characters apart (3.2), and
  which one a profile points at decides whether 5.1 is safe:
  - **Point every profile at this project's `InfrastructureAccess`**, reached through the `sso-group-infrastructure`
    group. That is the whole point of the group path, and it is what makes 5.1 a cleanup rather than a
    lockout.
  - **Control Tower's `AWSAdministratorAccess` — the Account Factory direct assignment — is the fallback
    to fall back *to*, not the one to configure.** A profile bound to it works today and stops working the
    moment 5.1 removes the assignment behind it.
  - `awsds-policy-canary` is the exception and has no choice: that account has only the direct
    assignment (3.1), so its profile is bound to `AWSAdministratorAccess` permanently. Record it, so the
    asymmetry reads as a decision rather than as a slip.
- **Why the canary profile is not an `awsds-infra-*`:** `Policy Canary` is not a Terraform-managed
  account and nothing is ever applied into it. The profile exists only to run Stage 1c's test battery, and
  the naming keeps that visible in shell history.
- **Verify:** `aws sts get-caller-identity --profile <each>` returns the expected account ID **and an
  assumed-role ARN naming the set the profile was bound to** — the ARN is the evidence, the account ID
  alone is not (Lesson 13: an `AWSReservedSSO_AWSAdministratorAccess_*` ARN and an
  `AWSReservedSSO_InfrastructureAccess_*` ARN both "work", and only the second means the group path
  resolved). The 3.2 rename makes that a glance rather than a careful read; it does not remove the need
  to look.
- **This step depends on nothing above it, which the previous version of this file did not say.** The
  Account Factory direct assignments exist since 1a step 4, so `aws configure sso` works before the
  delegation, before the groups and before the permission sets — bound to `AWSAdministratorAccess`. That
  is worth knowing for one reason: if anything in steps 1-4 goes wrong, the way back in is already
  configured. What the *ordering* buys is that the profiles written here are the ones the rest of the
  project uses, bound to the set the group path provides.
- **It used to be the second-to-last step and that was an ordering bug.** Every step below this one,
  and everything in Stages 1c, 1d and 2, does CLI or console work *inside a member account* — the
  `Policy Canary` battery, restricting the Config recorder, enabling Object Lock on the Log Archive
  bucket, raising the Lake Formation cross-account version in Data Governance, reading AZ IDs per
  account — and none of it is reachable without a profile.


### Step 5.1 — Retire the Account Factory direct assignments, or record that they cannot be

**A step of its own since 2026-08-09.** 3.8 describes these assignments and used to describe their removal
as something to do "after step 5" — an action with no number, no identity and no row in any table. It has
both now, because it is the one act in this stage that can lock the only administrator out of an account.

- **Precondition, and it is not the same as "step 5 is finished":** every profile from step 5 has returned
  an assumed-role ARN naming **this project's** `InfrastructureAccess`. That is the proof that
  `sso-group-infrastructure` → `InfrastructureAccess` → the account actually resolves. A profile still bound to
  `AWSAdministratorAccess` means the group path is untested in that account, and removing the direct
  assignment there is removing the only thing that is known to work.
- **Do it as `AWS Control Tower Admin` on the Management account, not from Identity** — measured
  2026-08-12, after the step stalled on an `AccessDenied` that the "Who executes what" table had
  mispredicted. **The delegated administrator cannot alter a permission set that is provisioned into the
  management account** (IAM Identity Center User Guide, "Delegated administration"), and Control Tower's
  `AWSAdministratorAccess` is provisioned there — it is what `AWSControlTowerAdmins` holds on Management.
  The protection is anchored on the **permission set** ARN rather than on the target account, so it reaches
  that set's assignments in *every* account, not only Management's. Both principals available in Identity
  were tried and both were denied, which is the part worth carrying: this is not fixable by choosing a
  different permission set in Identity, because it is not a property of the caller.
  - **It is a second, distinct boundary from the one step 4 measured, and the two are told apart by the
    error text.** Step 4's denial named `arn:aws:sso:::account/<MGMT_ID>` **with an explicit deny in a
    resource-based policy** — scoped by *target account*. This one names
    `arn:aws:sso:::permissionSet/<...>` with **no** explicit-deny clause — an implicit deny against a
    principal holding `AdministratorAccess`, scoped by *permission set*. Step 4 recorded that its probe
    could not tell whether Management-targeted assignments were the only thing out of reach and answered
    "no, not the only thing" on expectation; this is the measurement behind that answer.
  - **`InfrastructureAccess` is not provisioned into Management and is therefore outside this
    restriction** — so the delegated administrator keeps full control of the set Stage 2 step 5 imports and
    manages from `awsds-infra-identity`. Stated here because the `AccessDenied` above is exactly the
    evidence that would otherwise put that in doubt.
- **Do:** remove the direct user assignment of `AWSAdministratorAccess` from Sandbox, Development,
  Production, Data Governance and — **last, and only if the four others survived it** — Identity. The
  Identity account's assignment is what bootstrapped this whole stage; it is the last one to touch and the
  first one to restore. **Executing from Management removes the self-lockout hazard but not the ordering
  rule:** the reason Identity goes last is that each removal is a claim that the group path carries that
  account, and the claim is cheapest to withdraw while the bootstrap is still standing.
- **Never `Policy Canary`** (3.8). Its direct assignment is the only way into the account and it is
  permanent.
- **Then re-check, don't assume:** `aws sts get-caller-identity --profile <each>` again, after the
  removal. If a profile was bound to the set that was just removed, it fails here — which is the cheap
  version of that discovery, and the reason this step is not the last thing done in a session.
- **This is where verification (vi) is *opened*, and it cannot be closed here.** The question is whether
  the removal sticks, and the events that could undo it — a landing-zone update, an account update, a
  re-enrollment — are all in the future at the moment 5.1 runs. So the honest record is "removed on
  &lt;date&gt;, not re-created as of that date", plus the named event to re-check under. **Writing (vi) down
  as answered on the strength of the removal succeeding is the failure this bullet exists to prevent**: it
  reads as evidence and is only a timestamp. If the assignments do come back, stop removing them and record
  the direct assignment as a **permanent property of an Account Factory-vended account**, in
  `log/log-stage-01b-identity-and-controls.md` and in D32. Stage 2 step 5.2 then models nothing about them,
  which is already what it says.
- **Reversible**, and cheaply: the assignment can be re-created from the Identity account. It is a
  separate step because the *sequence* is what is dangerous, not the operation.


### Step 6 — Check the AZ name-to-ID mapping — **DONE 2026-08-12**

- **Do**, under each of `awsds-infra-sandbox-1`, `awsds-infra-dev` and `awsds-infra-prod`:
  `aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'`. **Now scripted** as
  [`aws/AZs.sh`](../../aws/INDEX.md), which runs every `awsds-*` profile and compares them — written during
  this step so the check survives each future vend as a re-run rather than as a remembered command.
- **Why it has a bill attached.** AWS maps AZ names to physical datacenters independently per account, so
  `data.aws_availability_zones` indexed by position can place "the same" AZ in different datacenters.
  D14 and D21 make this concrete: both peerings into Production are free within an AZ and USD 0.01/GB
  each way across AZs, and the VPN, SageMaker and GitLab talk across them constantly.
- **Staging and every future Sandbox get the same check when they are vended** — the *cost* argument does
  not apply to Staging (D20 leaves it unpeered), but Stage 3 anchors its subnets the same way, so the
  mapping has to be on record before it writes one.
- **Outcome: every measured account is identical, and Stage 3 anchors on `zone_id` anyway.** The full
  table is in `log/log-stage-01b-identity-and-controls.md`. This step used to end "*if* the mappings differ,
  anchor on `zone_ids`" — **the conditional was the wrong shape**, and saying so is the point worth keeping:
  the measurement covers only the accounts that exist, while `Staging` is unvended and D35 plus Stage 14
  multiply Sandboxes, each getting its own mapping at vend time. A rule that holds only while the account
  set is frozen is not a rule (Lesson 5), and the failure it would allow is silent — cross-AZ transfer, no
  error. `plan/architecture.md` §4.1 carries the reasoning; `plan/open-questions.md` item 3 is closed on it.


### Step 8 — Security delegation, the free detective control, and the alarm that has no preventive control above it

Principle 9, as amended 2026-08-08.

**Its two halves are executed at opposite ends of the stage, and the number does not say so.** 8.3 is the
**first** thing done in this stage — before step 1 — and 8.2 is the last, or a session of its own. Nothing
depends on 8.2; everything after step 1 depends on 8.3 existing. The at-a-glance table is the order.

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

#### 8.3 — Do **first**: an alarm on Identity Center membership and assignment changes (D33), which D34 promotes from prudent to load-bearing

**This is the first thing executed in Stage 1b**, before the delegation of step 1 — see the at-a-glance
table. It depends on nothing else in the stage: the groups it watches are Control Tower's, they exist since
1a, and the log group it reads is the one 1a step 5 already used.

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
  - **Do not filter by group. Match the six events above and nothing else** — settled 2026-08-09, and it
    is the choice this project makes rather than an option left at the keyboard (Lesson 16). The
    alternative was to key the pattern on each group's `groupId`, resolved once through
    `aws sso-admin list-instances` and `aws identitystore list-groups`. Three reasons it lost:
    - **Precision buys nothing at this size.** The whole directory holds six identities and five project
      groups. Every membership change in it is worth a notification; there is no class of edit this alarm
      *should* ignore.
    - **A filter keyed on a GUID is a filter with a hidden expiry.** Those IDs are properties of *this*
      directory instance. Replace the identity source — the move a real deployment makes the day it
      federates to a corporate IdP — and the groups are re-created with new IDs, leaving a pattern that
      matches nothing and an alarm that looks healthy (Lesson 13). CloudTrail's Identity Center payloads
      already changed once, in January 2025, in exactly the fields a name-based filter would have keyed on.
    - **The failure modes are not symmetric.** A noisy alarm is read and tuned; a silent one is trusted.
    **This inverts at scale, and that is written down rather than left implicit:** with hundreds of data
    scientists arriving through SCIM, an unfiltered alarm fires on every onboarding and is muted within a
    fortnight — which is worse than not having it. `plan/institutional-delta.md` carries the row, and the
    revision trigger is the arrival of an external identity source, not a headcount.
  - Namespace `AWSDS/Security`, its own metric name, metric value `1`, **`Default value` left empty** —
    a custom metric is USD 0.30/metric-month and is metered only in the hours it publishes.
  - Alarm: Sum, 1 minute, `≥ 1`, **missing data `notBreaching`** (the price of the empty default value),
    delivering to `awsds-org-break-glass-alerts` — the same SNS topic as the break-glass alarm, which is
    already confirmed on both channels.
  - **What "do not filter" costs in practice, which is less than it sounds.** Step 2 and step 3 generate a
    burst of these events, and so does Stage 2's first apply of `identity/sso/`. A CloudWatch alarm
    notifies on a **state transition**, not per datapoint, so a burst produces one notification and one
    later return to OK — not one per assignment. The cost of the choice is a handful of expected
    notifications at three known moments, all of them in this plan.
  - **Verify while executing (ix), and it can only be answered after step 1:** which account the events
    land in, and under which of the three event sources above. The filter is built here, while the
    directory is still administered from Management; the delegation then moves that administration to the
    Identity account, and **step 2's first group edit is the first event that answers the question**. If
    the events turn out to be recorded only in the Identity account, keep a filter there instead and point
    it at the same topic cross-account. Record which it was.
  - **Expect the alarm to fire minutes late, and do not treat that as a failure.** The path is
    CloudTrail → S3 → CloudWatch Logs → metric filter → alarm, so single-digit minutes of delay is normal
    for a detective control of this shape. It is why 1a's break-glass alarm is built the same way.
- **The test is step 2, not a contrived edit.** An untested alarm is a hypothesis (1a step 5 makes the same
  point about the same topic) — and because this alarm is built *before* the rest of the stage, putting the
  infrastructure user into the `sso-group-infrastructure` group is a real membership change that must produce a real
  notification. If step 2 completes and nothing arrives, stop: the alarm is not a control, and step 1 has
  already widened what it was supposed to be watching. The old instruction here was to add and remove a
  member of `AWSControlTowerAdmins` deliberately — a live edit to the most dangerous group in the
  organization, performed to test the thing that watches it. Ordering the stage properly removes the need
  for it.

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

- **SSO login works and the group path is real:** `aws sts get-caller-identity --profile awsds-infra-sandbox-1`
  returns the Sandbox account ID **and an ARN containing
  `AWSReservedSSO_InfrastructureAccess`** — this project's set, reached through the `sso-group-infrastructure` group —
  and the same for every other `awsds-infra-*` profile. The account ID alone proves only that *an*
  administrator assignment exists, which was already true before this stage started.
- **The delegation took effect:** `aws sso-admin list-instances --profile awsds-infra-identity` returns the
  Identity Center instance — from the *Identity* account, which is what makes it evidence about the
  delegation rather than about Identity Center existing.
- **The membership alarm is a control and not a hypothesis:** step 2's first group edit produced a
  notification on both channels, minutes later — with the alarm already in place *before* step 1 widened
  what it watches.
- **The direct assignments are settled either way** (5.1): removed and the profiles still work, or recorded
  as a permanent property of a vended account with D32 amended. What is not acceptable is not knowing.

## Decisions due while executing

**Blocking questions for the user: none — and since 2026-08-10, no decision is left to be made here
either.** The one decision this stage carried was settled *before* execution rather than at the keyboard,
which is Lesson 16 being applied rather than restated:

| # | Decision | Step | Settled |
|---|---|---|---|
| 2 | The name of this project's administrator permission set | 3.2 | **`InfrastructureAccess`**, 2026-08-10, propagated in the same session to `ORGANIZATION.md`, `plan/conventions.md`, D29, D32, Stages 1a, 1c, 1d, 2 and 4. The reasoning is in 3.2; the naming rule it produced is in `plan/conventions.md` |

**What is still owed to the log:** that the set was in fact created under that name, and the
`AWSReservedSSO_InfrastructureAccess_*` ARNs step 5 returns. A decision recorded in the plan and not
matched by the object in the console is the failure this table exists to prevent.

*The numbering is the landing zone's, not this file's: decisions 1, 5 and 6 are made in
[Stage 1c](stage-01c-preventive-policies.md), and 3 and 4 in
[Stage 1d](stage-01d-org-wide-enablement.md).*

## Risks

- **Step 1's delegation widens the Identity account's blast radius, and 8.3's alarm is the only thing above
  it.** The ordering — 8.3 first, then step 1 — is what makes that a control rather than a promise; the
  previous version of this file asked for the two to be in "the same session", which bounds nothing. This is
  also the constraint that decided the split: 8.3 belongs with step 1, not with the org-wide work it
  otherwise resembles.
- **5.1 is the one act here that can lock an administrator out of an account.** It is reversible from the
  Identity account, and it is safe only in the order the step states: profiles proven against this project's
  set first, Identity account last.
- **Nothing here is torn down between sessions** — everything 1b creates is `[P]` (D11). Account e-mails
  cannot be reused after an account is closed (a closed account holds its e-mail for 90 days), which is
  exactly why D11 keeps accounts in the persistent layer. The same is true of 1c and 1d.

## Verifications to answer while executing

Each is stated in its step; the list is the index, not a second copy. Record every answer in
`log/log-stage-01b-identity-and-controls.md`, including the ones that come out fine. **The numerals are the
landing zone's** — iii, iv, v, vii and viii are asked in Stages 1c and 1d.

| # | Question | Step |
|---|---|---|
| i | Does the Identity Center delegation coexist with the landing zone without raising drift? | 1 |
| ii | Are Management-targeted assignments the *only* thing the delegated administrator cannot manage? | 4 asks it; **5.1 answers it: no** — a permission set provisioned into Management is out of reach in every account |
| vi | Does removing an Account Factory direct assignment stick, or is it re-created? | 5.1 (described in 3.8). **Cannot be closed in-session** — it needs a landing-zone update, an account update or a re-enrollment, so 5.1 records it as provisional and names the event that settles it |
| ix | Are Identity Center membership events recorded in Management's org-trail log group after the delegation, and under which of the three event sources? | 8.3, answered by step 2 |

**Was (ix), and it does not belong to this stage:** *"does Macie's delegation enable Macie, as GuardDuty's
and Security Hub's do?"* — 8.1 defers Macie's delegation to **Stage 11**, so nothing here can answer it.
It is recorded in 8.1's table as the thing to check *there*.

---

*Stage index: [plan/stages/INDEX.md](INDEX.md) · Next: [Stage 1c](stage-01c-preventive-policies.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
