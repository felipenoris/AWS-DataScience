
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
pinned by `uv` (`pyproject.toml`/`uv.lock`), `WireGuard` **v1.0.16** (App Store), `wireguard-tools` **v1.0.20260223** (homebrew) which provides the `wg` utility, `session-manager-plugin` **1.2.835.0** (homebrew cask); `ruff` lints/formats.

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

- **The first exception, and it is fenced: [`aws/probes/`](aws/probes/README.md)** — the SCP battery has to
  *attempt* the calls a policy forbids, because that is the only way to measure a preventive control. It
  creates nothing and attaches nothing; the probes that would act without a deny are refused anywhere but
  `Policy Canary`. **Run it deliberately, not to gather information** — the difference from every other
  script in that folder.

- **The second exception is a flag, not a script: `./aws/vpn.py --on-host`** (2026-08-17) — SSM Run Command
  reading *inside* the WireGuard host, the only way to learn which peers the running interface actually
  holds. Every command it carries is a read, but `ssm:SendCommand` is a write API, so it is **off by
  default**: without the flag `vpn.py` is read-only like everything else, and with it the rule above is
  the battery's — run deliberately.

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
| [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` | Every step performed by hand in AWS, one file per stage, mirroring `docs/plan/stages/` — **the same slug as the stage file, with a `log-` prefix**, so the two never share a filename. **Written cooperatively — Claude only when the user asks, in that sitting, and never on its own initiative** (revised 2026-08-17). **Provenance is not optional**: every entry names whose hand wrote it, and a measurement the user pasted stays verbatim. **English, Markdown**, no account ids, concise. The two modes and the full rules: [`docs/log/INDEX.md`](docs/log/INDEX.md), "How an entry gets written" |
| [`docs/log/INDEX.md`](docs/log/INDEX.md) | The one exception under `docs/log/`: **Claude maintains it.** After reading a stage log, bring its `Records` cell to what the file now contains — a cell saying less than the file is what the index exists to prevent. Never restate a step there: the cell says *what is inside*, in one line |
| [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout, so people can understand the components |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes — **never a copy of the slice tree**, which lives in `docs/plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) | One row per entry in **every** document in `policies/`, all four policy types: what it does, why, and what it does once attached. **Reviewed in the same sitting as any policy change**, attachments included. `./scripts/check-index.py` decides the mechanical half; whether a row is still *true* is the reading |
| [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md) | The same discipline for the lake's own controls — one row per bucket/key-policy `Sid`, per LF-Tag assignment, per grant, per settings attribute. **Reviewed in the same sitting as a change to the slice's `.tf` files.** No mechanical check exists for it; the `.tf` comments carry the reasoning, this file carries the index |
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
| **The data-governance model** — the LF-Tag ontology (`layer`, `businessunit`, `security-zone`, `classification`), the grant rules and default expressions, the drop-box and derived-zone contracts | [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md) — Stage 5 decisions 1-3, the one copy; applied grants live in `docs/AWS_STATE.md`'s grant register |
| **Anything touching the SMUS surface** — a blueprint (enable, or a new one appears), the network mode, a Stage 6 cost question | [`docs/SMUS.md`](docs/SMUS.md) — the blueprint list with the user's three categories (2026-08-19) and billing shapes, and `VpcOnly`. Review it whenever SageMaker changes |
| **How the deployed tree is organised, and what is in it today** | [`terraform-live/README.md`](terraform-live/README.md) — **the slice-by-slice layout itself stays in `docs/plan/conventions.md` §6**, the authority when the two disagree |
| **What a given policy statement denies, and why that statement exists** | [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) — one row per `Sid`, per document, all four types. Policy ids and attachment dates are **not** there: those are in the stage log |
| **What governs the LAKE** — a bucket-policy branch, a key-policy statement, a tag assignment, an LF grant | [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md) — `POLICIES.md`'s discipline applied to the slice: one row each, reviewed in the same sitting as the change. It says what the **code** declares; **applied** triples are `docs/AWS_STATE.md`'s grant register. Read its §"A permission here is the intersection of two systems" before claiming what any principal can do (Lesson 28) |
| What was actually done by hand in a stage | [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` — **the stage file's slug, prefixed `log-`**; [`docs/log/INDEX.md`](docs/log/INDEX.md) first, so only one log is opened |
| **What is deployed right now** — accounts, OUs, SSO groups, users, permission sets, assignments | [`aws/INDEX.md`](aws/INDEX.md) — read-only scripts and their snapshots in `aws/output/` (untracked). **Regenerate rather than trust a stale file, and never copy an account id or email out of one** |
| **Whether something a snapshot shows is expected** — before reporting it as a finding | [`docs/AWS_STATE.md`](docs/AWS_STATE.md) — the invariants (`INV-nn`), the known exceptions (`EXC-nn`), and what a later stage will change anyway. **Read it whenever a snapshot is read** |
| Plan, review, or settle a decision | add [`docs/plan/lessons.md`](docs/plan/lessons.md) and [`docs/plan/open-questions.md`](docs/plan/open-questions.md) |
| Look up a decision | [`docs/plan/decisions/INDEX.md`](docs/plan/decisions/INDEX.md) first — open a decision file only for its reasoning |
| Cost of a new service | [`docs/PRICING.md`](docs/PRICING.md) — measured, never estimated (Lesson 6). The projection is [`docs/plan/cost-model.md`](docs/plan/cost-model.md) |
| Cross-account wiring | [`docs/plan/integrations.md`](docs/plan/integrations.md), the `INT-nn` rows |
| An unfamiliar acronym, or the notation | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| Running an `aws` command by hand, or signing in | [`aws/AWS-CLI.md`](aws/AWS-CLI.md) — the recipes, and which identity runs them |
| **A Terraform change by hand** — the two-commit tag order, blocked commits, **the staged apply (Recipe D — the only sanctioned `-target`)** | [`docs/plan/runbooks/terraform-changes.md`](docs/plan/runbooks/terraform-changes.md) |
| "What would an institution do?" | [`docs/plan/institutional-delta.md`](docs/plan/institutional-delta.md) — so a lab compromise is not learned as a pattern |
| Root is needed, or its alarm chain is being changed | [`docs/plan/runbooks/break-glass.md`](docs/plan/runbooks/break-glass.md) |
| **A VPN key event** — a copy is lost, the secret is touched, a device is revoked, the host pair rotates — **or a shell on the VPN host** | [`docs/plan/runbooks/vpn-keys.md`](docs/plan/runbooks/vpn-keys.md) — loss is recovery from the `[P]` secret, never rotation. **§0a is the SSM session** and where `--target` comes from |
| **Connecting a device to the VPN, or a tunnel that will not come up** | [`docs/plan/runbooks/vpn-client.md`](docs/plan/runbooks/vpn-client.md) — the client side only, no AWS call in it: the five config values and where each comes from, the three checks that prove three different claims, and the failure modes that are silent by design |
| **A policy is about to be attached, or was amended** | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md) — the probes, and the two distinguishable outcomes of each. **Running them is `./aws/probes/scp-battery.py`** ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| Explaining the design to someone | [`README.md`](README.md) — the argument for the account split and the three distinctions |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md) — almost never |

Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1c step 7` — never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

### Current position

- **Landing zone closed — Stages 0-1d DONE (2026-08-15)**, except the `Staging` vend: held on the
  account cap, open ticket (`aws/cloudshell/management-quotas.sh` re-asks). Battery 93/93.
- **Stage 2 DONE (2026-08-16), all nine verifications answered.** A state bucket per Terraform-managed
  account (`prod` carries D36's 2nd key); `identity/sso/` and `identity/org-policies/` (**adopted, none
  created**). Delegation narrowed to `InfrastructureAccess`, hand-applied, **out of Terraform**
  (`INV-15`). D11: `scripts/tfhygiene/layers.py` + `make up`/`down`/`status`/`slices`. SSM naming:
  conventions §6 (`awsds` is reserved).
- **Gates, no CI:** `make check` (offline), `make check-ou` (session), `make check-docs` — red on
  pre-Stage-2 prose, outside the commit gate. `check-identifiers.py` in both: no account id or e-mail in
  a tracked file; redact to `<The Account Name>`/`<that user's role>`, declared once per entry.
- **Stage 3 DONE 2026-08-16 — applied, measured, torn down; 0.0000 USD/h** (detail: its Status row).
  `egress_mode=A`; **a NAT does not bypass the S3 allow-list**; INT-05 names the gateway endpoints, never
  `egress/` ids. CIDR/`zone_ids`/peers: `scripts/tfhygiene/backend.py`. Left elsewhere: `Staging`'s
  NXDOMAIN; verification (ii) is Stage 6's.
- **NFS/EFS requirement withdrawn (2026-08-17; user edit to `objectives.md`, D24 withdrawn):** no
  `nfs/` slice anywhere, `elasticfilesystem` out of Sandbox's endpoints, `DL-10` measures EFS *absence*
  (a Studio domain's own tagged home exempt). Detail: `docs/plan/history.md`.
- **Stage 4 DONE 2026-08-18 — closed by the GuardDuty split** (close-out log entry is the user's; the
  host was left `running` — tunnel down first, then `make down`). **Stage 15 created the same day**: the
  whole GuardDuty scope, prepared — plans arrive ON, Audit's own switch-off meets
  `DenyGuardDutyTampering` (its decision 1), `ALL` never reaches Management. Principle 9 overruled once;
  the institutional-delta row argues it. `aws/guardduty.py` (`GD-1`–`GD-3`); `VP-8` retired; `vpn.py`
  default narrowed to two profiles.
- **Stage 5 OPENED 2026-08-18:** `docs/log/log-stage-05-data-foundation.md` initialized (no entries);
  baseline `./aws/datalake.py` green — `DL-5` reads `4/TRUE`, `DL-1/4/8/11` pre-stage notes. Pass 0
  underway: **decision 4 taken 2026-08-18 (Glue auto-compaction; the 4.3 `athena:StartQueryExecution`
  amendment owed via battery phase 4b, after any Athena-borne sample-table load)**; **decisions 1-3 taken
  2026-08-18 — `docs/GOVERNANCE.md` is the one copy** (ontology renamed: `layer`/`businessunit`/
  `security-zone`/`classification`; `raw` default `internal`, fail-open by the user's call; one `zn-lab`
  lake CMK, drop-box sharing it; grant register seeded empty in `AWS_STATE.md`); **decision 5 taken 2026-08-18** (recommendation
  as-is: admins = `InfrastructureAccess` only, shares to the two named accounts, TBAC default + the 7.1
  catalog-policy prerequisite); **decision 6 taken 2026-08-18 — the grain reframed: entitlement to
  roles/projects per the toolset's practice, per-user as mapped exploration (verif. viii = the map;
  OQ13's Stage 5 half answered). PASS 0 CLOSED — all six decisions taken. PASS 1 AUTHORED 2026-08-18,
  NOTHING APPLIED**: `data-governance/data/` (11 files, `58 to add`), registered in D11 (18/18).
  **Its finding: the 5.2 default-permission clearing cannot be stated in a plan** (Computed blocks,
  `= []` refused) → **the apply is TWO steps** — settings alone under `-target`, `DL-5`/`DL-6` read,
  then the rest. `s3-bucket` → **v0.2.0** (`any`, not `list(any)`): Recipe B, tag pushed first.
- **PASS 1 APPLIED 2026-08-18 — the lake exists.** Five `awsds-data-*` buckets under one CMK
  (`alias/awsds-data-zn-lab`), `raw`+`curated` registered, 3 LF-Tag keys, 3 databases,
  `curated.sample_trades` (Iceberg, `restricted` column) + its optimizer,
  `awsds-data-catalog-maintenance` + 2 unscheduled crawlers. Re-plan `No changes`; `DL-1`–`DL-6`,
  `DL-10` pass. **The measurement the split existed for: omission CLEARS** (`DbDefaults`/`TableDefaults`
  read `[]` before any database) — **keep the read-back anyway**, it is provider behaviour the plan
  still does not state. Verified per database: no `IAMAllowedPrincipals` anywhere. Added beyond the
  stage text: a **Glue security configuration** (gate finding; a crawler samples contents, so its logs
  take the lake key) — and the role needs `glue:GetSecurityConfiguration` to run under it. Nothing
  behavioural proven; crawlers never run. **Merged (PR #18), synced, re-planned `No changes` from the
  merge commit.** The finding generalised into **Lesson 27** + the runbook's **Recipe D** (`-target` as
  a measurement; `after_unknown` is the instrument — `providers schema` never marks `computed` on
  blocks). Sandbox not needed until pass 4's persona proofs (`make down ENV=sandbox` safe). Stage 4
  residuals, non-blocking: host left `running`; the user's close-out log entry still owed.
- **PASS 2 APPLIED 2026-08-19 — `9 added`, `DL` all pass.** `governance.tf` — the GM's own grants
  (`ASSOCIATE` on the 3 tag keys, `DESCRIBE` on the 3 databases + `ALL_TABLES`). **Verified by
  `list-permissions`, not the code: nine rows, `grant_option=NONE`, no `SELECT`** (by exhaustion).
  Register 3 rows / 9 triples. **6.2: every `s3:` in the six persona sets is a `Deny`** — D13 holds by
  *absence*. **Lesson 28.** Verification (viii) = decision 6's map in `GOVERNANCE.md` §"The grain" (TIP
  the only per-person surface; costs remote access; not adopted). Slice README is an **index of
  controls**. **Owed: can the persona actually tag? — needs a GM sign-in + the tunnel.**
- **PASS 3 APPLIED 2026-08-19 — `4 added`, re-plan `No changes`, `DL` 0 FAILED.** `shares.tf`: the
  Sandbox + Development TBAC shares. **4 `LakeFormation-V4-*` RAM shares `ACTIVE`, held by both
  consumers, ZERO invitations → INT-11 closed**; `DL-5` bracket holds (3rd reading = verification (i)).
  **Method change first: AWS's LF pages read fine in a *rendering* browser** — pass 2's "no body to
  fetch" caveat retired (**Lesson 30**), and its deferred question answered: the GM **tags, does not
  grant** (`Grant with LF-Tag expressions`; the *LF-Tag creator* clause stays Stage 6's). **Two
  corrections to the decided form**: the grant option is **mandatory on every** cross-account grant (the
  consumer's own DL-admin must re-grant), and the expression needed a `layer` gate or it shared the
  **drop-box** (**Lesson 29**; the applied form is DB `layer∈{raw,curated}` → `DESCRIBE`, TABLE + `AND
  classification∈{public,internal}` → `SELECT`). 7.1's catalog-policy prerequisite measured
  **conditional, not applicable** (no Glue resource policy). Register 9 rows / 17 triples.
  **`DL-7` rebuilt** — it reported one verdict for two opposite causes (Lesson 13's family); it now reads
  each consumer's *held* shares + admin count. **Pass 4's new opening prerequisite: each consumer account
  needs its OWN `DataLakeSettings`** (admins `[]` today → empty catalog by rule), with INT-11 and
  Lesson 27 both applying there. `sts:SetContext` only half-tested — vending waits for pass 4's query.
- **Stage 6 NOT open, but its decision 3 is CLOSED (2026-08-19, doc-only sitting — no AWS call at all;
  [log](docs/log/log-stage-06-unified-studio.md) initialized early because the stage file homes such
  decisions there).** Athena Spark off by **SCP** `athena:StartSession`/`UpdateSession` on `Interactive`,
  at **1.6 — not pulled forward** into Stage 5's phase-4b sitting; **no Athena clause in 2.1's boundary**
  (Lesson 20 — the 2nd denier is never the proven one); the 3 optional `athena.*` session endpoints
  **declined in writing** in both Interactive `egress/main.tf` (Lesson 5). Re-read corrections: the Tooling
  flag is **non-retroactive** too; the doc's 3rd control is *grant*-shaped on blueprint-authored policies,
  so the boundary is a **deviation to record**; `DenyUserAccessFromUnauthorizedVPCs` has a **3rd**
  condition (`aws:userid` `*:user-*` — INT-16's on-behalf carve-out already in AWS's shape). **The 2026-04
  Athena Spark PrivateLink release moves the client path, NOT executor placement** — trigger worded against
  the headline. **Decision 1 REOPENED**: EMR Serverless needs **4** endpoints vs Glue sessions' 1.
- **Stages 5-11 revised, pre-instrumented (2026-08-16/17):**
  `aws/{vpn,datalake,studio,supplychain,cicd,deploytargets,orchestration,dlp}.py` — `DL-5`/`DT-5` guard
  the LF `Parameters` (INT-11). **St.8 pass 4, St.9 passes 4-5, St.10's Staging leg wait on the vend.**
  St.11: internal access **USD 9/resource-month** → analyzer is create-read-delete; Macie adds existing
  members one by one; the first member trail owes `DenyCloudTrailKill`; **its step 4 gates on St.15 + a
  month of billing** and flips `GD-3`/`DP-6`.
- **Standing rules that outlive their stages:** never add an `sts:` action to the RCP without reading
  `CT.STS.PV.1`'s exclusion note; 1d step 9 is the **only** sanctioned by-hand use of
  `AWSControlTowerExecution`; **resolve an account by name only with the exact vended name** — every one
  carries an ` Account` suffix and a **SUSPENDED `Sandbox`** sits in the roster: filter on `ACTIVE`,
  fail loudly; subnets anchor on AZ `zone_id` (`./aws/AZs.py` after every vend); check the SSO token
  before each probe block and read the denial *wording*, never the exit code; account-level BPA is
  hand-managed. **Log Archive and Audit hold no CLI profile.**
- **Before reporting a gap, read the file that owns it:** unexercised denies → `POLICIES.md`;
  "expected" readings → `docs/AWS_STATE.md`; SMUS findings → open questions 12-15.
- **Deferred by decision — do not offer to close:** the USD 50 budget notifies nobody (D12); open
  question 10 waits for N=2; Config recorder left alone, Management unrecorded (Stage 12 hooks).
  **Every governed account sits under `us-west-2`.**
- **All 37 decisions closed** (D30 as a revert). **Still needed from the user: the domain name**
  (blocks Stage 13). **Settle earliest:** INT-11's remaining half (Stage 5 step 5.4, `DL-5`), INT-13.
- **The repository is not documentation-only:** the read-only `aws/` scripts, both Terraform trees,
  `scripts/`, the `Makefile`, the `pre-commit`/`tflint`/`checkov`/`ruff` gates. **Every script is
  Python 3 on `uv`** — shared code in `aws/awslib`, `scripts/repohygiene`, `scripts/tfhygiene`.
  **Exception: `aws/cloudshell/` is shell, standalone, for the no-profile accounts.**

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
27. **A plan is silent about the values the provider owns — including the one that must be right before
    anything else exists.**
28. **A service with its own permission layer makes reach an *intersection* — and the two halves sit in
    different slices, so a slice never answers "what can this persona do".**
29. **An attribute assigned to *describe* becomes a *selector* the moment a rule is written over it —
    and inherits every resource wearing it for an unrelated reason.**
30. **A tool's failure is not a property of the world, and gets written down as one.**
