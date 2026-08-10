# Stage 1c — Preventive policies: SCP, RCP, tag and declarative

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | **[Stage 1b](stage-01b-identity-and-controls.md) complete** — step 5's profiles are what run 7.3's battery, and step 3's permission sets are what the denies are written around. `Staging` is unvended, so nothing in the `Workloads` tier can be exercised against it |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D28](../decisions/D28-workflow-contract.md), [D29](../decisions/D29-policy-canary.md), [D30](../decisions/D30-scp-recovery.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | **Constrains** [INT-12](../integrations.md), whose fallback 7.6 forbids until the policy is amended |
| **Log** | `log/stage-01c-preventive-policies.md` |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**This stage is one step, and it keeps its number: step 7.** The landing zone's second half was one stage
until 2026-08-09; the split gave step 7 a stage of its own because it is the only part of it that is
neither fast nor freely reversible, and because it wants an uninterrupted sitting. Every other file's
`Stage 1b step 7` reference is now `Stage 1c step 7` — the same step, a different prefix, and nothing else
moved. Navigate by **7.1-7.8**.

**Why it comes this early:** prevention has precedence over detection (principle 9), and a guardrail
written after the thing it guards has already been used is a guardrail that arrives late. That is the whole
argument for attaching policy over accounts that are still empty.

## Before you start — the two things this stage may not begin without

Step 7 has no in-account repair. A bad `Deny` is undone from the Management account, which is exempt from
SCPs by AWS's design (D16), and that is the *whole* recovery path since D30 was reverted. So:

1. **The Management console is open, signed in as `AWS Control Tower Admin`, before the first attach** —
   a precondition, not a precaution. If the policy you are about to attach locks you out of the account you
   attached it from, the console you needed is the one you can no longer reach.
2. **The detach command is written down before it is needed**, with the policy ID left blank to fill in:

   ```bash
   aws organizations detach-policy --policy-id <POLICY_ID> --target-id <OU_OR_ACCOUNT_ID>
   aws organizations list-policies-for-target --target-id <OU_OR_ACCOUNT_ID> --filter SERVICE_CONTROL_POLICY
   ```

   Record the ID of every policy **as you attach it**, in `log/stage-01c-preventive-policies.md`. Reading
   an ID back out of a console you have just denied yourself access to is the failure this line exists to
   prevent.

Also required, and it is the control rather than the backup: **7.3's `Policy Canary` battery runs before
anything reaches a real OU** (D29). The battery is a procedure, not a property — it only works if it is
actually done, and the break-glass chain tested in 1a is what stands behind it if it is not.

## The stage at a glance

| # | What | Identity |
|---|---|---|
| 7.1 | What makes this step different, and the two rules that survive from D30 | — (read first) |
| 7.2 | Preconditions, in this order | CT Admin @ Management |
| 7.3 | The battery, against `Policy Canary` before anything real (D29) | Infra user, laptop (`awsds-policy-canary`) |
| 7.4 | The order of attachment — an instruction, not a listing order | CT Admin @ Management; step 1 of 7.4 also in each member account |
| 7.5 | The organization-root SCP set | CT Admin @ Management |
| 7.6 | The per-OU sets, one tier per OU policy set (D23) | CT Admin @ Management |
| 7.7 | The Control Tower managed controls — use theirs | CT Admin @ Management |
| 7.8 | RCPs, tag policies, declarative policies | CT Admin @ Management |

## Who executes what

| Part | Identity | Sign-in path |
|---|---|---|
| Policy-type enablement, org-root attachments, per-OU attachments, managed controls (7.2, 7.4-7.8) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 7.4 step 1 — account-level BPA on Log Archive and Audit | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Log Archive** / **Audit** |
| 7.3 (the battery), 7.4 step 1 in the other member accounts | **Infrastructure user**, from the laptop | the `awsds-policy-canary` and `awsds-infra-*` profiles from Stage 1b step 5 |

## What this stage costs

**Nothing.** SCPs, RCPs, tag policies, declarative policies and Control Tower controls are all free. The
one cost this stage *creates* lands elsewhere: 7.8's tag-forcing SCP is paid for at Stage 6, in the time
it takes to make every creation path carry the tags.

---

## To execute

### Step 7 — Preventive policies

The one step in the landing zone that is neither fast nor freely reversible from inside a governed
account. Read all of 7.1 before attaching anything.

#### 7.1 — What makes this step different, and the two rules that survive from D30

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

#### 7.2 — Preconditions, in this order. Two of them are the reason a first attempt fails

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

#### 7.3 — The battery, run against `Policy Canary` before anything reaches a real OU (D29)

An SCP
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

#### 7.4 — The order of attachment. This is an instruction, not a listing order

Two pairs interlock, and
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

#### 7.5 — The organization-root SCP set

(hand-written; moves to `terraform-live/identity/org-policies/`
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

#### 7.6 — The per-OU sets

One tier per OU policy set (D23), on top of the root set above.

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
  not held back by anyone declining a RAM invitation: `ram:EnableSharingWithAwsOrganization` (Stage 1d step 11)
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
    exist. **Record the diff in `log/stage-01c-preventive-policies.md`** — "it used to inherit that" is
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

#### 7.7 — The Control Tower managed controls: use theirs, do not hand-roll these two

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
  record which, in `log/stage-01c-preventive-policies.md`.

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

#### 7.8 — RCPs, tag policies, declarative policies

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


---

## Deliverables of 1c

Each one is written so that its output differs between working and broken (Lesson 13):

- **The perimeter is real:** an attempt to write to an S3 bucket outside the organization is denied, **and
  the CloudTrail record for that call names an explicit deny in a service control policy.** The denial alone
  is not the deliverable; a bucket you do not own would have refused you anyway.
- **The ceiling is real in the other direction too:** `ec2:RunInstances --dry-run` in `us-east-1` returns
  `UnauthorizedOperation`, while the same call in `us-west-2` returns `DryRunOperation`.
- **Every attached policy ID is recorded** in `log/stage-01c-preventive-policies.md`, which is what makes
  the detach command above executable rather than aspirational.

## Decisions due while executing

**Blocking questions for the user: one** — 7.6 asks whether the `Interactive` OU gets a policy set of its
own, and it carries none today. Three decisions are *made* during this stage, each written into
`log/stage-01c-preventive-policies.md` (Lesson 16):

| # | Decision | Step | Reversible? |
|---|---|---|---|
| 1 | Whether the `Interactive` OU gets a policy set of its own, and whether the `sagemaker:CreateNotebookInstance` candidate is adopted | 7.6 | Yes |
| 5 | Whether the tag-forcing SCP is adopted, and over which create actions | 7.8 | Yes, but its cost lands at Stage 6 |
| 6 | Which Region deny control is used — `CT.MULTISERVICE.PV.1` per OU, or landing-zone-wide `GRREGIONDENY` | 7.7 | Yes; enabling **both** is what is hard to undo, because the interaction is not predictable |

*The numbering is the landing zone's: decision 2 belongs to
[Stage 1b](stage-01b-identity-and-controls.md), 3 and 4 to
[Stage 1d](stage-01d-org-wide-enablement.md).*

## Risks

- **This is the only irreversible-from-inside stage in the landing zone's second half.** A bad `Deny` has
  no in-account repair and the recovery path is a detach from the Management account (D16; D30 reverted).
  The `Policy Canary` battery and an already-open Management console are the mitigations, and both are
  procedures rather than properties — they only work if they are actually done.
- **The size budget is small enough to hit.** 7.1 carries the numbers; count before writing.
- **Nothing here is torn down between sessions** — everything is `[P]` (D11).

## Verifications to answer while executing

Record every answer in `log/stage-01c-preventive-policies.md`, including the ones that come out fine.
**The numerals are the landing zone's**, so they are not contiguous here.

| # | Question | Step |
|---|---|---|
| iii | Do the hand-written SCPs/RCPs conflict with the SCPs Control Tower manages itself? | 7.3 |
| vii | Does `CT.MULTISERVICE.PV.1`'s current default `NotAction` still cover everything this project calls from `us-east-1`? Read it off the control's `Artifacts` tab and diff | 7.7 |
| viii | Which namespace does each Unified Studio action actually evaluate under — `datazone:*` or `sagemaker:*`? **Ask it of the `Data` OU as well as of `Workloads`** | 7.6 |

**Was (vii), now answered from the documentation rather than by execution:** *"is Region deny
landing-zone-wide, i.e. untestable against `Policy Test` first?"* — **the landing-zone control
`GRREGIONDENY` is; the OU-scoped `CT.MULTISERVICE.PV.1` is not, and can be canary-tested.** 7.7 carries the
choice that replaces the question.

---

*Stage index: [plan/stages/INDEX.md](INDEX.md) · Previous: [Stage 1b](stage-01b-identity-and-controls.md) · Next: [Stage 1d](stage-01d-org-wide-enablement.md)*
