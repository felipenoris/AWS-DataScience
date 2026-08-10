# Stage 2 — Terraform foundation

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | **Stage 1a and Stages 1b, 1c and 1d**, all complete. `Staging` is still unvended, so **step 3 skips `terraform-live/staging/bootstrap/`** and step 5 skips its Staging assignments — the same carve-out 1b steps 3 and 5 already carry, picked up at the vend |
| **Consumes** | [D3](../decisions/D03-terraform-state.md), [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D23](../decisions/D23-ou-structure.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md), [D36](../decisions/D36-internal-pki.md) |
| **Proves** | [INT-20](../integrations.md) — the Organizations **policy** delegation into the Identity account, which step 5 assumes and no earlier stage creates |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, Terraform and IAM rules).*

---

**Objective:** the repository can provision infrastructure reproducibly — and the policy set Stage 1c typed
into a console acquires a diff, a review and a rollback.

Everything built here is `[P]` (D11). Nothing in this stage is torn down between sessions, and `make down`
must not be able to reach any of it — which is itself one of the deliverables.

## Step numbers are identifiers, not an order

`plan/conventions.md` §6 already points at "Stage 2 step 9", so the ten numbers below are **stable
addresses** and are kept as they are. They are not the sequence to work in. The sequence is:

1. **Step 1** (repository skeleton) and **step 6** (tooling and hygiene) — nothing can be checked before the
   checkers exist.
2. **Step 9** (the two CI-less checks) — step 5 imports the very policies the wildcard-ARN check guards, so
   the check has to exist *before* the import, not four steps after it.
3. **Step 7** (the three modules), then **step 2** and **step 3** (the bootstrap slices) — with the caveat in
   2.3: bootstrap does **not** consume the modules.
4. **Step 5.1** (the Organizations delegation, in Management, by hand) — the precondition for all of step 5.
5. **Step 5** — `identity/sso/` first, `identity/org-policies/` second (5.5) — then **step 4** (backends
   everywhere else).
6. **Step 8** (the `Makefile`), **step 10** (documentation).

## Who executes what

Three identities, and confusing them produces an `AccessDenied` that reads like a policy bug (Lesson 17).

| Steps | Identity | How |
|---|---|---|
| 1, 6, 7, 8, 9, 10 | **Infrastructure user**, from the laptop | no AWS call at all — these are repository steps |
| 2, 3, 4 | **Infrastructure user** | one `awsds-infra-*` profile per account, one bootstrap each |
| **5.1** | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management**. The only Management-account action in this stage |
| 5 (the rest) | **Infrastructure user** | `awsds-infra-identity` |

**Nothing here is performed by root**, and the infrastructure user still holds no standing assignment on
Management (1b step 4) — 5.1 is why that step matters in practice and not only in principle.

## What this stage costs

**Nothing new against the ceiling, and that is a finding rather than an absence.** Both lines Stage 2 adds
are already inside `plan/cost-model.md`'s floor:

- **Six KMS customer-managed keys, ~USD 1.00/key-month** — one per Terraform-managed account
  (`Sandbox` ×N, `Development`, `Data Governance`, `Staging`, `Production`, `Identity`), plus the
  `production/pki/` key from D36. `PRICING.md` §2 already carries the row and already reads it as
  "one per Terraform-managed account", so **the key created in `bootstrap/` (2.4) is that key** — not a
  seventh one.
- **S3 state storage and its versions**, inside the ~USD 1.00 "S3 data + state + backups" row. Versioning on
  a state bucket accumulates a version per apply; at lab scale it is noise, but 2.1 sets a lifecycle rule
  anyway because a rule added later does not reach what already accumulated.

At **~USD 6-7/month for the keys alone this is the third-largest line in the floor**, so it is worth stating
what it buys: the key policy is where "who can read this state" is expressed, which is the only mechanism
D36 has (Lesson 18 — the infrastructure user authors it and is not constrained by it, so what is left is the
CloudTrail record of a `kms:Decrypt`).

## What this stage deliberately leaves outside Terraform

Step 5's argument — *a policy whose only record is a browser tab is owned by nobody* — applies word for word
to four artefacts Stages 1b-1d also created by hand. They stay console-managed anyway, and the reason is
structural rather than an oversight:

| Artefact | Where it lives | Why it cannot come into code here |
|---|---|---|
| The org-trail metric filter + the group-membership alarm (1b step 8.3) | **Management** | Principle 1: Terraform never holds Management credentials. There is no state bucket there and there will not be one |
| The organization-level Access Analyzer (1b step 8.2) | **Audit** | Audit is not a Terraform-managed account: no bootstrap, no profile, no state. Bringing it in means a seventh state bucket and a seventh key |
| Object Lock on `aws-controltower-logs-*` (1d step 9) | **Log Archive** | Same, plus the object is Control Tower's — managing it from Terraform is landing-zone drift |
| The Control Tower **controls** — Region deny, the two root controls (1c step 7.7) | landing zone | Not policies but controls. If they are ever coded, the resource is `aws_controltower_control` (5.4) |

And two accounts get **no state bucket at all, on purpose**: **`Policy Canary`** (`plan/architecture.md` §3:
"no Terraform slice, no state bucket" — an account whose point is to stay empty) and **Management**. Creating
one for either is the kind of thing that looks like tidiness and is not.

---

## To execute

### 1. Replace the placeholder tree

1. **Delete the empty `terraform/` folder.** It exists on disk only — Git does not track empty directories,
   so this is `rmdir`, not a commit.
2. **Create `terraform-live/` and `terraform-modules/`** exactly as `plan/conventions.md` §6 lays them out.
   That file is the authoritative layout **and it is the only copy** — if this stage needs the layout to
   change, edit §6, do not restate it here.
3. **Create `log/stage-02-terraform-foundation.md`** and its row in [`log/INDEX.md`](../../log/INDEX.md).
   Every decision this stage names as "record which way it went" lands there. *(The user writes it; Claude
   never edits `log/`.)*

### 2. The first bootstrap slice: `terraform-live/sandbox/bootstrap/`

**2.1 — What the slice contains.** One state bucket and the key that encrypts it, and nothing else:

- `aws_kms_key` + alias `alias/awsds-sandbox-tfstate` — **rotation enabled**, deletion window 30 days.
- `aws_s3_bucket` `awsds-sandbox-tfstate`, with **versioning on**, **SSE-KMS** against that key,
  **S3 Bucket Keys enabled** (`plan/cost-model.md`), and `aws_s3_bucket_public_access_block` with all four
  flags true.
- A **bucket policy denying `aws:SecureTransport = false`** — checkov requires it in step 6 anyway, and a
  policy the linter adds for you is a policy nobody read.
- A **noncurrent-version lifecycle rule** (expire after ~90 days). Every apply writes a version; a rule
  added later does not reach what has already accumulated.
- `lifecycle { prevent_destroy = true }` and `force_destroy = false` — `plan/conventions.md` §5.1 rule 1.

**2.2 — The two-phase apply, which is the documented chicken-and-egg exception.**

1. `terraform apply` with **local state**, creating the bucket and the key.
2. Add the `backend "s3"` block (2.5) and run `terraform init -migrate-state`.
3. **Delete the local `terraform.tfstate` and `terraform.tfstate.backup` afterwards** — and note that
   step 6.2's `.gitignore` has to cover them *before* phase 1 runs, not after. A state file carries account
   IDs and resource ARNs, and this repository is hosted on GitHub.
4. **The bucket now holds its own state**, so destroying it is a two-phase operation in reverse. That is
   intended and is what `prevent_destroy` says out loud.

**2.3 — Bootstrap consumes no module, deliberately.** Step 7 creates `s3-bucket` and `kms-key`, and
`plan/conventions.md` requires modules to be consumed **by git tag** — which cannot exist before the module
does. Beyond the ordering, bootstrap is the slice that makes every other slice possible; giving it a
dependency on the tree it bootstraps is how a repository acquires a cycle nobody can unwind at 23:00. Write
it as plain resources and leave it that way.

**2.4 — Which KMS key this is, since `plan/conventions.md` §6 puts "KMS keys" in `foundation/`.** It is not
that key and it cannot be: `foundation/` does not exist yet at bootstrap time, and **`identity/` and
`data-governance/` have no `foundation/` slice at all**. So:

- **The state key is created in `bootstrap/` and lives there.** It is the "one per Terraform-managed account"
  key that `PRICING.md` §2 and `plan/cost-model.md` already count.
- `foundation/` keys — where a `foundation/` exists — are the *general-purpose* keys for that account's data
  and logs, and they are **additional**, not the same object.
- The two are separated for the D31/D36 reason, applied one level down: a key shared between state and data
  makes "who may read the state" and "who may read the data" the same question.

**2.5 — The backend block, and the one place `plan/architecture.md` §4.1's no-region-literals rule cannot
apply.** A `backend` block **cannot interpolate variables** — no `var.region`, no locals. Reconcile it, do
not let step 9's grep discover it:

- Use **partial backend configuration**: keep `backend "s3" {}` in `providers.tf` and put `bucket`, `key`,
  `region`, `kms_key_id` and `use_lockfile = true` in a per-slice **`backend.hcl`**, passed as
  `terraform init -backend-config=backend.hcl`.
- `backend.hcl` is not a `.tf` file, so step 9's check does not read it, and the region literal sits in one
  generated file per slice instead of in the code. The `Makefile` (step 8) generates it.
- **Locking is `use_lockfile = true`** (D3) — native S3 locking, no DynamoDB table. Terraform **1.15.8** is
  installed and supports it.
- `key` is `<account>/<slice>/terraform.tfstate`, one state file per slice, one bucket per account (D3).

### 3. The remaining bootstrap slices

**One state bucket per account that Terraform manages, no shared state across environments (D3).**

**3.1 — Create now:** `development/`, `data-governance/`, `production/` and `identity/`.

**3.2 — Skip `staging/bootstrap/` until the account is vended.** It does not exist yet (Stage 1a's deferred
vend). Nothing before Stage 8 needs it, and D34 removed the ordering hazard that used to make deferring an
account expensive.

**3.3 — `sandbox/bootstrap/` is per business unit (D35), and N is 1.** Do not invent the per-unit naming
here: [Stage 14](stage-14-sandbox-vending.md) owns it. What this step owes Stage 14 is that nothing in the
bootstrap slice is written as *the* sandbox — no hardcoded `awsds-sandbox-tfstate` outside a variable.

**3.4 — `production/pki/` needs its state under the PKI key, not the account state key (D36).** This is the
detail that decides whether D36 is a control or a folder:

- D36 puts the CA **root private key in a state file**. If every Production slice shares one bucket
  encrypted with one key, then "who can read Production state" and "who can mint a certificate for any
  internal name" are the same permission — which is exactly the merge D36 exists to prevent.
- **The S3 backend accepts `kms_key_id` per slice**, and a per-object SSE-KMS key overrides the bucket
  default. So `production/pki/backend.hcl` names the PKI key; every other Production slice names the account
  state key. One bucket, two keys, two answerable questions.
- **This is what makes D36's alarm work at all** — an alarm on `kms:Decrypt` against the PKI key is
  meaningless if that key never encrypted anything, and it is *noise* if the key also encrypts the state
  somebody reads to change a subnet.
- **Verify while executing (i):** that the bucket's default-encryption setting and its TLS-only policy do
  not force a single key and reject the override. If they do, `pki/` gets its **own bucket**, which costs
  nothing and is the honest fallback.

### 4. Backends for every other slice

**The previous wording of this step ("migrate every subsequent slice") described work that does not exist.**
Only `bootstrap/` migrates, because only `bootstrap/` has to run before its own backend exists. **Every other
slice declares the backend from its first `init` and never holds local state at all.** Say it that way so
nobody goes looking for a migration to perform.

### 5. `terraform-live/identity/` — the import that gives the policy set an owner

This is the substance of the stage. Stages 1b-1d create permission sets, groups, assignments, SCPs, RCPs, tag
policies and declarative policies **by hand**; without this step nothing regenerates them, no stage owns
them, and the only record of what they say is a browser tab. That set is the one that can lock the
organization out of itself, and since D30 was reverted there is **no principal inside a governed account that
can work around a mistake in it** (D16 — the Management root is the whole recovery path). Code gives it a
diff, a review and a rollback; the console gives it none of the three.

*(This consequence arrived with D30 and outlived it. D30's own reason was narrower — a carve-out condition
repeated across several policies has to be generated, not typed — and that reason went away with the
decision. The ownership hole it happened to close did not.)*

**It is two slices, not one, and the seam is not a matter of taste.** `plan/conventions.md` §6 carries the
layout; the reasoning belongs here, because it is what the rest of this step is organised around:

| | `identity/sso/` | `identity/org-policies/` |
|---|---|---|
| **What it holds** | permission sets, groups, assignments | SCPs, RCPs, tag policy, declarative policy |
| **Reached through** | the **Identity Center** delegated administrator (`sso.amazonaws.com`, 1b step 1) | a **resource-based delegation policy** on the organization (5.1, INT-20) |
| **Proved when** | Stage 1b, already | **never** — 5.1 is the first attempt |
| **D34's rule** | grants are **enumerated** | the floor is **discovered** |
| **A mistake costs** | a person cannot sign in | the organization can be locked out of itself |

Four separations in one folder split, and any one of them would justify it:

1. **Two different delegations, granted by two different mechanisms.** Nothing about the first implies the
   second works, and 5.1 is the one that has never been exercised.
2. **They fail independently, so they should not stall together.** If 5.1 turns out to be incompatible with
   the landing zone (5.6), the SSO half still lands — with the boundary already drawn, rather than as a state
   move performed under the disappointment.
3. **Opposite rules under D34** — `for_each` on one side, written-out lists on the other. A single slice
   invites the discovered form to leak into assignments, which is exactly the failure this design exists to
   prevent.
4. **Very different blast radius.** An `apply` against `org-policies/` can deny the organization its own
   repair path; an `apply` against `sso/` cannot. Different risk deserves a different plan output to read
   before saying yes.

Both are applied with **`awsds-infra-identity`**, both keep their state in the Identity bootstrap bucket
under separate keys, and `sso/` reads nothing from `org-policies/` — there is no `terraform_remote_state`
between them, which is what keeps the independence real rather than nominal.

**5.1 — The precondition no stage creates yet, and `org-policies/` does not run without it.**

Permission sets reach the Identity account through the **Identity Center** delegated administrator
(1b step 1, `sso.amazonaws.com`). **SCPs, RCPs, tag policies and declarative policies do not** — they are
AWS Organizations objects, and by default only the Management account can touch them. Nothing in Stage 1a or
1b delegates that. So:

- **What it is:** a **resource-based delegation policy** on the organization
  (`organizations:PutResourcePolicy`), naming the Identity account as principal. It is not
  `register-delegated-administrator`; that is a different mechanism and it does not cover policy management.
- **Who runs it:** `AWS Control Tower Admin`, from Management (D34) — the only Management action in this
  stage. Record the exact document in `log/stage-02-terraform-foundation.md`.
- **What it must grant**, per AWS's own examples: the read half (`DescribeOrganization`,
  `ListRoots`, `ListOrganizationalUnitsForParent`, `ListChildren`, `ListParents`, `ListAccounts`,
  `ListPolicies`, `ListPoliciesForTarget`, `ListTargetsForPolicy`, `ListTagsForResource`) **plus**
  `CreatePolicy` / `UpdatePolicy` / `DeletePolicy` / `AttachPolicy` / `DetachPolicy`, each scoped by a
  `organizations:PolicyType` condition to the four types this project writes.
- **The `Resource` list must use the wildcard OU form** — `arn:aws:organizations::<mgmt>:ou/o-<org>/*` plus
  the `root/o-<org>/r-<root>` ARN and the account wildcard. AWS documents that naming a **single** OU
  *"excludes child OUs and accounts under child OUs"*, and this organization is **two levels deep** (D23:
  `Sandboxes` under `Interactive`). The same nesting that breaks a single-level `for_each` in 5.3 breaks a
  single-OU delegation here, and it breaks it the same silent way.
- **Exclude `DisablePolicyType` and `EnablePolicyType`.** They act on the root and turning a policy type off
  detaches every policy of that type at once. Nothing in this design needs them after 1c step 7.2.

**The blast radius this creates, stated rather than discovered.** AWS's own note is that the delegation
*"allows delegated administrators to perform the specified actions on policies created by any account in the
organization, including the management account"* — which includes **Control Tower's own guardrail SCPs**.
Scoping by policy ARN would fix it, and cannot: this project's policies have no ARNs until they are created.
So this is the **second** widening of the Identity account's blast radius, after the group-membership path
1b step 1 records — and its control is the same one: 1b step 8.3's alarm, plus the CloudTrail record. Write
it into `ORGANIZATION.md`'s description of that account rather than leaving it here.

**5.2 — What is imported, and — the half that is easier to get wrong — what is not.**

| Imported | Into | Left alone |
|---|---|---|
| This project's **five groups** (1b step 2) | `sso/` | **Control Tower's groups** — `AWSControlTowerAdmins`, `AWSAccountFactory`, the auditor and per-account groups |
| This project's **seven permission sets** (1b step 3.1) | `sso/` | **`AWSAdministratorAccess` and every other Control Tower set** — editing them is landing-zone drift (D10, consequence iii) |
| Their **group assignments** | `sso/` | The **direct Account Factory assignments** to the infrastructure user (D32, 1b step 3.8) — and if 1b's verification (vi) found they are re-created, they are a permanent property of a vended account, not something to model |
| The **org-root SCP set** (1c step 7.5), the **per-OU sets** (7.6), the **RCPs**, the **tag policy** and the **declarative EC2 policy** (7.8) | `org-policies/` | The **Control Tower controls** (7.7) — see 5.4 |

- **The declarative policy was missing from every earlier version of this step.** 1c step 7.8 creates one
  (IMDSv2 and EC2 public-access defaults) and it is an Organizations policy like the others.
  **Verify while executing (ii):** that `aws_organizations_policy` accepts `type =
  "DECLARATIVE_POLICY_EC2"` in the pinned provider version. If it does not, that one policy stays console
  managed and is recorded as such (Lesson 5 — an unowned artefact is worse when nobody wrote down that it is
  unowned).
- **Read the three landing-zone logs before writing anything** —
  `log/stage-01b-identity-and-controls.md`, `log/stage-01c-preventive-policies.md` and
  `log/stage-01d-org-wide-enablement.md`. Two of their four
  execute-time decisions change what exists to import: whether the `Interactive` OU got a policy set at all
  (1c step 7.6) and what this project's administrator permission set is actually called (1b step 3.2).

**5.3 — Write it so an OU or account created later is covered without anybody remembering (D34).**

Accounts and OUs are vended from the console, permanently and by design, and **that cannot make this state
inconsistent** — nothing here declares `aws_organizations_account` or
`aws_organizations_organizational_unit`, and a state file tracks only what a configuration declares. The risk
is the opposite of drift and it is silent: a new OU with no attachment, or a new account outside every
enumerated ARN condition, with `terraform plan` reporting **"No changes"** in both cases.

**The rule: the floor is discovered, the grants are enumerated — and the slice split runs along that same
seam**, which is the fourth reason to have made it.

1. **Discovered, in `org-policies/`** — attachments, the organization-root set and the tag policy are
   `for_each` over the `aws_organizations_*` data sources.
2. **Enumerated, in `sso/`** — **permission set assignments stay written out one by one**, because an account
   silently acquiring `DataScientistAccess` on the next apply is the failure this design exists to prevent.
3. **The nesting depth is 2 and is no longer an open question** (D23, 2026-08-09): `Sandboxes` sits under
   `Interactive`, and every business unit's Sandbox account sits under `Sandboxes`.
   `aws_organizations_organizational_units` returns the children of **one** parent, so a single `for_each`
   over the root's children enumerates neither the nested OU nor the accounts in it.
4. **There is a named data source for exactly this, and it is cheaper than hand-rolled recursion:**
   **`aws_organizations_organizational_unit_descendant_organizational_units`**, given the root ID, returns
   descendants at any depth. **Verify it against the pinned provider version before relying on it**
   (registry documentation for this family has been copied between pages) — the fallback is to enumerate
   both levels explicitly.
5. **Accounts do not have this problem and it is worth knowing which half is which.**
   `data.aws_organizations_organization.this.accounts` is already **flat**: it lists every account regardless
   of nesting. The depth problem is an *OU* problem, so it affects attachments and not account-keyed
   conditions.
6. **Fail the check, whichever way it is written:** step 9 gains a third check — an OU that neither level
   matched is an error, not a silent pass.
7. **Still to verify here:** that the `for_each` key is stable enough that adding an OU does not re-create
   the existing attachments. A plan that wants to destroy and re-create an SCP attachment is a momentary hole
   in the ceiling.

**5.4 — What is deliberately not imported: the region restriction.** It is Control Tower's own Region deny
control (1c step 7.7), not one of the hand-written documents, and the SCP that implements it is generated and
owned by the landing zone. Importing that SCP would put Terraform and Control Tower in a fight over the same
object — the landing-zone drift this plan already refuses to create for permission sets. If it is ever to be
in code, the resource is **`aws_controltower_control`** — the control, not the policy it emits.

**5.5 — The check that the import is faithful: `terraform plan` must come back empty, in both slices.** Not
"small", empty. An import that plans a change is either a policy that differs from what is attached, or a
resource whose attributes Terraform normalises differently — and the first of those is a control that does
not say what you think it says.

**Do `sso/` first and `org-policies/` second**, and not for convenience: `sso/` exercises an import mechanism
against objects whose worst failure is somebody being unable to sign in, so any misunderstanding about how a
faithful import behaves surfaces where it is cheap. `org-policies/` is the same mechanism against the set
that can lock the organization out of itself.

**5.6 — The fallback, if 5.1 turns out to be incompatible with the Control Tower landing zone.** Same family
of question as the Identity Center delegation in 1b step 1, and the split above is what makes the answer
cheap:

- **`identity/sso/` lands anyway.** It depends only on the Identity Center delegation, which 1b already
  proved, so a failure in 5.1 costs this stage half its scope rather than all of it — and costs no state
  move, because the boundary was drawn before the attempt rather than after it.
- **`identity/org-policies/` stays empty and the four policy types stay console-managed**, exactly as 1c left
  them. Step 9.2's wildcard check degrades from a script to a manual review — strictly worse, and
  **recorded as such in `log/stage-02-terraform-foundation.md`**, not absorbed (Lesson 5: an unowned artefact
  is worse when nobody wrote down that it is unowned).
- **Keep the empty slice, with a `README.md` naming INT-20 as the blocker.** An empty folder that says why is
  the only thing that will make somebody retry this; a deleted folder is a plan that quietly gave up.

### 6. Repository hygiene

**6.1 — Install the tooling first, because none of it is present.** `terraform`, `aws` and `uv` are
installed; **`tflint`, `checkov` and `pre-commit` are not.** Install them, pin the versions, and add them to
`CLAUDE.md`'s "Tools installed in the current environment" list — a gate that depends on a tool nobody
recorded installing is a gate the next machine does not have.

**6.2 — `.gitignore`, and it has to be right before step 2 runs.**

- **Ignore:** `.terraform/`, **`*.tfstate`**, `*.tfstate.*` (which covers `.backup`), `.terraform.lock.info`,
  `crash.log`, `*.tfvars` that carry account IDs, and `backend.hcl` if the `Makefile` generates it.
- **`*.tfstate` was missing from the previous version of this step**, which listed only `.terraform/` and
  `*.tfstate.backup` — so the local bootstrap state from 2.2, the one file this stage most insists must never
  be committed, was not covered by the rule meant to cover it.
- **Do not ignore `.terraform.lock.hcl`** — it is committed on purpose (6.3).

**6.3 — The lock file is committed, and it needs more than one platform in it.** The laptop is
`darwin_arm64`; the GitLab runners of Stage 7-8 are Linux (D8 puts GitLab on a Graviton instance, so
`linux_arm64` as well as `linux_amd64`). A lock file generated only on the laptop makes every runner fail on
`terraform init` with a checksum error that reads like a supply-chain attack.

```bash
terraform providers lock -platform=darwin_arm64 -platform=linux_amd64 -platform=linux_arm64
```

**6.4 — `pre-commit` with `terraform fmt`, `terraform validate` and `tflint`.**

**6.5 — `checkov` as a required gate, not an optional one** — a policy check that can be skipped is a policy
check that will be skipped on the day it would have mattered. Any suppression is an inline
`# checkov:skip=CKV_...` with a reason on the same line, never a global exclusion.

### 7. The first reusable modules

`terraform-modules/`: **`s3-bucket`, `iam-role`, `kms-key`.**

- **`s3-bucket`** enables **S3 Bucket Keys** by default (`plan/cost-model.md`) and blocks public access
  unconditionally. The account-level block from 1c step 7.4 is the blanket; this is the module-level half,
  and neither replaces the other.
- **`iam-role`** takes a **permissions boundary as a required argument**, so omitting one has to be
  deliberate (`plan/conventions.md`, IAM rules).
- **`kms-key`** with rotation on and a deletion window, because both are easier to set than to change.
- **Tag every module release; callers pin the tag** (`plan/conventions.md` §6) — never a branch.

### 8. Teardown/rebuild tooling (D11)

**8.1 — Each slice declares its layer** (`[P]`/`[D]`/`[E]`) in a table the `Makefile` reads, rather than in a
comment. `plan/conventions.md` §6 already assigns every slice its layer; the table is that assignment made
executable.

**8.2 — `make up ENV=<env>` / `make down ENV=<env>`.** `down` destroys the `[E]` slices in reverse dependency
order and stops the `[D]` instances; `up` starts the `[D]` instances and applies the `[E]` slices.

**8.3 — Four refusals, each of which is a bug if it is missing.**

1. **Never touch a `[P]` slice** — the general rule.
2. **`make down` with no `ENV` must fail**, not default to everything.
3. **`production/pki/` is excluded from every `down` path** (D36) — rotating a root on a session boundary
   invalidates three client surfaces at 09:00.
4. **`bootstrap/` is unreachable from either target**, which is the specific case the Validation below tests.

**8.4 — `make status`** reports what is running and the estimated hourly burn. **The rates come from a static
table sourced from `PRICING.md`**, not from a live pricing call: a status command that needs the network is a
status command that fails when you most want it (and prices are measured, not reasoned — Lesson 6).

**8.5 — `ENV` names a business unit's sandbox, not *the* sandbox (D35).** Stage 14 step 6 makes the same
pair work against a generated unit; write nothing here that assumes N=1.

**8.6 — The Studio-app teardown hook exists but is a no-op until Stage 6.** `plan/conventions.md` §6
requires `make down` to delete running apps through `sagemaker:ListApps`/`DeleteApp` against the
blueprint-provisioned domain, discovering the domain ID rather than having it pasted in. Write the hook now
and leave it empty — a hook added later is a hook that is missing from the first teardown that needed it.

### 9. The checks that keep two conventions honest

**None of these run in "CI", because there is no CI.** GitLab arrives at Stage 7 and `.gitlab-ci.yml` at
Stage 8. Until then the enforcement surfaces are **`pre-commit`** and a **`make check`** target calling
scripts in `scripts/` — the shape [`scripts/check-plan-refs.sh`](../../scripts/check-plan-refs.sh) already
establishes. **Stage 8 steps 5 and 6 move them into the pipeline** — step 5 is the `checkov` gate, step 6 is
this repository's own `fmt`/`validate`/`plan` pipeline. Write them as scripts so that move is a
`.gitlab-ci.yml` line and not a rewrite.

**9.1 — No region literals** (`plan/architecture.md` §4.1). `var.region` in every slice, AZs from
`data.aws_availability_zones` (or `zone_ids`, if 1b step 6 found the mappings differ), AMIs from SSM public
parameters. A `grep` over `*.tf` that fails on a hardcoded region keeps this honest at no cost — and it
**must skip `backend.hcl`**, for the reason in 2.5.

**9.2 — No wildcard account in an ARN condition.** This one guards a control rather than a convention: fail
if any policy document in `terraform-live/identity/` — either slice — carries `arn:aws:iam::*:role/...`.
That pattern means
"any principal of this name, in **any** account", so a condition meant to name one role silently names a role
anybody can create. It is invisible in a `plan` and cheap in a script. *(This check used to also require an
`awsds-scp-recovery` carve-out in every `Deny`; that half went away with D30. The wildcard half did not,
because it applies to the per-function carve-outs the design still has — D26, D27.)*

**9.3 — Every OU is matched by an attachment** (5.3). Enumerate the organization's OUs and fail if one of
them appears in no `for_each` result. This is the check that turns D34's silent failure mode into a red
build.

### 10. Documentation

Update **`README.md`** with the repository layout and the AWS resource structure (required by `CLAUDE.md`),
add the links used to **`REFERENCES.md`**, and record in **`log/stage-02-terraform-foundation.md`** the four
decisions listed below.

---

## Deliverables

Each is written so its output differs between working and broken (Lesson 13):

- **A slice applies end to end against a real account:** `terraform apply` in `sandbox/bootstrap/` under
  `awsds-infra-sandbox`, then `terraform init -migrate-state`, then a second `terraform plan` that reports
  **no changes** while reading state from S3.
- **Locking is real:** two concurrent `terraform plan` runs against the same slice — the second reports a
  lock held, rather than both succeeding.
- **Both imports are faithful:** `terraform plan` is **empty** in `identity/sso/` *and* in
  `identity/org-policies/`, and `aws organizations list-policies --filter SERVICE_CONTROL_POLICY` lists the
  same policy IDs the second state holds.
- **The two slices are independent, which is why they are two:** `terraform state list` in `sso/` names no
  `aws_organizations_*` resource, and `org-policies/` names no `aws_ssoadmin_*` one. Neither reads the other
  through `terraform_remote_state`.
- **The delegation took effect** (INT-20): `aws organizations describe-policy --policy-id <one of ours>`
  succeeds **under `awsds-infra-identity`** — from the Identity account, which is what makes it evidence
  about the delegation rather than about the policy existing.
- **The checks fail on purpose:** a commit introducing `us-west-2` in a `.tf` file, and one introducing
  `arn:aws:iam::*:role/x`, are both rejected. A check nobody has seen fail is a hypothesis.
- **The `Makefile` refuses what it must:** `make down ENV=sandbox` is a **safe no-op** at this point — no
  `[E]` or `[D]` slice exists yet — and `bootstrap/` is untouched; `make down` with no `ENV` exits non-zero.

## Validation

1. **Reproducibility:** create a throwaway `[E]` slice — `sandbox/scratch-test/`, holding one SSM parameter
   and nothing else, so it is free and instant — then `make down`, then `make up`, and confirm it comes back
   identical. Naming it here rather than leaving "a throwaway slice" to the keyboard is Lesson 16.
2. **Isolation:** confirm `make down` leaves `bootstrap/` untouched — by reading the plan output, not by
   trusting the target list.
3. **Delete the throwaway slice** when both pass.

## Decisions due while executing

**Blocking questions for the user: none.** Three decisions are *made* during the stage and each is written
into `log/stage-02-terraform-foundation.md` rather than left to whoever is at the keyboard (Lesson 16):

1. **The exact Organizations delegation document** (5.1) — which actions, which resource ARNs, and the
   explicit note that it reaches Control Tower's own SCPs.
2. **Whether `production/pki/` shares the Production state bucket** with its own `kms_key_id`, or gets a
   bucket of its own (3.4).
3. **The noncurrent-version lifecycle on the state buckets** (2.1) — the retention, and that it is a cost
   choice rather than a compliance one.

*(A fourth used to be here — whether to split `terraform-live/identity/`. It was settled on 2026-08-09,
before execution: the split is the design, its reasoning is in step 5 and the layout is in
`plan/conventions.md` §6. Splitting afterwards would have been a state move, which is the whole reason it
could not be left open.)*

## Risks

- **Step 5.1 widens the Identity account's blast radius a second time**, and unlike 1b step 1's widening this
  one reaches Control Tower's own guardrails. It has no preventive control above it; 1b step 8.3's alarm and
  the CloudTrail record are what is left (Lesson 18).
- **An import that plans a destroy is the dangerous outcome, not a failed import.** Re-creating an SCP
  attachment is a momentary hole in the ceiling, in an organization whose only repair path is the Management
  root. If 5.5's plan is not empty, stop and read it — do not apply to "converge".
- **Everything here is `[P]`** (D11). Nothing in this stage is destroyed between sessions, and the state
  buckets carry `prevent_destroy` for a reason that is not stylistic: the bucket holds its own state.
- **The tooling gate is only as strong as the machine it is installed on** (6.1) until Stage 8 puts it in a
  pipeline.

## Verifications to answer while executing

Record every answer in `log/stage-02-terraform-foundation.md`, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | Does the bucket's default encryption / TLS policy accept a per-slice `kms_key_id` override for `pki/`? | 3.4 |
| ii | Does the pinned provider support `aws_organizations_policy` with `type = "DECLARATIVE_POLICY_EC2"`? | 5.2 |
| iii | Does the Organizations **policy** delegation coexist with the Control Tower landing zone without raising drift? | 5.1 |
| iv | Does `aws_organizations_organizational_unit_descendant_organizational_units` really recurse, in the pinned version? | 5.3 |
| v | Is the `for_each` key stable enough that adding an OU does not re-create existing attachments? | 5.3 |

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
