#!/usr/bin/env -S uv run --quiet
# orchestration.py - Stage 10's evidence: the MWAA Serverless workflows in Staging and
# Production (D7 amended: one orchestrator; D41's chain layer above them is OR-9 once built),
# with their per-workflow roles (boundary, trust, the D13 absences), their NetworkConfiguration
# (present, two AZs, no default route), the named log groups with retention (D28 item 5), the
# failure rules and the model-approval rule, recent runs (the schedule evidence), the absence of
# any provisioned MWAA environment, the definitions home, and the registry's register/approve
# record (INT-07's registry half, consumed).
#
#   needs:    a live SSO session, and nothing else:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/orchestration.py                       # every awsds-* profile
#             ./aws/orchestration.py awsds-infra-staging   # only the ones named
#             python3 aws/orchestration.py -               # CloudShell, ambient credentials
#   writes:   aws/output/orchestration.txt   (untracked - see .gitignore)
#   reads:    mwaa-serverless:ListWorkflows, GetWorkflow, ListWorkflowVersions,
#             ListWorkflowRuns, GetWorkflowRun; mwaa:ListEnvironments; ec2:DescribeSubnets,
#             DescribeRouteTables; logs:DescribeLogGroups; events:ListRules; iam:GetRole,
#             ListRoles, ListRolePolicies, GetRolePolicy; s3:ListObjectsV2;
#             datazone:ListDomains, ListEnvironmentBlueprintConfigurations,
#             GetEnvironmentBlueprint (from each Sandbox); cloudtrail:LookupEvents;
#             sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# The subject spans accounts, so this script is multi-profile: the workflow is authored in a
# Sandbox project and runs in Staging, then Production (one module, two slices, Staging applied
# first), and the provisioned-MWAA reading (OR-6) is only meaningful measured in every account,
# since the OnDemand Workflows blueprint would create a fee-bearing environment in a member
# account. Section 1 prints the caller ARN of every profile.
#
# The contracts it reads, each named in the stage file so a rename fails loudly:
#   - workflows, their roles and their failure rules carry awsds-<env>-wf- (steps 1.1, 1.3, 3.1)
#   - log groups: /awsds/<env>/wf/ (step 1.1)
#   - the definitions home is s3://awsds-prod-outputs/workflows/, with the object's S3
#     VersionId pinned (steps 1.1, 2.4, decision 1)
#   - the approval rule is awsds-prod-model-approval (step 5.3)
#   - the chain layer carries awsds-<env>-chain- (steps 3.4, 3.5; OR-9, not written)
#   - the lake buckets carry awsds-data- (Stage 5a), so OR-3 can read D13's absence
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - Sandbox's portal-authored workflows. The Studio surface has no switch to read (6d step
#     4.1), and what it creates bills task-hours in Sandbox, outside these contracts.
#   - The behavioural proofs (an unattended scheduled run, the failure rules firing, the
#     lint rejecting a bad artifact) are the stage's own (Lesson 20).
#   - Whether the awscc apply lands under the deploy role's boundary (INT-14) is pass 2's
#     pipeline run; this file only shows what exists afterwards.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "orchestration.txt"

# Where each half lives (D14, D17, D20, D35). The workflow is one design in two accounts; the
# env token is the one its resource names carry. Blueprint configurations are applied, and
# listed, from the member accounts: the domain account lists none (measured 2026-10-10).
ORCH_ENVS = (("staging", "awsds-infra-staging"), ("prod", "awsds-infra-prod"))
PROD_PROFILE = "awsds-infra-prod"
SANDBOX_PREFIX = "awsds-infra-sandbox-"

# The contracts (see header).
AUTO_LOG_PREFIX = "/aws/mwaa-serverless/"
APPROVAL_RULE = "awsds-prod-model-approval"
DEF_BUCKET = "awsds-prod-outputs"
DEF_PREFIX = "workflows/"
LAKE_FRAG = "awsds-data-"
WF_PRINCIPAL = "airflow-serverless.amazonaws.com"
SLR_NAME = "AWSServiceRoleForAmazonMWAAServerless"
MIN_AZS = 2  # the private-routing shape's documented minimum (step 1.2)
VERSION_QUOTA = 50  # versions per workflow; no prune API is documented (risk 4)
VERSION_WARN = 40
LOOKUP_MAX = 50  # CloudTrail lookup page - registry writes are rare at lab scale
RUNS_MAX = 10  # recent runs per workflow

# The fields of an EC2 route that name its target, in the order a default route is reported.
ROUTE_TARGETS = (
    "GatewayId",
    "NatGatewayId",
    "EgressOnlyInternetGatewayId",
    "TransitGatewayId",
    "VpcPeeringConnectionId",
    "NetworkInterfaceId",
    "InstanceId",
    "CarrierGatewayId",
    "LocalGatewayId",
    "CoreNetworkArn",
)


def wf_frag(env: str) -> str:
    return f"awsds-{env}-wf-"


def log_prefix(env: str) -> str:
    return f"/awsds/{env}/wf/"


def _stmts(doc: dict) -> list:
    stmts = (doc or {}).get("Statement", [])
    return [stmts] if isinstance(stmts, dict) else list(stmts)


def _as_list(x) -> list:
    if x is None:
        return []
    return [x] if isinstance(x, str) else list(x)


def _json(res, default):
    """The parsed output of a call that answered, else ``default``."""
    if res.ok and not res.tolerated and res.stdout and res.stdout.strip() not in ("null", "None"):
        return json.loads(res.stdout)
    return default


def read_network(cli: AwsCli, subnet_ids: list) -> dict:
    """A workflow's subnets as the private-routing shape reads them (step 1.2).

    Returns ``rows`` (subnet, AZ id, Name tag, route table), ``zones`` (the AZ ids spanned),
    ``defaults`` (every 0.0.0.0/0 or ::/0 route in those tables, as subnet and target) and
    ``ok`` (whether every read answered). A subnet with no explicit association follows its
    VPC's main table, which a per-subnet association filter would never return.
    """
    out = {"rows": [], "zones": set(), "defaults": [], "ok": True}
    if not subnet_ids:
        return out
    res = cli.run(
        "ec2",
        "describe-subnets",
        "--subnet-ids",
        *subnet_ids,
        "--query",
        "Subnets[].[SubnetId,VpcId,AvailabilityZoneId,Tags[?Key=='Name']|[0].Value]",
        "--output",
        "json",
    )
    subnets = _json(res, None)
    if subnets is None:
        out["ok"] = False
        return out
    tables: list = []  # (vpc, route table)
    for vpc in sorted({str(s[1]) for s in subnets}):
        rt = cli.run(
            "ec2",
            "describe-route-tables",
            "--filters",
            f"Name=vpc-id,Values={vpc}",
            "--query",
            "RouteTables[].{id:RouteTableId,assoc:Associations,routes:Routes}",
            "--output",
            "json",
        )
        found = _json(rt, None)
        if found is None:
            out["ok"] = False
            return out
        tables += [(vpc, t) for t in found]

    def table_of(subnet: str, vpc: str) -> dict:
        mine = [t for v, t in tables if v == vpc]
        for t in mine:
            if any(a.get("SubnetId") == subnet for a in t.get("assoc") or []):
                return t
        for t in mine:
            if any(a.get("Main") for a in t.get("assoc") or []):
                return t
        return {}

    for sid, vpc, zone, name in subnets:
        table = table_of(str(sid), str(vpc))
        out["zones"].add(str(zone))
        out["rows"].append(
            (str(sid), str(zone), str(name or "-"), str(table.get("id") or "(none)"))
        )
        for r in table.get("routes") or []:
            if (
                r.get("DestinationCidrBlock") == "0.0.0.0/0"
                or r.get("DestinationIpv6CidrBlock") == "::/0"
            ):
                target = next((str(r[k]) for k in ROUTE_TARGETS if r.get(k)), "(no target)")
                out["defaults"].append((str(sid), target))
    return out


def read_workflows(cli: AwsCli, frag: str, logerr) -> dict:
    """Every workflow whose name carries ``frag``: name -> what Stage 10 reads of it.

    ``logerr(what, err)`` records a failed read, so a field missing because its call failed
    is never reported as a field the workflow lacks.
    """
    res = cli.run(
        "mwaa-serverless",
        "list-workflows",
        "--query",
        "Workflows[].[Name,WorkflowArn,WorkflowStatus,TriggerMode]",
        "--output",
        "json",
        log=False,
        tolerate="AccessDenied|UnknownOperation|UnrecognizedClient",
    )
    if not res.ok:
        logerr("mwaa-serverless list-workflows", res.stderr)
        return {}
    found: dict = {}
    for name, arn, status, tmode in _json(res, []):
        if frag not in str(name):
            continue
        d = {
            "arn": str(arn),
            "status": str(status),
            "trigger": str(tmode),
            "cron": "-",
            "role": "",
            "log_group": "",
            "subnets": [],
            "sgs": [],
            "def_bucket": "",
            "def_key": "",
            "def_version": "",
            "encryption": "-",
            "versions": "?",
            "runs": [],
        }
        r = cli.run(
            "mwaa-serverless",
            "get-workflow",
            "--workflow-arn",
            arn,
            "--query",
            "[RoleArn,LoggingConfiguration.LogGroupName,"
            "NetworkConfiguration.SubnetIds,NetworkConfiguration.SecurityGroupIds,"
            "DefinitionS3Location.Bucket,DefinitionS3Location.ObjectKey,"
            "DefinitionS3Location.VersionId,ScheduleConfiguration.CronExpression,"
            "EncryptionConfiguration.Type]",
            "--output",
            "json",
            log=False,
        )
        if r.ok and r.stdout:
            role, log_group, subnets, sgs, bucket, key, version, cron, enc = json.loads(r.stdout)
            d.update(
                role=str(role or ""),
                log_group=str(log_group or ""),
                subnets=_as_list(subnets),
                sgs=_as_list(sgs),
                def_bucket=str(bucket or ""),
                def_key=str(key or ""),
                def_version=str(version or ""),
                cron=str(cron or "-"),
                encryption=str(enc or "-"),
            )
        else:
            logerr(f"mwaa-serverless get-workflow ({name})", r.stderr)
        v = cli.run(
            "mwaa-serverless",
            "list-workflow-versions",
            "--workflow-arn",
            arn,
            "--query",
            "length(WorkflowVersions)",
            "--output",
            "text",
        )
        d["versions"] = v.stdout.strip() if v.ok else "?"
        # list-workflow-runs returns RunType null for every run (measured 2026-10-10), so the
        # type comes from get-workflow-run, one call per run.
        runs = cli.run(
            "mwaa-serverless",
            "list-workflow-runs",
            "--workflow-arn",
            arn,
            "--max-results",
            str(RUNS_MAX),
            "--query",
            "WorkflowRuns[].[RunId,RunDetailSummary.Status,RunDetailSummary.StartedAt]",
            "--output",
            "json",
        )
        for rid, rstatus, started in _json(runs, [])[:RUNS_MAX]:
            t = cli.run(
                "mwaa-serverless",
                "get-workflow-run",
                "--workflow-arn",
                arn,
                "--run-id",
                rid,
                "--query",
                "RunType",
                "--output",
                "text",
            )
            rtype = t.stdout.strip() if t.ok and t.stdout.strip() != "None" else "?"
            d["runs"].append((str(rid), rtype, str(rstatus), str(started or "-")[:19]))
        d["net"] = read_network(cli, d["subnets"])
        found[str(name)] = d
    return found


def read_roles(cli: AwsCli, frag: str) -> tuple:
    """The execution roles whose names carry ``frag``: ``(rows, bad)``.

    A row is (role, boundary tail, trusted services); a bad entry is (role, what is wrong).
    The contract (step 1.3): trust in the service principal alone, a permissions boundary, and
    no data reach - the orchestrator starts jobs, awsds-<env>-job-exec touches data (D13 one
    level up).
    """
    rows: list = []
    bad: list = []
    res = cli.run(
        "iam",
        "list-roles",
        "--query",
        f"Roles[?contains(RoleName, '{frag}')].RoleName",
        "--output",
        "json",
        log=False,
    )
    for role in _json(res, []):
        role = str(role)
        r = cli.run(
            "iam",
            "get-role",
            "--role-name",
            role,
            "--query",
            "Role.[PermissionsBoundary.PermissionsBoundaryArn,AssumeRolePolicyDocument]",
            "--output",
            "json",
            log=False,
        )
        if not (r.ok and r.stdout):
            rows.append((role, "(read failed)", "-"))
            continue
        boundary, trust = json.loads(r.stdout)
        services: list = []
        for st in _stmts(trust):
            services += _as_list((st.get("Principal", {}) or {}).get("Service"))
            if (st.get("Principal", {}) or {}).get("AWS"):
                bad.append((role, "an AWS principal in a service-role trust policy"))
        if set(services) != {WF_PRINCIPAL}:
            named = " ".join(sorted(set(services))) or "no service"
            bad.append((role, f"trust names {named}, not {WF_PRINCIPAL} alone (step 1.3)"))
        if not boundary:
            bad.append((role, "no permissions boundary (Stage 8 4.1's condition)"))
        pol = cli.run(
            "iam",
            "list-role-policies",
            "--role-name",
            role,
            "--query",
            "PolicyNames",
            "--output",
            "json",
            log=False,
        )
        for pname in _json(pol, []):
            pr = cli.run(
                "iam",
                "get-role-policy",
                "--role-name",
                role,
                "--policy-name",
                pname,
                "--query",
                "PolicyDocument",
                "--output",
                "json",
                log=False,
            )
            for st in _stmts(_json(pr, {})):
                if str(st.get("Effect", "")) != "Allow":
                    continue
                actions = " ".join(_as_list(st.get("Action"))).lower()
                resources = " ".join(map(str, _as_list(st.get("Resource"))))
                if "lakeformation:getdataaccess" in actions:
                    bad.append((role, f"lakeformation:GetDataAccess in {pname}"))
                if "s3:" in actions and LAKE_FRAG in resources:
                    bad.append((role, f"an s3 allow naming {LAKE_FRAG}* in {pname}"))
        btail = str(boundary).rsplit("/", 1)[-1] if boundary else "(none)"
        rows.append((role, btail, " ".join(sorted(set(services))) or "(none)"))
    return rows, bad


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    measured = [(env, p) for env, p in ORCH_ENVS if p in live]
    prod_live = PROD_PROFILE in live

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------- the serverless workflows (Staging, Production)
    workflows: dict = {}  # env -> {name -> detail}
    for env, p in measured:
        note(f"measuring {p} (serverless workflows) ...")
        workflows[env] = read_workflows(
            cli_for(p), wf_frag(env), lambda what, err, p=p: logerr(p, what, err)
        )

    # -------------------- the per-workflow roles: boundary, trust, the D13 absences
    role_rows: list = []  # (env, role, boundary tail, trusted services)
    role_bad: list = []  # (env, role, what)
    for env, p in measured:
        rows, bad = read_roles(cli_for(p), wf_frag(env))
        role_rows += [(env, *r) for r in rows]
        role_bad += [(env, *b) for b in bad]

    # ------------------------------------------ log groups and retention (D28 item 5)
    lg_rows: list = []  # (env, log group, retention)
    for env, p in measured:
        cli = cli_for(p)
        for prefix in (log_prefix(env), AUTO_LOG_PREFIX):
            res = cli.run(
                "logs",
                "describe-log-groups",
                "--log-group-name-prefix",
                prefix,
                "--query",
                "logGroups[].[logGroupName,retentionInDays]",
                "--output",
                "json",
                log=False,
            )
            for gname, days in _json(res, []):
                lg_rows.append((env, str(gname), str(days) if days else "(never expires)"))

    # ------------------------------ the EventBridge rules: failures + model approval
    rule_rows: list = []  # (env, rule, state)
    for env, p in measured:
        res = cli_for(p).run(
            "events",
            "list-rules",
            "--query",
            "Rules[].[Name,State]",
            "--output",
            "json",
            log=False,
        )
        for rname, state in _json(res, []):
            if wf_frag(env) in str(rname) or (env == "prod" and str(rname) == APPROVAL_RULE):
                rule_rows.append((env, str(rname), str(state)))

    # ----------------- provisioned MWAA environments - the absence reading (every account)
    env_rows: list = []  # (profile, environment name)
    env_unread: list = []  # profiles whose listing did not answer
    for p in live:
        note(f"measuring {p} (provisioned MWAA environments) ...")
        res = cli_for(p).run(
            "mwaa",
            "list-environments",
            "--query",
            "Environments",
            "--output",
            "json",
            log=False,
            tolerate="AccessDenied|explicit deny",
        )
        if res.tolerated or not res.ok:
            if not res.ok:
                logerr(p, "mwaa list-environments", res.stderr)
            env_unread.append(p)
            continue
        for name in _json(res, []):
            env_rows.append((p, str(name)))

    # ------------------------- the service-linked role (Lesson 17 - the 0.3/1.6 pair)
    slr_rows: list = []  # (env, state)
    for env, p in measured:
        res = cli_for(p).run(
            "iam",
            "get-role",
            "--role-name",
            SLR_NAME,
            "--query",
            "Role.CreateDate",
            "--output",
            "text",
            log=False,
            tolerate="NoSuchEntity",
        )
        if res.tolerated:
            state = "absent (the pre-CreateWorkflow baseline - step 0.3)"
        elif res.ok:
            state = f"present, created {res.stdout.strip()[:19]}"
        else:
            state = "(read failed)"
        slr_rows.append((env, state))

    # --------------------------------------- the definitions home (step 2.4, decision 1)
    def_rows: list = []  # (key, size)
    if prod_live:
        res = cli_for(PROD_PROFILE).run(
            "s3api",
            "list-objects-v2",
            "--bucket",
            DEF_BUCKET,
            "--prefix",
            DEF_PREFIX,
            "--max-keys",
            "10",
            "--query",
            "Contents[].[Key,Size]",
            "--output",
            "json",
            log=False,
            tolerate="NoSuchBucket|AccessDenied",
        )
        def_rows = [(str(k), str(s)) for k, s in _json(res, [])]

    # -------------- the registry record: who registered, who approved (INT-07's registry half)
    reg_rows: list = []  # (time, event, caller tail)
    reg_bad: list = []  # (event, caller)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (registry events) ...")
        for ev_name in ("CreateModelPackage", "UpdateModelPackage"):
            res = cli.run(
                "cloudtrail",
                "lookup-events",
                "--lookup-attributes",
                f"AttributeKey=EventName,AttributeValue={ev_name}",
                "--max-results",
                str(LOOKUP_MAX),
                "--query",
                "Events[].CloudTrailEvent",
                "--output",
                "json",
                log=False,
            )
            for raw in _json(res, []):
                try:
                    ev = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                caller = str((ev.get("userIdentity") or {}).get("arn") or "(unknown)")
                when = str(ev.get("eventTime") or "-")
                reg_rows.append((when, ev_name, caller.rsplit("/", 1)[-1][:40]))
                if "awsds-deploy-prod" not in caller:
                    reg_bad.append((ev_name, caller))

    # ----------------- the blueprint configurations, read where they live (each Sandbox)
    bp_rows: list = []  # (profile, blueprint name, enabled regions)
    for p in [q for q in live if q.startswith(SANDBOX_PREFIX)]:
        cli = cli_for(p)
        note(f"measuring {p} (blueprint configurations) ...")
        res = cli.run(
            "datazone",
            "list-domains",
            "--query",
            "items[?domainVersion=='V2'].id | [0]",
            "--output",
            "text",
            log=False,
        )
        domain_id = res.stdout.strip() if res.ok and res.stdout.strip() != "None" else ""
        if domain_id:
            res = cli.run(
                "datazone",
                "list-environment-blueprint-configurations",
                "--domain-identifier",
                domain_id,
                "--output",
                "json",
                log=False,
            )
            for c in _json(res, {}).get("items", []):
                bpid = c.get("environmentBlueprintId", "?")
                r = cli.run(
                    "datazone",
                    "get-environment-blueprint",
                    "--domain-identifier",
                    domain_id,
                    "--identifier",
                    bpid,
                    "--query",
                    "name",
                    "--output",
                    "text",
                    log=False,
                )
                name = r.stdout.strip() if r.ok else str(bpid)
                bp_rows.append((p, name, " ".join(c.get("enabledRegions", []) or ["-"])))

    # -------------------------------------------------------------------------- the checks

    # OR-1: each account's workflows exist and rest READY; an absence is a note before pass 2.
    for env, _p in measured:
        if not workflows[env]:
            checks.note(
                "OR-1",
                f"{env}: the workflows",
                f"nothing {wf_frag(env)}* exists - expected before pass 2; [E] between "
                "sessions is D11 working.",
            )
            continue
        for name, d in workflows[env].items():
            if d["status"] != "READY":
                checks.note(
                    "OR-1",
                    f"{env}: {name}",
                    f"status {d['status']} - mid-transition; re-run once it settles.",
                )
            else:
                checks.ok(
                    "OR-1",
                    f"{env}: {name}",
                    f"READY, trigger {d['trigger']}, cron {d['cron']}",
                )

    # OR-2: every workflow logs to a named group with retention (D28 item 5); the
    # auto-created /aws/mwaa-serverless/ group is what the item forbids.
    for env, ws in workflows.items():
        for name, d in ws.items():
            lg = d["log_group"]
            what = f"logging on {env}: {name}"
            if not lg:
                checks.fail(
                    "OR-2",
                    what,
                    f"no LogGroupName - the service auto-creates {AUTO_LOG_PREFIX}<id>/ "
                    "with no expiry (step 1.1).",
                )
            elif not lg.startswith(log_prefix(env)):
                checks.fail("OR-2", what, f"{lg} - outside the {log_prefix(env)} contract.")
            else:
                checks.ok("OR-2", what, lg)
    for env, gname, days in lg_rows:
        if days == "(never expires)":
            checks.fail("OR-2", f"retention on {env}: {gname}", "none set - D28 item 5 sets one.")
    for env in workflows:
        auto = [g for e, g, _ in lg_rows if e == env and g.startswith(AUTO_LOG_PREFIX)]
        if auto:
            checks.fail(
                "OR-2",
                f"{env}: auto-created MWAA groups",
                f"{len(auto)} group(s) under {AUTO_LOG_PREFIX} - a workflow ran without "
                "step 1.1's named group.",
            )

    # OR-3: the per-workflow roles (boundary, service trust, no data reach) and the
    # NetworkConfiguration - present, in two AZs, with no default route (step 1.2).
    if role_bad:
        for env, role, what in sorted(set(role_bad)):
            checks.fail("OR-3", f"{env}: role {role}", f"{what}.")
    elif role_rows:
        checks.ok(
            "OR-3",
            "the per-workflow roles",
            f"{len(role_rows)} role(s): bounded, {WF_PRINCIPAL} trust only, no lake reach",
        )
    for env, ws in workflows.items():
        for name, d in ws.items():
            what = f"NetworkConfiguration on {env}: {name}"
            net = d["net"]
            if not d["subnets"] or not d["sgs"]:
                checks.fail(
                    "OR-3",
                    what,
                    "absent - tasks would run in the service's VPC, outside every endpoint "
                    "policy and flow log (step 1.2; open question 12's shape).",
                )
            elif not net["ok"]:
                checks.fail(
                    "OR-3",
                    what,
                    "the subnets or their route tables did not answer - see section 14.",
                )
            elif net["defaults"]:
                routes = ", ".join(f"{s} -> {t}" for s, t in net["defaults"])
                checks.fail(
                    "OR-3",
                    what,
                    f"a default route ({routes}) - the private shape admits no NAT or IGW "
                    "route, and D38 no spoke default route (step 1.2).",
                )
            elif len(net["zones"]) < MIN_AZS:
                checks.fail(
                    "OR-3",
                    what,
                    f"{len(net['zones'])} AZ - the private shape documents two subnets in "
                    "two AZs (step 1.2).",
                )
            else:
                checks.ok(
                    "OR-3",
                    what,
                    f"{len(d['subnets'])} subnet(s) in {len(net['zones'])} AZs, no default "
                    f"route, {len(d['sgs'])} SG(s)",
                )

    # OR-4: each account with workflows has its failure rule; every rule read is ENABLED;
    # the approval rule is Production's [P] amendment (step 5.3).
    for env, ws in workflows.items():
        if ws and not any(
            e == env and r.endswith("-failed") and wf_frag(env) in r for e, r, _ in rule_rows
        ):
            checks.fail(
                "OR-4", f"{env}: the failure rules", f"no {wf_frag(env)}*-failed rule (step 3.1)."
            )
    for env, rname, state in rule_rows:
        if state != "ENABLED":
            checks.fail("OR-4", f"{env}: rule {rname}", f"state {state} - not watching.")
        else:
            checks.ok("OR-4", f"{env}: rule {rname}", "ENABLED")
    if prod_live and not any(r == APPROVAL_RULE for _, r, _ in rule_rows):
        checks.note("OR-4", f"prod: rule {APPROVAL_RULE}", "absent - expected before step 5.3.")

    # OR-5: each definition sits in the definitions home with its S3 version pinned.
    for env, ws in workflows.items():
        for name, d in ws.items():
            if not d["def_bucket"]:
                continue
            what = f"definition of {env}: {name}"
            loc = f"s3://{d['def_bucket']}/{d['def_key']}"
            if d["def_bucket"] != DEF_BUCKET or not d["def_key"].startswith(DEF_PREFIX):
                checks.fail(
                    "OR-5",
                    what,
                    f"{loc} - outside s3://{DEF_BUCKET}/{DEF_PREFIX} (decision 1).",
                )
            elif not d["def_version"]:
                checks.fail(
                    "OR-5",
                    what,
                    f"{loc} with no VersionId - step 1.1 pins the object version, so a "
                    "definition edit without a deploy cannot reach the workflow.",
                )
            else:
                checks.ok("OR-5", what, f"{loc} at version {d['def_version'][:12]}")

    # OR-6: no provisioned MWAA environment in any account read - 0.29 USD/h each. The
    # preventive half is DenyProvisionedMwaa on the root SCP (step 4.3); this is the reading.
    if env_rows:
        for p, name in env_rows:
            checks.fail(
                "OR-6",
                f"MWAA environment in {p}",
                f"{name} - a standing environment fee (PRICING 1.1); provisioned MWAA left "
                "the plan with D7's amendment (step 4.3).",
            )
    elif len(live) > len(env_unread):
        checks.ok(
            "OR-6",
            "provisioned MWAA environments",
            f"none in {len(live) - len(env_unread)} account(s) read",
        )
    if env_unread:
        checks.note(
            "OR-6",
            "provisioned MWAA environments",
            f"not read in {', '.join(env_unread)} - an unread account is not an empty one.",
        )

    # OR-7: version churn against the 50-version quota (risk 4).
    for env, ws in workflows.items():
        for name, d in ws.items():
            try:
                n = int(d["versions"])
            except (TypeError, ValueError):
                continue
            what = f"versions of {env}: {name}"
            if n >= VERSION_WARN:
                checks.fail("OR-7", what, f"{n}/{VERSION_QUOTA} - the quota is close (risk 4).")
            else:
                checks.ok("OR-7", what, f"{n}/{VERSION_QUOTA}")

    # OR-8: every registry write in the record was the deploy role (INT-07's registry half;
    # Stage 9 3.2's policy read back as behaviour).
    if reg_bad:
        for ev_name, caller in sorted(set(reg_bad)):
            checks.fail(
                "OR-8",
                f"{ev_name} caller",
                f"{head2(caller)} is not awsds-deploy-prod - registration is the "
                "pipeline's act (step 5.2, D17).",
            )
    elif reg_rows:
        checks.ok(
            "OR-8",
            "registry writes",
            f"{len(reg_rows)} event(s), every caller is awsds-deploy-prod",
        )

    # ---------------------------------------------------------------------- the report
    wf_table = [
        (env, name, d["status"], d["trigger"], d["cron"], d["encryption"], d["versions"])
        for env, ws in workflows.items()
        for name, d in ws.items()
    ]
    net_table = [
        (env, name, *row)
        for env, ws in workflows.items()
        for name, d in ws.items()
        for row in d["net"]["rows"]
    ]
    run_rows = [
        (env, name, *run)
        for env, ws in workflows.items()
        for name, d in ws.items()
        for run in d["runs"]
    ]
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("ORCHESTRATION - the Stage 10 evidence: workflows, roles, rules, runs")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/orchestration.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The serverless workflows (Staging, Production)
  3. The workflows' network: subnets, AZs, route tables
  4. The per-workflow roles: boundary, trust, the D13 absences
  5. Log groups and retention (D28 item 5)
  6. The EventBridge rules: failures and the approval rule
  7. Recent runs (the schedule evidence)
  8. Provisioned MWAA environments - the absence reading
  9. The service-linked role, and the definitions home
 10. The registry record: who registered, who approved (INT-07)
 11. The blueprint configurations in each Sandbox
 12. CHECKS
 13. The accounts nothing here is measuring
 14. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 10 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - AN ABSENT slice is [E] working between sessions, not an outage. What must NOT
    appear at rest is a provisioned MWAA environment (OR-6) or an auto-created
    /aws/mwaa-serverless/ log group in Staging or Production (OR-2).
  - THIS IS A CONTROL-PLANE READING. Whether a SCHEDULED run fires unattended,
    a failure rule pages, or the lint rejects a bad artifact is behavioural -
    the stage's own proofs (Lesson 20). INT-14's apply-under-boundary proof is
    pass 2's pipeline run, not this file's.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ==============================================================================
        rep.h1("1. Which accounts were measured, and as whom")
        rep.text("""A profile is an (account, permission set) pair; every awsds-* profile here resolves
to the infrastructure user. A `(failed)` row is a profile that did not authenticate,
never a compliant one.

""")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        # ==============================================================================
        rep.h1("2. The serverless workflows (Staging, Production)")
        for env, p in ORCH_ENVS:
            if p not in live:
                rep.line(f"{env}: {p} was not measured.")
            elif not workflows.get(env):
                rep.line(
                    f"{env}: no {wf_frag(env)}* workflow. Pre-pass-2, or [E] down between sessions."
                )
        if wf_table:
            rep.line()
            rep.tabulate(
                ["ENV\tNAME\tSTATUS\tTRIGGER\tCRON\tENCRYPTION\tVERSIONS"]
                + ["\t".join(r) for r in wf_table]
            )
        rep.text("""
The cron column is the schedule: it lives in the YAML definition and the service
runs it through EventBridge Scheduler internally; TriggerMode is the pause lever.
Staging is applied first (pass 2), so a Production workflow with no Staging twin
is worth a second look, not a failure - the [E] slices come and go by session.""")

        # ==============================================================================
        rep.h1("3. The workflows' network: subnets, AZs, route tables")
        if net_table:
            rep.tabulate(
                ["ENV\tWORKFLOW\tSUBNET\tAZ ID\tNAME\tROUTE TABLE"]
                + ["\t".join(r) for r in net_table]
            )
        else:
            rep.line("No workflow subnet to read.")
        rep.text("""
The private-routing shape (step 1.2): two private subnets in two AZs, no route to
a NAT device or an internet gateway, endpoints for logs, monitoring and kms. OR-3
fails on any 0.0.0.0/0 or ::/0 route in these tables; a subnet with no explicit
association is read against its VPC's main table.""")

        # ==============================================================================
        rep.h1("4. The per-workflow roles: boundary, trust, the D13 absences")
        if role_rows:
            rep.tabulate(
                ["ENV\tROLE\tBOUNDARY\tTRUSTED SERVICE(S)"] + ["\t".join(r) for r in role_rows]
            )
        else:
            rep.line("No awsds-<env>-wf-* role.")
        rep.text(f"""
The contract (step 1.3): trust in {WF_PRINCIPAL} alone, a permissions
boundary (the pipeline creates these under Stage 8 4.1's condition), and no data
reach - no s3 allow naming a lake bucket, no lakeformation:GetDataAccess. The
orchestrator starts jobs; awsds-<env>-job-exec touches data (D13 one level up).""")

        # ==============================================================================
        rep.h1("5. Log groups and retention (D28 item 5)")
        if lg_rows:
            rep.tabulate(["ENV\tLOG GROUP\tRETENTION (DAYS)"] + ["\t".join(r) for r in lg_rows])
        else:
            rep.line("No workflow log group yet.")

        # ==============================================================================
        rep.h1("6. The EventBridge rules: failures and the approval rule")
        if rule_rows:
            rep.tabulate(["ENV\tRULE\tSTATE"] + ["\t".join(r) for r in rule_rows])
        else:
            rep.line("No awsds-<env>-wf-* or model-approval rule (pre-step-3.1/5.3).")

        # ==============================================================================
        rep.h1("7. Recent runs (the schedule evidence)")
        if run_rows:
            rep.tabulate(
                ["ENV\tWORKFLOW\tRUN\tTYPE\tSTATUS\tSTARTED"]
                + ["\t".join(r) for r in run_rows[:40]]
            )
            if len(run_rows) > 40:
                rep.line(f"... and {len(run_rows) - 40} more row(s).")
        else:
            rep.line("No recorded run.")
        rep.text("""
Verification (v) wants at least one TYPE=SCHEDULED row with nobody at the
keyboard. The type is read per run with get-workflow-run: list-workflow-runs
returns RunType null for every run (measured 2026-10-10). Runs and their history
die with the [E] slice (Lesson 4) - 6.3 writes the disposition into the log
before the first make down.""")

        # ==============================================================================
        rep.h1("8. Provisioned MWAA environments - the absence reading")
        if env_rows:
            rep.tabulate(["PROFILE\tENVIRONMENT"] + ["\t".join(r) for r in env_rows])
        else:
            rep.line("None in any account read - the expected steady state (OR-6).")
        rep.text("""
An environment bills 0.29 USD/h (mw1.micro) for existing. Provisioned MWAA left the
plan with D7's amendment: the OnDemand Workflows blueprint is category 3, and
DenyProvisionedMwaa (step 4.3) refuses airflow:CreateEnvironment on the root SCP
once applied. This section is the reading behind that control.""")

        # ==============================================================================
        rep.h1("9. The service-linked role, and the definitions home")
        if slr_rows:
            rep.tabulate(["ENV\t" + SLR_NAME] + ["\t".join(r) for r in slr_rows])
        else:
            rep.line(f"{SLR_NAME}: not measured.")
        rep.line()
        if def_rows:
            rep.tabulate(
                [f"s3://{DEF_BUCKET}/{DEF_PREFIX}* KEY\tSIZE"] + ["\t".join(r) for r in def_rows]
            )
        else:
            rep.line(f"No object under s3://{DEF_BUCKET}/{DEF_PREFIX} (pre-2.4).")
        rep.text("""
The SLR appears at the first CreateWorkflow in each account (Lesson 17), Staging
before Production - 0.3 records the absent baseline, 1.6 the enumerated arrival.
The definitions home is decision 1's: versioned, CMK-protected, perimeter-branched
since Stage 9 1.1.""")

        # ==============================================================================
        rep.h1("10. The registry record: who registered, who approved (INT-07)")
        if reg_rows:
            rep.tabulate(["TIME\tEVENT\tCALLER"] + ["\t".join(r) for r in reg_rows[:25]])
            if len(reg_rows) > 25:
                rep.line(f"... and {len(reg_rows) - 25} more event(s).")
        else:
            rep.line("No Create/UpdateModelPackage event in the 90-day lookup.")
        rep.text("""
Stage 9 3.2's policy says register-and-approve is awsds-deploy-prod alone; this
is that sentence read back as behaviour. OR-8 fails on any other caller.""")

        # ==============================================================================
        rep.h1("11. The blueprint configurations in each Sandbox")
        if bp_rows:
            rep.tabulate(["PROFILE\tBLUEPRINT\tENABLED REGIONS"] + ["\t".join(r) for r in bp_rows])
        else:
            rep.line("No Sandbox profile measured, no V2 domain, or no blueprint configuration.")
        rep.text("""
Context, not a check. A configuration is applied, and listed, from the member
account; the domain account lists none. The serverless-Workflows surface needs no
configuration of its own (6d step 4.1 found it provided by the category-1 roster),
and a Workflows row here would be the category-3 blueprint, which ./aws/studio.py
US-3 refuses. What OR-6 refuses is its consequence - a fee-bearing environment in
any account.""")

        # ==============================================================================
        rep.h1("12. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  OR-1  each account's workflows exist and rest READY (step 1.1)
  OR-2  named log groups with retention; no /aws/mwaa-serverless/ orphan (D28 item 5)
  OR-3  per-workflow roles bounded, airflow-serverless trust only, no lake reach;
        NetworkConfiguration set, two AZs, no default route (steps 1.2, 1.3)
  OR-4  the *-failed rules and awsds-prod-model-approval ENABLED (steps 3.1, 5.3)
  OR-5  definitions under s3://awsds-prod-outputs/workflows/, VersionId pinned
        (steps 1.1, 2.4, decision 1)
  OR-6  no provisioned MWAA environment in any account read (step 4.3)
  OR-7  workflow versions vs the 50-version quota (risk 4)
  OR-8  every registry write was awsds-deploy-prod (INT-07, Stage 9 3.2)""")

        # ==============================================================================
        rep.h1("13. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 12 as a pass.

  - Sandbox's portal-authored workflows bill task-hours there and are not read
    here (6d step 4); `aws mwaa-serverless list-workflows` as
    awsds-infra-sandbox-1 lists them. OR-6 still reads Sandbox.
  - Every Sandbox beyond unit 1 has no profile until Stage 14 (D35).
  - GitLab's objects (the lint job, the approval manual job) live behind
    gitlab.awsds.internal - the stage log records them.""")

        # ==============================================================================
        rep.h1("14. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/orchestration.py")

    # ------------------------------------------------------------------------------ run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 14)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 12)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
