# Stage 2 — Terraform foundation

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 1. |
| **Consumes** | [D3](../decisions/D03-terraform-state.md), [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D34](../decisions/D34-account-vending.md) |
| **Proves** | — |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the repository can provision infrastructure reproducibly.

**Prerequisites:** Stage 1.

**To execute:**

1. Delete the empty `terraform/` folder; create `terraform-live/` and `terraform-modules/` as in `plan/conventions.md` §6.
2. `terraform-live/sandbox/bootstrap/`: S3 state bucket (versioning, SSE-KMS, public access blocked,
   `use_lockfile = true`). Applied once with local state, then the state is migrated into the bucket it
   just created (add the `backend "s3"` block, `terraform init -migrate-state`) — this is the documented
   chicken-and-egg exception. **The state file is never committed**: state carries account IDs and
   resource ARNs, which do not belong in the Git history of a repository hosted on GitHub.
3. Same for `terraform-live/development/bootstrap/`, `terraform-live/data-governance/bootstrap/`,
   `terraform-live/staging/bootstrap/`, `terraform-live/production/bootstrap/` and
   `terraform-live/identity/bootstrap/`. One state bucket per account that Terraform manages —
   no shared state across environments (D3).
4. Migrate every subsequent slice to the remote backend.
5. `terraform-live/identity/`: import the permission sets, groups and assignments created by hand in
   Stage 1, so identity stops being console-managed (D10). Applied with the `awsds-infra-identity`
   profile. `terraform plan` must come back empty after the import — that is the check that the import
   is faithful.
   **Import the SCPs, RCPs and tag policies here too, which no earlier version of this plan did.**
   They are created by hand in Stage 1b step 7 and would otherwise be owned by nobody: no stage imports
   them, nothing regenerates them, and the only record of what they say is the console. That is the most
   dangerous artefact in this plan to hold in a browser tab — it is the set that can lock the organization
   out of itself, and since D30 was reverted there is **no principal inside a governed account that can
   work around a mistake in it**. Code gives it a diff, a review and a rollback; the console gives it none
   of the three.
   (This consequence arrived with D30 and outlived it. D30's own reason was narrower — a carve-out
   condition repeated across several policies has to be *generated, not typed* — and that reason went away
   with the decision. The ownership hole it happened to close did not.)
   **Write this slice so an OU or account created later is covered without anybody remembering (D34).**
   Accounts and OUs are vended from the console, permanently and by design, and **that cannot make this
   state inconsistent** — nothing here declares `aws_organizations_account` or
   `aws_organizations_organizational_unit`, and a state file tracks only what a configuration declares. The
   risk is the opposite of drift and it is silent: a new OU with no attachment, or a new account outside
   every enumerated ARN/account-ID condition, with `terraform plan` reporting **"No changes"** in both
   cases. So: **the floor is discovered, the grants are enumerated.** Attachments, the organization-root
   set and the tag policy are `for_each` over `aws_organizations_organizational_units` /
   `aws_organizations_organization` data sources; **permission set assignments stay written out one by
   one**, because an account silently acquiring `DataScientistAccess` on the next apply is the failure this
   design exists to prevent. **The nesting depth is no longer an open question and the answer is 2**
   (D23, 2026-08-09): `Sandboxes` sits under `Interactive`, and every business unit's Sandbox account sits
   under `Sandboxes`. `aws_organizations_organizational_units` returns the children of **one** parent, so a
   single `for_each` over the root's children enumerates neither the nested OU nor the accounts in it — and
   the failure is the silent one this whole paragraph is about: those accounts stay outside every org-wide
   attachment while `terraform plan` reports "No changes". **Recurse, or enumerate both levels explicitly and
   fail the CI check if an OU exists that neither level matched.** *Still to verify here:* that the
   `for_each` key is stable enough that adding an OU does not
   re-create the existing attachments — a plan that wants to destroy and re-create an SCP attachment is a
   momentary hole in the ceiling.
   **What is deliberately *not* imported here: the region restriction.** It is Control Tower's own Region
   deny control (1b step 7), not one of the hand-written documents, and the SCP that implements it is
   generated and owned by the landing zone. Importing that SCP into `terraform-live/identity/` would put
   Terraform and Control Tower in a fight over the same object, which is the landing-zone drift this plan
   already refuses to create for permission sets. If it is to be in code at all, the resource is
   **`aws_controltower_control`** — the control, not the policy it emits.
   Organizations supports a **delegated administrator for policy management**, so this stays consistent
   with principle 1: the slice is applied with the delegated-admin profile and Terraform never holds
   credentials in Management. **Verify that delegation is compatible with the Control Tower landing zone
   before relying on it** — it is the same family of question as the Identity Center delegation in Stage 1b
   step 1, and the fallback is the same: the policies stay console-managed and the CI check below becomes
   a manual review, which is strictly worse and should be recorded as such rather than absorbed.
6. Repository hygiene: `.gitignore` for `.terraform/` and `*.tfstate.backup`; `.terraform.lock.hcl` is
   committed on purpose; `pre-commit` with `terraform fmt`, `terraform validate` and `tflint`; and
   **`checkov` as a required gate, not an optional one** — a policy check that can be skipped is a policy
   check that will be skipped on the day it would have mattered.
7. First reusable modules in `terraform-modules/`: `s3-bucket`, `iam-role`, `kms-key`. The `s3-bucket`
   module enables **S3 Bucket Keys** by default (`plan/cost-model.md`) and blocks public access unconditionally; the
   `iam-role` module takes a permissions boundary as a required argument, so omitting one has to be
   deliberate. Tag every module release; callers pin the tag (`plan/conventions.md` §6).
8. **Teardown/rebuild tooling (D11).** Each slice declares its layer (`[P]`/`[D]`/`[E]`), and a `Makefile`
   at the repository root exposes `make up ENV=sandbox` / `make down ENV=sandbox`: `down` destroys the
   `[E]` slices in reverse dependency order and stops the `[D]` instances; `up` starts the `[D]` instances
   and applies the `[E]` slices. Both must refuse to touch `[P]` slices. Add `make status` to report what
   is currently running and the estimated hourly burn.
9. **No region literals (`plan/architecture.md` §4.1).** `var.region` in every slice, AZs from `data.aws_availability_zones`,
   AMIs from SSM public parameters. A `grep` check in CI that fails on a hardcoded region keeps this
   honest at no cost.
   **A second check in the same spirit, and it guards a control rather than a convention: fail the build
   if any policy document in `terraform-live/identity/` carries an ARN condition with a wildcard account
   ID** (`arn:aws:iam::*:role/...`). That pattern means "any principal of this name, in any account", so a
   condition meant to name one role silently names a role anybody can create. It is invisible in a `plan`
   and cheap in CI. This check used to also require a `awsds-scp-recovery` carve-out in every `Deny`; that
   half went away with D30, and the wildcard half did not, because it applies to the per-function
   carve-outs the design still has (D26, D27).
10. Update `README.md` with the repository layout and the AWS resource structure (required by `CLAUDE.md`).

**Deliverables:** `terraform apply` works end-to-end against the Sandbox account using an SSO profile;
the `Makefile` exists with the slice-to-layer table wired up, even though no `[E]` or `[D]` slice exists
yet — `make down` at this point must be a safe no-op, not a command that reaches the `[P]` bootstrap slice.

**Validation:** destroy and re-create a throwaway `[E]` slice to prove reproducibility, and confirm
`make down` leaves `bootstrap/` untouched.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
