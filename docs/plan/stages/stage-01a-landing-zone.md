# Stage 1a — Landing zone, accounts and OUs

| | |
|---|---|
| **Status** | **done on 2026-08-09, except the deferred `Staging` vend** (step 4). Step 2's budget alerts + Cost Anomaly Detection are **skipped by decision**, not outstanding — [`docs/log/log-stage-01a-landing-zone.md`](../../log/log-stage-01a-landing-zone.md) is authoritative |
| **Prerequisites** | none outstanding (D1 decided, an e-mail registered for every account this stage creates) |
| **Consumes** | [D1](../decisions/D01-region.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D16](../decisions/D16-break-glass.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D29](../decisions/D29-policy-canary.md), [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md) |
| **Proves** | — |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** a working AWS Organization with the environment accounts and SSO access, so that everything
after this can be done by Terraform without root credentials.

**Prerequisites:** D1 is decided (`us-west-2`) and `secrets/emails.md` holds an e-mail for every account
this stage creates — `Policy Canary`'s was added by the user on 2026-08-08, after D29 introduced the
account.

**The second half is 1b, 1c and 1d.** 1a ends at a checkable state — every account exists, in its OU, with
the root credentials secured and a budget watching them — so a session that stops after it leaves a
coherent environment. **[1b](stage-01b-identity-and-controls.md)** carries identity, profiles and the alarm
(steps 1-6 and 8); **[1c](stage-01c-preventive-policies.md)** carries step 7, the policies, the one part
that is not freely reversible; **[1d](stage-01d-org-wide-enablement.md)** carries steps 9-11 — the audit
trail, the Config decision, the org-wide enablements. **The step numbers are the original ones**, so a
reference to `1c step 7` or `1d step 9` names the step it always did.

---

**Pre-flight, before step 1: the account quota.** It is the one item here that can stall for days. AWS
Organizations caps the number of accounts an organization may hold, and the cap on a young organization is
low. **Measured on 2026-08-08: this organization's limit is 10 accounts** — exactly the number this stage
ends with (Management plus the member accounts). It does not fit: an **older AWS account, predating this
project, is already attached to the organization** and consumes a slot, so the set is **eleven against a
cap of ten**.

- **A quota increase was requested at 15** (Service Quotas → AWS Organizations → "Maximum number of
  accounts"; a global setting, but the request is filed from `us-east-1`), recorded in
  `docs/log/log-stage-01a-landing-zone.md` as *requested*. **Confirm it was granted before vending the last
  accounts** — the granted value goes in the same file.
- **Until it is granted, defer `Staging`.** Its first hard dependency is Stage 8 and D20 keeps it unpeered
  from everything, so nothing earlier waits on it. D34 withdrew the retirement of the only identity that
  can vend, so no ordering trap is left and this is a scheduling choice.

**What the deferral leaves owed.** Each stage below carries its own "skip the Staging cell" note, which is
right for someone executing that stage and useless for someone vending the account six weeks later. **When
`Staging` is vended, work this list**, and record it in `docs/log/log-stage-01a-landing-zone.md` beside the
vend itself:

| Owed by | What |
|---|---|
| [1b step 3](stage-01b-identity-and-controls.md) | The `Staging` cells of the assignment table — `DataScientistStagingAccess`, and `DeploymentManagerAccess` on Staging. Both sets are **written in Stage 2 step 5**, so after Stage 2 this is an entry in the enumerated assignment list, not console work |
| [1b step 5](stage-01b-identity-and-controls.md) | The `awsds-infra-staging` profile, bound to this project's `InfrastructureAccess` |
| [1b step 6](stage-01b-identity-and-controls.md) | The AZ name→ID mapping for the account, before Stage 3 writes a subnet for it |
| [1c step 7.4](stage-01c-preventive-policies.md) | Account-level S3 Block Public Access. **Decision 7 settled it (2026-08-13): the root deny carries a carve-out for `InfrastructureAccess`**, so this is still possible after the vend — from `awsds-infra-staging` and from nothing else. Do it at the vend anyway; the carve-out makes it recoverable, not automatic |
| [1c step 7.7](stage-01c-preventive-policies.md) | Nothing extra *if* the account lands in the already-governed `Workloads` OU — confirm the controls enabled on that OU reached it, rather than assuming inheritance |
| [Stage 2 step 3](stage-02-terraform-foundation.md) | `terraform-live/staging/bootstrap/` — its state bucket and KMS key |

The first and the fourth change character with time: after Stage 2 the identity half is code, and after 1c
the BPA half may no longer be possible at all.

A thin margin has two consequences:

- A failed Account Factory provisioning that has to be retried can consume a slot, and a **closed account
  still counts against the quota** for the post-closure retention window (~90 days). The first retry is
  also the first quota breach.
- `Policy Canary` is disposable by design (D29). With zero margin it is not: closing it does not free the
  slot for ~90 days.

The increase is free and the support ticket can take days, so file it before anything else. **Quota
headroom is a standing item after this stage (D34)**, because vending is a standing capability. Under
**D35** the recurring consumer is **one slot per business unit**, since `Sandbox` is the account that
multiplies.

**To execute (all manual, by the user, recorded in `docs/log/log-stage-01a-landing-zone.md`):**

1. **Secure the Management account root user**, which under D16 is also the break-glass credential — this
   step and step 5 are two halves of one thing. MFA enabled (D16 leaves the *type* open; the user already
   has one configured on this root, so this is a confirm), strong password stored offline, **no access
   keys, ever**, billing alerts enabled. Two details:
   - **The password lives neither in this repository nor in `secrets/`** — offline means a password manager
     or paper, not a git-ignored folder.
   - **Check how many MFA devices are registered.** With exactly one, losing it means the AWS account
     recovery process, which depends on the phone number and payment method on the account — confirm both
     are current while you are here.
2. Create a Budget of **USD 50/month** (D12). **The e-mail alerts at 50%/80%/100% and Cost Anomaly
   Detection were skipped by decision on 2026-08-09**, so the budget is a figure in a console rather than a
   notification and **overspend is discovered by looking**. The optional budget *action* that attaches a
   deny-compute SCP at 100% was not built either; it is the only mechanism here that would act unwatched,
   so it is the first thing to revisit if the skip is undone.
3. Enable AWS Control Tower with `us-west-2` as the home region. It creates the Organization, the Log
   Archive and the Audit accounts (e-mails already in `secrets/emails.md`), and turns on org-wide CloudTrail
   and Config. The home region cannot be changed afterwards without redeploying the landing zone.

   **The wizard asks for two OU names, both awkward to change later.** The foundational security OU
   defaults to `Security` — keep it, D23 uses that name. The additional OU defaults to **`Sandbox`**: do
   not accept it, because this project has a `Sandbox` **account** and the collision makes every later
   sentence about SCPs ambiguous. Name it `Interactive` — the OU D23 wants anyway — or give it a throwaway
   name and create the real OUs in step 4.

   **What the landing zone creates without being asked (D33).** It builds an Identity Center directory and
   populates it: Control Tower's own groups (`AWSAccountFactory`, `AWSControlTowerAdmins`, the auditor
   groups), its own permission sets — including one named **`AWSAdministratorAccess`** — and a first
   administrator. That administrator is an Identity Center user with display name **`AWS Control Tower
   Admin`**, carrying the **Management account's root e-mail** and belonging to both `AWSAccountFactory` and
   `AWSControlTowerAdmins`; it announces itself as an *"Invitation to join AWS IAM Identity Center"* in that
   inbox. Those two memberships reach further than the Management account: `AWSControlTowerAdmins` is
   `AWSAdministratorAccess` on **Management, Log Archive and Audit**, plus `AWSOrganizationsFullAccess` on
   every member account. No field in the wizard asked about any of it (Lesson 17). Do three things before
   step 4 needs them:
   - **Set the AWS access portal URL** (IAM Identity Center → Settings) and record it in `secrets/emails.md`.
     It is the sign-in path for every human from this point on.
   - **Accept the invitation and put MFA on that user.** It administers the Management account *and* the
     Log Archive account, so it can delete the organization CloudTrail record of its own use, including the
     trail step 5's alarm reads. The reach cannot be trimmed while it is in use: `AWSControlTowerAdmins` is
     atomic, and the Management administrator this stage runs on comes in the same membership as the Log
     Archive one.
   - **Note it as the standing owner of Control Tower administration (D34, amending D33)** — it vends the
     accounts in step 4 and **keeps** that job afterwards: OUs, account vending, enrolment, landing-zone
     updates, from the console and never from Terraform. It is **not one of the five personas**: it holds
     one duty, approves nothing, and joins no project group. Its permanence makes three things
     non-optional — **MFA here**, **Object Lock in compliance mode** (1d step 9), and the
     **group-membership alarm** (1b step 8).
4. Create the `Sandbox`, `Development`, `Staging`, `Production`, `Data Governance`, `Identity` and
   `Policy Canary` accounts through Account Factory, using the e-mails in `secrets/emails.md`.

   **Sign in at the access portal first: Account Factory cannot be driven from root (D33).** From the root
   user the console returns *"Your AWS IAM identity does not have access to the AWS Control Tower Account
   Factory portfolio in AWS Service Catalog"*. Account Factory is a Service Catalog product whose portfolio
   grants access to IAM users, groups and roles; AWS states that provisioning requires
   `AWSServiceCatalogEndUserFullAccess` and that you **cannot be signed in as the root user**, and there is
   no principal to associate for root. The path is **access portal → `AWS Control Tower Admin` →
   `AWSAdministratorAccess` on the Management account → Control Tower → Account Factory**. Confirmed
   working on 2026-08-09.

   **Account Factory asks for two e-mail addresses and only one is the account's (D32).** The
   `Account email` becomes the vended account's **root** user. The second, under **Access configuration**
   (`SSOUserEmail`, with a first and last name beside it), is a permission decision: AWS's wording is that
   this user *"will have administrative access to the account you're provisioning"*. Fill it with the
   **infrastructure user** (address in `secrets/emails.md`; first/last name `Infrastructure` / `User`) and
   use **the same address on every account vended, here and later (D34)**. Account Factory recognises the
   existing Identity Center user and adds one more assignment instead of creating a second one, so the
   result is a single administrator with a single MFA device — the bootstrap access Stage 2 needs in order
   to run Terraform without root. Three ways to get this wrong, none of them cheap to undo:
   - **Do not reuse the account's own address here.** AWS permits it; this plan does not. That address is
     the root user, and step 5 alarms on root sign-in while step 6 removes root credentials centrally: an
     address that is also a daily login makes the alarm ambiguous and hands one inbox both the credential
     and its own warning.
   - **Do not use any of the other four personas.** The field grants administrator, so a data scientist or
     any of the three approvers placed here holds the separation of duties `docs/ORGANIZATION.md`
     describes before it has been built (Lesson 9).
   - **Do not treat it as changeable later.** Updating the provisioned product with a different
     `SSOUserEmail` **creates a second Identity Center user and leaves the first one in place** — a dormant
     administrator, the thing step 6 removes on the root side.

   **Two consequences, both picked up in 1b.** The infrastructure user **exists in Identity Center before
   1b step 2 runs**, so that step creates four users and not five. And every vended account is left holding
   a *direct* administrator assignment, outside the group model — **not removed here, and not removed by
   default**; D32 says when and whether.

   **Create the OUs from the Control Tower console, not from AWS Organizations.** An OU created directly in
   Organizations is not *registered* with Control Tower: Account Factory will not provision into it, the
   guardrails do not apply, and the accounts that land there are unenrolled — a state that looks correct in
   the Organizations tree and is not. Registering an OU afterwards is possible, and is extra work. The OUs,
   per D23, each named for the policy set it carries:
   - `Interactive` OU → `Development`, plus a nested **`Sandboxes` OU** holding the `Sandbox` accounts, one
     per business unit (D35). Interactive compute is *allowed*: unlike `Workloads` and `Data`, nothing here
     denies it. **This OU carries no set of its own**, and 1b step 7 holds the choice of whether to give it
     one. It is the only OU into which project blueprints may provision (D26). **If a set is written,
     attach it to `Interactive`, not to `Sandboxes`** — the nested OU carries none of its own and inherits,
     which is what makes a newly vended unit governed the moment it lands. Created this way on 2026-08-09
     (`docs/log/log-stage-01a-landing-zone.md`), which is why the organization's OU nesting depth is 2 —
     Stage 2 writes its `for_each` against that.
   - `Data` OU → `Data Governance` (D22, D26, D27). **No *user* compute**: the SCP denies EC2 and SageMaker
     outright, plus Glue job creation and execution (D25), and the set's other job is deletion protection.
     Two carve-outs. `datazone:*` is permitted because a DataZone domain is a governance control plane — it
     grants and records, it does not run anyone's code (D26). `glue:CreateCrawler`/`StartCrawler` plus the
     table-optimizer and column-statistics actions are permitted **only when the principal is the lake's
     catalog-maintenance role** (D27), which *is* real compute and is therefore bounded by role,
     event-driven and alarmed. Anything not on those two lists stays denied.
     **This OU is also the sole exception to an organization-root deny** (1c step 7): `datazone:CreateDomain`
     is denied everywhere and carved out here, so the unified domain can exist only in this account. SCPs
     are ceilings and an explicit `Deny` wins wherever it appears, so the exception is a **condition on the
     root deny** naming this OU, never an `Allow` written in this OU's own policy set.
   - `Workloads` OU → `Staging` and `Production` (D20). No interactive compute, no human control plane,
     written once and attached once. The `Policy Test` OU below is what the industry calls a *Policy
     Staging OU*; this plan does not use that name, so that `Staging` names one thing in this organization.
   - `Policy Test` OU → `Policy Canary` (D29). **Carries no policy set of its own**: it is where a
     *candidate* SCP or RCP is attached and exercised before it goes anywhere real, which is what 1b step 7
     needs. The account inside it is empty by design — no VPC, no data, no Terraform slice, no state
     bucket, no `awsds-infra-*` profile. It holds **an administrator principal**, assigned in 1b step 3,
     because an SCP is a permission *ceiling* and testing it with a restricted principal measures the
     identity policy instead. Enroll it through Account Factory like the others: an OU that is not
     registered with Control Tower does not inherit the CT controls, so a policy tested there meets a
     different baseline than the one it will meet in production, and that produces a false pass.
   - `Security` OU → the Log Archive and Audit accounts Control Tower created, **and nothing else.**
     `Identity` was meant to join them and could not: the vend was refused on 2026-08-09
     (`docs/log/log-stage-01a-landing-zone.md`). `Security` is a *foundational* OU in Control Tower's
     model, and an account Control Tower did not create does not join one.
   - `Identity` OU → `Identity`, the fallback this step named. **Measured on 2026-08-13**: the OU carries
     `aws-guardrails-coSzJr`, Control Tower's standard eight statements, the same document every other
     registered OU has — it was registered when it was created, so it inherits the same baseline. What
     `Security` carries beyond that is three statements about the log-archive and audit buckets, which mean
     nothing for an account that holds neither. **Still compare the two OUs' *enabled controls* in 1c step
     7.0 step 3**: that is a different registration from the SCP and is still unread. This is the account
     whose administrator can grant access to every other account.

   **The accounts listed above are the complete set *for this stage*, not the complete set (D34).** D14
   places the tooling in Production rather than in a separate Shared Services account; D20-D22 add the
   deployment target, the development account and the data account the AWS reference architectures
   describe; D29 adds the disposable one that makes the SCP procedure in 1c step 7 executable.
   `docs/plan/institutional-delta.md` records what a larger organization would still add beyond them.
   **An account added later is an ordinary event**: D34 carries the flow — the gate is which axis and which
   OU the account needs (D23), the owner is `AWS Control Tower Admin`, and the post-vend baseline is code
   that already exists (`bootstrap/`, the identity slice, `foundation/`, an SSO profile). **An account may
   therefore be deferred without a structural cost**, so if the quota increase has not been granted, vend
   what fits and vend the rest afterwards. Account creation here is manual through Account Factory;
   **Account Factory for Terraform (AFT)** is the automated equivalent and is not used — what keeps it out
   is measured cost (`docs/plan/institutional-delta.md`).
5. **Break-glass: the procedure and the alarm (D16).** Three deliverables: the procedure written down, the
   alarm chain built, and the whole thing tested once. The first is done —
   [`docs/plan/runbooks/break-glass.md`](../runbooks/break-glass.md), whose §0 carries why this step exists
   and whose §7 is the reference copy of the chain below. What follows is only the procedure.

   **Sign in as `AWS Control Tower Admin` → `AWSAdministratorAccess` on the Management account, region
   `us-west-2`.** The whole chain is built from that session; root is needed only in 5.5, to fire the alarm.

   **5.0 — The endpoints the alarm notifies, chosen before the console is open.** Pick the **e-mail
   address** (a dedicated alias, *not* the root address — runbook §0 says why) and the **mobile number** for
   the SMS endpoint, and register both in `secrets/emails.md`. That file is the user's and is git-ignored:
   neither value is ever copied into this repository.

   **5.1 — Verify what the landing zone already delivered. Build nothing yet.**
   - **CloudWatch → Logs → Log Management → Log groups** must contain **`aws-controltower/CloudTrailLogs`**.
     From landing zone 3.0 it is created **only in the Management account** (earlier versions put one in
     every enrolled account), which is why the filter goes here and not in Log Archive.
   - **CloudTrail → Trails → `aws-controltower-BaselineCloudTrail`** must show **Multi-region: Yes** and
     **Global service events: Yes**. **Root console sign-in is recorded in `us-east-1`**, because console
     sign-in is a global service in CloudTrail, so a new single-Region trail in `us-west-2` would not see
     the event at all. That is why this chain hangs off the existing organization trail.
   - Being an *organization* trail, member-account events land in this same log group, so **one metric
     filter covers every account** — useful until step 6 removes the member roots, and a backstop after.
   - **Do not modify the trail**: an edit is landing-zone drift. Adding a *metric filter* to the log group
     is not — it is a separate resource, and the log group survives even a decommission.
   - **If the log group is absent** (a landing zone set up without CloudWatch Logs), stop and re-plan: the
     fallback is a second, Management-only trail, which changes both the cost and the steps below.

   **5.2 — The SNS topic and its subscriptions.** SNS in `us-west-2`, **Standard** topic:
   - Name `awsds-org-break-glass-alerts`; **Display name** set (SMS requires one — it becomes the sender
     prefix).
   - **Leave encryption off.** With SSE under the AWS-managed `aws/sns` key, a CloudWatch alarm **cannot
     publish**: the CloudWatch service principal has no `kms:GenerateDataKey` on it, and the alarm fails
     silently (Lesson 13). Encrypting would require a customer-managed key with an explicit key policy.
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
     metered only for the hours it actually publishes, so with no default value a quiet month costs nothing
     (`docs/PRICING.md` §6). The price of that choice is paid in 5.4.

   **5.4 — The alarm.** CloudWatch → Alarms → Create → metric `AWSDS/Security` / `RootActivityCount`:
   - **Sum**, period **1 minute**, static threshold **≥ 1**, **1 of 1** datapoints.
   - **Missing data: `notBreaching`.** This is the price of 5.3: with no default value the metric publishes
     nothing while all is well, and any other setting turns silence into an alarm or an
     `INSUFFICIENT_DATA` that hides one.
   - Name `awsds-org-root-activity`; **In alarm** action → the topic from 5.2.

   **5.5 — Test the chain.** Sign in as Management root, do nothing, sign out. Allow **up to ~15 minutes**
   end to end (CloudTrail delivery → CloudWatch Logs → metric → alarm → SNS); past ~20 minutes it is a
   failure, not latency. Confirm the message arrived on **both** channels — a missing channel is a finding —
   and that the alarm returns to `OK` on its own.

   **5.6 — Record it.** Resource names and the test result in `docs/log/log-stage-01a-landing-zone.md` (the
   user's file), and the date in the **Last tested** row of the runbook.
6. **Centralized root access management.** Every member account — the ones Control Tower created (Log
   Archive, Audit) and the ones Account Factory created — arrives with its own root user and its own
   recovery e-mail: one dormant credential per account, none of which anybody will ever rotate, each
   re-obtainable by whoever holds that inbox. AWS Organizations can remove those credentials centrally and
   perform the few genuinely root-only actions on demand, as short sessions. **It does not touch the
   Management account root**, so it composes with D16: every member root disappears, one root remains, and
   that one is the break-glass.

   **6.0 — Sign in as `AWS Control Tower Admin` → `AWSAdministratorAccess` on the Management account.**
   Not as root: **`sts:AssumeRoot` cannot be called by a root user**, and every privileged action below is a
   root session. Same shape as step 4's Account Factory refusal (D33) — vending and this are the two
   Management-account jobs root cannot do.

   **6.1 — Do this before the `Staging` vend, if the quota allows.** Accounts created in Organizations
   *after* the feature is on have **no root credentials at all**, so `Staging` would be born clean and 6.4
   would never have to touch it. Nothing breaks in the other order; it costs one account's worth of manual
   work.

   **6.2 — Enable the feature.** IAM console (Management account) → **Root access management** → **Enable**:
   - Enable **both** capabilities. `Root credentials management` is the deletion; **`Privileged root actions
     in member accounts` is the way back** — without it `Allow password recovery` does not exist, and a
     deleted root has no documented path to restore it. AWS states the dependency plainly.
   - **Leave `Delegated administrator` empty.** The natural candidate is the `Identity` account by analogy
     with D10, and that analogy is why it waits: the account is vended and otherwise bare until 1b, and this
     delegation grants root sessions into **every** account in the organization. Deferring costs one
     reversible API call.
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
   **that report is the only time anybody will look at that account's root**: anything in it other than
   "nothing" belongs in `docs/log/log-stage-01a-landing-zone.md`. The deletion removes password, access keys
   and signing certificates and deactivates MFA. **There is no bulk action in the console**; the per-account
   CLI equivalent is

   ```bash
   aws sts assume-root --target-principal <account-id> --task-policy-arn arn=arn:aws:iam::aws:policy/root-task/IAMDeleteRootUserCredentials --duration-seconds 900 --region us-west-2
   ```

   followed by `delete-login-profile`, `delete-access-key`, `delete-signing-certificate` and
   `deactivate-mfa-device` under the returned credentials (`sts:AssumeRoot` has **no global endpoint** — the
   `--region` is required — and the session is capped at 900 seconds). The member accounts today are
   `Log Archive`, `Audit`, `Development`, `Sandbox Account 1`, `Production`, `Data Governance`,
   `Policy Canary` and `Identity`, plus `Staging` unless 6.1 made it moot — below the threshold where
   scripting a privileged path earns its own risk.

   **6.5 — Expect the break-glass alarm to fire; take it as the second test of step 5.** The *actions*
   inside a privileged session are logged in the target account as `userIdentity.type = "Root"`, which is
   what 5.3's filter matches, and the trail is org-wide, so **every deletion pages both channels**. From
   here on the alarm means "root activity anywhere", and a privileged session is told apart from a real root
   sign-in only by correlating the `sts.amazonaws.com` `AssumeRoot` event (`sessionContext.assumedRoot =
   true`, plus `requestParameters.targetPrincipal`) with the `accessKeyId` on the member-account events.
   **If nothing arrives on both channels here, step 5 never worked**:
   `docs/log/log-stage-01a-landing-zone.md` records the 5.5 test as performed but not its result, so this is
   where that gets settled.

   **6.6 — What it costs, and the reversal.** Afterwards a member account cannot sign in as root and cannot
   run password recovery; anything genuinely root-only there is done from Management as a ≤15-minute session,
   and **only five task policies exist** (audit credentials, create root password, delete credentials, unlock
   an S3 bucket policy, unlock an SQS queue policy). Two of those five are the "I denied myself" repairs. The
   one capability this design might have wanted and cannot have from inside the account is **S3 MFA
   Delete**, which requires that account's own root; 1d step 9 uses Object Lock in compliance mode instead.
   Reversal: **Allow password recovery** on that account (only offered once the credentials are gone), reset
   from the root inbox, do the task, delete again.

   **6.7 — Carry one consequence into 1c step 7.** Control Tower's strongly-recommended control
   **`AWS-GR_RESTRICT_ROOT_USER`** denies `*` where `aws:PrincipalArn` matches `arn:*:iam::*:root`, which
   **also denies privileged root sessions**, because in the member account they *are* that principal. It is
   **not enabled by default**, so nothing is broken today. If 1c step 7 enables it (or writes the
   hand-rolled equivalent), it must carry the **`ExemptAssumeRoot`** parameter, which adds
   `"Null": {"aws:AssumedRoot": "true"}` to the condition. Without that, the guardrail denies this step's
   own recovery action.

   **6.8 — Record it in `docs/log/log-stage-01a-landing-zone.md`**: date, which capabilities were enabled,
   whether a delegated administrator was set, what each account's credential report showed, and whether both
   alarm channels fired.

**Deliverables of 1a:** every account exists, in its OU, each with the **same** infrastructure user holding
administrative access through Identity Center (D32) — one user in the directory, not seven; the Management
root user is secured and its break-glass path has been tested once; member-account root credentials are
centrally managed; the USD 50 budget exists, **with no alert thresholds and no Cost Anomaly Detection
beside it** (skipped by decision — step 2). The `AWS Control Tower Admin` user exists, has MFA, and
**stays** — it is the standing owner of Control Tower administration (D34). Nothing here is torn down
between sessions, and nothing after this point can lock you out without a way back in.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
