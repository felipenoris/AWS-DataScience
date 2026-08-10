
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

**This table is the account map**, and the sections after it are one per account. `Purpose` says what the
account is *for*; `Policy set` says what the OU it sits in *constrains* — the two are deliberately different
questions, which is why an account can be high blast radius and carry a light policy set at the same time.

| Account | OU | Axis | Purpose | Policy set the OU carries |
|---|---|---|---|---|
| Management | root | Platform | **Organization owner** — the Organization itself, Control Tower, and the landing zone | Bootstrap only, manual, never managed by Terraform |
| Log Archive | Security | Platform | Central, **tamper-evident** log store (S3 Object Lock). Created by Control Tower, not vended by Account Factory | Control Tower guardrails |
| Audit | Security | Platform | **Security guardian** — GuardDuty, Security Hub, Macie and IAM Access Analyzer. Created by Control Tower, not vended by Account Factory | Control Tower guardrails; delegated security administration |
| Identity | **Identity** | Platform | The **access-management plane**: permission sets, groups and assignments. Separate from Audit so that access management and security monitoring do not share a blast radius | Delegated Identity Center administration. Its own OU since 2026-08-09: Control Tower would not vend the account into the foundational `Security` OU (D23) |
| Policy Canary | Policy Test | Platform | **Deliberately empty, and disposable** — the account a candidate SCP or RCP is exercised against before it reaches anything real. An SCP is evaluated only when a principal makes a call, so a policy-staging OU with no account inside it tests nothing, which is why this is an account and not just a folder. Holds an administrator principal and nothing else, because a deny exercised by a principal that lacked the permission anyway proves nothing about a ceiling | **None of its own** — the OU exists to hold *candidate* policies under test (D29) |
| Sandbox | Interactive → **Sandboxes** | Lifecycle (before the chain) | **Experimentation** — the unit of work is a notebook. Target of the unified domain's `experimentation` project blueprints (D26): interactive compute running unreviewed code against real, shared data, which makes it **the highest-risk account rather than the lowest** (`README.md` §3). Nothing here survives; nothing promotes from here | Interactive compute allowed — because nothing denies it. Neither `Sandboxes` nor `Interactive` carries a set of its own today, so what reaches this account is the organization-root set; infrastructure change is held off the data scientist by `DataScientistAccess`, an *identity* policy (Stage 1c step 7). **One account per business unit (D35)** — the only non-structural row in this table |
| Development | Interactive | Lifecycle (head of the chain) | **Development** — the unit of work is a pipeline: a repository with tests, git and CI. Target of the `engineering` project profile (D26). Work graduates in from Sandbox **through git, never through a pipeline**, and the promotion chain starts here | Same as Sandbox — the two differ in content, not in policy |
| Data Governance | Data | **Ownership** | The **state and governance of data**: the governed lake (S3 + Iceberg), the Glue catalog, Lake Formation, classification, the ingestion drop-box, the Glue Crawlers on raw and drop-box (D27), and the **SageMaker Unified Studio domain** with its catalog, project profiles, blueprints and account associations (D26). **A registry, not a runtime** — no VPC and no interactive sign-in; every environment reaches it through cross-account shares, and the portal it hosts is used by people who can never administer the account. Renamed from `Data Management` on 2026-08-08 | No user compute; catalog maintenance excepted by name; deletion denied |
| Staging | Workloads | Lifecycle | **Deployment target** — receives the built artifact, runs the integration tests against sampled or synthetic data local to it, and is torn down again. No Studio domain, no Model Registry of its own, no GitLab, no share from the lake. Data scientists: read-only | No interactive compute; no human control plane |
| Production | Workloads | Lifecycle (end of the chain) | The **software supply chain** (GitLab, runners, ECR, CodeArtifact), the production SageMaker runtime including the **Model Registry**, and the lake's **producer** — its job execution role holds the governed write, the only path by which governed data is ever written | Same as Staging |

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
before it goes anywhere real — which is what makes the procedure in Stage 1c step 7 a test rather than a
gesture. An empty OU would not do: with no account inside it, there is no principal, and attaching a policy
there proves only that the JSON parsed.

**What it holds: nothing.** No VPC, no data, no Terraform slice, no state bucket. It is not one of the six
Terraform-managed accounts. The one thing it does hold is the point of it — **an administrator principal**,
because a deny exercised by a principal that lacked the permission anyway proves nothing about a ceiling.
That principal is the infrastructure user, through the **direct assignment of Control Tower's
`AWSAdministratorAccess`** that Account Factory made at vend time (D32) — *that* set, not the
`InfrastructureAccess` this project creates, which the `sso-group-infrastructure` group carries on the six
Terraform-managed accounts and never here. Stage 1b step 3.1 confirms it rather than creating anything, and
step 3.8 marks it as the one direct assignment that is permanent: there is no group and no `awsds-infra-*`
profile behind it, so removing it removes the only way in.

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

- **It sits in an `Identity` OU of its own, not in `Security`** (D23, revised 2026-08-09). That was not the
  design: it was to join Log Archive and Audit under `Security`, and Control Tower refused the vend —
  `Security` is a **foundational** OU in its model. Stage 1a step 4 had named this as a thing to verify and
  named this exact fallback, so the plan followed the plan. **The consequence to carry: `Security`'s policy
  set was Control Tower's guardrails, inherited by the OU being foundational, and a new OU inherits none of
  it.** Whatever `Security` carried that `Identity` does not must be attached explicitly (Stage 1c step 7) —
  the account did not become less sensitive by moving, and this is the account whose administrator can grant
  access to every other one.

# The two families of IAM role

**Every IAM role in this project answers one of two questions, and the axis separating them is *who assumes
it — a person, or an AWS service*.** The four sections after this one are almost entirely about the first
family; most of the data-protection argument is about the second. Merging them in your head is the cheapest
way to write a control that constrains nothing.

| | Human access role | Execution role |
|---|---|---|
| Example | `AWSReservedSSO_DataScientistAccess_a1b2c3` | `awsds-sagemaker-training` |
| Assumed by | **a person**, through the SSO access portal | **a service** — SageMaker, Glue, Lambda, Step Functions |
| Comes from | a **[permission set](#permission-sets)** | a plain `aws_iam_role` |
| Declared in | `terraform-live/identity/sso/` (Stage 2 step 5) | the account's own slice — `sandbox/sagemaker/`, `production/sagemaker/` |
| Trust policy | generated by Identity Center, SAML-based, **not writable** | written here, naming a service principal |
| Lives for | the sign-in session | the life of the job |
| Answers | *what may this person **ask** for?* | *what may the **code** reach?* |

**An execution role has no permission set and cannot have one**, and that is structural rather than
conventional: an Identity Center assignment's principal must be a *user or a group*, and the role a
permission set generates trusts a SAML provider that no service principal can use. The two mechanisms do not
meet. What *can* cross the seam is a **policy document** — a customer-managed `aws_iam_policy` can be
attached to an execution role and referenced by a permission set at the same time, which is exactly the
permissions-boundary mechanism of Stage 1b step 3.4. The document crosses; the role never does.

## What actually happens when a job runs

```
  person  (member of sso-group-data-scientists)
     │
     │  SSO access portal → sso:GetRoleCredentials
     ▼
  AWSReservedSSO_DataScientistAccess_a1b2c3          ← family 1: human access
     │
     │  sagemaker:CreateTrainingJob
     │      RoleArn = arn:aws:iam::<acct>:role/awsds-sagemaker-training
     │      └──────────── this is iam:PassRole ───────────┐
     ▼                                                    │
  SageMaker, the service  ◄────────────────────────────────┘
     │  sts:AssumeRole
     ▼
  awsds-sagemaker-training                           ← family 2: execution
     │
     └─►  reads S3, resolves Glue tables, decrypts with KMS,
          and is what actually leaves the VPC
```

**The last hop is the whole point: the notebook's code does not run as the person's role.** The human role
is what *asked* for the job to exist; once SageMaker has assumed the execution role, it is out of the
picture. Every object read, every table resolved, every `kms:Decrypt` and every outbound packet is
authorised against the **execution role**.

## Why this is the seam the data-protection argument sits on

Three consequences, and each is a place this plan would be wrong if the two were treated as one:

- **Narrowing a permission set does not narrow what the code can read.** `DataScientistAccess` governs what
  the person may *click*; the execution role governs what the notebook may *reach*.
  [D13](plan/decisions/D13-lake-formation-enforcement.md)'s entire force is one sentence — *the roles running
  notebooks hold no S3 access to Lake Formation-registered prefixes* — and it is a claim about the second
  family. The same sentence said about a permission set would be notation.
- **`iam:PassRole` is the bridge, and therefore the escalation path.** Unqualified `PassRole` plus a
  job-creating API lets a person run arbitrary code under **any** role they can name. It is always scoped by
  `iam:PassedToService` **and** by resource ARN (`plan/conventions.md`) — never granted bare.
- **Whoever authors the execution role owns the control** (Lesson 11). Until D26 this project wrote those
  roles itself; the Unified Studio blueprints now provision the project environment *and its roles*, which
  is precisely what **`INT-15`** is open about. A decision that moves role authorship invalidates every
  claim that rested on the role.

## "Two" is a simplification, along the axis that matters

Other roles exist — the service-linked roles AWS creates for itself, the GitLab runner's instance role, the
cross-account roles Lake Formation uses. Each falls on one side of the same question, *is a person or a
service assuming this?*, and that question is what decides whether a given control reaches it at all.

# SSO Users

**This section is about *people*. The three that follow are about *entitlements*** —
[Permission Sets](#permission-sets), [SSO Groups](#sso-groups), [Assignments](#assignments). The split is
not editorial: it is the seam in `plan/conventions.md` ("The identity seam"). What is in this section stays
in the directory at any headcount; what is in the other three becomes Terraform
(`terraform-live/identity/sso/`, Stage 2 step 5).

The five users below are the **personas** the separation of duties is built from. They are not the whole
contents of the directory — see "Identities this project did not create" at the end of this section.

**Index — one persona per row, identified by the question it answers.** The question is what separates them:
two personas answering the same question are one persona with two names, and a persona whose question nobody
asks does not need to exist. The axis column is the same vocabulary the accounts use at the top of this file,
which is what makes a split survive an account being added.

| Persona | The question it answers | Axis | Where it acts |
|---|---|---|---|
| [Infrastructure](#infrastructure-user) | *does this exist?* — who builds and changes the infrastructure | **Platform** — it approves nothing, and nothing else builds | Terraform, from a workstation, against every account the project manages |
| [Data Scientist](#data-scientist-user) | *who uses the environment?* | **Consumption** | The Unified Studio portal, GitLab, the notebook |
| [Deployment Manager](#deployment-manager-user) | *is this build safe to release?* | **Lifecycle** | GitLab — the promotion pipeline's manual gate |
| [Governance Manager](#governance-manager-user) | *may this person read this dataset?* | **Ownership** | The Unified Studio portal |
| [Dev Env Steward](#dev-env-steward-user) | *is this runtime safe to hand to everyone?* | **Supply chain** | GitLab — the `dev-env` pipeline's manual gate |
| [`AWS Control Tower Admin`](#aws-control-tower-admin-d33) | *who creates OUs and vends accounts?* | **Not a persona** ([D33](plan/decisions/D33-control-tower-admin-user.md), [D34](plan/decisions/D34-account-vending.md)) — one standing duty, no approval, no data, no workload | The Control Tower console |

**A persona is not a person, and the difference decides what is in Terraform.** Five personas is a fixed
number — it is the design. The number of *humans* behind each is not: `Infrastructure`, both approvers and
the Governance Manager are one person each and stay that way, the `Dev Env Steward` is a handful in any real
deployment, and the `Data Scientist` is hundreds. Nothing in this file changes with that number, and
nothing in AWS does either **as long as the seam is respected**: a permission set and its assignment are
per *persona and account*, and only the directory — users, groups, memberships — is per person.
So entitlements are code (`terraform-live/identity/sso/`, Stage 2 step 5) and people are directory objects,
arriving over SCIM from a corporate IdP in any deployment large enough for it to matter.
`plan/conventions.md`, "The identity seam", carries the rule and the three ways to break it.

**The separation of duties runs between the Data Scientist and the three approvers; Infrastructure is not
part of it and contains it.** Those four are separated from one another by design, and no one of them can
complete a path alone. The infrastructure persona sits outside that argument entirely — see
[the limit of the separation of duties](#the-limit-of-the-separation-of-duties-which-is-this-user), which is
the paragraph to read before trusting the approver table further down.

## Infrastructure user

- roles: can assume infrastructure change roles.

**What it actually is: the builder.** It is the identity `terraform apply` runs as. Every VPC, bucket, role,
KMS key, permission set and policy in this design is authored by it and applied under its credentials,
through the `awsds-infra-*` SSO profiles over the VPN. It approves nothing, owns no dataset, runs no workload
and appears in no gate — which is exactly why it collides with none of the other personas: they answer *may
this happen?*, and this one answers *does it exist?*

**Its group and its permission set:** the `sso-group-infrastructure` group holding `InfrastructureAccess`, created in
Stage 1b step 3 — **not** Control Tower's `AWSAdministratorAccess`, which grants the same thing and is the
set behind every Account Factory direct assignment (D32). **The name is chosen against that collision, and
that is its whole point** (Stage 1b step 3.2, decided 2026-08-10): this set was to be called
`AdministratorAccess`, four characters from Control Tower's, and an assignment made against the wrong one
still works — so nothing would have reported it. It also restores the `<Persona>Access` shape the other six
sets follow, and it names the *group* rather than the permission level, which is how the exception in
`plan/conventions.md` is meant to be read: narrowly, covering one group.

**Why it is associated with the vended accounts, which was never a decision taken per account.** Account
Factory's form carries a second address, `SSOUserEmail`, which reads like a contact field and is not: AWS's
own wording is that the user *"will have administrative access to the account you're provisioning"*.
[D32](plan/decisions/D32-account-factory-sso-user.md) fixes that value as this user, identically on every
vend — one administrator, one MFA device, one credential to protect — and that is the concrete thing letting
Stage 2 run `terraform apply` without ever touching root. So the list below is not a list somebody curated:
it is **every account Account Factory has vended**. `Log Archive` and `Audit` are absent because the landing
zone created them itself rather than through Account Factory, and that absence is correct rather than
incidental.

**What exists today is not yet the model above, and the difference matters operationally.** Each vended
account carries a **direct user assignment** of Control Tower's `AWSAdministratorAccess`, made at vend time
and sitting outside the group model entirely; the `sso-group-infrastructure` group does not exist until Stage 1b. Two
consequences, both from D32: **remove none of those direct assignments until the group path is proven end to
end** — `sso-group-infrastructure` → `InfrastructureAccess` → a real `sts:GetCallerIdentity` under each profile — because
the only thing behind a lockout is the Management root ([D16](plan/decisions/D16-break-glass.md)); and
**whether they can be removed at all is a verification, not an assumption**, since a landing-zone update, an
account update or a re-enrollment may re-create them.

### Access, per account

| Account | What it holds | Why |
|---|---|---|
| Sandbox, Development, Staging, Production, Data Governance, Identity | `InfrastructureAccess`, through the `sso-group-infrastructure` group | These are the Terraform-managed slices, and this is the identity that applies them |
| Policy Canary | Control Tower's **`AWSAdministratorAccess`**, as a **direct** assignment and deliberately so — *not* `InfrastructureAccess` | Account Factory left it at vend time (D32) and it is **permanent**: the account is outside the Terraform-managed set, has no group and no `awsds-infra-*` profile, so removing it removes the only way in (Stage 1b step 3.8). It is reached through `awsds-policy-canary`. It needs an *administrator* or the [D29](plan/decisions/D29-policy-canary.md) battery measures the identity policy instead of the SCP ceiling |
| Management | **Nothing, permanently** | Principle 1 makes Management bootstrap-only and console-only; Terraform never runs against it. D33/D34 keep `AWS Control Tower Admin` standing precisely so this user needs no reach there, and [D10](plan/decisions/D10-identity-center-delegation.md) delegates Identity Center to the `Identity` account for the same reason. Stage 1b step 4 used to create an assignment here and no longer does |
| Log Archive, Audit | **Nothing** | Neither was vended by Account Factory and neither holds a Terraform slice. The audit trail has to survive its own administrators, which is an argument against adding one rather than a gap to close |

### The limit of the separation of duties, which is this user

**Read this before trusting the approver table further down.** That separation is real *among the four*: no
one of them can complete a path alone. It says nothing about this one — and in AWS terms **this user is a
strict superset of all four**, everywhere it holds administrator.

- In `Data Governance` it can call `lakeformation:GrantPermissions`, the act that *defines* the governance
  manager. The `Data` OU's policy set denies compute, `s3:DeleteBucket` and
  `lakeformation:DeregisterResource`; it does not deny granting.
- In `Production` it can `ecr:PutImage`, and in Sandbox and Development `sagemaker:CreateImageVersion` — the
  exact actions `DevEnvStewardAccess` denies so that the `dev-env` gate is not theatre.
- The derived zone's own CMK is what stops a release approver reading query output (D19 as revised by
  [D31](plan/decisions/D31-approver-read.md)). An administrator of the account holding the key rewrites the
  key policy — and, one level worse, **this user is the author of that key policy**, because it is the
  identity Terraform runs as. A policy never constrains the principal that writes it (Lesson 18).

**And the reach is not bounded by the table above.** It is administrator of `Identity`, which Stage 1b step 1
registers as the delegated administrator of IAM Identity Center — and a delegated administrator can manage
groups *assigned to* the Management account, `AWSControlTowerAdmins` among them. One membership edit and this
user is administrator of Management, Log Archive and Audit. So the claim repeated in `README.md`, D33 and D34
— *the infrastructure user gains no Management-account reach* — is exactly true of **standing assignment** and
not of reachability. It is written that way in all three; keep it written that way.

**Nothing preventive contains any of this, and that is a property of the design rather than a hole in it:**
whoever builds the control plane can rewrite the control plane. What contains it is **detective, and
enumerable — so it can be checked rather than assumed**: the alarm on Control Tower group membership
(Stage 1b step 8), S3 Object Lock in **compliance** mode on the Log Archive bucket (Stage 1d step 9), and
CloudTrail with log file validation. If one of those three is missing, this user is unobserved as well as
unbounded, and the difference between those two states is the whole control.

**Two rules follow, and AWS enforces neither:**

- **The "never the same person in two groups" rule below extends to this persona, and this is the hardest
  instance of it to keep.** A human in `sso-group-infrastructure` *plus* any approver group is not a partial overlap: it
  is the separation of duties gone in full, because the infrastructure half already contains the other half.
  With one operator this is a statement of intent — write it down anyway, so a second operator inherits a rule
  instead of a habit.
- **`InfrastructureAccess` here is the one named exception to `plan/conventions.md`'s "nothing gets
  `AdministratorAccess` or `PowerUserAccess`"** — it is the one set that attaches the first of those. Named
  rather than tacit, because the reason is structural: an
  identity that authors IAM cannot be constrained by the IAM it authors, so narrowing this set would be
  notation. The honest control is that it is **one human with one MFA device** — and the moment there is a
  second, D32's revision trigger fires.

## Data Scientist user

- roles: regular user with read-only access to production environment data, and read-write access to sandbox and development environment. Can't perform infrastructure changes, unless it is managed by some AWS Service (SageMaker). This user can commit to git repos to develop and trigger CI/CD deploy pipelines that promote artifacts along the chain Development -> Staging -> Production. Sandbox work enters that chain by graduating into a Development repository through git, never by a pipeline. This user can also commit to git repos that contains build scripts for `dev-env`.

- **The primary working surface is the SageMaker Unified Studio portal** (D26), reached through the VPN like
  every other endpoint. Signing in to the portal is not signing in to the Data Governance account that
  hosts it: the person's projects run in Sandbox and Development, and the access matrix below is unchanged
  by the portal's existence. In the portal this user is a **project member**, never a domain owner.

- the access matrix this expands into, per account ([D18](plan/decisions/D18-data-scientist-access.md)):

  - **Sandbox and Development**: read-write and interactive. This is where the person works. **The group
    behind the two halves is not the same one (D35):** `Development` is a single shared engineering account
    and keeps one `sso-group-data-scientists` group, while a `Sandbox` exists per business unit, so its assignment is
    to a **`sso-group-data-scientists-<bu>`** group covering that unit's Sandbox and nothing else — otherwise every
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
| Group | `sso-group-deployment-managers` | `sso-group-governance-managers` | `sso-group-dev-env-stewards` |
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
groups, and never in one of them plus `sso-group-data-scientists` — **or plus `sso-group-infrastructure`**, which is the
instance that matters most and the one this table hides, because `sso-group-infrastructure` is not a column here at
all: it already contains every column, and the argument is in "The limit of the separation of duties" above.
While there is a single operator the temptation is obvious and every split becomes notation the moment it is
given in to — Identity Center will not warn, and no policy can detect it.

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
Stage 1c step 7).

- **What it is for:** the only identity that can vend accounts, because **root cannot use Account Factory at
  all** — a documented restriction, not a permission to be granted. **Since D34 that is a standing job, not a
  bootstrap one:** it owns Control Tower administration — creating OUs, vending accounts, enrolling them,
  landing-zone updates — from the console, never from Terraform.
- **What it is not:** a sixth persona. It holds one duty and no other: it approves nothing, owns no data or
  workload, and appears in no separation of duties. Do not add it to `sso-group-infrastructure`, `sso-group-data-scientists` or
  any approver group, and do not give it a permission set of this project's.
- **Why not the narrow replacement.** `AWSAccountFactory` alone (`AWSServiceCatalogEndUserAccess`) is enough
  to vend into an OU that already exists, through the Service Catalog console — but not to reach the
  **Control Tower console**, where OUs are created and accounts enrolled, which AWS documents as reachable
  only by `AWSControlTowerAdmins`. Creating OUs is part of the job. The choice keeps the **infrastructure
  user out of the Management account**, which is what D32's one-administrator-one-MFA-device shape depends on.
- **What limits it, permanently.** The reach above cannot be trimmed: `AWSControlTowerAdmins` is atomic, and
  the Management administrator arrives in the same membership as the Log Archive one. So the control set is
  three things, none of which is optional and all of which are now permanent rather than covering a window:
  **MFA on the user**; **S3 Object Lock in *compliance* mode** on the Log Archive bucket (Stage 1d step 9),
  because this principal holds `s3:BypassGovernanceRetention` and walks through governance mode; and the
  **alarm on Identity Center membership and assignment changes** (Stage 1b step 8.3 — deliberately
  *unfiltered*, so it covers these groups without depending on anyone maintaining a list of which groups
  matter), which is what distinguishes the expected member from a second one somebody added.
- **Deliberately not renamed and not deleted.** Repointing it at a non-root address treats the symptom and
  risks a landing-zone update re-creating it under the root address, leaving the renamed one behind as a
  dormant administrator — D33 has the full argument, and a permanent identity makes it stronger.
- **The inbox collision is therefore permanent:** the break-glass alarm's SNS subscription (Stage 1a step 5)
  must not be that address, or one inbox holds the root credential, its own warning, and a routine login.
  Since every address here is a `+alias` on one mailbox, the **SMS endpoint** is the part of that separation
  that is actually real.

### The groups and permission sets that arrived with it

Control Tower also created its own permission sets — including one named **`AWSAdministratorAccess`**, which
is what every Account Factory direct assignment points at (D32) and what the `awsds-policy-canary` profile is
permanently bound to; Stage 1b step 3.2 named this project's set `InfrastructureAccess` to keep the two
distinguishable at a glance — and a set of groups that are **currently
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

# Permission Sets

**Seven sets, and the number is fixed by the design rather than by headcount.** That is what makes them
Terraform: unlike a user or a membership, no amount of hiring adds one.

| Permission set | Group behind it | What it is for, in one line | How it comes into existence | Design of record |
|---|---|---|---|---|
| `InfrastructureAccess` | `sso-group-infrastructure` | The builder — the identity `terraform apply` runs as. The **one named exception** to "nothing gets `AdministratorAccess`" | **By hand**, Stage 1b step 3 — then **imported** at Stage 2 step 5 | 3.1 |
| `DataScientistAccess` | `sso-group-data-scientists` | Studio use, scratch/derived read-write, Athena, ECR pull. **Not** `PowerUserAccess`, **not** `AmazonSageMakerFullAccess` | **Written** in Terraform, Stage 2 step 5 — never typed into a console | 3.4 |
| `DataScientistStagingAccess` | `sso-group-data-scientists` | Read-only on Staging, no write of any kind, not even a drop-box | **Written**, Stage 2 step 5 | 3.6 |
| `DataScientistProdAccess` | `sso-group-data-scientists` | Production data plane read: no compute, no control plane | **Written**, Stage 2 step 5 | 3.6 |
| `DeploymentManagerAccess` | `sso-group-deployment-managers` | **Diagnosis, not reading** — why a promotion failed. Nothing on Data Governance | **Written**, Stage 2 step 5 | 3.5 |
| `GovernanceManagerAccess` | `sso-group-governance-managers` | The catalog, never the rows | **Written**, Stage 2 step 5 | 3.5 |
| `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | The artifact, never the data — judging the `dev-env` image | **Written**, Stage 2 step 5 | 3.5 |

*The "Design of record" column is a subsection of [Stage 1b step 3](plan/stages/stage-01b-identity-and-controls.md),
which carries each set's grants **and its explicit denies**. That file is the specification and this table is
the inventory; neither restates the other, so they cannot drift.*

## What a permission set actually is: a factory for IAM roles

**It is not an alternative to an IAM role — it produces one**, and it produces only the *human* family; the
other one is [above](#the-two-families-of-iam-role). Assigning set `P` to a principal on account `A` makes IAM
Identity Center provision a real IAM role *inside* `A`:

```
arn:aws:iam::<A>:role/aws-reserved/sso.amazonaws.com/us-west-2/AWSReservedSSO_P_<random suffix>
```

It carries the set's policies and its permissions boundary, and its trust policy trusts Identity Center —
**not the person**, who appears in it nowhere. Signing in through the access portal returns temporary STS
credentials for that role, which is how `CLAUDE.md`'s "avoid IAM Users, in favor of assuming IAM Roles
temporarily" is actually delivered: no IAM user, no long-lived access key, anywhere in this design.

Four consequences, none of them cosmetic:

- **One set assigned on N accounts is N roles**, with N different ARNs. That is Stage 1b step 3.3 seen from
  the IAM side, and it is why every grant is scoped by resource ARN and by condition, never by "this account
  will not have that resource".
- **The assumed-role ARN is the evidence, the account ID is not.** Two administrator sets exist four
  characters apart (`InfrastructureAccess` and Control Tower's `AWSAdministratorAccess`) and an assignment
  against the wrong one still works — Stage 1b steps 3.2, 5 and 5.1 all turn on reading that ARN.
- **The suffix is generated per account, so the role ARN can never be hard-coded.** A bucket policy or KMS
  key policy naming a human principal matches `AWSReservedSSO_<Set>_*` — relevant from Stage 5 onward, where
  key policies are the backstop the permission sets are not.
- **The generated role is never edited by hand and never declared as `aws_iam_role`.** Identity Center
  reconciles it back, silently.

## The rules these seven obey

- **`<Persona>Access`, and never within four characters of a Control Tower set** (`plan/conventions.md`). The
  name says the *group*, not the permission level — a set named after a level invites reuse by a second
  principal.
- **Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now".** `InfrastructureAccess` is the single
  named exception, and the argument for it is structural rather than pragmatic: an identity that authors IAM
  cannot be constrained by the IAM it authors (Lesson 18). See
  [the limit of the separation of duties](#the-limit-of-the-separation-of-duties-which-is-this-user).
- **For the three approver sets the *denies* are the point of them.** An approver who can already read
  everything is not exercising a control when they approve. Those denies are explicit, not by omission.
- **The permissions boundary cannot be finished inside `identity/sso/`** (Stage 1b step 3.4). A
  customer-managed boundary is referenced *by name* and the `aws_iam_policy` must already exist **in every
  account the set is provisioned into** — different state, different profile, one more copy per business unit
  (D35). Miss one account and provisioning fails there alone, which is the quiet version of the mistake.
  Stage 2 step 5 carries it as a decision row.
- **Control Tower's own sets are never edited or reused.** `AWSAdministratorAccess` is theirs; a landing-zone
  update may reset it, and touching it is drift.

# SSO Groups

**Five groups, one per persona.** A group is *person-shaped* — its membership grows with headcount — so
**groups live in the directory and never in Terraform**, while the assignment that binds a group to a
permission set does. That is the seam, and it is what lets a joiner or a leaver be a directory edit rather
than a merge request.

| Group | Persona | Humans behind it, realistically | Holds |
|---|---|---|---|
| `sso-group-infrastructure` | [Infrastructure](#infrastructure-user) | **one**, with one MFA device — D32's shape depends on it | `InfrastructureAccess` on six accounts |
| `sso-group-data-scientists` | [Data Scientist](#data-scientist-user) | hundreds | The three `DataScientist*Access` sets |
| `sso-group-deployment-managers` | [Deployment Manager](#deployment-manager-user) | one | `DeploymentManagerAccess` on the four lifecycle accounts |
| `sso-group-governance-managers` | [Governance Manager](#governance-manager-user) | one | `GovernanceManagerAccess` on Data Governance alone |
| `sso-group-dev-env-stewards` | [Dev Env Steward](#dev-env-steward-user) | a handful | `DevEnvStewardAccess` on three accounts |

**One group is planned and deliberately not created yet:** `sso-group-data-scientists-<bu>`, one per business
unit, covering that unit's `Sandbox` and nothing else (D35, [Stage 14](plan/stages/stage-14-sandbox-vending.md)).
`Sandbox` is one account per business unit and N is currently 1, so what exists today is the *naming* — which
makes the second unit an addition rather than a refactor. `Development` is a single shared account and keeps
one group permanently.

## The rules these five obey

- **The `sso-group-` prefix separates two sets of same-named objects, and that is what it is for.** Control
  Tower's groups on one side (never joined, never repurposed — see
  [the groups that arrived with it](#the-groups-and-permission-sets-that-arrived-with-it)); and, from Stage 7,
  **GitLab groups that mirror these personas 1:1 and deliberately do *not* carry the prefix**. A bare
  `deployment-managers` in this repository means the GitLab group; a prefixed one means the directory.
- **The name is load-bearing mechanically, not editorially.** Assignments resolve their principal by
  **display name** through `data.aws_identitystore_group` — never by GUID, so that replacing the directory
  with a corporate IdP over SCIM re-creates the groups with new IDs and changes nothing in Terraform. A name
  written one way in the plan and another in the directory is a `terraform plan` that fails, or a second
  group somebody creates to make the error go away.
- **A permission set is assigned to a group, never to a user.** One object regardless of how many people are
  in it. The one exception is Account Factory's direct assignment to the infrastructure user (D32), which is
  documented rather than copied.
- **Never the same person in two of these groups**, and never in one plus `sso-group-data-scientists` — or
  plus `sso-group-infrastructure`, which is the instance that matters most because it already contains all
  the others. Identity Center will not warn, and no policy can detect it.

# Assignments

**The triple is the unit:** `(permission set, group, account)`. This is the table Stage 2 step 5 writes out
one row at a time — **enumerated, never generated from a `for_each` over discovered accounts** (D34), because
a grant that appears because an account appeared is the failure mode that rule exists to prevent.

| # | Permission set | Group | Account | What it is for |
|---|---|---|---|---|
| 1 | `InfrastructureAccess` | `sso-group-infrastructure` | Sandbox | Applies the account's Terraform slices |
| 2 | `InfrastructureAccess` | `sso-group-infrastructure` | Development | Applies the account's Terraform slices |
| 3 | `InfrastructureAccess` | `sso-group-infrastructure` | Staging \* | Applies the account's Terraform slices |
| 4 | `InfrastructureAccess` | `sso-group-infrastructure` | Production | Applies the account's Terraform slices, the supply chain included (D14) |
| 5 | `InfrastructureAccess` | `sso-group-infrastructure` | Data Governance | Applies the lake, the catalog and the Lake Formation wiring |
| 6 | `InfrastructureAccess` | `sso-group-infrastructure` | Identity | Applies `identity/sso/` and `identity/org-policies/` — the entitlement plane applying itself |
| 7 | `DataScientistAccess` | `sso-group-data-scientists` † | Sandbox | Where experimentation happens: read-write, interactive |
| 8 | `DataScientistAccess` | `sso-group-data-scientists` | Development | The shared engineering account: read-write, interactive |
| 9 | `DataScientistStagingAccess` | `sso-group-data-scientists` | Staging \* | Reading why the pipeline failed — and nothing else, so Staging stays evidence of what the pipeline does |
| 10 | `DataScientistProdAccess` | `sso-group-data-scientists` | Production | Data plane read: logs, catalog metadata, job status, named prefixes, a dedicated Athena workgroup |
| 11 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Sandbox | Diagnosing a build before releasing it |
| 12 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Development | Diagnosing a build before releasing it |
| 13 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Staging \* | The test results the promotion gate is decided on |
| 14 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Production | Diagnosing a failed promotion after the fact |
| 15 | `GovernanceManagerAccess` | `sso-group-governance-managers` | Data Governance | LF-Tags, subscriptions, domain ownership — the catalog, never the rows |
| 16 | `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | Production | ECR image metadata, enhanced-scanning findings, the build pipeline's logs (the registry lives here, D14) |
| 17 | `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | Sandbox | Confirming which image version is actually registered |
| 18 | `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | Development | Confirming which image version is actually registered |

\* **The three `Staging` rows do not exist yet** — the account is unvended (the increase to the account cap
is requested, not granted). Stage 1b step 3 and Stage 2 step 5 both skip them, and they are picked up at the
vend. **15 assignments today, 18 at the target.**

† **Row 7 is the one that changes shape at the second business unit.** D35 makes `Sandbox` one account per
unit, so its assignment moves to `sso-group-data-scientists-<bu>` — covering that unit's Sandbox alone —
while row 8 stays on the shared group. The permission set is unchanged and shared; only the principal
differs. With one unit there is no per-unit group yet.

## What is *not* in the table above, and why each absence is deliberate

| Account | Who has nothing there | Why |
|---|---|---|
| **Management** | **every persona, permanently** | Bootstrap-only and console-only (principle 1); Terraform never runs against it. D33/D34 keep `AWS Control Tower Admin` standing precisely so no persona needs reach here. Stage 1b step 4 used to create an assignment and now deliberately does not |
| **Data Governance** | `sso-group-data-scientists`, `sso-group-deployment-managers`, `sso-group-dev-env-stewards` | The lake is read from Sandbox and Development through the Lake Formation cross-account share (D18/D22), not by signing in. A release approver has no business in the account that grants data access — and `sso-group-governance-managers` is the mirror image, holding only this one |
| **Staging** | `sso-group-dev-env-stewards` | The artifact it judges is a container image, not an environment — the narrowest of the three approver sets |
| **Policy Canary** | **every group** | Reached only by the infrastructure *user*'s direct assignment (below). An account whose whole purpose is to have broken permissions is not somewhere a second persona should sign in and draw conclusions |
| **Log Archive, Audit** | every persona | Neither was vended by Account Factory and neither holds a Terraform slice. The audit trail has to survive its own administrators — an argument against adding an assignment, not a gap to close |

## The assignments that are not group assignments (D32)

Two kinds exist beside the table, and **neither is modelled in Terraform** — Stage 2 step 5.2 leaves both
alone deliberately:

- **The Account Factory direct assignments.** Every vended account carries a *direct* assignment of Control
  Tower's `AWSAdministratorAccess` to the **infrastructure user**, created at vend time from the
  `SSOUserEmail` field. They are what bootstraps the whole identity plane — rows 1-6 above do not exist until
  Stage 1b step 3 — and **Stage 1b step 5.1 is where they are retired, or recorded as un-retirable.** Removing
  one before the group path is proven end to end is the cheapest way to lock the only administrator out of an
  account whose sole remaining recovery path is the Management root (D16).
- **`Policy Canary`'s, which is permanent and is the exception to that step.** There is no group and no
  `awsds-infra-*` profile behind it, so removing it removes the only way in. It must be an *administrator*
  or [D29](plan/decisions/D29-policy-canary.md)'s battery measures the identity policy instead of the SCP
  ceiling — an SCP is a ceiling, and a deny a restricted principal could not have exercised anyway proves
  nothing about it. It is reached through the deliberately differently-named `awsds-policy-canary` profile.

**Control Tower's own assignments are likewise never modelled** — `AWSControlTowerAdmins` and `AWSAccountFactory`
carry theirs from the landing zone, and editing them is drift. They are described in
[the groups that arrived with it](#the-groups-and-permission-sets-that-arrived-with-it).
