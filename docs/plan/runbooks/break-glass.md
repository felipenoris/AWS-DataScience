# Runbook — Break-glass (Management account root)

| | |
|---|---|
| **Credential** | The **Management account root user**, and nothing else ([D16](../decisions/D16-break-glass.md)) |
| **Built by** | [Stage 1a](../stages/stage-01a-landing-zone.md) steps 1 and 5 |
| **Detects use** | CloudWatch alarm **`AWS Break Glass Alert`** → SNS `awsds-org-break-glass-alerts` (e-mail + SMS) |
| **Last tested** | **2026-08-14** — **unplanned, and it counts**: two root sign-ins to activate *IAM user and role access to Billing* (Stage 1d step 10) notified on **both** channels, and `AccountAccessKeysPresent` read `0` the same day, so §6 steps 3 and 4 were both exercised end to end. The last *deliberate* test is **2026-08-09** — root sign-in, no actions, delivered on both channels ([log](../../log/log-stage-01a-landing-zone.md)) |

---

## 0. What this is

**The credential was never built, and that is the point.** "No IAM Users" (principle 2) has no answer for an
Identity Center outage or a misapplied SCP, and an absolute rule with no escape hatch is one that gets broken
improvised, under pressure, at the worst moment. D16 settled the escape hatch as the **Management account
root**, which removes the exception instead of documenting one: the root is not an IAM user, it exists
whether or not you want it, there is nothing to create and nothing for Terraform to manage. So Stage 1a step
1 (secure the root) and step 5 (build the break-glass) are two halves of one thing, and what step 5 adds is
not a credential — it is what makes that credential a *break-glass* rather than just an account owner: this
written procedure, an alarm on its use, and one test.

**It is the only recovery path, and that is a decision rather than an omission.** A second, narrower
principal — standing, exempt from every custom `Deny` — was proposed, adopted and then reverted
([D30](../decisions/D30-scp-recovery.md)). The lab keeps no exemption, so this root carries all three
failures in §1 alone, and no principal inside a governed account can work around a bad `Deny`. Two
consequences, both already written into the plan: the chain in §7 must work **before** the first policy is
attached in Stage 1c step 7, and every candidate policy is exercised against the `Policy Canary`
([D29](../decisions/D29-policy-canary.md)) first — with no exemption, catching a bad policy before
attachment is far cheaper than repairing it afterwards.

**Which is also why it is built in Stage 1a and not later.** Every policy Stage 1c attaches is a way to lock
yourself out of your own organization. The escape hatch has to predate the hazard, or it is being built by
someone who already needs it.

**An intention is not a control** (Lesson 5): the alarm needs a *delivery path* that can be named. A
CloudWatch alarm cannot watch an S3 bucket, and the Control Tower organization trail delivers to the Log
Archive account's bucket — so "alarm on root usage" is not a setting, it is the explicit chain in §7: trail
→ CloudWatch Logs group → metric filter → metric → alarm → SNS topic → subscriptions. Each link is a place
it can silently fail, which is why §6 exists.

**The subscription must not be the address that logs in.** Root sign-in *is* e-mail plus password, so
alarming to the login address hands one person the credential and its own warning. Since
[D33](../decisions/D33-control-tower-admin-user.md) that address is disqualified twice over: it is also the
`AWS Control Tower Admin` login, i.e. a *routine* daily login, which would make every alarm ambiguous.
**But be honest about how much that rule buys here.** In an institution the alarm reaches someone who is not
holding the credential. In this lab every address is a `+alias` on one Gmail account and there is one human,
so a distinct address buys **routing and filterability — not separation**: the same mailbox compromise
defeats both. What adds a genuine second factor is a **second channel**, which is why the SMS endpoint in §7
is not optional decoration — it is the only part of the separation that survives the one-inbox problem.

**Two SNS topics already exist and neither is this one.** Control Tower created
`aws-controltower-SecurityNotifications` per Region and `aws-controltower-AggregateSecurityNotifications` in
the Audit account, and subscribed the Audit account's e-mail to the aggregate topic automatically. They are
deliberately noisy — AWS Config notifies on every resource it discovers — and an alarm that arrives in a
stream nobody reads is not an alarm. Note that the Audit account's *root* address being a notification
endpoint has the same shape as the rule above, one account over; Stage 1a step 6 defuses it by removing that
account's root credentials centrally, after which the address is a mailbox rather than a credential.

---

## 1. When using it is justified

Only these three failures. They are the whole list, because they are the only ones no other identity can fix:

1. **IAM Identity Center is unavailable** — the access portal does not authenticate, so no human has a role
   to assume anywhere in the organization.
2. **The organization itself is broken** — Control Tower or Organizations is in a state where the
   `AWS Control Tower Admin` user cannot operate (a failed landing-zone update, a lost delegated
   administrator, an account that must be removed from the organization).
3. **A custom SCP, RCP or tag policy denies something it should not** — including denying the very API that
   would detach it. This is the failure D30's revert made root-only, and the one the `Policy Canary`
   ([D29](../decisions/D29-policy-canary.md)) exists to make rare.

## 2. When it is *not* justified

If any of these is the reason you are reaching for root, stop — the answer is a different identity:

- **Vending an account, creating an OU, enrolling an account, updating the landing zone.** That is the
  `AWS Control Tower Admin` user ([D34](../decisions/D34-account-vending.md)), and root **cannot** do it:
  Account Factory is a Service Catalog product that refuses the root user by design
  ([D33](../decisions/D33-control-tower-admin-user.md)).
- **Applying Terraform, in any account.** That is the infrastructure user
  ([D32](../decisions/D32-account-factory-sso-user.md)).
- **Reading a log, a finding or a bill.** Those are readable from an assumed role.
- **Anything root-shaped in a *member* account** — deleting or restoring its root credentials, unlocking an
  S3 bucket policy or an SQS queue policy that denies everyone. Since Stage 1a step 6 that is a **privileged
  root session** taken from the Management account by `AWS Control Tower Admin`, scoped to one of five task
  policies and capped at 15 minutes. It fires this alarm (§7) and it is *not* this runbook.
- **"It is faster."** It is, and that is exactly the habit this runbook exists to prevent: a credential used
  routinely stops being detectable, because its alarm stops meaning anything.

## 3. Before you sign in

1. **Write down why**, in one sentence, before the login page — you will need it in the log of whichever
   stage is current (`docs/log/log-stage-NN-*.md`) afterwards, and
   the sentence is what distinguishes an emergency from a shortcut. If you cannot write it, see §2.
2. **Have the password and the MFA device in hand.** The password lives **offline** — a password manager or
   paper, never in this repository and never in `secrets/` (D16).
3. **Expect the alarm to fire.** It is not a warning that something is wrong; it is the confirmation that
   the detective control still works. An emergency where the alarm does *not* arrive is a second incident.

## 4. The procedure

1. Sign in at the console as the **Management account root** (e-mail + password + MFA).
2. **Do the one thing, and nothing else.** Typical shapes:
   - **Bad policy:** AWS Organizations → Policies → the SCP/RCP → **Detach** from the OU or account. Detach
     before editing — an edit can fail the same way the attachment did. Command, for the CLI:

     ```bash
     aws organizations detach-policy --policy-id <p-xxxxxxxx> --target-id <ou-or-account-id>
     ```

   - **Identity Center unavailable:** confirm the outage on the AWS Health Dashboard before touching
     anything. An outage is waited out, not repaired from root.
   - **Broken organization:** the specific Control Tower repair, and only it.
3. **Do not create an access key.** `iam:CreateAccessKey` on this root is an invariant, not hygiene: a key
   there is a permanent, unscoped, SCP-immune credential in a file (D16). If you catch yourself wanting one,
   the task belongs to an assumed role.
4. **Do not "tidy up while you are here."** Root can close accounts and change billing. The blast radius of a
   distracted click is the organization.
5. **Sign out**, and close the browser session.

## 5. After

1. **Confirm the alarm arrived**, on both channels (e-mail and SMS). A missing channel is a finding — fix it
   the same day, while the reason is still fresh.
2. **Record it in the current stage's `docs/log/log-stage-NN-*.md`** (the user's file, never written by Claude):
   date, the one-sentence reason, what
   was changed, and whether both alarm channels fired.
3. **Ask what made root necessary, and close that gap.** A bad SCP means the `Policy Canary` battery (D29)
   missed a case — add the case. A repeated cause is a design defect, not an operational one.
4. **Rotate the password** if there is any chance it was observed (screen share, shoulder, a machine you do
   not control).

## 6. Testing it

**An untested alarm is a hypothesis.** Test at build time (Stage 1a step 5) and after any change to the
trail, the log group, the metric filter, the alarm or the subscriptions.

1. Sign in as Management root, do nothing, sign out.
2. Wait — CloudTrail delivery is not instantaneous; allow **up to ~15 minutes** end to end
   (CloudTrail → CloudWatch Logs → metric → alarm → SNS).
3. Expect: the alarm goes to `In alarm`, and a message arrives on **both** subscriptions.
4. **While signed in, check that the root still has no access key** — *Security credentials* → *Access
   keys*, which must be empty. **Added 2026-08-14 by Stage 1d decision 8**, which declined the AWS Config
   rule D16 named (`iam-root-access-key-check`) because Management carries no configuration recorder and
   building one meant five hand-made resources there. This read is what replaces it, and it is deliberately
   hung on this procedure rather than left to memory: the alarm above sees the *act* of creating a key, this
   sees the *state*, and the tester is already signed in as the only principal that can look. It is
   read-only and does not disturb the test — the alarm has already been triggered by the sign-in itself.
   The equivalent from CloudShell as `AWS Control Tower Admin` on Management, if the check is ever wanted
   outside a test, is `aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'`, where
   `0` is the expected answer. **A non-empty list is an incident, not a finding**: that key is permanent,
   unscoped and beyond every SCP in the organization.
5. Update the **Last tested** row at the top of this file.

### 6.1 Attributing an alarm to an event — read this before concluding anything from one

**The notification's arrival time is not the event's time**, and that gap is the whole of it: the metric
filter stamps its datapoint with the CloudTrail `eventTime`, but the alarm can only evaluate once the record
has travelled trail → S3 → CloudWatch Logs, which is minutes. So an alarm that lands *while you are doing
something else* is usually reporting what you did **before** that. Two consequences that decide what you are
looking at:

- **Since Stage 1a step 6, the ordinary cause of this alarm is a privileged root session, not a sign-in.**
  `sts:AssumeRoot` returns credentials that *are* the member account's root, so `DeleteLoginProfile`,
  `DeactivateMFADevice` and friends are logged in **that** account as `userIdentity.type = "Root"` — the
  filter matches, even though the human is signed in as `AWS Control Tower Admin` the whole time. The
  `recipientAccountId` on the matched event names which member account it was. **It is the calls inside the
  session that match, not the opening of it** — the `AssumeRoot` call is logged under *your* identity as
  `AssumedRole` and matches nothing. Which means the read-only `IAMAuditRootUserCredentials` task pages both
  channels exactly like a deletion does: checking whether an account still has root credentials is not a
  free look.
- **A sign-in through the AWS access portal never matches this filter, `AWS Control Tower Admin` included.**
  That user carries the Management root's e-mail address (D33) and is still an Identity Center user: its
  events are logged as `IdentityCenterUser` / `AssumedRole`, never as `Root`. The shared address is an
  inbox-ambiguity problem, not a detection one.
- **The filter matches the whole root session, not the sign-in.** Every API call made while signed in as
  root is a datapoint — and a metric filter evaluates records as they are *ingested*, so calls made before
  the filter existed still count if they arrive after it. Building this chain from a root session therefore
  fires the alarm with the alarm's own creation.

**Two commands settle it**, both from the Management account. Compare the datapoint timestamp in the alarm's
history with the `eventTime` of what actually matched:

```bash
aws cloudwatch describe-alarm-history --alarm-name 'AWS Break Glass Alert' --history-item-type StateUpdate --max-records 10 --region us-west-2
```

```bash
aws logs filter-log-events --log-group-name 'aws-controltower/CloudTrailLogs-gcs-gsx' --filter-pattern '{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent" }' --start-time $(date -v-1d +%s000) --region us-west-2
```

The second runs the *same pattern the filter runs*, so what it returns is exactly what produced the metric —
`eventName`, `eventTime`, `sourceIPAddress` and `recipientAccountId` per event. Note the honest limit
(Lesson 13): an empty result proves only that no root call landed in that window, which is a useful answer
here only because the alarm firing is already known.

## 7. What the alarm is, exactly

The chain **as built on 2026-08-09**, all of it in the **Management account**, home region `us-west-2`:

```
Control Tower organization trail  (aws-controltower-BaselineCloudTrail, multi-region,
                                   global service events included)
        │
        ├── S3 in Log Archive                     ← the immutable copy (Object Lock, Stage 1d step 9)
        │
        └── CloudWatch Logs  aws-controltower/CloudTrailLogs-gcs-gsx   ← created by the landing zone in
                    │            (the -gcs-gsx suffix is this            the MANAGEMENT account
                    │             landing zone's, not a constant)        (landing zone ≥ 3.0)
                    │
            metric filter  awsds-org-root-activity
                    │      { $.userIdentity.type = "Root"
                    │        && $.userIdentity.invokedBy NOT EXISTS
                    │        && $.eventType != "AwsServiceEvent" }
                    │
            metric  AWSDS/Security → RootActivityCount   (no default value — see Cost below)
                    │
            alarm   AWS Break Glass Alert   (Sum ≥ 1 over 1 period, missing data = notBreaching)
                    │
            SNS     awsds-org-break-glass-alerts   (Standard, display name "AWS Break Glass Alert",
                    │                               unencrypted — see Stage 1a step 5.2)
                    ├── e-mail  (the break-glass address — NOT the root address)
                    └── SMS     (the second channel; the only part that survives the one-inbox problem)

  Both endpoints are recorded in the break-glass section of secrets/emails.md, which is
  git-ignored; neither value appears anywhere in this repository.
```

**The alarm and the metric filter do not share a name, and Stage 1a asked for one that they would.** The
plan's step 5.4 named the alarm `awsds-org-root-activity`, matching the filter; it was created as
**`AWS Break Glass Alert`**. Nothing is wrong — an alarm's name is a label — but every command in §6.1 takes
the name literally, so the built name is the one recorded here and the plan's is the stale one. If it is ever
renamed to match, this file and §6.1 change with it.

Four properties of this chain that are load-bearing:

- **It covers the whole organization, not just Management.** The trail is an organization trail, so member
  account events reach the same log group. Root use in *any* account fires this alarm — which matters until
  Stage 1a step 6 (centralized root access management) removes the member roots, and remains a useful
  backstop afterwards.
- **Root sign-in events are recorded in `us-east-1`**, because console sign-in is a global service in
  CloudTrail. They still arrive here: the trail is multi-region with global service events included, and the
  log group is a single destination for all regions. **A single-region trail in `us-west-2` would not have
  caught them** — this is the reason the chain hangs off the Control Tower trail rather than a new one.
- **The filter catches any root API call, not only sign-in.** `ConsoleLogin` is the expected event; anything
  else under a root identity is more interesting, not less.
- **It therefore also catches privileged root sessions, which are routine-ish rather than an emergency.**
  Since Stage 1a step 6 the management account can take a scoped root session into a member account
  (`sts:AssumeRoot`); the actions inside it are logged in that account as `userIdentity.type = "Root"`, so
  they match this filter. **Telling the two apart is a correlation, not a field**: look for an
  `sts.amazonaws.com` / `AssumeRoot` event with `sessionContext.assumedRoot = "true"` and
  `requestParameters.targetPrincipal`, and match its `accessKeyId` to the member-account events. An alarm
  with no such event, and a `ConsoleLogin` on the Management account, is the real thing.
- **The alarm lives in the account it watches.** The Management root can delete it, and so can
  `AWS Control Tower Admin`. That is accepted for this lab, with two compensations: the S3 copy in Log
  Archive is under Object Lock in *compliance* mode (Stage 1d step 9), which nobody can bypass; and the
  detection is a *deterrent plus a record*, not a preventive control. See
  [`docs/plan/institutional-delta.md`](../institutional-delta.md) for the cross-account answer.

**Cost:** one CloudWatch standard alarm, USD 0.10/month in `us-west-2`; SNS e-mail free at this volume; SMS
a few cents per message. The metric is a **custom** metric (USD 0.30/metric-month) but the filter is created
**without a default value**, so it publishes only when root is actually used and a quiet month costs nothing
— which is also why the alarm must treat missing data as `notBreaching` rather than as a breach. Rates in
[`docs/PRICING.md`](../../PRICING.md) §6.

## 8. The recovery path of the recovery path

If the **MFA device is lost**, AWS account recovery is what is left, and it depends on the **phone number**
and **payment method** registered on the Management account. Both must be current — that is part of this
design, not account hygiene (D16). Check them whenever this runbook is tested.

If **only one MFA device is registered**, losing it means that process. Registering a second device on the
root is the cheap way out and is deliberately left as a choice: D16 does not specify the MFA *type*, and
nothing in the plan depends on it.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Decision: [D16](../decisions/D16-break-glass.md)*
