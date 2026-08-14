# D37 — What a nested OU carries: inherit rather than copy

**Status:** Decided (2026-08-13, user): **nothing is attached or enabled on `Sandboxes` — no SCP, no RCP, no tag policy, no Control Tower control — unless it is a configuration that *differs* from `Interactive`'s**

**In one line:** Sameness between a nested OU and its parent is expressed by inheriting, never by copying; the price is that Control Tower reports the child as having zero controls while its accounts are fully governed.

**Related decisions:** [D23](D23-ou-structure.md), [D29](D29-policy-canary.md), [D34](D34-account-vending.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

---

## Rationale and consequences

**This was decided against a measurement, not in place of one.** Stage 1c verification (xi) asked whether
`Sandboxes` — nested under `Interactive`, the only depth-2 node in the tree (D23) — is a *registered target*
for Control Tower or is merely governed by inheritance. Step 7.7 answered **both halves, and they are both
yes**: the OU accepted `enable-control` and carried `aws-guardrails-yvYgxw` (`p-h7lc62d0`), the first policy
it ever held; and the deny that fires inside `awsds-infra-sandbox-1` names `p-umksvu5a`, which is
`Interactive`'s document. So the option exists and was declined knowingly. The control was disabled again
and its document ceased to exist with it.

**The argument for declining is Lesson 14 run backwards.** That lesson says a condition which must appear in
N places by hand will be missing from one of them. A statement duplicated onto a child OU is exactly such a
place: every future amendment to `Interactive`'s ceiling then has two homes, and the failure is silent
because the child keeps enforcing the *old* text. The worked example arrived in the same sitting —
`AWS-GR_RESTRICT_ROOT_USER` was enabled on `Policy Test` without `ExemptAssumeRoot` precisely because the
parameter is set per OU, at enable time, once per enablement. Five OUs meant five chances to omit it, and
one was taken.

**What it costs, and this is the part worth carrying rather than rediscovering.** A Control Tower *enabled
control* is per OU and is **not inherited as an enablement** — only the SCP statements it emits are
inherited. So:

| | |
|---|---|
| `controltower list-enabled-controls` on `Sandboxes` | **empty** |
| `organizations list-policies-for-target` on `Sandboxes` | `FullAWSAccess` and `RCPFullAWSAccess` only |
| What actually applies to a Sandbox account | the organization root's two SCPs **plus** `Interactive`'s full set, Region control included |

**The drift view is not the ceiling.** Anyone asking what governs a Sandbox account must read the parent,
and any tooling that enumerates governance per OU will under-report this node. That is the whole of the
trade, it is accepted, and it is why this is a decision rather than a convention.

**The exception clause is what keeps the rule usable.** It does not forbid the child from ever carrying a
policy — it forbids the child from carrying a *copy*. A requirement that applies to Sandbox accounts and
must **not** apply to Development is, by construction, a difference, and it earns its own attachment on
`Sandboxes`. The test before attaching anything there is one question: *would this same statement be correct
on `Interactive`?* If yes, it belongs on the parent.

**It generalises to the tree, not just to this node.** D35 makes `Sandbox` the one account class that
multiplies, and [Stage 14](../stages/stage-14-sandbox-vending.md) vends each new business unit's account
into this OU. The same reasoning governs any OU that stage ever nests: a nested OU is a grouping device for
vending, and grouping is not a reason to re-state a ceiling.

**Consequence for Stage 14's code:** the vending flow must not grow a per-OU policy attachment for the
sandbox branch. `ManagedOrganizationalUnit` points at `Sandboxes` and the account is governed on arrival;
there is nothing further to attach, and an attachment appearing there later is a finding
([`AWS_STATE.md`](../../AWS_STATE.md), INV-11).

**Revision trigger.** Two things would reopen this. **First, an audit requirement**: if a compliance report
or an auditor needs per-OU enablement to be visible on its own — which is what an institution would very
likely require ([`plan/institutional-delta.md`](../institutional-delta.md)) — then the reporting cost above
stops being acceptable and the controls get enabled explicitly, duplication and all. **Second, the first
genuine Sandbox-only requirement**, which is not a revision at all but the exception clause doing its job;
it is listed here so that attaching one policy is not mistaken for abandoning the rule.
