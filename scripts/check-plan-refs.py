#!/usr/bin/env -S uv run --quiet
# Verify the plan's stable identifiers and relative links still resolve.
# Run from anywhere:  ./scripts/check-plan-refs.py
#
#   reads:    *.md across the repository. No AWS session, no side effect.
#   exit:     0 clean | 1 at least one broken reference
#
# KNOWN RED (see the Makefile): three stage files record dated measurements phrased as
# "all six accounts with a profile", and the account-count scan cannot tell a historical
# measurement from a count that goes stale - which is why this runs as its own
# `make check-docs` target rather than inside the commit gate.

from __future__ import annotations

import os
import re
import sys
from glob import glob
from pathlib import Path

from repohygiene.markdown import (
    d_references,
    int_references,
    iter_md_files,
    relative_links,
    strip_mention_spans,
)

# Every prose file the plan owns. The root docs were outside this net until 2026-08-08,
# which is exactly where the stale references had survived.
PROSE_FIXED = [
    "docs/GENERAL_PLAN.md",
    "CLAUDE.md",
    "README.md",
    "docs/ORGANIZATION.md",
    "docs/GLOSSARY.md",
    "docs/PRICING.md",
    "docs/AWS_STATE.md",
    "docs/NETWORK.md",
    "aws/INDEX.md",
]

STALE_SECTION_RE = re.compile(r"§4\.4|\brows? \d+")
GENERAL_PLAN_PTR_RE = r"`?GENERAL_PLAN\.md`?\s+(§|D[0-9]|Stage |row |item )"
ACCOUNT_COUNT_RE = re.compile(
    r"\b(ten|nine|eight|seven|six|five|four|three)"
    r"\s+(accounts|governed accounts|member accounts|state buckets)\b"
    r"|\b(1[0-9]|[3-9])\s+(accounts|governed accounts)\b",
    re.IGNORECASE,
)
ACCOUNT_COUNT_EXCLUDE_RE = re.compile(r"quota|limit|Service Quotas", re.IGNORECASE)

# Bytes, per core file. The budget is what forces the CLAUDE.md / GENERAL_PLAN.md split: a core
# file that may grow without limit stops being a routing map and becomes the narrative it is
# supposed to point at. RAISED 20000 -> 40000 on 2026-08-19, deliberately and by the user: at
# Stage 5 the tree had outgrown the original ceiling, and the two ways to meet it were both worse
# than the overrun - move the routing table or the lesson keys out of CLAUDE.md, which is the one
# copy of each, or delete state nothing else records. The trigger to re-read this number is the
# same as before: a core file whose growth is narrative rather than state.
SIZE_BUDGET = 40000


def main() -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    fail = 0

    def say(text: str = "") -> None:
        print(text)

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    md_files = list(iter_md_files(Path(".")))
    all_md_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in md_files)

    say("== broken relative links ==")
    n = 0
    for src, tgt in (pair for p in md_files for pair in relative_links(p)):
        if (src.parent / tgt).exists():
            n += 1
        else:
            bad(f"./{src} -> {tgt}")
    say(f"  {n} links resolve")

    say("== D-references with no decision file ==")
    for d in sorted(d_references(all_md_text)):
        num = int(d[1:])
        if not 1 <= num <= 99:
            continue
        if not glob(f"docs/plan/decisions/D{num:02d}-*.md"):
            bad(f"{d} referenced, but no docs/plan/decisions/D{num:02d}-*.md")

    say("== INT-references with no row in docs/plan/integrations.md ==")
    integrations = Path("docs/plan/integrations.md").read_text(encoding="utf-8")
    for i in sorted(int_references(all_md_text)):
        if f"**{i}**" not in integrations:
            bad(f"{i} referenced, no row in docs/plan/integrations.md")

    prose = [Path(f) for f in PROSE_FIXED]
    prose += sorted(Path("docs/plan").rglob("*.md"), key=str)

    say("== stale section/row references (use a stable ID instead) ==")
    # Backticked and double-quoted spans are stripped first: those are mentions of the
    # old notation (in history, in the glossary), not uses of it.
    hits = []
    for path in prose:
        for ln_no, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if STALE_SECTION_RE.search(strip_mention_spans(line)):
                hits.append(f"{path}:{ln_no}: {line}")
    if hits:
        print("\n".join(hits))
        bad("replace the hits above with INT-nn")
    else:
        say("  none")

    say("== pointers into docs/GENERAL_PLAN.md for content that moved into docs/plan/ ==")
    # docs/GENERAL_PLAN.md is the core: principles, the account map, the two indexes. A
    # decision, a stage body or a numbered section is NOT in it, so a reference of that
    # shape is stale.
    rx = re.compile(GENERAL_PLAN_PTR_RE)
    hits = []
    for path in prose:
        for ln_no, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if rx.search(line):
                hits.append(f"{path}:{ln_no}:{line}")
    if hits:
        print("\n".join(hits))
        bad("point at docs/plan/decisions/, docs/plan/stages/ or the docs/plan/ file that holds it")
    else:
        say("  none")

    say("== hard-coded account counts (they go stale when an account is added) ==")
    # A *quota* is a measured external fact and keeps its number; a count of *our* accounts
    # is derived from the account map and goes stale the day the map changes. Only the
    # second is flagged.
    hits = []
    for path in prose:
        for ln_no, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if ACCOUNT_COUNT_RE.search(line) and not ACCOUNT_COUNT_EXCLUDE_RE.search(line):
                hits.append(f"{path}:{ln_no}:{line}")
    if hits:
        print("\n".join(hits))
        bad("write 'the accounts' / 'every governed account' instead")
    else:
        say("  none")

    say("== size budget (the whole point of the split) ==")
    for f in ("CLAUDE.md", "docs/GENERAL_PLAN.md"):
        b = Path(f).stat().st_size
        say(f"  {f}: {b} bytes")
        if b >= SIZE_BUDGET:
            bad(f"{f} over {SIZE_BUDGET // 1000} KB - move narrative into docs/plan/")

    say("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main())
