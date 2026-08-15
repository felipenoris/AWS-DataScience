# Stage 1d — Audit trail, Config scope, org-wide enablement

| | |
|---|---|
| **Status** | **in progress — steps 10, 11 and 12 are DONE (2026-08-14). Step 9 is the only one left, and 9.1 and 9.4 are already read.** Decisions 4, 8 and 10 are taken; verifications (v), (xiii) and (xiv)'s first half are answered; open question 16 is closed. What remains is **decision 9, then decision 3 and the write** — the only permanent act in the stage. **The before-state is already measured**: no Object Lock, versioning `Enabled`, and one lifecycle rule expiring current *and* noncurrent versions at **365 days**, which is the ceiling decision 3 must sit under. Read "What 1c measured that changes this stage" first: the step is **blocked as written** and runs, if it runs, as `AWSControlTowerExecution` assumed from Management |
| **Prerequisites** | **[Stage 1b](stage-01b-identity-and-controls.md) complete** — every step here runs inside a member account and needs step 5's profiles. **Stage 1c was not a prerequisite and is now done anyway** (2026-08-14): none of these steps depends on a policy being attached, but three of 1c's attached documents and one of Control Tower's own now sit across this stage's path, which is what the revision below is about |
| **Consumes** | [D12](../decisions/D12-budget-ceiling.md), [D16](../decisions/D16-break-glass.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md) (step 12), [D29](../decisions/D29-policy-canary.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | **The two organization-level halves of [INT-11](../integrations.md)** — org-wide RAM sharing and the Lake Formation cross-account version, **the second of which was already true before the stage started and is now a reading plus an instruction to Stage 5**. **Also closes [D16](../decisions/D16-break-glass.md)'s last unbuilt deliverable** (10.4) and **[open question 16](../open-questions.md)** (step 12). The third INT-11 item (`AWSLakeFormationCrossAccountManager` on the grantor) is Stage 5 step 7, because the role does not exist yet (11.4) |
| **Log** | `log/stage-01d-org-wide-enablement.md` |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Three steps kept their numbers — 9, 10 and 11 — and a fourth was added as 12.** The landing zone's second
half was one stage until 2026-08-09, and the step numbers did not change in the split: every other file's
`Stage 1d step 9` reference is this stage's step 9. **Step 12 is new (2026-08-14)** and closes
[open question 16](../open-questions.md), which 1c step 7.7 raised and addressed here by name.

**The four steps are independent of each other** and can be done in any order, or in four separate
sittings. What they have in common is that each is organization-level, manual, and done from inside a
member account rather than from Management alone.

## The stage at a glance

| # | What | Identity | Consumes | Why it is here and not later |
|---|---|---|---|---|
| 9 | Object Lock, compliance mode, on the CloudTrail log bucket — **blocked for every principal but one, see 9.6** | CT Admin @ Log Archive, **or `AWSControlTowerExecution`** | D33, D34 | Before there is anything worth hiding in the trail |
| 10 | Measure AWS Config, then decide — **and, in 10.4, the rule D16 owes** | CT Admin @ Management + Audit | D12, D16, D29 | The landing zone's largest recurring line. **10.4 is not about that line at all** and is independent of what 10.3 decides |
| 11 | Org-wide RAM sharing + LF cross-account version — **11.2 is already satisfied, it is now a reading** | CT Admin @ Management / Infra user @ Data | D22, D35 | Stage 5 fails **silently** without it |
| **12** | **The Region ceiling on `Security`** — the one OU 7.7 never targeted | CT Admin @ Management, measured from Log Archive/Audit | D23 | This is the stage that touches those two accounts, and the ceiling is free |

## Who executes what

| Steps | Identity | Sign-in path |
|---|---|---|
| 10.3 (Cost Explorer), **10.4 (the Config rule, which exists only in Management)**, 11.1 (RAM), **12 (enabling the control)** | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 9 (the *reading*, in Log Archive), 10 (the Config aggregator lives in Audit), **12's measurement** | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Log Archive** / **Audit** — the infrastructure user has *no* assignment in either (`ORGANIZATION.md`), so **there is no CLI profile for those two accounts and CloudShell is the only shell** |
| **9's write, if decision 9 goes that way** | **`AWSControlTowerExecution`**, assumed **from Management** | `aws sts assume-role` from CloudShell in Management as CT Admin — it is the **only** principal `CTS3PV8` exempts, and using it by hand is what decision 9 is about |
| 11.2 (Lake Formation) | **Infrastructure user**, from the laptop | the `awsds-infra-data` profile created in Stage 1b step 5 |

## What this stage costs

This is the stage that decides the largest recurring line in the whole landing zone:

- **Free:** S3 Object Lock (the lock itself; the storage it prevents from expiring is not),
  organization-wide RAM sharing, the Lake Formation cross-account version.
- **Decided here, not added:** AWS Config is the landing zone's main recurring cost — USD 0.003 per
  configuration item, USD 2.50-5.00/month at this account count (`PRICING.md` §2). Step 10 is about that
  number and, read honestly, is mostly about *measuring* it (D12).
- **The one cost that is easy to create by accident** is step 9's: a retention longer than the bucket's
  lifecycle expiration turns the Log Archive into an archive nobody chose to pay for, and compliance mode
  means it cannot be shortened.
- **Step 12 is free** and, if it goes the other way, so is not doing it: a Region control costs nothing
  either way, which is why the decision is about blast radius and not about money.

---

## What 1c measured that changes this stage

**Read this before executing anything.** Five facts, four of them measured after this stage was last
written, and three of them change what a step actually is. None is a blocker for *starting*; one is a
blocker for finishing step 9 the way it is written.

| # | What was measured | What it does to this stage |
|---|---|---|
| 1 | **`CTS3PV8`**, in the Control Tower guardrail on the `Security` OU, is a `Deny` with a **`NotAction`** list over `aws-controltower-logs-*`, `aws-controltower-cloudtrail-*` and `aws-controltower-access-logs-*`, exempting **`arn:*:iam::*:role/AWSControlTowerExecution` alone**. `s3:PutBucketObjectLockConfiguration` and `s3:PutBucketVersioning` are **not** in that list | **Step 9 cannot be performed by `AWS Control Tower Admin`.** It is not a permissions gap to be widened — it is AWS's own guardrail, and the only principal that walks through it is Control Tower's execution role. **New sub-step 9.6 and decision 9** |
| 2 | The same `NotAction` list **does** permit `s3:DeleteObject`, `s3:DeleteObjectVersion`, `s3:PutObject` and `s3:PutObjectRetention` to every principal | **The guardrail leaves object deletion open on purpose**, so step 9 is not redundant with it — the value of Object Lock is exactly in the actions `CTS3PV8` permits. This is the argument that keeps the step alive after finding 1, and it belongs in decision 9 |
| 3 | **The bucket is not called what this file said it was.** The organization trail `aws-controltower-BaselineCloudTrail` (org trail, home region `us-west-2`) writes to **`aws-controltower-cloudtrail-logs-<account>-<suffix>`**, read from the Identity account on 2026-08-14 | 9.1's names were a landing-zone 2.x shape. The `aws-controltower-logs-` prefix in the old deliverable command returns **`None`**, which reads like a failed lock (Lesson 13). Corrected in 9.1 and in the deliverables |
| 4 | **`CROSS_ACCOUNT_VERSION` already reads `4`** in Data Governance, alongside `SET_CONTEXT: TRUE`, with `DataLakeAdmins` empty and no lake registered (measured 2026-08-14, `awsds-infra-data`) | **11.2 has nothing to set** — it becomes a reading, and the dangerous `put-data-lake-settings` call is not made at all. **Verification (v) is answered before execution.** What survives, and grows, is 11.2's instruction to Stage 5 |
| 5 | **`GRCONFIGENABLED`** denies `config:PutConfigurationRecorder`, `PutDeliveryChannel`, `Stop…` and the retention configuration in **every** governed OU, exempting `AWSControlTowerExecution` only (7.0, verification (iii)) | 10.2's "editing the recorder by hand is drift" is now the *weaker* of two reasons: **it is denied outright.** And 10.4 works only because **Management is exempt from SCPs** — which is the whole reason that sub-step is possible at all |

**And one operational finding that applies to every step here** (1c, twice): the SSO token expires
mid-session and a vended role credential lives 4 h in `~/.aws/cli/cache`, so a stale success is as likely as
a stale failure. Check `aws sts get-caller-identity` immediately before each block, and read the *wording* of
an error rather than its exit code (Lesson 24).

---

## To execute

### Step 9 — Make the audit trail tamper-evident

An audit log that the compromised party can edit is not an audit log. Do this before there is anything
worth hiding in it.

#### 9.1 — Identify the right bucket first, because there are at least three and one of them must not be touched

**The names below were measured on 2026-08-14, and they are not the ones this file carried until then.**
Do not paste a prefix from a document; resolve the name from the trail, which is the only source that
cannot be stale:

```bash
aws cloudtrail describe-trails --region us-west-2 \
  --query "trailList[?Name=='aws-controltower-BaselineCloudTrail'].[S3BucketName,IsOrganizationTrail,LogFileValidationEnabled]" --output text
```

- **Object Lock goes on the CloudTrail log bucket, `aws-controltower-cloudtrail-logs-<account>-<suffix>`,
  in the Log Archive account** — *not* `aws-controltower-logs-*`, which is this landing zone's
  predecessor's name and matches nothing here.
- **It must never go on the access-log bucket** — `aws-controltower-access-logs-*` in the same account.
  That bucket is the destination for S3 server access logging, and **S3 buckets with Object Lock cannot be
  used as a server access log destination**: locking it silently stops access logging for the bucket
  beside it.
- **The Config logs are a third bucket, `aws-controltower-config-*`, and they are in Audit** — that is the
  landing-zone 4.x split, and Control Tower's own guardrail confirms it by protecting that prefix in a
  separate statement (`CTS3PV7`) from the three log buckets (`CTS3PV8`). The target of this step is the
  CloudTrail bucket; the other two are named here so that they are recognised and left alone.
- **Read the state before changing it**, all of which `CTS3PV8` permits because `s3:Get*` is in its
  `NotAction` list: `get-object-lock-configuration` (expect `ObjectLockConfigurationNotFoundError`),
  `get-bucket-versioning` (expect `Enabled` — Object Lock needs it, and `PutBucketVersioning` is denied, so
  versioning being already on is a precondition rather than a step) and
  `get-bucket-lifecycle-configuration`, whose expiration is the ceiling for 9.3's retention.

#### 9.2 — Use compliance mode, and this is the step that limits D33

The earlier wording left this
unsaid, so it was an intention rather than a control (Lesson 5). `AWSControlTowerAdmins` is administrator
*of the Log Archive account*, so the principal this step defends against holds
`s3:BypassGovernanceRetention`: **in governance mode it walks straight through.** In compliance mode a
locked object version cannot be deleted or overwritten by anyone, including that account's root. **Since
D34 that principal is permanent**, so this is not a control covering a two-week bootstrap window — it is
what keeps the audit trail surviving its own administrator for as long as the organization exists.
Getting the mode wrong here is a permanent hole, not a temporary one.

**And this is where finding 2 lands, because it is the reason the step is not redundant.** Control Tower's
own `CTS3PV8` already denies almost everything on these buckets to every principal but
`AWSControlTowerExecution` — but its `NotAction` list **permits `s3:DeleteObject` and
`s3:DeleteObjectVersion` to all of them.** AWS's guardrail protects the bucket's *configuration* and
deliberately leaves its *contents* deletable. So the exposure step 9 closes is precisely the one the
guardrail declines to close, and "Control Tower already protects that bucket" is not an argument against
this step.

#### 9.3 — Three practical constraints, all of which bite later if ignored

- **Compliance mode is not reversible and not shortenable**, and Object Lock itself cannot be disabled
  once enabled on a bucket. The retention period is a commitment, so keep it **short** — long enough that
  tampering is detectable, not long enough to become an archive. This is a detection control, not a
  retention policy.
- **Keep the retention shorter than Control Tower's own log lifecycle expiration**, or the landing zone's
  lifecycle deletions start failing against locked objects. **Read the bucket's existing lifecycle rule
  first** and set the lock inside it.
- **The bucket already exists**, which used to make this step impossible; Object Lock can now be enabled
  in place on an existing bucket (console: Properties → Object Lock → Edit → Enable; CLI:
  `put-object-lock-configuration`), and doing so requires versioning, which S3 turns on and which can no
  longer be suspended. **Existing objects are not locked retroactively** — the default retention applies
  to objects written *after* it, which is fine here and is the reason for "before there is anything worth
  hiding".

#### 9.4 — CloudTrail log file validation — **answered 2026-08-14, before the stage started**

**`LogFileValidationEnabled` is `true`** on `aws-controltower-BaselineCloudTrail`, which is an
**organization** trail with home region `us-west-2`. Measured from the *Identity* account with
`awsds-infra-identity`, which is worth recording as a second small read-boundary result: a member account
sees the organization trail's configuration, so this sub-step never needed Management or Log Archive.

**Verify rather than enable** stands as the rule — editing the trail is landing-zone drift (1a step 5 makes
the same distinction: adding a metric filter to the log group is not an edit to the trail). The re-check is
the same command as 9.1's, whose third column is this flag. If it ever reads `false`, that is a finding
about the landing zone and not a task for this step.

#### 9.5 — Verify while executing (iv):

that enabling Object Lock on the Control Tower-managed bucket does not raise landing-zone drift — **and,
since finding 1 makes the write run as `AWSControlTowerExecution`, a second half: whether the setting
survives a landing-zone update, an account update or a re-enrollment.** Neither half can be closed in the
sitting that makes the change; record the first as measured and the second as provisional, naming the event
that settles it — exactly as 1b step 5.1 did for verification (vi).

#### 9.6 — **The wall, and it is AWS's own** (added 2026-08-14, finding 1)

`CTS3PV8`, in the `aws-guardrails-*` document attached to the `Security` OU, is a `Deny` over the three log
buckets with a **`NotAction`** list and one exemption, `arn:*:iam::*:role/AWSControlTowerExecution`.
`s3:PutBucketObjectLockConfiguration` is not in the list, so **the write this step asks for is denied to
`AWS Control Tower Admin`, to the Log Archive account's administrators, and to every other principal in the
organization.** Read the document before acting — it is one call from the Identity account and 1c's
`./aws/org-policies.sh` already condenses it by `Sid`.

Three things follow, and the third is the decision:

- **This is not a permissions gap to widen.** The account is administered by the identity the deny is
  written against; there is no policy edit that fixes this without removing the guardrail.
- **The one principal that walks through it is `AWSControlTowerExecution`**, which exists in every member
  account and trusts the management account, so it is assumable from Management by `AWS Control Tower
  Admin`. 1c measured the shape of the condition key that makes this work: `aws:PrincipalArn` populates
  with the **role** ARN, not the `assumed-role` session ARN (decision 7's carve-out, proven in both
  directions), so an `ArnNotLike …:role/AWSControlTowerExecution` test does exempt a session assumed into
  it.
- **Using it by hand is a deliberate act and it is decision 9.** AWS reserves that role for Control Tower
  and it is unscoped in the account; borrowing it writes one permanent setting and hands nothing to anyone.
  The alternatives are honest and both cost something: leave the trail's *contents* deletable by the Log
  Archive administrator and record the residual, or stand up a second, project-owned trail with its own
  locked bucket — which is a new recurring line and a second copy of the same data
  (`plan/institutional-delta.md` is where that belongs, not here).

**Whatever is decided, the reasoning goes in the log, not only the outcome.** A future reader finding
Object Lock absent must be able to tell "decided against" from "was never attempted".


### Step 10 — Decide what the AWS Config recorder records — starting by measuring it

#### 10.1 — Why this step exists

Config is the main recurring cost of the landing zone
(`plan/cost-model.md`): USD 0.003 per configuration item, recorded in **every governed account**, so
the cost scales with the account count and with how busy `terraform apply` is — exactly the shape that
surprises people during the build-out stages.

#### 10.2 — There is no console switch, and this is the correction

The step used to read "restrict the
AWS Config recorder to the resource types this project actually uses", which is one line describing
something Control Tower does not offer:

- Control Tower **enables and owns** the recorder in every enrolled account. From landing zone 3.0 it
  already limits *global* resources to the home region, which is the one restriction you get for free.
- **Editing the recorder by hand in a governed account is drift** and is liable to be reset by a
  landing-zone update, an account update or a re-enrollment — the same class of behaviour step 3.8
  warns about for direct assignments. **Since 2026-08-13 that is the weaker of two reasons: it is denied.**
  1c's verification (iii) read `GRCONFIGENABLED` out of every OU's guardrail — `config:PutConfigurationRecorder`,
  `DeleteConfigurationRecorder`, `StopConfigurationRecorder`, the delivery channel and the retention
  configuration, all `Deny`, all exempting `arn:*:iam::*:role/AWSControlTowerExecution` and nothing else.
  So there is no by-hand path to try and fail at; the only door is the same role point 3 below uses.
- The documented path is a **deployed solution**: a Lambda driven by Control Tower lifecycle events
  (`UpdateLandingZone`, `CreateManagedAccount`, `UpdateManagedAccount`) that re-applies a chosen
  resource-type list through each account's `AWSControlTowerExecution` role. That is a real piece of
  infrastructure with its own failure modes, not a checkbox.

#### 10.3 — So do this instead, in this order

1. **Measure — and note that this takes two sign-ins, which the step used to hide.**
   - **Spend**, from **Management**: Cost Explorer filtered to `AWS Config`, grouped by **usage type**
     and by **linked account**, for the last full month. The usage-type breakdown is what separates
     configuration items from rule evaluations, and only one of those is what step 10 is about.
   - **Volume — and this bullet was half wrong, corrected 2026-08-14 by executing it.** It used to send
     the whole reading to the **Audit** aggregator on the grounds that going account by account "gives the
     same answer for more work". It does not: one loop over the six `awsds-infra-*` profiles with
     `aws configservice select-resource-config --expression "SELECT COUNT(*)"` is a single command, needs
     no sign-in, and grouping the same query by `resourceType` returns **more** than the aggregator's
     summary. **What survives is the second half of the objection, and it is the whole reason the
     aggregator is still needed**: `Log Archive` and `Audit` hold no profile, so those two accounts are
     readable only from the aggregator —
     `aws configservice describe-configuration-aggregators` to find it, then
     `select-aggregate-resource-config`. **Measured: 80-82 recorded resources per account** across the six
     with profiles; the composition is in the log, and a third of it is AWS service defaults that never
     change. **Read the aggregator with Lesson 13 in hand** — Management absent from it does *not* mean
     Management is unrecorded, only that it does not aggregate; (xiii) is answered in 10.4 and nowhere else.
   Record both numbers in `log/stage-01d-org-wide-enablement.md`. Prices are measured, not reasoned
   (Lesson 6), and the same rule applies to volumes.
   **Two caveats on the number you will get, and the first changes what to ask for.** There is no "last
   full month" — the organization is days old — so ask Cost Explorer for the **last 7 days, daily**, and
   record the daily rate rather than a month that does not exist. Cost Explorer also has to be enabled
   before it answers at all, and its first data appears about 24 hours later: if it is not on, turn it on
   and take the measurement in the next session rather than treating an empty report as a low number.
   **Second:** the accounts are nearly empty, so this measures the recorder's floor, not its cost during
   Stages 2-3. That is the honest reason step 10.3 point 2 defers the decision to Stage 12 rather than the
   reason it is written as if the number were final.
2. **Decide against the measured number, not the estimate.** If the item count sits inside the
   USD 2.50-5.00/month band `PRICING.md` projects, the honest answer is to leave the recorder alone and
   revisit at **Stage 12 step 5**, when there is a real bill and Stage 2-3's apply storm is over.
3. **Only if it does not**, deploy the lifecycle-event solution — and note that it must exclude nothing
   Control Tower's own controls and Security Hub's checks depend on, since both consume Config.
   **There are two levers, not one — and the second one points the wrong way here, which is worth writing
   down so it is not proposed again.** The recorder was read in Development on 2026-08-14:
   `allSupported: true`, `includeGlobalResourceTypes: true`, **`recordingFrequency: CONTINUOUS`**,
   `recordingScope: PAID`. The alternative is **`recordingFrequency: DAILY`**, which bills per *item-day*
   rather than per change — and `PRICING.md` §2 measures those at **USD 0.012 per item-day against
   USD 0.003 per change**, so **the break-even is four changes per resource per day, sustained**. Nothing
   in this project is near that: 1d measured an idle account recording essentially nothing, and Stage 6's
   Spark churn creates and destroys resources rather than modifying the same one repeatedly. **`DAILY`
   would multiply this line, not divide it** (Lesson 6 — the intuition that "daily is the cheap one" is
   AWS's framing for a workload this is not). Both levers sit behind the same locked door anyway:
   `GRCONFIGENABLED` denies `PutConfigurationRecorder` whichever field is changed.
4. **Do not unenroll an account to cut the bill.** It is the documented lever and it is the wrong one
   here: `Policy Canary` is the tempting candidate and unenrolling it removes the Control Tower control
   baseline that makes D29's battery a valid test rather than a false pass.

#### 10.4 — The one thing in step 10 that is not about cost: `iam-root-access-key-check` — **DONE 2026-08-14, and the rule was NOT built**

**Decision 8 is no, and this is the residual, written out.** Read the sub-step below for the reasoning it
was decided against; what follows is what execution added.

**Two measurements decided it, and the first changed the price.** Management holds **neither** a
configuration recorder **nor** a delivery channel (verification (xiii)), so decision 8 was never "turn on a
recorder": a delivery channel needs an S3 bucket, and Control Tower's `aws-controltower-config-*` bucket is
in Audit with a policy written for enrolled accounts, which Management is not. The real shape was **a
bucket, a bucket policy, a delivery channel, a recorder and a rule — five hand-made resources in the one
account this project deliberately keeps out of Terraform** (principle 1), for a control whose whole job is
to answer one boolean.

**And the second closed the window the alarm cannot see.** `AccountAccessKeysPresent` reads **`0`**: there
is no root access key on Management today. The rule's value over 1a's alarm was always *state versus
event* — a key created before the alarm existed, or one whose event was missed. **The first of those is now
excluded for good, and the second is a live channel**: the two root sign-ins earlier the same day notified
on **both** subscriptions, an unplanned end-to-end test of trail → S3 → Logs → filter → alarm.

**What is left uncovered, stated so it is not discovered later as a surprise.** If the alarm chain breaks
silently *and* someone creates a root access key inside that window, nothing reports it until a human looks.
That is a real gap and it is accepted, not closed. **It is made smaller by hanging the state read on a
ritual that already exists** rather than on memory (Lesson 5): the break-glass runbook's §6 test already
requires a Management root sign-in, and it now carries the access-key check as one of its steps. A check
that rides an existing procedure is not a control, but it is not an intention either.

**The revision trigger is written rather than left to judgement:** if Management becomes recorded for any
other reason — **Stage 5's Security Hub central configuration is the candidate** — the rule costs nothing
beyond itself and should be enabled at that point. Nothing else needs to change for that to happen.


[D16](../decisions/D16-break-glass.md) makes an access key on the Management root an **invariant** rather
than hygiene — it would be a permanent, unscoped, SCP-immune credential sitting in a file — and, since SCPs
cannot reach the Management account, it names the instrument: the AWS Config managed rule
`iam-root-access-key-check`, *"enabled with the recorder scope in Stage 1d step 10"*. **No sub-step carried
it until 2026-08-11**, which left a detective control over the only unrestricted credential in the project
owed by a step that never created it. This sub-step is that debt, and it starts by correcting the sentence
that assigned it.

**The rule has nothing to do with the recorder scope.** `IAM_ROOT_ACCESS_KEY_CHECK` is **periodic and
parameterless**: it evaluates on a schedule against the account rather than on a configuration item, so no
choice made in 10.3 can turn it on, off, or blind. It sits inside step 10 because both are about Config, not
because one configures the other — so 10.3's decision may be taken without reference to this sub-step, and
this sub-step executed whichever way 10.3 goes.

**Where it has to live is the awkward part: the Management account** — the one account this project
deliberately keeps out of Terraform (principle 1), and the one `plan/cost-model.md` is unsure about, reading
the Config line as "every governed account **except Management**" and asking Stage 1 to confirm it. Resolve
that first, because it decides whether this is a two-minute step or a decision:

```bash
# from Management, as AWS Control Tower Admin (CloudShell)
aws configservice describe-configuration-recorders --region us-west-2
aws configservice describe-delivery-channels --region us-west-2
```

An **empty list is the answer, not an error** (Lesson 13): `"ConfigurationRecorders": []` means Control Tower
left Management unrecorded, a Config rule has nothing to run in, and **decision 8** below applies. This is
**verification (xiii)** — renumbered from (x) on 2026-08-14, because 1c had already used that numeral for a
different question and the landing-zone numerals are one sequence across 1a-1d.

**And this sub-step is only possible because of what blocks 10.2: Management is exempt from SCPs.** The
`GRCONFIGENABLED` deny that makes a hand-made recorder impossible in every governed account does not reach
the management account, so creating one there needs no exemption and borrows no role. The asymmetry is
worth stating rather than discovering: the account this project keeps out of Terraform is also the only one
where this particular resource can be made by hand.

**Do not deploy it as an organization Config rule from the Audit delegated administrator** — the obvious
route, and the one that fails on this particular target. AWS Config does not create the service-linked role
in the management account on its own, and without that role a delegated administrator cannot deploy into it;
member accounts work, the management account does not. Since this rule is wanted on Management *only*, the
organization-rule mechanism buys nothing here and adds a failure mode.

**So create it by hand, in Management, as `AWS Control Tower Admin`** — the same identity and the same
precedent as 1a step 5's metric filter and alarm, which are also hand-made Management resources this project
accepts as permanently outside Terraform. Record the rule name and its first evaluation in
`log/stage-01d-org-wide-enablement.md`, beside the two numbers from 10.3.

**What it adds over the alarm 1a already built — because if the answer were "nothing" this sub-step would be
deleted rather than written.** `awsds-org-root-activity` fires on *any* root activity that is not an AWS
service event, so a root `iam:CreateAccessKey` **already** trips the break-glass alarm at the moment it
happens. The rule answers a different question, and the difference is **event versus state**: the alarm sees
the *act*, and only while the chain (trail → S3 → Logs → filter → alarm) is intact; the rule reports whether a
key **exists now** — including one created before 1a step 5 existed, one whose event was missed, and one that
is still there a month after everyone agreed it had been deleted.

**The fallback, if decision 8 goes against the recorder, and it answers the state question too.** From
Management, `aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'` returns `1` when a
root access key exists and `0` when it does not — the same fact, free, with no recorder and no rule. What it
does not do is *watch*: it is a command someone has to remember to run, which is an intention rather than a
control (Lesson 5). That is the whole trade in decision 8.

### Step 11 — Enable organization-wide resource sharing, so the Lake Formation shares of Stage 5 can exist (D22, INT-11)

Two settings to make now, **in two different accounts** — which is half of why this step is easy to get
wrong — and neither of which announces its absence.

#### 11.1 — `ram:EnableSharingWithAwsOrganization`, called from the *Management* account

It enables
trusted access for RAM across the organization; it is not a Data Governance setting and cannot be done
from there. Without it, a Lake Formation grant to another account produces an AWS RAM *invitation* that
somebody has to accept by hand, and it reappears every time the share is recreated. With it, accounts
inside the organization receive shares directly.

#### 11.2 — Lake Formation cross-account version — **already satisfied; do not write anything** (measured 2026-08-14)

Versions below 3 cannot grant to an Organization or an OU at all, only to an explicit list of account IDs —
and this project has three consumers at N=1, one more per business unit (D35), with more implied by every
`plan/institutional-delta.md` row about scale. **This step used to set that version. It no longer has to.**

`aws lakeformation get-data-lake-settings --profile awsds-infra-data --region us-west-2` reads, in an
account with no lake and no administrator:

```
Parameters: { "CROSS_ACCOUNT_VERSION": "4", "SET_CONTEXT": "TRUE" }
DataLakeAdmins: []   CreateDatabaseDefaultPermissions / CreateTableDefaultPermissions: IAM_ALLOWED_PRINCIPALS = ALL
```

So the requirement is met by the account's default, **verification (v) is answered without acting** — the
version is above 3 with no lake in the account — and the whole `put-data-lake-settings` hazard below is
avoided by not making the call. **Record the reading in the log; do not "confirm" it by writing it back.**

**Why the hazard is still documented, in full:** it does not go away, it moves to Stage 5. The version lives
inside `DataLakeSettings`, and **`put-data-lake-settings` replaces that whole structure rather than patching
it** — called with only `Parameters` set, it clears `DataLakeAdmins`, `CreateDatabaseDefaultPermissions` and
`CreateTableDefaultPermissions` in the same call. The safe shape is always get-modify-put:

```bash
aws lakeformation get-data-lake-settings --profile awsds-infra-data --region us-west-2 > "$SCRATCH/lf.json"
# edit DataLakeSettings.Parameters, keep every other key
aws lakeformation put-data-lake-settings --profile awsds-infra-data --cli-input-json "file://$SCRATCH/lf.json"
```

Note also that changing these settings requires being a Lake Formation **data lake administrator** or
holding `lakeformation:PutDataLakeSettings` outright — the infrastructure user has the latter through
`InfrastructureAccess`, so no administrator has to be registered first; Stage 5 still creates the real one.

**And this is what the step owes Stage 5 — which is now the *only* thing 11.2 produces, and it grew**
(added 2026-08-09, sharpened 2026-08-14). `aws_lakeformation_data_lake_settings` is the Terraform face of the
same replace-the-whole-structure API, and Stage 5 declares the data lake administrators through it. A
resource that names `admins` and omits `parameters` **resets both parameters on the first apply** — and the
failure that follows is INT-11's: the grant succeeds on the producer side and the share never arrives on the
consumer side, with nothing anywhere reporting an error. **The setting nobody chose is now the setting most
likely to be lost**, precisely because it was never typed by anyone. So:

- **Write the requirement into `log/stage-01d-org-wide-enablement.md` as an instruction to Stage 5**, with
  the values as *read*, not as remembered: the Stage 5 resource must carry
  `parameters = { CROSS_ACCOUNT_VERSION = "4", SET_CONTEXT = "TRUE" }` alongside its `admins` — **both
  keys**, and re-read immediately before writing it, since an account default can move again between now
  and then.
- **Stage 5 step 7 repeats the check from 11.3 after its first apply**, not only before it. Verifying a
  setting before the thing that overwrites it runs is the same class of mistake as verifying with a
  command that returns empty either way.
- **One new thing to test there rather than assume, and 1c is why.** Cross-account version 4 vends
  credentials through **`sts:SetContext`**, and `awsds-org-rcp-perimeter`'s
  `EnforceOrgIdentitiesOnRoleAssumption` names exactly that action. In-organization consumers populate
  `aws:PrincipalOrgID` and the AWS-service path is carved out, so the expected answer is "no effect" — but
  that is the same reasoning that was expected to hold for `AssumeRoleWithSAML` and cost every SSO user
  access to six accounts (Lesson 24). **If the first cross-account grant fails, the RCP is the first
  suspect**, and no `sts:` action is added to that document without re-reading `CT.STS.PV.1`'s exclusion
  note.

#### 11.3 — How to verify it, because the obvious command does not
`aws ram get-resource-share-associations` requires an `--association-type` and lists the associations of
shares that already exist — with no share yet created it returns an empty list, which is
indistinguishable from the failure it is supposed to detect (Lesson 13). The two checks that actually
answer the question:

```bash
aws organizations list-aws-service-access-for-organization --query "EnabledServicePrincipals[?ServicePrincipal=='ram.amazonaws.com']"
```

```bash
aws lakeformation get-data-lake-settings --profile awsds-infra-data --query 'DataLakeSettings.Parameters'
```

The first is run from Management and must return `ram.amazonaws.com`; the second must read a
cross-account version of 3 or above back. Confirming a silent-failure mode with a command that is itself
silent is how INT-11 stays open for a month.

**Both have a before-reading taken on 2026-08-14, so the after-reading has something to differ from.** The
trusted-access list answers from **Identity**, not only from Management (`awsds-infra-identity`), and holds
the **seven** principals of `INV-09` — `access-analyzer`, `cloudtrail`, `config`, `controltower`, `iam`,
`member.org.stacksets.cloudformation`, `sso` — with **`ram.amazonaws.com` absent**. So 11.1 has real work,
and its success is one name appearing in a list of seven that becomes eight; restate `INV-09` when it lands.
The second reads `4` already (11.2).

#### 11.4 — Not here, and deliberately: the third INT-11 item

The
**`AWSLakeFormationCrossAccountManager`** managed policy on the grantor and
`ram:AcceptResourceShareInvitation` on the data lake administrator role **in each consumer account** are
the fallback path if 11.1 or 11.2 is ever unavailable — and **neither role exists yet**: the data lake
administrator is created in Stage 5, the consumer-side roles in Stage 5 and Stage 9. Attempting it here
is attaching a policy to a principal that has not been written. It is recorded here because INT-11 is
settled here; it is *executed* in Stage 5 step 7.

#### 11.5 — Why this step is in the landing zone at all

It is organization-level and manual, like everything else in this stage. Stage 5 step 7 assumes it and will fail confusingly without it: the grant appears to succeed
on the producer side and the resource simply never shows up on the consumer side.

#### 11.6 — Verify while executing (v): **answered 2026-08-14, before execution**

The question was whether the Lake Formation cross-account version can be *raised* to 3+ in an account with
no lake in it. It reads **4** in Data Governance with no lake, no administrator and nothing registered — so
the version is not a thing this account has to be argued into, and the contingency this sub-step carried
("if it cannot, the setting moves into Stage 5") is void. What moves into Stage 5 instead is the *defence*
of a value nobody set: 11.2's last bullet.

### Step 12 — The Region ceiling on `Security`, the OU 7.7 never targeted (open question 16) — **DONE 2026-08-14**

**Decision 10 was taken and it was yes**: all three controls are on `Security`, `ExemptAssumeRoot` set on
`AWS-GR_RESTRICT_ROOT_USER` and deliberately absent from the access-key one (D16), both confirmed by
reading the document (`CHK-1`/`CHK-2` in `./aws/org-policies.sh`) rather than by probing, because no
principal here is root (Lesson 22). **The step's one real unknown is answered: `Security` accepts
`enable-control` even though it is Control Tower's foundational OU.** Control Tower packed the enablements
in a **third** shape — a new document (`aws-guardrails-KAmzSQ`, `p-idgyiios`) for the Region control, the
pre-existing AWS guardrail (`p-2xyaqn66`, 11 → 13 statements) for the root ones — so Lesson 23's rule is
not "one of two layouts" but that the layout is unknowable without reading. The text below is kept as
written, because it is the reasoning that produced the decision.

**Added 2026-08-14.** 1c step 7.7 enabled `CT.MULTISERVICE.PV.1` (allow `us-west-2`) on the five OUs its own
order named — `Policy Test`, `Workloads`, `Data`, `Interactive`, `Identity` — and deliberately not on
`Sandboxes` (D37, which is governed by inheritance from `Interactive`). **`Security` was simply outside the
step.** It is not drift and not a regression; it is a gap that was inherited rather than decided, and
`Log Archive` and `Audit` are consequently **the only governed accounts where a resource may be created in
any Region** — the two accounts holding the immutable copy of the trail and the organization's findings.

#### 12.1 — Why this is not a copy of 7.7

- **`Security` is Control Tower's own foundational OU**, its guardrail is AWS's rather than this project's
  (11 statements, not 8), and **Control Tower places resources in those accounts itself.** A Region ceiling
  there constrains a service that manages the landing zone, not a data scientist.
- **So read the exemptions first, against the roles that actually operate there.** Verification (vii)
  demonstrates the method and it is the same one: enable nowhere, read `describe-policy` from Identity, and
  check the resulting document's `NotAction` list and its Control Tower role exemptions. **Bind to the
  `Sid`, never to the document id or name** (Lesson 23) — 7.7 measured Control Tower packing the same
  control into a *different* document on `Identity` and `Data` than on the other three OUs.
- **What is in those accounts today is small and known**: the organization trail's bucket and the access-log
  bucket in Log Archive, the Config aggregator and `awsds-org-external-access` in Audit — all `us-west-2`.
  What arrives later is Stage 4's GuardDuty, Stage 5's Security Hub and Stage 11's Macie, each delegated to
  Audit and each `us-west-2` in this design. **The ceiling is therefore free today and is a constraint on
  those three stages**, which is the honest way to state it.

#### 12.2 — The measurement problem, which is new here and has to be planned for

**The battery cannot reach these two accounts.** `./aws/probes/scp-battery.sh` maps every probe's account
token to a **CLI profile**, and the infrastructure user has no assignment in Log Archive or Audit by design
(`ORGANIZATION.md`), so there is no profile to map. The alternatives, in order of preference:

1. **By hand in CloudShell**, signed in as `AWS Control Tower Admin` → `AWSAdministratorAccess`, in each of
   the two accounts: one call that must now fail in `us-east-1` and one that must still succeed in
   `us-west-2` — `ec2 create-key-pair --dry-run` is 7.7's own choice, because it authorizes with nothing but
   a name and needs no AMI lookup (the first version of that probe resolved an AMI through `ssm:GetParameter`
   *in the denied region* and measured itself). Read the **wording** of the failure — *"explicit deny in a
   service control policy"* — and the policy id it names, never the exit code.
2. **The document read from Identity**, which is not optional and not a substitute: it is what proves the
   exemption list, and it is the only instrument for anything a probe cannot produce a principal for
   (Lesson 22).

**Do not create a profile for these accounts to make the battery work.** That is an SSO assignment into the
two most sensitive member accounts, bought to save two manual commands, and it would outlive the reason for
it.

#### 12.3 — The two root-user controls belong to the same decision

7.7 also enabled `AWS-GR_RESTRICT_ROOT_USER` and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` on those same five
OUs and not on `Security`. The argument that made them nearly free elsewhere holds identically here — member
accounts hold no root credentials at all since 1a 6.4, so the population is empty and the one live side
effect is `sts:AssumeRoot` — **which is exactly why the `ExemptAssumeRoot` parameter must be set if they are
enabled, and why no probe can confirm it**: every principal available here is an Identity Center role and
`ArnLike …:root` never matches one. Read `GRRESTRICTROOTUSER` back out of the attached document and check
that it ANDs `Null: aws:AssumedRoot = true` (Lesson 22). The access-key control carries no exemption and must
not (D16).

#### 12.4 — Reversible, and known to be

Disabling a control removes it: 7.7 disabled `CT.MULTISERVICE.PV.1` on `Sandboxes` and the document
`p-h7lc62d0` ceased to exist with it. So decision 10 is a decision to be *taken*, not one to be feared —
the cost of getting it wrong is one disable, plus whatever ran in the meantime.

#### 12.5 — Verify while executing (xiv):

that a Region control on `Security` denies `us-east-1` and leaves `us-west-2` working **in both Log Archive
and Audit**, and that Control Tower's own operations in those accounts are unaffected — the second half is
answered by the exemption reading of 12.1, not by a probe, and re-checked at the next landing-zone update.

---

## Deliverables of 1d

Each one is written so that its output differs between working and broken (Lesson 13):

- **The audit trail survives its own administrator — or the log says why it does not.** Resolve the real
  bucket name first; the `*` below is this document's shorthand, not a glob the CLI expands, and the prefix
  this file carried until 2026-08-14 (`aws-controltower-logs-`) matches **nothing** in this landing zone,
  returning a `None` that reads like a failed lock:

  ```bash
  BUCKET=$(aws s3api list-buckets --query "Buckets[?starts_with(Name,'aws-controltower-cloudtrail-logs-')].Name | [0]" --output text)
  aws s3api get-object-lock-configuration --bucket "$BUCKET"
  ```

  Run it **inside Log Archive** — CloudShell under `AWS Control Tower Admin` → `AWSAdministratorAccess`, per
  "Who executes what"; the infrastructure user has no assignment there and no profile to pass. It must
  report `COMPLIANCE`, with a retention shorter than the bucket's lifecycle expiration
  (`aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET"`). **If decision 9 went the other way,
  this deliverable is the log entry instead**: which alternative was chosen, and the residual it leaves —
  `CTS3PV8` permits `s3:DeleteObjectVersion` to the account's administrator, and that sentence is the
  residual.
- **Stage 5's shares have somewhere to land:**
  `aws organizations list-aws-service-access-for-organization` lists `ram.amazonaws.com` — **eight
  principals where the before-reading had seven** — and
  `aws lakeformation get-data-lake-settings --profile awsds-infra-data` reports a cross-account version of 3
  or above, which it **already did before the stage started** (4, with `SET_CONTEXT: TRUE`). The half of
  this deliverable that can still fail is therefore the RAM half; the Lake Formation half is a reading whose
  only failure mode is finding it *changed*. *(Note what this deliverable used to say:
  `aws ram get-resource-share-associations` from the Data Governance profile, which returns an empty list
  both when sharing is enabled and when it is not.)*
- **Stage 5 is told, in writing, what to preserve:** the log carries
  `parameters = { CROSS_ACCOUNT_VERSION = "4", SET_CONTEXT = "TRUE" }` as an instruction to Stage 5's
  `aws_lakeformation_data_lake_settings`, with both keys. A value nobody typed is a value nobody defends,
  and INT-11's failure mode is silent on both sides.
- **The Region ceiling on `Security` is decided rather than inherited** (step 12): either the control is
  enabled and one command in each of Log Archive and Audit shows `us-east-1` denied while `us-west-2` works,
  or decision 10 declined it and the log says so. **The failure this deliverable prevents is the stage
  closing with the question still merely written down** — which is how open question 16 got here.
- **The Config number is measured and written down**, not estimated — both numbers from 10.3, in
  `log/stage-01d-org-wide-enablement.md` (Lesson 6).
- **Something other than a person's memory reports whether the break-glass root has an access key** (10.4,
  D16). Either the rule exists and answers — from Management,
  `aws configservice describe-compliance-by-config-rule --config-rule-names <name>` reports `COMPLIANT` —
  or decision 8 went the other way and the standing answer is
  `aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'` returning `0`, with the log
  saying **which of the two it is**. The failure this deliverable exists to prevent is the stage closing
  with neither, which is what happened to this control between D16 and 2026-08-11.

## Decisions due while executing

**Blocking questions for the user: none.** Two decisions are *made* during this stage, each written into
`log/stage-01d-org-wide-enablement.md` (Lesson 16) — and **the first of them is permanent**:

| # | Decision | Step | Reversible? |
|---|---|---|---|
| 3 | **The Object Lock retention period** | 9.3 | **No — compliance mode cannot be shortened and Object Lock cannot be disabled** |
| 4 | ~~Whether the Config recorder is left alone after the measurement~~ **TAKEN 2026-08-14: left alone, revisit at Stage 12 step 5.** ~USD 0.5/month recurring, below `PRICING.md`'s band, against a lifecycle-event Lambda with a StackSet and a role per account — and an exclusion list that is wrong breaks a detective control silently, since Control Tower's controls and Stage 5's Security Hub both consume Config. **The measured composition is what killed the exclusion list**: a third of each account's 82 items are AWS service defaults, recorded once and never changed, so removing them saves under a dollar across the organization *in total*. **The revision signal is EC2/ENI churn, not the resource count** | 10.3 | Yes |
| **8** | ~~Whether a Config recorder is turned on in Management for the sake of one rule~~ **TAKEN 2026-08-14: no.** The invariant is left to 1a's alarm plus the `get-account-summary` read, and **the residual is written rather than assumed away** — see 10.4. Two measurements decided it: Management has **neither** a recorder nor a delivery channel, so this was never "one resource" but a bucket, a delivery channel, a recorder and a rule, all hand-made in the account kept out of Terraform; and `AccountAccessKeysPresent` reads **`0`**, which closes the one window the alarm cannot see — a key created before 1a step 5 existed. **Revision trigger: if Management becomes recorded for any other reason, the rule costs nothing and goes on then** — Stage 5's Security Hub central configuration is the candidate | 10.4 | Yes |
| **9** | **Whether step 9 is performed at all, and by which principal.** `CTS3PV8` exempts `AWSControlTowerExecution` and nobody else, so the choices are: **borrow that role from Management** (one permanent setting, an unscoped role used by hand, and a setting whose survival across a landing-zone update is unknown); **decline and record the residual** (the Log Archive administrator can delete log object versions, which is the exposure the step exists to close); or **a second, project-owned trail with its own locked bucket** (a new recurring line and a second copy of the same data). **Decision 3 only exists if this one says yes** | 9.6 | The *choice* is; **its consequence is not** — see decision 3 |
| **10** | **Whether `Security` gets the Region ceiling, and whether the two root-user controls go with it.** Free either way; the trade is a constraint on Stages 4, 5 and 11 (all `us-west-2` in this design) against being the only governed accounts with no Region ceiling. **If yes, `ExemptAssumeRoot` is not optional** and only a document read can confirm it | 12 | Yes — disabling a control deletes its document, measured on `Sandboxes` in 7.7 |

*The numbering is the landing zone's: decision 2 belongs to
[Stage 1b](stage-01b-identity-and-controls.md), and 1, 5, 6 and 7 to
[Stage 1c](stage-01c-preventive-policies.md). **Decision 8 was added on 2026-08-11**, by the review that
found D16 assigning `iam-root-access-key-check` to a step that never carried it; **9 and 10 on 2026-08-14**,
by this stage's revision against 1c's findings. Each continues the landing zone's sequence rather than
renumbering anything. **Blocking questions for the user: still none** — 9 and 10 are both taken while
executing, with the readings that inform them listed in the step.*

## Risks

- **Step 9's compliance-mode retention cannot be shortened, and Object Lock cannot be disabled.** A
  retention chosen too long makes the Log Archive bucket an archive nobody chose to pay for; one longer than
  the lifecycle expiration makes the landing zone's own deletions fail. This is the one permanent act in
  the stage, and it is the reason 9.3 is a decision row rather than an instruction.
- **Step 9 now runs, if it runs, as `AWSControlTowerExecution` — the most privileged role in the account,
  borrowed by hand.** Two risks ride along and they are different from each other: the *use* (an unscoped
  session in the account holding the audit trail, which is why the log records the exact call), and the
  *durability* (a manual change to a Control Tower-managed bucket, made through Control Tower's own role, may
  be re-applied away by a landing-zone update — verification (iv)'s second half).
- **Step 11 fails silently, and it fails at Stage 5 rather than here.** Nothing in this stage reports that
  org-wide sharing is missing; the Lake Formation grant appears to succeed on the producer side and the
  resource never appears on the consumer side. 11.3's before/after readings are what turn that into a
  result — and since 11.2 now sets nothing, **the risk moved to Stage 5's first apply**, where a resource
  omitting `parameters` resets a version nobody chose and reintroduces exactly this failure.
- **Step 12 constrains the two accounts that no probe here can reach.** There is no CLI profile in Log
  Archive or Audit, so the battery cannot regress-test whatever step 12 attaches, ever. Anything enabled
  there is measured by hand at the time and re-read from the document afterwards; there is no automated
  safety net behind it, which is a reason to keep what goes on that OU minimal rather than a reason to avoid
  it.
- **Nothing here is torn down between sessions** — everything is `[P]` (D11).

## Verifications to answer while executing

Record every answer in `log/stage-01d-org-wide-enablement.md`, including the ones that come out fine.
**The numerals are the landing zone's**, so they are not contiguous here.

| # | Question | Step | State |
|---|---|---|---|
| iv | Does enabling Object Lock on the Control Tower-managed bucket raise landing-zone drift — **and does it survive a landing-zone update, an account update or a re-enrollment?** | 9.5 | Open. The second half was added 2026-08-14 and **cannot be closed in-session**: record it provisionally and name the event that settles it, as 1b 5.1 did for (vi) |
| v | Can the Lake Formation cross-account version be raised to 3+ with no lake in the account? | 11.6 | **Answered 2026-08-14, before execution: the question is void.** It reads **4** already, with `SET_CONTEXT: TRUE`, in an account with no lake and no administrator |
| **xiii** | **Does the Control Tower landing zone record the Management account at all?** `plan/cost-model.md` assumes it does not and asks Stage 1 to confirm; 10.4 is the first step that has to know, and the Config row's account count is wrong by one either way | 10.4 | **Answered 2026-08-14: it does not.** From Management as CT Admin, both `describe-configuration-recorders` and `describe-delivery-channels` return an **empty list** — the answer, not an error (Lesson 13). Corroborated from the other side: the organization aggregator in Audit lists **eight** accounts and Management is not among them. `plan/cost-model.md`'s assumption is confirmed and the Config row's account count is right. **Renumbered from (x) on 2026-08-14** — 1c had already answered a different question under that numeral, and the landing-zone numerals are one sequence across 1a-1d |
| **xiv** | Does a Region control on `Security` deny `us-east-1` and leave `us-west-2` working in **both** Log Archive and Audit, without touching Control Tower's own operations there? | 12.5 | **First half answered 2026-08-14** in both accounts, by hand in CloudShell: `us-east-1` denied naming `p-idgyiios`, `us-west-2` `DryRunOperation`. **Second half provisional** — the exemption reading covers it (the four Control Tower roles are exempt, `config:*` entirely), and it is re-checked at the **next landing-zone update, account update or re-enrollment**, exactly as (iv) and (vi) are |

---

*Stage index: [plan/stages/INDEX.md](INDEX.md) · Previous: [Stage 1c](stage-01c-preventive-policies.md) · Next: [Stage 2](stage-02-terraform-foundation.md)*
