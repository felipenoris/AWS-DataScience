#!/usr/bin/env -S uv run --quiet
# check-index.py - verify that POLICIES.md still describes the documents in policies/.
#
#   run:      ./terraform-live/identity/org-policies/check-index.py
#   reads:    policies/*.json and POLICIES.md. Touches nothing, needs no AWS session.
#   exit:     0 when every document's section lists exactly its Sids, in order; 1 otherwise.
#
# WHY THIS EXISTS AS A SCRIPT AND NOT AS A HABIT. POLICIES.md is the only place the reasoning
# behind each statement lives - the JSON carries no comments - so a statement added or
# renamed without its row leaves the next reader with a file that is confidently wrong.
# The failure is silent in both directions: a row with no statement describes a control
# that is not attached, and a statement with no row is one nobody can explain a year later.
#
# WHAT IT DOES NOT CHECK, deliberately: whether a row's *text* is still true. Nothing can.
# It checks the one property a machine can decide - that the two lists agree - which is
# what turns "review POLICIES.md at every change" from an intention into a step that fails.
#
# What plays the part of a `Sid` differs by policy TYPE, and step 7.8 put three types in
# this folder. The property being checked is the same in all three - "the index lists
# exactly what the document contains, in order" - so the extraction is what varies
# (tfhygiene.policydoc.entries), and a document whose type is not recognised STOPS the run
# rather than being skipped quietly: a checker that silently ignores a file is not a checker
# (Lesson 13).

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from tfhygiene.policydoc import UnknownPolicyShape, entries, load


def main() -> int:
    os.chdir(Path(__file__).resolve().parent)

    md = Path("POLICIES.md").read_text(encoding="utf-8")
    sections = re.split(r"\n## ", md)
    bad = 0

    for path in sorted(Path("policies").glob("*.json"), key=str):
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
