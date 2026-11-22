"""Builds code/app-genai.zip, the `code` of both workflows, and checks it as the worker reads it.

    python3 scripts/build_archive.py code/app-genai.zip

The archive holds the package `app_genai_tasks/` at its root, without bytecode, and
`prompts/triage.md` and `guardrail/definition.json` beside it. Every entry carries the same date, so
two builds of one tree are the same bytes. The check extracts the archive to an empty folder, as the
worker extracts it to /usr/local/airflow/dags, imports the package there in a fresh interpreter, and
reads both files through the package: a file the archive lacks fails the build, even where the
repository holds it.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "app_genai_tasks"
FILES = ("prompts/triage.md", "guardrail/definition.json")
CALLABLES = ("ensure_guardrail", "triage_messages", "check_answers", "probe_unguarded")
DATE = (1980, 1, 1, 0, 0, 0)

CHECK = """
import os
import sys

import app_genai_tasks
from app_genai_tasks import common

folder = os.path.realpath(sys.argv[1])
for name in sys.argv[2].split(","):
    if not callable(getattr(app_genai_tasks, name, None)):
        sys.exit(f"app_genai_tasks.{name} is not a callable of the archive")
if not os.path.realpath(app_genai_tasks.__file__).startswith(folder + os.sep):
    sys.exit(f"the package imported from {app_genai_tasks.__file__}, outside the archive")
for relative in sys.argv[3].split(","):
    path = os.path.realpath(common.bundled(relative))
    if not path.startswith(folder + os.sep):
        sys.exit(f"{relative} read from {path}, outside the archive")
print(f"imported on Python {sys.version.split()[0]}: {sys.argv[2]}; read beside it: {sys.argv[3]}")
"""


def entries(root: Path = ROOT) -> list[tuple[Path, str]]:
    """(source, name in the archive) for every file the archive holds, in name order."""
    found = []
    for path in sorted((root / "code" / PACKAGE).rglob("*")):
        relative = path.relative_to(root / "code")
        if path.is_file() and "__pycache__" not in relative.parts and path.suffix != ".pyc":
            found.append((path, relative.as_posix()))
    for name in FILES:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"{path}: a file the archive carries is missing")
        found.append((path, name))
    return sorted(found, key=lambda entry: entry[1])


def build(target: Path, root: Path = ROOT) -> list[str]:
    """The archive written to `target`; the names it holds."""
    names = []
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w") as archive:
        for source, name in entries(root):
            info = zipfile.ZipInfo(name, date_time=DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
            names.append(name)
    return names


def verify(target: Path) -> str:
    """The archive extracted and imported in a fresh interpreter; what that interpreter printed."""
    with tempfile.TemporaryDirectory() as folder:
        with zipfile.ZipFile(target) as archive:
            archive.extractall(folder)
        done = subprocess.run(
            [sys.executable, "-c", CHECK, folder, ",".join(CALLABLES), ",".join(FILES)],
            cwd=folder,
            env={**os.environ, "PYTHONPATH": folder, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=60,
        )
    if done.returncode != 0:
        raise RuntimeError(f"the archive does not import as the worker reads it: {done.stderr}")
    return done.stdout.strip()


def main(argv: list[str]) -> int:
    target = Path(argv[0]) if argv else ROOT / "code" / "app-genai.zip"
    names = build(target)
    for name in names:
        print(f"  {name}")
    print(f"{target}: {len(names)} file(s), {target.stat().st_size} bytes")
    print(verify(target))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
