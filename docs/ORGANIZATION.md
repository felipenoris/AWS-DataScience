
# AWS Accounts

The accounts below, grouped into organizational units. The account is the isolation boundary; the OU is the
policy boundary, so each OU is named for the policy set it carries rather than for its contents
([D23](plan/decisions/D23-ou-structure.md)).

## Accounts, OUs and axes

The accounts form three groups, not one sequence, and the group decides what an account may hold:

- **Lifecycle axis** — how mature and how protected the compute in an account is. Promotion runs along
  it: **Sandbox → Staging → Production** ([Stage 6b](plan/stages/stage-06b-development-becomes-staging.md)
  removed the `Development` link with the account behind it). Sandbox sits before the chain rather than at
  its head: work graduates out of it through git into a repository, never through a pipeline into an
  account. An account on this axis holds compute, and its policy set is about what that compute may do.
- **Ownership axis** — who owns a dataset, answers for its quality and decides who may read it. The lake
  outlives every application that reads it, so tying it to an environment account would tie the data's
  life to a deployable thing's life and force a copy per environment. Data Governance is the only account
  here. It holds state and governance, not compute, and every environment reaches it through Lake
  Formation cross-account shares.
- **Platform accounts, on neither axis** — the organization's own machinery, serving every account and
  belonging to no environment: the Organization itself (Management), the tamper-evident log store
  (Log Archive), the security findings plane (Audit), the access-management plane (Identity) and the
  disposable target the policy plane is tested against (Policy Canary, D29).

An account off the lifecycle axis is not "a production account": Data Governance, Identity and Audit are
cross-cutting. Several are **high blast radius** — whoever controls Identity can grant access to any
account, whoever controls Data Governance decides who reads which dataset — and sensitive and production
are different properties; only the second is a point on the lifecycle axis.

The boundary is the control plane, not the account (the refinement D14 makes for GitLab): a human may use a
service hosted in an account they can never administer — GitLab in Production over the VPN, the SageMaker
Unified Studio portal hosted in Data Governance. Using the service is not signing in to the account.

**Cardinality cuts across all three groups** ([D35](plan/decisions/D35-sandbox-cardinality.md)). Every
account is structural — exactly one, forever — except `Sandbox`, which is one per business unit; N is 1
today. The chain reads N Sandboxes → one Staging → one Production, so the cardinality boundary is D21's
graduation boundary: experimentation multiplies, the engineering chain after it does not, and N leaves the
promotion chain untouched. That decides where vending is automated: the structural accounts keep the
console flow (D34); the Sandbox gets [Stage 14](plan/stages/stage-14-sandbox-vending.md). A stage writing
"*the* Sandbox account" is writing a singleton assumption that has to be paid for later.

In the table, `What it is` says what the account is for and `Policy set the OU carries` says what the OU
constrains: two different questions, which is how an account can be high blast radius and carry a light
policy set at once. The sections after it are one per account. The full annotated tree, the two access
paths, region portability, the data perimeter and the two egress designs are in
[`docs/plan/architecture.md`](plan/architecture.md).

| Account | OU | Axis | What it is | Policy set the OU carries |
|---|---|---|---|---|
| Management | root | Platform | **Organization owner** — the Organization itself, Control Tower and the landing zone. Bootstrap only, console only, never Terraform. Its **root user is the break-glass credential** (D16) | Bootstrap only, manual, never managed by Terraform |
| Log Archive | Security | Platform | Control Tower's log sink: the central, **tamper-evident** log store (S3 Object Lock). Created by Control Tower, not vended by Account Factory | Control Tower guardrails |
| Audit | Security | Platform | **Security guardian** — GuardDuty, Security Hub, Macie and IAM Access Analyzer. Created by Control Tower, not vended by Account Factory | Control Tower guardrails; delegated security administration |
| Identity | **Identity** | Platform | The **access-management plane**: Identity Center delegated administration (D10) — permission sets, groups and assignments — and, since 2026-08-15, the organization's **policy** documents as well (the account's section below). As sensitive as Management. Separate from Audit so that access management and security monitoring do not share a blast radius | No user compute — `DenyUserCompute`, the same statement as `Data`'s and none of its neighbours (1c step 7.6), so a compromise of the identity plane cannot be turned into compute inside it. Its own OU since 2026-08-09: Control Tower would not vend the account into the foundational `Security` OU (D23), so what that OU carries by being foundational is attached here explicitly |
| Policy Canary | Policy Test | Platform | **Deliberately empty, and disposable** — the account a candidate SCP or RCP is exercised against before it reaches anything real (D29). An SCP is evaluated only when a principal makes a call, so a policy-staging OU with no account inside it tests nothing. Holds an administrator principal and nothing else: a deny exercised by a principal that lacked the permission anyway proves nothing about a ceiling | **None of this project's** — the OU holds *candidate* policies under test (D29). It carries the Control Tower controls every governed OU has (the `us-west-2` ceiling and the two root-user controls, 1c step 7.7), so a candidate is measured against the same floor as everything else |
| Sandbox | Interactive → **Sandboxes** | Lifecycle (before the chain: its origin, not its first link) | **Experimentation** — the unit of work is a notebook, and this is the **only** account where a human runs code (D17). Target of the unified domain's `experimentation` project blueprints (D26): interactive compute running unreviewed code against real, shared data, which makes it **the highest-risk account rather than the lowest** (`README.md` §3). Nothing here survives; nothing promotes from here. **One account per business unit (D35)** — the only non-structural row — grouped in a nested OU that carries no policy set of its own (D37). The VPN terminated here until [Stage 6c](plan/stages/stage-06c-networking-hub.md) moved it to Production's `VPC-Networking` | Interactive compute allowed, because nothing denies it save one statement. `Sandboxes` carries no set of its own; `Interactive` carries exactly one deny (classic notebook instances, Stage 1c step 7.6, 2026-08-13), so what reaches this account is the organization-root set plus that. Infrastructure change is held off the data scientist by `DataScientistAccess`, an *identity* policy |
| Data Governance | Data | **Ownership** | The **state and governance of data**: the governed lake (S3 + Iceberg), the Glue catalog, Lake Formation, classification, the ingestion drop-box, the Glue Crawlers on raw and drop-box (D27), and the **SageMaker Unified Studio domain** with its catalog, project profiles, blueprints and account associations (D22, D26). **A registry, not a runtime** — no VPC, no user compute, no interactive sign-in; every environment reaches it through cross-account shares, and the portal it hosts is used by people who can never administer the account. Renamed from `Data Management` on 2026-08-08 | No user compute; catalog maintenance excepted by name; deletion denied |
| Staging | Workloads | Lifecycle | **Deployment target**, written only by the pipeline: receives the built artifact, runs the integration tests against sampled or synthetic data local to it (D20), and is torn down again. No Studio domain, no Model Registry of its own, no GitLab, no share from the lake. Data scientists: read-only. **The renamed `Development` account since [Stage 6b](plan/stages/stage-06b-development-becomes-staging.md)** (2026-09-06): the quota refused a vend, and the interactive environment it used to be was found unnecessary (D21 superseded by its own larger branch) | No interactive compute; no human control plane |
| Production | Workloads | Lifecycle (end of the chain) | Deployment target **plus** the **software supply chain** (GitLab, runners, ECR, CodeArtifact — D14), the production SageMaker runtime including the **Model Registry**, the **orchestration** layer ([D7](plan/decisions/D07-orchestration.md)), and the lake's **producer** — its job execution role holds the governed write, the only path by which governed data is ever written. **Since [Stage 6c](plan/stages/stage-06c-networking-hub.md) also the network platform**: three VPCs, the estate's only internet gateway, the proxy and the VPN endpoint (D38, a quota-forced compromise with a trigger to move it out) | Same as Staging |

### The policy set each OU carries

`Workloads`, `Data`, `Identity` and `Interactive` each carry one document of this project's
([Stage 1c step 7.6](plan/stages/stage-01c-preventive-policies.md)). `Security` carries Control Tower's own
guardrails by being foundational. Two OUs carry no policy set of their own, each for a different reason:

- **`Policy Test`** ([D29](plan/decisions/D29-policy-canary.md)) holds a *candidate* SCP or RCP while it is
  exercised, before it reaches anything real. A document of this project's found there means a battery is
  in progress or was interrupted.
- **`Sandboxes`** ([D35](plan/decisions/D35-sandbox-cardinality.md),
  [D37](plan/decisions/D37-nested-ou-inheritance.md)) is a container for a *cardinality class*, nested under
  `Interactive` and inheriting whatever that OU carries. Nothing is attached or enabled here unless it
  *differs* from `Interactive`: sameness is inherited, never copied. That inheritance is what governs a new
  business unit's account on arrival, and it was measured: `sagemaker:CreateNotebookInstance` from
  `awsds-infra-sandbox-1` is denied by `Interactive`'s document.

`Interactive` carried nothing until 2026-08-13. Interactive compute is allowed there because almost nothing
denies it — the organization-root set is very nearly the whole ceiling — and what holds infrastructure
change off the data scientist is `DataScientistAccess`, an *identity* policy. Step 7.6 added **one
statement**, no classic `sagemaker:CreateNotebookInstance`, the candidate that needs no carve-out.

### Account names in AWS

Every document here — this one, `CLAUDE.md`, `docs/plan/`, `docs/log/` — names an account by its **role in
the design**. What AWS stores in `Account.Name` is different, and the two are never assumed equal in a
command. Stage 1d step 9 lost a run to this: `list-accounts` filtered on `Name=='Log Archive'` returned
`None`, which reads like a missing account rather than a missing suffix, and the empty value was carried
into a malformed role ARN.

| Name used in this repository | `Account.Name` in AWS |
|---|---|
| Management | **`FELIPE N TAVARES`** — no suffix, no relation to the logical name |
| Log Archive, Audit, Identity, Staging, Production, Data Governance, Policy Canary | the same words plus **` Account`** — `Log Archive Account`, `Staging Account`, … `Staging Account` was `Development Account` until 2026-09-06 and kept the suffix through the rename, so `identity/sso`'s exact-name lookup kept working with one value changed |
| Sandbox | **`Sandbox Account 1`** — the per-unit ordinal (D35), so there is no single name for this row |

**Never resolve an account by name in an API call.** Derive the id from a resource the task already binds
to — step 9 took it from the trail's own bucket name, since `list-buckets` returns only buckets the calling
account owns — or read it from `aws/output/list-identities.txt`, which prints name and id together and is
regenerated by `./aws/list-identities.py`. A name is an editable field nobody guaranteed, and a suspended
`Sandbox` that is not ours exists (EXC-01), so a name match can find the wrong account as easily as none.

## Management Account

- Owns the Organization, Control Tower and the landing zone. It is **bootstrap-only and console-only**
  (principle 1): everything done here is manual and recorded by the user in that stage's file under
  `docs/log/`, and **Terraform never runs against it**. No persona holds an assignment here, permanently;
  `AWS Control Tower Admin` is kept standing (D33, D34) so that none needs one.

- Its **root user is the break-glass credential** ([D16](plan/decisions/D16-break-glass.md)) — the only
  one since D30 was reverted, which is what makes D29's policy canary load-bearing. When it may be used,
  what to do with it, and the alarm chain that watches its use:
  [`docs/plan/runbooks/break-glass.md`](plan/runbooks/break-glass.md).

## Sandbox Account

- Represents an experimentation sandbox environment, where the unit of work is a notebook. Sandbox users will use this to experiment and develop artifacts.

- **One per business unit** ([D35](plan/decisions/D35-sandbox-cardinality.md)) — the only account in this
  file that is not structural; every other one is exactly one, forever. The chain reads **N Sandboxes →
  one Staging → one Production**, so the cardinality boundary is the D21 graduation boundary:
  experimentation is per unit, everything past it is institutional. **N is 1 today.** A unit's
  experimentation is private to it (its own account, its own people), and that isolation stops at the
  graduation boundary: past it there is one shared Staging and one shared Production, and whatever
  separation is required there is carried by Lake Formation grants and per-pipeline execution roles, not
  by an account boundary. Vending a unit's account is
  [Stage 14](plan/stages/stage-14-sandbox-vending.md).

- **Target of the `experimentation` project profile** ([D26](plan/decisions/D26-unified-studio.md)). The
  SageMaker Unified Studio domain lives in Data Governance; the compute does not. When a data scientist
  creates an experimentation project, its blueprints provision the environment — the SageMaker AI apps,
  the project bucket, the execution roles — **into this account**. Arbitrary code runs here, against this
  account's data and behind this account's egress controls.

- The **WireGuard instance**, the single human entry point, terminated here
  ([D4](plan/decisions/D04-vpn-wireguard.md), Stage 4) until Stage 6c moved it to Production's
  `VPC-Networking` (D38). Its host private key is a `[P]` Secrets Manager secret fetched by the instance at
  first boot — never a file in the repository or a value in the user data (Stage 4 decision 4, third
  review); every key event follows [`docs/plan/runbooks/vpn.md`](plan/runbooks/vpn.md) Part K. The shared
  EFS that used to sit beside it left with the NFS requirement (withdrawn 2026-08-17,
  [D24](plan/decisions/D24-shared-filesystem.md)); the exchange between Sandbox and the pipeline's accounts
  is S3 and git.

- **The highest-risk account in the organization, not the lowest**: real data meets unreviewed code,
  interactively, with a browser session attached. The argument is in [§3 of `README.md`](../README.md), and
  it is why the perimeter and the egress controls are built here first.

## Staging Account

- **Deployment target, not a staging area someone works in** ([D20](plan/decisions/D20-staging-account.md)).
  It receives the artifact the pipeline builds, runs the integration tests against it, and is torn down
  again. No Studio domain, no Model Registry of its own, no GitLab. Only the pipeline writes here, which its
  `Workloads` policy set enforces: no interactive compute, no human control plane.

- **The renamed `Development` account since 2026-09-06**
  ([Stage 6b](plan/stages/stage-06b-development-becomes-staging.md)). The quota increase for a vend was
  refused, so Stage 6b converted the account rather than creating one: it moved from `Interactive` to
  `Workloads` with a new persona set (`InfrastructureAccess`, `DataScientistStagingAccess`,
  `DeploymentManagerAccess`, and no `DevEnvStewardAccess`); the VPC, its CIDR and both `[P]` gateway
  endpoints are the ones Stage 3 built. `Development` had been the `Interactive` account at the head of
  the promotion chain, target of the `engineering` project profile, where the unit of work was a pipeline;
  the profile was destroyed with it (6b step 1.1). Nothing replaced it: the 2026-09-05 re-scope found one
  interactive environment sufficient, because the thing being developed is a **pipeline definition**,
  developed in git and executed by the pipeline into Staging. Work graduates out of Sandbox through git
  into a **repository**, not into an account, and the chain is `Sandbox → Staging → Production`.

- **Its data is sampled or synthetic, local to it, and in no Lake Formation share** — a departure from the
  reference architectures: a target where data scientists have read access and unattended tests run would
  otherwise be the cheapest route to production data. The accepted cost is a test suite that catches
  permission, schema and wiring errors and misses whatever only appears at production distribution and
  volume.

- **Read-only for the data scientist, with no write of any kind** — `DataScientistStagingAccess`
  ([D18](plan/decisions/D18-data-scientist-access.md)). The moment a person can adjust Staging by hand to
  make a test pass, the test stops being evidence about the pipeline.

## Production Account

- The end of the promotion chain and, since [D14](plan/decisions/D14-supply-chain-account.md), the
  **software supply chain**: GitLab and GitLab Pages, the runners, ECR, CodeArtifact, the SageMaker Model
  Registry and runtime, the orchestration layer (D7), and the lake's **producer** path. Since Stage 6c
  also the network platform: three VPCs, the estate's only internet gateway, the proxy and the VPN
  endpoint (D38).

- **"Only Terraform touches Production" is about the control plane, not the account.** Nobody changes
  Production *infrastructure* by hand — Terraform builds it and the pipeline deploys into it — but humans
  do *use* services hosted here: GitLab over the VPN, and the production data-plane read that
  `DataScientistProdAccess` grants (D18). Using a service is not administering the account.

- **The supply chain is here and not in a shared-services account** on cost (D14). Whoever controls
  GitLab, the runners and the registries controls what runs in Production, so they must not sit in an
  account where `sso-group-data-scientists` has broad permissions. The consequence: there is no boundary
  between what builds and what runs, so a compromise of GitLab is a compromise of Production.

- **The one deployment target that reaches the lake as a writer.** Its job execution role holds the Lake
  Formation share's **governed write** — the only path by which governed data is ever written
  ([D22](plan/decisions/D22-data-governance-account.md)) — and it is the consumer of the ingestion drop-box
  ([D25](plan/decisions/D25-drop-box-consumer.md)).

## Data Governance Account

Renamed from `Data Management` on 2026-08-08, when the SageMaker Unified Studio domain was placed here
(D26): the account owns the *technical* catalog and the *business* catalog, so its name says governance
rather than storage.

**The state of data it owns:** the raw and curated S3 buckets (Iceberg), the Glue Data Catalog, Lake
Formation with the LF-Tags and the D13 registrations, the data classification scheme, and the ingestion
drop-box.

**The governance of data it owns:** the **SageMaker Unified Studio domain** (a DataZone V2 domain) and
everything the domain registers: the project inventory, the project profiles and blueprints, the account
associations, project memberships, Git connections, and **SageMaker Catalog** — the business catalog,
glossary, data products and subscription requests.

**Compute it does not own.** A domain is a registry, not a runtime. It holds no notebook, no app, no
training job and no project bucket; blueprints provision all of that into the *associated* accounts
(Sandbox only since 2026-09-06; Sandbox and Development before), decided by the project profile. Two named
exceptions:

- **Catalog maintenance (D27)** — Glue Crawlers over the raw zone and the drop-box, Iceberg compaction and
  table optimizers, column statistics. A crawler samples object contents to infer schema, so it does read
  data. It runs only under the lake's maintenance role, which is not assumable interactively; it is
  event-driven rather than scheduled, and it is alarmed.
- **The DataZone control plane (`datazone:*`)** — not compute, in the sense that Lake Formation is not
  compute: a governance control plane that grants and records.

**The domain is here because it is on the ownership axis**, not the lifecycle axis: it outlives every
project registered in it, and an account that may one day be rebuilt should not carry the catalog. DataZone
fulfils an approved subscription by writing a **Lake Formation grant**, so co-locating the business catalog
with the technical catalog makes every approval a local operation instead of a cross-account one.

**Nobody signs in.** No interactive console access for any human, the data scientist included. The portal
*hosted* here is used by everyone; using a service is not administering the account.

**One accepted consequence.** The account has no VPC in the first build, so an AWS CodeConnections host
cannot reach the self-hosted GitLab in Production's private subnet from here. Unified Studio projects keep
their default repository, and the push into GitLab is manual ([INT-13](plan/integrations.md)). A VPC and a
peering here would cost the property that keeps the account simple: nothing standing, nothing metered,
nothing to reach.

## Policy Canary Account

Added by [D29](plan/decisions/D29-policy-canary.md) on 2026-08-08, alone in the `Policy Test` OU.

**Purpose.** A Service Control Policy is a permission *ceiling*, evaluated only when a principal makes a
call, so a candidate SCP or RCP is attached to the `Policy Test` OU and exercised from this account before
it goes anywhere real — what makes the procedure in Stage 1c step 7 a test rather than a gesture. An empty
OU holds no principal, and attaching a policy there proves only that the JSON parsed.

**Contents: nothing.** No VPC, no data, no Terraform slice, no state bucket; not one of the six
Terraform-managed accounts. It holds one thing — **an administrator principal** — because a deny exercised
by a principal that lacked the permission anyway proves nothing about a ceiling. That principal is the
infrastructure user, through the **direct assignment of Control Tower's `AWSAdministratorAccess`** that
Account Factory made at vend time (D32): *that* set, not the `InfrastructureAccess` this project creates,
which `sso-group-infrastructure` carries on the six Terraform-managed accounts and never here. Stage 1b
step 3.1 confirms it rather than creating anything, and step 3.8 marks it as the one permanent direct
assignment: no group and no `awsds-infra-*` profile stands behind it, so removing it removes the only way
in.

**Who signs in:** the infrastructure user, to run the test battery, through the `awsds-policy-canary`
profile. Nobody else: an account whose purpose is to have broken permissions is not a place for a second
persona to draw conclusions.

**The name.** The industry term for the OU is *Policy Staging*; this project already has a `Staging`
**account**, and the plan warns three separate times that the two collide in name and not in concept.
`Policy Test` and `Policy Canary` keep the word `Staging` naming exactly one thing.

## Log Archive Account

- The organization's **tamper-evident log sink**, created by Control Tower itself rather than vended by
  Account Factory — so no `SSOUserEmail` direct assignment exists here (D32) and it holds no Terraform
  slice. It receives the organization CloudTrail and the Config history.

- **S3 Object Lock in *compliance* mode** ([Stage 1d step 9](plan/stages/stage-01d-org-wide-enablement.md)),
  not governance mode: `AWS Control Tower Admin` administers this account and holds
  `s3:BypassGovernanceRetention`, so governance mode would be walked through by the identity the retention
  is there to survive. Together with CloudTrail log file validation and the alarm on Identity Center
  membership changes, it is one of the three permanent controls that make the standing administrators
  *observed* rather than merely unbounded.

- **Nobody holds an assignment here**, the infrastructure user included. The audit trail has to survive its
  own administrators — an argument against adding one, not a gap to close.

## Audit Account

- The **security guardian**, created by Control Tower rather than vended: the delegated administrator for
  GuardDuty, Security Hub, Macie and IAM Access Analyzer, and where their organization-wide findings land.

- **The services arrive stage by stage**, each naming the stage that turns it on: Access Analyzer's
  external-access findings in the landing zone (Stage 1b), because they are free; Security Hub at Stage 5,
  with the first governed data; Macie at Stage 11; GuardDuty at **Stage 15** — it was Stage 4's, coupled
  to the first internet-facing resource, until the 2026-08-18 split deferred it (the trade is an
  `institutional-delta.md` row). Guiding principle 9 carries the rule: detection is metered, and turning it
  on over empty accounts buys nothing while spending the one free window in which its real cost could be
  measured. Stage 11 adds one short-lived reading here: the organization **internal-access** analyzer —
  USD 9.00 per monitored resource per month — is created, read against D13/D19 and deleted inside the same
  month, never left standing.

- **Separate from `Identity`** so that access management and security monitoring do not share a blast
  radius, and **no persona holds an assignment here**, for the same reason as Log Archive.

## Identity Account

- Manage identity store, users, groups and permissions.

- **It sits in an `Identity` OU of its own, not in `Security`** (D23, 2026-08-09). It was to join Log
  Archive and Audit under `Security`, and Control Tower refused the vend: `Security` is a **foundational**
  OU in its model. Stage 1a step 4 had named this exact fallback. The consequence: `Security`'s policy set
  is Control Tower's guardrails, inherited by the OU being foundational, and a new OU inherits none of it,
  so whatever `Security` carries that `Identity` does not is attached explicitly (Stage 1c step 7). The
  account did not become less sensitive by moving; its administrator can grant access to every other one.

- **Since 2026-08-15 it also edits the organization's policy ceiling.** Stage 2 step 5.1 attached a
  **resource-based delegation policy** on the organization naming this account as principal, so that
  `terraform-live/identity/org-policies/` owns the ten SCP / RCP / tag / declarative documents instead of
  a browser tab. The delegation reaches policies *"created by any account in the organization, including
  the management account"* — **Control Tower's own guardrail SCPs** included — and cannot be narrowed by
  policy ARN, because this project's policies have no ARN until they are created. So this account can both
  **grant access to every other account** and **change what any account is permitted to do at all**. The
  controls are unchanged and detective: the Identity Center membership alarm (1b step 8.3) and the
  CloudTrail record. The document, its three `Sid`s and the reasons it stays out of Terraform are in
  [`terraform-live/identity/org-policies/POLICIES.md`](../terraform-live/identity/org-policies/POLICIES.md).

- **That authority is exercised, not merely granted** — Stage 2 step 5.0 measured it in four readings: an
  `organizations:UpdatePolicy` on a **root-attached** document succeeded from `awsds-infra-identity`, and
  a duplicate `AttachPolicy` against an already-attached pair returned `DuplicatePolicyAttachmentException`
  for both a root target and an OU one, while the same call from a principal holding no delegation
  returned `AccessDeniedException` — the negative control that makes the first answer evidence. Only the
  delegation's `account/…/*` entry is unexercised, and it cannot be reached inertly: nothing in this design
  is attached to an account.

- **The delegation names the *account*, not a role.** Its principal is
  `arn:aws:iam::<Identity Account>:root`, so it reaches **every principal in this account that also holds
  `organizations:*` on the identity side** — not only `InfrastructureAccess`. Control Tower's
  `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins` is assigned into every vended account, this one
  included, and its one member is [`AWS Control Tower Admin`](#aws-control-tower-admin-d33). So since
  2026-08-15 that identity can edit the organization's policy ceiling **through this account**, without
  joining `sso-group-infrastructure`: the two standing administrators converge here. Measured in the shape
  the previous bullet's negative control established: from **Identity** the Organizations reads answer and
  the duplicate `AttachPolicy` on the root returns `DuplicatePolicyAttachmentException`; from
  **Development**, the same permission set and no delegation, every one of those calls returns
  `AccessDenied`. **What to do about it is open** — the remaining half of
  [`docs/plan/open-questions.md`](plan/open-questions.md) item 11, and landing-zone state, so a decision in
  D32's neighbourhood rather than a cleanup. A resource policy's principal *is* an account, so there is no
  narrower principal to write; whether a `Condition` on `aws:PrincipalArn` beside it would scope the grant
  to one role is untested, and worth testing before it is proposed as the fix — this document already lost
  `NotAction`/`NotResource` to an AWS restriction.

# The families of IAM role

Every IAM role in this project answers one of two questions, and the axis separating them is *who assumes
it — a person, or an AWS service*. The sections after this one are almost entirely about the first family;
most of the data-protection argument is about the second. A control written with the two merged constrains
nothing.

| | Human access role | Execution role |
|---|---|---|
| Example | `AWSReservedSSO_DataScientistAccess_a1b2c3` | `awsds-sagemaker-training` |
| Assumed by | **a person**, through the SSO access portal | **a service** — SageMaker, Glue, Lambda, Step Functions |
| Comes from | a **[permission set](#permission-sets)** | a plain `aws_iam_role` |
| Declared in | `terraform-live/identity/sso/` (Stage 2 step 5) | the account's own slice — `sandbox/sagemaker/`, `production/sagemaker/` |
| Trust policy | generated by Identity Center, SAML-based, **not writable** | written here, naming a service principal |
| Lives for | the sign-in session | the life of the job |
| Answers | *what may this person **ask** for?* | *what may the **code** reach?* |

**An execution role has no permission set and cannot have one**: an Identity Center assignment's principal
must be a *user or a group*, and the role a permission set generates trusts a SAML provider that no service
principal can use. What *can* cross the seam is a **policy document** — a customer-managed `aws_iam_policy`
can be attached to an execution role and referenced by a permission set at the same time, which is the
permissions-boundary mechanism of Stage 1b step 3.4. The document crosses; the role never does.

## What happens when a job runs

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

**The notebook's code does not run as the person's role.** The human role *asked* for the job to exist;
once SageMaker has assumed the execution role, it is out of the picture. Every object read, every table
resolved, every `kms:Decrypt` and every outbound packet is authorised against the **execution role**.

## Consequences for the data-protection argument

Three places this plan would be wrong if the two families were treated as one:

- **Narrowing a permission set does not narrow what the code can read.** `DataScientistAccess` governs what
  the person may *click*; the execution role governs what the notebook may *reach*.
  [D13](plan/decisions/D13-lake-formation-enforcement.md)'s force is one sentence — *the roles running
  notebooks hold no S3 access to Lake Formation-registered prefixes* — and it is a claim about the second
  family. Said about a permission set it would be notation.
- **`iam:PassRole` is the bridge, and therefore the escalation path.** Unqualified `PassRole` plus a
  job-creating API lets a person run arbitrary code under **any** role they can name. It is always scoped
  by `iam:PassedToService` **and** by resource ARN (`docs/plan/conventions.md`), never granted bare.
- **Whoever authors the execution role owns the control** (Lesson 11). Until D26 this project wrote those
  roles itself; the Unified Studio blueprints now provision the project environment *and its roles*, which
  is what **`INT-15`** is open about. A decision that moves role authorship invalidates every claim that
  rested on the role.

## Other roles

The service-linked roles AWS creates for itself, the GitLab runner's instance role and the cross-account
roles Lake Formation uses each fall on one side of the same question, *is a person or a service assuming
this?*, and that question decides whether a given control reaches the role at all.

# SSO Users

This section is about *people*; the three that follow — [Permission Sets](#permission-sets),
[SSO Groups](#sso-groups), [Assignments](#assignments) — are about *entitlements*. The split is the seam in
`docs/plan/conventions.md` ("The identity seam"): what is in this section stays in the directory at any
headcount; what is in the other three is Terraform (`terraform-live/identity/sso/`, Stage 2 step 5).

The users below are the **personas** the separation of duties is built from. They are not the whole
contents of the directory — see "Identities this project did not create" at the end of this section.

Each persona is identified by the question it answers: two personas answering the same question are one
persona with two names, and a persona whose question nobody asks does not need to exist. The axis column
uses the vocabulary of the account table, which is what makes a split survive an account being added.

| Persona | The question it answers | Axis | Where it acts |
|---|---|---|---|
| [Infrastructure](#infrastructure-user) | *does this exist?* — who builds and changes the infrastructure | **Platform** — it approves nothing, and nothing else builds | Terraform, from a workstation, against every account the project manages |
| [Data Scientist](#data-scientist-user) | *who uses the environment?* | **Consumption** | The Unified Studio portal, GitLab, the notebook |
| [Deployment Manager](#deployment-manager-user) | *is this build safe to release?* | **Lifecycle** | GitLab — the promotion pipeline's manual gate |
| [Governance Manager](#governance-manager-user) | *may this person read this dataset?* | **Ownership** | The Unified Studio portal |
| [Dev Env Steward](#dev-env-steward-user) | *is this runtime safe to hand to everyone?* | **Supply chain** | GitLab — the `dev-env` pipeline's manual gate |
| [`AWS Control Tower Admin`](#aws-control-tower-admin-d33) | *who creates OUs and vends accounts?* | **Not a persona** ([D33](plan/decisions/D33-control-tower-admin-user.md), [D34](plan/decisions/D34-account-vending.md)) — one standing duty, no approval, no data, no workload | The Control Tower console |

**A persona is not a person, and the difference decides what is in Terraform.** The number of personas is
fixed by the design; the number of *humans* behind each is not: `Infrastructure`, the `Deployment Manager`
and the `Governance Manager` are one person each, the `Dev Env Steward` is a handful in any real
deployment, and the `Data Scientist` is hundreds. Nothing in this file or in AWS changes with that number
as long as the seam is respected: a permission set and its assignment are per *persona and account*, and
only the directory — users, groups, memberships — is per person. Entitlements are code
(`terraform-live/identity/sso/`, Stage 2 step 5); people are directory objects, arriving over SCIM from a
corporate IdP in any deployment large enough for it to matter. `docs/plan/conventions.md`, "The identity
seam", carries the rule and the three ways to break it.

**The separation of duties runs between the Data Scientist and the three approvers**: no one of the four
can complete a path alone. Infrastructure is not part of it and contains it — read
[the limit of the separation of duties](#the-limit-of-the-separation-of-duties-which-is-this-user) before
trusting the approver table further down.

## Infrastructure user

- roles: can assume infrastructure change roles.

**The builder.** It is the identity `terraform apply` runs as: every VPC, bucket, role, KMS key, permission
set and policy in this design is authored by it and applied under its credentials, through the
`awsds-infra-*` SSO profiles over the VPN. It approves nothing, owns no dataset, runs no workload and
appears in no gate, so it collides with none of the other personas: they answer *may this happen?*, and
this one answers *does it exist?*

**Its group and its permission set:** `sso-group-infrastructure` holding `InfrastructureAccess`, created in
Stage 1b step 3 — **not** Control Tower's `AWSAdministratorAccess`, which grants the same thing and is the
set behind every Account Factory direct assignment (D32). The name was chosen against that collision
(Stage 1b step 3.2, 2026-08-10): the set was to be called `AdministratorAccess`, four characters from
Control Tower's, and an assignment made against the wrong one still works, so nothing would have reported
it. The name also restores the `<Persona>Access` shape the other six sets follow and names the *group*
rather than the permission level, which is how the exception in `docs/plan/conventions.md` is meant to be
read: narrowly, covering one group.

**Why it is associated with the vended accounts.** Account Factory's form carries a second address,
`SSOUserEmail`, which reads like a contact field and is not: AWS's own wording is that the user *"will
have administrative access to the account you're provisioning"*.
[D32](plan/decisions/D32-account-factory-sso-user.md) fixes that value as this user, identically on every
vend — one administrator, one MFA device, one credential to protect — which is what lets Stage 2 run
`terraform apply` without ever touching root. So the list below is **every account Account Factory has
vended**. `Log Archive` and `Audit` are absent because the landing zone created them itself.

**The direct assignments.** Each vended account carries a **direct user assignment** of Control Tower's
`AWSAdministratorAccess`, made at vend time and sitting outside the group model; `sso-group-infrastructure`
does not exist until Stage 1b. Two consequences (D32): **remove none of those direct assignments until the
group path is proven end to end** — `sso-group-infrastructure` → `InfrastructureAccess` → a real
`sts:GetCallerIdentity` under each profile — because the only thing behind a lockout is the Management
root ([D16](plan/decisions/D16-break-glass.md)); and **whether they can be removed at all is a
verification**, since a landing-zone update, an account update or a re-enrollment may re-create them.

### Access, per account

| Account | What it holds | Why |
|---|---|---|
| Sandbox, Staging, Production, Data Governance, Identity | `InfrastructureAccess`, through the `sso-group-infrastructure` group | These are the Terraform-managed slices, and this is the identity that applies them |
| Policy Canary | Control Tower's **`AWSAdministratorAccess`**, as a **direct** assignment — *not* `InfrastructureAccess` | Account Factory left it at vend time (D32) and it is **permanent**: the account is outside the Terraform-managed set, has no group and no `awsds-infra-*` profile, so removing it removes the only way in (Stage 1b step 3.8). It is reached through `awsds-policy-canary`. It needs an *administrator*, or the [D29](plan/decisions/D29-policy-canary.md) battery measures the identity policy instead of the SCP ceiling |
| Management | **Nothing, permanently** | Principle 1 makes Management bootstrap-only and console-only; Terraform never runs against it. D33/D34 keep `AWS Control Tower Admin` standing so this user needs no reach there, and [D10](plan/decisions/D10-identity-center-delegation.md) delegates Identity Center to the `Identity` account for the same reason. Stage 1b step 4 creates no assignment here |
| Log Archive, Audit | **Nothing** | Neither was vended by Account Factory and neither holds a Terraform slice. The audit trail has to survive its own administrators — an argument against adding one, not a gap to close |

### The limit of the separation of duties, which is this user

The separation is real *among the four*: no one of them can complete a path alone. It says nothing about
this user, which in AWS terms is **a strict superset of all four**, everywhere it holds administrator.

- In `Data Governance` it can call `lakeformation:GrantPermissions`, the act that *defines* the governance
  manager. The `Data` OU's policy set denies compute, `s3:DeleteBucket` and
  `lakeformation:DeregisterResource`; it does not deny granting.
- In `Production` it can `ecr:PutImage`, and in Sandbox `sagemaker:CreateImageVersion` — the exact actions
  `DevEnvStewardAccess` denies so that the `dev-env` gate is not theatre.
- The derived zone's CMK is what stops a release approver reading query output (D19 as revised by
  [D31](plan/decisions/D31-approver-read.md); since D19's 2026-08-26 revision that key is the **project
  CMK**, the zone being the SMUS project path). An administrator of the account holding the key rewrites
  the key policy, and **this user is the author of that key policy**, because it is the identity Terraform
  runs as. A policy never constrains the principal that writes it (Lesson 18).

**The reach is not bounded by the table above.** It is administrator of `Identity`, which Stage 1b step 1
registers as the delegated administrator of IAM Identity Center, and a delegated administrator can manage
groups *assigned to* the Management account, `AWSControlTowerAdmins` among them. One membership edit and
this user is administrator of Management, Log Archive and Audit. The claim in `README.md`, D33 and D34 —
*the infrastructure user gains no Management-account reach* — is true of **standing assignment** and not
of reachability, and is written that way in all three.

**Since 2026-08-15 that reach no longer needs the membership edit to touch the ceiling.** The delegation of
Stage 2 step 5.1 lets this user write the organization's SCPs, RCPs, tag and declarative policies from
`Identity` — Control Tower's guardrail documents included, since the grant cannot be narrowed by policy
ARN. *Whoever builds the control plane can rewrite the control plane* now includes the preventive ceiling
itself, from a member account, with no Management sign-in anywhere in the path.

**Nothing preventive contains this**; it is a property of the design. What contains it is **detective, and
enumerable**, so it can be checked: the alarm on Control Tower group membership (Stage 1b step 8), S3
Object Lock in **compliance** mode on the Log Archive bucket (Stage 1d step 9), and CloudTrail with log file
validation. If one of those three is missing, this user is unobserved as well as unbounded.

**Two rules follow, and AWS enforces neither:**

- **The "never the same person in two groups" rule extends to this persona**, and it is the hardest
  instance to keep. A human in `sso-group-infrastructure` *plus* any approver group is the separation of
  duties gone in full, because the infrastructure half already contains the other half. With one operator
  this is a statement of intent; it is written down so a second operator inherits a rule instead of a
  habit.
- **`InfrastructureAccess` is the one named exception to `docs/plan/conventions.md`'s "nothing gets
  `AdministratorAccess` or `PowerUserAccess`"**, for a structural reason: an identity that authors IAM
  cannot be constrained by the IAM it authors, so narrowing this set would be notation. The control is that
  it is **one human with one MFA device**; the moment there is a second, D32's revision trigger fires.

## Data Scientist user

- roles: regular user with read-only access to production environment data, and read-write access to the sandbox environment. Can't perform infrastructure changes, unless it is managed by some AWS Service (SageMaker). This user can commit to git repos to develop and trigger CI/CD deploy pipelines that promote artifacts along the chain Sandbox -> Staging -> Production. Sandbox work enters that chain by graduating into an engineering repository through git, never by a pipeline. This user can also commit to git repos that contains build scripts for `dev-env`.

- **The primary working surface is the SageMaker Unified Studio portal** (D26), reached through the VPN
  like every other endpoint. Signing in to the portal is not signing in to the Data Governance account that
  hosts it: the person's projects run in Sandbox, and the access matrix below is unchanged by the portal.
  In the portal this user is a **project member**, never a domain owner.

- the access matrix this expands into, per account ([D18](plan/decisions/D18-data-scientist-access.md)):

  - **Sandbox**: read-write and interactive — the **only** account where the person works interactively.
    `Development`, the other half of this row, became the headless `Staging` on 2026-09-06 and carries a
    **read-only** persona instead (`DataScientistStagingAccess`, D18). **The group question survives the
    account (D35):** a `Sandbox` exists per business unit, so its assignment is to a
    **`sso-group-data-scientists-<bu>`** group covering that unit's Sandbox and nothing else; otherwise
    every data scientist can sign in to every unit's experimentation account. The permission set itself
    (`DataScientistAccess`) is unchanged and shared. With one unit there is no per-unit group yet; what
    exists now is the naming, so the second unit is an addition and not a refactor.
  - **Staging**: read-only, with no write of any kind. Staging is written by the pipeline and read by a
    human diagnosing why the pipeline failed.
  - **Production**: the data plane without compute — logs, catalog metadata, job status, named S3
    prefixes and Athena on a dedicated workgroup. No control plane, no ability to start compute.
  - **Data Governance**: no sign-in at all. The lake is read from Sandbox through the Lake Formation
    cross-account share. The only write toward the lake is `s3:PutObject` into the ingestion drop-box,
    granted by the drop-box **bucket policy in Data Governance together with the mirror statement in
    `DataScientistAccess`** — a cross-account write needs both halves (Lesson 28).
  - **Identity, Audit, Log Archive**: no access.

## The approver users

The original single `Manager user` ("approves deployment of artifacts") was split twice, each time because
a different question needed a different signature, and each time along one of the axes at the top of this
file. **Every split is a separation of duties.**

| | Deployment Manager | Governance Manager | Dev Env Steward |
|---|---|---|---|
| Axis | **Lifecycle** | **Ownership** | **Supply chain** |
| Approves | promotion of an artifact along Sandbox → Staging → Production | data subscriptions and every other access to data | the `dev-env` container image that every notebook runs on |
| Acts in | GitLab (the promotion pipeline's manual gate) | the SageMaker Unified Studio portal | GitLab (the dev-env pipeline's manual gate) |
| Question being answered | *is this build safe to release?* | *may this person read this dataset?* | *is this runtime safe to hand to everyone?* |
| Group | `sso-group-deployment-managers` | `sso-group-governance-managers` | `sso-group-dev-env-stewards` |
| Where they have access | `DeploymentManagerAccess` on Sandbox, Staging and Production — **nothing on Data Governance** | `GovernanceManagerAccess` on **Data Governance only** | `DevEnvStewardAccess` on Production (the registry) and read-only on Sandbox (where the image is registered) — **nothing on Staging, Data Governance or Identity** |
| What they may *read* | Logs, job and pipeline status, catalog metadata, image scan findings, enumerated build-artifact prefixes. **Not** query results, not the derived zones, not decrypted data (D31) | The catalog — names, schemas, classifications, lineage. **Not** the rows | The image: its `Dockerfile` history in GitLab, the build log, ECR image metadata and **enhanced-scanning findings**, and the SageMaker image / app-image-config resources. **No data at all** — no lake prefixes, no Athena, no `kms:Decrypt` |

Neither of the first two is a superset of the other, and the third is on a different axis from both: the
one account the deployment manager may not enter is the only one the governance manager may; the steward
enters neither of those and looks only at artifacts.

**Why the third persona exists** — the D14 argument one level up. Whoever controls the `dev-env` image
controls what code runs in every notebook, against whatever that notebook can reach. A malicious or
careless layer in that image is a credential exfiltrator installed on every workstation at once, and it
arrives *before* any of the other gates, because the data scientist runs it while writing the code the
deployment manager will later approve. D14 puts the supply chain (GitLab, runners, ECR, CodeArtifact) in
Production so the people the gate gates cannot modify it; this persona signs off on the one supply-chain
artifact the data scientist is *supposed* to be able to propose changes to.

**Why the split is a control.** With one persona, a single human could write a job that reads
`restricted` data, approve its promotion to Production, approve that job's access to the dataset, **and**
approve the runtime image the job was written on — four acts, one signature. Split, no one of them can
complete the path alone, at the cost of one extra SSO user per split.

**The steward must not be able to bypass their own gate**: if they can `ecr:PutImage` or create a SageMaker
image version by hand, the approval is theatre. Those actions are denied explicitly in their permission set;
the pipeline holds them, and the pipeline runs only after the gate.

**One rule AWS will not enforce:** never put the same person in more than one of these groups, and never in
one of them plus `sso-group-data-scientists` — **or plus `sso-group-infrastructure`**, the instance that
matters most and the one this table hides, because `sso-group-infrastructure` is not a column here: it
already contains every column ("The limit of the separation of duties" above). With a single operator
every split becomes notation the moment the rule is given in to; Identity Center will not warn, and no
policy can detect it.

### Deployment Manager user

- roles: when infrastructure changes are deployed through CD tool, this user will be used for approving
  deployment of artifacts.

- Exercises the manual approval step in the promotion pipeline, with the Staging test results and the
  Terraform plan in front of them ([Stage 8](plan/stages/stage-08-cicd-pipelines.md)). Also the approver
  for the **time-boxed elevated role** used to debug a failed production job (Stage 9) — a lifecycle act,
  not a data one.

- **Access:** the `DeploymentManagerAccess` permission set on Sandbox, Staging and Production — the
  lifecycle accounts, the axis this persona works on — and **no assignment of any kind on Data
  Governance**. No authority over data grants either: this user cannot approve a subscription, is not a
  domain owner in the Unified Studio domain, and cannot call `lakeformation:GrantPermissions`.

- **The set is not `ReadOnlyAccess`** ([D31](plan/decisions/D31-approver-read.md), 2026-08-08). It used to
  be. The rule stated below for the governance manager — *an approver who can already read everything is
  not exercising a control* — is symmetric: the AWS-managed `ReadOnlyAccess` includes `s3:Get*` and
  `athena:GetQueryResults`, so across those accounts this persona could read the D19 derived zone and other
  people's query output. The derived zone is where the result of a query over `restricted` data lands and,
  by D19's own classification rule, *is* `restricted` (since 2026-08-26 the zone is the SMUS project path;
  the address moved, the argument did not).

  The persona needs **diagnosis**, not reading: why did the promotion fail, is this build safe to release.
  So the set grants CloudWatch Logs read including Logs Insights, SageMaker job / pipeline / Model Registry
  status, Glue catalog metadata, ECR image metadata and scan findings, orchestration execution status, and
  `s3:GetObject` on enumerated build-artifact and test-report prefixes. It denies explicitly: `athena:*`,
  `kms:Decrypt`, secrets and parameters, the Terraform state buckets, and the control plane.

  **The approval itself loses nothing**: it never consumed an AWS permission, and happens in GitLab, driven
  by group membership.

  **The backstop is not in this set at all.** The derived zone sits under a KMS key whose policy names who
  may decrypt (D19 as revised by D31 — the **project CMK** since D19's 2026-08-26 revision). A permission
  set is a list someone has to maintain; the key policy is default-deny and covers prefixes nobody thought
  to enumerate.

### Governance Manager user

- roles: approves data subscriptions and every other access to data.

- **Domain owner / data steward** of the SageMaker Unified Studio domain. Approving a subscription is what
  causes DataZone to write the underlying **Lake Formation grant**, so this user's decisions are what the
  fine-grained access model in D13 resolves to. Also owns the data classification scheme and the LF-Tag
  assignments ([Stage 5](plan/stages/stage-05-data-foundation.md)): the taxonomy and the grants belong to
  the same person, or the taxonomy becomes decoration.

- **Access:** the `GovernanceManagerAccess` permission set on **Data Governance and nowhere else** —
  enough, because since D22 that is the account the governed catalog lives in. It grants Glue catalog
  metadata read, Lake Formation LF-Tag and permission administration, DataZone domain ownership and Macie
  findings read. No authority over releases: this user cannot approve a promotion, holds nothing in the
  lifecycle accounts, and has no role in the pipeline.

- **Not granted, because it is easy to grant by accident:** blanket read access to the data itself. An
  approver who can already read everything is not exercising a control when they approve a subscription.
  They see the catalog — names, schemas, classifications, lineage — not the rows.

### Dev Env Steward user

- roles: approves the `dev-env` container image — the runtime every notebook and every Unified Studio
  project app runs on.

- **The mechanism**, the same shape as the application promotion (Stage 8): the image's build code — a
  `Dockerfile` and its pinned package manifests — lives in a **GitLab repository the data scientist can
  write to**. A change is a merge request. The pipeline builds the image, smoke-tests it, scans it, and
  pushes it to ECR under an immutable tag. **Nothing reaches a working environment until this user approves
  the manual gate**; the approval is what causes the pipeline to register the image so it appears in the
  SageMaker image selector for the Sandbox projects.

- A `dev-env` image version is to the workbench what a **Model Registry version is to a model** (D17): it
  is *approved*, not copied. The build is cheap and anyone may propose one; what is gated is which built
  version becomes the one everybody gets.

- **The data scientist writes to that repository** because it is the one supply-chain artifact whose
  content is their expertise: which version of Julia, which CRAN snapshot, which Rust toolchain. Denying
  them write access would push the request into a ticket and make the environment stale, which is how
  people end up installing things by hand into a notebook and discovering at promotion time that Production
  has different versions. The control is who may *release*, not who may propose.

- **Access:** the `DevEnvStewardAccess` permission set on **Production** (ECR image metadata and enhanced
  scanning findings, the build pipeline's CloudWatch logs) and **read-only on Sandbox** (the SageMaker
  image and app-image-config resources, to confirm what is registered). **Nothing on Staging, Data
  Governance, Identity, Audit, Log Archive or Policy Canary.**

- **Denied explicitly rather than by omission**, because these would make the gate theatre:
  `ecr:PutImage`, `ecr:BatchDeleteImage`, `sagemaker:CreateImage*` and `sagemaker:UpdateAppImageConfig` —
  the pipeline holds those, and runs only after the approval. Also `athena:*`, `kms:Decrypt`, and any
  `s3:GetObject` on lake or derived prefixes: this persona approves a *runtime* and never needs to read
  data.

- **The failure it guards against** is not a bad package version, which shows up as a broken build, but a
  layer that quietly adds a credential-harvesting entrypoint or an outbound beacon to an image that then
  runs in every notebook, holding the SageMaker execution role, inside the VPC. That is why the gate is a
  human reading a diff, and why ECR enhanced scanning blocking on critical findings (Stage 8) is a
  companion to it rather than a substitute.

## Identities this project did not create

Enabling Control Tower (Stage 1a step 3) builds an IAM Identity Center directory **and populates it** with
groups, permission sets and a first administrator. None of it was requested by this plan, and none of it is
a persona. It is listed because **an administrator that appears in no document is indistinguishable from
one that should not be there**, a judgement a security review has to make quickly. One of them has since
been given a job — Control Tower administration (D34) — which makes it a *standing identity with one duty*,
still not a persona.

### `AWS Control Tower Admin` (D33)

An Identity Center user created by the landing zone, carrying the **Management account's root e-mail
address** — the address AWS has at landing-zone time, expected rather than a misconfiguration. Its entire
footprint is **two group memberships, with no direct assignment**:

| Group | Management | Log Archive | Audit | Member accounts |
|---|---|---|---|---|
| `AWSControlTowerAdmins` | `AWSAdministratorAccess` | `AWSAdministratorAccess` | `AWSAdministratorAccess` | `AWSOrganizationsFullAccess` |
| `AWSAccountFactory` | `AWSServiceCatalogEndUserAccess` | — | — | — |

**Read the second and third columns before the first.** It administers **Log Archive**, which holds the
organization CloudTrail bucket, and **Audit**, which holds the security findings plane: it can delete the
record of its own use, including the trail the break-glass alarm reads. The `AWSOrganizationsFullAccess` on
member accounts is close to inert, Organizations being a management-account API — measured from
`Development` on 2026-08-15: `describe-organization` and `describe-effective-policy` answer and every other
call returns `AccessDenied`. What survives in a plain member account is `organizations:LeaveOrganization`,
which a member account *can* call and which drops all governance for that account at once (denied at the
organization root, Stage 1c step 7).

**Identity is the exception.** There this same permission set reaches the whole Organizations surface,
**writes included**: the delegation of Stage 2 step 5.1 names the *account* as its principal rather than a
role ([Identity Account](#identity-account) carries the measurement and the two legs it rests on). So this
identity can edit the organization's policy ceiling — this project's ten documents and Control Tower's own
guardrails — without holding a single permission set of this project's: a fifth reach, not a fifth column.

- **Purpose:** the only identity that can vend accounts, because **root cannot use Account Factory at
  all** — a documented restriction. Since D34 that is a standing job: it owns Control Tower administration
  — creating OUs, vending accounts, enrolling them, landing-zone updates — from the console, never from
  Terraform.
- **Not a sixth persona.** It holds one duty and no other: it approves nothing, owns no data or workload,
  and appears in no separation of duties. It joins neither `sso-group-infrastructure`,
  `sso-group-data-scientists` nor any approver group, and holds no permission set of this project's.
- **Why not the narrow replacement.** `AWSAccountFactory` alone (`AWSServiceCatalogEndUserAccess`) is
  enough to vend into an OU that already exists, through the Service Catalog console, but not to reach the
  **Control Tower console**, where OUs are created and accounts enrolled, which AWS documents as reachable
  only by `AWSControlTowerAdmins`. Creating OUs is part of the job. The choice keeps the **infrastructure
  user out of the Management account**, which D32's one-administrator-one-MFA-device shape depends on.
- **What limits it, permanently.** The reach cannot be trimmed: `AWSControlTowerAdmins` is atomic, and the
  Management administrator arrives in the same membership as the Log Archive one. The control set is three
  permanent things: **MFA on the user**; **S3 Object Lock in *compliance* mode** on the Log Archive bucket
  (Stage 1d step 9), because this principal holds `s3:BypassGovernanceRetention` and walks through
  governance mode; and the **alarm on Identity Center membership and assignment changes** (Stage 1b step
  8.3 — *unfiltered*, so it covers these groups without a maintained list of which groups matter), which
  is what distinguishes the expected member from a second one somebody added.
- **Not renamed and not deleted.** Repointing it at a non-root address treats the symptom and risks a
  landing-zone update re-creating it under the root address, leaving the renamed one behind as a dormant
  administrator (D33).
- **The inbox collision is permanent:** the break-glass alarm's SNS subscription (Stage 1a step 5) must not
  be that address, or one inbox holds the root credential, its own warning, and a routine login. Every
  address here is a `+alias` on one mailbox, so the **SMS endpoint** is the part of that separation that
  is real.

### The groups and permission sets that arrived with it

Control Tower also created its own permission sets — among them **`AWSAdministratorAccess`**, the set every
Account Factory direct assignment points at (D32) and the one the `awsds-policy-canary` profile is
permanently bound to; Stage 1b step 3.2 named this project's set `InfrastructureAccess` to keep the two
distinguishable at a glance — and a set of groups that are **empty and pre-wired**:
`AWSServiceCatalogAdmins`, `AWSSecurityAuditors`, `AWSSecurityAuditPowerUsers`, `AWSLogArchiveAdmins`,
`AWSLogArchiveViewers`, `AWSAuditAccountAdmins`, `AWSAuditAccountViewers`.

**`AWSControlTowerAdmins` is not empty:** it permanently holds the vending owner above (D34), which is why
the alarm on membership changes to these groups is what tells an expected member from an added one. The
rest are empty.

**Empty is not harmless.** Each group already carries its assignments, so adding one person to one of them
is an organization-wide grant made by a single membership edit — `AWSSecurityAuditPowerUsers` holds
`AWSPowerUserAccess` on **every** account, the member accounts included. None of this project's personas
belongs in any of them: Stage 1b builds its own groups beside these, and the two sets stay separate.

# Permission Sets

**Seven sets, and the number is fixed by the design rather than by headcount** — which is what makes them
Terraform: unlike a user or a membership, no amount of hiring adds one.

| Permission set | Group behind it | What it is for, in one line | How it comes into existence | Design of record |
|---|---|---|---|---|
| `InfrastructureAccess` | `sso-group-infrastructure` | The builder — the identity `terraform apply` runs as. The **one named exception** to "nothing gets `AdministratorAccess`" | **By hand**, Stage 1b step 3 — then **imported** at Stage 2 step 5 | 3.1 |
| `DataScientistAccess` | `sso-group-data-scientists` | Studio use through SMUS projects, drop-box write, ECR pull (Athena and the derived-zone families left 2026-08-26 — D19 revised). **Not** `PowerUserAccess`, **not** `AmazonSageMakerFullAccess` | **Written** in Terraform, Stage 2 step 5 — never typed into a console | 3.4 |
| `DataScientistStagingAccess` | `sso-group-data-scientists` | Read-only on Staging, no write of any kind, not even a drop-box | **Written**, Stage 2 step 5 | 3.6 |
| `DataScientistProdAccess` | `sso-group-data-scientists` | Production data plane read: no compute, no control plane | **Written**, Stage 2 step 5 | 3.6 |
| `DeploymentManagerAccess` | `sso-group-deployment-managers` | **Diagnosis, not reading** — why a promotion failed. Nothing on Data Governance | **Written**, Stage 2 step 5 | 3.5 |
| `GovernanceManagerAccess` | `sso-group-governance-managers` | The catalog, never the rows | **Written**, Stage 2 step 5 | 3.5 |
| `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | The artifact, never the data — judging the `dev-env` image | **Written**, Stage 2 step 5 | 3.5 |

*The "Design of record" column is a subsection of
[Stage 1b step 3](plan/stages/stage-01b-identity-and-controls.md), which carries each set's grants **and
its explicit denies**. That file is the specification and this table is the inventory.*

## A permission set is a factory for IAM roles

**It is not an alternative to an IAM role — it produces one**, of the *human* family only; the other is
[above](#the-families-of-iam-role). Assigning set `P` to a principal on account `A` makes IAM Identity
Center provision a real IAM role *inside* `A`:

```
arn:aws:iam::<A>:role/aws-reserved/sso.amazonaws.com/us-west-2/AWSReservedSSO_P_<random suffix>
```

It carries the set's policies and its permissions boundary, and its trust policy trusts Identity Center —
**not the person**, who appears in it nowhere. Signing in through the access portal returns temporary STS
credentials for that role, which is how `CLAUDE.md`'s "avoid IAM Users, in favor of assuming IAM Roles
temporarily" is delivered: no IAM user, no long-lived access key, anywhere in this design.

Consequences:

- **One set assigned on N accounts is N roles**, with N different ARNs — Stage 1b step 3.3 seen from the
  IAM side, and why every grant is scoped by resource ARN and by condition, never by "this account will
  not have that resource".
- **The assumed-role ARN is the evidence, the account ID is not.** Two administrator sets exist four
  characters apart (`InfrastructureAccess` and Control Tower's `AWSAdministratorAccess`), an assignment
  against the wrong one still works, and Stage 1b steps 3.2, 5 and 5.1 all turn on reading that ARN.
- **The suffix is generated per account, so the role ARN is never hard-coded.** A bucket policy or KMS key
  policy naming a human principal matches `AWSReservedSSO_<Set>_*` — relevant from Stage 5 onward, where
  key policies are the backstop the permission sets are not.
- **The generated role is never edited by hand and never declared as `aws_iam_role`.** Identity Center
  reconciles it back, silently.

## Rules the permission sets obey

- **`<Persona>Access`, and never within four characters of a Control Tower set**
  (`docs/plan/conventions.md`). The name says the *group*, not the permission level; a set named after a
  level invites reuse by a second principal.
- **Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now".** `InfrastructureAccess` is the
  single named exception, for a structural reason: an identity that authors IAM cannot be constrained by
  the IAM it authors (Lesson 18). See
  [the limit of the separation of duties](#the-limit-of-the-separation-of-duties-which-is-this-user).
- **For the three approver sets the *denies* are the point.** An approver who can already read everything
  is not exercising a control when they approve. Those denies are explicit, not by omission.
- **The permissions boundary cannot be finished inside `identity/sso/`** (Stage 1b step 3.4). A
  customer-managed boundary is referenced *by name* and the `aws_iam_policy` must already exist **in every
  account the set is provisioned into** — different state, different profile, one more copy per business
  unit (D35). Miss one account and provisioning fails there alone. Stage 2 step 5 carries it as a decision
  row.
- **Control Tower's own sets are never edited or reused.** `AWSAdministratorAccess` is theirs; a
  landing-zone update may reset it, and touching it is drift.

# SSO Groups

**One group per persona.** A group is *person-shaped* — its membership grows with headcount — so **groups
live in the directory and never in Terraform**, while the assignment that binds a group to a permission set
does. That seam is what lets a joiner or a leaver be a directory edit rather than a merge request.

| Group | Persona | Humans behind it, realistically | Holds |
|---|---|---|---|
| `sso-group-infrastructure` | [Infrastructure](#infrastructure-user) | **one**, with one MFA device — D32's shape depends on it | `InfrastructureAccess` on every Terraform-managed account |
| `sso-group-data-scientists` | [Data Scientist](#data-scientist-user) | hundreds | The three `DataScientist*Access` sets |
| `sso-group-deployment-managers` | [Deployment Manager](#deployment-manager-user) | one | `DeploymentManagerAccess` on the lifecycle accounts |
| `sso-group-governance-managers` | [Governance Manager](#governance-manager-user) | one | `GovernanceManagerAccess` on Data Governance alone |
| `sso-group-dev-env-stewards` | [Dev Env Steward](#dev-env-steward-user) | a handful | `DevEnvStewardAccess` on Production and the `Interactive` OU's accounts (the Sandboxes only, since 6b) |

**One group is planned and not created yet:** `sso-group-data-scientists-<bu>`, one per business unit,
covering that unit's `Sandbox` and nothing else (D35,
[Stage 14](plan/stages/stage-14-sandbox-vending.md)). `Sandbox` is one account per business unit and N is
1, so what exists today is the *naming*, which makes the second unit an addition rather than a refactor.
`Staging` and `Production`, past the graduation boundary, are one each, permanently, and keep one group
each.

## Rules the groups obey

- **The `sso-group-` prefix separates two sets of same-named objects**: Control Tower's groups on one side
  (never joined, never repurposed — see
  [the groups that arrived with it](#the-groups-and-permission-sets-that-arrived-with-it)) and, from
  Stage 7, **GitLab groups that mirror these personas 1:1 and do *not* carry the prefix**. A bare
  `deployment-managers` in this repository means the GitLab group; a prefixed one means the directory.
- **The name is load-bearing mechanically.** Assignments resolve their principal by **display name**
  through `data.aws_identitystore_group` — never by GUID, so that replacing the directory with a corporate
  IdP over SCIM re-creates the groups with new IDs and changes nothing in Terraform. A name written one way
  in the plan and another in the directory is a `terraform plan` that fails, or a second group somebody
  creates to make the error go away.
- **A permission set is assigned to a group, never to a user**: one object regardless of how many people
  are in it. The one exception is Account Factory's direct assignment to the infrastructure user (D32),
  which is documented rather than copied.
- **Never the same person in two of these groups**, and never in one plus `sso-group-data-scientists` — or
  plus `sso-group-infrastructure`, which already contains all the others. Identity Center will not warn,
  and no policy can detect it.

# Assignments

**The triple is the unit:** `(permission set, group, account)`. Stage 2 step 5 writes this table out one
row at a time — **enumerated, never generated from a `for_each` over discovered accounts** (D34), because a
grant that appears because an account appeared is the failure mode that rule exists to prevent.

| # | Permission set | Group | Account | What it is for |
|---|---|---|---|---|
| 1 | `InfrastructureAccess` | `sso-group-infrastructure` | Sandbox | Applies the account's Terraform slices |
| 2 | `InfrastructureAccess` | `sso-group-infrastructure` | Staging \* | Applies the account's Terraform slices |
| 3 | `InfrastructureAccess` | `sso-group-infrastructure` | Production | Applies the account's Terraform slices, the supply chain included (D14) |
| 4 | `InfrastructureAccess` | `sso-group-infrastructure` | Data Governance | Applies the lake, the catalog and the Lake Formation wiring |
| 5 | `InfrastructureAccess` | `sso-group-infrastructure` | Identity | Applies `identity/sso/` and `identity/org-policies/` — the entitlement plane applying itself |
| 6 | `DataScientistAccess` | `sso-group-data-scientists` † | Sandbox | Where experimentation happens: read-write, interactive |
| 7 | `DataScientistStagingAccess` | `sso-group-data-scientists` | Staging \* | Reading why the pipeline failed — and nothing else, so Staging stays evidence of what the pipeline does |
| 8 | `DataScientistProdAccess` | `sso-group-data-scientists` | Production | Data plane read: logs, catalog metadata, job status, named prefixes, a dedicated Athena workgroup |
| 9 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Sandbox | Diagnosing a build before releasing it |
| 10 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Staging \* | The test results the promotion gate is decided on |
| 11 | `DeploymentManagerAccess` | `sso-group-deployment-managers` | Production | Diagnosing a failed promotion after the fact |
| 12 | `GovernanceManagerAccess` | `sso-group-governance-managers` | Data Governance | LF-Tags, subscriptions, domain ownership — the catalog, never the rows |
| 13 | `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | Production | ECR image metadata, enhanced-scanning findings, the build pipeline's logs (the registry lives here, D14) |
| 14 | `DevEnvStewardAccess` | `sso-group-dev-env-stewards` | Sandbox | Confirming which image version is actually registered |

\* **The `Staging` rows exist since 2026-09-06**, when Stage 6b made the account by renaming `Development`
after the vend was refused. `InfrastructureAccess` and `DeploymentManagerAccess` moved across with the
account (behind `moved {}` blocks, so nothing was revoked); the data-scientist row is
**`DataScientistStagingAccess`**, swapped in at 6b step 2.1, not `DataScientistAccess`. **There is no
`DevEnvStewardAccess` on Staging** — it judges a container image, and a deployment target registers none.
**14 assignments today, and 14 is the target** until a second business unit is vended.

† **The `DataScientistAccess` assignment on `Sandbox` changes shape at the second business unit.** D35
makes `Sandbox` one account per unit, so its principal moves to `sso-group-data-scientists-<bu>` —
covering that unit's Sandbox alone — while the assignments **past the graduation boundary**
(`DataScientistStagingAccess` on Staging, `DataScientistProdAccess` on Production) stay on the shared
group. The permission set is unchanged and shared; only the principal differs. With one unit there is no
per-unit group yet.

## Accounts with no assignment

| Account | Who has nothing there | Why |
|---|---|---|
| **Management** | **every persona, permanently** | Bootstrap-only and console-only (principle 1); Terraform never runs against it. D33/D34 keep `AWS Control Tower Admin` standing so no persona needs reach here. Stage 1b step 4 creates no assignment |
| **Data Governance** | `sso-group-data-scientists`, `sso-group-deployment-managers`, `sso-group-dev-env-stewards` | The lake is read from Sandbox through the Lake Formation cross-account share (D18/D22), not by signing in. A release approver has no business in the account that grants data access — and `sso-group-governance-managers` is the mirror image, holding only this one |
| **Staging** | `sso-group-dev-env-stewards` | The artifact it judges is a container image, not an environment — the narrowest of the three approver sets |
| **Policy Canary** | **every group** | Reached only by the infrastructure *user*'s direct assignment (below). An account whose whole purpose is to have broken permissions is not somewhere a second persona should sign in and draw conclusions |
| **Log Archive, Audit** | every persona | Neither was vended by Account Factory and neither holds a Terraform slice. The audit trail has to survive its own administrators — an argument against adding an assignment, not a gap to close |

## Assignments outside the table (D32)

Two kinds exist beside the table, and **neither is modelled in Terraform** — Stage 2 step 5.2 leaves both
alone:

- **The Account Factory direct assignments.** Every vended account carries a *direct* assignment of Control
  Tower's `AWSAdministratorAccess` to the **infrastructure user**, created at vend time from the
  `SSOUserEmail` field. They bootstrap the whole identity plane — the `InfrastructureAccess` assignments
  above do not exist until Stage 1b step 3 — and **Stage 1b step 5.1 is where they are retired, or
  recorded as un-retirable.** Removing one before the group path is proven end to end is the cheapest way
  to lock the only administrator out of an account whose sole remaining recovery path is the Management
  root (D16).
- **`Policy Canary`'s, which is permanent and is the exception to that step.** No group and no
  `awsds-infra-*` profile stands behind it, so removing it removes the only way in. It must be an
  *administrator*, or [D29](plan/decisions/D29-policy-canary.md)'s battery measures the identity policy
  instead of the SCP ceiling: a deny a restricted principal could not have exercised anyway proves nothing
  about a ceiling. It is reached through the `awsds-policy-canary` profile.

**Control Tower's own assignments are likewise never modelled** — `AWSControlTowerAdmins` and
`AWSAccountFactory` carry theirs from the landing zone, and editing them is drift. They are described in
[the groups that arrived with it](#the-groups-and-permission-sets-that-arrived-with-it).
