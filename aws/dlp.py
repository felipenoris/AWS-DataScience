#!/usr/bin/env -S uv run --quiet
# dlp.py - Stage 11's evidence, per account, side by side: Macie's per-account state and
# its delegation, the Lake Formation data cells filters, the data-event trails (data-only,
# validated, delivering into the governed logs bucket), the EventBridge rules + alarms +
# SNS topics of the exfiltration patterns, the two GuardDuty paid features (expected
# DISABLED before step 4 and ENABLED everywhere after it), and the CloudTrail-tampering
# Sid in the baseline SCP.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/dlp.py                     # every awsds-* profile
#             ./aws/dlp.py awsds-infra-data    # only the ones named
#             python3 aws/dlp.py -             # CloudShell, ambient credentials
#   writes:   aws/output/dlp.txt   (untracked - see .gitignore)
#   reads:    macie2:GetMacieSession, cloudtrail:DescribeTrails, GetTrailStatus,
#             GetEventSelectors, events:ListRules, cloudwatch:DescribeAlarms,
#             sns:ListTopics, s3api:ListBuckets, lakeformation:ListDataCellsFilter,
#             guardduty:ListDetectors, GetDetector,
#             organizations:ListDelegatedAdministrators, ListPolicies, DescribePolicy,
#             sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The stage's
# whole subject is detection ACROSS accounts: the lake and drop-box live in Data
# Governance while the derived zone - where governed data actually re-surfaces (D19; the
# SMUS project path since 2026-08-26) - lives in the Interactive accounts, so "is the monitored map covered" is only readable
# with the columns side by side; and the GuardDuty features are org-wide state, where one
# account silently uncovered is exactly the finding (the same argument as ./aws/guardduty.py).
#
# CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - trail name         awsds-<env>-data-events           (Stage 11 step 5.1)
#   - delivery bucket    awsds-data-logs                   (5.1, decision 7)
#   - filter name prefix awsds-flt-                        (2.1a)
#   - rule names         awsds-<env>-massread, awsds-<env>-presigned-use,
#                        awsds-data-unexpected-writer, awsds-data-athena   (5.2)
#   - SNS topic          awsds-<env>-security              (5.2)
#   - baseline Sid       DenyCloudTrailKill                (5.4, decision 6)
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - Everything in AUDIT: Macie's job history and results-repository answer, the
#     internal-access analyzer (audit-iam-analyser.sh reads that one), and GuardDuty's
#     org configuration. No CLI profile reaches that account, by design (D33/D34).
#   - The behavioural proofs - the alarm pair of 5.5, the filter pair of 2.3 - are the
#     stage's own, run from persona sessions (Lesson 20). A describe call proves none.
#   - Whether a rule's PATTERN is right is proven by 5.5 firing it, not by its name
#     existing here (presence, never sufficiency).

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "dlp.txt"

DATA_PROFILE = "awsds-infra-data"
IDENTITY_PROFILE = "awsds-infra-identity"


# The DLP-scoped accounts (decision 3's map at N=1): the lake account plus the two
# Interactive accounts whose projects buckets D19 (as revised 2026-08-26) puts in
# scope. Production joins when
# decision 3 adds awsds-prod-outputs; every sandbox ordinal is in scope (D35).
def env_token(profile: str) -> str | None:
    if profile.startswith("awsds-infra-sandbox"):
        return "sandbox"
    return {
        DATA_PROFILE: "data",
        "awsds-infra-dev": "dev",
    }.get(profile)


# The contracts (see header).
TRAIL_SUFFIX = "-data-events"
LOGS_BUCKET = "awsds-data-logs"
FILTER_PREFIX = "awsds-flt-"
TAMPER_SID = "DenyCloudTrailKill"
BASELINE_POLICY = "awsds-org-scp-baseline"

# The two detector features step 4 enables (Stage 15 step 3 switches them off by name;
# they arrive ON - that stage's step 0).
GD_FEATURES = ("S3_DATA_EVENTS", "EBS_MALWARE_PROTECTION")


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    scoped = [p for p in live if env_token(p)]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------------------------------ Macie, per account
    macie_rows: list = []  # (profile, status: ENABLED/PAUSED/disabled/(call failed))
    for p in scoped:
        cli = cli_for(p)
        note(f"measuring {p} ...")
        res = cli.run(
            "macie2",
            "get-macie-session",
            "--query",
            "status",
            "--output",
            "text",
            log=False,
            tolerate="Macie is not enabled",
        )
        if res.tolerated:
            macie_rows.append((p, "disabled"))
        elif not res.ok:
            logerr(p, "macie2 get-macie-session", res.stderr)
            macie_rows.append((p, "(call failed)"))
        else:
            macie_rows.append((p, res.stdout.strip() or "?"))

    macie_delegation = "(not read)"
    if IDENTITY_PROFILE in live:
        cli = cli_for(IDENTITY_PROFILE)
        res = cli.run(
            "organizations",
            "list-delegated-administrators",
            "--service-principal",
            "macie.amazonaws.com",
            "--query",
            "DelegatedAdministrators[].[Name,Status]",
            "--output",
            "text",
            log=False,
            tolerate="AccessDenied",
        )
        if res.tolerated:
            macie_delegation = "(read denied from Identity - check from Management)"
        elif res.ok:
            macie_delegation = res.stdout.strip() or "(none registered)"

    # ----------------------------------------------- the LF data cells filters, lake side
    data_live = DATA_PROFILE in live
    filters: list = []  # (name, database, table)
    if data_live:
        cli = cli_for(DATA_PROFILE)
        res = cli.run(
            "lakeformation",
            "list-data-cells-filter",
            "--query",
            "DataCellsFilters[].[Name,DatabaseName,TableName]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(DATA_PROFILE, "lakeformation list-data-cells-filter", res.stderr)
        else:
            filters = [tuple(r) for r in json.loads(res.stdout or "[]")]

    # -------------------------------------------------- the trails, selectors and delivery
    # (profile, trail name, logging, validation, s3 bucket, data-only, monitored ARN count)
    trail_rows: list = []
    derived_gap: list = []  # (profile, projects bucket) - exists, no selector names it
    for p in scoped:
        env = env_token(p)
        cli = cli_for(p)
        res = cli.run(
            "cloudtrail",
            "describe-trails",
            "--query",
            "trailList[].[Name,S3BucketName,LogFileValidationEnabled,HomeRegion]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(p, "cloudtrail describe-trails", res.stderr)
            continue
        ours = [
            t
            for t in json.loads(res.stdout or "[]")
            if t[0].startswith("awsds-") and t[0].endswith(TRAIL_SUFFIX)
        ]
        if not ours:
            trail_rows.append((p, "-", "-", "-", "-", "-", "-"))
            continue
        for name, bucket, validation, _home in ours:
            r = cli.run(
                "cloudtrail",
                "get-trail-status",
                "--name",
                name,
                "--query",
                "IsLogging",
                "--output",
                "text",
                log=False,
            )
            logging = r.stdout.strip() if r.ok else "(call failed)"
            if not r.ok:
                logerr(p, f"cloudtrail get-trail-status {name}", r.stderr)
            r = cli.run(
                "cloudtrail",
                "get-event-selectors",
                "--trail-name",
                name,
                "--output",
                "json",
                log=False,
            )
            data_only = "-"
            arn_count = 0
            selector_blob = ""
            if not r.ok:
                logerr(p, f"cloudtrail get-event-selectors {name}", r.stderr)
            else:
                doc = json.loads(r.stdout or "{}")
                adv = doc.get("AdvancedEventSelectors", [])
                basic = doc.get("EventSelectors")
                cats = set()
                for sel in adv:
                    for f in sel.get("FieldSelectors", []):
                        if f.get("Field") == "eventCategory":
                            cats.update(f.get("Equals", []))
                        if f.get("Field") == "resources.ARN":
                            arn_count += len(f.get("StartsWith", []) or f.get("Equals", []))
                selector_blob = json.dumps(adv)
                if basic:
                    data_only = "no (basic selectors)"
                elif "Management" in cats:
                    data_only = "no (Management selected)"
                elif "Data" in cats:
                    data_only = "yes"
                else:
                    data_only = "(no selectors)"
            trail_rows.append(
                (p, name, logging, str(validation), bucket, data_only, str(arn_count))
            )

            # D19's promise, re-homed 2026-08-26: the derived zone is the SMUS project
            # path now (awsds-<env>-smus-projects), so THAT bucket is the one each
            # Interactive account's trail must select - orphaned project prefixes
            # included, which is exactly what a scope written from the live project
            # list would miss (stage-11's callout).
            if env in ("sandbox", "dev") and selector_blob:
                r2 = cli.run(
                    "s3api",
                    "list-buckets",
                    "--query",
                    "Buckets[].Name",
                    "--output",
                    "json",
                    log=False,
                )
                if r2.ok:
                    derived = [
                        b for b in json.loads(r2.stdout or "[]") if b.endswith("-smus-projects")
                    ]
                    for b in derived:
                        if b not in selector_blob:
                            derived_gap.append((p, b))

    # ------------------------------------------------- the rules, alarms and topics per env
    rule_rows: list = []  # (profile, rule names found)
    alarm_rows: list = []  # (profile, alarm names found)
    topic_rows: list = []  # (profile, topic found: yes/no)
    for p in scoped:
        env = env_token(p)
        cli = cli_for(p)
        res = cli.run(
            "events",
            "list-rules",
            "--name-prefix",
            "awsds-",
            "--query",
            "Rules[].Name",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(p, "events list-rules", res.stderr)
            rules = []
        else:
            rules = json.loads(res.stdout or "[]")
        rule_rows.append((p, rules))

        res = cli.run(
            "cloudwatch",
            "describe-alarms",
            "--alarm-name-prefix",
            "awsds-",
            "--query",
            "MetricAlarms[].[AlarmName,StateValue]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(p, "cloudwatch describe-alarms", res.stderr)
            alarms = []
        else:
            alarms = [
                (n, s)
                for n, s in json.loads(res.stdout or "[]")
                if "massread" in n or "presigned" in n or "athena" in n or "writer" in n
            ]
        alarm_rows.append((p, alarms))

        res = cli.run(
            "sns",
            "list-topics",
            "--query",
            "Topics[].TopicArn",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(p, "sns list-topics", res.stderr)
            topic_rows.append((p, "(call failed)"))
        else:
            arns = json.loads(res.stdout or "[]")
            topic_rows.append(
                (p, "yes" if any(a.endswith(f"awsds-{env}-security") for a in arns) else "no")
            )

    # ------------------------------------------------------- GuardDuty features, org-wide
    gd_rows: list = []  # (profile, detector, per-feature status)
    for p in live:
        cli = cli_for(p)
        res = cli.run(
            "guardduty",
            "list-detectors",
            "--query",
            "DetectorIds[0]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "guardduty list-detectors", res.stderr)
            gd_rows.append((p, "-", "(call failed)"))
            continue
        det = res.stdout.strip()
        if not det or det == "None":
            gd_rows.append((p, "-", "no detector"))
            continue
        r = cli.run(
            "guardduty", "get-detector", "--detector-id", det, "--output", "json", log=False
        )
        if not r.ok:
            logerr(p, f"guardduty get-detector {det}", r.stderr)
            gd_rows.append((p, det, "(call failed)"))
            continue
        feat = {
            f.get("Name"): f.get("Status") for f in json.loads(r.stdout or "{}").get("Features", [])
        }
        gd_rows.append((p, det, " ".join(f"{n}={feat.get(n, 'absent')}" for n in GD_FEATURES)))

    # ------------------------------------------------ the baseline Sid, read from Identity
    tamper = "(not read)"
    if IDENTITY_PROFILE in live:
        cli = cli_for(IDENTITY_PROFILE)
        res = cli.run(
            "organizations",
            "list-policies",
            "--filter",
            "SERVICE_CONTROL_POLICY",
            "--query",
            f"Policies[?Name=='{BASELINE_POLICY}'].Id | [0]",
            "--output",
            "text",
            log=False,
            tolerate="AccessDenied",
        )
        if res.tolerated:
            tamper = "(read denied from Identity)"
        elif res.ok and res.stdout.strip() not in ("", "None"):
            pid = res.stdout.strip()
            r = cli.run(
                "organizations",
                "describe-policy",
                "--policy-id",
                pid,
                "--query",
                "Policy.Content",
                "--output",
                "text",
                log=False,
            )
            if not r.ok:
                logerr(IDENTITY_PROFILE, f"organizations describe-policy {pid}", r.stderr)
                tamper = "(call failed)"
            else:
                tamper = "present" if TAMPER_SID in r.stdout else "absent"

    # ------------------------------------------------------------------------- the checks
    # DP-1: Macie enabled in every scoped account - together, or not at all (Lesson 14's
    # shape: a partial rollout is the state that hides).
    if scoped:
        on = [p for p, s in macie_rows if s == "ENABLED"]
        off = [p for p, s in macie_rows if s == "disabled"]
        if not on:
            checks.note(
                "DP-1",
                "Macie in the scoped accounts",
                "disabled everywhere - expected before Stage 11 step 1.",
            )
        elif off:
            checks.fail(
                "DP-1",
                "Macie in the scoped accounts",
                f"enabled in {len(on)}, disabled in: {', '.join(off)} - auto-enable does "
                "not reach existing accounts (the documented inverse of GuardDuty's ALL); "
                "each one is added by the administrator (step 1.2).",
            )
        else:
            bad = [p for p, s in macie_rows if s not in ("ENABLED",)]
            if bad:
                checks.fail("DP-1", "Macie in the scoped accounts", f"unexpected state in: {bad}")
            else:
                checks.ok("DP-1", "Macie in the scoped accounts", f"ENABLED in all {len(on)}")

    # DP-2: the data cells filters exist under the name contract.
    if data_live:
        if not filters:
            checks.note(
                "DP-2",
                "LF data cells filters",
                "none - expected before Stage 11 step 2.",
            )
        else:
            bad = [n for n, _d, _t in filters if not n.startswith(FILTER_PREFIX)]
            if bad:
                checks.fail(
                    "DP-2",
                    "LF data cells filter naming",
                    f"outside the {FILTER_PREFIX}* contract: {', '.join(bad)} (step 2.1a).",
                )
            else:
                checks.ok("DP-2", "LF data cells filters", f"{len(filters)} under {FILTER_PREFIX}*")

    # DP-3: every scoped account carries its data-event trail: logging, validated,
    # data-only, delivering into the governed logs bucket.
    built = [r for r in trail_rows if r[1] != "-"]
    if scoped and not built:
        checks.note(
            "DP-3",
            "data-event trails",
            "none in any scoped account - expected before Stage 11 step 5.",
        )
    elif built:
        for p, name, logging, validation, bucket, data_only, arns in trail_rows:
            if name == "-":
                checks.fail(
                    "DP-3",
                    f"trail in {p}",
                    "other scoped accounts carry one and this one does not - the "
                    "monitored map is partial (step 5.1, decision 3).",
                )
                continue
            problems = []
            if logging != "True":
                problems.append(f"IsLogging={logging}")
            if validation != "True":
                problems.append("log file validation off")
            if bucket != LOGS_BUCKET:
                problems.append(f"delivers to {bucket}, not {LOGS_BUCKET} (decision 7)")
            if data_only != "yes":
                problems.append(
                    f"not data-event-only ({data_only}) - the management copy "
                    "is the org trail's; a second one bills for nothing"
                )
            if arns in ("0", "-"):
                problems.append(
                    "no resources.ARN selector - an unscoped data trail logs "
                    "every bucket and bills accordingly"
                )
            if problems:
                checks.fail("DP-3", f"trail {name} in {p}", "; ".join(problems) + ".")
            else:
                checks.ok("DP-3", f"trail {name} in {p}", f"logging, validated, {arns} ARN(s)")

    # DP-4: the D19 promise, re-homed 2026-08-26 - the derived zone is the SMUS project
    # path, so the projects bucket outside its own account's trail scope is the gap.
    if built:
        for p, b in derived_gap:
            checks.fail(
                "DP-4",
                f"projects bucket in {p}'s trail scope",
                f"{b} exists and no selector names it - the derived zone (D19 as revised "
                "2026-08-26) lives in it, orphaned project prefixes included; the map "
                "(decision 3) is missing a row.",
            )
        if not derived_gap:
            checks.ok("DP-4", "projects buckets in trail scope", "every projects bucket selected")

    # DP-5: rules, alarms and topic per scoped account - together, or not at all.
    if built:
        for p, rules in rule_rows:
            env = env_token(p)
            expected = [f"awsds-{env}-massread", f"awsds-{env}-presigned-use"]
            if env == "data":
                expected += ["awsds-data-unexpected-writer", "awsds-data-athena"]
            missing = [r for r in expected if r not in rules]
            if missing:
                checks.fail(
                    "DP-5",
                    f"EventBridge rules in {p}",
                    f"missing: {', '.join(missing)} (step 5.2).",
                )
            else:
                checks.ok("DP-5", f"EventBridge rules in {p}", f"all {len(expected)} present")
        for p, t in topic_rows:
            if t == "no":
                checks.fail(
                    "DP-5",
                    f"SNS topic in {p}",
                    f"no awsds-{env_token(p)}-security topic - alarms with no "
                    "subscriber are Lesson 5 (step 5.2).",
                )
    elif scoped:
        checks.note("DP-5", "rules, alarms, topics", "no trail yet - expected before step 5.")

    # DP-6: the two GuardDuty features move together, org-wide (step 4): all DISABLED
    # before the stage, all ENABLED after - the partial state is the finding either way.
    detectors = [r for r in gd_rows if r[1] != "-" and "(call failed)" not in r[2]]
    if live and not detectors:
        checks.note(
            "DP-6",
            "GuardDuty paid features",
            "no detector in any measured account - expected before Stage 15; "
            "this check has nothing to read until the base service exists.",
        )
    if detectors:
        enabled = [p for p, _d, f in detectors if all(f"{n}=ENABLED" in f for n in GD_FEATURES)]
        disabled = [
            p for p, _d, f in detectors if all(f"{n}=ENABLED" not in f for n in GD_FEATURES)
        ]
        mixed = [p for p, _d, _f in detectors if p not in enabled and p not in disabled]
        if not enabled and not mixed:
            checks.note(
                "DP-6",
                "GuardDuty paid features",
                "both DISABLED everywhere - expected before Stage 11 step 4 "
                "(./aws/guardduty.py GD-3 owns this reading until then).",
            )
        elif mixed or (enabled and disabled):
            checks.fail(
                "DP-6",
                "GuardDuty paid features",
                f"partial rollout - enabled: {enabled or '-'}; disabled: {disabled or '-'}; "
                f"mixed: {mixed or '-'}. Step 4's auto-enable ALL moves every account "
                "together; a member outside coverage is the gap it exists to close.",
            )
        else:
            checks.ok(
                "DP-6",
                "GuardDuty paid features",
                f"{' and '.join(GD_FEATURES)} ENABLED in all {len(enabled)} measured",
            )

    # DP-7: the tampering Sid lands with the first member trail (step 5.4, decision 6).
    if tamper == "absent":
        if built:
            checks.fail(
                "DP-7",
                f"{TAMPER_SID} in {BASELINE_POLICY}",
                "a member-account trail exists and nothing denies StopLogging/DeleteTrail "
                "- POLICIES.md's revision trigger has fired and the statement is owed "
                "(step 5.4, battery phases 1-3).",
            )
        else:
            checks.note(
                "DP-7",
                f"{TAMPER_SID} in {BASELINE_POLICY}",
                "absent - expected before Stage 11 step 5.",
            )
    elif tamper == "present":
        checks.ok("DP-7", f"{TAMPER_SID} in {BASELINE_POLICY}", "present")

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("DLP - the Stage 11 evidence: Macie, filters, trails, alarms, GuardDuty")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/dlp.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. Macie, per scoped account, and its delegation
  3. The Lake Formation data cells filters
  4. The data-event trails
  5. The rules, alarms and topics
  6. The two GuardDuty paid features, org-wide
  7. The CloudTrail-tampering Sid
  8. CHECKS
  9. The accounts nothing here is measuring
 10. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 11 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 9 names what nothing here
    reached: everything in Audit above all.
  - PRESENCE, NEVER SUFFICIENCY - whether a rule's pattern matches the right events
    is proven by firing it (stage step 5.5), not by its name existing here.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ==============================================================================
        rep.h1("1. Which accounts were measured, and as whom")
        rep.text("""A profile is an (account, permission set) pair; every awsds-* profile here resolves
to the infrastructure user. A `(failed)` row is a profile that did not authenticate,
never a compliant one.

""")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN\tDLP-SCOPED"]
            + [
                f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}"
                f"\t{'yes' if env_token(c.profile) else '-'}"
                for c in callers
            ]
        )

        # ==============================================================================
        rep.h1("2. Macie, per scoped account, and its delegation")
        if macie_rows:
            rep.tabulate(["PROFILE\tMACIE"] + [f"{p}\t{s}" for p, s in macie_rows])
        else:
            rep.line("No scoped profile was measured.")
        rep.line()
        rep.line(f"delegated administrator (macie.amazonaws.com): {macie_delegation}")
        rep.text("""
Delegating IS enabling (step 1.1): the designation is made from Management, the
members and the job from Audit - neither holds a profile, so this file reads only
each member's own session state. Restate INV-09 in docs/AWS_STATE.md when the
delegation lands, and re-run ./aws/org-trusted-access-services.py.""")

        # ==============================================================================
        rep.h1("3. The Lake Formation data cells filters")
        if not data_live:
            rep.line(f"{DATA_PROFILE} was not measured - nothing to show.")
        elif not filters:
            rep.line("No data cells filter. Expected before Stage 11 step 2.")
        else:
            rep.tabulate(["FILTER\tDATABASE\tTABLE"] + [f"{n}\t{d}\t{t}" for n, d, t in filters])
            rep.text("""
Presence, never sufficiency: what a filter returns to whom is the stage's 2.3
proof, run from a consumer session.""")

        # ==============================================================================
        rep.h1("4. The data-event trails")
        if trail_rows:
            rep.tabulate(
                ["PROFILE\tTRAIL\tLOGGING\tVALIDATED\tDELIVERS TO\tDATA-ONLY\tARNS"]
                + [f"{p}\t{n}\t{lg}\t{v}\t{b}\t{d}\t{a}" for p, n, lg, v, b, d, a in trail_rows]
            )
            rep.text(f"""
The org trail (Control Tower's) is deliberately not listed: these are the
project's member-account trails alone, data events only, delivering into
{LOGS_BUCKET} (decision 7). An unscoped data trail is a cost defect as well as a
design one - the ARNS column must never read 0.""")
        else:
            rep.line("No scoped profile was measured.")

        # ==============================================================================
        rep.h1("5. The rules, alarms and topics")
        for p, rules in rule_rows:
            rep.line(f"{p}:")
            if rules:
                for r in sorted(rules):
                    rep.line(f"  rule   {r}")
            else:
                rep.line("  (no awsds-* rule)")
            alarms = dict(alarm_rows).get(p, [])
            for n, s in sorted(alarms):
                rep.line(f"  alarm  {n} ({s})")
            rep.line(f"  topic  awsds-{env_token(p)}-security: {dict(topic_rows).get(p, '-')}")
            rep.line()

        # ==============================================================================
        rep.h1("6. The two GuardDuty paid features, org-wide")
        rep.tabulate(["PROFILE\tDETECTOR\tFEATURES"] + [f"{p}\t{d}\t{f}" for p, d, f in gd_rows])
        rep.text("""
Before Stage 11 step 4 both features read DISABLED everywhere (./aws/guardduty.py
GD-3 enforces that); after it they read ENABLED everywhere. The partial state is the
finding in both directions.""")

        # ==============================================================================
        rep.h1("7. The CloudTrail-tampering Sid")
        rep.line(f"{TAMPER_SID} in {BASELINE_POLICY}: {tamper}")
        rep.line("  - owed by step 5.4 the moment the first member trail exists")
        rep.line("    (POLICIES.md's named revision trigger; battery phases 1-3).")

        # ==============================================================================
        rep.h1("8. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  DP-1  Macie ENABLED in every scoped account, together (step 1.2)
  DP-2  the data cells filters exist under the awsds-flt-* contract (2.1a)
  DP-3  each scoped account's trail: logging, validated, data-only, scoped,
        delivering into the governed logs bucket (5.1, decision 7)
  DP-4  every derived bucket is inside its own account's trail scope - the
        Stage 5 step 9.2 promise (D19)
  DP-5  the rules, alarms and topic of 5.2, per account
  DP-6  the two GuardDuty features move together, org-wide (step 4)
  DP-7  the tampering Sid lands with the first member trail (5.4, decision 6)""")

        # ==============================================================================
        rep.h1("9. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 8 as a pass.

  - AUDIT holds no CLI profile (D33/D34): Macie's members list, job history and
    results-repository answer, the internal-access analyzer (2.1.3) and
    GuardDuty's org configuration are verified in its console or CloudShell -
    aws/cloudshell/audit-iam-analyser.sh reads the analyzer half.
  - Management is outside every profile here; the Macie delegation itself is the
    one thing this file reads about it, through Organizations.
  - Production and Staging are outside the DLP scope until decision 3 adds
    awsds-prod-outputs; a Stage 14 Sandbox joins the scope at its vend (D35) -
    re-run this script after each one.""")

        # ==============================================================================
        rep.h1("10. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/dlp.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 10)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 8)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
