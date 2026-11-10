#!/usr/bin/env -S uv run --quiet
# check-aws-supplement.py - docs/AWS_SUPPLEMENT.md's ids and its two indexes still hold.
#
#   run:      ./scripts/check-aws-supplement.py
#   reads:    docs/AWS_SUPPLEMENT.md, CLAUDE.md and every tracked text file that cites a SUP-nnn id.
#             No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one finding
#
# The supplement records what AWS and its tooling do that their documentation does not state, one
# SUP-nnn entry per behaviour. What is mechanical about it is checked here:
#
#   1. An id is an entry's address in other files: each is unique, each entry opens with one and a
#      bold title, and inside a section the ids ascend, which is what "a new entry takes the next
#      free number and goes at the end of its section" leaves behind.
#   2. A SUP-nnn cited anywhere in the tracked tree names an entry that exists.
#   3. The supplement's own table and CLAUDE.md's routing row both name every section and no other:
#      the row is the index a session holds before it opens the file.
#
# Blind spots, so nobody reads more into a green run (Lesson 13):
#
#   - Whether an entry is true, dated or still current is a reading. A behaviour that was measured
#     and never written here fails nothing.
#   - A number that was used once and removed leaves no trace this script can see: "never reused"
#     is held by git history.

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from repohygiene.identifiers import tracked_files

SUPPLEMENT = "docs/AWS_SUPPLEMENT.md"
MEMORY = "CLAUDE.md"

# The front matter's own headings: everything else at level 2 is a section of entries.
FRONT_MATTER = ("Rules for an entry", "Searching this file", "Sections")

ENTRY_RE = re.compile(r"^- `SUP-(\d{3})` ")
TITLED_ENTRY_RE = re.compile(r"^- `SUP-\d{3}` \*\*\S")
ANY_ENTRY_RE = re.compile(r"^- ")
ID_RE = re.compile(r"\bSUP-(\d{3})\b")
TABLE_LINK_RE = re.compile(r"^\| \[([^\]]+)\]\(#([^)]+)\) \|")
# The routing row of CLAUDE.md lists the sections after this word, separated by semicolons.
ROW_SECTIONS_RE = re.compile(r"Sections: (.+?)\s*\|\s*$")

# Suffixes whose text may cite an entry. Anything else in the tree is not prose or code of ours.
TEXT_SUFFIXES = {".md", ".tf", ".tftpl", ".py", ".sh", ".yml", ".yaml", ".hcl", ".json", ""}


def anchor(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    return re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    fail = 0

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    lines = Path(SUPPLEMENT).read_text(encoding="utf-8").splitlines()

    print(f"== {SUPPLEMENT}: entries and their ids ==")
    sections: list[str] = []
    table: list[tuple[str, str]] = []
    seen: dict[str, int] = {}
    where = ""
    last_in_block = 0
    for n, line in enumerate(lines, 1):
        if line.startswith("## ") or line.startswith("### "):
            where = line.lstrip("# ").strip()
            last_in_block = 0
            if line.startswith("## ") and where not in FRONT_MATTER:
                sections.append(where)
            continue
        if m := TABLE_LINK_RE.match(line):
            table.append((m.group(1), m.group(2)))
            continue
        in_entries = bool(sections) and where not in FRONT_MATTER
        if not (in_entries and ANY_ENTRY_RE.match(line)):
            continue
        m = ENTRY_RE.match(line)
        if not m:
            bad(f"line {n}: an entry opens with `SUP-nnn`: {line[:60]}")
            continue
        if not TITLED_ENTRY_RE.match(line):
            bad(f"line {n}: SUP-{m.group(1)} has no bold title after its id")
        num = int(m.group(1))
        if m.group(1) in seen:
            bad(f"line {n}: SUP-{m.group(1)} already names the entry at line {seen[m.group(1)]}")
        seen[m.group(1)] = n
        if num < last_in_block:
            bad(
                f"line {n}: SUP-{m.group(1)} sits after SUP-{last_in_block:03d} under "
                f'"{where}": a new entry goes at the end of its section'
            )
        last_in_block = max(last_in_block, num)
    if not seen:
        bad("no entry found")
        print("FAILED")
        return 1
    print(f"  {len(seen)} entries in {len(sections)} sections, the highest id SUP-{max(seen)}")

    print("== the supplement's own table of sections ==")
    for heading in sections:
        if (heading, anchor(heading)) not in table:
            bad(
                f'"{heading}" is not in the table under "Sections", or its link is not #{anchor(heading)}'
            )
    for heading, _ in table:
        if heading not in sections:
            bad(f'the table lists "{heading}", which is not a section')
    if len(set(sections)) != len(sections):
        bad("two sections share a heading")

    print(f"== {MEMORY}: the routing row indexes the same sections ==")
    row = next(
        (
            ln
            for ln in Path(MEMORY).read_text(encoding="utf-8").splitlines()
            if SUPPLEMENT in ln and "Sections: " in ln
        ),
        None,
    )
    if row is None:
        bad(f"{MEMORY} has no row that names {SUPPLEMENT} and lists its `Sections:`")
    else:
        m = ROW_SECTIONS_RE.search(row)
        indexed = [s.strip() for s in m.group(1).rstrip(".").split(";")] if m else []
        for heading in sections:
            if heading not in indexed:
                bad(f'{MEMORY} does not index the section "{heading}"')
        for heading in indexed:
            if heading not in sections:
                bad(f'{MEMORY} indexes "{heading}", which is not a section of the supplement')

    print("== SUP-nnn cited across the tracked tree ==")
    cited = 0
    for path in tracked_files(root):
        rel = path.relative_to(root).as_posix()
        if path.suffix not in TEXT_SUFFIXES or rel == SUPPLEMENT or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ln_no, line in enumerate(text.splitlines(), 1):
            for m in ID_RE.finditer(line):
                cited += 1
                if m.group(1) not in seen:
                    bad(f"{rel}:{ln_no}: SUP-{m.group(1)} names no entry")
    for n, line in enumerate(lines, 1):
        for m in ID_RE.finditer(line):
            if m.group(1) not in seen:
                bad(f"{SUPPLEMENT}:{n}: SUP-{m.group(1)} names no entry")
    print(f"  {cited} citations outside the supplement")

    print("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main())
