#!/usr/bin/env -S uv run --quiet
# warehouse.py - the Redshift Serverless warehouse, its cost ceiling and its grants.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/warehouse.py                        # every profiled account
#             ./aws/warehouse.py awsds-infra-sandbox-1  # one of them
#   writes:   aws/output/warehouse.txt   (untracked - see .gitignore)
#   reads:    redshift-serverless Get*/List*, logs:DescribeLogGroups, cloudwatch
#             DescribeAlarms + GetMetricStatistics, iam Get*/List*, secretsmanager
#             DescribeSecret, datazone ListConnections + GetConnection + ListJobRuns - all
#             reads. It also runs SELECT statements through redshift-data (see "the one call
#             that is not a describe").
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS FILE EXISTS. The warehouse is the most expensive object per unit of time in this estate
# - 1.44 USD for every hour a query runs at 4 base RPUs (docs/PRICING.md 5) - and three of the
# things that bound it are not visible in any single console page:
#
#   - THE USAGE LIMIT'S ACTION. `breach_action` defaults to `log`, which refuses nothing. A limit
#     whose action was left alone reads exactly like a ceiling and is not one. WH-3.
#   - THE RATCHET. AWS: "Once you scale your data warehouse beyond 4 RPUs ... Amazon Redshift
#     won't scale your data warehouse back down to 4 RPUs." No IAM condition key exists for base
#     capacity, so nothing PREVENTS it; WH-1 and the ComputeCapacity alarm are the detection.
#   - THE GRANTS. A Redshift GRANT is a fourth permission system with no LF-Tag, no
#     GetDataAccess and no list-permissions API. It is readable only from a database session,
#     which is why this script has one.
#
# THE ONE CALL THAT IS NOT A DESCRIBE. WH-6 and WH-12..WH-14 need SQL, so this script runs
# `redshift-data execute-statement` with the namespace's admin secret. Every statement it sends is
# a SELECT against a catalog view; it creates nothing and changes nothing. Two things follow:
#
#   - `redshift-data:ExecuteStatement` is a write-shaped API and `secretsmanager:GetSecretValue`
#     reads a credential, so this half runs only with --sql (off by default). Without it the
#     database checks report `note` rather than passing on no evidence.
#   - THE DATA API NEEDS NO NETWORK PATH. Measured 2026-09-20 from a laptop outside every VPC: it
#     reaches the database with an IAM identity and the secret alone. That is convenient here and
#     it is also why identity/sso denies the whole redshift-data family to DataScientistAccess -
#     a persona holding ExecuteStatement has a query path from anywhere.
#
# WHAT IT CANNOT SEE. Whether a SageMaker project can actually reach the warehouse: that is an
# intersection of three layers in three systems (Lesson 28) and only a connection answers it.

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "warehouse.txt"

# The name both objects carry, per account. A namespace and a workgroup may share a name and here
# they do: one name for one warehouse is what makes a rename fail in a check rather than in Stage
# 6h. The three audit log-group paths are DERIVED from the namespace name by the service, which is
# why the name is a contract rather than a label.
NAME_TMPL = "awsds-{env}-warehouse"
LOG_TYPES = ("userlog", "connectionlog", "useractivitylog")

# D40's two classes, by account. A Redshift `database` is the CLASS CONTAINER and a Redshift
# `schema` is what objectives.md calls a base - whose name is THEMATIC and therefore carries no
# authorization information at all (Stage 5b 2.1). So WH-6 cannot classify by name: what it can
# read is that each account holds its expected class container and not the other one.
CLASS_DB = {"sandbox": "sandbox", "prod": "governed"}

# The namespace's own first database, which Redshift creates whether one is wanted or not, plus
# `dev`, which it creates ANYWAY - naming db_name does not replace `dev`, it adds a database
# beside it (measured 2026-09-20). Both are inert: PUBLIC holds USAGE and no CREATE on their
# `public` schema (read 2026-09-21), so no REVOKE ran in either.
INERT_DBS = ("warehouse", "dev")

# Where the authored map lives, read rather than carried: a script with its own copy of "which
# projects are admitted" is one more consumer of a list that already has three (Lesson 33).
PROJECTS_VARS = "terraform-live/sandbox/warehouse/variables.tf"

# The wide tag AWS offers and this design refuses. `AmazonDataZoneProject` names ONE project;
# this names every project in the account, which is an empty deny-list permitting everything.
WIDE_TAG = "for-use-with-all-datazone-projects"

DEFAULT_PROFILES = ("awsds-infra-sandbox-1", "awsds-infra-prod")

# One entry of the `projects` map. The key's quotes are OPTIONAL: an identifier-shaped map key is
# written bare in HCL and `terraform fmt` leaves either spelling alone, so requiring them read an
# authored map of one project as `none` (2026-09-21).
PROJECTS_VAR_RE = re.compile(r'variable\s+"projects"\s*\{')
PROJECTS_DEFAULT_RE = re.compile(r"\n\s*default\s*=\s*\{")
ENTRY_RE = re.compile(r'"?(?P<id>[a-z0-9]+)"?\s*=\s*\{(?P<body>[^}]*)\}', re.S)

# The SMUS domain the admitted projects belong to, from the same file: WH-9 lists each project's
# connections in it.
DOMAIN_VAR_RE = re.compile(r'variable\s+"datazone_domain_id"\s*\{')
DOMAIN_DEFAULT_RE = re.compile(r'\n\s*default\s*=\s*"(dzd-[a-z0-9]+)"')

# A lineage job run in one of these states completed or is running, so the connection's scheduled
# sync is querying the warehouse on its meter (6h decision 3). A failed run is read in CloudTrail,
# not here: whether it minted a database session is `GetCredentials` by the access role.
LINEAGE_RAN = ("IN_PROGRESS", "SUCCESS", "PARTIALLY_SUCCEEDED")


def authored_projects(path: Path) -> dict | None:
    """The projects map as the slice declares it, or None when the file cannot be read.

    The map's extent is found by matching its braces rather than by a regex ending on an
    indented `}`: the variable's validation blocks sit below the default and contain text that a
    loose terminator lets ENTRY_RE read entries out of - it invented a project called `roject`,
    from the middle of `AmazonDataZoneProject`, on the first real map this parser ever saw.
    """
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    var = PROJECTS_VAR_RE.search(text)
    if not var:
        return None
    default = PROJECTS_DEFAULT_RE.search(text, var.end())
    if not default:
        return None
    depth, close = 0, None
    for i in range(text.index("{", default.start()), len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close is None:
        return None
    body = text[text.index("{", default.start()) + 1 : close]
    out = {}
    for m in ENTRY_RE.finditer(body):
        fields = dict(re.findall(r'(\w+)\s*=\s*"([^"]+)"', m.group("body")))
        out[m.group("id")] = fields
    return out


def authored_domain(path: Path) -> str | None:
    """The `datazone_domain_id` variable's default, or None when the file does not carry one."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    var = DOMAIN_VAR_RE.search(text)
    if not var:
        return None
    default = DOMAIN_DEFAULT_RE.search(text, var.end())
    return default.group(1) if default else None


def env_of(profile: str) -> str:
    """The <env> name token a profile's account uses, from the profile name."""
    if "sandbox" in profile:
        return "sandbox"
    if "prod" in profile:
        return "prod"
    if "staging" in profile:
        return "staging"
    if "-data" in profile:
        return "data"
    return "org"


class Sql:
    """A database session over the Data API. Every statement it sends is a SELECT."""

    def __init__(self, cli: AwsCli, workgroup: str, secret_arn: str):
        self.cli = cli
        self.workgroup = workgroup
        self.secret_arn = secret_arn

    def rows(self, sql: str, database: str) -> list | None:
        """The result rows, or None when the statement did not finish. Never raises."""
        res = self.cli.run(
            "redshift-data",
            "execute-statement",
            "--workgroup-name",
            self.workgroup,
            "--database",
            database,
            "--secret-arn",
            self.secret_arn,
            "--sql",
            sql,
            "--query",
            "Id",
            "--output",
            "text",
            tolerate="",
            log=False,
        )
        if not res.ok:
            return None
        statement_id = res.text.strip()
        # The Data API is ASYNCHRONOUS and the CLI has no waiter for it, so the poll is here.
        # The one-second sleep is load-bearing rather than polite: the first version of this loop
        # had none, span 60 describes in well under a second while the statement was still
        # `STARTED`, and reported "the Data API returned nothing" for a warehouse that was
        # answering perfectly (2026-09-20). A statement that never finishes returns None rather
        # than blocking a report.
        for _ in range(60):
            res = self.cli.run(
                "redshift-data",
                "describe-statement",
                "--id",
                statement_id,
                "--query",
                "Status",
                "--output",
                "text",
                tolerate="",
                log=False,
            )
            if not res.ok:
                return None
            if res.text.strip() in ("FINISHED", "FAILED", "ABORTED"):
                break
            time.sleep(1)
        if res.text.strip() != "FINISHED":
            return None
        res = self.cli.run(
            "redshift-data",
            "get-statement-result",
            "--id",
            statement_id,
            "--output",
            "json",
            tolerate="",
            log=False,
        )
        if not res.ok:
            return None
        try:
            payload = json.loads(res.stdout)
        except json.JSONDecodeError:
            return None
        return [
            [None if f.get("isNull") else next(iter(f.values())) for f in record]
            for record in payload.get("Records", [])
        ]


def read_connections(cli: AwsCli, domain: str | None, authored: dict | None) -> dict:
    """Each admitted project's Redshift connections as the portal wrote them, keyed by project.

    A value is a list of connections, `refused` when DataZone's own authorization layer turns this
    identity away (it does so for a non-member of the project: `EXC-17`), `no domain` when the slice
    names none, or None when a call failed for another reason and is in the failed calls.
    """
    out: dict = {}
    for pid in authored or {}:
        if not domain:
            out[pid] = "no domain"
            continue
        res = cli.run(
            "datazone",
            "list-connections",
            "--domain-identifier",
            domain,
            "--project-identifier",
            pid,
            "--type",
            "REDSHIFT",
            "--query",
            "items[].connectionId",
            "--output",
            "text",
            tolerate="not permitted|AccessDenied",
        )
        if res.tolerated:
            out[pid] = "refused"
            continue
        if not res.ok:
            out[pid] = None
            continue
        found = []
        for cid in res.text.split():
            got = cli.run(
                "datazone",
                "get-connection",
                "--domain-identifier",
                domain,
                "--identifier",
                cid,
                "--output",
                "json",
            )
            if not got.ok:
                continue
            conn = json.loads(got.stdout)
            props = (conn.get("props") or {}).get("redshiftProperties") or {}
            endpoint = (conn.get("physicalEndpoints") or [{}])[0]
            lineage = props.get("lineageSync") or {}
            runs: list | None = []
            if lineage.get("enabled") and lineage.get("lineageJobId"):
                jr = cli.run(
                    "datazone",
                    "list-job-runs",
                    "--domain-identifier",
                    domain,
                    "--job-identifier",
                    lineage["lineageJobId"],
                    "--query",
                    "items[].status",
                    "--output",
                    "text",
                )
                runs = jr.text.split() if jr.ok else None
            found.append(
                {
                    "name": conn.get("name"),
                    "workgroup": (props.get("storage") or {}).get("workgroupName"),
                    "database": props.get("databaseName"),
                    "access_role": (
                        (endpoint.get("awsLocation") or {}).get("accessRole") or ""
                    ).rsplit("/", 1)[-1],
                    "host": endpoint.get("host") or "",
                    "lineage": bool(lineage.get("enabled")),
                    "schedule": (lineage.get("schedule") or {}).get("schedule"),
                    "runs": runs,
                }
            )
        out[pid] = found
    return out


def read_account(
    cli: AwsCli, env: str, want_sql: bool, authored: dict | None, domain: str | None
) -> dict:
    """Every reading for one account, as data. No checks are decided here."""
    name = NAME_TMPL.format(env=env)
    facts: dict = {"env": env, "name": name}
    # The lifecycle target that destroys this account's compute, the one guard that is not a setting
    # (WH-15): the env token names the account folder except in Production (Stage 9 step 9.8).
    facts["make_env"] = {"prod": "production"}.get(env, env)

    res = cli.run(
        "redshift-serverless",
        "list-namespaces",
        "--query",
        "namespaces[].namespaceName",
        "--output",
        "text",
    )
    facts["namespaces"] = sorted(res.text.split()) if res.ok and res.text.strip() else []

    res = cli.run(
        "redshift-serverless",
        "list-workgroups",
        "--query",
        "workgroups[].workgroupName",
        "--output",
        "text",
    )
    facts["workgroups"] = sorted(res.text.split()) if res.ok and res.text.strip() else []

    if name in facts["namespaces"]:
        res = cli.run(
            "redshift-serverless", "get-namespace", "--namespace-name", name, "--output", "json"
        )
        if res.ok:
            facts["namespace"] = json.loads(res.stdout)["namespace"]
        res = cli.run(
            "redshift-serverless",
            "list-tags-for-resource",
            "--resource-arn",
            facts.get("namespace", {}).get("namespaceArn", "x"),
            "--output",
            "json",
            tolerate="",
        )
        if res.ok:
            facts["namespace_tags"] = {
                t["key"]: t["value"] for t in json.loads(res.stdout).get("tags", [])
            }

    if name in facts["workgroups"]:
        res = cli.run(
            "redshift-serverless", "get-workgroup", "--workgroup-name", name, "--output", "json"
        )
        if res.ok:
            facts["workgroup"] = json.loads(res.stdout)["workgroup"]
            arn = facts["workgroup"]["workgroupArn"]
            res = cli.run(
                "redshift-serverless",
                "list-usage-limits",
                "--resource-arn",
                arn,
                "--output",
                "json",
            )
            if res.ok:
                facts["usage_limits"] = json.loads(res.stdout).get("usageLimits", [])
            res = cli.run(
                "redshift-serverless",
                "list-tags-for-resource",
                "--resource-arn",
                arn,
                "--output",
                "json",
                tolerate="",
            )
            if res.ok:
                facts["workgroup_tags"] = {
                    t["key"]: t["value"] for t in json.loads(res.stdout).get("tags", [])
                }

    res = cli.run(
        "logs",
        "describe-log-groups",
        "--log-group-name-prefix",
        f"/aws/redshift/{name}",
        "--output",
        "json",
    )
    if res.ok:
        facts["log_groups"] = {
            g["logGroupName"]: g.get("retentionInDays") for g in json.loads(res.stdout)["logGroups"]
        }

    # THE NAMESPACE ROLE is read only where the namespace exists: an account without one has no
    # role either (Production's is Stage 9 step 9.2's), and WH-1b reads that as a note. Where the
    # namespace exists, `NoSuchEntity` becomes `exec_role: missing`, which WH-1b fails: a missing
    # role and a role holding no policy both answer two empty lists (Lesson 13). `None` means a
    # read failed for another reason and is in the failed calls.
    facts["exec_role"], facts["exec_attached"], facts["exec_inline"] = None, [], []
    if name in facts["namespaces"]:
        attached = cli.run(
            "iam",
            "list-attached-role-policies",
            "--role-name",
            f"{name}-exec",
            "--query",
            "AttachedPolicies[].PolicyName",
            "--output",
            "text",
            tolerate="NoSuchEntity",
        )
        inline = cli.run(
            "iam",
            "list-role-policies",
            "--role-name",
            f"{name}-exec",
            "--query",
            "PolicyNames",
            "--output",
            "text",
            tolerate="NoSuchEntity",
        )
        if attached.tolerated or inline.tolerated:
            facts["exec_role"] = "missing"
        elif attached.ok and inline.ok:
            facts["exec_role"] = "found"
            facts["exec_attached"] = attached.text.split()
            facts["exec_inline"] = inline.text.split()

    # LAYER 2, ONE ROLE PER ADMITTED PROJECT. The role is SMUS's, not this repository's, so all
    # three readings can fail independently: the project can be deleted, the boundary can be
    # detached by whoever recreates the role, and the attachment can be lost without the tag
    # moving. `NoSuchEntity` is tolerated so a deleted project reads as `found: False` rather
    # than as a broken run.
    facts["project_roles"] = {}
    for pid, entry in (authored if env == "sandbox" else {}).items():
        role = entry.get("role_name")
        if not role:
            continue
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            role,
            "--query",
            "Role.PermissionsBoundary.PermissionsBoundaryArn",
            "--output",
            "text",
            tolerate="NoSuchEntity",
        )
        found = res.ok and not res.tolerated
        boundary = res.text.strip() if found and res.text.strip() != "None" else None
        res = cli.run(
            "iam",
            "list-attached-role-policies",
            "--role-name",
            role,
            "--query",
            "AttachedPolicies[].PolicyName",
            "--output",
            "text",
            tolerate="NoSuchEntity",
        )
        facts["project_roles"][pid] = {
            "role": role,
            "found": found,
            "boundary": boundary,
            "attached": res.text.split() if res.ok and res.text.strip() else [],
        }

    # THE CONNECTION, 6h 3.2's object. It needs no workgroup: it is DataZone metadata, readable
    # while the [E] compute is down.
    facts["connections"] = read_connections(cli, domain, authored if env == "sandbox" else {})

    res = cli.run(
        "cloudwatch",
        "describe-alarms",
        "--alarm-name-prefix",
        name,
        "--query",
        "MetricAlarms[].[AlarmName,MetricName,Threshold,StateValue]",
        "--output",
        "text",
    )
    facts["alarms"] = [line.split("\t") for line in res.text.splitlines()] if res.ok else []

    # The burn. `ComputeSeconds` is "Accumulated compute-unit seconds used in the last 30
    # minutes", so this is what the warehouse has actually charged for rather than what it might.
    res = cli.run(
        "cloudwatch",
        "get-metric-statistics",
        "--namespace",
        "AWS/Redshift-Serverless",
        "--metric-name",
        "ComputeSeconds",
        "--dimensions",
        f"Name=Workgroup,Value={name}",
        "--start-time",
        context.utc_stamp()[:11] + "00:00:00Z",
        "--end-time",
        context.utc_stamp(),
        "--period",
        "1800",
        "--statistics",
        "Sum",
        "--query",
        "Datapoints[].[Timestamp,Sum]",
        "--output",
        "text",
        tolerate="",
    )
    # THE SERIES, NOT THE DAY'S SUM, and the reason is a mistake this file's own stage made three
    # times: a `Sum` over a 24-hour window answers a question about the window, and reading it as
    # "what is happening now" is how a query that ran for 6 h 33 min went unnoticed while the same
    # metric was being quoted. `ComputeSeconds` publishes per 30-minute interval, so the series shows
    # both the day's total and whether the meter is still turning.
    series = []
    if res.ok and res.text.strip():
        for line in res.text.splitlines():
            parts = line.split()
            if len(parts) == 2:
                series.append((parts[0], float(parts[1])))
    series.sort()
    facts["compute_series"] = series
    facts["compute_seconds_today"] = sum(v for _t, v in series)
    # The most recent published interval, as a rate. 7,200 RPU-seconds in a 1,800-second interval is
    # 4 RPU sustained - a workgroup that is never going idle, which is what a runaway looks like.
    facts["compute_last_interval"] = series[-1] if series else None

    if want_sql and "workgroup" in facts and "namespace" in facts:
        secret = facts["namespace"].get("adminPasswordSecretArn")
        if secret:
            sql = Sql(cli, name, secret)
            probe_db = CLASS_DB.get(env, "dev")
            facts["databases"] = sql.rows(
                "select database_name, database_type, nvl(database_acl, '(none)') "
                "from svv_redshift_databases order by database_name",
                probe_db,
            )
            facts["schemas"] = sql.rows(
                "select schema_name, schema_owner, nvl(schema_acl, '(none)') "
                "from svv_redshift_schemas "
                f"where database_name = '{probe_db}' "
                "and schema_name not in ('pg_catalog','information_schema') "
                "order by schema_name",
                probe_db,
            )
            facts["role_grants"] = sql.rows(
                "select role_name, granted_role_name from svv_role_grants order by 1,2",
                probe_db,
            )
            facts["user_grants"] = sql.rows(
                "select user_name, role_name from svv_user_grants order by 1,2",
                probe_db,
            )
            facts["users"] = sql.rows(
                "select usename, usesuper from pg_user order by usename",
                probe_db,
            )

            # WH-14's three readings. A themed schema is SHARED by design, and sharing survives
            # only if the theme role can read what another project's user wrote: ownership is
            # singular, and `USAGE, CREATE ON SCHEMA` does not carry SELECT on somebody else's
            # table. `pg_default_acl` is EMPTY on this platform - the default privileges live in
            # `svv_default_privileges` and nowhere else (measured 2026-10-10).
            facts["relations"] = sql.rows(
                "select n.nspname, c.relname, trim(u.usename) "
                "from pg_class c "
                "join pg_namespace n on n.oid = c.relnamespace "
                "join pg_user u on u.usesysid = c.relowner "
                "where n.nspname not in ('pg_catalog','information_schema','public') "
                "and n.nspname not like 'pg_%' and c.relkind in ('r','v') "
                "order by 1,2",
                probe_db,
            )
            facts["relation_role_reads"] = sql.rows(
                "select namespace_name, relation_name, identity_name "
                "from svv_relation_privileges "
                "where identity_type = 'role' and privilege_type = 'SELECT' order by 1,2,3",
                probe_db,
            )
            facts["default_privs"] = sql.rows(
                "select schema_name, owner_name, grantee_name, privilege_type "
                "from svv_default_privileges where grantee_type = 'role' order by 1,2,3",
                probe_db,
            )
    return facts


def judge(checks: Checks, facts: dict, authored: dict | None, want_sql: bool) -> None:
    """Every check for one account. Each one reads differently when broken (Lesson 13)."""
    env, name = facts["env"], facts["name"]
    tag = f"[{env}]"
    wg = facts.get("workgroup")
    ns = facts.get("namespace")

    # ---------------------------------------------------------------- WH-8, first: the inventory
    extra_ns = [n for n in facts["namespaces"] if n != name]
    extra_wg = [w for w in facts["workgroups"] if w != name]
    if extra_ns or extra_wg:
        checks.fail(
            "WH-8",
            f"{tag} only the authored warehouse exists",
            f"unexpected namespace(s) {extra_ns or '-'}, workgroup(s) {extra_wg or '-'} - "
            "a warehouse this repository did not build has none of its controls",
        )
    else:
        checks.ok(
            "WH-8",
            f"{tag} only the authored warehouse exists",
            f"{len(facts['namespaces'])} namespace(s), {len(facts['workgroups'])} "
            "workgroup(s), all expected",
        )

    # THE COMPUTE SLICE IS [E], so its absence is the normal state between sessions and must not
    # read as a fault (Lesson 50). Everything that needs a workgroup becomes a note.
    if wg is None:
        checks.note(
            "WH-1",
            f"{tag} the workgroup's shape",
            "no workgroup - the compute slice is [E] and `make down` destroys it. "
            "Redshift Serverless has no pause, so this IS the powered-off state",
        )
        checks.note("WH-2", f"{tag} the four config parameters", "no workgroup")
        checks.note("WH-3", f"{tag} the usage limit refuses at the ceiling", "no workgroup")
    else:
        problems = []
        if wg.get("baseCapacity") != 4:
            problems.append(
                f"baseCapacity={wg.get('baseCapacity')} (D40 fixes it at 4, and the "
                "ratchet means it does not come back down)"
            )
        if not wg.get("maxCapacity"):
            problems.append("maxCapacity unset - the service chooses the ceiling")
        if wg.get("publiclyAccessible"):
            problems.append("publiclyAccessible")
        if wg.get("enhancedVpcRouting"):
            problems.append(
                "enhancedVpcRouting on - it is off by design, which is what makes two "
                "subnets sufficient"
            )
        subnets = wg.get("subnetIds") or []
        if len(subnets) < 2:
            problems.append(f"{len(subnets)} subnet(s) - two AZs are the service's minimum")
        if problems:
            checks.fail("WH-1", f"{tag} the workgroup's shape", "; ".join(problems))
        else:
            checks.ok(
                "WH-1",
                f"{tag} the workgroup's shape",
                f"base {wg['baseCapacity']} / max {wg['maxCapacity']} RPU, private, "
                f"no EVR, {len(subnets)} subnets",
            )

        params = {p["parameterKey"]: p["parameterValue"] for p in wg.get("configParameters", [])}
        ppt = (wg.get("pricePerformanceTarget") or {}).get("status")
        bad = []
        if params.get("require_ssl") != "true":
            bad.append(f"require_ssl={params.get('require_ssl')}")
        if params.get("enable_user_activity_logging") != "true":
            bad.append(
                "enable_user_activity_logging off - useractivitylog then carries no SQL "
                "text, which is the half Stage 11 wants"
            )
        if not params.get("max_query_execution_time"):
            bad.append(
                "max_query_execution_time unset - a query then gets the service maximum of "
                "86,399 s, a 24-hour runaway at 1.44 USD/h"
            )
        # AWS: the price-performance target "is enabled by default ... and is set to Balanced", and
        # "We do not recommend using this feature for 4 Base RPU". So ENABLED at this capacity is a
        # finding, not a blank, and DISABLED reports no `level` at all.
        if ppt != "DISABLED":
            bad.append(
                f"pricePerformanceTarget={ppt} - AI-driven scaling is not recommended at 4 "
                "base RPUs and its default is ENABLED at Balanced"
            )
        if bad:
            checks.fail("WH-2", f"{tag} the four config parameters", "; ".join(bad))
        else:
            checks.ok(
                "WH-2",
                f"{tag} the four config parameters",
                f"ssl on, activity logging on, max_query {params['max_query_execution_time']}s, "
                "price-performance target DISABLED",
            )

        limits = facts.get("usage_limits", [])
        compute = [u for u in limits if u.get("usageType") == "serverless-compute"]
        if not compute:
            checks.fail(
                "WH-3",
                f"{tag} the usage limit refuses at the ceiling",
                "no serverless-compute usage limit - the compute has no ceiling the "
                "service enforces, and a budget notification arrives after the money",
            )
        elif len(compute) > 1:
            checks.fail(
                "WH-3",
                f"{tag} the usage limit refuses at the ceiling",
                f"{len(compute)} limits - the loosest one wins, so a second is a hole",
            )
        elif compute[0].get("breachAction") != "deactivate":
            checks.fail(
                "WH-3",
                f"{tag} the usage limit refuses at the ceiling",
                f"breachAction={compute[0].get('breachAction')} - the API's default is "
                "`log`, which refuses nothing and reads exactly like a ceiling",
            )
        else:
            checks.ok(
                "WH-3",
                f"{tag} the usage limit refuses at the ceiling",
                f"{compute[0]['amount']} RPU-hours {compute[0]['period']}, deactivate",
            )

    # ---------------------------------------------- WH-15: is the meter turning, and should it be?
    #
    # THIS IS A CHECK AND NOT ONLY A REPORT LINE, because on 2026-09-20 the burn was in the body of
    # this file's own report and nobody read it while a query ran for 6 h 33 min at base capacity. The
    # checks table is what gets scanned; a verdict that is not in it is a verdict nobody sees.
    #
    # It FAILS at or above 3.5 RPU sustained over a whole published interval, and that threshold is a
    # judgement worth stating. A legitimately busy warehouse is not a defect - but this one carries
    # `max_query_execution_time = 120`, so no single query is supposed to span a 30-minute interval at
    # all, and the estate's use is interactive rather than batch. A whole interval pinned at base
    # capacity therefore means either a query nobody is watching or a ceiling that is not enforced, and
    # both want somebody to look. The message says the legitimate case out loud so the failure does not
    # train its reader to ignore it (Lesson 50).
    last = facts.get("compute_last_interval")
    if wg is None:
        checks.note(
            "WH-15",
            f"{tag} the meter is not turning unexpectedly",
            "no workgroup - nothing can be running, and no compute can be billed",
        )
    elif last is None:
        checks.note(
            "WH-15",
            f"{tag} the meter is not turning unexpectedly",
            "ComputeSeconds has published no interval yet. It lands per 30 minutes, so a workgroup "
            "raised in the last half hour reads like this and it is not evidence of anything",
        )
    else:
        stamp, value = last
        rate = value / 1800.0
        if rate >= 3.5:
            checks.fail(
                "WH-15",
                f"{tag} the meter is not turning unexpectedly",
                f"{rate:.2f} RPU sustained through the interval ending {stamp} = "
                f"{rate * 0.36:.2f} USD/h while it lasts. At or above base capacity for a whole "
                "interval: either a query nobody is watching, or max_query_execution_time is not "
                "enforced. Read `select query_id, status, elapsed_time/1000000.0 from "
                "sys_query_history where status = 'running'`; end one with "
                "pg_terminate_backend(<session_id>), or destroy the compute with `make down "
                f"ENV={facts['make_env']}`, which is the only guard that is not a setting. If the work is "
                "legitimate, this row is the receipt for it rather than a fault",
            )
        elif rate >= 0.1:
            checks.note(
                "WH-15",
                f"{tag} the meter is not turning unexpectedly",
                f"{rate:.2f} RPU sustained ending {stamp} = {rate * 0.36:.2f} USD/h - something is "
                "running, below base capacity",
            )
        else:
            checks.ok(
                "WH-15",
                f"{tag} the meter is not turning unexpectedly",
                f"idle: {value:.0f} RPU-seconds in the interval ending {stamp}. An idle workgroup "
                "bills NOTHING for compute, which is the claim D40 rests on and is measured here "
                "rather than quoted",
            )

    # ------------------------------------------------------------------- WH-4: the audit trail
    groups = facts.get("log_groups", {})
    want = {f"/aws/redshift/{name}/{t}" for t in LOG_TYPES}
    missing = sorted(want - set(groups))
    never = sorted(g for g, r in groups.items() if r is None)
    if ns is None and not groups:
        checks.note("WH-4", f"{tag} the audit groups expire", "no namespace in this account")
    elif missing or never:
        checks.fail(
            "WH-4",
            f"{tag} the audit groups expire",
            f"missing {missing or '-'}; NEVER EXPIRE {never or '-'} - Redshift creates a "
            "group it finds absent at Never Expire, and this estate keeps exactly one "
            "such group as a dated exception (AWS_STATE.md EXC-10)",
        )
    else:
        checks.ok(
            "WH-4",
            f"{tag} the audit groups expire",
            ", ".join(f"{g.rsplit('/', 1)[1]}={r}d" for g, r in sorted(groups.items())),
        )

    # ----------------------------------------------------- WH-5: the credential is not anywhere
    if ns is None:
        checks.note(
            "WH-5",
            f"{tag} the admin credential is Secrets Manager's",
            "no namespace in this account",
        )
    elif not ns.get("adminPasswordSecretArn"):
        checks.fail(
            "WH-5",
            f"{tag} the admin credential is Secrets Manager's",
            "no adminPasswordSecretArn - the password is then a value somebody holds, and "
            "manage_admin_password = false puts it in the state file",
        )
    else:
        checks.ok(
            "WH-5",
            f"{tag} the admin credential is Secrets Manager's",
            "Redshift-managed; the secret's own key is the Secrets Manager one, because a "
            "CMK there buys only cross-account access (5b 1.8)",
        )

    # -------------------------------------------------- WH-7: the tag pair, and the wide form
    expected = set(authored) if authored is not None else None
    wg_tags = facts.get("workgroup_tags", {})
    ns_tags = facts.get("namespace_tags", {})
    wide = [o for o, t in (("workgroup", wg_tags), ("namespace", ns_tags)) if WIDE_TAG in t]
    if wide:
        checks.fail(
            "WH-7",
            f"{tag} the project tags match the authored map",
            f"{WIDE_TAG} on {', '.join(wide)} - that admits EVERY project in the account, "
            "which is per-account access wearing a per-project name",
        )
    elif expected is None:
        checks.note(
            "WH-7",
            f"{tag} the project tags match the authored map",
            f"{PROJECTS_VARS} could not be parsed - the authored side is unknown, so the "
            "live tags are reported rather than judged: "
            f"workgroup={wg_tags.get('AmazonDataZoneProject', '-')}, "
            f"namespace={ns_tags.get('AmazonDataZoneProject', '-')}",
        )
    elif env != "sandbox":
        # D26 keeps a deployment target out of the domain, so Production carries NO project tag.
        present = [
            o
            for o, t in (("workgroup", wg_tags), ("namespace", ns_tags))
            if "AmazonDataZoneProject" in t
        ]
        if present:
            checks.fail(
                "WH-7",
                f"{tag} the project tags match the authored map",
                f"AmazonDataZoneProject on {', '.join(present)} - a governed database gets "
                "no project connection (D26, 6h's opening paragraph)",
            )
        else:
            checks.ok(
                "WH-7",
                f"{tag} the project tags match the authored map",
                "no project tag, which is the governed class's correct state",
            )
    else:
        live = {t.get("AmazonDataZoneProject") for t in (wg_tags, ns_tags)} - {None}
        if wg is None and ns is None:
            checks.note(
                "WH-7", f"{tag} the project tags match the authored map", "neither object exists"
            )
        elif live != expected:
            checks.fail(
                "WH-7",
                f"{tag} the project tags match the authored map",
                f"authored {sorted(expected) or 'none'}, live {sorted(live) or 'none'} - "
                "the tag is on BOTH objects by AWS's requirement, so a difference is one "
                "of the two having drifted (Lesson 14)",
            )
        else:
            checks.ok(
                "WH-7",
                f"{tag} the project tags match the authored map",
                f"{sorted(live) or 'no project admitted'}, on both objects",
            )

    # ----------------------------------------- WH-11: layer 2 is attached, and still under D13
    #
    # Three things this cannot be folded into WH-7. The tag admits the project to the COMPUTE; this
    # policy is what lets the project role mint a database SESSION, and either can be present
    # without the other. And the boundary is the reason the policy is safe to attach at all: it is
    # the ceiling every interactive call in this account already sits under, so a role that has left
    # it is not a project role this estate governs - the policy would still read as attached.
    boundary_name = f"awsds-{env}-project-boundary"
    roles = facts.get("project_roles", {})
    if authored is None:
        checks.note(
            "WH-11",
            f"{tag} layer 2 is attached, inside the D13 boundary",
            f"{PROJECTS_VARS} could not be parsed, so there is no list of roles to read",
        )
    elif env != "sandbox":
        checks.note(
            "WH-11",
            f"{tag} layer 2 is attached, inside the D13 boundary",
            f"{PROJECTS_VARS} is Sandbox's map and this is {env}. D26 keeps a deployment target "
            "out of the domain, so no project is admitted to a warehouse outside Sandbox and "
            "layer 2 has nothing to attach here",
        )
    elif not roles:
        checks.note(
            "WH-11",
            f"{tag} layer 2 is attached, inside the D13 boundary",
            "no project admitted, so no policy is attached to any project role. Nothing is "
            "verified here: this reads the same whether layer 2 is correct or absent (Lesson 50)",
        )
    else:
        problems = []
        good = []
        for pid, r in sorted(roles.items()):
            want_policy = f"{name}-project-{pid}"
            if not r["found"]:
                problems.append(
                    f"{r['role']} does not exist - the project was deleted, and the "
                    f"tag `AmazonDataZoneProject={pid}` now admits nobody (runbook U)"
                )
                continue
            if want_policy not in r["attached"]:
                problems.append(
                    f"{r['role']} is missing {want_policy} - the tag admits the "
                    "project to the compute and nothing mints it a session"
                )
            if r["boundary"] is None:
                problems.append(f"{r['role']} carries NO permissions boundary")
            elif not r["boundary"].endswith(f"/{boundary_name}"):
                problems.append(
                    f"{r['role']} carries {r['boundary'].rsplit('/', 1)[-1]} rather "
                    f"than {boundary_name}"
                )
            if (
                want_policy in r["attached"]
                and r["boundary"]
                and r["boundary"].endswith(f"/{boundary_name}")
            ):
                good.append(pid)
        if problems:
            checks.fail(
                "WH-11",
                f"{tag} layer 2 is attached, inside the D13 boundary",
                "; ".join(problems),
            )
        else:
            checks.ok(
                "WH-11",
                f"{tag} layer 2 is attached, inside the D13 boundary",
                f"{good}: the warehouse policy is attached and the role is still under "
                f"{boundary_name}",
            )

    # ------------------------------------------ WH-9: the connection object as the portal wrote it
    #
    # DataZone's own authorization layer decides whether this identity may list a project's
    # connections, and no IAM policy reaches it. It refused three times while the identity was in no
    # project (2026-09-21, twice on 2026-10-10) and answers since 2026-10-15, when Sandbox's
    # InfrastructureAccess role was made contributor to both Sandbox projects as a group profile (6h
    # log, 2026-10-18). A refusal is therefore a note naming that cause, never a fail.
    #
    # What is compared: the workgroup and the host the connection names, and the access role, which
    # must be the one sandbox/warehouse/ authors for that project - any other role is a database
    # identity this repository did not write. `lineageSync` is the connection's scheduled query: the
    # portal shows no toggle and creates it ENABLED (read 2026-10-18), so it is read here rather than
    # assumed off. A run that completed fails the check; an enabled sync whose runs all failed is a
    # note, because it costs nothing until one succeeds (EXC-17).
    conns = (facts.get("connections") or {}) if env == "sandbox" else {}
    what9 = f"{tag} the connection object as the portal wrote it"
    if env != "sandbox":
        checks.note(
            "WH-9",
            what9,
            "no project is admitted to a warehouse outside Sandbox (D26), so no connection is expected",
        )
    elif not conns:
        checks.note("WH-9", what9, "no project is admitted, so there is no connection to read")
    else:
        problems, notes, good = [], [], []
        for pid, found in sorted(conns.items()):
            if found == "refused":
                notes.append(
                    f"{pid}: `list-connections` refused by DataZone's own authorization layer - this "
                    "identity is in no project, so the fields are a project member's reading (EXC-17)"
                )
            elif found == "no domain":
                notes.append(f"{pid}: {PROJECTS_VARS} names no `datazone_domain_id`")
            elif found is None:
                notes.append(f"{pid}: unread, a call failed (see the failed calls)")
            elif not found:
                notes.append(
                    f"{pid}: no Redshift connection - the portal half (6h 3.2) has not run, or the "
                    "connection was removed"
                )
            for c in found if isinstance(found, list) else []:
                role = f"{name}-access-{pid}"
                if c["workgroup"] != name or not c["host"].startswith(f"{name}."):
                    problems.append(f"{c['name']} names workgroup {c['workgroup']} at {c['host']}")
                if c["access_role"] != role:
                    problems.append(
                        f"{c['name']}'s access role is {c['access_role'] or 'none'}, not {role} - "
                        "a database identity this repository did not author"
                    )
                ran = [s for s in (c["runs"] or []) if s in LINEAGE_RAN]
                if c["lineage"] and ran:
                    problems.append(
                        f"{c['name']}'s lineageSync ran ({', '.join(sorted(set(ran)))}) on "
                        f"{c['schedule']} - a scheduled query on the warehouse's meter, which 6h "
                        "decision 3 keeps off"
                    )
                elif c["lineage"]:
                    runs = (
                        "runs unread"
                        if c["runs"] is None
                        else f"{len(c['runs'])} run(s), none completed"
                    )
                    notes.append(
                        f"{c['name']} (database {c['database']}): lineageSync ENABLED on "
                        f"{c['schedule']}, {runs} - off is 6h decision 3, and the portal shows no "
                        "toggle (EXC-17)"
                    )
                else:
                    good.append(f"{c['name']} (database {c['database']}, lineageSync off)")
        if problems:
            checks.fail("WH-9", what9, "; ".join(problems))
        elif notes:
            checks.note("WH-9", what9, "; ".join(notes + good))
        else:
            checks.ok(
                "WH-9",
                what9,
                "; ".join(good) + ": the authored workgroup and access role",
            )

    # ------------------------------------------- the namespace role reaches nothing (5b 2.4/D13)
    if ns is None:
        checks.note("WH-1b", f"{tag} the namespace role holds no policy", "no namespace")
    elif facts["exec_role"] == "missing":
        checks.fail(
            "WH-1b",
            f"{tag} the namespace role holds no policy",
            f"{name}-exec does not exist, and the namespace names it as its default role - "
            "an absent role holds no policy too, so this is drift from the warehouse slice "
            "and not a pass",
        )
    elif facts["exec_role"] is None:
        checks.note(
            "WH-1b",
            f"{tag} the namespace role holds no policy",
            f"unread: a read of {name}-exec failed (see the failed calls)",
        )
    elif facts["exec_attached"] or facts["exec_inline"]:
        checks.fail(
            "WH-1b",
            f"{tag} the namespace role holds no policy",
            f"attached {facts['exec_attached']}, inline {facts['exec_inline']} - this role "
            "is what COPY, UNLOAD and awsdatacatalog run as, so a lake grant here is the "
            "D13 bypass 5b decision 5 withheld. A grant is legal; it needs a named "
            "requester and a line in the log",
        )
    else:
        checks.ok(
            "WH-1b",
            f"{tag} the namespace role holds no policy",
            "no attached policy, no inline policy (5b decision 5)",
        )

    # ----------------------------------------------------------- the two alarms (5b 6.2, 6h dec 7)
    names = {a[0] for a in facts.get("alarms", [])}
    missing_alarms = [
        n for n in (f"{name}-compute-capacity", f"{name}-data-storage") if n not in names
    ]
    if ns is None:
        checks.note("WH-4b", f"{tag} both alarms exist", "no namespace")
    elif missing_alarms:
        checks.fail(
            "WH-4b",
            f"{tag} both alarms exist",
            f"missing {missing_alarms} - ComputeCapacity is the only notice that the "
            "irreversible ratchet moved, and DataStorage is the only bound on TOTAL "
            "storage (a schema QUOTA bounds one schema and nothing bounds their number)",
        )
    else:
        checks.ok(
            "WH-4b",
            f"{tag} both alarms exist",
            ", ".join(f"{a[0].rsplit('-', 2)[-1]}:{a[3]}" for a in facts["alarms"]),
        )

    # ------------------------------------------------------- WH-6 / WH-12: the database session
    dbs = facts.get("databases")
    if not want_sql:
        for cid, what in (
            ("WH-6", "one class container, and not the other class's"),
            ("WH-12", "the schemas, roles and grants"),
        ):
            checks.note(
                cid,
                f"{tag} {what}",
                "--sql not given. These need a database session, because a Redshift GRANT "
                "has no list-permissions API and is readable only from SVV_*",
            )
    elif dbs is None:
        checks.note(
            "WH-6",
            f"{tag} one class container, and not the other class's",
            "the Data API returned nothing - no workgroup, or the secret is unreadable",
        )
        checks.note("WH-12", f"{tag} the schemas, roles and grants", "no database session")
    else:
        local = {r[0] for r in dbs if r[1] == "local"}
        want_db = CLASS_DB.get(env)
        other = {v for k, v in CLASS_DB.items() if k != env}
        unexpected = local - {want_db} - set(INERT_DBS)
        wrong_class = local & other
        if wrong_class:
            checks.fail(
                "WH-6",
                f"{tag} one class container, and not the other class's",
                f"{sorted(wrong_class)} in this account - the class is the ACCOUNT plus "
                "the database name, and the account boundary is the real control",
            )
        elif want_db not in local:
            checks.fail(
                "WH-6",
                f"{tag} one class container, and not the other class's",
                f"`{want_db}` is absent; local databases are {sorted(local)}",
            )
        elif unexpected:
            checks.fail(
                "WH-6",
                f"{tag} one class container, and not the other class's",
                f"unexpected database(s) {sorted(unexpected)} - a second container is not "
                "prevented, only checked, which is the designed order",
            )
        else:
            checks.ok(
                "WH-6",
                f"{tag} one class container, and not the other class's",
                f"`{want_db}` plus the inert {sorted(local & set(INERT_DBS))}",
            )

        # WH-12 reports rather than judges: who may write which schema is the register's question,
        # and the register is docs/AWS_STATE.md. What it CAN fail on is the shape - a schema whose
        # owner is a project's own database user would make one project privileged over the others
        # sharing it, which is the ownership-is-singular problem the _rw role exists to avoid.
        schemas = facts.get("schemas") or []
        themed = [s for s in schemas if s[0] != "public"]
        checks.ok(
            "WH-12",
            f"{tag} the schemas, roles and grants",
            f"{len(themed)} themed schema(s) in `{want_db}`, "
            f"{len(facts.get('role_grants') or [])} role grant(s), "
            f"{len(facts.get('user_grants') or [])} user-role grant(s) - "
            "the register is docs/AWS_STATE.md",
        )

    # ---------------------------------- WH-14: a shared schema whose tables nobody else can read
    #
    # THE REQUIREMENT IS A SHARED SCHEMA AND OWNERSHIP IS SINGULAR. `sbx_<theme>_rw` carries
    # `USAGE, CREATE ON SCHEMA`, which lets every admitted project create its own tables - and
    # carries nothing on a table somebody else created. So a second project reads NOTHING of the
    # first's unless either the relation grants SELECT to the role, or the creating user has a
    # default privilege that does it for every future table.
    #
    # Measured 2026-10-10, on the first table a project ever wrote: `relacl` null, no default
    # privilege anywhere, so the schema was shareable in name only. This check is what makes that
    # state visible instead of arriving at the second project as "I cannot see their data".
    if not want_sql:
        checks.note("WH-14", f"{tag} a shared schema's tables are readable", "no database session")
    else:
        rels = facts.get("relations") or []
        reads = {(r[0], r[1]) for r in (facts.get("relation_role_reads") or [])}
        defaults = {(d[0], d[1]) for d in (facts.get("default_privs") or [])}
        unreadable = [
            f"{s}.{rel} (owner {owner})"
            for s, rel, owner in rels
            if (s, rel) not in reads and (s, owner) not in defaults
        ]
        if not rels:
            checks.note(
                "WH-14",
                f"{tag} a shared schema's tables are readable",
                "no table in any themed schema yet, so the sharing shape is untested. It is "
                "tested by the FIRST table a project writes, not by the grant that let it",
            )
        elif unreadable:
            checks.fail(
                "WH-14",
                f"{tag} a shared schema's tables are readable",
                f"{len(unreadable)} relation(s) no role can read: {', '.join(unreadable[:4])}. "
                "The schema is shared in name only - a second project admitted to it would get "
                "`CREATE` and see none of this data. Fix per relation with `GRANT SELECT ON "
                "TABLE <rel> TO ROLE <theme role>`, and for every future table with `ALTER "
                "DEFAULT PRIVILEGES FOR USER <the creating user> IN SCHEMA <theme> GRANT SELECT "
                "ON TABLES TO ROLE <theme role>` - which is per creating USER, so it is owed once "
                "per admitted project (Lesson 14)",
            )
        else:
            checks.ok(
                "WH-14",
                f"{tag} a shared schema's tables are readable",
                f"{len(rels)} relation(s), each reachable by a role through a grant or a default "
                f"privilege; {len(defaults)} default-privilege pair(s) cover future tables",
            )

    # ------------------------------------- WH-13: the quota, which cannot be read on this platform
    #
    # SVV_SCHEMA_QUOTA_STATE and STV_SCHEMA_QUOTA_STATE are both REFUSED to the namespace admin -
    # a superuser - through the Data API (measured 2026-09-20: "permission denied for relation
    # svv_schema_quota_state"). The view the plan named as this check's instrument is not readable,
    # and no other catalog view carries a schema's quota, so WH-13 is a note that says so rather
    # than a check that passes on nothing (Lesson 13). What IS measured is the enforcement: a
    # breach aborts the transaction with its own wording, recorded in the Stage 5b log.
    checks.note(
        "WH-13",
        f"{tag} every themed schema carries a quota",
        "UNREADABLE on Redshift Serverless: svv_schema_quota_state and its stv_ sibling "
        "are refused to a superuser through the Data API. The quota is authored in the "
        "runbook's CREATE SCHEMA and proven by breach, not by a describe",
    )


def main(argv: list) -> int:
    want_sql = "--sql" in argv
    wanted = [a for a in argv if not a.startswith("--")] or list(DEFAULT_PROFILES)

    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    errors = ErrorLog()
    callers = profiles.preflight(wanted, errors, out_label=out_label)
    authored = authored_projects(ctx.repo_root / PROJECTS_VARS)
    domain = authored_domain(ctx.repo_root / PROJECTS_VARS)

    checks = Checks()
    per_account = []
    for caller in callers:
        if not caller.live:
            continue
        cli = profiles.cli_for(caller.profile, errors)
        facts = read_account(cli, env_of(caller.profile), want_sql, authored, domain)
        per_account.append((caller, facts))
        judge(checks, facts, authored, want_sql)

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        rep.banner("The Redshift Serverless warehouse and its cost ceiling")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {", ".join(c.profile for c in callers)}
sql       : {"yes - SELECTs through the Data API" if want_sql else "no (pass --sql)"}

The stage files are docs/plan/stages/stage-05b-redshift-serverless.md (the warehouse) and
stage-06h-redshift-connection.md (the connection and its three layers). D40 settles what is
built and what is not.

WHAT THIS FILE CANNOT TELL YOU: whether a SageMaker project can reach the warehouse. That is an
intersection of three layers in three systems - the AmazonDataZoneProject tag on both objects,
the project role's IAM, and a Redshift GRANT - and only a connection answers it (Lesson 28).

This file is not versioned (aws/output/ is in .gitignore). Regenerate it rather than trusting a
stale copy.""")

        for caller, facts in per_account:
            rep.h1(f"{facts['env']} - {facts['name']}")
            wg = facts.get("workgroup")
            ns = facts.get("namespace")
            if ns is None and wg is None:
                rep.line("no namespace and no workgroup in this account.")
                continue
            rows = ["WHAT\tVALUE"]
            if ns:
                rows += [
                    f"namespace\t{ns['namespaceName']} ({ns['status']})",
                    f"admin user\t{ns.get('adminUsername', '-')}",
                    f"admin secret\t{'Secrets Manager' if ns.get('adminPasswordSecretArn') else 'NONE'}",
                    f"secret's key\t{ns.get('adminPasswordSecretKmsKeyId') or 'the Secrets Manager key'}",
                    f"log exports\t{', '.join(sorted(ns.get('logExports') or [])) or 'none'}",
                    f"default role\t{(ns.get('defaultIamRoleArn') or '-').rsplit('/', 1)[-1]}",
                ]
            if wg:
                ep = wg.get("endpoint") or {}
                rows += [
                    f"workgroup\t{wg['workgroupName']} ({wg['status']})",
                    f"capacity\tbase {wg.get('baseCapacity')} / max {wg.get('maxCapacity')} RPU",
                    f"price-perf target\t{(wg.get('pricePerformanceTarget') or {}).get('status')}",
                    f"host\t{(ep.get('address') or '-').split('.', 1)[0]}.<account>."
                    f"{'.'.join((ep.get('address') or '').split('.')[2:])}:{ep.get('port')}",
                    f"subnets\t{len(wg.get('subnetIds') or [])} in the private tier",
                ]
            else:
                rows.append(
                    "workgroup\tABSENT - the [E] compute is down, which is the "
                    "powered-off state (no pause exists)"
                )
            rep.tabulate(rows)

            rep.h2("the ceiling")
            limits = facts.get("usage_limits", [])
            if limits:
                rep.tabulate(
                    ["TYPE\tAMOUNT\tPERIOD\tBREACH ACTION"]
                    + [
                        f"{u['usageType']}\t{u['amount']}\t{u['period']}\t{u['breachAction']}"
                        for u in limits
                    ]
                )
            else:
                rep.line("no usage limit (there is no workgroup to carry one).")

            rep.h2("the burn")
            seconds = facts.get("compute_seconds_today", 0.0)
            # 0.36 USD/RPU-hour, docs/PRICING.md 5, offer file published 2026-09-11.
            rep.line(
                f"today, so far : {seconds:.0f} RPU-seconds "
                f"= {seconds / 3600 * 0.36:.4f} USD at 0.36/RPU-hour"
            )
            last = facts.get("compute_last_interval")
            if last:
                stamp, value = last
                rate = value / 1800.0
                verdict = (
                    "IDLE - nothing is running"
                    if rate < 0.1
                    else f"{rate:.2f} RPU sustained = {rate * 0.36:.2f} USD/h WHILE IT LASTS"
                )
                rep.line(f"last interval : {value:.0f} RPU-seconds at {stamp} -> {verdict}")
                if rate >= 3.5:
                    rep.line(
                        "  ^^ AT OR ABOVE BASE CAPACITY FOR A WHOLE INTERVAL. A workgroup that "
                        "never goes idle is a query nobody is watching: check "
                        "sys_query_history for status 'running' and how long."
                    )
            rep.line()
            rep.line(
                "READ THE LAST INTERVAL, NOT THE DAY'S TOTAL, to answer 'is it costing me anything "
                "right now'. The total is a sum over a window and stays high all day after one "
                "expensive query; it published 405, then 4,743, then 94,767 for the same day while "
                "a query was still running (Stage 5b, 5.3 and its three amendments)."
            )
            rep.line(
                "The metric lands per 30-minute interval, so the newest few minutes are never in it."
            )
            rep.line(
                "The free trial is active in Sandbox until 2026-12-19 (287.90 of 300 USD left on "
                "2026-10-17, the Redshift console's Free trial section; 5b verification xiii): these "
                "figures are absorbed by it, not billed, and the bill shows them only after it ends."
            )

            rep.h2("the audit groups")
            rep.tabulate(
                ["GROUP\tRETENTION"]
                + [
                    f"{g}\t{r if r is not None else 'NEVER EXPIRE'}"
                    for g, r in sorted(facts.get("log_groups", {}).items())
                ]
                or ["(none)"]
            )

            rep.h2("the tag pair - layer 1")
            rep.tabulate(
                ["OBJECT\tAmazonDataZoneProject\tWIDE TAG"]
                + [
                    f"{obj}\t{t.get('AmazonDataZoneProject', '-')}\t{t.get(WIDE_TAG, 'absent')}"
                    for obj, t in (
                        ("workgroup", facts.get("workgroup_tags", {})),
                        ("namespace", facts.get("namespace_tags", {})),
                    )
                ]
            )
            rep.line()
            rep.line(
                "AmazonDataZoneProject is a SINGLE-VALUED tag key, on both objects. AWS's "
                "only way to admit more than one project is the wide tag, refused here, so "
                "layer 1 admits exactly one project (6h decision 8)."
            )

            conn_rows = [
                f"{pid}\t{c['name']}\t{c['database']}\t{c['access_role']}\t"
                f"{('ON ' + str(c['schedule'])) if c['lineage'] else 'off'}"
                for pid, found in sorted((facts.get("connections") or {}).items())
                for c in (found if isinstance(found, list) else [])
            ]
            if facts.get("connections"):
                rep.h2("the connection - 6h 3.2")
                rep.tabulate(
                    ["PROJECT\tCONNECTION\tDATABASE\tACCESS ROLE\tLINEAGE SYNC"] + conn_rows
                    if conn_rows
                    else ["(no Redshift connection read - see WH-9)"]
                )

            if facts.get("databases") is not None:
                rep.h2("the databases, schemas and grants")
                rep.tabulate(
                    ["DATABASE\tTYPE\tACL"]
                    + ["\t".join(str(c) for c in r) for r in facts["databases"]]
                )
                rep.line()
                rep.tabulate(
                    ["SCHEMA\tOWNER\tACL"]
                    + ["\t".join(str(c) for c in r) for r in (facts.get("schemas") or [])]
                    or ["(none)"]
                )
                rep.line()
                rep.tabulate(
                    ["DB USER\tSUPERUSER"]
                    + ["\t".join(str(c) for c in r) for r in (facts.get("users") or [])]
                    or ["(none)"]
                )
                rep.line()
                rep.tabulate(
                    ["DB USER\tROLE"]
                    + ["\t".join(str(c) for c in r) for r in (facts.get("user_grants") or [])]
                    or ["(no user holds any role - layer 3 has admitted nobody)"]
                )

        rep.h1("Checks")
        rep.checks_table(checks)

        rep.h1("Calls that failed")
        failed_calls_epilogue(rep, errors)

    note(f"wrote {out_label}")
    if checks.n_fail():
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
