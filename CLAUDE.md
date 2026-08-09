
# General Objective

The objective of this project is to create a Data Science environment based on AWS cloud infrastructure, using my personal AWS account.

The goal is to achieve the following:

- All user access to the cloud infrastructure will be performed through a VPN.

- Use SageMaker as a development tool for Data Scientists.

- Protect data against leakage (DLP), mainly targeting SageMaker. There is no single AWS product that does
  this, so the requirement is broken into the four problems it has to solve:

	- sensitive-data discovery and classification: know which sensitive data exists and where it is stored.
	- fine-grained access control: restrict who can read which database, table, column and row.
	- egress control: restrict where data can be sent to from the development environment.
	- exfiltration detection: detect and alert on abnormal data access or data movement.

- SageMaker should have access to the internet. We'll explore implementing some restrictions, keeping the possibility of software updates, installing packages, and accessing a few websites.

- Use GitLab hosted on AWS for source-code control.

- Use GitLab Pages to host docs.

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

## Application source code layout

This is a template for an application developed by a data scientist and intended for deployment in a production environment.

```
app-etl/
├── src/
│   ├── main.py
│   ├── pipeline/
│   └── sql/
├── tests/
│   ├── test_pipeline.py
│   └── test_sql.py
├── .gitlab-ci.yml
├── Dockerfile # builds the application Docker container for deployment
├── terraform/ # uses predefined Terraform modules hosted at `terraform-modules`
│   ├── main.tf
│   ├── variables.tf
│   └── envs/
├── pyproject.toml
└── README.md
```

The development stack is similar to this application: <https://github.com/felipenoris/etl-cookbook-tutorial>.

# Guidelines

## AWS Region

All infrastructure will be deployed in the `us-west-2` Region.

## LOG

`LOG.md` contains all the actions performed during this project.
Never update `LOG.md`. I'll edit this file.

## Tools installed in the current environment

- terraform: <https://developer.hashicorp.com/terraform/install>.

- aws client: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>.

- uv: <https://docs.astral.sh/uv/>.

## `secrets` folder

This folder is ignored by git. It contains personal information. Never edit this folder, and never
write anything into it. Claude can read the files in this folder to gather information.

**Never copy or reproduce any email addresses or telephone numbers contained in this folder into any other project files.**.

## Organization

- The file `ORGANIZATION.md` contains the AWS OUs, accounts and users.

- All accounts will be registered under an AWS Organization managed by the `Management Account` using Control Tower.

- Accounts will be used to isolate environments.

- Promotion happens from: Development -> Staging -> Production. Given that Sandbox is the experimentation environment.

## terraform

- All infrastructure code will be in Terraform.

- Steps done manually by me will be recorded in the `LOG.md` file. Never update `LOG.md`. I'll edit this file.

- The Terraform code will have a subfolder for each controlled account (environment).

- Two trees: `terraform-live/` (one subfolder per controlled account, sliced by lifecycle layer) and
  `terraform-modules/` (reusable modules, consumed by git tag). **The authoritative layout, with the
  `[P]`/`[D]`/`[E]` layer of every slice, is in [`plan/conventions.md`](plan/conventions.md) §6** —
  kept in one place on purpose, so the two copies cannot drift.

## References

On every interaction, add to `REFERENCES.md` all the internet links Claude used as references.

## `README.md`

Update `README.md` with information about how we are structuring our AWS resources. Also, document the project layout so that people can understand the files and main components.

## Pricing

For every new AWS service referenced, update `PRICING.md`.

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

| Task | Read |
|---|---|
| Anything | this file + `GENERAL_PLAN.md` (plan core: principles, account map, both indexes) |
| Execute a stage | [`plan/stages/`](plan/stages/INDEX.md)`stage-NN-*.md`, the decisions in its **Consumes** row, and [`plan/conventions.md`](plan/conventions.md) |
| Plan, review, or settle a decision | add [`plan/lessons.md`](plan/lessons.md) and [`plan/open-questions.md`](plan/open-questions.md) |
| Look up a decision | [`plan/decisions/INDEX.md`](plan/decisions/INDEX.md) first — open a decision file only for its reasoning |
| Cost of a new service | [`PRICING.md`](PRICING.md) — measured from the Price List API, never estimated (Lesson 6) |
| Cross-account wiring | [`plan/integrations.md`](plan/integrations.md), the `INT-nn` rows |
| "What would an institution do?" | [`plan/institutional-delta.md`](plan/institutional-delta.md) |
| Root is needed, or its alarm chain is being changed | [`plan/runbooks/break-glass.md`](plan/runbooks/break-glass.md) |

Do not open by habit: [`plan/history.md`](plan/history.md), [`plan/institutional-delta.md`](plan/institutional-delta.md).
Reference things by **stable ID** — `D26`, `INT-11`, `Stage 1b step 7` — never by section or row number.

### Current position

- **Stage 1a nearly done; `LOG.md` is authoritative.** Control Tower enabled (`us-west-2`), budget set,
  and `Development`, `Sandbox Account 1`, `Production`, `Data Governance`, `Policy Canary` and `Identity`
  vended. **Accounts left: `Staging` alone**, deferred on the account cap — the increase to 15 is *requested*
  and has to be confirmed before that vend (Stage 1a pre-flight has the arithmetic). **Step left: 6**
  (centralized root access; procedure written 2026-08-09 as 6.0-6.8). Step 5's chain was built the same day,
  but `LOG.md` records the test as *run* and not its **result** — 6.5 settles it, since each deletion fires
  the same alarm. Best done **before** the `Staging` vend: accounts created afterwards have no root at all.
- **The OU tree is not the one D23 first described** — revised 2026-08-09 by execution; full tree in
  [`plan/architecture.md`](plan/architecture.md). `Identity` has an OU of its own, because the foundational
  `Security` OU refused the vend, so it inherits no guardrails and 1b step 7 must attach its set; and
  `Sandboxes` is nested under `Interactive`, holding the per-unit accounts with no policy set of its own.
  **Depth is 2** — Stage 2's OU `for_each` must recurse, or every Sandbox account is invisible to it.
- **The repository is documentation only**; `terraform/` is empty until Stage 2 replaces it with
  `terraform-live/` + `terraform-modules/`.
- **All thirty-five decisions are closed** ([`plan/decisions/INDEX.md`](plan/decisions/INDEX.md)). The four
  governing what happens next: **D32** (`SSOUserEmail` is always the infrastructure user, and it grants
  administrator), **D33**/**D34** (`AWS Control Tower Admin` vends, from the access portal, never root,
  permanently), **D35** (`Sandbox` is one per business unit; every other account is exactly one).
- **Still needed from the user**, none blocking now: **the domain name to register** (D15, blocks Stage 7),
  the AZ name-to-ID check (1b step 6), which decides how Stage 3 anchors subnets, and — due at 1b step 7 —
  whether the `Interactive` OU gets a policy set of its own; it carries none today.
- **Settle earliest:** **INT-11** (org-wide RAM sharing + Lake Formation cross-account v3 — fails
  *silently*) and **INT-13** (CodeConnections to the private GitLab — no convenience-preserving fallback).

**Budget for this section: ~2 KB** (raised from ~1 KB on 2026-08-09, when the section was cut back from
4.8 KB — [`plan/history.md`](plan/history.md) says why). It states *state*, not reasoning: reasoning belongs
in the decision file, narrative in `plan/history.md`. **A bullet here that explains *why* is a stale copy of
something that already lives elsewhere** — that test is the actual control, not the number. Re-trim whenever
a stage closes.

### Lessons carried forward

**Read [`plan/lessons.md`](plan/lessons.md) before planning, reviewing, or settling a decision.**
The eighteen titles are kept here so a lesson can be *recognised* without opening the file; the
reasoning that makes each one usable is in the file, and the titles alone are not a substitute.

1. **A copy of governed data landing somewhere less governed is not a hole to be closed.**
2. **A stand-in that shares an account with the thing it de-risks proves nothing about permissions.**
3. **When a decision moves a resource across an account boundary, re-check every condition that referenced it — especially conditions pointing at ephemeral things.**
4. **State that lives only inside an `[E]` resource is this design's recurring failure mode**
5. **An intention is not a control.**
6. **Prices are measured, not reasoned.**
7. **A rejected-on-cost option goes stale in the direction that flatters the rejection.**
8. **When the classic `aws` provider lacks a resource, check the CloudFormation registry and `awscc` before declaring a Terraform gap.**
9. **The axis question applies to people as well as to resources.**
10. **Before placing a new resource in an account, ask which axis it is on — and check whether a *registry* is being confused with a *runtime*.**
11. **A decision that changes *who authors* an IAM policy invalidates every claim made about that policy.**
12. **An edition or tier limit can reach a load-bearing control, not just a convenience.**
13. **A verification command that returns empty on both success and failure is not a verification.**
14. **A condition that has to appear in N places by hand is a control that will be missing from one of them.**
15. **An adopted-against-advice decision is undone by *delivery*, not by re-argument — and a revision trigger written about operating something cannot fire while you are still building it.**
16. **A manual step delegated to a console wizard is only as specified as the fields it names — and an unnamed field that grants permissions is a permission decision made by whoever is at the keyboard.**
17. **A service that "sets itself up" creates principals nobody chose — enumerate them before the next step depends on one.**
18. **A policy never constrains the principal that authors it.**

