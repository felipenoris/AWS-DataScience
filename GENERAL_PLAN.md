# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**. This file holds the **route** to get there.
- Every entry in the `Claude LOG` section of `CLAUDE.md` must reference the stage of this plan it belongs to
  (e.g. "Stage 3 - Networking, in progress").
- This plan is expected to change. Whenever a stage is finished or a decision is revisited, update this file
  in place. "Plan revision history" (§10) records only changes made **after** something has been provisioned
  — a plan edit that predates the resource it describes is just an earlier draft, and is not kept.
- Stages are ordered by dependency, not by importance. A stage can be split or reordered, but the
  prerequisites listed inside each stage must hold.

---

## 1. Baseline (state at the time this plan was written: 2026-08-07)

**Repository**

- Documentation only: `CLAUDE.md`, `LOG.md`, `README.md`, `REFERENCES.md`, `GENERAL_PLAN.md`, `LICENSE`.
- `ACCOUNTS_AND_USERS.md` (committed) describes the accounts and SSO users; `secrets/` (git-ignored)
  holds `emails.md` with the e-mail address behind each of them.
- `terraform/` exists but is empty. It must be replaced by `terraform-live/` and `terraform-modules/`
  (the layout defined in `CLAUDE.md`).
- Git remote is GitHub (`felipenoris/AWS-DataScience`). **This infrastructure repository stays on GitHub**;
  GitLab (Stage 7) hosts the *application* repositories and the CI/CD pipelines.

**Local tooling** (verified)

- `aws-cli` 2.36.18, `terraform` 1.15.8, `uv` installed.
- `~/.aws/config` has only a `[default]` profile with invalid credentials. No SSO profile configured yet.

**AWS**

- Management Account created manually through the AWS console. Nothing else exists.

**Planned accounts** (`ACCOUNTS_AND_USERS.md`, e-mails in `secrets/emails.md`): Management, Sandbox
(experimentation), **Development**, **Staging**, Production, **Data Governance**, Log Archive, Audit,
Identity — **nine accounts**, all e-mails registered. Staging arrived on 2026-08-08 with D20; Development
and Data Governance arrived later the same day with D21/D22, closing the two departures from the AWS
references that the first Staging revision had left open. Every earlier statement that six or seven
accounts "are the complete set" is superseded.
**Planned SSO users** (`ACCOUNTS_AND_USERS.md`): infrastructure (admin), **data scientist** (regular —
renamed from "sandbox user", read-write in Sandbox and Development), **deployment manager** (release
approvals) and **governance manager** (data-access approvals) — one persona until 2026-08-08, split then
because the two approvals sit on the two different axes (§3).

**Region:** `us-west-2` (decision D1, recorded in `CLAUDE.md`).

---

## 2. Guiding principles

These come from `CLAUDE.md` and constrain every stage:

1. **The Management account is bootstrap-only.** Anything done there is manual, through the console, and
   recorded by the user in `LOG.md`. Terraform does not manage the Management account.
2. **No IAM Users.** Humans authenticate through IAM Identity Center (SSO) and assume roles. Machines
   (GitLab CI) use OIDC federation to assume roles. No long-lived access keys anywhere — with exactly one
   documented exception, break-glass access (D16), because a rule with no escape hatch is a rule that gets
   broken under pressure.
3. **Everything else is Terraform.** One state per account/environment, no shared state across environments.
4. **Private by default.** Data assets and databases never face the public internet. The only public entry
   points are the VPN and, later (Stage 13), an experimental web tier.
5. **Incremental.** Each stage must leave the environment in a working, verifiable state.
6. **Cost is a first-class constraint.** This is a personal account. Every stage lists its recurring cost and,
   where relevant, a cheaper alternative.
7. **Pay nothing while idle** (decision D11). Between sessions, metered resources are destroyed, stateful
   ones are stopped, and anything free at rest is simply left alone. See §5.1 — every stage must say which
   layer its resources belong to, so this shapes how each stage is designed, not just how it is operated.
8. **The region is a variable, not an assumption** (decision D1). The lab runs in `us-west-2` and stays
   there; keeping the region out of the code is plain Terraform hygiene, not migration work. See §4.1.
9. **Preventive controls come before detective ones.** The data perimeter (§4.2) is part of the landing
   zone, not of the DLP stage. Detecting an exfiltration you could have made impossible is a worse outcome
   than preventing it, and the preventive half (SCPs, RCPs, endpoint policies) is free.
10. **The lab is not the reference architecture.** Most decisions here are bent by a USD 50/month ceiling
    and a single operator. §11 records, decision by decision, what a large institution would do instead —
    so that what is learned here is the pattern, not the compromise.

---

## 3. Target architecture (summary)

Layers per §5.1: `[P]` persistent (free at rest), `[D]` dormant (stopped between sessions),
`[E]` ephemeral (destroyed between sessions).

```
AWS Organization (Management account - console only)                        [P]
│
├── OU Security
│   ├── Log Archive account  (created by Control Tower, S3 Object Lock)     [P]
│   ├── Audit account        (created by Control Tower) <- security guardian [P]
│   │                           GuardDuty / Security Hub / Macie / Analyzer
│   └── Identity account     <- Identity Center delegated administration    [P]
│
├── OU Interactive           <- one SCP set: interactive compute allowed,
│   │                           no human infrastructure changes (D23)
│   ├── Sandbox account      <- EXPERIMENTATION: the unit of work is a notebook
│   │   ├── VPC, subnets, IGW, security groups, private DNS zone            [P]
│   │   ├── blueprint target (D26): the experimentation project's
│   │   │     environments are provisioned here by the domain in
│   │   │     Development (SageMaker AI apps VPC-only, restricted egress)   [E]
│   │   ├── scratch / derived-zone S3 buckets (per-principal, D19)          [P]
│   │   ├── WireGuard EC2    <- the only human entry point (see below)      [D]
│   │   ├── NAT Gateway + interface VPC endpoints                           [E]
│   │   └── EFS (NFS shared filesystem, lifecycle to IA) <- Sandbox only D24 [P]
│   │
│   └── Development account  <- DEVELOPMENT: the unit of work is a pipeline
│       │                       (repository with tests, workflows)          D21
│       ├── VPC (same module, own CIDR, peered to Production for GitLab)    [P]
│       ├── blueprint target (D26): the engineering project's
│       │     environments are provisioned here by the domain in
│       │     Data Governance                                               [E]
│       ├── scratch / derived-zone S3 buckets (per-principal, D19)          [P]
│       └── NAT + interface VPC endpoints                                   [E]
│
├── OU Data                  <- one SCP set: no USER compute (two named
│   │                           exceptions); data cannot be deleted, only
│   │                           governed (D22, D23, D26, D27)
│   └── Data Governance account <- the OWNERSHIP axis: owns the STATE of
│       │                          data AND its governance. Nobody signs in
│       ├── S3 raw/curated (Iceberg) - the only copy of governed data       [P]
│       ├── Glue Data Catalog + Lake Formation (LF-Tags, D13 registration)  [P]
│       ├── SageMaker unified domain (DataZone V2) + project profiles,
│       │     blueprints (Tooling, Lakehouse Glue/Athena, ML), account
│       │     associations, SageMaker Catalog            <- D26            [P]
│       │     A REGISTRY, NOT A RUNTIME: blueprints provision compute
│       │     into Sandbox and Development, never here
│       ├── Glue Crawlers (raw + drop-box) under the maintenance role,
│       │     event-driven; Iceberg optimizers           <- D27            [P] cfg
│       ├── ingestion drop-box prefix (PutObject-only, dated, D18)          [P]
│       └── LF cross-account shares -> Sandbox, Development (read),
│           Production (read + governed write: the producer path)           [P]
│
└── OU Workloads             <- one SCP set for both: no interactive compute,
    │                           no human control plane (D20)
    ├── Staging account      <- deployment target; integration tests land here
    │   ├── VPC (same module, own CIDR; deliberately not peered - Stage 3)  [P]
    │   ├── S3 + Glue Catalog (Iceberg) - sampled or synthetic data only,
    │   │     local to this account, never LF-shared production data        [P]
    │   ├── SageMaker job execution roles (no domain, no Model Registry)    [P]
    │   ├── NAT + interface VPC endpoints (only during a promotion run)     [E]
    │   └── app slices, deployed by the pipeline and torn down after tests  [E]
    │
    └── Production account   <- no human runs code here; no Studio domain   D17
        ├── VPC (mirrors sandbox topology; peering accepter for Sandbox
        │     and Development)                                              [P]
        ├── ECR (dev-env images, application images)          <- D14        [P]
        ├── CodeArtifact (package proxy: PyPI, Cargo, ...)    <- D14        [P]
        ├── SageMaker Model Registry + job execution roles    <- D17        [P]
        │     └── training/processing jobs, endpoints (pipeline-submitted)  [E]
        │         reading and writing the lake through the LF share (D22)
        ├── GitLab (EC2, private) + GitLab Pages              <- D14        [D]
        ├── internal ALB for GitLab/Pages (rebuilt per session)             [E]
        ├── GitLab Runners                                    <- D14        [E]
        ├── NAT Gateway + interface VPC endpoints                           [E]
        ├── orchestration, built twice and compared (D7):                   [E]
        │     (A) MWAA  (B) EventBridge + Step Functions + Lambda/Fargate
        └── (Stage 13) public web tier -> private backend                   [E]
```

**The two axes, made explicit (D22, D23, D26).** The OU axis is *lifecycle*: how mature and how protected
the compute in an account is (Interactive → Workloads). The Data OU sits on the other axis, *ownership*:
the lake outlives every application that reads it, so it lives in an account whose policy set is about
retention and governance, not deployment. Environments hold **compute**; the Data Governance account holds
**state and governance** — since D26 that includes the SageMaker unified domain, which is a registry of
projects and data products and therefore an ownership-axis resource, not a Development one. **The
platform accounts sit on neither axis** (Management, Log Archive, Audit, Identity): they serve every
account and belong to no environment. The consequence that has to be said out loud, because it is asked
every time: *an account off the lifecycle axis is not "a production account"*. Some of them —
Identity, Data Governance — are nonetheless high blast radius. Sensitive and production are different
properties. `ACCOUNTS_AND_USERS.md` carries the same classification per account. Every environment reaches the same single copy of the data through a Lake Formation
cross-account share — which is what `CLAUDE.md` asked for ("use AWS Lake Formation to share data
cross-account") taken to its logical conclusion: the share is the *default* read path, not an exception.

**Why the tooling sits in Production (D14).** GitLab, its runners, ECR and CodeArtifact are the supply
chain: whoever controls them controls what runs in Production. They must not live in the account where
the `data-scientists` group has broad permissions. Two consequences shape several stages: the Production
VPC has to exist before Stage 7 (so it is built in Stage 3, not Stage 9), and the human path to GitLab is
laptop → WireGuard in Sandbox → VPC peering → GitLab in Production.

Note the refinement this forces on "only Terraform and CI/CD touch Production": nobody changes Production
*infrastructure* by hand, but humans do *use* a service hosted there (GitLab, over the VPN). The boundary
is the control plane, not the account.

**How a human actually reaches each account, because "the VPN is the only entry point" hides two different
paths.** The WireGuard instance lives in Sandbox and is a **full tunnel** (Stage 4 step 5), so *all* the
laptop's traffic leaves through its Elastic IP — and that, not a route into every VPC, is what makes the
single entry point true. Concretely there are two paths and they should not be confused:

- **VPC-level reach**, which only Sandbox and Production have. The tunnel terminates in the Sandbox VPC,
  and the Sandbox↔Production peering extends it to the GitLab subnet. This is the path for private DNS
  names, the EFS mount (D24) and anything addressed by a private IP.
- **AWS API and portal reach**, which every account has, over public AWS endpoints exited through the
  WireGuard Elastic IP. This is how **the unified domain is used (D26)**: the Unified
  Studio portal — like the presigned Studio URL before it — is a public endpoint even when project
  compute is `VpcOnly`; VPC-only governs how the *app containers* reach the network, not how the browser
  reaches the UI. The laptop needs no route into the Development VPC.

The control that makes the second path VPN-only is therefore **`aws:SourceIp` on the WireGuard Elastic IP**
(Stage 4 step 8), not `aws:SourceVpce`. Getting that backwards is the fastest way to write a condition that
either denies everything or protects nothing.

**Where the humans are (D17, D18, D21).** D14 refined that boundary once; the decisions above refine it
further, and the resulting sentence is the one to remember: *humans run code in the Interactive OU and
nowhere else; they read the deployment targets' data planes; nobody changes a Workloads-OU control plane
by hand, and the lake is written only through governed engines.* Concretely: interactive compute exists in
Sandbox and Development and nowhere else — since D26 one unified domain, registered in Data Governance,
whose project blueprints provision compute into the two Interactive accounts and into no others (D17 as
revised by D21 and re-read by D26). The domain being elsewhere changes nothing about where code runs: it
is a registry, and the project profile names the target account. The data
scientist holds read-only
permission sets on Staging and Production for logs, catalog metadata, job status and Athena (D18); the
SageMaker runtime in Staging and Production is reachable only by a pipeline; and no human signs in to the
Data Governance account at all outside the infrastructure role (D22).

---

## 4. Key decisions

| # | Decision | Status | Notes |
|---|---|---|---|
| D1 | Region | Decided (2026-08-07): **`us-west-2`**, and it stays there | Oregon, chosen on cost — roughly half São Paulo's price on metered items. Data residency is explicitly not a concern: this is a test with no real data. The project mirrors something that would run in `sa-east-1` in practice, but **that move is hypothetical and is not planned work**; the only thing it implies is the Terraform hygiene in §4.1, which is worth doing anyway. The availability question was answered and recorded there: nothing this plan uses is missing from São Paulo. |
| D2 | Control Tower vs. plain Organizations | Decided: **Control Tower** | Required by `CLAUDE.md`. It creates the Log Archive and Audit accounts, enables CloudTrail/Config org-wide and provides guardrails. Downside: AWS Config is the main recurring cost of the landing zone. |
| D3 | Terraform state location | Decided: **per-account S3 bucket, native S3 locking** | Terraform 1.15 supports `use_lockfile = true`, so no DynamoDB table is needed. Sandbox state lives in the Sandbox account, Production state in the Production account, and identity state in the Identity account (D10). This avoids putting state in the Management account (principle 1) and avoids cross-account state access. |
| D4 | VPN technology | Decided (2026-08-07): **self-managed WireGuard** | A `t4g.nano` EC2 instance in a public subnet, layer `[D]` — stopped between sessions, not destroyed, so the host key and peer configuration stay stable. Idle cost is its 8 GB EBS volume (~USD 0.65/month) plus the Elastic IP, which lives in the `[P]` foundation slice (~USD 3.65/month) so the endpoint address never changes. Consequences to handle in Stage 4: no native Identity Center integration, so peer public keys are provisioned by Terraform from a git-ignored variable file; and it is a single point of failure, which is acceptable for a lab. AWS Client VPN (~USD 73/month, SAML to Identity Center) stays documented as the managed alternative if SSO-integrated VPN becomes a requirement. |
| D5 | SageMaker internet restriction mechanism | Decided (2026-08-07): **build BOTH and compare, in Stage 6** | Not one mechanism but two designs, implemented behind a switch and evaluated against each other — see §4.3. **(A) Limited internet:** NAT plus an allowlist, using Route 53 Resolver DNS Firewall and/or a Squid proxy. **(B) No internet:** no NAT at all for the SageMaker subnets; packages arrive through CodeArtifact (upstream to the public repositories) and ECR pull-through cache, everything else through VPC endpoints. AWS Network Firewall (~USD 290/month) stays documented as the enterprise variant of (A) but is not built. The user's stated reservation about (B) is recorded in §4.3: CodeArtifact does not cover every language this environment needs. |
| D6 | DLP approach | Decided (2026-08-07): **native AWS combination**, on top of a data perimeter | The objective in `CLAUDE.md` is split into four problems, each with its own control: discovery/classification → **Macie**; fine-grained access → **Lake Formation** (LF-Tags, column and row filters), made enforceable by D13; egress control → **D5** plus the SageMaker VPC-only domain; exfiltration detection → **CloudTrail data events + GuardDuty + Security Hub** with CloudWatch alarms. **Underneath all four sits the data perimeter (§4.2)** — SCPs, RCPs and VPC endpoint policies built in Stage 1, not Stage 11, because they are the only controls that make exfiltration structurally impossible rather than merely visible. A third-party agent-based DLP is only evaluated in Stage 11, after these are in place and their gaps are known. |
| D7 | Workflow orchestration in production | Decided (2026-08-08): **build BOTH and compare, in Stage 10** | Not one orchestrator but two implementations of the same workflow, behind the same application contract — the shape D5 already uses for egress. **(A) MWAA**, hosted Airflow, which is what `CLAUDE.md` names explicitly and what keeps the workflow expressed as a portable Airflow DAG. **(B) Plain AWS services**: **EventBridge Scheduler** as the trigger, **Step Functions** as the state machine, **Lambda** for glue steps and **ECS/Fargate** (or a SageMaker job) for the container steps. The two are *not* equivalent, which is the point of building both — see the cost and lifecycle asymmetry below. **Not built, kept documented:** SageMaker Pipelines (native to the environment the workflow is developed in, pay per execution — the shortest path from notebook to production, and the right answer if the workflow turns out to be a training pipeline rather than an ETL) and self-managed Airflow on ECS (all of Airflow's semantics, none of the managed cost, all of the operational burden). **Cost asymmetry (`us-west-2`, authoritative rates in `PRICING.md`):** MWAA charges an *environment fee per hour of existence*, billed at one-second resolution, whether or not a DAG runs — `mw1.micro` USD 0.29/h (~USD 212/month always-on), `mw1.small` USD 0.49/h (~USD 358/month), plus USD 0.10/GB-month of metadata-database storage and any additional worker/scheduler/web-server instances. Design B has **no standing fee at all**: Step Functions Standard is USD 0.000025 per state transition, EventBridge Scheduler USD 1.00 per million invocations, Lambda USD 0.0000166667 per GB-second — a nightly workflow costs cents per month. **The unit of billing is the *environment*, not the account, the user or the DAG** — one `CreateEnvironment` call, one hourly fee, whether it runs zero DAGs or two hundred, for one data scientist or for the whole team. Volume reaches the bill only through *concurrency*, via autoscaled worker instances. The consequence for the promotion chain is worth stating before someone proposes it: giving Development, Staging and Production each its own Airflow means three environments, ~USD 1 073/month in `us-west-2` — which is a second, financial reason for what D17 already decides on architectural grounds, that orchestration lives only in Production (§6). "Test the DAG in Staging first" is answered by an `[E]` environment for an hour, not by a standing second one. A third MWAA shape removes the multiplication entirely: **MWAA Serverless** (GA November 2025), USD 0.088 per task-hour with a one-minute minimum and **no environment fee**, which is pay-per-execution Airflow and therefore the variant to try first. Its trade-offs are not only financial and are set out in `PRICING.md` §1.3: YAML workflow definitions instead of Python DAGs, Airflow v3 fixed, **no Airflow web UI**, and — the one that cuts in this project's favour — **one IAM execution role per workflow**, where provisioned MWAA gives every task the same environment role. Against the data perimeter (§4.2) that is an argument for Serverless independent of cost. **The Terraform route, raised as a blocker in the morning revision and resolved in the evening one:** the classic `aws` provider still has nothing for MWAA Serverless (the issue requesting `aws_mwaaserverless_workflow` is open with no branch), but **`AWS::MWAAServerless::Workflow` exists in CloudFormation, and the `awscc` provider exposes it as `awscc_mwaaserverless_workflow`** — and `awscc` is a required provider anyway once D26 adopts the Unified Studio module. Alternative A is buildable in Terraform today; re-verify at Stage 10, with `aws_cloudformation_stack` as the wrapper fallback and a `mw1.micro` environment as the last resort. Alternative B's components are pinned by D28: **EventBridge Scheduler** as the trigger, **Step Functions** as the state machine, and an explicit **`aws_cloudwatch_log_group` per workflow** for execution logs. The full production artifact contract — what must exist in the deployment target for either alternative to receive a scientist-authored workflow — is D28. **Layer `[E]` — with a caveat that design B does not have:** an MWAA environment takes ~20-30 minutes to create and about as long to delete, so it does not fit the `make up`/`make down` cadence the way a NAT gateway does, and its metadata database (run history, XComs, UI-defined connections and variables) is state living *only* inside an `[E]` resource, which §5.1 rule 2 forbids. DAG code is in S3 and survives; run history does not. Either Stage 10 adds an export-before-teardown step, or MWAA is run as an `[E]` **experiment** whose history is expendable — decide that when the stage starts, and record it. Design B is `[E]` without qualification: the state machine definition *is* the state. **Unchanged from the previous version of this decision:** the application's entry point stays a plain container, so it can be driven by either implementation, or by the two options that were not built. |
| D8 | GitLab hosting | Decided: **self-managed on EC2 in the Production account, layer `[D]`** | Required by `CLAUDE.md`. GitLab CE Omnibus on a private-subnet EC2 instance, reached through the VPN, backed up to S3. Account placement per D14. Sizing: 8 GB RAM is the realistic minimum for GitLab + Pages — `t4g.large` (ARM) is ~20% cheaper than `t3.large` for the same memory and GitLab Omnibus ships arm64 packages. Stopped between sessions rather than destroyed (~USD 4/month of EBS), because rebuilding from backup on every session is the fragile path. |
| D9 | Number of AZs | Decided: **2 for subnets, 1 for metered endpoints** | Subnets, route tables and NAT-less network plumbing are free, so the topology spans 2 AZs and stays honest. Interface VPC endpoints are charged per AZ, so they default to a single AZ during lab sessions; a resource in the other AZ still resolves and reaches them, at the cost of cross-AZ traffic and no AZ redundancy — an acceptable trade in a lab, and a one-variable change if it ever is not. |
| D10 | Identity Center administration | Decided (2026-08-07): **delegated to a dedicated Identity account** | The Identity Center instance and its identity store are created in the Management account and cannot be moved; what is delegated is their *administration*. One member account is registered as delegated administrator (`sso.amazonaws.com`), and from there Terraform manages permission sets, groups and assignments — so Terraform never needs credentials in the Management account, which is what makes principle 1 real rather than aspirational. The role goes to a **dedicated Identity account** rather than to the Audit account: Audit stays the security guardian (GuardDuty, Security Hub, Macie findings) and Identity owns access management, so the two concerns do not share a blast radius. Costs one extra Control Tower-governed account, i.e. one more AWS Config recorder (~USD 0.50-1/month) — accepted in exchange for the separation. **Consequences:** (i) assignments whose *target* is the Management account cannot be managed from the delegated account and stay manual; (ii) the Identity account can grant administrative access to any account in the organization, so it is as sensitive as Management — the data scientist must never have access to it; (iii) Control Tower's own permission sets (`AWSAdministratorAccess` and friends) are left alone, since editing them causes landing-zone drift. |
| D11 | Lifecycle of the lab | Decided (2026-08-07): **resources are ephemeral, accounts are not** | The environment runs for a few hours per session and is shut down in between. Accounts, the Organization, Control Tower and Identity Center are never destroyed. Within the accounts the rule is not "destroy everything" but **"pay nothing while idle"**: resources that cost nothing at rest are simply left in place, resources that meter are destroyed, and stateful services that are awkward to rebuild are stopped rather than destroyed. Three layers, defined in §5.1. |
| D12 | Budget ceiling | Decided (2026-08-07): **USD 50/month** | With the three-layer model the projection is a ~USD 18-22/month floor plus ~USD 0.28-0.35 per lab hour, so roughly USD 26-27/month at the expected usage (§5). The AWS Budget created in Stage 1 alerts at 50/80/100% of USD 50, with Cost Anomaly Detection alongside it. This ceiling is what rules out always-on GitLab (~USD 60/month by itself) and confirms the stop/start approach. |
| D13 | How Lake Formation is actually enforced | Decided (2026-08-07): **execution roles get no direct S3 access to registered locations** | Lake Formation only constrains engines that ask it. A role holding `s3:GetObject` on a registered bucket can read the raw Parquet from a notebook and every column and row filter becomes decoration. So the fine-grained access control objective in `CLAUDE.md` is only real if the SageMaker execution role's S3 permissions **exclude** the Lake Formation-registered prefixes, and tabular access goes exclusively through an LF-aware engine: Athena, Glue interactive sessions, or EMR with runtime roles. Non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access. Lake Formation's **hybrid access mode** is the documented migration path if a workload turns out to need both, and is a deliberate exception rather than the default. This is decided in Stage 5, before Stage 6 can bake the bypass into the execution role. |
| D14 | Where GitLab, Runners, ECR and CodeArtifact live | Decided (2026-08-07): **the Production account** | These four are the software supply chain. In the Sandbox account they would sit next to a `data-scientists` group with broad permissions, which means the runner holding the deploy credentials, and the registry Production pulls from, would both be modifiable by the people the approval gate is supposed to gate. Putting them in Production removes that path and costs no extra account. **Accepted trade-off:** build and runtime now share an account, so there is no blast-radius boundary between "the thing that builds" and "the thing that runs" — a compromise of GitLab is a compromise of Production. A large institution splits these into a Shared Services / Tooling account in an `Infrastructure` OU (§11). **Consequences:** the Production VPC moves from Stage 9 to Stage 3; Sandbox↔Production VPC peering is needed so the VPN reaches GitLab (and, since D21, a second peering from Development); ECR and CodeArtifact are consumed cross-account from **both Interactive accounts**; and the data scientist needs a narrow, service-level (not infrastructure-level) reach into Production. |
| D15 | TLS for internal endpoints | Decided (2026-08-07): **a real public domain plus split-horizon DNS** | ACM cannot issue a certificate for `sandbox.internal` — public certificates require a domain you can validate publicly, and AWS Private CA costs ~USD 400/month (~USD 50 in short-lived mode), both over the ceiling. The workable path: register one public domain, keep a public hosted zone **for DNS validation only**, issue free public ACM certificates (including the wildcard GitLab Pages needs), and resolve the names to private addresses through the **private** hosted zone. A public certificate on an internal ALB is supported; nothing is published. Cost ~USD 0.50/zone plus the domain (~USD 12-15/year). **Needs input from the user: which domain name to register.** |
| D16 | Break-glass access | Decided (2026-08-07): **one documented emergency path, tested and alarmed** | "No IAM Users" (principle 2) has no answer for an IAM Identity Center outage or a misapplied SCP that locks everyone out, and an absolute rule with no escape hatch is one that gets broken improvised, under pressure, at the worst moment. The exception: a break-glass mechanism in the Management account with hardware MFA, credentials stored offline, never used in normal operation, and a CloudWatch alarm on any use of it. Documented in Stage 1 and tested once. The Management account root user's recovery path is documented alongside it. |
| D17 | Where the data scientist works, and what crosses the account boundary | Decided (2026-08-07), revised (2026-08-08, D21): **interactive compute exists only in the Interactive OU (Sandbox and Development); the deployment targets carry the SageMaker runtime, but only pipelines submit to it** | "SageMaker" is two things and the account boundary runs between them. The **interactive** half — Studio domains, user profiles, JupyterLab/Code Editor apps — exists in the Sandbox and Development accounts and nowhere else: a Studio domain in a deployment target would put unreviewed code back inside the account boundary, which is the one thing the split buys. (The original decision said "Sandbox-only"; D21 split the interactive world into two accounts, so the invariant is now stated against the OU, which is where the SCP enforcing it attaches anyway.) The **runtime** half — training and processing jobs, Pipelines, Model Registry, endpoints — exists in Staging and Production, because that is where artifacts are tested, retrained and served; what changes is that a pipeline submits to it, never a person. This is also what AWS's own multi-account MLOps references do: Studio lives in the development/data-science accounts, and staging and production are deployment targets with no domain of their own. **The promotion boundary is four artifacts**, all travelling Development → Staging → Production through the pipeline (D20, D21): the container image (ECR), the model version (Model Registry), the workflow definition and application code (a git tag), and the Terraform that instantiates them. Sandbox work enters that chain only by graduating into a Development repository through git (D21) — there is no Sandbox → Staging path. **The Model Registry lives in Production** — D14 already collapsed the reference architecture's Tooling account into Production, and a model package group costs nothing at rest; Staging reads the registry and runs the approved version, it does not keep one of its own. **Consequences:** `terraform-live/production/sagemaker/` is a `[P]` slice (model package groups, and the execution role that pipeline-submitted jobs assume), with a job-execution-role-only counterpart in `terraform-live/staging/sagemaker/`; Stage 8's shared base image remains load-bearing, because "promote only the code" is only true if the runtime is identical by construction; and debugging a failed production job is a time-boxed elevated role approved by `deployment-managers`, logged and alarmed — not a notebook (the release approver owns this, not the governance one: it is a lifecycle act). |
| D18 | Data scientist access outside the Interactive OU | Decided (2026-08-07, restated 2026-08-08 for the nine-account layout): **data plane read, no compute, no control plane; writes only to enumerated prefixes** | `ACCOUNTS_AND_USERS.md` gives the data scientist "read-only access to production environment data, and read-write access to sandbox and development environment". The full access matrix, per account: **Sandbox and Development** — read-write, interactive, the D19 derived zones; this is where the person works. **Staging — read-only, and nothing else.** No writes at all, not even a drop-box: Staging exists to be written by the pipeline and read by a human diagnosing why the pipeline failed, which is exactly what the `amazon-sagemaker-secure-mlops` reference grants in its staging account — a staging environment a human can write to stops being evidence of what the pipeline does. **Production — the data plane without compute:** CloudWatch logs of a failed job, Glue catalog metadata, SageMaker job/pipeline/registry status, named S3 prefixes (application outputs), and Athena on a dedicated workgroup with a scan limit. Denied explicitly: the control plane in full, plus `sagemaker:Create*Job`, `sagemaker:CreatePresignedDomainUrl`, `glue:StartJobRun` and `lakeformation:GrantPermissions`. **Data Governance — no sign-in at all.** The lake (D22) is read through the Lake Formation share from Sandbox and Development, which is the canonical analytical path — the tools are where the person is, so signing in to the account that stores the data accomplishes nothing. The one write the data scientist has toward the lake is the **ingestion drop-box** in Data Governance (`s3:PutObject` into a dated prefix — no `GetObject`, `DeleteObject` or `ListBucket`; a letterbox, not a shared folder), granted cross-account by bucket policy to the Interactive-OU roles rather than by a sign-in. **Deliberately not built:** any general-purpose exchange bucket between environments, which would be a promotion path running parallel to the Stage 8 approval gate. **One consequence to handle before it bites:** every `aws:SourceVpce` deny in a bucket policy (Stage 5, Stage 9) is evaluated against callers from *other* accounts — a data scientist at a laptop reaches S3 through the Sandbox or Development VPC endpoints or through the WireGuard Elastic IP — so the condition has to be a list that admits them (§4.4 row 5), or every call fails with an `AccessDenied` whose cause is invisible from the error. |
| D19 | The derived zone — what Lake Formation does *not* do (extends D13) | Decided (2026-08-07): **the copy is not prevented; the destination is managed and the perimeter contains it** | Running a `SELECT` against the lake and storing the result is what a data science environment is *for*. Any principal that can read tabular data can materialise it outside the governed prefixes, and no configuration changes that. This is not a hole introduced by D18 — it has been true of the Sandbox since Stage 5, and of every SageMaker installation ever built. What it actually means is worth stating plainly: **Lake Formation's column and row filters are an entitlement mechanism, not a containment mechanism.** They decide what a principal may see at the moment of read; they say nothing about where the bytes go next. D13 makes the entitlement real; this decision covers everything after it. The practice: (i) **the output location is not the user's choice** — the Athena workgroup sets `EnforceWorkGroupConfiguration = true`, so a client cannot override the result location, and `s3:PutObject` on execution roles and permission sets is scoped to enumerated prefixes, never `*`; (ii) derived prefixes are **per principal** (`…/derived/${aws:userid}/`), so one person's copy is not a way around another person's grants; (iii) they carry a **lifecycle expiry**, so the shadow lake does not become permanent by accident; (iv) they sit **inside Macie's scan scope and carry CloudTrail data events** (Stage 11), because this is where sensitive data actually accumulates; (v) classification **inherits** — the output of a query over `restricted` data is `restricted` — stated as policy, because nothing enforces it automatically at this scale (§11: this is exactly where a catalog with lineage earns its price). **And the containment itself comes from somewhere else entirely:** the copy is tolerable because the data perimeter (§4.2) stops it leaving the organization and D5 stops it leaving the network. Preventing the copy was never the control. The perimeter is. |
| D20 | The Staging account | Decided (2026-08-08): **a seventh account, `Staging`, in a new `Workloads` OU alongside Production** | Every AWS multi-account MLOps reference this plan checked puts a pre-production deployment target between the development account and production (`README.md`, "What the AWS references recommend"). This plan did not have one, and the consequence was stated plainly in the 2026-08-07 revision: the first time application code runs against a production-shaped path would be *in* production. That revision tried to stand in for it with a `staging` Glue namespace inside the Production account — **that stand-in is now removed.** It caught schema and logic errors, but it shared an account, an IAM surface and a blast radius with the very thing it was meant to de-risk, so it could never catch a *permission* error, which is the failure class a cross-account promotion actually produces. **What Staging is:** a deployment target. No Studio domain (D17), no Model Registry of its own (it reads Production's and runs the approved version), no GitLab (D14). It carries a VPC, a data platform whose catalog mirrors Production's schema, SageMaker job execution roles, and the application slices the pipeline deploys and tears down. **Its data is sampled or synthetic and never a copy of Production** — Staging is where automated tests run and where data scientists hold read access, so a full copy would mean the cheapest route to production data runs through the less-defended of the two accounts, and would double the storage and Macie bills for the privilege. **No VPC peering to Staging**, deliberately: Sandbox↔Production peering exists because the VPN has to reach GitLab, and nothing in Staging needs VPC-level reach from a laptop — the read access in D18 is data plane (S3, Athena, CloudWatch Logs) over public AWS API endpoints through the tunnel. A second peering would buy route-table complexity and one more hand-driven path into an account whose entire value is that nobody touches it by hand. Add it if something concrete needs it, not before. **OU shape:** `Workloads` with `Staging` and `Production` as children, so the SCP set meaning "no interactive compute, no human control plane" is written once and attached once; Sandbox keeps its own OU, because interactive compute is the whole point there. Not to be confused with a **Policy Staging OU** (§11), which is for testing SCPs before they reach anything real — the names collide, the concepts do not. **Cost:** one more AWS Config recorder (~USD 0.50-1/month) and one more KMS key; the VPC layer is free at rest and the metered `egress/` slice exists only while a promotion runs, which is minutes. The floor moves from ~USD 18-22 to ~USD 19-24 (§5), still comfortably under D12. Staging is never up during an ordinary Sandbox session: `make up ENV=staging` is a pipeline step, not part of a lab session. **Revised 2026-08-08 (D21):** the chain now starts in Development, not Sandbox — Development → Staging → Production; "a seventh account" reflects the count at the time of the decision, since superseded by D21/D22. |
| D21 | The Development account, and where experimentation ends | Decided (2026-08-08): **a dedicated Development account; Sandbox becomes pure experimentation; the promotion chain starts in Development** | The distinction the AWS MLOps roadmap draws and the previous revision collapsed "because there is one user": **Experimentation (Sandbox)** is where the unit of work is a *notebook* — no versioning expectation, nothing survives, cost is spasmodic and human-driven. **Development** is where the unit of work is a *pipeline* — a repository with tests, a SageMaker Pipeline, git, CI, the expectation that running it again on Tuesday gives the same answer. The user chose to build the boundary anyway, and it buys three real things even single-operator: (i) **the promotion chain gets an honest origin** — what enters CI from Development is already repository-shaped, so the pipeline never has to pretend a notebook is an artifact; (ii) **the graduation step becomes visible** — moving work from Sandbox to Development is a deliberate act (a git commit into a Development repository), not a gradual blurring inside one account; (iii) **cost attribution separates exploration from engineering**, which is the split a real budget conversation needs. **What Development is:** a second Interactive-OU account — Studio domain (VPC-only, same module as Sandbox), derived zone (D19), LF read share from the lake (D22), peering to Production for GitLab, and the place SageMaker Pipelines are *authored and test-run* before the pipeline promotes them. **What it is not:** a deployment target (humans work here interactively) and not a staging area (its runs prove the pipeline works, not that the artifact deploys). **Graduation Sandbox → Development is git, not a pipeline:** a notebook's logic is rewritten into the repository, reviewed, and committed — there is deliberately no automated path that lifts a notebook out of Sandbox, because the rewrite *is* the quality gate. Promotion is Development → Staging → Production and never starts in Sandbox. |
| D22 | The Data Governance account — state separated from compute | Decided (2026-08-08): **the governed lake moves out of the environment accounts into a dedicated Data Governance account; every environment reaches it through Lake Formation cross-account shares** | Environments (dev/staging/prod) sit on the *lifecycle* axis: how mature and protected a given copy of the application is. Data ownership sits on a different axis entirely: who produces a dataset, answers for its quality and sets its access policy. The lake outlives every application that reads it, so tying it to any environment account ties the data's life to a deployable thing's life — and forces a copy per environment. **What lives here:** the raw and curated S3 buckets (Iceberg), the Glue Data Catalog, Lake Formation with the LF-Tags and the D13 registrations, the classification scheme, the ingestion drop-box (D18), and Macie's primary scan scope (Stage 11). **What never lives here:** compute. No VPC in the first build — the data plane (S3, Glue, Athena, LF) is serverless, and consumers reach it through their *own* VPC endpoints; the SCP on the `Data` OU denies EC2 and SageMaker outright, and deletion protection is the policy set's whole personality (no `s3:DeleteBucket`, Object Lock where retention warrants it). **Who touches it:** nobody, interactively (D18). Sandbox and Development hold LF **read** shares; Production's job execution role holds LF read *and* the **governed write** — the producer path: production ETL writes curated tables through LF-aware engines, cross-account, and that is the only way governed data is ever written. Staging is deliberately not on the share (D20 — its data is sampled or synthetic, local to it). **What this closes and what it opens:** it closes the §11 row "the lab conflates environment with data domain", makes D13 cleaner (the execution roles in the environment accounts hold no S3 access at all to lake buckets — the accounts do not even contain them), and centralises what Macie scans. It opens more cross-account wiring: every row of §4.4 that involved "Production's lake" now points at Data Governance, and the LF share count goes from one to three. One domain, one team still — but now the mechanism is exercised in the shape it scales in. |
| D23 | OU structure — the account is the isolation boundary, the OU is the policy boundary | Decided (2026-08-08): **four OUs, each defined by the policy set it carries: Security, Interactive, Data, Workloads** | Segregating "by OU" versus "by account" is a false choice — accounts isolate (blast radius, quotas, billing, credentials), OUs attach policy once so it is inherited rather than remembered. An OU therefore earns its existence exactly when two or more accounts need the same policy set, and the OUs here are named for their policy, not for their contents: **Security** (Log Archive, Audit, Identity — Control Tower's guardrails plus delegated administration), **Interactive** (Sandbox, Development — interactive compute *allowed*, human infrastructure changes denied), **Data** (Data Governance — no *user* compute, with the two named carve-outs D26 and D27 add, deletion denied), **Workloads** (Staging, Production — no interactive compute, no human control plane; the D20 SCP set unchanged). A per-environment OU tree (one OU per account) was considered and rejected: an OU holding exactly one account forever is a folder with one file — policy might as well attach to the account. The revision triggers are recorded here so the structure is revisited deliberately: a second production-like account → nest `Workloads` into `NonProd`/`Prod`; the first time Staging and Production need genuinely different policy → the same; a second data domain → the `Data` OU stops being a single-account OU by itself. And one OU is still notably absent, unchanged from before: a **Policy Staging OU** for testing SCPs before they attach to anything real (§11) — the name collides with the Staging *account*, the concepts do not. |
| D24 | Where the shared filesystem lives, now that there are two Studio domains | Decided (2026-08-08): **EFS in Sandbox only; there is no shared filesystem in Development and no network path to Sandbox's** | D21 created a second Studio domain, and the NFS requirement in `CLAUDE.md` ("exchange files between users, the SageMaker environment and S3 buckets") did not automatically follow it. Three options were on the table: a second EFS in Development, a Sandbox↔Development VPC peering carrying NFS, or leaving the filesystem where it is. **The choice is the third**, and the reason it is a decision rather than an omission is that the alternatives each buy something real and are being declined on purpose. A second EFS costs cents but doubles a stateful `[P]` resource and creates the question nobody wants to answer at 23:00 — *which* of the two copies of a file is current. A peering would be the first network path between the two Interactive accounts, built for file convenience rather than for a requirement, and it would weaken the property that graduation is a *rewrite* (D21) by making it possible to simply drag files across. **What this means in practice:** the NFS requirement is served in Sandbox, which is where the VPN terminates and where the human file-exchange use case actually is. The exchange between Sandbox and Development is **S3 and git**, which is the same path the graduation itself takes — the rewrite passes through a repository either way. **Revision trigger:** the first time a Development workflow genuinely needs a POSIX filesystem (a training job that will not read from S3, a tool that mmaps), build the second EFS in `development/nfs/` from the Stage 5 module rather than reaching for the peering. Recorded in §11 as a lab-scale compromise: an institution gives every interactive account its own home and scratch filesystem and does not ask people to think about which account their files are in. |
| D25 | Who consumes the ingestion drop-box | Decided (2026-08-08): **the Production job execution role, on the producer path; the `Data` OU SCP is tightened so no compute can run in Data Governance at all** | D18 put an ingestion drop-box in the Data Governance account (`s3:PutObject` from the Interactive-OU roles into a dated prefix, no read, no list, no delete) and said "a pipeline picks up from it" — without naming the account that pipeline runs in. There is only one answer consistent with D22: **Production**, because Production's job role already holds the Lake Formation governed write, and ingestion is exactly the producer path applied to a file a human dropped rather than to an upstream feed. Data Governance cannot host it — the `Data` OU exists to make "nothing runs here" structural. **Two consequences to build rather than assume.** (i) The drop-box bucket policy needs a *second* statement, granting the Production job role `GetObject`, `ListBucket` on the dated prefixes and `DeleteObject` (the pickup has to consume what it read, or the letterbox never empties) — plus a grant on the drop-box KMS key, which is the half that is forgotten until the `AccessDenied` arrives. §4.4 row 10 carries it. (ii) The `Data` OU SCP as drafted in Stage 1 denies `ec2:RunInstances`, `sagemaker:Create*`, `glue:CreateDevEndpoint` and ECS/Lambda creation, but **not `glue:CreateJob`/`StartJobRun`** — a gap wide enough to run the whole ingestion in the wrong account by accident. Add Glue job creation and execution to the deny, so the SCP means what the OU's name promises. **The asymmetry is deliberate and worth stating:** the data scientist can put a file into the lake account but cannot read it back, and the thing that reads it runs behind the approval gate. That is what keeps the drop-box from becoming the general-purpose exchange bucket D18 refuses to build. **Revised 2026-08-08 (D26, D27):** "no compute at all" is now "no *user* compute". Two carve-outs were added by name, and the distinction between them is the useful part — `datazone:*` because a governance control plane is not compute (D26), and the crawler/optimizer actions under the catalog-maintenance role because they *are* compute and therefore need a bounded principal, an event trigger and an alarm (D27). The deny list in this decision is otherwise unchanged, Glue jobs included. |
| D26 | The development experience: SageMaker Unified Studio, and where its domain lives | Decided (2026-08-08): **one SageMaker unified domain — a DataZone V2 domain — in the Data Governance account (renamed from Data Management in the same decision), with account associations to Sandbox and Development; the two classic per-account Studio domains are dropped** | Reverses the Stage 6 note that recorded Unified Studio as deliberately not used. Two of that note's three reasons expired: **official Terraform support arrived in 2026-07** — the `aws-ia/terraform-aws-sagemaker-unified-studio` module provisions the domain and its IAM through the `aws` provider (≥ 6.51) and project profiles, blueprints and projects through **`awscc`** (Cloud Control, ≥ 1.89) — and SageMaker Catalog supplies exactly the publish/subscribe governance layer §11 said only an institution would have. What survives of the old argument is the *order of construction*: the Glue + LF-Tags substrate is still built first and by hand (Stage 5), so the portal is a storey, not the foundation. **Where the domain lives, and why it is not Development.** A first draft of this decision put it in Development and that was wrong in a specific way this plan has been wrong before (the `staging` Glue namespace inside Production, D20): it placed a resource from the **ownership** axis inside an account on the **lifecycle** axis. AWS's own multi-account guidance is a governance-first one — the *Governance account* hosts the domain, its users, account associations, project profiles, projects, Git connections and SageMaker Catalog. This project already has that account; what it lacked was the name. So `Data Management` becomes **`Data Governance`** and takes the domain, which also buys a mechanical gain: DataZone fulfils an approved subscription by **writing a Lake Formation grant**, so co-locating the business catalog with the technical catalog makes every approval local rather than cross-account. **The domain is a registry, not a runtime** — this is the sentence that keeps D17 and D21 intact. It holds projects, profiles, blueprints, memberships and the catalog; it holds no notebook, app, job or project bucket. Blueprints provision into the *associated* accounts, chosen by the project profile: an **`experimentation`** profile provisioning into **Sandbox** (the unit of work is a notebook), an **`engineering`** profile provisioning into **Development** (the unit of work is a pipeline). The Sandbox/Development boundary is therefore not weakened but *strengthened* — it stops depending on which URL a person opens and becomes a property of the project. The D21 graduation is unchanged: the move of code between the two projects' git repositories. **Staging and Production are never associated** — deployment targets stay headless, and D28 defines what crosses instead. **Blueprints enabled and no others:** Tooling; **Lakehouse Catalog in its Glue/Athena form — not the Redshift Serverless variant**, whose per-query RPU minimum has no place under D12; and **ML experience**, whose per-project SageMaker AI domain is where the Stage 6 VPC-only and IAM-condition hardening now applies. **Consequences in the Data OU.** Its policy set becomes "no *user* compute" rather than "no compute at all": `datazone:*` is carved out as a control plane, in the same sense Lake Formation always was, alongside D27's genuine-compute carve-out for crawlers. And the account still has no VPC, so a CodeConnections host cannot reach the private GitLab from here — §4.4 row 13 falls to its manual-push fallback, accepted rather than paid for with a VPC and a peering. **Authentication** is Identity Center — **the domain must be created in IdC's home Region; verify before creating, since neither can move**. **Cost:** DataZone metadata is request- and storage-priced (`PRICING.md`) — cents at lab scale; the cost lever is which blueprints exist, not the domain. **Revision trigger:** if the domain/portal model fights the lab (IdC region coupling, blueprint rigidity, a portal outage blocking all work), the classic two-domain Stage 6 design is in git history and rebuilds from the same substrate. |
| D27 | Catalog-maintenance compute in the Data OU: crawlers and optimizers | Decided (2026-08-08): **Glue Crawlers for the raw zone and the ingestion drop-box run in Data Governance, under a named catalog-maintenance exception to the Data OU SCP; no crawler ever points at an Iceberg table** | The 2026-08-08 revision asks for crawlers on the data-lake buckets; D25 had just tightened the Data OU SCP to deny all Glue compute. The collision is resolved by distinguishing **user compute** (ETL jobs, dev endpoints, notebooks, interactive sessions — still denied, no exception) from **the catalog's own maintenance** (crawlers, Iceberg compaction/table optimizers, column statistics — allowed, startable only by the lake's maintenance role, which is not assumable interactively). The exception must be *named*, not smuggled: a crawler samples object contents to infer schema, so it does read data — the honest statement is "no compute here **except** the bounded set that produces catalog metadata, under one role, alarmed". **Scope:** crawlers only where schema arrives from outside — the raw zone and the drop-box, where files land whose shape nobody declared. **Never on Iceberg tables**: Iceberg is catalog-native; a crawler would at best duplicate what the catalog already knows and at worst fight the table's own metadata. **Trigger:** EventBridge on drop-box object creation, or on demand before a pickup run (D25) — never a standing schedule; a crawler run bills per DPU-hour with a 10-minute minimum, so cron-always would out-cost the storage it catalogs. **SCP mechanics:** the deny list from D25 stays; add a condition carve-out for `glue:StartCrawler`/`CreateCrawler` and the table-optimizer/statistics actions when the principal is the maintenance role. |
| D28 | The production workflow contract: what must exist for a scientist-authored workflow to deploy | Decided (2026-08-08): **Production runs workflows headless — no domain, no portal, no blueprint ever touches a deployment target. The pipeline creates, from the application repository, exactly six artifact classes** | The question D26 forces: the workflow is authored in the unified domain (Development), Production has no domain (D17) — so what crosses the gate? **The project's git repository is the promotion vehicle**, and the deployable set is: **(1)** the container image in Production ECR (D14); **(2)** the **workflow definition** — MWAA Serverless YAML — versioned in the repo, deployed by the pipeline to a versioned S3 prefix in Production; **(3)** a **per-workflow IAM execution role** built from `terraform-modules/iam-role`, holding the LF producer grants it needs (D22/D25) and nothing else — one role per workflow is the Serverless isolation model, and the least-privilege property a provisioned MWAA environment structurally cannot offer; **(4)** the orchestration resource itself: **`awscc_mwaaserverless_workflow`** (D7 alternative A) and/or **`aws_sfn_state_machine` + `aws_scheduler_schedule`** (alternative B); **(5)** an explicit **`aws_cloudwatch_log_group` per workflow** — named, retention set — wired into A's `LoggingConfiguration` and B's state-machine logging, so execution logs are a deliverable rather than an accumulation of default log groups nobody expires; **(6)** for ML, the **model package group** (`aws_sagemaker_model_package_group`, Stage 9) whose resource policy lets the pipeline register and approve versions, Staging read approved ones, and Development read status only (§4.4 rows 4, 7). **Terraform support for (4) verified 2026-08-08:** `AWS::MWAAServerless::Workflow` exists in CloudFormation and the `awscc` provider exposes it as `awscc_mwaaserverless_workflow` — re-verify at Stage 10; fallbacks in order: `aws_cloudformation_stack` wrapping the CFN type, then provisioned MWAA (`aws_mwaa_environment`, `[E]`, with the metadata-database caveat back in force). **What authoring must respect, enforced by a promotion lint in Stage 8's CI:** the workflow YAML references the container by ECR URI and tag, never by anything project-scoped, and no operator may reference a domain resource (project connections, portal-scoped IDs) — a workflow that only runs where the portal exists is not a promotable artifact. §4.4 rows 12-14 carry the integration proofs. |

### 4.1 Region portability

The lab runs in `us-west-2` and **stays there**. A move to São Paulo is hypothetical and is not planned
work — no stage builds towards it, and no migration procedure is maintained here.

What remains is ordinary Terraform hygiene, which costs nothing and is worth doing on its own merits:

| Thing | Rule |
|---|---|
| Region | A single `var.region`, set per environment in `.tfvars`. No `us-west-2` literal in `.tf` files. |
| Availability zones | `data.aws_availability_zones` indexed by position, never `us-west-2a`. |
| AMI IDs | AMI IDs are region-scoped. Resolve through SSM public parameters (e.g. `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`), never a literal `ami-…`. |
| Bucket names | S3 names are globally unique — build them from variables rather than pasting a region in. |

Recorded for reference, from the check on 2026-08-07 and **corrected on 2026-08-08**: `sa-east-1` has
endpoints for almost every service this plan uses — Control Tower, IAM Identity Center, SageMaker (Studio
with `ml.t3.medium`, `ml.g5`, `p5.4xl`), MWAA, Macie, GuardDuty, Security Hub, Lake Formation, Glue,
Athena, EFS, ECR, Client VPN, Network Firewall and Graviton `t4g`. **The exception, missed by the original
check: AWS CodeArtifact is not available in `sa-east-1`** — it exists in thirteen Regions, `us-west-2`
among them, and São Paulo is not one. That is not a price difference, it is a missing component: D14 puts
CodeArtifact in the supply chain and egress design B (D5) depends on it as the *only* package path when
there is no NAT. A move to São Paulo would have to replace it (a self-hosted proxy such as devpi, or
design A only). The rest of the answer to "would anything break in São Paulo?" is no; the remaining
difference is price, **measured rather than guessed on 2026-08-08: roughly 1.5-2.1x**, service by service,
in `PRICING.md`. If a move ever became real, the one genuinely expensive part would be redeploying the
Control Tower landing zone, whose home region is fixed at deployment time.

One cross-region rule is permanent and unrelated to any of this: ACM certificates for CloudFront must live
in `us-east-1` regardless of where the workload runs (relevant only at Stage 13).

### 4.2 Data perimeter

The four DLP controls in D6 are all *inside* the accounts. None of them answers the question a perimeter
answers: **can a credential from this organization move data to somewhere outside it, or can something
outside it read data from here?** AWS publishes a three-axis framework for this, every part of it free, and
it belongs in the landing zone (Stage 1) rather than in the DLP stage:

| Axis | Question it answers | Control | Built in |
|---|---|---|---|
| Trusted identities | Can a principal from outside the organization touch my resources? | Resource policies and **RCPs** with `aws:PrincipalOrgID` | Stage 1 |
| Trusted resources | Can my principals write to resources outside the organization? | **SCPs** with `aws:ResourceOrgID` | Stage 1 |
| Trusted networks | Can my identities reach my resources from outside my networks? | **VPC endpoint policies** and resource policies with `aws:SourceVpce` / `aws:SourceVpc` | Stage 3 |

**Resource Control Policies (RCPs)** are the piece that does the most work here and the piece most easily
missed: applied at the OU or organization root, they set a maximum permission on the *resource* side for
S3, STS, KMS, SQS and Secrets Manager, regardless of what any account-level policy says. An RCP denying S3
access to principals outside the organization is, for the stated goal of preventing data leakage, worth more
than Macie — it removes the path instead of reporting on it afterwards.

The symmetric SCP (`aws:ResourceOrgID`) is what stops the most obvious exfiltration route in a data science
environment: a notebook copying a dataset to a personal S3 bucket in someone else's account. Note the known
gaps to keep in mind rather than assume away: these conditions do not cover every service, presigned URLs
are evaluated under the signer's identity, and any path that leaves through the *application* layer (an
HTTPS POST to an allowlisted site) is D5's problem, not the perimeter's.

**Implementation note:** none of these policies should be written from scratch. The aws-samples
**`data-perimeter-policy-examples`** repository carries reference SCPs, RCPs and endpoint policies with
the service carve-outs (`aws:ViaAWSService`, `aws:PrincipalIsAWSService`) that every one of these
conditions needs. A perimeter without the carve-outs blocks AWS services acting on your behalf — and the
first casualty in this plan would be Athena reading S3 under Lake Formation, i.e. the exact access path
D13 forces everything through (see Stage 5).

### 4.3 The two egress designs (D5)

Rather than pick one mechanism up front, Stage 6 builds both and measures them. They are not variations on
a theme — they answer the "SageMaker should have access to the internet" requirement in `CLAUDE.md` in
opposite ways, and the point of building both is to find out what the strict one actually costs in
day-to-day friction.

**(A) Limited internet — NAT plus allowlist.** The SageMaker private subnets route to the NAT gateway;
Route 53 Resolver DNS Firewall permits an explicit list of domains (PyPI, conda, CRAN, the Julia package
server, crates.io, the distro mirrors, GitLab) and blocks the rest, optionally with a Squid proxy for
HTTP-layer control. Familiar and flexible. Its honest weakness is that DNS-name filtering is bypassable by
connecting to a raw IP, so it is a strong control against accident and a weak one against intent.

**(B) No internet — proxied artifacts only.** The SageMaker subnets have no route to a NAT gateway at all.
Packages arrive through **CodeArtifact** repositories configured with an upstream to the public registry
(CodeArtifact itself fetches from the internet — AWS-side, not through your VPC), container images through
**ECR pull-through cache**, and everything else through VPC endpoints. There is no egress path to misuse,
which is why this is the shape regulated institutions converge on. It also removes the NAT gateway, the
single largest hourly line item in §5 — at the price of the two CodeArtifact interface endpoints
(~USD 0.02/h), still a clear net saving.

**The user's reservation about (B), recorded as a real constraint, not an objection to be argued away:**
this environment must support **Python, Julia, Rust and R**, and CodeArtifact does not cover all of them.
Concretely:

| Ecosystem | CodeArtifact | Fallback if not covered |
|---|---|---|
| Python (PyPI) | Supported | — |
| Rust (Cargo) | Supported — **confirm at Stage 6**, this is a comparatively recent format | `cargo vendor`, or a `panamax` mirror on S3 |
| Julia (Pkg) | **Not supported** | Self-hosted `PkgServer.jl` storage server, or bake into the dev-env image, or allowlist `pkg.julialang.org` |
| R (CRAN) | **Not supported** | Posit Package Manager (commercial), a `miniCRAN` mirror served from S3, or bake into the image |
| OS packages (dnf/apt) | Not applicable | Distro mirror on S3, or bake into the image |

The reframing that makes this tractable: **the dev-env container image is itself the dependency delivery
mechanism.** It is built by a CI pipeline (Stage 8) on a runner that *does* have internet, so Julia, R,
Rust and their package sets are installed at build time and arrive in SageMaker pre-installed. A package
proxy is then only needed for *ad-hoc* installation during exploration — which is mostly Python, which
CodeArtifact does cover. Design (B) therefore does not require solving four ecosystems; it requires solving
one, and making image rebuilds cheap enough that the other three are not painful. Whether that holds in
practice is exactly what Stage 6 is meant to find out.

**Deliverable of the comparison** (Stage 6): a written verdict covering, for each design, the measured
hourly cost, what breaks in a normal working session, how long a "I need package X right now" loop takes,
and what an intentional exfiltration attempt achieves. The plan does not pre-commit to a winner.

### 4.4 Cross-account integrations to prove

The account split (see `README.md`, "Account segregation") is the right call, and it is not free: it turns
several things that are one API call inside a single account into a resource policy, a KMS grant and a RAM
share spanning two. Earlier versions of this plan carried these as "verify this rather than assume" notes
scattered across five stages. Scattered, each one is an evening lost in isolation and re-derived from
nothing. Consolidated, they are a checklist with a stated fallback per row — which is the shape that
survives contact with a Tuesday night.

| # | Integration | Stage | Fallback if it does not work |
|---|---|---|---|
| 1 | Studio custom image pulled from the **Production** ECR (D14) into the Sandbox **and Development** domains | 6 | An ECR cross-account replication rule into a repository in each Interactive account. Not a pipeline |
| 2 | CodeArtifact consumed cross-account from Sandbox and Development — domain policy *and* KMS key policy | 6, 7 | Bake the packages into the dev-env image (§4.3), which is the delivery mechanism anyway |
| 3 | Lake Formation cross-account shares through AWS RAM, now **three** (D22): Data Governance → Sandbox (read), → Development (read), → Production (read + governed write, the producer path) — resource links and `IAMAllowedPrincipals` have version-dependent behaviour, and the *write* grant is the least-travelled variant | 5, 9 | None; instead, prove each grant restricts with the "read it with pandas" test *before* believing it, and prove the write path with a job that writes a curated table cross-account |
| 4 | Model Registry: reading or approving a Production model package group from Development (D17) | 9, 10 | Registration happens only under the pipeline's own Production role; the Development side never writes to the registry |
| 5 | S3 bucket policies (now mostly in **Data Governance**, D22) whose `aws:SourceVpce` condition must admit the endpoints of *every* consuming account — Sandbox, Development, Production — plus the WireGuard Elastic IP (D18). **The IDs must come from the `[P]` S3 gateway endpoints in each consumer's `foundation/`, never from the `[E]` interface endpoints in `egress/`**, whose IDs change on every `make up` — and which now sit in a different account from the policy | 5, 9 | Replace the condition with `aws:SourceVpce ∈ list` **or** `aws:SourceIp = <WireGuard EIP>`, maintained as a variable per consuming account rather than edited by hand; or anchor on `aws:SourceVpc` (the VPC ID, also `[P]`) |
| 6 | Whether S3 **console** browsing survives the `aws:SourceVpce` deny at all — console operations issued by the console backend carry neither the endpoint nor the user's source IP | 9 | Tell users to use the CLI over the tunnel, and write that in `README.md` rather than leaving a broken console as a surprise |
| 7 | **Staging** (D20) consuming Production: pulling the application image from the Production ECR and reading the approved model version from the Production Model Registry, both under the pipeline's Staging role | 8, 9 | Replicate the image into a Staging ECR repository as part of the promotion, and pass the model artifact's S3 URI explicitly instead of resolving it through the registry |
| 8 | The deploy roles assuming **across** accounts — the runner is in Production (D14), so the trust policies run Production → Staging and Production → Production | 8 | None needed; but write the two trust policies as separate roles with separate names, so an audit can tell which one was used |
| 9 | **Development ↔ Production VPC peering** (D21): Studio in Development must reach GitLab in Production to clone and push — the same narrow, per-subnet route shape as the Sandbox peering | 3, 7 | None at the network level; if the second peering proves troublesome, the mirror-to-GitHub policy from Stage 7 step 7 is the interim path for Development commits |
| 10 | **The ingestion drop-box pickup** (D25): the Production job role reading and deleting from a Data Governance prefix that the Interactive-OU roles write to — a bucket policy with two asymmetric statements, plus a grant on the drop-box KMS key | 5, 9 | Have the Interactive-OU roles write to a bucket in Production instead, and accept that the file lands outside the governed account before it is curated. Strictly worse — it puts an ungoverned copy in the deployment target — so treat it as a stopgap, not an alternative |
| 11 | **Organization-wide sharing enablement for Lake Formation** (D22): `ram:EnableSharingWithAwsOrganization`, LF **cross-account version 3 or above** (required to grant to an Organization or an OU rather than to an account list), and `AWSLakeFormationCrossAccountManager` on the Data Governance grantor | 1, 5 | Grant to explicit **account IDs** rather than to the OU, and accept a RAM invitation per share. Three shares accepted by hand, once, is survivable — but the invitations reappear whenever a share is recreated, so it is a tax on every rebuild |
| 12 | **The unified domain's account associations** (D26): the DataZone V2 domain in **Data Governance** associated with **Sandbox and Development** through RAM, and blueprints provisioning project environments into those accounts under their provisioning roles. This is the row that carries the whole D26 shape — if associations do not work, the domain is a catalog with no compute attached | 6 | One V2 domain **per Interactive account**, no associations — losing the single portal and the cross-account project model, but keeping projects, the catalog and the Terraform module. The domain would then sit on the lifecycle axis after all, which D26 rejects on principle, so treat this as a degraded mode rather than a design |
| 13 | **Unified Studio project git ↔ the self-hosted GitLab** (D14, D26): projects attach a repository through CodeConnections, which for self-managed GitLab requires a **CodeConnections host** reaching the instance in Production's private subnet. **Since D26 the domain is in Data Governance, which has no VPC** — so the host has nowhere to attach, and this row is expected to fail rather than merely at risk | 6, 7 | Accepted as the normal path, not as a fallback: the project keeps its default repository and the push into GitLab is a manual `git remote add` + push. The D21 graduation is a rewrite through a repository either way, so what is lost is convenience, not a control. Giving Data Governance a VPC and a peering to buy it back was considered and declined (D26) |
| 14 | **The pipeline creating `awscc_mwaaserverless_workflow` in Production** (D28): the Cloud Control path from the deploy role — verified to exist 2026-08-08, not yet verified to *apply* cleanly under a CI role with a permission boundary | 10 | `aws_cloudformation_stack` wrapping `AWS::MWAAServerless::Workflow`; second fallback, provisioned MWAA (`aws_mwaa_environment`, `[E]`, metadata-database caveat in force — D7) |

Rows 5, 6 and 11 are the ones most likely to surface as an `AccessDenied` — or, in row 11's case, as a
share that appears to have been granted and simply never arrives. Rows 7-10 are the price of real
environment separation: the promotion crosses an account boundary twice, the lake is consumed
cross-account from everywhere (D22), and each crossing is a place where a resource policy can be missing.
Rows 12-14 arrived with D26-D28 and are the Unified Studio set — row 13 is the one with no workaround
that preserves convenience, and row 14 is the one that decides whether D7's alternative A ships in
Terraform or in a wrapper. Check them deliberately rather than by symptom.

---

## 5. Cost model

Because of D11 the relevant question is not "what does this cost per month" but "what is the floor when
nothing is running, and what does an hour of lab time add on top". Order-of-magnitude figures for
`us-west-2`, to be confirmed with the AWS Pricing Calculator before each stage.

**The floor — paid every month even with the lab shut down (~USD 21-27):**

| Item | Approx. USD/month | Note |
|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | 0 | These cost nothing at rest, so there is no reason to destroy them |
| GitLab EBS volume (50 GB gp3) | ~4.00 | Paid while the instance is stopped; this is the price of not rebuilding GitLab |
| Elastic IP for WireGuard | ~3.65 | All public IPv4 addresses are charged hourly, attached or not |
| KMS customer-managed keys (3) | ~3.00 | ~1.00 per key per month |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~2-4.5 | One recorder per governed account — **eight of the nine**, every account except Management (D20-D22); confirm in Stage 1 whether the landing zone also records the Management account. The estimate assumes an idle lab; a heavy `terraform apply` session records a configuration item per resource change and can multiply this. Control Tower allows restricting the recorded resource types — the main cost lever of the landing zone, applied in Stage 1 |
| Route 53 hosted zones (1 private + 1 public, D15) | ~1.00 | The public zone exists only for ACM DNS validation |
| Public domain registration (D15) | ~1.00 | ~USD 12-15/year amortised |
| CodeArtifact | ~0.10 | USD 0.05/GB-month storage plus USD 0.05 per 10k requests; negligible at lab scale |
| Security Hub + IAM Access Analyzer | ~1-2 | Enabled org-wide from Stage 1 (principle 9). Access Analyzer external-access findings are free; Security Hub charges per check and per finding |
| GuardDuty | 0 → ~3-5 | Free for the first 30 days per account, then driven by CloudTrail/VPC flow/DNS log volume. S3 Protection and Malware Protection are extra and are the ones to watch against the ceiling |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |
| EFS (shared filesystem + Studio homes, lifecycle to IA) | ~0.50 | `[P]` — cents at rest, and it buys the removal of the sync-to-S3-on-teardown machinery (§5.1 rule 2) |
| SageMaker unified domain — DataZone V2 metadata (D26) | ~0.50 | Requests USD 10 per 100k, metadata storage USD 0.40/GiB-month, global rates (`PRICING.md`); cents at lab scale. The cost lever is which blueprints exist, not the domain itself |
| Staging, Development and Data Governance accounts at rest (D20-D22) | ~3.00 | ~USD 1 each: a Config recorder and a KMS key per account. VPCs, buckets and IAM roles are free at rest; Staging's metered slice exists only during a promotion, Development's only while someone is working, and Data Governance has no metered slice at all — its data plane is serverless (the lake storage itself is counted in the S3 row above) |
| **Revised floor** | **~USD 21-27** | Up from the ~USD 15 first estimate: mostly from moving the detective controls into the landing zone (principle 9), plus ~USD 3 for the three environment/data accounts added on 2026-08-08. Still under the USD 50 ceiling, with less headroom than before — worth rechecking against the real bill at Stage 12 |

Two cost levers worth applying rather than discovering later:

- **S3 Bucket Keys** on every SSE-KMS bucket. They cut KMS request charges by up to ~99%, and a data
  environment issues a KMS request per object operation — without this, KMS requests can quietly exceed
  the cost of the keys themselves. Free to enable; set it in the `s3-bucket` module from Stage 2.
- **Scope Macie deliberately** (Stage 11). Macie charges per GB inspected for sensitive-data discovery. Run
  it against a sampled prefix, not the whole lake, or it becomes the largest single line item in the
  project. The same caution applies to **CloudTrail S3 data events**, which bill per event: a single Spark
  job listing and reading thousands of objects generates a matching number of events.

**Per hour of lab time — added while the environment is up (~USD 0.25/h):**

| Item | Approx. USD/h |
|---|---|
| NAT Gateway (1) + its public IPv4 | ~0.050 + 0.045/GB processed — **zero under egress design B** (§4.3) |
| Interface VPC endpoints (9, single AZ per D9; 11 under design B) | ~0.090-0.110 (double if spread across 2 AZs) |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| Internal ALB in front of GitLab/Pages (only while GitLab is up) | ~0.023 + LCU usage |
| Production NAT + endpoints (only while runner builds need egress) | ~0.050 + 0.045/GB |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| WireGuard EC2 `t4g.nano` | ~0.004 |
| Sandbox ↔ Production **and** Development ↔ Production VPC peering (two of them, D21) | free within an AZ; USD 0.01/GB each way across AZs — see §9 item 3 |
| **Staging `egress/` during a promotion run** (D20) | ~0.10-0.15/h, but measured in *minutes* per promotion, not hours — `make up ENV=staging` is a pipeline step, and the pipeline tears it down. Budget ~USD 0.03 per promotion, not a standing hourly cost |
| **Development `egress/` + Studio apps** (D21) | Same shape as the Sandbox line items (~0.10-0.15/h endpoints + ~0.05/h per app), but only while pipeline-engineering work is happening. A session is either exploratory (Sandbox up) or engineering (Development up) — running both at once is the exception, so the *typical* hourly burn does not double even though the worst case does |
| EFS, Athena, Glue | usage-based; negligible at lab scale |

The endpoint count rose from 6 to 9 (11 under design B) because the Stage 3 list was incomplete: Studio in
VPC-only mode also needs `sagemaker.studio` and `kms`, and design B adds the two `codeartifact` endpoints.
At ~USD 0.01/h per endpoint per AZ this is the largest hourly item, so the list stays minimal and
single-AZ. The table now also carries the **Production** side — the runners' NAT and the GitLab ALB were
missing from earlier versions of this plan, which undercounted a full-stack hour.

**Projection:** ~USD 23 floor + 20 h/month × ~USD 0.28-0.40 (the upper end is a full-stack hour: GitLab,
its ALB, a runner build and one Interactive environment all running at once) + a handful of promotions at
~USD 0.03 each ≈ **USD 29-31/month**, against the USD 50 ceiling (D12). Staging and Data Governance cost
almost nothing precisely because neither ever has standing compute; the number to watch is whether Sandbox
and Development sessions actually stay disjoint, which is what keeps the hourly line from doubling.
Design B trades the NAT gateway for two CodeArtifact endpoints, so it is the *cheaper* of the two egress
options as well as the stricter one — which is worth knowing before the Stage 6 comparison starts.

**What the ceiling rules out:** always-on GitLab (~USD 60/month on its own), AWS Client VPN
(~USD 73/month, the D4 alternative), Network Firewall (~USD 290/month, option D5c) and an always-on MWAA
environment (~USD 212/month for `mw1.micro`, ~USD 358/month for `mw1.small` — D7 alternative A). Any of
these becomes affordable only as a short, deliberate experiment — which is precisely what the operating
model below is for. **D7 now commits to building MWAA rather than merely documenting it**, and this is the
line it has to respect: the environment is `[E]`, it exists for the length of a comparison run, and at
`mw1.micro` an eight-hour experiment costs ~USD 2.30. **MWAA Serverless** (USD 0.088 per task-hour, no
environment fee) removes the exposure entirely and is therefore the variant to try first. Authoritative
per-unit rates, for both `us-west-2` and `sa-east-1`, are in `PRICING.md`. The same discipline applies
inside the unified domain (D26): the Lakehouse blueprint is enabled in its Glue/Athena form only — its
**Redshift Serverless** variant would put a second, larger query bill on top of Athena's, and it is
excluded by decision, not by omission.

**Guardrail:** AWS Budgets with e-mail alerts must exist before any compute is created (Stage 1).

### 5.1 Operating model: three layers (D11)

The naive reading of "destroy it between sessions" is wrong, because most AWS resources cost nothing at
rest. The rule is **pay nothing while idle**, not **destroy everything**. That splits the environment into
three layers, and every stage must say which layer each of its resources belongs to.

**[P] Persistent — created once, never destroyed.** Free or nearly free at rest, or too slow to rebuild:
the Organization, the nine accounts, Control Tower, Identity Center, SCPs, Terraform state buckets, the
**VPC itself** (VPC, subnets, route tables, internet gateway, security groups, NACLs cost nothing),
Route 53 private zone, IAM roles, KMS keys, S3 data buckets, ECR repositories, budgets and alarms — and
the **SageMaker Studio domain with its user profiles** (a domain at rest bills
nothing; only running apps and home-filesystem GBs do) and the **EFS filesystem** (lifecycle to
Infrequent Access; cents per month at lab scale). Rule 2 below records why those two moved out of `[E]`.

**[D] Dormant — kept, but powered off between sessions.** Stateful services where a rebuild is riskier
than the idle cost: the GitLab EC2 instance and its EBS volume, and the WireGuard instance. `make down`
stops them, `make up` starts them. Idle cost is their EBS volumes (~USD 4.65/month) plus the Elastic IP
that WireGuard re-attaches on start — the address itself is allocated in `[P]`, so it survives even if the
instance is replaced. This is what makes the Stage 7 backup/restore cycle a disaster-recovery procedure
rather than a daily dependency.

**[E] Ephemeral — destroyed at the end of a session.** Everything metered by the hour and rebuildable in
minutes: NAT Gateway, interface VPC endpoints, SageMaker Studio *apps* (the domain stays), the internal
ALB in front of GitLab (an ALB cannot be stopped, only destroyed — it bills ~USD 0.023/h for as long as
it exists), GitLab Runners, both D7 orchestrators (the MWAA environment and the native
EventBridge/Step Functions/Lambda stack), the Stage 13 web tier. **MWAA is the awkward member of this
list** — ~20-30 minutes to create or delete, and a metadata database that holds state nothing else
persists; D7 records what Stage 10 must decide about it.

**Rules this imposes:**

1. Terraform slices are split along these lines. `terraform destroy` of an `[E]` slice must never be able
   to reach a `[P]` resource; persistent buckets get `prevent_destroy` lifecycle blocks.
2. No state lives only inside an `[E]` resource — enforced by construction: the two stateful resources that
   would otherwise be `[E]` are in `[P]` for exactly this reason. An `[E]` EFS would need a
   sync-to-S3-before-teardown step; that sync was the single most likely way to lose real work in
   this design, and at EFS-IA prices (~USD 0.016/GB-month) persistence costs cents. The Studio domain used
   to be `[E]` with an explicit home-filesystem delete in `make down`, because deleting a domain
   **retains** its home EFS by default (`RetentionPolicy` defaults to `Retain`) and every teardown would
   otherwise orphan a billing filesystem; a domain at rest is free, so keeping it removes both the hazard
   and the rebuild. SageMaker Studio home directories remain **scratch** by policy — real work lives in
   GitLab or S3.
3. `make up` and `make down` per environment, in dependency order, and both must be tested. A rebuild that
   only works by hand is a bug.
4. Anything slow or awkward to create — Control Tower, accounts, ACM DNS validation, Identity Center —
   belongs in `[P]` by construction.
5. Keep addresses stable: private DNS names instead of IPs, and a retained Elastic IP for WireGuard, so
   client configs survive a rebuild.
6. Each stage documents its teardown as well as its build, and records the measured rebuild time.
7. The layer assignment is a cost judgement and can change. If a `[D]` service turns out to be cheap to
   rebuild, demote it to `[E]`; if an `[E]` rebuild proves slow or fragile, promote it to `[D]` and pay
   the idle cost.

---

## 6. Conventions (to be applied from Stage 2 onwards)

**Naming:** `<project>-<env>-<component>[-<detail>]`, lowercase with hyphens.
Project prefix: `awsds`. The `<env>` token is one of `sandbox`, `dev`, `data`, `staging`, `prod`, `shared`.
Example: `awsds-sandbox-vpc`, `awsds-data-raw` (the lake lives in Data Governance since D22, so
`awsds-prod-raw-data` would name a bucket that does not exist), `awsds-prod-ecr-dev-env`.

**Mandatory tags on every resource:**
`Project=AWS-DataScience`, `Environment=sandbox|development|data|staging|production|shared`,
`ManagedBy=terraform`, `Owner=<sso-user>`, `CostCenter=<stage>`. (`shared` marks org-level resources — the
identity slice — not a Shared Services account, which D14 decided against. `data` marks the Data
Management account, which is not an environment at all: it sits on the ownership axis, not the lifecycle
one, so cost reports should be able to separate it from every environment.)

**Terraform layout:**

Each slice carries its layer from §5.1: `[P]` persistent, `[D]` dormant (stop/start), `[E]` ephemeral.

```
terraform-live/
├── identity/             # [P] permission sets, groups, assignments - applied with the
│   │                     #     delegated-admin profile (D10); never touches Management
│   └── bootstrap/        # [P] state bucket for the Identity account
├── sandbox/              # EXPERIMENTATION (D21): the unit of work is a notebook
│   ├── bootstrap/        # [P] state bucket for this account (state migrated in, never committed)
│   ├── foundation/       # [P] VPC, subnets, route tables, IGW, security groups, private
│   │                     #     hosted zone, KMS keys, IAM roles, WireGuard Elastic IP,
│   │                     #     peering requester + routes to Production (D14)
│   ├── data/             # [P] scratch + derived-zone buckets (per-principal, D19), Athena
│   │                     #     workgroup, LF resource links to the Data Governance share (D22).
│   │                     #     The lake itself is NOT here - it lives in data-governance/
│   ├── egress/           # [E] NAT gateway, interface VPC endpoints - the metered network.
│   │                     #     Two variants behind a switch: D5(A) with NAT, D5(B) without
│   ├── vpn/              # [D] WireGuard EC2 (stopped, not destroyed)
│   ├── nfs/              # [P] EFS filesystem, mount targets, access points (lifecycle to IA)
│   └── sagemaker/        # [P] blueprint target (D26): the experimentation project's
│                         #     environments are provisioned HERE by the domain in
│                         #     Development; running apps are [E], deleted by make down
├── development/          # DEVELOPMENT (D21): the unit of work is a pipeline
│   ├── bootstrap/        # [P] state bucket for the Development account
│   ├── foundation/       # [P] VPC (own CIDR), KMS, IAM roles, peering requester to
│   │                     #     Production - Studio here must reach GitLab (§4.4 row 9)
│   ├── data/             # [P] scratch + derived zone + Athena workgroup + LF resource
│   │                     #     links, same shape as sandbox/data/
│   ├── egress/           # [E] NAT + endpoints, same D5 switch as sandbox
│   ├── sagemaker/        # [P] blueprint target (D26): the engineering project's
│   │                     #     environments land here, provisioned by the domain in
│   │                     #     data-governance/. No domain of its own. Workflows are
│   │                     #     authored and test-run here before promotion
│   └── app/
│       └── app-etl/      # [E] the application running against Development's own data, applied
│                         #     by hand while it is being engineered (Stage 8 step 2). It is NOT
│                         #     part of the promotion chain - that starts at a git tag and its
│                         #     first target is Staging. No nfs/ slice here, by decision (D24)
├── data-governance/      # THE OWNERSHIP AXIS (D22, D26): state and governance,
│   │                     # never compute. Renamed from data-management/ on 2026-08-08
│   ├── bootstrap/        # [P] state bucket for the Data Governance account
│   ├── data/             # [P] raw/curated S3 (Iceberg), Glue Data Catalog, Lake Formation
│   │                     #     registrations + LF-Tags (D13), ingestion drop-box (D18),
│   │                     #     cross-account shares to sandbox/development/production,
│   │                     #     Glue Crawlers on raw + drop-box under the D27 exception
│   │                     #     (config is free at rest; runs are metered, event-driven)
│   └── governance/       # [P] the SageMaker unified domain (DataZone V2, D26) via the
│                         #     aws-ia module: domain + IAM through the aws provider,
│                         #     project profiles / blueprints / projects through awscc.
│                         #     Account associations to sandbox and development
│                         #     (§4.4 row 12). A registry: blueprints provision compute
│                         #     into those accounts, never into this one.
│                         #     No foundation/ slice: no VPC, no user compute, nothing
│                         #     standing - which is also why §4.4 row 13 has no host
├── staging/              # deployment target (D20): no Studio domain, no Model
│   │                     # Registry of its own, no GitLab
│   ├── bootstrap/        # [P] state bucket for the Staging account
│   ├── foundation/       # [P] VPC, subnets, KMS, IAM roles. No peering, by decision
│   ├── data/             # [P] S3 + Glue catalog mirroring production's schema,
│   │                     #     holding sampled or synthetic data only
│   ├── sagemaker/        # [P] job execution roles only
│   ├── egress/           # [E] NAT + endpoints, applied and destroyed by the
│   │                     #     promotion pipeline - up for minutes, not hours
│   └── app/
│       └── app-etl/      # [E] deployed by the pipeline, torn down after the tests
└── production/
    ├── bootstrap/        # [P]
    ├── foundation/       # [P] VPC etc. + peering accepters for Sandbox AND Development.
    │                     #     Built in Stage 3, because Stage 7 (GitLab) depends on it (D14)
    ├── data/             # [P] ECR, CodeArtifact (D14), application-output buckets, Athena
    │                     #     workgroup, LF resource links + the governed-write grant (D22).
    │                     #     The lake itself lives in data-governance/
    ├── sagemaker/        # [P] Model Registry (model package groups) + the execution role
    │                     #     pipeline-submitted jobs assume. No domain, no user profiles (D17)
    ├── egress/           # [E] NAT, endpoints, internal ALB for GitLab/Pages (ALBs cannot stop)
    ├── tooling/          # [D] GitLab EC2 + EBS (D8, D14) - its ALB lives in egress/ [E]
    ├── runners/          # [E] GitLab Runners (D14)
    ├── orchestration/    # [E] D7 builds two, behind a switch like D5's egress designs:
    │                     #     (A) mwaa-serverless/ - awscc_mwaaserverless_workflow per
    │                     #         app, YAML in S3, per-workflow role + log group (D28)
    │                     #     (B) native/ - aws_scheduler_schedule + aws_sfn_state_machine
    │                     #         + Lambda/Fargate, same log-group discipline
    │                     #     The 20-30-min-create / metadata-DB caveat applies only to
    │                     #     the provisioned-MWAA fallback (§4.4 row 14)
    └── app/
        └── app-etl/      # [E]

terraform-modules/        # reusable: vpc, wireguard, iam-role, ecr-repo, s3-bucket,
                          # step-function, mwaa-serverless-workflow, ...
                          # consumed by git tag, never by branch - a module that moves under a
                          # caller is a broken caller
```

`make down ENV=sandbox` destroys the `[E]` slices in reverse dependency order and stops the `[D]`
instances; `make up ENV=sandbox` starts the `[D]` instances and applies the `[E]` slices; `make status`
reports what is running and the current hourly burn. `[P]` slices are never touched by any of them — they
are applied deliberately, by hand. One `[E]` resource lives outside any slice: running SageMaker Studio
*apps* are created by users, not by Terraform, so `make down` deletes them through the API before
touching the slices.

`ENV=staging` is the one environment a human normally never runs these against: `make up ENV=staging` and
`make down ENV=staging` are steps *inside* the promotion pipeline (Stage 8), which brings Staging up,
deploys, tests, and tears it down again. They still have to work by hand — a rebuild that only works from
CI is the same bug as one that only works by hand — but the expected caller is the pipeline.

**Terraform rules:**

- Pin the provider version and `required_version`. One `providers.tf` per slice.
- Region, AZs and AMIs follow the portability rules in §4.1 — no region literals in `.tf` files.
- Authentication through named SSO profiles, one per Terraform-managed account — `awsds-infra-sandbox`,
  `awsds-infra-dev`, `awsds-infra-data`, `awsds-infra-staging`, `awsds-infra-prod`,
  `awsds-infra-identity` (Stage 1b step 10) — never keys.
- Every slice: `terraform fmt`, `validate` and `plan` must be clean before apply.
- Remote state read across slices through `terraform_remote_state` data sources, never hardcoded IDs.
- Modules are referenced by **git tag**, never by branch, so a module change cannot silently alter an
  existing deployment.

**IAM rules** (these are conventions because they are easy to violate one role at a time):

- Every role that a non-administrator can create or influence carries a **permissions boundary**.
- `iam:PassRole` is never granted unqualified. It is always scoped by `iam:PassedToService` and by resource
  ARN. `PassRole` plus a job-creating API (`sagemaker:CreateTrainingJob` is the relevant one here) is a
  privilege-escalation path: it lets a user run code under any role they are allowed to pass.
- Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now". The starting point of a permission set
  is narrow, because loosening a permission is a five-minute change and tightening one is a negotiation.

---

## 7. Stages

### Stage 0 - Baseline (DONE)

Management account created manually; `aws`, `terraform` and `uv` installed; repository documentation written
and reviewed. Nothing provisioned.

---

### Stage 1 - Organization, accounts and identity (manual, console)

**Objective:** a working AWS Organization with the environment accounts and SSO access, so that everything
after this can be done by Terraform without root credentials.

**Prerequisites:** none outstanding. D1 is decided (`us-west-2`) and all nine account e-mails are in
`secrets/emails.md`.

**Split into two halves, 1a and 1b.** This is the longest stage in the plan and it used to be one
unverifiable block of sixteen manual steps. The split is not cosmetic: **1a ends at a checkable state** —
nine accounts exist, in four OUs, with the root credentials secured and a budget watching them — and it is
the half that is slow, awkward to undo, and worth stopping after. 1b is everything that is fast, reversible
and iterative: identity, policies, detective controls and the organization-wide enablements. If a session
runs out before 1b is finished, the environment is still in a coherent state; if it ran out in the middle of
the old Stage 1, it was not.

---

#### Stage 1a - Landing zone, accounts and OUs

**To execute (all manual, by the user, recorded in `LOG.md`):**

1. Secure the Management account root user: hardware or virtual MFA, strong password, no access keys,
   billing alerts enabled.
2. Create a Budget of **USD 50/month** (D12) with e-mail alerts at 50%/80%/100%. Enable **Cost Anomaly
   Detection** next to it — it is free, and it catches a bad cost *pattern* days before a budget
   threshold trips. Optionally add a budget *action* that attaches a deny-compute SCP at 100% — a
   lab-appropriate emergency brake.
3. Enable AWS Control Tower with `us-west-2` as the home region. It will create the Organization, the
   Log Archive and the Audit accounts (e-mails already in `secrets/emails.md`), and turn on org-wide
   CloudTrail and Config. Note: the home region cannot be changed afterwards without redeploying the
   landing zone.
4. Create the `Sandbox`, `Development`, `Staging`, `Production`, `Data Governance` and `Identity` accounts
   through Account Factory, using the e-mails in `secrets/emails.md`. OUs, per D23 — each named for the
   policy set it carries, not for its contents:
   - `Interactive` OU → `Sandbox` and `Development` (D21). Interactive compute *allowed*; human
     infrastructure changes denied. The only OU into which project blueprints may provision (D26).
   - `Data` OU → `Data Governance` (D22, D26, D27). **No *user* compute** — the SCP denies EC2 and
     SageMaker outright, plus Glue job creation and execution (D25) — and deletion protection is the
     policy set's whole personality. **Two named carve-outs, and the distinction between them is the
     point:** `datazone:*` is permitted because a DataZone domain is a governance *control plane*, in the
     same sense Lake Formation always was — it grants and records, it does not run anyone's code (D26);
     and `glue:CreateCrawler`/`StartCrawler` plus the table-optimizer and column-statistics actions are
     permitted **only when the principal is the lake's catalog-maintenance role** (D27), which *is* real
     compute and is therefore bounded by role, event-driven and alarmed. Anything not on those two lists
     stays denied.
   - `Workloads` OU → `Staging` and `Production` (D20). No interactive compute, no human control plane,
     written once and attached once. This is *not* the "Policy Staging OU" of §11, which is a place to
     test SCPs; the names collide, the concepts do not.
   - `Security` OU → `Identity`, alongside the Log Archive and Audit accounts Control Tower created.

   **These nine accounts are the complete set** — D14 places the tooling in Production rather than in a
   separate Shared Services account, and D20-D22 add the deployment target, the development account and
   the data account the AWS reference architectures describe. §11 records what a larger organization
   would still add beyond them.
   Account creation here is manual through Account Factory; **Account Factory for Terraform (AFT)** is the
   automated equivalent and is deliberately not used — with six accounts to create, once, it is at the
   edge of repaying its setup and still loses (§11).
5. **Break-glass access (D16).** Set up the emergency path in the Management account: hardware or virtual
   MFA, credentials recorded offline (never in this repository, never in `secrets/`), a CloudWatch alarm on
   any use of it, and a documented procedure. Test it once, then leave it alone. Do the same for the
   Management root user's recovery path. **This belongs in 1a and not later**: every policy in 1b is a way
   to lock yourself out of your own organization, and the escape hatch has to predate the hazard.
6. **Centralized root access management.** The organization ends up with eight member accounts — two
   created by Control Tower (Log Archive, Audit) and six by Account Factory — each with its own
   root user and its own recovery e-mail: eight credentials nobody will ever rotate. AWS Organizations can
   remove root credentials from member accounts centrally and perform the few privileged root actions on
   demand. Enable it; this is one console setting that eliminates a whole class of dormant risk.

**Deliverables of 1a:** nine accounts exist, in four OUs; the Management root user is secured and its
break-glass path has been tested once; member-account root credentials are centrally managed; the budget
and Cost Anomaly Detection are live. Nothing here is torn down between sessions, and nothing after this
point can lock you out without a way back in.

---

#### Stage 1b - Identity, policies, detective controls and org-wide enablement

Everything in 1b is fast, reversible and iterative — which is exactly why it is separated from the half
that is not.

1. **Register the Identity account as delegated administrator of IAM Identity Center (D10).** From the
   Management account:
   `aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com`.
   This is reversible (`deregister-delegated-administrator`), so it is a cheap step to get wrong.
   Everything in steps 2 and 3 is then done **from the Identity account**, not from Management.
2. In IAM Identity Center, create the **four** users from `ACCOUNTS_AND_USERS.md` (e-mails in
   `secrets/emails.md`) and the groups `infrastructure`, `data-scientists`, **`deployment-managers`** and
   **`governance-managers`**. Enforce MFA. The two manager groups were one group (`managers`) until
   2026-08-08; they were split because the two approvals they carry sit on different axes and, more to the
   point, because one persona holding both means a single human can write a job that reads restricted
   data, approve its release *and* approve its access to that data — three acts, one signature.
   **Never put the same person in both groups**, even while there is only one human: the moment that
   happens the split is notation again, and nothing in AWS will warn you.
3. Create permission sets: `AdministratorAccess` (infrastructure), `DataScientistAccess` (the Interactive
   OU), `ReadOnlyAccess` (deployment-managers). An earlier draft also created a `DeployApprover` permission
   set; it was
   dropped — the deploy approval gate lives in GitLab (Stage 8), driven by GitLab group membership, and
   consumes no AWS-side permission. Create such a permission set only when something actually consumes it.
   **`GovernanceManagerAccess`, and it is the one shape worth thinking about rather than copying.** The
   governance manager approves who may read data, so their own reach must stop at the *catalog*, not the
   rows: Glue catalog metadata read, Lake Formation LF-Tag and permission administration, DataZone domain
   ownership, Macie findings read — and **no `s3:GetObject` on lake prefixes and no Athena workgroup**. An
   approver who can already read everything is not exercising a control when they approve a subscription.
   This is the only permission set in the plan whose *denials* are the point of it.
   **`DataScientistAccess` does not start as `PowerUserAccess`.** An earlier version of this plan gave it
   `PowerUserAccess` "until Stage 6", which contradicts `ACCOUNTS_AND_USERS.md` ("no permissions to
   perform infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let
   the data scientist create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the
   whole design — for five stages. It starts as: SageMaker Studio use, read/write on the account's scratch
   and derived prefixes, Athena, ECR pull, and nothing else. `AmazonSageMakerFullAccess` is *not* a safe
   starting point either: it grants `s3:*` on any bucket with "sagemaker" in the name plus a broad
   `iam:PassRole`. Attach a permissions boundary and scope `PassRole` per the IAM rules in §6.
   **One set, two targets (D21):** `DataScientistAccess` is assigned on Sandbox *and* Development — the
   two accounts are policy-identical at this level (that is what putting them in one OU asserts), and what
   differs between them is the work, not the permission shape.
   **A second permission set targeting Production (D18)** —
   `DataScientistProdAccess`, and it is a different shape, not a weaker copy: **data plane read, no
   compute, no control plane.** It grants CloudWatch Logs read, Glue catalog metadata read, SageMaker
   job/pipeline/Model Registry *status* read, `s3:GetObject` on named application-output prefixes, and
   Athena on the dedicated workgroup from Stage 9, and nothing else. It denies, explicitly rather than by
   omission: the control plane, `sagemaker:Create*Job`, `sagemaker:CreatePresignedDomainUrl`,
   `glue:StartJobRun` and `lakeformation:GrantPermissions`. GitLab and ECR access (D14) folds into this
   set rather than living as a separate grant. (The ingestion drop-box moved with the lake to Data
   Management, D22 — it is granted by bucket policy to the Interactive-OU roles, not by this set.)
   **And a third, `DataScientistStagingAccess` (D20)** — read-only, with no write of any kind, not even a
   drop-box. Staging exists to be written by the pipeline and read by a human working out why the pipeline
   failed; a staging environment a person can write to stops being evidence of what the pipeline actually
   does. Same denies as the Production set, minus every write grant.
   Assign them: infrastructure → the six Terraform-managed accounts (Sandbox, Development, Data
   Management, Staging, Production, Identity); data-scientists →
   `DataScientistAccess` on Sandbox and Development, `DataScientistStagingAccess` on Staging,
   `DataScientistProdAccess` on Production, **no assignment of any kind on Data Governance** (D18/D22);
   deployment-managers → `ReadOnlyAccess` on Sandbox, Development, Staging and Production (the approval
   itself happens in GitLab), and **nothing on Data Governance** — a release approver has no business in
   the account that grants data access; governance-managers → `GovernanceManagerAccess` on **Data
   Governance only**, which is the mirror image: the one account the deployment manager cannot enter is the
   only one the governance manager can.
   The data scientist gets no access to Identity, Audit or Log Archive.
   Leave Control Tower's own permission sets untouched — editing them causes landing-zone drift.
   These are created by hand here only because Terraform cannot run before SSO login works; Stage 2 moves
   them into `terraform-live/identity/` and imports them.
4. The infrastructure user's assignment **on the Management account itself** has to be created from the
   Management account — the delegated administrator cannot manage assignments targeting Management.
   This is the one identity task that stays there permanently.
5. **Preventive policies.** Attach to the OUs, in this order. They come in tiers, one per OU policy set
    (D23), on top of an organization-root set that applies everywhere:
    - **`Workloads` OU** (D20): deny `sagemaker:CreateDomain`, `sagemaker:CreateUserProfile` and
      `sagemaker:CreatePresignedDomainUrl` — this is what turns D17 from an intention into a control:
      "no Studio outside the Interactive OU" cannot be undone by anyone with a console and a good reason.
    - **`Data` OU** (D22): deny compute creation outright (`ec2:RunInstances`, `sagemaker:Create*`,
      `glue:CreateDevEndpoint`, **`glue:CreateJob` and `glue:StartJobRun`** — added by D25, because the
      original list left a Glue ETL job as a perfectly legal way to run the whole ingestion in the account
      whose entire policy set says nothing runs there — and ECS/Lambda creation), deny `s3:DeleteBucket`
      and `lakeformation:DeregisterResource`. The lake account's SCP is about what can never happen there,
      because nothing is supposed to *run* there at all.
    - **`Interactive` OU** (D21): no extra SageMaker denies — Studio is the point — but the same
      no-infrastructure guardrails as everywhere else. The differences between Sandbox and Development
      are differences of content, not of policy, which is why they share the OU.
    - **SCPs:** deny leaving the organization, deny disabling CloudTrail/Config/GuardDuty, restrict usable
      regions to `us-west-2` — the region SCP must still allow `us-east-1`, because IAM, Organizations,
      Route 53, CloudFront and Support only have endpoints there — and **deny writes to S3 resources
      outside this organization** (`aws:ResourceOrgID`), which is the trusted-resources axis of §4.2 and
      closes the most direct exfiltration route a notebook has. Two more, cheap and load-bearing:
      **deny `iam:CreateUser` and `iam:CreateAccessKey`** — principle 2 ("no IAM Users") is otherwise a
      convention with no enforcement, and break-glass (D16) is unaffected because the Management account
      is exempt from SCPs — and **deny `s3:PutAccountPublicAccessBlock`**, which protects the
      account-level setting enabled below.
    - **RCPs:** deny access to S3, STS, KMS, SQS and Secrets Manager from principals outside the
      organization (`aws:PrincipalOrgID`) — the trusted-identities axis of §4.2.
    - **Tag policies:** standardize the mandatory tags from §6 — with a precision the previous version of
      this plan got wrong: tag policies constrain *tagging operations*, they cannot force a resource to be
      created with tags at all. The forcing function is an SCP with `aws:RequestTag`/`aws:TagKeys`
      conditions on the create actions that matter (EC2, S3, SageMaker). One or the other, or the tags are
      a convention — and conventions do not survive contact with a `terraform apply` at 23:00.
    - **Account-level S3 Block Public Access** in every member account. The module-level block from
      Stage 2 only covers buckets the module creates; the account-level setting is the blanket that also
      covers the bucket someone creates outside it. Protected by the SCP above.
    - **Declarative policies:** enforce IMDSv2 and EC2 public-access defaults org-wide.
    Apply these to a test OU first — an SCP mistake is the fastest way to lock yourself out of your own
    organization, which is what the break-glass path in 1a step 5 exists for.
6. **Detective controls** (principle 9 — these belong to the landing zone, not to Stage 11). The
    *delegation* of each service to the Audit account runs **from the Management account**
    (`enable-organization-admin-account` / `register-delegated-administrator`, one manual console action
    per service — consistent with principle 1); everything after that is done from the Audit account:
    enable org-wide **Security Hub**, **IAM Access Analyzer** (external access, and unused access for
    Stage 12) and **GuardDuty**. Watch the cost of GuardDuty's S3 Protection and Malware
    Protection against D12 — enable the base service now and decide on those two with a real bill in hand.
7. **Make the audit trail tamper-evident:** enable **S3 Object Lock** on the Control Tower Log Archive
    bucket and **CloudTrail log file validation**. An audit log that the compromised party can edit is not
    an audit log. Do this before there is anything worth hiding in it.
8. **Restrict the AWS Config recorder** to the resource types this project actually uses. Config is the
    main recurring cost of the landing zone (§5) and the default records everything, in eight accounts.
9. **Enable organization-wide resource sharing, so the Lake Formation shares of Stage 5 can exist**
    (D22, §4.4 row 11). Three separate settings, none of which announces its absence:
    - **`ram:EnableSharingWithAwsOrganization`** — without it, a Lake Formation grant to another account
      produces an AWS RAM *invitation* that somebody has to accept by hand, and it reappears every time the
      share is recreated. With it, accounts inside the organization receive shares directly.
    - **Lake Formation cross-account version 3 or above**, set in the Data Governance account. Versions
      below 3 cannot grant to an Organization or an OU at all, only to an explicit list of account IDs —
      and this project has three consumers with more implied by every §11 row about scale.
    - The **`AWSLakeFormationCrossAccountManager`** managed policy on the grantor (Data Governance), and
      `ram:AcceptResourceShareInvitation` on the data lake administrator role in each consumer account,
      which is the fallback path if the two settings above are ever unavailable.

    This step is here rather than in Stage 5 because it is organization-level and manual, like everything
    else in this stage. Stage 5 step 7 assumes it and will fail confusingly without it: the grant appears
    to succeed on the producer side and the resource simply never shows up on the consumer side.
10. Configure local SSO profiles: `aws configure sso` for `awsds-infra-sandbox`, `awsds-infra-dev`,
    `awsds-infra-staging`, `awsds-infra-prod`, `awsds-infra-data` and `awsds-infra-identity`.
11. **Check the AZ name-to-ID mapping** across the Sandbox, Development and Production accounts
    (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
    profile). D14 and D21 make this matter for real: both peerings into Production are free within an AZ
    and USD 0.01/GB each way across AZs, so a mismatch has a bill attached. See §9 item 3.

**Deliverables of 1b:** SSO login working; `aws sts get-caller-identity --profile awsds-infra-sandbox`
returns the Sandbox account ID; `aws sso-admin list-instances --profile awsds-infra-identity` returns the
Identity Center instance, which is the proof that the delegation took effect; an attempt to write to an S3
bucket outside the organization is denied, which is the proof that the perimeter is real; and
`aws ram get-resource-share-associations` from the Data Governance profile shows organization sharing
enabled, which is the proof that Stage 5's shares have somewhere to land.

**Blocking questions for the user:** the domain name to register (D15). Not needed to start the stage, but
needed before Stage 7.

**Risks:** Control Tower landing zone deployment takes ~60 minutes and is awkward to undo. Account e-mails
cannot be reused after an account is closed (a closed account holds its e-mail for 90 days) — which is
exactly why D11 keeps accounts in the persistent layer. Everything created in this stage is persistent;
nothing here is torn down between sessions.

**To verify while executing this stage**, because Control Tower's handling of Identity Center has changed
more than once and the plan should not assume: (i) that the delegation coexists with the landing zone
without raising drift; (ii) that the restriction in 1b step 4 is exactly as described — that assignments
targeting the Management account are the *only* thing the delegated administrator cannot manage; and
(iii) that the RCPs and SCPs in 1b step 5 do not conflict with the SCPs Control Tower manages itself, which
is the usual source of "the guardrail I wrote silently does nothing"; (iv) that enabling S3 Object
Lock on the Control Tower-managed Log Archive bucket (1b step 7) does not raise landing-zone drift; and
(v) that the Lake Formation cross-account version can be raised to 3+ in an account that has no lake in it
yet (1b step 9) — if it cannot, that setting moves into Stage 5 and the rest of the step stays here.

---

### Stage 2 - Terraform foundation

**Objective:** the repository can provision infrastructure reproducibly.

**Prerequisites:** Stage 1.

**To execute:**

1. Delete the empty `terraform/` folder; create `terraform-live/` and `terraform-modules/` as in §6.
2. `terraform-live/sandbox/bootstrap/`: S3 state bucket (versioning, SSE-KMS, public access blocked,
   `use_lockfile = true`). Applied once with local state, then the state is migrated into the bucket it
   just created (add the `backend "s3"` block, `terraform init -migrate-state`) — this is the documented
   chicken-and-egg exception. **The state file is never committed**: state carries account IDs and
   resource ARNs, which do not belong in the Git history of a repository hosted on GitHub.
3. Same for `terraform-live/development/bootstrap/`, `terraform-live/data-governance/bootstrap/`,
   `terraform-live/staging/bootstrap/`, `terraform-live/production/bootstrap/` and
   `terraform-live/identity/bootstrap/`. Six state buckets, one per account that Terraform manages —
   no shared state across environments (D3).
4. Migrate every subsequent slice to the remote backend.
5. `terraform-live/identity/`: import the permission sets, groups and assignments created by hand in
   Stage 1, so identity stops being console-managed (D10). Applied with the `awsds-infra-identity`
   profile. `terraform plan` must come back empty after the import — that is the check that the import
   is faithful.
6. Repository hygiene: `.gitignore` for `.terraform/` and `*.tfstate.backup`; `.terraform.lock.hcl` is
   committed on purpose; `pre-commit` with `terraform fmt`, `terraform validate` and `tflint`; and
   **`checkov` as a required gate, not an optional one** — a policy check that can be skipped is a policy
   check that will be skipped on the day it would have mattered.
7. First reusable modules in `terraform-modules/`: `s3-bucket`, `iam-role`, `kms-key`. The `s3-bucket`
   module enables **S3 Bucket Keys** by default (§5) and blocks public access unconditionally; the
   `iam-role` module takes a permissions boundary as a required argument, so omitting one has to be
   deliberate. Tag every module release; callers pin the tag (§6).
8. **Teardown/rebuild tooling (D11).** Each slice declares its layer (`[P]`/`[D]`/`[E]`), and a `Makefile`
   at the repository root exposes `make up ENV=sandbox` / `make down ENV=sandbox`: `down` destroys the
   `[E]` slices in reverse dependency order and stops the `[D]` instances; `up` starts the `[D]` instances
   and applies the `[E]` slices. Both must refuse to touch `[P]` slices. Add `make status` to report what
   is currently running and the estimated hourly burn.
9. **No region literals (§4.1).** `var.region` in every slice, AZs from `data.aws_availability_zones`,
   AMIs from SSM public parameters. A `grep` check in CI that fails on a hardcoded region keeps this
   honest at no cost.
10. Update `README.md` with the repository layout and the AWS resource structure (required by `CLAUDE.md`).

**Deliverables:** `terraform apply` works end-to-end against the Sandbox account using an SSO profile;
the `Makefile` exists with the slice-to-layer table wired up, even though no `[E]` or `[D]` slice exists
yet — `make down` at this point must be a safe no-op, not a command that reaches the `[P]` bootstrap slice.

**Validation:** destroy and re-create a throwaway `[E]` slice to prove reproducibility, and confirm
`make down` leaves `bootstrap/` untouched.

---

### Stage 3 - Networking (Sandbox, **Development, Staging and Production**)

**Objective:** the private networks that everything else sits in.

**Prerequisites:** Stage 2.

**Scope change (D14):** this stage builds the Production VPC as well, not just the Sandbox one. It has
to: GitLab lives in Production (Stage 7) and cannot be built before its network exists. The VPC layer is
free at rest, so there is no cost argument for deferring it, and using the same module for both accounts on
the same day is how the modules get proven.

**Scope change (D20, D21):** and the Staging and Development VPCs, for the same reason applied again.
Staging's `egress/` is applied by the promotion pipeline rather than by a person; Development's is part of
an ordinary working session. Four applications of one module on one day is a better proof of the module
than four applications spread across four stages. **The Data Governance account gets no VPC at all
(D22)** — its data plane is serverless (S3, Glue, Athena, Lake Formation), consumers reach it through
their own VPC endpoints, and an account whose SCP denies compute has nothing to put in a subnet.

**To execute:**

The network is split across two slices per account, because the free half and the metered half have
different lifecycles (§5.1).

*`foundation/` — layer `[P]`, costs nothing at rest, never destroyed:*

1. `terraform-modules/vpc/`: VPC (`10.20.0.0/16` sandbox, `10.30.0.0/16` production, `10.40.0.0/16`
   staging, `10.50.0.0/16` development), 2 AZs, public + private + isolated (data) subnets. Applied to
   **all four** accounts. The ranges are non-overlapping even where no peering is planned — Staging is
   deliberately not peered (D20), but a CIDR chosen to overlap is a decision that cannot be revisited
   without rebuilding the VPC, and the address space costs nothing.
2. Internet Gateway, route tables, NACLs, baseline security groups.
3. S3 and DynamoDB **gateway** endpoints — these are free, so they live here. Being `[P]` is not incidental:
   their IDs are what the Data Governance bucket policies condition on (Stage 5 step 1), so they must
   survive every `make down`. Export each account's gateway endpoint ID from this slice's outputs, so the
   consumer list is read through `terraform_remote_state` rather than pasted.
4. Route 53 private hosted zone per account (e.g. `sandbox.internal`, `prod.internal`), plus the private
   zone that resolves the D15 public domain names to internal addresses (split-horizon DNS).
5. VPC Flow Logs to CloudWatch Logs with a short retention (a few days — retention is what costs).
6. **Sandbox ↔ Production VPC peering.** The requester lives in `sandbox/foundation/`, the accepter in
   `production/foundation/` (a provider alias, cross-account). Routes are added **per subnet, not per VPC**:
   the Sandbox private subnets reach only the Production subnet holding GitLab and the endpoints, and
   security groups reference the peer CIDR explicitly. Peering is a network path between an account where
   people experiment and the account that runs production — it earns a narrow route table, not a
   convenient one. This is also the path the VPN uses to reach GitLab (Stage 4).
   **Development ↔ Production peering as well (D21, §4.4 row 9), same shape:** Studio in Development must
   clone from and push to GitLab, so `development/foundation/` carries a second requester and
   `production/foundation/` a second accepter — the same narrow per-subnet routes, reaching only the
   GitLab subnet. Production now accepts two peerings and nothing else.
   **There is no peering to Staging from anywhere, and that is a decision rather than an omission (D20).**
   The two peerings into Production exist for one concrete reason — GitLab has to be reachable at the VPC
   level. Nothing in Staging needs that: the data scientists' read access there (D18) is data plane —
   S3, Athena, CloudWatch Logs — which reaches public AWS API endpoints through the tunnel, not through a
   peering. Building a third peering anyway would buy route-table complexity and one more hand-driven
   path into an account whose whole value is that nobody touches it by hand. Record it here so that the
   day something genuinely needs it, the question is reopened deliberately.

*`egress/` — layer `[E]`, destroyed at the end of every session:*

7. NAT Gateway — a single one, with a documented switch for one-per-AZ. **Built behind the D5 switch:**
   under egress design B (§4.3) the SageMaker subnets get no NAT route at all, so this resource is
   conditional, not assumed.
8. Interface VPC endpoints, added on demand per stage. The working list, corrected — the previous version
   of this plan was missing three that Studio and D5(B) require:
   `sts`, `logs`, `ecr.api`, `ecr.dkr`, `sagemaker.api`, `sagemaker.runtime`, **`sagemaker.studio`**
   (required for JupyterLab/CodeEditor apps in a VPC-only domain — Studio simply does not work without
   it), `elasticfilesystem`, **`kms`**, and under D5(B) **`codeartifact.api`** and
   **`codeartifact.repositories`**. Default to a single AZ during lab sessions (D9) — at ~USD 0.01/h per
   endpoint per AZ, two AZs doubles the largest hourly line item. A resource in the other AZ still resolves
   the endpoint DNS and reaches it; the cost is cross-AZ traffic and the loss of AZ redundancy, neither of
   which matters in a lab.
9. **Endpoint policies — the trusted-networks axis of §4.2.** Every interface and gateway endpoint carries
   a policy restricting it to resources within the organization (`aws:PrincipalOrgID` / `aws:ResourceOrgID`).
   Without this, the S3 gateway endpoint is a private, unlogged, unmetered path to *any* bucket on the
   internet, including someone's personal one — which is the exact failure mode the whole DLP objective is
   about. Free. Take the policy shapes from the `data-perimeter-policy-examples` repository (§4.2) rather
   than writing them by hand — the service carve-outs are the part everyone forgets.
10. Keep this slice's route-table associations parameterised, so D5 (Stage 6) can insert a firewall or
    proxy into the egress path, or remove it entirely under design B, without reshaping the foundation.

**Deliverables:** all four VPCs applied by Terraform from the same module; flow logs visible; endpoints
resolving privately; both peerings reachable in the intended direction and *not* reachable outside the
permitted subnets; **Staging unreachable from any other VPC at the network level** — the proof that the
missing peering is missing on purpose; an attempt to reach an out-of-organization S3 bucket through the
gateway endpoint denied; and `make down` followed by `make up` restoring egress without touching any VPC.

**Cost note:** this is where the metered bill starts, and `egress/` is the single biggest hourly cost of the
lab: ~USD 0.14/h with 9 endpoints and a NAT in one AZ; ~USD 0.11/h under design B — no NAT, but the two
CodeArtifact endpoints bring the count to 11. Keep the endpoint list minimal — every entry is a permanent
hourly charge for the whole session.

---

### Stage 4 - VPN access

**Objective:** the only human path into the private network.

**Prerequisites:** Stage 3. D4 is decided: self-managed WireGuard.

**To execute:**

1. `terraform-modules/wireguard/`: `t4g.nano` (ARM, Amazon Linux 2023) in a public subnet, WireGuard
   installed and configured by user data, IP forwarding and NAT (masquerade) enabled. **NAT is not
   optional** — a correction to the previous version, which mixed a NAT model with a routed one: VPC
   peering does no edge-to-edge routing and only forwards packets whose source and destination sit inside
   the two VPCs' CIDRs, so the WireGuard client range can never cross the peering to Production. Every
   packet the instance forwards must carry its own private IP, which also means security groups admit the
   WireGuard instance's SG (referencing a peer VPC's security group works across a same-region peering),
   never the client CIDR.
   Layer `[D]`: the instance is **stopped** between sessions, not destroyed (~USD 0.65/month of EBS),
   which keeps the host key and the peer configuration stable.
2. Elastic IP allocated in the `[P]` foundation slice and re-associated on start, so the endpoint address
   survives a teardown and client configs never have to be regenerated. ~USD 3.65/month — the price of not
   editing every client config on every rebuild.
3. Security group allowing only UDP/51820 inbound; SSH access only through SSM Session Manager, never
   port 22 from the internet.
4. Peer public keys supplied through a git-ignored `.tfvars` (keys are generated on the client and the
   private key never leaves the laptop). One peer per person and per device.
5. **Full tunnel, not split** — a correction to the previous version, forced by step 8: the client routes
   `0.0.0.0/0` through WireGuard, so AWS API and console traffic exits through the instance's Elastic IP
   and the `aws:SourceIp` condition can match it. A split tunnel routing only the two VPC CIDRs would
   leave every API call on the laptop's own connection — and step 8 would then deny the user everything,
   tunnel up or not. The cost of full tunnel is that ordinary browsing also transits the instance and
   bills as EC2 data transfer out (~USD 0.09/GB): connect for lab sessions, not as an always-on VPN.
   Reaching GitLab in Production still works through the Stage 3 peering (NATed by step 1). `DNS` in the
   client config points at the VPC resolver (`.2` of the Sandbox VPC CIDR) so private hosted zones and
   VPC endpoints resolve.
6. No return routes for the WireGuard peer network exist anywhere — with NAT on the instance (step 1) the
   VPCs only ever see the instance's private IP, and across the peering such a route would be dropped
   anyway (edge-to-edge, again). What is actually needed: Production's route back to the **Sandbox VPC
   CIDR** through the peering (already built in Stage 3), and security groups on GitLab, EFS and the
   endpoints that admit the WireGuard instance's SG or IP.
7. CloudWatch agent shipping the WireGuard handshake log; alarm if the instance is unhealthy.
8. **Close the other half of the objective: restrict the AWS control plane to the VPN.** `CLAUDE.md` says
   "all user access to the cloud infrastructure will be performed through a VPN", and a tunnel to the VPC
   only delivers the data plane — the console and the AWS APIs remain reachable from any network in the
   world with a valid SSO session. Add a deny with `NotIpAddress` on the WireGuard Elastic IP **combined
   with `aws:ViaAWSService: false`** to the permission sets in `terraform-live/identity/` — the second
   condition is not optional: services calling on the user's behalf (Athena reaching S3 is this plan's
   first casualty) do not carry the user's source IP, and a bare `aws:SourceIp` deny breaks them. Add the
   same condition pair on `sagemaker:CreatePresignedDomainUrl` so a Studio URL cannot even be minted from
   outside the tunnel. This restriction is what step 5's full tunnel exists for.
   Two cautions, both of which have locked people out before: apply it to the `data-scientists` and
   `deployment-managers` and `governance-managers` permission sets first and to `AdministratorAccess` only once it demonstrably works, and note
   that this pins access to a single Elastic IP — which is precisely why that IP lives in `[P]` (D4).
   Break-glass (D16) is the way out if this goes wrong.
9. Write the client setup instructions in `README.md`, including how to regenerate the config after a
   rebuild.

**Deliverables:** connecting from the laptop gives private access to a test resource in the Sandbox
**and Production** VPCs — the only two the tunnel reaches at the VPC level. The laptop has **no route into
the Development or Staging VPCs, by design**, and that is not a gap: both are used entirely through AWS
API endpoints, which the full tunnel already sends out through the WireGuard Elastic IP (§3, "How a human
actually reaches each account"). For Development specifically, that means Studio is opened by calling
`CreatePresignedDomainUrl` and following the returned URL — a public SageMaker endpoint, reached from the
tunnel's IP, and `VpcOnly` does not change that because it governs how the *app containers* reach the
network, not how the browser reaches the UI. So the deliverable to demonstrate here is **Studio in
Development opening with the tunnel up and refusing to open with it down** — which is the `aws:SourceIp`
condition of step 8 doing its job, not a network route. The Sandbox and Production test resources are
unreachable with the tunnel down; an AWS API call with the tunnel
down is denied for the data scientist **and the same call with the tunnel up succeeds** — the pair that
proves the full-tunnel/`aws:SourceIp` wiring; `make down` followed by `make up` restores connectivity
without changing the client configuration.

**Known trade-off (D4):** no Identity Center integration — revoking a person's access means removing their
peer and re-applying. Acceptable for a single-operator lab, and the reason AWS Client VPN stays documented
as the alternative.

---

### Stage 5 - Data foundation (S3, NFS, Glue, Iceberg, Lake Formation)

**Objective:** where data lives and how it is catalogued.

**Prerequisites:** Stage 3.

**Scope change (D22):** the governed lake — buckets, catalog, Lake Formation, classification — is built in
the **Data Governance account** (`terraform-live/data-governance/data/`), not in Sandbox. What the
environment accounts get in this stage is their *consumer* side: LF resource links, an Athena workgroup,
the scratch and derived-zone buckets (D19), and — Sandbox only — the NFS layer. The lake is written once;
the consumer slice is applied twice (Sandbox and Development), which is how the sharing shape gets proven
before Stage 9 repeats it for Production.

**To execute:**

*`data-governance/data/` — layer `[P]`; the KMS CMKs it uses live in the same account:*

1. KMS CMKs per data domain; S3 buckets `raw`, `curated`, `artifacts`, `athena-results`, `logs` with
   versioning, encryption, **S3 Bucket Keys** (§5), lifecycle rules, `prevent_destroy`, and a bucket policy
   that denies access not coming through the VPC endpoint (`aws:SourceVpce`) — the resource-side half of
   the trusted-networks axis in §4.2, complementing the endpoint policies from Stage 3. **The deny must
   carry the `aws:ViaAWSService` carve-out**, or it blocks Athena and Lake Formation vended access — the
   exact path D13 forces all tabular reads through; a bare `aws:SourceVpce` deny makes step 6 unusable.
   Take the policy shape from `data-perimeter-policy-examples` (§4.2). While in the bucket policy, add a
   `s3:signatureAge` cap: it bounds the lifetime of any presigned URL, the preventive counterpart of the
   detection Stage 11 sets up.
   **Write the `aws:SourceVpce` condition as a list from the start, not as a single ID** (§4.4 row 5) —
   and in this account the caller is *never* local (D22): every legitimate reader sits in Sandbox,
   Development or Production, or behind the WireGuard Elastic IP. The list is therefore a per-consumer
   variable from day one: `aws:SourceVpce ∈ [sandbox, development, production endpoints]` **or**
   `aws:SourceIp = <WireGuard EIP>`. Getting this wrong produces an `AccessDenied` with no usable
   diagnostic, in every environment at once.
   **And the endpoint IDs in that list must be the S3 *gateway* endpoints from each consumer's
   `foundation/` slice, never the interface endpoints from `egress/`.** This is the sharp edge D22
   created and it is worth spelling out, because the failure is total and the symptom is mute. Interface
   endpoints live in `egress/`, layer `[E]`: `make down` destroys them and `make up` recreates them with
   **new IDs**. A `[P]` bucket policy pinned to those IDs is stale after the first teardown — and since
   D22 the policy lives in a *different account* from the endpoints, so the `terraform apply` that
   recreates them cannot fix it either. The S3 gateway endpoint is the right anchor on both counts: S3
   traffic goes through it anyway, it is free, and it sits in `foundation/` (`[P]`), so its ID outlives
   every session. `aws:SourceVpc` — the VPC ID, also `[P]` — is the equally valid alternative and is the
   one to prefer if a service ever needs the condition without having a gateway endpoint. Record the
   chosen anchor in the module's variable description, so the next person does not "fix" it by pasting in
   an interface endpoint ID that works until Friday.
   Also here: the **ingestion drop-box** prefix (D18) — `s3:PutObject` granted by bucket policy to the
   Interactive-OU roles, dated prefix, no read, no list, no delete. **Its bucket policy has two asymmetric
   statements, not one** (D25, §4.4 row 10): the writer statement above, and a reader statement granting
   the **Production job execution role** `GetObject`, `ListBucket` on the dated prefixes and
   `DeleteObject`, because a letterbox nobody empties fills up. The Production role also needs a grant on
   the drop-box KMS key — that is the half that is forgotten until the `AccessDenied` arrives, and the
   error text will point at S3, not at KMS. The pickup job itself is built in Stage 9 step 2, on the
   producer path; nothing runs in this account (D25 tightens the `Data` OU SCP so that stays true).
2. **Define the data classification scheme before defining LF-Tags.** LF-Tags are the mechanism; the
   classification is the decision — which levels exist (e.g. public / internal / restricted / personal),
   who owns the assignment, and what each level permits. Writing the tags first produces a taxonomy shaped
   by whatever the first table happened to contain, and Stage 11's Macie findings then have nothing to map
   onto. This is the smallest piece of real data governance in the plan and it costs nothing but thought.
3. Glue Data Catalog databases (`raw`, `curated`). **Glue Crawlers where schema arrives from outside,
   and only there (D27):** one over the raw zone, one over the ingestion drop-box — in this account,
   under the named catalog-maintenance exception to the `Data` OU SCP, startable only by the maintenance
   role. Event-driven (EventBridge on drop-box object creation) or run before a D25 pickup, never on a
   standing schedule: a crawler run bills per DPU-hour with a 10-minute minimum, so cron-always would
   out-cost the storage it catalogs. **No crawler ever points at an Iceberg table** — Iceberg is
   catalog-native, and a crawler would at best duplicate what the catalog already knows.
4. Iceberg tables on S3. **Table maintenance gets an owner on day one**: scheduled `OPTIMIZE`
   (compaction) and `VACUUM` (snapshot expiry) through Athena, or Glue's automatic compaction — an
   Iceberg table nobody compacts degrades quietly and pays storage for every dead snapshot. **Amazon S3
   Tables** — managed Iceberg with automatic maintenance and Lake Formation integration — is the
   AWS-native alternative, deliberately not used here: D13's registered/unregistered prefix split leans
   on general-purpose buckets. Recorded in §11.
5. Enable Lake Formation as the permission model for the catalog; register the S3 locations; apply the
   LF-Tags from step 2.
6. **Implement D13 — make Lake Formation enforceable — which D22 makes structural.** In the old layout
   this required carefully *excluding* the registered prefixes from roles that lived next to them; now the
   environment accounts do not even contain the lake buckets. The SageMaker execution roles and the
   `DataScientistAccess` permission set hold **no S3 permission of any kind on Data Governance buckets**
   (except the drop-box `PutObject`) — tabular access goes through Athena, Glue interactive sessions or
   EMR runtime roles, which ask Lake Formation across the account boundary. This is the step that decides
   whether the fine-grained access control objective in `CLAUDE.md` is a control or a decoration.
   Record any exception through Lake Formation **hybrid access mode** rather than by quietly widening a
   role.
7. **The cross-account shares (D22, §4.4 rows 3 and 11).** **Prerequisite, and it is not optional:**
   Stage 1b step 9 must have enabled `ram:EnableSharingWithAwsOrganization` and raised the Lake Formation
   cross-account version to 3 or above. Without them the grant appears to succeed on this side and the
   resource never appears on the consumer side — which is the least diagnosable failure in the whole plan,
   because nothing errors. Check it first, then grant the catalog read share to the Sandbox and
   Development accounts through Lake Formation/RAM, create the resource links on the consumer side, and
   prove each one with the pandas test *before* Stage 6 builds anything on top. (The Production share,
   including the governed write, waits for Stage 9 — no consumer exists for it yet.)

   **The catalog gains a second storey in Stage 6 (D26):** SageMaker Catalog — the DataZone layer of the
   unified domain — sits on top of this Glue/LF substrate. Publishing an asset and approving a
   subscription happen in the portal, and for managed assets the *fulfilment* of an approval is a Lake
   Formation grant that DataZone writes. Nothing in this stage is replaced by that: the LF-Tags, the
   registrations and the cross-account shares built here are what the portal's approvals resolve to —
   which is why this stage still comes first. **Whose approvals:** the **governance manager**'s. That
   persona also owns the classification scheme from step 2 and the LF-Tag assignments — deliberately the
   same person, because a taxonomy owned by someone who does not answer for the grants is decoration.

*`sandbox/data/` and `development/data/` — the consumer side, layer `[P]`, same module for both:*

8. Per account: the **Athena workgroup** — result bucket local to the account, per-query scan limit, and
   **`EnforceWorkGroupConfiguration = true`** (the setting the console calls "override client-side
   settings"; without it the result location is whatever the client asks for, which makes step 9 a
   suggestion rather than a boundary, D19); LF **resource links** to the shared databases; and the
   scratch buckets.
9. **Build the derived zone deliberately (D19), in each Interactive account.** D13 makes the *entitlement*
   real; it does nothing about what happens after the read, and what happens after the read is that people
   store results — which is the job, not an abuse of it. So the local prefixes get designed rather than
   left over: `…/derived/${aws:userid}/` per principal, so one person's materialised result is not a way
   around another person's grants; a lifecycle expiry (30 days is a reasonable start) so the shadow lake
   does not silently become permanent; `s3:PutObject` scoped to exactly these prefixes on both the
   execution role and the permission sets, never `*`; and the prefixes recorded here as **in scope for
   Macie and for CloudTrail data events** in Stage 11, because this is where sensitive data will actually
   accumulate — *outside* the account Macie primarily watches, which is exactly why the scope has to be
   written down. State the classification rule alongside them: the output of a query over `restricted`
   data is `restricted`. Nothing enforces that automatically at this scale — it is policy, and §11 records
   that a catalog with lineage is what enforces it in an institution.

*`sandbox/nfs/` — layer `[P]`: mount targets are free, and EFS storage with a
lifecycle policy to Infrequent Access is ~USD 0.016/GB-month — cents at lab scale. **Sandbox only, and
that is now a decision rather than an accident (D24):** the file-exchange requirement in `CLAUDE.md` is
about people, the VPN terminates in Sandbox, and Development deliberately gets neither its own EFS nor a
path to this one — the exchange between the two Interactive accounts is S3 and git, the same path
graduation itself takes. Build `development/nfs/` from this module only when a Development workload
genuinely needs POSIX semantics:*

10. EFS filesystem + mount targets in the private subnets, access points per group; this is the NFS layer
   shared between users and SageMaker. Enable the lifecycle policy (transition to IA after 30 days).
   S3 ↔ EFS movement is an explicit copy in code when a dataset needs to cross — no standing
   synchronisation machinery (DataSync would cost per GB moved, and there is no teardown left to protect
   against).
11. **Access from the user's own machine**, which `CLAUDE.md` asks for ("exchange files between users, the
   SageMaker environment and S3"): NFSv4 over the WireGuard tunnel, TCP/2049 allowed from the VPN peer
   CIDR, using the EFS mount helper with TLS. Two caveats to state rather than discover: throughput over a
   VPN is poor enough that this is for exchanging files, not for working off; and **EFS has no mapping
   between POSIX UIDs and SSO identities**, so "who wrote this file" is not auditable. EFS Access Points
   pin a UID/GID per group, which bounds the problem to the group level — good enough for a lab, and named
   in §11 as a real gap for an institution.
12. **S3 is the source of truth for data; the filesystem itself now persists.** An earlier version had the
    EFS `[E]` with a sync-to-S3 step inside `make down` — and correctly called that sync the single most
    likely way to lose real work in this design. Persistence removes the failure mode outright, for cents;
    `make down` does not touch the filesystem at all.

**Deliverables:** a sample Iceberg table written in Data Governance and queried through Athena **from both
Sandbox and Development**, with access granted through the Lake Formation share rather than raw IAM
policies; **a demonstration that the same table cannot be read by pointing pandas at its S3 path from
either account** — which is the only convincing evidence that D13 holds, now with the account boundary
underneath it; **a demonstration that Athena still works with the bucket policy attached** — the evidence
that the `aws:ViaAWSService` carve-out is wired correctly; **a query whose result the client tries to
write outside the derived prefix, and fails to** — the evidence that D19's enforced workgroup
configuration holds; and a `make down`/`make up` cycle that provably leaves EFS content untouched.

---

### Stage 6 - SageMaker Unified Studio (the development experience)

**Objective:** the data scientist's working environment — since the 2026-08-08 revision (D26), one
SageMaker unified domain (DataZone V2) with projects, rather than two classic Studio domains.

**Read this before the steps, because it is the thing most easily misread:** the domain is registered in
**Data Governance**, but *no compute runs there*. A domain is a registry — projects, profiles, blueprints,
memberships, the catalog. The compute lands in whichever account the project profile names, which is
Sandbox for `experimentation` and Development for `engineering`. So this stage builds one resource in the
Data Governance account and provisions working environments into the two Interactive accounts, and the
Sandbox/Development boundary from D21 comes out of it stronger rather than weaker: it stops being "which
URL did the person open" and becomes a property of the project they opened.

**Prerequisites:** Stages 3, 4, 5, and the ECR/CodeArtifact repositories from Stage 7 step 5 — **pulled
forward**, because under egress design B they are how packages arrive, so they cannot come after the thing
that consumes them. **D5 is executed, not decided, in this stage**: both designs get built (§4.3).

**To execute:**

1. **The unified domain (D26), from the official module** — `aws-ia/terraform-aws-sagemaker-unified-studio`
   (`aws` ≥ 6.51 for the domain and its IAM roles, `awscc` ≥ 1.89 for project profiles, blueprints and
   projects): a single **DataZone V2 domain** in the **Data Governance** account
   (`data-governance/governance/`), authenticating through
   Identity Center. **Check before creating anything:** the domain must live in IdC's home Region
   (`us-west-2` if Stage 1 went as planned) — neither can move afterwards. Account associations through
   the org-wide RAM sharing Stage 1b step 9 enabled (§4.4 row 12): **Sandbox** and **Development**;
   **Staging and Production are never associated** (D28). Two project profiles: **`experimentation`**,
   whose blueprints provision into Sandbox (the unit of work is a notebook), and **`engineering`**,
   provisioning into Development (the unit of work is a pipeline) — the D21 graduation is the move of code
   between the two projects' git repositories, unchanged in substance. **The domain account is not a
   provisioning target for anything**: no blueprint is enabled in Data Governance itself, which is what
   keeps the `Data` OU's "no user compute" true while the registry lives there. Blueprints enabled and no
   others:
   **Tooling**; **Lakehouse Catalog in its Glue/Athena form — not the Redshift Serverless variant**
   (D26, D12); and **ML experience**, whose per-project SageMaker AI domain runs in **VPC-only** mode in
   the private subnets with the interface endpoints from Stage 3 — including `sagemaker.studio`, without
   which it will not start. The deployment targets never get a domain or an association: unreviewed code
   must not reach the accounts the split exists to protect, and the SageMaker runtime they carry (Stage 9)
   is submitted to by pipelines, not by people. The escape hatch for "I need to debug a production job
   interactively" is a time-boxed elevated role approved by `deployment-managers`, logged and alarmed — designed in
   Stage 9, not improvised on the night it is first needed.
2. Execution roles per user profile **and per project** (the one-role-per-workflow discipline of D28
   starts here, not in production), honouring **D13**: no `s3:GetObject` on Lake Formation-registered
   prefixes. Map user profiles to the Identity Center users.
3. **Lock down what the notebook can create, not just what the domain can reach.** A VPC-only domain
   constrains Studio itself; it does not constrain training, processing or transform jobs launched from a
   notebook through the API, which accept their own network configuration and will happily run outside the
   VPC. Add IAM conditions to the execution role and the permission set:
   `sagemaker:VpcSubnets` and `sagemaker:VpcSecurityGroupIds` (deny when null), `sagemaker:NetworkIsolation`,
   `sagemaker:InterContainerTrafficEncryption`, `sagemaker:VolumeKmsKey`. Add `sagemaker:InstanceTypes` as
   well: it is the only control that actually stops a USD 30/hour GPU instance from being started by a
   misplaced parameter, and idle-shutdown does not help within the first hour. Without this step, the
   entire VPC-only design is one API call away from being bypassed.
4. **Build egress design A (§4.3):** NAT route plus Route 53 Resolver DNS Firewall with an explicit
   allowlist (PyPI, CRAN, the Julia package server, crates.io, the distro mirrors, the GitLab host).
   Everything else denied and logged.
5. **Build egress design B (§4.3):** the same domain with no NAT route at all; packages from CodeArtifact
   (cross-account from Production, per D14 — a CodeArtifact domain policy grants the Sandbox **and
   Development** accounts) and
   images from ECR pull-through cache. Julia, R and the Rust toolchain arrive pre-installed in the dev-env
   image rather than through a proxy.
6. **Compare them and write the verdict** (the deliverable in §4.3): measured hourly cost, what breaks in a
   normal session, how long the "I need package X right now" loop takes, and what a deliberate
   exfiltration attempt achieves under each. Then choose, and record the choice as the closure of D5.
7. Attach EFS access points for the shared NFS area.
8. Lifecycle configuration for idle shutdown — mandatory cost control.
   **Layers: the domain and its user profiles are `[P]`; only the apps are `[E]`.** A domain at rest bills
   nothing — charges are per running app plus home-filesystem GBs — so destroying it each session would buy
   nothing and would create two problems: the orphaned-home-EFS hazard (the
   `RetentionPolicy` default is `Retain`, so every teardown left a billing filesystem behind unless it was
   deleted explicitly) and the churn of domain ID, user profiles and Identity Center mappings on every
   `make up`. `make down` now deletes running *apps* only and leaves the domain alone. **Studio home
   directories are scratch** by policy: notebooks live in GitLab, data lives in S3, shared files live on
   the Stage 5 EFS — and the home directories stay small, so their storage rounds to cents. State this to
   users explicitly.
9. CloudWatch log groups and metrics for the domain.

**To verify rather than assume** (§4.4 rows 1 and 2 carry these with their fallbacks): whether a Studio
custom image can be pulled from the **Production**
account's ECR (D14) — the BYOI documentation is strict about region and thin on cross-account; if it
fails, the fallback is a native ECR cross-account replication rule into a repository in **each Interactive
account**, not a pipeline. And whether SageMaker Studio offers any supported way to disable file
download or notebook export from the JupyterLab UI. As far as this plan knows it does not, and Stage 11
step 3 should not be written as though the control exists. If it does not, the honest position is that
preventing a determined user from taking data out through their own browser session requires a different
architecture (streaming desktop, or no direct data access at all), and everything else is detection.

**Deliverables:** the data scientist logs in through the VPN, opens the unified portal, works in the
`experimentation` project (compute provisioned in Sandbox) and in the `engineering` project (compute in
Development), installs a package, reads a lake table through Athena over the LF share — surfaced as a
subscribed asset in SageMaker Catalog — writes to EFS (Sandbox), and cannot reach a non-allowlisted site
under design A, nor any site at all under design B; from the `engineering` project, a `git clone` from
GitLab succeeds over the Development↔Production peering (§4.4 row 9 — the *network* path, which is
independent of the CodeConnections attachment in row 13 that D26 accepts losing). Plus the written
comparison of the two egress designs. **And one negative deliverable, recorded as a result rather than
assumed:** nothing was provisioned into the Data Governance account by any blueprint — check it, because
it is the property that keeps the `Data` OU's policy set honest.

**Note on the product direction (revised 2026-08-08, D26):** the first version of this stage built the
classic Studio generation (JupyterLab / Code Editor domains, one per Interactive account) and recorded
Unified Studio as deliberately not used — heavier baseline, less of the mechanics visible. D26 reverses
that: official Terraform support arrived in 2026-07 (the `aws-ia` module), and the governance layer this
plan assembles by hand in Stage 5 is exactly what SageMaker Catalog puts a portal on. What survives of
the old argument is the order of construction — the LF substrate is still built first, by hand, and the
portal is a storey on top of it, not the foundation. The corresponding §11 row is closed. One property
worth restating because it did not change: the portal, like the old Development Studio UI, is a **public
endpoint** controlled by `aws:SourceIp` against the WireGuard Elastic IP (§3) — adopting Unified Studio
neither opens nor closes that path.

---

### Stage 7 - GitLab, Runners and ECR

**Objective:** source control, docs hosting and a container registry, all private, **all in the Production
account** (D14).

**Prerequisites:** Stages 3 (which now builds the Production VPC), 4; decisions D8, D14, D15.

**Note on ordering:** step 5 (ECR and CodeArtifact) is pulled forward and applied before Stage 6, because
under egress design B it is how packages reach SageMaker. The rest of this stage stays here.

**To execute:**

1. GitLab CE Omnibus on EC2 in a **Production** private subnet; EBS with a snapshot schedule; an internal
   ALB in front — **layer `[E]`, in `production/egress/`**, correcting the previous version, which put it
   in the `[D]` tooling slice: an ALB cannot be stopped, it bills (~USD 0.023/h) for as long as it exists,
   so it is destroyed with the session and rebuilt by `make up` (target group, listener and certificate
   attachment are plain Terraform; the private DNS name hides the recreation). Route 53 record in the
   private zone. Reached from the laptop over the VPN through the Stage 3 peering.
   **Layer `[D]` (dormant), decided up front.** GitLab holds real state — repositories, CI history,
   registry metadata — and rebuilding it from a backup on every session is exactly the kind of fragile
   daily dependency §5.1 rule 2 warns about. So the instance and its EBS volume are **stopped**, not
   destroyed: ~USD 4/month idle, ~3-5 minutes to boot. Always-on would be ~USD 60/month, which the
   USD 50 ceiling (D12) rules out.
   Backups are still mandatory, but as disaster recovery rather than routine operation: scheduled
   `gitlab-backup create` to a `[P]` S3 bucket, plus `gitlab-secrets.json` in Secrets Manager — without
   that file a restored backup cannot decrypt its own data. Test the full backup → destroy → restore cycle
   once, so the recovery path is known to work.
   Instance type per D8: `t4g.large` (ARM, 8 GB). Point GitLab's object storage (artifacts, LFS, uploads,
   registry) at S3 rather than at the EBS volume — it keeps the volume small and puts the bulky, valuable
   data in a `[P]` bucket that is versioned and lifecycle-managed.
2. **TLS per D15**, correcting an error in the previous version of this plan: an ACM certificate cannot be
   issued for `sandbox.internal` or any other private-only name, because public certificates require
   public domain validation. Register the chosen domain, keep a public hosted zone for DNS validation only,
   issue a public ACM certificate (wildcard, for Pages), attach it to the **internal** ALB, and resolve the
   names privately. Nothing is published; the public zone contains validation records and nothing else.
3. SAML integration between GitLab and IAM Identity Center, so GitLab has no local accounts. **A caveat
   the previous version missed: SAML *login* works in GitLab CE, but SAML group sync is a paid-tier
   (Premium) feature.** GitLab group membership is therefore maintained by hand — acceptable at three
   users — with group names mirroring the Identity Center groups 1:1, so the Stage 8 approval gate is
   driven by the same identity names and a future upgrade to group sync changes nothing visible.
4. GitLab Pages enabled for documentation, reachable only through the VPN. Pages requires a **domain
   distinct from the GitLab host** (it serves user-supplied content, so sharing the origin would hand it
   the GitLab session cookie) and a **wildcard DNS record plus wildcard certificate** — both provided by
   D15, which is why that decision has to be made before this stage.
5. **Registries, in `production/data/`, layer `[P]` — applied early (before Stage 6):**
   ECR repositories `dev-env` (SageMaker images) and `app/*` (application images), with lifecycle policies
   to expire untagged images and **ECR enhanced scanning** enabled; an **ECR pull-through cache** rule for
   the upstream public registries; and a **CodeArtifact** domain with repositories per ecosystem, each
   configured with an upstream to the public registry. Both carry a resource policy granting the **Sandbox
   and Development** accounts pull/read access, and the KMS key policy has to grant both as well — the
   direction of sharing is the reverse of the previous plan, because the registries moved. §4.3 records
   which ecosystems CodeArtifact does not cover and what happens to them instead. Whether SageMaker Studio
   actually accepts the `dev-env` image cross-account is verified in Stage 6; the fallback is an ECR
   replication rule into a repository in each Interactive account.
6. GitLab Runners in `production/runners/`, layer `[E]`: autoscaling on EC2 or Fargate, in the private
   subnet, with an instance role that can push to ECR. Container builds with Kaniko or BuildKit (no
   privileged Docker-in-Docker). Runners hold no state worth keeping, so they are rebuilt every session.
   The runners need egress to fetch public dependencies while building the dev-env image — that is the one
   place internet access is legitimate under both egress designs, and it belongs to the build account, not
   to the notebook.
7. Decide and document the mirroring policy between this GitHub repository and GitLab.
8. Add GitLab start/stop to `make up` / `make down`, and measure the boot time — if it turns out to be
   much worse than the ~3-5 minutes assumed in D8, revisit the layer choice (§5.1 rule 7).

**Deliverables:** a repository pushed to GitLab over the VPN, a pipeline running on a private runner, an
image in ECR pulled successfully **from both Interactive accounts**, and a docs site served by Pages over
HTTPS with a valid certificate.

---

### Stage 8 - CI/CD pipelines (the three types)

**Objective:** the automation described in `CLAUDE.md`.

**Prerequisites:** Stage 7.

**To execute:**

1. **Development-environment pipeline — and the shared base image underneath it.** This pipeline builds
   *two* images, not one, and the split is what makes the whole promotion story true:
   - **`base`**: the language runtimes and their pinned versions — Python, Julia, R, the Rust toolchain —
     and nothing else. Tagged immutably.
   - **`dev-env`** = `base` + JupyterLab/Code Editor, notebook tooling, the interactive extras. Pushed to
     ECR and registered as a SageMaker custom image / app image config **in both Interactive domains**
     (D21) — same image, same version, both accounts, so Sandbox exploration and Development engineering
     run on the same runtime by construction. Triggered by tags.

   The reason for the split is D17: "promote only the code" is only true if the runtime the code lands on
   is identical to the one it was written against, and the only way to make that true *by construction* is
   a common ancestor image. Two independently built images with the same package list in them are two
   images that will diverge, quietly, at the first rebuild — and the divergence surfaces in production, as
   a version skew nobody changed.
   Under D5(B) this pipeline carries more weight still: it is where Julia, R and the Rust toolchain are
   installed, so it is the dependency delivery mechanism for every ecosystem CodeArtifact does not cover
   (§4.3). Its rebuild time is therefore a usability metric, not just a CI metric — measure it.
2. **Application build pipeline:** the `app-etl` template from `CLAUDE.md` — `uv` for dependencies,
   `pytest` for tests, linting, docs build published to Pages, Docker image pushed to ECR on tag.
   While the application is being engineered it is also applied by hand into
   `terraform-live/development/app/app-etl/`, against Development's own data. That slice is **not** a step
   of the promotion chain — the chain starts at the git tag this pipeline builds from, and its first
   target is Staging — but it is where the Terraform in the application repository gets exercised before
   a pipeline runs it unattended.
   The application image is `FROM base:<pinned tag>` — the same ancestor as `dev-env`, never a base of its
   own and never `FROM dev-env` (the application runtime has no business carrying Jupyter). A build that
   floats the base tag defeats the point of step 1.
3. **Promotion pipeline: Development → Staging → Production (D20, D21).** This replaces what earlier
   versions called the "production deploy pipeline", and the change is structural rather than cosmetic —
   there is a real environment between the tag and production, so the pipeline is a chain with a gate in
   the middle instead of a single deploy with an approval bolted on. The chain starts at a **tag on a
   Development repository** — Sandbox work enters it only by graduating into such a repository through
   git (D21); nothing promotes out of Sandbox directly:
   1. `make up ENV=staging` — apply the Staging `[E]` slices (NAT, endpoints), which exist only for the
      duration of this run;
   2. deploy: `terraform apply` for `terraform-live/staging/app/app-etl/`, pinned to the application tag,
      pulling the image from the Production ECR (§4.4 row 7);
   3. **run the integration tests against Staging data** — the step that justifies the whole account.
      These are not the unit tests from step 2; they are the ones that exercise the deployed artifact
      against a real catalog, real IAM and a real network;
   4. `make down ENV=staging` — tear it back down, so the metered cost is minutes;
   5. **manual approval**, assigned to the `deployment-managers` group, with the Staging test results and the
      Production `terraform plan` attached to it;
   6. promote the image and `terraform apply` for `terraform-live/production/app/app-etl/`.

   A failure at step 3 stops the chain and Production is never touched. That is the property the earlier
   `staging`-namespace-inside-Production stand-in could not provide, because a permission error there
   would have been evaluated against Production's own IAM and would have passed.
   **Two deploy roles, not one:** the runner lives in Production (D14), so it assumes
   `awsds-deploy-staging` for steps 1-4 and `awsds-deploy-prod` for step 6. Separate names on purpose —
   a CloudTrail audit has to be able to tell which one ran (§4.4 row 8).
4. **Credentials for the deploy roles:** no static keys — but **not GitLab OIDC federation either,
   correcting an earlier version**: to validate a job's ID token, IAM/STS fetches the issuer's discovery document
   and JWKS over the public internet, and a VPN-only GitLab (D8/D14) serves neither. The mechanism is a
   **dedicated deploy runner with an EC2 instance profile** — the runner's role *is* the deploy
   credential, no token exchange — locked to protected branches/tags and a protected environment, so an
   ordinary CI job never schedules onto it. OIDC remains the target design if a minimal public surface ever
   exists (exposing only `/.well-known/openid-configuration` and the JWKS path through a public ALB —
   plausible at Stage 13); §11 records it.
   **Note the consequence of D14, now partly softened by D20:** the deploy runner and its *Production*
   target are still in the same account, so no cross-account boundary protects Production from a
   compromised runner. The Staging leg does cross one, which is worth something — a runner compromise now
   has to survive the integration tests and the approval to reach Production, rather than simply reaching
   it. Compensate for the rest with what is available inside one account: deploy roles scoped to the
   `app/*` slices only, `terraform plan` output attached to the approval, and CloudTrail alarms on any use
   of either deploy role outside a pipeline context. §11 records the build/deploy account split an
   institution would use instead.
5. **Security gates in every pipeline:** `checkov` on Terraform, ECR enhanced scanning results blocking a
   promotion on critical findings, and dependency scanning on the application. A gate that only warns is
   documentation, not a gate — decide explicitly which findings block.
6. A pipeline for this infrastructure repository as well: `fmt` / `validate` / `plan` on merge requests,
   `apply` gated by approval. This repository lives on GitHub (§1), so that pipeline is either GitHub
   Actions — with its own OIDC role into AWS; GitHub's issuer *is* public, so federation works there — or
   it runs on the GitLab mirror from Stage 7 step 7. Decide alongside the mirroring policy.

**Note on ordering:** this stage builds the promotion *machinery* — the chain, the gates, the two deploy
roles. The Staging and Production *data platforms* it deploys against are built in Stage 9, so the first
fully meaningful end-to-end promotion happens at the end of that stage, not this one. Until then, exercise
the chain with an application that touches no data; a pipeline proven only against real data is a pipeline
whose failures are ambiguous.

**Deliverables:** a version tag on `app-etl` flows automatically from source through Staging to a running
artifact in Production, with one human approval; **a deliberately broken version fails in Staging and never
reaches Production** — which is the whole point of D20 and the one test that proves the account earns its
Config recorder; and a build with a known-vulnerable dependency is stopped by the gate.

---

### Stage 9 - The deployment targets' platforms, and the producer path into the lake

**Objective:** what Staging and Production need in order to run promoted artifacts, and the governed
write path through which Production becomes the lake's producer (D22).

**Prerequisites:** Stages 3, 5, 8.

**Scope change (D14):** the Production *networking* moved to Stage 3 and the *registries* to Stage 7, both
because GitLab needed them earlier. What remains here is the data platform and the sharing model — which
is the interesting part anyway.

**Scope change (D17, D18):** this stage also builds the two things those decisions put in Production — the
SageMaker *runtime* (Model Registry and job execution roles, with no domain) and the data scientists'
compute-free access to this account. Both belong here rather than in Stage 10, because Stage 10 consumes
the registry and would otherwise have to create it in passing.

**Scope change (D20):** and the Staging data platform, which is what the promotion chain built in Stage 8
actually deploys against. Note the ordering this creates: Stage 8 builds the chain, Stage 9 gives it
somewhere real to run, and the end of this stage is where the first fully meaningful promotion happens.

**To execute:**

1. Apply the `production/data/` consumer slice, same module as the Stage 5 consumer side: application
   output buckets, the Production Athena workgroup, and LF resource links to the Data Governance share.
   The lake itself is not here (D22) — Production's `data/` holds what applications *produce locally*
   (logs, intermediates, outputs pending curation), not governed tables.
2. **The producer path (D22, §4.4 row 3).** Grant the Production job execution role the Lake Formation
   read **and governed-write** share from Data Governance: production ETL writes curated tables through
   LF-aware engines, cross-account, and this is the only path by which governed data is ever written.
   Prove it with a job that writes a curated table, and prove its converse — the same role cannot
   `PutObject` into the lake buckets directly.
   **The ingestion drop-box pickup runs here too (D25, §4.4 row 10)**, because it is the same producer
   path applied to a file a human dropped rather than to an upstream feed: a job under the Production
   execution role reads the dated prefixes in Data Governance, curates the contents into a governed table
   through the LF write, and deletes what it consumed. Data Governance cannot host this job — its OU SCP
   denies compute, Glue jobs included — so if it does not run in Production it does not run anywhere.
   Verify the KMS grant explicitly: an `AccessDenied` on the drop-box key surfaces as an S3 error.
3. **`production/sagemaker/` — the runtime half of D17, layer `[P]`.** Model package groups for the Model
   Registry (**`aws_sagemaker_model_package_group`**, one per application or model family — D28 item 6),
   and the execution role that pipeline-submitted training, processing and batch-transform jobs
   assume. No domain, no user profiles, no interactive anything. **Each package group carries a resource
   policy written here, not improvised in Stage 10:** the pipeline's Production role registers and
   approves versions; the Staging deploy role reads approved versions (§4.4 row 7); the Development side
   reads status and nothing else (§4.4 row 4). The registry lives here rather than in
   an Interactive account because it is the promotion boundary: a model version is *approved*, and the
   approval has to sit on the far side of the gate from the person who trained it. A model package group
   costs nothing at rest, which is why this is `[P]` and not part of the `[E]` orchestration slice.
4. **The Staging data platform (D20)** — `terraform-live/staging/data/`, from the same modules again, plus
   `terraform-live/staging/sagemaker/` holding job execution roles and nothing else (no domain, no Model
   Registry; the approved model version is read from Production's).
   Its catalog **mirrors Production's schema** — same databases, same table definitions, same LF-Tags —
   because a staging run that fails on a schema difference tests the staging environment rather than the
   application.
   Its catalog mirrors the *lake's* schema (D22) — same databases, same table definitions, same
   LF-Tags — held locally with sampled or synthetic content.
   Its **data is sampled or synthetic and is never a copy of the lake, and Staging is not on the Data
   Management share (D20/D22)**. This is the part to hold the line on: Staging is a deployment target
   where the data scientists have read access (D18) and where automated tests run unattended, so a share
   or a copy would make the least-defended account the cheapest route to governed data. If a test
   genuinely needs production-shaped volume, generate it; if it needs production *values*, the test
   belongs in Production behind the approval gate, not in Staging.
   An earlier version of this plan put a `staging` Glue database inside the **Production** account as a
   stand-in for this. It is removed: it shared an account, an IAM surface and a blast radius with the very
   thing it was meant to de-risk, so it could catch a schema or logic error but never a permission one —
   which is the failure class a cross-account promotion actually produces.
5. **Apply the `DataScientistProdAccess` and `DataScientistStagingAccess` permission sets (D18)** created
   by hand in Stage 1b step 3, now from `terraform-live/identity/`, together with the Production Athena
   workgroup they depend on (`EnforceWorkGroupConfiguration = true`, scan limit, results to a
   per-principal prefix). The Staging set carries no write grant at all — confirm that in the plan output,
   not only in the intention.
6. **The production debugging escape hatch**, designed here rather than improvised later (D17): a
   time-boxed elevated role in Production, assumable only with an approval from `deployment-managers`, that grants
   read access to job inputs and outputs for a bounded window. CloudTrail alarm on every assumption of it.
   This exists because "nobody ever needs to look at production interactively" is not true, and an
   undesigned need becomes a permanent permission.
7. Cross-account IAM: the two deploy roles from Stage 8 step 3 (`awsds-deploy-staging` and
   `awsds-deploy-prod`, both assumed by the runner in Production), and the KMS key grants that let Staging
   decrypt what it pulls from the Production ECR.
8. **Verify the boundary rather than declare it.** Confirm, each as a test with its result recorded:
   - from a **Sandbox or Development** session — no deployment target's infrastructure can be changed; a
     lake table can be read through the share but not written (the governed write belongs to Production's
     job role alone, D22); a write to an S3 bucket outside the organization is denied (§4.2); the
     drop-box in Data Governance accepts a `PutObject` and refuses the matching `GetObject`;
   - from a **Production** session as the data scientist (D18) — no compute can be started
     (`sagemaker:CreateTrainingJob`, `glue:StartJobRun` both denied); Athena runs and its result lands in
     the per-principal prefix even when the client asks for somewhere else; and the reach does not extend
     to anything not enumerated in the permission set;
   - from a **Staging** session as the data scientist (D18, D20) — everything readable, nothing writable,
     including the buckets the pipeline writes to;
   - under the **Production job role** — a curated table written through the LF share succeeds, and a
     direct `PutObject` to the same bucket fails (step 2's pair);
   - and the two §4.4 traps — that S3 access from a laptop over the VPN survives the `aws:SourceVpce`
     condition (row 5), and what fraction of the S3 **console** survives it (row 6).

**Deliverables:** the data scientist reads a lake table from Studio in both Interactive accounts and is
denied on write; the same user, signed in to Production, can inspect a failed job and query through Athena
but cannot start compute; a production job writes a curated table through the governed path and the pandas
test still fails everywhere; the promotion chain from Stage 8 runs end to end against a real catalog in
Staging and then in Production; and every verification in step 8 is written down with its outcome —
including the ones that fail.

---

### Stage 10 - Workflow orchestration and promotion

**Objective:** take a workflow developed in SageMaker and run it in production on a schedule.

**Prerequisites:** Stages 8, 9. **D7 is settled — both implementations are built here** and compared
against the same application, which is the only way the MWAA-versus-native trade stops being abstract.
What remains to check at the start of this stage, not to decide: that `awscc_mwaaserverless_workflow`
still applies cleanly under the CI deploy role (§4.4 row 14 — verified to *exist* on 2026-08-08, not yet
verified to apply under a permission boundary). The metadata-database question from the earlier revision
of this stage applies **only if the provisioned fallback is ever used** — Serverless has no environment
to destroy, so its run history is not state inside an `[E]` resource.

**To execute:**

1. Implement **both** orchestrators against the same workflow, behind a switch, in
   `production/orchestration/`, each producing the D28 artifact set:
   - **(A) MWAA Serverless** — the workflow YAML from the application repository, deployed by the
     pipeline to a versioned S3 prefix; one **`awscc_mwaaserverless_workflow`** per application, with its
     own execution role and its own log group (D28 items 2-5). Fallbacks in order (§4.4 row 14):
     `aws_cloudformation_stack` wrapping `AWS::MWAAServerless::Workflow`; then a `mw1.micro` environment
     (`aws_mwaa_environment`, `[E]`, metadata-database caveat back in force).
   - **(B) Native** — an **`aws_scheduler_schedule`** (EventBridge Scheduler) triggers an
     **`aws_sfn_state_machine`**; container steps run on ECS/Fargate or as SageMaker jobs, glue steps on
     **Lambda**; the state machine's logging configuration writes to the same explicit
     **`aws_cloudwatch_log_group`** discipline as A — named, retention set, per workflow.
   **One asymmetry the comparison must not hide:** A is defined in YAML (DAG-factory format — AWS ships
   a Python-to-YAML converter), B in ASL. The Airflow DAG a data scientist writes in the domain converts
   to A mechanically; to B it must be *ported*. That difference is a large part of what is being compared.
   The rest to write down: cost per run and per month, time to deploy a change, how a failed task is
   retried and observed — under A this means logs only, there is no Airflow UI in Serverless — and what
   each costs in Terraform code and operational surface. Cost model and per-unit rates: §5, `PRICING.md`.
2. Define how a workflow authored in the unified domain becomes a deployable artifact — the D28 set: the
   container, the workflow YAML and the terraform/ folder, all versioned in the project repository that
   graduated into GitLab. **The container must be identical for both orchestrators**; if it is not, the
   comparison is measuring the packaging, not the orchestrator. **Add the D28 promotion lint to the
   Stage 8 CI here:** reject any workflow definition that references a domain resource (project
   connections, portal-scoped IDs) or names a container by anything other than ECR URI and tag — a
   workflow that only runs where the portal exists is not a promotable artifact.
3. Schedule, retry, alerting on failure to CloudWatch/SNS — alarms on the per-workflow log groups and on
   the workflow/state-machine failure metrics, in both implementations.
4. If — and only if — the provisioned fallback is used: document how to create and destroy the MWAA
   environment on demand, and what is lost when it goes. DAG code lives in S3 and survives; run history
   and UI-defined connections/variables do not. Either export them before teardown or state explicitly
   that they are expendable — the `[E]` rule in §5.1 does not allow leaving this implicit. Under
   Serverless this step is empty by construction, which is itself a point for the comparison in step 1.
5. **Close the notebook-to-production gap for models, not just for ETL.** The CI/CD in Stage 8 promotes a
   container; that covers the `app-etl` template in `CLAUDE.md` but not the other thing a data science
   environment produces, which is a trained model. The **SageMaker Model Registry** is the promotion
   boundary — a model version is *approved*, not a file copied — and D17 puts it in the Production account,
   built in Stage 9 step 2, so this stage consumes it rather than inventing it. What remains to define
   here: who registers a model version and under which role (the pipeline's, never the data scientist's),
   how an approved version is served (batch transform or an endpoint), and what is recorded alongside it —
   training data version, metrics, owner. Without this, "data science environment" means "notebooks with a
   nice network", and the whole promotion story only works for code.
   Where the *production* retraining job runs follows from D17 as well: in the Production account, on the
   execution role from `production/sagemaker/`, submitted by the orchestrator chosen at the top of this
   stage. Interactive-account training stays exploratory (Sandbox) or developmental (Development) and
   never produces a registered version directly — registration is the pipeline's act, after graduation
   through git (D21).
   **And the model follows the same chain as the code (D20):** an approved version is first served in
   Staging, against Staging's sampled data, and the promotion pipeline asserts that it loads and returns
   predictions of the expected shape before the Production deployment step runs. A model that only ever
   ran on the machine that trained it is not a promoted artifact — it is a file that changed accounts.

**Deliverables:** a workflow prototyped in Sandbox, engineered in Development and promoted through the
chain runs on schedule in production without manual steps, and a model reaches production through the
registry — exercised in Staging on the way — rather than by being copied.

---

### Stage 11 - Data protection and DLP

**Objective:** the protection layer, built on top of a working environment rather than before it.

**Prerequisites:** Stages 5, 6, 9; decision D6.

**To execute:**

**What is no longer in this stage:** the data perimeter (§4.2) moved to Stage 1 and Security Hub, GuardDuty
and Access Analyzer moved there with it (principle 9). What remains here is genuinely data-specific.

1. Amazon Macie for sensitive-data discovery — primary scope the **Data Governance** buckets (D22),
   plus the **derived zones in Sandbox and Development** (D19), which is where governed data re-surfaces
   outside the lake account and is the part a Data-Management-only scope would miss; findings to Security
   Hub; results mapped
   onto the classification scheme defined in Stage 5 step 2. **Scope it to a sampled prefix** — Macie bills
   per GB inspected and can dwarf every other line item in §5.
2. Lake Formation column-level and row-level filters driven by the LF-Tags from Stage 5, enforceable
   because of D13.
3. Egress hardening review of Stage 6, once D5 has been closed by the comparison in §4.3.
   **Correction:** the previous version of this plan listed "block SageMaker Studio file download /
   notebook export" as a control. Verify it exists before relying on it (Stage 6 flags the same doubt) —
   as far as this plan knows, Studio has no supported setting for that. If it does not, say so plainly in
   the threat model rather than leaving a control listed that nobody implemented.
4. Turn on GuardDuty's **S3 Protection and Malware Protection** — deferred from Stage 1 specifically so the
   decision could be made against a real bill (§5).
5. CloudTrail data events on the sensitive buckets; CloudWatch alarms for exfiltration patterns: mass
   `GetObject`, unusual egress volume, `PutObject` to an unexpected destination.
   **Correction:** the previous version listed an alarm on "presigned URL creation". That is not
   detectable — signing a presigned URL is a local SigV4 operation against credentials already held, it
   makes no API call and appears nowhere in CloudTrail. What *is* detectable is the **use** of one, which
   shows up as a request whose authentication method differs from a normal SigV4 call. Alarm on that.
6. Only then evaluate whether a third-party DLP agent adds anything the above does not cover.

**Deliverables:** a documented threat model with the control that addresses each item — and, for the items
where no control exists, an explicit statement that the risk is accepted rather than a control that was
never built; alarms that fire on a simulated exfiltration attempt.

---

### Stage 12 - Observability, governance and FinOps

**Objective:** know what is running, what it costs, and be told when something breaks.

**Prerequisites:** any stage that created resources.

**To execute:**

1. CloudWatch dashboards per environment (SageMaker, GitLab, VPN, NAT traffic, Athena scans).
2. Alarms → SNS → e-mail for: budget thresholds, failed pipelines, VPN down, GitLab unhealthy,
   unusual data scans.
3. Log retention policies everywhere (default retention is "forever", which quietly costs money).
4. Cost allocation tags activated in Billing; a monthly cost review against §5.
5. **Review the `[P]`/`[D]`/`[E]` assignments against the real bill**, which by this point exists. The two
   estimates most likely to be wrong are the interface endpoints (the largest hourly item) and GitLab
   (the largest idle item). Update §5 and §5.1 with measured numbers rather than the projections.
6. Config rules / conformance packs on top of the Control Tower guardrails; review the recorder scope set
   in Stage 1b step 8 against what the bill actually shows.
7. Tighten the permission sets in `terraform-live/identity/` against real usage, using **IAM Access
   Analyzer unused-access findings** — which is a better instrument than review, because it reports
   permissions that were granted and never exercised.
8. **Backup and recoverability**, which no earlier stage owns: an org-wide **AWS Backup** plan through an
   Organizations backup policy, covering the EBS volumes of the `[D]` instances and the EFS filesystem;
   **Vault Lock** on the backup vault so a compromised administrator cannot delete the backups; and
   cross-region copies for the state buckets and the GitLab backup. Then state the numbers the plan has so
   far avoided: what the recovery time objective actually is for GitLab, for the Terraform state, and for
   the data lake, and test each one at least once. An untested backup is a hypothesis.
9. Review **Service Quotas** for the services in use, and set CloudWatch alarms on the ones that would
   silently break a session (SageMaker instance limits, EIPs, VPC endpoints).

---

### Stage 13 - Public-facing web tier (experiment)

**Objective:** the experiment described in `CLAUDE.md` — a public web server reaching a private backend.

**Prerequisites:** Stages 3, 9.

**To execute:**

1. Public ALB in the public subnets with WAF and an ACM certificate; a public Route 53 hosted zone.
2. Application on ECS Fargate in the private subnets; database (RDS or the Iceberg catalog through Athena)
   in the isolated subnets.
3. Security groups allowing only ALB → app → data, and nothing else.
4. Document the blast radius and how to tear the whole tier down.

---

## 8. Cross-cutting work (continuous, not a stage)

- `LOG.md`: the user records every manual step (never edited by Claude).
- `CLAUDE.md` → `Claude LOG`: updated at the end of each stage, referencing the stage number from this plan.
- `REFERENCES.md`: every link used as a reference.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `GENERAL_PLAN.md`: revised whenever a decision changes or a stage is re-scoped.
- The **Well-Architected Machine Learning Lens** is the per-stage checklist: when a stage is built, walk
  its questions for the components the stage touched — it is to this environment what the SRA is to the
  account structure.

---

## 9. Open questions

Everything that was open before execution started is now closed in §4 (D1-D28). What follows is
what is genuinely still unanswered:

1. **Which domain name to register (D15).** The one input needed from the user. Not blocking Stage 1, but
   blocking Stage 7, and worth doing early since registration and validation take time.
2. **D7/D28 - two verifications, not decisions.** The orchestration decision is closed (both built,
   Stage 10; alternative A is MWAA Serverless via `awscc_mwaaserverless_workflow`, verified to exist
   2026-08-08). What is open: (i) whether the awscc resource *applies* cleanly under the CI deploy role
   (§4.4 row 14 — fallback chain recorded there); (ii) whether logs-only observability — Serverless has
   no Airflow UI — is livable for a data scientist debugging a failed run, which only the Stage 10
   comparison can answer. Keep application entry points as plain containers so both implementations, and
   the two options that were not built, remain viable.
3. **AZ name-to-ID mapping across accounts.** AWS maps AZ names to physical datacenters independently per
   account, so `data.aws_availability_zones` indexed by position can place "the same" AZ in different
   datacenters in Sandbox, Development and Production — which turns peering traffic that looks intra-AZ
   into cross-AZ traffic at USD 0.01/GB each way. **D14 and D21 made this concrete rather than
   theoretical:** the VPN, SageMaker and GitLab talk across the two peerings constantly. Check it in
   Stage 1b step 11
   (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
   profile). If the mappings differ, Stage 3 anchors subnets on `zone_ids` (`usw2-az1`, passed per
   environment in `.tfvars`) instead of on list position, and §4.1 is updated accordingly.
4. **Layer assignments.** `[P]`/`[D]`/`[E]` are cost judgements based on estimates. Revisit them at Stage 12
   against the real bill — especially the interface endpoints (the largest hourly item, now ~9 of them)
   and GitLab (the largest idle item).
5. **CodeArtifact ecosystem coverage (§4.3).** The CodeArtifact documentation lists Cargo among its
   supported formats, so the Rust question is down to confirming it in practice at Stage 6. Julia and R remain genuinely uncovered and keep their §4.3 fallbacks — they
   are what decides whether egress design B is livable.
6. **Whether SageMaker Studio can block file download** (Stage 6 — the question carries over unchanged to
   the ML-blueprint apps under D26). If not, Stage 11's threat model has to
   record an accepted risk rather than a control.
7. **The fourteen cross-account integrations in §4.4.** Each has a stated fallback, so none of them blocks
   a stage, but none of them is known to work either. They are listed there rather than repeated here.
   Row 11 (organization-wide RAM sharing and the Lake Formation cross-account version) is the one to
   settle earliest, because it is enabled in Stage 1b and consumed in Stage 5 — and since D26 it also
   carries the domain's account associations (row 12) — and its failure mode is silence rather than an
   error. Row 13 (CodeConnections from the unified domain to the self-hosted GitLab in a private subnet)
   is the one with no convenience-preserving fallback: check it while building Stage 7, when GitLab first
   exists.
8. **How much of the S3 console survives the `aws:SourceVpce` condition** (§4.4 row 6, Stage 9). This
   decides whether D18's "read named S3 prefixes in Production" is usable through the console at all, or
   whether it is a CLI-over-the-tunnel operation that `README.md` has to say so about. Cheap to answer,
   annoying to discover by symptom.
9. **Whether sampled or synthetic Staging data makes the integration tests meaningful** (D20, Stage 9).
   The decision that Staging never holds a copy of production data is firm — the reasoning is in D20 and
   it is a security argument, not a cost one. What is open is the consequence: a test suite running
   against a sample catches permission, schema and wiring errors and misses everything that only appears
   at production distribution and volume. Answer it by recording, for each production incident this
   environment ever has, whether a Staging run could have caught it. Until there is such a record, this
   is a belief rather than a finding.

---

## 10. Plan revision history

Kept deliberately short: this file, not its history, is the source of truth. A revision only earns a row
here once the environment exists — from Stage 1 onwards, when a change to the plan also means a change to
something already provisioned.

| Date | Change |
|---|---|
| 2026-08-07 → 2026-08-08 | **The plan, written and revised ten times before any AWS resource existed.** It arrived at: stages 0-13; decisions D1-D28, all closed — the ninth revision adopted **SageMaker Unified Studio** (D26), the catalog-maintenance exception for Glue Crawlers (D27) and the production workflow contract (D28), and the tenth placed the domain by asking which *axis* it sits on — **`Data Management` was renamed `Data Governance`** and took the domain, no tenth account being needed, and the single `Manager` persona split into **Deployment Manager** and **Governance Manager** so that releasing a job and granting it data are two signatures; the nine-account, four-OU layout; §4.2 the data perimeter; §4.3 the two egress designs; §4.4 the fourteen cross-account integrations; §5/§5.1 the cost model and the `[P]`/`[D]`/`[E]` operating model; §9 the open questions; §11 the lab-versus-institution delta. `GLOSSARY.md` and `PRICING.md` were created along the way, the latter measured from the AWS Price List bulk API rather than estimated. The individual revisions are not recorded here: everything that survived them is in the sections above, and with nothing provisioned they described only how the document changed, not how the environment did. The reasoning that would otherwise be lost is kept in the D-columns of §4 (each decision carries its own rationale and its revision triggers) and in the "Lessons carried forward" list in `CLAUDE.md`. |

---

## 11. What a large institution would do differently

Principle 10. Almost every decision in this plan is bent by two constraints a real organization does not
have: a USD 50/month ceiling and a single operator who is also the only user. That is a legitimate way to
build a lab, but it means the environment is not the reference architecture, and the difference should be
learned rather than absorbed by accident. This is the delta, decision by decision.

| Area | This lab | A large institution | Why the difference matters |
|---|---|---|---|
| Account structure | 9 accounts; tooling in Production (D14); one account per environment plus one data account (D20-D22) | Shared Services / Tooling account in an `Infrastructure` OU; a Network account; per-team sandbox accounts; separate Dev/Staging/Prod **per workload**; data accounts **per domain** | The lab still has no boundary between build and runtime, and none between teams. One account per environment role is enough for one team and one workload; at thirty of either, each role becomes a fleet |
| OUs | Security, Interactive, Data, Workloads (D23) | Plus Infrastructure, Deployments, Policy Staging, Suspended; Workloads nested into NonProd/Prod | The four OUs each carry a real policy set, which is the test an OU must pass. Policy Staging is the notable absence: an SCP tested on a throwaway OU before it reaches anything real is the difference between a guardrail and an outage. D23 records the nesting triggers |
| Account vending | Manual Account Factory, six times | **AFT** (Account Factory for Terraform) with a customization pipeline | At six accounts created once, automation costs more than it saves; at thirty it is the only way accounts stay consistent |
| Networking | One VPC per account, peered, NAT and endpoints per account | Transit Gateway or Cloud WAN, centralized egress through an inspection VPC, centralized interface endpoints shared by RAM, **IPAM** for CIDR allocation | Peering is O(n^2) and per-account endpoints are the largest hourly cost multiplied by the number of accounts. CIDRs chosen by hand collide eventually |
| VPN | Self-managed WireGuard, peers in a `.tfvars` (D4) | AWS Client VPN or Verified Access, federated to the corporate IdP, with per-user certificates and session logging | Revoking one person here means editing a file and re-applying. That does not survive an offboarding process |
| Identity | Identity Center as the identity source | Identity Center federated to the corporate IdP (Entra ID, Okta) via SAML + SCIM, groups driven by HR | Joiners/movers/leavers has to be automatic, or entitlements only ever accumulate |
| Data lake placement | One Data Governance account (D22), producer/consumer separation, LF cross-account sharing as the default read path | Data lake accounts **per domain**, a data-mesh org model, and subscription workflows in front of the shares | This row largely closed on 2026-08-08 — the mechanism is now the institutional one. What remains is scale: one domain and one producer here; an institution has many of each, and the request/approval workflow in front of the share becomes the product |
| Data governance | **Closed 2026-08-08 (D26): the lab adopted it** — a unified domain (DataZone V2) over the hand-built Glue + LF-Tags substrate | SageMaker Unified Studio / SageMaker Catalog (DataZone): business glossary, data products, subscription workflows, lineage | The one row in this table closed by product maturity rather than by budget: official Terraform support (2026-07) removed the practical objection, and the substrate is still built by hand first (Stage 5), so the teaching value survives underneath the portal |
| Who approves access to data | **Closed 2026-08-08: the lab adopted it.** The single `Manager` persona was split into a **Deployment Manager** (`deployment-managers`, lifecycle approvals in the pipeline) and a **Governance Manager** (`governance-managers`, subscription and data-access approvals in the portal, domain owner of the unified domain) | A data steward *per data domain*, sitting inside the producing team rather than centrally, with the subscription queue as their own backlog | The split was first recorded here as notational, then adopted a few hours later — because it is not notational: with one persona a single human writes a job reading restricted data, approves its release **and** approves its data access. What stays a lab compromise is that there is one governance manager for all data, not one per domain |
| Domain topology | One domain, one set of project profiles, all data in one Data Governance account | A domain per business data domain, **decentralised producer accounts** each owning and publishing their own datasets, consumers subscribing across them | This project's Data Governance account is a producer, a consumer and the governance plane at once. That collapse is invisible at one team and becomes the central problem at ten — it is what "data mesh" is a name for |
| Iceberg operations | General-purpose S3 buckets + scheduled Athena `OPTIMIZE`/`VACUUM`, because D13 leans on prefix-level IAM control | **Amazon S3 Tables**: managed Iceberg with automatic compaction, snapshot expiry and Lake Formation integration | The managed service removes the maintenance a hand-rolled lake forgets — but takes away the prefix-level control D13 is built on, so switching is an architecture decision, not a swap |
| Derived data (D19) | Per-principal prefixes with a lifecycle expiry; classification inheritance stated as policy and enforced by nobody | Lineage-aware catalog that propagates the classification of a source onto everything derived from it, plus periodic re-scan of the derived zone | The lab knows *where* copies land but not *what is in them* until Macie says so, days later. Inheritance by policy works with three users and fails silently with thirty |
| Environment promotion | Four environments: Sandbox (experimentation) feeding Development by git, then Development → Staging → Production through the pipeline (D20, D21) | The same chain, plus per-workload triples, and staging data that is a governed, masked copy of production rather than a sample | This row closed on 2026-08-08 in two steps — Staging in the morning, Development and the corrected chain origin in the evening. What stays open is the *data*: sampled data catches permission, schema and wiring errors, and misses everything that only appears at production distribution and volume |
| Access requests | Terraform merge request | Self-service request with approval workflow, time-bound grants | "Ask the platform engineer" does not scale, and permanent grants never get revoked |
| Egress control | DNS Firewall allowlist, or no internet (§4.3) | AWS Network Firewall with TLS inspection, plus an internal package mirror covering every ecosystem (Posit Package Manager, Artifactory or similar) | A commercial artifact manager solves in one product what §4.3 solves with four different fallbacks. It costs money the lab does not have |
| Egress cost | ~USD 0.05/h NAT | ~USD 290/month Network Firewall, accepted without discussion | The lab has to be clever precisely because it cannot buy the obvious answer |
| Shared storage | EFS with Access Points, in **Sandbox only** (D24); POSIX identity not tied to SSO | FSx for Lustre for training throughput, EFS for home directories in *every* interactive account, and file access auditable per user | Two gaps, not one. "Who read this file" is unanswerable in the lab design — in a regulated institution that is disqualifying. And a data scientist working in Development has no shared filesystem at all, so they have to think about which account their files are in; an institution would never make that the user's problem |
| CI/CD trust | Same-account deploy runner with an instance profile (D14; OIDC is blocked because IAM cannot fetch a VPN-only issuer's JWKS) | Build account separate from deploy targets; OIDC federation against a publicly resolvable issuer; signed artifacts; provenance attestation | A compromised runner in the lab compromises Production directly |
| Backups | AWS Backup + Vault Lock (Stage 12) | The same, plus tested DR runbooks, cross-region recovery, and RTO/RPO agreed per system rather than assumed | The lab tests recovery once; an institution rehearses it |
| Availability | 1 NAT, single-AZ endpoints, single VPN instance (D9, D4) | Multi-AZ everything, no single points of failure | Every availability shortcut here is a deliberate cost trade, and each one is listed in D4 and D9 |
| Operations | One person, `make up` / `make down` | On-call rotation, runbooks, change management, an internal platform team with its own product backlog | The largest difference of all, and the one no amount of Terraform addresses |

**How to use this table.** When a stage is built, check its row here. If the lab approach would be
indefensible at scale, say so in the stage's notes and record what the alternative was — that is the
artefact worth keeping from this project, more than the infrastructure itself.
