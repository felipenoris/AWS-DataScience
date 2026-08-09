
# AWS Accounts

The accounts below, grouped into organizational units. The account is the isolation boundary; the OU is the
policy boundary, so each OU is named for the policy set it carries rather than for its contents
([D23](plan/decisions/D23-ou-structure.md)) — with one exception, added by D29, whose OU carries no policy set at all because it is where
*candidate* policies are tried out.

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
  (Log Archive), the security findings plane (Audit), the access-management plane (Identity) and the
  disposable target the policy plane is tested against (Policy Canary, D29).

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
| Policy Canary | Policy Test | Platform | **None of its own** — the OU exists to hold *candidate* policies under test (D29) |
| Sandbox | Interactive | Lifecycle (before the chain) | Interactive compute allowed; human infrastructure changes denied. **One account per business unit (D35)** — the only non-structural row in this table |
| Development | Interactive | Lifecycle (head of the chain) | Same as Sandbox — the two differ in content, not in policy |
| Data Governance | Data | **Ownership** | No user compute; catalog maintenance excepted by name; deletion denied |
| Staging | Workloads | Lifecycle | No interactive compute; no human control plane |
| Production | Workloads | Lifecycle (end of the chain) | Same as Staging |

## Management Account

- represents the root account. Never touch it. This will be used only to bootstrap the AWS environment manually. All further actions will be performed using auxiliary accounts.

## Sandbox Account

- Represents an experimentation sandbox environment, where the unit of work is a notebook. Sandbox users will use this to experiment and develop artifacts.

- **There is one of these per business unit** ([D35](plan/decisions/D35-sandbox-cardinality.md)) — it is the
  only account in this file that is not structural. Every other account here, `Development` included, is
  exactly one, forever. The chain reads **N Sandboxes → one Development → one Staging → one Production**, so
  the cardinality boundary is the same line as the D21 graduation boundary: experimentation is naturally
  per-unit, engineering is institutional. **N is 1 today.** Two consequences worth stating here rather than
  discovering later: a unit's experimentation is private to it (its own account, its own filesystem, its own
  people), and **that isolation stops at the graduation boundary** — past it, one shared Development, and
  whatever separation is required is carried by Lake Formation grants and per-pipeline execution roles, not
  by an account boundary that is deliberately not there. Vending a unit's account is
  [Stage 14](plan/stages/stage-14-sandbox-vending.md).

- **Target of the `experimentation` project profile** ([D26](plan/decisions/D26-unified-studio.md)). The SageMaker Unified Studio
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
therefore keep their default repository, and the push into GitLab is manual
([INT-13](plan/integrations.md)). That was chosen over giving this account a VPC and a peering, which would cost the property that
makes it simple: nothing standing, nothing metered, nothing to reach.

## Policy Canary Account

Added by [D29](plan/decisions/D29-policy-canary.md) on 2026-08-08, alone in the `Policy Test` OU.

**What it is for:** a Service Control Policy is a permission *ceiling*, evaluated only when a principal
makes a call. So a candidate SCP or RCP is attached to the `Policy Test` OU and exercised from this account
before it goes anywhere real — which is what makes the procedure in Stage 1b step 7 a test rather than a
gesture. An empty OU would not do: with no account inside it, there is no principal, and attaching a policy
there proves only that the JSON parsed.

**What it holds: nothing.** No VPC, no data, no Terraform slice, no state bucket. It is not one of the six
Terraform-managed accounts. The one thing it does hold is the point of it — **an administrator principal**
(`AdministratorAccess` for the infrastructure user), because a deny exercised by a principal that lacked the
permission anyway proves nothing about a ceiling.

**Who signs in:** the infrastructure user, to run the test battery, through the deliberately
differently-named `awsds-policy-canary` profile. Nobody else — an account whose whole purpose is to have
deliberately broken permissions is not a place for a second persona to draw conclusions.

**The name.** The industry term for the OU is *Policy Staging*, and this project does not use it: there is
already a `Staging` **account**, and the plan warns three separate times that the two collide in name and
not in concept. `Policy Test` and `Policy Canary` keep the word `Staging` naming exactly one thing.

## Log Archive Account

- Log Archive account linked to Control Tower.

## Audit Account

- Audit account linked to Control Tower.

## Identity Account

- Manage identity store, users, groups and permissions.

# SSO Users

The five users below are the **personas** the separation of duties is built from. They are not the whole
contents of the directory — see "Identities this project did not create" at the end of this section.

## Infrastructure user

- roles: can assume infrastructure change roles

## Data Scientist user

- roles: regular user with read-only access to production environment data, and read-write access to sandbox and development environment. Can't perform infrastructure changes, unless it is managed by some AWS Service (SageMaker).

- **The primary working surface is the SageMaker Unified Studio portal** (D26), reached through the VPN like
  every other endpoint. Signing in to the portal is not signing in to the Data Governance account that
  hosts it: the person's projects run in Sandbox and Development, and the access matrix below is unchanged
  by the portal's existence. In the portal this user is a **project member**, never a domain owner.

- the access matrix this expands into, per account ([D18](plan/decisions/D18-data-scientist-access.md)):

  - **Sandbox and Development**: read-write and interactive. This is where the person works. **The group
    behind the two halves is not the same one (D35):** `Development` is a single shared engineering account
    and keeps one `data-scientists` group, while a `Sandbox` exists per business unit, so its assignment is
    to a **`data-scientists-<bu>`** group covering that unit's Sandbox and nothing else — otherwise every
    data scientist can sign in to every unit's experimentation account. The permission set itself
    (`DataScientistAccess`) is unchanged and shared. With one unit there is no per-unit group yet; what
    exists now is the naming, so the second unit is an addition and not a refactor.
  - **Staging**: read-only, with no write of any kind. Staging is written by the pipeline and read by a
    human diagnosing why the pipeline failed.
  - **Production**: the data plane without compute — logs, catalog metadata, job status, named S3
    prefixes and Athena on a dedicated workgroup. No control plane, no ability to start compute.
  - **Data Governance**: no sign-in at all. The lake is read from Sandbox and Development through the
    Lake Formation cross-account share. The only write toward the lake is `s3:PutObject` into the
    ingestion drop-box, granted by bucket policy rather than by a sign-in.
  - **Identity, Audit, Log Archive**: no access.

## The approver users

There used to be one `Manager user` — "approves deployment of artifacts". It has been split twice, each
time because a genuinely different question needed a different signature, and each time along one of the
axes described at the top of this file. **Every split is a separation of duties, not a reorganisation of
labels.**

| | Deployment Manager | Governance Manager | Dev Env Steward |
|---|---|---|---|
| Axis | **Lifecycle** | **Ownership** | **Supply chain** |
| Approves | promotion of an artifact along Development → Staging → Production | data subscriptions and every other access to data | the `dev-env` container image that every notebook runs on |
| Acts in | GitLab (the promotion pipeline's manual gate) | the SageMaker Unified Studio portal | GitLab (the dev-env pipeline's manual gate) |
| Question being answered | *is this build safe to release?* | *may this person read this dataset?* | *is this runtime safe to hand to everyone?* |
| Group | `deployment-managers` | `governance-managers` | `dev-env-stewards` |
| Where they have access | `DeploymentManagerAccess` on Sandbox, Development, Staging and Production — **nothing on Data Governance** | `GovernanceManagerAccess` on **Data Governance only** | `DevEnvStewardAccess` on Production (the registry) and read-only on Sandbox and Development (where the image is registered) — **nothing on Staging, Data Governance or Identity** |
| What they may *read* | Logs, job and pipeline status, catalog metadata, image scan findings, enumerated build-artifact prefixes. **Not** query results, not the derived zones, not decrypted data (D31) | The catalog — names, schemas, classifications, lineage. **Not** the rows | The image: its `Dockerfile` history in GitLab, the build log, ECR image metadata and **enhanced-scanning findings**, and the SageMaker image / app-image-config resources. **No data at all** — no lake prefixes, no Athena, no `kms:Decrypt` |

**Neither of the first two is a superset of the other, and the third is on a different axis from both.**
The one account the deployment manager may not enter is the only one the governance manager may; the
steward enters neither of those and looks only at artifacts.

**Why the third persona exists, and it is the same argument as D14 one level up.** Whoever controls the
`dev-env` image controls what code runs in every notebook, against whatever that notebook can reach. A
malicious or careless layer in that image is a credential exfiltrator installed on every workstation at
once — and it arrives *before* any of the other gates, because the data scientist is running it while they
write the code the deployment manager will later approve. D14 puts the supply chain (GitLab, runners, ECR,
CodeArtifact) in Production precisely so the people the gate gates cannot modify it; this persona is who
signs off on the one supply-chain artifact the data scientist is *supposed* to be able to propose changes
to.

**Why this is a control and not just tidier naming.** With one persona, a single human could write a job
that reads `restricted` data, approve its promotion to Production, approve that job's access to the
dataset, **and** approve the runtime image the job was written on — four acts, one signature. Split, no
one of them can complete the path alone. That is the separation of duties this environment otherwise only
claims to have, and it costs one extra SSO user per split.

**The steward must not be able to bypass their own gate**, which is the part that is easy to get wrong:
if they can `ecr:PutImage` or create a SageMaker image version by hand, the approval is theatre. Those
actions are denied explicitly in their permission set — the pipeline holds them, and the pipeline runs
only after the gate.

**One rule that nothing in AWS will enforce for you:** never put the same person in more than one of these
groups, and never in one of them plus `data-scientists`. While there is a single operator the temptation is
obvious and every split becomes notation the moment it is given in to — Identity Center will not warn, and
no policy can detect it.

### Deployment Manager user

- roles: when infrastructure changes are deployed through CD tool, this user will be used for approving
  deployment of artifacts.

- Exercises the manual approval step in the promotion pipeline, with the Staging test results and the
  Terraform plan in front of them ([Stage 8](plan/stages/stage-08-cicd-pipelines.md)). Also the approver for the **time-boxed
  elevated role** used to debug a failed production job (Stage 9) — that is a lifecycle act, not a data
  one.

- **Access:** the `DeploymentManagerAccess` permission set on Sandbox, Development, Staging and Production —
  the lifecycle accounts, which is the axis this persona works on — and **no assignment of any kind on
  Data Governance**. Deliberately **no** authority
  over data grants either: this user cannot approve a subscription, is not a domain owner in the Unified
  Studio domain, and cannot call `lakeformation:GrantPermissions`.

- **What that set is, and why it is not `ReadOnlyAccess` ([D31](plan/decisions/D31-approver-read.md), 2026-08-08).** It used to
  be. The rule stated below for the governance manager — *an approver who can already read everything is not
  exercising a control* — is symmetric, and the plan was applying it to one of the two approvers: the
  AWS-managed `ReadOnlyAccess` includes `s3:Get*` and `athena:GetQueryResults`, so across those accounts this
  persona could read the D19 derived zones and other people's query output. The derived zones are where the
  result of a query over `restricted` data lands and, by D19's own classification rule, *is* `restricted`.

  What the persona actually needs is **diagnosis**, not reading: why did the promotion fail, is this build
  safe to release. So the set grants CloudWatch Logs read including Logs Insights, SageMaker job / pipeline
  / Model Registry status, Glue catalog metadata, ECR image metadata and scan findings, orchestration
  execution status, and `s3:GetObject` on enumerated build-artifact and test-report prefixes. It denies
  explicitly: `athena:*`, `kms:Decrypt`, secrets and parameters, the Terraform state buckets, and the
  control plane.

  **The approval itself loses nothing**, because it never consumed an AWS permission — it happens in
  GitLab, driven by group membership.

  **And the backstop is not in this set at all**, which is the part worth remembering: the derived zone has
  its own KMS key whose policy names who may decrypt (D19 as revised by D31). A permission set is a list
  someone has to maintain; the key policy is default-deny and covers prefixes nobody thought to enumerate.

### Governance Manager user

- roles: approves data subscriptions and every other access to data.

- **Domain owner / data steward** of the SageMaker Unified Studio domain. Approving a subscription is what
  causes DataZone to write the underlying **Lake Formation grant**, so this user's decisions are what the
  fine-grained access model in D13 actually resolves to. Also owns the data classification scheme and the
  LF-Tag assignments ([Stage 5](plan/stages/stage-05-data-foundation.md)) — the taxonomy and the grants belong to the same person,
  or the taxonomy becomes decoration.

- **Access:** the `GovernanceManagerAccess` permission set on **Data Governance and nowhere else** — which
  is enough, because since D22 that is the account the governed catalog lives in. It grants Glue catalog
  metadata read, Lake Formation LF-Tag and permission administration, DataZone domain ownership and Macie
  findings read. Deliberately **no** authority over releases: this user cannot approve a promotion, holds
  nothing in the four lifecycle accounts, and has no role in the pipeline.

- **One thing this user should not have, and it is easy to grant by accident:** blanket read access to the
  data itself. An approver who can already read everything is not exercising a control when they approve a
  subscription. They see the catalog — names, schemas, classifications, lineage — not the rows.

### Dev Env Steward user

- roles: approves the `dev-env` container image — the runtime every notebook and every Unified Studio
  project app runs on.

- **The mechanism, which is deliberately the same shape as the application promotion** (Stage 8): the
  image's build code — a `Dockerfile` and its pinned package manifests — lives in a **GitLab repository the
  data scientist can write to**. A change is a merge request. The pipeline builds the image, smoke-tests
  it, scans it, and pushes it to ECR under an immutable tag. **Nothing reaches a working environment
  until this user approves the manual gate**; the approval is what causes the pipeline to register the
  image so it appears in the SageMaker image selector for the Sandbox and Development projects.

- **The parallel worth holding onto:** a `dev-env` image version is to the workbench what a **Model
  Registry version is to a model** (D17) — it is *approved*, not copied. The build is cheap and anyone may
  propose one; what is gated is which built version becomes the one everybody gets.

- **Why the data scientist writes to that repository and the plan is comfortable with it.** This is the one
  supply-chain artifact whose content is genuinely their expertise: which version of Julia, which CRAN
  snapshot, which Rust toolchain. Denying them write access would push the request into a ticket and make
  the environment stale, which is how people end up installing things by hand into a notebook and
  discovering at promotion time that Production has different versions. The control is not "who may
  propose" — it is "who may release", which is this persona.

- **Access:** the `DevEnvStewardAccess` permission set on **Production** (ECR image metadata and enhanced
  scanning findings, the build pipeline's CloudWatch logs) and **read-only on Sandbox and Development**
  (the SageMaker image and app-image-config resources, to confirm what is actually registered). **Nothing
  on Staging, Data Governance, Identity, Audit, Log Archive or Policy Canary.**

- **What is denied explicitly rather than by omission, because these are what would make the gate
  theatre:** `ecr:PutImage`, `ecr:BatchDeleteImage`, `sagemaker:CreateImage*` and
  `sagemaker:UpdateAppImageConfig` — the pipeline holds those, and the pipeline runs only after the
  approval. Also `athena:*`, `kms:Decrypt`, and any `s3:GetObject` on lake or derived prefixes: this
  persona approves a *runtime*, and never needs to read data to do it.

- **The failure this persona is really guarding against** is not a bad package version, which shows up as a
  broken build. It is a layer that quietly adds a credential-harvesting entrypoint or an outbound beacon to
  an image that then runs in every notebook, holding the SageMaker execution role, inside the VPC. That is
  why the gate is a human reading a diff, and why ECR enhanced scanning blocking on critical findings
  (Stage 8) is a companion to it rather than a substitute.

## Identities this project did not create

Enabling Control Tower (Stage 1a step 3) builds an IAM Identity Center directory **and populates it** — with
groups, permission sets and a first administrator. None of it was requested by this plan, and none of it is
a persona. It is listed here for one reason: **an administrator that appears in no document is
indistinguishable from one that should not be there**, and that is a judgement a security review has to make
quickly. One of them has since been given a job by this project — Control Tower administration (D34) — which
makes it a *standing identity with one duty*, still not a persona, and makes documenting it more necessary
rather than less.

### `AWS Control Tower Admin` (D33)

An Identity Center user created by the landing zone, carrying the **Management account's root e-mail
address** — the address AWS has at landing-zone time, so it is expected rather than a misconfiguration. Its
entire footprint comes from **two group memberships, with no direct assignment**:

| Group | Management | Log Archive | Audit | Member accounts |
|---|---|---|---|---|
| `AWSControlTowerAdmins` | `AWSAdministratorAccess` | `AWSAdministratorAccess` | `AWSAdministratorAccess` | `AWSOrganizationsFullAccess` |
| `AWSAccountFactory` | `AWSServiceCatalogEndUserAccess` | — | — | — |

**Read the second and third columns before the first.** This is not merely an administrator of the
Management account: it administers **Log Archive**, which holds the organization CloudTrail bucket, and
**Audit**, which holds the security findings plane. It can delete the record of its own use — including the
trail the break-glass alarm reads. The `AWSOrganizationsFullAccess` on member accounts is close to inert,
Organizations being a management-account API, except for `organizations:LeaveOrganization`, which a member
account *can* call and which drops all governance for that account at once (denied at the organization root,
Stage 1b step 7).

- **What it is for:** the only identity that can vend accounts, because **root cannot use Account Factory at
  all** — a documented restriction, not a permission to be granted. **Since D34 that is a standing job, not a
  bootstrap one:** it owns Control Tower administration — creating OUs, vending accounts, enrolling them,
  landing-zone updates — from the console, never from Terraform.
- **What it is not:** a sixth persona. It holds one duty and no other: it approves nothing, owns no data or
  workload, and appears in no separation of duties. Do not add it to `infrastructure`, `data-scientists` or
  any approver group, and do not give it a permission set of this project's.
- **Why not the narrow replacement.** `AWSAccountFactory` alone (`AWSServiceCatalogEndUserAccess`) is enough
  to vend into an OU that already exists, through the Service Catalog console — but not to reach the
  **Control Tower console**, where OUs are created and accounts enrolled, which AWS documents as reachable
  only by `AWSControlTowerAdmins`. Creating OUs is part of the job. The choice keeps the **infrastructure
  user out of the Management account**, which is what D32's one-administrator-one-MFA-device shape depends on.
- **What limits it, permanently.** The reach above cannot be trimmed: `AWSControlTowerAdmins` is atomic, and
  the Management administrator arrives in the same membership as the Log Archive one. So the control set is
  three things, none of which is optional and all of which are now permanent rather than covering a window:
  **MFA on the user**; **S3 Object Lock in *compliance* mode** on the Log Archive bucket (Stage 1b step 9),
  because this principal holds `s3:BypassGovernanceRetention` and walks through governance mode; and the
  **alarm on membership changes to its groups** (Stage 1b step 8), which is what distinguishes the expected
  member from a second one somebody added.
- **Deliberately not renamed and not deleted.** Repointing it at a non-root address treats the symptom and
  risks a landing-zone update re-creating it under the root address, leaving the renamed one behind as a
  dormant administrator — D33 has the full argument, and a permanent identity makes it stronger.
- **The inbox collision is therefore permanent:** the break-glass alarm's SNS subscription (Stage 1a step 5)
  must not be that address, or one inbox holds the root credential, its own warning, and a routine login.
  Since every address here is a `+alias` on one mailbox, the **SMS endpoint** is the part of that separation
  that is actually real.

### The groups and permission sets that arrived with it

Control Tower also created its own permission sets — including one named **`AWSAdministratorAccess`**, four
characters from the `AdministratorAccess` Stage 1b creates — and a set of groups that are **currently
empty and pre-wired**: `AWSServiceCatalogAdmins`, `AWSSecurityAuditors`, `AWSSecurityAuditPowerUsers`,
`AWSLogArchiveAdmins`, `AWSLogArchiveViewers`, `AWSAuditAccountAdmins`, `AWSAuditAccountViewers`.

**One of them is no longer empty:** `AWSControlTowerAdmins` permanently holds the vending owner above (D34),
which is why the alarm on membership changes to these groups is what tells an expected member from an added
one. The rest are empty.

**Empty is the important word, and it is not the same as harmless.** Each already carries its assignments,
so adding one person to one of them is an organization-wide grant made by a single membership edit —
`AWSSecurityAuditPowerUsers`, for instance, holds `AWSPowerUserAccess` on **every** account including the
member accounts. None of this project's five personas belongs in any of them: Stage 1b builds its own groups
beside these, and the two sets stay separate.
