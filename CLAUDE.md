
# General Objective

The objective of this project is to create a Data Science environment based on AWS cloud infrastructure, using my personal AWS account.

The goal is to achieve the following:

- All user access to the cloud infrastructure will be performed through a VPN.

- Use SageMaker Unified Studio as a development tool for Data Scientists.

- The main features Data Scientists can use inside SageMaker Unified Studio to develop data-science products are:

  - the use of Jupyter notebooks built in SageMaker Unified Studio: users can instantiate as many Jupyter notebook instances as they like, each one on a selected compute and dev-env image.
  - the user of vscode instances built in SageMaker Unified Studio: users can instantiate as many vscode web instances they wish, with possibility of remote connecting their local computer vscode to a remote session.
  - the use of data catalog and explorer, issuing SQL statements, built in SageMaker Unified Studio.
  - use of S3 buckets for storage, built in SageMaker Unified Studio user interface.
  - use of sagemaker's workflows and Visual ETL feature built in SageMaker Unified Studio.
  - use of IA models built in SageMaker Unified Studio

- The data scientist can promote Artifacts built in SageMaker (dev-env, ML models, workflows) to production (Sandbox -> Development -> Staging -> Production), making use of CI/CD pipelines (see below).

- Protect data against leakage (DLP), mainly targeting SageMaker. There is no single AWS product that does
  this, so the requirement is broken into the four problems it has to solve:

	- sensitive-data discovery and classification: know which sensitive data exists and where it is stored.
	- fine-grained access control: restrict who can read which database, table, column and row.
	- egress control: restrict where data can be sent to from the development environment.
	- exfiltration detection: detect and alert on abnormal data access or data movement.

- SageMaker should have access to the internet. We'll explore implementing some restrictions, keeping the possibility of software updates, installing packages, and accessing a few websites.

- Use GitLab hosted on AWS for source-code control, accessible only through intranet (VPN), not facing public internet.

- Use GitLab Pages to host docs, accessible only through intranet (VPN), not facing public internet.

- Use GitLab CI/CD to automate tests, docs and deployment.

- Use three kinds of CI/CD pipelines:

	- pipeline to build a development environment: this will be the Docker container (or image) used by developers on SageMaker.
	- pipeline to build an application: this should build a Docker image of the app.
	- pipeline to deploy an application into the production environment.

- Explore the possibility of deploying a workflow developed in SageMaker (Airflow/MWAA) to production.

- Use an NFS solution to exchange files between users, the SageMaker environment and S3 buckets.

- Data-science assets and databases should not face the public internet. Later in the project we'll experiment with setting up a web server facing the public internet, accessing a backend or database protected in the private subnet.

- Let's avoid using IAM Users, in favor of assuming IAM Roles temporarily.

- Use AWS CloudWatch to monitor the cloud infrastructure.

- Use AWS Organizations + Control Tower to set up account permissions.

- Use AWS Lake Formation to share data cross-account.

- Use AWS Glue Data Catalog with data stored on S3 buckets, using ICEBERG format, as Data Warehouse.

- Use Amazon ECR as container registry.

## How this will be done

We will start from scratch: the starting point is a root AWS account created manually.

The project will be implemented incrementally.

I'll ask Claude to plan the next step and Claude will guide me on each step until we reach the project goals.

The application repository template (`app-etl`) is a layout convention, and lives with the others:
[`plan/conventions.md`](plan/conventions.md), "Application repository layout".

# Guidelines

## AWS Region

All infrastructure will be deployed in the `us-west-2` Region.

## Tools installed in the current environment

`terraform`, the `aws` client and `uv` — install links in [`REFERENCES.md`](REFERENCES.md), "Tools".

## `secrets` folder

This folder is ignored by git. It contains personal information. Never edit this folder, and never
write anything into it. Claude can read the files in this folder to gather information.

**Never read the file `serets/prompts.md`!**

**Never copy or reproduce any email addresses, telephone numbers, account IDs contained in this folder into any other project files.**.

## Organization

- All accounts will be registered under an AWS Organization managed by the `Management Account` using Control Tower.

- Accounts will be used to isolate environments.

- Promotion happens from: Development -> Staging -> Production. Given that Sandbox is the experimentation environment.

## terraform

- All infrastructure code will be in Terraform.

- Two trees: `terraform-live/` (one subfolder per controlled account, sliced by lifecycle layer) and
  `terraform-modules/` (reusable modules, consumed by git tag). **The authoritative layout, with the
  `[P]`/`[D]`/`[E]` layer of every slice, is in [`plan/conventions.md`](plan/conventions.md) §6** —
  kept in one place on purpose, so the two copies cannot drift.

- never run `terraform apply` (or scripts that perform infrastructure changes), unless explicitly authorized. You are free to run *read-only* operations.

## aws cli

- you are free to run read-only operations using aws client.

- Never run write operations using aws, unless explicitly authorized.

- all scripts inside `aws/*` should perform only read-only operations. You are free to run them to gather information.

- **The one exception, and it is fenced: [`aws/probes/`](aws/probes/README.md)** — the SCP battery, which
  has to *attempt* the calls a policy forbids, because that is the only way to measure a preventive control.
  It creates nothing (every probe is read-only, `--dry-run`, or aimed at a prerequisite that does not exist),
  it never attaches or changes a policy, and the three probes that *would* act if a deny were missing are
  refused by the driver anywhere but `Policy Canary`. **Run it deliberately, not to gather information** —
  which is the difference from every other script in that folder.

- before running `aws` commands, check if the current session uses the correct `sso` user using `aws sts get-caller-identity`.

- **Whenever an SSO login is needed — asked for, or implied by a command Claude is about to hand over —
  Claude states three things, every time and without being asked**: the **SSO user** to sign in as, the
  **account** the work lands in, and the **permission set** behind it. Never "log in and run this".

  | Say | Example |
  |---|---|
  | SSO user | the infrastructure user (`felipenoris+infrastructure_user@…`) — the only one with CLI profiles; `AWS Control Tower Admin` is a *different* user, console-only |
  | Account | `Policy Canary`, `Development`, `Management`, … — by **name**, never by id |
  | Permission set | `InfrastructureAccess`, `AWSAdministratorAccess` — and the profile that reaches it |

  **"Role" and "permission set" are the same thing seen from two sides**, and the distinction only matters
  when writing a policy: a permission set is the Identity Center object; what it provisions into each
  account is an IAM role named `AWSReservedSSO_<PermissionSetName>_<per-account random suffix>`. A
  condition keyed on `aws:PrincipalArn` must name **that role ARN**, which is why the suffix being
  per-account is what forced decision 7's wildcard.

  **One `aws sso login --sso-session awsds` covers every profile** — the token is keyed by the
  `sso-session` name, not by profile or account — so the answer is never "which profile do I log in
  with", it is *which identity to pick in the browser*, plus where the work is about to land.

## Upkeep — the files this project maintains

| File | What it holds, and the rule |
|---|---|
| [`log/`](log/INDEX.md)`stage-NN-*.md` | Every step performed by hand in AWS, one file per stage, mirroring `plan/stages/`. **Written by the user — Claude never edits a stage log.** Claude may draft wording for the user to paste, and says so. **Every draft is delivered in English, in Markdown, inside a single fenced code block in the chat** — never as ordinary chat prose — so the user copies it into the file untouched and nothing is reformatted on the way. Use a ` ```markdown ` fence; replace real account IDs by `<Account Name>`; use use `<Management Account>` when replacing the ID from the Management Account on logs; if the draft itself has to contain a fenced block, use a longer outer fence (` ````markdown `) so the nesting survives. **Drafts are concise by default**: the command, the outcome, and any finding that does **not** survive elsewhere. Leave out what `aws/output/` already holds (it is regenerated on demand), what a `plan/` file explains, and the reasoning behind a choice — a log entry restating either is a copy that will go stale. Prose belongs in `plan/`; the log carries *what happened, in order* |
| [`log/INDEX.md`](log/INDEX.md) | The one exception under `log/`: **Claude maintains it.** After reading a stage log, bring its `Records` cell to what the file now contains — a cell saying less than the file is what the index exists to prevent. Never restate a step there: the cell says *what is inside*, in one line |
| [`ORGANIZATION.md`](ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`REFERENCES.md`](REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout, so people can understand the components |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes — **never a copy of the slice tree**, which lives in `plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) | One row per entry in **every** document in `policies/`, all four policy types since 7.8 (**called `SCPs.md` until 2026-08-15**): what it does, why it exists, what it does once attached. **Reviewed in the same sitting as any policy change** — an entry added, removed, renamed or re-conditioned, and any attach or detach. `./terraform-live/identity/org-policies/check-index.sh` decides the mechanical half and is type-aware (`Sid`s for SCP/RCP, tag keys for a tag policy, `ec2_attributes` names for a declarative one); whether a row is still *true* is the reading |
| [`PRICING.md`](PRICING.md) | A row for every new AWS service referenced |

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

Stage numbers refer to `plan/stages/`. **Always read `GENERAL_PLAN.md` before planning or executing a
step** — it is the plan core and carries both indexes — then read only the stage file and the decisions
its `Consumes` row lists.

### What to read, and when

**This table is the only routing map — every other file points here rather than repeating it.**

| Task | Read |
|---|---|
| Anything | this file + [`GENERAL_PLAN.md`](GENERAL_PLAN.md) (plan core: principles, the account map, the route) |
| Execute a stage | [`plan/stages/`](plan/stages/INDEX.md)`stage-NN-*.md`, the decisions in its **Consumes** row, and [`plan/conventions.md`](plan/conventions.md) |
| Design, or reason about where something belongs | [`plan/architecture.md`](plan/architecture.md) — target architecture, region portability, the data perimeter, the two egress designs |
| A naming, layout, Terraform or IAM rule | [`plan/conventions.md`](plan/conventions.md) — also the `[P]`/`[D]`/`[E]` layers and the `app-etl` repository template |
| **How the deployed tree is organised, and what is in it today** | [`terraform-live/README.md`](terraform-live/README.md) — one folder per account, sliced by lifecycle layer, what deliberately lives outside it. **The slice-by-slice layout itself stays in `plan/conventions.md` §6**, which is the authority when the two disagree |
| **What a given SCP statement denies, and why that statement exists** | [`terraform-live/identity/org-policies/POLICIES.md`](terraform-live/identity/org-policies/POLICIES.md) — one row per `Sid`, per document, plus the AWS reference for every action named. Policy ids and attachment dates are **not** there: those are in the stage log |
| What was actually done by hand in a stage | [`log/`](log/INDEX.md)`stage-NN-*.md` — **the same slug as the stage file**; [`log/INDEX.md`](log/INDEX.md) first, so only one log is opened |
| **What is deployed right now** — accounts, OUs, SSO groups, users, permission sets, assignments | [`aws/INDEX.md`](aws/INDEX.md) — read-only scripts and the snapshots they write to `aws/output/` (untracked). Its question table says which section answers what; **regenerate rather than trust a stale file, and never copy an account id or email out of one** |
| **Whether something a snapshot shows is expected** — before reporting it as a finding | [`AWS_STATE.md`](AWS_STATE.md) — the invariants (`INV-nn`), the known exceptions (`EXC-nn`, e.g. the suspended `Sandbox` account that is **not** ours), and what a later stage is going to change anyway. **Read it whenever a snapshot is read** |
| Plan, review, or settle a decision | add [`plan/lessons.md`](plan/lessons.md) and [`plan/open-questions.md`](plan/open-questions.md) |
| Look up a decision | [`plan/decisions/INDEX.md`](plan/decisions/INDEX.md) first — open a decision file only for its reasoning |
| Cost of a new service | [`PRICING.md`](PRICING.md) — measured from the Price List API, never estimated (Lesson 6) |
| The projection, and whether the ceiling still holds | [`plan/cost-model.md`](plan/cost-model.md) |
| Cross-account wiring | [`plan/integrations.md`](plan/integrations.md), the `INT-nn` rows |
| An unfamiliar acronym, or the notation | [`GLOSSARY.md`](GLOSSARY.md) |
| Running an `aws` command by hand | [`AWS-CLI.md`](AWS-CLI.md) — the recipes, and which identity runs them |
| "What would an institution do?" | [`plan/institutional-delta.md`](plan/institutional-delta.md) — so a lab compromise is not learned as a pattern |
| Root is needed, or its alarm chain is being changed | [`plan/runbooks/break-glass.md`](plan/runbooks/break-glass.md) |
| **A policy is about to be attached, or was amended** | [`plan/runbooks/scp-battery.md`](plan/runbooks/scp-battery.md) — the probes, and the two distinguishable outcomes of each. **Running them is `./aws/probes/scp-battery.sh`** ([`aws/probes/README.md`](aws/probes/README.md)); the probe list is `aws/probes/probes.sh`, and amending the ceiling means editing that file. The script measures and never attaches — **it is the one place under `aws/` that is not read-only** |
| Explaining the design to someone | [`README.md`](README.md) — the argument for the account split and the three distinctions |
| How the plan got here | [`plan/history.md`](plan/history.md) — almost never |

Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1c step 7` — never by section or row number.
The `§` numbers inside `plan/` files are historical anchors, not addresses.

### Current position

- **The landing zone is closed — Stages 0-1d DONE (2026-08-15)** — except the `Staging` vend, held on the
  account cap (`./aws/quotas.sh` re-asks, meaningful only from Management; the deferral's debts are one
  list in Stage 1a). Ten policy documents, four types, attached — **six on the organization root, four
  per-OU** — battery 93/93. The `log/` files are authoritative.
- **Next is Stage 2 — roteiro revised and review-corrected 2026-08-15.** The delegation goes first
  (5.0/5.1): INT-20's plausible failure — "works and still cannot touch a root attachment" — sizes the
  stage. **5.1's delegation `Resource` list must carry the four policy-type ARNs**
  (`policy/o-<org>/<type>/*`): a target-only list denies every write and reads exactly like "all
  refused" — `org-delegation.sh` `DEL-9` checks it. Per-OU attachments are **authored, not discovered**
  (a discovered `for_each` would reverse D37 on `Sandboxes`); discovery feeds check 9.3. Modules move
  last. Boundaries carry the two ARN-keyed carve-outs (BPA decision 7, D27), written once and referenced
  — **a carve-out keyed on a principal ARN cannot defend itself**; unverified and cheap: whether IAM
  permits `CreateRole` under `/aws-reserved/`. `InfrastructureAccess` runs from `awsds-infra-identity`;
  `AWSAdministratorAccess` only as CT Admin on Management (a set provisioned into Management cannot be
  altered from Identity). The OU walk recurses (depth 2). The five instruments exist (`aws/INDEX.md`);
  `org-policies.sh` lists ids for all four policy types since 2026-08-15. The stage log exists,
  header-only.
- **Standing rules that outlive their stages:** never add an `sts:` action to the RCP without reading
  `CT.STS.PV.1`'s exclusion note (its first shape locked every SSO user out of every member account);
  1d step 9 is the **only** sanctioned by-hand use of `AWSControlTowerExecution`; never resolve an
  account by name (`ORGANIZATION.md`); subnets anchor on AZ `zone_id` — run `./aws/AZs.sh` after every
  vend; check the SSO token before each probe block and read the denial *wording*, never the exit code;
  account-level BPA is hand-managed — its SCP deny carves out the very principal Terraform applies as, so
  the guard is Stage 2's repository grep.
- **Log Archive and Audit hold no CLI profile** — nothing there is regression-testable; `CHK-1`/`CHK-2`
  and `org-policies.sh` §4 are the standing instruments. **Every governed account sits under
  `us-west-2`**; Stages 4, 5 and 11 are committed there (`guardduty`, `securityhub`, `macie2` not exempt).
- **1b residue:** only `Policy Canary` keeps an Account Factory direct assignment (permanent, not
  modelled); verification (vi) and `sso-directory.amazonaws.com` re-check at the next landing-zone update.
- **Unexercised denies** (verify by reading, not probing — `POLICIES.md` and the 1c log):
  `ec2:ModifySnapshotAttribute`; `datazone:CreateDomain` (= Stage 6 step 0); `s3:DeleteBucket`; the
  positive D27 half (Stage 5's `awsds-data-catalog-maintenance` role). Athena is allowed in `Data` on
  purpose (Stage 11 detects); `guardduty:UpdateDetector` blocks Stage 11 step 4 in Audit by design.
- **SMUS findings for Stages 5/6/10:** open questions 12-15, summarized atop Stage 6. The load-bearing
  one: the default notebook Spark runtime has no VPC until Stage 6 disables it.
- **Deferred by decision — do not offer to close:** the USD 50 budget notifies nobody (D12); open
  question 10's per-unit tokens wait for N=2. **Stage 12 hooks:** Config recorder left alone (1d decision
  4), Management deliberately unrecorded (decision 8), INV-14 floors the log-bucket lifecycle at 90 days;
  billing reads need root's billing toggle (active).
- **All thirty-seven decisions are closed** (D30 as a revert). Still needed from the user: the domain
  name alone, blocking Stage 13 (D15 phase 2). No public DNS before Stage 13; internal names are
  `*.internal` off the internal CA (D36, INT-19).
- **Settle earliest:** INT-11 — organization halves done; what remains is Stage 5 defending
  `CROSS_ACCOUNT_VERSION` **4** + `SET_CONTEXT: TRUE` (values nobody set) at its first apply, carrying
  **both** keys — and INT-13 (no convenience-preserving fallback). The repository is documentation-only
  except `terraform-live/identity/org-policies/`; the first `.tf` arrives with Stage 2.

**Budget: ~2 KB.** State, not reasoning — **a bullet here that explains *why*, or that a stage file should
be carrying, is a stale copy of something that already lives elsewhere.** Re-trim whenever a stage closes.

### Lessons carried forward

**Read [`plan/lessons.md`](plan/lessons.md) before planning, reviewing, or settling a decision.**
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

