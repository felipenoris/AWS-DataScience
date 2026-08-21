# `terraform-modules/` — the reusable half

**Ten modules today** (2026-08-21): `vpc`, `vpc-egress`, `s3-bucket`, `kms-key`, `iam-role`,
`wireguard`, `consumer-data`, and Stage 6's three — **`ecr-repo`**, **`sagemaker-prereqs`** and
**`sagemaker-denies`**. The tree exists from Stage 2 step 1 and was empty until **Stage 3 step 1.1/1.1a**
wrote the first four; the section below is why the wait was deliberate, and it is kept because the
argument outlives the emptiness — it is the same argument `conventions.md` still applies to the unwritten
`sandbox-unit` module.

**`sagemaker-denies` is the first module here that creates NO RESOURCE AT ALL**, and it is worth saying why
that is not a violation of "a module that only forwards variables answers no question" below. It holds one
`aws_iam_policy_document` and outputs its JSON. What earns it a tag is that **the same statements have to
reach two different objects, in two different accounts, written by two different services**: the six
persona permission sets in `terraform-live/identity/sso/`, and the D13 permissions boundary that
`sagemaker-prereqs` imposes on the roles the SMUS blueprint authors. That is Lesson 33's exact shape — one
intent enforced in two places diverges, and sharing the *values* while duplicating the *structure* is what
makes it look like it cannot — so the structure **and** the values live here and both ends compose the
result through `source_policy_documents`. **The cost is named rather than hidden:** `identity/sso/`, the
entitlement plane, now has a module dependency it did not have before.

## Why it was still empty at the end of Stage 2

Stage 2 step 7 used to sit between the bootstrap slices and the identity ones, on the argument that
bootstrap consumes no module (step 2.3). That is true and does not reach far enough: **nothing in Stage 2
consumes one either.** `identity/sso/` and `identity/org-policies/` declare `aws_ssoadmin_*` and
`aws_organizations_*` resources directly and call no module at all.

That moved the step to the end of the stage on 2026-08-15, and **on 2026-08-16 it moved out of the stage
altogether**: the argument does not expire when the stage does, and at the end of Stage 2 there is still no
caller. The first is Stage 3's `foundation/`, which writes `vpc/` anyway.

Writing a module before a caller exists is guessing at an interface — which
[`docs/plan/conventions.md`](../docs/plan/conventions.md) already refuses to do for the `sandbox-unit` module. Same
argument, one stage earlier.

**The second reason the wait is cheap:** the `source` line below needs a **host** and a **tag scheme**, and
this is a monorepo whose host is GitHub today and **GitLab from Stage 7** (D8). Settling that with no caller
in hand settles it twice.

## The one rule that is not negotiable

**Modules are consumed by git tag, never by branch.**

```hcl
module "state_bucket" {
  source = "git::https://<host>/awsds/terraform-modules.git//s3-bucket?ref=s3-bucket-v1.2.0"
}
```

A module that moves under a caller is a broken caller, and it breaks at `apply` time in whichever account
happened to run next — never in the commit that caused it. A tag is the only reference that cannot move.

This is also why `bootstrap/` will never consume one (step 2.3): a tag has to exist before it can be
referenced, and bootstrap is the slice that makes every other slice possible. Giving it a dependency on the
tree it bootstraps is how a repository acquires a cycle nobody can unwind at 23:00.

## A module may consume another module — the tag order just gets one more link

**First done at Stage 5 pass 4 (2026-08-19), by `consumer-data`**, which calls `s3-bucket` and `kms-key`
the same way a slice does: by git tag, from origin. Nothing about the rule above changes, and no new rule
is needed — but the **order** does, and it fails loudly rather than subtly, which is the only reason this
section exists:

```
commit 1  s3-bucket edited          ->  tag s3-bucket-v0.3.0      ->  push
commit 2  consumer-data (calls it)  ->  tag consumer-data-v0.1.0  ->  push
commit 3  the slices (call that)
```

**Stage 6 added a second nesting, and its rungs are worth writing out because one of them is a RELATIVE
path rather than a tag:** `sagemaker-prereqs` calls `kms-key` and `iam-role` by tag, and calls
`sagemaker-denies` by **`../sagemaker-denies`**. That is legal and deliberate — Terraform's git getter
clones the whole repository and resolves a submodule inside that clone — and it makes the coupling honest:
the pin on the shared document is **`sagemaker-prereqs`'s own tag**, so a change to the denies is a new tag
at this level too. `identity/sso/` calls `sagemaker-denies` by tag, like any other caller.

Skip a rung and `terraform init` stops at `invalid ref: "<tag>"` — the same message
[Recipe B](../docs/plan/runbooks/terraform-changes.md) step 5 is written to prevent, one level deeper.
Recipe B is unchanged; it simply runs **once per rung**, bottom-up.

**What this does NOT license: a module whose only job is to bundle other modules.** `consumer-data` earns
its nesting because it holds a design — a key policy, an enforced workgroup, the settings-before-links
ordering, the re-grant pair — that two accounts must not spell differently. A module that only forwards
variables adds a tag to maintain and answers no question.

## What goes here, and what does not

**Here:** anything more than one slice instantiates — `vpc`, `wireguard`, `iam-role`, `ecr-repo`,
`s3-bucket`, `kms-key`, `consumer-data`, `step-function`, `mwaa-serverless-workflow`. **`consumer-data`
is the first that is a whole slice's design rather than one resource shape**: `sandbox/data/` and
`development/data/` differ only in which account they name, and D35 makes that three callers at the second
business unit.

**Not here:** anything applied against a specific account. That is a *slice*, and it lives in
[`terraform-live/`](../terraform-live/README.md). The distinction is the same one that file opens with: a
module has no state, no backend and no account; a slice has all three.

---

*Layout: [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6 · Deployed tree:
[`terraform-live/README.md`](../terraform-live/README.md)*
