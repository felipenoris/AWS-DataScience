# Stage 1c — Preventive policies: SCP, RCP, tag and declarative

| | |
|---|---|
| **Status** | **DONE — 2026-08-14, 7.0 through 7.8.** Ten documents attached across four policy types, full battery **93 as expected, 0 unexpected, 0 untested**, read-back clean. The one thing that went wrong is worth carrying at the top: **7.8's RCP locked every SSO user out of all six member accounts** by naming `sts:AssumeRoleWithSAML`/`TagSession`, the only actions an `AWSReservedSSO_*` trust policy permits — rescoped to `sts:AssumeRole` + `sts:SetContext` after AWS's `CT.STS.PV.1`, and **no `sts:` action is added to that document without reading that control's exclusion note** (Lesson 24). *What follows is the history of the sittings, kept because the order the work happened in is the reason several things were caught.* **Sitting A done; 7.6 done too** (2026-08-13). Attached and exercised: the two root documents (7.5) and **one per-OU document on each of `Workloads`, `Data`, `Interactive` and `Identity`** (7.6), each parked on `Policy Test` first, then moved and re-probed from that OU's own account. **The three amendments of 7.5a and 7.6a are uploaded and exercised** (2026-08-13): the EC2 launch siblings and the D27 service guard in `Data` and `Identity`, and the GuardDuty vocabulary fix plus the new `DenyImageAndSnapshotExport` in the root baseline — read back from Organizations, then re-probed, the OU pair through phase 4b and the root document through phases 1-3 on the canary. **What is left of the stage is 7.7 and 7.8.** Policy ids are in [`docs/log/log-stage-01c-preventive-policies.md`](../../log/log-stage-01c-preventive-policies.md); what each statement does is in [`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md) |
| **Prerequisites** | **[Stage 1b](stage-01b-identity-and-controls.md) is complete** (closed 2026-08-12; its log is authoritative). What this stage actually consumes from it: the six SSO profiles of step 5 — `awsds-infra-sandbox-1`, `-dev`, `-prod`, `-data`, `-identity` and **`awsds-policy-canary`** — and an administrator principal in the canary account (1b step 3.1). **Not its permission sets**: no policy written here names one, which is why the `Consumes` row carries no persona decision. `Staging` is unvended, so nothing in the `Workloads` tier can be exercised against it |
| **Consumes** | [D6](../decisions/D06-dlp-approach.md), [D10](../decisions/D10-identity-center-delegation.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D28](../decisions/D28-workflow-contract.md), [D29](../decisions/D29-policy-canary.md), [D30](../decisions/D30-scp-recovery.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md), [D37](../decisions/D37-nested-ou-inheritance.md) |
| **Proves** | **Constrains** [INT-12](../integrations.md), whose fallback 7.6 forbids until the policy is amended. **Touches [INT-01](../integrations.md) and [INT-07](../integrations.md)**: the perimeter RCP now covers ECR, so both cross-account image paths run through its service carve-out — admitted by `aws:PrincipalOrgID`, but only exercised in 7.8 |
| **Log** | [`docs/log/log-stage-01c-preventive-policies.md`](../../log/log-stage-01c-preventive-policies.md) — **it exists and carries 7.0**; the policy IDs recorded there as each one is attached are what makes the detach command executable |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**This stage is one step, and it keeps its number: step 7.** The landing zone's second half was one stage
until 2026-08-09; the split gave step 7 a stage of its own because it is the only part of it that is
neither fast nor freely reversible. Every other file's
`Stage 1b step 7` reference is now `Stage 1c step 7` — the same step, a different prefix, and nothing else
moved. Navigate by **7.0-7.8**.

**Two sittings, not one, and the boundary is stated rather than left to stamina** (revised 2026-08-09).
This file used to ask for "an uninterrupted sitting", which is not a thing the work supports: 7.7 alone is
a dozen Control Tower control operations, serialized, minutes each, blocking other landing-zone operations
while they run; the battery of 7.3 is per policy and reads CloudTrail, which lags. So:

| Sitting | Covers | Ends with |
|---|---|---|
| **A — DONE 2026-08-13** | 7.0 (preflight), 7.2 (policy types), 7.3 (the battery, phases 0-3), 7.4 step 1 (account-level BPA everywhere), 7.5 (the organization-root set) | The root set attached and exercised — it is |
| **B** | 7.6 (per-OU sets), 7.7 (the managed controls), 7.8 (RCP, tag, declarative) | The whole ceiling attached |

**What is genuinely uninterruptible is one attachment, not one stage.** The precondition below — Management
console open, detach command written down — is per attach, and it holds identically in both sittings. Do
not start an attachment you do not have time to test.

**Why it comes this early:** prevention has precedence over detection (principle 9), and a guardrail
written after the thing it guards has already been used is a guardrail that arrives late. That is the whole
argument for attaching policy over accounts that are still empty.

## Before you start — the three things this stage may not begin without

Step 7 has no in-account repair. A bad `Deny` is undone from the Management account, which is exempt from
SCPs by AWS's design (D16), and that is the *whole* recovery path since D30 was reverted. So:

1. **The Management console is open, signed in as `AWS Control Tower Admin`, before the first attach** —
   a precondition, not a precaution. If the policy you are about to attach locks you out of the account you
   attached it from, the console you needed is the one you can no longer reach.
2. **The detach command is written down before it is needed**, with the policy ID left blank to fill in:

   ```bash
   aws organizations detach-policy --policy-id <POLICY_ID> --target-id <OU_OR_ACCOUNT_ID>
   ```

   Record the ID of every policy **as you attach it**, in `docs/log/log-stage-01c-preventive-policies.md`. Reading
   an ID back out of a console you have just denied yourself access to is the failure this line exists to
   prevent.
3. **The break-glass chain is live.** Built in 1a and **tested 2026-08-09 on both channels** (e-mail and
   SMS) — that test is what this stage may not start without, and it is already done. It is not a mitigation
   for a bad policy; it is what tells you a root session happened at all.

Also required, and it is the control rather than the backup: **7.3's `Policy Canary` battery runs before
anything reaches a real OU** (D29). The battery is a procedure, not a property — it only works if it is
actually done.

## What changed since this file was last written, and what it changes here

Stage 1b closed on 2026-08-12 and `CLAUDE.md`'s objectives were revised on 2026-08-13. Six things now
enter this stage as **measurement** rather than as assumption — which is the difference between a plan that
can be executed and one that has to be re-derived at the keyboard.

| What 1b or the revision established | What it changes in this stage |
|---|---|
| **Only `SERVICE_CONTROL_POLICY` is `ENABLED` on the root** — measured 2026-08-11, `aws/list-identities.py` §2.2 | 7.2 precondition 1 is confirmed, not assumed. All three other types still have to be enabled, and half of this stage has nowhere to attach until they are |
| **The six SSO profiles all resolve**, and `awsds-policy-canary` is bound to `AWSAdministratorAccess` **permanently** (1b 3.1, 5, 5.1) | The canary has a profile of its own: 7.4's BPA call there is a CLI call like the other five, not a console visit. The battery runs from the laptop |
| **The Organizations *read* surface answers from the Identity account** (1b step 4 and `aws/org-trusted-access-services.py`, 2026-08-12) | 7.0's preflight reads can run under `awsds-infra-identity` without touching Management. **Writes cannot** — every `create-policy`, `attach-policy` and `enable-policy-type` here is CT Admin on Management |
| **A permission set provisioned into Management cannot be altered from Identity** (1b 5.1) | Nothing in this stage alters a permission set — stated so it is not re-discovered. It does mean that if a policy attached here breaks `awsds-policy-canary`, the repair is CT Admin on Management, not the Identity profile |
| **`AWSOrganizationsFullAccess` → `AWSControlTowerAdmins` reaches every vended account** (measured 2026-08-11; `docs/AWS_STATE.md` A.1) | 7.5's `organizations:LeaveOrganization` deny stops being hygiene and becomes the answer to a measured path. Its reach is [`docs/plan/open-questions.md`](../open-questions.md) item 11, and this stage is where it gets answered |
| **`CLAUDE.md` now names six SageMaker Unified Studio features as objectives** (2026-08-13) | 7.6 settles decision 1 **against the verified API surface** rather than against the feature names, and verification (viii) becomes a named list of actions instead of a question. See the box in 7.6 |

One thing that is *not* a change and is listed so it is not read as one: **`EXC-01`** — the `SUSPENDED`
account named `Sandbox` sitting directly on the organization root ([`docs/AWS_STATE.md`](../../AWS_STATE.md)).
It is not this project's, it runs nothing, and **it is not in any list in this stage**: no BPA, no profile,
no attachment. A suspended account cannot be acted on anyway.

## What 7.0 measured on 2026-08-13, and the five places it changes what is left

**The preflight did the thing it was added to do: four of these were assumptions this file stated as
fact.** The evidence is in the log and in the snapshots; what follows is only the consequence for the steps
that have not run. Each row is settled where it lands, not here.

| What was assumed | What was measured | Where it lands |
|---|---|---|
| Control Tower already denies changes to **CloudTrail and Config** on every registered OU | **Config yes, CloudTrail nowhere** — no `cloudtrail:` action appears in any of the six guardrail documents | **7.5**, and the user settled it the same day: **no CloudTrail deny is written**, deliberately |
| `Identity` "carries no policy set until code attaches one", being outside Control Tower's own flow | **False — it carries the standard 8-statement guardrail.** The only OU that differs is `Security`, by three statements about the log-archive and audit buckets | **7.6**: the `Security`/`Identity` diff it asks for is *done* for the SCP half; only the enabled-control half is left |
| All six non-foundational OUs are registered, because each received an Account Factory vend | **`Sandboxes` is the one OU with no guardrail policy at all**, and `Sandbox Account 1` is inside it | **7.7**: whether `CT.MULTISERVICE.PV.1` can be enabled there at all. Verification (xi) |
| 7.0 step 5 measures the policy quota | **Service Quotas publishes no policy quota for `organizations`** — only account counts | **7.1**: the budget is the documentation's number. The count fits regardless, and the documents are now written and sized |
| The Organizations read surface may not reach the *policy* calls | **It does** — every policy read answered from Identity; only `controltower list-enabled-controls` needs Management | **7.0 step 3** is the only part of the preflight still owed, and it is a CloudShell run |

**One thing 7.0 did *not* change, stated because it is the load-bearing one:** account-level BPA is
**unset in all six accounts** that have a profile, exactly as 7.4 assumed. Nothing there is a no-op, and
the interlock with 7.5 is unaffected.

## The stage at a glance

| # | What | Identity | Sitting |
|---|---|---|---|
| 7.0 | **Preflight — measure the ground before writing a line of JSON** — **DONE 2026-08-13**, step 3 included | Infra user (`awsds-infra-identity`) + CT Admin @ Management | A |
| 7.1 | What makes this step different, and the two rules that survive from D30 | — (read first) | both |
| 7.2 | Preconditions, in this order — **DONE** | CT Admin @ Management | A |
| 7.3 | The battery, against `Policy Canary` before anything real (D29) — **phases 0-3 done; it runs again per 7.6 document** | Infra user, laptop (`awsds-policy-canary`) | both — it runs per policy |
| 7.4 | The order of attachment — an instruction, not a listing order — **step 1 DONE in all nine accounts** | CT Admin @ Management; step 1 of 7.4 also in each member account | A |
| 7.5 | The organization-root SCP set — **DONE, both documents attached and exercised** | CT Admin @ Management | A |
| 7.6 | The per-OU sets, one tier per OU policy set (D23) | CT Admin @ Management | B |
| 7.7 | The Control Tower managed controls — use theirs | CT Admin @ Management | B |
| 7.8 | RCPs, tag policies, declarative policies | CT Admin @ Management | B |

## Who executes what

| Part | Identity | Sign-in path |
|---|---|---|
| Policy-type enablement, org-root attachments, per-OU attachments, managed controls (7.2, 7.4-7.8) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 7.4 step 1 — account-level BPA on Log Archive and Audit | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Log Archive** / **Audit**. Both are reachable: `AWSControlTowerAdmins` carries `AWSAdministratorAccess` on each (`docs/AWS_STATE.md` A.1, measured) |
| 7.0's reads, 7.3 (the battery), 7.4 step 1 in the other member accounts | **Infrastructure user**, from the laptop | the five `awsds-infra-*` profiles and `awsds-policy-canary` (1b step 5) |

## What this stage costs

**Nothing.** SCPs, RCPs, tag policies, declarative policies and Control Tower controls are all free. The
one cost this stage *creates* lands elsewhere: 7.8's tag-forcing SCP is paid for at Stage 6, in the time
it takes to make every creation path carry the tags.

---

## To execute

### Step 7 — Preventive policies

The one step in the landing zone that is neither fast nor freely reversible from inside a governed
account. Read all of 7.0 and 7.1 before attaching anything.

#### 7.0 — Preflight: measure the ground, then write

**New in the 2026-08-13 revision, and it is the reason the rest of the step can be executed rather than
interpreted.** Every policy below needs identifiers this plan deliberately does not carry (`CLAUDE.md`
forbids account ids in tracked files), and three of them need to know what Control Tower has *already*
attached. Collect all of it in one pass, into `docs/log/log-stage-01c-preventive-policies.md`, before the first
`create-policy`.

> **RUN 2026-08-13, and it is now two scripts rather than a dozen commands with ids threaded between
> them.** [`aws/org-policy-baseline.py`](../../../aws/INDEX.md) covers steps 1, 2, 3 and 5;
> [`aws/account-bpa.py`](../../../aws/INDEX.md) covers step 4. Both are read-only, both write to
> `aws/output/`, and both are re-run rather than remembered — step 4 in particular is read three times
> (before 7.4, after 7.4 and before 7.5, and at every vend).
>
> **What each numbered step below now says is what AWS answered**, with the command kept so it can be
> re-derived. The one part still owed is **step 3**, which no profile can answer: it is a `controltower`
> call, and a member account is told *"you must create a landing zone first"* — the member-account answer,
> not evidence about the landing zone. Run `python3 aws/org-policy-baseline.py -` in CloudShell on
> **Management** as `AWS Control Tower Admin`.
>
> **Verification (x) is therefore answered: yes.** `ListPoliciesForTarget`, `DescribePolicy`,
> `DescribeOrganization`, `ListRoots` and `ListOrganizationalUnitsForParent` all answer from the Identity
> account, so 7.0 *is* a script — which extends Stage 1b step 4's read boundary once more.

**1. The organization's own coordinates.** Read-only; these answer from Identity (measured 2026-08-12), so
no Management session is needed yet:

```bash
aws organizations describe-organization --profile awsds-infra-identity --query 'Organization.[Id,FeatureSet]' --output text
aws organizations list-roots --profile awsds-infra-identity --query 'Roots[0].[Id,Arn,PolicyTypes]'
aws organizations list-organizational-units-for-parent --parent-id <r-xxxx> --profile awsds-infra-identity --query 'OrganizationalUnits[].[Name,Id]' --output table
aws organizations list-organizational-units-for-parent --parent-id <ou-id-of-Interactive> --profile awsds-infra-identity --query 'OrganizationalUnits[].[Name,Id]' --output table
```

`FeatureSet` must read `ALL` (RCPs require it). The second `list-organizational-units-for-parent` is not
redundant: **the tree is two levels deep** (`Sandboxes` under `Interactive`, INV-03), and the first call
returns only the root's children.

**Write down, in the log: the organization id `o-xxxx`, the root id `r-xxxx`, and the id and full ARN of
every OU** — `Security`, `Interactive`, `Sandboxes`, `Workloads`, `Data`, `Identity`, `Policy Test`. Three
later things need the *path* rather than the id (7.5's `datazone` carve-out) and two need the *ARN* rather
than the id (7.7's control targets), and deriving either at 23:00 is how a policy gets attached to the
wrong node.

**2. What Control Tower has already attached.** This is the measurement that shrinks the work, and the old
version of this file left it as verification (iii) — a thing to notice afterwards rather than a thing to
read first:

```bash
for OU in <ou-id> ...; do
  echo "== $OU"
  aws organizations list-policies-for-target --target-id "$OU" --filter SERVICE_CONTROL_POLICY \
    --profile awsds-infra-identity --query 'Policies[].[Name,Id,AwsManaged]' --output table
done
```

**Measured 2026-08-13, and it is the reading that shrank the work — but not in the direction this file
predicted.** There is one `aws-guardrails-*` policy on every OU **except `Sandboxes`**, plus
`FullAWSAccess` everywhere. Reading the documents (`aws organizations describe-policy --policy-id <p-xxxx>`,
which the script does for you) produced three findings:

- **Config is already denied** — `GRCONFIGENABLED`, carved out for `AWSControlTowerExecution`. **7.5 must
  not write a second one.**
- **CloudTrail is denied nowhere.** No `cloudtrail:` action appears in any of the six documents; this file
  used to assert the opposite. The user settled it the same day as a **deliberate gap** — see 7.5.
- **Also already covered**, and so also not to be duplicated: tampering with `aws-controltower-*` /
  `*AWSControlTower*` / `stacksets-exec-*` roles, the Control Tower log groups, SNS topics, EventBridge
  rules, Lambda functions and S3 buckets. **GuardDuty is not covered by any of them**, which is why its
  four denies stay in the baseline.

The two consequences below are why this is read before writing, and both still hold:

- A hand-written deny that duplicates a Control Tower one costs SCP budget and adds a second place to get
  the carve-outs wrong — and Control Tower's carve-outs (`AWSControlTowerExecution`,
  `aws-controltower-ConfigRecorderRole`) are the ones that keep the landing zone able to update itself.
- If a policy read is denied from the Identity profile, that is information rather than a failure: the read
  surface 1b measured did not include the policy calls. **Re-run it from CloudShell on Management as CT
  Admin** and record which way it went — it is the honest answer to whether 7.0 can ever be a script.
  *(Answered 2026-08-13: none was denied.)*

**And one finding that belongs to 7.7 rather than to 7.5: `Sandboxes` carries no guardrail policy at all.**
Every other OU has one, so the absence is not the listing failing — `FullAWSAccess` is there, and the
failure section was empty. Two readings, and they are not equivalent: the nested OU is **not registered**
with Control Tower, or Control Tower **relies on inheritance** from `Interactive` and attaches nothing to
children. The discriminating evidence is step 3, which needs Management. It matters because a managed
control cannot be enabled on an unregistered target, and 7.7's order names `Sandboxes` explicitly.

**3. What each OU's control baseline already is**, from Management as CT Admin — and the same command is
7.7's registration check, which is why it is collected once:

```bash
aws controltower list-enabled-controls --target-identifier <ou-arn> --query 'enabledControls[].[controlIdentifier,statusSummary.status]' --output table
```

**An unregistered target errors rather than returning an empty list**, and that distinction is the check
(Lesson 13). Registration was *expected* for all six non-foundational OUs — every one of them received an
Account Factory vend (1a log) and Account Factory only offers registered OUs — **and step 2 has already
made `Sandboxes` the exception worth going in expecting**: it is the one OU with no guardrail policy.
Record the result per OU; 7.7 may not enable a control on an OU this call rejected.

**This is the one step of 7.0 still owed, and it cannot be answered from a profile.** Under
`awsds-infra-identity` all seven targets returned `ResourceNotFoundException — you must create a landing
zone first`, which is what a *member* account is told; the API only answers in Management. So:

```bash
python3 aws/org-policy-baseline.py -
```

in CloudShell on **Management** as `AWS Control Tower Admin` (bring the whole `aws/` folder — the script
imports `awslib`, so a single-file upload does not run; clone the repository, or upload it zipped and
unzip, per [`aws/INDEX.md`](../../../aws/INDEX.md); with `-` it uses ambient credentials and writes the
report under `aws/output/`). It answers three things
at once: whether `Sandboxes` is a registered target, the enabled-control diff between `Security` and
`Identity` that 7.6 asks for, and the baseline 7.7 is going to add to.

**4. The account-level Block Public Access state, before changing it.** 7.4 assumes it is off everywhere;
that assumption has never been measured, and if Control Tower or the Account Factory blueprint already
sets it, half of 7.4 step 1 is a no-op and decision 7 gets easier rather than harder:

```bash
for P in awsds-infra-sandbox-1 awsds-infra-dev awsds-infra-prod awsds-infra-data awsds-infra-identity awsds-policy-canary; do
  ACCT=$(aws sts get-caller-identity --profile "$P" --query Account --output text)
  printf '%-24s ' "$P"
  aws s3control get-public-access-block --account-id "$ACCT" --profile "$P" \
    --query 'PublicAccessBlockConfiguration' --output json 2>&1 | tr -d '\n '
  echo
done
```

`NoSuchPublicAccessBlockConfiguration` is the "not set" answer and is what to expect. **Management, Log
Archive and Audit have no profile** — run the same call for them from CloudShell as CT Admin, with
`--account-id` set to that account's own id.

**Measured 2026-08-13: all six accounts with a profile are `NOT SET`**, `awsds-policy-canary` included. So
7.4 step 1 has real work in every one of them, nothing is a no-op, and decision 7 got neither easier nor
harder. `./aws/account-bpa.py` is the loop above with the failure modes separated — a `(failed)` profile is
never counted as compliant, and `NoSuchPublicAccessBlockConfiguration` is reported as `NOT SET` rather than
as an error. **The three accounts with no profile are still unread**; the same script with `-` answers each
one from its own CloudShell.

**5. The quota that decides whether the set fits.** The policy count per node is the constraint 7.1
describes, and it is worth reading rather than remembering — Organizations quotas answer in `us-east-1`:

```bash
aws service-quotas list-service-quotas --service-code organizations --region us-east-1 \
  --query 'Quotas[?contains(QuotaName, `policies`)].[QuotaName,Value]' --output table
```

**Measured 2026-08-13, and the measurement is that there is nothing to measure: Service Quotas publishes no
policy quota for `organizations` at all** — only `Maximum number of accounts` and the billing-transfer
quotas, every one of them returning `0.0`. **The numbers themselves are not unknown**, they are just not
readable from the API: AWS's May 2026 announcement ([`docs/REFERENCES.md`](../../REFERENCES.md)) puts SCPs at
**10 per node and 10 240 characters per policy**, with **RCPs unchanged at 5 and 5 120**. Record in the log
which number was used and where it came from — this is the one place in the stage where Lesson 6's
"measured, not reasoned" cannot be honoured, and saying so is better than implying a reading.

**It does not bind, under either the old caps or the new ones, and the count is now exact rather than
prospective.** The **root** carries `FullAWSAccess` + baseline + perimeter + the tag-forcing SCP = 4;
**each OU** carries `FullAWSAccess` + its Control Tower guardrail + its tier + the Region control 7.7
attaches = 4. The two written documents are **1279** and **716** characters minified. Even against the
pre-increase 5-per-node/5 120 limits there is room. **Count again if a fifth document is ever proposed for
a node, and remember the RCP budget is the tighter one** — 7.8 puts seven services in one document.

#### 7.1 — What makes this step different, and the two rules that survive from D30

- **No `Deny` written below carries a blanket exemption for any principal (D30, reverted).** A standing
  role exempt from every custom deny was proposed and removed; the only carve-outs in this design are
  per-function and per-statement — the catalog-maintenance role against the `Data` OU's Glue deny (D27),
  the `datazone:*` control plane (D26), the account-level BPA carve-out settled as decision 7 (7.4), and a
  deploy role against a specific deny where automation would otherwise stall.
- **The practical consequence, and it is why 7.3's battery is not optional: a policy attached here has no
  in-account repair.** A mistake is undone by detaching the policy from the Management account, which is
  exempt from SCPs by design (D16) — so the battery *is* the control, and having the Management console
  already open is a precondition rather than a precaution.
- **A condition that has to appear in several policies is generated, not typed** — which is why these
  policies live in `terraform-live/identity/org-policies/` from Stage 2 rather than in the console
  (Lesson 14).
- **Write each document as a file *before* pasting it, and keep the file.** The folder exists since
  2026-08-13: [`terraform-live/identity/org-policies/`](../../../terraform-live/identity/org-policies/README.md),
  with `policies/` for the real documents and `canary/` for the throwaway ones. Record the returned policy
  ID beside the filename in `docs/log/log-stage-01c-preventive-policies.md`. Two things come free: the detach command
  above becomes executable (you have the ID), and **Stage 2 step 5.5's import compares a document against
  itself** instead of against a re-typing, which is the difference between an empty plan and an evening
  spent on JSON whitespace.
  **And every statement gets a row in [`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md), in
  the same sitting** — what it denies, why it exists, what it does once attached. JSON carries no comments,
  so a `Sid` whose reasoning lives only in the sitting that wrote it is one the next reader deletes or works
  around. That file also holds the AWS reference for every action named, which is what makes a review of an
  amendment a reading rather than a search.
  **The tracked files carry placeholders, and the paste comes from the rendered copy.** `<ORG_ID>` and the
  `Data` OU path appear in four documents between 7.5 and 7.8, and a value typed four times is eventually
  wrong in one of them, in the silent direction (Lesson 14) — so `render.py` fills them from the API into
  untracked `aws/output/rendered-policies/`, refuses to leave a placeholder unsubstituted, and prints each
  document's size against the limit. It is also the shape Stage 2 needs, where the id comes from
  `data.aws_organizations_organization` rather than from a literal.
- **Any ARN condition uses an enumerated list, never a wildcard account** — `arn:aws:iam::*:role/x` means
  "anyone who can create a role named `x`, anywhere". **One exception is adopted here, deliberately and
  once:** the BPA carve-out of 7.4/7.5, whose whole purpose is to reach accounts that do not exist yet and
  whose Identity Center role suffix is therefore unknowable. It is argued where it is used, not here, and
  `docs/plan/conventions.md` carries the rule it bends.
- **There is a size budget, and it cannot be read from the API — only from AWS's documentation.**
  **10 SCPs per node and 10 240 characters** since the May 2026 increase, **RCPs still 5 and 5 120**
  ([`docs/REFERENCES.md`](../../REFERENCES.md)); 7.0 step 5 went looking for those numbers in Service Quotas and
  found that it publishes **none** of them for `organizations`. Control Tower's guardrails consume part of
  the SCP allowance at every OU, **and 7.7 consumes one more slot per OU**. The root is asked to carry three
  documents (7.5's two plus 7.8's tag-forcing SCP) and 7.8's RCP covers **seven** services in one document.
  **It fits with room under the *old* caps too: 4 policies on the root and 4 on each OU**, the two written
  documents being 1279 and 716 characters. **Prefer one well-`Sid`-ed policy per node to several thin
  ones**, and watch the RCP side rather than the SCP side — that is the tighter budget now.
- **A third rule arrives with D34, and it is the one that survives an account being added later.** OUs
  and accounts are created from the console, outside every Terraform state — which cannot cause drift,
  because nothing here declares them, but *can* leave a new OU with no policy attached and a new account
  outside every enumerated condition, with `terraform plan` reporting "No changes" either way. So when
  these policies move into `terraform-live/identity/org-policies/` at Stage 2: **the floor is discovered
  and the grants are enumerated** — attachments and org-wide sets driven by `for_each` over the
  Organizations data sources, permission set assignments written out one by one.

#### 7.2 — Preconditions, in this order. Two of them are the reason a first attempt fails

1. **Enable the policy types that are not already on.** Control Tower enables `SERVICE_CONTROL_POLICY`;
   **`RESOURCE_CONTROL_POLICY`, `TAG_POLICY` and `DECLARATIVE_POLICY_EC2` are not enabled** — measured
   2026-08-11, not assumed — and cannot be attached until they are. RCPs additionally require an
   organization with **all features** enabled, which 7.0 step 1 confirms. **Run as CT Admin on Management**;
   the Identity account can read this state but not change it:

   ```bash
   aws organizations enable-policy-type --root-id <r-xxxx> --policy-type RESOURCE_CONTROL_POLICY
   aws organizations enable-policy-type --root-id <r-xxxx> --policy-type TAG_POLICY
   aws organizations enable-policy-type --root-id <r-xxxx> --policy-type DECLARATIVE_POLICY_EC2
   ```

   Re-run `list-roots` afterwards: each type must read `ENABLED`, not `PENDING_ENABLE`.
2. **Confirm the `Policy Canary` account is reachable** under `awsds-policy-canary` and holds an
   administrator (1b step 3.1 — the direct `AWSAdministratorAccess` assignment, which 1b step 5.1 left in
   place permanently because there is no group and no `awsds-infra-*` profile behind it):

   ```bash
   aws sts get-caller-identity --profile awsds-policy-canary
   ```

   It must return `AWSReservedSSO_AWSAdministratorAccess_*`. An expired session here, discovered mid-battery,
   is an hour of confusion attributed to the policy.
3. **Write the detach command down, and reach the Management console *now*, not in theory.** This is the
   whole recovery path, not a backup to one.
4. **Enable account-level S3 Block Public Access before the SCP that denies changing it** — see 7.4,
   where the ordering is stated as an instruction rather than implied.

#### 7.3 — The battery, run against `Policy Canary` before anything reaches a real OU (D29)

> **The executable form is [`docs/plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md)** — every probe with
> its exact command and, for each one, *the two outcomes that are distinguishable*. It lives in `runbooks/`
> rather than here because it is re-run whenever a policy is amended, and Stage 6 and Stage 9 both come back
> to the perimeter document. **What stays below is why each rule is a rule**; the runbook does not repeat it.

An SCP mistake is the fastest way to lock yourself out of your own organization — recoverable, because the
Management account is exempt from SCPs and 1a step 5's break-glass path exists, but recoverable is not
the same as cheap. Since D30 was reverted this is the only thing standing between a mistake and that
recovery. It is a procedure, not a gesture:

- **One policy at a time.** Attach, test, record, move on. A batch that breaks tells you that something
  in the batch is wrong, which is the least useful form of that information.
- **From an administrator principal.** An SCP is a ceiling; a deny exercised by a principal that lacked
  the permission anyway proves nothing. That is what the canary's administrator assignment is for.
- **Test in both directions, because the two failure modes are opposites.**
  - *Too tight* — the calls that must still **succeed**: `sts:GetCallerIdentity`,
    `s3:ListAllMyBuckets` (`aws s3 ls` — **not** `s3:ListBucket`, which is a different action about the
    objects *inside* one bucket, and naming the wrong one is how a battery produces a false pass),
    `ec2:DescribeVpcs` in `us-west-2`, and — once the region restriction is on — `iam:ListRoles`,
    `budgets:DescribeBudgets` and `ce:GetCostAndUsage`, all of which answer in `us-east-1` and must keep
    working.
  - *Too loose* — the calls that must now **fail**: an `iam:CreateUser`, and the trusted-resources deny
    exercised **by its complement** rather than against a bucket outside the organization (below).
  - **The region test belongs to 7.7, not to this battery, and the sequencing matters.** The
    discriminating check is `ec2:RunInstances --dry-run` in **`us-east-1` specifically** — under the
    correct construction `us-east-1` is *not* an allowed region and the call must fail, while under the
    loose construction this plan used to describe (adding `us-east-1` to the allowed list) it would
    succeed and look like a pass. But no policy written in 7.5 or 7.6 implements the region restriction:
    it comes from a **Control Tower managed control**, enabled in 7.7. So run this pair —
    `us-east-1` must return `UnauthorizedOperation`, `us-west-2` must return `DryRunOperation` — from
    `awsds-policy-canary` **after** 7.7, as the check that the managed control took effect.
- **Use `--dry-run` for the "must fail" half wherever the API supports it, because a passing test that is
  not dry-run is a resource you now own.** `ec2:RunInstances --dry-run` returns `DryRunOperation` when
  the call *would* have been allowed and `UnauthorizedOperation` when it is denied — two distinguishable
  outcomes and no instance, in an account whose whole point is to stay empty. Where there is no dry-run
  (`iam:CreateUser`), plan the cleanup before the call, not after it.
- **Read the denial, do not just observe it (Lesson 13).** `AccessDenied` from an SCP and `AccessDenied`
  from a missing grant or someone else's bucket policy look identical at the CLI. The discriminating
  evidence is the wording *"with an explicit deny in a service control policy"* — in the API's own error
  response, and in the CloudTrail `errorMessage` **for calls CloudTrail records**, which is not all of
  them (see the next bullet).
- **The trusted-resources deny is tested by its complement, because the obvious test cannot be run and its
  evidence would not exist** (corrected 2026-08-09). The old instruction was to attempt a `PutObject` to a
  bucket outside the organization and read the CloudTrail record. Two independent problems:
  - **There is no bucket outside the organization to write to.** Every account this project can reach is
    inside it, and a public AWS-owned bucket refuses the write on its own — which is the false pass 7.3
    exists to avoid.
  - **`s3:PutObject` is a CloudTrail *data* event.** The Control Tower trail records management events
    only, and data events for a bucket you do not own cannot be added to your trail by anyone. The record
    the old deliverable asked for would never have appeared, in success or in failure — the exact shape
    Lesson 13 warns about, in the verification rather than in the control.

  **So exercise the condition, which is the part that can actually be wrong.** Attach to `Policy Test` a
  throwaway SCP that is the real 7.5 statement with its condition **inverted** — deny the same S3 writes
  when `aws:ResourceOrgID` **equals** this organization, keeping `StringEqualsIfExists` beside
  `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}`. **That document is written and rendered:**
  `terraform-live/identity/org-policies/canary/awsds-canary-scp-perimeter-inverted.json`, whose only
  difference from the real one is the direction of one comparison — which is what makes the review of it a
  one-character review rather than a re-reading. Then attempt a write to a bucket you *do*
  own from `awsds-policy-canary`. It must fail, and the error must name an explicit deny in a service
  control policy. That proves the three things worth proving: the key populates, the `IfExists` pair
  evaluates the way it reads, and the deny reaches an ordinary principal. Detach it, then attach the real
  statement — whose only difference is the direction of the comparison. Record both outcomes.
  **The bucket to write to is a throwaway created in the canary itself, and deleted in the same sitting.**
  That is the one exception to "nothing is ever created in `Policy Canary`" (`docs/plan/conventions.md`), and it
  is the same exception the battery already makes for `iam:CreateUser`: plan the cleanup before the call,
  not after it. Do the *"must still succeed"* half against the same bucket while it exists — a write that
  works before the throwaway SCP is attached and fails after it is a controlled comparison, which is more
  than the original test would ever have produced.
  **What this does not prove**, stated so nobody reads more into it: that a write to a genuinely external
  bucket is denied. That claim rests on the policy being the complement of the one that was tested, which
  is a one-character review, and it is the honest limit of a lab with a single organization.

  **Run the same complement against ECR, because key population is per-service and the S3 run says nothing
  about it** (added 2026-08-12 with the ECR half of the 7.5 statement). What the bucket run proves is that
  the `IfExists` pair evaluates as written and that the deny reaches an ordinary principal — both
  service-independent. What it does **not** prove is that `aws:ResourceOrgID` populates on an **ECR**
  request, which is a property of that service's authorization, not of the policy. The probe is cheap and
  needs no image and no Docker: create a throwaway repository in `Policy Canary`, attach the inverted
  statement (deny these four actions when `aws:ResourceOrgID` **equals** this organization), and run
  **`aws ecr initiate-layer-upload --repository-name <throwaway>`**. It is one API call, it uploads nothing,
  and its two outcomes are distinguishable: an upload id means the key did not populate and the deny is not
  reaching ECR at all, an `AccessDenied` naming an explicit deny in a service control policy means it did.
  Delete the repository in the same sitting, under the same planned-cleanup rule as the bucket.
- **Test every condition that names a principal in both directions, and one of them has a trap worth
  naming.** For D27's catalog-maintenance role, D26's `datazone:*` control plane and **the BPA carve-out**:
  confirm the exempt principal *can* do the thing, and that a principal outside the carve-out *cannot*. A
  carve-out that silently fails to match is either a control you do not have or a job that will not run,
  and neither announces itself. **The trap:** `aws:PrincipalArn` for an assumed role resolves to the
  **IAM role ARN** (`arn:aws:iam::<acct>:role/aws-reserved/sso.amazonaws.com/<region>/AWSReservedSSO_...`),
  **not** to the `arn:aws:sts::<acct>:assumed-role/...` form that `sts:GetCallerIdentity` prints and that
  1b's log is full of. A condition written from the log's output matches nothing and fails *open* on a
  deny's carve-out — the direction that is silent. Prove it by exercising the carve-out, not by reading it.
- **Then move the attachment to its real target** — the OU named in 7.4/7.5, or the organization root for
  the org-wide set. The root-level policies can be exercised here exactly as they will behave in
  production, because `Policy Test` sits under the root and inherits from it like every other OU.
  **And that is also the canary's one permanent limitation, worth knowing before you rely on it a second
  time:** once the root set is attached, `Policy Canary` inherits it forever, so every later candidate is
  tested *on top of* the existing ceiling rather than in isolation. That is the right thing for
  regression — it is the real evaluation order — and the wrong thing for answering "does *this policy*
  deny X", because denies only ever compose: a call that fails may be failing on the root set. The half
  that stays clean is the *must still succeed* half, which composition can only make stricter — so a
  success there is still evidence about the candidate. For the deny half, read the CloudTrail
  `errorMessage`, which names the policy id.
- **Record each outcome.** A policy that passed both halves is a control; one that was only attached is a
  hope.
- **Two verifications ride along** (`docs/plan/open-questions.md` item 10): whether the **IAM Policy
  Simulator** evaluates SCPs for member-account principals — if it does, it is a cheaper first pass than
  any OU — and whether the OU has to be **registered with Control Tower** for the test to run against the
  real control baseline. The second is now answered by 7.0 step 3 rather than left to the battery.
- **Verification (iii) moved to 7.0 step 2**, where it belongs: whether the hand-written SCPs and RCPs
  conflict with the ones Control Tower manages is a thing to read *before* writing, not a surprise to
  notice after attaching. What stays here is the residue — a candidate whose deny composes badly with a
  Control Tower guardrail shows up as a `must still succeed` failure in the battery.

#### 7.4 — The order of attachment. This is an instruction, not a listing order

Two pairs interlock, and following the old "attach to the OUs, in this order" literally breaks one of them.

1. **Account-level S3 Block Public Access in every account, enumerated rather than implied.** The
   module-level block from Stage 2 only covers buckets the module creates; the account-level setting is
   the blanket that also covers the bucket someone creates outside it — so "every member account" has to
   be a list, or the one account nobody had a profile for is the one that keeps the hole. **Measured
   2026-08-13 (7.0 step 4): every one of the six accounts with a profile is `NOT SET`**, so none of this is
   a no-op and the list below is the work rather than a checklist to tick. The three without a profile are
   still unread. **Re-run `./aws/account-bpa.py` after setting them** — every row must read `ALL FOUR true`
   *before* 7.5 attaches the deny:
   - `AWS Control Tower Admin`, from the console or CloudShell: **Management**, **Log Archive**, **Audit**.
   - `awsds-infra-sandbox-1`, `-dev`, `-prod`, `-data`, `-identity` (`aws s3control put-public-access-block`).
   - **`awsds-policy-canary`** — the easiest one to forget, because the account is supposed to stay empty.
     It has a profile of its own since 1b step 5, so it is one more line in the same loop; it is still an
     account with an S3 API.
   - **`Staging` gets it at the vend**, with everything else deferred there ([Stage 1a](stage-01a-landing-zone.md),
     "What the deferral leaves owed").
   - **Not `EXC-01`** — the suspended `Sandbox` at the root is not ours and cannot be acted on.
   - **Management is on the list even though the deny below never reaches it** (SCPs do not apply to the
     management account, D16). The ordering interlock in step 2 is therefore about the *members*; doing
     Management first is simply doing it in the same sitting.

   ```bash
   aws s3control put-public-access-block --account-id <ACCT> --profile <PROFILE> \
     --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
   ```

   **The interlock is not a one-off, and treating it as one leaves every future account without the
   setting** (found 2026-08-09). Written as "do this, then attach the deny", it reads like a problem that
   ends when the deny is attached. It does not: D34 keeps vending as a standing capability and D35 says
   `Sandbox` multiplies, so **an account vended next year inherits the root deny the moment it lands in a
   governed OU — and from then on no principal inside it could call `s3:PutAccountPublicAccessBlock` at
   all.** There is no cross-account API for the account-level setting, so there would be no way to fix it
   from outside either.

   > **Decision 7 — settled by the user, 2026-08-13: the deny carries an enumerated carve-out.**
   > The alternative was to accept that every future account is permanently without account-level BPA, with
   > the residual exposure being a bucket created *outside* Stage 2's `s3-bucket` module in a *future*
   > account. The carve-out was chosen because a gap that can only be closed at vend time, in an account
   > nobody has stood up yet, is the kind that is discovered by an S3 finding rather than by a review.
   >
   > **What the carve-out costs, stated rather than buried: it is the one wildcard-account ARN in this
   > design.** The exempt principal is the Identity Center role behind `InfrastructureAccess`, whose ARN
   > carries a **per-account random suffix** — the five measured in 1b step 5 are all different — so the
   > accounts that matter most (the ones that do not exist yet) cannot be enumerated even in principle. The
   > residual risk this admits is bounded and worth writing down: a principal that can *create an IAM role*
   > in a governed account could mint a role matching the pattern and turn BPA off there. That principal is
   > an administrator of that account already, which is to say it is `InfrastructureAccess` — the very
   > identity the carve-out names. The exception is therefore self-consistent rather than a hole, and
   > `docs/plan/conventions.md`'s enumerated-ARN rule gains one named exception instead of quietly acquiring a
   > habit. **Stage 2 step 9.2's wildcard check must whitelist this one `Sid` by name**, or the check fails
   > on the policy it was written to protect.
   >
   > **And [Stage 14](stage-14-sandbox-vending.md) still gains a step**: a unit vended without BPA being set
   > is a unit that silently differs from the others, carve-out or no carve-out. The carve-out makes that
   > step *possible*; it does not make it automatic.

2. **Then** the organization-root SCP set (7.5), which includes the deny on
   `s3:PutAccountPublicAccessBlock`. **In the other order the deny blocks the very call that enables the
   setting it protects**, in every account at once, and the repair is a detach from Management.
3. **Then** the per-OU sets: `Workloads`, `Data`, `Identity`, and `Interactive`.
4. **Then** the managed Control Tower controls (7.7) — region deny and the two root-user controls.
5. **Then** RCPs, tag policies and declarative policies (7.8).

The same interlock appears once more inside 7.7: the region-deny exemption list has to contain
`s3:PutAccountPublicAccessBlock` and `s3:ListAllMyBuckets`, which are account-level calls evaluated
outside any region.

#### 7.5 — The organization-root SCP set

(hand-written; moves to `terraform-live/identity/org-policies/` at Stage 2).

**The set is two documents, not one, and the split is not cosmetic.** The perimeter statement is the one
most likely to need amending — it is the one with two `IfExists` traps in it, and the one Stage 6 and
Stage 9 will come back to — so it is detached and re-attached on its own rather than inside the document
that also holds `iam:CreateUser`. Both attach to the **organization root**; the root carries no Control
Tower guardrails (those go to registered OUs), so the budget there is spent only by this project.

| File in `policies/` | Attaches to | Carries |
|---|---|---|
| `awsds-org-scp-baseline.json` | organization root | `LeaveOrganization`, IAM-user denies, the BPA deny with its carve-out, the snapshot/AMI sharing deny, the `ecr-public:*` deny, `datazone:CreateDomain` with the `Data` carve-out, and the GuardDuty denies — **seven statements, 1279 characters.** No Config statement (Control Tower has it) and **no CloudTrail statement** (measured gap, kept open by decision) |
| `awsds-org-scp-perimeter.json` | organization root | the `aws:ResourceOrgID` write deny — **S3 and ECR**, alone. Two statements, 716 characters |
| `awsds-org-scp-require-tags.json` | organization root | 7.8's tag-forcing SCP — **not written yet**, because its scope is decision 5 and that is settled while executing |

**The first two exist as of 2026-08-13** — written before anything was attached, which is the order 7.1
asks for. They carry placeholders; `render.py` produces the pasteable copy. The
[folder's README](../../../terraform-live/identity/org-policies/README.md) carries what each document may not
become.

- **Deny `organizations:LeaveOrganization` — not hygiene: a real principal can call it, and it is now
  measured rather than reasoned.** Every vended account carries `AWSOrganizationsFullAccess` →
  `AWSControlTowerAdmins` (`docs/AWS_STATE.md` A.1, measured 2026-08-11), a group whose one member is the
  Control Tower admin user. This is one of the few Organizations calls a *member* account can make, and one
  call drops every SCP and every Control Tower control for that account.
  **While you are here, answer [`docs/plan/open-questions.md`](../open-questions.md) item 11**, which has been
  waiting for exactly this session: assume that permission set in one vended account and run the
  Organizations reads plus one harmless write. Whether anything *else* in that managed policy needs denying
  is the open half, and it costs minutes now versus a re-derivation later.
- **CloudTrail, Config and GuardDuty: the gap is measured, and it is not the gap this file predicted**
  (7.0 step 2, 2026-08-13). Three different answers, and writing them as one line is how the wrong one
  gets written:
  - **Config — already denied, do not write it again.** `GRCONFIGENABLED` is in every OU's guardrail,
    covering the recorder, the delivery channel and the retention configuration, carved out for
    `AWSControlTowerExecution`. A second copy costs SCP budget and adds a second place to get that
    carve-out wrong.
  - **GuardDuty — not covered by anything**, exactly as predicted, so `guardduty:DeleteDetector`,
    `guardduty:DisassociateFromMasterAccount`, `guardduty:UpdateDetector` and `guardduty:DeleteMembers`
    belong in `awsds-org-scp-baseline`. They are inert until GuardDuty is turned on — Stage 4 when this was
    written, Stage 15 since the 2026-08-18 split — and dormancy is deliberate rather than an oversight.
  - **CloudTrail — denied nowhere, and deliberately left that way** (user, 2026-08-13). This file used to
    assert that Control Tower's mandatory controls covered it; **no `cloudtrail:` action appears in any of
    the six guardrail documents.** The deny was still not written, and the reason is the one that makes it
    a choice rather than an omission: the trail is **organization-level and lives in the Management
    account**, which is exempt from SCPs by AWS's design (D16), so a member-account deny would protect
    nothing that is reachable. What *is* protected, and by Control Tower rather than by us, is the
    destination — `logs:DeleteLogGroup` and `logs:PutRetentionPolicy` on `*aws-controltower*` log groups,
    and the log-archive buckets under the `Security` OU's three extra statements. **Revision trigger:** the
    first trail this project creates in a member account — Stage 11's data events are the candidate — at
    which point the deny has something to bind and is written with that reason recorded.
  *(Considered and deliberately not adopted: a deny on `access-analyzer:DeleteAnalyzer`, protecting the
  organization analyzer 1b step 8.2 created in Audit. The analyzer is re-creatable in one call and its
  deletion is a management event the trail records; the deny would bind the Audit administrator, which is
  the identity that would legitimately re-create it. Recorded so it reads as a choice.)*
- **Deny writes to S3 and ECR resources outside this organization** (`aws:ResourceOrgID`) — the
  trusted-resources axis of `docs/plan/architecture.md` §4.2, and the most direct exfiltration route a notebook
  has. **Writes only, deliberately:** a read-side deny of the same shape breaks `docker pull`, package
  installs and every other legitimate read of an AWS-owned bucket.
  **ECR was added on 2026-08-12 (user), and the second amendment to this statement is what the two-document
  split in the table above was for** — this is the file that gets detached and re-attached on its own.
  Four precisions, and the first one is the difference between a control and a gesture:
  - **`ecr:PutImage` alone does not close the route — it only makes the push fail at the end.** A
    `docker push` is `InitiateLayerUpload` → `UploadLayerPart` → `CompleteLayerUpload` → `PutImage`, and
    **the layers are the data**: by the time `PutImage` is denied, the filesystem contents have already
    been written into the outside repository and only the manifest is missing. So the statement names
    **`ecr:PutImage`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart` and `ecr:CompleteLayerUpload`**. A
    deny on the manifest write alone is a completeness control that reads like an exfiltration control,
    which is the worse of the two failure modes.
  - **`ecr:GetAuthorizationToken` is deliberately not in the list, and the reason generalizes into a rule
    the whole document is written under** (added to `docs/plan/conventions.md`, 2026-08-13). It is
    registry-scoped and carries no resource, so `aws:ResourceOrgID` never populates for it — **and a
    negated or `IfExists` condition evaluates *true* when the key is absent**, which means an action with
    no resource is not missed by this deny, it is **caught unconditionally**. So the action lists here are
    enumerated to actions that populate the key, and **an action wildcard is forbidden**: `s3:Put*` would
    reach the account-level `s3:PutAccountPublicAccessBlock` and deny, in every account and for every
    principal, the exact call 7.4 depends on — with decision 7's carve-out unable to help, because it lives
    in a different statement in a different document. This is the one trap in 1c that fails *closed* over
    something legitimate rather than open, and it is invisible until somebody vends an account.
    Authenticating against an outside registry is harmless on its own; the write is the event, and the
    write is covered.
  - **No carve-out, and the pull-through cache objection was checked rather than assumed.** This plan
    flagged pull-through cache as the likely casualty — **it is not one.** A cache rule writes the fetched
    image **into your own registry**, so `aws:ResourceOrgID` equals this organization and the deny never
    evaluates against it; the upstream fetch is HTTPS to Docker Hub or ECR Public and is not an AWS API
    call against an AWS resource at all. The same holds for INT-01's replication, whose destinations are
    in-org and which ECR performs itself under the `PrincipalIsAWSService` carve-out. **Nothing in this
    design pushes an image to a registry outside the organization**, so the deny binds the pipeline and the
    infrastructure user exactly as hard as it binds a notebook (Lesson 18).
  - **`ecr-public` is a different namespace and is deliberately not covered by *this* statement** — it has
    its own deny in the baseline document, below. Pushing to an ECR **Public** repository is `ecr-public:*`
    against a repo *you own*, so `aws:ResourceOrgID` matches this organization and a trusted-resources
    condition correctly does not fire. Publication is a different threat from cross-organization transfer
    and gets a different statement, rather than a condition bolted onto this one.
  **Write the condition the way 7.8 writes the RCP's, because it is the same trap and this plan only
  spelled it out on one of the two sides:**
  `"StringNotEqualsIfExists": {"aws:ResourceOrgID": "<o-xxxx>"}` beside
  `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}`. A plain `StringNotEquals` evaluates **true
  when the key is absent**, so every call that does not populate `aws:ResourceOrgID` is denied — and the
  `BoolIfExists` pair is what stops the deny reaching calls an AWS service makes on your behalf. Both
  halves are invisible in the JSON review and obvious in the canary, which is what 7.3 is for.
- **Deny sharing snapshots and AMIs outside the organization** (added 2026-08-12, out of D6 and the D19
  revision). **This is the one exfiltration route that bypasses every other control in this design.** A
  Studio space's EBS volume holds whatever the user pulled down; `ec2:CreateSnapshot` followed by
  `ec2:ModifySnapshotAttribute` hands that whole volume to an account outside the organization in **two API
  calls with no network path**. NAT, the DNS Firewall, the VPC endpoint policies, D5's egress design and the
  `aws:ResourceOrgID` write deny immediately above are all irrelevant to it, because **none of them is in
  that route**. And no RCP reaches it either: the RCP service list does not include EC2 or RDS
  (`docs/plan/architecture.md` §4.2), which is exactly why this is an SCP, here, and not part of 7.8's perimeter
  RCP. Four precisions:
  - **The actions:** `ec2:ModifySnapshotAttribute`, `ec2:ModifyImageAttribute`,
    `rds:ModifyDBSnapshotAttribute`, `rds:ModifyDBClusterSnapshotAttribute`. The AMI action is separate on
    purpose — snapshot controls do not cover EBS-backed AMIs, and an AMI shared out carries its snapshots
    with it. The RDS pair is **inert until an RDS exists**, which is the same order as the GuardDuty denies
    above and for the same reason (principle 9), not an oversight.
  - **Deny the actions outright; do not condition on the destination account.** The refinement that suggests
    itself — allow the share when the target is inside the organization — buys nothing here, because nothing
    in this design shares a snapshot with a sibling account at all, and a condition that has to name
    something correctly is a condition that will eventually be wrong in the silent direction (Lesson 14).
    Carve later against a real need, with the need recorded.
  - **No carve-out, and that is the test it passes** — the same standard 7.6 applies to the
    `CreateNotebookInstance` deny. Nothing this project builds shares a snapshot outside the organization,
    so this binds the infrastructure user exactly as hard as it binds a data scientist, which is what
    separates a control from a convention (Lesson 18). If a future restore-from-snapshot workflow needs it,
    that is an amendment with a reason, not a pre-emptive exemption.
  - **Battery (7.3), and it needs a target.** `ec2:ModifySnapshotAttribute` takes a `DryRun` parameter, so
    **try `--dry-run` first** — `DryRunOperation` versus `UnauthorizedOperation` is the clean pair and costs
    nothing. **Whether it short-circuits on permissions before validating the snapshot id is not something
    this plan knows**, so if the dry run fails on the id rather than on permissions, fall back to the
    battery's existing planned-cleanup exception: snapshot an empty 1 GiB volume in `Policy Canary`, attempt
    the share, read the error for *"with an explicit deny in a service control policy"*, and delete volume
    and snapshot in the same sitting. The RDS half has no dry run at all and stays untested until an RDS
    exists — record that as untested rather than as passed.
- **Deny `ecr-public:*` outright** (added 2026-08-12, user). ECR Public publishes to a world-readable
  gallery, so this is the one exfiltration route in the plan where the destination is *inside* the
  organization and the data is public anyway — which is exactly why the perimeter statement in
  `awsds-org-scp-perimeter.json` cannot reach it: `aws:ResourceOrgID` matches, correctly, and says nothing
  about who can read the result. Four precisions:
  - **The whole namespace, not the publish actions.** Enumerating `CreateRepository`, `PutImage` and the
    layer uploads leaves the deny one AWS release behind the service, which is the drift a namespace deny
    does not have. Nothing in this design calls `ecr-public` for anything.
  - **This does not break pulling from `public.ecr.aws`, and that is the sentence to read before panicking
    about it.** An anonymous pull from the public gallery involves **no IAM action at all** — it is not an
    authenticated AWS API call, so no SCP evaluates against it. Under egress design B the images arrive
    through the **pull-through cache** anyway, whose upstream fetch ECR performs itself. **The one thing
    that would force an amendment** is an authenticated pull taken for the higher rate limit
    (`ecr-public:GetAuthorizationToken`); if the Stage 8 image build turns out to need it, carve that single
    action with the reason recorded, rather than dropping the statement.
  - **It does *not* overlap the Region control — measured 2026-08-13, and the prediction here was wrong in
    the direction that would have mattered.** This paragraph used to say ECR Public is a `us-east-1`-only
    API so `CT.MULTISERVICE.PV.1` "very likely denies it already". It does not: **`ecr-public:*` is one of
    the 86 entries in AWS's `NotAction` list**, so the Region control exempts it outright and
    `DenyEcrPublicEntirely` is the *only* thing standing between this organization and a world-readable
    registry. Had the statement been skipped as redundant, nothing would have denied it. **The general
    shape is worth more than the fact:** "another control probably covers this" is a guess about a list
    somebody else maintains, and the honest version is to read the list — which is exactly what
    verification (vii) is for. It also removes the ambiguity the next paragraph worried about. **This is not the CloudTrail/Config
    case above** — there the duplication was of a Control Tower control with the *same* intent, and the
    instruction was to write only the gap. Here a different control catches the action for a different
    reason, and one statement is the cost of not depending on that.
  - Tested in the 7.5 window, before 7.7, on the reasoning that the two policies would otherwise be
    indistinguishable — and **re-run after the Region control was enabled on `Policy Test`, where it still
    comes back naming `p-1fp032g8`**, the baseline. That is the same finding as above from the other side:
    the ambiguity never existed, because the Region control never reaches this action.
- **Deny `iam:CreateUser` and `iam:CreateAccessKey`.** Principle 2 ("no IAM Users") is otherwise a
  convention with no enforcement. Break-glass (D16) is unaffected: the Management account is exempt from
  SCPs.
- **Deny `s3:PutAccountPublicAccessBlock`, with the decision-7 carve-out**, protecting the setting enabled
  in 7.4 step 1. Two mechanical precisions:
  - **One action, not two.** The `DeletePublicAccessBlock` API is governed by the
    `s3:PutAccountPublicAccessBlock` permission, so naming that one action covers both directions. Adding a
    `s3:DeleteAccountPublicAccessBlock` that does not exist is a statement that silently does nothing.
  - **The condition is on the principal's IAM role ARN**, per the trap in 7.3:

    ```json
    {
      "Sid": "DenyAccountBpaChangeExceptInfrastructure",
      "Effect": "Deny",
      "Action": "s3:PutAccountPublicAccessBlock",
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*"
        }
      }
    }
    ```

    The `*` between the service path and the role name absorbs the Region segment that Identity Center
    inserts (`.../sso.amazonaws.com/us-west-2/AWSReservedSSO_...`) — IAM wildcards are not path-aware, so
    one pattern covers both the with-Region and without-Region forms. **Exercise it from
    `awsds-policy-canary`, which is bound to `AWSAdministratorAccess` and therefore *not* exempt: the call
    must fail there and succeed under an `awsds-infra-*` profile.** That pair is the whole proof, and it is
    the reason the canary's permission set being the "wrong" one is useful here.

  **And never declare `aws_s3_account_public_access_block` in a Terraform slice.** It is the obvious
  thing for a later reader to "fix" — the account setting looks exactly like something that belongs in
  `foundation/` — and after this deny is attached, any apply or drift correction touching it fails from
  every principal except the carved-out one, which is not a property to rely on.
  `docs/plan/conventions.md` carries the exclusion so it is not only in this paragraph.
- **Deny `datazone:CreateDomain`, with a carve-out for the `Data` OU** (added 2026-08-08). D26 says there
  is one unified domain and it is registered in Data Governance; until now that was a sentence rather
  than a control, and a second domain anywhere would quietly reintroduce the thing the account split
  exists to prevent — a second interactive entry point with its own blueprints and its own project roles.
  Three precisions:
  - **The carve-out is the OU, not a role:** `aws:PrincipalOrgPaths` admitting the `Data` OU and nothing
    else. SCPs are ceilings and an explicit `Deny` wins wherever it appears, so the exception is a
    **condition on the root deny**, never an `Allow` in the `Data` OU's own set.
    **Three mechanics decide whether it works at all, and each fails in the direction of a deny that never
    lifts:**
    - `aws:PrincipalOrgPaths` is a **multi-valued** key, so the deny's condition is
      `"ForAllValues:StringNotLike"`, never a bare `"StringNotLike"` — a set operator is required and a
      missing one is a policy that does not evaluate the way it reads.
    - **`ForAllValues` is vacuously true over an empty set**, so the same
      `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}` that the perimeter statement needs belongs
      here too — otherwise the deny reaches AWS service principals, which do not carry the key at all.
      This is the identical trap in a third place, which is Lesson 14 arriving on schedule.
    - The value is the **full path with a trailing slash**: `<o-xxxx>/r-xxxx/<ou-id-of-Data>/`. `Data`
      sits directly under the root, so that is the whole path; append `*` instead of the final `/` only
      if the carve-out is ever meant to reach nested OUs. **7.0 step 1 wrote the ids down** — confirm the
      string against `aws organizations list-parents`, never against a screenshot.

    Get any of them wrong and Data Governance cannot create the domain the whole of Stage 6 depends on,
    with an `AccessDenied` that names the root policy and not the condition. Exercise **both** directions
    in 7.3 — from an administrator in `Policy Canary` (must fail).
  - **It must be `CreateDomain` alone and not `datazone:*` at the root.** Sandbox and Development need
    `datazone:PutEnvironmentBlueprintConfiguration` for the blueprints to provision into them at all, so
    a root-wide namespace deny would break Stage 6 rather than protect it. The `Workloads` OU tightens to
    the full namespace on top of this (7.6).
  - **Read this against INT-12 before attaching it, because the two collide.** INT-12's stated fallback,
    if the domain's account associations do not work, is *one V2 domain per Interactive account* — which
    this deny makes impossible. That is acceptable only because it is now explicit: if Stage 6 has to
    fall back, this policy is amended first (carve the `Interactive` OU in, or drop the root deny to the
    `Workloads` OU only), deliberately and with the reason recorded. A fallback silently forbidden by a
    policy written five stages earlier is the worst version of this.

#### 7.6 — The per-OU sets

One tier per OU policy set (D23), on top of the root set above. One file each:
`awsds-org-scp-ou-workloads.json`, `-data.json`, `-interactive.json`, `-identity.json`.

**DONE 2026-08-13 — all four attached to their OUs and exercised there.** Sizes minified: **451**, **886**,
**201** and **405** characters, so the per-node count of 7.0 step 5 is unchanged. What the run settled,
beyond the deny half working:

- **The API's denial message names the policy id** (`… explicit deny in a service control policy: …/p-xxxxxxxx`),
  so attribution needs no CloudTrail. **But when several attached policies deny the same call AWS names one
  of them** — parked together on `Policy Test`, the `Interactive` document decided *nothing* and was
  attached-but-unexercised until it reached its own OU (**Lesson 20**).
- **Decision 1 costs no feature, and that is now measured rather than argued.** From `awsds-infra-dev` and
  `awsds-infra-sandbox-1`: `sagemaker:CreateNotebookInstance` is denied by the `Interactive` document while
  **`sagemaker:CreateSpace` and `datazone:ListDomains` still succeed** — the SMUS surface and the blueprint
  path are untouched.
- **`Sandboxes` is governed by inheritance, with no policy of its own** — the same deny fires in
  `awsds-infra-sandbox-1`. That is the **SCP half of verification (xi)**; whether the OU can carry an
  *enabled control* is still 7.7's, and the two are not the same question.
- **`Data` and `Identity` differ exactly where they were written to differ:** `glue:StartCrawler` and
  `lakeformation:DeregisterResource` are denied in Data Governance and **allowed in Identity**, which is the
  cross-check that says neither statement is leaking from the root set.
- **`datazone:*` is denied in `Workloads` and allowed in `Data`** — D26's control plane stays reachable in
  the account that holds the domain.
- **Untested, and recorded as such:** `s3:DeleteBucket` (S3 answers `NoSuchBucket` before authorizing; its
  `Sid` is proven through `lakeformation:DeregisterResource`) and the **positive** half of the D27 carve-out,
  which needs the Stage 5 role.

##### 7.5a — the root document, re-read against AWS's action list (2026-08-13)

*Recorded here, under 7.6, rather than back in 7.5: both amendments came out of **one** review held after
the per-OU documents were attached, and splitting them across two sections would hide that the root
document and the OU documents were re-read in the same sitting, by the same method.*

**The same review, run a second time over the two documents on the root, found two statements written
against the wrong vocabulary.** Neither is a design error and both were verified rather than reasoned — the
machine-readable action list is the source in each case. `awsds-org-scp-perimeter` survived unchanged.

- **`DenyGuardDutyTampering` named a deprecated action and not its replacement.** GuardDuty renamed
  master→administrator and **both spellings exist as actions today**: the document denied
  `DisassociateFromMasterAccount` and left `DisassociateFromAdministratorAccount` open. Four more went in
  with it — `DisassociateMembers` and `StopMonitoringMembers` (the current member-detach pair, of which
  only `DeleteMembers` was covered) and `DeletePublishingDestination`/`UpdatePublishingDestination`, which
  kill or redirect the export of findings without touching a detector. **The statement is inert until
  GuardDuty is turned on (Stage 4 when this was written; Stage 15 since the 2026-08-18 split), which is
  why fixing it now costs nothing and fixing it later costs a detection gap nobody would see.**
- **`DenySnapshotAndImageSharing` claimed to close "the one exfiltration route that bypasses every other
  control" and closed half of it.** Sharing an attribute is one way an image leaves the organization;
  **writing it into a bucket is another**, and `ec2:CreateStoreImageTask`, `ec2:ExportImage`,
  `ec2:CreateInstanceExportTask` and `rds:StartExportTask` all exist. They went into a **new `Sid`,
  `DenyImageAndSnapshotExport`**, rather than into the old one: two mechanisms, two probes, and the log's
  existing entry keeps describing a statement that still exists under that name.

Minified: **baseline 1629** in the template, **1651** rendered; perimeter unchanged at **708**. **Amending a
root document is not a phase 4b re-probe** — the root set reaches `Policy Canary`, so this one went back
through **phases 1-3** of [`docs/plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md).

**UPLOADED AND EXERCISED 2026-08-13. Six probes on the canary, six denies, all naming `p-1fp032g8`:**

| Probe | Outcome |
|---|---|
| `guardduty:DisassociateFromAdministratorAccount` | **denied** — the spelling that was open before this amendment, and the one call that justifies it |
| `guardduty:UpdateDetector` | denied (regression: it was already covered) |
| `guardduty:StopMonitoringMembers` | denied |
| `ec2:ExportImage` | **denied** — `DenyImageAndSnapshotExport`'s first real answer |
| `ec2:CreateInstanceExportTask` | denied |
| `ec2:CreateStoreImageTask` | denied, **on the second attempt** — see below |
| `rds:StartExportTask` | denied |

**GuardDuty authorizes before validating the detector id**, so all three of its probes measured with an
invented id — the opposite of what EC2 and RDS do, and the reason the amendment could be proven at all
while the service is still off in every account.

**The finding that outlives this sitting is about probing, not about GuardDuty.** The
validation-before-authorization wall is **per action, not per service**: in the same run, `ec2:ExportImage`
and `ec2:CreateInstanceExportTask` authorized against a *malformed* AMI id and came back denied, while
`ec2:CreateStoreImageTask` rejected the same id shape as `InvalidAMIID.Malformed` and only reached
authorization once a **real public AMI** was passed. So a first-try validation error is **a reason to retry
with something that exists, not a result** — recorded as a boxed rule in the battery runbook, because
recording *untested* too early understates the ceiling and costs the next reader an evening.
`ec2:StartInstances` is the one that stayed genuinely untested: `Malformed` at 17 characters, `NotFound` at
8, never authorization.

**One collision was found and deliberately not fixed here.** `guardduty:UpdateDetector` is denied
unconditionally on the root, so it reaches **Audit**, the GuardDuty administrator: org-wide administration
is unaffected (`UpdateOrganizationConfiguration`, `UpdateMemberDetectors`), but enabling a feature on
*Audit's own detector* is denied — which since the 2026-08-18 split is met twice: first by
[Stage 15](stage-15-guardduty.md)'s switch-OFF (its decision 1), then by [Stage 11 step 4](stage-11-dlp.md)'s
switch-on. It stays unconditional because the alternative is a carve-out naming a role that does not exist
yet, and a carve-out written before its principal is Lesson 14 waiting to happen — and Stage 15's step 5
later confirmed no such role ever appears. **Recorded in three places so it cannot be met cold**:
[Stage 15](stage-15-guardduty.md) step 0, Stage 11 step 4, and the note under the baseline table in
[`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md).

##### 7.6a — the amendment the post-attachment review produced (2026-08-13)

**Re-reading the four documents against what the probes had just measured found no error and three gaps of
scope.** Two of them changed `awsds-org-scp-ou-data` and `awsds-org-scp-ou-identity`; the third changed only
what is written down. **The documents in `policies/` are amended; `update-policy` and the phase 4b re-probe
are what close it** — until then the deployed content is the 2026-08-13 original.

- **`DenyUserCompute` did not hold its own name (Lesson 5).** It denied `ec2:RunInstances`, which is one
  launch door of several: `ec2:CreateFleet`, `RequestSpotInstances` and `RequestSpotFleet` all start
  instances without ever calling it, and `StartInstances` restarts a stopped one. All four verified as real
  action names against the machine-readable list, and added to both documents. Minified sizes go
  **886 → 1033** (`Data`) and **405 → 494** (`Identity`), so the per-node budget of 7.0 step 5 is still not
  in question. The residual is named rather than closed: an Auto Scaling group launches through a
  **service-linked role**, which AWS exempts from SCPs, so `autoscaling:CreateAutoScalingGroup` remains
  outside any document's reach.
- **The D27 carve-out was the one conditioned statement without the service guard (Lesson 14).** The two
  root statements both carry `BoolIfExists: aws:PrincipalIsAWSService=false`; this one carried only
  `ArnNotEquals`. An `ArnNotEquals` carve-out can only exempt principals it can spell, so a crawler run
  *initiated by Glue itself* would land on the deny side of a principal test it was never meant to take.
  **Nothing measured this and nothing can** — `aws:PrincipalIsAWSService` is set by AWS, not by the caller —
  and the schedule that would provoke it is the one [Stage 5](stage-05-data-foundation.md) deliberately does
  not create. It is fixed because the asymmetry is what the next reader would have had to re-derive.
- **Two absences in `DenyUserCompute` are deliberate and were not written anywhere.** `athena:StartQueryExecution`
  is *allowed* in `Data`, because Stage 5's Iceberg `OPTIMIZE`/`VACUUM` runs through it — so the lake
  account keeps a full read path with results written to S3, which the perimeter document only stops when
  the destination is outside the organization. EMR, EMR Serverless and Batch are uncovered because nothing
  in this design uses them. Both are now stated in [`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md),
  and the Athena path is written into [Stage 11](stage-11-dlp.md) as a detection target. **A hole that is
  documented is a decision; the same hole undocumented is the finding of a later audit.** *(The Athena
  half was overtaken on 2026-08-18: Stage 5 decision 4 chose Glue automatic compaction over Athena
  `OPTIMIZE`/`VACUUM`, so the allowance lost its reason — the amendment closing it is owed at Stage 5
  step 4.3, through phase 4b. This bullet stays as written because it records why the absence was
  deliberate at attachment; `POLICIES.md` carries the current reading.)*

**UPLOADED AND EXERCISED 2026-08-13, in each OU's own account** (phase 4b — the canary cannot reach these
OUs). `DenyUserCompute` now carries **18 actions** in both documents, and the read-back from Organizations
confirms the `BoolIfExists` guard is live in `Data`:

| Probe | `awsds-infra-data` | `awsds-infra-identity` |
|---|---|---|
| `ec2:RequestSpotInstances` (real AMI + real subnet, `--dry-run`) | **denied**, `p-gl01bcdm` | **denied**, `p-mmfc17ac` |
| `ec2:CreateFleet` (`--dry-run`, launch template that does not exist) | **denied**, `p-gl01bcdm` | **denied**, `p-mmfc17ac` |
| `ec2:StartInstances` (`--dry-run`) | **untested** — validated first | **untested** |
| `glue:StartCrawler` | denied, `p-gl01bcdm` — **the guard did not invert the carve-out** | *allowed* (`EntityNotFoundException`), the cross-check still holding |
| floor: `sts`, `s3 ls`, `describe-vpcs`, `glue get-databases` | all OK | all OK |

**`ec2:CreateFleet` was expected to be untestable and is not** — `--dry-run` authorizes *before* resolving
the launch template, so a name that exists nowhere still produces a real answer. That matters beyond the
probe: `CreateFleet` was the launch door this amendment was written for, and it is now the one proven
directly rather than by inference from its siblings. Nothing was created: spot requests and fleets both read
zero in both accounts afterwards.

**What the review did *not* change, and why the reasoning is worth keeping:** `s3:DeleteBucket` stays
unconditional in `Data` even though it reaches every bucket in the account and will stop a
`terraform destroy` — the amendment procedure went into [Stage 5](stage-05-data-foundation.md) instead,
because a statement scoped to a bucket-name pattern leaves anything outside the pattern unprotected in
silence, and this one binding the builder is the property that makes it a control.

**Verification (viii) is answered, and it was answered against AWS's own machine-readable action list**
(`https://servicereference.us-east-1.amazonaws.com/v1/<service>/<service>.json`) rather than against
documentation prose — the names in these documents are the names the service publishes today:

| Asked | Answered |
|---|---|
| Are `sagemaker:CreateSpace`, `CreateApp` and `StartSession` real names today? | **All three, yes.** `StartSession` is described by the API itself as *initiating a remote connection between a local IDE and a remote SageMaker space* — the local-VS-Code objective of `CLAUDE.md`, named exactly, and it matches neither `Create*` nor `datazone:*` |
| Which namespace does the **domain** evaluate under, asked of the `Data` OU? | **`datazone:*`.** A Unified Studio domain is created through the DataZone control plane (`datazone:CreateDomain`), with two roles the administrator supplies — `AmazonSageMakerDomainExecution` and `AmazonSageMakerDomainService`. No `sagemaker:Create*` appears in that path, so the `Data` OU's wildcard stands and **no carve-out is widened** |
| Where does `sagemaker:*` appear, then? | In whichever account a **project profile** targets when the ML surface provisions — Sandbox or Development by D26, never Data Governance. The multi-account mechanism has its own surface (`datazone:CreateAccountPool`, `StartAccountBootstrapAction`), which belongs to INT-12 and Stage 6 |

**The residual, stated rather than closed:** if Stage 6 ever provisions a project *into* Data Governance,
this deny is what stops it — five stages from here, with an `AccessDenied` naming the OU policy. That is
the intended direction (D26 says projects do not land there), and
[Stage 6 step 0](stage-06a-unified-studio.md) is already the place where this and the
`datazone:CreateDomain` carve-out are exercised together, before the domain is created.

**Four things were added or narrowed while writing, each with its reason:**

- **`Workloads` gains `sagemaker:CreateApp` and the two classic notebook-instance actions.** The table
  below says an SMUS notebook is a space *plus an app*, so denying the space and not the app is half a
  control. And decision 1's deny belongs here *a fortiori*: a deployment target able to stand up a classic
  notebook instance is exactly the ungoverned interactive surface D17 forbids, and `Interactive` denying it
  while `Workloads` permits it would be backwards.
- **`Workloads` may never use `sagemaker:Create*`, and the document is enumerated for that reason.**
  Staging and Production are where models are deployed — `CreateModel`, `CreateEndpoint` and
  `CreateTrainingJob` are their job. The wildcard belongs to `Data` and `Identity`, where nothing is
  supposed to run at all; the two documents are mirrors on purpose, and the failure of getting this
  backwards is a stage that cannot deploy rather than a route that stays open.
- **`Data`'s catalog-maintenance carve-out is on the crawler *runs*, not on their creation.** This narrows
  D27's mechanics line, for Lesson 18's reason: creating a crawler is Terraform's work, which is
  `InfrastructureAccess`, which is an administrator of that account — so a deny on the create action would
  have to exempt precisely the principal it was written to bind. **What D27 protects is the run**, because
  the run is what samples object contents. The exempt ARN names `awsds-data-catalog-maintenance` in the
  Data Governance account: **a contract with [Stage 5](stage-05-data-foundation.md)**, whose failure
  direction is closed (the crawler does not run) rather than open. **Its positive half cannot be exercised
  in this stage** — the role does not exist yet — so the battery records it as *untested until Stage 5*,
  which is a different sentence from "passed".
- **`Data` and `Identity` spell "interactive sessions and notebooks" as actions.** D25 and D27 both use
  those words; the actions behind them are `glue:CreateSession` and `glue:RunStatement` (a notebook
  attached to a Glue interactive session), `glue:StartNotebook` and `glue:CreateMLTransform` — none of
  which `CreateJob`/`StartJobRun` reaches. This is D25's own lesson applied once more: the gap that decision
  found was an enumerated list missing the action that mattered.

> **The Unified Studio surface, and why every deny below is now written against an API and not against a
> feature name.** `CLAUDE.md` gained six named SMUS features on 2026-08-13, and one of them —
> *"users can instantiate as many Jupyter notebook instances as they like"* — reads exactly like the thing
> the `Interactive` OU candidate deny forbids. It is not. Verified against AWS's documentation on
> 2026-08-13:
>
> | The feature, as `CLAUDE.md` states it | What it actually calls |
> |---|---|
> | Jupyter notebooks, "as many instances as they like" | a **space** plus an **app** — `sagemaker:CreateSpace`, `sagemaker:CreateApp`. **Not** `CreateNotebookInstance`, which is the standalone, pre-Studio product |
> | VS Code instances, incl. connecting a local VS Code | the same space/app pair with a Code Editor app, plus **`sagemaker:StartSession`** for the remote connection — an action that appears nowhere in this plan and that `sagemaker:Create*` does not match |
> | catalog, explorer, SQL | `datazone:*` for the catalog, `athena:*` / `glue:Get*` / `redshift-serverless:*` for the query |
> | S3 buckets from the SMUS UI | project buckets provisioned by a blueprint's own role, not by the user |
> | workflows and Visual ETL | **MWAA** (serverless or provisioned) and **Glue** — which is why D7/D28 and Stage 10 are the same surface as this feature, not a parallel one |
> | AI models | `bedrock:*` and the SageMaker inference actions |
>
> Three consequences land in this subsection, and one lands in Stage 6 (see the note at the end).

- **`Workloads` OU** (D20) — deny `sagemaker:CreateDomain`, `sagemaker:CreateUserProfile` and
  `sagemaker:CreatePresignedDomainUrl`. This is what turns D17 from an intention into a control: "no
  Studio outside the Interactive OU" cannot be undone by anyone with a console and a good reason.
  **And deny `datazone:*` outright, which the SageMaker list does not cover (corrected 2026-08-08).**
  Those three actions were the whole control when the interactive surface was the classic Studio; since
  D26 it is a DataZone V2 domain, and D26's "Staging and Production are never associated" had no policy
  line behind it. Three things were reachable and are now not:
  - **A DataZone domain created locally** in Staging or Production.
  - **The account associating itself to a domain and configuring a blueprint**
    (`datazone:PutEnvironmentBlueprintConfiguration`), which mints provisioning and manage-access roles
    with broad permissions in the account — even where the provisioning then fails.
  - **The blueprints that are not the ML one.** Tooling and Lakehouse provision a project bucket, a Glue
    database and an Athena workgroup; none of that passes through `sagemaker:*`, so none of it was
    denied.

  **Why the whole namespace rather than a list of actions.** This plan has already paid for an enumerated
  deny once: the `Data` OU list below omitted `glue:CreateJob` and left the whole ingestion runnable in
  the wrong account until D25 caught it. DataZone gains APIs, and a list written today goes stale in the
  direction of the false negative. Nothing legitimate in this design calls DataZone from a deployment
  target: what crosses the gate is the D28 artifact set, and Production's governed write resolves through
  Lake Formation, not through DataZone. **Revision trigger:** the first time Production needs to publish
  a data product of its own.
  **Add `sagemaker:StartSession` and `sagemaker:CreateSpace` to this list** (2026-08-13). A space needs a
  domain and the domain is denied, so this is belt-and-braces — but `StartSession` is a *remote shell into
  a running space from a laptop*, it is new enough that nothing else in this plan mentions it, and it
  matches neither `Create*` nor `datazone:*`. A deny that depends on a second deny holding is exactly what
  a per-OU tier is for.
  **What is *not* the gate, and it is worth knowing before debugging this.** The account association is
  not held back by anyone declining a RAM invitation: `ram:EnableSharingWithAwsOrganization` (Stage 1d step 11)
  makes shares inside the organization arrive without an invitation to accept. The gate is the target
  account being unable to configure a blueprint.

- **`Data` OU** (D22) — deny compute creation outright (`ec2:RunInstances`, `sagemaker:Create*`,
  `glue:CreateDevEndpoint`, **`glue:CreateJob` and `glue:StartJobRun`** — added by D25, because the
  original list left a Glue ETL job as a perfectly legal way to run the whole ingestion in the account
  whose entire policy set says nothing runs there — and ECS/Lambda creation), deny `s3:DeleteBucket` and
  `lakeformation:DeregisterResource`. The lake account's SCP is about what can never happen there,
  because nothing is supposed to *run* there at all. Two named carve-outs, and they are per-statement:
  `datazone:*` as a governance control plane (D26), and `glue:CreateCrawler`/`StartCrawler` plus the
  table-optimizer and column-statistics actions **only when the principal is the catalog-maintenance
  role** (D27).
  **`sagemaker:Create*` does not reach `sagemaker:StartSession`** — add it here explicitly, for the same
  reason as in `Workloads` and with more force: this account is supposed to have no interactive surface at
  all, and a remote IDE session is the most interactive thing there is.
  **The `sagemaker:Create*` line is the one to re-read before attaching, because this list predates D26.**
  It was written when the only thing that could run in Data Governance was a job somebody started by
  hand; since D26 the account also holds the **unified domain**, whose creation and whose Tooling
  blueprint provision resources into this very account. If any part of that surface evaluates under
  `sagemaker:*` rather than `datazone:*` — which is exactly what verification (viii) asks — then a
  `datazone:*`-only carve-out leaves the `Data` OU denying the creation of the domain the whole of
  Stage 6 depends on, five stages before anyone tries it. **So answer (viii) against the `Data` OU as
  well as against `Workloads`**, and if the answer is mixed, widen this carve-out to the specific
  `sagemaker:*` actions the domain needs rather than dropping the deny. The distinction the deny is
  protecting is *user compute*, not *the control plane that happens to share a prefix with it*.

- **`Interactive` OU** (D21) — **read this before writing anything here, because the phrase the plan used
  to carry did not describe a policy.** "Human infrastructure changes denied" appeared across six files as
  a property of this OU's SCP set, and no SCP implements it. What actually stops the data scientist from
  creating a VPC is `DataScientistAccess` and its permissions boundary — an **identity** policy,
  enumerated by hand, which is exactly the sort of thing an SCP is supposed to back up rather than the
  thing an SCP *is* (Lesson 5). Corrected across those files on 2026-08-09.
  *(Note the tense: `DataScientistAccess` does not exist yet — it is written at Stage 2 step 5, from the
  design in 1b step 3.4. Nobody it would constrain can sign in before Stage 6, so the gap is real and
  harmless.)*

  > **Decision 1 — settled 2026-08-13: the OU gets a set of its own, and it holds exactly one statement.**
  > Deny **`sagemaker:CreateNotebookInstance`** and **`sagemaker:CreatePresignedNotebookInstanceUrl`**.
  >
  > **What settled it was the table above, not a preference.** The candidate was left unadopted because
  > "the data scientist must be able to create notebooks" and "deny creating notebook instances" could not
  > both be true. They can: SMUS notebooks are **spaces and apps**, and the classic notebook instance is a
  > different product that this design uses nowhere. Denying it removes an ungoverned interactive surface
  > — one that bypasses the domain, the VPC-only app configuration and the `dev-env` image gate in a single
  > call — **without touching any feature `CLAUDE.md` asks for**.
  >
  > **It needs no carve-out at all, which is the property that makes it a control rather than a
  > convention.** It binds `InfrastructureAccess` exactly as hard as it binds anyone, and nothing in this
  > design — no blueprint, no Terraform module, no pipeline — calls either action. That is what the other
  > candidates for this OU could not offer: a deny of "infrastructure changes" here would have to exempt
  > the builder, which is the shape D30 proposed and had reverted, and then exempt DataZone's provisioning
  > roles, which do not exist until Stage 6 (Lesson 17).
  >
  > **Revision trigger, and it is the only thing that would undo this:** if any SMUS surface turns out to
  > provision a classic notebook instance on the user's behalf, the deny is dropped and the reason
  > recorded. Verification (viii) is where that would surface. Until then, adopt it.

  - **Attach it here and not to the nested `Sandboxes` OU** (D23, D35). `Sandboxes` groups the accounts
    that multiply and carries no set of its own; inheritance is what makes a unit vended next year
    governed on arrival, and a set attached twice is a set that will diverge in one of the two places.
  - The differences between Sandbox and Development are differences of content, not of policy, which is
    why they share the OU.

- **`Identity` OU** (D10, D23 as revised 2026-08-09) — **the tier this plan did not have, because the
  account was supposed to be in `Security`.** It is not: Control Tower refused the vend into a
  foundational OU (1a log), so the account sits in a sibling OU. Two things, in this order:
  - **The baseline is established, and it is not what this file assumed** (7.0 step 2, 2026-08-13). The
    assumption was that *"an OU created outside Control Tower's own flow carries no policy set until code
    attaches one"* — **false here: `Identity` carries `aws-guardrails-coSzJr`, the standard eight
    statements, identical to `Workloads`, `Data`, `Interactive` and `Policy Test`.** It is registered. What
    `Security` has extra is exactly three statements — `CTSNSPV1`, `CTS3PV7`, `CTS3PV8` — about the
    log-archive, access-logs and cloudtrail buckets and the centralized-logging SNS topic, **none of which
    means anything for an account that holds neither bucket**. So the SCP half of the diff this bullet asks
    for is done, it is in the log, and **no elective control is owed to `Identity` on that basis**. The
    *enabled-control* half is still open and comes from 7.0 step 3 on Management — a control is not an SCP,
    and "it carries the same guardrail policy" is not evidence that it carries the same controls.
  - **Then the hand-written set.** The root SCPs and RCPs already reach this account by inheritance, so
    what belongs *here* is what makes the identity plane's own blast radius smaller: deny the account
    creating compute at all — there is no workload here, only Terraform managing Identity Center, so
    `ec2:RunInstances`, `sagemaker:Create*` (plus `StartSession`) and the rest of the `Data` compute list
    apply for exactly the same reason they apply to `Data`. **Whether a CloudTrail deny belongs here is
    answered by 7.0 step 2**, not assumed: if Control Tower's mandatory control already covers it on this
    OU, writing a second one buys a second thing to maintain.
  - **Do not put the Identity account under the `Data` OU's set to save writing one**, tempting as the
    overlap looks: `Data`'s set denies `s3:DeleteBucket` and `lakeformation:DeregisterResource` and carves
    out `datazone:*` and the catalog-maintenance role, none of which means anything here, and an OU whose
    policy is *mostly* right is the kind of thing nobody re-reads.

**One consequence of the SMUS table lands outside this stage and is recorded so it is not lost here:** the
remote-IDE path (`sagemaker:StartSession`, a local VS Code attached to a running space) is a **file-transfer
channel to a laptop**, which is a Stage 11 threat-model item and an open question, not an SCP line —
denying it in the Interactive OU would deny the feature `CLAUDE.md` asks for. See
[`docs/plan/open-questions.md`](../open-questions.md) items 12-14.

#### 7.7 — The Control Tower managed controls: use theirs, do not hand-roll these two

**Before anything in this subsection: 7.0 step 3 must have returned a control list for every target OU.**
A managed control can only be enabled on a *registered* OU, and an unregistered target **errors rather than
returning an empty list** — which reads like a permissions problem and is not. D29's whole battery assumes
`Policy Test` is registered, and an unregistered OU has no control baseline, so a test against it would
measure something else.

> **`Sandboxes` is the one to go in expecting trouble from, and 7.0 step 2 is why** (2026-08-13). It is the
> only OU in the organization with **no `aws-guardrails-*` policy at all** — every other OU has one. Two
> readings, and step 3 on Management is what separates them:
>
> - **It is not registered.** Then `CT.MULTISERVICE.PV.1` **cannot be enabled on it**, and the choice is to
>   register it first (a Control Tower operation, and the honest fix) or to rely on inheritance.
> - **Control Tower attaches nothing to nested children and relies on inheritance from `Interactive`.**
>   Then the accounts inside `Sandboxes` are already governed by `Interactive`'s guardrail, and the Region
>   control enabled on `Interactive` reaches them the same way — because a Control Tower control of this
>   kind *is* an SCP, and SCP inheritance does not care whether the child OU is a registered target.
>
> **Either way the accounts end up covered; what differs is whether `Sandboxes` is a place policy can be
> attached at all** — which is a Stage 14 question as much as a 7.7 one, since that is where the OU starts
> filling up. Record which reading was true, and if it is the first, register the OU before enabling
> anything on it rather than skipping it silently.

- **Region restriction** (revised 2026-08-08; **corrected 2026-08-09 — there are two of these controls,
  and the plan knew only the one that cannot be canary-tested**). Goal unchanged: **`us-west-2` as the
  only allowed region**. Three reasons it is not in the hand-written set:
  - **Global services resolve to `us-east-1`.** `iam:CreateRole` goes to `iam.amazonaws.com`, which
    answers in `us-east-1`, so `aws:RequestedRegion` is `us-east-1` and a naive deny breaks IAM outright.
    The correct exemption is **`NotAction` on the global service prefixes**, never adding `us-east-1` to
    the allowed regions — the second is what an earlier version of this plan described, and it is much
    looser: it would permit `ec2:RunInstances` in a region with no Config recorder, no GuardDuty and no
    endpoints, which is precisely the blind spot the control exists to remove.
  - **That exemption list has to stay complete as AWS ships services, and AWS maintains theirs.** This is
    Lesson 14 applied to a list rather than to a condition — and the useful finding is that **AWS's
    default `NotAction` already contains every prefix this project was worried about**: `iam:*`,
    `organizations:*`, `sts:*`, `kms:*`, `sso:*`, `config:*`, `access-analyzer:*`, `route53:*`,
    **`route53domains:*`** (a separate prefix, and the one that registers the D15 domain at Stage 13),
    `acm:*`, `cloudfront:*`, `shield:*`, `waf:*`/`wafv2:*`, the whole billing family
    (`billing:*`, `budgets:*`, `ce:*`, `cur:*`, `pricing:*`, `tax:*`), and **`s3:PutAccountPublicAccessBlock`
    plus `s3:ListAllMyBuckets`** — the pair that interlocks with 7.4. **So do not maintain a list: read
    the current one off the control's `Artifacts` tab in the Control Tower console and diff it against
    what this project calls** (**verification (vii)**), then add only what is genuinely missing, through
    `ExemptedActions`.
  - **It also needs principal exemptions, not just service ones.** AWS's default already exempts
    `AWSControlTowerExecution`, `aws-controltower-ConfigRecorderRole`,
    `aws-controltower-ForwardSnsNotificationRole` and `AWSControlTower_VPCFlowLogsRole`, or the landing
    zone's own machinery breaks. A hand-written control has to remember them; this is the third reason
    not to write one.

  | | `GRREGIONDENY` | `CT.MULTISERVICE.PV.1` |
  |---|---|---|
  | Scope | The **whole landing zone**; applies to every registered OU at once | **Per OU**, chosen at enable time |
  | How | Landing zone settings → **Modify settings** — i.e. a landing-zone update, not a checkbox | Controls library → **Enable control** → pick the OU, or `aws controltower enable-control` |
  | Parameters | Region list only | `AllowedRegions` (mandatory), `ExemptedActions`, `ExemptedPrincipalARNs` |
  | Canary-testable (D29) | **No** | **Yes — enable it on `Policy Test` first** |

  > **Decision 6 — settled by the user, 2026-08-13: `CT.MULTISERVICE.PV.1`, per OU.** It is the only one of
  > the two that can be exercised against `Policy Test` before it reaches anything real, which is what D29
  > exists to require; it is parameterized where the other is not; and it avoids a landing-zone update.
  > What it costs is one Control Tower operation per OU, serialized — budget sitting B for that, not for a
  > click. **`GRREGIONDENY` is not enabled**, and enabling *both* is what would be hard to undo, because
  > AWS says the interaction between them is not predictable.

  **The order.** Enable it on **`Policy Test`** with `AllowedRegions=["us-west-2"]`, run the region pair
  from 7.3 under `awsds-policy-canary` (`us-east-1` → `UnauthorizedOperation`, `us-west-2` →
  `DryRunOperation`), and confirm the *must still succeed* list — `iam:ListRoles`, `budgets:DescribeBudgets`,
  `ce:GetCostAndUsage`.
  > **That pair is `./aws/probes/scp-battery.py --phase region`, and the *before* reading is already
  > taken** (2026-08-13): `us-east-1` came back `DryRunOperation` — allowed — while all four global-service
  > floor calls succeeded. So the phase currently reports one `FAIL`, and **that failing row is the
  > baseline**: it is what says the control is genuinely not enabled yet rather than enabled and inert.
  > Re-run the same phase after enabling, and the single row that must flip is the `us-east-1` one. A run
  > where *both* rows flip is the loose construction (`us-east-1` added to the allowed list) rather than the
  > control this step asks for. Only then enable it on `Interactive`, `Sandboxes`, `Workloads`, `Data` and
  `Identity`. **`Sandboxes` is on that list on purpose, and it is now the one with a known question mark:**
  a control enabled on `Interactive` is not automatically *enabled* on a nested child, but the SCP such a
  control attaches **is inherited** by one — and 7.0 step 2 found that `Sandboxes` carries no policy of its
  own at all. Read the box at the top of this subsection first, enable `Interactive`, then look at
  `Sandboxes` again: whether it needs its own enablement, cannot take one, or is already covered is
  verification (xi) — and the answer is the same for every OU Stage 14 ever nests there.

  > **ANSWERED, AND THEN REVERSED BY DECISION (2026-08-13).** `Sandboxes` *can* take an enablement of its
  > own — it accepted `enable-control` and carried `aws-guardrails-yvYgxw` (`p-h7lc62d0`), the first policy
  > that OU ever held. **The control was then disabled again and the document ceased to exist**, because
  > the user settled the general rule, now **[D37](../decisions/D37-nested-ou-inheritance.md)**: **nothing is attached or enabled on `Sandboxes` — no SCP, no RCP, no
  > tag policy, no control — unless it is a configuration that differs from `Interactive`'s.** Sameness is
  > expressed by inheriting, never by copying.
  >
  > **The measurement is what makes that a choice rather than a gap.** 7.6 proved the SCP half — the deny
  > fires in `awsds-infra-sandbox-1` with nothing attached to `Sandboxes` — and this step proved the OU is
  > a registered target, so the option was declined knowingly. What it costs is **Control Tower's own
  > reporting**: an enabled control is per OU and is not inherited *as an enablement*, only the statements
  > it emits are, so `Sandboxes` reads as zero controls while its accounts are fully governed. The drift
  > view is not the ceiling — read the parent. What it buys is Lesson 14 run backwards: a duplicated
  > statement is a second place to forget an amendment, and `ExemptAssumeRoot` is the worked example.
  >
  > **This governs Stage 14**, where every new per-unit Sandbox account lands under this OU
  > ([`docs/plan/architecture.md`](../architecture.md) carries the rule).

  **Two facts to have before you start.** The home region cannot be denied, and *nothing must already
  exist in the regions being denied* — trivially true here, and it is the reason to do this now rather
  than at Stage 12. The control is reversible from the Control Tower console.

  **ENABLED ON `Policy Test` 2026-08-13, and verification (vii) is answered from the deployed document
  rather than from a console tab.** The control lands as an ordinary SCP — `aws-guardrails-njKkvb`
  (`p-q3y11w1n`), one statement, `Sid: CTMULTISERVICEPV1` — which means it can be read back with
  `organizations describe-policy` from Identity and diffed like anything else. That is a better answer than
  the `Artifacts` tab the plan originally pointed at, and it is repeatable per OU.

  | Read from the attached document | Value |
  |---|---|
  | `NotAction` entries | **86**, all AWS's; this project added **no** `ExemptedActions` |
  | Condition | `StringNotEquals` on `aws:RequestedRegion = ["us-west-2"]`, and `ArnNotLike` on **`aws:PrincipalARN`** — note AWS's own spelling of the key differs in case from the `aws:PrincipalArn` this project writes; IAM keys are case-insensitive, so both are the same key |
  | Exempted principals | exactly the four the plan predicted: `AWSControlTowerExecution`, `aws-controltower-ConfigRecorderRole`, `aws-controltower-ForwardSnsNotificationRole`, `AWSControlTower_VPCFlowLogsRole` |

  **Every global-service prefix this project calls is present**, checked one by one rather than assumed:
  `iam`, `organizations`, `sts`, `kms`, `sso`, `config`, `access-analyzer`, `route53`, **`route53domains`**
  (Stage 13's registration, `us-east-1`-only), `acm`, `cloudfront`, `shield`, `waf`/`wafv2`, the whole
  billing family (`billing`, `budgets`, `ce`, `cur`, `pricing`, `tax`), `support`, `health`, `account`,
  `notifications`, and the three S3 account-level actions 7.4 depends on — `PutAccountPublicAccessBlock`,
  `GetAccountPublicAccessBlock`, `ListAllMyBuckets`. **Plus `ecr-public:*`, which is the correction above.**

  **What is deliberately absent is the control working**: `sagemaker`, `glue`, `datazone`, `lakeformation`,
  `ecr`, `ram`, `guardduty`, `securityhub`, `macie2` and `ssm` are all regional and are all denied outside
  `us-west-2`. Two consequences worth carrying rather than rediscovering:

  - **`ssm:GetParameter` is denied in `us-east-1`**, which broke the first version of the region probe — it
    resolved its AMI through the public SSM parameter *in the region being denied*, so the probe degraded
    to `UNTESTED` at the exact moment it finally had something to measure. The probe now uses
    `ec2:CreateKeyPair --dry-run`, which needs no resource at all.
  - **`cloudshell:*` and `servicequotas:*` are not exempt either.** Neither has bitten yet because both are
    used from **Management**, which is SCP-exempt — but a CloudShell opened in a *governed* account must be
    opened in `us-west-2`, and that is the kind of thing that reads as a broken console rather than as a
    control doing its job.

- **The two root-user controls, and the one parameter that decides whether they break 1a step 6.**
  `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` and `AWS-GR_RESTRICT_ROOT_USER` are *strongly recommended*
  controls — **not enabled by default**, so today the organization has neither.
  - The access-key one is free of consequences and matches the invariant D16 already states.
  - The other denies `*` wherever `aws:PrincipalArn` matches `arn:*:iam::*:root`, and **that reaches the
    privileged root sessions 1a step 6 depends on**: in a member account an `sts:AssumeRoot` session *is*
    that principal, so the control would deny the very action that restores a root credential or unlocks
    a self-denied S3 bucket policy. Enable it **with the `ExemptAssumeRoot` parameter**, which carves the
    centralized path back out by exempting requests carrying `aws:AssumedRoot`.
    **Three mechanics, confirmed against the control's documentation, because each is a way to get it
    wrong:** the parameter exists **only** on `AWS-GR_RESTRICT_ROOT_USER`; it is set **per OU**, at enable
    time, so every OU this control is enabled on needs it — miss one and 1a step 6's recovery path is
    closed in exactly that OU; and **it does not accept `false`** — presence means exempt, absence means
    not exempt, so "set it to false" is not a thing you can do or read back.
  - Both controls also take `ExemptedPrincipalArns`; neither exemption should be a wildcard account.
  - **The asymmetry that makes this safe to enable at all:** the controls attach to OUs, and the
    Management account is exempt from SCPs, so the break-glass root is untouched either way (D16).
    Enabled from the Control Tower console, so this one is reversible without a detach.

  > **ENABLED ON `Policy Test` 2026-08-13 — first *without* `ExemptAssumeRoot`, then corrected the same
  > day. The correction is measured; what is left is the five real OUs.** Control Tower folded both
  > statements into the OU's *existing* guardrail policy `aws-guardrails-vldGRP` (`p-kve97k0o`), and the
  > first read showed `GRRESTRICTROOTUSER` as `Deny *` on `ArnLike aws:PrincipalArn = arn:*:iam::*:root`
  > with **no second condition**. Re-enabling with the parameter produced exactly what 1a step 6.7
  > predicted:
  >
  > ```json
  > "Condition": { "Null":    { "aws:AssumedRoot": "true" },
  >                "ArnLike": { "aws:PrincipalArn": ["arn:*:iam::*:root"] } }
  > ```
  >
  > The two conditions are ANDed, so the deny fires only where the principal is a root ARN **and** the key
  > is absent — which is every root principal *except* a privileged session. **The policy id did not
  > change**: Control Tower edited the document in place rather than issuing a new one, so before and after
  > are a clean diff on one object and there is no second id to track. Org-wide, `aws:AssumedRoot` now
  > appears in **exactly one** policy, and the two root-user statements exist **only** there.
  >
  > **Why it was found rather than probed:** no CLI probe can measure this. Every principal available to
  > this project is an Identity Center role, and `ArnLike …:root` never matches one, so the statement is
  > invisible to the battery in both directions. **The document read is the only instrument**, which makes
  > this the first control in the stage whose verification is *reading* rather than *attempting* — worth
  > noticing, because the reflex by now is to reach for a probe.
  >
  > **What the omission would have cost, and why it was nearly free here.** 1a step 6.4 measured that **no
  > member account holds root credentials** — no password, therefore no root sign-in and no root access
  > key. So in a governed account the *only* way a request can carry `arn:aws:iam::<acct>:root` is an
  > `AssumeRoot` session, and an unexempted control denies **exactly and only** that: the population it
  > would otherwise restrict is empty by construction. It is also self-sealing — `IAMCreateRootUserPassword`
  > runs *inside* such a session, so the control denies the one path that could create the principal it
  > claims to restrict. The blast radius was one throwaway account, and Management, where the break-glass
  > root lives, is SCP-exempt regardless (D16). **That is the whole reason the canary exists**: the mistake
  > happened where mistakes are supposed to happen, before the control reached anything real.
  >
  > **The access-key control carries no exemption, and that asymmetry is correct rather than an oversight.**
  > The parameter does not exist on `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` — and should not: a root access
  > key minted inside a privileged session would be a standing, unscoped, SCP-immune credential, which is
  > the invariant D16 states outright.
  >
  > **DONE 2026-08-13 on `Workloads`, `Data`, `Interactive` and `Identity` — all four with the parameter,
  > read back per OU.** `aws:AssumedRoot` is present in every document that carries `GRRESTRICTROOTUSER`,
  > which is the whole test, and the five OUs holding these controls are `Policy Test` plus those four.
  > **`Sandboxes` was deliberately left out** and is the rule stated below, not an omission.
  >
  > **The read-back found something the region half had hidden: Control Tower's packing is not consistent
  > across OUs.** The two root statements were folded into the *original* guardrail document on
  > `Policy Test`, `Workloads` and `Interactive`, but into the *`CT.MULTISERVICE.PV.1`* document on
  > `Identity` (`p-fw2pctqw`) and `Data` (`p-pk85fvr1`) — the same two ids the battery had recorded as
  > "the Region policy" for those OUs. **So a document cannot be identified by what it was created for**,
  > and a future amendment that reads "the region policy" by id will find root statements in it on two OUs
  > out of five. Read the `Sid` list; never infer it.
  >
  > **`Security` carries neither control**, having never been in 7.7's target list — it is foundational,
  > its guardrail is Control Tower's own, and `Log Archive` and `Audit` are consequently the two accounts
  > in the organization with no Region ceiling. Noted rather than fixed here: changing it is a Control Tower
  > operation on the OU that holds the log archive, which is Stage 1d's ground, not this step's.

#### 7.8 — RCPs, tag policies, declarative policies

- **RCPs** — deny access to **S3, STS, KMS, SQS, Secrets Manager, DynamoDB and ECR** from principals outside
  the organization (`aws:PrincipalOrgID`): the trusted-identities axis of `docs/plan/architecture.md` §4.2. One
  file, `awsds-org-rcp-perimeter.json`, on the organization root.
  **Seven services, not five — widened by the user on 2026-08-12.** The first five were the set RCPs
  launched with, and this plan had been carrying them as though they were the whole of what RCPs support.
  §4.2 carries the current shape and the standing instruction to read AWS's list rather than either copy.
  The two additions are not equivalent and the log should not record them as though they were:
  - **ECR is the load-bearing one, and it is the one with something to get wrong.** D14 puts the registry in
    Production and three integrations cross an account boundary to reach it: **INT-01** (the Studio custom
    image pulled into the Sandbox and Development domains), **INT-07** (Staging pulling the application
    image), and the replication rule that is INT-01's own fallback. **All of those are inside the
    organization, so `aws:PrincipalOrgID` admits them** — that is the whole point of keying on the
    organization rather than on an account list. What needs exercising is the **service** half, not the
    cross-account half: ECR performs pull-through cache fetches and replication writes itself, so those
    depend entirely on the `aws:PrincipalIsAWSService` carve-out below being present and correct. **Test a
    pull-through cache fetch and a cross-account pull after attaching**, not before — this is the same
    distinction between a service principal and a service-linked role that the next bullet calls "the entire
    bug", arriving in the one service this project actually pulls images with.
  - **DynamoDB is inert today and is adopted anyway.** **Correction to what was written here on 2026-08-12:
    this project has no DynamoDB table and no plan for one** — D3 settled Terraform state on native S3
    locking specifically to avoid the table, and the only DynamoDB in the plan is the free gateway endpoint
    of Stage 3 step 3. So this clause protects nothing at the moment it is attached. It is adopted on the
    same reasoning the GuardDuty denies in 7.5 are: **a deny that costs nothing and is already in place when
    the resource appears beats remembering to add it later** (Lesson 14). Record it in the log as *inert on
    attachment*, so a later reader does not mistake it for evidence that something was protected.

  **The mirror is now closed too, in the same sitting (user, 2026-08-12).** The RCP governs who from outside
  reaches *our* ECR; the opposite direction — one of our principals pushing an image to a registry outside
  the organization — is the **SCP** side, and 7.5's `aws:ResourceOrgID` write deny was S3-only until this
  change. It now names the four push actions as well, so **ECR is covered on both axes**, which no other
  service in this design is. **The carve-out risk that was flagged here did not survive checking**: a
  pull-through cache writes into your own registry, so the deny never evaluates against it — the reasoning
  is in 7.5, and it is recorded because an unnecessary carve-out is a hole, not a safety margin.

  **The other direction is already settled and is not a scope question:** EC2, RDS and EFS are outside RCP
  reach entirely, which is why the snapshot route is denied by SCP in 7.5. (EFS's lack of any preventive
  control stopped mattering on 2026-08-17: the NFS requirement was withdrawn, and no filesystem exists.)
  Three things that are not optional:
  - **The policy type must be enabled first** (7.2), and the organization must have all features on.
  - **The condition needs `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}` beside the
    `aws:PrincipalOrgID` test.** Without it the RCP denies AWS's own service principals reaching your
    resources — CloudTrail and Config writing to the Log Archive bucket being the two that break first,
    in the account whose whole job is to receive them. Service-*linked* roles are exempt from RCPs by
    construction; service principals are not, and that distinction is the entire bug.
    **A third one to check while attaching, because it did not exist when this bullet was written:** the
    organization IAM Access Analyzer in Audit (1b step 8.2) reads resource policies across every account
    under `access-analyzer.amazonaws.com`. It is covered by the same `IfExists` pair — confirm it is, by
    checking that the analyzer still reports `ACTIVE` and still produces a finding count after the
    attachment (`./aws/cloudshell/audit-iam-analyser.sh`), rather than by reading the JSON again.
  - **RCPs do not apply to the Management account at all**, so nothing here protects it and nothing here
    can lock it out. That is the same asymmetry D16 relies on.
- **Tag policies** — standardize the mandatory tags from `docs/plan/conventions.md`, with a precision the
  previous version of this plan got wrong: tag policies constrain *tagging operations*, they cannot force
  a resource to be created with tags at all. **The forcing function is an SCP with
  `aws:RequestTag`/`aws:TagKeys` conditions on the create actions that matter.** One or the other, or the
  tags are a convention — and conventions do not survive contact with a `terraform apply` at 23:00.

  > **The `Environment` value for Sandbox accounts — settled by the user, 2026-08-13: one value,
  > `sandbox`, for every business unit.** This closes the `Environment` half of
  > [`docs/plan/open-questions.md`](../open-questions.md) item 10. The alternative, `sandbox-<n>`, would split
  > cost reports by unit but would require editing an organization policy at every vend — and forgetting is
  > an `AccessDenied` on the first apply in a brand-new account, found by whoever is standing it up
  > (Lesson 14). **Per-unit cost attribution is by account**, which the bill already gives for free.
  > The enumeration is therefore `sandbox|development|data|staging|production|org`, exactly as
  > `docs/plan/conventions.md` writes it, with no ordinal anywhere. *(The other four per-unit tokens in item 10
  > are untouched by this — the profile keeps its ordinal, and the group token stays open.)*

  **The forcing SCP is a decision, not a formality, and it is the one policy in 7.5-7.8 that binds the
  builder as hard as it binds anyone** (Lesson 18 read forwards for once). Three things it breaks if it
  is written broadly:
  - **Resources whose create API takes no tags.** `aws:RequestTag` can only be satisfied by a call that
    carries tags; where the API does not accept them, a `Deny` on the create action is a deny full stop.
  - **Resources this project does not create.** D26's blueprints provision project buckets, Glue
    databases, Athena workgroups and execution roles into Sandbox and Development under DataZone's own
    provisioning roles — they will not carry `CostCenter=<stage>`, and the failure surfaces at Stage 6 as
    a project that will not create. **`CLAUDE.md`'s "S3 buckets built in the SMUS user interface" is
    exactly this case**, which is the newest reason to keep the scope narrow.
  - **The landing zone's own machinery**, which creates resources in every enrolled account.

  **So adopt it narrowly or not at all**, and adopt it *here*, in writing: the defensible scope is the
  handful of create actions whose cost this project actually attributes and **whose create API carries
  tags** — `ec2:RunInstances` (through `TagSpecifications`) and `rds:CreateDBInstance` — with
  `Environment` and `Project` as the required keys and nothing else, exempting the blueprint and Control
  Tower principals per 7.1's enumerated-ARN rule. It is **decision 5**, it is due while executing, and it
  is the one whose cost lands on a stage nobody is looking at yet.
  **`s3:CreateBucket` was on that list until 2026-08-09 and it contradicted the first bullet above.**
  S3 has historically had no tag parameter on `CreateBucket` — the AWS provider creates the bucket and
  calls `PutBucketTagging` afterwards — so an `aws:RequestTag` condition on it is not a tagging rule, it is
  a **blanket deny on creating buckets**, and the first thing it would have denied is Stage 2's own
  bootstrap. **Verify the current API before putting it back**; if `CreateBucket` does carry tags today,
  the second question is still whether the provider sends them on the create call, and the answer decides
  it. Until both are answered yes, S3 stays out of the scope.

  > **MEASURED 2026-08-13, and the first half of that instruction came back *yes* — the premise this
  > exclusion rested on is stale.** From the machine-readable service reference
  > (`servicereference.us-east-1.amazonaws.com/v1/s3/s3.json`), **`s3:CreateBucket` maps
  > `aws:RequestTag/${TagKey}` and `aws:TagKeys`** — one of 11 S3 actions that do. So the API carries tags
  > and the 2026-08-09 reasoning no longer holds. **The second half is still unanswered and it is the one
  > that decides**: whether Terraform's `aws` provider sends the tags *on the create call* or still calls
  > `PutBucketTagging` afterwards. If it is the latter, the condition is unsatisfiable from the tool this
  > project builds with and the deny lands on Stage 2's own bootstrap bucket. **Answer it at Stage 2, where
  > it is free** — look at what the provider actually sends — not from documentation here.
  >
  > **`ec2:RunInstances` could not be measured the same way, and the shape of the failure is the finding.**
  > The reference maps `aws:RequestTag` to **0 of EC2's 793 actions** while declaring the key in EC2's
  > top-level `ConditionKeys` list — so the instrument knows the service supports it and does not say
  > *where*. Compare S3 (11 of 180) and RDS (35 of 169), which map it per action. **A result that is
  > negative for every action of one service and positive for others is a gap in the instrument, not a fact
  > about the service** (Lesson 13) — do not read it as "`RunInstances` does not support tag-on-create".
  > **Settle it by probe instead, which is cheap and is what the canary is for:** `ec2:RunInstances
  > --dry-run` with and without `--tag-specifications` under the candidate policy gives the two-different-
  > errors shape the battery prefers, and it answers from the authorization engine rather than from a
  > document.
  >
  > **What this leaves decision 5 as**, stated so the scope is not re-derived: `rds:CreateDBInstance` is
  > confirmed supported but **inert** — this project has no RDS and no plan for one — so including it is
  > the DynamoDB argument from the RCP above, not a control. `s3:CreateBucket` is **blocked on the provider
  > question**. `ec2:RunInstances` is the only member of the scope that is both live (WireGuard, GitLab,
  > the runners) and answerable now. **So: write the forcing SCP for `ec2:RunInstances` alone, exercise
  > both directions on the canary, and revisit S3 at Stage 2.**
- **Declarative policies** — enforce IMDSv2 and EC2 public-access defaults org-wide. Policy type enabled
  in 7.2. One file, `awsds-org-declarative-ec2.json`.
  **Name what "public-access defaults" means, because the name hides the limit that matters (2026-08-12).**
  The two EC2 attributes worth setting here are **block public access for snapshots** and **block public
  access for AMIs** — separate settings, because the snapshot one explicitly does not cover EBS-backed AMIs.
  Snapshot BPA is free, and it is *account-level and Regional*: a declarative policy is the only way to apply
  it across accounts and Regions at once, and once it is applied that way the setting can no longer be
  changed from inside an account, which is the reason to use it rather than the console.
  **What it does not do is the half this project cares about: AWS states plainly that it does not prevent
  private snapshot sharing.** It blocks the *public* snapshot — the accident — and leaves sharing with a
  named outside account, the deliberate exfiltration, completely open. That route is closed by the SCP in
  7.5, and **the two are not substitutes**: attaching this one and reading the words "block public access"
  as coverage is exactly the shape of Lesson 5.

##### How 7.8 is attached and measured

**One document at a time, each measured before the next is touched.** The order, the instrument and the
staging are [`docs/plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md), phase 5; three things belong here
because they change what the documents above should say.

- **The battery gained three phases, one per probeable document** — `--phase tags`, `--phase rcp`,
  `--phase decl`. The tag policy has none and should not: it carries no `enforced_for`, refuses no call, and
  so offers nothing to attempt.
- **The RCP is attached to `Policy Test` first, not to the root.** `EnforceOrgIdentitiesOnRoleAssumption`
  covers `sts:AssumeRoleWithSAML` and `AssumeRoleWithWebIdentity`, where the caller has no AWS principal yet,
  so `aws:PrincipalOrgID` cannot populate and the `IfExists` form denies **unconditionally**. The staging
  costs one extra attach and bounds a lockout to one account; the repair either way is a detach from
  Management, which is exempt. **Its deny half is never probed** — an out-of-organization principal is an
  identity this project cannot produce (Lesson 22), so only the floor is measured and the runbook's
  read-instead table carries the four statements.
- **The declarative policy is measured by reading, with `./aws/declarative-ec2.py`**, because the battery can
  only show that a *change* is refused, never what the setting **is**. Its four probes deliberately carry no
  `--dry-run`: a declarative policy is enforced in the service's control plane, so a dry-run form returns
  `DryRunOperation` whether or not the policy is attached.

**Two before-readings taken 2026-08-14, and both change what the attach is expected to do:**

| Measurement | Result | What it means for the attach |
|---|---|---|
| `./aws/declarative-ec2.py`, five profiled accounts | `image_block_public_access` **already** `block-new-sharing` and `serial_console_access` **already** off, in all five | Two of the four attributes are a **lock**, not a change. Only `snapshot_block_public_access` (`unblocked` → blocked) and `instance_metadata_defaults.http_tokens` (`not-set` → `required`) actually move state |
| `ec2:RunInstances --dry-run` in `Development`, four tag forms | **all four** returned `DryRunOperation` | The tag SCP's before-reading. After the attach, the untagged and single-tag forms must read `DENY-SCP` and the fully tagged form must still read `DryRunOperation` — **a run where every row denies is the over-broad-`Resource` failure, not a strict pass** |

`organizations describe-effective-policy --policy-type DECLARATIVE_POLICY_EC2` answers **`{}`** with the type
enabled and nothing attached, rather than raising — so an empty object is the before-reading, not an error.

**Making `http_tokens: required` the account default is the one line here that can break a launch**, and it
lands before Stage 4's WireGuard host and Stage 7's GitLab. It is a *default*, not a ceiling —
`http_tokens_enforced` is deliberately unset — so a launch may still override it, which is what the
`decl` phase's last row records. Tightening that is the follow-up, after both stages have launched
successfully, and only then.

---

## Deliverables of 1c

Each one is written so that its output differs between working and broken (Lesson 13):

- **The perimeter's condition is real, in both services it now names:** the inverted-condition run from 7.3
  denied a write to a bucket **this organization owns**, with the error naming an explicit deny in a service
  control policy — proving that `aws:ResourceOrgID` populates and that the `IfExists` pair evaluates as
  written. **And the same inverted run denied `ecr:initiate-layer-upload` against a throwaway repository in
  `Policy Canary`** — a separate result, because key population is a property of each service's
  authorization and the bucket run is not evidence about ECR. An upload id instead of an `AccessDenied` is
  the finding, not a pass.
- **The BPA carve-out is real in both directions:** `s3control put-public-access-block` **fails** from
  `awsds-policy-canary` (which holds `AWSAdministratorAccess`, not the carved-out set) and **succeeds**
  from an `awsds-infra-*` profile — the pair that proves `aws:PrincipalArn` matched the IAM role ARN and
  not the `sts::assumed-role` form.
- **The ceiling is real in the other direction too:** `ec2:RunInstances --dry-run` in `us-east-1` returns
  `UnauthorizedOperation`, while the same call in `us-west-2` returns `DryRunOperation`.
- **Publication is closed, and closed by *this* policy:** `ecr-public:CreateRepository` from
  `awsds-policy-canary` fails, **run before 7.7**, with the CloudTrail `errorMessage` naming the baseline
  policy id — not the Region control's. Run after 7.7 the same failure proves nothing about this statement.
- **The snapshot route is closed, and closed by the thing that actually closes it:** a share attempt from
  `awsds-policy-canary` fails with an error naming an explicit deny in a service control policy — recorded
  together with the fact that the declarative policy's block-public-access setting was **not** what produced
  that failure, since it does not reach private sharing. The RDS half is recorded as **untested until an RDS
  exists**, which is a different sentence from "passed" and has to read that way in the log.
- **The widened RCP did not break the registry:** after `awsds-org-rcp-perimeter.json` is attached, a
  **pull-through cache fetch** and a **cross-account pull from the Production ECR** both still succeed — the
  two calls that depend on the `aws:PrincipalIsAWSService` carve-out reaching a service principal rather than
  a service-linked role. A failure here is the carve-out, not the organization condition, and the log should
  say which. The DynamoDB clause is recorded as **inert on attachment** — no table exists to test it against,
  and that sentence is the deliverable.
- **The baseline was read, not assumed — DONE 2026-08-13, except one line.** 7.0's output is in the log:
  org id, root id, every OU id and its path, the Control Tower SCP on each OU **with its policy id and its
  document**, the pre-existing BPA state per account, and the finding that **the policy quota is not
  published at all**. What is still owed is **the enabled-control list per OU**, which needs the Management
  run — and it is the deliverable 7.7 cannot start without.
- **Every attached policy ID is recorded** in `docs/log/log-stage-01c-preventive-policies.md`, beside the filename
  in `terraform-live/identity/org-policies/policies/`, which is what makes the detach command executable
  rather than aspirational — and what makes Stage 2 step 5.5's import land on an empty plan.

## Decisions

**Three of the landing zone's decisions were settled before execution, on 2026-08-13, so this stage no
longer opens with a blocking question.** They are recorded here rather than only in the chat that settled
them, and each one is still written into `docs/log/log-stage-01c-preventive-policies.md` at the moment it is applied
(Lesson 16):

| # | Decision | Settled as | Step |
|---|---|---|---|
| **1** | Whether the `Interactive` OU gets a policy set of its own | **Yes** — one statement: deny `sagemaker:CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl`. Adopted because SMUS uses spaces/apps, so it costs no feature and needs no carve-out | 7.6 |
| **6** | Which Region deny control is used | **`CT.MULTISERVICE.PV.1`, per OU.** `GRREGIONDENY` is not enabled; enabling both is what is hard to undo | 7.7 |
| **7** | Whether the `s3:PutAccountPublicAccessBlock` deny carries a carve-out | **Yes**, on the `InfrastructureAccess` Identity Center role — the one wildcard-account ARN in this design, argued in 7.4 | 7.4 / 7.5 |
| — | The `Environment` tag value for Sandbox units | **One shared value, `sandbox`.** Closes the `Environment` half of open question 10 | 7.8 |
| — | The perimeter RCP's service scope | **Seven, not five** — S3, STS, KMS, SQS, Secrets Manager plus **DynamoDB and ECR** (user, 2026-08-12). ECR is load-bearing and needs the service carve-out exercised; DynamoDB is inert on attachment and is recorded as such | 7.8 |
| — | The perimeter SCP's service scope | **S3 and ECR** (user, 2026-08-12) — four push actions, not `PutImage` alone, because the layers are the data. No carve-out: the pull-through cache writes in-org | 7.5 |
| — | Publication to ECR Public | **Denied outright**, `ecr-public:*` in the baseline (user, 2026-08-12). Anonymous gallery pulls are unaffected — no IAM action. Tested **before** 7.7, or the Region control makes the result ambiguous | 7.5 |
| — | Whether the baseline denies CloudTrail tampering | **No — and it is a decision, not an omission** (user, 2026-08-13, on the 7.0 finding that Control Tower denies nothing there). The trail is organization-level and lives in Management, which is SCP-exempt, so a member-account deny binds nothing reachable. **Revision trigger:** the first trail this project creates in a member account | 7.5 |

**One decision remains open and it is made while executing, not before:**

| # | Decision | Step | Reversible? |
|---|---|---|---|
| 5 | Whether the tag-forcing SCP is adopted, and over which create actions | 7.8 | Yes, but its cost lands at Stage 6 |

*The numbering is the landing zone's: decision 2 belongs to
[Stage 1b](stage-01b-identity-and-controls.md), 3, 4 and 8 to
[Stage 1d](stage-01d-org-wide-enablement.md).*

## Risks

- **This is the only irreversible-from-inside stage in the landing zone's second half.** A bad `Deny` has
  no in-account repair and the recovery path is a detach from the Management account (D16; D30 reverted).
  The `Policy Canary` battery and an already-open Management console are the mitigations, and both are
  procedures rather than properties — they only work if they are actually done.
- **The stage's real duration is Control Tower's, not the policies'.** 7.7 is a control operation per OU,
  serialized and minutes each, during which other landing-zone operations are blocked. Budget sitting B
  accordingly — running out of evening halfway through a battery is how a policy ends up attached and
  untested.
- **The size budget is small enough to hit, and 7.7 spends from it.** Each OU pays for Control Tower's own
  guardrails, this stage's tier, *and* the Region deny control. 7.0 step 5 counts; 7.1 carries the numbers.
- **A wildcard-account ARN now exists in this design.** It is one `Sid`, argued and bounded — but
  Stage 2 step 9.2's check has to know about it by name, or the check fails on the policy it protects.
- **Nothing here is torn down between sessions** — everything is `[P]` (D11).

## Verifications to answer while executing

Record every answer in `docs/log/log-stage-01c-preventive-policies.md`, including the ones that come out fine.
**The numerals are the landing zone's**, so they are not contiguous here.

**Three are already answered, on 2026-08-13, and they are kept here with their answers rather than deleted
— a verification whose answer is only in a log is one the next reader re-runs.**

| # | Question | Step | Answer |
|---|---|---|---|
| iii | Do the hand-written SCPs/RCPs conflict with, or merely duplicate, the SCPs Control Tower manages itself? | 7.0 step 2 | **Duplicate on Config, nothing on CloudTrail, nothing on GuardDuty.** No conflict found. 7.5 rewritten accordingly |
| x | Does the Organizations *policy* read surface answer from the Identity account? | 7.0 step 2 | **Yes**, all of it. 7.0 is a script (`aws/org-policy-baseline.py`) except for its `controltower` section |
| xi | Is a control enabled on `Interactive` inherited by the nested `Sandboxes` OU? | 7.7 | **Half-answered before it was asked:** `Sandboxes` carries no policy of its own at all, so the live question is now whether it is a registered target — 7.0 step 3 on Management |
| viii | Which namespace does each Unified Studio action evaluate under, asked of `Data` as well as of `Workloads`? | 7.6 | **The domain is `datazone:*`** — `datazone:CreateDomain` plus the two administrator-supplied roles, no `sagemaker:Create*` in the path — **so the `Data` wildcard stands and nothing is widened.** `sagemaker:*` appears in the account a *project profile* targets, which D26 keeps out of Data Governance. `CreateSpace`, `CreateApp` and `StartSession` are all real names today, read off AWS's machine-readable action list. The table in 7.6 carries the whole answer |
| xii | Does `ec2:modify-snapshot-attribute --dry-run` evaluate permissions before validating the snapshot id? | 7.3 / 7.5 | **No** — an invented id is rejected as `InvalidSnapshotID.Malformed` before authorization, `--dry-run` included, so no fake-id probe reaches the SCP. The statement is left exercised only through its AMI sibling, and [`docs/plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md) records why that was accepted |

**Still open**, with (xi) carried forward as the sharper question it became:

| # | Question | Step |
|---|---|---|
| vii | **Answered 2026-08-13, and better than asked.** The control lands as an ordinary SCP, so the list was read from the **attached document** (`aws-guardrails-njKkvb`, `p-q3y11w1n`) rather than from the `Artifacts` tab — repeatable per OU and diffable. **86 entries, no `ExemptedActions` of ours, and every global prefix this project calls is present**, `route53domains` and the three S3 account-level actions included. It also **falsified one of this stage's own predictions**: `ecr-public:*` is exempt, so the Region control never denied it and `DenyEcrPublicEntirely` is the only thing that does | 7.7, done |
| xi | **ANSWERED IN BOTH HALVES, 2026-08-13.** SCP half (7.6): `Interactive`'s document denies `sagemaker:CreateNotebookInstance` in `awsds-infra-sandbox-1`, so the nested OU is governed by inheritance. Registered-target half (7.7): **`enable-control` against `Sandboxes` was accepted**, and the OU now carries `aws-guardrails-yvYgxw` (`p-h7lc62d0`) — **the first policy that OU has ever held**. So it is *both*: a registered target and a beneficiary of inheritance. **The probe cannot tell you that, and this is the sharpest instance of Lesson 20 in the stage:** the `us-east-1` deny in Sandbox Account 1 names `p-umksvu5a`, `Interactive`'s Region policy — not `Sandboxes`' own. Two policies deny the call, AWS names one, and the *inherited* one won. Attribution answered the question about coverage and said nothing about registration; only the OU's attached-policy list did. **For Stage 14 this is the useful form: a nested OU can carry its own controls, and does not need to in order to be governed** | 7.7, done |

**Was (vii), now answered from the documentation rather than by execution:** *"is Region deny
landing-zone-wide, i.e. untestable against `Policy Test` first?"* — **the landing-zone control
`GRREGIONDENY` is; the OU-scoped `CT.MULTISERVICE.PV.1` is not, and can be canary-tested.** Decision 6
replaces the question.

---

*Stage index: [docs/plan/stages/INDEX.md](INDEX.md) · Previous: [Stage 1b](stage-01b-identity-and-controls.md) · Next: [Stage 1d](stage-01d-org-wide-enablement.md)*
