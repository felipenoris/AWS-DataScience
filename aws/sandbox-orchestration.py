#!/usr/bin/env -S uv run --quiet
# sandbox-orchestration.py - Stage 6i's evidence: the exercise's MWAA Serverless workflows in
# the Sandbox project, the processing jobs they start, and the project storage they touch.
# The workflows (role, private network, project key, where the definition and the Code object
# live, the versions), their recent runs and task instances, each demo-devenv- processing job
# read against the D13 boundary's four job settings and the registered house image, the log
# groups the exercise makes, the shared/orchestration-demo/ prefixes, and CloudTrail's record
# of who created each workflow and each job, and through which door.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             and an AWS CLI that knows the workflow's Code field (2.37.12 does; 2.36.18
#             did not - Stage 6i step 0.2).
#   run:      ./aws/sandbox-orchestration.py                        # the Sandbox profile
#             ./aws/sandbox-orchestration.py awsds-infra-sandbox-1  # the same, named
#             python3 aws/sandbox-orchestration.py -                # CloudShell, ambient
#   writes:   aws/output/sandbox-orchestration.txt, and every version of each contract
#             workflow's definition under aws/output/sandbox-orchestration/<workflow>/,
#             once as served and once with the account ids replaced by placeholders, which
#             is the copy Stage 6i decision 1 commits (untracked - see .gitignore)
#   reads:    iam:ListRoles, GetRole; kms:ListAliases; mwaa-serverless:ListWorkflows,
#             GetWorkflow, ListWorkflowVersions, ListWorkflowRuns, GetWorkflowRun,
#             ListTaskInstances, GetTaskInstance; ec2:DescribeSubnets, DescribeRouteTables,
#             DescribeSecurityGroups; sagemaker:DescribeImageVersion, ListProcessingJobs,
#             DescribeProcessingJob, ListTags; logs:DescribeLogGroups; s3api:ListObjectsV2,
#             HeadObject; cloudtrail:LookupEvents; sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# One profile: the workflows, the jobs, the project role, the project bucket and the trail
# events are all in the Sandbox account, so awsds-infra-sandbox-1 (the infrastructure user,
# InfrastructureAccess in Sandbox) reads every one of them. The image lives in Production's
# registry; its digest is read from the image version registered in Sandbox, which is what
# a space and a job resolve.
#
# The project is read from the project roles' tags (AmazonDataZoneProject, ...Domain,
# KmsKeyId, DomainBucketName), never from this file, and a workflow belongs to the project
# whose role it runs as.
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - The container's own output: it goes to /aws/sagemaker/ProcessingJobs, which section 7
#     lists and the stage's read steps open by job name.
#   - The portal's editor and its fields (Stage 6i verification i) - a person reads them.
#   - Whether a definition's paste-ready config matches what the portal saved: the saved
#     definitions are the record, the comparison is the stage's.
#   - "Not built yet" is a note, never a fail.

from __future__ import annotations

import json
import re
import sys
from datetime import datetime

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "sandbox-orchestration.txt"
DEFS_DIR = "sandbox-orchestration"

SANDBOX_PROFILE = "awsds-infra-sandbox-1"

# Contracts named in the stage file, so a rename fails loudly rather than silently.
PROJECT_ROLE_PREFIX = "datazone_usr_role_"
KEY_ALIAS = "alias/awsds-sandbox-project"
PRIVATE_SUBNET_PREFIX = "awsds-sandbox-private-"
CODE_DIR = "awsds-demo-job/"  # under each project's shared/: the code demo-devenv-job's job reads
DEMO_DIR = "orchestration-demo/"  # under each project's shared/: each variant's inbox/ and outbox/
WORKFLOWS = {  # workflow name -> variant, which is also its prefix under DEMO_DIR
    "demo-devenv-job": "devenv",
    "demo-python-operator": "python",
    "demo-bash-operator": "bash",
}
# demo-bash-operator has two versions, told apart by a task id. The probe runs inline commands
# and must carry no Code object, or it is no control for decision 7; the exercise runs the
# package from its Code object. The PyPI negative is in both, and it must FAIL.
BASH_PROBE_TASK = "caller_identity"
BASH_COMMAND_TASK = "run_command"
BASH_NEGATIVE_TASK = "reach_pypi"
JOB_PREFIX = "demo-devenv-"
HOUSE_IMAGE = "awsds-sandbox-dev-env"
WORKER_SESSION = "AmazonMWAAServerless"
PROCESSING_LOG_GROUP = "/aws/sagemaker/ProcessingJobs"
WF_LOG_PREFIX = "/aws/mwaa-serverless/"
PACKAGE_MARKER = "src/awsds_demo_job/__main__.py"  # the project's entry point, under CODE_DIR

RUNS_MAX = 10  # recent runs read per workflow
JOBS_MAX = 20  # recent demo-devenv- jobs
LOOKUP_MAX = 50  # CloudTrail page per event name

ABSENT = "NoSuchEntity|ResourceNotFound|ValidationException.*does not exist|NoSuchKey|Not Found"


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _seconds(start: str | None, end: str | None) -> int | None:
    a, b = _ts(start), _ts(end)
    if a is None or b is None:
        return None
    return int((b - a).total_seconds())


def _billed_minutes(seconds: int | None) -> float:
    """MWAA Serverless bills each task for its duration with a one-minute minimum."""
    if seconds is None:
        return 0.0
    return max(60, seconds) / 60.0


def _task_attempt(instance_id: str) -> tuple:
    """`ex_<uuid>_<task id>_<attempt>` -> (`<task id>`, attempt); the shape read 2026-10-10."""
    m = re.match(r"^ex_[0-9a-f-]{36}_(.+)_(\d+)$", instance_id)
    return (m.group(1), int(m.group(2))) if m else (instance_id, 0)


def _task_id(instance_id: str) -> str:
    return _task_attempt(instance_id)[0]


def has_task(definition: str, task: str) -> bool:
    """Whether a workflow definition declares a task of that id. The definition is YAML and this
    script parses none: a task id is a mapping key alone on its line, as the portal saves it."""
    return re.search(rf"^\s+{re.escape(task)}:\s*$", definition, re.M) is not None


def last_attempts(task_instances: list) -> dict:
    """Task id -> the status of its highest attempt. A retried task lists every attempt,
    and the listing's order is not the attempts' order."""
    best = {}
    for t in task_instances:
        task, attempt = _task_attempt(t.get("TaskInstanceId", ""))
        if task not in best or attempt > best[task][0]:
            best[task] = (attempt, t.get("Status", "-"))
    return {task: status for task, (_a, status) in best.items()}


def sanitize(text: str, known: dict) -> str:
    """Every 12-digit account id becomes a placeholder: the known ones by name, any other as
    <ACCOUNT_ID>. A 13-digit run (the portal's epoch-ms workflow names) is left alone."""

    def repl(m: re.Match) -> str:
        return known.get(m.group(0), "<ACCOUNT_ID>")

    return re.sub(r"(?<!\d)\d{12}(?!\d)", repl, text)


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)
    defs_root = ctx.out_dir / DEFS_DIR

    selected = list(argv) if argv else [SANDBOX_PROFILE]
    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]
    checks = Checks()

    cli = AwsCli(profile=live[0].profile, region=context.REGION, errors=errors, echo_profile=True)
    account = live[0].account

    def logerr(what: str, err: str) -> None:
        errors.entries.append(f"[{cli.label}] aws {what}\n    {head2(err)}")

    def run_json(*args: str, tolerate: str | None = None):
        res = cli.run(*args, "--output", "json", log=False, tolerate=tolerate)
        if res.tolerated:
            return None
        if not res.ok:
            logerr(" ".join(args[:3]), res.stderr or res.stdout)
            return None
        return json.loads(res.stdout or "{}")

    note(f"measuring {cli.label} ...")

    # ------------------------------------------------------------------ the project(s)
    projects = {}  # role name -> dict
    roles = run_json(
        "iam",
        "list-roles",
        "--query",
        f"Roles[?starts_with(RoleName, '{PROJECT_ROLE_PREFIX}')].RoleName",
    )
    for rname in sorted(roles or []):
        role = run_json("iam", "get-role", "--role-name", rname)
        if not role:
            continue
        r = role.get("Role", {})
        tags = {t["Key"]: t["Value"] for t in r.get("Tags", [])}
        key_id = tags.get("KmsKeyId", "")
        aliases = run_json("kms", "list-aliases", "--key-id", key_id) if key_id else None
        domain, project = (
            tags.get("AmazonDataZoneDomain", ""),
            tags.get("AmazonDataZoneProject", ""),
        )
        projects[rname] = {
            "role": rname,
            "arn": r.get("Arn", ""),
            "boundary": (r.get("PermissionsBoundary") or {}).get("PermissionsBoundaryArn", ""),
            "project": project,
            "domain": domain,
            "key_id": key_id,
            "key_aliases": [a.get("AliasName", "") for a in (aliases or {}).get("Aliases", [])],
            "bucket": tags.get("DomainBucketName", ""),
            "shared": f"{domain}/{project}/shared/",
            "defs": f"{domain}/{project}/dev/workflows/",
        }
    by_arn = {p["arn"]: p for p in projects.values()}

    # ------------------------------------------------------------------ the house image
    image = run_json(
        "sagemaker", "describe-image-version", "--image-name", HOUSE_IMAGE, tolerate=ABSENT
    )
    container_image = (image or {}).get("ContainerImage", "")
    image_digest = container_image.split("@", 1)[1] if "@" in container_image else ""
    registry = container_image.split(".", 1)[0] if container_image else ""
    placeholders = {}
    if account:
        placeholders[account] = "<SANDBOX_ACCOUNT_ID>"
    if registry and registry.isdigit():
        placeholders.setdefault(registry, "<REGISTRY_ACCOUNT_ID>")

    # ------------------------------------------------------------------ the workflows
    listed = run_json("mwaa-serverless", "list-workflows") or {}
    all_wfs = listed.get("Workflows", [])
    # A name is not unique: the service appends a suffix to the ARN, and one portal save made two
    # workflows with one name 2 s apart (measured 2026-10-10). The newest is read in detail; SO-1
    # fails on the duplicates.
    same_name = {}
    for w in all_wfs:
        same_name.setdefault(w.get("Name"), []).append(w)
    for group in same_name.values():
        group.sort(key=lambda w: w.get("CreatedAt", ""), reverse=True)
    wf_by_name = {name: group[0] for name, group in same_name.items()}
    wfs = {}  # contract name -> details
    for name, variant in WORKFLOWS.items():
        w = wf_by_name.get(name)
        if w is None:
            continue
        arn = w.get("WorkflowArn", "")
        got = run_json("mwaa-serverless", "get-workflow", "--workflow-arn", arn) or {}
        versions = (
            run_json("mwaa-serverless", "list-workflow-versions", "--workflow-arn", arn) or {}
        ).get("WorkflowVersions", [])
        versions.sort(key=lambda v: v.get("CreatedAt", ""))
        wfs[name] = {
            "variant": variant,
            "arn": arn,
            "summary": w,
            "detail": got,
            "versions": versions,
        }

    # ------------------------------------------------------------------ network objects
    subnet_ids = sorted(
        {
            s
            for d in wfs.values()
            for s in (d["detail"].get("NetworkConfiguration") or {}).get("SubnetIds", [])
        }
    )
    sg_ids = sorted(
        {
            s
            for d in wfs.values()
            for s in (d["detail"].get("NetworkConfiguration") or {}).get("SecurityGroupIds", [])
        }
    )

    jobs = []
    listed_jobs = (
        run_json(
            "sagemaker",
            "list-processing-jobs",
            "--name-contains",
            JOB_PREFIX,
            "--sort-by",
            "CreationTime",
            "--sort-order",
            "Descending",
            "--max-results",
            str(JOBS_MAX),
        )
        or {}
    )
    for summary in listed_jobs.get("ProcessingJobSummaries", []):
        jname = summary.get("ProcessingJobName", "")
        if not jname.startswith(JOB_PREFIX):
            continue
        desc = (
            run_json("sagemaker", "describe-processing-job", "--processing-job-name", jname) or {}
        )
        tags = (
            run_json(
                "sagemaker",
                "list-tags",
                "--resource-arn",
                desc.get("ProcessingJobArn", summary.get("ProcessingJobArn", "")),
            )
            or {}
        )
        desc["_tags"] = {t["Key"]: t["Value"] for t in tags.get("Tags", [])}
        jobs.append(desc)
        vpc = (desc.get("NetworkConfig") or {}).get("VpcConfig") or {}
        subnet_ids = sorted(set(subnet_ids) | set(vpc.get("Subnets", [])))
        sg_ids = sorted(set(sg_ids) | set(vpc.get("SecurityGroupIds", [])))

    subnets = {}
    if subnet_ids:
        got = run_json("ec2", "describe-subnets", "--subnet-ids", *subnet_ids) or {}
        for s in got.get("Subnets", []):
            name = next((t["Value"] for t in s.get("Tags", []) if t["Key"] == "Name"), "-")
            subnets[s["SubnetId"]] = {
                "name": name,
                "az": s.get("AvailabilityZoneId", "-"),
                "vpc": s.get("VpcId", ""),
            }
    default_route = {}  # subnet id -> True when its route table carries a default route
    for sid, s in subnets.items():
        rts = (
            run_json(
                "ec2",
                "describe-route-tables",
                "--filters",
                f"Name=association.subnet-id,Values={sid}",
            )
            or {}
        ).get("RouteTables", [])
        if not rts:
            rts = (
                run_json(
                    "ec2",
                    "describe-route-tables",
                    "--filters",
                    f"Name=vpc-id,Values={s['vpc']}",
                    "Name=association.main,Values=true",
                )
                or {}
            ).get("RouteTables", [])
        default_route[sid] = any(
            r.get("DestinationCidrBlock") == "0.0.0.0/0"
            or r.get("DestinationIpv6CidrBlock") == "::/0"
            for rt in rts
            for r in rt.get("Routes", [])
        )
    sgs = {}
    if sg_ids:
        got = run_json("ec2", "describe-security-groups", "--group-ids", *sg_ids) or {}
        for g in got.get("SecurityGroups", []):
            tags = {t["Key"]: t["Value"] for t in g.get("Tags", [])}
            sgs[g["GroupId"]] = {
                "name": g.get("GroupName", "-"),
                "project": tags.get("AmazonDataZoneProject", ""),
            }

    # ------------------------------------------------------------------ runs and task instances
    runs = {}  # contract name -> list of run dicts, newest first
    for name, d in wfs.items():
        listed_runs = (
            run_json("mwaa-serverless", "list-workflow-runs", "--workflow-arn", d["arn"]) or {}
        ).get("WorkflowRuns", [])
        listed_runs.sort(
            key=lambda r: (r.get("RunDetailSummary") or {}).get("CreatedOn", ""), reverse=True
        )
        out = []
        for r in listed_runs[:RUNS_MAX]:
            rid = r.get("RunId", "")
            detail = (
                run_json(
                    "mwaa-serverless",
                    "get-workflow-run",
                    "--workflow-arn",
                    d["arn"],
                    "--run-id",
                    rid,
                )
                or {}
            )
            tis = (
                run_json(
                    "mwaa-serverless",
                    "list-task-instances",
                    "--workflow-arn",
                    d["arn"],
                    "--run-id",
                    rid,
                )
                or {}
            ).get("TaskInstances", [])
            out.append({"id": rid, "detail": detail, "tasks": tis})
        runs[name] = out

    # ------------------------------------------------------------------ log groups
    log_groups = {}
    for prefix in (PROCESSING_LOG_GROUP, WF_LOG_PREFIX):
        got = run_json("logs", "describe-log-groups", "--log-group-name-prefix", prefix) or {}
        for g in got.get("logGroups", []):
            log_groups[g["logGroupName"]] = g

    # ------------------------------------------------------------------ the demo prefixes
    prefixes = {}  # (project role, relative prefix) -> (count, bytes, first key)
    encryption = {}  # project role -> (key, SSEKMSKeyId) of one object under the demo prefix
    for p in projects.values():
        if not p["bucket"]:
            continue
        base = p["shared"]
        rels = [CODE_DIR] + [
            f"{DEMO_DIR}{v}/{part}/" for v in WORKFLOWS.values() for part in ("inbox", "outbox")
        ]
        for rel in rels:
            got = (
                run_json(
                    "s3api", "list-objects-v2", "--bucket", p["bucket"], "--prefix", base + rel
                )
                or {}
            )
            objs = [o for o in got.get("Contents", []) if not o.get("Key", "").endswith("/")]
            prefixes[(p["role"], rel)] = (
                len(objs),
                sum(int(o.get("Size", 0)) for o in objs),
                [o["Key"] for o in objs],
            )
            if objs and p["role"] not in encryption:
                head = (
                    run_json(
                        "s3api", "head-object", "--bucket", p["bucket"], "--key", objs[0]["Key"]
                    )
                    or {}
                )
                encryption[p["role"]] = (
                    objs[0]["Key"],
                    head.get("SSEKMSKeyId", head.get("ServerSideEncryption", "-")),
                )

    # ------------------------------------------------------------------ CloudTrail
    def lookup(event_name: str) -> list:
        got = (
            run_json(
                "cloudtrail",
                "lookup-events",
                "--lookup-attributes",
                f"AttributeKey=EventName,AttributeValue={event_name}",
                "--max-results",
                str(LOOKUP_MAX),
            )
            or {}
        )
        out = []
        for e in got.get("Events", []):
            try:
                out.append(json.loads(e.get("CloudTrailEvent", "{}")))
            except json.JSONDecodeError:
                continue
        return out

    def caller_of(ev: dict) -> tuple:
        """(role name, session name) of an assumed-role caller, else (arn, '-')."""
        arn = (ev.get("userIdentity") or {}).get("arn", "")
        m = re.match(r"^arn:aws:sts::\d{12}:assumed-role/([^/]+)/(.+)$", arn)
        return (m.group(1), m.group(2)) if m else (arn or "-", "-")

    def wf_name(ev: dict) -> str:
        rp = ev.get("requestParameters") or {}
        return rp.get("Name") or rp.get("name") or ""

    create_wf = [ev for ev in lookup("CreateWorkflow") if wf_name(ev) in WORKFLOWS]
    create_job = [
        ev
        for ev in lookup("CreateProcessingJob")
        if ((ev.get("requestParameters") or {}).get("processingJobName") or "").startswith(
            JOB_PREFIX
        )
    ]

    # ================================================================== checks
    def project_of(d: dict) -> dict | None:
        return by_arn.get(d["detail"].get("RoleArn", ""))

    # SO-1: each contract workflow exists, rests READY, and was created by its project role.
    for name in WORKFLOWS:
        d = wfs.get(name)
        if d is None:
            checks.note("SO-1", name, "absent - not built yet (Stage 6i passes 2, 4, 5).")
            continue
        status = d["summary"].get("WorkflowStatus", "-")
        twins = same_name.get(name, [])
        if len(twins) > 1:
            suffixes = ", ".join(w.get("WorkflowArn", "").rsplit("/", 1)[-1] for w in twins)
            checks.fail(
                "SO-1",
                name,
                f"{len(twins)} workflows carry this name ({suffixes}) - delete the extra ones; "
                "the newest is the one read below.",
            )
        evs = [ev for ev in create_wf if wf_name(ev) == name]
        who = sorted({caller_of(ev)[0] for ev in evs})
        if status != "READY":
            checks.fail("SO-1", name, f"status {status} - expected READY.")
        elif not evs:
            checks.note(
                "SO-1", name, "READY; no CreateWorkflow in the 90-day trail window to attribute."
            )
        elif all(w.startswith(PROJECT_ROLE_PREFIX) for w in who):
            checks.ok("SO-1", name, f"READY, created by {', '.join(who)}")
        else:
            checks.fail(
                "SO-1", name, f"READY, but created by {', '.join(who)} - not a project role."
            )

    # SO-2: the workflow's role, network and key are its project's.
    for name, d in wfs.items():
        det = d["detail"]
        p = project_of(d)
        if p is None:
            checks.fail(
                "SO-2",
                f"{name}: role",
                f"{det.get('RoleArn', '-')} is no project role read in this account.",
            )
            continue
        net = det.get("NetworkConfiguration") or {}
        sn = net.get("SubnetIds", [])
        names = [subnets.get(s, {}).get("name", "?") for s in sn]
        azs = {subnets.get(s, {}).get("az", "?") for s in sn}
        bad_sn = [n for n in names if not n.startswith(PRIVATE_SUBNET_PREFIX)]
        routed = [subnets.get(s, {}).get("name", s) for s in sn if default_route.get(s)]
        sg_ok = all(
            sgs.get(g, {}).get("project") == p["project"] for g in net.get("SecurityGroupIds", [])
        )
        enc = det.get("EncryptionConfiguration") or {}
        key_ok = (
            enc.get("Type") == "CUSTOMER_MANAGED_KEY"
            and p["key_id"]
            and p["key_id"] in (enc.get("KmsKeyId") or "")
        )
        problems = []
        if not sn:
            problems.append("no NetworkConfiguration - tasks would run in the service's VPC")
        if bad_sn:
            problems.append(f"subnets outside the private tier: {', '.join(bad_sn)}")
        if len(azs) < 2:
            problems.append(f"{len(azs)} AZ(s) - the private shape needs two")
        if routed:
            problems.append(f"a default route in {', '.join(routed)}")
        if not sg_ok:
            problems.append("a security group not tagged with the project")
        if not key_ok:
            problems.append(f"encryption {enc.get('Type', '-')} - expected the project key")
        if problems:
            checks.fail("SO-2", name, "; ".join(problems) + ".")
        else:
            checks.ok(
                "SO-2",
                name,
                f"{p['role']}; {', '.join(names)} ({len(azs)} AZs, no default route); project SG; "
                f"key {(p['key_aliases'] or [p['key_id']])[0]}",
            )

    # SO-3: where the definition and the Code object live; every version saved.
    saved = {}
    for name, d in wfs.items():
        det = d["detail"]
        p = project_of(d)
        loc = det.get("DefinitionS3Location") or {}
        code = (det.get("Code") or {}).get("S3Location") or {}
        problems = []
        if p and (
            loc.get("Bucket") != p["bucket"]
            or not (loc.get("ObjectKey") or "").startswith(p["defs"])
        ):
            problems.append(
                f"definition at s3://{loc.get('Bucket', '-')}/{loc.get('ObjectKey', '-')}, outside the project's dev/workflows/"
            )
        body = det.get("WorkflowDefinition") or ""
        if d["variant"] == "python" and not code:
            problems.append("no Code object - its Python task has nothing to run")
        elif d["variant"] == "bash":
            if has_task(body, BASH_COMMAND_TASK):
                if not code:
                    problems.append(f"no Code object - {BASH_COMMAND_TASK} has nothing to run")
            elif has_task(body, BASH_PROBE_TASK):
                if code:
                    problems.append("the probe carries a Code object, so it is no control")
            else:
                problems.append(f"neither {BASH_PROBE_TASK} (the probe) nor {BASH_COMMAND_TASK}")
        # every version, as served and with the account ids replaced
        files = []
        for i, v in enumerate(d["versions"], start=1):
            vid = v.get("WorkflowVersion", "")
            got = (
                run_json(
                    "mwaa-serverless",
                    "get-workflow",
                    "--workflow-arn",
                    d["arn"],
                    "--workflow-version",
                    vid,
                )
                or {}
            )
            body = got.get("WorkflowDefinition")
            if body is None:
                continue
            folder = defs_root / name
            folder.mkdir(parents=True, exist_ok=True)
            raw = folder / f"{i:02d}-{vid}.yaml"
            raw.write_text(body if body.endswith("\n") else body + "\n")
            clean = folder / f"{i:02d}-{vid}.sanitized.yaml"
            clean.write_text(sanitize(raw.read_text(), placeholders))
            files.append(clean.name)
        saved[name] = files
        detail = f"{len(d['versions'])} version(s); definition {loc.get('ObjectKey', '-')}"
        if code:
            detail += f"; Code s3://{code.get('Bucket', '-')}/{code.get('ObjectKey', '-')} snapshotted {det.get('CodeSnapshottedAt', '-')}"
        elif d["variant"] == "bash":
            detail += "; the probe, no Code object"
        if problems:
            checks.fail("SO-3", name, "; ".join(problems) + ".")
        else:
            checks.ok("SO-3", name, detail)

    # SO-4: the latest run of each workflow, read per run.
    for name, rs in runs.items():
        if not rs:
            checks.note("SO-4", name, "no run yet.")
            continue
        latest = rs[0]
        det = latest["detail"].get("RunDetail") or {}
        state = det.get("RunState", "-")
        kind = latest["detail"].get("RunType", "-")
        by_task = last_attempts(latest["tasks"])
        tasks = ", ".join(f"{k} {v}" for k, v in by_task.items()) or "no task instance"
        what = f"{name}: run {latest['id']} ({kind})"
        if wfs[name]["variant"] == "bash":
            neg = by_task.get(BASH_NEGATIVE_TASK)
            others = [v for k, v in by_task.items() if k != BASH_NEGATIVE_TASK]
            if neg == "SUCCESS":
                checks.fail(
                    "SO-4",
                    what,
                    f"{BASH_NEGATIVE_TASK} SUCCEEDED - the worker reached the internet: {tasks}.",
                )
            elif neg == "FAILED" and others and all(v == "SUCCESS" for v in others):
                checks.ok(
                    "SO-4",
                    what,
                    f"{BASH_NEGATIVE_TASK} FAILED and every other task SUCCESS, as designed: {tasks}",
                )
            else:
                checks.note("SO-4", what, f"{state}: {tasks}")
        elif state == "SUCCESS":
            checks.ok("SO-4", what, f"SUCCESS: {tasks}")
        elif state in ("RUNNING", "QUEUED", "STARTING"):
            checks.note("SO-4", what, f"{state} - read again when it ends.")
        else:
            checks.fail("SO-4", what, f"{state}: {tasks}")

    # SO-5: each demo-devenv- job against the boundary's settings, its project and the image.
    # A setting outside the boundary fails on any job. A failed outcome fails on the newest job
    # only: a processing job cannot be deleted, so an earlier probe's failure stays listed.
    for j in jobs:
        jname = j.get("ProcessingJobName", "-")
        net = j.get("NetworkConfig") or {}
        vpc = net.get("VpcConfig") or {}
        cluster = (j.get("ProcessingResources") or {}).get("ClusterConfig") or {}
        p = by_arn.get(j.get("RoleArn", ""))
        problems = []
        if net.get("EnableNetworkIsolation") is not True:
            problems.append("network isolation off")
        if net.get("EnableInterContainerTrafficEncryption") is not True:
            problems.append("inter-container encryption off")
        bad = [
            subnets.get(s, {}).get("name", s)
            for s in vpc.get("Subnets", [])
            if not subnets.get(s, {}).get("name", "").startswith(PRIVATE_SUBNET_PREFIX)
        ]
        if not vpc.get("Subnets"):
            problems.append("no VpcConfig")
        elif bad:
            problems.append(f"subnets outside the private tier: {', '.join(bad)}")
        if p is None:
            problems.append(f"role {j.get('RoleArn', '-')} is no project role")
        else:
            if not (
                p["key_id"]
                and p["key_id"] in (cluster.get("VolumeKmsKeyId") or "")
                or (cluster.get("VolumeKmsKeyId") in p["key_aliases"])
            ):
                problems.append(
                    f"volume key {cluster.get('VolumeKmsKeyId', '-')} is not the project key"
                )
            out_key = (j.get("ProcessingOutputConfig") or {}).get("KmsKeyId") or ""
            if not (p["key_id"] and p["key_id"] in out_key or out_key in p["key_aliases"]):
                problems.append(f"output key {out_key or '-'} is not the project key")
            if j["_tags"].get("AmazonDataZoneProject") != p["project"]:
                problems.append("no AmazonDataZoneProject tag naming the project")
            if any(
                sgs.get(g, {}).get("project") != p["project"]
                for g in vpc.get("SecurityGroupIds", [])
            ):
                problems.append("a security group not tagged with the project")
        uri = (j.get("AppSpecification") or {}).get("ImageUri", "")
        if image_digest and image_digest not in uri:
            problems.append("an image other than the registered house image's digest")
        status = j.get("ProcessingJobStatus", "-")
        secs = _seconds(j.get("ProcessingStartTime"), j.get("ProcessingEndTime"))
        summary = (
            f"{status}, {cluster.get('InstanceType', '-')}, {secs if secs is not None else '-'} s"
        )
        failure = None
        if status == "Failed":
            failure = f"Failed: {j.get('FailureReason') or j.get('ExitMessage') or '-'}"
            if j is jobs[0]:
                problems.append(failure)
        if problems:
            checks.fail("SO-5", jname, "; ".join(problems) + f" ({summary}).")
        elif failure:
            checks.note(
                "SO-5",
                jname,
                f"{failure} ({summary}) - an earlier job; the newest is "
                f"{jobs[0].get('ProcessingJobName', '-')}.",
            )
        elif status in ("InProgress", "Stopping"):
            checks.note("SO-5", jname, f"{summary} - read again when it ends.")
        else:
            checks.ok(
                "SO-5",
                jname,
                f"{summary}; isolated, encrypted, project role, key and tag, house image",
            )
    if not jobs:
        checks.note("SO-5", f"{JOB_PREFIX}*", "no processing job yet (Stage 6i pass 2).")

    # SO-6: the log groups the exercise makes, and their retention.
    expected = [PROCESSING_LOG_GROUP] + [
        f"{WF_LOG_PREFIX}{project_of(d)['domain']}-{project_of(d)['project']}/{name}"
        for name, d in wfs.items()
        if project_of(d)
    ]
    for lg in expected:
        g = log_groups.get(lg)
        if g is None:
            checks.note("SO-6", lg, "absent - created by the first run or job that writes to it.")
        elif g.get("retentionInDays"):
            checks.ok("SO-6", lg, f"retention {g['retentionInDays']} days")
        else:
            checks.note("SO-6", lg, "no retention - EXC-10's shape (Stage 6i decision 3).")

    # SO-7: the demo prefixes, and the encryption of what they hold.
    for p in projects.values():
        base = f"s3://{p['bucket']}/{p['shared']}"
        code_keys = prefixes.get((p["role"], CODE_DIR), (0, 0, []))[2]
        if not any(k.endswith(PACKAGE_MARKER) for k in code_keys):
            checks.note(
                "SO-7",
                f"{base}{CODE_DIR}",
                f"no {PACKAGE_MARKER} - not copied yet (Stage 6i pass 1).",
            )
        else:
            checks.ok(
                "SO-7",
                f"{base}{CODE_DIR}",
                f"{len(code_keys)} object(s), the entry point present",
            )
        for v in WORKFLOWS.values():
            n_in = prefixes.get((p["role"], f"{DEMO_DIR}{v}/inbox/"), (0, 0, []))[0]
            n_out = prefixes.get((p["role"], f"{DEMO_DIR}{v}/outbox/"), (0, 0, []))[0]
            if n_in:
                checks.note(
                    "SO-7",
                    f"{base}{DEMO_DIR}{v}/",
                    f"inbox holds {n_in} object(s) - a drop waiting, or a run that did not consume it; outbox {n_out}",
                )
            else:
                checks.ok(
                    "SO-7", f"{base}{DEMO_DIR}{v}/", f"inbox empty; outbox holds {n_out} object(s)"
                )
        if p["role"] in encryption:
            key, kms = encryption[p["role"]]
            if p["key_id"] and p["key_id"] in kms:
                checks.ok(
                    "SO-7", f"encryption under {base}", f"{key.rsplit('/', 1)[-1]}: the project key"
                )
            else:
                checks.fail(
                    "SO-7", f"encryption under {base}", f"{key}: {kms} - not the project key."
                )

    # SO-8: who created each demo job, and through which door.
    for ev in create_job:
        role, session = caller_of(ev)
        jname = (ev.get("requestParameters") or {}).get("processingJobName", "-")
        vpce = ev.get("vpcEndpointId") or ""
        err = ev.get("errorCode") or ""
        what = f"CreateProcessingJob {jname} at {ev.get('eventTime', '-')}"
        if err:
            checks.fail("SO-8", what, f"{err}: {ev.get('errorMessage', '-')}")
        elif not (role.startswith(PROJECT_ROLE_PREFIX) and session == WORKER_SESSION):
            checks.fail(
                "SO-8",
                what,
                f"called by {role}/{session} - expected a project role as {WORKER_SESSION}.",
            )
        elif vpce:
            checks.ok(
                "SO-8",
                what,
                f"{role}/{session} through {vpce} from {ev.get('sourceIPAddress', '-')}",
            )
        else:
            checks.note(
                "SO-8",
                what,
                f"{role}/{session}, no vpcEndpointId - the call came from {ev.get('sourceIPAddress', '-')}; read it.",
            )
    if not create_job:
        checks.note("SO-8", f"CreateProcessingJob {JOB_PREFIX}*", "none in the trail window yet.")

    # ================================================================== report
    with open(out_path, "w") as stream:
        rep = Report(stream)
        rep.banner(
            f"sandbox-orchestration.txt - the Sandbox orchestration exercise (Stage 6i)\n"
            f"generated {context.utc_stamp()} by ./aws/sandbox-orchestration.py"
        )
        rep.text(
            "\nSections: 1 who is asking; 2 the project; 3 the workflows; 4 versions and\n"
            "definitions; 5 runs and task instances; 6 processing jobs; 7 log groups; 8 the demo\n"
            "prefixes; 9 CloudTrail; 10 checks SO-1..SO-8; 11 calls that failed.\n"
            f"Contracts: WORKFLOWS={', '.join(WORKFLOWS)}  JOB_PREFIX={JOB_PREFIX}\n"
            f"           CODE_DIR=shared/{CODE_DIR}  DEMO_DIR=shared/{DEMO_DIR}\n"
        )

        rep.h1("1. Who is asking")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        rep.h1("2. The project")
        rows = ["ROLE\tPROJECT\tDOMAIN\tKEY\tBUCKET\tBOUNDARY"]
        for p in projects.values():
            rows.append(
                f"{p['role']}\t{p['project'] or '-'}\t{p['domain'] or '-'}\t"
                f"{(p['key_aliases'] or [p['key_id'] or '-'])[0]}\t{p['bucket'] or '-'}\t"
                f"{p['boundary'].rsplit('/', 1)[-1] or '(none)'}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no project role read)\t-\t-\t-\t-\t-"])
        rep.line()
        rep.line(
            f"house image: {HOUSE_IMAGE} version {(image or {}).get('Version', '-')}, digest {image_digest or '-'}"
        )

        rep.h1("3. The workflows")
        rows = ["NAME\tSTATUS\tTRIGGER\tROLE\tSUBNETS\tSECURITY GROUP\tKEY"]
        for w in sorted(all_wfs, key=lambda x: x.get("Name", "")):
            d = wfs.get(w.get("Name"))
            det = d["detail"] if d else {}
            net = det.get("NetworkConfiguration") or {}
            rows.append(
                f"{w.get('Name', '-')}{'' if d else ' (not a contract)'}\t{w.get('WorkflowStatus', '-')}\t"
                f"{w.get('TriggerMode', det.get('TriggerMode', '-'))}\t"
                f"{(det.get('RoleArn') or '-').rsplit('/', 1)[-1]}\t"
                f"{','.join(subnets.get(s, {}).get('name', s) for s in net.get('SubnetIds', [])) or '-'}\t"
                f"{','.join(sgs.get(g, {}).get('name', g) for g in net.get('SecurityGroupIds', [])) or '-'}\t"
                f"{(det.get('EncryptionConfiguration') or {}).get('Type', '-')}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-\t-\t-\t-"])
        for name, d in wfs.items():
            rep.show(
                cli,
                "mwaa-serverless",
                "get-workflow",
                "--workflow-arn",
                d["arn"],
                "--query",
                "{Name:Name,Version:WorkflowVersion,Definition:DefinitionS3Location,Code:Code,CodeSnapshottedAt:CodeSnapshottedAt,Logging:LoggingConfiguration}",
                lead_blank=True,
            )

        rep.h1("4. Versions and definitions")
        rows = ["WORKFLOW\t#\tVERSION\tCREATED\tLATEST\tSAVED AS"]
        for name, d in wfs.items():
            for i, v in enumerate(d["versions"], start=1):
                rows.append(
                    f"{name}\t{i}\t{v.get('WorkflowVersion', '-')}\t{v.get('CreatedAt', '-')}\t"
                    f"{'yes' if v.get('IsLatestVersion') else '-'}\t"
                    f"{DEFS_DIR}/{name}/{i:02d}-{v.get('WorkflowVersion', '-')}.yaml"
                )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-\t-\t-"])
        rep.line()
        rep.line(
            "Each version is saved twice under aws/output/: as served, and as .sanitized.yaml with"
        )
        rep.line(
            "the account ids replaced by <SANDBOX_ACCOUNT_ID>, <REGISTRY_ACCOUNT_ID> or <ACCOUNT_ID>."
        )

        rep.h1("5. Runs and task instances")
        rows = ["WORKFLOW\tRUN\tTYPE\tSTATE\tRUN S\tTASK\tTASK STATE\tTASK S\tBILLED MIN"]
        for name, rs in runs.items():
            for r in rs:
                det = r["detail"].get("RunDetail") or {}
                for t in r["tasks"] or [{}]:
                    secs = t.get("DurationInSeconds")
                    rows.append(
                        f"{name}\t{r['id']}\t{r['detail'].get('RunType', '-')}\t{det.get('RunState', '-')}\t"
                        f"{det.get('Duration', '-')}\t{_task_id(t.get('TaskInstanceId', '-'))}\t"
                        f"{t.get('Status', '-')}\t{secs if secs is not None else '-'}\t"
                        f"{_billed_minutes(secs):.0f}"
                        if t
                        else f"{name}\t{r['id']}\t-\t-\t-\t-\t-\t-\t-"
                    )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no run)\t-\t-\t-\t-\t-\t-\t-\t-"])
        rep.line()
        rep.line("BILLED MIN is the task's duration rounded up to the one-minute minimum, the unit")
        rep.line("MWAA Serverless bills (0.088 USD per task-hour, docs/PRICING.md section 1.3).")

        rep.h1(f"6. Processing jobs - {JOB_PREFIX}*")
        rows = ["JOB\tSTATUS\tINSTANCE\tSECONDS\tISOLATED\tICE\tVOLUME KEY\tTAG\tIMAGE DIGEST"]
        for j in jobs:
            net = j.get("NetworkConfig") or {}
            cluster = (j.get("ProcessingResources") or {}).get("ClusterConfig") or {}
            uri = (j.get("AppSpecification") or {}).get("ImageUri", "")
            secs = _seconds(j.get("ProcessingStartTime"), j.get("ProcessingEndTime"))
            rows.append(
                f"{j.get('ProcessingJobName', '-')}\t{j.get('ProcessingJobStatus', '-')}\t"
                f"{cluster.get('InstanceType', '-')}\t{secs if secs is not None else '-'}\t"
                f"{net.get('EnableNetworkIsolation', '-')}\t{net.get('EnableInterContainerTrafficEncryption', '-')}\t"
                f"{(cluster.get('VolumeKmsKeyId') or '-').rsplit('/', 1)[-1]}\t"
                f"{j['_tags'].get('AmazonDataZoneProject', '-')}\t"
                f"{uri.split('@', 1)[1][:19] + '...' if '@' in uri else uri.rsplit(':', 1)[-1] or '-'}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-\t-\t-\t-\t-\t-"])
        for j in jobs[:3]:
            rep.show(
                cli,
                "sagemaker",
                "describe-processing-job",
                "--processing-job-name",
                j.get("ProcessingJobName", ""),
                "--query",
                "{Status:ProcessingJobStatus,Failure:FailureReason,Exit:ExitMessage,Start:ProcessingStartTime,End:ProcessingEndTime,App:AppSpecification,Inputs:ProcessingInputs[].S3Input.S3Uri,Outputs:ProcessingOutputConfig}",
                lead_blank=True,
            )

        rep.h1("7. Log groups")
        rows = ["LOG GROUP\tRETENTION\tKMS\tSTORED BYTES"]
        for lg in sorted(log_groups):
            g = log_groups[lg]
            rows.append(
                f"{lg}\t{g.get('retentionInDays') or 'none'}\t{'yes' if g.get('kmsKeyId') else 'no'}\t{g.get('storedBytes', '-')}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-"])

        rep.h1(f"8. The exercise's prefixes - shared/{CODE_DIR} and shared/{DEMO_DIR}")
        rows = ["PROJECT\tPREFIX\tOBJECTS\tBYTES"]
        for (role, rel), (n, size, _keys) in sorted(prefixes.items()):
            rows.append(f"{projects[role]['project']}\t{rel}\t{n}\t{size}")
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-"])

        rep.h1("9. CloudTrail - CreateWorkflow and CreateProcessingJob for the contracts")
        rows = ["TIME\tEVENT\tSUBJECT\tROLE\tSESSION\tVPC ENDPOINT\tSOURCE\tERROR"]
        for ev in create_wf:
            role, session = caller_of(ev)
            rows.append(
                f"{ev.get('eventTime', '-')}\tCreateWorkflow\t{wf_name(ev) or '-'}\t"
                f"{role}\t{session}\t{ev.get('vpcEndpointId') or '-'}\t{ev.get('sourceIPAddress', '-')}\t{ev.get('errorCode') or '-'}"
            )
        for ev in create_job:
            role, session = caller_of(ev)
            rows.append(
                f"{ev.get('eventTime', '-')}\tCreateProcessingJob\t{(ev.get('requestParameters') or {}).get('processingJobName', '-')}\t"
                f"{role}\t{session}\t{ev.get('vpcEndpointId') or '-'}\t{ev.get('sourceIPAddress', '-')}\t{ev.get('errorCode') or '-'}"
            )
        rep.tabulate(
            rows if len(rows) > 1 else rows + ["(none in the window)\t-\t-\t-\t-\t-\t-\t-"]
        )

        rep.h1("10. Checks")
        rep.checks_table(checks)

        rep.h1("11. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/sandbox-orchestration.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 11)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 10)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
