
# General Objective

A Data Science environment on AWS, in one personal account tree: VPN-only access, SageMaker Unified Studio
as the workbench, a governed Iceberg lake, GitLab and its pipelines promoting artifacts along
**Sandbox → Development → Staging → Production**, and data-leakage protection as its own requirement.

**The requirements brief is [`docs/plan/objectives.md`](docs/plan/objectives.md)** — the full list, in the
user's words. **It is the specification a stage is measured against, so it is summarised nowhere**: the
paragraph above is an orientation, not a substitute. Read it before planning or reviewing a stage.

## How this will be done

We will start from scratch: the starting point is a root AWS account created manually.

The project will be implemented incrementally.

I'll ask Claude to plan the next step and Claude will guide me on each step until we reach the project goals.

# Guidelines

## AWS Region

All infrastructure will be deployed in the `us-west-2` Region.

## Tools installed in the current environment

`terraform` **1.15.8**, the `aws` client, `uv` **v0.12.5**, `jq`,
`pre-commit` **4.6.2**, `checkov` **3.3.11** (`uv tool install`), `tflint` **v0.64.0**. Python **3.14**
pinned by `uv` (`pyproject.toml`/`uv.lock`); `ruff` lints/formats.

## `secrets` folder

This folder is ignored by git. It contains personal information. Never edit this folder, and never
write anything into it. Claude can read the files in this folder to gather information.

**Never read the file `secrets/prompts.md`!**

**Never copy or reproduce any email addresses, telephone numbers, account IDs contained in this folder into any other project files.**.

## Organization

- All accounts will be registered under an AWS Organization managed by the `Management Account` using Control Tower.

- Accounts will be used to isolate environments.

- Promotion happens from: Development -> Staging -> Production. Given that Sandbox is the experimentation environment.

## terraform

- All infrastructure code will be in Terraform.

- Two trees: `terraform-live/` (one subfolder per controlled account, sliced by lifecycle layer) and
  `terraform-modules/` (reusable modules, consumed by git tag). **The authoritative layout, with every
  slice's `[P]`/`[D]`/`[E]` layer, is [`docs/plan/conventions.md`](docs/plan/conventions.md) §6** — one copy, so two
  cannot drift.

- never run `terraform apply` (or scripts that perform infrastructure changes), unless explicitly authorized. You are free to run *read-only* operations.

## aws cli

- you are free to run read-only operations using aws client.

- Never run write operations using aws, unless explicitly authorized.

- all scripts inside `aws/*` should perform only read-only operations. You are free to run them to gather information.

- **The one exception, and it is fenced: [`aws/probes/`](aws/probes/README.md)** — the SCP battery has to
  *attempt* the calls a policy forbids, because that is the only way to measure a preventive control. It
  creates nothing and attaches nothing; the probes that would act without a deny are refused anywhere but
  `Policy Canary`. **Run it deliberately, not to gather information** — the difference from every other
  script in that folder.

- before running `aws` commands, check if the current session uses the correct `sso` user using `aws sts get-caller-identity`.

- **Whenever an SSO login is needed — asked for, or implied by a command Claude is about to hand over —
  Claude states three things, every time and without being asked**: the **SSO user** to sign in as, the
  **account** the work lands in, and the **permission set** behind it. Never "log in and run this".

  | Say | Example |
  |---|---|
  | SSO user | the infrastructure user (`felipenoris+infrastructure_user@…`) — behind every `awsds-infra-*` and `awsds-policy-canary` profile; `AWS Control Tower Admin` is a *different* user, console-only **until the `awsds-ctadmin-orgfull-*` profiles of 2026-08-15**, which are the only CLI it has |
  | Account | `Policy Canary`, `Development`, `Management`, … — by **name**, never by id |
  | Permission set | `InfrastructureAccess`, `AWSAdministratorAccess` — and the profile that reaches it |

  **"Role" and "permission set" are two views of one object** — what it provisions, and why its ARN is
  never hard-coded, are in [`docs/GLOSSARY.md`](docs/GLOSSARY.md), "Permission set". **One login covers every profile
  on its `sso-session`, and there are two** (`awsds`, `awsds-ctadmin`), so the answer is never *which
  profile do I log in with* — it is which identity to pick in the browser
  ([`aws/AWS-CLI.md`](aws/AWS-CLI.md), "Signing in").

## Upkeep — the files this project maintains

| File | What it holds, and the rule |
|---|---|
| [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` | Every step performed by hand in AWS, one file per stage, mirroring `docs/plan/stages/` — **the same slug as the stage file, with a `log-` prefix**, so the two never share a filename. **Written by the user — Claude never edits a stage log.** Claude may draft wording for the user to paste, and says so: **English, Markdown, one single fenced code block in the chat**, no account ids, concise. The full drafting rules are in [`docs/log/INDEX.md`](docs/log/INDEX.md), "How Claude drafts an entry" |
| [`docs/log/INDEX.md`](docs/log/INDEX.md) | The one exception under `docs/log/`: **Claude maintains it.** After reading a stage log, bring its `Records` cell to what the file now contains — a cell saying less than the file is what the index exists to prevent. Never restate a step there: the cell says *what is inside*, in one line |
| [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout, so people can understand the components |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes — **never a copy of the slice tree**, which lives in `docs/plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) | One row per entry in **every** document in `policies/`, all four policy types: what it does, why, and what it does once attached. **Reviewed in the same sitting as any policy change**, attachments included. `./terraform-live/identity/org-policies/check-index.py` decides the mechanical half; whether a row is still *true* is the reading |
| [`docs/PRICING.md`](docs/PRICING.md) | A row for every new AWS service referenced |

# Claude memory

Edit this section with the main ideas gathered in this project, so that your future self will understand the context.

Never use external memory to store information. Store all your memory from this project in this session, and use it.

## Language

Use English when writing source code or any files in this repository.
When responding in chat, always write in Portuguese (Brazil).

## Expertise

This implementation plan assumes that the reader is a software or computer engineer with experience in software development and finance. The reader has basic knowledge of networking, AWS cloud services, and Terraform, and is familiar with Bash, Python, C, Rust, Julia, and R. Since DevOps is not the reader's primary area of expertise, provide sufficient context and explain the rationale behind DevOps-related tasks rather than assuming prior knowledge.

## git

You can edit files in the main branch, but never commit before asking.

Always commit changes to a separate branch with the `claude/` prefix.

Sometimes I'll commit the changes myself; in that case, there's nothing left for you to do.

When I authorize you, you can commit, push and open Pull Requests on GitHub. I'll merge them. After the merge, always synchronize the local folder with the upstream repo.

## Claude LOG

For every project step, review this section and add your own LOG, so that you can remember the current
stage of this project.

Stage numbers refer to `docs/plan/stages/`. **Always read `docs/GENERAL_PLAN.md` before planning or executing a
step** — it is the plan core and carries both indexes — then read only the stage file and the decisions
its `Consumes` row lists.

### What to read, and when

**This table is the only routing map — every other file points here rather than repeating it.**

| Task | Read |
|---|---|
| Anything | this file + [`docs/GENERAL_PLAN.md`](docs/GENERAL_PLAN.md) (plan core: principles, the account map, the route) |
| **What the project must achieve** — before planning or reviewing a stage | [`docs/plan/objectives.md`](docs/plan/objectives.md) — the requirements brief in the user's words. **The specification, summarised nowhere** |
| Execute a stage | [`docs/plan/stages/`](docs/plan/stages/INDEX.md)`stage-NN-*.md`, the decisions in its **Consumes** row, and [`docs/plan/conventions.md`](docs/plan/conventions.md) |
| Design, or reason about where something belongs | [`docs/plan/architecture.md`](docs/plan/architecture.md) — target architecture, region portability, the data perimeter, the two egress designs |
| A naming, layout, Terraform or IAM rule | [`docs/plan/conventions.md`](docs/plan/conventions.md) — also the `[P]`/`[D]`/`[E]` layers, the identity seam and the `app-etl` template |
| **How the deployed tree is organised, and what is in it today** | [`terraform-live/README.md`](terraform-live/README.md) — **the slice-by-slice layout itself stays in `docs/plan/conventions.md` §6**, the authority when the two disagree |
| **What a given policy statement denies, and why that statement exists** | [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) — one row per `Sid`, per document, all four types. Policy ids and attachment dates are **not** there: those are in the stage log |
| What was actually done by hand in a stage | [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` — **the stage file's slug, prefixed `log-`**; [`docs/log/INDEX.md`](docs/log/INDEX.md) first, so only one log is opened |
| **What is deployed right now** — accounts, OUs, SSO groups, users, permission sets, assignments | [`aws/INDEX.md`](aws/INDEX.md) — read-only scripts and their snapshots in `aws/output/` (untracked). **Regenerate rather than trust a stale file, and never copy an account id or email out of one** |
| **Whether something a snapshot shows is expected** — before reporting it as a finding | [`docs/AWS_STATE.md`](docs/AWS_STATE.md) — the invariants (`INV-nn`), the known exceptions (`EXC-nn`), and what a later stage will change anyway. **Read it whenever a snapshot is read** |
| Plan, review, or settle a decision | add [`docs/plan/lessons.md`](docs/plan/lessons.md) and [`docs/plan/open-questions.md`](docs/plan/open-questions.md) |
| Look up a decision | [`docs/plan/decisions/INDEX.md`](docs/plan/decisions/INDEX.md) first — open a decision file only for its reasoning |
| Cost of a new service | [`docs/PRICING.md`](docs/PRICING.md) — measured, never estimated (Lesson 6). The projection is [`docs/plan/cost-model.md`](docs/plan/cost-model.md) |
| Cross-account wiring | [`docs/plan/integrations.md`](docs/plan/integrations.md), the `INT-nn` rows |
| An unfamiliar acronym, or the notation | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| Running an `aws` command by hand, or signing in | [`aws/AWS-CLI.md`](aws/AWS-CLI.md) — the recipes, and which identity runs them |
| **A Terraform change by hand** — the two-commit tag order, blocked commits | [`docs/plan/runbooks/terraform-changes.md`](docs/plan/runbooks/terraform-changes.md) |
| "What would an institution do?" | [`docs/plan/institutional-delta.md`](docs/plan/institutional-delta.md) — so a lab compromise is not learned as a pattern |
| Root is needed, or its alarm chain is being changed | [`docs/plan/runbooks/break-glass.md`](docs/plan/runbooks/break-glass.md) |
| **A policy is about to be attached, or was amended** | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md) — the probes, and the two distinguishable outcomes of each. **Running them is `./aws/probes/scp-battery.py`** ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| Explaining the design to someone | [`README.md`](README.md) — the argument for the account split and the three distinctions |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md) — almost never |

Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1c step 7` — never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

### Current position

- **Landing zone closed — Stages 0-1d DONE (2026-08-15)**, except the `Staging` vend: held on the account
  cap, **open AWS support ticket** (`aws/cloudshell/management-quotas.sh` re-asks). Battery 93/93.
- **Stage 2 DONE (2026-08-16), all nine verifications answered.** Deployed: a state bucket per
  Terraform-managed account (`prod` carries D36's 2nd key); `identity/sso/` — 7 sets, 10 assignments;
  `identity/org-policies/` — ten policies + ten attachments **adopted, none created**, **content never
  sent** (live bytes are still 1c's paste), `prevent_destroy` on both.
  Delegation narrowed to `InfrastructureAccess`, hand-applied, **out of Terraform** (`INV-15`). D11:
  `scripts/tfhygiene/layers.py` + `make up`/`down`/`status`/`slices`; a slice with no row fails
  `make check`. (iii): `IN_SYNC` (`INV-17`). **`awsds` is reserved in SSM Parameter Store** — project parameters take
  `/datascience/<env>/…`.
- **Gates, and there is no CI:** `make check` (offline), `make check-ou` (session),
  `make check-docs` — **red** on pre-Stage-2 prose, outside the commit gate.
- **Stage 3 all three passes APPLIED 2026-08-16.** Step 0: AF VPCs gone (**StackSet on Management**),
  creation off. `foundation/` `[P]` in Sandbox/Development/Production
  (31/30/32, +1/+1/+32 — associations and peerings in **one ordered apply on the accepting side**).
  Pass 3: `vpc-egress-v0.1.0`, `egress/` `[E]` via **`make up`** (16/15/14; endpoints 12/11/10, NAT,
  0.48 USD/h). **`networking.py` and `egress.py`: 0 FAILED; every `foundation/` re-plan `No changes`.**
  Reaching other stages: `egress_mode=A`, and the S3 allow-list — **a NAT does not bypass it** (Stage 4).
  CIDR/`zone_ids`/peers: `scripts/tfhygiene/backend.py`. **Left: the `down`/`up` cycle and the two
  probes** (verification (iii)'s `dnf`); (ii) is Stage 6's.
- **Stages 4-9 revised, pre-instrumented (2026-08-16):**
  `aws/{vpn,datalake,studio,supplychain,cicd,deploytargets}.py` — `DL-5`/`DT-5` guard the LF
  `Parameters` (INT-11). **Stage 8 pass 4 and Stage 9 passes 4-5 wait on the `Staging` vend.**
- **Standing rules that outlive their stages:** never add an `sts:` action to the RCP without reading
  `CT.STS.PV.1`'s exclusion note; 1d step 9 is the **only** sanctioned by-hand use of
  `AWSControlTowerExecution`; **resolve an account by name only with the exact vended name** — every one
  carries an ` Account` suffix and a **SUSPENDED `Sandbox`** sits in the roster, so filter on `ACTIVE` and
  fail loudly (`<ACCOUNT_ID_DATA>` still derives from the `Data` OU); subnets anchor on AZ `zone_id` — run
  `./aws/AZs.py` after every vend; check the SSO token before each probe block and read the denial
  *wording*, never the exit code; account-level BPA is hand-managed (Stage 2's grep guards).
  **Log Archive and Audit hold no CLI profile** (`CHK-1`/`CHK-2` and `org-policies.py` §4 are the
  instruments there).
- **Before reporting a gap, read the file that owns it:** unexercised denies and deliberate allowances →
  `POLICIES.md`; 1b residue and every "expected" reading → `docs/AWS_STATE.md`; the SMUS findings for Stages
  5/6/10 → open questions 12-15, atop Stage 6.
- **Deferred by decision — do not offer to close:** the USD 50 budget notifies nobody (D12); open question
  10's per-unit tokens wait for N=2; Config recorder left alone and Management unrecorded (Stage 12 hooks).
  **Every governed account sits under `us-west-2`.**
- **All 37 decisions are closed** (D30 as a revert). **Still needed from the user: the domain
  name**, blocking Stage 13. **Settle earliest:** INT-11's remaining half (Stage 5 step 5.4, `DL-5`)
  and INT-13.
- **The repository is not documentation-only:** the read-only `aws/` scripts, both Terraform trees,
  `scripts/`, the `Makefile`, and the `pre-commit`/`tflint`/`checkov`/`ruff` gates.
  **Every script is Python 3 on `uv` since 2026-08-15** — shared code in `aws/awslib`,
  `scripts/repohygiene`, `scripts/tfhygiene`; CloudShell = plain `python3` with `aws/` present.
  **Exception: `aws/cloudshell/` stays shell, standalone, for the no-profile accounts.**

**Budget: ~4 KB.** State, not reasoning — **a bullet here that explains *why*, or that a stage file should
be carrying, is a stale copy of something that already lives elsewhere.** Re-trim whenever a stage closes.

### Lessons carried forward

**Read [`docs/plan/lessons.md`](docs/plan/lessons.md) before planning, reviewing, or settling a decision.**
These are recognition keys, not the lessons: each one is a title trimmed to what makes it identifiable, and
the reasoning that makes it *usable* is in the file. Recognising one is the signal to open it.

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
    failure hides the serious one.**
25. **A borrowed session outlives the command that needed it, and every later error names the wrong
    account.**
26. **An "already exists" error is a free authorization probe — and proves nothing without a negative
    control.**
