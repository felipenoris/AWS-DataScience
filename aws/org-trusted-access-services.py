#!/usr/bin/env -S uv run --quiet
# org-trusted-access-services.py - which AWS services are allowed to act across this
# organization, and which account administers each of them.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/org-trusted-access-services.py                   # awsds-infra-identity
#             ./aws/org-trusted-access-services.py awsds-infra-dev   # a different profile
#             ./aws/org-trusted-access-services.py -                 # no --profile: run it
#                                                                    # inside CloudShell
#             (CloudShell has no uv: run `python3 aws/org-trusted-access-services.py -`
#              with the aws/ folder present - awslib sits beside this script.)
#   writes:   aws/output/org-trusted-access-services.txt   (untracked - see .gitignore)
#   reads:    organizations:ListAWSServiceAccessForOrganization,
#             organizations:ListDelegatedAdministrators, sts:GetCallerIdentity.
#             This script never creates, updates or deletes anything.
#
# WHY THIS EXISTS. Trusted access is an organization-level allowlist keyed by *service
# principal*, switched on from the management account. What it grants is not an IAM
# permission and appears in no policy evaluation: it lets the service read the
# organization's structure and create service-linked roles inside member accounts. That is
# Lesson 10's "a service that sets itself up creates principals nobody chose", by design -
# so the list of who holds it is worth being able to re-read rather than remember.
# Delegated administration is the *second*, separate registration: which member account
# operates that service org-wide, so that the management account does not have to.
#
# The list is not static, and every stage that adds to it says so: `access-analyzer` in
# Stage 1b step 8.2, `ram` in Stage 1d step 11 (without which a Lake Formation grant
# silently becomes a pending RAM invitation), then GuardDuty at Stage 15 (the 2026-08-18
# split moved it out of Stage 4), Security Hub at
# Stage 5 and Macie at Stage 11 - each of those delegations *enables* its service, which is
# why they are not here yet (Stage 1b step 8.1).
#
# IDENTITY, and why a management-account script has a member-account profile. Both calls
# are AWS Organizations reads, and Organizations is administered from the management
# account - for which there is no local profile and never will be (guiding principle 1).
# The default is `awsds-infra-identity`: a delegated administrator for *any* service may
# make a set of Organizations read-only calls, which Stage 1b step 4 measured from this
# account for the calls it used. These two were outside that set until the first run of
# this script, 2026-08-12, and **both returned** - so the read boundary measured in step 4
# covers them too, and no CloudShell session is needed to read this state.
# The script still does not assume it: a denial is reported in full, in section 4, with a
# non-zero exit - and the fallback is one line, in CloudShell on the management account as
# `AWS Control Tower Admin`:
#
#     python3 aws/org-trusted-access-services.py -
#
# Organizations is a global service; --region only picks the endpoint and changes nothing
# about what is returned.

from __future__ import annotations

import os
import sys

from awslib import context
from awslib.awscli import AwsCli
from awslib.report import Report, note, tabulate

# The service principal section 3 is about. One edit moves the whole section.
FOCUS_PRINCIPAL = "access-analyzer.amazonaws.com"

OUT_NAME = "org-trusted-access-services.txt"


def main(argv: list) -> int:
    profile = argv[0] if argv else os.environ.get("AWSDS_PROFILE", "awsds-infra-identity")
    cli = AwsCli(profile=profile, region=context.REGION)
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    # ---------------------------------------------------------------------------- preflight
    note(f"profile: {cli.label} (region {cli.region})")
    res = cli.call("sts", "get-caller-identity", "--query", "Arn", "--output", "text")
    if not res.ok:
        note("")
        note(f"cannot authenticate as '{cli.label}':")
        for line in res.merged.splitlines():
            if line.strip():
                note(f"  {line}")
        note("")
        note("log in first:")
        note(f"  aws sso login --sso-session {context.SSO_SESSION}")
        note("")
        note(f"the previous {out_label}, if any, is left untouched.")
        return 1
    caller = res.stdout
    note(f"caller : {caller}")

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Trusted access and delegated administration, per AWS service")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {cli.label}
caller    : {caller}
region    : {cli.region}   (AWS Organizations is global; the region only picks an endpoint)
produced  : aws/org-trusted-access-services.py   (index: aws/INDEX.md)

SECTIONS
  1. Trusted access - the services allowed to act across this organization
  2. Delegated administrator for {FOCUS_PRINCIPAL}
  3. Delegated administrators, service by service
  4. Calls that failed

HOW TO READ THIS FILE
  - TWO DIFFERENT REGISTRATIONS, both made only from the management account:
      trusted access        "this SERVICE may act across my organization" - it may
                            read the org structure and create service-linked roles
                            in member accounts. Section 1.
      delegated administr.  "this ACCOUNT administers that service for the whole
                            organization". Sections 2 and 3.
    Trusted access is the prerequisite for the second, not a weaker form of it.
  - SECTION 1 IS AN INVENTORY NOBODY IN THIS PROJECT WROTE. Most of it was enabled
    by Control Tower when the landing zone was installed. A principal there that
    no stage accounts for is a finding, not a detail - docs/log/ and docs/AWS_STATE.md.
  - A service with trusted access and NO delegated administrator is administered
    from the management account. That is the default, not a gap. A service marked
    "no delegated administration for this service" is a third case: it holds
    trusted access and the API rejects the question, Control Tower being one.
  - Every "$ aws ..." line is the exact command that produced the block under it,
    minus `--region {cli.region}` and the profile, which every command carries.
  - AN EMPTY BLOCK AND A DENIED CALL ARE NOT THE SAME THING. A call that failed is
    printed with its error and listed again in section 4; anywhere else, empty
    means the call succeeded and returned nothing.
  - This is a point-in-time snapshot, not a source of truth: regenerate it rather
    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ------------------------------------------------------------------------------
        rep.h1("1. Trusted access - the services allowed to act across this organization")

        note("listing trusted access...")
        rep.show(
            cli,
            "organizations",
            "list-aws-service-access-for-organization",
            "--query",
            "EnabledServicePrincipals[].ServicePrincipal",
            "--output",
            "table",
        )

        rep.text("""Each row is a service that may read this organization and create its own roles
inside member accounts. Add `DateEnabled` to the --query above to see when each one
was switched on, which is what distinguishes a landing-zone default from something
this project turned on.""")

        # ------------------------------------------------------------------------------
        rep.h1(f"2. Delegated administrator for {FOCUS_PRINCIPAL}")

        note(f"listing the delegated administrator for {FOCUS_PRINCIPAL}...")
        rep.show(
            cli,
            "organizations",
            "list-delegated-administrators",
            "--service-principal",
            FOCUS_PRINCIPAL,
            "--query",
            "DelegatedAdministrators[].[Name,Id,Status]",
            "--output",
            "table",
        )

        rep.text("""Expected: the Audit account, ACTIVE - registered in Stage 1b step 8.2, and the
precondition for the organization-level Access Analyzer that lives there. An empty
result means the registration is absent, not that it is pending.""")

        # ------------------------------------------------------------------------------
        rep.h1("3. Delegated administrators, service by service")

        note("listing delegated administrators for every enabled principal...")
        res = cli.run(
            "organizations",
            "list-aws-service-access-for-organization",
            "--query",
            "EnabledServicePrincipals[].ServicePrincipal",
            "--output",
            "text",
        )
        principals = sorted(p for p in res.text.split() if p)

        if not principals:
            rep.line("No service principal returned - see section 4.")
        else:
            rows = ["SERVICE PRINCIPAL\tDELEGATED ADMIN\tACCOUNT ID\tSTATUS"]
            for sp in principals:
                res = cli.run(
                    "organizations",
                    "list-delegated-administrators",
                    "--service-principal",
                    sp,
                    "--query",
                    "DelegatedAdministrators[].[Name,Id,Status]",
                    "--output",
                    "text",
                    tolerate="unrecognized service principal",
                )
                if not res.ok:
                    rows.append(f"{sp}\t!! call failed - see section 4\t-\t-")
                elif res.tolerated:
                    rows.append(f"{sp}\t(no delegated administration for this service)\t-\t-")
                elif not res.text:
                    rows.append(f"{sp}\t(none - management account)\t-\t-")
                else:
                    for line in res.text.splitlines():
                        fields = line.split("\t")
                        if not fields or not fields[0]:
                            continue
                        name, admin_id, status = (fields + ["-", "-", "-"])[:3]
                        rows.append(f"{sp}\t{name}\t{admin_id}\t{status}")
            rep.line(tabulate(rows))
            rep.line()
            rep.text("""Section 2 is one row of this table, kept separate because it is the one Stage 1b
step 8.2 creates and verifies. Everything else here is the landing zone, until a
later stage delegates GuardDuty (Stage 15), Security Hub (Stage 5), RAM (Stage 1d
step 11) or Macie (Stage 11).""")

        # ------------------------------------------------------------------------------
        rep.h1("4. Calls that failed")

        if cli.errors:
            rep.text("""Each entry is a call whose output is missing above. An empty block anywhere else
in this file means the call succeeded and returned nothing.

""")
            rep.line(cli.errors.text())
            rep.text("""
If these are AccessDenied: both calls are AWS Organizations reads, and this
profile may not be inside the read-only set a delegated administrator is allowed.
Re-run from CloudShell on the MANAGEMENT account, as `AWS Control Tower Admin`:
  python3 aws/org-trusted-access-services.py -
and record in docs/log/ which identity the answer actually required.""")
        else:
            rep.line("None. Every call in this report returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/org-trusted-access-services.py")

    # ---------------------------------------------------------------------------------- run
    note("")
    if cli.errors:
        note(f"wrote {out_label} (some calls FAILED - see section 4)")
        return 1
    note(f"wrote {out_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
