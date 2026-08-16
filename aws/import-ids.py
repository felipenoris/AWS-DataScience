#!/usr/bin/env -S uv run --quiet
# import-ids.py - the exact strings `terraform import` takes, for every object Stage 2
# step 5 brings into state. The import manifest.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/import-ids.py                    # awsds-infra-identity
#             python3 aws/import-ids.py -            # CloudShell, ambient credentials
#   writes:   aws/output/import-ids.txt   (untracked - see .gitignore)
#   reads:    organizations:DescribeOrganization, ListRoots, ListOrganizationalUnitsForParent,
#             ListAccountsForParent, ListPolicies, ListTargetsForPolicy,
#             sso-admin:ListInstances, ListPermissionSets, DescribePermissionSet,
#             ListManagedPoliciesInPermissionSet, GetInlinePolicyForPermissionSet,
#             ListAccountsForProvisionedPermissionSet, ListAccountAssignments,
#             identitystore:DescribeGroup, DescribeUser, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 the manifest was produced | 1 a call failed
#
# WHY THIS IS A SCRIPT OF ITS OWN, AND NOT A SECTION IN list-identities.py. That file answers
# "who can reach what" and is read by a person, who tolerates a stale line and notices a wrong
# one. THIS file is a RENDERING whose only consumer is a shell. Its failure mode is different
# in kind: a wrong id does not read oddly, it imports the wrong object - or, more often,
# imports nothing under an address the configuration does not use, leaving `terraform plan`
# proposing to CREATE a policy that already exists while an orphan sits in state. That is the
# dangerous outcome Stage 2's Risks name, and it is worth a file that does one job.
#
# THE DIVISION OF LABOUR, WHICH IS THE DISCIPLINE OF SECTION 5. This script is authoritative
# about the RIGHT-HAND SIDE - the id. It is NOT authoritative about the left-hand side, the
# Terraform address: that belongs to the configuration, and only the configuration knows
# whether a resource is `aws_organizations_policy.baseline` or
# `aws_organizations_policy.this["awsds-org-scp-baseline"]`. So every line carries a SUGGESTED
# address that must be checked against the code, and the section says so rather than implying
# a copy-paste is safe.
#
# THE ONE THAT GOES WRONG, stated where it will be read: AN IMPORT INTO A `for_each` RESOURCE.
# The address is `...this["<key>"]` and the key has to be exactly what the configuration
# COMPUTES, not what reads naturally. A wrong key does not error. Import ONE, run `plan`, and
# only then import the rest.
#
# WHAT IT DELIBERATELY REFUSES TO EMIT, in section 4 - because the expensive mistake here is
# importing something that must stay outside Terraform, and an operator working from a
# complete-looking list will import all of it:
#   - Control Tower's `aws-guardrails-*` policies. Managing them from Terraform puts Terraform
#     and Control Tower in a fight over the same object: landing-zone drift (Stage 2 step 5.4).
#   - Control Tower's permission sets, `AWSAdministratorAccess` first among them. A permission
#     set provisioned into Management cannot even be altered from Identity - measured
#     2026-08-12, Stage 1b step 5.1 - and the deny is anchored on the SET, so it covers that
#     set's assignments in every account.
#   - The Account Factory DIRECT assignments (D32). They are a permanent property of a vended
#     account, not something to model.
# These are LISTED, with the reason, rather than filtered silently: a manifest that quietly
# omits things is one nobody can tell apart from a manifest that missed them.
#
# IDENTITY. `awsds-infra-identity`, which is both the Identity Center delegated administrator
# (D10) and an account whose Organizations reads already answer (Stage 1c verification (x)).
# One profile reaches both planes, which is why this is one script.

from __future__ import annotations

import os
import sys
from collections import deque

from awslib import context
from awslib.awscli import AwsCli
from awslib.report import Report, note

OUT_NAME = "import-ids.txt"

POLICY_TYPES = [
    "SERVICE_CONTROL_POLICY",
    "RESOURCE_CONTROL_POLICY",
    "TAG_POLICY",
    "DECLARATIVE_POLICY_EC2",
]

# The account NAME as Organizations reports it -> the terraform-live/ FOLDER, which is the
# for_each key terraform-live/identity/sso/ computes for an assignment (Stage 2 step 5.3).
#
# THIS SCRIPT FOLLOWS AND THE SLICE OWNS. The same five rows are locals.accounts there, and
# that file is the authority: it is what the apply reads. They are repeated here rather than
# parsed out of HCL because the alternative is a regex over a .tf file, which fails silently
# on a reformat - and a wrong key is precisely the failure step 5.5a(iii) is about: it does not
# error, it plans a create beside an orphan.
#
# AN ACCOUNT MISSING FROM THIS TABLE IS NOT AN ERROR. Management, Audit, Log Archive and Policy
# Canary hold no assignment this repository manages, and `Staging` arrives at the vend - the
# emitted key says <UNMAPPED:...> so the line is unrunnable rather than plausible.
ACCOUNT_FOLDER_BY_NAME = {
    "Sandbox Account 1": "sandbox",
    "Development Account": "development",
    "Data Governance Account": "data-governance",
    "Production Account": "production",
    "Identity Account": "identity",
}


def account_folder(account_id: str, account_name: str | None) -> str:
    """The sso/ slice's for_each key for an account, or a marker that cannot be pasted."""
    if account_name and account_name in ACCOUNT_FOLDER_BY_NAME:
        return ACCOUNT_FOLDER_BY_NAME[account_name]
    return f"<UNMAPPED:{account_name or account_id}>"


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

    # ---------------------------------------------------------------- the organization anchors
    note("reading the organization anchors...")

    res = cli.run(
        "organizations",
        "describe-organization",
        "--query",
        "Organization.[Id,MasterAccountId]",
        "--output",
        "text",
    )
    f = res.text.split("\t") if res.text else []
    org_id = f[0] if len(f) > 0 else ""
    mgmt_id = f[1] if len(f) > 1 else ""

    res = cli.run(
        "organizations", "list-roots", "--query", "Roots[0].[Name,Id]", "--output", "text"
    )
    f = res.text.split("\t") if res.text else []
    root_name = f[0] if len(f) > 0 else ""
    root_id = f[1] if len(f) > 1 else ""

    # Walk the tree breadth-first: depth is 2 (D23, `Sandboxes` under `Interactive`) and a
    # walk written for depth 1 misses it silently - the same nesting that breaks a
    # single-level `for_each` in Stage 2 step 5.3.
    nodes = [("ROOT", root_name, root_id, f"{org_id}/{root_id}/")]
    queue = deque([(root_id, f"{org_id}/{root_id}/")])
    while queue:
        pid, ppath = queue.popleft()
        res = cli.run(
            "organizations",
            "list-organizational-units-for-parent",
            "--parent-id",
            pid,
            "--query",
            "OrganizationalUnits[].[Name,Id]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) < 2 or not f[1]:
                continue
            nname, nid = f[0], f[1]
            npath = f"{ppath}{nid}/"
            nodes.append(("OU", nname, nid, npath))
            queue.append((nid, npath))

    # The `Data` OU and its single account. <ACCOUNT_ID_DATA> feeds awsds-org-scp-ou-data.json;
    # <ORG_PATH_DATA> feeds awsds-org-scp-BASELINE.json (the DenyDataZoneDomainOutsideDataOu
    # condition). Stage 2 step 5.5a(ii): derive from the OU, never by account NAME (1d step 9
    # recorded why a name lookup returns None here).
    ou_id_data = next((nid for _k, name, nid, _p in nodes if name == "Data"), "")
    org_path_data = next((p for _k, name, _nid, p in nodes if name == "Data"), "")
    account_id_data = ""
    n_data_accts = 0
    if ou_id_data:
        res = cli.run(
            "organizations",
            "list-accounts-for-parent",
            "--parent-id",
            ou_id_data,
            "--query",
            "Accounts[].Id",
            "--output",
            "text",
        )
        ids = [a for a in res.text.split() if a]
        account_id_data = ids[0] if ids else ""
        n_data_accts = len(ids)

    # The roster, read for ONE purpose: turning an account id into the terraform-live/ FOLDER
    # the sso/ slice keys its assignments on (section 5d). Names are the only handle the API
    # offers, and they are not the names anybody would guess - Control Tower vended every
    # account with an ` Account` suffix, and Stage 1d step 9 already paid for that once.
    acct_names = {}
    res = cli.run(
        "organizations",
        "list-accounts",
        "--query",
        "Accounts[?Status=='ACTIVE'].[Id,Name]",
        "--output",
        "text",
    )
    for line in res.text.splitlines():
        f = line.split("\t")
        if len(f) >= 2 and f[0]:
            acct_names[f[0]] = f[1]

    # ----------------------------------------------------------------- the organization policies
    note("listing the organization policies, all four types...")

    policies = []  # (type, pid, pname, ours yes|no)
    for ptype in POLICY_TYPES:
        res = cli.run(
            "organizations",
            "list-policies",
            "--filter",
            ptype,
            "--query",
            "Policies[?AwsManaged==`false`].[Id,Name]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) < 2 or not f[0]:
                continue
            pid, pname = f[0], f[1]
            ours = "yes" if pname.startswith("awsds-") else "no"
            policies.append((ptype, pid, pname, ours))

    note("listing each policy's targets...")
    attach = []  # (pid, pname, target id, target name, target type)
    for ptype, pid, pname, ours in policies:
        if ours != "yes":
            continue
        res = cli.run(
            "organizations",
            "list-targets-for-policy",
            "--policy-id",
            pid,
            "--query",
            "Targets[].[TargetId,Name,Type]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) < 3 or not f[0]:
                continue
            attach.append((pid, pname, f[0], f[1], f[2]))

    # --------------------------------------------------------------------- Identity Center
    note("reading the Identity Center instance...")

    res = cli.run(
        "sso-admin",
        "list-instances",
        "--query",
        "Instances[0].[InstanceArn,IdentityStoreId]",
        "--output",
        "text",
    )
    f = res.text.split("\t") if res.text else []
    instance_arn = f[0] if len(f) > 0 else ""
    store_id = f[1] if len(f) > 1 else ""

    psets = []  # (arn, name, ours yes|no)
    managed = []  # (ps arn, ps name, managed policy arn)
    inline = []  # (ps arn, ps name, yes|no)
    assign = []  # (ps arn, ps name, acct, principal type, principal id, principal name)

    if instance_arn:
        note("listing permission sets...")
        res = cli.run(
            "sso-admin",
            "list-permission-sets",
            "--instance-arn",
            instance_arn,
            "--query",
            "PermissionSets",
            "--output",
            "text",
        )
        for psarn in (a for a in res.text.split() if a):
            res = cli.run(
                "sso-admin",
                "describe-permission-set",
                "--instance-arn",
                instance_arn,
                "--permission-set-arn",
                psarn,
                "--query",
                "PermissionSet.Name",
                "--output",
                "text",
            )
            psname = res.text or "(unnamed)"
            # "Ours" is exactly the set Stage 2 imports: InfrastructureAccess and nothing
            # else. The other six persona sets are WRITTEN in step 5, never imported (Stage
            # 1b step 3.9), and Control Tower's are landing-zone drift if touched.
            ours = "yes" if psname == "InfrastructureAccess" else "no"
            psets.append((psarn, psname, ours))

        note("listing assignments...")
        for psarn, psname, ours in psets:
            if ours != "yes":
                continue

            res = cli.run(
                "sso-admin",
                "list-managed-policies-in-permission-set",
                "--instance-arn",
                instance_arn,
                "--permission-set-arn",
                psarn,
                "--query",
                "AttachedManagedPolicies[].Arn",
                "--output",
                "text",
            )
            for marn in (a for a in res.text.split() if a):
                managed.append((psarn, psname, marn))

            res = cli.run(
                "sso-admin",
                "get-inline-policy-for-permission-set",
                "--instance-arn",
                instance_arn,
                "--permission-set-arn",
                psarn,
                "--query",
                "InlinePolicy",
                "--output",
                "text",
            )
            inline.append((psarn, psname, "yes" if res.text and res.text != "None" else "no"))

            res = cli.run(
                "sso-admin",
                "list-accounts-for-provisioned-permission-set",
                "--instance-arn",
                instance_arn,
                "--permission-set-arn",
                psarn,
                "--query",
                "AccountIds",
                "--output",
                "text",
            )
            for acct in (a for a in res.text.split() if a):
                res = cli.run(
                    "sso-admin",
                    "list-account-assignments",
                    "--instance-arn",
                    instance_arn,
                    "--account-id",
                    acct,
                    "--permission-set-arn",
                    psarn,
                    "--query",
                    "AccountAssignments[].[PrincipalType,PrincipalId]",
                    "--output",
                    "text",
                )
                for line in res.text.splitlines():
                    f = line.split("\t")
                    if len(f) < 2 or not f[1]:
                        continue
                    ptype2, prid = f[0], f[1]
                    prname = "(unresolved)"
                    if ptype2 == "GROUP":
                        r = cli.run(
                            "identitystore",
                            "describe-group",
                            "--identity-store-id",
                            store_id,
                            "--group-id",
                            prid,
                            "--query",
                            "DisplayName",
                            "--output",
                            "text",
                        )
                        prname = r.text or "(unresolved)"
                    elif ptype2 == "USER":
                        r = cli.run(
                            "identitystore",
                            "describe-user",
                            "--identity-store-id",
                            store_id,
                            "--user-id",
                            prid,
                            "--query",
                            "UserName",
                            "--output",
                            "text",
                        )
                        prname = r.text or "(unresolved)"
                    assign.append((psarn, psname, acct, ptype2, prid, prname))

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        def imp(what: str, address: str, import_id: str) -> None:
            """One manifest line: the suggested address on the left, the measured id on
            the right, visibly separate - which is the whole point of section 5."""
            rep.line(f"# {what}")
            rep.line(f"terraform import '{address}' '{import_id}'")
            rep.line()

        rep.banner("The import manifest - what `terraform import` takes, for Stage 2 step 5")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {cli.label}
caller    : {caller}
produced  : aws/import-ids.py   (index: aws/INDEX.md)

SECTIONS
  1. The anchors, and the values the policy TEMPLATES need
  2. The organization policies and their targets
  3. Identity Center - the instance, the sets, the assignments
  4. WHAT MUST NOT BE IMPORTED, and why - read before section 5
  5. THE MANIFEST - the `terraform import` lines
  6. Calls that failed

HOW TO READ THIS FILE
  - THIS SCRIPT OWNS THE RIGHT-HAND SIDE, NOT THE LEFT. The id after the address is
    measured and correct. The ADDRESS is a suggestion: only the configuration knows
    whether the resource is `.baseline` or `.this["awsds-org-scp-baseline"]`.
  - AN IMPORT INTO A `for_each` RESOURCE IS THE ONE THAT GOES WRONG. The key has to
    be exactly what the configuration COMPUTES. A wrong key does not error - it
    leaves an orphan in state and a create in the plan. Import ONE, run `plan`, then
    the rest.
  - SECTION 4 IS NOT A FOOTNOTE. Importing a Control Tower policy or permission set
    is landing-zone drift, and the objects are listed there rather than filtered out
    so that an omission is distinguishable from an oversight.
  - THE IDS HERE ARE IDENTIFIERS. This file is untracked, like every snapshot under
    aws/output/. Nothing in it is copied into a tracked file (aws/INDEX.md rule 1) -
    which is also why Stage 2 decision 6 leans towards `terraform import` on the
    command line rather than `import {{}}` blocks, whose `id` would live in git.""")

        # ==============================================================================
        rep.h1("1. The anchors, and the values the policy TEMPLATES need")

        rep.tabulate(
            [
                "NAME\tVALUE\tWHAT IT IS",
                f"ORG_ID\t{org_id or '(unread)'}\tthe value aws:PrincipalOrgID and "
                "aws:ResourceOrgID are compared against",
                f"ROOT_ID\t{root_id or '(unread)'}\tthe organization root - the target of six "
                "of the ten documents",
                f"MGMT_ID\t{mgmt_id or '(unread)'}\tthe management account; the ARN namespace "
                "of every organizations:: ARN",
                f"INSTANCE_ARN\t{instance_arn or '(unread)'}\tthe Identity Center instance - "
                "the tail of every sso-admin import id",
                f"IDENTITY_STORE\t{store_id or '(unread)'}\tthe directory the group GUIDs "
                "belong to",
            ]
        )

        rep.text("""
THE THREE PLACEHOLDERS IN terraform-live/identity/org-policies/policies/*.json, and
what Terraform has to substitute for each (Stage 2 step 5.5a):

""")

        rep.tabulate(
            [
                "PLACEHOLDER\tRESOLVED VALUE\tWHERE TERRAFORM GETS IT",
                f"<ORG_ID>\t{org_id or '(unread)'}\tdata.aws_organizations_organization.this.id",
                f"<ORG_PATH_DATA>\t{org_path_data or '(unread)'}\tthe Data OU path, composed "
                "from the org, root and OU ids",
                f"<ACCOUNT_ID_DATA>\t{account_id_data or '(unread)'}\tthe single account under "
                "the Data OU - derived from the OU",
            ]
        )

        rep.text(f"""
TWO THINGS ABOUT THAT TABLE THAT ARE NOT DECORATION.

  - `templatefile()` CANNOT READ THESE TEMPLATES. The placeholders are angle-bracketed,
    not ${{...}}, on purpose (render.py explains why, and it anticipated this stage). The
    Terraform side is `replace(file(...), "<ORG_ID>", ...)`, wrapped in
    `jsonencode(jsondecode(...))` so BOTH sides are normalised the same way - which is
    what turns "the same document" from a claim about whitespace into one about content.
  - <ACCOUNT_ID_DATA> IS DERIVED FROM THE OU, NEVER FROM AN ACCOUNT NAME. Stage 1d step
    9 recorded why: a name filter returns None here, because the account is called
    `Data Governance Account` and not `Data Governance`. The Data OU holds exactly one
    account, so the OU is the safe handle.

Accounts under the Data OU: {n_data_accts} (expected: 1 - if this reads more, the derivation above
is ambiguous and the document needs an explicit choice rather than a head -1).""")

        # ==============================================================================
        rep.h1("2. The organization policies and their targets")

        rep.text("""AwsManaged policies (FullAWSAccess, RCPFullAWSAccess) are excluded - they are AWS`s
and cannot be imported. What is left is everything this organization created.

""")

        if policies:
            ordered = sorted(policies, key=lambda p: (p[3], "\t".join(p)))
            rep.tabulate(
                ["OURS\tTYPE\tPOLICY ID\tNAME"]
                + [f"{ours}\t{ptype}\t{pid}\t{pname}" for ptype, pid, pname, ours in ordered]
            )
        else:
            rep.line("(none found - see section 6)")

        rep.text("""
THE ATTACHMENTS, which are separate objects and separate imports. `aws_organizations_
policy_attachment` takes `<target_id>:<policy_id>` - the ONE import id in this file
that is a composite with a colon rather than commas.

""")

        if attach:
            rep.tabulate(
                ["POLICY\tPOLICY ID\tTARGET\tTARGET ID\tTARGET TYPE"]
                + [
                    f"{pname}\t{pid}\t{tname}\t{tid}\t{ttype}"
                    for pid, pname, tid, tname, ttype in sorted(attach)
                ]
            )
            rep.line()
            n_root = sum(1 for a in attach if a[4] == "ROOT")
            n_ou = sum(1 for a in attach if a[4] == "ORGANIZATIONAL_UNIT")
            rep.text(f"""{n_root} attachment(s) to the ROOT, {n_ou} to an OU.
THE ROOT COUNT IS THE ONE THAT DECIDES THE SIZE OF STAGE 2 - it is what Stage 2
step 5.0 and ./aws/org-delegation.py`s DEL-6 are about. If the delegation cannot
reach root attachments, every one of those rows stays console-managed.""")
        else:
            rep.line("(no attachments found - see section 6)")

        # ==============================================================================
        rep.h1("3. Identity Center - the instance, the sets, the assignments")

        if psets:
            ordered = sorted(psets, key=lambda p: (p[2], "\t".join(p)))
            rep.tabulate(
                ["IMPORT?\tNAME\tPERMISSION SET ARN"]
                + [f"{ours}\t{name}\t{arn}" for arn, name, ours in ordered]
            )
        else:
            rep.line("(no permission sets found - see section 6)")

        rep.text("""
ONLY `InfrastructureAccess` IS MARKED yes, AND THAT IS THE DESIGN, NOT A FILTER BUG.
The other six persona sets - DataScientistAccess, DataScientistStagingAccess,
DataScientistProdAccess, DeploymentManagerAccess, GovernanceManagerAccess,
DevEnvStewardAccess - are WRITTEN in Stage 2 step 5 and were never typed into a
console (Stage 1b step 3.9), so there is nothing to import and their first apply is a
CREATE. An empty plan there would mean nothing was written.

""")
        rep.h2("Assignments of the imported set")

        if assign:
            rep.tabulate(
                ["ACCOUNT\tPRINCIPAL TYPE\tPRINCIPAL\tPRINCIPAL ID\tPERMISSION SET"]
                + [
                    f"{acct}\t{ptype2}\t{prname}\t{prid}\t{psname}"
                    for _arn, psname, acct, ptype2, prid, prname in sorted(assign)
                ]
            )
            rep.text("""
THE PRINCIPAL ID IS A GUID AND THE IMPORT NEEDS IT - but the CONFIGURATION must not
carry it. `docs/plan/conventions.md` requires a group to be resolved by DISPLAY NAME
through `data.aws_identitystore_group`, because group IDs are properties of ONE
directory instance: federate to a corporate IdP and every hardcoded GUID becomes a
resource that matches nothing. So the GUID goes on the import command line and the
display name goes in the code - and this table is where the two are seen together.""")
        else:
            rep.line("(no assignments found for the imported set - see section 6)")

        # ==============================================================================
        rep.h1("4. WHAT MUST NOT BE IMPORTED, and why")

        rep.text("""Listed rather than filtered out, so that "not here" and "missed" stay distinguishable.

""")

        rep.h2("Control Tower's policies - importing one is landing-zone drift")

        ct_policies = [(ptype, pid, pname) for ptype, pid, pname, ours in policies if ours == "no"]
        if ct_policies:
            rep.tabulate(
                ["TYPE\tPOLICY ID\tNAME"]
                + [
                    f"{ptype}\t{pid}\t{pname}"
                    for ptype, pid, pname in sorted(ct_policies, key=lambda p: p[2])
                ]
            )
        else:
            rep.line("(none)")
        rep.text("""
These are generated and owned by the landing zone (Stage 2 step 5.4). Importing one
puts Terraform and Control Tower in a fight over the same object. If the REGION
restriction is ever to be in code, the resource is `aws_controltower_control` - the
control, not the SCP it emits.
""")

        rep.h2("Control Tower's permission sets - and one of them cannot even be reached")

        ct_psets = [(name, arn) for arn, name, ours in psets if ours == "no"]
        if ct_psets:
            rep.tabulate(
                ["NAME\tPERMISSION SET ARN"] + sorted(f"{name}\t{arn}" for name, arn in ct_psets)
            )
        else:
            rep.line("(none)")
        rep.text("""
`AWSAdministratorAccess` is the one to know about: a permission set PROVISIONED INTO
MANAGEMENT cannot be altered from the Identity account at all - measured 2026-08-12,
Stage 1b step 5.1 - and the deny is anchored on the SET rather than on the target
account, so it covers that set`s assignments in EVERY account. Anything touching it
runs as `AWS Control Tower Admin` on Management.

ALSO NOT MODELLED: the Account Factory DIRECT assignments (D32). `Policy Canary` still
carries one, permanently - it is the only way into that account. A direct assignment is
a property of a vended account, not an entitlement this repository designs.

AND NOT IN ANY STATE FILE, EVER: the four users, the five groups and the memberships.
They are people. `docs/plan/conventions.md`, "The identity seam".""")

        # ==============================================================================
        rep.h1("5. THE MANIFEST - the `terraform import` lines")

        rep.text("""CHECK EVERY ADDRESS AGAINST THE CONFIGURATION BEFORE RUNNING A LINE. The id is
measured; the address is a suggestion in the shape Stage 2 step 5.3 implies
(`for_each` in org-policies/, written-out resources in sso/).

Run them from inside the slice directory, with the right profile:

    AWS_PROFILE=awsds-infra-identity terraform import ...

and NEVER through `eval $(aws sts assume-role ...)` - an exported credential outlives
the command that needed it and every later error then names the wrong account
(Lesson 25).""")

        rep.h2("5a. terraform-live/identity/org-policies/ - the documents")

        emitted = False
        for ptype, pid, pname, ours in policies:
            if ours != "yes":
                continue
            emitted = True
            imp(f"{pname}  ({ptype})", f'aws_organizations_policy.this["{pname}"]', pid)
        if not emitted:
            rep.line("(nothing to emit)")
            rep.line()

        rep.h2("5b. terraform-live/identity/org-policies/ - the attachments")

        rep.text("""# ONE PER (policy, target) PAIR. The import id is <target_id>:<policy_id>.
# Import the FIRST one, run `terraform plan`, and only then the rest - if the
# for_each key is wrong the import succeeds and the plan proposes a create.
#
# THE KEY'S TARGET HALF IS THE AUTHORED MAP'S VOCABULARY, NOT THE API'S. The slice
# builds its for_each from attachments.json, where the root is the literal key
# `root` and an OU is its NAME - so the composed key is `<document>:root` or
# `<document>:<OU name>`. The Organizations API calls the root `Root`, and that is
# the one place the two vocabularies differ. This script follows the slice (the
# configuration owns the address, section 5's division of labour), which is the
# same correction the sso/ assignments needed on 2026-08-16.

""")

        if attach:
            for pid, pname, tid, tname, ttype in attach:
                target_key = "root" if ttype == "ROOT" else tname
                imp(
                    f"{pname} -> {tname} ({ttype})",
                    f'aws_organizations_policy_attachment.this["{pname}:{target_key}"]',
                    f"{tid}:{pid}",
                )
        else:
            rep.line("(nothing to emit)")
            rep.line()

        rep.h2("5c. terraform-live/identity/sso/ - the imported permission set")

        if instance_arn and psets:
            for psarn, psname, ours in psets:
                if ours != "yes":
                    continue
                imp(
                    f"{psname} - the permission set itself",
                    "aws_ssoadmin_permission_set.infrastructure",
                    f"{psarn},{instance_arn}",
                )

            for psarn, psname, marn in managed:
                base = marn.rsplit("/", 1)[-1]
                imp(
                    f"{psname} - managed policy {base}",
                    # A SINGLETON, NOT A for_each - the configuration declares exactly one
                    # (terraform-live/identity/sso/infrastructure-access.tf). This set carries
                    # one managed policy and it is AdministratorAccess, the one named exception
                    # in the IAM rules; a for_each here would suggest the list is open.
                    "aws_ssoadmin_managed_policy_attachment.infrastructure_admin",
                    f"{marn},{psarn},{instance_arn}",
                )

            for psarn, psname, has in inline:
                if has != "yes":
                    continue
                imp(
                    f"{psname} - its inline policy",
                    "aws_ssoadmin_permission_set_inline_policy.infrastructure",
                    f"{psarn},{instance_arn}",
                )
        else:
            rep.line("(nothing to emit - the Identity Center instance was not read, see section 6)")
            rep.line()

        rep.h2("5d. terraform-live/identity/sso/ - the assignments")

        rep.text("""# SIX comma-separated fields, in this order:
#   <principal_id>,<principal_type>,<target_id>,<target_type>,<permission_set_arn>,<instance_arn>
# The principal id is the GUID; the CONFIGURATION resolves the same group by display
# name through data.aws_identitystore_group (section 3).
#
# THE ADDRESS KEY IS THE ACCOUNT FOLDER of terraform-live/, because that is what the
# configuration computes - locals.accounts in terraform-live/identity/sso/, keyed on
# the same vocabulary as scripts/tfhygiene/backend.py. It is resolved here through the
# account NAME, which is the only handle the API offers, and the five rows of that map
# are repeated in ACCOUNT_FOLDER_BY_NAME below: the slice owns them, this script
# follows. A key that says <UNMAPPED:...> is an account the slice does not assign -
# not a bug in either file, and not a line to run.

""")

        if assign and instance_arn:
            for psarn, psname, acct, ptype2, prid, prname in assign:
                folder = account_folder(acct, acct_names.get(acct))
                imp(
                    f"{psname} for {prname} on account {acct}",
                    f'aws_ssoadmin_account_assignment.infrastructure["{folder}"]',
                    f"{prid},{ptype2},{acct},AWS_ACCOUNT,{psarn},{instance_arn}",
                )
        else:
            rep.line("(nothing to emit)")
            rep.line()

        # ==============================================================================
        rep.h1("6. Calls that failed")

        if cli.errors:
            rep.line(cli.errors.text())
            rep.text("""
A MANIFEST WITH A FAILED CALL IN IT IS INCOMPLETE, NOT WRONG - and the difference
matters: importing from a short list leaves objects unmanaged with an empty plan,
which looks exactly like success. Fix the failure and regenerate before importing.""")
        else:
            rep.line("None. Every call returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/import-ids.py")

    # ---------------------------------------------------------------------------------- run
    note("")
    if cli.errors:
        note(f"wrote {out_label} (some calls FAILED - see section 6; the manifest is INCOMPLETE)")
        return 1
    note(f"wrote {out_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
