#!/usr/bin/env -S uv run --quiet
# observability.py - Stage 12's instrument: the facts the stage keeps true, read per account side
# by side. Every one of them is describe-shaped (step 10), so every check reads configuration:
#
#   OB-1  every log group this project creates carries an explicit retention (step 3.1). A group
#         is this project's when it carries the Project tag every slice's default_tags stamps, or
#         when its name is in the project's namespace (/awsds/, awsds-). The rest are the
#         services' own; the ones that never expire are a note, the decision EXC-10 records.
#   OB-2  the organization trail's bucket expires no version sooner than 90 days, nor sooner than
#         its Object Lock retention (step 3.2, INV-14). The bucket's name is read off the trail.
#   OB-3  every alarm has a notification target that resolves (step 2): an SNS topic of this
#         account and Region with a confirmed subscription, a policy that admits CloudWatch, and
#         no key CloudWatch cannot encrypt under.
#   OB-4  an AWS Backup plan covers every volume of every [D] instance (step 8). The [D] rows are
#         read from scripts/tfhygiene/layers.py, never listed here (Lesson 14).
#   OB-5  each quota of step 9.1 is under 80 % of its limit.
#
# Steps 2 and 8 are not built. OB-3 reads `note` until some alarm measured carries an SNS action,
# and OB-4 until the [D] rows' account holds a backup plan; from then on an alarm that notifies
# nobody, or a volume no plan covers, is a `fail`, so a half-built step is loud (Lesson 50).
#
#   needs:    a live SSO session as the infrastructure user, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/observability.py                     # every awsds-infra-* profile
#             ./aws/observability.py awsds-infra-prod    # only the ones named
#             python3 aws/observability.py -             # CloudShell, ambient credentials
#   writes:   aws/output/observability.txt   (untracked - see .gitignore)
#   reads:    logs:DescribeLogGroups, ListTagsForResource; cloudtrail:DescribeTrails;
#             s3:GetBucketVersioning, GetBucketObjectLockConfiguration, GetLifecycleConfiguration
#             (in the bucket's own account only); cloudwatch:DescribeAlarms;
#             sns:GetTopicAttributes; kms:DescribeKey, GetKeyPolicy; ec2:DescribeInstances,
#             DescribeVolumes, DescribeAddresses, DescribeVpcs, DescribeVpcEndpoints;
#             backup:ListBackupPlans, GetBackupPlan, ListBackupSelections, GetBackupSelection,
#             DescribeRegionSettings; dlm:GetLifecyclePolicies, GetLifecyclePolicy;
#             route53:GetAccountLimit; servicequotas:GetServiceQuota, GetAWSDefaultServiceQuota,
#             ListServiceQuotas, ListAWSDefaultServiceQuotas; sagemaker:ListProcessingJobs,
#             ListTrainingJobs, ListTransformJobs, ListEndpoints, ListApps and the Describe call of
#             each running job and endpoint; sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - The CloudTrail bucket is Log Archive's, which holds no CLI profile (D33/D34). OB-2 is
#     decided by the `-` run in Log Archive's CloudShell, as AWS Control Tower Admin; a laptop
#     run reads the trail's bucket name and notes where it lives.
#   - Management holds the budgets step 2.1 alarms and the AWS Backup opt-in that a plan an
#     Organizations backup policy makes follows, outside every profile here.
#   - An alarm wired and never fired, and a backup never restored, are configurations: the proofs
#     are steps 2.4 and 8.4.
#   - OB-5 counts what runs now. With the environment down the counts are near zero, and the
#     reading that matters is taken with it up (step 9.1).

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, is_ambient
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "observability.txt"

# The infrastructure user's own reach, s3-persistence.py's default for its reason: the persona
# sessions belong to other people. Policy Canary is left out too, since no slice applies there and
# nothing this project creates lives in it.
INFRA_PREFIX = "awsds-infra-"

# OB-1's two marks of a group this project created: the tag every slice's provider stamps through
# default_tags (conventions 6), and the project's own namespace.
PROJECT_TAG_KEY = "Project"
PROJECT_TAG_VALUE = "AWS-DataScience"
PROJECT_PREFIXES = ("/awsds/", "awsds-")

# OB-2. The landing zone's organization trail, whose S3BucketName is the one source of the
# bucket's name that cannot be stale (INV-14), and the floor below which the landing zone's own
# expirations would fail against locked versions: the Object Lock default, COMPLIANCE / 90 days.
ORG_TRAIL = "aws-controltower-BaselineCloudTrail"
LIFECYCLE_FLOOR_DAYS = 90
BUCKET_ACCOUNT_RE = re.compile(r"-(\d{12})(?:-|$)")

# OB-4. The [D] rows, and the two vocabularies a host's Name tag and its profile are built from,
# read as text: aws/ imports nothing from scripts/, or the CloudShell fallback dies.
LAYERS_FILE = ("scripts", "tfhygiene", "layers.py")
BACKEND_FILE = ("scripts", "tfhygiene", "backend.py")
# The id prefix of a plan an Organizations backup policy made, as a member account lists it (a
# re:Post reading, REFERENCES.md). Such a plan follows the management account's resource opt-in,
# not the member's (AWS Backup's cross-account page), and no profile here reads Management's.
ORGANIZATIONS_PLAN_PREFIX = "orgs/"

# OB-5. Step 9.1's quotas with a fixed code: (label, service code, quota code, words its own name
# carries). The name is read back and compared, so a wrong code reads as a note rather than as a
# limit (Lesson 38).
EIP_QUOTA = ("Elastic IPs", "ec2", "L-0263D0A3", "elastic ip")
INTERFACE_ENDPOINT_QUOTA = ("interface endpoints", "vpc", "L-29B6F2EB", "endpoints per vpc")
GATEWAY_ENDPOINT_QUOTA = ("gateway endpoints", "vpc", "L-1B52E74A", "gateway vpc endpoints")
THRESHOLD = 0.8

# The SageMaker usage quotas, by the names Service Quotas gives them ("ml.m5.large for endpoint
# usage"). A Studio app's quota is found by its words instead: its name is not fixed here.
SAGEMAKER_QUOTA_NAMES = {
    "processing": "{} for processing job usage",
    "training": "{} for training job usage",
    "transform": "{} for transform job usage",
    "endpoint": "{} for endpoint usage",
}
STUDIO_APP_WORDS = {
    "JupyterLab": ("jupyterlab",),
    "CodeEditor": ("codeeditor", "code editor"),
    "KernelGateway": ("kernelgateway", "kernel gateway"),
}
ENDPOINT_GONE = ("OutOfService", "Failed", "Deleting")
ENDPOINT_TYPES_PER_VPC = ("Interface", "GatewayLoadBalancer")
ENDPOINT_GONE_STATES = ("deleted", "deleting", "failed", "rejected", "expired")


# ------------------------------------------------------------------------------- the reads


@dataclass
class Answer:
    """One call's parsed answer."""

    doc: dict
    ok: bool  # False: the call failed, and the failure is in the error log
    absent: bool = False  # True: the error said the thing asked about does not exist


class Reader:
    """One account's reads: the CLI bound to its profile, every failure into the shared log."""

    def __init__(self, caller: profiles.Caller, errors: ErrorLog) -> None:
        self.label = "- (ambient)" if is_ambient(caller.profile) else caller.profile
        self.account = caller.account or "-"
        self.errors = errors
        self.cli = AwsCli(
            profile=caller.profile, region=context.REGION, errors=errors, echo_profile=True
        )

    def json(self, *args: str, absent: str | None = None) -> Answer:
        """``aws <args> --output json``; ``absent`` is the error text that means "none exists"."""
        res = self.cli.run(*args, "--output", "json", log=False, tolerate=absent)
        if res.tolerated:
            return Answer({}, True, True)
        if not res.ok:
            self.errors.add(args, res.merged, self.label)
            return Answer({}, False)
        try:
            doc = json.loads(res.stdout or "{}")
        except json.JSONDecodeError:
            self.errors.add(args, f"the answer is not JSON: {res.stdout[:120]}", self.label)
            return Answer({}, False)
        return Answer(doc if isinstance(doc, dict) else {}, True)


def as_list(value) -> list:
    """A policy field as a list: one string, a list, or nothing."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def statements(document: dict) -> list:
    """The statements of a policy document."""
    return [s for s in as_list((document or {}).get("Statement")) if isinstance(s, dict)]


def covers(actions: list, wanted: str) -> bool:
    """Whether an action list names ``wanted``: exactly, by a trailing wildcard, or by ``*``."""
    wanted = wanted.lower()
    for action in actions:
        action = str(action).lower()
        if action == wanted or action == "*":
            return True
        if action.endswith("*") and wanted.startswith(action[:-1]):
            return True
    return False


def admits_service(statement: dict, service: str, account: str) -> bool:
    """Whether a statement's principal takes ``service``, and no source condition names another
    account. The shape of the statement, not an IAM evaluation."""
    principal = statement.get("Principal")
    if principal == "*":
        taken = True
    elif isinstance(principal, dict):
        services = as_list(principal.get("Service"))
        taken = service in services or "*" in as_list(principal.get("AWS"))
    else:
        taken = False
    if not taken:
        return False
    for pairs in (statement.get("Condition") or {}).values():
        for key, values in (pairs or {}).items():
            if key.lower() not in ("aws:sourceowner", "aws:sourceaccount"):
                continue
            if account not in [str(v) for v in as_list(values)]:
                return False
    return True


def parse_policy(text: str | None) -> dict:
    """A policy document held as a JSON string, or {} when it is absent or unparseable."""
    try:
        document = json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}
    return document if isinstance(document, dict) else {}


def tag_map(tags: list | None) -> dict:
    """EC2's [{Key, Value}] as a dict."""
    return {t.get("Key", ""): t.get("Value", "") for t in tags or []}


def count(n: int, noun: str) -> str:
    """``n`` and the noun, plural unless n is 1: 1 group, 3 groups."""
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def quota_text(value) -> str:
    """A quota value as the console prints it: 5, not 5.0."""
    return "-" if value is None else f"{value:g}"


# ------------------------------------------------------------------------------- OB-1


@dataclass
class LogGroup:
    name: str
    retention: int | None  # days; None when the group never expires
    stored_mb: float
    owner: str  # project | service | unread
    why: str  # how the owner was decided


def read_log_groups(reader: Reader) -> list | None:
    """Every log group of the account with its owner, or None when the listing failed."""
    listing = reader.json("logs", "describe-log-groups")
    if not listing.ok:
        return None
    groups = []
    for g in listing.doc.get("logGroups", []):
        name = g.get("logGroupName", "-")
        retention = g.get("retentionInDays")
        stored_mb = (g.get("storedBytes") or 0) / 1e6
        if name.startswith(PROJECT_PREFIXES):
            groups.append(LogGroup(name, retention, stored_mb, "project", "name"))
            continue
        # The tag answers for a group a slice declares under a service's own name (production's
        # /aws/sagemaker/ProcessingJobs); a group the service created carries none.
        arn = g.get("logGroupArn") or (g.get("arn") or "").removesuffix(":*")
        tags = reader.json("logs", "list-tags-for-resource", "--resource-arn", arn)
        if not tags.ok:
            groups.append(LogGroup(name, retention, stored_mb, "unread", "tags unread"))
        elif (tags.doc.get("tags") or {}).get(PROJECT_TAG_KEY) == PROJECT_TAG_VALUE:
            groups.append(LogGroup(name, retention, stored_mb, "project", "tag"))
        else:
            groups.append(LogGroup(name, retention, stored_mb, "service", "no tag"))
    return groups


def judge_log_groups(checks: Checks, label: str, groups: list | None) -> None:
    what = f"log retention in {label}"
    if groups is None:
        checks.fail(
            "OB-1",
            what,
            "the log group listing failed (section 9): a failed read is not an expected "
            "absence (Lesson 13).",
        )
        return
    ours = [g for g in groups if g.owner == "project"]
    forever = [g.name for g in ours if g.retention is None]
    unclassified = [g.name for g in groups if g.owner == "unread" and g.retention is None]
    if forever or unclassified:
        parts = []
        if forever:
            parts.append(f"groups of this project that never expire: {', '.join(forever)}")
        if unclassified:
            parts.append(
                f"never-expiring groups left unclassified, their tags unread: "
                f"{', '.join(unclassified)}"
            )
        checks.fail(
            "OB-1",
            what,
            "; ".join(parts) + ". Step 3.1 sets a retention on every group the project creates.",
        )
    elif ours:
        days = sorted(g.retention for g in ours)
        span = f"{days[0]}" if days[0] == days[-1] else f"{days[0]} to {days[-1]}"
        checks.ok(
            "OB-1",
            what,
            f"every group of this project has a retention, {span} days "
            f"({count(len(ours), 'group')})",
        )
    else:
        checks.ok("OB-1", what, "no group of this project in this account")
    services = [g for g in groups if g.owner == "service" and g.retention is None]
    if services:
        stored = sum(g.stored_mb for g in services)
        checks.note(
            "OB-1",
            f"service groups in {label}",
            f"{count(len(services), 'group')} no slice declares, never expiring, "
            f"{stored:.1f} MB: the services' own (EXC-10 records Sandbox's), a decision rather "
            "than this check.",
        )


# ------------------------------------------------------------------------------- OB-2


@dataclass
class TrailReading:
    label: str
    found: bool  # whether ORG_TRAIL is in this account's listing
    bucket: str = "-"
    prefix: str = "-"
    organization: str = "-"
    home: str = "-"
    owner: str = "-"  # the account id inside the bucket's name
    read_here: bool = False  # whether this account owns the bucket and read it
    complete: bool = True  # False when a read of the bucket failed
    versioning: str = "-"
    lock: dict | None = None  # ObjectLockConfiguration; None when absent or unread
    rules: list | None = None  # the lifecycle rules; None when unread
    lifecycle_absent: bool = False


def read_trail(reader: Reader) -> TrailReading | None:
    """The organization trail as this account sees it, and its bucket where this account owns
    it; None when the trail listing failed."""
    listing = reader.json("cloudtrail", "describe-trails")
    if not listing.ok:
        return None
    trail = None
    for t in listing.doc.get("trailList", []):
        if t.get("Name") == ORG_TRAIL:
            trail = t
    if trail is None:
        return TrailReading(reader.label, False)
    bucket = trail.get("S3BucketName") or "-"
    match = BUCKET_ACCOUNT_RE.search(bucket)
    reading = TrailReading(
        reader.label,
        True,
        bucket=bucket,
        prefix=trail.get("S3KeyPrefix") or "-",
        organization=str(trail.get("IsOrganizationTrail", "-")),
        home=trail.get("HomeRegion") or "-",
        owner=match.group(1) if match else "-",
    )
    # Another account's bucket refuses these reads by its policy: no call is made for it.
    if reading.owner != reader.account:
        return reading
    reading.read_here = True
    versioning = reader.json("s3api", "get-bucket-versioning", "--bucket", bucket)
    lock = reader.json(
        "s3api",
        "get-object-lock-configuration",
        "--bucket",
        bucket,
        absent="ObjectLockConfigurationNotFoundError",
    )
    lifecycle = reader.json(
        "s3api",
        "get-bucket-lifecycle-configuration",
        "--bucket",
        bucket,
        absent="NoSuchLifecycleConfiguration",
    )
    reading.complete = versioning.ok and lock.ok and lifecycle.ok
    reading.versioning = versioning.doc.get("Status", "never enabled") if versioning.ok else "-"
    if lock.ok and not lock.absent:
        reading.lock = lock.doc.get("ObjectLockConfiguration")
    if lifecycle.ok:
        reading.rules = lifecycle.doc.get("Rules", [])
        reading.lifecycle_absent = lifecycle.absent
    return reading


def lock_retention(lock: dict | None) -> tuple:
    """(mode, days) of an Object Lock default retention, or (None, None) when there is none."""
    if not lock or lock.get("ObjectLockEnabled") != "Enabled":
        return None, None
    retention = (lock.get("Rule") or {}).get("DefaultRetention") or {}
    if "Days" in retention:
        return retention.get("Mode"), retention["Days"]
    if "Years" in retention:
        return retention.get("Mode"), retention["Years"] * 365
    return retention.get("Mode"), None


def short_expirations(rules: list, floor: int) -> list:
    """Every enabled rule's expiration that deletes a version sooner than ``floor`` days.

    The noncurrent half is the one that binds under Object Lock, since it deletes versions; the
    current half is held to the same floor because INV-14 couples both to the lock. Every rule
    counts whatever its filter: the lock's default retention binds every object in the bucket.
    """
    short = []
    for rule in rules:
        if rule.get("Status") != "Enabled":
            continue
        rule_id = rule.get("ID") or "(no ID)"
        current = rule.get("Expiration") or {}
        if "Date" in current:
            short.append(f"{rule_id} expires current versions on a date, {current['Date']}")
        if current.get("Days") is not None and current["Days"] < floor:
            short.append(f"{rule_id} expires current versions at {current['Days']} days")
        noncurrent = (rule.get("NoncurrentVersionExpiration") or {}).get("NoncurrentDays")
        if noncurrent is not None and noncurrent < floor:
            short.append(f"{rule_id} expires noncurrent versions at {noncurrent} days")
    return short


def lifecycle_summary(rules: list | None) -> str:
    """The enabled rules' expirations in one phrase, for the report."""
    if rules is None:
        return "unread"
    parts = []
    for rule in rules:
        current = (rule.get("Expiration") or {}).get("Days", "-")
        noncurrent = (rule.get("NoncurrentVersionExpiration") or {}).get("NoncurrentDays", "-")
        parts.append(
            f"{rule.get('ID') or '(no ID)'} {rule.get('Status', '-')}: current {current} d, "
            f"noncurrent {noncurrent} d"
        )
    return "; ".join(parts) or "no rule"


def judge_trail(checks: Checks, readings: list) -> None:
    what = "CloudTrail bucket lifecycle"
    listed = [r for r in readings if r is not None]
    seen = [r for r in listed if r.found]
    owned = [r for r in seen if r.read_here]
    if not seen:
        checks.fail(
            "OB-2",
            what,
            f"no measured account sees {ORG_TRAIL}, the bucket's only source (INV-14)"
            if listed
            else "the trail listing failed in every account (section 9)",
        )
        return
    if not owned:
        checks.note(
            "OB-2",
            what,
            f"{seen[0].bucket} belongs to another account, Log Archive, which no profile here "
            "reaches: this check is decided by `python3 aws/observability.py -` in Log "
            "Archive's CloudShell, as AWS Control Tower Admin.",
        )
        return
    for r in owned:
        if not r.complete:
            checks.fail("OB-2", what, f"a read of {r.bucket} failed (section 9)")
            continue
        mode, lock_days = lock_retention(r.lock)
        problems = []
        if mode != "COMPLIANCE" or lock_days is None:
            problems.append(
                f"Object Lock reads {mode or 'absent'} / {lock_days or '-'} days where INV-14 "
                "records COMPLIANCE / 90: read INV-14 before anything else"
            )
        floor = max(LIFECYCLE_FLOOR_DAYS, lock_days or 0)
        problems += short_expirations(r.rules or [], floor)
        expiring = [
            rule
            for rule in r.rules or []
            if rule.get("Status") == "Enabled"
            and (rule.get("Expiration") or rule.get("NoncurrentVersionExpiration"))
        ]
        if problems:
            checks.fail(
                "OB-2",
                what,
                "; ".join(problems) + f". The floor is {floor} days, and below the lock it is "
                "unrecoverable (step 3.2).",
            )
        elif not expiring:
            reason = "no lifecycle configuration" if r.lifecycle_absent else "no enabled rule"
            checks.note(
                "OB-2",
                what,
                f"{reason} expires a version: every version is kept forever, which respects the "
                f"{floor}-day floor and is not the RetentionRule INV-14 records.",
            )
        else:
            checks.ok(
                "OB-2",
                what,
                f"every enabled rule expires at {floor} days or later "
                f"({lifecycle_summary(r.rules)}); Object Lock {mode} / {lock_days} days",
            )


# ------------------------------------------------------------------------------- OB-3


@dataclass
class Alarm:
    name: str
    kind: str  # metric | composite
    state: str
    enabled: bool  # ActionsEnabled
    alarm_actions: list
    other_actions: list  # the OK and INSUFFICIENT_DATA actions

    @property
    def sns_alarm_actions(self) -> list:
        return [a for a in self.alarm_actions if ":sns:" in a]

    @property
    def scaling_only(self) -> bool:
        """An alarm a scaling policy owns: it acts, and notifying is not its job."""
        return bool(self.alarm_actions) and all(":autoscaling:" in a for a in self.alarm_actions)

    @property
    def wired(self) -> bool:
        """Whether step 2 reached this alarm: its actions on and an SNS topic among them."""
        return self.enabled and bool(self.sns_alarm_actions)


@dataclass
class Topic:
    arn: str
    verdict: str  # resolves | broken | unread
    why: str
    confirmed: str = "-"
    admits: str = "-"  # the Sid that lets CloudWatch publish
    key: str = "-"


def read_alarms(reader: Reader) -> list | None:
    """Every metric and composite alarm of the account, or None when the listing failed."""
    listing = reader.json(
        "cloudwatch", "describe-alarms", "--alarm-types", "MetricAlarm", "CompositeAlarm"
    )
    if not listing.ok:
        return None
    alarms = []
    for kind, key in (("metric", "MetricAlarms"), ("composite", "CompositeAlarms")):
        for a in listing.doc.get(key, []):
            alarms.append(
                Alarm(
                    a.get("AlarmName", "-"),
                    kind,
                    a.get("StateValue", "-"),
                    bool(a.get("ActionsEnabled", True)),
                    list(a.get("AlarmActions") or []),
                    list(a.get("OKActions") or []) + list(a.get("InsufficientDataActions") or []),
                )
            )
    return alarms


def topic_admits_cloudwatch(policy: dict, account: str) -> str | None:
    """The Sid of a statement that lets CloudWatch publish to the topic, or None."""
    for st in statements(policy):
        if st.get("Effect") != "Allow" or not covers(as_list(st.get("Action")), "sns:Publish"):
            continue
        if admits_service(st, "cloudwatch.amazonaws.com", account):
            return st.get("Sid") or "(no Sid)"
    return None


def key_admits_cloudwatch(policy: dict, account: str) -> bool:
    """Whether a key policy grants CloudWatch both kms:Decrypt and kms:GenerateDataKey*, the two
    calls an alarm's publish to an encrypted topic makes."""
    actions = []
    for st in statements(policy):
        if st.get("Effect") == "Allow" and admits_service(st, "cloudwatch.amazonaws.com", account):
            actions += as_list(st.get("Action"))
    return covers(actions, "kms:Decrypt") and covers(actions, "kms:GenerateDataKey")


def judge_topic_key(reader: Reader, key: str | None) -> tuple:
    """(how the topic is encrypted, why CloudWatch could not publish under it or None)."""
    if not key:
        return "none", None
    described = reader.json("kms", "describe-key", "--key-id", key)
    if not described.ok:
        return key, "its key went unread (section 9)"
    meta = described.doc.get("KeyMetadata") or {}
    if meta.get("KeyManager") == "AWS":
        return (
            f"{key} (AWS managed)",
            "its AWS-managed key admits no service, so CloudWatch's publish fails",
        )
    policy = reader.json(
        "kms", "get-key-policy", "--key-id", meta.get("KeyId") or key, "--policy-name", "default"
    )
    if not policy.ok:
        return f"{key} (customer managed)", "its key policy went unread (section 9)"
    if not key_admits_cloudwatch(parse_policy(policy.doc.get("Policy")), reader.account):
        return (
            f"{key} (customer managed)",
            "its key policy grants CloudWatch no kms:Decrypt and kms:GenerateDataKey*",
        )
    return f"{key} (customer managed)", None


def resolve_topic(reader: Reader, arn: str) -> Topic:
    """Whether an alarm's SNS target would deliver: exists, admits CloudWatch, reaches someone."""
    parts = arn.split(":")
    if len(parts) != 6 or parts[2] != "sns":
        return Topic(arn, "broken", "not an SNS topic ARN")
    if parts[3] != context.REGION:
        return Topic(arn, "broken", f"in {parts[3]}, outside the estate's Region")
    if parts[4] != reader.account:
        return Topic(arn, "unread", "in another account, which this profile does not read")
    got = reader.json("sns", "get-topic-attributes", "--topic-arn", arn, absent="NotFound")
    if got.absent:
        return Topic(arn, "broken", "the topic does not exist")
    if not got.ok:
        return Topic(arn, "broken", "its attributes went unread (section 9)")
    attrs = got.doc.get("Attributes") or {}
    confirmed = attrs.get("SubscriptionsConfirmed") or "0"
    pending = attrs.get("SubscriptionsPending") or "0"
    sid = topic_admits_cloudwatch(parse_policy(attrs.get("Policy")), reader.account)
    key_text, key_problem = judge_topic_key(reader, attrs.get("KmsMasterKeyId"))
    problems = []
    if confirmed == "0":
        problems.append(f"no confirmed subscription ({pending} pending)")
    if sid is None:
        problems.append("its policy admits no CloudWatch publish")
    if key_problem:
        problems.append(key_problem)
    return Topic(
        arn,
        "broken" if problems else "resolves",
        "; ".join(problems) or "-",
        confirmed=f"{confirmed} ({pending} pending)",
        admits=sid or "none",
        key=key_text,
    )


def topic_name(arn: str) -> str:
    return arn.rsplit(":", 1)[-1]


def alarm_verdict(alarm: Alarm, topics: dict) -> tuple:
    """(verdict, why) of one alarm: resolves | broken | unwired | unread | scaling."""
    if alarm.scaling_only:
        return "scaling", "a scaling policy's alarm: it acts, and notifies nobody by design"
    referenced = [a for a in alarm.alarm_actions + alarm.other_actions if ":sns:" in a]
    broken = [topics[a] for a in referenced if topics[a].verdict == "broken"]
    if broken:
        return "broken", "; ".join(f"{topic_name(t.arn)}: {t.why}" for t in broken)
    if not alarm.enabled:
        return "unwired", "its actions are disabled"
    if not alarm.sns_alarm_actions:
        return "unwired", "no SNS topic among its alarm actions"
    unread = [topics[a] for a in referenced if topics[a].verdict == "unread"]
    if unread:
        return "unread", "; ".join(f"{t.arn}: {t.why}" for t in unread)
    return "resolves", ", ".join(topic_name(a) for a in alarm.sns_alarm_actions)


def judge_alarms(
    checks: Checks, label: str, alarms: list | None, verdicts: list, wired_by: str | None
) -> None:
    what = f"alarm targets in {label}"
    if alarms is None:
        checks.fail(
            "OB-3",
            what,
            "the alarm listing failed (section 9): a failed read is not an expected absence "
            "(Lesson 13).",
        )
        return
    judged = [(a, v, why) for a, (v, why) in zip(alarms, verdicts) if v != "scaling"]
    if not judged:
        checks.ok("OB-3", what, "no alarm in this account")
        return
    broken = [f"{a.name} ({why})" for a, v, why in judged if v == "broken"]
    unwired = [a.name for a, v, _ in judged if v == "unwired"]
    unread = [a.name for a, v, _ in judged if v == "unread"]
    if broken:
        checks.fail(
            "OB-3",
            what,
            f"{count(len(broken), 'alarm')} with a target that does not resolve: "
            f"{'; '.join(broken)}",
        )
    if unwired and wired_by:
        checks.fail(
            "OB-3",
            what,
            f"{count(len(unwired), 'alarm')} notifying nobody ({', '.join(unwired)}) while "
            f"{wired_by} notifies: step 2 is half-built.",
        )
    elif unwired:
        checks.note(
            "OB-3",
            what,
            f"{count(len(unwired), 'alarm')} notifying nobody ({', '.join(unwired)}): step 2 is "
            "not built, and no alarm measured carries an SNS action.",
        )
    if unread:
        checks.note(
            "OB-3",
            what,
            f"{count(len(unread), 'alarm')} notifying a topic in another account, unread here: "
            f"{', '.join(unread)}",
        )
    if not (broken or unwired or unread):
        checks.ok(
            "OB-3",
            what,
            f"every alarm notifies a topic that resolves ({count(len(judged), 'alarm')})",
        )


# ------------------------------------------------------------------------------- OB-4


def module_tree(path: Path):
    """The parsed module, or None when the file is absent or does not parse."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def assigned_node(tree, name: str):
    """The value node of a module-level ``name = ...``, or None."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return node.value
    return None


def assigned_literal(tree, name: str):
    """The literal a module-level ``name`` is assigned, or None when it is not a literal."""
    node = assigned_node(tree, name)
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except ValueError:
        return None


def dormant_slices(tree) -> list | None:
    """(account folder, slice) of every row of layers.SLICES whose layer is DORMANT, in table
    order; None when the table is not where it was."""
    table = assigned_node(tree, "SLICES")
    dormant = assigned_literal(tree, "DORMANT")
    if not isinstance(table, ast.List) or dormant is None:
        return None
    rows = []
    for row in table.elts:
        if not (isinstance(row, ast.Call) and getattr(row.func, "id", None) == "Slice"):
            continue
        fields = dict(zip(("account", "name", "layer"), row.args))
        for keyword in row.keywords:
            fields[keyword.arg] = keyword.value
        layer = fields.get("layer")
        named = isinstance(layer, ast.Name) and layer.id == "DORMANT"
        spelled = isinstance(layer, ast.Constant) and layer.value == dormant
        account, name = fields.get("account"), fields.get("name")
        if (
            (named or spelled)
            and isinstance(account, ast.Constant)
            and isinstance(name, ast.Constant)
        ):
            rows.append((account.value, name.value))
    return rows


@dataclass
class DormantRow:
    """One [D] slice and the host OB-4 looks for."""

    account: str  # the terraform-live/ folder
    slice: str
    host: str  # the Name tag, slices.py instance_name's rule
    profile: str  # backend.PROFILES' profile for the account folder


def read_dormant_rows(repo_root: Path) -> tuple:
    """([DormantRow], why the table is missing or ''). The Name tag follows slices.py
    instance_name: DORMANT_HOST_NAMES, else awsds-<env token>-<slice>."""
    layers = module_tree(repo_root.joinpath(*LAYERS_FILE))
    backend = module_tree(repo_root.joinpath(*BACKEND_FILE))
    if layers is None or backend is None:
        return [], f"{'/'.join(LAYERS_FILE)} or {'/'.join(BACKEND_FILE)} is not here"
    slices = dormant_slices(layers)
    overrides = assigned_literal(layers, "DORMANT_HOST_NAMES")
    tokens = assigned_literal(backend, "ENV_TOKENS")
    profile_map = assigned_literal(backend, "PROFILES")
    if slices is None or not isinstance(tokens, dict) or not isinstance(profile_map, dict):
        return [], "SLICES, DORMANT, ENV_TOKENS or PROFILES is not a literal where it was"
    rows = []
    for account, name in slices:
        host = (overrides or {}).get(
            (account, name)
        ) or f"awsds-{tokens.get(account, account)}-{name}"
        rows.append(DormantRow(account, name, host, profile_map.get(account, "-")))
    return rows, ""


@dataclass
class Volume:
    volume_id: str
    size: str
    device: str
    tags: dict
    backup: list = field(default_factory=list)  # the selections that cover it
    dlm: list = field(default_factory=list)  # the DLM policies that snapshot it


@dataclass
class Host:
    instance_id: str
    state: str
    tags: dict
    volumes: list  # [Volume]


@dataclass
class BackupState:
    """An account's AWS Backup plans, selections and resource-type opt-in, and its DLM policies."""

    complete: bool = True
    plans: list = field(default_factory=list)  # [(plan name, plan id, rules text, [selection])]
    opt_in: dict = field(default_factory=dict)
    dlm: list = field(default_factory=list)  # [(policy id, state, resource types, target tags)]


def read_backup_state(reader: Reader) -> BackupState:
    state = BackupState()
    listing = reader.json("backup", "list-backup-plans")
    state.complete = listing.ok
    for plan in listing.doc.get("BackupPlansList", []):
        plan_id = plan.get("BackupPlanId", "-")
        detail = reader.json("backup", "get-backup-plan", "--backup-plan-id", plan_id)
        rules = []
        for rule in (detail.doc.get("BackupPlan") or {}).get("Rules", []):
            rules.append(
                f"{rule.get('RuleName', '-')} {rule.get('ScheduleExpression', '-')} -> "
                f"{rule.get('TargetBackupVaultName', '-')}"
            )
        listed = reader.json("backup", "list-backup-selections", "--backup-plan-id", plan_id)
        selections = []
        for summary in listed.doc.get("BackupSelectionsList", []):
            one = reader.json(
                "backup",
                "get-backup-selection",
                "--backup-plan-id",
                plan_id,
                "--selection-id",
                summary.get("SelectionId", "-"),
            )
            state.complete = state.complete and one.ok
            if one.ok:
                selections.append(one.doc.get("BackupSelection") or {})
        state.complete = state.complete and detail.ok and listed.ok
        state.plans.append((plan.get("BackupPlanName", "-"), plan_id, "; ".join(rules), selections))
    settings = reader.json("backup", "describe-region-settings")
    state.complete = state.complete and settings.ok
    state.opt_in = settings.doc.get("ResourceTypeOptInPreference") or {}
    policies = reader.json("dlm", "get-lifecycle-policies")
    state.complete = state.complete and policies.ok
    for summary in policies.doc.get("Policies", []):
        policy_id = summary.get("PolicyId", "-")
        one = reader.json("dlm", "get-lifecycle-policy", "--policy-id", policy_id)
        state.complete = state.complete and one.ok
        details = (one.doc.get("Policy") or {}).get("PolicyDetails") or {}
        state.dlm.append(
            (
                policy_id,
                summary.get("State", "-"),
                details.get("ResourceTypes") or [],
                tag_map(details.get("TargetTags")),
            )
        )
    return state


def wildcard(pattern: str, value: str) -> bool:
    """AWS Backup's wildcard: ``*`` matches any run of characters, and nothing else is special."""
    regex = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.fullmatch(regex, value) is not None


def condition_key(key: str) -> str:
    """A selection's tag key without the ``aws:ResourceTag/`` the Conditions form carries."""
    return key.split("/", 1)[1] if key.startswith("aws:ResourceTag/") else key


def selects(selection: dict, arn: str, tags: dict) -> bool:
    """Whether a backup selection takes the resource: (Resources or ListOfTags) and every
    condition, less NotResources. A selection naming neither Resources nor ListOfTags is read as
    taking nothing."""
    by_arn = any(wildcard(p, arn) for p in selection.get("Resources") or [])
    by_tag = False
    for c in selection.get("ListOfTags") or []:
        if tags.get(condition_key(c.get("ConditionKey", ""))) == c.get("ConditionValue"):
            by_tag = True
    if not (by_arn or by_tag):
        return False
    conditions = selection.get("Conditions") or {}
    for c in conditions.get("StringEquals") or []:
        if tags.get(condition_key(c.get("ConditionKey", ""))) != c.get("ConditionValue"):
            return False
    for c in conditions.get("StringNotEquals") or []:
        if tags.get(condition_key(c.get("ConditionKey", ""))) == c.get("ConditionValue"):
            return False
    for c in conditions.get("StringLike") or []:
        value = tags.get(condition_key(c.get("ConditionKey", "")))
        if value is None or not wildcard(c.get("ConditionValue", ""), value):
            return False
    for c in conditions.get("StringNotLike") or []:
        value = tags.get(condition_key(c.get("ConditionKey", "")))
        if value is not None and wildcard(c.get("ConditionValue", ""), value):
            return False
    return not any(wildcard(p, arn) for p in selection.get("NotResources") or [])


def read_hosts(reader: Reader, name: str) -> list | None:
    """The live instances carrying Name=``name``, each with its volumes; None when a read
    failed."""
    found = reader.json("ec2", "describe-instances", "--filters", f"Name=tag:Name,Values={name}")
    if not found.ok:
        return None
    hosts = []
    for reservation in found.doc.get("Reservations", []):
        for i in reservation.get("Instances", []):
            state = (i.get("State") or {}).get("Name", "-")
            if state in ("terminated", "shutting-down"):
                continue
            devices = {}
            for m in i.get("BlockDeviceMappings", []):
                if "Ebs" in m:
                    devices[m["Ebs"].get("VolumeId", "-")] = m.get("DeviceName", "-")
            volumes = []
            if devices:
                described = reader.json("ec2", "describe-volumes", "--volume-ids", *devices)
                if not described.ok:
                    return None
                for v in described.doc.get("Volumes", []):
                    volume_id = v.get("VolumeId", "-")
                    volumes.append(
                        Volume(
                            volume_id,
                            f"{v.get('Size', '-')} GiB {v.get('VolumeType', '-')}",
                            devices.get(volume_id, "-"),
                            tag_map(v.get("Tags")),
                        )
                    )
            hosts.append(Host(i.get("InstanceId", "-"), state, tag_map(i.get("Tags")), volumes))
    return hosts


def cover(hosts: list, state: BackupState, account: str) -> None:
    """Fill each volume's covering selections and DLM policies.

    A volume is covered by an AWS Backup selection that takes its own ARN with EBS opted in, or
    its instance's ARN with EC2 opted in, since an EC2 backup images every attached volume. The
    opt-in is this account's, except for a plan an Organizations backup policy made: that one
    follows Management's, unread here, so its selection alone decides and its label says so.
    """
    for host in hosts:
        instance_arn = f"arn:aws:ec2:{context.REGION}:{account}:instance/{host.instance_id}"
        for volume in host.volumes:
            volume_arn = f"arn:aws:ec2:{context.REGION}:{account}:volume/{volume.volume_id}"
            for plan_name, plan_id, _, selections in state.plans:
                by_organizations = plan_id.startswith(ORGANIZATIONS_PLAN_PREFIX)
                ebs = by_organizations or state.opt_in.get("EBS") is True
                ec2 = by_organizations or state.opt_in.get("EC2") is True
                opt_in = ", Management's opt-in" if by_organizations else ""
                for s in selections:
                    label = f"{plan_name}/{s.get('SelectionName', '-')}"
                    if ebs and selects(s, volume_arn, volume.tags):
                        volume.backup.append(f"{label} (EBS{opt_in})")
                    elif ec2 and selects(s, instance_arn, host.tags):
                        volume.backup.append(f"{label} (EC2, the instance{opt_in})")
            for policy_id, policy_state, types, target in state.dlm:
                if policy_state != "ENABLED":
                    continue
                by_volume = "VOLUME" in types and any(
                    volume.tags.get(k) == v for k, v in target.items()
                )
                by_instance = "INSTANCE" in types and any(
                    host.tags.get(k) == v for k, v in target.items()
                )
                if by_volume or by_instance:
                    volume.dlm.append(policy_id)


def judge_dormant(
    checks: Checks, row: DormantRow, live: bool, hosts: list | None, state: BackupState | None
) -> None:
    what = f"backup of {row.account}/{row.slice}"
    if not live:
        checks.note("OB-4", what, f"not measured: {row.profile} is not in this run")
        return
    if hosts is None or state is None or not state.complete:
        checks.fail(
            "OB-4",
            what,
            "a read of the host or of the backup plans failed (section 9): a failed read is not "
            "an expected absence (Lesson 13).",
        )
        return
    if not hosts:
        checks.note(
            "OB-4",
            what,
            f"no instance carries Name={row.host}: nothing to cover (a slice not applied, or a "
            "host renamed against slices.py instance_name).",
        )
        return
    volumes = [v for h in hosts for v in h.volumes]
    uncovered = [f"{v.volume_id} {v.size}" for v in volumes if not v.backup]
    if not state.plans:
        snapshots = [f"{v.volume_id} by DLM {', '.join(v.dlm)}" for v in volumes if v.dlm]
        checks.note(
            "OB-4",
            what,
            f"no AWS Backup plan in this account, so step 8.1 is not built: "
            f"{count(len(uncovered), 'volume')} uncovered ({', '.join(uncovered)}); snapshots today: "
            f"{'; '.join(snapshots) or 'none'}.",
        )
    elif uncovered:
        opt_in = ", ".join(f"{k}={state.opt_in.get(k, '-')}" for k in ("EBS", "EC2"))
        checks.fail(
            "OB-4",
            what,
            f"no backup plan covers {', '.join(uncovered)}: {len(uncovered)} of "
            f"{count(len(volumes), 'volume')} of {row.host}, with this account's opt-in {opt_in}",
        )
    else:
        organizations = any(
            plan_id.startswith(ORGANIZATIONS_PLAN_PREFIX) for _, plan_id, _, _ in state.plans
        )
        caveat = (
            "; an Organizations plan follows Management's opt-in, which no profile here reads"
            if organizations
            else ""
        )
        checks.ok(
            "OB-4",
            what,
            f"every volume of {row.host} covered ({count(len(volumes), 'volume')}){caveat}",
        )


# ------------------------------------------------------------------------------- OB-5


@dataclass
class QuotaRow:
    scope: str  # what the count is of: the account, or one VPC
    label: str
    usage: int
    limit: float | None
    source: str  # applied | default | route53 | unmatched | unread
    code: str = "-"
    name: str = "-"
    misnamed: bool = False  # the code answered with a quota of another name

    @property
    def over(self) -> bool:
        """At or over THRESHOLD of the limit; nothing in use is never over, and a limit read
        under another quota's name is no limit."""
        if self.limit is None or self.misnamed:
            return False
        return self.usage > 0 and self.usage >= THRESHOLD * self.limit

    @property
    def percent(self) -> str:
        if self.limit is None:
            return "-"
        if self.limit == 0:
            return "-" if self.usage == 0 else "over"
        return f"{100 * self.usage / self.limit:.0f}%"


def fixed_quota(reader: Reader, spec: tuple) -> tuple:
    """(value, source, code, name, misnamed) of one quota by its code; the applied value, else
    AWS's default. value is None when the quota went unread."""
    label, service, code, words = spec
    got = reader.json(
        "service-quotas",
        "get-service-quota",
        "--service-code",
        service,
        "--quota-code",
        code,
        absent="NoSuchResourceException",
    )
    source = "applied"
    if got.absent:
        source = "default"
        got = reader.json(
            "service-quotas",
            "get-aws-default-service-quota",
            "--service-code",
            service,
            "--quota-code",
            code,
        )
    if not got.ok:
        return None, "unread", code, "-", False
    quota = got.doc.get("Quota") or {}
    name = quota.get("QuotaName") or "-"
    return quota.get("Value"), source, code, name, words not in name.lower()


def read_network_quotas(reader: Reader) -> tuple:
    """([QuotaRow], complete) for the Elastic IPs, the endpoints and the hosted zones."""
    rows = []
    addresses = reader.json("ec2", "describe-addresses")
    vpcs = reader.json("ec2", "describe-vpcs")
    endpoints = reader.json("ec2", "describe-vpc-endpoints")
    zones = reader.json("route53", "get-account-limit", "--type", "MAX_HOSTED_ZONES_BY_OWNER")
    complete = addresses.ok and vpcs.ok and endpoints.ok and zones.ok
    if addresses.ok:
        value, source, code, name, misnamed = fixed_quota(reader, EIP_QUOTA)
        rows.append(
            QuotaRow(
                "account",
                EIP_QUOTA[0],
                len(addresses.doc.get("Addresses", [])),
                value,
                source,
                code,
                name,
                misnamed,
            )
        )
    if vpcs.ok and endpoints.ok:
        live_endpoints = [
            e
            for e in endpoints.doc.get("VpcEndpoints", [])
            if str(e.get("State", "")).lower() not in ENDPOINT_GONE_STATES
        ]
        value, source, code, name, misnamed = fixed_quota(reader, INTERFACE_ENDPOINT_QUOTA)
        for vpc in vpcs.doc.get("Vpcs", []):
            vpc_id = vpc.get("VpcId", "-")
            vpc_name = tag_map(vpc.get("Tags")).get("Name", "-")
            count = sum(
                1
                for e in live_endpoints
                if e.get("VpcId") == vpc_id and e.get("VpcEndpointType") in ENDPOINT_TYPES_PER_VPC
            )
            rows.append(
                QuotaRow(
                    f"{vpc_id} {vpc_name}",
                    INTERFACE_ENDPOINT_QUOTA[0],
                    count,
                    value,
                    source,
                    code,
                    name,
                    misnamed,
                )
            )
        value, source, code, name, misnamed = fixed_quota(reader, GATEWAY_ENDPOINT_QUOTA)
        gateways = sum(1 for e in live_endpoints if e.get("VpcEndpointType") == "Gateway")
        rows.append(
            QuotaRow(
                "account",
                GATEWAY_ENDPOINT_QUOTA[0],
                gateways,
                value,
                source,
                code,
                name,
                misnamed,
            )
        )
    if zones.ok:
        rows.append(
            QuotaRow(
                "account",
                "hosted zones",
                int(zones.doc.get("Count") or 0),
                (zones.doc.get("Limit") or {}).get("Value"),
                "route53",
                "MAX_HOSTED_ZONES_BY_OWNER",
                "route53 get-account-limit",
            )
        )
    return rows, complete


def read_sagemaker_usage(reader: Reader) -> tuple:
    """({(category, instance type): count}, complete) of what runs now: in-progress processing,
    training and transform jobs, endpoints in service, and Studio apps."""
    usage = {}
    complete = True

    def add(category: str, instance_type: str | None, count) -> None:
        if not instance_type or instance_type == "system":
            return
        key = (category, instance_type)
        usage[key] = usage.get(key, 0) + int(count or 0)

    # (category, list command, its list key, the name key, the describe command, its flag)
    jobs = (
        (
            "processing",
            "list-processing-jobs",
            "ProcessingJobSummaries",
            "ProcessingJobName",
            "describe-processing-job",
            "--processing-job-name",
        ),
        (
            "training",
            "list-training-jobs",
            "TrainingJobSummaries",
            "TrainingJobName",
            "describe-training-job",
            "--training-job-name",
        ),
        (
            "transform",
            "list-transform-jobs",
            "TransformJobSummaries",
            "TransformJobName",
            "describe-transform-job",
            "--transform-job-name",
        ),
    )
    for category, command, key, name_key, describe, flag in jobs:
        listing = reader.json("sagemaker", command, "--status-equals", "InProgress")
        complete = complete and listing.ok
        for summary in listing.doc.get(key, []):
            one = reader.json("sagemaker", describe, flag, summary.get(name_key, "-"))
            complete = complete and one.ok
            if category == "processing":
                cluster = (one.doc.get("ProcessingResources") or {}).get("ClusterConfig") or {}
                add(category, cluster.get("InstanceType"), cluster.get("InstanceCount"))
            elif category == "training":
                config = one.doc.get("ResourceConfig") or {}
                add(category, config.get("InstanceType"), config.get("InstanceCount"))
                for group in config.get("InstanceGroups") or []:
                    add(category, group.get("InstanceType"), group.get("InstanceCount"))
            else:
                resources = one.doc.get("TransformResources") or {}
                add(category, resources.get("InstanceType"), resources.get("InstanceCount"))

    endpoints = reader.json("sagemaker", "list-endpoints")
    complete = complete and endpoints.ok
    for summary in endpoints.doc.get("Endpoints", []):
        if summary.get("EndpointStatus") in ENDPOINT_GONE:
            continue
        endpoint = reader.json(
            "sagemaker", "describe-endpoint", "--endpoint-name", summary.get("EndpointName", "-")
        )
        config = reader.json(
            "sagemaker",
            "describe-endpoint-config",
            "--endpoint-config-name",
            endpoint.doc.get("EndpointConfigName", "-"),
        )
        complete = complete and endpoint.ok and config.ok
        types = {
            v.get("VariantName"): v.get("InstanceType")
            for v in config.doc.get("ProductionVariants", [])
        }
        for variant in endpoint.doc.get("ProductionVariants", []):
            add(
                "endpoint",
                types.get(variant.get("VariantName")),
                variant.get("CurrentInstanceCount"),
            )

    apps = reader.json("sagemaker", "list-apps")
    complete = complete and apps.ok
    for app in apps.doc.get("Apps", []):
        if app.get("Status") not in ("InService", "Pending"):
            continue
        add(app.get("AppType", "-"), (app.get("ResourceSpec") or {}).get("InstanceType"), 1)
    return usage, complete


def sagemaker_quota_rows(reader: Reader, usage: dict) -> tuple:
    """([QuotaRow], complete): one row per (category, instance type) in use, its limit from
    Service Quotas, the applied value over AWS's default, matched by the quota's name."""
    if not usage:
        return [], True
    complete = True
    names = {}  # quota name -> (value, source, code)
    for command, source in (
        ("list-aws-default-service-quotas", "default"),
        ("list-service-quotas", "applied"),
    ):
        listing = reader.json("service-quotas", command, "--service-code", "sagemaker")
        complete = complete and listing.ok
        for q in listing.doc.get("Quotas", []):
            names[q.get("QuotaName", "")] = (q.get("Value"), source, q.get("QuotaCode", "-"))
    rows = []
    for (category, instance_type), in_use in sorted(usage.items()):
        if category in SAGEMAKER_QUOTA_NAMES:
            matches = [SAGEMAKER_QUOTA_NAMES[category].format(instance_type)]
            matches = [n for n in matches if n in names]
        else:
            words = STUDIO_APP_WORDS.get(category, (category.lower(),))
            matches = [
                n
                for n in names
                if instance_type in n.split()
                and "app" in n.lower()
                and any(w in n.lower() for w in words)
            ]
        label = f"{category} on {instance_type}"
        if len(matches) != 1:
            why = "no quota of that name" if not matches else f"{len(matches)} quotas match"
            rows.append(QuotaRow("account", label, in_use, None, "unmatched", "-", why))
            continue
        value, source, code = names[matches[0]]
        rows.append(QuotaRow("account", label, in_use, value, source, code, matches[0]))
    return rows, complete


def judge_quotas(checks: Checks, label: str, rows: list, complete: bool) -> None:
    what = f"quotas in {label}"
    if not complete:
        checks.fail(
            "OB-5",
            what,
            "a usage or limit read failed (section 9): a failed read is not an expected "
            "absence (Lesson 13).",
        )
    over = [f"{r.label} ({r.scope}) {r.usage} of {quota_text(r.limit)}" for r in rows if r.over]
    unknown = [f"{r.label} ({r.usage} in use, {r.name})" for r in rows if r.limit is None]
    misnamed = [f"{r.code} answered {r.name!r}" for r in rows if r.misnamed]
    if over:
        checks.fail(
            "OB-5",
            what,
            f"at or over {THRESHOLD:.0%} of the limit: {'; '.join(over)}. The path is an "
            "increase request in Service Quotas (step 9.2).",
        )
    if unknown:
        checks.note("OB-5", what, f"limit not read for {'; '.join(unknown)}")
    if misnamed:
        checks.note(
            "OB-5",
            what,
            f"a quota code answered with another quota's name: {'; '.join(misnamed)}. Read "
            "the console before trusting that row.",
        )
    if over or not complete:
        return
    measured = [r for r in rows if r.limit and not r.misnamed]
    if not measured:
        checks.ok("OB-5", what, "nothing in use against a known limit")
        return
    top = max(measured, key=lambda r: r.usage / r.limit)
    checks.ok(
        "OB-5",
        what,
        f"every quota under {THRESHOLD:.0%}; the highest is {top.label} ({top.scope}), "
        f"{top.usage} of {quota_text(top.limit)} ({top.percent})",
    )


# ------------------------------------------------------------------------------- the run


@dataclass
class Measured:
    """Everything read in one account."""

    reader: Reader
    groups: list | None = None
    trail: TrailReading | None = None
    alarms: list | None = None
    verdicts: list = field(default_factory=list)  # [(verdict, why)] in alarm order
    topics: dict = field(default_factory=dict)  # arn -> Topic
    quotas: list = field(default_factory=list)
    quotas_complete: bool = True


def select_profiles(argv: list) -> tuple:
    """The profiles named, else every awsds-infra-* profile in ~/.aws/config."""
    if argv:
        return profiles.select(argv)
    selected = [p for p in profiles.discover() if p.startswith(INFRA_PREFIX)]
    if not selected:
        note(f"no profiles to measure (no '{INFRA_PREFIX}*' profile in ~/.aws/config)")
        sys.exit(1)
    return selected, f"the infrastructure user's reach - every '{INFRA_PREFIX}*' profile"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = select_profiles(argv)
    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    checks = Checks()

    # ----------------------------------------------------------------- per account
    measured = []
    for caller in callers:
        if not caller.live:
            continue
        reader = Reader(caller, errors)
        note(f"measuring {reader.label} ...")
        m = Measured(reader)
        m.groups = read_log_groups(reader)
        m.trail = read_trail(reader)
        m.alarms = read_alarms(reader)
        for alarm in m.alarms or []:
            for arn in alarm.alarm_actions + alarm.other_actions:
                if ":sns:" in arn and arn not in m.topics:
                    m.topics[arn] = resolve_topic(reader, arn)
        m.verdicts = [alarm_verdict(a, m.topics) for a in m.alarms or []]
        m.quotas, m.quotas_complete = read_network_quotas(reader)
        usage, usage_complete = read_sagemaker_usage(reader)
        sagemaker_rows, limits_complete = sagemaker_quota_rows(reader, usage)
        m.quotas += sagemaker_rows
        m.quotas_complete = m.quotas_complete and usage_complete and limits_complete
        measured.append(m)

    # ----------------------------------------------------------------- the [D] rows
    dormant, dormant_missing = ([], "a standalone run carries no repository")
    if not ctx.standalone:
        dormant, dormant_missing = read_dormant_rows(ctx.repo_root)
    by_label = {m.reader.label: m for m in measured}
    backup_states = {}  # profile -> BackupState
    dormant_hosts = {}  # (account, slice) -> [Host] or None
    for row in dormant:
        m = by_label.get(row.profile)
        if m is None:
            continue
        if row.profile not in backup_states:
            note(f"reading the backup plans of {row.profile} ...")
            backup_states[row.profile] = read_backup_state(m.reader)
        hosts = read_hosts(m.reader, row.host)
        if hosts is not None:
            cover(hosts, backup_states[row.profile], m.reader.account)
        dormant_hosts[(row.account, row.slice)] = hosts

    # ----------------------------------------------------------------- the checks
    for m in measured:
        judge_log_groups(checks, m.reader.label, m.groups)
    judge_trail(checks, [m.trail for m in measured])
    wired_by = None
    for m in measured:
        for alarm in m.alarms or []:
            if alarm.wired and not alarm.scaling_only and wired_by is None:
                wired_by = f"{alarm.name} ({m.reader.label})"
    for m in measured:
        judge_alarms(checks, m.reader.label, m.alarms, m.verdicts, wired_by)
    if dormant_missing:
        checks.note(
            "OB-4",
            "backup of the [D] hosts",
            f"the [D] rows went unread: {dormant_missing}. OB-4 is the laptop run's.",
        )
    for row in dormant:
        judge_dormant(
            checks,
            row,
            row.profile in by_label,
            dormant_hosts.get((row.account, row.slice)),
            backup_states.get(row.profile),
        )
    for m in measured:
        judge_quotas(checks, m.reader.label, m.quotas, m.quotas_complete)

    # ----------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        write_report(rep, source, callers, measured, dormant, dormant_hosts, backup_states)
        rep.h1("8. CHECKS")
        rep.checks_table(checks)
        rep.line()
        rep.line(f"{checks.n_fail()} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  OB-1  every log group this project creates has an explicit retention (step 3.1); the
        services' never-expiring groups are a note, EXC-10's decision
  OB-2  the organization trail's bucket expires no version below 90 days nor below its
        Object Lock (step 3.2, INV-14); decided only in Log Archive
  OB-3  every alarm notifies an SNS topic that resolves (step 2); a note until the first
        alarm measured is wired, a fail for every unwired one after
  OB-4  an AWS Backup plan covers every volume of every [D] host in layers.py (step 8); a
        note while the account holds no plan, a fail for every volume left out after
  OB-5  every quota of step 9.1 under 80 % of its limit""")
        rep.h1("9. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/observability.py")

    # ----------------------------------------------------------------- the exit
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 9)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 8)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


def write_report(
    rep: Report,
    source: str,
    callers: list,
    measured: list,
    dormant: list,
    dormant_hosts: dict,
    backup_states: dict,
) -> None:
    """Sections 1 to 7: the readings each check is judged on."""
    rep.banner(
        "Observability - the Stage 12 evidence: retention, the trail, alarms, backup, quotas"
    )
    rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/observability.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. Log groups and their retention - OB-1
  3. The organization trail's bucket - OB-2
  4. Alarms and their notification targets - OB-3
  5. The [D] hosts' volumes and the backup plans - OB-4
  6. Quotas against their limits - OB-5
  7. What nothing here measures
  8. CHECKS
  9. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER FOR OB-3 AND OB-4 until steps 2 and 8 run:
    each reads `note`, and the first alarm wired or the first backup plan turns every
    one still missing into a `fail`.
  - OB-2 IS DECIDED IN LOG ARCHIVE ONLY. A laptop run names the bucket and notes it;
    the `-` run in Log Archive's CloudShell reads its lifecycle and its lock.
  - EVERY VERDICT IS A CONFIGURATION READING. A topic that resolves has not delivered
    anything until step 2.4 provokes its alarm, and a covered volume is not a backup
    until step 8.4 restores one.
  - OB-5 COUNTS WHAT RUNS NOW. Taken with the environment down it says little; the
    reading step 9.1 wants is taken with it up.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

    # ==================================================================================
    rep.h1("1. Which accounts were measured, and as whom")
    rep.text("""A profile is an (account, permission set) pair; every awsds-infra-* profile
resolves to the infrastructure user through InfrastructureAccess, and `-` is CloudShell's
ambient identity. A `(failed)` row is a profile that did not authenticate, never a
compliant one.

""")
    rep.tabulate(
        ["PROFILE\tACCOUNT\tCALLER ARN"]
        + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
    )

    # ==================================================================================
    rep.h1("2. Log groups and their retention - OB-1")
    rep.text("""$ aws --profile <p> logs describe-log-groups
$ aws --profile <p> logs list-tags-for-resource --resource-arn <group arn>

OWNER is `project` when the name is in the project's namespace (/awsds/, awsds-) or the
group carries Project=AWS-DataScience, the tag every slice's default_tags stamps; the
tags are read only for the groups outside the namespace. `service` is a group no slice
declares. RETENTION `never` is the API's missing retentionInDays.

""")
    for m in measured:
        rep.h2(m.reader.label)
        if m.groups is None:
            rep.line("(the listing failed - section 9)")
            continue
        if not m.groups:
            rep.line("(no log group in this account)")
            continue
        rep.tabulate(
            ["LOG GROUP\tRETENTION\tSTORED MB\tOWNER\tBY"]
            + [
                f"{g.name}\t{g.retention if g.retention is not None else 'never'}\t"
                f"{g.stored_mb:.1f}\t{g.owner}\t{g.why}"
                for g in sorted(m.groups, key=lambda g: g.name)
            ]
        )

    # ==================================================================================
    rep.h1("3. The organization trail's bucket - OB-2")
    rep.text(f"""$ aws --profile <p> cloudtrail describe-trails
$ aws s3api get-bucket-versioning --bucket "$BUCKET"                 # Log Archive only
$ aws s3api get-object-lock-configuration --bucket "$BUCKET"         # Log Archive only
$ aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET"    # Log Archive only

The bucket is read off {ORG_TRAIL}, the only source of its name that
cannot be stale (INV-14). OWNER is the account id inside the bucket's name; the bucket
is read only where it equals the caller's account, since another account's bucket
refuses these reads by its policy.

""")
    rep.tabulate(
        ["PROFILE\tTRAIL\tBUCKET\tKEY PREFIX\tORG TRAIL\tHOME\tOWNER\tREAD HERE"]
        + [trail_row(m.reader.label, m.trail) for m in measured]
    )
    for m in measured:
        t = m.trail
        if t is None or not t.read_here:
            continue
        mode, days = lock_retention(t.lock)
        rep.line()
        rep.line(f"BUCKET={t.bucket}")
        rep.line(f"  versioning  : {t.versioning}")
        rep.line(f"  object lock : {mode or 'absent'} / {days if days is not None else '-'} days")
        rep.line(f"  lifecycle   : {lifecycle_summary(t.rules)}")
        rep.line(f"  floor       : {max(LIFECYCLE_FLOOR_DAYS, days or 0)} days")

    # ==================================================================================
    rep.h1("4. Alarms and their notification targets - OB-3")
    rep.text("""$ aws --profile <p> cloudwatch describe-alarms \\
      --alarm-types MetricAlarm CompositeAlarm
$ aws --profile <p> sns get-topic-attributes --topic-arn <each SNS action>
$ aws --profile <p> kms describe-key --key-id <the topic's KmsMasterKeyId>
$ aws --profile <p> kms get-key-policy --key-id <its key id> --policy-name default

A topic RESOLVES when it exists in this account and Region, holds a confirmed
subscription, its policy carries an Allow on sns:Publish that takes
cloudwatch.amazonaws.com (or the default statement's AWS:* scoped to this account), and
it is unencrypted or under a customer key whose policy grants CloudWatch kms:Decrypt and
kms:GenerateDataKey*. The policies are read as shapes, not evaluated: a Deny elsewhere, or
a condition narrower than an account, is not seen here. Subscription endpoints are never
read, only their counts.

""")
    for m in measured:
        rep.h2(m.reader.label)
        if m.alarms is None:
            rep.line("(the listing failed - section 9)")
            continue
        if not m.alarms:
            rep.line("(no alarm in this account)")
            continue
        rep.tabulate(
            ["ALARM\tKIND\tSTATE\tACTIONS\tVERDICT\tWHY"]
            + [
                f"{a.name}\t{a.kind}\t{a.state}\t{'on' if a.enabled else 'off'}\t{v}\t{why}"
                for a, (v, why) in zip(m.alarms, m.verdicts)
            ]
        )
        if m.topics:
            rep.line()
            rep.tabulate(
                ["TOPIC\tCONFIRMED\tADMITS CLOUDWATCH\tKEY\tVERDICT"]
                + [
                    f"{t.arn}\t{t.confirmed}\t{t.admits}\t{t.key}\t"
                    + (t.verdict if t.why == "-" else f"{t.verdict}: {t.why}")
                    for t in m.topics.values()
                ]
            )

    # ==================================================================================
    rep.h1("5. The [D] hosts' volumes and the backup plans - OB-4")
    rep.text("""$ aws --profile <p> ec2 describe-instances --filters Name=tag:Name,Values=<host>
$ aws --profile <p> ec2 describe-volumes --volume-ids <its volumes>
$ aws --profile <p> backup list-backup-plans
$ aws --profile <p> backup get-backup-plan --backup-plan-id <id>
$ aws --profile <p> backup list-backup-selections --backup-plan-id <id>
$ aws --profile <p> backup get-backup-selection --backup-plan-id <id> --selection-id <id>
$ aws --profile <p> backup describe-region-settings
$ aws --profile <p> dlm get-lifecycle-policies
$ aws --profile <p> dlm get-lifecycle-policy --policy-id <id>

The rows are layers.py's [D] rows; the host is the Name tag slices.py instance_name
derives (DORMANT_HOST_NAMES, else awsds-<env token>-<slice>) and the profile is
backend.py's PROFILES entry for the account folder. A volume is COVERED by a backup
selection that takes its own ARN with EBS opted in, or its instance's ARN with EC2 opted
in. The opt-in is this account's, except for a plan an Organizations backup policy made
(id orgs/...), which follows Management's, read by no profile here. A selection is read
as (Resources or ListOfTags) and every Condition, less NotResources, with `*` the only
wildcard. DLM snapshots are context: they are not the locked, cross-region plan step 8
builds.

""")
    if not dormant:
        rep.line("(no [D] row was read - section 8 says why)")
    for row in dormant:
        rep.h2(f"{row.account}/{row.slice}  host {row.host}  profile {row.profile}")
        hosts = dormant_hosts.get((row.account, row.slice))
        if (row.account, row.slice) not in dormant_hosts:
            rep.line("(not measured: the profile is not in this run)")
            continue
        if hosts is None:
            rep.line("(a read failed - section 9)")
            continue
        if not hosts:
            rep.line(f"(no instance carries Name={row.host})")
            continue
        lines = ["INSTANCE\tSTATE\tVOLUME\tDEVICE\tSIZE\tAWS BACKUP\tDLM"]
        for h in hosts:
            for v in h.volumes:
                lines.append(
                    f"{h.instance_id}\t{h.state}\t{v.volume_id}\t{v.device}\t{v.size}\t"
                    f"{', '.join(v.backup) or 'none'}\t{', '.join(v.dlm) or 'none'}"
                )
        rep.tabulate(lines)
    for profile, state in backup_states.items():
        rep.h2(f"AWS Backup and DLM in {profile}")
        opt = ", ".join(f"{k}={state.opt_in.get(k, '-')}" for k in ("EBS", "EC2"))
        rep.line(f"resource-type opt-in: {opt}")
        rep.line()
        if not state.plans:
            rep.line("(no backup plan)")
        for name, plan_id, rules, selections in state.plans:
            rep.line(f"plan {name}  id {plan_id}")
            rep.line(f"  rules: {rules or '-'}")
            for s in selections:
                rep.line(
                    f"  selection {s.get('SelectionName', '-')}: {json.dumps(selection_shape(s))}"
                )
        rep.line()
        if not state.dlm:
            rep.line("(no DLM policy)")
        else:
            rep.tabulate(
                ["DLM POLICY\tSTATE\tRESOURCE TYPES\tTARGET TAGS"]
                + [
                    f"{pid}\t{st}\t{','.join(types) or '-'}\t"
                    f"{','.join(f'{k}={v}' for k, v in tags.items()) or '-'}"
                    for pid, st, types, tags in state.dlm
                ]
            )

    # ==================================================================================
    rep.h1("6. Quotas against their limits - OB-5")
    rep.text(f"""$ aws --profile <p> ec2 describe-addresses
$ aws --profile <p> ec2 describe-vpcs
$ aws --profile <p> ec2 describe-vpc-endpoints
$ aws --profile <p> route53 get-account-limit --type MAX_HOSTED_ZONES_BY_OWNER
$ aws --profile <p> service-quotas get-service-quota --service-code <svc> --quota-code <code>
$ aws --profile <p> sagemaker list-processing-jobs --status-equals InProgress   # and training,
                                                       # transform, list-endpoints, list-apps
$ aws --profile <p> service-quotas list-service-quotas --service-code sagemaker

A row is OVER at {THRESHOLD:.0%} of its limit or more; nothing in use is never over.
SOURCE `applied` is a value Service Quotas holds for the account, `default` AWS's own,
`unmatched` a SageMaker usage whose quota no name matched. The endpoint quota counts the
Interface and Gateway Load Balancer endpoints of each VPC; the gateway endpoints have a
Regional quota of their own. SageMaker counts only what runs now, so its rows exist
only while something does.

""")
    for m in measured:
        rep.h2(m.reader.label)
        if not m.quotas:
            rep.line("(nothing read - section 9)" if not m.quotas_complete else "(no quota row)")
            continue
        rep.tabulate(
            ["QUOTA\tSCOPE\tUSAGE\tLIMIT\tUSE\tSOURCE\tCODE\tQUOTA NAME"]
            + [
                f"{r.label}\t{r.scope}\t{r.usage}\t{quota_text(r.limit)}\t{r.percent}\t"
                f"{r.source}\t{r.code}\t{r.name}"
                for r in m.quotas
            ]
        )

    # ==================================================================================
    rep.h1("7. What nothing here measures")
    rep.text("""Read this BEFORE reading section 8 as a pass.

  - Log Archive and Audit hold no CLI profile (D33/D34). Log Archive is where OB-2 is
    decided: `python3 aws/observability.py -` in its CloudShell, as AWS Control Tower
    Admin through AWSAdministratorAccess, with the aws/ folder uploaded.
  - Management holds the budgets step 2.1 alarms, and AWS/Billing metrics publish only in
    us-east-1, outside this Region-bound instrument. It also holds the AWS Backup opt-in
    that every plan an Organizations backup policy makes follows (step 8.1's plan).
  - EventBridge rules that notify (the deploy roles' misuse rule, the debug role's
    assume rule) are not alarms; cicd.py and deploytargets.py read them.
  - A configuration is not a delivery: an alarm proves its target when step 2.4 provokes
    it, a backup plan its coverage when step 8.4 restores a volume.
  - Whether today's CloudTrail deliveries still carry the lock's retention, INV-14's
    quiet failure, is a per-object reading (`s3api get-object-retention` on a fresh
    object, in Log Archive), not a bucket setting.
  - SageMaker usage is a snapshot of this minute. A quota a job ran into an hour ago and
    a space started after this run are both invisible here.""")


def trail_row(label: str, trail: TrailReading | None) -> str:
    """One account's row of section 3's table."""
    if trail is None:
        return f"{label}\t(listing failed)\t-\t-\t-\t-\t-\t-"
    if not trail.found:
        return f"{label}\t(not visible)\t-\t-\t-\t-\t-\t-"
    return (
        f"{label}\t{ORG_TRAIL}\t{trail.bucket}\t{trail.prefix}\t{trail.organization}\t"
        f"{trail.home}\t{trail.owner}\t{'yes' if trail.read_here else 'no'}"
    )


def selection_shape(selection: dict) -> dict:
    """The fields of a backup selection that decide what it takes."""
    keys = ("Resources", "ListOfTags", "Conditions", "NotResources")
    return {k: selection[k] for k in keys if selection.get(k)}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
