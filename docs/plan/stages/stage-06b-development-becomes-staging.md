# Stage 6b — `Development` becomes `Staging`

| | |
|---|---|
| **Status** | not started — **created 2026-09-05**, when the user re-scoped the estate on three inputs: the account-quota increase was refused, so no account can be vended; the SageMaker experience showed no need for a *second* interactive environment; and the network needs a hub (6c). This stage converts the existing `Development Account` into the `Staging Account` the plan always described and never had: same account, same VPC CIDR, new name, new OU, new persona set, **no interactive surface**. It is [D21](../decisions/D21-development-account.md)'s own larger branch, pre-written on 2026-08-13 and now taken |
| **Prerequisites** | [6a](stage-06a-unified-studio.md) (what is being unwound was built there). **Nothing in 6c blocks this stage and this stage blocks nothing in 6c** — the two touch at exactly one object, the `Development ↔ Production` peering, which stays as it is until 6c re-cuts it |
| **Consumes** | [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D26](../decisions/D26-unified-studio.md), [D32](../decisions/D32-account-factory-sso-user.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | Nothing new crosses an account boundary here. What it **retires**: [INT-04](../integrations.md) (the registry read from Development, merged into INT-07), the Development halves of INT-01/02/12/15/17/18/19, and INT-03's third consumer. [INT-09](../integrations.md)'s premise (a Studio project in Development cloning GitLab) dies with the interactive surface; its peering is re-purposed at 6c |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, the slice
table) and [`docs/plan/runbooks/terraform-changes.md`](../runbooks/terraform-changes.md) (the two-commit
tag order, Recipe D, and **Recipe E**, which step 4.1 writes).*

---

**Objective:** one account changes role. `Development` — an Interactive member of the SageMaker Unified
Studio domain, with a Lake Formation share, a read-write data-scientist persona and eleven blueprint
configurations — becomes `Staging`: a **Workload** deployment target written only by the pipeline, holding
the SageMaker **runtime** and nothing a human runs code on. The promotion chain becomes
**N Sandboxes → one Staging → one Production**.

## Why the order below is the stage, and not an implementation detail

Three facts make this a choreography rather than a rename:

1. **The `Workloads` OU denies `datazone:*`** (`awsds-org-scp-ou-workloads`, `DenyDataZoneEntirely`). The
   eleven blueprint configurations and the eleven authorization grants are owned by the **member** account
   and only the member can delete them. An account moved to `Workloads` first can never destroy them, and
   an incomplete configuration pins its dependents in **both** directions (Lesson 39). **Every `datazone:`
   delete happens while the account is still in `Interactive`.**
2. **The vocabulary is derived.** `scripts/tfhygiene/backend.py` computes `profiles_enabled` from
   `SMUS_ASSOCIATED`; removing `development` from that list alone would flip the flag and the next
   `governance/` apply would destroy the **`experimentation`** profile too. The two lists move in **one**
   edit.
3. **The `dev` token names `[P]` objects that cannot be renamed** — `awsds-dev-tfstate`,
   `alias/awsds-dev-*`, `awsds-dev-smus-projects` — and the Terraform state key carries the folder name, so
   a folder rename moves every state object. There is no recipe for that in this repository; step 4.1
   writes one.

**What this stage does NOT do:** it does not touch the network (6c owns it), does not build Staging's
runtime (Stage 9 owns it), and does not create a data share of any kind — D20's Staging is never on the
lake share, and step 2 removes the one it inherits.

**Who does what, stated once:** **Claude** writes every edit, runs `plan`, the read-only `aws/` scripts and
the hygiene gates, and drafts every console step with each field named (Lesson 16). **The user** runs every
`terraform apply` and `destroy`, the console acts (the SMUS disassociation, `PutAccountName`, the Control
Tower *Update account*), edits `~/.aws/config`, and writes the log entries. Steps are tagged only where the
split is not obvious from this rule.

---

## To execute

### 0. Preflight — read what the account actually holds, before anything is removed

**Why:** the unwind is written against a snapshot from 2026-09-05, and three of its numbers (`22`
grants+configurations, zero projects, one Access Grants instance in Sandbox only) are the difference
between a clean destroy and a stranded object. A read that disagrees with this file stops the stage.

- **Reading the SMUS surface — Claude:** run `./aws/studio.py` and confirm, for the Development profile,
  `US-3` = 11 blueprint configurations, `US-4` = both project profiles, **no project**, and no SageMaker AI
  domain. A project here means step 1.2 grows a delete and the stage waits for it.
- **Reading the lake surface — Claude:** run `./aws/datalake.py` and record the Development rows —
  `DataLakeSettings` admins, the two resource links, the four re-grants and the two TBAC share triples that
  `data-governance/data/` holds for this consumer. These become step 2.3's expected destroy count.
- **Reading the identity surface — Claude:** run `./aws/list-identities.py` and record the four permission
  sets assigned to the account (`InfrastructureAccess`, `DataScientistAccess`, `DeploymentManagerAccess`,
  `DevEnvStewardAccess`) plus the customer-managed `awsds-org-project-storage-vending` reference.
- **Reading the organization's two switches — user**, CloudShell in **Management** as the
  **`AWS Control Tower Admin`** user (`AWSAdministratorAccess`; the `awsds-ctadmin-orgfull-*` profiles do
  not reach Management): `aws organizations list-aws-service-access-for-organization` (is
  `account.amazonaws.com` already trusted? step 3.1 needs it) and the landing zone's **account
  auto-enrollment** setting (it decides whether the OU move re-baselines by itself). Claude turns both into
  `aws/cloudshell/management-account-switches.sh` first.
- **Recording the snapshot — Claude:** paste the four readings into the stage log's first entry, so the
  destroy counts below are measured rather than quoted.

### 1. The SMUS unwind — remove the interactive surface while the account is still in `Interactive`

**Why:** this is the only window in which the deletes are permitted (see fact 1 above). The order inside
the pass is profile → configurations → association → vocabulary, which is the exact reverse of how 6a built
it.

- **Removing the `engineering` project profile — Claude edits, user applies:** delete `engineering` from
  `local.project_profiles` in `terraform-live/data-governance/governance/locals.tf` and the `development`
  provider alias and data source with it; apply as `awsds-infra-data`. **Expect exactly `2 destroyed`** —
  the profile and its `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to `sso-group-deployment-managers`. D21
  names this removal as the expected first act of its own larger branch.
- **Writing the staged-destroy exception first — Claude:** add to
  [`runbooks/terraform-changes.md`](../runbooks/terraform-changes.md) a **Recipe F — staged destroy of
  `awscc` objects with attached grants**, the mirror of Recipe D and the only other sanctioned `-target`:
  grants first, configurations second, one `-target` per resource type, `plan` between them. A destroy of a
  blueprint configuration with a grant attached has never been exercised in this estate.
- **Destroying the eleven configurations and their grants — Claude edits, user applies:** set
  `blueprints_enabled = false` in `terraform-live/development/sagemaker/` and apply as `awsds-infra-dev`.
  **Expect `22 destroyed`.** If the provider orders grant and configuration wrongly, fall back to Recipe F.
- **Reading the member back — Claude:** `aws datazone list-environment-blueprint-configurations` and
  `list-policy-grants` from `awsds-infra-dev` must both return empty. An error here is a different failure
  from an empty list, and only the empty list closes the step.
- **Disassociating the account — user**, console, in the **Data Governance** account: SageMaker Unified
  Studio → domain `awsds-studio` → **Account associations** → select the member → **Disassociate** → type
  `disassociate` to confirm. There is no API for this; the documentation lists no prerequisite, which is
  why the two read-backs above run first.
- **Reading the association back — Claude:** from `awsds-infra-dev`,
  `aws ram get-resource-shares --resource-owner OTHER-ACCOUNTS` shows no DataZone share, and
  `list-environment-blueprint-configurations` now **fails** rather than returning empty — 6a step 1.3's
  proof, in reverse.
- **Editing the vocabulary in one commit — Claude:** remove `development` from **both** `SMUS_MEMBERS` and
  `SMUS_ASSOCIATED` in `scripts/tfhygiene/backend.py`, regenerate the tfvars, and re-plan
  `data-governance/governance/` to **`No changes`**. That plan is the proof that fact 2 was respected.
- **Destroying the rest of the slice — Claude edits, user applies:** empty `awsds-dev-smus-projects` by
  hand (list it first — no project ever wrote to it), remove the module call so the `prevent_destroy`
  lifecycle block leaves the configuration with it, then destroy `terraform-live/development/sagemaker/`.
  The project CMK `alias/awsds-dev-project` enters its deletion window; record the scheduled date.
- **Re-reading the estate — Claude:** `./aws/studio.py` must now show one associated account, one project
  profile, and no Development rows anywhere; `US-6`'s "datazone reads denied in Workloads" is checked again
  at step 3.4, after the move.

### 2. The persona and the lake — make the account read-only, in the order that does not lock anybody out

**Why:** D18 says "Staging — read-only, and nothing else" and D20 says Staging is never on the lake share.
The account today holds the opposite of both. The order matters twice: an assignment must be **removed
before** the customer-managed policy it references, and the share must be revoked from the **producer**
side before the consumer slice that uses it is destroyed.

- **Swapping the assignments — Claude edits, user applies:** in `terraform-live/identity/sso/locals.tf`,
  replace `data-scientist@development` with `data-scientist-staging@staging` (the
  `DataScientistStagingAccess` set already exists, unassigned, with `DenyEveryWrite` and no `athena:`
  action), keep `deployment-manager`, and **remove `dev-env-steward`** — a Workload account has no image
  steward. Apply as `awsds-infra-identity`.
- **Retiring the vending policy — Claude edits, user applies:** shrink `PERSONA_VENDING_ACCOUNTS` with
  `SMUS_MEMBERS`, then lift `prevent_destroy` on `awsds-org-project-storage-vending` in
  `terraform-live/development/foundation/persona-vending.tf` in one commit and destroy it in the next
  (the runbook's two-commit rule). The object is referenced **by name** by the permission set, so it goes
  after the assignment, never before.
- **Revoking the share — Claude edits, user applies:** remove `development` from `consumer_accounts` and
  `writer_role_patterns` in `terraform-live/data-governance/data/`; apply as `awsds-infra-data`. Annotate
  the two triples in `docs/AWS_STATE.md`'s grant register as **revoked with a date** — never delete a
  register row.
- **Destroying the consumer slice — user applies:** destroy `terraform-live/development/data/`. It cannot
  be converted: its `data.tf` resolves `AWSReservedSSO_DataScientistAccess_*` with `one()`, which fails at
  plan time as soon as the account carries `DataScientistStagingAccess` instead. The account data CMK
  `alias/awsds-dev-data` goes with it; **Stage 9 creates Staging's CMK under its own name**, so no `dev`
  string survives into the new role.
- **Reading the conversion — Claude:** `./aws/datalake.py` `DL-5`/`DL-13` show no Development consumer and
  no orphan admin; `./aws/deploytargets.py` `DT-8` — *no resource link to Data Governance in a deployment
  target* — becomes answerable for the first time and must pass.

### 3. The rename and the OU move — the two console acts, and the two code sites that key on the name

**Why:** the account's name is not cosmetic here. `identity/sso/locals.tf` resolves the account by the
exact string `Development Account` behind a precondition that fails the plan, and `aws/import-ids.py` maps
the same string. Between the rename and the code edit, the `identity/sso` plan is **expected** to fail;
that is why the two happen in one sitting.

- **Enabling trusted access, if step 0 found it absent — user**, Management, CloudShell as
  `AWS Control Tower Admin`:
  `aws organizations enable-aws-service-access --service-principal account.amazonaws.com`. `PutAccountName`
  on a member requires it. Claude restates `INV-09`'s count afterwards.
- **Renaming the account — user**, Management: console *Organizations → AWS accounts → select the member →
  Actions → Update account name*, or

  ```bash
  aws account put-account-name --account-id <the account> --account-name "Staging Account"
  ```

  **Keep the ` Account` suffix** — it is the vended-name pattern the SSO slice measured. AWS documents up
  to four hours of propagation; a stale name inside that window is not a defect.
- **Re-pointing the two name-keyed sites — Claude, same sitting:** `terraform-live/identity/sso/locals.tf`
  (`accounts` map) and `aws/import-ids.py`; then re-plan `identity/sso/` and expect the precondition to
  pass again.
- **Moving the OU — user**, Control Tower console: *Organization → the account → **Update account** →
  registered OU = `Workloads`*, or the Service Catalog update of the provisioned product with
  `ManagedOrganizationalUnit = Workloads`. **Never `aws organizations move-account`** — that path raises
  `ACCOUNT_MOVED_BETWEEN_OUS` drift and, without auto-enrollment, leaves the old OU's Config-rule controls
  attached.
- **Updating the provisioned product's parameters — user**, same sitting: re-enter `AccountName` as
  `Staging Account` alongside the new OU, then **read the parameters back**. Control Tower documents the
  e-mail field as *not* following an out-of-band change; whether `AccountName` does is not documented. If
  it refuses, record the divergence as a permanent property of the provisioned product — the same treatment
  D32 gives the direct assignment.
- **Checking D32's trigger — Claude:** run `./aws/list-identities.py`. An *account update* is exactly what
  re-creates the direct `AWSAdministratorAccess` assignment (Stage 1b verification (vi)); if it came back,
  it is expected, and the row is restated rather than removed.
- **Re-running the battery — Claude, user-authorized:** `./aws/probes/scp-battery.py --phase ou` with the
  new `staging` token and **`Workloads` expectations**. Two consequences to record rather than discover:
  the account **loses** `DenyAthenaSparkStartSession` (the Sid exists only in the `Interactive` document)
  and **gains** `DenyInteractiveSageMakerSurface` and `DenyDataZoneEntirely`; and `Sandbox Account 1`
  becomes the only Interactive sample the battery has.
- **Closing the Athena Spark gap — Claude edits, user applies:** add `DenyAthenaSparkStartSession` to
  `awsds-org-scp-ou-workloads`. Athena for Spark runs its executors outside any VPC, so a Workload account
  that can start a session has an unproxied internet path in the account that will hold deploy
  credentials. Review `terraform-live/identity/org-policies/POLICIES.md` in the **same sitting** and move
  `EXC-03`'s Athena contrast probe to `Policy Canary`, which is what the battery uses it for.

### 4. The token and the state — migrate the tree from `development/` to `staging/`

**Why:** the folder name is the Terraform state key and the token is every physical name. There is no
migration recipe in this repository, and improvised `state mv` is forbidden by the runbook — so the recipe
is written first, exercised on the smallest slice, and only then applied to the rest. Splitting *migration*
from *token flip* is what keeps each plan readable: the first must produce `No changes`, the second must
produce a short, explainable list of replacements.

- **Writing Recipe E — Claude:** add to [`runbooks/terraform-changes.md`](../runbooks/terraform-changes.md)
  a **Recipe E — moving a slice between folders**: (a) `terraform init` with the old backend so the state
  is cached; (b) `git mv` the folder and regenerate `backend.hcl` for the new bucket and key, **with the
  old token still in the tfvars**; (c) `terraform init -migrate-state`; (d) `terraform plan` must return
  **`No changes`** — that empty plan is the proof of the migration and the gate for anything after it.
- **Creating the new state home — Claude writes, user applies:** `terraform-live/staging/bootstrap/`,
  producing `awsds-staging-tfstate` and `alias/awsds-staging-tfstate` under the existing bootstrap module.
  Add the `staging` rows to `PROFILES`, `ENV_TOKENS` (already present), `ENVIRONMENT_TAGS` and `ZONE_IDS`
  in `backend.py`, and the `staging` slice rows to `scripts/tfhygiene/layers.py`. Keep the `development`
  rows alive until the old bucket is gone — the generator still has to emit the old backend.
- **Migrating each surviving slice — Claude prepares, user applies:** `foundation/` and `probes/` are the
  only slices that survive steps 1 and 2 (`sagemaker/`, `data/` and `egress/` are destroyed by this stage
  or re-cut by 6c). Run Recipe E on each, one session per slice.
- **Flipping the token — Claude edits, user applies:** set `env = "staging"` and
  `environment_tag = "staging"` and read the plan carefully: the VPC, its subnets and the `[P]` S3 and
  DynamoDB **gateway endpoints keep their ids** (in-place tag changes only — this is what preserves
  INT-05's anchors and the lake's `trusted_vpce_ids`), while the security groups and the flow-log group
  **are replaced**. Anything else in the replacement list is a surprise and stops the step.
- **Keeping the CIDR — Claude, documentation only:** the account keeps **10.50.0.0/16**. A VPC CIDR cannot
  be renamed, a rebuild would invalidate the gateway-endpoint ids the lake's bucket policy names (Lesson 3),
  and the reservation the plan held for Staging (**10.40.0.0/16**) is freed for 6c to use.
- **Retiring the old bucket — user applies, last:** migrate `development/bootstrap/`'s own state to the new
  bucket, lift `prevent_destroy` in one commit, empty the versioned bucket by hand (object versions **and**
  delete markers), and destroy it in the next commit — the choreography D19's buckets already used. Only
  then remove the `development` rows from `backend.py` and `layers.py`.
- **Swapping the parity gate — Claude, in the `git mv` commit:** `scripts/check-bootstrap-parity.py` makes
  `development` REQUIRED and `staging` OPTIONAL; the two swap.

### 5. Close the stage — the instruments, the vocabularies and the documents that name the account

**Why:** a topology or role change is the trigger to re-read every instrument in the same sitting
(Lesson 31): a check written for an Interactive Development keeps reporting `pass` about an account that no
longer exists in that role.

- **Re-scoping the instruments — Claude:** drop `awsds-infra-dev` from `studio.py`'s
  `INTERACTIVE_PROFILES` and from `dns-allowlist.py`'s slice list (Staging is headless — retargeting would
  be wrong, removal is right); give `probes.py` a `staging` token with Workloads expectations; rename the
  profile constants in `cicd.py`, `deploytargets.py`, `supplychain.py`, `datalake.py`, `networking.py`,
  `egress.py`, `vpn.py` and `sandboxlake.py`.
- **Editing the four literal provider aliases — Claude:** provider aliases cannot be iterated, so
  `production/foundation/peers.tf`, `production/registry/providers.tf`,
  `data-governance/data/providers.tf` and `data-governance/governance/providers.tf` each carry a
  hand-written `development` alias and matching `for_each` keys. All four change in the same commit as the
  `backend.py` lists (Lesson 14).
- **Writing the new rename instrument — Claude:** `./aws/rename-check.py`, read-only, one report: the
  account's name and OU from Organizations, its permission-set assignments, the domain's RAM shares as seen
  from the member, `list-environment-blueprint-configurations`, the Lake Formation grants naming it, and
  the registry policies that name it. It is the single reading that says whether the conversion is complete.
- **Revising the documents that state the account as a fact — Claude:** `docs/ORGANIZATION.md` (tree, name
  table, assignment table), `docs/AWS_STATE.md` (INV-02, INV-07/A.1, INV-09, the §C rows, the lake, SMUS
  and vending rows, the grant register), `docs/plan/conventions.md` §6 (the `development` subtree retires,
  the `staging` subtree is rewritten to what exists), `terraform-live/README.md`, `docs/GOVERNANCE.md` (the
  consumer list), `docs/SMUS.md` (one associated account, one profile), `README.md`,
  `docs/GENERAL_PLAN.md`'s account map, `docs/plan/integrations.md` (the INT rows in the **Proves** row
  above), `docs/plan/cost-model.md`, and `docs/plan/decisions/` — D17, D18, D20, D21, D22, D26, D35 amended
  in place with a dated line each, and one bullet in `docs/plan/history.md`.
- **Writing the log — user, or Claude on request:** the console acts of steps 1, 3 and 4 with their fields
  and their read-backs.

---

## Deliverables

- An account named `Staging Account`, in the `Workloads` OU, holding `InfrastructureAccess`,
  `DataScientistStagingAccess` and `DeploymentManagerAccess` — and no SMUS association, no blueprint
  configuration, no project profile, no lake share, no resource link, no vending policy.
- `terraform-live/staging/{bootstrap,foundation,probes}/` on `awsds-staging-tfstate`, with
  `terraform-live/development/` gone from the tree and the old bucket destroyed.
- `Recipe E` (folder move) and `Recipe F` (staged `awscc` destroy) in the changes runbook.
- `./aws/rename-check.py`, and every instrument re-scoped to one Interactive account.
- `DenyAthenaSparkStartSession` on the `Workloads` document, with its `POLICIES.md` row.

## Validation

- `./aws/rename-check.py` reports the new name, the `Workloads` OU, three permission sets and **zero**
  DataZone objects.
- `./aws/studio.py` shows one associated account and one project profile; `US-6` passes from the renamed
  account.
- `./aws/datalake.py` `DL-5`/`DL-13` and `./aws/deploytargets.py` `DT-8` pass with no Development row.
- `./aws/probes/scp-battery.py --phase ou` reads the `Workloads` expectation set for the renamed account,
  with the Athena Spark deny exercised.
- `make check` and `make check-docs` green; every surviving slice re-plans `No changes`.

## Cost

Structurally negative and small: the account keeps its VPC (free at rest), loses one project CMK and one
data CMK (**−USD 2/month** at PRICING §2's key rate), and loses nothing else that bills. The new state
bucket is cents. The old bucket's storage disappears with it.

## Risks

- **A stranded `datazone` object.** Mitigated by doing every delete inside `Interactive` and reading the
  member back twice; the recovery, if one survives the move, is a temporary OU move back — expensive and
  avoidable.
- **A `prevent_destroy` met at the wrong moment.** Two objects carry it (the projects bucket, the vending
  policy) and both are handled by the two-commit rule, never by a `-target` improvisation.
- **The state migration losing a slice.** Mitigated by Recipe E's empty-plan gate, one slice per session,
  and the old bucket surviving (versioned) until every migration has produced `No changes`.
- **The provisioned product diverging from the account's name.** Accepted and recorded if it happens; it
  affects nothing this repository resolves, because the code reads Organizations.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
