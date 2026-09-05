# Stage 6b — `Development` becomes `Staging`

| | |
|---|---|
| **Status** | not started — **created 2026-09-05**, revised the same day into the action-checklist format. One account changes role: `Development` (an Interactive member of the SageMaker Unified Studio domain, with a Lake Formation share and a read-write persona) becomes `Staging` (a **Workload** deployment target written only by the pipeline). It is [D21](../decisions/D21-development-account.md)'s own larger branch, pre-written 2026-08-13 and now taken |
| **Prerequisites** | [6a](stage-06a-unified-studio.md) — what is being unwound was built there. **6c is not a prerequisite, but this stage runs FIRST**: see "Why this stage precedes 6c" below |
| **Consumes** | [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D26](../decisions/D26-unified-studio.md), [D32](../decisions/D32-account-factory-sso-user.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | Nothing new crosses an account boundary. What it **retires**: [INT-04](../integrations.md) (merged into INT-07), the Development halves of INT-01/02/12/15/17/18/19, INT-03's third consumer, and [INT-09](../integrations.md)'s premise (a Studio project cloning GitLab), whose peering 6c re-purposes |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, §6's slice
tree) and [`docs/plan/runbooks/terraform-changes.md`](../runbooks/terraform-changes.md) (**Recipe E** —
moving a slice between folders, and **Recipe F** — a staged `awscc` destroy; both were written on
2026-09-05 and are used, not authored, here).*

---

## What this stage changes, and in which account

| Object | Where | Becomes |
|---|---|---|
| 11 blueprint configurations + 11 authorization grants | the member account, `development/sagemaker/` | destroyed **while the account is still in `Interactive`** |
| The `engineering` project profile + its grant | `data-governance/governance/` | destroyed |
| The SMUS account association | the domain, Data Governance | disassociated (console only) |
| `DataScientistAccess`, `DevEnvStewardAccess` | `identity/sso/` | `DataScientistStagingAccess` alone; the steward seat is removed |
| The lake share (2 TBAC triples, 2 resource links, 4 re-grants) | `data-governance/data/` + `development/data/` | revoked, then the consumer slice destroyed |
| `awsds-org-project-storage-vending` | `development/foundation/` | destroyed |
| The account's name and OU | Organizations / Control Tower | `Staging Account`, OU `Workloads` |
| `terraform-live/development/` on `awsds-dev-tfstate` | the tree | `terraform-live/staging/` on `awsds-staging-tfstate` |

**What this stage does NOT do:** it does not touch the network (6c owns it), does not build Staging's
runtime (Stage 9), and creates no data share — D20's Staging is never on the lake share.

## Why this stage precedes 6c

Not because 6c needs it, but because running it second costs two edits instead of one and puts a rename
inside a network cut-over:

- **6c writes the peering map once.** The map in `backend.py` (6c step 3) is authored with `staging`
  already in it. Run in the other order, 6c writes `development` and 6b rewrites both sides of the same
  peering plus the four literal provider aliases a week later.
- **`production/foundation/peers.tf` finds a peer by the tag `awsds-<env>-vpc`.** The token flip (step 4.4)
  renames that tag to `awsds-staging-vpc`; doing it before 6c means the accepter side is authored against
  the final name.
- **6b destroys three slices 6c would otherwise have to reason about** (`sagemaker/`, `data/`, and the
  Interactive surface behind them).

The one object the two stages share is the `Development ↔ Production` peering. It stays exactly as it is
until 6c re-cuts it; nothing in this stage touches a route table.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply`/`destroy` or any AWS write — run **only after the user authorizes that specific action in chat**, with the SSO user / account / permission set stated first |
| **[user]** | console and CloudShell acts (Management holds no CLI profile for this work), `~/.aws/config`, git commits, and every log entry |

## Step numbers are identifiers, not an order

The sequence is six passes. **Passes 1 and 3 are order-critical and pass 1 must complete first**: the
`Workloads` OU denies `datazone:*` (`awsds-org-scp-ou-workloads`, `DenyDataZoneEntirely`), the eleven
blueprint configurations are owned by the **member**, and only the member can delete them. An account moved
to `Workloads` with a configuration still attached can never delete it, and an incomplete configuration
pins its dependents in **both** directions (Lesson 39).

| Pass | What | Slices touched | Applied as |
|---|---|---|---|
| **0** | preflight readings | none | read-only |
| **1** | the SMUS unwind — **inside `Interactive`** | `data-governance/governance/`, `development/sagemaker/` | `awsds-infra-data`, `awsds-infra-dev` |
| **2** | persona swap and lake revocation | `identity/sso/`, `data-governance/data/`, `development/{foundation,data}/` | `awsds-infra-identity`, `awsds-infra-data`, `awsds-infra-dev` |
| **3** | the rename and the OU move | `identity/sso/` (value only) | console + `awsds-infra-identity` |
| **4** | the folder and token migration | every surviving slice | `awsds-infra-dev` → `awsds-infra-staging` |
| **5** | instruments, vocabularies, documents | `aws/`, `scripts/`, `docs/` | — |

---

## To execute

### 0. Preflight — measure what the account holds before anything is removed

**Action:** take four readings and paste them into the stage log. **Why:** every destroy count below is
quoted from a 2026-09-05 snapshot, and a count that disagrees is the difference between a clean destroy and
a stranded object. **Explanation:** a reading that contradicts this file stops the stage rather than
adjusting it — the disagreement is the finding.

- **0.1 — [Claude] Read the SMUS surface**: `./aws/studio.py`. For the Development profile expect `US-3` =
  11 blueprint configurations, `US-4` = both project profiles, **no project**, and no SageMaker AI domain.
  A project here means pass 1 grows a project delete **before** 1.4, and the stage waits for it.
- **0.2 — [Claude] Read the lake surface**: `./aws/datalake.py`. Record the Development rows —
  `DataLakeSettings` admins, the two resource links, the four re-grants, and the two TBAC share triples
  `data-governance/data/` holds for this consumer. These are step 2.3's expected destroy count.
- **0.3 — [Claude] Read the identity surface**: `./aws/list-identities.py`. Record the four permission sets
  assigned (`InfrastructureAccess`, `DataScientistAccess`, `DeploymentManagerAccess`,
  `DevEnvStewardAccess`) and the customer-managed `awsds-org-project-storage-vending` reference.
- **0.4 — [Claude] Read the conversion in one report**: `./aws/rename-check.py` (written 2026-09-05).
  Expect the **BEFORE** verdict — old name, `Interactive`, DataZone objects present, share present. Any
  **MIXED** row before the stage starts is a finding, not a phase.
- **0.5 — [user] Read the organization's two switches**, CloudShell in **Management** as the
  **`AWS Control Tower Admin`** user, permission set `AWSAdministratorAccess` (the `awsds-ctadmin-orgfull-*`
  profiles do not reach Management): is `account.amazonaws.com` in
  `list-aws-service-access-for-organization`, and is the landing zone's **account auto-enrollment** on?
  **[Claude]** writes `aws/cloudshell/management-account-switches.sh` first, on the pattern of the three
  scripts already in that folder.
- **0.6 — [user] Paste the five readings into the stage log's first entry**, so every count below is
  measured rather than quoted.

### 1. Unwind the SMUS surface — while the account is still in `Interactive`

**Action:** delete the project profile, the eleven blueprint configurations and their grants, then
disassociate the account from the domain. **Why:** this is the only window in which the deletes are
permitted (see the ordering note above). **Explanation:** the order inside the pass is profile →
configurations → association → vocabulary, the exact reverse of how 6a built it; each step has a read-back,
because an error and an empty list are different outcomes and only the empty list closes a step.

- **1.1 — [Claude] Remove the `engineering` project profile**: delete `engineering` from
  `local.project_profiles` in `terraform-live/data-governance/governance/locals.tf`, and the `development`
  provider alias and data source with it. **[Claude⚡] Apply as `awsds-infra-data`. Expect exactly
  `2 destroyed`** — the profile and its `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to
  `sso-group-deployment-managers`.
- **1.2 — [Claude⚡] Destroy the eleven configurations and their grants**: set `blueprints_enabled = false`
  in `terraform-live/development/sagemaker/`, apply as `awsds-infra-dev`, **expect `22 destroyed`**. If the
  provider orders grant and configuration wrongly, fall back to **Recipe F** (staged destroy, one `-target`
  per resource type, `plan` between them) — a destroy of a blueprint configuration with a grant attached
  has never been exercised in this estate.
- **1.3 — [Claude] Read the member back**: `aws datazone list-environment-blueprint-configurations` and
  `list-policy-grants` from `awsds-infra-dev` must both return **empty**.
- **1.4 — [user] Disassociate the account**, console, in the **Data Governance** account: *SageMaker Unified
  Studio → domain `awsds-studio` → Account associations → select the member → Disassociate*, typing
  `disassociate` to confirm. There is no API for this, and the documentation lists no prerequisite — which
  is why 1.3 runs first.
- **1.5 — [Claude] Read the association back**: from `awsds-infra-dev`,
  `aws ram get-resource-shares --resource-owner OTHER-ACCOUNTS` shows no DataZone share, and
  `list-environment-blueprint-configurations` now **fails** rather than returning empty — 6a step 1.3's
  proof, in reverse.
- **1.6 — [Claude] Edit the vocabulary in ONE commit**: remove `development` from **both** `SMUS_MEMBERS`
  and `SMUS_ASSOCIATED` in `scripts/tfhygiene/backend.py`, regenerate the tfvars, and re-plan
  `data-governance/governance/` to **`No changes`**. `profiles_enabled` is computed from `SMUS_ASSOCIATED`,
  so editing one list alone would flip the flag and destroy the **`experimentation`** profile too; the
  empty plan is the proof that it did not.
- **1.7 — [Claude⚡] Destroy the rest of the slice**: list and empty `awsds-dev-smus-projects` by hand (no
  project ever wrote to it), remove the module call so the `prevent_destroy` lifecycle block leaves the
  configuration with it, then destroy `terraform-live/development/sagemaker/`. The project CMK
  `alias/awsds-dev-project` enters its deletion window — **record the scheduled date in the log**.
- **1.8 — [Claude] Re-read the estate**: `./aws/studio.py` shows one associated account, one project
  profile, and no Development row anywhere. `US-6` ("datazone reads denied in Workloads") is checked again
  at step 3.6, after the move.

### 2. Make the account read-only — the persona swap and the lake revocation, in the order that locks nobody out

**Action:** replace the read-write data-scientist seat with `DataScientistStagingAccess`, revoke the lake
share from the producer side, and destroy the consumer slice. **Why:** D18 says "Staging — read-only, and
nothing else" and D20 says Staging is never on the lake share; the account holds the opposite of both.
**Explanation:** the order matters twice — an assignment is removed **before** the customer-managed policy
it references by name, and the share is revoked from the **producer** side before the consumer slice that
uses it is destroyed.

- **2.1 — [Claude] Swap the permission set WITHOUT renaming the key**: in
  `terraform-live/identity/sso/locals.tf`, leave the assignment key `data-scientist@development` and the
  `account = "development"` field alone, and change only `set = "data_scientist"` →
  `set = "data_scientist_staging"` (`DataScientistStagingAccess` already exists, unassigned, with
  `DenyEveryWrite` and no `athena:` action). Delete `dev-env-steward@development` — a Workload account has
  no image steward. **Renaming the map key here would change the resource address and destroy/recreate the
  assignment for no reason**; the key is renamed at step 4.6 behind `moved {}` blocks, after the account
  itself is renamed. **[Claude⚡] Apply as `awsds-infra-identity`.**
- **2.2 — [Claude⚡] Retire the vending policy, two commits**: shrink `PERSONA_VENDING_ACCOUNTS` with
  `SMUS_MEMBERS`; then lift `prevent_destroy` on `awsds-org-project-storage-vending` in
  `terraform-live/development/foundation/persona-vending.tf` in one commit and destroy it in the next (the
  runbook's two-commit rule). The object is referenced **by name** by the permission set, so it goes after
  2.1 and never before.
- **2.3 — [Claude⚡] Revoke the share**: remove `development` from `consumer_accounts` and
  `writer_role_patterns` in `terraform-live/data-governance/data/`; apply as `awsds-infra-data`. Annotate
  the two triples in `docs/AWS_STATE.md`'s grant register as **revoked, with the date** — never delete a
  register row.
- **2.4 — [Claude⚡] Destroy the consumer slice**: `terraform-live/development/data/`. It cannot be
  converted — its `data.tf` resolves `AWSReservedSSO_DataScientistAccess_*` with `one()`, which fails at
  plan time the moment 2.1 lands. The account data CMK `alias/awsds-dev-data` goes with it; **Stage 9
  creates Staging's CMK under its own name**, so no `dev` string survives into the new role.
- **2.5 — [Claude] Read the conversion**: `./aws/datalake.py` `DL-5`/`DL-13` show no Development consumer
  and no orphan admin; `./aws/deploytargets.py` `DT-8` — *no resource link to Data Governance in a
  deployment target* — becomes answerable for the first time and must pass.

### 3. Rename the account and move the OU — the two console acts, and the code that keys on the name

**Action:** enable trusted access if absent, rename the account, move it to `Workloads` through Control
Tower, and re-point the two sites that resolve it by name. **Why:** `identity/sso/locals.tf` resolves the
account by the exact string `Development Account` behind a precondition that fails the plan, and
`aws/import-ids.py` maps the same string. **Explanation:** between the rename and the code edit the
`identity/sso` plan is **expected** to fail — which is why both happen in one sitting.

- **3.1 — [user] Enable trusted access, if 0.5 found it absent**, Management, CloudShell as
  `AWS Control Tower Admin` / `AWSAdministratorAccess`:

  ```bash
  aws organizations enable-aws-service-access --service-principal account.amazonaws.com
  ```

  AWS documents this as the prerequisite for using the `--account-id` parameter of the Account Management
  API against a member: management (or delegated-admin) credentials, **all features enabled**, trusted
  access on. Success produces no output. **[Claude]** restates `INV-09`'s count afterwards.
- **3.2 — [user] Rename the account**, Management: *Organizations → AWS accounts → select the member →
  Actions → Update account name*, or

  ```bash
  aws account put-account-name --account-id <the account> --account-name "Staging Account"
  ```

  The caller needs `account:PutAccountName`; the name is 1-50 characters matching `[ -;=?-~]+`; the
  management account cannot pass **its own** id. **Keep the ` Account` suffix** — it is the vended-name
  pattern the SSO slice measured. **A propagation delay is not documented**: read the name back with
  `aws organizations list-accounts` rather than re-issuing the call, and record what the read showed.
- **3.3 — [Claude] Re-point the two name-keyed sites, same sitting**: in
  `terraform-live/identity/sso/locals.tf` change the **value** `development = "Development Account"` to
  `"Staging Account"` (not the key), and update `aws/import-ids.py`. Re-plan `identity/sso/` and expect the
  precondition to pass again with **`No changes`** to the assignments.
- **3.4 — [user] Move the OU**, Control Tower console: *Organization → the account → **Update account** →
  registered OU = `Workloads`*, or the Service Catalog update of the provisioned product with
  `ManagedOrganizationalUnit = Workloads`. **Never `aws organizations move-account`** — that path raises
  `ACCOUNT_MOVED_BETWEEN_OUS` drift and, without auto-enrollment, leaves the old OU's Config-rule controls
  attached.
- **3.5 — [user] Update the provisioned product's parameters, same sitting**: re-enter `AccountName` as
  `Staging Account` alongside the new OU, then **read the parameters back**. Control Tower documents the
  e-mail field as *not* following an out-of-band change; whether `AccountName` does is not documented. If
  it refuses, record the divergence as a permanent property of the provisioned product — the treatment D32
  gives the direct assignment.
- **3.6 — [Claude] Check D32's trigger**: `./aws/list-identities.py`. An *account update* is exactly what
  re-creates the direct `AWSAdministratorAccess` assignment (Stage 1b verification (vi)); if it came back,
  it is **expected**, and the row is restated rather than removed.
- **3.7 — [Claude⚡] Re-run the battery**: `./aws/probes/scp-battery.py --phase ou` with the new `staging`
  token and **`Workloads` expectations**. Two consequences to record rather than discover: the account
  **loses** `DenyAthenaSparkStartSession` (that Sid exists only in the `Interactive` document) and **gains**
  `DenyInteractiveSageMakerSurface` and `DenyDataZoneEntirely`; and `Sandbox Account 1` becomes the only
  Interactive sample the battery has.
- **3.8 — [Claude⚡] Close the Athena Spark gap**: add `DenyAthenaSparkStartSession` to
  `awsds-org-scp-ou-workloads`. The SMUS network-isolation guide states that *"Amazon Athena for Apache
  Spark does not currently support Amazon VPC"* and gives the SCP denying `athena:StartSession` **and**
  `athena:UpdateSession` as the control — so a Workload account that can start a session has an unproxied
  path out of the account that will hold deploy credentials. Keep both actions even though
  `UpdateSession` appears in no API model this project could read: the deny costs nothing and AWS's own
  example carries it. Review
  [`terraform-live/identity/org-policies/POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md)
  in the **same sitting**, and move `EXC-03`'s Athena contrast probe to `Policy Canary`.

### 4. Migrate the tree — `development/` to `staging/`, folder first and token second

**Action:** create the new state home, move each surviving slice with Recipe E, then flip the token.
**Why:** the folder name is the Terraform state key and the token is every physical name. **Explanation:**
splitting *migration* from *token flip* is what keeps each plan readable — the first must produce
`No changes`, the second a short, explainable replacement list. Recipe E was written on 2026-09-05 and is
followed here, not authored.

- **4.1 — [Claude] Fix the address table BEFORE the token flip — the hazard that would replace the VPC**:
  in `scripts/tfhygiene/backend.py`, `CIDRS` is keyed by **account folder** and today reads
  `staging = 10.40.0.0/16`, `development = 10.50.0.0/16`. The moment the folder becomes `staging/`, the
  generated `vpc_cidr` would change and the plan would propose **replacing the VPC**. Set
  `CIDRS["staging"] = "10.50.0.0/16"`, delete the `development` row, and **free `10.40.0.0/16`** — 6c step 0
  consumes the freed block; it does not perform this edit. The account keeps 10.50 because a VPC CIDR is
  immutable and a rebuild would invalidate the `[P]` gateway-endpoint ids the lake's bucket policy names
  (Lesson 3).
- **4.2 — [Claude⚡] Create the new state home**: `terraform-live/staging/bootstrap/`, producing
  `awsds-staging-tfstate` and `alias/awsds-staging-tfstate` from the existing bootstrap module. Add the
  `staging` rows to `PROFILES` and `ZONE_IDS` (`ENV_TOKENS` and `ENVIRONMENT_TAGS` already carry one), and
  the `staging` slice rows to `scripts/tfhygiene/layers.py`. **Keep the `development` rows alive** until
  the old bucket is gone — the generator still has to emit the old backend.
- **4.3 — [Claude⚡] Migrate each surviving slice with Recipe E, one session per slice**: `foundation/` and
  `probes/` are the only ones left (`sagemaker/` and `data/` were destroyed in passes 1-2; `egress/`
  survives and is re-cut by 6c step 5, so it migrates here too). Recipe E's gate is that
  `terraform plan` returns **`No changes`** after `init -migrate-state`; nothing proceeds past a slice that
  does not.
- **4.4 — [Claude⚡] Flip the token**: set `env = "staging"` and `environment_tag = "staging"` and read the
  plan carefully. The VPC, its subnets and the `[P]` S3 and DynamoDB **gateway endpoints keep their ids**
  (in-place tag changes only — this is what preserves INT-05's anchors and the lake's `trusted_vpce_ids`),
  while the security groups and the flow-log group **are replaced**. Anything else in the replacement list
  is a surprise and stops the step.
- **4.5 — [Claude] Re-point the peer lookup in the same commit**: `production/foundation/peers.tf` finds a
  peer by the tag `awsds-<env>-vpc`, which 4.4 renames to `awsds-staging-vpc`. Edit the accepter side and
  the four literal provider aliases (`production/foundation/peers.tf`,
  `production/registry/providers.tf`, `data-governance/data/providers.tf`,
  `data-governance/governance/providers.tf`) together — provider aliases cannot be iterated, so all four
  are hand-written and all four move in one commit with the `backend.py` lists (Lesson 14).
- **4.6 — [Claude⚡] Rename the assignment keys behind `moved {}` blocks**: `data-scientist@development` →
  `data-scientist-staging@staging` and `deployment-manager@development` → `…@staging`, plus the
  `accounts` map key `development` → `staging`. Without `moved {}` these are address changes and Terraform
  destroys and re-creates each assignment; with them the plan reads `0 to add, 0 to change, 0 to destroy`.
- **4.7 — [Claude⚡] Retire the old bucket, last**: migrate `development/bootstrap/`'s own state to the new
  bucket, lift `prevent_destroy` in one commit, empty the versioned bucket by hand (object versions **and**
  delete markers), destroy it in the next commit. Only then remove the `development` rows from
  `backend.py` and `layers.py`.
- **4.8 — [Claude] Swap the parity gate**, in the `git mv` commit: `scripts/check-bootstrap-parity.py`
  makes `development` REQUIRED and `staging` OPTIONAL — the two swap.

### 5. Close the stage — instruments, vocabularies and the documents that state the account as a fact

**Action:** re-scope every instrument and revise every document that names the account. **Why:** a role
change is the trigger to re-read every instrument in the same sitting (Lesson 31) — a check written for an
Interactive Development keeps reporting `pass` about an account that no longer exists in that role.
**Explanation:** two of these are removals rather than retargets, and saying which is which is the step.

- **5.1 — [Claude] Re-scope the instruments**: drop `awsds-infra-dev` from `studio.py`'s
  `INTERACTIVE_PROFILES`, and **remove** the Development slice from `dns-allowlist.py` rather than
  retargeting it (Staging is headless — it resolves nothing a person chose). Give `probes.py` a `staging`
  token with Workloads expectations, and rename the profile constants in `cicd.py`, `deploytargets.py`,
  `supplychain.py`, `datalake.py`, `networking.py`, `egress.py`, `vpn.py` and `sandboxlake.py`.
- **5.2 — [Claude] Run the conversion report**: `./aws/rename-check.py` must now print the **AFTER**
  verdict — new name, `Workloads`, three permission sets, zero DataZone objects, no share, no vending
  policy. A **MIXED** verdict names the object that failed to cross.
- **5.3 — [Claude] Revise the documents that state the account as a fact**: `docs/ORGANIZATION.md` (tree,
  name table, assignment table), `docs/AWS_STATE.md` (`INV-02`, `INV-07`/A.1, `INV-09`, the §C rows, the
  lake, SMUS and vending rows, the grant register), `docs/plan/conventions.md` §6 (the `development`
  subtree retires; the `staging` subtree is rewritten to what exists), `terraform-live/README.md`,
  `docs/GOVERNANCE.md` (the consumer list), `docs/SMUS.md` (one associated account, one project profile),
  `README.md`, `docs/GENERAL_PLAN.md`'s account map, `docs/plan/integrations.md` (the INT rows in the
  **Proves** row above), `docs/plan/cost-model.md`, and `docs/plan/decisions/` — D17, D18, D20, D21, D22,
  D26, D35 amended in place with a dated line each, plus one bullet in `docs/plan/history.md`.
- **5.4 — [user] Write the log**: the console acts of passes 1, 3 and 4 with their fields and read-backs.
  **[Claude]** only on request, in that sitting.

---

## Deliverables

- An account named `Staging Account`, in the `Workloads` OU, holding `InfrastructureAccess`,
  `DataScientistStagingAccess` and `DeploymentManagerAccess` — and no SMUS association, no blueprint
  configuration, no project profile, no lake share, no resource link, no vending policy.
- `terraform-live/staging/{bootstrap,foundation,egress,probes}/` on `awsds-staging-tfstate`, with
  `terraform-live/development/` gone and the old bucket destroyed.
- `CIDRS` holding `staging = 10.50.0.0/16` and **`10.40.0.0/16` free** for 6c.
- `DenyAthenaSparkStartSession` on the `Workloads` document, with its `POLICIES.md` row.
- `aws/cloudshell/management-account-switches.sh`, and every instrument re-scoped to one Interactive
  account.

## Validation

- `./aws/rename-check.py` reports **AFTER**: the new name, the `Workloads` OU, three permission sets and
  **zero** DataZone objects.
- `./aws/studio.py` shows one associated account and one project profile; `US-6` passes from the renamed
  account.
- `./aws/datalake.py` `DL-5`/`DL-13` and `./aws/deploytargets.py` `DT-8` pass with no Development row.
- `./aws/probes/scp-battery.py --phase ou` reads the `Workloads` expectation set, with the Athena Spark
  deny exercised.
- `make check` and `make check-docs` green; every surviving slice re-plans `No changes`.

## Cost

Structurally negative and small: the account keeps its VPC (free at rest), loses one project CMK and one
data CMK (**−USD 2/month** at PRICING §2's key rate), and loses nothing else that bills. The new state
bucket is cents; the old bucket's storage disappears with it.

## Decisions due while executing

1. **Whether the provisioned product's `AccountName` follows the out-of-band rename** (3.5). Not
   documented. If it refuses, the divergence is recorded as permanent — the code reads Organizations, not
   Service Catalog.
2. **Whether `athena:UpdateSession` stays in the new Sid** (3.8). Recommended **yes**, matching AWS's own
   example, even though the action appears in no API model this project could read.

## Verifications to answer while executing

1. Does a blueprint configuration with an attached grant destroy in one plan, or does it need Recipe F?
   (1.2 — never exercised in this estate.)
2. Does `list-environment-blueprint-configurations` fail rather than return empty after disassociation?
   (1.5 — 6a step 1.3's proof in reverse.)
3. Does the OU move through Control Tower re-baseline the account by itself, or does it depend on account
   auto-enrollment? (0.5 + 3.4.)
4. Does the direct `AWSAdministratorAccess` assignment return after the account update? (3.6, D32.)

## Risks

- **A stranded `datazone` object.** Mitigated by doing every delete inside `Interactive` and reading the
  member back twice; the recovery, if one survives the move, is a temporary OU move back — expensive and
  avoidable.
- **A `prevent_destroy` met at the wrong moment.** Two objects carry it (the projects bucket, the vending
  policy); both are handled by the two-commit rule, never by a `-target` improvisation.
- **The state migration losing a slice.** Mitigated by Recipe E's empty-plan gate, one slice per session,
  and the old bucket surviving (versioned) until every migration has produced `No changes`.
- **A CIDR change smuggled in by the folder rename.** Closed by step 4.1, which edits the address table
  *before* the token flip; the replacement list at 4.4 is the check that it worked.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
