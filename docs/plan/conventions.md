# Conventions and operating model

Read this with any stage from Stage 2 onwards: naming, tags, the `terraform-live/` layout,
the Terraform and IAM rules, and the `[P]`/`[D]`/`[E]` layers every slice is classified into.

---

## 6. Conventions (to be applied from Stage 2 onwards)

**Naming:** `<project>-<env>-<component>[-<detail>]`, lowercase with hyphens.
Project prefix: `awsds`. The `<env>` token is one of `sandbox`, `dev`, `data`, `staging`, `prod`, `org`.
There is deliberately no token for `Policy Canary` (D29): nothing is ever created in that account, so
nothing in it needs a name — and the day something does, the account has stopped being what it is for.
*(One exception, and it is bounded: a battery run creates throwaway objects — a bucket, an IAM user — to
exercise a candidate policy, and deletes them in the same sitting. Stage 1c step 7.3 plans the cleanup
before the call. A throwaway that outlives its battery is the thing this rule is about.)*
Example: `awsds-sandbox-vpc`, `awsds-data-raw` (the lake lives in Data Governance since D22, so
`awsds-prod-raw-data` would name a bucket that does not exist), `awsds-prod-ecr-dev-env`.

**One service refuses this prefix outright, and it was measured rather than anticipated: SSM Parameter
Store** (Stage 2's Validation, 2026-08-16). Parameter Store reserves every name beginning with **`aws`** or
**`ssm`**, case-insensitive — and `awsds` begins with `aws`, so `/awsds/…` is rejected at `PutParameter`
with **`AccessDeniedException: No access to reserved parameter name`**, a message that reads like a policy
problem and is a naming one. **A project parameter therefore takes `/datascience/<env>/…` as its path** —
the project name spelled out, since the abbreviation is precisely what collides. Nothing else in this
design is affected: the collision is specific to Parameter Store *names*, and buckets, keys, roles, policies
and permission sets all keep `awsds-`. *(Reading a **public** parameter — `/aws/service/ami-…` for an AMI,
which `docs/plan/architecture.md` §4.1 requires — is unaffected: that is AWS's own namespace being read,
not ours being written.)*

**Mandatory tags on every resource:**
`Project=AWS-DataScience`, `Environment=sandbox|development|data|staging|production|org`,
`ManagedBy=terraform|console`, `Owner=<sso-group>`, `CostCenter=<stage>`. (`org` marks org-level and **platform**
resources — the identity slice, and D29's Policy Canary. **It was `shared` until 2026-08-09 and was renamed
before anything was built**, because D14's revision trigger can fire and the account it would create is
conventionally called `shared`: two different things answering to one token in cost reports is a defect that
is free to avoid now and means renaming deployed resources later. **`shared` is now reserved and unused** —
it names a Shared Services account if one is ever vended, and nothing else. `data` marks the Data
Governance account, which is not an environment at all: it sits on the ownership axis, not the lifecycle
one, so cost reports should be able to separate it from every environment.)

**`ManagedBy=console` is admitted, and it is not a lapse — settled 2026-08-12, when the first resource
needed it.** Stage 2 names seven artefacts that stay outside Terraform for structural reasons (wrong
account, Control Tower's object, the identity seam, or a setting hand-managed by decision), and the
organization Access Analyzer in Audit is one of them. Tagging it `terraform` would be false at the only moment the tag is read — when somebody is
working out where a resource's source of truth is. So the value is the honest one, and the rule that keeps
it from spreading is that **`console` is admissible only for a resource Stage 2's out-of-Terraform table
names**: anywhere else it is a resource that should have been code. Note it is outside the forcing SCP of
1c step 7.8, which requires `Environment` and `Project` and nothing else — so this enumeration is a
convention, not a control, and a tag policy that later enumerates `ManagedBy` values has to admit both.

**`Owner` names a group, never a person — settled 2026-08-10, while one resource carried it.** The value is
one of the project's `sso-group-*` groups (Stage 1b step 2), and it records **who owns the resource, not who
created it**: a vended account, an OU and the identity slice are all `Owner=sso-group-infrastructure` even
though `AWS Control Tower Admin` created them, since that identity is deliberately in no project group (D33,
D34). Ownership rather than authorship is what keeps the tag from being a second spelling of `ManagedBy`,
and what makes it carry information from Stage 6 onwards — when the interactive environment starts creating
resources the builder did not.

Three reasons it is not `<sso-user>`, which is what this line said until 2026-08-10:

- **The literal reading is an e-mail address.** Identity Center users are created with the address as their
  `userName` (Stage 1b step 2), so a per-user value would carry an address out of `secrets/` and into git
  twice over — through Stage 2's Terraform and through 1c step 7.8's tag policy — which `CLAUDE.md` forbids
  outright.
- **A group survives the identity source being replaced; a user name does not.** Same argument 1b step 8.3
  used to refuse a metric filter keyed on a GUID.
- **With one human it would be a constant.** `Owner=<the one builder>` on every resource attributes nothing
  that `ManagedBy=terraform` does not already say, and a column with one value is not an axis (Lesson 9).

**What this tag is not, and the name suggests otherwise:** it is not attribution evidence. A tag is written
by whoever creates the resource, so *who did this* is answered by CloudTrail's `userIdentity` — collected
org-wide since 1a step 5 — and never by `Owner` (Lesson 5). It is also **outside the forcing SCP**, which
requires `Environment` and `Project` and nothing else (1c step 7.8), so a resource provisioned by a service
on the project's behalf — a D26 blueprint role, the landing zone's own machinery — simply does not carry it
and nothing denies the call.

**Forward constraint from D35 — every `sandbox` token in this file is per business unit, not singular.**
`Sandbox` is the one account in the map that multiplies (one per business unit; N is 1 today), so six
things written here as singletons are really per-unit: the `<env>` token `sandbox`, the
`Environment=sandbox` tag value, the **`Owner=sso-group-data-scientists` tag value** — 1b step 2 already
names the per-unit form, `sso-group-data-scientists-<bu>` — the `terraform-live/sandbox/` tree, the
`awsds-infra-sandbox-<n>` SSO profile, and `make up`/`make down ENV=sandbox`. Everything else — Development, Staging, Production, Data Governance,
Identity, `org` — is structural and stays exactly as written.

**The per-unit token is an ordinal integer — settled by the user 2026-08-11, at the moment the first profile
was created.** `Sandbox Account 1` is reached through **`awsds-infra-sandbox-1`**; the second business unit's
account is `awsds-infra-sandbox-2`, and so on, with no gap-filling and no reuse of a retired number. D35
wrote the placeholder as `<bu>` — a business *unit name* — and this is deliberately not that. Two things the
ordinal buys and one it costs:

- **It matches the name AWS already shows.** The account is `Sandbox Account 1` in the organization, so the
  profile, the account and every console listing agree. A token derived from a unit name would be a second
  vocabulary for the same account, and the mapping between the two would live nowhere.
- **It cannot go stale.** A business unit can be renamed, merged or dissolved; anything named after it then
  carries a name nobody recognises, and renaming deployed resources is the cost this whole section exists to
  avoid. An ordinal has no meaning to lose.
- **What it costs, and it is a real duty rather than a footnote: the token carries no meaning.**
  `sandbox-2` does not say whose it is. So the **ordinal→business-unit mapping has to be written where a
  human reads it — `docs/ORGANIZATION.md`, at the vend** — or the ordinal is an index into a table that does not
  exist. [Stage 14](stages/stage-14-sandbox-vending.md) owns that duty; until N is 2 there is nothing to
  record and nothing yet lost.

**The `Environment` tag value is decided and it is *not* the ordinal — settled by the user, 2026-08-13.**
Every Sandbox account, at any N, tags `Environment=sandbox`. The enumeration above therefore stands exactly
as written, and 1c step 7.8's tag policy enumerates it with no ordinal anywhere. The reason is the failure
mode rather than the aesthetics: an enumerated value that does not admit a future unit turns the first
apply in a freshly vended account into an `AccessDenied` (Lesson 14), and per-unit cost attribution is
already available by **account** without spending an organization-policy edit at every vend.

**What is left to [Stage 14](stages/stage-14-sandbox-vending.md)** — alongside the CIDR allocation table
(Stage 3) and the VPN topology (Stage 4) — **is the directory shape and the `sandbox-unit` module's
interface, and no longer the token.** Guessing at the interface of a module that does not exist yet still
costs more than it saves; the token above stopped being a guess. **Which of the other five per-unit tokens
actually carry the ordinal is open** — `open-questions.md` item 10 — and it is open in the direction that
matters: `Environment=sandbox-1` is an enumerated value inside an SCP-forced tag policy (1c step 7.8), so it
is decided *before* that policy is written, not after. What this note fixes now is the cheaper half, and it
is the one that fails silently — **the two
enumerations above are Lesson 14 in naming.** The `<env>` list and the tag policy's allowed values both
enumerate `sandbox` — and since 2026-08-10 that policy enumerates `sso-group-data-scientists` for `Owner`
as well — while the forcing function behind the tags is an SCP conditioned on `aws:RequestTag` (1c step 7).
So an enumeration that does not admit a per-unit token turns the first apply in a freshly vended account
into an `AccessDenied` — discovered in a new account, by whoever is standing it up, which is the worst
possible place to find out about a naming rule. **`Owner` fails softer than `Environment` and in the same
place:** it is outside that SCP, so a value the policy does not admit is a non-compliant tagging operation
rather than a denied create — quieter, and therefore the one more likely to be found late. Write every list
so a per-unit token is admissible before it is needed.

**Terraform layout:**

Each slice carries its layer from §5.1: `[P]` persistent, `[D]` dormant (stop/start), `[E]` ephemeral.

**This tree is the authority and is deliberately in one place.** The folder's own
[`terraform-live/README.md`](../../terraform-live/README.md) explains *how the tree is organised* — the three
questions that decide where something goes, which profile applies which folder, what deliberately lives
outside it, and what exists there today — and points back here rather than repeating the tree. Two copies of
a directory listing drift, and the one that drifts is the one somebody reads first.

```
terraform-live/
├── identity/             # THE IDENTITY PLANE. TWO slices, not one (Stage 2 step 5): they
│   │                     # reach their objects through two DIFFERENT delegations, so they
│   │                     # are separated on that seam. Both applied with the
│   │                     # awsds-infra-identity profile; neither touches Management
│   ├── bootstrap/        # [P] state bucket for the Identity account
│   ├── sso/              # [P] permission sets, their policies and boundaries, and the
│   │                     #     group->account assignments. Reached through the IAM Identity
│   │                     #     Center delegated administrator (D10, sso.amazonaws.com),
│   │                     #     which Stage 1b step 1 already proves. SIX of the seven sets
│   │                     #     are WRITTEN here and were never typed into a console
│   │                     #     (Stage 1b step 3.9); the administrator set is imported.
│   │                     #     NOT here: users and groups - they are people, see "The
│   │                     #     identity seam" below. Control Tower's own sets and groups
│   │                     #     are NOT here either, nor the Account Factory direct
│   │                     #     assignments (D32): editing either is landing-zone drift
│   └── org-policies/     # [P] the SCPs, RCPs, the tag policy and the declarative policy.
│                         #     These are AWS ORGANIZATIONS objects and the Identity Center
│                         #     delegation does not reach them - they need a separate
│                         #     resource-based delegation policy written from Management
│                         #     (INT-20). Console-only and owned by nobody after Stage 1c,
│                         #     and since D30 was reverted no principal inside a governed
│                         #     account can work around a bad Deny, so this set needs a
│                         #     diff, a review and a rollback more than anything else here.
│                         #     NOT the region restriction: that is a Control Tower control,
│                         #     not a hand-written document (Stage 2 step 5.4)
├── sandbox/              # EXPERIMENTATION (D21): the unit of work is a notebook.
│   │                     # ONE OF THESE PER BUSINESS UNIT (D35) - the whole subtree
│   │                     # below is what Stage 14's sandbox-unit module composes
│   │                     # from a single input. N is 1 today; the naming is settled
│   │                     # there, not here (see the D35 note above)
│   ├── bootstrap/        # [P] state bucket for this account (state migrated in, never committed)
│   ├── foundation/       # [P] VPC, subnets, route tables, IGW, security groups, private
│   │                     #     hosted zone, KMS keys, IAM roles, WireGuard Elastic IP,
│   │                     #     peering requester + routes to Production (D14), and the
│   │                     #     persona's vending policy - a customer-managed policy the
│   │                     #     entitlement plane references BY NAME, so it lives in a [P]
│   │                     #     slice: a missing one fails PROVISIONING of the permission
│   │                     #     set in this account (2026-08-23, persona-vending.tf)
│   ├── data/             # [P] the derived zone (ONE bucket, three prefix families:
│   │                     #     results/, derived/${aws:userid}/, scratch/ - D19, and
│   │                     #     `scratch` is a PREFIX, per D13's own wording), its
│   │                     #     alias/awsds-<env>-data CMK (D31), the enforced Athena
│   │                     #     workgroup, this account's own DataLakeSettings, and the LF
│   │                     #     resource links + local re-grants to the Data Governance
│   │                     #     share (D22). ONE MODULE, consumer-data, shared with
│   │                     #     development/data/. The lake itself is NOT here
│   ├── lake/             # [P] the SANDBOX LAKE (Stage 16, APPLIED 2026-08-26):
│   │                     #     awsds-sandbox-lake, PERMANENT artifacts, one prefix per SSO
│   │                     #     group, mounted into SMUS projects via S3 connections and
│   │                     #     vended to laptops via S3 Access Grants. Deliberately neither
│   │                     #     the GOVERNED lake (no catalog object, no LF-Tag - D13's
│   │                     #     non-registered class) nor the derived zone (nothing expires
│   │                     #     here); the compensations are Stage 16's. Holds the bucket,
│   │                     #     the access role awsds-sandbox-lake-access and (its decision
│   │                     #     3) the Access Grants location + per-group grants; per-PROJECT
│   │                     #     grants are hand-made: runbooks/sandbox-lake.md
│   ├── egress/           # [E] NAT gateway, interface VPC endpoints - the metered network.
│   │                     #     Two variants behind a switch: D5(A) with NAT, D5(B) without
│   ├── probes/           # [E] Stage 3's measurement instruments (perimeter + peering),
│   │                     #     created and destroyed by make up/make down, ranked after
│   │                     #     egress/ so down tears them first
│   ├── vpn/              # [D] WireGuard EC2 (stopped, not destroyed) - and, since Stage 6
│   │                     #     step 5.0, the NAT INSTANCE for the isolated tier as well:
│   │                     #     vpc_nat_cidrs turns source/dest checking off and adds the
│   │                     #     masquerade rules buildbox/ routes traffic into
│   ├── buildbox/         # [E] the amd64 BUILD HOST for the dev-env image (Stage 6 step 5.0).
│   │                     #     Isolated tier, NO ingress rule at all (Session Manager needs
│   │                     #     none; the VPN-only requirement was withdrawn 2026-08-21),
│   │                     #     egress ONLY through vpn/ - no NAT gateway, so egress/ need
│   │                     #     never be up for a build. Driven by ./scripts/buildbox.py, not by
│   │                     #     make up: it must NOT coexist with probes/, whose perimeter
│   │                     #     reading is the absence of the default route this slice adds
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
│                         #     the VPC/subnet/AZ parameters handed PER REGION to EVERY blueprint
│                         #     configured in this account (`regional_parameters` over the enabled
│                         #     set - there is no "ML blueprint"; the per-project SageMaker AI
│                         #     domain comes from `Tooling`, and docs/SMUS.md is the one copy of
│                         #     the enabled list - Tooling alone adds S3Location/KmsKeyArn, the
│                         #     wizard-field set of 2026-08-22), the KMS key, the projects bucket
│                         #     awsds-<env>-smus-projects, the 11 CREATE_ENVIRONMENT_FROM_BLUEPRINT
│                         #     grants (layer 2 of the create authorization; layer 1 sits in
│                         #     governance/), and the D13 boundary policy attached
│                         #     to the project roles (INT-15). It does NOT declare the
│                         #     project environments themselves: DataZone owns those, and a
│                         #     Terraform resource for them would fight the blueprint.
│                         #     APPLIED 2026-08-21, and it APPLIES TWICE: the second apply
│                         #     adds the BLUEPRINT CONFIGURATIONS, which live here and not
│                         #     in governance/ because PutEnvironmentBlueprintConfiguration
│                         #     takes no account parameter - it configures the CALLER's
│                         #     account, which is why an associated account is what enables
│                         #     blueprints against a shared domain. The flag is
│                         #     backend.SMUS_ASSOCIATED, whose rows are measurements
├── development/          # DEVELOPMENT (D21): the unit of work is a pipeline
│   ├── bootstrap/        # [P] state bucket for the Development account
│   ├── foundation/       # [P] VPC (own CIDR), KMS, IAM roles, peering requester to
│   │                     #     Production - Studio here must reach GitLab (INT-09) - and
│   │                     #     the same persona vending policy as sandbox/foundation/,
│   │                     #     byte for byte: one NAME, one object per member account
│   ├── data/             # [P] the same consumer-data module as sandbox/data/, byte for
│   │                     #     byte: derived zone + its CMK + workgroup + settings + links
│   ├── egress/           # [E] NAT + endpoints, same D5 switch as sandbox
│   ├── probes/           # [E] Stage 3's instruments here: INT-09 reachability + the DNS half
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
│                         #     first target is Staging
├── data-governance/      # THE OWNERSHIP AXIS (D22, D26): state and governance,
│   │                     # never compute. Renamed from data-management/ on 2026-08-08
│   ├── bootstrap/        # [P] state bucket for the Data Governance account
│   ├── data/             # [P] raw/curated S3 (Iceberg), Glue Data Catalog, Lake Formation
│   │                     #     registrations + LF-Tags (D13), ingestion drop-box (D18),
│   │                     #     cross-account shares to sandbox/development/production,
│   │                     #     Glue Crawlers on raw + drop-box under the D27 exception
│   │                     #     (config is free at rest; runs are metered, event-driven)
│   └── governance/       # [P] the SageMaker unified domain (DataZone V2, D26) - APPLIED
│                         #     2026-08-21. VERIFICATION (ii) ANSWERED: the aws-ia module
│                         #     was NOT consumed. Its root requires vpc_id/subnet_ids and
│                         #     enables the Tooling blueprint IN THE DOMAIN ACCOUNT, which
│                         #     is what D22 forbids - and the resources are five, so
│                         #     writing them directly was cheaper than splitting a module
│                         #     that assumes a single account. The provider split the old
│                         #     text predicted is right and stands: domain + IAM through
│                         #     `aws`, project profiles AND the CREATE_PROJECT_FROM_PROJECT_PROFILE
│                         #     grants on the root unit (grants.tf, applied 2026-08-22 - layer 1
│                         #     of the create authorization) through `awscc` (the only provider
│                         #     with awscc_datazone_project_profile at all).
│                         #     Account associations to sandbox and development (INT-12)
│                         #     are CONSOLE-ONLY - no public API - and the blueprint
│                         #     CONFIGURATIONS are not here either: they are applied from
│                         #     the MEMBER account (see */sagemaker/ below).
│                         #     A registry: blueprints provision compute into those
│                         #     accounts, never into this one. No foundation/ slice: no
│                         #     VPC, no user compute, nothing standing - which is also why
│                         #     INT-13 has no host
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
    │                     #     their cross-account associations (D15 as revised 2026-08-09),
    │                     #     and GitLab's [P] anchors - the object-storage and backup
    │                     #     buckets and the gitlab-secrets container (Stage 7 step 1.1):
    │                     #     the restore path must survive tooling/'s destruction, the
    │                     #     same argument that put the WireGuard EIP in Sandbox's
    │                     #     foundation. NO public zone, NO registered domain: those are
    │                     #     Stage 13, and NOT the CA - see pki/ below
    ├── pki/              # [P] the internal root CA (D36). OWN state file and OWN KMS key,
    │                     #     deliberately not foundation/'s: foundation is opened to change
    │                     #     a CIDR or accept a peering, and every such edit would otherwise
    │                     #     decrypt the root. Applied at STAGE 7 PASS 1, with the leaves -
    │                     #     the "applied EARLY, before Stage 6" schedule was withdrawn on
    │                     #     2026-08-21 (D36 3 amended): nothing serves a .internal name
    │                     #     before Stage 7, so the dev-env image takes the root at Stage 7
    │                     #     step 2.6 instead (INT-19). Its state key already exists, in
    │                     #     production/bootstrap/ since 2026-08-15. Outputs the CA cert and
    │                     #     the issued leaves - NEVER the root private key. Excluded from
    │                     #     every make down path
    ├── data/             # [P] application-output buckets, Athena workgroup, LF resource
    │                     #     links + the governed-write REGRANT to the job role (D22; the
    │                     #     account-level grant is data-governance/data/'s - Stage 9
    │                     #     step 2's two-step). The lake itself lives in
    │                     #     data-governance/. The registries are NOT here - see below
    ├── registry/         # [P] ECR (+ pull-through cache) and CodeArtifact (D14), with their
    │                     #     OWN KMS key and consumer account ids from a map. Split out of
    │                     #     data/ on 2026-08-09 to preserve D14's revision option: if the
    │                     #     supply chain ever moves to a Shared Services account, this
    │                     #     slice leaves and data/ stays. A folder is not a boundary - it
    │                     #     buys migration cost only (Stage 7, option-preservation note).
    │                     #     APPLIED IN TWO PASSES, split by consumer on 2026-08-21: the
    │                     #     base/dev-env repositories, CodeArtifact, the key and the
    │                     #     consumer policies (Stage 7 step 5.a) go in at STAGE 6's pass 0,
    │                     #     because Stage 6 step 5.0 pushes into them; the pull-through
    │                     #     cache and the per-application repositories (5.b) wait for
    │                     #     Stage 7, which is the first thing that pulls from either.
    │                     #     THE 5.a HALF IS APPLIED (2026-08-21, 14 resources)
    ├── sagemaker/        # [P] Model Registry (model package groups) + the execution role
    │                     #     pipeline-submitted jobs assume. No domain, no user profiles (D17)
    ├── egress/           # [E] NAT, endpoints - and the internal ALB for GitLab/Pages ONLY
    │                     #     if Stage 7 decision 1 picks it over nginx-on-instance (an
    │                     #     ALB cannot stop, so if it exists it is [E])
    ├── probes/           # [E] Stage 3's instrument here: the peering target
    ├── tooling/          # [D] GitLab EC2 + EBS (D8, D14) - TLS terminates on its own
    │                     #     nginx, or on the egress/ ALB (Stage 7 decision 1)
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

terraform-modules/        # reusable modules (the roster and its tags: terraform-modules/README.md)
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
per-project SageMaker AI domain that the `Tooling` blueprint provisioned into the account, so the teardown is
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
- Region, AZs and AMIs follow the portability rules in `docs/plan/architecture.md` §4.1 — no region literals in `.tf` files.
- Authentication through named SSO profiles, one per Terraform-managed account — `awsds-infra-sandbox-1`,
  `awsds-infra-dev`, `awsds-infra-data`, `awsds-infra-staging`, `awsds-infra-prod`,
  `awsds-infra-identity` (Stage 1b step 5) — never keys. **The sandbox one is ordinal-suffixed and there is
  one per business unit** (D35): `-1` today, `-2` when the second unit is vended. The other five are
  structural and carry no suffix.
- Every slice: `terraform fmt`, `validate` and `plan` must be clean before apply.
- Remote state read across slices through `terraform_remote_state` data sources, never hardcoded IDs.
- **The Organization is never in Terraform, and the code is written to survive that (D34).** Accounts and
  OUs are created from the console, by design (principle 1), so no state declares them and none of it can
  drift. What it *can* do is leave a console-created OU or account outside code that was written as a list —
  invisible rather than drifted, with `terraform plan` reporting "No changes". So, across the two identity
  slices: **the floor is discovered, the grants are enumerated.** Anything that must cover everything —
  the organization-root SCP/RCP set, the tag policy, the declarative policy, all in
  `identity/org-policies/` — has to be covered *whatever* exists tomorrow; permission set assignments, in
  `identity/sso/`, are written out one by one, because an account acquiring a grant by simply existing is
  the opposite of the intended failure mode. **The split runs along the same seam** — discovered on one
  side, enumerated on the other — which is a second reason to keep it.
  **What "discovered" turned out to mean — corrected 2026-08-15, after Stage 1c was executed.** This rule
  was written expecting `for_each` over the `aws_organizations_*` data sources to *create the attachments*.
  1c attached every must-cover-everything document to the **organization root** instead, and SCPs inherit —
  so a new OU or account is covered the moment it exists, with no attachment to create. The four **per-OU**
  documents are all *different*, and three OUs deliberately carry **none** (`Policy Test`, `Security`, and
  `Sandboxes` under D37), so a `for_each` attaching "the OU document" everywhere would put one on
  `Sandboxes` and reverse a decision with `terraform plan` reading like ordinary coverage. **So: coverage is
  bought by the attachment point, and discovery is spent on the *check*** — `make check` enumerates the OUs
  at both levels and fails on one that appears in neither the authored OU→document map nor its explicit *no
  document* list ([Stage 2](stages/stage-02-terraform-foundation.md) step 9.3). The failure mode this rule
  exists to prevent is unchanged; what changed is which instrument prevents it.
  **What "enumerated" means once the Sandbox multiplies (D35), because the obvious reading forbids
  something it should not:** a `for_each` over a **human-authored map of business units**, kept in a
  `.tfvars`, is still enumeration — a unit acquires its assignment because somebody wrote its name down, not
  because an account appeared. What the rule forbids is `for_each` over a *data source*: an assignment
  keyed on `data.aws_organizations_organization.accounts` grants by discovery, and that is the failure mode.
  Stage 14 generates a unit's group and assignment from that same map.
- Modules are referenced by **git tag**, never by branch, so a module change cannot silently alter an
  existing deployment.

**The identity seam — what goes in Terraform, and the rule that keeps it true at any headcount:**

**Nothing whose count grows with the number of people belongs in Terraform.** The line runs between a
*person* and an *entitlement*, and it is drawn here rather than in a stage file because it has to survive
every stage:

| | Person-shaped | Entitlement-shaped |
|---|---|---|
| What | Identity Center **users**, **groups**, and group **memberships** | **permission sets**, their inline or customer-managed policies, **permissions boundaries**, and **group→account assignments** |
| How many | grows with headcount — hundreds of data scientists, a dozen `dev-env` stewards | fixed by the design: seven sets, and O(groups × accounts) assignments |
| Where it lives | the directory. Console at lab scale (four users, Stage 1b step 2); **SCIM from the corporate IdP** in any real deployment | `terraform-live/identity/sso/` (Stage 2 step 5) |
| Why not the other way | Terraform would become the HR system, with personal data in a state file and joiners/leavers as merge requests | a console-only entitlement has no diff, no review and no rollback |

Five rules follow, and each has a failure mode that is silent:

- **An Identity Center group is named `sso-group-<persona>`.** All five are: `sso-group-infrastructure`,
  `sso-group-data-scientists`, `sso-group-deployment-managers`, `sso-group-governance-managers`,
  `sso-group-dev-env-stewards`; a per-business-unit Sandbox group is `sso-group-data-scientists-<bu>`
  (D35, Stage 14). **The prefix separates two sets of same-named objects, and that is what it is for:**
  Control Tower's own groups on one side (`AWSControlTowerAdmins`, `AWSAccountFactory`, the auditor and
  per-account groups — never to be joined or repurposed), and, from Stage 7, **GitLab groups that mirror
  these personas 1:1 and deliberately do *not* carry the prefix** — `deployment-managers` and
  `dev-env-stewards` in GitLab are where the two approval gates actually live, and they are different
  objects in a different system. So a bare `deployment-managers` in this repository means the GitLab group
  and a prefixed one means the directory; before this rule the same token meant both.
  **The exactness matters mechanically, not just editorially:** assignments resolve their principal by
  **display name** through `data.aws_identitystore_group` (rule 3 below), so a name written one way in the
  plan and another way in the directory is a `terraform plan` that fails — or, worse, a second group
  someone creates to make the error go away.
- **A permission set is named `<Persona>Access`, and never within four characters of a Control Tower set.**
  All seven are: `InfrastructureAccess`, `DataScientistAccess`, `DataScientistStagingAccess`,
  `DataScientistProdAccess`, `DeploymentManagerAccess`, `GovernanceManagerAccess`, `DevEnvStewardAccess`.
  Two things follow from the shape. **It names the group, not the permission level** — a set called after a
  level invites reuse by a second principal, and the `AdministratorAccess` exception below is meant to be
  read narrowly. **And a near-miss with a Control Tower set is a silent fault, not an aesthetic one:** the
  administrator set was to be `AdministratorAccess`, four characters from Control Tower's
  `AWSAdministratorAccess`, and an assignment made against the wrong one still works while the two
  `AWSReservedSSO_*` ARNs differ only in a prefix nobody reads carefully (Stage 1b step 3.2, 2026-08-10 —
  the ARN is the evidence in step 5 and the precondition of step 5.1, so this collision would have degraded
  the one check standing between the operator and a lockout).
- **Assign a permission set to a group, never to a user.** A group assignment is one object no matter how
  many people are in the group; a user assignment is one per person, created one API call at a time. The
  one exception is Account Factory's own direct assignment to the infrastructure user (D32), which is
  documented rather than copied.
- **Resolve a group by display name, never by GUID** — `data.aws_identitystore_group`, not a pasted ID.
  Group IDs are properties of *one* directory instance: replace the identity source, which is exactly what
  federating to a corporate IdP does, and every hardcoded ID becomes a resource that matches nothing.
  Stage 1b step 8.3's alarm makes the same choice for the same reason, from the other side.
- **The number of people never appears in a resource count.** If a design change makes it appear — a
  per-person prefix, a per-person role, a per-person assignment — that is the signal to move the
  multiplication into a group or a boundary. D19's per-principal derived prefixes are the one deliberate
  exception, and they are bounded by a lifecycle rule rather than by headcount.

**One resource that must never be declared in any slice:** `aws_s3_account_public_access_block`. The
account-level setting is made by hand in Stage 1c step 7.4, and Stage 1c step 7.5 then denies
`s3:PutAccountPublicAccessBlock` — so an apply or a drift correction that touches it fails. It reads like
something that belongs in `foundation/`, which is exactly why it is written down here.
**The 2026-08-13 carve-out does not soften this and would make it worse if read as permission.** The deny
exempts exactly the principal Terraform runs as, so an apply declaring this resource would *succeed* — and
the setting would then have two owners, a hand-made one and a state file, with drift correction able to
turn the blanket off in an account the module never touches. The rule is unchanged: it is not declared.

**IAM rules** (these are conventions because they are easy to violate one role at a time):

- Every role that a non-administrator can create or influence carries a **permissions boundary**.
- `iam:PassRole` is never granted unqualified. It is always scoped by `iam:PassedToService` and by resource
  ARN. `PassRole` plus a job-creating API (`sagemaker:CreateTrainingJob` is the relevant one here) is a
  privilege-escalation path: it lets a user run code under any role they are allowed to pass.
- Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now". The starting point of a permission set
  is narrow, because loosening a permission is a five-minute change and tightening one is a negotiation.
  **One exception exists and it is named rather than tacit: the `sso-group-infrastructure` group** (D32;
  `docs/ORGANIZATION.md`, "The limit of the separation of duties"). It holds **`InfrastructureAccess`** — the one
  permission set that attaches `AdministratorAccess` — on every
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
  is checked by **`make check`** (Stage 2 step 9.2) — there is no CI before Stage 7 — moving into the
  pipeline at Stage 8.
  **One exception exists, it is named rather than tacit, and the check has to know it by name** (decision 7,
  2026-08-13): the `Sid` that carves `InfrastructureAccess` out of the organization-root deny on
  `s3:PutAccountPublicAccessBlock` (1c step 7.5). It must reach accounts that **do not exist yet** — the
  Identity Center role ARN carries a per-account random suffix, so the accounts that matter most cannot be
  enumerated even in principle. The residual it admits is bounded: minting a role that matches the pattern
  requires `iam:CreateRole` in that account, which is administrator, which is the identity the carve-out
  already names. **A second exception is a decision, not a precedent** — and `make check` failing on this
  one `Sid` is the check working, so whitelist it explicitly rather than loosening the rule.
- **In a deny keyed on a *resource* condition, the action list is enumerated and every action in it must
  populate that key — never an action wildcard** (found 2026-08-13, writing 1c step 7.5's perimeter
  document). This is the mirror image of the rule above, and it is the more dangerous of the two because it
  fails *closed* over something legitimate rather than open. A negated or `IfExists` condition **evaluates
  true when the key is absent**, so a `Deny` conditioned on `aws:ResourceOrgID` catches every action that
  carries no resource for the key to come from. `s3:Put*` therefore reaches
  **`s3:PutAccountPublicAccessBlock`**, which is account-level: the perimeter document would deny, in every
  account at once and for *every* principal, the exact call 7.4 depends on — and the decision-7 carve-out
  would not save it, because that carve-out lives in a different statement in a different document. The same
  applies to `ecr:GetAuthorizationToken`, which is registry-scoped and is left out of the ECR half of the
  same statement for exactly this reason. **So enumerate object- and repository-scoped actions**, and when
  the temptation to future-proof with a wildcard returns, note that the failure it buys is silent until
  somebody vends an account.

### Application repository layout

The template for an application written by a data scientist and intended for deployment, consumed by
[Stage 8](stages/stage-08-cicd-pipelines.md) (the three pipeline types) and
[Stage 10](stages/stage-10-orchestration-promotion.md). It lived in `CLAUDE.md` until 2026-08-09, which put
a Stage 8 artifact in the file loaded on every session:

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

The development stack is similar to <https://github.com/felipenoris/etl-cookbook-tutorial>. Note that the
application's own `terraform/` directory is the *source* of a slice; what is applied is the
`terraform-live/<env>/app/app-etl/` slice above, which is `[E]` in every environment.

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
requests and storage; the per-project SageMaker AI domain that the `Tooling` blueprint provisions likewise bills
nothing until an app runs). Rule 2 below records why it moved out of `[E]`.
The domain is also where the *catalog* lives — glossary, data products, subscription decisions — which is
state in the rule-2 sense and on its own settles the layer question.

**[D] Dormant — kept, but powered off between sessions.** Stateful services where a rebuild is riskier
than the idle cost: the GitLab EC2 instance and its EBS volume, and the WireGuard instance. `make down`
stops them, `make up` starts them. Idle cost is their EBS volumes (~USD 4.65/month) plus the Elastic IP,
which stays associated across a stop/start (and bills while stopped) — the address itself is allocated in
`[P]`, so it survives even if the instance is replaced. This is what makes the Stage 7 backup/restore cycle a disaster-recovery procedure
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
2. No state lives only inside an `[E]` resource — enforced by construction: the stateful resource that
   would otherwise be `[E]` is in `[P]` for exactly this reason. The Studio domain used
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

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
