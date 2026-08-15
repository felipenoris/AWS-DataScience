"""The ``aws`` CLI as a subprocess, with the conventions every script here shares.

Why the CLI and not boto3, said once for the whole folder: these scripts are wrappers around
the same commands an operator would type by hand, their documentation prints the exact
command above each output block, and the SCP battery reads the *wording* of CLI errors
(a standing rule: read the denial wording, never the exit code). Shelling out keeps the
authentication path, the profile semantics and the error text identical to a hand-run
command - which is what a snapshot is for - and keeps this package dependency-free, which is
what the CloudShell fallback needs.

Two call styles, the same two the shell versions had:

    run   capture the output for later use; a failure is logged (or tolerated) and returns
          an empty ``text`` so callers can keep the shell's ``[ -n "$RUN_OUT" ]`` shape
    show  is on the Report class: echo the command into the report, then its output
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

from . import context

# The two spellings the shell scripts accepted for "no --profile: ambient credentials".
AMBIENT = ("-", "none")


def is_ambient(profile: str | None) -> bool:
    return profile is None or profile in AMBIENT


def head2(text: str) -> str:
    """First two lines, joined by spaces - the shell's ``head -n 2 | tr '\\n' ' '``.

    A space joins the lines; a third-and-beyond line collapses into a single trailing
    space, exactly as the shell pipeline behaved.
    """
    lines = text.split("\n")
    head = " ".join(lines[:2])
    if len(lines) > 2:
        head += " "
    return head


class ErrorLog:
    """One entry per failed call, printed by every report's final section."""

    def __init__(self) -> None:
        self.entries: list[str] = []

    def add(self, args: tuple, output: str, profile: str | None = None) -> None:
        prefix = f"[{profile}] " if profile is not None else ""
        self.entries.append(f"{prefix}aws {' '.join(args)}\n    {head2(output)}")

    def __bool__(self) -> bool:
        return bool(self.entries)

    def text(self) -> str:
        return "\n".join(self.entries)


@dataclass
class CallResult:
    """What one CLI call answered."""

    stdout: str
    stderr: str
    status: int
    tolerated: bool = False

    @property
    def ok(self) -> bool:
        return self.status == 0

    @property
    def merged(self) -> str:
        """stdout+stderr as one stream - what the shell's ``2>&1`` captured."""
        if self.stdout and self.stderr:
            return self.stdout + self.stderr
        return self.stdout or self.stderr

    @property
    def text(self) -> str:
        """The shell's ``RUN_OUT``: the output on success, empty after a failure."""
        return self.stdout if self.ok else ""


@dataclass
class AwsCli:
    """One profile/region binding, mirroring the shell's ``aws_()`` function.

    ``profile=None`` (or ``-``/``none``) means ambient credentials - CloudShell, or an
    assumed role already in the environment. ``stdin`` is always closed, so a call made from
    inside a loop cannot swallow the loop's input (the shell's ``</dev/null``).
    """

    profile: str | None = None
    region: str = context.REGION
    errors: ErrorLog = field(default_factory=ErrorLog)
    # Whether the report's "$ aws ..." echo lines name the profile. Multi-profile scripts
    # do; single-profile scripts leave it implicit in the header.
    echo_profile: bool = False

    def __post_init__(self) -> None:
        if is_ambient(self.profile):
            self.profile = None

    @property
    def label(self) -> str:
        """How the profile is named in headers and messages."""
        if self.profile is None:
            return "(none - ambient credentials, e.g. CloudShell)"
        return self.profile

    def argv(self, args: tuple) -> list:
        cmd = ["aws"]
        if self.profile is not None:
            cmd += ["--profile", self.profile]
        if self.region:
            cmd += ["--region", self.region]
        cmd += list(args)
        return cmd

    def echo(self, args: tuple) -> str:
        """The ``$ aws ...`` line printed above an output block."""
        if self.echo_profile and self.profile is not None:
            return f"$ aws --profile {self.profile} {' '.join(args)}"
        return f"$ aws {' '.join(args)}"

    def call(self, *args: str) -> CallResult:
        """Execute, capture, judge nothing. The building block of ``run``."""
        proc = subprocess.run(
            self.argv(args),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=context.subprocess_env(),
        )
        # $(...) in shell strips trailing newlines; matching that here keeps every
        # downstream comparison and printf-style reassembly identical.
        return CallResult(
            stdout=proc.stdout.rstrip("\n"),
            stderr=proc.stderr.rstrip("\n"),
            status=proc.returncode,
        )

    def run(self, *args: str, tolerate: str | None = None, log: bool = True) -> CallResult:
        """The shell's ``run()``: capture; log a failure unless it matches ``tolerate``.

        ``tolerate`` is a regex of error text that means "the question does not apply
        here", not "this failed" - a matched error is reported as an empty, tolerated
        success and kept out of the failed-calls section, because a section that lists
        non-problems stops being read (the mirror image of Lesson 13).
        """
        res = self.call(*args)
        if res.ok:
            return res
        if tolerate and re.search(tolerate, res.merged):
            return CallResult(stdout="", stderr="", status=0, tolerated=True)
        if log:
            self.errors.add(args, res.merged, self.profile if self.echo_profile else None)
        return res
