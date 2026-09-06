# Log — Stage 6b — `Development` becomes `Staging`

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-06b-development-becomes-staging.md`](../plan/stages/stage-06b-development-becomes-staging.md).*

*Provenance is named by SUBJECT rather than by ordinal — the convention
[Stage 3's log](log-stage-03-networking.md) adopted. Identifiers are redacted as
`scripts/check-identifiers.py` requires: account ids are replaced by the account's name in angle
brackets, and ARNs are written without their account segment. **Nothing else is touched** — the domain
id, the RAM share names, the permission-set suffixes and the error wording are verbatim, because a log
that has been tidied stops being evidence. All times UTC.*

*File created 2026-09-05 by Claude, on the user's request, at the close of the preparation sitting —
**before any part of the stage has been executed**. Nothing below changed anything in AWS: every AWS
call in this entry is a read, and every write in it is a write to this repository.*

---

## 2026-09-05 — the preparation sitting (pass 0, and three corrections to the stage before it runs)

*Provenance: the request and the SSO sign-in are the user's; every reading, every repository edit and
the branch are Claude's. Readings carry the report's own UTC stamp, which had crossed midnight into
2026-09-06 by the time pass 0 ran.*

### What was asked, and what was found before anything was read

- **[user]** Asked Claude to prepare the next stage of the plan. Stage 6b is the next by the route in
  `GENERAL_PLAN.md` (6b → 6c → 6d → 7).
- **[Claude]** Read the stage against the code it names, and **three of its instructions did not
  survive the reading**. All three are corrected in the stage file; the reasoning is there and is not
  repeated here.
  1. Step 1.2 said *"set `blueprints_enabled = false` in `terraform-live/development/sagemaker/`"*.
     Nothing in that folder owns the value: it is generated from `SMUS_ASSOCIATED`, regenerated before
     every `init`, and the file it lands in is git-ignored. The edit 1.2 needs is **1.6's**, which now
     runs inside 1.2.
  2. The expected plan for that step was one line short. Nulling the flag also nulls the three domain
     inputs, and the module's key policy drops the domain execution role and every statement gated on
     the domain id — so the plan reads **`1 to change, 22 to destroy`**.
  3. `PERSONA_VENDING_ACCOUNTS` is `list(SMUS_MEMBERS)`, so the same edit leaves
     `development/foundation/` carrying a **destroy blocked by `prevent_destroy`** from 1.2 until 2.2.
- **[Claude]** Step 0.5 asked for a new CloudShell script, `management-account-switches.sh`. It was not
  written: **both switches were already being read** — trusted access by `org-trusted-access-services.py`
  from the laptop, `remediationTypes` by `management-landing-zone-drift.sh`, which has printed that
  field since its first run. What each lacked was the interpretation, and that is what was added.
- **[Claude]** Read AWS's account auto-enrollment documentation for the second switch and recorded it in
  `REFERENCES.md`. The three limits that decide step 3.4: it is not retroactive, it **does not touch the
  Account Factory provisioned product**, and it does not prevent `Moved member account` drift when the
  two OUs differ — which `Interactive` and `Workloads` do.

### Pass 0 — the preflight readings

- **[user]** Signed in as the **infrastructure user**, permission set **`InfrastructureAccess`** — one
  login, every `awsds-infra-*` profile. The persona and `awsds-ctadmin` sessions were **not** signed in,
  so nine profiles report `Error loading SSO Token` in every report below; that is the expected shape of
  "not signed in", not a finding.
- **[Claude] 0.1 — `./aws/studio.py`.** As the stage expected: `US-3` **11 blueprint configurations** in
  the member, `US-4` both project profiles (`experimentation`, `engineering`), **no project** (`US-8`
  reads *"no blueprint-provisioned role exists yet — the check is unexercised here"*), and no SageMaker
  AI domain in the account. `0 check(s) FAILED`. Pass 1 therefore needs no project delete.
- **[Claude] 0.2 — `./aws/datalake.py`.** `0 check(s) FAILED`. The member holds **two resource links**
  (`curated`, `raw`), `DL-5` reads `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE`, `DL-13` reads **the
  `InfrastructureAccess` seat alone** in this account — no service-appointed admin here, unlike Sandbox.
  `DL-7`: 5 shares out, 4 resource links across both consumers, no pending invitation.
- **[Claude] 0.2b — the re-grants, read directly**, because `datalake.py` has no section for them:
  `lakeformation list-permissions` in the member returns **6** permissions, of which **4 name
  `AWSReservedSSO_DataScientistAccess_93e51218b5f8bf66`** (two `DESCRIBE` on `Database`, two `DESCRIBE`
  on `LFTagPolicy`) and 2 name the `InfrastructureAccess` role. The four are step 2.4's expected loss.
- **[Claude] 0.3 — `./aws/list-identities.py`.** The account carries **seven** assignments, not four.
  Four are this project's personas — `InfrastructureAccess`, `DataScientistAccess`,
  `DeploymentManagerAccess`, `DevEnvStewardAccess`, each to its `sso-group-*` — and **three are the
  landing zone's**: `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins`, `AWSPowerUserAccess` →
  `AWSSecurityAuditPowerUsers`, `AWSReadOnlyAccess` → `AWSSecurityAuditors`. **No direct
  `AWSAdministratorAccess` assignment** — 1b step 5.1's removal is still holding, which is what makes
  step 3.6 a real question rather than a formality.
- **[Claude] 0.4 — `./aws/rename-check.py`, first run ever, and it found two faults in itself.**
  - **RC-6 could never have answered.** `list-permissions --principal <account>` without `--resource` is
    refused outright — *"Resource is mandatory if Principal is set in the input"* — so the check returned
    `(call failed)` in the BEFORE state and would have returned it identically in the AFTER one. Fixed to
    list the catalog and match the account client-side; it now reads **2**, the two TBAC triples.
  - **RC-5 failed on the untouched estate**, contradicting the file's own promise that everything notes
    before the stage runs. It had no BEFORE branch: the two forbidden permission sets are the account's
    starting state, and what makes the same reading a finding is the account having *already* been
    renamed or moved while still holding them. Fixed.
  - **RC-4 was reporting three shares as one question.** The `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` share
    goes at step 1; the two `LakeFormation-V4-*` shares go at step 2.3. Split into RC-4 / RC-4b / RC-4c so
    that a mid-stage reading names the step that clears it.
  - **The BEFORE verdict, after the three fixes: six notes, `0 check(s) FAILED`** — `Development Account`,
    `Interactive`, `dzd-d8yrvx1ko7im6o=11`, the DataZone share present, the two LakeFormation shares
    present, both forbidden permission sets present, 2 Lake Formation grants naming the account. Exactly
    the state the stage is written against.
- **[Claude] 0.5a — `./aws/org-trusted-access-services.py`.** **`account.amazonaws.com` is ABSENT.**
  Nine principals hold trusted access — `access-analyzer`, `cloudtrail`, `config`, `controltower`, `iam`,
  `member.org.stacksets.cloudformation`, `ram`, `securityhub`, `sso` — and Account Management is not one
  of them. **Step 3.1 is therefore a real step, not a conditional one**: without it the rename cannot be
  issued against a member at all.
- **[user] 0.5b — ran 2026-09-06T03:03:15Z**, CloudShell in **Management**, permission set
  **`AWSAdministratorAccess`**, `./aws/cloudshell/management-landing-zone-drift.sh`. Report pasted by the
  user; the load-bearing rows, verbatim:

  ```
  landing zone             arn:aws:controltower:us-west-2:<ACCOUNT>:landingzone/4I3ACTXON4Q7CJ8H
  status                   ACTIVE
  deployed version         4.0
  latest available         4.0
  DRIFT STATUS             IN_SYNC
  remediation types        INHERITANCE_DRIFT
  account auto-enrollment  on
  ```

  Section 4: **one operation ever** — `CREATE` / `SUCCEEDED`. Section 5: resource policy **PRESENT**, the
  `PrincipalArn` condition on exactly **two** statements. Section 7: no call failed.
- **[Claude] What that reading cost, and it is the reason the step exists.** **The stage predicted the
  opposite** — 0.5b said *"absent — the default, and the expected reading here"*. **The value had been in
  the repository since 2026-08-16**: `INV-17` records `remediationTypes: INHERITANCE_DRIFT` in the same
  sentence as the drift flag, and nobody had named it a switch, so the prediction was written without
  reading the file whose job is exactly that (`CLAUDE.md`: read `docs/AWS_STATE.md` whenever a snapshot is
  read). `INV-17` now carries the interpretation as well as the value.
- **[Claude] One of step 3.4's two reasons is struck.** It said the Organizations move path *"raises
  `ACCOUNT_MOVED_BETWEEN_OUS` drift and, **without auto-enrollment**, leaves the old OU's Config-rule
  controls attached"*. With the switch ON that second clause is false. **The conclusion survives**: the
  Control Tower `Update account` path is still the one, because auto-enrollment never touches the Account
  Factory **provisioned product** and does not prevent `Moved member account` drift between two OUs that
  differ — which `Interactive` and `Workloads` do.
- **[Claude] And verification 3 became unanswerable, which is the honest outcome.** *"Does the OU move
  through Control Tower re-baseline by itself, or does it depend on auto-enrollment?"* — with the switch
  ON both paths re-baseline, and producing the failing case would take an `update-landing-zone`, a write
  nobody should issue as a measurement (Lesson 22). What stays measurable at 3.4/3.5 is narrower and more
  useful: whether the account comes out carrying **only** the `Workloads` baseline, and whether the
  provisioned product's parameters follow the rename.

### What the sitting left in the repository

- **[Claude]** Branch `claude/stage-06b-preparation`, [PR #53](https://github.com/felipenoris/AWS-DataScience/pull/53).
  Nothing merged, nothing applied.
- **[Claude]** Two instruments given the interpretation they lacked (`org-trusted-access-services.py`,
  `management-landing-zone-drift.sh`); `rename-check.py` corrected in three places; the stage file
  corrected in the places listed above and re-reviewed against the pass 0 readings.

---

## 2026-09-06 — the plan reviewed against pass 0, and six more corrections

*Provenance: the request is the user's; every reading and every edit below are Claude's. All readings are
read-only calls as the infrastructure user through `InfrastructureAccess`, and the reports they produced
are `aws/output/{org-policies,tf-backends,networking}.txt` — untracked, regenerable, and not repeated here.*

- **[Claude] The policy delta of the OU move, measured instead of predicted** (`org-policies.py` §2,
  Development and Production read side by side). Both accounts sit at **25 statements in force**, so the
  count is not the check — the composition is. The account **loses two** Interactive Sids, not the one
  step 3.7 named: `DenyClassicNotebookInstances` **and** `DenyAthenaSparkStartSession`. The first is
  **fully absorbed** by `DenyInteractiveSageMakerSurface`, which denies the same two actions, so only the
  Athena one is a gap. Everything else — guardrail, `CTMULTISERVICEPV1`, the three root documents — is
  identical on both sides.
- **[Claude] Step 3.8 under-specified the statement it copies.** The applied
  `DenyAthenaSparkStartSession` carries **three** actions — `athena:StartSession`, `athena:UpdateSession`
  and **`athena:StartCalculationExecution`** — scoped to **`arn:aws:athena:*:*:workgroup/*`**. The stage
  named two actions and no resource; `POLICIES.md` had all three all along. The missing action is the one
  that runs the calculation.
- **[Claude] Step 2.3 does more than revoke grants: it rewrites the lake's bucket policies.**
  `local.consumer_vpce_ids` iterates the consumer remote states, so dropping the account from
  `consumer_accounts` also drops its **S3 gateway endpoint** out of `trusted_vpce_ids` — INT-05's
  `aws:SourceVpce` allow-list. Correct and intended, and a different class of change from a grant
  revocation.
- **[Claude] Two justifications in the stage expire before the step that uses them.** 3.4's *"without
  auto-enrollment, leaves the old OU's Config-rule controls attached"* died with the 0.5b reading; 4.1's
  *"a rebuild would invalidate the gateway-endpoint ids **the lake's bucket policy names**"* dies at 2.3,
  three steps before pass 4 runs. **Both conclusions survive on other grounds**, and both sentences were
  rewritten rather than left to be re-derived — Lesson 3 read backwards.
- **[Claude] `awsds-dev-tfstate` can actually be destroyed** (`tf-backends.py` §2): versioned, BPA 4/4,
  TLS-only, two lifecycle rules, and **Object Lock `off`**. On this estate that is not a formality —
  `INV-14`'s CloudTrail bucket is locked at `COMPLIANCE`/90 days, and the same setting here would have
  made step 4.7 unexecutable rather than slow.
- **[Claude] A consequence outside this stage, recorded where it belongs.** With auto-enrollment ON, an
  account created by `organizations:CreateAccount` and placed in a **registered OU** is baselined without
  Account Factory — which is the premise that kept a rung off [D34](../plan/decisions/D34-account-vending.md)'s
  vending ladder. D34 gains a dated note and [Stage 14](../plan/stages/stage-14-sandbox-vending.md) a
  pointer; **nothing is re-decided** — that stage is blocked on the account quota and D34's revision
  trigger is frequency, not mechanism (Lesson 7).
- **[Claude] One correction to Claude's own text of 2026-09-05.** The drift script's section 6 said the
  Stage 6b account update is *"the event 1b verification (vi), 1d (iv) and 1d (xiv) have each been waiting
  on"*. Only **(vi)** — that one is about this account's assignment. 1d (iv) waits on an update to **Log
  Archive** and 1d (xiv) on the **Security** OU's accounts; an update to a member in `Interactive`
  re-baselines neither.

---

## 2026-09-06 — pass 1 begins: step 1.1, the `engineering` project profile

*Provenance: the authorization is the user's, given in chat for this specific apply; the edits, the plan,
the apply and the read-backs are Claude's. Applied as the **infrastructure user**, account **Data
Governance**, permission set **`InfrastructureAccess`** (profile `awsds-infra-data`). Recipe A throughout —
branch, edit, generate, init, plan to a file outside the repository, apply exactly that file, re-plan.*

- **[Claude]** Removed the four sites the step names: the `engineering` key in `local.project_profiles`,
  the `development` row of `local.member_account_ids`, `data.aws_caller_identity.development`, and the
  `aws.development` provider alias.
- **[Claude] Plan: `0 to add, 0 to change, 2 to destroy`** — exactly the two the step predicted, read out
  of the saved plan before applying:

  ```
  delete     awscc_datazone_policy_grant.create_project_from_profile["engineering"]
  delete     awscc_datazone_project_profile.this["engineering"]
  ```

- **[user]** Authorized the apply. **[Claude]** Applied the saved plan; **re-plan returns
  `No changes`**.
- **[Claude] Read back from the domain**, not from the state: `list-project-profiles` returns
  **`experimentation` / `ENABLED`, alone**, and `list-policy-grants` for
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` on the root domain unit returns **one** grant — that profile, to
  the data-scientists group.
- **[Claude] Three comments the removal invalidated, corrected in the same commit**: `providers.tf`'s
  *"TWO ALIASES"*, `data.tf`'s *"member accounts"* plural, and `locals.tf`'s *"WHY THESE TWO GROUPS"* —
  which had itself predicted this removal as *"the expected outcome, not a regression"*, and now records
  that the open half of D21 closed against the interactive surface.
- **[Claude] `./aws/studio.py` `US-4` went RED the moment the apply landed**, asserting the two-profile
  shape: `missing engineering`. Re-scoped in the same sitting — `experimentation` alone is the contract,
  and `engineering` moved to a `RETIRED_PROFILE_NAMES` list so that its **return** is the failure. A check
  that only knows what it expects cannot report what it found. **`0 check(s) FAILED`** afterwards.
  This is the third instrument pass 5 would have re-scoped four passes too late, and the stage now says so
  at the head of that pass.

---

## 2026-09-06 — step 1.2: the eleven blueprint configurations and their grants

*Provenance: the authorization is the user's, for this specific apply; the edits, both plans, the apply and
every read-back are Claude's. Applied as the **infrastructure user**, account **Development**, permission
set **`InfrastructureAccess`** (profile `awsds-infra-dev`). The vocabulary edit that precedes it is
1.6's, taken here as the corrected stage says.*

- **[Claude] The vocabulary edit, one commit**: `development` out of **both** `SMUS_MEMBERS` and
  `SMUS_ASSOCIATED`. Regenerated tfvars: `blueprints_enabled = false` for the member slice,
  `profiles_enabled` still **true** for governance, and its `members` map down to `sandbox` alone.
- **[Claude] The vocabulary told me not to shrink a third list, and it was right.** The derivation
  `PERSONA_VENDING_ACCOUNTS = list(SMUS_MEMBERS)` would have dropped `persona_vending_policy_name` from
  `development/foundation/` at this moment — while `DataScientistAccess` is still assigned to that account
  until step 2.1 — leaving the slice carrying a destroy blocked by `prevent_destroy` for a whole pass. The
  comment above that constant already said what to do: *"THIS LIST FOLLOWS THE ASSIGNMENTS, not the
  members"*. Replaced by the literal for the window, with its expiry written into the comment; step 2.2
  restores the derivation.
- **[Claude] The two gates before the apply, both `No changes`**: `data-governance/governance/` (which is
  1.6's proof that `profiles_enabled` did not flip and `experimentation` survived) and
  `development/foundation/` (the payoff of the paragraph above).
- **[Claude] Plan: `0 to add, 1 to change, 22 to destroy`**, read out of the saved plan before applying:

  ```
  delete   awscc_datazone_environment_blueprint_configuration  x11
  delete   awscc_datazone_policy_grant                         x11
  update   aws_kms_key                                         x1
             module.sagemaker_prereqs.module.project_key.aws_kms_key.this
  ```

  The `1 to change` is the project CMK losing the domain execution role from
  `AllowKmsKeyUsageForSageMakerDomain` and every statement gated on the domain id — predicted in the
  preparation sitting by reading the module, confirmed here by the plan.
- **[user]** Authorized the apply. **[Claude]** Applied the saved plan. **One apply, one plan — Recipe F
  was not needed**, which answers this stage's verification 1: the provider orders each grant before its
  configuration by itself. Re-plan **`No changes`**.
- **[Claude] Read-back (step 1.3), and the step had asked the second call for an answer it cannot give.**
  `list-environment-blueprint-configurations` from the member returns **0 items**, succeeding — the
  association is still in place, which is what step 1.4 removes. But `list-policy-grants` on the grant's
  own entity raises
  `ValidationException: Environment Blueprint Configuration with id: 4k186sfh08eqxc does not exist in
  account: <Development Account>` — it **cannot** return empty, because the grants `for_each` rides the
  configurations and the entity they hang off went with them. An error and an empty list are different
  outcomes; only one of them was available here, and the stage now says which call gives which.
- **[Claude] `./aws/studio.py` after the apply: `0 check(s) FAILED`.** `US-3` for this account reads
  `note — none - the association exists (step 1.3, measured above), so what is left is step 1.4`, which is
  the intermediate state named correctly. Unlike `US-4` at step 1.1, this check already had the branch.

---

## 2026-09-06 — steps 1.4 and 1.5: the account leaves the domain

*Provenance: the console disassociation is the **user's**, performed in the **Data Governance** account as
the **Infrastructure User** through **`InfrastructureAccess`** — the identity that made the association on
2026-08-21. Every reading and every edit below are Claude's, read-only against AWS.*

- **[user]** Disassociated the account from domain `awsds-studio`.
- **[Claude] Read-back, first half — it FAILS now, and that is the answer.**
  `list-environment-blueprint-configurations` from `awsds-infra-dev` raises
  **`UnauthorizedException: Unauthorized`**. It returned `0` items, succeeding, one step earlier. Not an
  access-denied naming a policy — the domain is simply no longer shared into the account. **This answers
  the stage's verification 2**, and it is 6a step 1.3's proof exactly in reverse.
- **[Claude] Read-back, second half.** `ram get-resource-shares --resource-owner OTHER-ACCOUNTS` returns
  **two** shares, both `ACTIVE`: `LakeFormation-V4-FNJKZUVEM0` and `LakeFormation-V4-UQFJZDWRUL`. The
  `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` share is gone with the association.
- **[Claude] `./aws/rename-check.py`: `RC-3` and `RC-4` are now `pass`** — *"no domain visible - the
  association is gone"* and *"no DataZone share held - the disassociation (step 1) has landed"* — with
  `RC-4b` still noting the lake's two, which belong to step 2.3. **This is what the RC-4/RC-4b split bought:
  unsplit, the check would still be reporting "the console disassociation has not run" about a step that
  had just run.** `0 check(s) FAILED`.
- **[Claude] `./aws/studio.py` needed a third state, and got one.** Its two "nothing here" notes read
  *"correct **before** this account's association"* — green, and describing the wrong side of the event:
  an operator would be told the association is **pending** when it was **retired**. Added
  `RETIRED_MEMBER_PROFILES` for the state this file had no name for — a member whose association was
  removed on purpose, whose OU has not changed yet, so `datazone:*` is not denied and it is not headless
  either. Both notes now name the retirement and the row leaves with the profile rename at 5.1.
  `0 check(s) FAILED`.
- **[Claude] Two of the stage's four verifications are now answered**: 1 (no Recipe F needed) and 2 (the
  call fails rather than returning empty).

---

## 2026-09-06 — step 1.7: the slice is gone, and the two-commit shape did not survive the gates

*Provenance: the authorization is the user's; the edits, the plan, the apply and the read-backs are
Claude's. Applied as the **infrastructure user**, account **Development**, permission set
**`InfrastructureAccess`**.*

- **[Claude] The bucket needed no emptying.** `list-object-versions` on `awsds-dev-smus-projects`:
  **0 versions, 0 delete markers**. The step says "list and empty by hand" and the listing is what says
  there is nothing to empty — pass 0's "no project" seen a third way, after `US-8` and `US-4`.
- **[Claude] The module call was removed rather than the flag lifted.** The projects bucket comes from
  `terraform-modules/s3-bucket`, which hard-codes `prevent_destroy = true` and `force_destroy = false` and
  whose own comment says the flag *"cannot be parameterised"*. Removing the call removes the lifecycle
  block with it.
- **[Claude] Plan read before applying: 14 resources, every one a delete** — two service roles, two policy
  attachments, the D13 boundary policy, the project CMK, its alias, a CloudWatch log group, and the bucket
  with its five configuration resources.
- **[user]** Authorized. **[Claude] Applied: `0 added, 0 changed, 14 destroyed`.** Re-plan `No changes`.
- **[Claude] The project CMK is `PendingDeletion`, `DeletionDate` **2026-10-06** — the date this step asks
  for. `alias/awsds-dev-project` no longer resolves and `head-bucket` on the projects bucket returns
  **404**.
- **[Claude] The two-commit split failed at the hook, and the failure is the finding.** The first commit —
  "the configuration that permits the destroy" — was **rejected by tflint**: with the module call gone, the
  slice's three `terraform_remote_state` data sources and one variable are unused
  (`terraform_unused_declarations`, four warnings, exit 2). That intermediate configuration is not a state
  this repository accepts. The runbook's two-commit rule is for lifting `prevent_destroy` on a resource
  that **stays**; a whole-slice teardown applies from the working tree and commits the **end** state. The
  folder and its `scripts/tfhygiene/layers.py` row went in one commit, and the stage now says so.
- **[Claude] Documents revised in the same sitting**, as the rule requires: `docs/NETWORK.md`'s row for the
  two `sagemaker/` slices loses this one, and `terraform-live/README.md`'s *"applied twice, so the two
  accounts cannot drift"* becomes a dated past tense. `conventions.md` §6, `D21` and `INT-15` still name
  the slice and belong to step 5.3.

- **[Claude] Step 1.8, which closes pass 1**: `./aws/studio.py` reads **`0 check(s) FAILED`** — one
  associated account, `US-4` `pass` at one project profile, and every row about this account naming the
  **retirement** rather than a pending association. `US-8`'s note lost the word *"yet"* in the same
  sitting: with the two service roles and the boundary destroyed at 1.7, no blueprint-provisioned role
  will ever appear here, and a note saying one has not appeared *yet* points at a future that is not
  coming. **Pass 1 is complete.**

---

## 2026-09-06 — pass 2 begins: step 2.1, the persona swap

*Provenance: the user authorized the remaining Claude-only steps of the plan in one instruction; every
edit, plan, apply and read-back below is Claude's. Applied as the **infrastructure user**, account
**Identity**, permission set **`InfrastructureAccess`** (profile `awsds-infra-identity`).*

- **[Claude] Applied: `1 added, 0 changed, 2 destroyed`.** `data-scientist@development` is a **replacement**
  — the permission-set ARN is a forced-replacement field, and because the map KEY was deliberately left
  alone the resource address did not move. `dev-env-steward@development` is a plain delete. Re-plan
  `No changes`.
- **[Claude] Read back from Identity Center, not from state**: the account carries **six** permission
  sets — `DataScientistStagingAccess`, `DeploymentManagerAccess`, `InfrastructureAccess`, beside the
  landing zone's `AWSOrganizationsFullAccess`, `AWSPowerUserAccess` and `AWSReadOnlyAccess`. That is the
  count step 0.3 corrected the stage to expect; the old prose said "three permission sets" and would have
  read this as wrong.
- **[Claude] Two comments went in with the edit**, both recording a *reason* the estate had contradicted:
  the map key stays `@development` until 4.6's `moved {}` blocks, and the steward seat leaves for D14's
  reason (the registry is ECR in Production) rather than for the false one this step used to give.

- **[Claude] Step 2.2, in two commits, applied as `awsds-infra-dev`.** Commit 1 lifted `prevent_destroy`
  alone and the plan after it read **`No changes`** — a lifecycle flag changes no resource, which is
  exactly why it is its own commit. Commit 2 removed `persona-vending.tf`, its `nullable = false`
  variable and the `PERSONA_VENDING_ACCOUNTS` literal in one edit, and applied
  **`0 added, 0 changed, 1 destroyed`**. Re-plan `No changes`.
- **[Claude] The step's implied intermediate state does not exist.** With the resource still declared and
  the tfvar no longer emitted, Terraform refuses to load the slice at all — *no value for required
  variable* — because the variable is `nullable = false` with no default. So the object, its variable and
  the vocabulary restoration are necessarily **one** commit; only the guard can be separated. Same family
  as 1.7's finding, from the other direction: there the gate refused the intermediate state, here the tool
  does.
- **[Claude] Read back in BOTH accounts, which is the check.** `awsds-org-project-storage-vending` is gone
  from this account and **still present in Sandbox**, whose `DataScientistAccess` references it by name. A
  per-account object removed from the wrong account is a provisioning failure in an account nobody is
  watching — the failure the guard existed to prevent.

- **[Claude] Step 2.3, applied as `awsds-infra-data`: `0 added, 6 changed, 2 destroyed`.** The **2
  destroyed** are the TBAC triples — `share_databases["development"]` and `share_tables["development"]`.
  The **6 changed** are the **five lake bucket policies and the data CMK's key policy**: dropping the row
  from `DATA_CONSUMERS` removes that account's root principal *and* its S3 gateway endpoint from
  `local.trusted_vpce_ids`, which is INT-05's `aws:SourceVpce` allow-list. The stage said "the two
  triples"; the preparation sitting added the perimeter half by reading `locals.tf`, and this plan is that
  reading measured. Re-plan `No changes`.
- **[Claude]** `lakeformation list-permissions` filtered on that account: **2 → 0**. Six rows of the grant
  register in `docs/AWS_STATE.md` annotated **REVOKED 2026-09-06** — struck through, dated, **none
  deleted**, as the register's own rule requires.

- **[Claude] Step 2.4, applied as `awsds-infra-dev`: `0 added, 0 changed, 5 destroyed`** — two Glue
  resource-link databases, the account's `aws_lakeformation_data_lake_settings`, and the account data CMK
  with its alias. State empty afterwards; the folder and its `layers.py` row removed in the same commit,
  on 1.7's finding that a whole-slice teardown commits the end state.
- **[Claude] The stage named the wrong blocker, and the correction matters for the next consumer.** It said
  the slice "cannot be converted — its `data.tf` resolves `AWSReservedSSO_DataScientistAccess_*` with
  `one()`, which fails at plan time the moment 2.1 lands". **`one()` returns null on an empty collection**
  and errors only on two or more, so 2.1 would have fed a silent null into the module. What actually stops
  the slice is step **2.3**: dropping the account from `DATA_CONSUMERS` stops emitting the `lake` variable,
  which is `nullable = false` with no default, so Terraform cannot **load** the slice at all. The
  configuration was stripped, exactly as at 1.7.
- **[Claude] A prediction of mine that the measurement refuted.** Reading the plan's 5 deletes against the
  state's 11 entries, I took the four `aws_lakeformation_permissions` for orphans that Terraform could no
  longer see — a grant naming a role deleted at 2.1. **`list-permissions` in the account reads `0` after
  the apply**: they went with the resource links and the share. No orphan, and the state came back empty.
- **[Claude] `aws_lakeformation_data_lake_settings` "destroy" is a RESET.** The account came back with
  `CROSS_ACCOUNT_VERSION=1` and an **empty administrator list** — AWS defaults, not an absence. Read as a
  consumer that is exactly `DL-5` and `DL-13` failing; read as what the account now is — no share, no
  resource link, no catalog object — it is the resting state. **`DL-6` did not revert**: no
  `IAMAllowedPrincipals` default came back, which is the one that would have mattered.
- **[Claude] Step 2.5, and the fifth instrument to be re-scoped at the step that moved it.**
  `datalake.py`'s `CONSUMER_PROFILES` is now one profile, with the reset above written into the comment so
  the next reader does not re-diagnose it as drift. Then: `datalake.py` **`0 check(s) FAILED`**, `DL-7` at
  **2 resource links** (from 4); `rename-check.py` turns **RC-5 and RC-6 to `pass`** — six permission sets,
  no Lake Formation grant naming the account — leaving **only RC-1 and RC-2**, the rename and the OU move.
  **Pass 2 is complete, and everything that does not depend on the user is done.**

---

## 2026-09-06 — steps 3.1 and 3.8: the switch is on, and the Workloads ceiling gains the deny early

*Provenance: **step 3.1 is the user's** — `enable-aws-service-access --service-principal
account.amazonaws.com`, run in CloudShell on Management, no output, which is its success. Everything else
is Claude's, applied as the **infrastructure user**, account **Identity**, permission set
**`InfrastructureAccess`**.*

- **[Claude] 3.1 read back**: `./aws/org-trusted-access-services.py` section 1 now reports **PRESENT** for
  `account.amazonaws.com`, so `put-account-name --account-id` is available and **3.2 is unblocked**.
  `INV-09` restated — **ten** principals, not nine; `account` is the fourth this project turned on, holds
  no delegation, and the delegated count stays four.
- **[Claude] 3.8 taken BEFORE the OU move, deliberately.** The step is listed after 3.4 and does not depend
  on it, and the order matters in one direction only: applied first, the account **never spends a moment in
  `Workloads` without the deny it carried in `Interactive`**; applied after, that window is real. Applied
  **`0 added, 1 changed, 0 destroyed`**, re-plan `No changes`, and the document read back from
  Organizations carries three Sids. The statement was **copied verbatim** — three actions,
  `arn:aws:athena:*:*:workgroup/*` — not paraphrased.
- **[Claude] `EXC-03` named this event in advance, and it arrived.** That row says *"the row to watch is
  the contrast one — if it ever turns into a denial too, the pair stops attributing"*. Production **was**
  the contrast precisely because its OU document carried no athena action at all; the amendment ends that.
  The contrast moved to **`Policy Canary`**, whose `Policy Test` OU carries no project SCP.
- **[Claude] The battery re-run the same day, `--phase ou`: `25 as expected, 0 unexpected, 8 not
  measured`.** `prod` now reads `deny / DENY-NOT-SCP` beside the two Interactive rows; the canary reads
  `allow / ALLOWED / reached-authorization`, so the trio still attributes. **1.6's negative probe still
  passes** — *"interactive: athena:StartQueryExecution STILL WORKS"* — which is the one that matters: the
  amendment denies **Spark**, not SQL, and D13's query path is untouched. The eight not measured are the
  standing `no subnet in us-west-2` rows in Data and Identity, unrelated.
- **[Claude]** `POLICIES.md` gained its row and `./scripts/check-index.py` is clean; `EXC-03` rewritten
  with the move and its date.

- **[Claude] A contradiction between the stage and its own authority, settled by measurement.**
  `docs/plan/conventions.md` §6 — the authoritative slice tree — said `development/egress/` would be
  **destroyed**; step 4.3 said it would **migrate**, arguing that a slice left in the old folder is a slice
  on the old state bucket. **Both `[E]` slices were read instead: `egress/` and `probes/` hold ZERO
  resources**, because D11 leaves them torn down between sittings. So neither word was right: there is
  nothing to destroy and nothing to migrate. Their folders move with a `git mv` and their state is created
  fresh at the next `up`; **`foundation/` is the only surviving slice that actually needs Recipe E.** Both
  files now say that, and the two other `conventions.md` §6 lines that had gone false — the consumer-side
  `data/` caller and the lake's share list — were corrected with them.

## 2026-09-06 — steps 3.2 to 3.7: the account is renamed, it is in `Workloads`, and the battery follows it

*Written by Claude at the user's request, same day. The console acts are the user's and are named as
such; every reading is Claude's, as the infrastructure user.*

- **[user] Step 3.2 — the account is `Staging Account`**, and the **root e-mail was changed in the same
  sitting**, which the step did not ask for. Recording it because it is a fact about the account that no
  later reading explains: the vended-name pattern and the root address now agree.
- **[Claude] Read back with `./aws/rename-check.py` the same day. `0 check(s) FAILED`, and it is the
  first time this file has read the AFTER column**: `RC-1 pass — Staging Account` (exact match against
  the ACTIVE roster, never a prefix), `RC-2 pass — Workloads`, `RC-3 pass`, `RC-4 pass — no share held`,
  `RC-5 pass`, `RC-6 pass — no grant names the account`. **No propagation delay was observed** between
  the console act and the read, which the step had flagged as undocumented.
  - **`RC-3` answered from the other side of the cut, and that is the reading the file was written for.**
    It no longer says *"no blueprint configurations"*; it says **`datazone` is denied in this account —
    the Workloads ceiling is in force**. The MIXED case this instrument exists to catch — an account
    already in `Workloads` still holding DataZone objects it can no longer delete — did not happen,
    because pass 1 emptied the surface while the account was still in `Interactive`. **The step order
    was the control, and this is its evidence.**

- **[Claude] Step 3.3 — the two name-keyed sites re-pointed, and the gate is an empty plan.** The
  **values** changed in `terraform-live/identity/sso/locals.tf` and `aws/import-ids.py`; the **keys** did
  not (`development` stays the for_each key until 4.6 moves it behind a `moved {}` block). Re-planned
  `identity/sso/` as `awsds-infra-identity`: **`No changes`**. The precondition that fails the plan when
  the name does not resolve now resolves it, and not one assignment moved.
  - A third site was corrected in the same commit and it is **prose, not code**: `import-ids.py`'s header
    said *"`Staging` arrives at the vend"* — the vend the quota refused, which is the reason this stage
    exists. It now states why the key and the value disagree between 3.2 and 4.6.

- **[user] Step 3.4 — the account is in `Workloads`. [Claude] Measured two independent ways, and the
  path it took is still unread.** `RC-2` reads it from `organizations list-parents`. The stronger
  reading is the battery's, because it is the **ceiling answering rather than the directory**: the
  us-east-1 deny in this account is attributed to **`p-i0ney7mx`, the same policy id Production
  returns**, where `Sandbox Account 1` returns a different one. Same id, same OU, said by a denial.
  - **What this side cannot distinguish is Control Tower *Update account* from
    `organizations move-account`**, and the difference is not cosmetic — the second strands the Account
    Factory provisioned product on the old OU under the old name and raises `Moved member account` drift
    when the two OUs differ, which auto-enrollment re-baselines but does not un-drift. Both are visible
    only from Management, which holds **no CLI profile**. **The user reports Service Catalog still
    showing the old provisioned product**, which is consistent with either path — the provisioned
    product's *name* is fixed at vend time and never follows a rename. **The parameters are the reading
    that settles it, and it is owed from that console.**

- **[Claude] Step 3.6 — D32's trigger did NOT fire, and the caveat is half the answer.**
  `./aws/list-identities.py` §5.2: `Staging Account` carries **six** assignments — the three landing-zone
  group ones and this repository's three (`InfrastructureAccess`, `DeploymentManagerAccess`,
  `DataScientistStagingAccess`). **No direct `USER` assignment and no `AWSAdministratorAccess`**, so
  `INV-05` and the roster row stand unedited and `Policy Canary`'s remains the only direct D32 assignment
  in the organization.
  - **This does not yet close Stage 1b verification (vi).** That verification watches for the direct
    assignment returning *when an account update runs*; whether one ran is exactly what 3.4 cannot read
    from here. A reading that looks identical on *"it did not fire"* and *"it was never triggered"* is
    not a verification (Lesson 13), so the row stays open pending the Management console reading.

- **[Claude] Step 3.7 — the battery follows the account, and the `ou` phase was a re-composition rather
  than a retarget.** Token `dev` → `staging` in **both** files (`scp-battery.py`'s `PROFILES`, where a
  missing token stops the run, and `probes.py`, where it is every probe's second argument); no `dev`
  string survives under `aws/probes/`. **Full battery, every phase: `89 as expected, 0 unexpected, 10 not
  measured`** — all ten notes the by-design ones.
  - **The step's own first sentence was wrong, and 3.8 is why.** It predicted the account would **lose**
    `DenyAthenaSparkStartSession` because that Sid *"exists only in the Interactive document"*. It did
    not: 3.8 had put the Sid into the Workloads document hours earlier, deliberately before the move, so
    the account **crossed carrying the deny instead of into a gap**. The rest held exactly — it lost
    `DenyClassicNotebookInstances` (fully absorbed by `DenyInteractiveSageMakerSurface`) and gained that
    Sid and `DenyDataZoneEntirely`.
  - **A pure token flip would have made the battery lie by duplication.** Three of the five `dev` `ou`
    rows asked questions `prod` and `sandbox1` already ask; flipping them would have produced a third
    copy of each, and a probe count that no longer means a question count is what this file's own
    comments warn against. So: **two `allow` rows moved to `sandbox1`** (`sagemaker:CreateSpace`,
    `datazone:ListDomains` — the block's entire point is that decision 1 costs no feature, and deleting
    them would have left the Interactive document with **no permissive evidence at all**); **three rows
    deleted**; **one new row added for `staging`**.
  - **The Interactive sample is now an inherited one, and it is not weaker.** Nothing sits directly in
    `Interactive` any more and no account can restore that. But an SCP can only **deny**, and `Sandboxes`
    carries no document of its own — the probe directly below those two rows is that evidence — so an
    `allow` observed under Interactive+Sandboxes is at least as strong as one observed under Interactive
    alone. Both passed.
  - **The one row added asks something none of the others do**: not *is the Workloads document in force*
    but *did the account this stage moved actually acquire it* — a question about a membership rather
    than a policy, and worth keeping permanently because this is the account that will hold deploy
    credentials. It came back **`DENY-SCP p-83t232f4`, the same id Production's three rows return**.
  - **The silent half of the flip was the tag values, and it is the half that would have gone
    unreported.** Two probes hard-coded `Environment=development` in their `--tag-specifications`. The
    tag policy allows all six values org-wide, so neither would have **failed** after the flip — they
    would have quietly asserted a value nothing carries, which is worse than a failure. Both now read
    `staging`, confirmed an allowed value in `awsds-org-tag-policy.json`.

## 2026-09-06 — step 4.2, and the instruments that broke the moment the profile was renamed

*Written by Claude, same day. Every reading is Claude's, as the infrastructure user.*

- **[Claude] Step 4.2 — `terraform-live/staging/bootstrap/` written, planned, NOT applied.** It is the
  sixth bootstrap slice and Recipe E step 2's precondition: the destination bucket must exist before any
  `-migrate-state` can name it. The parity check accepts it — byte-identical to the reference, with
  `backend.tf` in the **sanctioned phase-1 commented form**, which is the one legitimate difference the
  check is built to tolerate. A first attempt added three lines of prose explaining the phase and the
  check failed it: parity compares the file **with the comment markers removed**, so explanatory prose
  inside that file is content, not commentary. The header already carries the explanation.
  **Plan: `8 to add, 0 to change, 0 to destroy`** → `awsds-staging-tfstate` and
  `alias/awsds-staging-tfstate`. **The apply was refused by this session's own tooling**, not by AWS and
  not by the user, and the saved plan is what the apply will consume unchanged.
- **[Claude] `PROFILES["development"]` was re-pointed rather than left alone, and that is the finding.**
  Step 5.0 renamed `awsds-infra-dev` → `awsds-infra-staging` in `~/.aws/config`, so **the old spelling
  now resolves to nothing**. Two folder keys naming one profile is a **window, not a design**: it closes
  at 4.7, when `development/bootstrap/` goes with the bucket every other migration reads from.
- **[Claude] A hazard found while reading Recipe E against this repository, and it is worth writing
  down before pass 4 runs it.** Recipe E step 3 says to `git mv` the folder and **regenerate the backend
  configuration, leaving the tfvars alone** — that is what makes step 5's `No changes` meaningful. In
  this tree the tfvars are **generated from the folder key**, so regenerating them *is* the token flip.
  The two are separable only because `terraform.auto.tfvars` is untracked and moves with the directory:
  **the migration must run `gen-backend-hcl.py` alone and never `gen-tfvars.py`.** Which makes
  `./scripts/slices.py` unusable for that one step — its `prepare()` regenerates the tfvars before every
  `init`, so `slices.py up` would flip the token silently, inside the very step whose gate is that
  nothing changed. `terraform` is called directly for 4.3, deliberately.

- **[Claude] Six instruments stopped resolving the moment 5.0 ran, and they were fixed now rather than
  at pass 5.** The stage's own pass-5 header is the reason: *"a check that is red for four passes is a
  check nobody reads on the fifth."* Every one of these named the profile, and a profile that does not
  exist produces a failed call rather than a finding.
  - `studio.py` — dropped from `INTERACTIVE_PROFILES`; `RETIRED_MEMBER_PROFILES` is **empty again** and
    kept rather than deleted, because that third state is not hypothetical: it was invented at 1.5 and
    held one row for the few hours between the disassociation and the OU move. **`HEADLESS_PROFILES`
    already carried `awsds-infra-staging`** as a promise; it is now an account, and the run says so —
    **`US-6 pass — datazone reads denied in awsds-infra-staging`**, which is D28's headless control
    holding, measured from the account rather than inferred from the OU.
  - `cicd.py` — the row was **deleted, not retargeted**. It named a dev-env *registration* home beside
    Sandbox; the account is a **deploy target** now, and it already appears one row up as
    `awsds-deploy-staging`, a different role for a different job. Interactive compute is Sandbox-only
    since the 2026-09-05 re-scope, so that map has one dev-env home **by design rather than by attrition**.
  - `supplychain.py`, `dlp.py`, `networking.py` and six usage-example comments — retargeted.
  - **`rename-check.py` keeps BOTH spellings on purpose** and the comment now says why it keeps a row
    that no longer resolves: the config edit and the AWS-side rename do not happen in the same second,
    and this is the file that has to keep reading across that gap.
  - **One thing was flagged instead of fixed, and the choice is the point.** `networking.py`'s `NT-5` and
    `NT-6` assert that nothing routes or peers into `10.40.0.0/16` and print *"Staging is deliberately
    unpeered (D20)"*. The assertion stays true; **the sentence is about to become false** — that vend
    never happened, the account called Staging lives at **10.50** and IS peered to Production, and 4.1
    frees 10.40 for 6c to spend. A check whose message and whose assertion disagree is read by whoever is
    debugging at the time, so the file now carries the dated warning and the rewrite waits for 4.1 to
    land and give it a measured allocation to name.

## 2026-09-06 — step 3.4 confirmed by the user, and Recipe E step 1 taken

- **[user] The OU move was done "via console AWS".** Recorded in the user's own words because the
  distinction that matters — Control Tower *Update account* versus the Organizations console, which is
  `move-account` under a different button — is not one to settle from memory. **3.5 settles it, and 3.5
  is the same act either way**: Control Tower *Update account* is the read-back, and if the move went
  through Organizations it is also the repair, because that path leaves the Account Factory provisioned
  product on the old OU under the old name.
  - **[Claude] What to expect from that act rather than discover**: it is exactly the account update
    Stage 1b verification (vi) has been waiting for. If a direct `AWSAdministratorAccess` assignment
    reappears afterwards, it is **expected** — the row gets restated, not reported. If it does not, (vi)
    closes in the negative, which is the answer 3.6 could not give on its own.

- **[Claude] Recipe E step 1 — the baseline, taken before the move rather than after it.**
  `development/foundation/` initialised against the OLD backend (`awsds-dev-tfstate`, key
  `development/foundation/…`) and planned: **`No changes`**. The state is now cached locally, which is
  what that step exists to produce.
  - **The reason to take it first is the reason the recipe orders it first**, and it is worth stating in
    the log because it is the kind of step that looks skippable: with a clean baseline, a non-empty plan
    on the far side of the migration **is the migration**. Without one, a non-empty plan is ambiguous
    between the migration and drift that was already sitting there — and the whole gate of Recipe E step
    5 is that the plan is empty.
  - **The generated `peers` map already carries both keys**, `development` and `staging`, both resolving
    to `awsds-infra-staging`, because 4.2 added the `staging` PROFILES row while `staging` was still in
    `CIDRS`. **Checked rather than assumed**: `production/foundation/peers.tf` builds
    `local.peer_vpc_ids` as a hand-written two-row map and never iterates `var.peers`, so the extra key
    is inert. The opposite would have been a third VPC peering proposed by a plan nobody was reading for
    that.

## 2026-09-06 — steps 4.2 and 4.3: the tree moves, and the gate is an empty plan

*The 4.2 apply is the user's; everything else Claude's, as the infrastructure user.*

- **[user] Step 4.2 applied: `8 to add, 0 to change, 0 to destroy`** → `awsds-staging-tfstate` and
  `alias/awsds-staging-tfstate`, both read back (`Enabled`/`CUSTOMER`).
- **[Claude] Phase 2 of the bootstrap pattern, same sitting**: backend block uncommented,
  `init -backend-config=backend.hcl -migrate-state` into the bucket the slice had just created, the two
  local state files deleted, re-plan **`No changes`**. Every bootstrap slice in this tree does this once;
  this is the sixth.
  - **The parity check rejected the first attempt and the reason is worth keeping.** Three lines of prose
    were added above the commented backend block explaining the phase. Parity compares that file **with
    the comment markers stripped**, so prose inside it is *content*, not commentary, and the slice read
    as diverged from the reference. The file tolerates exactly two forms — commented and live — and the
    explanation already lives in the header every copy shares.

- **[Claude] Step 4.3 — the gate passed.** `git mv` moved `foundation/`, `egress/` and `probes/` into
  `staging/`; `development/bootstrap/` stayed. `terraform plan` after `init -migrate-state`:
  **`No changes`**, with the same gateway-endpoint ids the baseline had shown, so the state arrived
  intact rather than being rebuilt.
  - **The tfvars were NOT regenerated, and that is the whole of Recipe E step 3.** The untracked
    `terraform.auto.tfvars` travelled with the directory still reading `env = "dev"`,
    `environment_tag = "development"`, `vpc_cidr = "10.50.0.0/16"`. Only `gen-backend-hcl.py` ran. That is
    what makes the empty plan mean *the migration worked* rather than *nothing was compared*.
  - **Step 4.1 was split in two, and the half that was NOT done is the interesting one.**
    `CIDRS["staging"]` became `10.50.0.0/16` in this same commit — it had to, because the tfvars are
    generated from the folder key and a `staging` folder reading the old `10.40` allocation would have
    proposed **replacing the VPC**. But the `development` row was **kept** and 10.40 is **not free yet**:
    `production/foundation/peers.tf` reads `var.peers["development"]` by literal and that map is built
    from this table's KEYS, so deleting the row breaks another account's slice until 4.5 re-points the
    four hand-written provider aliases. Recipe E step 8 in one sentence — *keep the old vocabulary rows
    alive* — applied to the one table another account reads. **6c step 0 must not spend 10.40 until 4.5.**
  - **The two `[E]` slices were migrated after all, and the step said they need not be.** It was right
    about the *necessity* and wrong about the tidiest path. Zero resources is still a state OBJECT with
    a lineage — measured, 749 and 697 bytes in the old bucket — and their `.terraform/` directories moved
    across still pointing at `awsds-dev-tfstate`, **a bucket step 4.7 destroys**. Left alone they would
    have made the next `make up` stop and prompt for a backend change in a slice nobody was thinking
    about. Two `init -migrate-state` calls, no plan gate, because a torn-down slice has nothing to gate.
- **[Claude] Four documents reviewed in the same sitting, which is where the mechanical gates earn
  their keep.** `./scripts/check-network-doc.py` went red immediately on three renamed slices and is
  green again; `conventions.md` §6 gained a real `staging/` entry and `(development/)` shrank to the one
  slice it still has; `terraform-live/README.md`'s account table had `development/` pointing at a profile
  that no longer exists and `staging/` described as *"none yet — the account is unvended"*, and its
  opening line still said **five** bootstrap slices. Only the first of those four was caught by a gate.

## 2026-09-06 — step 4.4 planned and read, and step 4.5 turns out to be bigger than its own text

*Claude, as the infrastructure user. No apply in this entry: every `terraform apply` in this session is
refused by the tooling, so the plan is read and saved and the apply is handed over.*

- **[Claude] Step 4.4 planned: `8 to add, 16 to change, 8 to destroy`**, and the shape is the predicted
  one. **The VPC, all six subnets, both gateway endpoints, all four route tables, the internet gateway
  and `aws_vpc_peering_connection.to_production` are IN-PLACE tag changes** — every id survives, which is
  what INT-05's anchors and the peering rest on.
  - **The step named five replacements; there are eight, and all eight are one class.** Predicted: the
    four security groups and the flow-log **log group**. Unlisted and also replaced: the flow-log **IAM
    role** (its name is `awsds-dev-vpc-flow-logs` — an input built from the env token, exactly the class
    the step describes), **its inline policy**, and **the flow log itself**, which binds role and group
    and cannot outlive either. The rule the step states is right; its enumeration was short. The usable
    form is *"every resource whose NAME is built from the env token, plus whatever binds them"*.
  - **Checked rather than assumed: nothing outside the account is replaced.** The lake's
    `trusted_vpce_ids` stopped naming this account at 2.3 and the gateway endpoints keep their ids
    regardless; the two `[E]` slices that read this state are torn down.

- **[Claude] Step 4.5 read before being written, and it does not do what its own text implies.** The
  step describes an edit to the accepter side and four provider aliases. What it omits is that
  `development` is a **`for_each` key** in `production/foundation/peers.tf`, not merely a name — and an
  address change is a destroy-and-create. **Applied as written, it would delete the peering
  connection**, because destroying an `aws_vpc_peering_connection_accepter` destroys the peering with it.
  - Four addresses need `moved {}` blocks and they are all cheap: the accepter's literal key, the two
    Route 53 authorization keys (`prod.development`, `pages.development`), and two resources whose
    *names* carry the token while their `for_each` keys do not — one block each covers every instance
    there.
  - **`aws_route.return` is the deliberate exception.** Its keys embed a `[P]` subnet id
    (`"<route-table>|development-private-<subnet-id>"`), so a `moved {}` block would have to paste those
    ids into a tracked file — which is precisely what `peers.tf`'s own header forbids: *"the peer's facts
    are READ, NEVER PASTED"* (Lesson 3). **Those routes are re-created instead.** The destination CIDRs
    do not change, a route is idempotent and cheap to rebuild, and the far end is `[E]` and torn down —
    so the cost is seconds on a path nothing is using, against a stale id living in the tree forever.
  - **This is the second time in this stage that a step's *rule* was right and its *list* was short**
    (4.4's replacements were the first, hours earlier). Both were caught by reading the plan instead of
    running it, which is the only reason Recipe A step 5 says to save the plan to a file and read it.

## 2026-09-06 — steps 4.4, 4.5 and 4.6: the token flips, and three `moved {}` blocks keep it boring

*The 4.4 apply is the user's; the planning, the code and the readings are Claude's. 4.5 and 4.6 are
planned and saved, not applied — every `terraform apply` in this session is refused by the tooling.*

- **[user] Step 4.4 applied. [Claude] Re-plan `No changes`, and the outputs are the verification.**
  **`s3_gateway_endpoint_id = vpce-0a222aef0c577abbb` and
  `dynamodb_gateway_endpoint_id = vpce-0d70ec5dc14566c45` — byte-identical to the pre-move baseline.**
  INT-05's anchors survived a folder rename, a state migration and a token flip in one day, which is
  what step 4.1 was protecting when it moved `CIDRS["staging"]` to 10.50. The two private route tables
  kept their ids as well; **all four security groups came back new**, as planned.

- **[Claude] Step 4.5 planned: `4 to add, 1 to change, 4 to destroy` on `production/foundation`.** The
  one change is **`aws_vpc_peering_connection_accepter.peer["staging"]` updated IN PLACE** — a tag,
  nothing more. That is the entire point of the five `moved {}` blocks: **eight addresses moved in
  state and the peering was never touched.** Without them this plan would have destroyed the accepter,
  and destroying an accepter destroys the peering connection.
  - The four adds and four destroys are `aws_route.return`, the exception taken deliberately, with
    **unchanged destination CIDRs** — Production's private route tables lose four routes and get four
    back under keys that say `staging`.
  - **`production/registry`: `No changes`.** Predicted, and worth having confirmed rather than assumed:
    the renamed provider alias reaches the same account, so the id behind it is unchanged and none of
    the four policies that enumerate consumers moved a byte.
  - The file's own "WHAT IS DELIBERATELY NOT HERE" list opened with *"No peering to Staging (6.6, D20 —
    a decision, not an omission)"*. **That sentence died today.** D20 reasoned about a Staging account
    this project never vended; the account called Staging is the one this file has peered to since
    Stage 3. The topology did not change — the name the same VPC answers to did.

- **[Claude] Step 4.6 planned: `0 to add, 0 to change, 0 to destroy`, which is exactly what the step
  predicts. Three `moved {}` blocks, and the step names two.**
  - **The third is the dangerous one and the plan is what found it.** The step lists the two
    `local.assignments` keys and the `accounts` map key. It does not say that
    **`aws_ssoadmin_account_assignment.infrastructure` `for_each`es over `local.accounts` itself** — so
    renaming that map key moves a third address. Without a block the plan read **`1 to add, 0 to change,
    1 to destroy`: `InfrastructureAccess` REVOKED on the account and re-granted.** That is the
    assignment whoever runs the apply is signed in through, and the two halves are separate
    asynchronous API calls, so the window is real and its length is not ours to choose.
  - **Third time in this stage that a step's RULE was right and its LIST was short** — 4.4's
    replacements, 4.5's `for_each` keys, now this — and all three were caught the same way: by saving
    the plan to a file and reading it rather than running it. That is the only reason Recipe A step 5
    is written the way it is.
  - `aws/import-ids.py` closed its seam in the same commit: the row that deliberately read
    `"Staging Account" → "development"` for one day now reads `→ "staging"`.

- **[Claude] `CIDRS` lost its `development` row and 10.40.0.0/16 is FREE from this commit** — 4.1's
  second half, held back one commit precisely because `production/foundation/peers.tf` read
  `var.peers["development"]` by literal. **6c step 0 can spend 10.40 now.** `REGISTRY_CONSUMERS` kept
  its row, renamed: a deployment target pulls images and packages like anything else, even though the
  same account stopped being a *lake* consumer at step 2.4. That table's comment predicted the two
  lists would diverge one day; this is the day.

## 2026-09-06 — steps 4.5 and 4.6 applied: the peering kept its id and nobody lost access

*User authorised Claude to run the applies for the remainder of this stage. Applies and readings are
Claude's, as the infrastructure user.*

- **[Claude] Step 4.5 applied on `production/foundation`: `4 added, 1 changed, 4 destroyed`**, re-plan
  **`No changes`**. **Read back from AWS, which is the check that matters here**:
  `describe-vpc-peering-connections` returns **`pcx-0999f9d9c55531877  awsds-prod-from-staging
  active`** — the SAME connection id, renamed, and still `active` rather than `pending-acceptance`. If
  the `moved {}` block had failed, this would have been a new `pcx-` in `pending-acceptance`, or
  nothing at all. **The state file said the accepter moved; AWS is what proves the peering was never
  destroyed.**
- **[Claude] Step 4.6 applied on `identity/sso`**, re-plan **`No changes`**. The three `moved {}` blocks
  resolved and no assignment was created or destroyed — including
  `aws_ssoadmin_account_assignment.infrastructure`, whose absence from the step would have revoked and
  re-granted the very access the apply was running through.
- **[Claude] `production/registry` needed no apply at all** — it had planned `No changes`, and that
  reading stands: the renamed provider alias reaches the same account, so the four policies that
  enumerate consumers by account id never moved.

## 2026-09-06 — step 4.7, first half: the old bucket is inspected, unpinned, and its state moved out

- **[Claude] Both buckets read before anything was touched, and it turned up something worth stopping
  for.** `awsds-staging-tfstate` holds `staging/bootstrap` and `staging/foundation`.
  `awsds-dev-tfstate` still holds **six** objects, and one of them — `development/sagemaker` — reported
  **`serial 11 | resources: 2`** in a slice step 1.7 recorded as destroyed.
  - **Both are `mode: data` (`terraform_remote_state` reads of `foundation` and `lake`), not managed
    resources.** A data source stays in state after a destroy because it is re-read rather than
    destroyed. So nothing is orphaned and 1.7's record stands — but *"2 resources"* in a state file
    about to be deleted is exactly the reading that should stop a hand, and the distinction that
    answers it is one field.
  - `development/data`, `egress` and `probes` all report **0 resources**, as expected.
- **[Claude] `staging/egress` and `staging/probes` have NO object in the new bucket, and that is
  correct.** Their migration configured the backend without writing anything, because there was nothing
  to write. Their `.terraform/` caches were read directly and all three moved slices name
  `awsds-staging-tfstate` with the right key, so the next `up` creates state there. What is lost when
  the old bucket goes is two empty states' *lineage*, which is what "created fresh at the next `up`"
  always meant.
- **[Claude] Object Lock: `ObjectLockConfigurationNotFoundError` — genuinely off.** Re-measured rather
  than trusted from the earlier `tf-backends.py` reading, because it is the single property that would
  make the by-hand emptying impossible and this step unexecutable.
- **[Claude] The state was moved OUT of the bucket by returning the slice to LOCAL state, which is a
  refinement of Recipe E step 7 rather than a deviation.** The recipe says to *migrate* `bootstrap/`'s
  own state; its purpose is to get the state out of the bucket about to be destroyed, and the slice is
  being **destroyed**, not moved — so there is no destination that outlives it. Commenting the backend
  block and running `init -migrate-state` is **phase 1 of the bootstrap pattern in reverse**, uses only
  the two forms that file documents, and needs no temporary lie in the vocabulary tables to name a
  bucket the generator would otherwise refuse to produce. `Successfully unset the backend "s3"`.
- **[Claude] `prevent_destroy` lifted, plan on local state `No changes` — and the two-commit shape did
  NOT survive the gates, for the second time in this stage.** The runbook's rule is that
  *"the configuration permits it"* and *"it happened"* are separate reviewable commits. But
  `./scripts/check-bootstrap-parity.py` compares every `*/bootstrap/` slice against the reference, and a
  slice with `prevent_destroy` lifted **has stopped being a copy** — so the intermediate commit fails
  the gate. Removing the folder from the check's lists instead fails it the other way
  (*"development/bootstrap/ is not an account folder this project knows"*). **There is no committable
  intermediate state**, which is exactly what step 1.7 found on 2026-09-06 about a whole-slice teardown.
  The teardown commits the END state, and the working tree carries the un-committed guard-lifting until
  the destroy runs.
- **[Claude] `force_destroy` lifted too, and it REPLACES this step's instruction rather than satisfying
  it.** 4.7 says to empty the versioned bucket **by hand** — measured: **163 object versions and 98
  delete markers**. Doing it through `terraform destroy` makes the emptying a **reviewable code change**
  and a planned operation, instead of a loop of `delete-objects` calls whose blast radius exists only in
  the operator's head. The safety the instruction was buying — that nobody empties a state bucket
  casually — is bought better by that one line being visible in a diff. **Both the apply that sets it and
  the destroy that uses it were refused by this session's tooling**, so the destroy is the user's.

## 2026-09-06 — pass 5 begins: the check that was flagged rather than half-fixed

- **[Claude] `networking.py`'s `NT-3`, `NT-5` and `NT-6` rewritten now that 4.1 has landed**, which is
  why they were flagged a sitting earlier instead of being patched then: there was no measured
  allocation to name. `STAGING_CIDR` is now **`UNALLOCATED_CIDR`**, and the three messages stopped saying
  *"Staging is deliberately unpeered (D20)"* — a sentence that died when the account called Staging
  turned out to be the one those checks' own estate has peered to since Stage 3.
  - **The assertion did not change and that is the point.** Nothing should route or peer into a range
    nobody has allocated; a route that does is either a mistake or an allocation somebody made without
    writing it down. What changed is the sentence a person reads while debugging, which is the half that
    was wrong.
  - **Run: `0 check(s) FAILED`**, and one row is an independent confirmation of step 4.5: **all four
    `NT-8` zone associations now resolve against `awsds-infra-staging`'s VPC** — the Route 53
    associations survived the `moved {}` blocks, read from AWS rather than from state.

## 2026-09-06 — step 4.7 finished: the old bucket is gone and pass 4 is closed

- **[user] Both commands run. [Claude] Read back: `awsds-dev-tfstate` returns 404, the
  `alias/awsds-dev-tfstate` is gone, and `list-buckets` in that account returns exactly one name —
  `awsds-staging-tfstate`.** The KMS key is in its 30-day deletion window, which is the module's
  `deletion_window_in_days` doing what it was written for.
- **[Claude] The local state left behind by the destroy reads `serial 16 | resources: 0`** — read before
  deleting the folder, because that file is the only record that the destroy actually completed rather
  than half-ran.
- **[Claude] `terraform-live/development/` deleted, and the `development` row left seven places in one
  commit**: `ENV_TOKENS`, `ENVIRONMENT_TAGS`, `PROFILES`, `layers.py`, `check-bootstrap-parity.py`,
  `conventions.md` §6 and `terraform-live/README.md`. **Pass 4 is closed.**
  - `terraform-live/README.md` had three further lines that had quietly gone false — the account list,
    the Stage 3 network sentence, and the Stage 5 consumer pair (whose second half was destroyed at step
    2.4). **No gate reads those**; they were found by grepping the file for the old name, which is the
    only method there is for prose.
  - The bootstrap count went back to **five**: `staging/`'s slice replaced `development/`'s rather than
    joining it, because this was a **rename, not a vend** — so the number never actually changed, and the
    "six" this README carried for one pass was the migration window showing through.

## 2026-09-06 — pass 5 closed: every document that stated the account as a fact

- **[Claude] 5.1 finished, and one of its instructions was REFUSED.** It said to **remove** the Development
  slice from `dns-allowlist.py` rather than retarget it, reasoning that a headless deploy target resolves
  whatever its pipeline resolves. **The reasoning is right about the design and wrong about the code**:
  `terraform-live/staging/egress/main.tf` still declares `dns_firewall = true` with an allow-list, so
  dropping the row would have left a list that exists in the tree with nothing reading it — **a check whose
  scope shrank while the thing it measures did not (Lesson 31)**, which is the failure this whole pass
  exists to catch. The row is retargeted; whether a headless account keeps a DNS firewall at all is 6c's
  decision, since D38 rewrites egress outright.
- **[Claude] 5.2: `./aws/rename-check.py` prints the AFTER verdict, `0 check(s) FAILED`** — and **no MIXED
  verdict appeared at any point in the stage**, which is the instrument's claim about the step ORDER
  rather than about any single reading.
- **[Claude] 5.3 across eleven documents and seven decisions.** Three findings came out of the sweep rather
  than out of the work:
  - `ORGANIZATION.md`'s assignment table footnote said **all three `Staging` rows** were pending a vend.
    **There are two.** A deployment target registers no container image, so `DevEnvStewardAccess` was never
    coming — the note had counted a row that no decision ever asked for. The table is now **14 rows**,
    renumbered, and 14 is exactly what `list-identities.py` reads.
  - `README.md`'s adopt/depart table holds **the one reference recommendation this project took and later
    gave back** — "experimentation and development as distinct accounts". The honest verdict is that the
    *boundary* survived and its *account* did not: what is developed past it is a pipeline definition,
    developed in git and executed into Staging, so the account was a place to stand that nobody stood in.
  - **The three reference-architecture summaries in `README.md` were deliberately NOT edited.** They say
    what AWS's samples say, and those samples still name a development account. Editing them would have
    turned a quotation into a claim.
- **[Claude] `docs/GENERAL_PLAN.md` needed nothing.** The 2026-09-05 re-scope had already brought its
  account map and stage index to the post-conversion shape — the one document in the set that was written
  after the decision instead of before it.

## 2026-09-06 — the stage closes

- **[Claude] Status row, `docs/log/INDEX.md`, `docs/GENERAL_PLAN.md`'s stage index — all three brought to
  what the stage actually did.** The index cell says what is *inside* this file, which is what that index
  is for: fifteen sections, provenance named per subject, and the failure modes worth re-reading rather
  than the steps.
- **[Claude] What the stage preserved is the harder half of what it did, and it is worth stating once in
  one place.** The VPC keeps `10.50.0.0/16` because a CIDR is immutable; **both `[P]` gateway-endpoint ids
  survived a folder rename, a state migration and a token flip**; and Production's peering kept its `pcx-`
  id through a `for_each` key rename that would otherwise have destroyed it. None of that was luck — each
  is a step that existed only to protect it (4.1's allocation swap, Recipe E's split, 4.5's `moved {}`
  blocks).
- **[Claude] Still owed, and not this stage's to take: step 3.5.** The Account Factory provisioned
  product's parameters are readable only from Management, which holds no CLI profile. That reading is also
  what would close **Stage 1b verification (vi)** — it decides whether "the direct assignment did not come
  back" means the trigger fired and produced nothing, or never fired at all.

## 2026-09-06 — the stage's own Validation list, run after the merge

*Claude, as the infrastructure user. The stage was already marked DONE; this is the list its Validation
section names, run rather than assumed.*

- **`make check` OK; `make check-ou` OK** — every OU's document count is as authored.
- **`./aws/datalake.py`: `0 check(s) FAILED`.** `DL-5` reads `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE`
  in both accounts (the 5.4 bracket holding); `DL-7` reads **3 shares out and 2 resource links on the
  consumer side, no pending invitation**; `DL-13` reads the create-time admin list unchanged in Data
  Governance and the two service-appointed SMUS seats in Sandbox. The exit code is 1 and it is **not** a
  finding — the persona `sso-session`s hold no token, which is section 14's whole content.
- **`./aws/deploytargets.py` — and this is where the sitting earned its keep.** The stage's Validation
  line says `DT-8` *"runs at all — it is skipped until `awsds-infra-staging` resolves — and passes"*.
  **`DT-8` is a PAIR and that line named one of them.** The D20 half passed:
  *"no resource link reaches Data Governance"*. The other half **failed**:
  *"mirror curated: DIVERGES (missing 1, extra 0)"*.
  - **Nothing had drifted.** Stage 9 has not built the Staging mirror, so the account holds zero tables
    against the lake's one — and the comparison could not tell that from a mirror that had fallen behind.
    **A check that reads the same on "not built yet" and on "drifted" is not a check** (Lesson 13).
  - **The reason nobody had ever seen it is the interesting part.** The check was not green before today;
    it was **skipped**, because `awsds-infra-staging` did not resolve. Stage 6b made that profile exist,
    and the first thing the newly-runnable check did was report a divergence against something no stage
    has built. It would have stayed red through 6c, 6d, 7 and 8 — *"a check that is red for four passes
    is a check nobody reads on the fifth"*, which is this stage's own pass-5 header, arriving as a
    measurement instead of a warning.
  - **The fix used a discriminator that already existed in the same file.** `built` — true once any
    Stage 9 object stands in the account (job role, model package group, workgroup, bucket) — is what
    `DT-9` two blocks below already uses for exactly this shape. `DT-8` now **notes** until then and
    **fails** from the first Stage 9 apply, with no further edit. Re-run: **`0 check(s) FAILED`**.

## 2026-09-06 — step 3.5, the last one owed: two answers, and one of them closes a 25-day-old verification

- **[user] Control Tower → *Update account*, and the screen answered the question before the button was
  pressed.** `Display Name` and `Account Email` are rendered **READ-ONLY**, still holding
  `Development Account` and the old root address, while the OU tree beside them already reads
  `Staging Account`. The step asked *"whether `AccountName` follows an out-of-band rename is not
  documented"* — **it does not, and there is no field through which to correct it.** A permanent
  divergence of the provisioned product, the same treatment D32 gives the direct assignment.
  - The e-mail half is sharper: the root address was changed out of band in the same sitting, AWS
    documents the e-mail as not following, and the screen confirms it. The provisioned product now
    disagrees with Organizations on **two** fields, and a future reader comparing them sees something that
    looks like drift and is not.
  - The editable fields — OU and access configuration — already held the right values. **The update was
    run anyway**, deliberately: it is the supported reconciliation, it clears any `Moved member account`
    drift an out-of-band move would have left, and it is the only controlled way to fire the event
    Stage 1b verification (vi) had been waiting on.
- **[Claude] Read back: `rename-check.py` `0 check(s) FAILED`** — `RC-1` still `Staging Account`, `RC-2`
  still `Workloads`. The read-only fields did not submit, which is what a disabled field means.
- **[Claude] AND THE ACCOUNT CAME BACK WITH A SEVENTH ASSIGNMENT.** `./aws/list-identities.py` §5.2 reads
  **`AWSAdministratorAccess` → the infrastructure user `(USER)`** where it had read six group rows that
  same morning. **Stage 1b verification (vi) closes in the affirmative, 25 days after step 5.1 removed
  it**: a Control Tower account update **re-asserts** the direct Account Factory assignment.
  - **The plan pre-wrote this branch and it is followed rather than re-argued.** 1b step 5.1 says: *"If
    the assignments do come back, stop removing them and record the direct assignment as a permanent
    property of an Account Factory-vended account."* Done — `D32` amended, `docs/AWS_STATE.md`'s two
    roster rows restated, the 1b Status row and its (vi) bullet closed.
  - **What it buys is a rule, not a row.** The absence of that assignment on the other four vended
    accounts is **not a control**: it survives only until each account's next update, and no gate may be
    written assuming otherwise. `Policy Canary`'s row is no longer *the only* direct `USER` assignment —
    it is the only one that is permanent **by design** rather than by re-assertion.
  - **This is also why 3.6's morning reading could not answer (vi).** It read the same on *"the trigger
    fired and produced nothing"* and *"the trigger never fired"* (Lesson 13), and the second turned out to
    be the case. The reading that settled it is the same instrument, run **after** the event — which is
    the whole reason 1b refused to close the verification on the strength of the removal succeeding.
  - **`RC-5` passed while listing the new set**, and that is correct scoping rather than a miss: it checks
    D18's persona row, and the landing zone's sets are not its subject. Worth knowing before someone reads
    that `pass` as "the assignment list is as designed".
