#!/usr/bin/env -S uv run --quiet
# datalake.py - Stage 5's evidence, per account, side by side: the lake buckets and their
# perimeter policies, the KMS aliases, the Glue catalog (databases, resource links,
# crawlers), the catalog-maintenance role and its trust, the Lake Formation settings WITH
# THE PARAMETERS READING THAT DEFENDS INT-11, the RAM shares and any pending invitation,
# the consumer Athena workgroups, the derived zone, the EFS reading (absence expected,
# save the home filesystem a Studio domain creates for itself - the NFS requirement was
# withdrawn 2026-08-17), and the Security Hub state. The preflight for Stage 5, and the standing regression after it.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/datalake.py                     # every awsds-* profile
#             ./aws/datalake.py awsds-infra-data    # only the ones named
#             python3 aws/datalake.py -             # CloudShell, ambient credentials
#   writes:   aws/output/datalake.txt   (untracked - see .gitignore)
#   reads:    s3api:ListBuckets, GetBucketVersioning, GetBucketEncryption,
#             GetPublicAccessBlock, GetBucketPolicy, GetBucketLifecycleConfiguration,
#             kms:ListAliases, glue:GetDatabases, GetCrawlers, iam:GetRole,
#             lakeformation:GetDataLakeSettings, ListResources, ListLFTags,
#             ram:GetResourceShares, GetResourceShareInvitations,
#             athena:ListWorkGroups, GetWorkGroup, efs:DescribeFileSystems,
#             securityhub:DescribeHub, GetEnabledStandards,
#             organizations:ListDelegatedAdministrators, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The whole subject
# is a CROSS-ACCOUNT shape (D22): the lake and its policy live in Data Governance while
# every legitimate reader sits in a consumer account, a share has a grantor side and a
# resource-link side on opposite sides of the boundary, and a pending RAM invitation is
# only visible from the consumer. A single-profile version would answer nothing. Section 1
# pays the rule back with the caller ARN of every profile.
#
# THE ONE CHECK TO KNOW BY NAME: DL-5. The account's DataLakeSettings carry
# CROSS_ACCOUNT_VERSION=4 / SET_CONTEXT=TRUE - values nobody set and nobody else defends -
# and the Stage 5 apply that declares admins RESETS them if it omits `parameters`
# (1d step 11.2, INT-11). The failure is total and mute: every later grant appears to
# succeed and no share ever arrives. This file turns that into a reading that fails.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the pandas pair, the workgroup boundary, the crawler run
#     as the maintenance role, the drop-box asymmetry - are the stage's own (Lesson 20).
#   - Bucket-policy readings are PRESENCE, never sufficiency: whether the aws:SourceVpce
#     list names the right gateway endpoints is proven by reads that succeed and fail
#     where they should, not by a grep.
#   - Security Hub's org configuration lives in Audit (no profile); only each member's
#     subscription state is read here.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "datalake.txt"

DATA_PROFILE = "awsds-infra-data"
IDENTITY_PROFILE = "awsds-infra-identity"
# The consumer side is PER BUSINESS UNIT (D35): unit 1's Sandbox plus Development today;
# Production joins at Stage 9. Add each vended unit's profile here as Stage 14 vends it.
CONSUMER_PROFILES = ("awsds-infra-sandbox-1", "awsds-infra-dev")

# Contracts named in the stage file, so a rename fails loudly rather than silently.
MAINT_ROLE = "awsds-data-catalog-maintenance"  # Stage 5 step 3.2, the SCP contract
LAKE_PREFIX = "awsds-data-"  # conventions: awsds-data-raw, -curated, -artifacts, -logs
# The tag a SageMaker AI domain stamps on the home EFS it creates for itself and retains
# past deletion (conventions 5.1 rule 2) - DL-10's one exemption from "none is the design".
SM_DOMAIN_TAG = "ManagedByAmazonSageMakerResource"
FSBP = "aws-foundational-security-best-practices"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    def run_json(cli: AwsCli, profile: str, *args: str, tolerate: str | None = None):
        res = cli.run(*args, "--output", "json", log=False, tolerate=tolerate)
        if res.tolerated:
            return None
        if not res.ok:
            logerr(profile, " ".join(args[:3]), res.stderr)
            return None
        return json.loads(res.stdout or "{}")

    data_live = DATA_PROFILE in live

    # ----------------------------------------------------- the lake buckets, Data Governance
    buckets: list = []  # (name, versioning, sse, bucketkey, policy summary, lifecycle)
    if data_live:
        cli = cli_for(DATA_PROFILE)
        note(f"measuring {DATA_PROFILE} ...")
        res = cli.run(
            "s3api", "list-buckets", "--query", "Buckets[].Name", "--output", "text", log=False
        )
        names = res.stdout.split() if res.ok else []
        if not res.ok:
            logerr(DATA_PROFILE, "s3api list-buckets", res.stderr)
        for b in sorted(names):
            if not b.startswith(LAKE_PREFIX) or b.endswith("-tfstate"):
                continue
            r = cli.run(
                "s3api",
                "get-bucket-versioning",
                "--bucket",
                b,
                "--query",
                "Status",
                "--output",
                "text",
                log=False,
            )
            versioning = r.stdout.strip() if r.ok else "(failed)"
            enc = run_json(cli, DATA_PROFILE, "s3api", "get-bucket-encryption", "--bucket", b)
            sse, bkey = "-", "-"
            if enc:
                rules = enc.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
                if rules:
                    d = rules[0].get("ApplyServerSideEncryptionByDefault", {})
                    sse = d.get("SSEAlgorithm", "-")
                    bkey = str(rules[0].get("BucketKeyEnabled", "-"))
            r = cli.run(
                "s3api",
                "get-bucket-policy",
                "--bucket",
                b,
                "--query",
                "Policy",
                "--output",
                "text",
                log=False,
                tolerate="NoSuchBucketPolicy",
            )
            pol = r.stdout if r.ok else ""
            summary = []
            for token, tag in (
                ("aws:SourceVpce", "vpce"),
                ("aws:SourceIp", "ip"),
                ("aws:ViaAWSService", "via"),
                ("s3:signatureAge", "sigage"),
                ("aws:PrincipalArn", "prin"),
                ("aws:PrincipalAccount", "prin"),
            ):
                if token in pol:
                    summary.append(tag)
            policy = "+".join(sorted(set(summary))) if summary else ("none" if not pol else "other")
            r = cli.run(
                "s3api",
                "get-bucket-lifecycle-configuration",
                "--bucket",
                b,
                "--query",
                "Rules[].ID",
                "--output",
                "text",
                log=False,
                tolerate="NoSuchLifecycleConfiguration",
            )
            lifecycle = "yes" if (r.ok and r.stdout.strip()) else "no"
            buckets.append((b, versioning, sse, bkey, policy, lifecycle))

    # --------------------------------------------------------------- KMS aliases, per account
    aliases: list = []  # (profile, alias)
    for p in live:
        cli = cli_for(p)
        res = cli.run(
            "kms",
            "list-aliases",
            "--query",
            "Aliases[].AliasName",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "kms list-aliases", res.stderr)
            continue
        for a in res.stdout.split():
            if a.startswith("alias/awsds-"):
                aliases.append((p, a))

    # ------------------------------------------------ the Glue catalog: databases and crawlers
    databases: list = []  # (profile, name, link target or '-')
    crawlers: list = []  # (name, role, schedule, s3 targets, catalog targets)
    for p in live:
        if p != DATA_PROFILE and p not in CONSUMER_PROFILES:
            continue
        cli = cli_for(p)
        doc = run_json(cli, p, "glue", "get-databases")
        if doc:
            for d in doc.get("DatabaseList", []):
                tgt = d.get("TargetDatabase", {})
                link = f"{tgt.get('CatalogId', '?')}:{tgt.get('DatabaseName', '?')}" if tgt else "-"
                databases.append((p, d.get("Name", "?"), link))
    if data_live:
        cli = cli_for(DATA_PROFILE)
        doc = run_json(cli, DATA_PROFILE, "glue", "get-crawlers")
        if doc:
            for c in doc.get("Crawlers", []):
                targets = c.get("Targets", {})
                s3t = ";".join(t.get("Path", "?") for t in targets.get("S3Targets", [])) or "-"
                catt = (
                    ";".join(
                        ",".join(t.get("Tables", ["?"])) for t in targets.get("CatalogTargets", [])
                    )
                    or "-"
                )
                crawlers.append(
                    (
                        c.get("Name", "?"),
                        (c.get("Role", "?") or "?").split("/")[-1],
                        "yes" if c.get("Schedule") else "-",
                        s3t,
                        catt,
                    )
                )

    # ------------------------------------------------------------- the maintenance role (D27)
    maint_role_state = "(not read)"
    maint_trust = ""
    if data_live:
        cli = cli_for(DATA_PROFILE)
        doc = run_json(
            cli,
            DATA_PROFILE,
            "iam",
            "get-role",
            "--role-name",
            MAINT_ROLE,
            tolerate="NoSuchEntity",
        )
        if doc is None:
            maint_role_state = "absent"
        else:
            maint_role_state = "present"
            pol = doc.get("Role", {}).get("AssumeRolePolicyDocument", {})
            principals = []
            for st in pol.get("Statement", []):
                pr = st.get("Principal", {})
                svc = pr.get("Service", [])
                principals += [svc] if isinstance(svc, str) else list(svc)
                if pr.get("AWS"):
                    principals.append("AWS-principal!")
            maint_trust = " ".join(sorted(set(principals))) or "(empty)"

    # ------------------------------------- Lake Formation: settings, registrations, LF-Tags
    lf_params: dict = {}
    lf_admins: list = []
    lf_db_defaults = lf_tbl_defaults = "-"
    lf_registered: list = []
    lf_tags: list = []
    lf_read = False
    if data_live:
        cli = cli_for(DATA_PROFILE)
        doc = run_json(cli, DATA_PROFILE, "lakeformation", "get-data-lake-settings")
        if doc is not None:
            lf_read = True
            s = doc.get("DataLakeSettings", {})
            lf_params = s.get("Parameters", {}) or {}
            lf_admins = [
                a.get("DataLakePrincipalIdentifier", "?") for a in s.get("DataLakeAdmins", [])
            ]
            lf_db_defaults = json.dumps(s.get("CreateDatabaseDefaultPermissions", []))
            lf_tbl_defaults = json.dumps(s.get("CreateTableDefaultPermissions", []))
        doc = run_json(cli, DATA_PROFILE, "lakeformation", "list-resources")
        if doc:
            lf_registered = [r.get("ResourceArn", "?") for r in doc.get("ResourceInfoList", [])]
        doc = run_json(
            cli,
            DATA_PROFILE,
            "lakeformation",
            "list-lf-tags",
            tolerate="AccessDenied|EntityNotFound",
        )
        if doc:
            lf_tags = [
                f"{t.get('TagKey', '?')}={','.join(t.get('TagValues', []))}"
                for t in doc.get("LFTags", [])
            ]

    # --------------------------------------------------- RAM: shares out, invitations pending
    shares: list = []  # (name, status)
    invitations: list = []  # (profile, share name, status)
    if data_live:
        cli = cli_for(DATA_PROFILE)
        doc = run_json(cli, DATA_PROFILE, "ram", "get-resource-shares", "--resource-owner", "SELF")
        if doc:
            shares = [
                (s.get("name", "?"), s.get("status", "?")) for s in doc.get("resourceShares", [])
            ]
    # THE CONSUMER-SIDE RECEIPT, added 2026-08-19 (Stage 5 pass 3) because DL-7 could not tell
    # its two failure branches apart. "Shares exist and no resource link" was reported as one
    # verdict whether step 8 had simply not run yet or the share had silently never arrived -
    # opposite causes, one message, which is Lesson 13's family. The discriminator is here: a
    # share the consumer's own RAM ACTUALLY HOLDS. Measured at pass 3, both consumers held
    # their two shares ACTIVE while their catalogs were still empty, so the empty catalog is
    # NOT evidence of a failed share.
    received: list = []  # (profile, share name, status)
    lf_admin_counts: dict = {}  # profile -> number of data lake admins in that account
    lf_consumer_settings: dict = {}  # profile -> {params, db_defaults, tbl_defaults}
    for p in CONSUMER_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        doc = run_json(cli, p, "ram", "get-resource-share-invitations")
        if doc:
            for inv in doc.get("resourceShareInvitations", []):
                invitations.append((p, inv.get("resourceShareName", "?"), inv.get("status", "?")))
        doc = run_json(cli, p, "ram", "get-resource-shares", "--resource-owner", "OTHER-ACCOUNTS")
        if doc:
            for s in doc.get("resourceShares", []):
                received.append((p, s.get("name", "?"), s.get("status", "?")))
        # WHY THE ADMIN COUNT RIDES ALONG: it is the CAUSE of the empty catalog above. AWS
        # requires at least one data lake administrator in a consumer account before a shared
        # resource is visible there at all, so zero admins explains the emptiness completely
        # and step 8 owes that account a DataLakeSettings of its own.
        doc = run_json(cli, p, "lakeformation", "get-data-lake-settings")
        if doc:
            cs = doc.get("DataLakeSettings", {})
            lf_admin_counts[p] = len(cs.get("DataLakeAdmins", []))
            # EXTENDED 2026-08-19 (Stage 5 pass 4). Until this pass only Data Governance had a
            # DataLakeSettings, so DL-5 and DL-6 read one account and said nothing about the
            # others. Both consumers were then measured carrying CROSS_ACCOUNT_VERSION=4 /
            # SET_CONTEXT=TRUE - values nobody in this repository set - and
            # IAM_ALLOWED_PRINCIPALS on BOTH create-defaults. So the two hazards are symmetric,
            # and the check that was scoped to the producer was reporting `pass` while two
            # accounts sat in exactly the state it exists to fail (Lesson 13's family).
            lf_consumer_settings[p] = {
                "params": cs.get("Parameters", {}) or {},
                "db_defaults": json.dumps(cs.get("CreateDatabaseDefaultPermissions", [])),
                "tbl_defaults": json.dumps(cs.get("CreateTableDefaultPermissions", [])),
            }

    # ----------------------------------------------------- Athena workgroups, consumer side
    workgroups: list = []  # (profile, name, enforce, output location, scan limit)
    for p in CONSUMER_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "athena",
            "list-work-groups",
            "--query",
            "WorkGroups[].Name",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "athena list-work-groups", res.stderr)
            continue
        for wg in res.stdout.split():
            if not wg.startswith("awsds-"):
                continue
            doc = run_json(cli, p, "athena", "get-work-group", "--work-group", wg)
            if not doc:
                continue
            conf = doc.get("WorkGroup", {}).get("Configuration", {})
            workgroups.append(
                (
                    p,
                    wg,
                    str(conf.get("EnforceWorkGroupConfiguration", "-")),
                    conf.get("ResultConfiguration", {}).get("OutputLocation", "-"),
                    str(conf.get("BytesScannedCutoffPerQuery", "-")),
                )
            )

    # ------------------------------------------------------------ derived zone, consumer side
    derived: list = []  # (profile, bucket, lifecycle expiry: yes/no)
    for p in CONSUMER_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "s3api", "list-buckets", "--query", "Buckets[].Name", "--output", "text", log=False
        )
        if not res.ok:
            logerr(p, "s3api list-buckets", res.stderr)
            continue
        for b in res.stdout.split():
            if "-derived" not in b:
                continue
            r = cli.run(
                "s3api",
                "get-bucket-lifecycle-configuration",
                "--bucket",
                b,
                "--output",
                "json",
                log=False,
                tolerate="NoSuchLifecycleConfiguration",
            )
            expiry = "no"
            if r.ok and r.stdout:
                rules = json.loads(r.stdout or "{}").get("Rules", [])
                if any("Expiration" in rule for rule in rules):
                    expiry = "yes"
            derived.append((p, b, expiry))

    # ------------------------------- the persona's IDENTITY half of the cross-account grants
    #
    # ADDED 2026-08-19 (pass 4c), and it exists because a review, a plan and a commit gate all
    # missed the thing it measures. The drop-box write crosses an account line, so it needs an
    # allow in the drop-box BUCKET POLICY (Data Governance, measured above as DL-2) *and* one
    # in the writer's own identity policy - and for a year of this plan only the first existed,
    # while the stage file asserted in writing that the absence was correct. Lesson 28, amended.
    #
    # IT READS THE PROVISIONED ROLE, NOT THE PERMISSION SET, and that is the whole point: a set
    # lives in the Identity account and becomes an IAM role in every account it reaches, so the
    # only place the permission actually IS is the role - which is also the object an
    # unprovisioned change would leave stale.
    persona_grants: list = []  # (profile, role, has dropbox put, has lake key via s3)
    for p in CONSUMER_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "iam",
            "list-roles",
            "--path-prefix",
            "/aws-reserved/sso.amazonaws.com/",
            "--query",
            "Roles[?contains(RoleName, `DataScientistAccess`)].RoleName",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "iam list-roles", res.stderr)
            continue
        for role in res.stdout.split():
            doc = run_json(
                cli,
                p,
                "iam",
                "get-role-policy",
                "--role-name",
                role,
                "--policy-name",
                "AwsSSOInlinePolicy",
            )
            if not doc:
                continue
            sids = {
                s.get("Sid", "")
                for s in doc.get("PolicyDocument", {}).get("Statement", [])
                if s.get("Effect") == "Allow"
            }
            persona_grants.append(
                (p, role, "WriteIngestionDropBox" in sids, "UseLakeZoneKeyViaS3" in sids)
            )

    # ------------------------------------------------------------------- EFS, the VPN home
    # The NFS requirement was withdrawn 2026-08-17 (D24 with it): no stage creates a
    # filesystem, so this reading is an absence check - with one exemption (2026-08-18).
    # A SageMaker AI domain creates a home EFS for itself and RETAINS it past deletion
    # (conventions 5.1 rule 2; Lesson 17 - a service that "sets itself up"), tagged with
    # the domain's ARN. From Stage 6 on that filesystem is the domain working as
    # documented; only an untagged one is drift.
    efs_rows: list = []  # (file system id, owning domain from SM_DOMAIN_TAG, or None)
    sbx_profile = CONSUMER_PROFILES[0]
    if sbx_profile in live:
        cli = cli_for(sbx_profile)
        doc = run_json(cli, sbx_profile, "efs", "describe-file-systems")
        for fs in (doc or {}).get("FileSystems", []):
            tags = {t.get("Key"): t.get("Value", "") for t in fs.get("Tags", [])}
            sm_arn = tags.get(SM_DOMAIN_TAG)
            # keep only the ARN's tail ("domain/d-..."): it names the owner and carries
            # no account id
            efs_rows.append(
                (fs.get("FileSystemId", "?"), sm_arn.split(":")[-1] if sm_arn else None)
            )

    # ------------------------------------------------------------- Security Hub, per account
    sh_rows: list = []  # (profile, hub, fsbp)
    for p in live:
        cli = cli_for(p)
        res = cli.run(
            "securityhub",
            "describe-hub",
            "--query",
            "HubArn",
            "--output",
            "text",
            log=False,
            tolerate="not subscribed|InvalidAccess|ResourceNotFound",
        )
        if res.tolerated:
            sh_rows.append((p, "not enabled", "-"))
            continue
        if not res.ok:
            logerr(p, "securityhub describe-hub", res.stderr)
            sh_rows.append((p, "(call failed)", "-"))
            continue
        std = cli.run(
            "securityhub",
            "get-enabled-standards",
            "--query",
            "StandardsSubscriptions[].StandardsArn",
            "--output",
            "text",
            log=False,
        )
        fsbp = "yes" if (std.ok and FSBP in std.stdout) else "no"
        sh_rows.append((p, "enabled", fsbp))
    sh_delegation = "(not read)"
    if IDENTITY_PROFILE in live:
        cli = cli_for(IDENTITY_PROFILE)
        res = cli.run(
            "organizations",
            "list-delegated-administrators",
            "--service-principal",
            "securityhub.amazonaws.com",
            "--query",
            "DelegatedAdministrators[].[Id,Name,Status]",
            "--output",
            "text",
            log=False,
            tolerate="AccessDenied",
        )
        if res.tolerated:
            sh_delegation = "(read denied from Identity - check from Management)"
        elif res.ok:
            sh_delegation = res.stdout.strip() or "(none registered)"

    # -------------------------------------------------------------------------------- checks
    # DL-1: the lake buckets and their baseline (step 1.2).
    if data_live and not buckets:
        checks.note(
            "DL-1",
            "lake buckets in Data Governance",
            f"none matching {LAKE_PREFIX}* - expected before Stage 5 pass 1.",
        )
    for b, versioning, sse, bkey, policy, _lc in buckets:
        problems = []
        if versioning != "Enabled":
            problems.append(f"versioning={versioning or 'off'}")
        if sse != "aws:kms":
            problems.append(f"sse={sse}")
        if bkey != "True":
            problems.append(f"bucketkey={bkey} (docs/plan/cost-model.md: KMS requests)")
        if problems:
            checks.fail("DL-1", f"baseline on {b}", "; ".join(problems) + " (step 1.2)")
        else:
            checks.ok("DL-1", f"baseline on {b}", "versioned, SSE-KMS, Bucket Key on")

    # DL-2: the perimeter policy's branches - presence, never sufficiency (step 1.3).
    for b, _v, _s, _k, policy, _lc in buckets:
        if policy == "none":
            checks.fail(
                "DL-2",
                f"bucket policy on {b}",
                "no policy - the trusted-networks half of the perimeter is missing "
                "(step 1.3, INT-05).",
            )
            continue
        missing = [tag for tag in ("vpce", "via", "sigage") if tag not in policy.split("+")]
        if missing:
            checks.fail(
                "DL-2",
                f"bucket policy on {b}",
                f"policy present but missing: {', '.join(missing)} - vpce is the network "
                "branch, via the Athena/LF carve-out (a bare deny makes step 6 unusable), "
                "sigage the presigned-URL cap (step 1.3).",
            )
        else:
            checks.ok("DL-2", f"bucket policy on {b}", f"carries {policy} (presence only)")

    # DL-3: crawler shape - never scheduled, never at an Iceberg/catalog target (step 3.6).
    if data_live and not crawlers and buckets:
        checks.note("DL-3", "crawlers", "none yet - expected before Stage 5 step 3.")
    for name, role, sched, _s3t, catt in crawlers:
        if sched == "yes":
            checks.fail(
                "DL-3",
                f"crawler {name}",
                "has a standing schedule - D27 says event-driven or on-demand only; "
                "cron-always out-costs the storage it catalogs, and a scheduled run "
                "lands on the service-guard side nobody probed (step 3.6).",
            )
        elif catt != "-":
            checks.fail(
                "DL-3",
                f"crawler {name}",
                f"points at catalog tables ({catt}) - no crawler ever points at an "
                "Iceberg table (D27, step 3.6).",
            )
        else:
            checks.ok("DL-3", f"crawler {name}", f"unscheduled, S3 targets only, role {role}")

    # DL-4: the maintenance role - the exact name is an SCP contract (step 3.2).
    if data_live:
        if maint_role_state == "absent":
            if crawlers:
                checks.fail(
                    "DL-4",
                    MAINT_ROLE,
                    "crawlers exist and the role does not - they can never run: the Data "
                    "OU SCP denies StartCrawler to every other principal (step 3.2).",
                )
            else:
                checks.note("DL-4", MAINT_ROLE, "absent - expected before Stage 5 step 3.")
        elif maint_role_state == "present":
            if maint_trust == "glue.amazonaws.com":
                checks.ok("DL-4", MAINT_ROLE, "present, trusts glue.amazonaws.com only")
            else:
                checks.fail(
                    "DL-4",
                    MAINT_ROLE,
                    f"trust policy names: {maint_trust} - the role must trust "
                    "glue.amazonaws.com and nothing else; an AWS principal in the trust "
                    "is a person holding the SCP exemption (D27, step 3.5).",
                )

    # DL-5: THE INT-11 DEFENCE - the parameters nobody set and Stage 5 can silently reset.
    if data_live and lf_read:
        ver = lf_params.get("CROSS_ACCOUNT_VERSION", "")
        setctx = lf_params.get("SET_CONTEXT", "")
        problems = []
        if not ver:
            problems.append("CROSS_ACCOUNT_VERSION ABSENT")
        elif ver not in ("3", "4"):
            problems.append(f"CROSS_ACCOUNT_VERSION={ver} (<3)")
        if setctx != "TRUE":
            problems.append(f"SET_CONTEXT={setctx or 'ABSENT'}")
        if problems:
            checks.fail(
                "DL-5",
                "DataLakeSettings.Parameters",
                "; ".join(problems) + " - measured 4/TRUE on 2026-08-14 (1d step 11.2); "
                "a regression here means an apply replaced the structure without carrying "
                "`parameters`, and every cross-account share now fails silently (INT-11, "
                "step 5.4). Fix the resource, re-apply, re-run this check.",
            )
        else:
            checks.ok(
                "DL-5",
                "DataLakeSettings.Parameters",
                f"CROSS_ACCOUNT_VERSION={ver}, SET_CONTEXT={setctx} - the 5.4 bracket holds",
            )

    # DL-5, THE CONSUMER HALF (added at pass 4). The reset is not the producer's peculiarity:
    # each consumer account carries its own Parameters map, this stage writes an
    # aws_lakeformation_data_lake_settings into both, and that resource replaces the whole
    # structure. Same failure, same silence, one account further from where anybody looks.
    for prof, cs in sorted(lf_consumer_settings.items()):
        ver = cs["params"].get("CROSS_ACCOUNT_VERSION", "")
        setctx = cs["params"].get("SET_CONTEXT", "")
        problems = []
        if not ver:
            problems.append("CROSS_ACCOUNT_VERSION ABSENT")
        elif ver not in ("3", "4"):
            problems.append(f"CROSS_ACCOUNT_VERSION={ver} (<3)")
        if setctx != "TRUE":
            problems.append(f"SET_CONTEXT={setctx or 'ABSENT'}")
        if problems:
            checks.fail(
                "DL-5",
                f"DataLakeSettings.Parameters ({prof})",
                "; ".join(problems) + " - measured 4/TRUE in BOTH consumers on 2026-08-19, "
                "before pass 4 wrote a settings resource there; a regression means that "
                "apply omitted `parameters` (INT-11, symmetric with 5.4).",
            )
        else:
            checks.ok(
                "DL-5",
                f"DataLakeSettings.Parameters ({prof})",
                f"CROSS_ACCOUNT_VERSION={ver}, SET_CONTEXT={setctx}",
            )

    # DL-6: the IAM-fallback defaults, once the catalog exists (step 5.2).
    dg_dbs = [d for d in databases if d[0] == DATA_PROFILE and d[2] == "-"]
    if data_live and lf_read and dg_dbs:
        if "IAM_ALLOWED_PRINCIPALS" in (lf_db_defaults + lf_tbl_defaults):
            checks.fail(
                "DL-6",
                "LF create-default permissions",
                "new databases/tables still default to IAMAllowedPrincipals - Lake "
                "Formation is then bookkeeping over plain IAM and D13 is decoration; "
                "empty both defaults and revoke the virtual group (step 5.2).",
            )
        else:
            checks.ok(
                "DL-6",
                "LF create-default permissions",
                "no IAMAllowedPrincipals default - grants are the model (step 5.2)",
            )

    # DL-6, THE CONSUMER HALF (added at pass 4, and it is the more dangerous one). The defaults
    # act at CREATION time and there is no second reading later: the first local catalog object
    # in a consumer account is the RESOURCE LINK, so a link created while they still stand is
    # born deferring to plain IAM and clearing them afterwards does not reach it. Reported per
    # account with no `databases exist` guard, deliberately - here the reading has to be
    # available BEFORE the first object, which is exactly when the guard would silence it.
    for prof, cs in sorted(lf_consumer_settings.items()):
        if "IAM_ALLOWED_PRINCIPALS" in (cs["db_defaults"] + cs["tbl_defaults"]):
            checks.fail(
                "DL-6",
                f"LF create-default permissions ({prof})",
                "new databases/tables in this account still default to IAMAllowedPrincipals. "
                "The first local object is the resource link of step 8 - create it now and it "
                "is born deferring to plain IAM, with nothing later able to repair it "
                "(Lesson 27, Recipe D). Clear the defaults, re-read THIS check, and only then "
                "apply the remainder of the slice.",
            )
        else:
            checks.ok(
                "DL-6",
                f"LF create-default permissions ({prof})",
                "no IAMAllowedPrincipals default - safe to create the resource links",
            )

    # DL-7: shares out, nothing pending on the consumer side, links resolved (step 7, 8).
    pending = [i for i in invitations if i[2] == "PENDING"]
    for p, name, _status in pending:
        checks.fail(
            "DL-7",
            f"pending RAM invitation in {p}",
            f"'{name}' awaits a manual accept - the org-sharing path is not doing the "
            "work (INT-11's fallback tax): it reappears at every rebuild. Check "
            "ram:EnableSharingWithAwsOrganization and the LF version before accepting "
            "by hand (step 7.3).",
        )
    links = [d for d in databases if d[0] in CONSUMER_PROFILES and d[2] != "-"]
    # THE TWO BRANCHES THAT USED TO SHARE ONE VERDICT (see the collection note above).
    consumers_seen = [p for p in CONSUMER_PROFILES if p in live]
    consumers_without = [p for p in consumers_seen if not any(r[0] == p for r in received)]
    if shares:
        if links and not pending:
            checks.ok(
                "DL-7",
                "shares and resource links",
                f"{len(shares)} share(s) out, {len(links)} resource link(s) on the "
                "consumer side, no pending invitation",
            )
        elif not links and consumers_without:
            checks.fail(
                "DL-7",
                "shares that never arrived",
                f"{len(shares)} share(s) exist here and "
                f"{', '.join(consumers_without)} hold NONE - this is the silent INT-11 "
                "failure, not a missing step 8: the grant succeeded and the resource did "
                "not travel. Read DL-5 first (a reset CROSS_ACCOUNT_VERSION does exactly "
                "this), then org sharing in RAM.",
            )
        elif not links:
            admins = ", ".join(f"{p}:{n}" for p, n in sorted(lf_admin_counts.items()))
            checks.note(
                "DL-7",
                "shares arrived, no resource link yet",
                f"{len(shares)} share(s) out and every consumer HOLDS its share - the "
                "share travelled. No resource link yet, which is step 8's, so this is the "
                f"expected state between passes 3 and 4. Data lake admins per consumer: "
                f"[{admins}] - at zero the consumer catalog is empty BY RULE, and step 8 "
                "owes that account a DataLakeSettings of its own.",
            )
    elif data_live and lf_registered:
        checks.note("DL-7", "cross-account shares", "none yet - expected before Stage 5 step 7.")

    # DL-8: the workgroup boundary (step 8, D19).
    if not workgroups and any(p in live for p in CONSUMER_PROFILES):
        checks.note(
            "DL-8",
            "consumer Athena workgroups",
            "no awsds-* workgroup - expected before Stage 5 step 8.",
        )
    for p, wg, enforce, out, limit in workgroups:
        problems = []
        if enforce != "True":
            problems.append(
                "EnforceWorkGroupConfiguration off - the result location is "
                "whatever the client asks for (D19)"
            )
        if out == "-":
            problems.append("no result location")
        if limit == "-":
            problems.append("no per-query scan limit")
        if problems:
            checks.fail("DL-8", f"workgroup {wg} ({p})", "; ".join(problems))
        else:
            checks.ok("DL-8", f"workgroup {wg} ({p})", f"enforced, limit {limit}, -> {out}")

    # DL-9: the derived zone's lifecycle expiry (step 9.2).
    for p, b, expiry in derived:
        if expiry == "yes":
            checks.ok("DL-9", f"derived-zone expiry on {b} ({p})", "lifecycle expiry present")
        else:
            checks.fail(
                "DL-9",
                f"derived-zone expiry on {b} ({p})",
                "no expiry rule - the shadow lake silently becomes permanent (D19, step 9.2).",
            )

    # DL-12: the identity half of the drop-box write (pass 4c; Lesson 28 amended). A
    # cross-account permission is the AND of two policies, and DL-2 only ever measured the
    # resource one. This is the other half, read off the provisioned role.
    if not persona_grants and any(p in live for p in CONSUMER_PROFILES):
        checks.note(
            "DL-12",
            "persona drop-box grants",
            "no DataScientistAccess role provisioned - expected before Stage 5 pass 4c.",
        )
    for p, role, has_put, has_key in persona_grants:
        missing = []
        if not has_put:
            missing.append("WriteIngestionDropBox (s3:PutObject on the dated prefix)")
        if not has_key:
            missing.append("UseLakeZoneKeyViaS3 (GenerateDataKey/Decrypt via S3)")
        if missing:
            checks.fail(
                "DL-12",
                f"drop-box identity half ({p})",
                "; ".join(missing)
                + " - the bucket policy alone denies the write, and the AccessDenied "
                "names the half that is right (Lesson 28, step 6.2's correction).",
            )
        else:
            checks.ok(
                "DL-12",
                f"drop-box identity half ({p})",
                "both statements present on the provisioned role",
            )

    # DL-10: no filesystem is the design - the NFS requirement was withdrawn 2026-08-17,
    # D24 with it. The one exemption: a Studio domain's own tagged home, reported by name
    # rather than failed. Anything untagged is drift, not progress.
    if sbx_profile in live:
        if not efs_rows:
            checks.ok(
                "DL-10", "EFS in the VPN home", "none - and none is the design (D24 withdrawn)."
            )
        for fsid, sm_owner in efs_rows:
            if sm_owner:
                checks.note(
                    "DL-10",
                    f"EFS {fsid}",
                    f"the home filesystem of SageMaker domain {sm_owner} - service-created "
                    "and retained by design (conventions 5.1 rule 2); expected from Stage 6.",
                )
            else:
                checks.fail(
                    "DL-10",
                    f"EFS {fsid}",
                    f"an EFS filesystem with no {SM_DOMAIN_TAG} tag - the plan creates "
                    "none since the NFS requirement was withdrawn (2026-08-17, D24 "
                    "withdrawn); drift, not progress.",
                )

    # DL-11: Security Hub coverage (step 13).
    enabled = [r for r in sh_rows if r[1] == "enabled"]
    if not enabled:
        checks.note(
            "DL-11",
            "Security Hub",
            "not enabled in any measured account - expected before Stage 5 step 13.",
        )
    else:
        for p, hub, fsbp in sh_rows:
            if hub == "not enabled":
                checks.fail(
                    "DL-11",
                    f"Security Hub in {p}",
                    "not enabled while other accounts are - auto-enable did not reach "
                    "this account (verification (ix)).",
                )
            elif hub == "enabled" and fsbp != "yes":
                checks.fail(
                    "DL-11",
                    f"FSBP standard in {p}",
                    "hub enabled without the Foundational Security Best Practices "
                    "standard - the checks are the point (step 13.1).",
                )
            elif hub == "enabled":
                checks.ok("DL-11", f"Security Hub in {p}", "enabled, FSBP on")

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Data foundation - the Stage 5 evidence, producer and consumers side by side")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/datalake.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The lake buckets (Data Governance)
  3. KMS aliases, per account
  4. Glue catalog - databases, resource links, crawlers
  5. The catalog-maintenance role (D27)
  6. Lake Formation - settings, PARAMETERS, registrations, LF-Tags
  7. RAM - shares out, invitations pending, shares HELD by each consumer
  8. Athena workgroups, consumer side
  9. The derived zone
  10. EFS (expected: none, or a Studio domain's own home)
  11. Security Hub
  12. CHECKS
  13. The accounts nothing here is measuring
  14. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 5 RUNS - a note, not a
    failure; it becomes a regression the moment the stage closes.
  - DL-5 IS THE CHECK TO READ FIRST after ANY apply in data-governance/data/: a
    reset CROSS_ACCOUNT_VERSION fails every share SILENTLY, days later (INT-11).
  - POLICY READINGS ARE PRESENCE, NEVER SUFFICIENCY (Lesson 20): the pandas pair,
    the workgroup boundary and the crawler run are the stage's behavioural proofs.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 13.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ==============================================================================
        rep.h1("1. Which accounts were measured, and as whom")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        # ==============================================================================
        rep.h1("2. The lake buckets (Data Governance)")
        if buckets:
            rep.tabulate(
                ["BUCKET\tVERSIONING\tSSE\tBUCKETKEY\tPOLICY BRANCHES\tLIFECYCLE"]
                + [f"{b}\t{v}\t{s}\t{k}\t{pol}\t{lc}" for b, v, s, k, pol, lc in buckets]
            )
            rep.text("""
POLICY BRANCHES greps the bucket policy for the step 1.3 conditions: vpce
(aws:SourceVpce), ip (the WireGuard EIP branch), prin (the maintenance-role
branch), via (aws:ViaAWSService), sigage (s3:signatureAge). Presence only.""")
        elif data_live:
            rep.line(f"No bucket matching {LAKE_PREFIX}*. Expected before Stage 5 pass 1.")
        else:
            rep.line(f"{DATA_PROFILE} was not measured - nothing to show.")

        # ==============================================================================
        rep.h1("3. KMS aliases, per account")
        if aliases:
            rep.tabulate(["PROFILE\tALIAS"] + [f"{p}\t{a}" for p, a in sorted(aliases)])
            rep.text("""
Expected once the stage closes: the domain keys in Data Governance (step 1.1,
decision 2), the drop-box key (decision 3), and one *-derived key per
Interactive account (step 9.2, D31) - the derived key SEPARATE from the account
key is the control, not a convention.""")
        else:
            rep.line("No awsds-* alias in any measured account.")

        # ==============================================================================
        rep.h1("4. Glue catalog - databases, resource links, crawlers")
        if databases:
            rep.tabulate(
                ["PROFILE\tDATABASE\tRESOURCE LINK ->"]
                + [f"{p}\t{n}\t{t}" for p, n, t in sorted(databases)]
            )
        else:
            rep.line("No database in any measured account.")
        rep.line()
        if crawlers:
            rep.tabulate(
                ["CRAWLER\tROLE\tSCHEDULED\tS3 TARGETS\tCATALOG TARGETS"]
                + [f"{n}\t{r}\t{s}\t{s3}\t{c}" for n, r, s, s3, c in crawlers]
            )
        else:
            rep.line("No crawler in Data Governance.")

        # ==============================================================================
        rep.h1("5. The catalog-maintenance role (D27)")
        rep.text(f"""ROLE={MAINT_ROLE}   state: {maint_role_state}   trust: {maint_trust or "-"}

The name is a contract with the Data OU SCP: under any other name the crawlers
never run (step 3.2). The positive half - the role CAN start a crawler - is the
stage's own probe (scp-battery phase 4), not this file's.""")

        # ==============================================================================
        rep.h1("6. Lake Formation - settings, PARAMETERS, registrations, LF-Tags")
        if lf_read:
            rep.line(f"Parameters       : {json.dumps(lf_params)}")
            rep.line(f"DataLakeAdmins   : {', '.join(lf_admins) or '(none)'}")
            rep.line(f"DB defaults      : {lf_db_defaults}")
            rep.line(f"Table defaults   : {lf_tbl_defaults}")
            rep.line()
            rep.line("Registered locations:")
            for arn in lf_registered or ["  (none)"]:
                rep.line(f"  {arn}")
            rep.line()
            rep.line(f"LF-Tags: {', '.join(lf_tags) or '(none)'}")
            rep.text("""
The Parameters line is the INT-11 reading (DL-5): 5.4 brackets every apply with
it. Admins present with Parameters absent is the reset having happened.""")
        else:
            rep.line("get-data-lake-settings was not read - see section 14.")

        # ==============================================================================
        rep.h1("7. RAM - shares out, invitations pending, shares HELD by each consumer")
        if shares:
            rep.tabulate(["SHARE\tSTATUS"] + [f"{n}\t{s}" for n, s in shares])
        else:
            rep.line("No resource share owned by Data Governance.")
        rep.line()
        if invitations:
            rep.tabulate(["PROFILE\tSHARE\tSTATUS"] + [f"{p}\t{n}\t{s}" for p, n, s in invitations])
            rep.line()
            rep.line("A PENDING row is the org-sharing path not working (INT-11, step 7.3).")
        else:
            rep.line("No invitation on any consumer - the expected state under org sharing.")
        rep.line()
        if received:
            rep.tabulate(
                ["PROFILE\tSHARE HELD\tSTATUS"] + [f"{p}\t{n}\t{s}" for p, n, s in received]
            )
        else:
            rep.line("No consumer holds a share from Data Governance.")
        rep.line()
        if lf_admin_counts:
            rep.tabulate(
                ["PROFILE\tDATA LAKE ADMINS\tPARAMETERS\tDB DEFAULTS\tTABLE DEFAULTS"]
                + [
                    "\t".join(
                        [
                            p,
                            str(n),
                            json.dumps(lf_consumer_settings.get(p, {}).get("params", {})),
                            lf_consumer_settings.get(p, {}).get("db_defaults", "-"),
                            lf_consumer_settings.get(p, {}).get("tbl_defaults", "-"),
                        ]
                    )
                    for p, n in sorted(lf_admin_counts.items())
                ]
            )
        rep.text("""
THE TWO TABLES ABOVE ARE READ TOGETHER, and they are what separates a share that
never travelled from one that has simply not been linked yet (step 8). A share
this side owns and no consumer HOLDS is the silent INT-11 failure. A share both
sides show, with an empty consumer catalog, is normal: AWS requires at least one
data lake administrator in the consumer account before a shared resource is
visible there, so a zero in the admins table explains the emptiness by itself.""")

        # ==============================================================================
        rep.h1("8. Athena workgroups, consumer side")
        if workgroups:
            rep.tabulate(
                ["PROFILE\tWORKGROUP\tENFORCED\tRESULT LOCATION\tSCAN LIMIT"]
                + [f"{p}\t{w}\t{e}\t{o}\t{lim}" for p, w, e, o, lim in workgroups]
            )
        else:
            rep.line("No awsds-* workgroup on any consumer.")

        # ==============================================================================
        rep.h1("9. The derived zone")
        if derived:
            rep.tabulate(
                ["PROFILE\tBUCKET\tLIFECYCLE EXPIRY"] + [f"{p}\t{b}\t{e}" for p, b, e in derived]
            )
        else:
            rep.line("No *-derived bucket on any consumer.")

        # ==============================================================================
        rep.h1("10. EFS (expected: none, or a Studio domain's own home)")
        if efs_rows:
            rep.tabulate(
                ["FILESYSTEM\tSAGEMAKER DOMAIN"]
                + [f"{f}\t{o or '- (untagged)'}" for f, o in efs_rows]
            )
            rep.line()
            rep.line("A row naming a domain is that domain's own home filesystem - service-")
            rep.line("created and retained by design (conventions 5.1 rule 2), expected from")
            rep.line("Stage 6 on. An untagged row is drift - see DL-10 in section 12.")
        else:
            rep.line("No EFS filesystem in the VPN home - none is the design (D24 withdrawn).")

        # ==============================================================================
        rep.h1("11. Security Hub")
        rep.tabulate(["PROFILE\tHUB\tFSBP STANDARD"] + [f"{p}\t{h}\t{f}" for p, h, f in sh_rows])
        rep.line()
        rep.line(f"delegated administrator (securityhub.amazonaws.com): {sh_delegation}")
        rep.text("""
Delegating IS enabling (step 13.1); the org configuration lives in Audit, which
holds no profile - only each member's subscription is read here. Restate INV-09
when the delegation lands.""")

        # ==============================================================================
        rep.h1("12. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  DL-1   lake buckets: versioned, SSE-KMS, Bucket Keys (step 1.2)
  DL-2   bucket policy carries vpce + via + sigage - presence only (step 1.3)
  DL-3   crawlers: never scheduled, never at a catalog/Iceberg target (step 3.6)
  DL-4   awsds-data-catalog-maintenance exists, trusts glue.amazonaws.com only
         (steps 3.2, 3.5)
  DL-5   DataLakeSettings.Parameters still read 4/TRUE - the INT-11 defence,
         IN EVERY ACCOUNT THAT HAS SETTINGS (producer since pass 1, both
         consumers since pass 4 - the hazard is symmetric)
         (step 5.4); THE check to read after any apply in this slice
  DL-6   no IAMAllowedPrincipals create-defaults, per account (step 5.2). In
         Data Governance it is guarded on databases existing; in a consumer it
         is NOT, because the reading has to be available BEFORE the first
         resource link, which is the only moment it can still be acted on
  DL-7   shares out AND HELD by every consumer, resource links resolved, NO
         pending invitation (steps 7, 8)
  DL-8   workgroups enforce their configuration, with a scan limit (step 8, D19)
  DL-9   derived buckets carry a lifecycle expiry (step 9.2, D19)
  DL-10  no EFS in the VPN home beyond a Studio domain's own tagged home
         (conventions 5.1 rule 2) - the plan itself creates none (the NFS
         requirement was withdrawn 2026-08-17, D24 with it)
  DL-11  Security Hub + FSBP in every measured account, or in none (step 13)
  DL-12  the persona's IDENTITY half of the drop-box write, read off the
         PROVISIONED role in each consumer account (pass 4c). DL-2 measures the
         resource half; a cross-account permission is the AND of the two, and
         for three passes only one of them existed (Lesson 28, amended)""")

        # ==============================================================================
        rep.h1("13. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 12 as a pass.

  - `Staging` is unvended and holds no profile; it is deliberately NOT on the
    share (D20) - its absence here is design, not silence.
  - Production joins the consumer side at Stage 9 (the read+write share, the
    drop-box pickup); until then its rows are expected to be empty.
  - Security Hub's org configuration and the first-report triage live in Audit
    (no profile) - console/CloudShell readings, recorded in the stage log.
  - Every Sandbox beyond unit 1 has no profile until Stage 14 vends it (D35);
    add its profile to CONSUMER_PROFILES at the vend.""")

        # ==============================================================================
        rep.h1("14. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/datalake.py")

    # ---------------------------------------------------------------------------------- run
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
