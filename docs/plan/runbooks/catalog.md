# Runbook — the SageMaker Catalog: assets, data products, sharing and lineage

| | |
|---|---|
| **Scope** | How the catalog of the domain `awsds-studio` is configured and used: the ways an asset comes to exist in a project's inventory, the business metadata a member adds to it, a data product, the publication of a listing, a subscription or a Share between projects and its revocation, and the lineage graph with the events that feed it, dbt's among them. The model stays in [`GOVERNANCE.md`](../../GOVERNANCE.md) (the three catalogs, the two roads into a table, the LF-Tags) and the mechanism in [`SMUS.md`](../../SMUS.md) ("The catalog surface"). An application's `publish` task is [`sagemaker-application.md`](sagemaker-application.md)'s, a promotion sitting is [`promotion.md`](promotion.md)'s, and the lake's Terraform grants are indexed in [`terraform-live/data-governance/data/README.md`](../../../terraform-live/data-governance/data/README.md) |
| **Operator** | The **project member**, an Identity Center user who is Owner or Contributor of a project, in the portal: the data scientist in a Sandbox project, the Governance Manager in `governed-lake`. The **infrastructure user** (`InfrastructureAccess`, the `awsds-infra-*` profiles), who reads with `./aws/catalog.py` and the CLI and writes the domain unit's grants and the lake's publishing grant in Terraform. An **application's tasks**, as the project role of the project the CI/CD CLI deployed them into |
| **The rules** | **A publish writes to the SageMaker Catalog alone**: no Glue, Lake Formation or S3 write, and no LF-Tag (`SUP-191`, `SUP-192`). **A table is reached by one of two roads** (`GOVERNANCE.md`, "The catalog road"): a subscription or a Share that DataZone fulfils, whose record is DataZone's subscription; or a grant Terraform writes, recorded in [`AWS_STATE.md`](../../AWS_STATE.md)'s grant register. **DataZone fulfils by name and reads no LF-Tag**, so the lake lists no table that holds a restricted or personal column (`CT-12`). **No source publishes on import, and no source over the lake generates names** (`CT-4`, `CT-5`). **Lineage is cooperative**: a graph holds what an engine or a client posted and what the catalog's own acts wrote, and the portal draws one only from an asset |
| **How a fact is marked** | *Measured*, with its date and the record that holds it (a stage's step or verification, a log, a `SUP-nnn`): it ran in this estate. *Read*, with its date: it was read in AWS's pages, in released code or in a policy, and nothing here ran it. *Unmeasured*: no record in this estate holds it. *Simulated*: Stage 20's runs against simulated services on a host outside this estate (its 0.8 and 0.16). A phrase in italics and quotation marks is an API's or a log's own wording, or AWS's |
| **The picture around it** | [Stage 6f](../stages/stage-06f-data-governance.md), the lake's publication; [Stage 18](../stages/stage-18-staging-deployment-project.md), a subscription across accounts and a Glue job's lineage; [Stage 19](../stages/stage-19-smus-native-data-product.md), a project's table as a data product; [Stage 20](../stages/stage-20-dbt-lineage.md), dbt's lineage; [Stage 21](../stages/stage-21-redshift-s3-data-products.md), a Redshift table, the namespace in the Glue Data Catalog and an S3 Object Collection as products. This file cites their steps, decisions and verifications by number, and their logs hold the runs. A platform behaviour by its id: [`AWS_SUPPLEMENT.md`](../../AWS_SUPPLEMENT.md); a data-leakage channel: [`threat-model.md`](../threat-model.md); an acronym: [`GLOSSARY.md`](../../GLOSSARY.md) |
| **Written** | 2026-11-17, Stage 20 steps 1.5 and 1.6, from those stages' records and from AWS's pages read again that day (the table that closes §O); no AWS call was made for it. The portal was not re-read on 2026-11-17: the paths below are the guide's of that day, beside the portal as read on 2026-11-14, and the re-reading is the user's portal act. §L holds no reading of dbt in this estate: Stage 20's passes 2 and 3 take them, and its step 6.2 writes them here |

| Section | Audience | What it holds |
|---|---|---|
| [§O](#o-the-pieces) | both | the domain and its projects, the three catalogs, the catalog's objects, who may do what by designation and by domain unit, the portal's menus, AWS's pages behind this file |
| [§A](#a-assets) | the project member | the ways an asset comes to exist, the inventory and a revision, the identifier an asset carries, what a subscriber's source imports, the order a deletion takes |
| [§M](#m-business-metadata) | the project member | names, descriptions and the README; generated names and the switch that keeps them off; glossaries; metadata forms and the rule that requires one |
| [§P](#p-data-products) | the project member | a data product: building and publishing one, its name, what one request gives, the CI/CD CLI carrying one |
| [§F](#f-the-publication-flow) | the project member | from a table to a listing, act by act; the house's `publish` task; who publishes; the approval switch; what publishing writes; unpublishing |
| [§S](#s-sharing-between-projects) | both | a subscription from request to grant, in one account and across accounts; filters; the Share; the revocation; what the catalog does not do; the controls around it |
| [§L](#l-lineage) | both | the capture mechanisms, an event, the nodes and their names, a Glue job's settings, the dbt case and a run past the worker's hour, other adapters' names, dbt's docs site, reading and deleting, the limits and the failures |
| [§V](#v-the-instruments) | the infrastructure user | `./aws/catalog.py`, the CLI's reads object by object, the trail each act lands in |

---

## O. The pieces

### The domain and its projects

The domain is `awsds-studio` (`dzd-d8yrvx1ko7im6o`), a `V2` Identity Center domain in Data Governance
([D26](../decisions/D26-unified-studio.md); [`SMUS.md`](../../SMUS.md), "Domain"). Sandbox is associated
through the domain's RAM share, created 2026-08-21; Staging and Production since 2026-11-11, by
`ram:AssociateResourceShare` (`SUP-349`). A project lives in one account, which holds its environments,
its project role and its Glue databases. The domain listed 24 managed blueprints and 24 managed asset types
on 2026-10-28 (Stage 19 0.8).

| Project | Account | Its part in the records |
|---|---|---|
| `eighth-experimentation` (`avhvbqn37ty7m8`) | Sandbox | published `house-price` (2026-09-13); subscribed to the lake's `curated.trades` (6f 11.8, 2026-10-26); ran `app-etl`'s pass 1 and listed `trades-notional` (Stage 19, 2026-11-10 to 2026-11-14, retired 2026-11-14); owns the form type `classification`; Stage 20's `app-dbt` is deployed into it |
| `test-experimentation` (`4gqfau9xuo6e4w`) | Sandbox | the consumer of Stage 19 pass 2 (2026-11-14) |
| `app-etl-dev` (`ceweti7jbiu1hs`) | Sandbox | `app-etl`'s `dev` project since 2026-11-14; `trades_notional` curated there (Stage 19 steps 15 and 17, 2026-11-15); its data product deleted 2026-11-16 (Stage 19 decision 26 (b)) |
| `governed-lake` (`3j4l4xmvz7fggg`) | Data Governance | lists `curated.trades` (6f 11.4 to 11.6, 2026-10-26) |
| `deploy-staging` (`5ido8bej1zoeq8`) | Staging | Staging's deployment project (2026-11-11); its asset `as6m73yp8shr80` stays unlisted (Stage 19 decisions 14 and 19 (c)) |
| `deploy-production` (`d7qcazihvr3s7k`) | Production | Production's deployment project (2026-11-11); lists `trades_notional` (`5hpftif3nnoj2o`) over the asset `da1fycta6l71n4` |

### The catalogs

Three catalogs decide three different things ([`GOVERNANCE.md`](../../GOVERNANCE.md), "Catalogs"). The
Glue Data Catalog holds the technical metadata: a database, a table, its schema and its location. Lake
Formation decides who reads a table. The SageMaker Catalog, DataZone's layer, holds the business metadata
and the access acts: assets, listings, data products, subscriptions and the lineage graph. A data source
copies a Glue database's technical metadata into a project's inventory; a fulfilment writes a Lake
Formation grant; a publish writes to the SageMaker Catalog alone (measured 2026-09-13 and 2026-10-26,
`SUP-191`).

### The catalog's objects

| Object | What it is | What creates it here |
|---|---|---|
| Asset | a project's record of a table or another object, in the project's inventory, which only the project's members see | a source's run (measured, §A); the portal's *Publish to Catalog* before the 2026-10-20 redesign (measured, `SUP-191`); a person by hand (unmeasured) |
| Revision | each edit of an asset's business or technical metadata, by a person, a source's run (`SYSTEM`) or an API call | DataZone (measured, Stage 19 iv) |
| Listing | a published revision of an asset or a data product, which every domain user can find | *Publish asset* or `CreateListingChangeSet` (measured, §F) |
| Data product | named assets published and subscribed as one listing | a member in the portal (measured, §P); Production's `publish` task (measured 2026-11-22, release G) |
| Data source | the import of a Glue database's or a Redshift schema's tables into an inventory, on a schedule or on demand | the `DataLake` environment of *Create database* or of `create-environment` (measured, `SUP-184`, Stage 19 xix); a member's *Create* (read) |
| Subscription | a project's access to a listing: a request, its approval, a grant per asset to a target | a member's request (measured, §S); an owner's Share (measured, `SUP-362`) |
| Metadata form type | a typed set of fields attached to an asset or a column | a member of its owning project, under the domain unit's `CREATE_FORM_TYPE` (measured, `SUP-344`) |
| Glossary and term | a vocabulary attached to assets and columns | a member, under `CREATE_GLOSSARY` (none created) |
| Lineage node | a dataset, a job or a job run, versioned by the events that touch it | DataZone, from a posted event or a catalog act (measured, §L) |

### Who may do what

**By designation.** A V2 domain admits two project designations, Owner (`PROJECT_OWNER`) and Contributor
(`PROJECT_CONTRIBUTOR`), and refuses `PROJECT_CATALOG_VIEWER`, `PROJECT_CATALOG_CONSUMER` and
`PROJECT_CATALOG_STEWARD`: *"Project member with designation PROJECT_CATALOG_VIEWER cannot be added to
project in V2 domain"* (measured 2026-10-20, Stage 18 6.1; `SUP-161`). Both admitted designations work on
the project's credentials, so no designation gives a person a view with no write. Member management is the
Owner's: a Contributor's `DeleteProjectMembership` was refused, *"DesignationPolicy does not allow access."*
(measured 2026-11-14, `SUP-157`). A custom designation's portal acts are unmeasured; its policy names
action groups, never individual actions (`SUP-384`). The domain's RAM share moved to version 13 of its
managed permission on 2026-11-19, and the associated accounts read the designations since; it moved to
version 14 on 2026-11-21, and they read the project profiles since (`SUP-360`).
Stage 19 decision 15 (d), a custom designation for Production's approver, was taken on 2026-11-17, and its
designation `subscription-approver` was created on 2026-11-19, assigned to no member yet. The release notes
of 2026-11-12 add a layout per designation, which they call presentation only (read 2026-11-17).

**By AWS's pages** (read 2026-11-17). Curating, publishing and unpublishing an asset take Owner or
Contributor of its project (the curation page). Requesting a subscription takes membership of the
requesting project (the subscription page). Approving, rejecting and revoking take membership of the owning
project (the approval and revocation pages).

**By domain unit.** The root unit's policies, read 2026-09-18 (6f 1.1): `CREATE_GLOSSARY`,
`CREATE_FORM_TYPE` and `CREATE_ASSET_TYPE` held no grant, `ADD_TO_PROJECT_MEMBER_POOL` admitted every user,
and no override grant existed. Since then
[`governance/grants.tf`](../../../terraform-live/data-governance/governance/grants.tf) grants
`CREATE_FORM_TYPE` to the owners of each project in `form_type_owners`, `eighth-experimentation`'s (applied
2026-11-10 00:36 UTC), and the three create grants to each project in `catalog_import_projects`, the
deployment projects, whose CLI import checks them first (`SUP-351`). `CT-9` fails on an override grant.

**The roles behind an act.**

- A person's catalog act in the portal runs as the domain execution role `awsds-data-studio-domain-execution`
  in Data Governance, the Identity Center user in the session name (6f 0.5). Its one managed policy,
  `SageMakerStudioDomainExecutionRolePolicy`, grants the whole approval cycle (read at version 23, 6f 1.2);
  version 27 was read 2026-11-14 ([`upstream-releases.md`](../upstream-releases.md)).
- A project role may read, search, publish, request and revoke: `SageMakerStudioProjectRoleMachineLearningPolicy`
  v47 grants `datazone:Get*`, `List*`, `Search*`, `CreateAsset*`, `CreateListingChangeSet`,
  `CreateSubscriptionRequest` and `RevokeSubscription` on `*`, and no managed policy on the role grants
  `StartDataSourceRun` (read 2026-11-08, Stage 19 1.1; `SMUS.md`). DataZone refuses `ListDomains` to a
  project role that IAM allows (measured 2026-10-26, `SUP-162`).
- Production's deployment project role holds the house grant `awsds-prod-workflows`
  ([`workflows.tf`](../../../terraform-live/production/studio/workflows.tf)): the source's start for its
  `publish` task, in Production alone since 2026-11-15 (Stage 19 decision 17), and `CreateDataProduct` with
  `CreateDataProductRevision`, statement `CreateTheProductsDataProductInTheProjectsDomain`, applied
  2026-11-17 ([`promotion.md`](promotion.md) §N.8.5 step 3). Each target's deploy role holds the start for
  the CLI's second import (Stage 19 decision 25; `CT-13`).
- Membership opens a project's inventory, and IAM does not: Data Governance's `InfrastructureAccess` is
  refused `GetAsset` and `GetDataProduct`, while Sandbox's, a Contributor of `eighth-experimentation` and
  `test-experimentation` since 2026-10-15, reads `GetAsset` (6f 0.6). A non-member reads a project's name, members, environments and data
  sources (measured 2026-11-11 and 2026-11-16, `SUP-157`).

### The portal's menus

The catalog's items moved three times, by the release notes (read 2026-11-17, newest entry 2026-11-12):

| Date | What moved |
|---|---|
| 2026-09-17 | a *Discover* landing page for Identity Center domains; *Browse catalog* deprecated; metadata forms, glossaries and asset types under *Manage* |
| 2026-10-08 | the old navigation removed; the catalog, glossaries, metadata forms and every domain management item of *Govern* under *Manage* |
| 2026-10-20 | the catalog browsed from inside a project only; incoming requests on a page of *Manage*, outgoing ones under *Discover → My subscriptions*; one *Catalog scope* filter on the *Assets* page (*Owned by this project*, the default; *Published by this project*; *Subscribed*; *Entire catalog*); *Query in Athena* and *Query in Redshift* one *Query* action; *Edit* and the *My subscription* tab gone from an asset's page; asset types under *Catalog management → Custom asset types*; associated accounts and domain users under *Domain management*; domain units and blueprints on pages of their own; the project profile page removed |

The entries of 2026-10-15 (the same landing page for IAM domains), 2026-11-03 and 2026-11-09 (Workday
connections) and 2026-11-12 (the designations' layout) move no catalog item of this domain.

The portal as read on 2026-11-14, as the Data Scientist User (Stage 19's log):
*Manage → Catalog management* lists *Assets*, *Subscription requests*, *Data sources*, *Metadata forms*,
*Business glossaries* and *Custom asset types*. An asset's page is
`/projects/<project>/catalog/assets/asset/<id>`, with the tabs *Overview*, *Schema*, *Asset filter*,
*Preview data*, *Lineage*, *Data profile*, *Data quality* and *Subscriptions*; the curation page of
2026-11-17 adds *History*. The paths in §A to §S are the guide's of 2026-11-17. The user re-reads them in
the portal, as a member of a Sandbox project, and a difference goes into this file with its date.

### AWS's pages behind this file

| Short name | Page | Read |
|---|---|---|
| the release notes | [SageMaker Unified Studio release notes](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/release-notes.html) | 2026-11-17 |
| the curation page | [Manage inventory and curate assets](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/update-metadata.html) | 2026-11-17 |
| the data source page | [Create a data source in the project catalog](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/create-data-source.html) | 2026-11-17 |
| DataZone's Glue source page | [DataZone: a data source for the Glue Data Catalog](https://docs.aws.amazon.com/datazone/latest/userguide/create-glue-data-source.html) | 2026-09-18 (6f 3.1) |
| the page on an asset by hand | [Create an asset manually](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/create-data-asset-manually.html) | 2026-11-16; on 2026-11-17 it answered its title alone |
| the forms page | [Standardize metadata using metadata forms](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/standardize-metadata-forms.html) | 2026-11-17 |
| the metadata rules page | [Metadata rules for publishing](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/metadata-rules-publishing.html) | 2026-11-08 |
| the glossaries page | [Create and manage business glossaries](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/manage-business-glossaries.html) | 2026-11-17 |
| the product pages | [Create](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/create-new-data-product.html) and [publish](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/publish-data-product.html) a data product | 2026-11-17 |
| the products overview and republication pages | [Data products](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/data-products.html), [Republish a data product](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/republish-data-product.html) | 2026-10-28 |
| the subscription page | [Request subscription to assets](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/subscribe-to-data-assets-managed.html) | 2026-11-17 |
| the approval page | [Approve or reject a subscription request](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/approve-reject-subscription-request.html) | 2026-11-17 |
| the revocation page | [Revoke an existing subscription](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/revoke-subscription.html) | 2026-11-17 |
| the fulfilment pages | [a Glue asset](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/grant-access-to-glue-asset.html), [a Redshift asset](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/grant-access-to-redshift-asset.html), [an unmanaged asset](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/grant-access-to-unmanaged-asset.html), [the troubleshooting page](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/troubleshooting-issues.html) | 2026-10-28; the first three again 2026-11-17 |
| the S3 pages | [Amazon S3 data](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/data-s3.html), [Sharing Amazon S3 data](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/data-s3-publish.html) | 2026-11-17 |
| the subscription target's reference | [`CreateSubscriptionTarget`](https://docs.aws.amazon.com/datazone/latest/APIReference/API_CreateSubscriptionTarget.html), [`SubscriptionTargetForm`](https://docs.aws.amazon.com/datazone/latest/APIReference/API_SubscriptionTargetForm.html) | 2026-11-17 |
| the filters page | [Approve with row and column filters](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/grant-access-with-filters.html) | 2026-10-27 |
| the lineage pages | [the support matrix](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-support-matrix.html), [lineage support](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-support.html), [OpenLineage](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-what-is-openlineage.html), [capture from tools](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-automate-capture-from-tools.html), [capture from data connections](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-automate-capture-from-data-connections.html), [the `sourceIdentifier` attribute](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-sourceIdentifier-attribute.html), [linking nodes](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-linking-nodes.html), [permissions](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-permissions.html), [authorization](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-authorization.html), [the APIs](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-data-lineage-apis.html), [troubleshooting](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-lineage-troubleshooting.html) | 2026-11-16 |
| the graph page | [Visualizing data lineage in IdC mode](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/datazone-visualizing-data-lineage-idc-mode.html) | 2026-11-17 |

[`REFERENCES.md`](../../REFERENCES.md) holds each with what it supported. dbt's, OpenLineage's and the
MWAA Serverless guide's pages are named where §L uses them.

---

## A. Assets

An asset in a project's inventory is visible to the project's members alone until it is published (the
curation page, read 2026-11-17). The ways it comes to exist follow.

### A project database and its source

The portal's *Create database* deploys a `DataLake` environment named
`create-datalake-database-env-<name>-<epoch ms>` (measured 2026-09-13 to 2026-11-14, `SUP-184`):

- the provisioning role creates the Glue database, located at the project's `dev/data/catalogs/`, with
  `CreateTableDefaultPermissions` empty; the stack keeps it (`Retain`) when the stack is deleted;
- Lake Formation grants follow within eight seconds, to `IAMPrincipals` under the project's
  `context.datazone.projectId` and to the manage-access role: `CREATE_TABLE`, `DESCRIBE` and `DROP` on the
  database, and `ALTER`, `DELETE`, `DESCRIBE`, `DROP`, `INSERT` and `SELECT` on its tables (read
  2026-10-28, Stage 19 question 1);
- a daily Glue data source over the database, scheduled at the minute of creation, which names no
  environment (`environmentId` null) and hangs from `project.default_lakehouse`, the `Tooling`
  environment's connection. What the environment's delete does to the source is unread.

A project's first `ACTIVE` `DataLake` environment carries `<environment>-default-target`, whichever path
created it, and a later one carries none, the portal's or one created by API,
`create-environment … --user-parameters name=glueDbName,value=<name>` (read 2026-11-19 across four
projects, `SUP-184`; Stage 19 xix measured a first one on 2026-11-11). The project's own default
`DataLake` environment holds the target a subscription lands on (§S).

A source's run is a `SYSTEM` session of the project role calling `glue:GetDatabase`, `GetTables` and
`lakeformation:GetResourceLFTags` (measured, Stage 18 7.2 and Stage 19 0.2). A run over `app_etl` with
`INCLUDE *` added the database's one table (`added: 1`) and later runs read `updated: 1`; with
`publishOnImport` false the asset stayed unlisted 32 minutes, until the task's first change set
(measured 2026-11-10, Stage 19 iii). Stage 18's first scheduled run started 7 minutes after its hour and
took 3 s (measured 2026-10-21). A member starts a run with *Run* on the source's *Data source runs* tab
(the data source page, read 2026-11-17); a project role cannot, except where a house grant gives it the
start (§O).

### A source over another Glue database

The data source page (read 2026-11-17): *Manage → Catalog management → Data sources → Create*, four steps.

1. *Define source*: a name; the type *AWS Glue (Lakehouse)* or *Amazon Redshift*, fixed once created; for
   Glue, the connection (`project.default_lakehouse` by default), an optional *Import data lineage*, the
   catalog, a database typed or picked from the suggestions, and include and exclude rules with `*`.
2. *Add details*: *Publish assets to the Catalog*, yes or no; *Automated business name generation*; for
   Glue, the import of Glue's data quality results; forms applied to every asset the source creates.
3. *Set up schedule*: on demand, or days, hour, minute and time zone.
4. *Review*, then *Create data source*.

DataZone's Glue source page (read 2026-09-18, 6f 3.1) offered in its dropdown only the environment's own
databases and said any other *"must be typed"*. The same page said that creating the source writes Lake
Formation read grants on every table of every database it names, to the environment's role, and tags the
database `DataZoneDiscoverable_${domainId}: true`. Measured otherwise for one way of creating it: the portal's
*Publish to Catalog* created a source over `curated` with no Glue or Lake Formation write after it
(2026-10-26, 6f 11.6; `SUP-191`). Whether a source created on the *Data sources* page writes those grants
is unmeasured.

### A Redshift source

The data source page (read 2026-11-17): a Redshift connection such as `project.redshift`, a database, a
schema, include rules alone, and an *Import data lineage* that needs a connection authenticated by an
Amazon Redshift secret. A Redshift asset is published only when both clusters meet Redshift data sharing's
requirements (the curation page). No record in this estate holds a Redshift data source; unmeasured.

### An S3 Object Collection

On a folder of the project's bucket in the portal's S3 browser, *Actions → Publish to Catalog* opens
*Publish asset*, whose one choice is *Subscription approval*, *Required* or *Not required*: no name,
description or form, and no data source is created. The asset takes the folder's name, the type
`amazon.datazone.S3ObjectCollectionAssetType`, an `externalIdentifier` that is the project id followed by
the prefix's ARN with no separator, and the forms `S3ObjectCollectionForm` (`bucketName` empty,
`bucketArn` the prefix's ARN, the connection `project.s3_default_folder` with the project's S3 Access
Grants location and `registerS3AccessGrantLocation` true) and `SubscriptionTermsForm`. A description and
a form are added after the publish, then *Re-publish asset* (measured 2026-11-23, Stage 21 5.2;
`SUP-479`). Its subscription is §S's.

### An asset created by hand, and a custom asset type

The page on an asset by hand (read 2026-11-16) calls the creation *"a one-time operation"*: the asset
stays in the inventory, unrefreshed, until it is published. Unmeasured here.

An asset of a type other than the managed ones needs a custom asset type, created through the API under
the domain unit's `CREATE_ASSET_TYPE` grant and listed under *Catalog management → Custom asset types*
(the release notes, 2026-10-20). The root unit grants it to no Sandbox project (6f 1.1). A custom type
is unmanaged: a subscription to it is fulfilled by no grant (§S). None has been created here (6f 3.1).

### The inventory, a revision and the identifier an asset carries

- Each edit of an asset's business or technical metadata, by hand, by a source's run or by an API call,
  creates a revision; a source run's revision shows `SYSTEM` as its creator on the *History* tab, and
  subscribers see a change only after a re-publish (the curation page, read 2026-11-17). Measured on
  `trades_notional`: revisions 3 to 5 written by the user and 6 to 7 by `SYSTEM` kept the description, the
  README and the form (2026-11-10, Stage 19 iv).
- A Glue table asset's external identifier is
  `arn:aws:glue:us-west-2:<account>:table/<database>/<table>.<project id>`, whichever act made the asset
  (measured 2026-11-10, `SUP-343`). Code that matches an asset on `<database>/<table>` finds none.
- The asset's `GlueTableForm` carries `catalogId` and `tableArn`, both naming the account (read, Stage 19
  decision 19).
- A dataset node meets an asset through `AssetCommonDetailsForm::sourceIdentifier` (the linking page,
  read 2026-11-16). The table node's `sourceIdentifier` is the table's ARN, with no project suffix
  (measured 2026-11-10, `SUP-347`), and the graph of 2026-11-14 joined it to the asset (Stage 19 v).

### What a subscriber's source imports

A Glue source over a subscriber's `DataLake` database imports the subscription's resource link as an
unlisted asset. After a revocation deletes the link, the asset stays, and a later run neither removes,
reports nor counts it (measured 2026-10-27, 2026-11-14 and 2026-11-15; `SUP-197`). Published, it would
list another owner's table under the subscriber's name: `CT-19` fails a listed link and notes an inventory
one.

### The order a deletion takes

`DeleteDataSource` is refused with an empty `ValidationException` while an asset the source imported
exists. The order is the listing's `UNPUBLISH`, then `DeleteAsset`, then the source, before the source's
next scheduled run imports the table again (read 2026-11-14 in Data Governance's trail, `SUP-366`; the
cause inferred from the order). Stage 20's rollback takes that order: the data product, the assets, the
source; the tables, by `DROP TABLE` through Athena as the project role, then the database; the `DataLake`
environment; the lineage events only if Stage 20 verification xv reads that a delete clears the graph. An
Iceberg table's `DROP TABLE` left its objects as noncurrent versions behind delete markers (Stage 20 0.7).

---

## M. Business metadata

### Names, descriptions and the README

The curation page (read 2026-11-17): on the asset's page, the edit icons beside the business name and the
description; on the *Overview* tab, *Summary*, *Glossary terms*, *Readme* (Markdown, up to 4,096
characters, written in a code editor with a *Side By Side Preview* switch, read 2026-11-21) and *Metadata
forms*; under *Asset details*, *Catalog visibility* and *Subscription approval*; on the *Schema* tab, each
column's business name, description, glossary terms and forms.

Measured: the user wrote `trades_notional`'s description, README and `classification` `internal` on
2026-11-10, and they travelled to listing revision 4 onwards and survived the source's updates (Stage 19
iv); read again in `app-etl-dev` at revision 4 on 2026-11-15 (step 15). In `app-dbt-dev` on 2026-11-21
each save was one revision, the description's check mark, the README's *Save* and the form's *Save*:
revisions 3 to 5 over a source's two, the README stored as `AssetCommonDetailsForm`'s `readMe`, and the
bundle's export carrying all three (Stage 20 8.6). A table's comments in Glue are
technical metadata: dbt writes a model's with `persist_docs`, the Athena adapter's `glue:UpdateTable`
(read, Stage 20 0.13), and whether a source carries them to the asset is Stage 20 verification xvi,
unmeasured.

### Generated names and the switch that keeps them off

- *Generate suggestions* on an asset's page, or a source's *Automated business name generation* during its
  runs, writes AI-made business names and descriptions for review (the curation and data source pages,
  read 2026-11-17). The models are Bedrock's, chosen by the service, called in-Region in `us-west-2` for
  names and descriptions (read 2026-10-18, 6f 5.1); business names bill as compute units at 1.776 USD each,
  0.2 free a month ([`PRICING.md`](../../PRICING.md)). Never run here.
- The switch is the source's `recommendation.enableBusinessNameGeneration`, or `predictionConfiguration` at
  `CreateAsset`; no IAM condition key reaches it (read 2026-10-18, `SUP-191`).
- Off on every source over the lake (6f decision 3, 2026-10-27; `CT-5`) and on every deployment project's
  source (`CT-14`); a Sandbox project's own database is its members' choice.
- The portal's *Publish to Catalog* created its source with generation on (`SUP-191`), so each lake publish
  was followed by `update-data-source`, sent without the `dataAccessRole` that `get-data-source` reports,
  which DataZone refuses for a source on a connection (measured 2026-10-26, `SUP-196`). A listing's
  `DataSourceReferenceForm` keeps the source's configuration as published, so a check reads the source,
  never the listing (measured 2026-10-27, `SUP-198`).

### Glossaries and terms

The glossaries page (read 2026-11-17): *Manage → Catalog management → Business glossaries → Create
glossary*. A term carries a name, a description, a README of up to 4,096 characters and an enabled switch,
and relates to other terms by *Is A Type of* and *Has Types*, at most 10 of each; a term attaches to at most
10 assets. A disabled glossary is offered to no new form; deleting a glossary needs it disabled and empty,
and deleting a term needs it disabled, detached and unrelated. A glossary is owned by the project that
creates it and visible to the whole domain (read, 6f 4.2). Creating one needs `CREATE_GLOSSARY`, which the
root unit gives no Sandbox project (6f 1.1). None has been created here.

### Metadata forms

- The forms page (read 2026-11-17): *Manage → Catalog management → Metadata forms → Create Form*, a display
  name and a technical name that cannot change, then fields of type String, Integer, Long, Float, Double,
  Boolean, Date or Business glossary, each optional or required and searchable or not. A form is deleted
  only when disabled and detached from every asset. A form attached to an asset type applies to every
  asset of that type, and one attached to the domain to every asset published there; a form changed after
  it was attached shows *Outdated* on the asset until a member updates it (the curation page).
- `CreateFormType` needs an owning project, and only its members edit the form (read 2026-11-10, Stage 19
  decision 4); creating one needs `CREATE_FORM_TYPE` (§O).
- Measured: `classification`, valued `public` or `internal`, owned by `eighth-experimentation`. Each save
  in the portal was a `CreateFormType` answering a new revision, revision 2 at 00:44:24 UTC on
  2026-11-10, and `GetFormType` answers a non-member (`SUP-344`). Every product listing carries it (Stage
  19 decision 4; `CT-18`); a table a data product's publication listed, reachable through the product alone,
  takes the product's form (decision 4 extended 2026-11-23). Its model is one `String` with no list of values, the description naming
  `public`, `internal`, `restricted` or `personal`, so *Add Form*'s *Enter field values* takes any text
  (read 2026-11-21, Stage 20 8.6).
- A domain unit's metadata rule can require a form at publishing (the metadata rules page, read
  2026-11-08); a required form shows *Required* on the asset and cannot be removed (the curation page). No
  rule is set here.

---

## P. Data products

### A product against an asset

A data product groups assets into one listing that a subscriber requests once (the products overview,
read 2026-10-28). Publishing a product publishes its unpublished assets, which are then reachable through
the product alone (the product pages, read 2026-11-17).

### Building and publishing a product

1. Build (the product pages, read 2026-11-17): *Manage → Catalog management → Assets → Create → Create
   data product*, a name and a description, the assets, *Create*. An asset's *Actions* also hold *Add to
   existing data product* and *Create new data product with this asset* (the curation page).
2. Publish: the *Data products* chip with *Owned by this project*, the product, *Publish*, then *Publish
   data product*.

Measured: `my-data-product` (2026-09-13, never subscribed; 6f); `trades-notional` (`bvs7m8z4h6w70w`) in
`eighth-experimentation`, created 03:38:11 and published 03:38:28 UTC on 2026-11-14, listing
`dpx3r3w5msguc0` (Stage 19 pass 2), retired the same day (Stage 19 item 20). Republishing a product
changes the access its subscribers hold (the republication page, read 2026-10-28); no republication of a
product has been read here.

### The product's name is the domain's

`CreateDataProduct` with a name another project's product holds answers `ConflictException`, *"Conflict
with dataProduct 5070mjwdvjwp3k"* (measured 2026-11-16, Stage 19 release F; `SUP-369`). No identity reads
a product's name across the domain: `Search` with the `DATA_PRODUCT` scope needs an owning project, and a
non-member's search is refused (measured 2026-11-16, `SUP-371`), so the create's conflict is the only
domain-wide answer. The stage that lists a product therefore owns it: Production's `publish` task creates
`trades-notional` there (Stage 19 decision 26 (b)), `app-etl-dev`'s product was deleted 2026-11-16, and the
grant for the pair of create actions was applied 2026-11-17 (§O). At release G's first run, on 2026-11-22,
DataZone authorized `CreateDataProduct` against the domain's ARN, as it did the product's
`CreateListingChangeSet` (Stage 19's log); `CreateDataProductRevision` waits for a release that revises the
product.

### What one request gives

One request for a product of one item, accepted at creation, fulfilled the item, `GRANTED` (read
2026-11-14, Stage 19 vii). A product of an S3 Object Collection and a Glue table (2026-11-23, Stage 21
5.4): one request accepted at creation, one subscription grant per item by `SYSTEM`, the table's
`COMPLETED` 52 s after the request and the collection's 75 s, the collection's S3 Access Grant `READ`. A
product's request takes no `assetPermissions` (*"assetPermissions is only supported for
S3ObjectCollection Listing"*), so write on a collection is asked on its own listing (`SUP-481`). The
table, unpublished before, was published by the product's publication with a listing that reads
`INACTIVE` and that `search-listings` omits (`SUP-482`); `CT-17` and `CT-18` reach it through the product
listing's items (§V). The subscription is listed under the
product listing's id and under each asset listing's, and its grant under the asset listing's alone
(measured 2026-11-14, `SUP-363`), so a join of grants to subscriptions asks under both (`CT-17`).

### The CI/CD CLI carrying a product

- The CLI 1.0.9's catalog export takes everything the source project owns, with no filter (read, Stage 19
  0.9 and 3.1).
- The import matches by `externalIdentifier`. `CreateAsset` with the source's identifier is a
  `ConflictException` the CLI counts as an update, so a target's asset comes only from its own source, and a
  later import maps the source's asset to it by name (measured 2026-11-15 and 2026-11-16, `SUP-369`).
- The import first checks the target project's domain unit for its create grants (`SUP-351`); `bundle`
  exits 0 when its caller cannot read the stage's project (`SUP-352`); `deploy` reports an import failed
  only when every item failed (`SUP-357`).
- The pipeline's `--catalog-follow-up` (Stage 19 decision 25 (b)) starts the target's source as the deploy
  role and imports a second time, which revised Staging's asset by name (measured 2026-11-16, pipeline
  #129; `SUP-369`).
- Production's listing `5hpftif3nnoj2o` read `ACTIVE` at revision 6 over the asset `da1fycta6l71n4`, and
  Staging's asset `as6m73yp8shr80` unlisted (read 2026-11-16 and 2026-11-17, Stage 19's log; `CT-15`).

---

## F. The publication flow

### From a table to a listing

1. **The table** exists in a database a source covers (§A).
2. **The import**: a source's run, scheduled, started by a member's *Run* or by the `publish` task, adds or
   updates the asset in the inventory, unpublished, since no source publishes on import (`CT-4`).
3. **The curation** (§M).
4. **The publication**: *Manage → Catalog management → Assets*, the asset, *Publish asset* (the curation
   page, read 2026-11-17). Only the latest revision is published; after an edit the page offers *Re-publish
   asset*, and *Asset details* show the latest inventory revision beside the published one. By API:

   ```bash
   aws datazone create-listing-change-set --domain-identifier dzd-d8yrvx1ko7im6o --entity-identifier <asset id> --entity-type ASSET --action PUBLISH --region us-west-2
   ```

   Measured: the listing `ACTIVE` 9 s after the call (2026-10-22, Stage 18 7.2). The revision the call
   answers stays `CREATING` while the service writes the next one `ACTIVE`, so a reader waits for the latest
   revision at or past the answered one; a republication passes through `UPDATING`, a status the API's model
   lacks (measured 2026-11-10, `SUP-345`).
5. **The short cut**: `publishOnImport` true publishes every import, a resource link included; `CT-4` fails
   it (Stage 19 decision 3).

The path before the 2026-10-20 redesign, *Data → Catalogs → AwsDataCatalog → `curated` → tables → `trades`
→ Publish to Catalog* (6f 11.6, 2026-10-26), created a source, the asset and the listing in one act, the
source with generation on, `INCLUDE *`, no schedule and `publishOnImport` false (`SUP-191`). Whether the
portal still offers it is part of the user's re-reading.

### The house's publish

The template's `publish` task ([`app_etl_tasks.py`](../../../examples/app-etl/code/app_etl_tasks.py)) takes
the API's path in the stage whose `PUBLISH_LISTING` is `true`, `prod` alone (Stage 19 decisions 3 and 20
(b)). It finds the project's source over the product's database, starts it and waits up to 600 s, finds
the asset by its external identifier for up to 120 s, publishes the latest revision and waits up to 120 s
for an `ACTIVE` listing revision; a workflow that names a data product then has it created or revised, and
listed. Measured in Sandbox on 2026-11-10 (Stage 19 ii) and in Production on release F's run of
2026-11-16 (Stage 19's log).

### Who may publish, and the approval switch

Owner or Contributor of the asset's project (the curation page, read 2026-11-17), or a project role through
`CreateListingChangeSet` (read 2026-11-08). The approval switch is *Subscription approval* under *Asset
details*, required by default, followed by a re-publish (the curation page); the listing carries it as
`SubscriptionTermsForm.approvalRequired` (`SUP-198`). With approval off, every request is approved at
creation (the approval page). Measured: `house-price` turned from `YES` to `NO` on 2026-11-14 and was kept
so by the user (6f 2.2). Every lake listing requires approval (6f decision 5; `CT-11`).

### What publishing writes

An asset's listing, and two lineage nodes, the asset's and the listing's, linked column by column; no Glue,
Lake Formation or S3 write (measured 2026-09-13 and 2026-10-26, `SUP-191`), and no LF-Tag on the asset or
the listing (measured 2026-09-18 and 2026-10-26, `SUP-192`). Access is a subscription's (§S).

### Unpublishing

*Actions → Unpublish* on the asset's page: new users can no longer find or subscribe to the asset, existing
subscriptions stay as they are, and *Publish asset* lists it again (the curation page, read 2026-11-17). By
API, `create-listing-change-set --action UNPUBLISH` (measured 2026-11-14 from the portal, `SUP-366`).

---

## S. Sharing between projects

### The request

- A member of the requesting project: *Discover*, a search, the asset, *Subscribe*, a justification,
  *Request*; the request's status under *Discover → My subscriptions → Requests* (the subscription page,
  read 2026-11-17). Since 2026-10-20 the catalog is browsed from inside a project (the release notes).
- By API: `aws datazone create-subscription-request --subscribed-listings identifier=<listing id>
  --subscribed-principals project={identifier=<project id>} --request-reason <text>`. Measured: 6f 11.8
  (2026-10-26) and Stage 18 7.2 (2026-10-22).
- A project role holds `CreateSubscriptionRequest` (read 2026-11-08). The `Workloads` OU's document denies
  it to every principal in Staging and Production (Stage 19 decision 13, measured 2026-11-11; `SUP-354`), so
  a deployment project subscribes to nothing.

### The approval, and when it is automatic

- A member of the owning project: *Manage → Catalog management → Subscription requests → Requests*, *View
  request*, *Full access* or *Filtered access* with one or more asset filters, an optional response,
  *Approve* or *Reject* (the approval page, read 2026-11-17). On a data product's listing the portal's
  *"Review subscription request"* panel offers no access choice (measured 2026-11-22, Stage 19 4.12):
  *Approve*, the default, or *Reject*, an optional decision comment of up to 150 characters, *Data
  permission* *"Read-only"*, and *Save*.
- Automatic, by the same page: when the listing requires no approval, and when the requester is Owner or
  Contributor of both the owning and the requesting project. A request from a space's terminal as the
  consumer's project role is recorded as the space's user, so it is automatic when that user owns both
  projects (measured 2026-11-23, Stage 21 5.4; `SUP-480`).
- Measured (6f 11.8, 2026-10-26): requested 21:34:55Z, approved 21:36:15Z, `COMPLETED` 21:37:18Z, each
  portal call as the domain execution role in the person's session. By API, `accept-subscription-request`
  as `awsds-infra-staging`, Staging's `InfrastructureAccess`, a member of Stage 18's deployment project in
  Staging, removed since (Stage 18 7.2, 2026-10-22).

### The target

A Glue table's subscription target is the subscriber's `DataLake` environment's,
`<environment>-default-target`, whose `manageAccessRole` is the project role; a project with no
`ACTIVE` `DataLake` environment receives none (read 2026-10-20, `SUP-193`). The project's first `ACTIVE`
`DataLake` environment carries it, whether *Create database* or the API created it, and a later one none
(§A, `SUP-184`).

### The fulfilment in one account

Measured 2026-11-14 (Stage 19 vi; `SUP-195`), each act in an `AWSDataZone-Subscriptions` session, which
carries no `aws:SourceIdentity` (`SUP-194`):

1. the owner's project role grants `SELECT` on the table to the account's `IAMPrincipals` under the
   consumer's `context.datazone.projectId`, with no grant option, 45 s after the request;
2. the consumer's project role creates the resource link in its `DataLake` database 10 s later, and grants
   `DESCRIBE` on it to `IAMPrincipals` and to `arn:aws:identitystore:::user/*` under the same condition;
3. the grant reads `COMPLETED` 65 s after the request.

No RAM share and no catalog policy is written.

### The fulfilment across accounts

Measured 2026-10-22 (Stage 18 7.2) and 2026-10-26 (6f 11.9), `SUP-195`. Beside the grant and the link:

- the grant carries `CROSS_ACCOUNT_VERSION` 5 in its own parameters, whatever the producer account's
  setting;
- a RAM share, `LakeFormation-V5-*`, of the producer's whole catalog (`catalog`, `database/*`, `table/*/*`);
- per-resource Glue policies naming the consumer account, on `catalog`, `database/*` and `table/*/*`,
  with `enableHybrid` `TRUE`: three `glue:PutResourcePolicy` calls in Staging (Stage 18 7.2) and four in
  Data Governance under `aws:PrincipalOrgID` (6f 11.9). `glue get-resource-policies` lists them, while
  `glue get-resource-policy` answers *"Policy not found"* either way (`SUP-099`).

Lake Formation's `SELECT` under the subscribing project's context scopes the read. The lake's grant reached
`COMPLETED` 63 s after the approval (6f 11.9).

### Managed and unmanaged assets

The managed types, by the unmanaged asset's page (read 2026-11-17): *"Lake Formation-managed AWS Glue Data
Catalog tables, AWS Glue Data Catalog views (Multi Dialect Views), and Amazon Redshift tables and views"*.
DataZone fulfils them with grants it writes. Every other type, a custom one among them, is unmanaged: no
grant, and an EventBridge event for the producer to act on (read 2026-09-13 and 2026-10-28); unmeasured.

A Redshift asset is delivered to *"the Amazon Redshift Serverless workgroup created for the project"*, in a
shape set by where the two sides live (the Redshift asset's page, read 2026-11-17):

| Producer and consumer | What DataZone writes |
|---|---|
| one cluster, one database | a grant on the source table |
| one cluster, two databases | a view in the consumer's database, and the grant on the view |
| two clusters in one account | a datashare, a view over the shared table, and the grant on the view |
| two accounts | the same, the producer authorizing the datashare and the consumer associating it |

No Redshift subscription target exists here (Stage 19 0.6, 2026-10-28), and no page says whether a project
that added a warehouse through *Connect to existing compute resources* receives one.
`CreateSubscriptionTarget` takes `applicableAssetTypes`, `authorizedPrincipals`, `manageAccessRole`, `name`,
`type` and a `subscriptionTargetConfig` of forms (`formName`, `content`), with an optional `provider` and
`subscriptionGrantCreationMode` (`AUTOMATIC` or `MANUAL`); its reference names no Redshift type or form (read
2026-11-17). [Stage 21](../stages/stage-21-redshift-s3-data-products.md) pass 2 measures the target AWS
documents, on a workgroup the `RedshiftServerless` blueprint creates for the consumer, and leaves the case
of a project admitted by hand open.

An S3 bucket or prefix published from the portal's S3 browser, *Actions → Publish to Catalog*, becomes an
asset of type *S3 Object Collection*, which the managed list leaves out (the S3 pages, read 2026-11-17). Its
subscription or Share is fulfilled through S3 Access Grants, read-only or read and write at the owner's
choice; after a revocation *"a project member may still get Amazon S3 Access Grants credentials for up to 5
minutes, and credentials can be used for 15 minutes"*, up to 20 minutes of access in all by the page; the
measured residual is the vended session's own duration, 3600 s by default (*The revocation* below).

Measured in Sandbox on 2026-11-23 (Stage 21 5.4 to 5.6; `SUP-481`), a collection under
`eighth-experimentation`'s `shared/` subscribed by `test-experimentation`:

- **The grant**: `CreateAccessGrant` by the owning project's role in session `AWSDataZone-Subscriptions`,
  invoked by DataZone, 66 s and 17 s after the two requests: grantee type `IAM`, the subscriber's project role;
  the owning project's location; the scope the prefix followed by `*`; `READ` for a product's
  subscription, `READWRITE` for a request on the collection's listing with `--asset-permissions
  'assetId=<asset>,permissions={s3=[READ,WRITE]}'`. The subscription grant shows no permission.
- **Reading it**: the subscriber's role alone is refused the objects (`403` on `HeadObject`). `aws
  s3control get-data-access --permission READ --target '<scope>'` answers credentials for 3,600 s
  (900 s with `--duration-seconds 900`), sessions of the owning project's role named
  `access-grants-<uuid>` under a session policy: they read and list inside the scope and are refused
  `s3:ListBucket` outside it, and a `READ` session's upload is refused at `kms:GenerateDataKey`. A
  target wider than the scope answers *"You do not have READ permissions to the requested S3 Prefix"*,
  and `WRITE` on a `READ` grant the same with *WRITE*. The portal reads the same grant in the subscriber's *Data →
  S3 buckets → Subscribed buckets*, which lists the objects and renders an image.
- **The door**: `GetDataAccess` goes to `<account>.s3-control.us-west-2.amazonaws.com`. From a space's
  terminal, which sets no proxy variables, it rides the spoke's S3 gateway endpoint; the JupyterLab
  plugin goes through the proxy (`SUP-091`).

### Reading through a subscription

Measured 2026-11-14 (Stage 19 viii). In the consumer's query editor on *Athena (SQL)*, `SELECT * … LIMIT 10`
on the link, as the consumer's project role in the user's session, `SUCCEEDED` in 1.9 s with 623 bytes
scanned, 40 s after the grant completed. A space's `project.spark.fineGrained` session, Glue 5.0 with 10
`G.1X` workers, counted 10 rows through the link. That session bills by its `DPUSeconds` (`SUP-368`).

### Row and column filters

An asset filter is made on the asset's *Asset filter* tab and chosen with *Filtered access* at an approval
or a Share (the curation page, read 2026-11-17). For a Glue table the filters of one subscription become one
Lake Formation data cells filter, and for Redshift a late-binding view (the filters page, read 2026-10-27).
Never run here.

### The Share

*Actions → Share* on the asset's page: up to 10 projects, read-only, *Full access* or *Filtered access*
(the curation page, read 2026-11-17). Measured (2026-11-14, `SUP-362`): a `CreateSubscriptionRequest` by
the owner for the consumer project, `ACCEPTED` at creation with no reviewer and no reason; its fulfilment is
a subscription's. No Share on a lake listing (6f decision 5): `CT-11` fails one, and `CT-16` notes one on a
Sandbox project's product.

On a data product's page the owner's *Actions* menu reads *Create subscription*, *Unpublish* and *Delete*
(read 2026-11-22, 6f 2.5). *Create subscription* grants the product to up to 10 principals, projects or IAM
roles, with no full or filtered choice, and its project selector lists every project of the domain, the
deployment projects among them. Its request is the Share's, accepted at creation with no reviewer, and the
fulfilment of `my-data-product`'s one item read `COMPLETED` 17.5 s after it.

### The revocation

- *Manage → Catalog management → Subscription requests → Access*, *Revoke*, an optional box that keeps the
  asset in the subscriber's targets, *Revoke subscription* (the revocation page, read 2026-11-17). With the
  box ticked, the page leaves the access to be removed later in Lake Formation. A revoked subscription
  cannot be approved again: the subscriber requests anew.
- The portal read 2026-11-22 shows a dialog *Revoke access* in its place, which asks for the word *confirm*,
  carries no box and sends `retainPermissions` `false` (6f 2.4): the owner's role revoked the grant 39 s
  later and the consumer's deleted the link at 49 s.
- Measured in one account (2026-11-14, Stage 19 ix; `SUP-365`): `RevokeSubscription` at 23:00:00 UTC, the
  producer's `BatchRevokePermissions` at 23:00:52 and the consumer's `DeleteTable` on the link at 23:01:02.
  A Spark session opened before the revocation read until the link's delete, then failed
  `TABLE_OR_VIEW_NOT_FOUND`. The subscriber's inventory keeps the asset its source imported from the link
  (`SUP-197`).
- Measured across accounts (2026-10-22, Stage 18 7.2's rollback): `revoke-subscription
  --no-retain-permissions` at 01:06:30Z, three `glue:DeleteResourcePolicy` on the per-resource policies at
  01:07:09Z (the trail, read 2026-11-17), the grant not found at 01:07:32Z; then no link in the consumer's
  database, no Lake Formation row naming the table and the RAM share `DELETED` (`SUP-195`).
- Measured on an S3 Object Collection (2026-11-23, Stage 21 5.6 and 5.7; `SUP-092`, `TM-37`): the owning
  project's role ran `DeleteAccessGrant` 62 s after `RevokeSubscription`, and the vend was refused 31 s after
  the delete. Credentials vended before it keep their own duration: a `READWRITE` session of 3600 s, the
  default, read and wrote under the scope 19 minutes after the delete, against the page's 15 minutes. The
  asset's *Unpublish* dialog says *"Users with existing access will retain their permissions."*

### What the catalog does not do

- No grant by LF-Tag: a fulfilment grants by name (the fulfilment pages, read 2026-10-28; `SUP-192`).
- No share across Regions, by the Glue and Redshift asset pages (read 2026-10-28 and 2026-11-17): *"Support
  for cross-Region sharing of assets in AWS Glue Data Catalog is not supported."*, *"Cross-Region data
  sharing using Amazon Redshift is not supported."* The unmanaged asset's page contradicts both (read
  2026-11-17): *"Cross-region subscriptions support AWS Glue tables, AWS Glue views, Amazon Redshift tables,
  and Amazon Redshift views across all standard (non-opt-in) AWS Regions"*, with the data lake or data
  warehouse blueprint enabled in both Regions. This estate is one Region; unmeasured.
- No subscription to a resource link (the troubleshooting page, read 2026-10-28).

### The controls around a subscription

- The `Workloads` OU denies `CreateSubscriptionRequest` (above).
- `CT-10`, `CT-11`, `CT-16` and `CT-17` judge every grant and access act (§V).
- Stage 19 step 4.12, `eighth-experimentation`'s subscription to Production's listing, is unrun. Its approver
  is Stage 19 decision 15, taken as (d) on 2026-11-17: the Governance Manager a member of
  `deploy-production` under the custom designation `subscription-approver`, created 2026-11-19. The
  membership, by the project's owner, comes first.
- The lake road: `governed-lake` lists `curated.trades`, the publishing role holding its read with the grant
  option in [`publishing.tf`](../../../terraform-live/data-governance/data/publishing.tf); a restricted or
  personal table travels on TBAC grants alone (6f decision 2; `CT-12`).

---

## L. Lineage

### The capture mechanisms

AWS's lineage pages (read 2026-11-16) describe five ways an event reaches the domain (Stage 20 question 1):

| Mechanism | Who emits | In this estate |
|---|---|---|
| The portal's own tools: a JupyterLab notebook on a Glue or EMR Serverless Spark session, a Visual ETL flow in Glue's compatibility mode, the query editor on Redshift | SageMaker Unified Studio, nothing configured | unmeasured |
| A data source or a connection with *Import data lineage* | DataZone, on the source's run: a Glue source captures the crawlers that fed it, under 250 tables a run; a Redshift source parses the system tables' queries daily | the Lakehouse and IAM connections carry `glueLineageSyncEnabled` true from their creation (`SUP-207`) and no project runs a crawler; the Redshift connection's daily sync fails while the workgroup is down (`EXC-17`) |
| An engine the producer configures | the engine's OpenLineage listener: Glue 5.0 and later, Spark DataFrames only; EMR Serverless 7.5, EMR on EC2 7.11, EMR on EKS 7.12 | measured: `app-etl`'s Glue job (Stage 18 7.1, Stage 19 v and xxi) |
| Any OpenLineage producer, through `PostLineageEvent` | the producer's client, through the `amazon_datazone_api` transport merged in OpenLineage 1.33.0 | dbt's door, measured on a worker and from a space on 2026-11-21 (Stage 20's sitting A) |
| The catalog's own acts | DataZone: a node per asset (`amazon.datazone.asset/<id>`) and per listing | measured: the edges *Cataloged*, *Published* and *Access Requested* (Stage 19 v) |

MWAA Serverless posts nothing of its own: of 44 events read, every one was a Glue job's (measured, Stage
10 xix). A task's own boto3 or pandas code posts nothing unless it calls the API. Athena and a SageMaker
processing or training job are absent from AWS's support matrix (read 2026-11-16).

### An event

The domain takes OpenLineage RunEvents alone, from OpenLineage 1.22.0 onwards, each under 300 KB (the
lineage pages, read 2026-11-16). An event carries an event type (`START`, `RUNNING`, `COMPLETE`, `FAIL`), a
run with its id, a job named by a namespace and a name, and input and output datasets, each with a
namespace, a name and facets, as the events below show. Measured: a Glue job's run posted 12 events, 4
`START`, 4 `RUNNING` and 4 `COMPLETE`, under the namespace `default` with the job name's `-` turned to `_`
(2026-10-19, `SUP-097`). Simulated: the dbt wrapper's events carried the facets `schema`, `symlinks`,
`documentation`, `columnLineage` and `dataQualityAssertions` (Stage 20 0.16).

### The nodes and their names

The graph page (read 2026-11-17) defines three node types: dataset, job and job run. Each version of a
dataset node is an event at its timestamp, listed on the node's *History* tab, and the portal combines a job
with its latest run. The `sourceIdentifier` page (read 2026-11-16) names each node:

- a job is `<namespace>.<name>`, a job run `<namespace>.<name>/<run_id>`;
- a dataset becomes the Glue table's ARN through its `symlinks` facet when the event carries Glue's
  environment properties (`GLUE_VERSION` and the like), and, measured, when it carries none (dbt's
  events, 2026-11-21, `SUP-391`);
- a namespace that begins with `redshift` becomes a Redshift ARN,
  `arn:aws:redshift-serverless:<region>:<account>:table/<workgroup>/<database>/<schema>/<table>` for a
  serverless workgroup;
- every other dataset is `<namespace>/<name>`.

Measured: a Glue table node's `sourceIdentifier` is the table's ARN; `GetLineageNode` refuses that ARN and
answers to the node's id, to an asset's `amazon.datazone.asset/<id>` and to a job's
`default.app_etl_avhvbqn37ty7m8` (2026-11-10, `SUP-347`). The publish of 2026-09-13 created the asset's
node `69dcbz6ii1j6hc` and the listing's `58w6xmloxbpvkg`, with column lineage between them (6f 6.1).

### How a dataset meets an asset

A dataset node links to an asset whose `AssetCommonDetailsForm::sourceIdentifier` equals the node's (the
linking page, read 2026-11-16). For an event a producer posts, the troubleshooting page's remedy for a node
that stands apart is to fix the dataset's namespace and name in the event and post it again (read
2026-11-16). Measured: the Glue job's table node joined `trades_notional`'s asset, and the portal drew the
S3 input, two Spark job runs, the Glue table and the catalog's edges (2026-11-14, Stage 19 v).

### A Glue job's settings

The template's Glue job ([`app-etl.yaml`](../../../examples/app-etl/workflows/app-etl.yaml)) carries the
listener in its `--conf` argument, beside its Iceberg catalog (Stage 19 decision 10, Stage 18 7.1's
settings):

```text
--conf spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener
--conf spark.openlineage.transport.type=amazon_datazone_api
--conf spark.openlineage.transport.domainId={domain.id}
--conf spark.glue.accountId={env.ACCOUNT_ID}
--conf spark.openlineage.facets.custom_environment_variables=[AWS_DEFAULT_REGION;GLUE_VERSION;GLUE_COMMAND_CRITERIA;GLUE_PYTHON_VERSION;]
--conf spark.openlineage.columnLineage.datasetLineageEnabled=True
--conf spark.glue.JOB_NAME=app-etl-{proj.id}
```

The job reaches the domain through the `datazone` interface endpoint of its VPC, which AWS's troubleshooting
page asks for (read 2026-10-19). Without it the job posted nothing, held the listener about 33 s per
attempt and still succeeded (measured 2026-10-19, `SUP-097`). With it: 12 events and no graph, since no node
was an asset (Stage 18 7.1, run B); 92 events and a graph once the table was an asset (Stage 19 v,
2026-11-10 and 2026-11-14); 69 in Production and 46 in Staging (Stage 19 xxi, 2026-11-16).

### The dbt case

Read and simulated in Stage 20's pass 0, then measured on a worker and from a space on 2026-11-21, in Stage
20's sitting A.

- **The wrapper** `dbt-ol` (OpenLineage 1.55.0, read 2026-11-16, Stage 20 0.9) handles `run`, `seed`,
  `snapshot`, `test`, `build` and `retry`, and passes any other command to `dbt` untouched. It starts `dbt`
  as a subprocess, returns dbt's exit code, and treats a failed post as a warning, *"OpenLineage client
  failed to emit event"*. `send-events` emits from the last run's artifacts without running dbt. It emits a
  `START` and a `COMPLETE` or `FAIL` for the command, for each model and for each model's tests, with the
  table's schema, the compiled SQL, the tests' assertions and a column-lineage facet parsed from the SQL
  (Stage 20 question 2).
- **The names**: `dbt-athena`'s dataset is `awsdatacatalog.<database>.<table>` under
  `awsathena://athena.<region>.amazonaws.com`, with a `symlinks` facet naming `table/<database>/<table>`
  under `arn:aws:glue:<region>:<account>`, the account from the profile's `assume_role_arn` or from
  `sts:GetCallerIdentity`; the event carries no Glue environment properties. The job namespace is
  `OPENLINEAGE_NAMESPACE`, `dbt` by default, and a model's job is `<database>.<schema>.<project>.<model>`,
  with `.build.run` under `dbt build` and `.build.test` for its tests (0.9).
- **The node it gets**: the Glue table's ARN. The page's rule gives
  `awsathena://athena.<region>.amazonaws.com/awsdatacatalog.<database>.<table>` to an event with no Glue
  environment properties, and the domain honoured the symlink regardless: a model's node joined its asset
  and the Glue job's nodes in one graph (measured 2026-11-21, Stage 20 vi and vii, `SUP-391`).
- **The renaming** (Stage 20 decision 3 (b)): OpenLineage's `transform` transport rewrites each dataset in
  the client before the post, to the namespace `arn:aws:glue:<region>:<account>:table` and the name
  `<database>/<table>`, the one form the general rule turns into the ARN, and the form a third party's
  hand-posted event needed ([Classmethod](https://dev.classmethod.jp/en/articles/20260712-amazon-sagemaker-data-lineage-iam-domain/),
  2026-07-12). `app-dbt`'s `LINEAGE_NAMES` picks `as-built` or `glue-arn`.
- **The transport** `amazon_datazone_api` takes `domainId`, `region` and `endpointOverride`, posts RunEvents
  alone and has no timeout; with `endpointOverride` its client takes the Region from the environment (0.9).
- **The archive**: 26,119,606 bytes, 82,819,034 unzipped, 5,102 entries, against the worker's 250 MB for
  each (0.15). The wrapper's SQL parser asks for glibc 2.28, and a worker reads glibc 2.34 (Stage 20 2.2,
  2026-11-21).
- **Simulated** (0.16): a first `dbt build` ended 0 in 7.9 s and posted 6 events after dbt ended; with the
  endpoint's port closed and one attempt, exit 0 and *"Emitted 0 OpenLineage events"*; with a 403, exit 0
  and no event; each failed post's warning prints the whole event, the logs growing to 125 kB and 77 kB
  against 3.5 kB; a failing test returned dbt's exit code 1. A seed emitted no event and was no input of
  the model that read it (0.8).
- **Measured** (Stage 20 2.3 to 3.3, 2026-11-21): a worker's `dbt build` posted six events as the project
  role's session `AmazonMWAAServerless` through the VPC's `datazone` endpoint; a person's `dbt run` from a
  space posted four as the person (`SUP-402`), a job of its own in the workflow's graph under the namespace
  the person chose. Each table swap renames by a create and a delete (`SUP-400`). A refused, a rejected and
  an unanswered post each left the task `SUCCESS`, exit code 0 and *"Emitted 0 OpenLineage events"*; the
  unanswered one added 60 seconds per event at one attempt.

### A dbt run past the worker's hour

The worker caps a task at 3,600 s. The MWAA Serverless [quotas page](https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/mwaa-serverless-quotas.html)
gives a maximum task execution timeout of 60 minutes, with no column for what can be raised; its
[parameters page](https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/supported-airflow-parameters.html)
validates `execution_timeout` at 3,600 s, `retries` from 0 to 3 and `retry_delay` up to 300 s, and ignores
`deferrable` (read 2026-11-16, Stage 20 0.12). The institution's typical run can pass one hour (Stage 20
step 1.1). Stage 20 runs dbt in one Bash task on the worker (decision 2), whose limits are 1 vCPU, 3 GiB,
250 MB of code and the hour. The forms below are desk readings of 2026-11-16 and 2026-11-17, from AWS's
pages and the released wheels of `apache-airflow-task-sdk` 1.0.6 and `apache-airflow-providers-amazon`
9.38.0 (0.12, 0.14); no pass of Stage 20 measures one.

| Form | What it needs | What carries it past the hour | What nothing here measured |
|---|---|---|---|
| A processing job in the project's network, with a waiting task | Stage 20 decision 13 applied (its pass 4, unapplied): `CreateProcessingJob` taken out of `DenySageMakerJobsWithoutNetworkIsolation` in [`sagemaker-denies`](../../../terraform-modules/sagemaker-denies/main.tf), which the persona sets, the `Workloads` OU's document and the project boundary of `sagemaker-prereqs` compose, then the SCP battery. The lint's rules as [`sagemaker-application.md`](sagemaker-application.md) §W gives them today, `retries: 0`, a `MaxRuntimeInSeconds` of at most 2,820 s and `EnableNetworkIsolation: true` on every job, refuse this form until they change. An image holding dbt and the wrapper. The job then runs as the project role in the project's subnets and security group, and meets the proxy's allow-list for its source range: a space's in Sandbox, an empty one in Staging and Production (0.14) | `SageMakerProcessingOperator` with `wait_for_completion: false`, then a `SageMakerProcessingSensor` task. A try ended by the task's `execution_timeout` raises `AirflowTaskTimeout` and is retried, up to three times: about four hours a waiting task. A sensor's own `timeout` raises `AirflowSensorTimeout`, which fails the task for good. The operator has no `on_kill`, and a retried try of it starts a second job (`action_if_job_exists: timestamp`) (0.12) | the form on the service, and the price and start of an ML instance for a client that only sends SQL: a processing task held its worker 791 s for a one-second command (measured 2026-10-11, 6i) |
| Several Bash tasks, each `dbt build --select <part>` | nothing beyond decision 2's Bash task: each task's models read the tables an earlier task built, and the workflow's `dependencies` hold the order | each task has its own hour, so the run as a whole can pass it; 0.088 USD per task-hour, one-minute minimum ([`serverless-workflows.md`](serverless-workflows.md) §O) | the form; it does nothing for one model longer than the hour, and it moves the project's order from dbt's graph into the workflow |
| A Glue job as dbt's runtime, the form of awslabs' [`runner-dbt-aws-airflow`](https://awslabs.github.io/runner-dbt-aws-airflow/) 1.0.0 | operators that run dbt and its adapter in a Glue Spark job, a Glue interactive session or a Glue Python shell job, carried in the worker's code package; every wheel under the application's prefix, since no Glue job here reaches PyPI; an adapter for dbt Core 1.11, which `dbt-glue` lacks (1.10.19, then the 1.12 line) and `dbt-spark` 1.11.0 offers with `pyspark` in its `session` extra (0.10). The runner names MWAA, not MWAA Serverless, installs dbt from the internet in its default variant, and pins OpenLineage 1.50.0 in its lineage extra (read 2026-11-16). A waiting task with `retries` above 0, which the lint's `retries: 0` refuses as it stands | the waiting task is capped like any other. `GlueJobOperator` leaves its run going when its try is ended (`stop_job_run_on_kill` false), and with `resume_glue_job_on_retry` a retried try finds that run by its `--airflow_task_uuid` instead of starting another (0.12). The job runs in the project's network already | the form, its lineage, and its bill: a job by DPU-hour, an interactive session by its `DPUSeconds` (`SUP-368`) |

Not offered (Stage 20 question 4): a Python task calling dbt's `dbtRunner`, where the worker's
pre-installed packages win over the archive's and Airflow 3.0.6's constraints pin `click` 8.2.1, `protobuf`
4.25.8 and `sqlparse` 0.5.3, below dbt-core 1.11's floors, and `mmh3` 5.2.0, above `dbt-athena` 1.11.1's
ceiling of 4.2.0; and a provider's operator in the code package, since AWS names none for dbt Core. A space
is a person's (D17), and no operator starts one.

### The names other adapters give their datasets

`dbt-redshift`'s events name a dataset `<database>.<schema>.<table>` under
`redshift://<workgroup>.<account>.<region>.redshift-serverless.amazonaws.com:5439`, the form of the
`sourceIdentifier` page's own example for a serverless workgroup, whose stated result is the table's
Redshift ARN; the convention the page quotes beside that example is shorter,
`provider://{cluster_identifier or workgroup}.{region_name}:{port}` (read 2026-11-16). For the `glue`
adapter type the wrapper names a dataset `<database>.<schema>.<table>` under
`arn:aws:glue:<region>:<account>` (read, 0.9), which the page's general rule turns into
`<namespace>/<name>`, no table's ARN: an inference from the page, not run. Only the Athena adapter's events
carry the Glue symlink (0.9). Redshift and Glue with Spark are a later revision's (Stage 20 decision 1), and
no pass reads what the domain builds from either.

### dbt's docs site against the catalog's graph

dbt's own lineage is its `manifest.json`, whose `parent_map` and `child_map` hold each resource's
first-order parents and children ([dbt's page](https://docs.getdbt.com/reference/artifacts/manifest-json),
updated 2026-09-08, read 2026-11-16), and `dbt docs` draws that file as a graph of models. Column-level
lineage needs dbt's hosted platform on an Enterprise plan, or dbt v2 locally
([dbt's page](https://docs.getdbt.com/docs/explore/column-level-lineage), updated 2026-10-01, read
2026-11-16). The docs site draws dbt's models alone: no Glue job, no asset and no catalog act. The
institution holds proposals to use it and nothing official (Stage 20 step 1.1). Not run here.

### Reading a graph, and deleting an event

- The portal: the asset's *Lineage* tab draws from upstream job runs and source tables to the asset's
  inventory and published versions, with *Show dataset nodes only*, *Display in event timestamp order* and
  *Graph depth* (the curation page, read 2026-11-17). With dataset nodes only, the graph cannot be expanded
  (the graph page). Measured at depth 5 on 2026-11-14 (Stage 19 v).
- The API (the lineage pages, read 2026-11-16): `GetLineageNode`, `ListLineageNodeHistory`, `QueryGraph`
  (announced 2026-03-17), `ListLineageEvents`, `GetLineageEvent`, `PostLineageEvent` and
  `DeleteLineageEvent` (announced 2026-07-07). A node's id is in Data Governance's trail, in each
  `CreateLineageNode`'s `additionalEventData` (`SUP-191`, `SUP-347`). `list-lineage-events` read empty on
  2026-09-18 and 2026-10-18 (6f 6.1), before any engine posted.
- `DeleteLineageEvent` is refused to the infrastructure user in Sandbox, by the domain's resource share,
  and in Data Governance, by DataZone (2026-11-21, `SUP-401`). What it removes, Stage 20 verification xv,
  stays unmeasured, and a posted event stays in the graph: Stage 20 3.4's foreign event is drawn into
  `app-dbt-dev`'s `notional_by_desk`.

### Who may post and who may read

Every domain user reads the graph through `GetLineageNode`, `ListLineageNodeHistory` and `QueryGraph`;
`ListLineageEvents` and `GetLineageEvent` need their own allow; posting needs `datazone:PostLineageEvent`,
which IAM authorizes at the API Gateway layer (the permissions and authorization pages, read 2026-11-16).
The project role holds `PostLineageEvent` through `SageMakerStudioProjectUserRolePolicy` (read 2026-10-19,
Stage 18 7.1). A Glue job posts as the project role's `GlueJobRunnerSession` (measured, Stage 19 xxi), a
worker task as its `AmazonMWAAServerless` and a person from a space as its `SageMaker`, the person named as
the creator (Stage 20 2.3 and 2.6, 2026-11-21, `SUP-402`). The post is checked against no dataset's owning
project: an event from `test-experimentation`'s role joined `app-dbt-dev`'s table node and its asset's tab
(Stage 20 3.4, xi).

### The limits, and how each failure shows

The limits (the lineage pages, read 2026-11-16): RunEvents alone, OpenLineage 1.22.0 or later, 300 KB an
event, a graph drawn only when one of its nodes is an asset, a crawler's lineage only under 250 tables a run,
and a Redshift capture that leaves out external tables, `COPY` and `UNLOAD`, `MERGE` and `UPDATE`, events
over 16 MB and datashares.

| Failure | How it shows | Record |
|---|---|---|
| a Glue job with no path to the `datazone` endpoint | no event; the driver's error stream alone shows it, about 33 s per attempt; the job succeeds | measured 2026-10-19, `SUP-097` |
| events none of whose nodes is an asset | no graph in the portal, the events posted | measured 2026-10-19, Stage 18 7.1 run B |
| dataset names that do not resolve to an asset's `sourceIdentifier` | nodes that stand apart from the asset | read (the troubleshooting page); dbt's names resolve through the symlink, measured 2026-11-21 (Stage 20 vi, `SUP-391`) |
| the wrapper's post refused, rejected or unreachable | the task `SUCCESS`, exit 0, a warning per event that prints the whole event; 60 s more per event when unanswered | measured 2026-11-21, Stage 20 3.3 (ix) |
| an event about another project's dataset | a version of that dataset's node, drawn on its asset's tab | measured 2026-11-21, Stage 20 3.4 (xi), `SUP-402` |
| a dbt seed | no event, and no input edge into the model that reads it | simulated 2026-11-08, Stage 20 0.8 |
| the Redshift connection's daily sync | a failed run each day the workgroup is down at 03:43 UTC | measured, `EXC-17` |

---

## V. The instruments

### `./aws/catalog.py`

The infrastructure user runs it, `InfrastructureAccess` in Data Governance, Sandbox, Staging and Production
(`awsds-infra-data`, `awsds-infra-sandbox-1`, `awsds-infra-staging`, `awsds-infra-prod`), one sign-in for
the four ([`AWS-CLI.md`](../../../aws/AWS-CLI.md), "Signing in"). It writes `aws/output/catalog.txt`, makes
no write, and exits 0 when every check passed, 1 when a call failed and 2 when a check failed;
`--self-check` runs the product road's rules on samples with no AWS call ([`catalog.py`](../../../aws/catalog.py)).

| Check | What it reads |
|---|---|
| `CT-1` | one domain, `AVAILABLE`, in Data Governance, and none in a consumer account |
| `CT-2` | every listing's owning project exists |
| `CT-3` | the access acts per listing: subscriptions, requests, grants |
| `CT-4` | no source publishes on import |
| `CT-5` | no source over a lake database generates names |
| `CT-6` | every scheduled run is one somebody chose, and succeeds (`EXC-11`) |
| `CT-7`, `CT-8` | the grants SMUS-managed principals hold on the lake, and the project condition on every conditioned `IAMPrincipals` grant |
| `CT-9` | no override of a project owner or a domain unit owner |
| `CT-10` | every grant on a published lake table explained, by the publishing role or by a subscription |
| `CT-11` | every access act on a lake listing went through the approval |
| `CT-12` | what the lake lists is the declared list, each table public or internal |
| `CT-13` | every source's start is its own project's |
| `CT-14` | a deployment project's sources: Glue, one per database, publishing nothing, generating nothing |
| `CT-15` | Staging lists nothing, and a chain application's `dev` project lists by exception |
| `CT-16` | the access acts on a project's product, judged by the stage that owns it |
| `CT-17` | every grant on a project's listed table explained, a table its data product's publication listed included: each product listing's items are read with `get-listing`, those `search-listings` omits among them (`SUP-482`) |
| `CT-18` | every product listing carries the `classification` form, the same tables as `CT-17`: the table's own form, or for a table with none reachable through its data products alone, every carrying product's (Stage 19 decision 4 extended 2026-11-23); any other table with no form fails, its products' forms named |
| `CT-19` | no listing publishes a resource link |
| `CT-20` | every S3 Access Grant a project role holds on another project's folder explained by an approved subscription to an S3 Object Collection at that prefix |
| `CT-21` | the lineage events of the last seven days by `processingStatus` and job namespace: a `FAILED` event fails, an empty window is a note |
| `CT-22` | each Glue table asset hangs from the node of its own table, the one its `externalIdentifier` names, fed by a job's run or, for a table a subscription created, by the listing's node; in a deployment project a node nothing fed, or no node, fails (`SUP-097`), and another account's node is a note (`SUP-483`), the import's window when the forms name that table (`SUP-454`) |
| `CT-23` | every Glue table node the registry's trail created is carried by an asset; a node carried by none is a note |
| `CT-24` | a deployment project's asset carries the description, README and `classification` of its table's asset in a chain application's `dev` project, and its forms name its own account's table; a difference, or the import's window, is a note (Stage 20 xxi) |

The last run: 2026-11-24 from 00:54 to 00:55 UTC, every check passed, 15 `pass` and 10 `note`, 12 listings
and none of `deploy-staging`. `CT-21` passed on 279 events in seven days, each `SUCCESS`; `CT-22` to `CT-24`
are notes on the import's window, the four target `app-dbt` assets and Staging's `trades_notional` naming and
hanging from Sandbox's tables until the targets' sources run again (Stage 20's log). `--self-check` read 62 of
62 on 2026-11-24, and `aws/tests/test_catalog_lineage.py` holds the lineage rows' cases.

### The CLI's reads, object by object

Every `aws datazone` call takes `--domain-identifier dzd-d8yrvx1ko7im6o`, and every call
`--region us-west-2`. With the tunnel down, macOS's
system proxy breaks the CLI, and `NO_PROXY='*'` is the override
([`client-vpn-proxy-configuration.md`](client-vpn-proxy-configuration.md)).

| Object | Read with | Who is answered |
|---|---|---|
| Projects, members, environments | `list-projects`, `list-project-memberships`, `list-environments` | any associated account's `InfrastructureAccess` (`SUP-157`) |
| Assets | `search --search-scope ASSET --owning-project-identifier <project>`, `get-asset`, `list-asset-revisions` | a member of the project (6f 0.6) |
| Listings | `search-listings`, `get-listing`, whose forms come as a JSON string; the latest revision, never the answered one (`SUP-345`) | every domain user |
| Data products | `search --search-scope DATA_PRODUCT --owning-project-identifier <project>`, the project mandatory (`SUP-371`); `get-data-product` | a member of the project |
| Data sources and runs | `list-data-sources`, `get-data-source`, `list-data-source-runs`, `get-data-source-run`, `list-data-source-run-activities` | a non-member too (`SUP-157`) |
| Subscriptions | `list-subscriptions`, `list-subscription-requests` (a product's under its listing's id and its assets'), `list-subscription-grants`, `get-subscription-grant`, `list-subscription-targets` (`SUP-363`) | read in Data Governance by its `InfrastructureAccess`, a member of none (`SUP-363`) |
| Forms | `get-form-type`, whose `createdAt` is the newest revision's (`SUP-344`) | a non-member too |
| The domain unit's grants | `list-policy-grants` | Data Governance's `InfrastructureAccess` |
| Lineage | `list-lineage-events`, `get-lineage-node`, `list-lineage-node-history` | the reads every domain user holds, and `ListLineageEvents` with its own allow |
| The fulfilment | `aws lakeformation list-permissions` in the table's account; `aws glue get-table` on a link (its `TargetTable`); `aws glue get-resource-policies`; `aws ram get-resource-shares` | the account's `InfrastructureAccess` |

### The trail each act lands in

| Act | Trail | As whom |
|---|---|---|
| A portal act on the catalog: a publish, a request, an approval, a revocation, a form, a source's delete | Data Governance's | the domain execution role in the person's session (6f 0.5; `SUP-191`, `SUP-344`, `SUP-362`, `SUP-366`) |
| A lineage node's creation | Data Governance's, its id and `sourceIdentifier` in `additionalEventData` | `datazone.amazonaws.com` (`SUP-191`, `SUP-347`) |
| A fulfilment, and a revocation's removal of it | the account that holds the table, and the consumer's | the project roles' `AWSDataZone-Subscriptions` sessions, no `aws:SourceIdentity` (`SUP-194`, `SUP-195`, `SUP-365`) |
| A source's run | the project's account | the project role's `SYSTEM` session, `aws:SourceIdentity` `SYSTEM` (`SUP-194`) |
| A `PostLineageEvent` | the poster's account and Data Governance's, one shared event | the poster (Stage 19 xxi) |

How to read a trail for an act whose door is in question: [`log-debugging.md`](log-debugging.md).
