# Stage 15 — GuardDuty org-wide

| | |
|---|---|
| **Status** | **Unchanged by the 2026-09-05 re-scope, and deliberately so (user).** The hub puts two internet-facing hosts in Production, which is a widening of exposure this stage would watch; pulling it forward was offered and declined, so the deviation stays argued in `institutional-delta.md` rather than closed early. Two things do change: the accounts it enables over are **one Interactive account plus the renamed Staging**, and its verification that waited on "the Staging vend" is unblocked by [6b](stage-06b-development-becomes-staging.md) instead; and **the estate now has two internet-facing hosts rather than one**, both in Production, so the exposure this stage watches is the WireGuard host *and* the Squid proxy — whose access log is separately Stage 11's evidence, and is not a substitute for a detector. — *earlier:* not started — **created 2026-08-18 by splitting Stage 4's pass 4 out whole**, hours after that pass had been prepared against the current documentation, so it arrives already revised: the preparation's findings (the protection plans arrive ON, decision 1's collision with `DenyGuardDutyTampering`, verification (i)'s first half answered NO by documentation, the measured SNS statements behind step 4's do-not-reuse rule) are all in the steps below rather than waiting to be discovered. **The step numbers 0-6 map onto Stage 4's retired 10.0-10.6 one for one** (10.2a became decision 3 plus step 2a); the stage log for the split sitting is [Stage 4's](../../log/log-stage-04-vpn.md). Pre-instrumented by `./aws/guardduty.py` (`GD-1`–`GD-3`), carved out of `./aws/vpn.py` the same day — `VP-8` is retired, not renumbered |
| **Prerequisites** | **None that block.** Stage 4 built the thing this stage watches — the one internet-facing host — and everything below could have run the day that host booted; running it *here* instead is a **deliberate deferral, not a dependency**, recorded in [`institutional-delta.md`](../institutional-delta.md) (an institution enables detection with, or before, its first exposed resource — principle 9's own argument, and this stage is the plan overruling its own principle with its eyes open). What the deferral buys and costs is in "Why this stage is where it is" below. **This stage gates others rather than being gated:** [Stage 11](stage-11-dlp.md) step 4 (the paid features against a real bill) needs this stage plus about a month of billing behind it, and [Stage 5](stage-05-data-foundation.md) step 13.2's "Security Hub ingests GuardDuty findings" ingests nothing until this stage runs |
| **Consumes** | [D12](../decisions/D12-budget-ceiling.md), [D16](../decisions/D16-break-glass.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | — (no `INT-nn` row; the delegation lands in `INV-09`, step 6) |

*Read with [`docs/plan/conventions.md`](../conventions.md). The battery runbook applies to decision 1:
[`scp-battery.md`](../runbooks/scp-battery.md).*

---

**Objective:** threat detection over the whole organization — delegated to Audit, auto-enabled for every
account present and future, held to **foundational detection only** (every optional protection plan
switched off until [Stage 11](stage-11-dlp.md) step 4 decides the paid ones against a real bill), and its
findings routed to a human for the first time in the project.

## Why this stage is where it is, and what the position costs

GuardDuty was Stage 4 step 10 — principle 9's own scheduling: enable detection with the first thing worth
detecting, which was the WireGuard host, the project's only internet-facing resource. **The move to
Stage 15 (2026-08-18) deliberately breaks that coupling**, and the trade should be read before the steps:

- **What it costs:** the exposed host runs through Stages 5-14 — the lake, the Studio, GitLab, the
  pipelines — with no detector behind it. The failure modes GuardDuty exists to catch on exactly that
  host (role credentials used from outside AWS, outbound to known-bad destinations, mining patterns) go
  unwatched for the whole build-out. And one of [open question 17](../open-questions.md)'s named reopeners — the
  off-VPN administrative credential gaining a watcher — is deferred with it: the one credential outside
  `DenyControlPlaneOffVpn` stays unobserved for as long as this stage waits.
- **What it buys:** the 30-day free window (every account at once, every protection plan) now opens over
  a **populated estate** instead of an empty one. At Stage 4 the trial could only have priced S3
  Protection against nothing — a number near zero that flatters the option it tests (Lesson 7). Opening
  it here, with real job volume behind it, turns the window into the measurement instrument Stage 11
  step 4 actually needs — the one thing the Stage 4 Cost note said the trial could never be.
- **What it does not change:** nothing below got easier or harder by waiting. The defaults problem
  (step 0), the SCP collision (decision 1), the Management gap (decision 3) are all properties of the
  service, not of the calendar.

## What this stage builds, and in which accounts

One org-wide enablement, done by hand — no slice, no profile, no Terraform:

| Where | What | Layer |
|---|---|---|
| Management, by hand | the delegation: `enable-organization-admin-account` naming Audit | — |
| Audit, by hand | the org configuration (auto-enable `ALL`, every optional plan `NONE`), the detector clean-up, the findings route (EventBridge → SNS → e-mail) | — |
| every member account | a detector, arriving via auto-enable — foundational sources only | — |

**Executor markers are Stage 4's** (`[Claude]` / `[Claude⚡]` / `[user]`): both acting accounts hold no
CLI profile (D33/D34), so every AWS act below is **[user]** as `AWS Control Tower Admin` →
`AWSAdministratorAccess`, console or CloudShell, in **`us-west-2`** — the Region ceiling does not exempt
GuardDuty (open question 16's closure), and the delegated administrator must be the **same account in
every Region**, so a second Region later repeats step 1's command, never picks a different account.

## To execute

- **0 — [Claude] Read the defaults before opening a console: they invert step 3** (documentation,
  2026-08-18). Enabling GuardDuty in an account for the first time turns on **every protection plan
  except Runtime Monitoring** — S3 Protection, EKS Protection, Malware Protection for EC2, RDS
  Protection, Lambda Protection, AI Protection — each inside its own 30-day free trial. The S3
  Protection page says it outright ("GuardDuty will also enable S3 Protection, which is included in the
  free trial"), and the FAQ states the exception in one line: Runtime Monitoring "is the only protection
  plan that is not enabled by default". **So the add-ons are not *left* off — they arrive on and have to
  be switched off**, and the switch is a different API in each of the three places they land, one of
  which this organization denies:

  | Where a plan is on | The call that turns it off | Under `awsds-org-scp-baseline` |
  |---|---|---|
  | a **member** account | `guardduty:UpdateMemberDetectors` | allowed |
  | **future** accounts (the org preference) | `guardduty:UpdateOrganizationConfiguration` | allowed |
  | **Audit's own** detector | `guardduty:UpdateDetector` | **denied — `DenyGuardDutyTampering`** |

  That third row is
  [`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md)'s documented collision —
  written expecting Stage 11 to need `UpdateDetector` to turn a feature **on** — arriving earlier and in
  the opposite direction: this stage needs the same call to turn six **off**. **No ordering avoids it**:
  Audit's detector is created *by* step 1, with the add-ons already enabled, before any configuration is
  possible. It is **decision 1** below, taken before step 1 and not at the console — the exact situation
  `POLICIES.md` says must never be discovered at the console in the evening.

- **1 — [user] Delegate from Management** — CloudShell or console:

  ```
  aws guardduty enable-organization-admin-account --admin-account-id <Audit> --region us-west-2
  ```

  Three properties of this one call, all documented and all consequential. **It is per-Region** (the
  same-account rule above). **It enables GuardDuty in Audit** and registers `guardduty.amazonaws.com`
  for trusted access in one act — that is what step 6's INV-09 restatement records; **delegating IS
  enabling**, which is why Stage 1b step 8 deferred the delegation out of the landing zone in the first
  place. **It does not enable GuardDuty in Management** — the console path can, because its "Get
  started" button is on the same page, so prefer the CLI form here and let step 2a decide Management
  deliberately.

- **2 — [user] Set the org configuration in Audit** — GuardDuty console → **Accounts**, or
  `update-organization-configuration` against **Audit's own detector id**. Auto-enable **`ALL`**: it
  covers existing accounts, suspended or removed ones, **and the delegated administrator itself**; allow
  up to 24 h to propagate. **Set every optional plan's auto-enable to `NONE` in the SAME act, not
  afterwards** — one call carrying both `--auto-enable-organization-members ALL` and a `--features` list
  of `{"Name":"…","AutoEnable":"NONE"}`, or one **Save** on the console's Protection Plans page, which
  has a row per plan. The order inside the step is the whole point: `ALL` is what brings the members up,
  so `ALL` first and `NONE` second means every member comes up with every plan **on**, and step 3 then
  owes a clean-up pass that a single call would have made unnecessary. **Type the feature names from
  `get-detector`'s own `Features` list, not from memory** — Audit's detector exists by now and
  enumerates them, AI Protection included, which a typed list would miss (Lesson 23's shape: bind to
  what the API returns).

- **2a — [user] Management's own coverage — decision 3, executed here.** `ALL` does **not** reach the
  management account on its own: "before the management account gets added as a GuardDuty member, it
  must have GuardDuty enabled" — verification (i)'s first half, answered by documentation before the
  stage ever ran. If decision 3 lands as recommended, enable GuardDuty **in Management, as the
  management account**, then add it as a member from Audit; its own add-ons switch off without
  decision 1's procedure, because Management is SCP-exempt and `UpdateDetector` works there.

- **3 — [user] Leave the estate on foundational detection only** — S3 Protection and Malware Protection
  for EC2 were always the named two (billed separately, decided in Stage 11 step 4 against a real
  bill); step 0 widens the list to every optional plan. **Where each is switched off:** members through
  `UpdateMemberDetectors` (allowed, one call for all of them); future accounts through step 2's `NONE`;
  **Audit's own detector through decision 1, and nothing else works**. `./aws/guardduty.py` `GD-3`
  reads every feature of every detector it can reach and fails on any that is `ENABLED`, so drift and
  an unfinished step 3 look the same in the report — which is the intent.

- **4 — [user] Route findings** — in Audit, console-built (`ManagedBy` n/a — no Terraform reaches that
  account by design): an EventBridge rule on GuardDuty findings → SNS → e-mail. Decision 2 below;
  record the topic name and who subscribes — D12 skipped budget alerts, so this is the project's first
  automatic notification of anything. **Create a new `awsds-*` topic; do not reuse Control Tower's** —
  and this is measured, not assumed: the `Security` OU's Control Tower SCP was read from the Identity
  profile on 2026-08-18 and carries three SNS statements, all excluding only `AWSControlTowerExecution`.
  `GRSNSSUBSCRIPTIONPOLICY` denies `sns:Subscribe`/`Unsubscribe` on
  `aws-controltower-SecurityNotifications`; `GRSNSTOPICPOLICY` denies `AddPermission`, `CreateTopic`,
  `DeleteTopic`, `RemovePermission` and `SetTopicAttributes` on all three `aws-controltower-*`
  notification topics; `CTSNSPV1` is a deny-all-but-a-short-list over
  `aws-controltower-CentralizedLoggingNotifications*`. **Both halves of the reuse fail** — the
  subscription *and* the topic-policy edit an EventBridge target needs — so reuse is not a shortcut that
  half works, it is refused twice. A topic this project names has no statement over it at all.
  **A related absence to leave related, not conflated**: the WireGuard health alarm
  (`terraform-modules/wireguard/observability.tf`) carries **no SNS action** — deferred to Stage 12, and
  its comment names this step's topic only as the project's first notification of anything. The alarm
  lives in the VPN home and this topic in Audit, so wiring them is a cross-account question for Stage 12,
  not a to-do of this step; record here only that the topic now exists.

- **5 — Read the SCP interaction, settled here because it is free here and costly later**:
  `awsds-org-scp-baseline` denies `guardduty:UpdateDetector` on the organization root, Audit included —
  org-wide administration through `UpdateOrganizationConfiguration`/`UpdateMemberDetectors` is not
  denied, and enabling the base service needs neither, so **steps 1 and 2 are not blocked**; step 3's
  Audit half is, and Stage 11 step 4 will be. **What this step can now answer, which is why
  `POLICIES.md` deferred the question: the only principal GuardDuty creates is the service-linked role
  `AWSServiceRoleForAmazonGuardDuty`** (one per account where the service is enabled) — the *service's*
  identity, not an administration role, and it never calls `UpdateDetector` on a human's behalf. **So
  `POLICIES.md`'s "carve out a named administration role" alternative has no candidate in GuardDuty's
  own creations**: the only nameable principal that could hold the carve-out is the Identity Center
  administrator role in Audit (`AWSReservedSSO_AWSAdministratorAccess_*`), which is decision 1's
  option (c). Record the SLR's exact ARN once it exists, in the stage log, so Stage 11 inherits a
  reading rather than a search.

- **6 — [Claude] Close the paperwork in the same sitting**: restate `INV-09` in
  [`docs/AWS_STATE.md`](../../AWS_STATE.md) (nine trusted-access principals, `guardduty` delegated to
  Audit — §C already predicts it); re-run `./aws/org-trusted-access-services.py` and
  `./aws/guardduty.py`; and **re-read [open question 17](../open-questions.md)** — the reopener it names
  for this stage (the off-VPN administrative credential gaining a watcher) is met the day this stage closes, so the
  question is re-read against that fact, which is not the same as reopening it. **[user]** Record
  steps 1-4 in the stage log — including the feature list `get-detector` actually returned, which is
  this stage's only measurement of what "the defaults" mean on the day it ran.

## Deliverables

- **The delegation, read back**: `guardduty.amazonaws.com` in the trusted-access list with Audit as its
  delegated administrator (`./aws/org-trusted-access-services.py`, and `GD-1`).
- **Coverage without silence**: `./aws/guardduty.py` shows a detector `ENABLED` in **every measured
  account** — and section 3 of its report names the accounts nothing measured (Management, Log Archive,
  Audit, the unvended `Staging`), because a missing account is not a passing account (Lesson 13).
- **Foundational only**: `GD-3` green — every optional plan `DISABLED` on every detector it can read.
  Audit's own detector is outside every profile; its clean-up is proven in the same sitting as
  decision 1's procedure, by `get-detector` read back in its CloudShell **before** the SCP re-attach.
- **The first notification**: a test finding (`CreateSampleFindings` in Audit) arrives by e-mail.
  Sample findings are the documented instrument for exactly this; record the finding type used.

## Validation

1. Run `./aws/guardduty.py` — `GD-1`–`GD-3` pass, 0 FAILED.
2. Re-run `./aws/org-policies.py` after decision 1's procedure — the re-attach landed and nothing else
   about the ceiling changed; then re-run phases 1-3 of the battery
   ([`scp-battery.md`](../runbooks/scp-battery.md)) in the same sitting.
3. `terraform plan` on `identity/org-policies/` reads `No changes` — the by-hand detach/re-attach of
   decision 1(a) is invisible to the slice, which is what proves the pair completed.

## Cost

Measured rows in [`docs/PRICING.md`](../../PRICING.md) (Lesson 6): free for the first 30 days per
account, then **~USD 3-5/month for foundational detection** — the cost-model floor's low→high band moves
with this stage. **The trial covers every plan, not only the foundational sources**, and the window
starts at step 1 in every account at once. The plans that arrive on publish usage metrics — CloudWatch,
`AWS/GuardDuty` namespace, `AnalyzedCount`/`AnalyzedBytes` per data source, hourly — and **this is the
one argument the deferral to Stage 15 strengthens**: at Stage 4 those metrics would have priced an empty
estate (Lesson 7); here they price real volume, which is exactly the number Stage 11 step 4 wants. Of
the default-on set, only **S3 Protection** has a cost surface that grows with the lake; **Malware
Protection for EC2** bills only when a finding triggers a scan.

## Decisions due while executing

1. **How Audit's own detector loses the add-ons it was born with** (steps 0, 3) — **due before step 1**,
   because the detector is created by that call with every optional plan already enabled and
   `guardduty:UpdateDetector` is denied to Audit by `awsds-org-scp-baseline`. Three exits, and the
   recommendation is (a):
   **(a) the detach/re-attach procedure `POLICIES.md` already writes down** — detach
   `awsds-org-scp-baseline` from the root, switch the plans off in Audit, re-attach, and re-run phases
   1-3 of [`scp-battery.md`](../runbooks/scp-battery.md) before the sitting is called done. It is the
   same shape as the `s3:DeleteBucket` procedure in `Data`, it is minutes long, and it leaves the
   ceiling exactly as it was. Its cost is a window in which nothing denies GuardDuty tampering anywhere
   — nor anything else in that document: `DenyLeaveOrganization`, `DenyIamUserCreation`, the two
   exfiltration statements and `DenyEcrPublicEntirely` all lift with it — which is why it is a
   *procedure*, done in one sitting, never left half-finished. **Three mechanics to have in hand before
   starting it**, none of them obvious at the keyboard: the detach and the re-attach run as **the
   infrastructure user on Identity** (`awsds-infra-identity`), which holds `AttachPolicy`/`DetachPolicy`
   through the delegation — *not* as the Control Tower admin doing the GuardDuty half in Audit, so this
   is two identities in one sitting; the attachment is **Terraform-managed with `prevent_destroy`**, so
   the by-hand detach is drift and the end-state test is `terraform plan` on `identity/org-policies/`
   reading **`No changes`** after the re-attach, which is what proves the pair completed rather than a
   memory of having typed it; and the GuardDuty change in the middle is `update-detector` against
   **Audit's own detector id**, from CloudShell in Audit, with `get-detector` read back before
   re-attaching — because re-attaching first and then discovering the change did not land means running
   the whole procedure twice.
   **(b) leave Audit's add-ons on for the free trial** and revisit at Stage 11 step 4. Cheap, honest
   about the trial — and the empty-estate argument that rejected it at Stage 4 is **weaker here**, since
   the estate is populated by now; what still rejects it is narrower and still sufficient: Audit's own
   S3 and EBS surface is Control Tower's buckets and nothing else, so the number it measures is not the
   number Stage 11 needs, and it leaves `GD-3` failing for a month, which trains the reader to ignore a
   red check. If it is ever chosen anyway, **flip `GD-3` rather than living with the red** — a decision
   left only in prose is measured by nobody.
   **(c) carve a named principal out of `DenyGuardDutyTampering`** — the only candidate is Audit's
   Identity Center administrator role (`AWSReservedSSO_AWSAdministratorAccess_*`), since GuardDuty
   itself creates only the service-linked role (step 5). It converts a procedure into a standing
   exemption held by the one role a compromise of Audit would already have, and the statement exists to
   stop exactly that principal from turning detection off (Lesson 18's neighbourhood). Reject unless a
   second sitting proves (a) unworkable.
2. **Findings routing** (step 4) — recommended: EventBridge → SNS → e-mail, in Audit, console-built.
   Record the topic name and who subscribes.
3. **Management's own coverage** (step 2a) — recommended: **enable it.** It is the SCP-exempt account,
   it holds break-glass root (D16), and it is the one place where a compromise is constrained by
   nothing this project wrote — which makes "GuardDuty everywhere except there" the wrong shape. It
   costs one more account's foundational detection after the trial. Record the answer either way.

## Verifications to answer while executing

Record every answer, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | ~~Does auto-enable `ALL` reach **Management itself**?~~ **Answered NO by the documentation (2026-08-18, while this was still Stage 4 verification (v))** — "before the management account gets added as a GuardDuty member, it must have GuardDuty enabled", so `ALL` never reaches it on its own and coverage there is a deliberate act (step 2a, decision 3). What remains of this row: **does a later vend arrive covered** — the `Staging` vend or Stage 14's first unit, whichever lands first (existing members were already documented as covered) | 2, 2a |
| ii | What does `get-detector` actually return in a freshly enabled account — which features, with which statuses? The documentation says "all but Runtime Monitoring"; this is the reading that turns that into a measurement, and it is also where AI Protection's feature name comes from | 0, 2 |
| iii | How does the **SUSPENDED `Sandbox`** in the roster surface under auto-enable `ALL` — an error, a skipped row, or a member entry? The documentation says `ALL` includes "accounts that may have been suspended", and the standing rule (resolve accounts by exact vended name, filter on `ACTIVE`) exists because that account is a trap for instruments; record what the Accounts table shows for it | 2 |
| iv | Does the `Security` OU's Region ceiling interact with the delegation at all — the enablement is `us-west-2` by design, but record whether any console surface tries another Region and is refused (the ceiling's `NotAction` list does not exempt GuardDuty, by decision 10 of Stage 1d) | 1, 2 |

## Risks

- **Decision 1(a)'s window is org-wide**: while `awsds-org-scp-baseline` is detached, nothing denies
  GuardDuty tampering, `LeaveOrganization`, IAM user creation, snapshot sharing or ECR Public anywhere.
  Minutes long, one sitting, battery re-run before it is called done — the procedure is the control.
- **The GuardDuty free window starts at step 1, in every account at once** — the measured bill appears
  in month two; do not read month one as the steady state (Lesson 6). Stage 11 step 4 reads the bill
  *after* the window closes, which is the earliest a real number exists.
- **A propagation gap reads as a failure**: `ALL` takes up to 24 h to reach every member. `GD-2` red on
  the evening of step 2 and green the next morning is the documented behaviour, not drift.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
