#!/usr/bin/env -S uv run --quiet
"""Packages a uv project as the code input of a SageMaker processing job in the house image.

    ./examples/sandbox-orchestration/operators/package-uv-job.py <project dir> <output dir>
    ./examples/sandbox-orchestration/operators/package-uv-job.py --constraints

The job runs /opt/awsds/venv/bin/python, CPython 3.13 on linux x86_64, with no network, so every
dependency is either in the house environment already or travels in the code input. The input is a
folder, not an archive: a ProcessingInput downloads an S3 prefix, and an extension module cannot be
imported from a zip. PYTHONPATH puts that folder ahead of the house environment's site-packages, so a
package present in both would shadow the image's copy - the failure images/dev-env/python/pyproject.toml
documents for numpy. The output therefore holds the project and only the packages the house
environment lacks, and a package both hold at different versions stops the build.

A disagreement is fixed in the project: the build prints a [tool.uv] constraint-dependencies block
pinning every package the project shares with the image to the image's version, and `uv lock` then
resolves within them. --constraints prints every house version in requirements form, for
`uv pip compile -c` or `uv add -c`. The house environment is read from this repository's
images/dev-env/python/uv.lock, which must be the lock of the image version the job names. The
procedure: docs/plan/runbooks/serverless-workflows.md section J.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOUSE_ENV = Path(__file__).resolve().parents[3] / "images" / "dev-env" / "python"
TARGET = ["--python-version", "3.13", "--python-platform", "x86_64-manylinux2014"]
PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)")


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def uv(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(["uv", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"uv {' '.join(args[:2])} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def pins(text: str) -> dict:
    """`name==version` lines of a requirements text, by normalised name."""
    found = {}
    for line in text.splitlines():
        m = PIN.match(line)
        if m:
            found[norm(m.group(1))] = m.group(2)
    return found


def blocks(text: str) -> dict:
    """Each requirement of an exported file with its hash lines, by normalised name."""
    found, name = {}, None
    for line in text.splitlines():
        m = PIN.match(line)
        if m:
            name = norm(m.group(1))
            found[name] = [line]
        elif name and line.startswith((" ", "\t")):
            found[name].append(line)
    return found


def house_pins() -> dict:
    out = uv(
        "export", "--frozen", "--no-dev", "--no-emit-project", "--no-hashes", "--no-header",
        "--quiet", cwd=HOUSE_ENV,
    )  # fmt: skip
    return pins(out)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="package-uv-job.py", description=__doc__.split("\n")[0])
    parser.add_argument(
        "project", nargs="?", type=Path, help="a uv project: pyproject.toml + uv.lock"
    )
    parser.add_argument("output", nargs="?", type=Path, help="a folder that does not exist yet")
    parser.add_argument("--constraints", action="store_true", help="print the house versions")
    args = parser.parse_args(argv)

    house = house_pins()
    if args.constraints:
        sys.stdout.write("".join(f"{n}=={v}\n" for n, v in sorted(house.items())))
        return 0
    if args.project is None or args.output is None:
        parser.error("name a project and an output folder, or pass --constraints")
    project = args.project.resolve()
    if not (project / "uv.lock").is_file():
        sys.exit(f"no uv.lock in {project} - run uv lock there first")
    if args.output.exists():
        sys.exit(f"{args.output} exists - name a folder that does not, so nothing is overwritten")

    # The locked closure with its hashes, then the part of it that applies to the job's platform.
    exported = uv(
        "export", "--locked", "--no-dev", "--no-emit-project", "--no-header", "--quiet", cwd=project
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "locked.txt").write_text(exported)
        closure = pins(
            uv("pip", "compile", str(tmp / "locked.txt"), "--no-deps", "--no-header",
               "--no-annotate", "--quiet", *TARGET)
        )  # fmt: skip

        provided = {n: v for n, v in closure.items() if house.get(n) == v}
        conflicts = {n: (v, house[n]) for n, v in closure.items() if n in house and house[n] != v}
        vendored = {n: v for n, v in closure.items() if n not in house}
        if conflicts:
            print("the project's lock and the house environment disagree:", file=sys.stderr)
            for n, (mine, theirs) in sorted(conflicts.items()):
                print(f"  {n}: {mine} in the lock, {theirs} in the image", file=sys.stderr)
            shared = sorted(set(provided) | set(conflicts))
            print(
                "\nadd this to the project's pyproject.toml and run uv lock; a lower bound in the\n"
                "project above an image version fails that lock, and then the image is what changes:\n"
                "\n[tool.uv]\nconstraint-dependencies = [\n"
                + "".join(f'  "{n}=={house[n]}",\n' for n in shared)
                + "]",
                file=sys.stderr,
            )
            return 1

        stage = tmp / "stage"
        if vendored:
            by_name = blocks(exported)
            (tmp / "vendored.txt").write_text(
                "\n".join("\n".join(by_name[n]) for n in sorted(vendored)) + "\n"
            )
            uv("pip", "install", "--quiet", "--target", str(stage), "--no-deps",
               "--only-binary", ":all:", *TARGET, "-r", str(tmp / "vendored.txt"))  # fmt: skip
        uv("build", str(project), "--wheel", "--out-dir", str(tmp / "dist"), "--quiet")
        wheels = sorted((tmp / "dist").glob("*.whl"))
        uv("pip", "install", "--quiet", "--target", str(stage), "--no-deps", *TARGET,
           *map(str, wheels))  # fmt: skip

        # uv's lock file for --target, console scripts and bytecode are not code the job imports.
        for leftover in (stage / ".lock", stage / "bin"):
            if leftover.is_dir():
                shutil.rmtree(leftover)
            elif leftover.exists():
                leftover.unlink()
        for cache in list(stage.rglob("__pycache__")):
            shutil.rmtree(cache, ignore_errors=True)
        shutil.copytree(stage, args.output)

    size = sum(p.stat().st_size for p in args.output.rglob("*") if p.is_file())
    print(f"{args.output}: {size} bytes")
    print(f"from the image ({len(provided)}): {', '.join(sorted(provided)) or '-'}")
    print(
        f"vendored ({len(vendored)}): {', '.join(f'{n}=={v}' for n, v in sorted(vendored.items())) or '-'}"
    )
    print("top level:", ", ".join(sorted(p.name for p in args.output.iterdir())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
