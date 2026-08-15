#!/usr/bin/env -S uv run --quiet
# org-policy-baseline.py - the ceiling that already exists: every organization node, the
# policies attached to it, the Control Tower controls enabled on it, and the quota that
# says how much more will fit.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile in ~/.aws/config that declares
#             `sso_session = awsds` (see aws/INDEX.md).
#
#   run:      ./aws/org-policy-baseline.py                   # awsds-infra-identity
#             ./aws/org-policy-baseline.py awsds-infra-dev   # a different profile
#             python3 aws/org-policy-baseline.py -           # no --profile: CloudShell on
#                                                            # MANAGEMENT, as CT Admin (no
#                                                            # uv there; bring aws/)
#   writes:   aws/output/org-policy-baseline.txt   (untracked - see .gitignore)
#   reads:    organizations:DescribeOrganization, ListRoots,
#             ListOrganizationalUnitsForParent, ListPoliciesForTarget, DescribePolicy,
#             controltower:ListEnabledControls, servicequotas:ListServiceQuotas,
#             sts:GetCallerIdentity. This script never creates, updates or deletes anything.
#
# WHY THIS EXISTS. Stage 1c step 7.0 is a preflight: five measurements that every policy in
# 7.5-7.8 needs as input, collected in one pass *before* the first `create-policy`. Written
# out by hand they are a dozen commands with ids threaded between them, run in the evening,
# at the start of the one landing-zone step that has no in-account repair. Three of the five
# are here (7.0 steps 1, 2, 3) plus the quota (step 5); step 4 is per-account and lives in
# aws/account-bpa.py, because its subject is the difference between accounts.
#
# The three things it is collected FOR, so that a reader knows what to do with each section:
#   - The ids, ARNs and full OU PATHS that 7.5's `aws:PrincipalOrgPaths` carve-out and 7.7's
#     control targets are written from. A path derived at 23:00 is how a policy lands on the
#     wrong node.
#   - The GAP. Control Tower's mandatory controls already deny changes to CloudTrail and to
#     the Config recorder on every registered OU, with the service-role carve-outs that keep
#     the landing zone able to update itself. Section 4 prints those documents so that 7.5
#     writes only what is missing instead of a second, thinner copy of them (verification
#     (iii) - which is a thing to read BEFORE writing, not to notice afterwards).
#   - The BUDGET. 10 SCPs per node and 10 240 characters per document since May 2026, but
#     RCPs are still 5 and 5 120, and 7.7 spends one more SCP slot on every OU it touches.
#     Section 6 goes looking for those numbers rather than trusting a remembered one
#     (Lesson 6 applied to a quota) - and its first run, 2026-08-13, found that Service
#     Quotas publishes NONE of them for `organizations`, only account counts. That is a
#     finding about the API, not about the limits: the numbers above are AWS's own, from the
#     announcement recorded in docs/REFERENCES.md.
#
# IDENTITY, and the question this script answers by running. Organizations is administered
# from the management account, for which there is no local profile and never will be
# (guiding principle 1). Reads are a different matter: Stage 1b step 4 measured that a
# delegated administrator answers the Organizations read surface, and 2026-08-12 extended
# that to the trusted-access calls. Whether it extends to the *policy* reads
# (ListPoliciesForTarget, DescribePolicy) is Stage 1c verification (x), open at the time
# this script was written - so the script does not assume it: a denial is reported in full
# in the last section, with a non-zero exit, and the fallback is one line in CloudShell on
# the management account as `AWS Control Tower Admin`:
#
#     python3 aws/org-policy-baseline.py -
#
# Record in docs/log/ which identity the answer actually required. `controltower
# list-enabled-controls` (section 5) is expected to need that fallback even if the
# Organizations reads do not - it is not an Organizations call at all.
#
# WHAT IT CANNOT SEE, stated because an empty block and a missing thing look alike:
#   - A policy type that is not ENABLED on the root cannot be listed per target: the call
#     raises instead of returning empty, and section 3 prints `(policy type not enabled)`.
#     Today that is the expected answer for RCP, tag and declarative policies - it is
#     Stage 1c step 7.2's precondition, measured rather than assumed.
#   - An UNREGISTERED target errors on list-enabled-controls rather than returning an empty
#     list, and section 5 keeps the two apart on purpose (Lesson 13). 7.7 may not enable a
#     control on an OU this call rejected.
#   - Accounts are not listed here at all. The tree with its accounts is
#     aws/list-identities.py section 2.3; this script's subject is the NODES and what is
#     attached to them, which is why it prints ARNs and paths that one does not.

from __future__ import annotations

import os
import sys
from collections import deque
from dataclasses import dataclass

from awslib import context
from awslib.awscli import AwsCli, head2
from awslib.report import Report, note

OUT_NAME = "org-policy-baseline.txt"
QUOTA_REGION = "us-east-1"  # Organizations quotas answer in us-east-1 only

POLICY_TYPES = [
    "SERVICE_CONTROL_POLICY",
    "RESOURCE_CONTROL_POLICY",
    "TAG_POLICY",
    "DECLARATIVE_POLICY_EC2",
]


@dataclass
class Node:
    kind: str  # ROOT | OU
    name: str
    node_id: str
    arn: str
    path: str  # the full aws:PrincipalOrgPaths value, trailing slash included
    depth: int


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

    seen_policies: dict = {}  # pid -> (name, aws_managed) - remembered for section 4

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner(
            "The organization ceiling as it stands: nodes, attached policies, enabled controls"
        )
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {cli.label}
caller    : {caller}
region    : {cli.region}   (Organizations is global; quotas are read in {QUOTA_REGION})
produced  : aws/org-policy-baseline.py   (index: aws/INDEX.md)

SECTIONS
  1. The organization: id, feature set, root, enabled policy types
  2. Every node - id, ARN and the full PATH a policy condition needs
  3. Policies attached per node, per policy type
  4. The documents of the policies found - what is ALREADY denied
  5. Control Tower controls enabled per node, and whether the node is registered
  6. The quota: how many policies fit on one node, and how large each may be
  7. Calls that failed

HOW TO READ THIS FILE
  - THIS IS AN INPUT TO WRITING POLICY, not a record of it. Stage 1c step 7.0.
    What was decided from it goes in docs/log/log-stage-01c-preventive-policies.md; the
    documents themselves go in terraform-live/identity/org-policies/policies/.
  - SECTION 4 IS THE ONE THAT SHRINKS THE WORK. Control Tower mandatory controls
    already deny changes to CloudTrail and to the Config recorder on every
    REGISTERED OU, with the carve-outs (AWSControlTowerExecution,
    aws-controltower-ConfigRecorderRole) that keep the landing zone able to update
    itself. Write only the gap: a hand-written duplicate costs SCP budget and adds
    a second place to get those carve-outs wrong.
  - `(policy type not enabled)` in section 3 is a MEASUREMENT, not a failure: the
    type has to be enabled on the root before anything of that type can attach
    (step 7.2). Only SERVICE_CONTROL_POLICY is expected to be enabled today.
  - IN SECTION 5, AN ERROR AND AN EMPTY LIST MEAN DIFFERENT THINGS. An unregistered
    target errors; a registered one with no elective control returns an empty list.
    7.7 may not enable a control on a target this call rejected (Lesson 13).
  - Every "$ aws ..." line is the exact command that produced the block under it,
    minus `--region` and the profile, which every command carries.
  - This is a point-in-time snapshot, not a source of truth: regenerate it rather
    than trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ------------------------------------------------------------------------------
        rep.h1("1. The organization: id, feature set, root, enabled policy types")

        note("describing the organization...")
        rep.show(
            cli,
            "organizations",
            "describe-organization",
            "--query",
            "Organization.[Id,FeatureSet,MasterAccountId,Arn]",
            "--output",
            "table",
        )

        rep.text("""FeatureSet must read ALL: RESOURCE_CONTROL_POLICY requires an organization with all
features enabled, and half of Stage 1c has nowhere to attach without it.

""")

        res = cli.run(
            "organizations",
            "describe-organization",
            "--query",
            "Organization.Id",
            "--output",
            "text",
        )
        org_id = res.text or "<o-unknown>"
        rep.line(f"ORG_ID={org_id}")
        rep.line()

        rep.text("""ORG_ID is the value both data-perimeter condition keys are compared against:
aws:PrincipalOrgID (is the CALLER inside my organization?) and aws:ResourceOrgID
(is the RESOURCE being written to?) - the two axes of docs/plan/architecture.md. It is
also what terraform-live/identity/org-policies/render.py substitutes for the
<ORG_ID> placeholder of the Stage 1c documents, so no paste of it is done by hand.""")

        rep.h2("1.2 The root, and the policy types that may be attached at all")

        note("listing roots...")
        rep.show(
            cli,
            "organizations",
            "list-roots",
            "--query",
            "Roots[].[Id,Name,Arn]",
            "--output",
            "table",
        )

        res = cli.run("organizations", "list-roots", "--query", "Roots[0].Id", "--output", "text")
        root_id = res.text or "<r-unknown>"
        rep.line(f"ROOT_ID={root_id}")
        rep.line()

        rep.show(
            cli,
            "organizations",
            "list-roots",
            "--query",
            "Roots[0].PolicyTypes[].[Type,Status]",
            "--output",
            "table",
        )

        rep.text("""Expected today (measured 2026-08-11): SERVICE_CONTROL_POLICY ENABLED and nothing
else. Step 7.2 enables RESOURCE_CONTROL_POLICY, TAG_POLICY and
DECLARATIVE_POLICY_EC2 - from the MANAGEMENT account, as CT Admin; the Identity
account can read this and cannot change it. After enabling, each must read ENABLED
and not PENDING_ENABLE.""")

        # ------------------------------------------------------------------------------
        rep.h1("2. Every node - id, ARN and the full PATH a policy condition needs")

        note("walking the OU tree...")

        # The root is a node like any other for attachment purposes, and it is where 7.5
        # attaches.
        res = cli.run("organizations", "list-roots", "--query", "Roots[0].Arn", "--output", "text")
        root_arn = res.text or "-"
        nodes = [Node("ROOT", "(root)", root_id, root_arn, f"{org_id}/{root_id}/", 0)]

        # Breadth-first, because the tree is two levels deep (INV-03: `Sandboxes` under
        # `Interactive`) and a one-level walk would silently miss every nested OU - the
        # same failure a one-level Terraform for_each would have.
        queue = deque([(root_id, f"{org_id}/{root_id}/", 0)])
        while queue:
            parent_id, parent_path, depth = queue.popleft()
            res = cli.run(
                "organizations",
                "list-organizational-units-for-parent",
                "--parent-id",
                parent_id,
                "--query",
                "OrganizationalUnits[].[Name,Id,Arn]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                fields = line.split("\t")
                if len(fields) < 3 or not fields[0]:
                    continue
                name, node_id, arn = fields[0], fields[1], fields[2]
                child_path = f"{parent_path}{node_id}/"
                nodes.append(Node("OU", name, node_id, arn, child_path, depth + 1))
                queue.append((node_id, child_path, depth + 1))

        rep.tabulate(
            ["KIND\tNAME\tID\tARN\tPATH (aws:PrincipalOrgPaths)\tDEPTH"]
            + [f"{n.kind}\t{n.name}\t{n.node_id}\t{n.arn}\t{n.path}\t{n.depth}" for n in nodes]
        )

        rep.text("""
THE PATH COLUMN IS WHAT 7.5 IS WRITTEN FROM. `aws:PrincipalOrgPaths` is
multi-valued, so its condition is ForAllValues:StringNotLike and never a bare
StringNotLike; the value is the full path WITH the trailing slash, exactly as
printed above. Use the `Data` row for the datazone:CreateDomain carve-out. Confirm
any path against `aws organizations list-parents`, never against a screenshot.

THE ARN COLUMN IS WHAT 7.7 IS WRITTEN FROM: `controltower enable-control` takes its
--target-identifier as an ARN, not as an id.

DEPTH 2 IS EXPECTED AND IS INV-03. A node missing here that exists in the console
means the walk was denied somewhere - check section 7 before believing the tree.""")

        # ------------------------------------------------------------------------------
        rep.h1("3. Policies attached per node, per policy type")

        note("listing attached policies per node...")

        rep.text("""One block per node. AwsManaged=True is Control Tower or AWS; False is this
project's. Nothing of this project's is expected here before Stage 1c step 7.5.""")

        for n in nodes:
            rep.h2(f"3.x {n.kind} {n.name}  ({n.node_id})")
            for ptype in POLICY_TYPES:
                rep.line(f"{ptype}:")
                res = cli.run(
                    "organizations",
                    "list-policies-for-target",
                    "--target-id",
                    n.node_id,
                    "--filter",
                    ptype,
                    "--query",
                    "Policies[].[Name,Id,AwsManaged]",
                    "--output",
                    "text",
                    tolerate="PolicyTypeNotEnabledException|policy type is not enabled",
                )
                if res.tolerated:
                    rep.line("  (policy type not enabled on the root - step 7.2 enables it)")
                elif not res.text:
                    rep.line("  (none attached)")
                else:
                    for line in res.text.splitlines():
                        rep.line("  " + line.replace("\t", " "))
                    # remember the SCP ids, so section 4 can print their documents once each
                    if ptype == "SERVICE_CONTROL_POLICY":
                        for line in res.text.splitlines():
                            fields = line.split("\t")
                            if len(fields) >= 3 and fields[1]:
                                seen_policies[fields[1]] = (fields[0], fields[2])
                rep.line()

        rep.text("""EXPECT `aws-guardrails-*` ON EVERY REGISTERED OU, and expect those to already deny
what 7.5 was going to write by hand for CloudTrail and Config. Read the documents in
section 4 and write only the gap. GuardDuty is the part Control Tower does NOT cover
here, which is why its four denies belong in awsds-org-scp-baseline.json.""")

        # ------------------------------------------------------------------------------
        rep.h1("4. The documents of the policies found - what is ALREADY denied")

        if not seen_policies:
            rep.text("""No service control policy was returned by section 3 - either none is attached
anywhere (which would contradict a Control Tower landing zone) or the listing was
denied. Check section 7 before concluding the first.""")
        else:
            note("describing each policy found...")
            for pid in sorted(seen_policies):
                pname, pmanaged = seen_policies[pid]
                rep.h2(f"4.x {pname}  ({pid}, AwsManaged={pmanaged})")
                rep.show(
                    cli,
                    "organizations",
                    "describe-policy",
                    "--policy-id",
                    pid,
                    "--query",
                    "Policy.Content",
                    "--output",
                    "text",
                )
            rep.text("""READ THESE FOR THREE THINGS: which actions are already denied (do not duplicate);
which principals are carved out (AWSControlTowerExecution,
aws-controltower-ConfigRecorderRole - the landing zone updates itself through
them); and how much of the per-node character budget they already spend.""")

        # ------------------------------------------------------------------------------
        rep.h1("5. Control Tower controls enabled per node, and whether the node is registered")

        note("listing enabled controls per node...")

        rep.text("""This is 7.0 step 3 and 7.7 registration check in one call. AN UNREGISTERED TARGET
ERRORS rather than returning an empty list - that distinction IS the check.
Registration is expected for every non-foundational OU (each received an Account
Factory vend, and Account Factory only offers registered OUs), but expected is not
measured. The organization ROOT is not a control target and is skipped.

This is a controltower: call, not an Organizations one, so the read boundary Stage
1b step 4 measured says nothing about it. If every row below failed, re-run in
CloudShell on MANAGEMENT as CT Admin:  python3 aws/org-policy-baseline.py -""")

        for n in nodes:
            if n.kind != "OU":
                continue
            rep.h2(f"5.x OU {n.name}  ({n.node_id})")
            rep.line(f"target: {n.arn}")
            rep.line()
            rep.show(
                cli,
                "controltower",
                "list-enabled-controls",
                "--target-identifier",
                n.arn,
                "--query",
                "enabledControls[].[controlIdentifier,statusSummary.status,"
                "driftStatusSummary.driftStatus]",
                "--output",
                "table",
            )

        rep.text("""DIFF `Security` AGAINST `Identity` HERE (7.6). `Identity` was created outside
Control Tower's own flow, so it carries no policy set until code attaches one; what
`Security` has extra is mostly the foundational set about the log-archive and audit
buckets, which means nothing for an account that holds neither. Record the diff.

AND CHECK `Sandboxes` AGAINST `Interactive` after 7.7 enables the first control:
whether a nested OU inherits an enabled control is verification (xi), and this is
the call that answers it.""")

        # ------------------------------------------------------------------------------
        rep.h1("6. The quota: how many policies fit on one node, and how large each may be")

        note("reading the Organizations quotas...")

        rep.text(f"""Organizations quotas answer in {QUOTA_REGION} only; that is why this one call changes region.

""")

        rep.line(
            f"$ aws service-quotas list-service-quotas --service-code organizations "
            f"--region {QUOTA_REGION}"
        )
        rep.line()
        quota_cli = AwsCli(profile=profile, region=QUOTA_REGION, errors=cli.errors)
        qres = quota_cli.call(
            "service-quotas",
            "list-service-quotas",
            "--service-code",
            "organizations",
            "--query",
            "Quotas[].[QuotaName,Value]",
            "--output",
            "text",
        )
        if not qres.ok:
            rep.line(qres.merged)
            rep.line()
            rep.line(f"!! COMMAND FAILED (exit {qres.status})")
            rep.line()
            cli.errors.entries.append(
                "aws service-quotas list-service-quotas --service-code organizations\n"
                f"    {head2(qres.merged)}"
            )
        else:
            lines = [ln for ln in qres.stdout.splitlines() if ln]
            keyword_rows = sorted(
                ln
                for ln in lines
                if any(k in ln.lower() for k in ("polic", "attach", "size", "maximum"))
            )
            rep.tabulate(["QUOTA\tVALUE"] + keyword_rows)
            rep.line()
            rep.line("(full list, unfiltered:)")
            rep.line()
            for ln in sorted(lines):
                rep.line(ln.replace("\t", "  "))

        rep.text("""
WHAT TO DO WITH THIS. Count the slots per node BEFORE writing, and remember that
7.7 consumes one more SCP slot on every OU it touches (the Region deny is
implemented as an SCP that Control Tower attaches). SCPs and RCPs do not share a
budget and the numbers differ - prefer one well-Sid-ed policy per node to several
thin ones. A policy that will not attach is discovered at the END of the evening.
If a quota is missing above, Service Quotas does not publish it: fall back to the
Organizations documentation and record which number you used and where it came from.""")

        # ------------------------------------------------------------------------------
        rep.h1("7. Calls that failed")

        if cli.errors:
            rep.text("""Each entry is a call whose output is missing above. An empty block anywhere else
in this file means the call succeeded and returned nothing.

""")
            rep.line(cli.errors.text())
            rep.text("""
If these are AccessDenied, WHICH CALLS FAILED IS THE ANSWER TO VERIFICATION (x):
  - Organizations reads denied  -> the delegated-administrator read surface does
    NOT extend to the policy calls, and 7.0 can never be a script from Identity.
  - only controltower: denied   -> expected; that call is not an Organizations one.
Either way, re-run in CloudShell on MANAGEMENT as `AWS Control Tower Admin`:
  python3 aws/org-policy-baseline.py -
and record in docs/log/log-stage-01c-preventive-policies.md which identity each answer
actually required.""")
        else:
            rep.text(f"""None. Every call in this report returned successfully - which also answers
verification (x) in the affirmative: the policy reads and list-enabled-controls
both answered as {cli.label}.""")

        rep.line()
        rep.line("Regenerate with:  ./aws/org-policy-baseline.py")

    # ---------------------------------------------------------------------------------- run
    note("")
    if cli.errors:
        note(f"wrote {out_label} (some calls FAILED - see section 7)")
        return 1
    note(f"wrote {out_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
