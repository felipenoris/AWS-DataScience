#!/usr/bin/env -S uv run --quiet
# check-index.py - POLICIES.md still describes the documents in policies/.
#
#   run:      ./scripts/check-index.py
#   reads:    terraform-live/identity/org-policies/{policies/*.json,POLICIES.md}.
#             Touches nothing, needs no AWS session.
#   exit:     0 when every document's section lists exactly its Sids, in order; 1 otherwise.
#
# POLICIES.md is the only place the reasoning behind each statement lives (the JSON carries no
# comments), and the failure is silent both ways: a row with no statement describes a control that is
# not attached, and a statement with no row is one nobody can explain later. This checks the one
# property a machine can decide, that the two lists agree; whether a row's text is still true is the
# reading.
#
# What plays the part of a `Sid` differs by policy type. The extraction is
# tfhygiene.policydoc.entries, and a document whose type is not recognised stops the run rather than
# being skipped (Lesson 13).

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from tfhygiene.policydoc import UnknownPolicyShape, entries, load

# Paths are named from the repository root, like every other script under scripts/.
FOLDER = Path("terraform-live/identity/org-policies")


def main() -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    md = (FOLDER / "POLICIES.md").read_text(encoding="utf-8")
    sections = re.split(r"\n## ", md)
    bad = 0

    for path in sorted((FOLDER / "policies").glob("*.json"), key=str):
        name = path.name
        try:
            sids = entries(load(path), name)
        except UnknownPolicyShape as e:
            sys.exit(str(e))
        section = [s for s in sections if s.startswith("`" + name + "`")]
        if not section:
            print(f"DIFF {name}: no section in POLICIES.md")
            bad += 1
            continue
        rows = [r for r in re.findall(r"^\| `(\w+)` \|", section[0], re.M) if r != "Sid"]
        if rows == sids:
            print(f"OK   {name}  ({len(sids)} statements)")
            continue
        bad += 1
        print(f"DIFF {name}")
        print(f"       json: {sids}")
        print(f"       md  : {rows}")
        for s in sids:
            if s not in rows:
                print(f"       -> in the policy, missing from POLICIES.md: {s}")
        for r in rows:
            if r not in sids:
                print(f"       -> in POLICIES.md, missing from the policy: {r}")

    print()
    print("clean" if not bad else f"REVIEW NEEDED - {bad} document(s) out of sync")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
