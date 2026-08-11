# D35 — Two classes of account: structural, and the Sandbox multiplied per business unit

**Status:** Decided (2026-08-09): **`Sandbox` is one *per business unit*; every other account in the map, `Development` included, is structural and stays singular. The multiplied one gets an automated, Terraform-driven vending flow ([Stage 14](../stages/stage-14-sandbox-vending.md)); the structural ones keep the console flow of D34. N is 1 today**

**In one line:** The account population has a cardinality property the map did not have, and its boundary is exactly D21's graduation boundary — experimentation multiplies per business unit, the engineering chain that follows it does not.

**Related decisions:** [D17](D17-interactive-vs-runtime.md), [D18](D18-data-scientist-access.md), [D20](D20-staging-account.md), [D21](D21-development-account.md), [D23](D23-ou-structure.md), [D24](D24-shared-filesystem.md), [D26](D26-unified-studio.md), [D34](D34-account-vending.md)

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 1d](../stages/stage-01d-org-wide-enablement.md), [Stage 3](../stages/stage-03-networking.md), [Stage 4](../stages/stage-04-vpn.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

---

## Rationale and consequences

**D34 said the account list is not static. This says *which part* of it is not.** Read the map with the
question "how many of these will exist in five years", and it splits in two:

| Class | Accounts | Cardinality | Vending |
|---|---|---|---|
| **Structural** | Management, Log Archive, Audit, Identity, Policy Canary, Data Governance, **Development**, Staging, Production | **one, always** | console, by the D34 owner |
| **Multiplied** | **Sandbox** | **one per business unit** | automated ([Stage 14](../stages/stage-14-sandbox-vending.md)) |

**The boundary is not arbitrary — it is D21's graduation boundary, and that is what makes this decision hold
together.** D21 already draws the line: in Sandbox the unit of work is a *notebook* and the account is for
experimentation; in Development the unit of work is a *pipeline* and the promotion chain begins. Work crosses
that line by being **rewritten into a Development repository through git, never by a pipeline**. This decision
adds one observation on top: **experimentation is naturally per-business-unit** — each unit explores its own
data, with its own people, on its own schedule — while **engineering is institutional**, a single discipline,
a single set of repositories, a single chain. So the cardinality boundary and the graduation boundary are the
same line, seen from two directions. The chain reads: **N Sandboxes → one Development → one Staging → one
Production.**

**A useful consequence of that coincidence: the promotion chain is untouched by N.** Nothing in Stages 8, 9
or 10 multiplies — one Development means one set of pipelines, one deploy role pair, one approval gate. The
multiplication is entirely upstream of the gate, which is the cheapest place for it to be.

**This is a property, not a fourth axis.** The map's axes say *what an account is for* — lifecycle,
ownership, platform. Cardinality says *how many there will be*. It cuts across: the lifecycle axis carries
both classes (Sandbox multiplies; Development, Staging and Production do not), while ownership and platform
are entirely structural.

**Where per-unit isolation stops, stated plainly because it is the thing most likely to be assumed
wrongly.** A business unit's *experimentation* is private to it — its own account, its own filesystem, its
own people. Its *engineering* is not: everything that graduates lands in one shared Development account, and
from there in one Staging and one Production. So the account boundary carries isolation only up to the
graduation point. Past it, whatever isolation is required has to be carried by **Lake Formation grants,
LF-Tags and per-pipeline execution roles** — not by an account boundary that is deliberately not there. A
request to isolate one unit's *pipelines* from another's is a request for a second Development, which is this
decision's revision trigger rather than a configuration change.

**Why decide it now, before any of it is built.** Automation at the end is the cheap part. The expensive part
is that **several stages are currently written for exactly one Sandbox**, and each of those singular
assumptions is nearly free to loosen while it is prose:

- **CIDR allocation (Stage 3).** Ranges are hardcoded one per account. Three of the four stay fixed; the
  **Sandbox class needs a supernet with room for the units that will exist**, one `/16` allocated per unit
  from a recorded table. Ranges stay non-overlapping even between accounts that never peer — D20's argument
  applies unchanged: an overlap cannot be revisited without rebuilding the VPC. The concrete allocation is
  settled when Stage 3 is written, which has not happened yet, which is exactly why this costs nothing today.
- **Where the VPN terminates, and this is the one that actually breaks (Stage 4, D24).** The tunnel lands in
  *the* Sandbox account, the client resolver points at the Sandbox VPC, and one Sandbox↔Production peering
  carries the path to GitLab. **The VPN lives on the multiplied side** — so all of it is per-unit: N landing
  accounts, N resolver targets, N peerings. Development's own peering is fixed and single, and is not part of
  the problem. **This decision does not settle the topology** (a designated hub, a Transit Gateway in a shared
  network account, or per-unit VPN endpoints are all live) because the answer depends on N and on whether
  units may reach each other at all. What it settles is that **Stage 4 must not write "the Sandbox account"
  as though there is one** — it names the VPN home as a role an account plays, so the topology change is a
  substitution rather than a rewrite. [Stage 14](../stages/stage-14-sandbox-vending.md) carries it as its
  central open question.
- **Identity (Stage 1b).** `DataScientistAccess` is currently assigned to one `sso-group-data-scientists` group on
  Sandbox and Development. The Development half is right and stays — it is the shared engineering account.
  The Sandbox half becomes **`sso-group-data-scientists-<bu>`, assigned on that unit's Sandbox only**, or every data
  scientist can enter every unit's experimentation account. **Do not create per-unit groups yet** — there is
  one unit. Create the *naming* and write the assignment so the second unit is an addition rather than a
  refactor; the permission set itself is unchanged and shared.
  **Amended 2026-08-11 — the per-unit token is an ordinal, and `<bu>` above is now only half true.** The
  user settled the token as an integer at the moment the first SSO profile was created:
  `awsds-infra-sandbox-1`, matching the account AWS already names `Sandbox Account 1`
  (`plan/conventions.md`). That is the **account** axis. Whether the *group* takes the ordinal too, or keeps
  a unit name — a group exists to say who is in it, which an ordinal does not do — is
  `open-questions.md` item 10, along with the `Environment` tag value, whose enumeration inside the 1c
  step 7.8 tag policy is the one that fails as an `AccessDenied` in a fresh account if it is guessed wrong.
- **Domain association (Stage 6, D26).** The single unified domain is associated with **N + 1** interactive
  accounts — every Sandbox plus the one Development — each needing its own blueprint configuration. That is
  the intended mechanism, so it scales; what it makes heavier is the root deny on `datazone:CreateDomain`
  (1c step 7), because with many sandboxes the pressure to let a unit "just create its own domain" is exactly
  what that deny exists to resist, and INT-12's one-domain-per-account fallback gets more expensive with
  every unit.
- **Cost (`plan/cost-model.md`).** A business unit costs **one** account, one Config recorder, one KMS key,
  one EFS (D24) — and the term that dominates, **one set of interface VPC endpoints**. `plan/institutional-delta.md`
  already names per-account endpoints as the largest hourly cost multiplied by account count; under this
  decision, centralized endpoints shared by RAM stop being the institutional answer and become the arithmetic
  one. Also **one account slot per unit** against the organization quota (D34's headroom item).

**What is already future-proof, stated so it is not re-solved.** SCPs attach to the **OU**, so a new Sandbox
inherits its whole policy set by being placed correctly — that is D23 paying off, and since 2026-08-09
"correctly" has a name: the **`Sandboxes` OU** nested under `Interactive`, which holds the multiplied class
and deliberately carries no policy set of its own (D23). The cost of that nesting is one line in Stage 2: the
organization's OU depth is now 2, so the `for_each` below has to recurse. D34's "the floor is
discovered, the grants are enumerated" rule means a new account is picked up by the organization-wide
policies on the next apply. And Lake Formation cross-account **v3** (1d step 11) can grant to an OU or to a
list, so the mechanical ceiling on N consumers is already lifted.

**One precision on that last one, because "grant to the OU" is the wrong lesson to take from it.** v3 removes
the *mechanical* limit; it does not answer the *governance* question. Granting to the Interactive OU gives
every business unit the same data, which is very likely not what a per-unit split is for. The per-unit grant
shape — LF-Tags per unit, or per-account grants driven by the subscription workflow — is a decision that
arrives with the **second** business unit and belongs to the governance manager, not to this file.

**What this does not change.** The Interactive OU's policy set (D23) — Sandboxes and Development still share
one, which is what putting them in one OU asserts. The graduation-is-a-rewrite property (D21), now doing
double duty as the cardinality boundary. The filesystem staying in Sandbox (D24 — now "in each unit's
Sandbox", which strengthens its argument: the exchange between a unit's Sandbox and Development remains S3
and git, and with N units a peering-for-convenience would be N peerings). And the promotion chain's single
destination.

**Revision trigger:** a business unit needing its own **Development** — which would move an account off the
structural side of the table and break the "the chain is untouched by N" property this decision rests on;
**or** a unit needing a *policy* different from the Interactive OU's set, at which point the question is an OU
and not an account (D23); **or** a request for a per-unit Staging or Production, which is a different
decision entirely.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
