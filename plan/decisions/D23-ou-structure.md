# D23 — OU structure — the account is the isolation boundary, the OU is the policy boundary

**Status:** Decided (2026-08-08): **four OUs, each defined by the policy set it carries: Security, Interactive, Data, Workloads. Revised the same day by D29: a fifth, `Policy Test`, holding the throwaway `Policy Canary` account. Revised again on 2026-08-09 against what execution produced: a sixth, `Identity`, because Control Tower would not vend into the foundational `Security` OU, and a nested `Sandboxes` under `Interactive`**

**In one line:** Six OUs plus one nested, each named for the policy set it carries or for the class of account it groups; the account isolates, the OU attaches policy.

**Related decisions:** [D10](D10-identity-center-delegation.md), [D20](D20-staging-account.md), [D26](D26-unified-studio.md), [D27](D27-catalog-maintenance.md), [D29](D29-policy-canary.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 1d](../stages/stage-01d-org-wide-enablement.md), [Stage 2](../stages/stage-02-terraform-foundation.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

---

## Rationale and consequences

Segregating "by OU" versus "by account" is a false choice — accounts isolate (blast radius, quotas, billing, credentials), OUs attach policy once so it is inherited rather than remembered. An OU therefore earns its existence exactly when two or more accounts need the same policy set, and the OUs here are named for their policy, not for their contents: **Security** (Log Archive, Audit — Control Tower's guardrails; *this originally included `Identity`, and the section below records why it does not*), **Interactive** (Development plus the nested `Sandboxes` — interactive compute *allowed*, and it is allowed because this is the one OU that adds **no deny of its own** to the organization-root set; *this clause used to read "human infrastructure changes denied", which described `DataScientistAccess` — an identity policy — and not an SCP, corrected 2026-08-09: see Stage 1c step 7 for the correction, for why the literal SCP cannot be written without exempting the builder, and for the one candidate deny that would need no exemption. The nesting also arrived later, below*), **Data** (Data Governance — no *user* compute, with the two named carve-outs D26 and D27 add, deletion denied), **Workloads** (Staging, Production — no interactive compute, no human control plane; the D20 SCP set unchanged). A per-environment OU tree (one OU per account) was considered and rejected: an OU holding exactly one account forever is a folder with one file — policy might as well attach to the account. The revision triggers are recorded here so the structure is revisited deliberately: a second production-like account → nest `Workloads` into `NonProd`/`Prod`; the first time Staging and Production need genuinely different policy → the same; a second data domain → the `Data` OU stops being a single-account OU by itself. **The OU this row used to list as notably absent — a policy staging OU for testing SCPs before they attach to anything real — was built the same day as D29**, under the names `Policy Test` (OU) and `Policy Canary` (account), chosen precisely to avoid the collision with the Staging *account* that this row spent a sentence warning about. It is the one single-account OU that passes the test above rather than failing it: its purpose *is* to contain a disposable account, so the account and the OU are the same decision.

## Revised 2026-08-09 by execution: the tree has two shapes this file did not describe

Both were found in the organization rather than argued into it, and both are adopted rather than undone.
The tree as built:

```
Root
├── Security      <- Log Archive, Audit          (foundational, Control Tower's own)
├── Identity      <- Identity                    (NEW - see below)
├── Interactive   <- Development
│   └── Sandboxes <- Sandbox, one per business unit (D35)
├── Data          <- Data Governance
├── Workloads     <- Staging, Production
└── Policy Test   <- Policy Canary
```

**`Identity` is its own OU because Control Tower would not put the account anywhere else.** The account was
to live in `Security` alongside Log Archive and Audit; vending it there was blocked
(`log/stage-01a-landing-zone.md`, 2026-08-09),
and the most likely reason is the one Stage 1a step 4 had already written down as a thing to verify —
`Security` is a **foundational** OU in Control Tower's model, and a non-foundational account does not simply
join it. So the fallback that step named fired, exactly as written. **This is not the "folder with one file"
the test above rejects**, and the reason matters: `Security`'s policy set was never ours — it is Control
Tower's guardrails, which the account inherits by being *foundational*, not by being in a folder. `Identity`
therefore carries a policy set of its own or it carries none at all, which makes it an OU by the test rather
than in spite of it.

**The consequence this paragraph drew — "a new OU carries no policy set until code attaches one" — was
measured on 2026-08-13 and is not what happened here** (Stage 1c step 7.0; `log/stage-01c-preventive-policies.md`).
`Identity` carries `aws-guardrails-coSzJr`, Control Tower's standard eight statements, identical to every
other registered OU: creating it through the console **registered** it, and registration is what attaches
the guardrail — not being foundational. What `Security` has extra is three statements about the log-archive
and audit buckets, which mean nothing for an account that holds neither. **The rule survives where it is
actually load-bearing** — an OU created outside Control Tower entirely, or by Terraform at Stage 2, would
carry nothing, and D34 keeps vending outside every state — so the instruction stands in its narrow form:
compare the **enabled controls** of `Security` and `Identity`, which are a separate registration from the
SCP, and attach explicitly whatever differs. "It used to inherit that" is still not a control (Lesson 5),
and neither is "the OU next to it has one".

**`Sandboxes` is nested under `Interactive` and groups the class that multiplies.** It holds every business
unit's `Sandbox` account; `Development` stays directly under `Interactive`. **It carries no policy set of its
own, deliberately** — SCPs, RCPs and the tag policy attach to `Interactive` and inherit down, which is what
keeps D35's "a new Sandbox inherits its whole policy set by being placed correctly" true. Do not attach the
Interactive set twice. So it does not fail the test above either, because it is not claiming to be a policy
boundary: it is a **container for a cardinality class**, the same role `Policy Test` plays for a disposable
account. That is a third legitimate reason for an OU to exist, alongside "two accounts need the same policy
set" and "the OU exists to hold a throwaway", and it is worth naming so the next nesting question is asked
against the right list.

**The one mechanical consequence, and it is the one that bites silently: the organization's OU nesting depth
is now 2.** `aws_organizations_organizational_units` returns the children of **one** parent, so a `for_each`
written over the root's children enumerates `Sandboxes` not at all — and D34's rule is precisely that the
floor must be *discovered*. Stage 2 lists the depth as a thing to verify; it is no longer open, and the
answer is 2. A single-level enumeration there would leave every Sandbox account outside the org-wide
attachments while `terraform plan` reports "No changes".

**Revision trigger, added here:** a third level of nesting, or `Sandboxes` ever needing a policy the rest of
`Interactive` does not have — at which point it stops being a container and becomes a policy boundary, and
D35's "Sandbox and Development share one policy set" is what is actually being revised.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
