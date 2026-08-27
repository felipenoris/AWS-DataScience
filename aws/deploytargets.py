#!/usr/bin/env -S uv run --quiet
# deploytargets.py - Stage 9's evidence, producer and targets side by side: the Production
# data platform (buckets, CMK, the enforced workgroup), the runtime (the job role with D13's
# absence, the model package groups with their resource policies), the Lake Formation
# settings in every account that has any (DL-5's discipline extended - DT-5), the write
# share with its links and invitations (INT-03), the drop-box contract from both sides
# (INT-10), the Staging mirror and the ABSENCE that is a control (D20), the escape hatch
# with its alarm, and the persona sets' owed allows read back through the delegated admin.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/deploytargets.py                    # every awsds-* profile
#             ./aws/deploytargets.py awsds-infra-prod   # only the ones named
#             python3 aws/deploytargets.py -            # CloudShell, ambient credentials
#   writes:   aws/output/deploytargets.txt   (untracked - see .gitignore)
#   reads:    s3api get-bucket-*, kms list-aliases/get-key-policy/list-grants,
#             athena get-work-group, sagemaker list-model-package-groups /
#             get-model-package-group-policy, iam get-role/list-role-policies/
#             get-role-policy, lakeformation get-data-lake-settings/list-permissions,
#             glue get-databases/get-tables, ram get-resource-share-invitations,
#             events list-rules, cloudtrail lookup-events, sso-admin (reads only),
#             sts get-caller-identity. It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is
# the producer path BETWEEN accounts: the lake and the drop-box live in Data Governance
# while the only principal allowed to write them lives in Production (D22, D25), Staging's
# whole value is what it does NOT reach (D20), and the persona allows live in Identity.
# Section 1 pays the rule back with the caller ARN of every profile.
#
# CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - the job role is awsds-prod-job-exec (step 3.1 - the SAME name Stage 5 step 1.4's
#     drop-box statement and key grant carry)
#   - the workgroup is awsds-prod-athena; Staging's is awsds-staging-athena (steps 1.2, 4.2)
#   - the buckets are awsds-prod-outputs and awsds-prod-derived (step 1.1 - the derived
#     zone arrives with the consumer-data call, so its policy is module-shaped: TLS-only
#     plus the presigned cap, no perimeter branches - those are the lake's and outputs')
#   - the package groups match awsds-prod-model-* (step 3.2)
#   - the debug role is awsds-prod-debug, its rule awsds-prod-debug-assume (step 6)
#   - Staging's job role is awsds-staging-job-exec (step 4.3)
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the LF write landing, the direct PutObject dying, the
#     pickup emptying the letterbox, the console fraction (INT-06) - are the stage's own
#     (Lesson 20): configuration for configuration questions, probes for behaviour.
#   - Whether the write share WORKS is 2.4's job run; this file only shows it was granted.
#   - `Staging` rows appear only once the account is vended and holds a profile.

from __future__ import annotations

import datetime as _dt
import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "deploytargets.txt"

DATA_PROFILE = "awsds-infra-data"
PROD_PROFILE = "awsds-infra-prod"
STAGING_PROFILE = "awsds-infra-staging"
IDENTITY_PROFILE = "awsds-infra-identity"

# The contracts (see header).
JOB_ROLE = "awsds-prod-job-exec"
DEBUG_ROLE = "awsds-prod-debug"
DEBUG_RULE_SUBSTR = "debug-assume"
PROD_WG = "awsds-prod-athena"
STAGING_WG = "awsds-staging-athena"
STAGING_JOB_ROLE = "awsds-staging-job-exec"
OUT_BUCKET = "awsds-prod-outputs"
# NOTE 2026-08-26: consumer-data v0.6.0 REMOVED the derived bucket + enforced workgroup
# from the module (D19 revised - the Interactive derived zone re-homed onto the SMUS project
# path). Production has NO SMUS (D28), so where ITS results land is Stage 9's to re-decide at
# revision - this expectation stands as the stage file wrote it and is re-read there, not here.
RESULTS_BUCKET = "awsds-prod-derived"  # results/ is a prefix family in it, never a bucket
MPG_PREFIX = "awsds-prod-model-"
PROD_CMK_ALIAS = "alias/awsds-prod-data"  # renamed 2026-08-19 (twice): one data CMK per account
DROPBOX_SUBSTR = "dropbox"
LAKE_BUCKET_SUBSTR = "awsds-data-"
MIRROR_DBS = ("raw", "curated")  # the lake databases the Staging catalog mirrors (4.1)
SETS_READ = ("DataScientistProdAccess", "DataScientistStagingAccess")
LOOKUP_MAX = 50

POLICY_BRANCHES = (
    ("vpce", "aws:SourceVpce"),
    ("ip", "aws:SourceIp"),
    ("via", "aws:ViaAWSService"),
)


def _stmts(doc: dict) -> list:
    stmts = (doc or {}).get("Statement", [])
    return [stmts] if isinstance(stmts, dict) else list(stmts)


def _as_list(value) -> list:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    account_of = {c.profile: c.account for c in callers if c.live}
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    prod_live = PROD_PROFILE in live
    data_live = DATA_PROFILE in live
    staging_live = STAGING_PROFILE in live
    identity_live = IDENTITY_PROFILE in live
    prod_account = account_of.get(PROD_PROFILE)
    data_account = account_of.get(DATA_PROFILE)

    # ------------------------------------------ 2. buckets, CMK, workgroup (Production)
    bucket_rows: list = []  # (bucket, state, versioning, sse, branches, expiry)
    wg_row = None  # (enforce, output location, cutoff, encryption)
    cmk_present = False
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (buckets, workgroup) ...")
        res = cli.run(
            "kms", "list-aliases", "--query", "Aliases[].AliasName", "--output", "json", log=False
        )
        aliases = json.loads(res.stdout or "[]") if res.ok and res.stdout else []
        cmk_present = PROD_CMK_ALIAS in aliases
        for bucket in (OUT_BUCKET, RESULTS_BUCKET):
            r = cli.run(
                "s3api",
                "head-bucket",
                "--bucket",
                bucket,
                log=False,
                tolerate="404|NoSuchBucket|Not Found",
            )
            if r.tolerated or not r.ok:
                bucket_rows.append((bucket, "(absent)", "-", "-", "-", "-"))
                continue
            v = cli.run(
                "s3api",
                "get-bucket-versioning",
                "--bucket",
                bucket,
                "--query",
                "Status",
                "--output",
                "text",
                log=False,
            )
            versioning = (v.stdout or "").strip() or "(unset)"
            e = cli.run(
                "s3api",
                "get-bucket-encryption",
                "--bucket",
                bucket,
                "--query",
                "ServerSideEncryptionConfiguration.Rules[0]."
                "ApplyServerSideEncryptionByDefault.SSEAlgorithm",
                "--output",
                "text",
                log=False,
                tolerate="ServerSideEncryptionConfigurationNotFoundError",
            )
            sse = "(none)" if e.tolerated else ((e.stdout or "").strip() or "(none)")
            p = cli.run(
                "s3api",
                "get-bucket-policy",
                "--bucket",
                bucket,
                "--query",
                "Policy",
                "--output",
                "text",
                log=False,
                tolerate="NoSuchBucketPolicy",
            )
            if p.tolerated:
                branches = "(no policy)"
            else:
                text = p.stdout or ""
                branches = (
                    "/".join(tag for tag, key in POLICY_BRANCHES if key in text) or "(none match)"
                )
            expiry = "-"
            if bucket == RESULTS_BUCKET:
                lc = cli.run(
                    "s3api",
                    "get-bucket-lifecycle-configuration",
                    "--bucket",
                    bucket,
                    "--query",
                    "Rules[?Status=='Enabled'].Expiration.Days",
                    "--output",
                    "json",
                    log=False,
                    tolerate="NoSuchLifecycleConfiguration",
                )
                if lc.tolerated:
                    expiry = "(none)"
                else:
                    days = json.loads(lc.stdout or "[]") if lc.ok and lc.stdout else []
                    expiry = f"{days[0]}d" if days else "(none)"
            bucket_rows.append((bucket, "present", versioning, sse, branches, expiry))
        res = cli.run(
            "athena",
            "get-work-group",
            "--work-group",
            PROD_WG,
            "--query",
            "WorkGroup.Configuration.[EnforceWorkGroupConfiguration,"
            "ResultConfiguration.OutputLocation,BytesScannedCutoffPerQuery,"
            "ResultConfiguration.EncryptionConfiguration.EncryptionOption]",
            "--output",
            "json",
            log=False,
            tolerate="InvalidRequestException",
        )
        if res.ok and not res.tolerated and res.stdout:
            wg_row = json.loads(res.stdout)

    # ----------------------------- 3. the runtime: job role (D13) and the registry (D28)
    job_role_state = "(not measured)"
    job_trust_bad: list = []
    job_lake_hits: list = []  # (policy, resource) - an s3 statement reaching a lake bucket
    mpg_rows: list = []  # (group, policy state)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (job role, registry) ...")
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            JOB_ROLE,
            "--query",
            "Role.AssumeRolePolicyDocument",
            "--output",
            "json",
            log=False,
            tolerate="NoSuchEntity",
        )
        if res.tolerated:
            job_role_state = "(absent)"
        elif res.ok and res.stdout:
            job_role_state = "present"
            for st in _stmts(json.loads(res.stdout)):
                principal = st.get("Principal", {}) or {}
                services = _as_list(principal.get("Service"))
                for svc in services:
                    if str(svc) not in ("glue.amazonaws.com", "sagemaker.amazonaws.com"):
                        job_trust_bad.append(f"service {svc}")
                if principal.get("AWS") or principal.get("Federated"):
                    job_trust_bad.append("a non-service principal in the trust policy")
            res = cli.run(
                "iam",
                "list-role-policies",
                "--role-name",
                JOB_ROLE,
                "--query",
                "PolicyNames",
                "--output",
                "json",
                log=False,
            )
            for pname in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                r = cli.run(
                    "iam",
                    "get-role-policy",
                    "--role-name",
                    JOB_ROLE,
                    "--policy-name",
                    pname,
                    "--query",
                    "PolicyDocument",
                    "--output",
                    "json",
                    log=False,
                )
                if not (r.ok and r.stdout):
                    continue
                for st in _stmts(json.loads(r.stdout)):
                    actions = " ".join(_as_list(st.get("Action")))
                    if "s3:" not in actions or str(st.get("Effect")) != "Allow":
                        continue
                    for arn in _as_list(st.get("Resource")):
                        if LAKE_BUCKET_SUBSTR in str(arn) and DROPBOX_SUBSTR not in str(arn):
                            job_lake_hits.append((str(pname), str(arn)))
        res = cli.run(
            "sagemaker",
            "list-model-package-groups",
            "--query",
            "ModelPackageGroupSummaryList[].ModelPackageGroupName",
            "--output",
            "json",
            log=False,
        )
        groups = [
            str(g)
            for g in (json.loads(res.stdout or "[]") if res.ok and res.stdout else [])
            if str(g).startswith(MPG_PREFIX)
        ]
        for group in groups:
            r = cli.run(
                "sagemaker",
                "get-model-package-group-policy",
                "--model-package-group-name",
                group,
                "--query",
                "ResourcePolicy",
                "--output",
                "text",
                log=False,
                tolerate="ResourceNotFound|ValidationException",
            )
            if r.tolerated:
                mpg_rows.append((group, "(no resource policy)"))
            elif r.ok:
                n = (r.stdout or "").count('"Sid"')
                mpg_rows.append((group, f"policy present ({n} statement(s))"))
            else:
                mpg_rows.append((group, "(read failed)"))

    # -------------------- 4. the Lake Formation settings, every account that has any
    lf_rows: list = []  # (profile, parameters, create defaults, admins)
    lf_data_params: dict = {}
    for p in (DATA_PROFILE, PROD_PROFILE, STAGING_PROFILE):
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "lakeformation",
            "get-data-lake-settings",
            "--query",
            "DataLakeSettings.[Parameters,CreateDatabaseDefaultPermissions,"
            "CreateTableDefaultPermissions,DataLakeAdmins[].DataLakePrincipalIdentifier]",
            "--output",
            "json",
            log=False,
        )
        if not (res.ok and res.stdout):
            lf_rows.append((p, "(read failed)", "-", "-"))
            continue
        params, db_defaults, tb_defaults, admins = json.loads(res.stdout)
        if p == DATA_PROFILE:
            lf_data_params = params or {}
        param_txt = ",".join(f"{k}={v}" for k, v in sorted((params or {}).items())) or "(empty)"
        defaults_txt = f"db:{len(db_defaults or [])} tbl:{len(tb_defaults or [])}"
        admin_txt = " ".join(str(a).rsplit("/", 1)[-1] for a in (admins or [])) or "(none)"
        lf_rows.append((p, param_txt, defaults_txt, admin_txt))

    # ------------------------- 5. the write share, the links, the invitations (INT-03)
    share_perm_rows: list = []  # (principal tail, resource, permissions)
    write_share_seen = False
    link_rows: list = []  # (profile, database, target catalog tail, target database)
    pending_invites: list = []  # (profile, share name, status)
    if data_live:
        cli = cli_for(DATA_PROFILE)
        note(f"measuring {DATA_PROFILE} (grantor permissions) ...")
        res = cli.run(
            "lakeformation",
            "list-permissions",
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            for entry in json.loads(res.stdout).get("PrincipalResourcePermissions", []):
                principal = str(
                    (entry.get("Principal") or {}).get("DataLakePrincipalIdentifier") or ""
                )
                if prod_account and prod_account not in principal:
                    continue
                if not prod_account:
                    continue
                perms = ",".join(entry.get("Permissions") or [])
                resource = entry.get("Resource") or {}
                if "Table" in resource:
                    r = resource["Table"]
                    where = f"table:{r.get('DatabaseName')}.{r.get('Name') or '*'}"
                elif "Database" in resource:
                    where = f"database:{resource['Database'].get('Name')}"
                else:
                    where = next(iter(resource.keys()), "?")
                share_perm_rows.append((principal[-12:], where, perms))
                if "INSERT" in perms:
                    write_share_seen = True
        elif not res.ok:
            logerr(DATA_PROFILE, "lakeformation list-permissions", res.stderr)
    for p in (PROD_PROFILE, STAGING_PROFILE):
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "glue",
            "get-databases",
            "--query",
            "DatabaseList[].[Name,TargetDatabase.CatalogId,TargetDatabase.DatabaseName]",
            "--output",
            "json",
            log=False,
        )
        for name, target_catalog, target_db in (
            json.loads(res.stdout or "[]") if res.ok and res.stdout else []
        ):
            if target_catalog:
                link_rows.append((p, str(name), str(target_catalog)[-4:], str(target_db)))
        res = cli.run(
            "ram",
            "get-resource-share-invitations",
            "--query",
            "resourceShareInvitations[].[resourceShareName,status]",
            "--output",
            "json",
            log=False,
        )
        for share_name, status in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            if str(status) == "PENDING":
                pending_invites.append((p, str(share_name), str(status)))

    # ------------------------------- 6. the drop-box contract, both sides (INT-10, D25)
    dropbox_bucket = None
    dropbox_stmt = "(not measured)"
    dropbox_key_names_role = "(not measured)"
    if data_live:
        cli = cli_for(DATA_PROFILE)
        note(f"measuring {DATA_PROFILE} (drop-box) ...")
        res = cli.run(
            "s3api", "list-buckets", "--query", "Buckets[].Name", "--output", "json", log=False
        )
        for name in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            if DROPBOX_SUBSTR in str(name):
                dropbox_bucket = str(name)
                break
        if dropbox_bucket:
            res = cli.run(
                "s3api",
                "get-bucket-policy",
                "--bucket",
                dropbox_bucket,
                "--query",
                "Policy",
                "--output",
                "text",
                log=False,
                tolerate="NoSuchBucketPolicy",
            )
            if res.tolerated:
                dropbox_stmt = "(no bucket policy)"
            elif res.ok:
                text = res.stdout or ""
                has_role = JOB_ROLE in text
                has_delete = "s3:DeleteObject" in text
                dropbox_stmt = (
                    f"names {JOB_ROLE}: {'yes' if has_role else 'NO'}; "
                    f"DeleteObject present: {'yes' if has_delete else 'NO'}"
                )
            res = cli.run(
                "kms",
                "list-aliases",
                "--query",
                f"Aliases[?contains(AliasName, '{DROPBOX_SUBSTR}')].TargetKeyId",
                "--output",
                "json",
                log=False,
            )
            key_ids = [k for k in (json.loads(res.stdout or "[]") if res.ok else []) if k]
            if key_ids:
                key_id = str(key_ids[0])
                hit = False
                r = cli.run(
                    "kms",
                    "get-key-policy",
                    "--key-id",
                    key_id,
                    "--policy-name",
                    "default",
                    "--query",
                    "Policy",
                    "--output",
                    "text",
                    log=False,
                )
                if r.ok and JOB_ROLE in (r.stdout or ""):
                    hit = True
                r = cli.run(
                    "kms",
                    "list-grants",
                    "--key-id",
                    key_id,
                    "--query",
                    "Grants[].GranteePrincipal",
                    "--output",
                    "json",
                    log=False,
                )
                if r.ok and any(JOB_ROLE in str(g) for g in json.loads(r.stdout or "[]")):
                    hit = True
                dropbox_key_names_role = "yes" if hit else "NO"
            else:
                dropbox_key_names_role = "(no drop-box key alias)"

    # ------------------- 7. the Staging mirror, and the absence that is a control (D20)
    staging_links_to_data: list = []  # resource links pointing at Data Governance
    mirror_rows: list = []  # (database, lake tables, staging tables, verdict)
    staging_wg_row = None
    staging_job_state = "(not measured)"
    if staging_live:
        for p, db, catalog_tail, target_db in link_rows:
            if p == STAGING_PROFILE and data_account and data_account.endswith(catalog_tail):
                staging_links_to_data.append((db, target_db))
        cli = cli_for(STAGING_PROFILE)
        note(f"measuring {STAGING_PROFILE} (mirror) ...")
        res = cli.run(
            "athena",
            "get-work-group",
            "--work-group",
            STAGING_WG,
            "--query",
            "WorkGroup.Configuration.[EnforceWorkGroupConfiguration,"
            "ResultConfiguration.OutputLocation,BytesScannedCutoffPerQuery]",
            "--output",
            "json",
            log=False,
            tolerate="InvalidRequestException",
        )
        if res.ok and not res.tolerated and res.stdout:
            staging_wg_row = json.loads(res.stdout)
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            STAGING_JOB_ROLE,
            "--query",
            "Role.RoleName",
            "--output",
            "text",
            log=False,
            tolerate="NoSuchEntity",
        )
        staging_job_state = "(absent)" if res.tolerated else ("present" if res.ok else "(failed)")
        if data_live:
            for db in MIRROR_DBS:
                lake_tables: set = set()
                staging_tables: set = set()
                for profile, sink in (
                    (DATA_PROFILE, lake_tables),
                    (STAGING_PROFILE, staging_tables),
                ):
                    r = cli_for(profile).run(
                        "glue",
                        "get-tables",
                        "--database-name",
                        db,
                        "--query",
                        "TableList[].Name",
                        "--output",
                        "json",
                        log=False,
                        tolerate="EntityNotFoundException",
                    )
                    if r.ok and not r.tolerated and r.stdout:
                        sink.update(str(t) for t in json.loads(r.stdout))
                if not staging_tables and not lake_tables:
                    verdict = "(neither exists)"
                elif staging_tables == lake_tables:
                    verdict = "mirrored"
                else:
                    missing = lake_tables - staging_tables
                    extra = staging_tables - lake_tables
                    verdict = f"DIVERGES (missing {len(missing)}, extra {len(extra)})"
                mirror_rows.append((db, str(len(lake_tables)), str(len(staging_tables)), verdict))

    # ------------------------------ 8. the escape hatch: role, alarm, assumptions (step 6)
    debug_state = "(not measured)"
    debug_window = "-"
    debug_window_open = False
    debug_trust_ok = False
    debug_session_max = "-"
    debug_rules: list = []  # (rule, state)
    debug_events: list = []  # (time, caller tail)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (escape hatch) ...")
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            DEBUG_ROLE,
            "--query",
            "Role.[AssumeRolePolicyDocument,MaxSessionDuration]",
            "--output",
            "json",
            log=False,
            tolerate="NoSuchEntity",
        )
        if res.tolerated:
            debug_state = "(absent)"
        elif res.ok and res.stdout:
            debug_state = "present"
            trust, max_duration = json.loads(res.stdout)
            debug_session_max = str(max_duration)
            for st in _stmts(trust):
                cond = (st.get("Condition") or {}).get("DateLessThan") or {}
                when = str(cond.get("aws:CurrentTime") or "")
                principals = " ".join(_as_list((st.get("Principal") or {}).get("AWS")))
                if when and "DataScientistProdAccess" in principals:
                    debug_trust_ok = True
                    debug_window = when
                    try:
                        end = _dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
                        debug_window_open = end > _dt.datetime.now(_dt.timezone.utc)
                    except ValueError:
                        debug_window = f"{when} (unparseable)"
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
            if DEBUG_RULE_SUBSTR in str(rname):
                debug_rules.append((str(rname), str(state)))
        res = cli.run(
            "cloudtrail",
            "lookup-events",
            "--lookup-attributes",
            "AttributeKey=EventName,AttributeValue=AssumeRole",
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
            role_arn = str(((ev.get("requestParameters") or {}).get("roleArn")) or "")
            if DEBUG_ROLE not in role_arn:
                continue
            caller = str((ev.get("userIdentity") or {}).get("arn") or "(unknown)")
            debug_events.append((str(ev.get("eventTime") or "-"), caller.rsplit("/", 1)[-1][:40]))

    # --------------------- 9. the persona sets' owed allows, read back (step 5, D18)
    set_rows: list = []  # (set, finding)
    if identity_live:
        cli = cli_for(IDENTITY_PROFILE)
        note(f"measuring {IDENTITY_PROFILE} (permission sets) ...")
        res = cli.run(
            "sso-admin",
            "list-instances",
            "--query",
            "Instances[0].InstanceArn",
            "--output",
            "text",
            log=False,
        )
        instance = (res.stdout or "").strip() if res.ok else ""
        inline_by_name: dict = {}
        if instance:
            res = cli.run(
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                instance,
                "--query",
                "PermissionSets",
                "--output",
                "json",
                log=False,
            )
            for ps_arn in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                r = cli.run(
                    "sso-admin",
                    "describe-permission-set",
                    "--instance-arn",
                    instance,
                    "--permission-set-arn",
                    ps_arn,
                    "--query",
                    "PermissionSet.Name",
                    "--output",
                    "text",
                    log=False,
                )
                name = (r.stdout or "").strip() if r.ok else ""
                if name not in SETS_READ:
                    continue
                r = cli.run(
                    "sso-admin",
                    "get-inline-policy-for-permission-set",
                    "--instance-arn",
                    instance,
                    "--permission-set-arn",
                    ps_arn,
                    "--query",
                    "InlinePolicy",
                    "--output",
                    "text",
                    log=False,
                )
                inline_by_name[name] = r.stdout or "" if r.ok else ""
        prod_inline = inline_by_name.get("DataScientistProdAccess", "")
        if prod_inline:
            set_rows.append(
                (
                    "DataScientistProdAccess",
                    f"names {PROD_WG}: {'yes' if PROD_WG in prod_inline else 'NO (owed by 5.1)'}; "
                    f"names {DEBUG_ROLE}: {'yes' if DEBUG_ROLE in prod_inline else 'NO (owed by 5.1)'}",
                )
            )
        staging_inline = inline_by_name.get("DataScientistStagingAccess", "")
        if staging_inline:
            set_rows.append(
                (
                    "DataScientistStagingAccess",
                    f"DenyEveryWrite: {'yes' if 'DenyEveryWrite' in staging_inline else 'MISSING'}; "
                    f"athena allow: {'ABSENT (correct)' if 'athena:StartQueryExecution' not in staging_inline else 'PRESENT - forbidden'}",
                )
            )

    built = (
        job_role_state == "present"
        or bool(mpg_rows)
        or wg_row is not None
        or any(state == "present" for _b, state, *_ in bucket_rows)
    )

    # -------------------------------------------------------------------------- the checks

    # DT-1: the two buckets - versioned, SSE-KMS, perimeter branches; results expire.
    if prod_live:
        for bucket, state, versioning, sse, branches, expiry in bucket_rows:
            if state == "(absent)":
                (checks.fail if built else checks.note)(
                    "DT-1", f"bucket {bucket}", "absent - expected before step 1.5."
                )
                continue
            problems = []
            if versioning != "Enabled":
                problems.append(f"versioning {versioning}")
            if "kms" not in sse.lower():
                problems.append(f"SSE {sse}")
            if bucket == OUT_BUCKET:  # the derived bucket's policy is module-shaped (header)
                for tag, _key in POLICY_BRANCHES:
                    if tag not in branches:
                        problems.append(f"policy branch '{tag}' missing")
            if bucket == RESULTS_BUCKET and expiry in ("(none)", "-"):
                problems.append("no lifecycle expiry (D19's shape, step 1.1)")
            if problems:
                checks.fail("DT-1", f"bucket {bucket}", "; ".join(problems) + ".")
            else:
                checks.ok(
                    "DT-1", f"bucket {bucket}", f"{sse}, branches {branches}, expiry {expiry}"
                )
        if built and not cmk_present:
            checks.note(
                "DT-1",
                PROD_CMK_ALIAS,
                "alias absent - decision 1 pending, or the foundation key was chosen.",
            )

    # DT-2: the workgroup enforces its configuration - the documented override (1.2).
    if prod_live:
        if wg_row is None:
            (checks.fail if built else checks.note)(
                "DT-2", f"workgroup {PROD_WG}", "absent - expected before step 1.5."
            )
        else:
            enforce, location, cutoff, encryption = wg_row
            problems = []
            if enforce is not True:
                problems.append(
                    "EnforceWorkGroupConfiguration is off - D19's boundary is a suggestion"
                )
            if not location or RESULTS_BUCKET not in str(location):
                problems.append(f"result location {location} is not the results zone")
            if not cutoff:
                problems.append("no BytesScannedCutoffPerQuery (decision 2)")
            if problems:
                checks.fail("DT-2", f"workgroup {PROD_WG}", "; ".join(problems) + ".")
            else:
                checks.ok(
                    "DT-2",
                    f"workgroup {PROD_WG}",
                    f"enforced, results in {RESULTS_BUCKET}, cutoff {cutoff}, {encryption}",
                )

    # DT-3: every package group carries a resource policy (D28 item 6, step 3.2).
    if prod_live:
        if not mpg_rows:
            (checks.fail if built else checks.note)(
                "DT-3",
                f"package groups {MPG_PREFIX}*",
                "none exist - expected before step 3.4.",
            )
        else:
            for group, state in mpg_rows:
                if state.startswith("policy present"):
                    checks.ok("DT-3", f"group {group}", state)
                else:
                    checks.fail(
                        "DT-3",
                        f"group {group}",
                        f"{state} - a group without its policy is Stage 10 improvising one (D28).",
                    )

    # DT-4: the job role - service-only trust, and NO s3 allow reaching a lake bucket (D13).
    if prod_live:
        if job_role_state == "(absent)":
            (checks.fail if built else checks.note)(
                "DT-4", f"role {JOB_ROLE}", "absent - expected before step 3.4."
            )
        elif job_role_state == "present":
            if job_trust_bad:
                for what in sorted(set(job_trust_bad)):
                    checks.fail(
                        "DT-4",
                        f"trust on {JOB_ROLE}",
                        f"{what} - 3.1 admits glue and sagemaker only.",
                    )
            else:
                checks.ok(
                    "DT-4", f"trust on {JOB_ROLE}", "glue + sagemaker service principals only"
                )
            if job_lake_hits:
                for pname, arn in sorted(set(job_lake_hits)):
                    checks.fail(
                        "DT-4",
                        f"D13 on {JOB_ROLE}",
                        f"inline {pname} allows s3 on {arn} - the governed write must be LF-vended only.",
                    )
            else:
                checks.ok(
                    "DT-4",
                    f"D13 on {JOB_ROLE}",
                    "no inline s3 allow reaches a lake bucket (drop-box excepted)",
                )

    # DT-5: the LF settings discipline, three accounts (DL-5's twin).
    for p, param_txt, defaults_txt, admin_txt in lf_rows:
        if p == DATA_PROFILE:
            version = str(lf_data_params.get("CROSS_ACCOUNT_VERSION", ""))
            set_context = str(lf_data_params.get("SET_CONTEXT", "")).upper()
            if version and int(version) >= 4 and set_context == "TRUE":
                checks.ok("DT-5", f"{p} parameters", param_txt)
            else:
                checks.fail(
                    "DT-5",
                    f"{p} parameters",
                    f"{param_txt} - the INT-11 values regressed; stop and re-read Stage 5 step 5.4.",
                )
        else:
            if defaults_txt == "db:0 tbl:0":
                checks.ok("DT-5", f"{p} create-defaults", "emptied (step 1.3/4.1's kill)")
            elif built:
                checks.fail(
                    "DT-5",
                    f"{p} create-defaults",
                    f"{defaults_txt} - IAMAllowedPrincipals defaults still granting; the regrants restrict nothing.",
                )
            else:
                checks.note(
                    "DT-5", f"{p} create-defaults", f"{defaults_txt} - expected before 1.5/4.5."
                )

    # DT-6: the write share arrived and nothing is pending (INT-03, INT-11's tax).
    if data_live and prod_account:
        if write_share_seen:
            checks.ok("DT-6", "the write share", "an INSERT grant names the Production account")
        elif built:
            checks.fail(
                "DT-6",
                "the write share",
                "no INSERT grant to Production in the grantor's listing - step 2.1 has not landed.",
            )
        else:
            checks.note("DT-6", "the write share", "not granted yet - expected before step 2.2.")
    for p, share_name, status in pending_invites:
        checks.fail(
            "DT-6",
            f"RAM invitation in {p}",
            f"{share_name} is {status} - the org-sharing path is not working (INT-11's fallback tax).",
        )

    # DT-7: the drop-box contract names the exact role, on both the bucket and the key.
    if data_live and dropbox_bucket:
        if "NO" in dropbox_stmt:
            (checks.fail if built else checks.note)(
                "DT-7",
                f"drop-box policy ({dropbox_bucket})",
                dropbox_stmt + " - the Stage 5 statement and the 3.1 contract disagree.",
            )
        elif dropbox_stmt.startswith("names"):
            checks.ok("DT-7", f"drop-box policy ({dropbox_bucket})", dropbox_stmt)
        if dropbox_key_names_role == "NO":
            (checks.fail if built else checks.note)(
                "DT-7",
                "drop-box KMS grant",
                f"neither key policy nor grants name {JOB_ROLE} - the pickup dies as an S3 error (2.5).",
            )
        elif dropbox_key_names_role == "yes":
            checks.ok("DT-7", "drop-box KMS grant", f"the key names {JOB_ROLE}")

    # DT-8: Staging touches nothing governed - no link to Data Governance; the mirror agrees.
    if staging_live:
        if staging_links_to_data:
            for db, target in staging_links_to_data:
                checks.fail(
                    "DT-8",
                    f"staging link {db}",
                    f"resolves into Data Governance ({target}) - D20 forbids the share; remove it.",
                )
        else:
            checks.ok("DT-8", "staging isolation", "no resource link reaches Data Governance")
        for db, lake_n, staging_n, verdict in mirror_rows:
            if verdict == "mirrored":
                checks.ok("DT-8", f"mirror {db}", f"{staging_n} table(s), names agree")
            elif verdict.startswith("DIVERGES"):
                checks.fail(
                    "DT-8",
                    f"mirror {db}",
                    f"{verdict} - a drifted mirror produces false test failures (4.1, decision 3).",
                )

    # DT-9: the escape hatch - windowed trust, closed at rest, 1 h sessions, alarmed.
    if prod_live:
        if debug_state == "(absent)":
            (checks.fail if built else checks.note)(
                "DT-9", f"role {DEBUG_ROLE}", "absent - expected before step 3.4."
            )
        elif debug_state == "present":
            if not debug_trust_ok:
                checks.fail(
                    "DT-9",
                    f"trust on {DEBUG_ROLE}",
                    "no DateLessThan window bound to the DataScientistProdAccess principal (6.1).",
                )
            elif debug_window_open:
                checks.note(
                    "DT-9",
                    f"window on {DEBUG_ROLE}",
                    f"OPEN until {debug_window} - close it in the same sitting (6.3).",
                )
            else:
                checks.ok("DT-9", f"window on {DEBUG_ROLE}", f"closed (ends {debug_window})")
            if debug_session_max not in ("-",) and int(debug_session_max) > 3600:
                checks.fail(
                    "DT-9",
                    f"session length on {DEBUG_ROLE}",
                    f"{debug_session_max}s - 6.1 caps it at 3600.",
                )
            if not debug_rules:
                (checks.fail if debug_state == "present" else checks.note)(
                    "DT-9", "the assumption alarm", f"no *{DEBUG_RULE_SUBSTR}* rule (6.2)."
                )
            else:
                for rname, state in debug_rules:
                    if state != "ENABLED":
                        checks.fail("DT-9", f"rule {rname}", f"state {state} - not watching.")
                    else:
                        checks.ok("DT-9", f"rule {rname}", "ENABLED")

    # DT-10: the persona halves, read through the delegated administrator (step 5).
    for set_name, finding in set_rows:
        if "NO (owed" in finding and built:
            checks.fail("DT-10", set_name, finding + " - apply step 5.3.")
        elif "MISSING" in finding or "forbidden" in finding:
            checks.fail("DT-10", set_name, finding + ".")
        elif "NO (owed" in finding:
            checks.note("DT-10", set_name, finding + ".")
        else:
            checks.ok("DT-10", set_name, finding)

    # ---------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("DEPLOY TARGETS - the Stage 9 evidence: producer path, registry, mirrors")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/deploytargets.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The Production data platform: buckets, CMK, the enforced workgroup
  3. The runtime: the job role (D13) and the Model Registry (D28)
  4. The Lake Formation settings, every account that has any (DT-5)
  5. The write share, the links, the invitations (INT-03)
  6. The drop-box contract, both sides (INT-10)
  7. The Staging mirror, and the absence that is a control (D20)
  8. The escape hatch: role, alarm, assumptions (step 6)
  9. The persona sets' owed allows (step 5)
 10. CHECKS
 11. The accounts nothing here is measuring
 12. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 9 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - THIS IS A CONTROL-PLANE READING. Whether the LF write LANDS, the direct
    PutObject DIES, the pickup EMPTIES the letterbox and the console survives the
    endpoint condition are the stage's behavioural proofs (Lesson 20).
  - RUN IT AFTER EVERY APPLY THAT TOUCHES DataLakeSettings, not at stage end -
    DT-5 is DL-5's discipline extended to three accounts, and the failure it
    watches for is silent.

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
        rep.h1("2. The Production data platform: buckets, CMK, the enforced workgroup")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            rep.tabulate(
                ["BUCKET\tSTATE\tVERSIONING\tSSE\tPOLICY BRANCHES\tEXPIRY"]
                + ["\t".join(r) for r in bucket_rows]
            )
            rep.line()
            rep.line(f"{PROD_CMK_ALIAS}: {'present' if cmk_present else '(absent)'}")
            if wg_row is not None:
                enforce, location, cutoff, encryption = wg_row
                rep.line(
                    f"workgroup {PROD_WG}: enforce={enforce} location={location} "
                    f"cutoff={cutoff} encryption={encryption}"
                )
            else:
                rep.line(f"workgroup {PROD_WG}: (absent)")
            rep.text("""
The branches are PRESENCE, never sufficiency (vpce/ip/via - Stage 5 step 1.3's
shape). One enforced result location, not one per principal: within-persona
visibility of query output is the stage's stated limit (risk 6), and the CMK is
what keeps it from the approvers and from Staging (D31).""")

        # ==============================================================================
        rep.h1("3. The runtime: the job role (D13) and the Model Registry (D28)")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            rep.line(f"role {JOB_ROLE}: {job_role_state}")
            if job_lake_hits:
                rep.tabulate(
                    ["INLINE POLICY\tLAKE-BUCKET RESOURCE"]
                    + ["\t".join(r) for r in sorted(set(job_lake_hits))]
                )
            rep.line()
            if mpg_rows:
                rep.tabulate(["PACKAGE GROUP\tRESOURCE POLICY"] + ["\t".join(r) for r in mpg_rows])
            else:
                rep.line(f"No package group matches {MPG_PREFIX}*.")
            rep.text("""
D13 read from the role's own policies: the governed write must arrive only
through lakeformation:GetDataAccess vending, so an inline s3 allow naming a lake
bucket is the finding, and the drop-box statements are the named exception. The
Staging principals join the group policies at the vend (step 4.6).""")

        # ==============================================================================
        rep.h1("4. The Lake Formation settings, every account that has any (DT-5)")
        if lf_rows:
            rep.tabulate(
                ["PROFILE\tPARAMETERS\tCREATE-DEFAULTS\tADMINS"] + ["\t".join(r) for r in lf_rows]
            )
        else:
            rep.line("No account with an LF read was measured.")
        rep.text("""
DL-5's discipline, extended: a DataLakeSettings apply REPLACES the whole
structure in whichever account it runs, so each of the three accounts now has
parameters someone must carry explicitly. Read this section after every apply
of data-governance/data/, production/data/ or staging/data/.""")

        # ==============================================================================
        rep.h1("5. The write share, the links, the invitations (INT-03)")
        if share_perm_rows:
            rep.tabulate(
                ["PRINCIPAL (TAIL)\tRESOURCE\tPERMISSIONS"]
                + ["\t".join(r) for r in share_perm_rows]
            )
        elif data_live:
            rep.line("No grantor-side permission names the Production account yet (pre-2.2).")
        if link_rows:
            rep.line()
            rep.tabulate(
                ["PROFILE\tDATABASE\tTARGET CATALOG\tTARGET DB"] + ["\t".join(r) for r in link_rows]
            )
        if pending_invites:
            rep.line()
            rep.tabulate(["PROFILE\tSHARE\tSTATUS"] + ["\t".join(r) for r in pending_invites])
        rep.text("""
INSERT in the permissions column is the write share (ALTER rides with it - an
Iceberg commit rewrites table metadata). A PENDING invitation anywhere is the
org-sharing path not working: INT-11's fallback tax, reappearing at every
rebuild. Whether the write WORKS is 2.4's job, not this listing.""")

        # ==============================================================================
        rep.h1("6. The drop-box contract, both sides (INT-10)")
        if not data_live:
            rep.line(f"{DATA_PROFILE} was not measured - nothing to show.")
        elif not dropbox_bucket:
            rep.line(
                "No bucket matching *dropbox* in Data Governance (Stage 5 decision 3 creates it)."
            )
        else:
            rep.line(f"bucket {dropbox_bucket}: {dropbox_stmt}")
            rep.line(f"drop-box key names {JOB_ROLE}: {dropbox_key_names_role}")
            rep.text("""
Stage 5 wrote both against this stage's role name before the role existed - the
contract this section watches. A NO on either line is the pickup failing later
with an error that names S3 and means KMS or a typo (2.5, D25).""")

        # ==============================================================================
        rep.h1("7. The Staging mirror, and the absence that is a control (D20)")
        if not staging_live:
            rep.line(f"{STAGING_PROFILE} has no profile until the vend - the whole section waits.")
        else:
            if staging_links_to_data:
                rep.tabulate(
                    ["LINK\tRESOLVES INTO"] + ["\t".join(r) for r in staging_links_to_data]
                )
            else:
                rep.line("No Staging resource link reaches Data Governance - D20 holding.")
            if mirror_rows:
                rep.line()
                rep.tabulate(
                    ["DATABASE\tLAKE TABLES\tSTAGING TABLES\tVERDICT"]
                    + ["\t".join(r) for r in mirror_rows]
                )
            if staging_wg_row is not None:
                enforce, location, cutoff = staging_wg_row
                rep.line()
                rep.line(
                    f"workgroup {STAGING_WG}: enforce={enforce} location={location} cutoff={cutoff}"
                )
            rep.line(f"role {STAGING_JOB_ROLE}: {staging_job_state}")
            rep.text("""
The mirror agreeing is 4.1 working; the link NOT existing is the control (D20:
Staging is never on the share). The workgroup serves the integration tests and
the app - DataScientistStagingAccess holds no Athena at all (Stage 2).""")

        # ==============================================================================
        rep.h1("8. The escape hatch: role, alarm, assumptions (step 6)")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            rep.line(f"role {DEBUG_ROLE}: {debug_state}")
            if debug_state == "present":
                rep.line(
                    f"window: {'OPEN' if debug_window_open else 'closed'} (DateLessThan {debug_window}); "
                    f"max session {debug_session_max}s"
                )
            if debug_rules:
                rep.tabulate(["RULE\tSTATE"] + ["\t".join(r) for r in debug_rules])
            else:
                rep.line(f"No *{DEBUG_RULE_SUBSTR}* rule (pre-6.2).")
            if debug_events:
                rep.line()
                rep.tabulate(["TIME\tCALLER"] + ["\t".join(r) for r in debug_events[:25]])
            else:
                rep.line("No AssumeRole event names the debug role in the last 90 days.")
            rep.text("""
Closed at rest is the design: the DateLessThan default sits in the past, an
approval is a recorded apply, and EVERY assumption alarms (not just misuse).
The read-only-by-API shape is imposed by the Workloads OU SCP - a session
under this role cannot become a notebook (6.3 proves it once).""")

        # ==============================================================================
        rep.h1("9. The persona sets' owed allows (step 5)")
        if set_rows:
            rep.tabulate(["PERMISSION SET\tFINDING"] + ["\t".join(r) for r in set_rows])
        elif identity_live:
            rep.line("Neither set answered through the delegated administrator.")
        else:
            rep.line(f"{IDENTITY_PROFILE} was not measured - nothing to show.")
        rep.text("""
Read through the Identity Center delegated administrator (D10), the same path
vpn.py uses for the deny Sids. The Prod set gains the workgroup and the debug
role at 5.1; the Staging set gains NOTHING here - DenyEveryWrite present and no
Athena allow is that set read back correct (5.2, Lesson 22).""")

        # ==============================================================================
        rep.h1("10. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  DT-1   the two buckets: versioned, SSE-KMS, perimeter branches, results expiry (1.1)
  DT-2   the workgroup enforces location + scan limit (1.2, D19)
  DT-3   every awsds-prod-model-* group carries a resource policy (3.2, D28 item 6)
  DT-4   the job role: service-only trust, no s3 allow on lake buckets (3.1, D13)
  DT-5   the LF settings discipline in all three accounts (1.3/2.2/4.1, DL-5's twin)
  DT-6   the write share granted, no pending invitation (2.1-2.2, INT-03/INT-11)
  DT-7   the drop-box statement and key both name awsds-prod-job-exec (2.5, INT-10)
  DT-8   no Staging link to Data Governance; the mirror agrees (4.1, D20)
  DT-9   the escape hatch: windowed trust, closed at rest, <=1h, alarmed (6.1-6.2)
  DT-10  the persona halves read back through the delegated admin (5.1-5.2)""")

        # ==============================================================================
        rep.h1("11. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 10 as a pass.

  - `Staging` has no profile until the vend - sections 5, 7 and the DT-8 pair
    are blind until then, and INT-07's registry half (4.6) with them.
  - Development appears here only as a principal in the group policies -
    INT-04's behavioural half (3.4) is a session, not a listing.
  - Log Archive and Audit hold no profile by design; nothing in this stage
    lives there.""")

        # ==============================================================================
        rep.h1("12. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/deploytargets.py")

    # ------------------------------------------------------------------------------ run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 12)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 10)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
