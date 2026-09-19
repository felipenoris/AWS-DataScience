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
#             ListProjectMemberships, SearchListings, GetListing, ListDataSources, GetDataSource,
#             ListSubscriptions, ListSubscriptionRequests, ListSubscriptionGrants,
#             ListPolicyGrants, ListLineageEvents, lakeformation:ListPermissions, ListLFTags,
#             glue:GetDatabases; in Sandbox - lakeformation:ListPermissions, ListLFTags,
#             glue:GetDatabases; and sts:GetCallerIdentity. Every one is a read.
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# THE TWO ROADS AN ACCESS ACT CAN TAKE, which is what this script exists to keep apart. On the
# catalog road a subscription or a direct Share is approved in the portal and DataZone writes a Lake
# Formation grant in the account that owns the table (INT-23). On the register road a grant is
# written by Terraform and carries a row in docs/AWS_STATE.md's grant register. A grant on the first
# road with no row on the second is invisible to every review this estate performs, so section 5
# reads both and CT-7 is the comparison.
#
# The checks:
#   CT-1  one domain, AVAILABLE, in the registry account - and no domain in the consumer account
#         (D26: the registry and the runtimes are different accounts).
#   CT-2  every listing names an owning project that exists, and its type is reported.
#   CT-3  the access acts: subscriptions, requests and grants per listing. Zero is the reading
#         today; when one exists, CT-7 is what says whether it is registered.
#   CT-4  no data source publishes on import. A publish that happens at import time is a listing
#         nobody reviewed, and publishOnImport is the only switch that does it.
#   CT-5  the data sources that generate business names with AI, reported with their schedule.
#         A note until Stage 6f decision 3 settles it (Lesson 50: a check written to a stage's
#         final expectation is red on every pass until that stage ends).
#   CT-6  every scheduled data source run is one somebody chose. A blueprint-created data source
#         on a cron nobody wrote is Lesson 17's shape and is named here rather than discovered.
#   CT-7  no SMUS-managed principal holds a grant on a lake database, a lake table or an LF-Tag.
#         The design reads the lake through TBAC re-grants to a persona (GOVERNANCE.md §Grants),
#         so a project role or a conditioned IAMPrincipals entry reaching `raw`, `curated` or
#         `dropbox` is a second road into governed data with no row in the register.
#   CT-8  every conditioned IAMPrincipals grant carries the project condition. An unconditioned
#         one grants the whole account, which is what that principal means without a Condition.
#   CT-9  nobody may override a project owner or a domain unit owner. The owner project's approval
#         is the control on the catalog road; an override grant removes it.
#
# What it cannot see (0.6, measured 2026-09-13): DataZone refuses GetAsset and GetDataProduct to
# InfrastructureAccess, so the asset behind a listing is read through GetListing or not at all.
# ListPolicyGrants is refused for two policy types on the same ceiling; those cells read DENIED
# rather than empty, because an empty listing and a refused read are different facts.

from __future__ import annotations

import json
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

# What makes a principal SMUS-managed. The service names its own roles by prefix and writes the
# account-wide entry as `<account>:IAMPrincipals`, which is a grant to everyone in the account
# unless a Condition narrows it (CT-8).
SMUS_ROLE_MARKERS = (
    "datazone_usr_role_",
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
    return (kind, "-")


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
            sources.append(
                (
                    pname,
                    body.get("name", "-"),
                    body.get("type", "-"),
                    bool(body.get("publishOnImport")),
                    bool((body.get("recommendation") or {}).get("enableBusinessNameGeneration")),
                    (body.get("schedule") or {}).get("schedule", "-"),
                    body.get("status", "-"),
                    body.get("lastRunAssetCount", "-"),
                )
            )

    # ---------------------------------------------------------------- CT-4 publish on import
    publishing = [n for _, n, _, poi, _, _, _, _ in sources if poi]
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
    ai_on = [n for _, n, _, _, ai, _, _, _ in sources if ai]
    checks.note(
        "CT-5",
        "the data sources that generate business names with AI",
        f"{', '.join(ai_on) if ai_on else 'none'} - Stage 6f decision 3 decides whether this stays on",
    )

    # ---------------------------------------------------------------- CT-6 the schedules
    scheduled = [(n, s) for _, n, _, _, _, s, _, _ in sources if s != "-"]
    if not scheduled:
        checks.ok(
            "CT-6", "every scheduled run is one somebody chose", "no data source is scheduled"
        )
    else:
        checks.note(
            "CT-6",
            "every scheduled run is one somebody chose",
            "; ".join(f"{n} on {s}" for n, s in scheduled)
            + " - a blueprint-created source arrives with a cron nobody wrote (Lesson 17)",
        )

    # ---------------------------------------------------------------- the grants, both accounts
    grant_rows: list = []
    for label, cli, profile in (
        ("registry", dat, DATA_PROFILE),
        ("consumer", sbx, SANDBOX_PROFILE),
    ):
        if not live[profile].live:
            continue
        res = cli.run("lakeformation", "list-permissions", "--output", "json")
        for row in (json_or_none(res.stdout) or {}).get("PrincipalResourcePermissions", []):
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

    # ---------------------------------------------------------------- CT-7 SMUS reaching the lake
    reaching = [g for g in smus_grants if touches_lake(g[2], g[3])]
    if not grant_rows:
        checks.note("CT-7", "no SMUS principal reaches the governed lake", "no grant read")
    elif reaching:
        checks.fail(
            "CT-7",
            "no SMUS principal reaches the governed lake",
            "; ".join(f"{short_principal(g[1])} on {g[2]} {g[3]}" for g in reaching)
            + " - a second road into governed data, with no row in AWS_STATE.md's register",
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
    if not iam_principals:
        checks.note("CT-8", "every IAMPrincipals grant is project-conditioned", "none exists")
    elif account_wide:
        checks.fail(
            "CT-8",
            "every IAMPrincipals grant is project-conditioned",
            "; ".join(f"{g[2]} {g[3]}" for g in account_wide)
            + " - without the condition this grants every principal in the account",
        )
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
            "sections 1 to 4 are the catalog (DataZone), section 5 is Lake Formation, and CT-7 is\n"
            "the question of whether one has reached into the other."
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
                ["PROJECT\tSOURCE\tTYPE\tPUBLISH ON IMPORT\tAI NAMES\tSCHEDULE\tSTATUS\tASSETS"]
                + [
                    f"{p}\t{n}\t{t}\t{'YES' if poi else 'no'}\t{'yes' if ai else 'no'}\t{s}\t{st}\t{a}"
                    for p, n, t, poi, ai, s, st, a in sources
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

        rep.h1("6. The LF-Tag ontology, by account")
        if not tag_rows:
            rep.text("No LF-Tag is defined in either account.")
        else:
            rep.tabulate(["WHERE\tKEY\tVALUES"] + [f"{w}\t{k}\t{v}" for w, k, v in tag_rows])

        rep.h1("7. Checks")
        rep.checks_table(checks)

        rep.h1("8. What this report cannot see")
        rep.text(
            "DataZone refuses GetAsset and GetDataProduct to InfrastructureAccess (Stage 6f 0.6), so\n"
            "the asset behind a listing is read through GetListing or not at all, and a DENIED cell in\n"
            "section 4 is the permission ceiling rather than an empty policy. Whether a fulfilment\n"
            "grant would land where CT-7 looks is unmeasured until one is made: no subscription or\n"
            "Share has ever run here."
        )

        rep.h1("9. Calls that failed")
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
