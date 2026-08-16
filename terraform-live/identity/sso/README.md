# `identity/sso/` — the entitlement plane

**Permission sets, their policies, and group→account assignments — and nothing that is
person-shaped.** Written at [Stage 2 step 5](../../../docs/plan/stages/stage-02-terraform-foundation.md),
against the design of record in [Stage 1b step 3](../../../docs/plan/stages/stage-01b-identity-and-controls.md),
which this file does not restate.

Applied with **`awsds-infra-identity`** — the infrastructure user, on the **Identity** account,
through **`InfrastructureAccess`**. State: the Identity bootstrap bucket, `identity/sso/`.

```bash
./scripts/gen-tfvars.py identity sso && ./scripts/gen-backend-hcl.py identity sso
```

## Why this is a slice of its own, and not half of `identity/`

It reaches its objects through the **IAM Identity Center delegated administrator**
(`sso.amazonaws.com`, D10) — a different delegation from the resource-based policy that
[`org-policies/`](../org-policies/README.md) needs, proved by a different stage, failing
independently. The full four-way argument is in Stage 2 step 5; the short form is the last
row of its table: **a mistake here costs a person their sign-in, and a mistake there can lock
the organization out of itself.** Different blast radius deserves a different plan to read.

`sso/` reads nothing from `org-policies/` — there is no `terraform_remote_state` between them.

## What is here, and what deliberately is not

| | Here | Not here |
|---|---|---|
| Entitlements | the **six persona sets**, written; **`InfrastructureAccess`**, imported; every group→account assignment | Control Tower's own sets — editing one is landing-zone drift |
| Directory objects | — | the four **users** and five **groups**. They are people: their count grows with headcount, so they stay in the directory and arrive over SCIM in any real deployment (`docs/plan/conventions.md`, "The identity seam") |
| Assignments | the enumerated group ones | the **Account Factory direct assignments** (D32) — re-created by Control Tower, so a property of a vended account rather than something to model; and `Policy Canary`'s, permanently (D29) |
| Boundaries | — | **deferred by decision 4** — see below |

## The two rules that shape every file

**Resolve a group by display name, never by GUID.** Group IDs belong to *one* directory
instance; federating to a corporate IdP re-creates every group with new ones. The GUIDs exist
only on the `terraform import` command line (`aws/output/import-ids.txt` §3).

**The grants are enumerated, the floor is discovered — and this slice owns the enumerated
half** (D34). Every assignment is a row somebody typed in [`locals.tf`](locals.tf). A `for_each`
over a *data source* would let an account acquire `DataScientistAccess` by simply existing,
which is the failure the design exists to prevent. The one data source here,
`aws_organizations_organization`, exists to turn an authored **name** into the id the API
requires — and the names are exact: Control Tower vended every account with an ` Account`
suffix, and a **suspended** account called plain `Sandbox` is still in the roster.

## What is complete, and what a later stage owes

These sets are written five stages before most of the resources they govern, so the file draws
one line and states it: **every deny is complete; every allow whose resource is the service or
the account is complete; no allow is scoped to an object that does not exist yet.** Writing
those from the naming convention would be guessing at an interface — the same thing this stage
refuses to do for a module — and in an S3 ARN an `awsds-*` wildcard means any bucket of that
shape *on earth*.

| Owed by | To which set | What |
|---|---|---|
| Stage 5 | `DataScientistAccess` | scratch and derived prefixes (D19: per-principal, its CMK is the read control — D31); lake read through the Lake Formation share |
| Stage 6 | `DataScientistAccess` | Studio use against the blueprint-provisioned domain, and the `iam:PassRole` for job submission — scoped by `iam:PassedToService` **and** by role ARN |
| Stage 7 | `DataScientistAccess`, `DataScientistProdAccess`, `DevEnvStewardAccess` | the ECR repository ARNs, so pull and metadata reads stop being account-wide |
| Stage 8 | `DeploymentManagerAccess` | `s3:GetObject` on **enumerated** build-artifact and test-report prefixes — never a bucket wildcard, which is what produced D31 |
| Stage 9 | `DataScientistProdAccess` | the enforced `awsds-prod-athena` workgroup (`EnforceWorkGroupConfiguration` is what makes the output location not the user's choice), the named output prefixes, the results-zone read/write, and the `awsds-prod-debug` assumption (its step 6). `DataScientistStagingAccess` gains **nothing** — Stage 9 step 5.2 only reads it back (no Athena, `DenyEveryWrite` intact) |
| Stage 3 | all six | **the permissions boundary** — see below |

Nobody signs in before Stage 6 (1b step 3.9), so nothing is blocked by this.

## The boundary, deferred by decision 4 (2026-08-16)

A customer-managed boundary must exist as an `aws_iam_policy` of the same name and path **in
every account a set is provisioned into**, and no governed account has a `foundation/` slice
yet — the reference would fail *provisioning*, per account, in an account nobody is watching.
So no `aws_ssoadmin_permissions_boundary_attachment` is written here yet.

**What did not wait is the content.** The two denies step 5.2 wanted from every boundary —
`iam:CreateRole` and `iam:UpdateAssumeRolePolicy` — are in
[`policies-shared.tf`](policies-shared.tf) today, because the carve-outs they defend
(`DenyAccountBpaChangeExceptInfrastructure`, `DenyCatalogMaintenanceRunsExceptMaintenanceRole`)
are attached today, and **a carve-out cannot defend itself**.

## The size discipline

Three of these sets are long enumerated denies, and a permission set **becomes an IAM role** in
every account it reaches — where the inline-policy limit is far lower than the Identity Center
API's. So `terraform plan` fails on an oversized policy (`var.inline_policy_max_bytes`) and
`terraform output inline_policy_bytes` reports the margin. **If it fires, the answer is a
customer-managed policy, not a larger threshold** — which lands back on decision 4.

## Pointers

| Question | File |
|---|---|
| What each set is *for*, persona by persona | [Stage 1b step 3](../../../docs/plan/stages/stage-01b-identity-and-controls.md) — the design of record |
| Why six are written and one is imported | 1b step 3.9 |
| The import commands and their ids | [`infrastructure-access.tf`](infrastructure-access.tf), and untracked `aws/output/import-ids.txt` |
| Naming, tags, the identity seam, the IAM rules | [`docs/plan/conventions.md`](../../../docs/plan/conventions.md) |
| What is deployed right now | [`aws/INDEX.md`](../../../aws/INDEX.md) — `list-identities.py` §3 |

---

*Slice index: [`terraform-live/README.md`](../../README.md) · Plan core: [GENERAL_PLAN.md](../../../docs/GENERAL_PLAN.md)*
