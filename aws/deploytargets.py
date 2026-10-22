#!/usr/bin/env -S uv run --quiet
# deploytargets.py - Stage 9's evidence, producer and targets side by side: the Production
# data platform (buckets, CMK, the enforced workgroup), the runtime (the job role under
# D13, the model package groups with their resource policies), the Lake Formation settings
# in every account that has any (DT-5), the write share with its links and invitations
# (INT-03), the drop-box contract from both sides (INT-10), Staging's read-only share and the
# absence of any copy (decision 3), the escape hatch with its alarm, the persona sets' owed
# allows read back through the delegated admin, and the job settings on the Workloads OU (DT-11).
#
#   needs:    a live SSO session, and nothing else:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/deploytargets.py                    # every awsds-* profile
#             ./aws/deploytargets.py awsds-infra-prod   # only the ones named
#             python3 aws/deploytargets.py -            # CloudShell, ambient credentials
#   writes:   aws/output/deploytargets.txt   (untracked - see .gitignore)
#   reads:    s3api get-bucket-*, kms list-aliases/get-key-policy/list-grants,
#             athena get-work-group, logs describe-log-groups,
#             sagemaker list-model-package-groups /
#             get-model-package-group-policy, iam get-role/list-role-policies/
#             get-role-policy, lakeformation get-data-lake-settings/list-permissions,
#             glue get-databases/get-tables, ram get-resource-share-invitations,
#             events list-rules, cloudtrail lookup-events, sso-admin (reads only),
#             organizations list-roots/list-organizational-units-for-parent/
#             list-policies-for-target/describe-policy, sts get-caller-identity. It never
#             creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# The subject is the producer path between accounts, so this script is multi-profile: the
# lake and the drop-box live in Data Governance while the only principal allowed to write
# them lives in Production (D22, D25), Staging's value is what it does not reach (D20), and
# the persona allows and the OU documents are read from Identity, the delegated administrator.
# Section 1 prints the caller ARN of every profile.
#
# The contracts it reads, each named in the stage file so a rename fails loudly:
#   - the job role is awsds-prod-job-exec (step 3.1 - the name Stage 5a step 1.4's drop-box
#     statement and key grant carry)
#   - the workgroup is awsds-prod-athena; Staging's is awsds-staging-athena (steps 1.2, 4.2)
#   - the buckets are awsds-prod-outputs and awsds-prod-derived (step 1.1 - the derived
#     zone arrives with the consumer-data call, so its policy is module-shaped: TLS-only
#     plus the presigned cap, no perimeter branches - those belong to the lake and outputs)
#   - the package groups match awsds-prod-model-* (step 3.2)
#   - the debug role is awsds-prod-debug, its rules awsds-prod-debug-assume and
#     awsds-prod-debug-assume-console, in the state that receives AssumeRole (step 6)
#   - Staging's job role is awsds-staging-job-exec (step 4.3)
#   - the Workloads OU carries awsds-org-scp-ou-workloads, holding sagemaker-denies' five Sids
#     and DenySageMakerServerlessInference (steps 3.5, 3.7)
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - The behavioural proofs - the LF write landing, the direct PutObject dying, the
#     pickup emptying the letterbox, the console fraction (INT-06) - are the stage's own
#     (Lesson 20).
#   - Whether the write share works is 2.4's job run; this file only shows it was granted.
#   - `Staging` rows need the `awsds-infra-staging` profile; the account is the renamed
#     `Development` (Stage 6b), so no vend is owed.

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
# EventBridge classes STS AssumeRole as a read-only management event, and a rule in plain ENABLED
# state receives none: only this state delivers it (cicd.py CI-7, the same reading).
ALARM_RULE_STATE = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"
PROD_WG = "awsds-prod-athena"
STAGING_WG = "awsds-staging-athena"
STAGING_JOB_ROLE = "awsds-staging-job-exec"
STAGING_CMK_ALIAS = "alias/awsds-staging-data"  # staging/data/'s key (4.1)
OUT_BUCKET = "awsds-prod-outputs"
# consumer-data v0.6.0 (2026-08-26) dropped the derived bucket and the enforced workgroup from
# the module: D19 was revised and the Interactive derived zone re-homed onto the SMUS project
# path. Neither deployment target has SMUS (D17/D28), so the re-homed zone exists in neither.
# Where Production's and Staging's results land is Stage 9's to re-decide at revision, and
# STAGING_WG's result location was never named anywhere. Both expectations stand as the stage
# file wrote them and are re-read there.
RESULTS_BUCKET = "awsds-prod-derived"  # results/ is a prefix family in it, never a bucket
MPG_PREFIX = "awsds-prod-model-"
PROD_CMK_ALIAS = "alias/awsds-prod-data"  # one data CMK per account
DROPBOX_SUBSTR = "dropbox"
LAKE_BUCKET_SUBSTR = "awsds-data-"
LAKE_DBS = ("raw", "curated")  # the lake databases a consumer reads through its share (2.1, 4.1)
# What a read share grants: Staging receives these and nothing else (decision 3).
READ_PERMISSIONS = {"DESCRIBE", "SELECT"}
SETS_READ = ("DataScientistProdAccess", "DataScientistStagingAccess")
WORKLOADS_OU = "Workloads"
WORKLOADS_DOC = "awsds-org-scp-ou-workloads"
# terraform-modules/sagemaker-denies' Sids, which the Workloads document carries (decision 9,
# shape (a)), and step 3.7's own deny beside them.
JOB_DENY_SIDS = (
    "DenySageMakerJobsOffVpc",
    "DenySageMakerInstanceCeiling",
    "DenySageMakerJobsWithoutNetworkIsolation",
    "DenySageMakerJobsWithoutInterContainerEncryption",
    "DenySageMakerJobsWithoutVolumeEncryption",
    "DenySageMakerServerlessInference",
)

# The job log groups each job role's slice declares with a retention (steps 3.1 and 4.3, EXC-10):
# the names SageMaker and Glue write to by default, which each service creates with no retention
# when a job runs before the slice (Stage 18 4.4 did so in Staging on 2026-10-19).
JOB_LOG_GROUPS = (
    "/aws/sagemaker/ProcessingJobs",
    "/aws/sagemaker/TrainingJobs",
    "/aws/sagemaker/TransformJobs",
    "/aws-glue/jobs/output",
    "/aws-glue/jobs/error",
    "/aws-glue/jobs/logs-v2",
)

# Step 5.1's marks in DataScientistProdAccess, one apply: the workgroup, the debug role and the
# Redshift deny land together, so some of them without the others is a partial 5.3.
PROD_SET_OWED = (PROD_WG, DEBUG_ROLE, "DenyMintingARedshiftDatabaseSession")

# The branches the outputs bucket's network deny carries (Stage 9 step 1.1, D39): the endpoint
# and service branches, and a principal branch for DataScientistProdAccess's read of the named
# prefixes. An address branch is refused: a person reaches AWS by identity from any network.
POLICY_BRANCHES = (
    ("vpce", "aws:SourceVpce"),
    ("via", "aws:ViaAWSService"),
    ("prin", "aws:PrincipalArn"),
)
REFUSED_BRANCH = ("ip", "aws:SourceIp")


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
                    "/".join(tag for tag, key in (*POLICY_BRANCHES, REFUSED_BRANCH) if key in text)
                    or "(none match)"
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
    def read_job_role(cli: AwsCli, role: str, dropbox_excepted: bool) -> tuple:
        """The role's state, its trust findings, and its s3 allows reaching a lake bucket (D13).

        The drop-box is the producer's one excepted bucket (Stage 5a decision 3). In Staging it is a
        finding like every other lake bucket: it reads the lake through Lake Formation alone (D13).
        """
        trust_bad: list = []
        lake_hits: list = []  # (policy, resource) - an s3 statement reaching a lake bucket
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            role,
            "--query",
            "Role.AssumeRolePolicyDocument",
            "--output",
            "json",
            log=False,
            tolerate="NoSuchEntity",
        )
        if res.tolerated:
            return "(absent)", trust_bad, lake_hits
        if not (res.ok and res.stdout):
            return "(failed)", trust_bad, lake_hits
        for st in _stmts(json.loads(res.stdout)):
            principal = st.get("Principal", {}) or {}
            for svc in _as_list(principal.get("Service")):
                if str(svc) not in ("glue.amazonaws.com", "sagemaker.amazonaws.com"):
                    trust_bad.append(f"service {svc}")
            if principal.get("AWS") or principal.get("Federated"):
                trust_bad.append("a non-service principal in the trust policy")
        res = cli.run(
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
        for pname in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            r = cli.run(
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
            if not (r.ok and r.stdout):
                continue
            for st in _stmts(json.loads(r.stdout)):
                actions = " ".join(_as_list(st.get("Action")))
                if "s3:" not in actions or str(st.get("Effect")) != "Allow":
                    continue
                for arn in _as_list(st.get("Resource")):
                    if LAKE_BUCKET_SUBSTR in str(arn) and not (
                        dropbox_excepted and DROPBOX_SUBSTR in str(arn)
                    ):
                        lake_hits.append((str(pname), str(arn)))
        return "present", trust_bad, lake_hits

    job_role_state = "(not measured)"
    job_trust_bad: list = []
    job_lake_hits: list = []  # (policy, resource) - an s3 statement reaching a lake bucket
    mpg_rows: list = []  # (group, policy state)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (job role, registry) ...")
        job_role_state, job_trust_bad, job_lake_hits = read_job_role(
            cli, JOB_ROLE, dropbox_excepted=True
        )
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

    # ------------------- 3b. the job log groups, both accounts (steps 3.1 and 4.3, EXC-10)
    log_rows: list = []  # (profile, group, retention, key) - "(absent)" when the group does not exist
    data_key_arns: dict = {}  # profile -> the account data key's ARN, the job groups' key
    for p, alias in ((PROD_PROFILE, PROD_CMK_ALIAS), (STAGING_PROFILE, STAGING_CMK_ALIAS)):
        if p not in live:
            continue
        found: dict = {}
        for prefix in ("/aws/sagemaker/", "/aws-glue/"):
            res = cli_for(p).run(
                "logs",
                "describe-log-groups",
                "--log-group-name-prefix",
                prefix,
                "--query",
                "logGroups[].[logGroupName,retentionInDays,kmsKeyId]",
                "--output",
                "json",
                log=False,
            )
            for name, days, key in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                found[str(name)] = (days, key)
        res = cli_for(p).run(
            "kms",
            "describe-key",
            "--key-id",
            alias,
            "--query",
            "KeyMetadata.Arn",
            "--output",
            "text",
            log=False,
            tolerate="NotFoundException",
        )
        if res.ok and not res.tolerated and res.stdout.strip():
            data_key_arns[p] = res.stdout.strip()
        for group in JOB_LOG_GROUPS:
            if group not in found:
                log_rows.append((p, group, "(absent)", "-"))
            else:
                days, key = found[group]
                log_rows.append((p, group, f"{days}d" if days else "(none)", key or "(AWS-owned)"))

    # -------------------- 4. the Lake Formation settings, every account that has any
    lf_rows: list = []  # (profile, parameters, create defaults, admins)
    lf_params: dict = {}  # profile -> DataLakeSettings.Parameters
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
        lf_params[p] = params or {}
        param_txt = ",".join(f"{k}={v}" for k, v in sorted((params or {}).items())) or "(empty)"
        defaults_txt = f"db:{len(db_defaults or [])} tbl:{len(tb_defaults or [])}"
        admin_txt = " ".join(str(a).rsplit("/", 1)[-1] for a in (admins or [])) or "(none)"
        lf_rows.append((p, param_txt, defaults_txt, admin_txt))

    # ------------------------- 5. the write share, the links, the invitations (INT-03)
    share_perm_rows: list = []  # (principal tail, resource, permissions)
    write_share_seen = False
    staging_account = account_of.get(STAGING_PROFILE)
    staging_share_rows: list = []  # (resource, permissions) granted to Staging's account
    staging_write_grants: list = []  # (resource, permissions beyond DESCRIBE and SELECT)
    staging_local_dbs: list = []  # Staging's databases that are not resource links
    share_listed = False  # the grantor's listing read to its last page
    link_rows: list = []  # (profile, database, target catalog tail, target database)
    pending_invites: list = []  # (profile, share name, status)
    if data_live:
        cli = cli_for(DATA_PROFILE)
        note(f"measuring {DATA_PROFILE} (grantor permissions) ...")
        # ListPermissions has no CLI paginator: one call answers the first page and a NextToken.
        listing = cli.pages("lakeformation", "list-permissions")
        share_listed = listing.complete
        for entry in listing.items("PrincipalResourcePermissions"):
            principal = str((entry.get("Principal") or {}).get("DataLakePrincipalIdentifier") or "")
            granted = list(entry.get("Permissions") or [])
            optioned = list(entry.get("PermissionsWithGrantOption") or [])
            perms = ",".join(granted)
            resource = entry.get("Resource") or {}
            if "Table" in resource:
                r = resource["Table"]
                where = f"table:{r.get('DatabaseName')}.{r.get('Name') or '*'}"
            elif "Database" in resource:
                where = f"database:{resource['Database'].get('Name')}"
            else:
                where = next(iter(resource.keys()), "?")
            if staging_account and staging_account in principal:
                staging_share_rows.append((where, perms))
                beyond = sorted(set(granted + optioned) - READ_PERMISSIONS)
                if beyond:
                    staging_write_grants.append((where, ",".join(beyond)))
            if not prod_account or prod_account not in principal:
                continue
            share_perm_rows.append((principal[-12:], where, perms))
            if "INSERT" in perms:
                write_share_seen = True
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
            elif p == STAGING_PROFILE:
                staging_local_dbs.append(str(name))
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

    # --------------------------- 7. Staging's read of the lake, through its share (decision 3)
    staging_links_to_data: list = []  # resource links resolving into Data Governance
    staging_copies: list = []  # (local database, table) named like a lake table
    staging_wg_row = None
    staging_job_state = "(not measured)"
    staging_trust_bad: list = []
    staging_lake_hits: list = []  # (policy, resource) - any lake bucket, the drop-box included
    staging_cmk_present = False
    if staging_live:
        for p, db, catalog_tail, target_db in link_rows:
            if p == STAGING_PROFILE and data_account and data_account.endswith(catalog_tail):
                staging_links_to_data.append((db, target_db))
        cli = cli_for(STAGING_PROFILE)
        note(f"measuring {STAGING_PROFILE} (the read share) ...")
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
        staging_job_state, staging_trust_bad, staging_lake_hits = read_job_role(
            cli, STAGING_JOB_ROLE, dropbox_excepted=False
        )
        res = cli.run(
            "kms", "list-aliases", "--query", "Aliases[].AliasName", "--output", "json", log=False
        )
        aliases = json.loads(res.stdout or "[]") if res.ok and res.stdout else []
        staging_cmk_present = STAGING_CMK_ALIAS in aliases
        # A copy reads as a local table carrying a lake table's name: the application's own tables are
        # its schemas, and a governed table is read through the links, never re-created here.
        if data_live and staging_local_dbs:
            lake_tables: set = set()
            for db in LAKE_DBS:
                r = cli_for(DATA_PROFILE).run(
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
                    lake_tables.update(str(t) for t in json.loads(r.stdout))
            for db in staging_local_dbs:
                r = cli.run(
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
                for t in json.loads(r.stdout or "[]") if r.ok and r.stdout else []:
                    if str(t) in lake_tables:
                        staging_copies.append((db, str(t)))

    # ------------------------------ 8. the escape hatch: role, alarm, assumptions (step 6)
    debug_state = "(not measured)"
    debug_window = "-"
    debug_window_open = False
    debug_trust_ok = False
    debug_region_pinned = False
    debug_session_max = "-"
    debug_rules: list = []  # (rule, state)
    debug_events: list = []  # (time, caller tail)
    debug_arn = ""
    debug_read = False  # the role's AssumeRole history answered
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (escape hatch) ...")
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            DEBUG_ROLE,
            "--query",
            "Role.[AssumeRolePolicyDocument,MaxSessionDuration,Arn]",
            "--output",
            "json",
            log=False,
            tolerate="NoSuchEntity",
        )
        if res.tolerated:
            debug_state = "(absent)"
        elif res.ok and res.stdout:
            debug_state = "present"
            trust, max_duration, debug_arn = json.loads(res.stdout)
            debug_session_max = str(max_duration)
            for st in _stmts(trust):
                cond = (st.get("Condition") or {}).get("DateLessThan") or {}
                when = str(cond.get("aws:CurrentTime") or "")
                principals = " ".join(_as_list((st.get("Principal") or {}).get("AWS")))
                if when and "DataScientistProdAccess" in principals:
                    debug_trust_ok = True
                    debug_window = when
                    pinned = (st.get("Condition") or {}).get("StringEquals") or {}
                    debug_region_pinned = pinned.get("aws:RequestedRegion") == context.REGION
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
        # Looked up by the role's ARN, every page: Production held 80,211 AssumeRole events of
        # every kind on 2026-10-21, about 1,100 a day, and the latest 50 spanned 95 minutes.
        raws: list = []
        if debug_arn:
            res = cli.run(
                "cloudtrail",
                "lookup-events",
                "--lookup-attributes",
                f"AttributeKey=ResourceName,AttributeValue={debug_arn}",
                "--query",
                "Events[?EventName=='AssumeRole'].CloudTrailEvent",
                "--output",
                "json",
            )
            debug_read = res.ok
            raws = json.loads(res.stdout or "[]") if res.ok else []
        for raw in raws:
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
    set_rows: list = []  # (set, finding, verdict: ok, owed, partial or bad)
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
            marks = [m for m in PROD_SET_OWED if m in prod_inline]
            set_rows.append(
                (
                    "DataScientistProdAccess",
                    "; ".join(f"{m}: {'yes' if m in marks else 'no'}" for m in PROD_SET_OWED),
                    "ok"
                    if len(marks) == len(PROD_SET_OWED)
                    else ("owed" if not marks else "partial"),
                )
            )
        staging_inline = inline_by_name.get("DataScientistStagingAccess", "")
        if staging_inline:
            write_denied = "DenyEveryWrite" in staging_inline
            athena_absent = "athena:StartQueryExecution" not in staging_inline
            set_rows.append(
                (
                    "DataScientistStagingAccess",
                    f"DenyEveryWrite: {'yes' if write_denied else 'MISSING'}; "
                    f"athena allow: {'absent (correct)' if athena_absent else 'present - forbidden'}",
                    "ok" if write_denied and athena_absent else "bad",
                )
            )

    # ------------------- 10. the job settings on the Workloads OU (step 3.5, decision 9)
    workloads_attached = False
    workloads_sids: list = []
    if identity_live:
        cli = cli_for(IDENTITY_PROFILE)
        note(f"measuring {IDENTITY_PROFILE} (the {WORKLOADS_OU} OU document) ...")
        res = cli.run("organizations", "list-roots", "--query", "Roots[0].Id", "--output", "text")
        root_id = (res.stdout or "").strip() if res.ok else ""
        ou_id = ""
        if root_id:
            res = cli.run(
                "organizations",
                "list-organizational-units-for-parent",
                "--parent-id",
                root_id,
                "--query",
                f"OrganizationalUnits[?Name=='{WORKLOADS_OU}'].Id | [0]",
                "--output",
                "text",
            )
            ou_id = (res.stdout or "").strip() if res.ok else ""
        policy_id = ""
        if ou_id and ou_id != "None":
            res = cli.run(
                "organizations",
                "list-policies-for-target",
                "--target-id",
                ou_id,
                "--filter",
                "SERVICE_CONTROL_POLICY",
                "--query",
                f"Policies[?Name=='{WORKLOADS_DOC}'].Id | [0]",
                "--output",
                "text",
            )
            policy_id = (res.stdout or "").strip() if res.ok else ""
        if policy_id and policy_id != "None":
            workloads_attached = True
            res = cli.run(
                "organizations",
                "describe-policy",
                "--policy-id",
                policy_id,
                "--query",
                "Policy.Content",
                "--output",
                "text",
            )
            try:
                content = json.loads(res.stdout or "{}") if res.ok else {}
            except ValueError:
                content = {}
            workloads_sids = [str(st.get("Sid") or "") for st in _stmts(content)]

    # Each check fails on an absence only once the pass that creates the object has applied, and
    # notes it before (Lesson 50): a stage applied pass by pass would otherwise read red at every
    # pass but its last. A pass is read from its own objects:
    #   pass 1  production/sagemaker/ - the job role, a package group or the debug role stands
    #   pass 3  production/data/ - a bucket, the workgroup or the account data CMK stands; its first,
    #           targeted apply seats Production's data lake administrator (1.3, Recipe D)
    #   pass 4  identity/sso/ - one of step 5.1's statements is in DataScientistProdAccess (DT-10)
    #   pass 5  staging/data/ - a resource link, the workgroup or the account data CMK stands, and
    #           its targeted apply seats Staging's administrator; staging/sagemaker/ - the job role
    runtime_built = job_role_state == "present" or bool(mpg_rows) or debug_state == "present"
    prod_data_built = (
        cmk_present
        or wg_row is not None
        or any(state == "present" for _b, state, *_ in bucket_rows)
    )
    staging_data_built = (
        bool(staging_links_to_data) or staging_wg_row is not None or staging_cmk_present
    )
    lf_seated = {
        p: admins != "(none)" for p, _params, _defaults, admins in lf_rows if admins != "-"
    }

    # -------------------------------------------------------------------------- the checks

    # DT-1: the two buckets - versioned, SSE-KMS, perimeter branches; results expire.
    if prod_live:
        for bucket, state, versioning, sse, branches, expiry in bucket_rows:
            if state == "(absent)":
                if prod_data_built:
                    checks.fail(
                        "DT-1",
                        f"bucket {bucket}",
                        "absent while production/data/'s other objects stand - a partial 1.5.",
                    )
                else:
                    checks.note("DT-1", f"bucket {bucket}", "absent - expected before step 1.5.")
                continue
            problems = []
            if versioning != "Enabled":
                problems.append(f"versioning {versioning}")
            if "kms" not in sse.lower():
                problems.append(f"SSE {sse}")
            if bucket == OUT_BUCKET:  # the derived bucket's policy is module-shaped (header)
                for tag, _key in POLICY_BRANCHES:
                    if tag not in branches.split("/"):
                        problems.append(f"policy branch '{tag}' missing")
                if REFUSED_BRANCH[0] in branches.split("/"):
                    problems.append(
                        "an address branch (aws:SourceIp) - D39 admits the persona by principal"
                    )
            if bucket == RESULTS_BUCKET and expiry in ("(none)", "-"):
                problems.append("no lifecycle expiry (D19's shape, step 1.1)")
            if problems:
                checks.fail("DT-1", f"bucket {bucket}", "; ".join(problems) + ".")
            else:
                checks.ok(
                    "DT-1", f"bucket {bucket}", f"{sse}, branches {branches}, expiry {expiry}"
                )
        if prod_data_built and not cmk_present:
            checks.note(
                "DT-1",
                PROD_CMK_ALIAS,
                "alias absent - decision 1 pending, or the foundation key was chosen.",
            )

    # DT-2: the workgroup enforces its configuration - the documented override (1.2).
    if prod_live:
        if wg_row is None:
            (checks.fail if prod_data_built else checks.note)(
                "DT-2",
                f"workgroup {PROD_WG}",
                "absent while production/data/'s other objects stand - a partial 1.5."
                if prod_data_built
                else "absent - expected before step 1.5.",
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
            (checks.fail if runtime_built else checks.note)(
                "DT-3",
                f"package groups {MPG_PREFIX}*",
                "none while production/sagemaker/'s other objects stand - a partial 3.4."
                if runtime_built
                else "none exist - expected before step 3.4.",
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

    # DT-4: the job role - service-only trust, and no s3 allow reaching a lake bucket (D13).
    if prod_live:
        if job_role_state == "(absent)":
            (checks.fail if runtime_built else checks.note)(
                "DT-4",
                f"role {JOB_ROLE}",
                "absent while production/sagemaker/'s other objects stand - a partial 3.4."
                if runtime_built
                else "absent - expected before step 3.4.",
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

    # DT-4, Staging: the same trust, and no s3 allow reaching any lake bucket, the drop-box included
    # (4.3, D13). Absent until 4.5 applies staging/sagemaker/.
    if staging_live:
        if staging_job_state == "(absent)":
            checks.note("DT-4", f"role {STAGING_JOB_ROLE}", "absent - expected before step 4.5.")
        elif staging_job_state == "present":
            if staging_trust_bad:
                for what in sorted(set(staging_trust_bad)):
                    checks.fail(
                        "DT-4",
                        f"trust on {STAGING_JOB_ROLE}",
                        f"{what} - 4.3 admits glue and sagemaker only.",
                    )
            else:
                checks.ok(
                    "DT-4",
                    f"trust on {STAGING_JOB_ROLE}",
                    "glue + sagemaker service principals only",
                )
            if staging_lake_hits:
                for pname, arn in sorted(set(staging_lake_hits)):
                    checks.fail(
                        "DT-4",
                        f"D13 on {STAGING_JOB_ROLE}",
                        f"inline {pname} allows s3 on {arn} - Staging reads the lake through Lake Formation alone.",
                    )
            else:
                checks.ok(
                    "DT-4",
                    f"D13 on {STAGING_JOB_ROLE}",
                    "no inline s3 allow reaches a lake bucket, the drop-box included",
                )

    # DT-5: the LF settings discipline, three accounts (DL-5's twin). A DataLakeSettings apply that
    # omits `parameters` empties them, which reads as SET_CONTEXT gone. The grantor and Production,
    # the share's two ends, read CROSS_ACCOUNT_VERSION 4 (Production's own reading, 2026-10-22, the
    # value 1.5 copies); Staging reads 1, takes no share, and is held to SET_CONTEXT alone.
    for p, param_txt, defaults_txt, admin_txt in lf_rows:
        if param_txt == "(read failed)":
            continue
        params = lf_params.get(p, {})
        version = str(params.get("CROSS_ACCOUNT_VERSION", ""))
        set_context = str(params.get("SET_CONTEXT", "")).upper() == "TRUE"
        version_held = p == STAGING_PROFILE or (version.isdigit() and int(version) >= 4)
        if set_context and version_held:
            checks.ok("DT-5", f"{p} parameters", param_txt)
        else:
            checks.fail(
                "DT-5",
                f"{p} parameters",
                f"{param_txt} - the INT-11 values regressed; stop and re-read Stage 5a step 5.4.",
            )
        if p == DATA_PROFILE:
            continue
        if defaults_txt == "db:0 tbl:0":
            checks.ok("DT-5", f"{p} create-defaults", "emptied (step 1.3/4.1's kill)")
        elif lf_seated.get(p):
            checks.fail(
                "DT-5",
                f"{p} create-defaults",
                f"{defaults_txt} with an administrator seated - IAMAllowedPrincipals defaults still "
                "granting, so the regrants restrict nothing (1.3's two-step).",
            )
        else:
            checks.note(
                "DT-5", f"{p} create-defaults", f"{defaults_txt} - expected before 1.5/4.5."
            )

    # DT-6: the write share arrived and nothing is pending (INT-03, INT-11's tax).
    if data_live and prod_account:
        if write_share_seen:
            checks.ok("DT-6", "the write share", "an INSERT grant names the Production account")
        elif not share_listed:
            checks.note(
                "DT-6",
                "the write share",
                "no INSERT grant to Production in what was read - the grantor's listing was not "
                "read to its last page (section 13).",
            )
        elif lf_seated.get(PROD_PROFILE):
            checks.fail(
                "DT-6",
                "the write share",
                "no INSERT grant to Production in the grantor's listing, with Production's "
                "administrator seated - pass 3 ran before 2.1's grant landed.",
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
            (checks.fail if job_role_state == "present" else checks.note)(
                "DT-7",
                f"drop-box policy ({dropbox_bucket})",
                dropbox_stmt + " - the Stage 5a statement and the 3.1 contract disagree.",
            )
        elif dropbox_stmt.startswith("names"):
            checks.ok("DT-7", f"drop-box policy ({dropbox_bucket})", dropbox_stmt)
        if dropbox_key_names_role == "NO":
            (checks.fail if job_role_state == "present" else checks.note)(
                "DT-7",
                "drop-box KMS grant",
                f"neither key policy nor grants name {JOB_ROLE} - the pickup dies as an S3 error (2.5).",
            )
        elif dropbox_key_names_role == "yes":
            checks.ok("DT-7", "drop-box KMS grant", f"the key names {JOB_ROLE}")

    # DT-8: Staging reads the lake through its share and writes none of it (decision 3): every grant
    # to its account is DESCRIBE or SELECT, its links resolve into Data Governance once staging/data/
    # stands, and no local table carries a lake table's name.
    if staging_live:
        if data_live and share_listed:
            if staging_write_grants:
                for where, beyond in staging_write_grants:
                    checks.fail(
                        "DT-8",
                        f"staging grant {where}",
                        f"carries {beyond} - Staging reads the lake and writes none of it (decision 3).",
                    )
            elif staging_share_rows:
                checks.ok(
                    "DT-8",
                    "staging share",
                    f"{len(staging_share_rows)} grant(s) to Staging, DESCRIBE and SELECT alone",
                )
            else:
                (checks.fail if staging_data_built else checks.note)(
                    "DT-8",
                    "staging share",
                    "no grant to Staging while staging/data/ stands - pass 2 precedes pass 5."
                    if staging_data_built
                    else "no grant to Staging yet - expected before pass 2's apply.",
                )
        if staging_links_to_data:
            checks.ok(
                "DT-8",
                "staging links",
                "resolve into Data Governance: "
                + ", ".join(sorted(t for _db, t in staging_links_to_data)),
            )
        else:
            (checks.fail if staging_data_built else checks.note)(
                "DT-8",
                "staging links",
                "none while staging/data/ stands - the read share is consumed through them (4.1)."
                if staging_data_built
                else "none yet - expected before step 4.5.",
            )
        if staging_copies:
            for db, t in staging_copies:
                checks.fail(
                    "DT-8",
                    f"staging table {db}.{t}",
                    "carries a lake table's name - Staging holds no copy (decision 3).",
                )
        else:
            checks.ok("DT-8", "staging copies", "no local table carries a lake table's name")

    # DT-9: the escape hatch - windowed trust, closed at rest, 1 h sessions, alarmed.
    if prod_live:
        if debug_state == "(absent)":
            (checks.fail if runtime_built else checks.note)(
                "DT-9",
                f"role {DEBUG_ROLE}",
                "absent while production/sagemaker/'s other objects stand - a partial 3.4."
                if runtime_built
                else "absent - expected before step 3.4.",
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
            if debug_trust_ok and not debug_region_pinned:
                checks.fail(
                    "DT-9",
                    f"trust on {DEBUG_ROLE}",
                    f"the window does not pin aws:RequestedRegion to {context.REGION}: an "
                    "assumption through the global STS endpoint is logged in us-east-1, where no "
                    "rule watches (6.1).",
                )
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
                    if state == ALARM_RULE_STATE:
                        checks.ok("DT-9", f"rule {rname}", state)
                    elif state == "ENABLED":
                        checks.fail(
                            "DT-9",
                            f"rule {rname}",
                            "state ENABLED - it receives no AssumeRole, which EventBridge classes "
                            f"as a read-only management event; {ALARM_RULE_STATE} does.",
                        )
                    else:
                        checks.fail("DT-9", f"rule {rname}", f"state {state} - not watching.")

    # DT-10: the persona halves, read through the delegated administrator (step 5).
    for set_name, finding, verdict in set_rows:
        if verdict == "ok":
            checks.ok("DT-10", set_name, finding)
        elif verdict == "owed":
            checks.note("DT-10", set_name, finding + " - owed by step 5.1, pass 4.")
        elif verdict == "partial":
            checks.fail(
                "DT-10",
                set_name,
                finding + " - a partial 5.3: step 5.1's statements are one apply.",
            )
        else:
            checks.fail("DT-10", set_name, finding + ".")

    # DT-11: the job settings bind whoever calls Create*Job in Staging and Production (step 3.5,
    # decision 9 shape (a), verification xv), and serverless inference is refused there (3.7).
    if identity_live:
        missing = [sid for sid in JOB_DENY_SIDS if sid not in workloads_sids]
        if not workloads_attached:
            checks.fail(
                "DT-11",
                f"{WORKLOADS_DOC} on {WORKLOADS_OU}",
                "not attached - the OU documents are 1c's and never come off.",
            )
        elif missing:
            (checks.fail if runtime_built else checks.note)(
                "DT-11",
                f"{WORKLOADS_DOC} on {WORKLOADS_OU}",
                f"missing {', '.join(missing)} - "
                + (
                    "apply step 3.5 (battery first)."
                    if runtime_built
                    else "expected before 3.5's apply."
                ),
            )
        else:
            checks.ok(
                "DT-11",
                f"{WORKLOADS_DOC} on {WORKLOADS_OU}",
                f"attached, the {len(JOB_DENY_SIDS)} job Sids present",
            )

    # DT-12: the job log groups, declared with a retention by the slice that holds the account's
    # job role (3.1, 4.3, EXC-10), each under the account data key once data/ stands. Before that
    # slice, a group a job created is the import 4.3 owes.
    for p, role_state in ((PROD_PROFILE, job_role_state), (STAGING_PROFILE, staging_job_state)):
        rows = [(g, days, key) for q, g, days, key in log_rows if q == p]
        if not rows:
            continue
        if role_state == "present":
            bad = [f"{g} {days}" for g, days, _key in rows if days in ("(absent)", "(none)")]
            if bad:
                checks.fail(
                    "DT-12",
                    f"{p} job log groups",
                    f"{', '.join(bad)} - the job role's slice declares each with a retention.",
                )
            else:
                checks.ok(
                    "DT-12",
                    f"{p} job log groups",
                    f"{len(rows)} declared, retention {', '.join(sorted({d for _g, d, _k in rows}))}",
                )
            # The key, once the account data key exists. Another key, or the data key on some groups
            # only, fails. The AWS-owned key on all of them is the association written on 2026-10-22
            # and not yet applied (3.1, 4.3), a note.
            data_key = data_key_arns.get(p)
            standing = [(g, key) for g, days, key in rows if days != "(absent)"]
            if data_key and standing:
                other = [g for g, key in standing if key not in ("(AWS-owned)", data_key)]
                keyed = [g for g, key in standing if key == data_key]
                unkeyed = [g for g, key in standing if key == "(AWS-owned)"]
                if other:
                    checks.fail(
                        "DT-12",
                        f"{p} job log groups' key",
                        f"{', '.join(other)} under a key other than the account data key.",
                    )
                elif keyed and unkeyed:
                    checks.fail(
                        "DT-12",
                        f"{p} job log groups' key",
                        f"{', '.join(unkeyed)} under the AWS-owned key while {len(keyed)} carry the "
                        "account data key - a partial apply.",
                    )
                elif keyed:
                    checks.ok(
                        "DT-12",
                        f"{p} job log groups' key",
                        f"{len(keyed)} under the account data key",
                    )
                else:
                    checks.note(
                        "DT-12",
                        f"{p} job log groups' key",
                        "the AWS-owned key on all of them - the association with the account data "
                        "key is written (2026-10-22), not applied (3.1, 4.3).",
                    )
        else:
            early = [f"{g} {days}" for g, days, _key in rows if days != "(absent)"]
            if early:
                checks.note(
                    "DT-12",
                    f"{p} job log groups",
                    f"{', '.join(early)} before the job role's slice - 4.3 imports each group "
                    "a job created first.",
                )

    # ---------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner(
            "DEPLOY TARGETS - the Stage 9 evidence: producer path, registry, the read shares"
        )
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/deploytargets.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The Production data platform: buckets, CMK, the enforced workgroup
  3. The runtime: the job roles (D13), their log groups and the Model Registry (D28)
  4. The Lake Formation settings, every account that has any (DT-5)
  5. The write share, the links, the invitations (INT-03)
  6. The drop-box contract, both sides (INT-10)
  7. Staging's read of the lake, through its share (decision 3)
  8. The escape hatch: role, alarm, assumptions (step 6)
  9. The persona sets' owed allows (step 5)
 10. The job settings on the Workloads OU (step 3.5)
 11. CHECKS
 12. The accounts nothing here is measuring
 13. Calls that failed

HOW TO READ THIS FILE
  - An object absent before the pass that creates it is a note, and the same absence
    after that pass is a failure: each check reads its pass from the pass's own
    objects (Lesson 50), so a stage applied pass by pass reads clean at every pass.
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
The branches are PRESENCE, never sufficiency (vpce/ip/via - Stage 5a step 1.3's
shape). One enforced result location, not one per principal: within-persona
visibility of query output is the stage's stated limit (risk 6), and the CMK is
what keeps it from the approvers and from Staging (D31).""")

        # ==============================================================================
        rep.h1("3. The runtime: the job roles (D13), their log groups and the Model Registry (D28)")
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
        if log_rows:
            rep.line()
            rep.tabulate(
                ["PROFILE\tJOB LOG GROUP\tRETENTION\tKEY"]
                + ["\t".join((q, g, days, key.rsplit(":", 1)[-1])) for q, g, days, key in log_rows]
            )
        if prod_live:
            rep.text("""
D13 read from the role's own policies: the governed write must arrive only
through lakeformation:GetDataAccess vending, so an inline s3 allow naming a lake
bucket is the finding, and the drop-box statements are the named exception. The
Staging principals join the group policies at step 4.6. A service creates its
job log group with no retention when a job runs before the slice that declares
it, so DT-12 reads the six in every account with a job role, and the key each
carries: the account data key once data/ stands.""")

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
        elif data_live and share_listed:
            rep.line("No grantor-side permission names the Production account yet (pre-2.2).")
        elif data_live:
            rep.line("The grantor's listing was not read to its last page - section 13.")
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
                "No bucket matching *dropbox* in Data Governance (Stage 5a decision 3 creates it)."
            )
        else:
            rep.line(f"bucket {dropbox_bucket}: {dropbox_stmt}")
            rep.line(f"drop-box key names {JOB_ROLE}: {dropbox_key_names_role}")
            rep.text("""
Stage 5a wrote both against this stage's role name before the role existed - the
contract this section watches. A NO on either line is the pickup failing later
with an error that names S3 and means KMS or a typo (2.5, D25).""")

        # ==============================================================================
        rep.h1("7. Staging's read of the lake, through its share (decision 3)")
        if not staging_live:
            rep.line(
                f"{STAGING_PROFILE} did not answer - the whole section waits for a session on it."
            )
        else:
            if staging_share_rows:
                rep.tabulate(
                    ["GRANT TO STAGING\tPERMISSIONS"] + ["\t".join(r) for r in staging_share_rows]
                )
            else:
                rep.line("No grant of the lake names Staging's account (pass 2 grants its read).")
            rep.line()
            if staging_links_to_data:
                rep.tabulate(
                    ["LINK\tRESOLVES INTO"] + ["\t".join(r) for r in staging_links_to_data]
                )
            else:
                rep.line("No Staging resource link reaches Data Governance (4.1 creates them).")
            rep.line(f"local databases: {', '.join(staging_local_dbs) or '(none)'}")
            if staging_wg_row is not None:
                enforce, location, cutoff = staging_wg_row
                rep.line(
                    f"workgroup {STAGING_WG}: enforce={enforce} location={location} cutoff={cutoff}"
                )
            rep.line(f"role {STAGING_JOB_ROLE}: {staging_job_state}")
            if staging_lake_hits:
                rep.tabulate(
                    ["INLINE POLICY\tLAKE-BUCKET RESOURCE"]
                    + ["\t".join(r) for r in sorted(set(staging_lake_hits))]
                )
            rep.line(f"{STAGING_CMK_ALIAS}: {'present' if staging_cmk_present else '(absent)'}")
            rep.text("""
Staging reads the governed lake through the share Sandbox holds and writes none of it
(decision 3, amending D20): a grant beyond DESCRIBE and SELECT is the finding, and so is a
local table carrying a lake table's name, since each deploy creates the application's own
tables and a governed table is read through the links. The workgroup serves the integration
tests and the application; DataScientistStagingAccess holds no Athena (Stage 2).""")

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
            elif not debug_arn:
                rep.line("The AssumeRole history was not read: it is looked up by the role's ARN.")
            elif not debug_read:
                rep.line("The AssumeRole history was not read: the lookup failed (section 13).")
            else:
                rep.line("No AssumeRole event names the debug role in the last 90 days.")
            rep.text("""
Closed at rest is the design: the DateLessThan default sits in the past, an
approval is a recorded apply, and EVERY assumption alarms (not just misuse).
The read-only-by-API shape is imposed by the Workloads OU SCP - a session
under this role cannot become a notebook (6.3 proves it once). The events read
are API AssumeRole calls that succeeded: a refused one records no roleArn
(6.2), and a console switch records a sign-in SwitchRole event, which the
second rule watches and 6.3 locates.""")

        # ==============================================================================
        rep.h1("9. The persona sets' owed allows (step 5)")
        if set_rows:
            rep.tabulate(["PERMISSION SET\tFINDING"] + ["\t".join(r[:2]) for r in set_rows])
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
        rep.h1("10. The job settings on the Workloads OU (step 3.5)")
        if not identity_live:
            rep.line(f"{IDENTITY_PROFILE} was not measured - nothing to show.")
        else:
            rep.line(
                f"{WORKLOADS_DOC} on {WORKLOADS_OU}: "
                f"{'attached' if workloads_attached else '(not attached)'}"
            )
            rep.tabulate(
                ["SID\tPRESENT"]
                + [f"{sid}\t{'yes' if sid in workloads_sids else 'NO'}" for sid in JOB_DENY_SIDS]
            )
            rep.text("""
The five job settings bind the caller of Create*Job, never the role the job runs
as (Lesson 66), so they sit on the OU, where they reach Stage 10's execution
roles, the deploy roles and any role a pipeline creates. Presence by Sid only:
identity/org-policies compares the document with sagemaker-denies on every plan,
and the SCP battery's Stage 9 rows measure each deny (scp-battery.md).""")

        # ==============================================================================
        rep.h1("11. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  DT-1   the two buckets: versioned, SSE-KMS, perimeter branches (vpce, via, prin; never
         ip, D39), results expiry (1.1)
  DT-2   the workgroup enforces location + scan limit (1.2, D19)
  DT-3   every awsds-prod-model-* group carries a resource policy (3.2, D28 item 6)
  DT-4   the job roles: service-only trust, no s3 allow on lake buckets - Production's
         drop-box excepted (3.1, D13), Staging's with no exception (4.3, D13)
  DT-5   the LF settings discipline in all three accounts: parameters carried, create
         defaults emptied once an administrator is seated (1.3/2.2/4.1, DL-5's twin)
  DT-6   the write share granted, no pending invitation (2.1-2.2, INT-03/INT-11)
  DT-7   the drop-box statement and key both name awsds-prod-job-exec (2.5, INT-10)
  DT-8   Staging's grants on the lake are DESCRIBE or SELECT, its links resolve into Data
         Governance once staging/data/ stands, and no local table copies a lake table (4.1,
         decision 3)
  DT-9   the escape hatch: windowed trust pinned to the Region, closed at rest, <=1h,
         alarmed by rules that receive AssumeRole (6.1-6.2)
  DT-10  the persona halves read back through the delegated admin (5.1-5.2)
  DT-11  the Workloads OU document attached, with the five job settings and the
         serverless-inference deny (3.5-3.7, decision 9, verification xv)
  DT-12  the six job log groups declared with a retention wherever the job role stands,
         each under the account data key once data/ stands, and a group a job created
         before the slice named for import (3.1, 4.3, EXC-10)""")

        # ==============================================================================
        rep.h1("12. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 11 as a pass.

  - `Staging` has a profile since 2026-09-06: Stage 6b made the account by
    renaming `Development`, so sections 5 and 7, DT-8 and INT-07's registry
    half (4.6) report a real reading, not an absence.
  - `Development` is gone as an account name. Where this report still says it,
    read `Staging`: same account, renamed 2026-09-06. INT-04 was retired into
    INT-07 at the 2026-09-05 re-scope.
  - Log Archive and Audit hold no profile by design; nothing in this stage
    lives there.""")

        # ==============================================================================
        rep.h1("13. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/deploytargets.py")

    # ------------------------------------------------------------------------------ run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 13)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 11)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
