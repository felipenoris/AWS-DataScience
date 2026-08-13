# `probes/` — the SCP battery, executable

**The reasoning is [`plan/runbooks/scp-battery.md`](../../plan/runbooks/scp-battery.md); this folder is the
same battery as a program.** The runbook says *why* each probe is shaped the way it is and what each
outcome means. The script runs them, classifies the answers and reports. Read the runbook once; run the
script every time.

```bash
./aws/probes/scp-battery.sh              # read-back, then every phase
./aws/probes/scp-battery.sh --phase ou   # one phase: root | ou | region
./aws/probes/scp-battery.sh --list       # what would run, and in which account
```

| File | What it is |
|---|---|
| `scp-battery.sh` | The driver: sessions, real-id resolution, classification, report, exit code |
| `probes.sh` | **The battery itself, as data.** Amending the ceiling means editing this file and nothing else |
| `readback.py` | Compares the SCPs *attached in the organization* against the documents in `terraform-live/identity/org-policies/policies/`, before any probe runs |

## The one folder under `aws/` that is not read-only

`CLAUDE.md` says every script under `aws/*` performs **only read-only operations**, which is what makes
those scripts safe to run without asking. **These are not read-only**, and the exception is written into
that rule rather than left to be discovered: a preventive control can only be measured by attempting the
thing it prevents, so the battery calls write actions on purpose. It reaches authorization and leaves
`AccessDenied` events in CloudTrail.

**Nothing is created, and that is a declared field rather than a promise** — see the safety classes below.
The practical difference from its neighbours in `aws/`: those are run to gather information, this one is
run deliberately, when a policy has just been attached or amended.

## The seam: the script measures, the human attaches

**`scp-battery.sh` never creates, updates, attaches or detaches a policy.** Policy changes are made by
hand in the Management console, as `AWS Control Tower Admin`; the script only measures what the attached
ceiling does. That separation is deliberate: a tool that could both change the ceiling and report on it
would be able to report on a ceiling it had just changed, and this project's whole preventive layer rests
on the report being independent of the change.

## What a run looks like

```
ok   ou   data   deny   DENY-SCP   p-gl01bcdm   data: ec2:CreateFleet (7.6a)
ok   ou   identity allow ALLOWED   reached-authorization   identity: glue:StartCrawler is ALLOWED here
FAIL region canary deny ALLOWED    dry-run      region: ec2:RunInstances in us-east-1 must be denied
```

Four outcomes, and the distinctions are the point:

| Outcome | Means |
|---|---|
| `DENY-SCP` | An explicit deny in a **service control policy**, and the detail column is the policy id the API named — attribution without CloudTrail. **AWS names one policy even when several deny**, so a document that appears in no row is attached but unexercised (Lesson 20) |
| `DENY-NOT-SCP` | `AccessDenied` naming **no** policy — an IAM or permission-set deny. It answers a different question from the one being asked, and it is never counted as the ceiling working |
| `ALLOWED` | `DryRunOperation`, an exit code of 0, or the wording that proves *this action* reached authorization — declared per probe, because "the service validates first" is a property of the action, not of the service (Lesson 21) |
| `UNTESTED` | The call never reached authorization. **Not a pass and not a failure** — a probe that needs a better input, usually a real id |

`FAIL` marks a row whose outcome contradicts its expectation, in either direction: a `deny` that came back
`ALLOWED` is a hole in the ceiling; an `allow` that came back denied is the ceiling reaching something it
should not. Either exits 1. **A dead SSO session exits 2 and records nothing** — it makes every probe read
exactly like a deny, which happened twice in one hand-run sitting and is the single most expensive way to
misread this battery.

The report lands in `aws/output/scp-battery-<stamp>.txt`, untracked, with account ids masked.

## Amending the battery

Add the probe next to its statement's siblings in `probes.sh`:

```bash
probe <phase> <account> <expect> <allowed-regex|-> <flags|-> <label> -- <aws args...>
```

- **`expect`** — `deny` (the ceiling must stop it) or `allow` (a cross-check, or the must-still-succeed
  floor). The floor is not decoration: it is the half that composition can only make stricter, so a
  failure there is real no matter which document caused it.
- **`allowed-regex`** — the wording that proves this action reached authorization
  (`EntityNotFoundException`, `ValidationException`, …). Omit it with `-` and anything that is not a deny
  is reported `UNTESTED` rather than assumed allowed. **Getting this field wrong is the one way to make
  the script lie**, and it lies in the flattering direction.
- **`flags`** — `creates` for a creation-shaped probe with no `--dry-run`. The driver **refuses to run
  those outside `Policy Canary`**; give it a `--dry-run` form or leave it on the canary.
- **`@AMI@`, `@SUBNET@`, `@ACCT@`** are substituted with real ids read from the account being probed.
  Use them wherever an invented id would be rejected before authorization.

Then run the script. A new statement that produces no `DENY-SCP` row naming its policy is attached and
unexercised — which is the state this battery exists to make visible.

---

*Runbook: [`plan/runbooks/scp-battery.md`](../../plan/runbooks/scp-battery.md) ·
Documents: [`terraform-live/identity/org-policies/`](../../terraform-live/identity/org-policies/README.md) ·
Statements: [`SCPs.md`](../../terraform-live/identity/org-policies/SCPs.md)*
