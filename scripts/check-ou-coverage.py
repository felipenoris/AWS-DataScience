#!/usr/bin/env -S uv run --quiet
# check-ou-coverage.py - Stage 2 step 9.3. Every OU is accounted for, and the authored map
# still describes what is attached.
#
#   needs:    a live SSO session - the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./scripts/check-ou-coverage.py          # awsds-infra-identity
#             ./scripts/check-ou-coverage.py -        # no --profile: CloudShell on Management
#   reads:    organizations:ListRoots, ListOrganizationalUnitsForParent, ListPoliciesForTarget,
#             sts:GetCallerIdentity - and terraform-live/identity/org-policies/. It never
#             creates, updates, attaches or detaches anything.
#   exit:     0 clean | 1 a check FAILED | 2 could not run (no session, or a call failed)
#
# WHY THIS CHECK CARRIES MORE THAN ITS SIZE. Accounts and OUs are vended from the console, by
# decision and permanently (D34), so nothing in Terraform declares them and they cannot drift.
# The risk runs the other way and it is silent: a new OU with no document attached, and
# `terraform plan` reporting "No changes" because a state file tracks only what a configuration
# declares. Step 5.3 moved the per-OU coverage guarantee out of the apply and into here, so
# this script is where that risk is actually paid for.
#
# THE TWO-LIST SHAPE IS THE POINT. attachments.json lists the OUs that carry a document AND the
# OUs that deliberately carry none, with the reason. A check that treated "absent" and
# "deliberately absent" alike would either fail forever or pass on a real gap - the same answer
# on success and on failure, which is not a check (Lesson 13). `Sandboxes` is the entry that
# has to be named: it is the only OU whose emptiness a future reader will try to fix (D37).
#
# THREE THINGS IT DOES NOT LOOK AT, so a green run is not read as more than it is:
#
#   - CONTROL TOWER'S OWN DOCUMENTS. Every governed OU carries aws-guardrails-* documents that
#     this project neither wrote nor may edit. A document counts as ours only when a file of
#     that name exists in policies/, which is a stronger binding than a name prefix and the
#     reason the map may hold names at all (Lesson 23 warns against naming a document whose
#     PACKING somebody else owns - these are the ones we own).
#   - ACCOUNT-LEVEL ATTACHMENTS. This design has none: the census is the root plus four OUs,
#     and the delegation's account/* entry is an unexercised over-grant (step 5.0). The full
#     per-node census is ./aws/org-policies.py section 1, which is the instrument for that.
#   - WHETHER A DOCUMENT'S CONTENT IS RIGHT. That is POLICIES.md and check-index.py.

from __future__ import annotations

import json
import os
import shutil
import sys
from collections import deque
from pathlib import Path

# This is the one script under scripts/ that talks to AWS, so it runs on the same plumbing
# as the aws/ snapshots (awslib) plus the authored-map loader (tfhygiene). Both come from
# the uv environment - this check always runs from a clone, never from CloudShell alone.
from awslib.awscli import AwsCli
from awslib.profiles import wrong_identity
from tfhygiene import attachments

MAP = "terraform-live/identity/org-policies/attachments.json"
POLICY_DIR = "terraform-live/identity/org-policies/policies"
TYPES = [
    "SERVICE_CONTROL_POLICY",
    "RESOURCE_CONTROL_POLICY",
    "TAG_POLICY",
    "DECLARATIVE_POLICY_EC2",
]


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    profile = argv[0] if argv else "awsds-infra-identity"
    # This script inherits the caller's region resolution, exactly as the shell version
    # passed no --region: Organizations is global and the profile's own region applies.
    cli = AwsCli(profile=profile, region="")

    fail = 0

    def say(text: str = "") -> None:
        print(text)

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    if shutil.which("aws") is None:
        say("aws is not on PATH")
        return 2
    if not Path(MAP).is_file():
        say(f"no authored map at {MAP}")
        return 2
    try:
        amap = attachments.load(Path(MAP))
    except (json.JSONDecodeError, OSError):
        say(f"{MAP} does not parse")
        return 2

    # The session is checked before anything else and its failure is exit 2, never exit 0. A
    # coverage check reporting "clean" because it could not reach AWS is the worst output this
    # script could produce (CLAUDE.md: check the caller identity before running aws commands).
    res = cli.call("sts", "get-caller-identity", "--query", "Arn", "--output", "text")
    if not res.ok:
        suffix = f" for profile {profile}" if cli.profile else ""
        say(f"no usable session{suffix}:")
        say(f"  {res.merged}")
        say("  sign in as the INFRASTRUCTURE USER, Identity account, InfrastructureAccess:")
        if wrong_identity(res.merged):
            # Naming the right identity is not enough when a token for the WRONG one is
            # already cached under this sso-session: the login below finds it valid and
            # returns success without asking the browser anything (measured 2026-08-20).
            say("      aws sso logout && aws sso login --sso-session awsds")
            say("  a token IS cached - for a user without this role. the logout is the fix.")
        else:
            say("      aws sso login --sso-session awsds")
        return 2
    who = res.stdout
    say("== identity ==")
    say(f"  {who}" + (f"  (profile {profile})" if cli.profile else ""))

    # ---------------------------------------------------------------- the organization's OUs
    res = cli.call("organizations", "list-roots", "--output", "json")
    if not res.ok:
        say(f"list-roots failed: {res.merged}")
        return 2
    root_id = (json.loads(res.stdout).get("Roots") or [{}])[0].get("Id")
    if not root_id:
        say("could not read the organization root")
        return 2

    # Breadth-first over the whole tree, not one level. The nesting is two deep today
    # (Sandboxes under Interactive, D23) and a single ListOrganizationalUnitsForParent over
    # the root's children would enumerate neither the nested OU nor anything below it - the
    # same silent under-reach step 5.3 refuses in a for_each.
    ous = []  # (id, name), every depth, in discovery order
    queue = deque([root_id])
    while queue:
        parent = queue.popleft()
        res = cli.call(
            "organizations",
            "list-organizational-units-for-parent",
            "--parent-id",
            parent,
            "--output",
            "json",
        )
        if not res.ok:
            say(f"list-organizational-units-for-parent {parent} failed: {res.merged}")
            return 2
        for ou in json.loads(res.stdout).get("OrganizationalUnits", []):
            ous.append((ou["Id"], ou["Name"]))
            queue.append(ou["Id"])
    ou_names = [name for _id, name in ous]
    say(f"  root {root_id}, {len(ous)} OU(s) at every depth")

    with_doc = sorted(amap.ou.keys())
    without_doc = sorted(amap.ou_with_no_document.keys())

    # ---------------------------------------------------------------- 1. every OU accounted for
    say()
    say("== 1. every OU appears in the authored map, or in its deliberately-empty list ==")
    for ou_id, name in ous:
        if name in amap.ou:
            say(f"  {name} -> {', '.join(amap.ou[name])}")
        elif name in amap.ou_with_no_document:
            say(f"  {name} -> no document, on purpose: {amap.ou_with_no_document[name][:58]}...")
        else:
            bad(f"OU '{name}' ({ou_id}) is in neither list of {MAP}")
            say(
                "          attach a document and add it to .ou, or record in "
                ".ou_with_no_document why it carries none"
            )

    # The other direction: a map entry for an OU that no longer exists is a for_each key that
    # fails an apply, and a reason nobody can act on.
    say()
    say("== 2. every OU the map names still exists ==")
    n_missing = 0
    for name in with_doc + without_doc:
        if name not in ou_names:
            bad(f"the map names OU '{name}', which the organization does not have")
            n_missing = 1
    if n_missing == 0:
        say("  none missing")

    # ---------------------------------------------------------------- 3. the documents exist
    say()
    say("== 3. every document the map names is a file in policies/ ==")
    n_absent = 0
    for doc in amap.documents():
        if not Path(POLICY_DIR, f"{doc}.json").is_file():
            bad(f"map names '{doc}', but {POLICY_DIR}/{doc}.json does not exist")
            n_absent = 1
    if n_absent == 0:
        say("  all present")

    # ---------------------------------------------------------------- 4. authored == attached
    say()
    say("== 4. what is attached matches what the map authors ==")
    say(
        "  (this project's documents only - a policy counts as ours when "
        "policies/<name>.json exists)"
    )

    def attached_ours(target_id: str):
        """Our documents attached to a target, sorted - or None when a listing failed."""
        names = []
        for ptype in TYPES:
            res = cli.call(
                "organizations",
                "list-policies-for-target",
                "--target-id",
                target_id,
                "--filter",
                ptype,
                "--output",
                "json",
            )
            if not res.ok:
                return None
            names += [p["Name"] for p in json.loads(res.stdout).get("Policies", [])]
        return sorted(n for n in names if Path(POLICY_DIR, f"{n}.json").is_file())

    def compare(label: str, target_id: str, authored: list) -> None:
        actual = attached_ours(target_id)
        if actual is None:
            bad(f"{label}: list-policies-for-target failed")
            return
        authored = sorted(a for a in authored if a)
        if authored == actual:
            say(f"  {label}: {len(actual)} document(s), as authored")
            return
        bad(f"{label}: the map and the organization disagree")
        for name in authored:
            if name not in actual:
                say(f"          authored, NOT attached: {name}")
        for name in actual:
            if name not in authored:
                say(f"          attached, NOT authored: {name}")

    compare(f"root ({root_id})", root_id, amap.root)
    for ou_id, name in ous:
        compare(f"OU {name}", ou_id, amap.ou.get(name, []))

    say()
    say("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
