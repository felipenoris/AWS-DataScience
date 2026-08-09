# D32 — Which Identity Center user Account Factory associates with each vended account

**Status:** Decided (2026-08-08): **the infrastructure user, the same one for every vended account**

**In one line:** Account Factory's `SSOUserEmail` is a permission decision, not a contact field — it gets the infrastructure user, identically on every account vended.

**Related decisions:** [D10](D10-identity-center-delegation.md), [D16](D16-break-glass.md), [D29](D29-policy-canary.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md)

---

## Rationale and consequences

**The field, and why it needed a decision at all.** Account Factory's form asks for **two** e-mail
addresses: the `Account email`, which becomes the vended account's **root** user, and a second one under
**Access configuration** (`SSOUserEmail`), which reads like a notification address and is not — AWS's own
wording is that this user *"will have administrative access to the account you're provisioning"*. Stage 1a
step 4 named only the first, so the second was going to be answered by whoever was at the keyboard, at the
moment they least wanted to think about identity design (Lesson 16). **The choice: the infrastructure
user** — its address as registered in `secrets/emails.md`, first/last name `Infrastructure` / `User` — **and the
same address on every vended account** (Sandbox, Development, Staging, Production, Data Governance,
Identity, Policy Canary in Stage 1a, and every account vended after it — D34 makes vending a standing
capability, so this value is chosen once and reused rather than being a list with an end). Account Factory
recognises the existing Identity Center user and adds one more
assignment rather than creating a second user, so the result is **one administrator, one MFA device, one
credential to protect**, holding admin everywhere. That is not a convenience: principle 2 says humans
authenticate through Identity Center and assume roles, and this is the concrete thing that lets **Stage 2
run `terraform apply` without ever touching root**. **Why not the account's own e-mail, which AWS permits.**
That address *is* the root user, and three separate parts of this stage are built on root being a dormant,
exceptional credential: step 6 removes member-account root credentials centrally, D16 reserves root for
break-glass and nothing else, and step 5 builds an alarm that fires on `userIdentity.type = Root`. An
address that is simultaneously the root recovery path and a daily federated login makes that alarm
ambiguous and hands the same inbox both the credential and its own warning. **Why not a throwaway
administrator per account.** Seven dormant administrators, each needing its own MFA, none of which anybody
will ever rotate — the exact shape of the problem step 6 exists to remove on the root side, recreated one
layer up in Identity Center. **Why not one of the other four personas.** The field grants *administrator*.
A data scientist, a deployment manager, a governance manager or a dev env steward placed here holds
administrative access to accounts the entire separation-of-duties argument in `ORGANIZATION.md` says
they must not (Lesson 9) — and holds it from stage one, before any of the permission sets that describe
their real reach exist. **Why not a placeholder to be replaced later**, which is the tempting third option:
updating the provisioned product with a different `SSOUserEmail` **creates a new Identity Center user and
does not remove the previous one** (documented behaviour). The placeholder does not get replaced; it gets
*joined*, and becomes precisely the dormant administrator this decision is avoiding. So the value is chosen
once, at vend time, deliberately. **Consequence 1 — the infrastructure user pre-dates Stage 1b.** 1b step 2
used to read as "create the five users"; it creates **four**, and the fifth is added to the `infrastructure`
group rather than re-created under a second address. **Consequence 2 — every vended account carries a
*direct* user assignment**, outside the group model 1b builds, of Control Tower's own administrator
permission set. **It is deliberately not removed during 1b**, and the order is the whole point: the
group-based path (`infrastructure` → `AdministratorAccess` → a real `sts:GetCallerIdentity` under each
profile) must be *proven* first, because since D30 was reverted the only thing behind a lockout is the
Management root. **And whether it can be removed at all is a verification, not an assumption:** Control
Tower may re-create the assignment on a landing-zone update, an account update or a re-enrollment, in which
case the honest outcome is to record the direct assignment as a permanent property of Account
Factory-vended accounts rather than to keep deleting something that keeps coming back. **Consequence 3 —
D29's test principal arrives early, for free.** `Policy Canary` needs an *administrator* or the SCP battery
measures the identity policy instead of the ceiling; vending it with this same `SSOUserEmail` gives it one
at creation time, so 1b step 3's assignment there becomes a confirmation rather than a task. That the
canary's admin is a direct assignment rather than a group one is fine — the account is deliberately outside
the Terraform-managed set and has no `awsds-infra-*` profile either. **Revision trigger:** a second human
gains infrastructure access — at which point a single shared bootstrap administrator stops being one
person's credential and the assignment has to be split, or moved wholly to the group model; **or** the
verification above finds that Control Tower re-creates the assignment, in which case this file stops
promising a cleanup and documents the permanent state instead.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
