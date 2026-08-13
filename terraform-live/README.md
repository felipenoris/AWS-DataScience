# `terraform-live/` — the deployed tree

**One folder per controlled AWS account, each sliced into independently applied units.** This is the tree
that describes what actually exists in an account; the reusable code it calls lives in
`terraform-modules/` and is consumed **by git tag, never by branch** — a module that moves under a caller
is a broken caller.

> **The authoritative layout is [`plan/conventions.md`](../plan/conventions.md) §6, and it is not repeated
> here.** That file carries the full annotated tree with every slice and its `[P]`/`[D]`/`[E]` layer, on
> purpose: two copies of a directory tree drift, and the copy that drifts is always the one somebody reads
> first. **This README explains how the tree is organised and what is in it today.** When the two disagree,
> conventions §6 wins and this file is the one that was not updated.

## What is here today, and it is almost nothing

**The repository is documentation only, with one exception since 2026-08-13.** There is **no `.tf` file
anywhere in this tree** and there will be none before [Stage 2](../plan/stages/stage-02-terraform-foundation.md),
which writes the state buckets and the module skeletons.

The exception is [`identity/org-policies/`](identity/org-policies/README.md), which holds the organization's
**preventive policy documents** — the JSON attached to the organization root and to the OUs in
[Stage 1c step 7](../plan/stages/stage-01c-preventive-policies.md), plus `render.sh`, which substitutes this
organization's identifiers into the templates and writes the pasteable copies to untracked `aws/output/`.
Those documents are pasted into the Management console by hand and **imported into Terraform at Stage 2
step 5.5** — which is why they live in a file at all: an import compares a document against itself instead
of against a re-typing.

## The three questions that decide where something goes

1. **Which account?** → the top-level folder. The account is the only hard boundary AWS offers
   ([`README.md`](../README.md), "Account segregation"), so it is the first cut.
2. **Which slice?** → the sub-folder. A slice is one Terraform state and one `apply`. The seam between two
   slices is a *reason*, not a size: `identity/` is split into `sso/` and `org-policies/` because the two
   reach their objects through **different delegations**; `production/pki/` is split from `foundation/`
   because foundation is opened to change a CIDR and that edit would otherwise decrypt the root CA.
3. **Which layer?** → `[P]` persistent, `[D]` dormant (stopped, not destroyed), `[E]` ephemeral (destroyed
   between sessions). This is principle 7 — *pay nothing while idle* (D11) — and it is a property of the
   slice, so `make down` can act on whole slices rather than on hand-picked resources.

## The account folders

Names only — **no account id ever enters a tracked file**. The profile column is the one Stage 1b step 5
created; it is also the answer to "who runs `terraform apply` here".

| Folder | Account | OU | Profile that applies it |
|---|---|---|---|
| `identity/` | Identity | `Identity` | `awsds-infra-identity` |
| `sandbox/` | Sandbox Account 1 | `Sandboxes` | `awsds-infra-sandbox-1` — **one such folder per business unit** (D35), N is 1 today |
| `development/` | Development | `Interactive` | `awsds-infra-dev` |
| `data-governance/` | Data Governance | `Data` | `awsds-infra-data` |
| `staging/` | Staging | `Workloads` | **none yet — the account is unvended**, held on the account cap |
| `production/` | Production | `Workloads` | `awsds-infra-prod` |

**No folder for Management, Log Archive, Audit or Policy Canary, and each absence is a rule.** Management is
bootstrap-only and never Terraform (principle 1); Log Archive and Audit are Control Tower's, and editing
their contents is landing-zone drift; `Policy Canary` is deliberately empty (D29) — the day something is
created there, the account has stopped being what it is for.

## What deliberately does not live in this tree

- **`terraform-modules/`** — the reusable code. `terraform-live/` composes; it does not define.
- **People.** Identity Center **users, groups and memberships** stay in the directory; only **entitlements**
  — permission sets, boundaries, group→account assignments — are Terraform, in `identity/sso/`. The seam and
  its reasoning are in `plan/conventions.md`, "The identity seam".
- **OUs and accounts.** They are created from the console (D34), outside every state. Nothing here declares
  them, so they cannot drift — but a new OU can end up with no policy attached and a new account outside
  every enumerated condition, with `terraform plan` reporting *"No changes"* either way. Hence the rule that
  survives it: **the floor is discovered** (`for_each` over the Organizations data sources) **and the grants
  are enumerated**.
- **`aws_s3_account_public_access_block`** — never declared in any slice. The account-level setting is made
  by hand in Stage 1c step 7.4 and then denied by the SCP of step 7.5; it reads exactly like something that
  belongs in `foundation/`, which is why the exclusion is written down in three places.
- **The Region restriction.** It is a Control Tower **managed control** (`CT.MULTISERVICE.PV.1`, decision 6),
  not a hand-written document — so it is not in `identity/org-policies/` and not in any slice.

## Pointers

| Question | File |
|---|---|
| The full slice-by-slice tree, with the `[P]`/`[D]`/`[E]` layer of each | [`plan/conventions.md`](../plan/conventions.md) §6 — **the authority** |
| Naming, tags, the IAM rules, the identity seam | [`plan/conventions.md`](../plan/conventions.md) |
| What the policy documents are and what each may not become | [`identity/org-policies/README.md`](identity/org-policies/README.md) |
| **What every SCP statement does, and why it exists** | [`identity/org-policies/SCPs.md`](identity/org-policies/SCPs.md) |
| Which stage builds a given slice | [`plan/stages/INDEX.md`](../plan/stages/INDEX.md) |
| What is deployed right now | [`aws/INDEX.md`](../aws/INDEX.md) and [`AWS_STATE.md`](../AWS_STATE.md) |

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Rules: [`plan/conventions.md`](../plan/conventions.md)*
