#!/usr/bin/env -S uv run --quiet
"""catalog.py - the SageMaker Catalog over the governed lake: what the business catalog holds, what
             it has granted, and which Lake Formation grants a SMUS-managed principal carries.

needs:    a live SSO session for the infrastructure user; one login covers every profile:

              aws sso login --sso-session awsds

run:      ./aws/catalog.py
          ./aws/catalog.py --self-check   # the product road's rules on samples, no AWS call
writes:   aws/output/catalog.txt   (untracked - see .gitignore)
reads:    in Data Governance - datazone:ListDomains, GetDomain, ListProjects,
          ListProjectMemberships, ListEnvironments, GetUserProfile, GetGroupProfile,
          SearchListings, GetListing, ListDataSources, GetDataSource, ListDataSourceRuns,
          ListSubscriptions, ListSubscriptionRequests, ListSubscriptionGrants,
          ListPolicyGrants, ListLineageEvents, GetLineageNode, ListLineageNodeHistory,
          lakeformation:GetResourceLFTags, ListLFTags; in Sandbox -
          lakeformation:ListLFTags; in each account read - lakeformation:ListPermissions and
          cloudtrail:LookupEvents; in the account a project's environments live in -
          datazone:Search over that project's assets and glue:GetTable; in Sandbox -
          s3:ListAccessGrants and ListAccessGrantsLocations; and sts:GetCallerIdentity. Every
          one is a read.
exits:    0 every check passed | 1 a call failed | 2 a check FAILED, or a --self-check case
          read otherwise
"""

# THE TWO ROADS AN ACCESS ACT CAN TAKE, which is what this script exists to keep apart. On the
# catalog road a subscription or a direct Share is approved in the portal and DataZone writes a Lake
# Formation grant in the account that owns the table (INT-23). On the register road a grant is
# written by Terraform and carries a row in docs/AWS_STATE.md's grant register. Since Stage 6f
# decision 2 (2026-10-27) the catalog road's grants on the lake are registered by reading: DataZone's
# subscription is each grant's record, and CT-10 is the join that fails on a grant no subscription
# explains. Section 5 reads Lake Formation, section 6 the road's records, and CT-7 and CT-10 are the
# comparison.
#
# The catalog road has a second end since Stage 19, the product's: a project lists a table of its
# own database, in the account its environments live in, and DataZone fulfils a subscription there
# as the owning project's role (SUP-195). Stage 19 decision 11 keeps a Sandbox project's fulfilments
# outside the register, DataZone's subscription their record, and gives Production's one register
# row by class. Section 7 reads that end, and CT-15 to CT-19 are its checks.
#
# The checks:
#   CT-1  one domain, AVAILABLE, in the registry account - and no domain in the consumer account
#         (D26: the registry and the runtimes are different accounts).
#   CT-2  every listing names an owning project that exists, and its type is reported.
#   CT-3  the access acts: subscriptions, requests and grants per listing. Subscriptions exist
#         since 2026-10-26 (6f step 11); CT-7 is what says whether each is registered.
#   CT-4  no data source publishes on import. A publish that happens at import time is a listing
#         nobody reviewed, and publishOnImport is the only switch that does it.
#   CT-5  no data source over a lake database generates business names with AI. Stage 6f
#         decision 3 (2026-10-27) keeps the generation off on every source over the governed
#         lake; no IAM condition key reaches the flag, so this reading is the only place the
#         setting is checked. The portal's Publish to Catalog creates its source with the flag on,
#         so each publish is followed by update-data-source. Sources over a project's own
#         database are the project's choice and are listed in the detail.
#   CT-6  every scheduled data source run is one somebody chose, AND succeeds. A blueprint-created
#         data source on a cron nobody wrote is Lesson 17's shape; one whose completed runs have all
#         failed is EXC-11's, and the live `status` field does not show it - a run's stoppedAt is its
#         successor's startedAt, so a daily source reads RUNNING however long it has been failing.
#         The exception is by name and each project's Tooling environment creates one source, so
#         the note prints how many sources it covered.
#   CT-7  no SMUS-managed principal holds a grant on a lake database, a lake table or an LF-Tag,
#         but on the catalog road. The design reads the lake through TBAC re-grants to a persona
#         (GOVERNANCE.md §Grants), so a project role or a conditioned IAMPrincipals entry reaching
#         `raw`, `curated` or `dropbox` is a second road into governed data with no row in the
#         register. Since Stage 6f decision 1 (2026-10-26) one such road is designed: a table in
#         PUBLISHED_LAKE_TABLES carries the publishing project role's grant and the grants DataZone
#         fulfils, which this check lists as a note; CT-10 judges each of them. Any other SMUS
#         grant on the lake fails as before.
#   CT-8  every conditioned IAMPrincipals grant carries the project condition. An unconditioned
#         one grants the whole account, which is what that principal means without a Condition.
#   CT-9  nobody may override a project owner or a domain unit owner. The owner project's approval
#         is the control on the catalog road; an override grant removes it.
#   CT-10 every grant on a published lake table is explained, whatever its principal: the
#         publishing project role's read with the grant option (data/publishing.tf), the
#         administrator's and creator's, or a fulfilment - SELECT or DESCRIBE, no grant option, to
#         the consumer account's IAMPrincipals under the context of a project that holds an
#         APPROVED subscription to the table's listing with a COMPLETED grant. Stage 6f decision 2
#         (2026-10-27) makes DataZone's subscription the per-grant record of the catalog road and
#         this join its register. The publishing role may regrant what it holds with the grant
#         option in any session (SageMakerStudioProjectUserRolePolicy's LFResourceSharingPermissions
#         allows lakeformation:BatchGrantPermissions on * with no condition, read 2026-10-27), so a
#         grant no subscription explains is the finding.
#   CT-11 every access act on a lake listing went through the approval. Stage 6f decision 5
#         (2026-10-27) allows no direct Share on the lake: each APPROVED subscription to a lake
#         listing is a project's, comes from an ACCEPTED request whose requester is no member of
#         the owning project and whose reviewer is its owner, and the listing requires approval.
#         The owning project's members are its owner, an Identity Center user, its own project
#         role and this account's InfrastructureAccess: a member can approve, and holds the
#         project role's sessions.
#   CT-12 what the lake publishes is the declared list, and each table on it is public or
#         internal on the table and on every column (Stage 6f decision 2, 2026-10-27). DataZone
#         fulfils by name and reads no LF-Tag, so a restricted column on a published table would
#         reach every subscriber whole; restricted and personal tables travel on TBAC grants
#         alone.
#   CT-13 every start of a data source is its own project's. DataZone admits a project role's
#         StartDataSourceRun on another project's source, and IAM reaches the action at the
#         domain alone (SUP-346); Stage 19 decision 17 keeps the grant the publishing task
#         needs on Production's deployment project role alone, and the check judges each start
#         CloudTrail holds, in the registry, the Interactive account and, since their projects
#         exist, both deployment targets. A deploy role holds the start for a target's second
#         import (decision 25) and is judged against its deployment project.
#   CT-14 a deployment project's sources are Glue sources, one per database, publishing nothing
#         on import and generating no names (Stage 19 step 4.6). CT-5 leaves the generation over a
#         project's own database to the project; a deployment project has no person to choose,
#         and the generation is a model call over the target's metadata.
#   CT-15 Staging's project lists nothing, and a chain application's `dev` project lists by
#         exception. The domain is one catalog for every account, so a listing offers its table
#         to every project's search: Stage 19 decisions 14 and 19 (c) keep Staging's sample data
#         unlisted, and decision 20 (b) lists a chain application's product in Production alone.
#         That gate is the template's default and no control, since a member's portal publish
#         lists, so a listing a project in CHAIN_DEV_PROJECTS owns is a note. Every listing type
#         counts.
#   CT-16 the access acts on a project's product, judged by the stage that owns it. A deployment
#         project subscribes to nothing (decisions 13 and 14): the Workloads SCP denies a
#         target's own request, and an owner's Share made for one is the owner's call, which
#         this reading alone sees. On a listing a deployment project owns, CT-11's rules hold
#         with decision 15's approver: each APPROVED subscription is a project's, from an
#         ACCEPTED request whose requester is no member of the owning project and whose
#         reviewer is a person among its members or its InfrastructureAccess session group. A
#         Sandbox project shares its product as SMUS lets it (decision 20 (b)): those acts are a
#         note naming each one's shape, the owner's Share among them (SUP-362).
#   CT-17 every grant on a project's listed table is explained: the owning project's role; the
#         blueprint's grants on the project's database, to its members under the project's own
#         context and to SMUS's two roles; or a fulfilment - SELECT or DESCRIBE on the table by
#         name, no grant option, to the IAMPrincipals of the account a project lives in, under
#         the context of that project, which holds an APPROVED subscription with a COMPLETED
#         grant to the table's listing or to a data product that carries it. This is CT-10's
#         join made in the account that holds the table: the same account for two Sandbox
#         projects, Production's for its product read from Sandbox (decision 11).
#   CT-18 every product listing carries the classification form, public or internal (decision
#         4). This is CT-12's rule read from the catalog, since a project's table carries no
#         LF-Tag and DataZone fulfils by name. A listing with no form fails, but one named in
#         UNCLASSIFIED_BY_EXCEPTION, which is a note, and one reachable through its data
#         products alone, which takes every carrying product's form (decision 4 extended
#         2026-11-23).
#   CT-19 no listing publishes a resource link. A consumer's source imports the link its
#         subscription created as an inventory asset (Stage 19 0.5); published, it would list
#         another owner's table under the consumer's name. CT-4 keeps every source from
#         publishing on import, and this check reads what a person published: a listed link
#         fails, and an inventory link is a note, a member's publish being one act away.
#   CT-20 every S3 Access Grant a project role holds on another project's folder is explained by
#         an APPROVED subscription of that project to an S3 Object Collection the folder's project
#         lists, at exactly the collection's prefix (Stage 21 6.3). DataZone fulfils a collection
#         with a grant on the owning project's location to the subscriber's project role, written
#         by the owner's role in session AWSDataZone-Subscriptions, READ for a product's
#         subscription and what the request asked for on the collection's own listing (Stage 21
#         5.4, 5.6). A grant to a person's role, or on a location no project owns, is the
#         sandbox lake's and outside this check.
#   CT-21 the lineage events posted in the last LINEAGE_WINDOW_DAYS days, by processingStatus and
#         job namespace (Stage 20 step 6.1). A FAILED event is a run whose nodes the domain did not
#         write, and fails; an empty window is a note.
#   CT-22 each Glue table asset hangs from the dataset node keyed by its own table, the table its
#         externalIdentifier names, and a job's run wrote that node or, for the table a
#         subscription created, the listing's node feeds it (Stage 20 6.1, verification xx). A
#         deployment project's tables are a release run's outputs, so there a node nothing fed, or
#         no node at all, is a run that posted no lineage (SUP-097) and fails; in any other
#         project it is a table no instrumented engine wrote, a note. An asset hanging from
#         another account's node of the same table is a note (SUP-483), the import's window when
#         its forms name that table too (SUP-454).
#   CT-23 every Glue table node is carried by an asset: a node no asset's node hangs from is a
#         note, the target's own node SUP-483 leaves behind among them (Stage 20 6.1).
#   CT-24 a deployment project's Glue table asset carries the description, README and
#         classification of the asset of the same table in a chain application's dev project, and
#         its forms name its own account's table (Stage 20 xxi). The release's catalog import
#         carries the curation, and the dev project may curate again before the next release, so
#         a difference is a note; forms naming another account's table are the import's window,
#         which the target's source closes at its next run (SUP-454).
#
# CT-7 and CT-8 read every page of ListPermissions in the registry, in the Interactive account
# and, since their projects exist, in both deployment targets: the CLI has no paginator for that
# operation, so one call answers the first page and a NextToken. A listing not read to its last
# page leaves both checks a note, never a pass; a grant it did read still fails them. In a target
# the lake is the resource links `raw` and `curated`, and a SMUS grant on one is CT-7's finding
# there too; the catalog road CT-7 admits is the registry's and the Interactive account's alone.
#
# What it cannot see (0.6, measured 2026-09-13 and again 2026-10-18): DataZone refuses GetAsset and
# GetDataProduct to InfrastructureAccess in Data Governance, the session this script reads the
# domain with, so the asset behind a listing is read through GetListing or not at all. The refusal
# is the project-membership check: the Sandbox session, a contributor of both projects since
# 2026-10-15, is answered. ListPolicyGrants is refused for two policy types on the same ceiling;
# those cells read DENIED rather than empty, because an empty listing and a refused read are
# different facts. Lake Formation lists no grant to an Identity Center principal (Stage 6f,
# measured in Sandbox 2026-10-20 and 2026-10-21): the provisioning role grants
# `arn:aws:identitystore:::user/*` on a project's database and its tables under the project
# condition (CloudTrail BatchGrantPermissions, no failure), ListPermissions by resource omits it,
# and asked for that principal it answers InvalidInputException, "LakeFormation Identity Center
# Configuration not configured for requested catalog". CT-7, CT-8 and CT-10 judge the role and
# IAMPrincipals grants alone; a grant to an Identity Center user is read in CloudTrail or not at
# all. A subscription that would be fulfilled for one is a user's or a group's, which CT-11 fails
# from DataZone's own record.
#
# On the product road (read 2026-11-14): datazone:Search over a project's assets answers the
# session of the account the project's environments live in, for each of the seven projects, so
# an inventory is read with that session and a project with no environment is not read, which
# CT-19 says. ListSubscriptions and ListSubscriptionRequests return a data product's subscription
# under each asset listing the product carries, and ListSubscriptionGrants answers under the asset
# listing alone (SUP-363); both ids are asked. A listing of another asset type, a Bedrock model or
# a Redshift table, is on neither road: CT-15 counts it by owner and no check judges its grants.
# A product's publication lists each unpublished asset it holds INACTIVE, and SearchListings omits
# that listing (SUP-482, measured 2026-11-23): each data product listing's items are read with
# GetListing, and a Glue table among them the search did not return is judged as a listed one,
# owned by the project its listing names. One that reads INACTIVE is reachable through its products
# alone, and CT-18 reads the products' forms for it when it carries none of its own.

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from awslib import cmdline, context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "catalog.txt"

# The registry account holds the domain (D22, D26); the Interactive account holds the projects'
# compute and the Lake Formation grants SMUS writes for them.
DATA_PROFILE = "awsds-infra-data"
SANDBOX_PROFILE = "awsds-infra-sandbox-1"
# The deployment targets, each holding one project since Stage 19 step 4.6. Their trails are read
# for CT-13: a start made there is recorded with the role's name in that account alone.
STAGING_PROFILE = "awsds-infra-staging"
PROD_PROFILE = "awsds-infra-prod"
STAGING_PROJECT = "deploy-staging"
PRODUCTION_PROJECT = "deploy-production"
DEPLOYMENT_PROJECTS = (STAGING_PROJECT, PRODUCTION_PROJECT)
# Each target's deploy role, by name, and the deployment project whose source it starts (CT-13).
DEPLOY_ROLES = {"awsds-deploy-staging": STAGING_PROJECT, "awsds-deploy-prod": PRODUCTION_PROJECT}

# The projects a chain application's `dev` stage deploys from, by id (Stage 19 decision 18 (d),
# step 1.5; Stage 20 step 2.0). Decision 20 (b) lists such an application's product in Production
# alone, by the template's default: CT-15 reports a listing one of these owns as a note.
CHAIN_DEV_PROJECTS = {"ceweti7jbiu1hs": "app-etl-dev", "dnl3l158mbhrio": "app-dbt-dev"}

# The governed lake's databases, in the registry account. A SMUS principal reaching one of these is
# CT-7's finding; a project's own database is not.
LAKE_DATABASES = ("raw", "curated", "dropbox")

# The lake tables the lake-publishing pilot publishes (Stage 6f decision 1, step 11), as
# `<database>.<table>`: the same list as data-governance/data/publishing.tf's `published_tables`.
# A SMUS grant on one of these is the catalog road's; a table published there and missing here
# fails CT-7, which is the reading that keeps the two lists together (Lesson 14).
PUBLISHED_LAKE_TABLES = ("curated.trades",)

# The classifications the catalog road admits on a published table and on each of its columns
# (Stage 6f decision 2, CT-12): data/publishing.tf refuses the same at plan. CT-18 admits the same
# on a product's form.
CATALOG_ROAD_CLASSIFICATIONS = ("public", "internal")

# The metadata form that carries a product's classification, and the name of its one field (Stage
# 19 decision 4). The field is a String: the portal offers no enumerated type.
CLASSIFICATION_FORM = "classification"

# The form of a data product listing that lists its items' asset listing ids (Stage 21 5.3).
PRODUCT_ITEMS_FORM = "ownedByDataProductListing"

# A product listing with no classification form, by asset id, with the exception that records it.
# CT-18 reports these as a note and fails on any other listing without the form (Lesson 50).
# Remove a row here when its exception is closed, and CT-18 turns red the same day.
UNCLASSIFIED_BY_EXCEPTION: dict = {}

# What each kind of principal may hold on a published table (CT-10). The publisher holds the read
# with the grant option, which DataZone's terms for a Glue table require; a fulfilment is read-only
# and carries no grant option.
PUBLISHER_PERMISSIONS = frozenset({"DESCRIBE", "SELECT"})
FULFILMENT_PERMISSIONS = frozenset({"DESCRIBE", "SELECT"})

# The registry account's administrator, which also creates the lake's tables and holds the
# creator's permissions on them (AWS_STATE.md, the note under the grant register).
ADMIN_ROLE_MARKER = "AWSReservedSSO_InfrastructureAccess_"

# A data source name embeds the account id of its catalog; this mask keeps it out of the report.
ACCOUNT_ID = re.compile(r"\b\d{12}\b")

# What makes a principal SMUS-managed. The service names its own roles by prefix and writes the
# account-wide entry as `<account>:IAMPrincipals`, which is a grant to everyone in the account
# unless a Condition narrows it (CT-8).
PROJECT_ROLE_MARKER = "datazone_usr_role_"
# The two roles SMUS acts as in each account, which a blueprint grants on every database it creates.
BLUEPRINT_ROLE_SUFFIXES = ("-smus-provisioning", "-smus-manage-access")
SMUS_ROLE_MARKERS = (
    PROJECT_ROLE_MARKER,
    *BLUEPRINT_ROLE_SUFFIXES,
    "AmazonDataZone",
)
IAM_PRINCIPALS_SUFFIX = ":IAMPrincipals"

# A SMUS project's S3 Access Grants location, `s3://<projects bucket>/<domain id>/<project id>/`
# (SMUS.md, the vending surface), and a project role by the project id its name carries (CT-20).
PROJECT_LOCATION = re.compile(r"s3://[^/]+/dzd[-_][a-z0-9]+/([a-z0-9]+)/")
PROJECT_ROLE = re.compile(r":role/" + PROJECT_ROLE_MARKER + r"([a-z0-9]+)_[a-z0-9]+$")
S3_COLLECTION_TYPE = "S3ObjectCollectionAssetType"
S3_COLLECTION_FORM = "S3ObjectCollectionForm"

# The shape of a DataZone user profile id. A request's requester or reviewer of another shape, an
# absent reviewer among them, is not looked up.
PROFILE_ID = re.compile(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")

# The policy types ListPolicyGrants accepts on a domain unit. The four it rejects for that entity
# type are not asked for: a ValidationException is a fact about the API, not about this domain.
DOMAIN_UNIT_POLICY_TYPES = (
    "CREATE_PROJECT",
    "CREATE_PROJECT_FROM_PROJECT_PROFILE",
    "CREATE_DOMAIN_UNIT",
    "CREATE_GLOSSARY",
    "CREATE_FORM_TYPE",
    "CREATE_ASSET_TYPE",
    "ADD_TO_PROJECT_MEMBER_POOL",
    "OVERRIDE_DOMAIN_UNIT_OWNERS",
    "OVERRIDE_PROJECT_OWNERS",
)

# A scheduled data source already known to fail, with the exception that records it. The exemption is
# by name, so it covers every source of that name, and each project's Tooling environment creates one:
# CT-6 prints how many sources it covered, and the project of each. CT-6 reports these as a note and
# fails on anything else, so the check stays readable while the exception stands (Lesson 50). Remove
# a row here when its exception is closed, and CT-6 turns red the same day.
FAILING_BY_EXCEPTION: dict[str, str] = {}

# Starts of another project's source made on purpose, by the event's request id. CT-13 reports these
# as a note and fails on any other cross-project start (Lesson 50). CloudTrail's event history keeps
# 90 days: remove an entry once lookup-events no longer returns its event.
MEASURED_CROSS_PROJECT_STARTS = {
    "01d1d646-13a9-434c-848c-13df03911521": (
        "Stage 19 verification ii's negative, eighth-experimentation's role starting "
        "test-experimentation's source on 2026-11-10 (SUP-346)"
    ),
}

# The two that must stay empty for the owner project's approval to be the control (CT-9).
OVERRIDE_TYPES = ("OVERRIDE_DOMAIN_UNIT_OWNERS", "OVERRIDE_PROJECT_OWNERS")

# The days back from the run CT-21 reads ListLineageEvents over.
LINEAGE_WINDOW_DAYS = 7
# A job's run carries the edges into and out of a dataset node; an asset's node is a dataset node
# that answers to `amazon.datazone.asset/<asset id>` (SUP-347). A listing's node answers to
# `amazon.datazone.listing/<listing id>`, and the table a subscription's fulfilment creates hangs
# from it (the Stage 6f and Stage 20 logs, 2026-11-22).
JOB_RUN_NODE_TYPE = "amazon.datazone.JobRunLineageNodeType"
DATASET_NODE_TYPE = "amazon.datazone.DatasetLineageNodeType"
ASSET_NODE_PREFIX = "amazon.datazone.asset/"
LISTING_NODE_PREFIX = "amazon.datazone.listing/"
# The versions of a dataset node CT-22 reads, newest first, for the run that wrote it: a dbt test's
# version carries no upstream edge (Stage 20 2.4), the model's run before it does.
LINEAGE_VERSIONS_READ = 20
# A Glue table's ARN: the sourceIdentifier of the dataset node the domain keys a table by
# (SUP-391), and of an asset's AssetCommonDetailsForm; with `.<project id>` after it, a Glue table
# asset's externalIdentifier (SUP-343).
GLUE_TABLE_ARN = re.compile(r"arn:aws:glue:[a-z0-9-]+:(\d{12}):table/([^/]+)/([^/]+)")


def json_or_none(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def is_smus_principal(identifier: str) -> bool:
    """True for a principal the SMUS service created or writes grants for."""
    if identifier.endswith(IAM_PRINCIPALS_SUFFIX):
        return True
    return any(m in identifier for m in SMUS_ROLE_MARKERS)


def short_principal(identifier: str) -> str:
    """A principal without its account id, which may not appear in a tracked file."""
    if identifier.endswith(IAM_PRINCIPALS_SUFFIX):
        return "ACCOUNT:IAMPrincipals"
    if ":role/" in identifier:
        return "role/" + identifier.split(":role/", 1)[1].rsplit("/", 1)[-1]
    if identifier.count(":") == 0 and identifier.isdigit():
        return "ACCOUNT"
    return identifier


def resource_of(resource: dict) -> tuple[str, str]:
    """(kind, name) of a Lake Formation resource, with the database it belongs to when it has one."""
    if not resource:
        return ("-", "-")
    kind = next(iter(resource))
    body = resource[kind] or {}
    if kind == "Database":
        return (kind, body.get("Name", "-"))
    if kind in ("Table", "TableWithColumns"):
        name = body.get("Name") or ("ALL_TABLES" if body.get("TableWildcard") is not None else "-")
        return (kind, f"{body.get('DatabaseName', '-')}.{name}")
    if kind == "DataLocation":
        arn = body.get("ResourceArn", "-")
        return (kind, arn.replace("arn:aws:s3:::", ""))
    if kind == "LFTag":
        return (kind, body.get("TagKey", "-"))
    if kind == "LFTagPolicy":
        expr = body.get("Expression") or []
        return (kind, " AND ".join(f"{e.get('TagKey')}∈{e.get('TagValues')}" for e in expr) or "-")
    if kind == "DataCellsFilter":
        # A subscription approved with row or column filters is fulfilled as SELECT on one data
        # cells filter over the table, so the filter is read as a grant on that table.
        return (kind, f"{body.get('DatabaseName', '-')}.{body.get('TableName', '-')}")
    return (kind, "-")


TABLE_KINDS = ("Table", "TableWithColumns", "DataCellsFilter")


def mask_account(text: str) -> str:
    """A name without the account id DataZone embeds in it."""
    return ACCOUNT_ID.sub("ACCOUNT", text)


def condition_project(expression: str) -> str:
    """The project id a SMUS grant's Cedar condition names, or empty when it names none."""
    m = re.search(r'context\.datazone\.projectId\s*==\s*"([^"]+)"', expression or "")
    return m.group(1) if m else ""


def listing_forms(body: dict) -> dict:
    """GetListing's forms, which the API returns as a JSON string inside the asset listing or the
    data product listing."""
    item = body.get("item") or {}
    raw = (item.get("assetListing") or item.get("dataProductListing") or {}).get("forms")
    if isinstance(raw, dict):
        return raw
    return json_or_none(raw) or {}


def product_items(body: dict) -> list:
    """The asset listing ids a data product listing carries, from GetListing's answer: its items
    and its forms' ownedByDataProductListing, which named the same listings on 2026-11-23."""
    product = (body.get("item") or {}).get("dataProductListing") or {}
    ids = [entry.get("listingId") for entry in product.get("items") or []]
    owned = listing_forms(body).get(PRODUCT_ITEMS_FORM)
    ids += owned if isinstance(owned, list) else []
    return list(dict.fromkeys(i for i in ids if isinstance(i, str) and i))


def explain_grant(
    row: tuple,
    registry_account: str,
    consumer_account: str,
    listed_owner: str,
    fulfilled_projects: set,
) -> str:
    """Why a grant on a published lake table exists, or empty when nothing explains it (CT-10).

    `row` is a section-5 grant row; `listed_owner` the project that owns the table's listing, empty
    before the table is listed; `fulfilled_projects` the projects holding an APPROVED subscription
    to that listing whose grant is COMPLETED."""
    _, ident, _, _, perms, grantable, cond = row
    held = set(perms.split("+")) if perms != "-" else set()
    regrant = set(grantable.split("+")) if grantable != "-" else set()
    if ADMIN_ROLE_MARKER in ident and f":{registry_account}:" in ident:
        return "the administrator, the table's creator"
    if f":{registry_account}:role/{PROJECT_ROLE_MARKER}" in ident:
        project = ident.split(f":role/{PROJECT_ROLE_MARKER}", 1)[1].split("_", 1)[0]
        if listed_owner and project != listed_owner:
            return ""
        if held <= PUBLISHER_PERMISSIONS and regrant <= PUBLISHER_PERMISSIONS:
            return "the publishing project role's declared read (data/publishing.tf)"
        return ""
    if ident.endswith(IAM_PRINCIPALS_SUFFIX):
        account = ident[: -len(IAM_PRINCIPALS_SUFFIX)]
        project = condition_project(cond)
        if (
            account == consumer_account
            and project in fulfilled_projects
            and held <= FULFILMENT_PERMISSIONS
            and not regrant
        ):
            return f"the fulfilment of {project}'s approved subscription"
    return ""


def road_problems(
    lake_listings: list,
    subscriptions: list,
    requests: dict,
    members: dict,
    profiles_by_id: dict,
) -> list:
    """What breaks CT-11's rule on the lake road, one sentence per finding.

    `lake_listings` holds (listing id, table, owning project, approvalRequired); `subscriptions`
    (listing id, table, subscription id, status, principal kind, project id, request id);
    `requests` maps an ACCEPTED request id to (requester, reviewer); `members` maps a project id
    to its (kind, member id, designation, principal ARN or "-") rows; `profiles_by_id` maps a
    user profile id to (type, IAM ARN or "-")."""
    problems = []
    owner_of = {lid: owner for lid, _, owner, _ in lake_listings}
    for lid, table, owner, approval in lake_listings:
        if approval != "YES":
            problems.append(
                f"{table}'s listing reads approvalRequired {approval}: every request is approved at creation"
            )
    for project, rows in members.items():
        owners = [r for r in rows if r[2] == "PROJECT_OWNER"]
        if (
            len(owners) != 1
            or owners[0][0] != "user"
            or profiles_by_id.get(owners[0][1], ("-",))[0] != "SSO"
        ):
            problems.append(f"{project} has {len(owners)} owner(s), not one Identity Center user")
        for kind, mid, designation, arn in rows:
            if designation == "PROJECT_OWNER":
                continue
            own_role = (
                kind == "user"
                and f":role/{PROJECT_ROLE_MARKER}{project}_"
                in profiles_by_id.get(mid, ("-", "-"))[1]
            )
            admin_group = kind == "group" and ADMIN_ROLE_MARKER in arn
            if designation != "PROJECT_CONTRIBUTOR" or not (own_role or admin_group):
                problems.append(
                    f"{project} counts a member outside the design: {kind} {mid} as {designation}"
                )
    for lid, table, sid, status, kind, project, rid in subscriptions:
        if status != "APPROVED":
            continue
        if kind != "project":
            problems.append(
                f"subscription {sid} to {table} is a {kind}'s: Lake Formation lists no grant to an Identity Center principal"
            )
            continue
        if rid not in requests:
            problems.append(
                f"subscription {sid} to {table} has no ACCEPTED request: a direct Share"
            )
            continue
        requester, reviewer = requests[rid]
        owner = owner_of.get(lid, "")
        rows = members.get(owner, [])
        member_ids = {mid for k, mid, _, _ in rows if k == "user"}
        member_roles = {arn for k, _, _, arn in rows if k == "group" and arn != "-"}
        requester_arn = profiles_by_id.get(requester, ("-", "-"))[1]
        if requester in member_ids or requester_arn in member_roles:
            problems.append(
                f"subscription {sid} to {table} was requested by a member of {owner}: a Share or a self-approval"
            )
        owner_ids = {mid for k, mid, d, _ in rows if k == "user" and d == "PROJECT_OWNER"}
        if reviewer not in owner_ids:
            problems.append(
                f"subscription {sid} to {table} was approved by {reviewer}, not by {owner}'s owner"
            )
    return problems


class Product(NamedTuple):
    """A listing of a project's own Glue table: the product end of the catalog road."""

    listing: str  # the asset listing's id
    name: str
    where: str  # the label of the account whose catalog holds the table; "elsewhere" when unread
    account: str  # that account's id
    table: str  # "<database>.<table>"
    owner: str  # the owning project's id
    approval: str  # SubscriptionTermsForm's approvalRequired
    classification: str | None  # the classification form's value; None with no form
    asset: str  # the asset's id
    # True for a listing SearchListings omits that reads INACTIVE: a data product's publication
    # listed it, reachable through the product alone (SUP-482).
    product_only: bool = False


def classification_value(forms: dict) -> str | None:
    """What a listing's classification form reads: None with no form, empty with no value."""
    form = forms.get(CLASSIFICATION_FORM)
    if not isinstance(form, dict):
        return None
    return str(form.get(CLASSIFICATION_FORM) or "")


def classification_findings(
    products: list, exceptions: dict | None = None, carried: dict | None = None
) -> tuple:
    """CT-18's readings, as (problems, excepted): one sentence per listing that breaks the rule,
    and the Product rows the exceptions cover, UNCLASSIFIED_BY_EXCEPTION unless given. `carried`
    maps an asset listing id to the (name, classification) of each data product listing that
    carries it. A listing is judged by its own form (Stage 19 decision 4); one with none that is
    reachable through its products alone by every carrying product's form (decision 4 extended
    2026-11-23); any other with none fails, its products' forms named."""
    exceptions = UNCLASSIFIED_BY_EXCEPTION if exceptions is None else exceptions
    carried = carried or {}
    problems = []
    excepted = []
    for p in products:
        carriers = carried.get(p.listing, [])
        if p.classification is None and p.asset in exceptions:
            excepted.append(p)
        elif p.classification is None and p.product_only:
            if not carriers:
                problems.append(f"{p.name} ({p.table}) carries no classification form")
            for name, value in carriers:
                if value is None:
                    problems.append(
                        f"{p.name} ({p.table}) carries no classification form, nor does its "
                        f"data product {name}"
                    )
                elif value not in CATALOG_ROAD_CLASSIFICATIONS:
                    problems.append(
                        f"{p.name} ({p.table}) is classified {value or 'with an empty value'} "
                        f"by its data product {name}"
                    )
        elif p.classification is None:
            products_read = "; ".join(
                f"its data product {name} reads "
                + ("no form" if value is None else value or "an empty value")
                for name, value in carriers
            )
            problems.append(
                f"{p.name} ({p.table}) carries no classification form"
                + (f" ({products_read})" if products_read else "")
            )
        elif p.classification not in CATALOG_ROAD_CLASSIFICATIONS:
            problems.append(
                f"{p.name} ({p.table}) is classified {p.classification or 'with an empty value'}"
            )
    return problems, excepted


def classification_label(p: Product, carried: dict) -> str:
    """What CT-18 reads as a listing's classification: its own form's value, or each carrying
    product's for a listing reachable through its products alone."""
    if p.classification is None and p.product_only:
        by_product = ", ".join(
            f"{'no form' if value is None else value or 'empty'} by its data product {name}"
            for name, value in carried.get(p.listing, [])
        )
        return by_product or "NO FORM"
    return "NO FORM" if p.classification is None else p.classification or "EMPTY"


def road_listings(listings: list, read, registry_account: str, where_of: dict) -> tuple:
    """The listings both ends of the catalog road judge, as (lake listings, products, bundles,
    product classifications, unread).

    `listings` holds section 2's rows, SearchListings's; `read` answers GetListing's body for a
    listing id, None when the read failed; `where_of` maps an account id to its label. A Glue
    table listing is the lake's when its table form names a lake database in the registry
    account's catalog, and a project's product when it names any other table. A data product
    listing is read for the asset listings it carries and for its classification form. Each
    carried listing SearchListings did not return is read the same way: a product's publication
    lists an unpublished table INACTIVE, reachable through the product alone (SUP-482). Such a
    listing is owned by the project its own record names, or else by the product's owner, is
    marked product_only when it reads INACTIVE, and is on neither road with no Glue table form.
    `unread` holds "GetListing <id>" per failed read.

    Lake listings are (listing id, "<db>.<table>", owning project, approvalRequired); products
    are Product rows; bundles map an asset listing id to the data product listings that carry
    it; product classifications map a data product listing id to its form's value, None with no
    form."""
    lake: list = []
    products: list = []
    bundles: dict = {}
    product_classes: dict = {}
    unread: list = []
    owner_of = {lid: owner for lid, _, _, owner, _ in listings}

    def judge(lid: str, name: str, owner: str, body: dict, product_only: bool = False) -> None:
        forms = listing_forms(body)
        glue = forms.get("GlueTableForm") or {}
        table = f"{glue.get('databaseName', '-')}.{glue.get('tableName', '-')}"
        approval = (forms.get("SubscriptionTermsForm") or {}).get("approvalRequired", "-")
        catalog = glue.get("catalogId") or "-"
        if catalog == registry_account and glue.get("databaseName") in LAKE_DATABASES:
            lake.append((lid, table, owner, approval))
            return
        products.append(
            Product(
                listing=lid,
                name=name,
                where=where_of.get(catalog, "elsewhere"),
                account=catalog,
                table=table,
                owner=owner,
                approval=approval,
                classification=classification_value(forms),
                asset=((body.get("item") or {}).get("assetListing") or {}).get("assetId", "-"),
                product_only=product_only,
            )
        )

    for lid, name, etype, owner, _ in listings:
        if etype not in ("GlueTableAssetType", "DataProduct"):
            continue
        body = read(lid)
        if body is None:
            unread.append(f"GetListing {lid}")
            continue
        if etype == "DataProduct":
            product_classes[lid] = classification_value(listing_forms(body))
            for item in product_items(body):
                bundles.setdefault(item, []).append(lid)
            continue
        judge(lid, name, owner, body)
    for lid in sorted(set(bundles) - set(owner_of)):
        body = read(lid)
        if body is None:
            unread.append(f"GetListing {lid}")
            continue
        if "GlueTableForm" not in listing_forms(body):
            continue
        record = (body.get("item") or {}).get("assetListing") or {}
        owner = record.get("owningProjectId") or owner_of.get(bundles[lid][0], "-")
        judge(lid, body.get("name") or lid, owner, body, body.get("status") == "INACTIVE")
    return lake, products, bundles, product_classes, unread


def link_target(target: dict | None, where_of: dict) -> str:
    """Where a Glue resource link points, as `<account label>:<database>.<table>`, from GetTable's
    TargetTable; empty for a table that is no link. `where_of` maps an account id to its label."""
    if not target:
        return ""
    where = where_of.get(target.get("CatalogId", ""), "another account")
    return f"{where}:{target.get('DatabaseName', '-')}.{target.get('Name', '-')}"


def stage_listings(listings: list, projects: dict) -> tuple:
    """CT-15's readings, as (staging, dev): the listings Staging's project owns and the ones a
    chain application's `dev` project owns, each as (listing name, project name). `listings`
    holds section 2's rows and `projects` maps a project id to its name."""
    staging = [
        (name, projects[owner])
        for _, name, _, owner, _ in listings
        if projects.get(owner) == STAGING_PROJECT
    ]
    dev = [
        (name, CHAIN_DEV_PROJECTS[owner])
        for _, name, _, owner, _ in listings
        if owner in CHAIN_DEV_PROJECTS
    ]
    return staging, dev


def product_acts(
    products: list,
    subscriptions: list,
    requests: dict,
    members: dict,
    profiles_by_id: dict,
    projects: dict,
    target_subscriptions: list,
) -> tuple:
    """CT-16's readings, as (problems, acts).

    `products` holds Product rows; `subscriptions`, `requests`, `members` and `profiles_by_id`
    are `road_problems`'s, over the product listings; `projects` maps a project id to its name;
    `target_subscriptions` holds (deployment project, subscription id, status, listing name).
    `problems` is one sentence per finding. `acts` holds one (subscription id, table, owner,
    subscriber, shape) per APPROVED subscription to a listing no deployment project owns."""
    problems = []
    acts = []
    for name, sid, status, listing in target_subscriptions:
        if status == "APPROVED":
            problems.append(
                f"{name} holds subscription {sid} to {listing}: a deployment project subscribes "
                "to nothing"
            )
    by_listing = {p.listing: p for p in products}
    for p in products:
        if projects.get(p.owner) in DEPLOYMENT_PROJECTS and p.approval != "YES":
            problems.append(
                f"{p.table} of {projects[p.owner]} reads approvalRequired {p.approval}: every "
                "request is approved at creation"
            )
    for lid, table, sid, status, kind, project, rid in subscriptions:
        if status != "APPROVED" or lid not in by_listing:
            continue
        owner = by_listing[lid].owner
        owner_name = projects.get(owner, owner)
        rows = members.get(owner, [])
        member_ids = {mid for k, mid, _, _ in rows if k == "user"}
        member_roles = {arn for k, _, _, arn in rows if k == "group" and arn != "-"}
        requester, reviewer = requests.get(rid, ("-", "-"))
        requester_arn = profiles_by_id.get(requester, ("-", "-"))[1]
        reviewer_type, reviewer_arn = profiles_by_id.get(reviewer, ("-", "-"))
        designed = False
        if kind != "project":
            shape = f"a {kind}'s subscription, whose grant Lake Formation does not list"
        elif rid not in requests:
            shape = "a subscription with no accepted request"
        elif requester in member_ids or requester_arn in member_roles:
            shape = "the owner's Share, a request made by a member of the owning project"
        elif (reviewer_type == "SSO" and reviewer in member_ids) or (
            ADMIN_ROLE_MARKER in reviewer_arn and reviewer_arn in member_roles
        ):
            shape = "a request approved by a person among the owning project's members"
            designed = True
        else:
            who = short_principal(reviewer_arn) if reviewer_arn != "-" else reviewer
            shape = f"a request approved by {'nobody' if who == '-' else who}"
        if projects.get(owner) in DEPLOYMENT_PROJECTS:
            if not designed:
                problems.append(f"subscription {sid} to {table} of {owner_name} is {shape}")
            continue
        subscriber = projects.get(project, project) if kind == "project" else f"a {kind}"
        acts.append((sid, table, owner_name, subscriber, shape))
    return problems, acts


def explain_product_grant(row: tuple, account: str, owner: str, fulfilled: dict) -> str:
    """Why a grant on a project's listed table exists, or empty when nothing explains it (CT-17).

    `row` is a section-5 grant row on the table or on its database's ALL_TABLES; `account` the
    account whose catalog holds the table; `owner` the project that owns the table's listing.
    `fulfilled` maps each project holding an APPROVED subscription with a COMPLETED grant, to
    that listing or to a data product that carries it, to the accounts its environments live in,
    None when they were not read."""
    _, ident, _, name, perms, grantable, cond = row
    held = set(perms.split("+")) if perms != "-" else set()
    regrant = set(grantable.split("+")) if grantable != "-" else set()
    wildcard = name.endswith(".ALL_TABLES")
    role = ident.split(":role/", 1)[1].rsplit("/", 1)[-1] if ":role/" in ident else ""
    local = f":{account}:" in ident
    if local and role.startswith(f"{PROJECT_ROLE_MARKER}{owner}_"):
        return "the owning project's role"
    if local and wildcard and role.endswith(BLUEPRINT_ROLE_SUFFIXES):
        return "SMUS's own role, the blueprint's grant on the project's database"
    if ident.endswith(IAM_PRINCIPALS_SUFFIX):
        holder = ident[: -len(IAM_PRINCIPALS_SUFFIX)]
        project = condition_project(cond)
        if holder == account and project == owner:
            return "the owning project's members, under its own context"
        if not wildcard and project in fulfilled and held <= FULFILMENT_PERMISSIONS and not regrant:
            accounts = fulfilled[project]
            if accounts is None or holder in accounts:
                return f"the fulfilment of {project}'s approved subscription"
    return ""


def classes(entries: list) -> list:
    """The classification values in a list of LF-Tag entries."""
    return [
        v
        for e in entries or []
        if e.get("TagKey") == "classification"
        for v in e.get("TagValues") or []
    ]


def table_classes(tags: dict) -> list:
    """A table's own classification, or its database's when the table carries none."""
    return classes(tags.get("LFTagsOnTable")) or classes(tags.get("LFTagOnDatabase"))


def classification_problems(table: str, tags: dict) -> list:
    """What breaks CT-12's rule on one published table, from GetResourceLFTags's answer."""
    problems = []
    on_table = table_classes(tags)
    if not on_table:
        problems.append(f"{table} carries no classification")
    for v in on_table:
        if v not in CATALOG_ROAD_CLASSIFICATIONS:
            problems.append(f"{table} is {v}")
    for col in tags.get("LFTagsOnColumns") or []:
        for v in classes(col.get("LFTags")):
            if v not in CATALOG_ROAD_CLASSIFICATIONS:
                problems.append(f"{table}.{col.get('Name', '-')} is {v}")
    return problems


def on_catalog_road(principal: str, kind: str, name: str, permissions: str) -> bool:
    """True for a SMUS grant the lake-publishing pilot designs: any grant on a published table, and
    a project role's DESCRIBE alone on the database that holds one (data/publishing.tf)."""
    if kind in TABLE_KINDS:
        return name in PUBLISHED_LAKE_TABLES
    if kind == "Database":
        holders = {t.split(".", 1)[0] for t in PUBLISHED_LAKE_TABLES}
        return name in holders and permissions == "DESCRIBE" and PROJECT_ROLE_MARKER in principal
    return False


def touches_lake(kind: str, name: str) -> bool:
    """True when a grant reaches the governed lake rather than a project's own objects."""
    if kind == "LFTag" or kind == "LFTagPolicy":
        return True
    head = name.split(".", 1)[0]
    return head in LAKE_DATABASES or any(
        name.startswith(f"awsds-data-{d}") for d in ("raw", "dropbox", "curated")
    )


def judge_start(body: dict, source_project: dict, deploy_projects: dict) -> tuple:
    """One StartDataSourceRun event for CT-13, as (verdict, caller, source id, source's project id).

    `source_project` maps a data source id to its project id, `deploy_projects` a deploy role's name
    to its deployment project's id: a deploy role is judged as that project's. The verdict is `own`, `cross`,
    `measured` (a cross-project start MEASURED_CROSS_PROJECT_STARTS names), `unknown source` (no
    source of that id is listed), `other` (a caller that is no project role: an administrator, a
    portal session, the service) or `unresolved` (a call from another account, which the domain's
    account records with that account and the role's id alone). A principal id's session part is
    dropped: an Identity Center session is named by the person's e-mail address."""
    identity = body.get("userIdentity") or {}
    source = (body.get("requestParameters") or {}).get("dataSourceIdentifier", "-")
    owner = source_project.get(source, "")
    if identity.get("type") == "AWSAccount":
        role_id = (identity.get("principalId") or "-").split(":", 1)[0]
        return ("unresolved", f"role id {role_id}", source, owner)
    issuer = ((identity.get("sessionContext") or {}).get("sessionIssuer") or {}).get("userName", "")
    if issuer in deploy_projects:
        issuer = f"{PROJECT_ROLE_MARKER}{deploy_projects[issuer]}_deploy-role"
    if not issuer.startswith(PROJECT_ROLE_MARKER):
        if identity.get("onBehalfOf"):
            who = "an Identity Center session"
        else:
            who = issuer or identity.get("invokedBy") or identity.get("type", "-")
        return ("other", who, source, owner)
    caller = issuer[len(PROJECT_ROLE_MARKER) :].split("_", 1)[0]
    if not owner:
        return ("unknown source", caller, source, owner)
    if caller == owner:
        return ("own", caller, source, owner)
    if body.get("requestID") in MEASURED_CROSS_PROJECT_STARTS:
        return ("measured", caller, source, owner)
    return ("cross", caller, source, owner)


def collection_scope(bucket_arn: str) -> str:
    """The grant scope DataZone writes for an S3 Object Collection's prefix ARN (Stage 21 5.4)."""
    prefix = "arn:aws:s3:::"
    return f"s3://{bucket_arn[len(prefix) :]}*" if bucket_arn.startswith(prefix) else ""


def explain_access_grant(location: str, grantee: str, scope: str, collections: dict) -> str | None:
    """CT-20's verdict on one S3 Access Grant. None when the check does not judge it: a location no
    project owns, or a grantee that is no project role. The reason when the grantee is the
    location's own project role, or another project's role that an APPROVED subscription to an S3
    Object Collection of the location's project, at exactly this scope, explains; empty when
    nothing does. collections maps a grant scope to (listing name, owning project, subscribed
    projects) for each S3 Object Collection listing whose prefix it is."""
    owned = PROJECT_LOCATION.fullmatch(location)
    role = PROJECT_ROLE.search(grantee)
    if not owned or not role:
        return None
    owner, holder = owned.group(1), role.group(1)
    if holder == owner:
        return "the location's own project role"
    for name, listing_owner, subscribed in collections.get(scope, ()):
        if listing_owner == owner and holder in subscribed:
            return f"the fulfilment of {holder}'s approved subscription to {name}"
    return ""


def glue_table_label(arn: str, where_of: dict) -> str:
    """'<where>:<database>.<table>' for a Glue table's ARN, an account not read labelled
    'elsewhere'; empty for anything else."""
    m = GLUE_TABLE_ARN.fullmatch(arn or "")
    if not m:
        return ""
    account, database, table = m.groups()
    return f"{where_of.get(account, 'elsewhere')}:{database}.{table}"


def asset_table_label(external_id: str, project_id: str, where_of: dict) -> str:
    """The table a Glue table asset's externalIdentifier names, `<table ARN>.<project id>`
    (SUP-343). The catalog import leaves it the target's own table while it writes the source
    project's into the forms (SUP-454)."""
    suffix = f".{project_id}"
    arn = external_id[: -len(suffix)] if external_id.endswith(suffix) else external_id
    return glue_table_label(arn, where_of)


def feeder(node: dict) -> tuple:
    """(kind, name) of a node a dataset node's version hangs from: ('job', the job a run's node
    belongs to, its name `<job>/<run id>` without the run), ('listing', the listing's name and id)
    for a subscription's table, or ('node', its name) for anything else."""
    name = mask_account(node.get("name") or node.get("sourceIdentifier") or "-")
    source = node.get("sourceIdentifier") or ""
    if node.get("typeName") == JOB_RUN_NODE_TYPE:
        return ("job", name.rsplit("/", 1)[0])
    if source.startswith(LISTING_NODE_PREFIX):
        return ("listing", f"{name} ({source[len(LISTING_NODE_PREFIX) :]})")
    return ("node", name)


def feeders(nodes: list) -> tuple:
    """(kind, names) over the nodes one version of a dataset node hangs from: 'job' when a job's
    run is among them, 'listing' when every one is a listing, 'node' otherwise; ('', '') for
    none."""
    found = [feeder(n) for n in nodes]
    if not found:
        return ("", "")
    kinds = {k for k, _ in found}
    kind = "job" if "job" in kinds else ("listing" if kinds == {"listing"} else "node")
    return (kind, ", ".join(sorted({n for _, n in found})))


def fed_by_label(kind: str, names: str) -> str:
    """The report's word for what fed a dataset node."""
    if not kind:
        return "no run"
    return names if kind == "job" else f"{kind} {names}"


def event_verdict(events: list, since: str, read: bool) -> tuple:
    """CT-21's (result, detail) over ListLineageEvents' items posted since `since`. A FAILED event
    is a run whose nodes the domain did not write; REQUESTED and PROCESSING are still in flight."""
    if not read:
        return ("note", "ListLineageEvents not read: an absence, not a pass")
    if not events:
        return ("note", f"no event since {since}: an absence, not a pass")
    statuses: dict = {}
    spaces: dict = {}
    for e in events:
        status = e.get("processingStatus") or "-"
        statuses[status] = statuses.get(status, 0) + 1
        job = ((e.get("eventSummary") or {}).get("openLineageRunEventSummary") or {}).get("job")
        space = mask_account((job or {}).get("namespace") or "-")
        spaces[space] = spaces.get(space, 0) + 1
    spread = "by job namespace " + ", ".join(f"{s} {n}" for s, n in sorted(spaces.items()))
    failed = [e for e in events if e.get("processingStatus") == "FAILED"]
    if failed:
        return (
            "fail",
            f"{len(failed)} of {len(events)} event(s) since {since} FAILED: "
            + ", ".join(e.get("id") or "-" for e in failed)
            + f" - the domain wrote no node from them; {spread}",
        )
    if set(statuses) != {"SUCCESS"}:
        counts = ", ".join(f"{n} {s}" for s, n in sorted(statuses.items()))
        return ("note", f"{counts} since {since}, the rest in flight; {spread}")
    return ("pass", f"{len(events)} event(s) since {since}, every one SUCCESS; {spread}")


class AssetLineage(NamedTuple):
    """A Glue table asset and the dataset nodes its lineage node hangs from (CT-22)."""

    project: str  # the owning project's name
    deployment: bool  # owned by a deployment project, whose tables a release's run writes
    asset: str
    own: str  # '<where>:<db>.<table>', the table its externalIdentifier names
    named: str  # the table its AssetCommonDetailsForm's sourceIdentifier names
    upstream: tuple  # (the node's table label or source, feeders' kind, feeders' names) triples
    read: bool = True  # False when its node or an upstream node's history was not read


def lineage_findings(rows: list) -> tuple:
    """CT-22's readings as (failures, notes, passes): sentences, the passes as (kind, sentence).

    An asset hangs from the node keyed by its own table, written by a job's run or, for a
    subscription's table, fed by the listing's node: the pass. In a deployment project every table
    is a release run's output, so a node nothing fed, or no node while the forms name the asset's
    own table, is a run that posted no lineage (SUP-097), a failure. Anywhere else it is a table no
    instrumented engine wrote, a note. A node of another account's table of the same name is a
    note (SUP-483), and the import's window when the forms name that table too (SUP-454)."""
    fails, notes, passes = [], [], []
    for r in rows:
        who = f"{r.asset} of {r.project}"
        if not r.read:
            notes.append(f"{who}: its lineage not read")
            continue
        window = (
            f"; its forms name {r.named}, the import's window (SUP-454)"
            if r.named and r.named != r.own
            else ""
        )
        own = [(kind, names) for table, kind, names in r.upstream if table == r.own]
        others = [(table, kind, names) for table, kind, names in r.upstream if table != r.own]
        kinds = {kind for kind, _ in own}
        if kinds & {"job", "listing"}:
            kind = "job" if "job" in kinds else "listing"
            names = ", ".join(n for k, n in own if k == kind)
            passes.append((kind, f"{who} <- {fed_by_label(kind, names)}"))
        elif "node" in kinds:
            names = ", ".join(n for k, n in own if k == "node")
            notes.append(f"{who} hangs from its table's node, fed by {names}'s node")
        elif own:
            line = f"{who} hangs from its table's node, which no job run wrote"
            if r.deployment:
                fails.append(f"{line} - the release's run posted no lineage for it (SUP-097)")
            else:
                notes.append(line)
        elif others:
            sources = ", ".join(
                f"{t}'s node" + (f" ({fed_by_label(k, n)})" if k else "") for t, k, n in others
            )
            notes.append(f"{who} hangs from {sources}, not {r.own}'s (SUP-483){window}")
        elif r.deployment and not window:
            fails.append(
                f"{who} hangs from no dataset node - the release's run posted no lineage for "
                "its table (SUP-097)"
            )
        else:
            notes.append(f"{who} hangs from no dataset node{window}")
    return fails, notes, passes


def fed_count(passes: list) -> str:
    """'<n> from their own table's job run, <m> from a subscription's listing' over CT-22's
    passes."""
    jobs = sum(1 for kind, _ in passes if kind == "job")
    return (
        f"{jobs} from their own table's job run, {len(passes) - jobs} from a subscription's listing"
    )


def lineage_verdict(rows: list, unread: list) -> tuple:
    """CT-22's (result, detail) over every Glue table asset of the inventories read."""
    fails, notes, passes = lineage_findings(rows)
    gaps = [f"the inventory of {n}" for n in unread]
    if fails:
        return ("fail", "; ".join(fails + notes))
    if not rows and not gaps:
        return ("note", "no Glue table asset in any inventory: an absence, not a pass")
    if notes or gaps:
        parts = ([f"not read: {', '.join(gaps)}"] if gaps else []) + notes + [fed_count(passes)]
        return ("note", "; ".join(parts))
    projects = len({r.project for r in rows})
    return (
        "pass",
        f"{len(rows)} asset(s) in {projects} project(s), each hanging from its own table's node: "
        + fed_count(passes),
    )


def orphan_verdict(nodes: list, carried: set, unread: list) -> tuple:
    """CT-23's (result, detail): the Glue table nodes, (node id, table label), that no asset's
    node hangs from, among those the registry's trail created."""
    orphans = sorted({(label, nid) for nid, label in nodes if nid not in carried})
    listed = ", ".join(f"{label} ({nid})" for label, nid in orphans)
    if unread:
        return (
            "note",
            f"not read: {', '.join(unread)}"
            + (f"; carried by no asset read: {listed}" if listed else ""),
        )
    if not nodes:
        return ("note", "no Glue table node in the registry's trail: an absence, not a pass")
    if orphans:
        return (
            "note",
            f"{len(orphans)} of {len({n for n, _ in nodes})} Glue table node(s) carried by no asset: {listed}",
        )
    return (
        "pass",
        f"each of the {len({n for n, _ in nodes})} Glue table node(s) carried by an asset",
    )


class Curation(NamedTuple):
    """What a person curates on an asset, and the table its forms name (CT-24)."""

    description: str
    readme: str  # AssetCommonDetailsForm's readMe
    classification: str | None  # the classification form's value; None with no form
    named: str  # '<where>:<db>.<table>' its AssetCommonDetailsForm's sourceIdentifier names


def curation_findings(pairs: list) -> tuple:
    """CT-24's readings as (notes, passes) over (deployment project, asset, own table label, its
    Curation, the dev project's name or '', the dev asset's Curation or None) rows.

    A release's catalog import carries the dev asset's description, README and classification
    (Stage 20 xxi), and the dev project's curation may move on before the next release, so a
    difference is a note, as is a deployment project's asset naming another account's table, the
    import's window (SUP-454)."""
    notes, passes = [], []
    for project, asset, own, mine, dev_project, dev in pairs:
        who = f"{asset} of {project}"
        found = []
        if dev is None:
            found.append(f"no chain application's dev project holds an asset of {own}")
        else:
            fields = [
                label
                for label, a, b in (
                    ("description", mine.description, dev.description),
                    ("README", mine.readme, dev.readme),
                    ("classification", mine.classification, dev.classification),
                )
                if a != b
            ]
            if fields:
                found.append(f"its {', '.join(fields)} differ from {dev_project}'s")
        if mine.named and mine.named != own:
            found.append(f"its forms name {mine.named}, not {own}: the import's window (SUP-454)")
        if found:
            notes.append(f"{who}: " + "; ".join(found))
        else:
            passes.append(f"{who} = {dev_project}'s")
    return notes, passes


def curation_verdict(pairs: list, unread: list) -> tuple:
    """CT-24's (result, detail) over every Glue table asset of the deployment projects read."""
    notes, passes = curation_findings(pairs)
    gaps = [f"the inventory of {n}" for n in unread]
    if not pairs and not gaps:
        return ("note", "no Glue table asset in a deployment project: an absence, not a pass")
    if notes or gaps:
        parts = ([f"not read: {', '.join(gaps)}"] if gaps else []) + notes
        return ("note", "; ".join(parts + [f"{len(passes)} as their dev asset"]))
    return (
        "pass",
        f"{len(passes)} asset(s) carry their dev asset's description, README and classification, "
        "each naming its own account's table",
    )


def self_check() -> int:
    """The product road's rules on sample records: the cases the estate cannot show before
    Production lists a product (Stage 19 step 4.12), and the ones it must never show."""
    sbx, prd = "sandbox-account", "production-account"
    own, con, lab = "ownerproject", "consumerproject", "labproject"
    owner_role = f"arn:aws:iam::{prd}:role/{PROJECT_ROLE_MARKER}{own}_env"
    admin_role = f"arn:aws:iam::{prd}:role/aws-reserved/sso/{ADMIN_ROLE_MARKER}0"
    smus_role = f"arn:aws:iam::{prd}:role/awsds-prod{BLUEPRINT_ROLE_SUFFIXES[1]}"
    there, here = f"{sbx}{IAM_PRINCIPALS_SUFFIX}", f"{prd}{IAM_PRINCIPALS_SUFFIX}"
    one, every = "app_etl.t", "app_etl.ALL_TABLES"
    fulfilment = f"the fulfilment of {con}'s approved subscription"

    def why(principal, name, perms, regrant="-", project="", account=prd, subscribed=None):
        """explain_product_grant on one sample grant on the owner's table."""
        cond = f'context.datazone.projectId=="{project}"' if project else ""
        row = ("production", principal, "Table", name, perms, regrant, cond)
        fulfilled = {con: {sbx}} if subscribed is None else subscribed
        return explain_product_grant(row, account, own, fulfilled)

    # CT-17: what explains a grant on Production's product, and what does not.
    members_grant = "the owning project's members, under its own context"
    blueprint_grant = "SMUS's own role, the blueprint's grant on the project's database"
    cases = [
        ("a cross-account fulfilment", why(there, one, "SELECT", project=con), fulfilment),
        ("a same-account one", why(there, one, "SELECT", project=con, account=sbx), fulfilment),
        (
            "a fulfilment whose subscriber's account was not read",
            why(there, one, "SELECT", project=con, subscribed={con: None}),
            fulfilment,
        ),
        ("no subscription", why(there, one, "SELECT", project=con, subscribed={}), ""),
        (
            "a fulfilment to another account than the subscriber's",
            why(there, one, "SELECT", project=con, subscribed={con: {"another-account"}}),
            "",
        ),
        ("a fulfilment with the grant option", why(there, one, "SELECT", "SELECT", con), ""),
        ("a fulfilment that writes", why(there, one, "INSERT", project=con), ""),
        ("a subscriber on every table", why(there, every, "SELECT", project=con), ""),
        ("IAMPrincipals with no context", why(here, one, "SELECT"), ""),
        ("the owner's members", why(here, every, "SELECT", project=own), members_grant),
        ("the owner's role", why(owner_role, one, "ALL", "ALL"), "the owning project's role"),
        ("another project's role", why(owner_role.replace(own, con), one, "SELECT"), ""),
        ("the role's name elsewhere", why(owner_role.replace(prd, sbx), one, "SELECT"), ""),
        ("SMUS's role on every table", why(smus_role, every, "SELECT", "SELECT"), blueprint_grant),
        ("SMUS's role on one table", why(smus_role, one, "SELECT"), ""),
    ]

    # CT-16: Production's listing, its owner session group and the Governance Manager among its
    # members, and a Sandbox project's listing beside it.
    products = [
        Product("lp", "t", "production", prd, one, own, "YES", "internal", "a1"),
        Product("ls", "u", "consumer", sbx, "lab.u", lab, "YES", "internal", "a2"),
    ]
    dev_id, dev_name = next(iter(CHAIN_DEV_PROJECTS.items()))
    projects = {
        own: PRODUCTION_PROJECT,
        con: "consumer",
        lab: "lab",
        "stagingproject": STAGING_PROJECT,
        dev_id: dev_name,
    }
    members = {
        own: [
            ("group", "g1", "PROJECT_OWNER", admin_role),
            ("user", "role", "PROJECT_CONTRIBUTOR", "-"),
            ("user", "gm", "PROJECT_CONTRIBUTOR", "-"),
        ],
        lab: [("user", "scientist", "PROJECT_OWNER", "-")],
    }
    profiles_by_id = {
        "gm": ("SSO", "-"),
        "scientist": ("SSO", "-"),
        "outsider": ("SSO", "-"),
        "role": ("IAM", owner_role),
        "admin": ("IAM", admin_role),
    }

    def acts_on(product, requester, reviewer, kind="project", targets=()):
        """product_acts on one APPROVED subscription to a sample listing."""
        subs = [(product.listing, product.table, "s1", "APPROVED", kind, con, "r1")]
        accepted = {"r1": (requester, reviewer)}
        return product_acts(
            [product], subs, accepted, members, profiles_by_id, projects, list(targets)
        )

    ours, theirs = products
    share = "the owner's Share, a request made by a member of the owning project"
    refused = f"subscription s1 to {one} of {PRODUCTION_PROJECT} is "
    by_user = "a user's subscription, whose grant Lake Formation does not list"
    by_role = f"a request approved by role/{PROJECT_ROLE_MARKER}{own}_env"
    open_listing = ours._replace(approval="NO")
    subscriber = [(STAGING_PROJECT, "s9", "APPROVED", "t"), (STAGING_PROJECT, "s8", "REVOKED", "t")]
    cases += [
        ("approved by the Governance Manager", acts_on(ours, "outsider", "gm"), ([], [])),
        ("approved by the owner session group", acts_on(ours, "outsider", "admin"), ([], [])),
        ("a Share on Production's listing", acts_on(ours, "admin", "-")[0], [refused + share]),
        ("requested and approved by one person", acts_on(ours, "gm", "gm")[0], [refused + share]),
        (
            "approved by the project's role",
            acts_on(ours, "outsider", "role")[0],
            [refused + by_role],
        ),
        (
            "approved by nobody",
            acts_on(ours, "outsider", "-")[0],
            [refused + "a request approved by nobody"],
        ),
        (
            "approved by a person outside the project",
            acts_on(ours, "outsider", "scientist")[0],
            [refused + "a request approved by scientist"],
        ),
        ("a user's subscription", acts_on(ours, "outsider", "gm", "user")[0], [refused + by_user]),
        (
            "a Share on a Sandbox project's listing",
            acts_on(theirs, "scientist", "-"),
            ([], [("s1", "lab.u", "lab", "consumer", share)]),
        ),
        (
            "Production's listing with no approval required",
            acts_on(open_listing, "outsider", "gm")[0],
            [
                f"{one} of {PRODUCTION_PROJECT} reads approvalRequired NO: every request is "
                "approved at creation"
            ],
        ),
        (
            "a deployment project that subscribes",
            acts_on(ours, "outsider", "gm", targets=subscriber)[0],
            [
                f"{STAGING_PROJECT} holds subscription s9 to t: a deployment project subscribes "
                "to nothing"
            ],
        ),
    ]

    # CT-15, CT-18 and CT-19.
    listed = [
        ("l1", "t", "GlueTableAssetType", own, "1"),
        ("l2", "sample", "GlueTableAssetType", "stagingproject", "1"),
        ("l3", "bundle", "DataProduct", dev_id, "1"),
    ]
    form = {CLASSIFICATION_FORM: {CLASSIFICATION_FORM: "internal"}}
    restricted = ours._replace(name="r", classification="restricted")
    unfilled = ours._replace(name="e", classification="")
    bare = ours._replace(name="n", classification=None)
    sample_exceptions = {"sampleasset": "EXC-00: a sample exception"}
    known = bare._replace(name="x", asset="sampleasset")
    unclassified = [
        "r (app_etl.t) is classified restricted",
        "e (app_etl.t) is classified with an empty value",
        "n (app_etl.t) carries no classification form",
    ]
    link = {"CatalogId": prd, "DatabaseName": "app_etl", "Name": "t"}
    cases += [
        (
            "Staging's listing and a dev project's",
            stage_listings(listed, projects),
            ([("sample", STAGING_PROJECT)], [("bundle", dev_name)]),
        ),
        ("Production's listing alone", stage_listings(listed[:1], projects), ([], [])),
        ("a form's value", classification_value(form), "internal"),
        ("a listing with no form", classification_value({"GlueTableForm": {}}), None),
        ("a form with no value", classification_value({CLASSIFICATION_FORM: {}}), ""),
        (
            "the classifications that fail, and the one excepted",
            classification_findings([ours, restricted, unfilled, bare, known], sample_exceptions),
            (unclassified, [known]),
        ),
        ("a link's target", link_target(link, {prd: "production"}), "production:app_etl.t"),
        ("a table that is no link", link_target(None, {}), ""),
    ]

    # CT-17 and CT-18 on a table a data product's publication listed, which SearchListings omits
    # (SUP-482): the listings' shape as Stage 21 5.3 read it on 2026-11-23.
    def asset_listing(
        name: str, forms: dict, owner: str | None = own, status: str = "INACTIVE"
    ) -> dict:
        """GetListing's answer for an asset listing, its forms a JSON string."""
        record = {"assetId": f"asset-{name}", "forms": json.dumps(forms)}
        if owner:
            record["owningProjectId"] = owner
        return {"name": name, "status": status, "item": {"assetListing": record}}

    def product_listing(items: list, owned: list, classification: str | None) -> dict:
        """GetListing's answer for a data product listing, items and forms as 5.3 read them."""
        forms: dict = {PRODUCT_ITEMS_FORM: owned}
        if classification is not None:
            forms[CLASSIFICATION_FORM] = {CLASSIFICATION_FORM: classification}
        record = {
            "forms": json.dumps(forms),
            "owningProjectId": own,
            "items": [{"listingId": i, "listingRevision": "1"} for i in items],
        }
        return {"name": "images", "status": "ACTIVE", "item": {"dataProductListing": record}}

    def glue_form(catalog: str, database: str, table: str) -> dict:
        return {
            "GlueTableForm": {"catalogId": catalog, "databaseName": database, "tableName": table},
            "SubscriptionTermsForm": {"approvalRequired": "YES"},
        }

    registry = "registry-account"
    where_of = {sbx: "consumer", prd: "production"}
    searched = [
        ("sl", "collection", S3_COLLECTION_TYPE, own, "4"),
        ("pl", "images", "DataProduct", own, "1"),
        ("gl", "listed", "GlueTableAssetType", own, "1"),
    ]
    bodies = {
        "pl": product_listing(["sl", "tl"], ["sl", "tl"], "internal"),
        "gl": asset_listing("listed", {**glue_form(sbx, "db", "listed"), **form}, status="ACTIVE"),
        "sl": asset_listing("collection", {S3_COLLECTION_FORM: {"bucketArn": "arn:aws:s3:::b/p/"}}),
        "tl": asset_listing("hidden", glue_form(sbx, "db", "hidden")),
    }

    def road(changed: dict | None = None, rows: list | None = None) -> tuple:
        """road_listings over the sample listings, `changed` replacing GetListing's answers."""
        answers = {**bodies, **(changed or {})}
        return road_listings(searched if rows is None else rows, answers.get, registry, where_of)

    listed_table = Product(
        "gl", "listed", "consumer", sbx, "db.listed", own, "YES", "internal", "asset-listed"
    )
    hidden_table = Product(
        "tl", "hidden", "consumer", sbx, "db.hidden", own, "YES", None, "asset-hidden", True
    )
    ownerless = asset_listing("hidden", glue_form(sbx, "db", "hidden"), owner=None)
    searchable = asset_listing("hidden", glue_form(sbx, "db", "hidden"), status="ACTIVE")
    _, found, carriers, product_forms, _ = road()
    carried = {"tl": [("images", product_forms["pl"])]}
    no_form = "hidden (db.hidden) carries no classification form"
    listed_no_form = "listed (db.listed) carries no classification form"
    fulfil = (
        "consumer",
        f"{sbx}{IAM_PRINCIPALS_SUFFIX}",
        "Table",
        "db.hidden",
        "SELECT",
        "-",
        f'context.datazone.projectId=="{con}"',
    )
    cases += [
        (
            "a table only its product's listing carries, read beside a searched one",
            (found, carriers, product_forms),
            ([listed_table, hidden_table], {"sl": ["pl"], "tl": ["pl"]}, {"pl": "internal"}),
        ),
        (
            "a table item in the product listing's forms alone",
            product_items(product_listing(["sl"], ["sl", "tl"], None)),
            ["sl", "tl"],
        ),
        (
            "a hidden table whose listing names no owner, owned by its product's",
            road({"tl": ownerless})[1][1:],
            [hidden_table],
        ),
        (
            "a hidden table whose GetListing fails",
            [road({"tl": None})[i] for i in (1, 4)],
            [[listed_table], ["GetListing tl"]],
        ),
        (
            "a hidden lake table, on the lake's road",
            road({"tl": asset_listing("trades", glue_form(registry, "curated", "trades"))})[0],
            [("tl", "curated.trades", own, "YES")],
        ),
        (
            "a hidden S3 Object Collection, on neither road",
            road(rows=searched[1:2])[1],
            [hidden_table],
        ),
        (
            "CT-17: the subscriber's grant on the hidden table",
            [
                explain_product_grant(fulfil, p.account, p.owner, {con: {sbx}})
                for p in found
                if p.listing == "tl"
            ],
            [fulfilment],
        ),
        (
            "an omitted table whose listing reads ACTIVE, which needs its own form",
            road({"tl": searchable})[1][1:],
            [hidden_table._replace(product_only=False)],
        ),
        (
            "CT-18: a table reachable through its product alone takes the product's form",
            classification_findings(found, {}, carried),
            ([], []),
        ),
        (
            "its label",
            classification_label(hidden_table, carried),
            "internal by its data product images",
        ),
        (
            "CT-18: such a table whose product carries no form",
            classification_findings([hidden_table], {}, {"tl": [("images", None)]}),
            ([f"{no_form}, nor does its data product images"], []),
        ),
        (
            "CT-18: such a table whose product is restricted",
            classification_findings([hidden_table], {}, {"tl": [("images", "restricted")]}),
            (["hidden (db.hidden) is classified restricted by its data product images"], []),
        ),
        (
            "CT-18: such a table in two products, one with no form",
            classification_findings(
                [hidden_table], {}, {"tl": [("images", "internal"), ("other", None)]}
            ),
            ([f"{no_form}, nor does its data product other"], []),
        ),
        (
            "CT-18: such a table's own form, judged before its product's",
            classification_findings(
                [hidden_table._replace(classification="restricted")], {}, carried
            ),
            (["hidden (db.hidden) is classified restricted"], []),
        ),
        (
            "CT-18: a table listed on its own with no form, its product's named",
            classification_findings(
                [listed_table._replace(classification=None)], {}, {"gl": [("images", "internal")]}
            ),
            ([f"{listed_no_form} (its data product images reads internal)"], []),
        ),
    ]

    # CT-13: a start judged by its caller, a deploy role as its deployment project's.
    def start_by(issuer: str, source: str) -> dict:
        context = {"sessionIssuer": {"userName": issuer}}
        return {
            "userIdentity": {"type": "AssumedRole", "sessionContext": context},
            "requestParameters": {"dataSourceIdentifier": source},
            "requestID": "r",
        }

    owners = {"s-own": own, "s-con": con}
    deploying = {"awsds-deploy-prod": own}
    cases += [
        (
            "a project role's start of its own source",
            judge_start(start_by(f"{PROJECT_ROLE_MARKER}{own}_env", "s-own"), owners, deploying)[0],
            "own",
        ),
        (
            "a project role's start of another's",
            judge_start(start_by(f"{PROJECT_ROLE_MARKER}{own}_env", "s-con"), owners, deploying)[0],
            "cross",
        ),
        (
            "a deploy role's start of its project's source",
            judge_start(start_by("awsds-deploy-prod", "s-own"), owners, deploying)[:2],
            ("own", own),
        ),
        (
            "a deploy role's start of another project's",
            judge_start(start_by("awsds-deploy-prod", "s-con"), owners, deploying)[0],
            "cross",
        ),
        (
            "a deploy role whose project is not listed",
            judge_start(start_by("awsds-deploy-staging", "s-own"), owners, deploying)[0],
            "other",
        ),
    ]

    # CT-20: what explains an S3 Access Grant on a project's folder, and what does not.
    folder = f"s3://projects-bucket/dzd-domain/{own}/"
    images = f"{folder}shared/images/*"
    reader = f"arn:aws:iam::{sbx}:role/{PROJECT_ROLE_MARKER}{con}_env"
    approved = {images: [("images", own, {con})]}
    cases += [
        (
            "a subscriber's grant at the collection's scope",
            explain_access_grant(folder, reader, images, approved),
            f"the fulfilment of {con}'s approved subscription to images",
        ),
        (
            "the scope DataZone writes for a collection's prefix",
            collection_scope("arn:aws:s3:::projects-bucket/dzd-domain/p/shared/images/"),
            "s3://projects-bucket/dzd-domain/p/shared/images/*",
        ),
        (
            "a grant with no subscription",
            explain_access_grant(folder, reader, images, {images: [("images", own, set())]}),
            "",
        ),
        (
            "a grant wider than the collection",
            explain_access_grant(folder, reader, f"{folder}shared/*", approved),
            "",
        ),
        (
            "a collection another project owns at the same scope",
            explain_access_grant(folder, reader, images, {images: [("images", lab, {con})]}),
            "",
        ),
        (
            "the location's own project role",
            explain_access_grant(folder, owner_role.replace(prd, sbx), images, {}),
            "the location's own project role",
        ),
        (
            "a person's role on a project's folder",
            explain_access_grant(folder, admin_role, images, {}),
            None,
        ),
        (
            "a project role on a location no project owns",
            explain_access_grant("s3://lake-bucket/", reader, "s3://lake-bucket/team/*", {}),
            None,
        ),
    ]

    wrong = [(what, got, want) for what, got, want in cases if got != want]
    for what, got, want in wrong:
        print(f"  FAIL  {what}: read {got!r}, expected {want!r}")
    print(f"catalog.py --self-check: {len(cases) - len(wrong)} of {len(cases)} cases as expected")
    return 2 if wrong else 0


def main(argv: list) -> int:
    cmdline.check(argv, __doc__, flags=("--self-check",), positional=False)
    if "--self-check" in argv:
        return self_check()
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    errors = ErrorLog()
    callers = profiles.preflight(
        [DATA_PROFILE, SANDBOX_PROFILE, STAGING_PROFILE, PROD_PROFILE], errors, out_label=out_label
    )
    live = {c.profile: c for c in callers}
    dat = AwsCli(profile=DATA_PROFILE, region=context.REGION, errors=errors, echo_profile=True)
    sbx = AwsCli(profile=SANDBOX_PROFILE, region=context.REGION, errors=errors, echo_profile=True)
    stg = AwsCli(profile=STAGING_PROFILE, region=context.REGION, errors=errors, echo_profile=True)
    prd = AwsCli(profile=PROD_PROFILE, region=context.REGION, errors=errors, echo_profile=True)
    checks = Checks()

    # ---------------------------------------------------------------- CT-1 the domain
    # `list-domains` in an ASSOCIATED member account returns the shared domain, so the listing
    # alone cannot say where a domain lives. `managedAccountId` can: it names the account that
    # owns the domain, and the same id appears on both sides of an association.
    domains: list = []
    domain_id = ""
    root_unit = ""
    if live[DATA_PROFILE].live:
        res = dat.run(
            "datazone",
            "list-domains",
            "--query",
            "items[].[id,name,status,managedAccountId]",
            "--output",
            "json",
        )
        domains = json_or_none(res.stdout) or []
        available = [d for d in domains if d[2] == "AVAILABLE"]
        if len(available) == 1:
            domain_id = available[0][0]
            res = dat.run(
                "datazone",
                "get-domain",
                "--identifier",
                domain_id,
                "--query",
                "rootDomainUnitId",
                "--output",
                "text",
            )
            root_unit = (res.stdout or "").strip()
    sandbox_domains: list = []
    if live[SANDBOX_PROFILE].live:
        res = sbx.run(
            "datazone",
            "list-domains",
            "--query",
            "items[].[id,name,status,managedAccountId]",
            "--output",
            "json",
        )
        sandbox_domains = json_or_none(res.stdout) or []
    registry_account = live[DATA_PROFILE].account
    consumer_account = live[SANDBOX_PROFILE].account
    # The accounts read, each by the label its grant rows carry.
    estate = (
        ("registry", dat, DATA_PROFILE),
        ("consumer", sbx, SANDBOX_PROFILE),
        ("staging", stg, STAGING_PROFILE),
        ("production", prd, PROD_PROFILE),
    )
    where_of = {live[p].account: label for label, _, p in estate if live[p].live}
    cli_of = {label: cli for label, cli, _ in estate}
    owned_elsewhere = [d for d in domains if d[3] != registry_account]
    owned_by_consumer = [d for d in sandbox_domains if d[3] == consumer_account]
    if not domains:
        checks.fail("CT-1", "one domain, owned by the registry account", "none read")
    elif len([d for d in domains if d[2] == "AVAILABLE"]) != 1:
        checks.fail(
            "CT-1",
            "one domain, owned by the registry account",
            f"{len([d for d in domains if d[2] == 'AVAILABLE'])} available domains",
        )
    elif owned_elsewhere or owned_by_consumer:
        checks.fail(
            "CT-1",
            "one domain, owned by the registry account",
            f"{len(owned_by_consumer)} domain(s) owned by the consumer account - D26 keeps the registry separate",
        )
    else:
        checks.ok(
            "CT-1",
            "one domain, owned by the registry account",
            f"{domain_id} AVAILABLE; the consumer account sees it by association and owns none",
        )

    # ---------------------------------------------------------------- the projects
    projects: dict = {}
    if domain_id:
        res = dat.run(
            "datazone",
            "list-projects",
            "--domain-identifier",
            domain_id,
            "--query",
            "items[].[id,name]",
            "--output",
            "json",
        )
        projects = {i: n for i, n in json_or_none(res.stdout) or []}
    deploy_projects = {
        role: pid for role, name in DEPLOY_ROLES.items() for pid, n in projects.items() if n == name
    }

    # ---------------------------------------------------------------- CT-2 the listings
    listings: list = []
    listed_assets: set = set()  # the ids of the assets and data products that carry a listing
    if domain_id:
        res = dat.run(
            "datazone",
            "search-listings",
            "--domain-identifier",
            domain_id,
            "--output",
            "json",
        )
        for item in (json_or_none(res.stdout) or {}).get("items", []):
            body = item.get("assetListing") or item.get("dataProductListing") or {}
            listed_assets.add(body.get("entityId", "-"))
            listings.append(
                (
                    body.get("listingId", "-"),
                    body.get("name", "-"),
                    body.get("entityType", "DataProduct"),
                    body.get("owningProjectId", "-"),
                    body.get("listingRevision", "-"),
                )
            )
    orphans = [n for _, n, _, p, _ in listings if p not in projects]
    if not listings:
        checks.note("CT-2", "every listing names a project that exists", "no listing published")
    elif orphans:
        checks.fail(
            "CT-2",
            "every listing names a project that exists",
            f"owning project not found for: {', '.join(orphans)}",
        )
    else:
        checks.ok(
            "CT-2",
            "every listing names a project that exists",
            f"{len(listings)} listings, all owned by a live project",
        )

    # ---------------------------------------------------------------- CT-3 the access acts
    access_rows: list = []
    total_acts = 0
    for lid, name, _, _, _ in listings:
        counts = []
        for verb, flag in (
            ("list-subscriptions", "--subscribed-listing-id"),
            ("list-subscription-requests", "--subscribed-listing-id"),
            ("list-subscription-grants", "--subscribed-listing-id"),
        ):
            res = dat.run(
                "datazone",
                verb,
                "--domain-identifier",
                domain_id,
                flag,
                lid,
                "--query",
                "length(items)",
                "--output",
                "text",
                tolerate="ValidationException",
            )
            n = (res.stdout or "").strip()
            counts.append(n if n.isdigit() else "DENIED" if not res.ok else "0")
            if n.isdigit():
                total_acts += int(n)
        access_rows.append((name, *counts))
    if not listings:
        checks.note("CT-3", "the access acts on the catalog road", "no listing to subscribe to")
    elif total_acts == 0:
        checks.note(
            "CT-3",
            "the access acts on the catalog road",
            "no subscription, request or grant on any listing - publishing has changed no access",
        )
    else:
        checks.note(
            "CT-3",
            "the access acts on the catalog road",
            f"{total_acts} across {len(listings)} listings; CT-7 says whether they are registered",
        )

    # ---------------------------------------------------------------- the data sources
    sources: list = []
    source_dbs: dict = {}  # data source id -> the databases its Glue filter names (CT-5)
    source_project: dict = {}  # data source id -> its project id (CT-13)
    sources_listed: set = set()  # the projects whose listing answered (CT-14)
    for pid, pname in projects.items():
        res = dat.run(
            "datazone",
            "list-data-sources",
            "--domain-identifier",
            domain_id,
            "--project-identifier",
            pid,
            "--query",
            "items[].dataSourceId",
            "--output",
            "json",
        )
        if res.ok:
            sources_listed.add(pname)
        for dsid in json_or_none(res.stdout) or []:
            res = dat.run(
                "datazone",
                "get-data-source",
                "--domain-identifier",
                domain_id,
                "--identifier",
                dsid,
                "--output",
                "json",
            )
            body = json_or_none(res.stdout) or {}
            source_project[dsid] = pid
            glue_run = (body.get("configuration") or {}).get("glueRunConfiguration") or {}
            source_dbs[dsid] = [
                f.get("databaseName", "-")
                for f in glue_run.get("relationalFilterConfigurations") or []
            ]
            sources.append(
                (
                    pname,
                    mask_account(body.get("name", "-")),
                    body.get("type", "-"),
                    bool(body.get("publishOnImport")),
                    bool((body.get("recommendation") or {}).get("enableBusinessNameGeneration")),
                    (body.get("schedule") or {}).get("schedule", "-"),
                    body.get("status", "-"),
                    body.get("lastRunAssetCount", "-"),
                    dsid,
                )
            )

    # The run history, which the data source's own `status` field does not give. A run's stoppedAt is
    # its successor's startedAt, so a daily source always shows one RUNNING however long it has been
    # failing: the live status reads healthy while every completed run failed (EXC-11).
    runs: dict = {}
    for src in sources:
        dsid = src[-1]
        res = dat.run(
            "datazone",
            "list-data-source-runs",
            "--domain-identifier",
            domain_id,
            "--data-source-identifier",
            dsid,
            "--query",
            "items[].status",
            "--output",
            "json",
        )
        statuses = json_or_none(res.stdout) or []
        runs[dsid] = {s: statuses.count(s) for s in set(statuses)}

    # ---------------------------------------------------------------- CT-4 publish on import
    publishing = [n for _, n, _, poi, _, _, _, _, _ in sources if poi]
    if not sources:
        checks.note("CT-4", "no data source publishes on import", "no data source read")
    elif publishing:
        checks.fail(
            "CT-4",
            "no data source publishes on import",
            f"{', '.join(publishing)} publish at import time - a listing nobody reviewed",
        )
    else:
        checks.ok(
            "CT-4",
            "no data source publishes on import",
            f"all {len(sources)} carry publishOnImport false",
        )

    # ---------------------------------------------------------------- CT-5 AI business names
    lake_ai = [
        f"{n} in {p}"
        for p, n, _, _, ai, _, _, _, d in sources
        if ai and set(source_dbs.get(d, [])) & set(LAKE_DATABASES)
    ]
    project_ai = [
        n
        for _, n, _, _, ai, _, _, _, d in sources
        if ai and not set(source_dbs.get(d, [])) & set(LAKE_DATABASES)
    ]
    lake_sources = [d for d, dbs in source_dbs.items() if set(dbs) & set(LAKE_DATABASES)]
    elsewhere = (
        f"; over a project's own database: {', '.join(project_ai)}, the project's choice"
        if project_ai
        else ""
    )
    if not sources:
        checks.note("CT-5", "no source over the lake generates business names", "no source read")
    elif lake_ai:
        checks.fail(
            "CT-5",
            "no source over the lake generates business names",
            f"{', '.join(lake_ai)} - Stage 6f decision 3 keeps the generation off on every lake "
            "source; update-data-source --recommendation enableBusinessNameGeneration=false"
            + elsewhere,
        )
    else:
        checks.ok(
            "CT-5",
            "no source over the lake generates business names",
            f"{len(lake_sources)} source(s) over the lake, each with the generation off"
            + elsewhere,
        )

    # ---------------------------------------------------------------- CT-14 a deployment project
    for name in DEPLOYMENT_PROJECTS:
        ct14 = f"{name}'s sources: Glue, one per database, nothing published or generated"
        if name not in projects.values():
            checks.note("CT-14", ct14, "no such project - Stage 19 step 4.6 creates it")
            continue
        if name not in sources_listed:
            checks.note("CT-14", ct14, "its data sources were not read")
            continue
        mine = [s for s in sources if s[0] == name]
        problems = []
        seen_dbs: list = []
        for _, sname, stype, poi, ai, _, _, _, dsid in mine:
            dbs = source_dbs.get(dsid, [])
            if stype != "GLUE":
                problems.append(f"{sname} is a {stype} source")
            if len(dbs) != 1:
                problems.append(f"{sname} names {len(dbs)} databases")
            if poi:
                problems.append(f"{sname} publishes on import")
            if ai:
                problems.append(f"{sname} generates business names")
            seen_dbs += dbs
        repeated = sorted({d for d in seen_dbs if seen_dbs.count(d) > 1})
        if repeated:
            problems.append(f"more than one source over {', '.join(repeated)}")
        if problems:
            checks.fail(
                "CT-14",
                ct14,
                "; ".join(problems) + " - the publishing task is the one publisher (Stage 19 "
                "decision 14), and nobody chooses a setting in a deployment project",
            )
        elif not mine:
            checks.note("CT-14", ct14, "no data source: no database was created in it yet")
        else:
            checks.ok(
                "CT-14",
                ct14,
                f"{len(mine)} source(s), over {', '.join(sorted(set(seen_dbs)))}",
            )

    # ---------------------------------------------------------------- CT-6 the schedules
    # The first draft of this check read the schedule and stopped there, and passed over 26 days of
    # daily failures because the data source's own `status` read RUNNING (EXC-11). What decides the
    # verdict is the run history: a scheduled source whose COMPLETED runs all failed is a failure,
    # however healthy the live status looks.
    scheduled = [(p, n, s, d) for p, n, _, _, _, s, _, _, d in sources if s != "-"]
    failing = []
    for p, n, s, dsid in scheduled:
        by_status = runs.get(dsid, {})
        done = {k: v for k, v in by_status.items() if k != "RUNNING"}
        if done and all(k == "FAILED" for k in done):
            failing.append((p, n, s, sum(done.values())))
    # The discriminator (Lesson 50). A source is failing by a recorded exception, so reporting it
    # as a failure every run would leave this check permanently red and teach the reader to skip it.
    # It reads as a note naming EXC-11, with the number of sources the name covered, because the
    # exemption is by name and every new project adds one; anything ELSE failing is the finding
    # this check exists for.
    excepted = [f for f in failing if f[1] in FAILING_BY_EXCEPTION]
    unexpected = [f for f in failing if f[1] not in FAILING_BY_EXCEPTION]
    if not scheduled:
        checks.ok(
            "CT-6",
            "every scheduled run is one somebody chose, and succeeds",
            "no data source is scheduled",
        )
    elif unexpected:
        checks.fail(
            "CT-6",
            "every scheduled run is one somebody chose, and succeeds",
            "; ".join(
                f"{n} in {p} on {s}: every completed run FAILED ({c})" for p, n, s, c in unexpected
            )
            + " - a service-created source on a service-chosen cron, failing unwatched (Lesson 17)",
        )
    elif excepted:
        covered: dict = {}
        for p, n, s, c in excepted:
            covered.setdefault(n, []).append(f"{p} on {s}, {c} runs")
        checks.note(
            "CT-6",
            "every scheduled run is one somebody chose, and succeeds",
            "; ".join(
                f"{n}: {len(rows)} source(s), every completed run FAILED ({'; '.join(rows)})"
                f" - {FAILING_BY_EXCEPTION[n]}"
                for n, rows in covered.items()
            ),
        )
    else:
        checks.note(
            "CT-6",
            "every scheduled run is one somebody chose, and succeeds",
            "; ".join(
                f"{n} in {p} on {s} ({', '.join(f'{v} {k}' for k, v in sorted(runs.get(d, {}).items())) or 'no run'})"
                for p, n, s, d in scheduled
            )
            + " - a blueprint-created source arrives with a cron nobody wrote (Lesson 17)",
        )

    # ---------------------------------------------------------------- CT-13 the starts
    # The caller's account records the role's name; the domain's account records a call from another
    # account with that account and the role's id alone. The callers' copies are read first, the
    # Interactive account's and each deployment target's, and the registry's copy of the same request
    # is skipped. A refused start started nothing.
    starts: list = []  # (time, verdict, caller, source id, source's project id, request id)
    seen_requests: set = set()
    trails_read = 0
    trail_clis = (
        (sbx, SANDBOX_PROFILE),
        (stg, STAGING_PROFILE),
        (prd, PROD_PROFILE),
        (dat, DATA_PROFILE),
    )
    for cli, profile in trail_clis:
        if not live[profile].live:
            continue
        res = cli.run(
            "cloudtrail",
            "lookup-events",
            "--lookup-attributes",
            "AttributeKey=EventName,AttributeValue=StartDataSourceRun",
            "--output",
            "json",
        )
        if not res.ok:
            continue
        trails_read += 1
        for event in (json_or_none(res.stdout) or {}).get("Events", []):
            body = json_or_none(event.get("CloudTrailEvent", "")) or {}
            request = body.get("requestID", "")
            if body.get("errorCode") or (request and request in seen_requests):
                continue
            seen_requests.add(request)
            starts.append(
                (body.get("eventTime", "-"),)
                + judge_start(body, source_project, deploy_projects)
                + (request,)
            )
    starts.sort()
    by_verdict: dict = {}
    for row in starts:
        by_verdict.setdefault(row[1], []).append(row)

    def started(row: tuple) -> str:
        time, _, caller, source, owner, _ = row
        return f"{time} {projects.get(caller, caller)} started {source} of {projects.get(owner, owner or '-')}"

    ct13 = "every start of a data source is its own project's"
    if by_verdict.get("cross"):
        checks.fail(
            "CT-13",
            ct13,
            "; ".join(started(r) for r in by_verdict["cross"])
            + " - a project role starting another project's source (SUP-346, TM-29)",
        )
    elif trails_read < len(trail_clis):
        checks.note(
            "CT-13",
            ct13,
            f"{len(trail_clis) - trails_read} of the {len(trail_clis)} trails not read",
        )
    elif any(by_verdict.get(v) for v in ("measured", "unresolved", "unknown source")):
        checks.note(
            "CT-13",
            ct13,
            "; ".join(
                [
                    f"{started(r)}: {MEASURED_CROSS_PROJECT_STARTS[r[5]]}"
                    for r in by_verdict.get("measured", [])
                ]
                + [
                    f"{r[0]} {r[2]} from another account started {r[3]}, unresolved"
                    for r in by_verdict.get("unresolved", [])
                ]
                + [
                    f"{r[0]} {projects.get(r[2], r[2])} started {r[3]}, no such source listed"
                    for r in by_verdict.get("unknown source", [])
                ]
            )
            + f"; {len(by_verdict.get('own', []))} start(s) by the source's own project role",
        )
    else:
        others = sorted({r[2] for r in by_verdict.get("other", [])})
        checks.ok(
            "CT-13",
            ct13,
            f"{len(by_verdict.get('own', []))} start(s) in CloudTrail's 90 days, each by the source's own project's role or deploy role"
            + (f"; callers that are no project role: {', '.join(others)}" if others else ""),
        )

    # ---------------------------------------------------------------- the grants, every account read
    grant_rows: list = []
    lf_read: dict = {}  # where -> (grants, pages, read to the last page)
    for label, cli, profile in estate:
        if not live[profile].live:
            lf_read[label] = (0, 0, False)
            continue
        listing = cli.pages("lakeformation", "list-permissions")
        entries = listing.items("PrincipalResourcePermissions")
        lf_read[label] = (len(entries), len(listing.pages), listing.complete)
        for row in entries:
            ident = (row.get("Principal") or {}).get("DataLakePrincipalIdentifier", "-")
            kind, name = resource_of(row.get("Resource") or {})
            grant_rows.append(
                (
                    label,
                    ident,
                    kind,
                    name,
                    "+".join(row.get("Permissions") or []) or "-",
                    "+".join(row.get("PermissionsWithGrantOption") or []) or "-",
                    (row.get("Condition") or {}).get("Expression", ""),
                )
            )

    smus_grants = [g for g in grant_rows if is_smus_principal(g[1])]
    # The accounts whose listing stopped before its last page, or was never read. A grant found
    # in what was read is a finding; an absence there proves nothing (Lesson 62).
    unlisted = [w for w, (_, _, whole) in lf_read.items() if not whole]
    partial = f"not read to its last page: {', '.join(unlisted)} (section 5)"

    # ---------------------------------------------------------------- CT-7 SMUS reaching the lake
    lake_grants = [g for g in smus_grants if touches_lake(g[2], g[3])]
    # The road is the registry's, with the Interactive account its one consumer: a deployment
    # project subscribes to nothing (CT-16), so no grant in a target is on it.
    catalog_road = [
        g
        for g in lake_grants
        if g[0] in ("registry", "consumer") and on_catalog_road(g[1], g[2], g[3], g[4])
    ]
    reaching = [g for g in lake_grants if g not in catalog_road]
    if not grant_rows:
        checks.note("CT-7", "no SMUS principal reaches the governed lake", "no grant read")
    elif reaching:
        checks.fail(
            "CT-7",
            "no SMUS principal reaches the governed lake",
            "; ".join(f"{short_principal(g[1])} on {g[2]} {g[3]}" for g in reaching)
            + " - a second road into governed data, with no row in AWS_STATE.md's register",
        )
    elif unlisted:
        checks.note(
            "CT-7",
            "no SMUS principal reaches the governed lake",
            f"{len(smus_grants)} SMUS grants read, {len(catalog_road)} on the catalog road and "
            f"the rest on project-owned objects; {partial}",
        )
    elif catalog_road:
        checks.note(
            "CT-7",
            "no SMUS principal reaches the governed lake but through the catalog road",
            "; ".join(
                f"{short_principal(g[1])} on {g[2]} {g[3]}: {g[4]}"
                + (f" (grantable {g[5]})" if g[5] != "-" else "")
                + (f" [{g[6]}]" if g[6] else "")
                for g in catalog_road
            )
            + f" - Stage 6f decision 1's published tables; the other "
            f"{len(smus_grants) - len(catalog_road)} SMUS grants are on project-owned objects",
        )
    else:
        checks.ok(
            "CT-7",
            "no SMUS principal reaches the governed lake",
            f"{len(smus_grants)} SMUS grants, all on project-owned objects",
        )

    # ---------------------------------------------------------------- CT-8 the account-wide entry
    account_wide = [
        g for g in grant_rows if g[1].endswith(IAM_PRINCIPALS_SUFFIX) and "projectId" not in g[6]
    ]
    iam_principals = [g for g in grant_rows if g[1].endswith(IAM_PRINCIPALS_SUFFIX)]
    if account_wide:
        checks.fail(
            "CT-8",
            "every IAMPrincipals grant is project-conditioned",
            "; ".join(f"{g[2]} {g[3]}" for g in account_wide)
            + " - without the condition this grants every principal in the account",
        )
    elif unlisted:
        checks.note(
            "CT-8",
            "every IAMPrincipals grant is project-conditioned",
            f"{len(iam_principals)} read, all carrying context.datazone.projectId; {partial}",
        )
    elif not iam_principals:
        checks.note("CT-8", "every IAMPrincipals grant is project-conditioned", "none exists")
    else:
        checks.ok(
            "CT-8",
            "every IAMPrincipals grant is project-conditioned",
            f"all {len(iam_principals)} carry context.datazone.projectId",
        )

    # ---------------------------------------------------------------- CT-9 the domain's authorization
    policy_grants: list = []
    for pt in DOMAIN_UNIT_POLICY_TYPES:
        if not root_unit:
            break
        res = dat.run(
            "datazone",
            "list-policy-grants",
            "--domain-identifier",
            domain_id,
            "--entity-type",
            "DOMAIN_UNIT",
            "--entity-identifier",
            root_unit,
            "--policy-type",
            pt,
            "--query",
            "grantList[].principal",
            "--output",
            "json",
            tolerate="AccessDeniedException",
        )
        if not res.ok:
            policy_grants.append((pt, "DENIED"))
            continue
        body = json_or_none(res.stdout)
        if body is None:
            policy_grants.append((pt, "DENIED"))
        elif not body:
            policy_grants.append((pt, "-"))
        else:
            policy_grants.append((pt, json.dumps(body, separators=(",", ":"))))
    overrides = [
        (pt, v) for pt, v in policy_grants if pt in OVERRIDE_TYPES and v not in ("-", "DENIED")
    ]
    unread = [pt for pt, v in policy_grants if pt in OVERRIDE_TYPES and v == "DENIED"]
    if not policy_grants:
        checks.note("CT-9", "nobody may override an owner", "the root domain unit was not read")
    elif unread:
        checks.note(
            "CT-9",
            "nobody may override an owner",
            f"refused for {', '.join(unread)} - the reading is the ceiling, not the grant",
        )
    elif overrides:
        checks.fail(
            "CT-9",
            "nobody may override an owner",
            "; ".join(f"{pt}: {v}" for pt, v in overrides)
            + " - the owner project's approval stops being the control",
        )
    else:
        checks.ok(
            "CT-9",
            "nobody may override an owner",
            "both override policy types are empty; approval stays with the owner project",
        )

    # ---------------------------------------------------------------- the catalog road's records
    # SearchListings carries no form, so each Glue table listing is read whole, and each data
    # product listing for the asset listings it carries, those SearchListings omits included.
    def get_listing(lid: str) -> dict | None:
        res = dat.run(
            "datazone",
            "get-listing",
            "--domain-identifier",
            domain_id,
            "--identifier",
            lid,
            "--output",
            "json",
            tolerate="AccessDeniedException",
        )
        if res.tolerated or not res.ok:
            return None
        return json_or_none(res.stdout) or {}

    lake_listings, products, bundles, product_classes, failed_reads = road_listings(
        listings, get_listing, registry_account, where_of
    )
    # The reads CT-10 and CT-11 could not make, and the same for CT-16 to CT-19: an absence there
    # proves nothing.
    road_unread: list = list(failed_reads)
    product_unread: list = list(failed_reads)
    # The product tables SearchListings did not return, read through a data product listing.
    searched = {lid for lid, _, _, _, _ in listings}
    unsearched = [p for p in products if p.listing not in searched]

    def acts(asset_listing: str, table: str, unread: list) -> tuple:
        """One asset listing's subscriptions, ACCEPTED requests and COMPLETED grants, asked under
        its own id and under each data product listing that carries it (SUP-363)."""
        subs: dict = {}  # subscription id -> (listing, table, id, status, principal kind, project, request)
        accepted: dict = {}  # ACCEPTED request id -> (requester, reviewer)
        done: set = set()  # the subscriptions whose grant is COMPLETED
        for lid in [asset_listing, *bundles.get(asset_listing, [])]:
            for verb, extra in (
                ("list-subscriptions", ()),
                ("list-subscription-requests", ("--status", "ACCEPTED")),
                ("list-subscription-grants", ()),
            ):
                res = dat.run(
                    "datazone",
                    verb,
                    "--domain-identifier",
                    domain_id,
                    "--subscribed-listing-id",
                    lid,
                    *extra,
                    "--output",
                    "json",
                )
                if not res.ok:
                    unread.append(f"{verb} {lid}")
                    continue
                for item in (json_or_none(res.stdout) or {}).get("items", []):
                    if verb == "list-subscriptions":
                        principal = item.get("subscribedPrincipal") or {}
                        subs[item.get("id", "-")] = (
                            asset_listing,
                            table,
                            item.get("id", "-"),
                            item.get("status", "-"),
                            next(iter(principal), "-"),
                            (principal.get("project") or {}).get("id", "-"),
                            item.get("subscriptionRequestId") or "-",
                        )
                    elif verb == "list-subscription-requests":
                        accepted[item.get("id", "-")] = (
                            item.get("createdBy", "-"),
                            item.get("reviewerId") or "-",
                        )
                    elif item.get("status") == "COMPLETED":
                        done.add(item.get("subscriptionId", "-"))
        return list(subs.values()), accepted, done

    road_subs: list = []  # (listing id, table, subscription id, status, principal kind, project, request)
    road_requests: dict = {}  # ACCEPTED request id -> (requester, reviewer)
    completed: dict = {}  # listing id -> subscription ids whose grant is COMPLETED
    for lid, table, _, _ in lake_listings:
        subs, accepted, done = acts(lid, table, road_unread)
        road_subs += subs
        road_requests.update(accepted)
        completed[lid] = done

    # The publishing projects' members, each resolved to what it is: an approver holds the project
    # role's sessions too, so the membership is the boundary of who can regrant a published table.
    road_members: dict = {}  # project id -> [(kind, member id, designation, role ARN or "-")]
    profiles_by_id: dict = {}  # user profile id -> (type, IAM ARN or "-")

    def profile(user_id: str, unread: list) -> tuple:
        if user_id not in profiles_by_id:
            res = dat.run(
                "datazone",
                "get-user-profile",
                "--domain-identifier",
                domain_id,
                "--user-identifier",
                user_id,
                "--output",
                "json",
            )
            body = json_or_none(res.stdout) or {}
            if not res.ok:
                unread.append(f"GetUserProfile {user_id}")
            profiles_by_id[user_id] = (
                body.get("type", "-"),
                ((body.get("details") or {}).get("iam") or {}).get("arn", "-"),
            )
        return profiles_by_id[user_id]

    def members_of(project: str, unread: list) -> list | None:
        """A project's members as (kind, member id, designation, role ARN or "-"); None when the
        membership was not read."""
        res = dat.run(
            "datazone",
            "list-project-memberships",
            "--domain-identifier",
            domain_id,
            "--project-identifier",
            project,
            "--output",
            "json",
        )
        if not res.ok:
            unread.append(f"ListProjectMemberships {project}")
            return None
        rows = []
        for m in (json_or_none(res.stdout) or {}).get("members", []):
            details = m.get("memberDetails") or {}
            if "user" in details:
                uid = (details.get("user") or {}).get("userId", "-")
                profile(uid, unread)
                rows.append(("user", uid, m.get("designation", "-"), "-"))
            else:
                gid = (details.get("group") or {}).get("groupId", "-")
                res = dat.run(
                    "datazone",
                    "get-group-profile",
                    "--domain-identifier",
                    domain_id,
                    "--group-identifier",
                    gid,
                    "--output",
                    "json",
                )
                if not res.ok:
                    unread.append(f"GetGroupProfile {gid}")
                body = json_or_none(res.stdout) or {}
                rows.append(
                    ("group", gid, m.get("designation", "-"), body.get("rolePrincipalArn") or "-")
                )
        return rows

    for project in sorted({owner for _, _, owner, _ in lake_listings}):
        rows = members_of(project, road_unread)
        if rows is not None:
            road_members[project] = rows
    for requester, _ in road_requests.values():
        profile(requester, road_unread)

    # The classification of every table the road covers, table and columns, read live.
    road_tables = sorted(set(PUBLISHED_LAKE_TABLES) | {t for _, t, _, _ in lake_listings})
    classifications: dict = {}  # table -> GetResourceLFTags's answer
    for table in road_tables:
        db, name = table.split(".", 1)
        res = dat.run(
            "lakeformation",
            "get-resource-lf-tags",
            "--resource",
            json.dumps({"Table": {"DatabaseName": db, "Name": name}}),
            "--show-assigned-lf-tags",
            "--output",
            "json",
        )
        if res.ok:
            classifications[table] = json_or_none(res.stdout) or {}
        else:
            road_unread.append(f"GetResourceLFTags {table}")

    # ---------------------------------------------------------------- CT-10 every road grant explained
    listed_owner = {t: owner for _, t, owner, _ in lake_listings}
    listing_of = {t: lid for lid, t, _, _ in lake_listings}
    road_rows = [
        g for g in grant_rows if g[0] == "registry" and g[2] in TABLE_KINDS and g[3] in road_tables
    ]
    explained: list = []  # (row, why)
    unexplained: list = []
    for g in road_rows:
        lid = listing_of.get(g[3], "")
        fulfilled = {
            s[5]
            for s in road_subs
            if s[0] == lid and s[3] == "APPROVED" and s[2] in completed.get(lid, set())
        }
        why = explain_grant(
            g,
            registry_account or "-",
            consumer_account or "-",
            listed_owner.get(g[3], ""),
            fulfilled,
        )
        (explained if why else unexplained).append((g, why))
    fulfilments = [g for g, why in explained if why.startswith("the fulfilment")]
    unfulfilled = [
        s
        for s in road_subs
        if s[3] == "APPROVED"
        and not any(condition_project(g[6]) == s[5] and g[3] == s[1] for g in fulfilments)
    ]
    gap = (
        f"; {len(unfulfilled)} APPROVED subscription(s) the lake holds no grant for: "
        + ", ".join(s[2] for s in unfulfilled)
        if unfulfilled
        else ""
    )
    if unexplained:
        checks.fail(
            "CT-10",
            "every grant on a published lake table is explained",
            "; ".join(
                f"{short_principal(g[1])} on {g[2]} {g[3]}: {g[4]}"
                + (f" (grantable {g[5]})" if g[5] != "-" else "")
                for g, _ in unexplained
            )
            + " - neither data/publishing.tf nor an approved subscription explains it",
        )
    elif unlisted or road_unread or not live[SANDBOX_PROFILE].live:
        checks.note(
            "CT-10",
            "every grant on a published lake table is explained",
            f"{len(explained)} explained; not read: "
            + ", ".join(
                [f"{w} grants" for w in unlisted]
                + road_unread
                + ([] if live[SANDBOX_PROFILE].live else ["the consumer account"])
            )
            + gap,
        )
    elif not road_rows:
        checks.note(
            "CT-10", "every grant on a published lake table is explained", "no grant on the road"
        )
    else:
        checks.ok(
            "CT-10",
            "every grant on a published lake table is explained",
            f"{len(road_rows)} grants on {', '.join(road_tables)}: "
            f"{len(fulfilments)} fulfilment(s), each an approved subscription's, and "
            f"{len(explained) - len(fulfilments)} the publisher's or the administrator's" + gap,
        )

    # ---------------------------------------------------------------- CT-11 the approvals
    problems = road_problems(lake_listings, road_subs, road_requests, road_members, profiles_by_id)
    approved = [s for s in road_subs if s[3] == "APPROVED"]
    if problems:
        checks.fail(
            "CT-11",
            "every access act on the lake went through the owner's approval",
            "; ".join(problems),
        )
    elif road_unread:
        checks.note(
            "CT-11",
            "every access act on the lake went through the owner's approval",
            f"not read: {', '.join(road_unread)}",
        )
    elif not lake_listings:
        checks.note(
            "CT-11",
            "every access act on the lake went through the owner's approval",
            "nothing of the lake is published",
        )
    else:
        checks.ok(
            "CT-11",
            "every access act on the lake went through the owner's approval",
            f"{len(lake_listings)} lake listing(s) requiring approval, {len(approved)} approved "
            "subscription(s), each a project's request approved by the owner, no direct Share; "
            "the publishing projects hold their designed members alone",
        )

    # ---------------------------------------------------------------- CT-12 what the lake publishes
    findings = [
        f"{t} is published and absent from data/publishing.tf's list"
        for _, t, _, _ in lake_listings
        if t not in PUBLISHED_LAKE_TABLES
    ]
    for table in road_tables:
        if table in classifications:
            findings.extend(classification_problems(table, classifications[table]))
    if findings:
        checks.fail(
            "CT-12",
            "the lake publishes the declared list, public or internal throughout",
            "; ".join(findings)
            + " - DataZone fulfils by name and reads no LF-Tag (Stage 6f decision 2)",
        )
    elif len(classifications) < len(road_tables):
        checks.note(
            "CT-12",
            "the lake publishes the declared list, public or internal throughout",
            f"not read: {', '.join(t for t in road_tables if t not in classifications)}",
        )
    else:
        checks.ok(
            "CT-12",
            "the lake publishes the declared list, public or internal throughout",
            "; ".join(f"{t} {'/'.join(table_classes(classifications[t]))}" for t in road_tables)
            + f", no column outside {' or '.join(CATALOG_ROAD_CLASSIFICATIONS)}",
        )

    # ---------------------------------------------------------------- the product end's records
    # The acts on each listed project table and its owner's members, as the lake's end holds them.
    product_subs: list = []  # road_subs's rows, over the product listings
    product_requests: dict = {}  # ACCEPTED request id -> (requester, reviewer)
    product_completed: dict = {}  # listing id -> subscription ids whose grant is COMPLETED
    for p in products:
        subs, accepted, done = acts(p.listing, p.table, product_unread)
        product_subs += subs
        product_requests.update(accepted)
        product_completed[p.listing] = done

    product_members: dict = {}  # owning project id -> its members, in road_members's rows
    for project in sorted({p.owner for p in products}):
        rows = road_members.get(project) or members_of(project, product_unread)
        if rows is not None:
            product_members[project] = rows
    for pair in product_requests.values():
        for uid in pair:
            if PROFILE_ID.fullmatch(uid):
                profile(uid, product_unread)

    # The accounts each project's environments live in: a fulfilment names the IAMPrincipals of
    # the subscriber's account, and a project's inventory answers that account's session.
    project_accounts: dict = {}  # project id -> account ids; absent when the read failed
    for pid, pname in projects.items():
        res = dat.run(
            "datazone",
            "list-environments",
            "--domain-identifier",
            domain_id,
            "--project-identifier",
            pid,
            "--query",
            "items[].awsAccountId",
            "--output",
            "json",
        )
        if res.ok:
            project_accounts[pid] = set(json_or_none(res.stdout) or [])
        else:
            product_unread.append(f"ListEnvironments {pname}")

    # What each deployment project subscribes to, asked by subscriber: no listing has to be known.
    target_subs: list = []  # (deployment project, subscription id, status, listing name)
    for pid, pname in projects.items():
        if pname not in DEPLOYMENT_PROJECTS:
            continue
        res = dat.run(
            "datazone",
            "list-subscriptions",
            "--domain-identifier",
            domain_id,
            "--owning-project-id",
            pid,
            "--output",
            "json",
        )
        if not res.ok:
            product_unread.append(f"list-subscriptions of {pname}")
            continue
        for item in (json_or_none(res.stdout) or {}).get("items", []):
            target_subs.append(
                (
                    pname,
                    item.get("id", "-"),
                    item.get("status", "-"),
                    (item.get("subscribedListing") or {}).get("name", "-"),
                )
            )

    # Whether a Glue table is a resource link, read in the account whose catalog holds it. A table
    # Glue no longer holds is no link: its asset outlived it.
    links_read: dict = {}  # (where, "<db>.<table>") -> (read, where the link points or "")
    tables_gone: set = set()

    def link_of(where: str, table: str) -> tuple:
        key = (where, table)
        if key not in links_read:
            read, target = False, ""
            if where in where_of.values():
                database, name = table.split(".", 1)
                res = cli_of[where].run(
                    "glue",
                    "get-table",
                    "--database-name",
                    database,
                    "--name",
                    name,
                    "--query",
                    "Table.TargetTable",
                    "--output",
                    "json",
                    tolerate="EntityNotFoundException",
                )
                if res.tolerated:
                    read = True
                    tables_gone.add(key)
                elif res.ok:
                    read, target = True, link_target(json_or_none(res.stdout), where_of)
            links_read[key] = (read, target)
        return links_read[key]

    tables_unread: list = []  # the tables Glue was not read for, as "<where>:<db>.<table>"
    link_listings: list = []  # (Product, where its link points)
    for p in products:
        read, target = link_of(p.where, p.table)
        if not read:
            tables_unread.append(f"{p.where}:{p.table}")
        elif target:
            link_listings.append((p, target))

    # Each project's inventory, read as the session of the account the project lives in. A Glue
    # table asset is judged; an asset of another type is counted.
    inventory: list = []  # (project, asset, "<db>.<table>", where, listed, link target or "")
    inventory_unread: list = []  # the projects whose inventory was not read whole
    inventory_assets = 0
    # (project name, asset id, asset name, the table its externalIdentifier names, its Curation),
    # for each Glue table asset (CT-22, CT-24)
    glue_assets: list = []
    for pid, pname in projects.items():
        homes = sorted(where_of[a] for a in project_accounts.get(pid, ()) if a in where_of)
        if not homes:
            inventory_unread.append(pname)
            continue
        found = cli_of[homes[0]].pages(
            "datazone",
            "search",
            "--domain-identifier",
            domain_id,
            "--search-scope",
            "ASSET",
            "--owning-project-identifier",
            pid,
            "--additional-attributes",
            "FORMS",
            token="nextToken",
        )
        if not found.complete:
            inventory_unread.append(pname)
        for entry in found.items("items"):
            asset = entry.get("assetItem") or {}
            inventory_assets += 1
            if not asset.get("typeIdentifier", "").endswith("GlueTableAssetType"):
                continue
            forms = {
                f.get("formName"): json_or_none(f.get("content")) or {}
                for f in (asset.get("additionalAttributes") or {}).get("formsOutput") or []
            }
            glue = forms.get("GlueTableForm") or {}
            where = where_of.get(glue.get("catalogId") or "-", "elsewhere")
            table = f"{glue.get('databaseName', '-')}.{glue.get('tableName', '-')}"
            details = forms.get("AssetCommonDetailsForm") or {}
            glue_assets.append(
                (
                    pname,
                    asset.get("identifier", "-"),
                    asset.get("name", "-"),
                    asset_table_label(asset.get("externalIdentifier") or "", pid, where_of),
                    Curation(
                        asset.get("description") or "",
                        details.get("readMe") or "",
                        classification_value(forms),
                        glue_table_label(details.get("sourceIdentifier") or "", where_of),
                    ),
                )
            )
            read, target = link_of(where, table)
            if not read:
                tables_unread.append(f"{where}:{table}")
            inventory.append(
                (
                    pname,
                    asset.get("name", "-"),
                    table,
                    where,
                    asset.get("identifier") in listed_assets,
                    target,
                )
            )
    tables_unread = sorted(set(tables_unread))

    # ---------------------------------------------------------------- CT-15 the stages that list
    ct15 = "Staging's project lists nothing, a chain's dev project by exception"
    staging_listed, dev_listed = stage_listings(listings, projects)
    production_listed = [n for _, n, _, p, _ in listings if projects.get(p) == PRODUCTION_PROJECT]
    if staging_listed:
        checks.fail(
            "CT-15",
            ct15,
            "; ".join(f"{project} lists {lname}" for lname, project in staging_listed)
            + " - Staging's sample data offered to every project's search (Stage 19 decisions 14 "
            "and 19 (c))",
        )
    elif not listings:
        checks.note("CT-15", ct15, "no listing published")
    elif dev_listed:
        checks.note(
            "CT-15",
            ct15,
            "; ".join(f"{project} lists {lname}" for lname, project in dev_listed)
            + " - a chain application's product is listed in Production alone (Stage 19 decision "
            "20 (b)); the gate is the template's default, and a member's portal publish lists",
        )
    else:
        checks.ok(
            "CT-15",
            ct15,
            f"{len(listings)} listings: {len(production_listed)} of {PRODUCTION_PROJECT}, none of "
            f"{STAGING_PROJECT} or of a chain application's dev project "
            f"({', '.join(CHAIN_DEV_PROJECTS.values())})",
        )

    # ---------------------------------------------------------------- CT-16 the product's access acts
    ct16 = "the access acts on a project's product, by the stage that owns it"
    act_problems, sandbox_acts = product_acts(
        products,
        product_subs,
        product_requests,
        product_members,
        profiles_by_id,
        projects,
        target_subs,
    )
    product_owner = {p.listing: p.owner for p in products}
    governed_acts = [
        s
        for s in product_subs
        if s[3] == "APPROVED" and projects.get(product_owner.get(s[0], "")) in DEPLOYMENT_PROJECTS
    ]
    governed = "no deployment project subscribes; " + (
        f"{len(governed_acts)} approved subscription(s) to a deployment project's listing, each a "
        "project's request a person among its members approved"
        if governed_acts
        else "no subscription to a deployment project's listing"
    )
    if act_problems:
        checks.fail("CT-16", ct16, "; ".join(act_problems) + " - Stage 19 decisions 13 and 15")
    elif product_unread:
        checks.note("CT-16", ct16, f"not read: {', '.join(product_unread)}")
    elif sandbox_acts:
        checks.note(
            "CT-16",
            ct16,
            "; ".join(
                f"{subscriber} reads {table} of {owner} by {shape} ({sid})"
                for sid, table, owner, subscriber, shape in sandbox_acts
            )
            + " - a Sandbox project shares its product as SMUS lets it, DataZone's subscription "
            f"the record (Stage 19 decisions 11 and 20 (b)); {governed}",
        )
    else:
        checks.ok("CT-16", ct16, f"{governed}; no access act on another project's product")

    # ---------------------------------------------------------------- CT-17 every product grant explained
    ct17 = "every grant on a project's listed table is explained"
    hidden_tables = (
        "; read through a data product, SearchListings omitting them (SUP-482): "
        + ", ".join(p.table for p in unsearched)
        if unsearched
        else ""
    )
    product_rows: dict = {}  # grant row -> why it exists, empty when nothing explains it
    for p in products:
        fulfilled = {
            s[5]: project_accounts.get(s[5])
            for s in product_subs
            if s[0] == p.listing
            and s[3] == "APPROVED"
            and s[4] == "project"
            and s[2] in product_completed.get(p.listing, set())
        }
        every_table = f"{p.table.split('.', 1)[0]}.ALL_TABLES"
        for g in grant_rows:
            if g[0] != p.where or g[2] not in TABLE_KINDS or g[3] not in (p.table, every_table):
                continue
            why = explain_product_grant(g, p.account, p.owner, fulfilled)
            if why or g not in product_rows:
                product_rows[g] = why
    product_fulfilments = [g for g, why in product_rows.items() if why.startswith("the fulfilment")]
    product_unexplained = [g for g, why in product_rows.items() if not why]
    # The accounts whose grants were not read whole: an absence there proves nothing (Lesson 62).
    unjudged = sorted({p.where for p in products if p.where == "elsewhere" or p.where in unlisted})
    product_where = {p.listing: p.where for p in products}
    product_unfulfilled = [
        s
        for s in product_subs
        if s[3] == "APPROVED"
        and product_where.get(s[0]) not in unjudged
        and not any(condition_project(g[6]) == s[5] and g[3] == s[1] for g in product_fulfilments)
    ]
    product_gap = (
        f"; {len(product_unfulfilled)} APPROVED subscription(s) with no grant on the table: "
        + ", ".join(s[2] for s in product_unfulfilled)
        if product_unfulfilled
        else ""
    )
    if product_unexplained:
        checks.fail(
            "CT-17",
            ct17,
            "; ".join(
                f"{g[0]}: {short_principal(g[1])} on {g[2]} {g[3]}: {g[4]}"
                + (f" (grantable {g[5]})" if g[5] != "-" else "")
                + (
                    f" [{projects.get(condition_project(g[6]), condition_project(g[6]))}]"
                    if condition_project(g[6])
                    else ""
                )
                for g in product_unexplained
            )
            + " - neither the owning project nor an approved subscription explains it",
        )
    elif not products:
        checks.note("CT-17", ct17, "no project table is listed")
    elif unjudged or product_unread:
        checks.note(
            "CT-17",
            ct17,
            f"{len(product_rows) - len(product_unexplained)} explained; not read: "
            + ", ".join(
                [
                    "the grants of an account no live session reads"
                    if w == "elsewhere"
                    else f"{w} grants"
                    for w in unjudged
                ]
                + product_unread
            )
            + product_gap
            + hidden_tables,
        )
    else:
        checks.ok(
            "CT-17",
            ct17,
            f"{len(product_rows)} grants on {', '.join(sorted({p.table for p in products}))}: "
            f"{len(product_fulfilments)} fulfilment(s), each an approved subscription's, and "
            f"{len(product_rows) - len(product_fulfilments)} the owning project's or the blueprint's"
            + product_gap
            + hidden_tables,
        )

    # ---------------------------------------------------------------- CT-18 the product's classification
    ct18 = "every product listing carries a classification, public or internal"
    listing_names = {lid: n for lid, n, _, _, _ in listings}
    carried = {
        aid: [(listing_names.get(pid, pid), product_classes.get(pid)) for pid in pids]
        for aid, pids in bundles.items()
    }
    class_problems, class_excepted = classification_findings(products, carried=carried)
    listings_unread = [u for u in product_unread if u.startswith("GetListing")]
    if class_problems:
        checks.fail(
            "CT-18",
            ct18,
            "; ".join(class_problems)
            + " - the form is a product's only classification, and a subscriber reads the table "
            "whole (Stage 19 decision 4)",
        )
    elif listings_unread:
        checks.note("CT-18", ct18, f"not read: {', '.join(listings_unread)}")
    elif not products:
        checks.note("CT-18", ct18, "no project table is listed")
    elif class_excepted:
        checks.note(
            "CT-18",
            ct18,
            "; ".join(
                f"{p.name} carries no form - {UNCLASSIFIED_BY_EXCEPTION[p.asset]}"
                for p in class_excepted
            )
            + f"; {len(products) - len(class_excepted)} other listing(s) read public or internal",
        )
    else:
        checks.ok(
            "CT-18",
            ct18,
            "; ".join(
                f"{p.name} {classification_label(p, carried)}"
                + (" (SearchListings omits it)" if p in unsearched and not p.product_only else "")
                for p in products
            ),
        )

    # ---------------------------------------------------------------- CT-19 the resource links
    ct19 = "no listing publishes a resource link"
    inventory_links = [row for row in inventory if row[5] and not row[4]]
    held_links = "; ".join(
        f"{asset} in {project} ({table} -> {target})"
        for project, asset, table, _, _, target in inventory_links
    )
    if link_listings:
        checks.fail(
            "CT-19",
            ct19,
            "; ".join(
                f"{p.name} of {projects.get(p.owner, p.owner)} lists {p.table}, a link to {target}"
                for p, target in link_listings
            )
            + " - another owner's table listed under the consumer's name (Stage 19 0.5)",
        )
    elif tables_unread or inventory_unread:
        checks.note(
            "CT-19",
            ct19,
            "not read: "
            + ", ".join(
                [f"table {t}" for t in tables_unread]
                + [f"the inventory of {n}" for n in inventory_unread]
            )
            + (f"; unlisted links in an inventory: {held_links}" if held_links else ""),
        )
    elif inventory_links:
        checks.note(
            "CT-19",
            ct19,
            f"{held_links} - unlisted: a source's import of the link its project's subscription "
            "created (Stage 19 0.5). CT-4 keeps a source from publishing it on import, and a "
            "member's publish would list it",
        )
    else:
        checks.ok(
            "CT-19",
            ct19,
            f"{len(products)} listed project table(s) and {len(inventory)} Glue table asset(s) "
            f"in {len(projects)} inventories, none a resource link",
        )

    # ---------------------------------------------------------------- CT-20 the S3 Access Grants
    # An S3 Object Collection is fulfilled by an S3 Access Grant in the account that holds the
    # bucket, written by the owning project's role (Stage 21 5.4). Each collection is read from its
    # listing, those a product carries and SearchListings omits included, and each subscription
    # from DataZone, under the collection's listing and every product listing that carries it.
    ct20 = "every S3 Access Grant a project role holds on another project's folder is explained"
    s3_unread: list = []
    owner_of = {lid: owner for lid, _, _, owner, _ in listings}
    collection_ids = {lid for lid, _, etype, _, _ in listings if etype == S3_COLLECTION_TYPE}
    collection_ids |= set(bundles) - set(owner_of)
    collections: dict = {}  # grant scope -> [(listing name, owning project, subscribed projects)]
    for lid in sorted(collection_ids):
        res = dat.run(
            "datazone",
            "get-listing",
            "--domain-identifier",
            domain_id,
            "--identifier",
            lid,
            "--output",
            "json",
            tolerate="AccessDeniedException",
        )
        if res.tolerated or not res.ok:
            s3_unread.append(f"GetListing {lid}")
            continue
        body = json_or_none(res.stdout) or {}
        form = listing_forms(body).get(S3_COLLECTION_FORM)
        if not isinstance(form, dict):
            continue
        scope = collection_scope(form.get("bucketArn") or "")
        carriers = bundles.get(lid, [])
        owner = owner_of.get(lid) or next((owner_of[c] for c in carriers if c in owner_of), "-")
        subscribed: set = set()
        for asked in [lid, *carriers]:
            res = dat.run(
                "datazone",
                "list-subscriptions",
                "--domain-identifier",
                domain_id,
                "--subscribed-listing-id",
                asked,
                "--status",
                "APPROVED",
                "--output",
                "json",
            )
            if not res.ok:
                s3_unread.append(f"list-subscriptions {asked}")
                continue
            for item in (json_or_none(res.stdout) or {}).get("items", []):
                project = (item.get("subscribedPrincipal") or {}).get("project") or {}
                subscribed.add(project.get("id", "-"))
        collections.setdefault(scope, []).append((body.get("name", lid), owner, subscribed))

    access_grants: list = []  # (grant id, location scope, grantee, permission, grant scope)
    if live[SANDBOX_PROFILE].live:
        located = sbx.run(
            "s3control",
            "list-access-grants-locations",
            "--account-id",
            consumer_account,
            "--output",
            "json",
        )
        granted = sbx.run(
            "s3control", "list-access-grants", "--account-id", consumer_account, "--output", "json"
        )
        if located.ok and granted.ok:
            scope_of = {
                loc.get("AccessGrantsLocationId"): loc.get("LocationScope", "-")
                for loc in (json_or_none(located.stdout) or {}).get("AccessGrantsLocationsList", [])
            }
            for g in (json_or_none(granted.stdout) or {}).get("AccessGrantsList", []):
                access_grants.append(
                    (
                        g.get("AccessGrantId", "-"),
                        scope_of.get(g.get("AccessGrantsLocationId"), "-"),
                        (g.get("Grantee") or {}).get("GranteeIdentifier", "-"),
                        g.get("Permission", "-"),
                        g.get("GrantScope", "-"),
                    )
                )
        else:
            s3_unread.append("the S3 Access Grants of the consumer account")
    else:
        s3_unread.append("the consumer account")

    verdicts = [(g, explain_access_grant(g[1], g[2], g[4], collections)) for g in access_grants]
    judged = [(g, why) for g, why in verdicts if why is not None]
    unexplained = [g for g, why in judged if not why]
    fulfilled = [(g, why) for g, why in judged if why.startswith("the fulfilment")]
    if unexplained:
        checks.fail(
            "CT-20",
            ct20,
            "; ".join(f"{short_principal(g[2])} {g[3]} on {g[4]}" for g in unexplained)
            + " - a project reads another's folder with no approved subscription to a collection "
            "at that scope",
        )
    elif s3_unread:
        checks.note("CT-20", ct20, f"not read: {', '.join(s3_unread)}")
    elif not fulfilled:
        checks.note(
            "CT-20",
            ct20,
            f"no fulfilment among {len(access_grants)} grant(s); "
            f"{sum(len(v) for v in collections.values())} S3 Object Collection listing(s)",
        )
    else:
        checks.ok(
            "CT-20",
            ct20,
            "; ".join(f"{g[3]} on {g[4]}: {why}" for g, why in fulfilled),
        )

    # ---------------------------------------------------------------- the lineage graph
    # Every lineage read is the domain's and is asked of the registry's session: ListLineageEvents
    # answered the same 394 events to each of the four accounts' sessions, and GetLineageNode an
    # asset's node of a deployment project to the registry's (read 2026-11-24, Stage 20 xxi).
    lineage_live = bool(domain_id) and live[DATA_PROFILE].live
    since = (datetime.now(timezone.utc) - timedelta(days=LINEAGE_WINDOW_DAYS)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    lineage_events: list = []
    events_read = False
    if lineage_live:
        res = dat.run(
            "datazone",
            "list-lineage-events",
            "--domain-identifier",
            domain_id,
            "--timestamp-after",
            since,
            "--output",
            "json",
        )
        if res.ok:
            events_read = True
            lineage_events = (json_or_none(res.stdout) or {}).get("items", [])
    result, detail = event_verdict(lineage_events, since, events_read)
    ct21 = f"the lineage events of the last {LINEAGE_WINDOW_DAYS} days by processingStatus"
    checks.add(result, "CT-21", ct21, detail)

    # A node read at an event's timestamp carries that event's edges alone (Stage 20 2.4), so the
    # run that wrote a dataset node is found by reading its versions newest first.
    nodes_read: dict = {}  # (node id, event timestamp or "") -> its body; {} not found; None unread

    def lineage_node(nid: str, at: str = "") -> dict | None:
        key = (nid, at)
        if key not in nodes_read:
            args = ["datazone", "get-lineage-node", "--domain-identifier", domain_id]
            args += ["--identifier", nid] + (["--event-timestamp", at] if at else [])
            res = dat.run(*args, "--output", "json", tolerate="ResourceNotFoundException")
            if res.tolerated:
                nodes_read[key] = {}
            else:
                nodes_read[key] = (json_or_none(res.stdout) or {}) if res.ok else None
        return nodes_read[key]

    writers: dict = {}  # dataset node id -> feeders() of its newest fed version; None unread

    def fed_by(nid: str) -> tuple | None:
        if nid not in writers:
            res = dat.run(
                "datazone",
                "list-lineage-node-history",
                "--domain-identifier",
                domain_id,
                "--identifier",
                nid,
                "--sort-order",
                "DESCENDING",
                "--output",
                "json",
            )
            found: tuple | None = ("", "") if res.ok else None
            versions = (json_or_none(res.stdout) or {}).get("nodes", []) if res.ok else []
            for version in versions[:LINEAGE_VERSIONS_READ]:
                body = lineage_node(nid, version.get("eventTimestamp") or "")
                ups = [u.get("id") for u in (body or {}).get("upstreamNodes") or []]
                if body is None or ups:
                    bodies = [lineage_node(u) for u in ups]
                    found = None if body is None or None in bodies else feeders(bodies)
                    break
            writers[nid] = found
        return writers[nid]

    asset_lineage: list = []  # AssetLineage rows (CT-22)
    carried: set = set()  # the dataset node ids an asset's node hangs from (CT-23)
    for project, asset_id, name, own, curation in glue_assets:
        body = lineage_node(ASSET_NODE_PREFIX + asset_id) if lineage_live else None
        upstream: list = []
        complete = body is not None
        for up in (body or {}).get("upstreamNodes") or []:
            nid = up.get("id") or "-"
            carried.add(nid)
            node = lineage_node(nid)
            fed = fed_by(nid) if node else None
            if node is None or fed is None:
                complete = False
            kind, names = fed or ("", "")
            source = (node or {}).get("sourceIdentifier") or (node or {}).get("name") or nid
            label = glue_table_label(source, where_of) or mask_account(source)
            upstream.append((label, kind, names))
        asset_lineage.append(
            AssetLineage(
                project,
                project in DEPLOYMENT_PROJECTS,
                name,
                own,
                curation.named,
                tuple(upstream),
                complete,
            )
        )
    result, detail = lineage_verdict(asset_lineage, inventory_unread)
    ct22 = "each Glue table asset hangs from its own table's node, fed by a job's run or a listing"
    checks.add(result, "CT-22", ct22, detail)

    # The registry's trail records each node's creation with its id and sourceIdentifier (SUP-347),
    # the one listing of the nodes the API has; its 90 days hold every node since the domain's
    # first event of 2026-10-19 until 2027-01-17.
    table_nodes: list = []  # (node id, table label) of each Glue table node the trail created
    nodes_unread: list = [f"the inventory of {n}" for n in inventory_unread]
    if not lineage_live:
        nodes_unread.append("the lineage graph")
    if live[DATA_PROFILE].live:
        res = dat.run(
            "cloudtrail",
            "lookup-events",
            "--lookup-attributes",
            "AttributeKey=EventName,AttributeValue=CreateLineageNode",
            "--output",
            "json",
        )
        if res.ok:
            for event in (json_or_none(res.stdout) or {}).get("Events", []):
                extra = (json_or_none(event.get("CloudTrailEvent", "")) or {}).get(
                    "additionalEventData"
                ) or {}
                label = glue_table_label(extra.get("sourceIdentifier") or "", where_of)
                if extra.get("typeName") == DATASET_NODE_TYPE and label and extra.get("identifier"):
                    table_nodes.append((extra["identifier"], label))
        else:
            nodes_unread.append("the registry's trail")
    else:
        nodes_unread.append("the registry's trail")
    result, detail = orphan_verdict(table_nodes, carried, nodes_unread)
    checks.add(result, "CT-23", "every Glue table node is carried by an asset", detail)

    # A deployment project's asset against the asset of the same table in a chain application's
    # dev project, which the release's bundle exported (Stage 20 xxi).
    dev_names = set(CHAIN_DEV_PROJECTS.values())
    dev_assets: dict = {}  # "<db>.<table>" -> (dev project name, its Curation)
    for project, _, _, own, curation in glue_assets:
        if project in dev_names and own:
            dev_assets.setdefault(own.split(":", 1)[1], (project, curation))
    curation_pairs: list = []
    for project, _, name, own, curation in glue_assets:
        if project not in DEPLOYMENT_PROJECTS:
            continue
        dev_project, dev = dev_assets.get(own.split(":", 1)[-1], ("", None))
        curation_pairs.append((project, name, own, curation, dev_project, dev))
    curation_unread = [n for n in inventory_unread if n in DEPLOYMENT_PROJECTS or n in dev_names]
    result, detail = curation_verdict(curation_pairs, curation_unread)
    ct24 = "a deployment project's asset carries its dev asset's curation and names its own table"
    checks.add(result, "CT-24", ct24, detail)

    # ---------------------------------------------------------------- the LF-Tag ontology
    tag_rows: list = []
    for label, cli, profile in (
        ("registry", dat, DATA_PROFILE),
        ("consumer", sbx, SANDBOX_PROFILE),
    ):
        if not live[profile].live:
            continue
        res = cli.run("lakeformation", "list-lf-tags", "--output", "json")
        for t in (json_or_none(res.stdout) or {}).get("LFTags", []):
            tag_rows.append((label, t.get("TagKey", "-"), ",".join(t.get("TagValues") or [])))

    # ---------------------------------------------------------------- the report
    with out_path.open("w", encoding="utf-8") as fh:
        rep = Report(fh)
        rep.banner("The SageMaker Catalog over the governed lake")
        rep.line(f"generated {context.utc_stamp()}")
        rep.line()
        rep.text(
            "The catalog road and the register road are different systems. This report reads both:\n"
            "sections 1 to 4 are the catalog (DataZone), section 5 is Lake Formation, section 6\n"
            "joins them on the lake's published tables and section 7 on a project's own listed\n"
            "table, and CT-7, CT-10 and CT-17 are the question of whether one has reached into\n"
            "the other. Section 8 reads the lineage graph the domain draws from the posted events."
        )

        rep.h1("1. The domain")
        rep.tabulate(
            ["READ FROM\tDOMAIN\tNAME\tSTATUS\tOWNED BY"]
            + [
                f"registry\t{i}\t{n}\t{s}\t{'registry' if m == registry_account else 'ELSEWHERE'}"
                for i, n, s, m in domains
            ]
            + [
                f"consumer\t{i}\t{n}\t{s}\t{'consumer' if m == consumer_account else 'registry (association)'}"
                for i, n, s, m in sandbox_domains
            ]
        )
        rep.line()
        rep.tabulate(["PROJECT\tNAME"] + [f"{i}\t{n}" for i, n in projects.items()])

        rep.h1("2. The listings, and what they have granted")
        if not listings:
            rep.text("Nothing is published.")
        else:
            rep.tabulate(
                ["LISTING\tTYPE\tREV\tOWNER PROJECT\tSUBS\tREQUESTS\tGRANTS"]
                + [
                    f"{n}\t{t}\t{rv}\t{projects.get(p, p)}\t" + "\t".join(access_rows[i][1:])
                    for i, (_, n, t, p, rv) in enumerate(listings)
                ]
            )

        rep.h1("3. The data sources")
        if not sources:
            rep.text("No data source.")
        else:
            rep.tabulate(
                [
                    "PROJECT\tSOURCE\tTYPE\tPUBLISH ON IMPORT\tAI NAMES\tSCHEDULE\tSTATUS\tASSETS\tRUNS"
                ]
                + [
                    f"{p}\t{n}\t{t}\t{'YES' if poi else 'no'}\t{'yes' if ai else 'no'}\t{s}\t{st}\t{a}\t"
                    + (", ".join(f"{v} {k}" for k, v in sorted(runs.get(d, {}).items())) or "none")
                    for p, n, t, poi, ai, s, st, a, d in sources
                ]
            )
        rep.line()
        if not starts:
            rep.text("No StartDataSourceRun in any trail's 90 days (CT-13).")
        else:
            rep.text(
                "The starts CloudTrail holds, each judged against the source's project (CT-13):"
            )
            rep.tabulate(
                ["STARTED (UTC)\tCALLER\tSOURCE\tSOURCE'S PROJECT\tVERDICT"]
                + [
                    f"{t}\t{projects.get(c, c)}\t{d}\t{projects.get(o, o or '-')}\t{v}"
                    for t, v, c, d, o, _ in starts
                ]
            )

        rep.h1("4. The domain's authorization policies")
        rep.tabulate(["POLICY TYPE\tPRINCIPALS"] + [f"{pt}\t{v}" for pt, v in policy_grants])

        rep.h1("5. The Lake Formation grants a SMUS principal holds")
        if not smus_grants:
            rep.text("None.")
        else:
            rep.tabulate(
                ["WHERE\tPRINCIPAL\tKIND\tRESOURCE\tPERMISSIONS\tWITH GRANT\tCONDITION"]
                + [
                    f"{w}\t{short_principal(p)}\t{k}\t{r}\t{perm}\t{wg}\t{'projectId' if 'projectId' in c else (c or '-')}"
                    for w, p, k, r, perm, wg, c in smus_grants
                ]
            )
        rep.line()
        rep.text(
            f"Every grant read: {len(grant_rows)} ({len(smus_grants)} SMUS-managed). The rest are the\n"
            "register's own, and docs/AWS_STATE.md is where they are judged."
        )
        rep.line()
        rep.tabulate(
            ["WHERE\tGRANTS\tPAGES\tLISTING"]
            + [
                f"{w}\t{g}\t{p}\t"
                + ("read to its last page" if whole else "NOT read to its last page - section 12")
                for w, (g, p, whole) in lf_read.items()
            ]
        )

        rep.h1("6. The catalog road into the lake")
        if not lake_listings:
            rep.text("No lake table is published.")
        else:
            rep.tabulate(
                ["LISTING\tTABLE\tOWNER PROJECT\tAPPROVAL REQUIRED"]
                + [f"{lid}\t{t}\t{projects.get(o, o)}\t{a}" for lid, t, o, a in lake_listings]
            )
            rep.line()
            rep.tabulate(
                ["TABLE\tSUBSCRIPTION\tSTATUS\tPRINCIPAL\tREQUEST\tREQUESTER\tREVIEWER\tGRANT"]
                + [
                    f"{t}\t{sid}\t{st}\t{kind} {projects.get(p, p)}\t{rid}\t"
                    + "\t".join(road_requests.get(rid, ("-", "-")))
                    + f"\t{'COMPLETED' if sid in completed.get(lid, set()) else '-'}"
                    for lid, t, sid, st, kind, p, rid in road_subs
                ]
            )
            rep.line()
            rep.tabulate(
                ["PUBLISHING PROJECT\tMEMBER\tDESIGNATION\tPRINCIPAL"]
                + [
                    f"{projects.get(p, p)}\t{k} {mid}\t{d}\t"
                    + (
                        short_principal(arn)
                        if arn != "-"
                        else profiles_by_id.get(mid, ("-",))[0]
                        + (
                            f" {short_principal(profiles_by_id[mid][1])}"
                            if profiles_by_id.get(mid, ("-", "-"))[1] != "-"
                            else ""
                        )
                    )
                    for p, rows in road_members.items()
                    for k, mid, d, arn in rows
                ]
            )
        rep.line()
        rep.tabulate(
            ["ROAD TABLE\tON THE TABLE\tON A COLUMN"]
            + [
                f"{t}\t"
                + (
                    ",".join(table_classes(classifications[t])) or "none"
                    if t in classifications
                    else "NOT READ"
                )
                + "\t"
                + (
                    "; ".join(
                        f"{c.get('Name')}={v}"
                        for c in classifications.get(t, {}).get("LFTagsOnColumns") or []
                        for v in classes(c.get("LFTags"))
                    )
                    or "-"
                )
                for t in road_tables
            ]
        )
        rep.line()
        rep.text("Each grant on a road table, and why it exists (CT-10):")
        rep.tabulate(
            ["PRINCIPAL\tKIND\tTABLE\tPERMISSIONS\tWITH GRANT\tWHY"]
            + [
                f"{short_principal(g[1])}\t{g[2]}\t{g[3]}\t{g[4]}\t{g[5]}\t{why or 'UNEXPLAINED'}"
                for g, why in explained + unexplained
            ]
        )

        rep.h1("7. The catalog road for a project's own table")

        def link_cell(where: str, table: str) -> str:
            read, target = link_of(where, table)
            if not read:
                return "NOT READ"
            if (where, table) in tables_gone:
                return "no such table"
            return target or "-"

        if not products:
            rep.text("No project table is listed.")
        else:
            listing_name = {lid: n for lid, n, _, _, _ in listings}
            rep.tabulate(
                [
                    "LISTING\tNAME\tTABLE\tWHERE\tOWNER PROJECT\tAPPROVAL REQUIRED\tCLASSIFICATION"
                    "\tDATA PRODUCT\tRESOURCE LINK TO"
                ]
                + [
                    f"{p.listing}\t{p.name}\t{p.table}\t{p.where}\t{projects.get(p.owner, p.owner)}"
                    f"\t{p.approval}\t"
                    + classification_label(p, carried)
                    + "\t"
                    + (", ".join(listing_name.get(b, b) for b in bundles.get(p.listing, [])) or "-")
                    + f"\t{link_cell(p.where, p.table)}"
                    for p in products
                ]
            )
            rep.line()
            if not product_subs:
                rep.text("No subscription to a project's table.")
            else:
                rep.tabulate(
                    ["TABLE\tSUBSCRIPTION\tSTATUS\tPRINCIPAL\tREQUEST\tREQUESTER\tREVIEWER\tGRANT"]
                    + [
                        f"{t}\t{sid}\t{st}\t{kind} {projects.get(pr, pr)}\t{rid}\t"
                        + "\t".join(product_requests.get(rid, ("-", "-")))
                        + f"\t{'COMPLETED' if sid in product_completed.get(lid, set()) else '-'}"
                        for lid, t, sid, st, kind, pr, rid in product_subs
                    ]
                )
            rep.line()
            rep.text(
                "Each grant on a listed project table or on every table of its database, and why it\n"
                "exists (CT-17):"
            )
            rep.tabulate(
                ["WHERE\tPRINCIPAL\tKIND\tTABLE\tPERMISSIONS\tWITH GRANT\tCONTEXT\tWHY"]
                + [
                    f"{g[0]}\t{short_principal(g[1])}\t{g[2]}\t{g[3]}\t{g[4]}\t{g[5]}\t"
                    + (projects.get(condition_project(g[6]), condition_project(g[6])) or "-")
                    + f"\t{why or 'UNEXPLAINED'}"
                    for g, why in product_rows.items()
                ]
            )
        rep.line()
        if not target_subs:
            rep.text("No deployment project holds a subscription (CT-16).")
        else:
            rep.text("What each deployment project subscribes to (CT-16):")
            rep.tabulate(
                ["PROJECT\tSUBSCRIPTION\tSTATUS\tLISTING"]
                + [f"{p}\t{sid}\t{st}\t{n}" for p, sid, st, n in target_subs]
            )
        rep.line()
        rep.text(
            f"The inventories: {inventory_assets} assets in {len(projects)} projects, "
            f"{len(inventory)} of them Glue tables (CT-19)."
            + (f" Not read whole: {', '.join(inventory_unread)}." if inventory_unread else "")
        )
        if inventory:
            rep.tabulate(
                ["PROJECT\tASSET\tTABLE\tWHERE\tLISTED\tRESOURCE LINK TO"]
                + [
                    f"{project}\t{asset}\t{table}\t{where}\t{'yes' if listed else 'no'}"
                    f"\t{link_cell(where, table)}"
                    for project, asset, table, where, listed, _ in inventory
                ]
            )

        rep.h1("8. The lineage graph")
        if not events_read:
            rep.text("ListLineageEvents was not read (CT-21).")
        else:
            statuses: dict = {}
            for e in lineage_events:
                job = ((e.get("eventSummary") or {}).get("openLineageRunEventSummary") or {}).get(
                    "job"
                ) or {}
                key = (mask_account(job.get("namespace") or "-"), e.get("processingStatus") or "-")
                statuses[key] = statuses.get(key, 0) + 1
            rep.text(f"The lineage events posted since {since}, by job namespace (CT-21):")
            rep.tabulate(
                ["JOB NAMESPACE\tPROCESSING STATUS\tEVENTS"]
                + [f"{ns}\t{st}\t{n}" for (ns, st), n in sorted(statuses.items())]
            )
        rep.line()
        if not asset_lineage:
            rep.text("No Glue table asset was read (CT-22).")
        else:
            rep.text(
                "Each Glue table asset, the nodes its lineage node hangs from and what fed each\n"
                "one's newest version with an upstream: a job's run, or a listing for a\n"
                "subscription's table (CT-22). OWN TABLE is the table its externalIdentifier names,\n"
                "FORMS NAME the one its sourceIdentifier names:"
            )
            rep.tabulate(
                ["PROJECT\tASSET\tOWN TABLE\tFORMS NAME\tHANGS FROM\tFED BY"]
                + [
                    f"{r.project}\t{r.asset}\t{r.own or '-'}\t{r.named or '-'}\t"
                    + (", ".join(t for t, _, _ in r.upstream) or ("-" if r.read else "NOT READ"))
                    + "\t"
                    + (", ".join(fed_by_label(k, n) for _, k, n in r.upstream) or "-")
                    for r in asset_lineage
                ]
            )
        rep.line()
        orphans = sorted({(label, nid) for nid, label in table_nodes if nid not in carried})
        if not orphans:
            rep.text(f"Every one of the {len(table_nodes)} Glue table nodes is carried (CT-23).")
        else:
            rep.text("The Glue table nodes no asset's node hangs from (CT-23):")
            rep.tabulate(["TABLE\tNODE"] + [f"{label}\t{nid}" for label, nid in orphans])
        rep.line()
        if not curation_pairs:
            rep.text("No Glue table asset in a deployment project (CT-24).")
        else:

            def same(a, b) -> str:
                return "same" if a == b else "DIFFERS"

            rep.text("Each deployment project's asset against its dev asset (CT-24):")
            rep.tabulate(
                ["PROJECT\tASSET\tDEV PROJECT\tDESCRIPTION\tREADME\tCLASSIFICATION\tFORMS NAME"]
                + [
                    f"{project}\t{name}\t{dev_project or '-'}\t"
                    + (
                        "\t".join(
                            same(getattr(mine, f), getattr(dev, f))
                            for f in ("description", "readme", "classification")
                        )
                        if dev
                        else "-\t-\t-"
                    )
                    + f"\t{mine.named or '-'}"
                    for project, name, _, mine, dev_project, dev in curation_pairs
                ]
            )

        rep.h1("9. The LF-Tag ontology, by account")
        if not tag_rows:
            rep.text("No LF-Tag is defined in either account.")
        else:
            rep.tabulate(["WHERE\tKEY\tVALUES"] + [f"{w}\t{k}\t{v}" for w, k, v in tag_rows])

        rep.h1("10. Checks")
        rep.checks_table(checks)

        rep.h1("11. What this report cannot see")
        rep.text(
            "DataZone refuses GetAsset and GetDataProduct to InfrastructureAccess in Data Governance\n"
            "(Stage 6f 0.6), the session this report reads the domain with, so the asset behind a\n"
            "listing is read through GetListing or not at all, and a DENIED cell in section 4 is the\n"
            "permission ceiling rather than an empty policy. The Sandbox session is answered, as a\n"
            "contributor of both projects. A fulfilment lands where CT-7 and CT-10 look (measured\n"
            "2026-10-26, Stage 6f 11.9). A direct Share ran once, on a Sandbox project's product and\n"
            "no lake listing (Stage 19 pass 2, 2026-11-14): it left a request made by a member of the\n"
            "owning project, accepted at creation with no reviewer. CT-11 fails on that record and\n"
            "on a subscription with no accepted request, on a lake listing; CT-16 fails on it on a\n"
            "deployment project's listing and names it in a note on a Sandbox project's."
        )
        rep.line()
        rep.text(
            "On the product road, a project's inventory is read with datazone:Search as the session\n"
            "of the account the project's environments live in, so a project with no environment is\n"
            "not read (CT-19). A subscription to a data product is listed under each asset listing\n"
            "the product carries, and its grant under the asset listing alone (SUP-363); both ids\n"
            "are asked. A listing of another asset type, a Bedrock model or a Redshift table, is on\n"
            "neither road: CT-15 counts it by owner and no check judges its grants. A table a data\n"
            "product's publication listed reads INACTIVE and SearchListings omits it (SUP-482):\n"
            "each product listing's items are read with GetListing, and such a table is in section\n"
            "7 with its product named, and absent from section 2."
        )
        rep.line()
        rep.text(
            "Lake Formation lists no grant to an Identity Center principal. The provisioning role\n"
            "grants arn:aws:identitystore:::user/* on a project's database and its tables under the\n"
            "project condition (CloudTrail BatchGrantPermissions); ListPermissions by resource omits\n"
            'it, and by principal answers InvalidInputException, "LakeFormation Identity Center\n'
            'Configuration not configured for requested catalog". CT-7, CT-8 and CT-10 judge the\n'
            "role and IAMPrincipals grants of section 5 alone; a subscription to a user or a group,\n"
            "which would be fulfilled for an Identity Center principal, fails CT-11 instead."
        )
        rep.line()
        rep.text(
            "The lineage graph is read as the registry's session, which every lineage read answers\n"
            "as it answers each account's. An asset's node carries its edges to the dataset nodes\n"
            "as they stand, whatever version is asked (measured 2026-11-24, Stage 20 xxi), so CT-22\n"
            "reads where an asset hangs now, not where it hung. The Glue table nodes CT-23 judges\n"
            "are those CreateLineageNode records in the registry's trail, 90 days of them: every\n"
            "node since the domain's first event of 2026-10-19, until 2027-01-17."
        )
        rep.line()
        rep.text(
            "CT-13 reads CloudTrail's last 90 days. The domain's account records a start from another\n"
            "account with that account and the role's id alone: the caller's own copy names the role,\n"
            "so the Interactive account's and both deployment targets' trails are read beside the\n"
            "registry's (Stage 19 pass 4)."
        )

        rep.h1("12. Calls that failed")
        failed_calls_epilogue(rep, errors)

    n_fail = checks.n_fail()
    note(
        f"wrote {out_label}",
        f"checks: {len(checks.rows) - n_fail} passed or noted, {n_fail} FAILED"
        if n_fail
        else "all checks passed",
    )
    if n_fail:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
