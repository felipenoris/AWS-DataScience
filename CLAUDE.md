
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
| [`log/`](log/INDEX.md)`stage-NN-*.md` | Every step performed by hand in AWS, one file per stage, mirroring `plan/stages/`. **Written by the user — Claude never edits a stage log.** Claude may draft wording for the user to paste, and says so. **Drafts are concise by default**: the command, the outcome, and any finding that does **not** survive elsewhere. Leave out what `aws/output/` already holds (it is regenerated on demand), what a `plan/` file explains, and the reasoning behind a choice — a log entry restating either is a copy that will go stale. Prose belongs in `plan/`; the log carries *what happened, in order* |
| [`log/INDEX.md`](log/INDEX.md) | The one exception under `log/`: **Claude maintains it.** After reading a stage log, bring its `Records` cell to what the file now contains — a cell saying less than the file is what the index exists to prevent. Never restate a step there: the cell says *what is inside*, in one line |
| [`ORGANIZATION.md`](ORGANIZATION.md) | The AWS OUs, accounts and users |
| [`REFERENCES.md`](REFERENCES.md) | Every internet link used as a reference, added on the interaction that used it |
| [`README.md`](README.md) | How the AWS resources are structured, and the project layout, so people can understand the components |
| [`terraform-live/README.md`](terraform-live/README.md) | How the deployed tree is organised. Updated when an account folder or a top-level rule changes — **never a copy of the slice tree**, which lives in `plan/conventions.md` §6 |
| [`terraform-live/identity/org-policies/SCPs.md`](terraform-live/identity/org-policies/SCPs.md) | One row per entry in **every** document in `policies/`, all four policy types since 7.8 (the filename is historical): what it does, why it exists, what it does once attached. **Reviewed in the same sitting as any policy change** — an entry added, removed, renamed or re-conditioned, and any attach or detach. `./terraform-live/identity/org-policies/check-index.sh` decides the mechanical half and is type-aware (`Sid`s for SCP/RCP, tag keys for a tag policy, `ec2_attributes` names for a declarative one); whether a row is still *true* is the reading |
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
| **What a given SCP statement denies, and why that statement exists** | [`terraform-live/identity/org-policies/SCPs.md`](terraform-live/identity/org-policies/SCPs.md) — one row per `Sid`, per document, plus the AWS reference for every action named. Policy ids and attachment dates are **not** there: those are in the stage log |
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

- **7.8 IS ATTACHED AND MEASURED, so Stage 1c is done: full battery 93 as expected, 0 unexpected, 0
  untested** (2026-08-14), all ten documents matching `policies/` on read-back. Four policy types now live
  on the root — `baseline`, `perimeter`, `tag-enforcement` (SCP), `awsds-org-rcp-perimeter` (RCP),
  `awsds-org-tag-policy`, `awsds-org-declarative-ec2`. **The RCP cost one outage first**: its STS statement
  named `AssumeRoleWithSAML`/`TagSession`, which is all an `AWSReservedSSO_*` trust policy permits, and it
  locked every SSO user out of all six member accounts while Management stayed reachable. Rescoped to
  `sts:AssumeRole` + `sts:SetContext`, matching AWS's own `CT.STS.PV.1` — **never add an `sts:` action to
  it without reading that control's exclusion note.** Lesson 24 is the general form; the battery now
  records a lockout instead of aborting on it, and `classify` no longer reads a declarative policy's
  message *echoed by a successful read* as a deny.
- **Stage 1a is done but for the `Staging` vend; 1b and 1c are DONE. Stage 1d is the landing zone's last
  stage and is ready to start** — the `log/` files are authoritative. 1a: Control Tower enabled
  (`us-west-2`), budget set, `Development`, `Sandbox Account 1`, `Production`, `Data Governance`,
  `Policy Canary` and `Identity` vended, centralized root access on, break-glass **tested 2026-08-09 on both
  channels**.
- **1d's roteiro was revised 2026-08-14 against 1c and four fresh readings, and three of its four steps
  changed.** (a) **Step 9 is blocked as written**: Control Tower's own `CTS3PV8` on the `Security` OU is a
  `Deny`+`NotAction` over the log buckets exempting **`AWSControlTowerExecution` alone**, and
  `s3:PutBucketObjectLockConfiguration` is not in the list — so CT Admin cannot enable Object Lock, which is
  **decision 9**. The step survives because the same `NotAction` **permits `s3:DeleteObjectVersion`**: AWS
  protects the bucket's configuration and leaves its contents deletable. (b) **The bucket is
  `aws-controltower-cloudtrail-logs-*`**, not `aws-controltower-logs-*`; the old prefix matches nothing and
  returns a `None` that reads like a failed lock. CloudTrail log-file validation is **already `true`**, read
  from Identity. (c) **11.2 is already satisfied** — `CROSS_ACCOUNT_VERSION` reads **4** with
  `SET_CONTEXT: TRUE` in Data Governance with no lake, so verification (v) is answered, no
  `put-data-lake-settings` is made, and what survives is the instruction to Stage 5 to carry **both** keys.
  `ram.amazonaws.com` is confirmed **absent**, so 11.1 has real work. (d) **New step 12**: the Region ceiling
  on `Security` (open question 16, decision 10) — and the battery can never test it, since neither Log
  Archive nor Audit has a CLI profile and creating one is refused.
- **1b's residue, all of it:** the six SSO profiles resolve (five `awsds-infra-*` →
  `AWSReservedSSO_InfrastructureAccess_*`, `awsds-policy-canary` → `AWSReservedSSO_AWSAdministratorAccess_*`);
  **only `Policy Canary` still carries an Account Factory direct assignment**, permanently; the org IAM
  Access Analyzer lives in **Audit** (`ORGANIZATION` zone of trust) after the console wizard first put it in
  the wrong account. **(vi) is open by construction** — whether 5.1's removals stick is re-checked at the
  next landing-zone update, account update or re-enrollment, not now.
- **Subnets anchor on the AZ `zone_id`, never on list position** — 1b step 6, 2026-08-12. Every measured
  account returns the *same* mapping (`us-west-2a` → `usw2-az2`; the names are not in ID order), so position
  would work today; it is forbidden because an unvended account gets its own mapping and the failure is
  silent. `./aws/AZs.sh` re-measures — **run it after every vend**. Open question 3 is closed.
- **A permission set provisioned into Management cannot be altered from the Identity account** — measured
  2026-08-12, and it is a *second* delegated-administrator boundary, distinct from the Management-targeted
  one step 4 found. The deny is anchored on the **permission set** ARN, so it covers that set's assignments
  in every account. **Anything touching `AWSAdministratorAccess` runs as CT Admin on Management.**
  `InfrastructureAccess` is not provisioned into Management and is unaffected — Stage 2 step 5 still manages
  it from `awsds-infra-identity`.
- **`sso-directory.amazonaws.com` (the console path) is still unexercised** by 8.3's filter — 5.1's console
  removals emitted `sso.amazonaws.com`, not the directory pair.
- **The Sandbox per-unit token is an ordinal** — `awsds-infra-sandbox-1`, `-2`, … (user, 2026-08-11),
  matching the account name AWS shows. **It does *not* propagate to the `Environment` tag**, settled
  2026-08-13; the other four tokens of [`plan/open-questions.md`](plan/open-questions.md) item 10 are open
  and none blocks anything before Stage 2.
- **`CLAUDE.md`'s objectives gained six named Unified Studio features on 2026-08-13, and reading them
  against AWS's docs produced four findings that are Stage 5/6/10's, not the landing zone's**
  ([`plan/open-questions.md`](plan/open-questions.md) items 12-15, summarized in the table at the top of
  [Stage 6](plan/stages/stage-06-unified-studio.md)). The load-bearing one: **the default notebook Spark
  runtime is Athena for Spark, which does not support VPC** — principle 4 is about the account, not about
  what the data scientist actually runs, until Stage 6 disables it. Also: **notebooks have no trusted
  identity propagation**, so D13's fine-grained grain may be the *project* and not the user; and
  **`sagemaker:StartSession`** (local VS Code onto a space) is a real objective *and* a file channel to a
  laptop. SMUS notebooks/VS Code are **spaces and apps** — which is what made 1c's decision 1 free.
- **The `Staging` vend is held on the account cap, and the increase has *not* landed** — measured from
  Management during 7.0: `Maximum number of accounts` reads **10**, not the requested 15. (From a member
  account the same quota reads `0.0`, so only the Management run is evidence.) **What the deferral owes is
  one list, in [Stage 1a](plan/stages/stage-01a-landing-zone.md)** ("What the deferral leaves owed"), not
  five per-stage footnotes.
- **The USD 50 budget notifies nobody.** Its 50/80/100% alerts and Cost Anomaly Detection are **skipped by
  decision** (2026-08-09), not pending — do not offer to close them in passing. D12 holds the trade and its
  revision trigger.
- **The OU tree is not the one D23 first described** — revised 2026-08-09 by execution; full tree in
  [`plan/architecture.md`](plan/architecture.md). `Identity` has an OU of its own; `Sandboxes` is nested
  under `Interactive` and carries no policy set of its own. **Depth is 2 — Stage 2's OU `for_each` must
  recurse**, or every Sandbox account is invisible to it.
- **What 7.0's preflight established that still governs work.** **`Identity` is a registered OU** with the
  same 9 `AWS-GR_*` controls as every ordinary one; **`Security` adds exactly three** (`CT.S3.PV.7`,
  `CT.S3.PV.8`, `CT.SNS.PV.1`) and names them in the `controlcatalog:::control/<opaque>` namespace while
  every other OU uses `controltower:…/AWS-GR_*` — same controls, two id schemes. **Control Tower denies the
  Config recorder** (`GRCONFIGENABLED`, exempting `AWSControlTowerExecution` alone — which is why Stage 1d
  10.4 is possible only in SCP-exempt Management) **and *nothing* about CloudTrail**, the CloudTrail deny
  being **skipped by decision**. **Service Quotas publishes no policy quota for `organizations`**, so the
  size budget is the documentation's number and the count fits either way. Account-level BPA reads all four
  flags `true` in **all nine accounts** — `./aws/account-bpa.sh` re-measures the six with a profile;
  Management, Log Archive and Audit are console-verified and **this laptop cannot read them**.
- **The root set (7.5) is attached and exercised, and three of its measurements outlive the stage.**
  **Decision 7 is measured, not assumed** — `aws:PrincipalArn` names the `role/aws-reserved/...` form and
  not the `assumed-role` one, which is also what makes Stage 1d 9.6's `AWSControlTowerExecution` exemption
  work. **`aws:ResourceOrgID` populates for S3 *and* ECR**, proven by an inverted document. **Two statements
  are attached but unexercised**, both because the service validates input before authorizing:
  `ec2:ModifySnapshotAttribute` (its AMI sibling *was* denied) and `datazone:CreateDomain` — **that one is
  [Stage 6 step 0](plan/stages/stage-06-unified-studio.md)**, because `ForAllValues:` over a key that does
  not populate evaluates *true* and the untested failure is the deny reaching `Data` too.
- **The SSO token expires faster than a battery does** — it died twice mid-run, and both times every probe
  came back as a non-answer that reads like a deny. **Check the token immediately before each block of
  probes**, and read the error *wording* (`explicit deny in a service control policy`), never the exit code.
- **The per-OU set (7.6, amended by 7.6a) is attached and exercised in each OU's own account.**
  Verification (viii) answered (an SMUS domain is `datazone:*`, so `Data`'s `sagemaker:Create*` wildcard
  stands; `Workloads` is enumerated because Staging and Production legitimately call
  `CreateModel`/`CreateEndpoint`). **Decision 1 costs no feature, measured:** `CreateNotebookInstance` denied
  while `CreateSpace` and `datazone:ListDomains` still work. **`Sandboxes` is governed by inheritance.**
  Three consequences are *stated* rather than open: **Athena is allowed in `Data`** on purpose (Stage 5's
  Iceberg maintenance), Stage 11's to detect; an ASG launches through a service-linked role and no SCP
  reaches it; and **`guardduty:UpdateDetector` blocks Stage 11 step 4 in Audit** by design. Untested and
  recorded so: `s3:DeleteBucket`, and the **positive** half of the `Data` crawler carve-out, which needs
  Stage 5's **`awsds-data-catalog-maintenance`** role.
- **The denial message names the policy id**, so attribution needs no CloudTrail — **but AWS names only one
  matching policy**, which is how a document sits attached and unexercised (Lesson 20).
- **The battery is a script: `./aws/probes/scp-battery.sh`** (2026-08-13), probes in `probes/probes.sh`, phases
  `root`/`ou`/`region`/`tags`/`rcp`/`decl`. It read-backs deployed policies against `policies/` first
  (all four types — reading only `SERVICE_CONTROL_POLICY` reported three of them as absent both before and
  after attachment), aborts on a dead SSO session, and **never attaches** — that stays a human act on
  Management. Last full run: **93 as expected, 0 unexpected, 0 untested**. It has **no reach into Log Archive
  or Audit** and never will: those accounts hold no profile, which is what Stage 1d step 12 has to plan
  around. Every probe declares a mandatory `safety` (`ro`/`dryrun`/`blocked`/`creates`);
  the **three `creates` run in `Policy Canary` and nowhere else**, enforced by the driver, so the whole `ou`
  phase cannot create anything in a real account even with the ceiling removed.
- **7.7 IS DONE. `CT.MULTISERVICE.PV.1` on five OUs and the two root-user controls on the same five**
  (`Policy Test`, `Workloads`, `Data`, `Interactive`, `Identity`) — **not `Sandboxes`, by the rule below;
  not `Security`, which was never a target, so `Log Archive` and `Audit` have no Region ceiling and that is
  now Stage 1d step 12's decision.** Region
  half measured 61/61 by the battery. **Verification (vii) answered** from the attached document (86
  `NotAction` entries, none of ours) — and it **falsified a plan prediction: `ecr-public:*` is exempt**, so
  `DenyEcrPublicEntirely` is the only thing denying it. `ssm:GetParameter` *is* denied in `us-east-1`.
- **Control Tower's packing is per enablement and inconsistent across OUs** — the root statements went into
  the *original* guardrail on `Policy Test`/`Workloads`/`Interactive` but into the *Region* document on
  `Identity` (`p-fw2pctqw`) and `Data` (`p-pk85fvr1`). **Read the `Sid` list; a document's id says nothing
  about its contents**, and "the region policy" is a name for two different things.
- **Nothing is attached or enabled on `Sandboxes` unless it *differs* from `Interactive`** — **D37**,
  2026-08-13, and it governs Stage 14. Verification (xi) was closed both ways first: the OU accepted
  `enable-control` (registered target), *and* the deny that fires there names `Interactive`'s (Lesson 20) —
  then the control was disabled and its document deleted. **Cost: `Sandboxes` reads as zero controls while
  its accounts are governed** — an enablement is not inherited, only the statements are.
- **`ExemptAssumeRoot` is set on all five, verified by reading every document** — `Policy Test` was enabled
  without it first, and **no probe can see that**: every principal here is an SSO role and `ArnLike …:root`
  never matches, so the document read is the only instrument. `GRRESTRICTROOTUSER` ANDs
  `Null: aws:AssumedRoot=true` with the ARN test. **The omission was nearly free because member accounts
  hold no root credentials at all (1a 6.4), so an unexempted control denies exactly and only
  `AssumeRoot`** — empty population, one side effect, and it is self-sealing
  (`IAMCreateRootUserPassword` runs *inside* such a session). The access-key control carries no exemption
  and must not (D16).
- **The validation-before-authorization wall is per *action*, not per service** — measured: `ExportImage`
  authorized against a malformed AMI id, `CreateStoreImageTask` needed a real one, `StartInstances` never
  authorized at all. **A first-try validation error is a reason to retry with a real id, not a result**
  (Lesson 21).
- **A carve-out keyed on a principal ARN cannot defend itself** — whoever can create a role matching the
  pattern, or edit the exempted role's trust policy, inherits the exemption. Both carve-outs (BPA, D27) are
  now a written requirement on **Stage 2's boundaries** and Stage 5's role. Unverified and cheap: whether
  IAM even permits `CreateRole` under `/aws-reserved/`.
- **The repository is documentation only, with one exception since 2026-08-13**:
  `terraform-live/identity/org-policies/` holds 1c's policy **documents** (templates with placeholders, plus
  `render.sh`, which writes the pasteable copies into untracked `aws/output/`). No `.tf` anywhere until
  Stage 2.
- **All thirty-six decisions are closed** ([`plan/decisions/INDEX.md`](plan/decisions/INDEX.md)). The four
  governing what happens next: **D32** (`SSOUserEmail`), **D33**/**D34** (who vends), **D35** (`Sandbox` is
  one per business unit; every other account is exactly one).
- **The landing zone's second half is three stages, and only 1d is left**: **1b** (done), **1c** (done),
  **1d** (steps 9, 10, 11 and the new 12, independent of each other and doable in any order).
  **1d has no `log/` file yet** — the user creates it from an existing header.
- **The identity seam, settled 2026-08-09 by review** (`plan/conventions.md`): **people** — users, groups,
  memberships — stay in the directory; **entitlements** — permission sets, boundaries, group→account
  assignments — are Terraform. So **1b creates one permission set and specifies seven**; the other six are
  *written* in Stage 2 step 5, never typed into a console. **1b step 8.3's alarm is unfiltered** by
  decision, with the filtered variant in `plan/institutional-delta.md` for real headcount.
- **Still needed from the user: one thing, and it blocks Stage 13 alone** — **the domain name** (D15
  phase 2). Everything the landing zone was waiting on is settled.
- **No public DNS before Stage 13** (D15); internal names are `*.internal` off an internal CA (D36, INT-19).
- **Settle earliest:** **INT-11** — half of it is measured already (LF cross-account reads **4**), so what
  is left is 1d 11.1's RAM enablement plus **defending a value nobody set** against Stage 5's first apply —
  and **INT-13** (no convenience-preserving fallback).

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

