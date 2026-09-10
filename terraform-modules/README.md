# `terraform-modules/` — the reusable half

The roster: `vpc`, `vpc-egress`, `s3-bucket`, `kms-key`, `iam-role`, `wireguard`, `consumer-data`, and
Stage 6's `ecr-repo`, `sagemaker-prereqs` and `sagemaker-denies`. The tree exists from Stage 2 step 1;
**Stage 3 step 1.1/1.1a** wrote the first four, and the rule that kept it empty until then still governs the
unwritten `sandbox-unit` module.

`sagemaker-denies` **creates no resource**: it holds one `aws_iam_policy_document` and outputs its JSON.
What earns it a tag is that the same statements have to reach two objects, in two accounts, written by two
services — the six persona permission sets in `terraform-live/identity/sso/`, and the D13 permissions
boundary that `sagemaker-prereqs` imposes on the roles the SMUS blueprint authors. Sharing the *values*
while duplicating the *structure* is how one intent enforced in two places diverges (Lesson 33), so both
live here and each end composes the result through `source_policy_documents`. The cost: `identity/sso/`,
the entitlement plane, now carries a module dependency.

## A module is written once a caller exists

Nothing in Stage 2 consumes one. `bootstrap/` consumes none by rule (step 2.3), and `identity/sso/` and
`identity/org-policies/` declare `aws_ssoadmin_*` and `aws_organizations_*` resources directly. The first
caller is Stage 3's `foundation/`, which writes `vpc/` anyway.

Writing a module before a caller exists is guessing at an interface, which
[`docs/plan/conventions.md`](../docs/plan/conventions.md) already refuses to do for the `sandbox-unit`
module. The `source` line below also needs a **host** and a **tag scheme**, and this is a monorepo whose
host is GitHub today and **GitLab from Stage 7** (D8): settling that with no caller in hand settles it
twice.

## Modules are consumed by git tag, never by branch

```hcl
module "state_bucket" {
  source = "git::https://<host>/awsds/terraform-modules.git//s3-bucket?ref=s3-bucket-v1.2.0"
}
```

A module that moves under a caller breaks that caller at `apply` time, in whichever account happened to run
next, never in the commit that caused it. A tag is the only reference that cannot move.

This is also why `bootstrap/` will never consume one (step 2.3): a tag has to exist before it can be
referenced, and bootstrap is the slice that makes every other slice possible, so a dependency on the tree
it bootstraps is a cycle nobody can unwind.

## A module consuming another module

First done at Stage 5 pass 4 (2026-08-19) by `consumer-data`, which calls `s3-bucket` and `kms-key` the way
a slice does: by git tag, from origin. Nothing about the rule above changes; the **order** gains a link, and
skipping one fails loudly.

```
commit 1  s3-bucket edited          ->  tag s3-bucket-v0.3.0      ->  push
commit 2  consumer-data (calls it)  ->  tag consumer-data-v0.1.0  ->  push
commit 3  the slices (call that)
```

Stage 6 nests a second time, and one rung is a **relative path** rather than a tag: `sagemaker-prereqs`
calls `kms-key` and `iam-role` by tag, and calls `sagemaker-denies` by `../sagemaker-denies`. Terraform's
git getter clones the whole repository and resolves a submodule inside that clone, so the pin on the shared
document is `sagemaker-prereqs`'s own tag, and a change to the denies is a new tag at this level too.
`identity/sso/` calls `sagemaker-denies` by tag, like any other caller.

Skip a rung and `terraform init` stops at `invalid ref: "<tag>"` — the message
[Recipe B](../docs/plan/runbooks/terraform-changes.md) step 5 is written to prevent, one level deeper.
Recipe B is unchanged; it runs **once per rung**, bottom-up.

This does not license a module whose only job is to bundle other modules. `consumer-data` earns its nesting
because it holds a design — a key policy, an enforced workgroup, the settings-before-links ordering, the
re-grant pair — that two accounts must not spell differently. A module that only forwards variables adds a
tag to maintain and answers no question.

## What goes here, and what does not

**Here:** anything more than one slice instantiates — `vpc`, `wireguard`, `iam-role`, `ecr-repo`,
`s3-bucket`, `kms-key`, `consumer-data`, `step-function`, `mwaa-serverless-workflow`. **`consumer-data` is
the first that is a whole slice's design rather than one resource shape**: `sandbox/data/` and, until
Stage 6b destroyed it, `development/data/` differed only in which account they named; D35 makes it two
callers again at the second business unit.

**Not here:** anything applied against a specific account. That is a *slice*, and it lives in
[`terraform-live/`](../terraform-live/README.md). A module has no state, no backend and no account; a slice
has all three.

---

*Layout: [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6 · Deployed tree:
[`terraform-live/README.md`](../terraform-live/README.md)*
