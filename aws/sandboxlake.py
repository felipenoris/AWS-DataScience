#!/usr/bin/env -S uv run --quiet
# sandboxlake.py - Stage 16's evidence: the sandbox lake (awsds-sandbox-lake) and the
# register of who can reach it. The bucket's shape (versioning, SSE-KMS under the account
# data CMK, BPA, the TLS-only statement, NO expiry on current objects - permanence is the
# design), the access role and its trust (enumerated, never a wildcard), the S3 Access
# Grants location and EVERY grant on the bucket classified by SHAPE against the contract
# (group folders, the two grantee classes, orphans) - a grant whose project role no
# longer exists is a dead project that skipped runbook §R. The preflight for Stage 16,
# and the standing regression after it.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/sandboxlake.py                        # the Sandbox profile
#             ./aws/sandboxlake.py awsds-infra-sandbox-1  # the same, named
#             python3 aws/sandboxlake.py -                # CloudShell, ambient credentials
#   writes:   aws/output/sandboxlake.txt   (untracked - see .gitignore)
#   reads:    s3api:GetBucketVersioning, GetBucketEncryption, GetPublicAccessBlock,
#             GetBucketPolicy, GetBucketLifecycleConfiguration, kms:ListAliases,
#             iam:GetRole, ListRoles, ListRolePolicies, GetRolePolicy,
#             ListAttachedRolePolicies, GetPolicy, GetPolicyVersion,
#             s3control:GetAccessGrantsInstance, ListAccessGrantsLocations,
#             ListAccessGrants, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# ONE PROFILE, and why it can see what it sees: every object this stage builds lives in
# the Sandbox account - the bucket, the access role, the Access Grants instance and its
# grants - so awsds-infra-sandbox-1 (the infrastructure user, InfrastructureAccess in
# Sandbox) reads all of it. The domain lives in Data Governance, but nothing here needs
# it: project roles are classified by reading IAM in THIS account.
#
# THE ONE CHECK TO KNOW BY NAME: SL-4. Access is vended-only by design, so the whole
# entitlement is the grant list - an enumerable register. Every grant on the bucket must
# classify as either a standing per-group grant (grantee = a reserved persona role, scope
# = one sso-group folder) or a per-project grant (grantee = a live datazone_usr_role_*).
# Anything else - a directory grantee nobody decided (Stage 16 decision 2), an unknown
# principal, an orphaned project role - is a FAIL to attribute, never a row to tidy.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the in-project read/write through the S3 connection, the
#     s3-read-write vend, the two refusals - are the stage's own (Lesson 20).
#   - Policy readings are PRESENCE, never sufficiency (the TLS statement, the trust).
#   - Whether a well-shaped grant was AUTHORIZED: SL-4 reads shape and orphans; the
#     authorized-or-not half is a HUMAN diff against AWS_STATE.md, which this script
#     does not read.
#   - SL-5's wildcard nuance: a literal bucket name in an Allow is a FAIL; a wildcard
#     resource that merely COVERS the bucket surfaces as a note to read, never a pass.
#   - The portal's connection objects (DataZone-side) are read at the stage, not here:
#     the grant register is the entitlement; a connection without a grant reaches nothing.
#   - "Not built yet" is a note, never a fail - the first run predates pass 1.

from __future__ import annotations

import fnmatch
import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "sandboxlake.txt"

SANDBOX_PROFILE = "awsds-infra-sandbox-1"

# Contracts named in the stage file, so a rename fails loudly rather than silently.
BUCKET = "awsds-sandbox-lake"  # Stage 16 pass 1, conventions naming
ACCESS_ROLE = "awsds-sandbox-lake-access"  # Stage 16 step 2.1 - location AND connection role
DATA_KEY_ALIAS = "alias/awsds-sandbox-data"  # Stage 16 decision 1(a), GOVERNANCE §Encryption
GROUP_PREFIX = "sso-group-"  # every lake prefix is one SSO group's folder
PROJECT_ROLE_PREFIX = "datazone_usr_role_"  # SMUS project user roles
PERSONA_MARK = "AWSReservedSSO_"  # reserved roles = permission-set principals

# The checker's copy of var.tenants (terraform-live/sandbox/lake/variables.tf) - the group
# name IS the prefix, and the pairing is the whole standing-grant contract. A checker
# necessarily restates what it checks, and this divergence is LOUD by construction: a tenant
# added to the slice without a mirror row here makes SL-4 FAIL on the new legitimate grant,
# which is the direction that gets a human to read both files. What the pre-2026-08-26 shape
# got wrong (found by step 6.1's sacrificial grant, the detector's first live anomaly): ANY
# AWSReservedSSO_* grantee classified as standing - the operator's own role included - and
# the detail printed '<group>/*' whatever the real sub-prefix was.
TENANTS = {
    "sso-group-data-scientists": "DataScientistAccess",
    "sso-group-deployment-managers": "DeploymentManagerAccess",
    "sso-group-dev-env-stewards": "DevEnvStewardAccess",
}
PERSONA_SET = "DataScientistAccess"  # SL-5: the set that must NOT allow the bucket directly

ABSENT = (
    "NoSuchBucket|NoSuchPublicAccessBlockConfiguration|NoSuchLifecycleConfiguration"
    "|NoSuchBucketPolicy|ServerSideEncryptionConfigurationNotFoundError|NoSuchEntity"
    "|AccessGrantsInstanceNotExistsError"
)


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

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
            logerr(" ".join(args[:3]), res.stderr)
            return None
        return json.loads(res.stdout or "{}")

    note(f"measuring {cli.label} ...")

    # ------------------------------------------------------------------- the bucket shape
    versioning = run_json("s3api", "get-bucket-versioning", "--bucket", BUCKET, tolerate=ABSENT)
    encryption = run_json("s3api", "get-bucket-encryption", "--bucket", BUCKET, tolerate=ABSENT)
    bpa = run_json("s3api", "get-public-access-block", "--bucket", BUCKET, tolerate=ABSENT)
    policy = run_json("s3api", "get-bucket-policy", "--bucket", BUCKET, tolerate=ABSENT)
    lifecycle = run_json(
        "s3api", "get-bucket-lifecycle-configuration", "--bucket", BUCKET, tolerate=ABSENT
    )
    bucket_exists = versioning is not None

    aliases = run_json("kms", "list-aliases") or {}
    data_key_id = next(
        (
            a.get("TargetKeyId", "")
            for a in aliases.get("Aliases", [])
            if a.get("AliasName") == DATA_KEY_ALIAS
        ),
        "",
    )

    # --------------------------------------------------------------------- the access role
    role = run_json("iam", "get-role", "--role-name", ACCESS_ROLE, tolerate=ABSENT)

    # ------------------------------------------------- the Access Grants instance and rows
    instance = run_json(
        "s3control", "get-access-grants-instance", "--account-id", account, tolerate=ABSENT
    )
    locations = (
        run_json(
            "s3control", "list-access-grants-locations", "--account-id", account, tolerate=ABSENT
        )
        or {}
    ).get("AccessGrantsLocationsList", [])
    grants = (
        run_json("s3control", "list-access-grants", "--account-id", account, tolerate=ABSENT) or {}
    ).get("AccessGrantsList", [])

    lake_scope = f"s3://{BUCKET}"

    def under_lake(scope: str) -> bool:
        # A delimiter matters: s3://awsds-sandbox-lake-<x>/... is a DIFFERENT bucket
        # (the OQ 10 second-unit shape) and must not be swept into this register.
        return scope in (lake_scope, lake_scope + "/") or scope.startswith(lake_scope + "/")

    lake_locations = [loc for loc in locations if under_lake(loc.get("LocationScope", ""))]
    lake_grants = [g for g in grants if under_lake(g.get("GrantScope", ""))]
    default_locations = [loc for loc in locations if loc.get("LocationScope", "") == "s3://"]

    # --------------------------------------- project roles, for the SL-4 orphan reading
    roles_json = run_json(
        "iam",
        "list-roles",
        "--query",
        f"Roles[?starts_with(RoleName, `{PROJECT_ROLE_PREFIX}`)].RoleName",
    )
    roster_read = roles_json is not None  # a failed listing must not read as "no projects"
    project_roles = set(roles_json or [])

    # --------------------------------------------------- the persona inline doc, for SL-5
    reserved = run_json(
        "iam",
        "list-roles",
        "--path-prefix",
        "/aws-reserved/sso.amazonaws.com/",
        "--query",
        f"Roles[?contains(RoleName, `{PERSONA_MARK}{PERSONA_SET}_`)].RoleName",
    )
    persona_role = (reserved or [None])[0]
    persona_docs: list = []  # (policy label, parsed document) - inline AND attached
    if persona_role:
        names = run_json("iam", "list-role-policies", "--role-name", persona_role) or {}
        for pname in names.get("PolicyNames", []):
            doc = run_json(
                "iam", "get-role-policy", "--role-name", persona_role, "--policy-name", pname
            )
            if doc:
                persona_docs.append((f"inline:{pname}", doc.get("PolicyDocument", {})))
        # The attached half is where persona S3 access actually arrives now (the vending
        # policy is a customer-managed attachment) - inline-only would be Lesson 31's gap.
        attached = run_json("iam", "list-attached-role-policies", "--role-name", persona_role) or {}
        for ap in attached.get("AttachedPolicies", []):
            arn = ap.get("PolicyArn", "")
            meta = run_json("iam", "get-policy", "--policy-arn", arn) or {}
            ver = meta.get("Policy", {}).get("DefaultVersionId")
            if not ver:
                continue
            pv = run_json("iam", "get-policy-version", "--policy-arn", arn, "--version-id", ver)
            if pv:
                persona_docs.append(
                    (
                        f"attached:{ap.get('PolicyName', arn)}",
                        pv.get("PolicyVersion", {}).get("Document", {}),
                    )
                )

    # ------------------------------------------------------------------------------ checks

    # SL-1: the bucket's shape - and its PERMANENCE, which is the stage's whole point.
    if not bucket_exists:
        checks.note("SL-1", f"bucket {BUCKET}", "not built yet - expected before Stage 16 pass 1.")
    else:
        vstatus = (versioning or {}).get("Status", "-")
        if vstatus != "Enabled":
            checks.fail("SL-1", "versioning", f"'{vstatus}' - the house module enables it; drift.")
        else:
            checks.ok("SL-1", "versioning", "Enabled")
        rules = (encryption or {}).get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
        sse = rules[0].get("ApplyServerSideEncryptionByDefault", {}) if rules else {}
        keyref = sse.get("KMSMasterKeyID", "")
        if sse.get("SSEAlgorithm") != "aws:kms":
            checks.fail(
                "SL-1", "encryption", f"algorithm '{sse.get('SSEAlgorithm', '-')}' - not SSE-KMS."
            )
        elif not data_key_id:
            checks.fail(
                "SL-1",
                "encryption key",
                f"{DATA_KEY_ALIAS} was not found among this account's aliases - the key binding "
                "is unverifiable this run, and a pass here would be a claim, not a reading "
                "(the alias exists since Stage 5, so its absence is itself a finding).",
            )
        elif data_key_id not in keyref:
            checks.fail(
                "SL-1",
                "encryption key",
                f"default key is not {DATA_KEY_ALIAS} - decision 1(a) binds this bucket to the "
                "account data CMK (GOVERNANCE §Encryption); a different key is an unrecorded decision.",
            )
        else:
            checks.ok("SL-1", "encryption", f"SSE-KMS under {DATA_KEY_ALIAS}")
        flags = (bpa or {}).get("PublicAccessBlockConfiguration", {})
        if flags and all(flags.values()) and len(flags) == 4:
            checks.ok("SL-1", "public access block", "all four flags true")
        else:
            checks.fail("SL-1", "public access block", f"{flags or 'absent'} - must be four trues.")
        pol = (policy or {}).get("Policy", "")
        if "DenyInsecureTransport" in pol:
            checks.ok(
                "SL-1", "bucket policy", "TLS-only statement present (presence, not sufficiency)"
            )
        else:
            checks.fail(
                "SL-1", "bucket policy", "no DenyInsecureTransport statement - module drift."
            )
        current_expiry = [
            r
            for r in (lifecycle or {}).get("Rules", [])
            if r.get("Status") == "Enabled" and "Expiration" in r
        ]
        if current_expiry:
            checks.fail(
                "SL-1",
                "lifecycle",
                f"{len(current_expiry)} rule(s) expire CURRENT objects - permanence is the design; "
                "expiry is the derived zone's contract, not this bucket's (Stage 16's objective; since D19's 2026-08-26 revision the zone is the SMUS project path - OQ 25 owns ITS expiry).",
            )
        else:
            noncurrent = any(
                "NoncurrentVersionExpiration" in r for r in (lifecycle or {}).get("Rules", [])
            )
            checks.ok(
                "SL-1",
                "lifecycle",
                "no expiry on current objects"
                + ("; noncurrent-version expiry present" if noncurrent else ""),
            )

    # SL-2: the access role's trust - enumerated principals, never a wildcard.
    if role is None:
        checks.note(
            "SL-2", f"role {ACCESS_ROLE}", "not built yet - expected before Stage 16 pass 2."
        )
    else:
        problems = []
        project_roles: set = set()
        trust_stmts = role.get("Role", {}).get("AssumeRolePolicyDocument", {}).get("Statement", [])
        trust_stmts = [trust_stmts] if isinstance(trust_stmts, dict) else trust_stmts
        for st in trust_stmts:
            principal = st.get("Principal", {})
            if principal == "*":
                problems.append("a wildcard principal")
                continue
            if not isinstance(principal, dict):
                problems.append(f"an unparsed principal {principal!r}")
                continue
            if principal.get("AWS") == "*":
                problems.append("a wildcard principal")
                continue
            for key in principal:
                if key not in ("Service", "AWS"):
                    problems.append(f"a {key} principal - not a class the design admits")
            services = principal.get("Service", [])
            services = [services] if isinstance(services, str) else services
            for svc in services:
                if svc != "access-grants.s3.amazonaws.com":
                    problems.append(f"unexpected service {svc}")
            arns = principal.get("AWS", [])
            arns = [arns] if isinstance(arns, str) else arns
            for arn in arns:
                if PROJECT_ROLE_PREFIX in arn:
                    # DISTINCT roles, not statements: each wired project contributes THREE
                    # statements (Assume / SetSourceIdentity / TagSession) naming one role,
                    # and a statement count read as a role count says "3 projects" where
                    # one is wired (found on the first wiring, 2026-08-26).
                    project_roles.add(arn.split("/")[-1])
                else:
                    problems.append(f"unexpected AWS principal {arn.split('/')[-1]}")
        if problems:
            checks.fail(
                "SL-2",
                f"trust of {ACCESS_ROLE}",
                "; ".join(problems) + " - the trust admits access-grants.s3.amazonaws.com plus "
                "enumerated project roles and nothing else (Stage 16 step 2.1).",
            )
        else:
            checks.ok(
                "SL-2",
                f"trust of {ACCESS_ROLE}",
                f"the Access Grants service plus {len(project_roles)} enumerated project role(s)",
            )

    # SL-3: the location - the bucket registered against the access role, once.
    if not lake_locations:
        checks.note("SL-3", "lake location", "none - expected before Stage 16 pass 3.")
    else:
        for loc in lake_locations:
            role_arn = loc.get("IAMRoleArn", "-")
            if role_arn.endswith(f"/{ACCESS_ROLE}"):
                checks.ok(
                    "SL-3",
                    f"location {loc.get('AccessGrantsLocationId', '-')}",
                    f"scope {loc.get('LocationScope', '-')} vends {ACCESS_ROLE}",
                )
            else:
                checks.fail(
                    "SL-3",
                    f"location {loc.get('AccessGrantsLocationId', '-')}",
                    f"scope {loc.get('LocationScope', '-')} vends {role_arn.split('/')[-1]} - a "
                    "lake location under any other role is an unrecorded path into the bucket "
                    "(verification (ii) asks whether the connection registered its own; attribute "
                    "before tidying).",
                )
        if len(lake_locations) > 1:
            checks.note(
                "SL-3",
                "lake locations",
                f"{len(lake_locations)} locations under the bucket - verification (ii)'s reading; "
                "record which act created each.",
            )
    for loc in default_locations:
        checks.note(
            "SL-3",
            f"location {loc.get('AccessGrantsLocationId', '-')}",
            f"a DEFAULT-scope location (s3://) covers the lake beside everything else - it vends "
            f"{loc.get('IAMRoleArn', '-').split('/')[-1]}; read which act created it before "
            "treating the lake's register as complete.",
        )

    # SL-4: THE REGISTER. Every grant on the bucket classifies, or it is a finding.
    if not lake_grants:
        checks.note("SL-4", "lake grants", "none - expected before Stage 16 pass 3.")
    for g in lake_grants:
        gid = g.get("AccessGrantId", "-")
        scope = g.get("GrantScope", "")
        rel = scope[len(lake_scope) :].strip("/")  # '<group>/*' or deeper
        top = rel.split("/", 1)[0]
        grantee = g.get("Grantee", {})
        gtype = grantee.get("GranteeType", "-")
        gval = grantee.get("GranteeIdentifier", "-")
        gname = gval.split("/")[-1]
        if gtype != "IAM":
            checks.fail(
                "SL-4",
                f"grant {gid}",
                f"grantee type {gtype} - directory grantees are decision 2(b), not taken; nobody "
                "decided this grant (the register rule).",
            )
        elif not top.startswith(GROUP_PREFIX):
            checks.fail(
                "SL-4",
                f"grant {gid}",
                f"scope '{scope}' is not under an sso-group folder - the prefix contract (§G) "
                "admits group folders only.",
            )
        elif PERSONA_MARK in gname:
            pset = gname.split("_")[1] if "_" in gname else gname
            if TENANTS.get(top) != pset or rel != f"{top}/*":
                checks.fail(
                    "SL-4",
                    f"grant {gid}",
                    f"'{rel}' to {pset} matches no tenant row - a standing grant is exactly "
                    f"'<group>/*' to that group's own permission set (var.tenants); a reserved "
                    "role outside the tenant table (the operator included) holds no prefix.",
                )
            else:
                checks.ok("SL-4", f"grant {gid}", f"standing: {rel} to {pset}")
        elif gname.startswith(PROJECT_ROLE_PREFIX):
            if not roster_read:
                checks.note(
                    "SL-4",
                    f"grant {gid}",
                    f"project grantee {gname} - the IAM roster read FAILED this run, so "
                    "live-or-orphan is unreadable (see the failed-calls section); re-run before "
                    "acting on this row.",
                )
            elif gname in project_roles:
                checks.ok("SL-4", f"grant {gid}", f"project: {rel} to {gname}")
            else:
                checks.fail(
                    "SL-4",
                    f"grant {gid}",
                    f"grantee {gname} no longer exists in IAM - a dead project that skipped "
                    "runbook §R; revoke and deregister (sandbox-lake.md §R).",
                )
        else:
            checks.fail(
                "SL-4",
                f"grant {gid}",
                f"grantee {gname} is neither a reserved persona role nor a project role - "
                "a grant nobody authorized is a finding; attribute it before touching it.",
            )

    # SL-5: vended-only means the persona holds NO direct allow on the bucket - read off
    # the role's inline AND attached documents. A literal bucket name is decisive (fail);
    # a wildcard that merely covers it is surfaced to be read (note), because deciding it
    # here would need the action-by-action reasoning a human owes the statement.
    if persona_role is None:
        checks.note("SL-5", f"{PERSONA_SET} role", "not found in this account - nothing to read.")
    else:
        bucket_arns = (f"arn:aws:s3:::{BUCKET}", f"arn:aws:s3:::{BUCKET}/*")
        offending: list = []
        covered: list = []
        for pname, doc in persona_docs:
            stmts = doc.get("Statement", [])
            stmts = [stmts] if isinstance(stmts, dict) else stmts
            for st in stmts:
                if st.get("Effect") != "Allow":
                    continue  # a Deny naming the bucket would be belt on braces, not a finding
                label = f"{pname}/{st.get('Sid', '(no Sid)')}"
                actions = st.get("Action", [])
                actions = [actions] if isinstance(actions, str) else actions
                s3ish = any(a == "*" or a.lower().startswith("s3") for a in actions)
                resources = st.get("Resource", [])
                resources = [resources] if isinstance(resources, str) else resources
                if any(BUCKET in r for r in resources):
                    offending.append(label)
                elif s3ish and any(
                    fnmatch.fnmatchcase(b, r) for r in resources for b in bucket_arns
                ):
                    covered.append(label)
        if offending:
            checks.fail(
                "SL-5",
                f"{PERSONA_SET} documents",
                f"Allow statement(s) name {BUCKET}: {', '.join(offending)} - the design is "
                "vended-only access (Stage 16, the third compensation); a standing identity "
                "statement bypasses the grant register.",
            )
        if covered:
            checks.note(
                "SL-5",
                f"{PERSONA_SET} documents",
                f"wildcard resource(s) COVER the bucket without naming it: {', '.join(covered)} - "
                "read each statement's actions before calling this reach; a note, not a verdict.",
            )
        if not offending:
            checks.ok(
                "SL-5",
                f"{PERSONA_SET} documents",
                f"no inline or attached Allow names {BUCKET} - vended-only holds on the identity "
                "side" + (" (wildcard coverage noted separately)" if covered else ""),
            )

    # ------------------------------------------------------------------------------ report
    with open(out_path, "w") as stream:
        rep = Report(stream)
        rep.banner(
            f"sandboxlake.txt - the sandbox lake and its register (Stage 16)\n"
            f"generated {context.utc_stamp()} by ./aws/sandboxlake.py"
        )
        rep.text(
            f"\nSections: 1 who is asking; 2 the bucket; 3 the access role; 4 the Access\n"
            f"Grants register; 5 project roles + the persona's policy roster; 6 checks\n"
            f"SL-1..SL-5; 7 calls that failed.\n"
            f"Contracts: BUCKET={BUCKET}  ACCESS_ROLE={ACCESS_ROLE}  KEY={DATA_KEY_ALIAS}\n"
        )

        rep.h1("1. Who is asking")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        rep.h1(f"2. The bucket - {BUCKET}")
        if bucket_exists:
            for args in (
                ("s3api", "get-bucket-versioning", "--bucket", BUCKET),
                ("s3api", "get-bucket-encryption", "--bucket", BUCKET),
                ("s3api", "get-public-access-block", "--bucket", BUCKET),
                ("s3api", "get-bucket-policy", "--bucket", BUCKET),
                ("s3api", "get-bucket-lifecycle-configuration", "--bucket", BUCKET),
            ):
                rep.show(cli, *args)
        else:
            rep.line("(absent - not built yet; SL-1 reads `note` until Stage 16 pass 1)")

        rep.h1(f"3. The access role - {ACCESS_ROLE}")
        if role is not None:
            rep.show(cli, "iam", "get-role", "--role-name", ACCESS_ROLE)
        else:
            rep.line("(absent - not built yet; SL-2 reads `note` until Stage 16 pass 2)")

        rep.h1("4. The Access Grants register")
        rep.line(f"ACCOUNT={account}")
        rep.line()
        if instance is not None:
            rep.show(cli, "s3control", "get-access-grants-instance", "--account-id", account)
            rep.show(cli, "s3control", "list-access-grants-locations", "--account-id", account)
            rep.show(cli, "s3control", "list-access-grants", "--account-id", account)
            rep.h2("the lake's rows, classified (SL-4 is the verdict)")
            rows = ["GRANT\tSCOPE\tGRANTEE\tPERMISSION"]
            for g in lake_grants:
                rows.append(
                    f"{g.get('AccessGrantId', '-')}\t{g.get('GrantScope', '-')}\t"
                    f"{g.get('Grantee', {}).get('GranteeIdentifier', '-').split('/')[-1]}\t"
                    f"{g.get('Permission', '-')}"
                )
            rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-"])
        else:
            rep.line("(no Access Grants instance - it is SMUS-born at the first project;")
            rep.line(" its absence here means no project has ever been provisioned)")

        rep.h1("5. Project roles, and the persona's policy roster")
        rep.line("Project roles in this account (the SL-4 orphan reading's roster):")
        rep.line()
        rep.tabulate(["ROLE"] + (sorted(project_roles) if project_roles else ["(none read)"]))
        rep.line()
        rep.line(f"{PERSONA_SET} documents read for SL-5 ({persona_role or '(role not found)'}):")
        rep.line()
        rep.tabulate(["POLICY"] + ([label for label, _ in persona_docs] or ["(none)"]))

        rep.h1("6. Checks")
        rep.checks_table(checks)

        rep.h1("7. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/sandboxlake.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 7)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 6)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
