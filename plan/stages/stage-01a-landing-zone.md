# Stage 1a — Landing zone, accounts and OUs

| | |
|---|---|
| **Status** | ready to start — nothing blocking |
| **Prerequisites** | none outstanding (D1 decided, all ten e-mails registered) |
| **Consumes** | [D1](../decisions/D01-region.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D16](../decisions/D16-break-glass.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D29](../decisions/D29-policy-canary.md) |
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
is low. **Measured on 2026-08-08: this organization's limit is 10 accounts** — exactly the number this stage
ends with (Management plus the member accounts), so it fits with **no margin at all**. Two consequences,
both of which bite at the worst moment:

- A failed Account Factory provisioning that has to be retried can consume a slot, and a **closed account
  still counts against the quota** while it is in the post-closure retention window (~90 days). So the
  first retry is also the first quota breach.
- `Policy Canary` is disposable *by design* (D29). With zero margin it is not actually disposable: closing
  it does not free the slot for ~90 days.

So **request a quota increase before enabling Control Tower** — Service Quotas, AWS Organizations,
"Maximum number of accounts", ask for something with headroom (15 is plenty). It is free, it is a support
ticket that can take days, and it is the only item in this stage that cannot be worked around once started.
Record the granted value in `LOG.md`.

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
4. Create the `Sandbox`, `Development`, `Staging`, `Production`, `Data Governance`, `Identity` and
   `Policy Canary` accounts through Account Factory, using the e-mails in `secrets/emails.md`.
   **Create the OUs from the Control Tower console, not from AWS Organizations.** An OU created directly in
   Organizations is not *registered* with Control Tower: Account Factory will not provision into it, the
   guardrails do not apply, and the accounts that land there are unenrolled — a state that looks correct in
   the Organizations tree and is not. Registering an OU afterwards is possible but is extra work at exactly
   the moment there is least appetite for it. OUs, per D23 — each named for the
   policy set it carries, not for its contents:
   - `Interactive` OU → `Sandbox` and `Development` (D21). Interactive compute *allowed*; human
     infrastructure changes denied. The only OU into which project blueprints may provision (D26).
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
   - `Security` OU → `Identity`, alongside the Log Archive and Audit accounts Control Tower created.
     **To verify while doing it:** the Security OU is a *foundational* OU in Control Tower's model and
     carries its own guardrail set, so placing a third, non-Control-Tower-created account in it is worth
     confirming rather than assuming. If it fights back, the fallback is a sibling `Identity` OU with the
     same policy set — the D23 test ("an OU earns its existence when two or more accounts need the same
     policy set") is not met by that, but a landing zone that will not enrol the account is worse.

   **The accounts listed above are the complete set** — D14 places the tooling in Production rather than in
   a separate Shared Services account, D20-D22 add the deployment target, the development account and
   the data account the AWS reference architectures describe, and D29 adds the disposable one that makes
   the SCP procedure in 1b step 7 executable. `plan/institutional-delta.md` records what a larger organization would still add
   beyond them.
   Account creation here is manual through Account Factory; **Account Factory for Terraform (AFT)** is the
   automated equivalent and is deliberately not used — at this handful of accounts, created once, it is at
   the edge of repaying its setup and still loses (`plan/institutional-delta.md`).
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
   own warning. Build the chain here and fire it once with a deliberate sign-in; an untested alarm is a
   hypothesis.
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

**Deliverables of 1a:** every account exists, in its OU; the Management root user is secured and its
break-glass path has been tested once; member-account root credentials are centrally managed; the budget
and Cost Anomaly Detection are live. Nothing here is torn down between sessions, and nothing after this
point can lock you out without a way back in.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
