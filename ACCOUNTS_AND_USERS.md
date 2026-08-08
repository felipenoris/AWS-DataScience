
# AWS Accounts

Nine accounts, in four organizational units. The account is the isolation boundary; the OU is the policy
boundary, so each OU is named for the policy set it carries rather than for its contents (`GENERAL_PLAN.md`
D23).

## The two axes, and the accounts that sit on neither

The accounts do not form a single sequence. Reading them as one — "sandbox, then dev, then staging, then
prod, and some others" — is what produces the recurring question of whether a given account is "a
production account". There are three groups, and the distinction decides what each account is allowed to
hold:

- **Lifecycle axis** — how mature and how protected the compute in an account is. This is the axis
  promotion runs along: **Development → Staging → Production**, with **Sandbox** sitting *before* the
  chain rather than at its head (work graduates from Sandbox into a Development repository through git,
  never through a pipeline). An account on this axis holds **compute**, and its policy set is about what
  that compute may do.

- **Ownership axis** — who owns a dataset, answers for its quality and decides who may read it. The lake
  outlives every application that reads it, so tying it to an environment account would tie the data's
  life to a deployable thing's life, and force a copy per environment. **Data Governance** is the only
  account here. It holds **state and governance**, not compute, and every environment reaches it through
  Lake Formation cross-account shares.

- **Neither axis: platform accounts** — the organization's own machinery. They serve every account and
  belong to no environment: the Organization itself (Management), the tamper-evident log store
  (Log Archive), the security findings plane (Audit) and the access-management plane (Identity).

**A consequence worth stating explicitly, because it comes up every time:** an account off the lifecycle
axis is *not* "a production account". Data Governance, Identity and Audit are not production; they are
cross-cutting. Several of them are nonetheless **high blast radius** — whoever controls Identity can grant
access to any account, and whoever controls Data Governance decides who reads which dataset. Sensitive and
production are different properties, and only the second is a point on the lifecycle axis.

A second refinement, the same one D14 makes for GitLab: **the boundary is the control plane, not the
account.** A human may *use* a service hosted in an account they can never administer — GitLab in
Production over the VPN, the SageMaker Unified Studio portal hosted in Data Governance. Using the service
is not signing in to the account.

| Account | OU | Axis | Policy set the OU carries |
|---|---|---|---|
| Management | root | Platform | Bootstrap only, manual, never managed by Terraform |
| Log Archive | Security | Platform | Control Tower guardrails |
| Audit | Security | Platform | Control Tower guardrails; delegated security administration |
| Identity | Security | Platform | Control Tower guardrails; delegated Identity Center administration |
| Sandbox | Interactive | Lifecycle (before the chain) | Interactive compute allowed; human infrastructure changes denied |
| Development | Interactive | Lifecycle (head of the chain) | Same as Sandbox — the two differ in content, not in policy |
| Data Governance | Data | **Ownership** | No user compute; catalog maintenance excepted by name; deletion denied |
| Staging | Workloads | Lifecycle | No interactive compute; no human control plane |
| Production | Workloads | Lifecycle (end of the chain) | Same as Staging |

## Management Account

- represents the root account. Never touch it. This will be used only to bootstrap the AWS environment manually. All further actions will be performed using auxiliary accounts.

## Sandbox Account

- Represents an experimentation sandbox environment, where the unit of work is a notebook. Sandbox users will use this to experiment and develop artifacts.

- **Target of the `experimentation` project profile** (`GENERAL_PLAN.md` D26). The SageMaker Unified Studio
  domain lives in Data Governance, but the compute does not: when a data scientist creates an
  experimentation project, its blueprints provision the environment — the SageMaker AI apps, the project
  bucket, the execution roles — **into this account**. Arbitrary code runs here, against this account's
  data and behind this account's egress controls, exactly as it did before the domain existed.

## Development Account

- Represents a development environment, where the unit of work is a pipeline (repository with tests, workflow definitions). In contrast with the Sandbox environment, the Development environment uses git, CI and automation tools.

- **Target of the `engineering` project profile** (D26), by the same mechanism as Sandbox. This is the head
  of the promotion chain: what leaves this account as a git tag is what Staging and then Production
  receive.

## Staging Account

- Staging area before promotion to Production.

## Production Account

- represents the production environment. All actions in this account will be done using terraform.

## Data Governance Account

Renamed from `Data Management` on 2026-08-08, when the SageMaker Unified Studio domain was placed here
(D26): the account already owned the *technical* catalog, and it now owns the *business* catalog as well,
so its name should say governance rather than storage.

**What it owns — the state of data:** the raw and curated S3 buckets (Iceberg), the Glue Data Catalog,
Lake Formation with the LF-Tags and the D13 registrations, the data classification scheme, and the
ingestion drop-box.

**What it owns — the governance of data:** the **SageMaker Unified Studio domain** (a DataZone V2 domain)
and everything the domain registers: the project inventory, the project profiles and blueprints, the
account associations, project memberships, Git connections, and **SageMaker Catalog** — the business
catalog, glossary, data products and subscription requests.

**What it does not own: compute.** A domain is a registry, not a runtime. It holds no notebook, no app, no
training job and no project bucket; blueprints provision all of that into the *associated* accounts
(Sandbox and Development), decided by the project profile. Two exceptions exist, and both are named rather
than implied:

- **Catalog maintenance (D27)** — Glue Crawlers over the raw zone and the drop-box, Iceberg compaction and
  table optimizers, column statistics. This is genuinely compute, and a crawler samples object contents to
  infer schema, so it does read data. It runs only under the lake's maintenance role, which is not
  assumable interactively; it is event-driven rather than scheduled, and it is alarmed.
- **The DataZone control plane (`datazone:*`)** — not compute at all, in the same sense that Lake Formation
  is not compute: a governance control plane that grants and records, and which already lived here.

**Why the domain is here rather than in Development.** The domain is on the ownership axis, not the
lifecycle axis: it outlives every project registered in it, and an account that may one day be rebuilt
should not be carrying the catalog. There is also a mechanical gain — DataZone fulfils an approved
subscription by writing a **Lake Formation grant**, so co-locating the business catalog with the technical
catalog makes every approval a local operation instead of a cross-account one.

**Who signs in: nobody.** No interactive console access for any human, including the data scientist. The
portal *hosted* here is used by everyone, which is the D14 refinement again — using a service is not
administering the account.

**One accepted consequence.** This account has no VPC in the first build, so an AWS CodeConnections host
cannot reach the self-hosted GitLab in Production's private subnet from here. Unified Studio projects
therefore keep their default repository, and the push into GitLab is manual (`GENERAL_PLAN.md` §4.4
row 13). That was chosen over giving this account a VPC and a peering, which would cost the property that
makes it simple: nothing standing, nothing metered, nothing to reach.

## Log Archive Account

- Log Archive account linked to Control Tower.

## Audit Account

- Audit account linked to Control Tower.

## Identity Account

- Manage identity store, users, groups and permissions.

# SSO Users

## Infrastructure user

- roles: can assume infrastructure change roles

## Data Scientist user

- roles: regular user with read-only access to production environment data, and read-write access to sandbox and development environment. Can't perform infrastructure changes, unless it is managed by some AWS Service (SageMaker).

- **The primary working surface is the SageMaker Unified Studio portal** (D26), reached through the VPN like
  every other endpoint. Signing in to the portal is not signing in to the Data Governance account that
  hosts it: the person's projects run in Sandbox and Development, and the access matrix below is unchanged
  by the portal's existence. In the portal this user is a **project member**, never a domain owner.

- the access matrix this expands into, per account (`GENERAL_PLAN.md` D18):

  - **Sandbox and Development**: read-write and interactive. This is where the person works.
  - **Staging**: read-only, with no write of any kind. Staging is written by the pipeline and read by a
    human diagnosing why the pipeline failed.
  - **Production**: the data plane without compute — logs, catalog metadata, job status, named S3
    prefixes and Athena on a dedicated workgroup. No control plane, no ability to start compute.
  - **Data Governance**: no sign-in at all. The lake is read from Sandbox and Development through the
    Lake Formation cross-account share. The only write toward the lake is `s3:PutObject` into the
    ingestion drop-box, granted by bucket policy rather than by a sign-in.
  - **Identity, Audit, Log Archive**: no access.

## The two Manager users

There used to be one `Manager user` — "approves deployment of artifacts". SageMaker Catalog (D26)
introduced a second kind of approval, and on 2026-08-08 the persona was **split in two rather than
extended**, because the two approvals sit on the two different axes described at the top of this file:

| | Deployment Manager | Governance Manager |
|---|---|---|
| Axis | **Lifecycle** | **Ownership** |
| Approves | promotion of an artifact along Development → Staging → Production | data subscriptions and every other access to data |
| Acts in | GitLab (the pipeline's manual gate) | the SageMaker Unified Studio portal |
| Question being answered | *is this build safe to release?* | *may this person read this dataset?* |
| Group | `deployment-managers` | `governance-managers` |
| Where they have access | `ReadOnlyAccess` on Sandbox, Development, Staging and Production — **nothing on Data Governance** | `GovernanceManagerAccess` on **Data Governance only** |

**The access row is mirrored on purpose:** the one account the deployment manager may not enter is the
only one the governance manager may. Neither persona is a superset of the other, and neither is a weaker
copy of the data scientist — they are two different jobs that happen to share the word "approve".

**Why this is a control and not just tidier naming.** With one persona, a single human could write a job
that reads `restricted` data, approve its promotion to Production, **and** approve that job's access to the
dataset — three acts, one signature. Split, the promotion gate and the data grant require two different
people, and neither can complete the path alone. That is the separation of duties this environment
otherwise only claims to have, and it costs one extra SSO user.

**One rule that nothing in AWS will enforce for you:** never put the same person in both groups. While
there is a single operator the temptation is obvious and the split becomes notation the moment it is
given in to — Identity Center will not warn, and no policy can detect it.

### Deployment Manager user

- roles: when infrastructure changes are deployed through CD tool, this user will be used for approving
  deployment of artifacts.

- Exercises the manual approval step in the promotion pipeline, with the Staging test results and the
  Terraform plan in front of them (`GENERAL_PLAN.md` Stage 8). Also the approver for the **time-boxed
  elevated role** used to debug a failed production job (Stage 9) — that is a lifecycle act, not a data
  one.

- **Access:** the `ReadOnlyAccess` permission set on Sandbox, Development, Staging and Production — the
  four lifecycle accounts, which is the axis this persona works on — and **no assignment of any kind on
  Data Governance**. Deliberately **no** authority
  over data grants either: this user cannot approve a subscription, is not a domain owner in the Unified
  Studio domain, and cannot call `lakeformation:GrantPermissions`.

### Governance Manager user

- roles: approves data subscriptions and every other access to data.

- **Domain owner / data steward** of the SageMaker Unified Studio domain. Approving a subscription is what
  causes DataZone to write the underlying **Lake Formation grant**, so this user's decisions are what the
  fine-grained access model in D13 actually resolves to. Also owns the data classification scheme and the
  LF-Tag assignments (`GENERAL_PLAN.md` Stage 5) — the taxonomy and the grants belong to the same person,
  or the taxonomy becomes decoration.

- **Access:** the `GovernanceManagerAccess` permission set on **Data Governance and nowhere else** — which
  is enough, because since D22 that is the account the governed catalog lives in. It grants Glue catalog
  metadata read, Lake Formation LF-Tag and permission administration, DataZone domain ownership and Macie
  findings read. Deliberately **no** authority over releases: this user cannot approve a promotion, holds
  nothing in the four lifecycle accounts, and has no role in the pipeline.

- **One thing this user should not have, and it is easy to grant by accident:** blanket read access to the
  data itself. An approver who can already read everything is not exercising a control when they approve a
  subscription. They see the catalog — names, schemas, classifications, lineage — not the rows.
