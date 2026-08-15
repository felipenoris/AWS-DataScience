# Stage 1a — Landing zone, accounts and OUs

| | |
|---|---|
| **Status** | **done on 2026-08-09, except the deferred `Staging` vend** (step 4). Step 2's budget alerts + Cost Anomaly Detection are **skipped by decision**, not outstanding — [`log/log-stage-01a-landing-zone.md`](../../log/log-stage-01a-landing-zone.md) is authoritative |
| **Prerequisites** | none outstanding (D1 decided, an e-mail registered for every account this stage creates) |
| **Consumes** | [D1](../decisions/D01-region.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D16](../decisions/D16-break-glass.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D29](../decisions/D29-policy-canary.md), [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md) |
| **Proves** | — |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** a working AWS Organization with the environment accounts and SSO access, so that everything
after this can be done by Terraform without root credentials.

**Prerequisites:** none outstanding. D1 is decided (`us-west-2`) and an e-mail is registered in
`secrets/emails.md` for every account this stage creates — `Policy Canary`'s was added by the user on
2026-08-08, after D29 introduced the account.

**Split into halves, then the second half into three.** This is the longest stage in the plan and it used
to be one unverifiable block of sixteen manual steps. The split is not cosmetic: **1a ends at a checkable
state** — every account exists, in its OU, with the root credentials secured and a budget watching them —
and it is the half that is slow, awkward to undo, and worth stopping after. If a session runs out anywhere
after it, the environment is still in a coherent state; if it ran out in the middle of the old Stage 1, it
was not.

The second half was itself split on 2026-08-09, along the sessions it already described:
**[1b](stage-01b-identity-and-controls.md)** (identity, profiles, the alarm — steps 1-6 and 8),
**[1c](stage-01c-preventive-policies.md)** (step 7, the policies, the one part that is not freely
reversible) and **[1d](stage-01d-org-wide-enablement.md)** (steps 9-11: the audit trail, the Config
decision, the org-wide enablements). **The step numbers did not change**, so references from this file to
`1c step 7` or `1d step 9` name exactly the steps they always did.

---

**Pre-flight, before step 1 — the account quota, which is the one thing here that can stall for days.**
AWS Organizations caps the number of accounts an organization may hold, and the cap on a young organization
is low. **Measured on 2026-08-08: this organization's limit is 10 accounts** — the number this stage ends
with (Management plus the member accounts), so it would fit with **no margin at all**.

**And it does not fit, because the organization was not empty.** An **older AWS account, predating this
project, is already attached to the organization** and consumes a slot, so this stage's set plus that one is
**eleven against a cap of ten**. Two things follow, and neither is optional:

- **A quota increase was requested at 15** (Service Quotas → AWS Organizations → "Maximum number of
  accounts"; it is a global setting but the request is filed from `us-east-1`). It is recorded in `log/log-stage-01a-landing-zone.md`
  as *requested*. **Confirm it was granted before vending the last accounts** — the granted value goes in
  `log/log-stage-01a-landing-zone.md`.
- **Until it is granted, defer `Staging`.** It is the right one to defer and the reason is structural, not
  arbitrary: its first hard dependency is Stage 8, and D20 keeps it unpeered from everything, so nothing
  earlier is waiting on it. **Deferring costs nothing now that D34 has withdrawn the retirement of the only
  identity that can vend** — there is no "vend it before the vending credential goes away" ordering trap
  left, so this is a scheduling choice and not a structural one.

**What the deferral leaves owed, in one list — because it is currently owed by five different files.**
Each of the stages below carries its own "skip the Staging cell" note, which is right for someone executing
that stage and useless for someone vending the account six weeks later. **When `Staging` is vended, work
this list**, and record it in `log/log-stage-01a-landing-zone.md` beside the vend itself:

| Owed by | What |
|---|---|
| [1b step 3](stage-01b-identity-and-controls.md) | The `Staging` cells of the assignment table — `DataScientistStagingAccess`, and `DeploymentManagerAccess` on Staging. Both sets are **written in Stage 2 step 5**, so after Stage 2 this is an entry in the enumerated assignment list, not console work |
| [1b step 5](stage-01b-identity-and-controls.md) | The `awsds-infra-staging` profile, bound to this project's `InfrastructureAccess` |
| [1b step 6](stage-01b-identity-and-controls.md) | The AZ name→ID mapping for the account, before Stage 3 writes a subnet for it |
| [1c step 7.4](stage-01c-preventive-policies.md) | Account-level S3 Block Public Access. **Decision 7 settled it (2026-08-13): the root deny carries a carve-out for `InfrastructureAccess`**, so this is still possible after the vend — from `awsds-infra-staging` and from nothing else. Do it at the vend anyway; the carve-out makes it recoverable, not automatic |
| [1c step 7.7](stage-01c-preventive-policies.md) | Nothing extra *if* the account lands in the already-governed `Workloads` OU — confirm the controls enabled on that OU reached it, rather than assuming inheritance |
| [Stage 2 step 3](stage-02-terraform-foundation.md) | `terraform-live/staging/bootstrap/` — its state bucket and KMS key |

The first and the fourth are the ones that change character with time: after Stage 2 the identity half is
code, and after 1c the BPA half may no longer be possible at all.

Two consequences of a thin margin, both of which bite at the worst moment:

- A failed Account Factory provisioning that has to be retried can consume a slot, and a **closed account
  still counts against the quota** while it is in the post-closure retention window (~90 days). So the
  first retry is also the first quota breach.
- `Policy Canary` is disposable *by design* (D29). With zero margin it is not actually disposable: closing
  it does not free the slot for ~90 days.

The increase is free and it is a support ticket that can take days, which is why it is the one item here
worth filing before anything else. **It also stops being a stage pre-flight after this stage (D34):
quota headroom is a standing item**, because vending is a standing capability — and under **D35** the
recurring consumer of slots is named: **one slot per business unit**, since `Sandbox` is the one account
that multiplies.

**To execute (all manual, by the user, recorded in `log/log-stage-01a-landing-zone.md`):**

1. **Secure the Management account root user — which since D16 is also the break-glass credential, so this
   step and step 5 are two halves of one thing rather than two mechanisms.** MFA enabled (the *type* is
   deliberately unspecified — see D16; the user already has one configured on this root, so here this is a
   *confirm*, not a *do*), strong password stored offline, **no access keys, ever**, billing alerts enabled.
   Two details that are load-bearing rather than hygienic:
   - **The password does not live in this repository and not in `secrets/` either** — offline means a
     password manager or paper, not a git-ignored folder.
   - **Check how many MFA devices are registered.** With exactly one, losing it means the AWS account
     recovery process, which depends on the phone number and payment method on the account — so confirm
     both are current while you are here. This is the recovery path of the recovery path, and it is the
     only part of the MFA question that still has consequences once the type is left open.
2. Create a Budget of **USD 50/month** (D12). **The e-mail alerts at 50%/80%/100% and Cost Anomaly
   Detection were skipped by decision on 2026-08-09** — both free, both described here as the way the
   ceiling announces itself, and neither exists. What was built is the budget alone, which is a figure in
   a console rather than a notification, so **overspend is discovered by looking**. The optional budget
   *action* that attaches a deny-compute SCP at 100% was not built either; with no alert above it, it is
   now the only mechanism in this step that would act without being watched, which is the argument for
   revisiting it first if the skip is ever undone.
3. Enable AWS Control Tower with `us-west-2` as the home region. It will create the Organization, the
   Log Archive and the Audit accounts (e-mails already in `secrets/emails.md`), and turn on org-wide
   CloudTrail and Config. Note: the home region cannot be changed afterwards without redeploying the
   landing zone.
   **Two things the setup wizard asks that this plan has an opinion about, and which are awkward to change
   later:** it asks for the name of the foundational security OU (default `Security` — keep it, D23 uses
   that name) *and* for an additional OU whose **default name is `Sandbox`**. Do **not** accept that
   default: this project has a `Sandbox` **account**, and an OU with the same name guarantees a permanent
   ambiguity in every later sentence about SCPs. Name it `Interactive` here — it is the OU D23 wants
   anyway — or give it a throwaway name and create the four real OUs in step 4.

   **What this step silently creates, and which nothing else in the plan asked for (D33).** Setting up the
   landing zone builds an Identity Center directory **and populates it**: Control Tower's own groups
   (`AWSAccountFactory`, `AWSControlTowerAdmins`, the auditor groups), its own permission sets — including
   one named **`AWSAdministratorAccess`** — and a first administrator. That administrator is an Identity
   Center user with display name **`AWS Control Tower Admin`**, carrying the **Management account's root
   e-mail** and belonging to both `AWSAccountFactory` and `AWSControlTowerAdmins`; it announces itself as an
   *"Invitation to join AWS IAM Identity Center"* in that inbox. Those two memberships are its whole
   footprint, and they reach further than the Management account: `AWSControlTowerAdmins` is
   `AWSAdministratorAccess` on **Management, Log Archive and Audit**, plus `AWSOrganizationsFullAccess` on
   every member account. No field in the wizard asked about any of it (Lesson 17), and **1b steps 2 and 3
   were written assuming an empty directory** — they now say otherwise.
   Three things to do while still here, before step 4 needs it:
   - **Set the AWS access portal URL** (IAM Identity Center → Settings) and record it in `secrets/emails.md`.
     It is the sign-in path for every human from this point on.
   - **Accept the invitation and put MFA on that user — this is the one item here that is not optional.**
     It administers the Management account *and the Log Archive account*, so it can delete the organization
     CloudTrail record of its own use, including the trail step 5's alarm reads. Password-only, under an
     address that is also the root login, is a worse credential than the root beside it. The reach cannot be
     trimmed while it is in use: `AWSControlTowerAdmins` is atomic, and the Management administrator this
     stage runs on comes in the same membership as the Log Archive one.
   - **Note it as the standing owner of Control Tower administration (D34, amending D33)** — it vends the
     accounts in step 4 and **keeps** that job afterwards: OUs, account vending, enrolment, landing-zone
     updates, from the console and never from Terraform. It was originally to be disabled at the end of 1b;
     that retirement is withdrawn, because the account list is not static and Control Tower administration
     needs an owner rather than an end date. It is still **not one of the five personas** — it holds one
     duty, approves nothing, and joins no project group. Its permanence moves weight onto three things that
     are therefore not optional: **MFA here**, **Object Lock in compliance mode** (1d step 9), and the
     **group-membership alarm** (1b step 8).
4. Create the `Sandbox`, `Development`, `Staging`, `Production`, `Data Governance`, `Identity` and
   `Policy Canary` accounts through Account Factory, using the e-mails in `secrets/emails.md`.

   **Sign in at the access portal first — Account Factory cannot be driven from root, at all (D33).** From
   the root user the console returns *"Your AWS IAM identity does not have access to the AWS Control Tower
   Account Factory portfolio in AWS Service Catalog"*, and that is the documented design rather than
   something to repair: Account Factory is a Service Catalog product whose portfolio grants access to IAM
   users, groups and roles, and AWS states that provisioning requires `AWSServiceCatalogEndUserFullAccess`
   and that you **cannot be signed in as the root user**. There is no principal to associate for root. The
   path is: **access portal → `AWS Control Tower Admin` → `AWSAdministratorAccess` on the Management
   account → Control Tower → Account Factory.** Confirmed working on 2026-08-09.

   **Account Factory asks for two e-mail addresses and only one of them is the account's (D32).** The
   `Account email` becomes the vended account's **root** user. The second, under **Access configuration**
   (`SSOUserEmail`, with a first and last name beside it), is a permission decision wearing a contact
   field's clothes — AWS's own wording is that this user *"will have administrative access to the account
   you're provisioning"*. Fill it with the **infrastructure user** (its address is registered in
   `secrets/emails.md`; first/last name `Infrastructure` / `User`) and use **the same address on
   every account vended, here and later (D34)**: Account Factory recognises the existing Identity Center user and adds one more
   assignment instead of creating a second one, so the result is a single administrator with a single MFA
   device — which is exactly the bootstrap access Stage 2 needs in order to run Terraform without root.
   Three ways to get this wrong, none of them cheap to undo:
   - **Do not reuse the account's own address here.** AWS permits it; this plan does not. That address is
     the root user, and step 5 alarms on root sign-in while step 6 removes root credentials centrally — an
     address that is also a normal daily login makes the alarm ambiguous and hands one inbox both the
     credential and its own warning.
   - **Do not use any of the other four personas.** The field grants administrator, so a data scientist or
     any of the three approvers placed here holds the separation of duties `ORGANIZATION.md`
     describes before it has been built (Lesson 9).
   - **Do not treat it as changeable later.** Updating the provisioned product with a different
     `SSOUserEmail` **creates a second Identity Center user and leaves the first one in place** — a dormant
     administrator, which is the very thing step 6 is removing on the root side.

   **Two consequences to carry forward, both picked up in 1b.** The infrastructure user now **exists in
   Identity Center before 1b step 2 runs**, so that step creates four users and not five. And every vended
   account is left holding a *direct* administrator assignment, outside the group model — **not removed
   here, and not removed by default**; D32 says when and whether.

   **Create the OUs from the Control Tower console, not from AWS Organizations.** An OU created directly in
   Organizations is not *registered* with Control Tower: Account Factory will not provision into it, the
   guardrails do not apply, and the accounts that land there are unenrolled — a state that looks correct in
   the Organizations tree and is not. Registering an OU afterwards is possible but is extra work at exactly
   the moment there is least appetite for it. OUs, per D23 — each named for the
   policy set it carries, not for its contents:
   - `Interactive` OU → `Development`, plus a nested **`Sandboxes` OU** holding the `Sandbox` accounts, one
     per business unit (D35). Interactive compute *allowed* — because, unlike `Workloads` and `Data`, nothing
     here denies it. **This OU carries no set of its own**, and the line that used to say "human
     infrastructure changes denied" described an identity policy (`DataScientistAccess`), not an SCP; Stage 1b
     step 7 carries the correction and the choice of whether to give the OU a set at all. The only OU into
     which project blueprints may provision (D26). **If a set is written, attach it to `Interactive`, not to
     `Sandboxes`** — the nested OU carries none of its own and inherits, which is what would make a newly
     vended unit governed the moment it lands. Created this way on 2026-08-09 (`log/log-stage-01a-landing-zone.md`); it is the reason the
     organization's OU nesting depth is 2, which Stage 2 has to write its `for_each` against.
   - `Data` OU → `Data Governance` (D22, D26, D27). **No *user* compute** — the SCP denies EC2 and
     SageMaker outright, plus Glue job creation and execution (D25) — and deletion protection is the
     policy set's whole personality. **Two named carve-outs, and the distinction between them is the
     point:** `datazone:*` is permitted because a DataZone domain is a governance *control plane*, in the
     same sense Lake Formation always was — it grants and records, it does not run anyone's code (D26);
     and `glue:CreateCrawler`/`StartCrawler` plus the table-optimizer and column-statistics actions are
     permitted **only when the principal is the lake's catalog-maintenance role** (D27), which *is* real
     compute and is therefore bounded by role, event-driven and alarmed. Anything not on those two lists
     stays denied.
     **This OU is also the sole exception to an organization-root deny** (1c step 7): `datazone:CreateDomain`
     is denied everywhere and carved out here, so the unified domain can exist only in this account. Note
     the mechanism, because getting it backwards produces a policy that does nothing — SCPs are ceilings and
     an explicit `Deny` wins wherever it appears, so the exception is a **condition on the root deny**
     naming this OU, never an `Allow` written in this OU's own policy set.
   - `Workloads` OU → `Staging` and `Production` (D20). No interactive compute, no human control plane,
     written once and attached once. **Not to be confused with the `Policy Test` OU below** — the industry
     calls that one a *Policy Staging OU*, and this plan deliberately does not, precisely so that the word
     `Staging` names exactly one thing in this organization.
   - `Policy Test` OU → `Policy Canary` (D29). **Carries no policy set of its own** — it is where a
     *candidate* SCP or RCP is attached and exercised before it goes anywhere real, which is what step 7 of
     1b needs and what the plan previously asked for without providing. The account inside it is
     deliberately empty: no VPC, no data, no Terraform slice, no state bucket, no `awsds-infra-*` profile.
     It holds one thing and that is the whole design — **an administrator principal**, assigned in 1b step
     3, because an SCP is a permission *ceiling* and testing it with a restricted principal measures the
     identity policy instead. Enroll it through Account Factory like the others: an OU that is not
     registered with Control Tower does not inherit the CT controls, so a policy tested there is tested
     against a different baseline than the one it will meet in production — which is worse than not
     testing, because it produces a false pass.
   - `Security` OU → the Log Archive and Audit accounts Control Tower created, **and nothing else.**
     `Identity` was meant to join them and **could not** — the vend was refused on 2026-08-09 (`log/log-stage-01a-landing-zone.md`).
     This step had flagged it as a thing to verify rather than assume, for the right reason: `Security` is a
     *foundational* OU in Control Tower's model, and a non-Control-Tower-created account does not simply
     join one.
   - `Identity` OU → `Identity`. **This is the fallback this step named, and it fired.** The consequence
     this file predicted — that a brand-new sibling OU inherits **none** of `Security`'s policy set, since
     that set is Control Tower's guardrails reaching it by being *foundational* — **was measured on
     2026-08-13 and is wrong.** `Identity` carries `aws-guardrails-coSzJr`, Control Tower's standard eight
     statements, the same document every other registered OU has: it was registered when it was created.
     What `Security` has extra is three statements about the log-archive and audit buckets, which mean
     nothing for an account that holds neither. **The instruction stands in weakened form** — compare the
     *enabled controls* of the two in 1c step 7.0 step 3, which is a different registration from the SCP
     and is still unread. This is the account whose administrator can grant access to every other account;
     it did not become less sensitive by moving.

   **The accounts listed above are the complete set *for this stage*, which is not the same as the complete
   set (D34).** D14 places the tooling in Production rather than in a separate Shared Services account,
   D20-D22 add the deployment target, the development account and the data account the AWS reference
   architectures describe, and D29 adds the disposable one that makes the SCP procedure in 1c step 7
   executable. `plan/institutional-delta.md` records what a larger organization would still add beyond them.
   **An account added later is an ordinary event, not an exception**: D34 carries the flow — the gate is
   which axis and which OU the account needs (D23), the owner is `AWS Control Tower Admin`, and the
   post-vend baseline is code that already exists (`bootstrap/`, the identity slice, `foundation/`, an SSO
   profile). **A consequence that matters right now: an account may be deferred without a structural cost**,
   so if the quota increase has not been granted, vend what fits and vend the rest afterwards.
   Account creation here is manual through Account Factory; **Account Factory for Terraform (AFT)** is the
   automated equivalent and is deliberately not used — but note that its rejection rested on "created once",
   a premise D34 retired, so what keeps it out now is measured cost and not frequency
   (`plan/institutional-delta.md`).
5. **Break-glass: the procedure and the alarm (D16).** Three deliverables: the procedure written down, the
   alarm chain built, and the whole thing tested once. **The first is done —
   [`plan/runbooks/break-glass.md`](../runbooks/break-glass.md)**, whose §0 carries *why* this step exists
   and whose §7 is the reference copy of the chain below. Read it once before building; what follows is only
   the procedure.

   **Sign in as `AWS Control Tower Admin` → `AWSAdministratorAccess` on the Management account, region
   `us-west-2`.** The whole chain is built from that session. The root is needed only in 5.5, to fire the
   alarm.

   **5.0 — Two choices, made before the console is open.** Pick the **e-mail address the alarm notifies**
   (a dedicated alias, *not* the root address — runbook §0 says why) and the **mobile number** for the SMS
   endpoint, and register both in `secrets/emails.md`. That file is the user's and is git-ignored: neither
   value is ever copied into this repository.

   **5.1 — Verify what the landing zone already delivered. Build nothing yet.**
   - **CloudWatch → Logs → Log Management → Log groups** must contain **`aws-controltower/CloudTrailLogs`**. From landing zone 3.0
     it is created **only in the Management account** (earlier versions put one in every enrolled account),
     which is why the filter goes here and not in Log Archive.
   - **CloudTrail → Trails → `aws-controltower-BaselineCloudTrail`** must show **Multi-region: Yes** and
     **Global service events: Yes**. This is load-bearing: **root console sign-in is recorded in
     `us-east-1`**, because console sign-in is a global service in CloudTrail. A new single-Region trail in
     `us-west-2` would not see the event at all — which is precisely why this chain hangs off the existing
     organization trail instead of creating one.
   - Being an *organization* trail, member-account events land in this same log group, so **one metric
     filter covers every account** — useful until step 6 removes the member roots, and a backstop after.
   - **Do not modify the trail**: an edit is landing-zone drift. Adding a *metric filter* to the log group
     is not — it is a separate resource, and the log group survives even a decommission.
   - **If the log group is absent** (a landing zone set up without CloudWatch Logs), stop and re-plan: the
     fallback is a second, Management-only trail, which changes both the cost and the steps below.

   **5.2 — The SNS topic and its two subscriptions.** SNS in `us-west-2`, **Standard** topic:
   - Name `awsds-org-break-glass-alerts`; **Display name** set (SMS requires one — it becomes the sender
     prefix).
   - **Leave encryption off.** With SSE under the AWS-managed `aws/sns` key, a CloudWatch alarm **cannot
     publish** — the CloudWatch service principal has no `kms:GenerateDataKey` on it, and the alarm fails
     *silently*: a chain that cannot deliver looks exactly like a quiet organization (Lesson 13), which is
     the one failure mode this whole step exists to prevent. Encrypting would require a customer-managed key
     with an explicit key policy; not worth it here.
   - **E-mail subscription** → the 5.0 address → **confirm the link**; it stays `Pending confirmation` until
     then, and an unconfirmed subscription is a channel that does not exist.
   - **SMS subscription**, which needs one prior step: a new account is in the **SNS SMS sandbox** and can
     only send to *verified* numbers. **SNS → Text messaging (SMS) → Sandbox destination phone numbers →
     Add**, verify by OTP, then subscribe the number to the topic. Nothing else is needed for Brazil: it
     supports short codes, does **not** support long codes or sender IDs, and requires **no** registration,
     so there is no origination identity to buy and no filing to wait on — AWS sends over its shared
     short-code pool, best effort.
   - **Do not reuse the two Control Tower topics** — runbook §0 says why.

   **5.3 — The metric filter.** On `aws-controltower/CloudTrailLogs` → **Metric filters → Create**:
   - Pattern (the CIS root-usage pattern; it catches **any** root API call, not only `ConsoleLogin`):
     `{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent" }`
   - Filter name `awsds-org-root-activity`; namespace `AWSDS/Security`; metric name `RootActivityCount`;
     metric value `1`.
   - **Leave `Default value` empty.** A metric-filter metric is a *custom* metric at USD 0.30/metric-month,
     metered only for the hours it actually publishes — so with no default value a quiet month costs nothing
     (`PRICING.md` §6). The price of that choice is paid in 5.4.

   **5.4 — The alarm.** CloudWatch → Alarms → Create → metric `AWSDS/Security` / `RootActivityCount`:
   - **Sum**, period **1 minute**, static threshold **≥ 1**, **1 of 1** datapoints.
   - **Missing data: `notBreaching`.** This is the price of 5.3: with no default value the metric publishes
     nothing while all is well, and any other setting turns silence into an alarm or an
     `INSUFFICIENT_DATA` that hides one.
   - Name `awsds-org-root-activity`; **In alarm** action → the topic from 5.2.

   **5.5 — Test it. An untested alarm is a hypothesis.** Sign in as Management root, do nothing, sign out.
   Allow **up to ~15 minutes** end to end (CloudTrail delivery → CloudWatch Logs → metric → alarm → SNS);
   past ~20 minutes it is a failure, not latency. Confirm the message arrived on **both** channels — a
   missing channel is a finding — and that the alarm returns to `OK` on its own.

   **5.6 — Record it.** Resource names and the test result in `log/log-stage-01a-landing-zone.md` (the user's file), and the date in
   the **Last tested** row of the runbook.
6. **Centralized root access management.** Every member account — the ones Control Tower created (Log
   Archive, Audit) and the ones Account Factory created — arrives with its own root user and its own
   recovery e-mail: one dormant credential per account, none of which anybody will ever rotate, and each one
   re-obtainable by whoever holds that inbox. AWS Organizations can remove those credentials centrally and
   perform the few genuinely root-only actions on demand, as short sessions. **It does not touch the
   Management account root**, which is what makes it compose with D16 instead of competing with it: every
   member root disappears, one root remains, and that one is the break-glass.

   **6.0 — Sign in as `AWS Control Tower Admin` → `AWSAdministratorAccess` on the Management account.**
   Not as root, and that is a hard constraint rather than a preference: **`sts:AssumeRoot` cannot be called
   by a root user**, and every privileged action below is a root session. Same shape as step 4's Account
   Factory refusal (D33) — vending and this are the two Management-account jobs root cannot do.

   **6.1 — Do this before the `Staging` vend, if the quota allows.** Accounts created in Organizations
   *after* the feature is on have **no root credentials at all**, so `Staging` would be born clean and 6.4
   would never have to touch it. Nothing breaks in the other order; it is one account's worth of manual work,
   and the pre-flight's quota wait is the only reason it might come to that.

   **6.2 — Enable the feature.** IAM console (Management account) → **Root access management** → **Enable**:
   - Enable **both** capabilities. `Root credentials management` is the deletion; **`Privileged root actions
     in member accounts` is the way back** — without it `Allow password recovery` does not exist, and a
     deleted root is deleted with no documented path to restore it. AWS states the dependency plainly, which
     is why enabling only the first is the one wrong way to do this step.
   - **Leave `Delegated administrator` empty.** The natural candidate is the `Identity` account by analogy
     with D10, and that analogy is exactly why it waits: the account is vended and otherwise bare until 1b,
     and this delegation grants root sessions into **every** account in the organization. Deferring costs
     nothing — it is one reversible API call — and a delegation of that reach is a decision with a number,
     not a field filled in while passing.
   - If the page reads **`Root access management is disabled`**, trusted access for IAM is not on in
     Organizations: enable `iam.amazonaws.com` there and come back.

   **6.3 — Verify, with something that cannot pass silently** (Lesson 13). From CloudShell in the Management
   account, `aws iam list-organizations-features` must list **both** `RootCredentialsManagement` and
   `RootSessions`, and `aws organizations list-aws-service-access-for-organization` must include
   `iam.amazonaws.com`. Both return content on success and different content on failure, which the
   per-account view does not.

   **6.4 — Delete the credentials, one account at a time.** IAM → **Root access management** → select the
   account → **Take privileged action** → **Delete root credentials**. The console shows a credential report
   first — password present, access key present and when it was last used, signing certificates, MFA — and
   **that report is the only time anybody will ever look at that account's root**: anything in it other than
   "nothing" belongs in `log/log-stage-01a-landing-zone.md`. The deletion removes password, access keys and signing certificates and
   deactivates MFA. **There is no bulk action in the console**; the per-account CLI equivalent is

   ```bash
   aws sts assume-root --target-principal <account-id> --task-policy-arn arn=arn:aws:iam::aws:policy/root-task/IAMDeleteRootUserCredentials --duration-seconds 900 --region us-west-2
   ```

   followed by `delete-login-profile`, `delete-access-key`, `delete-signing-certificate` and
   `deactivate-mfa-device` under the returned credentials (note: `sts:AssumeRoot` has **no global endpoint** —
   the `--region` is required — and the session is capped at 900 seconds). The member accounts today are
   `Log Archive`, `Audit`, `Development`, `Sandbox Account 1`, `Production`, `Data Governance`,
   `Policy Canary` and `Identity`, plus `Staging` unless 6.1 made it moot — eight or nine is below the
   threshold where scripting a privileged path earns its own risk.

   **6.5 — Expect the break-glass alarm to fire, and take it as the second test of step 5.** The *actions*
   inside a privileged session are logged in the target account as `userIdentity.type = "Root"`, which is
   precisely what 5.3's filter matches, and the trail is org-wide — so **every deletion pages both
   channels**. Two things follow, better written down than discovered: from here on the alarm means "root
   activity anywhere", and a privileged session is told apart from a real root sign-in only by correlating
   the `sts.amazonaws.com` `AssumeRoot` event (`sessionContext.assumedRoot = true`, plus
   `requestParameters.targetPrincipal`) with the `accessKeyId` on the member-account events. And **if nothing
   arrives on both channels here, step 5 never worked**: `log/log-stage-01a-landing-zone.md` records the 5.5 test as performed but not
   its result, so this is where that gets settled.

   **6.6 — What it costs, and the reversal.** Afterwards a member account cannot sign in as root and cannot
   run password recovery; anything genuinely root-only there is done from Management as a ≤15-minute session,
   and **only five task policies exist** (audit credentials, create root password, delete credentials, unlock
   an S3 bucket policy, unlock an SQS queue policy). Two of those five are the "I denied myself" repairs, so
   the practical loss is narrow. The one capability this design might have wanted and cannot have from inside
   the account is **S3 MFA Delete**, which requires that account's own root — and 1d step 9 uses Object Lock
   in compliance mode instead, so nothing is actually given up. Reversal, if it is ever needed: **Allow
   password recovery** on that account (only offered once the credentials are gone), reset from the root
   inbox, do the task, delete again.

   **6.7 — Carry one consequence into 1c step 7.** Control Tower's strongly-recommended control
   **`AWS-GR_RESTRICT_ROOT_USER`** denies `*` where `aws:PrincipalArn` matches `arn:*:iam::*:root` — which
   **also denies privileged root sessions**, because in the member account they *are* that principal. It is
   **not enabled by default**, so nothing is broken today. If 1c step 7 enables it (or writes the
   hand-rolled equivalent), it must carry the **`ExemptAssumeRoot`** parameter, which adds
   `"Null": {"aws:AssumedRoot": "true"}` to the condition. Without that, the control and this step's own
   recovery action cancel out — the escape hatch is denied by the guardrail meant to protect it.

   **6.8 — Record it in `log/log-stage-01a-landing-zone.md`**: date, which capabilities were enabled, whether a delegated administrator
   was set, what each account's credential report showed, and whether both alarm channels fired.

**Deliverables of 1a:** every account exists, in its OU, each with the **same** infrastructure user holding
administrative access through Identity Center (D32) — one user in the directory, not seven; the Management
root user is secured and its break-glass path has been tested once; member-account root credentials are
centrally managed; the USD 50 budget exists, **with no alert thresholds and no Cost Anomaly Detection
beside it** (skipped by decision — step 2). The `AWS Control Tower Admin` user exists,
has MFA, and **stays** — it is the standing owner of Control Tower administration (D34), not a credential
awaiting retirement. Nothing here is torn down between sessions, and nothing after this
point can lock you out without a way back in.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
