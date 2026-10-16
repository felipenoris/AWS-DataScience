#!/usr/bin/env -S uv run --quiet
# check-gitlab-pins.py - the runners' gitlab-runner release keeps the GitLab server's major.minor.
#
#   run:      ./scripts/check-gitlab-pins.py                                # the two slices
#             ./scripts/check-gitlab-pins.py <server .tf> <runners .tf>     # any pair, for testing
#   reads:    two variables.tf files. No AWS session, no side effect, nothing written.
#   exit:     0 the major.minor agree | 1 they differ | 2 a pin the reader cannot find or parse
#
# production/tooling/ installs gitlab-ce at var.gitlab_ce_version (Stage 7 decision 10) and
# production/runners/ installs gitlab-runner at var.gitlab_runner_version (Stage 8 decision 24).
# GitLab keeps a runner's major.minor with the server's, so an upgrade on the host moves both
# defaults in the same sitting (runbook gitlab.md §P). The two defaults sit in two slices and
# nothing else reads them together: this check fails when their major.minor differ.
#
# Blind spots, so nobody reads more into a green run (Lesson 13):
#
#   - It compares two files, never a host. The release the GitLab host runs is read by
#     ./aws/supplychain.py SC-13 through the newest backup's name; a runner's by its boot log.
#   - A value given by -var or a tfvars file at apply time is not read: the defaults are the pins.

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from tfhygiene import hcl

# (the file, the variable, the package it installs), the server first.
SERVER = ("terraform-live/production/tooling/variables.tf", "gitlab_ce_version", "gitlab-ce")
RUNNERS = (
    "terraform-live/production/runners/variables.tf",
    "gitlab_runner_version",
    "gitlab-runner",
)
# The shape both variables' validations accept.
RELEASE_RE = re.compile(r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.[0-9]+")


class Unread(Exception):
    """A pin the reader cannot find or parse; the message names the file and the reason."""


def pin(path: Path, variable: str) -> tuple[str, int]:
    """The literal default of ``variable`` in ``path``, and its line."""
    try:
        body = hcl.parse(path.read_text(encoding="utf-8-sig"))
    except OSError as e:
        raise Unread(f"{path}: {e.strerror}") from e
    except hcl.HclError as e:
        raise Unread(f"{path}: {e}") from e
    blocks = [
        b
        for b in body
        if isinstance(b, hcl.Block) and b.type == "variable" and b.labels == [variable]
    ]
    if not blocks:
        raise Unread(f'{path}: no variable "{variable}"')
    default = blocks[0].argument("default")
    if default is None:
        raise Unread(f'{path}:{blocks[0].line}: variable "{variable}" has no default')
    parts = default.string_parts()
    if parts is None or any(kind != hcl.LITERAL for kind, _ in parts):
        source = " ".join(default.source.split())
        raise Unread(f"{path}:{default.line}: {variable}'s default is not a literal: {source}")
    value = "".join(text for _, text in parts)
    if not RELEASE_RE.fullmatch(value):
        raise Unread(f'{path}:{default.line}: {variable} = "{value}" is not a release like 19.4.2')
    return value, default.line


def main(argv: list) -> int:
    if argv and len(argv) != 2:
        print("usage: check-gitlab-pins.py [<server variables.tf> <runners variables.tf>]")
        return 2
    paths = [Path(a).resolve() for a in argv]
    os.chdir(Path(__file__).resolve().parents[1])
    if not paths:
        paths = [Path(SERVER[0]), Path(RUNNERS[0])]

    print("== the GitLab release pins: the server's and the runners' ==")
    releases, unread = [], []
    for (_, variable, package), path in zip((SERVER, RUNNERS), paths):
        try:
            value, line = pin(path, variable)
        except Unread as e:
            unread.append(str(e))
            print(f"  UNREAD         {e}")
            continue
        releases.append(value)
        print(f'  {package:<13}  {path}:{line}  {variable} = "{value}"')

    print()
    if unread:
        print(f"UNREAD - {len(unread)} pin(s) the reader cannot find or parse, nothing compared")
        return 2
    server, runners = (RELEASE_RE.fullmatch(v) for v in releases)
    server_line = f"{server['major']}.{server['minor']}"
    runners_line = f"{runners['major']}.{runners['minor']}"
    if server_line != runners_line:
        print(f"  the server installs {server_line} and the runners {runners_line}")
        print("  move gitlab_runner_version to the newest release of the server's major.minor")
        print("  in the same sitting (docs/plan/runbooks/gitlab.md, section K)")
        print("FAILED")
        return 1
    print(f"  both on {server_line}")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
