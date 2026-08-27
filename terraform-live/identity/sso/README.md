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
which is the failure the design exists to prevent — and where a `for_each` does appear here it
runs over an **authored map**, never over a data source: `locals.tf`'s own maps for the sets and
assignments, and `backend.py`'s generated tfvars for the three cross-account state reads. The name-resolving
lookup, `aws_organizations_organization`, exists to turn an authored **name** into the id the API
requires — and the names are exact: Control Tower vended every account with an ` Account`
suffix, and a **suspended** account called plain `Sandbox` is still in the roster. The
cross-account `terraform_remote_state` reads (`vpn_home` since Stage 4; `consumer_data` +
`lake_data` since Stage 5 pass 4c) supply ARNs no naming convention may compose.

## What is complete, and what a later stage owes

These sets are written five stages before most of the resources they govern, so the file draws
one line and states it: **every deny is complete; every allow whose resource is the service or
the account is complete; no allow is scoped to an object that does not exist yet.** Writing
those from the naming convention would be guessing at an interface — the same thing this stage
refuses to do for a module — and in an S3 ARN an `awsds-*` wildcard means any bucket of that
shape *on earth*.

| Owed by | To which set | What |
|---|---|---|
| ~~Stage 5~~ **DELIVERED 2026-08-19; the Athena + derived families REMOVED 2026-08-26** (D19 revised — the derived zone re-homed onto the SMUS project path; `DataScientistAccess` carries no `athena:` action and the drop-box write is the surviving Stage 5 half) | `DataScientistAccess` | ~~the enforced Athena workgroups, the derived zone's three prefix families~~ (write per-`${aws:userid}`, delete in `scratch/` only) and **the drop-box write's identity half** — every ARN read from the consumer and lake slices' state, which is why this row waited for them (Stage 5 pass 4c). **One line of it was corrected rather than delivered**: this row used to owe *"lake read through the Lake Formation share"*, and **no such grant will ever arrive** — vended access hands the engine credentials through `lakeformation:GetDataAccess`, already held, and a direct `s3:GetObject` on a registered prefix is the bypass D13 exists to exclude. The derived zone's CMK is still the read control (D31), and it grants through the **key policy**, which is why no KMS statement for it appears in this slice |
| — **DELIVERED 2026-08-23** (user-decided, Stage-6-adjacent) | `DataScientistAccess` | the **S3 Access Grants vending handshake** — `s3:GetDataAccess` + `s3:ListCallerAccessGrants`, so a laptop can vend prefix-scoped **project-role** credentials for its SMUS project storage (consumer: `s3-read-write/`). **It is the slice's first customer-managed policy, and the first time decision 4's constraint is MET rather than deferred**: the object is `awsds-org-project-storage-vending`, created by each member's `foundation/` (`persona-vending.tf`, which carries the argument), referenced here by name. It went this way because the inline document had **23 characters of headroom** and the statement costs ~251 — the size discipline below, firing for the first time. **The handshake opens no object**: a per-project Access Grants grant does, and it is revocable without touching either half. **Apply order: the members before this slice.** **APPLIED 2026-08-23**, all three slices, and provisioning read back on the persona role in both member accounts |
| Stage 6 | `DataScientistAccess` | Studio use against the blueprint-provisioned domain, and the `iam:PassRole` for job submission — scoped by `iam:PassedToService` **and** by role ARN |
| Stage 7 | `DataScientistAccess`, `DataScientistProdAccess`, `DevEnvStewardAccess` | the ECR repository ARNs, so pull and metadata reads stop being account-wide |
| Stage 8 | `DeploymentManagerAccess` | `s3:GetObject` on **enumerated** build-artifact and test-report prefixes — never a bucket wildcard, which is what produced D31 |
| Stage 9 | `DataScientistProdAccess` | the enforced `awsds-prod-athena` workgroup (`EnforceWorkGroupConfiguration` is what makes the output location not the user's choice), the named output prefixes, the results-zone read/write, and the `awsds-prod-debug` assumption (its step 6). `DataScientistStagingAccess` gains **nothing** — Stage 9 step 5.2 only reads it back (no Athena, `DenyEveryWrite` intact) |
| Stage 3 | all six | **the permissions boundary** — see below |

Nobody signs in before Stage 6 (1b step 3.9), so nothing is blocked by this.

## The boundary, deferred by decision 4 (2026-08-16)

A customer-managed boundary must exist as an `aws_iam_policy` of the same name and path **in
every account a set is provisioned into** — a reference that does not resolve fails
*provisioning*, per account, in an account nobody is watching. So no
`aws_ssoadmin_permissions_boundary_attachment` is written here.

**The reason given here until 2026-08-23 has expired, and the decision has not.** That sentence
read *"no governed account has a `foundation/` slice yet"*; every governed account has had one
since Stage 3, and on 2026-08-23 the vending policy above **demonstrated the whole mechanism** —
an `aws_iam_policy` in each member's `foundation/`, referenced from here by name, planning
clean. So what defers the boundary now is the decision itself — which sets get one, what it
denies, and who applies the member half first — and no longer the absence of somewhere to put
it. Re-opening it is decision 4's own business; this note exists so the next reader does not
inherit a blocker that is gone.

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

**It fired on 2026-08-23**, on `DataScientistAccess`, at **10217 of 10240** — 23 characters
against a statement costing ~251. It was answered as written: the vending handshake became
`awsds-org-project-storage-vending`, a customer-managed policy in each member's `foundation/`.
Two things a future reader should take from it rather than rediscover — the margin was reported
by that output **before** the failure, which is what the output is for; and the set still owes
grants to Stages 6 and 7, so the next addition faces the same wall and now has somewhere to go.

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
