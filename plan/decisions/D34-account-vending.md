# D34 — Account vending is a standing capability, not a bootstrap job

**Status:** Decided (2026-08-09): **`AWS Control Tower Admin` is kept enabled as the standing owner of Control Tower administration — OUs and accounts, from the console, never from Terraform. D33's retirement is withdrawn**

**In one line:** The account list is not static, so the ability to create accounts and OUs gets a permanent owner instead of an end date — and the Organization staying outside Terraform is exactly why console vending cannot make any state inconsistent.

**Related decisions:** [D16](D16-break-glass.md), [D23](D23-ou-structure.md), [D29](D29-policy-canary.md), [D32](D32-account-factory-sso-user.md), [D33](D33-control-tower-admin-user.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 2](../stages/stage-02-terraform-foundation.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

**Refined by [D35](D35-sandbox-cardinality.md):** this decision says the account list is not static; D35 says *which part* of it is not — everything structural keeps the console flow below, while `Sandbox` alone multiplies per business unit and gets an automated one (Stage 14).

---

## Rationale and consequences

**What changed is the premise, not the mechanism.** D33 sized this user as "a bootstrap credential with a
defined end" on the strength of one sentence — vending "is a finite job that ends inside Stage 1a" — and
`plan/institutional-delta.md` rejected AFT on the same premise, "created once". The premise is false. A
sandbox for a different line of work, a second data domain, a per-workload staging account are ordinary
requests, and each of them is an account. **D33 anticipated this in its own revision trigger** — *"any stage
after 1a needs Account Factory, at which point the owner question above must be answered rather than
deferred"* — so this decision is that trigger firing, not a reversal of its reasoning. It is also Lesson 7
applied to a *frequency* premise instead of a price: a rejection that rests on "this happens once" goes stale
in the direction that flatters the rejection.

**The decision.** `AWS Control Tower Admin` stays enabled and is the named owner of Control Tower
administration: creating OUs, vending accounts through Account Factory, enrolling accounts, and landing-zone
updates. Console only, no Terraform. It is recorded in `secrets/emails.md` (by the user, 2026-08-09) and in
`ORGANIZATION.md`.

**Why this identity and not the narrow path, which D33 preferred.** The job splits into two classes and only
one of them fits `AWSAccountFactory`:

- **vending an account into an OU that already exists** → `AWSServiceCatalogEndUserAccess` on Management, from
  the **Service Catalog** console. Narrow, and enough.
- **creating an OU, enrolling an existing account, updating the landing zone** → the **Control Tower console**,
  which AWS documents as reachable only by members of `AWSControlTowerAdmins`.

Creating OUs is explicitly part of the stated job, so the narrow path does not cover it; and splitting the
job across two identities to avoid a permission that one of them holds anyway buys nothing. What the choice
does buy, and it is the reason to write it down rather than assume it: **the infrastructure user gains no
Management-account reach**, so D32's shape — one administrator, one MFA device, over the vended accounts —
survives intact.

**What this costs, stated as a permanent condition rather than as a window.** D33 sized the exposure as "MFA
plus a short window" and the window is now open-ended, so the control set has to be restated with the
mechanism named (Lesson 5), not merely re-promised:

- **MFA on this user is the standing control**, not a stopgap for a few days.
- **Stage 1b step 9's Object Lock must be in *compliance* mode.** This principal is administrator *of Log
  Archive*, so it holds `s3:BypassGovernanceRetention` and governance mode is transparent to it. Compliance
  mode is now the only thing that keeps the audit trail surviving its own administrator, indefinitely.
- **Stage 1b step 8's alarm on Control Tower group membership stays and gains a second reason:** with this
  user standing, the cheapest way to acquire its reach is to be added to its group.
- **The inbox collision is permanent.** The login address is the Management root's, so the break-glass SNS
  subscription (Stage 1a step 5) must be a different address — and, since every address here is a `+alias` on
  one mailbox, the **SMS endpoint** is the only part of that separation that is real.
- **Do not repoint it at a non-root address.** D33's argument is untouched by this decision and is stronger
  under it: Control Tower owns the object, a landing-zone update may re-create it under the root address, and
  the renamed one would be left behind as a dormant administrator.
- **Separation of duties: none, and that is the honest word.** The identity that creates accounts also
  administers the account holding the audit trail, and nobody approves a vend. One human, one lab; recorded
  in `plan/institutional-delta.md` rather than argued away.

## Terraform state — why console vending is safe, and what replaces drift

**It cannot make any Terraform state inconsistent, and the reason is structural.** No state in this project
manages the Organization: principle 1 keeps the Management account out of Terraform entirely, so
`aws_organizations_account` and `aws_organizations_organizational_unit` are declared nowhere, and a state file
only ever tracks what a configuration declares. There is nothing to drift, before or after Terraform starts
holding state elsewhere.

**The failure mode that replaces drift is the one to design against, because it is silent.** Drift is code and
reality disagreeing, and `terraform plan` reports it. This is reality holding something the code never
mentioned, and `terraform plan` reports **"No changes"**. A console-vended account is *invisible*, not
*drifted* — and three of the things Stage 2 moves into `terraform-live/identity/` are exactly where that
matters:

- **SCP/RCP attachments**, which attach to **OUs**. An OU created from the console carries no policy set until
  code attaches one.
- **Permission set assignments.** A vended account arrives holding only the direct Account Factory assignment
  (D32) and nothing from the group model.
- **Enumerated ARN and account-ID conditions**, which `plan/conventions.md` requires to be lists rather than
  wildcards. A new account is silently outside every one of them — Lesson 14, arriving through a new door.

**The rule, and it is a mechanism rather than a checklist line: the floor is discovered, the grants are
enumerated.** In `terraform-live/identity/`, anything that must cover *everything* — the organization-root
SCP/RCP set, the tag policy, the per-OU attachments — is driven by `for_each` over
`aws_organizations_organizational_units` / `aws_organizations_organization` data sources, so an OU or account
created yesterday from the console is covered by the next apply with nobody remembering. Permission set
assignments stay **explicit**, because a new account silently acquiring `DataScientistAccess` is precisely the
failure this design exists to prevent. *To verify while writing Stage 2:* that the data sources enumerate OUs
at the nesting depth this organization actually uses — **answered on 2026-08-09 and the answer is 2**
(D23: `Sandboxes` under `Interactive`), so a single-level enumeration over the root's children misses every
Sandbox account — and that the `for_each` key is stable enough that adding
an OU does not re-create the existing attachments.

## The flow, which is what makes an added account cheap

1. **The gate is the axis and the OU, and it comes before the account exists.** A new account declares which
   axis it is on — lifecycle, ownership, or platform — and which OU's policy set it needs. If an existing set
   fits, and "another sandbox" almost always means the `Interactive` set, the account joins that OU and
   inherits SCP, RCP, tag policy and the region control for free. If no set fits, **the request is an OU
   decision, not an account decision** (D23: an OU earns its existence when two or more accounts need the same
   policy set), and it goes through the `Policy Canary` battery (D29) before it is attached anywhere real.
2. **The owner is `AWS Control Tower Admin`**, per the decision above.
3. **The post-vend baseline is code that already exists**, which is the whole reason account N+1 is cheap:
   `terraform-live/<env>/bootstrap/` for the state bucket, the identity slice for the assignments, OU
   membership for the policy set, `foundation/` if the account needs a VPC, an `awsds-infra-<env>` SSO profile,
   and the mandatory tags. **For an interactive account, name what it actually pulls in** — Stage 3 (VPC,
   private hosted zone associations), Stage 4 (peering and VPN reach), Stage 6 (domain association and a
   project profile). That list is what makes the real cost of "just one more sandbox" visible at the moment
   somebody asks for it, which is the point of having a gate at all.
4. **Quota headroom is a standing item, not a stage pre-flight.** Keep slack for a failed provisioning that has
   to be retried; a closed account holds both its slot and its e-mail address for ~90 days; addresses follow
   the `+alias` convention already in `secrets/emails.md`.

**One consequence worth stating, because it removes a trap this plan had just acquired.** With no retirement
there is no "vend the account before disabling the only identity that can vend", so **deferring an account is
now a scheduling choice with no structural cost** — which is what makes postponing `Staging` until the quota
increase is granted an ordinary decision rather than an ordering hazard.

**There are three rungs here, not two, and naming only the outer ones is how the status quo wins by
forfeit.** A revision trigger offering a choice between "keep doing it by hand" and "adopt a whole product"
resolves itself: on the day it fires, AFT looks expensive — probably correctly — and the conclusion becomes
"so we carry on manually", with the middle option never considered. The ladder:

| Rung | What it is | What it costs |
|---|---|---|
| 1. **Today** | Account Factory from the console, by the owner above | nothing; the request has no diff and no review |
| 2. **The middle** | `aws_servicecatalog_provisioned_product` against the **Account Factory product**, with `AccountEmail`, `AccountName`, `ManagedOrganizationalUnit` and the SSO fields as provisioning parameters | one slice; a principal with Service Catalog rights **in Management**, which reopens the ownership question above; and `prevent_destroy`, because terminating that resource **closes an account** |
| 3. **AFT** | the full product: its own management account, pipelines, per-account customization repositories | a dedicated account slot plus metered services |

Rung 2 keeps the account being created **by Account Factory**, so Control Tower enrolment, guardrails and
baseline are untouched — it only moves who fills in the form. *To verify before writing it:* the product name
and the exact parameter keys, which change between landing-zone versions. **This is the rung
[Stage 14](../stages/stage-14-sandbox-vending.md) uses**, because D35 puts the one recurring account
(`Sandbox`, one per business unit) on a different footing from the structural ones.

**Revision trigger:** account creation becoming frequent enough that the post-vend baseline is run from memory
rather than read, or a second human joining — at which point the **ladder above** is walked from rung 1, not
jumped to rung 3, with the cost of whichever rung is chosen *measured* into `PRICING.md` first (Lesson 6),
including whether AFT requires a dedicated management account, which would itself consume an account slot.
Note what is **no longer** a trigger: Control Tower re-creating or re-enabling this user, which D33 tracked
because the plan promised a retirement. It promises one no longer.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
