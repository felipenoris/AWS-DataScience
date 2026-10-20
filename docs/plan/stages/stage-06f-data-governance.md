# Stage 6f — Data governance: the SageMaker Catalog over the governed lake

| | |
|---|---|
| **Status** | **In progress: step 1 is done, 5.1 and 6.1 are read, and no access act has run.** ([log](../../log/log-stage-06f-data-governance.md)). 2026-09-12/13: a database and a table created in the portal, and the project path found LF-registered by the service (`GOVERNANCE.md` corrected, `DL-14` written). 2026-09-13: the table published, a data product built on it and published, and both measured to change no grant. **2026-09-18, read-only: step 1 closed** — [`./aws/catalog.py`](../../../aws/catalog.py) written and run (`CT-1`..`CT-9`), the domain's authorization read on the root domain unit, and the domain execution role's managed policy read at **v23**. What those readings settle: **the catalog road has not reached the lake** (`CT-7`: twelve SMUS grants, fourteen on 2026-10-18 with the second project's, all on project-owned objects), **nothing at the domain level restricts a direct Share** and **`ADD_TO_PROJECT_MEMBER_POOL` is open to every user by default**, so decision due 5's control belongs on the domain execution role — which also holds `AddPolicyGrant` over the policies that would carry it. Verification vi is answered ahead of its step: **a published asset shows no LF-Tag**, though this one had none to show. Two things nobody had asked about: the `Tooling` blueprint's own data source runs on a daily cron nobody wrote and has failed every run since 2026-08-24 (`EXC-11`, Lesson 17), and AI business-name generation is **on** for the Glue source, which is decision due 3's first measurement. **Five decisions remain open** and no subscription or Share has run. **Step 3.1 is read on both halves the same day, and decision due 1's recommendation moved to (c)**: shape (d) needs a custom asset type, because *managed* is a property of the asset type and `GlueTableAssetType` is one; and shape (a) **writes Lake Formation grants at creation**, over every table in the database named, before any subscription exists. **Steps 6.2, 8.1 and 9.1 are done the same day**: lineage arrives by three routes, with the MWAA-Serverless question handed to Stage 10 step 3.3; the warehouse row is in `institutional-delta.md`; and a vend adds a **domain unit**, written into Stage 14. **2026-10-18, read-only, the environment down**: 5.1 is closed from AWS's pages (generation runs on Bedrock in the Region, from the asset's metadata, and has never run here); 6.1 is answered (the two publish-time nodes link an asset to its listing and nothing else); 6.2's blueprint setting is corrected (the Glue sync is a property of each project's connections, `true` in both projects, and no Terraform declares lineage); decision due 5's DataZone half is read (each project role is a DataZone user and a contributor of its own project); and `EXC-11` counts two failing `Tooling` data sources, one per project. Decision due 3's last input is read the same day: no IAM condition key reaches business-name generation. **2026-10-20**: the manage-access role's missing Lake Formation actions, the reason every Sandbox `DataLake` environment failed, are written into `sagemaker-prereqs-v0.8.0` and applied by the user, and the two failed environments are decision due 6, taken the same night: `test-experimentation` holds an `ACTIVE` `DataLake` environment, the Glue subscription target 2.2 needs, its opt-in the manage-access role's first passing call in Sandbox. Steps 2.0-2.6 are the user's acts |
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
   local"*). `US-3` fails on any blueprint configuration in `Data Governance`; step 3 measures whether
   publishing the lake needs one. The revision trigger on `DenyDataZoneEntirely` stands as written.
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
  project's id (2026-09-13, `SMUS.md` §S3 item 1b).
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

- **2.0 [user] Apply `sandbox/sagemaker/` at `sagemaker-prereqs-v0.8.0`, and take decision due 6.** Done 2026-10-20:
  the apply at 02:38:53Z, and `test-experimentation-lakehouse` (`4zojr4rr6bmnww`) `ACTIVE` at 02:51:33Z.
  The consumer project needs an `ACTIVE` `DataLake` environment before 2.2: a Glue table's subscription
  target is that environment's, and each `Tooling` environment carries targets for Bedrock models,
  feature groups and model package groups alone (read 2026-10-20). [Claude] reads the environment
  `ACTIVE`, its subscription target, the conditioned grants and the manage-access role's opt-in in the
  trail.
- **2.1 [user] Name the consumer project**: `test-experimentation` (D41's `test`, which exists), or a
  new one from the `experimentation` profile. Start no space. **The requester must not be a member of
  `eighth-experimentation`.** AWS's approval page (read 2026-10-18) approves a request at creation
  when the requester is an owner or contributor of both projects, and the two live projects share
  their owner (the data scientist user) and a contributor (the Sandbox `InfrastructureAccess` role,
  since 2026-10-15), so a request made as either identity is approved with nothing to approve, and 2.2
  would read the auto-approved path. Who requests is the user's choice.
- **2.2 [user] Subscribe to `house-price` from the consumer project and approve it from
  `eighth-experimentation`.** [Claude] reads the grant written (principal, condition, permissions), the
  role that wrote it, what appears in the subscriber's catalog, the subscription grant's status, and the
  time from approval to grant.
- **2.3 [user] Query `house-price` from the consumer project.** [Claude] reads the principal on
  `GetDataAccess`, then tests the other door: whether the consumer project role can `GetObject` the upload
  folder directly, which the managed policy's per-project path shape should refuse.
- **2.4 [user] Revoke the subscription.** [Claude] reads the grant's removal and whether a vended
  credential outlives it.
- **2.5 [user] Share `my-data-product` directly with the consumer project.** [Claude] reads the same set
  as 2.2, and who appears as approver.
- **2.6 [user] Subscribe to the data product.** [Claude] reads whether one approval fulfils every item.
- **2.7 [Claude] Delete `eighth-experimentation`'s failed `DataLake` record, `4lrapnc3syxd74`**, on the
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
    in `Data Governance` (every cross-account grant carries the grant option);
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
  on each published table. Under (a) or (b), every published lake table takes a named-resource grant, the
  kind `GOVERNANCE.md` §Grants keeps for exceptions; under (d) the catalog writes none.
- **3.3 [user] Exercise (a), or (d) if 3.1 finds a table publishable unmanaged, on
  `curated.sample_trades`**, with `publishOnImport` and name generation off. [Claude] reads what the run
  imported and what a subscription would require.
- **3.4 Decision due 1.**

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
  execution role of 0.5.
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
    carried no `predictionConfiguration`, and 90 days of the trail hold no `StartDataSourceRun`.
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
  allow.
- **7.3 Decision due 4.**

### 8. Redshift in the institutional pattern

- **8.1 [Claude] Write the `institutional-delta.md` row**: the warehouse registered to the Glue Data
  Catalog as a federated catalog, Lake Formation over the lake and the warehouse, the SageMaker Catalog
  publishing both asset types, and data scientists reading governed schemas and writing only their own.
  None of that pattern is built: the Sandbox warehouse (D40) stands outside it.

### 9. Domain units and business units

- **9.1 [Claude] Read what a domain unit scopes** (projects, glossaries, policies, owners) and, if one unit
  per business unit fits D35, write it into Stage 14.

### 10. Close

- **10.1 [Claude]** `SMUS.md` §"SageMaker Catalog" with the object model and the measurements;
  `GOVERNANCE.md`; `AWS_STATE.md` (fulfilment grants in the register, or the rule that keeps them out);
  `POLICIES.md` if a deny lands; a decision file for each of decisions due 1, 2 and 5; `CLAUDE.md`.
- **10.2 [user]** Keep or delete the consumer project and the test listings. Neither has an hourly meter.
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

## Decisions due

1. **How the governed lake enters the catalog**: shape (a), (b), (c) or (d) of step 3.
   **The reading of 2026-09-18 changed what each shape costs.** (a) is possible — a data source takes
   a resource link by name — but **creating it grants the environment role read on every table in the
   database**, so it is an access act at creation time, wider than a subscription and earlier than
   any approval. (b) adds D22's reversal on top of the same grants. **(d) is not available for a Glue
   table as written**: *managed* is a property of the asset type, and `GlueTableAssetType` is managed,
   so unmanaged publication needs a **custom asset type** — a type whose schema the catalog does not
   derive and whose meaning no other tooling shares. (c) writes no grant at all and costs only
   discoverability in the catalog. **Recommendation: (c), with (d) as the shape to revisit** if
   discoverability of the lake turns out to matter more than keeping every lake grant in the
   register — the two are the only shapes that leave the TBAC model intact. A reading of 2026-10-17
   ([Stage 18](stage-18-staging-deployment-project.md) step 7.2) weighs on (a): the troubleshooting
   page says SageMaker Unified Studio *"does not support subscriptions to resource links"*, so
   what a data source over `raw` and `curated` publishes could not be subscribed to, which no run
   has tested.
2. **How a fulfilment grant enters the grant register**, and whether `restricted` and `personal` tables
   may be managed assets at all: register every fulfilment grant by reading it (`catalog.py`), or publish
   only `public` and `internal` as managed assets and keep the rest unmanaged, approved by the Governance
   Manager and granted by Terraform.
3. **AI metadata generation**: on, off per data source, or denied. 5.1's readings are the inputs:
   the generation runs in `us-west-2` from the asset's metadata, bills names as compute (USD 1.776 per
   unit, 0.2 free a month) and descriptions by token, has never run here, and the Glue source carries
   the switch on. Off per data source is the source's *automated business name generation* field in
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
   the names and leaves a data source's own run untouched. The decision stays the user's.
4. **Whether a deployment target is ever associated.** Recommended: no, as a standing association.
   Production publishes through the lake, and `DenyDataZoneEntirely` stands with its revision trigger.
   [Stage 18](stage-18-staging-deployment-project.md) (written 2026-10-17, pass 0 in progress since
   2026-10-18) associates
   `Staging Account` once, carves it out of `DenyDataZoneEntirely` for the length of one measurement
   and unwinds both at its pass 8 ([D26](../decisions/D26-unified-studio.md) records it). The
   recommendation is about a standing association, which D26 still excludes.
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
     to authorize. The lake is outside both halves today: no lake table is published (decision 1 is
     open) and `CT-7` reads no SMUS grant on it.
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
   asset 2.2 to 2.6 exercise. Its deletion is 2.7.

## Cost

- DataZone metadata: USD 10.00 per 100,000 requests and USD 0.40 per GiB-month (`PRICING.md` §5), cents at
  this scale.
- The consumer project: its Tooling environment bills nothing hourly without an app, and step 2 starts
  none. Its `DataLake` environment (2.0) holds a Glue database and a daily data source run over it,
  DataZone requests at the metadata rate above, and no standing resource.
- AI generation, if decision 3 keeps it: descriptions at USD 0.015 per 1,000 input tokens and 0.075 per
  1,000 output tokens; business names as compute, USD 1.776 per unit with 0.2 free a month, billed per
  completed job (the pricing page, read 2026-10-18).
- Athena: USD 5.00 per TB scanned; step 2's queries scan kilobytes.
- Layers: projects, listings, glossaries and grants are `[P]` metadata, free at rest. The stage creates no
  `[E]` resource.

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
