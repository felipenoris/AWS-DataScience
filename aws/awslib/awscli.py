"""The ``aws`` CLI as a subprocess, with the conventions every script here shares.

The CLI rather than boto3: these scripts wrap the same commands an operator would type by
hand, their documentation prints the exact command above each output block, and the SCP
battery reads the *wording* of CLI errors (a standing rule: read the denial wording, never the
exit code). Shelling out keeps the authentication path, the profile semantics and the error
text identical to a hand-run command, and keeps this package dependency-free, which the
CloudShell fallback needs.

The call styles:

    run    capture the output for later use; a failure is logged (or tolerated) and returns
           an empty ``text``, so a caller can test the result for emptiness
    pages  every page of a listing the CLI does not paginate itself, and whether the reading
           reached the last one
    show   is on the Report class: echo the command into the report, then its output;
           ``show_pages`` does the same for a listing ``pages`` reads
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field

from . import context

# The two spellings for "no --profile: ambient credentials".
AMBIENT = ("-", "none")

# The most pages ``pages`` reads before it reports the listing incomplete. Lake Formation's
# ListPermissions answers empty pages that still carry a NextToken: 6 pages for 29 grants in Sandbox
# and 5 for 28 in Data Governance, the last four of each empty (measured 2026-10-21).
MAX_PAGES = 50


def is_ambient(profile: str | None) -> bool:
    return profile is None or profile in AMBIENT


def head2(text: str) -> str:
    """First two lines joined by a space; anything past them collapses to a trailing space."""
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
        """stdout and stderr as one stream."""
        if self.stdout and self.stderr:
            return self.stdout + self.stderr
        return self.stdout or self.stderr

    @property
    def text(self) -> str:
        """The output on success, empty after a failure."""
        return self.stdout if self.ok else ""


@dataclass
class Listing:
    """Every page one listing answered, and how the reading ended.

    ``complete`` is true only when the last page carried no token. Otherwise ``last`` says
    why: tolerated, failed, or ``ok`` at the page limit. An absence in an incomplete listing
    proves nothing; a presence does.
    """

    pages: list
    last: CallResult
    complete: bool
    token: str = "NextToken"

    def items(self, key: str) -> list:
        """The entries under ``key``, from every page read."""
        return [item for page in self.pages for item in page.get(key) or []]

    @property
    def why(self) -> str:
        """Why the reading stopped short, in the failed-calls log's words; empty when complete."""
        if self.complete:
            return ""
        if self.last.tolerated:
            return "tolerated"
        if not self.last.ok:
            return self.last.merged
        return (
            f"{self.token} still present after {len(self.pages)} pages: the listing is incomplete"
        )

    def merged(self) -> dict:
        """The pages as one answer: each list member joined in page order, any other member
        from the first page that carries it, the token dropped."""
        doc: dict = {}
        for page in self.pages:
            for key, value in page.items():
                if key == self.token:
                    continue
                if isinstance(value, list):
                    joined = doc.get(key)
                    doc[key] = (joined if isinstance(joined, list) else []) + value
                elif key not in doc:
                    doc[key] = value
        return doc


@dataclass
class AwsCli:
    """One profile/region binding.

    ``profile=None`` (or ``-``/``none``) means ambient credentials - CloudShell, or an
    assumed role already in the environment. ``stdin`` is always closed, so a call made from
    inside a loop cannot swallow the loop's input.
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
        # Trailing newlines are stripped, so every downstream comparison and printf-style
        # reassembly works on the exact text.
        return CallResult(
            stdout=proc.stdout.rstrip("\n"),
            stderr=proc.stderr.rstrip("\n"),
            status=proc.returncode,
        )

    def run(self, *args: str, tolerate: str | None = None, log: bool = True) -> CallResult:
        """The shell's ``run()``: capture; log a failure unless it matches ``tolerate``.

        ``tolerate`` is a regex of error text meaning "the question does not apply here"
        rather than "this failed": a matched error becomes an empty, tolerated success and
        stays out of the failed-calls section.
        """
        res = self.call(*args)
        if res.ok:
            return res
        if tolerate and re.search(tolerate, res.merged):
            return CallResult(stdout="", stderr="", status=0, tolerated=True)
        if log:
            self.errors.add(args, res.merged, self.profile if self.echo_profile else None)
        return res

    def pages(
        self,
        *args: str,
        token: str = "NextToken",
        max_pages: int = MAX_PAGES,
        tolerate: str | None = None,
        log: bool = True,
    ) -> Listing:
        """``run`` for a listing the CLI does not paginate, following its token.

        The CLI pages an operation itself only when botocore defines a paginator for it; for
        any other, one call answers the first page and a token. ``token`` is the member that
        carries it in the answer and in the request (``nextToken`` for OpenSearch Serverless);
        the request option is its kebab-case spelling, ``--next-token`` for both. ``args``
        carry no ``--output`` and no ``--query``: the pages are read as JSON, and a query would
        drop the token. A failure, or a token still present after ``max_pages``, is logged
        under ``args`` without the token unless ``log`` is false.
        """
        option = "--" + re.sub(r"(?<!^)(?=[A-Z])", "-", token).lower()
        pages: list = []
        value = None
        while True:
            res = self.run(
                *args,
                *((option, value) if value else ()),
                "--output",
                "json",
                tolerate=tolerate,
                log=False,
            )
            if res.tolerated:
                return Listing(pages, res, complete=False, token=token)
            if not res.ok:
                if log:
                    self.errors.add(args, res.merged, self.profile if self.echo_profile else None)
                return Listing(pages, res, complete=False, token=token)
            page = json.loads(res.stdout or "{}")
            pages.append(page)
            value = page.get(token)
            if not value:
                return Listing(pages, res, complete=True, token=token)
            if len(pages) >= max_pages:
                listing = Listing(pages, res, complete=False, token=token)
                if log:
                    self.errors.add(args, listing.why, self.profile if self.echo_profile else None)
                return listing
