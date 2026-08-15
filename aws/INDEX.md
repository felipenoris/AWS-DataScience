# `aws/` — index

**Read-only scripts that photograph what is actually deployed in AWS, and the text snapshots they
produce.** Nothing here creates, changes or deletes a resource, and nothing here is infrastructure code —
that is `terraform-live/` from Stage 2 on.

Why this exists: [`GENERAL_PLAN.md`](../GENERAL_PLAN.md) and `plan/` say what *should* be there, the
[`log/`](../log/INDEX.md) files say what was *done by hand*, and these snapshots say what AWS *reports right
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
| [`list-identities.sh`](list-identities.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user) | `awsds-infra-identity` (Identity account, IAM Identity Center delegated administrator — D10) | `output/list-identities.txt` | The Organization: **organization id** — the value `aws:PrincipalOrgID` and `aws:ResourceOrgID` are compared against — management account id, root and its enabled policy types, the whole OU tree, every account. The directory: Identity Store instance, groups, users, group memberships. The entitlements: permission sets with what each grants, and every assignment triple. |
| [`AZs.sh`](AZs.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user) — including behind `awsds-policy-canary`, which is the **same human** through a different permission set (D32) | **every** `awsds-*` profile in `~/.aws/config`, or the ones named as arguments — the one script here that is not single-profile, see below | `output/AZs.txt` | The availability-zone **name → zone ID** mapping each account reports, one listing per account, the mappings side by side, and a check on whether they agree. |
| [`org-trusted-access-services.sh`](org-trusted-access-services.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; takes another profile as its argument, or `-` to run with no profile at all — inside CloudShell on Management | `output/org-trusted-access-services.txt` | Which AWS services hold **trusted access** across the organization, which account is each one's **delegated administrator**, and the `access-analyzer` registration on its own. |
| [`audit-iam-analyser.sh`](audit-iam-analyser.sh) | [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) — **the only one**, no laptop path | **no profile — CloudShell on the Audit account**, as `AWS Control Tower Admin`. Takes a profile as its argument if one ever exists there; see below | `output/audit-iam-analyser.txt` | The IAM Access Analyzer analyzers of that account and Region: type (the **zone of trust**), status, tags, archive rules, findings — and a check that there is exactly one, `ORGANIZATION`, `ACTIVE`. |
| [`org-policy-baseline.sh`](org-policy-baseline.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user) — **open, and what section 7 answers**; [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback, which section 5 is expected to need anyway | `awsds-infra-identity` by default; takes another profile, or `-` for CloudShell on **Management** as `AWS Control Tower Admin` — which is the fallback if the policy reads are denied | `output/org-policy-baseline.txt` | **The ceiling that already exists.** Organization id and feature set, the root and its enabled policy types, every node with its **id, ARN and full path**, the policies attached per node per type, the **documents** of the ones found, the Control Tower controls enabled per node, and the policy quota. Stage 1c step 7.0 steps 1, 2, 3 and 5 in one pass. |
| [`org-policies.sh`](org-policies.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; takes another profile, or `-` for CloudShell on **Management** | `output/org-policies.txt` | **What governs each node right now, by `Sid`** — no document bodies. Attached per node condensed to its statement names; **what governs each *account* once inheritance is resolved**; the **read-only checks** that no probe can reach; and a per-OU ceiling table. **Exits 2 when a check fails**, so it can gate a change. **Gap found and fixed the same day (2026-08-15):** section 1 used to list ids for `SERVICE_CONTROL_POLICY` only, leaving three of the ten attached documents with no id in any snapshot (the [1c log](../log/log-stage-01c-preventive-policies.md) alone carried them). **All four policy types now carry their ids** — which is what [Stage 2](../plan/stages/stage-02-terraform-foundation.md) step 5.5 needs, where an id is an argument |
| [`account-bpa.sh`](account-bpa.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) for the `-` runs in Management, Log Archive and Audit | **every** `awsds-*` profile, or the ones named as arguments, or `-` inside CloudShell for the three accounts that have no profile — the second script here that is not single-profile, see below | `output/account-bpa.txt` | The **account-level** S3 Block Public Access configuration of each account, the four flags side by side, and which accounts nothing is measuring. Read three times: before 7.4, after 7.4 and before 7.5, and at every vend. |
| [`declarative-ec2.sh`](declarative-ec2.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) for the `-` runs | **every** `awsds-*` profile, the ones named, or `-` inside CloudShell — the third non-single-profile script, and for the same reason | `output/declarative-ec2.txt` | **The four EC2 settings `awsds-org-declarative-ec2` declares, read back per account** against the document. A declarative policy is enforced in the service's control plane, so the battery can only show that a *change* is refused — this shows what the setting **is**, which is the control. Also the one instrument that can answer whether a root-attached declarative policy reaches **Management**, which AWS documentation leaves undecided. |
| [`org-delegation.sh`](org-delegation.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; takes another profile, or `-` for CloudShell on **Management** | `output/org-delegation.txt` | **INT-20 — can the Identity account manage the organization's *policies*, and which of them.** The organization **resource policy**, kept in three distinguishable states (present / absent / the read itself denied), then decomposed into nine checks: the principal, the read and write halves, the two actions that must be **absent**, and — the three that fail silently — whether the `Resource` list reaches the **root**, **nested** OUs, and the **policy-type ARNs** at all (`DEL-9`, added 2026-08-15: a target-only list denies every write and reads exactly like "all refused"). Plus the documents a write would have to reach, split by target class. **Exits 2 when a check fails.** |
| [`import-ids.sh`](import-ids.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user) | `awsds-infra-identity` — one profile reaches both planes: Identity Center delegated administrator (D10) *and* Organizations reads (1c verification (x)) | `output/import-ids.txt` | **The import manifest for Stage 2 step 5** — the exact strings `terraform import` takes, in the four formats, for every policy, every attachment, the `InfrastructureAccess` set and its assignments. Also the resolved values of the three template placeholders. **Section 4 lists what must *not* be imported**, with the reason, rather than filtering it out. |
| [`tf-backends.sh`](tf-backends.sh) | [Infrastructure](../ORGANIZATION.md#infrastructure-user) | **every** `awsds-*` profile, or the ones named, or `-` — the fourth non-single-profile script, same reason | `output/tf-backends.txt` | **The Terraform state buckets and their keys, side by side.** Existence, versioning, SSE-KMS and the key's **alias**, the four BPA flags, the TLS-only statement, the noncurrent-version lifecycle, Object Lock — plus every bucket in each account, so one under an unexpected name is visible. Section 4 is where Stage 2 step 3.4's **two keys in Production** are either true or not. **Exits 2 when a check fails.** |
| [`quotas.sh`](quotas.sh) | [`AWS Control Tower Admin`](../ORGANIZATION.md#aws-control-tower-admin-d33) — **the only one**, no laptop path | **no profile — CloudShell on Management.** Takes a profile if one ever exists there | `output/quotas.txt` | **Has the account-cap increase landed** — the one number the `Staging` vend is held on. The applied value (not the default), how much of it is spent, and any pending request. **Refuses to interpret the number outside Management**, where the same quota reads `0.0`. |

**The first two columns are different questions, and the whole table above collapses into two identities.** A
profile is a *(account, permission set)* pair; the **user** is whoever holds the assignment for that pair
([`ORGANIZATION.md`](../ORGANIZATION.md), "Assignments"). Every `awsds-*` profile resolves to the
**infrastructure user** — the five `awsds-infra-*` through `sso-group-infrastructure` → `InfrastructureAccess`,
and `awsds-policy-canary` through the permanent Account Factory direct assignment of Control Tower's
`AWSAdministratorAccess` (D32) — so **everything runnable from this laptop is one person and one login**.
Everything run with `-` is `AWS Control Tower Admin` in CloudShell, and that is not a convenience: `-` exists
exactly for Management, Log Archive and Audit, the three accounts where **no persona holds an assignment by
design** and where that standing identity (D33, D34) is the only way in.

**`org-policy-baseline.sh` and `org-policies.sh` walk the same tree and are not duplicates — they are
opposite ends of one change.** The baseline is a **preflight**, run *before* writing policy (step 7.0): it
prints whole documents, the quota and the organization's metadata, and answers *what already exists that I
must not duplicate*. `org-policies.sh` is a **check**, run *after* every attachment and at every vend: it
prints no document bodies at all, binds to `Sid` because a managed document's id says nothing about its
contents (Lesson 23), resolves inheritance down to each account, and **fails with exit 2** on the statements
the SCP battery is structurally blind to (Lesson 22). Reach for the first when writing a policy and the
second when verifying one.

Run any of them from anywhere; each one `cd`s to the repository root itself:

```bash
./aws/list-identities.sh
```

```bash
./aws/AZs.sh
```

```bash
./aws/org-trusted-access-services.sh
```

```bash
./aws/audit-iam-analyser.sh
```

```bash
./aws/org-policy-baseline.sh
```

```bash
./aws/account-bpa.sh
```

```bash
./aws/org-policies.sh
```

```bash
./aws/declarative-ec2.sh
```

```bash
./aws/org-delegation.sh
```

```bash
./aws/import-ids.sh
```

```bash
./aws/tf-backends.sh
```

`quotas.sh` is the exception: it has no laptop path, because Management holds no CLI profile.
Run it inside **CloudShell on the Management account**, signed in as `AWS Control Tower Admin`
through `AWSAdministratorAccess`:

```bash
./aws/quotas.sh
```

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

## `aws/output/` — the snapshots

**Untracked** (`.gitignore`), and **regenerated, never edited**. Deleting the folder loses nothing.

Three rules, in the order they matter:

1. **Never copy an account id or an email address out of these files into a tracked file.** The same rule
   the `secrets` folder carries, for the same reason ([`CLAUDE.md`](../CLAUDE.md)). A snapshot may be read
   freely; what it says may be *used* freely; the identifiers themselves stay here.
2. **A snapshot is evidence, not intent.** It records what AWS answered at one instant. Why a resource
   exists belongs in [`plan/decisions/`](../plan/decisions/INDEX.md), what was typed to create it belongs in
   [`log/`](../log/INDEX.md), and neither is derivable from a listing.
3. **Check the timestamp in the header before trusting a line.** If the file predates the work being
   reasoned about, re-run the script — it costs seconds and only reads.

**Before reporting anything in a snapshot as a finding, read [`AWS_STATE.md`](../AWS_STATE.md).** It holds
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
([`plan/lessons.md`](../plan/lessons.md)). Section 6 empty means every `(none)` in the file is a real none.

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
[`plan/architecture.md`](../plan/architecture.md) §4.1 and [`plan/open-questions.md`](../plan/open-questions.md)
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
nobody chose). The expected content is `INV-09` in [`AWS_STATE.md`](../AWS_STATE.md).

**Both calls answer from the Identity account** — measured on this script's first run, 2026-08-12. That
extends the read boundary Stage 1b step 4 established: a delegated administrator for *any* service may make
these Organizations reads, so the management account is needed to *change* this state and not to read it.
If a future run is denied anyway, section 4 says so and the fallback is in the script header.

## Finding an answer in `output/audit-iam-analyser.txt`

| Question | Section |
|---|---|
| Was this run in the account it was meant to be run in? | 1 — read it **first**; every other section is about whatever account answered |
| Which analyzers exist here, and since when? | 2 |
| **Is the zone of trust the organization, or just this account?** | 2 and 5 — the `type` column |
| Is anything suppressing findings? | 3 — archive rules; none is expected |
| What has been found, and in which account? | 4 — `resourceOwnerAccount` names the account the exposed resource is in |
| Did something not answer? | 6 |

**This is the one script here that does not run from a profile, and the absence is the design.** The
organization analyzer lives in **Audit** (Stage 1b step 8.2), and no project persona holds an assignment
there — [`ORGANIZATION.md`](../ORGANIZATION.md) records that as permanent. The only identity that reaches
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
| What is the organization id, and is `FeatureSet` `ALL` (which RCPs require)? | 1 — `ORG_ID`, printed as a named variable because it is the value `aws:ResourceOrgID` and `aws:PrincipalOrgID` are compared against, and what `render.sh` puts in place of `<ORG_ID>` |
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
Log Archive and Audit hold no project persona, so they are read from CloudShell (`./aws/account-bpa.sh -`)
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

## The four written for Stage 2, and the one thing they have in common

**Written 2026-08-15**: `org-delegation.sh`, `import-ids.sh`, `tf-backends.sh` and `quotas.sh`.
[Stage 2](../plan/stages/stage-02-terraform-foundation.md) is the first stage that has to **feed an
AWS-generated identifier back into a command** rather than read it, and that is a different job from every
snapshot above. A snapshot tolerates a stale line because a human reads it and notices; **an import id is
pasted into a state file, and a wrong one produces an orphan and a create rather than an error.** So the
three Stage 2 scripts are stricter about one thing than the rest of this folder: each of them says out loud
what it is *not* authoritative about — `import-ids.sh` owns the id and not the Terraform address,
`org-delegation.sh` owns the delegation's scope and not whether a write will land, `tf-backends.sh` owns
what is there and not what should be.

**One defect was found and fixed in an existing script at the same time.** `org-policies.sh` §1 listed ids
for `SERVICE_CONTROL_POLICY` only and reduced the RCP to a presence check, so **three of the ten attached
documents had no id in any snapshot** and existed only in the 1c log. All four types now carry theirs.

## Adding a script here

Keep the shape, so that one file explains all of them:

- **Read-only.** A script that changes something does not belong in `aws/`.
- **One profile per script**, named at the top, with the reason that profile can see what it sees — and
  **name the SSO user behind it in the table above**, since a profile is a *(account, permission set)* pair
  and the user is a second fact, not a restatement of it.
  **`AZs.sh`, `account-bpa.sh` and `declarative-ec2.sh` are the exceptions, and they are what an exception
  has to look like:** in all three, the subject is a *per-account* fact whose meaning is the comparison
  **between** accounts — an AZ name→ID mapping is only interesting next to another account's, and a setting
  that is right in five accounts and unset in the sixth is the sixth account's hole. A single-profile version
  would answer nothing. All three pay the rule back by printing the caller ARN of every profile in section 1
  — which is what naming one profile at the top exists to make visible. Multi-profile is not a licence; it is
  for a script whose subject is the difference between accounts.
- **Output to `aws/output/<script-name>.txt`**, one file per script, `mkdir -p` its own folder.
- **Print the command above its output** — `show` in `list-identities.sh` — so any line can be re-derived
  by hand, and prefer `--output table` over post-processing.
- **Share arguments through shell variables** (`MGMT_ID`, `ROOT_ID`, `IDS`, `INST`), printed as
  `NAME=value` where they are set, so a reader can re-run any later command.
- **Log every failed call into a final section** rather than letting it read as an empty result.
- **Number the sections** and list them in the header, then add the row to the table above and to the
  question table.

---

*Project root: [`README.md`](../README.md) · CLI recipes run by hand: [`AWS-CLI.md`](../AWS-CLI.md) ·
What was done by hand: [`log/INDEX.md`](../log/INDEX.md)*
