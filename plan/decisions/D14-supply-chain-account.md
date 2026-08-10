# D14 — Where GitLab, Runners, ECR and CodeArtifact live

**Status:** Decided (2026-08-07): **the Production account**. **Revised 2026-08-09** — the decision stands,
its cost basis does not: see *What changed on 2026-08-09*.

**In one line:** GitLab, Runners, ECR and CodeArtifact live in Production, not next to the people the gate gates.

**Related decisions:** [D21](D21-development-account.md), [D20](D20-staging-account.md), [D23](D23-ou-structure.md), [D34](D34-account-vending.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 3](../stages/stage-03-networking.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 9](../stages/stage-09-deployment-targets.md)

---

## Rationale and consequences

These four are the software supply chain. In the Sandbox account they would sit next to a `sso-group-data-scientists` group with broad permissions, which means the runner holding the deploy credentials, and the registry Production pulls from, would both be modifiable by the people the approval gate is supposed to gate. Putting them in Production removes that path and costs no extra account. **Accepted trade-off:** build and runtime now share an account, so there is no blast-radius boundary between "the thing that builds" and "the thing that runs" — a compromise of GitLab is a compromise of Production. A large institution splits these into a Shared Services / Tooling account in an `Infrastructure` OU (`plan/institutional-delta.md`). **Consequences:** the Production VPC moves from Stage 9 to Stage 3; Sandbox↔Production VPC peering is needed so the VPN reaches GitLab (and, since D21, a second peering from Development); ECR and CodeArtifact are consumed cross-account from **both Interactive accounts**; and the data scientist needs a narrow, service-level (not infrastructure-level) reach into Production.

---

## What changed on 2026-08-09 — the rejection's cost basis

**The decision is unchanged. What is rewritten here is *why* the alternative stays rejected**, because the
original reason has gone stale in the direction that flatters it (Lesson 7). The sentence above —
"costs no extra account" — carried two distinct claims that have since separated:

- **"An extra account is expensive to create and own."** *Retired by [D34](D34-account-vending.md).* Vending
  an account is now an ordinary event with a named gate (which axis, which OU), a named owner
  (`AWS Control Tower Admin`) and a baseline made of code that already exists. This premise no longer
  supports anything.
- **"An extra account is expensive to *run*."** *Still true, and now the whole of the argument.* A separate
  account needs its own VPC floor: one NAT Gateway (0.045 USD/h ≈ **33 USD/month** in `us-west-2`) plus the
  interface endpoints it cannot share (0.010 USD/h each, per AZ). Call it **50-65 USD/month**, against a
  ceiling of 50 (D12). That, and the Organizations account quota — measured at 10, requested at 15, with
  `Staging` already deferred for it (Stage 1a) — are the two live reasons. **Neither is a security
  argument**, and this decision should not be quoted as if it were one.

## What the rejection actually costs, stated in full

The original text names one consequence — no boundary between build and runtime. There are three more,
and they are recorded here so the price is visible when the revision trigger fires:

1. **The trust hierarchy is inverted.** The supply chain is the highest-privilege system in the
   organization: it deploys into Development, Staging *and* Production. Housing it inside one of its own
   targets means the administrators of that target administer the pipeline that governs the other two.
   Separated, the pipeline would be uniformly cross-account — which is *simpler* to audit, not harder,
   since the cross-account shape is already required for the other two targets.
2. **It dilutes the `Workloads` OU policy set, so the cost lands on `Staging` too.** D20 gives that OU the
   contract "no interactive compute, no human control plane". GitLab is precisely a human control plane
   with a web UI, and it is why the VPN has to reach into Production at all. The OU's ceiling is therefore
   written around an exception, and `Staging` — which needs no exception — inherits the looser set.
3. **Production is reachable from the Interactive accounts, and would otherwise not be.**
   [Stage 3 step 6](../stages/stage-03-networking.md) states that the Sandbox↔Production and
   Development↔Production peerings exist **for one reason: reaching GitLab**. In a separate account both
   peerings point at that account instead and **Production accepts none** — a verifiable property of the
   perimeter rather than an intention (Lesson 5). This is the single largest thing the rejection buys away.

Also note the framing trap this decision sits next to (Lesson 10): ECR and CodeArtifact are a **registry**,
consumed by every account. Their placement follows the supply chain here for the reason above, not because
they belong to a runtime.

**How much of the loss is real in this lab, honestly.** One human is administrator on every account, so the
account boundary separates the *software*, not the operator — the inverse of Lesson 2. The property this
project actually has to demonstrate — *the people the approval gate gates cannot modify the gate* — is
already obtained by moving the chain out of `Sandbox`, which is what this decision does. What a separate
account adds is the second property, *a compromise of the build system is not a compromise of production
data*, and with one operator that property is largely notional.

**Revision trigger.** Revisit when **any** of these becomes true: (a) the budget ceiling rises enough to
absorb a second VPC floor, *or* the egress design settles on B (no NAT) so the floor is endpoints only;
(b) a second person gains administrative access to any account, which is the point at which the boundary
stops being notional; (c) the account quota stops binding **and** a Transit Gateway already exists for
another reason, so the network cost of the move is incremental rather than new. Until then the option is
kept cheap rather than taken — see the option-preservation note in
[Stage 7](../stages/stage-07-gitlab-runners-ecr.md), and note that the `<env>` token **`shared` is reserved
and unused** for exactly this account (`plan/conventions.md` §6; the platform token became `org` on
2026-08-09).

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
