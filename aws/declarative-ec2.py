#!/usr/bin/env -S uv run --quiet
# declarative-ec2.py - the four EC2 settings awsds-org-declarative-ec2 declares, read back
# from each account, one row per account per attribute.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/declarative-ec2.py                       every awsds-* profile
#             ./aws/declarative-ec2.py awsds-infra-dev ...   only the profiles named
#             python3 aws/declarative-ec2.py -              no --profile: CloudShell (no uv
#                                                           there; bring the aws/ folder),
#                                                           for the three accounts with none
#   writes:   aws/output/declarative-ec2.txt   (untracked - see .gitignore)
#   reads:    ec2:GetImageBlockPublicAccessState, ec2:GetSnapshotBlockPublicAccessState,
#             ec2:GetSerialConsoleAccessStatus, ec2:GetInstanceMetadataDefaults,
#             organizations:DescribeEffectivePolicy, sts:GetCallerIdentity.
#             This script never creates, updates or deletes anything.
#   exits:    0 every measured account matches the document | 1 a call failed or a value
#             does not match
#
# WHY THIS EXISTS AND THE BATTERY DOES NOT COVER IT. A declarative policy is enforced in the
# SERVICE's control plane, not in authorization - so it produces no "explicit deny", names no
# policy id, and governs service-linked roles, which no SCP does. The SCP battery can only
# show that an account is REFUSED when it tries to change one of these settings. It cannot
# show what the setting IS, and the setting is the control. That is this script.
#
# The two instruments answer different questions and both are needed:
#
#   ./aws/probes/scp-battery.py --phase decl   does the account get refused, and does it
#                                              receive OUR exception message?
#   ./aws/declarative-ec2.py                   is the value actually what the document says?
#
# WHAT MAKES THE SECOND QUESTION NON-OBVIOUS: attaching this policy CHANGES EXISTING STATE in
# every account it reaches, which none of 7.5/7.6/7.7's documents do - those only constrain
# future calls. Detaching rolls each attribute back to whatever it was before the attach
# (AWS Organizations user guide). So "attached" and "in effect" are two facts here, and only
# the second one is a control.
#
# TWO VOCABULARIES, and they do not match, which is the trap this script exists to absorb:
# the policy document writes `block_all_sharing` and `disabled`; the EC2 API answers
# `block-all-sharing` and `false`. The expected values below are therefore written in the
# API's spelling and mapped by hand - deriving them from the JSON would be a translation
# nobody reviews.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - MANAGEMENT, LOG ARCHIVE and AUDIT have no profile on this laptop and never will
#     (guiding principle 1). Run this with `-` in CloudShell inside each and record the three
#     answers by hand. MANAGEMENT MATTERS HERE IN A WAY IT DOES NOT ELSEWHERE: it is exempt
#     from SCPs and RCPs, but AWS documents no such exemption for declarative policies, so a
#     root attach is expected to reach it. That expectation is UNMEASURED until someone runs
#     this there, and it is the one reading that decides it.
#   - `Staging` is not vended; every Sandbox beyond the first has no profile until Stage 14.
#   - EXC-01, the SUSPENDED `Sandbox` at the organization root, is not this project's.

from __future__ import annotations

import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Report, note

OUT_NAME = "declarative-ec2.txt"

# ------------------------------------------------------------------ the four attributes
#
# name | the aws ec2 sub-command | the --query that isolates the value | expected (API spelling)
#
# The expected column is the DOCUMENT translated into what the API answers. Change the
# document and this list has to change with it - which is deliberate: the translation is
# where a mistake would otherwise hide, so it is written where a reviewer will see it.
ATTRS = [
    (
        "image_block_public_access",
        "get-image-block-public-access-state",
        "ImageBlockPublicAccessState",
        "block-new-sharing",
    ),
    (
        "snapshot_block_public_access",
        "get-snapshot-block-public-access-state",
        "State",
        "block-all-sharing",
    ),
    (
        "serial_console_access",
        "get-serial-console-access-status",
        "SerialConsoleAccessEnabled",
        "False",
    ),
    (
        "instance_metadata_defaults.http_tokens",
        "get-instance-metadata-defaults",
        "AccountLevel.HttpTokens",
        "required",
    ),
]


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    rows: list = []
    bad = 0

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("EC2 declarative policy - the settings, read back per account")
        rep.text(f"""generated : {context.utc_stamp()}
document  : terraform-live/identity/org-policies/policies/awsds-org-declarative-ec2.json
profiles  : {source}
region    : {context.REGION}
produced  : aws/declarative-ec2.py   (index: aws/INDEX.md)

HOW TO READ THIS FILE
  - A `MISMATCH` row is not necessarily a failure of the policy. Before the document
    is attached EVERY row mismatches, and that is the before-reading. After the
    attach, a mismatch is either an account the attachment does not reach or a
    setting that was changed and did not roll forward - both are findings.
  - `not-set` IS AN ANSWER, not an error: it is what an account returns for an
    attribute nobody has ever configured. It is reported as a mismatch, because a
    control that is not set is not a control.
  - THE MEASURED SET IS NOT THE ORGANIZATION. Section 4 names the accounts this
    laptop cannot reach; one of them is MANAGEMENT, and whether a root-attached
    declarative policy reaches it is UNDECIDED by AWS documentation.
  - Section 3 is the effective policy as Organizations computes it, which answers a
    different question from section 2: what the account is SUPPOSED to have, versus
    what EC2 actually reports. Those disagree while an attachment propagates.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        rep.h1("1. Which accounts were measured, and as whom")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        rep.h1("2. The settings, per account")
        for c in live:
            cli = cli_for(c.profile)
            for attr_name, subcommand, query, want in ATTRS:
                res = cli.call("ec2", subcommand, "--query", query, "--output", "text")
                if not res.ok:
                    errors.add(("ec2", subcommand), res.merged, c.profile)
                    rows.append(f"{c.profile}\t{attr_name}\t{want}\t(call failed)\tCALL FAILED")
                    bad += 1
                    continue
                got = res.stdout
                if not got or got == "None":
                    got = "not-set"
                if got == want:
                    rows.append(f"{c.profile}\t{attr_name}\t{want}\t{got}\tok")
                else:
                    rows.append(f"{c.profile}\t{attr_name}\t{want}\t{got}\tMISMATCH")
                    bad += 1
        rep.tabulate(["PROFILE\tATTRIBUTE\tEXPECTED\tACTUAL\tVERDICT"] + rows)

        rep.text("""
EXPECTED is awsds-org-declarative-ec2.json translated into the spelling the EC2 API
answers in. The document says `block_all_sharing` and `disabled`; the API says
`block-all-sharing` and `False`. That mapping is written by hand in this script and
has to be updated with the document - it is the one place the two can silently
disagree.""")

        rep.h1("3. The effective declarative policy, as Organizations computes it")
        for c in live:
            cli = cli_for(c.profile)
            rep.line(f"--- {c.profile} ---")
            rep.line()
            res = cli.call(
                "organizations",
                "describe-effective-policy",
                "--policy-type",
                "DECLARATIVE_POLICY_EC2",
                "--query",
                "EffectivePolicy.PolicyContent",
                "--output",
                "text",
            )
            if not res.ok:
                if (
                    "EffectivePolicyNotFoundException" in res.merged
                    or "PolicyTypeNotEnabledException" in res.merged
                ):
                    rep.text("""no effective EC2 declarative policy for this account.
Before the attach this is the expected answer; after it, it is a finding.

""")
                else:
                    rep.line(res.merged)
                    rep.line()
                    errors.add(
                        ("organizations", "describe-effective-policy"), res.merged, c.profile
                    )
            elif not res.stdout or res.stdout in ("{}", "None"):
                # Measured 2026-08-14: with the policy type ENABLED but nothing attached,
                # Organizations answers `{}` rather than raising
                # EffectivePolicyNotFoundException. An empty object and a missing policy are
                # the same fact and neither is an error - which is worth saying, because a
                # script that only handled the exception would print `{}` as if it were
                # content.
                rep.text("""{}  - no EC2 declarative policy reaches this account.
Before the attach this is the expected answer; after it, it is a finding.

""")
            else:
                rep.line(res.stdout)
                rep.line()

        rep.text("""Section 2 is EC2 reporting the setting; this section is Organizations reporting the
intent. A disagreement between them means an attachment that has not taken effect,
which is a state that exists and resolves on its own - re-run before acting on it.""")

        rep.h1("4. The accounts this laptop cannot reach")
        rep.text("""MANAGEMENT, LOG ARCHIVE and AUDIT hold no project persona (guiding principle 1).
Reach them as `AWS Control Tower Admin` through the access portal and run, in
CloudShell inside each (no uv there - bring the aws/ folder and use python3):

    python3 aws/declarative-ec2.py -

MANAGEMENT IS THE ONE THAT MATTERS AND IT IS NOT A FORMALITY. SCPs and RCPs skip the
management account by design; AWS documents NO SUCH EXEMPTION for declarative
policies, and they are enforced in the service control plane rather than in
authorization, which is where that exemption lives. So a root attach is EXPECTED to
reach Management - the first time in this project that a root-attached document
does - and the only way to find out is to read it there. Record the answer in
docs/log/log-stage-01c-preventive-policies.md.

Also absent, and none is a gap: `Staging` (not vended), every Sandbox beyond the
first (no profile until Stage 14), and EXC-01, the suspended `Sandbox` that is not
this project account.""")

        rep.h1("5. Calls that failed")
        if errors:
            rep.line(errors.text())
            rep.line()
            rep.line(
                f"If a profile did not authenticate:  aws sso login --sso-session "
                f"{context.SSO_SESSION}"
            )
        else:
            rep.line("None. Every call in this report returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/declarative-ec2.py")

    # ---------------------------------------------------------------------------------- run
    n_all = len(rows)
    note("")
    note(f"wrote {out_label}  ({n_all - bad} of {n_all} readings match the document)")
    if errors or bad > 0:
        note("MISMATCH or failed call present - see sections 2 and 5.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
