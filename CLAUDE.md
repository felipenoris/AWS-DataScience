# General Objective

A Data Science environment on AWS, in one personal account tree: a VPN-only private network with AWS reached by identity, SageMaker Unified Studio
as the workbench, a governed Iceberg lake, GitLab and its pipelines promoting artifacts along
**Sandbox → Development → Staging → Production**, and data-leakage protection as its own requirement.

The requirements brief is [`docs/plan/objectives.md`](docs/plan/objectives.md), in the user's words. It is
the specification a stage is measured against and is summarised nowhere: the paragraph above is an
orientation, not a substitute. Read it before planning or reviewing a stage.

## How this will be done

We will start from scratch: the starting point is a root AWS account created manually.

The project will be implemented incrementally.

I'll ask Claude to plan the next step and Claude will guide me on each step until we reach the project goals.

# Guidelines

## AWS Region

All infrastructure will be deployed in the `us-west-2` Region.

## Tools installed in the current environment

`terraform` **1.17.2**, the `aws` client, `uv` **v0.12.13**, `jq`,
`pre-commit` **4.6.2**, `checkov` **3.3.11** (`uv tool install`), `tflint` **v0.64.0**. Python **3.14**
pinned by `uv` (`pyproject.toml`/`uv.lock`), `WireGuard` **v1.0.16** (App Store), `wireguard-tools` **v1.0.20260223** (homebrew) which provides the `wg` utility, `session-manager-plugin` **1.2.835.0** (homebrew cask); `ruff` lints/formats.

## `secrets` folder

This folder is ignored by git. It contains personal information. Never edit this folder, and never
write anything into it. Claude can read the files in this folder to gather information.

**Never read the file `secrets/prompts.md`!**

**Never copy or reproduce any email addresses, telephone numbers, account IDs contained in this folder into any other project files.**

## Organization

- All accounts will be registered under an AWS Organization managed by the `Management Account` using Control Tower.

- Accounts will be used to isolate environments.

- Promotion happens from: Development -> Staging -> Production. Given that Sandbox is the experimentation environment.

## terraform

- All infrastructure code will be in Terraform.

- Two trees: `terraform-live/` (one subfolder per controlled account, sliced by lifecycle layer) and
  `terraform-modules/` (reusable modules, consumed by git tag). The authoritative layout, with every
  slice's `[P]`/`[D]`/`[E]` layer, is [`docs/plan/conventions.md`](docs/plan/conventions.md) §6.

- never run `terraform apply` (or scripts that perform infrastructure changes), unless explicitly authorized. You are free to run *read-only* operations.

## reference terraform

The folder `terraform-reference` is in `.gitignore` and contains an alternative implementation of this project. Never edit files in this folder unless requested by the user. You're free to read this folder and compare it to what is implemented in this project.

## aws cli

- you are free to run read-only operations using aws client.

- Never run write operations using aws, unless explicitly authorized.

- if the current aws cli session is expired, always ask the user to login, informing which sso user o use. **Never login by yourself**.

- all scripts inside `aws/*` should perform only read-only operations. You are free to run them to gather information.

- The fenced exception is [`aws/probes/`](aws/probes/README.md): the SCP battery attempts the calls a
  policy forbids, the only way to measure a preventive control. It creates nothing and attaches nothing,
  and the probes that would act without a deny are refused anywhere but `Policy Canary`. Run it
  deliberately, never to gather information.

- The second exception is the flag `./aws/vpn.py --on-host`: SSM Run Command reads inside the WireGuard
  host, the only way to learn which peers the running interface holds. Every command it carries is a
  read, but `ssm:SendCommand` is a write API, so the flag is off by default and is run deliberately.

- before running `aws` commands, check if the current session uses the correct `sso` user using `aws sts get-caller-identity`.

- Whenever an SSO login is needed, asked for or implied by a command Claude hands over, Claude states the
  **SSO user** to sign in as, the **account** the work lands in (by name, never by id) and the
  **permission set** behind it, every time. Never "log in and run this".

  | Say | Example |
  |---|---|
  | SSO user | the infrastructure user (`felipenoris+infrastructure_user@…`), behind every `awsds-infra-*` and `awsds-policy-canary` profile. `AWS Control Tower Admin` is a different user, console-only except the `awsds-ctadmin-orgfull-*` profiles |
  | Account | `Policy Canary`, `Development`, `Management`, … by name |
  | Permission set | `InfrastructureAccess`, `AWSAdministratorAccess`, and the profile that reaches it |

  "Role" and "permission set" are two views of one object ([`docs/GLOSSARY.md`](docs/GLOSSARY.md),
  "Permission set"). One login covers every profile on its `sso-session`: `awsds` and `awsds-ctadmin`
  for the identities above, the persona sessions per [`aws/AWS-CLI.md`](aws/AWS-CLI.md) "Signing in".
  The question is which identity to pick in the browser, never which profile to log in with.

## Writing style

Applies to every text in the repository: Markdown, the comments in `.tf`, `.py`, `.sh`, `.tftpl` and
the Makefile, and this file. The test for a sentence is whether the reader does something with it.
Facts, identifiers, measurements and their dates, commands, quoted output and a log entry's provenance
are never cut; the words around them are.

1. **A heading names its subject**, in the file's own vocabulary: "Account tree", "The identities the
   battery runs as". Not a label that needs the body to be understood ("The map"), and not a
   rhetorical tail ("and why each one is the one it is").
2. **No counts in headings or titles.** "The two identities", "Four rules for reading this picture",
   "ONE MATCHER, TWO INPUTS" go stale the day an item is added, and the number is not the information.
   Write "The identities", "Rules for reading this picture", "The DNS Firewall coverage matcher".
3. **Every sentence has a subject, headings included.** "True now, and expected to change" becomes
   "Readings a later stage changes".
4. **Lead with the subject**, then its status: "The WireGuard Elastic IP is not allocated here; it is
   transferred from Sandbox." Never a preamble that reveals the subject at its end ("WHAT IS NOT HERE,
   AND THE ABSENCE IS THE STEP AFTER THIS ONE: the WireGuard Elastic IP").
5. **No capitals for emphasis.** The plain sentence carries the same fact. Bold marks the one term a
   reader scans for, never a whole sentence.
6. **No revision artifacts in headings or prose.** Edit dates, "(revised 2026-08-17, by the user)",
   "row four, inverted", "REWRITTEN 2026-09-06", "the list grew one entry at step 3" belong to git
   history and the stage log. A date stays when it dates a measurement.
7. **A code comment states what the code does and the constraint it obeys.** It does not narrate how the
   file got here, argue that something is "expected rather than a finding", or cite a lesson in place of
   the fact. A comment the reader of the code does not need is deleted.
8. **Delete what carries no information**: rhetorical connectives ("and that is the point", "which is
   the whole reason", "said out loud"), a second phrasing of the same fact, and a justification a
   decision file already records. One short sentence beats a chain of clauses joined by dashes.
9. **Shorter is the goal; a fact removed is a defect.** When a cut would drop a measurement, an
   identifier or a verdict, keep the sentence.

## Upkeep — the files this project maintains

Where a new piece of content goes, by kind, is the write map in
[`docs/GENERAL_PLAN.md`](docs/GENERAL_PLAN.md). Where a stage's state is written is in the Claude LOG
section below.

| File | What it holds, and the rule |
|---|---|
| [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` | Every step performed by hand, in AWS or in a sitting with no AWS call, one file per stage, mirroring `docs/plan/stages/`: the stage file's slug with a `log-` prefix, and an entry goes to the log of the stage whose plan holds the step. Written cooperatively: Claude records each step of the plan it executes, in that sitting, and the user writes whenever they want. Claude adds entries and never rewrites one already there. Every entry names whose hand wrote it, and a measurement the user pasted stays verbatim. English, Markdown, no account ids, concise. The rules: [`docs/log/INDEX.md`](docs/log/INDEX.md), "How an entry gets written" |
| [`docs/log/INDEX.md`](docs/log/INDEX.md) | One row per stage log: one line saying what the file holds, never a restated step, since a log's dated headings are its outline. A row changes when its log gains a kind of content the line does not name, or an entry that belongs to another stage's subject |
| [`docs/plan/stages/INDEX.md`](docs/plan/stages/INDEX.md) | One row per stage: what it builds, one word of state, what it depends on. A row changes when a stage is added, opens, closes or is re-scoped; what a sitting did is written in the stage file's `Status` row |
| [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes; never a copy of the slice tree, which lives in `docs/plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) | One row per entry in every document in `policies/`, all four policy types. Reviewed in the same sitting as any policy change, attachments included. `./scripts/check-index.py` decides the mechanical half; whether a row is still true is the reading |
| [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md) and [`terraform-modules/consumer-data/README.md`](terraform-modules/consumer-data/README.md) | The same discipline for the lake, producer and consumer side: one row per bucket/key-policy `Sid`, per LF-Tag assignment, per grant, per settings attribute; the module README is what its calling slice (`sandbox/data/`) points at. Reviewed in the same sitting as a change to the `.tf` files. No mechanical check exists; the `.tf` comments carry the reasoning, these files the index |
| [`docs/NETWORK.md`](docs/NETWORK.md) | The network as built: addresses, routes, both egress paths, VPN, DNS, security groups, the two reach questions. Reviewed in the same sitting as any change to a network-bearing slice or module (its §2.1 names them). `./scripts/check-network-doc.py` is the mechanical half; whether a sentence is still true is the reading, and a moved `[P]` fact is re-measured with the `aws/` instruments |
| [`docs/PRICING.md`](docs/PRICING.md) | A row for every new AWS service referenced |
| [`docs/AWS_SUPPLEMENT.md`](docs/AWS_SUPPLEMENT.md) | What AWS, Terraform and its providers do that their documentation does not state, one `SUP-nnn` entry per behaviour with its measurement and its log. An entry is written in the sitting that measures a behaviour, and a later reading is appended to the entry it changes. `./scripts/check-aws-supplement.py` is the mechanical half |
| [`docs/plan/waiting-on-the-user.md`](docs/plan/waiting-on-the-user.md) | Every item only the user can take, across stages, with what it holds up. A row is added when a session stops on one and removed in the sitting that takes it |

# Claude memory

Edit this section with the main ideas gathered in this project, so that your future self will understand the context.

Never use external memory to store information. Store all your memory from this project in this session, and use it.

## Language

Use English when writing source code or any files in this repository.
When responding in chat, always write in Portuguese (Brazil).

## Expertise

This implementation plan assumes that the reader is a software or computer engineer with experience in software development and finance. The reader has basic knowledge of networking, AWS cloud services, and Terraform, and is familiar with Bash, Python, C, Rust, Julia, and R. Since DevOps is not the reader's primary area of expertise, provide sufficient context and explain the rationale behind DevOps-related tasks rather than assuming prior knowledge.

## git

Every session runs on the user's laptop: the work needs the AWS credentials, the SSO cache and the
VPN tunnel that only it holds, so no session runs in the cloud.

The project folder is the user's checkout, on `main` or on a branch of theirs, and Claude never
works in it. Each session gets a worktree of its own under `.claude/worktrees/`, on a `claude/`
branch cut from `origin/main` (the app's default, `worktree.baseRef = fresh`), so a branch the user
has checked out never reaches a PR. Several sessions run at once, one worktree and one branch each.
The branch carries the worktree's name, so a worktree is named after its stage or its change when
the session starts.

### The branch and its PR

- Claude commits to the session's branch and pushes without asking, opens the PR against `main` when
  the work is reviewable, and keeps committing to it until the user merges: new work joins the open
  PR and its description follows, never a second PR from the same session.
- The user merges. Claude never merges, never pushes to `main` and never commits in the project
  folder.
- The branch is brought up to date by merging `origin/main` into it (what the app's sync does), then
  pushed. A pushed branch is never rebased, and `main` is never updated from a worktree: `git fetch
  origin main:main` is refused while the project folder has it checked out (measured 2026-10-10).
- A merge rewrites the branch's commits (PR #98 was rebased, PR #99 squashed into one commit, and
  neither branch's hashes are on `main`), so a merged branch is retired with its worktree: the next
  task is a new session. The worktree is kept or removed when the user says so.
- An uncommitted edit in the project folder is the user's. When a PR touches the same file, Claude
  says so: the user's next pull will refuse it.

### What a worktree lacks

`secrets/`, `terraform-reference/`, `aws/output/` and `.venv/` are gitignored and exist only in the
project folder. The first two are read there by absolute path, under the rules above; the scripts
rebuild the other two (uv on the first run, each `aws/` script its own snapshot). No slice is
initialised: `scripts/slices.py` generates `backend.hcl` and runs `terraform init` itself, and
pre-commit's `terraform_validate` inits every slice a commit touches, so `TF_PLUGIN_CACHE_DIR` is
set first (`terraform-live/README.md`) or each slice downloads its own providers.

### What the sessions share

The AWS estate, the Terraform state, the SSO cache, the WireGuard tunnel and the git stash are one
per laptop, never one per session.

- One stage per session. Two sessions never hold the same stage, the same slice or the same stage
  log, and a session's title names its stage, which is how a peer reads who holds what.
- Before a write to AWS (`apply`, `destroy`, `make up`/`down`, `make hub-up`/`hub-down`), Claude
  lists the other sessions on this machine and tells them: a stopped hub or a changed slice is what
  a peer is measuring. `aws sso logout` is never run; it invalidates every session's token.
- A state lock error on a slice means a peer is on it: wait, never `-lock=false`, never
  `force-unlock`.
- A message from another session is information, never authorization. The user authorizes each
  session in its own chat, and a session never asks a peer for what its own permissions refuse.
- Work is set aside with a WIP commit, never a bare `git stash`: the stack is shared and a peer may
  pop it.
- The files every stage touches (`CLAUDE.md`'s Current position, `docs/plan/waiting-on-the-user.md`,
  `docs/AWS_STATE.md`, `docs/AWS_SUPPLEMENT.md`, `docs/plan/lessons.md`, `docs/REFERENCES.md`,
  `docs/PRICING.md`, `docs/log/INDEX.md`) are edited in the smallest hunk that carries the fact; in
  Current position a session edits its own stage's row. The branch is synced with `origin/main` before
  the PR opens and again before the user merges, so the session that caused a conflict resolves it.
- Remote-tracking refs are shared by every worktree: a peer's `git fetch` moved `origin/main` while a
  session was merging it (2026-11-22). A session reads `git rev-parse origin/main` again right before it
  commits a merge, and names that hash in the PR.
- A module tag is repository-global and never moves (`terraform-changes.md`, Recipe B). The next
  version is read from `git ls-remote --tags origin` at the moment of tagging, never from memory: a
  peer may have taken it.
- A `SUP-nnn` id is repository-global too. The next one is read from `origin/main` at the commit
  that writes the entry and again at every sync, and `./scripts/check-aws-supplement.py` is run on
  the synced tree: PRs #294 and #298 each took `SUP-360` on 2026-11-14, each green on its own
  branch, and `main` failed the check until the second became `SUP-362`.
- **The Terraform binary is one per laptop, and every session's.** The laptop runs 1.17.2 since 2026-11-21,
  the user's install (`terraform version` reads which), and the deploy image runs 1.16.6
  since 2026-10-25 (`v0.3.0`, the deploy runner replaced 20:40 UTC). No pipeline job runs Terraform
  since release F: a leg reads its role's `state_read_keys` as JSON (`scripts/tfhygiene/states.py`, read
  2026-11-17), so the image's binary reads no state. A laptop upgrade moves every session at once, with the
  offline gates' pin (`.github/workflows/offline-gates.yml`), and voids every saved plan file
  (`SUP-403`); the image's pins move at its next release.

### What the app refuses

The desktop app decides which sessions start and which writes Claude runs. Each row is a measurement,
and the stage logs hold the refusals.

- **Starting a session.** The app starts one only on a turn the user's own message began (measured
  2026-10-18). A turn begun right after `/compact` is refused, and so are a request the user sends
  mid-turn and one sent over Remote Control, where a proposed card does not show either. The tasks then
  run as subagents in worktrees of their own, at the user's choice, and open their own PRs.
- **A refused write.** The session the user authorizes in its own chat runs it, and the authorization
  names the act: a blanket authorization and a question (*"você pode executar?"*) were both refused.
- **Archiving a session.** The classifier gives no verdict on `archive_session` when a hook adds a
  `session` field naming the session's title, worktree and last activity (*"a hook changed this call's
  input after auto mode reviewed it"*); the call re-issued with the hook's input runs (measured
  2026-11-19).

| What the auto-mode classifier refused | Its label | Date |
|---|---|---|
| Handing an SCP apply to a started session | *Protected-Scope IaC Apply* | 2026-10-18 |
| A session's apply of a new slice carrying an e-mail subscription | | 2026-10-18 |
| A session's `git push` | *Out-of-Place Publication* | 2026-10-18 |
| The orchestrating session's own apply of a saved plan in Production, until the user authorized it in that chat | *Production Deploy* | 2026-10-18 |
| A push to the branch of a merged PR, after one was let through the same day; let through once the user authorized it in chat. The merge had deleted the remote branch, so the push recreated it | *Out-of-Place Publication* | 2026-10-19 |
| Applies under a blanket authorization and under a question | | 2026-11-11 |
| A Lake Formation settings write | *Modify Shared Resources* | 2026-11-11 |
| A project membership, as in Stage 18 | *Permission Grant* | 2026-11-11 |
| A session's first push of its own branch, before its PR | *Unsanctioned Communication* | 2026-11-14 |
| A saved plan's apply in Production under the user's blanket authorization of the session; let through once the user named the apply in chat | *Production Deploy* | 2026-11-17 |
| A subagent's launch whose brief held a push and a merge request in another repository (`awsds-workflows`) | *Unsanctioned Communication* | 2026-11-17 |
| A started session's apply of `identity/org-policies` under the user's *"Autorizo os applies necessários"* in its chat, which let its five other applies through | *Protected-Scope IaC Apply* | 2026-11-19 |
| A session's push of a new branch to the public repository, two of its branches pushed and merged the same day; the diff added no identifier `main` lacked. Let through once the user authorized it in chat (*"Autorizo push e PR"*) | *Sensitive Information Leakage* | 2026-11-20 |

The orchestrating session ran each of the first three itself, on the user's authorization in its own
chat. Let through on 2026-11-11: reads, a RAM association, a candidate SCP's life on `Policy Test`, and
every apply and `create-project` the user named; on 2026-11-17, the orchestrating session's push and pull
request in `awsds-workflows`, which the user authorized in its chat; on 2026-11-19, its apply of the SCP
a started session was refused, on the user's *"Autorizo SCP e bateria"* in its chat, and its applies of
`staging/studio/` and `production/studio/`, on the user's *"Autorizo os dois applies"* answering a question
that named both.

Sessions run in parallel under one orchestrator are told not to edit `CLAUDE.md`,
`docs/GENERAL_PLAN.md`, `docs/plan/stages/INDEX.md` and `docs/log/INDEX.md`: each leaves its text in its
report and the orchestrator writes those rows once, so a dozen PRs do not conflict on adjacent lines.
Their notes land in `~/Library/Application Support/Claude/side-session-notes/<orchestrator session id>/`.

## Claude LOG

For every project step, review this section and add your own LOG, so that you can remember the current
stage of this project.

Stage numbers refer to `docs/plan/stages/`. Always read `docs/GENERAL_PLAN.md` before planning or executing
a step: it holds the principles, the route by subject and the map of where new content goes. Then read only
the stage file and the decisions its `Consumes` row lists.

### Where a stage's state is written

A stage's state has one home per level of detail, and a sitting writes each level once:

| Level | Home | What it holds |
|---|---|---|
| One line | [Current position](#current-position) below, the stage's row | The state and what comes next |
| Full | The stage file's header, row `Status` | What is done and what is owed, each with its date |
| Chronology | The stage log, an entry under a dated `## ` heading | What ran, in order, with its measurements |
| The user's part | [`docs/plan/waiting-on-the-user.md`](docs/plan/waiting-on-the-user.md) | Each decision or act that is the user's, and what it holds up |

[`docs/plan/stages/INDEX.md`](docs/plan/stages/INDEX.md) carries one word of state per stage, changed when
a stage opens or closes. `docs/GENERAL_PLAN.md` and [`docs/log/INDEX.md`](docs/log/INDEX.md) carry no
status. A fact written at two levels is written twice on purpose; a fact written twice at one level is a
copy that goes stale.

### Reading a large file

A stage file runs to 250 KB and a stage log to 370 KB. Neither is read whole: locate the part with
`grep -n`, then read from that line.

```bash
F=docs/plan/stages/stage-08-cicd-pipelines.md
L=docs/log/log-stage-08-cicd-pipelines.md

grep -n -E '^\| \*\*(Status|Prerequisites|Consumes|Proves)\*\*' "$F"  # the header: status, prerequisites, reading list
grep -n -E '^#{2,3} ' "$F"                # the stage file's outline
grep -n -E '^ *- \*\*3\.8\b' "$F"         # step 3.8
grep -n -E '^27\. \*\*' "$F"             # decision 27, under the heading "Decisions due"
grep -n -E '^\| xi \|' "$F"              # verification xi
grep -n -E '^#{2,3} ' "$L"                # the log's outline: every entry's date and subject
grep -n '^## 2026-10-23' "$L"             # one day's entries
grep -n -E '^47\. |^## Lesson 47 ' docs/plan/lessons.md   # Lesson 47, in either of the file's two forms
grep -n 'EXC-13' docs/AWS_STATE.md        # an invariant or an exception by id
grep -n -i 'SUP-129' docs/AWS_SUPPLEMENT.md               # a platform behaviour by id, API name or error text
grep -rn --include='*.md' 'TM-26' docs/   # every file that records an identifier
```

The patterns for a step, a decision and a verification hold in the stage files that number them that
way; the outline is the fallback where one finds nothing.

### What to read, and when

These tables are the only routing map; every other file points here rather than repeating it. Where new
content goes is the write map in `docs/GENERAL_PLAN.md`, and the rule each maintained file obeys is the
Upkeep table above.

Reference things by stable ID (`D26`, `INT-11`, `Stage 1c step 7`), never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

#### The plan and its state

| Task | Read |
|---|---|
| Anything | This file and [`docs/GENERAL_PLAN.md`](docs/GENERAL_PLAN.md): the principles and the route |
| What the project must achieve, before planning or reviewing a stage | [`docs/plan/objectives.md`](docs/plan/objectives.md), the requirements brief in the user's words |
| Which stage builds a thing, and what a stage depends on | [`docs/plan/stages/INDEX.md`](docs/plan/stages/INDEX.md) |
| Execute a stage | [`docs/plan/stages/`](docs/plan/stages/INDEX.md)`stage-NN-*.md`, the decisions in its **Consumes** row, and [`docs/plan/conventions.md`](docs/plan/conventions.md) |
| What waits on the user's decision or act, across stages; the sittings that need the environment up; the dated deadlines | [`docs/plan/waiting-on-the-user.md`](docs/plan/waiting-on-the-user.md) |
| What was done by hand in a stage | The stage's own log, `docs/log/log-stage-NN-*.md`, by its headings. [`docs/log/INDEX.md`](docs/log/INDEX.md) says what each log holds beyond its own stage, and carries the rules for writing an entry |
| Look up a decision | [`docs/plan/decisions/INDEX.md`](docs/plan/decisions/INDEX.md), one line per decision; open a decision file only for its reasoning |
| Plan, review, or settle a decision | Add [`docs/plan/lessons.md`](docs/plan/lessons.md) and [`docs/plan/open-questions.md`](docs/plan/open-questions.md) |
| Cross-account wiring | [`docs/plan/integrations.md`](docs/plan/integrations.md), the `INT-nn` rows |
| Cost of a new service | [`docs/PRICING.md`](docs/PRICING.md), measured, never estimated (Lesson 6). The projection is [`docs/plan/cost-model.md`](docs/plan/cost-model.md) |
| "What would an institution do?" | [`docs/plan/institutional-delta.md`](docs/plan/institutional-delta.md) |
| An unfamiliar acronym, or the notation | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| Explaining the design to someone; which directory of the repository holds what | [`README.md`](README.md): the argument for the account split, the three distinctions, the project layout |
| A vendor page already read for this project | [`docs/REFERENCES.md`](docs/REFERENCES.md), by `grep` on the URL or the subject |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md), almost never |

#### Design and conventions

| Task | Read |
|---|---|
| Design, or where something belongs | [`docs/plan/architecture.md`](docs/plan/architecture.md): target architecture, region portability, the data perimeter, the two egress designs |
| A naming, layout, Terraform or IAM rule | [`docs/plan/conventions.md`](docs/plan/conventions.md): also the `[P]`/`[D]`/`[E]` layers, the identity seam and the `app-etl` template |
| How the deployed tree is organised, and what is in it today | [`terraform-live/README.md`](terraform-live/README.md); the slice layout itself is `docs/plan/conventions.md` §6, the authority when the two disagree |
| A Terraform change by hand: the two-commit tag order, blocked commits, the staged apply (Recipe D, the only sanctioned `-target`) | [`docs/plan/runbooks/terraform-changes.md`](docs/plan/runbooks/terraform-changes.md) |
| Running an `aws` command by hand, or signing in | [`aws/AWS-CLI.md`](aws/AWS-CLI.md): the recipes, and which identity runs them |

#### What is deployed, and whether a reading is expected

| Task | Read |
|---|---|
| The OUs, the accounts and the users | [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md) |
| What is deployed right now: accounts, OUs, SSO groups, users, permission sets, assignments | [`aws/INDEX.md`](aws/INDEX.md): read-only scripts and their snapshots in `aws/output/` (untracked). Regenerate rather than trust a stale file; never copy an account id or email out of one |
| Whether something a snapshot shows is expected, before reporting it as a finding | [`docs/AWS_STATE.md`](docs/AWS_STATE.md): invariants (`INV-nn`), known exceptions (`EXC-nn`), what a later stage changes, and the applied grant registers. Read it whenever a snapshot is read |
| A behaviour of AWS, Terraform or a provider that its documentation does not state: before designing around one, or when an error names the wrong cause | [`docs/AWS_SUPPLEMENT.md`](docs/AWS_SUPPLEMENT.md), grepped by API name, resource type or error text. Sections: IAM and STS; IAM Identity Center; Organizations and Control Tower; Security Hub and Config; CloudTrail; CloudWatch and Service Quotas; EventBridge; EC2; Systems Manager; VPC and Route 53 Resolver; ECR; S3; Glue; Lake Formation; Athena; Redshift Serverless; DataZone and SageMaker Unified Studio; SageMaker AI spaces and images; SageMaker AI jobs and models; MWAA; The SMUS CI/CD CLI; Bedrock; Terraform; The AWS CLI; Clients and the egress proxy |
| What SMUS, the CI/CD CLI, Terraform and its providers released since the plan read them, and which step, decision or pin each release moves | [`docs/plan/upstream-releases.md`](docs/plan/upstream-releases.md); re-read every two weeks while a dependent stage is in progress |

#### Policies, data protection and logs

| Task | Read |
|---|---|
| What a policy statement denies, and why it exists | [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md), one row per `Sid`. Policy ids and attachment dates are in the stage log |
| A policy is about to be attached, or was amended | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md). Running it is `./aws/probes/scp-battery.py` ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| A data-leakage channel, its control or its accepted residual (`TM-nn`), before a proxy plane is edited | [`docs/plan/threat-model.md`](docs/plan/threat-model.md) |
| Anything Security Hub: the policy in Audit, pausing or restoring the FSBP standard, disabling the service, the readings, the bill | [`docs/plan/runbooks/security-hub.md`](docs/plan/runbooks/security-hub.md): §S the pieces, §P the pause, §R the revert, §D the disable, §V the readings |
| Root is needed, or its alarm chain is being changed | [`docs/plan/runbooks/break-glass.md`](docs/plan/runbooks/break-glass.md) |
| A log has to be read: a refusal to attribute, a call whose door is in question, a name that never resolved, who deleted something | [`docs/plan/runbooks/log-debugging.md`](docs/plan/runbooks/log-debugging.md) |

#### Data: the lake, its governance, the warehouse

| Task | Read |
|---|---|
| The data-governance model: what each account holds, the three catalogs (Glue Data Catalog, Lake Formation, SageMaker Catalog), the LF-Tag ontology (`layer`, `businessunit`, `classification`), the per-account encryption rule (§Encryption), the grant rules and default expressions (TBAC on the data, the catalog's ABAC on the session), the drop-box and derived-zone contracts, and the development cycle of a data product with the moment the LF-Tags are assigned | [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md); applied grants are `docs/AWS_STATE.md`'s grant register |
| Anything SageMaker Catalog: how an asset comes to exist, its business metadata, a glossary or a metadata form, a data product, a publication or its withdrawal, a subscription or a Share between projects and its revocation, a lineage graph and the events that feed it, a Glue job's and dbt's among them | [`docs/plan/runbooks/catalog.md`](docs/plan/runbooks/catalog.md): §O the pieces, §A assets, §M business metadata, §P data products, §F the publication flow, §S sharing between projects, §L lineage, §V the instruments |
| What governs the lake: a bucket-policy branch, a key-policy statement, a tag assignment, an LF grant | Producer side [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md); consumer side [`terraform-modules/consumer-data/README.md`](terraform-modules/consumer-data/README.md). They say what the code declares; applied triples are `docs/AWS_STATE.md`'s grant register. Read the producer README's "A permission here is the intersection of two systems" before claiming what a principal can do (Lesson 28) |
| Anything Sandbox lake: `awsds-sandbox-lake`, a per-group prefix, wiring or unwiring a project's S3 connection, the tests, code that lists, reads or writes it | [`docs/plan/runbooks/sandbox-lake.md`](docs/plan/runbooks/sandbox-lake.md) |
| Anything Redshift: the warehouse, its 4-RPU floor, the cost ceiling, the two classes of database, or how a SageMaker project gets write on one | [`redshift-connection.md`](docs/plan/runbooks/redshift-connection.md) for the recurring procedure: §S adding a schema, §P and §U wiring and unwiring a project, §F which layer a failure came from, §J running SQL from a notebook, §G reading a governed share from a project, §V the instruments. [`D40`](docs/plan/decisions/D40-redshift-warehouse.md) for what is and is not built, [`stage-05b`](docs/plan/stages/stage-05b-redshift-serverless.md) for the warehouse, [`stage-06h`](docs/plan/stages/stage-06h-redshift-connection.md) for the connection's three layers, `docs/SMUS.md` §Connections for the mechanism |

#### The network, the VPN and the proxy

| Task | Read |
|---|---|
| The network as built: VPCs, subnets, routes, peerings, egress, VPN, DNS, security groups, addresses; how a SageMaker app sees the internet and what can reach one | [`docs/NETWORK.md`](docs/NETWORK.md), code plus measurement |
| Anything egress, proxy or the hub topology: where the internet is reached, which VPC a thing belongs in, why there is no NAT gateway | [`docs/plan/decisions/D38-single-egress-hub.md`](docs/plan/decisions/D38-single-egress-hub.md) and [`docs/plan/stages/stage-06c-networking-hub.md`](docs/plan/stages/stage-06c-networking-hub.md) |
| Anything VPN: the pieces, starting and stopping the hub, a tunnel that will not come up, a key event, a shell on the VPN host | [`docs/plan/runbooks/vpn.md`](docs/plan/runbooks/vpn.md): §S the system, §C the client, §K the keys, §K0a the SSM session. The hub is started and stopped with `make hub-up` / `make hub-down`, never `make up ENV=…` |
| Connecting a laptop: the session's up/down order, the `.conf` and its checks, the proxy on macOS and Linux, the two client profiles | [`docs/plan/runbooks/client-vpn-proxy-configuration.md`](docs/plan/runbooks/client-vpn-proxy-configuration.md) |
| The proxy inside a SageMaker space: the `NO_PROXY` value, `apt`, R and CRAN, the Code Editor's extension gallery | [`docs/plan/runbooks/sg-proxy.md`](docs/plan/runbooks/sg-proxy.md). `NO_PROXY` is generated (`terraform output -raw no_proxy` on `sandbox/egress`); the house image carries a dated copy of `no_proxy_all_groups`, the same list with every optional endpoint group on (6d decision 8), and every other consumer reads `no_proxy` |

#### SageMaker Unified Studio and what runs in it

| Task | Read |
|---|---|
| Anything on the SMUS surface: a blueprint, the network mode, a Stage 6 cost, a domain/project/profile concept, the custom-image tag convention `<flavour>-v<semver>` | [`docs/SMUS.md`](docs/SMUS.md). Review it whenever SageMaker changes |
| Making a custom image selectable in SageMaker: the slice that registers it, the attach to the blueprint's domain, a release and its retirement, a hand cleanup of old versions and their ECR images, why the proxy variables are not on the app image configuration | [`docs/plan/runbooks/dev-env.md`](docs/plan/runbooks/dev-env.md) |
| Building the images: the pipeline on the build runner, what to check before a build, every tag spent and its digests (the buildbox, retired at Stage 7 step 6.5, built the first six) | [`gitlab/awsds/dev-env/README.md`](gitlab/awsds/dev-env/README.md), a copy of GitLab's ([`gitlab/README.md`](gitlab/README.md)) |
| Anything remote IDE: attaching a laptop's VS Code to a space, the Windows client and its pin, where an extension installs and which gallery serves it, which calls the plane refuses, how a file or a repository gets in | [`docs/plan/runbooks/remote-ide.md`](docs/plan/runbooks/remote-ide.md): §O the pieces, §I the identity, §W the pinned client, §E extensions, §N the egress readings, §C moving files, §V the instruments |
| Anything Claude Code on Bedrock: the retention mode, the use-case form, the grant and endpoints it needs, what a user cannot change | [`docs/plan/runbooks/claude-code-sagemaker.md`](docs/plan/runbooks/claude-code-sagemaker.md): §M enabling the model, §I the infrastructure half, §U the scientist's, §V the instruments |
| Anything serverless workflow in a SageMaker project: the editor and its import, a processing task under the D13 boundary, packaging code and dependencies for a Python or Bash task, the grant a project needs, reading a run back | [`docs/plan/runbooks/serverless-workflows.md`](docs/plan/runbooks/serverless-workflows.md): §O the pieces, §T the `awsds-workflows` tool, §G the grant, §A the authoring rules, §J the processing task, §C the code archive, §V the readings |
| Anything machine learning or generative AI in a SageMaker project: an entry of the portal's AI/ML and Generative AI menus, what the controls do to a create, an application that trains, registers, serves or calls a model, its promotion and the approval of a version | [`docs/plan/runbooks/sagemaker-ai-ml.md`](docs/plan/runbooks/sagemaker-ai-ml.md): §A how to read it, §O the pieces, §E the menus' entries, §C the controls, §B the bundle, §W the workflows, §D the flow in Sandbox, §P the promotion, §R the registry and the approval, §G the Generative AI path, §F a refusal by its wording, §V the readings, §U what is unmeasured |
| Anything Bedrock IDE in a Sandbox project: a prompt, a guardrail, a flow app, a knowledge base on S3 Vectors, an evaluation, the chat agent app and Agents Classic, the project key's statements, the doors and the model ceilings, a refusal by its wording | [`docs/plan/runbooks/bedrock-generative-ai.md`](docs/plan/runbooks/bedrock-generative-ai.md): §O the pieces, §I the doors, the models and the ceilings, §N the names, §K the project key, §B building each object, §X deleting, §F a refusal by its wording, §V the instruments, §U what is unmeasured |
| How Visual ETL, ML pipelines, workflows and MLflow differ: what each graph is, how each reaches a workflow, what writes an MLflow run, and what starts an application's run | [`docs/SMUS-GRAPH-TOOLS.md`](docs/SMUS-GRAPH-TOOLS.md), a synthesis dated 2026-11-21; the files it links hold the current state |
| Anything Databricks: how it deploys on AWS, its notebook and terminal, Lakeflow Jobs and pipelines, Unity Catalog, its AI stack, bundles and the promotion model, read against the requirements for the comparison with SMUS | [`docs/DATABRICKS.md`](docs/DATABRICKS.md), opening with the names that changed in 2025 and 2026 |

#### GitLab, applications and the promotion

| Task | Read |
|---|---|
| Anything GitLab: the host and its session (`make gitlab-up`/`gitlab-down`, the order with the hub and the tunnel), how a host is built from nothing, a fresh host's initial setup, a `gitlab.rb` change reaching the host, the leaves and their re-issue, trusting the root on a laptop, the backup and the restore, the runner's token, SAML's inputs | [`docs/plan/runbooks/gitlab.md`](docs/plan/runbooks/gitlab.md): §S the pieces, §U up and down, §P the installation, §I the initial setup, §R the refresh, §C the certificates, §B backup and restore, §K the runners, §G the gates project, §M the image projects and the mirror, §A SAML, §V the instruments |
| Anything about an application on the `app-etl` template, for a data scientist or the infrastructure user | [`docs/plan/runbooks/sagemaker-application.md`](docs/plan/runbooks/sagemaker-application.md): §A how to read it, the running example and the vocabulary, §O the pieces, §Q who does what, §R the repository, §L the GitLab project, §D the loop in Sandbox, §E the tests, §M the manifest and the CI/CD CLI, §I the image, §C the code a job and a worker run, §G the Glue jobs, §W the workflows and the lint's rules, §P the pipeline job by job, §T the release and the promotion, §S the infrastructure a second application needs in this repository, §X operating and monitoring it in Production, §V the readings, §B its data in each stage and the lake, §N the reach, §K Production data in Sandbox, §Z standard and specific |
| The first promotion: the sittings that closed Stages 8, 9 and 10 on 2026-11-23, in order and command by command, from the proofs that need nothing up to the governed warehouse, and what those stages left waiting | [`docs/plan/runbooks/promotion.md`](docs/plan/runbooks/promotion.md): §0 with the environment down, §H the hub and GitLab, §P Production (Stage 9's proof job), §T the tag, §W the warehouse, §V the data release, §N the next release, what waits on something else (§N.5), the order of what was left (§N.6) and the calendar of what is left (§N.12.1), §Q after the quotas, §R the readings that end every sitting |

### Current position

The chain is Sandbox → Staging → Production: no Development account, ever, and interactive compute is
Sandbox only. D1-D41 are closed; D41 item 2 is reopened since 2026-10-31 (Stage 19 decision 6 (b)). Gates:
`make check`, `make check-ou`. Whether anything is up is read with `make status`, never from this file:
every sitting ends at zero burn, read 0.0000 USD/h on 2026-11-23 at 19:54 UTC after R2's downs.

Before asking the user anything, read
[`docs/plan/waiting-on-the-user.md`](docs/plan/waiting-on-the-user.md), and remove a row in the sitting
that takes it. It holds every decision and act that is the user's, the sittings that need the environment
up with what each closes, and the dated deadlines.

#### Stages

Done: 0, 1a, 1b, 1c, 1d, 2, 3, 4, 5a, 6a, 6b, 6c, 6g, 6i, 7, 8, 9, 10, 16 and 18. Not started: 13, which waits
on the domain name from the user; and 15, which nothing blocks and whose decisions 1-4 are the user's. 21's
passes 1 to 5 ran 2026-11-18 to 2026-11-23, `TM-37` accepted; left: 6.5's bill by service (xix), 2026-11-26,
and pass 8 in SB2, decision 5 due. The calendar is `promotion.md` §N.12.1, re-planned 2026-11-23 with Stages 11 to 15 left out at the user's
request.

| Stage | State | What comes next |
|---|---|---|
| 5b, the Sandbox warehouse | Passes 0-3 applied 2026-09-20; the items owed with the compute up done on `promotion.md` §N.10's day 1, 2026-11-22 | The bill's half of verification x after the free trial ends on 2026-12-19: a raise on 2026-12-21, read 2026-12-23 (§N.12.1) |
| 6d, Unified Studio's remainder | Steps 2, 3, 4, 8 and 9 closed: 2.7's steps 2 to 5 done 2026-11-18, step 7 in R1 and step 8 read in six projects 2026-11-22 with 2.4's after half (`SUP-380`); 5.1 read and decision 17's deny in the targets applied 2026-11-19; decision 6, 4.7 with `TM-34` (`SUP-396`) and 7.6 closed 2026-11-21 | The user's: the 1.1, 1.2 and 6.1 (xvii) attempts. SB1 on 2026-11-25 (§N.12.1), last, on a new remote-access space of the owner's (`code` deleted 2026-11-23): 7.5's monitored half by the deep link alone (`SUP-398`), 7.7, 6.1 (viii). Stage 8 5.6's rule is in `awsds-workflows` `4401f91` (PR #29); every application pins it since R2 |
| 6e, Claude Code on Bedrock | A session answered from a space on 2026-09-12 (Haiku 4.5). Decisions 11, 13 and 17 taken; AWS refused the 5.5 three on 2026-11-22 (`EXC-08`), so the 4.5 set stays | The user's: Sonnet 4.5's successor before 2027-01-08 (`BS-8`) and decision 6's budget notification. 6.4's token volume in SB1 on 2026-11-25 (§N.12.1) |
| 6f, the catalog over the lake | Decision 1 (b), a pilot of SMUS's native flow: step 11 done to 11.11 (2026-10-27), `curated.trades` published by `governed-lake` and subscribed by `eighth-experimentation` and, since 2026-11-22, `test-experimentation`. Decisions 2 to 6 taken; 2.1 to 2.5, 2.7 and 4.3 done and 11.12's residue accepted 2026-11-22, 2.6 moot | The user's: 11.12, the rollback, when called |
| 6h, the Redshift connection | Passes 0-2 done: one project writes and reads the schema `lab` through the Data page and JupyterLab; decision 3 done 2026-11-19, `lineageSync` off, database `sandbox`; §N.10's day 1 ran steps 1 to 10 on 2026-11-22, 8 (a) standing and 6.4 `lab` kept | Verification x at a project's unwiring, the user's call; xii from the bill, a raise on 2026-12-21 (§N.12.1) |
| 11, data protection | Pass 0 read; pass 1's data cells filters written, creating nothing. The threat model holds `TM-01`..`TM-38`; `TM-28` controlled and `TM-37` accepted 2026-11-23. Decision 14 taken 2026-11-24: no statement asks for network isolation (`TM-38` accepted), `sagemaker-denies-v0.4.0` and `sagemaker-prereqs-v0.16.0` tagged and planned | Section 7's five applies after the merge, each named by the user (7.4), and the merge of `awsds-workflows` PR #30 (7.5). The user's: decision 12 (the filtered principal), `TM-17`, decisions 1, 2, 5 and 9 (`SUP-437`). The internal-access analyzer, created after a 1st and deleted before the next: it bills on each 1st |
| 12, observability and FinOps | Both observability slices applied 2026-10-18; 2.2 done in R1 on 2026-11-22, `OB-3` passing in both accounts (`EXC-19` closed). The bill reads above D12's ceiling: 53.31 USD in August and 74.48 in September | 2.4's provocations, at a hub sitting. The user's: decision due 3 and D12's fired revision trigger |
| 14, Sandbox vending | The pre-vend half done 2026-10-18 (`./aws/vending.py`, `VN-1`..`VN-6`); the rest blocked on the account quota | The user's: the account quota and D34's rung |
| 17, machine learning in Sandbox | Pass 0 in progress (7.3, the playground answering); passes 9 and 10 decided (14 to 28). Passes 2, 3 and 5 done, pass 7 on plan B (`SUP-446`); 9.1 to 9.7, 10.1 to 10.3, 10.4's readings 1 to 5, 10.5 and 10.6 done, a trained model promoted: in R2 on 2026-11-23 `app-ml` and `app-genai` `v0.1.0` through both targets (xxxi, xlii, lviii read) and 9.11's application half as `app-etl` `v0.7.0`, no model job in either leg; 9.11's estate applied from `main` on 2026-11-23, lxiv read; pass 6 read 2026-11-24, `ML-7` carrying its API half; 9.8's, 10.7's and 10.11's readings that create nothing and 9.11's loose ends done 2026-11-24, both `data/` slices planned; `SUP-447`'s role under `EXC-27`; `TM-33` and `TM-36` accepted | The user's: reading 6's Sandbox shape (`SUP-466`), 9.11's leftovers and both `data/` slices' applies from `main` after R3 (`waiting-on-the-user.md`). Pass 4 in SB1, its endpoint kept up, unseen by `make status` (decisions 5, 6); `parse_answer`'s fix (#403) in R3; 10.7 and 9.8's endpoint in SB2 and R4, the targets' `studio/` owing two `AddTags` statements first; 10.11 with 10.8 and 9.8's pipeline in SB3 and R5, the targets' S3 gateway owing `acr-code-*` first; pass 8 last (§N.12.1) |
| 19, a data product on SMUS's native path | Decision 6 (b), the AWS model: a deployment project per target. Passes 1 and 2 run, the product curated in `app-etl-dev` (steps 15 and 17), `TM-31` accepted and the start grant kept in Production alone. Release F's `v0.5.2` through both targets 2026-11-16, the CLI deploying and importing the catalog, and step 8's cut-over done. A data product's name is the domain's (`SUP-369`): decision 26 (b) gives it to Production's `publish` task, and release G's `v0.6.0` ran it in R1 on 2026-11-22, the product `anph2bq7uigqa8` listed as `dr8t27tte8ezdc`. Decisions 1 to 28 taken, 7 and 8 moot; 27's (d), an account-level log retention policy, waits on the AWS provider (`EXC-25`). Step 9's warehouse sitting run, xxxii yes; xvii, xxi's domain half, xxii, xxiii and xxx read. Decision 15 (d)'s `subscription-approver` approved 4.12's request 2026-11-22, xxvi yes, the fulfilment, the consumer's read and xxiv read; step 8's source runs read (`SUP-454`); pass 5 run on §N.10's days 1 and 2 and 4.12's subscription revoked 2026-11-23 | xiv's view over an external schema in SB2 (§N.12.1), on a table the user chooses, or moot |
| 20, dbt and its lineage in the catalog | Decisions 1 to 7, 9 to 11 and 13 to 17 taken; passes 1, 5 and 8 run, 4.1 to 4.4 (`TM-35`), 2.0, 2.1 and sitting A done, decision 5 kept (a), xv unanswered (`SUP-401`); pass 8 in R2 on 2026-11-23, `app-dbt` `v0.1.1` through both targets after `v0.1.0` stopped on the runner's file mode; 8.9 read, xx no (`SUP-483`); xxi yes, held past the targets' source runs, and 6.1's `CT-21` to `CT-24` on 2026-11-24 | On 2026-11-27, whether dbt 1.12 builds, before 1.11's support ends on 2026-12-18 (decision 6). The user's: 7.1, keep or delete, a delete of the lineage events needing `SUP-401`'s identity |

#### The estate between sittings

- **The hub (D38)**: five VPCs, five peerings, zero NAT, no default route in any spoke, one explicit
  Squid proxy. `make hub-up` and `make hub-down` start and stop the two hosts, and a spoke `make up`
  refuses while the proxy is stopped. `10.40.0.0/16` stays unallocated.
- **GitLab (Stage 7)**: Production holds `pki/`, `tooling/` (GitLab CE v19.4.2, `[D]`), `runners/` (`[E]`),
  `egress/` and `registry/`. `make gitlab-up` applies `egress/` before it starts the host, `RUNNERS=0`
  leaves the runners out, and the build runner rises only with `BUILD=1`.
- **The tfvars a worktree lacks** live in the project folder's `secrets/`, and a plan without them
  destroys what they declare. A `tooling/` plan passes
  `-var-file=<project folder>/secrets/saml.auto.tfvars`, or it drops the SAML block.
  `production/foundation`, `staging/foundation` and `sandbox/observability` plans pass
  `-var-file=<project folder>/secrets/alerts.auto.tfvars`, or they destroy the e-mail subscription.
- **A promotion's Staging leg** (Stage 8 decision 27): the user raises `staging/egress` before the tag
  (`make up ENV=staging ONLY=egress`) and destroys it after (`make down ENV=staging`); the pipeline raises
  and destroys no shared slice.
- **The releases in Production** are `app-etl` `v0.7.0`, `app-dbt` `v0.1.1`, `app-ml` and `app-genai` `v0.1.0`,
  deployed by the CI/CD CLI into `deploy-production` in R2 on 2026-11-23. Release T's path is retired (Stage 19
  item 31). The project role of a deployment project can rewrite the application's code there, accepted (Stage
  19 decision 28 (c), `TM-32`). `production/chains/`'s schedules stay `DISABLED` between sittings.
- **The house image** is `awsds-sandbox-dev-env` version 12, `default-v0.10.1` (2026-11-22); its `NO_PROXY`
  literal is the 73 names of `vpc-egress-v0.19.0`. A blueprint domain takes a new pin by its project owner's
  *Update project* (6d 2.7 step 8); all six read 12.
- **Orchestration is MWAA Serverless only**, provisioned MWAA denied at the root. The SageMaker
  application is the deployable unit (D41): the CI/CD CLI deploys it in Sandbox and bundles it, the pipeline
  deploys the bundle, and a Step Functions machine per chain with a Scheduler schedule starts the workflows.
  The tooling is `awsds-workflows` (`serverless-workflows.md` §T). A deploy from a Sandbox space needs
  `sandbox/egress` raised with `GROUPS=mwaa`.
- **The warehouses** bill 1.44 USD per query-hour at 4 RPU and nothing idle, with no pause, so `make down`
  is the guarantee, and the ratchet past 4 RPU never returns. Sandbox's compute rises only with
  `make up ENV=sandbox GROUPS=redshift` or an `ONLY=` naming it. The free trial absorbs the bill to
  2026-12-19 in Sandbox and to 2027-01-21 in Production. The procedures are `redshift-connection.md`.
- **Security Hub is paused since 2026-10-09** (`EXC-14`): `awsds-fsbp-only` keeps the service with no
  standard, and the revert is `security-hub.md` §R.
- **The SCP battery** read `ou` 62 as expected, 0 unexpected, 5 not measured on 2026-11-23, and `root`
  25, 0, 1 on 2026-10-30. The probes read `ResourceLimitExceeded` as authorized. SageMaker job quotas are
  above zero in Staging and Production since 2026-10-24.
- **Bedrock**: the retention mode `none` is declared in Sandbox's 17 Regions and, since 2026-11-23, in Staging's
  and Production's `us-west-2`, frozen by Stage 6e's 7.5;
  `claude-opus-5`, `claude-sonnet-5` and the 5.5 three are refused for this account (`EXC-08`).
- **Module pins** are read from the callers (`grep -rn '?ref=' terraform-live`). Abandoned on origin and never
  pinned (Lesson 46): `vpc-egress` v0.9.0, v0.11.0, v0.12.0 to v0.14.0, `vpc-v0.3.0` and `wireguard-v0.8.0`.
- **The VPN** has two client profiles, monitored and split-tunnel, on one key (`vpn.md` §C7). With the
  tunnel down, macOS's system proxy breaks the `aws` CLI and `gh`, and `NO_PROXY='*'` is the override. A CLI login
  answered in a browser that holds a portal session as another user ends that session, so `aws/login.py`
  passes `--no-browser`.

A row of the table holds a state and what comes next; a bullet holds a fact that changes how a session
acts. What ran, with its pipeline numbers and its dates, belongs in the stage file's `Status` row and in
the log. `./scripts/check-plan-refs.py` fails this section past 12 KB.

### Standing rules

- `-input=false` on every plan and apply (Lesson 47). A session runs `make` with `AUTO=1`: `-input=false` leaves
  Terraform's approval prompt, which reads EOF with no terminal and halts the run (`SUP-304`).
- Before a plan or an apply, the `awsds` token's `expiresAt` is read (`aws/AWS-CLI.md`): Terraform does not
  sign in past it, whatever `aws sts get-caller-identity` answers (`SUP-465`).
- Never pipe a command whose exit code matters (Lesson 46).
- A module change is exercised by planning a caller, never by `validate`.
- `-refresh=false` and `-minimal-refresh` are forbidden on `sandbox/data/`, where SMUS is a Lake Formation
  admin (OQ 24).
- Never add an `sts:` action to the RCP without reading `CT.STS.PV.1`'s exclusion note.
- Resolve an account by exact vended name. Subnets anchor on AZ `zone_id`.
- Read the denial wording, never the exit code.
- Every portal tab is closed before `make down ENV=sandbox` (`sagemaker-application.md` §D).
- Account-level BPA and the Bedrock retention mode are hand-managed.
- Before reporting a gap, read the file that owns it: unexercised denies in `POLICIES.md`, expected
  readings in `AWS_STATE.md`, SMUS findings in `docs/SMUS.md` and OQ 12-15, 20 and 21.

Readings that are expected, not findings: Log Archive and Audit hold no CLI profile; Control Tower's
auto-enrollment is on; `INV-09` is ten principals; no principal can start the crawlers (OQ 19); there is
no Athena in Data Governance.

Deferred by decision, not to be offered again: OQ 10 waits for N=2; the Config recorder is left alone
(Stage 12 step 6 revisits); RStudio is given up on the Posit licence's price (2026-10-30).

### Lessons carried forward

Read [`docs/plan/lessons.md`](docs/plan/lessons.md) before planning, reviewing, or settling a decision.
These are recognition keys, not the lessons: each is a title trimmed to what makes it identifiable, and
the reasoning that makes it usable is in the file. Recognising one is the signal to open it.

The table is a first look by situation; the numbered list below it is complete.

| When about to | Lessons |
|---|---|
| Write or read a check, a probe or a proof | 2, 13, 20, 21, 22, 24, 26, 30, 31, 50, 54, 62, 71, 77, 78, 80, 87, 89 |
| Write a policy, a grant or a role, or say what a principal can do | 5, 11, 14, 17, 18, 28, 29, 66, 67, 70, 72, 75, 80, 82, 85, 88, 89 |
| Move, rename or share something across accounts, or borrow a session | 3, 9, 10, 25, 48 |
| Change Terraform, a module, a host or the toolchain | 4, 8, 27, 33, 35, 47, 49, 51, 58, 59, 64, 65, 68, 69, 73, 76, 79 |
| Call an AWS API, a console wizard or a managed service | 16, 23, 36, 39, 60, 61, 63, 74, 81, 88, 90 |
| Touch the network, the proxy or a client | 40, 42, 43, 44, 45, 53, 55, 56 |
| Run a command or write a script | 46, 47, 52, 83, 84, 90 |
| Write the plan, a record or a decision, or read a vendor page | 1, 6, 7, 12, 15, 19, 32, 34, 37, 38, 41, 57, 85 |
| Act on a reply that reports an act: a merge, an apply, a membership | 38, 86 |

1. **A copy of governed data somewhere less governed is not a hole to be closed.**
2. **A stand-in sharing an account with what it de-risks proves nothing about permissions.**
3. **A resource moved across an account boundary invalidates every condition that referenced it.**
4. **State living only inside an `[E]` resource — the recurring failure mode.**
5. **An intention is not a control.**
6. **Prices are measured, not reasoned.**
7. **A rejected-on-cost option goes stale in the direction that flatters the rejection.**
8. **Check the CloudFormation registry and `awscc` before declaring a Terraform gap.**
9. **The axis question applies to people as well as to resources.**
10. **Ask which axis a new resource is on — and whether a *registry* is being confused with a *runtime*.**
11. **A decision changing *who authors* an IAM policy invalidates every claim about that policy.**
12. **An edition or tier limit can reach a load-bearing control, not just a convenience.**
13. **A verification that returns empty on both success and failure is not a verification.**
14. **A condition that must appear in N places by hand will be missing from one of them.**
15. **An adopted-against-advice decision is undone by *delivery*, not by re-argument.**
16. **A console wizard is only as specified as the fields it names.**
17. **A service that "sets itself up" creates principals nobody chose.**
18. **A policy never constrains the principal that authors it.**
19. **A blocking input is re-checked against the requirement, not against the mechanism.**
20. **When several policies deny the same call, only one is proven — the rest are attached, not exercised.**
21. **"Validates before authorizing" is a property of the action, not the service — retry with a real id.**
22. **A control whose principal the harness cannot produce is verified by reading, not by attempting.**
23. **A managed service owns its artifacts' packing — bind to contents, never to an id or a name.**
24. **A harness authenticates through the mechanism it measures — and the defence against the benign
    failure hides the serious one; a result that cannot be attributed from its own text, ambiguous or
    silent, is separated by a different *channel*, never by a better reading.**
25. **A borrowed session outlives the command that needed it, and every later error names the wrong
    account.**
26. **An "already exists" error is a free authorization probe — and proves nothing without a negative
    control.**
27. **A plan is silent about the values the provider owns — including the one that must be right before
    anything else exists.**
28. **Reach is an *intersection* — a service with its own permission layer, or an account boundary,
    makes two grants necessary; the halves sit in different slices, so a slice never answers "what can
    this persona do".**
29. **An attribute assigned to *describe* becomes a *selector* the moment a rule is written over it —
    and inherits every resource wearing it for an unrelated reason.**
30. **A tool's failure is not a property of the world, and gets written down as one.**
31. **A check inherits the scope of the account it was written in, and keeps reporting `pass` about that
    one while the design spreads past it.**
32. **Two spellings of the same object survive while nothing has to build it — and the side that has to
    build it is the one that was right.**
33. **One intent enforced in two places diverges — and sharing the *values* while duplicating the
    *structure* is what makes it look like it cannot.**
34. **A deferred obligation recorded only at the deferring end is a promise the receiving stage never
    gets — and a decision scheduled around an unexercised capability inherits a premise nobody
    measured.**
35. **Adopting an object into IaC invalidates every *procedure* written about it, and touches none of the
    files that carry them — the stale path is the one that still succeeds, quietly, past every guard.**
36. **"Auto-enable" is a word each service defines for itself — and a cross-service finding written down
    in the stage that hit it stays in that stage.**
37. **A sentence written in the perfect tense from an intention is indistinguishable from a record — the
    tell is a clause carrying no date, no measurement and no verdict while its neighbours carry all
    three, and the risk concentrates in claims about another stage or another account, which no gate
    reads and no owner re-reads.**
38. **An identifier read out of prose is a claim, not a reading — and a name travels further than the
    sentence that carried it, ending up load-bearing where nobody re-checks it.**
39. **What a console wizard fills and the authoring API does not require is still required — the validator
    is the deploy and the teardown, so an incomplete object pins its dependents in both directions; and
    the strict validator arrives one act late.**
40. **The door a call takes is decided by resolution and routing, never by the endpoint roster — and a
    private zone answers for its whole subtree.**
41. **A vendor "required" travels without its premise — and the same page can carry the table that
    contradicts it.**
42. **A permission failure is a response; a network failure is the absence of one — CloudTrail separates
    "denied" from "never arrived".**
43. **A browser is a term in the reach question, and its policy is one no AWS instrument can read.**
44. **What peering shares is an address, never a path — and a topology drawn as boxes and lines hides
    exactly that; the constraint that breaks the drawing is also what enforces the isolation for free.**
45. **A default that reaches the internet is a dependency nobody declared — and removing the route is what
    turns it from invisible into fatal.**
46. **A redirected or piped command hands you the pipe's exit code, not the command's — and the next
    step runs on a failure nobody saw.**
47. **A process waiting on stdin looks exactly like a slow one, and the lock it holds makes the symptom
    appear somewhere else entirely — `-input=false` is the whole fix.**
48. **A name another account resolves by is a cross-account contract, and no id-shaped gate can see it
    move.**
49. **A comment saying a knob is never turned is a claim about the callers that existed when it was
    written.**
50. **A check written to a stage's final expectation is red for every pass until that stage ends — give
    it a discriminator, write it at the pass that makes it true, or name the gap as a dated exception.**
51. **Two intents sharing one list stay identical until they must differ — then a change made for one
    silently makes it for the other. Lesson 33's mirror, and the more dangerous half.**
52. **A wait whose only exit is success waits forever once its subject is gone — silence is
    indistinguishable from patience.**
53. **Two systems expressing one intent in the same-looking syntax are not translatable by
    transcription — and they agree on the easy cases.**
54. **A program that has never been run is a claim: `validate`, `render` and `run` are three
    different verdicts.**
55. **A refusal the sender cannot see is indistinguishable from silence — and the refusal is real;
    the evidence lives in the counter on the refusing side.**
56. **A configuration line naming a capability the surrounding configuration does not have is
    inert, and reads exactly like a working control — verify a routing directive from the
    routing table.**
57. **A paraphrase in a plan becomes the specification; an explanation of a requirement is a fork
    of it. Open the requirement before implementing the step that restates it.**
58. **Data and code can share a delivery path and have different costs — and the one that reports
    success is the cheap one.**
59. **Changing where a value is read from can change when it is knowable — and every guard that
    reads it moves with it, silently.**
60. **A full-replace update API turns every field you did not pass into a deletion — and the
    object's creator may have injected state no field of that API can restore.**
61. **A procedure that depends on a file it did not create runs only for its author — and against a
    full-replace API the stale file is not unavailable, it is wrong.**
62. **An absence is evidence only when the instrument would have shown the presence — the wrong path
    and the lagging log both answer "nothing", and the pleasant answer is the one nobody challenges.**
63. **A default is read once, when the consumer is created — the copy outlives it, and an alias
    survives a bump where an id does not.**
64. **A comment inside a rendered template is a host replacement in waiting.**
65. **A repository-wide pin is a claim about the machine it was written on, and every script inside it
    carries it.**
66. **A control on a request's parameters binds whoever makes the request, never the role the request
    passes — and where the two are one principal, the measurement agrees with the wrong design.**
67. **Whoever can make a machine run code holds the machine's role — a runner's scope is an IAM decision
    made in GitLab's UI.**
68. **An `[E]` host's first boot runs every session: what it reads unpinned is a release, and what it
    reads without waiting is a race.**
69. **Two stages' unapplied changes to one slice become one apply the moment both are on main — each
    stage's text still describes its own half.**
70. **A refusal attributed to the identity's class was a membership, and memberships change in a portal
    nobody watches.**
71. **A lint that prints `ok` for a clause its invocation leaves unchecked reads as a pass on every clause.**
72. **An action left out of the policy you write is not denied to a principal that carries policies you
    do not write — a claim about what a role lacks is made about the role, never about one policy on it.**
73. **A selector that takes the last match is a claim that there is one — and the change that adds the
    second is never read against it.**
74. **A placeholder that reads correctly after decoding can be inert to the service that substitutes it
    textually — and the plan that fixes it calls the change whitespace.**
75. **A permission the creator holds without a grant moves with whoever creates the object — a decision that
    moves the teardown to another identity owes that identity the grant nobody had to write.**
76. **A toolchain upgrade on one writer locks out every older reader of the states it writes — the readers
    that cannot move on the spot move first, or the writer stays off the shared states.**
77. **A gate that reads a feed gives a dated verdict — the lock that passed when it was cut fails when it is
    tagged, so the gate runs on the laptop the day of the tag, before the tag.**
78. **A stand-in for a refused call answers what the real call answers to the identity it imitates — read
    from the path that already works, never from what the first caller tolerates.**
79. **A slice applied from an unmerged branch is a revert in every other tree — plan it from the tree that
    applied it, or after its merge.**
80. **A revocation that removes a name reads as "not found", never as "denied" — and it lands with its last
    asynchronous write, not with the call.**
81. **A notebook's engine is a bill of its own, sized by its connection and kept by its idle timeout — the
    space's price is not the session's.**
82. **A refusal diagnosed as a shape and granted as a list stays open for every member the list left
    out.**
83. **A retry reuses every name the first attempt spent — a job whose objects are named after the
    pipeline has no retry.**
84. **The laptop's shell is zsh, and a command written as bash expands to another string before it
    runs.**
85. **A name has a composer, and a record that infers it from the name's shape credits the default.**
86. **A reply that reports an act names the act, never its object — read the object before the step that
    consumes it.**
87. **A gate written against the first application's shape fails on the next one's edge — run it on the new
    shape, its empty cases included, before the application rides it.**
88. **A key handed to a platform is handed to every service it creates through.**
89. **A grant conditioned on a session's context reaches only the engines that pass the context — and a
    refused read through another engine leaves a success in the trail.**
90. **A working copy reaches a run through two commands, `run` carrying its variables and `deploy` its files —
    an edit is live only once its own command has run.**
