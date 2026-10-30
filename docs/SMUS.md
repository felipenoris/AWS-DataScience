# SageMaker Unified Studio — the object model, blueprints, configuration

What the SMUS/DataZone-V2 surface is made of, read from the terminology page and the project-profile
admin pages ([`REFERENCES.md`](REFERENCES.md), beside the 2026-08-16 documentation-pass block). Prices
quoted are the measured ones from [`PRICING.md`](PRICING.md) (Lesson 6 — a cell without a number means
*not measured yet*, never *free*). The blueprint categories are the user's decision of 2026-08-19 —
Stage 6 decisions 4 and 5, recorded in [the stage log](log/log-stage-06a-unified-studio.md);
`./aws/studio.py`'s `US-3` measures them.


**The domain has one associated account outside Stage 18's window.** `Development` became the headless `Staging` at
[Stage 6b](plan/stages/stage-06b-development-becomes-staging.md) on 2026-09-06, so its eleven blueprint
configurations, its eleven authorization grants and the `engineering` project profile are all unwound,
and the associated-account count is **N Sandboxes** rather than N + 1 (D26 amended). One project profile
survives, `experimentation`, pinned to Sandbox. Stage 18 associates `Staging` as well, from 2026-10-19 to
that stage's pass 8, for one deployment project born of a second profile, `deployment`.

## The object model — domain, project, and the profiles between them

Definitions quoted below are the documentation's wording, read 2026-08-19.

### Domain

The domain **is** the SMUS instance: "the organizing entity for connecting together your assets,
users, and their projects" — one portal URL (AWS-issued; D15 phase 1 needs no domain of ours), one
sign-on wiring (IdC here), one **SageMaker Catalog**, whose scope is the domain: what a project
publishes is discoverable by every project in the domain, and by nothing outside it. Mechanically it
is `aws_datazone_domain` with `domain_version = "V2"` — without that argument the same resource
creates plain DataZone (V1), which is *not* Unified Studio ([`GLOSSARY.md`](GLOSSARY.md)).

Properties this design leans on:

- **A domain is a registry, not a runtime.** It holds projects, profiles, blueprint configurations and
  the catalog; all compute comes from blueprints, and no blueprint is enabled in the domain account but
  the lake-publishing pilot's `Tooling`, with spaces off ([Stage 6f](plan/stages/stage-06f-data-governance.md)
  step 11, D22 amended 2026-10-26; configured 2026-10-26, 11.3). The domain lives in `Data Governance`, where
  `sagemaker:Create*` is denied (1c step 7.6) — a denial that stays free because of this split (Stage 6
  step 0.4), and because the pilot's profile locks `enableSpaces` to `false`.
- **Member accounts join by *account association*** — console-only (**no public API**, read
  2026-08-16): a RAM share DataZone initiates. Sandbox alone is associated since 2026-09-06 — the
  second association was removed from the member side at Stage 6b step 1.4; **Staging and Production
  never are** (D28), Staging's association for Stage 18's measurement aside: since 2026-10-19, with
  `Tooling` its one blueprint configuration (`EXC-20`), until that stage's pass 8. Measured 2026-08-21: under Stage 1d's org-wide RAM enablement the share is created
  organization-scoped and **auto-accepts**, zero invitations either side, so *"invitations expiring in
  7 days"* names a clock that never starts.
- **The domain and IdC must share a Region** (Stage 6 step 1.1) — `us-west-2` twice, and neither can
  move afterwards.

Inside a domain, **domain units** subdivide it: assets and authorization policies (project creation,
project membership, environment-profile creation, glossary creation, …) can be organized and granted
at domain-unit grain. Nothing in this plan creates one — the admission control this design needs
rides on the two project profiles and the IdC groups.

**The name trap:** the per-project **SageMaker AI domain** the Tooling blueprint provisions in the
member account is the classic Studio object — apps, spaces, EBS volumes — and shares nothing with
the SMUS domain but the word. One SMUS domain ↔ many projects; each project ↔ its own SageMaker AI
domain.

### RAM under this surface

RAM is AWS **Resource Access Manager** — the cross-account sharing service, never memory
([`GLOSSARY.md`](GLOSSARY.md) owns the definition). It is the machinery under two SMUS seams:

- **Account association *is* a RAM share** the domain initiates on your behalf, which is why there is
  no public API for it. Measured 2026-08-21: the permission is
  **`AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`**, and
  `AWSRAMPermissionDataZoneDefault` **does not exist in RAM at all** — a name copied out of the V1 user
  guide's prose, while `ram list-permissions --resource-type datazone:Domain` publishes six, none of
  them called that. It carries **152 actions against the resource-type default's 111**, the extras
  being the SMUS **V2** workbench surface (notebooks, cells, compute, connections,
  `GetDomainExecutionRoleCredentials`). There is **no invitation to expire**: the share is
  organization-scoped, so it auto-accepts, the same behaviour the LF shares below show. **Read that
  permission as a ceiling on the share, never as access** (Lesson 28); what any principal can do is
  that ∩ its IAM ∩ the SCPs, and the Interactive OU carries no `datazone:` deny — open question 21.
- **Cross-account catalog access rides Lake Formation cross-account sharing, which rides RAM.** The
  substrate is already exercised: Stage 5a's TBAC shares are RAM shares, measured at INT-11's close
  as 4 `ACTIVE` with **0 invitations** in both consumers — the zero comes from Stage 1d step 11's
  `ram enable-sharing-with-aws-organization`. Without the org-wide enablement, every recreated share
  is a hand-accepted invitation (INT-11's fallback column prices that tax). A catalog subscription
  fulfilled across accounts lands on this same path.
- The organization half lives in Management: `ram.amazonaws.com` is a trusted-access principal, with
  `AWSServiceRoleForResourceAccessManager` (INV-09).

### Project

The unit the data scientist inhabits. The docs give it three capabilities, in their words: "business
context for the user's work", "a collaboration boundary", and "a permissions boundary which gives
users access to all the project artifacts and data/compute permissions after the users are added". A
domain holds several projects; a user can sit in several; the creator becomes the first **owner**, and
owners add **members** (owners or contributors). Artifacts stay inside the project unless published to
the catalog.

What a project physically *is* in the member account is whatever the blueprints its profile bundles
have provisioned: the SageMaker AI domain and its apps (Tooling), the project roles, the
consumer-side Glue database and Athena workgroup (`DataLake`), the project S3 path (§S3 below), the
file storage.

The console states: "Projects do not provide strong security isolation. To limit cross-domain and
cross-project resource discovery you can consider creating projects in separate accounts." That is
what the two profiles pinned to two accounts do (D21/D35): the *account* boundary carries the
isolation the project boundary does not.

### The project's "permissions boundary" — grant-shaped, and a name collision

The third capability in the definition above is a boundary of **membership**: being added to the
project is what *grants* — the project roles' powers, and the data the project subscribed to. It is
a concession mechanism wearing a restriction's name, and what it natively restricts is thin:

- the member's **designation** — owner vs contributor, and since 2026-10-29 a **custom designation**, a
  Cedar permit policy over the project's actions the domain defines (`CreateDesignation`;
  [`upstream-releases.md`](plan/upstream-releases.md)); `awsds-studio` holds the two managed ones alone
  (read 2026-10-30) — plus the domain's authorization policies over who creates projects, who joins, who
  assumes ownership;
- the **surface** — inherited from the profile: which blueprints exist, which parameters are locked.
  The member does not choose it; it came with the mold;
- **which assets the project reaches** — every catalog asset crosses a subscription request approved
  by the producer project. Membership ≠ access to the domain's data.

What it does not hold is the isolation sentence quoted above, so every restriction this design counts
on lives *outside* the project object, in layers whose intersection is the answer (Lesson 28):

| Layer | The control |
|---|---|
| the **IAM permissions boundary** — the literal object | `awsds-<env>-project-boundary` (Stage 6 step 2.1; name contract `US-8`), imposed on the roles the blueprint authors: no `s3:*` on LF-registered prefixes (D13), the drop-box `PutObject` + lake-data-key KMS pair as the one sanctioned direct write. **Measured 2026-08-22: it is on the provisioned role** — the configuration's write-only field is injected into the environment's stack template as the `ToolingUserRole`'s `PermissionsBoundary` (the conditional Bedrock roles too; **the template's two conditional EMR roles carry none** — AWS's template, the recorded gap for the day EMR-in-Tooling turns on). Whether it **survives blueprint reconciliation** is INT-15's remaining half, measured at step 2.5 — `US-8` reads it per role via `get-role` (`list-roles` omits the field by contract, Lesson 30) |
| OU SCPs | reach every IAM principal in the member accounts, project roles included — why the Athena Spark disable is an SCP (step 1.6), never an edit to blueprint-authored policies (Lesson 11) |
| Lake Formation | what a project *queries* is governed by LF grants, not IAM — broad IAM with no grant reads no table (Lesson 28's producer-README section) |
| network | `VpcOnly` non-Editable, the endpoint policies, both egress designs (§`VpcOnly` below) |

**The name collision:** the docs' "permissions boundary" (membership, above) and the IAM *permissions
boundary* ([`GLOSSARY.md`](GLOSSARY.md): a policy capping what a role can ever be granted) are two
objects sharing three words. The D13 control is the IAM one; "the project's permissions boundary"
without qualification is ambiguous.

### Project profile

"A template for projects … a collection of blueprints, which are configurations used to create
projects. A project profile can define if a particular blueprint is enabled during the creation of
the project, or available later for the project users to enable on demand." Domain-admin-only,
created in the domain account (Stage 6 step 1.5).

Validation, measured 2026-08-22 (Lesson 39): **`CreateProjectProfile` validates nothing against the
blueprint templates** — a locked value the template rejects sails through and dies at the first deploy
— while **`UpdateProjectProfile` validates required template parameters without defaults**. The
templates are downloadable by any associated account via the blueprint's `templateUrl`, so locked
values are checked against the template, never against prose (Lesson 38).

What a profile fixes, per the custom-create console flow (read 2026-08-19):

| Field | What it fixes |
|---|---|
| the blueprint set | which capabilities projects born of it can ever exercise — carried as environment configurations, § below |
| account and Region | pinned per profile, **or** deferred to project creation (all associated accounts, or *account pools*). Here: pinned — `experimentation` → Sandbox. *(`engineering` → Development existed until 2026-09-06; the profile was destroyed at Stage 6b step 1.1 and the account converted.)* |
| Tooling deployment settings | the parameter surface step 1.5 locks: `sagemakerDomainNetworkType = VpcOnly`, idle shutdown, `maxEbsVolumeSize`, TIP (decision 2) — **non-Editable** (Lesson 5: the *Editable* flag is what turns a default into a control) |
| project files storage | Amazon S3 or a Git repository (§S3 below) |
| authorization | which users/groups may create projects from it — grantable domain-wide or per domain unit |
| readiness | a profile can exist disabled, to be customized before anyone can instantiate it |

The two profile names are a contract with `./aws/studio.py` (`US-4`).

### Environment configuration

The per-blueprint entry *inside* a project profile — the grain the `CreateProjectProfile` API takes.
Each one names the blueprint it exercises, the target account and Region, a **deployment mode**
(*on create*: provisioned the moment the project is born; *on demand*: sits in the portal until a
project member enables it — the API spelling of the enabled-vs-available distinction in the profile
definition above), and the blueprint's parameters, **each with its own Editable flag**. One profile
holds one per blueprint it bundles. Both SMUS levers this project pulls live at this grain: *which
account* a project provisions into, and *which parameters* its creator can no longer change.

### Environment — and the V1 "environment profile"

An **environment** is what exercising one blueprint leaves behind: the provisioned resource set for
one project × blueprint × account. The portal shows it inside the project; the resources are real,
in the member account. Conventions §6's rule follows: the `sagemaker/` slices declare *prerequisites
only, never a project environment* — DataZone owns environments, and a Terraform resource for one
would fight the blueprint (Stage 6 step 2.1).

An **environment profile** is the *DataZone-V1* template: one blueprint × account × parameters,
created within a project, from which project members then created environments by hand — the flow
`aws_datazone_environment_profile` / `CreateEnvironmentProfile` serve. In V2 that role moved into
the project profile's environment configurations — the choice of surface moved from the project
member (after creation) to the domain admin (before). The entity survives in V2's authorization
model (a blueprint configuration carries "create environment profiles using this blueprint"
policies, grantable to projects and to domain-unit owners) but nothing in this plan touches it. The
practical rule has Lesson 32's shape: **material speaking "environment profile" is V1-flow
material** — for this V2 domain the object to write is the project profile
(`awscc_datazone_project_profile`, in `terraform-live/data-governance/governance/profiles.tf`,
Stage 6 step **1.5**).

### The chain

blueprint (AWS-owned template)
→ **blueprint configuration** — enabled per domain × member account, naming the provisioning role,
the manage-access role and the VPC parameters (step 1.4)
→ **environment configuration** — a project profile bundles it: account, Region, mode, locked
parameters
→ **project profile** — the template an authorized user instantiates (step 1.5)
→ **project** — the registry object in the domain
→ **environment** — the provisioned resources in the member account, one per exercised blueprint.

| Object | Written by | Lives in | In this design |
|---|---|---|---|
| blueprint | AWS | the service | the 23 in the table below (custom blueprints are made with `CreateEnvironmentBlueprint`, and since 2026-10-09 one with the `TOOLING` category can be a profile's base, [`upstream-releases.md`](plan/upstream-releases.md); outside decision 5, so outside `US-3`'s allow-list; the domain held none on 2026-10-18) |
| blueprint configuration | Terraform, per member account (1.4) | domain × account | category 1's **thirteen**, in one account: eleven applied 2026-08-21 in Sandbox and in Development, Development's 22 objects (11 configurations and their 11 grants) destroyed 2026-09-06, and `MLflowApp`'s and `AmazonBedrockKnowledgeBase`'s applied in Sandbox 2026-10-19 (Stage 17 1.3 and 7.0b). `Tooling` in Data Governance, from `data-governance/publishing/`, is Stage 6f step 11's (applied 2026-10-26, 11.3) |
| project profile + its environment configurations | domain admin (1.5) | the domain | `experimentation`, `engineering` |
| project | an authorized user, in the portal | the domain (registry) | step 2.4's throwaway first |
| environment | DataZone, through the provisioning role | the member account | read back by `US-8` / step 2.5 |
| environment profile | the V1 flow | — | none, by design |

### The installed profiles

The project profiles this installation carries, each `ENABLED` and read back by `US-4`: `experimentation`
created 2026-08-21 by the second apply of `terraform-live/data-governance/governance/` (step 1.5), the
model governance profile on 2026-10-19 (Stage 17 decision 13):

| Profile | Provisions into | The unit of work (D21) | Who may create from it |
|---|---|---|---|
| `experimentation` | **Sandbox** | a notebook — experimentation happens where nothing downstream depends on it | `sso-group-data-scientists` |
| `Generative AI model governance` | nothing: no environment configuration; the console creates one custom environment per enabled model, in the model's account | the project `GenerativeAIModelGovernanceProject`, which owns the Amazon Bedrock model listings the console publishes | Terraform's identity, the root domain unit's owner; Sandbox's InfrastructureAccess is a `PROJECT_CONTRIBUTOR` through its session group |
| ~~`deployment`~~ | ~~**Staging**~~ | **Destroyed 2026-10-22** (Stage 18 step 8.2), at the end of that stage's window: its verdict kept D41 item 2, so no project provisions into a deployment account | — |
| `lake-publishing` | **Data Governance**, the domain's own account | the lake's published tables: `Tooling` alone, `enableSpaces` `false` locked, no compute. Stage 6f decision 1's pilot, behind `LAKE_PUBLISHERS`, applied 2026-10-26 (11.3); its project `governed-lake` created the same evening (11.4) | `sso-group-governance-managers`; its one project, `governed-lake`, is the Governance Manager's |
| ~~`engineering`~~ | ~~**Development**~~ | **Destroyed 2026-09-06** (Stage 6b step 1.1). The account it targeted became the headless `Staging`, and the chain now starts at a repository rather than an account | — |

Identical in everything but the target account: **eleven environment configurations** (decision 5's
category 1; `experimentation` holds **thirteen** since 2026-10-19, `MLflowApp` and `AmazonBedrockKnowledgeBase` `ON_DEMAND` at orders 11 and 12), `Tooling` the only base — `ON_CREATE`, every other blueprint `ON_DEMAND`; a second base
cannot ride along on demand, which is what re-cut `ToolingLite` to category 3 (its row in the
blueprint table below) — and the same Tooling parameters, read back after the apply. Since 2026-08-22
both profiles also declare the only two required-no-default blueprint parameters across the eleven
(`S3Bucket.bucketName`, `S3TableCatalog.catalogName`, both consumed by literal `Ref`) as **editable
placeholders** (`changeme-project-bucket`, `changemecatalog`) that the member replaces per project at
capability-enable time: `UpdateProjectProfile` demands them declared even though
`CreateProjectProfile` does not.

| Parameter | Value | Editable |
|---|---|---|
| `sagemakerDomainNetworkType` | `VpcOnly` | no |
| `lifecycleManagement` | `ENABLED` | no — the template's AllowedValues are the enum `ENABLED`/`DISABLED`; the boolean `"true"` was rejected by CloudFormation at the first deploy on 2026-08-22, `CreateProjectProfile` having validated nothing (Lesson 39) |
| `idleTimeoutInMinutes` | `60` | **yes** — the per-project default a member may tune, under the ceiling |
| `maxIdleTimeoutInMinutes` | `120` | no — the admin ceiling (step 8.1) |
| `maxEbsVolumeSize` | `100` (GB) | no |
| `enableTrustedIdentityPropagationPermissions` | `false` | no — decision 2, delivered |

#### Who may create a project, and from which profile

The fourth column is a separate object from the other three. A project profile is a *template*;
creating a project from it is an **authorization**, granted on a domain unit and named
`CREATE_PROJECT_FROM_PROJECT_PROFILE`. Listing the profiles is a read and needs neither; the portal's
*Project profiles* page left on 2026-10-20, the console's domain page lists them, and the creation form still
offers them.

**Measured 2026-08-22, in step 1.7's portal sitting:** the portal offered both profiles and the
button returned `User is not permitted to perform operation: CreateProject`, identical with the
tunnel up and down, which ruled the network out. `list-policy-grants` on the root domain unit then
returned an **empty list** for `CREATE_PROJECT` *and* `CREATE_PROJECT_FROM_PROJECT_PROFILE`, and the
unit's only owner was the group profile whose `rolePrincipalArn` is the `InfrastructureAccess` role
that created the domain. So the only principal that could create a project was the one that runs
Terraform.

The association above is the user's decision of 2026-08-22, and the two halves are not the same kind
of claim:

- **`experimentation` → the data scientists** is a standing right. It is the Sandbox, where D21 is
  already decided.
- **`engineering` → the deployment managers** is the **instrument of D21's open half** — whether a
  person needs an interactive surface next to a second account's data at all. It goes to the persona
  that owns the promotion chain the account exists to start, and if that question closes against the
  surface, the grant is removed. That removal is the expected outcome, not a regression.

**The grain is per profile, not domain-wide** (`CREATE_PROJECT` would carry every profile the domain
gains later), and **every field of a grant is `createOnly`** in the CFN schema — there is no in-place
edit, so moving a profile to another group destroys and re-creates the grant. The entity is the
**root domain unit**, the only one this design has; `include_child_domain_units` is `false`,
describing today's shape rather than restricting anything.

**Applied 2026-08-22** — `2 added`, re-plan `No changes`, read back independently through
`list-policy-grants`; the stage file's owed table carries the record.

The account pinning is D21's boundary as a property of the *project* rather than of the URL a person
opened, and the two names are the `US-4` contract. The reasoning lives with the code
(`terraform-live/data-governance/governance/locals.tf`).

#### Who may create an environment, and from which blueprint

The authorization above has a twin one layer down, found at the first real project creation
(2026-08-22). With the profile grants applied, `CreateProject` succeeded and the project died in
deployment: *"Caller is not authorized to create environment using blueprintId \<Tooling's id\>"*,
full rollback, nothing provisioned or billed in the member account. Creating a project and creating
the environments its profile bundles are **separate authorizations**: the second is
`CREATE_ENVIRONMENT_FROM_BLUEPRINT`, granted on the **blueprint configuration** rather than on a
domain unit, and `list-policy-grants` read **zero** such grants across all 22 configurations
(11 per member). The cause is the same shape as the profile gap: the console's *enable blueprint*
flow fills **"Authorized domain units"**, which emits this grant; `PutEnvironmentBlueprintConfiguration`
— all step 1.4 ran — only creates the configuration.

Two facts about the grant are documented nowhere. Both were measured, then confirmed against AWS's
own working sample (`aws-samples/sample-automate-sagemaker-unified-studio-using-iac`):

- **the entity identifier is `<account-id>:<blueprint-id>`** — the account is the configuration's
  *owner*, the member, not the domain account (fed the domain account the API answers "does not
  exist in account"); every publicly derivable spelling — bare id, `domain|id`, the ARN — is
  rejected as *format invalid*, and the API reference gives no format at all;
- **the principal is copied from the sample, not designed**: every project in the root domain unit,
  designation `CONTRIBUTOR`. What a designation means for this policy type is unwritten; the sample
  is a working end-to-end implementation whose `ON_CREATE` Tooling deploys at project creation — the
  failure mode above — so its principal is a measurement where a choice of ours would be a guess.

Because the entity is per member account, the grant lives in **`terraform-modules/sagemaker-prereqs/`
(`grants.tf`, tag `v0.3.0`)**, riding `for_each` over the blueprint configurations so a blueprint
joining category 1 arrives authorized in the same apply. Without its grant, every `ON_DEMAND`
blueprint fails as Tooling did, one capability-enable at a time. **Applied 2026-08-22 in both member
slices** — `11 added` each, re-plan `No changes`, all 22 read back with exactly one grant (the stage
file's owed table is the record).

## Blueprints — the object

An **environment blueprint** is a provisioning template owned by AWS. It works in two steps:

1. **Enabling it in an associated account** (Stage 6 step 1.4) registers the template in that
   member account, naming the provisioning role, the manage-access role and the VPC parameters it
   may use. Enabling by itself creates no billed resource.

   *(a)* **The API takes a `domainIdentifier` and no account parameter** (measured 2026-08-21), so
   `PutEnvironmentBlueprintConfiguration` configures the **caller's** account. That is why enabling
   blueprints is something an *associated* account does against a *shared* domain (the share's RAM
   permission is what lets it — `…DatazoneDomainExtendedServiceAccess`, measured 2026-08-21; §RAM),
   and why the resources live in each member's `sagemaker/` slice rather than in
   `data-governance/governance/`. *(b)* **The resource this project uses is
   `awscc_datazone_environment_blueprint_configuration`, not the `aws` provider's**, because only the
   `awscc` one carries **`environment_role_permission_boundary`** — the field that makes DataZone
   attach the D13 boundary **while it creates a project role**, instead of the boundary being attached
   afterwards and racing reconciliation. That is INT-15's mechanism (Lesson 8).
   **The trade, measured 2026-08-22: an existing configuration is immutable through `awscc`** — its
   identifiers are createOnly *and* write-only, the read never returns them, so every update patch
   looks like it adds createOnly properties and CloudControl refuses (`NotUpdatableException`).
   A field change on a configuration already applied is therefore a **`put-environment-blueprint-configuration`
   that re-sends the full object to match the already-committed code** (recorded per occurrence in
   the stage file; the Tooling manage-access fix is the first), or a replace — never an in-place
   update. Creates are unaffected. *(c)* **Every field the console wizard fills and the Put API
   does not require is validated at environment deployment and teardown, not at Put** — an
   incomplete configuration pins its projects in both directions. Tooling's full set, measured
   rung by rung on 2026-08-22: `manageAccessRoleArn`, and the regional parameters `S3Location`
   (`s3://awsds-<env>-smus-projects`, one bucket per member under the project CMK) and
   `KmsKeyArn` (the project CMK itself) beside `VpcId`/`Subnets`/`AZs`.
2. **A project uses it**: when a project whose profile targets that account exercises the blueprint,
   DataZone provisions the real resources the template describes — into the member account, through
   the registered provisioning role. The resource set this leaves behind is an **environment**
   (§object model above).

A blueprint is therefore a **capability gate**: enabled, the feature exists in the portal for every
project the profile admits and the service holds the right to create those resources in the account;
disabled, the feature is absent. Consequences:

- **The cost lever of Unified Studio is which blueprints exist**, not the domain (D26; the domain's
  metadata is cents per month, `PRICING.md` §5). What a blueprint provisions ranges from
  pay-per-use to billed-hourly-while-existing — the billing-shape column below — and the D12 budget
  notifies nobody, so a standing resource a project click created is the expensive kind of surprise.
- **Every enabled blueprint adds service-authored principals** (Lesson 17) and one more
  reconciliation surface the D13 boundary must survive (INT-15, Stage 6 verification (v)).
- **Enabling is cheap to do later** (one Terraform resource per account); disabling after
  environments were provisioned from it is not symmetrical. Start minimal.

### Blueprint categories

The categories are the user's decision of 2026-08-19. **`undefined` is the absence of a choice**, not
a fourth category; it exists because the 2026-08-21 roster reading found thirteen blueprints no
decision covers. Every blueprint requires a Terraform apply to exist — what distinguishes the
categories is what must happen **before** that apply:

| Category | Meaning | To enable |
|---|---|---|
| **1 — enabled by default** | in the step 1.4 map from the stage's first apply | nothing — born with the stage |
| **2 — on demand** | already authorized, with a **named trigger**; outside the map until it fires | commit + apply when the trigger fires — and the price measured at that moment if the row below lacks one (Lesson 6) |
| **3 — disabled** | outside the decision | an **amendment to Stage 6 decision 5**: price measured first, recorded in the stage log, then commit + apply. The *never* subset requires reopening an earlier decision instead |
| **`undefined`** | **nothing has been weighed** — the blueprint was never seen by the plan, or the decision that would have covered it named an object with no API identifier | decide its category first. **`US-3` fails on an `undefined` as it fails on a category-3**: a red battery that is merely uncategorised is indistinguishable from one that caught something |

The `US-3` allow-list in [`aws/studio.py`](../aws/studio.py) holds **category 1**; a category-2
blueprint joins the constant in the same commit that adds it to the step 1.4 map, so the check and
the code never disagree (Lesson 14).

**Promoting a blueprint out of category 2 — the checklist** (Lesson 39). One commit, one module tag
bump, in this order:

1. **The three roster copies move together** (Lesson 14): `sagemaker-prereqs`' `blueprint_names`
   default, `data-governance/governance/locals.tf`'s list, `US-3`'s allow-list.
2. **The project CMK gains the blueprint's documented key-policy statements** — `kms.tf` names the two
   absentees today (Redshift for `RedshiftServerless`-backed shapes, Airflow for `Workflows`); the
   adminguide key-permissions page is the source, never prose.
3. **Download the blueprint's template** (`templateUrl`, readable by any associated account) and read
   two things against it: every **required parameter without a default** (declare it in BOTH profiles —
   `UpdateProjectProfile` validates what `CreateProjectProfile` will not) and every **locked value
   against its `AllowedValues`** (the `lifecycleManagement` trap).
4. **Enumerate the console's enable-wizard fields for that blueprint and treat every one as required**
   (Lesson 39): a field the wizard fills and the Put does not demand is validated at environment deploy
   and teardown, and an incomplete configuration pins its projects in both directions. The seven
   `AmazonBedrock*` blueprints have no wizard of their own: the console enables them as the grouping
   `AmazonBedrockGenerativeAI`, whose form *Set up generative AI* asks for the provisioning role and two
   model roles, and whose Submit also writes an OpenSearch Serverless encryption policy over
   `collection/bedrock-ide-*` (read 2026-10-19 in the console and its code, Stage 17 7.0a).
5. **What arrives free**: the `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant (`grants.tf` `for_each`s the
   configurations) and — because a NEW configuration is a create, not an update — no reconciliation Put
   (§Blueprints item (b) bites only on changes to an existing one).
6. **The profile side**: an `ON_DEMAND` environment configuration in the profiles' list (the governance
   copy of step 1) — and the price measured at that moment if the category row lacks one (Lesson 6).
7. **The portal, read before and after the applies.** Steps 1 to 6 do not make the tool usable by
   themselves, because each portal entry gates itself in the browser, and the gates differ (read from
   the portal's code and its query state, 2026-10-19, [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md)
   1.5):
   - **The MLflow entries** (*Create MLflow App*, *Create MLflow Tracking Server*) resolve the blueprint
     by name from `ListEnvironmentBlueprintConfigurations`, called with the domain id alone as the
     domain execution role, so they read Data Governance's configurations, where `US-3` admits the
     lake-publishing pilot's `Tooling` alone (D22, Stage 6f step 11). They stay greyed in every project whatever the profile carries, *Update project* has nothing
     to apply (`UPDATE_NOT_AVAILABLE`), and a project created later reads the same list. What the
     entry would send is a `CreateEnvironment` with the profile's configuration id, and that call,
     made through the API by a project contributor, creates the tool (the `MLflowApp` environment and
     its app, 2026-10-19).
   - **The Generative AI menu** (the Playground and *AI apps*) opens only when the profile carries all
     seven Bedrock types, `AmazonBedrockKnowledgeBase` among them; with six it answers *"This tool is
     not available for this project."* Measured 2026-10-19 (Stage 17 7.2): once the seventh was
     applied, both projects' *AI apps* opened the Bedrock IDE and the Playground opened, with no
     *Update project* and no environment deployed by the reading. A second gate stands behind it: every
     model list reads *"No models found. Contact your admin to enable more models."*, since the account
     enables no model for projects or the playground (the console's **Amazon Bedrock models** tab, whose
     *Manage* publishes each model through a governance project the domain does not hold; the catalog
     surface below, Stage 17 decision 13).
   A promoted blueprint is therefore read in the portal after the applies, and its entry's gate is read
   before a refusal is attributed to the profile.

### Blueprints

The roster is measured. Read 2026-08-21 from the live domain `awsds-studio`,
`datazone list-environment-blueprints --managed` returns **23**, and the console's *Blueprints* page
lists **13**; re-read 2026-10-18, the same 23 names, and **24** on 2026-10-30, `SageMakerAIDomain` the one
added (its row below; the release note of 2026-10-20 says the console's *Blueprints* tab lists it, unread
here). How the two reconcile is why this table is keyed on the **API name**:

- **`AmazonBedrockGenerativeAI` is a console grouping, not an API blueprint.** The console shows one
  entry — *"consists of multiple blueprints"* — and the API returns the **seven** `AmazonBedrock*`
  rows below. Terraform and `US-3` can only name the seven. Stage 6 decision 5 put the *grouping* in
  category 1, which is why all seven arrive here as `undefined`: the decision was taken about an
  object that has no API identifier, so it does not carry to any of them by itself.
- **`LakeHouseDatabase` (console) is `DataLake` (API)** — the pair the plan already carried (Lesson 32).
- **12 direct + 7 from the grouping = 19**, leaving **four the API returns and the console never
  offers**: `LakehouseAdmin`, `S3Bucket`, `S3TableCatalog`, `ToolingLite`. Their descriptions below
  come from `get-environment-blueprint`, the only place they are written down.

**Three names read off documentation prose do not resolve**: `EMRServerless` is **`EmrServerless`**,
`EMRonEC2` is **`EmrOnEc2`**, `Quicksight` is **`QuickSight`** — Lesson 38, and why the column header
says *API name* rather than *name*.

Billing **shape** is read from documentation; billing **numbers** only where `PRICING.md` measured
them. The per-blueprint resource lists were re-read 2026-08-19 (that pass caught `LakehouseCatalog`
being Redshift-backed, Stage 6 decision 4); there is no "ML experience" blueprint, and the per-project
SageMaker AI domain comes from **`Tooling`** — both corrections to D26's wording, 2026-08-16.

Alphabetical by API name, the order `list-environment-blueprints` returns sorted — so a future roster
can be diffed against this table directly.

| Blueprint (API name) | What it provisions | Billing shape | Trigger | Category |
|---|---|---|---|---|
| `AmazonBedrockChatAgent` | A configurable generative AI app with a conversational interface | **Per use** — token-billed on demand, no standing resource (`PRICING.md` §5) | — | **1** |
| `AmazonBedrockEvaluation` | LLM evaluation for text generation, classification, question answering and summarization | **Per use** — token-billed; evaluation jobs bill the models they call | — | **1** |
| `AmazonBedrockFlow` | A configurable generative AI workflow | **Per use** — token-billed | — | **1** |
| `AmazonBedrockFunction` | A reusable component for including dynamic information in model output | **Per use** — token-billed | — | **1** |
| `AmazonBedrockGuardrail` | A reusable component for implementing safeguards on model output | **Per use** — token-billed; guardrail evaluation is its own unit | — | **1** |
| `AmazonBedrockKnowledgeBase` | A reusable component for providing your own data to apps: a Bedrock knowledge base, its data source and execution role, an OpenSearch Serverless collection and two Lambdas (the index and the ingestion trigger) with their role, per AWS's blueprint page (read 2026-10-12); the IDE's form also offers S3 Vectors and Neptune Analytics as the store. Its template (`DataZone-AmazonBedrockKnowledgeBase-prod-20260316`, read 2026-10-19) creates all of that only for an OpenSearch Serverless store, behind a `network` policy with `AllowFromPublic` true and no encryption policy; its two roles exist only when DataZone passes none, and carry AWS's `SageMakerStudioProjectUserRolePermissionsBoundary`, not the D13 boundary. Any other store leaves the stack with its wait handles alone | **Per use plus the store**: the embeddings are token-billed (Titan Text Embeddings V2 **0.00002 USD per 1K tokens**, `AmazonBedrock` offer of 2026-10-10) and the vector store is the shape that can bill while idle — **measured 2026-10-12**: OpenSearch Serverless **0.24 per OCU-hour** plus 0.024 per GB-month (a classic collection holds 1-2 OCU, 5.76-11.52 a day; a next-generation one scales to zero), S3 Vectors **0.06 per GB-month** plus requests (`PRICING.md` §5) | **Fired: [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md) decision 1** (taken 2026-10-12): a chat agent over the repository's runbooks, S3 Vectors the recommended store (its decision 12) and the embeddings model admitted at the SCP (its decision 11). The checklist's readings of 2026-10-19 (7.0a): no key statement, no profile parameter (the template's four parameters without a default are DataZone's), and nothing from the console's *Set up generative AI* form joins `blueprints.tf`. **The configuration, its grant and the profile's element were applied 2026-10-19** at `sagemaker-prereqs-v0.7.0` (7.0b), and both projects' Generative AI menus opened, offering no model (the checklist's step 7). It was the only Bedrock row that is not purely per use, which is why it left category 1 on 2026-08-21 while its six siblings stayed | **1** |
| `AmazonBedrockPrompt` | A reusable set of inputs that guide model output | **Per use** — token-billed | — | **1** |
| `DataLake` (console: `LakeHouseDatabase`) | Per project: **Glue databases, Lake Formation permissions, an Athena workgroup** — the catalog/SQL surface on the Glue + LF substrate Stage 5a built, the query path D13 depends on. Its environment carries the project's subscription target for `GlueTableAssetType` and `GlueViewAssetType`, which `Tooling`'s do not, and a daily Glue data source over its database, at the minute of its creation (read 2026-10-20 in Staging and in Sandbox's `test-experimentation`). Its template (`DataLakeDefault-prod-20250618`) keeps the database at every stack deletion (`DeletionPolicy: Retain`), and its add-on fails without the Glue manage-access policy on the manage-access role (`sagemaker-prereqs-v0.8.0`) | **Per use**: Athena SQL **USD 5.00/TB scanned** (`PRICING.md` §5); Glue catalog negligible at lab scale. No standing resource; the environment's daily data source run is ingestion, billed in compute units per completed job (§5), unmeasured per run | default — configured at step 1.4 | **1** |
| `EmrOnEc2` | EMR clusters on EC2 instances — Spark, Hive and other big-data workloads from a reusable CloudFormation template | **Standing in practice** — instance-hours + EMR uplift while the cluster exists; a forgotten cluster bills on. Not measured | amend the decision (unowned until 2026-08-19) | **3** |
| `EmrOnEks` | Amazon EMR on EKS resources, same workload family as `EmrOnEc2` | **Standing in practice** — an EKS cluster underneath, plus EMR uplift. Not measured | — | **3** |
| `EmrServerless` | An EMR Serverless application per project — the VPC-capable Spark runtime replacing the Athena-Spark default (open question 12), and **the only engine whose compute connection documents an LF fine-grained mode** (`project.spark.fineGrained`; the notebook Spark Connect path is full-table on every engine). Under `VpcOnly` it asks for **four** optional endpoints against Glue interactive sessions' one (≈USD 0.06/h across both Interactive accounts under Stage 3's single-AZ rule, while the `egress/` slices are up) | **Per use**: **USD 0.0526/vCPU-h + 0.0058/GB-h** (x86; ARM cheaper), billed only while a session runs (`PRICING.md` §5). Near-standing tail: a **started** interactive application keeps one 4 vCPU/16 GB kernel worker even with no *pre-initialized capacity* configured (`autoStop` 30 min idle; the 60-min kernel timeout is not configurable) | default — **Stage 6 decision 1, taken 2026-08-21 as KEEP-or-REMOVE**: enabled at 1.4, and removed if either of the two in-stage readings comes out against it | **1** |
| `LakehouseAdmin` | *"Creates a unified data source across all Lakehouse catalogs in the account and automatically ingests and catalogs all available data."* An automatic, account-wide ingest-and-catalog is the shape `docs/GOVERNANCE.md` exists to prevent, and the account it would run in holds a governed lake | Not documented. Whatever a standing crawl of everything costs, plus the catalog it writes | **step 2.4 has measured** what the environment provisions, under whose role, and what the D13 boundary actually stops — **or** a category-1 blueprint proves it depends on this one. Until then it is not registered, so no project can create it | **2** |
| `LakehouseCatalog` | A new catalog in the SageMaker Lakehouse **backed by S3 tables or Redshift Managed Storage** — *not* the Glue/Athena surface its name suggests (the 2026-08-19 re-read) | RMS storage + the Redshift query path; the RPU-hour rate is now measured (`PRICING.md` §5) and the base capacity this blueprint would pick is not | amend **decision 4** (2026-08-19); the Glue/Athena form this project uses is `DataLake`. **D40 does not reach this row**: it admits a warehouse Terraform sizes, not a catalog a blueprint provisions on Redshift-managed storage | **3** |
| `MLExperiments` | An **MLflow tracking server** for the project (OnDemand blueprint) | **Standing** — the server bills per hour while up (no idle shutdown like the apps have) + storage. **Measured 2026-10-12** in the `AmazonSageMaker` offer (`us-west-2`, published 2026-10-12T18:05:38Z): Small **0.60**, Medium **1.04**, Large **1.91** USD/h, storage 0.10 USD/GB-month (`PRICING.md` §8). Known floor under `VpcOnly`: its interface endpoint, +USD 0.010/h per account — the tracking server's service name is `aws.sagemaker.us-west-2.experiments`; `aws.sagemaker.us-west-2.mlflow` is the MLflow App's (read 2026-10-12) | a tracking need the MLflow App does not meet: [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md) decision 2 took the app over the server on 2026-10-12, the offering AWS's own MLflow page says to prefer (read 2026-10-12) | **2** |
| `MLflowApp` | *"Creates an MLflow App for SageMaker Unified Studio."* **The same capability as `MLExperiments`, arriving twice**, and the pair was categorised together so enabling one would not quietly imply the other, until Stage 17 decision 2 took the app and left the server in category 2. Serverless: `CreateMlflowApp` makes `mlflow-app/<id>` with an S3 artifact store and a role, reached from a VPC through the `aws.sagemaker.<region>.mlflow` interface endpoint and from the portal through a presigned URL minted on `sagemaker.api` (read 2026-10-12). `CreateMlflowApp` takes `KmsKeyId` since 2026-08-20, and an app made without it carries no customer-managed key; neither CloudFormation nor either provider has the field (read 2026-10-18) | **No usage type in the `AmazonSageMaker` offer of 2026-10-12** (the tracking-server sizes, its storage and the partner-app SKUs are there; nothing for the app), and AWS's launch post of 2025-12-02 says no additional cost beyond the artifact store. **Measured in the bill at [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md) 8.2** | **Fired: Stage 17 decision 2** (taken 2026-10-12, the app over the server). Pass 1's change was written 2026-10-17 (PR #157): the three roster copies (`sagemaker-prereqs-v0.5.0`, the profile, `US-3`) and the `mlflow` endpoint group (`vpc-egress-v0.18.0`, its decision 4); the checklist's template and wizard readings (steps 3 and 4) were made on 2026-10-18, with nothing to declare. **The configuration, its grant and the profile's element were applied 2026-10-19** (Stage 17 1.3); the endpoint group is not. The portal's Compute → *MLflow* tab greyed out *Create MLflow App* before the applies (*"The MLflowApp blueprint is not enabled for this project"*) and still does after them, in both projects, because the entry resolves the blueprint from Data Governance's configurations (the checklist's step 7). **The app `ml-demo-mlflow` was created 2026-10-19 through `CreateEnvironment`** in `eighth-experimentation` (Stage 17 1.5): DataZone's deployer calls `CreateMlflowApp` as the provisioning role, with the project role as the app's role, the store under the project's path in `awsds-sandbox-smus-projects` and no `KmsKeyId` | **1** |
| `PartnerApps` | An IAM role and a Connection giving access to third-party Partner AI Apps | **Standing/subscription** — partner licence + deployed infrastructure; varies by partner. Not measured | amend the decision | **3** |
| `QuickSight` | The QuickSight analytics/dashboard surface inside a project | **Subscription** — per author/month + per reader session. Not measured | amend the decision. **Also blocked in fact**: the console reads *"QuickSight account not set up"* (2026-08-21) | **3** |
| `RedshiftServerless` | A Redshift Serverless workgroup + namespace | **Per use** with a **60-second minimum charge per query** + storage, at **0.36 USD/RPU-hour** measured (`PRICING.md` §5) — and a blueprint-provisioned workgroup takes the service default of **128 base RPUs**, which is **46.08 USD per query-hour** | **Never** — and the trigger changed on 2026-09-19 without the verdict changing. [D40](plan/decisions/D40-redshift-warehouse.md) **admits a warehouse and keeps this blueprint disabled**: the warehouse is one namespace per account, written by Terraform at `base_capacity = 4` with a usage limit, reached through a **connection to an existing compute resource** (§Connections below, [Stage 6h](plan/stages/stage-06h-redshift-connection.md)). Enabling *this* row would put a 128-RPU workgroup one click from every project member, which is the thing D26 refused and D40 did not un-refuse. `US-3` fails if it appears, with its own message. **The warehouse it was refused in favour of exists since 2026-09-20** and reads back at `base 4 / max 8 RPU` with a 10-RPU-hour monthly limit that `deactivate`s on breach — measured refusing queries, so the comparison in this row is now against something real | **3** |
| `S3Bucket` | *"Create S3 bucket for SageMaker Unified Studio project."* Not offered by the console — read from `get-environment-blueprint` | Storage + requests. Not measured. **The governing question is not cost**: a bucket born here has an encryption key and a policy nobody in this project chose (`docs/GOVERNANCE.md` §Encryption) | — | **1** |
| `S3TableCatalog` | *"Create S3 table catalog for SageMaker Unified Studio project."* Not offered by the console. **Possibly what `LakehouseCatalog` expands into when its S3-tables form is picked** — the same one-console-entry-to-many-API-rows shape as the Bedrock grouping. **Hypothesis, not a reading** | S3 Tables storage + maintenance. Not measured | — | **1** |
| `SageMakerAIDomain` | *"A SageMaker AI domain for managing SageMaker spaces and apps"* (read 2026-10-30 from `get-environment-blueprint`; in the roster since the reading of 2026-10-30, `createdAt` 2026-08-21, `updatedAt` 2026-10-22). A standalone SageMaker AI domain per project beside `Tooling`'s, from the template `DataZone-SageMakerAIDomain-prod-20260905`: one `AWS::SageMaker::Domain`, `VpcOnly` on the Tooling environment's network, the project role as every space's execution role, the Tooling key; the profile's parameters carry the custom images (a JSON list of `ImageName`, `AppImageConfigName` and `ImageVersionNumber`, 30 per app type, which the service translates into the template's `name;config;version`), the default image version, the idle timeouts and their ranges, the hidden instance types and distribution versions, the volume ceiling (100 GB), the domain name and `enableRStudio`, whose `true` cannot be undone and which adds an EFS home, service-managed security groups and Posit's RStudio (§Custom images; [`upstream-releases.md`](plan/upstream-releases.md)) | The domain at rest is free (§10); JupyterLab and Code Editor apps bill as `Tooling`'s; an RStudio session bills the instance rate (`ml.t3.medium` **0.050/h**) and the server app **0.00**, the Posit licence outside AWS's price list (`PRICING.md` §8, §11) | **6d decision 15, taken 2026-10-30 by the user as (b)**: the pilot on `experimentation` (`ON_DEMAND`, order 13; `sagemaker-prereqs-v0.9.0`), the house image pinned at `var.sandbox_dev_env_version`, applied 2026-10-30, the image lists in JSON since the two `[]`s of 2.6 item 3; `test-experimentation` holds `lab-sagemaker-ai-domain` (`d-odhynkcev3yw`) since 2026-10-30 with the house image pinned at 11; RStudio off until the Posit licence, the licence and the inline policy the user's | **1** |
| `Tooling` | The project's basic environment: the per-project **SageMaker AI domain** (only under the template's `sageMakerDomainRequired`, a default Tooling with `enableSpaces == "true"`, read 2026-10-19 in `ToolingDefault-prod-20260918`: a profile with `enableSpaces` false creates none, Stage 18 decision 1), project roles, security groups, Athena workgroups, the project S3 location — and the parameter surface Stage 6 step 1.5 locks (`sagemakerDomainNetworkType`, idle shutdown, `maxEbsVolumeSize`, TIP). Mandatory — nothing else provisions a working environment | Per **app-hour running** (`ml.t3.medium` JupyterLab/Code Editor at **USD 0.050/h**, `PRICING.md` §8) + EBS. An open app bills whether used or not — the step 8 idle shutdown is what converts "up" into "in use" | default — mandatory | **1** |
| `ToolingLite` | *"Create basic resources for SageMaker Unified Studio project."* Not offered by the console. **Its template** (`ToolingLiteDefault-prod-20260723`, read 2026-10-19 for [Stage 18](plan/stages/stage-18-staging-deployment-project.md) decision 1): one user parameter, `s3BucketLocation`; a bucket when none is given, a security group, Glue connections, an Athena workgroup, a schedule group and an `AWS::SageMaker::Domain` with no condition; no project role of its own (`executionRoleArn` is a parameter), no log group, no Lake Formation registration; it exports the VPC, the subnets, the security group and the key the CI/CD CLI reads. **Measured at step 1.5 (2026-08-21): a base variant, not a capability** — bundled in a project profile, the service demands `deployment_mode = ON_CREATE` (*"ToolingLite environment blueprint configuration must have deployment mode ON_CREATE"*, DataZone 400), so it cannot ride a `Tooling` profile as an on-demand extra, and a second base would double-provision every new project | Not documented. Presumably the same app-hour shape as `Tooling` with fewer resources — **unread** | amending the decision | **3** |
| `Workflows` | A **provisioned MWAA (Airflow) environment** from a CloudFormation template — billed hourly while it exists | **Standing**: MWAA `mw1.micro` **≈ USD 211.70/month** left up (`PRICING.md` §1) — the shape D7 rejected for daily use | **Never** while D7 stands: its amendment of 2026-09-05 took provisioned MWAA off INT-14's ladder, which removed the trigger this row's category-2 placement named, and Stage 10 step 4.3's `DenyProvisionedMwaa` (`airflow:CreateEnvironment` on the root SCP) refuses what this blueprint creates once applied. The *serverless* Workflows surface is **not** this blueprint and needs no configuration of its own: 6d step 4 found it already provided by the eleven category-1 configurations (§The workflow surface) | **3** |

**All 23 rows carry a category** (user, 2026-08-21), settled against the measured roster rather than
against the console grouping decision 5 had addressed: closed at 12/5/6 and re-cut to 11/5/7 the same
day, when step 1.5's refusal measured `ToolingLite` as a second base (its row above), then to 11/4/8
when D7's amendment removed the `Workflows` trigger (its row above), then to 12/3/8 when Stage 17
decision 2 took `MLflowApp` (its row above; applied 2026-10-19), then to 13/2/8 when its decision 1
took `AmazonBedrockKnowledgeBase` (applied the same day).
**Category 1 is thirteen**: `Tooling`, `DataLake`, `S3Bucket`, `S3TableCatalog`, `EmrServerless`,
the seven `AmazonBedrock*` and `MLflowApp`. Category 2 is two, `LakehouseAdmin` and `MLExperiments`;
category 3 is eight, and **no row is `undefined`** — which is what step 1.4 needed, because `US-3`
fails on an uncategorised blueprint as it fails on a forbidden one.

**`AmazonBedrockKnowledgeBase` joined its six siblings in category 1 on 2026-10-19**, and nothing
downstream may yet reason about "the Bedrock blueprints" as one billing shape: the other six are purely
token-billed, while a knowledge base stands up a **vector store**, which an OpenSearch Serverless
collection bills while it exists and S3 Vectors bills by the gigabyte stored (`PRICING.md` §5, measured
2026-10-12). That standing shape is the one D12's silent budget is worst at catching, so the store is
chosen per knowledge base ([Stage 17](plan/stages/stage-17-sandbox-machine-learning.md) decision 12).

**`S3Bucket` and `S3TableCatalog` create storage this project did not author.** The governing question
is not their cost but their **encryption key and bucket policy**, which come from the blueprint rather
than from `docs/GOVERNANCE.md` §Encryption's per-account CMK rule. Stage 6 step 2.4's throwaway project
is where those fields get read (Lesson 16); verification (xviii) is the receiving end.

**`ToolingLite` moved 1 → 3 by measurement** (step 1.5, 2026-08-21): the service does not select the
lighter variant on its own, it refuses a profile that bundles it `ON_DEMAND`, which makes it a second
base, present only by explicit choice. A base beside `Tooling` would double-provision every new
project with an unmeasured shape, so it is disabled; if it ever returns, it returns as its own project
profile, never as an extra on these two.

**`LakehouseAdmin` is category 2.**

> It was placed in category 1 and moved the same day, before anything was applied. The category-1 row
> carried a note — *read it at step 2.4's throwaway project before a real project uses it* — and a
> note is an **intention, not a control** (Lesson 5): nothing executes it, and the capability exists
> from the apply regardless. In category 2 that same sentence becomes the **trigger**, the condition of
> enabling. Nothing in `objectives.md` asks for this blueprint, no stage consumes it, and it was not
> known to exist before 2026-08-21, so category 2 costs nothing anyone has named while category 1 buys
> availability nobody requested.
> **The counter-argument is not settled**: if *"a unified data source across all Lakehouse catalogs"*
> turns out to be how a project sees the shared catalog at all, this belongs in category 1 and its
> absence would break the point of the stage. That looks unlikely — `DataLake` provisions the
> per-project catalog surface and Stage 5a already established the lake path through resource links and
> Athena — but it is unread. If step 2.4 finds a dependency, it moves up **with evidence**, before any
> real project exists. The failure mode of being wrong this way is a loud apply error; the other way it
> is an unmeasured account-wide ingest sitting one click from a project member.

> **It is not Lake Formation's *data lake administrator*.** The AWS portal text consulted on
> 2026-08-21 describes that other object — a privileged IAM principal designated under
> *Administration → Data lake administrators*, which this project already owns and already assigned
> (Stage 5a pass 4, `DL-6`, and `docs/ORGANIZATION.md` names who). **This blueprint's own description,
> from `get-environment-blueprint`, is a provisioning template**: *"Creates a unified data source
> across all Lakehouse catalogs in the account and **automatically ingests and catalogs all available
> data**."* The two share a word and nothing else; reading one as the other is Lesson 38's shape in
> reverse, a real name attached to the wrong object.
>
> **The risk, stated so the trigger can retire it.** Enabling a blueprint provisions nothing — it
> *registers* a template, and the ingest happens only if a project creates an environment from it. The
> concern is that a category-1 placement puts an account-wide automatic ingest **one click from a
> project member**, in an account holding a governed lake. Whether the D13 boundary
> `awsds-<env>-project-boundary` and Lake Formation's own permissions stop that ingest reaching
> registered locations is **unmeasured** — INT-15 and Stage 6 verification (v)'s question, what a
> service-authored role can do that this project did not grant. The boundary's S3 deny names the
> **LF-registered** buckets, so it says nothing about the derived zone, where a project's outputs live.

## The workflow surface

Measured at [6d](plan/stages/stage-06d-unified-studio-remainder.md) step 4, 2026-09-09/10, against a
workflow a person authored in the portal on 2026-08-27.

- **Nothing enables it.** The surface exists with the eleven category-1 blueprint configurations 6a
  applied; no twelfth configuration, no blueprint change and no flag stands between a project and a
  workflow. The roster claim that the serverless surface is separate from the eleven is therefore
  false: it is one of the things they already provide.
- **It is MWAA Serverless** (D7 amended), billed at USD 0.088 per task-hour. The provisioned
  `Workflows` blueprint is category 3: D7's amendment took provisioned MWAA off INT-14's ladder, and
  Stage 10 step 4.3's `DenyProvisionedMwaa` refuses `airflow:CreateEnvironment` once applied.
- **A failed task is attempted twice**, with no `retries` key in the definition, so a failed run's
  duration is about double the task's and the task's `DurationInSeconds` is the reading. The one
  successful run read (`simple-s3-copy`, 2026-09-10) shows one attempt, 49 s.
- **`list-workflow-runs` returns `RunType` null for every run**; `get-workflow-run` carries it
  (`ON_DEMAND` or `SCHEDULED`), so a run's type is read one run at a time (read 2026-10-10).
- **A "Notebook task" is a `CreateTrainingJob`.** `SageMakerNotebookOperator` executes the notebook as
  a training job, which is why it meets `DenySageMakerJobsOffVpc` in the **D13 boundary's** copy of
  the statement and not in the persona sets' (Lesson 33). Filling the portal's empty `compute` block
  satisfies one of the boundary's five conditions and changes nothing else, so the portal's notebook
  operator does not run in this estate, by decision: 6d decision due 14 took (b) on 2026-10-10, so the
  portal's notebook task is not offered and workflows orchestrate with operators the repository
  controls, `PythonOperator` and `BashOperator` among them. Other operators do run: a portal-authored
  `S3CopyObjectOperator` task finished `SUCCESS` as the project role (`simple-s3-copy`, 2026-09-10).
  Query-book and Visual ETL tasks are unmeasured.
- **A Visual ETL flow is documented to run as a notebook**, and a query book's editor schedule too
  (read 2026-10-13; unmeasured). A flow is the file `<name>.vetl` in the project's repository, under
  `src/dataflows/`, authored on Glue interactive sessions. The editor's schedule is an EventBridge
  Scheduler schedule whose target is `CreateTrainingJob`, and the documented workflow route is a DAG whose
  `NOTEBOOK_PATH` names the `.vetl`; MWAA Serverless lists `SageMakerNotebookOperator` as its only Unified
  Studio artifact executor. A scheduled flow is therefore expected to meet the boundary a notebook task
  meets. What reaches a deployment target is the generated script, as a Glue job of the application (D28
  class (2c), Stage 10 step 2.2).
- **`update-workflow` is a full replace** (Lesson 60), and the portal injects domain and project state
  no field of that API restores, so an update authored outside the portal severs it.
- **A workflow's name and key are fixed at creation**: `AWS::MWAAServerless::Workflow` marks `Name` and
  `EncryptionConfiguration` create-only (registry, read 2026-10-18), so a change of key is a new workflow.

Measured at [6i](plan/stages/stage-06i-sandbox-orchestration.md), 2026-10-10/11, on Sandbox's private
shape. The procedures are [`serverless-workflows.md`](plan/runbooks/serverless-workflows.md).

- **The editor is a form per task, and the import carries the whole YAML.** The processing form has no
  field for `NetworkConfig`, either KMS key or the tags, so a processing workflow is imported (*Actions →
  Import definition file*). The saved definition keeps every field and adds `is_paused_upon_creation:
  false`. An import into a saved workflow's editor is refused at save with `ConflictException`.
- **Every save sends a code location.** The editor pre-fills *Operator files zip S3 location* on a new
  workflow, a processing-only one included; with no file there the service answers `Code not found in
  specified S3 location`, and emptying the field saves with no `Code`.
- **Operators run on the private shape**: `S3KeySensor`, `S3DeleteObjectsOperator`,
  `SageMakerProcessingOperator` (a job in the house image under the D13 boundary's four settings, once
  `sandbox/workflows/` grants the existence check and the tag), `PythonOperator` and `BashOperator`.
- **A Python or Bash task's code is a `Code` object the service copies at every save** to
  `mwaa-serverless-code-files-<AWS-owned account>-<region>-prod`. Each worker has
  `airflow-serverless.amazonaws.com` fetch that copy through the VPC's S3 gateway endpoint, whose policy
  must admit the family (`vpc-v0.4.0`, 6i decision 7).
- **The worker** is Python 3.12.14 with boto3 1.43.1, no proxy and no internet, and a pre-installed
  package wins over a bundled one. A processing job takes its dependencies as a folder in its code
  input (6i verification xvi).
- **The workflow's log group exists from its first save**, `/aws/mwaa-serverless/<domain>-<project>/<workflow>`,
  with no retention, and outlives the workflow.
- **A run's state lags its task instances**: `RunState` read `QUEUED` after the first task had
  finished.

## The CI/CD tool deploys between projects

The SageMaker Unified Studio CI/CD feature is the open-source `aws-smus-cicd-cli`, and AWS's guide says
it deploys only into projects that already exist; its 1.0.9 code also creates one when a stage says
`project.create: true`, and its `destroy` then deletes it (read 2026-10-17, Stage 18 step 0.1).
A deployment target under D26 has no project and no domain
association, so the tool cannot reach one (Stage 18 gave Staging both for its window, below, and its
verdict kept the rule): it deploys an application from its repository into the
Sandbox projects, `dev` and `test`, and makes the bundle, and the GitLab pipeline stays the deployer in
Staging and Production (D28, D41). Measured in the lab on 2026-10-15: `deploy` syncs the manifest's
`storage` content into the project's S3 and the workflow is born by the bootstrap action
`workflow.create`, which resolves the YAML's variables, rewrites it at the same key and calls
`CreateWorkflow` with the project role, the Tooling subnets, security group and key, no `TriggerMode`
(so `manual_only`), the log group `/aws/mwaa-serverless/<domain>-<project>/<name>` and six tags
(`AmazonDataZoneProject`, `AmazonDataZoneDomain`, `Target`, `CreatedBy=SMUS-CICD`, `STAGE`, `Pipeline`);
the name is `<application>_<project>_<workflow>`, every other character turned into `_`. The CLI's
pre-deployment validation simulates the role's policies with no context keys, so every SCP conditioned
on `aws:RequestedRegion` or `aws:ResourceOrgID` reads denied and the deploy runs with
`--skip-validation`; `--no-events` keeps its `PutEvents` off the default bus; its boto3 ignores the
`aws` CLI's SSO cache. Stage 8 step 5.6 writes the lint that enforces the difference, on the rendered
file. 1.0.9 is still the latest release on 2026-10-18. When its identity cannot read a domain-scoped VPC
connection or the Tooling environment's `privateSubnets`, `securityGroup` and `kmsKeyArn`, `workflow.create`
omits the network and the key, prints one line and creates the workflow in the service's default worker
network under a service-managed key (its `helpers/datazone.py`; [`upstream-releases.md`](plan/upstream-releases.md)).

**From a space, as the project role** (Stage 8 decision 22), the deploy and its run measured on
2026-10-26 (Stage 10 2.1), after three findings that the lab's laptop run could not show:

- **Two CLIs in one image.** The SageMaker Distribution ships `aws-smus-cicd-cli` 1.0.8 in
  `/opt/conda/bin`, first on a space's `PATH`, and it refuses a manifest's `content.workflows[].code`
  (*"Additional properties are not allowed ('code' was unexpected)"*); the house environment's 1.0.9 is
  reached by its path, through the template's `scripts/dev-cli.sh`. An image's `ENV PATH` cannot reorder
  the two: every start script of the distribution runs `micromamba activate base` before its server, and
  the activation puts `/opt/conda/bin` first, so the server and its terminals see conda's directory
  first whatever the image declares; the base environment's `etc/conda/activate.d/` scripts run after
  that export (read 2026-10-26 in 4.5.2's scripts and libmamba's activation, not measured in a space).
  The house image prepends `/opt/awsds/bin`, the house CLI's entry point alone, through such a hook from
  `default-v0.10.0`, Sandbox's version 11 (Stage 8 decision 22): its smoke read the name as the house's
  1.0.9 after `micromamba activate base` on 2026-10-26, and a space's reading is `promotion.md` §N.7.3.
- **DataZone refuses `ListDomains` to a project's role** (*"User is not permitted to perform operation:
  ListDomains"*, CloudTrail `AccessDenied` with no message) though the role's managed policy allows
  `datazone:List*`; the CLI 1.0.9 resolves the domain by name with that call in the project step of every
  deploy with bootstrap actions and again in `workflow.create`, the manifest's id notwithstanding. The
  deploy roles' call returns the associated domain, so the pipeline never meets it. Reported upstream as
  [issue 413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413) (2026-10-26).
- **The MWAA Serverless API answers on `airflow-serverless.<region>.api.aws` alone**, a family the compute
  plane's proxy refuses, so a space reaches it only through the interface endpoint
  (`com.amazonaws.<region>.airflow-serverless`, private DNS on), `vpc-egress`'s `mwaa` group since
  `v0.19.0`, with the name in `NO_PROXY`.

[`runbooks/sagemaker-application.md`](plan/runbooks/sagemaker-application.md) §D carries the commands. A
run started from the portal on a workflow the CLI made carries none of the stage's variables and fails at
the DAG's template before any task (Stage 10 xxix).

### A deployment project in a `Workloads` account

Measured in `Staging` from 2026-10-19 to 2026-10-22 and removed ([Stage 18](plan/stages/stage-18-staging-deployment-project.md)
and its log); D41 item 2 kept the rule above.

- **What the blueprint creates.** A `Tooling` environment whose profile locks `enableSpaces` to `"false"`
  creates no SageMaker AI domain, so only `DenyDataZoneEntirely` needs a carve-out. Its stack holds
  thirteen resources: three roles under the configuration's boundary, the project role among them, a
  security group, two Glue network connections, two Athena workgroups, a log group at 731 days, the
  project's `dev/` prefix registered in Lake Formation and a schedule group. Outside the stack the
  provisioning seated itself and the manage-access role as the account's Lake Formation admins
  (`PutDataLakeSettings`, a full replace), set `AllowFullTableExternalDataAccess` `true`, created the S3
  Access Grants instance `default` with a location for the project's prefix, and the service-linked
  role `AWSServiceRoleForAmazonAthena`. `DataLake` on demand adds a Glue database, its
  project-conditioned Lake Formation grants and a daily data source, its manage-access role needing
  `AmazonDataZoneGlueManageAccessRolePolicy`.
- **What the CLI needs there.** The deploying role is a member through its `IAM_ROLE_SESSION_GROUP`
  profile, which DataZone creates at the role's first call; as a non-member it lists the project and
  every storage item stops on `ListConnections`. It holds the DataZone reads, the workflow calls on
  workflows tagged with the project, `iam:PassRole` of the project role to the service, the project's
  `shared/` prefix and the project key. `run` starts the workflow and returns; a pipeline follows the
  run with `get-workflow-run`.
- **A person in it.** The V2 domain admits `PROJECT_OWNER`, `PROJECT_CONTRIBUTOR` and, since 2026-10-29, a
  `USER_CREATED_DESIGNATION` of the domain's own (none here, read 2026-10-30); a member of any designation
  acts as the project role, and with spaces off the portal offers no Workflows tool.
  DataZone sets `aws:SourceIdentity` on the sessions it opens for a member and as `SYSTEM`, and none
  is set on a worker's session or on a subscription fulfilment's.
- **A subscription across accounts.** The fulfilment acts as each side's project role, in
  `AWSDataZone-Subscriptions` sessions. The producer side grants `SELECT` to the consumer account's
  `IAMPrincipals` under the subscribing project's context, with `CROSS_ACCOUNT_VERSION` 5 in the grant
  whatever the account's setting; shares the producer's catalog, databases and tables to the consumer
  account through RAM; and writes three statements into the producer's Data Catalog resource policy.
  The consumer side creates a resource link and grants `DESCRIBE` on it to the project's context. The
  consumer's query editor reads the table; a revocation removes every piece on both sides.
- **What a teardown leaves.** `delete-project --skip-deletion-check` deletes the environments' stacks,
  and with them the project role, the security group, the Glue connections, the project's Athena
  workgroups and the Access Grants location. It leaves the stack's log group, the `DataLake` database
  and a failed environment's, the Lake Formation admins and settings, the Access Grants instance, the
  Athena service-linked role, the CLI's and the runs' log groups with no retention, SageMaker's lineage
  entities and the `operatorFiles/` copies, all removed by hand; and the domain keeps the members' user
  and group profiles, the lineage events and the subscription records, which no delete API reached.

## The catalog surface

The business catalog over this domain is [Stage 6f](plan/stages/stage-06f-data-governance.md)'s
subject and [`GOVERNANCE.md`](GOVERNANCE.md) holds the model. What belongs here is what the SMUS
objects above turn out to do, read 2026-09-18 by [`./aws/catalog.py`](../aws/catalog.py).

- **Publishing the lake needs a project in the lake's account, and that project needs a VPC there.**
  Stage 6f decision 1 took shape (b) on 2026-10-26, and its step 11 writes it. Read from the two
  templates that day: `Tooling` (`ToolingDefault-prod-20260918`) takes `vpcId`, `subnets` and
  `availabilityZones` with no default and creates the project's security group in that VPC unless one is
  passed, with spaces off as with them; `DataLake` (`DataLakeDefault-prod-20250618`) imports
  `s3BucketPath-<project>-<scope>`, which only the same account's `Tooling` stack exports, so neither
  runs alone in an account with no VPC. `Tooling`'s `LakeFormationResourceToRegisterProjectsS3Location`
  carries no `DeletionPolicy`, so deleting a project calls `lakeformation:DeregisterResource`, which
  `Data Governance`'s OU denies to every principal.
- **A subscription's fulfilment writes per-resource catalog policies, not the account's** (read
  2026-10-26, 6f 11.9). The publishing role's four `glue:PutResourcePolicy` calls carry a `resourceArn`
  (`catalog`, `database/*`, `table/*/*`) and `enableHybrid` `TRUE`; `glue get-resource-policies` lists
  what they wrote, and `glue get-resource-policy` keeps answering *"Policy not found"*.
- **The publishing project's role can regrant its published tables in any session** (read 2026-10-27,
  6f decision 5). `SageMakerStudioProjectUserRolePolicy` v75's `LFResourceSharingPermissions` allows
  `lakeformation:BatchGrantPermissions` on `*` with no condition; the RAM share and the catalog policies
  of a cross-account grant follow through `aws:CalledVia` (`XAcctLFCreate`, `XAcctRAMGlue`). What the
  role can regrant is what Lake Formation gave it with the grant option, so the publisher's grant is the
  bound, and `./aws/catalog.py` `CT-10` is what notices a grant no subscription explains.
- **A listing carries its approval switch, and a copy of its source.** `get-listing` returns the forms
  as a JSON string: `SubscriptionTermsForm.approvalRequired` (`YES` on `trades`, read by `CT-11`), the
  `GlueTableForm` naming the table, and a `DataSourceReferenceForm` holding the source's configuration
  as it was at the publish, which keeps reading generation `true` after the source itself was turned off.
- **A subscription can be approved with row and column filters** (AWS's page, read 2026-10-27): the
  fulfilment unions them into one Lake Formation data cells filter and grants `SELECT` on it. Never run
  here; 6f decision 2 keeps `restricted` and `personal` data off the road instead.

- **A project's Tooling environment creates a data source nobody asked for, and it fails.**
  `Tooling-default-sagemaker-modelpackagegroup-datasource` tracks `SageMakerModelPackageGroupAssetType`
  and runs on a **daily cron** the environment chooses, `cron(32 17 * * ? *)` for the first project and
  `cron(6 6 * * ? *)` for the second. Every completed run has failed since 2026-08-24 on the RAM-share
  validation error (`EXC-11`; 57 failed runs across the two sources on 2026-10-18). It publishes
  nothing (`publishOnImport: false`), finds no asset and bills nothing, but it is a scheduled run this
  repository did not write (Lesson 17). The Glue data source a person creates in the portal carries no
  schedule and **`enableBusinessNameGeneration: true`**, which sends the asset's metadata (table and
  column names, producer-supplied metadata) to a Bedrock model in the Region and has never run here.
  6f decision 3 keeps it off on every source over the lake (2026-10-27), which `CT-5` checks.
- **Lineage sync is a connection property.** `glueLineageSyncEnabled` is `true` on each project's
  `LAKEHOUSE` and `IAM` connections (read 2026-10-18, never updated since creation), and the blueprint
  configuration carries no lineage field. The Redshift connection's `lineageSync` is the separate
  meter below, and it is enabled (`cron(43 3 * * ? *)`, read 2026-10-18): its eight daily runs since
  2026-10-11 all failed, the newest on *"Redshift endpoint doesn't exist in this region"* while the
  workgroup was down, and that run processed no query.
- **The domain offers 23 managed asset types**, `GlueTableAssetType` among them, all owned by the
  domain's own project. A custom type is not needed to publish a Glue table.
- **`list-domains` in an associated member account returns the shared domain.** The listing alone
  cannot say where a domain lives; `managedAccountId` can, and it names the registry account on both
  sides of an association. Any check that reads the listing reports the association as a second
  domain.
- **The blueprint's manage-access role is a Lake Formation administrator.** Sandbox's
  `DataLakeSettings` names `awsds-sandbox-smus-provisioning` and `awsds-sandbox-smus-manage-access`
  beside the one this repository declares, and neither was written here (open question 24;
  `consumer-data-v0.5.0` holds the declared seat under `ignore_changes`, and `DL-13` is what notices a
  change). The manage-access seat acted on nothing in Sandbox while its identity policy carried no
  `lakeformation:` action, until `sagemaker-prereqs-v0.8.0`, whose Glue manage-access policy grants
  `GrantPermissions`, `BatchGrantPermissions`, `RevokePermissions`, `RegisterResource`, the opt-ins and
  the data cells filters on `*`. Applied 2026-10-20, so what the seat grants from then on is what
  DataZone fulfils, the role trusting `datazone.amazonaws.com` from the domain account alone. Its first
  calls, 02:51:23Z: the opt-in on `test-experimentation`'s new database, and a `RevokePermissions` of
  `ALL` from `IAM_ALLOWED_PRINCIPALS` answered `InvalidInputException`.
- **Every user of the domain may be added to any project's member pool.**
  `ADD_TO_PROJECT_MEMBER_POOL` on the root domain unit reads `allUsersGrantFilter`, DataZone's
  default. Both override policy types are empty, so the owner project's approval is the control on a
  subscription — and nothing at the domain level restricts a direct Share. 6f decision 5 (2026-10-27)
  allows none on a lake listing, and `CT-11` detects one from the subscription's record.
- **The domain execution role carries more than the approval verbs.**
  `SageMakerStudioDomainExecutionRolePolicy`, at **v23**, grants the whole subscription cycle plus
  `AddPolicyGrant` and `RemovePolicyGrant` over the policies above, `datazone:GetEnvironmentCredentials`,
  `sts:SetContext` and `q:PassRequest`. It is AWS's document and moves without this repository being
  asked (Lesson 11), which is why a preventive control over publishing or sharing belongs on this role
  rather than in an OU document.
- **A Bedrock model reaches a project as a catalog subscription** (read 2026-10-19 in the console's and
  the portal's code, [Stage 17](plan/stages/stage-17-sandbox-machine-learning.md) decision 13; the
  publishing measured the same evening, the subscription not yet). The console's **Amazon Bedrock models** tab publishes each enabled model as an asset,
  `BedrockModelAssetType` for projects and `BedrockInferenceOnlyAssetType` for the playground, owned by a
  project named `GenerativeAIModelGovernanceProject` and listed with `approvalRequired` `NO`; the asset's
  form names a provisioning or consumption role, held by a custom environment of that project in the
  model's account. A project's first use subscribes to the listing, and the grant's target is an
  application inference profile in the project's account, the only door AWS's policies on the project
  role and on the Bedrock IDE's roles open to a model. The domain holds no governance project, and an
  associated account's console creates none: only the domain account's setup does, in the run that also
  configures the Bedrock blueprints and `Tooling` there, which D22 forbids.
  Here `data-governance/governance/` writes it, and `sandbox/model-access/` the two roles the console
  adopts. Enabling five models created six custom environments, six assets and listings and the
  playground's two application inference profiles, and no role (2026-10-19).

## Connections — how a project reaches something Terraform owns

A **connection** is a domain object that attaches a project to an external resource. This estate has used two
kinds, and both exist because the alternative was a blueprint provisioning something nobody sized:

| Kind | Reaches | Written by | Stage |
|---|---|---|---|
| **S3** | `awsds-sandbox-lake`, per SSO-group prefix | by hand, per project ([`runbooks/sandbox-lake.md`](plan/runbooks/sandbox-lake.md)) | [16](plan/stages/stage-16-sandbox-lake.md) |
| **Redshift** | `awsds-sandbox-warehouse`, one themed **schema** in its `sandbox` database — shareable with several projects | a project member, in the portal ([6h](plan/stages/stage-06h-redshift-connection.md) decision 1). DataZone answers `ListConnections` to Sandbox's `InfrastructureAccess` role since that role was made a contributor to both Sandbox projects on 2026-10-15, and `WH-9` reads the object (`EXC-17`) | [6h](plan/stages/stage-06h-redshift-connection.md) |

**A Redshift connection is three layers, and none of them is the connection.** Read 2026-09-19, for
[6h](plan/stages/stage-06h-redshift-connection.md); the requirement it implements is *access per database ×
project*, and no single mechanism expresses that:

1. **A tag on the workgroup *and* its namespace** — `AmazonDataZoneProject=<projectId>` — decides which
   project may use the compute at all. AWS also documents a wide form,
   `for-use-with-all-datazone-projects=true`, *"to allow all Amazon SageMaker Unified Studio projects in this
   account to access it"*; this estate refuses it, and `WH-7` fails if it appears. The tag is on **two**
   objects, which is Lesson 14's shape, so both come from one authored map in `sandbox/warehouse/`.
   **It is a tag KEY, so it names exactly one project** (read 2026-09-20): AWS's instruction is to add *"1 of
   the following tags"*, and the two options are one project or every project in the account. There is no
   per-project list, so **this layer does not have the grain the requirement asks for** — layer 3 does,
   and admitting a second project is [6h](plan/stages/stage-06h-redshift-connection.md) decision 8 rather
   than a second map entry. `sandbox/warehouse/`'s `projects` variable refuses one at plan time, because the
   alternative is a silent overwrite that breaks the first project's connection with nothing to say which.
2. **The IAM reach** — `redshift-serverless:GetCredentials`, `GetWorkgroup`, `ListTagsForResource` —
   mints the database session, and it sits on **two** roles: the project role, and the per-project
   **access role** the form demands (below). On the Data page `GetCredentials` is called by the access
   role; on a direct notebook session, by the project role (measured 2026-10-10). The project role must
   also fit inside the **D13 project boundary** (INT-15), which is a ceiling, so a grant the boundary does
   not admit reaches nothing; it admits `GetCredentials`. This repository grants `redshift-data:` to
   neither role and neither door needed it, while AWS's `SageMakerStudioProjectUserRolePolicy` v75 grants
   the project role the Data API and `GetCredentials` on a workgroup tagged with its project, every project
   role the same on a workgroup carrying the wide tag and no `AmazonDataZoneEnvironment` tag, and
   `GetCredentials` on any workgroup through `sqlworkbench` (simulated 2026-10-18,
   [6h](plan/stages/stage-06h-redshift-connection.md) 2.2, 5.1 and decision 8). So layer 2 is per project
   on the access role alone. The Query editor adds
   `sqlworkbench:CreateConnection` and `DriverExecute` on the access role, which CloudTrail records as the
   events `GetResources` and `ExecuteQuery`: a refusal's `errorMessage` names the action, its `eventName`
   does not.
3. **A Redshift `GRANT`** decides the database, schema and tables. This is the requirement's own grain, it is
   SQL rather than Terraform, and **nothing in a plan shows it** — including its absence after a project is
   unwired.

Layers 1 and 2 are per *workgroup*; only layer 3 is per *database*. So admitting a project to the warehouse
grants it nothing in any database, which is the asymmetry 6h step 5.2 measures rather than asserts.

**The credential is one of three, and the choice is a control.** AWS: *"The credential type must be one of the
following options: Username and password, IAM credentials, AWS Secrets Manager."* This estate takes **IAM
credentials** — the only one carrying no standing credential — and pays for it in display: *"Using a username
and password enables Amazon SageMaker Unified Studio to display more information for a resource."*

**On the form, IAM credentials is an access role** (measured 2026-09-21). `Access role ARN` is mandatory
on a same-account connection, which AWS's same-account procedure and the field's own help both deny, and
`AWS Secret` is optional beside it. `create-connection`'s `credentials` union has only `secretArn` and
`usernamePassword`, so the IAM path is `awsLocation.accessRole` plus that role's `RedshiftDbUser` tag.
**Redshift prefixes the tag's value with `IAMR:`** (measured 2026-10-10), so a tag carrying the project
role's name yields `IAMR:datazone_usr_role_<project>_<env>`. A connection reading `Available` has minted
no database session; the user appears at the first query. The Data page's path called no
provisioned-cluster API (`DescribeClusters`, `GetClusterCredentials`), so `DenyRedshiftProvisionedClusters`
costs it nothing.

**Two doors, and they have different prerequisites.** *"If you want to query the Amazon Redshift resources
using JupyterLab within Amazon SageMaker Unified Studio, the Amazon Redshift resource must use the same VPC as
the Amazon SageMaker Unified Studio project"*, while *"You can still query using the Data page of your project
if you are using different VPCs."* That is why the sandbox warehouse is in Sandbox's own VPC and why the
governed one in `VPC-Workloads` is unreachable from a notebook by construction — Sandbox does not peer with it,
and the absence is a control (`docs/NETWORK.md` §3).

**The doors resolve to different database users** (measured 2026-10-10). The Data page reaches the
database through the access role, as the per-project user its tag names. A notebook connecting directly
reaches it as the project role, whose session carries a `RedshiftDbUser` SMUS sets per person on every
assume, so Redshift auto-creates `IAMR:user-<Identity Center user id>@<project id>`, holding nothing. A
session tag overrides the role's own tag, and none is transitive, so a notebook that assumes the access
role first lands on the per-project user ([6h](plan/stages/stage-06h-redshift-connection.md) decision 8a;
the recipe is [`runbooks/redshift-connection.md`](plan/runbooks/redshift-connection.md) §J).
`RedshiftDbRoles = datazone_env_<environment id>` rides the portal's session and not the space's, so it
maps nothing on the notebook door.

**`lineageSync` is a scheduled query on an hourly meter.** `awscc_datazone_connection`'s
`redshift_properties.lineage_sync` takes an `enabled` flag and a `schedule`, and every run is a query on a
workgroup billing **1.44 USD/hour** at 4 RPUs. The portal's form offers no toggle for it on this path
(measured 2026-09-21), and the connection the form wrote has the sync enabled; every run to 2026-10-18
failed (§The catalog surface). Switching it off is an `UpdateConnection` by a project member, and
whether to is 6h decision 3, the user's.

**`enable_trusted_identity_propagation` exists per connection**, not only per project profile — which
corrects the premise of open question 13, where TIP is recorded as a profile-level switch whose cost is that
remote access stops working. Unadopted either way; the correction is that the *grain* of the choice is finer
than the question assumed.

**DataZone also models `VPC` and `GIT` connections, scoped to the domain or to a project** (the API model the
AWS CLI 2.37.12 ships, read 2026-10-18). A domain-scoped VPC connection is where the portal and the CI/CD CLI
take a workflow's subnets and security group from before the Tooling environment's; `awsds-studio` held none
on 2026-10-18. Since 2026-09-24 `CreateConnection` takes the project role in `iamProperties.roleArn`.

## S3 — the project's own storage, and where the lake is not

Four distinct S3 relationships meet the SMUS surface. All read 2026-08-19 except where dated
otherwise.

**1. The project S3 path — the project's working storage.** Purpose, in the doc's words: "a secure,
project-isolated location for storing temporary execution data and other project-related artifacts",
structured `<bucket>/<domain_id>/<project_id>/<project_scope>/` "to ensure separation between
projects". Three named tenants: "the location for the provisioned consumer AWS Glue database, Athena
Workgroup output, and temporary storage for individual workflow runs". The bucket pattern in AWS's
2025-09 shared-storage announcement is `amazon-datazone-<account-id>-<region>-<domain-id>`; the
`shared/` scope mounts as a folder in JupyterLab and Code Editor (a space's *personal* work is its
EBS volume, not S3). **Measured 2026-08-22 (v0.3.2)**: the bucket is `awsds-<env>-smus-projects`, one
per member account, created by **Terraform** (the `sagemaker-prereqs` module's house `s3-bucket` call,
not by the service; the `amazon-datazone-*` pattern above is what the wizard would have defaulted to),
handed to Tooling as the `S3Location` regional parameter, and encrypted under the **project CMK** — a
key this project chose, the deliberate exception `docs/GOVERNANCE.md` §Encryption names beside the
data-CMK rule. The name is free because the managed provisioning policy reaches content by the **path
shape** (`*/dzd*/<project>/…`), never by bucket name. **The path shape was measured 2026-08-26** —
Stage 6 step 2.4, verification (xviii)'s remaining third, read-only:
`<bucket>/<domain-id>/<project-id>/<scope>/`, the documented structure, with **two** scopes live,
`shared/` and `dev/`, and **no per-person grain anywhere** — the project id is the finest division the
path has. Since the same evening this path **is** the estate's derived zone ([D19 revised
2026-08-26](plan/decisions/D19-derived-zone.md), the user's decision on this reading:
`awsds-<env>-derived` and the enforced workgroups removed, the persona's Athena path with them;
`docs/GOVERNANCE.md` §"Derived zone" carries the surviving contracts). Two things the reading found
that the documentation does not say:

- **Deleting a project does not delete its path.** Five project prefixes stood under the domain id
  against **one** live project — four orphans of deleted projects, one carrying a whole `.git` tree and a
  notebook. The house `s3-bucket` module gives the bucket versioning, a 90-day **noncurrent** expiry and
  MPU abort; **no rule expires a current version**, so nothing reaps an orphan. This bucket is therefore
  a place where a data scientist's work outlives the project that governed it.
- **The project's own Athena workgroup writes here, and it is enforced.**
  `workgroup-<project-id>-<environment-id>` — the suffix is the **Tooling environment's** id, confirmed
  against `list-environments` rather than inferred from the shape (it is the same suffix the provisioned
  roles carry: `datazone_usr_role_<project-id>_<environment-id>`, underscores there and hyphens here) —
  carries `EnforceWorkGroupConfiguration = true` and an output location of `…/<project-id>/dev/sys/athena/`
  — so the doc's "Athena Workgroup output" tenant is *this* path and **not** the derived zone, the
  premise Stage 6 decision 6 rests on. The Spark workgroup the same blueprint provisions
  (`sagemaker-studio-spark-workgroup-<project>`) exists and has **no** output location: what makes it
  inert is Stage 6 step 1.6's SCP, never the absence of the object, so its existence is expected.

**1a. The vending surface under that same path — S3 Access Grants (measured 2026-08-23).** At first
project provisioning in a member account, SMUS also creates the account×Region **S3 Access Grants**
singleton instance (`default`) and one Access Grants **location** per project — `LocationScope` = the
project prefix, the location's IAM role = the **project role** — with
`enableS3AccessGrantsForTools = true` on the Tooling environment and **zero grants**. This is the
surface the 2026-08-23 laptop-access decision (strategy 1-A, user-approved) builds on: one
per-project, user-authorized **grant** to the `DataScientistAccess` role lets a laptop, from any network
(D39), vend prefix-scoped **project-role** credentials (`s3control GetDataAccess`) — the same identity
Studio uses, so no second permission surface appears over the projects bucket or the project CMK.
The persona's half is a **customer-managed policy**, `awsds-org-project-storage-vending`, created by
each member's `foundation/` slice and referenced by name from `DataScientistAccess` (applied
2026-08-23) — one object per member account, each naming its **own** account's instance, and a policy
may name a resource that does not exist. The second member's instance never existed and since
2026-09-06 never will: that account is the headless `Staging`, and its vending policy went at Stage 6b
step 2.2. The consumer is **`s3-read-write/`**, whose README carries the grant recipe and the
first-run probe sequence. Two properties: grants are **membership-blind** (the grantee grain is the
persona role — every set holder vends for every granted project), and the vended credentials are
**bearer** for their duration (the OQ-14 shape). Requests are metered: USD 0.03 per 1,000 non-delete
AG calls (`PRICING.md` §5).

**1b. Lake Formation over the same path — registration, conditional grants, and what the portal
creates (measured 2026-09-12: CloudTrail since 2026-08-20, and the objects read back).**

- **The service registers each project's `dev/` scope.** At project creation
  `awsds-<env>-smus-provisioning` (session `AmazonDataZoneEnvironmentDeployer-*`, via
  `datazone.amazonaws.com`) calls `RegisterResource` on `…/<project-id>/dev/` with the **project role**
  as registration role, `HybridAccessEnabled = false` and `WithFederation = false`. At deletion it calls
  `DeregisterResource`, and the prefix stays (item 1). Sandbox's trail holds five registrations and four
  deregistrations; `list-resources` returns the live project's alone. `shared/` is not registered.
  `./aws/datalake.py` `DL-14` reads the list.
- **The service grants to a condition, not to a role.** The provisioning role runs
  `BatchGrantPermissions` to `<account-id>:IAMPrincipals` and `arn:aws:identitystore:::user/*`, each with
  the condition `context has datazone && context.datazone has projectId &&
  context.datazone.projectId=="<project-id>"`, Lake Formation's ABAC grant: the attribute is on the
  caller's session, never on the data. LF-TBAC, the lake's form (`GOVERNANCE.md` §Access control), puts
  it on the object as an LF-Tag. Lake Formation evaluates a principal's permissions as the union of its
  grants, named-resource and LF-Tag alike (`REFERENCES.md`), so a tag on a project table neither gates
  nor blocks these grants, and DataZone documents no LF-TBAC support for the Glue assets it manages
  (Stage 6f 3.2). At project creation it grants `DATA_LOCATION_ACCESS` on the `dev/` location and `DESCRIBE` on `default`, the
  database the first project created (2026-08-22); at deletion `BatchRevokePermissions` removes the
  same pair. Lake Formation's ABAC page does not describe `context.datazone` (`REFERENCES.md`), and
  which sessions carry it is unmeasured. Neither SMUS role has granted, revoked or registered anything
  on `raw` or `curated`, and the project role's `glue:GetDatabase` on both resource links is refused:
  *"Insufficient Lake Formation permission(s): Required Describe on raw"*.
- **A portal "Create database" is a Glue call made by the provisioning role.** *Data → Catalogs →
  AwsDataCatalog → Create database* produced `glue:CreateDatabase` with the description *"Created by
  DataZone for project <name>"*, `LocationUri` `…/<project-id>/dev/data/catalogs/` and
  `CreateTableDefaultPermissions: []`, and wrote no object. The grants followed within eight seconds. The
  two conditioned principals received `CREATE_TABLE`, `DESCRIBE` and `DROP` on the database, and
  `SELECT`, `INSERT`, `DELETE`, `ALTER`, `DROP` and `DESCRIBE` on all its tables.
  `awsds-<env>-smus-manage-access` received `CREATE_TABLE` and grantable `DESCRIBE` on the database, and
  grantable `DESCRIBE` and `SELECT` on its tables. The manage-access role then called
  `lakeformation:CreateLakeFormationOptIn` for the conditioned principal on the database and was refused
  (*"no identity-based policy allows"*); the query below succeeded without the opt-in. The portal's
  *Create database* deploys a `DataLake` environment, `create-datalake-database-env-<name>-<epoch ms>`,
  and the refusal failed it: `AmazonDataZoneSageMakerManageAccessRolePolicy` v4 carries no
  `lakeformation:` action, and `AmazonDataZoneGlueManageAccessRolePolicy` v18 carries the opt-in (read
  2026-10-20). With both on the role, Staging's environment reached `ACTIVE` (Stage 18 7.2);
  `sagemaker-prereqs-v0.8.0` attaches both in Sandbox, applied by the user 2026-10-20 (6f step 2.0). The failed
  environment's stack was deleted and the database stayed, the template's `GlueDatabase` being
  `DeletionPolicy: Retain`, so `mydatabase` exists outside any environment.
- **A table created by uploading a file points at a folder the upload flow chose, not at the database
  location.** The Parquet landed at `…/dev/local-uploads/<epoch-ms>/<name>.parquet`. `glue:CreateTable`,
  called by the project role from the browser, set that folder as the table's location: `EXTERNAL_TABLE`,
  `ParquetHiveSerDe`, `IsRegisteredWithLakeFormation: true`. An external table stores the schema and the
  location; its rows are read from the folder's objects at query time.
- **The query editor and the querybook are separate surfaces.** The query editor runs through SQL
  Workbench: `sqlworkbench:ExecuteQuery`, then `athena:StartQueryExecution` from
  `sqlworkbench.amazonaws.com` as the project role, then `lakeformation:GetDataAccess` for `SELECT` on
  the table. A `SELECT … LIMIT 10` returned 10 rows (`OutputRows`), with results in `dev/sys/athena/`. A
  querybook is a DataZone notebook of type `SQL`, and its cells need a managed compute; §"Querybook
  compute" records why none started.

**2. Project files storage — S3, and a git repository beside it, not instead of it** (measured
2026-08-26). The documentation reads *"S3 or Git"*; the profile answers it directly. The `Tooling`
configuration carries five parameters — `gitConnectionArn`, `gitFullRepositoryId`, `gitBranchName`,
`isNewGitRepository`, `enableProjectRepositoryAutoSync` — and in **both** profiles every one is empty
or `false`. So it is not an either/or: the S3 project path is the storage regardless (the live
project's is full — item 1 above), and the repository is an **additional**, currently unconfigured
binding carrying an **auto-sync** flag. **`gitConnectionArn` is `isEditable = false`** — the blueprint
template's own doing, not a lock this project wrote — so a project cannot bring its own connection and
the profile must carry one: **no project in this domain can have a project repository today.** Whether
enabling it *syncs* the folder or *replaces* it is unmeasured. The connection is Stage 7's surface
(INT-09/INT-13), and **open question 26** carries the promotion question all of this opens. **Read 2026-10-25 on AWS's pages** (`upstream-releases.md`): since 2026-07-30 Git connections are created and enabled at the account level (*Settings → Account settings → Git connections*), reach every domain and project in the account, may come from another account through RAM, and new project profiles no longer choose S3 or Git; whether this domain's page offers the GitLab self-managed flow, and what it asks, is a console reading owed in Data Governance (the waiting list, INT-13).

**3. The lake — reached through the catalog, never mounted.** Governed data enters a project by
publish/subscribe on the SageMaker Catalog, fulfilled on the Lake Formation substrate Stage 5a built
(the TBAC shares; applied grants in `docs/AWS_STATE.md`'s register). The `DataLake` blueprint
provisions the *consumer-side* Glue database and workgroup, whose **output** lands in the project
path — the `awsds-data-*` buckets themselves stay behind Lake Formation. The enforcement that keeps
it that way is D13's boundary (Stage 6 step 2.1): no `s3:*` on LF-registered prefixes for project
roles, with the drop-box `PutObject` on the dated prefix as the one sanctioned direct write
([`GOVERNANCE.md`](GOVERNANCE.md) §Drop-box, INT-10).

**4. Existing buckets as catalog assets.** An existing bucket or prefix can be published into the
catalog as an **S3 Object Collection** asset — a curated, versioned *metadata* object under
subscription rules. No stage uses it: this lake's path into the catalog is tables on the LF
substrate, not object collections.

Three things in a member account all answered to "working storage" — **two buckets and a workgroup**.
Since 2026-08-26/27 there is one: the other two were destroyed with D19's revision, and their rows are
kept struck as the record of what the account used to hold.

| Object | Created by | Holds |
|---|---|---|
| `awsds-<env>-smus-projects`, a **bucket** (the project path lives inside it) | **Terraform** — the member's `sagemaker-prereqs` slice (v0.3.2), consumed by Tooling's `S3Location`; settled 2026-08-22 | `shared/` files, the blueprint workgroup's Athena output, workflow temp, the consumer Glue database location, the portal's file uploads behind the tables they created (item 1b) |
| ~~`awsds-<env>-derived`, a **bucket**~~ | ~~`consumer-data` (Stage 5a pass 4a)~~ | **Destroyed 2026-08-26/27.** Held the persona's derived zone — per-user write, persona-grain read, the `scratch/` prefix |
| ~~`awsds-<env>-athena`, **a workgroup, not a bucket**~~ | ~~`consumer-data` (Stage 5a pass 4a)~~ | **Deleted 2026-08-26/27**: `DeleteWorkGroup` counts query *history* as contents, so it took `RecursiveDeleteOption` after refusing the plain destroy. It was the *enforced* workgroup, forcing results into `s3://awsds-<env>-derived/results/` under a 10 GiB cap |

Step 2.4 measured the destination on **2026-08-26**: the project's own workgroup is enforced into
`…/<project-id>/dev/sys/athena/`. The user's answer was not to repoint anything but to **keep the
service's destination and delete ours** ([D19 revised](plan/decisions/D19-derived-zone.md)).

Two consequences follow from the deletions. Pass 4c's boundary — the persona's Athena family scoped to
the two *enforced* workgroup ARNs, with a blueprint-provisioned project workgroup outside that scope —
has no subject left: `DataScientistAccess` carries **no `athena:` action at all**, so the project
workgroup is the only one, exercised by project roles because there is no other kind of caller. And
*"whether the two query paths stay parallel or converge"* (TIP — Stage 6 decision 2) is moot from the
same date for the same reason: there is one path. TIP itself was delivered `false` and non-editable in
both project profiles.

## SageMaker configuration

### `VpcOnly` — where the traffic runs

When `Tooling` provisions a project's SageMaker AI domain, the domain is created in one of two
network modes:

| Mode | Where app traffic runs |
|---|---|
| `PublicInternetOnly` | apps run with direct internet access through an **AWS-managed** network — outside the account's VPC, routes, security groups and flow logs |
| `VpcOnly` | apps attach ENIs **inside the account's private subnets** — every packet crosses the account's own routes, security groups and flow logs |

**Why this is load-bearing here:** the whole data perimeter
([`architecture.md`](plan/architecture.md) §4.2) is built from controls that only see traffic
inside the VPC — the gateway/interface **endpoint policies** (Stage 3's S3 allow-list), the
**`aws:SourceVpce`** conditions on bucket policies, the **flow logs**, and both D5 egress designs.
An app in `PublicInternetOnly` reads the lake and talks to the internet without touching any of
them: "private by default" would be true of the account and false of the thing the data scientist
actually runs. The same logic disables Athena Spark — its sessions and executors run outside the VPC
(no `NetworkConfiguration` in the API; the 2026-04 PrivateLink release moved only where a session is
reached *from*, not where it runs — open question 12, Stage 6 step 1.6).

**The consequences of choosing it:**

- **Every AWS service an app reaches needs a VPC interface endpoint in the account**, under the admin
  guide's premise of no public egress from the VPC — its "network isolation", which is design B and
  **not** a property of `VpcOnly`. Design A is gone since 6c step 5.1, and 5.2 completed the required
  set: **18 endpoints in `sandbox/egress/`**, each checked against the Region's own catalog. The
  guide's required list is `athena`, `datazone` + `datazone-fips`, `ec2`, `ec2messages`, `q`, `s3`,
  `sagemaker.api`, `sagemaker.runtime`, `glue`, `kms`, `secretsmanager`, `sts`, `ssm`, `ssmmessages`
  (re-read 2026-08-19; `REFERENCES.md` — Stage 6 step 4.2 points here rather than carrying a second
  copy), plus per-blueprint optional ones. Each costs **USD 0.010/h** (~USD 7/month) per account,
  continuously — the hidden fixed cost a new blueprint can carry. **The same page's third table caps
  the direction (read 2026-08-24): the portal requires the public internet** — client assets, client
  APIs (`agent.datazone.<region>.api.aws` among them), the IdC sign-in endpoints — while an interface
  endpoint's private zone shadows exactly such subdomains (`NETWORK.md` §5, the measured break). A
  no-egress VPC can host the *apps*; it cannot host the *portal experience*. **The portal experience is
  assigned to the client plane by requirement** (the 2026-08-25 objectives clarification; D5
  re-scoped; D39): the user's browser reaches those public names from whatever network the laptop is on
  — through the institutional HTTP/HTTPS proxy while it is on the monitored VPN profile — never through
  the compute VPC's. What the compute VPC owes the portal is only that its endpoints not shadow the
  client's DNS.
- **The required table's framing carries a premise this design does not meet** (Lesson 41). The page
  introduces the list with *"The Amazon SageMaker Unified Studio portal calls the following AWS
  services"*, and its `DenyUserAccessFromUnauthorizedVPCs` example is written for *"portal calls to AWS
  service APIs from outside the allowed Amazon VPC"* — AWS is describing an estate in which **the
  user's browser resolves and routes through the same VPC as the compute**. Ours does not, by decision:
  the client plane resolves through `VPC-Networking` and, on the monitored profile, leaves through the
  institutional proxy (D38),
  while the compute plane keeps its own endpoints. So **the compute needs only the subset of that list
  that its own calls use**, and chasing the rest buys nothing — every name in the page's *public
  internet* tables is the browser's, which the page states three times (*"These endpoints are used by
  the Amazon SageMaker Unified Studio portal"*, and once *"...by the AWS console"*).
- **A space started while the endpoint set is down does not fail — it hangs** (measured 2026-09-07, 6c
  step 6.2). JupyterLab loads, the terminal works, the banner *"IDE configuration in progress"* never
  clears and a kernel never returns: the app's DataZone and SageMaker calls have **no path at all** under
  design B — no default route, no endpoint — so they get silence rather than an error (Lesson 42).
  `make up ENV=sandbox` and a stop/start of the space cleared it. The discriminator from the space's own
  terminal: `getent hosts sts.us-west-2.amazonaws.com` → `10.20.x.x` and
  `curl https://sts.us-west-2.amazonaws.com/` → `302` with the endpoints up; public addresses and a
  timeout without. The working terminal is what makes it look like a Studio fault, not a network one.
- One required entry cannot be satisfied in-Region: the `q` row pairs with
  `com.amazonaws.us-east-1.codewhisperer`, *available only in `us-east-1`* — a `us-west-2` VPC
  cannot reach it through an interface endpoint at all (Stage 6 step 4.2 records what that breaks).
- **The page's optional table is not optional once a blueprint is enabled.** It is introduced with
  *"Create these Amazon VPC endpoints if you plan to deploy Amazon SageMaker Unified Studio projects
  that include blueprints using the services listed below"* — so it is keyed to the **enabled blueprint
  list**, not to taste. This estate's category 1 contains the seven `AmazonBedrock*` blueprints and
  `EmrServerless`, whose rows are `bedrock-agent`, `bedrock-agent-runtime`, `bedrock-runtime` and the
  `emr-serverless`/`elasticmapreduce` family. With a NAT their absence was invisible; with **no default
  route** a project using either blueprint fails on first use. **The enabled-blueprint list and the
  endpoint list are one decision** — enabling a blueprint has an hourly price that is not the
  blueprint's own (Stage 6c step 5).
- **`sagemaker.runtime` carries an AZ affinity the rest of the list does not** (SageMaker AI developer
  guide, read 2026-09-05): *"you must ensure that the VPC interface endpoint is activated in the
  Availability Zone of your client in order for private DNS resolution to work. Otherwise, you may see DNS
  failures when attempting to resolve the URL."* This collides with D9's single-AZ rule for metered
  resources whenever an app lands in the other AZ, and it fails as a **resolution error**, not as the
  cross-AZ data charge D9 weighed. Stage 6c step 5 carries the three ways out and the recommendation.
- **The `s3` entry in that list is verified, not provisioned on faith** (Stage 5a pass 4d). Each account
  already carries a `[P]` **gateway** endpoint for S3, whose prefix-list route is more specific than
  any default — so where that route is on an app subnet's route table, S3 traffic takes the
  **gateway**, and the request arrives carrying the **gateway's** `aws:SourceVpce`, not the interface
  endpoint's. Stage 5a measured this on the VPN home and it cost a working control: a network condition
  written for one endpoint id silently failed to match traffic that took the other (Lesson 33). **Stage
  6 step 4.2 owes a measurement** — for each project subnet, which S3 route wins, and which endpoint id
  the resulting call presents in CloudTrail. Every `aws:SourceVpce` list the SMUS projects must satisfy
  (the lake's `trusted_vpce_ids`, the derived buckets') is written against that answer, and the failure
  mode if it is guessed is the 4d one: an `AccessDenied` on a path everybody believes is allowed.

**How it is enforced:** `VpcOnly` is already the blueprint **default** (read 2026-08-16). Stage 6
step 1.5 sets `sagemakerDomainNetworkType = VpcOnly` in both project profiles and marks the parameter
**non-Editable** — the *Editable* flag is what turns a default into a control (Lesson 5): the
parameter exists so nobody can flip a project to `PublicInternetOnly`.

### Querybook compute

A querybook, the SQL notebook the portal opens from the catalog, runs its cells on a managed compute
that `datazone:StartNotebookCompute` starts. In Sandbox that call fails with
`ServiceQuotaExceededException`, which the portal shows as status code 402 (measured 2026-09-12, six
attempts by the project role):

- `L-F63F402C`, *SageMaker Unified Studio Querybooks running on sc.t3.medium instances*, reads **0**
  against an AWS default of **5**. `L-B3401D17` (*Querybook Runs running on sc.t3.medium instances*)
  reads 0 against 5, and `L-85C9EC5A` (*The maximum number of concurrent notebook runs per account*)
  0 against 15. Of the 81 `sc.*` quotas in the `datazone` service code with a default above zero, 79
  read 0; the two others are `L-DBBAE884` (*Notebooks running on sc.t3.medium instances*, 2 against 6)
  and `L-B890B049` (*Compute environments running on sc.t3.large instances*, 5 against 5). No increase
  had been requested before 2026-09-13.
- The request names where the compute would run: `networkAccessType = VPC_ONLY`, `awsds-sandbox-vpc`,
  the subnets `awsds-sandbox-private-usw2-az1` and `awsds-sandbox-private-usw2-az2`, the security group
  `datazone-<project-id>-dev` (*"Security group for the project."*), the project role as execution role,
  and the project path under the project CMK as storage. That is the placement `VpcOnly` asks for,
  read from a request that never ran; the compute's own calls, and their path through the endpoints and
  the proxy, are unmeasured.
- The price list has no querybook usage type. `UnifiedStudio:Notebook-sc.t3.medium` is USD 0.050/h
  in `us-west-2` (`PRICING.md` §8); what a querybook bills under is unmeasured.
- The user requested the three at their defaults on 2026-09-13: `L-F63F402C` and `L-B3401D17` at 5
  (`PENDING`), `L-85C9EC5A` at 15 (`CASE_OPENED`), all three still applied at 0 when read at 03:46Z. A
  request below the default is refused with `IllegalArgumentException` (*"You must provide a quota value
  greater than the default quota value of 5.0"*), and a request equal to the default is accepted. An
  approval turns on a compute surface this estate has not measured. The query editor runs Athena
  through SQL Workbench without it (§S3 item 1b). The three requests were closed on 2026-09-24 07:49Z
  without an increase, and the applied values still read 0 on 2026-10-17 (6d log), so the Querybook
  has no capacity in this account until a new request.

A DataZone notebook is of type `SQL`, the querybook, or `DATA`, the native notebook the user guide documents
beside JupyterLab and Code Editor (the API model and the guide, read 2026-10-18). `L-DBBAE884` above reads 2,
and its name makes it the `DATA` notebook's quota (inferred, unmeasured), so one may start here. The native
notebook's kernels run in the
domain-level VPC configuration (since 2026-04-23); Athena for Apache Spark is still its default Spark runtime
and still outside any VPC (open question 12); and since 2026-08-19 its Athena, Redshift and EMR Serverless
sessions carry the Identity Center identity in a project whose profile enables TIP, while Glue and EMR on EC2
stay in compatibility mode. Remote space connections remain unsupported in such a profile, so Stage 6
decision 2 holds. The SageMaker Data Agent these notebooks and the Query Editor offer stores prompts in the
domain's Region and may infer in another.

### Custom images (BYOI) — and how they are named

A project's spaces run the **SageMaker Distribution** unless a custom image is attached to the
SageMaker AI domain `Tooling` provisions in the member account: an image, an image version and an app
image config, then the domain's `CustomImages` (Stage 6 step 5.1). INT-01 closed on 2026-09-10 (6d
step 2.5); INT-17's open half is whether the attachment survives a blueprint reconciliation, which is
verification (vi) and 6d step 2.4.

**Three of the four objects are Terraform's, and the fourth is the blueprint's** (measured 2026-09-10,
Stage 6d step 2). `sandbox/dev-env/` holds the image, the version and one app image configuration per
app type; `CustomImages` is a field of the domain's user settings, so making an image *selectable* is a
hand step against an object `Tooling` owns, and `UpdateDomain` replaces `DefaultUserSettings` whole
(Lesson 60). A **space** carries no image *list* — `SpaceSettings.CodeEditorAppSettings`
has neither `CustomImages` nor `LifecycleConfigArns` — **but it does name one image and one version**,
in `DefaultResourceSpec`, and that copy **overrides the domain's default for that space** (measured
2026-09-12, correcting the 2026-09-10 reading above, which said a space cannot name an image at all).
The copy is written when the space is created and never revisited, so a release reaches new spaces
only, and a deleted version strands the spaces that name it — `AWS_STATE.md` `EXC-09`,
[Lesson 63](plan/lessons.md), and the move is [`dev-env.md`](plan/runbooks/dev-env.md) §B, *Moving a
space*. **A domain entry with no `ImageVersionNumber` offers every version of the image** in the
picker, newest first, and the portal's `CreateSpace` pins the chosen one (measured 2026-10-15), which is
how this estate attaches the house image since Stage 8 decision 7: a release is a new version and no
domain write. **AWS's own images are named by a mutable alias** (`SageMakerImageVersionAlias`) rather
than a version ARN; a custom image's alias works the same way in a space's spec, and the portal then
banners that space as an outdated SageMaker Distribution (2026-10-15). Two principals read the repository and they are not the same one: at `CreateImageVersion` the image's
`RoleArn` reads it **by tag** and pins the version to a digest; when a space starts, the **project
role** reads it **by digest**, so a space never sees the tag. Both a **JupyterLab** and a **Code
Editor** space started on this image (2026-09-10) from the `DefaultUserSettings` block, with
`DefaultSpaceSettings` empty as the control. The recipe, per account and per release, is
[`runbooks/dev-env.md`](plan/runbooks/dev-env.md).

**The `SageMakerAIDomain` blueprint carries the attachment as profile parameters** (read 2026-10-30 from its
template; [`upstream-releases.md`](plan/upstream-releases.md)). `customImagesJupyterLab` and
`customImagesCodeEditor` take a JSON list of `ImageName`, `AppImageConfigName` and `ImageVersionNumber`
(measured 2026-10-30: the template's own `name;config;version` triple, written in the profile, fails the
environment's validation with `[]`; the service translates the JSON into it), which the template writes
into the domain's `CustomImages` with the version number set, and `defaultImageVersionArn*` into
`DefaultResourceSpec`; so on a project born of such a profile the attachment is Terraform's
(`governance/profiles.tf`), survives a reconciliation by construction, and pins one version per profile: the
no-version entry the portal reads as every version is not expressible, and a release is a profile change and
an *Update project* per project. `hiddenSageMakerImageVersionAliases` hides versions of
`sagemaker_distribution` from the picker, the case of 2026-09-12 below. 6d decision 15 (b) took it to
`experimentation` on 2026-10-30: the pilot's parameters are `governance/locals.tf`'s
`sagemaker_ai_domain_parameters`, the pin `var.sandbox_dev_env_version`.

**What the app image configuration cannot carry is the proxy environment.**
`ContainerEnvironmentVariables` caps each value at 256 characters against a generated `NO_PROXY` of
1,514 characters (52 entries, 2026-09-12), so the mechanism Stage 6c step 5.6 and Stage 6d step 8.4
both assumed does not exist. 6d
decision 8 (2026-09-10) puts the six variables in the **image** instead — `ENV` in
`gitlab/awsds/dev-env/dev-env/Dockerfile`, the bypass list a dated literal there — which makes the image
estate-shaped: an endpoint added to the account's list is a Dockerfile edit, a rebuild, a new tag and
every space moved to the new version.

**What such an image must satisfy** — the `public.ecr.aws/sagemaker/sagemaker-distribution` ancestor at
≥ `2.6-cpu`, **no `ENTRYPOINT`**, AWS's three owned paths, the EBS mount at `/home/sagemaker-user`, the
activity-monitor extension idle shutdown reads — is [`gitlab/awsds/dev-env/README.md`](../gitlab/awsds/dev-env/README.md)'s and
Stage 6 step 5.0's, and is not repeated here. This section owns the **naming**: Stage 8 step 1's
pipeline inherits whatever convention the first push wrote, and both repositories are
**tag-immutable**, so a tag is spent the first time it lands.

#### The image reference

```
<account-id>.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-dev-env:default-v0.1.0
└──────────────── registry ─────────────────┘└──── repository ────┘└──── tag ────┘
```

**Both repositories live in the Production account, and the `prod` in their names is where the
*registry* is, not who the image serves.** `terraform-live/production/registry/ecr.tf` builds them as
`awsds-${var.env}-ecr-*` with `env = prod`, and Sandbox and Staging reach them by
`AllowConsumerAccountsToPull`. Reading the pair as "one for production, one for development" inverts
D17: there is **one** ancestor for every environment, and what gets promoted is the code, never a
per-environment image.

| Repository | What it is | Who pulls it |
|---|---|---|
| `awsds-prod-ecr-base` | the **common ancestor** (D17) — every application image is `FROM base`, `dev-env` included | Stage 8's pipeline; the consumer accounts carry the pull grant on purpose, so a project building its own image does not read a missing grant as a network fault |
| `awsds-prod-ecr-dev-env` | the **SMUS custom image (BYOI)** — the runtime a space actually starts | the member accounts, through `CustomImages` |

So the repository already answers *what the image is*. Putting that word back inside the tag —
`awsds-prod-ecr-dev-env:dev-env-…` — spends it twice in every pipeline line that ever references it.

#### The tag rule

**`<flavour>-v<major>.<minor>.<patch>`, and the same number in both repositories.** That is the
release, the protected tag on the GitLab project `awsds/dev-env`; the images its pipeline pushes carry
`-<short sha>` after it, the commit built, so two builds of one release never meet in a tag-immutable
repository (Stage 8 step 1.1). The hand builds, `default-v0.1.0` to `default-v0.6.0`, carry none. The
first release the pipeline registered is `default-v0.7.1-c268de48`, Sandbox's version 7 (2026-10-15).

The **flavour** is the axis this estate branches on, decided by the user on 2026-08-22 while choosing
the first tag: a project wanting **GPUs**, one wanting **Spark** libraries, and one wanting neither
are three different runtimes, and the plain one is named `default` rather than left implicit. **The
flavour axis reaches `base` too** — a GPU `dev-env` descends from
`sagemaker-distribution:<version>-gpu`, a different digest and therefore a different ancestor, so the
branch happens at `base` first. If only `dev-env` carried the flavour, the day a GPU base arrives
`base:v0.1.0` silently starts meaning *the CPU one*.

**Why flavour first and version second**, when the ancestor itself writes `4.3.0-cpu` the other way
round: the lifecycle policy is what selects a subset of these tags, and *"keep the last N GPU images"*
is a rule worth having separately from the CPU ones, because a GPU image costs several times the
storage.

**The policy already exists.** `terraform-modules/ecr-repo` gives every repository two rules, applied
and read back (`./aws/supplychain.py` reports `LIFECYCLE: yes`): **untagged expire after 14 days**, and
**tagged images are kept to the most recent 30** — selected with `tagPatternList = ["*"]`, so **rule 2
counts every flavour together**. That is the collision: the day a second flavour exists, a burst of
`default-` pushes evicts `gpu-` images that nothing else would have touched, and the fix is to split
rule 2 per flavour. The flavour segment is what makes that split expressible.

**What flavour-first buys** (read 2026-08-22): ECR's simpler selector, `tagPrefixList`, matches a
**prefix** only, so flavour-first is selectable with it and groups the flavours in any listing — but
`tagPatternList` takes up to four `*` wildcards per string, would match `*-gpu` just as well, and is
both AWS's stated best practice and what this module already uses. So the ordering is **readability and
convenience, not capability**. Before amending that rule either way: the two selectors are **mutually
exclusive** within a rule, and *"if you specify multiple tags, only the images with all specified tags
are selected"* — an **AND** where a list reads like an OR.

**Why one number across both repositories.** `dev-env` is `FROM base`, so a change to `base` rebuilds
`dev-env` from its first layer — Julia, R and Rust download again. The two therefore never move alone,
and a shared number says so; **Stage 7 step 2.6**, which fills the CA-install layer with the internal
PKI root, took both to the next free minor, `default-v0.6.0` (2026-10-12). The tags spent so far, with their
dates, digests and what each changed, are [`gitlab/awsds/dev-env/README.md`](../gitlab/awsds/dev-env/README.md) §*The releases*.

**When a flavour graduates from a tag to its own repository.** The trigger is reaching for a knob that
exists **per repository and not per tag**: a different set of accounts allowed to pull (the repository
policy), a different retention (the lifecycle policy), a different scan configuration, or a different
KMS key. Until one of those differs, a flavour is a tag — reversible, and one `module "ecr_…"` block
cheaper.

**The tag is not the identity — the digest is.** A tag is a movable pointer everywhere except here,
where `IMMUTABLE` freezes it on first landing; what Stage 6 step 5.1 registers as an image version and
what Stage 7 step 2.6 must be able to say it replaced is the **digest**, which is why both are recorded
in the stage log at push time. The image cannot be asked either: `dev-env`'s own
`/opt/awsds-runtimes.txt` records the **build-time** reference (`awsds/base:local`), not the ECR tag it
was later given.

**Applied 2026-08-22, Stage 6 step 5.0:** `default-v0.1.0` in both repositories.
**2026-09-08, Stage 6d step 9.5:** `default-v0.1.1` in both — the same recipe rebuilt to exercise the
`open` build plane, so the bump is a **patch**. Digests: `base` `sha256:a4b763a3…1ea6`, `dev-env`
`sha256:6916fc13…6d13`.

#### The hand-off to the pipeline

The convention was written by a hand build; **Stage 8 step 1 is where a pipeline takes it over**, and
it changes shape once on the way (all three rows settled 2026-08-22, the stage files carrying the same
words):

| Who builds | Tag | Why the difference |
|---|---|---|
| the two **hand** builds — Stage 6 step 5.0, Stage 7 step 2.6 | `<flavour>-v<semver>` | there is no pipeline provenance to record; the tag is exactly the release |
| the **pipeline**, Stage 8 step 1.1 | `<flavour>-v<semver>-<short-sha>` | two runs of one release tag must not collide where a tag is spent on first landing — and the suffix's absence is what identifies the two hand-built images forever |
| **application** images (`app-etl` and successors), Stage 8 step 2 | `v<semver>-<short-sha>` — **no flavour** | the flavour axis is about *runtimes* branching (GPU, Spark, plain); an application does not branch that way, and a mandatory `default-` would be a word that never varies |

One consequence reaches GitLab: the protected-tag pattern for `dev-env/` was `v*`, which **does not
match `default-v0.2.0`**. Since a Community Edition release gate *is* the protected tag (who may create
it), leaving the pattern alone would quietly unprotect every release of this repository while the
settings page still reads as protected. Stage 8 step 1.0 specifies `*-v*` and says to verify it by
attempting a tag creation as a Developer — the application repositories keep `v*`, because their tags
have no flavour segment.
