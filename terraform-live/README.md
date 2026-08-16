# `terraform-live/` — the deployed tree

**One folder per controlled AWS account, each sliced into independently applied units.** This is the tree
that describes what actually exists in an account; the reusable code it calls lives in
`terraform-modules/` and is consumed **by git tag, never by branch** — a module that moves under a caller
is a broken caller.

> **The authoritative layout is [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6, and it is not repeated
> here.** That file carries the full annotated tree with every slice and its `[P]`/`[D]`/`[E]` layer, on
> purpose: two copies of a directory tree drift, and the copy that drifts is always the one somebody reads
> first. **This README explains how the tree is organised and what is in it today.** When the two disagree,
> conventions §6 wins and this file is the one that was not updated.

## What is here today

**Five `bootstrap/` folders — Stage 2 step 1, 2026-08-15 — and `sandbox/bootstrap/` now holds the
resources.** All five (`sandbox/`, `development/`, `data-governance/`, `production/` and `identity/`) carry
`versions.tf` and a committed `.terraform.lock.hcl`; **`sandbox/bootstrap/` also carries the state bucket and
its KMS key (step 2)**, and the other four acquire theirs at step 3. **No `staging/`**: the account is
unvended (step 3.2), and a folder for an account that does not exist is a folder that fails at `init` with a
message about S3.

**Two files per slice are GENERATED and untracked**, because a `.tf` file may hold neither of the values they
carry — the backend cannot interpolate anything, and the region may not be a literal (step 9.1's check
scans for it). Both are written from `scripts/tfhygiene/backend.py`, one table with two writers, so the
region the backend records and the region the provider uses cannot disagree:

```bash
./scripts/gen-tfvars.py      sandbox bootstrap   # terraform.auto.tfvars: region, env, environment_tag
./scripts/gen-backend-hcl.py sandbox bootstrap   # backend.hcl: bucket, key, region, kms alias
```

`bootstrap/` is the one slice whose `backend "s3" {}` block starts **commented out**: it creates the bucket
that will hold its own state, so it applies once with local state and then migrates (step 2.2). Every other
slice declares its backend from the first `init` and never holds local state at all.

**The rest of `docs/plan/conventions.md` §6's tree is not on disk, and that is the deliberate reading of step 1.**
Git does not track empty directories, so a skeleton of ~35 empty slices means ~35 `.gitkeep` files — a second
copy of §6's listing, in a form that drifts silently and that no reader consults. Each slice folder is created
by the stage that first writes a `.tf` file into it, and **§6 stays the one place the layout is written down**.

**`versions.tf` is byte-identical in every slice**, because Terraform has no repository-wide pin: the
constraint belongs to each root module. Step 9's check is what keeps the copies from drifting (Lesson 14).

**Four checks stand over this tree — Stage 2 step 9, 2026-08-15 — and there is no CI to run them in.**
Until Stage 8 puts them in a pipeline the surfaces are `pre-commit` and the repository's `Makefile`, both
calling the same scripts:

```bash
make check      # offline: region literals, indexed AZs, account-level BPA, wildcard ARNs, the policy index
make check-ou   # needs an SSO session as the infrastructure user on Identity
```

Two of them exist because nothing else can enforce their rule: **no `.tf` in this tree may declare
`aws_s3_account_public_access_block`** (the SCP that denies the API carves out exactly the principal every
slice applies as, so the apply would *succeed*), and **no policy document in `identity/` may carry a
wildcard-account ARN** except the one statement whitelisted by `Sid`.

**Set `TF_PLUGIN_CACHE_DIR` before working in this tree**, or every slice downloads its own ~250 MB copy of
the AWS provider — `terraform validate` in the pre-commit hook runs `init` per slice:

```bash
export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
```

The one older exception is [`identity/org-policies/`](identity/org-policies/README.md), which holds the organization's
**preventive policy documents** — the JSON attached to the organization root and to the OUs in
[Stage 1c step 7](../docs/plan/stages/stage-01c-preventive-policies.md), plus `render.py`, which substitutes this
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
  its reasoning are in `docs/plan/conventions.md`, "The identity seam".
- **OUs and accounts.** They are created from the console (D34), outside every state. Nothing here declares
  them, so they cannot drift — but a new OU can end up with no policy attached and a new account outside
  every enumerated condition, with `terraform plan` reporting *"No changes"* either way. Hence the rule that
  survives it: **the floor is discovered and the grants are enumerated** — where "discovered", since 1c put
  every must-cover-everything document on the **organization root**, means *inherited* coverage plus a
  `make check` that fails on an OU nobody accounted for, **not** a `for_each` that attaches. See
  [`docs/plan/conventions.md`](../docs/plan/conventions.md), the D34 bullet, for why the distinction is load-bearing.
- **`aws_s3_account_public_access_block`** — never declared in any slice. The account-level setting is made
  by hand in Stage 1c step 7.4 and then denied by the SCP of step 7.5; it reads exactly like something that
  belongs in `foundation/`, which is why the exclusion is written down in three places.
- **The Region restriction.** It is a Control Tower **managed control** (`CT.MULTISERVICE.PV.1`, decision 6),
  not a hand-written document — so it is not in `identity/org-policies/` and not in any slice.

## Pointers

| Question | File |
|---|---|
| The full slice-by-slice tree, with the `[P]`/`[D]`/`[E]` layer of each | [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6 — **the authority** |
| Naming, tags, the IAM rules, the identity seam | [`docs/plan/conventions.md`](../docs/plan/conventions.md) |
| What the policy documents are and what each may not become | [`identity/org-policies/README.md`](identity/org-policies/README.md) |
| **What every policy statement does, and why it exists** — all four types | [`identity/org-policies/POLICIES.md`](identity/org-policies/POLICIES.md) |
| Which stage builds a given slice | [`docs/plan/stages/INDEX.md`](../docs/plan/stages/INDEX.md) |
| What is deployed right now | [`aws/INDEX.md`](../aws/INDEX.md) and [`docs/AWS_STATE.md`](../docs/AWS_STATE.md) |

---

*Plan core: [GENERAL_PLAN.md](../docs/GENERAL_PLAN.md) · Rules: [`docs/plan/conventions.md`](../docs/plan/conventions.md)*
