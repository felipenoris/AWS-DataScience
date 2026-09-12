# General Objective

A Data Science environment on AWS, in one personal account tree: VPN-only access, SageMaker Unified Studio
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

`terraform` **1.15.8**, the `aws` client, `uv` **v0.12.5**, `jq`,
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

| File | What it holds, and the rule |
|---|---|
| [`docs/log/`](docs/log/INDEX.md)`log-stage-NN-*.md` | Every step performed by hand in AWS, one file per stage, mirroring `docs/plan/stages/`: the stage file's slug with a `log-` prefix. Written cooperatively; Claude writes only when the user asks, in that sitting, never on its own initiative. Every entry names whose hand wrote it, and a measurement the user pasted stays verbatim. English, Markdown, no account ids, concise. The rules: [`docs/log/INDEX.md`](docs/log/INDEX.md), "How an entry gets written" |
| [`docs/log/INDEX.md`](docs/log/INDEX.md) | The one file under `docs/log/` Claude maintains on its own. After reading a stage log, bring its `Records` cell to what the file contains: one line saying what is inside, never a restated step |
| [`docs/ORGANIZATION.md`](docs/ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes; never a copy of the slice tree, which lives in `docs/plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) | One row per entry in every document in `policies/`, all four policy types. Reviewed in the same sitting as any policy change, attachments included. `./scripts/check-index.py` decides the mechanical half; whether a row is still true is the reading |
| [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md) and [`terraform-modules/consumer-data/README.md`](terraform-modules/consumer-data/README.md) | The same discipline for the lake, producer and consumer side: one row per bucket/key-policy `Sid`, per LF-Tag assignment, per grant, per settings attribute; the module README is what its calling slice (`sandbox/data/`) points at. Reviewed in the same sitting as a change to the `.tf` files. No mechanical check exists; the `.tf` comments carry the reasoning, these files the index |
| [`docs/NETWORK.md`](docs/NETWORK.md) | The network as built: addresses, routes, both egress paths, VPN, DNS, security groups, the two reach questions. Reviewed in the same sitting as any change to a network-bearing slice or module (its §2.1 names them). `./scripts/check-network-doc.py` is the mechanical half; whether a sentence is still true is the reading, and a moved `[P]` fact is re-measured with the `aws/` instruments |
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

Stage numbers refer to `docs/plan/stages/`. Always read `docs/GENERAL_PLAN.md` before planning or executing
a step; it is the plan core and carries both indexes. Then read only the stage file and the decisions its
`Consumes` row lists.

### What to read, and when

This table is the only routing map; every other file points here rather than repeating it.

| Task | Read |
|---|---|
| Anything | this file + [`docs/GENERAL_PLAN.md`](docs/GENERAL_PLAN.md): principles and the route |
| What the project must achieve, before planning or reviewing a stage | [`docs/plan/objectives.md`](docs/plan/objectives.md), the requirements brief in the user's words |
| Execute a stage | [`docs/plan/stages/`](docs/plan/stages/INDEX.md)`stage-NN-*.md`, the decisions in its **Consumes** row, and [`docs/plan/conventions.md`](docs/plan/conventions.md) |
| Design, or where something belongs | [`docs/plan/architecture.md`](docs/plan/architecture.md): target architecture, region portability, the data perimeter, the two egress designs |
| A naming, layout, Terraform or IAM rule | [`docs/plan/conventions.md`](docs/plan/conventions.md): also the `[P]`/`[D]`/`[E]` layers, the identity seam and the `app-etl` template |
| The data-governance model: the LF-Tag ontology (`layer`, `businessunit`, `classification`), the per-account encryption rule (§Encryption), the grant rules and default expressions, the drop-box and derived-zone contracts | [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md); applied grants are `docs/AWS_STATE.md`'s grant register |
| Anything on the SMUS surface: a blueprint, the network mode, a Stage 6 cost, a domain/project/profile concept, the custom-image tag convention `<flavour>-v<semver>` | [`docs/SMUS.md`](docs/SMUS.md). Review it whenever SageMaker changes |
| How the deployed tree is organised, and what is in it today | [`terraform-live/README.md`](terraform-live/README.md); the slice layout itself is `docs/plan/conventions.md` §6, the authority when the two disagree |
| What a policy statement denies, and why it exists | [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md), one row per `Sid`. Policy ids and attachment dates are in the stage log |
| What governs the lake: a bucket-policy branch, a key-policy statement, a tag assignment, an LF grant | Producer side [`terraform-live/data-governance/data/README.md`](terraform-live/data-governance/data/README.md); consumer side [`terraform-modules/consumer-data/README.md`](terraform-modules/consumer-data/README.md). They say what the code declares; applied triples are `docs/AWS_STATE.md`'s grant register. Read the producer README's "A permission here is the intersection of two systems" before claiming what a principal can do (Lesson 28) |
| What was done by hand in a stage | [`docs/log/INDEX.md`](docs/log/INDEX.md) first, then the one `log-stage-NN-*.md` |
| What is deployed right now: accounts, OUs, SSO groups, users, permission sets, assignments | [`aws/INDEX.md`](aws/INDEX.md): read-only scripts and their snapshots in `aws/output/` (untracked). Regenerate rather than trust a stale file; never copy an account id or email out of one |
| Whether something a snapshot shows is expected, before reporting it as a finding | [`docs/AWS_STATE.md`](docs/AWS_STATE.md): invariants (`INV-nn`), known exceptions (`EXC-nn`), what a later stage changes. Read it whenever a snapshot is read |
| Plan, review, or settle a decision | add [`docs/plan/lessons.md`](docs/plan/lessons.md) and [`docs/plan/open-questions.md`](docs/plan/open-questions.md) |
| Look up a decision | [`docs/plan/decisions/INDEX.md`](docs/plan/decisions/INDEX.md); open a decision file only for its reasoning |
| Cost of a new service | [`docs/PRICING.md`](docs/PRICING.md), measured, never estimated (Lesson 6). The projection is [`docs/plan/cost-model.md`](docs/plan/cost-model.md) |
| Cross-account wiring | [`docs/plan/integrations.md`](docs/plan/integrations.md), the `INT-nn` rows |
| An unfamiliar acronym, or the notation | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| Running an `aws` command by hand, or signing in | [`aws/AWS-CLI.md`](aws/AWS-CLI.md): the recipes, and which identity runs them |
| A Terraform change by hand: the two-commit tag order, blocked commits, the staged apply (Recipe D, the only sanctioned `-target`) | [`docs/plan/runbooks/terraform-changes.md`](docs/plan/runbooks/terraform-changes.md) |
| "What would an institution do?" | [`docs/plan/institutional-delta.md`](docs/plan/institutional-delta.md) |
| Root is needed, or its alarm chain is being changed | [`docs/plan/runbooks/break-glass.md`](docs/plan/runbooks/break-glass.md) |
| Anything VPN: the pieces, starting and stopping the hub, a tunnel that will not come up, a key event, a shell on the VPN host | [`docs/plan/runbooks/vpn.md`](docs/plan/runbooks/vpn.md): §S the system, §C the client, §K the keys, §K0a the SSM session. The hub is started and stopped with `make hub-up` / `make hub-down`, never `make up ENV=…` |
| Connecting a laptop: the session's up/down order, the `.conf` and its checks, the proxy on macOS and Linux, the two client profiles | [`docs/plan/runbooks/client-vpn-proxy-configuration.md`](docs/plan/runbooks/client-vpn-proxy-configuration.md) |
| The proxy inside a SageMaker space: the `NO_PROXY` value, `apt`, R and CRAN, the Code Editor's extension gallery | [`docs/plan/runbooks/sg-proxy.md`](docs/plan/runbooks/sg-proxy.md). `NO_PROXY` is generated (`terraform output -raw no_proxy` on `sandbox/egress`); the house image carries a dated copy of it (6d decision 8) and every other consumer reads the output |
| Anything egress, proxy or the hub topology: where the internet is reached, which VPC a thing belongs in, why there is no NAT gateway | [`docs/plan/decisions/D38-single-egress-hub.md`](docs/plan/decisions/D38-single-egress-hub.md) and [`docs/plan/stages/stage-06c-networking-hub.md`](docs/plan/stages/stage-06c-networking-hub.md) |
| The network as built: VPCs, subnets, routes, peerings, egress, VPN, DNS, security groups, addresses; how a SageMaker app sees the internet and what can reach one | [`docs/NETWORK.md`](docs/NETWORK.md), code plus measurement |
| Anything buildbox: the `[E]` `amd64` build host, `production/buildbox/` | [`docs/plan/runbooks/buildbox.md`](docs/plan/runbooks/buildbox.md) |
| Making a custom image selectable in SageMaker: the slice that registers it, the attach to the blueprint's domain, a version bump, why the proxy variables are not on the app image configuration | [`docs/plan/runbooks/dev-env.md`](docs/plan/runbooks/dev-env.md) |
| Anything remote IDE: attaching a laptop's VS Code to a space, the Windows client and its pin, where an extension installs and which gallery serves it, which calls the plane refuses, how a file or a repository gets in | [`docs/plan/runbooks/remote-ide.md`](docs/plan/runbooks/remote-ide.md): §O the pieces, §I the identity, §W the pinned client, §E extensions, §N the egress readings, §C moving files, §V the instruments |
| Anything Claude Code on Bedrock: the retention mode, the use-case form, the grant and endpoints it needs, what a user cannot change | [`docs/plan/runbooks/claude-code-sagemaker.md`](docs/plan/runbooks/claude-code-sagemaker.md): §M enabling the model, §I the infrastructure half, §U the scientist's, §V the instruments |
| Anything Sandbox lake: `awsds-sandbox-lake`, a per-group prefix, wiring or unwiring a project's S3 connection, the tests, code that lists, reads or writes it | [`docs/plan/runbooks/sandbox-lake.md`](docs/plan/runbooks/sandbox-lake.md) |
| A log has to be read: a refusal to attribute, a call whose door is in question, a name that never resolved, who deleted something | [`docs/plan/runbooks/log-debugging.md`](docs/plan/runbooks/log-debugging.md) |
| A policy is about to be attached, or was amended | [`docs/plan/runbooks/scp-battery.md`](docs/plan/runbooks/scp-battery.md). Running it is `./aws/probes/scp-battery.py` ([`aws/probes/README.md`](aws/probes/README.md)); amending the ceiling means editing `probes.py` |
| Explaining the design to someone | [`README.md`](README.md): the argument for the account split and the three distinctions |
| How the plan got here | [`docs/plan/history.md`](docs/plan/history.md), almost never |

Reference things by stable ID (`D26`, `INT-11`, `Stage 1c step 7`), never by section or row number.
The `§` numbers inside `docs/plan/` files are historical anchors, not addresses.

### Current position

- **Stages 0-1d, 2, 3, 4, 5, 16, 6a, 6b, 6c are done.** Battery 100. Stage 5 register 13 rows / 24
  triples. Gates: `make check`, `make check-ou`. The chain is Sandbox → Staging → Production: no
  Development account, ever; interactive compute is Sandbox only. All 38 decisions are closed; D38 §6
  was amended 2026-09-08. Still needed from the user: the domain name (blocks Stage 13).
- **Stage 6d is in progress.** Steps 9, 3, 8 and 2 are closed; step 4 exercised 2026-09-09/10 and closed
  as a decision (the portal's notebook operator dies on the D13 boundary; Stage 10's own DAGs can pass a
  full `VpcConfig`). `sandbox/dev-env/` (rank 49, `[P]`) registers `awsds-sandbox-dev-env`; version **3**
  is `default-v0.3.0`, frozen to its digest, attached by hand to the domain's `DefaultUserSettings` —
  what a space's picker reads, both app types.
  INT-01/INT-17 closed (image role by tag, project role by digest). **The app image config caps each env
  value at 256 chars** vs a `NO_PROXY` of ~1,500, so decision 8 put the six variables in the Dockerfile
  as `ENV`, a dated literal (52 entries, sha256 `fc11caaa3…`); `./aws/devenv.py` reads the drift, bump
  order `dev-env.md` §B. The image's Python is a second uv env under `/opt/awsds` on
  CPython **3.13** (no TF wheel past `cp313`), own kernel; R on conda, `rust-src` since v0.3.0. Owed: 2.4; 1.1's persona half,
  1.2/1.3; 3.4, 3.5, 3.7; step 5 beyond the idle shutdown seen unasked; step 6; 7.6, 7.7, 7.9.
- **The remote IDE works, and it is outside every control written for it** (6d step 7, 2026-09-11, a
  Windows laptop off the VPN). `StartSession` is called **by the client as the project role**, and the
  deep link is that principal from the browser, so `DenyControlPlaneOffVpn` and 6a's tag pair never
  evaluate: decision 4's repair lands on the project role — `aws:SourceIdentity` or the space's
  `OwnerUserProfileName` for *whose space*, `aws:SourceIp` for *VPN-only*. Decision 5: the space's own
  fetch of the server and of each `.vsix` is refused (`403`) and Remote - SSH copies both from the
  laptop — **no Microsoft name joins the plane**, and the session is a **file channel in both
  directions that no hostname list describes**. **Two IDE servers run in one
  container**, separate extension directories and settings, so a version complaint is the client's
  marketplace and never the remote runtime. A remote space needs **≥ 8 GB** (`ml.t3.large` 0.100/h);
  the space path carries no instance ceiling since `sagemaker-denies-v0.2.0`, and
  `session-manager-plugin` honours `HTTPS_PROXY` only if the environment reaches its process.
  Runbook: `remote-ide.md`.
- **Stage 6e: a session answered from a space 2026-09-12** — Haiku 4.5, project role, via the
  `bedrock-runtime` endpoint. Four premises fell. **The
  agreement enables a model, not the form** (`create-foundation-model-agreement`, per model; `NOT_AVAILABLE` = none created). **A cross-region profile is authorized per
  destination region**, so CT's `CT.MULTISERVICE.PV.1` on `Interactive` refuses it until
  `bedrock:` actions join its `NotAction` — five did; compensating deny owed (dec 15). **Retention
  mode is per account AND region**: `none` in `us-west-2`, `inherit` in the other two (dec 16).
  **`claude-opus-5`/`claude-sonnet-5` are refused for this account**, every principal, every
  instrument green (`EXC-08`); **the set is the 4.5 generation since dec 14**, delivery owed (image).
  Grant per project, `sandbox/bedrock/` (rank 52, `[P]`): its `models` map is all a space can invoke. The `us.` profiles route to three US regions (D1's exception).
  Runbook: `claude-code-sagemaker.md`.
- **The hub (D38, 6c).** Five VPCs, five peerings, zero NAT, no spoke default route, one explicit Squid
  proxy, no interface endpoint in the hub. Endpoint sets: Sandbox 20, Staging 11, SharedServices 13,
  Workloads 0; estate fixed rate 0.410/h; DNS Firewall 14 domains. `make hub-up` / `hub-down` start and
  stop the two hub hosts, and a spoke `make up` refuses while one is stopped. `./aws/proxy.py`
  PX-1..PX-5; NT-11/NT-12 are two-sided, by CIDR. `production/egress/` is a prerequisite of a build
  (the buildbox's SSM door). `10.40.0.0/16` stays unallocated.
- **Proxy planes.** A plane is a CIDR, not a host (Lesson 29); its mode is decided by which map holds it
  (`proxy_allow_by_plane` / `proxy_deny_by_plane`, preconditions on both). The client plane and the build
  plane (`production-foundation` = all of `VPC-SharedServices`) are `open`: any public name, logged. The
  compute plane `sandbox-foundation` is an allow-list of 25 names (`docs/NETWORK.md` counts it, dated);
  `github.com` was removed 2026-09-09 by the user, CRAN added 2026-09-11, conda refused. **An empty
  allow-list refuses everything and an empty deny-list permits everything**; an `open` plane emits no
  `dstdeny_` ACL and an empty allow-list plane emits nothing. `DN-4` reads "no plane is `open` except the
  ones a decision names" (`OPEN_BY_DECISION`). **A plane edit bites at the next half-hourly association
  tick**, so `DN-3` (code vs parameter) and `PX-3` (parameter vs the running file) are two questions
  (`terraform-changes.md` Recipe A step 8). The three global denies, the absent default route and the
  3128-only SG are unchanged.
- **Squid matches the name the client requested, never a DNS answer** (2026-09-08): a CNAME is invisible,
  an HTTP redirect is a new name, and a bare entry matches exactly (`github.com` covers neither
  `api.github.com` nor `raw.githubusercontent.com`). A refusal over https reads `000` at the client. A missing name can also fail **without** a `403`: the
  second instrument is `/awsds/sandbox/dns-firewall`, and the hub carries no DNS Firewall, so an
  `ENOTFOUND` comes from a compute VPC.
- **`NO_PROXY` is generated** (`vpc-egress` output), never written: it reads each endpoint's `dns_entry`
  rather than the service's one canonical name (`v0.14.1`, 52 entries on `sandbox/egress`), and a gateway
  endpoint has no private DNS at all, so S3/DynamoDB are hand-named in both spellings. The other three
  `egress/` slices are down and take v0.11.1 on their next `make up`. **The first question about a `403`
  is whether the name has an endpoint**; `streaming-logs` is still unexercised.
- **Inside a space**: on `default-v0.2.0` nothing is exported — `apt`, `uv`, Julia, Rust and the four
  kernels work as they are (earlier images: `sg-proxy.md`). A space started while
  `sandbox/egress` is down hangs at "IDE configuration in progress". CRAN is on the plane since
  2026-09-11 and needs a writable per-space library; `conda` is not, by decision. A rebuild is not
  byte-reproducible.
- **Orchestration is MWAA Serverless only** (USD 0.088/task-hour), exercised 6d step 4 (2026-09-09/10):
  one workflow, `READY`, `manual_only`; every run is two attempts, so read the task's
  `DurationInSeconds`, never the run's. The surface needs nothing — 6a's eleven configurations
  unchanged, and the `Workflows` blueprint is the provisioned shape, not this one. It runs as the
  project role inside the D13 boundary; workers in two AZs, private subnets, no proxy (a priced D9
  exception), CMK `alias/awsds-sandbox-project`. A "Notebook task" is a `CreateTrainingJob` and dies on
  `DenySageMakerJobsOffVpc` in the **boundary's** copy (Lesson 20); filling the portal's empty `compute`
  changes nothing. `update-workflow` is a full replace (Lesson 60) and severs the domain/project the
  portal injects. The SMUS CI/CD tool deploys only into existing projects; the pipeline stays the
  deployer (D26/D28).
- **VPN.** Two client profiles (vpn.md §C7): monitored (full tunnel) and split-tunnel (`AllowedIPs` =
  the five VPC CIDRs + `10.90.0.0/24`), same key, same `DNS`, laptop-only. The reach difference is by
  identity, never by network. The tunnel is dual-family (`wireguard-v0.6.0`) and rejects IPv6
  (Lesson 56). macOS's system proxy is not consulted while the tunnel is primary (issue #67), and with
  the tunnel down it breaks the `aws` CLI — `NO_PROXY='*'` is the override. 6c decision due 4 taken as
  (c); 6.6 as (ii), re-taken at Stage 11 3.4. `aws sso logout` invalidates every cached session's token, a browser sign-out invalidates
  none, and a cached token is keyed by `sso-session` name, never by user.
- **Module tags**: `vpc-egress-v0.14.1`, `wireguard-v0.6.0`, `vpc-v0.3.1`, `sagemaker-denies-v0.2.0`
  (abandoned on origin, Lesson 46: `vpc-egress` v0.9.0, v0.11.0, v0.12.0-v0.14.0, `vpc-v0.3.0`).
  `-input=false` on every plan and apply (Lesson 47); never pipe a command whose exit code matters;
  a module change is exercised by planning a caller, never by `validate` (it passed on all three).
- **SMUS mechanics**: a blueprint configuration is applied from the member account; an existing one is
  immutable via `awscc`; the D13 boundary field is write-only (always `get-role`); an incomplete
  configuration pins its projects both ways. SMUS is a Lake Formation admin in Sandbox (OQ 24);
  `-refresh=false` is forbidden on that slice. A denied call does not always name the policy.
- **Standing rules**: never add an `sts:` action to the RCP without reading `CT.STS.PV.1`'s exclusion
  note; resolve an account by exact vended name; subnets anchor on AZ `zone_id`; read the denial wording,
  never the exit code; account-level BPA **and the Bedrock retention mode** are hand-managed; Log
  Archive and Audit hold no CLI profile; auto-enrollment is on; `INV-09` is ten principals. Before
  reporting a gap, read the file that owns it:
  unexercised denies → `POLICIES.md`; expected readings → `AWS_STATE.md`; SMUS findings → OQ 12-15, 20,
  21. From Stage 5: no principal can start the crawlers (OQ 19); `EXC-02`; no Athena in Data
  Governance. Deferred by decision, do not offer to close: OQ 10 waits for N=2; the Config recorder is
  left alone. **D12's budget notifies nobody — 6e 8.3 re-opens it**, Bedrock being the first thing here
  that bills per use with no ceiling.

Budget: about 8 KB, state only. A bullet here that explains why, or that a stage file should carry, is a
stale copy of something that lives elsewhere. Re-trim whenever a stage closes.

### Lessons carried forward

Read [`docs/plan/lessons.md`](docs/plan/lessons.md) before planning, reviewing, or settling a decision.
These are recognition keys, not the lessons: each is a title trimmed to what makes it identifiable, and
the reasoning that makes it usable is in the file. Recognising one is the signal to open it.

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
59. **Changing WHERE a value is read from can change WHEN it is knowable — and every guard that
    reads it moves with it, silently.**
60. **A full-replace update API turns every field you did not pass into a deletion — and the
    object's creator may have injected state no field of that API can restore.**
61. **A procedure that depends on a file it did not create runs only for its author — and against a
    full-replace API the stale file is not unavailable, it is wrong.**
62. **An absence is evidence only when the instrument would have shown the presence — the wrong path
    and the lagging log both answer "nothing", and the pleasant answer is the one nobody challenges.**

**[`lessons.md`](docs/plan/lessons.md) also carries a second list — "What AWS does that its
documentation does not say"** — platform behaviours that cost a measurement to learn, each with its
date and its reading. Consult it before designing around an AWS behaviour nobody here has measured;
add to it when a vendor page turns out not to say the thing that mattered.
