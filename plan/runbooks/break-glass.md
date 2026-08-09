# Runbook — Break-glass (Management account root)

| | |
|---|---|
| **Credential** | The **Management account root user**, and nothing else ([D16](../decisions/D16-break-glass.md)) |
| **Built by** | [Stage 1a](../stages/stage-01a-landing-zone.md) steps 1 and 5 |
| **Detects use** | CloudWatch alarm `awsds-org-root-activity` → SNS `awsds-org-break-glass-alerts` (e-mail + SMS) |
| **Last tested** | *(fill in at each test — see §6)* |

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
attached in Stage 1b step 7, and every candidate policy is exercised against the `Policy Canary`
([D29](../decisions/D29-policy-canary.md)) first — with no exemption, catching a bad policy before
attachment is far cheaper than repairing it afterwards.

**Which is also why it is built in Stage 1a and not later.** Every policy 1b attaches is a way to lock
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
- **"It is faster."** It is, and that is exactly the habit this runbook exists to prevent: a credential used
  routinely stops being detectable, because its alarm stops meaning anything.

## 3. Before you sign in

1. **Write down why**, in one sentence, before the login page — you will need it in `LOG.md` afterwards and
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
2. **Record it in `LOG.md`** (the user's file, never written by Claude): date, the one-sentence reason, what
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
4. Update the **Last tested** row at the top of this file.

## 7. What the alarm is, exactly

The chain, all of it in the **Management account**, home region `us-west-2`:

```
Control Tower organization trail  (aws-controltower-BaselineCloudTrail, multi-region,
                                   global service events included)
        │
        ├── S3 in Log Archive                     ← the immutable copy (Object Lock, Stage 1b step 9)
        │
        └── CloudWatch Logs  aws-controltower/CloudTrailLogs   ← created by the landing zone in the
                    │                                            MANAGEMENT account (landing zone ≥ 3.0)
                    │
            metric filter  awsds-org-root-activity
                    │      { $.userIdentity.type = "Root"
                    │        && $.userIdentity.invokedBy NOT EXISTS
                    │        && $.eventType != "AwsServiceEvent" }
                    │
            metric  AWSDS/Security → RootActivityCount
                    │
            alarm   awsds-org-root-activity   (Sum ≥ 1 over 1 period, missing data = notBreaching)
                    │
            SNS     awsds-org-break-glass-alerts
                    ├── e-mail  (the break-glass address — NOT the root address)
                    └── SMS     (the second channel; the only part that survives the one-inbox problem)

  Both endpoints are recorded in the break-glass section of secrets/emails.md, which is
  git-ignored; neither value appears anywhere in this repository.
```

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
- **The alarm lives in the account it watches.** The Management root can delete it, and so can
  `AWS Control Tower Admin`. That is accepted for this lab, with two compensations: the S3 copy in Log
  Archive is under Object Lock in *compliance* mode (Stage 1b step 9), which nobody can bypass; and the
  detection is a *deterrent plus a record*, not a preventive control. See
  [`plan/institutional-delta.md`](../institutional-delta.md) for the cross-account answer.

**Cost:** one CloudWatch standard alarm, USD 0.10/month in `us-west-2`; SNS e-mail free at this volume; SMS
a few cents per message. The metric is a **custom** metric (USD 0.30/metric-month) but the filter is created
**without a default value**, so it publishes only when root is actually used and a quiet month costs nothing
— which is also why the alarm must treat missing data as `notBreaching` rather than as a breach. Rates in
[`PRICING.md`](../../PRICING.md) §6.

## 8. The recovery path of the recovery path

If the **MFA device is lost**, AWS account recovery is what is left, and it depends on the **phone number**
and **payment method** registered on the Management account. Both must be current — that is part of this
design, not account hygiene (D16). Check them whenever this runbook is tested.

If **only one MFA device is registered**, losing it means that process. Registering a second device on the
root is the cheap way out and is deliberately left as a choice: D16 does not specify the MFA *type*, and
nothing in the plan depends on it.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Decision: [D16](../decisions/D16-break-glass.md)*
