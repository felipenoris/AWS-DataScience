"""File collection and comment-aware line scanning for the Terraform convention checks."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

# A full-line comment. These files carry their reasoning in prose, and a check that forbade naming
# us-west-2 in an explanation would buy vagueness and no safety, so full-line comments are skipped.
# An inline trailing comment on a code line is still read: prose about the region beside code goes
# on its own line.
_FULL_LINE_COMMENT = re.compile(r"^\s*(#|//)")


def collect_files(targets: list[str], suffixes: tuple[str, ...] = (".tf",)) -> list[Path]:
    """Every matching file under ``targets``, sorted, with ``.terraform/`` pruned.

    Pruned as a *directory*, not filtered by substring, so a vendored module whose path
    merely contains the string is not excluded by accident. A target that is itself a file
    is taken as-is, which is how the checks are pointed at fixtures to test themselves.
    """
    files: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_file():
            files.append(p)
            continue
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if ".terraform" in f.parts:
                continue
            if f.is_file() and f.suffix in suffixes:
                files.append(f)
    # Sorted as strings, matching the shell's `find | sort`: Path objects compare by parts,
    # which orders `a-b` and `a/b` differently from the byte order every caller printed.
    return sorted(files, key=str)


def scan_code_lines(files: list[Path], pattern: str) -> Iterator[tuple[Path, int, str]]:
    """``(file, line-number, line)`` for every non-comment line matching ``pattern``.

    Line numbers restart per file. A pattern that does not compile raises here, before
    anything is scanned: a scanner that fails quietly reports the same "none" on a clean tree
    and on a broken regex (Lesson 13).
    """
    rx = re.compile(pattern)
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            if _FULL_LINE_COMMENT.match(line):
                continue
            if rx.search(line):
                yield path, n, line
