#!/usr/bin/env -S uv run --quiet
# proxy.py - Stage 6c's evidence for the estate's SINGLE INTERNET EXIT: the Squid host ([D]),
# the [P] anchors it wears (the Elastic IP, the security group, the allow-list parameter, the
# access log group), the ORDER of its `http_access` rules, and whether the config actually
# running on the host is the one this repository committed.
#
# THE SHAPE IS ./aws/vpn.py's, DELIBERATELY: same two-mode structure, same --on-host fence, same
# "an empty answer and a failed answer are different things" discipline. The two files are the
# instruments for D38's two hosts - one way in, one way out - and a reader who knows one should
# not have to learn the other.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/proxy.py                      # the two profiles it needs (see below)
#             ./aws/proxy.py awsds-infra-prod     # only the ones named
#             ./aws/proxy.py --on-host            # ALSO read inside the host (see below)
#   writes:   aws/output/proxy.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeInstances, DescribeAddresses, DescribeSecurityGroups,
#             ssm:GetParameter, logs:DescribeLogGroups, DescribeSubscriptionFilters,
#             DescribeExportTasks, sso-admin:ListInstances, ListPermissionSets,
#             DescribePermissionSet, GetInlinePolicyForPermissionSet, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything - see the next line for the
#             single, typed exception.
#   sends:    NOTHING IN AWS, unless --on-host is typed. That flag adds ssm:SendCommand +
#             GetCommandInvocation, and SendCommand is a WRITE API - it creates a Command, is a
#             mutating CloudTrail event, and runs code on an instance - even though every
#             command it carries is a read. It is a flag and not a default precisely so that
#             `./aws/proxy.py` stays safe to fire at anything. What it buys is PX-3: the
#             squid.conf the host is SERVING, which no describe call can reach.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS TWO-PROFILE, which aws/INDEX.md admits only for a reason: PX-5 asks whether the
# address the perimeter NAMES is the address the estate actually leaves under, and those two
# facts live in two accounts by design - the permission sets are in Identity, the Elastic IP is
# in Production. One login covers both (they share the `awsds` sso-session).
#
# FOUR CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - the instance Name tag is awsds-<env>-proxy                     (6c step 4.8)
#   - the security group's name is awsds-<env>-proxy                 (6c step 4.1)
#   - the allow-list parameter is /datascience/<env>/proxy/allowlist (6c step 4.10)
#   - the deny statement's Sid is DenyControlPlaneOffVpn             (Stage 4 step 8.1)
#
# WHAT IT CANNOT SEE, stated because a clean run here is not a working proxy:
#   - WHETHER A REQUEST SUCCEEDS. Every check below reads configuration; the behavioural proof
#     is a request through the proxy from inside a spoke, which is 6c step 6.3's probe and its
#     four readings (no internet without the proxy; 403 to a private address; 200 to a name on
#     the plane; 403 to a name on none). A describe call proves none of them (Lesson 20).
#   - THE ALLOW-LIST'S CONTENT as a policy question. PX-3 asks whether the running list EQUALS
#     the committed one; whether the committed one is the right list is `./aws/dns-allowlist.py`
#     (DN-1..DN-4), which resolves every name on every plane. The chain is
#     code -> parameter -> host: DN-3 is the first link and PX-3 is the second, and neither one
#     alone says the proxy is enforcing what was written.
#   - WHAT THE HOST DID. That is the access log (4.11), which is where an unlisted hostname gets
#     NAMED - `docker pull` says only `Forbidden`. PX-4 checks the group exists; reading it is
#     `aws logs filter-log-events --filter-pattern DENIED`.

from __future__ import annotations

import json
import re
import sys
import time

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "proxy.txt"

PROXY_HOME_PROFILE = "awsds-infra-prod"
IDENTITY_PROFILE = "awsds-infra-identity"

NAME_TAG_PATTERN = "awsds-*-proxy"
PROXY_PORT = 3128
PARAMETER = "/datascience/prod/proxy/allowlist"
LOG_GROUP = "/awsds/prod/proxy"
DENY_SID = "DenyControlPlaneOffVpn"
INFRA_SET = "InfrastructureAccess"

# The committed configuration, read from this repository rather than from AWS. PX-2's default
# source: the ORDER of `http_access` lines is the security property, and it is decidable from the
# template without any session at all - which matters because the answer is most wanted BEFORE
# an apply, not after one.
TEMPLATE = ("terraform-live", "production", "proxy", "squid.conf.tftpl")


# --------------------------------------------------------------- the inside of the host
#
# THIS IS THE ONE PART OF THIS FILE THAT IS NOT READ-ONLY, WHICH IS WHY IT IS OPT-IN. Everything
# the commands below do ON the host is a read - cat, grep, systemctl is-active - but
# `ssm:SendCommand` is a WRITE API: it creates a Command, appears in CloudTrail as a mutating
# call, and executes code on an instance. `aws/*` is read-only so that anyone may run these
# scripts without thinking about it, so the escalation has to be typed.
#
# WHY IT EXISTS AT ALL: the parameter is [P] and readable with a plain GetParameter, but the
# FILE THE DAEMON IS SERVING is not. A State Manager association re-renders it every thirty
# minutes (4.10) and its silence is indistinguishable from success - which is exactly the shape
# PX-3 exists to break. Nothing else can see a host whose render failed and whose squid is still
# serving the previous list.
#
# `cat /etc/squid/squid.conf` CARRIES NO SECRET, and that is checked rather than assumed: the
# allow-lists are public names, there is no authentication configured, and the banned fragments
# below keep it that way if somebody ever adds one.
# TWO FILES, NOT ONE, AND THE SPLIT IS THE DESIGN RATHER THAN AN ACCIDENT (measured 2026-09-06,
# on the first --on-host run, which read `running 0 planes` from a host serving five). The main
# `squid.conf` is owned by Terraform because the ORDER of its `http_access` lines is the security
# property and a drop-in cannot express "before"; the PER-PLANE lists are a drop-in at
# `/etc/squid/conf.d/awsds-planes.conf`, rendered from the [P] parameter, because their content
# changes without their position doing so. PX-2 reads the first file and PX-3 the second, and a
# probe that read only one of them would have answered one question about the other's subject.
#
# THE `|| true` ON THE PLANES FILE IS NOT DEFENSIVE PADDING. Without it a host that has never
# rendered makes the whole invocation `Failed`, and SSM's status is what the report prints - so a
# missing drop-in would surface as "the command failed" rather than as "there are no planes on
# this host", which are different findings (Lesson 13).
HOST_PROBE_COMMANDS = (
    "echo ---SQUIDCONF---",
    "cat /etc/squid/squid.conf",
    "echo ---PLANES---",
    "cat /etc/squid/conf.d/awsds-planes.conf || true",
    "echo ---SERVICE---",
    "systemctl is-active squid",
)
HOST_PROBE_BANNED = ("passwd", "shadow", "private", ">", "rm ", "systemctl start", "systemctl stop")
HOST_PROBE_POLLS = 20
HOST_PROBE_INTERVAL_S = 5


def _assert_probe_commands_are_reads() -> None:
    """Refuse to send a command list that stopped being a read, before it is sent."""
    for cmd in HOST_PROBE_COMMANDS:
        for banned in HOST_PROBE_BANNED:
            if banned in cmd:
                note(f"REFUSING --on-host: {banned!r} appears in {cmd!r}")
                sys.exit(1)


def read_host(cli: AwsCli, instance_id: str, logerr) -> tuple:
    """Run HOST_PROBE_COMMANDS on one instance through SSM; return (status, output).

    Three failure states are distinguishable on purpose: ``(send failed)`` is usually an
    instance that is not SSM-managed yet, ``(still running)`` is a host that is up and not
    answering, and SSM's own ``Failed``/``TimedOut`` is a command that ran and did not work.
    """
    params = json.dumps({"commands": list(HOST_PROBE_COMMANDS)})
    res = cli.run(
        "ssm",
        "send-command",
        "--instance-ids",
        instance_id,
        "--document-name",
        "AWS-RunShellScript",
        "--parameters",
        params,
        "--query",
        "Command.CommandId",
        "--output",
        "text",
        log=False,
    )
    if not res.ok:
        logerr(PROXY_HOME_PROFILE, f"ssm send-command {instance_id}", res.stderr)
        return "(send failed)", ""
    command_id = res.stdout.strip()

    status, out, err = "(still running)", "", ""
    for _ in range(HOST_PROBE_POLLS):
        inv = cli.run(
            "ssm",
            "get-command-invocation",
            "--command-id",
            command_id,
            "--instance-id",
            instance_id,
            "--output",
            "json",
            log=False,
        )
        if inv.ok:
            doc = json.loads(inv.stdout or "{}")
            status = doc.get("Status", "?")
            out = doc.get("StandardOutputContent", "") or ""
            err = doc.get("StandardErrorContent", "") or ""
            if status not in ("Pending", "InProgress", "Delayed"):
                break
        time.sleep(HOST_PROBE_INTERVAL_S)
    text = out
    if err.strip():
        text += "\n--- stderr ---\n" + err
    return status, text


# --------------------------------------------------------------- the ordering question (PX-2)

_ACCESS = re.compile(r"^\s*http_access\s+(allow|deny)\s+(\S+)", re.M)


def access_order(config_text: str) -> list:
    """Every `http_access` line, in file order, as (action, acl name).

    ORDER IS THE SECURITY PROPERTY HERE AND NOT A STYLE. Squid evaluates `http_access` top to
    bottom and stops at the first match, so a single `allow` above the private-destination deny
    turns the proxy into an L7 bridge between VPCs that peering deliberately keeps apart - a
    peering nobody built, at layer 7 (Lesson 44). That is why the whole `squid.conf` is owned by
    Terraform rather than dropped into `conf.d/`: a drop-in cannot express "before".
    """
    return [(m.group(1), m.group(2)) for m in _ACCESS.finditer(config_text)]


def order_verdict(lines: list, deny_acl: str = "to_private") -> tuple:
    """(ok, detail) - is the private-destination deny above every allow?"""
    if not lines:
        return False, "no http_access line found at all - this is not a squid.conf"
    deny_at = next((i for i, (a, acl) in enumerate(lines) if a == "deny" and acl == deny_acl), None)
    if deny_at is None:
        return False, f"no `http_access deny {deny_acl}` line at all"
    allows_before = [f"{a} {acl}" for a, acl in lines[:deny_at] if a == "allow"]
    if allows_before:
        return False, f"{len(allows_before)} allow(s) precede it: {'; '.join(allows_before)}"
    last = lines[-1]
    tail = (
        ""
        if last == ("deny", "all")
        else f"; and the LAST line is `{last[0]} {last[1]}`, not `deny all`"
    )
    return (
        not tail
    ), f"`deny {deny_acl}` is line {deny_at + 1} of {len(lines)}, above every allow{tail}"


def host_section(text: str, marker: str) -> str:
    """One `echo ---X---` section of the host probe's output.

    THE TWO FILES MUST NOT BE CONCATENATED, and the first --on-host run showed why: read as one
    blob, the ordering check sees the drop-in's `http_access allow` lines AFTER `deny all` and
    reports a proxy that allows everything at the end. They are two files, evaluated by squid in
    the order the `include` sets, and the report has to keep them apart to say anything true
    about either.
    """
    start = text.find(f"---{marker}---")
    if start < 0:
        return ""
    start = text.index("\n", start) + 1
    nxt = re.search(r"^---[A-Z]+---$", text[start:], re.M)
    return text[start : start + nxt.start()] if nxt else text[start:]


def parse_allowlist(raw: str) -> dict:
    """The parameter's planes, or {} when it is not the JSON this design writes."""
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return {k: list(v.get("allow", [])) for k, v in doc.items() if isinstance(v, dict)}


def running_allowlist(config_text: str) -> dict:
    """The planes as the HOST spells them: `acl dst_<plane> dstdomain <names>`, in the drop-in.

    Matched on the acl NAME rather than on position, because the render script builds one acl
    per plane from the parameter's keys - so a plane that vanished from the parameter and stayed
    on the host is exactly what PX-3 is looking for, and it is only visible as a missing key.
    The name is `dst_<plane>` and the file is `/etc/squid/conf.d/awsds-planes.conf`; both are
    render-squid.sh's contract, and a rename there must fail loudly here.
    """
    out: dict = {}
    for m in re.finditer(r"^\s*acl\s+dst_(\S+)\s+dstdomain\s+(.+)$", config_text, re.M):
        out.setdefault(m.group(1), []).extend(m.group(2).split())
    return out


def plane_key(name: str) -> str:
    """One spelling for a plane, because the two sides use two.

    `render-squid.sh` builds its acl names with `gsub("-"; "_")`, so the parameter's
    `production-foundation` is the host's `dst_production_foundation`. Comparing the raw keys
    reports every plane as both missing and extra - which is what the first --on-host run did,
    and it is Lesson 53's shape at its smallest: two systems, one intent, and a spelling rule
    between them that nothing had written down.
    """
    return name.replace("-", "_")


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    on_host = "--on-host" in argv
    argv = [a for a in argv if a != "--on-host"]
    if on_host:
        _assert_probe_commands_are_reads()

    if argv:
        selected, source = profiles.select(argv)
    else:
        selected = [PROXY_HOME_PROFILE, IDENTITY_PROFILE]
        source = "the two profiles this file needs (the proxy's account and Identity)"

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    home_live = PROXY_HOME_PROFILE in live
    instances: list = []  # (id, type, state, subnet, public ip, sg ids)
    ingress: list = []  # (sg id, sg name, proto, from, to, cidr)
    addresses: list = []  # (allocation id, public ip, instance id or '-')
    committed: dict = {}
    param_raw = ""
    log_groups: list = []  # (name, retention)
    subscriptions: list = []  # (log group, filter name, destination)
    host_status, host_text = "(not requested)", ""

    if home_live:
        cli = cli_for(PROXY_HOME_PROFILE)

        res = cli.run(
            "ec2",
            "describe-instances",
            "--filters",
            f"Name=tag:Name,Values={NAME_TAG_PATTERN}",
            "Name=instance-state-name,Values=pending,running,stopping,stopped",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(PROXY_HOME_PROFILE, "ec2 describe-instances", res.stderr)
        else:
            for resv in json.loads(res.stdout or "{}").get("Reservations", []):
                for inst in resv.get("Instances", []):
                    instances.append(
                        (
                            inst.get("InstanceId", "?"),
                            inst.get("InstanceType", "?"),
                            (inst.get("State") or {}).get("Name", "?"),
                            inst.get("SubnetId", "?"),
                            inst.get("PublicIpAddress", "-"),
                            [g.get("GroupId") for g in inst.get("SecurityGroups", [])],
                        )
                    )

        res = cli.run(
            "ec2",
            "describe-security-groups",
            "--filters",
            f"Name=group-name,Values={NAME_TAG_PATTERN}",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(PROXY_HOME_PROFILE, "ec2 describe-security-groups", res.stderr)
        else:
            for g in json.loads(res.stdout or "{}").get("SecurityGroups", []):
                for perm in g.get("IpPermissions", []):
                    for rng in perm.get("IpRanges", []):
                        ingress.append(
                            (
                                g.get("GroupId", "?"),
                                g.get("GroupName", "?"),
                                perm.get("IpProtocol", "?"),
                                perm.get("FromPort", "-"),
                                perm.get("ToPort", "-"),
                                rng.get("CidrIp", "?"),
                            )
                        )

        res = cli.run("ec2", "describe-addresses", "--output", "json", log=False)
        if not res.ok:
            logerr(PROXY_HOME_PROFILE, "ec2 describe-addresses", res.stderr)
        else:
            for a in json.loads(res.stdout or "{}").get("Addresses", []):
                addresses.append(
                    (
                        a.get("AllocationId", "?"),
                        a.get("PublicIp", "?"),
                        a.get("InstanceId", "-"),
                    )
                )

        res = cli.run(
            "ssm",
            "get-parameter",
            "--name",
            PARAMETER,
            "--query",
            "Parameter.Value",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(PROXY_HOME_PROFILE, f"ssm get-parameter {PARAMETER}", res.stderr)
        else:
            param_raw = res.stdout.strip()
            committed = parse_allowlist(param_raw)

        res = cli.run(
            "logs",
            "describe-log-groups",
            "--log-group-name-prefix",
            LOG_GROUP,
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(PROXY_HOME_PROFILE, "logs describe-log-groups", res.stderr)
        else:
            for g in json.loads(res.stdout or "{}").get("logGroups", []):
                log_groups.append((g.get("logGroupName", "?"), g.get("retentionInDays", "never")))
                sub = cli.run(
                    "logs",
                    "describe-subscription-filters",
                    "--log-group-name",
                    g.get("logGroupName", ""),
                    "--output",
                    "json",
                    log=False,
                )
                if sub.ok:
                    for f in json.loads(sub.stdout or "{}").get("subscriptionFilters", []):
                        subscriptions.append(
                            (
                                g.get("logGroupName", "?"),
                                f.get("filterName", "?"),
                                f.get("destinationArn", "?"),
                            )
                        )

        if on_host and instances:
            running = [i for i in instances if i[2] == "running"]
            if not running:
                host_status = "(host not running)"
            else:
                host_status, host_text = read_host(cli, running[0][0], logerr)
        elif on_host:
            host_status = "(no host found)"

    # ------------------------------------------------------- Identity: which sets name the address
    deny_addresses: dict = {}  # permission set name -> [addresses in the deny]
    identity_live = IDENTITY_PROFILE in live
    if identity_live:
        cli = cli_for(IDENTITY_PROFILE)
        res = cli.run("sso-admin", "list-instances", "--output", "json", log=False)
        arn = ""
        if res.ok:
            insts = json.loads(res.stdout or "{}").get("Instances", [])
            arn = insts[0].get("InstanceArn", "") if insts else ""
        else:
            logerr(IDENTITY_PROFILE, "sso-admin list-instances", res.stderr)
        if arn:
            res = cli.run(
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                arn,
                "--query",
                "PermissionSets",
                "--output",
                "text",
                log=False,
            )
            for ps in res.stdout.split() if res.ok else []:
                name = cli.run(
                    "sso-admin",
                    "describe-permission-set",
                    "--instance-arn",
                    arn,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "PermissionSet.Name",
                    "--output",
                    "text",
                    log=False,
                )
                inline = cli.run(
                    "sso-admin",
                    "get-inline-policy-for-permission-set",
                    "--instance-arn",
                    arn,
                    "--permission-set-arn",
                    ps,
                    "--output",
                    "text",
                    log=False,
                )
                if not (name.ok and inline.ok):
                    continue
                doc = inline.stdout or ""
                if DENY_SID not in doc:
                    continue
                deny_addresses[name.stdout.strip()] = sorted(
                    set(re.findall(r"\b(\d{1,3}(?:\.\d{1,3}){3})/32\b", doc))
                )

    # ------------------------------------------------------------------------------ the report
    template_path = ctx.repo_root.joinpath(*TEMPLATE)
    template_text = template_path.read_text(encoding="utf-8") if template_path.is_file() else ""

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        rep.banner("proxy - the estate's single internet exit, and whether it is the one committed")
        rep.text(f"""generated : {context.utc_stamp()}
region    : {context.REGION}
profiles  : {source}
parameter : {PARAMETER}
log group : {LOG_GROUP}
on-host   : {"yes - ssm:SendCommand was used (a WRITE API carrying only reads)" if on_host else "no (--on-host)"}

D38 gives this estate ONE way out. Everything below reads CONFIGURATION; whether a request
actually succeeds is 6c step 6.3's probe, whose four readings are the behavioural proof.
""")

        rep.h1("1. The host and its [P] anchors")
        rep.tabulate(
            ["INSTANCE\tTYPE\tSTATE\tSUBNET\tPUBLIC IP\tSECURITY GROUPS"]
            + [f"{i}\t{t}\t{s}\t{sn}\t{ip}\t{','.join(g)}" for i, t, s, sn, ip, g in instances]
            or [
                "INSTANCE\tTYPE\tSTATE\tSUBNET\tPUBLIC IP\tSECURITY GROUPS",
                "none found\t-\t-\t-\t-\t-",
            ]
        )
        rep.h2("Elastic IPs in this account")
        rep.tabulate(
            ["ALLOCATION\tADDRESS\tATTACHED TO"] + [f"{a}\t{p}\t{i}" for a, p, i in addresses]
        )

        rep.h1("2. Who may reach 3128 (PX-1)")
        rep.text(
            "The group is the [P] half of the perimeter: it decides WHO may open a connection,\n"
            "and the allow-list decides what they may then REACH. A rule here for a source with no\n"
            "plane is reachable and mute - the failure that looks like a network fault.\n"
        )
        rep.tabulate(
            ["GROUP\tNAME\tPROTO\tFROM\tTO\tSOURCE"]
            + [f"{g}\t{n}\t{pr}\t{f}\t{t}\t{c}" for g, n, pr, f, t, c in ingress]
            or ["GROUP\tNAME\tPROTO\tFROM\tTO\tSOURCE", "no ingress rule found\t-\t-\t-\t-\t-"]
        )

        rep.h1("3. The rule ORDER (PX-2)")
        rep.text(
            "Squid evaluates `http_access` top to bottom and stops at the first match, so one\n"
            "`allow` above the private-destination deny turns this host into an L7 bridge between\n"
            "VPCs that peering deliberately keeps apart. That is why the whole squid.conf is owned\n"
            "by Terraform rather than dropped into conf.d/ - a drop-in cannot express `before`.\n"
        )
        running_conf = host_section(host_text, "SQUIDCONF") if on_host else ""
        planes_conf = host_section(host_text, "PLANES") if on_host else ""
        for label, text in (
            ("the COMMITTED template", template_text),
            ("the RUNNING squid.conf", running_conf),
        ):
            rep.h2(label)
            if not text:
                rep.text(
                    "  not read - "
                    + (
                        "--on-host was not given"
                        if "RUNNING" in label
                        else f"no template at {'/'.join(TEMPLATE)}"
                    )
                    + "\n"
                )
                continue
            lines = access_order(text)
            rep.tabulate(
                ["#\tACTION\tACL"] + [f"{i + 1}\t{a}\t{acl}" for i, (a, acl) in enumerate(lines)]
            )
            ok, detail = order_verdict(lines)
            rep.text(f"\n  {'ok' if ok else 'PROBLEM'}: {detail}\n")

        rep.h1("4. The allow-list: committed against running (PX-3)")
        rep.text(
            "The chain is code -> parameter -> host. `./aws/dns-allowlist.py` DN-3 compares the\n"
            "repository with the parameter; this compares the PARAMETER with the file the daemon is\n"
            "serving. A State Manager association re-renders every thirty minutes and its silence is\n"
            "indistinguishable from success, which is the whole reason this check exists.\n"
        )
        rep.h2(f"committed - {PARAMETER}")
        rep.tabulate(
            ["PLANE\tENTRIES"] + [f"{k}\t{len(v)}" for k, v in sorted(committed.items())]
            or ["PLANE\tENTRIES", "not read\t-"]
        )
        running = running_allowlist(planes_conf) if on_host else {}
        rep.h2("running - the host's own squid.conf")
        if not on_host:
            rep.text("  not read - --on-host was not given\n")
        else:
            rep.tabulate(
                ["PLANE\tENTRIES"] + [f"{k}\t{len(v)}" for k, v in sorted(running.items())]
                or ["PLANE\tENTRIES", f"none parsed (ssm status: {host_status})\t-"]
            )

        rep.h1("5. The access log (PX-4)")
        rep.tabulate(
            ["LOG GROUP\tRETENTION (days)"] + [f"{n}\t{r}" for n, r in log_groups]
            or ["LOG GROUP\tRETENTION (days)", "none found\t-"]
        )
        rep.h2("export to Log Archive")
        rep.tabulate(
            ["LOG GROUP\tFILTER\tDESTINATION"] + [f"{g}\t{f}\t{d}" for g, f, d in subscriptions]
            or ["LOG GROUP\tFILTER\tDESTINATION", "none\t-\t-"]
        )

        rep.h1("6. Which permission sets name an address (PX-5)")
        rep.tabulate(
            ["PERMISSION SET\tADDRESSES IN " + DENY_SID]
            + [f"{k}\t{', '.join(v) or '(none)'}" for k, v in sorted(deny_addresses.items())]
            or ["PERMISSION SET\tADDRESSES IN " + DENY_SID, "not read\t-"]
        )

        # ------------------------------------------------------------------------ the checks
        rep.h1("7. Checks")

        rules = [r for r in ingress if r[2] == "tcp" and r[3] == PROXY_PORT and r[4] == PROXY_PORT]
        others = [r for r in ingress if r not in rules]
        world = [r for r in rules if r[5] in ("0.0.0.0/0", "::/0")]
        if not ingress:
            checks.note(
                "PX-1",
                f"only the spokes and the tunnel may reach {PROXY_PORT}",
                "no ingress rule read - the group is absent or the call failed",
            )
        elif world or others:
            checks.fail(
                "PX-1",
                f"only the spokes and the tunnel may reach {PROXY_PORT}",
                (f"{len(world)} world-open rule(s); " if world else "")
                + (
                    f"{len(others)} rule(s) on another port/protocol: "
                    f"{'; '.join(f'{r[2]} {r[3]}-{r[4]} from {r[5]}' for r in others)}"
                    if others
                    else ""
                ),
            )
        else:
            checks.ok(
                "PX-1",
                f"only the spokes and the tunnel may reach {PROXY_PORT}",
                f"{len(rules)} rule(s), all TCP/{PROXY_PORT} from private ranges: "
                + ", ".join(sorted(r[5] for r in rules)),
            )

        if not template_text:
            checks.note(
                "PX-2",
                "no http_access allow precedes the private-destination deny",
                "the committed template was not readable from this checkout",
            )
        else:
            ok, detail = order_verdict(access_order(template_text))
            detail = f"committed: {detail}"
            # BOTH SOURCES COUNT. The first version decided the verdict from the committed
            # template alone and merely PRINTED the running one, which would have reported
            # `pass` for a host serving a file nobody committed - a check that reads its own
            # subject and then does not use it.
            if on_host and running_conf:
                run_ok, run_detail = order_verdict(access_order(running_conf))
                ok = ok and run_ok
                detail += f"; running: {run_detail}"
            elif on_host:
                detail += "; the RUNNING file could not be read (see the ssm status above)"
            else:
                detail += "; the RUNNING file is not read without --on-host"
            (checks.ok if ok else checks.fail)(
                "PX-2", "no http_access allow precedes the private-destination deny", detail
            )

        if not on_host:
            checks.note(
                "PX-3",
                "the running allow-list equals the committed one",
                "not answered - re-run with --on-host (ssm:SendCommand, a WRITE API "
                "carrying only reads). DN-3 in ./aws/dns-allowlist.py is the OTHER link "
                "of the chain and needs no write at all",
            )
        elif not committed or not running:
            checks.fail(
                "PX-3",
                "the running allow-list equals the committed one",
                f"one side is empty - committed {len(committed)} plane(s), running "
                f"{len(running)} (ssm status: {host_status})",
            )
        else:
            diffs = []
            want_by = {plane_key(k): v for k, v in committed.items()}
            got_by = {plane_key(k): v for k, v in running.items()}
            for plane in sorted(set(want_by) | set(got_by)):
                want = [d.strip() for d in want_by.get(plane, [])]
                got = [d.strip() for d in got_by.get(plane, [])]
                if sorted(want) != sorted(got):
                    diffs.append(
                        f"{plane}: only committed {sorted(set(want) - set(got)) or '-'}, "
                        f"only running {sorted(set(got) - set(want)) or '-'}"
                    )
            (checks.fail if diffs else checks.ok)(
                "PX-3",
                "the running allow-list equals the committed one",
                "; ".join(diffs)
                if diffs
                else f"{len(committed)} planes, entry for entry - the render is current",
            )

        if not log_groups:
            checks.fail(
                "PX-4",
                "the access log group exists, with its Log Archive export",
                f"no log group named {LOG_GROUP} - 4.11's evidence is not being written",
            )
        elif not subscriptions:
            # NOT A FAIL, AND THE REASON IS DATED: 4.11's second half is an OPEN DECISION (the
            # stage's decision due #4) between a subscription filter into a Firehose in Log
            # Archive and a scheduled CreateExportTask to S3. They have different cost shapes,
            # and picking one silently would be an estimate standing in for a measurement
            # (Lesson 6). A `fail` here would report a gap the plan is holding open on purpose.
            checks.note(
                "PX-4",
                "the access log group exists, with its Log Archive export",
                f"{log_groups[0][0]} exists ({log_groups[0][1]} days) and has NO export - "
                "4.11's second half is an open decision (6c decision due #4), not drift. "
                "Until it lands, the author of the allow-list also owns its record "
                "(Lesson 18)",
            )
        else:
            checks.ok(
                "PX-4",
                "the access log group exists, with its Log Archive export",
                f"{log_groups[0][0]} -> " + ", ".join(d for _, _, d in subscriptions),
            )

        proxy_ips = {p for _, p, i in addresses if i != "-" and any(i == x[0] for x in instances)}
        if not deny_addresses:
            checks.note(
                "PX-5",
                "the perimeter names the address the estate leaves under",
                "no permission set carrying the deny was read (Identity profile absent?)",
            )
        elif not proxy_ips:
            checks.note(
                "PX-5",
                "the perimeter names the address the estate leaves under",
                "the proxy's Elastic IP could not be read, so there is nothing to compare",
            )
        else:
            missing = {
                s: sorted(proxy_ips - set(a))
                for s, a in deny_addresses.items()
                if s != INFRA_SET and (proxy_ips - set(a))
            }
            if missing:
                checks.fail(
                    "PX-5",
                    "the perimeter names the address the estate leaves under",
                    "; ".join(f"{s} does not name {', '.join(v)}" for s, v in missing.items()),
                )
            else:
                checks.ok(
                    "PX-5",
                    "the perimeter names the address the estate leaves under",
                    f"{', '.join(sorted(proxy_ips))} appears in {DENY_SID} on "
                    f"{len([s for s in deny_addresses if s != INFRA_SET])} persona set(s); "
                    f"{INFRA_SET} is exempt by decision (open question 17's recovery path)",
                )

        rep.checks_table(checks)
        rep.text("""
PX-1 and PX-2 are the two halves of one sentence: WHO may connect, and WHAT they may then
reach. Either alone is a control with a hole - a group that admits a spoke whose plane is
empty is reachable and mute, and an allow-list in front of a group that admits the world is
a filter anybody may ask to be applied to them.

PX-3 IS THE SECOND OF TWO LINKS. DN-3 in ./aws/dns-allowlist.py compares the repository with
the parameter and needs no write API; this compares the parameter with the file the daemon is
serving, and needs one. A green DN-3 with no PX-3 says what was written reached the parameter
and nothing about what the proxy is enforcing.

A clean run here is not a working proxy. The behavioural proof is 6c step 6.3's probe: no
internet without the proxy, 403 to a private address through it, 200 to a name on the plane,
403 to a name on none. Four readings, four different ways to be wrong.
""")

        rep.h1("8. Calls that failed")
        failed_calls_epilogue(rep, errors)

    note(f"\nwrote {out_label}")
    print(open(out_path, encoding="utf-8").read())
    if errors.entries and checks.n_fail() == 0:
        return 1
    return 2 if checks.n_fail() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
