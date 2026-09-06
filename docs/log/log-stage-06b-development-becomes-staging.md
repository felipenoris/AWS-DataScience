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
- **0.5b — not yet run.** It is the user's: CloudShell in **Management** as the **`AWS Control Tower
  Admin`** user, permission set **`AWSAdministratorAccess`**, running
  `./aws/cloudshell/management-landing-zone-drift.sh`, whose section 2 now answers the auto-enrollment
  question.

### What the sitting left in the repository

- **[Claude]** Branch `claude/stage-06b-preparation`, [PR #53](https://github.com/felipenoris/AWS-DataScience/pull/53).
  Nothing merged, nothing applied.
- **[Claude]** Two instruments given the interpretation they lacked (`org-trusted-access-services.py`,
  `management-landing-zone-drift.sh`); `rename-check.py` corrected in three places; the stage file
  corrected in the places listed above and re-reviewed against the pass 0 readings.
