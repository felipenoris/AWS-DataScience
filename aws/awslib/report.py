"""The report file: section headers, ``column -t`` tables, echoed commands.

Every snapshot is a sectioned text file whose shape the shell versions fixed: a ``====``
banner, numbered ``h1`` sections, ``$ aws ...`` lines above the output they produced, and
tab-separated tables aligned exactly as BSD ``column -t -s $'\\t'`` aligned them. The Python
scripts keep that shape byte for byte - a diff of two runs is one of the standing
deliverables (networking's [P]-stability), so the formatting is part of the contract.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from typing import IO, Union

from .awscli import AwsCli, head2

Rows = Iterable[Union[str, Iterable[str]]]


def note(*parts: str) -> None:
    """Progress, on stderr, so it reaches the terminal and not the report."""
    print(*parts, file=sys.stderr)


def tabulate(rows: Rows) -> str:
    """Align tab-separated rows exactly as BSD ``column -t -s $'\\t'`` does.

    Measured behaviour, reproduced deliberately: empty fields are DROPPED (which is why
    every caller writes ``-`` for an empty cell), empty lines are dropped, each column is
    padded to its widest cell plus a two-space gutter, and the last cell of a row carries
    no trailing padding.
    """
    split: list[list[str]] = []
    for row in rows:
        line = row if isinstance(row, str) else "\t".join(row)
        fields = [f for f in line.split("\t") if f != ""]
        if fields:
            split.append(fields)
    widths: dict[int, int] = {}
    for fields in split:
        for i, cell in enumerate(fields):
            widths[i] = max(widths.get(i, 0), len(cell))
    out = []
    for fields in split:
        body = "".join(cell.ljust(widths[i] + 2) for i, cell in enumerate(fields[:-1]))
        out.append(body + fields[-1])
    return "\n".join(out)


class Report:
    """A report under construction, wrapping the output stream.

    The shell versions built the report by redirecting ``main`` to the output file; this
    class is that redirection made explicit. ``line``/``text`` write verbatim - the prose
    blocks of each report are kept exactly as the shell printed them.
    """

    def __init__(self, stream: IO[str]):
        self._s = stream

    # ------------------------------------------------------------------ plain text
    def line(self, text: str = "") -> None:
        self._s.write(text + "\n")

    def text(self, block: str) -> None:
        """A multi-line block, written verbatim with a final newline."""
        if not block.endswith("\n"):
            block += "\n"
        self._s.write(block)

    def raw(self, block: str) -> None:
        """Write exactly these bytes - for content whose own trailing newline (or lack of
        one) is part of the fidelity contract, e.g. a file echoed into the report."""
        self._s.write(block)

    # ------------------------------------------------------------------ structure
    def h1(self, title: str) -> None:
        self._s.write("\n\n" + "#" * 80 + "\n" + f"# {title}\n" + "#" * 80 + "\n\n")

    def h2(self, title: str) -> None:
        self._s.write(f"\n--- {title} ---\n\n")

    def banner(self, title: str) -> None:
        self._s.write("=" * 80 + "\n" + title + "\n" + "=" * 80 + "\n")

    def tabulate(self, rows: Rows, indent: str = "") -> None:
        table = tabulate(rows)
        if indent:
            table = "\n".join(indent + ln for ln in table.split("\n"))
        self._s.write(table + "\n")

    # ------------------------------------------------------------------ aws calls
    def show(self, cli: AwsCli, *args: str, lead_blank: bool = False) -> int:
        """The shell's ``show()``: echo the command, then its output or its error.

        Failures are echoed in place *and* logged for the failed-calls section, so an
        empty block is never ambiguous between "nothing there" and "denied".
        """
        if lead_blank:
            self.line()
        self.line(cli.echo(args))
        self.line()
        res = cli.call(*args)
        if not res.ok:
            self.line(res.merged)
            self.line()
            self.line(f"!! COMMAND FAILED (exit {res.status})")
            self.line()
            cli.errors.add(args, res.merged, cli.profile if cli.echo_profile else None)
            return res.status
        if res.merged:
            self.line(res.merged)
        else:
            self.line("(empty result - the call succeeded and returned nothing)")
        self.line()
        return 0

    # ------------------------------------------------------------------ checks table
    def checks_table(self, checks: Checks) -> None:
        """fail rows first, then note, then pass - the order every script prints."""
        rows = ["RESULT\tID\tWHAT\tDETAIL"]
        for kind in ("fail", "note", "pass"):
            rows += [r for r in checks.rows if r.startswith(kind + "\t")]
        self.tabulate(rows)


class Checks:
    """The pass/fail/note ledger the checking scripts accumulate."""

    def __init__(self) -> None:
        self.rows: list[str] = []

    def add(self, result: str, check_id: str, what: str, detail: str) -> None:
        self.rows.append(f"{result}\t{check_id}\t{what}\t{detail}")

    def ok(self, check_id: str, what: str, detail: str) -> None:
        self.add("pass", check_id, what, detail)

    def fail(self, check_id: str, what: str, detail: str) -> None:
        self.add("fail", check_id, what, detail)

    def note(self, check_id: str, what: str, detail: str) -> None:
        self.add("note", check_id, what, detail)

    def n_fail(self, check_id: str | None = None) -> int:
        rows = self.rows
        if check_id is not None:
            rows = [r for r in rows if r.split("\t")[1] == check_id]
        return sum(1 for r in rows if r.startswith("fail\t"))


def failed_calls_epilogue(rep: Report, errors, *extra_lines: str) -> None:
    """The standard body of a "Calls that failed" section."""
    if errors:
        rep.text(
            "Each entry is a call whose output is missing above. An empty block anywhere else\n"
            "in this file means the call succeeded and returned nothing.\n\n"
        )
        rep.line(errors.text())
        for ln in extra_lines:
            rep.line(ln)
    else:
        rep.line("None. Every call in this report returned successfully.")


__all__ = ["Report", "Checks", "note", "tabulate", "failed_calls_epilogue", "head2"]
