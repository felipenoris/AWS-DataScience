
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
| **The NETWORK as built** — VPCs, subnets, routes, peerings, egress, VPN, DNS, security groups, every internal address; **how a SageMaker app sees the internet, and what can reach one** | [`docs/NETWORK.md`](docs/NETWORK.md) — code plus measurement, with diagrams. The runbooks stay the procedures, `AWS_STATE.md` stays what is *expected* |
| **Anything BUILDBOX** — the `[E]` `amd64` build host of St.6 5.0, its route, or why the VPN host is also a NAT instance | [`docs/plan/runbooks/buildbox.md`](docs/plan/runbooks/buildbox.md) — seven short sections: what it is, why it exists (**the images are `amd64`, the laptop is `arm64`**), the components (**the route is the reach; `vpc_nat_cidrs` is the capability**), `up`, **§S space** (the 64 GiB root against two images that share layers — prune before recreating), **§P push** (**build and push are ONE session** — the volume dies with the host; the identity arrives as an ECR **token**, never as a permission), `down`. It **must not coexist with `sandbox/probes/`** and a **stopped VPN host makes its route a blackhole, not an error** |
| **Anything SANDBOX LAKE** — the ungoverned fourth Sandbox bucket (`awsds-sandbox-lake`, St.16), a per-group prefix, wiring or unwiring a project's S3 connection, either read/write test, or **code that lists/reads/writes it** | [`docs/plan/runbooks/sandbox-lake.md`](docs/plan/runbooks/sandbox-lake.md) — six short sections, **exercised 2026-08-26** (except §R's trust half — a real project's death): what it is and is not (**not the governed lake**), **§G** the prefix contract, **§W** wire a project (a grant + a trust entry + the portal form), **§T** the two tests (the in-image direct-refusal test is UNRUNNABLE — the laptop is that control's home), **§P** the Python examples (notebook = plain boto3, the plugin vends; laptop = explicit vend, the only door), **§R** revoke — an orphaned grant is `SL-4`'s finding |
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
  (`INV-15`). D11: `scripts/tfhygiene/layers.py` + `make up`/`down`/`status`/`slices`; the
  **`ENV` list is `slices.py envs` alone** — `make help` and the missing-ENV guard read it (2026-08-23).
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
- **THE CDN WALL WAS AN API DEFAULT, NOT THE SERVICE (2026-08-23, same day 4.3 measured it; Lesson 30 on
  a default, `EXC-05` CLOSED, NOT APPLIED YET).** Chain evaluation is the **per-rule**
  `FirewallDomainRedirectionAction` — the module had never set it, so it took
  `INSPECT_REDIRECTION_DOMAIN`. **`v0.4.0` makes it a module INPUT (default INSPECT) and both Interactive
  slices pass `TRUST_REDIRECTION_DOMAIN`** — per slice, beside the list, like `v0.3.0` did to the list:
  inspect the QUERIED name, trust the chain. **It does not open the CDN** — the trust is ONE query
  transaction, so a redirection target asked for directly matches nothing and is BLOCKED. So
  pip/cargo/apt/ECR-Public **do** have a path under A. **12 hop entries off Sandbox (10 distinct), 1 off
  Development**: a listed hop is now a WIDENING, and `DN-2` inverted to say so. **Two bypasses stay open,
  neither DNS-closable** — a raw address, and a query to `1.1.1.1`/DoH the VPC resolver never sees. The L7
  answers are `architecture.md` §4.3a, **not built**.
- **Stage 5 DONE, every pass (2026-08-18/20) — the governed lake exists, is granted, shared and
  consumed.** `docs/GOVERNANCE.md` is the one copy of the ontology + grant rules; **one data CMK per
  account** (`alias/awsds-<env>-data`). **Producer:** 5 `awsds-data-*` buckets, `raw`+`curated`
  registered, 2 LF-Tag keys, `curated.sample_trades` (12 synthetic rows), 2 **never-run** crawlers, 2 TBAC
  shares (**INT-11 closed**). **Consumer, per account:** own CMK, own `DataLakeSettings`, 2 links, 4
  re-grants — the derived bucket and the enforced workgroup **DESTROYED 2026-08-26/27** (D19 revised).
  **Persona:** `DataScientistAccess` is **7 statements** since that day, six of the query/derived family
  gone — no `athena:`, no derived, no scratch. **Full inventory: `AWS_STATE.md`'s lake row + the two
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
- **1.7 DONE AND FULLY ATTRIBUTED 2026-08-22 — INT-16 ANSWERED, fallback (ii): the permission-set
  `aws:SourceIp` deny does NOT reach the portal.** It opened with the tunnel down and enumerated both
  profiles for a `DataScientistAccess` identity; identical with it up (EIP confirmed). **The
  same-sitting console contrast closed the attribution**: off VPN the console refused
  `logs:DescribeLogGroups` **`with an explicit deny in an identity-based policy`** — no SCP or boundary
  produces that wording and no other deny those six documents carry reaches `logs:` — clean with the
  tunnel up. **The message named the persona role and `us-west-2` itself**, so identity and the
  wrong-Region trap were ruled out from inside the reading, not from the operator's report. **VPN-only
  APIs and console, not a VPN-only portal**; `README.md` now carries the qualification. **The off-VPN reading
  (same day, evening) delivered the choice's missing input in the STRONG form: all three rungs —
  create, space, JupyterLab — pass IDENTICALLY on and off VPN.** `VpcOnly` governs the app's ENIs and
  egress, never the user's ingress (the Studio front-end under the portal session). `README.md` item 3
  states the full reach; **the ripe decision — the user's — is fallback (i)
  (`DenyUserAccessFromUnauthorizedVPCs` on the domain execution role, re-keyed on the EIP, AWS's
  `*:user-*` third condition kept) versus recorded acceptance; recommendation on record: (i).**
- **CREATING IS AUTHORIZED IN TWO LAYERS, AND BOTH STARTED AT ZERO (measured 2026-08-22, one per
  sitting).** Layer 1, the PROFILE: `CREATE_PROJECT_FROM_PROJECT_PROFILE` on the root domain unit —
  governance `grants.tf` **APPLIED 2026-08-22**: `experimentation`→`sso-group-data-scientists`
  (standing), `engineering`→`sso-group-deployment-managers` (**D21's open half**; removal is the
  expected outcome if it closes). Layer 2, the BLUEPRINT: the first real project then got past
  `CreateProject` and **rolled back on `Caller is not authorized to create environment using
  blueprintId`** — `CREATE_ENVIRONMENT_FROM_BLUEPRINT` sits on each blueprint CONFIGURATION, and all
  22 had ZERO grants (the console's "Authorized domain units" emits it; the Put API does not).
  **The entity id is the undocumented `<member-account>:<blueprint-id>`** — the configuration's OWNER,
  and every other spelling is rejected; principal copied from `aws-samples`' SMUS-IaC sample
  (root-unit projects, `CONTRIBUTOR` — a measurement where ours would be a guess); the detail is a
  JSON-string `"{}"` in awscc. `sagemaker-prereqs` **`v0.3.0`** adds the 11 grants per member
  (`for_each` the configurations) + `root_domain_unit_id`; both member slices bump the ref —
  **APPLIED 2026-08-22, both members: `11 added`, re-plan `No changes`, 22/22 read back** (the member
  MAY AddPolicyGrant on its own configuration — the cross-account risk was empty). Every grant field
  **`createOnly`**, both layers.
- **THE WIZARD-FIELD LADDER (2026-08-22, one sitting): what the console's Enable-Tooling wizard
  fills and the Put API does not require is validated at DEPLOY *and* TEARDOWN** — an incomplete
  configuration pins its projects in both directions (a stuck project cannot even be deleted).
  Three rungs measured: the `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grants (v0.3.0), `manageAccessRoleArn`
  (v0.3.1), and `S3Location`+`KmsKeyArn` regional parameters (v0.3.2 — `awsds-<env>-smus-projects`
  per member via the house s3-bucket module; the **project CMK found its consumer**; bucket name is
  FREE, the managed policy reaches content by `*/dzd*/<project>/` path). Each config fix = apply
  (predicted `NotUpdatableException`) + user-authorized Put + re-plan `No changes`. Tooling's set is
  believed complete — it now matches every wizard field. **Rounds 5-6 (same day, v0.3.3) were NOT
  wizard fields but two independent defects: both service-role TRUSTS pinned the MEMBER account
  where the documented `AmazonSageMakerProvisioning-<domainAccountId>` trust demands
  `aws:SourceAccount = the DOMAIN account` (the service could never assume them; invisible in the
  member trail — cross-account service denials leave no event, attribution came from the doc), and
  the project CMK's delegate-to-IAM policy reached no service principal (the validator's
  `DescribeKey` is `datazone.amazonaws.com` + the domain execution role; the key now carries the
  documented SMUS statement set minus Redshift/Airflow, category 2). `3 changed` per member,
  in-place, no Put. Round 7 (governance slice, no tag): the profile locked `lifecycleManagement =
  "true"` against the template's `ENABLED`/`DISABLED` enum — CreateProjectProfile validates nothing
  against the template, and the CFN 400 that caught it was the FIRST in-account failure (the trust
  fix proven; the three stuck projects all deleted). UpdateProjectProfile then validated what Create
  did not: required blueprint params without defaults must be declared — exactly two across all 11
  (`S3Bucket.bucketName`, `S3TableCatalog.catalogName`, both literal `Ref` → per-project names),
  now editable placeholders in both profiles. Templates are downloadable via the blueprint's
  `templateUrl` by an associated account — check locked values against them, not against prose.**
- **THE CREATE PATH CLOSED 2026-08-22 — the FIFTH attempt created a project END TO END** (`ACTIVE`,
  Tooling stack `CREATE_COMPLETE`, ~4.5 min): the behavioural proof of all seven findings, and the
  three stuck projects deleted cleanly. **Verification (v)'s first real reading: the D13 boundary IS
  on the provisioned role — delivered via the stack TEMPLATE** (the write-only configuration field is
  injected as the `ToolingUserRole`'s `PermissionsBoundary`; **the template's two conditional EMR
  roles carry NONE** — AWS's template, noted for the day `createEmrResourceInTooling` turns true).
  **US-8 said the opposite first and the instrument was wrong** (Lesson 30): `iam list-roles` OMITS
  `PermissionsBoundary` by documented contract (`GetRole`-only, with `Tags`) — fixed to `get-role`
  per role, re-run `pass`. **What St.6 still owes: the fallback-(i)-or-acceptance decision (the 1.7
  bullet), the off-VPN probe's teardown confirmed, then passes 3-5 + 5.1 (less 4.1 and 4.3, RUN 2026-08-23; `vpc-egress-v0.3.0` moved the list OUT of the module — each slice owns its own, default EMPTY; `EXC-04`)** — pass 3 stands on a
  measured create path. **5.0 is DONE** (`default-v0.1.0`
  pushed to both repos 2026-08-22, one buildbox session). Decisions 1 (EMR-S vs Glue) and 6 (prefix
  shape) stay in-stage; **2 is delivered** (TIP `false`, non-editable, both profiles).
- **s3-read-write MERGED 2026-08-24 — the laptop reads/writes/lists its SMUS project's S3 path by
  vending the PROJECT ROLE through S3 Access Grants** (strategy 1-A, the user's; consumer
  `s3-read-write/`, an independent uv project). `awsds-org-project-storage-vending` is the estate's
  **first customer-managed policy** (both members' `foundation/`, referenced by name from
  `DataScientistAccess` — decision 4's mechanism demonstrated, its expired blocker corrected in the sso
  README). The handshake opens nothing; **one hand-made grant per project × persona role** does —
  membership-blind, accepted with the decision. Instance facts 2026-08-24: Sandbox's is **SMUS-born**
  (2026-08-22), carries **no IdC association** (directory grantees unavailable — OQ 13's mapped option);
  **Development has none until its first project** (the policy inert there by design). Full inventory:
  `AWS_STATE.md`'s vending row. OQ 22 (managed-policy revision watch) is the user's to schedule.
- **THE PORTAL ON THE VPN BROKE IN TWO LAYERS; BOTH ARE NOW MEASURED CLOSED.** **(1) DNS, 2026-08-24**
  (Lessons 40-42): `datazone`'s private zone is authoritative for its subtree, so `agent.datazone…` —
  which AWS's network-isolation page lists **public-internet-required** (its THIRD table) — was NXDOMAIN
  for every VPC-resolver client, zero CloudTrail arrivals; 4.2's "REQUIRED under VpcOnly" was a misread of
  a design-B-scoped table (6 of the 15 never existed here). **REMOVED from both `extra_services`
  (issue #39); APPLIED + MEASURED 2026-08-26, both halves** — the name resolves publicly, and DataZone
  events carry NO `vpcEndpointId`, splitting by plane (app → NAT, browser → VPN EIP). **12 → 11**
  endpoints per Interactive account, 0.170 → 0.160/h.
  **(2) THE BROWSER, 2026-08-26 (Lesson 43):** the portal then broke with the SAME words — surviving zones
  answer client-plane names with **private** addresses, and a **public** origin needs Chrome's **Local
  Network Access** grant to reach one. Granting it restored JupyterLab + catalog (CloudTrail: catalog =
  Glue, JupyterLab = SageMaker API, from the VPN host's PRIVATE address, across ~25 min of ZERO arrivals).
  Every `aws/` instrument, `dig` and `curl` read clean throughout — **no gate here can see it.**
  **The rule over both**: no endpoint whose private zone shadows a CLIENT-plane name may live in the VPC
  the client resolves through. `datazone` could leave; `sagemaker.studio` cannot — so **OQ 23 (client
  plane off this resolver) is the only structural repair**, the grant is the interim, and design B must
  re-add `datazone` and move the portal instead. Meanwhile **`EXC-06`**: the user's deliberate `*`
  on Sandbox's allow-list (portal sign-in fix; cannot fix shadowing; `DN-3` fails on the divergence).
  Design-B input RE-SCOPED 2026-08-25 (D5/D6 + objectives): the portal's public egress is the CLIENT
  plane's — B constrains COMPUTE only; A-vs-B = short whitelist vs empty, both behind the St.11 proxy (OQ 23).
- **STAGE 16 DONE 2026-08-26 — the SANDBOX LAKE: created, applied, exercised, closed and LOGGED in ONE
  day** (stage file §"What ran" = the record; `docs/log/log-stage-16-sandbox-lake.md` written by Claude
  on request, 6.3). **The standing state — bucket, ONE access role, location, 3+1 grants, wired project
  `avhvbqn37ty7m8`, connection `sandbox-lake`, invariants — is `AWS_STATE.md`'s sandbox-lake row, not
  here.** Facts that OUTLIVE the stage: **(1) the SMUS JupyterLab image ships
  `aws_s3_access_grants_boto3_plugin` (1.3.0)** — every "direct" S3 call auto-vends, credential cache
  included, so an in-image direct-refusal test is UNRUNNABLE and the laptop is that control's only home
  (§T). **(2) Revocation timing (§R, measured on a sacrificial grant)**: the vend door closes between
  **+1 s and +19 s** of the delete — a fresh 900 s bearer was minted INSIDE the window — and issued
  credentials survive revocation to their own expiry (horizon = delete+propagation+duration). §R's
  trust half UNEXERCISED (waits a real project death); (iv)'s object half waits St.11 data events.
  **(3) `SL-4` hardened by its FIRST LIVE ANOMALY**: the old classifier took any `AWSReservedSSO_*`
  grantee for a tenant; now: tenant table + exact `<group>/*` shape. **(4) A sacrificial-revoke
  grantee must hold NO standing grant** — with a tenant grantee the standing `<group>/*` grant answers
  every post-delete vend and the refusal is unmeasurable. Verification (ix): match `grant_scope`,
  never `grants[0]` (the lake lists first).
- **THE APPLY FOUND SMUS AS A LAKE FORMATION ADMIN IN SANDBOX (2026-08-26; 2 service roles, self-appointed
  at the first project).** Surfaced only from an unrelated plan — `DL-5` reads `parameters`, not `admins`
  (Lessons 17 + 31). Settled in TWO steps the same day: v0.4.0 ADOPTED the seats (froze the list — wrong,
  the user's question caught it), **`consumer-data-v0.5.0` is the answer: ONE create-time admin +
  `ignore_changes = [admins, allow_full_table_external_data_access]`** (the catalog.tf Iceberg shape,
  Lesson 23). **MEASURED: 3 admins live, 1 declared, plan `No changes`** — and `-refresh=false` is the one
  defeat, forbidden on that slice. **The plan's defence is REPLACED by `DL-13`** (datalake.py; first run:
  producer+dev `pass`, sandbox `note` naming both seats): FAIL on the required seat missing, FAIL on a seat
  nobody granted, `note` on the SMUS pair. **OQ 24** keeps the governance half: whether a SMUS role *should*
  administer LF (it can grant itself anything in the LOCAL catalog, resource links to `raw`/`curated`
  included) — St.6's residue; the seats cannot just be revoked (the create path was measured AFTER them).
- **Standing St.6 mechanics:** a blueprint configuration is applied **from the MEMBER account** (the
  Put takes no account param); `awscc`'s carries **`environment_role_permission_boundary`** and the
  `aws` resource does not (INT-15's mechanism, Lesson 8); **an EXISTING configuration is IMMUTABLE
  via `awscc`** (createOnly+write-only ids break every update patch — `NotUpdatableException`): a
  field change is a full-object `put-environment-blueprint-configuration` matching the committed
  code (user-authorized per occurrence; Tooling manage-access 2026-08-22 was the first) or a
  replace, never an update — and **an incomplete configuration pins its projects in BOTH directions**
  (deploy AND delete validate it); **`athena:UpdateSession` is in no API model**
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
- **THE DERIVED ZONE IS RE-HOMED ONTO THE SMUS PROJECT PATH (2026-08-26 evening, the user's decision;
  D19 revised — the one copy).** Trigger: 2.4's reading answered (xviii) — the path is
  `<domain>/<project>/<scope>/`, no person grain; the project's OWN enforced workgroup writes to
  `dev/sys/athena/`; a deleted project KEEPS its prefix; the projects bucket has NO current-object
  expiry (OQ 25, now the derived zone's expiry question). **`awsds-<env>-derived` + `awsds-<env>-athena`
  + the persona's whole Athena/derived family are REMOVED** — `DataScientistAccess` carries no
  `athena:` action; SMUS is the only query surface in member accounts. The data CMK SURVIVES (Sandbox:
  the sandbox lake's key; Dev: held empty, dated); its persona statement removed (would have been a
  KMS-layer path around the lake's vending door). Stage 6 decision 6 DISSOLVED; 2.6 re-cut to the
  removal choreography; (xix) re-homed to the projects bucket; Stage 5 step 9.3's extension point died
  unconsumed. `DL-8`/`DL-9` flipped to ABSENCE checks (FAIL until the destroys apply — deliberate);
  `DP-4` re-aimed at `*-smus-projects`. **APPLIED 2026-08-26/27** (`consumer-data-v0.6.0`): buckets emptied by
  hand then destroyed, both workgroups deleted, both key policies tightened; three slices re-plan `No
  changes`, `DL-8`/`DL-9` `pass`. **`DeleteWorkGroup` REFUSED both workgroups first — query HISTORY is
  "contents" (4 and 2 executions, 0 named queries), no API deletes an execution, and `force_destroy` was
  unreachable because the resource had left the configuration carrying the flag: A DESTROY-TIME FLAG IS
  SET BEFORE THE RESOURCE IS REMOVED, never in the same version.** Production and Staging NOT covered
  (no SMUS in either) — Stage 9 re-decides where its results land.
- **All 37 decisions closed** (D30 as a revert; **D5/D6 re-scoped 2026-08-25** — two egress planes, one proxy). **Still needed from the user: the domain name**
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
