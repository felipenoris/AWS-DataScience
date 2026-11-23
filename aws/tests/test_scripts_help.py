"""Every program in aws/ and aws/probes/ answers -h, --help and an unknown option before it acts.

Each runs in a subprocess under an empty AWS configuration, with a sitecustomize that records and
refuses every subprocess, name lookup and outbound connection: a script that reached the aws CLI, dig
or the network fails here, and so does one that wrote under aws/output/ or ran past RUN_LIMIT seconds.
The usage it must print is its module docstring, read without importing the script.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

AWS = Path(__file__).resolve().parents[1]
OUTPUT = AWS / "output"
RUN_LIMIT = 5.0  # seconds; an answer before any call takes a fraction of one

TRIPWIRE = """\
import os
import socket
import subprocess


def _trip(what):
    with open(os.environ["AWSDS_TRIPWIRE"], "a") as log:
        log.write(what + "\\n")
    raise RuntimeError("tripwire: " + what)


def _popen(self, args, *rest, **kwargs):
    _trip("subprocess %r" % (args,))


def _getaddrinfo(host, port, *rest, **kwargs):
    _trip("getaddrinfo %r" % ((host, port),))


def _connect(self, address):
    _trip("connect %r" % (address,))


subprocess.Popen.__init__ = _popen
socket.getaddrinfo = _getaddrinfo
socket.socket.connect = _connect
socket.socket.connect_ex = _connect
"""


def programs() -> list:
    """Every file in aws/ and aws/probes/ that runs as a program: a shebang or a __main__ block."""
    found = []
    for path in sorted([*AWS.glob("*.py"), *(AWS / "probes").glob("*.py")]):
        text = path.read_text(encoding="utf-8")
        if text.startswith("#!") or 'if __name__ == "__main__":' in text:
            found.append(path)
    return found


PROGRAMS = programs()
IDS = [p.relative_to(AWS).as_posix() for p in PROGRAMS]


def usage_of(script: Path) -> str:
    """The module docstring as cmdline prints it: cleaned, as inspect.cleandoc cleans it."""
    return ast.get_docstring(ast.parse(script.read_text(encoding="utf-8"))) or ""


def output_state() -> tuple:
    """Whether aws/output/ exists, and every path under it with its size and modification time."""
    if not OUTPUT.exists():
        return (False, [])
    paths = sorted(OUTPUT.rglob("*"))
    return (True, [(str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in paths])


@pytest.fixture
def sandbox(tmp_path):
    """The child environment, and the log the tripwire writes when a child trips it."""
    site = tmp_path / "site"
    site.mkdir()
    (site / "sitecustomize.py").write_text(TRIPWIRE, encoding="utf-8")
    log = tmp_path / "tripwire.log"
    env = dict(os.environ)
    env.update(
        {
            "AWS_CONFIG_FILE": "/dev/null",
            "AWS_SHARED_CREDENTIALS_FILE": "/dev/null",
            "AWS_PROFILE": "",
            "AWS_DEFAULT_PROFILE": "",
            "AWSDS_TRIPWIRE": str(log),
            "PYTHONPATH": str(site),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env, log


def run(env: dict, *argv: str) -> tuple:
    """(the completed process, its run time in seconds), from the repository root."""
    start = time.monotonic()
    res = subprocess.run(
        [sys.executable, *argv],
        cwd=AWS.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return res, time.monotonic() - start


def test_the_walk_finds_every_program():
    names = set(IDS)
    assert {"login.py", "list-identities.py", "catalog.py", "vpn.py"} <= names
    assert {"probes/scp-battery.py", "probes/readback.py"} <= names
    assert "probes/probes.py" not in names, "the battery's data is imported, never run"


@pytest.mark.parametrize(
    "code, entry",
    [
        ("import subprocess; subprocess.run(['true'])", "subprocess ['true']"),
        ("import socket; socket.getaddrinfo('localhost', 9)", "getaddrinfo ('localhost', 9)"),
        ("import socket; socket.socket().connect(('127.0.0.1', 9))", "connect ('127.0.0.1', 9)"),
        # devenv.py's path, with no proxy so the lookup is the URL's own on every laptop.
        (
            "import urllib.request as u;"
            " u.build_opener(u.ProxyHandler({})).open('http://127.0.0.1:9/', timeout=1)",
            "getaddrinfo ('127.0.0.1', 9)",
        ),
    ],
)
def test_the_tripwire_records_and_refuses(sandbox, code, entry):
    env, log = sandbox
    res, _ = run(env, "-c", code)
    assert res.returncode != 0
    assert log.read_text(encoding="utf-8").splitlines() == [entry]


@pytest.mark.parametrize("script", PROGRAMS, ids=IDS)
@pytest.mark.parametrize("flag", ["--help", "-h", "--no-such-option"])
def test_answers_before_it_acts(sandbox, script, flag):
    env, log = sandbox
    usage = usage_of(script)
    assert usage, f"{script.name} has no module docstring to print"
    before = output_state()
    res, took = run(env, str(script), flag)
    if flag in ("--help", "-h"):
        assert (res.returncode, res.stdout, res.stderr) == (0, usage + "\n", "")
    else:
        expected = f"{script.name}: unknown option {flag}\n\n{usage}\n"
        assert (res.returncode, res.stdout, res.stderr) == (2, "", expected)
    assert not log.exists(), log.read_text(encoding="utf-8")
    assert output_state() == before, "the run wrote under aws/output/"
    assert took < RUN_LIMIT
