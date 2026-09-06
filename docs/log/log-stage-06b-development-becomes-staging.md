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
