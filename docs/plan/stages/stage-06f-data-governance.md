# Stage 6f — Data governance: the SageMaker Catalog over the governed lake

| | |
|---|---|
| **Status** | **Not started as a plan; its first acts were taken by hand before it was written** ([log](../../log/log-stage-06f-data-governance.md)). 2026-09-12/13: a database and a table created in the portal, and the project path found LF-registered by the service (`GOVERNANCE.md` corrected, `DL-14` written). 2026-09-13: the table published, a data product built on it and published, and both measured to change no grant. No access act (subscription or direct Share) has run, and the decisions below are open |
| **Prerequisites** | **None that block.** Stage 5's lake and its TBAC shares, 6a's domain and association, and one live project (`eighth-experimentation`) holding a published asset and a published data product. Step 2 creates the second project it needs |
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

| | Glue Data Catalog | Lake Formation | SageMaker Catalog (DataZone V2) |
|---|---|---|---|
| Holds | databases, tables, schemas, S3 locations | grants on those objects, LF-Tags, registered locations | assets, listings, data products, glossaries, metadata forms, subscriptions, lineage nodes |
| Scope | one per account and Region | one per account and Region | the domain, across its associated accounts and Regions |
| In this estate | the lake's in `Data Governance`; each consumer's own, holding resource links | TBAC shares from `Data Governance`; the conditioned grants SMUS writes in `Sandbox` | domain `awsds-studio` in `Data Governance`; `Sandbox` the only associated account |
| Written by | Glue, the crawlers (D27), the engines, the SMUS provisioning role | Terraform (the register), the SMUS service roles | the portal, as `awsds-data-studio-domain-execution` |

A publish writes to the third column only (measured 2026-09-13). Access reaches the second column when
a subscription or a Share is fulfilled, which is INT-23.

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
2. **Redshift and the Glue Data Catalog connect in both directions, and neither is built here**
   (`RedshiftServerless` is excluded by D26/D12). Redshift reads Data Catalog tables through the
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
- **0.7 No project reads the lake today.** The project role's `glue:GetDatabase` on `raw` and `curated`
  is refused for want of a Lake Formation `DESCRIBE`.
- **0.8 The approval verbs are in `GovernanceManagerAccess`** (`OwnTheDataZoneDomain`), while DataZone
  gives subscription decisions to *"asset owners"*, the owner project's members. The membership half has
  never run.

## To execute

### 1. The catalog's authorization

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

- **2.1 [user] Create a consumer project** from the `experimentation` profile. Start no space.
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

### 3. The lake in the catalog

- **3.1 [Claude] Read the prerequisites of three shapes**, without writing:
  - **(a) a Glue data source in a Sandbox project over the resource links** `raw` and `curated`: whether
    DataZone accepts a resource link, and which grants the manage-access role would need on the target
    in `Data Governance` (every cross-account grant carries the grant option);
  - **(b) a publishing configuration in `Data Governance`**: the smallest blueprint configuration that
    carries a manage-access role and no compute, which `US-3` fails today;
  - **(c) the lake kept out of the catalog**: projects read it through TBAC re-grants to project roles in
    `sandbox/data/`, the register discipline unchanged, and the catalog carries project assets only.
- **3.2 [Claude] Record the constraint that separates them.** The DataZone user guide says *"Access
  management for the AWS Glue Data Catalog assets using the AWS Lake Formation LF-TBAC method is not
  supported"*, and requires the manage-access role to hold `DESCRIBE` and `SELECT` with the grant option
  on each published table. Under (a) or (b), every published lake table takes a named-resource grant, the
  kind `GOVERNANCE.md` §Grants keeps for exceptions.
- **3.3 [user] Exercise (a) on `curated.sample_trades` if 3.1 finds it possible**, with `publishOnImport`
  and name generation off. [Claude] reads what the run imported and what a subscription would require.
- **3.4 Decision due 1.**

### 4. Classification and approval in the catalog

- **4.1 [Claude] Read whether a published Glue asset shows its LF-Tags.** If it does not, `classification`
  and `layer` need a glossary or a required metadata form in the catalog.
- **4.2 [user] Create the glossary or the form**, and [Claude] reads which project owns it: glossaries are
  *"owned by the project that creates them"* and visible to the whole domain.
- **4.3 [user] Add the Governance Manager user to the owner project and approve a request as that user.**
  [Claude] reads which policy the approval was evaluated against: `GovernanceManagerAccess`, or the domain
  execution role of 0.5.
- **4.4 Decision due 2.**

### 5. AI-generated metadata

- **5.1 [Claude] Read where business-name and description generation run**, what they send (table and
  column names, sample values), and the rate already in `PRICING.md` §5 (AI recommendations, USD 0.015
  input and 0.075 output per 1,000 tokens). Compare with 6e's retention posture and D1.
- **5.2 Decision due 3.**

### 6. Lineage

- **6.1 [Claude] Read the two nodes the publish created** and what they link.
- **6.2 [Claude] List the engines that emit lineage events** (Glue ETL, EMR, the workflows), and write
  Stage 10's part into that stage file when it is decided (Lesson 34).

### 7. Publishing Production's outputs

- **7.1 [Claude] Write `GOVERNANCE.md` §"Business catalog"**: a project listing is an experiment with an
  owner project; the authoritative product is a governed table that Production's pipeline writes and the
  governance side publishes under decision 1; Production stays unassociated.
- **7.2 [Claude] If decision 1 publishes the lake, write the publish act into Stage 8 or 9**: the role in
  `Data Governance` that runs the data source or the listing change after a deploy, and its `datazone:`
  allow.
- **7.3 Decision due 4.**

### 8. Redshift in the institutional pattern

- **8.1 [Claude] Write the `institutional-delta.md` row**: the warehouse registered to the Glue Data
  Catalog as a federated catalog, Lake Formation over the lake and the warehouse, the SageMaker Catalog
  publishing both asset types, and data scientists reading governed schemas and writing only their own.
  Nothing is built.

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
| v | Does a Glue data source accept a resource link, and what would a subscription need in `Data Governance`? | 3.1, 3.3 |
| vi | Does a published asset show its LF-Tags? | 4.1 |
| vii | Which policy decides an approval made in the portal? | 4.3 |
| viii | Where does AI metadata generation run, and what does it send? | 5.1 |
| ix | What do the publish-time lineage nodes link? | 6.1 |

## Decisions due

1. **How the governed lake enters the catalog**: shape (a), (b) or (c) of step 3. Provisional
   recommendation: (c) until 2.2 and 3.1 are read, because (a) and (b) both put named-resource grants beside
   the TBAC shares, and (b) also reverses D22's rule that nothing is configured in `Data Governance`.
2. **How a fulfilment grant enters the grant register**, and whether `restricted` and `personal` tables
   may be managed assets at all: register every fulfilment grant by reading it (`catalog.py`), or publish
   only `public` and `internal` as managed assets and keep the rest unmanaged, approved by the Governance
   Manager and granted by Terraform.
3. **AI metadata generation**: on, off per data source, or denied.
4. **Whether a deployment target is ever associated.** Recommended: no. Production publishes through the
   lake, and `DenyDataZoneEntirely` stands with its revision trigger.
5. **Whether a direct Share is allowed**, and where its control lives: DataZone's authorization, a deny on
   the domain execution role, or detection by `catalog.py`.

## Cost

- DataZone metadata: USD 10.00 per 100,000 requests and USD 0.40 per GiB-month (`PRICING.md` §5), cents at
  this scale.
- The consumer project: its Tooling environment bills nothing hourly without an app, and step 2 starts
  none.
- AI recommendations, if decision 3 keeps them: USD 0.015 input and 0.075 output per 1,000 tokens.
- Athena: USD 5.00 per TB scanned; step 2's queries scan kilobytes.
- Layers: projects, listings, glossaries and grants are `[P]` metadata, free at rest. The stage creates no
  `[E]` resource.

## What this stage does not do

- Build Redshift (D26, D12).
- Grant per person: trusted identity propagation stays unadopted (open question 13).
- Decide when the crawlers run (open question 19), what expires in the projects bucket (open question 25),
  or how code reaches Production (open question 26).
- Filter rows and columns: Stage 11.

---

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md) · Log:
[log-stage-06f-data-governance.md](../../log/log-stage-06f-data-governance.md)*
