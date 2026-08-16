# Stage 2 — Terraform foundation

| | |
|---|---|
| **Status** | **DONE — 2026-08-16. Every step closed and all nine verifications answered**, (iii) last: read from Management as `AWS Control Tower Admin`, `driftStatus: IN_SYNC` with the delegation intact — **and with two limits stated rather than glossed: the landing-zone manifest has no concept of a resource policy, and the landing zone has run exactly once (`CREATE`), so it has not yet had occasion to disagree.** *What follows is the history of the three sittings, kept because the order the work happened in is why several things were caught.* **Steps 5.0, 5.1, 1, 6, 9, 2 and 3 closed 2026-08-15** — the delegation applied and *exercised* (INT-20 answered: `identity/org-policies/` is scoped to all ten documents), the five `bootstrap/` slices created with the version pin and a committed multi-platform lock, the `pre-commit`/`tflint`/`checkov` chain passing end to end, the four checks written, wired into **`make check`** and into the commit gate, each demonstrated failing on purpose — **and the project's first `terraform apply`**: `sandbox/bootstrap/` applied local, migrated into its own bucket, second plan empty, locking proven by two concurrent plans. **Step 3 applied the same slice in the four remaining accounts** — **five state buckets now exist**, `production/` carries 3.4's second key, every second plan is empty, and the copy's failure mode is guarded by a fifth check (3.5). **Step 4 is a statement, not work.** **2026-08-16: step 5.1a closed** — the delegation is narrowed to the `InfrastructureAccess` role, verification (ix) answered in all three halves, `DEL-10` green; **decisions 4, 5 and 6 settled** (inline-only boundary, `replace(file(…))`, the CLI import); and **`terraform-live/identity/sso/` is written** — six persona sets, the shared deny fragment, ten enumerated assignments, `InfrastructureAccess` **imported** (seven objects, `0 to change`) and the 22 creates **applied** — the next `plan` is empty, no provisioning failed, and the six sets reach exactly the accounts 1b step 3.1 assigns them. **Step 5 closed the same day with `org-policies/`** — ten documents and ten attachments **adopted, none created**, `0 to add / 10 to change / 0 to destroy` with not one `content` or `type` diff in it, second plan `No changes`, and the ceiling proven unrewritten by the bytes rather than by the plan. **Sitting C, 2026-08-16, closed the stage in three blocks.** *Step 8*: the layer table, `make up`/`down`/`status`/`slices`, all four refusals demonstrated (refusal 3 against a fixture that claimed `production/pki` was `[E]`), a sixth check in `make check` and in the commit gate. *The Validation*: `sandbox/scratch-test/` applied, destroyed and rebuilt — the destroy plan named one SSM parameter and `bootstrap/` sat in the refused list — then deleted, its orphan state object with it; **the run found that `awsds` is a reserved SSM Parameter Store prefix** and that the rebuild is proven by a restarted `Version`, not by the ARN. *The close-out*: **(ii), (iv), (v) and (viii) answered**, three of them by the step 5 applies and recorded here for the first time. **Step 7 left the stage** for Stage 3 step 1.1a. **Roteiro revised 2026-08-15 against the closed landing zone**, see the table below |
| **Prerequisites** | **Stage 1a and Stages 1b, 1c and 1d**, all complete (the landing zone closed 2026-08-15). `Staging` is still unvended, so **step 3 skips `terraform-live/staging/bootstrap/`** and step 5 skips its Staging assignments — the same carve-out 1b steps 3 and 5 already carry, picked up at the vend |
| **Consumes** | [D3](../decisions/D03-terraform-state.md), [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D16](../decisions/D16-break-glass.md), [D23](../decisions/D23-ou-structure.md), [D27](../decisions/D27-catalog-maintenance.md), [D30](../decisions/D30-scp-recovery.md) *(reverted; its surviving consequence is step 5's rationale)*, [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md), [D36](../decisions/D36-internal-pki.md), [D37](../decisions/D37-nested-ou-inheritance.md) *(5.3/9.3 — `Sandboxes` deliberately carries nothing)* — **plus, for step 5's six permission sets, the design of record in [Stage 1b step 3](stage-01b-identity-and-controls.md) and the decisions it lists** (D14, D18-D22, D31). They are written here and specified there; neither file restates the other |
| **Proves** | [INT-20](../integrations.md) — the Organizations **policy** delegation into the Identity account, which step 5 assumes and no earlier stage creates |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, Terraform and IAM rules).*

---

**Objective:** the repository can provision infrastructure reproducibly — and the policy set Stage 1c typed
into a console acquires a diff, a review and a rollback.

Everything built here is `[P]` (D11). Nothing in this stage is torn down between sessions, and `make down`
must not be able to reach any of it — which is itself one of the deliverables.

## What the closed landing zone changed in this stage

**Revised 2026-08-15, reading Stages 1b-1d's measurements against what was written here before any of them
ran.** Each row is a *measurement*, not a preference, and each one changed a step rather than confirming it.
The two that move work are the first and the last.

| What was measured | Where | What it changes here |
|---|---|---|
| **Three project SCPs sit on the organization *root*** — `awsds-org-scp-baseline`, `awsds-org-scp-perimeter`, `awsds-org-scp-tag-enforcement` — **and so do the RCP, the tag policy and the declarative policy.** Only **four** documents are per-OU | 1c step 7, `aws/output/org-policies.txt` §1 | INT-20's sharp edge is now the stage's **first** action, not its fifth: six of the ten documents are reachable only if the delegation reaches **root** attachments. **5.0** is new |
| **The per-OU documents are all different**, and three OUs carry none — `Policy Test`, `Security`, and `Sandboxes` **by decision** (D37) | 1c 7.6, D37, `org-policies.txt` §4 | **5.3 was wrong in shape.** Attachments cannot be discovered: a `for_each` that attaches "the OU document" to every discovered OU would put one on `Sandboxes` and silently reverse D37. Rewritten below |
| **Organizations reads succeed from the Identity account under the Region ceiling** — `org-policies.py` runs as `awsds-infra-identity` and every call returns | 1d step 12, `org-policies.txt` §5 | Removes the fear that `CTMULTISERVICEPV1` blocks this slice outright (Organizations answers in `us-east-1`). **The write half is not proven by it** — verification (vii) below |
| **A permission set provisioned into Management cannot be altered from Identity**, and the deny is anchored on the **permission set** ARN, so it covers that set in every account | 1b step 5.1 | Confirms 5.2's "leave `AWSAdministratorAccess` alone" is a *wall*, not a convention. `InfrastructureAccess` is not provisioned into Management and is unaffected |
| **`awsds-org-scp-tag-enforcement` names `ec2:RunInstances` and nothing else** | 1c 7.8, the document | No create in this stage can be denied for a missing tag. The mandatory-tag *convention* still applies and 2.1 now says how it is satisfied once |
| **`policies/*.json` are templates — eight placeholders across four files**: `<ORG_ID>` ×6 (the RCP ×4, the perimeter SCP ×2), `<ORG_PATH_DATA>` ×1 in the **baseline** document, `<ACCOUNT_ID_DATA>` ×1 in the `Data` document *(census corrected 2026-08-15; an earlier row counted `<ORG_ID>` ×8 and put `<ORG_PATH_DATA>` in the `Data` file)* | measured over `policies/`, `render.py` | 5.5's "the import compares a document against itself" needs a **mechanism**, and `templatefile()` is not it — the placeholder syntax is wrong for it. Written out below |
| ~~**`tflint`, `checkov` and `pre-commit` are absent**~~; `terraform` is v1.15.8 and `uv` is present; the placeholder `terraform/` folder no longer exists | measured on this laptop, 2026-08-15 | 6.1 stands as written and 1.1 is **obsolete**. **All three installed the same day** (6.1 below); `tflint` **v0.64.0** by release download, the other two by `uv tool install` |
| **A borrowed session outlives the command that needed it** (Lesson 25) | 1d step 9 | One rule, stated in "Who executes what": this stage uses `AWS_PROFILE` and never `eval $(aws sts assume-role …)` |
| **Until 2026-08-15 no snapshot listed the policy id of the RCP, the tag policy or the declarative policy** — `org-policies.py` §1 read `SERVICE_CONTROL_POLICY` with ids and the RCP only as a presence check, so three of the ten ids existed only in the 1c log | `org-policies.txt` | The import needs all ten ids. The script is fixed, and `import-ids.py` emits every import string — see "The instruments this stage runs on" |

## Step numbers are identifiers, not an order

`docs/plan/conventions.md` §6 already points at "Stage 2 step 9", so the ten numbers below are **stable
addresses** and are kept as they are. They are not the sequence to work in. The sequence is:

1. **Step 5.0 and step 5.1 — the delegation, and the reachability question under it.** *(Moved to the front
   on 2026-08-15; it was fourth.)* Two facts moved it, and either alone would be enough. **It can delete
   scope**: INT-20 states plainly that the plausible outcome is not "the delegation is hard" but "the
   delegation works and still cannot touch a root-attached document" — and the landing zone then attached
   **six of ten documents to the root**, so that outcome now costs most of `org-policies/` rather than a
   corner of it. **And it needs nothing this stage builds**: no repository, no state bucket, no Terraform,
   no module — one console action on Management, plus two reads and one deliberate write from
   `awsds-infra-identity`. Anything that can
   remove half a stage's scope and costs nothing to try belongs before the half it removes, not after it
   (Lesson 19: a blocking input is re-checked against the requirement, not against the mechanism).
2. **Step 1** (repository skeleton) and **step 6** (tooling and hygiene) — nothing can be checked before the
   checkers exist. Step 1 also **pins the provider**, which two verifications depend on.
3. **Step 9** (the four CI-less checks) — step 5 writes and imports the very policies the wildcard-ARN check
   guards, so the check has to exist *before* them, not four steps after.
4. **Step 2** and **step 3** (the bootstrap slices).
5. **Step 5** — `identity/sso/` first, `identity/org-policies/` second (5.5). **Step 4** is a rule these two
   obey, not work of its own.
6. ~~**Step 7** (the three modules).~~ **Moved out of this stage entirely on 2026-08-16 — it is now Stage 3
   work.** The reasoning is in step 7 below; the short form is that the argument which moved it to the end
   of the stage on 2026-08-15 does not expire at the end of the stage.
7. **Step 8** (the `Makefile`), the **Validation**, **step 10** (documentation), and the stage's own
   **close-out** — the status header and the verifications table.

**What the reordering does not change:** step 5.1 is still the only Management action, and it is still
performed by `AWS Control Tower Admin`. What changes is that the stage now learns its own scope on the first
evening rather than on the fourth.

**Three sittings, and the first seam is 5.0's answer** — the same shape Stage 1c used, and for the same
reason. **Sitting A** is items 1-4 above: the delegation and its reachability question, the skeleton, the
tooling, the checks, and the bootstrap slices. It ends with **state buckets that exist and a known scope for
the second half** — which is a place the work can genuinely be put down. **Sitting B** is item 5, the two
identity slices, and it is the one that **must not be split**: `sso/` and `org-policies/` are two applies,
but an import left half-done is a state file that disagrees with the organization, and that is the one
condition in this stage nobody wants to sleep on. *(Both closed 2026-08-16.)* **Sitting C is item 7** and is
described next — it was called "the close-out" for a day, which under-counted it by three steps.

### Sitting C — what is actually left, in order *(written 2026-08-16)*

**The reason this needs writing down rather than being obvious:** on 2026-08-16 both `CLAUDE.md` and
`docs/log/INDEX.md` said the stage had nothing left but its status header. Measured against the disk that
was wrong in three places — `terraform-modules/` held only a `README.md`, the `Makefile` said in its own
header that `up`/`down`/`status` were *"not here yet"*, and no `[E]` slice had ever existed, so the
Validation had never run. **A stage is closed against its own file, not against a summary of it**, and the
summary is what was current.

| Block | What | AWS? |
|---|---|---|
| ~~**1**~~ | ~~**Step 8**~~ — **DONE 2026-08-16**: the layer table as data, `up`/`down`/`status`, the four refusals of 8.3 each demonstrated, and 8.6's Studio hook | none |
| ~~**2**~~ | ~~**The Validation**~~ — **DONE 2026-08-16**: `sandbox/scratch-test/` applied, torn down, rebuilt and deleted; **verification (iv) answered** in the same session; the `awsds`/SSM reserved-prefix collision found | one session as `awsds-infra-sandbox-1` |
| ~~**3**~~ | ~~**Step 10** and the **close-out**~~ — **DONE 2026-08-16**, **(iii) included**: read from Management as `AWS Control Tower Admin` the same evening, through a third `aws/cloudshell/` script | one **Management** CloudShell run |

**Block 1 has nothing to operate on, and that is the argument for doing it now rather than later.** All
seven slices on disk are `[P]`, so `make up` and `make down` are no-ops until Stage 3's `egress/` — which is
precisely why the machinery is written before the first `[E]` slice exists rather than after it. It is 8.6's
own reasoning applied to the whole target: *a hook added later is a hook that is missing from the first
teardown that needed it.*

**Block 3 carries more than a header, because four verifications were answered by the step 5 applies and
recorded nowhere.** (ii) — the pinned provider accepted `DECLARATIVE_POLICY_EC2`, since
`awsds-org-declarative-ec2` is one of the ten imported. (viii) — zero `content` diff across all four policy
types, the RCP and the declarative policy included, which is the round-trip the question asked for. (v) —
answered **by reading**: the `for_each` keys come from `attachments.json`, which authors **names**, so an OU
created later moves no key. Only (iv) still costs a call, and it costs exactly one: the descendant data
source has to be seen returning `Sandboxes`, which sits at depth 2 — **the postconditions do not prove it**,
because every name the map requires sits at depth 1.

## Who executes what

Three identities, and confusing them produces an `AccessDenied` that reads like a policy bug (Lesson 17).

| Steps | Identity | How |
|---|---|---|
| 1, 6, 7, 8, 9, 10 | **Infrastructure user**, from the laptop | no AWS call at all — these are repository steps |
| 2, 3, 4 | **Infrastructure user** | one `awsds-infra-*` profile per account, one bootstrap each |
| **5.1** | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management**. The only Management-account action in this stage |
| 5.0, 5 (the rest) | **Infrastructure user** | `awsds-infra-identity` |

**Nothing here is performed by root**, and the infrastructure user still holds no standing assignment on
Management (1b step 4) — 5.1 is why that step matters in practice and not only in principle.

**And nothing here borrows `AWSControlTowerExecution`.** Stage 1d step 9 recorded the only sanctioned
by-hand use of that role; a Terraform apply reaching for it would make every account's state file
readable by whoever holds Management. **Every step in this stage authenticates through `AWS_PROFILE` and a
named SSO profile, and never through `eval $(aws sts assume-role …)`** — Lesson 25: an exported credential
is ambient state with no visible marker, it outlives the command that needed it, and the errors it causes
afterwards name the wrong account. With one profile per slice the profile is on the command line, where it
can be read.

## What this stage costs

**Nothing new against the ceiling, and that is a finding rather than an absence.** Both lines Stage 2 adds
are already inside `docs/plan/cost-model.md`'s floor:

- **KMS customer-managed keys, ~USD 1.00/key-month** — one per Terraform-managed account
  (`Sandbox` ×N, `Development`, `Data Governance`, `Staging`, `Production`, `Identity`), plus the key that
  encrypts `production/pki/`'s **state** under D36. `docs/PRICING.md` §2 already carries the row and already
  reads it as "one per Terraform-managed account", so **the key created in `bootstrap/` (2.4) is that key**
  — not an extra one. **The number this stage actually creates is six, not seven**: `Staging` is unvended
  (3.2), so its key arrives with the account.
- **S3 state storage and its versions**, inside the ~USD 1.00 "S3 data + state + backups" row. Versioning on
  a state bucket accumulates a version per apply; at lab scale it is noise, but 2.1 sets a lifecycle rule
  anyway because a rule added later does not reach what already accumulated.

At **~USD 6-7/month these keys are most of the KMS row — the largest line in the floor**, so it is worth stating
what it buys: the key policy is where "who can read this state" is expressed, which is the only mechanism
D36 has (Lesson 18 — the infrastructure user authors it and is not constrained by it, so what is left is the
CloudTrail record of a `kms:Decrypt`). **That record is narrower than the sentence sounds, and 2.7 measures
exactly how narrow** — it names who, when and which key, and neither what was decrypted nor which object.

## What this stage deliberately leaves outside Terraform

Step 5's argument — *a policy whose only record is a browser tab is owned by nobody* — applies word for word
to seven artefacts Stages 1b-1d also produced by hand. They stay outside anyway, and each reason is
structural rather than an oversight. **Two different reasons, and the last three rows are the second one:**
the first four *cannot* be in code (wrong account, or Control Tower's object); the last three *must not* be
(the identity seam, a hand-managed-by-decision setting, a document that must not persist).

| Artefact | Where it lives | Why it cannot come into code here |
|---|---|---|
| The org-trail metric filter + the group-membership alarm (1b step 8.3) | **Management** | Principle 1: Terraform never holds Management credentials. There is no state bucket there and there will not be one |
| The organization-level Access Analyzer (1b step 8.2) | **Audit** | Audit is not a Terraform-managed account: no bootstrap, no profile, no state. Bringing it in means a seventh state bucket and a seventh key |
| Object Lock on `aws-controltower-logs-*` (1d step 9) | **Log Archive** | Same, plus the object is Control Tower's — managing it from Terraform is landing-zone drift |
| The Control Tower **controls** — Region deny, the two root controls (1c step 7.7) | landing zone | Not policies but controls. If they are ever coded, the resource is `aws_controltower_control` (5.4) |
| The four **users** and five **groups** (1b step 2) | the Identity Center directory | They are people, not entitlements. In a real deployment they arrive over SCIM from the corporate IdP, and nothing here should have an opinion about that (`docs/plan/conventions.md`, "The identity seam") |
| **Account-level S3 Block Public Access** (1c step 7.4) | each member account | Hand-managed by decision — see 1c step 7.4. **The SCP would not stop the apply**: 1c step 7.5's deny carves out `InfrastructureAccess`, exactly the principal every slice applies as. The enforcement is step 9.1's repository grep |
| **`org-policies/canary/`** — the inverted document the battery attaches to prove a deny fires | `Policy Canary`, and only during a battery run | It is a throwaway attached and detached in one sitting (`docs/plan/conventions.md`, the naming exception). A Terraform resource for it would make a document that must not persist into one that does. **It sits inside `terraform-live/` and is the row most likely to be swept in by a `for_each` over `policies/`** — so the configuration reads `policies/*.json` and never the parent folder |

And two accounts get **no state bucket at all, on purpose**: **`Policy Canary`** (`docs/plan/architecture.md` §3:
"no Terraform slice, no state bucket" — an account whose point is to stay empty) and **Management**. Creating
one for either is the kind of thing that looks like tidiness and is not.

---

## To execute

### 1. Replace the placeholder tree

1. ~~**Delete the empty `terraform/` folder.**~~ **Obsolete — measured 2026-08-15: there is no `terraform/`
   folder on disk.** Git does not track empty directories, so it went away on its own. Kept struck through
   rather than deleted, because a reader who remembers it should find out that it is gone rather than go
   looking.
2. **Create `terraform-live/` and `terraform-modules/`** exactly as `docs/plan/conventions.md` §6 lays them out.
   That file is the authoritative layout **and it is the only copy** — if this stage needs the layout to
   change, edit §6, do not restate it here. `terraform-live/identity/org-policies/` **already exists** and
   holds 1c's documents; this step creates the rest around it.
3. **Pin `hashicorp/aws` and `required_version`, and record both in the log.** This is a step rather than a
   detail of 6.4 because **two of this stage's verifications are phrased "in the pinned provider version"**
   — (ii), whether `aws_organizations_policy` accepts `DECLARATIVE_POLICY_EC2`, and (iv), whether the
   descendant-OU data source really recurses — and a verification whose subject was never written down is a
   verification nobody can repeat. `terraform` is **v1.15.8** on this laptop (measured 2026-08-15), which is
   what `use_lockfile` needs (2.5); the provider version is chosen here.
4. **`docs/log/log-stage-02-terraform-foundation.md` already exists** (header-only, created 2026-08-15) and its row
   in [`docs/log/INDEX.md`](../../log/INDEX.md) links it. Every decision this stage names as "record which way
   it went" lands there. *(The user writes it; Claude never edits `docs/log/`.)*

### 2. The first bootstrap slice: `terraform-live/sandbox/bootstrap/`

**2.1 — What the slice contains.** One state bucket and the key that encrypts it, and nothing else:

- `aws_kms_key` + alias `alias/awsds-sandbox-tfstate` — **rotation enabled**, deletion window 30 days.
- `aws_s3_bucket` `awsds-sandbox-tfstate`, with **versioning on**, **SSE-KMS** against that key,
  **S3 Bucket Keys enabled** (`docs/plan/cost-model.md`), and `aws_s3_bucket_public_access_block` with all four
  flags true.
- A **bucket policy denying `aws:SecureTransport = false`** — checkov requires it in step 6 anyway, and a
  policy the linter adds for you is a policy nobody read.
- A **noncurrent-version lifecycle rule** (expire after ~90 days). Every apply writes a version; a rule
  added later does not reach what has already accumulated.
- `lifecycle { prevent_destroy = true }` and `force_destroy = false` — `docs/plan/conventions.md` §5.1 rule 1.
- **`default_tags` in the provider block**, carrying the five mandatory tags of `docs/plan/conventions.md`
  (`Project`, `Environment`, `ManagedBy=terraform`, `Owner`, `CostCenter`). Named here because this is the
  first slice that could have got it wrong and because **nothing will stop it**: 1c's tag SCP names
  `ec2:RunInstances` and nothing else (measured), so an untagged bucket is created happily and shows up
  later as a cost report with a hole in it. `default_tags` makes the convention a property of the provider
  rather than a line to repeat per resource — which is the Lesson 14 shape applied to tags.

**2.2 — The two-phase apply, which is the documented chicken-and-egg exception.**

1. `terraform apply` with **local state**, creating the bucket and the key.
2. Add the `backend "s3"` block (2.5) and run `terraform init -migrate-state`.
3. **Delete the local `terraform.tfstate` and `terraform.tfstate.backup` afterwards** — and note that
   step 6.2's `.gitignore` has to cover them *before* phase 1 runs, not after. A state file carries account
   IDs and resource ARNs, and this repository is hosted on GitHub.
4. **The bucket now holds its own state**, so destroying it is a two-phase operation in reverse. That is
   intended and is what `prevent_destroy` says out loud.

**2.3 — Bootstrap consumes no module, deliberately.** Step 7 creates `s3-bucket` and `kms-key`, and
`docs/plan/conventions.md` requires modules to be consumed **by git tag** — which cannot exist before the module
does. Beyond the ordering, bootstrap is the slice that makes every other slice possible; giving it a
dependency on the tree it bootstraps is how a repository acquires a cycle nobody can unwind at 23:00. Write
it as plain resources and leave it that way.

**2.4 — Which KMS key this is, since `docs/plan/conventions.md` §6 puts "KMS keys" in `foundation/`.** It is not
that key and it cannot be: `foundation/` does not exist yet at bootstrap time, and **`identity/` and
`data-governance/` have no `foundation/` slice at all**. So:

- **The state key is created in `bootstrap/` and lives there.** It is the "one per Terraform-managed account"
  key that `docs/PRICING.md` §2 and `docs/plan/cost-model.md` already count.
- `foundation/` keys — where a `foundation/` exists — are the *general-purpose* keys for that account's data
  and logs, and they are **additional**, not the same object.
- The two are separated for the D31/D36 reason, applied one level down: a key shared between state and data
  makes "who may read the state" and "who may read the data" the same question.

**2.5 — The backend block, and the one place `docs/plan/architecture.md` §4.1's no-region-literals rule cannot
apply.** A `backend` block **cannot interpolate variables** — no `var.region`, no locals. Reconcile it, do
not let step 9's grep discover it:

- Use **partial backend configuration**: keep `backend "s3" {}` in **`backend.tf`** — a file of its own
  since step 3 (3.5); it was in `providers.tf` for the sandbox slice's own apply — and put `bucket`, `key`,
  `region`, `kms_key_id` and `use_lockfile = true` in a per-slice **`backend.hcl`**, passed as
  `terraform init -backend-config=backend.hcl`.
- `backend.hcl` is not a `.tf` file, so step 9's check does not read it, and the region literal sits in one
  generated file per slice instead of in the code. **A helper in `scripts/` generates it** — written with
  step 1, because steps 2, 3 and 5 all run `init` before step 8 exists; the `Makefile` (step 8) then
  *calls* that helper rather than owning a second copy of the logic (Lesson 14 — two mechanisms for one
  file is the shape decision 5 warns about).
- **Locking is `use_lockfile = true`** (D3) — native S3 locking, no DynamoDB table. Terraform **1.15.8** is
  installed and supports it.
- `key` is `<account>/<slice>/terraform.tfstate`, one state file per slice, one bucket per account (D3).

**2.6 — The second generated file, which the step needed and did not name** *(added on execution,
2026-08-15)*. `backend.hcl` is not the only value a slice cannot write down: the **provider's `region`** may
not be a literal either (9.1 scans for it), and 3.3 forbids hardcoding `sandbox` when D35 vends one Sandbox
per business unit. So `region`, the `<env>` **name token** and the `Environment` **tag value** arrive as
variables with no defaults, from a generated, gitignored **`terraform.auto.tfvars`** —
`./scripts/gen-tfvars.py <account> <slice>`, written from `scripts/tfhygiene/backend.py`, the same table
`gen-backend-hcl.py` reads. **One vocabulary, two writers**: the region the backend records and the region
the provider uses cannot disagree, which they could the moment the second one was typed (Lesson 14). It
carries no `zone_ids` — those are per-environment and belong to a network slice's own tfvars, and a
generator emitting an unused list sends the next reader looking for the resource that consumes it.

**2.7 — What the `kms:Decrypt` record actually contains, measured rather than assumed** *(added on
execution, 2026-08-16)*. This stage leans on that record twice — in "What this stage costs" above and in
D36 — because Lesson 18 leaves nothing else: the infrastructure user authors the key policy. So the record
was read, from the trail of this slice's own applies and its lock test, and it is **narrower on two axes
than "the CloudTrail record of a `kms:Decrypt`" suggests**:

- **It never carries plaintext, and no setting makes it.** `GenerateDataKey`'s `responseElements` **is** the
  data key, and KMS logs it as `null`; `Decrypt` logs neither the ciphertext in nor the plaintext out. The
  event is *that* a decryption happened — `userIdentity`, `eventTime`, the key ARN in `resources`, and the
  `keyMaterialId`, which is what will distinguish material generations after the first rotation.
- **It does not name the object, because S3 Bucket Keys coarsen the encryption context to the bucket.**
  Measured: `"encryptionContext": {"aws:s3:arn": "arn:aws:s3:::awsds-sandbox-tfstate"}`, where without the
  bucket key it would have been the object ARN — the `<account>/<slice>/terraform.tfstate` path. **Today
  there is one object per bucket and nothing is lost. From step 4 on, every slice of an account shares that
  bucket and that key**, and the trail then answers "something in this bucket was decrypted" rather than
  "the `foundation` state was read". **S3 data events would close it and are off by default** — Stage 11
  owns them and prices them, and this is a second reason for that stage to exist, not a new item here.
- **The call is made by S3 under the caller's identity** — `invokedBy: fas.s3.amazonaws.com`, a forward
  access session — so reading a state file requires `s3:GetObject` **and** `kms:Decrypt`, and denying only
  the second is enough. That is what makes the key policy load-bearing rather than decorative.
- **D36's alarm survives the coarsening, for a reason worth writing down before 3.4 relies on it**: it is
  scoped to the *key*, which the event names in `resources`, and the PKI state key encrypts exactly one
  file — so there the key **is** the object. What 3.4 still has to measure, next to verification (i), is
  whether a bucket key applies to a per-slice `kms_key_id` override at all or only to the bucket default.
  The two questions are one read, on the same apply.

The trade is accepted as it stands: at lab scale the bucket key is a real line in `docs/plan/cost-model.md`
and the lost axis is recoverable at Stage 11. It is recorded because **a control whose record is thinner
than the sentence describing it is Lesson 5's shape** — an intention is not a control — and the thinning
here happened for a cost reason two subsections away from the claim.

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
- **"The PKI key" is two different objects and the step used to name only one.** There is the key that
  encrypts the **`production/pki/` state file** and there is whatever key the CA itself uses operationally
  later. Only the first belongs to this stage, and **it cannot be created by the `pki/` slice**: a backend
  is configured at `init`, before the slice has ever applied, so a key the slice creates does not exist when
  the backend needs it. **So `production/bootstrap/` creates two keys** — `alias/awsds-prod-tfstate` and
  `alias/awsds-prod-tfstate-pki` — and D36's `kms:Decrypt` alarm hangs on the second. This is the chicken-
  and-egg of 2.2 in a second place, and it is cheaper to see it here than at `terraform init`.
- **The S3 backend accepts `kms_key_id` per slice**, and a per-object SSE-KMS key overrides the bucket
  default. So `production/pki/backend.hcl` names the PKI state key; every other Production slice names the
  account state key. One bucket, two keys, two answerable questions.
- **This is what makes D36's alarm work at all** — an alarm on `kms:Decrypt` against the PKI key is
  meaningless if that key never encrypted anything, and it is *noise* if the key also encrypts the state
  somebody reads to change a subnet.
- **Verify while executing (i):** that the bucket's default-encryption setting and its TLS-only policy do
  not force a single key and reject the override. If they do, `pki/` gets its **own bucket**, which costs
  nothing and is the honest fallback.

**3.5 — The five slices are one slice, copied — and the copy needs an instrument** *(added on execution,
2026-08-15)*. Step 2.3 already ruled out the obvious alternative: a module is consumed **by git tag**, a tag
cannot exist before `terraform-modules/` does, and bootstrap is the slice that makes every other slice
possible — a relative-path module inside `terraform-live/` would dodge the tag rule and keep the cycle. So
the copy stands, by decision. What the step owes in exchange is an answer to the copy's own failure mode,
which is **Lesson 14 in its purest form: a bucket setting changed in four places out of five, with the fifth
still applying and nothing announcing that the copy stopped being one.**

- **`./scripts/check-bootstrap-parity.py`, in `make check` and in the commit gate** — the fifth check of a
  stage that had four. `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`, `versions.tf` and
  `.terraform.lock.hcl` must be **byte-identical** across every `terraform-live/*/bootstrap/`.
- **The two legitimate differences were pushed into files of their own so that the rule can be that blunt:**
  - **`backend.tf`** now holds the `terraform { backend "s3" {} }` block, alone. A slice that has not
    migrated yet (2.2) must not declare a backend, so this is the one file that differs — and it is
    compared **with the comment markers stripped**, so the commented and the live forms must still be the
    same three lines. It also turns the phase-2 edit into *uncomment a file* rather than surgery inside
    `providers.tf`, which is what `git status` should show.
  - **`production/bootstrap/pki-key.tf`** is the one extra file in the tree, 3.4's second key, **allow-listed
    by name**. A second entry has to be added deliberately. It carries a `precondition` on `var.env == "prod"`,
    so a copy of it into another account's slice fails the plan instead of quietly creating a key.
- **The generated files are deliberately outside the comparison** — `backend.hcl` and `terraform.auto.tfvars`
  are per-slice by construction, and `gen-backend-hcl.py`/`gen-tfvars.py` are what keep *them* honest, from
  one table (2.6).
- **`staging/bootstrap/` is optional to the check, not unknown to it.** Absent, it prints a note naming 3.2;
  the day it is written, the check starts comparing it with no edit.

**3.6 — Four applies, one per account, each the two-phase dance of 2.2.** Nothing is shared between them and
they are independent, so the order is a convenience: `development`, `data-governance`, `production`,
`identity`. Each runs as the **infrastructure user** on **that account** through **`InfrastructureAccess`**
(`awsds-infra-dev`, `awsds-infra-data`, `awsds-infra-prod`, `awsds-infra-identity`), and `AWS_PROFILE` is set
on every command rather than exported once — **Lesson 25**, a borrowed session outlives the command that
needed it and every later error names the wrong account. `./aws/tf-backends.py` is the read-back, and its
section 5 already states the expected shape: **five state buckets, six once `Staging` is vended.**

### 4. Backends for every other slice

**The previous wording of this step ("migrate every subsequent slice") described work that does not exist.**
Only `bootstrap/` migrates, because only `bootstrap/` has to run before its own backend exists. **Every other
slice declares the backend from its first `init` and never holds local state at all.** Say it that way so
nobody goes looking for a migration to perform.

### 5. `terraform-live/identity/` — where the entitlement plane acquires an owner

This is the substance of the stage, and **it is two different jobs that the previous version of this step
described as one**: the six persona permission sets are **written here, from the design in Stage 1b step 3**,
having never been typed into a console; the organization's policy set is **imported**, because prevention had
to precede it (principle 9) and 1c therefore attached it by hand. Both end in the same place — an artefact
with a diff, a review and a rollback, which is what neither has while its only record is a browser tab. That
matters most for the policy half: since D30 was reverted there is **no principal inside a governed account
that can work around a mistake in it** (D16 — the Management root is the whole recovery path).

**Written here, not imported (1b step 3.9):** `DataScientistAccess`, `DataScientistStagingAccess`,
`DataScientistProdAccess`, `DeploymentManagerAccess`, `GovernanceManagerAccess`, `DevEnvStewardAccess`, and
every group assignment except the administrator's. Nothing before Stage 5 needs any of them, so hand-typing
them into a console and then demanding that code reproduce them byte for byte (5.5) was the same work twice
with a gate in the middle that fails on JSON whitespace.

**Imported:** the `InfrastructureAccess` set and its assignments (1b step 3), and the whole
`org-policies/` set (1c step 7).

*(This consequence arrived with D30 and outlived it. D30's own reason was narrower — a carve-out condition
repeated across several policies has to be generated, not typed — and that reason went away with the
decision. The ownership hole it happened to close did not.)*

**It is two slices, not one, and the seam is not a matter of taste.** `docs/plan/conventions.md` §6 carries the
layout; the reasoning belongs here, because it is what the rest of this step is organised around:

| | `identity/sso/` | `identity/org-policies/` |
|---|---|---|
| **What it holds** | permission sets, their policies and boundaries, and **group→account assignments** | SCPs, RCPs, tag policy, declarative policy |
| **What it deliberately does not hold** | **users and groups** — directory objects, person-shaped, owned by the IdP in any real deployment (`docs/plan/conventions.md`, "The identity seam") | the Control Tower **controls** (5.4) |
| **How it gets there** | six sets **written**, the administrator set **imported** (1b step 3.9) | **imported** — 1c attached it by hand because prevention precedes it |
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

**5.0 — The reachability preflight, which runs before anything else in this stage and can delete half of
it.** *(New 2026-08-15. It exists because the landing zone put most of the policy set somewhere the
delegation may not reach.)*

INT-20 already said the plausible failure is not "the delegation is hard" but "**the delegation works and
still cannot touch a root-attached document**". What 1c then did makes that failure expensive rather than
awkward — measured from `aws/output/org-policies.txt`:

| Attached to | Documents |
|---|---|
| **the organization root** | `awsds-org-scp-baseline`, `awsds-org-scp-perimeter`, `awsds-org-scp-tag-enforcement`, `awsds-org-rcp-perimeter`, `awsds-org-tag-policy`, `awsds-org-declarative-ec2` — **six of ten** |
| **an OU** | `awsds-org-scp-ou-workloads`, `-identity`, `-interactive`, `-data` — four, one each on `Workloads`, `Identity`, `Interactive`, `Data` |

So the answer to "can a delegated administrator manage a root attachment" decides whether `org-policies/`
is the whole policy set, four per-OU documents, or nothing. **Run it as two reads and one write, in this
order, and record all three** (the reads cost nothing, and the first is informative even before 5.1 exists):

1. **Before 5.1**, from `awsds-infra-identity`: `organizations describe-resource-policy`. Expect
   `ResourcePolicyNotFoundException` — which is the *good* answer, because it distinguishes "no delegation"
   from "denied", and a run that cannot tell those apart is Lesson 13.
2. **After 5.1**, from `awsds-infra-identity`: `organizations describe-policy` on one **root-attached**
   document and one **OU-attached** one. Reading is not managing, but a read that is refused settles the
   question immediately and for free.
3. **After 5.1**, the real test, and it must be a *write* because only a write is evidence: from
   `awsds-infra-identity`, `organizations update-policy` on the **least dangerous** document with its own content — the tag policy,
   whose enforcement is off (`enforced_for` unset), so an identical rewrite changes nothing even if it lands
   in a way nobody expected. Not `awsds-org-scp-baseline`; not from the canary, which has no delegation.
   **"Its own content" needs a mechanism, the same way 5.5's import does** *(added 2026-08-15)*: read the
   document back with `describe-policy --query 'Policy.Content' --output text` into a file, and feed **that
   file** to `update-policy --content file://…`. Retyping it is a different test — a document differing by a
   byte measures the delegation *and* edits the policy, and the two are no longer separable in the result.
   `update-policy` leaves `Name` and `Description` unchanged when neither is passed, so `--content` alone is
   the whole call.

**What each outcome costs, decided here rather than at the keyboard:** all three succeed → `org-policies/`
is written as designed. Root refused, OU allowed → the slice holds **four** documents, the six on the root
stay console-managed and 9.2's check keeps them in scope by reading `policies/*.json` regardless of who
manages them. All refused → 5.6's fallback, unchanged. **One reading discipline before declaring either
refusal:** a denied write is evidence about *root reach* only if the delegation's `Resource` list carries
the **policy-type ARNs** (5.1) — a list of targets alone denies every write, on every document, and reads
exactly like "all refused". `DEL-9` is the check.

**Answered 2026-08-15 — all three readings ran, all three succeeded, and `org-policies/` is written as
designed with all ten documents.** The write landed on `awsds-org-tag-policy`, a **root-attached** document,
from `awsds-infra-identity`. INT-20's predicted failure did not occur.

**But it settled less than "a root attachment is manageable", and the gap is a Lesson 20 gap.**
`UpdatePolicy` authorizes against the **policy** ARN alone; only `AttachPolicy`/`DetachPolicy` authorize
against the **target** as well. So the successful write proves the `policy/o-<org>/<type>/*` half of the
`Resource` list and proves the condition does not block — it says **nothing** about the `root/…` and `ou/…`
entries, which are still supported only by *reading* them (`DEL-6`, `DEL-7`). And the stage will not exercise
them either: 5.5 **imports** attachments that already exist, so a matching configuration plans clean and
calls no `AttachPolicy` at all. The delegation's target half therefore stays attached-but-unexercised past
the end of this stage, and the first call that needs it — Stage 3 attaching a new document, or any
re-attachment — is where a denial would surface, far from anything that would explain it.

4. **Closing the target half, non-mutating and worth the two minutes** *(added 2026-08-15)*: from
   `awsds-infra-identity`, `organizations attach-policy` for a pair that is **already attached** — the tag
   policy on the root, read out of `aws/output/org-delegation.txt` §5 immediately before, never from memory.
   The two outcomes are distinguishable and neither changes anything: `DuplicatePolicyAttachmentException`
   means authorization **passed** and the service then refused the duplicate; `AccessDenied` means the target
   half is not reachable, and `org-policies/` must then own documents without owning their attachments. The
   idiom is `aws/probes/`'s own — a call aimed at something that cannot take effect — and it carries that
   folder's rule with it: **it is a deliberate act, and the pair must be verified as attached first**, because
   the same call against an unattached pair is a real attachment.

   **Ran 2026-08-15: `DuplicatePolicyAttachmentException`.** The `root/…/r-zhj6` entry is exercised, not
   merely read — `AttachPolicy` authorizes against target **and** policy, so both matched. The `ou/…/*`
   wildcard was closed the same way, against an already-attached per-OU pair: same exception, so the
   wildcard matches a real call.

   **And this reading needs a negative control, which is Lesson 21 arriving from the other side.** It is
   only evidence if IAM authorization runs *before* the service's duplicate check; if the order were
   reversed, an unauthorized principal would get `DuplicatePolicyAttachmentException` too and the reading
   would be worth nothing. The discriminator costs one command and cannot mutate anything either: **the same
   call from `awsds-policy-canary`**, a principal with no delegation at all. `AccessDenied` there proves the
   ordering and retroactively makes the Identity result proof; `DuplicatePolicyAttachmentException` there
   voids it. **A probe with no negative control is a check that returns the same answer on success and
   failure** (Lesson 13). **It returned `AccessDeniedException`** — so the ordering holds and both duplicate
   readings above are evidence rather than coincidence.

   **One entry stays a reading, and by construction rather than by omission: `account/o-<org>/*`.** This
   design attaches nothing to an account — the census is 6 root + 4 OU, zero account-level — so there is no
   already-attached pair to aim an inert call at, and the only call that would exercise it is one that
   really attaches. It is an unexercised **over-grant**, not a gap: nothing in Stages 2-3 needs it, and if
   it is ever removed the delegation gets narrower rather than broken.

**5.1 — The precondition no stage creates yet, and `org-policies/` does not run without it.**

Permission sets reach the Identity account through the **Identity Center** delegated administrator
(1b step 1, `sso.amazonaws.com`). **SCPs, RCPs, tag policies and declarative policies do not** — they are
AWS Organizations objects, and by default only the Management account can touch them. Nothing in Stage 1a or
1b delegates that. So:

- **What it is:** a **resource-based delegation policy** on the organization
  (`organizations:PutResourcePolicy`), naming the Identity account as principal. It is not
  `register-delegated-administrator`; that is a different mechanism and it does not cover policy management.
- **Who runs it, and by which path:** `AWS Control Tower Admin` / `AWSAdministratorAccess`, from Management
  (D34) — the only Management action in this stage. In the console: **Settings** → the **Delegated
  administrator for AWS Organizations** section → **Delegate** → the JSON editor → **Create policy**. The CLI
  equivalent is `aws organizations put-resource-policy --content file://<document>.json`; either path needs
  `organizations:PutResourcePolicy` **and** `organizations:DescribeResourcePolicy`. AWS additionally requires
  the delegated account's principals to hold the matching **identity-based** permissions — the resource half
  alone grants nothing — which is satisfied because `InfrastructureAccess` carries `AdministratorAccess` and
  the `Identity` OU's `CT.MULTISERVICE.PV.1` keeps `organizations:*` wholly inside its `NotAction`
  (verification (vii), answered by reading). Record the exact document in
  `docs/log/log-stage-02-terraform-foundation.md`; its `Sid`s are indexed in
  [`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md), in the one section
  `check-index.py` cannot see.
- **What it must grant**, per AWS's own examples: the read half (`DescribeOrganization`,
  `ListRoots`, `ListOrganizationalUnitsForParent`, `ListChildren`, `ListParents`, `ListAccounts`,
  `ListPolicies`, `ListPoliciesForTarget`, `ListTargetsForPolicy`, `ListTagsForResource`) **plus**
  `CreatePolicy` / `UpdatePolicy` / `DeletePolicy` / `AttachPolicy` / `DetachPolicy`, each scoped by a
  `organizations:PolicyType` condition to the four types this project writes.
  **Four reads this list omitted, added after reading the examples rather than paraphrasing them**
  *(corrected 2026-08-15)*: `DescribeOrganizationalUnit`, `DescribeAccount`, `DescribeEffectivePolicy` and
  `ListAccountsForParent` appear in **every** AWS example, and — the load-bearing one —
  **`DescribePolicy`**, which is what the provider calls on every refresh of an
  `aws_organizations_policy`: without it 5.5's import succeeds and the next `plan` fails. Add
  **`DescribeResourcePolicy`** as well, for the instrument rather than for Terraform: it answers from the
  Identity account *today* with no delegation at all (that is how 5.0's reading 1 ran), and if creating the
  policy were to change that, `org-delegation.py` would report `DEL-1` as *denied* and every check below it
  would go vacuous — the instrument blinding itself at the moment it starts being useful.
- **The condition operator is `StringLikeIfExists`, not `StringEquals`** *(corrected 2026-08-15; every AWS
  example uses it and the earlier wording named no operator at all)*. The difference is the failure this
  whole step is built to avoid: with a bare `StringEquals`, any call that does **not** carry
  `organizations:PolicyType` in its request context fails the condition and is **denied** — which arrives at
  the keyboard as *"every write refused"*, indistinguishable from 5.0's "the delegation cannot reach a root
  attachment", the one outcome 5.0 exists to measure. `IfExists` makes the condition act only when the key
  is present, and confinement to the four types is still carried by the policy ARN path in `Resource`.
  ~~**`DEL-8` cannot catch this**~~ — **it can, since 2026-08-15.** The check used to iterate the operator
  and discard it, so a `StringEquals` document passed and failed every apply; it now reports the operator
  and **fails** on any form without an `IfExists` suffix. Demonstrated against the live document with the
  operator name as the only edit.
- **Tagging is a third statement, unconditioned and policy-scoped** *(added 2026-08-15)*.
  `organizations:TagResource` / `UntagResource` do **not** accept the `organizations:PolicyType` condition —
  AWS's tagging example puts them in a separate statement with no condition for exactly that reason — so
  folding them into the write statement grants nothing. The ten attached documents carry **no tags today**
  (measured), so nothing needs this yet; it is here because `default_tags` in the provider block will try to
  tag an `aws_organizations_policy` at 5.5, *after* 5.0 has already declared the delegation good, and the
  denial would land on the import rather than on the delegation. Scope the `Resource` list to the four
  **policy** ARN classes only — not to accounts, OUs or the root, which would hand the Identity account
  re-tagging of the organization's structure for no benefit here.
- **The `Resource` list is four ARN classes — targets *and* policies — and the earlier wording named only
  the targets** *(corrected 2026-08-15)*. The targets: `arn:aws:organizations::<mgmt>:ou/o-<org>/*` (the
  wildcard OU form), the `root/o-<org>/r-<root>` ARN and the account wildcard. AWS documents that naming a
  **single** OU *"excludes child OUs and accounts under child OUs"*, and this organization is **two levels
  deep** (D23: `Sandboxes` under `Interactive`). The same nesting that breaks a single-level `for_each` in
  5.3 breaks a single-OU delegation here, and it breaks it the same silent way. **And the policies**:
  `arn:aws:organizations::<mgmt>:policy/o-<org>/service_control_policy/*` plus its
  `resource_control_policy`, `tag_policy` and `declarative_policy_ec2` siblings — AWS's own examples carry
  them, because `CreatePolicy`/`UpdatePolicy`/`DeletePolicy` authorize against the **policy** ARN and
  `AttachPolicy`/`DetachPolicy` against target *and* policy. A delegation without the policy class denies
  **every** write on **every** document — indistinguishable at the keyboard from 5.0's "all refused", which
  is the outcome 5.0 exists to detect. `org-delegation.py`'s **`DEL-9`** reads the delegation document for
  exactly this: no policy-type ARN class in the `Resource` list is a **fail**, not a note.
- **Exclude `DisablePolicyType` and `EnablePolicyType`.** They act on the root and turning a policy type off
  detaches every policy of that type at once. Nothing in this design needs them after 1c step 7.2.
- **Two AWS-side constraints on the *shape* of this document, neither of which is a choice**
  *(found 2026-08-15, on the procedure page)*. **`NotAction` and `NotResource` are rejected outright since
  2026-06-30** — AWS calls them incompatible with the delegation allowlist model — so the exemption-shaped
  idiom used throughout `policies/` is unavailable here even in principle, and a document written that way
  fails at creation rather than at use. And **the delegable actions are a published closed list**: an action
  absent from it cannot be delegated however the document is written, which is the first thing to check if a
  later stage wants to widen this grant.

**The blast radius this creates, stated rather than discovered.** AWS's own note is that the delegation
*"allows delegated administrators to perform the specified actions on policies created by any account in the
organization, including the management account"* — which includes **Control Tower's own guardrail SCPs**.
Scoping by policy ARN would fix it, and cannot: this project's policies have no ARNs until they are created.
So this is the **second** widening of the Identity account's blast radius, after the group-membership path
1b step 1 records — and its control is the same one: 1b step 8.3's alarm, plus the CloudTrail record. Write
it into `docs/ORGANIZATION.md`'s description of that account rather than leaving it here.

**5.1a — Narrowing the delegation to one role.** *(New 2026-08-15, from
[open question 11](../open-questions.md). The second Management action of this stage, and the only one 5.1
did not anticipate.)*

5.1's `Principal` is `arn:aws:iam::<Identity>:root` — the **account**, because a resource policy's
principal *is* an account and there is no narrower one to write. Measured the same day: that reaches
**every** principal in Identity that also holds `organizations:*` on the identity side, and Control Tower
put a second one there that nobody chose — `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins`,
assigned into every vended account, this one included. The A/B that proves it: the duplicate `AttachPolicy`
returns `DuplicatePolicyAttachmentException` from **Identity** as `AWS Control Tower Admin`, and
`AccessDenied` from **Development** as the same user with the same permission set.

**Why this rather than removing that assignment.** The Control Tower admin holds `AWSAdministratorAccess`
on **Management**, where Organizations is native — the Identity path grants it nothing new. Removing the
assignment closes an instance the same human walks around, and buys a standing check because Control Tower
re-creates landing-zone assignments. **The account-wide principal is the durable half**: it will reach the
six persona sets of 5.2 and any pipeline role Stage 8 puts in this account, none of which exists yet.

**What to add**, to `DelegatePolicyLifecycleToIdentity` and `DelegatePolicyTaggingToIdentity` — and *not*
to the navigation statement, which grants nothing the account does not already have as a delegated
administrator of another service:

```json
"ArnLike": {
  "aws:PrincipalArn": "arn:aws:iam::*:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*"
}
```

The wildcard account and the trailing `*` are **decision 7's, for decision 7's reason**: the SSO role
suffix is minted per account — observed 2026-08-15 as `3e25cf051c1ea198` in Identity against
`ae101c6e565bd25b` in Development — so an exact ARN breaks the first time Identity Center re-provisions
the role.

**Three costs, stated before the keyboard rather than after:**

1. **It is a second place a principal is enumerated** (Lesson 14). Anything else that must ever write an
   organization policy — a Stage 8 pipeline role is the candidate — has to be added here, and forgetting
   surfaces as an `AccessDenied` on an apply, far from this file.
2. **`org-delegation.py` needs a `DEL-10`**, or nothing checks the condition and it becomes an intention
   rather than a control (Lesson 5). It reads the two write statements and fails if either lacks it.
   **Written 2026-08-15, before the paste, and demonstrated on both forms**: red against the live document
   (the true state until 5.1a lands — the wording says so), green against the amended one, operator named.
   The amended document itself is generated, not typed: the live document read back through
   `describe-resource-policy` into untracked `aws/output/delegation-live.json` (which is also the rollback
   copy), the two `ArnLike` blocks added programmatically, the result in `aws/output/delegation-5.1a.json`
   — and a diff asserting **nothing else changed**, which is 5.0's "its own content" discipline applied to
   an edit instead of a rewrite.
3. **If the condition is wrong, every write against `org-policies/` stops** — and the repair is the
   Management console, which is D16's design rather than a surprise.

~~**Unverified, and cheap to find out: whether this document accepts a `Condition` on `aws:PrincipalArn` at
all.**~~ **Answered 2026-08-16: it does.** It already rejects `NotAction`/`NotResource` (5.1), so a refusal
was a live possibility — and a safe one, since `put-resource-policy` would have errored and left the
existing document standing. It did not: the amended document was accepted on the first paste. **The two
rejections are therefore not one rule with two instances** — the allowlist model refuses
`NotAction`/`NotResource` because they are exemption-shaped, and a `Condition` narrowing an allow is not.

**Verification (ix), which reuses open question 11's harness and is the whole of it.** Both halves, because
either alone proves nothing:

- (a) the duplicate `AttachPolicy` from **`awsds-ctadmin-orgfull-identity`** must turn from
  `DuplicatePolicyAttachmentException` into `AccessDenied`; and
- (b) the same call from **`awsds-infra-identity`** must still return
  `DuplicatePolicyAttachmentException`.

(a) without (b) is indistinguishable from having broken the delegation outright — which is the failure this
step is most likely to cause and the one that would read as success.

**Who runs it:** `AWS Control Tower Admin` / `AWSAdministratorAccess` on **Management**, the same path as
5.1.

**Ran 2026-08-16, and both halves came back as designed — 5.1a is CLOSED.** The paste was accepted;
`./aws/org-delegation.py` flipped `DEL-10` from red to `pass`, which is the instrument reporting the change
it was written before. Then:

| From | Expected | Got |
|---|---|---|
| (a) `awsds-ctadmin-orgfull-identity` | `AccessDenied`, where `DuplicatePolicyAttachmentException` came before | **`AccessDeniedException`** |
| (b) `awsds-infra-identity` | still `DuplicatePolicyAttachmentException` | **`DuplicatePolicyAttachmentException`** |

Both calls are writes that cannot take effect — the pair was verified attached first, `aws/probes/`'s own
idiom — and the reading is the **wording** of the error, never the exit code. **The three costs above stand
unchanged**: cost 1 (a second place a principal is enumerated) is now live, and the candidate that will hit
it is a Stage 8 pipeline role.

**5.2 — What is written, what is imported, and — the half that is easiest to get wrong — what is neither.**

| Object | How it gets into state | Left alone |
|---|---|---|
| The **six persona permission sets** and their policies (design of record: 1b step 3.1-3.7) | **Written** — `aws_ssoadmin_permission_set` + `aws_ssoadmin_permission_set_inline_policy`, applied here for the first time | — |
| Their **group→account assignments** (`aws_ssoadmin_account_assignment`) | **Written**, enumerated one by one (5.3), with the principal resolved by **display name** through `data.aws_identitystore_group` | — |
| The **`InfrastructureAccess`** set (1b step 3) and its assignments | **Imported** — it is the credential this apply runs as, so it cannot be created by the apply | **`AWSAdministratorAccess` and every other Control Tower set** — editing them is landing-zone drift (D10, consequence iii). The Account Factory direct assignments of that set are not modelled either (row below) |
| This project's **five groups** and its **four users** (1b step 2) | **Neither.** They stay directory objects, outside every state file | **Control Tower's groups** — `AWSControlTowerAdmins`, `AWSAccountFactory`, the auditor and per-account groups |
| The **direct Account Factory assignments** (D32, 1b step 3.8/5.1) | **Neither** — and if 1b's verification (vi) found they are re-created, they are a permanent property of a vended account rather than something to model | — |
| The **org-root SCP set** (1c step 7.5), the **per-OU sets** (7.6), the **RCPs**, the **tag policy** and the **declarative EC2 policy** (7.8) | **Imported** | The **Control Tower controls** (7.7) — see 5.4 |

- **Why the four users and five groups stay out, since everything else identity-shaped is coming in.** It is
  the seam in `docs/plan/conventions.md`, "The identity seam": a permission set and an assignment are
  *entitlements*, and their number is fixed by the design; a user and a group membership are *people*, and
  their number grows with headcount — hundreds of data scientists, a dozen stewards. Putting people in
  Terraform makes the repository an HR system, puts personal data in a state file, and turns joiners and
  leavers into merge requests. In a real deployment they arrive over SCIM from the corporate IdP, and this
  slice is unchanged by that — **which is exactly why an assignment must resolve its group by display name
  and never by GUID**: a replaced directory re-creates the groups with new IDs.
- **The permissions boundary is the one thing here that cannot be finished inside this slice** (1b step
  3.4). A customer-managed boundary referenced from a permission set must exist as an `aws_iam_policy` with
  the same name and path **in every account the set is provisioned into**, and those accounts' policies
  belong to their own `foundation/` slices — different state, different profile, one more copy per business
  unit (D35). **Decide it here** (decision 4 below): boundary created by each account's `foundation/` and
  attached afterwards through `aws_ssoadmin_permissions_boundary_attachment`, an AWS-managed policy as the
  boundary, or the sets stay inline-only until Stage 3 exists. Attaching a customer-managed reference before
  the policy exists in the target account fails the *provisioning*, in that account only — which is the
  quiet version of this mistake.
  **Decided 2026-08-16 — inline-only, and the two denies below do not wait with it.** The reasoning is in
  decision 4; what it means for this slice is that no `aws_ssoadmin_permissions_boundary_attachment` is
  written here yet, and that the file which will carry it says so by name rather than by absence.
- **Every boundary written here must deny two things that have nothing to do with this account's
  resources, because 1c's SCPs are only as strong as control over the principals they exempt.** Two
  carve-outs exist in the attached ceiling and both name a principal:
  `DenyAccountBpaChangeExceptInfrastructure` matches the ARN *pattern*
  `…:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*` (decision 7, the one
  wildcard-account ARN), and `DenyCatalogMaintenanceRunsExceptMaintenanceRole` names one exact role in Data
  Governance (D27). So:
  - **`iam:CreateRole` under the `/aws-reserved/` path** would mint a principal matching the first pattern.
    Whether IAM permits that path at all is **unverified** — one `create-role` in `Policy Canary` answers
    it, and it is worth running before the boundaries are written rather than after.
  - **`iam:UpdateAssumeRolePolicy` on an exempted role** hands its exemption to whoever can edit the trust
    policy, without them ever having to *be* that principal. This one needs no verification: it is how IAM
    works.
  Neither is exploitable today — `iam:CreateRole` lives with `InfrastructureAccess`, which is already the
  exempted identity, and the maintenance role does not exist yet. **Both become exploitable the moment this
  step creates a set that is neither**, which is why the requirement is recorded against the boundaries and
  not against the SCPs: a carve-out cannot defend itself. **And the two denies are written once, not N
  times** (Lesson 14): one shared fragment — a `locals`/`jsonencode` block, or step 7's `iam-role` module
  boundary input once it exists — referenced by every boundary, never retyped per set.
- **There is a size cap on a permission set's inline policy**, and three of these sets are long enumerated
  denies (1b step 3.5). Count before writing, the same discipline 1c step 7.1 applies to SCPs; the way out
  is a customer-managed policy, which lands back on the paragraph above.
- **The declarative policy was missing from every earlier version of this step.** 1c step 7.8 creates one
  (IMDSv2 and EC2 public-access defaults) and it is an Organizations policy like the others.
  **Verify while executing (ii):** that `aws_organizations_policy` accepts `type =
  "DECLARATIVE_POLICY_EC2"` in the pinned provider version. If it does not, that one policy stays console
  managed and is recorded as such (Lesson 5 — an unowned artefact is worse when nobody wrote down that it is
  unowned).
- **Read the three landing-zone logs before writing anything** —
  `docs/log/log-stage-01b-identity-and-controls.md`, `docs/log/log-stage-01c-preventive-policies.md` and
  `docs/log/log-stage-01d-org-wide-enablement.md`. Three of their execute-time decisions change what exists here:
  whether the `Interactive` OU got a policy set at all (1c step 7.6), what this project's administrator
  permission set is actually called (1b step 3.2), and whether the Account Factory direct assignments could
  be removed (1b step 5.1).
- **One thing that must never be declared in any slice, because it looks like it belongs in one:**
  `aws_s3_account_public_access_block`. The setting is hand-managed by decision (1c step 7.4) — and the SCP
  is **not** what stops the apply: 1c step 7.5's deny carves out `InfrastructureAccess`, exactly the
  principal every slice applies as, so an apply that touches it would *succeed*. The enforcement is step
  9.1's repository grep, which is why that grep exists.

**5.3 — Write it so an OU or account created later is covered without anybody remembering (D34).**

Accounts and OUs are vended from the console, permanently and by design, and **that cannot make this state
inconsistent** — nothing here declares `aws_organizations_account` or
`aws_organizations_organizational_unit`, and a state file tracks only what a configuration declares. The risk
is the opposite of drift and it is silent: a new OU with no attachment, or a new account outside every
enumerated ARN condition, with `terraform plan` reporting **"No changes"** in both cases.

**The rule: the floor is discovered, the grants are enumerated — and the slice split runs along that same
seam**, which is the fourth reason to have made it. **But 1c's execution changed what "discovered" can mean
on the policy side, and the previous wording of this step would now produce a wrong apply.** Read point 1
and its second half together:

1. **The floor is discovered — and it turns out to be *inherited*, not attached per node.** Everything that
   must cover everything went onto the **organization root** (5.0's table: six of ten documents). A new OU
   or a new account inherits all six the moment it exists, with no attachment to create and no `for_each` to
   run. So the coverage guarantee is real and it is bought by the *attachment point*, not by discovery.
   **And the per-OU documents cannot be discovered — writing them as if they could is the failure this
   step exists to prevent.** The four are **different documents**, one per OU, and **three OUs carry none**
   — `Policy Test`, `Security`, and `Sandboxes` **by decision** (D37). A `for_each` over the discovered OUs
   attaching "the OU document" therefore does two wrong things at once: it has nothing to attach for three
   of the seven, and for `Sandboxes` it would attach something and **silently reverse D37** — an apply that
   undoes a decision is worse than one that fails. **So the OU→document map is authored**, in the same sense
   `docs/plan/conventions.md` admits for the business-unit map: a document reaches an OU because somebody wrote
   the pair down. **Written down since 2026-08-15 in
   [`terraform-live/identity/org-policies/attachments.json`](../../../terraform-live/identity/org-policies/attachments.json)**
   (step 9) — the root's six, the four OU pairs, and the three OUs that carry none with the reason each is
   empty, by **name**. This slice's `for_each` reads that file rather than restating it, so the map the
   check guards is the map the apply uses. What the Organizations data sources buy here is **step 9.3's
   check** — an OU in no map is a red `make check-ou`, not a silent attachment — which moves this whole risk
   out of an `apply` and into a script, where it is cheap.
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
   both levels explicitly. **What it is for changed with point 1 above**: it feeds the *check*, not the
   attachments, so a wrong answer here now costs a check that under-reports rather than an apply that
   attaches in the wrong place. That is a real reduction in the stakes of verification (iv), and it is worth
   knowing before spending an evening on it.
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

**5.5 — The check that an import is faithful: after the import, `terraform plan` must come back empty.** Not
"small", empty. An import that plans a change is either a policy that differs from what is attached, or a
resource whose attributes Terraform normalises differently — and the first of those is a control that does
not say what you think it says.

**Read it against 5.2's first column, because the gate now applies to one half of the stage and not the
other.** The six written permission sets plan a *creation* on their first apply — that is the point of them,
and an empty plan there would mean nothing was written. The gate is for the imported objects: the
administrator set and its assignments in `sso/`, and everything in `org-policies/`.

**The cheap way to make the policy import land empty, which costs 1c nothing.** The usual failure is
cosmetic — the JSON typed into the console and the JSON rendered from the configuration differ in
whitespace or key order, and the plan shows a rewrite of a policy nobody changed. So **1c wrote each
document as a tracked template in `terraform-live/identity/org-policies/policies/*.json` first and pasted
the rendered copies into the console** (`render.py` → untracked `aws/output/rendered-policies/`; the policy
ids landed in the 1c log, and come from `import-ids.py` now). The import then compares the same template,
substituted the same way. **The groundwork is in place** — but "the same way" needs one more step than the
sentence implies, and that step is below.

**5.5a — The three mechanical facts this step used to leave to the keyboard.** *(Added 2026-08-15; each one
is a place an import silently produces a diff.)*

**(i) The tracked documents are templates, and `templatefile()` cannot read them.** Eight placeholders
across four files, measured 2026-08-15: `<ORG_ID>` ×6 (`awsds-org-rcp-perimeter.json` ×4,
`awsds-org-scp-perimeter.json` ×2); `<ORG_PATH_DATA>` ×1 in **`awsds-org-scp-baseline.json`** — the
`DenyDataZoneDomainOutsideDataOu` condition, so the org-path substitution belongs to the **root-attached
baseline**, and in 5.0's "root refused, OU allowed" outcome it stays with the console-managed half;
`<ACCOUNT_ID_DATA>` ×1 in `awsds-org-scp-ou-data.json`. *(An earlier version of this step counted
`<ORG_ID>` ×8 and put `<ORG_PATH_DATA>` in the `Data` document — a substitution wired from that map would
have left the baseline's placeholder literal, a deny that never fires.)* The placeholders are
angle-bracketed on purpose — `render.py` explains why,
and it explicitly anticipated this stage — but they are **not** `${…}`, so Terraform's `templatefile()` does
not substitute them. The configuration therefore reads the same tracked file and substitutes explicitly:

```
jsonencode(jsondecode(replace(file("policies/awsds-org-scp-perimeter.json"), "<ORG_ID>", data.aws_organizations_organization.this.id)))
```

The `jsonencode(jsondecode(…))` wrapper is not decoration: it **normalises both sides the same way**, which
is what turns "the same document" from a claim about whitespace into a claim about content. The alternative
— converting the placeholders to `${…}` — is admissible but costs a matching edit to `render.py` in the same
commit, and `render.py` is what produced the bytes that are attached right now.

**(ii) `<ACCOUNT_ID_DATA>` must not become a literal, and that is not a style rule here.** No account id
enters a tracked file (`aws/INDEX.md` rule 1). It also must not be resolved *by account name* — 1d step 9
recorded why (`Log Archive` returns `None`; the account is `Log Archive Account`). **Derive it from the
`Data` OU**, which holds exactly one account, through the same data-source walk 5.3 already performs. That
is discovery in the safe direction: the id follows from the OU the document is about. `<ORG_PATH_DATA>`
rides the same walk plus two values already in hand: it renders as `<org-id>/<root-id>/<Data-OU-id>/`
(exactly what `render.py` computes), so the **baseline** document's substitution needs the root id and the
`Data` OU id as well as the org id.

**(iii) The import ids, and the one that goes wrong.** Four resource types, four formats, and the last two
carry commas rather than colons:

| Resource | Import id |
|---|---|
| `aws_organizations_policy` | the policy id — `p-…` |
| `aws_organizations_policy_attachment` | `<target_id>:<policy_id>` — **and every attachment is a separate import**, which the step's "the whole `org-policies/` set" glosses over |
| `aws_ssoadmin_permission_set` | `<permission_set_arn>,<instance_arn>` |
| `aws_ssoadmin_account_assignment` | `<principal_id>,<principal_type>,<target_id>,<target_type>,<permission_set_arn>,<instance_arn>` |

Two more formats ride along with the `InfrastructureAccess` import and are easy to miss:
`aws_ssoadmin_managed_policy_attachment` (`<managed_policy_arn>,<ps_arn>,<instance_arn>`) and, if the set
carries one, `aws_ssoadmin_permission_set_inline_policy` (`<ps_arn>,<instance_arn>`). The table above lists
the four principal formats, not the whole manifest — that is `import-ids.py` §5.

**The one that goes wrong is an import into a `for_each` resource**: the address is
`aws_organizations_policy_attachment.this["<key>"]` and **the key has to be exactly what the configuration
computes**, not what reads naturally. Import one, run `plan`, and only then import the rest — a wrong key
does not error, it plans a create alongside an orphan.

**None of these ids should be typed by hand** — `./aws/import-ids.py` emits every one (see "The instruments
this stage runs on"). Until the 2026-08-15 fix to `org-policies.py`, three of the ten policy ids existed
only in `docs/log/log-stage-01c-preventive-policies.md`; a fresh snapshot now carries all ten.

If the groundwork above was somehow not done, expect an iteration or two here and **do not "converge" by
applying** — read the diff first (see the Risks).

**Do `sso/` first and `org-policies/` second**, and not for convenience: `sso/` exercises the import
mechanism against objects whose worst failure is somebody being unable to sign in, so any misunderstanding
about how a faithful import behaves surfaces where it is cheap. `org-policies/` is the same mechanism
against the set that can lock the organization out of itself.

**5.6 — The fallback, if 5.1 turns out to be incompatible with the Control Tower landing zone.** Same family
of question as the Identity Center delegation in 1b step 1, and the split above is what makes the answer
cheap:

- **`identity/sso/` lands anyway.** It depends only on the Identity Center delegation, which 1b already
  proved, so a failure in 5.1 costs this stage half its scope rather than all of it — and costs no state
  move, because the boundary was drawn before the attempt rather than after it.
- **`identity/org-policies/` stays empty and the four policy types stay console-managed**, exactly as 1c left
  them. Step 9.2's wildcard check degrades from a script to a manual review — strictly worse, and
  **recorded as such in `docs/log/log-stage-02-terraform-foundation.md`**, not absorbed (Lesson 5: an unowned artefact
  is worse when nobody wrote down that it is unowned).
- **Keep the empty slice, with a `README.md` naming INT-20 as the blocker.** An empty folder that says why is
  the only thing that will make somebody retry this; a deleted folder is a plan that quietly gave up.

### 6. Repository hygiene

**6.1 — Install the tooling first, because none of it is present.** **Re-measured on this laptop
2026-08-15 and the sentence still holds exactly:** `terraform` is **v1.15.8** (`darwin_arm64`), `aws` and
`uv` are present; **`tflint`, `checkov` and `pre-commit` are all absent.** Install them, pin the versions,
and add them to `CLAUDE.md`'s "Tools installed in the current environment" list — a gate that depends on a
tool nobody recorded installing is a gate the next machine does not have.

**Done 2026-08-15, and the machine split the three tools into two classes the step had not
distinguished.** `pre-commit` **4.6.2** and `checkov` **3.3.11** are Python and went in with
`uv tool install`, one command each. **`tflint` is a Go binary, and this laptop has no `brew`, no `go`, no
`npm` and no `docker`** — every packaged route is absent, so it is a signed release download plus a
checksum check, performed deliberately. **The user installed it the same day: `tflint` v0.64.0, in
`~/local/bin`.** All three are now in `CLAUDE.md`'s tool list, and the tool list is the deliverable here —
a gate that depends on a tool nobody recorded installing is a gate the next machine does not have.

**One thing the install leaves behind, and it is not the binary.** `tflint`'s rulesets are **plugins,
downloaded on demand**, so a fresh clone with `tflint` on its `PATH` still fails until `tflint --init` has
been run against `.tflint.hcl`. That is a second setup step with no announcement of its own — it belongs in
the same sentence as the install, and it is why `.tflint.hcl` carries it as a comment at the top of the
file rather than leaving it to be rediscovered from an error message.

**6.2 — `.gitignore`, and it has to be right before step 2 runs.**

- **Ignore:** `.terraform/`, **`*.tfstate`**, `*.tfstate.*` (which covers `.backup` and the local lock file
  `.terraform.tfstate.lock.info` — the previously listed `.terraform.lock.info` is a name Terraform never
  writes), `crash.log`, `*.tfvars` that carry account IDs, and `backend.hcl` — unconditionally, whichever
  mechanism generates it (2.5).
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

**Run it once and copy the result, rather than once per slice** *(added 2026-08-15)*. The lock file is a
function of the version constraint and the platform list, nothing else — and `versions.tf` is identical in
every slice by construction — so the five files are identical, and generating them separately downloads the
provider three times per slice for no additional information. `md5` across the five is the check that the
copy was faithful. **Also export `TF_PLUGIN_CACHE_DIR` before any of this**: `terraform_validate` in the
pre-commit hook runs `init` per slice, and without a shared cache each one fetches its own ~250 MB copy.

**6.4 — `pre-commit` with `terraform fmt`, `terraform validate` and `tflint`.**

**6.5 — `checkov` as a required gate, not an optional one** — a policy check that can be skipped is a policy
check that will be skipped on the day it would have mattered. Any suppression is an inline
`# checkov:skip=CKV_...` with a reason on the same line, never a global exclusion.

**Expect the first run against `bootstrap/` to fail, and decide the suppressions rather than discover
them.** A state bucket trips the checks for **server access logging** and **cross-region replication** by
construction, and neither is an oversight: a log destination for the state bucket is a second bucket in the
same account holding the same secrets, and replication is a Stage 12 item (`docs/plan/cost-model.md` has no line
for it). **Record which suppressions were taken and why in the log at the first run** — the point of an
inline skip with a reason is that the reason was thought about once, and a stage that lets them accumulate
silently has a gate in name only (Lesson 5).

**Measured 2026-08-15 against `sandbox/bootstrap/`: 30 passed, 3 failed, and the three are the two
predicted plus one.** `CKV_AWS_18` (access logging) and `CKV_AWS_144` (replication) arrived as written, and
**`CKV2_AWS_62`** — S3 event notifications — came with them: there is no queue, no topic and no function in
the account to notify, and "who is told when state changes" is a Stage 12 question. All three are inline
skips with a reason. **The mechanical detail that cost the first run:** checkov reads a
`# checkov:skip=<ID>:<reason>` only **inside** the resource block; above it the line is an ordinary comment
and the check fails anyway, with nothing saying the suppression was ignored.

### 7. The first reusable modules — **moved to Stage 3 on 2026-08-16**

`terraform-modules/`: **`s3-bucket`, `iam-role`, `kms-key`** — **no longer built here.** They are written in
[Stage 3](stage-03-networking.md) step 1.1, in the same sitting as `vpc/`, and the requirements below travel
with them unchanged:

- **`s3-bucket`** enables **S3 Bucket Keys** by default (`docs/plan/cost-model.md`) and blocks public access
  unconditionally. The account-level block from 1c step 7.4 is the blanket; this is the module-level half,
  and neither replaces the other.
- **`iam-role`** takes a **permissions boundary as a required argument**, so omitting one has to be
  deliberate (`docs/plan/conventions.md`, IAM rules).
- **`kms-key`** with rotation on and a deletion window, because both are easier to set than to change.
- **Tag every module release; callers pin the tag** (`docs/plan/conventions.md` §6) — never a branch.

**Why it moved, and it is the same argument twice rather than a new one.** On 2026-08-15 this step was moved
to the *end* of the stage because nothing in Stage 2 consumes a module: `bootstrap/` is forbidden one (2.3),
and `sso/` and `org-policies/` declare `aws_ssoadmin_*` and `aws_organizations_*` resources directly.
**That argument does not expire when the stage does.** At the end of Stage 2 there is still no caller, so
writing the three interfaces here is guessing — the thing `docs/plan/conventions.md` already refuses to do
for the `sandbox-unit` module. The first caller is Stage 3's `foundation/`, and Stage 3 **already writes a
module of its own** (`vpc/`), so the move costs that stage a sitting's structure rather than a new one.

**And it un-blocks an input this stage cannot settle.** A module is consumed **by git tag**, and this is a
monorepo: the reference is `…/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v1.0.0` against
a host that is GitHub today and **GitLab from Stage 7** (D8). Choosing the tag scheme and the source host
with no caller in hand is choosing them twice. Stage 3 settles both against a real `foundation/`, which is
where a wrong answer is visible as a failed `init` rather than as a convention nobody exercised.

*Recorded in [`docs/plan/history.md`](../history.md): this is a re-scope decided after the stage had already
provisioned, which is the class of plan change that file keeps.*

### 8. Teardown/rebuild tooling (D11)

**8.1 — Each slice declares its layer** (`[P]`/`[D]`/`[E]`) in a table the `Makefile` reads, rather than in a
comment. `docs/plan/conventions.md` §6 already assigns every slice its layer; the table is that assignment made
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
table sourced from `docs/PRICING.md`**, not from a live pricing call: a status command that needs the network is a
status command that fails when you most want it (and prices are measured, not reasoned — Lesson 6).

**8.5 — `ENV` names a business unit's sandbox, not *the* sandbox (D35).** Stage 14 step 6 makes the same
pair work against a generated unit; write nothing here that assumes N=1.

**8.6 — The Studio-app teardown hook exists but is a no-op until Stage 6.** `docs/plan/conventions.md` §6
requires `make down` to delete running apps through `sagemaker:ListApps`/`DeleteApp` against the
blueprint-provisioned domain, discovering the domain ID rather than having it pasted in. Write the hook now
and leave it empty — a hook added later is a hook that is missing from the first teardown that needed it.

**Built 2026-08-16, offline, with no AWS call in the sitting.** Two files own it and the `Makefile` owns
none of it — the division step 9 established: [`scripts/tfhygiene/layers.py`](../../../scripts/tfhygiene/layers.py)
is the table, [`scripts/slices.py`](../../../scripts/slices.py) is `list`/`check`/`up`/`down`/`status`, and
`make up`/`make down`/`make status`/`make slices` call it. **Five things the step decided while being
written, each of which it had left open:**

- **8.1's table is a `dataclass` list, and the *rank* is not one of its fields.** Order is read from a
  `RANKS` map keyed by **slice name** — `bootstrap` 0, `sso` 10, `org-policies` 11, `foundation` 20, `pki`
  30, `egress` 50 — because the dependency runs along the slice axis and not the account one. A row cannot
  carry a rank that disagrees with the map, and a slice name absent from the map **raises** rather than
  defaulting to the end of the order, so a new kind of slice declares its position deliberately.
- **The table is authored and the tree is discovered, and the disagreement is an error in both
  directions** — `./scripts/slices.py check`, in `make check` and in `pre-commit` on any `terraform-live/`
  `.tf`. **The expensive direction is a slice on disk with no row**: `make down` skips what it has never
  heard of, in silence, and for an `[E]` slice that is a bill. **Both directions were demonstrated failing**
  before being believed. It is `attachments.json`'s two-list shape (9.3) one target over.
- **8.4's `status` distinguishes "nothing is declared" from "everything is down", and that is the whole of
  what it can honestly say today.** It prints the empty set and *why* it is empty rather than `USD 0.00/h`,
  which is the answer a broken read would also produce (Lesson 13). Once a `[D]`/`[E]` slice exists it reads
  `terraform show -json` per slice and multiplies by that row's `usd_per_hour` — a **static** rate from
  `docs/PRICING.md` §3 — and a slice it could not read is reported as `UNREADABLE` and makes the total a
  floor rather than a measurement.
- **8.6's hook detects its own obsolescence instead of exiting 0 forever.**
  [`scripts/down-studio-apps.py`](../../../scripts/down-studio-apps.py) calls `sagemaker list-domains` in the
  target account: no domain → nothing to delete; **a domain → exit 1** naming the stage that owes it a body;
  a call that *failed* → exit 1 saying explicitly that this is not evidence no app is running. "Write the
  hook and leave it empty" is right about the body and would be Lesson 13 about the exit code.
  **It runs only when the `down` has something to destroy**, because it needs an SSO session and a no-op
  `make down` must not fail on credentials it never needed.
- **The `[D]` half is a stub that refuses to be reached silently.** Nothing on disk is `[D]` — **the first
  is Stage 4's WireGuard `vpn/`**, and `docs/plan/conventions.md` §5.1 names only two dormant things ever,
  that instance and Stage 7's GitLab EC2 with its EBS volume. **`nfs/`'s EFS is not one of them: it is `[P]`
  by rule 2** (D24), which is the distinction worth keeping, because "stateful" is what makes a slice `[D]`
  *or* `[P]` and the two readings diverge exactly there. So `up`/`down` print *"none declared"*, and a `[D]`
  row arriving before the hook has a body raises, naming 8.2 — the same shape as 8.6, for the same reason.

**All four refusals demonstrated in the same sitting** — 2 with `make down` and no `ENV` (exit 2, from the
`Makefile` guard *and* from `argparse`, two independent guards for the one refusal whose failure mode is
"destroyed the wrong account"); 4 against `production/bootstrap`; 1 against `identity/sso` and
`identity/org-policies`; and **3 against a fixture row that deliberately claimed `production/pki` was
`[E]`** — the only way to prove that the D36 exclusion is independent of the layer field rather than
shadowed by it. The fixture was removed and `check` reported the stale row on the way out, which
demonstrated the table's other direction for free.

**One thing 8.5 did not settle and this build did not settle either:** `ENV` is the **account folder**
(`sandbox`, `development`, `data-governance`, `production`, `identity`), and `sandbox` is written as unit 1's
**allocation** rather than as *the* sandbox. The per-unit token is open question 10's and is deferred to
N=2 — the same caveat `ENV_TOKENS` already carries, in the same file, so the two move together.

**A fourth vocabulary landed in [`scripts/tfhygiene/backend.py`](../../../scripts/tfhygiene/backend.py):
`PROFILES`**, the account folder → SSO profile map `up`/`down` authenticate through. It goes there because
that file is already the one keyed by account folder (Lesson 14), and because the profile is passed as
`AWS_PROFILE` **on each command** — never exported — which is Lesson 25 made structural rather than
remembered. `--dry-run` prints every command and runs none, which is also how the Validation reads a plan
instead of trusting a target list.

### 9. The checks that keep the conventions honest — four of them since 2026-08-15

**None of these run in "CI", because there is no CI.** GitLab arrives at Stage 7 and `.gitlab-ci.yml` at
Stage 8. Until then the enforcement surfaces are **`pre-commit`** and a **`make check`** target calling
scripts in `scripts/` — the shape [`scripts/check-plan-refs.py`](../../../scripts/check-plan-refs.py) already
establishes. **Stage 8 steps 5 and 6 move them into the pipeline** — step 5 is the `checkov` gate, step 6 is
this repository's own offline-gates pipeline (`fmt`/`validate` and these checks; `plan`/`apply` stay by
hand — Stage 8 decision 3, revised 2026-08-16). Write them as scripts so that move is a
pipeline line and not a rewrite.

**Done 2026-08-15. Four scripts, one `Makefile`, three new `pre-commit` hooks — and both surfaces call the
same scripts, so a gate and a target cannot disagree.**

| Check | Script | Where it runs |
|---|---|---|
| 9.1 | [`scripts/check-tf-conventions.py`](../../../scripts/check-tf-conventions.py) | `make check` + `pre-commit` on any `*.tf` |
| 9.2 | [`scripts/check-iam-wildcards.py`](../../../scripts/check-iam-wildcards.py) | `make check` + `pre-commit` on `terraform-live/identity/**` |
| 9.3 | [`scripts/check-ou-coverage.py`](../../../scripts/check-ou-coverage.py) | **`make check-ou` only** — it needs an SSO session |
| 9.4 | [`scripts/check-index.py`](../../../scripts/check-index.py) | `make check` + `pre-commit` on `policies/` or `POLICIES.md` — **moved out of `terraform-live/identity/org-policies/` on 2026-08-16**, so the six gates sit in one folder |
| 3.5 | [`scripts/check-bootstrap-parity.py`](../../../scripts/check-bootstrap-parity.py) | `make check` + `pre-commit` on `terraform-live/*/bootstrap/` — **a fifth, added by step 3** rather than by this step, because it guards a rule step 3 creates |
| 8.1 | [`scripts/slices.py`](../../../scripts/slices.py)` check` | `make check` + `pre-commit` on any `terraform-live/**/*.tf` — **a sixth, added by step 8** (2026-08-16), same reason: it guards a rule step 8 creates. A slice with no layer row is skipped by `make down` in silence |

**Four things settled while writing them, none of which the step had decided:**

- **9.3's authored map is a file, and it is the file step 5 will read** —
  [`terraform-live/identity/org-policies/attachments.json`](../../../terraform-live/identity/org-policies/attachments.json).
  It carries the root's six documents, the four OU pairs and the three OUs that carry none **with the reason
  each one is empty**, and it holds **names, never ids**. One file with two consumers is the whole point: the
  `for_each` of 5.3 and the check that guards it read the same bytes, so the thing that is checked is the
  thing that is applied (Lesson 14). A map living only inside the configuration would be checked by nothing
  until after an apply.
- **`make check` excludes `check-plan-refs.py`, which is red on prose that predates this stage** — three
  stage files record dated measurements phrased as *"all six accounts with a profile"*, and the check cannot
  tell a historical measurement from a count that goes stale. It keeps a target of its own, `make
  check-docs`. Folding a known-red check into the commit gate teaches people to bypass the gate, which costs
  more than the drift it catches.
- **9.1 skips full-line comments, and 9.2 does not skip anything.** A comment creates nothing and these files
  carry their reasoning in prose, so a check forbidding the *word* `us-west-2` in an explanation would buy
  vagueness and no safety. 9.2's exception is a `Sid`, not a line, and it is checked in **both** directions —
  a whitelist entry whose statement no longer carries a wildcard is a **failure**, because a
  permanently-satisfied exemption is how the next wildcard arrives under a name nobody re-reads.
- **A scanner that did not run must not report a clean section**, and this was measured rather than
  imagined: the first (shell) form of 9.1's `perl` failed to compile, printed its error on stderr and
  reported `none` over a file holding all three violations — the same output as a clean tree (Lesson 13).
  The exit status was then checked, and a failed scanner is a `FAIL`. The same afternoon produced the other
  scar in that function: without `close ARGV if eof`, `$.` counts across the whole file list and reports a
  violation at line 162 of a three-line file. *The 2026-08-15 rewrite of every script into Python on `uv`
  (same paths, same checks, same callers; `scripts/tfhygiene` and `scripts/repohygiene` hold the shared
  logic) keeps both properties structurally: a pattern that does not compile raises before anything is
  scanned, and line numbers restart per file because the loop is per file.*

**9.1 — No region literals** (`docs/plan/architecture.md` §4.1). `var.region` in every slice, AZs anchored on
**`zone_ids` from `.tfvars`** (settled by 1b step 6, 2026-08-12 — not on list position), AMIs from SSM public
parameters. A `grep` over `*.tf` that fails on a hardcoded region keeps this honest at no cost — and it
**must skip `backend.hcl`**, for the reason in 2.5. **Worth a second check in the same script:** an AZ
selected by index (`data.aws_availability_zones.this.names[0]`) is the failure §4.1 describes, and it is a
pattern a `grep` catches as cheaply as a region literal. **And a third: any occurrence of
`aws_s3_account_public_access_block` fails** — the account-level setting is hand-managed (5.2), and the SCP
that denies the API carves out exactly the principal that runs every apply, so this grep is the only
enforcement the rule has.

**9.2 — No wildcard account in an ARN condition.** This one guards a control rather than a convention: fail
if any policy document in `terraform-live/identity/` — either slice — carries `arn:aws:iam::*:role/...`.
That pattern means
"any principal of this name, in **any** account", so a condition meant to name one role silently names a role
anybody can create. It is invisible in a `plan` and cheap in a script. *(This check used to also require an
`awsds-scp-recovery` carve-out in every `Deny`; that half went away with D30. The wildcard half did not,
because it applies to the per-function carve-outs the design still has — D26, D27.)*
**One `Sid` is whitelisted by name, and the whitelist is part of the check rather than a loosening of it**
(1c decision 7, 2026-08-13): `DenyAccountBpaChangeExceptInfrastructure` in `awsds-org-scp-baseline.json`
carves the `InfrastructureAccess` Identity Center role out of the account-level BPA deny, and it *must*
carry a wildcard account because its whole purpose is to reach accounts that do not exist yet — the role's
ARN suffix is minted per account. **Whitelist that one `Sid` explicitly and fail on every other match**; a
check that is relaxed to accommodate its one exception stops being a check (`docs/plan/conventions.md`, IAM rules).

**9.3 — Every OU is accounted for** (5.3, as corrected). **This check carries more weight than the earlier
wording gave it, because point 1 of 5.3 moved the per-OU coverage guarantee out of the apply and into here.**
Enumerate the organization's OUs **at both levels** and fail if one appears neither in the authored
OU→document map nor in the map's explicit *no document* list. The two-list shape is the point: `Policy
Test`, `Security` and `Sandboxes` carry nothing **on purpose**, and a check that treats "absent" and
"deliberately absent" alike either fails permanently or passes on a real gap — Lesson 13, in a script.
`Sandboxes` is the one that must be listed by name with D37 beside it, because it is the only OU whose
emptiness a future reader will try to fix.

**As written it does four things, and the last two were not in the step.** The OU walk is
**breadth-first over the whole tree**, not two levels, so a depth nobody planned is enumerated rather than
missed. Then: (1) every OU is in one of the two lists; (2) every OU the map names still exists — a map entry
for a deleted OU is a `for_each` key that fails an apply; (3) every document the map names is a file in
`policies/`; and (4) **what is attached matches what the map authors**, per target, for all four policy
types. (4) is what makes the map a control rather than a comment, and it is scoped to *our* documents by
testing for `policies/<name>.json` — a stronger binding than a name prefix, and the reason Lesson 23's
"never bind to a name" does not apply: these are the documents this project owns. It looks at **no
account-level attachment**, because this design has none; that census is `./aws/org-policies.py` §1.

**9.4 — `check-index.py` joins `make check`.** It already exists, it already decides the mechanical half of
"does `POLICIES.md` still describe `policies/`", it needs no AWS session and it exits non-zero when it
drifts — and it is run by hand today, which is exactly the state 6.4 and 9 exist to end. Once
`org-policies/` manages those documents, a statement added in Terraform with no row in `POLICIES.md` is a
control nobody can explain, and this is the script that catches it.

### 10. Documentation

Update **`README.md`** with the repository layout and the AWS resource structure (required by `CLAUDE.md`),
add the links used to **`docs/REFERENCES.md`**, and record in **`docs/log/log-stage-02-terraform-foundation.md`** the
decisions listed below.

---

## The instruments this stage runs on — written 2026-08-15, before the stage

**This stage is the first that must feed AWS-generated identifiers back into a command**, and that is a
different job from every snapshot `aws/` held before it: a snapshot is read by a human who tolerates a stale
line, an import id is pasted into a state file and a wrong one produces an orphan and a create rather than
an error. Four scripts were written for that, and one existing defect fixed. **They exist now, so this stage
starts with its instruments rather than building them.**

| Instrument | What it answers here | Run it at |
|---|---|---|
| [`./aws/org-delegation.py`](../../../aws/org-delegation.py) | **INT-20 / verification (vi)** — whether a delegation exists, and whether its `Resource` list reaches the **root** (`DEL-6`), **nested** OUs (`DEL-7`) and the **policy-type ARNs** (`DEL-9`, added 2026-08-15 — a target-only list denies every write). Reports the resource policy in **three** states, so "not delegated" and "the read was denied" stay apart | **5.0**, before and after 5.1; then at every landing-zone update |
| [`./aws/import-ids.py`](../../../aws/import-ids.py) | Every `terraform import` string, in the four formats of 5.5a(iii); the resolved values of the three template placeholders; and **section 4, what must not be imported** | **5.5**, immediately before importing |
| [`./aws/tf-backends.py`](../../../aws/tf-backends.py) | Before step 2: *is anything already there*. After step 3: *did every bootstrapped account get the same treatment* — and whether **Production carries the two keys of 3.4** | **2** and **3**, on both sides |
| [`./aws/cloudshell/management-quotas.sh`](../../../aws/cloudshell/management-quotas.sh) | Whether the account-cap increase has landed — the number **3.2** is waiting on. Refuses to interpret the value outside Management, where the same quota reads `0.0` | before **3.2**, whenever it is worth re-asking |
| [`./aws/org-policies.py`](../../../aws/org-policies.py) | **Fixed 2026-08-15**: §1 listed ids for `SERVICE_CONTROL_POLICY` only, so **three of the ten attached documents had no id in any snapshot**. All four types now carry theirs | after any attach, and at every vend |

**Two disciplines these carry that this stage depends on, and neither is a detail of the scripts.**

- **`import-ids.py` owns the right-hand side and not the left.** The id is measured; the Terraform
  *address* is a suggestion, because only the configuration knows whether a resource is `.baseline` or
  `.this["awsds-org-scp-baseline"]`. That division is what makes 5.5a(iii)'s `for_each` warning actionable
  rather than a caution.
- **`org-delegation.py` stops before the write, and says why.** Organizations *reads* already answer from
  the Identity account with no policy delegation at all (1c verification (x)), so a read-based check would
  return OK before **and** after 5.1 — not a verification (Lesson 13). It therefore decides **scope by
  reading the delegation document** — not Lesson 22's case (the harness *can* produce the principal;
  `awsds-infra-identity` is the delegate) but `aws/`'s own fence: a measurement that changes a policy is a
  deliberate human act, the same line `aws/probes/` draws. That act is 5.0's `update-policy`, run **from
  `awsds-infra-identity`** — from Management it always succeeds and proves nothing.

---

## Deliverables

Each is written so its output differs between working and broken (Lesson 13):

- **A slice applies end to end against a real account:** `terraform apply` in `sandbox/bootstrap/` under
  `awsds-infra-sandbox-1`, then `terraform init -migrate-state`, then a second `terraform plan` that reports
  **no changes** while reading state from S3.
- **Locking is real:** two concurrent `terraform plan` runs against the same slice — the second reports a
  lock held, rather than both succeeding.
- **Both imports are faithful:** after the import and the first apply, `terraform plan` is **empty** in
  `identity/sso/` *and* in `identity/org-policies/`, and `organizations list-policies` **run once per policy
  type** — `SERVICE_CONTROL_POLICY`, `RESOURCE_CONTROL_POLICY`, `TAG_POLICY`, `DECLARATIVE_POLICY_EC2` —
  lists the same policy IDs the second state holds. **One filter is not the check**: reading only
  `SERVICE_CONTROL_POLICY` reported three of the ten documents as absent both before and after they were
  attached, which is how 1c nearly mis-read its own read-back. **And the attachments, not only the
  policies**: state holds an `aws_organizations_policy_attachment` per target/policy pair of
  `org-policies.txt` §1/§4 — an attachment missing from both the configuration and the import passes the
  empty-plan gate silently.
- **The written half exists where it did not before:** the six persona permission sets are returned by
  `aws sso-admin list-permission-sets` **and none of them was created before this stage** — the log of
  1b records one set created by hand, not seven. A group assignment resolves to a group by name:
  `terraform state show` on one of them names a principal ID that
  `aws identitystore describe-group` resolves back to the expected display name.
- **The two slices are independent, which is why they are two:** `terraform state list` in `sso/` names no
  `aws_organizations_*` **managed resource**, and `org-policies/` names no `aws_ssoadmin_*` one. Neither
  reads the other through `terraform_remote_state`.
  **The word "managed" is doing work and was added on execution, 2026-08-16, rather than discovered as a
  failed check.** `sso/` *does* read `data.aws_organizations_organization` — one data source, and there is
  no second way to turn an authored account **name** into the id `aws_ssoadmin_account_assignment` requires
  while `aws/INDEX.md` rule 1 keeps ids out of tracked files. That is the same shape `attachments.json`
  already uses on the other side: names in the file, ids resolved by the consumer. **The independence the
  split exists to buy is about who *owns* an object** — a failed `apply` in one slice must not be able to
  change anything the other declares — and a read does not own. State will list the data source; the claim
  is that nothing under `aws_organizations_*` in `sso/` has a lifecycle.
- **The delegation took effect** (INT-20): 5.0 step 3's **write** — `organizations update-policy` on the
  tag policy with its own content — succeeds **under `awsds-infra-identity`**, and `./aws/org-delegation.py`
  passes `DEL-6` (root reach), `DEL-7` (nested OUs) and `DEL-9` (policy-type ARNs) on the read-back
  document. A `describe-policy` read is not the evidence: it succeeds identically with no delegation at all
  (Lesson 13). **Met 2026-08-15**, and reading 4 met the half `UpdatePolicy` cannot reach: it authorizes on
  the policy ARN only, so the `Resource` list's **target** entries needed the duplicate-attach —
  `DuplicatePolicyAttachmentException` on the root **and** on the `ou/…/*` wildcard, with the negative
  control from `awsds-policy-canary` returning `AccessDeniedException` — which is what makes the two
  duplicate answers evidence at all. **Step 5.0 is closed**; only `account/…/*` is unexercised, and it is
  an over-grant nothing here needs.
- **The checks fail on purpose:** a commit introducing `us-west-2` in a `.tf` file, and one introducing
  `arn:aws:iam::*:role/x`, are both rejected. A check nobody has seen fail is a hypothesis.
  **Met 2026-08-15**, with both violations staged together: `pre-commit` exits 1 and three hooks go red —
  9.1 on the region literal, 9.2 on the wildcard, and 9.4 on the document with no row in `POLICIES.md`.
  Each of 9.1's three rules was also fired separately against a fixture, **and so was the failure mode
  underneath them all**: a scanner made to break reports `FAIL … this section checked NOTHING`, not `none`.
- **The `Makefile` refuses what it must:** `make down ENV=sandbox` is a **safe no-op** at this point — no
  `[E]` or `[D]` slice exists yet — and `bootstrap/` is untouched; `make down` with no `ENV` exits non-zero.
  **Met 2026-08-16**, and then met a second time in the way that matters more: **against a real `[E]`
  slice.** A no-op proving a refusal is Lesson 13's shape — a target that refuses everything and a target
  that does nothing print the same thing — so the Validation gave `make down` something it *could* destroy,
  and the destroy plan named the SSM parameter and nothing else while `bootstrap/` sat in the refused list.
  All four refusals were fired individually, refusal 3 against a fixture row that deliberately claimed
  `production/pki` was `[E]`, which is the only way to show the D36 exclusion is not merely shadowed by the
  layer filter.
- **A slice that declares no layer cannot pass the gate:** creating `sandbox/scratch-test/` turned
  `./scripts/slices.py check` red before its rows were written, and removing the slice while leaving a row
  turned it red the other way. **Met 2026-08-16**, both directions, which is what makes the layer table
  evidence rather than a listing.

## Validation

1. **Reproducibility:** create a throwaway `[E]` slice — `sandbox/scratch-test/`, holding one SSM parameter
   and nothing else, so it is free and instant — then `make down`, then `make up`, and confirm it comes back
   identical. Naming it here rather than leaving "a throwaway slice" to the keyboard is Lesson 16.
2. **Isolation:** confirm `make down` leaves `bootstrap/` untouched — by reading the plan output, not by
   trusting the target list.
3. **Delete the throwaway slice** when both pass.

**The recipe, written out 2026-08-16 so the sitting is a paste rather than a design** *(step 8 exists now,
so the Validation has something to validate)*. **Who:** the infrastructure user on `Sandbox Account 1`
through `InfrastructureAccess` — profile `awsds-infra-sandbox-1`, and `AWS_PROFILE` is on each command
because `slices.py` puts it there (Lesson 25). One `aws sso login --sso-session awsds` first.

1. **The slice.** `terraform-live/sandbox/scratch-test/` with `versions.tf` and `providers.tf` copied from
   `sandbox/bootstrap/`, a `backend.tf` that is **live from the start** — only `bootstrap/` migrates
   (step 4) — and one `main.tf` holding a single `aws_ssm_parameter` (`String`, one value, the five tags
   arriving from `default_tags`). Free, instant, and it deletes cleanly.
2. **Two rows, not one.** `layers.py` gains `Slice("sandbox", "scratch-test", EPHEMERAL, …)` **and**
   `RANKS` gains `"scratch-test"` — the rank map raises on an unknown name rather than defaulting, which is
   the guard 8.1 was given. `make check` is red between creating the folder and adding the rows, and that is
   the check doing its job rather than an obstacle.
3. **First apply** — `make up ENV=sandbox`, which is now non-trivial for the first time: the refusal list
   still prints five `[P]` slices and the `[E]` one is applied. Record the parameter's ARN.
4. **`make down ENV=sandbox`**, and **read the plan before approving** — the isolation test is that
   `bootstrap/` appears in the *refused* list and in no destroy plan. `--dry-run` prints every command
   without running one, which is the cheaper half of the same reading.
5. **`make up ENV=sandbox` again**, and confirm the parameter comes back with the same name and value.
   *An identical ARN is not the claim* — SSM parameters have no generation in their ARN, so what is
   demonstrated is a slice rebuilt from code, not a resource that survived.
6. **`make status`** now takes its other branch for the first time: a declared `[E]` slice, read rather
   than assumed. It reports `UP` before the `down` and `down` after it — the distinction the empty-set
   branch cannot make, and the reason 8.4 was written with two branches.
7. **Delete the folder and both table rows**, then `make check` green again. The Validation is a
   measurement, not a fixture: an `[E]` slice left behind would be the first row in a table whose whole
   claim is that it matches the disk.

**RAN 2026-08-16 — both halves pass, and the slice is gone.** Infrastructure user on `Sandbox Account 1`
through `InfrastructureAccess` (`awsds-infra-sandbox-1`). **Four things the run produced that the recipe had
not, and the first is the one that outlives this stage:**

- **`awsds` is a reserved prefix in SSM Parameter Store, and the repository's own naming convention walked
  straight into it.** The first apply used `/awsds/sandbox/scratch-test/validation` and AWS refused at
  `PutParameter`: *`AccessDeniedException: No access to reserved parameter name`*. Parameter Store reserves
  any name beginning with **`aws`** or **`ssm`**, and `awsds` begins with `aws`. **The collision is specific
  to Parameter Store *names*** — `awsds-` is untouched everywhere else, which is why the state buckets, the
  ten policy documents and the permission sets never met it. **Any stage that writes a project parameter needs a
  different first segment**, and the failure is an `AccessDenied` that reads like a policy problem rather
  than like a naming one. Recorded in `docs/plan/conventions.md` under naming.
- **The value is read back from AWS, not exported from state — and the provider is what forced the
  question.** `aws_ssm_parameter.value` is sensitive, so an output needs `sensitive = true`; that is
  available and is the wrong answer, because the Validation's claim is *rebuilt from code* and a value read
  out of the state file is the state agreeing with itself. Same discipline as step 5's read-backs.
- **The rebuild is proven by the `Version`, not by the ARN.** After `down` then `up` the parameter reads
  back with the same name and value at **`Version 1`**, not 2 — SSM's version counter restarts, so the
  object is demonstrably **new** rather than a survivor. The ARN is derived from the name and would have
  been identical either way, which is exactly why `outputs.tf` says so in the file.
- **The Validation leaves an orphan state object and it was deleted deliberately.**
  `sandbox/scratch-test/terraform.tfstate` (540 bytes, an empty resource list) survives a `destroy` because
  a destroy empties a state, it does not remove it. Left behind, it is a state key for a slice that no
  longer exists — the residue `./aws/tf-backends.py` would later have to explain. Deleted; versioning being
  on, that is a delete marker whose noncurrent versions expire under 2.1's 90-day rule.

**The two claims the Validation exists to make, measured rather than asserted:** `make down ENV=sandbox`
planned **`0 to add, 0 to change, 1 to destroy`** and named only the parameter — `bootstrap/` appeared in
the *refused* list and in no plan, and its bucket and key answered afterwards unchanged. And `make status`
took **both** of its branches for the first time: `UP 1 resource(s)` before the teardown, `down 0
resource(s)` after it, and the empty-set branch again once the rows were removed. **8.6's hook ran for
real**, not as a stub: *"no SageMaker domain in sandbox - nothing to delete"*.

## Decisions due while executing

**Blocking questions for the user: none.** Six decisions are *made* during the stage and each is written
into `docs/log/log-stage-02-terraform-foundation.md` rather than left to whoever is at the keyboard (Lesson 16):

1. **The exact Organizations delegation document** (5.1) — which actions, which resource ARNs, and the
   explicit note that it reaches Control Tower's own SCPs.
2. **Whether `production/pki/` shares the Production state bucket** with its own `kms_key_id`, or gets a
   bucket of its own (3.4).
3. **The noncurrent-version lifecycle on the state buckets** (2.1) — the retention, and that it is a cost
   choice rather than a compliance one.
4. **How `DataScientistAccess`'s permissions boundary is delivered** (5.2, 1b step 3.4) — an `aws_iam_policy`
   created by each target account's `foundation/` and attached afterwards, an AWS-managed policy, or
   inline-only sets until Stage 3 exists. It is a decision rather than a preference because a
   customer-managed reference that is missing in *one* account fails provisioning **in that account only**,
   and with one Sandbox per business unit (D35) the number of places it can be missing grows.

   **Settled 2026-08-16: inline-only here, the boundary *object* deferred to Stage 3 — and the two denies
   that mattered are not deferred with it.** The three options are not equally available today. A
   customer-managed reference needs an `aws_iam_policy` of that name and path in **every** account a set is
   provisioned into, and no governed account has a `foundation/` slice yet, so the reference would fail
   *provisioning* per account — the quiet form of the mistake. An AWS-managed policy as the boundary is
   available and buys nothing: none of them expresses the two denies this design actually needs, and a
   boundary that does not carry them is a boundary in name.
   **What is deferred is therefore the container, not the content.** The two denies 5.2 requires of every
   boundary — `iam:CreateRole` under the `/aws-reserved/` path, and `iam:UpdateAssumeRolePolicy` on a role
   the ceiling exempts — go into the **shared deny fragment** of the six sets **now**, written once and
   referenced by all six (Lesson 14), because the carve-outs they defend are attached *now*. A boundary
   would have made them un-escapable rather than merely present; the inline deny makes them present, which
   is the whole of what a set can do to itself. Stage 3's `foundation/` creates the `aws_iam_policy` per
   account and this slice gains one `aws_ssoadmin_permissions_boundary_attachment` per set — a diff, in the
   stage that can actually satisfy it.
   **One thing that does *not* wait on Stage 3, and is now cheaper than the step assumed:** the
   `Policy Canary` `create-role` probe. 5.2 wanted it *before* the boundaries were written; with the deny
   written and no boundary, its answer no longer gates anything — it says whether the first deny is
   load-bearing or belt-and-braces, and the deny costs nothing either way.
5. **How the placeholders in `policies/*.json` are substituted** (5.5a(i)) — `replace(file(…))` against the
   templates as they stand, or a conversion to `${…}` with a matching edit to `render.py` in the same
   commit. Either works; taking one and not writing it down leaves two mechanisms for the same substitution,
   which is the shape Lesson 14 keeps producing.

   **Settled 2026-08-16: `replace(file(…))` wrapped in `jsonencode(jsondecode(…))`, and `render.py` is not
   touched.** The conversion to `${…}` is the tidier of the two and it is the wrong one *here*, for a
   reason specific to this moment: **`render.py` produced the bytes that are attached to the organization
   right now**, and 5.5's whole claim is that the import compares a document against itself. Editing the
   generator in the same commit that first compares against what it generated makes the reference and the
   comparison move together — the shape 5.0's "its own content" rule already refuses for `update-policy`.
   The wrapper is what makes the choice safe rather than merely available: it normalises both sides
   identically, so what is compared is content and not whitespace. **Re-openable, and the trigger is
   named:** if a later stage needs `templatefile()` for something else in `policies/`, convert then — with
   the documents already imported, a normalising diff is a `plan`, not a leap.
6. **`import {}` blocks or `terraform import` on the command line** (the `aws/` section above). Blocks are
   reviewable and live in git — which is the problem: their `id` is an account id or a policy id, and no
   account id enters a tracked file. Record the choice and, if it is the CLI, that the manifest lives in
   untracked `aws/output/`.

   **Settled 2026-08-16: the CLI, with the manifest in untracked `aws/output/import-ids.txt`.** The
   argument for blocks is real — they are reviewable and they leave a record — and it loses on one
   measured fact rather than on taste: **the `sso/` half cannot be written as blocks without putting five
   account ids in a tracked file.** `aws_ssoadmin_account_assignment`'s import id is
   `<principal_id>,GROUP,<account_id>,AWS_ACCOUNT,<ps_arn>,<instance_arn>` — the target account id is
   *inside* the id — and `aws/INDEX.md` rule 1 admits no exception. The same id also carries the group
   **GUID**, which the configuration is forbidden to hold for a different reason (conventions, "resolve a
   group by display name"): a block would put in git precisely the two values the design keeps out of it.
   **What replaces the reviewability:** `./aws/import-ids.py` is the record — regenerable, dated, and it
   owns the right-hand side while the configuration owns the address.

*(One more used to be here — whether to split `terraform-live/identity/`. It was settled on 2026-08-09,
before execution: the split is the design, its reasoning is in step 5 and the layout is in
`docs/plan/conventions.md` §6. Splitting afterwards would have been a state move, which is the whole reason it
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
- **The apply that reverses a decision is worse than the apply that fails, and 5.3 had one in it.** A
  `for_each` attaching a per-OU document to every discovered OU would have put one on `Sandboxes` and undone
  D37 with `terraform plan` reading like ordinary coverage. It is corrected above; the general form is worth
  carrying — **a rule written as "cover everything" meets a decision written as "this one is deliberately
  empty", and the rule wins silently.**
- **Six of the ten documents are on the organization root, so 5.0 can remove most of `org-policies/`.**
  That is a scope risk rather than a technical one, and the mitigation is entirely in the ordering: it is now
  the first thing the stage does, so the answer arrives before anything has been written against it.

## Verifications to answer while executing

Record every answer in `docs/log/log-stage-02-terraform-foundation.md`, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | **First half answered 2026-08-15, by reading the applied bucket: yes — `pki/` keeps its own key inside the shared Production bucket, and the own-bucket fallback is not needed.** The bucket policy is *one* statement (`DenyInsecureTransport`, `Bool aws:SecureTransport = false`) with **no `s3:x-amz-server-side-encryption-aws-kms-key-id` condition anywhere**, and SSE-KMS default encryption is a *default*: a `PutObject` naming another key overrides it. **The second half — does an S3 Bucket Key apply to that override — stays open, and it is not answerable by reading**: `BucketKeyEnabled` is reported per object, so it needs an object encrypted under the PKI key. It arrives free at Stage 7's first `production/pki/` init, or earlier from a three-call probe (`put-object --ssekms-key-id`, `head-object`, `delete-object`). **Either answer leaves D36's alarm intact** — it is scoped to the *key*, which the event names in `resources` (2.7) — so what is open is how the record reads, not whether the control fires | 3.4 |
| ii | ~~Does the pinned provider support `aws_organizations_policy` with `type = "DECLARATIVE_POLICY_EC2"`?~~ **Answered 2026-08-16 by the apply: yes.** `awsds-org-declarative-ec2` is one of the ten documents imported and tagged in `identity/org-policies/`, under **aws 6.60.0**, and its `type` produced no diff in a plan that read `0 to add, 10 to change, 0 to destroy`. The fallback the question was written for — that one policy stays console-managed and is *recorded* as unowned — is not needed | 5.2 |
| **iii** | ~~Does the Organizations **policy** delegation coexist with the Control Tower landing zone without raising drift?~~ **Answered 2026-08-16 from Management as `AWS Control Tower Admin` / `AWSAdministratorAccess`, through [`aws/cloudshell/management-landing-zone-drift.sh`](../../../aws/cloudshell/management-landing-zone-drift.sh): no drift — `ACTIVE`, version `4.0` = latest, `driftStatus: IN_SYNC`, `remediationTypes: INHERITANCE_DRIFT`, and the resource policy `PRESENT` with 5.1a's condition still on exactly two statements. The delegation raises no drift and the landing zone did not disturb it.** **And the answer carries two limits, both named rather than glossed, because the run made them sharper than the question anticipated.** *(1)* The **manifest** holds `accessManagement`, `backup`, `centralizedLogging`, `config`, `governedRegions: ["us-west-2"]` and `securityRoles` — **nothing about an organization resource policy**, so `IN_SYNC` is *silence* about the delegation rather than approval of it. *(2)* The **operation history is a single `CREATE`, `SUCCEEDED`** — **the landing zone has never re-run**, so the positive evidence the report was built to capture (an `UPDATE`/`RESET` after 2026-08-15 that survived) **does not exist yet**, and "has not disagreed" is not "has agreed". **The strong test — `update-landing-zone`/`reset-landing-zone` — is a write and stays refused** (Lesson 22). **Re-read at the next landing-zone update, at the next Control Tower version bump (the two version fields are equal today) and at the `Staging` vend** | 5.1 |
| iv | ~~Does `aws_organizations_organizational_unit_descendant_organizational_units` really recurse, in the pinned version?~~ **Answered 2026-08-16: yes**, read from the applied slice with `terraform console` as `awsds-infra-identity`. It returns **seven** OUs — `Data`, `Identity`, `Interactive`, `Policy Test`, `Sandboxes`, `Security`, `Workloads` — and **`Sandboxes` is the evidence**: it sits at depth 2 under `Interactive` (D23), so a single-level source would have omitted exactly it. **The postconditions do not prove this and could not**: every name `attachments.json` requires sits at depth 1, so they pass identically against a non-recursing source. The stakes were already reduced by 5.3 point 1 — this feeds `make check-ou`, not the attachments | 5.3 |
| v | ~~Is the `for_each` key stable enough that adding an OU does not re-create existing attachments?~~ **Answered by reading, 2026-08-16, and the reading is short because 5.3 point 1 made it so.** The keys are computed from `attachments.json`, which authors **names**; the OU data source only turns an authored name into an id. A new OU therefore adds no key, changes no key and is invisible to this `for_each` — it surfaces in `make check-ou` as an OU in neither list, which is where 9.3 was moved to catch it. This is Lesson 22's shape: the harness cannot produce a new OU without vending one, and the property is decided by what computes the key | 5.3 |
| **vi** | **Can the delegated administrator manage a *root-attached* document, not only an OU-attached one?** This is the one that decides the size of the stage, and it is answered first | **5.0** |
| **vii** | ~~Does `CTMULTISERVICEPV1` exempt `organizations:*` for *writes*?~~ **Answered by reading — the 1d log already took the read (2026-08-14): the `CT.MULTISERVICE.PV.1` document on `Identity` (`p-fw2pctqw`) carries `organizations:*` wholly in its `NotAction`**, the service wildcard, so writes are exempt along with the reads. Every call this slice makes is out-of-Region by construction (Organizations answers in `us-east-1`) and none is Region-denied. Re-read in 5.0 only if the landing zone was updated since | 5.0 |
| **viii** | ~~**Does `jsonencode(jsondecode(replace(file(…))))` reproduce the attached bytes**, for all four policy types?~~ **Answered 2026-08-16: yes for all four, and the answer cost one tracked file.** The plan carried **no `content` diff on any of the ten documents**, RCP and declarative policy included, and the apply's read-back confirms the live bytes are still 1c's console paste — so the comparison is *structural*, not byte-for-byte, which is what `jsonencode(jsondecode(…))` was chosen to make true. **The one file that had to change is the finding**: `awsds-org-rcp-perimeter.json` wrote a single action as `["ecr:*"]` where Organizations holds `"ecr:*"` — identical to IAM, different to the provider — and it was the folder's only one-element action array against seven single-action statements already written as scalars | 5.5a |
| **ix** | ~~**Does the delegation document accept a `Condition` on `aws:PrincipalArn` at all** — and, if it does, does the A/B come back (a) `AccessDenied` from `awsds-ctadmin-orgfull-identity` **and** (b) still `DuplicatePolicyAttachmentException` from `awsds-infra-identity`?~~ **Answered 2026-08-16, all three halves: the document accepts the condition** (unlike `NotAction`/`NotResource`, which it still rejects — so those are not one rule with two instances); **(a) returned `AccessDeniedException` and (b) still returned `DuplicatePolicyAttachmentException`**, with `DEL-10` flipping red→`pass` on the read-back. Half an answer here would have been indistinguishable from a broken delegation, which is why both legs were run in the same sitting | **5.1a** |

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
