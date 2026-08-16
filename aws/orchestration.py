#!/usr/bin/env -S uv run --quiet
# orchestration.py - Stage 10's evidence, both orchestrators read side by side: the MWAA
# Serverless workflows (design A) and the Scheduler->Step Functions pair (design B) with
# their per-workflow roles (boundary, trust, the D13 absences, NetworkConfiguration), the
# named log groups with retention (D28 item 5), the three EventBridge rules, recent runs
# (the schedule evidence), the no-provisioned-environment reading (the burn), the
# definitions home, and the registry's register/approve record (INT-04 consumed).
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/orchestration.py                   # every awsds-* profile
#             ./aws/orchestration.py awsds-infra-prod  # only the ones named
#             python3 aws/orchestration.py -           # CloudShell, ambient credentials
#   writes:   aws/output/orchestration.txt   (untracked - see .gitignore)
#   reads:    mwaa-serverless:ListWorkflows, GetWorkflow, ListWorkflowRuns,
#             ListWorkflowVersions; states:ListStateMachines, DescribeStateMachine,
#             ListExecutions; scheduler:ListSchedules; mwaa:ListEnvironments;
#             logs:DescribeLogGroups; events:ListRules, ListTargetsByRule; iam:GetRole,
#             ListRoles, ListRolePolicies, GetRolePolicy; s3:ListObjectsV2;
#             datazone:ListDomains, ListEnvironmentBlueprintConfigurations,
#             GetEnvironmentBlueprint; cloudtrail:LookupEvents; sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject spans
# accounts by design: the workflow is authored in Development's project (D21), runs in
# Production (D17), and the provisioned-MWAA burn reading (OR-6) is only meaningful measured
# in EVERY account - the OnDemand Workflows blueprint would create a fee-bearing environment
# in a member account, not in Production. Section 1 pays the rule back with the caller ARN
# of every profile.
#
# CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - workflow resources, roles and failure rules carry awsds-prod-wf- (steps 1A/1B/3)
#   - log groups: /awsds/prod/wf/ (design A) and /aws/vendedlogs/states/awsds-prod-wf-
#     (design B - the documented vended-logs prefix) (steps 1A.1, 1B.2)
#   - the definitions home is s3://awsds-prod-outputs/workflows/ (step 2.4, decision 1)
#   - the approval rule is awsds-prod-model-approval (step 5.3)
#   - the lake buckets carry awsds-data- (Stage 5), so OR-3 can read D13's absence
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The Studio's serverless-Workflows surface (step 0.4) is console-recorded; no stable
#     public API names it (research flag, 2026-08-16). The stage log carries it.
#   - The behavioural proofs (an unattended SCHEDULED run, the failure rules firing, the
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

# Where each half lives (D14, D17, D22).
PROD_PROFILE = "awsds-infra-prod"
DATA_PROFILE = "awsds-infra-data"

# The contracts (see header).
WF_FRAG = "awsds-prod-wf-"
LOG_PREFIX_A = "/awsds/prod/wf/"
LOG_PREFIX_B = "/aws/vendedlogs/states/awsds-prod-wf-"
APPROVAL_RULE = "awsds-prod-model-approval"
DEF_BUCKET = "awsds-prod-outputs"
DEF_PREFIX = "workflows/"
LAKE_FRAG = "awsds-data-"
SLR_NAME = "AWSServiceRoleForAmazonMWAAServerless"
LOOKUP_MAX = 50  # CloudTrail lookup page - registry writes are rare at lab scale
RUNS_MAX = 10  # recent runs per workflow / state machine


def _stmts(doc: dict) -> list:
    stmts = (doc or {}).get("Statement", [])
    return [stmts] if isinstance(stmts, dict) else list(stmts)


def _as_list(x) -> list:
    if x is None:
        return []
    return [x] if isinstance(x, str) else list(x)


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    prod_live = PROD_PROFILE in live

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------- design A: the serverless workflows (prod)
    wf_rows: list = []  # (name, status, trigger mode, cron, engine ver count)
    wf_detail: dict = {}  # name -> {arn, role, log_group, net, def_bucket, def_key, versions}
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (serverless workflows) ...")
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
        if res.tolerated:
            wf_rows = []
        elif not res.ok:
            logerr(PROD_PROFILE, "mwaa-serverless list-workflows", res.stderr)
        else:
            for name, arn, status, tmode in json.loads(res.stdout or "[]"):
                if WF_FRAG not in str(name):
                    continue
                r = cli.run(
                    "mwaa-serverless",
                    "get-workflow",
                    "--workflow-arn",
                    arn,
                    "--query",
                    "[RoleArn,LoggingConfiguration.LogGroupName,"
                    "NetworkConfiguration.SubnetIds,NetworkConfiguration.SecurityGroupIds,"
                    "DefinitionS3Location.Bucket,DefinitionS3Location.ObjectKey,"
                    "ScheduleConfiguration.CronExpression]",
                    "--output",
                    "json",
                    log=False,
                )
                role = log_group = cron = ""
                subnets: list = []
                sgs: list = []
                def_bucket = def_key = ""
                if r.ok and r.stdout:
                    role, log_group, subnets, sgs, def_bucket, def_key, cron = json.loads(r.stdout)
                v = cli.run(
                    "mwaa-serverless",
                    "list-workflow-versions",
                    "--workflow-arn",
                    arn,
                    "--query",
                    "length(WorkflowVersions)",
                    "--output",
                    "text",
                    log=False,
                )
                versions = v.stdout.strip() if v.ok else "?"
                wf_rows.append((str(name), str(status), str(tmode), str(cron or "-"), versions))
                wf_detail[str(name)] = {
                    "arn": str(arn),
                    "role": str(role or ""),
                    "log_group": str(log_group or ""),
                    "subnets": _as_list(subnets),
                    "sgs": _as_list(sgs),
                    "def_bucket": str(def_bucket or ""),
                    "def_key": str(def_key or ""),
                    "versions": versions,
                }

    # ------------------------------- design B: state machines and schedules (prod)
    sm_rows: list = []  # (name, type, log level, log group tail, role tail)
    sm_detail: dict = {}  # name -> {arn, role, log_group}
    sched_rows: list = []  # (name, state, target tail)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (state machines, schedules) ...")
        res = cli.run(
            "stepfunctions",
            "list-state-machines",
            "--query",
            "stateMachines[].[name,stateMachineArn,type]",
            "--output",
            "json",
            log=False,
        )
        for name, arn, sm_type in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            if WF_FRAG not in str(name):
                continue
            r = cli.run(
                "stepfunctions",
                "describe-state-machine",
                "--state-machine-arn",
                arn,
                "--query",
                "[roleArn,loggingConfiguration.level,"
                "loggingConfiguration.destinations[0].cloudWatchLogsLogGroup.logGroupArn]",
                "--output",
                "json",
                log=False,
            )
            role = level = dest = ""
            if r.ok and r.stdout:
                role, level, dest = json.loads(r.stdout)
            dest_tail = str(dest).split(":log-group:", 1)[-1].rstrip(":*") if dest else "(none)"
            sm_rows.append(
                (
                    str(name),
                    str(sm_type),
                    str(level or "OFF"),
                    dest_tail,
                    str(role or "").rsplit("/", 1)[-1],
                )
            )
            sm_detail[str(name)] = {
                "arn": str(arn),
                "role": str(role or ""),
                "log_group": dest_tail,
                "type": str(sm_type),
            }
        res = cli.run(
            "scheduler",
            "list-schedules",
            "--query",
            "Schedules[].[Name,State,GroupName,Target.Arn]",
            "--output",
            "json",
            log=False,
        )
        for name, state, group, target in (
            json.loads(res.stdout or "[]") if res.ok and res.stdout else []
        ):
            if WF_FRAG not in str(name):
                continue
            sched_rows.append(
                (str(name), str(state), str(group), str(target or "").rsplit(":", 1)[-1][:40])
            )

    built = bool(wf_rows or sm_rows or sched_rows)

    # -------------------- the per-workflow roles: boundary, trust, the D13 absences
    role_rows: list = []  # (role, boundary tail, trusted services)
    role_bad: list = []  # (role, what)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "iam",
            "list-roles",
            "--query",
            f"Roles[?contains(RoleName, '{WF_FRAG}')].RoleName",
            "--output",
            "json",
            log=False,
        )
        for role in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
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
                role_rows.append((role, "(read failed)", "-"))
                continue
            boundary, trust = json.loads(r.stdout)
            services: list = []
            for st in _stmts(trust):
                services += _as_list((st.get("Principal", {}) or {}).get("Service"))
                if (st.get("Principal", {}) or {}).get("AWS"):
                    role_bad.append((role, "an AWS principal in a service-role trust policy"))
            btail = str(boundary).rsplit("/", 1)[-1] if boundary else "(none)"
            if not boundary:
                role_bad.append((role, "no permissions boundary (Stage 8 4.1's condition)"))
            # D13 one level up: the orchestrator role holds no lake S3, no GetDataAccess.
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
            for pname in json.loads(pol.stdout or "[]") if pol.ok and pol.stdout else []:
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
                if not (pr.ok and pr.stdout):
                    continue
                for st in _stmts(json.loads(pr.stdout)):
                    if str(st.get("Effect", "")) != "Allow":
                        continue
                    actions = " ".join(_as_list(st.get("Action"))).lower()
                    resources = " ".join(map(str, _as_list(st.get("Resource"))))
                    if "lakeformation:getdataaccess" in actions:
                        role_bad.append((role, f"lakeformation:GetDataAccess in {pname}"))
                    if "s3:" in actions and LAKE_FRAG in resources:
                        role_bad.append((role, f"an s3 allow naming {LAKE_FRAG}* in {pname}"))
            role_rows.append((role, btail, " ".join(sorted(set(services))) or "(none)"))

    # ------------------------------------------ log groups and retention (D28 item 5)
    lg_rows: list = []  # (log group, retention)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        for prefix in (LOG_PREFIX_A, LOG_PREFIX_B, "/aws/mwaa-serverless/"):
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
            for gname, days in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                lg_rows.append((str(gname), str(days) if days else "(never expires)"))

    # ------------------------------ the EventBridge rules: failures + model approval
    rule_rows: list = []  # (rule, state)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "events",
            "list-rules",
            "--query",
            "Rules[].[Name,State]",
            "--output",
            "json",
            log=False,
        )
        for rname, state in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            if WF_FRAG in str(rname) or str(rname) == APPROVAL_RULE:
                rule_rows.append((str(rname), str(state)))

    # ------------------------------------ recent runs, both designs (the schedule evidence)
    run_rows: list = []  # (design, workflow, run/execution, type, status, started)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        for name, d in wf_detail.items():
            res = cli.run(
                "mwaa-serverless",
                "list-workflow-runs",
                "--workflow-arn",
                d["arn"],
                "--max-results",
                str(RUNS_MAX),
                "--query",
                "WorkflowRuns[].[RunId,RunType,RunDetailSummary.Status,RunDetailSummary.StartedAt]",
                "--output",
                "json",
                log=False,
            )
            for rid, rtype, status, started in (
                json.loads(res.stdout or "[]") if res.ok and res.stdout else []
            ):
                run_rows.append(
                    ("A", name, str(rid)[:20], str(rtype), str(status), str(started or "-")[:19])
                )
        for name, d in sm_detail.items():
            res = cli.run(
                "stepfunctions",
                "list-executions",
                "--state-machine-arn",
                d["arn"],
                "--max-results",
                str(RUNS_MAX),
                "--query",
                "executions[].[name,status,startDate]",
                "--output",
                "json",
                log=False,
            )
            for ename, status, started in (
                json.loads(res.stdout or "[]") if res.ok and res.stdout else []
            ):
                run_rows.append(
                    ("B", name, str(ename)[:20], "-", str(status), str(started or "-")[:19])
                )

    # ----------------- provisioned MWAA environments - the burn reading (every account)
    env_rows: list = []  # (profile, environment name)
    for p in live:
        cli = cli_for(p)
        note(f"measuring {p} (provisioned MWAA environments) ...")
        res = cli.run(
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
            if not res.ok and not res.tolerated:
                logerr(p, "mwaa list-environments", res.stderr)
            continue
        for name in json.loads(res.stdout or "[]"):
            env_rows.append((p, str(name)))

    # ------------------------- the service-linked role (Lesson 17 - the 0.3/1.5 pair)
    slr_state = "(not measured)"
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
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
            slr_state = "absent (pre-CreateWorkflow baseline - step 0.3)"
        elif res.ok:
            slr_state = f"present, created {res.stdout.strip()[:19]}"

    # --------------------------------------- the definitions home (step 2.4, decision 1)
    def_rows: list = []  # (key, size)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
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
        if res.ok and not res.tolerated and res.stdout and res.stdout.strip() != "null":
            def_rows = [(str(k), str(s)) for k, s in json.loads(res.stdout)]

    # ---------------- the registry record: who registered, who approved (INT-04 consumed)
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
            for raw in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                try:
                    ev = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                caller = str((ev.get("userIdentity") or {}).get("arn") or "(unknown)")
                when = str(ev.get("eventTime") or "-")
                reg_rows.append((when, ev_name, caller.rsplit("/", 1)[-1][:40]))
                if "awsds-deploy-prod" not in caller:
                    reg_bad.append((ev_name, caller))

    # -------------------- the domain's Workflows surface (Data Governance, read-only)
    bp_rows: list = []  # (blueprint name, enabled regions)
    data_live = DATA_PROFILE in live
    if data_live:
        cli = cli_for(DATA_PROFILE)
        note(f"measuring {DATA_PROFILE} (domain blueprints) ...")
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
            for c in (json.loads(res.stdout or "{}") or {}).get("items", []) if res.ok else []:
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
                bp_rows.append((name, " ".join(c.get("enabledRegions", []) or ["-"])))

    # -------------------------------------------------------------------------- the checks

    # OR-1: the two implementations, whole or absent - a half-built design fails loudly.
    if prod_live:
        if not built:
            checks.note(
                "OR-1",
                "the orchestrators",
                "nothing awsds-prod-wf-* exists - expected before pass 2; [E] between "
                "sessions is D11 working.",
            )
        else:
            if wf_rows:
                for name, status, tmode, cron, _v in wf_rows:
                    checks.ok("OR-1", f"A: {name}", f"{status}, trigger {tmode}, cron {cron}")
            if sm_rows and not sched_rows:
                checks.fail(
                    "OR-1",
                    "design B",
                    "a state machine with no schedule - half of 1B.1 is missing.",
                )
            elif sched_rows and not sm_rows:
                checks.fail(
                    "OR-1",
                    "design B",
                    "a schedule with no state machine - half of 1B.1 is missing.",
                )
            elif sm_rows:
                for name, sm_type, _lv, _dst, _r in sm_rows:
                    if sm_type != "STANDARD":
                        checks.fail(
                            "OR-1",
                            f"B: {name}",
                            f"type {sm_type} - Express supports no .sync pattern and caps "
                            "at 5 minutes (1B.1's documented elimination).",
                        )
                    else:
                        checks.ok("OR-1", f"B: {name}", "STANDARD, schedule present")

    # OR-2: every workflow/machine logs to a NAMED group with retention (D28 item 5);
    # the auto-created /aws/mwaa-serverless/ group is exactly what the item forbids.
    for name, d in wf_detail.items():
        lg = d["log_group"]
        if not lg:
            checks.fail(
                "OR-2",
                f"logging on {name}",
                "no LogGroupName - the service will "
                "auto-create /aws/mwaa-serverless/<id>/ with no expiry (1A.1).",
            )
        elif not lg.startswith(LOG_PREFIX_A):
            checks.fail(
                "OR-2", f"logging on {name}", f"{lg} - outside the {LOG_PREFIX_A} contract."
            )
        else:
            checks.ok("OR-2", f"logging on {name}", lg)
    for name, d in sm_detail.items():
        lg = d["log_group"]
        if lg == "(none)":
            checks.fail("OR-2", f"logging on {name}", "no CloudWatch destination (1B.2).")
        elif not lg.startswith("/aws/vendedlogs/"):
            checks.fail(
                "OR-2",
                f"logging on {name}",
                f"{lg} - outside /aws/vendedlogs/: each such group burns one of the ten "
                "per-Region CloudWatch Logs resource policies (1B.2).",
            )
        else:
            checks.ok("OR-2", f"logging on {name}", lg)
    for gname, days in lg_rows:
        if days == "(never expires)":
            checks.fail("OR-2", f"retention on {gname}", "none set - D28 item 5 sets one.")
    auto_groups = [g for g, _ in lg_rows if g.startswith("/aws/mwaa-serverless/")]
    if auto_groups:
        checks.fail(
            "OR-2",
            "auto-created MWAA groups",
            f"{len(auto_groups)} group(s) under /aws/mwaa-serverless/ - a workflow ran "
            "without 1A.1's named group.",
        )

    # OR-3: the per-workflow roles - boundary, service trust, no data reach (D13 one
    # level up), and design A's NetworkConfiguration present (the non-VPC bypass).
    if role_bad:
        for role, what in sorted(set(role_bad)):
            checks.fail("OR-3", f"role {role}", f"{what}.")
    elif role_rows:
        checks.ok(
            "OR-3",
            "the per-workflow roles",
            f"{len(role_rows)} role(s): bounded, service trust only, no lake reach",
        )
    for name, d in wf_detail.items():
        if not d["subnets"] or not d["sgs"]:
            checks.fail(
                "OR-3",
                f"NetworkConfiguration on {name}",
                "absent - tasks would run in the SERVICE's VPC, outside every endpoint "
                "policy and flow log (1A.1; open question 12's shape).",
            )
        else:
            checks.ok(
                "OR-3",
                f"NetworkConfiguration on {name}",
                f"{len(d['subnets'])} subnet(s), {len(d['sgs'])} SG(s)",
            )

    # OR-4: the failure rules and the approval rule exist and are ENABLED once built.
    if prod_live and built:
        failed_rules = [r for r in rule_rows if r[0].endswith("-failed")]
        if not failed_rules:
            checks.fail("OR-4", "the failure rules", "no awsds-prod-wf-*-failed rule (step 3).")
        for rname, state in rule_rows:
            if state != "ENABLED":
                checks.fail("OR-4", f"rule {rname}", f"state {state} - not watching.")
            else:
                checks.ok("OR-4", f"rule {rname}", "ENABLED")
        if not any(r[0] == APPROVAL_RULE for r in rule_rows):
            checks.note(
                "OR-4",
                f"rule {APPROVAL_RULE}",
                "absent - expected before step 5.3.",
            )

    # OR-5: the definitions home holds objects under the contract prefix once A exists.
    for name, d in wf_detail.items():
        if not d["def_bucket"]:
            continue
        if d["def_bucket"] != DEF_BUCKET or not d["def_key"].startswith(DEF_PREFIX):
            checks.fail(
                "OR-5",
                f"definition of {name}",
                f"s3://{d['def_bucket']}/{d['def_key']} - outside "
                f"s3://{DEF_BUCKET}/{DEF_PREFIX} (decision 1).",
            )
        else:
            checks.ok("OR-5", f"definition of {name}", f"s3://{d['def_bucket']}/{d['def_key']}")

    # OR-6: no provisioned MWAA environment anywhere - 0.29 USD/h each. If step 4's
    # fallback is deliberately in use, it is [E] in the same sitting; this is its meter.
    if env_rows:
        for p, name in env_rows:
            checks.fail(
                "OR-6",
                f"MWAA environment in {p}",
                f"{name} - a standing environment fee (PRICING 1.1); step 4's fallback "
                "is same-sitting [E], and the OnDemand Workflows blueprint is refused (0.4).",
            )
    elif live:
        checks.ok("OR-6", "provisioned MWAA environments", f"none in {len(live)} account(s)")

    # OR-7: version churn against the 50-version quota (risk 4).
    for name, d in wf_detail.items():
        try:
            n = int(d["versions"])
        except (TypeError, ValueError):
            continue
        if n >= 40:
            checks.fail("OR-7", f"versions of {name}", f"{n}/50 - the quota is close (risk 4).")
        else:
            checks.ok("OR-7", f"versions of {name}", f"{n}/50")

    # OR-8: every registry write in the record was the deploy role (INT-04 consumed;
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
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("ORCHESTRATION - the Stage 10 evidence: both designs, roles, rules, runs")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/orchestration.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. Design A - the serverless workflows (Production)
  3. Design B - state machines and schedules (Production)
  4. The per-workflow roles: boundary, trust, the D13 absences
  5. Log groups and retention (D28 item 5)
  6. The EventBridge rules: failures and the approval rule
  7. Recent runs, both designs (the schedule evidence)
  8. Provisioned MWAA environments - the burn reading
  9. The service-linked role, and the definitions home
 10. The registry record: who registered, who approved (INT-04)
 11. The domain's blueprint configurations (Data Governance)
 12. CHECKS
 13. The accounts nothing here is measuring
 14. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 10 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - AN ABSENT slice is [E] working between sessions, not an outage. What must NOT
    appear at rest is a provisioned MWAA environment (OR-6) or an auto-created
    /aws/mwaa-serverless/ log group (OR-2).
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
        rep.h1("2. Design A - the serverless workflows (Production)")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        elif wf_rows:
            rep.tabulate(
                ["NAME\tSTATUS\tTRIGGER\tCRON\tVERSIONS"] + ["\t".join(r) for r in wf_rows]
            )
        else:
            rep.line(f"No {WF_FRAG}* workflow. Pre-pass-2, or [E] down between sessions.")
        rep.text("""
The cron column IS the schedule - it lives in the YAML definition and the service
runs it through EventBridge Scheduler internally; TriggerMode is the pause lever.""")

        # ==============================================================================
        rep.h1("3. Design B - state machines and schedules (Production)")
        if sm_rows:
            rep.tabulate(
                ["NAME\tTYPE\tLOG LEVEL\tLOG GROUP\tROLE"] + ["\t".join(r) for r in sm_rows]
            )
        else:
            rep.line(f"No {WF_FRAG}* state machine.")
        rep.line()
        if sched_rows:
            rep.tabulate(["SCHEDULE\tSTATE\tGROUP\tTARGET"] + ["\t".join(r) for r in sched_rows])
        else:
            rep.line(f"No {WF_FRAG}* schedule.")

        # ==============================================================================
        rep.h1("4. The per-workflow roles: boundary, trust, the D13 absences")
        if role_rows:
            rep.tabulate(["ROLE\tBOUNDARY\tTRUSTED SERVICE(S)"] + ["\t".join(r) for r in role_rows])
        else:
            rep.line(f"No {WF_FRAG}* role.")
        rep.text("""
The contract (1A.2/1B.2): service principals only, a permissions boundary (the
pipeline creates these under Stage 8 4.1's condition), and NO data reach - no
s3 allow naming a lake bucket, no lakeformation:GetDataAccess. The orchestrator
starts jobs; awsds-prod-job-exec touches data (D13 one level up).""")

        # ==============================================================================
        rep.h1("5. Log groups and retention (D28 item 5)")
        if lg_rows:
            rep.tabulate(["LOG GROUP\tRETENTION (DAYS)"] + ["\t".join(r) for r in lg_rows])
        else:
            rep.line("No workflow log group yet.")

        # ==============================================================================
        rep.h1("6. The EventBridge rules: failures and the approval rule")
        if rule_rows:
            rep.tabulate(["RULE\tSTATE"] + ["\t".join(r) for r in rule_rows])
        else:
            rep.line("No awsds-prod-wf-* or model-approval rule (pre-step-3/5.3).")

        # ==============================================================================
        rep.h1("7. Recent runs, both designs (the schedule evidence)")
        if run_rows:
            rep.tabulate(
                ["DESIGN\tWORKFLOW\tRUN\tTYPE\tSTATUS\tSTARTED"]
                + ["\t".join(r) for r in run_rows[:40]]
            )
            if len(run_rows) > 40:
                rep.line(f"... and {len(run_rows) - 40} more row(s).")
        else:
            rep.line("No recorded run.")
        rep.text("""
Verification (v) wants at least one TYPE=SCHEDULED row per design with nobody at
the keyboard. Runs and their history die with the [E] slice (Lesson 4) - 6.3
writes the disposition into the log before the first make down.""")

        # ==============================================================================
        rep.h1("8. Provisioned MWAA environments - the burn reading")
        if env_rows:
            rep.tabulate(["PROFILE\tENVIRONMENT"] + ["\t".join(r) for r in env_rows])
        else:
            rep.line("None anywhere measured - the expected steady state (OR-6).")
        rep.text("""
An environment bills 0.29 USD/h (mw1.micro) for existing. Step 4's fallback is
[E] in the same sitting; the OnDemand Workflows blueprint is refused at 0.4.""")

        # ==============================================================================
        rep.h1("9. The service-linked role, and the definitions home")
        rep.line(f"{SLR_NAME}: {slr_state}")
        rep.line()
        if def_rows:
            rep.tabulate(
                [f"s3://{DEF_BUCKET}/{DEF_PREFIX}* KEY\tSIZE"] + ["\t".join(r) for r in def_rows]
            )
        else:
            rep.line(f"No object under s3://{DEF_BUCKET}/{DEF_PREFIX} (pre-2.4).")
        rep.text("""
The SLR appears at the FIRST CreateWorkflow (Lesson 17) - 0.3 records the absent
baseline, 1.5 the enumerated arrival. The definitions home is decision 1's:
versioned, CMK-protected, perimeter-branched since Stage 9 1.1.""")

        # ==============================================================================
        rep.h1("10. The registry record: who registered, who approved (INT-04)")
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
        rep.h1("11. The domain's blueprint configurations (Data Governance)")
        if bp_rows:
            rep.tabulate(["BLUEPRINT\tENABLED REGIONS"] + ["\t".join(r) for r in bp_rows])
        else:
            rep.line("No V2 domain, or no blueprint configuration (or the profile was absent).")
        rep.text("""
Context for step 0.4, not a check: the serverless-Workflows surface is recorded
from the console (no stable public API names it). What OR-6 refuses is the
provisioned consequence - a fee-bearing environment appearing in any account.""")

        # ==============================================================================
        rep.h1("12. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  OR-1  both implementations whole: A READY; B machine STANDARD + schedule (1A/1B)
  OR-2  named log groups with retention; no /aws/mwaa-serverless/ orphan (D28 item 5)
  OR-3  per-workflow roles bounded, service trust, no lake reach; A's
        NetworkConfiguration set (1A.2, 1B.2, open question 12's shape)
  OR-4  the *-failed rules and awsds-prod-model-approval ENABLED (steps 3, 5.3)
  OR-5  definitions under s3://awsds-prod-outputs/workflows/ (2.4, decision 1)
  OR-6  no provisioned MWAA environment anywhere (the burn; step 4 is [E])
  OR-7  workflow versions vs the 50-version quota (risk 4)
  OR-8  every registry write was awsds-deploy-prod (INT-04, Stage 9 3.2)""")

        # ==============================================================================
        rep.h1("13. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 12 as a pass.

  - `Staging` has no profile until the vend - the model chain's Staging leg
    (5.4) and the full promotion (6.1) are measured only after it.
  - Every Sandbox beyond unit 1 has no profile until Stage 14 (D35).
  - GitLab's objects (the lint job, the approval manual job) live behind
    gitlab.prod.internal - the stage log records them.
  - The Studio's serverless-Workflows surface is console-recorded (0.4);
    Development's project-side runs bill task-hours there and are not listed
    here - this file reads Production's workflows only.""")

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
