"""Markdown scanning primitives for the plan's reference checks."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

# A relative markdown link target: `](path.md` up to the closing paren, no fragment, no whitespace.
_MD_LINK = re.compile(r"\]\(([^)#\s]+\.md)")

# Stable-ID references. D-numbers are 1-2 digits; INT rows are always two.
_D_REF = re.compile(r"\bD([0-9]{1,2})\b")
_INT_REF = re.compile(r"\bINT-[0-9]{2}\b")

# Spans that mention notation rather than using it: backticked code and double-quoted strings are
# stripped before the stale-reference scan.
_CODE_SPAN = re.compile(r"`[^`]*`")
_QUOTED_SPAN = re.compile(r'"[^"]*"')


# Directories holding markdown this repository did not author: git's own store, Terraform's module
# cache (which vendors git-sourced modules along with the `docs/` snapshot of whatever commit they
# were fetched at), the Claude session worktrees (each a full copy of the repository), the uv
# environment and any vendored node package. All of them are ignored by `.gitignore` or by git
# itself, and a broken link inside one belongs to a copy nobody here edits.
#
# Pruned as *directories* rather than by substring, so a path that merely contains one of these
# names is not excluded by accident - the rule `tfhygiene/scan.py` already applies to `.tf`.
# Measured 2026-09-18, before this prune existed: 753 of the 755 reported failures came from
# `.terraform/modules/` and `.claude/worktrees/`, which is enough noise to make the target unread.
_PRUNED_DIRS = frozenset({".git", ".claude", ".terraform", ".venv", "node_modules"})


def iter_md_files(root: Path) -> Iterator[Path]:
    """Every ``*.md`` under ``root`` this repository authored, sorted for stable output."""
    return iter(sorted(p for p in root.rglob("*.md") if _PRUNED_DIRS.isdisjoint(p.parts)))


def relative_links(path: Path) -> Iterator[tuple[Path, str]]:
    """Every relative ``.md`` link in ``path`` as ``(source, target)`` pairs."""
    text = path.read_text(encoding="utf-8", errors="replace")
    for m in _MD_LINK.finditer(text):
        yield path, m.group(1)


def d_references(text: str) -> set:
    """The distinct ``D<n>`` tokens in ``text`` (as strings, e.g. ``\"D26\"``)."""
    return {f"D{m.group(1)}" for m in _D_REF.finditer(text)}


def int_references(text: str) -> set:
    """The distinct ``INT-nn`` tokens in ``text``."""
    return set(_INT_REF.findall(text))


def strip_mention_spans(line: str) -> str:
    """Remove backticked and double-quoted spans: mentions, not uses, of old notation."""
    return _QUOTED_SPAN.sub("", _CODE_SPAN.sub("", line))


def grep(paths, pattern: str, flags: int = 0) -> Iterator[tuple[Path, int, str]]:
    """``(path, line-number, line)`` for every line of ``paths`` matching ``pattern``."""
    rx = re.compile(pattern, flags)
    for path in paths:
        for n, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if rx.search(line):
                yield path, n, line
