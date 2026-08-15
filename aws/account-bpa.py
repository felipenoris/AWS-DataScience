#!/usr/bin/env -S uv run --quiet
# account-bpa.py - the ACCOUNT-level S3 Block Public Access setting, one row per account.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile below: the cached token is keyed by the
#             sso-session name, not by profile or account (see aws/INDEX.md).
#
#   run:      ./aws/account-bpa.py                       every awsds-* profile
#             ./aws/account-bpa.py awsds-infra-dev ...   only the profiles named
#             python3 aws/account-bpa.py -              no --profile: CloudShell (which has
#                                                       no uv), for the three accounts that
#                                                       have none
#   writes:   aws/output/account-bpa.txt   (untracked - see .gitignore)
#   reads:    s3control:GetPublicAccessBlock and sts:GetCallerIdentity. This script never
#             creates, updates or deletes anything - the `put` command is PRINTED, not run.
#
# WHY THIS EXISTS, and why it is worth a script rather than a loop typed once. There are two
# Block Public Access settings and they are not the same control: the BUCKET-level one, which
# Stage 2's s3-bucket module sets on every bucket IT creates, and the ACCOUNT-level one below,
# which also covers the bucket somebody creates outside that module. Only the second is a
# blanket, and it has no cross-account API: it is set from inside each account, so "every
# member account" has to be a LIST or the one account nobody had a profile for is the one
# that keeps the hole.
#
# It is read three times, which is what makes it a script:
#   - BEFORE 7.4 step 1, as Stage 1c step 7.0 step 4: the plan assumes BPA is off everywhere
#     and that assumption had never been measured. Where the Account Factory blueprint
#     already set it, half of 7.4 is a no-op.
#   - AFTER 7.4 step 1, as the confirmation that every row now reads four times `true` -
#     BEFORE 7.5 attaches the SCP that denies changing it. In the other order the deny blocks
#     the very call that enables the setting it protects, in every account at once, and the
#     repair is a detach from the management account.
#   - AT EVERY VEND, forever (D34, D35). A new account lands with BPA unset and inherits the
#     root deny the moment it enters a governed OU; from then on only the carved-out
#     InfrastructureAccess role can set it (Stage 1c decision 7). Stage 14 owes a step for
#     this, and this script is how that step is checked.
#
# ONE DELIBERATE DEVIATION from aws/INDEX.md's "one profile per script", the same one AZs.py
# takes and for the same reason: the subject is a per-account setting compared ACROSS
# accounts, so a single-profile version answers nothing. Section 1 names the identity behind
# every row, which is what the one-profile rule exists to make visible.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - MANAGEMENT, LOG ARCHIVE and AUDIT have no profile on this laptop and never will
#     (guiding principle 1; docs/ORGANIZATION.md). They are invisible here. Run this script
#     with `-` inside CloudShell in each of them, as `AWS Control Tower Admin`, and record
#     the three answers by hand - section 4 prints the exact command.
#   - `Staging` is not vended, and every Sandbox beyond the first has no profile until
#     Stage 14 gives it one. Absent, not reassuring.
#   - EXC-01, the SUSPENDED `Sandbox` at the organization root, is not this project's and
#     cannot be acted on. It has no profile and belongs in no list here.
#   - This is the ACCOUNT setting only. A bucket may still be public-blocked or not on its
#     own; that is a different call (s3api get-public-access-block --bucket).

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Report, note

OUT_NAME = "account-bpa.txt"

FLAGS = ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    # `-` runs with ambient credentials (CloudShell); it is a valid "profile list" of one.
    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    rows: list = []  # profile \t account \t 4 flags \t verdict

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Account-level S3 Block Public Access, one row per account")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}   (the setting is account-wide; the region only picks an endpoint)
produced  : aws/account-bpa.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The raw answer, per account
  3. The verdict table - all four flags, side by side
  4. The accounts this laptop cannot reach, and how to read them
  5. How to SET it, and the ordering that must not be reversed
  6. Calls that failed

HOW TO READ THIS FILE
  - `NoSuchPublicAccessBlockConfiguration` IS THE "NOT SET" ANSWER, and it is what
    to expect before Stage 1c step 7.4. It is reported as NOT SET, not as a failure.
  - THE TARGET STATE IS ALL FOUR FLAGS true, in every account. Three of four is not
    a partial pass: RestrictPublicBuckets alone still allows a public ACL, and
    BlockPublicAcls alone still allows a public bucket POLICY.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 4 names the ones this laptop
    cannot reach; an account absent from both section 3 and section 4 is an account
    nobody is measuring, which is the hole this script exists to make visible.
  - ORDER MATTERS AND IS IRREVERSIBLE-ISH: set BPA everywhere FIRST, then attach the
    SCP that denies changing it (7.5). Reversed, the deny blocks the enabling call in
    every account at once and the repair is a detach from the management account.
  - This is a point-in-time snapshot, not a source of truth: regenerate it rather
    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ------------------------------------------------------------------------------
        rep.h1("1. Which accounts were measured, and as whom")

        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )
        rep.text("""
A `(failed)` row is a profile that did not authenticate - it is EXCLUDED from
section 3 and never counted as compliant. `awsds-policy-canary` is on this list on
purpose: it is the easiest account to forget precisely because it is supposed to
stay empty, and it still has an S3 API.""")

        # ------------------------------------------------------------------------------
        rep.h1("2. The raw answer, per account")

        for c in live:
            cli = cli_for(c.profile)
            rep.h2(f"2.x {c.profile}  ({c.account})")
            res = cli.call(
                "s3control",
                "get-public-access-block",
                "--account-id",
                c.account,
                "--query",
                "PublicAccessBlockConfiguration",
                "--output",
                "json",
            )
            # cli.echo drops the --profile flag on an ambient (`-`) run, as the shell did.
            rep.line(cli.echo(("s3control", "get-public-access-block", "--account-id", c.account)))
            rep.line()
            rep.line(res.merged)
            rep.line()

            if not res.ok:
                if "NoSuchPublicAccessBlockConfiguration" in res.merged:
                    rep.text("""=> NOT SET. This is the expected answer before 7.4 step 1, and it is not an
   error: the account simply has no account-level configuration.""")
                    rows.append(f"{c.profile}\t{c.account}\t-\t-\t-\t-\tNOT SET")
                else:
                    rep.text("""=> THE CALL FAILED for another reason - see section 6. This is NOT evidence
   about the setting either way.""")
                    errors.entries.append(
                        f"[{c.profile}] aws s3control get-public-access-block\n"
                        f"    {head2(res.merged)}"
                    )
                    rows.append(f"{c.profile}\t{c.account}\t?\t?\t?\t?\tCALL FAILED")
                continue

            try:
                config = json.loads(res.stdout)
            except json.JSONDecodeError:
                config = {}
            values = {flag: str(config[flag]).lower() if flag in config else "-" for flag in FLAGS}
            if all(values[f] == "true" for f in FLAGS):
                verdict = "ALL FOUR true"
                rep.line("=> ALL FOUR true. Nothing to do here in 7.4 step 1.")
            else:
                verdict = "PARTIAL - fix"
                rep.text("""=> PARTIAL. A configuration exists but does not block everything; 7.4 step 1
   sets all four. Three of four is not a partial pass.""")
            rows.append(
                f"{c.profile}\t{c.account}\t" + "\t".join(values[f] for f in FLAGS) + f"\t{verdict}"
            )

        # ------------------------------------------------------------------------------
        rep.h1("3. The verdict table - all four flags, side by side")

        rep.tabulate(
            [
                "PROFILE\tACCOUNT\tBlockPublicAcls\tIgnorePublicAcls\tBlockPublicPolicy"
                "\tRestrictPublicBuckets\tVERDICT"
            ]
            + rows
        )
        rep.line()
        good = sum(1 for r in rows if "ALL FOUR true" in r)
        rep.text(f"""{good} of {len(rows)} measured accounts have all four flags set.
THE MEASURED SET IS NOT THE ORGANIZATION - read section 4 before reading this as a
pass. Three accounts have no profile here by design, and one account nobody
measures is exactly the hole the account-level setting exists to close.""")

        # ------------------------------------------------------------------------------
        rep.h1("4. The accounts this laptop cannot reach, and how to read them")

        rep.text("""MANAGEMENT, LOG ARCHIVE and AUDIT hold no project persona (guiding principle 1,
docs/ORGANIZATION.md), so they cannot appear above. The identity that reaches them is
`AWS Control Tower Admin` through the access portal, and the reading is done in
CloudShell inside each one:

    python3 aws/account-bpa.py -

With `-` the script uses ambient credentials and resolves the account id from
sts:GetCallerIdentity, so the same command works in all three (CloudShell has no uv;
bring the aws/ folder, whose awslib package sits beside this script). Record each
answer in docs/log/log-stage-01c-preventive-policies.md by hand - a CloudShell run
cannot write into this snapshot.

ALSO NOT HERE, and none of the three is a gap:
  - `Staging` - not vended. It gets BPA AT THE VEND, with everything else deferred
    there (Stage 1a, "What the deferral leaves owed").
  - Every Sandbox beyond the first - no profile until Stage 14 vends it one, which
    is the stage that owes a BPA step of its own.
  - EXC-01, the SUSPENDED `Sandbox` at the organization root - not this project
    account, runs nothing, cannot be acted on. Do not add it to any list.""")

        # ------------------------------------------------------------------------------
        rep.h1("5. How to SET it, and the ordering that must not be reversed")

        rep.text("""This script never writes. The command 7.4 step 1 runs, per account:

    aws s3control put-public-access-block --account-id <ACCT> --profile <PROFILE> \\
      --public-access-block-configuration \\
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

Then re-run this script: every row must read ALL FOUR true BEFORE 7.5 attaches
awsds-org-scp-baseline.json, which denies s3:PutAccountPublicAccessBlock everywhere
except the carved-out InfrastructureAccess role (Stage 1c decision 7).

AND NEVER DECLARE aws_s3_account_public_access_block IN A TERRAFORM SLICE. It looks
exactly like something that belongs in foundation/, and after the deny is attached
any apply or drift correction touching it fails from every principal except that
one. docs/plan/conventions.md carries the exclusion.""")

        # ------------------------------------------------------------------------------
        rep.h1("6. Calls that failed")

        if errors:
            rep.text("""Each entry is a call whose output is missing or unusable above. Note that
`NoSuchPublicAccessBlockConfiguration` is NOT here: it is a valid answer, reported
as NOT SET in sections 2 and 3.

""")
            rep.line(errors.text())
            rep.line()
            rep.line(
                f"If a profile did not authenticate:  aws sso login --sso-session "
                f"{context.SSO_SESSION}"
            )
        else:
            rep.line("None. Every call in this report returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/account-bpa.py")

    # ---------------------------------------------------------------------------------- run
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 6)")
        return 1
    note(f"wrote {out_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
