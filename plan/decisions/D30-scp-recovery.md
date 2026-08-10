# D30 — The SCP recovery principal — a named role exempt from every custom deny

**Status:** **Reverted (2026-08-08)** by the user's decision, after being adopted earlier the same day. **There is no standing SCP exemption in this design. The break-glass credential is the Management account root and nothing else (D16).** `awsds-scp-recovery` is not built, in any account.

**In one line:** Proposed, recommended against, adopted, then reverted the same day — the lab keeps a single recovery path, the Management root, and no principal stands outside its own guardrails.

**Related decisions:** [D16](D16-break-glass.md), [D29](D29-policy-canary.md), [D10](D10-identity-center-delegation.md), [D27](D27-catalog-maintenance.md)

**Referenced by stages:** — (the stages that used to consume it no longer do: [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 2](../stages/stage-02-terraform-foundation.md), [Stage 3](../stages/stage-03-networking.md))

---

## What survives this decision, and it is the part that matters

**The SCPs, RCPs and tag policies stay in code**, in `terraform-live/identity/org-policies/`, imported in Stage 2 step 5. D30 is what first forced them out of the console, but the reason it gave was only the *proximate* one ("a carve-out condition typed four times is a condition that will exist in three of them"). The *durable* reason is older and independent: until D30 no stage owned those policies after Stage 1b created them by hand, nothing imported them, and the only record of what they said was the console. That hole is real whether or not any carve-out exists, and the SCP set is the single most dangerous artefact in this plan to hold only in a browser tab. **So the consequence is kept and re-attributed** — see Stage 2 step 5, which no longer cites this decision as its reason.

Likewise the generalisable half of Lesson 14 survives the specific case that produced it: any condition that must appear in N places gets **generated, not typed**, and any ARN condition gets an **enumerated list, never a wildcard account**.

---

## Rationale — why it was recommended against, why it was adopted, and why it was reverted

**Recommended against, originally.** With root as the break-glass credential (D16), the recovery path already exists without a hole: SCPs never apply to the Management account, so a mistaken policy can always be detached from there. A standing exemption buys convenience against a hazard that already has an answer, and pays for it with a principal permanently outside every guardrail the project writes.

**Adopted anyway**, for two reasons that were not "we need it to recover": (i) fixing a policy in place would keep repairs out of the Management console, which principle 1 wants touched as little as possible; (ii) the carve-out condition is a real production pattern with real sharp edges, and building it once is the kind of thing `plan/institutional-delta.md` says this lab exists to learn.

**Reverted, and the reason is the more interesting half of this record.** The pre-Stage-1 review that examined the adopted design found that **the role could not be delivered where its own argument needed it**, and that reason (i) above did not survive contact with the rest of the plan:

- **The role does not repair the policy.** Being exempt from a `Deny` means the principal can perform the denied *action* inside that account. Detaching or editing an SCP is an `organizations:*` call, which is made from the Management account or from the delegated policy administrator — not from the account the deny is hurting. So "repair in place" was never quite what the role did.
- **The account where the repair actually happens is `Identity`** — D30 itself moved the SCPs to `terraform-live/identity/org-policies/`, applied with the delegated-admin profile. A mis-written organization-root SCP (the region restriction is the obvious candidate: Identity Center is regional and `organizations:*` answers in `us-east-1`) denies *that* account the call that would fix the policy.
- **And `Identity` was one of the accounts the design could not reach.** The role was to be created in each account's `foundation/` slice, and `foundation/` exists only where there is a VPC. `Data Governance` has none by decision (D22) and `Identity` has only `bootstrap/`. The delivered design would therefore have placed the exemption in every account where it was a convenience and omitted it from the one where it was the mechanism. The `Policy Canary` battery in Stage 1c step 7 had the same problem in a sharper form: it instructed the operator to assume the role in an account D29 defines as holding no Terraform slice at all.

That is Lesson 3 and Lesson 11 applied to this decision: D30 was adopted in the same pass that moved the SCPs into the Identity account, and nobody re-read its scope against that move. Given the choice between engineering the scope out (a minimal `foundation/` for two accounts, a hand-made role in the canary, an enumerated ARN list maintained across all of them) and removing the exemption, **the user chose to remove it.** The lab returns to the institutional answer, which `plan/institutional-delta.md` had recorded all along: no standing exemption; the policy is detached from the Management account by whoever owns it.

**What the revert costs, stated rather than hidden.** A mistaken SCP now has exactly one repair path, and it runs through the Management root — a credential that cannot be scoped, whose every compensating control is detective (D16). Three things already in the plan carry that weight, and they stop being hygiene:

1. **The `Policy Canary` battery (D29) is now the primary defence, not a nicety** — a bad policy is far cheaper to catch before attachment than to repair after it.
2. **Stage 1a step 5 requires the break-glass path to be built and fired once *before* any policy is attached.** That ordering was already deliberate; it is now the thing standing between a mistake and a locked organization.
3. **Stage 1c step 7's "with the detach command written down and the Management account already open before the first attach"** is no longer belt-and-braces. It is the procedure.

**On the revision trigger, because it is worth noticing that it did not fire.** D30's recorded triggers were "a second person gains access" and "the role is assumed for anything other than repairing a policy". Neither happened; what happened was a review finding the decision undeliverable as scoped. A trigger written only about *operating* the thing cannot catch a defect in *building* it — worth remembering when writing the next one.

**If this is ever revisited**, the shape to revisit it in is the institutional one rather than the original: not a standing exemption, but an incident-scoped role elevated for a bounded window and expiring on its own.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
