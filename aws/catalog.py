#!/usr/bin/env -S uv run --quiet
# catalog.py - the SageMaker Catalog over the governed lake: what the business catalog holds, what
#              it has granted, and which Lake Formation grants a SMUS-managed principal carries.
#
#   needs:    a live SSO session for the infrastructure user; one login covers both profiles:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/catalog.py
#   writes:   aws/output/catalog.txt   (untracked - see .gitignore)
#   reads:    in Data Governance - datazone:ListDomains, GetDomain, ListProjects,
#             ListProjectMemberships, GetUserProfile, GetGroupProfile, SearchListings, GetListing,
#             ListDataSources, GetDataSource, ListSubscriptions, ListSubscriptionRequests,
#             ListSubscriptionGrants, ListPolicyGrants, ListLineageEvents,
#             lakeformation:ListPermissions, GetResourceLFTags, ListLFTags, glue:GetDatabases; in
#             Sandbox - lakeformation:ListPermissions, ListLFTags, glue:GetDatabases; and
#             sts:GetCallerIdentity. Every one is a read.
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# THE TWO ROADS AN ACCESS ACT CAN TAKE, which is what this script exists to keep apart. On the
# catalog road a subscription or a direct Share is approved in the portal and DataZone writes a Lake
# Formation grant in the account that owns the table (INT-23). On the register road a grant is
# written by Terraform and carries a row in docs/AWS_STATE.md's grant register. Since Stage 6f
# decision 2 (2026-10-27) the catalog road's grants on the lake are registered by reading: DataZone's
# subscription is each grant's record, and CT-10 is the join that fails on a grant no subscription
# explains. Section 5 reads Lake Formation, section 6 the road's records, and CT-7 and CT-10 are the
# comparison.
#
# The checks:
#   CT-1  one domain, AVAILABLE, in the registry account - and no domain in the consumer account
#         (D26: the registry and the runtimes are different accounts).
#   CT-2  every listing names an owning project that exists, and its type is reported.
#   CT-3  the access acts: subscriptions, requests and grants per listing. Zero is the reading
#         today; when one exists, CT-7 is what says whether it is registered.
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
#
# CT-7 and CT-8 read every page of ListPermissions in both accounts: the CLI has no paginator for
# that operation, so one call answers the first page and a NextToken. A listing not read to its
# last page leaves both checks a note, never a pass; a grant it did read still fails them.
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

from __future__ import annotations

import json
import re
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "catalog.txt"

# The registry account holds the domain (D22, D26); the Interactive account holds the projects'
# compute and the Lake Formation grants SMUS writes for them.
DATA_PROFILE = "awsds-infra-data"
SANDBOX_PROFILE = "awsds-infra-sandbox-1"

# The governed lake's databases, in the registry account. A SMUS principal reaching one of these is
# CT-7's finding; a project's own database is not.
LAKE_DATABASES = ("raw", "curated", "dropbox")

# The lake tables the lake-publishing pilot publishes (Stage 6f decision 1, step 11), as
# `<database>.<table>`: the same list as data-governance/data/publishing.tf's `published_tables`.
# A SMUS grant on one of these is the catalog road's; a table published there and missing here
# fails CT-7, which is the reading that keeps the two lists together (Lesson 14).
PUBLISHED_LAKE_TABLES = ("curated.trades",)

# The classifications the catalog road admits on a published table and on each of its columns
# (Stage 6f decision 2, CT-12): data/publishing.tf refuses the same at plan.
CATALOG_ROAD_CLASSIFICATIONS = ("public", "internal")

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
SMUS_ROLE_MARKERS = (
    PROJECT_ROLE_MARKER,
    "-smus-provisioning",
    "-smus-manage-access",
    "AmazonDataZone",
)
IAM_PRINCIPALS_SUFFIX = ":IAMPrincipals"

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
FAILING_BY_EXCEPTION = {
    "Tooling-default-sagemaker-modelpackagegroup-datasource": (
        "EXC-11: the Tooling blueprint's own source, one per project, tracking an asset type this "
        "estate has never produced; it bills nothing and creates nothing"
    ),
}

# The two that must stay empty for the owner project's approval to be the control (CT-9).
OVERRIDE_TYPES = ("OVERRIDE_DOMAIN_UNIT_OWNERS", "OVERRIDE_PROJECT_OWNERS")


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
    """GetListing's forms, which the API returns as a JSON string inside the asset listing."""
    raw = ((body.get("item") or {}).get("assetListing") or {}).get("forms")
    if isinstance(raw, dict):
        return raw
    return json_or_none(raw) or {}


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


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    errors = ErrorLog()
    callers = profiles.preflight([DATA_PROFILE, SANDBOX_PROFILE], errors, out_label=out_label)
    live = {c.profile: c for c in callers}
    dat = AwsCli(profile=DATA_PROFILE, region=context.REGION, errors=errors, echo_profile=True)
    sbx = AwsCli(profile=SANDBOX_PROFILE, region=context.REGION, errors=errors, echo_profile=True)
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

    # ---------------------------------------------------------------- CT-2 the listings
    listings: list = []
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

    # ---------------------------------------------------------------- the grants, both accounts
    grant_rows: list = []
    lf_read: dict = {}  # where -> (grants, pages, read to the last page)
    for label, cli, profile in (
        ("registry", dat, DATA_PROFILE),
        ("consumer", sbx, SANDBOX_PROFILE),
    ):
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
    catalog_road = [g for g in lake_grants if on_catalog_road(g[1], g[2], g[3], g[4])]
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
    # A listing is the lake's when its Glue table form names a lake database in the registry
    # account's catalog. SearchListings carries no form, so each Glue table listing is read whole.
    road_unread: list = []  # the reads CT-10 and CT-11 could not make; an absence there proves nothing
    lake_listings: list = []  # (listing id, "<db>.<table>", owning project, approvalRequired)
    for lid, _, etype, owner, _ in listings:
        if etype != "GlueTableAssetType":
            continue
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
        if not res.ok:
            road_unread.append(f"GetListing {lid}")
            continue
        forms = listing_forms(json_or_none(res.stdout) or {})
        glue = forms.get("GlueTableForm") or {}
        if (
            glue.get("catalogId") != registry_account
            or glue.get("databaseName") not in LAKE_DATABASES
        ):
            continue
        lake_listings.append(
            (
                lid,
                f"{glue.get('databaseName')}.{glue.get('tableName', '-')}",
                owner,
                (forms.get("SubscriptionTermsForm") or {}).get("approvalRequired", "-"),
            )
        )

    road_subs: list = []  # (listing id, table, subscription id, status, principal kind, project, request)
    road_requests: dict = {}  # ACCEPTED request id -> (requester, reviewer)
    completed: dict = {}  # listing id -> subscription ids whose grant is COMPLETED
    for lid, table, _, _ in lake_listings:
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
                road_unread.append(f"{verb} {lid}")
                continue
            for item in (json_or_none(res.stdout) or {}).get("items", []):
                if verb == "list-subscriptions":
                    principal = item.get("subscribedPrincipal") or {}
                    road_subs.append(
                        (
                            lid,
                            table,
                            item.get("id", "-"),
                            item.get("status", "-"),
                            next(iter(principal), "-"),
                            (principal.get("project") or {}).get("id", "-"),
                            item.get("subscriptionRequestId") or "-",
                        )
                    )
                elif verb == "list-subscription-requests":
                    road_requests[item.get("id", "-")] = (
                        item.get("createdBy", "-"),
                        item.get("reviewerId", "-"),
                    )
                elif item.get("status") == "COMPLETED":
                    completed.setdefault(lid, set()).add(item.get("subscriptionId", "-"))

    # The publishing projects' members, each resolved to what it is: an approver holds the project
    # role's sessions too, so the membership is the boundary of who can regrant a published table.
    road_members: dict = {}  # project id -> [(kind, member id, designation, role ARN or "-")]
    profiles_by_id: dict = {}  # user profile id -> (type, IAM ARN or "-")

    def profile(user_id: str) -> tuple:
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
                road_unread.append(f"GetUserProfile {user_id}")
            profiles_by_id[user_id] = (
                body.get("type", "-"),
                ((body.get("details") or {}).get("iam") or {}).get("arn", "-"),
            )
        return profiles_by_id[user_id]

    for project in sorted({owner for _, _, owner, _ in lake_listings}):
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
            road_unread.append(f"ListProjectMemberships {project}")
            continue
        rows = []
        for m in (json_or_none(res.stdout) or {}).get("members", []):
            details = m.get("memberDetails") or {}
            if "user" in details:
                uid = (details.get("user") or {}).get("userId", "-")
                profile(uid)
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
                    road_unread.append(f"GetGroupProfile {gid}")
                body = json_or_none(res.stdout) or {}
                rows.append(
                    ("group", gid, m.get("designation", "-"), body.get("rolePrincipalArn") or "-")
                )
        road_members[project] = rows
    for requester, _ in road_requests.values():
        profile(requester)

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
            "joins them on the lake's published tables, and CT-7 and CT-10 are the question of\n"
            "whether one has reached into the other."
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
                + ("read to its last page" if whole else "NOT read to its last page - section 10")
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

        rep.h1("7. The LF-Tag ontology, by account")
        if not tag_rows:
            rep.text("No LF-Tag is defined in either account.")
        else:
            rep.tabulate(["WHERE\tKEY\tVALUES"] + [f"{w}\t{k}\t{v}" for w, k, v in tag_rows])

        rep.h1("8. Checks")
        rep.checks_table(checks)

        rep.h1("9. What this report cannot see")
        rep.text(
            "DataZone refuses GetAsset and GetDataProduct to InfrastructureAccess in Data Governance\n"
            "(Stage 6f 0.6), the session this report reads the domain with, so the asset behind a\n"
            "listing is read through GetListing or not at all, and a DENIED cell in section 4 is the\n"
            "permission ceiling rather than an empty policy. The Sandbox session is answered, as a\n"
            "contributor of both projects. A fulfilment lands where CT-7 and CT-10 look (measured\n"
            "2026-10-26, Stage 6f 11.9). A direct Share has never run here (6f 2.5): CT-11 fails on\n"
            "a subscription with no accepted request and on one requested by a member of the owning\n"
            "project, so either record a Share leaves is a failure."
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

        rep.h1("10. Calls that failed")
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
