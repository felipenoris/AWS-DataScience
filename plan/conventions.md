# Conventions and operating model

Read this with any stage from Stage 2 onwards: naming, tags, the `terraform-live/` layout,
the Terraform and IAM rules, and the `[P]`/`[D]`/`[E]` layers every slice is classified into.

---

## 6. Conventions (to be applied from Stage 2 onwards)

**Naming:** `<project>-<env>-<component>[-<detail>]`, lowercase with hyphens.
Project prefix: `awsds`. The `<env>` token is one of `sandbox`, `dev`, `data`, `staging`, `prod`, `org`.
There is deliberately no token for `Policy Canary` (D29): nothing is ever created in that account, so
nothing in it needs a name — and the day something does, the account has stopped being what it is for.
Example: `awsds-sandbox-vpc`, `awsds-data-raw` (the lake lives in Data Governance since D22, so
`awsds-prod-raw-data` would name a bucket that does not exist), `awsds-prod-ecr-dev-env`.

**Mandatory tags on every resource:**
`Project=AWS-DataScience`, `Environment=sandbox|development|data|staging|production|org`,
`ManagedBy=terraform`, `Owner=<sso-user>`, `CostCenter=<stage>`. (`org` marks org-level and **platform**
resources — the identity slice, and D29's Policy Canary. **It was `shared` until 2026-08-09 and was renamed
before anything was built**, because D14's revision trigger can fire and the account it would create is
conventionally called `shared`: two different things answering to one token in cost reports is a defect that
is free to avoid now and means renaming deployed resources later. **`shared` is now reserved and unused** —
it names a Shared Services account if one is ever vended, and nothing else. `data` marks the Data
Governance account, which is not an environment at all: it sits on the ownership axis, not the lifecycle
one, so cost reports should be able to separate it from every environment.)

**Forward constraint from D35 — every `sandbox` token in this file is per business unit, not singular.**
`Sandbox` is the one account in the map that multiplies (one per business unit; N is 1 today), so five
things written here as singletons are really per-unit: the `<env>` token `sandbox`, the
`Environment=sandbox` tag value, the `terraform-live/sandbox/` tree, the `awsds-infra-sandbox` SSO profile,
and `make up`/`make down ENV=sandbox`. Everything else — Development, Staging, Production, Data Governance,
Identity, `org` — is structural and stays exactly as written.

**The concrete scheme is settled in [Stage 14](stages/stage-14-sandbox-vending.md)**, alongside the CIDR
allocation table (Stage 3) and the VPN topology (Stage 4): choosing a directory and token shape here, with
one unit and no `sandbox-unit` module written, would be guessing at the interface of something that does not
exist yet. What this note fixes now is the cheaper half, and it is the one that fails silently — **the two
enumerations above are Lesson 14 in naming.** The `<env>` list and the tag policy's allowed values both
enumerate `sandbox`, and the forcing function behind the tags is an SCP conditioned on `aws:RequestTag`
(1b step 7). So an enumeration that does not admit a per-unit token turns the first apply in a freshly
vended account into an `AccessDenied` — discovered in a new account, by whoever is standing it up, which is
the worst possible place to find out about a naming rule. Write both lists so a per-unit token is admissible
before it is needed.

**Terraform layout:**

Each slice carries its layer from §5.1: `[P]` persistent, `[D]` dormant (stop/start), `[E]` ephemeral.

```
terraform-live/
├── identity/             # [P] permission sets, groups, assignments - applied with the
│   │                     #     delegated-admin profile (D10); never touches Management.
│   │                     #     ALSO the SCPs, RCPs and tag policies: they used to be
│   │                     #     console-only and owned by nobody after Stage 1b. Since D30
│   │                     #     was reverted there is no principal that can work around a
│   │                     #     bad Deny from inside a governed account, so this set needs
│   │                     #     a diff, a review and a rollback more than anything else here
│   └── bootstrap/        # [P] state bucket for the Identity account
├── sandbox/              # EXPERIMENTATION (D21): the unit of work is a notebook.
│   │                     # ONE OF THESE PER BUSINESS UNIT (D35) - the whole subtree
│   │                     # below is what Stage 14's sandbox-unit module composes
│   │                     # from a single input. N is 1 today; the naming is settled
│   │                     # there, not here (see the D35 note above)
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
│   ├── dev-env/          # [P] the approved dev-env image registered for this account:
│   │                     #     aws_sagemaker_image + image_version + app_image_config.
│   │                     #     Applied by the Stage 8 step 1 pipeline after the dev-env
│   │                     #     steward's approval, through awsds-deploy-devenv-sandbox -
│   │                     #     the one slice written from Production into an Interactive
│   │                     #     account (INT-18). Its only input is the approved digest
│   └── sagemaker/        # [P] blueprint target (D26): the experimentation project's
│                         #     environments are provisioned HERE by the domain in
│                         #     data-governance/; running apps are [E], deleted by make down.
│                         #     What Terraform owns in this slice is the PREREQUISITES the
│                         #     blueprint consumes - the provisioning and manage-access roles,
│                         #     the VPC/subnet/security-group parameters the ML blueprint is
│                         #     pointed at, the KMS key, and the D13 boundary policy attached
│                         #     to the project roles (INT-15). It does NOT declare the
│                         #     project environments themselves: DataZone owns those, and a
│                         #     Terraform resource for them would fight the blueprint
├── development/          # DEVELOPMENT (D21): the unit of work is a pipeline
│   ├── bootstrap/        # [P] state bucket for the Development account
│   ├── foundation/       # [P] VPC (own CIDR), KMS, IAM roles, peering requester to
│   │                     #     Production - Studio here must reach GitLab (INT-09)
│   ├── data/             # [P] scratch + derived zone + Athena workgroup + LF resource
│   │                     #     links, same shape as sandbox/data/
│   ├── egress/           # [E] NAT + endpoints, same D5 switch as sandbox
│   ├── dev-env/          # [P] same slice, same module, same pipeline, applied through
│   │                     #     awsds-deploy-devenv-dev - the image is identical in both
│   │                     #     Interactive accounts by construction (D17, Stage 8 step 1)
│   ├── sagemaker/        # [P] blueprint target (D26): the engineering project's
│   │                     #     environments land here, provisioned by the domain in
│   │                     #     data-governance/. No domain of its own. Workflows are
│   │                     #     authored and test-run here before promotion.
│   │                     #     Same Terraform/DataZone split as sandbox/sagemaker/:
│   │                     #     prerequisites here, environments owned by the blueprint
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
│                         #     (INT-12). A registry: blueprints provision compute
│                         #     into those accounts, never into this one.
│                         #     No foundation/ slice: no VPC, no user compute, nothing
│                         #     standing - which is also why INT-13 has no host
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
    │                     #     Built in Stage 3, because Stage 7 (GitLab) depends on it (D14).
    │                     #     ALSO the prod.internal and pages.internal private zones and
    │                     #     their cross-account associations (D15 as revised 2026-08-09).
    │                     #     NO public zone, NO registered domain: those are Stage 13, and
    │                     #     NOT the CA - see pki/ below
    ├── pki/              # [P] the internal root CA (D36). OWN state file and OWN KMS key,
    │                     #     deliberately not foundation/'s: foundation is opened to change
    │                     #     a CIDR or accept a peering, and every such edit would otherwise
    │                     #     decrypt the root. Applied EARLY, with registry/ below, because
    │                     #     the dev-env image is built from Stage 6 and must carry the root
    │                     #     (INT-19). Outputs the CA cert and the issued leaves - NEVER the
    │                     #     root private key. Excluded from every make down path
    ├── data/             # [P] application-output buckets, Athena workgroup, LF resource
    │                     #     links + the governed-write grant (D22). The lake itself lives
    │                     #     in data-governance/. The registries are NOT here - see below
    ├── registry/         # [P] ECR (+ pull-through cache) and CodeArtifact (D14), with their
    │                     #     OWN KMS key and consumer account ids from a map. Split out of
    │                     #     data/ on 2026-08-09 to preserve D14's revision option: if the
    │                     #     supply chain ever moves to a Shared Services account, this
    │                     #     slice leaves and data/ stays. A folder is not a boundary - it
    │                     #     buys migration cost only (Stage 7, option-preservation note)
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
    │                     #     the provisioned-MWAA fallback (INT-14)
    └── app/
        └── app-etl/      # [E]

terraform-modules/        # reusable: vpc, wireguard, iam-role, ecr-repo, s3-bucket,
                          # step-function, mwaa-serverless-workflow, ...
                          # consumed by git tag, never by branch - a module that moves under a
                          # caller is a broken caller
```

`make down ENV=sandbox` destroys the `[E]` slices in reverse dependency order and stops the `[D]`
instances; `make up ENV=sandbox` starts the `[D]` instances and applies the `[E]` slices; `make status`
reports what is running and the current hourly burn. **`ENV` names a business unit's sandbox rather than
*the* sandbox (D35)** — Stage 14 step 6 makes the same `up`/`down` pair work against a generated unit, which
is what makes a unit disposable rather than merely creatable. `[P]` slices are never touched by any of them — they
are applied deliberately, by hand. One `[E]` resource lives outside any slice: the running **apps inside a
Unified Studio project** are created by users, not by Terraform, so `make down` deletes them through the
API before touching the slices. **Which API, since D26 changed the answer:** the apps live in the
per-project SageMaker AI domain that the ML blueprint provisioned into the account, so the teardown is
`sagemaker:ListApps`/`DeleteApp` (and the enclosing space) scoped to that domain — *not* a call against
the DataZone domain, which owns no compute. `make down` must discover the domain ID rather than have it
pasted in, since the blueprint chose it. This is the one place where the registry/runtime split shows up
as an operational detail rather than as a principle.

`ENV=staging` is the one environment a human normally never runs these against: `make up ENV=staging` and
`make down ENV=staging` are steps *inside* the promotion pipeline (Stage 8), which brings Staging up,
deploys, tests, and tears it down again. They still have to work by hand — a rebuild that only works from
CI is the same bug as one that only works by hand — but the expected caller is the pipeline.

**Terraform rules:**

- Pin the provider version and `required_version`. One `providers.tf` per slice.
- Region, AZs and AMIs follow the portability rules in `plan/architecture.md` §4.1 — no region literals in `.tf` files.
- Authentication through named SSO profiles, one per Terraform-managed account — `awsds-infra-sandbox`,
  `awsds-infra-dev`, `awsds-infra-data`, `awsds-infra-staging`, `awsds-infra-prod`,
  `awsds-infra-identity` (Stage 1b step 5) — never keys. **One of these per business unit is the sandbox
  one** (D35); the other five are structural.
- Every slice: `terraform fmt`, `validate` and `plan` must be clean before apply.
- Remote state read across slices through `terraform_remote_state` data sources, never hardcoded IDs.
- **The Organization is never in Terraform, and the code is written to survive that (D34).** Accounts and
  OUs are created from the console, by design (principle 1), so no state declares them and none of it can
  drift. What it *can* do is leave a console-created OU or account outside code that was written as a list —
  invisible rather than drifted, with `terraform plan` reporting "No changes". So in `terraform-live/identity/`:
  **the floor is discovered, the grants are enumerated.** Anything that must cover everything — SCP/RCP
  attachments, the organization-root set, the tag policy — is `for_each` over the `aws_organizations_*` data
  sources; permission set assignments are written out one by one, because an account acquiring a grant by
  simply existing is the opposite of the intended failure mode.
- Modules are referenced by **git tag**, never by branch, so a module change cannot silently alter an
  existing deployment.

**IAM rules** (these are conventions because they are easy to violate one role at a time):

- Every role that a non-administrator can create or influence carries a **permissions boundary**.
- `iam:PassRole` is never granted unqualified. It is always scoped by `iam:PassedToService` and by resource
  ARN. `PassRole` plus a job-creating API (`sagemaker:CreateTrainingJob` is the relevant one here) is a
  privilege-escalation path: it lets a user run code under any role they are allowed to pass.
- Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now". The starting point of a permission set
  is narrow, because loosening a permission is a five-minute change and tightening one is a negotiation.
  **One exception exists and it is named rather than tacit: the `infrastructure` group** (D32;
  `ORGANIZATION.md`, "The limit of the separation of duties"). It holds `AdministratorAccess` on every
  Terraform-managed account because it is the identity `terraform apply` runs as, and an identity that
  *authors* IAM cannot be constrained by the IAM it authors — narrowing that set would be notation, not a
  control (Lesson 18). What contains it is detective and enumerated: the Control Tower group-membership
  alarm, Object Lock in compliance mode, CloudTrail with log file validation. **Read the exception
  narrowly** — it covers one group, and any *other* principal that turns up holding administrator is a
  finding, not a precedent.
- **And no broad managed policy for a principal that is itself a control** (D31). `ReadOnlyAccess` looks
  harmless and is not, for an approver: it carries `s3:Get*` and `athena:GetQueryResults`, so it reaches the
  derived zones and other people's query output. Every persona in this plan gets a set written for its job —
  three for the data scientist (D18), one for each approver — and the two approver sets are the ones whose
  *denials* are the point of them.
- **Where a read restriction has to survive forgetting, put it in a KMS key policy rather than in a list of
  prefixes** (D19 as revised by D31). A permission set enumerates; a key policy is default-deny. The
  derived zone has its own CMK for exactly this reason, and the separation from the account's general-purpose
  key is what makes it expressible at all.
- **No principal is exempt from a deny "just in case", and since D30 was reverted there is no exception
  to that at all.** Carve-outs are per function and per statement: the catalog-maintenance role exempt
  from the `Data` OU's Glue deny (D27), `datazone:*` as a governance control plane (D26), a deploy role
  exempt from a specific deny so automation does not stall. Each names one principal, one statement and
  one reason. A standing role exempt from *every* custom deny was proposed and removed — the recovery path
  is the Management account, which sits outside SCPs by AWS's design rather than by ours (D16), and the
  cheap defence is catching the bad policy in the `Policy Canary` before it is attached (D29).
- **Any ARN condition uses an enumerated list, never a wildcard account.** `arn:aws:iam::*:role/x` reads
  as "any principal named `x`, in any account", so a condition written to name one role silently names a
  role that anybody able to create a role can mint. This applies to the per-function carve-outs above and
  is checked in CI (Stage 2 step 9).

---

### 5.1 Operating model: three layers (D11)

The naive reading of "destroy it between sessions" is wrong, because most AWS resources cost nothing at
rest. The rule is **pay nothing while idle**, not **destroy everything**. That splits the environment into
three layers, and every stage must say which layer each of its resources belongs to.

**[P] Persistent — created once, never destroyed.** Free or nearly free at rest, or too slow to rebuild:
the Organization, the accounts, Control Tower, Identity Center, SCPs, Terraform state buckets, the
**VPC itself** (VPC, subnets, route tables, internet gateway, security groups, NACLs cost nothing),
Route 53 private zone, IAM roles, KMS keys, S3 data buckets, ECR repositories, budgets and alarms — and
the **SageMaker unified domain and its projects** (D26 — a DataZone V2 domain at rest bills only metadata
requests and storage; the per-project SageMaker AI domain that the ML blueprint provisions likewise bills
nothing until an app runs) and the **EFS filesystem** (lifecycle to
Infrequent Access; cents per month at lab scale). Rule 2 below records why those two moved out of `[E]`.
The domain is also where the *catalog* lives — glossary, data products, subscription decisions — which is
state in the rule-2 sense and on its own settles the layer question.

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

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
