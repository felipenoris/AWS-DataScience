# Conventions and operating model

Read this with any stage from Stage 2 onwards: naming, tags, the `terraform-live/` layout,
the Terraform and IAM rules, and the `[P]`/`[D]`/`[E]` layers every slice is classified into.

---

## 6. Conventions

**Naming:** `<project>-<env>-<component>[-<detail>]`, lowercase with hyphens.
Project prefix: `awsds`. The `<env>` token is one of `sandbox`, `dev`, `data`, `staging`, `prod`, `org`.
`Policy Canary` has no token (D29): nothing is ever created in that account, so nothing in it needs a
name. One bounded exception: a battery run creates throwaway objects — a bucket, an IAM user — to
exercise a candidate policy and deletes them in the same sitting, and Stage 1c step 7.3 plans the cleanup
before the call.
Example: `awsds-sandbox-vpc`, `awsds-data-raw` (the lake lives in Data Governance since D22, so
`awsds-prod-raw-data` would name a bucket that does not exist), `awsds-prod-ecr-dev-env`.

**SSM Parameter Store refuses this prefix** (Stage 2's Validation, 2026-08-16). It reserves every name
beginning with `aws` or `ssm`, case-insensitive, and `awsds` begins with `aws`: `/awsds/…` is rejected at
`PutParameter` with `AccessDeniedException: No access to reserved parameter name`, a message that reads
like a policy problem and is a naming one. **A project parameter takes `/datascience/<env>/…` as its
path** — the project name spelled out, since the abbreviation is what collides. The collision is specific
to Parameter Store *names*; buckets, keys, roles, policies and permission sets all keep `awsds-`. Reading
a public parameter — `/aws/service/ami-…` for an AMI, which `docs/plan/architecture.md` §4.1 requires — is
unaffected: that is AWS's own namespace being read, not ours being written.

**Mandatory tags on every resource:**
`Project=AWS-DataScience`, `Environment=sandbox|development|data|staging|production|org`,
`ManagedBy=terraform|console`, `Owner=<sso-group>`, `CostCenter=<stage>`. `org` marks org-level and
platform resources — the identity slice, and D29's Policy Canary. `shared` is reserved and unused: it
names a Shared Services account if D14's revision trigger ever vends one, and nothing else. `data` marks
the Data Governance account, which is not an environment at all: it sits on the ownership axis, not the
lifecycle one, so cost reports can separate it from every environment.

**`ManagedBy=console` is admitted** (2026-08-12). Stage 2 names seven artefacts that stay outside
Terraform for structural reasons — wrong account, Control Tower's object, the identity seam, or a setting
hand-managed by decision — and the organization Access Analyzer in Audit is one of them. Tagging it
`terraform` would be false at the only moment the tag is read: when somebody is working out where a
resource's source of truth is. **`console` is admissible only for a resource Stage 2's out-of-Terraform
table names**; anywhere else it is a resource that should have been code. `ManagedBy` sits outside the
forcing SCP of 1c step 7.8, which requires `Environment` and `Project` and nothing else, so this
enumeration is a convention rather than a control, and a tag policy that later enumerates `ManagedBy`
values has to admit both.

**`Owner` names a group, never a person** (2026-08-10). The value is one of the project's `sso-group-*`
groups (Stage 1b step 2), and it records who owns the resource, not who created it: a vended account, an
OU and the identity slice are all `Owner=sso-group-infrastructure` even though `AWS Control Tower Admin`
created them, since that identity is in no project group (D33, D34). Ownership rather than authorship
keeps the tag from being a second spelling of `ManagedBy`, and makes it carry information from Stage 6
onwards, when the interactive environment starts creating resources the builder did not.

Why the value is not `<sso-user>`:

- **The literal reading is an e-mail address.** Identity Center users are created with the address as their
  `userName` (Stage 1b step 2), so a per-user value would carry an address out of `secrets/` and into git
  twice over — through Stage 2's Terraform and through 1c step 7.8's tag policy — which `CLAUDE.md` forbids
  outright.
- **A group survives the identity source being replaced; a user name does not.** Same argument 1b step 8.3
  used to refuse a metric filter keyed on a GUID.
- **With one human it would be a constant.** `Owner=<the one builder>` on every resource attributes nothing
  that `ManagedBy=terraform` does not already say, and a column with one value is not an axis (Lesson 9).

**`Owner` is not attribution evidence.** A tag is written by whoever creates the resource, so *who did
this* is answered by CloudTrail's `userIdentity` — collected org-wide since 1a step 5 — and never by
`Owner` (Lesson 5). It is outside the forcing SCP as well, so a resource provisioned by a service on the
project's behalf — a D26 blueprint role, the landing zone's own machinery — does not carry it and nothing
denies the call.

**Every `sandbox` token in this file is per business unit (D35).** `Sandbox` is the one account in the map
that multiplies — one per business unit, N is 1 today — so the tokens written here as singletons are
per-unit: the `<env>` token `sandbox`, the `Environment=sandbox` tag value, the
`Owner=sso-group-data-scientists` tag value (1b step 2 names the per-unit form,
`sso-group-data-scientists-<bu>`), the `terraform-live/sandbox/` tree, the `awsds-infra-sandbox-<n>` SSO
profile, and `make up`/`make down ENV=sandbox`. Development, Staging, Production, Data Governance,
Identity and `org` are structural and stay as written.

**The per-unit token is an ordinal integer** (user, 2026-08-11). `Sandbox Account 1` is reached through
`awsds-infra-sandbox-1`; the second business unit's account is `awsds-infra-sandbox-2`, and so on, with no
gap-filling and no reuse of a retired number. D35 wrote the placeholder as `<bu>`, a business *unit name*,
and this is not that.

- **It matches the name AWS already shows.** The account is `Sandbox Account 1` in the organization, so the
  profile, the account and every console listing agree. A token derived from a unit name would be a second
  vocabulary for the same account, and the mapping between the two would live nowhere.
- **It cannot go stale.** A business unit can be renamed, merged or dissolved; anything named after it then
  carries a name nobody recognises, and renaming deployed resources is the cost this section exists to
  avoid. An ordinal has no meaning to lose.
- **What it costs: the token carries no meaning.** `sandbox-2` does not say whose it is, so the
  **ordinal→business-unit mapping is written where a human reads it — `docs/ORGANIZATION.md`, at the
  vend** — or the ordinal is an index into a table that does not exist.
  [Stage 14](stages/stage-14-sandbox-vending.md) owns that duty; until N is 2 there is nothing to record.

**The `Environment` tag value is not the ordinal** (user, 2026-08-13). Every Sandbox account, at any N,
tags `Environment=sandbox`, and 1c step 7.8's tag policy enumerates it with no ordinal anywhere. An
enumerated value that does not admit a future unit turns the first apply in a freshly vended account into
an `AccessDenied` (Lesson 14), and per-unit cost attribution is already available by **account** without
an organization-policy edit at every vend.

**Left to [Stage 14](stages/stage-14-sandbox-vending.md)**, alongside the CIDR allocation table (Stage 3)
and the VPN topology (Stage 4): the directory shape and the `sandbox-unit` module's interface. Which of
the other per-unit tokens carry the ordinal is open (`open-questions.md` item 10), and
`Environment=sandbox-1` would be an enumerated value inside an SCP-forced tag policy (1c step 7.8), so
that half is decided before the policy is written.

**The `<env>` list and the tag policy's allowed values both enumerate `sandbox`**, and the policy
enumerates `sso-group-data-scientists` for `Owner`, while the forcing function behind the tags is an SCP
conditioned on `aws:RequestTag` (1c step 7). `Owner` fails softer than `Environment`: it is outside that
SCP, so a value the policy does not admit is a non-compliant tagging operation rather than a denied
create — quieter, and therefore the one more likely to be found late. Write every list so a per-unit
token is admissible before it is needed.

**Terraform layout:**

Each slice carries its layer from §5.1: `[P]` persistent, `[D]` dormant (stop/start), `[E]` ephemeral.

**This tree is the authority.** [`terraform-live/README.md`](../../terraform-live/README.md) explains how
the tree is organised — the questions that decide where something goes, which profile applies which
folder, what lives outside it, and what exists there today — and points back here rather than repeating
the tree.

```
terraform-live/
├── identity/             # The identity plane. Two slices (Stage 2 step 5): they reach
│   │                     # their objects through two different delegations, so they are
│   │                     # separated on that seam. Both applied with the
│   │                     # awsds-infra-identity profile; neither touches Management
│   ├── bootstrap/        # [P] state bucket for the Identity account
│   ├── sso/              # [P] permission sets, their policies and boundaries, and the
│   │                     #     group->account assignments. Reached through the IAM Identity
│   │                     #     Center delegated administrator (D10, sso.amazonaws.com),
│   │                     #     which Stage 1b step 1 proves. Six of the seven sets are
│   │                     #     written here and were never typed into a console
│   │                     #     (Stage 1b step 3.9); the administrator set is imported.
│   │                     #     Not here: users and groups - they are people, see "The
│   │                     #     identity seam" below. Nor Control Tower's own sets and
│   │                     #     groups, nor the Account Factory direct assignments (D32):
│   │                     #     editing either is landing-zone drift
│   └── org-policies/     # [P] the SCPs, RCPs, the tag policy and the declarative policy.
│                         #     These are AWS Organizations objects and the Identity Center
│                         #     delegation does not reach them - they need a separate
│                         #     resource-based delegation policy written from Management
│                         #     (INT-20). Console-only and owned by nobody after Stage 1c;
│                         #     since D30 was reverted no principal inside a governed
│                         #     account can work around a bad Deny, so this set needs a
│                         #     diff, a review and a rollback more than anything else here.
│                         #     Not the region restriction: that is a Control Tower control,
│                         #     not a hand-written document (Stage 2 step 5.4)
├── sandbox/              # Experimentation (D21): the unit of work is a notebook.
│   │                     # One per business unit (D35) - the subtree below is what
│   │                     # Stage 14's sandbox-unit module composes from a single
│   │                     # input. N is 1 today; the naming is settled there, not
│   │                     # here (see the D35 note above)
│   ├── bootstrap/        # [P] state bucket for this account (state migrated in, never committed)
│   ├── foundation/       # [P] VPC, subnets, route tables, IGW, security groups, the
│   │                     #     sandbox.awsds.internal zone, KMS keys, IAM roles, the peering
│   │                     #     requester + routes to both Production VPCs (INT-22), and the
│   │                     #     persona's vending policy - a customer-managed policy the
│   │                     #     entitlement plane references by name, so it lives in a [P]
│   │                     #     slice: a missing one fails provisioning of the permission
│   │                     #     set in this account (2026-08-23, persona-vending.tf).
│   │                     #     And awsds-deploy-devenv-sandbox (Stage 8 step 4.2, the
│   │                     #     deploy-role module): the one role the supply chain writes
│   │                     #     into this account with, ending at the image version.
│   │                     #     The Stage 4 VPN anchors and sandbox.internal left at 6c step
│   │                     #     6.5 (2026-09-08): the Elastic IP forgotten (it is
│   │                     #     production/networking/'s [P] allocation), the group, the
│   │                     #     secret and the zone destroyed
│   ├── data/             # [P] the lake's consumer side (consumer-data - the only caller
│   │                     #     since 2026-09-06; development/data/ was destroyed at Stage 6b
│   │                     #     step 2.4): this account's DataLakeSettings, the LF
│   │                     #     resource links + local re-grants to the Data Governance
│   │                     #     share (D22), and the alias/awsds-<env>-data CMK - since
│   │                     #     2026-08-26 the sandbox lake's key, not a derived zone's
│   │                     #     (D19 revised: the zone is the SMUS project path under
│   │                     #     sagemaker/; the derived bucket + enforced workgroup left
│   │                     #     at consumer-data-v0.6.0). The lake itself is not here
│   ├── lake/             # [P] the sandbox lake (Stage 16, applied 2026-08-26):
│   │                     #     awsds-sandbox-lake, permanent artifacts, one prefix per SSO
│   │                     #     group, mounted into SMUS projects via S3 connections and
│   │                     #     vended to laptops via S3 Access Grants. Neither the governed
│   │                     #     lake (no catalog object, no LF-Tag - D13's non-registered
│   │                     #     class) nor the derived zone, which is the SMUS project path
│   │                     #     (D19 revised); the compensations are Stage 16's. Holds the
│   │                     #     bucket, the access role awsds-sandbox-lake-access and (its
│   │                     #     decision 3) the Access Grants location + per-group grants;
│   │                     #     per-project grants are hand-made: runbooks/sandbox-lake.md
│   ├── egress/           # [E] interface VPC endpoints (20 since 6e step 4, single AZ) and the
│   │                     #     DNS Firewall - no NAT, no default route (D38; the NAT code left
│   │                     #     vpc-egress at v0.6.0). The optional families (bedrock, emr,
│   │                     #     mwaa) exist only when `make up ENV=sandbox GROUPS=...` names one
│   ├── probes/           # [E] Stage 3's measurement instruments (perimeter + peering),
│   │                     #     created and destroyed by make up/make down, ranked after
│   │                     #     egress/ so down tears them first
│   ├── warehouse-compute/# [E] the workgroup and its usage limit, and nothing else (D40, Stage 5b
│   │                     #     step 1.7, rank 54). [E] because Redshift Serverless has NO PAUSE -
│   │                     #     create-workgroup and delete-workgroup and nothing in between - so
│   │                     #     "powered off" means "does not exist", which is the only hard
│   │                     #     guarantee that no RPU can be billed. The usage limit is in this
│   │                     #     slice and this apply because a workgroup that exists without its
│   │                     #     ceiling, for even one plan cycle, is the window a mistake costs
│   │                     #     1.44 USD/h in. make down destroys it; RMS storage keeps billing,
│   │                     #     which is the price of keeping the data and is warehouse/'s row
│   ├── warehouse/        # [P] the Redshift Serverless warehouse's data half (D40, Stage 5b,
│   │                     #     rank 53): the namespace awsds-sandbox-warehouse under
│   │                     #     alias/awsds-sandbox-data (read from data/), its Secrets-Manager
│   │                     #     admin credential, its three audit log groups (pre-created with a
│   │                     #     retention period, or Redshift makes them Never Expire), the
│   │                     #     namespace IAM role, the workgroup's security group and the
│   │                     #     alarms. [P] because the namespace holds every database, schema,
│   │                     #     table, database user, role and GRANT - state no plan re-creates,
│   │                     #     which is 5.1 rule 2; the `sandbox` database and its themed
│   │                     #     schemas are SQL inside it. The compute is warehouse-compute/
│   │                     #     above, in the PRIVATE tier's two subnets in two AZs - not the
│   │                     #     isolated tier, which carries no peering route and no client.
│   │                     #     Per admitted project: the tag, the IAM policy and the access
│   │                     #     role Stage 6h's connection needs. No Lake Formation object: the
│   │                     #     sandbox class is outside it by design, like lake/ beside it
│   ├── bedrock/          # [P] the Bedrock grant (6e step 3): one IAM policy for the scoped
│   │                     #     Claude models and one attachment per SMUS project role. The
│   │                     #     roles are the service's, minted per project, so `project_roles`
│   │                     #     is hand-written after a project exists - the blueprint offers a
│   │                     #     boundary for every project role and no grant for any
│   │                     #     (runbooks/claude-code-sagemaker.md section P)
│   ├── model-access/     # [P] the console's model access (Stage 17 decision 13, rank 52): the
│   │                     #     model provisioning role, under the name the console adopts,
│   │                     #     AmazonSageMakerBedrockModelManagementRole-<domain account>, and the
│   │                     #     playground's consumption role, both under the D13 boundary; the
│   │                     #     project they serve is data-governance/governance/'s
│   ├── workflows/        # [P] the workflows grant (6i decision 6, rank 56): one IAM policy -
│   │                     #     DescribeProcessingJob on a processing job no project tag marks,
│   │                     #     which SageMakerProcessingOperator's existence check needs, and
│   │                     #     AddTags of the caller's own project tag, which creating the job
│   │                     #     needs - and one attachment per SMUS project role, hand-written
│   │                     #     like bedrock/'s. Since Stage 8 decision 19 (applied 2026-10-16)
│   │                     #     also awsds-deploy-sandbox-test, the role the deploy
│   │                     #     runner assumes for the CI/CD CLI's test deploy (INT-25), on the
│   │                     #     deploy-role module with its own ceiling: the supply chain's
│   │                     #     second write path into Sandbox, after dev-env/'s
│   ├── observability/    # [P] Stage 12 steps 1, 2 and 9 (rank 70): the account dashboard
│   │                     #     awsds-sandbox-environment, the account's alerts topic
│   │                     #     awsds-sandbox-alerts (Stage 8 decision 5 gave one to each
│   │                     #     deployment target's foundation/, and Sandbox is none), and the
│   │                     #     80 % quota alarms on the SageMaker types in use and the VPC's
│   │                     #     interface endpoints. Reads foundation/; builds warehouse/'s name
│   │                     #     and its two alarms' as that slice does, since warehouse/ reads
│   │                     #     this slice's alerts_topic_arn
│   ├── dev-env/          # [P] the approved dev-env image registered for this account
│   │                     #     (6d step 2, applied 2026-09-10): aws_sagemaker_image +
│   │                     #     image_version + one app_image_config per app type + the
│   │                     #     image role. Reads production/registry/'s state for the
│   │                     #     repository. The domain's CustomImages is NOT here - it is
│   │                     #     the blueprint's field, attached by hand (runbooks/dev-env.md).
│   │                     #     Applied by the Stage 8 step 1 pipeline after the dev-env
│   │                     #     steward's approval, through awsds-deploy-devenv-sandbox -
│   │                     #     the one slice written from Production into an Interactive
│   │                     #     account (INT-18). Its only input is the approved digest
│   └── sagemaker/        # [P] blueprint target (D26): the experimentation project's
│                         #     environments are provisioned here by the domain in
│                         #     data-governance/; running apps are [E], deleted by make down.
│                         #     Terraform owns the prerequisites the blueprint consumes - the
│                         #     provisioning and manage-access roles, the VPC/subnet/AZ
│                         #     parameters handed per region to every blueprint configured in
│                         #     this account (`regional_parameters` over the enabled set -
│                         #     there is no "ML blueprint"; the per-project SageMaker AI
│                         #     domain comes from `Tooling`, and docs/SMUS.md carries the
│                         #     enabled list - Tooling alone adds S3Location/KmsKeyArn, the
│                         #     wizard-field set of 2026-08-22), the KMS key, the projects
│                         #     bucket awsds-<env>-smus-projects, the 11
│                         #     CREATE_ENVIRONMENT_FROM_BLUEPRINT grants (layer 2 of the
│                         #     create authorization; layer 1 sits in governance/), and the
│                         #     D13 boundary policy attached to the project roles (INT-15).
│                         #     It does not declare the project environments themselves:
│                         #     DataZone owns those, and a Terraform resource for them would
│                         #     fight the blueprint. Applied 2026-08-21, and it applies
│                         #     twice: the second apply adds the blueprint configurations,
│                         #     which live here and not in governance/ because
│                         #     PutEnvironmentBlueprintConfiguration takes no account
│                         #     parameter - it configures the caller's account, which is why
│                         #     an associated account is what enables blueprints against a
│                         #     shared domain. The flag is backend.SMUS_ASSOCIATED, whose
│                         #     rows are measurements
├── data-governance/      # The ownership axis (D22, D26): state and governance,
│   │                     # never compute
│   ├── bootstrap/        # [P] state bucket for the Data Governance account
│   ├── data/             # [P] raw/curated S3 (Iceberg), Glue Data Catalog, Lake Formation
│   │                     #     registrations + LF-Tags (D13), ingestion drop-box (D18),
│   │                     #     cross-account shares to sandbox (+ production at Stage 9;
│   │                     #     development's was revoked 2026-09-06, Stage 6b step 2.3),
│   │                     #     Glue Crawlers on raw + drop-box under the D27 exception
│   │                     #     (config is free at rest; runs are metered, event-driven);
│   │                     #     behind LAKE_PUBLISHERS, the two SMUS administrator seats and
│   │                     #     the publisher's grant on each published table (publishing.tf)
│   ├── publishing/       # [P] Stage 6f step 11, the lake-publishing pilot (decision 1,
│   │                     #     shape (b), 2026-10-26; D22 amended): the VPC the managed
│   │                     #     Tooling template takes (vpc module, no internet route, no
│   │                     #     peering) and terraform-modules/sagemaker-prereqs/ with Tooling
│   │                     #     alone; the configuration and its grant follow LAKE_PUBLISHERS,
│   │                     #     the domain's own account needing no association. Rank 46;
│   │                     #     first apply 2026-10-26 (11.2), the configuration unapplied. The
│   │                     #     rollback destroys it but the projects bucket, which the Data
│   │                     #     OU's s3:DeleteBucket deny keeps
│   └── governance/       # [P] the SageMaker unified domain (DataZone V2, D26), applied
│                         #     2026-08-21. Verification (ii) answered: the aws-ia module
│                         #     was not consumed - its root requires vpc_id/subnet_ids and
│                         #     enables the Tooling blueprint in the domain account, which
│                         #     D22 forbids, and the resources are five, so writing them
│                         #     directly was cheaper than splitting a module that assumes a
│                         #     single account. Domain + IAM through `aws`; project profiles
│                         #     and the CREATE_PROJECT_FROM_PROJECT_PROFILE grants on the
│                         #     root unit (grants.tf, applied 2026-08-22 - layer 1 of the
│                         #     create authorization) through `awscc`, the only provider with
│                         #     awscc_datazone_project_profile. Account associations to
│                         #     sandbox and development (INT-12) are console-only - no public
│                         #     API - and the blueprint configurations are applied from the
│                         #     member account (see */sagemaker/ below).
│                         #     A registry: blueprints provision compute into those
│                         #     accounts, never into this one; the lake-publishing pilot's
│                         #     Tooling, with spaces off, is the one environment it
│                         #     provisions into itself (the `lake-publishing` profile,
│                         #     LAKE_PUBLISHERS). No foundation/ slice and no user compute;
│                         #     the one VPC is publishing/'s and peers with nothing, which
│                         #     is why INT-13 still has no host. Since Stage 17 decision 13 also the
│                         #     project the console's model access publishes into,
│                         #     GenerativeAIModelGovernanceProject, its profile with no
│                         #     environment configuration, and Sandbox's InfrastructureAccess
│                         #     as its contributor (model-governance.tf)
├── staging/              # Deployment target (D20, D17): the Development account renamed at
│   │                     # Stage 6b (2026-09-06) - not a vend, the quota refused that.
│   │                     # SageMaker runtime only - no domain, no space, no blueprint, no
│   │                     # Model Registry of its own, no GitLab, no lake share (revoked at
│   │                     # 6b 2.3). CIDR stays 10.50.0.0/16: a CIDR is immutable and a
│   │                     # rebuild would replace every subnet, endpoint and the peering.
│   │                     # There is no development/ entry: its sagemaker/ and data/ were
│   │                     # destroyed at 6b 1.7 and 2.4, foundation/, egress/ and probes/
│   │                     # migrated here at 4.3, and bootstrap/ - which owned
│   │                     # awsds-dev-tfstate, the bucket every migration read from - went
│   │                     # last at 4.7. probes/ left at Stage 8 step 3.1 with no state:
│   │                     # its target sits in VPC-SharedServices, which this VPC does
│   │                     # not peer with
│   ├── bootstrap/        # [P] awsds-staging-tfstate + its key (6b 4.2, applied 2026-09-06)
│   ├── foundation/       # [P] VPC, subnets, KMS, IAM roles - migrated from
│   │                     #     development/foundation/ with its VPC and its [P] gateway
│   │                     #     endpoint ids intact (the INT-05 anchors). Peering requester
│   │                     #     to VPC-Networking only (D20 amended at 6c): the proxy is
│   │                     #     this account's whole internet, and there is no default route.
│   │                     #     And awsds-deploy-staging with awsds-staging-alerts (Stage 8
│   │                     #     step 4.1, decision 5), the deploy-role module
│   ├── data/             # [P] the lake read through a read-only share (Stage 9 decision 3:
│   │                     #     no mirror, no copy), the outputs and derived buckets and the
│   │                     #     enforced workgroup, under alias/awsds-staging-data - a new key
│   │                     #     created at Stage 9, never the dev-named one 6b destroyed
│   ├── sagemaker/        # [P] awsds-staging-job-exec, its job log groups, and the jobs'
│   │                     #     security group and Glue connection (Stage 9 4.3, decision 12)
│   ├── orchestration/    # [E] MWAA Serverless workflows for the staging leg (D7 amended:
│   │                     #     a serverless workflow bills nothing at rest, so the reason
│   │                     #     orchestration was Production-only is gone), with the chain
│   │                     #     layer above them (D41), as in production/orchestration/
│   ├── egress/           # [E] interface endpoints only (7, VPC-Workloads' set since Stage 9
│   │                     #     step 4.3a and decision 12) and the DNS Firewall - NO NAT, no default route
│   │                     #     (D38). Measured empty at the migration; D11 leaves it torn
│   │                     #     down between sittings
│   └── app/
│       └── app-etl/      # [E] deployed by the pipeline, destroyed by the user's make down
└── production/
    ├── bootstrap/        # [P]
    ├── foundation/       # [P] VPC-SharedServices (10.30.0.0/16 - the VPC built at Stage 3,
    │                     #     re-labelled at 6c): GitLab, Pages, the runners and the build
    │                     #     host. Peering accepters, and the awsds.internal apex zone
    │                     #     plus awsds-pages.internal (D15/D36 amended); the old
    │                     #     prod.internal and pages.internal zones were destroyed at
    │                     #     6c 2.6 (2026-09-07). Built in Stage 3, because Stage 7
    │                     #     (GitLab) depends on it (D14). Also GitLab's [P] anchors - the
    │                     #     object-storage and backup buckets, the gitlab-secrets container
    │                     #     and the runner-token container (Stage 7 step 1.1): an anchor
    │                     #     must survive the destruction of tooling/ and runners/, the same
    │                     #     argument that keeps both hub hosts' anchors in networking/
    │                     #     below. Also the deploy runner's anchors - its role, instance
    │                     #     profile and token container (Stage 8 step 4.3: a trust policy
    │                     #     keeps a role's unique id, so the role outlives the [E] host) -
    │                     #     awsds-deploy-prod and awsds-prod-alerts. No public zone, no
    │                     #     registered domain: those are Stage 13, and not the CA - see
    │                     #     pki/ below
    ├── networking/       # [P] VPC-Networking (10.31.0.0/16, created at 6c - D38): the
    │                     #     estate's only internet gateway and its only internet-facing
    │                     #     tier, the peering accepter for every spoke, and the [P]
    │                     #     anchors of both hub hosts (the WireGuard Elastic IP, transferred
    │                     #     from Sandbox with its host, two security groups, the host-key
    │                     #     secret, the proxy allow-list parameter).
    │                     #     Carries no interface endpoint with private DNS and no
    │                     #     service-name private zone: the VPN client resolves here
    │                     #     (Lessons 40-43)
    ├── vpn/              # [D] the WireGuard host (D4 amended: the home moved here at 6c).
    │                     #     The instance only - same rule as proxy/ below. Forwards tunnel
    │                     #     packets to RFC1918 destinations only
    ├── proxy/            # [D] the Squid host - the estate's single egress. The instance only:
    │                     #     its Elastic IP, security group and allow-list parameter are
    │                     #     networking/'s [P] anchors, so a `make down` cannot release the
    │                     #     address (6g decision due 1 re-reads that, D39). Its access log
    │                     #     is Stage 11's egress evidence
    ├── workloads/        # [P] VPC-Workloads (10.32.0.0/16, created at 6c): the production
    │                     #     SageMaker runtime, MWAA Serverless workers, production jobs.
    │                     #     No IGW route in any table. Two private subnets in two AZs -
    │                     #     the one D9 exception in the estate, required by MWAA
    │                     #     Serverless's documented private-routing shape (Stage 10 1.2)
    ├── workloads-egress/ # [E] the interface endpoints and DNS firewall for VPC-Workloads.
    │                     #     A second endpoint slice in one account, because an egress-
    │                     #     shaped slice reads exactly one foundation/: egress/ below
    │                     #     serves VPC-SharedServices and cannot also serve this one.
    │                     #     Rank 51, just above egress (50). Created at 6c step 1.3a;
    │                     #     Stage 9 step 3.3a names the jobs' seven endpoints and turns the
    │                     #     DNS Firewall on, AWS namespaces only; Stage 10 step 1.2 adds
    │                     #     the workers'
    ├── pki/              # [P] the internal root CA (D36). Own state file and own KMS key,
    │                     #     not foundation/'s: foundation is opened to change a CIDR or
    │                     #     accept a peering, and every such edit would otherwise decrypt
    │                     #     the root. Applied at Stage 7 pass 1, with the leaves (D36 3
    │                     #     amended 2026-08-21): nothing serves a .internal name before
    │                     #     Stage 7, so the dev-env image takes the root at Stage 7 step
    │                     #     2.6 (INT-19). Its state key exists in production/bootstrap/
    │                     #     since 2026-08-15. Outputs the CA cert and the issued leaves -
    │                     #     never the root private key. Excluded from every make down path
    ├── data/             # [P] application-output buckets, Athena workgroup, LF resource
    │                     #     links + the governed-write regrant to the job role (D22; the
    │                     #     account-level grant is data-governance/data/'s - Stage 9
    │                     #     step 2's two-step). The lake itself lives in
    │                     #     data-governance/. The registries are not here - see below
    ├── registry/         # [P] ECR (+ pull-through cache) and CodeArtifact (D14), with their
    │                     #     own KMS key and consumer account ids from a map. Separate from
    │                     #     data/ to preserve D14's revision option: if the supply chain
    │                     #     ever moves to a Shared Services account, this slice leaves and
    │                     #     data/ stays. A folder is not a boundary - it buys migration
    │                     #     cost only (Stage 7, option-preservation note). Applied in two
    │                     #     passes, split by consumer: the base/dev-env repositories,
    │                     #     CodeArtifact, the key and the consumer policies (Stage 7 step
    │                     #     5.a) go in at Stage 6's pass 0, because Stage 6 step 5.0
    │                     #     pushes into them; the pull-through cache and the
    │                     #     per-application repositories (5.b) wait for Stage 7, the first
    │                     #     thing that pulls from either. The 5.a half is applied
    │                     #     (2026-08-21, 14 resources). Stage 8 decision 20 (applied
    │                     #     2026-10-16) adds awsds-prod-releases, the bucket
    │                     #     each application release's bundle is stored in, under the
    │                     #     slice's key, its deletes denied to every principal but
    │                     #     InfrastructureAccess
    ├── warehouse-compute/# [E] the governed workgroup and its usage limit (D40, Stage 9 step 9,
    │                     #     rank 54). Same split and same reason as sandbox/'s: no pause exists
    ├── warehouse/        # [P] the governed half of the warehouse (D40, Stage 9 step 9, rank 53):
    │                     #     the namespace awsds-prod-warehouse; its workgroup is
    │                     #     warehouse-compute/'s, in VPC-Workloads' two private subnets, so
    │                     #     this account needs no new network work. Holds the `governed`
    │                     #     database, whose rows awsds-prod-job-exec writes, and reaches readers
    │                     #     only through Lake Formation, by Stage 9 decision 5's shape: a
    │                     #     Lake Formation-managed datashare Data Governance registers
    │                     #     (decision 14), read from Sandbox on 2026-10-25. No project
    │                     #     tag, no connection: D26 keeps deployment targets out of the domain,
    │                     #     so 6h's three layers collapse to the GRANT alone
    ├── sagemaker/        # [P] Model Registry (model package groups) + the execution role
    │                     #     pipeline-submitted jobs assume, its job log groups, and the
    │                     #     escape hatch awsds-prod-debug with its alarm (Stage 9 steps 3
    │                     #     and 6, rank 46); the rule awsds-prod-model-approval on every
    │                     #     model package's state change (Stage 10 step 5.3), and the jobs'
    │                     #     security group and Glue connection (decision 12). No domain, no
    │                     #     user profiles (D17)
    ├── egress/           # [E] VPC-SharedServices' interface endpoints (12 since Stage 7: 6c
    │                     #     5.5's 13 plus secretsmanager, step 1.7, minus the SageMaker pair,
    │                     #     decision 9) - no NAT anywhere (D38; the NAT
    │                     #     code left vpc-egress at v0.6.0, 6c 5.1). No internal ALB: Stage 7
    │                     #     decision 1 terminates TLS on GitLab's own nginx
    ├── probes/           # [E] Stage 3's instrument here: the peering target
    ├── tooling/          # [D] GitLab CE on a t4g.large + its data volume (D8, D14), rank 52,
    │                     #     above egress/ (50): the host starts after the ssm endpoint its
    │                     #     agent registers through exists, and stops before it is destroyed.
    │                     #     Applied 2026-10-12. TLS terminates on its own nginx with pki/'s
    │                     #     leaves (Stage 7 decision 1); letsencrypt['enable'] = false is
    │                     #     mandatory, since Omnibus turns it on whenever external_url is
    │                     #     https and retries every reconfigure (1.3). gitlab.rb is rendered
    │                     #     into the objects bucket and fetched by the host (decision 8);
    │                     #     the user data and the AMI are held. Also both security groups,
    │                     #     the two records and the daily DLM snapshot policy
    ├── runners/          # [E] the build runner (D14), rank 57 - amd64 on the buildbox's
    │                     #     measured m8i.xlarge, registered at boot with the token in
    │                     #     foundation/'s container, pushing with its instance profile and
    │                     #     holding no deploy permission; the buildbox (rank 55) retired
    │                     #     into it at Stage 7 step 6.5
    ├── observability/    # [P] Stage 12 steps 1, 2 and 9 (rank 70): the hub dashboard
    │                     #     awsds-prod-hub, which carries Production's own panels too (the free
    │                     #     tier holds three dashboards, counted once per bill); the proxy access
    │                     #     log's two metric filters and the refusal alarm; the VPCs-per-Region
    │                     #     quota alarm. The alarms notify foundation/'s awsds-prod-alerts.
    │                     #     Reads foundation/, networking/ and workloads/; names the [D] hosts'
    │                     #     alarms by name and never reads a [D] state (Lesson 4)
    ├── orchestration/    # [E] MWAA Serverless only (D7 amended 2026-09-05):
    │                     #     awscc_mwaaserverless_workflow per app, YAML in S3, a
    │                     #     per-workflow role and log group (D28), NetworkConfiguration
    │                     #     always set on VPC-Workloads' private subnets. Above the
    │                     #     workflows, the chain layer (D41): per account a schedule
    │                     #     group, the machines' log group and the chain roles; per
    │                     #     chain a Step Functions state machine, its Scheduler schedule
    │                     #     and its failure rule; per bridge an EventBridge rule; the
    │                     #     provisioned-MWAA rung is gone
    └── app/
        └── app-etl/      # [E]

terraform-modules/        # reusable modules (the roster and its tags: terraform-modules/README.md)
                          # consumed by git tag, never by branch - a module that moves under a
                          # caller is a broken caller
```

`make down ENV=sandbox` destroys the `[E]` slices in reverse dependency order and stops the `[D]`
instances; `make up ENV=sandbox` starts the `[D]` instances and applies the `[E]` slices; `make status`
reports what is running and the current hourly burn. **`ENV` names a business unit's sandbox, not *the*
sandbox** (D35): Stage 14 step 6 makes the same `up`/`down` pair work against a generated unit, which is
what makes a unit disposable rather than merely creatable. `[P]` slices are never touched by any of them;
they are applied by hand. One `[E]` resource lives outside any slice: the running **apps inside a Unified
Studio project** are created by users, not by Terraform, so `make down` deletes them through the API
before touching the slices. The apps live in the per-project SageMaker AI domain the `Tooling` blueprint
provisioned into the account (D26), so the teardown is `sagemaker:ListApps`/`DeleteApp` (and the enclosing
space) scoped to that domain, never a call against the DataZone domain, which owns no compute. `make down`
discovers the domain ID rather than having it pasted in, since the blueprint chose it.

`ENV=staging` is raised and taken down by the user, as every other environment (Stage 8 decision 27,
2026-10-24): `make up ENV=staging ONLY=egress` before a promotion's tag and `make down ENV=staging` after
its leg. The pipeline applies the application's own slices alone, `staging/app/<app>/` and
`staging/orchestration/`, destroys nothing, as in Production, and `layers.py` refusal 10 keeps its profile
off every shared slice. The user's destroy of a table the deploy role created rests on
`InfrastructureAccess`'s `DROP` on `app_outputs` ([`GOVERNANCE.md`](../GOVERNANCE.md) §Grants, Lesson 75).
Both paths work by hand — a rebuild that only works from CI is the
same bug as one that only works by hand.

**Terraform rules:**

- Pin the provider version and `required_version`. One `providers.tf` per slice.
- Region, AZs and AMIs follow the portability rules in `docs/plan/architecture.md` §4.1 — no region
  literals in `.tf` files.
- Authentication through named SSO profiles, one per Terraform-managed account — `awsds-infra-sandbox-1`,
  `awsds-infra-data`, `awsds-infra-staging` (the renamed `Development`'s since Stage 6b; `awsds-infra-dev`
  is gone), `awsds-infra-prod`, `awsds-infra-identity` (Stage 1b step 5) — never keys. **The sandbox one is
  ordinal-suffixed and there is one per business unit** (D35): `-1` today, `-2` when the second unit is
  vended. The other four are structural and carry no suffix.
- Every slice: `terraform fmt`, `validate` and `plan` must be clean before apply.
- Remote state read across slices through `terraform_remote_state` data sources, never hardcoded IDs.
- **The Organization is never in Terraform (D34).** Accounts and OUs are created from the console, by
  design (principle 1), so no state declares them and none of it can drift. What it *can* do is leave a
  console-created OU or account outside code written as a list — invisible rather than drifted, with
  `terraform plan` reporting "No changes". So, across the two identity slices: **the floor is discovered,
  the grants are enumerated.** Anything that must cover everything — the organization-root SCP/RCP set,
  the tag policy, the declarative policy, all in `identity/org-policies/` — has to be covered whatever
  exists tomorrow; permission set assignments, in `identity/sso/`, are written out one by one, because an
  account acquiring a grant by simply existing is the failure mode this rule prevents.
  **Coverage is bought by the attachment point, and discovery is spent on the check** — corrected
  2026-08-15, after Stage 1c was executed. 1c attached every must-cover-everything document to the
  **organization root**, and SCPs inherit, so a new OU or account is covered the moment it exists, with no
  attachment to create. The four per-OU documents are all *different*, and three OUs carry **none**
  (`Policy Test`, `Security`, and `Sandboxes` under D37), so a `for_each` attaching "the OU document"
  everywhere would put one on `Sandboxes` and reverse a decision with `terraform plan` reading like
  ordinary coverage. `make check` enumerates the OUs at both levels and fails on one that appears in
  neither the authored OU→document map nor its explicit *no document* list
  ([Stage 2](stages/stage-02-terraform-foundation.md) step 9.3).
  **What "enumerated" means once the Sandbox multiplies (D35):** a `for_each` over a human-authored map of
  business units, kept in a `.tfvars`, is still enumeration — a unit acquires its assignment because
  somebody wrote its name down, not because an account appeared. What the rule forbids is `for_each` over
  a *data source*: an assignment keyed on `data.aws_organizations_organization.accounts` grants by
  discovery. Stage 14 generates a unit's group and assignment from that same map.
- Modules are referenced by **git tag**, never by branch, so a module change cannot silently alter an
  existing deployment.

**The identity seam — what goes in Terraform:**

**Nothing whose count grows with the number of people belongs in Terraform.** The line runs between a
*person* and an *entitlement*, and it is drawn here rather than in a stage file because it has to survive
every stage:

| | Person-shaped | Entitlement-shaped |
|---|---|---|
| What | Identity Center **users**, **groups**, and group **memberships** | **permission sets**, their inline or customer-managed policies, **permissions boundaries**, and **group→account assignments** |
| How many | grows with headcount — hundreds of data scientists, a dozen `dev-env` stewards | fixed by the design: seven sets, and O(groups × accounts) assignments |
| Where it lives | the directory. Console at lab scale (four users, Stage 1b step 2); **SCIM from the corporate IdP** in any real deployment | `terraform-live/identity/sso/` (Stage 2 step 5) |
| Why not the other way | Terraform would become the HR system, with personal data in a state file and joiners/leavers as merge requests | a console-only entitlement has no diff, no review and no rollback |

Each rule below has a silent failure mode:

- **An Identity Center group is named `sso-group-<persona>`:** `sso-group-infrastructure`,
  `sso-group-data-scientists`, `sso-group-deployment-managers`, `sso-group-governance-managers`,
  `sso-group-dev-env-stewards`; a per-business-unit Sandbox group is `sso-group-data-scientists-<bu>`
  (D35, Stage 14). The prefix separates two sets of same-named objects: Control Tower's own groups
  (`AWSControlTowerAdmins`, `AWSAccountFactory`, the auditor and per-account groups — never to be joined
  or repurposed), and, from Stage 7, GitLab groups that mirror these personas 1:1 and do *not* carry the
  prefix — `deployment-managers` and `dev-env-stewards` in GitLab hold the two approval gates. A bare
  `deployment-managers` in this repository means the GitLab group; a prefixed one means the directory.
  The exactness matters mechanically: assignments resolve their principal by **display name** through
  `data.aws_identitystore_group`, so a name written one way in the plan and another way in the directory
  is a `terraform plan` that fails — or, worse, a second group someone creates to make the error go away.
- **A permission set is named `<Persona>Access`, and never within four characters of a Control Tower set:**
  `InfrastructureAccess`, `DataScientistAccess`, `DataScientistStagingAccess`, `DataScientistProdAccess`,
  `DeploymentManagerAccess`, `GovernanceManagerAccess`, `DevEnvStewardAccess`. The name is the group's,
  not the permission level's: a set called after a level invites reuse by a second principal, and the
  `AdministratorAccess` exception below is meant to be read narrowly. A near-miss with a Control Tower set
  is a silent fault: the administrator set was to be `AdministratorAccess`, four characters from Control
  Tower's `AWSAdministratorAccess`, and an assignment made against the wrong one still works while the two
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

**`aws_s3_account_public_access_block` is never declared in any slice.** The account-level setting is made
by hand in Stage 1c step 7.4, and step 7.5 then denies `s3:PutAccountPublicAccessBlock`, so an apply or a
drift correction that touches it fails. It reads like something that belongs in `foundation/`, which is
why it is written down here. The 2026-08-13 carve-out does not soften the rule: the deny exempts exactly
the principal Terraform runs as, so an apply declaring this resource would *succeed*, and the setting
would then have two owners — a hand-made one and a state file, with drift correction able to turn the
blanket off in an account the module never touches.

**IAM rules** (conventions, because they are easy to violate one role at a time):

- Every role that a non-administrator can create or influence carries a **permissions boundary**.
- `iam:PassRole` is never granted unqualified. It is always scoped by `iam:PassedToService` and by resource
  ARN. `PassRole` plus a job-creating API (`sagemaker:CreateTrainingJob` is the relevant one here) is a
  privilege-escalation path: it lets a user run code under any role they are allowed to pass.
- Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now". A permission set starts narrow:
  loosening a permission is a five-minute change and tightening one is a negotiation. **The one exception
  is the `sso-group-infrastructure` group** (D32; `docs/ORGANIZATION.md`, "The limit of the separation of
  duties"). It holds **`InfrastructureAccess`** — the one permission set that attaches
  `AdministratorAccess` — on every Terraform-managed account, because it is the identity `terraform apply`
  runs as and an identity that *authors* IAM cannot be constrained by the IAM it authors (Lesson 18). What
  contains it is detective and enumerated: the Control Tower group-membership alarm, Object Lock in
  compliance mode, CloudTrail with log file validation. **Read the exception narrowly** — it covers one
  group, and any other principal holding administrator is a finding, not a precedent.
- **No broad managed policy for a principal that is itself a control** (D31). `ReadOnlyAccess` is not
  harmless for an approver: it carries `s3:Get*` and `athena:GetQueryResults`, so it reaches the derived
  zones and other people's query output. Every persona gets a set written for its job — three for the data
  scientist (D18), one for each approver — and the two approver sets exist for their *denials*.
- **Where a read restriction has to survive forgetting, put it in a KMS key policy rather than in a list of
  prefixes** (D19 as revised by D31). A permission set enumerates; a key policy is default-deny. The
  derived zone has its own CMK for this reason, and the separation from the account's general-purpose key
  is what makes the restriction expressible at all.
- **No principal is exempt from a deny "just in case"**, and D30's reversion left no exception. Carve-outs
  are per function and per statement: the catalog-maintenance role exempt from the `Data` OU's Glue deny
  (D27), `datazone:*` as a governance control plane (D26), a deploy role exempt from a specific deny so
  automation does not stall. Each names one principal, one statement and one reason. A standing role
  exempt from *every* custom deny was proposed and removed: the recovery path is the Management account,
  which sits outside SCPs by AWS's design (D16), and the cheap defence is catching the bad policy in the
  `Policy Canary` before it is attached (D29).
- **Any ARN condition uses an enumerated list, never a wildcard account.** `arn:aws:iam::*:role/x` reads
  as "any principal named `x`, in any account", so a condition written to name one role silently names a
  role that anybody able to create a role can mint. This applies to the per-function carve-outs above and
  is checked by **`make check`** (Stage 2 step 9.2), which the CI runs on every pull request
  (`.github/workflows/offline-gates.yml`, Stage 8 step 6.2).
  **The one exception, which the check knows by name** (decision 7, 2026-08-13): the `Sid` that carves
  `InfrastructureAccess` out of the organization-root deny on `s3:PutAccountPublicAccessBlock` (1c step
  7.5). It must reach accounts that **do not exist yet** — the Identity Center role ARN carries a
  per-account random suffix, so the accounts that matter most cannot be enumerated even in principle. The
  residual is bounded: minting a role that matches the pattern requires `iam:CreateRole` in that account,
  which is administrator, which is the identity the carve-out already names. A second exception would be a
  decision, not a precedent, and `make check` failing on this one `Sid` is the check working — whitelist
  it explicitly rather than loosening the rule.
- **In a deny keyed on a *resource* condition, the action list is enumerated and every action in it must
  populate that key — never an action wildcard** (found 2026-08-13, writing 1c step 7.5's perimeter
  document). This is the mirror image of the rule above, and the more dangerous of the two, because it
  fails *closed* over something legitimate. A negated or `IfExists` condition **evaluates true when the key
  is absent**, so a `Deny` conditioned on `aws:ResourceOrgID` catches every action that carries no resource
  for the key to come from. `s3:Put*` therefore reaches **`s3:PutAccountPublicAccessBlock`**, which is
  account-level: the perimeter document would deny, in every account at once and for every principal, the
  exact call 7.4 depends on — and the decision-7 carve-out would not save it, because that carve-out lives
  in a different statement in a different document. The same applies to `ecr:GetAuthorizationToken`, which
  is registry-scoped and is left out of the ECR half of the same statement. So enumerate object- and
  repository-scoped actions: a wildcard's failure is silent until somebody vends an account.

### Application repository layout

The template for an application written by a data scientist and intended for deployment, consumed by
[Stage 8](stages/stage-08-cicd-pipelines.md) (the three pipeline types) and
[Stage 10](stages/stage-10-orchestration-promotion.md):

```
app-etl/
├── src/app_etl/      # the code a processing job reads as its input, never in the image (D28 class 2d)
│   ├── pipeline.py   # the transformation
│   └── __main__.py   # the command a processing job runs
├── tests/
│   └── test_pipeline.py
├── samples/          # synthetic input: the image's smoke test and a Sandbox job read it
├── .gitlab-ci.yml    # the pipeline, with the shared gates of awsds/ci-gates
├── Dockerfile        # the application image and the job image, FROM base by digest: the lock's dependencies, not the project
├── manifest.yaml     # the SageMaker application: its name, its content and its stages (D41)
├── workflows/
│   └── app-etl.yaml  # the MWAA Serverless definition in the CI/CD CLI's notation, checked by the D28 lint on its rendered copy
├── code/             # modules for PythonOperator/BashOperator tasks, zipped by CI (D28 class 2b)
├── glue/             # one script per Glue job, a Visual ETL flow's generated script among them (D28 class 2c)
├── pyproject.toml    # and uv.lock
└── README.md
```

The template's first content is [`examples/app-etl/`](../../examples/app-etl/README.md), pushed to GitLab's
`awsds/app-etl` at Stage 8 step 2.2; `manifest.yaml`, `workflows/`, `code/` and `glue/` joined it at
Stage 8 step 2.5 (2026-10-16), whose four tasks include the Glue job (D41). The development stack is similar to <https://github.com/felipenoris/etl-cookbook-tutorial>: uv, pytest and pdoc. The
application's Terraform is not in its repository: each environment's slice is
`terraform-live/<env>/app/app-etl/` above, `[E]` everywhere and written from `terraform-modules/`
(Sandbox's retired by Stage 8 decision 21, 2026-10-16, the `dev` project being D41's engineering loop),
and the release it runs is a variable whose default is a tracked line (Stage 8 decision 12). `workflows/` holds
the definition in the CI/CD CLI's notation, which the CLI deploys to the `dev` and `test` projects and
bundles (Stage 10 steps 2.1-2.2); the release job renders it per environment from the release's bundle
and copies it to the definitions home with the code package the tag pipeline built from `code/` when
there is one, which the `orchestration/` slices pin, and `src/` beside them as the processing job's input
(step 2.4). `glue/` holds the scripts the application's Glue jobs run: the release job copies them under
the release's prefix, and the jobs the application slice declares name them there (Stage 10 decision 12).

The directories follow D28's line between content and activation. `src/` is the code a SageMaker job
runs, read as the job's input on the application image, which carries the lock's dependencies (D41 item
7), and `glue/` the code of a step that reads or writes governed data. `workflows/` is the activation:
the definition that starts that code on a schedule or on demand, with `code/` holding the orchestration
code its Python and Bash tasks run on the worker, never a data path, the line the CLI's manifest draws
the same way (D41). The application's slice is structure, applied by the pipeline at deploy time with no
workflow. A notebook's logic graduates as code in `src/` plus a task in `workflows/app-etl.yaml` that
calls it; the notebook itself does not graduate (6d decision due 14). What a team does with this layout,
from a space to Production, hand by hand, is [`runbooks/sagemaker-application.md`](runbooks/sagemaker-application.md).

---

### 5.1 Operating model: the `[P]`, `[D]` and `[E]` layers (D11)

The rule is **pay nothing while idle**, not **destroy everything**: most AWS resources cost nothing at
rest. That splits the environment into three layers, and every stage must say which layer each of its
resources belongs to.

**[P] Persistent — created once, never destroyed.** Free or nearly free at rest, or too slow to rebuild:
the Organization, the accounts, Control Tower, Identity Center, SCPs, Terraform state buckets, the
**VPC itself** (VPC, subnets, route tables, internet gateway, security groups, NACLs cost nothing),
Route 53 private zone, IAM roles, KMS keys, S3 data buckets, ECR repositories, budgets and alarms — and
the **SageMaker unified domain and its projects** (D26 — a DataZone V2 domain at rest bills only metadata
requests and storage; the per-project SageMaker AI domain that the `Tooling` blueprint provisions
likewise bills nothing until an app runs). The domain also holds the *catalog* — glossary, data products,
subscription decisions — which is state in rule 2's sense and settles the layer question on its own.

**[D] Dormant — kept, but powered off between sessions.** Stateful services where a rebuild is riskier
than the idle cost: the WireGuard host and the Squid proxy — D38's two hub hosts, in `production/` since
Stage 6c (2026-09-06) — and, since Stage 7 (2026-10-12), the GitLab host and its data volume
(`production/tooling/`, started and stopped by `make gitlab-up`/`gitlab-down`). `make down` stops
them, `make up` starts them, and **the hub pair has its own `make hub-up` / `make hub-down`** (D11 amended
2026-09-05): every other account's session depends on those two, so a spoke's `make up` refuses while either
is stopped. Idle cost is their EBS volumes (~USD 4.65/month) plus the Elastic IPs, which stay associated
across a stop/start (and bill while stopped) — the addresses, the host-key secret and the security groups
live in `[P]` (`production/networking/`), so they survive even if the instance is replaced. This is what
makes the Stage 7 backup/restore cycle a disaster-recovery procedure rather than a daily dependency.

**[E] Ephemeral — destroyed at the end of a session.** Everything metered by the hour and rebuildable in
minutes — **and, since 2026-09-20, one thing that is metered per query and has no off switch of its own**: a
**Redshift Serverless workgroup** (D40, Stage 5b). Its compute bills nothing while no query runs, but *nothing*
is conditional — an unclosed transaction, a connection pool's keep-alive and a cancelled query all bill — and
the service offers **no pause**: `create-workgroup` and `delete-workgroup` and nothing between them. So the
only hard guarantee is that the object does not exist, which is what `[E]` means. Its namespace stays `[P]`
because it holds the schemas, the database users and the `GRANT`s, so the pair is two slices (`warehouse/` and
`warehouse-compute/`) for rule 1's reason. Also `[E]`: interface VPC endpoints (the `egress/` slices — **no NAT gateway exists anywhere since D38**, 6c
step 5.1, 2026-09-06), the probes, the `amd64` build host, SageMaker Studio *apps* (the domain and the
spaces stay), GitLab Runners, and the Stage 13 web tier's ALB (an ALB cannot be stopped, only destroyed —
it bills ~USD 0.023/h for as long as it exists; nothing fronts GitLab itself, which terminates TLS on its
own nginx since D15 was revised). The provisioned MWAA environment (~20-30 minutes to create or delete,
and a metadata database holding state nothing else persists) is not built: D7 amended 2026-09-05 makes
**MWAA Serverless the only orchestrator**, and a serverless workflow bills nothing at rest, so the
`orchestration/` slices stay `[E]` with no idle cost and nothing to lose on a destroy.

**Where each SageMaker Unified Studio object sits** (Stage 6d step 5.3, read 2026-09-12). Three owners
share the surface — Terraform, the `Tooling` blueprint and the portal — and only the first appears in a
plan, so the layer of the other two is written here rather than inferred from a slice:

| Object | Layer | Owner | At rest | `make down` |
|---|---|---|---|---|
| the DataZone V2 domain, its project profiles and the catalog | `[P]` | `data-governance/governance/` | metadata and storage | never |
| blueprint configurations | `[P]` | the member account, by hand; immutable through `awscc` | nothing | never |
| the project and its role, `datazone_usr_role_*` | `[P]` | the `Tooling` blueprint | nothing | never |
| the D13 boundary on that role | `[P]` | `sandbox/sagemaker/` (the `sagemaker-prereqs` module) | nothing | never |
| the project's SageMaker AI domain, its `DefaultUserSettings` and the `CustomImages` attachment | `[P]` | the blueprint; the attachment by hand ([`dev-env.md`](runbooks/dev-env.md) §C6) | nothing until an app runs | never |
| the registered image, its version and app image configurations | `[P]` | `sandbox/dev-env/`, rank 49 | nothing | never |
| the Bedrock grant | `[P]` | `sandbox/bedrock/`, rank 52 | nothing | never |
| the governance project of the console's model access, its profile and Sandbox's membership | `[P]` | `data-governance/governance/` (Stage 17 decision 13) | nothing | never |
| the model provisioning and consumption roles | `[P]` | `sandbox/model-access/`, rank 52 | nothing | never |
| a model's catalog asset and environment in the governance project; a project's application inference profile of a model | `[P]` in shape | the console's *Manage*; DataZone, at a subscription's grant | nothing | never: the console's disable revokes the listing's subscriptions and unpublishes and deletes the asset (its code, read 2026-10-19); whether it deletes the environment is unread |
| the workflows grant | `[P]` | `sandbox/workflows/`, rank 56 | nothing | never |
| the CI/CD CLI's `test` deploy role, `awsds-deploy-sandbox-test`, and its ceiling | `[P]` | `sandbox/workflows/`, rank 56 (Stage 8 decision 19; applied 2026-10-16) | nothing | never |
| **a space** | **`[D]` in shape**: kept between sessions, its app stopped, its volume billing — though no `make` target starts one | the portal, by hand | **USD 0.112 per GB-month** of its volume (`UnifiedStudio:VolumeUsage.gp3`); 56 GB and USD 6.27 a month across the three spaces of 2026-09-12 | **not by default**: `scripts/down-studio-apps.py --spaces` deletes them, and the home directories with them |
| an app (JupyterLab, Code Editor) | `[E]` | the portal | instance-hours while it runs, nothing after | deleted by `scripts/down-studio-apps.py` |
| a processing or training job, a MWAA Serverless run | `[E]` | Stage 10 | nothing | nothing to delete |

**A space is not `[E]`**, although the step that asked for this table first listed it there: it holds a
user's home directory and, since [Stage 6d](stages/stage-06d-unified-studio-remainder.md) step 7, the
`RemoteAccess` flag and a project's S3 connection, so destroying it is a data loss rather than a cost
saving. It also carries **its own copy of the image version number**, so a release reaches it only
when it is moved (`dev-env.md` §B, *Moving a space*; `AWS_STATE.md` `EXC-09`).

**Rules this imposes:**

1. Terraform slices are split along these lines. `terraform destroy` of an `[E]` slice must never be able
   to reach a `[P]` resource; persistent buckets get `prevent_destroy` lifecycle blocks.
2. No state lives only inside an `[E]` resource: the stateful resource that would otherwise be `[E]` is in
   `[P]` for this reason. Deleting a Studio domain **retains** its home EFS (`RetentionPolicy` defaults to
   `Retain`), so an `[E]` domain would orphan a billing filesystem at every teardown; a domain at rest is
   free, so keeping it removes both the hazard and the rebuild. SageMaker Studio home directories remain
   **scratch** by policy — real work lives in GitLab or S3.
3. `make up` and `make down` per environment, in dependency order, and both must be tested. A rebuild that
   only works by hand is a bug.
4. Anything slow or awkward to create — Control Tower, accounts, ACM DNS validation, Identity Center —
   belongs in `[P]` by construction.
5. Keep addresses stable where something pins them: private DNS names instead of IPs, and a retained
   Elastic IP for the WireGuard host, so client configs survive a rebuild. The proxy wears its
   instance's own address, released at every stop, because no condition and no client names it
   (D39; 6g decision 1).
6. Each stage documents its teardown as well as its build, and records the measured rebuild time.
7. The layer assignment is a cost judgement and can change. If a `[D]` service turns out to be cheap to
   rebuild, demote it to `[E]`; if an `[E]` rebuild proves slow or fragile, promote it to `[D]` and pay
   the idle cost.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
