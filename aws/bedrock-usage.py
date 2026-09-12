#!/usr/bin/env -S uv run --quiet
# bedrock-usage.py - what Amazon Bedrock consumed in a window, per model, and what that costs.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/bedrock-usage.py                                         # this month, to now (UTC)
#             ./aws/bedrock-usage.py 2026-09                                 # one calendar month
#             ./aws/bedrock-usage.py 2026-09-12T21:00Z 2026-09-12T23:00Z     # one window
#             ./aws/bedrock-usage.py --profile awsds-infra-staging           # another account
#   writes:   aws/output/bedrock-usage.txt   (untracked - see .gitignore)
#   reads:    cloudwatch:ListMetrics and GetMetricData on the AWS/Bedrock namespace, cloudtrail:
#             LookupEvents for the four invocation event names, and sts:GetCallerIdentity, all in
#             us-west-2. Every one is a read; this script invokes no model. GetMetricData is billed
#             per metric requested (USD 0.01 per 1,000), which one run keeps to fractions of a cent.
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# A TIME WITH NO OFFSET IS REFUSED. `2026-09-12T21:00` is 21:00 in whatever zone the reader assumes,
# and this machine's aws CLI renders timestamps in local time (-03:00) while the API takes UTC - the
# reading this script replaces confused the two once, on 2026-09-12. Write `Z` or `-03:00`.
#
# WHERE THE NUMBERS COME FROM, AND WHY TWO CHANNELS.
#
#   CloudWatch  AWS/Bedrock publishes Invocations and four token counts per ModelId, the inference
#               profile id, with model invocation logging OFF. For a cross-region `us.` profile every
#               invocation lands in the SOURCE region's series, whichever region processed it -
#               measured 2026-09-12, 22/20/3 against CloudTrail. That matters here: the Control Tower
#               Region ceiling refuses cloudwatch:ListMetrics in us-east-1 and us-east-2.
#   CloudTrail  records every call in the source region. It carries no token counts, and it is the
#               only channel that can say the CloudWatch series missed something another region
#               holds.
#
# WHAT RECONCILES, measured 2026-09-12, and what does not:
#
#   - Tokens: the dimensionless series equals the sum of the per-model series, exactly, for all
#     four token metrics. A difference means a model this report did not query (BU-2).
#   - Invocations: the dimensionless series equals the per-model sum PLUS InvocationClientErrors,
#     which is published only without a ModelId - 66 = 60 + 6 (BU-3).
#   - Successful invocations per model: CloudTrail events carrying a modelId and no errorCode equal
#     CloudWatch's per-model Invocations. InvokeModelWithResponseStream writes a second event with
#     an empty requestParameters and InvokeModel does not; the sibling carries no modelId, so
#     counting only events that name one counts each invocation once (BU-4).
#   - Refusals do NOT reconcile across channels: a denied call reaches CloudTrail with no modelId,
#     and one hour held 18 AccessDenied events against 6 client errors. Both are printed; neither
#     is asserted against the other.
#
# WHAT THE DOLLARS ARE. Measured tokens times the rates docs/PRICING.md records - computed, not
# billed. Cache writes are priced at the 5-minute TTL rate, because CloudWatch does not separate a
# 5-minute write from a 1-hour one and the 1-hour rate is higher (Opus 4.5: 11.00 against 6.875).
# Cost Explorer's usage types separate them and carry the billed amount, a day late.
#
# WHAT IT CANNOT SEE (Lesson 13): which space, which user or which session spent the tokens. Every
# space in a project invokes as the same project role, and neither channel names the space - so a
# window that measures one session is one in which nothing else ran.

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.bedrockscope import SCP_PATH, scp_declaration
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "bedrock-usage.txt"
DEFAULT_PROFILE = "awsds-infra-sandbox-1"
PRICING = "docs/PRICING.md"

UTC = timezone.utc
NAMESPACE = "AWS/Bedrock"
TOKENS = (
    "InputTokenCount",
    "OutputTokenCount",
    "CacheReadInputTokenCount",
    "CacheWriteInputTokenCount",
)
SHORT = {
    "Invocations": "invocations",
    "InputTokenCount": "input",
    "OutputTokenCount": "output",
    "CacheReadInputTokenCount": "cache read",
    "CacheWriteInputTokenCount": "cache write",
}
INVOCATION_EVENTS = ("InvokeModel", "InvokeModelWithResponseStream", "Converse", "ConverseStream")

# CloudWatch keeps 1-minute points for 15 days, 5-minute for 63, 1-hour for 455 (the vendor's
# retention schedule); a period finer than the data still held returns nothing, silently.
RETENTION = ((timedelta(days=15), 60), (timedelta(days=63), 300), (timedelta(days=455), 3600))
CLOUDTRAIL_HISTORY = timedelta(days=90)
# Both channels publish minutes behind their events (Lesson 62's quiet clock), so a window ending
# closer to now than this is reported as possibly incomplete rather than as a disagreement.
LAG = timedelta(minutes=15)
# LookupEvents answers 50 events a page at two requests a second; a month at this estate's volume is
# a few hundred, and a cap keeps a busy month from turning a read into minutes.
MAX_EVENTS = 4000

MONTH_RE = re.compile(r"^(?P<y>\d{4})-(?P<m>\d{2})$")
# `| **Claude Opus 4.5** — the primary | **5.50** | **27.50** | **0.55** | **6.875** |`
RATE_ROW_RE = re.compile(
    r"^\|\s*\**Claude (?P<family>Opus|Sonnet|Haiku) (?P<version>[0-9.]+)\**[^|]*"
    + r"\|\s*\**(?P<input>[0-9.]+)\**\s*"
    + r"\|\s*\**(?P<output>[0-9.]+)\**\s*"
    + r"\|\s*\**(?P<cache_read>[0-9.]+)\**\s*"
    + r"\|\s*\**(?P<cache_write>[0-9.]+)\**\s*\|",
    re.M,
)
# `us.anthropic.claude-opus-4-5-20251101-v1:0` -> prefix `us`, key `claude-opus-4-5`
MODEL_KEY_RE = re.compile(
    r"^(?:(?P<prefix>[a-z]+)\.)?anthropic\.(?P<key>claude-[a-z]+-[0-9-]+?)(?:-\d{8}-v\d+:\d+)?$"
)


def parse_instant(text: str) -> datetime:
    """An ISO-8601 instant WITH an offset, as UTC. A naive time raises."""
    value = text.strip()
    if value[-1:] in ("Z", "z"):
        value = value[:-1] + "+00:00"
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise ValueError(f"{text!r} carries no offset - write Z or an explicit one such as -03:00")
    return moment.astimezone(UTC)


def window_from(args: list, now: datetime) -> tuple[datetime, datetime, bool]:
    """(start, end, month mode) from the positional arguments."""
    if not args:
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now, True
    if len(args) == 1 and MONTH_RE.match(args[0]):
        m = MONTH_RE.match(args[0])
        start = datetime(int(m.group("y")), int(m.group("m")), 1, tzinfo=UTC)
        end = (start + timedelta(days=32)).replace(day=1)
        return start, min(end, now), True
    if len(args) == 2:
        start, end = parse_instant(args[0]), parse_instant(args[1])
        if end <= start:
            raise ValueError("the end is not after the start")
        return start, min(end, now), False
    raise ValueError("expected nothing, a month YYYY-MM, or a START and an END")


def resolution(start: datetime, now: datetime) -> int | None:
    """The finest period CloudWatch still holds for data as old as `start`; None past retention."""
    age = now - start
    for limit, period in RETENTION:
        if age <= limit:
            return period
    return None


def model_key(model_id: str) -> tuple[str | None, str | None]:
    """(profile prefix, rate key) for an Anthropic model id; (None, None) for anything else."""
    m = MODEL_KEY_RE.match(model_id)
    if not m:
        return None, None
    return m.group("prefix"), m.group("key")


def recorded_rates(path: Path) -> dict:
    """Rate key -> (input, output, cache read, cache write 5 min), USD per 1M tokens."""
    if not path.is_file():
        return {}
    rates = {}
    for m in RATE_ROW_RE.finditer(path.read_text(encoding="utf-8")):
        key = f"claude-{m.group('family').lower()}-{m.group('version').replace('.', '-')}"
        rates[key] = tuple(
            float(m.group(g)) for g in ("input", "output", "cache_read", "cache_write")
        )
    return rates


def metric_data(cli: AwsCli, queries: list, start: datetime, end: datetime) -> dict | None:
    """Id -> [(timestamp, value)], following NextToken; None when a call failed."""
    out: dict = defaultdict(list)
    token = None
    while True:
        args = [
            "cloudwatch",
            "get-metric-data",
            "--start-time",
            start.isoformat(),
            "--end-time",
            end.isoformat(),
            "--metric-data-queries",
            json.dumps(queries),
            "--output",
            "json",
        ]
        if token:
            args += ["--next-token", token]
        res = cli.run(*args)
        if not res.ok:
            return None
        page = json.loads(res.stdout)
        for r in page.get("MetricDataResults", []):
            out[r["Id"]].extend(zip(r.get("Timestamps", []), r.get("Values", [])))
        token = page.get("NextToken")
        if not token:
            return out


def stat(qid: str, metric: str, dimensions: list, period: int) -> dict:
    return {
        "Id": qid,
        "MetricStat": {
            "Metric": {"Namespace": NAMESPACE, "MetricName": metric, "Dimensions": dimensions},
            "Period": period,
            "Stat": "Sum",
        },
    }


def usd(value: float) -> str:
    return f"{value:.4f}" if value < 1 else f"{value:.2f}"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    profile = DEFAULT_PROFILE
    if "--profile" in argv:
        i = argv.index("--profile")
        if i + 1 >= len(argv):
            note("--profile needs a name")
            return 2
        profile = argv[i + 1]
        argv = argv[:i] + argv[i + 2 :]

    now = datetime.now(UTC).replace(microsecond=0)
    try:
        start, end, month_mode = window_from(argv, now)
    except ValueError as exc:
        note(f"bedrock-usage.py: {exc}")
        return 2
    # Minute boundaries: the API aligns to them, and a fractional edge would silently round.
    start = start.replace(second=0, microsecond=0)
    if end.second or end.microsecond:
        end = end.replace(second=0, microsecond=0) + timedelta(minutes=1)

    errors = ErrorLog()
    caller = profiles.preflight([profile], errors, out_label=out_label)[0]
    cli = AwsCli(profile=profile, region=context.REGION, errors=errors)
    checks = Checks()

    # ------------------------------------------------------------------ what the window allows
    finest = resolution(start, now)
    period = None
    if finest is None:
        checks.fail(
            "BU-1",
            "CloudWatch still holds the window",
            f"{start.isoformat()} is older than the 455 days CloudWatch keeps any Bedrock point",
        )
    else:
        # One bucket the length of the window is its exact sum (measured 2026-09-12: one period of
        # two hours, of a day and of twelve days each returned the totals the hourly series added
        # to). The bucket is widened to the finest period still held, never narrowed.
        period = max(finest, math.ceil((end - start).total_seconds() / finest) * finest)
        # Widening past `now` reads nothing that exists, so only the part before it is a distortion.
        widened = min(start + timedelta(seconds=period), now) - end
        if widened <= timedelta(0):
            checks.ok(
                "BU-1",
                "CloudWatch still holds the window",
                f"{start.isoformat()} to {end.isoformat()}, read from {finest}-second data",
            )
        else:
            checks.note(
                "BU-1",
                "CloudWatch still holds the window",
                f"data this old is kept at {finest}-second resolution, so the window reads up to "
                f"{int(widened.total_seconds())} s past its end",
            )

    # ------------------------------------------------------------------------ which models
    listed: set = set()
    declared: set = set()
    if caller.live:
        res = cli.run(
            "cloudwatch",
            "list-metrics",
            "--namespace",
            NAMESPACE,
            "--metric-name",
            "Invocations",
            "--query",
            "Metrics[].Dimensions[?Name=='ModelId'].Value[]",
            "--output",
            "json",
        )
        if res.ok:
            listed = set(json.loads(res.stdout or "[]"))
    # ListMetrics names only series with data in the last two weeks, so a model used earlier in a
    # long window would drop out of the report in silence. The scoped set is always queried; BU-2 is
    # what catches anything else.
    pairs, _, _ = scp_declaration(ctx.repo_root / SCP_PATH)
    if pairs:
        declared = {p for p in pairs.values() if p}
    models = sorted(listed | declared)

    # ------------------------------------------------------------------------- CloudWatch
    totals: dict = defaultdict(lambda: defaultdict(float))  # model -> metric -> sum
    aggregate: dict = defaultdict(float)
    by_day: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    cloudwatch_read = False
    if caller.live and period is not None:
        queries, names = [], {}
        for i, model in enumerate(models):
            for j, metric in enumerate(("Invocations",) + TOKENS):
                qid = f"m{i}x{j}"
                names[qid] = (model, metric)
                queries.append(stat(qid, metric, [{"Name": "ModelId", "Value": model}], period))
        for j, metric in enumerate(("Invocations", "InvocationClientErrors") + TOKENS):
            qid = f"a{j}"
            names[qid] = (None, metric)
            queries.append(stat(qid, metric, [], period))
        data = metric_data(cli, queries, start, start + timedelta(seconds=period))
        if data is not None:
            cloudwatch_read = True
            for qid, points in data.items():
                model, metric = names[qid]
                value = sum(v for _, v in points)
                if model is None:
                    aggregate[metric] = value
                else:
                    totals[model][metric] = value

        if month_mode and cloudwatch_read:
            daily, names = [], {}
            for i, model in enumerate(models):
                for j, metric in enumerate(("Invocations",) + TOKENS):
                    qid = f"d{i}x{j}"
                    names[qid] = (model, metric)
                    daily.append(stat(qid, metric, [{"Name": "ModelId", "Value": model}], 86400))
            data = metric_data(cli, daily, start, end)
            if data is not None:
                for qid, points in data.items():
                    model, metric = names[qid]
                    for stamp, value in points:
                        day = datetime.fromisoformat(stamp).astimezone(UTC).date().isoformat()
                        by_day[day][model][metric] += value

    active = [m for m in models if any(totals[m][k] for k in ("Invocations",) + TOKENS)]
    # An identity over nothing holds whatever the instrument is doing - reading the wrong region
    # would pass it too - so an empty window is reported as unverified, never as agreement.
    empty = cloudwatch_read and not any(
        aggregate[k] for k in ("Invocations", "InvocationClientErrors") + TOKENS
    )
    nothing = "nothing in the window to reconcile - an empty window satisfies every identity"

    if empty:
        checks.note("BU-2", "every token is attributed to a model", nothing)
        checks.note("BU-3", "every invocation is a model's or a refusal", nothing)
    elif cloudwatch_read:
        missing = {
            metric: aggregate[metric] - sum(totals[m][metric] for m in models) for metric in TOKENS
        }
        unattributed = {k: v for k, v in missing.items() if v}
        if unattributed:
            checks.fail(
                "BU-2",
                "every token is attributed to a model",
                ", ".join(f"{int(v)} {SHORT[k]}" for k, v in unattributed.items())
                + " tokens belong to a ModelId this report did not query - the per-model table "
                "under-reports; ListMetrics names only series active in the last two weeks",
            )
        else:
            checks.ok(
                "BU-2",
                "every token is attributed to a model",
                f"the dimensionless series equals the per-model sum, {len(models)} model(s) queried",
            )
        per_model = sum(totals[m]["Invocations"] for m in models)
        refused = aggregate["InvocationClientErrors"]
        if int(aggregate["Invocations"]) == int(per_model + refused):
            checks.ok(
                "BU-3",
                "every invocation is a model's or a refusal",
                f"{int(aggregate['Invocations'])} = {int(per_model)} by model + {int(refused)} client errors",
            )
        else:
            checks.note(
                "BU-3",
                "every invocation is a model's or a refusal",
                f"{int(aggregate['Invocations'])} in the dimensionless series against "
                f"{int(per_model)} by model + {int(refused)} client errors - a category this identity "
                "does not name, such as server errors or throttles",
            )
    elif caller.live:
        checks.fail("BU-2", "every token is attributed to a model", "CloudWatch was not read")

    # ------------------------------------------------------------------------- CloudTrail
    trail_ok: Counter = Counter()
    trail_denied: Counter = Counter()
    events_read = 0
    newest_event = None
    capped = False
    trail_read = False
    if caller.live and now - start <= CLOUDTRAIL_HISTORY:
        trail_read = True
        for name in INVOCATION_EVENTS:
            token = None
            while not capped:
                args = [
                    "cloudtrail",
                    "lookup-events",
                    "--lookup-attributes",
                    f"AttributeKey=EventName,AttributeValue={name}",
                    "--start-time",
                    start.isoformat(),
                    "--end-time",
                    end.isoformat(),
                    "--max-results",
                    "50",
                    "--output",
                    "json",
                ]
                if token:
                    args += ["--next-token", token]
                res = cli.run(*args)
                if not res.ok:
                    trail_read = False
                    break
                page = json.loads(res.stdout)
                for event in page.get("Events", []):
                    events_read += 1
                    record = json.loads(event["CloudTrailEvent"])
                    stamp = datetime.fromisoformat(
                        record["eventTime"].replace("Z", "+00:00")
                    ).astimezone(UTC)
                    newest_event = max(newest_event, stamp) if newest_event else stamp
                    model_id = (record.get("requestParameters") or {}).get("modelId")
                    if record.get("errorCode"):
                        trail_denied[record["errorCode"]] += 1
                    elif model_id:
                        trail_ok[model_id.rsplit("/", 1)[-1]] += 1
                token = page.get("NextToken")
                capped = events_read >= MAX_EVENTS
                if not token:
                    break

    recent = now - end < LAG
    if caller.live and now - start > CLOUDTRAIL_HISTORY:
        checks.note(
            "BU-4",
            "CloudTrail agrees with CloudWatch, per model",
            "not compared - the window starts beyond CloudTrail's 90-day event history",
        )
    elif caller.live and (not trail_read or not cloudwatch_read):
        checks.note(
            "BU-4", "CloudTrail agrees with CloudWatch, per model", "one channel was not read"
        )
    elif caller.live:
        rows = set(trail_ok) | set(active)
        differ = [
            (m, trail_ok.get(m, 0), int(totals[m]["Invocations"]))
            for m in sorted(rows)
            if trail_ok.get(m, 0) != int(totals[m]["Invocations"])
        ]
        detail = ", ".join(f"{m} CloudTrail {a} / CloudWatch {b}" for m, a, b in differ)
        if not rows and not trail_denied:
            checks.note("BU-4", "CloudTrail agrees with CloudWatch, per model", nothing)
        elif not differ and not capped:
            checks.ok(
                "BU-4",
                "CloudTrail agrees with CloudWatch, per model",
                f"{sum(trail_ok.values())} successful invocations, {len(rows)} model(s), both channels",
            )
        elif capped:
            checks.note(
                "BU-4",
                "CloudTrail agrees with CloudWatch, per model",
                f"stopped at {events_read} events (the cap is {MAX_EVENTS}) - not a full comparison",
            )
        elif recent:
            checks.note(
                "BU-4",
                "CloudTrail agrees with CloudWatch, per model",
                f"the window ends {int((now - end).total_seconds() // 60)} min ago and both channels "
                f"publish late: {detail}. Re-run once {LAG} has passed",
            )
        else:
            checks.fail("BU-4", "CloudTrail agrees with CloudWatch, per model", detail)

    # --------------------------------------------------------------------------- the prices
    rates = recorded_rates(ctx.repo_root / PRICING)
    cost: dict = {}  # model -> (input, output, cache read, cache write) USD
    unpriced: dict = {}
    for model in active:
        prefix, key = model_key(model)
        if key is None:
            unpriced[model] = "not an Anthropic model; docs/PRICING.md prices it elsewhere"
        elif prefix not in (None, "us"):
            unpriced[model] = (
                f"a `{prefix}.` profile, whose rates the recorded table does not carry"
            )
        elif key not in rates:
            unpriced[model] = f"no `Claude ...` row for {key} in {PRICING}"
        else:
            r = rates[key]
            cost[model] = tuple(totals[model][t] * r[n] / 1e6 for n, t in enumerate(TOKENS))
    if ctx.standalone or not (ctx.repo_root / PRICING).is_file():
        checks.note("BU-5", "every model with tokens has a recorded rate", f"{PRICING} not found")
    elif unpriced:
        checks.note(
            "BU-5",
            "every model with tokens has a recorded rate",
            f"{len(unpriced)} unpriced: " + ", ".join(sorted(unpriced)),
        )
    elif active:
        checks.ok(
            "BU-5",
            "every model with tokens has a recorded rate",
            f"{len(cost)} model(s), from {PRICING}",
        )
    else:
        checks.ok("BU-5", "every model with tokens has a recorded rate", "no tokens in the window")

    total_usd = sum(sum(c) for c in cost.values())
    parts = [sum(c[i] for c in cost.values()) for i in range(4)]

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        mode = "month to date" if month_mode and end == now else "month" if month_mode else "window"
        rep.banner("Amazon Bedrock: what a window consumed, per model, and what it costs")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {profile}
region    : {context.REGION}
window    : {start.isoformat()} to {end.isoformat()}   ({mode}, UTC)
produced  : aws/bedrock-usage.py   (index: aws/INDEX.md)

SECTIONS
  1. What was read, and as whom
  2. By model
  3. By day
  4. Where the money went
  5. The two channels
  6. Checks
  7. Calls that failed

HOW TO READ THIS FILE
  - THE DOLLARS ARE COMPUTED, NOT BILLED. Measured tokens times the rates docs/PRICING.md
    records. Cache writes are priced at the 5-minute TTL rate; CloudWatch does not separate
    a 1-hour write, which costs more. Cost Explorer carries the billed amount, a day late.
  - CACHE, NOT OUTPUT, IS WHERE A CODING SESSION SPENDS. The client re-sends and caches its
    whole context every turn: on 2026-09-12 cache writes were 52% of the day and output 15%.
  - NOTHING HERE NAMES A SPACE OR A USER. Every space invokes as its project role. A window
    measures one session only if nothing else ran in it.
  - A WINDOW ENDING IN THE LAST {int(LAG.total_seconds() // 60)} MINUTES MAY BE INCOMPLETE. Both channels
    publish late; re-run rather than read a short count as a low one.

This file is not versioned (aws/output/ is in .gitignore). Regenerate it rather than
trusting a stale copy.""")

        rep.h1("1. What was read, and as whom")
        rep.tabulate(
            [
                "WHAT\tWHERE",
                f"tokens and invocations\tCloudWatch {NAMESPACE}, {context.REGION}, one {period or '-'} s bucket",
                f"models queried\t{len(listed)} listed by ListMetrics + {len(declared)} declared in the SCP = {len(models)}",
                f"invocation events\tCloudTrail {context.REGION}, {events_read} read"
                + (" (capped)" if capped else ""),
                f"newest event\t{newest_event.isoformat() if newest_event else '-'}",
                f"rates\t{PRICING}, {len(rates)} Claude row(s)",
                f"caller\t{caller.arn or '(failed)'}",
            ]
        )

        rep.h1("2. By model")
        if not active:
            rep.text("No invocation and no token in the window.")
        else:
            rows = ["MODEL\tINVOCATIONS\tINPUT\tOUTPUT\tCACHE READ\tCACHE WRITE\tUSD"]
            for model in active:
                t = totals[model]
                price = usd(sum(cost[model])) if model in cost else "unpriced"
                rows.append(
                    f"{model}\t{int(t['Invocations'])}\t{int(t['InputTokenCount'])}\t"
                    f"{int(t['OutputTokenCount'])}\t{int(t['CacheReadInputTokenCount'])}\t"
                    f"{int(t['CacheWriteInputTokenCount'])}\t{price}"
                )
            rows.append(
                f"all\t{int(sum(totals[m]['Invocations'] for m in active))}\t"
                + "\t".join(str(int(sum(totals[m][k] for m in active))) for k in TOKENS)
                + f"\t{usd(total_usd)}"
            )
            rep.tabulate(rows)
            for model, why in sorted(unpriced.items()):
                rep.line(f"unpriced: {model} - {why}")

        rep.h1("3. By day")
        if not month_mode:
            rep.text("A window, not a month: the totals above are one bucket.")
        elif not by_day:
            rep.text("No day in the month carried a Bedrock invocation.")
        else:
            rows = ["DAY (UTC)\tINVOCATIONS\tINPUT\tOUTPUT\tCACHE READ\tCACHE WRITE\tUSD"]
            for day in sorted(by_day):
                spent, counts = 0.0, defaultdict(float)
                for model, metrics in by_day[day].items():
                    for k, v in metrics.items():
                        counts[k] += v
                    _, key = model_key(model)
                    if model in cost and key in rates:
                        spent += sum(metrics[t] * rates[key][n] / 1e6 for n, t in enumerate(TOKENS))
                rows.append(
                    f"{day}\t{int(counts['Invocations'])}\t"
                    + "\t".join(str(int(counts[k])) for k in TOKENS)
                    + f"\t{usd(spent)}"
                )
            rep.tabulate(rows)

        rep.h1("4. Where the money went")
        if not total_usd:
            rep.text("Nothing priced in the window.")
        else:
            rep.tabulate(
                ["COMPONENT\tUSD\tSHARE"]
                + [
                    f"{name}\t{usd(value)}\t{100 * value / total_usd:.0f}%"
                    for name, value in zip(("input", "output", "cache read", "cache write"), parts)
                ]
            )
            rep.text(
                "\nCache writes are priced at the 5-minute rate. If the client wrote with the 1-hour "
                "TTL,\nthat row is an underestimate, and Cost Explorer is where the two are told apart."
            )

        rep.h1("5. The two channels")
        rows = ["MODEL\tCLOUDTRAIL OK\tCLOUDWATCH INVOCATIONS"]
        for model in sorted(set(trail_ok) | set(active)):
            rows.append(f"{model}\t{trail_ok.get(model, 0)}\t{int(totals[model]['Invocations'])}")
        rep.tabulate(rows)
        rep.text(f"""
refusals, CloudTrail (no modelId on a denied call) : {sum(trail_denied.values())}  {dict(trail_denied) or ""}
refusals, CloudWatch InvocationClientErrors      : {int(aggregate["InvocationClientErrors"])}

The two refusal counts are not expected to match: on 2026-09-12 one hour held 18
AccessDenied events against 6 client errors. Only the successful invocations reconcile.""")

        rep.h1("6. Checks")
        rep.checks_table(checks)

        rep.h1("7. Calls that failed")
        failed_calls_epilogue(rep, errors)

    for model in active:
        price = f"USD {usd(sum(cost[model]))}" if model in cost else "unpriced"
        note(
            f"  {model:48} {int(totals[model]['Invocations']):>5} inv  "
            f"{int(totals[model]['OutputTokenCount']):>9} out  "
            f"{int(totals[model]['CacheWriteInputTokenCount']):>9} cache-write  {price}"
        )
    note(f"  {start.isoformat()} to {end.isoformat()}: USD {usd(total_usd)} computed, not billed")
    n_fail = checks.n_fail()
    note(
        f"wrote {out_label}",
        f"checks: {len(checks.rows) - n_fail} passed or noted, {n_fail} FAILED"
        if n_fail
        else "all checks passed",
    )
    if n_fail:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
