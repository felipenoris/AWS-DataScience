
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

## reference terraform

The folder `terraform-reference` is in `.gitignore` and contains an alternative implementation of this project. Never edit files in this folder unless requested by the user. You're free to read this folder and compare it to what is implemented in this project.

## aws cli

- you are free to run read-only operations using aws client.

- Never run write operations using aws, unless explicitly authorized.

- if the current aws cli session is expired, always ask the user to login, informing which sso user o use. **Never login by yourself**.

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
| [`docs/NETWORK.md`](docs/NETWORK.md) | **The network as built** — addresses, routes, both egress paths, VPN, DNS, security groups, and the two reach questions. **Reviewed in the same sitting as any change to a network-bearing slice or module** (its §2.1 names which those are), so a stage putting a host on the wire updates it as part of the stage. `./scripts/check-network-doc.py` is the mechanical half; whether a sentence is still **true** is the reading, and a moved `[P]` fact is **re-measured** with the `aws/` instruments, never re-imagined |
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
| **Anything touching the SMUS surface** — a blueprint (enable, or a new one appears), the network mode, a Stage 6 cost question, or a domain/project/profile concept | [`docs/SMUS.md`](docs/SMUS.md) — the object model (domain, project, the two profile kinds, environment configurations, the project S3 path), the blueprint list with the user's three categories (2026-08-19) and billing shapes, `VpcOnly`, and the **custom-image (BYOI) tag convention** (`<flavour>-v<semver>`, 2026-08-22 — the one copy; `images/README.md` points at it). Review it whenever SageMaker changes |
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
| **Anything EGRESS, PROXY or the hub topology** — where the internet is reached, which VPC a thing belongs in, why there is no NAT gateway | [`docs/plan/decisions/D38-single-egress-hub.md`](docs/plan/decisions/D38-single-egress-hub.md) (the decision, closing OQ 23) + [`docs/plan/stages/stage-06c-networking-hub.md`](docs/plan/stages/stage-06c-networking-hub.md) (the build). **Peering shares an address, never a path** (Lesson 44): no spoke has a default route, the single egress is an **explicit proxy**, and the hub carries no interface endpoint with private DNS |
| **The NETWORK as built** — VPCs, subnets, routes, peerings, egress, VPN, DNS, security groups, every internal address; **how a SageMaker app sees the internet, and what can reach one** | [`docs/NETWORK.md`](docs/NETWORK.md) — code plus measurement, with diagrams. **Its first section now names the six facts Stage 6c replaces**; until that apply the tables below it are current, and they are **re-measured** then, never edited ahead. The runbooks stay the procedures, `AWS_STATE.md` stays what is *expected* |
| **Anything BUILDBOX** — the `[E]` `amd64` build host of St.6 5.0, its route, or why the VPN host is also a NAT instance | [`docs/plan/runbooks/buildbox.md`](docs/plan/runbooks/buildbox.md) — seven short sections: what it is, why it exists (**the images are `amd64`, the laptop is `arm64`**), the components (**the route is the reach; `vpc_nat_cidrs` is the capability**), `up`, **§S space** (the 64 GiB root against two images that share layers — prune before recreating), **§P push** (**build and push are ONE session** — the volume dies with the host; the identity arrives as an ECR **token**, never as a permission), `down`. It **must not coexist with `sandbox/probes/`** and a **stopped VPN host makes its route a blackhole, not an error** |
| **Anything SANDBOX LAKE** — the ungoverned fourth Sandbox bucket (`awsds-sandbox-lake`, St.16), a per-group prefix, wiring or unwiring a project's S3 connection, either read/write test, or **code that lists/reads/writes it** | [`docs/plan/runbooks/sandbox-lake.md`](docs/plan/runbooks/sandbox-lake.md) — six short sections, **exercised 2026-08-26** (except §R's trust half — a real project's death): what it is and is not (**not the governed lake**), **§G** the prefix contract, **§W** wire a project (a grant + a trust entry + the portal form), **§T** the two tests (the in-image direct-refusal test is UNRUNNABLE — the laptop is that control's home), **§P** the Python examples (notebook = plain boto3, the plugin vends; laptop = explicit vend, the only door), **§R** revoke — an orphaned grant is `SL-4`'s finding |
| **A policy is about to be attached, or was amended** | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md) — the probes, and the two distinguishable outcomes of each. **Running them is `./aws/probes/scp-battery.py`** ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| Explaining the design to someone | [`README.md`](README.md) — the argument for the account split and the three distinctions |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md) — almost never |

Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1c step 7` — never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

### Current position

- **RE-SCOPED 2026-09-05** (quota refused, one interactive environment is enough, the network too thin).
  **Stage 6 split into four**: `06a` (record), `06b` (`Development` → `Staging`), `06c` (the network),
  `06d` (the remainder); log at `log-stage-06a-*`. **Order: 6b → 6c → 6d → 7.** New: **D38**, **Lesson 44**,
  **INT-21/INT-22**; **D21 superseded**; D4/5/6/7/9/11/12/14/15/17/18/19/20/22/23/26/35/36 amended; **OQ 23
  closed**; Stage 14 **blocked on the quota**; Stage 15 **not** pulled forward (declined).
- **6b/6c/6d re-reviewed the same day** into the action-checklist format; **6b runs before 6c**. Corrections
  outside 6c's own table: three VPCs collide on the flow-log **log group and IAM role**; `VPN_HOMES` rows
  read `foundation/` while the hub's EIP is in `networking/`; AWS's `DenyUserAccessFromUnauthorizedVPCs`
  **cannot be copied** (`StringNotEquals` on an **absent** `aws:SourceVpc` matches every browser call).
  Planned: `./aws/eip-transfer.py`, `./aws/proxy.py`.
- **Stages 7-15 reviewed the same day (third sitting)** — each had a re-scoped Status row over a stale body.
  **Stage 10 contradicted itself** (it still built design B and ran a comparison D7 had settled): now one
  design in **two** accounts, Staging first; step 4 is the fallback ladder; provisioned MWAA replaced by
  `DenyProvisionedMwaa` and `OR-6` flipped to an absence check. **Stage 7 rewritten whole** (seven
  documentation corrections in its own table); 12 and 13 rewritten into the action-checklist format;
  **Stage 9 gained the steps its Status row had only announced** — 3.5-3.7 move the off-VPC deny onto the
  job **roles** as a boundary (`get-role`, never `list-roles`) and deny serverless inference by SCP;
  Stage 8 lost its vend gate and owns the D28 lint; Stage 14's VPN question closed without N.
  **Back into 6c**: three NAT gateways not two; `vpc-egress` needs `vpc`'s `name_suffix`;
  `production/workloads-egress/` (rank 51) added. **New: Lesson 45.** D38 gains a NAT-contingency candidate
  (ECR's pull-through cache, measured at Stage 7 5.2); INT-19 is **four** surfaces; INT-04 retired into
  INT-07.
- **The chain is `Sandbox → Staging → Production`** (`objectives.md` edited by the user). Interactive
  compute exists in **Sandbox only**; Staging and Production carry the SageMaker **runtime**, which needs
  no domain object. `DataScientistStagingAccess` exists, unassigned, and is 6b's target.
- **D38 in one paragraph:** peering shares an **address, never a path** (Lesson 44), so the single egress
  is an **explicit Squid proxy** in `VPC-Networking` (Production, 10.31/16), **zero NAT gateways** (three
  destroyed), and no spoke has a default route. `VPC-SharedServices` = 10.30/16; `VPC-Workloads` = 10.32/16
  (+ its own `workloads-egress/` `[E]` slice); Staging keeps **10.50/16**; 10.40 free; 10.60 reserved.
  **Five peerings** — the absent ones are the isolation control. WireGuard and Squid are **two `[D]` hosts**;
  the WireGuard **EIP transfers** (free, 7-day accept, disassociate first, **tags reset**), so no client
  `.conf` changes. **The VPN client is a private-network client**: its whole internet crosses the proxy, so
  every VPN-only condition re-keys onto the **proxy's** EIP. **The hub carries no interface endpoint with
  private DNS** — the repair of Lessons 40-43, and why endpoints are never centralized. `awsds.internal`
  apex + `sandbox|staging|prod.` children + `awsds-pages.internal`, with the INT-22 matrix.
- **The SMUS CI/CD tool is `aws-smus-cicd-cli` and deploys only into EXISTING SMUS projects** — an
  **exporter** on the Sandbox side; the pipeline stays the deployer (D26/D28).
- **Orchestration is MWAA Serverless only** (USD 0.088/task-hour, no standing fee;
  `awscc_mwaaserverless_workflow`; the `aws` provider has none). Design B is INT-14's documented-not-built
  terminal fallback; a root-SCP `airflow:CreateEnvironment` deny replaces the prose. **Workers accept no
  proxy** — `NetworkConfiguration` always set on AWS's **documented private-routing shape** (no NAT, no IGW
  route; `logs`/`monitoring`/`kms` endpoints; self-referencing SG; **two AZs — a priced D9 exception**):
  D38's first named exception, with **no** internet path at all.
- **Landing zone closed — Stages 0-1d DONE (2026-08-15).** Battery **100** (4 `note` by design, `EXC-03`).
  **Stage 2 DONE**; a state bucket per Terraform-managed account; delegation narrowed and hand-applied
  (`INV-15`). **Gates:** `make check` (offline), `check-ou` (session), `check-docs` (red on pre-St.2
  prose); `check-identifiers.py` forbids any account id or e-mail in a tracked file.
- **Stage 3 DONE 2026-08-16** — applied, measured, torn down to 0.0000 USD/h. **Stage 4 DONE 2026-08-18**;
  the VPN host is amd64 `t3.nano` at BASELINE; a shape change is a REPLACEMENT and the disk comes down
  only by `-replace`. **Stage 5 DONE, every pass** — the governed lake exists, is granted, shared and
  consumed; `GOVERNANCE.md` is the one copy of the ontology; register **13 rows / 24 triples**; the
  derived zone was **removed** 2026-08-26/27 (D19 revised) and `DataScientistAccess` carries no `athena:`.
  **Stage 16 DONE 2026-08-26** — the sandbox lake, created, exercised and logged in one day.
- **Three things Stage 5 leaves standing:** no principal can start the crawlers (**OQ 19**), so D18/D25
  ingestion is broken at one end; `EXC-02`'s uncollectable object; and no Athena in Data Governance.
- **Standing SMUS mechanics:** a blueprint configuration is applied **from the member account**; an
  existing one is **immutable via `awscc`**; the D13 boundary field is **write-only**, so drift never shows
  in a plan (`US-8` is the sentinel, and **`list-roles` omits any permissions boundary — always `get-role`**,
  which Stage 9's `DT-9` now inherits); an incomplete configuration pins its projects in **both** directions.
- **SMUS is a Lake Formation admin in Sandbox** (2 service roles, self-appointed at the first project).
  `consumer-data-v0.5.0` declares ONE create-time admin with `ignore_changes` over the list; the defence
  is `./aws/datalake.py` `DL-13`, not a plan. `-refresh=false` is forbidden on that slice. **OQ 24** keeps
  the governance half.
- **A cached SSO token is keyed by `sso-session` name, NEVER by user** — the wrong identity fills the
  right one's slot and `aws sso login` then succeeds doing nothing; remedy is `aws sso logout` + portal
  sign-out. The battery separates that from a real ceiling breach by asking **IdC** what the token holds.
- **A denied call does not always name the policy** — attribution moves to a **contrast probe**: the same
  call from an OU the deny misses.
- **Standing rules that outlive their stages:** never add an `sts:` action to the RCP without reading
  `CT.STS.PV.1`'s exclusion note; **resolve an account by name only with the exact vended name** (every
  one carries an ` Account` suffix and a SUSPENDED `Sandbox` sits in the roster — filter on `ACTIVE`);
  subnets anchor on AZ `zone_id`; check the SSO token before each probe block and read the denial
  **wording**, never the exit code; account-level BPA is hand-managed; **Log Archive and Audit hold no CLI
  profile**; 1d step 9 is the only sanctioned by-hand use of `AWSControlTowerExecution`.
- **Before reporting a gap, read the file that owns it:** unexercised denies → `POLICIES.md`; "expected"
  readings → `docs/AWS_STATE.md`; SMUS findings → open questions 12-15, 20, 21.
- **Deferred by decision — do not offer to close:** the USD 50 budget notifies nobody (D12); OQ 10 waits
  for N=2; the Config recorder is left alone and Management deliberately unrecorded (Stage 12 hooks).
  **Every governed account sits under `us-west-2`.**
- **All 38 decisions closed.** Still needed from the user: **the domain name** (blocks Stage 13 — the only
  blocking input left in the plan).
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
39. **What a console wizard fills and the authoring API does not require is still required — the validator
    is the deploy AND the teardown, so an incomplete object pins its dependents in both directions; and
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
