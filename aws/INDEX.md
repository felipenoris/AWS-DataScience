# `aws/` — index

**Read-only scripts that photograph what is actually deployed in AWS, and the text snapshots they
produce.** Nothing here creates, changes or deletes a resource, and nothing here is infrastructure code —
that is `terraform-live/` from Stage 2 on.

Why this exists: [`GENERAL_PLAN.md`](../GENERAL_PLAN.md) and `plan/` say what *should* be there, the
[`log/`](../log/INDEX.md) files say what was *done by hand*, and these snapshots say what AWS *reports right
now*. Each answers a different question, and the three disagreeing is itself information.

## The scripts

| Script | Profile it runs as | Writes | Captures |
|---|---|---|---|
| [`list-identities.sh`](list-identities.sh) | `awsds-infra-identity` (Identity account, IAM Identity Center delegated administrator — D10) | `output/list-identities.txt` | The Organization: management account id, root and its enabled policy types, the whole OU tree, every account. The directory: Identity Store instance, groups, users, group memberships. The entitlements: permission sets with what each grants, and every assignment triple. |
| [`AZs.sh`](AZs.sh) | **every** `awsds-*` profile in `~/.aws/config`, or the ones named as arguments — the one script here that is not single-profile, see below | `output/AZs.txt` | The availability-zone **name → zone ID** mapping each account reports, one listing per account, the mappings side by side, and a check on whether they agree. |
| [`org-trusted-access-services.sh`](org-trusted-access-services.sh) | `awsds-infra-identity` by default; takes another profile as its argument, or `-` to run with no profile at all — inside CloudShell on Management | `output/org-trusted-access-services.txt` | Which AWS services hold **trusted access** across the organization, which account is each one's **delegated administrator**, and the `access-analyzer` registration on its own. |
| [`audit-iam-analyser.sh`](audit-iam-analyser.sh) | **no profile — CloudShell on the Audit account**, as `AWS Control Tower Admin`. Takes a profile as its argument if one ever exists there; see below | `output/audit-iam-analyser.txt` | The IAM Access Analyzer analyzers of that account and Region: type (the **zone of trust**), status, tags, archive rules, findings — and a check that there is exactly one, `ORGANIZATION`, `ACTIVE`. |

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

## Adding a script here

Keep the shape, so that one file explains all of them:

- **Read-only.** A script that changes something does not belong in `aws/`.
- **One profile per script**, named at the top, with the reason that profile can see what it sees.
  **`AZs.sh` is the one exception, and it is what an exception has to look like:** the comparison *between*
  accounts is the measurement, so a single-profile version would answer nothing. It pays the rule back by
  printing the caller ARN of every profile in section 1 — which is what naming one profile at the top exists
  to make visible. Multi-profile is not a licence; it is for a script whose subject is the difference
  between accounts.
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
