#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging>=24"]
# ///
"""Packages a uv project as the code input of a SageMaker processing job in the house image.

    ./examples/sandbox-orchestration/operators/package-uv-job.py <project dir> <output dir>
    ./examples/sandbox-orchestration/operators/package-uv-job.py --python 3.14 <project dir> <output dir>
    ./examples/sandbox-orchestration/operators/package-uv-job.py --constraints

The job runs the house environment's interpreter, /opt/awsds/venv/bin/python, with no network, so
every dependency is either in the house environment already or travels in the code input. The input
is a folder, not an archive: a ProcessingInput downloads an S3 prefix, and an extension module cannot
be imported from a zip. PYTHONPATH puts that folder ahead of the house environment's site-packages,
so a package present in both would shadow the image's copy - the failure
images/dev-env/python/pyproject.toml documents for numpy. The output therefore holds the project and
only the packages the house environment lacks, and a package both hold at different versions stops
the build.

The target is the image's: --python defaults to the ARG PYTHON_VERSION of images/dev-env/Dockerfile
and --platform to x86_64-manylinux_2_28, and the house versions are evaluated for that target, since
the house lock can resolve a package differently per Python version. The markers are evaluated here,
not by a resolver: the image holds torch from PyTorch's own index and packages with no wheel for every
Python, which a resolver would refuse. The image's glibc is at least
2.28: the house environment holds onnxruntime 1.30.0, which publishes no wheel older than
manylinux_2_28 (measured 2026-10-11), so manylinux2014 cannot describe it. The house environment is read
from this repository's images/dev-env/python/uv.lock, which must be the lock of the image version the
job names.

A disagreement is fixed in the project: the build prints a [tool.uv] constraint-dependencies block
pinning every package the project shares with the image to the image's version, and `uv lock` then
resolves within them. --constraints prints every house version in requirements form, for
`uv pip compile -c` or `uv add -c`. The procedure: docs/plan/runbooks/serverless-workflows.md
section J.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from packaging.markers import Marker

IMAGE = Path(__file__).resolve().parents[3] / "images" / "dev-env"
HOUSE_ENV = IMAGE / "python"
DEFAULT_PLATFORM = "x86_64-manylinux_2_28"
PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)(?:\s*;\s*([^\\]+?))?\s*\\?$")


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def uv(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(["uv", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"uv {' '.join(args[:2])} failed:\n{proc.stderr.strip()}")
    return proc.stdout


def pins(text: str, env: dict) -> dict:
    """`name==version` lines of an exported file whose marker holds for env, by normalised name."""
    found = {}
    for line in text.splitlines():
        m = PIN.match(line)
        if m and (not m.group(3) or Marker(m.group(3)).evaluate(env)):
            found[norm(m.group(1))] = m.group(2)
    return found


def environment(python: str, platform: str) -> dict:
    """The marker environment of CPython <python> on <platform>, e.g. x86_64-manylinux_2_28."""
    full = python if python.count(".") >= 2 else f"{python}.0"
    return {
        "implementation_name": "cpython",
        "implementation_version": full,
        "os_name": "posix",
        "platform_machine": platform.split("-")[0],
        "platform_python_implementation": "CPython",
        "platform_release": "",
        "platform_system": "Linux",
        "platform_version": "",
        "python_full_version": full,
        "python_version": ".".join(full.split(".")[:2]),
        "sys_platform": "linux",
    }


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


def image_python() -> str:
    """The interpreter version the house image installs, from its Dockerfile."""
    m = re.search(r"^ARG PYTHON_VERSION=(\S+)", (IMAGE / "Dockerfile").read_text(), re.MULTILINE)
    if not m:
        sys.exit(f"no ARG PYTHON_VERSION in {IMAGE / 'Dockerfile'}")
    return m.group(1)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="package-uv-job.py", description=__doc__.split("\n")[0])
    parser.add_argument(
        "project", nargs="?", type=Path, help="a uv project: pyproject.toml + uv.lock"
    )
    parser.add_argument("output", nargs="?", type=Path, help="a folder that does not exist yet")
    parser.add_argument("--python", help="the job's interpreter version (default: the image's)")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM, help="uv's --python-platform")
    parser.add_argument("--constraints", action="store_true", help="print the house versions")
    args = parser.parse_args(argv)

    image = image_python()
    python = args.python or image
    if python != image:
        print(
            f"note: {python} is not the image's {image} (images/dev-env/Dockerfile)",
            file=sys.stderr,
        )
    target = ["--python-version", python, "--python-platform", args.platform]
    env = environment(python, args.platform)

    house_export = uv(
        "export", "--frozen", "--no-dev", "--no-emit-project", "--no-hashes", "--no-header",
        "--quiet", cwd=HOUSE_ENV,
    )  # fmt: skip
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        house = pins(house_export, env)
        if args.constraints:
            sys.stdout.write("".join(f"{n}=={v}\n" for n, v in sorted(house.items())))
            return 0
        if args.project is None or args.output is None:
            parser.error("name a project and an output folder, or pass --constraints")
        project = args.project.resolve()
        if not (project / "uv.lock").is_file():
            sys.exit(f"no uv.lock in {project} - run uv lock there first")
        if args.output.exists():
            sys.exit(
                f"{args.output} exists - name a folder that does not, so nothing is overwritten"
            )

        # The locked closure with its hashes, then the part of it that applies to the target.
        exported = uv(
            "export", "--locked", "--no-dev", "--no-emit-project", "--no-header", "--quiet",
            cwd=project,
        )  # fmt: skip
        closure = pins(exported, env)

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
               "--only-binary", ":all:", *target, "-r", str(tmp / "vendored.txt"))  # fmt: skip

        # The project's own wheel must be pure Python: one built here for its extension modules
        # would be built for this machine, not for the job.
        uv("build", str(project), "--wheel", "--out-dir", str(tmp / "dist"), "--quiet")
        wheels = sorted((tmp / "dist").glob("*.whl"))
        impure = [w.name for w in wheels if not w.name.endswith("-none-any.whl")]
        if impure:
            sys.exit(
                f"{', '.join(impure)}: not pure Python, so it cannot be built here for the job"
            )
        uv("pip", "install", "--quiet", "--target", str(stage), "--no-deps", *target,
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
    listed = ", ".join(f"{n}=={v}" for n, v in sorted(vendored.items())) or "-"
    print(f"{args.output}: {size} bytes, for CPython {python} on {args.platform}")
    print(f"from the image ({len(provided)}): {', '.join(sorted(provided)) or '-'}")
    print(f"vendored ({len(vendored)}): {listed}")
    print("top level:", ", ".join(sorted(p.name for p in args.output.iterdir())))
    print(
        "next: copy the folder into the project's storage (in a space: cp -r <folder> ~/shared/<name>/),\n"
        "      name that prefix as the job's code input at /opt/ml/processing/code, and set\n"
        "      PYTHONPATH: /opt/ml/processing/code in the job's Environment"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
