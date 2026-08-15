#!/usr/bin/env -S uv run --quiet
# check-iam-wildcards.py - Stage 2 step 9.2. No wildcard-account ARN in the identity plane.
#
#   run:      ./scripts/check-iam-wildcards.py            # terraform-live/identity/
#             ./scripts/check-iam-wildcards.py <path>...  # anything else, for testing the check
#   reads:    *.json and *.tf. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 an unauthorised wildcard, or a stale whitelist entry
#
# WHAT IT GUARDS, and this one is a control rather than a convention. `arn:aws:iam::*:role/X`
# means "any principal called X, in ANY account". A condition written to name one role
# therefore names a role that anybody who can create a role can mint - and the design leans on
# exactly that kind of condition twice over, in the per-function carve-outs of D26 and D27. It
# is invisible in a terraform plan and free to catch in a script.
#
# THE ONE EXCEPTION IS WHITELISTED BY Sid, AND THE WHITELIST IS PART OF THE CHECK.
# `DenyAccountBpaChangeExceptInfrastructure` in awsds-org-scp-baseline.json MUST carry a
# wildcard account: it carves the InfrastructureAccess Identity Center role out of the
# account-level BPA deny, and its whole purpose is to reach accounts that do not exist yet -
# the role's ARN suffix is minted per account (1c decision 7). Everything else fails.
#
# A CHECK RELAXED TO FIT ITS ONE EXCEPTION HAS STOPPED BEING A CHECK, so the exception is
# bound to the statement rather than to a line or a file, and it is verified in BOTH
# directions: an unauthorised wildcard fails, and a whitelist entry whose Sid is no longer in
# the document ALSO fails. A permanently-satisfied exemption for a statement somebody deleted
# is how the next wildcard gets waved through under a name nobody re-read.
#
# THE TWO FILE CLASSES ARE JUDGED DIFFERENTLY, on purpose:
#
#   - A JSON POLICY DOCUMENT is parsed and walked statement by statement, so the whitelist can
#     be a Sid at all. A JSON file that is not a policy document (the tag policy, the
#     declarative policy, attachments.json) is scanned as text, with no exception available.
#   - A .tf FILE is scanned as text and has NO exception. Nothing written in this stage needs
#     one: a permissions boundary is account-local, so it names its own account through
#     data.aws_caller_identity rather than a wildcard. If a future stage believes it needs one,
#     the argument belongs in this file - as a second named entry - and not around it.

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from tfhygiene.policydoc import is_policy_document, statement_texts
from tfhygiene.scan import collect_files

# (document basename, Sid) -> why. Both halves are checked: the pair must be FOUND, and
# nothing outside it may match.
WHITELIST = {
    (
        "awsds-org-scp-baseline.json",
        "DenyAccountBpaChangeExceptInfrastructure",
    ): "1c decision 7 - the InfrastructureAccess carve-out must reach accounts that do not "
    "exist yet; the SSO role's ARN suffix is minted per account",
}

PATTERN = re.compile(r"arn:aws:iam::\*:")


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    targets = argv or ["terraform-live/identity"]
    files = collect_files(targets, suffixes=(".json", ".tf"))

    bad = 0
    allowed_seen = set()
    scanned = set()

    print(f"== scanning {len(files)} file(s) under: {' '.join(targets)} ==")

    for path in files:
        base = path.name
        scanned.add(base)
        text = path.read_text(encoding="utf-8", errors="replace")
        if not PATTERN.search(text):
            continue

        doc = None
        if path.suffix == ".json":
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                print(f"  FAIL  {path}: does not parse as JSON ({e})")
                bad += 1
                continue
            if is_policy_document(parsed):
                doc = parsed

        if doc is not None:
            # A policy document: the whitelist can name a statement, so judge one at a time.
            for sid, stmt_json in statement_texts(doc):
                if not PATTERN.search(stmt_json):
                    continue
                key = (base, sid)
                if key in WHITELIST:
                    allowed_seen.add(key)
                    print(f"  allow {path}  Sid={sid}")
                    print(f"          {WHITELIST[key]}")
                else:
                    print(
                        f"  FAIL  {path}  Sid={sid}: wildcard-account ARN in a statement "
                        "that is not whitelisted"
                    )
                    bad += 1
            continue

        # Not a policy document, or a .tf: no exception is available here.
        for i, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line):
                print(f"  FAIL  {path}:{i}: {line.strip()}")
                bad += 1

    # The other direction. A whitelisted Sid that no longer matches is an exemption nobody can
    # retire, sitting in the check for the next wildcard to arrive under the same name.
    # Judged only when the document was actually in scope: run against some other path - which
    # is how this check is itself tested - the entry is neither satisfied nor stale, it was
    # not read.
    for key, _why in WHITELIST.items():
        if key in allowed_seen:
            continue
        if key[0] not in scanned:
            print(
                f"  note  whitelist entry {key[0]} Sid={key[1]} not judged: the document is "
                "outside the scanned path"
            )
            continue
        print(
            f"  FAIL  stale whitelist entry: {key[0]} Sid={key[1]} no longer carries a "
            "wildcard-account ARN - remove it from this script"
        )
        bad += 1

    print()
    print("OK" if not bad else f"FAILED - {bad} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
