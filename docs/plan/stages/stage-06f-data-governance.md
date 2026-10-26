# Stage 6f — Data governance: the SageMaker Catalog over the governed lake

| | |
|---|---|
| **Status** | **In progress: steps 1 and 2.0 are done, 5.1 and 6.1 are read, and no access act of this stage has run.** ([log](../../log/log-stage-06f-data-governance.md)). **Decision due 1 taken 2026-10-26 by the user: shape (b), as a pilot**, the SageMaker Catalog's native flow over the lake even without LF-Tags; [D22](../decisions/D22-data-governance-account.md) and [D26](../decisions/D26-unified-studio.md) amended. **Step 11 is the pilot, written and planned the same day; 11.2 and 11.3 applied that evening** by Claude on the user's word: `data-governance/publishing/`'s 44 objects (the VPC and the blueprint prerequisites), then `LAKE_PUBLISHERS` and its three applies (the two Lake Formation seats, the `Tooling` configuration, the `lake-publishing` profile), each re-planned `No changes`. Next is 11.4, the Governance Manager's project in the portal. The pilot needs a VPC in `Data Governance`, since the managed `Tooling` template takes one with no default, and its rollback leaves the projects bucket and one Lake Formation registration, which the Data OU's deny keeps. Stage 18 7.2 ran one into `test-experimentation` on 2026-10-22, revoked the same night. 2026-09-12/13: a database and a table created in the portal, and the project path found LF-registered by the service (`GOVERNANCE.md` corrected, `DL-14` written). 2026-09-13: the table published, a data product built on it and published, and both measured to change no grant. **2026-09-18, read-only: step 1 closed** — [`./aws/catalog.py`](../../../aws/catalog.py) written and run (`CT-1`..`CT-9`), the domain's authorization read on the root domain unit, and the domain execution role's managed policy read at **v23**. What those readings settle: **the catalog road has not reached the lake** (`CT-7`: twelve SMUS grants, fourteen on 2026-10-18 with the second project's, all on project-owned objects), **nothing at the domain level restricts a direct Share** and **`ADD_TO_PROJECT_MEMBER_POOL` is open to every user by default**, so decision due 5's control belongs on the domain execution role — which also holds `AddPolicyGrant` over the policies that would carry it. Verification vi is answered ahead of its step: **a published asset shows no LF-Tag**, though this one had none to show. Two things nobody had asked about: the `Tooling` blueprint's own data source runs on a daily cron nobody wrote and has failed every run since 2026-08-24 (`EXC-11`, Lesson 17), and AI business-name generation is **on** for the Glue source, which is decision due 3's first measurement. **Five decisions remain open** and no subscription or Share has run. **Step 3.1 is read on both halves the same day, and decision due 1's recommendation moved to (c)**: shape (d) needs a custom asset type, because *managed* is a property of the asset type and `GlueTableAssetType` is one; and shape (a) **writes Lake Formation grants at creation**, over every table in the database named, before any subscription exists. **Steps 6.2, 8.1 and 9.1 are done the same day**: lineage arrives by three routes, with the MWAA-Serverless question handed to Stage 10 step 3.3; the warehouse row is in `institutional-delta.md`; and a vend adds a **domain unit**, written into Stage 14. **2026-10-18, read-only, the environment down**: 5.1 is closed from AWS's pages (generation runs on Bedrock in the Region, from the asset's metadata, and has never run here); 6.1 is answered (the two publish-time nodes link an asset to its listing and nothing else); 6.2's blueprint setting is corrected (the Glue sync is a property of each project's connections, `true` in both projects, and no Terraform declares lineage); decision due 5's DataZone half is read (each project role is a DataZone user and a contributor of its own project); and `EXC-11` counts two failing `Tooling` data sources, one per project. Decision due 3's last input is read the same day: no IAM condition key reaches business-name generation. **2026-10-20**: the manage-access role's missing Lake Formation actions, the reason every Sandbox `DataLake` environment failed, are written into `sagemaker-prereqs-v0.8.0` and applied by the user, and the two failed environments are decision due 6, taken the same night: `test-experimentation` holds an `ACTIVE` `DataLake` environment, the Glue subscription target 2.2 needs, its opt-in the manage-access role's first passing call in Sandbox. Steps 2.0-2.6 are the user's acts |
| **Prerequisites** | **None that block.** A Glue table's subscription target is a `DataLake` environment's, and every `DataLake` environment in Sandbox failed on the manage-access role's Lake Formation opt-in until `sagemaker-prereqs-v0.8.0` attached the policy that carries it (applied by the user 2026-10-20); `test-experimentation` holds an `ACTIVE` one since the same night (2.0, decision due 6), so 2.1's recommended consumer has the target. The rest is in place: Stage 5a's lake and its TBAC shares, 6a's domain and association, and two live projects: `eighth-experimentation`, holding a published asset and a published data product, and `test-experimentation`, created 2026-10-15 as D41's `test` project. Step 2.1 names the consumer: the second project exists, so a third is created only if the user prefers one |
| **Consumes** | [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D22](../decisions/D22-data-governance-account.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D28](../decisions/D28-workflow-contract.md), [D31](../decisions/D31-approver-read.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | [INT-23](../integrations.md) (new): a catalog access act becomes a Lake Formation grant in the account that owns the table |

*Read with [`docs/GOVERNANCE.md`](../../GOVERNANCE.md), the substrate this stage puts a business catalog on,
and [`docs/SMUS.md`](../../SMUS.md) §S3 item 1b. The vendor sources are the 2026-09-13 rows in
[`docs/REFERENCES.md`](../../REFERENCES.md).*

---

**Objective:** decide, by measurement, what the SageMaker Catalog governs in this estate and who acts in
it: how an access request becomes a Lake Formation grant and enters the grant register, whether the
governed lake enters the catalog and from which account, who approves and whether a direct Share
bypasses approval, what the catalog sends to generative AI, and how Production's outputs are published
without giving a deployment target a domain.

## Glue Data Catalog, Lake Formation and the SageMaker Catalog

The three systems, their scopes and what each holds here are `GOVERNANCE.md` §Catalogs. A publish
writes to the SageMaker Catalog only (measured 2026-09-13); access reaches Lake Formation when a
subscription or a Share is fulfilled, which is INT-23. The two grant forms Lake Formation carries, TBAC
with the attribute on the data and ABAC with it on the caller's session, are `GOVERNANCE.md` §Access
control's: the grants SMUS writes are the second form (`SMUS.md` §S3 1b), a fulfilment is documented as
a named-resource grant (3.2) whose condition is verification i, and Lake Formation evaluates a
principal's permissions as the union of its grants, so no tag gates either. On the catalog road the
control is the owner project's approval; on the register road, the tag and the expression.

## Production, Redshift and the domain boundary

1. **Production publishes through the lake, not through an association.** D17 keeps interactive compute
   in Sandbox, D26 keeps deployment targets out of the domain, and `DenyDataZoneEntirely` enforces it on
   `Workloads`. An association is the vendor's mechanism for an account that publishes its own catalog —
   *"publish and consume data from these AWS accounts"* — and it brings blueprint configurations and SMUS
   service roles into that account's Lake Formation administrators, the shape open question 24 found in
   Sandbox. In this design Production's pipeline writes into the governed lake through Stage 9's write
   share, so the authoritative table is in `Data Governance`'s catalog, and the publishing act belongs
   beside it (D26: *"co-locating the business catalog with the technical catalog makes every approval
   local"*). Publishing the lake needs one blueprint configuration in `Data Governance`, `Tooling`, and
   decision due 1 (2026-10-26) admits it for step 11's pilot, `US-3` admitting that one and failing on
   any other. The revision trigger on `DenyDataZoneEntirely` stands as written.
2. **Redshift and the Glue Data Catalog connect in both directions, and this stage builds neither.**
   The Sandbox warehouse exists since 2026-09-20 ([D40](../decisions/D40-redshift-warehouse.md),
   [Stage 5b](stage-05b-redshift-serverless.md), built by hand); the `RedshiftServerless` blueprint
   stays excluded by D26/D12. Redshift reads Data Catalog tables through the
   auto-mounted `awsdatacatalog` database, read-only. A Redshift namespace or cluster registered to the
   Data Catalog becomes a federated catalog: its schemas and tables are governed by Lake Formation and
   queried by Iceberg engines such as Athena and EMR. The SageMaker Catalog publishes Redshift tables and
   views as assets of their own type. Glue crawlers read S3, DynamoDB, Iceberg, Delta Lake and Hudi
   natively; Amazon Redshift, Snowflake, Aurora, MariaDB, SQL Server, MySQL, Oracle and PostgreSQL over
   JDBC; MongoDB, MongoDB Atlas and DocumentDB through the MongoDB client. Step 8 writes the institutional
   pattern.
3. **Production has its own Glue Data Catalog**, as every account does per Region. Stage 9's
   `production/data/` gives it resource links to the lake and a local outputs database; the governed
   tables stay in `Data Governance`'s catalog, written through the links. None of it depends on the
   domain.
4. **An association joins one account to one domain**, and the DataZone user guide says an account
   *"can be associated with one or more"* domains. Publishing, subscription and Share happen inside one
   domain; the documentation names no mechanism between domains. An institution therefore shares across
   business units inside one domain, through domain units (step 9), and a second domain is a separation.
   Lake Formation shares depend on no domain.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, run only after the user authorizes that action in chat |
| **[user]** | the portal and the console, where no read-only call can act |

## 0. What is already measured

- **0.1 A database created in the portal is a Glue call made by the provisioning role**, followed by
  grants to `<account-id>:IAMPrincipals` and `arn:aws:identitystore:::user/*` conditioned on the
  project's id (2026-09-13, `SMUS.md` §S3 item 1b). The call belongs to a `DataLake` environment,
  `create-datalake-database-env-<name>-<epoch ms>`, which failed on the manage-access role's opt-in until
  2026-10-20 and left its database behind (decision due 6).
- **0.2 A project's `dev/` scope is LF-registered** under the project role, hybrid access off, from the
  project's creation; `./aws/datalake.py` `DL-14` reads it.
- **0.3 A table created by upload is an external table over its upload folder**,
  `IsRegisteredWithLakeFormation: true`, created by the project role.
- **0.4 Publishing writes metadata only.** A Glue data source over the whole database (`INCLUDE *`,
  never run, `publishOnImport: false`, AI name generation on), an asset, a listing, two lineage nodes
  (three versions), a data product and its listing. No Glue or Lake Formation write, no S3 change, zero subscriptions
  (2026-09-13).
- **0.5 The portal's catalog calls run as `awsds-data-studio-domain-execution` in `Data Governance`**,
  with the Identity Center user in the session name. A preventive control over publishing or sharing
  therefore belongs on that role or in DataZone's own authorization, not in the `Interactive` OU's
  documents.
- **0.6 IAM administration does not open a project's inventory.** `InfrastructureAccess` in
  `Data Governance` is refused `GetAsset` and `GetDataProduct` by DataZone, and `search-listings` answers.
  The refusal is DataZone's project-membership check, not IAM. Since 2026-10-15 (the portal's
  `CreateProjectMembership` at 06:15Z, as the data scientist user) the Sandbox `InfrastructureAccess`
  role is a contributor of both projects through a role group profile, and its session reads `GetAsset`,
  `ListConnections` and `GetConnection` (2026-10-18), while the `Data Governance` session is refused the
  same calls.
- **0.7 No project reads the lake today.** The project role's `glue:GetDatabase` on `raw` and `curated`
  is refused for want of a Lake Formation `DESCRIBE`.
- **0.8 The approval verbs are in `GovernanceManagerAccess`** (`OwnTheDataZoneDomain`), while DataZone
  gives subscription decisions to *"asset owners"*, the owner project's members. The membership half has
  never run.
- **0.9 A Glue table's subscription target is a `DataLake` environment's** (2026-10-20): each such
  environment carries `<name>-default-target` for `GlueTableAssetType` and `GlueViewAssetType`, whose
  `manageAccessRole` reads the project role, while each `Tooling` environment's targets serve Bedrock
  models, feature groups and model package groups. `test-experimentation` holds one since 2026-10-20 (2.0).
- **0.10 The manage-access role acts in Lake Formation since 2026-10-20.** `sagemaker-prereqs-v0.8.0`
  gave it `AmazonDataZoneGlueManageAccessRolePolicy`, whose grant, revoke, registration and opt-in actions
  run on `*`; its first allowed call was 2.0's opt-in, conditioned on the project. The `DataLake`
  template keeps its database on every stack deletion (`DeletionPolicy: Retain`).

## To execute

### 1. The catalog's authorization

- **Step 1 is done, 2026-09-18, read-only** ([log](../../log/log-stage-06f-data-governance.md)).
  - **1.1 — of the policy types that apply to a domain unit, one carries a grant and one carries the
    default.** On the root domain unit: `CREATE_PROJECT`, `CREATE_DOMAIN_UNIT`, `CREATE_GLOSSARY`,
    `CREATE_FORM_TYPE` and `CREATE_ASSET_TYPE` are empty; `CREATE_PROJECT_FROM_PROJECT_PROFILE` names
    one Identity Center group; **`ADD_TO_PROJECT_MEMBER_POOL` is `allUsersGrantFilter`** — every user
    of the domain, which is DataZone's default and open question 20's axis. **Both override types are
    empty**, so the owner project's approval is the control on the catalog road; nothing at the domain
    level restricts a direct Share, which puts decision due 5 on the role or on `catalog.py`.
    `CREATE_ENVIRONMENT` and `USE_ASSET_TYPE` are refused to `InfrastructureAccess` (0.6 again) and
    read `DENIED` rather than empty.
  - **1.2 — the domain execution role's reach is one AWS-managed policy at version 23**, no inline
    policy and no boundary. It grants the whole approval cycle (`AcceptSubscriptionRequest`,
    `RejectSubscriptionRequest`, `CreateSubscriptionGrant`, `DeleteSubscriptionGrant`,
    `RevokeSubscription`), **`AddPolicyGrant` and `RemovePolicyGrant`** over the very policies 1.1
    reads, `datazone:GetEnvironmentCredentials`, `sts:SetContext` and **`q:PassRequest`** — the last
    being a door [Stage 6d](stage-06d-unified-studio-remainder.md) step 10.5 assumed shut. So a
    preventive control over publishing or sharing has one home at the identity layer, and it is a
    deny on this role; a domain-level policy will not carry it.
  - **1.3 — [`./aws/catalog.py`](../../../aws/catalog.py) exists**, `CT-1`..`CT-9`, run for the first
    time the same day: `CT-1`, `CT-2`, `CT-4`, `CT-7`, `CT-8`, `CT-9` pass; `CT-3`, `CT-5` and `CT-6`
    are notes. **`CT-7` is the check the stage exists for** and it passes: twelve grants are held by
    SMUS-managed principals and every one is on a project-owned object, so the catalog road has not
    reached the lake. **`CT-1` had to be rewritten**: `list-domains` in an associated member account
    returns the shared domain, so the draft read the association as a second domain — the
    discriminator is `managedAccountId`. Two readings the step did not ask for: a second data source
    the `Tooling` blueprint created on a daily cron nobody wrote, which has failed every run since
    2026-08-24 (`CT-6`, `EXC-11`, Lesson 17), and `enableBusinessNameGeneration: true` on the Glue
    source, which is decision due 3's first measurement. The run of 2026-10-18 passes and notes the
    same checks with fourteen SMUS grants (the second project's `default` entry and `dev/` location)
    and two `Tooling` sources of that name, one per project, 57 failed runs in all.
- **1.1 [Claude] Map DataZone's authorization model**: domain units and their authorization policies
  (project creation and membership, glossary, metadata-form and asset-type creation), owner-project
  approval, and whether any domain or unit policy restricts a direct Share. Source: the DataZone
  *Domain units and authorization policies* and *Authorization* pages.
- **1.2 [Claude] Read the domain execution role's `datazone:` reach**, and whether a deny on it or a
  DataZone policy is the only preventive place for decision due 5.
- **1.3 [Claude] Write `./aws/catalog.py`**, read-only, over `awsds-infra-data` and
  `awsds-infra-sandbox-1`: the domain's listings; subscriptions, requests and grants per listing; each
  project data source with `publishOnImport`, schedule and `enableBusinessNameGeneration`; and every Lake
  Formation grant held by a SMUS-managed principal (conditioned `IAMPrincipals`, `identitystore:::user/*`,
  project roles, the manage-access role) compared with `AWS_STATE.md`'s grant register. Checks `CT-n`,
  with 0.6 as its stated limit. Run it and record the first reading.

### 2. Subscription and Share inside Sandbox

The same-account half of INT-23, and the reading open question 24 still owes.

- **2.0 [user] Apply `sandbox/sagemaker/` at `sagemaker-prereqs-v0.8.0`, and take decision due 6;
  [Claude⚡] delete `test-experimentation`'s failed record and create its `DataLake` environment.** Done
  2026-10-20: the apply at 02:38:53Z, `d42fq38p5bkbdc` deleted at 02:50:03Z, and
  `test-experimentation-lakehouse` (`4zojr4rr6bmnww`) `ACTIVE` at 02:51:33Z, read back with its target,
  the conditioned grants and the opt-in in the trail (0.9, 0.10). The consumer project needs that
  environment before 2.2. **Still to read: the new data source's first run**, 2026-10-21 at 02:51 UTC
  (Staging's twin runs at 02:02): `CT-6` fails on a scheduled source whose completed runs all failed, and
  this one is under no exception. The run lists an empty database as the project role, through the
  conditioned grants. Staging's twin answered for its account (Stage 18, 2026-10-21): its first run, seven
  minutes past its cron minute, ended `SUCCESS` in 3 s with no asset, its `SYSTEM` session, with no
  session tag, passing `GetDatabase` and `GetTables` (the conditioned grants admitting it, inferred). A
  completed run is ingestion, billed in compute units (Cost); if the runs fail or bill, switching the
  source's schedule off is the user's call, the source then running on demand.
- **2.1 [user] Name the consumer project**: `test-experimentation` (D41's `test`, which exists), or a
  new one from the `experimentation` profile. Start no space. **The requester must not be a member of
  `eighth-experimentation`.** AWS's approval page (read 2026-10-18) approves a request at creation
  when the requester is an owner or contributor of both projects, and the two live projects share
  their owner (the data scientist user) and a contributor (the Sandbox `InfrastructureAccess` role,
  since 2026-10-15), so a request made as either identity is approved with nothing to approve, and 2.2
  would read the auto-approved path. Who requests is the user's choice. `test-experimentation` holds the
  `DataLake` environment 2.2 needs (2.0); a new consumer project needs its own, created the same way.
- **2.2 [user] Subscribe to `house-price` from the consumer project and approve it from
  `eighth-experimentation`.** [Claude] reads the grant written (principal, condition, permissions), the
  role that wrote it, what appears in the subscriber's catalog, the subscription grant's status, and the
  time from approval to grant. Across accounts the fulfilment acted as each side's project role, in sessions with
  no source identity: the publisher's, which had also created the table, granted `SELECT` to
  `IAMPrincipals` under the subscribing project's context, and the consumer's created a resource link
  (Stage 18 7.2, 2026-10-22; verification i's cross-account answer). Here the candidates are the
  publisher's role, `eighth-experimentation`'s, the manage-access role, whose Glue policy carries the
  grant actions since 2026-10-20, and the target's `manageAccessRole`, the consumer's project role; the
  approval itself runs as the domain execution role (0.5). Whether the subscribed table appears
  in the target's database, `glue_db_4zojr4rr6bmnww`, is read with it.
- **2.3 [user] Query `house-price` from the consumer project.** [Claude] reads the principal on
  `GetDataAccess`, then tests the other door: whether the consumer project role can `GetObject` the upload
  folder directly, which the managed policy's per-project path shape should refuse; and Lake Formation's own, since SMUS's
  provisioning set `AllowFullTableExternalDataAccess` `true` in Sandbox (read again 2026-10-21, Stage 18),
  under which AWS documents S3 credentials for a whole table vended to a caller holding full-table
  permission outside an integrated engine (6g 0.1), unexercised.
- **2.4 [user] Revoke the subscription.** [Claude] reads the grant's removal and whether a vended
  credential outlives it. Across accounts `revoke-subscription --no-retain-permissions` removed every
  piece in about a minute (Stage 18, 2026-10-22); which `retainPermissions` the portal sends is read too.
- **2.5 [user] Share `my-data-product` directly with the consumer project.** [Claude] reads the same set
  as 2.2, and who appears as approver.
- **2.6 [user] Subscribe to the data product.** [Claude] reads whether one approval fulfils every item.
- **2.7 [Claude⚡] Delete `eighth-experimentation`'s failed `DataLake` record, `4lrapnc3syxd74`**, on the
  user's authorization once 2.6 is read (decision due 6), and read `mydatabase`, `house-price` and its
  data source back in the same sitting.

### 3. The lake in the catalog

- **3.1's API half read 2026-09-18; the documentation half is what remains.** What the estate
  reports:
  - **(a) has its targets**: Sandbox's Glue catalog carries the resource links `raw` and `curated`,
    both pointing at the registry account's databases. Whether a DataZone Glue data source accepts a
    resource link as its `databaseName` is the vendor question this step still owes.
  - **(b) starts from nothing**: `Data Governance` holds **zero** blueprint configurations, which is
    `US-3` passing and also the whole cost of shape (b) — it would be the first object ever configured
    there, against D22's rule.
  - **(d) needs no custom asset type**: the domain offers **23 managed asset types**, including
    `GlueTableAssetType`, all owned by the domain's own project. What the reading does not settle is
    whether a Glue table can be published as an **unmanaged** asset, which is a property of the
    fulfilment rather than of the type, and is the second vendor question.
  - **The manage-access role already holds the shape 3.2 names**, on a project table: `DESCRIBE` and
    `SELECT` **with the grant option** on `mydatabase.house-price`. So the grant form (a) and (b)
    would need is one the service already writes for project-owned objects; what neither reading
    covers is the same grant on a lake table in another account.
- **3.1's documentation half read 2026-09-18, and it moves decision due 1.** Three sentences from
  the Glue data-source page ([`REFERENCES.md`](../../REFERENCES.md)) settle what the API half could
  not:
  - **(a) is mechanically possible and is not metadata-only.** A data source takes **any database by
    name** — the dropdown offers only the environment's own two, and a database the environment did
    not create *"must be typed"*, which is what a resource link would be. But **creating the data
    source writes Lake Formation grants**: read-only permissions for the environment's IAM role over
    **all the tables** in every database named. So pointing one at `raw` or `curated` is an access
    act at creation time, before any subscription, and it lands on the whole database rather than on
    a table. It also **tags the database** `DataZoneDiscoverable_${domainId}: true` (Lesson 29).
  - **(d) as this stage wrote it does not exist for a Glue table.** *"Managed assets"* is defined by
    **asset type**, not by a publisher's choice: the concepts page names Glue tables and Redshift
    tables and views, and *"for all other asset types (unmanaged assets)"* DataZone emits the
    EventBridge event instead. A Glue table published as `GlueTableAssetType` is therefore managed by
    definition, and the domain's 23 managed types include it. Publishing the lake unmanaged would
    mean a **custom asset type** standing for a table DataZone can see and has been told not to
    fulfil — which keeps the grant in the register at the price of a type nobody else's tooling
    understands, and of an asset whose schema the catalog no longer derives.
  - **What this leaves for the decision.** (a) and (b) both write named-resource grants beside the
    TBAC shares, and (a) writes them **earlier and wider** than 3.2 assumed. (d) is available only
    through a custom type. (c) — the lake kept out of the catalog, read through TBAC re-grants —
    costs discoverability and nothing else, and is the only shape that writes no grant. The
    recommendation below is re-read against that.
- **3.1 [Claude] Read the prerequisites of three shapes**, without writing:
  - **(a) a Glue data source in a Sandbox project over the resource links** `raw` and `curated`: whether
    DataZone accepts a resource link, and which grants the manage-access role would need on the target
    in `Data Governance` (every cross-account grant carries the grant option). Its IAM half exists since
    2026-10-20 (0.10);
  - **(b) a publishing configuration in `Data Governance`**: the smallest blueprint configuration that
    carries a manage-access role and no compute, which `US-3` fails today;
  - **(c) the lake kept out of the catalog**: projects read it through TBAC re-grants to project roles in
    `sandbox/data/`, the register discipline unchanged, and the catalog carries project assets only;
  - **(d) the lake published as unmanaged assets**: discovery, the request and the approval in the
    catalog, the grant in the register. DataZone fulfils a managed asset itself and emits an EventBridge
    event for the rest (`REFERENCES.md`, the concepts page), so an approval becomes a register change in
    TBAC form, reviewed by the Governance Manager. To read: whether a Glue table can be published
    unmanaged or needs a custom asset type, and from which project.
- **3.2 [Claude] Record the constraint that separates them.** The DataZone user guide says *"Access
  management for the AWS Glue Data Catalog assets using the AWS Lake Formation LF-TBAC method is not
  supported"*, and requires the manage-access role to hold `DESCRIBE` and `SELECT` with the grant option
  on each published table. Stage 18's subscription across accounts was fulfilled by the publishing
  project's role, on a table that role had created (7.2, 2026-10-22), so which role a published lake table
  needs the grant option on, the manage-access role or the publishing project's, is unread. Under (a) or
  (b), every published lake table takes a named-resource grant, the
  kind `GOVERNANCE.md` §Grants keeps for exceptions; under (d) the catalog writes none.
- **3.3 [user] Exercise (a), or (d) if 3.1 finds a table publishable unmanaged, on
  `curated.sample_trades`**, with `publishOnImport` and name generation off. [Claude] reads what the run
  imported and what a subscription would require. **Not run**: decision due 1 took neither (a) nor (d),
  and step 11 exercises (b) on `curated.trades`.
- **3.4 Decision due 1.** Taken 2026-10-26: (b), as a pilot (Decisions due).

### 4. Classification and approval in the catalog

- **4.1 is half answered, 2026-09-18: a published asset shows no LF-Tag, and this one had none to
  show.** `get-listing` on `house-price` carries `lakeFormationDetails: {}` and five forms, none
  carrying a tag; `list-lf-tags` in **Sandbox returns none** — the ontology lives in `Data Governance`
  alone — and the project table carries no assignment. So verification vi reads **no**, and the case
  that separates *the catalog does not display LF-Tags* from *this asset has none* is a **lake** table
  published under decision 1. What holds either way is the step's own alternative: `classification`
  and `layer` reach the catalog through a glossary or a required metadata form.
- **4.1 [Claude] Read whether a published Glue asset shows its LF-Tags.** If it does not, `classification`
  and `layer` need a glossary or a required metadata form in the catalog.
- **4.2 [user] Create the glossary or the form**, and [Claude] reads which project owns it: glossaries are
  *"owned by the project that creates them"* and visible to the whole domain.
- **4.3 [user] Add the Governance Manager user to the owner project and approve a request as that user.**
  [Claude] reads which policy the approval was evaluated against: `GovernanceManagerAccess`, or the domain
  execution role of 0.5. A V2 domain admits the user as an owner or a contributor alone, either acting as
  the project role in the portal (Stage 18 6.1), whose query editor reads the project's tables with no
  compute (Stage 18 7.2), past `DenyReadingTheRows` (open question 20).
- **4.4 Decision due 2.**

### 5. AI-generated metadata

- **5.1 is read, 2026-10-18, from AWS's pages** ([`REFERENCES.md`](../../REFERENCES.md); the log has the
  detail): the two `autodoc` guides, DataZone's and SageMaker Unified Studio's.
  - **Where it runs.** On Amazon Bedrock models the service chooses and does not name, and the pages say
    it inherits Bedrock's controls. `US West (Oregon)` is a supported Region and its requests use the
    in-Region endpoint: the pages route through Bedrock's cross-Region endpoint for `US East (Ohio)`
    alone (names and descriptions) and, on the Unified Studio page, for glossary-term generation in
    every supported Region. Name and description generation therefore stays in `us-west-2` (D1);
    glossary-term generation, which nothing here uses, would not.
  - **What it sends.** The asset's metadata: table and column names, optional producer-supplied
    metadata and, for a custom asset type, the relational-table form's schema. AWS's launch post says
    it does not read the table's rows unless the user puts them in the metadata. No page says whether
    sample values are ever sent.
  - **What no page says.** Whether the service's calls obey 6e's retention posture, a setting of this
    account's own Bedrock use (`none` in all 17 Regions). Bedrock's per-model retention exceptions (the
    abuse-detection page, read again 2026-10-18: Fable 5 and 5.1, and the classifier-flagged traffic of
    most OpenAI models) cannot be ruled in or out for a model nobody here chooses.
  - **Cost.** Descriptions bill by token and business names as compute, USD 1.776 per unit with 0.2
    free a month (the pricing page, read 2026-10-18); the quota is 50,000 name generations a month.
  - **Measured here.** Nothing has generated: the Glue source has no run, `CreateAsset` at publish
    carried no `predictionConfiguration`, and 90 days of the trail hold no `StartDataSourceRun`. The
    source a `DataLake` environment creates carries generation off (Staging's and `test-experimentation`'s,
    2026-10-20), while the one the 2026-09-13 publish made carries it on.
- **5.2 Decision due 3.**

### 6. Lineage

- **6.1 is answered, 2026-10-18.** `list-lineage-events` is empty (read 2026-09-18 and again
  2026-10-18) and 90 days of both trails hold no `PostLineageEvent`, so the two nodes 0.4 recorded were
  written by the publish itself and 6.2's engine list starts from zero. `GetLineageNode` is open to
  every domain user (the lineage page), so `InfrastructureAccess` in `Data Governance` reads both nodes
  where it is refused `GetAsset` (0.6). Both are `amazon.datazone.DatasetLineageNodeType`, created by
  `SYSTEM` on 2026-09-13:
  - `69dcbz6ii1j6hc` is the **asset** `house-price` (`amazon.datazone.asset/dbund4fvvvt05s`): no
    upstream node, the listing node downstream, two versions, no name and no forms.
  - `58w6xmloxbpvkg` is the **listing** (`amazon.datazone.listing/cetyru4cvy1bio`, revision 2, owned by
    `eighth-experimentation`): the asset node upstream, nothing downstream. It carries the listing, the
    dataset and the schema forms (13 columns) and a column lineage form that maps each listing column
    to the same-named asset column.

  So the publish links an asset to its listing, column by column, and nothing outside the catalog: no
  job, no run, no source table and no S3 object. The graph starts at the asset.
- **6.1 [Claude] Read the two nodes the publish created** and what they link: done above.
- **6.2 answered 2026-09-18, and the switch is not where the step assumed.** Lineage is
  OpenLineage-compatible, and it arrives by three routes: **automatic capture from AWS Glue and
  Amazon Redshift databases** when they are added to the domain; **Spark ETL job runs in AWS Glue
  v5.0 and higher**, from the console or a notebook, configured to send events to the domain; and
  **the OpenLineage-compatible APIs**, which take anything else — *"transformations in Amazon S3, AWS
  Glue, and other services"*. Two node types carry it: a **dataset node**, auto-generated with a Glue
  or Redshift icon for published assets and created by hand for everything else, and a **job (run)
  node** with its run history.
  - **The automatic half is a property of each project's connections, and the blueprint
    configuration does not carry it.** The lineage page says *"domain administrators can configure
    lineage while setting up data lake and data warehouse built-in blueprints"* and documents a
    console option on the blueprint's Region (*Import data lineage*). On this domain (read
    2026-10-18) the `DataLake` blueprint configuration holds the provisioning and manage-access role
    ARNs, the boundary, the Region and its parameters, and no lineage field; no `.tf` file in
    `terraform-live` or `terraform-modules` names lineage; and the Glue sync is
    `glueLineageSyncEnabled: true` on `project.default_lakehouse` (`LAKEHOUSE`) and `project.iam`
    (`IAM`) in both projects, with no `UpdateConnection` in 90 days of either trail. The Redshift
    connection's `lineageSync` is enabled too, on `cron(43 3 * * ? *)`: its eight daily runs since
    2026-10-11 all failed, the newest on a missing Redshift endpoint (the workgroup is `[E]` and
    down) and processing no query (`SMUS.md`). So no code change is owed to turn lineage on, and
    an empty `list-lineage-events` says that nothing emitted, not that the setting is off.
  - **What the page does not say is whether MWAA Serverless emits anything**, which is the engine
    this estate actually orchestrates with (D7). Carried into [Stage 10](stage-10-orchestration-promotion.md)
    rather than recorded only here (Lesson 34).
- **6.2 [Claude] List the engines that emit lineage events** (Glue ETL, EMR, the workflows), and write
  Stage 10's part into that stage file when it is decided (Lesson 34).

### 7. Publishing Production's outputs

- **7.1 [Claude] Revise `GOVERNANCE.md` §"The development cycle of a data product" against decision 1**:
  a project listing is an experiment with an owner project; the authoritative product is a governed
  table that Production's pipeline writes and the governance side publishes under decision 1; Production
  stays unassociated.
- **7.2 [Claude] If decision 1 publishes the lake, write the publish act into Stage 8 or 9**: the role in
  `Data Governance` that runs the data source or the listing change after a deploy, and its `datazone:`
  allow. Decision 1 publishes the lake (2026-10-26); in the pilot the Governance Manager publishes by
  hand in the portal (11.6), and this step is written once step 11's readings say what a run needs.
- **7.3 Decision due 4.**

### 8. Redshift in the institutional pattern

- **8.1 [Claude] Write the `institutional-delta.md` row**: the warehouse registered to the Glue Data
  Catalog as a federated catalog, Lake Formation over the lake and the warehouse, the SageMaker Catalog
  publishing both asset types, and data scientists reading governed schemas and writing only their own.
  None of that pattern is built: the Sandbox warehouse (D40) stands outside it.

### 9. Domain units and business units

- **9.1 [Claude] Read what a domain unit scopes** (projects, glossaries, policies, owners) and, if one unit
  per business unit fits D35, write it into Stage 14.

### 11. The pilot of shape (b): `curated.trades` published from the lake account

Decision due 1, taken 2026-10-26 as (b). The Governance Manager's project `governed-lake`, provisioned
into `Data Governance`, publishes one `internal` table, `curated.trades`; `eighth-experimentation`
subscribes from Sandbox; the Governance Manager approves in the portal and DataZone fulfils. What
DataZone writes is read before anything widens (11.11). Nothing here is applied: every apply and
every AWS write below waits for the user's word in this stage's chat, after the other sessions on the
laptop are listed and told (`CLAUDE.md`, "What the sessions share").

**Identities.** The applies and the CLI writes run as the infrastructure user, permission set
`InfrastructureAccess`: in `Data Governance` through `awsds-infra-data`, in `Sandbox Account 1` through
`awsds-infra-sandbox-1`. The portal acts are two Identity Center users, signed in to the portal with
no permission set: the Governance Manager user (`sso-group-governance-managers`) and the Data Scientist
User. One SSO login covers both profiles; the portal sign-in is per person, from a separate browser
profile for the second one (Stage 18 7.2's form).

**What the code holds** (11.1). One switch, `scripts/tfhygiene/backend.py`'s `LAKE_PUBLISHERS`, moves
three slices of `Data Governance`:

| Slice | With the switch off | With `LAKE_PUBLISHERS = ["data-governance"]` |
|---|---|---|
| `data-governance/publishing/` (new, rank 46, `[P]`) | the VPC `10.70.0.0/16` through the `vpc` module (3×2, no internet route, no peering, the two gateway endpoints, flow logs), the flow-log role, and `sagemaker-prereqs-v0.8.0` with `Tooling` alone: the provisioning and manage-access roles, the D13 boundary `awsds-data-project-boundary`, the project key `alias/awsds-data-project`, the projects bucket `awsds-data-smus-projects`, the log group | adds the `Tooling` configuration (the boundary, the two roles, the VPC and its private subnets, `S3Location`, `KmsKeyArn`) and its `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant to `CONTRIBUTOR` projects of the root domain unit; the project key's policy gains the domain execution role |
| `data-governance/governance/` | unchanged | adds the profile `lake-publishing` (`Tooling` `ON_CREATE` in `Data Governance`, `experimentation`'s six Tooling overrides and `enableSpaces` `false`, locked) and its `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to `sso-group-governance-managers` |
| `data-governance/data/` | unchanged | the Lake Formation administrators gain `awsds-data-smus-provisioning` and `awsds-data-smus-manage-access` beside `InfrastructureAccess` (`publishing.tf`); `lake_publisher_role`, null until 11.5, then grants the publishing project's role `DESCRIBE` on `curated` and `DESCRIBE` and `SELECT` with the grant option on `trades` |

**What DataZone writes, and how each slice stays consistent with it.** Stage 18 measured the shape in
Staging (its 3.3 and 7.2); the lake account's own readings are 11.4 and 11.9.

| Object | Written by | The slice that meets it | How it stays consistent |
|---|---|---|---|
| Lake Formation settings: the two SMUS seats, `AllowFullTableExternalDataAccess`, `Parameters`, the create-defaults (`PutDataLakeSettings`, a full replace) | the provisioning role, at the first `Tooling` environment | `data/` (`lakeformation.tf`) | the seats are declared before the environment (11.3); the flag is `true` in code since 2026-10-23 (Stage 9 decision 13, `TM-26`); `Parameters` 4/`TRUE` and empty defaults are what the provisioning kept in Sandbox (open question 24). `data/` re-plans `No changes` after 11.4, or the diff names what the service changed, with `DL-5` read before and after |
| the registration of `s3://awsds-data-smus-projects/<domain>/<project>/dev/` | the Tooling stack, under the project role | none: `data/` declares `raw` and `curated` alone | none needed; the Data OU denies its deregistration (11.12) |
| project-conditioned grants on the project's `dev/` location and databases, and a `default` database if the account has none | the provisioning role | none | a grant to another principal drifts no `aws_lakeformation_permissions` resource; `catalog.py` `CT-8` reads the condition |
| the publisher's grant on `curated` and `curated.trades` | Terraform, `data/publishing.tf` | `data/` | declared; the register's exception, recorded in the producer README |
| the fulfilment: `SELECT` on `curated.trades` to Sandbox's `IAMPrincipals` under `eighth-experimentation`'s context, `CROSS_ACCOUNT_VERSION` 5 in the grant | the publishing project's role, `AWSDataZone-Subscriptions` sessions | none | not Terraform's: `catalog.py` reads it into the register (decision due 2's first option) |
| a RAM share `LakeFormation-V5-*` of the lake's catalog, `database/*` and `table/*/*` to Sandbox's account | the same sessions | none: `shares.tf`'s TBAC grants own their `LakeFormation-V4-*` shares | RAM shares are in no state; `DL-7` counts one more share out. The share is a ceiling: Lake Formation's `SELECT` scopes the read |
| three statements in the lake's Data Catalog resource policy, naming Sandbox's account for table and partition reads and writes | the same sessions | none: `shares.tf` keeps the policy absent on purpose | no `aws_glue_resource_policy` exists, so nothing drifts, and `shares.tf`'s premise is false while a subscription lives: the Prerequisites page asks for `glue:ShareResource` to `ram.amazonaws.com` once an account shares through a catalog policy, read at 11.9 before any later `shares.tf` change |
| a resource link `trades` in `eighth-experimentation`'s `DataLake` database, and `DESCRIBE` on it to the project's context | `eighth-experimentation`'s role | none: `sandbox/data/` declares the persona's regrants | a DataZone-owned database, outside every state |

- **11.1 [Claude] The code, written and planned 2026-10-26** (the log). The switch off: `publishing/`
  plans 44 to add, nothing changed or destroyed; `governance/` and `data/` re-plan `No changes`. The
  switch on in the working copy and back: `publishing/` 46 to add, the configuration and its grant
  beside the 44; `governance/` 2 to add, the profile and its grant; `data/` refused at plan, *"reading
  IAM Role (awsds-data-smus-provisioning): couldn't find resource"* and the same for the manage-access
  role, the designed refusal before 11.2 creates them. Written with it, so each reads
  the pilot at the apply that makes it true (Lesson 50): `./aws/studio.py` `US-3` admits `Tooling`
  alone in `Data Governance` and `US-4` the profile `lake-publishing`; `./aws/catalog.py` `CT-7`
  reads the publisher's grant and the fulfilment's on a published table as the catalog road's, and any
  other SMUS grant on the lake as before; `./aws/datalake.py` leaves `awsds-data-smus-projects` out of
  the lake's buckets; `./aws/networking.py` `NT-1` admits the `VPC_CIDRS` row of `Data Governance`.
- **11.2 [Claude⚡] Apply `data-governance/publishing/`, the switch off**, as `awsds-infra-data`:

  ```bash
  ./scripts/gen-tfvars.py data-governance publishing && ./scripts/gen-backend-hcl.py data-governance publishing
  AWS_PROFILE=awsds-infra-data terraform -chdir=terraform-live/data-governance/publishing init -backend-config=backend.hcl -input=false
  AWS_PROFILE=awsds-infra-data terraform -chdir=terraform-live/data-governance/publishing plan -input=false -out="$HOME/tmp/6f-11-2.tfplan"
  AWS_PROFILE=awsds-infra-data terraform -chdir=terraform-live/data-governance/publishing apply -input=false "$HOME/tmp/6f-11-2.tfplan"
  ```

  A plan other than 44 to add stops the step. [Claude] reads after: the re-plan `No changes`; the VPC,
  its six subnets and no route to the gateway (`./aws/networking.py`); both roles' trusts naming
  `datazone.amazonaws.com` from this account; the bucket versioned, every public-access block on;
  `./aws/datalake.py`'s `DL-1` and `DL-2` on the five lake buckets alone.
  **Done 2026-10-26** (the log), the user's words: *"Autorizo o 11.2: apply de
  data-governance/publishing/ com LAKE_PUBLISHERS vazio, como infrastructure user, conta Data
  Governance, InfrastructureAccess (awsds-infra-data), aceitando a VPC 10.70.0.0/16."* The plan read 44
  to add at 20:05:10Z, the apply 44 added from 20:05:22Z to 20:06:53Z, the re-plan `No changes` at
  20:07:29Z. Read back: `awsds-data-vpc`, its six subnets in `usw2-az1` and `usw2-az2`, every route
  table carrying the two gateway endpoints' prefix lists alone, the gateway attached and unrouted, no
  peering, the flow log `ACTIVE`; both service roles trusting their services from this account alone;
  the boundary at `v1`; the key `Enabled`; the bucket versioned, all four public-access blocks on, SSE-KMS
  with the Bucket Key; Lake Formation's settings and the zero configurations as before the apply.
- **11.3 [Claude] The switch**: `LAKE_PUBLISHERS = ["data-governance"]`, the three tfvars regenerated,
  committed to the step's branch. **[Claude⚡] The three applies, in this order**, each from a saved plan
  and re-planned `No changes` after:
  1. `data/`: 1 to change, the settings' admin list alone. `./aws/datalake.py` before and after:
     `DL-5` 4/`TRUE`, `DL-6` no create-default, `DL-13` the required seat and two SMUS seats as a note.
     Any other attribute in the diff stops the step (INT-11).
  2. `publishing/`: the configuration and its grant added, the key's policy changed.
  3. `governance/`: the profile and its grant added, `experimentation` and the model governance project
     unchanged. A plan that destroys `awscc_datazone_project_profile.this["experimentation"]` stops it.

  [Claude] reads: `datazone list-environment-blueprint-configurations` as `awsds-infra-data` returns
  `Tooling` alone, with the boundary and both roles; `list-policy-grants` on it and on the root domain
  unit; `./aws/studio.py` `US-3` and `US-4`.
  **Done 2026-10-26** (the log), the user's words: *"Autorizo o 11.3: LAKE_PUBLISHERS =
  ["data-governance"] e os três applies na ordem data/, publishing/, governance/, como infrastructure user,
  conta Data Governance, InfrastructureAccess (awsds-infra-data)."* `data/`: 1 changed at 20:16:33Z, the
  admin list alone (+2), the other eight attributes unchanged, Lake Formation reading the three seats
  with 4/`TRUE`, the flag `true` and both default lists empty. `publishing/`: 2 added and 1 changed by
  20:18:17Z, the configuration created at 20:18:00Z with the boundary, both roles and `VpcId`,
  `Subnets`, `AZs`, `S3Location`, `KmsKeyArn`, its grant to `CONTRIBUTOR` projects of the root unit, and
  the project key's policy gaining the domain execution role and the project-role statements.
  `governance/`: 2 added by 20:20:04Z, `lake-publishing` `ENABLED` (`cc45618tw9f7yo`), `Tooling`
  `ON_CREATE` in this account with the seven overrides, and its create grant to
  `sso-group-governance-managers`, `experimentation`'s grant unchanged. Each slice re-planned
  `No changes`.
- **11.4 [user] The Governance Manager creates the project**: signed in to the portal as the Governance
  Manager user, *Create project*, profile `lake-publishing`, name `governed-lake`. Then, as its owner,
  *Members → Add members*, `Data Governance`'s `InfrastructureAccess` role as `PROJECT_CONTRIBUTOR`, so
  Claude's DataZone reads of the project pass (0.6). Claude never approves a request in it. **[Claude]
  reads**, as `awsds-infra-data`:
  - the project `SUCCESSFUL` and `Tooling` `ACTIVE`, with no SageMaker AI domain (`US-2`); a failure is
    read from the refused call and its policy's wording, and goes to 11.12;
  - the stack's resources against Stage 18 3.3's list: three roles under the boundary, the security
    group, two Glue connections, two Athena workgroups, the log group, the `dev/` registration, the
    schedule group; outside the stack, the S3 Access Grants instance and its location, and
    `AWSServiceRoleForAmazonAthena`;
  - Lake Formation's settings field by field, then `data/`'s plan: `No changes` means the full replace
    wrote only what the code declares;
  - every `lakeformation:`, `glue:` and `datazone:` call in `Data Governance`'s trail from the project's
    creation, by principal: whether the provisioning role created `default` in the lake's catalog,
    and whether either seat granted anything on `raw` or `curated`;
  - the project role's name, `datazone_usr_role_<project>_<environment>`, which 11.5 writes;
  - the `Tooling` environment's data source (`EXC-11`'s name, covered by `CT-6`).
- **11.5 [Claude⚡] The publisher's grant**: `lake_publisher_role` in `data/variables.tf` defaults to the
  role 11.4 read, committed; plan 2 to add (`DESCRIBE` on `curated`; `DESCRIBE` and `SELECT` with the
  grant option on `trades`), applied, re-planned `No changes`, `DL-5` before and after. [Claude] reads
  `lakeformation list-permissions --principal DataLakePrincipalIdentifier=<role ARN>`, and the producer
  README and the grant register gain their rows.
- **11.6 [user] The Governance Manager publishes `trades`**, in `governed-lake`: *Data sources → Create*,
  type AWS Glue, database `curated`, table selection *include* `trades`, *automated business name
  generation* off, *publish assets automatically* off, no schedule; *Run*; the asset `trades` reviewed
  and *Published*. [Claude] reads: `CreateDataSource` and `StartDataSourceRun` in the trail, with any
  Lake Formation grant written between them (3.1's documentation said a data source grants the
  environment role read on every table of the database it names); the source's `publishOnImport` and
  `enableBusinessNameGeneration` (`CT-4`, `CT-5`); the run's assets; the listing in `search-listings` from
  Sandbox; and whether the asset carries `classification=internal` anywhere in its forms (verification
  vi's lake half).
- **11.7 [Claude⚡] `eighth-experimentation`'s subscription target**, a `DataLake` environment, as
  `awsds-infra-sandbox-1`, a contributor of the project, the form 2.0 ran for `test-experimentation`:

  ```bash
  aws datazone create-environment --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier avhvbqn37ty7m8 --environment-configuration-id 40631117-4a84-42b1-b2dc-c2deef6c3d52 --environment-blueprint-identifier d8w7c3fmbsz5cg --name eighth-experimentation-lakehouse --profile awsds-infra-sandbox-1 --region us-west-2
  ```

  The failed record `4lrapnc3syxd74` stays until 2.7 (decision due 6). If DataZone refuses a second
  environment from one configuration in one project, 2.7 runs first, the user's call, with `mydatabase`
  and `house-price` read back. [Claude] reads the environment `ACTIVE`, its database
  `glue_db_<environment id>`, the target `eighth-experimentation-lakehouse-default-target` for
  `GlueTableAssetType`, the conditioned grants and the opt-in, as 2.0 read them.
- **11.8 [user] The subscription and its approval.** Signed in as the Data Scientist User, who is no
  member of `governed-lake`: search the catalog for `trades`, *Subscribe*, project
  `eighth-experimentation`, a reason. Signed in as the Governance Manager user: *Subscription requests*
  in `governed-lake`, *Approve*. The request waits for the approval because its requester is a member of
  one project alone (2.1). [Claude] reads verification vii: the `AcceptSubscriptionRequest` event, the
  role it ran as and the identity in its session name; the subscription `APPROVED` and its grant to
  `COMPLETED`, with the times.
- **11.9 [Claude] The fulfilment, read to its end**, in both accounts:
  - in `Data Governance`'s trail, every call of the publishing role's `AWSDataZone-Subscriptions`
    sessions: `ListPermissions`, `BatchGrantPermissions`, `ram:CreateResourceShare`,
    `glue:PutResourcePolicy`, and any refusal;
  - `lakeformation list-permissions` on `curated.trades` as `awsds-infra-data`: the grant's principal,
    condition and permissions;
  - `glue get-resource-policy` as `awsds-infra-data`: the statements, and whether one gives
    `glue:ShareResource` to `ram.amazonaws.com`;
  - `ram get-resource-shares --resource-owner SELF` and `list-resources` on the new share, and the same
    share among Sandbox's received ones, `ACTIVE`, with no invitation;
  - in Sandbox, the resource link in `glue_db_<environment id>` and its `DESCRIBE`, through
    `glue get-tables` and `lakeformation list-permissions` as `awsds-infra-sandbox-1`;
  - `./aws/catalog.py` (`CT-7` the catalog road's grants, `CT-8`), `./aws/datalake.py` (`DL-5`, `DL-7`,
    `DL-13`), and `data/`'s re-plan `No changes`.
- **11.10 [user] The read.** Signed in as the Data Scientist User, `eighth-experimentation`'s query editor,
  with no space:

  ```sql
  SELECT * FROM "glue_db_<environment id>"."trades" LIMIT 10;
  ```

  [Claude] reads `lakeformation:GetDataAccess` in both trails and the query's state and bytes scanned.
  The rows reached, the pilot unlocks two reads a project role could not make without a lake grant,
  each in its own stage's sitting with a space up: [Stage 9](stage-09-deployment-targets.md) 8.1's space
  half (a lake table read through the subscription, never written) and
  [6g](stage-06g-access-by-identity.md) 2.4's (an Athena query over `curated` from a Sandbox space).
- **11.11 [Claude] What DataZone wrote, before anything widens**: the log entry; the grant register's
  rows for the fulfilment, its RAM share and catalog policy, marked as DataZone's; the producer README's
  rows; `docs/SMUS.md`'s catalog section; `TM-27` read against the measurement. No second table and no
  second subscriber until then, and no `restricted` or `personal` table in `publishing.tf`'s list before
  decision due 2 rules on them.
- **11.12 The rollback**, whenever the user calls it, in this order; each write [Claude⚡] on the user's
  word, or the user's from Claude's saved plans:
  1. The subscription revoked: `revoke-subscription --no-retain-permissions`, or the portal's *Revoke*
     (whose `retainPermissions` is read); then read gone on both sides, Stage 18 8.1's way: the grant,
     the RAM share, the catalog policy back to *"Policy not found"*, the resource link.
  2. The listing unpublished, the asset and the data source deleted, by the Governance Manager in the
     portal or as the contributor.
  3. `data/`: `lake_publisher_role` back to null, 2 to destroy, `DL-5` bracketing it.
  4. `governed-lake` deleted, `delete-project --skip-deletion-check` as `awsds-infra-data`. The Tooling
     stack's `LakeFormationResourceToRegisterProjectsS3Location` has no `DeletionPolicy`, and the Data
     OU's `DenyLakeDeletionAndDeregistration` denies `lakeformation:DeregisterResource` to every
     principal, so the stack is expected to stop `DELETE_FAILED` on it. Then `cloudformation delete-stack
     --stack-name DataZone-Env-<environment id> --retain-resources
     LakeFormationResourceToRegisterProjectsS3Location` as `awsds-infra-data`, and the deletion retried.
     The registration stays, its role gone, unless the user amends the deny for that sitting (battery
     phase 4b). Outside the stack, removed by hand as Stage 18 8.1 did: the S3 Access Grants location and
     instance, the Athena service-linked role, the log group `datazone-<project>-dev` and its two
     siblings, and the `default` database if 11.4 found the provisioning created it.
  5. `LAKE_PUBLISHERS = []`, then `governance/` (the profile and its grant destroyed), `publishing/` (the
     configuration and its grant), `data/` (the two seats), each re-planned `No changes`.
  6. `publishing/` destroyed but for the projects bucket: every version and delete marker removed, the
     bucket's six resources taken out of state (`terraform state rm`), then `terraform destroy`; the key
     goes to `PendingDeletion`. The bucket stays, empty: the Data OU denies `s3:DeleteBucket`.
  7. The slice's folder and rows, the `VPC_CIDRS` row, the instruments' admissions and D22's amendment
     marked reverted, in one commit.

  `eighth-experimentation`'s `DataLake` environment stays: it is the project's subscription target, and
  its database is `Retain` at every deletion.

### 10. Close

- **10.1 [Claude]** `SMUS.md` §"SageMaker Catalog" with the object model and the measurements;
  `GOVERNANCE.md`; `AWS_STATE.md` (fulfilment grants in the register, or the rule that keeps them out);
  `POLICIES.md` if a deny lands; a decision file for each of decisions due 1, 2 and 5; `CLAUDE.md`.
- **10.2 [user]** Keep or delete the consumer project, its `DataLake` environment and the test listings.
  None has an hourly meter. Deleting the environment keeps `glue_db_4zojr4rr6bmnww` (`DeletionPolicy:
  Retain`), and `mydatabase` stands outside any environment, so a clean-up deletes each database by name
  as a Lake Formation administrator holding `DROP` on it, granted to itself first (Stage 18 8.1,
  2026-10-22); whether the environment's data source, which hangs from the `Tooling`
  connection, goes with it is unread.
- **10.3 [Claude]** The log, at the user's request.

## Verifications

| # | Question | Step |
|---|---|---|
| i | Does a fulfilled subscription grant the subscriber project role, a conditioned `IAMPrincipals` entry, or both, and which role writes it? | 2.2 |
| ii | Does a direct Share write the same grant, and does the trail show any approver? | 2.5 |
| iii | Does revocation remove the grant, and does a credential issued before it survive? | 2.4 |
| iv | Does one approval of a data product fulfil every item? | 2.6 |
| v | Does a Glue data source accept a resource link, can a Glue table be published unmanaged, and what would a subscription need in `Data Governance`? | 3.1, 3.3 |
| vi | Does a published asset show its LF-Tags? | 4.1 |
| vii | Which policy decides an approval made in the portal? | 4.3 |
| viii | Where does AI metadata generation run, and what does it send? | 5.1 |
| ix | What do the publish-time lineage nodes link? | 6.1 |
| x | Does the publishing project's first environment change any Lake Formation setting `data/` declares, and does it grant anything on `raw` or `curated`? | 11.4 |
| xi | Does a Glue data source over `curated` write a Lake Formation grant at its creation, and on which tables? | 11.6 |
| xii | Which role writes the fulfilment from the lake, and what does it add to the lake's RAM shares and Data Catalog resource policy? | 11.9 |
| xiii | Does `eighth-experimentation` read `curated.trades` through the subscription, with no space? | 11.10 |

## Decisions due

1. **How the governed lake enters the catalog**: shape (a), (b), (c) or (d) of step 3.
   **The reading of 2026-09-18 changed what each shape costs.** (a) is possible — a data source takes
   a resource link by name — but **creating it grants the environment role read on every table in the
   database**, so it is an access act at creation time, wider than a subscription and earlier than
   any approval. (b) adds D22's reversal on top of the same grants, and Stage 18 measured the rest of its price in
   `Staging` (2026-10-19 to 2026-10-22): the first `Tooling` environment seats two SMUS roles as Lake
   Formation admins by a full replace of the settings, which `data-governance/data/` declares with no
   `ignore_changes`, and turns on `AllowFullTableExternalDataAccess`, unset in `Data Governance` (6g
   0.1); a subscription across accounts shares the producer's whole catalog through RAM and writes its
   Data Catalog resource policy, which `shares.tf` keeps absent on purpose, Lake Formation's `SELECT`
   alone scoping the read. **(d) is not available for a Glue
   table as written**: *managed* is a property of the asset type, and `GlueTableAssetType` is managed,
   so unmanaged publication needs a **custom asset type** — a type whose schema the catalog does not
   derive and whose meaning no other tooling shares. (c) writes no grant at all and costs only
   discoverability in the catalog. **Recommendation: (c), with (d) as the shape to revisit** if
   discoverability of the lake turns out to matter more than keeping every lake grant in the
   register — the two are the only shapes that leave the TBAC model intact. A reading of 2026-10-17
   ([Stage 18](stage-18-staging-deployment-project.md) step 7.2) weighs on (a): the troubleshooting
   page says SageMaker Unified Studio *"does not support subscriptions to resource links"*, so
   what a data source over `raw` and `curated` publishes could not be subscribed to, which no run
   has tested. Since 2026-10-20 the manage-access role holds the IAM half of the grants (a) and (b)
   would write in Sandbox (0.10), and Sandbox's TBAC shares carry the grant option, so under (c) what
   keeps the lake out of the catalog is that nothing publishes it or points a data source at its
   resource links. `CT-7` reads that, and a narrower seat is open question 24's other half.

   **Taken 2026-10-26 by the user: (b), as a pilot** (relayed to this stage's session the same day).
   The reason is the native flow: subscription and approval in the portal grant, DataZone fulfils, and
   no Terraform apply is owed per grant. The user's complement: *"vamos priorizar a solução nativa do
   SMUS, mesmo que isso implique em não utilizar as LF-TAGS"*. So, for what enters through the catalog,
   DataZone's named-resource grants prevail over the TBAC model, and `GOVERNANCE.md` §Grants' rule that
   keeps named-resource grants for exceptions stops applying to that path; the TBAC shares stay
   whole for every reader they already reach. It reverses D22 for the pilot (its amendment): `Data
   Governance` gains a `Tooling` configuration and a publishing project. The pilot is step 11, one
   `internal` table, `curated.trades`, published by `governed-lake` and subscribed by
   `eighth-experimentation`, and what DataZone writes is read before anything widens. Stage 18's
   measurements become the plan's terms: the Lake Formation administrators are declared in `data/`
   rather than left to the service; the full-table flag is already on in the lake (`TM-26`); the RAM
   share and the catalog policy are read at 11.9 against `shares.tf`'s premise; and the grants are read
   into the register by `catalog.py`. Writing the step found a price the readings had not: the
   managed `Tooling` template takes a VPC, so `Data Governance` gains one with no route out, and the
   Data OU's deny keeps the projects bucket and one registration past a rollback (11.12).

   **What the pilot unlocks**: [Stage 9](stage-09-deployment-targets.md) 8.1's space half and
   [6g](stage-06g-access-by-identity.md) 2.4's, both a project role reading a lake table, which no
   project role could without a lake grant (0.7). **What it opens**: decisions due 2 to 5 below, each
   now about a live path, and Stage 11 decision 12, whose recommendation assumed (c).
2. **How a fulfilment grant enters the grant register**, and whether `restricted` and `personal` tables
   may be managed assets at all: register every fulfilment grant by reading it (`catalog.py`), or publish
   only `public` and `internal` as managed assets and keep the rest unmanaged, approved by the Governance
   Manager and granted by Terraform. **Live since decision 1 (2026-10-26)**: the pilot takes the first
   option for its one table, `CT-7` reading the fulfilment as the catalog road's, and the second half
   is the gate on widening: no `restricted` or `personal` table enters `data/publishing.tf`'s list until
   this decision rules on them.
3. **AI metadata generation**: on, off per data source, or denied. 5.1's readings are the inputs:
   the generation runs in `us-west-2` from the asset's metadata, bills names as compute (USD 1.776 per
   unit, 0.2 free a month) and descriptions by token, has never run here, and the Glue source the
   publish made carries the switch on, while a `DataLake` environment's source arrives with it off
   (2026-10-20). Off per data source is the source's *automated business name generation* field in
   the portal, or the `predictionConfiguration` flag at `CreateAsset`. **No IAM condition key can target
   either** (the Service Authorization Reference for DataZone and its machine-readable copy, read
   2026-10-18): DataZone defines six keys, `aws:RequestTag`, `aws:ResourceTag`, `aws:TagKeys`,
   `datazone:domainId`, `datazone:projectId` and `datazone:userId`, and no action row carries the last
   three; `CreateAsset`, `CreateAssetRevision`, `CreateDataSource`, `UpdateDataSource`,
   `StartDataSourceRun`, `StartMetadataGenerationRun`, `AcceptPredictions` and `RejectPredictions` take no
   resource type and no condition key. So "denied" can only be a deny on a whole action:
   `StartMetadataGenerationRun` refuses business names, descriptions and glossary associations together,
   since no key reads its `type`, and a deny on the four create and update actions would stop the
   publishing that carries the flag. "Off per data source" is a setting no policy enforces, which
   `catalog.py` `CT-5` reports as a note. Recommended: **off per data source on the sources over the
   governed lake until what DataZone sends to Bedrock, and under which retention, is read** (5.1 read where
   the generation runs, not what it keeps), the setting read by `CT-5` as an intention rather than a
   control (Lesson 5); not the action-level deny, which refuses descriptions and glossary associations with
   the names and leaves a data source's own run untouched. The decision stays the user's. **The pilot's
   source over `curated` follows the recommendation** (11.6): generation off, read by `CT-5`, the first
   source over the governed lake.
4. **Whether a deployment target is ever associated.** Recommended: no, as a standing association.
   Production publishes through the lake, and `DenyDataZoneEntirely` stands with its revision trigger.
   [Stage 18](stage-18-staging-deployment-project.md) associated `Staging Account` on
   2026-10-19, carved it out of `DenyDataZoneEntirely` for one measurement, unwound both at its pass 8
   on 2026-10-22, and its verdict kept D41 item 2 the same day ([D26](../decisions/D26-unified-studio.md)
   records it). The
   recommendation is about a standing association, which D26 still excludes. Decision 1's pilot
   associates no account: its project is provisioned into the domain's own account.
5. **Whether a direct Share is allowed**, and where its control lives: DataZone's authorization, a deny on
   the domain execution role, or detection by `catalog.py`. A reading of 2026-10-17
   ([Stage 17's log](../../log/log-stage-17-sandbox-machine-learning.md)) adds the project role to the
   question: v45 of its `SageMakerStudioProjectRoleMachineLearningPolicy` grants
   `datazone:CreateSubscriptionRequest`, `RevokeSubscription`, `CreateListingChangeSet`, `Get*`,
   `*Agent*` and `*DataApp*` on `*`, which the D13 boundary does not narrow, so code running as a project
   role holds the IAM half of a subscription request, a revocation and a publication. DataZone's own
   authorization is the other half, read 2026-10-18 without a call as the project role:
   - **The project role is a DataZone user.** Each `datazone_usr_role_*` has an `IAM` user profile
     (`ACTIVATED`), and in both live projects it is a `PROJECT_CONTRIBUTOR` beside the owner, the data
     scientist user, and the Sandbox `InfrastructureAccess` role's group profile.
   - **AWS's pages put the checks on membership.** Publishing needs the owner or contributor
     designation; a subscription request, membership of a project; approving, rejecting and revoking,
     membership of the owning project. A publisher may switch subscription approval off for an asset it
     owns, and every request to it is then approved at creation.
   - **The IAM half, simulated** with the Region context key (`iam simulate-principal-policy`): v45
     allows `CreateSubscriptionRequest`, `RevokeSubscription`, `CreateListingChangeSet` and `CreateAsset`
     for both project roles, and no policy of either allows `AcceptSubscriptionRequest`,
     `RejectSubscriptionRequest`, `CreateSubscriptionGrant` or `AddPolicyGrant`.
   - **So both halves admit** a project role to publish its own project's assets, with approval off if
     it chooses, and to request a subscription for its own project. They do not admit it to approve or
     to widen the domain's policies. No call as a project role appears in 90 days of either trail, so
     the call itself is unmeasured: it is a write, run from a space (the environment up) and the user's
     to authorize. Stage 18 7.2 measured more on 2026-10-22: the fulfilment's session of the producer's
     project role called `lakeformation:BatchGrantPermissions`, `ram:CreateResourceShare` and
     `glue:PutResourcePolicy`, none refused. Which statement admits them, and whether a space's session
     of the role is admitted too, letting a project grant its own tables outside any approval, is unread. The lake is outside both halves today: no lake table is published and `CT-7` reads no
     SMUS grant on it. **Decision 1's pilot brings it in**: `governed-lake`'s role holds `SELECT` with
     the grant option on `curated.trades` (11.5), and a direct Share of that asset, or a member's
     session of the role granting it outside an approval, would reach the lake; 11.9's reading of
     which statement admits the fulfilment's calls is this decision's input.
6. **The two failed `DataLake` environments, once `sandbox/sagemaker/` runs `sagemaker-prereqs-v0.8.0`.**
   Both are `CREATE_FAILED` on the manage-access role's `lakeformation:CreateLakeFormationOptIn`, hold no
   resource (`provisionedResources` null, each stack `DELETE_COMPLETE`) and bill nothing. Read
   2026-10-20 ([log](../../log/log-stage-06f-data-governance.md)):
   - **`eighth-experimentation`'s `4lrapnc3syxd74`** (`glueDbName` `mydatabase`, 2026-09-13) left
     `mydatabase`, which holds `house-price`, the asset 2.2 subscribes to. Staging's failed environment of
     Stage 18 7.2 left its database through the environment's deletion as well (no `DeleteDatabase` in its
     trail), so a deletion here is expected to leave `mydatabase`; that reading was made on an empty
     database, never on one holding a published table. The data source over `mydatabase`
     (`6kk4bknmo46o0g`, created at the publish, 2026-09-13 04:06:38Z) hangs from
     `project.default_lakehouse`, the `Tooling` environment's connection, not from the failed one.
   - **`test-experimentation`'s `d42fq38p5bkbdc`** (`test`, 2026-10-15) left nothing: the project role
     deleted `test` 16 s after the opt-in was refused, from the laptop's address, as the portal acts.
   - **The Glue subscription target is the `DataLake` environment's**, so the consumer project of 2.1
     needs one `ACTIVE` before 2.2, and the publisher does not.
   - **A new environment** adds a database `glue_db_<environment id>` under the project's
     `dev/data/catalogs/`, the project-conditioned grants, and a Glue data source over that database
     alone, daily at the minute it was created, with `publishOnImport` and business-name generation off
     (Staging's, `cron(2 2 * * ? *)`, read 2026-10-20). One named `mydatabase` would ask DataZone for a database that exists, which no
     run has read.

   The options: (a) delete both, and create one `DataLake` environment, with the default database name,
   in the consumer project 2.1 names; (b) delete both and recreate both, `eighth-experimentation`'s under
   a new database name, which gives the publisher a target and a daily data source it does not use; (c)
   leave both records and create the consumer's environment only. **Recommended: (a)**, with `mydatabase`
   and `house-price` read back right after `4lrapnc3syxd74`'s deletion. The creation is `datazone
   create-environment` with the profile's `DataLake` configuration, by the infrastructure user (a
   contributor of both projects since 2026-10-15, the path of Stage 17 1.5 and Stage 18 7.2), or the
   portal's *Create database* by the user, which names the database. Each delete and create is a write
   Claude runs only on the user's authorization, after telling the other sessions.

   **Taken 2026-10-20 by the user**, *"Vamos seguir sua recomendação ajustada"*: (a) in two steps.
   `test-experimentation`'s record is deleted and a `DataLake` environment with the default database name
   created there now, the target 2.2 needs. `eighth-experimentation`'s record stays until step 2 ends:
   deleting it buys a clean listing, and its small, unmeasured risk would fall on `house-price`, the
   asset 2.2 to 2.6 exercise. Its deletion is 2.7. Executed the same night (2.0): `d42fq38p5bkbdc`
   deleted at 02:50:03Z with no `DeleteDatabase` in the trail, and `test-experimentation-lakehouse`
   `ACTIVE` at 02:51:33Z.

## Cost

- DataZone metadata: USD 10.00 per 100,000 requests and USD 0.40 per GiB-month (`PRICING.md` §5), cents at
  this scale.
- The consumer project: its Tooling environment bills nothing hourly without an app, and step 2 starts
  none. Its `DataLake` environment (2.0) holds a Glue database, free at rest, and a data source that runs
  daily over it: ingestion, billed in compute units per completed job (USD 1.776 per unit, 0.2 free a
  month, `PRICING.md` §5), what a run over an empty database consumes unmeasured.
- AI generation, if decision 3 keeps it: descriptions at USD 0.015 per 1,000 input tokens and 0.075 per
  1,000 output tokens; business names as compute, USD 1.776 per unit with 0.2 free a month, billed per
  completed job (the pricing page, read 2026-10-18).
- Athena: USD 5.00 per TB scanned; step 2's queries scan kilobytes.
- Step 11's pilot: the project key in `Data Governance`, USD 1.00 a month while it exists (`PRICING.md`
  §2); the VPC, its subnets, route tables, security groups, gateway endpoints and the unattached
  route's gateway are free; its flow logs bill by the GB ingested, and nothing in the VPC sends traffic
  (inferred); the `Tooling` environment bills nothing without an app, and spaces are off; the data
  source runs on demand, in compute units per completed run; `eighth-experimentation`'s new `DataLake`
  environment adds a daily source like 2.0's.
- Layers: projects, environments, databases, listings, glossaries and grants are `[P]` metadata, free at
  rest. The stage creates no `[E]` resource.

## What this stage does not do

- Build a warehouse or enable the `RedshiftServerless` blueprint: Stage 5b built the Sandbox warehouse
  by hand under D40, and the blueprint stays excluded by D26 and D12.
- Grant per person: trusted identity propagation stays unadopted (open question 13).
- Decide when the crawlers run (open question 19), what expires in the projects bucket (open question 25),
  or how code reaches Production (open question 26).
- Filter rows and columns: Stage 11.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Log:
[log-stage-06f-data-governance.md](../../log/log-stage-06f-data-governance.md)*
