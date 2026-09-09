
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
| **Anything VPN** — the pieces, starting/stopping the hub, connecting a device, a tunnel that will not come up, a key event (loss, revocation, rotation), or a shell on the VPN host | [`docs/plan/runbooks/vpn.md`](docs/plan/runbooks/vpn.md) — one runbook, three parts. **REWRITTEN 2026-09-06 for the Production home**: the host is `production/vpn/` in `VPC-Networking`, profile `awsds-infra-prod`, and **`make hub-up` / `make hub-down`** start and stop it *with the proxy* — never `make up ENV=…`, which raises endpoint sets a tunnel does not use and now **refuses** while the hub is down. **The Elastic IP and the host key did NOT move** (transferred, and copied by hand), so **the only client edit is `DNS = 10.31.0.2`** — and without it the tunnel comes up and nothing resolves. **§S** the system: the FORWARD chain is the perimeter (RFC1918 accepted, the rest REJECTED), the masquerade has a deliberate hole so Squid sees a per-device address, and the isolated-tier NAT job is **gone**. **§C** the client: what it may reach and when it does not work — **the procedure itself moved to the row below on 2026-09-07**. **§K** the keys — loss is recovery, never rotation, and the account move is that rule's strongest evidence — and **§K0a is the SSM session** |
| **Connecting a LAPTOP** — the session's up/down order, the `.conf` and its four checks, and the proxy on macOS (system, terminal, Chrome) and Linux | [`docs/plan/runbooks/client-vpn-proxy-configuration.md`](docs/plan/runbooks/client-vpn-proxy-configuration.md) — **new 2026-09-07**, the procedures moved out of `vpn.md` §S5 and §C0-§C3; four short sections, the reasoning stays in `vpn.md`. **macOS's system proxy is NOT the path** (issue #67 — ignored while the tunnel is up, and it breaks the `aws` CLI when the tunnel is down): the terminal's variables and Chrome's `--proxy-server` flag are. **Nothing private goes through the proxy, and everything public does — AWS included**. **Two profiles since 2026-09-08** (§3.3; `vpn.md` §C7): *monitored* (full tunnel, the institution's) and *split-tunnel* (the private ranges only, internet direct and unmonitored — for building the plan; persona work still through the proxy, the infrastructure user proxy-free) |
| **The PROXY inside a SageMaker space** — the `NO_PROXY` value, `apt`, the Code Editor's extension gallery | [`docs/plan/runbooks/sg-proxy.md`](docs/plan/runbooks/sg-proxy.md) — **the space side**, as `client-vpn-proxy-configuration.md` is the laptop side. `NO_PROXY` is **generated** (`terraform output -raw no_proxy` on `sandbox/egress`), never transcribed. **The variables stop at `sudo`** — `apt` needs `-o Acquire::http::Proxy` or the image's own file — and **the VS Code server never had them at all** (6d step 8) |
| **Anything EGRESS, PROXY or the hub topology** — where the internet is reached, which VPC a thing belongs in, why there is no NAT gateway | [`docs/plan/decisions/D38-single-egress-hub.md`](docs/plan/decisions/D38-single-egress-hub.md) (the decision, closing OQ 23) + [`docs/plan/stages/stage-06c-networking-hub.md`](docs/plan/stages/stage-06c-networking-hub.md) (the build). **Peering shares an address, never a path** (Lesson 44): no spoke has a default route, the single egress is an **explicit proxy**, and the hub carries no interface endpoint with private DNS |
| **The NETWORK as built** — VPCs, subnets, routes, peerings, egress, VPN, DNS, security groups, every internal address; **how a SageMaker app sees the internet, and what can reach one** | [`docs/NETWORK.md`](docs/NETWORK.md) — code plus measurement, with diagrams. **Its first section now names the six facts Stage 6c replaces**; until that apply the tables below it are current, and they are **re-measured** then, never edited ahead. The runbooks stay the procedures, `AWS_STATE.md` stays what is *expected* |
| **Anything BUILDBOX** — the `[E]` `amd64` build host of St.6 5.0, now `production/buildbox/` | [`docs/plan/runbooks/buildbox.md`](docs/plan/runbooks/buildbox.md) — seven short sections: what it is, why it exists (**the images are `amd64`, the laptop is `arm64`**), the components, `up`, **§S space** (the 64 GiB root against two images that share layers — prune before recreating), **§P push** (**build and push are ONE session** — the volume dies with the host; the identity arrives as an ECR **token**, never as a permission), `down`. **It MOVED at 6c 5.8**: `VPC-SharedServices` private tier, **no route at all** — the internet is the proxy and the host is told in **four** places; `production/egress/` is now a **prerequisite** (its SSM endpoints are the only door), the `probes/` exclusion is **deleted**, and the far-end ECR refusal no longer applies because the host is in the registry's own account |
| **Anything SANDBOX LAKE** — the ungoverned fourth Sandbox bucket (`awsds-sandbox-lake`, St.16), a per-group prefix, wiring or unwiring a project's S3 connection, either read/write test, or **code that lists/reads/writes it** | [`docs/plan/runbooks/sandbox-lake.md`](docs/plan/runbooks/sandbox-lake.md) — six short sections, **exercised 2026-08-26** (except §R's trust half — a real project's death): what it is and is not (**not the governed lake**), **§G** the prefix contract, **§W** wire a project (a grant + a trust entry + the portal form), **§T** the two tests (the in-image direct-refusal test is UNRUNNABLE — the laptop is that control's home), **§P** the Python examples (notebook = plain boto3, the plugin vends; laptop = explicit vend, the only door), **§R** revoke — an orphaned grant is `SL-4`'s finding |
| **A policy is about to be attached, or was amended** | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md) — the probes, and the two distinguishable outcomes of each. **Running them is `./aws/probes/scp-battery.py`** ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| Explaining the design to someone | [`README.md`](README.md) — the argument for the account split and the three distinctions |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md) — almost never |

Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1c step 7` — never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

### Current position

- **STAGE 6c DONE (2026-09-08), PASS 8 INCLUDED — two client profiles.** The **split-tunnel** profile beside
  the **monitored** one (`objectives.md`'s words — *open* is the proxy plane's `mode`, not a profile): same
  key, same `DNS`, `AllowedIPs` = the five VPC CIDRs + `10.90.0.0/24`; laptop-only, **no host change**;
  `vpn.md` §C7. **Measured 2026-09-08**: the reach difference is by **identity**, never by network —
  `InfrastructureAccess` direct; a persona's call direct is an *explicit* deny, through the proxy an
  *implicit* one or a success; the host's `REJECT` counter flat across a burst; the App Store client sends
  **every DNS query** through the tunnel and installs an inert `I`-flagged default on the `utun`. Carried to
  6d decision due 4 (Method 1 expected to work under split-tunnel; 7.5 reads both) and Stage 11 step 3.4
  (input (f): the portal alarm fires on split-tunnel sessions). Decision due 4 taken as **(c)**:
  the access log stays in Production until Stage 11 step 5.1 folds it in; `PX-4` a note.
  Pass 6: **a space started while `sandbox/egress` is down HANGS** at "IDE configuration in progress";
  the no-internet timeout is the **host's per-destination ICMP rate limit** (Lesson 55); a laptop call takes
  **two doors by service family** (`sts` public, `s3control` via the hub's S3 gateway endpoint); **`VP-3`
  reads every account**; **6.6 taken as (ii),
  recorded acceptance** — Stage 11 step 3.4 re-takes it, its 5.2 alarms on an off-proxy portal session.
  **`aws sso logout` invalidates EVERY cached session's token; a browser sign-out invalidates none.**
- **D38 §6 AMENDED (2026-09-08, the user): THE BUILD PLANE IS `open`, NOT AN ALLOW-LIST.**
  `production-foundation` (= all of `VPC-SharedServices`) reaches **any** public name through the proxy,
  everything logged. **A build host's control is the reviewed Dockerfile, not a hostname list** — and the
  list was a treadmill whose own comment called its next revision *"a WHEN rather than an IF"*.
  `proxy_allow_shared` and `d5l0dvt14r5h8.cloudfront.net` **deleted**; a plane's mode is now decided by
  **which of two maps** it is in (`proxy_allow_by_plane` / `proxy_deny_by_plane`), with plan-time
  preconditions on both. **`sandbox-foundation` is untouched** — the first time source-scoping earns its
  keep in the *permissive* direction. Unchanged: the three global denies, the absent default route, the
  3128-only SG. **A plane is a CIDR, not a host** (Lesson 29). `DN-4` rewritten to *"no plane is `open`
  except the ones a decision names"* (`OPEN_BY_DECISION`, reasons in the pass line). **APPLIED 2026-09-08**
  with `open-vsx.org` in one parameter write: `0 added, 1 changed`, re-plan `No changes`, `DN-1`..`DN-4`
  pass. **`PX-3` still owed** (the running `squid.conf`; needs `--on-host`), and 9.5 — one build and push.
- **SQUID MATCHES THE NAME THE CLIENT REQUESTED, AND NEVER A DNS ANSWER** (measured 2026-09-08). **A CNAME
  is INVISIBLE** (`static.crates.io` works with no CDN entry); **an HTTP redirect is a NEW name**
  (`codeload.github.com`, the ECR CloudFront); **a bare entry matches EXACTLY** — `github.com` covers
  neither `api.github.com` nor `raw.githubusercontent.com`. **`amazonwebservices.com` is NOT
  `amazonaws.com`** (`idetoolkits.*` refused beside `idetoolkits-hostedfiles.amazonaws.com` allowed).
- **6d STEP 3 RUN, STEPS 8 AND 9 OPENED (2026-09-08).** The proxy works from a space with the variables exported
  by hand (`pypi.org` 200, `example.com` 403, `NO_PROXY` held on **two** channels). **Two components then
  failed for ONE cause — no proxy IN THE PROCESS, never a refused one**: `sudo` strips the variables
  (`apt` needs `-o Acquire::http::Proxy`, or the image's own file) and a **Code Editor**'s VS Code server
  never had them — four `ENOTFOUND open-vsx.org`, **AWS's own two extensions**, at every space start.
  `open-vsx.org` authored onto `proxy_allow_sandbox` (**20 → 21, UNAPPLIED**); step 8 owns the delivery
  mechanism and the **unread asset host**; 2.2 grew two image-side files. **A missing plane name can fail
  WITHOUT a `403`** — the second instrument is `/awsds/sandbox/dns-firewall`, which **answered 8.2**
  (`open-vsx.org` BLOCK from a Sandbox address: **the space asked**) and named three more the Code Editor
  needs; **the hub carries no DNS Firewall**, so an `ENOTFOUND` can only come from a compute VPC.
  `--noproxy '*'` → `000` measured **DNS**, not the absent route. Measured on the plane: **Python, Rust and
  `github.com` clone all work**; `uv`/Julia/R still owed.
- **STAGE 6d: 3.6, 7.2 AND 7.1 DONE (2026-09-07); STEP 7 RE-CUT AROUND ONE FINDING — THE CONNECTION
  METHOD DECIDES THE PERIMETER.** 7.1: **nothing to add on either side** — the space's seven names are all
  in `sandbox/egress/`, the laptop's five ride the `open` tunnel plane; `ec2messages` is on neither vendor
  page. The deep link's `StartSession` is made **server-side by the project role** (AWS's managed policy
  scopes it by the two DataZone tags, in Allow form; usable **off-VPN**); SSH/Toolkit use the laptop's
  credentials (VPN-bound) but the persona sets hold **no Allow** and a persona session carries **no
  DataZone tag**, so 6a's pair would **deny every space, not scope** — decision due 4 (recommended:
  Method 3 + an `IDC_UserName` Allow + `StartSession` denied on the D13 boundary). A remote space needs
  **≥ 8 GB** (`ml.t3.large` **0.100/h**, measured); **the space path carries NO instance ceiling since
  2026-09-07** (`sagemaker-denies-v0.2.0`: `CreateApp`/`CreateSpace`/`UpdateSpace` exempt via `NotAction`,
  simulated; jobs keep the list) — **APPLIED 2026-09-07**, both re-plans `No changes`, read back from both objects; **the VS Code server is downloaded by the SPACE** —
  `remote.SSH.localServerDownload=always` keeps the compute plane unchanged (decision due 5). The
  `session-manager-plugin` honours `HTTPS_PROXY` only if the env reaches it: a browser-launched VS Code on
  macOS has none → direct dial → REJECT → **timeout**. **Portal Query Editors has NO endpoint in any VPC**
  (3.6). `conda` and CRAN are **not** on the compute plane (3.1). Pending a sign-in: the project role's
  policies.
- **THE CLIENT PLANE IS `open`, NOT AN ALLOW-LIST (2026-09-07).** The client's internet is **monitored**;
  the restriction belongs to the **compute** plane (`sandbox-foundation`, **21 names**) —
  **and since 2026-09-08 the BUILD plane is `open` too**, so `allowlist` is now the compute planes' mode,
  not every spoke's. Each plane carries a
  `mode`; **empty means OPPOSITE things** — allow-list empty = refuse everything, deny-list empty = permit
  everything. **The parameter is DATA (30 min); the renderer is CODE (a new host)** — a State Manager
  `Success` only proves the script the host already has ran.
- **THE TUNNEL IS DUAL-FAMILY SINCE 2026-09-07** (`wireguard-v0.6.0`, `fd90::/64`): it carries no IPv6 —
  it **rejects** it — because `AllowedIPs = ::/0` was **inert** without a matching `Address` (Lesson 56).
  Not a control against the device's owner. **macOS: the system proxy is NOT consulted while the tunnel is
  primary** (issue #67): Chrome's `--proxy-server` flag or Firefox; with the tunnel **down** the same
  setting breaks the `aws` CLI — `NO_PROXY='*'` is the override. **The no-internet check times out OR refuses fast — the host's per-destination ICMP rate limit
  decides** (Lesson 55, mechanism corrected 2026-09-07): the evidence is the counter on the refusing side.
- **Pass 5 made design B real:** zero NAT as code; endpoint sets **counted** — Sandbox **18**, Staging
  **11**, SharedServices **13**, Workloads **0**; estate fixed rate **0.390/h**; `optional_service_groups`
  behind `make up ENV=<x> GROUPS=…` (empty by default); DNS Firewall **63 → 10**. **Pass 7:** `make
  hub-up` / `hub-down`; a spoke's `make up` **REFUSES** while a hub host is stopped; `./aws/proxy.py`
  `PX-1`..`PX-5`; `NT-11`/`NT-12` (two-sided, by CIDR).
- **`NO_PROXY` is GENERATED, never written** (`vpc-egress` output): 8 of 29 service names are not
  derivable from the token and a gateway endpoint has no `PrivateDnsName`, so S3/DynamoDB are hand-named
  in **both** spellings. **Squid matches the hostname the client REQUESTED** — a redirect is a new name; a
  refusal over `https` reads `000`. **`production/egress/` is a PREREQUISITE of a build** (the buildbox's
  SSM door).
- **Module tags: `vpc-egress-v0.10.1`, `wireguard-v0.6.0`, `vpc-v0.3.1`** (`vpc-egress-v0.9.0` and
  `vpc-v0.3.0` ABANDONED on origin — Lesson 46). **`-input=false` on every plan AND apply** (Lesson 47);
  **never pipe a command whose exit code matters**. **`10.40.0.0/16` stays unallocated.**
- **STAGE 6b DONE.** `Development` → **`Staging`**; the provisioned product does not follow an
  out-of-band rename. **The chain is `Sandbox → Staging → Production`** — no Development account, ever;
  interactive compute is **Sandbox only**. **D38:** peering shares an **address, never a path** (Lesson
  44); one explicit Squid proxy, **zero NAT**, no spoke default route, **five peerings**; the hub carries
  no interface endpoint.
- **Orchestration is MWAA Serverless only** (USD 0.088/task-hour); workers accept no proxy — two AZs, a
  priced D9 exception; the `Workflows` blueprint is the **provisioned** shape, not this one. **The SMUS
  CI/CD tool deploys only into EXISTING projects**; the pipeline stays the deployer (D26/D28).
- **Landing zone closed — Stages 0-1d DONE.** Battery **100**. **Stages 2, 3, 4, 5, 16, 6a, 6b DONE.**
  Stage 5 register **13 rows / 24 triples**. Gates: `make check`, `check-ou`. Standing from Stage 5: no
  principal can start the crawlers (**OQ 19**); `EXC-02`'s uncollectable object; no Athena in Data
  Governance.
- **Standing SMUS mechanics:** a blueprint configuration is applied **from the member account**; an
  existing one is **immutable via `awscc`**; the D13 boundary field is **write-only** (**always
  `get-role`**); an incomplete configuration pins its projects **both** ways. **SMUS is a Lake Formation
  admin in Sandbox** (OQ 24); `-refresh=false` forbidden on that slice. **A cached SSO token is keyed by
  `sso-session` name, NEVER by user.** **A denied call does not always name the policy** — attribution is
  a **contrast probe**.
- **Standing rules:** never add an `sts:` action to the RCP without reading `CT.STS.PV.1`'s exclusion
  note; **resolve an account by exact vended name**; subnets anchor on AZ `zone_id`; read the denial
  **wording**, never the exit code; account-level BPA is hand-managed; **Log Archive and Audit hold no CLI
  profile**; auto-enrollment is ON; `INV-09` is **ten** principals. **Before reporting a gap, read the file
  that owns it:** unexercised denies → `POLICIES.md`; "expected" readings → `AWS_STATE.md`; SMUS findings
  → OQ 12-15, 20, 21. **Deferred by decision — do not offer to close:** the USD 50 budget notifies nobody
  (D12); OQ 10 waits for N=2; the Config recorder is left alone. **All 38 decisions closed; D38 §6 amended 2026-09-08.** Still needed
  from the user: **the domain name** (blocks Stage 13). **Every script is Python 3 on `uv`;
  `aws/cloudshell/` is shell.**

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
46. **A redirected or piped command hands you the pipe's exit code, not the command's — and the next
    step runs on a failure nobody saw.**
47. **A process waiting on stdin looks exactly like a slow one, and the lock it holds makes the symptom
    appear somewhere else entirely — `-input=false` is the whole fix.**
48. **A name another account resolves by is a cross-account contract, and no id-shaped gate can see it
    move.**
49. **A comment saying a knob is never turned is a claim about the callers that existed when it was
    written.**
50. **A check written to a stage's FINAL expectation is red for every pass until that stage ends — give
    it a discriminator, write it at the pass that makes it true, or name the gap as a dated exception.**
51. **Two intents sharing one list stay identical until they must differ — then a change made for one
    silently makes it for the other. Lesson 33's mirror, and the more dangerous half.**
52. **A wait whose only exit is SUCCESS waits forever once its subject is gone — silence is
    indistinguishable from patience.**
53. **Two systems expressing one intent in the same-looking syntax are not translatable by
    transcription — and they agree on the easy cases.**
54. **A program that has never been run is a claim: `validate`, `render` and `run` are three
    different verdicts.**
55. **A refusal the sender cannot see is indistinguishable from silence — and the refusal is real;
    the evidence lives in the counter on the refusing side.**
56. **A configuration line naming a capability the surrounding configuration does not have is
    INERT, and reads exactly like a working control — verify a routing directive from the
    ROUTING TABLE.**
57. **A paraphrase in a plan becomes the specification; an explanation of a requirement is a fork
    of it. Open the requirement before implementing the step that restates it.**
58. **Data and code can share a delivery path and have different costs — and the one that reports
    SUCCESS is the cheap one.**

**[`lessons.md`](docs/plan/lessons.md) also carries a second list — "What AWS does that its
documentation does not say"** — platform behaviours that cost a measurement to learn, each with its
date and its reading. Consult it before designing around an AWS behaviour nobody here has measured;
add to it when a vendor page turns out not to say the thing that mattered.
