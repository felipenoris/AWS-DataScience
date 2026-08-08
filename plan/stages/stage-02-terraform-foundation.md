# Stage 2 — Terraform foundation

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 1. |
| **Consumes** | [D3](../decisions/D03-terraform-state.md), [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D30](../decisions/D30-scp-recovery.md) |
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
   `terraform-live/identity/bootstrap/`. Six state buckets, one per account that Terraform manages —
   no shared state across environments (D3).
4. Migrate every subsequent slice to the remote backend.
5. `terraform-live/identity/`: import the permission sets, groups and assignments created by hand in
   Stage 1, so identity stops being console-managed (D10). Applied with the `awsds-infra-identity`
   profile. `terraform plan` must come back empty after the import — that is the check that the import
   is faithful.
   **Import the SCPs, RCPs and tag policies here too (D30), which no earlier version of this plan did.**
   Until D30 they were created by hand in Stage 1b step 7 and then owned by nobody: no stage imported them,
   nothing regenerated them, and the only record of what they said was the console. That was tolerable
   while they were four hand-written documents; it stops being tolerable once **every** `Deny` in them has
   to carry an identical carve-out condition, because a condition that is typed four times is a condition
   that will exist in three of them. So they move into code and the condition is **generated** from the
   `awsds-scp-recovery` ARNs exported by each account's `foundation/`.
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
   **A second check in the same spirit, and it guards a control rather than a convention (D30): fail the
   build if any `Deny` statement in `terraform-live/identity/` lacks the `awsds-scp-recovery` carve-out
   condition, or if any carve-out uses a wildcard account ID.** Both failure modes are silent — a missing
   carve-out means one policy you cannot repair in place, a wildcard means every policy is escapable by
   anyone who can create a role — and neither shows up in a `plan`. This is the cheapest place to catch
   the drift that D30 accepts as its main risk.
10. Update `README.md` with the repository layout and the AWS resource structure (required by `CLAUDE.md`).

**Deliverables:** `terraform apply` works end-to-end against the Sandbox account using an SSO profile;
the `Makefile` exists with the slice-to-layer table wired up, even though no `[E]` or `[D]` slice exists
yet — `make down` at this point must be a safe no-op, not a command that reaches the `[P]` bootstrap slice.

**Validation:** destroy and re-create a throwaway `[E]` slice to prove reproducibility, and confirm
`make down` leaves `bootstrap/` untouched.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
