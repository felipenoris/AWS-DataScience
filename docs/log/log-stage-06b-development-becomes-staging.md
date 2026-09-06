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
