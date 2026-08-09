# Stage 1a — Landing zone, accounts and OUs

| | |
|---|---|
| **Status** | **in progress** — see `LOG.md` for exactly how far. Control Tower enabled, OUs created, accounts being vended |
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

**Split into two halves, 1a and 1b.** This is the longest stage in the plan and it used to be one
unverifiable block of sixteen manual steps. The split is not cosmetic: **1a ends at a checkable state** —
every account exists, in its OU, with the root credentials secured and a budget watching them — and it is
the half that is slow, awkward to undo, and worth stopping after. 1b is everything that is fast, reversible
and iterative: identity, policies, detective controls and the organization-wide enablements. If a session
runs out before 1b is finished, the environment is still in a coherent state; if it ran out in the middle of
the old Stage 1, it was not.

---

**Pre-flight, before step 1 — the account quota, which is the one thing here that can stall for days.**
AWS Organizations caps the number of accounts an organization may hold, and the cap on a young organization
is low. **Measured on 2026-08-08: this organization's limit is 10 accounts** — the number this stage ends
with (Management plus the member accounts), so it would fit with **no margin at all**.

**And it does not fit, because the organization was not empty.** An **older AWS account, predating this
project, is already attached to the organization** and consumes a slot, so this stage's set plus that one is
**eleven against a cap of ten**. Two things follow, and neither is optional:

- **A quota increase was requested at 15** (Service Quotas → AWS Organizations → "Maximum number of
  accounts"; it is a global setting but the request is filed from `us-east-1`). It is recorded in `LOG.md`
  as *requested*. **Confirm it was granted before vending the last accounts** — the granted value goes in
  `LOG.md`.
- **Until it is granted, defer `Staging`.** It is the right one to defer and the reason is structural, not
  arbitrary: its first hard dependency is Stage 8, and D20 keeps it unpeered from everything, so nothing
  earlier is waiting on it. **Deferring costs nothing now that D34 has withdrawn the retirement of the only
  identity that can vend** — there is no "vend it before the vending credential goes away" ordering trap
  left, so this is a scheduling choice and not a structural one.

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

**To execute (all manual, by the user, recorded in `LOG.md`):**

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
2. Create a Budget of **USD 50/month** (D12) with e-mail alerts at 50%/80%/100%. Enable **Cost Anomaly
   Detection** next to it — it is free, and it catches a bad cost *pattern* days before a budget
   threshold trips. Optionally add a budget *action* that attaches a deny-compute SCP at 100% — a
   lab-appropriate emergency brake.
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
     are therefore not optional: **MFA here**, **Object Lock in compliance mode** (1b step 9), and the
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
     any of the three approvers placed here holds the separation of duties `ACCOUNTS_AND_USERS.md`
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
     per business unit (D35). Interactive compute *allowed*; human infrastructure changes denied. The only
     OU into which project blueprints may provision (D26). **Attach the policy set to `Interactive`, not to
     `Sandboxes`** — the nested OU carries none of its own and inherits, which is what makes a newly vended
     unit governed the moment it lands. Created this way on 2026-08-09 (`LOG.md`); it is the reason the
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
     **This OU is also the sole exception to an organization-root deny** (1b step 7): `datazone:CreateDomain`
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
     `Identity` was meant to join them and **could not** — the vend was refused on 2026-08-09 (`LOG.md`).
     This step had flagged it as a thing to verify rather than assume, for the right reason: `Security` is a
     *foundational* OU in Control Tower's model, and a non-Control-Tower-created account does not simply
     join one.
   - `Identity` OU → `Identity`. **This is the fallback this step named, and it fired.** Take the one
     consequence seriously rather than treating the OU as a rename: `Security`'s policy set was never
     written by this project — it is Control Tower's guardrails, inherited by the OU being *foundational* —
     so a brand-new sibling OU inherits **none** of it. **Enumerate the controls applied to `Security` and to
     `Identity`, compare them, and attach whatever differs explicitly in 1b step 7** (D34: a console-created
     OU carries no policy set until code attaches one). This is the account whose administrator can grant
     access to every other account; it did not become less sensitive by moving.

   **The accounts listed above are the complete set *for this stage*, which is not the same as the complete
   set (D34).** D14 places the tooling in Production rather than in a separate Shared Services account,
   D20-D22 add the deployment target, the development account and the data account the AWS reference
   architectures describe, and D29 adds the disposable one that makes the SCP procedure in 1b step 7
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
5. **Break-glass: the procedure and the alarm (D16).** The *credential* was handled in step 1 — it is this
   root, there is no second mechanism to build. What is left here is what makes it a break-glass rather
   than just an account owner: write the procedure down (what situations justify using it — an Identity
   Center outage, an organization-level policy that locked everyone out; what to do; what to record
   afterwards), build the alarm, and test the whole thing once. **This belongs in 1a and not later**: every
   policy in 1b is a way to lock yourself out of your own organization, and the escape hatch has to predate
   the hazard.
   **The alarm needs a delivery path, not just an intention** (Lesson 5 in `CLAUDE.md`: name the policy line
   that enforces the stated property). A CloudWatch alarm cannot watch an S3 bucket, and Control Tower's
   organization trail delivers to the Log Archive account's bucket. So the alarm requires an explicit chain:
   the trail (or a Management-account trail) writing to a **CloudWatch Logs** group, a **metric filter**
   matching `userIdentity.type = Root`, a metric, an alarm, and an SNS
   topic with a subscription that is **not** the same e-mail as the account being alarmed on — root sign-in
   *is* e-mail plus password, so alarming to the login address hands the same person the credential and its
   own warning. Since D33 that address is doubly disqualified: it is also the `AWS Control Tower Admin`
   login. Build the chain here and fire it once with a deliberate sign-in; an untested alarm is a
   hypothesis.
   **Be honest about how much the "different address" rule buys here, because the prose above overstates
   it (Lesson 5).** In an institution the alarm goes to someone who is *not* holding the root credential.
   In this lab every address is a `+alias` on one Gmail account and there is one human, so a distinct
   address buys **routing and filterability — not separation**: the same mailbox compromise defeats both.
   What actually adds a second factor is a **second channel**: subscribe an SMS endpoint to the topic
   alongside the e-mail. SNS supports it directly, it costs cents at this volume, and it is the only part of
   this step that survives the one-inbox problem. Register whichever address is chosen in
   `secrets/emails.md` before building the topic.
   **Two SNS topics already exist and are not this one.** Control Tower created
   `aws-controltower-SecurityNotifications` per Region and `aws-controltower-AggregateSecurityNotifications`
   in the Audit account, and **subscribed the Audit account's e-mail to the aggregate topic automatically**.
   Do not reuse them for break-glass: they are deliberately noisy — AWS Config notifies on every resource it
   discovers — and an alarm that arrives in a stream nobody reads is not an alarm. Note also that the
   Audit account's *root* address being a notification endpoint is the same shape as the rule above, one
   account over; step 6 is what defuses it, by removing that account's root credentials centrally, after
   which the address is a mailbox rather than a credential.
   **This is the only recovery path, and that is a decision rather than an omission (D30, reverted).** A
   narrower standing principal exempt from every custom `Deny` was proposed, adopted and then removed: the
   lab keeps no exemption, so the root handles all three failures — "Identity Center is down", "the
   organization itself is broken", and "a custom SCP denies something it should not". **Two consequences
   for how the rest of Stage 1 is executed, and both are already written into it:** the break-glass chain
   below must work *before* the first policy is attached in 1b step 7, and every candidate policy goes
   through the `Policy Canary` battery (D29) first — with no exemption, catching a bad policy before
   attachment is far cheaper than repairing it afterwards.
6. **Centralized root access management.** Every member account — the ones Control Tower created (Log
   Archive, Audit) and the ones Account Factory created — arrives with its own root user and its own
   recovery e-mail: one dormant credential per account, none of which anybody will ever rotate. AWS
   Organizations can remove root credentials from member accounts centrally and perform the few privileged
   root actions on demand. Enable it; this is one console setting that eliminates a whole class of dormant
   risk.

**Deliverables of 1a:** every account exists, in its OU, each with the **same** infrastructure user holding
administrative access through Identity Center (D32) — one user in the directory, not seven; the Management
root user is secured and its break-glass path has been tested once; member-account root credentials are
centrally managed; the budget and Cost Anomaly Detection are live. The `AWS Control Tower Admin` user exists,
has MFA, and **stays** — it is the standing owner of Control Tower administration (D34), not a credential
awaiting retirement. Nothing here is torn down between sessions, and nothing after this
point can lock you out without a way back in.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
