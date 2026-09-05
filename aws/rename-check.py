#!/usr/bin/env -S uv run --quiet
# rename-check.py - Stage 6b's instrument: is the account that used to be `Development`
# a Workload account yet, and is anything left stranded on the way?
#
# WHY THIS EXISTS AS ITS OWN FILE. Stage 6b converts one account from an Interactive
# member of the SageMaker Unified Studio domain into the headless `Staging` deployment
# target: a rename, an OU move, an SMUS unwind, a Lake Formation share revocation and a
# persona swap, in that order and across four accounts. Each half is already visible in
# some other instrument - studio.py sees the blueprint configurations, datalake.py the
# grants, list-identities.py the assignments - and NONE of them answers the only question
# an operator has mid-conversion: which side of the cut is this account on, and did
# anything fail to cross? Reading six files and holding the answer in your head is exactly
# how a stranded object survives (Lesson 31: a check inherits the scope of the account it
# was written in).
#
# THE THREE ANSWERS IT GIVES, and the middle one is the reason for the file:
#
#   BEFORE   the roster still shows the old name in `Interactive`, the domain still has
#            two associated accounts, the share still exists. Nothing has run. Every
#            check `note`s; nothing fails.
#   AFTER    the new name in `Workloads`, no DataZone object, no share, no vending
#            policy, the Staging persona set. Every check passes.
#   MIXED    any combination of the two - and this is a FINDING, not a phase. The one
#            that costs a sitting: an account already in `Workloads` that still holds
#            blueprint configurations, which can no longer be deleted from inside it
#            (the OU denies `datazone:*`). Stage 6b's step order exists to make that
#            impossible; this file is what proves the order was followed.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/rename-check.py                  # every awsds-* profile
#             ./aws/rename-check.py awsds-infra-dev  # only the ones named (partial reading)
#   writes:   aws/output/rename-check.txt   (untracked - see .gitignore)
#   reads:    organizations:ListAccounts, ListParents, DescribeOrganizationalUnit,
#             sso-admin:ListPermissionSetsProvisionedToAccount, DescribePermissionSet,
#             datazone:ListEnvironmentBlueprintConfigurations, ListDomains,
#             ram:GetResourceShares, lakeformation:ListPermissions,
#             sts:GetCallerIdentity.  It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing read look alike:
#   - The Account Factory PROVISIONED PRODUCT's parameters. Whether Service Catalog's
#     `AccountName` follows an out-of-band `PutAccountName` is undocumented, and the
#     answer is only visible from Management, which holds no profile here. Read it in
#     that account's console after step 3 and write what it says into the stage log.
#   - The account's OU as CONTROL TOWER sees it. This file reads Organizations; a
#     `Moved member account` drift is a Control Tower concept and shows in its console.
#   - The state migration (Recipe E). `./scripts/slices.py check` and an empty plan are
#     that half's evidence, not an AWS read.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "rename-check.txt"

# The account under conversion, by both of its names. Resolution is by EXACT vended name
# (every Account Factory account carries an ` Account` suffix) and never by a prefix
# match: a SUSPENDED `Sandbox` that predates this project sits in the same roster, and a
# loose match finds it.
OLD_NAME = "Development Account"
NEW_NAME = "Staging Account"

OLD_OU = "Interactive"
NEW_OU = "Workloads"

# The profile that reads the organization. Organizations is administered from Identity
# (D10), and every read below is a describe.
ORG_PROFILE = "awsds-infra-identity"

# The member profile. It is named `awsds-infra-dev` before the rename and
# `awsds-infra-staging` after it; both are tried, because during the sitting the
# ~/.aws/config edit and the AWS-side rename do not happen in the same second.
MEMBER_PROFILES = ("awsds-infra-dev", "awsds-infra-staging")

# The producer of the lake share, and the account that owns the registry policies.
PRODUCER_PROFILE = "awsds-infra-data"

# What D18 says the account may hold once it is a Workload deployment target. A set
# rather than a list: the order permission sets come back in is the API's business.
STAGING_SETS = {"InfrastructureAccess", "DataScientistStagingAccess", "DeploymentManagerAccess"}
# What it must NOT hold. `DataScientistAccess` is read-write; `DevEnvStewardAccess` is an
# image steward's, and a headless account has no images to steward.
FORBIDDEN_SETS = {"DataScientistAccess", "DevEnvStewardAccess"}


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = {c.profile: c for c in callers if c.live}
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------------------- 1. the roster: name and OU
    acct_id = None
    acct_name = "(not read)"
    acct_ou = "(not read)"
    roster_rows: list = []
    if ORG_PROFILE in live:
        cli = cli_for(ORG_PROFILE)
        note(f"reading the organization as {ORG_PROFILE} ...")
        res = cli.run(
            "organizations",
            "list-accounts",
            "--query",
            "Accounts[?Status=='ACTIVE'].[Name,Id]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(ORG_PROFILE, "organizations list-accounts", res.stderr)
        else:
            for name, ident in json.loads(res.stdout or "[]"):
                roster_rows.append((name, ident))
                if name in (OLD_NAME, NEW_NAME):
                    acct_id, acct_name = ident, name
        if acct_id:
            r = cli.run(
                "organizations",
                "list-parents",
                "--child-id",
                acct_id,
                "--query",
                "Parents[0].Id",
                "--output",
                "text",
                log=False,
            )
            if r.ok and r.stdout.strip() not in ("", "None"):
                parent = r.stdout.strip()
                r2 = cli.run(
                    "organizations",
                    "describe-organizational-unit",
                    "--organizational-unit-id",
                    parent,
                    "--query",
                    "OrganizationalUnit.Name",
                    "--output",
                    "text",
                    log=False,
                )
                acct_ou = r2.stdout.strip() if r2.ok else "(call failed)"
            else:
                acct_ou = "(root, or the call failed)"

    # --------------------------------------------- 2. the permission sets on the account
    sets_on_account: list = []
    if ORG_PROFILE in live and acct_id:
        cli = cli_for(ORG_PROFILE)
        inst = cli.run(
            "sso-admin",
            "list-instances",
            "--query",
            "Instances[0].InstanceArn",
            "--output",
            "text",
            log=False,
        )
        if inst.ok and inst.stdout.strip() not in ("", "None"):
            instance_arn = inst.stdout.strip()
            r = cli.run(
                "sso-admin",
                "list-permission-sets-provisioned-to-account",
                "--instance-arn",
                instance_arn,
                "--account-id",
                acct_id,
                "--query",
                "PermissionSets[]",
                "--output",
                "json",
                log=False,
            )
            if r.ok:
                for ps_arn in json.loads(r.stdout or "[]"):
                    d = cli.run(
                        "sso-admin",
                        "describe-permission-set",
                        "--instance-arn",
                        instance_arn,
                        "--permission-set-arn",
                        ps_arn,
                        "--query",
                        "PermissionSet.Name",
                        "--output",
                        "text",
                        log=False,
                    )
                    sets_on_account.append(d.stdout.strip() if d.ok else "(name unread)")
            else:
                logerr(
                    ORG_PROFILE, "sso-admin list-permission-sets-provisioned-to-account", r.stderr
                )

    # ------------------------------------- 3. the member's own DataZone and RAM surfaces
    member_profile = next((p for p in MEMBER_PROFILES if p in live), None)
    blueprints = "(not read)"
    ram_shares = "(not read)"
    if member_profile:
        cli = cli_for(member_profile)
        note(f"reading the member as {member_profile} ...")
        dom = cli.run(
            "datazone",
            "list-domains",
            "--query",
            "items[?status=='AVAILABLE'].id",
            "--output",
            "json",
            log=False,
            tolerate="AccessDenied",
        )
        if dom.tolerated:
            # The Workloads OU denies datazone:* outright, so a refusal HERE is the
            # strongest evidence the move landed - and it is the reading that flips
            # RC-3 from "no configurations" to "cannot even ask", which are different
            # facts (Lesson 13).
            blueprints = "(datazone denied - the Workloads ceiling is in force)"
        elif dom.ok:
            ids = json.loads(dom.stdout or "[]")
            if not ids:
                blueprints = "no domain visible (the association is gone)"
            else:
                counts = []
                for did in ids:
                    r = cli.run(
                        "datazone",
                        "list-environment-blueprint-configurations",
                        "--domain-identifier",
                        did,
                        "--query",
                        "length(items)",
                        "--output",
                        "text",
                        log=False,
                        tolerate="AccessDenied",
                    )
                    if r.tolerated:
                        counts.append(f"{did}=denied")
                    elif r.ok:
                        counts.append(f"{did}={r.stdout.strip()}")
                    else:
                        counts.append(f"{did}=(call failed)")
                blueprints = " ".join(counts)
        else:
            logerr(member_profile, "datazone list-domains", dom.stderr)
            blueprints = "(call failed)"

        r = cli.run(
            "ram",
            "get-resource-shares",
            "--resource-owner",
            "OTHER-ACCOUNTS",
            "--query",
            "resourceShares[?status=='ACTIVE'].name",
            "--output",
            "json",
            log=False,
            tolerate="AccessDenied",
        )
        if r.tolerated:
            ram_shares = "(read denied)"
        elif r.ok:
            names = json.loads(r.stdout or "[]")
            ram_shares = ", ".join(names) if names else "(none)"
        else:
            logerr(member_profile, "ram get-resource-shares", r.stderr)
            ram_shares = "(call failed)"

    # ------------------------------------ 4. the producer side: does a grant name it still
    lf_grants = "(not read)"
    if PRODUCER_PROFILE in live and acct_id:
        cli = cli_for(PRODUCER_PROFILE)
        note(f"reading the lake's grants as {PRODUCER_PROFILE} ...")
        r = cli.run(
            "lakeformation",
            "list-permissions",
            "--principal",
            f"DataLakePrincipalIdentifier={acct_id}",
            "--query",
            "length(PrincipalResourcePermissions)",
            "--output",
            "text",
            log=False,
            tolerate="AccessDenied",
        )
        if r.tolerated:
            lf_grants = "(read denied)"
        elif r.ok:
            lf_grants = r.stdout.strip()
        else:
            logerr(PRODUCER_PROFILE, "lakeformation list-permissions", r.stderr)
            lf_grants = "(call failed)"

    # -------------------------------------------------------------------------- the checks
    #
    # Every check below reads three ways on purpose: the BEFORE state notes, the AFTER
    # state passes, and the combination that should not exist fails. A `note` here is a
    # statement that the stage has not run - never that it does not apply.

    # RC-1: the name.
    if acct_name == OLD_NAME:
        checks.note("RC-1", "the account's name", f"{OLD_NAME} - step 3 has not run")
    elif acct_name == NEW_NAME:
        checks.ok("RC-1", "the account's name", NEW_NAME)
    else:
        checks.fail(
            "RC-1",
            "the account's name",
            f"neither name found in the ACTIVE roster (read: {acct_name}). Either the "
            "rename used a different string - the vended pattern is '<name> Account' and "
            "two code sites resolve on it - or this profile cannot read Organizations.",
        )

    # RC-2: the OU, against the name. The pair is the check, not either alone.
    if acct_ou == OLD_OU and acct_name == OLD_NAME:
        checks.note("RC-2", "the account's OU", f"{OLD_OU} - the move has not run")
    elif acct_ou == NEW_OU and acct_name == NEW_NAME:
        checks.ok("RC-2", "the account's OU", NEW_OU)
    elif acct_ou in (OLD_OU, NEW_OU):
        checks.fail(
            "RC-2",
            "the account's OU",
            f"name={acct_name} but OU={acct_ou} - the rename and the move are one sitting "
            "(step 3), and a half-done pair leaves the two name-keyed code sites planning "
            "against a precondition that fails.",
        )
    else:
        checks.note("RC-2", "the account's OU", acct_ou)

    # RC-3: THE ORDERING CHECK, and the reason this file exists. Blueprint configurations
    # are deleted by the MEMBER, and the destination OU denies datazone:* on arrival.
    in_workloads = acct_ou == NEW_OU
    if blueprints == "(not read)":
        checks.note("RC-3", "the SMUS surface", "no member profile authenticated")
    elif blueprints.startswith("(datazone denied"):
        checks.ok(
            "RC-3",
            "the SMUS surface",
            "datazone is denied in this account - the Workloads ceiling is in force and "
            "no DataZone object can be created here",
        )
    elif "no domain visible" in blueprints:
        checks.ok("RC-3", "the SMUS surface", "no domain visible - the association is gone")
    elif in_workloads:
        checks.fail(
            "RC-3",
            "the SMUS surface",
            f"{blueprints} - blueprint configurations are visible from an account that is "
            "ALREADY in Workloads. They are deleted by the member and the OU denies "
            "datazone:*, so they are now stranded: move the account back to Interactive, "
            "destroy them, and move it forward again (Stage 6b step 1, whose whole order "
            "exists to prevent this).",
        )
    else:
        checks.note("RC-3", "the SMUS surface", f"{blueprints} - step 1 has not run")

    # RC-4: the RAM share the association rides on.
    if ram_shares == "(not read)":
        checks.note("RC-4", "the domain's RAM share", "no member profile authenticated")
    elif ram_shares == "(none)":
        checks.ok("RC-4", "the domain's RAM share", "none held from other accounts")
    elif ram_shares.startswith("("):
        checks.note("RC-4", "the domain's RAM share", ram_shares)
    else:
        checks.note(
            "RC-4",
            "the domain's RAM share",
            f"{ram_shares} - the console disassociation (step 1) has not run, or the share "
            "outlived it. The documentation does not say the share is deleted, so read this "
            "row rather than assuming either way.",
        )

    # RC-5: the persona set, against D18's row.
    if not sets_on_account:
        checks.note(
            "RC-5", "the permission sets", "none read (no org profile, or none provisioned)"
        )
    else:
        held = set(sets_on_account)
        wrong = sorted(held & FORBIDDEN_SETS)
        missing = sorted(STAGING_SETS - held)
        if wrong:
            checks.fail(
                "RC-5",
                "the permission sets",
                f"{', '.join(wrong)} still provisioned - D18 says Staging is read-only and "
                "nothing else, and the assignment must be removed BEFORE the customer-managed "
                "vending policy it references (Stage 6b step 2).",
            )
        elif missing:
            checks.note(
                "RC-5",
                "the permission sets",
                f"holds {', '.join(sorted(held))}; still missing {', '.join(missing)}",
            )
        else:
            checks.ok("RC-5", "the permission sets", ", ".join(sorted(held)))

    # RC-6: the lake share. D20 says Staging is never on it.
    if lf_grants in ("(not read)", "(read denied)", "(call failed)"):
        checks.note("RC-6", "Lake Formation grants naming the account", lf_grants)
    elif lf_grants == "0":
        checks.ok("RC-6", "Lake Formation grants naming the account", "none")
    else:
        checks.note(
            "RC-6",
            "Lake Formation grants naming the account",
            f"{lf_grants} - step 2's revocation has not run. Annotate the register rows in "
            "docs/AWS_STATE.md as revoked with a date; never delete one.",
        )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("rename-check - is the account a Workload target yet, and is anything stranded?")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/rename-check.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The account under conversion
  3. The surfaces that must be gone
  4. CHECKS
  5. Calls that failed

HOW TO READ THIS FILE
  - "HAS NOT RUN" IS THE EXPECTED ANSWER UNTIL STAGE 6b RUNS. Every such reading
    is a note. The stage is done when every check reads pass.
  - A MIXED READING IS A FINDING, NOT A PHASE. The expensive one is RC-3: an
    account already in Workloads that still holds blueprint configurations
    cannot delete them from inside itself.
  - THIS FILE READS ORGANIZATIONS, NOT CONTROL TOWER. A "Moved member account"
    drift, and whether the Account Factory provisioned product's AccountName
    followed the rename, are visible only from Management.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        rep.h1("1. Which accounts were measured, and as whom")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        rep.h1("2. The account under conversion")
        rep.tabulate(
            [
                "FACT\tREADING",
                f"name\t{acct_name}",
                f"account id\t{acct_id or '(not resolved)'}",
                f"OU\t{acct_ou}",
                f"permission sets\t{', '.join(sorted(sets_on_account)) or '(none read)'}",
                f"member profile used\t{member_profile or '(none authenticated)'}",
            ]
        )
        rep.text("""
The name is resolved by EXACT match against the ACTIVE roster. Every Account
Factory account carries an ' Account' suffix, and a SUSPENDED `Sandbox` that
predates this project sits in the same list - which is why nothing here matches
on a prefix.""")

        rep.h1("3. The surfaces that must be gone")
        rep.tabulate(
            [
                "SURFACE\tREADING\tOWNED BY",
                f"blueprint configurations\t{blueprints}\tthe member (step 1)",
                f"RAM shares from other accounts\t{ram_shares}\tthe domain account (step 1)",
                f"Lake Formation grants\t{lf_grants}\tthe producer (step 2)",
            ]
        )

        rep.h1("4. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are:
  RC-1  the account's name is one of the two, exactly (step 3)
  RC-2  name and OU agree - the pair is the check (step 3)
  RC-3  the SMUS surface is gone, or still deletable. FAILS when the account is
        in Workloads and configurations are still visible: the OU denies
        datazone:* and only the member can delete them (step 1's order)
  RC-4  no RAM share from another account survives the disassociation (step 1)
  RC-5  the persona set is D18's row, with no read-write and no image steward
        (step 2, assignment before the policy object)
  RC-6  no Lake Formation grant names the account (step 2)""")

        rep.h1("5. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/rename-check.py")

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
