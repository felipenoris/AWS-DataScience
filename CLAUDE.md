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

`terraform` **1.16.6**, the `aws` client, `uv` **v0.12.13**, `jq`,
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
- A module tag is repository-global and never moves (`terraform-changes.md`, Recipe B). The next
  version is read from `git ls-remote --tags origin` at the moment of tagging, never from memory: a
  peer may have taken it.
- **The Terraform binary is one per laptop, and every session's.** The laptop and the deploy image both run
  1.16.6 since 2026-10-25 (`v0.3.0`, the deploy runner replaced 20:40 UTC). A laptop upgrade comes after the
  image's rebuild, never before: a state written by a newer Terraform is refused by the image's older one in
  every pipeline job that reads it (Lesson 76), and the slices the pipeline reads are the application and
  orchestration slices, `staging/egress`, `production/workloads-egress`, and both targets' `data/`,
  `sagemaker/`, `foundation/` and `workloads/`.

### What the app refuses

The desktop app decides which sessions start and which writes Claude runs. Each row is a measurement,
and the stage logs hold the refusals.

- **Starting a session.** The app starts one only on a turn the user's own message began (measured
  2026-10-18). A turn begun right after `/compact` is refused, and so are a request the user sends
  mid-turn and one sent over Remote Control, where a proposed card does not show either. The tasks then
  run as subagents in worktrees of their own, at the user's choice, and open their own PRs.
- **A refused write.** The session the user authorizes in its own chat runs it, and the authorization
  names the act: a blanket authorization and a question (*"você pode executar?"*) were both refused.

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

The orchestrating session ran each of the first three itself, on the user's authorization in its own
chat. Let through on 2026-11-11: reads, a RAM association, a candidate SCP's life on `Policy Test`, and
every apply and `create-project` the user named.

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
| Anything Databricks: how it deploys on AWS, its notebook and terminal, Lakeflow Jobs and pipelines, Unity Catalog, its AI stack, bundles and the promotion model, read against the requirements for the comparison with SMUS | [`docs/DATABRICKS.md`](docs/DATABRICKS.md), opening with the names that changed in 2025 and 2026 |

#### GitLab, applications and the promotion

| Task | Read |
|---|---|
| Anything GitLab: the host and its session (`make gitlab-up`/`gitlab-down`, the order with the hub and the tunnel), how a host is built from nothing, a fresh host's initial setup, a `gitlab.rb` change reaching the host, the leaves and their re-issue, trusting the root on a laptop, the backup and the restore, the runner's token, SAML's inputs | [`docs/plan/runbooks/gitlab.md`](docs/plan/runbooks/gitlab.md): §S the pieces, §U up and down, §P the installation, §I the initial setup, §R the refresh, §C the certificates, §B backup and restore, §K the runners, §G the gates project, §M the image projects and the mirror, §A SAML, §V the instruments |
| Anything about an application on the `app-etl` template, for a data scientist or the infrastructure user | [`docs/plan/runbooks/sagemaker-application.md`](docs/plan/runbooks/sagemaker-application.md): §A how to read it, the running example and the vocabulary, §O the pieces, §Q who does what, §R the repository, §L the GitLab project, §D the loop in Sandbox, §E the tests, §M the manifest and the CI/CD CLI, §I the image, §C the code a job and a worker run, §G the Glue jobs, §W the workflows and the lint's rules, §P the pipeline job by job, §T the release and the promotion, §S the infrastructure a second application needs in this repository, §X operating and monitoring it in Production, §V the readings, §B its data in each stage and the lake, §N the reach, §K Production data in Sandbox, §Z standard and specific |
| The first promotion: the sittings that close Stages 8, 9 and 10, in order and command by command, from the proofs that need nothing up to the governed warehouse | [`docs/plan/runbooks/promotion.md`](docs/plan/runbooks/promotion.md): §0 with the environment down, §H the hub and GitLab, §P Production (Stage 9's proof job), §T the tag, §W the warehouse, §V the data release, §N the next release and the order of what is left (§N.6), §Q after the quotas, §R the readings that end every sitting |

### Current position

The chain is Sandbox → Staging → Production: no Development account, ever, and interactive compute is
Sandbox only. D1-D41 are closed; D41 item 2 is reopened since 2026-10-31 (Stage 19 decision 6 (b)). Gates:
`make check`, `make check-ou`. Whether anything is up is read with `make status`, never from this file:
every sitting ends at zero burn, and Stage 19's pass 4 found nothing up on 2026-11-11.

Before asking the user anything, read
[`docs/plan/waiting-on-the-user.md`](docs/plan/waiting-on-the-user.md), and remove a row in the sitting
that takes it. It holds every decision and act that is the user's, the sittings that need the environment
up with what each closes, and the dated deadlines.

#### Stages

Done: 0, 1a, 1b, 1c, 1d, 2, 3, 4, 5a, 6a, 6b, 6c, 6i, 7, 16 and 18. Not started: 13, which waits on the
domain name from the user, and 15, which nothing blocks and whose decisions 1-4 are the user's.

| Stage | State | What comes next |
|---|---|---|
| 5b, the Sandbox warehouse | Passes 0-3 applied 2026-09-20 | A warehouse sitting: the `max_query_execution_time` test and the `enable_large_strings_opt_in` re-plan. The bill's half of verification x after the free trial ends on 2026-12-19. The user's: decision 9, when to spend the trial |
| 6d, Unified Studio's remainder | Steps 3, 4, 8 and 9 closed, step 2 but 2.4's after half. Decision 15 (b) applied 2026-10-30: `test-experimentation` holds the `SageMakerAIDomain` pilot, the house image pinned | The user's: decision due 16 (the blueprint as every Sandbox project's standard, then step 2.7), decision 9 (step 10, the Kiro CLI door), the 1.1 and 1.2 attempts. A Sandbox sitting: 5.1, 6.1 (viii), 7.5's monitored half, 7.6, 7.7, 8.8's tail |
| 6e, Claude Code on Bedrock | A session answered from a space on 2026-09-12 (Haiku 4.5, the `bedrock-runtime` endpoint). Held by PR #108 | The user's: the three Claude 5.5 model agreements (decision 17), decisions 11 and 13. Then 6.4's token volume and 8.3's budget notification |
| 6f, the catalog over the lake | Decision 1 (b), a pilot of SMUS's native flow: step 11 done to 11.11 (2026-10-27), `curated.trades` published by `governed-lake` and subscribed by `eighth-experimentation`. Decisions 2 to 6 taken | The user's: step 2's portal acts, 11.12's rollback residue |
| 6g, access by identity | Applied 2026-09-17, 1.4 closed on both profiles | 2.4's Athena read, which the user re-specifies. Decision 1's proxy-host replacement at the next `production/proxy/` apply, in a hub sitting |
| 6h, the Redshift connection | Passes 0-2 done: one project writes and reads the schema `lab` through the Data page and through JupyterLab | The user's: decision 3 (`lineageSync`) and decision 8 (how a second project is admitted). Then a warehouse sitting: the negatives 5.1 and 5.2b, 0.4's portal half, 6.4 |
| 8, the pipelines | Passes 0-3 done; pass 4 ran with Stage 10's passes: the first promotion on 2026-10-24 (`v0.3.3`), `v0.4.6` in Production since 2026-10-26. Every decision taken | Release T, the next tag (`v0.4.7`), once the user's GitLab acts land: `runbooks/promotion.md` §N.8.2. What is left, in order: §N.6 |
| 9, the deployment targets | Passes 1, 2, 3 and 5 applied; the producer path (2.4), the governed warehouse and its datashare (9.1 to 9.7) run and read to 2026-10-30. Every decision taken | The warehouse and backup sitting, 2026-11-22 to 2026-11-25 (`promotion.md` §N.8.3): `EXC-13`'s Production half. The quota cases, still `CASE_OPENED`. What is left, in order: §N.6 |
| 10, orchestration | Passes 1-3 done in Staging and Production; the schedules read starting both chains unattended (6.1, 2026-10-25). Every decision taken | At the release sitting (`promotion.md` §N.8.2, step 12): xx's second half and decision 11's Staging half. What is left, in order: §N.6 |
| 11, data protection | Pass 0 read; pass 1's data cells filters written, creating nothing. The threat model holds `TM-01`..`TM-30` | The user's: decision 12 (the filtered principal), `TM-17`, decisions 1, 2, 5 and 9. The internal-access analyzer, created after a 1st and deleted before the next: it bills on each 1st |
| 12, observability and FinOps | Both observability slices applied 2026-10-18; `OB-3` passes in Sandbox and fails in Production by design (`EXC-19`). The bill reads above D12's ceiling: 53.31 USD in August and 74.48 in September | A hub sitting: the three `[D]` hosts' alarm actions. The user's: decisions due 1 and 3, D12's fired revision trigger and its budget notification |
| 14, Sandbox vending | The pre-vend half done 2026-10-18 (`./aws/vending.py`, `VN-1`..`VN-6`); the rest blocked on the account quota | The user's: the account quota and D34's rung |
| 17, machine learning in Sandbox | Pass 0 in progress; `MLflowApp` and `AmazonBedrockKnowledgeBase` enabled, `ml-demo-mlflow` created, five models enabled, the playground answering (7.3) | A Sandbox sitting with `GROUPS=mlflow`: 1.4 and 1.6, then passes 2-5. The user's: decisions 5, 6, 7, 10 and 12 |
| 19, a data product on SMUS's native path | Decision 6 (b), the AWS model: a deployment project per target. Pass 1 run 2026-11-10. Pass 4 owes nothing more with nothing up: `deploy-staging` and `deploy-production` created, the full-table flag off in both targets and `awsds-deploy-staging` an owner of `deploy-staging` since 2026-11-12 (4.7, `DT-13` passing). Release F, the CLI's legs (4.9 to 4.11), written 2026-11-12 and its grants that need nothing up applied the same day; both `chains/` slices unapplied. Decisions 1 to 24 taken, 7 and 8 moot | The user's: pass 2's portal acts, and `awsds-deploy-prod`'s membership once its first pipeline run has created its group. Then release T (the `test` stage retired, its template the tree of `36bcf916`: `promotion.md` §N.8.2) and release F's promotion sitting (§N.8.4) |

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
- **The release in Production is `v0.4.6`**: the four `release.tf` and the orchestration slices' defaults
  name it, and a by-hand apply on a stale default rolls the workflows back. `production/orchestration`'s
  three schedules stay `DISABLED` between sittings.
- **The house image** is `awsds-sandbox-dev-env` version 11, `default-v0.10.0` (2026-10-26); its `NO_PROXY`
  literal is the 73 names of `vpc-egress-v0.19.0`.
- **Orchestration is MWAA Serverless only**, provisioned MWAA denied at the root. The SageMaker
  application is the deployable unit (D41): the CI/CD CLI deploys it in Sandbox and bundles it, the pipeline
  deploys the bundle, and a Step Functions machine per chain with a Scheduler schedule starts the workflows.
  The tooling is `awsds-workflows` (`serverless-workflows.md` §T). A deploy from a Sandbox space needs
  `sandbox/egress` raised with `GROUPS=mwaa`.
- **The warehouses** bill 1.44 USD per query-hour at 4 RPU and nothing idle, with no pause, so `make down`
  is the guarantee, and the ratchet past 4 RPU never returns. Sandbox's compute rises only with
  `make up ENV=sandbox GROUPS=redshift` or an `ONLY=` naming it. The free trial absorbs the bill to
  2026-12-19 in Sandbox and to 2027-01-21 in Production. The connection's `lineageSync` runs daily at
  03:43 UTC and fails (`EXC-17`). The procedures are `redshift-connection.md`.
- **Security Hub is paused since 2026-10-09** (`EXC-14`): `awsds-fsbp-only` keeps the service with no
  standard, and the revert is `security-hub.md` §R.
- **The SCP battery** read `ou` 52 as expected, 0 unexpected, 5 not measured on 2026-11-11, and `root`
  25, 0, 1 on 2026-10-30. The probes read `ResourceLimitExceeded` as authorized. SageMaker job quotas are
  above zero in Staging and Production since 2026-10-24.
- **Bedrock**: the retention mode `none` is declared in all 17 Regions and frozen by Stage 6e's 7.5;
  `claude-opus-5` and `claude-sonnet-5` are refused for this account (`EXC-08`).
- **Module pins** are read from the callers (`grep -rn '?ref=' terraform-live`). Abandoned on origin and
  never pinned (Lesson 46): `vpc-egress` v0.9.0, v0.11.0, v0.12.0 to v0.14.0, and `vpc-v0.3.0`.
- **The VPN** has two client profiles, monitored and split-tunnel, on one key (`vpn.md` §C7). With the
  tunnel down, macOS's system proxy breaks the `aws` CLI, and `NO_PROXY='*'` is the override. A CLI login
  answered in a browser that holds a portal session as another user ends that session, so `aws/login.py`
  passes `--no-browser`.

A row of the table holds a state and what comes next; a bullet holds a fact that changes how a session
acts. What ran, with its pipeline numbers and its dates, belongs in the stage file's `Status` row and in
the log. `./scripts/check-plan-refs.py` fails this section past 12 KB.

### Standing rules

- `-input=false` on every plan and apply (Lesson 47).
- Never pipe a command whose exit code matters (Lesson 46).
- A module change is exercised by planning a caller, never by `validate`.
- `-refresh=false` is forbidden on `sandbox/data/`, where SMUS is a Lake Formation admin (OQ 24).
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
| Write or read a check, a probe or a proof | 2, 13, 20, 21, 22, 24, 26, 30, 31, 50, 54, 62, 71, 77, 78 |
| Write a policy, a grant or a role, or say what a principal can do | 5, 11, 14, 17, 18, 28, 29, 66, 67, 70, 72, 75 |
| Move, rename or share something across accounts, or borrow a session | 3, 9, 10, 25, 48 |
| Change Terraform, a module, a host or the toolchain | 4, 8, 27, 33, 35, 47, 49, 51, 58, 59, 64, 65, 68, 69, 73, 76, 79 |
| Call an AWS API, a console wizard or a managed service | 16, 23, 36, 39, 60, 61, 63, 74 |
| Touch the network, the proxy or a client | 40, 42, 43, 44, 45, 53, 55, 56 |
| Run a command or write a script | 46, 47, 52 |
| Write the plan, a record or a decision, or read a vendor page | 1, 6, 7, 12, 15, 19, 32, 34, 37, 38, 41, 57 |

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
