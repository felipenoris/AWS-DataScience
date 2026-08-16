# `aws/` — index

**Read-only scripts that photograph what is actually deployed in AWS, and the text snapshots they
produce.** Nothing here creates, changes or deletes a resource, and nothing here is infrastructure code —
that is `terraform-live/` from Stage 2 on.

Why this exists: [`docs/GENERAL_PLAN.md`](../docs/GENERAL_PLAN.md) and `docs/plan/` say what *should* be there, the
[`docs/log/`](../docs/log/INDEX.md) files say what was *done by hand*, and these snapshots say what AWS *reports right
now*. Each answers a different question, and the three disagreeing is itself information.

**One subfolder is the exception to the sentence above, and it is fenced rather than hidden:
[`probes/`](probes/README.md).** The SCP battery has to *attempt* the calls a policy forbids — that is the
only way to measure a preventive control — so it reaches authorization and leaves `AccessDenied` events in
CloudTrail. It still creates nothing: every probe is read-only, carries `--dry-run`, or names a prerequisite
that does not exist, and the three that would really act if a deny were missing are refused by the driver
anywhere but `Policy Canary`. **The difference that matters for this index: the scripts above are safe to
run to gather information; the battery is run deliberately.** Its reports land in `output/` alongside these
snapshots.

## The scripts

| Script | SSO user signed in | Profile it runs as | Writes | Captures |
|---|---|---|---|---|
| [`list-identities.py`](list-identities.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | `awsds-infra-identity` (Identity account, IAM Identity Center delegated administrator — D10) | `output/list-identities.txt` | The Organization: **organization id** — the value `aws:PrincipalOrgID` and `aws:ResourceOrgID` are compared against — management account id, root and its enabled policy types, the whole OU tree, every account. The directory: Identity Store instance, groups, users, group memberships. The entitlements: permission sets with what each grants, and every assignment triple. |
| [`AZs.py`](AZs.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) — including behind `awsds-policy-canary`, which is the **same human** through a different permission set (D32) | **every** `awsds-*` profile in `~/.aws/config`, or the ones named as arguments — the one script here that is not single-profile, see below | `output/AZs.txt` | The availability-zone **name → zone ID** mapping each account reports, one listing per account, the mappings side by side, and a check on whether they agree. |
| [`org-trusted-access-services.py`](org-trusted-access-services.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; takes another profile as its argument, or `-` to run with no profile at all — inside CloudShell on Management | `output/org-trusted-access-services.txt` | Which AWS services hold **trusted access** across the organization, which account is each one's **delegated administrator**, and the `access-analyzer` registration on its own. |
| [`cloudshell/audit-iam-analyser.sh`](cloudshell/audit-iam-analyser.sh) | [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) — **the only one**, no laptop path | **no profile — CloudShell on the Audit account**, as `AWS Control Tower Admin`. Takes a profile as its argument if one ever exists there; see below | `output/cloudshell/audit-iam-analyser.txt` | The IAM Access Analyzer analyzers of that account and Region: type (the **zone of trust**), status, tags, archive rules, findings — and a check that there is exactly one, `ORGANIZATION`, `ACTIVE`. |
| [`org-policy-baseline.py`](org-policy-baseline.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) — **open, and what section 7 answers**; [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback, which section 5 is expected to need anyway | `awsds-infra-identity` by default; takes another profile, or `-` for CloudShell on **Management** as `AWS Control Tower Admin` — which is the fallback if the policy reads are denied | `output/org-policy-baseline.txt` | **The ceiling that already exists.** Organization id and feature set, the root and its enabled policy types, every node with its **id, ARN and full path**, the policies attached per node per type, the **documents** of the ones found, the Control Tower controls enabled per node, and the policy quota. Stage 1c step 7.0 steps 1, 2, 3 and 5 in one pass. |
| [`org-policies.py`](org-policies.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; takes another profile, or `-` for CloudShell on **Management** | `output/org-policies.txt` | **What governs each node right now, by `Sid`** — no document bodies. Attached per node condensed to its statement names; **what governs each *account* once inheritance is resolved**; the **read-only checks** that no probe can reach; and a per-OU ceiling table. **Exits 2 when a check fails**, so it can gate a change. **Gap found and fixed the same day (2026-08-15):** section 1 used to list ids for `SERVICE_CONTROL_POLICY` only, leaving three of the ten attached documents with no id in any snapshot (the [1c log](../docs/log/log-stage-01c-preventive-policies.md) alone carried them). **All four policy types now carry their ids** — which is what [Stage 2](../docs/plan/stages/stage-02-terraform-foundation.md) step 5.5 needs, where an id is an argument |
| [`account-bpa.py`](account-bpa.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for the `-` runs in Management, Log Archive and Audit | **every** `awsds-*` profile, or the ones named as arguments, or `-` inside CloudShell for the three accounts that have no profile — the second script here that is not single-profile, see below | `output/account-bpa.txt` | The **account-level** S3 Block Public Access configuration of each account, the four flags side by side, and which accounts nothing is measuring. Read three times: before 7.4, after 7.4 and before 7.5, and at every vend. |
| [`declarative-ec2.py`](declarative-ec2.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for the `-` runs | **every** `awsds-*` profile, the ones named, or `-` inside CloudShell — the third non-single-profile script, and for the same reason | `output/declarative-ec2.txt` | **The four EC2 settings `awsds-org-declarative-ec2` declares, read back per account** against the document. A declarative policy is enforced in the service's control plane, so the battery can only show that a *change* is refused — this shows what the setting **is**, which is the control. Also the one instrument that can answer whether a root-attached declarative policy reaches **Management**, which AWS documentation leaves undecided. |
| [`org-delegation.py`](org-delegation.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; takes another profile, or `-` for CloudShell on **Management** | `output/org-delegation.txt` | **INT-20 — can the Identity account manage the organization's *policies*, and which of them.** The organization **resource policy**, kept in three distinguishable states (present / absent / the read itself denied), then decomposed into nine checks: the principal, the read and write halves, the two actions that must be **absent**, and — the three that fail silently — whether the `Resource` list reaches the **root**, **nested** OUs, and the **policy-type ARNs** at all (`DEL-9`, added 2026-08-15: a target-only list denies every write and reads exactly like "all refused"). Plus the documents a write would have to reach, split by target class. **Exits 2 when a check fails.** |
| [`import-ids.py`](import-ids.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | `awsds-infra-identity` — one profile reaches both planes: Identity Center delegated administrator (D10) *and* Organizations reads (1c verification (x)) | `output/import-ids.txt` | **The import manifest for Stage 2 step 5** — the exact strings `terraform import` takes, in the four formats, for every policy, every attachment, the `InfrastructureAccess` set and its assignments. Also the resolved values of the three template placeholders. **Section 4 lists what must *not* be imported**, with the reason, rather than filtering it out. |
| [`tf-backends.py`](tf-backends.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | **every** `awsds-*` profile, or the ones named, or `-` — the fourth non-single-profile script, same reason | `output/tf-backends.txt` | **The Terraform state buckets and their keys, side by side.** Existence, versioning, SSE-KMS and the key's **alias**, the four BPA flags, the TLS-only statement, the noncurrent-version lifecycle, Object Lock — plus every bucket in each account, so one under an unexpected name is visible. Section 4 is where Stage 2 step 3.4's **two keys in Production** are either true or not. **Exits 2 when a check fails.** |
| [`networking.py`](networking.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | **every** `awsds-*` profile, the ones named, or `-` inside CloudShell — the fifth non-single-profile script, and for the standing reason: a CIDR overlap, a peering and a cross-account zone association are facts *between* accounts | `output/networking.txt` | **The `[P]` networking half, per account, side by side** — [Stage 3](../docs/plan/stages/stage-03-networking.md)'s preflight and its standing regression. VPCs with **default and Account Factory vend artifacts flagged** (every vended account carries one — `docs/AWS_STATE.md` §C), the two DNS attributes of step 4.1, subnets with their **zone IDs** (step 1.5), route tables and routes, IGWs, the **gateway endpoint IDs that are the INT-05 anchor** (the only endpoint IDs any policy may name — Lesson 3), peerings **from both sides** (INT-09), the three private zones with associations and **pending authorizations** (the 4.5 trap made visible), flow logs with retention, NACLs and SGs. Checks `NT-1`–`NT-8` mechanise validation 2 (no route into `10.40.0.0/16`, local routes excluded on purpose), step 6.5 (`10.90.0.0/24` nowhere), step 1.2 (no overlap), 4.1, 4.4 and 5. **Exits 2 when a check fails.** The `[P]`-stability deliverable is a **diff of two runs** of this file, either side of a `make down`/`make up` |
| [`egress.py`](egress.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | same multi-profile shape, same reason: step 8's endpoint list is deliberately **per account role**, so "is the set right" is only readable with the columns side by side | `output/egress.txt` | **The `[E]` networking half, plus the burn meter.** Interface endpoints (subnet count per D9, private DNS per 8.5), NAT gateways, elastic addresses, every endpoint **policy** read against step 9 — the org condition (9.1) and the AWS-owned-bucket allow (9.3), **presence, never completeness** (the no-NAT `dnf` probe is the stage's) — the service×account **matrix** read against step 8's lists (deliberately not encoded here — Lesson 14), the **hourly burn right now** (the manual instrument the forgotten-egress risk gets, D12 having skipped the alerts; zero everywhere is D11 working), and the region's **endpoint service-name catalog**, which answers stage verification (i) and the `VpcEndpointPolicySupported` flag read-only, before anything is paid for. Checks `EG-1`–`EG-4`; **exits 2 when a check fails** |
| [`vpn.py`](vpn.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | **every** `awsds-*` profile, the ones named, or `-` — multi-profile for the standing reason: GuardDuty coverage is a fact *across* accounts, and the step 8 deny lives in Identity while the Elastic IP it names lives in the VPN home | `output/vpn.txt` | **[Stage 4](../docs/plan/stages/stage-04-vpn.md)'s evidence.** The WireGuard host (`[D]` — type, state, IMDSv2), the `[P]` Elastic IP (`WG_EIP=` printed — the value step 8 and Stage 5's bucket policy name), the **one world-open SG rule** (UDP/51820 and nothing else, never port 22), the handshake log and alarm, **which permission sets carry `DenyControlPlaneOffVpn`** (read back through the Identity Center delegated admin — the six persona sets move together, `InfrastructureAccess` reported as the separate 8.3 decision), and **GuardDuty per account** with the two Stage-11-deferred add-ons that must read `DISABLED`. Checks `VP-1`–`VP-8`; **exits 2 when a check fails** |
| [`datalake.py`](datalake.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | same multi-profile shape, same reason: the lake and its policy live in Data Governance while every legitimate reader is in a consumer account (D22), and a pending RAM invitation is visible only from the consumer | `output/datalake.txt` | **[Stage 5](../docs/plan/stages/stage-05-data-foundation.md)'s evidence, producer and consumers side by side.** The lake buckets with their policy **branches** (vpce/ip/via/sigage/prin — presence, never sufficiency), KMS aliases, the Glue catalog with **resource links** flagged, crawlers (never scheduled, never at an Iceberg target), the `awsds-data-catalog-maintenance` role and its trust, **the Lake Formation `Parameters` reading that defends INT-11** (`DL-5` — the check to read after *any* apply in `data-governance/data/`), RAM shares + **pending invitations**, consumer workgroup enforcement, the derived zone's expiry, EFS (including the mount-target SG shape Stage 4's NAT forces), and Security Hub per account. Checks `DL-1`–`DL-11`; **exits 2 when a check fails** |
| [`cloudshell/management-landing-zone-drift.sh`](cloudshell/management-landing-zone-drift.sh) | [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) — **the only one**, no laptop path | **no profile — CloudShell on Management.** Takes a profile if one ever exists there | `output/cloudshell/management-landing-zone-drift.txt` | **Stage 2 verification (iii)** — whether the Organizations **resource policy** of step 5.1 shows up as landing-zone drift. The `driftStatus` flag, the **manifest** that says what the flag is even comparing, the **operation history** (an update that ran *after* the delegation and succeeded is the only positive evidence available without writing), and whether the document is still there and still narrowed to two statements. **Sections 2-4 are suppressed outside Management and the run exits 2** — measured: from a member account both landing-zone calls *succeed and return empty*, so an unguarded report would state "the landing zone has never run". Section 5 answers from Identity too, because the delegation grants it. |
| [`cloudshell/management-quotas.sh`](cloudshell/management-quotas.sh) | [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) — **the only one**, no laptop path | **no profile — CloudShell on Management.** Takes a profile if one ever exists there | `output/cloudshell/management-quotas.txt` | **Has the account-cap increase landed** — the one number the `Staging` vend is held on. The applied value (not the default), how much of it is spent, and any pending request. **Refuses to interpret the number outside Management**, where the same quota reads `0.0`. |

**The first two columns are different questions, and the whole table above collapses into two identities.** A
profile is a *(account, permission set)* pair; the **user** is whoever holds the assignment for that pair
([`docs/ORGANIZATION.md`](../docs/ORGANIZATION.md), "Assignments"). Every `awsds-*` profile resolves to the
**infrastructure user** — the five `awsds-infra-*` through `sso-group-infrastructure` → `InfrastructureAccess`,
and `awsds-policy-canary` through the permanent Account Factory direct assignment of Control Tower's
`AWSAdministratorAccess` (D32) — so **everything runnable from this laptop is one person and one login**.
Everything run with `-` is `AWS Control Tower Admin` in CloudShell, and that is not a convenience: `-` exists
exactly for Management, Log Archive and Audit, the three accounts where **no persona holds an assignment by
design** and where that standing identity (D33, D34) is the only way in.

**`org-policy-baseline.py` and `org-policies.py` walk the same tree and are not duplicates — they are
opposite ends of one change.** The baseline is a **preflight**, run *before* writing policy (step 7.0): it
prints whole documents, the quota and the organization's metadata, and answers *what already exists that I
must not duplicate*. `org-policies.py` is a **check**, run *after* every attachment and at every vend: it
prints no document bodies at all, binds to `Sid` because a managed document's id says nothing about its
contents (Lesson 23), resolves inheritance down to each account, and **fails with exit 2** on the statements
the SCP battery is structurally blind to (Lesson 22). Reach for the first when writing a policy and the
second when verifying one.

**All but the `cloudshell/` pair are Python scripts on the uv project at the repository root
(2026-08-15)**, sharing the [`awslib`](awslib/__init__.py) package that sits beside them. The shebang is
`#!/usr/bin/env -S uv run --quiet`, so the invocations below stay one path: uv resolves
`pyproject.toml`, pins the interpreter to `.python-version` and provides the packages —
nothing to install or activate beyond uv itself. Run any of them from anywhere; each one
locates the repository root itself:

```bash
./aws/list-identities.py
```

```bash
./aws/AZs.py
```

```bash
./aws/org-trusted-access-services.py
```

```bash
./aws/org-policy-baseline.py
```

```bash
./aws/account-bpa.py
```

```bash
./aws/org-policies.py
```

```bash
./aws/declarative-ec2.py
```

```bash
./aws/org-delegation.py
```

```bash
./aws/import-ids.py
```

```bash
./aws/tf-backends.py
```

```bash
./aws/networking.py
```

```bash
./aws/egress.py
```

```bash
./aws/vpn.py
```

```bash
./aws/datalake.py
```

**`cloudshell/` holds the three scripts with no laptop path — and they are shell on purpose.**
`management-quotas.sh` and `management-landing-zone-drift.sh` answer only from **Management**,
`audit-iam-analyser.sh` only from **Audit**: the two accounts that hold no CLI profile by design
(D33/D34). Both run inside **CloudShell**,
signed in as `AWS Control Tower Admin` through `AWSAdministratorAccess` — and CloudShell has
no uv, so they stay shell and **standalone**: no `awslib`, no environment, one self-contained
file each. Upload just the file (Actions → Upload file) and run it where it lands:

```bash
bash management-quotas.sh
```

```bash
bash audit-iam-analyser.sh
```

```bash
bash management-landing-zone-drift.sh
```

In a clone they are [`cloudshell/management-quotas.sh`](cloudshell/management-quotas.sh),
[`cloudshell/audit-iam-analyser.sh`](cloudshell/audit-iam-analyser.sh) and
[`cloudshell/management-landing-zone-drift.sh`](cloudshell/management-landing-zone-drift.sh), and their
reports land in `aws/output/cloudshell/` rather than beside the script. **All three refuse to interpret
a result from the wrong account**, which is the failure mode this folder exists around: the calls in
question do not error there, they answer with something meaningless that looks like an answer.

**A *Python* script run in CloudShell still needs the whole `aws/` folder**: the `-` modes of
`account-bpa.py`, `declarative-ec2.py`, `networking.py`, `egress.py` and the `org-*` scripts
import `awslib`, which sits beside them, so the system `python3` runs them as long as the
folder is present — clone the repository, or upload it zipped and unzip. A single `.py` file
alone is the one shape that does not work.

They need a live SSO session. If the run stops with `cannot authenticate`:

```bash
aws sso login --sso-session awsds
```

**One login covers every script here, whatever profile each one declares.** The login authenticates against
the *access portal* — the `awsds` sso-session — and the token it caches is keyed by the session name, not by
profile or account: every `awsds-*` profile in `~/.aws/config` declares `sso_session = awsds` and shares it.
The profile only matters one step later, when a call trades that token for temporary credentials of its
account's role (`sso_account_id` + `sso_role_name`). `aws sso login --profile awsds-infra-identity` reaches
the same session through the profile and is equivalent; naming the session says what is happening.
[`login.py`](login.py) wraps that exact command and nothing else, so the login sits in the same folder as
the scripts it unblocks.

## `aws/output/` — the snapshots

**Untracked** (`.gitignore`), and **regenerated, never edited**. Deleting the folder loses nothing.

Three rules, in the order they matter:

1. **Never copy an account id or an email address out of these files into a tracked file.** The same rule
   the `secrets` folder carries, for the same reason ([`CLAUDE.md`](../CLAUDE.md)). A snapshot may be read
   freely; what it says may be *used* freely; the identifiers themselves stay here.
2. **A snapshot is evidence, not intent.** It records what AWS answered at one instant. Why a resource
   exists belongs in [`docs/plan/decisions/`](../docs/plan/decisions/INDEX.md), what was typed to create it belongs in
   [`docs/log/`](../docs/log/INDEX.md), and neither is derivable from a listing.
3. **Check the timestamp in the header before trusting a line.** If the file predates the work being
   reasoned about, re-run the script — it costs seconds and only reads.

**Before reporting anything in a snapshot as a finding, read [`docs/AWS_STATE.md`](../docs/AWS_STATE.md).** It holds
what a snapshot is expected to show (`INV-nn`), the differences already accounted for (`EXC-nn` — the
suspended `Sandbox` account at the root is not ours), and what a later stage is going to change anyway. A
snapshot read without it produces false alarms, which is worse than not reading it: a real finding stops
being distinguishable from the ones already known.

## Finding an answer in `output/list-identities.txt`

The file is sectioned and each block prints the command that produced it. Jump to the section, don't read
the file end to end.

| Question | Section |
|---|---|
| **What is the organization id** — the value `aws:PrincipalOrgID` and `aws:ResourceOrgID` take? | 2.1 — `ORG_ID`; the same value, with the enabled policy types beside it, is section 1 of `org-policy-baseline.txt` |
| What is the management account id? | 2.1 — `MGMT_ID` |
| Which policy types can be attached at all (SCP, RCP, tag, declarative)? | 2.2 — the root's `PolicyTypes`, `ENABLED` or not |
| What does the OU tree look like, and how deep is it? | 2.3 — the indented tree first, then one pair of tables per parent |
| Which OU is an account in? | 2.3 — the account appears under its parent |
| Which accounts exist, and are they `ACTIVE`? | 2.4 |
| What is the Identity Store id, and is there exactly one? | 3.1 and 3.2 — 3.2 is a hard check; the report stops there if it fails |
| Which `sso-group-*` groups exist? | 3.3 |
| Which SSO users exist? | 3.4 |
| Who is in a group? | 3.5 — one table per group |
| Which permission sets exist, and how long is a session? | 4.1 and 4.2 |
| What does a permission set actually grant — managed policies, boundary, inline policy, tags? | 4.3 |
| Who can reach which account, through which permission set? | 5.1 (full triples) and 5.2 (same rows, grouped by account) |
| Did something not answer? | 6 — every failed call, with its error |

**Section 6 is what makes an empty block readable.** A listing that returns nothing and a listing that was
denied look identical otherwise, and reading one as the other is Lesson 13
([`docs/plan/lessons.md`](../docs/plan/lessons.md)). Section 6 empty means every `(none)` in the file is a real none.

## Finding an answer in `output/AZs.txt`

| Question | Section |
|---|---|
| Which zone ID is `us-west-2a` **in this account**? | 2 — one listing per account, or 3 for all of them at once |
| Do the accounts name the same physical datacenter the same way? | 4 — the verdict, with the differing rows printed if they do not |
| Which accounts were actually measured? | 1 — a `(failed)` row is a profile that did not authenticate |
| Is a zone something other than a plain, available AZ? | 2 — `ZoneType`, `State` and `OptInStatus` are in the per-account listing |

**Two ways this file can mislead, both stated inside it.** An account with **no profile** on this laptop
does not appear at all — `Staging` today, and every Sandbox until Stage 14 gives it one — so the file is
silent about it rather than reassuring. And a **single** measured profile agrees with itself, which the
check reports as *"nothing was compared"* rather than as a pass: a verification that returns OK on both
success and vacuity is Lesson 13 again.

**What was decided from this measurement is not in the file** (rule 2 below): it is
[`docs/plan/architecture.md`](../docs/plan/architecture.md) §4.1 and [`docs/plan/open-questions.md`](../docs/plan/open-questions.md)
item 3.

## Finding an answer in `output/org-trusted-access-services.txt`

| Question | Section |
|---|---|
| Which services may act across every account in this organization? | 1 |
| Is the Audit account registered as the Access Analyzer delegated administrator? | 2 — the one row Stage 1b step 8.2 creates |
| Who administers GuardDuty / Security Hub / RAM / Config / Identity Center org-wide? | 3 — one row per enabled principal |
| Did something not answer? | 4 |

**Two registrations, and section 3 is where they stop looking alike.** *Trusted access* says a **service**
may read the organization and create its own service-linked roles inside member accounts; *delegated
administration* says an **account** operates that service for the whole organization. The first is the
prerequisite for the second, not a weaker form of it — so a service can appear in section 1 and have no row
worth reading in section 3, which means it is administered from Management. That is the default, not a gap.
A third case, `(no delegated administration for this service)`, is the API rejecting the question — Control
Tower is one.

**Section 1 is an inventory nobody in this project wrote**, which is why it is worth re-reading rather than
remembering: most of it is what Control Tower switched on when the landing zone was installed, and a service
there that no stage accounts for is a finding (Lesson 17 — a service that "sets itself up" creates principals
nobody chose). The expected content is `INV-09` in [`docs/AWS_STATE.md`](../docs/AWS_STATE.md).

**Both calls answer from the Identity account** — measured on this script's first run, 2026-08-12. That
extends the read boundary Stage 1b step 4 established: a delegated administrator for *any* service may make
these Organizations reads, so the management account is needed to *change* this state and not to read it.
If a future run is denied anyway, section 4 says so and the fallback is in the script header.

## Finding an answer in `output/cloudshell/audit-iam-analyser.txt`

| Question | Section |
|---|---|
| Was this run in the account it was meant to be run in? | 1 — read it **first**; every other section is about whatever account answered |
| Which analyzers exist here, and since when? | 2 |
| **Is the zone of trust the organization, or just this account?** | 2 and 5 — the `type` column |
| Is anything suppressing findings? | 3 — archive rules; none is expected |
| What has been found, and in which account? | 4 — `resourceOwnerAccount` names the account the exposed resource is in |
| Did something not answer? | 6 |

**This script and `cloudshell/management-quotas.sh` are the two that do not run from a profile, and the
absence is the design.** The
organization analyzer lives in **Audit** (Stage 1b step 8.2), and no project persona holds an assignment
there — [`docs/ORGANIZATION.md`](../docs/ORGANIZATION.md) records that as permanent. The only identity that reaches
Audit is `AWS Control Tower Admin`, which D33/D34 keep in the console. So the run is CloudShell inside
Audit, and section 1 resolves the **account name** through Organizations rather than trusting the operator
to be where they think they are — the check the console wizard did not have on 2026-08-12, when it named
the zone of trust and never the account the analyzer was being created in (Lesson 16).

**Two ways this file can mislead, both answered inside it.** An empty findings table is not evidence: access
*inside* the organization is not external to an organization zone of trust, and the estate is nearly empty
until Stages 2-3 — so section 4 prints a **count**, which is a measurement, rather than leaving an absent
table to be read as a pass. And an `ACCOUNT`-type analyzer sitting in Audit stays `ACTIVE`, reports on one
near-empty account and raises nothing, which is why the `type` is a checked field and not a column
(Lesson 13).

## Finding an answer in `output/org-policy-baseline.txt`

| Question | Section |
|---|---|
| What is the organization id, and is `FeatureSet` `ALL` (which RCPs require)? | 1 — `ORG_ID`, printed as a named variable because it is the value `aws:ResourceOrgID` and `aws:PrincipalOrgID` are compared against, and what `render.py` puts in place of `<ORG_ID>` |
| Which policy types may be attached at all? | 1.2 — the same reading as `list-identities.txt` 2.2, kept here so this file stands alone |
| What is an OU's **id**, its **ARN** (which `enable-control` takes), or its **full path** (which `aws:PrincipalOrgPaths` takes)? | 2 |
| What is already attached to this node, and is it AWS's or ours? | 3 — one block per node, one line per policy type |
| **What is already denied** — i.e. what should Stage 1c *not* write again? | 4 — the policy documents themselves, and the carve-outs inside them |
| Is this OU registered with Control Tower, and which controls does it already have? | 5 — **an error means unregistered**, an empty list means registered with nothing elective |
| How many policies still fit on this node, and how large may each be? | 6 |
| Did something not answer? | 7 — and *which* calls failed is the answer to Stage 1c verification (x) |

**The two sections that change what gets written are 4 and 6, and both are read *before* the first
`create-policy`.** Control Tower's mandatory controls already deny changes to CloudTrail and to the Config
recorder on every registered OU, with the service-role carve-outs that keep the landing zone able to update
itself — so a hand-written duplicate costs SCP budget and adds a second place to get those carve-outs wrong.
That is Stage 1c verification (iii), and it is a thing to read first rather than to notice afterwards.

**Section 5 is the one place in `aws/` where an error is the answer.** `controltower
list-enabled-controls` rejects an unregistered target instead of returning an empty list, which is exactly
the Lesson 13 shape inverted: here the empty result and the failure genuinely mean different things, so the
report keeps them apart rather than tidying them together.

## Finding an answer in `output/account-bpa.txt`

| Question | Section |
|---|---|
| Does this account have account-level S3 Block Public Access, and are all four flags set? | 3 — the verdict table; 2 for the raw answer |
| Which accounts is nobody measuring? | 4 — **read it before reading section 3 as a pass** |
| Which identity produced each row? | 1 — a `(failed)` row is a profile that did not authenticate, never a compliant one |
| How is it set, and in which order relative to the SCP? | 5 — the command, and the interlock that must not be reversed |

**`NoSuchPublicAccessBlockConfiguration` is the "not set" answer, not a failure**, and it is what to expect
before Stage 1c step 7.4 — so it is reported as `NOT SET` in sections 2 and 3 and kept out of the failure
section. The other direction matters as much: **a missing account is not a passing account.** Management,
Log Archive and Audit hold no project persona, so they are read from CloudShell (`./aws/account-bpa.py -`)
and recorded by hand; `Staging` and every Sandbox beyond the first have no profile yet, and `EXC-01` is not
ours. An account in neither section 3 nor section 4 is the hole this snapshot exists to expose.

## Finding an answer in `output/org-delegation.txt`

| Question | Section |
|---|---|
| Has the Organizations **policy** delegation been created at all (Stage 2 step 5.1)? | 2 — and it has **three** states, not two |
| Is "no delegation" being confused with "the read was denied"? | 2 — they are separate states on purpose; only the first is the expected pre-5.1 answer |
| **Can the delegated administrator reach a *root-attached* document?** | 3 — `DEL-6`. The check that decides how much of Stage 2 exists |
| Does it reach the **nested** OU, or only a named one? | 3 — `DEL-7`; AWS excludes child OUs when a single OU is named, and this tree is depth 2 |
| Which policy types does it admit, and does it wrongly grant `Enable`/`DisablePolicyType`? | 3 — `DEL-8` and `DEL-5` |
| Is the type condition on an operator that **denies every write** — one without `IfExists`? | 3 — `DEL-8`, which reads the operator and not only the values (since 2026-08-15) |
| Which documents would a write have to reach, and how many are on the root? | 5 |

**Section 4 is the main finding, not a disclaimer.** Organizations *reads* already answer from the Identity
account with **no** policy delegation — measured in Stage 1b step 4 and 1c verification (x) — so nothing
that merely reads is evidence here, and a script built on `describe-policy` would return OK before *and*
after step 5.1 (Lesson 13). What this file decides is **scope, by reading the document** (Lesson 22). The
decisive test is a *write*, it is named precisely in Stage 2 step 5.0, and it is a human act on Management.

## Finding an answer in `output/import-ids.txt`

| Question | Section |
|---|---|
| What string does `terraform import` take for this object? | 5 — split by slice: 5a documents, 5b attachments, 5c the permission set, 5d the assignments |
| What are `<ORG_ID>`, `<ORG_PATH_DATA>` and `<ACCOUNT_ID_DATA>` right now? | 1 — and how Terraform is meant to derive each |
| Which policies exist, of which type, and where is each attached? | 2 |
| Which permission sets exist, and which one does Stage 2 actually import? | 3 — only `InfrastructureAccess` is marked `yes`, and that is the design |
| **What must I not import?** | 4 — Control Tower's policies and sets, and the Account Factory direct assignments, each with the reason |

**The address is a suggestion; the id is the measurement.** Only the configuration knows whether a resource
is `.baseline` or `.this["awsds-org-scp-baseline"]`, and **an import into a `for_each` resource with the
wrong key does not error** — it leaves an orphan in state and a create in the plan. Import one, run `plan`,
then the rest. **A manifest with a failed call in it is incomplete, not wrong**, and section 6 says so:
importing from a short list leaves objects unmanaged with an empty plan, which looks exactly like success.

## Finding an answer in `output/tf-backends.txt`

| Question | Section |
|---|---|
| Does this account have a Terraform state bucket, and is it versioned, SSE-KMS, closed, TLS-only, lifecycled? | 2 — the side-by-side table; 3 for the verdict |
| Is there already a bucket under the name the bootstrap slice is about to claim? | 2 — the per-account listing of **every** bucket, below the table |
| **Does Production carry the second key of Stage 2 step 3.4?** | 4 — the alias list; Production is the one account that should show two |
| Which accounts is nobody measuring, and which of those is correct? | 5 — **read it before reading section 3 as a pass** |
| Which identity produced each row? | 1 — a `(failed)` row is a profile that did not authenticate, never a compliant one |

**"No state bucket" is the expected answer until Stage 2 steps 2 and 3 have run**, so it is reported as a
`note` rather than a failure — and it becomes a **regression** the moment that account has been
bootstrapped. Bucket names are **discovered** by matching `tfstate`, not composed from a convention: the
`<env>` token for the Identity account is not settled in any plan file, and a hardcoded guess would report
a correctly-named bucket as missing.

## Finding an answer in `output/networking.txt`

| Question | Section |
|---|---|
| Which VPCs exist here, and which of them did **nobody in this project create**? | 2 — the DEFAULT column, plus `NT-1` in 10: every vended account carries an **Account Factory VPC** (`docs/AWS_STATE.md` §C), which is not the default VPC and not ours |
| Are both DNS attributes on (step 4.1)? | 2; checked as `NT-2` |
| Which **zone ID** is each subnet in — is a peering about to be cross-AZ? | 3, read next to `AZs.txt` |
| Does any route table reach into Staging's range (validation 2), or carry the WireGuard client range (step 6.5)? | 4, decided by `NT-3`/`NT-4` — `NT-3` excludes `local` routes on purpose, so a future Staging VPC does not fail against its own local route |
| **What may Stage 5's bucket policies anchor on (INT-05)?** | 5 — the gateway endpoint IDs, and only those; the interface endpoints of `egress.txt` are `[E]` and may anchor nothing (Lesson 3) |
| Are the two peerings there — and only the two? | 6, with both sides printed; `NT-6` holds the D20 half |
| Did the step 4.4 zone handshake complete, and is an authorization still pending (the 4.5 trap)? | 7, decided by `NT-8` |
| Is a flow log missing, or retaining forever? | 8; `NT-7` |
| Did somebody add a NACL rule (2.3), or open an SG to the world? | 9 — the SG listing is informational: from Stage 4 on, exactly one world-open rule is expected (UDP 51820) |
| **Is the `[P]` half byte-stable across `make down`/`make up`?** | the whole file: run, copy aside, cycle, run, `diff` — only the timestamp may change |
| Which accounts is nobody measuring? | 11 — **Staging above all**, whose "peering list is empty" deliverable is unrunnable until the vend |

## Finding an answer in `output/egress.txt`

| Question | Section |
|---|---|
| Which interface endpoints are up, in how many AZs (D9), with private DNS (8.5)? | 2; `EG-2`/`EG-3` |
| Is a NAT running, and which elastic addresses exist? | 3 |
| Does every endpoint policy name the organization (9.1), and does the S3 gateway policy carry the AWS-owned-bucket allow (9.3)? | 4; `EG-1`/`EG-4` — **presence, never sufficiency**: only the stage's no-NAT `dnf` probe shows the allow-list is complete. Account Factory endpoints are notes, not step 9 failures |
| Does each account's endpoint set match step 8's per-role list? | 5 — the matrix, read against the stage file rather than a copy here |
| **What is the burn right now — did I forget `make down`?** | 6 — the D12 instrument. Zero everywhere is D11 working, not an absent reading |
| What is the Studio endpoint's real service name (verification (i)), does CodeArtifact exist here (8.4), and which services can carry a policy at all? | 7 |
| Which accounts is nobody measuring? | 9 — Staging's list (8.3) is unmeasurable until the vend |

**`networking.py` and `egress.py` split one stage the way the stage itself does, and the split is a
cadence.** `foundation/` is `[P]` and never destroyed, so `networking.py` is run at each vend, after each
Stage 3 pass, and on **both sides of a lifecycle cycle** — the diff of two runs *is* the stability
deliverable. `egress/` is `[E]` and dies with the session, so `egress.py` is run at the session's two ends:
after `make up` (is the set right) and after `make down` (is anything still burning — the one question
nothing else in this design asks, since D12 declined the budget alerts). Both are **control-plane
readings**: the stage's behavioural proofs — `dnf` through the endpoint, `NXDOMAIN` from Staging, the probe
reaching GitLab's port — belong to the stage's throwaway probe instances, and no describe call substitutes
for them (Lesson 20's rule: configuration for configuration questions, probes for behaviour).

## Finding an answer in `output/vpn.txt`

| Question | Section |
|---|---|
| Is the WireGuard host there, what type, and is it running or stopped ([D])? | 2 — `stopped` between sessions is D11 working, not an outage |
| **What is the Elastic IP** — the value step 8's deny and Stage 5's bucket policy name? | 3 — printed as `WG_EIP=`; also whether it is associated with the host |
| Is anything world-open besides UDP/51820 — did port 22 sneak in? | 3, decided by `VP-3` |
| Is the handshake log shipping, and does the health alarm exist (step 7)? | 4 |
| **Which permission sets carry `DenyControlPlaneOffVpn`** — did the 8.2 rollout reach all six, and has the deliberate 8.3 diff been applied to `InfrastructureAccess`? | 5, decided by `VP-7` — a partial rollout FAILS (Lesson 14) |
| Is GuardDuty enabled in every measured account, with S3/Malware Protection still off? | 6, decided by `VP-8`; the delegation registration is printed below the table |
| Which accounts is nobody measuring? | 8 — GuardDuty's org configuration in Audit above all |

## Finding an answer in `output/datalake.txt`

| Question | Section |
|---|---|
| Do the lake buckets exist with versioning, SSE-KMS and Bucket Keys? | 2, decided by `DL-1` |
| Does each bucket policy carry the three step 1.3 branches and the two guards? | 2 — the BRANCHES column; `DL-2` (presence, never sufficiency) |
| **Did an apply reset `CROSS_ACCOUNT_VERSION`/`SET_CONTEXT`** — the silent INT-11 failure? | 6, decided by **`DL-5`** — read it after *every* apply in `data-governance/data/` |
| Are the IAM-fallback defaults still granting `IAMAllowedPrincipals` (step 5.2)? | 6, decided by `DL-6` once databases exist |
| Does the maintenance role exist under its exact contracted name, trusting only Glue? | 5, decided by `DL-4` |
| Is a crawler scheduled, or pointed at an Iceberg table — both forbidden (D27)? | 4, decided by `DL-3` |
| Did the shares arrive as resource links, with **no pending RAM invitation**? | 7 and 4, decided by `DL-7` — a PENDING row is INT-11's fallback tax |
| Is the consumer workgroup actually enforcing its result location and scan limit (D19)? | 8, decided by `DL-8` |
| Does the derived zone expire, and does EFS admit the WireGuard **SG** rather than the peer CIDR? | 9 and 10, decided by `DL-9`/`DL-10` |
| Is Security Hub on everywhere, with FSBP? | 11, decided by `DL-11` |
| Which accounts is nobody measuring? | 13 — Staging is absent by design (D20), Production joins at Stage 9 |

## The two written for Stages 4 and 5, before either stage starts

**Written 2026-08-16**: `vpn.py` and `datalake.py`, from the revised
[Stage 4](../docs/plan/stages/stage-04-vpn.md) and
[Stage 5](../docs/plan/stages/stage-05-data-foundation.md) roteiros — the same
before-the-stage pattern as the Stage 3 pair. Until each stage runs, every absent resource reads as a
`note` ("expected before Stage N step M"), so today's clean state passes and a *partial* build fails
loudly. **Their first run already measured the thing `DL-5` exists to defend**: Data Governance answers
`CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE` with no admins declared — the exact INT-11 state Stage 5
step 5.4 must carry through its first apply — and confirmed the `IAMAllowedPrincipals` create-defaults
are still in place, which is what step 5.2 exists to remove. Each script names its contracts (the
`awsds-*-vpn` Name tag, the `DenyControlPlaneOffVpn` Sid, the `awsds-data-catalog-maintenance` role
name) so a rename fails in a check rather than in a stage.

## The four written for Stage 2, and the one thing they have in common

**Written 2026-08-15**: `org-delegation.py`, `import-ids.py`, `tf-backends.py` and `cloudshell/management-quotas.sh`.
[Stage 2](../docs/plan/stages/stage-02-terraform-foundation.md) is the first stage that has to **feed an
AWS-generated identifier back into a command** rather than read it, and that is a different job from every
snapshot above. A snapshot tolerates a stale line because a human reads it and notices; **an import id is
pasted into a state file, and a wrong one produces an orphan and a create rather than an error.** So the
three Stage 2 scripts are stricter about one thing than the rest of this folder: each of them says out loud
what it is *not* authoritative about — `import-ids.py` owns the id and not the Terraform address,
`org-delegation.py` owns the delegation's scope and not whether a write will land, `tf-backends.py` owns
what is there and not what should be.

**One defect was found and fixed in an existing script at the same time.** `org-policies.py` §1 listed ids
for `SERVICE_CONTROL_POLICY` only and reduced the RCP to a presence check, so **three of the ten attached
documents had no id in any snapshot** and existed only in the 1c log. All four types now carry theirs.

## The two written for Stage 3, and what their first run already found

**Written 2026-08-15**: `networking.py` and `egress.py`, from the
[Stage 3](../docs/plan/stages/stage-03-networking.md) roteiro *before* the stage starts — because the stage's
own validations are exactly the kind of reading that otherwise gets done once, in one console tab, per
account. **Their first run measured something no plan file had:** every vended account carries an
**Account Factory VPC** with an S3 gateway endpoint on the default full-access policy — recorded in
[`docs/AWS_STATE.md`](../docs/AWS_STATE.md) §C, decided in Stage 3. Both scripts report those artifacts as `note`
rows tied to that decision, so today's known state reads clean and a *new* deviation still fails loudly.

## Adding a script here

Keep the shape, so that one file explains all of them:

- **Read-only.** A script that changes something does not belong in `aws/`.
- **Build on [`awslib`](awslib/__init__.py)**, the package beside the scripts: `context`
  (repo root, output dir, the CloudShell fallback), `awscli` (the CLI as a subprocess, with
  `run`'s capture/tolerate semantics), `report` (sections, `column -t` tables, the
  failed-calls log), `profiles` (discovery and the preflight). The scripts shell out to the
  `aws` CLI rather than using an SDK on purpose: the report prints the exact command above
  each block, and the battery reads the CLI's error wording - both are the contract.
  `awslib` must stay standard-library-only and must import nothing from outside `aws/`,
  or the CloudShell fallback dies.
  **[`cloudshell/`](cloudshell/management-quotas.sh) is the deliberate exception**: its two scripts run
  where neither uv nor the repository may exist, so they stay standalone shell — one
  self-contained file each, no `awslib`, uploadable alone.
- **One profile per script**, named at the top, with the reason that profile can see what it sees — and
  **name the SSO user behind it in the table above**, since a profile is a *(account, permission set)* pair
  and the user is a second fact, not a restatement of it.
  **`AZs.py`, `account-bpa.py` and `declarative-ec2.py` are the exceptions, and they are what an exception
  has to look like:** in all three, the subject is a *per-account* fact whose meaning is the comparison
  **between** accounts — an AZ name→ID mapping is only interesting next to another account's, and a setting
  that is right in five accounts and unset in the sixth is the sixth account's hole. A single-profile version
  would answer nothing. All three pay the rule back by printing the caller ARN of every profile in section 1
  — which is what naming one profile at the top exists to make visible. Multi-profile is not a licence; it is
  for a script whose subject is the difference between accounts.
- **Output to `aws/output/<script-name>.txt`**, one file per script (`awslib.context` creates the folder).
- **Print the command above its output** — `Report.show` — so any line can be re-derived
  by hand, and prefer `--output table` over post-processing.
- **Print reused identifiers as `NAME=value` lines** (`MGMT_ID`, `ROOT_ID`, `IDS`, `INST`) where they are
  resolved, so a reader can re-run any later command by hand.
- **Log every failed call into a final section** rather than letting it read as an empty result.
- **Number the sections** and list them in the header, then add the row to the table above and to the
  question table.

---

*Project root: [`README.md`](../README.md) · CLI recipes run by hand: [`aws/AWS-CLI.md`](AWS-CLI.md) ·
What was done by hand: [`docs/log/INDEX.md`](../docs/log/INDEX.md)*
