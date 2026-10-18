#!/usr/bin/env -S uv run --quiet
# bedrock-scope.py - the Bedrock scope this repository DECLARES, against what AWS actually does.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/bedrock-scope.py                       # sandbox
#             ./aws/bedrock-scope.py awsds-infra-staging   # any awsds-* profile
#   writes:   aws/output/bedrock-scope.txt   (untracked - see .gitignore)
#   reads:    bedrock:ListInferenceProfiles, GetInferenceProfile, GetFoundationModel,
#             GetFoundationModelAvailability, GetAccountDataRetention; account:ListRegions;
#             sts:GetCallerIdentity. Every one is a read: this script creates nothing, changes
#             nothing and invokes no model.
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS FILE EXISTS. Stage 6e's scoped set is ONE LIST WITH SEVERAL CONSUMERS, and two of the
# facts it rests on are AWS's rather than ours:
#
#   - WHICH REGIONS A PROMPT IS PROCESSED IN. Every scoped model is invocable only through a
#     cross-region `us.` inference profile, and AWS owns that routing. It can add a region under a
#     pinned model id, with no diff anywhere in this repository. Two controls are written against
#     the routing as it was last read - the SCP's region condition, and the account's data
#     retention mode, which is per region - so a routing change silently invalidates both. This is
#     the drift nothing else here can see.
#   - WHETHER A MODEL IS STILL ENABLED. A model is invocable only while the account holds an
#     agreement for it. An agreement can be deleted, and a model can be gated commercially with
#     every other reading still green (AWS_STATE.md EXC-08).
#   - WHEN A MODEL IS RETIRED. The provider moves a model to LEGACY and AWS publishes the dates on
#     the foundation model, while its `us.` profile keeps reading ACTIVE - so BS-2 stays green.
#     Sonnet 4.5 went LEGACY on 2026-10-08 and the only signal was an AWS Health e-mail.
#
# THE DECLARATION IS THE SCP, NOT THIS SCRIPT. terraform-live/identity/org-policies/policies/
# awsds-org-scp-ou-interactive.json carries both halves in the two statements Stage 6e decision 15
# added: the six ARNs of DenyBedrockInvocationOutsideTheScopedModels' NotResource, and the region
# list of DenyBedrockReadsOutsideTheRoutedRegions' condition. Reading them from there rather than
# from a constant is the point - a script with its own copy is one more consumer to keep in step
# (Lesson 33), and the SCP is the one copy that is also a control.
#
# WHAT A FAILURE HERE MEANS, per check, because they are different faults:
#
#   BS-3  AWS routes to a region the SCP does not name -> invocation is DENIED by our own
#         statement, loudly, at the first prompt. Repair: widen the region list, then declare the
#         retention mode there (runbook M1) before anything is invoked.
#   BS-4  AWS stopped routing to a named region -> nothing breaks; the statement is merely wider
#         than it needs to be. Narrow it at leisure.
#   BS-5  a scoped model has no agreement -> that model refuses at the first prompt with
#         "not available for this account", which names neither this policy nor the grant.
#   BS-6  a region reads anything but `none` -> zero retention is not declared where a prompt may
#         be processed. This is the requirement Stage 6e exists to meet, and it fails silently:
#         nothing refuses, the prompt is simply retained under the vendor's default.
#   BS-7  the four consumers disagree -> the list drifted. Which one is wrong is a reading, not a
#         verdict: this script reports the difference and names both sides.
#   BS-8  a scoped model is past ACTIVE -> a note while it is LEGACY, a failure once its public
#         extended access begins (the provider sets a higher price) or it is EOL. A LEGACY model
#         may also stop answering an account that has not called it for 15 days, which no reading
#         shows (model-lifecycle-legacy page, read 2026-10-11). Repair: Stage 6e decision 17's
#         order - add the successor to the SCP and the grant, release the image, then remove.

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.bedrockscope import (
    GRANT_VARS,
    SCP_PATH,
    SID_REGIONS,
    grant_models,
    scp_declaration,
    settings_pins,
)
from awslib.devenvrecipe import SETTINGS
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "bedrock-scope.txt"

DEFAULT_PROFILE = "awsds-infra-sandbox-1"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)
    profile = argv[0] if argv else DEFAULT_PROFILE

    errors = ErrorLog()
    callers = profiles.preflight([profile], errors, out_label=out_label)
    if not callers:
        return 1
    cli = AwsCli(profile=profile, region=context.REGION, errors=errors)

    checks = Checks()

    # -------------------------------------------------------- what the repository declares
    declared, declared_regions, why = scp_declaration(ctx.repo_root / SCP_PATH)
    if declared is None or declared_regions is None:
        checks.note("BS-1", "the SCP declares the scope", why)
        with open(out_path, "w", encoding="utf-8") as stream:
            rep = Report(stream)
            rep.banner("The declared Bedrock scope, against AWS")
            rep.text(f"generated : {context.utc_stamp()}\nprofile   : {profile}\n")
            rep.h1("Checks")
            rep.checks_table(checks)
        note(f"wrote {out_label}", why)
        return 2 if checks.n_fail() else 0
    checks.ok(
        "BS-1",
        "the SCP declares the scope",
        f"{len(declared)} model(s), {len(declared_regions)} region(s)",
    )

    # ------------------------------------------------------------------- what AWS actually does
    live_profiles = {}
    routed: dict[str, list] = {}
    agreements: dict[str, str] = {}
    lifecycles: dict[str, dict] = {}

    res = cli.run(
        "bedrock",
        "list-inference-profiles",
        "--query",
        "inferenceProfileSummaries[].[inferenceProfileId,status]",
        "--output",
        "text",
    )
    if res.ok:
        for line in res.text.splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                live_profiles[parts[0]] = parts[1]

    for model, profile_id in sorted(declared.items()):
        res = cli.run(
            "bedrock",
            "get-inference-profile",
            "--inference-profile-identifier",
            profile_id,
            "--query",
            "models[].modelArn",
            "--output",
            "text",
        )
        if res.ok and res.text:
            routed[profile_id] = sorted(
                {arn.split(":")[3] for arn in res.text.split() if arn.count(":") >= 4}
            )
        res = cli.run(
            "bedrock",
            "get-foundation-model-availability",
            "--model-id",
            model,
            "--query",
            "agreementAvailability.status",
            "--output",
            "text",
        )
        agreements[model] = res.text.strip() if res.ok else "(unreadable)"
        res = cli.run(
            "bedrock",
            "get-foundation-model",
            "--model-identifier",
            model,
            "--query",
            "modelDetails.modelLifecycle",
            "--output",
            "json",
        )
        if res.ok and res.stdout.strip():
            lifecycles[model] = json.loads(res.stdout) or {}

    # BS-2 - every declared profile exists and is ACTIVE.
    bad = [
        f"{p}={live_profiles.get(p, 'absent')}"
        for p in sorted(set(declared.values()))
        if live_profiles.get(p) != "ACTIVE"
    ]
    if live_profiles and bad:
        checks.fail("BS-2", "every declared profile is ACTIVE", ", ".join(bad))
    elif live_profiles:
        checks.ok("BS-2", "every declared profile is ACTIVE", f"{len(declared)} profile(s)")
    else:
        checks.note("BS-2", "every declared profile is ACTIVE", "the profile list did not read")

    # BS-3 / BS-4 - the routing, against the region list the SCP condition names.
    live_regions = sorted({r for regs in routed.values() for r in regs})
    if not routed:
        checks.note("BS-3", "AWS routes only where the SCP permits", "no profile was readable")
        checks.note("BS-4", "the SCP names no unused region", "no profile was readable")
    else:
        extra = [r for r in live_regions if r not in declared_regions]
        if extra:
            checks.fail(
                "BS-3",
                "AWS routes only where the SCP permits",
                f"routed and NOT in the SCP: {', '.join(extra)} - invocation is denied there by "
                f"{SID_REGIONS}, and the retention mode is not declared there either",
            )
        else:
            checks.ok(
                "BS-3", "AWS routes only where the SCP permits", ", ".join(live_regions) or "none"
            )
        unused = [r for r in declared_regions if r not in live_regions]
        if unused:
            checks.note(
                "BS-4",
                "the SCP names no unused region",
                f"named and not routed to: {', '.join(unused)} - wider than it needs to be, "
                "nothing is broken",
            )
        else:
            checks.ok("BS-4", "the SCP names no unused region", ", ".join(declared_regions))

    # BS-5 - every scoped model still holds an agreement.
    not_enabled = [f"{m}={s}" for m, s in sorted(agreements.items()) if s != "AVAILABLE"]
    if not_enabled:
        checks.fail(
            "BS-5",
            "every scoped model holds an agreement",
            ", ".join(not_enabled) + " - that model refuses at the first prompt",
        )
    else:
        checks.ok(
            "BS-5", "every scoped model holds an agreement", f"{len(agreements)} model(s) AVAILABLE"
        )

    # BS-6 - the retention mode, in every ENABLED region rather than in the routed ones. Stage 6e
    # decision 16: the routing can move, so the invariant is written to survive it.
    res = cli.run(
        "account",
        "list-regions",
        "--region-opt-status-contains",
        "ENABLED",
        "ENABLED_BY_DEFAULT",
        "--query",
        "Regions[].RegionName",
        "--output",
        "text",
    )
    retention: dict[str, str] = {}
    if res.ok and res.text:
        for region in sorted(res.text.split()):
            rcli = AwsCli(profile=cli.profile, region=region, errors=errors)
            r = rcli.run(
                "bedrock",
                "get-account-data-retention",
                "--query",
                "mode",
                "--output",
                "text",
                tolerate="AccessDenied|UnrecognizedClientException|could not be found",
            )
            retention[region] = (r.text.strip() or "(unreadable)") if r.ok else "(unreadable)"
        wrong = [f"{r}={m}" for r, m in sorted(retention.items()) if m != "none"]
        if wrong:
            checks.fail(
                "BS-6",
                "every enabled region declares mode none",
                ", ".join(wrong) + " - a prompt processed there is retained under the vendor "
                "default, and nothing refuses",
            )
        else:
            checks.ok(
                "BS-6",
                "every enabled region declares mode none",
                f"{len(retention)} region(s)",
            )
    else:
        checks.note(
            "BS-6", "every enabled region declares mode none", "the region list did not read"
        )

    # BS-7 - the four consumers of one list agree with each other.
    grant = grant_models(ctx.repo_root / GRANT_VARS)
    pins = settings_pins(ctx.repo_root / SETTINGS)
    if grant is None or pins is None:
        checks.note("BS-7", "the repository's copies agree", "a file was unreadable")
    else:
        problems = []
        if grant != declared:
            problems.append(f"{GRANT_VARS} maps {sorted(grant.items())}")
        pinned = set(pins.values())
        if pinned - set(declared.values()):
            problems.append(f"{SETTINGS} pins {sorted(pinned - set(declared.values()))}")
        if problems:
            checks.fail("BS-7", "the repository's copies agree", "; ".join(problems))
        else:
            checks.ok(
                "BS-7",
                "the repository's copies agree",
                f"SCP, {GRANT_VARS.split('/')[-3]}/{GRANT_VARS.split('/')[-2]} and the image pins",
            )

    # BS-8 - every scoped model is ACTIVE; a LEGACY one is a note until its extended access begins.
    now = datetime.now(UTC)
    legacy, retired = [], []
    for model in sorted(declared):
        lc = lifecycles.get(model)
        if lc is None:
            continue
        status = lc.get("status", "(none)")
        if status == "ACTIVE":
            continue
        dates = ", ".join(
            f"{label} {lc[key][:10]}"
            for label, key in (
                ("legacy", "legacyTime"),
                ("extended access", "publicExtendedAccessTime"),
                ("EOL", "endOfLifeTime"),
            )
            if lc.get(key)
        )
        extended = lc.get("publicExtendedAccessTime")
        past_extended = extended is not None and datetime.fromisoformat(extended) <= now
        entry = f"{model} {status} ({dates or 'no dates published'})"
        if status == "LEGACY" and not past_extended:
            legacy.append(entry)
        else:
            retired.append(entry)
    unread = sorted(set(declared) - set(lifecycles))
    if retired:
        checks.fail(
            "BS-8",
            "every scoped model is ACTIVE",
            "; ".join(retired) + " - past the price change or the end; move the set (decision 17)",
        )
    elif legacy:
        checks.note(
            "BS-8",
            "every scoped model is ACTIVE",
            "; ".join(legacy) + " - a LEGACY model may refuse an account idle for 15 days",
        )
    elif unread:
        checks.note("BS-8", "every scoped model is ACTIVE", f"unreadable: {', '.join(unread)}")
    else:
        checks.ok("BS-8", "every scoped model is ACTIVE", f"{len(lifecycles)} model(s)")

    # ------------------------------------------------------------------------------ the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        rep.banner("The declared Bedrock scope, against what AWS does")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {profile}
declared  : {SCP_PATH}
produced  : aws/bedrock-scope.py   (index: aws/INDEX.md)

SECTIONS
  1. What the repository declares
  2. What AWS does
  3. The data retention mode, region by region
  4. Checks
  5. Calls that failed

HOW TO READ THIS FILE
  - THE SCP IS THE DECLARATION, not this script. Both halves come out of the two
    statements Stage 6e decision 15 added, so there is no fifth copy of the list.
  - BS-3 IS THE ONE THAT COSTS A SESSION. A region AWS routes to and the SCP does not
    name is an invocation denied by our own statement, and the retention mode is not
    declared there either. Widen the list, declare the mode (runbook M1), then invoke.
  - BS-6 FAILS SILENTLY IN PRODUCTION. Nothing refuses when a region reads `inherit`;
    the prompt is simply retained under the vendor's default. That is the requirement
    Stage 6e exists to meet.
  - NONE OF THIS SAYS A PRINCIPAL CAN INVOKE. Reach is an intersection (Lesson 28) and
    the only instrument for it is a call - runbook claude-code-sagemaker.md M6.

This file is not versioned (aws/output/ is in .gitignore). Regenerate it rather than
trusting a stale copy.""")

        rep.h1("1. What the repository declares")
        rep.tabulate(["MODEL\tPROFILE"] + [f"{m}\t{p}" for m, p in sorted(declared.items())])
        rep.line()
        rep.line(f"routed regions the SCP permits: {', '.join(declared_regions)}")

        rep.h1("2. What AWS does")
        rows = ["PROFILE\tSTATUS\tROUTES TO"]
        for model, pid in sorted(declared.items()):
            rows.append(
                f"{pid}\t{live_profiles.get(pid, 'absent')}\t{', '.join(routed.get(pid, [])) or '-'}"
            )
        rep.tabulate(rows)
        rep.line()
        rows = ["MODEL\tAGREEMENT\tLIFECYCLE\tLEGACY\tEXTENDED ACCESS\tEOL"]
        for m, s in sorted(agreements.items()):
            lc = lifecycles.get(m, {})
            rows.append(
                f"{m}\t{s}\t{lc.get('status', '(unreadable)')}\t"
                + "\t".join(
                    (lc.get(k) or "-")[:10]
                    for k in ("legacyTime", "publicExtendedAccessTime", "endOfLifeTime")
                )
            )
        rep.tabulate(rows)

        rep.h1("3. The data retention mode, region by region")
        if retention:
            rep.tabulate(["REGION\tMODE"] + [f"{r}\t{m}" for r, m in sorted(retention.items())])
        else:
            rep.line("(the enabled-region list did not read)")

        rep.h1("4. Checks")
        rep.checks_table(checks)

        rep.h1("5. Calls that failed")
        failed_calls_epilogue(rep, errors)

    note(f"wrote {out_label}")
    if checks.n_fail():
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
