# Stage 1d — Audit trail, Config scope, org-wide enablement

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | **[Stage 1b](stage-01b-identity-and-controls.md) complete** — every step here runs inside a member account and needs step 5's profiles. **Stage 1c is not a prerequisite**: none of these three steps depends on a policy being attached, so this stage can be executed before it if a session is short |
| **Consumes** | [D12](../decisions/D12-budget-ceiling.md), [D16](../decisions/D16-break-glass.md), [D22](../decisions/D22-data-governance-account.md), [D29](../decisions/D29-policy-canary.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | **The two organization-level halves of [INT-11](../integrations.md)** — org-wide RAM sharing and Lake Formation cross-account v3. **Also closes [D16](../decisions/D16-break-glass.md)'s last unbuilt deliverable** (10.4). The third (`AWSLakeFormationCrossAccountManager` on the grantor) is Stage 5 step 7, because the role does not exist yet (11.4) |
| **Log** | `log/stage-01d-org-wide-enablement.md` |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Three steps, and they keep their numbers: 9, 10 and 11.** The landing zone's second half was one stage
until 2026-08-09, and the step numbers did not change in the split — every other file's `Stage 1d step 9`
reference is this stage's step 9.

**The three steps are independent of each other** and can be done in any order, or in three separate
sittings. What they have in common is that each is organization-level, manual, and done from inside a
member account rather than from Management alone.

## The stage at a glance

| # | What | Identity | Consumes | Why it is here and not later |
|---|---|---|---|---|
| 9 | Object Lock, compliance mode, on the log bucket | CT Admin @ Log Archive | D33, D34 | Before there is anything worth hiding in the trail |
| 10 | Measure AWS Config, then decide — **and, in 10.4, the rule D16 owes** | CT Admin @ Management + Audit | D12, D16, D29 | The landing zone's largest recurring line. **10.4 is not about that line at all** and is independent of what 10.3 decides |
| 11 | Org-wide RAM sharing + LF cross-account v3 | CT Admin @ Management / Infra user @ Data | D22, D35 | Stage 5 fails **silently** without it |

## Who executes what

| Steps | Identity | Sign-in path |
|---|---|---|
| 10.3 (Cost Explorer), **10.4 (the Config rule, which exists only in Management)**, 11.1 (RAM) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 9 (Object Lock, *in Log Archive*), 10 (the Config aggregator lives in Audit) | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Log Archive** / **Audit** — the infrastructure user has *no* assignment in either (`ORGANIZATION.md`) |
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

---

## To execute

### Step 9 — Make the audit trail tamper-evident

An audit log that the compromised party can edit is not an audit log. Do this before there is anything
worth hiding in it.

#### 9.1 — Identify the right bucket first, because there are at least two and one of them must not be touched

- **Object Lock goes on the CloudTrail log bucket, `aws-controltower-logs-*`, in the Log Archive
  account.**
- **It must never go on `aws-controltower-s3-access-logs-*`.** That bucket is the destination for S3
  server access logging, and **S3 buckets with Object Lock cannot be used as a server access log
  destination** — locking it silently stops access logging for the bucket beside it.
- **Check the landing zone version while you are here.** From landing zone 4.0 the *Config* logs move to
  `aws-controltower-config-logs-*` in the Config integration (Audit) account, while the CloudTrail logs
  stay in Log Archive. The target of this step is the CloudTrail bucket either way; knowing the version
  tells you whether a second bucket exists that this step deliberately does not cover.

#### 9.2 — Use compliance mode, and this is the step that limits D33

The earlier wording left this
unsaid, so it was an intention rather than a control (Lesson 5). `AWSControlTowerAdmins` is administrator
*of the Log Archive account*, so the principal this step defends against holds
`s3:BypassGovernanceRetention`: **in governance mode it walks straight through.** In compliance mode a
locked object version cannot be deleted or overwritten by anyone, including that account's root. **Since
D34 that principal is permanent**, so this is not a control covering a two-week bootstrap window — it is
what keeps the audit trail surviving its own administrator for as long as the organization exists.
Getting the mode wrong here is a permanent hole, not a temporary one.

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

#### 9.4 — CloudTrail log file validation

Control Tower's `aws-controltower-BaselineCloudTrail` is
expected to have it on already; **verify rather than enable**, because editing the trail is landing-zone
drift (1a step 5 makes the same distinction: adding a metric filter to the log group is not an edit to
the trail). `aws cloudtrail get-trail --name aws-controltower-BaselineCloudTrail` reports
`LogFileValidationEnabled`.

#### 9.5 — Verify while executing (iv):

that enabling Object Lock on the Control Tower-managed bucket does
not raise landing-zone drift. Record the answer.


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
  warns about for direct assignments.
- The documented path is a **deployed solution**: a Lambda driven by Control Tower lifecycle events
  (`UpdateLandingZone`, `CreateManagedAccount`, `UpdateManagedAccount`) that re-applies a chosen
  resource-type list through each account's `AWSControlTowerExecution` role. That is a real piece of
  infrastructure with its own failure modes, not a checkbox.

#### 10.3 — So do this instead, in this order

1. **Measure — and note that this takes two sign-ins, which the step used to hide.**
   - **Spend**, from **Management**: Cost Explorer filtered to `AWS Config`, grouped by **usage type**
     and by **linked account**, for the last full month. The usage-type breakdown is what separates
     configuration items from rule evaluations, and only one of those is what step 10 is about.
   - **Volume**, from **Audit**: 1a made Audit the **Config aggregator** account, so the item counts for
     every enrolled account are readable there in one place —
     `aws configservice describe-configuration-aggregators` to find it, then the Config console's
     aggregated view. Going account by account under the `awsds-infra-*` profiles gives the same answer
     for more work, and misses Log Archive and Audit, where the infrastructure user has no assignment.
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
4. **Do not unenroll an account to cut the bill.** It is the documented lever and it is the wrong one
   here: `Policy Canary` is the tempting candidate and unenrolling it removes the Control Tower control
   baseline that makes D29's battery a valid test rather than a false pass.

#### 10.4 — The one thing in step 10 that is not about cost: `iam-root-access-key-check`

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
left Management unrecorded, a Config rule has nothing to run in, and **decision 8** below applies.

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

#### 11.2 — Lake Formation cross-account version 3 or above, set in the Data Governance account
(`awsds-infra-data`). Versions below 3 cannot grant to an Organization or an OU at all, only to an
explicit list of account IDs — and this project has three consumers at N=1, one more per business unit
(D35), with more implied by every `plan/institutional-delta.md` row about scale.

**Prefer the console for this one, and if you use the CLI, read this first.** The version lives inside
`DataLakeSettings`, and **`put-data-lake-settings` replaces that whole structure rather than patching
it** — call it with only `Parameters` set and you have just cleared `DataLakeAdmins`,
`CreateDatabaseDefaultPermissions` and `CreateTableDefaultPermissions` in the same call. The safe shape
is get-modify-put:

```bash
aws lakeformation get-data-lake-settings --profile awsds-infra-data > /tmp/lf.json
# edit DataLakeSettings.Parameters.CROSS_ACCOUNT_VERSION to "3", keep every other key
aws lakeformation put-data-lake-settings --profile awsds-infra-data --cli-input-json file:///tmp/lf.json
```

Today the structure is nearly empty, which is exactly why this is cheap to do now and expensive to do
after Stage 5 has registered a lake and named its administrators. Note also that changing these settings
requires being a Lake Formation **data lake administrator** or holding
`lakeformation:PutDataLakeSettings` outright — the infrastructure user has the latter through
`InfrastructureAccess`, so no administrator has to be registered first; Stage 5 still creates the real
one.

**And this is what the step owes Stage 5, because the value set here is the one Stage 5 will silently
overwrite** (added 2026-08-09). `aws_lakeformation_data_lake_settings` is the Terraform face of the same
replace-the-whole-structure API, and Stage 5 declares the data lake administrators through it. A resource
that names `admins` and omits `parameters` **resets `CROSS_ACCOUNT_VERSION` to its default on the first
apply** — and the failure that follows is INT-11's: the grant succeeds on the producer side and the share
never arrives on the consumer side, with nothing anywhere reporting an error. So:

- **Write the requirement into `log/stage-01d-org-wide-enablement.md` as an instruction to Stage 5**, not
  only the value that was set: the Stage 5 resource must carry
  `parameters = { CROSS_ACCOUNT_VERSION = "3" }` alongside its `admins`.
- **Stage 5 step 7 repeats the check from 11.3 after its first apply**, not only before it. Verifying a
  setting before the thing that overwrites it runs is the same class of mistake as verifying with a
  command that returns empty either way.

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

#### 11.6 — Verify while executing (v):

that the Lake Formation cross-account version can be raised to 3+
in an account that has no lake in it yet. If it cannot, that setting moves into Stage 5 and the rest of
this step stays here.


---

## Deliverables of 1d

Each one is written so that its output differs between working and broken (Lesson 13):

- **The audit trail survives its own administrator:** resolve the real bucket name first — the `*` in
  `aws-controltower-logs-*` is this document's shorthand, not a glob the CLI expands, and pasting it returns
  a bucket-not-found that reads like a failed lock:

  ```bash
  BUCKET=$(aws s3api list-buckets --query "Buckets[?starts_with(Name,'aws-controltower-logs-')].Name | [0]" --output text)
  aws s3api get-object-lock-configuration --bucket "$BUCKET"
  ```

  Run it **inside Log Archive** — CloudShell under `AWS Control Tower Admin` → `AWSAdministratorAccess`, per
  "Who executes what"; the infrastructure user has no assignment there and no profile to pass. It must
  report `COMPLIANCE`, with a retention shorter than the bucket's lifecycle expiration
  (`aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET"`).
- **Stage 5's shares have somewhere to land:**
  `aws organizations list-aws-service-access-for-organization` (from Management) lists `ram.amazonaws.com`,
  and `aws lakeformation get-data-lake-settings --profile awsds-infra-data` reports a cross-account version
  of 3 or above. *(Note what this deliverable used to say:
  `aws ram get-resource-share-associations` from the Data Governance profile, which returns an empty list
  both when sharing is enabled and when it is not.)*
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
| 4 | Whether the Config recorder is left alone after the measurement | 10.3 | Yes |
| **8** | **Whether a Config recorder is turned on in Management for the sake of one rule** — ~USD 0.50-1/month for the same shape of recorder every other governed account already carries, plus a hand-made resource in the account this project keeps out of Terraform — **or the invariant is left to 1a's alarm plus the `get-account-summary` check**, which is an intention rather than a control (Lesson 5) | 10.4 | Yes |

*The numbering is the landing zone's: decision 2 belongs to
[Stage 1b](stage-01b-identity-and-controls.md), and 1, 5, 6 and 7 to
[Stage 1c](stage-01c-preventive-policies.md). **Decision 8 was added on 2026-08-11**, by the review that
found D16 assigning `iam-root-access-key-check` to a step that never carried it — it continues the landing
zone's sequence rather than renumbering anything.*

## Risks

- **Step 9's compliance-mode retention cannot be shortened, and Object Lock cannot be disabled.** A
  retention chosen too long makes the Log Archive bucket an archive nobody chose to pay for; one longer than
  the lifecycle expiration makes the landing zone's own deletions fail. This is the one permanent act in
  the stage, and it is the reason 9.3 is a decision row rather than an instruction.
- **Step 11 fails silently, and it fails at Stage 5 rather than here.** Nothing in this stage reports that
  org-wide sharing is missing; the Lake Formation grant appears to succeed on the producer side and the
  resource never appears on the consumer side. 11.6's verification is what turns that into a result.
- **Nothing here is torn down between sessions** — everything is `[P]` (D11).

## Verifications to answer while executing

Record every answer in `log/stage-01d-org-wide-enablement.md`, including the ones that come out fine.
**The numerals are the landing zone's**, so they are not contiguous here.

| # | Question | Step |
|---|---|---|
| iv | Does enabling Object Lock on the Control Tower-managed bucket raise landing-zone drift? | 9.5 |
| v | Can the Lake Formation cross-account version be raised to 3+ with no lake in the account? | 11.6 |
| x | **Does the Control Tower landing zone record the Management account at all?** `plan/cost-model.md` assumes it does not and asks Stage 1 to confirm; 10.4 is the first step that has to know, and the Config row's account count is wrong by one either way | 10.4 |

---

*Stage index: [plan/stages/INDEX.md](INDEX.md) · Previous: [Stage 1c](stage-01c-preventive-policies.md) · Next: [Stage 2](stage-02-terraform-foundation.md)*
