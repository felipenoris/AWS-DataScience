# Stage 6b — `Development` becomes `Staging`

| | |
|---|---|
| **Status** | **PASS 0 COMPLETE — 0.1-0.5a 2026-09-05, 0.5b 2026-09-06**; nothing else started. Pass 0's last reading found **account auto-enrollment ON**, against this file's own prediction, and struck one of step 3.4's two reasons. **Created 2026-09-05**, revised the same day into the action-checklist format, then corrected against the code and against pass 0's own readings in the preparation sitting — the corrections are marked in place and the sitting is [logged](../../log/log-stage-06b-development-becomes-staging.md). One account changes role: `Development` (an Interactive member of the SageMaker Unified Studio domain, with a Lake Formation share and a read-write persona) becomes `Staging` (a **Workload** deployment target written only by the pipeline). It is [D21](../decisions/D21-development-account.md)'s own larger branch, pre-written 2026-08-13 and now taken |
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
| The `DataScientistAccess` and `DevEnvStewardAccess` **assignments** — the sets themselves survive on other accounts | `identity/sso/` | `DataScientistStagingAccess` alone; the steward seat is removed |
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
| **0** | preflight readings — **DONE** (0.1-0.5a 2026-09-05, 0.5b 2026-09-06) | none | read-only |
| **1** | the SMUS unwind — **inside `Interactive`** | `data-governance/governance/`, `development/sagemaker/` — **and `scripts/tfhygiene/backend.py`**, whose vocabulary edit is what flips the flag (1.2/1.6) | `awsds-infra-data`, `awsds-infra-dev` |
| **2** | persona swap and lake revocation | `identity/sso/`, `data-governance/data/`, `development/{foundation,data}/` | `awsds-infra-identity`, `awsds-infra-data`, `awsds-infra-dev` |
| **3** | the rename and the OU move | `identity/sso/` (value only), `identity/org-policies/` (3.8's new Sid), `aws/probes/` (3.7's token) | console + `awsds-infra-identity` |
| **4** | the folder and token migration | every surviving slice | `awsds-infra-dev` → `awsds-infra-staging` |
| **5** | instruments, vocabularies, documents | `aws/`, `scripts/`, `docs/` | — |

---

## To execute

### 0. Preflight — measure what the account holds before anything is removed

**Action:** take the readings and paste them into the stage log. **Why:** every destroy count below is
quoted from a snapshot, and a count that disagrees is the difference between a clean destroy and a
stranded object. **Explanation:** a reading that contradicts this file stops the stage rather than
adjusting it — the disagreement is the finding.

> **PASS 0 IS COMPLETE** — 0.1-0.5a on 2026-09-05 as the infrastructure user through
> `InfrastructureAccess`, 0.5b on 2026-09-06 from CloudShell in Management. Every reading below now carries
> what it *measured*, so the numbers in passes 1-4 are dated evidence rather than expectations, and **two
> of the readings contradicted this file** (0.3's count, 0.5b's switch). The readings are in
> [`log-stage-06b-development-becomes-staging.md`](../../log/log-stage-06b-development-becomes-staging.md);
> what follows is only what each one *decides*.

- **0.1 — [Claude] Read the SMUS surface**: `./aws/studio.py`. For the Development profile expect `US-3` =
  11 blueprint configurations, `US-4` = both project profiles, **no project**, and no SageMaker AI domain.
  A project here means pass 1 grows a project delete **before** 1.4, and the stage waits for it.
  **MEASURED 2026-09-05, `0 check(s) FAILED`: exactly that.** `US-8` reads *"no blueprint-provisioned role
  exists yet — the check is unexercised here"*, which is the no-project reading stated from the other side.
  **Pass 1 needs no project delete.**
- **0.2 — [Claude] Read the lake surface**: `./aws/datalake.py`. Record the Development rows —
  `DataLakeSettings` admins, the two resource links, the four re-grants, and the two TBAC share triples
  `data-governance/data/` holds for this consumer. These are step 2.3's expected destroy count.
  **MEASURED 2026-09-05, `0 check(s) FAILED`:** two resource links (`curated`, `raw`); `DL-13` = **the
  `InfrastructureAccess` seat alone** — no service-appointed Lake Formation admin in this account, unlike
  Sandbox, so `OQ 24` does not reach the conversion; `DL-5` = `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE`.
  - **The four re-grants are NOT in `datalake.py`** — it has no section for consumer-side permissions, and
    the stage said "record them" without saying from where. Read them directly:
    `aws lakeformation list-permissions --profile awsds-infra-dev`. **Measured: 6 permissions, of which 4
    name `AWSReservedSSO_DataScientistAccess_*`** (two `DESCRIBE` on `Database`, two on `LFTagPolicy`) and
    2 name the `InfrastructureAccess` role. **The four are step 2.4's expected loss**; the two
    Infrastructure ones belong to the local databases and go with the slice.
- **0.3 — [Claude] Read the identity surface**: `./aws/list-identities.py`. Record the permission sets
  assigned and the customer-managed `awsds-org-project-storage-vending` reference.
  **MEASURED 2026-09-05, and the count in this step was wrong: the account carries SEVEN assignments, not
  four.** Four are this project's personas — `InfrastructureAccess`, `DataScientistAccess`,
  `DeploymentManagerAccess`, `DevEnvStewardAccess`, each to its `sso-group-*` — and **three are the landing
  zone's**, identical in every governed account: `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins`,
  `AWSPowerUserAccess` → `AWSSecurityAuditPowerUsers`, `AWSReadOnlyAccess` → `AWSSecurityAuditors`.
  **This stage touches none of the three**, so the account ends at **six** assignments, three of them the
  project's — which is what the Deliverables and Validation now say instead of "three permission sets".
  - **No direct `AWSAdministratorAccess` assignment today** — 1b step 5.1's removal is still holding. That
    is what makes step 3.6 a real question: the account update is exactly the event that may re-create it,
    and the negative baseline is what makes the return detectable.
- **0.4 — [Claude] Read the conversion in one report**: `./aws/rename-check.py` (written 2026-09-05).
  Expect the **BEFORE** verdict — old name, `Interactive`, DataZone objects present, share present. Any
  **MIXED** row before the stage starts is a finding, not a phase.
  **MEASURED 2026-09-05 — and the first run found three faults in the instrument, not in the estate.**
  (i) **RC-6 could never have answered**: `list-permissions --principal <account>` without `--resource` is
  refused — *"Resource is mandatory if Principal is set in the input"* — so it returned `(call failed)` in
  the BEFORE state and would have returned it identically in the AFTER one (Lesson 13). It now lists the
  catalog and matches client-side, and reads **2**: the two TBAC triples. (ii) **RC-5 failed on the
  untouched estate**, against the file's own promise that everything notes before the stage runs; it had no
  BEFORE branch, and what makes the same reading a *finding* is the account having already been renamed or
  moved while still holding the two sets. (iii) **RC-4 reported three RAM shares as one question** — the
  `DataZone-*` share goes at step 1, the two `LakeFormation-V4-*` shares at 2.3 — now split into
  **RC-4 / RC-4b / RC-4c** so a mid-stage reading names the step that clears it.
  **After the fixes: six notes, `0 check(s) FAILED`** — the clean BEFORE verdict this step asked for.
- **0.5 — Read the organization's two switches — with the two instruments that already read them.**
  This step used to open by writing `aws/cloudshell/management-account-switches.sh`. **It does not, and
  that is a finding of the 2026-09-05 preparation sitting**: both switches were already being read, one
  per instrument, and a third script would have been a second copy of two readings that exist — the
  divergence Lesson 33 describes, bought for nothing. What the two instruments lacked was not the call but
  the **interpretation**, and that is what was added to each.
  - **0.5a — [Claude] `account.amazonaws.com` trusted access**: `./aws/org-trusted-access-services.py`,
    from the laptop as `awsds-infra-identity`. Section 1 lists every principal and, since 2026-09-05,
    names this one as a **switch** and says what its absence costs: it is the prerequisite for passing
    `--account-id` to the Account Management API, which is how a **member** account is renamed (step 3.2).
    **No CloudShell session is needed for this half** — Organizations reads answer from Identity, and this
    exact call was measured answering there on 2026-08-12. **MEASURED 2026-09-05: `account.amazonaws.com`
    is ABSENT.** Nine principals hold trusted access (`access-analyzer`, `cloudtrail`, `config`,
    `controltower`, `iam`, `member.org.stacksets.cloudformation`, `ram`, `securityhub`, `sso`) and Account
    Management is not one of them — **so step 3.1 is a real step, not a conditional one**.
  - **0.5b — [user] account auto-enrollment**: `./aws/cloudshell/management-landing-zone-drift.sh`,
    CloudShell in **Management** as the **`AWS Control Tower Admin`** user, permission set
    `AWSAdministratorAccess` (the `awsds-ctadmin-orgfull-*` profiles do not reach Management). Its
    section 2 has printed `remediationTypes` since its first run; since 2026-09-05 it also says what the
    value decides. `INHERITANCE_DRIFT` present = Control Tower re-baselines an account moved with the
    Organizations API; absent = a hand move leaves the **source** OU's baseline and controls attached and
    raises inheritance drift. The feature needs landing zone 3.1 or later; this one is 4.0.
    **MEASURED 2026-09-06, from CloudShell in Management: `remediationTypes: INHERITANCE_DRIFT` —
    AUTO-ENROLLMENT IS ON**, and this step predicted the opposite ("absent — the default, and the expected
    reading here"). **The value was already in the repository**: `INV-17` has carried it since 2026-08-16,
    unread as a switch because nothing had named it one. That is what `docs/AWS_STATE.md` exists to
    prevent, and the prediction was written without consulting it — the reading cost nothing, the
    prediction would have cost step 3.4's reasoning.
    The same run re-confirmed the rest of `INV-17` unchanged: `ACTIVE`, 4.0 = latest, `IN_SYNC`, and
    **one operation ever — `CREATE`/`SUCCEEDED`**, so the landing zone still has not re-run since the
    Stage 2 delegation, and section 5 still reads the resource policy `PRESENT` with its condition on two
    statements.
  - **What neither reading changes: step 3.4 — but one of its two reasons is now void.** Auto-enrollment
    does **not** create, modify or terminate the Account Factory **provisioned product**, and does **not**
    prevent `Moved member account` drift when the two OUs differ in configuration — which `Interactive` and
    `Workloads` do. Those two still make the Control Tower `Update account` path the supported one. What
    the measurement **removes** is 3.4's second clause: with the switch ON, an Organizations move would no
    longer strand the source OU's Config-rule controls. The conclusion survives its own justification
    shrinking, which is the only reason it is worth writing down.
- **0.6 — [user] Paste the five readings into the stage log's first entry**, so every count below is
  measured rather than quoted.

### 1. Unwind the SMUS surface — while the account is still in `Interactive`

**Action:** delete the project profile, the eleven blueprint configurations and their grants, then
disassociate the account from the domain. **Why:** this is the only window in which the deletes are
permitted (see the ordering note above). **Explanation:** the order inside the pass is profile →
configurations → association → vocabulary, the exact reverse of how 6a built it; each step has a read-back,
because an error and an empty list are different outcomes and only the empty list closes a step.

- **1.1 — DONE 2026-09-06.** Applied as `awsds-infra-data`: **`0 to add, 0 to change, 2 to destroy`**,
  exactly the two the step named —
  `awscc_datazone_policy_grant.create_project_from_profile["engineering"]` and
  `awscc_datazone_project_profile.this["engineering"]` — re-plan **`No changes`**, and the domain now
  lists **one** project profile (`experimentation`, `ENABLED`) with **one**
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant, to the data-scientists group. Three comments the removal
  invalidated were corrected in the same commit: `providers.tf`'s "TWO ALIASES", `data.tf`'s "member
  accounts" plural, and `locals.tf`'s "WHY THESE TWO GROUPS" — the last of which had itself predicted this
  removal as *"the expected outcome, not a regression"*.
  - **And `studio.py`'s `US-4` went red the moment the apply landed** — it asserted the *two*-profile
    shape, so it now read `missing engineering`. Re-scoped in the same sitting to expect
    `experimentation` **alone**, with `engineering` kept as a `RETIRED_PROFILE_NAMES` entry so its
    **return** is the failure rather than an unknown name: a check that only knows what it expects cannot
    report what it found. `0 check(s) FAILED` after the fix. **This is the third instrument that pass 5
    would have re-scoped four passes too late** (the probe token at 3.7 was the second) — see the note on
    pass 5.
- **1.1 — [Claude] Remove the `engineering` project profile — four sites in three files** (enumerated
  2026-09-05, because "and the provider alias with it" hides one): the `engineering` key in
  `local.project_profiles` **and** the `development` row of `local.member_account_ids`
  (`locals.tf`), `data.aws_caller_identity.development` (`data.tf`), and the `aws.development` provider
  alias (`providers.tf`). They come out together — the data source is the alias's only consumer and
  `member_account_ids` is the profile's. **[Claude⚡] Apply as `awsds-infra-data`. Expect exactly
  `2 destroyed`** — the profile and its `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to
  `sso-group-deployment-managers`; the two removals above are a data source and a provider, which have no
  plan line of their own. **This precedes 1.2's vocabulary edit**, which is what removes the `members` map
  row those sites read.
- **1.2 — DONE 2026-09-06.** Applied as `awsds-infra-dev`: **`0 to add, 1 to change, 22 to destroy`** —
  the count this step was corrected to predict, and the composition read out of the saved plan before
  applying: **11 × `awscc_datazone_environment_blueprint_configuration`** and **11 ×
  `awscc_datazone_policy_grant`** deleted, **1 × `aws_kms_key` updated**, namely
  `module.sagemaker_prereqs.module.project_key.aws_kms_key.this`. One apply, in one plan — **Recipe F was
  not needed**, which answers this stage's verification 1: the provider orders the grant before its
  configuration by itself. Re-plan **`No changes`**.
- **1.2 — [Claude⚡] Destroy the eleven configurations and their grants — and the edit that does it is
  1.6's, taken here.** *Corrected 2026-09-05 while preparing the stage; this step used to read "set
  `blueprints_enabled = false` in `terraform-live/development/sagemaker/`", which names a value **nothing
  in that folder owns**.* `blueprints_enabled` is **generated**: `scripts/tfhygiene/backend.py` emits it as
  `account in SMUS_ASSOCIATED`, `slices.py`'s `prepare()` re-runs `gen-tfvars.py` before **every** `init`,
  and `terraform.auto.tfvars` is git-ignored — so a hand-edited flag is overwritten by the very command
  that would consume it. **Do 1.6's vocabulary edit first** (both lists, one commit), regenerate, then
  apply as `awsds-infra-dev`.
  - **Expect `1 to change, 22 to destroy`, not `22 destroyed`.** The 22 are the eleven configurations and
    their eleven grants. The **1** is the project CMK: `blueprints_enabled = false` also nulls
    `domain_execution_role_arn`, `domain_id` and `root_domain_unit_id` (this slice's `main.tf` gates all
    three on the flag), and `sagemaker-prereqs`' `kms.tf` drops the domain execution role from
    `AllowKmsKeyUsageForSageMakerDomain` and every statement it filters with `if var.domain_id != null`.
    The policy is inline on `aws_kms_key.this`, so it is **one in-place update** to
    `module.sagemaker_prereqs.module.project_key.aws_kms_key.this` — harmless, because 1.7 destroys that
    key anyway, and worth writing down because this stage stops on a plan it did not predict.
  - If the provider orders grant and configuration wrongly, fall back to **Recipe F** (staged destroy, one
    `-target` per resource type, `plan` between them) — a destroy of a blueprint configuration with a grant
    attached has never been exercised in this estate.
- **1.3 — DONE 2026-09-06, and this step asked the second call for an answer it cannot give.**
  `list-environment-blueprint-configurations` from `awsds-infra-dev` returns **0 items** — empty, and
  *succeeding*, which is the association still being in place. But `list-policy-grants` on the grant's own
  entity (`ENVIRONMENT_BLUEPRINT_CONFIGURATION`, identified `<account>:<blueprintId>`) **cannot return
  empty**: with the configuration destroyed it raises
  `ValidationException: Environment Blueprint Configuration with id: … does not exist in account: …`.
  An error and an empty list are different outcomes and only one of them was available here — the grants
  `for_each` rides the configurations, so the entity the grant hangs off is gone with it. **Read the
  error, not an empty list**; the empty list belongs to the *first* call only.
- **1.3 — [Claude] Read the member back**: `aws datazone list-environment-blueprint-configurations` and
  `list-policy-grants` from `awsds-infra-dev`.
- **1.4 — [user] Disassociate the account**, console. **Sign in as the *Infrastructure User*, account
  **Data Governance**, permission set **`InfrastructureAccess`** — the same identity that made the
  association, recorded verbatim in [6a's log](../../log/log-stage-06a-unified-studio.md) for 2026-08-21:
  *"Login AWS Console as Infrastructure User -> Data Governance Account -> InfrastructureAccess -> Amazon
  DataZone -> View Domains -> `awsds-studio` -> Account Associations"*. **`GovernanceManagerAccess` cannot
  do it** despite owning that account's governance surface: its `datazone` actions are subscription-shaped
  (`AcceptSubscriptionRequest`, `Create/DeleteProjectMembership`, `Get*`, `List*`), and an association is
  not a subscription.
  - **Two front doors to the same object**: *SageMaker Unified Studio → domain `awsds-studio` → Account
    associations*, or the **Amazon DataZone** console → *View Domains → `awsds-studio` → Account
    Associations*. The second is the one 6a actually walked; either lands on the member row. Select the
    member → **Disassociate**, typing `disassociate` to confirm. There is no API for this, and the
    documentation lists no prerequisite — which is why 1.3 runs first.
- **1.5 — DONE 2026-09-06, both halves.** `list-environment-blueprint-configurations` from the member
  now raises **`UnauthorizedException: Unauthorized`** — it fails rather than returning empty, which
  **answers this stage's verification 2** and is 6a step 1.3's proof exactly in reverse. And the RAM
  listing is down to the **two `LakeFormation-V4-*` shares, both `ACTIVE`**: the
  `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` share went with the disassociation. `./aws/rename-check.py` turns
  **RC-3 and RC-4 to `pass`** ("no domain visible - the association is gone", "no DataZone share held - the
  disassociation has landed") with RC-4b still noting the lake's two — **which is the whole point of having
  split them**: unsplit, RC-4 would still be reporting *"the console disassociation has not run"* about a
  step that had just run.
  - **`studio.py` needed a third state, and got one.** Its two "nothing here" notes read *"correct **before**
    this account's association"* — green, and describing the wrong side of the event: an operator debugging
    an incident would be told the association is *pending* when it was *retired*. Added
    `RETIRED_MEMBER_PROFILES` — a member whose association was removed on purpose, whose OU has not changed
    yet, so `datazone:*` is not denied and it is not headless either. Both notes now say what happened, and
    the row leaves with the profile rename at 5.1. **`0 check(s) FAILED`.**
- **1.5 — [Claude] Read the association back**: from `awsds-infra-dev`,
  `aws ram get-resource-shares --resource-owner OTHER-ACCOUNTS` shows no DataZone share, and
  `list-environment-blueprint-configurations` now **fails** rather than returning empty — 6a step 1.3's
  proof, in reverse. **The account holds THREE shares, from two different steps (measured 2026-09-05)**:
  the `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` one is this step's, and the two `LakeFormation-V4-*` are the
  lake's and are **expected to survive until 2.3**. Read `RC-4` and `RC-4b` rather than a share count —
  "three became two" is the success here, and a bare count would read like a failed disassociation.
- **1.6 — [Claude] The vocabulary edit, and the proof it cost nothing else. PERFORMED AT 1.2** (the
  numbers are identifiers, not an order): remove `development` from **both** `SMUS_MEMBERS` and
  `SMUS_ASSOCIATED` in `scripts/tfhygiene/backend.py`, regenerate the tfvars, and re-plan
  `data-governance/governance/` to **`No changes`**. **DONE 2026-09-06 — the governance re-plan is
  `No changes`, so `profiles_enabled` did not flip and `experimentation` survived.** `profiles_enabled` is
  `set(SMUS_MEMBERS) <= set(SMUS_ASSOCIATED)`, so editing one list alone flips it false and destroys the
  **`experimentation`** profile too; the empty plan is the proof that it did not. What is left at *this*
  point in the pass is that re-plan, taken after 1.5.
  - **Two side effects of the same edit, both by design and neither obvious from the diff.**
    (i) **AVOIDED, on the vocabulary's own instruction (2026-09-06).** `PERSONA_VENDING_ACCOUNTS` is
    derived as `list(SMUS_MEMBERS)`, so this edit would have dropped `persona_vending_policy_name` from
    `development/foundation/`'s tfvars and left that slice carrying a **destroy blocked by
    `prevent_destroy`** for a whole pass. But the comment above that constant already says what to do when
    the two lists diverge — *"THIS LIST FOLLOWS THE ASSIGNMENTS, not the members"* — and they diverge
    exactly here, because `DataScientistAccess` stays assigned until 2.1. So the derivation was replaced by
    the literal `["sandbox", "development"]` for the window, with the reason and its expiry in the comment.
    **Measured: `development/foundation/` re-plans `No changes`.** Step 2.2 restores the derivation.
    (ii) `SMUS_ASSOCIATED` briefly disagrees with AWS: the console association still exists until 1.4. The
    list's operative meaning is *"this member should carry blueprint configurations"*, and 6b is the one
    pass where that separates from *"is associated"* — necessarily, since the configurations must go
    **before** the association does.
- **1.7 — DONE 2026-09-06.** **`0 added, 0 changed, 14 destroyed`**, re-plan `No changes`: the two service
  roles and their attachments, the D13 boundary policy, the project CMK and its alias, the
  `/awsds/dev/studio` log group, and the projects bucket with its five configuration resources. **Nothing
  in the plan was anything but a delete.** The bucket needed no emptying — `list-object-versions` returned
  **0 versions and 0 delete markers**, which is 0.1's "no project" seen a third way. The project CMK
  `alias/awsds-dev-project` is `PendingDeletion` with **`DeletionDate` 2026-10-06**; the alias and the
  bucket are gone (`404` on `head-bucket`).
  - **The two-commit shape does not survive this repository's own gates, and that is worth knowing before
    the next whole-slice teardown.** With the module call removed, the slice's remaining declarations are
    orphans — three `terraform_remote_state` data sources and one variable — and **tflint fails the commit**
    on `terraform_unused_declarations`. So "the configuration that permits the destroy" is **not a
    committable state** here. The runbook's two-commit rule is for lifting `prevent_destroy` on a resource
    that *stays*; a whole-slice teardown applies from the working tree and commits the **end** state: the
    folder deleted, its `layers.py` row with it.
  - **Same sitting, because the rule says so**: `docs/NETWORK.md`'s row for the two `sagemaker/` slices
    loses this one, and `terraform-live/README.md`'s "applied twice, so the two accounts cannot drift"
    becomes a dated past tense. `docs/plan/conventions.md` §6, `D21` and `INT-15` still name the slice and
    are **5.3's**, not this step's.
- **1.7 — [Claude⚡] Destroy the rest of the slice**: list and empty `awsds-dev-smus-projects` by hand,
  remove the module call so the `prevent_destroy` lifecycle block leaves the configuration with it, then
  destroy `terraform-live/development/sagemaker/`. **MEASURED 2026-09-05: the bucket is empty** —
  `list-objects-v2` returns no `Contents` at all, which is 0.1's "no project" seen from the storage side.
  Still list it rather than assuming: the bucket is versioned, so **delete markers and non-current versions
  are a separate listing** (`list-object-versions`) and they are what a destroy actually trips on. The project CMK
  `alias/awsds-dev-project` enters its deletion window — **record the scheduled date in the log**.
- **1.8 — DONE 2026-09-06, and it closes pass 1.** `./aws/studio.py`: **`0 check(s) FAILED`**, one
  associated account, `US-4` `pass` at one project profile, and every row about this account naming the
  **retirement** rather than a pending association. `US-8`'s note lost the word *"yet"* in the same
  sitting — with the two service roles and the boundary destroyed at 1.7, no blueprint-provisioned role
  will ever appear here, and a note saying one has not appeared *yet* is a check pointing at a future that
  is not coming.
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

- **2.1 — DONE 2026-09-06.** Applied as `awsds-infra-identity`: **`1 added, 0 changed, 2 destroyed`** —
  `data-scientist@development` **replaced** (the permission-set ARN is a forced replacement; the map key,
  and therefore the resource address, is untouched) and `dev-env-steward@development` deleted. Re-plan
  `No changes`. **The account now carries exactly six permission sets** — `DataScientistStagingAccess`,
  `DeploymentManagerAccess`, `InfrastructureAccess`, beside the landing zone's three — which is the count
  0.3 corrected this stage to expect.
- **2.1 — [Claude] Swap the permission set WITHOUT renaming the key**: in
  `terraform-live/identity/sso/locals.tf`, leave the assignment key `data-scientist@development` and the
  `account = "development"` field alone, and change only `set = "data_scientist"` →
  `set = "data_scientist_staging"` (`DataScientistStagingAccess` already exists, unassigned, with
  `DenyEveryWrite` and no `athena:` action). Delete `dev-env-steward@development`. **Renaming the map key
  here would change the resource address and destroy/recreate the assignment for no reason**; the key is
  renamed at step 4.6 behind `moved {}` blocks, after the account itself is renamed.
  **[Claude⚡] Apply as `awsds-infra-identity`.**
  - **Why the steward seat goes, corrected 2026-09-05.** This step used to say *"a Workload account has no
    image steward"*, and the estate contradicts it: **Production is a Workload account and holds
    `DevEnvStewardAccess` today**. The reason is narrower and it is D14's — the steward curates **images**,
    the registry is ECR **in Production**, and Staging has no registry to steward.
  - **Both permission sets survive the stage**: `DataScientistAccess` stays on Sandbox,
    `DevEnvStewardAccess` on Sandbox and Production. What is deleted here is two *assignments*, never a
    set — which is also why nothing in `identity/sso/`'s permission-set half changes.
- **2.2 — DONE 2026-09-06, in the two commits the runbook asks for.** Commit 1 lifted `prevent_destroy`
  and the plan after it read **`No changes`** — which is the point of splitting it: "the guard came off" is
  a reviewable act with no side effect. Commit 2 removed the object, its variable and the derivation's
  literal together, and applied **`0 added, 0 changed, 1 destroyed`**; re-plan `No changes`.
  - **The variable is `nullable = false` with no default**, so the intermediate state that step 2.2 used to
    imply — the resource still declared while the tfvar stops being emitted — is not a state Terraform will
    even load: it fails with *no value for required variable*. That is why the resource, the variable and
    the `PERSONA_VENDING_ACCOUNTS` restoration are **one** commit, and only the guard is its own.
  - **Read back in both accounts**: the policy is gone from this one and **still present in Sandbox**,
    whose `DataScientistAccess` still references it by name. That pair is the check — a per-account object
    removed from the wrong account is a provisioning failure nobody is watching.
- **2.2 — [Claude⚡] Retire the vending policy, two commits.** **Restore the derivation first**:
  `PERSONA_VENDING_ACCOUNTS` is the literal `["sandbox", "development"]` since 1.2 (see 1.6's side effect
  (i)), and it goes back to `list(SMUS_MEMBERS)` here — after 2.1 has removed the assignment that made the
  literal necessary. That edit is what drops `persona_vending_policy_name` from the slice's tfvars, so it
  and the guard belong in the same pass: lift `prevent_destroy` on
  `awsds-org-project-storage-vending` in `terraform-live/development/foundation/persona-vending.tf` in one
  commit and destroy it in the next (the runbook's two-commit rule). The object is referenced **by name**
  by the permission set, so it goes after 2.1 and never before.
- **2.3 — DONE 2026-09-06.** Applied as `awsds-infra-data`: **`0 added, 6 changed, 2 destroyed`** — and
  the shape is the one this step was corrected to predict. The **2 destroyed** are the TBAC triples
  (`share_databases["development"]`, `share_tables["development"]`); the **6 changed** are the **five
  bucket policies and the lake's data CMK key policy**, because the account's root principal and its S3
  gateway endpoint leave `trusted_vpce_ids`. Re-plan `No changes`. `list-permissions` naming that account
  went from **2 to 0**. Six register rows in `docs/AWS_STATE.md` annotated **REVOKED 2026-09-06**, none
  deleted.
- **2.3 — [Claude⚡] Revoke the share**: remove `development` from `consumer_accounts` and
  `writer_role_patterns` in `terraform-live/data-governance/data/`; apply as `awsds-infra-data`. Annotate
  the two triples in `docs/AWS_STATE.md`'s grant register as **revoked, with the date** — never delete a
  register row.
  - **This apply is not only grants: it rewrites the lake's BUCKET POLICIES** (read 2026-09-06).
    `local.consumer_vpce_ids` is built by iterating `data.terraform_remote_state.consumer_foundation`,
    which is keyed by `consumer_accounts` — so dropping the row also drops **this account's S3 gateway
    endpoint id** out of `local.trusted_vpce_ids`, which is INT-05's `aws:SourceVpce` allow-list in
    `buckets.tf`. Expect bucket-policy updates in the plan and read them: the perimeter narrowing is
    correct and intended, but it is a **different kind of change** from a grant revocation and it is the
    one that could lock out a principal nobody was thinking about.
- **2.4 — DONE 2026-09-06.** **`0 added, 0 changed, 5 destroyed`**, state empty afterwards, folder and
  `layers.py` row removed. Three things measured rather than assumed:
  - **The blocker was the missing VARIABLE, not the missing role.** This step said the slice "cannot be
    converted — its `data.tf` resolves `AWSReservedSSO_DataScientistAccess_*` with `one()`, which fails at
    plan time the moment 2.1 lands". **`one()` returns null on an empty collection** and errors only on two
    or more, so 2.1 would have produced a silent null, not a failure. What actually stops the slice is 2.3
    dropping the account from `DATA_CONSUMERS`: the `lake` variable is `nullable = false` with no default
    and stops being emitted, so Terraform cannot **load** the slice. The configuration was stripped, as at
    1.7.
  - **The four Lake Formation re-grants were gone before the apply reached them** — the plan carried
    5 deletes, not 9, and `list-permissions` in the account reads **0** afterwards. They went with the
    resource-link databases and the share, not by a separate revocation. *A first reading of the plan
    guessed an orphan; the measurement says there is none.*
  - **Destroying `aws_lakeformation_data_lake_settings` is a RESET, not a deletion.** The account came back
    with `CROSS_ACCOUNT_VERSION=1` and an **empty administrator list**, which read as `DL-5` and `DL-13`
    failing until `datalake.py` was re-scoped (below). `DL-6` did **not** revert — no `IAMAllowedPrincipals`
    default returned.
- **2.5 — DONE 2026-09-06.** `./aws/datalake.py` **`0 check(s) FAILED`** with `DL-7` at **2 resource
  links** (from 4, both survivors Sandbox's); `./aws/rename-check.py` turns **RC-5 and RC-6 to `pass`** —
  the six permission sets and **no** Lake Formation grant naming the account — leaving only RC-1 and RC-2,
  which are pass 3's console acts. **`datalake.py` was the fifth instrument to need its scope moved at the
  step that moved it** rather than at 5.1: `CONSUMER_PROFILES` is now one profile, with the reset above
  written into the comment so the next reader does not re-diagnose it as drift.
- **2.4 — [Claude⚡] Destroy the consumer slice**: `terraform-live/development/data/`. It cannot be
  converted — its `data.tf` resolves `AWSReservedSSO_DataScientistAccess_*` with `one()`, which fails at
  plan time the moment 2.1 lands. The account data CMK `alias/awsds-dev-data` goes with it; **Stage 9
  creates Staging's CMK under its own name**, so no `dev` string survives into the new role.
- **2.5 — [Claude] Read the conversion**: `./aws/datalake.py` `DL-7`'s resource-link count falls from
  **4 to 2** (both survivors Sandbox's) and `DL-5`/`DL-13` show no Development consumer and no orphan
  admin.
  - **`DT-8` is NOT answerable here** *(corrected 2026-09-05)*. `deploytargets.py` gates **every** Staging
    reading on `STAGING_PROFILE = "awsds-infra-staging"` being live, and at 2.5 the account is still
    reached as `awsds-infra-dev`: the check is not failing, it is **not running**, which is the pair
    Lesson 13 is about. It becomes answerable after step 4's migration and the `~/.aws/config` rename of
    5.0, and it is asserted in the Validation rather than here. The instrument also still says
    *"`Staging` has no profile until the vend"* — stale prose from before the re-scope, corrected at 5.1.

### 3. Rename the account and move the OU — the two console acts, and the code that keys on the name

**Action:** enable trusted access — **0.5a measured it absent** — rename the account, move it to
`Workloads` through Control Tower, and re-point the two sites that resolve it by name. **Why:** `identity/sso/locals.tf` resolves the
account by the exact string `Development Account` behind a precondition that fails the plan, and
`aws/import-ids.py` maps the same string. **Explanation:** between the rename and the code edit the
`identity/sso` plan is **expected** to fail — which is why both happen in one sitting.

- **3.1 — DONE 2026-09-06 by the user**, CloudShell in Management; the call produced no output, which is
  its success. **Read back the same day**: `./aws/org-trusted-access-services.py` section 1 now reports
  *"PRESENT — `account.amazonaws.com` holds trusted access"*, so `put-account-name --account-id` is
  available and **step 3.2 is unblocked**. `INV-09` restated: **ten** principals, not nine; `account` is
  the fourth this project turned on, it holds no delegation, and the delegated count stays **four**.
- **3.1 — [user] Enable trusted access — 0.5a measured it ABSENT on 2026-09-05, so this runs**,
  Management, CloudShell as `AWS Control Tower Admin` / `AWSAdministratorAccess`:

  ```bash
  aws organizations enable-aws-service-access --service-principal account.amazonaws.com
  ```

  AWS documents this as the prerequisite for using the `--account-id` parameter of the Account Management
  API against a member: management (or delegated-admin) credentials, **all features enabled**, trusted
  access on. Success produces no output. **[Claude]** restates `INV-09`'s count afterwards.
- **3.2 — DONE 2026-09-06 by the user**, and the **root e-mail was changed in the same sitting**,
  which the step did not ask for and is worth recording as its own fact: the account now carries a
  `staging`-flavoured root address, so the vended-name pattern and the root address agree again.
  **Read back the same day** with `./aws/rename-check.py`: `RC-1 pass — Staging Account`, resolved by
  **exact** match against the ACTIVE roster. No propagation delay was observed between the console act
  and the read.
- **3.2 — [user] Rename the account**, Management: *Organizations → AWS accounts → select the member →
  Actions → Update account name*, or

  ```bash
  aws account put-account-name --account-id <the account> --account-name "Staging Account"
  ```

  The caller needs `account:PutAccountName`; the name is 1-50 characters matching `[ -;=?-~]+`; the
  management account cannot pass **its own** id. **Keep the ` Account` suffix** — it is the vended-name
  pattern the SSO slice measured. **A propagation delay is not documented**: read the name back with
  `aws organizations list-accounts` rather than re-issuing the call, and record what the read showed.
- **3.3 — DONE 2026-09-06.** Both **values** changed, both **keys** left alone (`development` stays the
  for_each key until 4.6 renames it behind a `moved {}` block). `identity/sso/` re-planned as
  `awsds-infra-identity`: **`No changes`** — the precondition resolves the account by the new name and
  not one assignment moved, which is the whole gate.
  - **A third site was corrected in the same commit, and it is prose rather than code**:
    `aws/import-ids.py`'s header said *"`Staging` arrives at the vend"* — the vend the quota refused.
    It now says the row's key is the **AWS name** and its value the **folder**, that the two disagree on
    purpose between 3.2 and 4.6, and that matching the row to the slice is the reason the row exists.
- **3.3 — [Claude] Re-point the two name-keyed sites, same sitting**: in
  `terraform-live/identity/sso/locals.tf` change the **value** `development = "Development Account"` to
  `"Staging Account"` (not the key), and update `aws/import-ids.py`. Re-plan `identity/sso/` and expect the
  precondition to pass again with **`No changes`** to the assignments.
- **3.4 — DONE 2026-09-06 by the user, "via console AWS", and the account IS in `Workloads`.** Which
  console is the half that still matters and it is **not** a question anyone should answer from memory —
  **3.5's read-back settles it**, and 3.5 is the same act either way: Control Tower *Update account* is
  both the reading and, if the move went through the Organizations console, the repair. **One
  consequence to expect rather than discover**: that act is precisely the account update Stage 1b
  verification (vi) watches for, so a direct `AWSAdministratorAccess` assignment reappearing afterwards
  is **expected** and gets restated, not reported as a finding. **The account IS in `Workloads`, measured
  two independent ways on 2026-09-06.** The two readings:
  `./aws/rename-check.py` `RC-2 pass` from `organizations list-parents`, and — the stronger one, because
  it is the ceiling answering rather than the directory — the battery's `region` phase attributes the
  us-east-1 deny in this account to **`p-i0ney7mx`, the same policy id Production returns**, where
  `Sandbox Account 1` returns a different one. Same id, same OU, said by a denial rather than by a list.
  - **What no instrument here can distinguish** is Control Tower *Update account* from
    `organizations move-account`, and the difference is not cosmetic: the second leaves the Account
    Factory **provisioned product** pointing at the old OU under the old name, and raises
    `Moved member account` drift when the two OUs differ in configuration — which auto-enrollment
    (**ON**, 0.5b) re-baselines but does not un-drift. Both are visible only from Management, which holds
    **no CLI profile**, so this is a **console reading owed by the user**, not a gap in the tree.
- **3.4 — [user] Move the OU**, Control Tower console: *Organization → the account → **Update account** →
  registered OU = `Workloads`*, or the Service Catalog update of the provisioned product with
  `ManagedOrganizationalUnit = Workloads`. **Never `aws organizations move-account`** — that path raises
  `ACCOUNT_MOVED_BETWEEN_OUS` drift and leaves the Account Factory **provisioned product** pointing at the
  old OU under the old name, which auto-enrollment explicitly does not fix. *This step used to carry a
  third reason — "without auto-enrollment it leaves the old OU's Config-rule controls attached" — and
  **0.5b measured the switch ON on 2026-09-06**, so that clause is struck rather than left to be
  re-derived by whoever reads it next.*
- **3.5 — [user] Update the provisioned product's parameters, same sitting**: re-enter `AccountName` as
  `Staging Account` alongside the new OU, then **read the parameters back**. Control Tower documents the
  e-mail field as *not* following an out-of-band change; whether `AccountName` does is not documented. If
  it refuses, record the divergence as a permanent property of the provisioned product — the treatment D32
  gives the direct assignment.
- **3.6 — DONE 2026-09-06, and the trigger did NOT fire — with a caveat that is the honest half of the
  answer.** `./aws/list-identities.py` §5.2: `Staging Account` carries **six** assignments — the three
  landing-zone group ones (`AWSOrganizationsFullAccess`, `AWSPowerUserAccess`, `AWSReadOnlyAccess`) and
  this repository's three (`InfrastructureAccess`, `DeploymentManagerAccess`,
  `DataScientistStagingAccess`). **No direct `USER` assignment, and no `AWSAdministratorAccess` at all**,
  so `AWS_STATE.md`'s roster row and `INV-05` stand unedited, and the one surviving D32 direct assignment
  is still `Policy Canary`'s alone.
  - **This does not yet answer Stage 1b verification (vi)**, and saying so is the point. That
    verification watches for the direct assignment returning *when an account update runs*. Whether an
    account update ran at all is exactly what 3.4 above cannot read from this side. If the user took the
    Control Tower path, this reading answers (vi) **in the negative** and it can be closed; if the move
    was `organizations move-account`, the event never happened and (vi) is still waiting — a
    verification that reads the same on "it did not fire" and "it was never triggered" is not yet a
    verification (Lesson 13).
- **3.6 — [Claude] Check D32's trigger**: `./aws/list-identities.py`. An *account update* is exactly what
  re-creates the direct `AWSAdministratorAccess` assignment (Stage 1b verification (vi)); if it came back,
  it is **expected**, and the row is restated rather than removed.
- **3.7 — DONE 2026-09-06. Full battery, every phase: `89 as expected, 0 unexpected, 10 not measured`**
  — all ten notes are the by-design ones (`EXC-03`'s four `DENY-NOT-SCP` Athena rows, six `UNTESTED` in
  accounts with no subnet). **The token is `staging` in both files** and no `dev` string survives
  anywhere under `aws/probes/`.
  - **This step's own first sentence was wrong and 3.8 is why**: it predicted the account would **lose**
    `DenyAthenaSparkStartSession` because *"that Sid exists only in the `Interactive` document"*. It did
    not — **3.8 put the Sid into the Workloads document three hours earlier**, deliberately before the
    move, so the account crossed with the deny rather than into a gap. The rest of the prediction held
    exactly: it lost `DenyClassicNotebookInstances` (fully absorbed) and gained
    `DenyInteractiveSageMakerSurface` and `DenyDataZoneEntirely`.
  - **The `ou` phase was not a retarget, it was a re-composition — five rows, and only one of them moved
    to `staging`.** A token flip alone would have produced three copies of questions `prod` and
    `sandbox1` already ask, and a battery whose probe count stops meaning a question count is the failure
    this file's own comments warn about:
    - **Two `allow` rows moved to `sandbox1`** (`sagemaker:CreateSpace`, `datazone:ListDomains`) — the
      block's whole point is that decision 1 *costs no feature*, and deleting them would have left the
      Interactive document with no permissive evidence at all. **Both passed.** The sample is now an
      **inherited** one, and it is not weaker: an SCP can only deny, `Sandboxes` carries no document of
      its own (the row below them is that evidence), so an `allow` under Interactive+Sandboxes is at
      least as strong as one under Interactive alone. What is genuinely gone is the direct-attachment
      sample, and **no account can restore it** — nothing sits directly in `Interactive` any more.
    - **Three rows deleted, not moved**: `sagemaker:CreateNotebookInstance` (the same question, from a
      different Sid, already asked by `prod` and `sandbox1`), `athena:StartSession` (`sandbox1` carries
      the Interactive half, `prod` the Workloads half), and 1.6's `athena:StartQueryExecution` negative
      probe — whose own comment already said Sandbox's identical row exists as 4e's contrast. That row
      is now the **only** place D13's query path is watched, and it passed.
    - **One row added for `staging`**, and it asks something none of the others do: not *is the Workloads
      document in force* but *did the account this stage moved actually acquire it*. It is
      `datazone:ListDomains`, `ro`, and it came back **`DENY-SCP p-83t232f4` — the same policy id
      Production's three rows return**. That is 3.4's attribution, and it is worth keeping permanently:
      this is the account that will hold deploy credentials.
  - **The silent half of the flip was the tag values, and both were caught**: the `tags` allow-probe and
    the `decl` IMDSv1 probe hard-coded `Environment=development` in their `--tag-specifications`. The tag
    policy allows all six values org-wide, so neither would have *failed* after the flip — they would
    have quietly asserted a value nothing carries. Both now read `staging`, and `staging` is confirmed an
    allowed value in `awsds-org-tag-policy.json`.
- **3.7 — [Claude⚡] Re-run the battery**: `./aws/probes/scp-battery.py --phase ou` with the new `staging`
  token and **`Workloads` expectations**. Two consequences to record rather than discover: the account
  **loses** `DenyAthenaSparkStartSession` (that Sid exists only in the `Interactive` document) and **gains**
  `DenyInteractiveSageMakerSurface` and `DenyDataZoneEntirely`; and `Sandbox Account 1` becomes the only
  Interactive sample the battery has.
  - **The delta, measured 2026-09-06 rather than predicted** (`./aws/org-policies.py` §2, both accounts
    read side by side): the account sits at **25 statements in force** today and Production — a Workloads
    account — sits at **25 as well**, so the count is not the check; the composition is. It **loses two**
    Interactive Sids, not one: `DenyClassicNotebookInstances` **and** `DenyAthenaSparkStartSession`. The
    first is **fully absorbed** — `DenyInteractiveSageMakerSurface` denies `sagemaker:CreateNotebookInstance`
    and `CreatePresignedNotebookInstanceUrl`, exactly the two actions it carried — so **only the Athena one
    is a gap**, which is what 3.8 closes. Everything else is unchanged: both OUs carry a Control Tower
    guardrail, the Region ceiling (`CTMULTISERVICEPV1`) and the root controls, and the three root documents
    apply either way.
  - **The token edit belongs HERE, not at 5.1** *(corrected 2026-09-05 — 5.1 scheduled it a pass late, and
    a battery run against a `dev` token that no longer resolves is not a measurement)*. It is **two files,
    not one**: `scp-battery.py`'s `PROFILES` map — the single place a probe's account token becomes a CLI
    profile, and a token missing from it **stops the run** rather than skipping a probe — and `probes.py`,
    where the token is the probe's second positional argument and the OU expectations hang off it.
  - **Two probes also hard-code `Environment=development` in their `--tag-specifications`** (the `tags`
    allow-probe and the `decl` IMDSv1 probe). The tag policy allows all six values **org-wide**, so neither
    will fail after the flip — they will simply be asserting the wrong account, which is worse than a
    failure because nothing reports it. Move both with the token.
  - **Left deliberately undone:** `development` stays an allowed value in `awsds-org-tag-policy` even
    though nothing carries it after 4.4. Removing a value is a policy change with its own `POLICIES.md`
    row and its own battery run, and it is not this stage's.
- **3.8 — DONE 2026-09-06, and taken BEFORE the OU move rather than after it.** The step is listed after
  3.4 but does not depend on it, and the order matters in one direction only: applied first, the account
  **never spends a moment in `Workloads` without the deny it had in `Interactive`**; applied after, that
  window is real. Applied as `awsds-infra-identity`, **`0 added, 1 changed, 0 destroyed`**, re-plan
  `No changes`, and the document read back from Organizations carries three Sids.
  - **The Sid was copied verbatim** — three actions, workgroup-scoped — because the two OUs deny the same
    thing for the same reason and a paraphrase is a second spelling to keep in step (Lesson 33).
  - **`EXC-03` named this event in advance and it arrived**: *"the row to watch is the contrast one — if it
    ever turns into a denial too, the pair stops attributing"*. Production **was** the contrast precisely
    because its OU document carried no athena action; now it inherits the deny. The contrast moved to
    **`Policy Canary`** (`Policy Test` carries no project SCP), and the battery was re-run the same day:
    **25 as expected, 0 unexpected** — `prod` and both Interactive rows `DENY-NOT-SCP`, the canary
    `ALLOWED / reached-authorization`, and 1.6's negative probe still reading
    *"athena:StartQueryExecution STILL WORKS"*, so **SQL and D13's query path are untouched**.
  - `POLICIES.md` reviewed in the same sitting (`./scripts/check-index.py` clean), and `EXC-03` rewritten
    with the move.
- **3.8 — [Claude⚡] Close the Athena Spark gap**: add `DenyAthenaSparkStartSession` to
  `awsds-org-scp-ou-workloads`. The SMUS network-isolation guide states that *"Amazon Athena for Apache
  Spark does not currently support Amazon VPC"* and gives the SCP denying `athena:StartSession` **and**
  `athena:UpdateSession` as the control — so a Workload account that can start a session has an unproxied
  path out of the account that will hold deploy credentials. Keep `UpdateSession` even though it appears in
  no API model this project could read: the deny costs nothing and AWS's own example carries it.
  - **Copy the Sid as it stands — it is THREE actions and it is workgroup-scoped** (read 2026-09-06; this
    step named two actions and no resource). The applied statement denies `athena:StartSession`,
    `athena:UpdateSession` **and `athena:StartCalculationExecution`** on
    **`arn:aws:athena:*:*:workgroup/*`**, not on `*`. `POLICIES.md` records all three; only this step was
    short, and the missing one is the action that actually runs the calculation. Review
  [`terraform-live/identity/org-policies/POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md)
  in the **same sitting**, and move `EXC-03`'s Athena contrast probe to `Policy Canary`.

### 4. Migrate the tree — `development/` to `staging/`, folder first and token second

**Action:** create the new state home, move each surviving slice with Recipe E, then flip the token.
**Why:** the folder name is the Terraform state key and the token is every physical name. **Explanation:**
splitting *migration* from *token flip* is what keeps each plan readable — the first must produce
`No changes`, the second a short, explainable replacement list. Recipe E was written on 2026-09-05 and is
followed here, not authored.

- **4.1 — DONE 2026-09-06, and SPLIT IN TWO on purpose.** `CIDRS["staging"]` is `10.50.0.0/16` as of
  the 4.3 commit — the half that prevents the VPC replacement, and it had to land in the same commit as
  the `git mv` because the tfvars are generated from the folder key. **The `development` row was NOT
  deleted and 10.40 is NOT free yet**: `production/foundation/peers.tf` reads `var.peers["development"]`
  by literal, and that map is built from this table's KEYS, so deleting the row breaks Production's slice
  until 4.5 re-points the four hand-written provider aliases. Both go in that one commit — Recipe E step
  8's rule (*keep the old vocabulary rows alive*) applied to the one table that is read by another
  account. **6c step 0 must not consume 10.40 until then.**
- **4.1 — [Claude] Fix the address table BEFORE the token flip — the hazard that would replace the VPC**:
  in `scripts/tfhygiene/backend.py`, `CIDRS` is keyed by **account folder** and today reads
  `staging = 10.40.0.0/16`, `development = 10.50.0.0/16`. The moment the folder becomes `staging/`, the
  generated `vpc_cidr` would change and the plan would propose **replacing the VPC**. Set
  `CIDRS["staging"] = "10.50.0.0/16"`, delete the `development` row, and **free `10.40.0.0/16`** — 6c step 0
  consumes the freed block; it does not perform this edit. The account keeps 10.50 because a VPC CIDR is
  immutable and a rebuild would replace every subnet, route table, endpoint and the peering with it.
  - **The reason this step used to give expires two passes earlier, and that is worth saying rather than
    leaving to be re-derived** *(2026-09-06)*: it said a rebuild "would invalidate the `[P]`
    gateway-endpoint ids **the lake's bucket policy names**" — but **step 2.3 already removes this
    account's endpoint from `trusted_vpce_ids`**, so by pass 4 the lake names none of them. The
    conclusion is unchanged and now rests where it should: a VPC replacement rebuilds the whole
    `foundation/` slice and forces 6c to re-cut a peering it has not built yet. **Second instance of the
    same shape in this stage** — step 3.4's Config-rule clause was the first — and both are Lesson 3 read
    backwards: a fact that moved invalidates the sentence that cited it, even when the conclusion holds.
- **4.2 — DONE 2026-09-06** (the user ran the apply; Claude wrote, planned and migrated).
  **`8 to add, 0 to change, 0 to destroy`** → `awsds-staging-tfstate` and
  `alias/awsds-staging-tfstate`, then **phase 2 of the bootstrap pattern**: backend uncommented,
  `init -migrate-state` into the bucket the slice had just created, local state deleted, re-plan
  **`No changes`**. `./scripts/check-bootstrap-parity.py` clean in both phases.
  - **The parity check rejected the first attempt, and the reason is worth carrying**: three lines of
    prose were added above the commented backend block explaining the phase. Parity compares that file
    **with the comment markers removed**, so prose inside it is *content*, and the slice read as diverged.
    The two forms it tolerates are exactly two — commented and live — and the explanation already lives
    in the header every copy shares.
- **4.2 — [Claude⚡] Create the new state home**: `terraform-live/staging/bootstrap/`, producing
  `awsds-staging-tfstate` and `alias/awsds-staging-tfstate` from the existing bootstrap module. **`PROFILES`
  is the only table missing a `staging` row** — `ENV_TOKENS`, `ENVIRONMENT_TAGS` and `ZONE_IDS` already
  carry one (read 2026-09-05; this step used to name `ZONE_IDS` among the missing). **`CIDRS` carries one
  too, with the WRONG VALUE** — that is 4.1's edit, not this one, and the two must not both claim it. The
  `staging` slice rows go into `scripts/tfhygiene/layers.py`, whose `staging joins at vend` comment is
  stale prose to correct in the same commit. **Keep the `development` rows alive** until the old bucket is gone — the
  generator still has to emit the old backend.
- **4.3 — DONE 2026-09-06. The gate passed: `terraform plan` → `No changes` after
  `init -migrate-state`**, with the same gateway-endpoint ids the baseline showed, so the state arrived
  intact. `foundation/`, `egress/` and `probes/` moved with `git mv`; `development/bootstrap/` stayed.
  - **The tfvars were NOT regenerated, and that is the whole of Recipe E step 3.** The untracked
    `terraform.auto.tfvars` moved with the directory still reading `env = "dev"`,
    `environment_tag = "development"`, so the plan compares the same names against the same resources
    and an empty plan means the migration. Only `gen-backend-hcl.py` ran.
  - **The two `[E]` slices WERE migrated after all, and this step said they need not be.** That was right
    about the *necessity* and wrong about the tidiest path: zero resources is still a state OBJECT with a
    lineage (measured: 749 and 697 bytes in the old bucket), and their `.terraform/` directories moved
    still pointing at `awsds-dev-tfstate` — a bucket 4.7 destroys. Leaving them would have made the next
    `make up` prompt for a backend change in a slice nobody was thinking about. Two `init -migrate-state`
    calls, no plan gate, because there is genuinely nothing to gate in a torn-down slice.
- **4.3 — Recipe E step 1 DONE 2026-09-06; steps 3-5 wait on 4.2's apply.** `development/foundation/`
  initialised against the OLD backend (`awsds-dev-tfstate`, key `development/foundation/…`) and planned:
  **`No changes`**. That is the baseline the whole recipe rests on and it is worth taking *before* the
  move rather than after: with it, a non-empty plan on the far side is the **migration**; without it, a
  non-empty plan is ambiguous between the migration and drift that was already there. The state is now
  cached locally, which is what Recipe E step 1 exists to produce.
  - **The generated `peers` map already carries BOTH keys** — `development` and `staging`, both resolving
    to `awsds-infra-staging` — because 4.2 added the `staging` PROFILES row while `staging` was still in
    `CIDRS`. It is **inert**: `production/foundation/peers.tf` builds `local.peer_vpc_ids` as a
    hand-written two-row map and never iterates `var.peers`, so an extra key creates no peering. Checked
    rather than assumed, because the opposite would have been a third VPC peering proposed by a plan
    nobody was reading for that.
- **4.3 — [Claude⚡] Migrate with Recipe E — and only ONE slice actually needs it** *(measured
  2026-09-06)*. `foundation/` is the only surviving slice carrying resources; **`egress/` and `probes/` are
  `[E]` and their states are EMPTY — zero resources each**, because D11 leaves them torn down between
  sittings. So they are not migrations at all: their folders move with a `git mv` and their state is
  created fresh at the next `up`, with no `init -migrate-state` and no empty-plan gate, because there is
  nothing to gate. This also settles a contradiction: `conventions.md` §6 said `egress/` was *destroyed*
  while this step said it *migrated*, and the measurement says neither word was right. (`sagemaker/` and
  `data/` were destroyed in passes 1-2; `bootstrap/` is last and is 4.7's.) For `foundation/`, Recipe E's
  gate is that
  `terraform plan` returns **`No changes`** after `init -migrate-state`; nothing proceeds past a slice that
  does not.
- **4.4 — PLANNED AND READ 2026-09-06, apply pending.** `8 to add, 16 to change, 8 to destroy`, and
  the shape is the predicted one: **the VPC, all six subnets, both gateway endpoints, all four route
  tables, the IGW and `aws_vpc_peering_connection.to_production` are IN-PLACE tag changes** — every id
  survives, which is what INT-05's anchors and the peering depend on.
  - **The step named five replacements and there are EIGHT, all of one class.** Predicted: the four
    security groups (`endpoints` + the three tiers) and the flow-log **log group**. Also replaced, and
    unlisted: **`module.flow_log_role.aws_iam_role.this`** (its name is `awsds-dev-vpc-flow-logs`, an
    input built from the env token — exactly the class the step describes), **its inline policy**, and
    **`aws_flow_log.this`**, which binds the two and cannot outlive either. So the rule the step states is
    right and its enumeration was short; the reading is *"every resource whose NAME is built from the env
    token, plus whatever binds them"*, which is a rule rather than a list.
  - **Nothing outside the account is replaced, and that was checked rather than assumed**: the lake's
    `trusted_vpce_ids` stopped naming this account at 2.3, and the gateway endpoints keep their ids
    anyway; the two `[E]` slices that read this state are torn down. **What DOES break the moment this
    applies is `production/foundation/`**, whose data sources look the VPC up by the tag `awsds-dev-vpc`
    — which is 4.5, and why the two applies are back to back.
- **4.4 — [Claude⚡] Flip the token**: set `env = "staging"` and `environment_tag = "staging"` and read the
  plan carefully. The VPC, its subnets and the `[P]` S3 and DynamoDB **gateway endpoints keep their ids**
  (in-place tag changes only — INT-05's anchors; **not** the lake's `trusted_vpce_ids`, which stopped
  naming this account at 2.3),
  while the security groups and the flow-log group **are replaced**. Anything else in the replacement list
  is a surprise and stops the step.
- **4.5 — READ BEFORE WRITING, 2026-09-06, and it is BIGGER than this step says: without `moved {}`
  blocks it DESTROYS THE PEERING.** The step describes an edit to the accepter side and four provider
  aliases. What it does not say is that `development` is a **`for_each` key**, not just a name, in
  `production/foundation/peers.tf` — so renaming it is an address change, and Terraform's answer to an
  address change is destroy-and-create:
  - **`aws_vpc_peering_connection_accepter.peer["development"]`** — the load-bearing one. Destroying an
    accepter deletes the peering connection. **One `moved {}` block, literal key.**
  - **`aws_route53_vpc_association_authorization.peer["prod.development"]` and `["pages.development"]`** —
    two literal keys, two blocks.
  - **`aws_route53_zone_association.development`** and **`aws_route.development_forward`** — resource
    *names*, not keys (both `for_each` over keys that carry no token), so **one block each** covers every
    instance.
  - **`aws_route.return`** is the exception and it is taken deliberately. Its keys are
    `"<route-table>|development-private-<subnet-id>"`, so a `moved {}` would have to name `[P]` subnet
    ids in a tracked file — precisely what this file's own header forbids (*"the peer's facts are READ,
    NEVER PASTED"*, Lesson 3). **Those routes are re-created instead**: the destination CIDRs are
    unchanged, a route is idempotent and cheap, and the far end is `[E]` and torn down. The cost is a
    handful of seconds on a path nothing is using; the alternative is a stale id in the tree forever.
  - **`production/registry/` is the fourth alias and it is the easy half**: the provider alias,
    `data.aws_caller_identity.development` and one `locals` reference. Data sources hold no address the
    apply defends, and the account id behind them is unchanged, so its policies do not move.
  - **`REGISTRY_CONSUMERS` keeps the row**, renamed — Staging pulls images and packages like any deploy
    target; it is `DATA_CONSUMERS` that lost it (2.4). The two lists answering different questions is
    exactly what that table's comment predicted would matter one day.
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
  delete markers), destroy it in the next commit. **Measured 2026-09-06 (`./aws/tf-backends.py` §2):
  `awsds-dev-tfstate` is versioned, BPA 4/4, TLS-only, two lifecycle rules — and `OBJ LOCK` is `off`.**
  That last field is the one worth having read: Object Lock on this bucket would have made the by-hand
  emptying impossible and the step unexecutable, and it is on in exactly one bucket in this estate
  (`INV-14`'s CloudTrail bucket), so the shape is not hypothetical. Only then remove the `development` rows from
  `backend.py` and `layers.py`.
- **4.8 — DONE 2026-09-06, in the `git mv` commit.** `staging` is REQUIRED, `development` is OPTIONAL —
  and the comment says what the word now means, because it inverted: it used to mean *"not vended yet,
  and this check starts comparing it the day somebody writes it"*; it now means *"still present, and its
  absence is the expected end state"*.
- **4.8 — [Claude] Swap the parity gate**, in the `git mv` commit: `scripts/check-bootstrap-parity.py`
  makes `development` REQUIRED and `staging` OPTIONAL — the two swap.

### 5. Close the stage — instruments, vocabularies and the documents that state the account as a fact

> **Read this pass before running passes 1-4, not after.** Three times now an instrument listed here has
> gone red — or gone unrunnable — at the pass that *caused* the change rather than at this one: `studio.py`'s
> `US-4` at 1.1 (2026-09-06, measured), the probe token at 3.7, and `deploytargets.py`'s `DT-8`, which is
> not runnable until step 4 makes the profile resolve. **A check that is red for four passes is a check
> nobody reads on the fifth.** So each item below carries the pass that actually owns it, and what stays
> here is only what the *finished* conversion changes.

**Action:** re-scope every instrument and revise every document that names the account. **Why:** a role
change is the trigger to re-read every instrument in the same sitting (Lesson 31) — a check written for an
Interactive Development keeps reporting `pass` about an account that no longer exists in that role.
**Explanation:** two of these are removals rather than retargets, and saying which is which is the step.

- **5.0 — [user] The three profiles in `~/.aws/config`, because only one of them is Claude's to rename.**
  Measured 2026-09-05: the account is reached by **`awsds-infra-dev`** (renamed to `awsds-infra-staging` at
  step 4), **`awsds-ctadmin-orgfull-dev`** (the `AWSOrganizationsFullAccess` seat of 2026-08-15 — rename it
  too, so no `dev` token outlives the account) and **`awsds-scientist-dev`**, which step 2.1 **kills**: its
  permission set leaves the account, so the profile authenticates into nothing. **No instrument depends on
  any of the three names** — `awslib/profiles.py` enumerates `awsds-*` at run time, and the only tracked
  files naming the last two are log entries, which are never edited. So this is a `~/.aws/config` act with
  no code half, which is exactly why it needs a step of its own.
- **5.1 — [Claude] Re-scope the instruments**: drop `awsds-infra-dev` from `studio.py`'s
  `INTERACTIVE_PROFILES`, and **remove** the Development slice from `dns-allowlist.py` rather than
  retargeting it (Staging is headless — it resolves nothing a person chose). **The probe token is NOT
  here** — it moved to step 3.7, which is the run that needs it. Rename the profile constants — **and, in
  `deploytargets.py`, the prose that still waits for a vend that will not happen** — in
  `cicd.py`, `deploytargets.py`,
  `supplychain.py`, `datalake.py`, `networking.py`, `egress.py`, `vpn.py` and `sandboxlake.py`.
- **5.2 — [Claude] Run the conversion report**: `./aws/rename-check.py` must now print the **AFTER**
  verdict — new name, `Workloads`, the three persona sets, zero DataZone objects, no share, no vending
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

- An account named `Staging Account`, in the `Workloads` OU, carrying **six SSO assignments — three of
  them this project's**: `InfrastructureAccess`, `DataScientistStagingAccess` and
  `DeploymentManagerAccess`, beside the three the landing zone puts in every governed account
  (`AWSOrganizationsFullAccess`, `AWSPowerUserAccess`, `AWSReadOnlyAccess`), which this stage does not
  touch. And no SMUS association, no blueprint configuration, no project profile, no lake share, no
  resource link, no vending policy.
- `terraform-live/staging/{bootstrap,foundation,egress,probes}/` on `awsds-staging-tfstate`, with
  `terraform-live/development/` gone and the old bucket destroyed.
- `CIDRS` holding `staging = 10.50.0.0/16` and **`10.40.0.0/16` free** for 6c.
- `DenyAthenaSparkStartSession` on the `Workloads` document, with its `POLICIES.md` row.
- Every instrument re-scoped to one Interactive account — and **no new CloudShell script**: the two
  switches of 0.5 are read by `org-trusted-access-services.py` and `management-landing-zone-drift.sh`,
  each of which gained the interpretation it was missing on 2026-09-05.

## Validation

- `./aws/rename-check.py` reports **AFTER**: the new name, the `Workloads` OU, `RC-5` naming the three
  persona sets (it ignores the landing zone's three by design), `RC-4`/`RC-4b` both clear, `RC-6` = 0, and
  **zero** DataZone objects.
- `./aws/studio.py` shows one associated account and one project profile; `US-6` passes from the renamed
  account.
- `./aws/datalake.py` `DL-5`/`DL-13` pass with no Development row, and `DL-7` reads two resource links.
- `./aws/deploytargets.py` `DT-8` **runs at all** — it is skipped until `awsds-infra-staging` resolves —
  and passes: no resource link from the deployment target to Data Governance (D20).
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

1. ~~Does a blueprint configuration with an attached grant destroy in one plan, or does it need Recipe F?~~
   **ANSWERED 2026-09-06 (1.2): one plan, one apply.** The provider orders each grant before its
   configuration by itself; Recipe F was not needed and stays unexercised.
2. ~~Does `list-environment-blueprint-configurations` fail rather than return empty after disassociation?~~
   **ANSWERED 2026-09-06 (1.5): it fails — `UnauthorizedException: Unauthorized`.** Not an access-denied
   naming a policy: the domain is simply no longer shared into the account. 6a step 1.3's proof in reverse,
   and the distinction 1.3's own read-back turns on.
3. Does the OU move through Control Tower re-baseline the account by itself, or does it depend on account
   auto-enrollment? (0.5 + 3.4.) **Narrowed by documentation on 2026-09-05 and then made UNANSWERABLE by
   measurement on 2026-09-06**, which is the honest outcome rather than a gap: auto-enrollment is **ON** in
   this landing zone, so both paths re-baseline and the estate can no longer show what the other one would
   have done (Lesson 22 — the failing case cannot be produced without an `update-landing-zone`, which is a
   write nobody should take as a measurement). **What stays measurable at 3.4/3.5 is the narrower question
   that actually matters here**: does the account come out carrying **only** the `Workloads` baseline, and
   do the provisioned product's parameters follow?
4. Does the direct `AWSAdministratorAccess` assignment return after the account update? (3.6, D32.)
   **The negative baseline is measured (2026-09-05): the account carries no such assignment today**, so a
   return is detectable rather than arguable — which is what 1b verification (vi) has been waiting for.

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
