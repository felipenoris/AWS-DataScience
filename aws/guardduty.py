#!/usr/bin/env -S uv run --quiet
# guardduty.py - Stage 15's evidence, per account, side by side: the detector each account
# holds (org-wide coverage is only meaningful read across every account at once - one
# account silently uncovered is exactly the finding), every protection-plan feature on each
# detector (they all arrive ON except Runtime Monitoring - Stage 15 step 0 - and step 3
# switches them off, so any ENABLED reading is either drift or an unfinished step 3, and
# the two are supposed to look the same here), and the delegated-administrator
# registration visible from Identity.
#
# CARVED OUT OF ./aws/vpn.py ON 2026-08-18, the day GuardDuty left Stage 4 for Stage 15.
# The check ids there were VP-8; they are GD-* here, and VP-8 is RETIRED in vpn.py rather
# than renumbered - the Stage 4 log's readings cite it by that name.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/guardduty.py                  # every awsds-* profile
#             ./aws/guardduty.py awsds-infra-identity   # only the ones named
#             python3 aws/guardduty.py -          # CloudShell, ambient credentials
#   writes:   aws/output/guardduty.txt   (untracked - see .gitignore)
#   reads:    guardduty:ListDetectors, GetDetector,
#             organizations:ListDelegatedAdministrators, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - GuardDuty's ORG CONFIGURATION (auto-enable ALL, the per-plan NONE list) lives in
#     Audit, which holds no CLI profile (D33/D34): it is verified in the Audit console or
#     CloudShell, never here. This file reads only the members' detectors and the
#     delegation registration.
#   - Management's own detector (Stage 15 step 2a, decision 3) is outside every profile
#     here; read it from its CloudShell.
#   - The findings route (step 4) is proven by a sample finding arriving by e-mail, not by
#     a describe call (Lesson 20).

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "guardduty.txt"

IDENTITY_PROFILE = "awsds-infra-identity"

# The optional protection plans. Enabling GuardDuty turns on EVERY ONE OF THEM except
# Runtime Monitoring (documented 2026-08-18, Stage 15 step 0), so step 3 is a SWITCH-OFF
# and not an omission, and GD-3 is written against the whole set rather than the two the
# plan first named (S3 Protection, Malware Protection for EC2 - Stage 11 step 4's pair).
# THE CHECK IS NOT DRIVEN BY THIS TUPLE: the report prints every feature the API returns
# and the check fails on any that reads ENABLED, so a protection plan AWS adds next year
# is measured on the day it appears instead of staying invisible until somebody remembers
# to extend a constant (Lesson 23). The names below only fix the report's column order;
# anything unknown is appended in the API's own order.
KNOWN_FEATURES = (
    "S3_DATA_EVENTS",
    "EKS_AUDIT_LOGS",
    "EBS_MALWARE_PROTECTION",
    "RDS_LOGIN_EVENTS",
    "LAMBDA_NETWORK_LOGS",
    "RUNTIME_MONITORING",
)


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

    # ----------------------------------------------------------------- detectors, per account
    gd_rows: list = []  # (profile, detector id or '-', status, protection-plan summary)
    for p in live:
        cli = cli_for(p)
        note(f"measuring {p} ...")
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
            gd_rows.append((p, "-", "(call failed)", "-"))
            continue
        det = res.stdout.strip()
        if not det or det == "None":
            gd_rows.append((p, "-", "no detector", "-"))
            continue
        r = cli.run(
            "guardduty", "get-detector", "--detector-id", det, "--output", "json", log=False
        )
        if not r.ok:
            logerr(p, f"guardduty get-detector {det}", r.stderr)
            gd_rows.append((p, det, "(call failed)", "-"))
            continue
        doc = json.loads(r.stdout or "{}")
        status = doc.get("Status", "?")
        feat = {f.get("Name"): f.get("Status") for f in doc.get("Features", [])}
        ordered = [n for n in KNOWN_FEATURES if n in feat] + [
            n for n in feat if n not in KNOWN_FEATURES
        ]
        plans = " ".join(f"{n}={feat[n]}" for n in ordered) or "(no features reported)"
        gd_rows.append((p, det, status, plans))

    # ----------------------------------------------------------- the delegation, one read
    delegation = "(not read)"
    if IDENTITY_PROFILE in live:
        cli = cli_for(IDENTITY_PROFILE)
        res = cli.run(
            "organizations",
            "list-delegated-administrators",
            "--service-principal",
            "guardduty.amazonaws.com",
            "--query",
            "DelegatedAdministrators[].[Id,Name,Status]",
            "--output",
            "text",
            log=False,
            tolerate="AccessDenied",
        )
        if res.tolerated:
            delegation = "(read denied from Identity - check from Management)"
        elif res.ok:
            delegation = res.stdout.strip() or "(none registered)"
        else:
            logerr(IDENTITY_PROFILE, "organizations list-delegated-administrators", res.stderr)
            delegation = "(call failed)"

    # -------------------------------------------------------------------------- the checks
    # GD-1: the delegation is registered to Audit (step 1). Before Stage 15 the absence is
    # the expected state; after it, an empty registration is the whole stage undone.
    if IDENTITY_PROFILE in live:
        if delegation == "(none registered)":
            checks.note(
                "GD-1",
                "delegated administrator",
                "none registered - expected before Stage 15 step 1.",
            )
        elif delegation == "(call failed)":
            checks.fail(
                "GD-1",
                "delegated administrator",
                "the delegation read itself failed (section 5) - a failed read is not an "
                "expected absence (Lesson 13); rerun before reading anything else here.",
            )
        elif delegation.startswith("(read denied"):
            checks.note("GD-1", "delegated administrator", delegation)
        elif "Audit" in delegation and "ACTIVE" in delegation:
            checks.ok("GD-1", "delegated administrator", "guardduty.amazonaws.com -> Audit, ACTIVE")
        else:
            checks.fail(
                "GD-1",
                "delegated administrator",
                f"{delegation} - Stage 15 step 1 names Audit, and the delegated "
                "administrator must be the same account in every Region.",
            )

    # GD-2: a detector ENABLED in every measured account (step 2's auto-enable ALL). One
    # account without one, while others have theirs, is the gap org-wide enablement exists
    # to close - with one documented exception: up to 24 h of propagation.
    detectors = [r for r in gd_rows if r[1] != "-" and r[2] not in ("(call failed)",)]
    if not detectors:
        checks.note(
            "GD-2",
            "GuardDuty detectors",
            "none in any measured account - expected before Stage 15 step 1.",
        )
    else:
        for p, det, status, plans in gd_rows:
            if det == "-" and status == "no detector":
                checks.fail(
                    "GD-2",
                    f"GuardDuty in {p}",
                    "no detector while other accounts have one - auto-enable did not reach "
                    "this account. Within 24 h of step 2 this is the documented propagation "
                    "window (a Risks row), not drift; standing longer, it is verification "
                    "(i)'s residual failing.",
                )
            elif det != "-" and status != "ENABLED":
                checks.fail("GD-2", f"GuardDuty in {p}", f"detector {det} status {status}")
            elif det != "-":
                checks.ok("GD-2", f"GuardDuty in {p}", "ENABLED")

    # GD-3: every optional protection plan off, on every detector this file can read
    # (steps 0/3). They arrive ENABLED, so this check reads red between step 1 and the end
    # of step 3 by design - and if decision 1's option (b) (the trial window) is ever taken
    # instead, FLIP THIS CHECK rather than living with the red: a decision left only in
    # prose is measured by nobody (the VP-7 precedent, Stage 4).
    for p, det, status, plans in gd_rows:
        if det == "-" or status != "ENABLED":
            continue
        bad_feat = [tok.split("=", 1)[0] for tok in plans.split() if tok.endswith("=ENABLED")]
        if bad_feat:
            checks.fail(
                "GD-3",
                f"protection plans in {p}",
                f"{' '.join(bad_feat)} ENABLED - every optional plan arrives ON and step 3 "
                "switches it off; the paid ones are decided in Stage 11 step 4 against a "
                "real bill, not before. In a MEMBER account the fix is UpdateMemberDetectors "
                "from Audit; on AUDIT'S OWN detector UpdateDetector is denied by "
                "DenyGuardDutyTampering - that is decision 1, not a console click.",
            )
        else:
            checks.ok("GD-3", f"protection plans in {p}", "foundational detection only")

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("GuardDuty - the Stage 15 evidence: detectors, plans, the delegation")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/guardduty.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. Detectors and protection plans, per account
  3. The accounts nothing here is measuring
  4. CHECKS
  5. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 15 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 3 names what nothing here
    reached, GuardDuty's org configuration in Audit above all.
  - GD-3 READS RED BETWEEN STEP 1 AND THE END OF STEP 3 BY DESIGN: the plans
    arrive ON (step 0) and the switch-off is the work, so a red here during the
    sitting is the stage in progress, and the same red a week later is drift.

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
        rep.h1("2. Detectors and protection plans, per account")
        rep.tabulate(
            ["PROFILE\tDETECTOR\tSTATUS\tPROTECTION PLANS (all must be DISABLED)"]
            + [f"{p}\t{d}\t{s}\t{f}" for p, d, s, f in gd_rows]
        )
        rep.line()
        rep.line(f"delegated administrator (guardduty.amazonaws.com): {delegation}")
        rep.text("""
Delegating IS enabling (Stage 15 step 1): the registration is made from
Management, the org configuration from Audit - neither holds a profile, so this
file can only read the registration and each member's detector. Restate INV-09
in docs/AWS_STATE.md when the delegation lands, and re-run
./aws/org-trusted-access-services.py.""")

        # ==============================================================================
        rep.h1("3. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 4 as a pass.

  - GuardDuty's ORG CONFIGURATION lives in Audit, which holds no CLI profile
    (D33/D34): auto-enable ALL and the per-plan NONE list are verified in the
    Audit console or CloudShell, not here. Section 2 reads only the members'
    detectors.
  - Management's own detector is outside every profile here (step 2a,
    decision 3); read it from its CloudShell.
  - Log Archive holds no profile either; its detector arrives via auto-enable
    and is visible only from Audit's Accounts table.
  - `Staging` is unvended; every Sandbox beyond unit 1 has no profile until
    Stage 14. A vend must ARRIVE covered by auto-enable - re-run this script
    after each one (verification (i)'s residual).""")

        # ==============================================================================
        rep.h1("4. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  GD-1  the delegation registered to Audit, ACTIVE (Stage 15 step 1)
  GD-2  a detector ENABLED in every measured account (step 2; 24 h propagation
        is the one excused window)
  GD-3  EVERY optional protection plan off, on every detector readable here
        (steps 0/3). They arrive ENABLED, so this is red mid-sitting by design -
        and if the trial-window option is ever taken instead (decision 1b), FLIP
        THIS CHECK rather than living with the red: a decision left only in
        prose is measured by nobody (Stage 4's VP-7 precedent)""")

        # ==============================================================================
        rep.h1("5. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/guardduty.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 5)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 4)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
