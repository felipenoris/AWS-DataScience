#!/usr/bin/env -S uv run --quiet
# org-policies.py - what governs each node RIGHT NOW, by Sid, with inheritance resolved -
# and the handful of checks that no probe can perform.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/org-policies.py                   # awsds-infra-identity
#             python3 aws/org-policies.py -           # no --profile: CloudShell on
#                                                     # MANAGEMENT, as CT Admin (no uv
#                                                     # there; bring the aws/ folder)
#   writes:   aws/output/org-policies.txt   (untracked - see .gitignore)
#   reads:    organizations:ListRoots, ListOrganizationalUnitsForParent, ListAccountsForParent,
#             ListPoliciesForTarget, DescribePolicy,
#             sts:GetCallerIdentity. This script never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# ALL FOUR POLICY TYPES CARRY THEIR ID SINCE 2026-08-15, and the omission it fixes was not
# cosmetic. Section 1 used to list `SERVICE_CONTROL_POLICY` documents with their ids and
# reduce the RCP to a presence check, while the tag policy and the declarative policy did
# not appear at all - so THREE OF THE TEN ATTACHED DOCUMENTS had no id in any snapshot and
# existed only in docs/log/log-stage-01c-preventive-policies.md. That was survivable while they
# were console-managed and stops being survivable at Stage 2 step 5.5, where the id is the
# argument `terraform import` takes. Reading one filter is also how a read-back reports
# three attached documents as absent (Lesson 13, and 1c nearly did it).
#
# WHY THIS EXISTS, AND HOW IT DIFFERS FROM org-policy-baseline.py - which walks the same
# tree and would otherwise be a duplicate of it.
#
#   org-policy-baseline.py is a PREFLIGHT, run once before writing policy (Stage 1c step
#   7.0). It prints whole documents, the quota and the organization's metadata, and its
#   question is "what already exists that I must not duplicate".
#
#   THIS script is a CHECK, run after every policy change and at every vend. It prints no
#   document bodies at all - only `Sid` lists - and its questions are:
#
#     1. what is attached where, condensed enough to diff by eye;
#     2. what actually governs a given ACCOUNT once inheritance is resolved;
#     3. do the statements that no probe can reach still say what they must.
#
# THE THREE THINGS THAT MADE IT WORTH WRITING, each one a lesson that has already cost
# something:
#
#   - LESSON 23 - a managed service owns its artifacts' packing. Control Tower packs per
#     ENABLEMENT, not per control, and inconsistently: the two root-user controls landed in
#     the original guardrail on Policy Test, Workloads and Interactive, and in the REGION
#     document on Identity and Data. So a document cannot be identified by its id or by the
#     job it was created for, and every section here binds to `Sid`.
#
#   - LESSON 22 - a control whose principal the harness cannot produce is verified by
#     READING, not by attempting. `GRRESTRICTROOTUSER` is conditioned on an ARN no Identity
#     Center role can ever match, so the SCP battery is structurally blind to it: it was
#     enabled on Policy Test without `ExemptAssumeRoot` while the battery reported 61 of 61
#     as expected. Section 3 is that class, and it is the reason this script exits 2.
#
#   - D37 - `Sandboxes` carries nothing unless it DIFFERS from `Interactive`, so reading the
#     OU tells you nothing about what governs the accounts inside it. Section 2 resolves the
#     chain so that the answer does not depend on remembering that.
#
# IDENTITY. Every Organizations *policy* read answers from the Identity account as the
# delegated administrator - Stage 1c verification (x), measured 2026-08-13. The `-` fallback
# is CloudShell on Management as `AWS Control Tower Admin`, for the day that stops being
# true. Nothing here needs `controltower:*`, which is the one surface a member account
# cannot read.

from __future__ import annotations

import json
import os
import sys
from collections import deque

from awslib import context, policydoc
from awslib.awscli import AwsCli
from awslib.report import Checks, Report, note

OUT_NAME = "org-policies.txt"

# NODEPOL below stays SCP-only ON PURPOSE. Sections 2, 3 and 4 resolve inheritance and read
# conditions, and only an SCP composes down the tree the way those sections describe: an RCP
# bounds a resource rather than a principal, a tag policy reports instead of denying, and a
# declarative policy is not a permission boundary in either direction. Widening it would
# have made section 2's "N statements in force over this account" quietly wrong.
# NODEALL is the inventory; NODEPOL is the ceiling.
POLICY_TYPES = [
    "SERVICE_CONTROL_POLICY",
    "RESOURCE_CONTROL_POLICY",
    "TAG_POLICY",
    "DECLARATIVE_POLICY_EC2",
]

UNREADABLE = "(document unreadable - see section 5)"


def main(argv: list) -> int:
    profile = argv[0] if argv else os.environ.get("AWSDS_PROFILE", "awsds-infra-identity")
    cli = AwsCli(profile=profile, region=context.REGION)
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    checks = Checks()

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

    # ------------------------------------------------------------------- collect the tree
    note("walking the OU tree...")

    res = cli.run(
        "organizations", "list-roots", "--query", "Roots[0].[Name,Id]", "--output", "text"
    )
    fields = res.text.split("\t") if res.text else []
    root_name = fields[0] if len(fields) > 0 else ""
    root_id = fields[1] if len(fields) > 1 else ""
    if not root_id:
        note(f"could not read the organization root - see the failures section of {out_label}")
        with open(out_path, "w", encoding="utf-8") as stream:
            stream.write("FATAL: organizations list-roots returned nothing.\n")
            stream.write(cli.errors.text() + "\n" if cli.errors else "")
        return 1

    # nodes: (kind, name, id, ancestors) - ancestors include the node itself, root first.
    nodes = [("ROOT", root_name, root_id, [root_id])]

    # breadth-first, depth-agnostic: `Sandboxes` sits at depth 2 and a walk written for
    # depth 1 would miss it silently (D23, D34).
    queue = deque([(root_id, [root_id])])
    while queue:
        parent_id, parent_anc = queue.popleft()
        res = cli.run(
            "organizations",
            "list-organizational-units-for-parent",
            "--parent-id",
            parent_id,
            "--query",
            "OrganizationalUnits[].[Name,Id]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) < 2 or not f[1]:
                continue
            name, node_id = f[0], f[1]
            anc = parent_anc + [node_id]
            nodes.append(("OU", name, node_id, anc))
            queue.append((node_id, anc))

    def node_name(node_id: str) -> str:
        for _kind, name, nid, _anc in nodes:
            if nid == node_id:
                return name
        return ""

    note("listing accounts per node...")
    accounts = []  # (name, id, parent id, ancestors)
    for _kind, _name, node_id, anc in nodes:
        res = cli.run(
            "organizations",
            "list-accounts-for-parent",
            "--parent-id",
            node_id,
            "--query",
            "Accounts[].[Name,Id]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) < 2 or not f[1]:
                continue
            accounts.append((f[0], f[1], node_id, anc))

    note("listing attached policies per node, all four types...")
    node_all = []  # (node id, type, pid, pname)
    node_pol = []  # (node id, pid, pname) - SCP ONLY
    node_rcp = []  # (node id, pname)
    for _kind, _name, node_id, _anc in nodes:
        for ptype in POLICY_TYPES:
            res = cli.run(
                "organizations",
                "list-policies-for-target",
                "--target-id",
                node_id,
                "--filter",
                ptype,
                "--query",
                "Policies[].[Id,Name]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                f = line.split("\t")
                if len(f) < 2 or not f[0]:
                    continue
                pid, pname = f[0], f[1]
                node_all.append((node_id, ptype, pid, pname))
                if ptype == "SERVICE_CONTROL_POLICY":
                    node_pol.append((node_id, pid, pname))
                elif ptype == "RESOURCE_CONTROL_POLICY":
                    node_rcp.append((node_id, pname))

    # ------------------------------------------------------- fetch-once policy documents
    doc_cache: dict = {}

    def fetch_doc(pid: str) -> dict | None:
        if pid not in doc_cache:
            res = cli.run(
                "organizations",
                "describe-policy",
                "--policy-id",
                pid,
                "--query",
                "Policy.Content",
                "--output",
                "text",
            )
            if not res.text:
                doc_cache[pid] = None
            else:
                try:
                    doc_cache[pid] = json.loads(res.text)
                except json.JSONDecodeError as e:
                    cli.errors.entries.append(f"parsing policy {pid}\n    {e}")
                    doc_cache[pid] = None
        return doc_cache[pid]

    def stmt_lines(pid: str) -> list | None:
        """(sid, compact-json rest) per statement, or None when the document is unreadable."""
        doc = fetch_doc(pid)
        if doc is None:
            return None
        return policydoc.statement_lines(doc)

    def sids_of(pid: str) -> str:
        lines = stmt_lines(pid)
        if not lines:
            return UNREADABLE
        return ", ".join(sid for sid, _rest in lines)

    def nstmts_of(pid: str) -> int:
        lines = stmt_lines(pid)
        return len(lines) if lines else 0

    def entries_of(pid: str) -> str:
        # Deliberately the same extraction as check-index.py, and for the same reason: the
        # property worth printing is "what entries does this document contain", and a type
        # nobody taught the script about is named rather than skipped (Lesson 13).
        doc = fetch_doc(pid)
        if doc is None:
            return UNREADABLE
        return ", ".join(policydoc.entries(doc))

    def stmt_of(pid: str, sid: str) -> str | None:
        """The compact JSON of one named statement, or None when absent/unreadable."""
        lines = stmt_lines(pid)
        if not lines:
            return None
        for s, rest in lines:
            if s == sid:
                return rest
        return None

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("What governs each node right now - by Sid, with inheritance resolved")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {cli.label}
caller    : {caller}
produced  : aws/org-policies.py   (index: aws/INDEX.md)

SECTIONS
  1. Attached per node, all four policy types, with ids - no document bodies
  2. What governs each ACCOUNT, inheritance resolved - SCPs only, see below
  3. The read-only checks - the class no probe can reach
  4. The ceiling at a glance, per OU
  5. Calls that failed

HOW TO READ THIS FILE
  - BIND TO THE Sid, NEVER TO THE POLICY ID OR ITS NAME (Lesson 23). Control Tower
    packs per ENABLEMENT and does it inconsistently across OUs, in THREE measured
    shapes: the root-user controls sit in the original guardrail on `Policy Test`,
    `Workloads` and `Interactive`; in the REGION document on `Identity` and `Data`;
    and on `Security` the two enablements split across BOTH documents at once - a
    new one for the Region control, the pre-existing AWS guardrail for the root
    ones. "The region policy" is not a stable way to refer to anything.
  - SECTION 3 IS THE POINT OF THIS SCRIPT. Those statements are invisible to the
    SCP battery in BOTH directions, because every principal this project can obtain
    is an Identity Center role (Lesson 22). A green battery says nothing about them,
    and a FAIL here is a real defect however clean ./aws/probes/scp-battery.py ran.
  - SECTION 1 LISTS ALL FOUR TYPES; SECTION 2 RESOLVES ONLY SCPs, and that is not an
    omission. Only an SCP composes down the tree as a ceiling over a principal. An
    RCP bounds a RESOURCE, a tag policy REPORTS rather than denying (enforced_for is
    unset here), and a declarative policy sets a service attribute rather than an
    authorization boundary. Folding them into "N statements in force" would produce
    a number that is confidently wrong.
  - AN OU ROW SAYING "nothing attached" IS NOT AN UNGOVERNED OU. `Sandboxes` carries
    nothing by decision (D37) and is fully governed by inheritance - section 2 is
    where that question is actually answered, per account.
  - This is a point-in-time snapshot, not a source of truth. Regenerate rather than
    trusting a stale copy; expectations live in docs/AWS_STATE.md, intent in docs/plan/.""")

        # ==============================================================================
        rep.h1("1. Attached per node, all four policy types, with ids")

        rep.text("""FullAWSAccess and RCPFullAWSAccess are omitted here - they allow everything and
their presence is checked in section 4 instead. What is left is the ceiling.

THE ID IN BRACKETS IS THE ONLY PLACE OUTSIDE THE 1c LOG THAT CARRIES IT, and it is
what Stage 2 step 5.5 passes to `terraform import`. Bind your READING to the entry
names (Lesson 23); use the id as an argument, never as a name for the document.
The entry column means something different per type, on purpose: `Sid`s for an SCP
or an RCP, tag KEYS for a tag policy, ATTRIBUTE names for a declarative policy.""")

        for kind, name, node_id, _anc in nodes:
            rep.h2(f"{kind} {name}  ({node_id})")
            found = False
            for ptype in POLICY_TYPES:
                type_found = False
                for nid, ntype, pid, pname in node_all:
                    if nid != node_id or ntype != ptype:
                        continue
                    if pname in ("FullAWSAccess", "RCPFullAWSAccess"):
                        continue
                    if not type_found:
                        rep.line(f"  [{ptype}]")
                        type_found = True
                    found = True
                    rep.line(f"    {pname}  ({pid})")
                    rep.line(f"        {entries_of(pid)}")
            if not found:
                rep.line("  (nothing attached beyond FullAWSAccess / RCPFullAWSAccess)")

        # ==============================================================================
        rep.h1("2. What governs each ACCOUNT, inheritance resolved")

        rep.text("""SCPs are inherited down the tree and denies compose, so the ceiling over an account
is the union of every statement on every ancestor. This section is the answer to
"what applies here", and it is the reason a nested OU carrying nothing (D37) costs
nothing: read the account, not the folder.""")

        for aname, aid, _parent, anc in accounts:
            rep.h2(f"ACCOUNT {aname}  ({aid})")
            chain = " -> ".join(node_name(nid) for nid in anc)
            rep.line(f"  inherits from: {chain}")
            rep.line()
            total = 0
            for nid in anc:
                nname = node_name(nid)
                for pnid, pid, pname in node_pol:
                    if pnid != nid or pname == "FullAWSAccess":
                        continue
                    total += nstmts_of(pid)
                    rep.line(f"  from {nname:<14} {pname}")
                    rep.line(f"  {'':<19}   {sids_of(pid)}")
            rep.line()
            rep.line(f"  {total} statements in force over this account.")

        # ==============================================================================
        rep.h1("3. The read-only checks - the class no probe can reach")

        rep.text("""Each of these is a statement whose condition selects a principal this project cannot
produce, so attempting the call proves nothing and reading the document is the only
instrument (Lesson 22). See docs/plan/runbooks/scp-battery.md, "the class the battery
cannot reach", for the same table written as a procedure.

""")

        # --- CHK-1 / CHK-2: the two root-user controls -----------------------------------
        seen_rootctl = False
        for nid, pid, pname in node_pol:
            nname = node_name(nid)
            line = stmt_of(pid, "GRRESTRICTROOTUSER")
            if line is not None:
                seen_rootctl = True
                if "aws:AssumedRoot" in line:
                    checks.ok(
                        "CHK-1",
                        f"ExemptAssumeRoot on {nname}",
                        f"{pname} ({pid}) - aws:AssumedRoot present",
                    )
                else:
                    checks.fail(
                        "CHK-1",
                        f"ExemptAssumeRoot on {nname}",
                        f"{pname} ({pid}) - NO aws:AssumedRoot: sts:AssumeRoot is "
                        f"denied into every account under {nname}, which is 1a "
                        "step 6's only member-account recovery. Disable and "
                        "re-enable the control WITH the parameter; it has no false "
                        "value.",
                    )

            line = stmt_of(pid, "GRRESTRICTROOTUSERACCESSKEYS")
            if line is not None:
                if "aws:AssumedRoot" in line:
                    checks.fail(
                        "CHK-2",
                        f"no access-key exemption on {nname}",
                        f"{pname} ({pid}) - aws:AssumedRoot present, and it must "
                        "not be: a root access key minted inside a privileged "
                        "session is a standing, unscoped, SCP-immune credential "
                        "(D16).",
                    )
                else:
                    checks.ok(
                        "CHK-2",
                        f"no access-key exemption on {nname}",
                        f"{pname} ({pid}) - correctly unexempted",
                    )
        if not seen_rootctl:
            checks.note("CHK-1", "root-user controls", "not enabled on any OU - nothing to check")

        # --- CHK-3: D27's service guard ---------------------------------------------------
        seen_d27 = False
        for nid, pid, pname in node_pol:
            nname = node_name(nid)
            line = stmt_of(pid, "DenyCatalogMaintenanceRunsExceptMaintenanceRole")
            if line is None:
                continue
            seen_d27 = True
            if "aws:PrincipalIsAWSService" in line:
                checks.ok(
                    "CHK-3",
                    f"D27 service guard on {nname}",
                    f"{pname} ({pid}) - aws:PrincipalIsAWSService present",
                )
            else:
                checks.fail(
                    "CHK-3",
                    f"D27 service guard on {nname}",
                    f"{pname} ({pid}) - the carve-out has no "
                    "aws:PrincipalIsAWSService guard, so a service principal "
                    "inherits the exemption.",
                )
        if not seen_d27:
            checks.note(
                "CHK-3",
                "D27 service guard",
                "the Data OU document is not attached anywhere - nothing to check",
            )

        # --- CHK-4: D37, Sandboxes carries nothing ----------------------------------------
        sb_id = next((nid for _k, name, nid, _a in nodes if name == "Sandboxes"), "")
        if sb_id:
            extra = ", ".join(
                pname for nid, _pid, pname in node_pol if nid == sb_id and pname != "FullAWSAccess"
            )
            if not extra:
                checks.ok(
                    "CHK-4",
                    "D37 - Sandboxes carries nothing",
                    "only FullAWSAccess, governed by Interactive through inheritance",
                )
            else:
                checks.fail(
                    "CHK-4",
                    "D37 - Sandboxes carries nothing",
                    f"attached: {extra}. Either this is a deliberate divergence "
                    "from Interactive - in which case write it down in D37 and in "
                    "the stage log - or it is drift.",
                )
        else:
            checks.note("CHK-4", "D37 - Sandboxes", "no OU named Sandboxes in the tree")

        # --- CHK-5: RCPFullAWSAccess everywhere (INV-11) ----------------------------------
        for _kind, name, node_id, _anc in nodes:
            if any(nid == node_id and pname == "RCPFullAWSAccess" for nid, pname in node_rcp):
                checks.ok("CHK-5", f"RCPFullAWSAccess on {name}", "present")
            else:
                checks.fail(
                    "CHK-5",
                    f"RCPFullAWSAccess on {name}",
                    "MISSING - an RCP set with no allow is a closed door, so this "
                    "denies everything at this node.",
                )

        rep.checks_table(checks)

        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        if n_fail > 0:
            rep.text("""A failure here is a real defect no matter how clean the battery ran - these
statements are the ones it cannot see.""")

        # ==============================================================================
        rep.h1("4. The ceiling at a glance, per OU")

        rows = ["OU\tGUARDRAIL\tREGION CEILING\tROOT CONTROLS\tPROJECT SCP"]
        for kind, name, node_id, _anc in nodes:
            if kind != "OU":
                continue
            g = r = u = p = "-"
            for nid, pid, pname in node_pol:
                if nid != node_id:
                    continue
                if pname.startswith("aws-guardrails-"):
                    g = "yes"
                if pname.startswith("awsds-org-scp-"):
                    p = "yes"
                if stmt_of(pid, "CTMULTISERVICEPV1") is not None:
                    r = "yes"
                if stmt_of(pid, "GRRESTRICTROOTUSER") is not None:
                    u = "yes"
            rows.append(f"{name}\t{g}\t{r}\t{u}\t{p}")
        rep.tabulate(rows)

        rep.text("""
READ THE GAPS, NOT THE YESES. Exactly ONE is expected, and it is not drift:
  - `Sandboxes` is blank across the row by decision (D37) and its accounts are
    governed by `Interactive` - section 2 shows that resolved.
Every other OU carries a guardrail, a Region ceiling and the root controls. `Security`
joined them on 2026-08-14 (Stage 1d step 12, decision 10), which closed open question
16 - so a `Security` row reading `-` under REGION CEILING or ROOT CONTROLS is now a
REGRESSION, not the inherited gap it used to be.
Anything else missing from this table is drift. docs/AWS_STATE.md INV-11 and INV-12 hold
the expected shape, and are what this table should be diffed against.

AND THE TABLE CANNOT BE REGRESSION-TESTED FOR TWO OF THE NINE ACCOUNTS. `Log Archive`
and `Audit` hold no CLI profile by design, so ./aws/probes/scp-battery.py has no reach
into them and never will. Whatever the `Security` row says here is the ONLY standing
instrument over those two accounts; the probes behind it were run by hand, once, in
CloudShell (Stage 1d step 12.2).""")

        # ==============================================================================
        rep.h1("5. Calls that failed")

        if cli.errors:
            rep.line(cli.errors.text())
            rep.text("""
If these are AccessDenied, retry from CloudShell on Management as
`AWS Control Tower Admin`:  python3 aws/org-policies.py -""")
        else:
            rep.line("None. Every call returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/org-policies.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if cli.errors:
        note(f"wrote {out_label} (some calls FAILED - see section 5)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 3)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
