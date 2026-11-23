"""The command line every script in ``aws/`` and ``aws/probes/`` shares.

Each script parses its own arguments and reads a token it does not look for as a profile name, or
ignores it, so an option it does not know would run the whole script. ``check`` runs first in the
script's entry point, before the output directory is located, a profile is read or a subprocess
starts:

    -h or --help anywhere             the usage on stdout, exit 0
    a command line it does not take   the reason and the usage on stderr, exit 2

The usage is the script's module docstring. Nothing runs in either case: no ``aws`` call, no login,
no file under ``aws/output/``. Python 3.9 and the standard library only, for the CloudShell fallback.
"""

from __future__ import annotations

import inspect
import sys
from collections.abc import Iterable
from pathlib import Path

HELP = ("-h", "--help")


def problem(
    argv: Iterable[str],
    flags: Iterable[str] = (),
    valued: Iterable[str] = (),
    positional: bool = True,
) -> str:
    """Why the script does not take ``argv``; empty when it does.

    ``flags`` are the options taken alone and ``valued`` the ones followed by a value. A value is
    the next token, ``-`` and a negative number included; a missing one, or one that starts with
    ``--``, is refused. A lone ``-`` is a positional argument, the CloudShell fallback's "no
    profile". With ``positional`` false the script takes no positional argument at all.
    """
    args = list(argv)
    alone, with_value = set(flags), set(valued)
    i = 0
    while i < len(args):
        arg = args[i]
        i += 1
        if arg in with_value:
            if i == len(args) or args[i].startswith("--"):
                return f"{arg} needs a value"
            i += 1
        elif arg in alone:
            continue
        elif arg.startswith("-") and arg != "-":
            return f"unknown option {arg}"
        elif not positional:
            return f"unexpected argument {arg}"
    return ""


def check(
    argv: Iterable[str],
    doc: str | None,
    flags: Iterable[str] = (),
    valued: Iterable[str] = (),
    positional: bool = True,
) -> None:
    """Exit before the script acts when ``argv`` asks for help or is not one it takes.

    ``-h`` or ``--help`` anywhere wins, even as the value of an option. Returns when ``argv``
    passes; the script then parses it as before.
    """
    args = list(argv)
    usage = inspect.cleandoc(doc or "")
    if any(arg in HELP for arg in args):
        print(usage)
        sys.exit(0)
    why = problem(args, flags, valued, positional)
    if why:
        print(f"{Path(sys.argv[0]).name}: {why}\n\n{usage}", file=sys.stderr)
        sys.exit(2)
