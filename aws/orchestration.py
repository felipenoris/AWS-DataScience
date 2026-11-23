#!/usr/bin/env -S uv run --quiet
"""orchestration.py - Stage 10's evidence: the MWAA Serverless workflows in Staging and
Production, which the SMUS CI/CD CLI creates in each account's deployment project (Stage 19
decision 6 (b)), and D41's chain layer above them (OR-9): each workflow's execution role, the
project's (boundary, trust, the policies <env>/studio/ attaches), its NetworkConfiguration
(present, two AZs, no default route), its log group and retention (D28 item 5), its failure
rule, the model-approval rule, recent runs with their type, the absence of any provisioned MWAA
environment, the definitions, and the registry's register/approve record (INT-07's registry
half, consumed).

needs:    a live SSO session, and nothing else:

              aws sso login --sso-session awsds

run:      ./aws/orchestration.py                       # every awsds-* profile
          ./aws/orchestration.py awsds-infra-staging   # only the ones named
          python3 aws/orchestration.py -               # CloudShell, ambient credentials
writes:   aws/output/orchestration.txt   (untracked - see .gitignore)
reads:    mwaa-serverless:ListWorkflows, GetWorkflow, ListWorkflowVersions,
          ListWorkflowRuns, GetWorkflowRun; mwaa:ListEnvironments; ec2:DescribeSubnets,
          DescribeRouteTables; logs:DescribeLogGroups; events:ListRules; iam:GetRole,
          ListRoles, ListRolePolicies, GetRolePolicy, ListAttachedRolePolicies;
          scheduler:GetScheduleGroup, GetSchedule; states:ListStateMachines;
          datazone:ListDomains, ListEnvironmentBlueprintConfigurations,
          GetEnvironmentBlueprint (from each Sandbox); cloudtrail:LookupEvents;
          sts:GetCallerIdentity.
          It never creates, updates or deletes anything.
exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
"""

# The subject spans accounts, so this script is multi-profile: an application is developed in a
# Sandbox project and the CLI deploys it into Staging's deployment project, then Production's, and
# the provisioned-MWAA reading (OR-6) is only meaningful measured in every account, since the
# OnDemand Workflows blueprint would create a fee-bearing environment in a member account.
# Section 1 prints the caller ARN of every profile.
#
# The contracts it reads, each named in the stage files so a rename fails loudly:
#   - every workflow in a deployment target is the CLI's, <application>_<project>_<workflow> with
#     each character outside [A-Za-z0-9_] an underscore, the project deploy-staging or
#     deploy-production (Stage 19 step 4.6); OR-1 fails on any other, release T's included
#   - no workflow carries a cron of its own: a chain's Scheduler schedule starts every production
#     workflow (Stage 10 decision 13), so OR-1 fails on one
#   - a workflow runs as its project's role, datazone_usr_role_<project id>_<environment id>, under
#     awsds-<env>-project-boundary and carrying the policies <env>/studio/ attaches (OR-3)
#   - its log group is the CLI's, /aws/mwaa-serverless/<domain id>-<project id>/<workflow>,
#     which the service creates with no retention; D28 item 5 asks one (SUP-254; OR-2)
#   - its definition is the CLI's upload under <domain id>/<project id>/shared/ in the account's
#     projects bucket, awsds-<env>-smus-projects (OR-5)
#   - its failure rule is awsds-<env>-wf-<application>-<workflow>-failed, matching its ARN up to the
#     service's suffix and naming the service's detail types, which carry the "MWAA Serverless "
#     prefix (Stage 10 step 3.1, terraform-modules/orchestration; OR-4)
#   - the approval rule is awsds-prod-model-approval (Stage 10 step 5.3)
#   - the chain layer carries awsds-<env>-chain-, the group awsds-<env>-chains and the roles
#     awsds-<env>-chain-exec and -chain-scheduler, which the module creates with no boundary and
#     no managed policy (OR-9)
#   - release T named its per-workflow roles awsds-<env>-wf-<application>-<workflow>; OR-3 fails on
#     one, since release T's orchestration/ slice holds nothing in either target
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - Sandbox's workflows, which ./aws/sandbox-orchestration.py reads.
#   - The behavioural proofs (a chain's schedule firing unattended, the failure rules firing) are
#     the stage's own (Lesson 20).

from __future__ import annotations

import json
import re
import sys

from awslib import cmdline, context, profiles
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
# Each account's deployment project (Stage 19 step 4.6), whose name the CLI writes into each
# workflow's name, and the projects bucket the CLI uploads the definitions to (sagemaker-prereqs).
DEPLOY_PROJECTS = {"staging": "deploy-staging", "prod": "deploy-production"}
PROJECT_BUCKETS = {"staging": "awsds-staging-smus-projects", "prod": "awsds-prod-smus-projects"}
PROJECT_ROLE_PREFIX = "datazone_usr_role_"
# The policies <env>/studio/ attaches to the deployment project's role (workflows.tf,
# person-session.tf, notebook-run.tf, warehouse.tf). A workflow runs as that role.
PROJECT_ROLE_POLICIES = {
    "staging": (
        "awsds-staging-workflows",
        "awsds-staging-person-session-deny",
        "awsds-staging-notebook-run-deny",
    ),
    "prod": (
        "awsds-prod-workflows",
        "awsds-prod-person-session-deny",
        "awsds-prod-notebook-run-deny",
        "awsds-prod-warehouse-load",
    ),
}
WF_PRINCIPAL = "airflow-serverless.amazonaws.com"
# The service's events carry the "MWAA Serverless " prefix (the EventBridge reference page and an
# example event, read 2026-10-22); a failure rule must name both run-level failures (step 3.1).
WF_EVENT_SOURCE = "aws.airflow-serverless"
FAILURE_DETAIL_TYPES = (
    "MWAA Serverless Workflow Run Failed",
    "MWAA Serverless Workflow Run Timeout",
)
# The chain layer's roles and the service each one trusts alone (terraform-modules/orchestration).
CHAIN_ROLES = {
    "chain-exec": "states.amazonaws.com",
    "chain-scheduler": "scheduler.amazonaws.com",
}
# What a chain role never holds: the chains start and read workflows, and touch no job and no data.
CHAIN_FORBIDDEN = ("s3:", "glue:", "sagemaker:", "lakeformation:", "iam:passrole")
SLR_NAME = "AWSServiceRoleForAmazonMWAAServerless"
MIN_AZS = 2  # the private-routing shape's documented minimum (step 1.2)
VERSION_QUOTA = 50  # versions per workflow; no prune API is documented (risk 4)
VERSION_WARN = 40
LOOKUP_MAX = 50  # CloudTrail's largest lookup page: --max-results turns the CLI's paging off
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
    """The prefix of a workflow's failure rule, and of release T's per-workflow roles."""
    return f"awsds-{env}-wf-"


def cli_frag(env: str) -> str:
    """The deployment project's part of a workflow name the CLI composes."""
    return "_" + re.sub(r"[^A-Za-z0-9_]", "_", DEPLOY_PROJECTS[env]) + "_"


def chain_frag(env: str) -> str:
    return f"awsds-{env}-chain-"


def project_boundary(env: str) -> str:
    return f"awsds-{env}-project-boundary"


def rule_prefixes(pattern: dict) -> list:
    """The workflowArn prefixes a failure rule's pattern matches: "" when it names none."""
    matchers = _as_list((pattern.get("detail") or {}).get("workflowArn"))
    if not matchers:
        return [""]
    found = []
    for m in matchers:
        if isinstance(m, dict) and m.get("prefix"):
            found.append(str(m["prefix"]))
        elif isinstance(m, str):
            found.append(m)
    return found


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


def read_workflows(cli: AwsCli, env: str, logerr) -> dict:
    """Every workflow of the account: name -> what Stage 10 reads of it.

    ``cli`` marks a name the CLI composes for the account's deployment project, and ``read``
    whether get-workflow answered. ``logerr(what, err)`` records a failed read, so a field
    missing because its call failed is never reported as a field the workflow lacks.
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
        d = {
            "arn": str(arn),
            "cli": cli_frag(env) in str(name),
            "read": False,
            "status": str(status),
            "trigger": str(tmode),
            "cron": "-",
            "role": "",
            "log_group": "",
            "subnets": [],
            "sgs": [],
            "def_bucket": "",
            "def_key": "",
            "snapshot": "-",
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
            "CodeSnapshottedAt,ScheduleConfiguration.CronExpression,"
            "EncryptionConfiguration.Type]",
            "--output",
            "json",
            log=False,
        )
        if r.ok and r.stdout:
            role, log_group, subnets, sgs, bucket, key, snapshot, cron, enc = json.loads(r.stdout)
            d.update(
                read=True,
                role=str(role or ""),
                log_group=str(log_group or ""),
                subnets=_as_list(subnets),
                sgs=_as_list(sgs),
                def_bucket=str(bucket or ""),
                def_key=str(key or ""),
                snapshot=str(snapshot or "-")[:19],
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


def read_chain_layer(cli: AwsCli, env: str, rules: dict) -> dict:
    """The chain layer of one account, by its contract names (steps 3.4-3.7).

    Returns ``group`` (the schedule group exists), ``log_retention`` (the machines' log group's
    retention, "" when absent, "(never expires)" when unset), ``roles`` (name -> (boundary tail,
    trusted services, forbidden actions found, attached managed policies) or None when absent),
    ``machines`` (name -> (schedule state or "(none)", failure rule state or "(none)")) and
    ``unread`` (calls that did not answer, so an absence is never inferred from one). ``rules``
    is the account's list-rules answer, name -> state.
    """
    out = {
        "group": False,
        "log_retention": "",
        "roles": {},
        "machines": {},
        "unread": [],
    }
    group = f"awsds-{env}-chains"
    res = cli.run(
        "scheduler",
        "get-schedule-group",
        "--name",
        group,
        "--query",
        "State",
        "--output",
        "text",
        log=False,
        tolerate="ResourceNotFoundException",
    )
    if res.ok and not res.tolerated:
        out["group"] = True
    elif not res.ok:
        out["unread"].append("scheduler get-schedule-group")

    log_group = f"/aws/vendedlogs/states/awsds-{env}-chains"
    res = cli.run(
        "logs",
        "describe-log-groups",
        "--log-group-name-prefix",
        log_group,
        "--query",
        "logGroups[].[logGroupName,retentionInDays]",
        "--output",
        "json",
        log=False,
    )
    for gname, days in _json(res, []):
        if gname == log_group:
            out["log_retention"] = str(days) if days else "(never expires)"

    for suffix, service in CHAIN_ROLES.items():
        role = f"awsds-{env}-{suffix}"
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
            tolerate="NoSuchEntity",
        )
        if r.tolerated:
            out["roles"][role] = None
            continue
        if not (r.ok and r.stdout):
            out["unread"].append(f"iam get-role {role}")
            continue
        boundary, trust = json.loads(r.stdout)
        services: list = []
        for st in _stmts(trust):
            services += _as_list((st.get("Principal", {}) or {}).get("Service"))
        forbidden: list = []
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
                for action in _as_list(st.get("Action")):
                    if str(action).lower().startswith(CHAIN_FORBIDDEN) or str(action) == "*":
                        forbidden.append(str(action))
        att = cli.run(
            "iam",
            "list-attached-role-policies",
            "--role-name",
            role,
            "--query",
            "AttachedPolicies[].PolicyName",
            "--output",
            "json",
            log=False,
        )
        if not att.ok:
            out["unread"].append(f"iam list-attached-role-policies {role}")
        btail = str(boundary).rsplit("/", 1)[-1] if boundary else "(none)"
        out["roles"][role] = (
            btail,
            sorted(set(services)),
            sorted(set(forbidden)),
            sorted(map(str, _json(att, []))),
        )

    res = cli.run(
        "stepfunctions",
        "list-state-machines",
        "--query",
        f"stateMachines[?starts_with(name, '{chain_frag(env)}')].name",
        "--output",
        "json",
        log=False,
    )
    if not res.ok:
        out["unread"].append("stepfunctions list-state-machines")
    for name in _json(res, []):
        s = cli.run(
            "scheduler",
            "get-schedule",
            "--group-name",
            group,
            "--name",
            str(name),
            "--query",
            "State",
            "--output",
            "text",
            log=False,
            tolerate="ResourceNotFoundException",
        )
        schedule = s.stdout.strip() if s.ok and not s.tolerated else "(none)"
        out["machines"][str(name)] = (schedule, rules.get(f"{name}-failed", "(none)"))
    return out


def read_project_role(cli: AwsCli, role: str) -> dict | None:
    """A workflow's execution role as OR-3 reads it, or None when get-role did not answer.

    Returns ``boundary`` (the boundary's name, "(none)" without one), ``services`` (every
    service its trust names), ``tags`` (Key -> Value: DataZone tags its project role with
    AmazonDataZoneProject and AmazonDataZoneDomain) and ``attached`` (the managed policies'
    names, None when the listing did not answer).
    """
    r = cli.run(
        "iam",
        "get-role",
        "--role-name",
        role,
        "--query",
        "Role.[PermissionsBoundary.PermissionsBoundaryArn,AssumeRolePolicyDocument,Tags]",
        "--output",
        "json",
    )
    if not (r.ok and r.stdout):
        return None
    boundary, trust, tags = json.loads(r.stdout)
    services: list = []
    for st in _stmts(trust):
        services += _as_list((st.get("Principal", {}) or {}).get("Service"))
    att = cli.run(
        "iam",
        "list-attached-role-policies",
        "--role-name",
        role,
        "--query",
        "AttachedPolicies[].PolicyName",
        "--output",
        "json",
    )
    return {
        "boundary": str(boundary).rsplit("/", 1)[-1] if boundary else "(none)",
        "services": sorted(set(map(str, services))),
        "tags": {str(t.get("Key")): str(t.get("Value")) for t in tags or []},
        "attached": sorted(map(str, _json(att, []))) if att.ok else None,
    }


def read_release_t_roles(cli: AwsCli, env: str) -> list | None:
    """The roles named awsds-<env>-wf-*, release T's per-workflow roles; None when unread."""
    res = cli.run(
        "iam",
        "list-roles",
        "--query",
        f"Roles[?starts_with(RoleName, '{wf_frag(env)}')].RoleName",
        "--output",
        "json",
    )
    if not res.ok:
        return None
    return sorted(map(str, _json(res, [])))


def project_home(info: dict | None) -> tuple:
    """(domain id, project id) from a project role's DataZone tags; ("", "") when unknown."""
    tags = (info or {}).get("tags") or {}
    return tags.get("AmazonDataZoneDomain", ""), tags.get("AmazonDataZoneProject", "")


def main(argv: list) -> int:
    cmdline.check(argv, __doc__)
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
            cli_for(p), env, lambda what, err, p=p: logerr(p, what, err)
        )

    # ------------------- the execution roles: each workflow's project role, release T's roles
    proj_roles: dict = {}  # env -> {role name -> read_project_role() or None}
    release_t_roles: dict = {}  # env -> [role] or None when unread
    for env, p in measured:
        cli = cli_for(p)
        proj_roles[env] = {}
        for d in workflows[env].values():
            role = d["role"].rsplit("/", 1)[-1]
            if role and role not in proj_roles[env]:
                proj_roles[env][role] = read_project_role(cli, role)
        release_t_roles[env] = read_release_t_roles(cli, env)

    # ------------------------------------------ log groups and retention (D28 item 5)
    lg_rows: list = []  # (env, log group, retention)
    for env, p in measured:
        res = cli_for(p).run(
            "logs",
            "describe-log-groups",
            "--log-group-name-prefix",
            AUTO_LOG_PREFIX,
            "--query",
            "logGroups[].[logGroupName,retentionInDays]",
            "--output",
            "json",
        )
        for gname, days in _json(res, []):
            lg_rows.append((env, str(gname), str(days) if days else "(never expires)"))

    # ------------------------------ the EventBridge rules: failures + model approval
    rule_rows: list = []  # (env, rule, state)
    rule_patterns: dict = {}  # (env, rule) -> the parsed event pattern
    all_rules: dict = {}  # env -> {rule: state}, for the chain layer's rules (OR-9)
    for env, p in measured:
        res = cli_for(p).run(
            "events",
            "list-rules",
            "--query",
            "Rules[].[Name,State,EventPattern]",
            "--output",
            "json",
            log=False,
        )
        all_rules[env] = {}
        for rname, state, pattern in _json(res, []):
            all_rules[env][str(rname)] = str(state)
            if wf_frag(env) in str(rname) or (env == "prod" and str(rname) == APPROVAL_RULE):
                rule_rows.append((env, str(rname), str(state)))
                try:
                    rule_patterns[(env, str(rname))] = json.loads(pattern or "{}")
                except ValueError:
                    rule_patterns[(env, str(rname))] = {}

    # ----------------------------------------- the chain layer (steps 3.4-3.7, D41)
    chains: dict = {}  # env -> read_chain_layer()
    for env, p in measured:
        note(f"measuring {p} (the chain layer) ...")
        chains[env] = read_chain_layer(cli_for(p), env, all_rules.get(env, {}))

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

    # -------------- the registry record: who registered, who approved (INT-07's registry half)
    reg_rows: list = []  # (time, event, caller tail)
    reg_bad: list = []  # (event, caller)
    reg_unread: list = []  # event names whose history was not read to its last page
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (registry events) ...")
        for ev_name in ("CreateModelPackage", "UpdateModelPackage"):
            listing = cli.pages(
                "cloudtrail",
                "lookup-events",
                "--lookup-attributes",
                f"AttributeKey=EventName,AttributeValue={ev_name}",
                "--max-results",
                str(LOOKUP_MAX),
            )
            if not listing.complete:
                reg_unread.append(ev_name)
            for item in listing.items("Events"):
                try:
                    ev = json.loads(item.get("CloudTrailEvent") or "")
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

    # OR-1: every workflow of a deployment target is the CLI's in the account's deployment project,
    # and rests READY with no cron. Release F's deploys created them in both targets on 2026-11-16,
    # and they stay between sittings, so an absence is a deletion.
    for env, _p in measured:
        if not workflows[env]:
            checks.fail(
                "OR-1",
                f"{env}: the workflows",
                f"none - the CLI creates them at a deploy into {DEPLOY_PROJECTS[env]}, and "
                "release F's created them in both targets on 2026-11-16 (Stage 19).",
            )
            continue
        for name, d in workflows[env].items():
            if not d["cli"]:
                checks.fail(
                    "OR-1",
                    f"{env}: {name}",
                    f"not a workflow the CLI composes for {DEPLOY_PROJECTS[env]} (no "
                    f"{cli_frag(env)} in its name): release T's orchestration/ slice creates "
                    f"{wf_frag(env)}* workflows, and holds nothing in either target.",
                )
            elif d["status"] != "READY":
                checks.note(
                    "OR-1",
                    f"{env}: {name}",
                    f"status {d['status']} - mid-transition; re-run once it settles.",
                )
            elif d["cron"] != "-":
                checks.fail(
                    "OR-1",
                    f"{env}: {name}",
                    f"cron {d['cron']} - a chain's schedule starts every production "
                    "workflow (Stage 10 decision 13).",
                )
            else:
                checks.ok(
                    "OR-1",
                    f"{env}: {name}",
                    f"READY, trigger {d['trigger']}, cron {d['cron']}",
                )

    def home_of(env: str, d: dict) -> tuple:
        return project_home(proj_roles[env].get(d["role"].rsplit("/", 1)[-1]))

    # OR-2: every workflow logs to the group the CLI names for it, and every group under
    # /aws/mwaa-serverless/ carries a retention (D28 item 5). The service creates the group with
    # none (SUP-254): EXC-25 until Stage 19 decision 27.
    for env, ws in workflows.items():
        for name, d in ws.items():
            if not (d["cli"] and d["read"]):
                continue
            domain, project = home_of(env, d)
            expected = f"{AUTO_LOG_PREFIX}{domain}-{project}/{name}" if project else ""
            lg = d["log_group"]
            what = f"logging on {env}: {name}"
            if not lg:
                checks.fail("OR-2", what, "no LogGroupName.")
            elif expected and lg != expected:
                checks.fail(
                    "OR-2", what, f"{lg} - not {expected}, the CLI's group for the workflow."
                )
            elif not expected:
                checks.note("OR-2", what, f"{lg} - its role's project was not read (section 4).")
            else:
                checks.ok("OR-2", what, lg)
    for env, gname, days in lg_rows:
        what = f"retention on {env}: {gname}"
        if days == "(never expires)":
            checks.fail(
                "OR-2",
                what,
                "none set - D28 item 5 sets one; EXC-25 until Stage 19 decision 27 is applied.",
            )
        else:
            checks.ok("OR-2", what, f"{days} days")

    # OR-3: each workflow runs as its project's role, under the project boundary, trusted by the
    # service and carrying what <env>/studio/ attaches; its NetworkConfiguration is present, in two
    # AZs, with no default route (Stage 10 step 1.2). Release T's per-workflow roles are gone.
    for env, ws in workflows.items():
        for name, d in ws.items():
            if not (d["cli"] and d["read"]):
                continue
            role = d["role"].rsplit("/", 1)[-1]
            info = proj_roles[env].get(role)
            what = f"role of {env}: {name}"
            _domain, project = project_home(info)
            if not role:
                checks.fail("OR-3", what, "no RoleArn.")
            elif info is None:
                checks.note("OR-3", what, f"{role} - get-role did not answer (section 14).")
            elif not (project and role.startswith(f"{PROJECT_ROLE_PREFIX}{project}_")):
                checks.fail(
                    "OR-3",
                    what,
                    f"{role} - not a project role: {PROJECT_ROLE_PREFIX}<project id>_<environment "
                    "id>, tagged AmazonDataZoneProject with that project id.",
                )
            elif info["boundary"] != project_boundary(env):
                checks.fail(
                    "OR-3",
                    what,
                    f"{role}: boundary {info['boundary']}, not {project_boundary(env)}.",
                )
            elif WF_PRINCIPAL not in info["services"]:
                checks.fail("OR-3", what, f"{role}: its trust does not name {WF_PRINCIPAL}.")
            elif info["attached"] is None:
                checks.note(
                    "OR-3", what, f"{role}: its managed policies were not listed (section 14)."
                )
            elif missing := [x for x in PROJECT_ROLE_POLICIES[env] if x not in info["attached"]]:
                checks.fail(
                    "OR-3",
                    what,
                    f"{role} lacks {', '.join(missing)}, which <env>/studio/ attaches: the runs "
                    "go without that grant or deny.",
                )
            else:
                checks.ok(
                    "OR-3",
                    what,
                    f"{role}: {info['boundary']}, {' '.join(PROJECT_ROLE_POLICIES[env])}",
                )
    for env, roles in release_t_roles.items():
        if roles is None:
            checks.note(
                "OR-3", f"{env}: release T's roles", "list-roles did not answer (section 14)."
            )
        for role in roles or []:
            checks.fail(
                "OR-3",
                f"{env}: role {role}",
                "release T's per-workflow role: its orchestration/ slice holds nothing in either "
                "target, and an apply of it recreates the role.",
            )
    for env, ws in workflows.items():
        for name, d in ws.items():
            if not (d["cli"] and d["read"]):
                continue
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

    # OR-4: every workflow has a failure rule matching its ARN, every rule read is ENABLED and
    # names the service's source and both run-failure detail types (Stage 10 step 3.1); the
    # approval rule is Production's (step 5.3).
    for env, ws in workflows.items():
        wf_rules = {
            r: rule_prefixes(rule_patterns.get((env, r), {}))
            for e, r, _ in rule_rows
            if e == env and r.endswith("-failed") and wf_frag(env) in r
        }
        for name, d in ws.items():
            if not d["cli"]:
                continue
            heard = sorted(
                r for r, ps in wf_rules.items() if any(d["arn"].startswith(x) for x in ps)
            )
            if heard:
                checks.ok("OR-4", f"{env}: failure rule of {name}", " ".join(heard))
            else:
                checks.fail(
                    "OR-4",
                    f"{env}: failure rule of {name}",
                    f"no {wf_frag(env)}*-failed rule matches its ARN: a failed run notifies "
                    "nobody (step 3.1).",
                )
    for env, rname, state in rule_rows:
        missing = []
        if rname.endswith("-failed") and wf_frag(env) in rname:
            pattern = rule_patterns.get((env, rname), {})
            missing = [
                t for t in FAILURE_DETAIL_TYPES if t not in _as_list(pattern.get("detail-type"))
            ]
            if _as_list(pattern.get("source")) != [WF_EVENT_SOURCE]:
                missing.append(f"source {WF_EVENT_SOURCE}")
        if state != "ENABLED":
            checks.fail("OR-4", f"{env}: rule {rname}", f"state {state} - not watching.")
        elif missing:
            checks.fail(
                "OR-4",
                f"{env}: rule {rname}",
                f"its pattern lacks {', '.join(missing)}: a rule on a detail type the service "
                "never emits is inert and reads ENABLED (step 3.1, Lesson 56).",
            )
        else:
            checks.ok("OR-4", f"{env}: rule {rname}", "ENABLED")
    if prod_live and not any(r == APPROVAL_RULE for _, r, _ in rule_rows):
        checks.note("OR-4", f"prod: rule {APPROVAL_RULE}", "absent - expected before step 5.3.")

    # OR-5: each definition is the CLI's upload, under its project's shared/ prefix in the
    # account's projects bucket.
    for env, ws in workflows.items():
        for name, d in ws.items():
            if not (d["cli"] and d["read"]):
                continue
            domain, project = home_of(env, d)
            home = f"{domain}/{project}/shared/" if project else ""
            what = f"definition of {env}: {name}"
            loc = f"s3://{d['def_bucket']}/{d['def_key']}"
            if not d["def_bucket"]:
                checks.fail("OR-5", what, "no DefinitionS3Location.")
            elif d["def_bucket"] != PROJECT_BUCKETS[env] or not (
                home and d["def_key"].startswith(home)
            ):
                place = home or "<domain id>/<project id>/shared/"
                checks.fail("OR-5", what, f"{loc} - outside s3://{PROJECT_BUCKETS[env]}/{place}.")
            else:
                checks.ok("OR-5", what, loc)

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
    elif reg_unread:
        checks.note(
            "OR-8",
            "registry writes",
            f"{' and '.join(reg_unread)} not read to the last page (section 14); "
            f"{len(reg_rows)} event(s) read.",
        )
    elif reg_rows:
        checks.ok(
            "OR-8",
            "registry writes",
            f"{len(reg_rows)} event(s), every caller is awsds-deploy-prod",
        )

    # OR-9: the chain layer (steps 3.4-3.7), <env>/chains/'s since 2026-11-16, whose machines start
    # the CLI's workflows. Every base piece, each machine's schedule and failure rule, and each
    # role's one service, no managed policy and no job or data action are required: the module
    # gives the roles no boundary, so what their inline policies allow is all they allow.
    for env, layer in chains.items():
        if layer["unread"]:
            checks.note(
                "OR-9",
                f"{env}: the chain layer",
                f"{', '.join(layer['unread'])} did not answer - an unread piece is not an absent one.",
            )
        if not layer["group"]:
            checks.fail(
                "OR-9", f"{env}: schedule group", f"awsds-{env}-chains is absent (step 3.4)."
            )
        if not layer["log_retention"]:
            checks.fail(
                "OR-9",
                f"{env}: the machines' log group",
                f"/aws/vendedlogs/states/awsds-{env}-chains is absent (step 3.4).",
            )
        elif layer["log_retention"] == "(never expires)":
            checks.fail(
                "OR-9", f"{env}: the machines' log group", "no retention - D28 item 5 sets one."
            )
        for role, found in layer["roles"].items():
            service = CHAIN_ROLES[role.split(f"awsds-{env}-", 1)[1]]
            if found is None:
                checks.fail("OR-9", f"{env}: role {role}", "absent (step 3.4).")
                continue
            btail, services, forbidden, attached = found
            if services != [service]:
                checks.fail(
                    "OR-9",
                    f"{env}: role {role}",
                    f"trust names {' '.join(services) or 'no service'}, not {service} alone.",
                )
            elif attached:
                checks.fail(
                    "OR-9",
                    f"{env}: role {role}",
                    f"carries {' '.join(attached)}: the module attaches no managed policy, and "
                    "this reading covers the inline ones alone (Lesson 72).",
                )
            elif forbidden:
                checks.fail(
                    "OR-9",
                    f"{env}: role {role}",
                    f"allows {' '.join(forbidden)} - a chain role touches no job and no data.",
                )
            else:
                checks.ok(
                    "OR-9",
                    f"{env}: role {role}",
                    f"{service} trust, inline policies only, boundary {btail}",
                )
        if not layer["machines"] and not layer["unread"]:
            checks.fail(
                "OR-9",
                f"{env}: the chains",
                f"no {chain_frag(env)}* state machine: nothing starts the workflows (step 3.5).",
            )
        for machine, (schedule, rule) in layer["machines"].items():
            if schedule == "(none)":
                checks.fail(
                    "OR-9",
                    f"{env}: chain {machine}",
                    f"no schedule {machine} in awsds-{env}-chains (step 3.5).",
                )
            elif rule != "ENABLED":
                checks.fail(
                    "OR-9",
                    f"{env}: chain {machine}",
                    f"failure rule {machine}-failed is {rule} (step 3.7).",
                )
            else:
                checks.ok(
                    "OR-9", f"{env}: chain {machine}", f"schedule {schedule}, failure rule ENABLED"
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
    role_table = []  # (env, workflow, role, boundary, project, managed policies of this estate)
    def_table = []  # (env, workflow, definition, snapshot)
    for env, ws in workflows.items():
        for name, d in ws.items():
            role = d["role"].rsplit("/", 1)[-1]
            info = proj_roles.get(env, {}).get(role)
            mine = [x for x in (info or {}).get("attached") or [] if x.startswith("awsds-")]
            role_table.append(
                (
                    env,
                    name,
                    role or "-",
                    info["boundary"] if info else "(unread)",
                    project_home(info)[1] or "-",
                    " ".join(mine) or "-",
                )
            )
            if d["def_bucket"]:
                def_table.append(
                    (env, name, f"s3://{d['def_bucket']}/{d['def_key']}", d["snapshot"])
                )
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
  4. The workflows' execution roles: the project's role, its boundary and policies
  5. Log groups and retention (D28 item 5)
  6. The EventBridge rules: failures and the approval rule
  7. Recent runs
  8. Provisioned MWAA environments - the absence reading
  9. The service-linked role, and the definitions
 10. The registry record: who registered, who approved (INT-07)
 11. The blueprint configurations in each Sandbox
 12. CHECKS
 13. The accounts nothing here is measuring
 14. Calls that failed

HOW TO READ THIS FILE
  - The workflows are the CI/CD CLI's, created in each account's deployment project
    at a deploy, and they stay between sittings: an absent workflow is a deleted one.
    A workflow outside that contract is release T's or a hand's (OR-1).
  - A provisioned MWAA environment must not appear at rest (OR-6). A group under
    /aws/mwaa-serverless/ with no retention fails OR-2, expected while EXC-25 stands.
  - This is a control-plane reading. Whether a chain's schedule fires unattended or
    a failure rule notifies is behavioural, the stage's own proofs (Lesson 20).

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
                rep.line(f"{env}: no workflow (OR-1).")
        if wf_table:
            rep.line()
            rep.tabulate(
                ["ENV\tNAME\tSTATUS\tTRIGGER\tCRON\tENCRYPTION\tVERSIONS"]
                + ["\t".join(r) for r in wf_table]
            )
        rep.text("""
The CLI creates or updates each workflow at a deploy into the account's deployment
project, Staging's leg first, and names it <application>_<project>_<workflow>; its
ARN carries a suffix the service generates. The cron column reads "-" for every
workflow here: a chain's Scheduler schedule starts each one, the pause is that
schedule's state (Stage 10 decision 13, OR-9), and a workflow with no schedule
carries TriggerMode manual_only. Production's warehouse workflow has no Staging
twin: Staging has no warehouse (Stage 19 decision 16 (b)).""")

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
        rep.h1("4. The workflows' execution roles: the project's role, its boundary and policies")
        if role_table:
            rep.tabulate(
                ["ENV\tWORKFLOW\tROLE\tBOUNDARY\tPROJECT\tAWSDS POLICIES"]
                + ["\t".join(r) for r in role_table]
            )
        else:
            rep.line("No workflow, so no execution role.")
        for env, roles in release_t_roles.items():
            for role in roles or []:
                rep.line(f"{env}: release T's role {role} exists (OR-3).")
        rep.text(f"""
A workflow the CLI creates runs as its project's role, the Tooling environment's,
tagged AmazonDataZoneProject and AmazonDataZoneDomain. The contract: a role named
for that project, under awsds-<env>-project-boundary, whose trust names
{WF_PRINCIPAL}, carrying what <env>/studio/ attaches (the
workflows' grant, the person-session deny and, in Production, the warehouse load).
The AWS managed policies on the role are not listed. Release T ran each workflow as
a role of its own, awsds-<env>-wf-*; OR-3 fails on one.""")

        # ==============================================================================
        rep.h1("5. Log groups and retention (D28 item 5)")
        if lg_rows:
            rep.tabulate(["ENV\tLOG GROUP\tRETENTION (DAYS)"] + ["\t".join(r) for r in lg_rows])
        else:
            rep.line(f"No group under {AUTO_LOG_PREFIX}.")
        rep.text("""
The CLI names each workflow's group /aws/mwaa-serverless/<domain id>-<project id>/<workflow>
in CreateWorkflow, the service creates it with no retention, and the group outlives
its workflow (SUP-254). OR-2 fails on every group here with no retention; EXC-25
expects it until Stage 19 decision 27 is applied.""")

        # ==============================================================================
        rep.h1("6. The EventBridge rules, and the chain layer above the workflows")
        if rule_rows:
            rep.tabulate(["ENV\tRULE\tSTATE"] + ["\t".join(r) for r in rule_rows])
        else:
            rep.line("No awsds-<env>-wf-* or model-approval rule (pre-step-3.1/5.3).")
        rep.line()
        chain_table = []
        for env, layer in chains.items():
            chain_table.append(
                (env, f"awsds-{env}-chains", "group", "present" if layer["group"] else "absent")
            )
            chain_table.append(
                (
                    env,
                    f"/aws/vendedlogs/states/awsds-{env}-chains",
                    "log group",
                    layer["log_retention"] or "absent",
                )
            )
            for role, found in layer["roles"].items():
                reading = f"boundary {found[0]}, {len(found[3])} managed" if found else "absent"
                chain_table.append((env, role, "role", reading))
            for machine, (schedule, rule) in layer["machines"].items():
                chain_table.append((env, machine, "chain", f"schedule {schedule}, rule {rule}"))
        if chain_table:
            rep.tabulate(["ENV\tNAME\tPIECE\tREADING"] + ["\t".join(r) for r in chain_table])
        rep.text("""
A chain's state machine finds each workflow by name, starts it with the
application's stage variables, which it reads from
/datascience/<env>/applications/<application>/stage-variables, and waits for the
run; its Scheduler schedule starts the machine, and the schedule's state is the
pause lever (steps 3.4-3.7, D41). Staging's schedules are DISABLED by design
(Stage 10 decision 19), and Production's between sittings since 2026-10-25, since a
run needs workloads-egress/'s [E] endpoints; a sitting that wants the scheduled
runs turns them on by a commit (step 6.1). A failure rule passes OR-4 only when its
pattern names both MWAA Serverless run-failure detail types the service emits.""")

        # ==============================================================================
        rep.h1("7. Recent runs")
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
A run a chain's machine starts reads ON_DEMAND, the type of a StartWorkflowRun
call, scheduled runs included (verification xxiv, read 2026-10-25); the unattended
proof is CloudTrail's StartExecution by the Scheduler's role. The type
is read per run with get-workflow-run: list-workflow-runs returns RunType null for
every run (measured 2026-10-10). Runs and their history die with the workflow: one
deleted and created again takes a new suffix and an empty history, and its log
group keeps the runs' logs (SUP-253, SUP-254).""")

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
        rep.h1("9. The service-linked role, and the definitions")
        if slr_rows:
            rep.tabulate(["ENV\t" + SLR_NAME] + ["\t".join(r) for r in slr_rows])
        else:
            rep.line(f"{SLR_NAME}: not measured.")
        rep.line()
        if def_table:
            rep.tabulate(
                ["ENV\tWORKFLOW\tDEFINITION\tCODE SNAPSHOTTED AT"]
                + ["\t".join(r) for r in def_table]
            )
        else:
            rep.line("No workflow definition read.")
        rep.text("""
The SLR appears at the first CreateWorkflow in each account (Lesson 17), Staging
before Production - 0.3 records the absent baseline, 1.6 the enumerated arrival.
The CLI uploads each definition under its project's shared/ prefix in the account's
projects bucket, awsds-<env>-smus-projects, and names no S3 version. The last
column is get-workflow's CodeSnapshottedAt as read, "-" where it is null. Release T's
rendered copies under applications/ in each account's outputs bucket are not read
here.""")

        # ==============================================================================
        rep.h1("10. The registry record: who registered, who approved (INT-07)")
        if reg_rows:
            rep.tabulate(["TIME\tEVENT\tCALLER"] + ["\t".join(r) for r in reg_rows[:25]])
            if len(reg_rows) > 25:
                rep.line(f"... and {len(reg_rows) - 25} more event(s).")
        if reg_unread:
            rep.line(
                f"{' and '.join(reg_unread)} not read to the last page (section 14): an "
                "absence here proves nothing."
            )
        elif not reg_rows:
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
  OR-1  each account's workflows exist, each the CLI's in the deployment project,
        READY with no cron (Stage 19 step 4.6, Stage 10 decision 13)
  OR-2  each workflow logs to the CLI's group for it, and every group under
        /aws/mwaa-serverless/ carries a retention (D28 item 5, SUP-254; EXC-25)
  OR-3  each workflow runs as its project's role, under the project boundary, its
        trust naming airflow-serverless, carrying <env>/studio/'s policies; no
        release T role; NetworkConfiguration set, two AZs, no default route (1.2)
  OR-4  each workflow heard by a failure rule matching its ARN; the *-failed rules
        and awsds-prod-model-approval ENABLED, each workflow rule's pattern naming
        the service's two run-failure detail types (Stage 10 3.1, 5.3)
  OR-5  definitions under the project's shared/ prefix in the account's projects
        bucket (Stage 19 step 4.6)
  OR-6  no provisioned MWAA environment in any account read (step 4.3)
  OR-7  workflow versions vs the 50-version quota (risk 4)
  OR-8  every registry write was awsds-deploy-prod (INT-07, Stage 9 3.2)
  OR-9  the chain layer: the group, the machines' log group with retention, the
        chain roles (one service each, no managed policy, no job or data
        action), one machine at least, each machine's schedule and failure rule
        (steps 3.4-3.7)""")

        # ==============================================================================
        rep.h1("13. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 12 as a pass.

  - Sandbox's workflows bill task-hours there and are not read here;
    ./aws/sandbox-orchestration.py reads them. OR-6 still reads Sandbox.
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
