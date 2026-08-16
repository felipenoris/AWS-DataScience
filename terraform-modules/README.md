# `terraform-modules/` — the reusable half

**Empty on purpose today.** The tree exists from Stage 2 step 1; the first modules — `vpc`, and with it
`s3-bucket`, `iam-role`, `kms-key` — arrive with **Stage 3 step 1.1/1.1a**.

## Why it is still empty at the end of Stage 2

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

## What goes here, and what does not

**Here:** anything more than one slice instantiates — `vpc`, `wireguard`, `iam-role`, `ecr-repo`,
`s3-bucket`, `kms-key`, `step-function`, `mwaa-serverless-workflow`.

**Not here:** anything applied against a specific account. That is a *slice*, and it lives in
[`terraform-live/`](../terraform-live/README.md). The distinction is the same one that file opens with: a
module has no state, no backend and no account; a slice has all three.

---

*Layout: [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6 · Deployed tree:
[`terraform-live/README.md`](../terraform-live/README.md)*
