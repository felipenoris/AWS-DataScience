#!/usr/bin/env -S uv run --quiet
# s3-persistence.py - every S3 persistence resource the infrastructure user can reach, and
# how each one is configured, all accounts side by side.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile below: the cached token is keyed by the
#             sso-session name, not by profile or account (aws/AWS-CLI.md, "Signing in").
#
#   run:      ./aws/s3-persistence.py                      the infrastructure user's reach
#             ./aws/s3-persistence.py awsds-infra-data     only the profiles named
#             python3 aws/s3-persistence.py -              CloudShell, ambient credentials
#   writes:   aws/output/s3-persistence.txt   (untracked - see .gitignore)
#   reads:    s3api:ListBuckets / ListDirectoryBuckets and, per bucket, GetBucketLocation,
#             GetBucketVersioning, GetBucketEncryption, GetPublicAccessBlock,
#             GetBucketOwnershipControls, GetBucketPolicy, GetBucketLifecycleConfiguration,
#             GetObjectLockConfiguration, GetBucketReplication, GetBucketLogging,
#             GetBucketNotificationConfiguration, GetBucketWebsite, GetBucketCors,
#             GetBucketTagging; s3control:GetPublicAccessBlock / ListAccessPoints /
#             ListMultiRegionAccessPoints / ListStorageLensConfigurations;
#             s3tables:ListTableBuckets; kms:ListAliases; cloudwatch:ListMetrics /
#             GetMetricStatistics; sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call that should always work failed | 2 a check FAILED
#
#   cost:     nothing. Every call is a control-plane read, and the two CloudWatch calls read
#             the free daily storage metrics S3 publishes on its own - no S3 Storage Lens
#             advanced tier, no S3 Inventory report, nothing that bills per object.
#
# WHAT THIS ANSWERS THAT NOTHING ELSE DOES - the reason it is a script and not a loop.
#
#   Three files already judge S3, and each judges ONE contract: tf-backends.py judges the
#   Stage 2 state buckets, datalake.py judges the Stage 5 lake, account-bpa.py judges the
#   ACCOUNT-level Block Public Access flag. Every one of them starts from a list of buckets
#   it expects. None of them answers "what is actually there" - and a bucket nobody expected
#   is invisible to all three, which is precisely the bucket worth finding.
#
#   So this file inverts the direction: it starts from the estate and judges it against
#   invariants that hold for EVERY bucket regardless of which stage made it - it is in
#   us-west-2, it blocks public access, it is encrypted, its ACLs are disabled, its policy
#   admits nobody outside the organization, it serves no website. Data-leakage protection is
#   a requirement of its own (docs/plan/objectives.md), and the estate view is the only one
#   in which "a bucket somewhere less governed" (Lesson 1's shape) is even visible.
#
#   IT DELIBERATELY DOES NOT RE-JUDGE THE OTHER THREE CONTRACTS. A state bucket without a
#   noncurrent-version lifecycle is tf-backends.py's BK-5, not a failure here; the lake's
#   policy branches are datalake.py's. Encoding a step list in two files is Lesson 14 in the
#   small, and the copy that is not the owner is the one that goes stale.
#
# ONE DELIBERATE DEVIATION from aws/INDEX.md's "one profile per script", the same one AZs.py,
# account-bpa.py and tf-backends.py take, for the same reason: the subject is a per-account
# fact whose meaning is the comparison BETWEEN accounts. A bucket holding governed data is
# not a finding; the same bucket in the wrong account is. Section 1 names the identity behind
# every row, which is what the one-profile rule exists to make visible.
#
# WHY THE DEFAULT PROFILE LIST IS NARROWER THAN `awsds-*`. profiles.discover() would also
# return the four persona sessions (awsds-scientist-*, awsds-deploy-*, awsds-governance-*,
# awsds-devenv-*), which belong to DIFFERENT PEOPLE and different sso-sessions: including
# them would make one run demand four more logins to answer a question none of them is asked.
# The default here is the infrastructure user's own reach - every awsds-infra-* profile plus
# awsds-policy-canary, which is the same human through a different permission set (D32) -
# and any profile named on the command line overrides it.
#
# ABSENT IS NOT DENIED, AND THE TABLE SAYS WHICH. A bucket with no lifecycle rule and a
# bucket whose lifecycle this identity may not read both return no rows; read as one value
# they are Lesson 13's verification that answers the same thing either way. Every per-bucket
# call here is classified: a 404 with a "not configured" error code becomes `none`, anything
# else becomes `DENIED` in the cell and a row in section 11's second table. Denied reads do
# NOT set the exit code - refusals are an expected reading of a permission ceiling, and only
# a call that should always work (the preflight, the listings) makes this exit 1.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - MANAGEMENT, LOG ARCHIVE and AUDIT hold no CLI profile and never will (guiding
#     principle 1). Log Archive is where the CloudTrail bucket lives, and INV-14's Object
#     Lock on it is therefore NOT measured here. Section 10 names them.
#   - `Staging` is unvended and every Sandbox beyond the first has no profile until Stage 14.
#     Absent, not reassuring.
#   - THIS IS THE CONFIGURATION, NEVER THE CONTENT. No object is listed, read or counted by
#     hand; the object count in section 6 is CloudWatch's daily metric, which lags by a day
#     or two and is a scale reading, not an inventory.
#   - A PERMISSION IS THE INTERSECTION OF TWO SYSTEMS (Lesson 28). The bucket policy in
#     section 4 is the RESOURCE half. What a given principal may actually do also depends on
#     its identity policy, the SCP above it and, for the lake, Lake Formation - so nothing
#     here proves anyone CAN read a bucket, only who the bucket itself lets in.

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from awslib import context, policydoc, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, note

OUT_NAME = "s3-persistence.txt"

# The infrastructure user's own reach - see the header. `awsds-policy-canary` is the same
# human through a different permission set (D32), so it rides the same sso-session.
INFRA_PREFIX = "awsds-infra-"
CANARY_PROFILE = "awsds-policy-canary"

# The four flags of a Block Public Access configuration, in the order the API returns them.
BPA_FLAGS = ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")

# "This bucket has no such configuration" is a 404 carrying a per-feature error code, and it
# is an ANSWER, not a failure. Everything not on this list - AccessDenied, PermanentRedirect,
# a throttle - reads DENIED in the cell and lands in section 11's second table.
NOT_CONFIGURED = "|".join(
    (
        "NoSuchBucketPolicy",
        "ServerSideEncryptionConfigurationNotFoundError",
        "NoSuchLifecycleConfiguration",
        "ObjectLockConfigurationNotFoundError",
        "ReplicationConfigurationNotFoundError",
        "NoSuchTagSet",
        "NoSuchWebsiteConfiguration",
        "NoSuchCORSConfiguration",
        "NoSuchPublicAccessBlockConfiguration",
        "OwnershipControlsNotFoundError",
        "NoSuchConfiguration",
    )
)

# Condition keys that tie a wildcard principal back to something the organization owns. A
# statement that allows `*` and carries NONE of them is open to the whole internet; one that
# carries any of them is scoped, and WHICH one is the reading - section 4 prints the keys
# rather than collapsing them, because `aws:PrincipalOrgID` and `aws:SourceIp` scope to very
# different things and only the first survives a device moving.
ORG_GUARD_KEYS = frozenset(
    (
        "aws:principalorgid",
        "aws:principalorgpaths",
        "aws:principalaccount",
        "aws:principalarn",
        "aws:principalisawsservice",
        "aws:principaltype",
        "aws:sourceaccount",
        "aws:sourceowner",
        "aws:sourcearn",
        "aws:sourceorgid",
        "aws:sourceorgpaths",
        "aws:sourcevpc",
        "aws:sourcevpce",
        "aws:sourceip",
        "s3:dataaccesspointaccount",
        "s3:dataaccesspointarn",
    )
)

# Name prefixes that say who made a bucket. `awsds-` is this project's convention
# (docs/plan/conventions.md); the rest are the ones a console, a blueprint or a landing zone
# creates on its own - Lesson 17's principals nobody chose, wearing names nobody picked. A
# bucket matching neither is reported as `other`, which is the row to read first.
PROJECT_PREFIX = "awsds-"
SERVICE_PREFIXES = (
    "aws-controltower-",
    "aws-athena-query-results-",
    "aws-glue-",
    "aws-emr-",
    "aws-logs-",
    "awsconfigconforms",
    "cf-templates-",
    "sagemaker-",
    "amazon-",
    "do-not-delete-",
    "datazone-",
    "config-bucket-",
    "elasticbeanstalk-",
)


# ---------------------------------------------------------------------------- small helpers
def human_bytes(value) -> str:
    """A byte count a person can read. `-` when CloudWatch published nothing."""
    if value is None:
        return "-"
    n = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{int(n)} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return "-"


def tsv_rows(text: str) -> list:
    """The rows of an `--output text` answer, with JMESPath's null dropped.

    MEASURED 2026-08-23, and it is why this function exists: `X[].[a,b]` over a key the
    response does not carry at all evaluates to null, and `--output text` prints null as the
    literal string `None`. Read naively that is ONE PHANTOM ROW PER ACCOUNT in every table
    whose real answer is "there is nothing here" - the Storage Lens table said six
    configurations existed, named `None`, in six accounts that have none. Dropping it here is
    what lets an empty section say empty.
    """
    out = []
    for line in text.splitlines():
        fields = line.split("\t")
        if fields and fields[0] and fields[0] != "None":
            out.append(fields)
    return out


def bpa_cell(text: str) -> str:
    """`n/4` - how many of the four Block Public Access flags this reading returned true.

    Three of four is never a partial pass: `RestrictPublicBuckets` on its own still lets a
    public ACL through, so the fraction is printed rather than a yes/no.
    """
    n = text.split("\t").count("True")
    return f"{n}/4"


def origin_of(name: str) -> str:
    """project / service / other - see SERVICE_PREFIXES."""
    if name.startswith(PROJECT_PREFIX):
        return "project"
    if any(name.startswith(p) for p in SERVICE_PREFIXES):
        return "service"
    return "other"


def condense_principal(stmt: dict) -> str:
    """One cell for a statement's Principal, with NotPrincipal marked rather than hidden.

    `Allow` + `NotPrincipal` reads as a narrow statement and is the widest shape in the
    language: it admits everyone the list does not name. It is prefixed `NOT ` here so the
    cell cannot be skimmed as an allow-list.
    """
    key = "NotPrincipal" if "NotPrincipal" in stmt else "Principal"
    principal = stmt.get(key)
    if principal is None:
        return "-"
    if isinstance(principal, str):
        parts = [principal]
    else:
        parts = []
        for kind, value in sorted(principal.items()):
            for one in value if isinstance(value, list) else [value]:
                parts.append(f"{kind}:{one}")
    return ("NOT " if key == "NotPrincipal" else "") + ",".join(parts)


def condition_keys(stmt: dict) -> list:
    """Every condition KEY in a statement, flattened out of its operators."""
    keys = []
    for operand in (stmt.get("Condition") or {}).values():
        if isinstance(operand, dict):
            keys.extend(operand.keys())
    return sorted(set(keys))


def wildcard_principal(stmt: dict) -> bool:
    if "NotPrincipal" in stmt:
        return True
    principal = stmt.get("Principal")
    if principal == "*":
        return True
    if isinstance(principal, dict):
        for value in principal.values():
            if any(one == "*" for one in (value if isinstance(value, list) else [value])):
                return True
    return False


def is_open(stmt: dict) -> bool:
    """Does this statement allow a principal the organization does not contain?

    Allow + a wildcard principal + no condition key tying the caller back to the org, an
    account, a VPC endpoint or an address. A `Deny` with `Principal: *` is the TLS-only
    statement and the opposite of a hole, which is why Effect is tested first.
    """
    if stmt.get("Effect") != "Allow" or not wildcard_principal(stmt):
        return False
    return not ({k.lower() for k in condition_keys(stmt)} & ORG_GUARD_KEYS)


def count_actions(stmt: dict) -> str:
    actions = stmt.get("Action", stmt.get("NotAction"))
    if actions is None:
        return "0"
    n = len(actions) if isinstance(actions, list) else 1
    return f"{n}!" if "NotAction" in stmt else str(n)


@dataclass
class Bucket:
    """One bucket's whole reading. Every field is already a printable cell."""

    profile: str
    name: str
    created: str
    region: str
    origin: str
    versioning: str = "-"
    mfa_delete: str = "-"
    sse: str = "-"
    key: str = "-"
    bucket_key: str = "-"
    bpa: str = "-"
    ownership: str = "-"
    policy: str = "-"
    tls_only: str = "-"
    statements: list = field(default_factory=list)  # (sid, effect, principal, n, conds, open)
    n_open: int = 0
    lifecycle: str = "-"
    lock: str = "-"
    replication: str = "-"
    repl_targets: list = field(default_factory=list)
    logging: str = "-"
    notify: str = "-"
    website: str = "-"
    cors: str = "-"
    tags: str = "-"
    objects: str = "-"
    size: str = "-"
    classes: str = "-"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    if argv:
        selected, source = profiles.select(argv)
    else:
        every = profiles.discover()
        selected = [x for x in every if x.startswith(INFRA_PREFIX)]
        if CANARY_PROFILE in every:
            selected.append(CANARY_PROFILE)
        if not selected:
            note(f"no profiles to measure (no '{INFRA_PREFIX}*' profile in ~/.aws/config)")
            return 1
        source = (
            f"the infrastructure user's reach - every '{INFRA_PREFIX}*' profile "
            f"plus {CANARY_PROFILE}"
        )

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]
    checks = Checks()

    # Reads this identity was refused, kept OUT of the error log on purpose: a refusal is a
    # reading of the permission ceiling, not a broken script. Section 11 prints them.
    refused: list = []  # (profile, subject, call, wording)

    def probe(cli: AwsCli, subject: str, *args: str) -> tuple:
        """(text, state) with state in {ok, none, denied}. The one call shape this file uses.

        `none` is a configuration that is not there; `denied` is a configuration this
        identity may not read. Collapsing the two is what makes an S3 report unreadable.
        """
        res = cli.run(*args, tolerate=NOT_CONFIGURED, log=False)
        if res.tolerated:
            return "", "none"
        if not res.ok:
            refused.append((cli.profile or "-", subject, " ".join(args[:2]), head2(res.merged)))
            return "", "denied"
        return res.stdout, "ok"

    def cell(text: str, state: str, when_none: str = "none") -> str:
        return {"none": when_none, "denied": "DENIED"}.get(state, text or when_none)

    # ------------------------------------------------------------------ measure each account
    aliases: list = []  # (profile, alias, target key id)
    buckets: list = []  # Bucket
    account_bpa: dict = {}  # profile -> "4/4" | ...
    access_points: list = []  # (profile, name, bucket, network origin, bpa)
    mraps: list = []  # (profile, name, alias, status)
    table_buckets: list = []  # (profile, name, arn, created)
    dir_buckets: list = []  # (profile, name, created)
    storage_lens: list = []  # (profile, id, home region, enabled)

    def alias_of(profile: str, key: str) -> str:
        """A KMS key ARN or id resolved back to its alias, so a table can name the key.

        `(no alias)` is a real finding in its own right: a bucket encrypted under a key
        nothing can refer to by name makes every later report unreadable (tf-backends.py's
        BK-2 note carries the same sentence).
        """
        if not key:
            return "-"
        kid = key.rsplit("/", 1)[-1]
        for p, aname, akey in aliases:
            if p == profile and akey == kid:
                return aname
        if key.startswith("arn:") or len(kid) == 36:
            return "(no alias)"
        return key

    now = datetime.now(timezone.utc)
    metric_start = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    metric_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    for caller in live:
        p = caller.profile
        cli = profiles.cli_for(p, errors)
        note(f"measuring {p} ...")

        # KMS aliases first, so every later row can name a key rather than a uuid.
        res = cli.run(
            "kms",
            "list-aliases",
            "--query",
            "Aliases[?starts_with(AliasName,`alias/`)].[AliasName,TargetKeyId]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) >= 2 and f[0]:
                aliases.append((p, f[0], f[1]))

        # -------------------------------------------------------------- the account surfaces
        acct = caller.account or ""
        if acct:
            text, state = probe(
                cli,
                "account",
                "s3control",
                "get-public-access-block",
                "--account-id",
                acct,
                "--query",
                "PublicAccessBlockConfiguration.[" + ",".join(BPA_FLAGS) + "]",
                "--output",
                "text",
            )
            if state == "ok":
                account_bpa[p] = bpa_cell(text)
            else:
                account_bpa[p] = {"none": "NOT SET", "denied": "DENIED"}[state]

            text, state = probe(
                cli,
                "account",
                "s3control",
                "list-access-points",
                "--account-id",
                acct,
                "--query",
                "AccessPointList[].[Name,Bucket,NetworkOrigin]",
                "--output",
                "text",
            )
            for f in tsv_rows(text):
                access_points.append((p, f[0], f[1], f[2] if len(f) > 2 else "-"))

            text, state = probe(
                cli,
                "account",
                "s3control",
                "list-multi-region-access-points",
                "--account-id",
                acct,
                "--query",
                "AccessPoints[].[Name,Alias,Status]",
                "--output",
                "text",
            )
            for f in tsv_rows(text):
                mraps.append((p, f[0], f[1] if len(f) > 1 else "-", f[2] if len(f) > 2 else "-"))

            text, state = probe(
                cli,
                "account",
                "s3control",
                "list-storage-lens-configurations",
                "--account-id",
                acct,
                "--query",
                "StorageLensConfigurationList[].[Id,HomeRegion,IsEnabled]",
                "--output",
                "text",
            )
            for f in tsv_rows(text):
                storage_lens.append(
                    (p, f[0], f[1] if len(f) > 1 else "-", f[2] if len(f) > 2 else "-")
                )

        # S3 Tables and S3 Express are separate namespaces: neither shows up in list-buckets,
        # which is exactly why they are asked for by name. `S3TableCatalog` is one of the
        # eleven enabled SMUS blueprints (docs/SMUS.md), so a table bucket is a surface a
        # project can create without anyone writing Terraform for it.
        text, state = probe(
            cli,
            "account",
            "s3tables",
            "list-table-buckets",
            "--query",
            "tableBuckets[].[name,arn,createdAt]",
            "--output",
            "text",
        )
        for f in tsv_rows(text):
            table_buckets.append(
                (p, f[0], f[1] if len(f) > 1 else "-", f[2] if len(f) > 2 else "-")
            )

        text, state = probe(
            cli,
            "account",
            "s3api",
            "list-directory-buckets",
            "--query",
            "Buckets[].[Name,CreationDate]",
            "--output",
            "text",
        )
        for f in tsv_rows(text):
            dir_buckets.append((p, f[0], f[1] if len(f) > 1 else "-"))

        # Which (bucket, storage class) pairs S3 publishes a daily size metric for. One call
        # per account instead of one per bucket, and it doubles as the storage-class column.
        classes: dict = {}
        text, state = probe(
            cli,
            "account",
            "cloudwatch",
            "list-metrics",
            "--namespace",
            "AWS/S3",
            "--metric-name",
            "BucketSizeBytes",
            "--query",
            "Metrics[].Dimensions",
            "--output",
            "json",
        )
        if state == "ok" and text:
            try:
                for dims in json.loads(text):
                    d = {x["Name"]: x["Value"] for x in dims}
                    if "BucketName" in d and "StorageType" in d:
                        classes.setdefault(d["BucketName"], []).append(d["StorageType"])
            except (ValueError, KeyError, TypeError):
                pass

        # --------------------------------------------------------------------- the buckets
        res = cli.run(
            "s3api", "list-buckets", "--query", "Buckets[].[Name,CreationDate]", "--output", "text"
        )
        if not res.ok:
            continue
        rows = sorted(tsv_rows(res.text))

        note(f"  {len(rows)} bucket(s) in {p}")
        for row in rows:
            name = row[0]
            note(f"    {name}")
            created = (row[1] if len(row) > 1 else "-").split("T")[0]

            # THE REGION COMES FIRST, and not only because it is a finding on its own: every
            # per-bucket call below has to be made against the bucket's OWN Region or S3
            # answers PermanentRedirect, which would read as a denial for a bucket that is
            # merely somewhere else.
            loc, loc_state = probe(
                cli,
                name,
                "s3api",
                "get-bucket-location",
                "--bucket",
                name,
                "--query",
                "LocationConstraint",
                "--output",
                "text",
            )
            if loc_state != "ok":
                region = "DENIED" if loc_state == "denied" else "?"
            else:
                # The two legacy spellings the API still returns for its two oldest Regions.
                region = {"None": "us-east-1", "EU": "eu-west-1", "": "us-east-1"}.get(loc, loc)

            b = Bucket(
                profile=p,
                name=name,
                created=created,
                region=region,
                origin=origin_of(name),
            )
            buckets.append(b)
            if loc_state != "ok":
                continue

            bcli = AwsCli(profile=p, region=region, errors=errors, echo_profile=True)

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-versioning",
                "--bucket",
                name,
                "--query",
                "[Status,MFADelete]",
                "--output",
                "text",
            )
            if state == "ok":
                f = text.split("\t")
                b.versioning = f[0] if f and f[0] not in ("None", "") else "NOT SET"
                b.mfa_delete = f[1] if len(f) > 1 and f[1] != "None" else "-"
            else:
                b.versioning = cell("", state, "NOT SET")

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-encryption",
                "--bucket",
                name,
                "--query",
                "ServerSideEncryptionConfiguration.Rules[0].["
                "ApplyServerSideEncryptionByDefault.SSEAlgorithm,"
                "ApplyServerSideEncryptionByDefault.KMSMasterKeyID,"
                "BucketKeyEnabled]",
                "--output",
                "text",
            )
            if state == "ok":
                f = text.split("\t")
                b.sse = f[0] if f and f[0] != "None" else "NOT SET"
                b.key = alias_of(p, "" if len(f) < 2 or f[1] == "None" else f[1])
                b.bucket_key = f[2] if len(f) > 2 and f[2] != "None" else "-"
            else:
                b.sse = cell("", state, "NOT SET")

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-public-access-block",
                "--bucket",
                name,
                "--query",
                "PublicAccessBlockConfiguration.[" + ",".join(BPA_FLAGS) + "]",
                "--output",
                "text",
            )
            b.bpa = bpa_cell(text) if state == "ok" else cell("", state, "NOT SET")

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-ownership-controls",
                "--bucket",
                name,
                "--query",
                "OwnershipControls.Rules[0].ObjectOwnership",
                "--output",
                "text",
            )
            b.ownership = cell(text, state, "NOT SET")

            # THE RESOURCE HALF OF EVERY PERMISSION THIS BUCKET GRANTS - and only that half
            # (Lesson 28). Parsed rather than grepped: `Principal: *` is the whole question
            # and it is one JSON level below any string a grep would match.
            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-policy",
                "--bucket",
                name,
                "--query",
                "Policy",
                "--output",
                "text",
            )
            if state == "ok" and text:
                try:
                    doc = json.loads(text)
                except ValueError:
                    b.policy = "UNPARSEABLE"
                else:
                    stmts = policydoc.statements(doc)
                    b.policy = f"{len(stmts)} stmt(s)"
                    b.tls_only = "-"
                    for st in stmts:
                        opened = is_open(st)
                        keys = condition_keys(st)
                        if st.get("Effect") == "Deny" and any(
                            k.lower() == "aws:securetransport" for k in keys
                        ):
                            b.tls_only = "yes"
                        b.statements.append(
                            (
                                st.get("Sid") or "(no Sid)",
                                st.get("Effect", "?"),
                                condense_principal(st),
                                count_actions(st),
                                ",".join(keys) or "-",
                                "OPEN" if opened else "-",
                            )
                        )
                        if opened:
                            b.n_open += 1
                    if b.tls_only == "-":
                        b.tls_only = "NO"
            else:
                b.policy = cell("", state, "none")
                b.tls_only = "-" if state == "none" else "DENIED"

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-lifecycle-configuration",
                "--bucket",
                name,
                "--query",
                "Rules[].[ID,Status]",
                "--output",
                "text",
            )
            if state == "ok":
                n = len([ln for ln in text.splitlines() if ln])
                b.lifecycle = f"{n} rule(s)" if n else "none"
            else:
                b.lifecycle = cell("", state)

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-object-lock-configuration",
                "--bucket",
                name,
                "--query",
                "ObjectLockConfiguration.[ObjectLockEnabled,Rule.DefaultRetention.Mode]",
                "--output",
                "text",
            )
            if state == "ok":
                f = [x for x in text.split("\t") if x and x != "None"]
                b.lock = "/".join(f) if f else "off"
            else:
                b.lock = cell("", state, "off")

            # REPLICATION IS AN EGRESS PATH WITH NO NETWORK IN IT. A rule here copies every
            # new object into another bucket - possibly another account - continuously, and
            # no VPC endpoint policy, no SCP on the reader and no DNS allow-list is in that
            # path. Every destination is printed; none is judged, because whether it is
            # inside the organization is not derivable from a bucket ARN.
            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-replication",
                "--bucket",
                name,
                "--query",
                "ReplicationConfiguration.Rules[].[ID,Status,Destination.Bucket,"
                "Destination.Account]",
                "--output",
                "text",
            )
            if state == "ok":
                lines = [ln for ln in text.splitlines() if ln]
                b.replication = f"{len(lines)} rule(s)" if lines else "none"
                for ln in lines:
                    f = ln.split("\t")
                    b.repl_targets.append(
                        (
                            p,
                            name,
                            f[0],
                            f[1] if len(f) > 1 else "-",
                            f[2] if len(f) > 2 else "-",
                            f[3] if len(f) > 3 else "-",
                        )
                    )
            else:
                b.replication = cell("", state)

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-logging",
                "--bucket",
                name,
                "--query",
                "LoggingEnabled.[TargetBucket,TargetPrefix]",
                "--output",
                "text",
            )
            if state == "ok" and text and not text.startswith("None"):
                f = text.split("\t")
                b.logging = f"{f[0]}/{f[1] if len(f) > 1 and f[1] != 'None' else ''}"
            else:
                b.logging = cell("", state, "off")

            # A notification is the other silent egress: an object landing here can invoke a
            # Lambda, fill a queue or raise an EventBridge event, and the target may sit in
            # another account. Counted per channel so a non-zero cell names which one.
            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-notification-configuration",
                "--bucket",
                name,
                "--output",
                "json",
            )
            if state == "ok" and text:
                try:
                    cfg = json.loads(text)
                except ValueError:
                    b.notify = "UNPARSEABLE"
                else:
                    parts = []
                    for label, key in (
                        ("topic", "TopicConfigurations"),
                        ("queue", "QueueConfigurations"),
                        ("lambda", "LambdaFunctionConfigurations"),
                    ):
                        n = len(cfg.get(key) or [])
                        if n:
                            parts.append(f"{label}:{n}")
                    if cfg.get("EventBridgeConfiguration") is not None:
                        parts.append("eventbridge")
                    b.notify = ",".join(parts) if parts else "none"
            else:
                b.notify = cell("", state)

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-website",
                "--bucket",
                name,
                "--query",
                "IndexDocument.Suffix",
                "--output",
                "text",
            )
            # THE CALL SUCCEEDING IS THE FACT, not what the query returned: a redirect-only
            # website configuration carries no IndexDocument, so `--query IndexDocument.Suffix`
            # answers `None` for a bucket that is very much serving the web. Reading the query
            # instead of the status is how a website reads `no` (Lesson 13's shape).
            if state == "ok":
                b.website = f"YES ({text})" if text and text != "None" else "YES (redirect-only)"
            else:
                b.website = cell("", state, "no")

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-cors",
                "--bucket",
                name,
                "--query",
                "CORSRules[].AllowedOrigins[]",
                "--output",
                "text",
            )
            if state == "ok":
                origins = sorted(set(text.split())) if text else []
                if not origins:
                    b.cors = "none"
                elif "*" in origins:
                    b.cors = "ANY ORIGIN"
                else:
                    b.cors = ",".join(origins)
            else:
                b.cors = cell("", state)

            text, state = probe(
                bcli,
                name,
                "s3api",
                "get-bucket-tagging",
                "--bucket",
                name,
                "--query",
                "TagSet[].[Key,Value]",
                "--output",
                "text",
            )
            if state == "ok":
                pairs = [ln.replace("\t", "=") for ln in text.splitlines() if ln]
                b.tags = " ".join(pairs) if pairs else "none"
            else:
                b.tags = cell("", state)

            # ---------------------------------------------------------- what is actually in it
            b.classes = ",".join(sorted(set(classes.get(name, [])))) or "-"
            total = None
            for storage_type in sorted(set(classes.get(name, []))):
                text, state = probe(
                    cli,
                    name,
                    "cloudwatch",
                    "get-metric-statistics",
                    "--namespace",
                    "AWS/S3",
                    "--metric-name",
                    "BucketSizeBytes",
                    "--dimensions",
                    f"Name=BucketName,Value={name}",
                    f"Name=StorageType,Value={storage_type}",
                    "--start-time",
                    metric_start,
                    "--end-time",
                    metric_end,
                    "--period",
                    "86400",
                    "--statistics",
                    "Average",
                    "--query",
                    "sort_by(Datapoints,&Timestamp)[-1].Average",
                    "--output",
                    "text",
                )
                if state == "ok" and text and text != "None":
                    total = (total or 0) + float(text)
            b.size = human_bytes(total)

            text, state = probe(
                cli,
                name,
                "cloudwatch",
                "get-metric-statistics",
                "--namespace",
                "AWS/S3",
                "--metric-name",
                "NumberOfObjects",
                "--dimensions",
                f"Name=BucketName,Value={name}",
                "Name=StorageType,Value=AllStorageTypes",
                "--start-time",
                metric_start,
                "--end-time",
                metric_end,
                "--period",
                "86400",
                "--statistics",
                "Average",
                "--query",
                "sort_by(Datapoints,&Timestamp)[-1].Average",
                "--output",
                "text",
            )
            b.objects = str(int(float(text))) if state == "ok" and text and text != "None" else "-"

    # -------------------------------------------------------------------------------- checks
    for caller in live:
        p = caller.profile
        mine = [b for b in buckets if b.profile == p]
        if not mine:
            checks.note(
                "SP-0",
                f"{p} holds no bucket",
                "list-buckets returned nothing. Correct for `Policy Canary`, whose "
                "point is to stay empty (D29); a REGRESSION for any account whose "
                "stages have run.",
            )
            continue
        by_origin = {}
        for b in mine:
            by_origin[b.origin] = by_origin.get(b.origin, 0) + 1
        checks.ok(
            "SP-0",
            f"{p} holds {len(mine)} bucket(s)",
            ", ".join(f"{k}:{v}" for k, v in sorted(by_origin.items())),
        )
        if by_origin.get("other"):
            checks.note(
                "SP-0",
                f"{p} holds {by_origin['other']} bucket(s) matching no known prefix",
                "neither `awsds-` nor a service prefix this file knows. Either a "
                "bucket made by hand, or a service whose prefix belongs in "
                "SERVICE_PREFIXES - section 2 names them.",
            )

    for b in buckets:
        where = f"{b.name} ({b.profile})"

        if b.region == context.REGION:
            checks.ok("SP-1", f"{where} is in {context.REGION}", b.region)
        elif b.region in ("DENIED", "?"):
            checks.note("SP-1", f"{where} has no readable Region", b.region)
        else:
            checks.fail(
                "SP-1",
                f"{where} is in {context.REGION}",
                f"{b.region} - every governed account sits under {context.REGION} "
                "(CLAUDE.md). A bucket outside it is outside every Region-scoped "
                "condition written so far, and outside the endpoints the VPCs have.",
            )

        if b.bpa == "4/4":
            checks.ok("SP-2", f"block public access on {where}", "4/4")
        elif b.bpa == "DENIED":
            checks.note("SP-2", f"block public access on {where}", "not readable as this identity")
        else:
            checks.fail(
                "SP-2",
                f"block public access on {where}",
                f"{b.bpa} - three of four is not a partial pass: RestrictPublicBuckets "
                "alone still allows a public ACL. The ACCOUNT-level flag may still "
                "cover it (section 7), and relying on that is a different control.",
            )

        if b.sse in ("aws:kms", "aws:kms:dsse"):
            checks.ok("SP-3", f"default encryption on {where}", f"{b.sse}, key {b.key}")
            if b.key == "(no alias)":
                checks.note(
                    "SP-3",
                    f"the key behind {where} has no alias",
                    "nothing in a report can name it. Aliases are free; add one.",
                )
        elif b.sse == "AES256":
            checks.note(
                "SP-3",
                f"default encryption on {where}",
                "AES256 - SSE-S3, an AWS-owned key. Encrypted, but the key policy "
                "is where 'who may read this' is expressed and SSE-S3 has none "
                "(Lesson 18). A contract-bearing bucket failing this is "
                "tf-backends.py's BK-2 or datalake.py's, not this file's.",
            )
        elif b.sse == "DENIED":
            checks.note("SP-3", f"default encryption on {where}", "not readable as this identity")
        else:
            checks.fail(
                "SP-3",
                f"default encryption on {where}",
                f"{b.sse} - S3 has applied SSE-S3 by default since 2023, so an unset "
                "configuration is not plaintext; it is an unstated intention, and "
                "nothing prevents an upload choosing otherwise (Lesson 5).",
            )

        if b.ownership == "BucketOwnerEnforced":
            checks.ok("SP-4", f"ACLs disabled on {where}", b.ownership)
        elif b.ownership == "DENIED":
            checks.note("SP-4", f"ACLs disabled on {where}", "not readable as this identity")
        else:
            checks.fail(
                "SP-4",
                f"ACLs disabled on {where}",
                f"{b.ownership} - with ACLs live, a grant can be attached to an "
                "OBJECT, below every bucket policy in this report. Block Public "
                "Access neutralises the public grants and leaves the "
                "cross-account ones.",
            )

        if b.policy == "DENIED":
            checks.note("SP-5", f"the policy on {where}", "not readable as this identity")
        elif b.n_open:
            checks.fail(
                "SP-5",
                f"the policy on {where} admits only the organization",
                f"{b.n_open} statement(s) Allow a wildcard principal with no "
                "condition tying the caller to an org, an account, a VPC endpoint "
                "or an address - section 4 names the Sids.",
            )
        elif b.policy != "none":
            checks.ok("SP-5", f"the policy on {where} admits only the organization", b.policy)

        if b.website.startswith("YES"):
            checks.fail(
                "SP-6",
                f"{where} serves no website",
                f"{b.website} - a website endpoint is anonymous HTTP over the "
                "bucket's objects and answers on a path no VPC endpoint policy sees.",
            )
        elif b.cors == "ANY ORIGIN":
            checks.fail(
                "SP-6",
                f"{where} has no wildcard CORS",
                "AllowedOrigins includes `*` - any page on the internet may issue "
                "browser reads against this bucket. It is not itself an "
                "authorization, and it removes the only obstacle in front of one.",
            )
        elif b.website not in ("DENIED", "-") and b.cors not in ("DENIED", "-"):
            checks.ok("SP-6", f"{where} serves no website, no wildcard CORS", f"cors: {b.cors}")

        if b.repl_targets:
            checks.note(
                "SP-7",
                f"{where} replicates continuously",
                f"{b.replication} - read the destinations in section 5. Replication "
                "copies every new object out with no network in the path: no VPC "
                "endpoint policy, no SCP on a reader, no DNS allow-list.",
            )

        if b.versioning == "Enabled":
            checks.ok("SP-8", f"versioning on {where}", "Enabled")
        elif b.versioning == "DENIED":
            checks.note("SP-8", f"versioning on {where}", "not readable as this identity")
        else:
            checks.note(
                "SP-8",
                f"versioning on {where}",
                f"{b.versioning} - a durability reading, not an exposure one, so it "
                "is a note here. It is a FAILURE for a state bucket "
                "(tf-backends.py BK-1) and for the lake (datalake.py), which own it.",
            )

    extra = len(dir_buckets) + len(table_buckets) + len(access_points) + len(mraps)
    if extra:
        checks.note(
            "SP-9",
            "surfaces list-buckets does not show",
            f"{len(dir_buckets)} directory bucket(s), {len(table_buckets)} table "
            f"bucket(s), {len(access_points)} access point(s), {len(mraps)} "
            "multi-region access point(s). Section 7. None of them appears in "
            "section 2, and none is covered by any other file in aws/.",
        )
    else:
        checks.ok(
            "SP-9",
            "surfaces list-buckets does not show",
            "none - no directory bucket, table bucket, access point or MRAP anywhere",
        )

    # ---------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Every S3 persistence resource this identity can reach, and its configuration")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION} (per-bucket calls follow the bucket's own Region)
produced  : aws/s3-persistence.py   (index: aws/INDEX.md)

SECTIONS
  1.  Which accounts were measured, and as whom
  2.  The estate - every bucket, side by side
  3.  Encryption - the key behind each bucket
  4.  Exposure - what could reach a bucket from outside
  5.  Durability - versioning, lifecycle, lock, replication, logging, notifications
  6.  What is actually stored
  7.  The surfaces `list-buckets` does not show
  8.  Tags - which buckets somebody declared, and which somebody left
  9.  The checks
  10. The accounts and objects nothing here is measuring
  11. Calls that failed, and reads this identity was refused

HOW TO READ THIS FILE
  - `none` AND `DENIED` ARE DIFFERENT ANSWERS and never share a cell. `none` is a
    configuration that is not there; `DENIED` is one this identity may not read. A
    refusal does not set the exit code - it is a reading of the permission ceiling,
    and section 11's second table is where they are collected.
  - THIS FILE OWNS NO STAGE CONTRACT. It judges the estate against invariants that
    hold for every bucket: in {context.REGION}, public access blocked, encrypted,
    ACLs disabled, no wildcard principal, no website. The state buckets' own
    contract is `tf-backends.py`, the lake's is `datalake.py`, the ACCOUNT-level
    Block Public Access flag is `account-bpa.py`. Where a reading here disagrees
    with one of those, THAT file is the owner.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 10 names the ones nothing
    reached; an account in neither section 2 nor section 10 is the hole this script
    exists to expose.
  - THE `ORIGIN` COLUMN IS A NAME MATCH, NOT PROVENANCE. `project` is the
    `awsds-` convention, `service` is a prefix a console or a landing zone uses,
    `other` is a bucket matching neither - which is the row to read first, and is
    a note rather than a failure because a service this file has not met yet looks
    exactly the same.
  - SECTION 6 IS CLOUDWATCH, NOT AN INVENTORY. S3 publishes those two metrics once
    a day, so a bucket filled this morning still reads `-`, and a bucket emptied
    this morning still reads its old size.
  - Before calling anything here a finding, read docs/AWS_STATE.md - the
    invariants, the known exceptions, and what a later stage changes anyway.""")

        # =====================================================================================
        rep.h1("1. Which accounts were measured, and as whom")

        rep.text("""A profile is an (account, permission set) pair. The default list is the infrastructure
user's own reach - every `awsds-infra-*` profile plus `awsds-policy-canary`, the same
human through a different permission set (D32) - because the four persona sessions
belong to different people and would each demand their own login. A `(failed)` row is a
profile that did not authenticate, never a compliant one.

""")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        # =====================================================================================
        rep.h1("2. The estate - every bucket, side by side")

        rep.text("""$ aws --profile <profile> s3api list-buckets
$ aws --profile <profile> s3api get-bucket-location --bucket <bucket>

ONE ROW PER BUCKET, IN EVERY ACCOUNT THIS IDENTITY REACHES. Nothing is filtered: the
question this file asks is what is there, and a filter is what makes an unexpected
bucket invisible. `CREATED` is the bucket's creation date, which S3 also bumps when the
bucket policy is edited - so it is an age, not an audit trail.

""")
        if buckets:
            rep.tabulate(
                ["PROFILE\tBUCKET\tREGION\tCREATED\tORIGIN\tOBJECTS\tSIZE"]
                + [
                    f"{b.profile}\t{b.name}\t{b.region}\t{b.created}\t{b.origin}\t"
                    f"{b.objects}\t{b.size}"
                    for b in buckets
                ]
            )
            rep.line()
            others = [b for b in buckets if b.origin == "other"]
            if others:
                rep.text("""THE `other` ROWS, GATHERED - a bucket matching neither the project convention nor a
service prefix this file knows. Read each one: it is either somebody's hand, or a
service whose prefix belongs in SERVICE_PREFIXES at the top of the script.

""")
                rep.tabulate(
                    ["PROFILE\tBUCKET\tCREATED"]
                    + [f"{b.profile}\t{b.name}\t{b.created}" for b in others]
                )
            else:
                rep.line("Every bucket above matches either the `awsds-` convention or a known")
                rep.line("service prefix. No `other` rows.")
        else:
            rep.line("(no bucket in any measured account)")

        # =====================================================================================
        rep.h1("3. Encryption - the key behind each bucket")

        rep.text("""$ aws --profile <profile> s3api get-bucket-encryption --bucket <bucket>
$ aws --profile <profile> kms list-aliases

THE ALGORITHM IS NOT THE CONTROL; THE KEY POLICY IS. Every bucket S3 hands back is
encrypted at rest, so the column that decides anything is `KEY`: `aws:kms` under a
customer-managed key means "who may read this" is expressible and expressed somewhere,
`AES256` means an AWS-owned key with no policy anyone can write (Lesson 18). The
per-account rule for the lake is one data CMK per account, `alias/awsds-<env>-data`
(docs/GOVERNANCE.md) - which is why this table names aliases and not uuids.

`BUCKET KEY` is a cost switch, not a security one: it caches a data key per bucket and
cuts the KMS call rate, and it is `True` on everything the house s3-bucket module makes.

""")
        if buckets:
            rep.tabulate(
                ["PROFILE\tBUCKET\tSSE\tKEY\tBUCKET KEY"]
                + [f"{b.profile}\t{b.name}\t{b.sse}\t{b.key}\t{b.bucket_key}" for b in buckets]
            )
        else:
            rep.line("(no bucket measured)")

        rep.text("""
Every KMS alias in each measured account, so a key named in the table above can be
placed, and a key that should exist and does not is visible:

""")
        if aliases:
            rep.tabulate(
                ["PROFILE\tALIAS\tTARGET KEY"] + sorted(f"{p}\t{a}\t{k}" for p, a, k in aliases)
            )
        else:
            rep.line("(no alias in any measured account)")

        # =====================================================================================
        rep.h1("4. Exposure - what could reach a bucket from outside")

        rep.text("""$ aws --profile <profile> s3api get-public-access-block         --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-ownership-controls  --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-policy              --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-website             --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-cors                --bucket <bucket>

FIVE INDEPENDENT DOORS, WHICH IS WHY THEY ARE ONE TABLE. Block Public Access is the
blanket; object ownership decides whether per-object ACLs exist at all, BELOW every
policy here; the bucket policy is the resource half of every grant (the identity half
lives in Identity, and reach is the intersection of the two - Lesson 28); a website
configuration is anonymous HTTP over the objects; a wildcard CORS rule removes the one
obstacle a browser puts in front of a cross-origin read.

`OPEN` counts statements that Allow a wildcard principal with NO condition tying the
caller back to an organization, an account, a VPC endpoint or an address. A `Deny` with
`Principal: *` - the TLS-only statement - is the opposite of a hole and is not counted.

""")
        if buckets:
            rep.tabulate(
                ["PROFILE\tBUCKET\tBPA\tOWNERSHIP\tPOLICY\tTLS-ONLY\tOPEN\tWEBSITE\tCORS"]
                + [
                    f"{b.profile}\t{b.name}\t{b.bpa}\t{b.ownership}\t{b.policy}\t"
                    f"{b.tls_only}\t{b.n_open or '-'}\t{b.website}\t{b.cors}"
                    for b in buckets
                ]
            )
        else:
            rep.line("(no bucket measured)")

        rep.text("""
EVERY BUCKET POLICY, ONE ROW PER STATEMENT - the discipline POLICIES.md applies to the
organization policies, applied here to the resource ones. The document bodies are NOT
reproduced: what a statement is FOR belongs in the slice READMEs
(terraform-live/data-governance/data/README.md, terraform-modules/consumer-data/README.md),
and a second copy of a policy is a copy that goes stale. `ACTIONS` is a count; a trailing
`!` marks a `NotAction`, which is a count of what is EXCLUDED.

""")
        with_policy = [b for b in buckets if b.statements]
        if with_policy:
            for b in with_policy:
                rep.h2(f"{b.profile}  {b.name}")
                rep.tabulate(
                    ["SID\tEFFECT\tPRINCIPAL\tACTIONS\tCONDITION KEYS\tOPEN"]
                    + ["\t".join(s) for s in b.statements],
                    indent="  ",
                )
        else:
            rep.line("(no bucket in this reading carries a bucket policy)")

        # =====================================================================================
        rep.h1("5. Durability - versioning, lifecycle, lock, replication, logging, events")

        rep.text("""$ aws --profile <profile> s3api get-bucket-versioning                --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-lifecycle-configuration   --bucket <bucket>
$ aws --profile <profile> s3api get-object-lock-configuration        --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-replication               --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-logging                   --bucket <bucket>
$ aws --profile <profile> s3api get-bucket-notification-configuration --bucket <bucket>

WHAT SURVIVES, WHAT EXPIRES, AND WHAT LEAVES ON ITS OWN. Versioning and Object Lock
decide what an overwrite or a delete costs; lifecycle decides what disappears without
anybody deciding again; replication and notifications are the two ways an object moves
out of a bucket with NO NETWORK IN THE PATH - no VPC endpoint policy, no DNS allow-list,
no SCP on a reader is anywhere near either of them.

`MFA DELETE` can only ever be set by the bucket's root user, so `-` is the expected
reading everywhere in this design (root is break-glass only).

""")
        if buckets:
            rep.tabulate(
                [
                    "PROFILE\tBUCKET\tVERSIONING\tMFA DEL\tLIFECYCLE\tOBJ LOCK\t"
                    "REPLICATION\tACCESS LOGGING\tEVENTS"
                ]
                + [
                    f"{b.profile}\t{b.name}\t{b.versioning}\t{b.mfa_delete}\t{b.lifecycle}\t"
                    f"{b.lock}\t{b.replication}\t{b.logging}\t{b.notify}"
                    for b in buckets
                ]
            )
        else:
            rep.line("(no bucket measured)")

        rep.text("""
REPLICATION DESTINATIONS, IN FULL. Nothing here is judged: whether a destination is
inside the organization is not derivable from a bucket ARN, so every rule is printed
and read by hand.

""")
        repl_rows = [t for b in buckets for t in b.repl_targets]
        if repl_rows:
            rep.tabulate(
                ["PROFILE\tSOURCE BUCKET\tRULE\tSTATUS\tDESTINATION\tDEST ACCOUNT"]
                + ["\t".join(r) for r in repl_rows]
            )
        else:
            rep.line("None. No bucket in this reading replicates anywhere.")

        # =====================================================================================
        rep.h1("6. What is actually stored")

        rep.text("""$ aws --profile <profile> cloudwatch list-metrics --namespace AWS/S3 \\
      --metric-name BucketSizeBytes
$ aws --profile <profile> cloudwatch get-metric-statistics --namespace AWS/S3 \\
      --metric-name BucketSizeBytes --dimensions Name=BucketName,Value=<bucket> \\
      Name=StorageType,Value=<class> --period 86400 --statistics Average

A SCALE READING, NOT AN INVENTORY, and free: S3 publishes these two metrics once a day
at no charge, and this file never lists an object. Three consequences worth knowing
before a number here is used as evidence: a bucket filled today still reads `-`, a
bucket emptied today still reads its old size, and `STORAGE CLASSES` is the set of
classes S3 has ever published a metric for - which is how a lifecycle transition
that already happened becomes visible.

""")
        if buckets:
            rep.tabulate(
                ["PROFILE\tBUCKET\tOBJECTS\tSIZE\tSTORAGE CLASSES"]
                + [f"{b.profile}\t{b.name}\t{b.objects}\t{b.size}\t{b.classes}" for b in buckets]
            )
        else:
            rep.line("(no bucket measured)")

        # =====================================================================================
        rep.h1("7. The surfaces `list-buckets` does not show")

        rep.text("""FOUR NAMESPACES THAT HOLD DATA AND ARE NOT GENERAL-PURPOSE BUCKETS. Every one of them
is asked for BY NAME, because none appears in section 2 and none is covered by any
other file in aws/:

  - DIRECTORY BUCKETS (S3 Express One Zone). `list-buckets` documents that it does not
    return them; they are a different endpoint, a different naming scheme, and one AZ.
  - TABLE BUCKETS (S3 Tables). `S3TableCatalog` is one of the eleven blueprint
    configurations enabled per member account (docs/SMUS.md), so a project can create
    one without anybody writing Terraform - a managed Iceberg store beside the governed
    lake, which is Lesson 1's shape if data lands in it.
  - ACCESS POINTS. Each carries its OWN policy and its own Block Public Access, so a
    bucket that reads 4/4 in section 4 can still be reachable through one. `NETWORK
    ORIGIN` says `Internet` or `VPC`.
  - MULTI-REGION ACCESS POINTS. A global endpoint in front of buckets in several
    Regions; the alias is a name that resolves worldwide.

Storage Lens is listed too - it is not storage, but its configurations can export a
daily manifest INTO a bucket, which is another writer nobody remembers.

""")
        rep.h2("account-level Block Public Access")
        rep.text("""Reported, not checked: `account-bpa.py` owns this setting and is read three times per
its own schedule. It is here because the bucket flag in section 4 and this one are
different controls, and a bucket reading 3/4 may still be covered by a 4/4 here.

""")
        rep.tabulate(
            ["PROFILE\tACCOUNT BPA"]
            + [f"{c.profile}\t{account_bpa.get(c.profile, '-')}" for c in live]
        )

        rep.h2("directory buckets (S3 Express One Zone)")
        if dir_buckets:
            rep.tabulate(["PROFILE\tBUCKET\tCREATED"] + ["\t".join(r) for r in dir_buckets])
        else:
            rep.line("None in any measured account.")

        rep.h2("table buckets (S3 Tables)")
        if table_buckets:
            rep.tabulate(["PROFILE\tNAME\tARN\tCREATED"] + ["\t".join(r) for r in table_buckets])
        else:
            rep.line("None in any measured account.")

        rep.h2("access points")
        if access_points:
            rep.tabulate(
                ["PROFILE\tNAME\tBUCKET\tNETWORK ORIGIN"] + ["\t".join(r) for r in access_points]
            )
        else:
            rep.line("None in any measured account.")

        rep.h2("multi-region access points")
        if mraps:
            rep.tabulate(["PROFILE\tNAME\tALIAS\tSTATUS"] + ["\t".join(r) for r in mraps])
        else:
            rep.line("None in any measured account.")

        rep.h2("S3 Storage Lens configurations")
        if storage_lens:
            rep.tabulate(
                ["PROFILE\tID\tHOME REGION\tENABLED"] + ["\t".join(r) for r in storage_lens]
            )
        else:
            rep.line("None beyond the default dashboard, which has no configuration object.")

        # =====================================================================================
        rep.h1("8. Tags - which buckets somebody declared, and which somebody left")

        rep.text("""$ aws --profile <profile> s3api get-bucket-tagging --bucket <bucket>

READ AS PROVENANCE, NEVER AS A CONTROL. A tag is how a bucket says which slice made it
and what it is for, and that is worth reading. It is not worth writing a rule over:
an attribute assigned to DESCRIBE becomes a SELECTOR the moment a policy references it,
and then inherits every resource wearing it for an unrelated reason (Lesson 29).

""")
        if buckets:
            rep.tabulate(
                ["PROFILE\tBUCKET\tTAGS"] + [f"{b.profile}\t{b.name}\t{b.tags}" for b in buckets]
            )
        else:
            rep.line("(no bucket measured)")

        # =====================================================================================
        rep.h1("9. The checks")

        rep.text("""SP-1 Region  SP-2 bucket Block Public Access  SP-3 default encryption
SP-4 ACLs disabled  SP-5 no principal outside the organization  SP-6 no website, no
wildcard CORS  SP-7 replication named  SP-8 versioning  SP-9 the other surfaces.

A `note` is a reading that needs a human, not a soft failure: a refused read, a
durability property another file owns, or a surface that merely exists.

""")
        rep.checks_table(checks)
        rep.line()
        rep.line(f"{checks.n_fail()} check(s) FAILED.")

        # =====================================================================================
        rep.h1("10. The accounts and objects nothing here is measuring")

        rep.text("""Read this BEFORE reading section 9 as a pass.

  - MANAGEMENT, LOG ARCHIVE and AUDIT hold NO CLI profile, by design (guiding
    principle 1; docs/ORGANIZATION.md), and they are invisible here. This matters more
    for S3 than anywhere else: LOG ARCHIVE is where the CloudTrail bucket lives, so
    INV-14's Object Lock on it is NOT measured by this file and must not be read out of
    section 5. Run this script with `-` inside CloudShell in each of them, as
    `AWS Control Tower Admin`, to reach them.
  - `Staging` is UNVENDED, held on the account cap (Stage 1a), and every Sandbox beyond
    the first has no profile until Stage 14 vends it (D35). Absent, not reassuring.
  - EXC-01, the SUSPENDED `Sandbox` at the organization root, is not this project's and
    has no profile. It belongs in no list here.
  - THE FOUR PERSONA SESSIONS are deliberately outside the default profile list - they
    belong to different people (aws/AWS-CLI.md). What a persona can actually READ in
    these buckets is the INTERSECTION of its identity policy, the SCP above it, the
    bucket policy in section 4 and, for the lake, Lake Formation (Lesson 28). Nothing
    in this file answers it.
  - THIS IS CONFIGURATION, NEVER CONTENT. No object was listed or read. Section 6 is
    CloudWatch's daily metric and nothing else.
  - GLACIER VAULTS, EFS, EBS SNAPSHOTS and every other persistence surface outside S3
    are out of scope by name. EFS is measured by datalake.py (DL-10), which reads its
    ABSENCE - the NFS requirement was withdrawn 2026-08-17.""")

        # =====================================================================================
        rep.h1("11. Calls that failed, and reads this identity was refused")

        rep.h2("calls that failed")
        rep.text("""A call that should always work and did not: the preflight, a listing, the alias read.
This is what sets exit 1.

""")
        if errors:
            rep.line(errors.text())
        else:
            rep.line("None. Every call in this section returned successfully.")

        rep.h2("reads this identity was refused")
        rep.text("""A DIFFERENT THING, AND NOT AN ERROR. These are per-resource reads that came back
denied rather than empty - a permission ceiling being measured, which is why they set
no exit code and why the cell above says `DENIED` instead of looking like `none`.
Read the WORDING, never the exit code: `AccessDenied ... explicit deny in a service
control policy` and a plain `AccessDenied` are two different findings.

""")
        if refused:
            rep.tabulate(
                ["PROFILE\tSUBJECT\tCALL\tWORDING"]
                + [f"{p}\t{s}\t{c}\t{w}" for p, s, c, w in refused]
            )
        else:
            rep.line("None. Every per-resource read this file attempted was answered.")

        rep.line()
        rep.line("Regenerate with:  ./aws/s3-persistence.py")

    # --------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    note(f"{len(buckets)} bucket(s) across {len(live)} account(s); {len(refused)} refused read(s)")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 11)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 9)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
