# Stage 1c — Preventive policies: SCP, RCP, tag and declarative

| | |
|---|---|
| **Status** | not started — **every prerequisite is met** (revised 2026-08-13) |
| **Prerequisites** | **[Stage 1b](stage-01b-identity-and-controls.md) is complete** (closed 2026-08-12; its log is authoritative). What this stage actually consumes from it: the six SSO profiles of step 5 — `awsds-infra-sandbox-1`, `-dev`, `-prod`, `-data`, `-identity` and **`awsds-policy-canary`** — and an administrator principal in the canary account (1b step 3.1). **Not its permission sets**: no policy written here names one, which is why the `Consumes` row carries no persona decision. `Staging` is unvended, so nothing in the `Workloads` tier can be exercised against it |
| **Consumes** | [D6](../decisions/D06-dlp-approach.md), [D10](../decisions/D10-identity-center-delegation.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D28](../decisions/D28-workflow-contract.md), [D29](../decisions/D29-policy-canary.md), [D30](../decisions/D30-scp-recovery.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | **Constrains** [INT-12](../integrations.md), whose fallback 7.6 forbids until the policy is amended. **Touches [INT-01](../integrations.md) and [INT-07](../integrations.md)**: the perimeter RCP now covers ECR, so both cross-account image paths run through its service carve-out — admitted by `aws:PrincipalOrgID`, but only exercised in 7.8 |
| **Log** | `log/stage-01c-preventive-policies.md` — **create it before starting**; the policy IDs recorded there are what makes the detach command executable |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

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
| **A** | 7.0 (preflight), 7.2 (policy types), 7.4 step 1 (account-level BPA everywhere), 7.5 (the organization-root set) | The root set attached and exercised |
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

   Record the ID of every policy **as you attach it**, in `log/stage-01c-preventive-policies.md`. Reading
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
| **Only `SERVICE_CONTROL_POLICY` is `ENABLED` on the root** — measured 2026-08-11, `aws/list-identities.sh` §2.2 | 7.2 precondition 1 is confirmed, not assumed. All three other types still have to be enabled, and half of this stage has nowhere to attach until they are |
| **The six SSO profiles all resolve**, and `awsds-policy-canary` is bound to `AWSAdministratorAccess` **permanently** (1b 3.1, 5, 5.1) | The canary has a profile of its own: 7.4's BPA call there is a CLI call like the other five, not a console visit. The battery runs from the laptop |
| **The Organizations *read* surface answers from the Identity account** (1b step 4 and `aws/org-trusted-access-services.sh`, 2026-08-12) | 7.0's preflight reads can run under `awsds-infra-identity` without touching Management. **Writes cannot** — every `create-policy`, `attach-policy` and `enable-policy-type` here is CT Admin on Management |
| **A permission set provisioned into Management cannot be altered from Identity** (1b 5.1) | Nothing in this stage alters a permission set — stated so it is not re-discovered. It does mean that if a policy attached here breaks `awsds-policy-canary`, the repair is CT Admin on Management, not the Identity profile |
| **`AWSOrganizationsFullAccess` → `AWSControlTowerAdmins` reaches every vended account** (measured 2026-08-11; `AWS_STATE.md` A.1) | 7.5's `organizations:LeaveOrganization` deny stops being hygiene and becomes the answer to a measured path. Its reach is [`plan/open-questions.md`](../open-questions.md) item 11, and this stage is where it gets answered |
| **`CLAUDE.md` now names six SageMaker Unified Studio features as objectives** (2026-08-13) | 7.6 settles decision 1 **against the verified API surface** rather than against the feature names, and verification (viii) becomes a named list of actions instead of a question. See the box in 7.6 |

One thing that is *not* a change and is listed so it is not read as one: **`EXC-01`** — the `SUSPENDED`
account named `Sandbox` sitting directly on the organization root ([`AWS_STATE.md`](../../AWS_STATE.md)).
It is not this project's, it runs nothing, and **it is not in any list in this stage**: no BPA, no profile,
no attachment. A suspended account cannot be acted on anyway.

## The stage at a glance

| # | What | Identity | Sitting |
|---|---|---|---|
| 7.0 | **Preflight — measure the ground before writing a line of JSON** | Infra user (`awsds-infra-identity`) + CT Admin @ Management | A |
| 7.1 | What makes this step different, and the two rules that survive from D30 | — (read first) | both |
| 7.2 | Preconditions, in this order | CT Admin @ Management | A |
| 7.3 | The battery, against `Policy Canary` before anything real (D29) | Infra user, laptop (`awsds-policy-canary`) | both — it runs per policy |
| 7.4 | The order of attachment — an instruction, not a listing order | CT Admin @ Management; step 1 of 7.4 also in each member account | A |
| 7.5 | The organization-root SCP set | CT Admin @ Management | A |
| 7.6 | The per-OU sets, one tier per OU policy set (D23) | CT Admin @ Management | B |
| 7.7 | The Control Tower managed controls — use theirs | CT Admin @ Management | B |
| 7.8 | RCPs, tag policies, declarative policies | CT Admin @ Management | B |

## Who executes what

| Part | Identity | Sign-in path |
|---|---|---|
| Policy-type enablement, org-root attachments, per-OU attachments, managed controls (7.2, 7.4-7.8) | **`AWS Control Tower Admin`** (D33/D34) | access portal → `AWSAdministratorAccess` on **Management** |
| 7.4 step 1 — account-level BPA on Log Archive and Audit | **`AWS Control Tower Admin`** | access portal → `AWSAdministratorAccess` on **Log Archive** / **Audit**. Both are reachable: `AWSControlTowerAdmins` carries `AWSAdministratorAccess` on each (`AWS_STATE.md` A.1, measured) |
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
attached. Collect all of it in one pass, into `log/stage-01c-preventive-policies.md`, before the first
`create-policy`.

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

**Expect `aws-guardrails-*` policies on every registered OU, and expect them to already deny what 7.5's
second bullet was going to write by hand** — Control Tower's *mandatory* controls include "disallow changes
to CloudTrail" and "disallow changes to AWS Config" and are applied to every registered OU without being
asked for. Read the documents (`aws organizations describe-policy --policy-id <p-xxxx>`), and **write only
the gap.** Two consequences, and both are the point of doing this first:

- A hand-written deny that duplicates a Control Tower one costs SCP budget and adds a second place to get
  the carve-outs wrong — and Control Tower's carve-outs (`AWSControlTowerExecution`,
  `aws-controltower-ConfigRecorderRole`) are the ones that keep the landing zone able to update itself.
- If a policy read is denied from the Identity profile, that is information rather than a failure: the read
  surface 1b measured did not include the policy calls. **Re-run it from CloudShell on Management as CT
  Admin** and record which way it went — it is the honest answer to whether 7.0 can ever be a script.

**3. What each OU's control baseline already is**, from Management as CT Admin — and the same command is
7.7's registration check, which is why it is collected once:

```bash
aws controltower list-enabled-controls --target-identifier <ou-arn> --query 'enabledControls[].[controlIdentifier,statusSummary.status]' --output table
```

**An unregistered target errors rather than returning an empty list**, and that distinction is the check
(Lesson 13). Registration is *expected* for all six non-foundational OUs — every one of them received an
Account Factory vend (1a log) and Account Factory only offers registered OUs — but expected is not
measured. Record the result per OU; 7.7 may not enable a control on an OU this call rejected.

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

**5. The quota that decides whether the set fits.** The policy count per node is the constraint 7.1
describes, and it is worth reading rather than remembering — Organizations quotas answer in `us-east-1`:

```bash
aws service-quotas list-service-quotas --service-code organizations --region us-east-1 \
  --query 'Quotas[?contains(QuotaName, `policies`)].[QuotaName,Value]' --output table
```

**Count the slots before writing, per node, and remember that 7.7 consumes one more on every OU it
touches:** the OU-scoped Region deny is implemented as an SCP that Control Tower attaches. An OU that fits
today and not after 7.7 is the failure this count exists to prevent.

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
- **Write each document as a file *before* pasting it, and keep the file.** Put it in
  `terraform-live/identity/org-policies/policies/<name>.json` — the folder does not exist yet and creating
  it early costs nothing — paste those exact bytes into the console, and record the returned policy ID
  beside the filename in `log/stage-01c-preventive-policies.md`. Two things come free: the detach command
  above becomes executable (you have the ID), and **Stage 2 step 5.5's import compares a document against
  itself** instead of against a re-typing, which is the difference between an empty plan and an evening
  spent on JSON whitespace.
- **Any ARN condition uses an enumerated list, never a wildcard account** — `arn:aws:iam::*:role/x` means
  "anyone who can create a role named `x`, anywhere". **One exception is adopted here, deliberately and
  once:** the BPA carve-out of 7.4/7.5, whose whole purpose is to reach accounts that do not exist yet and
  whose Identity Center role suffix is therefore unknowable. It is argued where it is used, not here, and
  `plan/conventions.md` carries the rule it bends.
- **There is a size budget, and it is small enough to hit.** AWS Organizations caps how many policies
  attach to one node and how large each is — **10 SCPs per node and 10 240 characters** since the May 2026
  increase, but **RCPs are still 5 per node and 5 120 characters**; 7.0 step 5 measures both rather than
  trusting this line. Control Tower's own guardrails consume part of the SCP allowance at every OU it
  registers, **and 7.7 consumes one more slot per OU**. The organization root is asked to carry three
  documents (7.5's two plus 7.8's tag-forcing SCP) and 7.8's RCP covers five services in one document.
  **Count before writing, and prefer one well-`Sid`-ed policy per node to several thin ones** — a policy
  that will not attach is discovered at the end of the work rather than at the start.
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
  `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}` — then attempt a write to a bucket you *do*
  own from `awsds-policy-canary`. It must fail, and the error must name an explicit deny in a service
  control policy. That proves the three things worth proving: the key populates, the `IfExists` pair
  evaluates the way it reads, and the deny reaches an ordinary principal. Detach it, then attach the real
  statement — whose only difference is the direction of the comparison. Record both outcomes.
  **The bucket to write to is a throwaway created in the canary itself, and deleted in the same sitting.**
  That is the one exception to "nothing is ever created in `Policy Canary`" (`plan/conventions.md`), and it
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
- **Two verifications ride along** (`plan/open-questions.md` item 10): whether the **IAM Policy
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
   be a list, or the one account nobody had a profile for is the one that keeps the hole. **Measure first
   (7.0 step 4)**, then set only what is unset:
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
   > `plan/conventions.md`'s enumerated-ARN rule gains one named exception instead of quietly acquiring a
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
| `awsds-org-scp-baseline.json` | organization root | `LeaveOrganization`, IAM-user denies, the BPA deny with its carve-out, the snapshot/AMI sharing deny, the `ecr-public:*` deny, `datazone:CreateDomain` with the `Data` carve-out, and whatever of the CloudTrail/Config/GuardDuty denies 7.0 step 2 shows Control Tower is *not* already doing |
| `awsds-org-scp-perimeter.json` | organization root | the `aws:ResourceOrgID` write deny — **S3 and ECR**, alone |
| `awsds-org-scp-require-tags.json` | organization root | 7.8's tag-forcing SCP — written last, because its scope is decision 5 |

- **Deny `organizations:LeaveOrganization` — not hygiene: a real principal can call it, and it is now
  measured rather than reasoned.** Every vended account carries `AWSOrganizationsFullAccess` →
  `AWSControlTowerAdmins` (`AWS_STATE.md` A.1, measured 2026-08-11), a group whose one member is the
  Control Tower admin user. This is one of the few Organizations calls a *member* account can make, and one
  call drops every SCP and every Control Tower control for that account.
  **While you are here, answer [`plan/open-questions.md`](../open-questions.md) item 11**, which has been
  waiting for exactly this session: assume that permission set in one vended account and run the
  Organizations reads plus one harmless write. Whether anything *else* in that managed policy needs denying
  is the open half, and it costs minutes now versus a re-derivation later.
- **CloudTrail, Config and GuardDuty: write only the gap.** The old text said "deny disabling CloudTrail,
  Config and GuardDuty" as though none of it existed. Control Tower's mandatory controls already deny
  changes to the trail and to the Config recorder on every registered OU, with the service-role carve-outs
  that keep the landing zone able to update itself — **7.0 step 2 is what turns that expectation into a
  reading.** What is *not* covered is **GuardDuty**, which Control Tower does not manage here, so
  `guardduty:DeleteDetector`, `guardduty:DisassociateFromMasterAccount`, `guardduty:UpdateDetector` and
  `guardduty:DeleteMembers` belong in `awsds-org-scp-baseline`. They are inert until Stage 4 turns
  GuardDuty on, and that is the correct order under principle 9 rather than an oversight.
  *(Considered and deliberately not adopted: a deny on `access-analyzer:DeleteAnalyzer`, protecting the
  organization analyzer 1b step 8.2 created in Audit. The analyzer is re-creatable in one call and its
  deletion is a management event the trail records; the deny would bind the Audit administrator, which is
  the identity that would legitimately re-create it. Recorded so it reads as a choice.)*
- **Deny writes to S3 and ECR resources outside this organization** (`aws:ResourceOrgID`) — the
  trusted-resources axis of `plan/architecture.md` §4.2, and the most direct exfiltration route a notebook
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
  - **`ecr:GetAuthorizationToken` is deliberately not in the list.** It is registry-scoped and carries no
    resource, so `aws:ResourceOrgID` never populates for it and an `IfExists` deny would either miss it or
    catch everything. Authenticating against an outside registry is harmless on its own; the write is the
    event, and the write is covered.
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
  (`plan/architecture.md` §4.2), which is exactly why this is an SCP, here, and not part of 7.8's perimeter
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
  - **It overlaps the Region control, and the overlap is the reason to write it rather than a reason not
    to.** ECR Public is a `us-east-1`-only API, so `CT.MULTISERVICE.PV.1` (7.7) very likely denies it
    already — as a **side effect** of an exemption list AWS maintains and changes, which is what
    verification (vii) exists to re-read. That is a deny by accident: it states no intent, and it silently
    disappears the day `ecr-public` is added to the `NotAction` list. **This is not the CloudTrail/Config
    case above** — there the duplication was of a Control Tower control with the *same* intent, and the
    instruction was to write only the gap. Here a different control catches the action for a different
    reason, and one statement is the cost of not depending on that.
  - **Test it in the 7.5 window, before 7.7 enables the Region control**, or the result is ambiguous: after
    7.7 an `ecr-public:CreateRepository` from `awsds-policy-canary` fails under *either* policy and the CLI
    error cannot tell you which (Lesson 13). Run it here, and record the policy id from the CloudTrail
    `errorMessage`.
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
  `plan/conventions.md` carries the exclusion so it is not only in this paragraph.
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
  foundational OU (1a log), so the account sits in a sibling OU — and **an OU created outside Control
  Tower's own flow carries no policy set until code attaches one** (D34). Two things, in this order:
  - **Establish the baseline before writing anything.** 7.0 step 3 already listed the controls enabled on
    every OU: diff `Security` against `Identity`. **The expected difference is small and knowing that
    saves an hour** — Control Tower's *mandatory* controls reach every registered OU, so what `Security`
    has extra is the foundational set about the log-archive and audit buckets, most of which means nothing
    for an account that holds neither. Enable the equivalent elective controls on `Identity` where they
    exist and where they apply. **Record the diff in `log/stage-01c-preventive-policies.md`** — "it used to
    inherit that" is not a control (Lesson 5), and neither is "it probably inherits it".
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
[`plan/open-questions.md`](../open-questions.md) items 12-14.

#### 7.7 — The Control Tower managed controls: use theirs, do not hand-roll these two

**Before anything in this subsection: 7.0 step 3 must have returned a control list for every target OU.**
A managed control can only be enabled on a *registered* OU, and an unregistered target **errors rather than
returning an empty list** — which reads like a permissions problem and is not. Registration is expected for
all six (each received an Account Factory vend, and Account Factory only offers registered OUs), but D29's
whole battery assumes `Policy Test` is registered, and an unregistered OU has no control baseline, so a
test against it would measure something else.

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
  `ce:GetCostAndUsage`. Only then enable it on `Interactive`, `Sandboxes`, `Workloads`, `Data` and
  `Identity`. **`Sandboxes` is on that list on purpose:** it is a separate registered OU, and a control
  enabled on `Interactive` is not automatically enabled on a nested child — verify that against the first
  one you enable rather than assuming it either way, and record which it was.

  **Two facts to have before you start.** The home region cannot be denied, and *nothing must already
  exist in the regions being denied* — trivially true here, and it is the reason to do this now rather
  than at Stage 12. The control is reversible from the Control Tower console.

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

#### 7.8 — RCPs, tag policies, declarative policies

- **RCPs** — deny access to **S3, STS, KMS, SQS, Secrets Manager, DynamoDB and ECR** from principals outside
  the organization (`aws:PrincipalOrgID`): the trusted-identities axis of `plan/architecture.md` §4.2. One
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
  reach entirely, which is why the snapshot route is denied by SCP in 7.5 and why EFS has no preventive
  control at all.
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
    attachment (`./aws/audit-iam-analyser.sh`), rather than by reading the JSON again.
  - **RCPs do not apply to the Management account at all**, so nothing here protects it and nothing here
    can lock it out. That is the same asymmetry D16 relies on.
- **Tag policies** — standardize the mandatory tags from `plan/conventions.md`, with a precision the
  previous version of this plan got wrong: tag policies constrain *tagging operations*, they cannot force
  a resource to be created with tags at all. **The forcing function is an SCP with
  `aws:RequestTag`/`aws:TagKeys` conditions on the create actions that matter.** One or the other, or the
  tags are a convention — and conventions do not survive contact with a `terraform apply` at 23:00.

  > **The `Environment` value for Sandbox accounts — settled by the user, 2026-08-13: one value,
  > `sandbox`, for every business unit.** This closes the `Environment` half of
  > [`plan/open-questions.md`](../open-questions.md) item 10. The alternative, `sandbox-<n>`, would split
  > cost reports by unit but would require editing an organization policy at every vend — and forgetting is
  > an `AccessDenied` on the first apply in a brand-new account, found by whoever is standing it up
  > (Lesson 14). **Per-unit cost attribution is by account**, which the bill already gives for free.
  > The enumeration is therefore `sandbox|development|data|staging|production|org`, exactly as
  > `plan/conventions.md` writes it, with no ordinal anywhere. *(The other four per-unit tokens in item 10
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
- **The baseline was read, not assumed:** 7.0's output is in the log — org id, root id, every OU id and
  ARN, the Control Tower SCPs already on each OU, the enabled-control list per OU, the pre-existing BPA
  state per account, and the measured policy quota.
- **Every attached policy ID is recorded** in `log/stage-01c-preventive-policies.md`, beside the filename
  in `terraform-live/identity/org-policies/policies/`, which is what makes the detach command executable
  rather than aspirational — and what makes Stage 2 step 5.5's import land on an empty plan.

## Decisions

**Three of the landing zone's decisions were settled before execution, on 2026-08-13, so this stage no
longer opens with a blocking question.** They are recorded here rather than only in the chat that settled
them, and each one is still written into `log/stage-01c-preventive-policies.md` at the moment it is applied
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

Record every answer in `log/stage-01c-preventive-policies.md`, including the ones that come out fine.
**The numerals are the landing zone's**, so they are not contiguous here.

| # | Question | Step |
|---|---|---|
| iii | Do the hand-written SCPs/RCPs conflict with, or merely duplicate, the SCPs Control Tower manages itself? **Read before writing** | 7.0 step 2 |
| vii | Does `CT.MULTISERVICE.PV.1`'s current default `NotAction` still cover everything this project calls from `us-east-1`? Read it off the control's `Artifacts` tab and diff | 7.7 |
| viii | Which namespace does each Unified Studio action evaluate under — `datazone:*`, `sagemaker:*`, `glue:*`, `athena:*` or `bedrock:*`? **Ask it of the `Data` OU as well as of `Workloads`**, and settle in particular whether `sagemaker:StartSession` and `sagemaker:CreateSpace` are the right names today | 7.6 |
| x | **New.** Does the Organizations *policy* read surface (`ListPolicies`, `ListPoliciesForTarget`, `DescribePolicy`) answer from the Identity account, or only from Management? Decides whether 7.0 can ever become a script in `aws/` | 7.0 step 2 |
| xi | **New.** Is a Control Tower control enabled on `Interactive` inherited by the nested `Sandboxes` OU, or does `Sandboxes` need its own enablement? | 7.7 |
| xii | **New.** Does `ec2:modify-snapshot-attribute --dry-run` evaluate permissions *before* validating the snapshot id? If it does, the snapshot deny is testable without creating anything and the battery's planned-cleanup exception is not needed for it | 7.3 / 7.5 |

**Was (vii), now answered from the documentation rather than by execution:** *"is Region deny
landing-zone-wide, i.e. untestable against `Policy Test` first?"* — **the landing-zone control
`GRREGIONDENY` is; the OU-scoped `CT.MULTISERVICE.PV.1` is not, and can be canary-tested.** Decision 6
replaces the question.

---

*Stage index: [plan/stages/INDEX.md](INDEX.md) · Previous: [Stage 1b](stage-01b-identity-and-controls.md) · Next: [Stage 1d](stage-01d-org-wide-enablement.md)*
