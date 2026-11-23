"""awslib.cmdline: which command lines a script takes, and what -h, --help and a refusal print."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
from awslib import cmdline

DOC = """x.py - a stand-in script.

run:      ./aws/x.py                  # every profile
          ./aws/x.py awsds-infra-prod # only the ones named
"""
USAGE = inspect.cleandoc(DOC)
PROG = Path(sys.argv[0]).name

CASES = [
    # argv, flags, valued, positional, the reason ("" when the script takes it)
    ([], (), (), True, ""),
    (["awsds-infra-prod", "awsds-infra-staging"], (), (), True, ""),
    (["-"], (), (), True, ""),
    (["2026-09-12T21:00-03:00", "2026-09-12T23:00Z"], (), (), True, ""),
    (["--on-host", "awsds-infra-prod"], ("--on-host",), (), True, ""),
    (["--profile", "awsds-infra-staging", "2026-09"], (), ("--profile",), True, ""),
    (["--profile", "-"], (), ("--profile",), True, ""),
    (["--days", "-1"], (), ("--days",), True, ""),
    (["--days", "30"], (), ("--days",), False, ""),
    (["--self-check"], ("--self-check",), (), False, ""),
    (["--bogus"], (), (), True, "unknown option --bogus"),
    (["awsds-infra-prod", "-x"], (), (), True, "unknown option -x"),
    (["--"], (), (), True, "unknown option --"),
    (["--days=30"], (), ("--days",), True, "unknown option --days=30"),
    (["--on-host"], (), (), True, "unknown option --on-host"),
    (["--profile"], (), ("--profile",), True, "--profile needs a value"),
    (["--phase", "--list"], ("--list",), ("--phase",), False, "--phase needs a value"),
    (["now"], (), (), False, "unexpected argument now"),
    (
        ["--self-check", "self-check"],
        ("--self-check",),
        (),
        False,
        "unexpected argument self-check",
    ),
]


@pytest.mark.parametrize("argv, flags, valued, positional, reason", CASES)
def test_problem(argv, flags, valued, positional, reason):
    assert cmdline.problem(argv, flags, valued, positional) == reason


@pytest.mark.parametrize(
    "argv, valued",
    [
        (["--help"], ()),
        (["-h"], ()),
        (["awsds-infra-prod", "--help"], ()),
        (["--bogus", "-h"], ()),
        (["--profile", "--help"], ("--profile",)),
    ],
)
def test_help_prints_the_usage_and_exits_0(capsys, argv, valued):
    with pytest.raises(SystemExit) as exit_:
        cmdline.check(argv, DOC, valued=valued)
    assert exit_.value.code == 0
    out, err = capsys.readouterr()
    assert out == USAGE + "\n"
    assert err == ""


@pytest.mark.parametrize(
    "argv, positional, reason",
    [
        (["--bogus"], True, "unknown option --bogus"),
        (["now"], False, "unexpected argument now"),
    ],
)
def test_refusal_prints_the_reason_and_the_usage_and_exits_2(capsys, argv, positional, reason):
    with pytest.raises(SystemExit) as exit_:
        cmdline.check(argv, DOC, positional=positional)
    assert exit_.value.code == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"{PROG}: {reason}\n\n{USAGE}\n"


def test_a_command_line_the_script_takes_returns_silently(capsys):
    assert cmdline.check(["--on-host", "awsds-infra-prod"], DOC, flags=("--on-host",)) is None
    assert capsys.readouterr() == ("", "")
