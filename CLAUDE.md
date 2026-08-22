
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
  on its `sso-session`** — `awsds` and `awsds-ctadmin` for the identities in the table above; the persona
  sessions are [`aws/AWS-CLI.md`](aws/AWS-CLI.md) "Signing in"'s, the roster's owner — so the answer is
  never *which profile do I log in with*: it is which identity to pick in the browser.

## Upkeep — the files this project maintains

| File | What it holds, and the rule |
|---|---|
| [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` | Every step performed by hand in AWS, one file per stage, mirroring `docs/plan/stages/` — **the same slug as the stage file, with a `log-` prefix**, so the two never share a filename. **Written cooperatively — Claude only when the user asks, in that sitting, and never on its own initiative** (revised 2026-08-17). **Provenance is not optional**: every entry names whose hand wrote it, and a measurement the user pasted stays verbatim. **English, Markdown**, no account ids, concise. The two modes and the full rules: [`docs/log/INDEX.md`](docs/log/INDEX.md), "How an entry gets written" |
| [`docs/log/INDEX.md`](docs/log/INDEX.md) | The one exception under `docs/log/`: **Claude maintains it.** After reading a stage log, bring its `Records` cell to what the file now contains — a cell saying less than the file is what the index exists to prevent. Never restate a step there: the cell says *what is inside*, in one line |
| [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout, so people can understand the components |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes — **never a copy of the slice tree**, which lives in `docs/plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) | One row per entry in **every** document in `policies/`, all four policy types. **Reviewed in the same sitting as any policy change**, attachments included. `./scripts/check-index.py` decides the mechanical half; whether a row is still *true* is the reading. What each row says: the routing table below |
| [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md) **and** [`terraform-modules/consumer-data/README.md`](terraform-modules/consumer-data/README.md) | The same discipline for the lake, producer side and consumer side — one row per bucket/key-policy `Sid`, per LF-Tag assignment, per grant, per settings attribute; the module README is what its two calling slices (`sandbox/data/`, `development/data/`) point at. **Reviewed in the same sitting as a change to the `.tf` files.** No mechanical check exists; the `.tf` comments carry the reasoning, these files carry the index |
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
| **The data-governance model** — the LF-Tag ontology (`layer`, `businessunit`, `classification`), the per-account encryption rule (§Encryption), the grant rules and default expressions, the drop-box and derived-zone contracts | [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md) — Stage 5 decisions 1-3 as revised, the one copy; applied grants live in `docs/AWS_STATE.md`'s grant register |
| **Anything touching the SMUS surface** — a blueprint (enable, or a new one appears), the network mode, a Stage 6 cost question, or a domain/project/profile concept | [`docs/SMUS.md`](docs/SMUS.md) — the object model (domain, project, the two profile kinds, environment configurations, the project S3 path), the blueprint list with the user's three categories (2026-08-19) and billing shapes, and `VpcOnly`. Review it whenever SageMaker changes |
| **How the deployed tree is organised, and what is in it today** | [`terraform-live/README.md`](terraform-live/README.md) — **the slice-by-slice layout itself stays in `docs/plan/conventions.md` §6**, the authority when the two disagree |
| **What a given policy statement denies, and why that statement exists** | [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) — one row per `Sid`, per document, all four types. Policy ids and attachment dates are **not** there: those are in the stage log |
| **What governs the LAKE** — a bucket-policy branch, a key-policy statement, a tag assignment, an LF grant | Two files, `POLICIES.md`'s discipline applied per slice: [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md) for the **producer** side, [`terraform-modules/consumer-data/README.md`](terraform-modules/consumer-data/README.md) for the **consumer** half its two calling slices point at (derived bucket, account data CMK, `DataLakeSettings`, the re-grants). They say what the **code** declares; **applied** triples are `docs/AWS_STATE.md`'s grant register. Read the producer README's §"A permission here is the intersection of two systems" before claiming what any principal can do (Lesson 28) |
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
| **Anything VPN** — what the pieces are and what the NAT is *not* part of, starting/stopping the host, connecting a device, a tunnel that will not come up, a key event (loss, revocation, rotation), or a shell on the VPN host | [`docs/plan/runbooks/vpn.md`](docs/plan/runbooks/vpn.md) — one runbook, three parts (unified 2026-08-19). **§S** the system: components, the measured topology, host start/stop (`InsufficientInstanceCapacity` is retried, never redesigned around). **§C** the client, no AWS call in it: the five config values, the three checks that prove three different claims, the silent-by-design failure modes. **§K** the keys — loss is recovery from the `[P]` secret, never rotation — and **§K0a is the SSM session** and where `--target` comes from |
| **Anything DEVBOX** — the `[E]` `amd64` build host of St.6 5.0, its route, or why the VPN host is also a NAT instance | [`docs/plan/runbooks/devbox.md`](docs/plan/runbooks/devbox.md) — six short sections: what it is, why it exists (**the images are `amd64`, the laptop is `arm64`**), the components (**the route is the reach; `vpc_nat_cidrs` is the capability**), `up`, **§S space** (the 64 GiB root against two images that share layers — prune before recreating), `down`. It **must not coexist with `sandbox/probes/`** and a **stopped VPN host makes its route a blackhole, not an error** |
| **A policy is about to be attached, or was amended** | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md) — the probes, and the two distinguishable outcomes of each. **Running them is `./aws/probes/scp-battery.py`** ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| Explaining the design to someone | [`README.md`](README.md) — the argument for the account split and the three distinctions |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md) — almost never |

Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1c step 7` — never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

### Current position

- **Landing zone closed — Stages 0-1d DONE (2026-08-15)**, except the `Staging` vend: held on the
  account cap, open ticket (`aws/cloudshell/management-quotas.sh` re-asks). Battery **100** (4 `note`).
- **Stage 2 DONE (2026-08-16), all nine verifications answered.** A state bucket per Terraform-managed
  account (`prod` carries D36's 2nd key); `identity/sso/` and `identity/org-policies/` (**adopted, none
  created**). Delegation narrowed to `InfrastructureAccess`, hand-applied, **out of Terraform**
  (`INV-15`). D11: `scripts/tfhygiene/layers.py` + `make up`/`down`/`status`/`slices`.
- **Gates, no CI:** `make check` (offline), `make check-ou` (session), `make check-docs` — red on
  pre-St.2 prose, outside the commit gate. `check-identifiers.py` in both: **no account id or e-mail in a
  tracked file**; redact to `<The Account Name>`/`<that user's role>`, declared once per entry.
- **Stage 3 DONE 2026-08-16 — applied, measured, torn down; 0.0000 USD/h** (detail: its Status row).
  `egress_mode=A`; **a NAT does not bypass the S3 allow-list**; INT-05 names the gateway endpoints, never
  `egress/` ids. CIDR/`zone_ids`/peers: `scripts/tfhygiene/backend.py`.
- **NFS/EFS requirement withdrawn (2026-08-17; user edit to `objectives.md`, D24 withdrawn):** no `nfs/`
  slice anywhere, `DL-10` measures EFS *absence*. Detail: `docs/plan/history.md`.
- **Stage 4 DONE 2026-08-18 — closed by the GuardDuty split**; **Stage 15** created the same day carries
  the whole GuardDuty scope, prepared (`aws/guardduty.py`, `GD-1`–`GD-3`).
- **The VPN host is amd64 and back at BASELINE (`t3.nano`, 8 GiB gp3, 2026-08-21; `wireguard-v0.3.0`, D4
  amended).** `VP-1`–`VP-9` pass, 0 FAILED, no cost table understates anything. Two standing facts: a shape
  change is a **REPLACEMENT** — the `[P]` EIP and host key survive, so no client `.conf` moves — and **the
  DISK comes down only by `-replace`**, because EBS refuses a shrinking `ModifyVolume` and strands the
  slice one `~ volume_size` short of its own code. Detail: `AWS_STATE.md`'s VPN row, `vpn.md` §S6. The
  probe slices stay Graviton — not the VPN.
- **Stage 5 DONE, every pass (2026-08-18/20) — the governed lake exists, is granted, shared and
  consumed.** `docs/GOVERNANCE.md` is the one copy of the ontology + grant rules; **one data CMK per
  account** (`alias/awsds-<env>-data`). **Producer:** 5 `awsds-data-*` buckets, `raw`+`curated`
  registered, 2 LF-Tag keys, `curated.sample_trades` (12 synthetic rows), 2 **never-run** crawlers, 2 TBAC
  shares (**INT-11 closed**). **Consumer, per account:** own CMK, `awsds-<env>-derived`, enforced
  `awsds-<env>-athena`, own `DataLakeSettings`, 2 links, 4 re-grants. **Persona:** 7 statements in
  `DataScientistAccess`; **`scratch` is a PREFIX**. **Full inventory: `AWS_STATE.md`'s lake row + the two
  slice READMEs, not here.** Register **13 rows / 24 triples**.
- **Pass 6 RAN 2026-08-20 — Stage 5 has no unrun pass left.** Security Hub **CSPM**, never the **v2**
  beside it (both on hands the Config recorder to a service-linked one, so `DL-11` fails on v2's
  **ARRIVAL**); org-wide by **central configuration on the root** (`awsds-fsbp-only`), never auto-enable;
  Management **`SELF_MANAGED`**, so **nothing records it before St.12** (this also killed St.1d decision
  8's trigger). **16/18 `SUCCESS`** — the 2 left are the suspended `Sandbox` **and the `ROOT` above it**,
  so *"every row `SUCCESS`"* is unavailable here (`EXC-01`). `INV-09` → **nine/four**. **Left: 13.3's
  triage**, and a disable there turns the policy custom.
- **Three things Stage 5 leaves standing — read the owner before calling any of them a gap:**
  (1) **no principal can start the crawlers** (trust admits `glue.amazonaws.com` alone, `Schedule` null;
  Lesson 22; **OQ 19**), **so D18/D25 ingestion is broken at ONE end**: files land and nothing catalogues
  them. (2) **`EXC-02`**, one uncollectable object in the drop-box — do not grant a delete to tidy it.
  (3) since 4e, **no Athena in Data Governance at all**, `InfrastructureAccess` included.
- **A denied call does not always name the policy** (Athena, 2026-08-20/21): attribution moves to a
  **CONTRAST PROBE** — the same call from an OU the deny misses. `probes.py` 93→96→**100**; 4 rows read
  `note` forever by design (`EXC-03`).
- **A cached SSO token is keyed by `sso-session` name, NEVER by user** (2026-08-20): the wrong identity
  fills the right one's slot and `aws sso login` then succeeds doing nothing — **remedy is `aws sso
  logout` + portal sign-out**; wording is `ForbiddenException`/`GetRoleCredentials`. **That same wording
  was a real ceiling breach on 2026-08-14**, so the battery separates them by asking **IdC what the token
  is assigned** (STS never touches that path). Never suppress it by text alone — Lesson 24, in reverse.
- **Stage 6 OPEN — passes 0 THROUGH 2 APPLIED 2026-08-21, three sittings; the stage file's §"What ran" is the one record.**
  Four new slices (24 total): `production/registry/`, `{sandbox,development}/sagemaker/`,
  `data-governance/governance/` (**`awsds-studio`, V2, `AVAILABLE`**, domain `dzd-d8yrvx1ko7im6o`), plus
  step 3's deny pair in **all six** persona sets and **1.6's `DenyAthenaSparkStartSession`**.
  **`pki/` is St.7 pass 1** (D36 §3 amended, D36 off the Consumes row), so **5.0's image carries NO CA
  root** — it takes one at St.7 2.6.
- **St.6's two pre-apply measurements are clean (2026-08-21).** Verification (i) answered both ways —
  domain created from `Data`; the canary replay hit `awsds-org-scp-baseline`'s **explicit SCP deny** —
  so INT-12's fallback is closed, and the 2026-08-20 wall was the **missing `--service-role`** (Lesson
  24). Battery `--phase ou` **25/0/7**; `StartSession` denied in dev+sandbox, allowed in prod,
  `StartQueryExecution` intact (D13) — and `StartSession` **authorizes before it validates**.
- **1.3 DONE 2026-08-21 — the association AUTO-ACCEPTS: no invitation, no 7-day clock** (org-scoped
  RAM share). Permission: `…DatazoneDomainExtendedServiceAccess` (152 actions, the +41 = the V2
  workbench) — a **ceiling**, not access. `US-2` reads the owner from the **ARN** (it first FAILED by
  working — visibility is not ownership).
- **1.4/1.5 DONE 2026-08-21: 11 blueprint configurations per member (all carrying the D13 boundary),
  two project profiles** (`experimentation`→Sandbox, `engineering`→Development; `Tooling` sole base,
  `ON_CREATE`; five locked params read back non-editable; **TIP `false` — decision 2 DELIVERED**);
  battery **0 FAILED**. **The `awscc` configuration takes the blueprint NAME, the `aws` resource the id**
  (Lesson 32; the first apply failed 12/12 — `v0.2.2` fixes it; **`v0.2.1` is a STILLBORN tag nothing may
  reference**). **The boundary field is WRITE-ONLY — drift never surfaces in a plan; `US-8` is the
  sentinel** (verification v). **`ToolingLite` is a BASE variant** (the service demands `ON_CREATE` when
  it is bundled) — **re-cut to category 3 by the user** (`v0.2.3`, 12→11). `DataLakeSettings` untouched
  by enablement (xiv's seat question is subscription-time). **The member-before-`governance/` order rule
  survives for the next member (St.14).**
- **THE ROSTER IS MEASURED, THE PLAN'S NAMES WERE NOT (2026-08-21; Lesson 38):** the API says
  `EmrServerless`/`EmrOnEc2`/`QuickSight`, and **`AmazonBedrockGenerativeAI` is a CONSOLE GROUPING
  with no API identifier** — 23 by API, 13 in the console. **Decision 5 closed 12/5/6, re-cut SAME DAY
  to 11/5/7** (`ToolingLite` → cat 3, finding 9). **The Bedrock family is SPLIT** (`KnowledgeBase` cat
  2 — its vector store bills while it exists); **`LakehouseAdmin` is cat 2** (an account-wide
  ingest-and-catalog TEMPLATE, not LF's *data lake administrator*). The list lives in **three** places
  (`locals.tf`, the module default, `US-3`) — one commit moves all three, a module TAG BUMP each time.
- **What St.6 still owes:** **5.0's docker PUSH** (build clean on the devbox 2026-08-21; the devbox
  cannot push); **1.7's portal reading (user)**; then passes 3-5. Decisions 1 (EMR-S vs Glue) and 6
  (prefix shape) stay in-stage; **2 is delivered** (TIP `false`, non-editable, both profiles).
- **Standing St.6 mechanics:** a blueprint configuration is applied **from the MEMBER account** (the
  Put takes no account param); `awscc`'s carries **`environment_role_permission_boundary`** and the
  `aws` resource does not (INT-15's mechanism, Lesson 8); **`athena:UpdateSession` is in no API model**
  — shipped anyway from AWS's own sample, `StartCalculationExecution` beside it.
- **Stages 5-11 revised, pre-instrumented (2026-08-16/17):**
  `aws/{vpn,datalake,studio,supplychain,cicd,deploytargets,orchestration,dlp}.py` — `DL-5`/`DT-5` guard
  the LF `Parameters` (INT-11). **St.8 pass 4, St.9 passes 4-5, St.10's Staging leg wait on the vend;
  St.11's step 4 gates on St.15 + a month of billing** and flips `GD-3`/`DP-6`.
- **Standing rules that outlive their stages:** never add an `sts:` action to the RCP without reading
  `CT.STS.PV.1`'s exclusion note; 1d step 9 is the **only** sanctioned by-hand use of
  `AWSControlTowerExecution`; **resolve an account by name only with the exact vended name** — every one
  carries an ` Account` suffix and a **SUSPENDED `Sandbox`** sits in the roster: filter on `ACTIVE`,
  fail loudly; subnets anchor on AZ `zone_id` (`./aws/AZs.py` after every vend); check the SSO token
  before each probe block and read the denial *wording*, never the exit code; account-level BPA is
  hand-managed. **Log Archive and Audit hold no CLI profile.**
- **Before reporting a gap, read the file that owns it:** unexercised denies → `POLICIES.md`;
  "expected" readings → `docs/AWS_STATE.md`; SMUS findings → open questions 12-15 and **21**.
- **Deferred by decision — do not offer to close:** the USD 50 budget notifies nobody (D12); open
  question 10 waits for N=2; Config recorder left alone, Management unrecorded (Stage 12 hooks).
  **Every governed account sits under `us-west-2`.**
- **All 37 decisions closed** (D30 as a revert). **Still needed from the user: the domain name**
  (blocks Stage 13). **Settle earliest:** INT-13 (INT-11's vending half closed at 4d, 2026-08-19).
- **The repository is not documentation-only:** read-only `aws/` scripts, both Terraform trees, `scripts/`,
  the `Makefile`, the `pre-commit`/`tflint`/`checkov`/`ruff` gates. **Every script is Python 3 on `uv`** —
  shared code in `aws/awslib`, `scripts/repohygiene`, `scripts/tfhygiene`. **Exception:
  `aws/cloudshell/` is shell, standalone, for the no-profile accounts.**

**Budget: ~8 KB** (raised from 4 KB by the user, 2026-08-19). State, not reasoning — **a bullet here that explains *why*, or that a stage file should
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
    failure hides the serious one; a result that cannot be attributed from its own text — ambiguous OR
    silent — is separated by a different *channel*, never by a better reading.**
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
