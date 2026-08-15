#!/usr/bin/env -S uv run --quiet
# list-identities.py - snapshot of the Organization tree and of the IAM Identity Center
# directory, as seen from the Identity account.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             The login authenticates against the access portal, not against an account:
#             the cached token is keyed by the sso-session name, so one login covers every
#             profile in ~/.aws/config that declares `sso_session = awsds`, and the profile
#             below only matters one step later, when a call trades that token for the
#             temporary credentials of its account's role. `aws sso login --profile
#             awsds-infra-identity` reaches the same session and is equivalent.
#             This is checked before any listing runs: a missing or expired token stops the
#             script with that command, leaving the previous snapshot untouched.
#
#   run:      ./aws/list-identities.py
#   writes:   aws/output/list-identities.txt   (untracked - see .gitignore)
#   reads:    everything; this script never creates, updates or deletes anything.
#
# Identity: the `awsds-infra-identity` SSO profile, i.e. the Identity account acting as the
# IAM Identity Center delegated administrator (D10). Reads are not restricted from there -
# only *writes* against Management-targeted objects are - which is why the Organizations
# calls below answer even though only Management could change what they return
# (docs/log/log-stage-01b-identity-and-controls.md, step 4).
#
# Two call styles, on purpose:
#   show  - prints the command and the CLI's own `--output table` under it. What a reader
#           sees is exactly what the CLI returned.
#   run   - captures `--output text` for values that later commands need as arguments, or
#           for rows this script joins into a table.
# Both record a failing call in the error log printed by section 6, so that an empty block
# is never ambiguous between "nothing there" and "the call was denied".

from __future__ import annotations

import io
import sys

from awslib import context
from awslib.awscli import AwsCli
from awslib.report import Report, note

PROFILE = "awsds-infra-identity"
OUT_NAME = "list-identities.txt"


def main() -> int:
    cli = AwsCli(profile=PROFILE, region=context.REGION)
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    # ---------------------------------------------------------------------------- preflight
    note(f"profile: {PROFILE} (region {cli.region})")
    res = cli.call("sts", "get-caller-identity", "--query", "Arn", "--output", "text")
    if not res.ok:
        note("")
        note(f"cannot authenticate with profile '{PROFILE}':")
        for line in res.merged.splitlines():
            if line.strip():
                note(f"  {line}")
        note("")
        note("log in first:")
        note(f"  aws sso login --sso-session {context.SSO_SESSION}")
        return 1
    caller = res.stdout
    note(f"caller:  {caller}")

    # The name maps sections 3-5 join against; all print "(unknown)" rather than nothing,
    # so a missing name is visible in the report instead of collapsing a column.
    account_map: dict = {}
    user_map: dict = {}  # id -> (username, display)
    group_map: list = []  # (id, display), in listing order
    ps_map: dict = {}

    def account_name(acct: str) -> str:
        return account_map.get(acct, "(unknown)")

    def user_name(uid: str) -> str:
        return user_map.get(uid, ("(unknown)", "(unknown)"))[0]

    def user_display(uid: str) -> str:
        return user_map.get(uid, ("(unknown)", "(unknown)"))[1]

    def group_name(gid: str) -> str:
        return dict(group_map).get(gid, "(unknown)")

    def ps_name(ps: str) -> str:
        return ps_map.get(ps, "(unknown)")

    status = 0
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        def detail(tolerate, label: str, *args: str) -> None:
            """One labelled detail block, indented under a permission set. Distinguishes a
            failed call from a genuinely empty one, which is the whole point."""
            rep.line(f"  {label}")
            res = cli.run(*args, tolerate=tolerate)
            if not res.ok:
                rep.line("    !! call failed - see section 6")
            elif not res.text or res.text in ("None", "null"):
                rep.line("    (none)")
            elif "\t" in res.text:
                rep.tabulate(res.text.splitlines(), indent="    ")
            else:
                for line in res.text.splitlines():
                    rep.line(f"    {line}")
            rep.line()

        rep.banner("list-identities - Organization and IAM Identity Center state")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {PROFILE}
region    : {cli.region}
caller    : {caller}
produced  : aws/list-identities.py   (index: aws/INDEX.md)

SECTIONS
  1. Caller - the identity that produced this file
  2. Organization        2.1 ORG_ID and MGMT_ID  2.2 ROOT_ID and policy types
                         2.3 the OU tree  2.4 every account
  3. Identity Center     3.1 instances  3.2 CHECK: exactly one  3.3 groups
                         3.4 users  3.5 group memberships
  4. Permission sets     4.1 ARNs  4.2 described  4.3 what each one grants
  5. Assignments         5.1 every triple  5.2 grouped by account
  6. Calls that failed

HOW TO READ THIS FILE
  - Every "$ aws ..." line is the exact command that produced the block under it,
    minus `--profile {PROFILE} --region {cli.region}`, which every command carries.
  - NAME=value lines are shell variables reused by the commands that follow.
  - A table without a "$ aws" line above it was joined by the script from several
    calls; the calls are named in the paragraph next to it.
  - An empty block says which kind of empty it is. Section 6 lists every call that
    failed, so "(none)" always means none.
  - This is a point-in-time snapshot, not a source of truth: regenerate it rather
    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS
AND EMAIL ADDRESSES. Do not copy either into a tracked file.""")

        # ------------------------------------------------------------------------------
        rep.h1("1. Caller - the identity that produced this file")
        rep.show(cli, "sts", "get-caller-identity", "--output", "table")

        # ------------------------------------------------------------------------------
        rep.h1("2. Organization")

        rep.h2("2.1 ORG_ID and MGMT_ID - the organization, and the account that manages it")

        # ORG_ID is not a curiosity: it is the value both data-perimeter condition keys
        # take, so it is printed as a named variable rather than left as an unlabelled row
        # of the table below.
        res = cli.run(
            "organizations",
            "describe-organization",
            "--query",
            "Organization.Id",
            "--output",
            "text",
        )
        org_id = res.text
        rep.text(f"""$ ORG_ID=$(aws organizations describe-organization \\
      --query Organization.Id \\
      --output text)
$ echo $ORG_ID
{org_id or "(call failed - see section 6)"}

This id is what the two data-perimeter condition keys of docs/plan/architecture.md are
compared against: aws:PrincipalOrgID (is the CALLER inside my organization?) and
aws:ResourceOrgID (is the RESOURCE being written to?). It is also the value
terraform-live/identity/org-policies/render.py substitutes for the <ORG_ID>
placeholder of the Stage 1c policy documents - read it here, never paste it by hand.

""")

        res = cli.run(
            "organizations",
            "describe-organization",
            "--query",
            "Organization.MasterAccountId",
            "--output",
            "text",
        )
        mgmt_id = res.text
        rep.text(f"""$ MGMT_ID=$(aws organizations describe-organization \\
      --query Organization.MasterAccountId \\
      --output text)
$ echo $MGMT_ID
{mgmt_id or "(call failed - see section 6)"}

""")

        rep.show(
            cli,
            "organizations",
            "describe-organization",
            "--query",
            "Organization.[Id,Arn,FeatureSet,MasterAccountId]",
            "--output",
            "table",
        )

        rep.h2("2.2 ROOT_ID - the organization root, and the policy types enabled on it")

        res = cli.run("organizations", "list-roots", "--query", "Roots[0].Id", "--output", "text")
        root_id = res.text
        rep.line(f"ROOT_ID={root_id or '(call failed - see section 6)'}")
        rep.line()

        rep.show(
            cli,
            "organizations",
            "list-roots",
            "--query",
            "Roots[].[Name,Id,Arn]",
            "--output",
            "table",
        )

        # Which policy types are ENABLED here decides what can be attached to an OU at all:
        # an SCP, an RCP, a tag policy or a declarative policy that is not ENABLED on the
        # root cannot be attached anywhere, whatever the OU tree looks like.
        rep.show(
            cli,
            "organizations",
            "list-roots",
            "--query",
            "Roots[0].PolicyTypes[].[Type,Status]",
            "--output",
            "table",
        )

        rep.h2("2.3 The OU tree, walked from the root")

        # The tree is deeper than one level (Sandboxes is nested under Interactive), so
        # this recurses. Two things come out of the walk: the indented tree printed first,
        # and one pair of tables per parent - its child OUs, and the accounts sitting
        # directly in it.
        tree_lines: list = []
        detail_stream = io.StringIO()
        detail_rep = Report(detail_stream)

        def walk_ou(parent: str, label: str, depth: int) -> None:
            pad = "  " * depth

            detail_rep.h2(f"children of {label} ({parent})")

            detail_rep.show(
                cli,
                "organizations",
                "list-organizational-units-for-parent",
                "--parent-id",
                parent,
                "--query",
                "OrganizationalUnits[].[Name,Id,Arn]",
                "--output",
                "table",
            )
            detail_rep.show(
                cli,
                "organizations",
                "list-accounts-for-parent",
                "--parent-id",
                parent,
                "--query",
                "Accounts[].[Name,Id,Status]",
                "--output",
                "table",
            )

            res = cli.run(
                "organizations",
                "list-accounts-for-parent",
                "--parent-id",
                parent,
                "--query",
                "Accounts[].[Id,Name,Status]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                fields = line.split("\t")
                if len(fields) >= 3 and fields[0]:
                    tree_lines.append(f"{pad}  AC {fields[1]} ({fields[0]}) {fields[2]}")

            res = cli.run(
                "organizations",
                "list-organizational-units-for-parent",
                "--parent-id",
                parent,
                "--query",
                "OrganizationalUnits[].[Id,Name]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                fields = line.split("\t")
                if len(fields) >= 2 and fields[0]:
                    ou_id, ou_name = fields[0], fields[1]
                    tree_lines.append(f"{pad}  OU {ou_name} ({ou_id})")
                    walk_ou(ou_id, ou_name, depth + 1)

        note("walking the OU tree...")
        walk_ou(root_id or "r-unknown", "Root", 0)

        rep.text(f"""Tree, joined by this script from the calls shown below.
OU = organizational unit, AC = account; indentation is depth under the root.

Root ({root_id or "?"})""")
        for line in tree_lines:
            rep.line(line)
        rep.text(detail_stream.getvalue())

        rep.h2("2.4 Every account in the organization")

        rep.show(
            cli,
            "organizations",
            "list-accounts",
            "--query",
            "sort_by(Accounts, &Name)[].[Id,Name,Status]",
            "--output",
            "table",
        )

        res = cli.run(
            "organizations", "list-accounts", "--query", "Accounts[].[Id,Name]", "--output", "text"
        )
        for line in res.text.splitlines():
            fields = line.split("\t")
            if len(fields) >= 2:
                account_map[fields[0]] = fields[1]

        # ------------------------------------------------------------------------------
        rep.h1("3. IAM Identity Center - the directory")

        rep.h2("3.1 Identity Store instances")
        rep.show(
            cli,
            "sso-admin",
            "list-instances",
            "--query",
            "Instances[].[IdentityStoreId,InstanceArn,OwnerAccountId,Status]",
            "--output",
            "table",
        )

        rep.h2("3.2 CHECK - there must be exactly one Identity Store")

        res = cli.run(
            "sso-admin", "list-instances", "--query", "length(Instances)", "--output", "text"
        )
        n_instances = res.text
        rep.text(f"""$ N_INSTANCES=$(aws sso-admin list-instances \\
      --query "length(Instances)" \\
      --output text)
$ echo $N_INSTANCES
{n_instances or "(call failed - see section 6)"}

""")

        if n_instances != "1":
            rep.text(f"""CHECK FAILED: expected exactly 1 Identity Store instance, found "{n_instances}".

Everything below addresses "the" Identity Store by its id, so the rest of this
report is not produced. Either a second instance exists - which contradicts the
single-directory assumption the plan is built on - or the call was denied.""")
            rep.h1("6. Calls that failed")
            if cli.errors:
                rep.line(cli.errors.text())
            note(f"CHECK FAILED: found '{n_instances}' Identity Store instances, expected 1")
            status = 1
        else:
            rep.text("CHECK OK: exactly one instance. Its ids are used by every command below.\n\n")

            res = cli.run(
                "sso-admin",
                "list-instances",
                "--query",
                "Instances[0].IdentityStoreId",
                "--output",
                "text",
            )
            ids = res.text
            res = cli.run(
                "sso-admin",
                "list-instances",
                "--query",
                "Instances[0].InstanceArn",
                "--output",
                "text",
            )
            inst = res.text
            rep.line(f"IDS={ids}")
            rep.line(f"INST={inst}")

            rep.h2("3.3 Groups")

            rep.show(
                cli,
                "identitystore",
                "list-groups",
                "--identity-store-id",
                ids,
                "--query",
                "sort_by(Groups, &DisplayName)[].[DisplayName,GroupId,Description]",
                "--output",
                "table",
            )

            res = cli.run(
                "identitystore",
                "list-groups",
                "--identity-store-id",
                ids,
                "--query",
                "sort_by(Groups, &DisplayName)[].[GroupId,DisplayName]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                fields = line.split("\t")
                if len(fields) >= 2:
                    group_map.append((fields[0], fields[1]))

            rep.h2("3.4 Users")

            rep.show(
                cli,
                "identitystore",
                "list-users",
                "--identity-store-id",
                ids,
                "--query",
                "sort_by(Users, &UserName)[].[UserName,DisplayName,UserId]",
                "--output",
                "table",
            )
            rep.show(
                cli,
                "identitystore",
                "list-users",
                "--identity-store-id",
                ids,
                "--query",
                "sort_by(Users, &UserName)[].[UserName,Name.GivenName,Name.FamilyName,"
                "Emails[0].Value,Emails[0].Type]",
                "--output",
                "table",
            )

            res = cli.run(
                "identitystore",
                "list-users",
                "--identity-store-id",
                ids,
                "--query",
                "Users[].[UserId,UserName,DisplayName]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                fields = line.split("\t")
                if len(fields) >= 3:
                    user_map[fields[0]] = (fields[1], fields[2])

            rep.h2("3.5 Group memberships")

            # One table per group. UserName and DisplayName are resolved from 3.4's listing
            # rather than by a describe-user per member, so a name here and a name there
            # cannot disagree.
            note("listing group memberships...")
            for gid, gname in group_map:
                rep.line(f"{gname} ({gid})")
                rep.line()
                rep.text(f"""$ aws identitystore list-group-memberships \\
      --identity-store-id $IDS \\
      --group-id {gid} \\
      --query "GroupMemberships[].[MemberId.UserId,MembershipId]" \\
      --output text

""")
                res = cli.run(
                    "identitystore",
                    "list-group-memberships",
                    "--identity-store-id",
                    ids,
                    "--group-id",
                    gid,
                    "--query",
                    "GroupMemberships[].[MemberId.UserId,MembershipId]",
                    "--output",
                    "text",
                )
                if not res.ok:
                    rep.line("  !! call failed - see section 6")
                    rep.line()
                    continue
                members = [ln.split("\t") for ln in res.text.splitlines() if ln]
                if not members:
                    rep.line("  (no members)")
                    rep.line()
                    continue
                rows = ["USERNAME\tDISPLAY NAME\tUSER ID\tMEMBERSHIP ID"]
                for member_id, membership_id in members:
                    rows.append(
                        f"{user_name(member_id)}\t{user_display(member_id)}"
                        f"\t{member_id}\t{membership_id}"
                    )
                rep.tabulate(rows, indent="  ")
                rep.line()

            # --------------------------------------------------------------------------
            rep.h1("4. IAM Identity Center - permission sets")

            rep.h2("4.1 The permission set ARNs")
            rep.show(
                cli,
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                inst,
                "--output",
                "table",
            )

            res = cli.run(
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                inst,
                "--query",
                "PermissionSets[]",
                "--output",
                "text",
            )
            ps_arns = [a for a in res.text.split() if a]

            rep.h2("4.2 Permission sets, described")

            # Joined by the script: one `describe-permission-set` per ARN listed in 4.1.
            note("describing permission sets...")
            rows = ["NAME\tSESSION\tPS ID\tDESCRIPTION"]
            for ps in ps_arns:
                res = cli.run(
                    "sso-admin",
                    "describe-permission-set",
                    "--instance-arn",
                    inst,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "PermissionSet.[Name,SessionDuration,Description]",
                    "--output",
                    "text",
                )
                fields = res.text.split("\t") if res.text else []
                ps_nm = fields[0] if len(fields) > 0 and fields[0] else "-"
                ps_dur = fields[1] if len(fields) > 1 and fields[1] else "-"
                ps_desc = fields[2] if len(fields) > 2 and fields[2] else "-"
                if ps_desc == "None":
                    ps_desc = "-"
                rows.append(f"{ps_nm}\t{ps_dur}\t{ps.rsplit('/', 1)[-1]}\t{ps_desc}")
                ps_map[ps] = ps_nm
            rep.tabulate(rows)
            rep.text("""
PS ID is the tail of the ARN listed in 4.1. SESSION is the maximum session
duration, ISO-8601.""")

            rep.h2("4.3 What each permission set grants")

            for ps in ps_arns:
                rep.line()
                rep.line(f"{ps_name(ps)}  [{ps.rsplit('/', 1)[-1]}]")
                rep.line(f"  arn: {ps}")
                rep.line()

                detail(
                    None,
                    "AWS managed policies (list-managed-policies-in-permission-set)",
                    "sso-admin",
                    "list-managed-policies-in-permission-set",
                    "--instance-arn",
                    inst,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "AttachedManagedPolicies[].[Name,Arn]",
                    "--output",
                    "text",
                )

                detail(
                    None,
                    "Customer managed policy references "
                    "(list-customer-managed-policy-references-in-permission-set)",
                    "sso-admin",
                    "list-customer-managed-policy-references-in-permission-set",
                    "--instance-arn",
                    inst,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "CustomerManagedPolicyReferences[].[Name,Path]",
                    "--output",
                    "text",
                )

                detail(
                    "ResourceNotFoundException",
                    "Permissions boundary (get-permissions-boundary-for-permission-set)",
                    "sso-admin",
                    "get-permissions-boundary-for-permission-set",
                    "--instance-arn",
                    inst,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "PermissionsBoundary",
                    "--output",
                    "json",
                )

                detail(
                    None,
                    "Inline policy (get-inline-policy-for-permission-set)",
                    "sso-admin",
                    "get-inline-policy-for-permission-set",
                    "--instance-arn",
                    inst,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "InlinePolicy",
                    "--output",
                    "text",
                )

                detail(
                    None,
                    "Tags (list-tags-for-resource)",
                    "sso-admin",
                    "list-tags-for-resource",
                    "--instance-arn",
                    inst,
                    "--resource-arn",
                    ps,
                    "--query",
                    "Tags[].[Key,Value]",
                    "--output",
                    "text",
                )

            # --------------------------------------------------------------------------
            rep.h1("5. IAM Identity Center - assignments")

            # An assignment is the triple (principal, permission set, account). No API
            # lists them all, so this walks the two enumerable sides: for each permission
            # set, the accounts it is provisioned to
            # (list-accounts-for-provisioned-permission-set), then the assignments on that
            # pair (list-account-assignments). Names come from 2.4, 3.3, 3.4 and 4.2.
            rep.h2("5.1 Every assignment triple")

            note(
                "listing assignments (one call per permission set, then one per account "
                "it reaches)..."
            )
            triples: list = []
            for ps in ps_arns:
                res = cli.run(
                    "sso-admin",
                    "list-accounts-for-provisioned-permission-set",
                    "--instance-arn",
                    inst,
                    "--permission-set-arn",
                    ps,
                    "--query",
                    "AccountIds[]",
                    "--output",
                    "text",
                )
                accounts = [a for a in res.text.split() if a]

                for acct in accounts:
                    res = cli.run(
                        "sso-admin",
                        "list-account-assignments",
                        "--instance-arn",
                        inst,
                        "--account-id",
                        acct,
                        "--permission-set-arn",
                        ps,
                        "--query",
                        "AccountAssignments[].[PrincipalType,PrincipalId]",
                        "--output",
                        "text",
                    )
                    if not res.ok:
                        triples.append(
                            f"{account_name(acct)}\t{acct}\t{ps_name(ps)}"
                            "\t-\t!! call failed, see section 6\t-"
                        )
                        continue
                    assignments = [ln.split("\t") for ln in res.text.splitlines() if ln]
                    if not assignments:
                        triples.append(
                            f"{account_name(acct)}\t{acct}\t{ps_name(ps)}"
                            "\t-\t(provisioned, no assignment)\t-"
                        )
                        continue
                    for ptype, pid in assignments:
                        if ptype == "GROUP":
                            pname = group_name(pid)
                        elif ptype == "USER":
                            pname = user_name(pid)
                        else:
                            pname = "(unknown principal type)"
                        triples.append(
                            f"{account_name(acct)}\t{acct}\t{ps_name(ps)}\t{ptype}\t{pname}\t{pid}"
                        )

            def triple_key(row: str):
                f = row.split("\t")
                return (f[0], f[2], f[4])

            triples_sorted = sorted(triples, key=triple_key)
            rep.tabulate(
                ["ACCOUNT\tACCOUNT ID\tPERMISSION SET\tPRINCIPAL TYPE\tPRINCIPAL\tPRINCIPAL ID"]
                + triples_sorted
            )
            rep.text("""
A "(provisioned, no assignment)" row is a permission set still provisioned into an
account that no principal is assigned to any more.""")

            rep.h2("5.2 The same triples, grouped by account")

            rows = ["ACCOUNT\tPERMISSION SET\tPRINCIPAL"]
            for row in triples_sorted:
                f = row.split("\t")
                rows.append(f"{f[0]}\t{f[2]}\t{f[4]} ({f[3]})")
            rep.tabulate(rows)

            # --------------------------------------------------------------------------
            rep.h1("6. Calls that failed")

            if cli.errors:
                rep.text("""Each entry is a call whose output is missing above. An empty block anywhere else
in this file means the call succeeded and returned nothing.

""")
                rep.line(cli.errors.text())
            else:
                rep.line("None. Every call in this report returned successfully.")

            rep.line()
            rep.line("Regenerate with:  ./aws/list-identities.py")

    # ---------------------------------------------------------------------------------- run
    note("")
    if status == 0:
        if cli.errors:
            note(f"wrote {out_label} (some calls failed - see section 6)")
        else:
            note(f"wrote {out_label}")
    else:
        note(f"wrote {out_label} (INCOMPLETE - the section 3.2 check failed)")
    return status


if __name__ == "__main__":
    sys.exit(main())
