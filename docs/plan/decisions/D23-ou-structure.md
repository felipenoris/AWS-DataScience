# D23 — OU structure — the account is the isolation boundary, the OU is the policy boundary

**Status:** Decided (2026-08-08): four OUs, each defined by the policy set it carries — Security, Interactive, Data, Workloads. Revised the same day by D29: a fifth, `Policy Test`, holding the throwaway `Policy Canary` account. Revised 2026-08-09 against what execution produced: a sixth, `Identity`, because Control Tower would not vend into the foundational `Security` OU, and a nested `Sandboxes` under `Interactive`.

**Amended 2026-09-05:** `Interactive` keeps its nested `Sandboxes` child and has nothing else beneath it. The collapse its own one-file-folder test invites is **declined**: collapsing moves SCP attachments *and* Control Tower enabled controls, and the deny measured inside a Sandbox account names `Interactive`'s document (D37). Revisit when the quota lapses and Stage 14 vends a second unit.

**In one line:** Six OUs plus one nested, each named for the policy set it carries or for the class of account it groups; the account isolates, the OU attaches policy.

**Related decisions:** [D10](D10-identity-center-delegation.md), [D20](D20-staging-account.md), [D26](D26-unified-studio.md), [D27](D27-catalog-maintenance.md), [D29](D29-policy-canary.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 1d](../stages/stage-01d-org-wide-enablement.md), [Stage 2](../stages/stage-02-terraform-foundation.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

---

## Rationale and consequences

Segregating "by OU" versus "by account" is a false choice: accounts isolate (blast radius, quotas, billing, credentials), OUs attach policy once so it is inherited rather than remembered. An OU earns its existence when two or more accounts need the same policy set, and the OUs here are named for their policy, not for their contents: **Security** (Log Archive, Audit — Control Tower's guardrails; the section below records why `Identity` is not among them), **Interactive** (Development plus the nested `Sandboxes` — interactive compute *allowed*, because this is the one OU that adds **no deny of its own** to the organization-root set; Stage 1c step 7 carries the 2026-08-09 correction of an earlier "human infrastructure changes denied", which described `DataScientistAccess`, an identity policy, and not an SCP — it also carries why the literal SCP cannot be written without exempting the builder, and the one candidate deny that would need no exemption), **Data** (Data Governance — no *user* compute, with the two named carve-outs D26 and D27 add, deletion denied), **Workloads** (Staging, Production — no interactive compute, no human control plane; the D20 SCP set unchanged). A per-environment OU tree (one OU per account) was considered and rejected: an OU holding exactly one account forever is a folder with one file, and policy might as well attach to the account. The revision triggers: a second production-like account → nest `Workloads` into `NonProd`/`Prod`; the first time Staging and Production need genuinely different policy → the same; a second data domain → the `Data` OU stops being a single-account OU by itself. **A policy staging OU, for testing SCPs before they attach to anything real, was built the same day as D29**, under the names `Policy Test` (OU) and `Policy Canary` (account), chosen to avoid a collision with the Staging *account*. It is the one single-account OU that passes the test above rather than failing it: its purpose *is* to contain a disposable account, so the account and the OU are the same decision.

## The tree as built

Both shapes below were found in the organization rather than argued into it, and both are adopted rather
than undone:

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
(`docs/log/log-stage-01a-landing-zone.md`, 2026-08-09). The most likely reason is the one Stage 1a step 4
had already written down as a thing to verify: `Security` is a **foundational** OU in Control Tower's model,
and a non-foundational account does not join it. The fallback that step named fired as written. This is not
the "folder with one file" the test above rejects, because `Security`'s policy set was never ours — it is
Control Tower's guardrails, which the account inherits by being *foundational*, not by being in a folder.
`Identity` therefore carries a policy set of its own or none at all, which makes it an OU by the test rather
than in spite of it.

**"A new OU carries no policy set until code attaches one" was measured on 2026-08-13 and is not what
happened here** (Stage 1c step 7.0; `docs/log/log-stage-01c-preventive-policies.md`).
`Identity` carries `aws-guardrails-coSzJr`, Control Tower's standard eight statements, identical to every
other registered OU: creating it through the console **registered** it, and registration is what attaches
the guardrail, not being foundational. What `Security` has extra is three statements about the log-archive
and audit buckets, which mean nothing for an account that holds neither. The rule survives where it is
load-bearing — an OU created outside Control Tower entirely, or by Terraform at Stage 2, would carry
nothing, and D34 keeps vending outside every state — so the instruction stands in its narrow form:
compare the **enabled controls** of `Security` and `Identity`, which are a separate registration from the
SCP, and attach explicitly whatever differs. "It used to inherit that" is not a control (Lesson 5), and
neither is "the OU next to it has one".

**`Sandboxes` is nested under `Interactive` and groups the class that multiplies.** It holds every business
unit's `Sandbox` account; `Development` stays directly under `Interactive`. **It carries no policy set of its
own** — SCPs, RCPs and the tag policy attach to `Interactive` and inherit down, which keeps D35's "a new
Sandbox inherits its whole policy set by being placed correctly" true. Do not attach the Interactive set
twice. It does not fail the test above either, because it is not claiming to be a policy boundary: it is a
**container for a cardinality class**, the role `Policy Test` plays for a disposable account. That is a
third legitimate reason for an OU to exist, alongside "two accounts need the same policy set" and "the OU
exists to hold a throwaway", so the next nesting question is asked against the right list.

**The mechanical consequence: the organization's OU nesting depth is now 2.**
`aws_organizations_organizational_units` returns the children of **one** parent, so a `for_each` written
over the root's children does not enumerate `Sandboxes` at all, and D34's rule is that the floor must be
*discovered*. Stage 2 lists the depth as a thing to verify; it is no longer open, and the answer is 2. A
single-level enumeration there would leave every Sandbox account outside the org-wide attachments while
`terraform plan` reports "No changes".

**Revision trigger:** a third level of nesting, or `Sandboxes` needing a policy the rest of `Interactive`
does not have — at which point it stops being a container and becomes a policy boundary, and what is being
revised is D35's "Sandbox and Development share one policy set".

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
