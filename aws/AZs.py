#!/usr/bin/env -S uv run --quiet
# AZs.py - the availability-zone name -> zone ID mapping, one listing per account, plus the
# comparison across them.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile below: the cached token is keyed by the
#             sso-session name, not by profile or account (see aws/INDEX.md).
#
#   run:      ./aws/AZs.py                       every awsds-* profile in ~/.aws/config
#             ./aws/AZs.py awsds-infra-dev ...   only the profiles named
#   writes:   aws/output/AZs.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeAvailabilityZones and sts:GetCallerIdentity. This script never
#             creates, updates or deletes anything.
#
# WHY THIS EXISTS. AWS maps AZ *names* (`us-west-2a`) to physical datacenters independently
# per account, so the same name can be a different datacenter in two accounts. The AZ *ID*
# (`usw2-az1`) is the stable identifier. The distinction has a bill attached: the two
# peerings into Production (D14, D21) are free within an AZ and USD 0.01/GB each way across
# AZs, and the divergence produces no error - only a line on the invoice. Measured first in
# Stage 1b step 6; the outcome is in docs/plan/architecture.md §4.1 and docs/plan/open-questions.md
# item 3, and is not repeated here (aws/INDEX.md: a snapshot is evidence, not intent).
#
# ONE DELIBERATE DEVIATION from aws/INDEX.md's "one profile per script": this script runs
# every profile it is given, because the comparison *between* accounts is the whole
# measurement. A single-profile version of it would answer nothing. Section 1 names the
# identity behind each block, which is what the one-profile rule exists to make visible.
#
# WHAT IT CANNOT SEE, stated because an empty column and a missing account look alike:
#   - An account with no profile in ~/.aws/config is invisible here. `Staging` is the open
#     case - not vended, so not measured - and every Sandbox vended under Stage 14 will be
#     too until its profile exists.
#   - A profile whose call failed is reported as `(failed)` and excluded from the agreement
#     check in section 4. It is never counted as agreeing.
#   - The default listing shows the zones available to the account. Opt-in-required zones
#     (Local Zones, Wavelength) are excluded; nothing in this plan uses one.

from __future__ import annotations

import sys

from awslib import context, profiles
from awslib.awscli import ErrorLog
from awslib.report import Report, note

OUT_NAME = "AZs.txt"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    clis = {p: profiles.cli_for(p, errors) for p in live}
    n_live = len(live)

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("AZs - availability-zone name to zone ID, per account")
        rep.text(f"""generated : {context.utc_stamp()}
region    : {context.REGION}
profiles  : {source}
measured  : {n_live} of {len(callers)}
produced  : aws/AZs.py   (index: aws/INDEX.md)

SECTIONS
  1. Callers - the identity behind each block
  2. One listing per account
  3. The mappings side by side
  4. CHECK: do the accounts agree?
  5. Calls that failed

HOW TO READ THIS FILE
  - AZ NAMES ARE PER-ACCOUNT LABELS; AZ IDS ARE THE STABLE IDENTIFIER. Two accounts
    showing the same name against different ids are naming different datacenters.
  - Every "$ aws ..." line is the exact command that produced the block under it,
    minus `--region {context.REGION}`, which every command carries.
  - Section 3 is joined by this script from the calls in section 2.
  - A "(failed)" profile is excluded from the section 4 check, never counted as
    agreeing. Section 5 lists every call that failed.
  - An account with no profile on this laptop does not appear at all.
  - This is a point-in-time snapshot, not a source of truth: regenerate it rather
    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.
    What was decided from this measurement: docs/plan/architecture.md 4.1 and
    docs/plan/open-questions.md item 3.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ------------------------------------------------------------------------------
        rep.h1("1. Callers - the identity behind each block")

        rep.tabulate(
            ["PROFILE\tCALLER ARN"]
            + [f"{c.profile}\t{c.arn if c.live else '(failed)'}" for c in callers]
        )
        rep.text("""
Each row is `aws --profile <profile> sts get-caller-identity --query Arn`.
A "(failed)" row means the profile did not authenticate - an expired SSO session is
the usual cause. Its account is absent from sections 2-4, not agreeing with them.""")

        # ------------------------------------------------------------------------------
        rep.h1("2. One listing per account")

        note("listing availability zones...")
        # profile -> ordered (ZoneName, ZoneId) pairs, the map sections 3 and 4 join on
        zone_maps: dict = {}
        for p in live:
            rep.h2(p)

            rep.show(
                clis[p],
                "ec2",
                "describe-availability-zones",
                "--query",
                "sort_by(AvailabilityZones, &ZoneName)[]"
                ".[ZoneName,ZoneId,ZoneType,State,OptInStatus]",
                "--output",
                "table",
            )

            res = clis[p].run(
                "ec2",
                "describe-availability-zones",
                "--query",
                "sort_by(AvailabilityZones, &ZoneName)[].[ZoneName,ZoneId]",
                "--output",
                "text",
            )
            zone_maps[p] = [tuple(ln.split("\t")) for ln in res.text.splitlines() if ln]

        rep.text("""
The five columns are ZoneName, ZoneId, ZoneType, State and OptInStatus. Anything
other than `availability-zone` / `available` / `opt-in-not-required` is worth a
second look before a subnet is placed there.""")

        def zone_id_of(p: str, zone_name: str) -> str:
            for name, zid in zone_maps.get(p, []):
                if name == zone_name:
                    return zid
            return "-"

        # ------------------------------------------------------------------------------
        rep.h1("3. The mappings side by side")

        zone_names = sorted({name for pairs in zone_maps.values() for name, _ in pairs})

        if not zone_names:
            rep.line("No zone returned by any profile. See section 5.")
        else:
            rows = ["ZONE NAME" + "".join(f"\t{p}" for p in live)]
            for z in zone_names:
                rows.append(z + "".join(f"\t{zone_id_of(p, z)}" for p in live))
            rep.tabulate(rows)
            rep.text("""
One column per measured profile; the cell is the zone ID that account reports for
that zone name. A "-" means the account did not return that zone at all.""")

        # ------------------------------------------------------------------------------
        rep.h1("4. CHECK: do the accounts agree?")

        ref = live[0]
        disagree = 0

        rep.text(f"Reference: {ref}. Every other measured profile is compared against it.\n\n")

        rows = ["PROFILE\tVERDICT"]
        for p in live:
            if p == ref:
                rows.append(f"{p}\treference")
            elif zone_maps[p] == zone_maps[ref]:
                rows.append(f"{p}\tsame mapping")
            else:
                rows.append(f"{p}\t!! DIFFERS")
                disagree += 1
        rep.tabulate(rows)
        rep.line()

        if n_live == 1:
            rep.text("""NOTHING WAS COMPARED: only one account was measured, and it agrees with itself.
This is not a passing check - it is an absent one. Re-run against at least two
profiles before reading anything into section 3.

""")
        elif disagree == 0:
            rep.text(f"""CHECK OK: the {n_live} measured accounts return an identical name-to-ID mapping.

This says nothing about an account that was not measured. A newly vended account
gets its own mapping at vend time, and nothing makes it match the ones above -
which is why anchoring on zone IDs is the standing rule rather than a reaction to
a divergence (docs/plan/architecture.md 4.1).""")
        else:
            rep.text(
                f"!! CHECK FAILED: {disagree} profile(s) disagree with {ref}. "
                "The differing rows:\n\n"
            )
            for p in live:
                if p == ref or zone_maps[p] == zone_maps[ref]:
                    continue
                rep.text(f"  {ref} vs {p}\n\n")
                detail = [f"  ZONE NAME\t{ref}\t{p}"]
                for z, ref_id in zone_maps[ref]:
                    other = zone_id_of(p, z)
                    if other != ref_id:
                        detail.append(f"  {z}\t{ref_id}\t{other}")
                rep.tabulate(detail)
                rep.line()
            rep.text("""Anchor subnets on zone IDs, never on list position. A `for_each` over
`data.aws_availability_zones` by index places peered subnets in different
datacenters, which raises no error and shows up only as cross-AZ transfer.""")

        not_measured = [c.profile for c in callers if not c.live]
        if not_measured:
            rep.line()
            rep.line("Not measured, and therefore not covered by the verdict above:")
            for p in not_measured:
                rep.line(f"  {p}")

        # ------------------------------------------------------------------------------
        rep.h1("5. Calls that failed")

        if errors:
            rep.text("""Each entry is a call whose output is missing above. An empty block anywhere else
in this file means the call succeeded and returned nothing.

""")
            rep.line(errors.text())
        else:
            rep.line("None. Every call in this report returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/AZs.py")

    # ---------------------------------------------------------------------------------- run
    note("")
    if disagree == 0 and n_live == 1:
        note(f"wrote {out_label} (1 account only - nothing was compared, see section 4)")
    elif disagree == 0:
        note(f"wrote {out_label} ({n_live} accounts, mappings identical)")
    else:
        note(f"wrote {out_label} ({disagree} account(s) DISAGREE - see section 4)")
    if errors:
        note("some calls failed - see section 5")
    return disagree


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
