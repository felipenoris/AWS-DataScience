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

Run any of them from anywhere; each one `cd`s to the repository root itself:

```bash
./aws/list-identities.sh
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

## Adding a script here

Keep the shape, so that one file explains all of them:

- **Read-only.** A script that changes something does not belong in `aws/`.
- **One profile per script**, named at the top, with the reason that profile can see what it sees.
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
