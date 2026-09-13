#!/usr/bin/env -S uv run --quiet
# remote-ide.py - the remote-IDE channel's standing facts: what a laptop's VS Code session into a
#                 Sandbox space rests on, and who opened one from where.
#
#   needs:    a live SSO session for the infrastructure user; one login covers the three profiles:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/remote-ide.py
#             ./aws/remote-ide.py --days 30      # how far back RI-5 reads StartSession (default 7)
#   writes:   aws/output/remote-ide.txt   (untracked - see .gitignore)
#   reads:    in Sandbox - ec2:DescribeVpcEndpoints, sagemaker:ListDomains, ListSpaces, DescribeSpace,
#             ec2:DescribeInstanceTypes, iam:GetRole, ListAttachedRolePolicies, GetPolicy,
#             GetPolicyVersion, cloudtrail:LookupEvents; in Identity - sso-admin:ListInstances,
#             ListPermissionSets, DescribePermissionSet, GetInlinePolicyForPermissionSet; in
#             Production - ec2:DescribeAddresses; and sts:GetCallerIdentity. Every one is a read.
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# WHAT THE CHANNEL IS, as Stage 6d step 7 measured it (2026-09-07/11). `sagemaker:StartSession` is
# called by the client AS THE PROJECT ROLE, so the persona sets' deny pair and DenyControlPlaneOffVpn
# never evaluate on it. What scopes the call is therefore AWS's managed policy on the project role -
# an Allow conditioned on two tag pairs - and that policy is AWS's, versioned, and moves without this
# repository. The pair in the persona sets is ours and matches it key for key today. RI-3 and RI-4 read
# both, because the day they diverge the scoping this estate relies on is the one it did not write.
#
# The checks:
#   RI-1  the seven endpoints the space side needs (6d step 7.1) exist while sandbox/egress is up. A
#         partial set is the failure; an empty one is the slice being down, reported as a note.
#   RI-2  every space with RemoteAccess ENABLED is at least 8 GiB, the vendor's floor; its type, memory
#         and the us-west-2 rate docs/PRICING.md records are printed. No ceiling is asserted on spaces.
#   RI-3  every Allow of sagemaker:StartSession reaching a project role is conditioned on both the
#         project tag and the user tag. An unconditioned Allow is the failure.
#   RI-4  the persona sets carry both deny Sids, on the same resource-tag keys RI-3's Allow reads.
#   RI-5  the StartSession calls of the last N days, by caller and by source address - the proxy's
#         Elastic IP (the monitored VPN profile), the VPN host's, or anything else. An "other public
#         address" is a laptop's own uplink, which is either off the VPN or on the split-tunnel
#         profile: split-tunnel sends public AWS API calls out of the laptop's uplink by design, so
#         the two read identically here. Reported, not asserted: "VPN-only" for this channel is
#         Stage 6d decision 4, which is open.
#
# What it cannot see (Lesson 13): whether a session is live, whether it outlived the tunnel or a
# portal logout (6d step 7.7), and which user a project-role call stands for - the role's session
# name is the service's, and the principal tags the conditions read are not in CloudTrail.

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatchcase

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "remote-ide.txt"
SANDBOX = "awsds-infra-sandbox-1"
IDENTITY = "awsds-infra-identity"
PRODUCTION = "awsds-infra-prod"

BEDROCK_VARIABLES = "terraform-live/sandbox/bedrock/variables.tf"
PRICING = "docs/PRICING.md"

# 6d step 7.1: the SMUS isolated-VPC table read against sandbox/egress. `sagemaker.studio` is the one
# service whose name carries the `aws.` prefix rather than `com.amazonaws.`.
ENDPOINT_SERVICES = (
    "com.amazonaws.{r}.sts",
    "com.amazonaws.{r}.ssm",
    "com.amazonaws.{r}.ssmmessages",
    "com.amazonaws.{r}.sagemaker.api",
    "com.amazonaws.{r}.sagemaker.runtime",
    "aws.sagemaker.{r}.studio",
    "com.amazonaws.{r}.datazone",
)
MIN_MEMORY_MIB = 8 * 1024

# The six sets the persona deny pair is composed into (identity/sso policies-sagemaker.tf).
PERSONA_SETS = (
    "DataScientistAccess",
    "DataScientistStagingAccess",
    "DataScientistProdAccess",
    "DeploymentManagerAccess",
    "GovernanceManagerAccess",
    "DevEnvStewardAccess",
)
PAIR_SIDS = ("DenyRemoteSessionOnSomeoneElsesSpace", "DenyRemoteSessionAsSomeoneElse")
PROXY_EIP_NAME = "awsds-prod-proxy"
VPN_EIP_NAME = "awsds-prod-vpn"

PROJECT_ROLES_RE = re.compile(
    r'variable\s+"project_roles"\s*\{.*?default\s*=\s*\[(?P<body>.*?)\]', re.S
)


def listify(value) -> list:
    return value if isinstance(value, list) else [value]


def matches(action: str, statement: dict) -> bool:
    """Whether a statement's Action/NotAction covers `action`, wildcards included."""
    if "Action" in statement:
        return any(fnmatchcase(action.lower(), a.lower()) for a in listify(statement["Action"]))
    if "NotAction" in statement:
        return not any(
            fnmatchcase(action.lower(), a.lower()) for a in listify(statement["NotAction"])
        )
    return False


def condition_keys(statement: dict) -> set:
    """Every condition key a statement reads, lower-cased."""
    return {key.lower() for block in (statement.get("Condition") or {}).values() for key in block}


def json_or_none(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def recorded_rate(pricing_text: str, instance_type: str) -> str | None:
    """The us-west-2 cell of a PRICING.md row naming a Studio app at `instance_type`."""
    for line in pricing_text.splitlines():
        if "SageMaker Studio" in line and f"`{instance_type}`" in line and line.startswith("|"):
            cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
            if len(cells) >= 3 and re.fullmatch(r"[0-9.]+", cells[2]):
                return cells[2]
    return None


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    days = 7
    if "--days" in argv:
        i = argv.index("--days")
        try:
            days = int(argv[i + 1])
        except (IndexError, ValueError):
            note("--days needs a whole number")
            return 2

    errors = ErrorLog()
    callers = profiles.preflight([SANDBOX, IDENTITY, PRODUCTION], errors, out_label=out_label)
    live = {c.profile: c for c in callers}
    sbx = AwsCli(profile=SANDBOX, region=context.REGION, errors=errors, echo_profile=True)
    idn = AwsCli(profile=IDENTITY, region=context.REGION, errors=errors, echo_profile=True)
    prd = AwsCli(profile=PRODUCTION, region=context.REGION, errors=errors, echo_profile=True)
    checks = Checks()

    # ------------------------------------------------------------------ RI-1 the endpoints
    wanted = [s.format(r=context.REGION) for s in ENDPOINT_SERVICES]
    endpoints: dict = {}
    if live[SANDBOX].live:
        res = sbx.run(
            "ec2",
            "describe-vpc-endpoints",
            "--filters",
            f"Name=service-name,Values={','.join(wanted)}",
            "--query",
            "VpcEndpoints[].[ServiceName,VpcEndpointId,State]",
            "--output",
            "json",
        )
        for name, vpce, state in json_or_none(res.stdout) or []:
            endpoints.setdefault(name, []).append((vpce, state))
        available = [s for s in wanted if any(st == "available" for _, st in endpoints.get(s, []))]
        if not endpoints:
            checks.note(
                "RI-1",
                "the seven endpoints the space side needs",
                "none exists - sandbox/egress is down, and no space can start or be reached",
            )
        elif len(available) == len(wanted):
            checks.ok("RI-1", "the seven endpoints the space side needs", "all available")
        else:
            missing = [
                s.split(".")[-1] if s.startswith("com.") else "sagemaker.studio"
                for s in wanted
                if s not in available
            ]
            checks.fail(
                "RI-1",
                "the seven endpoints the space side needs",
                f"missing or not available: {', '.join(missing)} - a partial set is a slice defect",
            )

    # ------------------------------------------------------------------ RI-2 the spaces
    pricing_text = (
        (ctx.repo_root / PRICING).read_text(encoding="utf-8")
        if (ctx.repo_root / PRICING).is_file()
        else ""
    )
    space_rows: list = []
    memory: dict = {}
    if live[SANDBOX].live:
        res = sbx.run(
            "sagemaker", "list-domains", "--query", "Domains[].DomainId", "--output", "json"
        )
        for domain in json_or_none(res.stdout) or []:
            res = sbx.run(
                "sagemaker",
                "list-spaces",
                "--domain-id-equals",
                domain,
                "--query",
                "Spaces[].SpaceName",
                "--output",
                "json",
            )
            for space in json_or_none(res.stdout) or []:
                res = sbx.run(
                    "sagemaker",
                    "describe-space",
                    "--domain-id",
                    domain,
                    "--space-name",
                    space,
                    "--query",
                    "SpaceSettings",
                    "--output",
                    "json",
                )
                settings = json_or_none(res.stdout) or {}
                app = settings.get("AppType") or "-"
                spec = (settings.get(f"{app}AppSettings") or {}).get("DefaultResourceSpec") or {}
                space_rows.append(
                    (
                        space,
                        app,
                        settings.get("RemoteAccess") or "-",
                        spec.get("InstanceType") or "-",
                    )
                )
        types = sorted({t for *_, t in space_rows if t.startswith("ml.")})
        if types:
            res = sbx.run(
                "ec2",
                "describe-instance-types",
                "--instance-types",
                *[t[3:] for t in types],
                "--query",
                "InstanceTypes[].[InstanceType,MemoryInfo.SizeInMiB]",
                "--output",
                "json",
            )
            memory = {f"ml.{name}": mib for name, mib in json_or_none(res.stdout) or []}
        remote = [r for r in space_rows if r[2] == "ENABLED"]
        small = [r for r in remote if memory.get(r[3], 0) < MIN_MEMORY_MIB]
        if not remote:
            checks.note(
                "RI-2",
                "every remote-access space is at least 8 GiB",
                "no space has RemoteAccess ENABLED",
            )
        elif small:
            checks.fail(
                "RI-2",
                "every remote-access space is at least 8 GiB",
                ", ".join(f"{s} {t} ({memory.get(t, '?')} MiB)" for s, _, _, t in small),
            )
        else:
            checks.ok(
                "RI-2",
                "every remote-access space is at least 8 GiB",
                ", ".join(f"{s} {t}" for s, _, _, t in remote),
            )

    # ------------------------------------------------------------------ RI-3 the project role
    grants: list = []  # (role, policy, version, sid, condition keys)
    boundaries: dict = {}
    roles: list = []
    variables = ctx.repo_root / BEDROCK_VARIABLES
    if variables.is_file():
        m = PROJECT_ROLES_RE.search(variables.read_text(encoding="utf-8"))
        roles = re.findall(r'"([^"]+)"', m.group("body")) if m else []
    if live[SANDBOX].live and roles:
        for role in roles:
            res = sbx.run(
                "iam",
                "get-role",
                "--role-name",
                role,
                "--query",
                "Role.PermissionsBoundary.PermissionsBoundaryArn",
                "--output",
                "text",
            )
            boundaries[role] = res.stdout.strip() if res.ok else "(call failed)"
            res = sbx.run(
                "iam",
                "list-attached-role-policies",
                "--role-name",
                role,
                "--query",
                "AttachedPolicies[].PolicyArn",
                "--output",
                "json",
            )
            for arn in json_or_none(res.stdout) or []:
                version = sbx.run(
                    "iam",
                    "get-policy",
                    "--policy-arn",
                    arn,
                    "--query",
                    "Policy.DefaultVersionId",
                    "--output",
                    "text",
                )
                if not version.ok:
                    continue
                vid = version.stdout.strip()
                doc = sbx.run(
                    "iam",
                    "get-policy-version",
                    "--policy-arn",
                    arn,
                    "--version-id",
                    vid,
                    "--query",
                    "PolicyVersion.Document",
                    "--output",
                    "json",
                )
                for statement in listify((json_or_none(doc.stdout) or {}).get("Statement", [])):
                    if statement.get("Effect") == "Allow" and matches(
                        "sagemaker:StartSession", statement
                    ):
                        grants.append(
                            (
                                role,
                                arn.rsplit("/", 1)[-1],
                                vid,
                                statement.get("Sid", "-"),
                                condition_keys(statement),
                            )
                        )
    allow_keys: set = set()
    if not roles:
        checks.note(
            "RI-3",
            "StartSession reaches a project role only tag-scoped",
            f"no project_roles read from {BEDROCK_VARIABLES}",
        )
    elif live[SANDBOX].live:
        unscoped = [
            g
            for g in grants
            if not {"aws:resourcetag/amazondatazoneproject", "aws:resourcetag/amazondatazoneuser"}
            <= g[4]
        ]
        allow_keys = set().union(*(g[4] for g in grants)) if grants else set()
        if not grants:
            checks.note(
                "RI-3",
                "StartSession reaches a project role only tag-scoped",
                "no Allow of sagemaker:StartSession found - the remote IDE cannot open",
            )
        elif unscoped:
            checks.fail(
                "RI-3",
                "StartSession reaches a project role only tag-scoped",
                "; ".join(
                    f"{p} {v} {sid} reads {sorted(k) or 'no condition'}"
                    for _, p, v, sid, k in unscoped
                ),
            )
        else:
            checks.ok(
                "RI-3",
                "StartSession reaches a project role only tag-scoped",
                "; ".join(f"{p} {v} {sid}" for _, p, v, sid, _ in grants),
            )

    # ------------------------------------------------------------------ RI-4 the persona pair
    pair_rows: list = []  # (set, sid present per PAIR_SIDS, resource-tag keys)
    if live[IDENTITY].live:
        res = idn.run(
            "sso-admin", "list-instances", "--query", "Instances[0].InstanceArn", "--output", "text"
        )
        instance = res.stdout.strip() if res.ok else ""
        if instance and instance != "None":
            res = idn.run(
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                instance,
                "--query",
                "PermissionSets[]",
                "--output",
                "json",
            )
            for arn in json_or_none(res.stdout) or []:
                name = idn.run(
                    "sso-admin",
                    "describe-permission-set",
                    "--instance-arn",
                    instance,
                    "--permission-set-arn",
                    arn,
                    "--query",
                    "PermissionSet.Name",
                    "--output",
                    "text",
                ).stdout.strip()
                if name not in PERSONA_SETS:
                    continue
                body = idn.run(
                    "sso-admin",
                    "get-inline-policy-for-permission-set",
                    "--instance-arn",
                    instance,
                    "--permission-set-arn",
                    arn,
                    "--query",
                    "InlinePolicy",
                    "--output",
                    "text",
                ).stdout
                statements = {
                    s.get("Sid"): s
                    for s in listify((json_or_none(body) or {}).get("Statement", []))
                }
                keys = (
                    set().union(
                        *(condition_keys(statements[s]) for s in PAIR_SIDS if s in statements)
                    )
                    if statements
                    else set()
                )
                pair_rows.append(
                    (
                        name,
                        tuple(s in statements for s in PAIR_SIDS),
                        {k for k in keys if k.startswith("aws:resourcetag/")},
                    )
                )
        missing_sets = [n for n in PERSONA_SETS if n not in {r[0] for r in pair_rows}]
        lacking = [r[0] for r in pair_rows if not all(r[1])]
        allow_tags = {k for k in allow_keys if k.startswith("aws:resourcetag/")}
        differ = [r[0] for r in pair_rows if allow_tags and r[2] != allow_tags]
        if missing_sets or lacking:
            checks.fail(
                "RI-4",
                "the persona pair matches the project role's Allow",
                f"sets not read: {missing_sets or '-'}; sets without both Sids: {lacking or '-'}",
            )
        elif differ:
            checks.fail(
                "RI-4",
                "the persona pair matches the project role's Allow",
                f"{', '.join(differ)} scope on {sorted(pair_rows[0][2])} where the Allow reads {sorted(allow_tags)}",
            )
        elif not allow_tags:
            checks.note(
                "RI-4",
                "the persona pair matches the project role's Allow",
                "all six carry both Sids; RI-3 read no Allow to compare",
            )
        else:
            checks.ok(
                "RI-4",
                "the persona pair matches the project role's Allow",
                f"all six carry both Sids, on {sorted(allow_tags)}",
            )

    # ------------------------------------------------------------------ RI-5 the calls
    eips: dict = {}
    if live[PRODUCTION].live:
        res = prd.run(
            "ec2",
            "describe-addresses",
            "--query",
            "Addresses[].[PublicIp,Tags[?Key=='Name']|[0].Value]",
            "--output",
            "json",
        )
        eips = {ip: name for ip, name in json_or_none(res.stdout) or []}
    calls: list = []
    if live[SANDBOX].live:
        start = (
            (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()
        )
        token = None
        while True:
            args = [
                "cloudtrail",
                "lookup-events",
                "--lookup-attributes",
                "AttributeKey=EventName,AttributeValue=StartSession",
                "--start-time",
                start,
                "--max-results",
                "50",
                "--output",
                "json",
            ]
            if token:
                args += ["--next-token", token]
            res = sbx.run(*args)
            page = json_or_none(res.stdout) or {}
            for event in page.get("Events", []):
                record = json_or_none(event.get("CloudTrailEvent")) or {}
                if record.get("eventSource") != "sagemaker.amazonaws.com":
                    continue
                arn = record.get("userIdentity", {}).get("arn", "")
                caller = arn.split("/")[-2] if arn.count("/") >= 2 else arn
                ip = record.get("sourceIPAddress", "-")
                where = eips.get(ip) or (
                    "private" if ip.startswith("10.") else "other public address"
                )
                calls.append(
                    (
                        record.get("eventTime", ""),
                        caller,
                        ip,
                        where,
                        record.get("errorCode") or "ok",
                    )
                )
            token = page.get("NextToken")
            if not token or not res.ok:
                break
        calls.sort(reverse=True)
        by_where = Counter(c[3] for c in calls)
        if not calls:
            checks.note("RI-5", f"StartSession calls, last {days} days", "none")
        else:
            checks.note(
                "RI-5",
                f"StartSession calls, last {days} days",
                ", ".join(f"{n} from {w}" for w, n in by_where.most_common())
                + (
                    "; an 'other public address' is a laptop's own uplink - off the VPN or on the "
                    "split-tunnel profile, which this reading cannot tell apart (6d decision 4)"
                    if by_where.get("other public address")
                    else ""
                ),
            )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        rep.banner("The remote-IDE channel: what a session rests on, and who opened one")
        rep.text(f"""generated : {context.utc_stamp()}
region    : {context.REGION}
produced  : aws/remote-ide.py   (index: aws/INDEX.md)

SECTIONS
  1. What was read, and as whom
  2. The endpoints the space side needs
  3. The spaces, and which accept a remote session
  4. What grants StartSession to the project role
  5. The persona deny pair
  6. StartSession calls
  7. Checks
  8. Calls that failed

HOW TO READ THIS FILE
  - THE SCOPING THIS CHANNEL HAS IS AWS'S. The call is made as the project role, so the
    persona pair in section 5 never evaluates on it; section 4's managed-policy Allow is
    what scopes it, and its version moves without this repository.
  - "OTHER PUBLIC ADDRESS" IN SECTION 6 IS A LAPTOP'S OWN UPLINK: off the VPN, or on the
    split-tunnel profile, which sends public AWS API calls out of the laptop by design. Only
    the monitored profile arrives from the proxy's address. Nothing refuses either today;
    that is Stage 6d decision 4, open.
  - A SPACE AT LESS THAN 8 GiB WITH REMOTE ACCESS ON starts, and then its session fails.

This file is not versioned (aws/output/ is in .gitignore). Regenerate it rather than
trusting a stale copy.""")

        rep.h1("1. What was read, and as whom")
        rep.tabulate(["PROFILE\tCALLER"] + [f"{c.profile}\t{c.arn or '(failed)'}" for c in callers])

        rep.h1("2. The endpoints the space side needs")
        rep.tabulate(
            ["SERVICE\tENDPOINT\tSTATE"]
            + [
                f"{s}\t{', '.join(v for v, _ in endpoints.get(s, [])) or '-'}\t{', '.join(st for _, st in endpoints.get(s, [])) or 'absent'}"
                for s in wanted
            ]
        )

        rep.h1("3. The spaces, and which accept a remote session")
        if not space_rows:
            rep.text("No space read.")
        else:
            rep.tabulate(
                ["SPACE\tAPP\tREMOTE ACCESS\tINSTANCE\tMEMORY MiB\tUSD/H (PRICING.md)"]
                + [
                    f"{s}\t{a}\t{r}\t{t}\t{memory.get(t, '-')}\t{recorded_rate(pricing_text, t) or 'not recorded'}"
                    for s, a, r, t in space_rows
                ]
            )

        rep.h1("4. What grants StartSession to the project role")
        rep.tabulate(
            ["ROLE\tBOUNDARY"]
            + [
                f"{r}\t{b.rsplit('/', 1)[-1] if b and b != 'None' else 'NONE'}"
                for r, b in boundaries.items()
            ]
        )
        rep.line()
        rep.tabulate(
            ["POLICY\tVERSION\tSID\tCONDITION KEYS"]
            + [f"{p}\t{v}\t{sid}\t{', '.join(sorted(k)) or 'none'}" for _, p, v, sid, k in grants]
        )

        rep.h1("5. The persona deny pair")
        rep.tabulate(
            ["PERMISSION SET\t" + "\t".join(PAIR_SIDS) + "\tRESOURCE-TAG KEYS"]
            + [
                f"{n}\t"
                + "\t".join("yes" if p else "NO" for p in present)
                + f"\t{', '.join(sorted(k)) or '-'}"
                for n, present, k in pair_rows
            ]
        )

        rep.h1(f"6. StartSession calls, last {days} days")
        if not calls:
            rep.text("None in CloudTrail.")
        else:
            rep.tabulate(
                ["TIME (UTC)\tCALLER\tSOURCE\tWHERE\tRESULT"]
                + [f"{t}\t{c}\t{ip}\t{w}\t{e}" for t, c, ip, w, e in calls[:40]]
            )

        rep.h1("7. Checks")
        rep.checks_table(checks)

        rep.h1("8. Calls that failed")
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
